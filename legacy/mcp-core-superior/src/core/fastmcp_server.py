"""
FastMCP Server Principal para MCP Core Superior
Integra los 5 agentes especializados como herramientas MCP
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, AsyncIterator
from datetime import datetime

from .fastmcp_local import FastMCP, Context

from .core.config import settings, get_environment_config
from .core.exceptions import handle_exceptions, MCPCoreException
from .agents import (
    ReasonerAgentWrapper,
    PlannerAgentWrapper,
    ExecutorAgentWrapper,
    VerifierAgentWrapper,
    MemoryManagerAgentWrapper
)
from .orchestrator.multi_agent_orchestrator import MultiAgentOrchestrator
from .orchestrator.streaming_engine import StreamingEngine
from .services.contextforge_client import ContextForgeClient
from .services.vector_store_client import VectorStoreClient
from .services.auth_service import AuthService
from .utils.logging_config import setup_logging


class MCPCoreServer:
    """
    Servidor MCP Core Superior
    
    Integra todos los componentes del sistema:
    - Wrappers de agentes MCP
    - Orquestador multi-agente
    - Motor de streaming
    - Servicios de integración
    """
    
    def __init__(self):
        # Setup logging
        self.logger = logging.getLogger("mcp.core.server")
        self._setup_logging()
        
        # Inicializar FastMCP
        self.mcp = FastMCP("MCP Core Superior")
        
        # Servicios principales
        self.contextforge_client = ContextForgeClient()
        self.vector_store_client = VectorStoreClient()
        self.auth_service = AuthService()
        
        # Agentes
        self.reasoner_agent = ReasonerAgentWrapper()
        self.planner_agent = PlannerAgentWrapper()
        self.executor_agent = ExecutorAgentWrapper()
        self.verifier_agent = VerifierAgentWrapper()
        self.memory_manager_agent = MemoryManagerAgentWrapper()
        
        # Orquestador y streaming
        self.orchestrator = MultiAgentOrchestrator()
        self.streaming_engine = StreamingEngine()
        
        # Estado del servidor
        self.is_initialized = False
        self._init_lock = asyncio.Lock()
        
        self.logger.info("MCPCoreServer inicializado")
    
    def _setup_logging(self) -> None:
        """Configurar logging del servidor"""
        log_config = get_environment_config()
        setup_logging(
            level=log_config["log_level"],
            format=log_config.get("log_format", "json"),
            file=log_config.get("log_file")
        )
    
    async def initialize(self) -> None:
        """Inicializar todos los componentes del servidor"""
        if self.is_initialized:
            return
        
        async with self._init_lock:
            if self.is_initialized:
                return
            
            try:
                self.logger.info("Iniciando inicialización del MCPCoreServer...")
                
                # Inicializar servicios
                await self.contextforge_client.initialize()
                await self.vector_store_client.initialize()
                await self.auth_service.initialize()
                
                # Inicializar agentes
                await self.reasoner_agent.ensure_initialized()
                await self.planner_agent.ensure_initialized()
                await self.executor_agent.ensure_initialized()
                await self.verifier_agent.ensure_initialized()
                await self.memory_manager_agent.ensure_initialized()
                
                # Inicializar orquestador y streaming
                await self.orchestrator.initialize()
                await self.streaming_engine.initialize()
                
                # Registrar herramientas MCP
                self._register_mcp_tools()
                
                self.is_initialized = True
                self.logger.info("MCPCoreServer inicializado exitosamente")
                
            except Exception as e:
                self.logger.error(f"Error durante inicialización: {e}")
                raise MCPCoreException(
                    message=f"Error inicializando MCPCoreServer: {str(e)}",
                    error_code="INITIALIZATION_ERROR",
                    original_error=e
                )
    
    def _register_mcp_tools(self) -> None:
        """Registrar todas las herramientas MCP"""
        self.logger.info("Registrando herramientas MCP...")
        
        # === HERRAMIENTAS INDIVIDUALES DE AGENTES ===
        
        # ReasonerAgent Tools
        @self.mcp.tool
        async def reasoner_analyze_intent(
            objective: str,
            context: Optional[Dict[str, Any]] = None,
            conversation_id: Optional[str] = None,
            user_id: Optional[str] = None
        ) -> Dict[str, Any]:
            """Analiza intención del usuario y define estrategia inicial"""
            await self.initialize()
            
            return await self.reasoner_agent.analyze_intent(
                objective=objective,
                context=context,
                conversation_id=conversation_id,
                user_id=user_id
            )
        
        # PlannerAgent Tools
        @self.mcp.tool
        async def planner_create_execution_plan(
            objective: str,
            analysis: Dict[str, Any],
            constraints: Optional[Dict[str, Any]] = None,
            parallel_agents: bool = True
        ) -> Dict[str, Any]:
            """Crea plan de ejecución con descomposición de tareas"""
            await self.initialize()
            
            return await self.planner_agent.create_execution_plan(
                objective=objective,
                analysis=analysis,
                constraints=constraints,
                parallel_agents=parallel_agents
            )
        
        # ExecutorAgent Tools
        @self.mcp.tool
        async def executor_execute_tasks(
            plan: Dict[str, Any],
            objective: str,
            max_concurrent: int = 3,
            timeout_seconds: int = 300
        ) -> Dict[str, Any]:
            """Ejecuta herramientas según el plan del PlannerAgent"""
            await self.initialize()
            
            return await self.executor_agent.execute_tasks(
                plan=plan,
                objective=objective,
                max_concurrent=max_concurrent,
                timeout_seconds=timeout_seconds
            )
        
        # VerifierAgent Tools
        @self.mcp.tool
        async def verifier_validate_results(
            execution_results: Dict[str, Any],
            validation_criteria: List[str],
            trajectory: Optional[List[Dict[str, Any]]] = None
        ) -> Dict[str, Any]:
            """Valida calidad y consistencia de resultados"""
            await self.initialize()
            
            return await self.verifier_agent.validate_results(
                execution_results=execution_results,
                validation_criteria=validation_criteria,
                trajectory=trajectory
            )
        
        # MemoryManagerAgent Tools
        @self.mcp.tool
        async def memory_manage(
            operation: str,
            content: Optional[str] = None,
            query: Optional[str] = None,
            conversation_id: Optional[str] = None,
            user_id: Optional[str] = None
        ) -> Dict[str, Any]:
            """Gestiona memoria semántica y contexto"""
            await self.initialize()
            
            return await self.memory_manager_agent.manage_memory(
                operation=operation,
                content=content,
                query=query,
                conversation_id=conversation_id,
                user_id=user_id
            )
        
        # === ORQUESTADOR MULTI-AGENTE ===
        
        @self.mcp.tool
        async def orchestrate_multitask(
            objective: str,
            context: Optional[Dict[str, Any]] = None,
            user_id: Optional[str] = None,
            streaming_enabled: bool = True,
            quality_threshold: float = 0.8
        ) -> Dict[str, Any]:
            """Ejecuta flujo multi-agente completo: Reasoner → Planner → Executor → Verifier"""
            await self.initialize()
            
            return await self.orchestrator.orchestrate_task(
                objective=objective,
                context=context or {},
                user_id=user_id,
                streaming_enabled=streaming_enabled,
                quality_threshold=quality_threshold
            )
        
        # === HERRAMIENTAS DE ESTADO Y MONITOREO ===
        
        @self.mcp.tool
        async def get_agent_status() -> Dict[str, Any]:
            """Obtiene estado actual de todos los agentes"""
            await self.initialize()
            
            return {
                "reasoner": self.reasoner_agent.get_status(),
                "planner": self.planner_agent.get_status(),
                "executor": self.executor_agent.get_status(),
                "verifier": self.verifier_agent.get_status(),
                "memory_manager": self.memory_manager_agent.get_status(),
                "orchestrator": await self.orchestrator.get_status(),
                "streaming_engine": await self.streaming_engine.get_status()
            }
        
        @self.mcp.tool
        async def get_task_progress(task_id: str) -> Dict[str, Any]:
            """Obtiene progreso de una tarea específica"""
            await self.initialize()
            
            return await self.orchestrator.get_task_progress(task_id)
        
        @self.mcp.tool
        async def cancel_task(task_id: str) -> Dict[str, Any]:
            """Cancela una tarea en ejecución"""
            await self.initialize()
            
            return await self.orchestrator.cancel_task(task_id)
        
        # === STREAMING TOOLS ===
        
        @self.mcp.tool
        async def stream_task_updates(task_id: str, duration: int = 300) -> str:
            """Stream de updates en tiempo real para una tarea"""
            await self.initialize()
            
            # Retornar ID del stream para que el cliente pueda conectarse
            stream_id = await self.streaming_engine.create_stream(task_id, duration)
            return f"stream://{stream_id}"
        
        # === UTILITY TOOLS ===
        
        @self.mcp.tool
        async def health_check() -> Dict[str, Any]:
            """Health check completo del sistema"""
            await self.initialize()
            
            health_status = {
                "server_status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "components": {}
            }
            
            try:
                # Health check de agentes
                health_status["components"]["agents"] = {
                    "reasoner": await self.reasoner_agent.health_check(),
                    "planner": await self.planner_agent.health_check(),
                    "executor": await self.executor_agent.health_check(),
                    "verifier": await self.verifier_agent.health_check(),
                    "memory_manager": await self.memory_manager_agent.health_check()
                }
                
                # Health check de servicios
                health_status["components"]["services"] = {
                    "contextforge": await self.contextforge_client.health_check(),
                    "vector_store": await self.vector_store_client.health_check(),
                    "auth_service": await self.auth_service.health_check()
                }
                
                # Health check de orchestrator y streaming
                health_status["components"]["orchestrator"] = await self.orchestrator.health_check()
                health_status["components"]["streaming"] = await self.streaming_engine.health_check()
                
                # Verificar estado general
                all_healthy = all(
                    comp.get("status") == "healthy" 
                    for comp in health_status["components"].values()
                )
                
                if not all_healthy:
                    health_status["server_status"] = "degraded"
                
            except Exception as e:
                health_status["server_status"] = "unhealthy"
                health_status["error"] = str(e)
                self.logger.error(f"Error en health check: {e}")
            
            return health_status
        
        @self.mcp.tool
        async def reset_agent_metrics(agent_name: Optional[str] = None) -> Dict[str, Any]:
            """Resetear métricas de agentes"""
            await self.initialize()
            
            if agent_name:
                agent_map = {
                    "reasoner": self.reasoner_agent,
                    "planner": self.planner_agent,
                    "executor": self.executor_agent,
                    "verifier": self.verifier_agent,
                    "memory_manager": self.memory_manager_agent
                }
                
                if agent_name in agent_map:
                    agent_map[agent_name].reset_metrics()
                    return {"status": "success", "message": f"Métricas de {agent_name} reseteadas"}
                else:
                    raise MCPCoreException(
                        message=f"Agente {agent_name} no encontrado",
                        error_code="INVALID_REQUEST"
                    )
            else:
                # Reset all agents
                for agent in agent_map.values():
                    agent.reset_metrics()
                return {"status": "success", "message": "Métricas de todos los agentes reseteadas"}
        
        @self.mcp.tool
        async def get_system_info() -> Dict[str, Any]:
            """Obtener información del sistema"""
            await self.initialize()
            
            return {
                "server_info": {
                    "name": "MCP Core Superior",
                    "version": settings.app_version,
                    "environment": settings.environment.value,
                    "debug": settings.debug
                },
                "configuration": {
                    "max_concurrent_tasks": settings.max_concurrent_tasks,
                    "max_concurrent_tools": settings.max_concurrent_tools,
                    "default_timeout": settings.default_timeout_seconds,
                    "streaming_enabled": settings.streaming_enabled,
                    "metrics_enabled": settings.metrics_enabled
                },
                "integrations": {
                    "contextforge_url": settings.contextforge_url,
                    "database_url": settings.database_url.split("@")[-1] if "@" in settings.database_url else "configured",
                    "vector_db_url": settings.vector_db_url.split("@")[-1] if "@" in settings.vector_db_url else "configured"
                },
                "capabilities": {
                    "multi_agent_orchestration": True,
                    "streaming_real_time": True,
                    "vector_storage": True,
                    "semantic_search": True,
                    "quality_validation": True
                }
            }
        
        self.logger.info(f"Registradas {len(self.mcp._tools)} herramientas MCP")
    
    # === LIFECYCLE METHODS ===
    
    async def start(self) -> None:
        """Iniciar el servidor MCP"""
        await self.initialize()
        self.logger.info("MCPCoreServer iniciado")
    
    async def stop(self) -> None:
        """Detener el servidor MCP"""
        self.logger.info("Deteniendo MCPCoreServer...")
        
        try:
            # Cerrar servicios
            await self.streaming_engine.cleanup()
            await self.orchestrator.cleanup()
            await self.vector_store_client.cleanup()
            await self.contextforge_client.cleanup()
            
            self.is_initialized = False
            self.logger.info("MCPCoreServer detenido")
            
        except Exception as e:
            self.logger.error(f"Error deteniendo servidor: {e}")
    
    async def __aenter__(self):
        """Context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.stop()


# === FACTORY FUNCTION ===

def create_mcp_server() -> MCPCoreServer:
    """Factory para crear instancia del servidor MCP"""
    return MCPCoreServer()


# === MAIN SERVER INSTANCE ===

# Instancia global del servidor
_server_instance: Optional[MCPCoreServer] = None

def get_server() -> MCPCoreServer:
    """Obtener instancia global del servidor"""
    global _server_instance
    if _server_instance is None:
        _server_instance = create_mcp_server()
    return _server_instance


# === CLI INTEGRATION ===

def create_server_for_cli() -> MCPCoreServer:
    """Crear servidor optimizado para CLI"""
    server = create_mcp_server()
    return server


# Ejemplo de uso:
if __name__ == "__main__":
    async def main():
        async with create_mcp_server() as server:
            # El servidor estará disponible via MCP protocol
            print("MCP Core Superior iniciado")
            
            # Mantener corriendo
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("Deteniendo servidor...")
    
    asyncio.run(main())
