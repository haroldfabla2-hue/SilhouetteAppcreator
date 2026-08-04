"""
API REST con FastAPI
Expone endpoints del sistema multi-agente
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import asyncio
import json
import logging
import os

from app.core import settings
from app.core.llm_router import LLMRouter
from app.orchestrator import MultiAgentOrchestrator
from app.api import tools, memory, tasks, health
from app.api.memory import initialize_memory_manager


# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Inicializar FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Sistema Multi-Agente Superior a MiniMax Agent"
)


# CORS: lista blanca explícita. El comodín junto a allow_credentials=True es
# inválido según la especificación y expone la API a cualquier sitio web.
_DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("SILHOUETTE_CORS_ORIGINS", _DEFAULT_CORS_ORIGINS).split(",")
    if origin.strip() and origin.strip() != "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)


# Modelos de request/response
class TaskRequest(BaseModel):
    """Request para crear una tarea"""
    objetivo: str = Field(..., description="Objetivo a cumplir")
    contexto: Optional[Dict[str, Any]] = Field(None, description="Contexto adicional")
    user_id: Optional[str] = Field(None, description="ID del usuario")
    stream: bool = Field(False, description="Activar streaming de respuesta")


class TaskResponse(BaseModel):
    """Response de una tarea"""
    conversation_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Response de health check"""
    status: str
    version: str
    llm_stats: Optional[Dict[str, Any]] = None


# Estado global
llm_router: Optional[LLMRouter] = None
orchestrator: Optional[MultiAgentOrchestrator] = None


