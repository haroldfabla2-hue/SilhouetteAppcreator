"""
Orquestador Enterprise Principal para MCP Core Superior
Integra todos los componentes enterprise: ESB, API Gateway, Rate Limiting, Circuit Breakers, Monitoring, Security y Compliance
"""

import asyncio
import time
import json
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor

# Importar componentes enterprise
from .enterprise_service_bus import EnterpriseServiceBus, ServiceEndpoint, MessagePriority
from .advanced_api_gateway import AdvancedAPIGateway, RouteRule, LoadBalancingStrategy
from .enterprise_resilience import AdvancedRateLimiter, ConnectionPool
from .circuit_breakers import RetryManager, CircuitBreakerConfig, RetryConfig, RetryStrategy
from .advanced_monitoring import (
    AdvancedMetrics, AlertManager, SecurityScanner, ComplianceManager, 
    StructuredLogger, MetricType, AlertSeverity
)

from ..core.config import settings


class ServiceStatus(Enum):
    """Estados de servicios enterprise"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


@dataclass
class EnterpriseServiceConfig:
    """Configuración de servicios enterprise"""
    service_name: str
    service_type: str
    version: str = "1.0.0"
    instances: int = 1
    cpu_limit: float = 1.0
    memory_limit_mb: int = 512
    dependencies: List[str] = field(default_factory=list)
    health_check_path: str = "/health"
    readiness_probe_path: str = "/ready"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FaultTolerancePolicy:
    """Política de tolerancia a fallos"""
    max_failures: int = 3
    failure_window: int = 60  # segundos
    recovery_time: int = 300  # segundos
    circuit_breaker_enabled: bool = True
    auto_restart: bool = True
    max_restart_attempts: int = 5
    escalation_policy: str = "notify_only"  # "notify_only", "auto_scale", "alert_team"


class EnterpriseOrchestrator:
    """Orquestador Enterprise Principal para 50+ servicios"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Componentes enterprise
        self.enterprise_esb: Optional[EnterpriseServiceBus] = None
        self.api_gateway: Optional[AdvancedAPIGateway] = None
        self.rate_limiter: Optional[AdvancedRateLimiter] = None
        self.connection_pool: Optional[ConnectionPool] = None
        self.retry_manager: Optional[RetryManager] = None
        self.monitoring_system: Optional[Dict[str, Any]] = None
        
        # Gestión de servicios
        self.services: Dict[str, EnterpriseServiceConfig] = {}
        self.service_status: Dict[str, ServiceStatus] = {}
        self.service_instances: Dict[str, List[Dict[str, Any]]] = {}
        
        # Fault tolerance
        self.fault_tolerance_policies: Dict[str, FaultTolerancePolicy] = {}
        self.failure_counters: Dict[str, List[datetime]] = {}
        self.auto_restart_counters: Dict[str, int] = {}
        
        # Métricas enterprise
        self.enterprise_metrics = {
            "services_managed": 0,
            "healthy_services": 0,
            "unhealthy_services": 0,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "uptime_percentage": 0.0,
            "fault_tolerance_activations": 0,
            "auto_restarts": 0
        }
        
        # Estado del orquestador
        self.is_running = False
        self.startup_time: Optional[datetime] = None
        self.executor = ThreadPoolExecutor(max_workers=20)
        
        # Tareas de background
        self.background_tasks: List[asyncio.Task] = []
    
    async def initialize(self) -> None:
        """Inicializar orquestador enterprise"""
        try:
            self.logger.info("Inicializando Enterprise Orchestrator...")
            
            # 1. Inicializar sistema de monitoreo primero
            await self._initialize_monitoring()
            
            # 2. Inicializar componentes de resilencia
            await self._initialize_resilience_components()
            
            # 3. Inicializar ESB y API Gateway
            await self._initialize_messaging_and_gateway()
            
            # 4. Registrar servicios por defecto
            await self._register_default_services()
            
            # 5. Configurar fault tolerance policies
            await self._setup_fault_tolerance()
            
            # 6. Iniciar tareas de background
            await self._start_background_tasks()
            
            self.startup_time = datetime.utcnow()
            self.is_running = True
            
            self.logger.info("Enterprise Orchestrator inicializado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando Enterprise Orchestrator: {e}")
            raise
    
    async def _initialize_monitoring(self) -> None:
        """Inicializar sistema de monitoreo enterprise"""
        self.logger.info("Inicializando sistema de monitoreo enterprise...")
        
        monitoring_config = self.config.get("monitoring", {})
        
        # Inicializar métricas avanzadas
        metrics = AdvancedMetrics(monitoring_config.get("metrics", {}))
        await metrics.initialize()
        
        # Inicializar alert manager
        alert_manager = AlertManager(monitoring_config.get("alerts", {}), metrics)
        await alert_manager.initialize()
        
        # Inicializar security scanner
        security_scanner = SecurityScanner(monitoring_config.get("security", {}))
        
        # Inicializar compliance manager
        compliance_manager = ComplianceManager(monitoring_config.get("compliance", {}))
        
        self.monitoring_system = {
            "metrics": metrics,
            "alerts": alert_manager,
            "security": security_scanner,
            "compliance": compliance_manager,
            "logger": StructuredLogger(monitoring_config.get("logging", {}))
        }
        
        self.logger.info("Sistema de monitoreo inicializado")
    
    async def _initialize_resilience_components(self) -> None:
        """Inicializar componentes de resilencia enterprise"""
        self.logger.info("Inicializando componentes de resilencia...")
        
        from .enterprise_resilience import initialize_enterprise_resilience
        
        await initialize_enterprise_resilience(self.config.get("resilience", {}))
        
        # Obtener instancias
        from .enterprise_resilience import get_rate_limiter, get_connection_pool
        from .circuit_breakers import initialize_enterprise_resilience_system, get_retry_manager
        
        self.rate_limiter = await get_rate_limiter()
        self.connection_pool = await get_connection_pool()
        self.retry_manager = await initialize_enterprise_resilience_system(self.config.get("circuit_breakers", {}))
        
        self.logger.info("Componentes de resilencia inicializados")
    
    async def _initialize_messaging_and_gateway(self) -> None:
        """Inicializar ESB y API Gateway"""
        self.logger.info("Inicializando ESB y API Gateway...")
        
        # Inicializar Enterprise Service Bus
        from .enterprise_service_bus import initialize_enterprise_esb
        self.enterprise_esb = await initialize_enterprise_esb(self.config.get("esb", {}))
        
        # Inicializar API Gateway
        from .advanced_api_gateway import initialize_api_gateway
        self.api_gateway = await initialize_api_gateway(self.config.get("gateway", {}))
        
        self.logger.info("ESB y API Gateway inicializados")
    
    async def _register_default_services(self) -> None:
        """Registrar servicios por defecto del sistema"""
        default_services = [
            EnterpriseServiceConfig(
                service_name="mcp_core_superior",
                service_type="orchestrator",
                version="1.0.0",
                instances=3,
                cpu_limit=2.0,
                memory_limit_mb=1024,
                health_check_path="/health",
                metadata={"description": "MCP Core Superior Main Orchestrator"}
            ),
            EnterpriseServiceConfig(
                service_name="reasoner_agent",
                service_type="agent",
                version="1.0.0",
                instances=2,
                cpu_limit=1.0,
                memory_limit_mb=512,
                health_check_path="/health",
                metadata={"description": "Reasoner Agent Service"}
            ),
            EnterpriseServiceConfig(
                service_name="planner_agent",
                service_type="agent",
                version="1.0.0",
                instances=2,
                cpu_limit=1.0,
                memory_limit_mb=512,
                health_check_path="/health",
                metadata={"description": "Planner Agent Service"}
            ),
            EnterpriseServiceConfig(
                service_name="executor_agent",
                service_type="agent",
                version="1.0.0",
                instances=5,
                cpu_limit=1.5,
                memory_limit_mb=768,
                health_check_path="/health",
                metadata={"description": "Executor Agent Service"}
            ),
            EnterpriseServiceConfig(
                service_name="verifier_agent",
                service_type="agent",
                version="1.0.0",
                instances=2,
                cpu_limit=1.0,
                memory_limit_mb=512,
                health_check_path="/health",
                metadata={"description": "Verifier Agent Service"}
            ),
            EnterpriseServiceConfig(
                service_name="database_service",
                service_type="database",
                version="1.0.0",
                instances=1,
                cpu_limit=2.0,
                memory_limit_mb=2048,
                health_check_path="/health",
                metadata={"description": "Database Service"}
            ),
            EnterpriseServiceConfig(
                service_name="cache_service",
                service_type="cache",
                version="1.0.0",
                instances=2,
                cpu_limit=1.0,
                memory_limit_mb=1024,
                health_check_path="/health",
                metadata={"description": "Redis Cache Service"}
            ),
            EnterpriseServiceConfig(
                service_name="vector_store_service",
                service_type="database",
                version="1.0.0",
                instances=2,
                cpu_limit=2.0,
                memory_limit_mb=1536,
                health_check_path="/health",
                metadata={"description": "Vector Store Service"}
            ),
            EnterpriseServiceConfig(
                service_name="streaming_service",
                service_type="streaming",
                version="1.0.0",
                instances=3,
                cpu_limit=1.0,
                memory_limit_mb=768,
                health_check_path="/health",
                metadata={"description": "Real-time Streaming Service"}
            ),
            EnterpriseServiceConfig(
                service_name="security_service",
                service_type="security",
                version="1.0.0",
                instances=2,
                cpu_limit=1.0,
                memory_limit_mb=512,
                health_check_path="/health",
                metadata={"description": "Security and Auth Service"}
            )
        ]
        
        for service in default_services:
            await self.register_service(service)
        
        self.logger.info(f"Registrados {len(default_services)} servicios por defecto")
    
    async def _setup_fault_tolerance(self) -> None:
        """Configurar políticas de tolerancia a fallos"""
        default_policies = [
            FaultTolerancePolicy(
                max_failures=3,
                failure_window=60,
                recovery_time=300,
                circuit_breaker_enabled=True,
                auto_restart=True,
                max_restart_attempts=5
            ),
            FaultTolerancePolicy(
                max_failures=2,
                failure_window=30,
                recovery_time=180,
                circuit_breaker_enabled=True,
                auto_restart=True,
                max_restart_attempts=3,
                escalation_policy="alert_team"
            )
        ]
        
        # Aplicar políticas por defecto a todos los servicios
        for service_name in self.services:
            self.fault_tolerance_policies[service_name] = default_policies[0]
        
        self.logger.info("Políticas de fault tolerance configuradas")
    
    async def _start_background_tasks(self) -> None:
        """Iniciar tareas de background del orquestador"""
        self.background_tasks.extend([
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._fault_tolerance_loop()),
            asyncio.create_task(self._metrics_collection_loop()),
            asyncio.create_task(self._service_discovery_loop()),
            asyncio.create_task(self._auto_scaling_loop())
        ])
        
        self.logger.info("Tareas de background iniciadas")
    
    async def register_service(self, service: EnterpriseServiceConfig) -> None:
        """Registrar un nuevo servicio enterprise"""
        try:
            # Agregar a registry
            self.services[service.service_name] = service
            self.service_status[service.service_name] = ServiceStatus.HEALTHY
            
            # Crear instancias
            instances = []
            for i in range(service.instances):
                instance = {
                    "instance_id": f"{service.service_name}-{i+1}",
                    "host": f"{service.service_name}-{i+1}",
                    "port": 8000 + i,
                    "status": "running",
                    "last_health_check": None,
                    "restart_count": 0,
                    "metadata": service.metadata
                }
                instances.append(instance)
            
            self.service_instances[service.service_name] = instances
            
            # Registrar en ESB
            for instance in instances:
                endpoint = ServiceEndpoint(
                    service_name=service.service_name,
                    service_type=service.service_type,
                    host=instance["host"],
                    port=instance["port"],
                    version=service.version,
                    capabilities=service.metadata.get("capabilities", []),
                    metadata=service.metadata
                )
                
                if self.enterprise_esb:
                    await self.enterprise_esb.register_service(endpoint)
            
            # Actualizar métricas
            self.enterprise_metrics["services_managed"] += 1
            self.enterprise_metrics["healthy_services"] += 1
            
            self.logger.info(f"Servicio registrado: {service.service_name} ({service.instances} instancias)")
            
        except Exception as e:
            self.logger.error(f"Error registrando servicio {service.service_name}: {e}")
            raise
    
    async def unregister_service(self, service_name: str) -> None:
        """Desregistrar un servicio"""
        try:
            if service_name in self.services:
                # Desregistrar del ESB
                if self.enterprise_esb:
                    await self.enterprise_esb.unregister_service(service_name)
                
                # Limpiar datos
                del self.services[service_name]
                del self.service_status[service_name]
                del self.service_instances[service_name]
                
                if service_name in self.fault_tolerance_policies:
                    del self.fault_tolerance_policies[service_name]
                
                # Actualizar métricas
                self.enterprise_metrics["services_managed"] -= 1
                
                self.logger.info(f"Servicio desregistrado: {service_name}")
                
        except Exception as e:
            self.logger.error(f"Error desregistrando servicio {service_name}: {e}")
            raise
    
    async def _health_check_loop(self) -> None:
        """Loop principal de health checks"""
        while self.is_running:
            try:
                await self._perform_comprehensive_health_checks()
                await asyncio.sleep(30)  # Health check cada 30 segundos
                
            except Exception as e:
                self.logger.error(f"Error en health check loop: {e}")
                await asyncio.sleep(30)
    
    async def _perform_comprehensive_health_checks(self) -> None:
        """Realizar health checks comprehensivos"""
        healthy_count = 0
        total_count = len(self.services)
        
        for service_name, service in self.services.items():
            try:
                instances = self.service_instances.get(service_name, [])
                healthy_instances = 0
                
                for instance in instances:
                    # Simular health check
                    is_healthy = await self._check_instance_health(instance, service)
                    instance["is_healthy"] = is_healthy
                    instance["last_health_check"] = datetime.utcnow()
                    
                    if is_healthy:
                        healthy_instances += 1
                
                # Determinar estado del servicio
                if healthy_instances == len(instances):
                    new_status = ServiceStatus.HEALTHY
                elif healthy_instances > 0:
                    new_status = ServiceStatus.DEGRADED
                else:
                    new_status = ServiceStatus.UNHEALTHY
                
                # Actualizar estado si cambió
                if self.service_status[service_name] != new_status:
                    old_status = self.service_status[service_name]
                    self.service_status[service_name] = new_status
                    
                    # Log del cambio de estado
                    self.logger.warning(f"Service {service_name} status changed: {old_status.value} -> {new_status.value}")
                    
                    # Actualizar métricas
                    if new_status == ServiceStatus.HEALTHY:
                        self.enterprise_metrics["healthy_services"] += 1
                        if old_status != ServiceStatus.HEALTHY:
                            self.enterprise_metrics["unhealthy_services"] -= 1
                    else:
                        if old_status == ServiceStatus.HEALTHY:
                            self.enterprise_metrics["healthy_services"] -= 1
                            self.enterprise_metrics["unhealthy_services"] += 1
                
                if new_status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]:
                    healthy_count += 1
                    
            except Exception as e:
                self.logger.error(f"Error checking health for service {service_name}: {e}")
                self.service_status[service_name] = ServiceStatus.UNHEALTHY
        
        # Actualizar métricas generales
        if total_count > 0:
            health_percentage = (healthy_count / total_count) * 100
            # Implementar promedio móvil para uptime
            current_uptime = self.enterprise_metrics.get("uptime_percentage", 95.0)
            self.enterprise_metrics["uptime_percentage"] = (current_uptime * 0.9) + (health_percentage * 0.1)
    
    async def _check_instance_health(self, instance: Dict[str, Any], service: EnterpriseServiceConfig) -> bool:
        """Verificar health de una instancia específica"""
        try:
            # Simular verificación de health
            # En implementación real, hacer HTTP request al health endpoint
            
            # Verificar uso de recursos
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            # Verificar límites
            if memory_mb > service.memory_limit_mb * 1.2:  # Allow 20% overhead
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking instance health: {e}")
            return False
    
    async def _fault_tolerance_loop(self) -> None:
        """Loop de tolerancia a fallos"""
        while self.is_running:
            try:
                await self._monitor_and_handle_failures()
                await asyncio.sleep(10)  # Monitoreo cada 10 segundos
                
            except Exception as e:
                self.logger.error(f"Error en fault tolerance loop: {e}")
                await asyncio.sleep(10)
    
    async def _monitor_and_handle_failures(self) -> None:
        """Monitorear y manejar fallos automáticamente"""
        current_time = datetime.utcnow()
        
        for service_name, policy in self.fault_tolerance_policies.items():
            try:
                service_status = self.service_status.get(service_name)
                
                # Solo manejar servicios no saludables
                if service_status in [ServiceStatus.UNHEALTHY, ServiceStatus.DEGRADED]:
                    await self._handle_service_failure(service_name, policy, current_time)
                
            except Exception as e:
                self.logger.error(f"Error handling failure for service {service_name}: {e}")
    
    async def _handle_service_failure(self, service_name: str, policy: FaultTolerancePolicy, current_time: datetime) -> None:
        """Manejar fallo de servicio"""
        # Agregar timestamp al contador de fallos
        if service_name not in self.failure_counters:
            self.failure_counters[service_name] = []
        
        self.failure_counters[service_name].append(current_time)
        
        # Limpiar fallos antiguos fuera de la ventana
        window_start = current_time - timedelta(seconds=policy.failure_window)
        self.failure_counters[service_name] = [
            failure_time for failure_time in self.failure_counters[service_name]
            if failure_time > window_start
        ]
        
        # Verificar si excedemos el límite de fallos
        recent_failures = len(self.failure_counters[service_name])
        
        if recent_failures >= policy.max_failures:
            self.logger.warning(f"Service {service_name} exceeded failure threshold: {recent_failures}/{policy.max_failures}")
            
            # Activar fault tolerance
            self.enterprise_metrics["fault_tolerance_activations"] += 1
            
            if policy.auto_restart:
                await self._attempt_auto_restart(service_name, policy)
            
            # Notificar según política de escalación
            if policy.escalation_policy == "alert_team":
                await self._send_alert(service_name, f"Service {service_name} requires manual intervention")
    
    async def _attempt_auto_restart(self, service_name: str, policy: FaultTolerancePolicy) -> None:
        """Intentar reinicio automático"""
        current_restarts = self.auto_restart_counters.get(service_name, 0)
        
        if current_restarts < policy.max_restart_attempts:
            self.logger.info(f"Attempting auto-restart for service {service_name} (attempt {current_restarts + 1}/{policy.max_restart_attempts})")
            
            # Simular reinicio de servicio
            await self._restart_service_instances(service_name)
            
            # Actualizar contadores
            self.auto_restart_counters[service_name] = current_restarts + 1
            self.enterprise_metrics["auto_restarts"] += 1
            
        else:
            self.logger.error(f"Max restart attempts reached for service {service_name}")
            await self._escalate_incident(service_name, "Max restart attempts exceeded")
    
    async def _restart_service_instances(self, service_name: str) -> None:
        """Reiniciar instancias de un servicio"""
        instances = self.service_instances.get(service_name, [])
        
        for instance in instances:
            try:
                instance["status"] = "restarting"
                instance["restart_count"] += 1
                
                # Simular proceso de reinicio
                await asyncio.sleep(2)
                
                instance["status"] = "running"
                self.logger.info(f"Instance {instance['instance_id']} restarted successfully")
                
            except Exception as e:
                self.logger.error(f"Failed to restart instance {instance['instance_id']}: {e}")
                instance["status"] = "failed"
    
    async def _send_alert(self, service_name: str, message: str) -> None:
        """Enviar alerta"""
        if self.monitoring_system:
            alert_manager = self.monitoring_system["alerts"]
            # Crear alerta directamente
            self.logger.critical(f"ALERT: {service_name} - {message}")
    
    async def _escalate_incident(self, service_name: str, reason: str) -> None:
        """Escalar incidente"""
        self.logger.critical(f"INCIDENT ESCALATION: Service {service_name} - {reason}")
        
        # En implementación real, enviar a sistema de incidentes
        # ej. PagerDuty, OpsGenie, etc.
    
    async def _metrics_collection_loop(self) -> None:
        """Loop de recolección de métricas enterprise"""
        while self.is_running:
            try:
                await self._collect_enterprise_metrics()
                await asyncio.sleep(60)  # Recolectar cada minuto
                
            except Exception as e:
                self.logger.error(f"Error en metrics collection loop: {e}")
                await asyncio.sleep(60)
    
    async def _collect_enterprise_metrics(self) -> None:
        """Recolectar métricas enterprise"""
        if not self.monitoring_system:
            return
        
        metrics = self.monitoring_system["metrics"]
        
        # Métricas de servicios
        metrics.record_gauge("enterprise.services.total", len(self.services))
        metrics.record_gauge("enterprise.services.healthy", 
                           sum(1 for status in self.service_status.values() if status == ServiceStatus.HEALTHY))
        metrics.record_gauge("enterprise.services.unhealthy",
                           sum(1 for status in self.service_status.values() if status == ServiceStatus.UNHEALTHY))
        
        # Métricas de fault tolerance
        metrics.record_counter("enterprise.fault_tolerance.activations", 
                             self.enterprise_metrics["fault_tolerance_activations"])
        metrics.record_counter("enterprise.fault_tolerance.auto_restarts",
                             self.enterprise_metrics["auto_restarts"])
        
        # Métricas de uptime
        if self.startup_time:
            uptime_seconds = (datetime.utcnow() - self.startup_time).total_seconds()
            metrics.record_gauge("enterprise.uptime.seconds", uptime_seconds)
        
        # Métricas del sistema
        metrics.record_gauge("enterprise.metrics.collection_interval", 60)
    
    async def _service_discovery_loop(self) -> None:
        """Loop de service discovery y auto-registration"""
        while self.is_running:
            try:
                await self._update_service_registry()
                await asyncio.sleep(120)  # Actualizar cada 2 minutos
                
            except Exception as e:
                self.logger.error(f"Error en service discovery loop: {e}")
                await asyncio.sleep(120)
    
    async def _update_service_registry(self) -> None:
        """Actualizar registro de servicios en ESB"""
        if not self.enterprise_esb:
            return
        
        for service_name, service in self.services.items():
            instances = self.service_instances.get(service_name, [])
            
            for instance in instances:
                if instance.get("is_healthy", True):
                    endpoint = ServiceEndpoint(
                        service_name=service.service_name,
                        service_type=service.service_type,
                        host=instance["host"],
                        port=instance["port"],
                        version=service.version,
                        load_weight=100 if instance["status"] == "running" else 0,
                        metadata=service.metadata
                    )
                    
                    await self.enterprise_esb.register_service(endpoint)
    
    async def _auto_scaling_loop(self) -> None:
        """Loop de auto-scaling basado en métricas"""
        while self.is_running:
            try:
                await self._evaluate_scaling_needs()
                await asyncio.sleep(300)  # Evaluar cada 5 minutos
                
            except Exception as e:
                self.logger.error(f"Error en auto-scaling loop: {e}")
                await asyncio.sleep(300)
    
    async def _evaluate_scaling_needs(self) -> None:
        """Evaluar necesidades de auto-scaling"""
        # Implementar lógica de auto-scaling basada en métricas
        # ej. CPU usage, memory usage, request rate, etc.
        
        for service_name, service in self.services.items():
            instances = self.service_instances.get(service_name, [])
            
            # Evaluación simplificada - en implementación real usar métricas reales
            current_load = len(instances)  # Placeholder
            
            if current_load < service.instances * 0.3:  # Si uso < 30%
                # Posible scale down
                pass
            elif current_load > service.instances * 0.8:  # Si uso > 80%
                # Posible scale up
                pass
    
    def get_enterprise_dashboard(self) -> Dict[str, Any]:
        """Obtener dashboard enterprise completo"""
        return {
            "orchestrator_status": "running" if self.is_running else "stopped",
            "uptime": (datetime.utcnow() - self.startup_time).total_seconds() if self.startup_time else 0,
            "services": {
                "total": len(self.services),
                "healthy": sum(1 for status in self.service_status.values() if status == ServiceStatus.HEALTHY),
                "degraded": sum(1 for status in self.service_status.values() if status == ServiceStatus.DEGRADED),
                "unhealthy": sum(1 for status in self.service_status.values() if status == ServiceStatus.UNHEALTHY),
                "by_type": {
                    service_type: sum(1 for service in self.services.values() if service.service_type == service_type)
                    for service_type in set(service.service_type for service in self.services.values())
                }
            },
            "fault_tolerance": {
                "policies_active": len(self.fault_tolerance_policies),
                "recent_failures": sum(len(counter) for counter in self.failure_counters.values()),
                "auto_restarts_total": sum(self.auto_restart_counters.values())
            },
            "enterprise_metrics": self.enterprise_metrics,
            "component_status": {
                "enterprise_esb": self.enterprise_esb is not None,
                "api_gateway": self.api_gateway is not None,
                "rate_limiter": self.rate_limiter is not None,
                "connection_pool": self.connection_pool is not None,
                "retry_manager": self.retry_manager is not None,
                "monitoring_system": self.monitoring_system is not None
            }
        }
    
    async def shutdown(self) -> None:
        """Shutdown graceful del orquestador"""
        self.logger.info("Iniciando shutdown del Enterprise Orchestrator...")
        
        self.is_running = False
        
        # Cancelar tareas de background
        for task in self.background_tasks:
            task.cancel()
        
        # Cerrar componentes
        if self.enterprise_esb:
            await self.enterprise_esb.cleanup()
        
        if self.monitoring_system:
            metrics = self.monitoring_system["metrics"]
            await metrics.stop_collection()
            
            alerts = self.monitoring_system["alerts"]
            await alerts.stop_evaluation()
        
        if self.connection_pool:
            await self.connection_pool.cleanup_pools()
        
        # Esperar tareas
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        self.executor.shutdown(wait=True)
        
        self.logger.info("Enterprise Orchestrator shutdown completado")


# Instancia global del orquestador
enterprise_orchestrator: Optional[EnterpriseOrchestrator] = None


async def initialize_enterprise_orchestrator(config: Dict[str, Any]) -> EnterpriseOrchestrator:
    """Inicializar orquestador enterprise completo"""
    global enterprise_orchestrator
    
    enterprise_orchestrator = EnterpriseOrchestrator(config)
    await enterprise_orchestrator.initialize()
    
    return enterprise_orchestrator


async def get_enterprise_orchestrator() -> EnterpriseOrchestrator:
    """Obtener instancia del orquestador enterprise"""
    if not enterprise_orchestrator:
        raise RuntimeError("Enterprise Orchestrator no inicializado")
    return enterprise_orchestrator