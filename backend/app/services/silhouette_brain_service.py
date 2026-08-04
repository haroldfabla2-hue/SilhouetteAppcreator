"""Memoria cognitiva de 4 niveles, respaldada por el paquete `silhouette-brain`.

Este módulo era una fachada con cifras inventadas: declaraba Redis, SQLite,
FastEmbed y Neo4j sin importar ninguno, y `get_stats()` devolvía constantes
escritas a mano. Ahora delega en el paquete real
(https://github.com/haroldfabla2-hue/silhouette-brain), que implementa los
cuatro niveles:

    WORKING (LRU/Redis) → EPISODIC (SQLite) → SEMANTIC (vectores) → DEEP (grafo)

El núcleo funciona sin servicios externos (SQLite + grafo en memoria + embedder
sin dependencias) y sube a Redis/Neo4j/fastembed en cuanto se configuran.

Si el paquete no está instalado, el servicio queda `available == False` y toda
operación lanza `BrainUnavailable`. No se inventan datos: es preferible un error
explícito a una métrica falsa.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger("SilhouetteBrainService")

try:
    from silhouette.errors import MemorySkipped
    from silhouette.reasoning.context_assembler import ContextAssembler
    from silhouette.storage.memory import MemorySystem

    BRAIN_AVAILABLE = True
    _IMPORT_ERROR: str | None = None
except ImportError as exc:  # pragma: no cover - depende del entorno
    BRAIN_AVAILABLE = False
    _IMPORT_ERROR = str(exc)
    MemorySkipped = RuntimeError
    ContextAssembler = None
    MemorySystem = None
    logger.warning(
        "silhouette-brain no está instalado (%s). La memoria cognitiva queda "
        "desactivada; instale con: pip install -e '.[memory]'",
        exc,
    )


class BrainUnavailable(RuntimeError):
    """El paquete silhouette-brain no está disponible en este entorno."""


class SilhouetteBrainService:
    """Adaptador asíncrono sobre `MemorySystem`.

    El paquete es síncrono (SQLite); las operaciones se ejecutan en el executor
    por defecto para no bloquear el bucle de eventos de FastAPI.
    """

    def __init__(self, memory: Any = None, assembler: Any = None) -> None:
        self._memory = memory
        self._assembler = assembler

        if self._memory is None and BRAIN_AVAILABLE:
            self._memory = MemorySystem()
        if self._assembler is None and self._memory is not None and ContextAssembler is not None:
            self._assembler = ContextAssembler(self._memory)

        if self.available:
            logger.info(
                "SilhouetteBrainService activo (embedder=%s)",
                self._memory.stats().get("embedder", "desconocido"),
            )

    @property
    def available(self) -> bool:
        return self._memory is not None

    def _require(self) -> Any:
        if self._memory is None:
            raise BrainUnavailable(
                "silhouette-brain no está instalado. "
                f"Error de importación: {_IMPORT_ERROR}. "
                "Instale con: pip install -e '.[memory]'"
            )
        return self._memory

    async def _run(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))

    # -- ingesta -----------------------------------------------------------
    async def remember_event(
        self,
        content: str,
        importance: float = 0.8,
        *,
        tags: list[str] | None = None,
        source: str = "agent",
    ) -> dict[str, Any]:
        """Indexa un evento en los cuatro niveles. Devuelve el registro real."""
        memory = self._require()
        try:
            record = await self._run(
                memory.remember,
                content,
                importance=importance,
                tags=tags or [],
                source=source,
            )
        except MemorySkipped as exc:
            # El filtro de ruido descartó el contenido: se informa, no se finge.
            return {"success": False, "skipped": True, "reason": str(exc)}

        return {
            "success": True,
            "memory_id": record.id,
            "content": record.content,
            "importance": record.importance,
            "tags": list(record.tags),
            "indexed_layers": ["working", "episodic", "semantic", "deep_graph"],
        }

    # -- recuperación ------------------------------------------------------
    async def recall(self, query: str, *, limit: int = 5, min_score: float = 0.0) -> dict[str, Any]:
        """Búsqueda semántica sobre el nivel vectorial."""
        memory = self._require()
        scored = await self._run(memory.recall, query, limit=limit, min_score=min_score)
        return {
            "query": query,
            "results": [
                {
                    "id": s.record.id,
                    "content": s.record.content,
                    "score": s.score,
                    "importance": s.record.importance,
                    "tags": list(s.record.tags),
                }
                for s in scored
            ],
            "count": len(scored),
        }

    async def assemble_context(
        self,
        query: str,
        token_budget: int = 4000,
        *,
        include_graph: bool = True,
        synthesize: bool = False,
    ) -> dict[str, Any]:
        """Ensambla contexto respetando un presupuesto de tokens.

        El presupuesto se aplica de verdad: el ensamblador poda los registros de
        menor valor hasta encajar, y `tokens_used` es el recuento resultante.
        """
        self._require()
        if self._assembler is None:  # pragma: no cover - defensivo
            raise BrainUnavailable("El ensamblador de contexto no está inicializado.")

        packet = await self._run(
            self._assembler.assemble,
            query,
            token_budget=token_budget,
            include_graph=include_graph,
            synthesize=synthesize,
        )
        return {
            "query": query,
            "token_budget": token_budget,
            "tokens_used": packet.token_estimate,
            "sources_used": list(packet.sources_used),
            "latency_ms": round(packet.latency_ms, 2),
            "semantic": [
                {"content": s.record.content, "score": s.score} for s in packet.semantic
            ],
            "recent": [r.content for r in packet.recent],
            "entities": [{"name": e.name, "type": e.type} for e in packet.entities],
            "graph": [
                {"source": r.source, "target": r.target, "type": r.type} for r in packet.graph
            ],
            "synthesis": packet.synthesis,
        }

    # -- introspección -----------------------------------------------------
    def get_stats(self) -> dict[str, Any]:
        """Estadísticas reales, contadas desde los almacenes."""
        if not self.available:
            return {
                "available": False,
                "reason": "silhouette-brain no instalado",
                "import_error": _IMPORT_ERROR,
            }
        stats = self._memory.stats()
        return {
            "available": True,
            "embedder": stats["embedder"],
            "tiers": {
                "working": stats["working"],
                "episodic": stats["episodic"],
                "semantic": stats["semantic"],
                "deep_graph": {
                    "entities": stats["entities"],
                    "relationships": stats["relationships"],
                },
            },
        }

    def close(self) -> None:
        if self._memory is not None:
            self._memory.close()
