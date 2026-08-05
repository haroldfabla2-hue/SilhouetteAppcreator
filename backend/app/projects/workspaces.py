"""Espacios de trabajo aislados para agentes concurrentes.

Se afirmaba que cuando el orquestador lanzaba varios agentes a modificar código,
«cada uno trabaja en su propia rama aislada mediante Git Worktrees» y que al
terminar «el SemanticMerger combina las ramas». Las dos clases existían y
**ninguna se invocaba**: no había una sola referencia desde el orquestador.

Aquí eso pasa a ocurrir de verdad, y sobre cualquier proyecto registrado:

    reservar(tarea)  ->  git worktree add -b agente/<tarea>  ->  el agente edita
                     ->  integrar()  ->  merge; si hay conflicto, el merger
                     ->  liberar()   ->  git worktree remove

Dos decisiones deliberadas frente a la versión archivada:

- **Docker es opcional.** El `HybridSandboxManager` original hacía
  `docker.from_env()` en el constructor, así que sin Docker fallaba antes de
  hacer nada. El aislamiento por worktree no necesita contenedores.
- **La integración no fuerza.** Si la fusión produciría conflictos y no hay
  quien los resuelva, se informa y se deja la rama intacta. Perder trabajo de un
  agente por integrarlo a ciegas es peor que dejarlo pendiente.
"""
from __future__ import annotations

import asyncio
import logging
import re
import shutil
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("Workspaces")

WORKTREES_DIR = ".silhouette-worktrees"
BRANCH_PREFIX = "silhouette"
GIT_TIMEOUT_S = 120.0

SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,80}$")


class WorkspaceError(RuntimeError):
    """No se pudo preparar o integrar un espacio de trabajo."""


@dataclass
class Workspace:
    """Un worktree aislado asignado a un agente."""

    task_id: str
    agent: str
    branch: str
    path: str
    base_branch: str
    project_id: str
    created_at: float = field(default_factory=time.time)
    integrated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IntegrationResult:
    workspace: str
    merged: bool
    conflicts: list[str] = field(default_factory=list)
    resolved_by: str = ""
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


async def _git(cwd: Path, *args: str, check: bool = True) -> str:
    """Ejecuta git en un directorio. Nunca con shell."""
    try:
        proceso = await asyncio.create_subprocess_exec(
            "git", "-C", str(cwd), *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.DEVNULL,
        )
    except FileNotFoundError:
        raise WorkspaceError("git no está instalado o no está en el PATH.") from None

    try:
        salida, error = await asyncio.wait_for(proceso.communicate(), timeout=GIT_TIMEOUT_S)
    except asyncio.TimeoutError:
        proceso.kill()
        await proceso.wait()
        raise WorkspaceError(f"git {args[0]} agotó el límite de {GIT_TIMEOUT_S:.0f} s.") from None

    texto = salida.decode("utf-8", errors="replace")
    if proceso.returncode != 0 and check:
        detalle = error.decode("utf-8", errors="replace").strip()
        raise WorkspaceError(f"git {' '.join(args[:2])} falló: {detalle[:400]}")
    return texto


