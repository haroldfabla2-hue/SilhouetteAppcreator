"""
MCP Core Superior - Core Module
Componentes fundamentales del sistema
"""

# Intentar importar configuración principal, usar configuración de prueba como fallback
try:
    from .config import (
        settings,
        MCPCoreSettings,
        Environment,
        LogLevel,
        get_environment_config,
        get_security_config,
        validate_dependencies
    )
    print("✅ Configuración principal cargada correctamente")
except Exception as e:
    print(f"⚠️  Configuración principal falló: {e}")
    print("🔄 Usando configuración de prueba...")
    try:
        from .test_config import test_settings as settings
        from enum import Enum
        
        class Environment(str, Enum):
            DEVELOPMENT = "development"
            STAGING = "staging" 
            PRODUCTION = "production"
            
        class LogLevel(str, Enum):
            DEBUG = "DEBUG"
            INFO = "INFO"
            WARNING = "WARNING"
            ERROR = "ERROR"
            CRITICAL = "CRITICAL"
        
        def get_environment_config():
            return {"log_level": LogLevel.INFO, "debug": True}
            
        def get_security_config():
            return {"jwt_secret": settings.jwt_secret}
            
        def validate_dependencies():
            pass  # No validación en modo test
            
    except Exception as test_e:
        print(f"❌ Configuración de prueba también falló: {test_e}")
        raise e

from .exceptions import (
    MCPCoreException,
    AgentException,
    OrchestrationException,
    StreamingException,
    DatabaseException,
    ValidationException,
    TaskNotFoundException,
    AgentNotAvailableException,
    TaskTimeoutException,
    StreamingDisconnectedException,
    DatabaseConnectionException,
    ValidationError,
    ConfigurationException,
    UnauthorizedException,
    ForbiddenException,
    RateLimitException,
    ErrorCode,
    handle_exceptions,
    create_agent_error,
    create_orchestration_error,
    ParallelExecutionException,
    ResourceLimitExceededException,
    AgentInstanceException
)

from .parallel_execution_engine import (
    ParallelExecutionEngine,
    Task,
    AgentInstance,
    PerformanceMetrics,
    ResourcePool,
    TaskState,
    ExecutionStrategy,
    LoadBalancingStrategy,
    ResourceType
)

__all__ = [
    # Configuración
    "settings",
    "MCPCoreSettings", 
    "Environment",
    "LogLevel",
    "get_environment_config",
    "get_security_config",
    "validate_dependencies",
    
    # Excepciones
    "MCPCoreException",
    "AgentException",
    "OrchestrationException",
    "StreamingException",
    "DatabaseException",
    "ValidationException",
    "TaskNotFoundException",
    "AgentNotAvailableException",
    "TaskTimeoutException",
    "StreamingDisconnectedException",
    "DatabaseConnectionException",
    "ValidationError",
    "ConfigurationException",
    "UnauthorizedException",
    "ForbiddenException",
    "RateLimitException",
    "ErrorCode",
    "handle_exceptions",
    "create_agent_error",
    "create_orchestration_error",
    "ParallelExecutionException",
    "ResourceLimitExceededException",
    "AgentInstanceException",
    
    # Motor de Paralelización
    "ParallelExecutionEngine",
    "Task",
    "AgentInstance",
    "PerformanceMetrics", 
    "ResourcePool",
    "TaskState",
    "ExecutionStrategy",
    "LoadBalancingStrategy",
    "ResourceType"
]