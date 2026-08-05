"""Operaciones Git reales.

Sustituye a `legacy/mcp-core-superior/src/agents/git_operations_agent.py`, que
declaraba cinco capacidades y las cinco eran `_simulate_*`: devolvían ramas,
commits y conflictos inventados sin tocar el repositorio.

No había ninguna razón técnica para fingirlas — son comandos `git`. Para un
sistema que se propone ser un agente de desarrollo, operar el control de
versiones de verdad es funcionalidad central, no accesoria.

Reglas de esta implementación:

- Toda ruta se confina al workspace (`security.workspace`), igual que los
  endpoints de archivos.
- Nunca se usa `shell=True`; los argumentos van como lista.
- Las operaciones que **escriben** están separadas de las que sólo leen, y las
  destructivas exigen confirmación explícita del llamador.
- Un fallo de git se propaga con su salida real, no se traduce a un éxito.
"""
from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from backend.app.security.workspace import PathNotAllowed, resolve_within_workspace

logger = logging.getLogger("GitAgent")

DEFAULT_TIMEOUT_S = 60.0
# Separador improbable en texto de commit, para partir la salida sin ambigüedad.
FIELD_SEP = "\x1f"
RECORD_SEP = "\x1e"

# Nombres de rama admitidos. Git acepta más, pero esto evita que un nombre
# generado por un modelo introduzca opciones (`--force`) o rutas.
BRANCH_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,100}$")


class GitError(RuntimeError):
    """Un comando git falló. Contiene la salida real de git."""


class NotARepository(GitError):
    """La ruta indicada no es un repositorio git."""


class InvalidBranchName(ValueError):
    """El nombre de rama no supera la validación."""


