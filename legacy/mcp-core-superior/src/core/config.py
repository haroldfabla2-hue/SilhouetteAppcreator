"""
Configuración centralizada para MCP Core Superior
Gestiona todas las configuraciones del sistema de manera type-safe
"""
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
import os
from enum import Enum


class LogLevel(str, Enum):
    """Niveles de logging disponibles"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    """Entornos de ejecución"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class MCPCoreSettings(BaseSettings):
    """Configuraciones principales del MCP Core Superior"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="MCP_CORE_"
    )
    
    # === CONFIGURACIÓN BÁSICA ===
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    app_name: str = "MCP Core Superior"
    app_version: str = "1.0.0"
    
    # === PUERTOS Y HOSTS ===
    host: str = "0.0.0.0"
    port: int = 8080
    mcp_port: int = 8081
    
    # === CONTEXTFORGE GATEWAY ===
    contextforge_url: str = Field(default="http://localhost:8001", description="URL del ContextForge Gateway")
    contextforge_api_key: Optional[str] = Field(default=None, description="API Key para ContextForge")
    contextforge_timeout: int = Field(default=30, description="Timeout para requests a ContextForge")
    
    # === BASE DE DATOS ===
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/mcp_core",
        description="URL de conexión a PostgreSQL"
    )
    database_pool_size: int = Field(default=10, description="Tamaño del pool de conexiones")
    database_max_overflow: int = Field(default=20, description="Máximo overflow del pool")
    database_pool_timeout: int = Field(default=30, description="Timeout del pool")
    
    # === VECTOR STORE ===
    vector_db_url: str = Field(
        default="postgresql://user:password@localhost:5432/vector_db",
        description="URL de conexión a Vector Store"
    )
    vector_db_pool_size: int = Field(default=5, description="Tamaño del pool de Vector DB")
    embedding_model: str = Field(default="text-embedding-ada-002", description="Modelo de embeddings")
    embedding_dimension: int = Field(default=1536, description="Dimensión de embeddings")
    
    # === REDIS CACHE ===
    redis_url: str = Field(default="redis://localhost:6379", description="URL de Redis")
    redis_pool_size: int = Field(default=10, description="Tamaño del pool de Redis")
    redis_timeout: int = Field(default=30, description="Timeout de Redis")
    
    # === AUTENTICACIÓN ===
    jwt_secret: str = Field(description="Secret para JWT")
    jwt_algorithm: str = Field(default="HS256", description="Algoritmo JWT")
    jwt_expiration_hours: int = Field(default=24, description="Expiración de JWT en horas")
    
    # === PERFORMANCE ===
    max_concurrent_tasks: int = Field(default=10, description="Máximo de tareas concurrentes")
    max_concurrent_tools: int = Field(default=5, description="Máximo de herramientas por tarea")
    default_timeout_seconds: int = Field(default=300, description="Timeout por defecto en segundos")
    streaming_buffer_size: int = Field(default=1000, description="Tamaño del buffer de streaming")
    
    # === STREAMING ===
    streaming_enabled: bool = Field(default=True, description="Habilitar streaming")
    streaming_frequency: float = Field(default=1.0, description="Frecuencia de updates en segundos")
    streaming_max_duration: int = Field(default=3600, description="Duración máxima de streaming")
    
    # === RATE LIMITING ===
    rate_limit_enabled: bool = Field(default=True, description="Habilitar rate limiting")
    rate_limit_requests: int = Field(default=100, description="Requests por minuto")
    rate_limit_window: int = Field(default=60, description="Ventana de rate limiting en segundos")
    
    # === LOGGING ===
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Nivel de logging")
    log_format: str = Field(
        default="json",
        description="Formato de logging (json/text)"
    )
    log_file: Optional[str] = Field(default=None, description="Archivo de log")
    log_max_size: int = Field(default=100, description="Tamaño máximo del log en MB")
    log_backup_count: int = Field(default=5, description="Número de backups de log")
    
    # === MONITOREO ===
    metrics_enabled: bool = Field(default=True, description="Habilitar métricas")
    metrics_port: int = Field(default=9090, description="Puerto de métricas Prometheus")
    tracing_enabled: bool = Field(default=False, description="Habilitar distributed tracing")
    
    # === AGENTES ===
    agent_timeout_seconds: int = Field(default=60, description="Timeout por agente")
    agent_retry_attempts: int = Field(default=3, description="Intentos de retry por agente")
    agent_retry_delay: float = Field(default=1.0, description="Delay entre retries")
    
    # === EXECUTOR ===
    executor_max_workers: int = Field(default=4, description="Máximo workers para executor")
    executor_memory_limit_mb: int = Field(default=512, description="Límite de memoria por ejecución")
    executor_cpu_limit: float = Field(default=1.0, description="Límite de CPU por ejecución")
    
    # === MEMORY MANAGER ===
    memory_cache_size: int = Field(default=1000, description="Tamaño del cache de memoria")
    memory_cleanup_interval: int = Field(default=3600, description="Intervalo de cleanup en segundos")
    memory_max_age_hours: int = Field(default=24, description="Edad máxima de elementos en memoria")
    
    # === VERIFIER ===
    verification_quality_threshold: float = Field(default=0.8, description="Umbral de calidad mínimo")
    verification_strict_mode: bool = Field(default=False, description="Modo estricto de verificación")
    
    # === HEALTH CHECKS ===
    health_check_interval: int = Field(default=30, description="Intervalo de health checks")
    health_check_timeout: int = Field(default=10, description="Timeout de health checks")
    
    # === CORS ===
    cors_enabled: bool = Field(default=True, description="Habilitar CORS")
    cors_origins: List[str] = Field(default=["*"], description="Orígenes permitidos")
    cors_methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE"], description="Métodos permitidos")
    cors_headers: List[str] = Field(default=["*"], description="Headers permitidos")
    
    @validator("jwt_secret")
    def validate_jwt_secret(cls, v):
        """Validar que JWT secret esté configurado en producción"""
        if not v:
            raise ValueError("JWT_SECRET debe estar configurado")
        return v
    
    @validator("database_url")
    def validate_database_url(cls, v):
        """Validar formato de URL de base de datos"""
        if not v.startswith(("postgresql://", "postgres://")):
            raise ValueError("DATABASE_URL debe ser una URL de PostgreSQL válida")
        return v
    
    @validator("max_concurrent_tasks")
    def validate_max_concurrent_tasks(cls, v):
        """Validar límite de tareas concurrentes"""
        if v < 1 or v > 100:
            raise ValueError("MAX_CONCURRENT_TASKS debe estar entre 1 y 100")
        return v
    
    @validator("streaming_frequency")
    def validate_streaming_frequency(cls, v):
        """Validar frecuencia de streaming"""
        if v < 0.1 or v > 10.0:
            raise ValueError("STREAMING_FREQUENCY debe estar entre 0.1 y 10.0 segundos")
        return v
    
    @validator("verification_quality_threshold")
    def validate_quality_threshold(cls, v):
        """Validar umbral de calidad"""
        if v < 0.0 or v > 1.0:
            raise ValueError("VERIFICATION_QUALITY_THRESHOLD debe estar entre 0.0 y 1.0")
        return v
    
    def is_production(self) -> bool:
        """Verificar si estamos en producción"""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Verificar si estamos en desarrollo"""
        return self.environment == Environment.DEVELOPMENT
    
    def get_database_config(self) -> dict:
        """Obtener configuración de base de datos para SQLAlchemy"""
        return {
            "pool_size": self.database_pool_size,
            "max_overflow": self.database_max_overflow,
            "pool_timeout": self.database_pool_timeout,
            "pool_recycle": 3600,
            "pool_pre_ping": True
        }
    
    def get_vector_db_config(self) -> dict:
        """Obtener configuración de Vector DB para asyncpg"""
        return {
            "server_settings": {
                "jit": "off"
            }
        }
    
    def get_redis_config(self) -> dict:
        """Obtener configuración de Redis"""
        return {
            "max_connections": self.redis_pool_size,
            "socket_timeout": self.redis_timeout,
            "socket_connect_timeout": self.redis_timeout,
            "retry_on_timeout": True,
            "health_check_interval": 30
        }


