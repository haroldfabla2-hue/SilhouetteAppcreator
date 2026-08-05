#!/usr/bin/env python3
"""
Sistema de Orquestación de Integración SilhouetteMCP
====================================================

Sistema completo de orquestación que conecta todos los sistemas mejorados (8010-8024)
con los originales (8001-8002). Incluye comunicación bidireccional WebSocket y HTTP,
configuración automática de seguridad, coordinación de auto-healing y load balancing,
integración de auto-scaling, endpoints unificados, y monitoreo centralizado.

Autor: Sistema SilhouetteMCP
Fecha: 2025-11-06
Versión: 1.0.0
"""

import asyncio
import json
import logging
import time
import uuid
import weakref
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Tuple, Union
import hashlib
import threading
import queue
import signal
import sys
import socket
import ssl
import gzip
import pickle
import base64
import websockets
import requests
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import psutil
import numpy as np
from contextlib import asynccontextmanager

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/code/orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Enums y Constantes
class ServiceStatus(Enum):
    """Estados de los servicios"""
    UNKNOWN = "unknown"
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    FAILED = "failed"
    STOPPING = "stopping"
    STOPPED = "stopped"
    SCALING_UP = "scaling_up"
    SCALING_DOWN = "scaling_down"
    MAINTENANCE = "maintenance"

class LoadBalanceStrategy(Enum):
    """Estrategias de balanceador de carga"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    IP_HASH = "ip_hash"
    FASTEST_RESPONSE = "fastest_response"
    CPU_BASED = "cpu_based"

class HealthStatus(Enum):
    """Estados de salud del sistema"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

# Dataclasses
@dataclass
class ServiceConfig:
    """Configuración de servicio"""
    service_id: str
    host: str
    port: int
    protocol: str  # http, https, ws, wss
    weight: int = 1
    max_connections: int = 1000
    timeout: float = 30.0
    health_check_url: Optional[str] = None
    retry_count: int = 3
    retry_delay: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ServiceInstance:
    """Instancia de servicio"""
    config: ServiceConfig
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_health_check: Optional[datetime] = None
    response_time: float = 0.0
    connection_count: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    error_count: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        self.instance_id = f"{self.config.service_id}_{uuid.uuid4().hex[:8]}"

@dataclass
class HealthCheck:
    """Resultado de verificación de salud"""
    service_id: str
    instance_id: str
    status: HealthStatus
    response_time: float
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AlertRule:
    """Regla de alerta"""
    rule_id: str
    name: str
    condition: str  # métrica > umbral
    threshold: float
    duration: int = 60  # segundos
    severity: str = "warning"
    enabled: bool = True
    actions: List[str] = field(default_factory=list)

@dataclass
class SystemMetrics:
    """Métricas del sistema"""
    timestamp: datetime
    total_services: int
    healthy_services: int
    total_instances: int
    healthy_instances: int
    total_requests_per_second: float
    average_response_time: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    active_websocket_connections: int
    request_queue_size: int = 0

# Interfaces
class ServiceRegistry(ABC):
    """Registro de servicios"""
    
    @abstractmethod
    async def register_service(self, service: ServiceInstance) -> bool:
        """Registrar servicio"""
        pass
    
    @abstractmethod
    async def unregister_service(self, service_id: str) -> bool:
        """Desregistrar servicio"""
        pass
    
    @abstractmethod
    async def get_services(self, service_id: Optional[str] = None) -> List[ServiceInstance]:
        """Obtener servicios"""
        pass
    
    @abstractmethod
    async def get_healthy_services(self) -> List[ServiceInstance]:
        """Obtener servicios saludables"""
        pass

class LoadBalancer(ABC):
    """Balanceador de carga"""
    
    @abstractmethod
    async def select_service(self, service_id: str, strategy: LoadBalanceStrategy) -> Optional[ServiceInstance]:
        """Seleccionar servicio"""
        pass
    
    @abstractmethod
    async def update_service_stats(self, instance_id: str, stats: Dict[str, Any]) -> None:
        """Actualizar estadísticas del servicio"""
        pass

class HealthMonitor(ABC):
    """Monitor de salud"""
    
    @abstractmethod
    async def start_monitoring(self) -> None:
        """Iniciar monitoreo"""
        pass
    
    @abstractmethod
    async def stop_monitoring(self) -> None:
        """Detener monitoreo"""
        pass
    
    @abstractmethod
    async def check_service_health(self, service: ServiceInstance) -> HealthCheck:
        """Verificar salud del servicio"""
        pass

class AutoScaler(ABC):
    """Escalador automático"""
    
    @abstractmethod
    async def evaluate_scaling(self) -> List[str]:
        """Evaluar necesidades de escalado"""
        pass
    
    @abstractmethod
    async def scale_up(self, service_id: str, instances: int = 1) -> bool:
        """Escalar hacia arriba"""
        pass
    
    @abstractmethod
    async def scale_down(self, service_id: str, instances: int = 1) -> bool:
        """Escalar hacia abajo"""
        pass

class SecurityManager(ABC):
    """Gestor de seguridad"""
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[str]:
        """Autenticar"""
        pass
    
    @abstractmethod
    async def authorize(self, token: str, resource: str, action: str) -> bool:
        """Autorizar"""
        pass
    
    @abstractmethod
    async def generate_token(self, user_id: str, permissions: List[str]) -> str:
        """Generar token"""
        pass

