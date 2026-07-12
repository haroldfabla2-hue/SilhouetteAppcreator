"""
API Gateway Avanzado para MCP Core Superior
Maneja routing, load balancing, rate limiting y seguridad
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import aiohttp
from aiohttp import web, ClientSession, ClientTimeout
from aiohttp.web_runner import AppRunner, TCPSite
import jwt
import logging
from urllib.parse import urlparse, parse_qs
import hashlib
from collections import defaultdict, deque


class LoadBalancingStrategy(Enum):
    """Estrategias de load balancing"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    IP_HASH = "ip_hash"
    LEAST_RESPONSE_TIME = "least_response_time"


@dataclass
class RouteRule:
    """Regla de routing para el API Gateway"""
    path_pattern: str
    methods: List[str]
    target_services: List[str]
    load_balancing: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    weights: Optional[Dict[str, int]] = None
    timeout_seconds: int = 30
    retry_attempts: int = 3
    circuit_breaker_enabled: bool = True
    rate_limit_rps: Optional[int] = None
    authentication_required: bool = True
    allowlist: Optional[List[str]] = None
    blocklist: Optional[List[str]] = None
    headers_to_add: Optional[Dict[str, str]] = None
    headers_to_remove: Optional[List[str]] = None
    transform_request: Optional[Callable] = None
    transform_response: Optional[Callable] = None


