"""
Endpoints para búsqueda en memoria/base de datos RAG
/api/v1/memory/search - Búsqueda semántica real
/api/v1/memory/store - Almacenamiento de documentos
"""
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..agents.memory_manager import MemoryManagerAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/memory", tags=["memory"])

# Estado global del MemoryManagerAgent
memory_manager: MemoryManagerAgent | None = None

def get_memory_manager() -> MemoryManagerAgent:
    """Obtiene instancia del MemoryManagerAgent"""
    global memory_manager
    if memory_manager is None:
        raise HTTPException(
            status_code=503,
            detail="Memory Manager no inicializado"
        )
    return memory_manager

def initialize_memory_manager(llm_client=None, vector_store=None, embedding_service=None):
    """Inicializa el MemoryManagerAgent global con servicios completos"""
    global memory_manager
    memory_manager = MemoryManagerAgent(
        llm_client=llm_client,
        vector_store=vector_store,
        embedding_service=embedding_service
    )
    logger.info("Memory Manager actualizado en API global")

# Modelos de request/response
class MemorySearchRequest(BaseModel):
    """Request para búsqueda en memoria"""
    query: str = Field(..., description="Consulta de búsqueda")
    search_type: Literal["semantic", "keyword", "hybrid"] = Field("hybrid", description="Tipo de búsqueda")
    limit: int = Field(10, description="Número máximo de resultados", ge=1, le=100)
    time_range: str | None = Field(None, description="Rango temporal (1h, 1d, 1w, 1m, all)")
    conversation_id: str | None = Field(None, description="Filtrar por conversación específica")
    content_type: str | None = Field(None, description="Filtrar por tipo de contenido")
    user_id: str | None = Field(None, description="Filtrar por usuario")


class MemorySearchResponse(BaseModel):
    """Response de búsqueda en memoria"""
    query: str
    search_type: str
    total_results: int
    results: list[dict[str, Any]]
    search_metadata: dict[str, Any]
    execution_time_ms: int


class MemoryStoreRequest(BaseModel):
    """Request para almacenar información en memoria"""
    content: str = Field(..., description="Contenido a almacenar")
    content_type: str = Field("text", description="Tipo de contenido")
    conversation_id: str | None = Field(None, description="ID de conversación")
    user_id: str | None = Field(None, description="ID del usuario")
    metadata: dict[str, Any] | None = Field(None, description="Metadatos adicionales")
    tags: list[str] | None = Field(None, description="Etiquetas")


class MemoryStoreResponse(BaseModel):
    """Response de almacenamiento en memoria"""
    memory_id: str
    status: str
    stored_at: str
    metadata: dict[str, Any]


class MemoryStatsResponse(BaseModel):
    """Response con estadísticas de memoria"""
    total_memories: int
    memories_by_type: dict[str, int]
    memories_by_user: dict[str, int]
    recent_activity: dict[str, Any]
    storage_stats: dict[str, Any]


class StoreDocumentRequest(BaseModel):
    """Request para almacenar documento"""
    content: str = Field(..., description="Contenido del documento a almacenar")
    title: str = Field(..., description="Título del documento")
    source_type: str = Field("manual_entry", description="Tipo de fuente")
    source_url: str | None = Field(None, description="URL de la fuente")
    source_file: str | None = Field(None, description="Archivo de origen")
    tags: list[str] | None = Field(None, description="Etiquetas")
    chunking_strategy: str = Field("semantic", description="Estrategia de chunking")
    max_tokens: int = Field(500, description="Máximo tokens por chunk")


@router.get("/search", response_model=MemorySearchResponse)
async def search_memory_get(
    query: str = Query(..., description="Términos de búsqueda"),
    search_type: str = Query("semantic", description="Tipo de búsqueda: semantic, keyword, hybrid"),
    limit: int = Query(10, description="Número máximo de resultados", ge=1, le=100),
    time_range: str | None = Query(None, description="Rango temporal: 1h, 1d, 1w, 1m, all"),
    conversation_id: str | None = Query(None, description="Filtrar por conversación"),
    content_type: str | None = Query(None, description="Filtrar por tipo de contenido"),
    user_id: str | None = Query(None, description="Filtrar por usuario")
):
    """Alias GET para búsqueda semántica"""
    return await search_memory_semantic(
        query=query,
        search_type=search_type,
        limit=limit,
        time_range=time_range,
        conversation_id=conversation_id,
        content_type=content_type,
        user_id=user_id
    )