# Implementaciones
class InMemoryServiceRegistry(ServiceRegistry):
    """Registro de servicios en memoria"""
    
    def __init__(self):
        self._services: Dict[str, ServiceInstance] = {}
        self._lock = asyncio.Lock()
    
    async def register_service(self, service: ServiceInstance) -> bool:
        """Registrar servicio"""
        async with self._lock:
            self._services[service.instance_id] = service
            logger.info(f"Servicio registrado: {service.instance_id}")
            return True
    
    async def unregister_service(self, service_id: str) -> bool:
        """Desregistrar servicio"""
        async with self._lock:
            removed = False
            for instance_id, service in list(self._services.items()):
                if service.config.service_id == service_id:
                    del self._services[instance_id]
                    removed = True
                    logger.info(f"Servicio desregistrado: {instance_id}")
            return removed
    
    async def get_services(self, service_id: Optional[str] = None) -> List[ServiceInstance]:
        """Obtener servicios"""
        async with self._lock:
            if service_id:
                return [s for s in self._services.values() if s.config.service_id == service_id]
            return list(self._services.values())
    
    async def get_healthy_services(self) -> List[ServiceInstance]:
        """Obtener servicios saludables"""
        async with self._lock:
            return [s for s in self._services.values() if s.status == ServiceStatus.RUNNING]

class LoadBalancerImpl(LoadBalancer):
    """Implementación del balanceador de carga"""
    
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self._strategy_counters = defaultdict(int)
        self._connection_stats = defaultdict(int)
        self._response_times = defaultdict(deque)
    
    async def select_service(self, service_id: str, strategy: LoadBalanceStrategy) -> Optional[ServiceInstance]:
        """Seleccionar servicio según estrategia"""
        healthy_services = await self.registry.get_healthy_services()
        target_services = [s for s in healthy_services if s.config.service_id == service_id]
        
        if not target_services:
            return None
        
        if strategy == LoadBalanceStrategy.ROUND_ROBIN:
            return self._round_robin(target_services)
        elif strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
            return self._least_connections(target_services)
        elif strategy == LoadBalanceStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin(target_services)
        elif strategy == LoadBalanceStrategy.IP_HASH:
            return self._ip_hash(target_services)
        elif strategy == LoadBalanceStrategy.FASTEST_RESPONSE:
            return self._fastest_response(target_services)
        elif strategy == LoadBalanceStrategy.CPU_BASED:
            return self._cpu_based(target_services)
        else:
            return target_services[0]  # fallback
    
    def _round_robin(self, services: List[ServiceInstance]) -> ServiceInstance:
        """Round Robin"""
        counter_key = f"rr_{services[0].config.service_id}"
        self._strategy_counters[counter_key] += 1
        index = self._strategy_counters[counter_key] % len(services)
        return services[index]
    
    def _least_connections(self, services: List[ServiceInstance]) -> ServiceInstance:
        """Menor número de conexiones"""
        return min(services, key=lambda s: s.connection_count)
    
    def _weighted_round_robin(self, services: List[ServiceInstance]) -> ServiceInstance:
        """Weighted Round Robin"""
        # Implementación simplificada basada en pesos
        total_weight = sum(s.config.weight for s in services)
        if total_weight == 0:
            return services[0]
        
        # Seleccionar basado en peso relativo
        target = sum(s.config.weight for s in services) * np.random.random()
        current_weight = 0
        for service in services:
            current_weight += service.config.weight
            if current_weight >= target:
                return service
        
        return services[0]
    
    def _ip_hash(self, services: List[ServiceInstance]) -> ServiceInstance:
        """IP Hash"""
        client_ip = hash(str(uuid.uuid4()))  # Simular IP del cliente
        hash_value = client_ip % len(services)
        return services[hash_value]
    
    def _fastest_response(self, services: List[ServiceInstance]) -> ServiceInstance:
        """Tiempo de respuesta más rápido"""
        return min(services, key=lambda s: s.response_time)
    
    def _cpu_based(self, services: List[ServiceInstance]) -> ServiceInstance:
        """Menor uso de CPU"""
        return min(services, key=lambda s: s.cpu_usage)
    
    async def update_service_stats(self, instance_id: str, stats: Dict[str, Any]) -> None:
        """Actualizar estadísticas del servicio"""
        services = await self.registry.get_services()
        for service in services:
            if service.instance_id == instance_id:
                if 'connection_count' in stats:
                    service.connection_count = stats['connection_count']
                if 'response_time' in stats:
                    service.response_time = stats['response_time']
                if 'cpu_usage' in stats:
                    service.cpu_usage = stats['cpu_usage']
                if 'memory_usage' in stats:
                    service.memory_usage = stats['memory_usage']

