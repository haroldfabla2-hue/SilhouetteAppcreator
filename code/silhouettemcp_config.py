"""
SilhouetteMCP - Configuración Centralizada
==========================================

Archivo de configuración centralizada para todos los puertos, endpoints y sistemas
del ecosistema SilhouetteMCP. Incluye sistemas originales, mejorados, configuraciones
de seguridad, load balancing, auto-scaling y endpoints unificados.

Autor: Sistema SilhouetteMCP
Fecha: 2025-11-06
Versión: 4.0.0
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
import os

class EnvironmentType(Enum):
    """Tipos de entorno de despliegue"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ENTERPRISE = "enterprise"

class LoadBalancingStrategy(Enum):
    """Estrategias de balanceador de carga"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    IP_HASH = "ip_hash"
    RANDOM = "random"

class SecurityLevel(Enum):
    """Niveles de seguridad"""
    BASIC = "basic"
    ENHANCED = "enhanced"
    ENTERPRISE = "enterprise"
    MILITARY_GRADE = "military_grade"

@dataclass
class PortConfig:
    """Configuración de puerto individual"""
    port: int
    service_name: str
    protocol: str = "http"
    ssl_enabled: bool = False
    max_connections: int = 1000
    timeout: int = 30
    health_check_path: str = "/health"
    service_type: str = "api"
    priority: int = 1
    weight: int = 1

@dataclass
class SecurityConfig:
    """Configuración de seguridad completa"""
    security_level: SecurityLevel
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600
    csrf_protection: bool = True
    rate_limiting: bool = True
    ddos_protection: bool = True
    encryption_level: str = "AES-256"
    api_key_required: bool = True
    audit_logging: bool = True
    cors_enabled: bool = True
    cors_origins: List[str] = None
    allowed_methods: List[str] = None
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]
        if self.allowed_methods is None:
            self.allowed_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]

@dataclass
class LoadBalancerConfig:
    """Configuración de balanceador de carga"""
    strategy: LoadBalancingStrategy
    health_check_interval: int = 30
    health_check_timeout: int = 5
    health_check_path: str = "/health"
    failure_threshold: int = 3
    recovery_threshold: int = 2
    session_affinity: bool = False
    sticky_session: bool = False
    circuit_breaker: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    retry_attempts: int = 3
    retry_delay: float = 1.0

@dataclass
class AutoScalingConfig:
    """Configuración de auto-escalado"""
    enabled: bool = True
    min_replicas: int = 2
    max_replicas: int = 50
    target_cpu_utilization: int = 70
    target_memory_utilization: int = 80
    scale_up_cooldown: int = 300
    scale_down_cooldown: int = 300
    scale_up_policy: str = "cpu"
    scale_down_policy: str = "memory"
    custom_metrics: List[str] = None
    advanced_policies: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_metrics is None:
            self.custom_metrics = ["request_count", "response_time"]
        if self.advanced_policies is None:
            self.advanced_policies = {}

@dataclass
class UnifiedEndpoint:
    """Endpoint unificado"""
    name: str
    path: str
    target_services: List[str]
    method: str = "GET"
    authentication_required: bool = True
    rate_limit_per_minute: int = 100
    cache_ttl: int = 300
    description: str = ""
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = ["api", "unified"]

class SilhouetteMCPConfig:
    """
    Configuración centralizada del sistema SilhouetteMCP
    ==================================================
    """
    
    def __init__(self, environment: EnvironmentType = EnvironmentType.PRODUCTION):
        self.environment = environment
        self.version = "4.0.0"
        self.build_date = "2025-11-06"
        
        # === PUERTOS DE SISTEMAS ORIGINALES (8001-8002) ===
        self.original_systems_ports = {
            8001: PortConfig(
                port=8001,
                service_name="silhouettemcp_core",
                protocol="http",
                ssl_enabled=False,
                max_connections=500,
                timeout=30,
                health_check_path="/health",
                service_type="core",
                priority=1,
                weight=1
            ),
            8002: PortConfig(
                port=8002,
                service_name="silhouettemcp_api",
                protocol="http",
                ssl_enabled=False,
                max_connections=800,
                timeout=30,
                health_check_path="/api/health",
                service_type="api",
                priority=2,
                weight=1
            )
        }
        
        # === PUERTOS DE SISTEMAS MEJORADOS (8007-8024) ===
        self.enhanced_systems_ports = {
            # Sistemas Core Mejorados
            8007: PortConfig(
                port=8007,
                service_name="enhanced_core_engine",
                protocol="https",
                ssl_enabled=True,
                max_connections=2000,
                timeout=45,
                health_check_path="/health",
                service_type="core",
                priority=1,
                weight=2
            ),
            8008: PortConfig(
                port=8008,
                service_name="enhanced_api_gateway",
                protocol="https",
                ssl_enabled=True,
                max_connections=3000,
                timeout=30,
                health_check_path="/api/gateway/health",
                service_type="gateway",
                priority=1,
                weight=3
            ),
            
            # Sistemas de Base de Datos
            8009: PortConfig(
                port=8009,
                service_name="database_operations",
                protocol="https",
                ssl_enabled=True,
                max_connections=1500,
                timeout=60,
                health_check_path="/db/health",
                service_type="database",
                priority=2,
                weight=2
            ),
            8010: PortConfig(
                port=8010,
                service_name="vector_store",
                protocol="https",
                ssl_enabled=True,
                max_connections=1200,
                timeout=45,
                health_check_path="/vector/health",
                service_type="storage",
                priority=2,
                weight=2
            ),
            
            # Sistemas de Agentes Especializados
            8011: PortConfig(
                port=8011,
                service_name="analytics_agent",
                protocol="https",
                ssl_enabled=True,
                max_connections=1000,
                timeout=40,
                health_check_path="/agent/analytics/health",
                service_type="agent",
                priority=3,
                weight=1
            ),
            8012: PortConfig(
                port=8012,
                service_name="financial_agent",
                protocol="https",
                ssl_enabled=True,
                max_connections=800,
                timeout=45,
                health_check_path="/agent/financial/health",
                service_type="agent",
                priority=3,
                weight=1
            ),
            8013: PortConfig(
                port=8013,
                service_name="web_scraping_agent",
                protocol="https",
                ssl_enabled=True,
                max_connections=1200,
                timeout=60,
                health_check_path="/agent/scraping/health",
                service_type="agent",
                priority=3,
                weight=1
            ),
            8014: PortConfig(
                port=8014,
                service_name="git_operations_agent",
                protocol="https",
                ssl_enabled=True,
                max_connections=600,
                timeout=30,
                health_check_path="/agent/git/health",
                service_type="agent",
                priority=3,
                weight=1
            ),
            8015: PortConfig(
                port=8015,
                service_name="python_executor_agent",
                protocol="https",
                ssl_enabled=True,
                max_connections=900,
                timeout=90,
                health_check_path="/agent/python/health",
                service_type="agent",
                priority=3,
                weight=1
            ),
            8016: PortConfig(
                port=8016,
                service_name="search_engine_agent",
                protocol="https",
                ssl_enabled=True,
                max_connections=1000,
                timeout=30,
                health_check_path="/agent/search/health",
                service_type="agent",
                priority=3,
                weight=1
            ),
            
            # Sistemas de Orquestación
            8017: PortConfig(
                port=8017,
                service_name="multi_agent_orchestrator",
                protocol="https",
                ssl_enabled=True,
                max_connections=2000,
                timeout=60,
                health_check_path="/orchestrator/health",
                service_type="orchestrator",
                priority=1,
                weight=2
            ),
            8018: PortConfig(
                port=8018,
                service_name="task_manager",
                protocol="https",
                ssl_enabled=True,
                max_connections=1500,
                timeout=45,
                health_check_path="/tasks/health",
                service_type="management",
                priority=2,
                weight=2
            ),
            
            # Sistemas de Monitoreo y Observabilidad
            8019: PortConfig(
                port=8019,
                service_name="advanced_metrics",
                protocol="https",
                ssl_enabled=True,
                max_connections=800,
                timeout=30,
                health_check_path="/metrics/health",
                service_type="monitoring",
                priority=3,
                weight=1
            ),
            8020: PortConfig(
                port=8020,
                service_name="observability",
                protocol="https",
                ssl_enabled=True,
                max_connections=600,
                timeout=30,
                health_check_path="/observability/health",
                service_type="monitoring",
                priority=3,
                weight=1
            ),
            
            # Sistemas de Seguridad
            8021: PortConfig(
                port=8021,
                service_name="security_system",
                protocol="https",
                ssl_enabled=True,
                max_connections=1000,
                timeout=30,
                health_check_path="/security/health",
                service_type="security",
                priority=1,
                weight=2
            ),
            8022: PortConfig(
                port=8022,
                service_name="ddos_protection",
                protocol="https",
                ssl_enabled=True,
                max_connections=2000,
                timeout=15,
                health_check_path="/protection/health",
                service_type="security",
                priority=1,
                weight=3
            ),
            
            # Sistemas de Auto-healing
            8023: PortConfig(
                port=8023,
                service_name="auto_healing",
                protocol="https",
                ssl_enabled=True,
                max_connections=800,
                timeout=30,
                health_check_path="/healing/health",
                service_type="healing",
                priority=2,
                weight=2
            ),
            
            # Sistemas de Comunicación
            8024: PortConfig(
                port=8024,
                service_name="collaboration_engine",
                protocol="https",
                ssl_enabled=True,
                max_connections=1500,
                timeout=45,
                health_check_path="/collaboration/health",
                service_type="communication",
                priority=2,
                weight=2
            )
        }
        
        # === CONFIGURACIONES DE SEGURIDAD ===
        self.security_configs = {
            SecurityLevel.BASIC: SecurityConfig(
                security_level=SecurityLevel.BASIC,
                jwt_secret_key=os.getenv("JWT_SECRET_BASIC", "basic-secret-key-2025"),
                jwt_expiration=1800,
                csrf_protection=True,
                rate_limiting=True,
                ddos_protection=False,
                encryption_level="AES-128",
                api_key_required=False,
                audit_logging=False,
                cors_enabled=True
            ),
            SecurityLevel.ENHANCED: SecurityConfig(
                security_level=SecurityLevel.ENHANCED,
                jwt_secret_key=os.getenv("JWT_SECRET_ENHANCED", "enhanced-secret-key-2025"),
                jwt_expiration=3600,
                csrf_protection=True,
                rate_limiting=True,
                ddos_protection=True,
                encryption_level="AES-256",
                api_key_required=True,
                audit_logging=True,
                cors_enabled=True
            ),
            SecurityLevel.ENTERPRISE: SecurityConfig(
                security_level=SecurityLevel.ENTERPRISE,
                jwt_secret_key=os.getenv("JWT_SECRET_ENTERPRISE", "enterprise-secret-key-2025"),
                jwt_expiration=7200,
                csrf_protection=True,
                rate_limiting=True,
                ddos_protection=True,
                encryption_level="AES-256-GCM",
                api_key_required=True,
                audit_logging=True,
                cors_enabled=True,
                cors_origins=["https://*.silhouettemcp.com", "https://*.company.com"]
            ),
            SecurityLevel.MILITARY_GRADE: SecurityConfig(
                security_level=SecurityLevel.MILITARY_GRADE,
                jwt_secret_key=os.getenv("JWT_SECRET_MILITARY", "military-grade-secret-key-2025"),
                jwt_expiration=3600,
                csrf_protection=True,
                rate_limiting=True,
                ddos_protection=True,
                encryption_level="AES-256-GCM",
                api_key_required=True,
                audit_logging=True,
                cors_enabled=False,
                cors_origins=[],
                allowed_methods=["GET", "POST"]
            )
        }
        
        # === CONFIGURACIONES DE LOAD BALANCING ===
        self.load_balancer_configs = {
            LoadBalancingStrategy.ROUND_ROBIN: LoadBalancerConfig(
                strategy=LoadBalancingStrategy.ROUND_ROBIN,
                health_check_interval=30,
                health_check_timeout=5,
                failure_threshold=3,
                recovery_threshold=2,
                session_affinity=False,
                circuit_breaker=True
            ),
            LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN: LoadBalancerConfig(
                strategy=LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN,
                health_check_interval=30,
                health_check_timeout=5,
                failure_threshold=3,
                recovery_threshold=2,
                session_affinity=True,
                sticky_session=True,
                circuit_breaker=True
            ),
            LoadBalancingStrategy.LEAST_CONNECTIONS: LoadBalancerConfig(
                strategy=LoadBalancingStrategy.LEAST_CONNECTIONS,
                health_check_interval=15,
                health_check_timeout=3,
                failure_threshold=2,
                recovery_threshold=2,
                session_affinity=True,
                circuit_breaker=True
            ),
            LoadBalancingStrategy.IP_HASH: LoadBalancerConfig(
                strategy=LoadBalancingStrategy.IP_HASH,
                health_check_interval=45,
                health_check_timeout=10,
                failure_threshold=5,
                recovery_threshold=3,
                session_affinity=True,
                sticky_session=True,
                circuit_breaker=False
            ),
            LoadBalancingStrategy.RANDOM: LoadBalancerConfig(
                strategy=LoadBalancingStrategy.RANDOM,
                health_check_interval=20,
                health_check_timeout=5,
                failure_threshold=3,
                recovery_threshold=2,
                session_affinity=False,
                circuit_breaker=True
            )
        }
        
        # === CONFIGURACIONES DE AUTO-SCALING ===
        self.auto_scaling_configs = {
            EnvironmentType.DEVELOPMENT: AutoScalingConfig(
                enabled=True,
                min_replicas=1,
                max_replicas=5,
                target_cpu_utilization=80,
                target_memory_utilization=85,
                scale_up_cooldown=120,
                scale_down_cooldown=180
            ),
            EnvironmentType.STAGING: AutoScalingConfig(
                enabled=True,
                min_replicas=2,
                max_replicas=10,
                target_cpu_utilization=70,
                target_memory_utilization=80,
                scale_up_cooldown=180,
                scale_down_cooldown=240
            ),
            EnvironmentType.PRODUCTION: AutoScalingConfig(
                enabled=True,
                min_replicas=3,
                max_replicas=30,
                target_cpu_utilization=65,
                target_memory_utilization=75,
                scale_up_cooldown=300,
                scale_down_cooldown=600,
                custom_metrics=["request_count", "response_time", "error_rate"]
            ),
            EnvironmentType.ENTERPRISE: AutoScalingConfig(
                enabled=True,
                min_replicas=5,
                max_replicas=100,
                target_cpu_utilization=60,
                target_memory_utilization=70,
                scale_up_cooldown=180,
                scale_down_cooldown=900,
                custom_metrics=[
                    "request_count", "response_time", "error_rate",
                    "queue_length", "processing_time", "throughput"
                ],
                advanced_policies={
                    "predictive_scaling": True,
                    "scale_on_queue_depth": True,
                    "scale_on_latency": True,
                    "aggressive_scale_up": False,
                    "conservative_scale_down": True
                }
            )
        }
        
        # === ENDPOINTS UNIFICADOS ===
        self.unified_endpoints = [
            # Endpoints Core
            UnifiedEndpoint(
                name="health_check",
                path="/api/v1/health",
                target_services=["silhouettemcp_core", "enhanced_core_engine"],
                method="GET",
                authentication_required=False,
                rate_limit_per_minute=1000,
                cache_ttl=30,
                description="Verificación de salud del sistema",
                tags=["health", "core"]
            ),
            UnifiedEndpoint(
                name="system_status",
                path="/api/v1/status",
                target_services=["enhanced_api_gateway", "multi_agent_orchestrator"],
                method="GET",
                authentication_required=True,
                rate_limit_per_minute=500,
                cache_ttl=60,
                description="Estado completo del sistema",
                tags=["status", "monitoring"]
            ),
            
            # Endpoints de Agentes
            UnifiedEndpoint(
                name="agent_execute",
                path="/api/v1/agents/execute",
                target_services=[
                    "analytics_agent", "financial_agent", "web_scraping_agent",
                    "git_operations_agent", "python_executor_agent", "search_engine_agent"
                ],
                method="POST",
                authentication_required=True,
                rate_limit_per_minute=300,
                cache_ttl=0,
                description="Ejecución de agentes especializados",
                tags=["agents", "execution"]
            ),
            UnifiedEndpoint(
                name="agent_status",
                path="/api/v1/agents/status",
                target_services=["multi_agent_orchestrator"],
                method="GET",
                authentication_required=True,
                rate_limit_per_minute=1000,
                cache_ttl=30,
                description="Estado de los agentes",
                tags=["agents", "status"]
            ),
            
            # Endpoints de Base de Datos
            UnifiedEndpoint(
                name="database_query",
                path="/api/v1/database/query",
                target_services=["database_operations", "vector_store"],
                method="POST",
                authentication_required=True,
                rate_limit_per_minute=200,
                cache_ttl=0,
                description="Consultas de base de datos",
                tags=["database", "query"]
            ),
            UnifiedEndpoint(
                name="database_health",
                path="/api/v1/database/health",
                target_services=["database_operations", "vector_store"],
                method="GET",
                authentication_required=False,
                rate_limit_per_minute=1000,
                cache_ttl=30,
                description="Salud de bases de datos",
                tags=["database", "health"]
            ),
            
            # Endpoints de Tareas
            UnifiedEndpoint(
                name="task_create",
                path="/api/v1/tasks/create",
                target_services=["task_manager", "multi_agent_orchestrator"],
                method="POST",
                authentication_required=True,
                rate_limit_per_minute=500,
                cache_ttl=0,
                description="Crear nueva tarea",
                tags=["tasks", "create"]
            ),
            UnifiedEndpoint(
                name="task_status",
                path="/api/v1/tasks/{task_id}",
                target_services=["task_manager"],
                method="GET",
                authentication_required=True,
                rate_limit_per_minute=1000,
                cache_ttl=30,
                description="Estado de tarea específica",
                tags=["tasks", "status"]
            ),
            UnifiedEndpoint(
                name="task_list",
                path="/api/v1/tasks/list",
                target_services=["task_manager"],
                method="GET",
                authentication_required=True,
                rate_limit_per_minute=300,
                cache_ttl=60,
                description="Listar tareas",
                tags=["tasks", "list"]
            ),
            
            # Endpoints de Monitoreo
            UnifiedEndpoint(
                name="metrics",
                path="/api/v1/metrics",
                target_services=["advanced_metrics", "observability"],
                method="GET",
                authentication_required=True,
                rate_limit_per_minute=600,
                cache_ttl=120,
                description="Métricas del sistema",
                tags=["metrics", "monitoring"]
            ),
            UnifiedEndpoint(
                name="logs",
                path="/api/v1/logs",
                target_services=["observability"],
                method="GET",
                authentication_required=True,
                rate_limit_per_minute=100,
                cache_ttl=300,
                description="Logs del sistema",
                tags=["logs", "monitoring"]
            ),
            
            # Endpoints de Seguridad
            UnifiedEndpoint(
                name="security_check",
                path="/api/v1/security/check",
                target_services=["security_system", "ddos_protection"],
                method="POST",
                authentication_required=True,
                rate_limit_per_minute=1000,
                cache_ttl=30,
                description="Verificación de seguridad",
                tags=["security", "check"]
            ),
            UnifiedEndpoint(
                name="security_status",
                path="/api/v1/security/status",
                target_services=["security_system"],
                method="GET",
                authentication_required=True,
                rate_limit_per_minute=500,
                cache_ttl=60,
                description="Estado de seguridad",
                tags=["security", "status"]
            ),
            
            # Endpoints de Auto-healing
            UnifiedEndpoint(
                name="healing_trigger",
                path="/api/v1/healing/trigger",
                target_services=["auto_healing"],
                method="POST",
                authentication_required=True,
                rate_limit_per_minute=100,
                cache_ttl=0,
                description="Disparar auto-healing",
                tags=["healing", "trigger"]
            ),
            UnifiedEndpoint(
                name="healing_status",
                path="/api/v1/healing/status",
                target_services=["auto_healing"],
                method="GET",
                authentication_required=True,
                rate_limit_per_minute=300,
                cache_ttl=30,
                description="Estado de auto-healing",
                tags=["healing", "status"]
            ),
            
            # Endpoints de Colaboración
            UnifiedEndpoint(
                name="collaboration_session",
                path="/api/v1/collaboration/session",
                target_services=["collaboration_engine"],
                method="POST",
                authentication_required=True,
                rate_limit_per_minute=200,
                cache_ttl=0,
                description="Nueva sesión de colaboración",
                tags=["collaboration", "session"]
            ),
            UnifiedEndpoint(
                name="collaboration_status",
                path="/api/v1/collaboration/status",
                target_services=["collaboration_engine"],
                method="GET",
                authentication_required=True,
                rate_limit_per_minute=500,
                cache_ttl=30,
                description="Estado de colaboraciones",
                tags=["collaboration", "status"]
            )
        ]
    
    def get_all_ports(self) -> Dict[int, PortConfig]:
        """Obtiene todos los puertos configurados"""
        all_ports = {}
        all_ports.update(self.original_systems_ports)
        all_ports.update(self.enhanced_systems_ports)
        return all_ports
    
    def get_port_config(self, port: int) -> Optional[PortConfig]:
        """Obtiene configuración específica de puerto"""
        all_ports = self.get_all_ports()
        return all_ports.get(port)
    
    def get_service_ports(self, service_name: str) -> List[int]:
        """Obtiene puertos por nombre de servicio"""
        all_ports = self.get_all_ports()
        return [port for port, config in all_ports.items() 
                if config.service_name == service_name]
    
    def get_ports_by_type(self, service_type: str) -> List[int]:
        """Obtiene puertos por tipo de servicio"""
        all_ports = self.get_all_ports()
        return [port for port, config in all_ports.items() 
                if config.service_type == service_type]
    
    def get_security_config(self, level: SecurityLevel) -> SecurityConfig:
        """Obtiene configuración de seguridad"""
        return self.security_configs.get(level, self.security_configs[SecurityLevel.ENHANCED])
    
    def get_load_balancer_config(self, strategy: LoadBalancingStrategy) -> LoadBalancerConfig:
        """Obtiene configuración de balanceador de carga"""
        return self.load_balancer_configs.get(
            strategy, 
            self.load_balancer_configs[LoadBalancingStrategy.ROUND_ROBIN]
        )
    
    def get_auto_scaling_config(self, environment: EnvironmentType = None) -> AutoScalingConfig:
        """Obtiene configuración de auto-escalado"""
        if environment is None:
            environment = self.environment
        return self.auto_scaling_configs.get(
            environment,
            self.auto_scaling_configs[EnvironmentType.PRODUCTION]
        )
    
    def get_unified_endpoint(self, name: str) -> Optional[UnifiedEndpoint]:
        """Obtiene endpoint unificado por nombre"""
        for endpoint in self.unified_endpoints:
            if endpoint.name == name:
                return endpoint
        return None
    
    def get_endpoints_by_tag(self, tag: str) -> List[UnifiedEndpoint]:
        """Obtiene endpoints por tag"""
        return [endpoint for endpoint in self.unified_endpoints if tag in endpoint.tags]
    
    def get_endpoints_by_service(self, service_name: str) -> List[UnifiedEndpoint]:
        """Obtiene endpoints que apuntan a un servicio específico"""
        return [endpoint for endpoint in self.unified_endpoints 
                if service_name in endpoint.target_services]
    
    def export_config(self) -> Dict[str, Any]:
        """Exporta toda la configuración como diccionario"""
        return {
            "version": self.version,
            "build_date": self.build_date,
            "environment": self.environment.value,
            "original_systems_ports": {
                str(port): {
                    "service_name": config.service_name,
                    "protocol": config.protocol,
                    "ssl_enabled": config.ssl_enabled,
                    "max_connections": config.max_connections,
                    "timeout": config.timeout,
                    "health_check_path": config.health_check_path,
                    "service_type": config.service_type,
                    "priority": config.priority,
                    "weight": config.weight
                }
                for port, config in self.original_systems_ports.items()
            },
            "enhanced_systems_ports": {
                str(port): {
                    "service_name": config.service_name,
                    "protocol": config.protocol,
                    "ssl_enabled": config.ssl_enabled,
                    "max_connections": config.max_connections,
                    "timeout": config.timeout,
                    "health_check_path": config.health_check_path,
                    "service_type": config.service_type,
                    "priority": config.priority,
                    "weight": config.weight
                }
                for port, config in self.enhanced_systems_ports.items()
            },
            "unified_endpoints": [
                {
                    "name": endpoint.name,
                    "path": endpoint.path,
                    "target_services": endpoint.target_services,
                    "method": endpoint.method,
                    "authentication_required": endpoint.authentication_required,
                    "rate_limit_per_minute": endpoint.rate_limit_per_minute,
                    "cache_ttl": endpoint.cache_ttl,
                    "description": endpoint.description,
                    "tags": endpoint.tags
                }
                for endpoint in self.unified_endpoints
            ]
        }
    
    def validate_config(self) -> Dict[str, Any]:
        """Valida la configuración actual"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "summary": {}
        }
        
        # Validar puertos duplicados
        all_ports = self.get_all_ports()
        port_services = {}
        for port, config in all_ports.items():
            if port in port_services:
                validation_result["warnings"].append(
                    f"Puerto {port} usado por múltiples servicios: "
                    f"{port_services[port]} y {config.service_name}"
                )
            port_services[port] = config.service_name
        
        # Validar endpoints unificados
        endpoint_paths = {}
        for endpoint in self.unified_endpoints:
            if endpoint.path in endpoint_paths:
                validation_result["errors"].append(
                    f"Path de endpoint duplicado: {endpoint.path}"
                )
            endpoint_paths[endpoint.path] = endpoint.name
            
            # Validar que los servicios target existen
            for service in endpoint.target_services:
                service_ports = self.get_service_ports(service)
                if not service_ports:
                    validation_result["warnings"].append(
                        f"Endpoint {endpoint.name} referencia servicio inexistente: {service}"
                    )
        
        # Validar configuraciones de entorno
        if self.environment == EnvironmentType.ENTERPRISE:
            scaling_config = self.get_auto_scaling_config()
            if scaling_config.max_replicas < 10:
                validation_result["warnings"].append(
                    "Configuración enterprise debería tener al menos 10 réplicas máximas"
                )
        
        # Resumen de validación
        validation_result["summary"] = {
            "total_ports": len(all_ports),
            "total_services": len(set(config.service_name for config in all_ports.values())),
            "total_endpoints": len(self.unified_endpoints),
            "security_levels": len(self.security_configs),
            "load_balancer_strategies": len(self.load_balancer_configs),
            "environment": self.environment.value
        }
        
        if validation_result["errors"]:
            validation_result["valid"] = False
        
        return validation_result