@dataclass
class ServiceInstance:
    """Instancia de servicio en el gateway"""
    service_name: str
    host: str
    port: int
    path: str = "/"
    protocol: str = "http"
    weight: int = 100
    health_check_path: str = "/health"
    is_healthy: bool = True
    current_connections: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_health_check: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class APIKeyManager:
    """Gestor de API Keys para el gateway"""
    
    def __init__(self):
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.rate_limits: Dict[str, Dict[str, int]] = defaultdict(lambda: {"requests": 0, "reset_time": 0})
        self.blocked_keys: set = set()
    
    def register_api_key(
        self,
        key_id: str,
        name: str,
        permissions: List[str],
        rate_limit_rps: int = 100,
        rate_limit_rpm: int = 6000,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Registrar una nueva API Key"""
        self.api_keys[key_id] = {
            "name": name,
            "permissions": permissions,
            "rate_limit_rps": rate_limit_rps,
            "rate_limit_rpm": rate_limit_rpm,
            "expires_at": expires_at,
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
            "last_used": None,
            "usage_count": 0
        }
    
    def validate_api_key(self, key_id: str) -> Optional[Dict[str, Any]]:
        """Validar API Key"""
        if key_id in self.blocked_keys:
            return None
            
        key_info = self.api_keys.get(key_id)
        if not key_info:
            return None
            
        # Verificar expiración
        if key_info["expires_at"] and key_info["expires_at"] < datetime.utcnow():
            return None
            
        # Actualizar uso
        key_info["last_used"] = datetime.utcnow()
        key_info["usage_count"] += 1
        
        return key_info
    
    def check_rate_limit(self, key_id: str, limit_type: str = "rps") -> bool:
        """Verificar rate limit para una API Key"""
        now = time.time()
        current_window = int(now // 60)  # Ventana de 1 minuto
        
        if key_id not in self.rate_limits:
            self.rate_limits[key_id] = {"requests": 0, "reset_time": current_window}
        
        rate_data = self.rate_limits[key_id]
        
        # Reset ventana si cambió
        if rate_data["reset_time"] != current_window:
            rate_data["requests"] = 0
            rate_data["reset_time"] = current_window
        
        # Verificar límites
        key_info = self.api_keys.get(key_id)
        if not key_info:
            return False
            
        limit_key = f"rate_limit_{limit_type}"
        limit_value = key_info.get(limit_key, 100)
        
        if rate_data["requests"] >= limit_value:
            return False
            
        rate_data["requests"] += 1
        return True
    
    def block_api_key(self, key_id: str) -> None:
        """Bloquear una API Key"""
        self.blocked_keys.add(key_id)
    
    def unblock_api_key(self, key_id: str) -> None:
        """Desbloquear una API Key"""
        self.blocked_keys.discard(key_id)


class AdvancedAPIGateway:
    """API Gateway Avanzado para MCP Core Superior"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.routes: List[RouteRule] = []
        self.services: Dict[str, List[ServiceInstance]] = defaultdict(list)
        self.load_balancers: Dict[str, int] = defaultdict(int)  # Para round robin
        self.api_key_manager = APIKeyManager()
        self.health_checker_task = None
        self.stats_collector_task = None
        self.is_running = False
        self.app = web.Application()
        self.setup_routes()
        
        # Métricas
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "blocked_requests": 0,
            "average_response_time": 0.0,
            "active_connections": 0,
            "services_healthy": 0,
            "services_total": 0
        }
        
        # Circuit breakers state
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
    
    def setup_routes(self) -> None:
        """Configurar rutas del gateway"""
        self.app.router.add_post("/gateway/route", self.handle_request)
        self.app.router.add_get("/gateway/health", self.health_check)
        self.app.router.add_get("/gateway/metrics", self.get_metrics)
        self.app.router.add_post("/gateway/register-route", self.register_route)
        self.app.router.add_post("/gateway/register-service", self.register_service)
    
    async def start(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        """Iniciar el API Gateway"""
        try:
            runner = AppRunner(self.app)
            await runner.setup()
            site = TCPSite(runner, host, port)
            await site.start()
            
            self.is_running = True
            self.health_checker_task = asyncio.create_task(self._health_check_loop())
            self.stats_collector_task = asyncio.create_task(self._stats_collection_loop())
            
            # Cargar configuración inicial
            await self._load_default_routes()
            
            self.logger.info(f"API Gateway iniciado en {host}:{port}")
            
        except Exception as e:
            self.logger.error(f"Error iniciando API Gateway: {e}")
            raise
    
    async def stop(self) -> None:
        """Detener el API Gateway"""
        self.is_running = False
        
        if self.health_checker_task:
            self.health_checker_task.cancel()
            
        if self.stats_collector_task:
            self.stats_collector_task.cancel()
            
        self.logger.info("API Gateway detenido")
    
    async def _load_default_routes(self) -> None:
        """Cargar rutas por defecto"""
        default_routes = [
            RouteRule(
                path_pattern="/api/v1/{path:.*}",
                methods=["GET", "POST", "PUT", "DELETE"],
                target_services=["mcp_core_superior"],
                load_balancing=LoadBalancingStrategy.ROUND_ROBIN,
                timeout_seconds=30,
                retry_attempts=3,
                circuit_breaker_enabled=True,
                rate_limit_rps=100
            ),
            RouteRule(
                path_pattern="/agents/{path:.*}",
                methods=["GET", "POST"],
                target_services=["reasoner_agent", "planner_agent", "executor_agent", "verifier_agent"],
                load_balancing=LoadBalancingStrategy.LEAST_CONNECTIONS,
                timeout_seconds=60,
                retry_attempts=2,
                circuit_breaker_enabled=True,
                rate_limit_rps=50
            ),
            RouteRule(
                path_pattern="/streaming/{path:.*}",
                methods=["GET", "POST"],
                target_services=["streaming_engine"],
                load_balancing=LoadBalancingStrategy.ROUND_ROBIN,
                timeout_seconds=120,
                retry_attempts=1,
                circuit_breaker_enabled=False,  # WebSocket no es compatible con circuit breaker
                rate_limit_rps=20
            )
        ]
        
        for route in default_routes:
            self.routes.append(route)
    
    async def register_route(self, request: web.Request) -> web.Response:
        """Registrar una nueva ruta"""
        try:
            data = await request.json()
            
            route = RouteRule(
                path_pattern=data["path_pattern"],
                methods=data.get("methods", ["GET"]),
                target_services=data["target_services"],
                load_balancing=LoadBalancingStrategy(data.get("load_balancing", "round_robin")),
                weights=data.get("weights"),
                timeout_seconds=data.get("timeout_seconds", 30),
                retry_attempts=data.get("retry_attempts", 3),
                circuit_breaker_enabled=data.get("circuit_breaker_enabled", True),
                rate_limit_rps=data.get("rate_limit_rps"),
                authentication_required=data.get("authentication_required", True),
                allowlist=data.get("allowlist"),
                blocklist=data.get("blocklist"),
                headers_to_add=data.get("headers_to_add"),
                headers_to_remove=data.get("headers_to_remove")
            )
            
            self.routes.append(route)
            
            return web.json_response({"status": "success", "message": "Ruta registrada"})
            
        except Exception as e:
            self.logger.error(f"Error registrando ruta: {e}")
            return web.json_response({"error": str(e)}, status=400)
    
    async def register_service(self, request: web.Request) -> web.Response:
        """Registrar una nueva instancia de servicio"""
        try:
            data = await request.json()
            
            instance = ServiceInstance(
                service_name=data["service_name"],
                host=data["host"],
                port=data["port"],
                path=data.get("path", "/"),
                protocol=data.get("protocol", "http"),
                weight=data.get("weight", 100),
                health_check_path=data.get("health_check_path", "/health"),
                metadata=data.get("metadata")
            )
            
            self.services[instance.service_name].append(instance)
            self.metrics["services_total"] = len(self.services)
            
            return web.json_response({"status": "success", "message": "Servicio registrado"})
            
        except Exception as e:
            self.logger.error(f"Error registrando servicio: {e}")
            return web.json_response({"error": str(e)}, status=400)
    
    async def handle_request(self, request: web.Request) -> web.Response:
        """Manejar request a través del gateway"""
        start_time = time.time()
        
        try:
            self.metrics["total_requests"] += 1
            
            # Extraer API Key del header
            api_key = request.headers.get("X-API-Key")
            if not api_key:
                self.metrics["blocked_requests"] += 1
                return web.json_response({"error": "API Key requerida"}, status=401)
            
            # Validar API Key
            key_info = self.api_key_manager.validate_api_key(api_key)
            if not key_info:
                self.metrics["blocked_requests"] += 1
                return web.json_response({"error": "API Key inválida"}, status=401)
            
            # Verificar rate limit
            if not self.api_key_manager.check_rate_limit(api_key, "rps"):
                self.metrics["blocked_requests"] += 1
                return web.json_response({"error": "Rate limit excedido"}, status=429)
            
            # Buscar ruta coincidente
            route = self._find_matching_route(request.path, request.method)
            if not route:
                return web.json_response({"error": "Ruta no encontrada"}, status=404)
            
            # Verificar autenticación y permisos
            if route.authentication_required and not self._check_permissions(key_info, route):
                self.metrics["blocked_requests"] += 1
                return web.json_response({"error": "Permisos insuficientes"}, status=403)
            
            # Obtener servicio target
            service_instance = self._select_service_instance(route)
            if not service_instance:
                return web.json_response({"error": "Servicio no disponible"}, status=503)
            
            # Verificar circuit breaker
            if route.circuit_breaker_enabled and self._is_circuit_breaker_open(service_instance):
                return web.json_response({"error": "Circuito abierto - servicio temporalmente no disponible"}, status=503)
            
            # Preparar request
            modified_request = await self._prepare_request(request, route, service_instance)
            
            # Enviar request
            response = await self._proxy_request(modified_request, service_instance, route)
            
            # Actualizar métricas y circuit breaker
            response_time = time.time() - start_time
            self._update_service_metrics(service_instance, response, response_time)
            self._update_circuit_breaker(service_instance, response, response_time)
            
            if response.status < 400:
                self.metrics["successful_requests"] += 1
            else:
                self.metrics["failed_requests"] += 1
            
            # Transformar respuesta
            transformed_response = await self._transform_response(response, route)
            
            return transformed_response
            
        except Exception as e:
            self.logger.error(f"Error procesando request: {e}")
            self.metrics["failed_requests"] += 1
            return web.json_response({"error": "Error interno del gateway"}, status=500)
    
    def _find_matching_route(self, path: str, method: str) -> Optional[RouteRule]:
        """Encontrar ruta coincidente"""
        for route in self.routes:
            if self._path_matches(path, route.path_pattern) and method in route.methods:
                return route
        return None
    
    def _path_matches(self, path: str, pattern: str) -> bool:
        """Verificar si path coincide con patrón (simplificado)"""
        import re
        # Convertir patrón a regex
        regex_pattern = pattern.replace("{path:.*}", ".*")
        regex_pattern = regex_pattern.replace("{path}", ".*")
        
        return bool(re.match(f"^{regex_pattern}$", path))
    
    def _check_permissions(self, key_info: Dict[str, Any], route: RouteRule) -> bool:
        """Verificar permisos de API Key para la ruta"""
        required_permissions = self._get_required_permissions(route)
        
        if not required_permissions:
            return True
            
        key_permissions = key_info.get("permissions", [])
        return any(perm in key_permissions for perm in required_permissions)
    
    def _get_required_permissions(self, route: RouteRule) -> List[str]:
        """Obtener permisos requeridos para una ruta"""
        # Simplificado - en implementación real sería más sofisticado
        return ["api:access"]
    
    def _select_service_instance(self, route: RouteRule) -> Optional[ServiceInstance]:
        """Seleccionar instancia de servicio usando load balancing"""
        healthy_instances = [
            instance for service_instances in [
                self.services.get(service_name, []) 
                for service_name in route.target_services
            ]
            for instance in service_instances
            if instance.is_healthy
        ]
        
        if not healthy_instances:
            return None
        
        # Aplicar estrategia de load balancing
        if route.load_balancing == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_select(healthy_instances, route.target_services)
        elif route.load_balancing == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_select(healthy_instances, route)
        elif route.load_balancing == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return min(healthy_instances, key=lambda x: x.current_connections)
        elif route.load_balancing == LoadBalancingStrategy.IP_HASH:
            return self._ip_hash_select(healthy_instances)
        else:
            return healthy_instances[0]
    
    def _round_robin_select(self, instances: List[ServiceInstance], service_names: List[str]) -> ServiceInstance:
        """Selección round robin"""
        service_index = self.load_balancers["round_robin"] % len(service_names)
        selected_service = service_names[service_index]
        self.load_balancers["round_robin"] += 1
        
        # Obtener instancia saludable de ese servicio
        for instance in instances:
            if instance.service_name == selected_service:
                return instance
        
        return instances[0]  # Fallback
    
    def _weighted_round_robin_select(self, instances: List[ServiceInstance], route: RouteRule) -> ServiceInstance:
        """Selección weighted round robin"""
        if not route.weights:
            return instances[0]
        
        # Implementar weighted round robin
        total_weight = sum(route.weights.values())
        random_weight = sum(instance.weight for instance in instances) % total_weight
        
        current_weight = 0
        for instance in instances:
            weight = route.weights.get(instance.service_name, instance.weight)
            current_weight += weight
            if current_weight >= random_weight:
                return instance
        
        return instances[0]
    
    def _ip_hash_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Selección IP hash"""
        # En implementación real, usar IP del cliente
        hash_value = hash("client_ip") % len(instances)
        return instances[hash_value]
    
    def _is_circuit_breaker_open(self, instance: ServiceInstance) -> bool:
        """Verificar si circuit breaker está abierto"""
        service_id = f"{instance.service_name}:{instance.host}:{instance.port}"
        
        if service_id not in self.circuit_breakers:
            return False
        
        breaker = self.circuit_breakers[service_id]
        return breaker.get("state") == "open"
    
    def _prepare_request(self, request: web.Request, route: RouteRule, service: ServiceInstance) -> Dict[str, Any]:
        """Preparar request para enviar al servicio"""
        # Construir URL del servicio
        service_url = f"{service.protocol}://{service.host}:{service.port}{service.path}"
        if request.path_qs:
            service_url += request.path_qs
        
        # Preparar headers
        headers = dict(request.headers)
        
        # Agregar headers de la ruta
        if route.headers_to_add:
            headers.update(route.headers_to_add)
        
        # Remover headers de la ruta
        if route.headers_to_remove:
            for header in route.headers_to_remove:
                headers.pop(header, None)
        
        # Preparar request data
        request_data = {
            "method": request.method,
            "url": service_url,
            "headers": headers,
            "timeout": ClientTimeout(total=route.timeout_seconds)
        }
        
        # Agregar body si existe
        if request.can_read_body:
            request_data["data"] = request.content_type
        
        return request_data
    
    async def _proxy_request(self, request_data: Dict[str, Any], service: ServiceInstance, route: RouteRule) -> aiohttp.ClientResponse:
        """Enviar request al servicio con retry y circuit breaker"""
        last_error = None
        
        for attempt in range(route.retry_attempts + 1):
            try:
                service.current_connections += 1
                
                async with ClientSession() as session:
                    async with session.request(**request_data) as response:
                        service.current_connections -= 1
                        return response
                        
            except Exception as e:
                service.current_connections -= 1
                last_error = e
                self.logger.warning(f"Request fallido a {service.service_name}, intento {attempt + 1}: {e}")
                
                if attempt < route.retry_attempts:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise last_error
    
    def _update_service_metrics(self, service: ServiceInstance, response: aiohttp.ClientResponse, response_time: float) -> None:
        """Actualizar métricas del servicio"""
        service.total_requests += 1
        
        if response.status >= 400:
            service.failed_requests += 1
        
        # Actualizar tiempo de respuesta promedio
        if service.total_requests == 1:
            service.average_response_time = response_time
        else:
            service.average_response_time = (
                (service.average_response_time * (service.total_requests - 1) + response_time) / service.total_requests
            )
    
    def _update_circuit_breaker(self, service: ServiceInstance, response: aiohttp.ClientResponse, response_time: float) -> None:
        """Actualizar estado del circuit breaker"""
        service_id = f"{service.service_name}:{service.host}:{service.port}"
        
        if service_id not in self.circuit_breakers:
            self.circuit_breakers[service_id] = {
                "state": "closed",
                "failure_count": 0,
                "last_failure_time": None,
                "consecutive_failures": 0
            }
        
        breaker = self.circuit_breakers[service_id]
        
        if response.status >= 500:
            breaker["failure_count"] += 1
            breaker["consecutive_failures"] += 1
            breaker["last_failure_time"] = datetime.utcnow()
            
            # Abrir circuito si hay demasiados fallos consecutivos
            if breaker["consecutive_failures"] >= 5:
                breaker["state"] = "open"
                self.logger.warning(f"Circuit breaker abierto para {service.service_name}")
                
        else:
            # Reset contador en caso de éxito
            breaker["consecutive_failures"] = 0
            
            # Cerrar circuito si está en half-open y el request fue exitoso
            if breaker["state"] == "half_open":
                breaker["state"] = "closed"
                self.logger.info(f"Circuit breaker cerrado para {service.service_name}")
        
        # Cambiar a half-open después del timeout
        if breaker["state"] == "open":
            timeout_duration = timedelta(seconds=60)  # 1 minuto
            if breaker["last_failure_time"] and datetime.utcnow() - breaker["last_failure_time"] > timeout_duration:
                breaker["state"] = "half_open"
    
    async def _transform_response(self, response: aiohttp.ClientResponse, route: RouteRule) -> web.Response:
        """Transformar respuesta según reglas de la ruta"""
        try:
            # Leer respuesta
            body = await response.read()
            
            # Aplicar transformaciones de la ruta
            if route.transform_response:
                body = route.transform_response(body)
            
            # Crear respuesta
            resp = web.Response(
                body=body,
                status=response.status,
                headers=dict(response.headers)
            )
            
            return resp
            
        except Exception as e:
            self.logger.error(f"Error transformando respuesta: {e}")
            return web.json_response({"error": "Error procesando respuesta"}, status=500)
    
    async def _health_check_loop(self) -> None:
        """Loop de health checks"""
        while self.is_running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(30)  # Health check cada 30 segundos
                
            except Exception as e:
                self.logger.error(f"Error en health check loop: {e}")
                await asyncio.sleep(30)
    
    async def _stats_collection_loop(self) -> None:
        """Loop de recolección de estadísticas"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Recopilar estadísticas cada minuto
                self._update_global_metrics()
                
            except Exception as e:
                self.logger.error(f"Error en stats collection loop: {e}")
                await asyncio.sleep(60)
    
    async def _perform_health_checks(self) -> None:
        """Realizar health checks a todos los servicios"""
        healthy_count = 0
        total_count = 0
        
        for service_instances in self.services.values():
            for instance in service_instances:
                total_count += 1
                try:
                    # Health check simple
                    async with aiohttp.ClientSession() as session:
                        health_url = f"{instance.protocol}://{instance.host}:{instance.port}{instance.health_check_path}"
                        async with session.get(health_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                            instance.is_healthy = response.status < 400
                            instance.last_health_check = datetime.utcnow()
                            
                            if instance.is_healthy:
                                healthy_count += 1
                                
                except Exception as e:
                    instance.is_healthy = False
                    self.logger.warning(f"Health check fallido para {instance.service_name}:{instance.host}:{instance.port}: {e}")
        
        self.metrics["services_healthy"] = healthy_count
        self.metrics["services_total"] = total_count
    
    def _update_global_metrics(self) -> None:
        """Actualizar métricas globales"""
        total_requests = self.metrics["successful_requests"] + self.metrics["failed_requests"]
        if total_requests > 0:
            self.metrics["average_response_time"] = (
                self.metrics.get("total_response_time", 0) / total_requests
            )
    
    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.json_response({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": self.metrics
        })
    
    async def get_metrics(self, request: web.Request) -> web.Response:
        """Obtener métricas del gateway"""
        return web.json_response({
            "metrics": self.metrics,
            "services": {
                name: [
                    {
                        "host": instance.host,
                        "port": instance.port,
                        "healthy": instance.is_healthy,
                        "connections": instance.current_connections,
                        "requests": instance.total_requests,
                        "avg_response_time": instance.average_response_time
                    }
                    for instance in instances
                ]
                for name, instances in self.services.items()
            },
            "circuit_breakers": self.circuit_breakers
        })


# Instancia global del gateway
api_gateway: Optional[AdvancedAPIGateway] = None


async def initialize_api_gateway(config: Dict[str, Any]) -> AdvancedAPIGateway:
    """Inicializar API Gateway"""
    global api_gateway
    
    api_gateway = AdvancedAPIGateway(config)
    await api_gateway.start()
    
    return api_gateway


async def get_api_gateway() -> AdvancedAPIGateway:
    """Obtener instancia del API Gateway"""
    if not api_gateway:
        raise RuntimeError("API Gateway no inicializado. Llamar initialize_api_gateway primero.")
    return api_gateway