class HealthMonitorImpl(HealthMonitor):
    """Monitor de salud"""
    
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self.is_monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._health_checks: Dict[str, HealthCheck] = {}
        self._check_interval = 30  # segundos
    
    async def start_monitoring(self) -> None:
        """Iniciar monitoreo de salud"""
        self.is_monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Monitoreo de salud iniciado")
    
    async def stop_monitoring(self) -> None:
        """Detener monitoreo de salud"""
        self.is_monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Monitoreo de salud detenido")
    
    async def _monitor_loop(self):
        """Loop principal de monitoreo"""
        while self.is_monitoring:
            try:
                services = await self.registry.get_services()
                tasks = [self.check_service_health(service) for service in services]
                await asyncio.gather(*tasks, return_exceptions=True)
                
                await asyncio.sleep(self._check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en loop de monitoreo: {e}")
                await asyncio.sleep(self._check_interval)
    
    async def check_service_health(self, service: ServiceInstance) -> HealthCheck:
        """Verificar salud del servicio"""
        start_time = time.time()
        status = HealthStatus.CRITICAL
        details = {}
        
        try:
            if service.config.health_check_url:
                # Realizar health check real
                async with asyncio.timeout(service.config.timeout):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            service.config.health_check_url,
                            headers={'User-Agent': 'SilhouetteMCP-HealthCheck/1.0'}
                        ) as response:
                            response_time = time.time() - start_time
                            
                            if response.status == 200:
                                status = HealthStatus.HEALTHY
                            else:
                                status = HealthStatus.CRITICAL
                                details['status_code'] = response.status
                            
                            details['response_time'] = response_time
            else:
                # Health check básico basado en estado del proceso
                if service.status == ServiceStatus.RUNNING:
                    status = HealthStatus.HEALTHY
                elif service.status == ServiceStatus.DEGRADED:
                    status = HealthStatus.WARNING
                else:
                    status = HealthStatus.CRITICAL
                
                response_time = time.time() - start_time
                details['response_time'] = response_time
            
            # Actualizar estado del servicio
            service.status = ServiceStatus.RUNNING if status == HealthStatus.HEALTHY else \
                           ServiceStatus.DEGRADED if status == HealthStatus.WARNING else \
                           ServiceStatus.FAILED
            service.last_health_check = datetime.now()
            
            health_check = HealthCheck(
                service_id=service.config.service_id,
                instance_id=service.instance_id,
                status=status,
                response_time=response_time,
                timestamp=datetime.now(),
                details=details
            )
            
            self._health_checks[service.instance_id] = health_check
            return health_check
            
        except Exception as e:
            response_time = time.time() - start_time
            service.status = ServiceStatus.FAILED
            service.last_health_check = datetime.now()
            
            health_check = HealthCheck(
                service_id=service.config.service_id,
                instance_id=service.instance_id,
                status=HealthStatus.CRITICAL,
                response_time=response_time,
                timestamp=datetime.now(),
                details={'error': str(e)}
            )
            
            self._health_checks[service.instance_id] = health_check
            return health_check

class AutoScalerImpl(AutoScaler):
    """Escalador automático"""
    
    def __init__(self, registry: ServiceRegistry, monitor: HealthMonitor):
        self.registry = registry
        self.monitor = monitor
        self.scaling_rules = {}
        self.min_instances = 1
        self.max_instances = 10
    
    async def evaluate_scaling(self) -> List[str]:
        """Evaluar necesidades de escalado"""
        scaling_actions = []
        
        try:
            services = await self.registry.get_services()
            service_groups = defaultdict(list)
            
            # Agrupar servicios por ID
            for service in services:
                service_groups[service.config.service_id].append(service)
            
            for service_id, instances in service_groups.items():
                if service_id not in self.scaling_rules:
                    continue
                
                rule = self.scaling_rules[service_id]
                metrics = await self._calculate_service_metrics(instances)
                
                # Evaluar escalado hacia arriba
                if metrics['avg_response_time'] > rule.get('response_time_threshold', 1.0) or \
                   metrics['avg_cpu_usage'] > rule.get('cpu_threshold', 80.0) or \
                   metrics['total_requests_per_second'] > rule.get('rps_threshold', 100.0):
                    
                    if len(instances) < self.max_instances:
                        scaling_action = await self.scale_up(service_id)
                        if scaling_action:
                            scaling_actions.append(f"scaled_up_{service_id}")
                
                # Evaluar escalado hacia abajo
                elif metrics['avg_response_time'] < rule.get('response_time_threshold', 0.5) and \
                     metrics['avg_cpu_usage'] < rule.get('cpu_threshold', 30.0) and \
                     metrics['total_requests_per_second'] < rule.get('rps_threshold', 20.0):
                    
                    if len(instances) > self.min_instances:
                        scaling_action = await self.scale_down(service_id)
                        if scaling_action:
                            scaling_actions.append(f"scaled_down_{service_id}")
            
            return scaling_actions
            
        except Exception as e:
            logger.error(f"Error evaluando escalado: {e}")
            return []
    
    async def _calculate_service_metrics(self, instances: List[ServiceInstance]) -> Dict[str, float]:
        """Calcular métricas de los servicios"""
        if not instances:
            return {
                'avg_response_time': 0.0,
                'avg_cpu_usage': 0.0,
                'total_requests_per_second': 0.0
            }
        
        return {
            'avg_response_time': np.mean([i.response_time for i in instances if i.response_time > 0]),
            'avg_cpu_usage': np.mean([i.cpu_usage for i in instances if i.cpu_usage > 0]),
            'total_requests_per_second': sum([i.total_requests for i in instances])
        }
    
    async def scale_up(self, service_id: str, instances: int = 1) -> bool:
        """Escalar hacia arriba"""
        try:
            logger.info(f"Escalando servicio {service_id} hacia arriba con {instances} instancias")
            
            # Simular escalado - en producción esto iniciaría nuevas instancias
            services = await self.registry.get_services(service_id)
            if services:
                first_service = services[0]
                for i in range(instances):
                    new_instance = ServiceInstance(
                        config=ServiceConfig(
                            service_id=service_id,
                            host=first_service.config.host,
                            port=first_service.config.port,
                            protocol=first_service.config.protocol,
                            weight=first_service.config.weight
                        )
                    )
                    new_instance.status = ServiceStatus.SCALING_UP
                    await self.registry.register_service(new_instance)
                
                # Simular que las instancias están listas después de un tiempo
                await asyncio.sleep(2)
                for service in services + await self.registry.get_services(service_id):
                    if service.status == ServiceStatus.SCALING_UP:
                        service.status = ServiceStatus.RUNNING
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error escalando hacia arriba: {e}")
            return False
    
    async def scale_down(self, service_id: str, instances: int = 1) -> bool:
        """Escalar hacia abajo"""
        try:
            logger.info(f"Escalando servicio {service_id} hacia abajo con {instances} instancias")
            
            services = await self.registry.get_services(service_id)
            instances_to_remove = [s for s in services if s.status in [ServiceStatus.RUNNING, ServiceStatus.DEGRADED]]
            
            # Seleccionar las instancias con menor carga para eliminar
            instances_to_remove.sort(key=lambda s: (s.connection_count, s.total_requests))
            instances_to_remove = instances_to_remove[:instances]
            
            for instance in instances_to_remove:
                instance.status = ServiceStatus.SCALING_DOWN
                await asyncio.sleep(1)  # Dar tiempo para cerrar conexiones
                # En producción, esto terminaría el proceso real
                logger.info(f"Instancia {instance.instance_id} eliminada")
            
            return True
            
        except Exception as e:
            logger.error(f"Error escalando hacia abajo: {e}")
            return False
    
    def set_scaling_rule(self, service_id: str, rule: Dict[str, Any]) -> None:
        """Establecer regla de escalado"""
        self.scaling_rules[service_id] = rule