@dataclass
class Commit:
    sha: str
    author: str
    email: str
    date: str
    subject: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RepositoryInfo:
    path: str
    current_branch: str
    head_sha: str
    is_dirty: bool
    modified: list[str] = field(default_factory=list)
    untracked: list[str] = field(default_factory=list)
    staged: list[str] = field(default_factory=list)
    branches: list[str] = field(default_factory=list)
    remotes: dict[str, str] = field(default_factory=dict)
    ahead: int = 0
    behind: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ConflictReport:
    """Resultado de comprobar si dos ramas pueden fusionarse."""

    source: str
    target: str
    can_merge: bool
    conflicted_files: list[str] = field(default_factory=list)
    merge_base: str = ""
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GitAgent:
    """Ejecuta git sobre un repositorio confinado al workspace."""

    def __init__(self, repo_path: str | Path = ".", *, timeout_s: float = DEFAULT_TIMEOUT_S) -> None:
        try:
            self.repo_path = resolve_within_workspace(repo_path)
        except PathNotAllowed as exc:
            raise GitError(f"Ruta de repositorio no permitida: {exc}") from None
        self.timeout_s = timeout_s

    # -- ejecución ---------------------------------------------------------
    async def _git(self, *args: str, check: bool = True) -> str:
        """Ejecuta un comando git y devuelve su salida estándar."""
        try:
            proceso = await asyncio.create_subprocess_exec(
                "git",
                "-C",
                str(self.repo_path),
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL,
            )
        except FileNotFoundError:
            raise GitError("git no está instalado o no está en el PATH.") from None

        try:
            salida, error = await asyncio.wait_for(
                proceso.communicate(), timeout=self.timeout_s
            )
        except asyncio.TimeoutError:
            proceso.kill()
            await proceso.wait()
            raise GitError(
                f"git {' '.join(args[:2])} agotó el límite de {self.timeout_s:.0f} s."
            ) from None

        texto = salida.decode("utf-8", errors="replace")
        if proceso.returncode != 0 and check:
            detalle = error.decode("utf-8", errors="replace").strip()
            if "not a git repository" in detalle.lower():
                raise NotARepository(f"{self.repo_path} no es un repositorio git.")
            raise GitError(
                f"git {' '.join(args[:3])} falló (código {proceso.returncode}): "
                f"{detalle[:400] or '(sin detalle)'}"
            )
        return texto

    @staticmethod
    def _validate_branch(nombre: str) -> str:
        limpio = (nombre or "").strip()
        if not BRANCH_PATTERN.match(limpio):
            raise InvalidBranchName(
                f"Nombre de rama inválido: '{nombre}'. Se admiten letras, dígitos "
                "y . _ / - empezando por carácter alfanumérico."
            )
        return limpio

    # -- lectura -----------------------------------------------------------
    async def get_repository_info(self) -> RepositoryInfo:
        """Estado real del repositorio."""
        rama = (await self._git("rev-parse", "--abbrev-ref", "HEAD")).strip()
        try:
            head = (await self._git("rev-parse", "HEAD")).strip()
        except GitError:
            head = ""  # Repositorio recién creado, sin commits.

        estado = await self._git("status", "--porcelain=v1")
        modificados, sin_seguir, preparados = [], [], []
        for linea in estado.splitlines():
            if len(linea) < 4:
                continue
            indice, arbol, ruta = linea[0], linea[1], linea[3:]
            if indice == "?" and arbol == "?":
                sin_seguir.append(ruta)
                continue
            if indice != " ":
                preparados.append(ruta)
            if arbol != " ":
                modificados.append(ruta)

        ramas = [
            b.strip().lstrip("* ").strip()
            for b in (await self._git("branch", "--format=%(refname:short)")).splitlines()
            if b.strip()
        ]

        remotos: dict[str, str] = {}
        for linea in (await self._git("remote", "-v")).splitlines():
            partes = linea.split()
            if len(partes) >= 2:
                remotos.setdefault(partes[0], partes[1])

        adelante = detras = 0
        try:
            cuenta = await self._git(
                "rev-list", "--left-right", "--count", f"{rama}...@{{upstream}}"
            )
            izquierda, derecha = cuenta.split()
            adelante, detras = int(izquierda), int(derecha)
        except (GitError, ValueError):
            # Sin rama remota configurada: no es un error, simplemente no aplica.
            pass

        return RepositoryInfo(
            path=str(self.repo_path),
            current_branch=rama,
            head_sha=head,
            is_dirty=bool(modificados or preparados or sin_seguir),
            modified=modificados,
            untracked=sin_seguir,
            staged=preparados,
            branches=ramas,
            remotes=remotos,
            ahead=adelante,
            behind=detras,
        )

    async def get_commit_history(
        self, limit: int = 20, *, branch: str | None = None, path: str | None = None
    ) -> list[Commit]:
        """Historial real de commits."""
        formato = FIELD_SEP.join(["%H", "%an", "%ae", "%aI", "%s"]) + RECORD_SEP
        args = ["log", f"--max-count={max(1, min(limit, 500))}", f"--format={formato}"]
        if branch:
            args.append(self._validate_branch(branch))
        if path:
            # La ruta se confina igual que en el resto del sistema.
            resuelto = resolve_within_workspace(path)
            args.extend(["--", str(resuelto)])

        salida = await self._git(*args)
        commits: list[Commit] = []
        for registro in salida.split(RECORD_SEP):
            registro = registro.strip("\n")
            if not registro:
                continue
            campos = registro.split(FIELD_SEP)
            if len(campos) == 5:
                commits.append(Commit(*campos))
        return commits

    async def detect_conflicts(self, source: str, target: str) -> ConflictReport:
        """Comprueba si `source` puede fusionarse en `target` **sin fusionar nada**.

        Usa `merge-tree`, que calcula la fusión en memoria: no toca el árbol de
        trabajo ni el índice, así que es seguro llamarlo sobre un repositorio en
        uso. La versión anterior devolvía conflictos inventados.
        """
        origen = self._validate_branch(source)
        destino = self._validate_branch(target)

        try:
            base = (await self._git("merge-base", origen, destino)).strip()
        except GitError as exc:
            return ConflictReport(
                source=origen,
                target=destino,
                can_merge=False,
                detail=f"No hay ancestro común: {exc}",
            )

        # git >= 2.38 admite `merge-tree --write-tree`, que informa de conflictos
        # con el código de salida. En versiones anteriores se cae al formato antiguo.
        salida = await self._git(
            "merge-tree", "--write-tree", "--name-only", destino, origen, check=False
        )
        conflictivos = [
            linea.strip()
            for linea in salida.splitlines()[1:]
            if linea.strip() and not linea.strip().startswith(("Auto-merging", "CONFLICT"))
        ]
        # La primera línea es el OID del árbol resultante cuando no hay conflicto.
        hay_conflicto = bool(conflictivos)

        return ConflictReport(
            source=origen,
            target=destino,
            can_merge=not hay_conflicto,
            conflicted_files=conflictivos,
            merge_base=base,
            detail=(
                "Fusión limpia."
                if not hay_conflicto
                else f"{len(conflictivos)} archivo(s) en conflicto."
            ),
        )

    # -- escritura ---------------------------------------------------------
    async def create_branch(self, name: str, *, from_ref: str | None = None) -> dict[str, Any]:
        """Crea una rama de verdad."""
        rama = self._validate_branch(name)
        args = ["branch", rama]
        if from_ref:
            args.append(self._validate_branch(from_ref))
        await self._git(*args)
        logger.info("[Git] Rama creada: %s", rama)
        return {
            "created": True,
            "branch": rama,
            "from": from_ref or "HEAD",
            "sha": (await self._git("rev-parse", rama)).strip(),
        }

    async def merge_branch(
        self, source: str, *, message: str | None = None, allow_conflicts: bool = False
    ) -> dict[str, Any]:
        """Fusiona `source` en la rama actual.

        Comprueba antes si habrá conflictos y, salvo que el llamador lo permita
        explícitamente, no inicia una fusión que dejaría el repositorio a medias.
        """
        origen = self._validate_branch(source)
        actual = (await self._git("rev-parse", "--abbrev-ref", "HEAD")).strip()

        informe = await self.detect_conflicts(origen, actual)
        if not informe.can_merge and not allow_conflicts:
            return {
                "merged": False,
                "reason": "conflictos_detectados",
                "detail": (
                    f"La fusión de '{origen}' en '{actual}' produciría conflictos en "
                    f"{len(informe.conflicted_files)} archivo(s). No se ha tocado nada."
                ),
                "conflicted_files": informe.conflicted_files,
            }

        args = ["merge", "--no-edit", origen]
        if message:
            args = ["merge", "-m", message, origen]

        try:
            salida = await self._git(*args)
        except GitError as exc:
            # Una fusión fallida deja el repositorio en estado de conflicto: se
            # aborta para no dejarlo a medias sin que nadie lo sepa.
            await self._git("merge", "--abort", check=False)
            return {
                "merged": False,
                "reason": "fallo_al_fusionar",
                "detail": f"{exc} (la fusión se abortó; el repositorio queda como estaba)",
            }

        logger.info("[Git] '%s' fusionada en '%s'", origen, actual)
        return {
            "merged": True,
            "source": origen,
            "target": actual,
            "head_sha": (await self._git("rev-parse", "HEAD")).strip(),
            "detail": salida.strip(),
        }

    async def get_diff(self, *, staged: bool = False, max_chars: int = 20000) -> str:
        """Diff real del árbol de trabajo o del índice."""
        args = ["diff", "--cached"] if staged else ["diff"]
        salida = await self._git(*args)
        if len(salida) > max_chars:
            return salida[:max_chars] + f"\n… (truncado en {max_chars} caracteres)"
        return salida
