"""Búsqueda real de literatura científica.

Sustituye a `legacy/code/silhouettemcp_expanded_research.py`, un «Research
Intelligence Agent» que generaba números de patente, fechas, oficinas y hasta
nombres de inventores con `random.choice()`:

    "inventors": [{"name": f"Dr. {random.choice(['John','Mary','Carlos','Ana'])} ..."}]

Devolvía resultados con aspecto plausible que no existían. En una herramienta de
investigación eso es peor que no tener herramienta: nadie comprueba una cita que
parece correcta.

Aquí se consultan dos APIs públicas y gratuitas, sin credenciales:

- **arXiv** (`export.arxiv.org/api/query`) — preprints de física, matemáticas,
  informática y biología.
- **Semantic Scholar** (`api.semanticscholar.org/graph/v1`) — cobertura amplia
  con recuento de citas.

Lo que **no** cubre: patentes. Requiere una API de pago y es una decisión de
producto, no técnica. Se declara en lugar de fingirse.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict, dataclass, field
from typing import Any

import httpx

logger = logging.getLogger("Research")

# El XML llega de la red, así que se parsea con `defusedxml`, que desactiva la
# expansión de entidades. Con la biblioteca estándar, un feed manipulado puede
# provocar denegación de servicio por expansión exponencial («billion laughs»).
#
# No hay respaldo con el parser estándar a propósito: recurrir a él dejaría un
# camino vulnerable abierto sin que nadie lo notara. Sin `defusedxml`, arXiv se
# declara no disponible — igual que cualquier otra capacidad que falte.
try:
    from defusedxml import ElementTree as ET

    XML_HARDENED = True
except ImportError:  # pragma: no cover - depende del entorno
    ET = None
    XML_HARDENED = False
    logger.warning(
        "defusedxml no está instalado: la búsqueda en arXiv queda desactivada. "
        "Instale con: pip install defusedxml"
    )

# Tamaño máximo de respuesta XML que se acepta parsear. Un límite explícito
# acota el daño aunque falte defusedxml.
MAX_XML_BYTES = 8 * 1024 * 1024

ARXIV_API = "https://export.arxiv.org/api/query"
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"

DEFAULT_TIMEOUT_S = 20.0
MAX_RESULTS = 50

# arXiv rechaza peticiones seguidas; el reintento cubre el corte transitorio.
ARXIV_RETRIES = 3
ARXIV_RETRY_DELAY_S = 1.5

ATOM = "{http://www.w3.org/2005/Atom}"


class ResearchUnavailable(RuntimeError):
    """No se pudo consultar la fuente. Nunca se sustituye por resultados inventados."""


@dataclass
class Paper:
    """Un artículo real, con su identificador verificable."""

    title: str
    authors: list[str]
    abstract: str
    published: str
    url: str
    source: str
    doi: str = ""
    arxiv_id: str = ""
    citation_count: int | None = None  # None = la fuente no lo informa
    categories: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean(texto: str | None) -> str:
    return " ".join((texto or "").split())


def _parse_arxiv(xml_text: str) -> list[Paper]:
    """Convierte la respuesta Atom de arXiv en artículos."""
    if not XML_HARDENED:
        raise ResearchUnavailable(
            "arXiv requiere `defusedxml` para parsear su respuesta de forma segura. "
            "Instale con: pip install defusedxml"
        )
    if len(xml_text) > MAX_XML_BYTES:
        raise ResearchUnavailable(
            f"La respuesta de arXiv supera el límite de {MAX_XML_BYTES // 1024 // 1024} MiB."
        )
    try:
        raiz = ET.fromstring(xml_text)
    except Exception as exc:  # defusedxml y la stdlib lanzan tipos distintos
        raise ResearchUnavailable(f"arXiv devolvió XML inválido: {exc}") from None

    articulos: list[Paper] = []
    for entrada in raiz.findall(f"{ATOM}entry"):
        enlace = entrada.findtext(f"{ATOM}id", default="")
        arxiv_id = enlace.rsplit("/", 1)[-1] if enlace else ""
        doi = entrada.findtext("{http://arxiv.org/schemas/atom}doi", default="") or ""

        articulos.append(
            Paper(
                title=_clean(entrada.findtext(f"{ATOM}title")),
                authors=[
                    _clean(a.findtext(f"{ATOM}name"))
                    for a in entrada.findall(f"{ATOM}author")
                ],
                abstract=_clean(entrada.findtext(f"{ATOM}summary")),
                published=entrada.findtext(f"{ATOM}published", default=""),
                url=enlace,
                source="arxiv",
                doi=doi,
                arxiv_id=arxiv_id,
                categories=[
                    c.get("term", "") for c in entrada.findall(f"{ATOM}category")
                ],
            )
        )
    return articulos


async def search_arxiv(
    query: str, *, limit: int = 10, timeout_s: float = DEFAULT_TIMEOUT_S
) -> list[Paper]:
    """Busca en arXiv. Sin credenciales, sin coste."""
    parametros = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max(1, min(limit, MAX_RESULTS)),
        "sortBy": "relevance",
    }
    # arXiv corta conexiones cuando recibe peticiones seguidas. Es un fallo
    # transitorio, no una ausencia de resultados: se reintenta antes de darlo
    # por perdido, pero si agota los intentos se declara — nunca se rellena.
    ultimo_error: Exception | None = None
    for intento in range(ARXIV_RETRIES):
        try:
            # arXiv responde con una redirección; sin seguirla se recibe el
            # cuerpo del redirect en lugar del XML de resultados.
            async with httpx.AsyncClient(timeout=timeout_s, follow_redirects=True) as cliente:
                respuesta = await cliente.get(ARXIV_API, params=parametros)
                respuesta.raise_for_status()
            break
        except httpx.HTTPError as exc:
            ultimo_error = exc
            if intento < ARXIV_RETRIES - 1:
                await asyncio.sleep(ARXIV_RETRY_DELAY_S * (intento + 1))
    else:
        detalle = str(ultimo_error) or type(ultimo_error).__name__
        raise ResearchUnavailable(
            f"No se pudo consultar arXiv tras {ARXIV_RETRIES} intentos: {detalle}"
        ) from None

    articulos = _parse_arxiv(respuesta.text)
    logger.info("[Research] arXiv: %d resultado(s) para '%s'", len(articulos), query[:50])
    return articulos


async def search_semantic_scholar(
    query: str, *, limit: int = 10, timeout_s: float = DEFAULT_TIMEOUT_S
) -> list[Paper]:
    """Busca en Semantic Scholar. Sin credenciales; con límite de peticiones."""
    campos = "title,abstract,authors,year,url,citationCount,externalIds,publicationDate"
    parametros = {"query": query, "limit": max(1, min(limit, 100)), "fields": campos}

    try:
        async with httpx.AsyncClient(timeout=timeout_s, follow_redirects=True) as cliente:
            respuesta = await cliente.get(SEMANTIC_SCHOLAR_API, params=parametros)
            if respuesta.status_code == 429:
                raise ResearchUnavailable(
                    "Semantic Scholar aplicó límite de peticiones. Reintente en unos segundos."
                )
            respuesta.raise_for_status()
            datos = respuesta.json()
    except httpx.HTTPError as exc:
        raise ResearchUnavailable(f"No se pudo consultar Semantic Scholar: {exc}") from None
    except ValueError as exc:
        raise ResearchUnavailable(f"Semantic Scholar devolvió JSON inválido: {exc}") from None

    articulos: list[Paper] = []
    for item in datos.get("data") or []:
        externos = item.get("externalIds") or {}
        articulos.append(
            Paper(
                title=_clean(item.get("title")),
                authors=[_clean(a.get("name")) for a in (item.get("authors") or [])],
                abstract=_clean(item.get("abstract")),
                published=str(item.get("publicationDate") or item.get("year") or ""),
                url=item.get("url") or "",
                source="semantic_scholar",
                doi=externos.get("DOI", "") or "",
                arxiv_id=externos.get("ArXiv", "") or "",
                citation_count=item.get("citationCount"),
            )
        )
    logger.info(
        "[Research] Semantic Scholar: %d resultado(s) para '%s'", len(articulos), query[:50]
    )
    return articulos


def _dedupe(articulos: list[Paper]) -> list[Paper]:
    """Fusiona duplicados entre fuentes usando DOI o arXiv ID."""
    vistos: dict[str, Paper] = {}
    sin_id: list[Paper] = []

    for a in articulos:
        clave = (a.doi or a.arxiv_id or "").lower()
        if not clave:
            sin_id.append(a)
            continue
        existente = vistos.get(clave)
        if existente is None:
            vistos[clave] = a
        elif existente.citation_count is None and a.citation_count is not None:
            # Se conserva la versión con más metadatos.
            a.abstract = a.abstract or existente.abstract
            vistos[clave] = a

    return [*vistos.values(), *sin_id]


async def search(
    query: str, *, limit: int = 10, sources: tuple[str, ...] = ("arxiv", "semantic_scholar")
) -> dict[str, Any]:
    """Busca en varias fuentes a la vez y fusiona los resultados.

    Si una fuente falla, se informa de cuál y por qué, y se devuelven los
    resultados de las demás. Un fallo parcial se declara; no se disimula.
    """
    tareas = []
    nombres = []
    if "arxiv" in sources:
        tareas.append(search_arxiv(query, limit=limit))
        nombres.append("arxiv")
    if "semantic_scholar" in sources:
        tareas.append(search_semantic_scholar(query, limit=limit))
        nombres.append("semantic_scholar")

    if not tareas:
        raise ValueError(f"Ninguna fuente válida en {sources}.")

    resultados = await asyncio.gather(*tareas, return_exceptions=True)

    articulos: list[Paper] = []
    fallos: dict[str, str] = {}
    consultadas: list[str] = []
    for nombre, resultado in zip(nombres, resultados, strict=True):
        if isinstance(resultado, BaseException):
            fallos[nombre] = str(resultado)
        else:
            articulos.extend(resultado)
            consultadas.append(nombre)

    if not consultadas:
        raise ResearchUnavailable(
            "Ninguna fuente respondió: " + "; ".join(f"{k}: {v}" for k, v in fallos.items())
        )

    unicos = _dedupe(articulos)
    # Los más citados primero; los que no informan citas, al final.
    unicos.sort(key=lambda p: (p.citation_count is None, -(p.citation_count or 0)))

    return {
        "query": query,
        "sources_queried": consultadas,
        "sources_failed": fallos,
        "total": len(unicos),
        "papers": [p.to_dict() for p in unicos[:limit]],
    }


async def patents_search(query: str) -> dict[str, Any]:
    """Búsqueda de patentes: no implementada.

    La versión archivada la fingía con `random.choice()`. Implementarla de
    verdad requiere una API de pago (Google Patents, PatentsView, EPO OPS), que
    es una decisión de producto. Se declara en lugar de inventarse.
    """
    raise NotImplementedError(
        "La búsqueda de patentes no está implementada. Requiere una API externa "
        "(PatentsView es gratuita con registro; Google Patents y EPO OPS son de pago). "
        "Indique cuál desea usar y se implementa."
    )
