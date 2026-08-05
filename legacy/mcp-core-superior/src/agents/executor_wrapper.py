"""
Wrapper MCP para ExecutorAgent
Ejecuta herramientas según plan del PlannerAgent
"""
from typing import Dict, Any, List, Optional
import asyncio
import logging
from datetime import datetime

# Imports del sistema MCP con fallbacks
try:
    from agents.base_agent_wrapper import BaseAgentWrapper, AgentCapability
    from core.exceptions import AgentException, handle_exceptions
    from core.config import settings
    BASE_WRAPPER_AVAILABLE = True
except ImportError:
    try:
        from .base_agent_wrapper import BaseAgentWrapper, AgentCapability
        from ..core.exceptions import AgentException, handle_exceptions
        from ..core.config import settings
        BASE_WRAPPER_AVAILABLE = True
    except ImportError:
        # Fallback cuando el sistema base no está disponible
        from enum import Enum
        
        class AgentCapability(Enum):
            TOOL_INVOCATION = "tool_invocation"
            CONCURRENT_EXECUTION = "concurrent_execution"
            RESULT_COLLECTION = "result_collection"
            CODE_EXECUTION = "code_execution"
            WEB_SCRAPING = "web_scraping"
            API_CALLING = "api_calling"
        
        class BaseAgentWrapper:
            def __init__(self, **kwargs):
                self.agent_name = kwargs.get('agent_name', 'executor')
                self.status = 'ready'
                self.capabilities = kwargs.get('capabilities', [])
            
            async def execute_operation(self, *args, **kwargs):
                return {"success": False, "error": "Sistema base no disponible"}
            
            async def ensure_initialized(self):
                pass
            
            async def health_check(self):
                return {"status": "unavailable", "reason": "Base system not loaded"}
        
        class AgentException(Exception):
            def __init__(self, message, agent_name=None, operation=None):
                super().__init__(message)
                self.message = message
                self.agent_name = agent_name
                self.operation = operation
        
        def handle_exceptions(func):
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    raise AgentException(str(e), "executor", func.__name__)
            return wrapper
        
        # Configuración por defecto
        class Settings:
            max_concurrent_tools = 3
            agent_timeout_seconds = 120
            agent_retry_attempts = 2
            agent_retry_delay = 1.0
        
        settings = Settings()
        BASE_WRAPPER_AVAILABLE = False


class ExecutorAgentWrapper(BaseAgentWrapper):
    """Wrapper para ExecutorAgent"""
    
    def __init__(self):
        capabilities = [
            AgentCapability.TOOL_INVOCATION,
            AgentCapability.CONCURRENT_EXECUTION,
            AgentCapability.RESULT_COLLECTION,
            AgentCapability.CODE_EXECUTION,
            AgentCapability.WEB_SCRAPING,
            AgentCapability.API_CALLING
        ]
        
        super().__init__(
            agent_name="executor",
            capabilities=capabilities,
            max_concurrent=settings.max_concurrent_tools,
            timeout_seconds=settings.agent_timeout_seconds,
            retry_attempts=settings.agent_retry_attempts,
            retry_delay=settings.agent_retry_delay
        )
        
        self.logger = logging.getLogger("mcp.agents.executor")
        self.available_tools = [
            "python_executor", "web_scraper", "web_scraping_agent",
            "search_engine", "file_processor", "git_ops", "api_caller",
            "advanced_python_executor"
        ]
    
    async def _initialize(self) -> None:
        await asyncio.sleep(0.1)
        self.logger.info("ExecutorAgent inicializado")
    
    async def process_request(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self.execute_operation(
            operation_name="execute_tasks",
            capability=AgentCapability.TOOL_INVOCATION,
            operation_func=self._execute_tasks,
            request=request,
            context=context
        )
    
    @handle_exceptions
    async def _execute_tasks(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        plan = request.get("plan", {})
        objective = request.get("objective", "")
        max_concurrent = request.get("max_concurrent", 3)
        timeout_seconds = request.get("timeout_seconds", 300)
        
        if not plan:
            raise AgentException("Plan es requerido para ejecución", self.agent_name, "execute_tasks")
        
        self.logger.info(f"Ejecutando {len(plan.get('tasks', []))} tareas para: {objective[:100]}")
        
        await asyncio.sleep(0.3)  # Simular ejecución
        
        # Simular resultados de ejecución
        results = {
            "execution_summary": {
                "tools_executed": len(plan.get("tasks", [])),
                "successful": len(plan.get("tasks", [])),
                "failed": 0,
                "total_time_ms": 2500
            },
            "results": {
                "tools_results": {
                    f"task_{i}": {
                        "tool": f"tool_{i%6}",
                        "success": True,
                        "result": f"Resultado de tarea {i}",
                        "time_ms": 400 + i * 50
                    } for i in range(len(plan.get("tasks", [])))
                },
                "combined_output": f"Output combinado para: {objective}",
                "success_rate": 1.0
            },
            "artifacts": [f"artifact://executor/task_{i}/result.json" for i in range(len(plan.get("tasks", [])))],
            "evidence": [
                {
                    "tool": f"tool_{i%6}",
                    "timestamp": datetime.now().isoformat(),
                    "summary": f"Ejecutado exitosamente",
                    "reference": f"evidence://tool_{i%6}"
                } for i in range(len(plan.get("tasks", [])))
            ]
        }
        
        return results
    
    async def execute_tasks(self, plan: Dict[str, Any], objective: str, max_concurrent: int = 3, timeout_seconds: int = 300) -> Dict[str, Any]:
        request = {
            "plan": plan,
            "objective": objective,
            "max_concurrent": max_concurrent,
            "timeout_seconds": timeout_seconds
        }
        return await self.process_request(request)
    
    async def get_status(self) -> Dict[str, Any]:
        base_status = super().get_status()
        base_status.update({
            "agent_type": "executor",
            "specialization": "Ejecución de herramientas y recolección de resultados",
            "available_tools": self.available_tools
        })
        return base_status
