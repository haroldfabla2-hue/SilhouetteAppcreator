"""
Excepciones personalizadas para MCP Core Superior
Define excepciones específicas para cada componente del sistema
"""
from typing import Any, Dict, Optional, List
from enum import Enum


class ErrorCode(str, Enum):
    """Códigos de error estandarizados"""
    # Errores generales
    INVALID_REQUEST = "INVALID_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    
    # Errores de agentes
    AGENT_NOT_AVAILABLE = "AGENT_NOT_AVAILABLE"
    AGENT_TIMEOUT = "AGENT_TIMEOUT"
    AGENT_EXECUTION_ERROR = "AGENT_EXECUTION_ERROR"
    AGENT_VALIDATION_FAILED = "AGENT_VALIDATION_FAILED"
    
    # Errores de orquestación
    ORCHESTRATION_FAILED = "ORCHESTRATION_FAILED"
    TASK_EXECUTION_ERROR = "TASK_EXECUTION_ERROR"
    TASK_TIMEOUT = "TASK_TIMEOUT"
    TASK_CANCELLED = "TASK_CANCELLED"
    
    # Errores de streaming
    STREAMING_ERROR = "STREAMING_ERROR"
    STREAMING_DISCONNECTED = "STREAMING_DISCONNECTED"
    STREAMING_BUFFER_FULL = "STREAMING_BUFFER_FULL"
    
    # Errores de base de datos
    DATABASE_ERROR = "DATABASE_ERROR"
    DATABASE_CONNECTION_FAILED = "DATABASE_CONNECTION_FAILED"
    DATABASE_QUERY_ERROR = "DATABASE_QUERY_ERROR"
    VECTOR_DB_ERROR = "VECTOR_DB_ERROR"
    
    # Errores de memoria
    MEMORY_ERROR = "MEMORY_ERROR"
    MEMORY_OVERFLOW = "MEMORY_OVERFLOW"
    MEMORY_RETRIEVAL_FAILED = "MEMORY_RETRIEVAL_FAILED"
    
    # Errores de validación
    VALIDATION_ERROR = "VALIDATION_ERROR"
    SCHEMA_ERROR = "SCHEMA_ERROR"
    PARAMETER_ERROR = "PARAMETER_ERROR"
    
    # Errores de paralelización
    PARALLEL_EXECUTION_ERROR = "PARALLEL_EXECUTION_ERROR"
    RESOURCE_LIMIT_EXCEEDED = "RESOURCE_LIMIT_EXCEEDED"
    AGENT_INSTANCE_ERROR = "AGENT_INSTANCE_ERROR"
    WORKFLOW_EXECUTION_ERROR = "WORKFLOW_EXECUTION_ERROR"
    LOAD_BALANCING_ERROR = "LOAD_BALANCING_ERROR"
    
    # Errores de configuración
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    ENVIRONMENT_ERROR = "ENVIRONMENT_ERROR"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"


class MCPCoreException(Exception):
    """Excepción base para MCP Core Superior"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INVALID_REQUEST,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.original_error = original_error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir excepción a diccionario para respuestas API"""
        response = {
            "error": {
                "code": self.error_code.value,
                "message": self.message,
                "status_code": self.status_code,
                "details": self.details
            }
        }
        
        if self.original_error:
            response["error"]["original_error"] = str(self.original_error)
        
        return response
    
    def __str__(self) -> str:
        base_msg = f"[{self.error_code.value}] {self.message}"
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            base_msg += f" ({details_str})"
        return base_msg


class AgentException(MCPCoreException):
    """Excepción específica para errores de agentes"""
    
    def __init__(
        self,
        message: str,
        agent_name: str,
        operation: str,
        error_code: ErrorCode = ErrorCode.AGENT_EXECUTION_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details={
                "agent_name": agent_name,
                "operation": operation,
                **(details or {})
            },
            original_error=original_error
        )


