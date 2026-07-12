"""
Observabilidad y Logging Estructurado para MCP Core Superior

Este módulo proporciona capacidades avanzadas de observabilidad incluyendo:
- Logging estructurado con formato JSON
- Trazado distribuido y correlation IDs
- Métricas de performance
- Audit trails para compliance
- Filtrado de datos sensibles
- Integración con ELK stack y servicios de cloud logging

=== SISTEMA OPENTELEMETRY ===

El sistema de OpenTelemetry integrado proporciona:
- Tracing automático de agentes MCP
- Spans para operaciones de base de datos
- Context propagation entre servicios
- Custom spans para workflows complejos
- Exporters configurables (Jaeger, Zipkin, OTLP)
- Sampling strategies
- Trace correlation IDs
- Performance metrics collection
- Error tracking y Exception capturing
- Integration con FastMCP Server

=== DASHBOARD Y DEPLOYMENT ===

- Configuración de dashboards (Grafana, Prometheus, Jaeger)
- Utilidades de despliegue automático
- Scripts de configuración para diferentes entornos
- Integration específica con FastMCP Server
"""

# === LOGGING ESTRUCTURADO ===
from .structured_logger import (
    StructuredLogger,
    LogLevel,
    LogContext,
    PerformanceLogger,
    AuditLogger,
    CorrelationContext,
    SensitiveDataFilter,
    LogAggregator,
    LogRotator,
    ELKShipper,
    CloudLogShipper
)

# === SISTEMA OPENTELEMETRY ===
from .opentelemetry_system import (
    # Configuración
    TraceConfig,
    ExportBackend,
    SamplingType,
    TraceLevel,
    
    # Componentes principales
    OpenTelemetrySystem,
    CorrelationContext,
    PerformanceMetrics,
    MCPAgentInstrumentor,
    DatabaseInstrumentor,
    CustomSpanFactory,
    ErrorTracker,
    
    # Funciones de utilidad
    get_otel_system,
    initialize_opentelemetry,
    trace_function,
    trace_async_function,
    create_span,
    add_span_event,
    set_correlation_id,
    get_correlation_id,
    
    # Tipos y enums
    SpanData
)

# === MÉTRICAS AVANZADAS ===
from .advanced_metrics import (
    # Tipos de métricas
    MetricType,
    AlertSeverity,
    TimeSeriesAggregation,
    
    # Modelos de datos
    LatencyMetric,
    ThroughputMetric,
    ErrorRateMetric,
    ResourceUtilizationMetric,
    AgentHealthScore,
    BusinessMetric,
    CapacityPlanningMetric,
    CustomAlert,
    
    # Componentes principales
    AdvancedMetricsCollector,
    TimeSeriesStorage,
    PercentileCalculator,
    GrafanaDashboardConfig,
    
    # Funciones de utilidad
    get_advanced_metrics_collector,
    initialize_advanced_metrics
)

# === CONFIGURACIÓN DE MÉTRICAS ===
from .metrics_config import (
    MetricsConfig,
    AlertConfig,
    DashboardConfig,
    BusinessMetricsConfig,
    MetricsConfigurationManager,
    get_metrics_config_manager,
    create_default_configs
)

# === DASHBOARD DE OBSERVABILIDAD ===
from .dashboard_config import (
    DashboardConfig,
    DashboardType,
    ObservabilityDashboard,
    setup_observability_dashboard,
    get_grafana_dashboard_config,
    get_prometheus_config
)

# === INTEGRACIÓN CON FASTMCP ===
from .fastmcp_integration import (
    MCPMiddleware,
    MCPEndpointInstrumentor,
    FastMCPServerInstrumentor,
    instrument_fastmcp_server,
    instrument_mcp_tool,
    trace_mcp_workflow
)

# === UTILIDADES DE DEPLOYMENT ===
from .deployment_utils import (
    DeploymentConfig,
    DockerComposeGenerator,
    ObservabilityDeployment,
    deploy_observability,
    quick_setup_development
)

__all__ = [
    # Logging estructurado
    'StructuredLogger',
    'LogLevel', 
    'LogContext',
    'PerformanceLogger',
    'AuditLogger',
    'CorrelationContext',
    'SensitiveDataFilter',
    'LogAggregator',
    'LogRotator',
    'ELKShipper',
    'CloudLogShipper',
    
    # OpenTelemetry
    'TraceConfig',
    'ExportBackend',
    'SamplingType',
    'TraceLevel',
    'OpenTelemetrySystem',
    'CorrelationContext',
    'PerformanceMetrics',
    'MCPAgentInstrumentor',
    'DatabaseInstrumentor',
    'CustomSpanFactory',
    'ErrorTracker',
    'get_otel_system',
    'initialize_opentelemetry',
    'trace_function',
    'trace_async_function',
    'create_span',
    'add_span_event',
    'set_correlation_id',
    'get_correlation_id',
    'SpanData',
    
    # Métricas Avanzadas
    'MetricType',
    'AlertSeverity',
    'TimeSeriesAggregation',
    'LatencyMetric',
    'ThroughputMetric',
    'ErrorRateMetric',
    'ResourceUtilizationMetric',
    'AgentHealthScore',
    'BusinessMetric',
    'CapacityPlanningMetric',
    'CustomAlert',
    'AdvancedMetricsCollector',
    'TimeSeriesStorage',
    'PercentileCalculator',
    'GrafanaDashboardConfig',
    'get_advanced_metrics_collector',
    'initialize_advanced_metrics',
    
    # Configuración de Métricas
    'MetricsConfig',
    'AlertConfig',
    'DashboardConfig',
    'BusinessMetricsConfig',
    'MetricsConfigurationManager',
    'get_metrics_config_manager',
    'create_default_configs',
    
    # Dashboard
    'DashboardConfig',
    'DashboardType',
    'ObservabilityDashboard',
    'setup_observability_dashboard',
    'get_grafana_dashboard_config',
    'get_prometheus_config',
    
    # FastMCP Integration
    'MCPMiddleware',
    'MCPEndpointInstrumentor',
    'FastMCPServerInstrumentor',
    'instrument_fastmcp_server',
    'instrument_mcp_tool',
    'trace_mcp_workflow',
    
    # Deployment
    'DeploymentConfig',
    'DockerComposeGenerator',
    'ObservabilityDeployment',
    'deploy_observability',
    'quick_setup_development'
]

__version__ = '2.0.0'