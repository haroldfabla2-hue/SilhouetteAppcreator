"""
Configuración específica para el Sistema de Colaboración en Tiempo Real

Gestiona configuraciones relacionadas con colaboración multi-usuario,
WebSocket management, Redis sessions, conflict resolution, y monitoreo de agentes.
"""

from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from enum import Enum

from .config import settings


class CollaborationEnvironment(str, Enum):
    """Entornos específicos para colaboración"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ENTERPRISE = "enterprise"


class WebSocketConfig(BaseModel):
    """Configuración de WebSockets"""
    max_connections: int = Field(default=1000, description="Máximo de conexiones WebSocket simultáneas")
    connection_timeout: int = Field(default=30, description="Timeout de conexión en segundos")
    message_size_limit: int = Field(default=1024*1024, description="Límite de tamaño de mensaje en bytes")
    heartbeat_interval: int = Field(default=30, description="Intervalo de heartbeat en segundos")
    max_message_queue: int = Field(default=1000, description="Máximo de mensajes en cola por conexión")
    compression_enabled: bool = Field(default=True, description="Habilitar compresión de mensajes")
    ssl_enabled: bool = Field(default=False, description="Habilitar SSL para WebSockets")


class RedisCollaborationConfig(BaseModel):
    """Configuración específica de Redis para colaboración"""
    session_ttl_seconds: int = Field(default=3600, description="TTL de sesiones en Redis (1 hora)")
    agent_state_ttl_seconds: int = Field(default=1800, description="TTL de estados de agente (30 min)")
    message_history_ttl_seconds: int = Field(default=86400, description="TTL de historial de mensajes (24 horas)")
    cleanup_interval_seconds: int = Field(default=300, description="Intervalo de limpieza de datos expirados (5 min)")
    max_sessions_per_user: int = Field(default=5, description="Máximo de sesiones activas por usuario")
    max_session_participants: int = Field(default=50, description="Máximo de participantes por sesión")


class ConflictResolutionConfig(BaseModel):
    """Configuración de resolución de conflictos"""
    max_conflicts_per_session: int = Field(default=10, description="Máximo de conflictos por sesión")
    conflict_timeout_seconds: int = Field(default=3600, description="Timeout de conflictos sin resolver (1 hora)")
    auto_resolution_enabled: bool = Field(default=False, description="Habilitar resolución automática de conflictos")
    escalation_threshold: int = Field(default=3, description="Número de conflictos antes de escalar")
    resolution_strategies: List[str] = Field(
        default=["reassign_tasks", "release_locks", "priority_override", "manual_resolution"],
        description="Estrategias de resolución disponibles"
    )
    priority_conflict_threshold: int = Field(default=2, description="Diferencia de prioridad para conflicto")


class AgentMonitoringConfig(BaseModel):
    """Configuración de monitoreo de agentes"""
    utilization_monitoring_enabled: bool = Field(default=True, description="Habilitar monitoreo de utilización")
    monitoring_interval_seconds: int = Field(default=60, description="Intervalo de monitoreo en segundos")
    health_check_interval_seconds: int = Field(default=300, description="Intervalo de health checks (5 min)")
    utilization_alert_threshold: float = Field(default=90.0, description="Umbral de alerta de utilización (%)")
    idle_agent_threshold_seconds: int = Field(default=1800, description="Tiempo para considerar agente inactivo (30 min)")
    performance_metrics_tracking: bool = Field(default=True, description="Habilitar tracking de métricas de rendimiento")
    max_agent_sessions: int = Field(default=10, description="Máximo de sesiones por agente")


class CollaborationSecurityConfig(BaseModel):
    """Configuración de seguridad para colaboración"""
    authentication_required: bool = Field(default=True, description="Requerir autenticación para colaboración")
    authorization_enabled: bool = Field(default=True, description="Habilitar autorización basada en roles")
    session_validation_enabled: bool = Field(default=True, description="Validar sesiones activas")
    message_validation_enabled: bool = Field(default=True, description="Validar formato de mensajes")
    rate_limiting_enabled: bool = Field(default=True, description="Habilitar rate limiting")
    rate_limit_messages_per_minute: int = Field(default=60, description="Límite de mensajes por minuto")
    max_concurrent_sessions_per_user: int = Field(default=3, description="Máximo de sesiones concurrentes por usuario")
    guest_access_enabled: bool = Field(default=False, description="Habilitar acceso de invitados")
    guest_permissions: List[str] = Field(default=["view_session"], description="Permisos para invitados")


class NotificationConfig(BaseModel):
    """Configuración de notificaciones"""
    real_time_notifications_enabled: bool = Field(default=True, description="Habilitar notificaciones en tiempo real")
    notification_types_enabled: List[str] = Field(
        default=[
            "user_joined", "user_left", "task_assigned", "task_completed",
            "conflict_resolved", "agent_status_change", "session_update"
        ],
        description="Tipos de notificaciones habilitadas"
    )
    notification_history_size: int = Field(default=100, description="Tamaño del historial de notificaciones")
    delivery_methods: List[str] = Field(default=["websocket"], description="Métodos de entrega de notificaciones")
    notification_timeout_seconds: int = Field(default=10, description="Timeout para entrega de notificaciones")
    batch_notifications_enabled: bool = Field(default=True, description="Habilitar notificaciones en lote")


class CollaborationLimitsConfig(BaseModel):
    """Configuración de límites del sistema"""
    max_total_sessions: int = Field(default=1000, description="Máximo total de sesiones activas")
    max_session_name_length: int = Field(default=100, description="Longitud máxima de nombres de sesión")
    max_session_description_length: int = Field(default=500, description="Longitud máxima de descripción de sesión")
    max_context_entries_per_session: int = Field(default=1000, description="Máximo de entradas de contexto por sesión")
    max_tasks_per_session: int = Field(default=500, description="Máximo de tareas por sesión")
    max_locked_resources_per_user: int = Field(default=10, description="Máximo de recursos bloqueados por usuario")
    max_user_permissions: int = Field(default=50, description="Máximo de permisos por usuario")


class CollaborationPerformanceConfig(BaseModel):
    """Configuración de rendimiento"""
    async_workers: int = Field(default=4, description="Número de workers asíncronos")
    message_processing_batch_size: int = Field(default=100, description="Tamaño de lote para procesamiento de mensajes")
    cache_enabled: bool = Field(default=True, description="Habilitar cache en memoria")
    cache_ttl_seconds: int = Field(default=300, description="TTL del cache (5 minutos)")
    compression_threshold_bytes: int = Field(default=1024, description="Umbral de compresión en bytes")
    gc_interval_seconds: int = Field(default=60, description="Intervalo de garbage collection (1 minuto)")
    memory_limit_mb: int = Field(default=512, description="Límite de memoria en MB")


class CollaborationConfig(BaseModel):
    """Configuración completa del sistema de colaboración"""
    
    # Configuración básica
    environment: CollaborationEnvironment = CollaborationEnvironment.DEVELOPMENT
    debug: bool = True
    service_name: str = "mcp-collaboration"
    service_version: str = "1.0.0"
    
    # Configuraciones específicas
    websocket: WebSocketConfig = WebSocketConfig()
    redis: RedisCollaborationConfig = RedisCollaborationConfig()
    conflicts: ConflictResolutionConfig = ConflictResolutionConfig()
    agents: AgentMonitoringConfig = AgentMonitoringConfig()
    security: CollaborationSecurityConfig = CollaborationSecurityConfig()
    notifications: NotificationConfig = NotificationConfig()
    limits: CollaborationLimitsConfig = CollaborationLimitsConfig()
    performance: CollaborationPerformanceConfig = CollaborationPerformanceConfig()
    
    # Configuración de logging específico
    log_level: str = Field(default="INFO", description="Nivel de logging para colaboración")
    log_collaboration_events: bool = Field(default=True, description="Log de eventos de colaboración")
    log_conflicts: bool = Field(default=True, description="Log de conflictos")
    log_agent_updates: bool = Field(default=True, description="Log de actualizaciones de agentes")
    
    # Configuración de métricas
    metrics_enabled: bool = Field(default=True, description="Habilitar métricas de colaboración")
    metrics_port: int = Field(default=9091, description="Puerto de métricas de colaboración")
    health_check_enabled: bool = Field(default=True, description="Habilitar health checks")
    health_check_port: int = Field(default=8082, description="Puerto de health checks")
    
    # Configuración de WebSocket server
    ws_host: str = Field(default="0.0.0.0", description="Host para servidor WebSocket")
    ws_port: int = Field(default=8083, description="Puerto para servidor WebSocket")
    ws_path: str = Field(default="/ws", description="Path base para WebSockets")
    
    # Configuración de fallback
    fallback_to_memory_on_redis_failure: bool = Field(default=True, description="Usar memoria si Redis falla")
    max_memory_sessions: int = Field(default=100, description="Máximo de sesiones en memoria")
    
    def is_production(self) -> bool:
        """Verificar si estamos en producción"""
        return self.environment == CollaborationEnvironment.PRODUCTION
    
    def is_enterprise(self) -> bool:
        """Verificar si estamos en enterprise"""
        return self.environment == CollaborationEnvironment.ENTERPRISE
    
    def get_redis_config_dict(self) -> Dict[str, any]:
        """Obtener configuración de Redis específica para colaboración"""
        return {
            "session_ttl": self.redis.session_ttl_seconds,
            "agent_state_ttl": self.redis.agent_state_ttl_seconds,
            "message_history_ttl": self.redis.message_history_ttl_seconds,
            "max_sessions_per_user": self.redis.max_sessions_per_user,
            "max_session_participants": self.redis.max_session_participants,
            "max_total_sessions": self.limits.max_total_sessions
        }
    
    def get_websocket_config_dict(self) -> Dict[str, any]:
        """Obtener configuración de WebSocket"""
        return {
            "max_connections": self.websocket.max_connections,
            "connection_timeout": self.websocket.connection_timeout,
            "message_size_limit": self.websocket.message_size_limit,
            "heartbeat_interval": self.websocket.heartbeat_interval,
            "compression_enabled": self.websocket.compression_enabled,
            "ssl_enabled": self.websocket.ssl_enabled
        }
    
    def get_conflict_resolution_config_dict(self) -> Dict[str, any]:
        """Obtener configuración de resolución de conflictos"""
        return {
            "max_conflicts_per_session": self.conflicts.max_conflicts_per_session,
            "conflict_timeout_seconds": self.conflicts.conflict_timeout_seconds,
            "auto_resolution_enabled": self.conflicts.auto_resolution_enabled,
            "escalation_threshold": self.conflicts.escalation_threshold,
            "resolution_strategies": self.conflicts.resolution_strategies,
            "priority_conflict_threshold": self.conflicts.priority_conflict_threshold
        }
    
    def get_agent_monitoring_config_dict(self) -> Dict[str, any]:
        """Obtener configuración de monitoreo de agentes"""
        return {
            "utilization_monitoring_enabled": self.agents.utilization_monitoring_enabled,
            "monitoring_interval_seconds": self.agents.monitoring_interval_seconds,
            "health_check_interval_seconds": self.agents.health_check_interval_seconds,
            "utilization_alert_threshold": self.agents.utilization_alert_threshold,
            "idle_agent_threshold_seconds": self.agents.idle_agent_threshold_seconds,
            "max_agent_sessions": self.agents.max_agent_sessions
        }
    
    def validate_config(self) -> List[str]:
        """Validar configuración y retornar lista de errores"""
        errors = []
        
        # Validar límites
        if self.limits.max_total_sessions <= 0:
            errors.append("max_total_sessions debe ser mayor que 0")
        
        if self.websocket.max_connections <= 0:
            errors.append("max_connections debe ser mayor que 0")
        
        if self.redis.max_sessions_per_user <= 0:
            errors.append("max_sessions_per_user debe ser mayor que 0")
        
        if self.conflicts.max_conflicts_per_session <= 0:
            errors.append("max_conflicts_per_session debe ser mayor que 0")
        
        # Validar umbrales
        if not 0 <= self.agents.utilization_alert_threshold <= 100:
            errors.append("utilization_alert_threshold debe estar entre 0 y 100")
        
        # Validar intervalos
        if self.websocket.heartbeat_interval <= 0:
            errors.append("heartbeat_interval debe ser mayor que 0")
        
        if self.agents.monitoring_interval_seconds <= 0:
            errors.append("monitoring_interval_seconds debe ser mayor que 0")
        
        return errors
    
    def apply_environment_overrides(self):
        """Aplicar overrides específicos del entorno"""
        if self.environment == CollaborationEnvironment.PRODUCTION:
            self.debug = False
            self.log_level = "WARNING"
            self.security.rate_limiting_enabled = True
            self.performance.cache_enabled = True
            self.metrics_enabled = True
            self.fallback_to_memory_on_redis_failure = False
            
        elif self.environment == CollaborationEnvironment.ENTERPRISE:
            self.debug = False
            self.log_level = "INFO"
            self.security.rate_limiting_enabled = True
            self.performance.cache_enabled = True
            self.metrics_enabled = True
            self.websocket.max_connections = 5000
            self.limits.max_total_sessions = 10000
            self.redis.max_session_participants = 200
            
        elif self.environment == CollaborationEnvironment.STAGING:
            self.debug = True
            self.log_level = "INFO"
            self.metrics_enabled = True


# Instancia global de configuración de colaboración
collaboration_settings = CollaborationConfig()

# Aplicar overrides de entorno
collaboration_settings.apply_environment_overrides()

# Validar configuración
config_errors = collaboration_settings.validate_config()
if config_errors and collaboration_settings.environment != CollaborationEnvironment.DEVELOPMENT:
    raise ValueError(f"Errores de configuración de colaboración: {', '.join(config_errors)}")


# Configuración por defecto basada en el entorno
def get_collaboration_config_for_environment(env: CollaborationEnvironment) -> CollaborationConfig:
    """Obtener configuración específica para entorno"""
    config = CollaborationConfig()
    config.environment = env
    config.apply_environment_overrides()
    return config


# Configuración de desarrollo
DEV_COLLABORATION_CONFIG = get_collaboration_config_for_environment(CollaborationEnvironment.DEVELOPMENT)

# Configuración de producción
PROD_COLLABORATION_CONFIG = get_collaboration_config_for_environment(CollaborationEnvironment.PRODUCTION)

# Configuración enterprise
ENTERPRISE_COLLABORATION_CONFIG = get_collaboration_config_for_environment(CollaborationEnvironment.ENTERPRISE)


# Funciones de utilidad para configuración
def get_redis_url_for_collaboration() -> str:
    """Obtener URL de Redis específica para colaboración"""
    base_redis_url = settings.redis_url
    
    # Agregar configuración específica si es necesario
    # Por ejemplo: redis://localhost:6379/collaboration
    
    return base_redis_url


def get_websocket_server_config() -> Dict[str, any]:
    """Obtener configuración completa del servidor WebSocket"""
    return {
        "host": collaboration_settings.ws_host,
        "port": collaboration_settings.ws_port,
        "path": collaboration_settings.ws_path,
        **collaboration_settings.get_websocket_config_dict()
    }


def get_collaboration_metrics_config() -> Dict[str, any]:
    """Obtener configuración de métricas de colaboración"""
    return {
        "enabled": collaboration_settings.metrics_enabled,
        "port": collaboration_settings.metrics_port,
        "service_name": collaboration_settings.service_name
    }


# Configuración de integración con sistema principal
COLLABORATION_INTEGRATION_CONFIG = {
    "enabled": True,
    "auto_register_agents": True,
    "session_auto_cleanup": True,
    "conflict_auto_detection": True,
    "real_time_sync": True,
    "webhook_endpoints": {
        "session_created": "/api/v1/collaboration/sessions",
        "user_joined": "/api/v1/collaboration/users",
        "task_updated": "/api/v1/collaboration/tasks",
        "conflict_resolved": "/api/v1/collaboration/conflicts"
    }
}


# Validación de dependencias externas
def validate_collaboration_dependencies():
    """Validar que todas las dependencias estén disponibles"""
    dependencies = ["redis", "websockets", "asyncio"]
    
    missing = []
    for dep in dependencies:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)
    
    if missing:
        raise ImportError(f"Dependencias faltantes para colaboración: {', '.join(missing)}")


# Auto-validación al importar
try:
    validate_collaboration_dependencies()
except ImportError as e:
    if collaboration_settings.environment == CollaborationEnvironment.PRODUCTION:
        raise
    else:
        import warnings
        warnings.warn(f"Advertencia de dependencias de colaboración: {e}", UserWarning)


__all__ = [
    "CollaborationConfig",
    "CollaborationEnvironment", 
    "WebSocketConfig",
    "RedisCollaborationConfig",
    "ConflictResolutionConfig",
    "AgentMonitoringConfig",
    "CollaborationSecurityConfig",
    "NotificationConfig",
    "CollaborationLimitsConfig",
    "CollaborationPerformanceConfig",
    "collaboration_settings",
    "DEV_COLLABORATION_CONFIG",
    "PROD_COLLABORATION_CONFIG",
    "ENTERPRISE_COLLABORATION_CONFIG",
    "get_collaboration_config_for_environment",
    "get_redis_url_for_collaboration",
    "get_websocket_server_config",
    "get_collaboration_metrics_config",
    "COLLABORATION_INTEGRATION_CONFIG",
    "validate_collaboration_dependencies"
]