class OrchestrationException(MCPCoreException):
    """Excepción específica para errores de orquestación"""
    
    def __init__(
        self,
        message: str,
        task_id: str,
        phase: Optional[str] = None,
        error_code: ErrorCode = ErrorCode.ORCHESTRATION_FAILED,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details={
                "task_id": task_id,
                "phase": phase,
                **(details or {})
            },
            original_error=original_error
        )


class StreamingException(MCPCoreException):
    """Excepción específica para errores de streaming"""
    
    def __init__(
        self,
        message: str,
        stream_id: str,
        error_code: ErrorCode = ErrorCode.STREAMING_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details={
                "stream_id": stream_id,
                **(details or {})
            },
            original_error=original_error
        )


class DatabaseException(MCPCoreException):
    """Excepción específica para errores de base de datos"""
    
    def __init__(
        self,
        message: str,
        operation: str,
        table: Optional[str] = None,
        error_code: ErrorCode = ErrorCode.DATABASE_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details={
                "operation": operation,
                "table": table,
                **(details or {})
            },
            original_error=original_error
        )


class ValidationException(MCPCoreException):
    """Excepción específica para errores de validación"""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Any = None,
        error_code: ErrorCode = ErrorCode.VALIDATION_ERROR,
        status_code: int = 422,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details={
                "field": field,
                "value": value,
                **(details or {})
            },
            original_error=original_error
        )


class TaskNotFoundException(MCPCoreException):
    """Excepción para tareas no encontradas"""
    
    def __init__(self, task_id: str):
        super().__init__(
            message=f"Tarea no encontrada: {task_id}",
            error_code=ErrorCode.NOT_FOUND,
            status_code=404,
            details={"task_id": task_id}
        )


class AgentNotAvailableException(AgentException):
    """Excepción para agentes no disponibles"""
    
    def __init__(self, agent_name: str, operation: str):
        super().__init__(
            message=f"Agente {agent_name} no disponible para operación {operation}",
            agent_name=agent_name,
            operation=operation,
            error_code=ErrorCode.AGENT_NOT_AVAILABLE,
            status_code=503
        )


class TaskTimeoutException(OrchestrationException):
    """Excepción para timeout de tareas"""
    
    def __init__(self, task_id: str, timeout_seconds: int):
        super().__init__(
            message=f"Tarea {task_id} excedió timeout de {timeout_seconds} segundos",
            task_id=task_id,
            error_code=ErrorCode.TASK_TIMEOUT,
            status_code=408,
            details={"timeout_seconds": timeout_seconds}
        )


class StreamingDisconnectedException(StreamingException):
    """Excepción para desconexión de streaming"""
    
    def __init__(self, stream_id: str, reason: str = "Cliente desconectado"):
        super().__init__(
            message=f"Streaming desconectado: {reason}",
            stream_id=stream_id,
            error_code=ErrorCode.STREAMING_DISCONNECTED,
            status_code=499,  # Client Closed Request
            details={"reason": reason}
        )


class DatabaseConnectionException(DatabaseException):
    """Excepción para errores de conexión a BD"""
    
    def __init__(self, operation: str, connection_details: Optional[str] = None):
        super().__init__(
            message=f"Error de conexión a base de datos en operación {operation}",
            operation=operation,
            error_code=ErrorCode.DATABASE_CONNECTION_FAILED,
            status_code=503,
            details={"connection_details": connection_details}
        )


class ValidationError(Exception):
    """Excepción para errores de validación de datos"""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(f"Validation error: {message}")


class ConfigurationException(MCPCoreException):
    """Excepción para errores de configuración"""
    
    def __init__(
        self,
        message: str,
        config_key: str,
        error_code: ErrorCode = ErrorCode.CONFIGURATION_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details={
                "config_key": config_key,
                **(details or {})
            },
            original_error=original_error
        )