@app.on_event("startup")
async def startup_event():
    """Inicialización al arrancar con VectorStore y servicios completos"""
    global llm_router, orchestrator
    
    logger.info("Iniciando Sistema Multi-Agente Superior con VectorStore RAG...")
    
    try:
        # 1. Inicializar LLM Router
        llm_router = LLMRouter()
        logger.info("✅ LLM Router inicializado")
        
        # 2. Inicializar Embedding Service (HuggingFace)
        from app.services.embedding_service import EmbeddingService
        try:
            embedding_service = EmbeddingService(model_name="all-MiniLM-L6-v2")
            await embedding_service.initialize()
            logger.info("✅ Embedding Service (HuggingFace) inicializado")
        except Exception as e:
            logger.warning(f"⚠️ Embedding Service no disponible: {e}")
            logger.info("🔄 Continuando sin Embedding Service (modo fallback)")
            embedding_service = None
        
        # 3. Inicializar VectorStore con PostgreSQL + pgvector
        from app.services.vector_store import VectorStore
        vector_store = None
        try:
            if embedding_service:
                vector_store = VectorStore(
                    db_url=settings.DATABASE_URL,
                    embedding_service=embedding_service
                )
                await vector_store.initialize()
                logger.info("✅ VectorStore (PostgreSQL + pgvector) inicializado")
            else:
                logger.info("🔄 Saltando VectorStore - Embedding Service no disponible")
        except Exception as e:
            logger.warning(f"⚠️ VectorStore no disponible: {e}")
            logger.info("🔄 Continuando sin VectorStore (modo fallback)")
            vector_store = None
        
        # 4. Inicializar Memory Manager actualizado con servicios disponibles
        from app.agents.memory_manager import MemoryManagerAgent
        memory_manager = MemoryManagerAgent(
            llm_client=llm_router,
            vector_store=vector_store,  # Puede ser None
            embedding_service=embedding_service  # Puede ser None
        )
        if vector_store:
            logger.info("✅ Memory Manager con VectorStore inicializado")
        else:
            logger.info("✅ Memory Manager (modo fallback sin VectorStore) inicializado")
        
        # 5. Inicializar Redis (básico por ahora)
        try:
            import redis.asyncio as redis
            redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            await redis_client.ping()
            logger.info("✅ Redis conectado")
        except Exception as e:
            logger.warning(f"⚠️ Redis no disponible: {e}")
            redis_client = None
        
        # 6. Inicializar Orquestador con todos los servicios
        orchestrator = MultiAgentOrchestrator(
            llm_router=llm_router,
            redis_client=redis_client,
            vector_store=vector_store
        )
        logger.info("✅ MultiAgent Orchestrator inicializado")
        
        # 7. Inicializar TaskManager y TaskOrchestratorIntegrator
        from app.services.task_manager import task_manager
        from app.services.task_orchestrator_integrator import initialize_task_orchestrator_integrator
        initialize_task_orchestrator_integrator(task_manager, orchestrator)
        logger.info("✅ TaskManager y TaskOrchestratorIntegrator inicializados")
        
        # 8. Actualizar el memory manager global en la API
        from app.api.memory import initialize_memory_manager
        initialize_memory_manager(
            llm_client=llm_router,
            vector_store=vector_store,  # Puede ser None
            embedding_service=embedding_service  # Puede ser None
        )
        
        logger.info("🎉 Sistema completo inicializado exitosamente")
        logger.info("📊 Servicios activos:")
        logger.info("   - LLM Router con modelos minimax-m2 y llama-3.3-70b")
        logger.info("   - Embedding Service (HuggingFace all-MiniLM-L6-v2)")
        logger.info("   - VectorStore (PostgreSQL + pgvector)")
        logger.info("   - Memory Manager con búsqueda semántica")
        logger.info("   - Redis (cache y sesiones)")
        logger.info("   - Multi-Agent Orchestrator")
        
    except Exception as e:
        logger.error(f"❌ Error durante inicialización: {e}")
        import traceback
        traceback.print_exc()
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al cerrar"""
    global llm_router
    
    logger.info("Cerrando Sistema Multi-Agente Superior...")
    
    if llm_router:
        await llm_router.close()
    
    logger.info("Sistema cerrado correctamente")


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check principal"""
    return {
        "status": "running",
        "version": settings.VERSION,
        "llm_stats": llm_router.get_stats() if llm_router else None
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check detallado"""
    
    health_status = {
        "status": "healthy",
        "version": settings.VERSION,
        "llm_stats": None
    }
    
    if llm_router:
        health_status["llm_stats"] = llm_router.get_stats()
    
    if orchestrator is None:
        health_status["status"] = "degraded"
    
    return health_status


@app.post("/api/v1/tasks", response_model=TaskResponse)
async def create_task(request: TaskRequest):
    """
    Crea y ejecuta una tarea con el sistema multi-agente
    
    - **objetivo**: Descripción de lo que se quiere lograr
    - **contexto**: Información adicional opcional
    - **user_id**: Identificador del usuario (opcional)
    - **stream**: Si activar streaming (no implementado aún)
    """
    
    if orchestrator is None:
        raise HTTPException(
            status_code=503,
            detail="Orquestador no inicializado"
        )
    
    try:
        logger.info(f"Nueva tarea: {request.objetivo[:100]}")
        
        # Procesar request con orquestador
        result = await orchestrator.process_request(
            objetivo=request.objetivo,
            contexto=request.contexto,
            user_id=request.user_id
        )
        
        return TaskResponse(
            conversation_id=result["conversation_id"],
            status=result["status"],
            result=result.get("result"),
            error=result.get("error"),
            metadata=result.get("metadata")
        )
        
    except Exception as e:
        logger.exception("Error procesando tarea")
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando tarea: {str(e)}"
        )


@app.get("/api/v1/tasks/{conversation_id}")
async def get_task_status(conversation_id: str):
    """
    Obtiene el estado de una tarea por su conversation_id
    """
    
    # TODO: Implementar recuperación de estado desde Redis
    
    return {
        "conversation_id": conversation_id,
        "status": "not_implemented",
        "message": "Consulta de estado no implementada aún"
    }


@app.get("/api/v1/stats")
async def get_system_stats():
    """
    Obtiene estadísticas del sistema
    """
    
    stats = {
        "system": {
            "version": settings.VERSION,
            "status": "running"
        }
    }
    
    if llm_router:
        stats["llm"] = llm_router.get_stats()
    
    if orchestrator:
        stats["orchestrator"] = {
            "active_sessions": len(orchestrator.active_sessions),
            "agents": {
                "reasoner": orchestrator.reasoner.agent_id,
                "planner": orchestrator.planner.agent_id,
                "verifier": orchestrator.verifier.agent_id,
                "memory_manager": orchestrator.memory_manager.agent_id,
                "executors": list(orchestrator.executors.keys())
            }
        }
    
    return stats


@app.post("/api/v1/llm/test")
async def test_llm(prompt: str = "Hola, ¿cómo estás?"):
    """
    Endpoint de prueba para el LLM Router
    """
    
    if llm_router is None:
        raise HTTPException(
            status_code=503,
            detail="LLM Router no inicializado"
        )
    
    try:
        response = await llm_router.chat_completion(prompt)
        
        return {
            "prompt": prompt,
            "response": response,
            "stats": llm_router.get_stats()
        }
        
    except Exception as e:
        logger.exception("Error en test LLM")
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


@app.post("/api/v1/rag/test")
async def test_rag_system(
    query: str = "test query",
    content: str = "This is a test content for RAG system"
):
    """
    Endpoint de prueba del sistema RAG completo
    Almacena contenido de prueba y luego lo busca
    """
    
    try:
        from app.api.memory import get_memory_manager
        
        logger.info("Probando sistema RAG...")
        
        # Obtener Memory Manager
        memory_mgr = get_memory_manager()
        
        # Paso 1: Almacenar contenido de prueba
        test_source = {
            "title": "Test Document",
            "source_type": "test",
            "tags": ["test", "rag"]
        }
        
        store_result = await memory_mgr.store_insight(
            insight=content,
            metadata=test_source
        )
        
        if not store_result.get("success"):
            raise Exception(f"Error almacenando: {store_result.get('error')}")
        
        # Paso 2: Buscar el contenido
        search_result = await memory_mgr.search_in_memory(
            query=query,
            limit=5
        )
        
        return {
            "status": "success",
            "test_query": query,
            "stored_content": content,
            "store_result": store_result,
            "search_result": search_result,
            "rag_system": "operational"
        }
        
    except Exception as e:
        logger.exception("Error en test RAG")
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


# Incluir routers de endpoints
app.include_router(tools.router, prefix="/api/v1")
app.include_router(memory.router, prefix="/api/v1") 
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
