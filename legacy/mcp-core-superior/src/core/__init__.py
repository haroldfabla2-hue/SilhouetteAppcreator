"""
MCP Core Superior - Core Module
Componentes fundamentales del sistema
"""

# FastMCP Local - Implementación local del framework MCP
from .fastmcp_local import (
    # Clases principales
    FastMCP,
    Context,
    InitializeRequest,
    InitializeResult,
    CallToolRequest,
    CallToolResult,
    Tool,
    ToolInputSchema,
    Content,
    ToolArguments,
    MCPCapabilities,
    ClientInfo,
    ServerInfo,
    
    # Enums
    MCPServerStatus,
    ToolStatus,
    
    # Clases internas
    ToolHandler,
    
    # Factories
    create_fastmcp_server,
    mock_fastmcp_imports
)

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

from .intelligent_router import (
    IntelligentRouter,
    RoutingContext,
    RoutingDecision,
    RoutingStrategy,
    OptimizationObjective,
    AgentMetrics,
    intelligent_router,
    PerformancePredictor,
    CostOptimizer,
    ABTestManager
)

# Auto-Healing System
from .auto_healing_engine import (
    AutoHealingEngine,
    CircuitBreaker,
    PredictiveFailureDetector,
    AutoHealingMixin,
    HealthMetrics,
    HealthStatus,
    CircuitState,
    ScalingAction,
    RecoveryStrategy,
    ErrorEvent,
    CircuitBreakerConfig,
    AutoScalingConfig,
    get_auto_healing_engine,
    create_auto_healing_engine
)

from .health_metrics import (
    HealthMetricsCollector,
    SystemResourceMetrics,
    ApplicationMetrics,
    AgentPerformanceMetrics,
    MetricsAggregator,
    get_metrics_collector,
    initialize_metrics_collection
)

from .auto_healing_config import (
    AutoHealingConfiguration,
    DynamicThresholds,
    AgentSpecificConfig,
    ConfigurationManager,
    ConfigurationSource,
    get_config_manager,
    create_default_config,
    merge_configurations,
    export_config_to_file,
    import_config_from_file
)

from .healing_integration import (
    HealingIntegration,
    with_healing_integration,
    create_healing_integrated_server
)

__all__ = [
    # FastMCP Local
    "FastMCP",
    "Context",
    "InitializeRequest",
    "InitializeResult",
    "CallToolRequest",
    "CallToolResult",
    "Tool",
    "ToolInputSchema",
    "Content",
    "ToolArguments",
    "MCPCapabilities",
    "ClientInfo",
    "ServerInfo",
    "MCPServerStatus",
    "ToolStatus",
    "ToolHandler",
    "create_fastmcp_server",
    "mock_fastmcp_imports",
    
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
    "ResourceType",
    
    # Intelligent Router
    "IntelligentRouter",
    "RoutingContext",
    "RoutingDecision",
    "RoutingStrategy",
    "OptimizationObjective",
    "AgentMetrics",
    "intelligent_router",
    "PerformancePredictor",
    "CostOptimizer",
    "ABTestManager",
    
    # Auto-Healing Engine
    "AutoHealingEngine",
    "CircuitBreaker",
    "PredictiveFailureDetector",
    "AutoHealingMixin",
    "HealthMetrics",
    "HealthStatus",
    "CircuitState",
    "ScalingAction",
    "RecoveryStrategy",
    "ErrorEvent",
    "CircuitBreakerConfig",
    "AutoScalingConfig",
    "get_auto_healing_engine",
    "create_auto_healing_engine",
    
    # Health Metrics
    "HealthMetricsCollector",
    "SystemResourceMetrics",
    "ApplicationMetrics",
    "AgentPerformanceMetrics",
    "MetricsAggregator",
    "get_metrics_collector",
    "initialize_metrics_collection",
    
    # Auto-Healing Configuration
    "AutoHealingConfiguration",
    "DynamicThresholds",
    "AgentSpecificConfig",
    "ConfigurationManager",
    "ConfigurationSource",
    "get_config_manager",
    "create_default_config",
    "merge_configurations",
    "export_config_to_file",
    "import_config_from_file",
    
    # Healing Integration
    "HealingIntegration",
    "with_healing_integration",
    "create_healing_integrated_server"
]