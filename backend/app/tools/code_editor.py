"""Edición de código segura y verificable.

Un agente de desarrollo se define por lo que puede cambiar sin romper nada. El
sistema tenía un endpoint que escribía archivos enteros — suficiente para
generar, insuficiente para *editar*: reescribir un archivo completo para cambiar
tres líneas es cómo se pierde trabajo.

Este módulo aporta las tres garantías que faltaban:

1. **Edición por coincidencia exacta.** Se sustituye un fragmento concreto, y si
   aparece más de una vez la operación se rechaza en lugar de adivinar cuál.
2. **Validación antes de escribir.** Si el resultado no compila (Python, JSON,
   TOML, YAML), no se guarda. Un agente que deja el árbol roto es peor que uno
   que no edita.
3. **Copia de seguridad y reversión.** Cada escritura guarda el contenido
   anterior; `revert()` lo restaura.

Todo se confina al workspace, igual que el resto del sistema.
"""
from __future__ import annotations

import ast
import difflib
import json
import logging
import shutil
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from backend.app.security.workspace import (
    PathNotAllowed,
    resolve_within_workspace,
    safe_relative,
)

logger = logging.getLogger("CodeEditor")

MAX_FILE_BYTES = 4 * 1024 * 1024
BACKUP_DIR = Path("data/edit_backups")
MAX_BACKUPS_PER_FILE = 10


class EditError(RuntimeError):
    """La edición no se pudo aplicar. El archivo queda como estaba."""


class AmbiguousMatch(EditError):
    """El fragmento a sustituir aparece varias veces."""


class NoMatch(EditError):
    """El fragmento a sustituir no aparece en el archivo."""


class ValidationFailed(EditError):
    """El resultado de la edición no es válido; no se escribió nada."""


@dataclass
class EditResult:
    path: str
    applied: bool
    lines_added: int = 0
    lines_removed: int = 0
    diff: str = ""
    backup: str = ""
    validated_as: str = ""
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FileView:
    path: str
    content: str
    lines: int
    size_bytes: int
    language: str
    symbols: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


LANGUAGES: dict[str, str] = {
    ".py": "python",
    ".json": "json",
    ".toml": "toml",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".md": "markdown",
    ".sh": "shell",
    ".html": "html",
    ".css": "css",
}


def _language(path: Path) -> str:
    return LANGUAGES.get(path.suffix.lower(), "text")


def _validate(contenido: str, path: Path) -> str:
    """Comprueba que el contenido es sintácticamente válido para su tipo.

    Devuelve el nombre del validador aplicado, o cadena vacía si el tipo no
    tiene validación. Lanza `ValidationFailed` si el contenido está roto.
    """
    idioma = _language(path)

    if idioma == "python":
        try:
            ast.parse(contenido, filename=str(path))
        except SyntaxError as exc:
            raise ValidationFailed(
                f"El resultado no es Python válido (línea {exc.lineno}): {exc.msg}. "
                "No se ha escrito nada."
            ) from None
        return "python-ast"

    if idioma == "json":
        try:
            json.loads(contenido)
        except json.JSONDecodeError as exc:
            raise ValidationFailed(
                f"El resultado no es JSON válido (línea {exc.lineno}): {exc.msg}. "
                "No se ha escrito nada."
            ) from None
        return "json"

    if idioma == "toml":
        try:
            import tomllib

            tomllib.loads(contenido)
        except ImportError:
            return ""
        except Exception as exc:
            raise ValidationFailed(f"El resultado no es TOML válido: {exc}") from None
        return "toml"

    if idioma == "yaml":
        try:
            import yaml

            yaml.safe_load(contenido)
        except ImportError:
            return ""
        except Exception as exc:
            raise ValidationFailed(f"El resultado no es YAML válido: {exc}") from None
        return "yaml"

    return ""