@router.post("/search", response_model=MemorySearchResponse)
async def search_memory_semantic(
    query: str = Query(..., description="Términos de búsqueda"),
    search_type: str = Query("semantic", description="Tipo de búsqueda: semantic, keyword, hybrid"),
    limit: int = Query(10, description="Número máximo de resultados", ge=1, le=100),
    time_range: str | None = Query(None, description="Rango temporal: 1h, 1d, 1w, 1m, all"),
    conversation_id: str | None = Query(None, description="Filtrar por conversación"),
    content_type: str | None = Query(None, description="Filtrar por tipo de contenido"),
    user_id: str | None = Query(None, description="Filtrar por usuario")
):
    """
    Busca en la base de datos de memoria usando búsqueda semántica RAG

    - **query**: Términos de búsqueda
    - **search_type**: Tipo de búsqueda (semantic, keyword, hybrid)
    - **limit**: Número máximo de resultados (1-100)
    - **time_range**: Filtro temporal (1h, 1d, 1w, 1m, all)
    - **conversation_id**: Filtrar por conversación específica
    - **content_type**: Filtrar por tipo de contenido
    - **user_id**: Filtrar por usuario específico
    """

    start_time = datetime.now()

    try:
        logger.info(f"Búsqueda semántica en memoria: '{query}' ({search_type})")

        # Obtener instancia del MemoryManagerAgent
        memory_mgr = get_memory_manager()

        # Construir filtros para la búsqueda
        filters = {}
        if time_range:
            # Agregar filtro temporal a metadata si es necesario
            pass
        if conversation_id:
            filters["conversation_id"] = conversation_id
        if user_id:
            filters["user_id"] = user_id
        if content_type:
            filters["source_type"] = content_type

        # Realizar búsqueda semántica usando VectorStore si está disponible
        try:
            if memory_mgr.vector_store:
                search_results = await memory_mgr.search_knowledge(
                    query=query,
                    limit=limit,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    content_type=content_type,
                    time_range=time_range
                )
                results = search_results
            else:
                # Fallback a búsqueda en cache local
                search_results = await memory_mgr.search_in_memory(
                    query=query,
                    limit=limit,
                    filters=filters
                )
                results = search_results.get("results", []) if search_results.get("success") else []
        except Exception as e:
            logger.warning(f"VectorStore no disponible, usando fallback: {e}")
            # Fallback a búsqueda en cache local
            search_results = await memory_mgr.search_in_memory(
                query=query,
                limit=limit,
                filters=filters
            )
            results = search_results.get("results", []) if search_results.get("success") else []

        # Búsquedas adicionales para tipos específicos
        if search_type == "hybrid":
            # Búsqueda híbrida: primero semántica, luego filtrado por keywords
            if results and memory_mgr.vector_store:
                search_results = await memory_mgr.search_knowledge(
                    query=query,
                    limit=limit,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    content_type=content_type,
                    time_range=time_range
                )

                results = search_results

                # Aplicar filtrado por palabras clave
                if results:
                    results = _filter_by_keywords(results, query)
        else:  # keyword search
            # Búsqueda por palabras clave usando VectorStore
            if memory_mgr.vector_store:
                search_results = await memory_mgr.search_knowledge(
                    query=query,
                    limit=limit * 2,  # Obtener más para filtrar
                    user_id=user_id,
                    conversation_id=conversation_id,
                    content_type=content_type,
                    time_range=time_range
                )

                results = _filter_by_keywords(search_results, query)


        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

        # Preparar resultados para el response
        formatted_results = []
        for result in results:
            # Los resultados del VectorStore ya tienen el formato correcto
            content = result.get("content", "")

            formatted_results.append({
                "memory_id": result.get("id", ""),
                "content": content,
                "title": result.get("title", ""),
                "content_type": result.get("content_type", "text"),
                "relevance_score": result.get("similarity_score", 0.0),
                "conversation_id": result.get("metadata", {}).get("conversation_id"),
                "user_id": result.get("metadata", {}).get("user_id"),
                "created_at": result.get("created_at", ""),
                "metadata": result.get("metadata", {}),
                "result_type": result.get("result_type", "document_chunk")
            })

        return MemorySearchResponse(
            query=query,
            search_type=search_type,
            total_results=len(formatted_results),
            results=formatted_results,
            search_metadata={
                "filters": {
                    "time_range": time_range,
                    "conversation_id": conversation_id,
                    "content_type": content_type,
                    "user_id": user_id
                },
                "strategy": search_type,
                "semantic_threshold": 0.7,
                "rag_enabled": True,
                "embeddings_model": "sentence-transformers/all-MiniLM-L6-v2"
            },
            execution_time_ms=execution_time
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error en búsqueda de memoria")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/store", response_model=MemoryStoreResponse)
async def store_memory(request: MemoryStoreRequest):
    """
    Almacena información en la base de datos de memoria

    - **content**: Contenido a almacenar
    - **content_type**: Tipo de contenido (text, code, document, result, etc.)
    - **conversation_id**: ID de conversación (opcional)
    - **user_id**: ID del usuario (opcional)
    - **metadata**: Metadatos adicionales
    - **tags**: Etiquetas para categorización
    """

    try:
        memory_id = f"mem_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(request.content) % 10000:04d}"

        logger.info(f"Almacenando memoria: {memory_id}")

        almacenado = await _store_memory(memory_id, request)

        # El estado refleja lo que ocurrió: el filtro de ruido puede descartar
        # el contenido, y antes se respondía "stored" igualmente.
        return MemoryStoreResponse(
            memory_id=memory_id,
            status="stored" if almacenado else "skipped",
            stored_at=datetime.now().isoformat(),
            metadata={
                "stored": almacenado,
                "content_type": request.content_type,
                "content_length": len(request.content),
                "conversation_id": request.conversation_id,
                "user_id": request.user_id,
                "tags": request.tags or [],
                "storage_method": "four_tier_memory" if almacenado else "none",
            }
        )

    except Exception as e:
        logger.exception("Error almacenando memoria")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/stats", response_model=MemoryStatsResponse)