# === INSTANCIAS PREDEFINIDAS PARA DIFERENTES ENTORNOS ===

# Configuración para Desarrollo
dev_config = SilhouetteMCPConfig(EnvironmentType.DEVELOPMENT)

# Configuración para Staging
staging_config = SilhouetteMCPConfig(EnvironmentType.STAGING)

# Configuración para Producción
prod_config = SilhouetteMCPConfig(EnvironmentType.PRODUCTION)

# Configuración para Enterprise
enterprise_config = SilhouetteMCPConfig(EnvironmentType.ENTERPRISE)

# === FUNCIONES DE UTILIDAD ===

def get_config_for_environment(env: str) -> SilhouetteMCPConfig:
    """
    Obtiene configuración para un entorno específico
    
    Args:
        env: Nombre del entorno ('development', 'staging', 'production', 'enterprise')
    
    Returns:
        Instancia de SilhouetteMCPConfig configurada para el entorno
    """
    env_mapping = {
        "development": dev_config,
        "staging": staging_config,
        "production": prod_config,
        "enterprise": enterprise_config
    }
    return env_mapping.get(env.lower(), prod_config)

def get_port_ranges() -> Dict[str, tuple]:
    """
    Obtiene rangos de puertos definidos
    
    Returns:
        Diccionario con rangos de puertos
    """
    return {
        "original_systems": (8001, 8002),
        "enhanced_systems": (8007, 8024),
        "all_systems": (8001, 8024)
    }