def _extract_symbols(contenido: str, path: Path) -> list[dict[str, Any]]:
    """Funciones y clases de un archivo Python, con su línea."""
    if _language(path) != "python":
        return []
    try:
        arbol = ast.parse(contenido)
    except SyntaxError:
        return []

    simbolos: list[dict[str, Any]] = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ClassDef):
            tipo = "class"
        elif isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            tipo = "async def" if isinstance(nodo, ast.AsyncFunctionDef) else "def"
        else:
            continue
        simbolos.append(
            {
                "name": nodo.name,
                "kind": tipo,
                "line": nodo.lineno,
                "docstring": (ast.get_docstring(nodo) or "").split("\n")[0][:100],
            }
        )
    return sorted(simbolos, key=lambda s: s["line"])


class CodeEditor:
    """Lee y edita archivos del workspace con validación y reversión."""

    def __init__(self, *, backup_dir: Path = BACKUP_DIR) -> None:
        self.backup_dir = Path(backup_dir)

    def _resolve(self, path: str | Path) -> Path:
        try:
            return resolve_within_workspace(path)
        except PathNotAllowed as exc:
            raise EditError(str(exc)) from None

    # -- lectura -----------------------------------------------------------
    def read(self, path: str | Path, *, with_symbols: bool = True) -> FileView:
        """Lee un archivo con su estructura."""
        destino = self._resolve(path)
        if not destino.is_file():
            raise EditError(f"No existe el archivo '{safe_relative(destino)}'.")
        if destino.stat().st_size > MAX_FILE_BYTES:
            raise EditError(
                f"'{safe_relative(destino)}' supera el límite de "
                f"{MAX_FILE_BYTES // 1024 // 1024} MiB."
            )

        try:
            contenido = destino.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise EditError(f"'{safe_relative(destino)}' no es texto UTF-8.") from None

        return FileView(
            path=safe_relative(destino),
            content=contenido,
            lines=contenido.count("\n") + 1,
            size_bytes=len(contenido.encode("utf-8")),
            language=_language(destino),
            symbols=_extract_symbols(contenido, destino) if with_symbols else [],
        )

    # -- respaldo ----------------------------------------------------------
    def _backup(self, destino: Path, contenido: str) -> str:
        """Guarda el contenido anterior antes de sobrescribir."""
        relativo = safe_relative(destino).replace("/", "__")
        carpeta = self.backup_dir / relativo
        carpeta.mkdir(parents=True, exist_ok=True)

        copia = carpeta / f"{int(time.time() * 1000)}.bak"
        copia.write_text(contenido, encoding="utf-8")

        # Sólo se conservan las últimas N versiones.
        versiones = sorted(carpeta.glob("*.bak"))
        for vieja in versiones[:-MAX_BACKUPS_PER_FILE]:
            vieja.unlink(missing_ok=True)

        return str(copia)

    @staticmethod
    def _diff(antes: str, despues: str, nombre: str) -> tuple[str, int, int]:
        lineas = list(
            difflib.unified_diff(
                antes.splitlines(keepends=True),
                despues.splitlines(keepends=True),
                fromfile=f"a/{nombre}",
                tofile=f"b/{nombre}",
                n=3,
            )
        )
        añadidas = sum(1 for x in lineas if x.startswith("+") and not x.startswith("+++"))
        quitadas = sum(1 for x in lineas if x.startswith("-") and not x.startswith("---"))
        return "".join(lineas), añadidas, quitadas

    # -- escritura ---------------------------------------------------------
    def _write(self, destino: Path, nuevo: str, anterior: str | None) -> EditResult:
        """Valida, respalda y escribe. Cualquier fallo deja el archivo intacto."""
        validado = _validate(nuevo, destino)

        respaldo = ""
        if anterior is not None:
            respaldo = self._backup(destino, anterior)

        destino.parent.mkdir(parents=True, exist_ok=True)
        # Escritura atómica: si el proceso muere a mitad, el original sobrevive.
        temporal = destino.with_suffix(destino.suffix + ".tmp")
        temporal.write_text(nuevo, encoding="utf-8")
        temporal.replace(destino)

        diff, añadidas, quitadas = self._diff(anterior or "", nuevo, safe_relative(destino))
        logger.info(
            "[Editor] %s: +%d -%d (validado: %s)",
            safe_relative(destino), añadidas, quitadas, validado or "sin validación",
        )

        return EditResult(
            path=safe_relative(destino),
            applied=True,
            lines_added=añadidas,
            lines_removed=quitadas,
            diff=diff,
            backup=respaldo,
            validated_as=validado,
            detail="Cambio aplicado.",
        )

    def create(self, path: str | Path, content: str) -> EditResult:
        """Crea un archivo nuevo. Falla si ya existe."""
        destino = self._resolve(path)
        if destino.exists():
            raise EditError(
                f"'{safe_relative(destino)}' ya existe. Use `replace` o `write` para modificarlo."
            )
        return self._write(destino, content, None)

    def write(self, path: str | Path, content: str) -> EditResult:
        """Sobrescribe un archivo entero, respaldando el anterior."""
        destino = self._resolve(path)
        anterior = destino.read_text(encoding="utf-8") if destino.is_file() else None
        return self._write(destino, content, anterior)

    def replace(
        self, path: str | Path, old: str, new: str, *, replace_all: bool = False
    ) -> EditResult:
        """Sustituye un fragmento exacto.

        Si `old` aparece varias veces y no se pidió `replace_all`, la operación
        se rechaza: adivinar cuál era la ocurrencia correcta es cómo un agente
        corrompe un archivo sin que nadie se entere.
        """
        destino = self._resolve(path)
        if not destino.is_file():
            raise EditError(f"No existe el archivo '{safe_relative(destino)}'.")

        contenido = destino.read_text(encoding="utf-8")
        apariciones = contenido.count(old)

        if apariciones == 0:
            raise NoMatch(
                f"El fragmento no aparece en '{safe_relative(destino)}'. "
                "Compruebe espacios e indentación: la coincidencia es exacta."
            )
        if apariciones > 1 and not replace_all:
            raise AmbiguousMatch(
                f"El fragmento aparece {apariciones} veces en "
                f"'{safe_relative(destino)}'. Amplíe el contexto para que sea único, "
                "o pase replace_all=True si desea cambiarlas todas."
            )

        nuevo = contenido.replace(old, new) if replace_all else contenido.replace(old, new, 1)
        if nuevo == contenido:
            return EditResult(
                path=safe_relative(destino),
                applied=False,
                detail="El contenido resultante es idéntico; no se escribió nada.",
            )

        resultado = self._write(destino, nuevo, contenido)
        resultado.detail = f"{apariciones if replace_all else 1} sustitución(es) aplicada(s)."
        return resultado

    def revert(self, path: str | Path) -> EditResult:
        """Restaura la última versión respaldada de un archivo."""
        destino = self._resolve(path)
        carpeta = self.backup_dir / safe_relative(destino).replace("/", "__")
        versiones = sorted(carpeta.glob("*.bak")) if carpeta.is_dir() else []

        if not versiones:
            raise EditError(
                f"No hay copias de seguridad de '{safe_relative(destino)}'."
            )

        ultima = versiones[-1]
        contenido = ultima.read_text(encoding="utf-8")
        actual = destino.read_text(encoding="utf-8") if destino.is_file() else ""

        shutil.copy2(ultima, destino)
        ultima.unlink(missing_ok=True)

        diff, añadidas, quitadas = self._diff(actual, contenido, safe_relative(destino))
        logger.info("[Editor] %s revertido", safe_relative(destino))
        return EditResult(
            path=safe_relative(destino),
            applied=True,
            lines_added=añadidas,
            lines_removed=quitadas,
            diff=diff,
            detail=f"Restaurada la copia {ultima.name}.",
        )

    def backups(self, path: str | Path) -> list[dict[str, Any]]:
        """Copias disponibles de un archivo."""
        destino = self._resolve(path)
        carpeta = self.backup_dir / safe_relative(destino).replace("/", "__")
        if not carpeta.is_dir():
            return []
        return [
            {
                "name": v.name,
                "saved_at": int(v.stem) / 1000,
                "size_bytes": v.stat().st_size,
            }
            for v in sorted(carpeta.glob("*.bak"), reverse=True)
        ]