class SecurityManagerImpl(SecurityManager):
    """Gestor de seguridad"""
    
    def __init__(self, secret_key: str = "silhouettemcp_secret_key_2025"):
        self.secret_key = secret_key
        self.users = {}
        self.permissions = defaultdict(list)
        self.active_tokens = {}
        self.token_expiry = 3600  # 1 hora
    
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[str]:
        """Autenticar usuario"""
        try:
            username = credentials.get('username')
            password = credentials.get('password')
            
            if username in self.users and self.users[username] == password:
                permissions = self.permissions.get(username, [])
                token = await self.generate_token(username, permissions)
                self.active_tokens[token] = {
                    'username': username,
                    'issued_at': datetime.now(),
                    'expires_at': datetime.now() + timedelta(seconds=self.token_expiry)
                }
                return token
            
            return None
            
        except Exception as e:
            logger.error(f"Error en autenticación: {e}")
            return None
    
    async def authorize(self, token: str, resource: str, action: str) -> bool:
        """Verificar autorización"""
        try:
            if token not in self.active_tokens:
                return False
            
            token_info = self.active_tokens[token]
            if datetime.now() > token_info['expires_at']:
                del self.active_tokens[token]
                return False
            
            username = token_info['username']
            user_permissions = self.permissions.get(username, [])
            
            # Verificar si tiene permiso para la acción
            return f"{resource}:{action}" in user_permissions or "admin" in user_permissions
            
        except Exception as e:
            logger.error(f"Error en autorización: {e}")
            return False
    
    async def generate_token(self, user_id: str, permissions: List[str]) -> str:
        """Generar token JWT"""
        payload = {
            'user_id': user_id,
            'permissions': permissions,
            'iat': datetime.now().timestamp(),
            'exp': (datetime.now() + timedelta(seconds=self.token_expiry)).timestamp()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def add_user(self, username: str, password: str, permissions: List[str]) -> None:
        """Agregar usuario"""
        self.users[username] = password
        self.permissions[username] = permissions

class MonitoringSystem:
    """Sistema de monitoreo centralizado"""
    
    def __init__(self):
        self.metrics_history = deque(maxlen=1000)
        self.alert_rules = {}
        self.active_alerts = {}
        self.alert_callbacks = []
    
    def add_alert_rule(self, rule: AlertRule) -> None:
        """Agregar regla de alerta"""
        self.alert_rules[rule.rule_id] = rule
    
    def evaluate_alerts(self, metrics: SystemMetrics) -> List[str]:
        """Evaluar alertas basadas en métricas"""
        triggered_alerts = []
        
        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue
            
            try:
                # Evaluar condición
                if self._evaluate_condition(rule.condition, metrics):
                    alert_key = f"{rule.rule_id}_{int(time.time() // rule.duration)}"
                    
                    if alert_key not in self.active_alerts:
                        self.active_alerts[alert_key] = {
                            'rule': rule,
                            'triggered_at': datetime.now(),
                            'metrics': metrics
                        }
                        triggered_alerts.append(rule.rule_id)
                        self._trigger_alert(rule, metrics)
            except Exception as e:
                logger.error(f"Error evaluando regla {rule.rule_id}: {e}")
        
        return triggered_alerts
    
    def _evaluate_condition(self, condition: str, metrics: SystemMetrics) -> bool:
        """Evaluar condición de alerta"""
        try:
            # Implementar parser simple de condiciones
            if 'cpu_usage' in condition:
                threshold = float(condition.split('>')[1].strip())
                return metrics.cpu_usage > threshold
            elif 'memory_usage' in condition:
                threshold = float(condition.split('>')[1].strip())
                return metrics.memory_usage > threshold
            elif 'response_time' in condition:
                threshold = float(condition.split('>')[1].strip())
                return metrics.average_response_time > threshold
            elif 'healthy_services' in condition:
                threshold = int(condition.split('<')[1].strip())
                return metrics.healthy_services < threshold
            
            return False
        except Exception as e:
            logger.error(f"Error evaluando condición: {e}")
            return False
    
    def _trigger_alert(self, rule: AlertRule, metrics: SystemMetrics) -> None:
        """Disparar alerta"""
        alert_data = {
            'rule_id': rule.rule_id,
            'rule_name': rule.name,
            'severity': rule.severity,
            'timestamp': datetime.now(),
            'metrics': metrics,
            'details': f"Condición {rule.condition} activada"
        }
        
        logger.warning(f"ALERTA: {rule.name} - {alert_data['details']}")
        
        # Ejecutar acciones
        for action in rule.actions:
            self._execute_action(action, alert_data)
        
        # Ejecutar callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                logger.error(f"Error en callback de alerta: {e}")
    
    def _execute_action(self, action: str, alert_data: Dict[str, Any]) -> None:
        """Ejecutar acción de alerta"""
        if action == "log":
            logger.warning(f"Alerta activada: {alert_data['rule_name']}")
        elif action == "email" and "admin@silhouettemcp.com" in alert_data.get('details', ''):
            # Simular envío de email
            logger.info(f"Email de alerta enviado: {alert_data['rule_name']}")
        # Agregar más acciones según sea necesario
    
    def add_alert_callback(self, callback: Callable) -> None:
        """Agregar callback de alerta"""
        self.alert_callbacks.append(callback)
    
    async def collect_system_metrics(self, registry: ServiceRegistry) -> SystemMetrics:
        """Recopilar métricas del sistema"""
        try:
            services = await registry.get_services()
            healthy_services = await registry.get_healthy_services()
            
            # Métricas del sistema
            cpu_usage = psutil.cpu_percent()
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
            network_io = psutil.net_io_counters()
            
            # Métricas de servicios
            total_requests_per_second = sum(s.total_requests for s in services) / 60  # por minuto
            average_response_time = np.mean([s.response_time for s in services if s.response_time > 0]) if services else 0.0
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                total_services=len(set(s.config.service_id for s in services)),
                healthy_services=len(set(s.config.service_id for s in healthy_services)),
                total_instances=len(services),
                healthy_instances=len(healthy_services),
                total_requests_per_second=total_requests_per_second,
                average_response_time=average_response_time,
                cpu_usage=cpu_usage,
                memory_usage=memory_info.percent,
                disk_usage=disk_info.percent,
                network_io={
                    'bytes_sent': network_io.bytes_sent,
                    'bytes_recv': network_io.bytes_recv,
                    'packets_sent': network_io.packets_sent,
                    'packets_recv': network_io.packets_recv
                },
                active_websocket_connections=0  # Se actualizará dinámicamente
            )
            
            self.metrics_history.append(metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"Error recopilando métricas: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                total_services=0,
                healthy_services=0,
                total_instances=0,
                healthy_instances=0,
                total_requests_per_second=0.0,
                average_response_time=0.0,
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                network_io={}
            )

