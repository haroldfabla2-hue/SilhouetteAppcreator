"""Comprensión del repositorio.

Un agente que edita código a ciegas produce parches que no encajan. Antes de
cambiar algo hay que poder responder: ¿dónde está definida esta función? ¿quién
la usa? ¿qué forma tiene este proyecto?

Este módulo construye un índice real del repositorio a partir del código:

- **Estructura**: qué lenguajes, cuántos archivos, cuántas líneas.
- **Símbolos**: clases y funciones de cada módulo Python, con su línea, extraídos
  con `ast` — no con expresiones regulares, que fallan con decoradores,
  anidamiento y cadenas.
- **Búsqueda**: texto y símbolos, con contexto.

El índice se construye leyendo archivos, no estimando. Si un archivo no se puede
parsear, se cuenta como no indexado y se dice — no se omite en silencio.
"""
from __future__ import annotations

import ast
import logging
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from backend.app.security.workspace import (
    DENIED_DIRS,
    resolve_within_workspace,
    safe_relative,
    workspace_root,
)

logger = logging.getLogger("RepoIndex")

# Directorios que nunca se indexan: no son código del proyecto.
SKIP_DIRS = frozenset(
    {*DENIED_DIRS, "legacy", "dist", "build", ".pytest_cache", ".mypy_cache",
     ".ruff_cache", "mcp-context-forge", "data", "artifacts", ".vite"}
)

CODE_SUFFIXES = frozenset(
    {".py", ".ts", ".tsx", ".js", ".jsx", ".sh", ".yml", ".yaml", ".toml", ".json", ".md"}
)

MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_SEARCH_RESULTS = 200


@dataclass
class Symbol:
    name: str
    kind: str
    file: str
    line: int
    signature: str = ""
    docstring: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SearchHit:
    file: str
    line: int
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RepoStats:
    files: int = 0
    lines: int = 0
    by_language: dict[str, int] = field(default_factory=dict)
    symbols: int = 0
    #: Archivos Python que no se pudieron parsear (sintaxis inválida).
    unparsed: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _skip(ruta: Path, raiz: Path) -> bool:
    try:
        relativa = ruta.relative_to(raiz)
    except ValueError:
        return True
    return bool(set(relativa.parts) & SKIP_DIRS)


def _signature(nodo: ast.AST) -> str:
    """Firma legible de una función, sin su cuerpo."""
    if not isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return ""
    argumentos = [a.arg for a in nodo.args.args]
    if nodo.args.vararg:
        argumentos.append(f"*{nodo.args.vararg.arg}")
    if nodo.args.kwarg:
        argumentos.append(f"**{nodo.args.kwarg.arg}")
    prefijo = "async def" if isinstance(nodo, ast.AsyncFunctionDef) else "def"
    return f"{prefijo} {nodo.name}({', '.join(argumentos)})"