async def get_memory_stats():
    """
    Obtiene estadísticas de la base de datos de memoria
    """

    try:
        logger.info("Obteniendo estadísticas de memoria")

        # Simular consulta de estadísticas
        stats = await _get_memory_statistics()

        return MemoryStatsResponse(**stats)

    except Exception as e:
        logger.exception("Error obteniendo estadísticas de memoria")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.delete("/clear")
async def clear_memory(
    user_id: str | None = Query(None, description="Limpiar memorias de usuario específico"),
    conversation_id: str | None = Query(None, description="Limpiar memorias de conversación específica"),
    older_than: str | None = Query(None, description="Limpiar memorias más antiguas que (ej: 30d)")
):
    """
    Limpia memorias según criterios especificados

    - **user_id**: Limpiar memorias de usuario específico
    - **conversation_id**: Limpiar memorias de conversación específica
    - **older_than**: Limpiar memorias más antiguas que el período especificado
    """

    try:
        logger.info(f"Limpiando memoria - user: {user_id}, conv: {conversation_id}, older: {older_than}")

        # Simular limpieza
        cleared_count = await _clear_memory(user_id, conversation_id, older_than)

        return {
            "status": "cleared",
            "cleared_count": cleared_count,
            "cleared_at": datetime.now().isoformat(),
            "criteria": {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "older_than": older_than
            }
        }

    except Exception as e:
        logger.exception("Error limpiando memoria")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# Funciones auxiliares
def _build_time_filter(time_range: str | None) -> datetime | None:
    """Construye filtro temporal basado en el rango especificado"""

    if not time_range or time_range == "all":
        return None

    now = datetime.now()

    if time_range == "1h":
        return now - timedelta(hours=1)
    elif time_range == "1d":
        return now - timedelta(days=1)
    elif time_range == "1w":
        return now - timedelta(weeks=1)
    elif time_range == "1m":
        return now - timedelta(days=30)

    return None