class WorkspaceManager:
    """Reparte worktrees entre agentes e integra su trabajo."""

    def __init__(self, registry: Any = None, merger: Any = None) -> None:
        if registry is None:
            from backend.app.projects.registry import project_registry

            registry = project_registry
        self.registry = registry
        self._merger = merger
        self._workspaces: dict[str, Workspace] = {}

    # -- ramas -------------------------------------------------------------
    async def list_branches(self, project_id: str | None = None) -> dict[str, Any]:
        """Ramas reales del proyecto, con cuál está activa."""
        raiz = self.registry.resolve_root(project_id)
        if not (raiz / ".git").exists():
            raise WorkspaceError(f"'{raiz}' no es un repositorio git.")

        actual = (await _git(raiz, "rev-parse", "--abbrev-ref", "HEAD")).strip()
        salida = await _git(raiz, "branch", "--format=%(refname:short)%09%(objectname:short)%09%(committerdate:relative)")

        ramas = []
        for linea in salida.splitlines():
            partes = linea.split("\t")
            if len(partes) >= 3:
                ramas.append(
                    {
                        "name": partes[0].strip(),
                        "sha": partes[1].strip(),
                        "last_commit": partes[2].strip(),
                        "current": partes[0].strip() == actual,
                        "is_workspace": partes[0].strip().startswith(f"{BRANCH_PREFIX}/"),
                    }
                )
        return {"project": str(raiz), "current": actual, "branches": ramas}

    async def create_branch(
        self, name: str, *, project_id: str | None = None, from_ref: str | None = None,
        checkout: bool = False,
    ) -> dict[str, Any]:
        """Crea una rama en el proyecto."""
        if not SAFE_NAME.match(name or ""):
            raise WorkspaceError(
                f"Nombre de rama inválido: '{name}'. Sólo letras, dígitos y . _ / -"
            )
        raiz = self.registry.resolve_root(project_id)
        args = ["branch", name] + ([from_ref] if from_ref else [])
        await _git(raiz, *args)
        if checkout:
            await _git(raiz, "checkout", name)

        logger.info("[Workspaces] Rama '%s' creada en %s", name, raiz)
        return {
            "created": True,
            "branch": name,
            "checked_out": checkout,
            "sha": (await _git(raiz, "rev-parse", name)).strip(),
        }

    async def switch_branch(self, name: str, *, project_id: str | None = None) -> dict[str, Any]:
        """Cambia de rama. Se niega si hay cambios sin guardar."""
        if not SAFE_NAME.match(name or ""):
            raise WorkspaceError(f"Nombre de rama inválido: '{name}'.")
        raiz = self.registry.resolve_root(project_id)

        sucio = (await _git(raiz, "status", "--porcelain")).strip()
        if sucio:
            raise WorkspaceError(
                f"Hay {len(sucio.splitlines())} archivo(s) con cambios sin guardar. "
                "Cambiar de rama ahora podría perderlos: confirme o descarte antes."
            )

        await _git(raiz, "checkout", name)
        logger.info("[Workspaces] Cambiado a la rama '%s'", name)
        return {"switched": True, "branch": name}

    async def delete_branch(
        self, name: str, *, project_id: str | None = None, force: bool = False
    ) -> dict[str, Any]:
        """Borra una rama. Sin `force`, git se niega si tiene trabajo sin fusionar."""
        if not SAFE_NAME.match(name or ""):
            raise WorkspaceError(f"Nombre de rama inválido: '{name}'.")
        raiz = self.registry.resolve_root(project_id)
        try:
            await _git(raiz, "branch", "-D" if force else "-d", name)
        except WorkspaceError as exc:
            if not force and "not fully merged" in str(exc):
                raise WorkspaceError(
                    f"La rama '{name}' tiene trabajo sin fusionar. "
                    "Use force=true si está seguro de descartarlo."
                ) from None
            raise
        return {"deleted": True, "branch": name, "forced": force}

    # -- espacios aislados -------------------------------------------------
    async def reserve(
        self, task_id: str, agent: str, *, project_id: str | None = None,
        base_branch: str | None = None,
    ) -> Workspace:
        """Reserva un worktree aislado para que un agente trabaje sin colisionar."""
        raiz = self.registry.resolve_root(project_id)
        if not (raiz / ".git").exists():
            raise WorkspaceError(f"'{raiz}' no es un repositorio git; no hay aislamiento posible.")

        seguro = re.sub(r"[^A-Za-z0-9._-]", "-", f"{agent}-{task_id}")[:60]
        rama = f"{BRANCH_PREFIX}/{seguro}"
        destino = raiz / WORKTREES_DIR / seguro

        if destino.exists():
            raise WorkspaceError(f"Ya hay un espacio reservado en {destino}.")

        base = base_branch or (await _git(raiz, "rev-parse", "--abbrev-ref", "HEAD")).strip()
        destino.parent.mkdir(parents=True, exist_ok=True)
        await _git(raiz, "worktree", "add", "-b", rama, str(destino), base)

        espacio = Workspace(
            task_id=task_id,
            agent=agent,
            branch=rama,
            path=str(destino),
            base_branch=base,
            project_id=project_id or (self.registry.active_id or ""),
        )
        self._workspaces[task_id] = espacio
        logger.info("[Workspaces] %s reservó %s sobre %s", agent, rama, base)
        return espacio

    async def integrate(self, task_id: str, *, resolve_conflicts: bool = True) -> IntegrationResult:
        """Fusiona el trabajo de un espacio en su rama base.

        Comprueba antes si habrá conflictos. Si los hay y se pidió resolverlos,
        se delega en el `SemanticMerger`; si no hay quien resuelva, **no se
        fusiona** y se informa de qué archivos chocan.
        """
        espacio = self._workspaces.get(task_id)
        if espacio is None:
            raise WorkspaceError(f"No hay ningún espacio reservado para la tarea '{task_id}'.")

        raiz = self.registry.resolve_root(espacio.project_id or None)

        # ¿Hay algo que integrar?
        cambios = (await _git(Path(espacio.path), "status", "--porcelain")).strip()
        if cambios:
            await _git(Path(espacio.path), "add", "-A")
            await _git(
                Path(espacio.path), "commit", "-m",
                f"{espacio.agent}: trabajo de la tarea {espacio.task_id}",
            )

        commits = (
            await _git(raiz, "rev-list", "--count", f"{espacio.base_branch}..{espacio.branch}")
        ).strip()
        if commits == "0":
            return IntegrationResult(
                workspace=task_id, merged=False,
                detail=f"{espacio.agent} no produjo ningún cambio; no hay nada que integrar.",
            )

        # Comprobación no destructiva: merge-tree calcula en memoria.
        prueba = await _git(
            raiz, "merge-tree", "--write-tree", "--name-only",
            espacio.base_branch, espacio.branch, check=False,
        )
        conflictivos = [
            linea.strip() for linea in prueba.splitlines()[1:]
            if linea.strip() and not linea.strip().startswith(("Auto-merging", "CONFLICT"))
        ]

        if conflictivos and not resolve_conflicts:
            return IntegrationResult(
                workspace=task_id, merged=False, conflicts=conflictivos,
                detail=f"{len(conflictivos)} archivo(s) en conflicto. No se ha fusionado nada.",
            )

        actual = (await _git(raiz, "rev-parse", "--abbrev-ref", "HEAD")).strip()
        if actual != espacio.base_branch:
            await _git(raiz, "checkout", espacio.base_branch)

        try:
            await _git(raiz, "merge", "--no-edit", espacio.branch)
        except WorkspaceError as exc:
            if not conflictivos or not resolve_conflicts:
                await _git(raiz, "merge", "--abort", check=False)
                return IntegrationResult(
                    workspace=task_id, merged=False, conflicts=conflictivos,
                    detail=f"La fusión falló y se abortó: {exc}",
                )

            resuelto = await self._resolve_with_merger(raiz)
            if not resuelto:
                await _git(raiz, "merge", "--abort", check=False)
                return IntegrationResult(
                    workspace=task_id, merged=False, conflicts=conflictivos,
                    detail=(
                        "Hay conflictos y no se pudieron resolver automáticamente. "
                        "La fusión se abortó; la rama del agente sigue intacta."
                    ),
                )
            espacio.integrated = True
            return IntegrationResult(
                workspace=task_id, merged=True, conflicts=conflictivos,
                resolved_by="semantic_merger",
                detail=f"{len(conflictivos)} conflicto(s) resueltos por el merger.",
            )

        espacio.integrated = True
        logger.info("[Workspaces] %s integrado en %s", espacio.branch, espacio.base_branch)
        return IntegrationResult(
            workspace=task_id, merged=True,
            detail=f"Trabajo de {espacio.agent} integrado en {espacio.base_branch}.",
        )

    async def _resolve_with_merger(self, raiz: Path) -> bool:
        """Delega la resolución en el SemanticMerger, si hay uno con router."""
        merger = self._merger
        if merger is None:
            return False
        try:
            resuelto = await merger._resolve_conflicts()  # noqa: SLF001 - API del merger
            return bool(resuelto)
        except Exception as exc:  # noqa: BLE001 - un merger caído no debe romper la integración
            logger.warning("[Workspaces] El merger no pudo resolver: %s", exc)
            return False

    async def release(self, task_id: str, *, keep_branch: bool = False) -> dict[str, Any]:
        """Libera el worktree. Por defecto borra también la rama ya integrada."""
        espacio = self._workspaces.pop(task_id, None)
        if espacio is None:
            return {"released": False, "detail": f"No había espacio para '{task_id}'."}

        raiz = self.registry.resolve_root(espacio.project_id or None)
        await _git(raiz, "worktree", "remove", "--force", espacio.path, check=False)
        shutil.rmtree(espacio.path, ignore_errors=True)

        borrada = False
        if not keep_branch and espacio.integrated:
            await _git(raiz, "branch", "-D", espacio.branch, check=False)
            borrada = True
        elif not keep_branch:
            # Sin integrar, la rama se conserva: contiene trabajo que se perdería.
            logger.info(
                "[Workspaces] Se conserva '%s': tiene trabajo sin integrar", espacio.branch
            )

        return {
            "released": True,
            "branch": espacio.branch,
            "branch_deleted": borrada,
            "detail": (
                "Espacio liberado."
                if borrada
                else f"Espacio liberado; la rama '{espacio.branch}' se conserva."
            ),
        }

    def active_workspaces(self) -> list[dict[str, Any]]:
        return [w.to_dict() for w in self._workspaces.values()]


workspace_manager = WorkspaceManager()