class UnauthorizedException(MCPCoreException):
    """Excepción para errores de autorización"""
    
    def __init__(self, message: str = "No autorizado", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.UNAUTHORIZED,
            status_code=401,
            details=details
        )


class ForbiddenException(MCPCoreException):
    """Excepción para errores de acceso prohibido"""
    
    def __init__(self, message: str = "Acceso prohibido", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.FORBIDDEN,
            status_code=403,
            details=details
        )


class RateLimitException(MCPCoreException):
    """Excepción para rate limiting"""
    
    def __init__(self, message: str = "Rate limit excedido", retry_after: int = 60):
        super().__init__(
            message=message,
            error_code=ErrorCode.RATE_LIMITED,
            status_code=429,
            details={"retry_after": retry_after}
        )


# Funciones helper para crear excepciones específicas

def create_agent_error(
    agent_name: str,
    operation: str,
    original_error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> AgentException:
    """Crear excepción de agente basada en error original"""
    
    if "timeout" in str(original_error).lower():
        return AgentException(
            message=f"Timeout en {operation} del agente {agent_name}",
            agent_name=agent_name,
            operation=operation,
            error_code=ErrorCode.AGENT_TIMEOUT,
            original_error=original_error,
            details=context
        )
    
    return AgentException(
        message=f"Error en {operation} del agente {agent_name}: {str(original_error)}",
        agent_name=agent_name,
        operation=operation,
        error_code=ErrorCode.AGENT_EXECUTION_ERROR,
        original_error=original_error,
        details=context
    )


def create_orchestration_error(
    task_id: str,
    phase: str,
    original_error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> OrchestrationException:
    """Crear excepción de orquestación basada en error original"""
    
    if "timeout" in str(original_error).lower():
        return OrchestrationException(
            message=f"Timeout en fase {phase} de tarea {task_id}",
            task_id=task_id,
            phase=phase,
            error_code=ErrorCode.TASK_TIMEOUT,
            original_error=original_error,
            details=context
        )
    
    return OrchestrationException(
        message=f"Error en fase {phase} de tarea {task_id}: {str(original_error)}",
        task_id=task_id,
        phase=phase,
        error_code=ErrorCode.ORCHESTRATION_FAILED,
        original_error=original_error,
        details=context
    )


# Excepciones para Motor de Paralelización

class ParallelExecutionException(MCPCoreException):
    """Excepción para errores de ejecución paralela"""
    
    def __init__(
        self, 
        message: str, 
        task_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        phase: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.PARALLEL_EXECUTION_ERROR,
            status_code=503,
            **kwargs
        )
        self.task_id = task_id
        self.workflow_id = workflow_id
        self.phase = phase


class ResourceLimitExceededException(MCPCoreException):
    """Excepción para límites de recursos excedidos"""
    
    def __init__(
        self, 
        resource_type: str,
        current_usage: float,
        limit: float,
        **kwargs
    ):
        message = f"Límite de {resource_type} excedido: {current_usage}/{limit}"
        super().__init__(
            message=message,
            error_code=ErrorCode.RESOURCE_LIMIT_EXCEEDED,
            status_code=429,
            **kwargs
        )
        self.resource_type = resource_type
        self.current_usage = current_usage
        self.limit = limit


class AgentInstanceException(MCPCoreException):
    """Excepción para errores de instancias de agentes"""
    
    def __init__(
        self, 
        message: str, 
        agent_type: Optional[str] = None,
        instance_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.AGENT_INSTANCE_ERROR,
            status_code=503,
            **kwargs
        )
        self.agent_type = agent_type
        self.instance_id = instance_id


# Decorador para manejo automático de excepciones

def handle_exceptions(func):
    """Decorador para manejo automático de excepciones"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except MCPCoreException:
            raise
        except Exception as e:
            raise MCPCoreException(
                message=f"Error inesperado en {func.__name__}: {str(e)}",
                error_code=ErrorCode.INVALID_REQUEST,
                status_code=500,
                original_error=e
            )
    return wrapper