# Estas cuatro funciones devolvían datos inventados: resultados de búsqueda
# fabricados a partir de la consulta, `True` sin almacenar nada, estadísticas
# escritas a mano (1247 memorias, 245,7 MB) y conteos de borrado ficticios.
# Ahora todas delegan en SilhouetteBrainService, que sí persiste.

_brain_service: Any = None


def _get_brain() -> Any:
    """Servicio de memoria compartido, creado bajo demanda."""
    global _brain_service
    if _brain_service is None:
        from backend.app.services.silhouette_brain_service import SilhouetteBrainService

        _brain_service = SilhouetteBrainService()
    return _brain_service


async def _perform_memory_search(
    query: str,
    search_type: str,
    limit: int,
    time_filter: datetime | None,
    conversation_id: str | None,
    content_type: str | None,
    user_id: str | None
) -> list[dict[str, Any]]:
    """Busca en la memoria semántica real."""
    brain = _get_brain()
    if not brain.available:
        raise HTTPException(
            status_code=503,
            detail=(
                "La memoria cognitiva no está disponible. "
                "Instale con: pip install -e '.[memory]'"
            ),
        )

    resultado = await brain.recall(query, limit=limit)
    memorias: list[dict[str, Any]] = []

    for item in resultado["results"]:
        registro = {
            "memory_id": item["id"],
            "content": item["content"],
            "content_type": content_type or "text",
            "relevance_score": round(item["score"], 4),
            "conversation_id": conversation_id,
            "user_id": user_id,
            "created_at": None,
            "metadata": {
                "importance": item["importance"],
                "tags": item["tags"],
            },
        }
        # El filtro por etiquetas es la vía real de acotar por conversación.
        if conversation_id and conversation_id not in item["tags"]:
            continue
        memorias.append(registro)

    return memorias


async def _store_memory(memory_id: str, request: MemoryStoreRequest) -> bool:
    """Almacena en los cuatro niveles de memoria. Devuelve si se indexó."""
    brain = _get_brain()
    if not brain.available:
        raise HTTPException(
            status_code=503,
            detail="La memoria cognitiva no está disponible; no se almacenó nada.",
        )

    etiquetas = list(getattr(request, "tags", None) or [])
    for atributo in ("conversation_id", "user_id", "content_type"):
        valor = getattr(request, atributo, None)
        if valor:
            etiquetas.append(str(valor))

    resultado = await brain.remember_event(
        request.content,
        importance=getattr(request, "importance", 0.6),
        tags=etiquetas,
        source="api:memory",
    )
    if not resultado.get("success"):
        # El filtro de ruido descartó el contenido: se informa, no se finge.
        logger.info("Memoria descartada por el filtro: %s", resultado.get("reason"))
        return False

    logger.info("Memoria almacenada: %s", resultado["memory_id"])
    return True


async def _get_memory_statistics() -> dict[str, Any]:
    """Estadísticas contadas desde los almacenes reales."""
    brain = _get_brain()
    stats = brain.get_stats()
    if not stats.get("available"):
        return {
            "available": False,
            "reason": stats.get("reason", "memoria no disponible"),
            "total_memories": 0,
        }

    niveles = stats["tiers"]
    return {
        "available": True,
        "embedder": stats["embedder"],
        "total_memories": niveles["episodic"],
        "memories_by_tier": {
            "working": niveles["working"],
            "episodic": niveles["episodic"],
            "semantic": niveles["semantic"],
        },
        "knowledge_graph": niveles["deep_graph"],
    }


async def _clear_memory(
    user_id: str | None,
    conversation_id: str | None,
    older_than: str | None
) -> int:
    """El borrado selectivo aún no está implementado.

    Se declara en lugar de devolver un conteo inventado: antes esta función
    respondía 15, 234 o 89 elementos «limpiados» sin tocar nada.
    """
    raise HTTPException(
        status_code=501,
        detail=(
            "El borrado selectivo de memoria no está implementado. "
            "El nivel episódico usa poda por antigüedad y el motor Janitor "
            "resuelve contradicciones; no hay borrado por usuario ni conversación."
        ),
    )