class RepoIndex:
    """Índice del repositorio, construido leyendo el código."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root).resolve() if root else workspace_root()
        self._symbols: list[Symbol] = []
        self._stats = RepoStats()
        self._built = False

    # -- construcción ------------------------------------------------------
    def build(self) -> RepoStats:
        """Recorre el repositorio y construye el índice."""
        simbolos: list[Symbol] = []
        estadisticas = RepoStats()
        por_lenguaje: Counter[str] = Counter()

        for ruta in self.root.rglob("*"):
            if not ruta.is_file() or _skip(ruta, self.root):
                continue
            if ruta.suffix.lower() not in CODE_SUFFIXES:
                continue
            if ruta.stat().st_size > MAX_FILE_BYTES:
                continue

            try:
                contenido = ruta.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            estadisticas.files += 1
            estadisticas.lines += contenido.count("\n") + 1
            por_lenguaje[ruta.suffix.lower().lstrip(".")] += 1

            if ruta.suffix.lower() == ".py":
                extraidos = self._symbols_of(contenido, ruta)
                if extraidos is None:
                    estadisticas.unparsed.append(safe_relative(ruta, root=self.root))
                else:
                    simbolos.extend(extraidos)

        estadisticas.by_language = dict(por_lenguaje.most_common())
        estadisticas.symbols = len(simbolos)

        self._symbols = simbolos
        self._stats = estadisticas
        self._built = True

        logger.info(
            "[Índice] %d archivos, %d líneas, %d símbolos (%d sin parsear)",
            estadisticas.files, estadisticas.lines, estadisticas.symbols,
            len(estadisticas.unparsed),
        )
        return estadisticas

    def _symbols_of(self, contenido: str, ruta: Path) -> list[Symbol] | None:
        """Símbolos de un módulo Python. `None` si no se pudo parsear."""
        try:
            arbol = ast.parse(contenido, filename=str(ruta))
        except SyntaxError:
            return None

        relativa = safe_relative(ruta, root=self.root)
        encontrados: list[Symbol] = []

        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.ClassDef):
                tipo = "class"
            elif isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
                tipo = "function"
            else:
                continue
            encontrados.append(
                Symbol(
                    name=nodo.name,
                    kind=tipo,
                    file=relativa,
                    line=nodo.lineno,
                    signature=_signature(nodo),
                    docstring=(ast.get_docstring(nodo) or "").split("\n")[0][:150],
                )
            )
        return encontrados

    def _ensure(self) -> None:
        if not self._built:
            self.build()

    # -- consulta ----------------------------------------------------------
    def stats(self) -> dict[str, Any]:
        self._ensure()
        return self._stats.to_dict()

    def find_symbol(self, name: str, *, exact: bool = False) -> list[dict[str, Any]]:
        """Localiza dónde está definido un símbolo."""
        self._ensure()
        objetivo = name.lower()
        if exact:
            coincidencias = [s for s in self._symbols if s.name == name]
        else:
            coincidencias = [s for s in self._symbols if objetivo in s.name.lower()]
        # Coincidencia exacta primero.
        coincidencias.sort(key=lambda s: (s.name.lower() != objetivo, s.file, s.line))
        return [s.to_dict() for s in coincidencias[:MAX_SEARCH_RESULTS]]

    def search_text(
        self, pattern: str, *, regex: bool = False, suffix: str | None = None
    ) -> list[dict[str, Any]]:
        """Busca texto en el repositorio, devolviendo archivo y línea."""
        try:
            compilado = (
                re.compile(pattern) if regex else re.compile(re.escape(pattern), re.IGNORECASE)
            )
        except re.error as exc:
            raise ValueError(f"Expresión regular inválida: {exc}") from None

        resultados: list[SearchHit] = []
        for ruta in self.root.rglob("*"):
            if len(resultados) >= MAX_SEARCH_RESULTS:
                break
            if not ruta.is_file() or _skip(ruta, self.root):
                continue
            if ruta.suffix.lower() not in CODE_SUFFIXES:
                continue
            if suffix and ruta.suffix.lower() != suffix.lower():
                continue
            if ruta.stat().st_size > MAX_FILE_BYTES:
                continue
            try:
                contenido = ruta.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            for numero, linea in enumerate(contenido.splitlines(), 1):
                if compilado.search(linea):
                    resultados.append(
                        SearchHit(
                            file=safe_relative(ruta, root=self.root),
                            line=numero,
                            text=linea.strip()[:200],
                        )
                    )
                    if len(resultados) >= MAX_SEARCH_RESULTS:
                        break

        return [r.to_dict() for r in resultados]

    def find_references(self, symbol: str) -> dict[str, Any]:
        """Dónde se define un símbolo y dónde se usa.

        Es la consulta que hay que poder responder antes de cambiar una firma.
        """
        definiciones = self.find_symbol(symbol, exact=True)
        usos = self.search_text(rf"\b{re.escape(symbol)}\b", regex=True)
        lineas_definicion = {(d["file"], d["line"]) for d in definiciones}
        referencias = [u for u in usos if (u["file"], u["line"]) not in lineas_definicion]

        return {
            "symbol": symbol,
            "definitions": definiciones,
            "references": referencias,
            "definition_count": len(definiciones),
            "reference_count": len(referencias),
        }

    def outline(self, path: str) -> dict[str, Any]:
        """Estructura de un archivo: sus clases y funciones con su línea."""
        ruta = resolve_within_workspace(path)
        if not ruta.is_file():
            raise FileNotFoundError(f"No existe '{path}'.")
        contenido = ruta.read_text(encoding="utf-8")

        simbolos = self._symbols_of(contenido, ruta)
        if simbolos is None:
            return {
                "file": safe_relative(ruta, root=self.root),
                "parsed": False,
                "detail": "El archivo no es Python válido; no se pudo extraer su estructura.",
                "symbols": [],
            }

        return {
            "file": safe_relative(ruta, root=self.root),
            "parsed": True,
            "lines": contenido.count("\n") + 1,
            "symbols": [s.to_dict() for s in sorted(simbolos, key=lambda s: s.line)],
        }