def print_configuration_summary():
    """Imprime un resumen de la configuración"""
    config = get_config_for_environment(os.getenv("SILHOUETTE_ENV", "production"))
    ports = config.get_all_ports()
    
    print("=" * 80)
    print(f"SILHOUETTEMCP CONFIGURATION SUMMARY")
    print("=" * 80)
    print(f"Versión: {config.version}")
    print(f"Fecha de construcción: {config.build_date}")
    print(f"Entorno: {config.environment.value}")
    print(f"Total de puertos: {len(ports)}")
    print(f"Total de endpoints unificados: {len(config.unified_endpoints)}")
    print(f"Niveles de seguridad: {len(config.security_configs)}")
    print(f"Estrategias de balanceo: {len(config.load_balancer_configs)}")
    
    print("\n--- PUERTOS POR CATEGORÍA ---")
    original_ports = list(config.original_systems_ports.keys())
    enhanced_ports = list(config.enhanced_systems_ports.keys())
    
    print(f"Sistemas Originales: {min(original_ports)}-{max(original_ports)} ({len(original_ports)} puertos)")
    print(f"Sistemas Mejorados: {min(enhanced_ports)}-{max(enhanced_ports)} ({len(enhanced_ports)} puertos)")
    
    print("\n--- SERVICIOS POR TIPO ---")
    service_types = {}
    for port, config_obj in ports.items():
        service_type = config_obj.service_type
        if service_type not in service_types:
            service_types[service_type] = []
        service_types[service_type].append(config_obj.service_name)
    
    for service_type, services in service_types.items():
        print(f"{service_type.upper()}: {len(services)} servicios")
        for service in services[:3]:  # Mostrar solo los primeros 3
            print(f"  - {service}")
        if len(services) > 3:
            print(f"  ... y {len(services) - 3} más")
    
    print("\n--- ENDPOINTS POPULARES ---")
    endpoint_counts = {}
    for endpoint in config.unified_endpoints:
        for tag in endpoint.tags:
            endpoint_counts[tag] = endpoint_counts.get(tag, 0) + 1
    
    sorted_tags = sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)
    for tag, count in sorted_tags[:5]:
        print(f"{tag}: {count} endpoints")
    
    print("=" * 80)

if __name__ == "__main__":
    # Mostrar resumen al ejecutar el archivo directamente
    print_configuration_summary()