# Funciones auxiliares para búsquedas avanzadas
async def _keyword_search(
    memory_mgr: MemoryManagerAgent,
    query: str,
    limit: int,
    filters: dict[str, Any]
) -> list[dict[str, Any]]:
    """Búsqueda simple por palabras clave"""

    # Primero obtener todos los resultados semánticos
    semantic_results = await memory_mgr.retrieve_relevant(
        query=query,
        limit=limit * 2,  # Obtener más resultados para filtrar
        memory_type=filters.get("memory_type"),
        conversation_id=filters.get("conversation_id")
    )

    if not semantic_results.get("success"):
        return []

    results = semantic_results.get("results", [])

    # Filtrar por palabras clave
    return _filter_by_keywords(results, query)[:limit]


def _filter_by_keywords(results: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    """Filtra resultados por palabras clave de la query"""

    # Extraer palabras clave de la query
    keywords = set(re.findall(r'\b\w+\b', query.lower()))

    filtered = []

    for result in results:
        # Extraer texto del contenido
        content = result.get("content", {})
        if isinstance(content, dict):
            text = content.get("text", json.dumps(content))
        else:
            text = str(content)

        # Contar coincidencias de palabras clave
        text_lower = text.lower()
        matches = 0

        for keyword in keywords:
            if keyword in text_lower:
                matches += 1

        # Calcular score de palabras clave
        if keywords:
            keyword_score = matches / len(keywords)
        else:
            keyword_score = 0

        # Combinar con score original
        original_score = result.get("score", 0.0)
        combined_score = (original_score * 0.6) + (keyword_score * 0.4)

        result["keyword_score"] = keyword_score
        result["combined_score"] = combined_score

        filtered.append(result)

    # Ordenar por score combinado
    filtered.sort(key=lambda x: x.get("combined_score", 0.0), reverse=True)

    return filtered


@router.post("/store-document")
async def store_document_endpoint(request: StoreDocumentRequest):
    """
    Almacena un documento completo con chunking inteligente

    - **content**: Contenido del documento
    - **title**: Título del documento
    - **source_type**: Tipo de fuente (document, web_page, manual_entry)
    - **source_url**: URL de origen si aplica
    - **source_file**: Archivo de origen si aplica
    - **tags**: Etiquetas para categorización
    - **chunking_strategy**: Estrategia de chunking (semantic, fixed_size, sentence_based)
    - **max_tokens**: Máximo tokens por chunk
    """

    try:
        logger.info(f"Almacenando documento: {request.title}")

        # Obtener instancia del MemoryManagerAgent
        memory_mgr = get_memory_manager()

        # Preparar metadatos
        metadata = {
            "source_type": request.source_type,
            "source_url": request.source_url,
            "source_file": request.source_file,
            "tags": request.tags or [],
            "chunking_strategy": request.chunking_strategy,
            "max_tokens": request.max_tokens
        }

        # Almacenar documento usando VectorStore si está disponible
        try:
            if memory_mgr.vector_store:
                document_id = await memory_mgr.store_knowledge(
                    title=request.title,
                    content=request.content,
                    content_type=request.source_type,
                    metadata=metadata
                )
            else:
                # Fallback usando store_insight
                insight_result = await memory_mgr.store_insight(
                    insight=f"[{request.title}] {request.content}",
                    metadata=metadata
                )
                document_id = insight_result.get("memory_id", f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        except Exception as e:
            logger.warning(f"VectorStore no disponible, usando fallback: {e}")
            # Fallback usando store_insight
            insight_result = await memory_mgr.store_insight(
                insight=f"[{request.title}] {request.content}",
                metadata=metadata
            )
            document_id = insight_result.get("memory_id", f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

        return {
            "status": "stored",
            "document_id": document_id,
            "title": request.title,
            "content_type": request.source_type,
            "content_length": len(request.content),
            "strategy_used": request.chunking_strategy,
            "stored_at": datetime.now().isoformat(),
            "memory_agent_id": memory_mgr.agent_id
        }

    except Exception as e:
        logger.exception("Error almacenando documento")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# NOTA: aquí había una segunda ruta GET /stats. FastAPI resuelve con la
# primera coincidencia, así que era código muerto desde su creación: nunca
# se ejecutó. La ruta viva es `get_memory_stats` más arriba.
