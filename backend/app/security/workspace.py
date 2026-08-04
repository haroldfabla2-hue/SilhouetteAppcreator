"""Confinamiento de rutas al workspace.

Los endpoints de lectura/escritura de archivos aceptaban cualquier ruta del
disco. Este módulo obliga a que toda ruta resuelta caiga dentro de la raíz del
workspace y bloquea los archivos sensibles que viven dentro de ella.

La resolución usa `Path.resolve()`, que sigue enlaces simbólicos, de modo que un
symlink apuntando fuera del workspace se detecta después de resolverlo, no antes.
"""
from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

ENV_WORKSPACE_ROOT = "SILHOUETTE_WORKSPACE_ROOT"

# Nombres que nunca se sirven ni se escriben, aunque estén dentro del workspace.
DENIED_NAMES = frozenset(
    {
        ".env",
        ".env.local",
        ".env.production",
        ".env.silhouettemcp",
        "master.key",
        "id_rsa",
        "id_ed25519",
        ".htpasswd",
        ".netrc",
        ".pypirc",
        "credentials.json",
        "token.json",
    }
)

# Directorios cuyo contenido completo queda fuera de alcance.
DENIED_DIRS = frozenset({".git", ".ssh", "node_modules", "__pycache__", ".venv", "venv"})

# Sufijos de material criptográfico.
DENIED_SUFFIXES = frozenset({".key", ".pem", ".pfx", ".p12", ".keystore", ".jks"})


class PathNotAllowed(ValueError):
    """La ruta solicitada queda fuera del workspace o está en la lista de bloqueo."""


def workspace_root() -> Path:
    """Raíz del workspace: variable de entorno, o la raíz del repositorio."""
    configured = os.getenv(ENV_WORKSPACE_ROOT)
    if configured:
        return Path(configured).expanduser().resolve()
    # backend/app/security/workspace.py -> raíz del repositorio
    return Path(__file__).resolve().parents[3]


def _is_denied(relative: Path) -> bool:
    if any(part in DENIED_DIRS for part in relative.parts):
        return True
    if relative.name in DENIED_NAMES:
        return True
    if relative.suffix.lower() in DENIED_SUFFIXES:
        return True
    # Cualquier variante de .env (.env.template, .env.example, ...)
    return relative.name.startswith(".env")


def resolve_within_workspace(candidate: str | os.PathLike[str], *, root: Path | None = None) -> Path:
    """Resuelve `candidate` y garantiza que cae dentro del workspace.

    Lanza `PathNotAllowed` si la ruta escapa de la raíz o está bloqueada.
    """
    base = (root or workspace_root()).resolve()
    raw = Path(candidate).expanduser()
    resolved = (raw if raw.is_absolute() else base / raw).resolve()

    try:
        relative = resolved.relative_to(base)
    except ValueError:
        raise PathNotAllowed(
            f"La ruta queda fuera del workspace ({base}). Rutas permitidas: relativas a la raíz del proyecto."
        ) from None

    if _is_denied(relative):
        raise PathNotAllowed(
            f"'{relative.as_posix()}' está en la lista de bloqueo (secretos, control de versiones o dependencias)."
        )
    return resolved


def is_within_workspace(candidate: str | os.PathLike[str], *, root: Path | None = None) -> bool:
    try:
        resolve_within_workspace(candidate, root=root)
    except PathNotAllowed:
        return False
    return True


def safe_relative(path: Path, *, root: Path | None = None) -> str:
    """Ruta relativa a la raíz, para mostrarla sin revelar la estructura del disco."""
    base = (root or workspace_root()).resolve()
    try:
        return path.resolve().relative_to(base).as_posix()
    except ValueError:
        return path.name


def iter_workspace_files(patterns: Iterable[str], *, root: Path | None = None) -> list[Path]:
    """Expande patrones glob dentro del workspace, descartando lo bloqueado."""
    base = (root or workspace_root()).resolve()
    found: list[Path] = []
    for pattern in patterns:
        for match in base.glob(pattern):
            if match.is_file() and is_within_workspace(match, root=base):
                found.append(match)
    return found