# Instancia global de configuración
settings = MCPCoreSettings()


# Configuración específica por entorno
def get_environment_config() -> dict:
    """Obtener configuración específica del entorno actual"""
    env = settings.environment
    
    base_config = {
        "debug": settings.debug,
        "log_level": settings.log_level,
        "metrics_enabled": settings.metrics_enabled,
        "streaming_enabled": settings.streaming_enabled
    }
    
    if env == Environment.PRODUCTION:
        base_config.update({
            "debug": False,
            "log_level": LogLevel.WARNING,
            "metrics_enabled": True,
            "streaming_enabled": True,
            "rate_limit_enabled": True,
            "health_check_interval": 15
        })
    elif env == Environment.STAGING:
        base_config.update({
            "debug": True,
            "log_level": LogLevel.INFO,
            "metrics_enabled": True,
            "streaming_enabled": True,
            "rate_limit_enabled": True
        })
    else:  # DEVELOPMENT
        base_config.update({
            "debug": True,
            "log_level": LogLevel.DEBUG,
            "metrics_enabled": True,
            "streaming_enabled": True,
            "rate_limit_enabled": False
        })
    
    return base_config


# Validación de dependencias
def validate_dependencies() -> None:
    """Validar que todas las dependencias necesarias estén configuradas"""
    required_vars = [
        "database_url",
        "vector_db_url", 
        "jwt_secret"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Variables de entorno requeridas faltantes: {', '.join(missing_vars)}")


# Configuración de seguridad
def get_security_config() -> dict:
    """Obtener configuración de seguridad"""
    return {
        "jwt_secret": settings.jwt_secret,
        "jwt_algorithm": settings.jwt_algorithm,
        "jwt_expiration_hours": settings.jwt_expiration_hours,
        "rate_limit_enabled": settings.rate_limit_enabled,
        "rate_limit_requests": settings.rate_limit_requests,
        "rate_limit_window": settings.rate_limit_window,
        "cors_enabled": settings.cors_enabled,
        "cors_origins": settings.cors_origins,
        "cors_methods": settings.cors_methods,
        "cors_headers": settings.cors_headers
    }


# Validar configuración al importar
try:
    validate_dependencies()
except ValueError as e:
    if settings.environment == Environment.PRODUCTION:
        raise
    else:
        # En desarrollo, solo warning
        import warnings
        warnings.warn(f"Configuración incompleta: {e}", UserWarning)
