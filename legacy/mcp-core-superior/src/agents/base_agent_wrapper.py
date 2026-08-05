"""
Wrapper base para agentes MCP
Proporciona funcionalidad común para todos los wrappers de agentes
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncIterator, Callable
from enum import Enum
import asyncio
import time
import logging
from datetime import datetime
import uuid

from ..core.exceptions import (
    AgentException,
    AgentNotAvailableException,
    handle_exceptions
)


class AgentCapability(Enum):
    """Capacidades disponibles de agentes"""
    # ReasonerAgent
    INTENT_ANALYSIS = "intent_analysis"
    STRATEGY_DEFINITION = "strategy_definition"
    CONTEXT_ENRICHMENT = "context_enrichment"
    
    # PlannerAgent
    TASK_DECOMPOSITION = "task_decomposition"
    TOOL_SELECTION = "tool_selection"
    DEPENDENCY_MANAGEMENT = "dependency_management"
    PLAN_OPTIMIZATION = "plan_optimization"
    
    # ExecutorAgent
    TOOL_INVOCATION = "tool_invocation"
    CONCURRENT_EXECUTION = "concurrent_execution"
    RESULT_COLLECTION = "result_collection"
    CODE_EXECUTION = "code_execution"
    WEB_SCRAPING = "web_scraping"
    API_CALLING = "api_calling"
    
    # VerifierAgent
    QUALITY_VALIDATION = "quality_validation"
    CONSISTENCY_CHECKING = "consistency_checking"
    TRAJECTORY_EVALUATION = "trajectory_evaluation"
    GATE_QUALITY = "gate_quality"
    
    # MemoryManagerAgent
    KNOWLEDGE_STORAGE = "knowledge_storage"
    SEMANTIC_SEARCH = "semantic_search"
    CONTEXT_RETRIEVAL = "context_retrieval"
    CONVERSATION_MANAGEMENT = "conversation_management"
    
    # Location Intelligence Agent
    GEOCODING = "geocoding"
    REVERSE_GEOCODING = "reverse_geocoding"
    PLACE_SEARCH = "place_search"
    DIRECTIONS = "directions"
    DISTANCE_CALCULATION = "distance_calculation"
    MAPS_API = "maps_api"
    
    # Communication Agent
    EMAIL_SENDING = "email_sending"
    EMAIL_RECEIVING = "email_receiving"
    MESSAGING = "messaging"
    NOTIFICATION_SENDING = "notification_sending"
    CONTACT_MANAGEMENT = "contact_management"
    
    # Document Creation Agent
    DOCUMENT_CREATION = "document_creation"
    SPREADSHEET_CREATION = "spreadsheet_creation"
    DOCUMENT_FORMATTING = "document_formatting"
    TEMPLATE_ENGINE = "template_engine"
    DOCUMENT_EXPORT = "document_export"
    
    # Social Media Agent
    SOCIAL_POSTING = "social_posting"
    SOCIAL_MONITORING = "social_monitoring"
    HASHTAG_ANALYSIS = "hashtag_analysis"
    SOCIAL_ANALYTICS = "social_analytics"
    PLATFORM_INTEGRATION = "platform_integration"
    
    # Commerce Agent
    PRODUCT_SEARCH = "product_search"
    PRICE_COMPARISON = "price_comparison"
    ECOMMERCE_INTEGRATION = "ecommerce_integration"
    CART_MANAGEMENT = "cart_management"
    CHECKOUT_PROCESSING = "checkout_processing"
    
    # Analytics Agent
    FINANCIAL_ANALYTICS = "financial_analytics"
    DATA_ANALYSIS = "data_analysis"
    REPORT_GENERATION = "report_generation"
    KPI_TRACKING = "kpi_tracking"
    PREDICTIVE_ANALYTICS = "predictive_analytics"
    
    # Scheduling Agent
    CALENDAR_MANAGEMENT = "calendar_management"
    SCHEDULE_OPTIMIZATION = "schedule_optimization"
    REMINDER_MANAGEMENT = "reminder_management"
    MEETING_COORDINATION = "meeting_coordination"
    TIME_SLOT_FINDING = "time_slot_finding"
    
    # Content Creation Agent
    CONTENT_GENERATION = "content_generation"
    MULTIMEDIA_CREATION = "multimedia_creation"
    TEXT_TO_AUDIO = "text_to_audio"
    TEXT_TO_VIDEO = "text_to_video"
    IMAGE_GENERATION = "image_generation"


class AgentStatus(Enum):
    """Estados de agentes"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class AgentCapabilityError(Exception):
    """Excepción cuando un agente no tiene la capacidad requerida"""
    pass


