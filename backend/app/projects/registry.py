"""Proyectos: carpetas locales sobre las que el sistema puede trabajar.

Hasta ahora el sistema sólo sabía operar sobre su propio directorio: el
confinamiento de rutas apuntaba a la raíz del repositorio y no había forma de
decirle «trabaja en esta otra carpeta». Para un agente de desarrollo eso es una
limitación grave — nadie tiene un solo proyecto.

Un proyecto es una carpeta local registrada explícitamente. Registrarla es el
acto de consentimiento: el sistema **no** puede tocar nada que no esté
registrado, y cada operación de archivos se confina a la raíz del proyecto
activo igual que antes se confinaba a la del repositorio.

Se guarda en `data/projects.json`, con la ruta absoluta, si es un repositorio
git y cuándo se usó por última vez.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("Projects")

REGISTRY_PATH = Path("data/projects.json")

# Carpetas que nunca se admiten como proyecto: registrarlas daría acceso a
# prácticamente todo el disco.
FORBIDDEN_ROOTS = {
    Path.home(),
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path("/"),
    Path("C:/"),
    Path("C:/Windows"),
    Path("C:/Program Files"),
}


class ProjectError(ValueError):
    """La carpeta no puede registrarse como proyecto."""


@dataclass
class Project:
    """Una carpeta local sobre la que se puede trabajar."""

    id: str
    name: str
    path: str
    is_git: bool = False
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    description: str = ""

    @property
    def root(self) -> Path:
        return Path(self.path)

    @property
    def exists(self) -> bool:
        return self.root.is_dir()

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "exists": self.exists}


def _slug(nombre: str) -> str:
    limpio = "".join(c if c.isalnum() or c in "-_" else "-" for c in nombre.lower())
    return "-".join(p for p in limpio.split("-") if p)[:48] or "proyecto"


def _validate_root(ruta: Path) -> Path:
    """Comprueba que la carpeta puede registrarse sin abrir todo el disco."""
    resuelta = ruta.expanduser().resolve()

    if not resuelta.exists():
        raise ProjectError(f"No existe la carpeta '{resuelta}'.")
    if not resuelta.is_dir():
        raise ProjectError(f"'{resuelta}' no es una carpeta.")

    for prohibida in FORBIDDEN_ROOTS:
        try:
            if resuelta == prohibida.resolve():
                raise ProjectError(
                    f"'{resuelta}' es una carpeta raíz del sistema o del usuario. "
                    "Registre el directorio concreto del proyecto, no su contenedor."
                )
        except (OSError, RuntimeError):
            continue

    # Una carpeta con cientos de miles de archivos casi siempre es un error
    # de selección (la raíz del disco, la carpeta de usuario…).
    try:
        for primeros, _ in enumerate(resuelta.iterdir(), 1):
            if primeros > 20000:
                raise ProjectError(
                    f"'{resuelta}' contiene demasiadas entradas de primer nivel. "
                    "¿Ha seleccionado la carpeta correcta?"
                )
    except PermissionError:
        raise ProjectError(f"Sin permiso de lectura sobre '{resuelta}'.") from None

    return resuelta


class ProjectRegistry:
    """Registro persistente de proyectos."""

    def __init__(self, path: Path = REGISTRY_PATH) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()
        self._projects: dict[str, Project] = {}
        self._active: str | None = None
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("No se pudo leer %s (%s); se parte sin proyectos.", self.path, exc)
            return
        for datos in raw.get("projects", []):
            proyecto = Project(**datos)
            self._projects[proyecto.id] = proyecto
        self._active = raw.get("active")
        logger.info("[Proyectos] %d registrado(s)", len(self._projects))

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "projects": [asdict(p) for p in self._projects.values()],
            "active": self._active,
        }
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)

    # -- alta y baja -------------------------------------------------------
    def register(self, path: str | Path, *, name: str = "", description: str = "") -> Project:
        """Registra una carpeta local como proyecto."""
        raiz = _validate_root(Path(path))

        with self._lock:
            for existente in self._projects.values():
                if Path(existente.path) == raiz:
                    existente.last_used = time.time()
                    self._save()
                    return existente

            nombre = name.strip() or raiz.name
            identificador = _slug(nombre)
            sufijo = 1
            while identificador in self._projects:
                sufijo += 1
                identificador = f"{_slug(nombre)}-{sufijo}"

            proyecto = Project(
                id=identificador,
                name=nombre,
                path=str(raiz),
                is_git=(raiz / ".git").exists(),
                description=description.strip(),
            )
            self._projects[identificador] = proyecto
            if self._active is None:
                self._active = identificador
            self._save()

        logger.info("[Proyectos] Registrado '%s' en %s (git=%s)", proyecto.name, raiz, proyecto.is_git)
        return proyecto

    def unregister(self, project_id: str) -> bool:
        """Quita un proyecto del registro. **No borra la carpeta.**"""
        with self._lock:
            if project_id not in self._projects:
                return False
            del self._projects[project_id]
            if self._active == project_id:
                self._active = next(iter(self._projects), None)
            self._save()
        logger.info("[Proyectos] '%s' retirado del registro (la carpeta no se toca)", project_id)
        return True

    # -- consulta ----------------------------------------------------------
    def get(self, project_id: str) -> Project | None:
        return self._projects.get(project_id)

    def require(self, project_id: str) -> Project:
        proyecto = self._projects.get(project_id)
        if proyecto is None:
            raise ProjectError(
                f"No hay ningún proyecto '{project_id}'. Registrados: "
                + (", ".join(self._projects) or "ninguno")
            )
        if not proyecto.exists:
            raise ProjectError(
                f"La carpeta de '{project_id}' ya no existe: {proyecto.path}"
            )
        return proyecto

    def list_all(self) -> list[dict[str, Any]]:
        return [p.to_dict() for p in sorted(self._projects.values(), key=lambda p: -p.last_used)]

    # -- proyecto activo ---------------------------------------------------
    @property
    def active_id(self) -> str | None:
        return self._active

    def active(self) -> Project | None:
        return self._projects.get(self._active) if self._active else None

    def set_active(self, project_id: str) -> Project:
        proyecto = self.require(project_id)
        with self._lock:
            self._active = project_id
            proyecto.last_used = time.time()
            self._save()
        logger.info("[Proyectos] Activo: %s", proyecto.name)
        return proyecto

    def resolve_root(self, project_id: str | None = None) -> Path:
        """Raíz sobre la que confinar las operaciones de archivos.

        Sin proyecto indicado ni activo, se usa la del propio repositorio: el
        comportamiento anterior, que sigue siendo el seguro por defecto.
        """
        if project_id:
            return self.require(project_id).root
        activo = self.active()
        if activo is not None and activo.exists:
            return activo.root

        from backend.app.security.workspace import workspace_root

        return workspace_root()


project_registry = ProjectRegistry()