# WebSocket Manager
class WebSocketManager:
    """Gestor de conexiones WebSocket"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_stats = defaultdict(int)
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Aceptar conexión WebSocket"""
        await websocket.accept()
        async with self._lock:
            self.active_connections[client_id] = websocket
            self.connection_stats[client_id] += 1
        logger.info(f"WebSocket conectado: {client_id}")
    
    async def disconnect(self, client_id: str) -> None:
        """Desconectar WebSocket"""
        async with self._lock:
            if client_id in self.active_connections:
                del self.active_connections[client_id]
                logger.info(f"WebSocket desconectado: {client_id}")
    
    async def send_personal_message(self, message: str, client_id: str) -> None:
        """Enviar mensaje a cliente específico"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
            except Exception as e:
                logger.error(f"Error enviando mensaje a {client_id}: {e}")
                await self.disconnect(client_id)
    
    async def broadcast(self, message: str) -> None:
        """Enviar mensaje a todos los clientes"""
        disconnected = []
        
        async with self._lock:
            clients = list(self.active_connections.keys())
        
        for client_id in clients:
            try:
                await self.active_connections[client_id].send_text(message)
            except Exception as e:
                logger.error(f"Error enviando broadcast a {client_id}: {e}")
                disconnected.append(client_id)
        
        # Limpiar conexiones desconectadas
        for client_id in disconnected:
            await self.disconnect(client_id)
    
    def get_connection_count(self) -> int:
        """Obtener número de conexiones activas"""
        return len(self.active_connections)

# Orquestador Principal
class SilhouetteMCPIntegrationOrchestrator:
    """Orquestador principal de integración SilhouetteMCP"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        
        # Componentes principales
        self.registry = InMemoryServiceRegistry()
        self.load_balancer = LoadBalancerImpl(self.registry)
        self.health_monitor = HealthMonitorImpl(self.registry)
        self.auto_scaler = AutoScalerImpl(self.registry, self.health_monitor)
        self.security_manager = SecurityManagerImpl(self.config.get('secret_key'))
        self.monitoring_system = MonitoringSystem()
        self.websocket_manager = WebSocketManager()
        
        # Estado interno
        self.is_running = False
        self.background_tasks = set()
        self._shutdown_event = asyncio.Event()
        
        # Configuración de servicios predefinidos
        self._setup_default_services()
        self._setup_default_users()
        self._setup_default_alerts()
        
        # FastAPI app
        self.app = FastAPI(
            title="SilhouetteMCP Integration Orchestrator",
            description="Sistema completo de orquestación de integración",
            version="1.0.0"
        )
        self._setup_middleware()
        self._setup_routes()
    
    def _default_config(self) -> Dict[str, Any]:
        """Configuración por defecto"""
        return {
            'host': '0.0.0.0',
            'port': 8025,
            'secret_key': 'silhouettemcp_secret_key_2025',
            'enable_websocket': True,
            'enable_monitoring': True,
            'enable_auto_scaling': True,
            'health_check_interval': 30,
            'auto_scaling_interval': 60,
            'monitoring_interval': 10
        }
    
    def _setup_default_services(self) -> None:
        """Configurar servicios predefinidos"""
        # Servicios originales (8001-8002)
        original_services = [
            ServiceConfig("silhouettemcp_core", "localhost", 8001, "http", weight=2),
            ServiceConfig("silhouettemcp_server", "localhost", 8002, "http", weight=2),
        ]
        
        # Servicios mejorados (8010-8024)
        enhanced_services = [
            ServiceConfig("enhanced_scalability", "localhost", 8010, "http"),
            ServiceConfig("enhanced_security", "localhost", 8011, "http"),
            ServiceConfig("hierarchical_architecture", "localhost", 8012, "http"),
            ServiceConfig("robust_diagnostic", "localhost", 8013, "http"),
            ServiceConfig("comprehensive_verification", "localhost", 8014, "http"),
            ServiceConfig("expanded_content", "localhost", 8015, "http"),
            ServiceConfig("expanded_finance", "localhost", 8016, "http"),
            ServiceConfig("expanded_maps", "localhost", 8017, "http"),
            ServiceConfig("expanded_research", "localhost", 8018, "http"),
            ServiceConfig("expanded_social_travel", "localhost", 8019, "http"),
            ServiceConfig("expanded_supabase", "localhost", 8020, "http"),
            ServiceConfig("superior_allocator", "localhost", 8021, "http"),
            ServiceConfig("comprehensive_diagnostic", "localhost", 8022, "http"),
            ServiceConfig("enhanced_architecture", "localhost", 8023, "http"),
            ServiceConfig("server_unified", "localhost", 8024, "http"),
        ]
        
        all_services = original_services + enhanced_services
        
        # Registrar instancias de servicio
        for service_config in all_services:
            for i in range(2):  # Dos instancias por servicio
                service_instance = ServiceInstance(service_config)
                service_instance.status = ServiceStatus.RUNNING
                asyncio.create_task(self.registry.register_service(service_instance))
        
        # Configurar reglas de auto-scaling
        scaling_rules = {
            "enhanced_scalability": {
                "response_time_threshold": 1.0,
                "cpu_threshold": 70.0,
                "rps_threshold": 50.0
            },
            "enhanced_security": {
                "response_time_threshold": 0.8,
                "cpu_threshold": 60.0,
                "rps_threshold": 30.0
            }
        }
        
        for service_id, rule in scaling_rules.items():
            self.auto_scaler.set_scaling_rule(service_id, rule)
    
    def _setup_default_users(self) -> None:
        """Configurar usuarios por defecto"""
        self.security_manager.add_user("admin", "admin123", ["admin"])
        self.security_manager.add_user("user", "user123", ["read"])
        self.security_manager.add_user("orchestrator", "orch123", ["orchestrator"])
    
    def _setup_default_alerts(self) -> None:
        """Configurar alertas por defecto"""
        alert_rules = [
            AlertRule(
                rule_id="high_cpu",
                name="Alto uso de CPU",
                condition="cpu_usage > 80",
                threshold=80.0,
                severity="warning",
                actions=["log"]
            ),
            AlertRule(
                rule_id="high_memory",
                name="Alto uso de memoria",
                condition="memory_usage > 85",
                threshold=85.0,
                severity="critical",
                actions=["log", "email"]
            ),
            AlertRule(
                rule_id="high_response_time",
                name="Tiempo de respuesta alto",
                condition="response_time > 2.0",
                threshold=2.0,
                severity="warning",
                actions=["log"]
            ),
            AlertRule(
                rule_id="low_healthy_services",
                name="Pocos servicios saludables",
                condition="healthy_services < 2",
                threshold=2,
                severity="critical",
                actions=["log"]
            )
        ]
        
        for alert_rule in alert_rules:
            self.monitoring_system.add_alert_rule(alert_rule)
    
    def _setup_middleware(self) -> None:
        """Configurar middleware de FastAPI"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    def _setup_routes(self) -> None:
        """Configurar rutas de la API"""
        
        # Endpoints principales
        @self.app.get("/", response_model=Dict[str, Any])
        async def root():
            """Endpoint raíz"""
            return {
                "status": "ok",
                "message": "SilhouetteMCP Integration Orchestrator",
                "version": "1.0.0",
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/health", response_model=Dict[str, Any])
        async def health_check():
            """Verificación de salud del orquestador"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "registry": "ok",
                    "load_balancer": "ok",
                    "health_monitor": "ok" if self.health_monitor.is_monitoring else "stopped",
                    "auto_scaler": "ok",
                    "security_manager": "ok",
                    "monitoring_system": "ok"
                }
            }
        
        @self.app.get("/metrics", response_model=SystemMetrics)
        async def get_metrics():
            """Obtener métricas del sistema"""
            metrics = self.monitoring_system.collect_system_metrics(self.registry)
            metrics.active_websocket_connections = self.websocket_manager.get_connection_count()
            return metrics
        
        @self.app.get("/services", response_model=List[ServiceInstance])
        async def get_all_services():
            """Obtener todos los servicios registrados"""
            services = await self.registry.get_services()
            return services
        
        @self.app.get("/services/{service_id}", response_model=List[ServiceInstance])
        async def get_service_instances(service_id: str):
            """Obtener instancias de un servicio específico"""
            services = await self.registry.get_services(service_id)
            if not services:
                raise HTTPException(status_code=404, detail=f"Servicio {service_id} no encontrado")
            return services
        
        @self.app.post("/services/{service_id}/scale_up")
        async def scale_up_service(service_id: str, instances: int = 1):
            """Escalar servicio hacia arriba"""
            success = await self.auto_scaler.scale_up(service_id, instances)
            if not success:
                raise HTTPException(status_code=500, detail=f"Error escalando {service_id}")
            return {"message": f"Servicio {service_id} escalado hacia arriba", "instances": instances}
        
        @self.app.post("/services/{service_id}/scale_down")
        async def scale_down_service(service_id: str, instances: int = 1):
            """Escalar servicio hacia abajo"""
            success = await self.auto_scaler.scale_down(service_id, instances)
            if not success:
                raise HTTPException(status_code=500, detail=f"Error escalando {service_id}")
            return {"message": f"Servicio {service_id} escalado hacia abajo", "instances": instances}
        
        @self.app.get("/load_balancer/strategies", response_model=List[str])
        async def get_load_balance_strategies():
            """Obtener estrategias disponibles de balanceador de carga"""
            return [strategy.value for strategy in LoadBalanceStrategy]
        
        @self.app.post("/load_balancer/route/{service_id}")
        async def route_request(service_id: str, strategy: LoadBalanceStrategy):
            """Enrutar solicitud usando estrategia específica"""
            service = await self.load_balancer.select_service(service_id, strategy)
            if not service:
                raise HTTPException(status_code=404, detail=f"Servicio {service_id} no disponible")
            return {
                "selected_service": service.instance_id,
                "strategy": strategy.value,
                "host": service.config.host,
                "port": service.config.port
            }
        
        @self.app.post("/auth/login")
        async def login(credentials: Dict[str, Any]):
            """Autenticar usuario"""
            token = await self.security_manager.authenticate(credentials)
            if not token:
                raise HTTPException(status_code=401, detail="Credenciales inválidas")
            return {"token": token, "expires_in": 3600}
        
        @self.app.get("/auth/verify")
        async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
            """Verificar token"""
            if not await self.security_manager.authorize(
                credentials.credentials, "system", "read"
            ):
                raise HTTPException(status_code=403, detail="Token inválido")
            return {"valid": True}
        
        @self.app.get("/alerts", response_model=List[Dict[str, Any]])
        async def get_active_alerts():
            """Obtener alertas activas"""
            return list(self.monitoring_system.active_alerts.values())
        
        @self.app.get("/alerts/rules", response_model=List[AlertRule])
        async def get_alert_rules():
            """Obtener reglas de alerta"""
            return list(self.monitoring_system.alert_rules.values())
        
        # WebSocket endpoint
        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str):
            await self.websocket_manager.connect(websocket, client_id)
            try:
                while True:
                    data = await websocket.receive_text()
                    
                    # Procesar mensaje y responder
                    response = {
                        "type": "response",
                        "client_id": client_id,
                        "message": data,
                        "timestamp": datetime.now().isoformat(),
                        "orchestrator_info": {
                            "total_services": len(await self.registry.get_services()),
                            "healthy_services": len(await self.registry.get_healthy_services()),
                            "websocket_connections": self.websocket_manager.get_connection_count()
                        }
                    }
                    
                    await websocket.send_text(json.dumps(response))
                    
            except WebSocketDisconnect:
                await self.websocket_manager.disconnect(client_id)
        
        # Endpoint de proxy para servicios
        @self.app.api_route("/proxy/{service_id}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
        async def proxy_request(
            service_id: str,
            path: str,
            request: Request,
            background_tasks: BackgroundTasks
        ):
            """Proxy para enrutar solicitudes a servicios"""
            try:
                # Seleccionar servicio usando estrategia por defecto
                service = await self.load_balancer.select_service(
                    service_id, 
                    LoadBalanceStrategy.ROUND_ROBIN
                )
                
                if not service:
                    raise HTTPException(status_code=404, detail=f"Servicio {service_id} no disponible")
                
                # Construir URL objetivo
                target_url = f"{service.config.protocol}://{service.config.host}:{service.config.port}/{path}"
                
                # Reenviar solicitud
                async with aiohttp.ClientSession() as session:
                    method = request.method
                    headers = dict(request.headers)
                    headers.pop("host", None)  # Remover host original
                    
                    body = await request.body()
                    
                    async with session.request(
                        method=method,
                        url=target_url,
                        headers=headers,
                        data=body,
                        timeout=aiohttp.ClientTimeout(total=service.config.timeout)
                    ) as response:
                        content = await response.read()
                        
                        # Actualizar estadísticas del servicio
                        background_tasks.add_task(
                            self._update_service_stats,
                            service.instance_id,
                            {"response_time": response.headers.get("X-Response-Time", 0)}
                        )
                        
                        return Response(
                            content=content,
                            status_code=response.status,
                            headers=dict(response.headers)
                        )
            
            except Exception as e:
                logger.error(f"Error en proxy: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _update_service_stats(self, instance_id: str, stats: Dict[str, Any]) -> None:
        """Actualizar estadísticas del servicio"""
        await self.load_balancer.update_service_stats(instance_id, stats)
    
    async def start_background_tasks(self) -> None:
        """Iniciar tareas de fondo"""
        logger.info("Iniciando tareas de fondo del orquestador")
        
        # Monitoreo de salud
        await self.health_monitor.start_monitoring()
        
        # Tarea de auto-scaling
        async def auto_scaling_task():
            while self.is_running:
                try:
                    await self.auto_scaler.evaluate_scaling()
                    await asyncio.sleep(self.config['auto_scaling_interval'])
                except Exception as e:
                    logger.error(f"Error en tarea de auto-scaling: {e}")
                    await asyncio.sleep(self.config['auto_scaling_interval'])
        
        # Tarea de monitoreo del sistema
        async def monitoring_task():
            while self.is_running:
                try:
                    metrics = self.monitoring_system.collect_system_metrics(self.registry)
                    metrics.active_websocket_connections = self.websocket_manager.get_connection_count()
                    
                    # Evaluar alertas
                    triggered_alerts = self.monitoring_system.evaluate_alerts(metrics)
                    
                    # Enviar métricas por WebSocket
                    if self.websocket_manager.get_connection_count() > 0:
                        await self.websocket_manager.broadcast(json.dumps({
                            "type": "metrics",
                            "data": {
                                "timestamp": metrics.timestamp.isoformat(),
                                "cpu_usage": metrics.cpu_usage,
                                "memory_usage": metrics.memory_usage,
                                "healthy_services": metrics.healthy_services,
                                "total_instances": metrics.total_instances,
                                "active_websocket_connections": metrics.active_websocket_connections,
                                "average_response_time": metrics.average_response_time
                            },
                            "triggered_alerts": triggered_alerts
                        }))
                    
                    await asyncio.sleep(self.config['monitoring_interval'])
                except Exception as e:
                    logger.error(f"Error en tarea de monitoreo: {e}")
                    await asyncio.sleep(self.config['monitoring_interval'])
        
        # Ejecutar tareas en background
        self.background_tasks.add(asyncio.create_task(auto_scaling_task()))
        self.background_tasks.add(asyncio.create_task(monitoring_task()))
    
    async def stop_background_tasks(self) -> None:
        """Detener tareas de fondo"""
        logger.info("Deteniendo tareas de fondo del orquestador")
        
        # Cancelar todas las tareas
        for task in self.background_tasks:
            task.cancel()
        
        # Esperar a que terminen
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # Detener monitoreo de salud
        await self.health_monitor.stop_monitoring()
        
        # Limpiar conjunto de tareas
        self.background_tasks.clear()
    
    async def start(self) -> None:
        """Iniciar el orquestador"""
        if self.is_running:
            logger.warning("El orquestador ya está ejecutándose")
            return
        
        logger.info("Iniciando SilhouetteMCP Integration Orchestrator...")
        self.is_running = True
        
        # Iniciar tareas de fondo
        await self.start_background_tasks()
        
        # Configurar manejo de señales
        for sig in [signal.SIGTERM, signal.SIGINT]:
            signal.signal(sig, self._signal_handler)
        
        logger.info("Orquestador iniciado exitosamente")
        logger.info(f"Servidor ejecutándose en http://{self.config['host']}:{self.config['port']}")
        logger.info(f"WebSocket disponible en ws://{self.config['host']}:{self.config['port']}/ws/{{client_id}}")
    
    def _signal_handler(self, signum, frame):
        """Manejador de señales para shutdown graceful"""
        logger.info(f"Señal {signum} recibida, iniciando shutdown...")
        asyncio.create_task(self.stop())
    
    async def stop(self) -> None:
        """Detener el orquestador"""
        if not self.is_running:
            logger.warning("El orquestador no está ejecutándose")
            return
        
        logger.info("Deteniendo SilhouetteMCP Integration Orchestrator...")
        self.is_running = False
        
        # Detener tareas de fondo
        await self.stop_background_tasks()
        
        # Cerrar conexiones WebSocket
        for client_id in list(self.websocket_manager.active_connections.keys()):
            await self.websocket_manager.disconnect(client_id)
        
        # Configurar evento de shutdown
        self._shutdown_event.set()
        
        logger.info("Orquestador detenido exitosamente")
    
    async def wait_for_shutdown(self) -> None:
        """Esperar por shutdown"""
        await self._shutdown_event.wait()
    
    def run(self) -> None:
        """Ejecutar el orquestador con uvicorn"""
        try:
            # Crear evento loop si no existe
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Iniciar orquestador
            loop.run_until_complete(self.start())
            
            # Configurar servidor uvicorn
            config = uvicorn.Config(
                app=self.app,
                host=self.config['host'],
                port=self.config['port'],
                log_level="info"
            )
            server = uvicorn.Server(config)
            
            # Ejecutar servidor con manejo graceful de shutdown
            loop.run_until_complete(server.serve())
            
        except KeyboardInterrupt:
            logger.info("Interrupción por teclado detectada")
        except Exception as e:
            logger.error(f"Error ejecutando orquestador: {e}")
        finally:
            # Cleanup
            try:
                loop.run_until_complete(self.stop())
            except:
                pass
            
            try:
                loop.close()
            except:
                pass

# Función principal
async def main_async():
    """Función principal asíncrona"""
    # Configuración del orquestador
    config = {
        'host': '0.0.0.0',
        'port': 8025,
        'secret_key': 'silhouettemcp_secret_key_2025',
        'enable_websocket': True,
        'enable_monitoring': True,
        'enable_auto_scaling': True,
        'health_check_interval': 30,
        'auto_scaling_interval': 60,
        'monitoring_interval': 10
    }
    
    # Crear e iniciar orquestador
    orchestrator = SilhouetteMCPIntegrationOrchestrator(config)
    
    try:
        await orchestrator.start()
        
        # Mantener el orquestador corriendo
        print("=" * 80)
        print("SilhouetteMCP Integration Orchestrator iniciado exitosamente")
        print("=" * 80)
        print(f"🌐 API HTTP: http://{config['host']}:{config['port']}")
        print(f"🔗 WebSocket: ws://{config['host']}:{config['port']}/ws/{{client_id}}")
        print(f"📊 Métricas: http://{config['host']}:{config['port']}/metrics")
        print(f"❤️  Salud: http://{config['host']}:{config['port']}/health")
        print("=" * 80)
        print("Servicios registrados:")
        
        services = await orchestrator.registry.get_services()
        service_groups = defaultdict(list)
        for service in services:
            service_groups[service.config.service_id].append(service)
        
        for service_id, instances in service_groups.items():
            print(f"  • {service_id}: {len(instances)} instancias")
        
        print("=" * 80)
        print("Presiona Ctrl+C para detener el orquestador")
        print("=" * 80)
        
        # Esperar por shutdown
        await orchestrator.wait_for_shutdown()
        
    except KeyboardInterrupt:
        print("\n⏹️  Deteniendo orquestador...")
    finally:
        await orchestrator.stop()
        print("✅ Orquestador detenido exitosamente")

def main():
    """Función principal"""
    try:
        # Ejecutar orquestador asíncrono
        asyncio.run(main_async())
    except Exception as e:
        logger.error(f"Error ejecutando orquestador: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()