class BaseAgentWrapper(ABC):
    """
    Wrapper base para agentes MCP
    
    Proporciona funcionalidad común:
    - Gestión de estado y capacidades
    - Timeouts y manejo de errores
    - Logging y métricas
    - Validación de parámetros
    - Retry logic
    """
    
    def __init__(
        self,
        agent_name: str,
        capabilities: List[AgentCapability],
        max_concurrent: int = 3,
        timeout_seconds: int = 60,
        retry_attempts: int = 3,
        retry_delay: float = 1.0
    ):
        self.agent_name = agent_name
        self.capabilities = capabilities
        self.max_concurrent = max_concurrent
        self.timeout_seconds = timeout_seconds
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        
        # Estado del agente
        self.status = AgentStatus.INITIALIZING
        self.current_operations = 0
        self.total_operations = 0
        self.successful_operations = 0
        self.failed_operations = 0
        self.last_activity = datetime.now()
        
        # Métricas
        self.metrics = {
            "response_times": [],
            "errors": [],
            "capability_usage": {cap.value: 0 for cap in capabilities}
        }
        
        # Setup logging
        self.logger = logging.getLogger(f"mcp.agents.{agent_name}")
        
        # Semáforo para limitar concurrencia
        self._semaphore = asyncio.Semaphore(max_concurrent)
        
        # Inicialización
        self._initialized = False
        self._init_lock = asyncio.Lock()
    
    @property
    def is_ready(self) -> bool:
        """Verificar si el agente está listo para usar"""
        return self.status == AgentStatus.READY and self._initialized
    
    @property
    def is_busy(self) -> bool:
        """Verificar si el agente está ocupado"""
        return self.status == AgentStatus.BUSY or self.current_operations >= self.max_concurrent
    
    @property
    def utilization(self) -> float:
        """Obtener utilización actual del agente (0.0 - 1.0)"""
        return min(self.current_operations / self.max_concurrent, 1.0)
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Obtener capacidades del agente"""
        return self.capabilities.copy()
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado completo del agente"""
        return {
            "agent_name": self.agent_name,
            "status": self.status.value,
            "is_ready": self.is_ready,
            "is_busy": self.is_busy,
            "utilization": self.utilization,
            "current_operations": self.current_operations,
            "max_concurrent": self.max_concurrent,
            "total_operations": self.total_operations,
            "successful_operations": self.successful_operations,
            "failed_operations": self.failed_operations,
            "success_rate": (
                self.successful_operations / max(self.total_operations, 1)
            ),
            "last_activity": self.last_activity.isoformat(),
            "capabilities": [cap.value for cap in self.capabilities],
            "metrics": self.metrics.copy()
        }
    
    async def ensure_initialized(self) -> None:
        """Asegurar que el agente esté inicializado"""
        if not self._initialized:
            async with self._init_lock:
                if not self._initialized:  # Double-check
                    await self._initialize()
                    self._initialized = True
                    self.status = AgentStatus.READY
                    self.logger.info(f"Agente {self.agent_name} inicializado correctamente")
    
    async def _initialize(self) -> None:
        """Inicialización específica del agente (override en subclases)"""
        # Implementación base - puede ser sobrescrita
        await asyncio.sleep(0.1)  # Simular inicialización
    
    def _validate_capability(self, capability: AgentCapability) -> None:
        """Validar que el agente tenga la capacidad requerida"""
        if capability not in self.capabilities:
            raise AgentCapabilityError(
                f"Agente {self.agent_name} no tiene la capacidad {capability.value}"
            )
    
    def _record_operation_start(self) -> str:
        """Registrar inicio de operación y retornar ID"""
        operation_id = str(uuid.uuid4())[:8]
        self.current_operations += 1
        self.total_operations += 1
        self.last_activity = datetime.now()
        
        self.logger.debug(
            f"Iniciando operación {operation_id} en {self.agent_name} "
            f"(operaciones activas: {self.current_operations})"
        )
        
        return operation_id
    
    def _record_operation_end(
        self,
        operation_id: str,
        success: bool,
        response_time: float,
        error: Optional[Exception] = None
    ) -> None:
        """Registrar fin de operación"""
        self.current_operations = max(0, self.current_operations - 1)
        self.last_activity = datetime.now()
        
        if success:
            self.successful_operations += 1
            self.metrics["response_times"].append(response_time)
            # Mantener solo últimos 100 tiempos de respuesta
            if len(self.metrics["response_times"]) > 100:
                self.metrics["response_times"] = self.metrics["response_times"][-100:]
        else:
            self.failed_operations += 1
            self.metrics["errors"].append({
                "timestamp": datetime.now().isoformat(),
                "operation_id": operation_id,
                "error": str(error) if error else "Unknown error"
            })
            # Mantener solo últimos 50 errores
            if len(self.metrics["errors"]) > 50:
                self.metrics["errors"] = self.metrics["errors"][-50:]
        
        self.logger.debug(
            f"Completando operación {operation_id} en {self.agent_name} "
            f"({'success' if success else 'failure'}, tiempo: {response_time:.3f}s)"
        )
    
    async def _execute_with_retry(
        self,
        operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Ejecutar operación con retry logic"""
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                # Crear timeout task
                result = await asyncio.wait_for(
                    operation(*args, **kwargs),
                    timeout=self.timeout_seconds
                )
                return result
                
            except asyncio.TimeoutError as e:
                last_error = e
                self.logger.warning(
                    f"Timeout en intento {attempt + 1}/{self.retry_attempts} "
                    f"para operación en {self.agent_name}"
                )
                
            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"Error en intento {attempt + 1}/{self.retry_attempts} "
                    f"para operación en {self.agent_name}: {str(e)}"
                )
            
            # Retry delay (excepto en último intento)
            if attempt < self.retry_attempts - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        # Si llegamos aquí, todos los intentos fallaron
        raise AgentException(
            message=f"Agente {self.agent_name} falló después de {self.retry_attempts} intentos",
            agent_name=self.agent_name,
            operation="execute_with_retry",
            error_code="AGENT_EXECUTION_ERROR",
            original_error=last_error
        )
    
    async def execute_operation(
        self,
        operation_name: str,
        capability: AgentCapability,
        operation_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Ejecutar operación del agente con manejo completo
        
        Args:
            operation_name: Nombre de la operación
            capability: Capacidad requerida
            operation_func: Función a ejecutar
            *args, **kwargs: Argumentos para la función
            
        Returns:
            Resultado de la operación
        """
        # Validaciones
        await self.ensure_initialized()
        self._validate_capability(capability)
        
        if self.status == AgentStatus.ERROR:
            raise AgentNotAvailableException(self.agent_name, operation_name)
        
        # Ejecutar con semáforo para limitar concurrencia
        async with self._semaphore:
            operation_id = self._record_operation_start()
            start_time = time.time()
            
            try:
                # Cambiar estado a busy
                old_status = self.status
                self.status = AgentStatus.BUSY
                
                # Ejecutar operación
                result = await self._execute_with_retry(operation_func, *args, **kwargs)
                
                # Registrar éxito
                response_time = time.time() - start_time
                self._record_operation_end(operation_id, True, response_time)
                
                # Actualizar métricas de uso de capacidad
                self.metrics["capability_usage"][capability.value] += 1
                
                return result
                
            except Exception as e:
                # Registrar falla
                response_time = time.time() - start_time
                self._record_operation_end(operation_id, False, response_time, e)
                
                # Si hay muchos errores, marcar como error
                if self.failed_operations > self.successful_operations and self.total_operations > 5:
                    self.status = AgentStatus.ERROR
                    self.logger.error(f"Agente {self.agent_name} marcado en estado ERROR")
                
                raise
                
            finally:
                # Restaurar estado
                self.status = old_status
    
    @abstractmethod
    async def process_request(
        self,
        request: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Procesar request específico del agente
        
        Args:
            request: Request del cliente
            context: Contexto adicional
            
        Returns:
            Respuesta del agente
        """
        pass
    
    def reset_metrics(self) -> None:
        """Resetear métricas del agente"""
        self.metrics["response_times"] = []
        self.metrics["errors"] = []
        # No resetear usage counters
        
        self.logger.info(f"Métricas reseteadas para agente {self.agent_name}")
    
    def set_maintenance_mode(self, enabled: bool) -> None:
        """Activar/desactivar modo mantenimiento"""
        if enabled:
            self.status = AgentStatus.MAINTENANCE
            self.logger.info(f"Agente {self.agent_name} en modo mantenimiento")
        else:
            if self.current_operations == 0:
                self.status = AgentStatus.READY
                self.logger.info(f"Agente {self.agent_name} salir de modo mantenimiento")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check del agente"""
        try:
            await self.ensure_initialized()
            
            health_status = {
                "agent_name": self.agent_name,
                "status": "healthy",
                "is_ready": self.is_ready,
                "is_busy": self.is_busy,
                "utilization": self.utilization,
                "last_activity": self.last_activity.isoformat(),
                "success_rate": (
                    self.successful_operations / max(self.total_operations, 1)
                ),
                "average_response_time": (
                    sum(self.metrics["response_times"]) / 
                    max(len(self.metrics["response_times"]), 1)
                )
            }
            
            # Si hay errores recientes, marcar como warning
            recent_errors = [
                err for err in self.metrics["errors"]
                if (datetime.now() - datetime.fromisoformat(err["timestamp"])).seconds < 300
            ]
            
            if recent_errors:
                health_status["status"] = "warning"
                health_status["recent_errors"] = len(recent_errors)
            
            return health_status
            
        except Exception as e:
            return {
                "agent_name": self.agent_name,
                "status": "unhealthy",
                "error": str(e)
            }
    
    def __str__(self) -> str:
        return f"AgentWrapper({self.agent_name}, status={self.status.value})"
    
    def __repr__(self) -> str:
        return (
            f"AgentWrapper("
            f"agent_name='{self.agent_name}', "
            f"status='{self.status.value}', "
            f"capabilities={len(self.capabilities)}, "
            f"utilization={self.utilization:.2%}"
            f")"
        )


class AgentWrapperFactory:
    """Factory para crear wrappers de agentes"""
    
    _wrappers: Dict[str, BaseAgentWrapper] = {}
    
    @classmethod
    def register_wrapper(cls, name: str, wrapper_class: type) -> None:
        """Registrar clase de wrapper"""
        cls._wrappers[name] = wrapper_class
    
    @classmethod
    def create_wrapper(
        cls,
        agent_type: str,
        **kwargs
    ) -> BaseAgentWrapper:
        """Crear instancia de wrapper"""
        if agent_type not in cls._wrappers:
            raise ValueError(f"Tipo de agente no soportado: {agent_type}")
        
        wrapper_class = cls._wrappers[agent_type]
        return wrapper_class(**kwargs)
    
    @classmethod
    def get_available_types(cls) -> List[str]:
        """Obtener tipos de agentes disponibles"""
        return list(cls._wrappers.keys())
