"""
Sistema de Rate Limiting Enterprise para MCP Core Superior
Implementa rate limiting granular por servicio, usuario y endpoint
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import aioredis
import logging
from concurrent.futures import ThreadPoolExecutor


class RateLimitStrategy(Enum):
    """Estrategias de rate limiting"""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    ADAPTIVE = "adaptive"


@dataclass
class RateLimitConfig:
    """Configuración de rate limiting por servicio/endpoint"""
    service_name: str
    endpoint: str = "*"
    requests_per_second: Optional[float] = None
    requests_per_minute: Optional[int] = None
    requests_per_hour: Optional[int] = None
    requests_per_day: Optional[int] = None
    burst_allowance: int = 10
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    headers_to_add: Dict[str, str] = field(default_factory=dict)
    blocked_response: Dict[str, Any] = field(default_factory=lambda: {
        "status": 429,
        "message": "Rate limit exceeded",
        "retry_after": 60
    })
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RateLimitEntry:
    """Entrada de rate limiting para tracking"""
    identifier: str  # user_id, api_key, ip, etc.
    service_name: str
    endpoint: str
    timestamp: float
    request_data: Dict[str, Any] = field(default_factory=dict)


class AdvancedRateLimiter:
    """Sistema avanzado de rate limiting enterprise"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.redis = None
        self.memory_store = {}
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        # Configuraciones por servicio
        self.rate_configs: Dict[str, RateLimitConfig] = {}
        
        # Storage para diferentes estrategias
        self.fixed_windows: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        self.sliding_windows: Dict[str, deque] = defaultdict(deque)
        self.token_buckets: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(lambda: 1.0))
        self.adaptive_limits: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(lambda: 1.0))
        
        # Métricas
        self.metrics = {
            "requests_allowed": 0,
            "requests_blocked": 0,
            "average_check_time": 0.0,
            "services_configured": 0,
            "active_identifiers": set()
        }
    
    async def initialize(self) -> None:
        """Inicializar el rate limiter"""
        try:
            # Conectar a Redis para persistencia
            redis_config = self.config.get("redis", {})
            self.redis = await aioredis.from_url(
                redis_config.get("url", "redis://localhost:6379"),
                **redis_config.get("connection", {})
            )
            
            # Cargar configuraciones por defecto
            await self._load_default_configs()
            
            self.logger.info("Advanced Rate Limiter inicializado")
            
        except Exception as e:
            self.logger.error(f"Error inicializando rate limiter: {e}")
            raise
    
    async def _load_default_configs(self) -> None:
        """Cargar configuraciones por defecto"""
        default_configs = [
            RateLimitConfig(
                service_name="mcp_core_superior",
                endpoint="/api/v1/*",
                requests_per_second=100,
                requests_per_minute=6000,
                burst_allowance=20,
                strategy=RateLimitStrategy.SLIDING_WINDOW
            ),
            RateLimitConfig(
                service_name="agents",
                endpoint="*",
                requests_per_second=50,
                requests_per_minute=3000,
                burst_allowance=10,
                strategy=RateLimitStrategy.TOKEN_BUCKET
            ),
            RateLimitConfig(
                service_name="streaming",
                endpoint="*",
                requests_per_second=20,
                requests_per_minute=1200,
                burst_allowance=5,
                strategy=RateLimitStrategy.FIXED_WINDOW
            ),
            RateLimitConfig(
                service_name="auth",
                endpoint="*",
                requests_per_second=10,
                requests_per_minute=600,
                burst_allowance=3,
                strategy=RateLimitStrategy.ADAPTIVE
            )
        ]
        
        for config in default_configs:
            await self.register_rate_config(config)
    
    async def register_rate_config(self, config: RateLimitConfig) -> None:
        """Registrar configuración de rate limiting"""
        key = f"{config.service_name}:{config.endpoint}"
        self.rate_configs[key] = config
        self.metrics["services_configured"] += 1
        
        self.logger.debug(f"Rate limit config registrada: {key}")
    
    async def check_rate_limit(
        self,
        identifier: str,
        service_name: str,
        endpoint: str,
        request_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Verificar rate limit para un request"""
        start_time = time.time()
        
        try:
            # Buscar configuración aplicable
            config = self._find_rate_config(service_name, endpoint)
            if not config:
                # Sin configuración = sin límites
                return {
                    "allowed": True,
                    "remaining": float('inf'),
                    "reset_time": time.time() + 3600,
                    "reason": "no_config"
                }
            
            # Verificar según estrategia
            result = await self._check_by_strategy(
                config, identifier, service_name, endpoint, request_data
            )
            
            # Actualizar métricas
            check_time = time.time() - start_time
            self._update_metrics(result["allowed"], check_time)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error verificando rate limit: {e}")
            # En caso de error, permitir request pero loggear
            return {
                "allowed": True,
                "remaining": 0,
                "reset_time": time.time() + 3600,
                "reason": "error_fallback"
            }
    
    def _find_rate_config(self, service_name: str, endpoint: str) -> Optional[RateLimitConfig]:
        """Encontrar configuración de rate limit aplicable"""
        # Buscar configuración específica exacta
        specific_key = f"{service_name}:{endpoint}"
        if specific_key in self.rate_configs:
            return self.rate_configs[specific_key]
        
        # Buscar configuración con wildcard
        for key, config in self.rate_configs.items():
            if config.service_name == service_name:
                if config.endpoint == "*" or endpoint.startswith(config.endpoint.rstrip("*")):
                    return config
        
        return None
    
    async def _check_by_strategy(
        self,
        config: RateLimitConfig,
        identifier: str,
        service_name: str,
        endpoint: str,
        request_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Verificar rate limit según estrategia específica"""
        limit_key = f"{identifier}:{service_name}:{endpoint}"
        
        if config.strategy == RateLimitStrategy.FIXED_WINDOW:
            return await self._check_fixed_window(config, limit_key)
        elif config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return await self._check_sliding_window(config, limit_key)
        elif config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return await self._check_token_bucket(config, limit_key)
        elif config.strategy == RateLimitStrategy.ADAPTIVE:
            return await self._check_adaptive(config, limit_key, request_data)
        else:
            # Fallback a sliding window
            return await self._check_sliding_window(config, limit_key)
    
    async def _check_fixed_window(self, config: RateLimitConfig, limit_key: str) -> Dict[str, Any]:
        """Fixed window rate limiting"""
        current_time = int(time.time())
        window_start = current_time - (current_time % 60)  # Ventana de 1 minuto
        
        if limit_key not in self.fixed_windows[str(window_start)]:
            self.fixed_windows[str(window_start)][limit_key] = deque()
        
        window = self.fixed_windows[str(window_start)][limit_key]
        
        # Limpiar ventanas antiguas
        for old_window in list(self.fixed_windows.keys()):
            if int(old_window) < current_time - 300:  # Mantener 5 minutos de histórico
                del self.fixed_windows[old_window]
        
        # Verificar límites
        max_requests = config.requests_per_minute or config.requests_per_second * 60
        if len(window) >= max_requests:
            return {
                "allowed": False,
                "remaining": 0,
                "reset_time": window_start + 60,
                "reason": "fixed_window_exceeded",
                **config.blocked_response
            }
        
        # Agregar request
        window.append(current_time)
        
        remaining = max_requests - len(window)
        return {
            "allowed": True,
            "remaining": remaining,
            "reset_time": window_start + 60,
            "reason": "fixed_window_ok"
        }
    
    async def _check_sliding_window(self, config: RateLimitConfig, limit_key: str) -> Dict[str, Any]:
        """Sliding window rate limiting"""
        current_time = time.time()
        window_size = 60  # 1 minuto
        
        # Obtener ventana actual
        if limit_key not in self.sliding_windows:
            self.sliding_windows[limit_key] = deque()
        
        window = self.sliding_windows[limit_key]
        
        # Remover requests fuera de la ventana
        while window and (current_time - window[0]) > window_size:
            window.popleft()
        
        # Verificar límites
        max_requests = config.requests_per_minute or int(config.requests_per_second * 60)
        if len(window) >= max_requests:
            # Agregar headers informativos
            result = {
                "allowed": False,
                "remaining": 0,
                "reset_time": current_time + window_size,
                "reason": "sliding_window_exceeded",
                **config.blocked_response
            }
            
            # Agregar headers RFC compliant
            result.update({
                "headers": {
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + window_size)),
                    "Retry-After": str(int(window_size))
                }
            })
            
            return result
        
        # Agregar request
        window.append(current_time)
        
        remaining = max_requests - len(window)
        reset_time = current_time + window_size
        
        return {
            "allowed": True,
            "remaining": remaining,
            "reset_time": reset_time,
            "reason": "sliding_window_ok",
            "headers": {
                "X-RateLimit-Limit": str(max_requests),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(int(reset_time))
            }
        }
    
    async def _check_token_bucket(self, config: RateLimitConfig, limit_key: str) -> Dict[str, Any]:
        """Token bucket rate limiting"""
        current_time = time.time()
        
        # Obtener bucket
        if limit_key not in self.token_buckets:
            self.token_buckets[limit_key] = {"tokens": float(config.burst_allowance), "last_refill": current_time}
        
        bucket = self.token_buckets[limit_key]
        
        # Calcular tokens a agregar
        rate_per_second = config.requests_per_second or 1.0
        time_passed = current_time - bucket["last_refill"]
        tokens_to_add = time_passed * rate_per_second
        
        # Refill bucket
        bucket["tokens"] = min(config.burst_allowance, bucket["tokens"] + tokens_to_add)
        bucket["last_refill"] = current_time
        
        # Verificar si hay tokens disponibles
        if bucket["tokens"] < 1.0:
            return {
                "allowed": False,
                "remaining": 0,
                "reset_time": current_time + (1.0 / rate_per_second),
                "reason": "token_bucket_empty",
                **config.blocked_response
            }
        
        # Consumir token
        bucket["tokens"] -= 1.0
        
        return {
            "allowed": True,
            "remaining": int(bucket["tokens"]),
            "reset_time": current_time + (1.0 / rate_per_second),
            "reason": "token_bucket_ok"
        }
    
    async def _check_adaptive(
        self,
        config: RateLimitConfig,
        limit_key: str,
        request_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Adaptive rate limiting (ajusta límites basado en performance del sistema)"""
        current_time = time.time()
        
        # Obtener límites adaptivos actuales
        if limit_key not in self.adaptive_limits:
            self.adaptive_limits[limit_key] = {
                "current_rps": config.requests_per_second or 10.0,
                "last_adjustment": current_time,
                "performance_score": 1.0
            }
        
        adaptive = self.adaptive_limits[limit_key]
        
        # Ajustar límites cada minuto basado en performance
        if current_time - adaptive["last_adjustment"] > 60:
            await self._adjust_adaptive_limits(limit_key, adaptive, config)
        
        # Usar sliding window con límites adaptivos
        current_config = RateLimitConfig(
            service_name="adaptive",
            endpoint="adaptive",
            requests_per_second=adaptive["current_rps"],
            burst_allowance=config.burst_allowance,
            strategy=RateLimitStrategy.SLIDING_WINDOW
        )
        
        result = await self._check_sliding_window(current_config, limit_key)
        
        # Ajustar score basado en resultado
        if result["allowed"]:
            adaptive["performance_score"] = min(1.0, adaptive["performance_score"] + 0.1)
        else:
            adaptive["performance_score"] = max(0.1, adaptive["performance_score"] - 0.2)
        
        return result
    
    async def _adjust_adaptive_limits(
        self,
        limit_key: str,
        adaptive: Dict[str, float],
        config: RateLimitConfig,
        request_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Ajustar límites adaptativos basado en métricas del sistema"""
        # Obtener métricas del sistema (CPU, memoria, latencia, etc.)
        system_metrics = await self._get_system_metrics()
        
        # Ajustar límites basado en performance
        base_rps = config.requests_per_second or 10.0
        
        # Reducir límites si el sistema está bajo estrés
        cpu_usage = system_metrics.get("cpu_usage", 0.5)
        memory_usage = system_metrics.get("memory_usage", 0.5)
        avg_response_time = system_metrics.get("avg_response_time", 1.0)
        
        stress_factor = (cpu_usage + memory_usage) / 2
        latency_factor = min(2.0, avg_response_time / 1.0)  # Normalizar a 1.0s
        
        # Ajustar límites
        adaptive["current_rps"] = base_rps * adaptive["performance_score"] / (stress_factor + latency_factor)
        adaptive["current_rps"] = max(1.0, min(base_rps * 2, adaptive["current_rps"]))  # Clamp entre 1 y 2x base
        adaptive["last_adjustment"] = time.time()
        
        self.logger.debug(f"Límites adaptativos ajustados para {limit_key}: {adaptive['current_rps']:.2f} RPS")
    
    async def _get_system_metrics(self) -> Dict[str, float]:
        """Obtener métricas del sistema para ajuste adaptativo"""
        try:
            # En implementación real, usar psutil
            import psutil
            return {
                "cpu_usage": psutil.cpu_percent(interval=1) / 100.0,
                "memory_usage": psutil.virtual_memory().percent / 100.0,
                "avg_response_time": 1.0,  # Placeholder
                "active_connections": 100  # Placeholder
            }
        except ImportError:
            # Sin psutil, usar valores por defecto
            return {
                "cpu_usage": 0.5,
                "memory_usage": 0.5,
                "avg_response_time": 1.0,
                "active_connections": 100
            }
    
    def _update_metrics(self, allowed: bool, check_time: float) -> None:
        """Actualizar métricas del rate limiter"""
        if allowed:
            self.metrics["requests_allowed"] += 1
        else:
            self.metrics["requests_blocked"] += 1
        
        # Promedio móvil del tiempo de verificación
        total_checks = self.metrics["requests_allowed"] + self.metrics["requests_blocked"]
        current_avg = self.metrics["average_check_time"]
        
        if total_checks > 1:
            new_avg = ((current_avg * (total_checks - 1)) + check_time) / total_checks
            self.metrics["average_check_time"] = new_avg
        else:
            self.metrics["average_check_time"] = check_time
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del rate limiter"""
        return {
            **self.metrics,
            "active_identifiers": len(self.metrics["active_identifiers"]),
            "configured_services": len(self.rate_configs),
            "memory_usage": {
                "fixed_windows": len(self.fixed_windows),
                "sliding_windows": len(self.sliding_windows),
                "token_buckets": len(self.token_buckets),
                "adaptive_limits": len(self.adaptive_limits)
            }
        }
    
    async def reset_limits(self, identifier: str, service_name: str, endpoint: str = "*") -> None:
        """Resetear límites para un identificador específico"""
        # Limpiar de todas las estructuras
        keys_to_clean = []
        
        for key in self.fixed_windows:
            if f"{identifier}:{service_name}:{endpoint}" in self.fixed_windows[key]:
                del self.fixed_windows[key][f"{identifier}:{service_name}:{endpoint}"]
        
        limit_key = f"{identifier}:{service_name}:{endpoint}"
        if limit_key in self.sliding_windows:
            del self.sliding_windows[limit_key]
        
        if limit_key in self.token_buckets:
            del self.token_buckets[limit_key]
        
        if limit_key in self.adaptive_limits:
            del self.adaptive_limits[limit_key]
        
        self.metrics["active_identifiers"].discard(identifier)
        
        self.logger.info(f"Rate limits reseteados para {identifier} en {service_name}:{endpoint}")
    
    async def cleanup(self) -> None:
        """Limpiar recursos"""
        if self.redis:
            await self.redis.close()
        
        self.executor.shutdown(wait=True)
        
        self.logger.info("Advanced Rate Limiter limpiado")


class ConnectionPool:
    """Sistema avanzado de connection pooling"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.pools: Dict[str, Any] = {}
        self.active_connections: Dict[str, set] = defaultdict(set)
        self.metrics = {
            "total_connections_created": 0,
            "total_connections_closed": 0,
            "peak_concurrent": 0,
            "average_connection_lifetime": 0.0
        }
    
    async def initialize_pools(self, pool_configs: List[Dict[str, Any]]) -> None:
        """Inicializar pools de conexiones"""
        for config in pool_configs:
            pool_name = config["name"]
            
            try:
                if config["type"] == "http":
                    self.pools[pool_name] = aiohttp.TCPConnector(
                        limit=config.get("max_connections", 100),
                        limit_per_host=config.get("max_connections_per_host", 10),
                        ttl_dns_cache=300,
                        use_dns_cache=True,
                        keepalive_timeout=30,
                        enable_cleanup_closed=True
                    )
                elif config["type"] == "database":
                    # Pool de base de datos (implementación específica)
                    pass
                elif config["type"] == "redis":
                    self.pools[pool_name] = aiohttp.TCPConnector(
                        limit=config.get("max_connections", 50),
                        limit_per_host=config.get("max_connections_per_host", 5)
                    )
                
                self.logger.info(f"Pool de conexiones creado: {pool_name}")
                
            except Exception as e:
                self.logger.error(f"Error creando pool {pool_name}: {e}")
    
    async def get_connection(self, pool_name: str) -> Any:
        """Obtener conexión del pool"""
        if pool_name not in self.pools:
            raise ValueError(f"Pool {pool_name} no existe")
        
        connection_id = f"{pool_name}:{time.time()}:{id(self.pools[pool_name])}"
        self.active_connections[pool_name].add(connection_id)
        
        # Actualizar métricas
        self.metrics["total_connections_created"] += 1
        self.metrics["peak_concurrent"] = max(
            self.metrics["peak_concurrent"],
            len(self.active_connections[pool_name])
        )
        
        return self.pools[pool_name]
    
    async def return_connection(self, pool_name: str, connection: Any) -> None:
        """Retornar conexión al pool"""
        # Actualizar métricas
        self.metrics["total_connections_closed"] += 1
        
        # Limpiar referencias (aiohttp maneja esto automáticamente)
        pass
    
    async def cleanup_pools(self) -> None:
        """Limpiar todos los pools"""
        for pool_name, pool in self.pools.items():
            try:
                if hasattr(pool, 'close'):
                    await pool.close()
                self.logger.info(f"Pool limpiado: {pool_name}")
            except Exception as e:
                self.logger.error(f"Error limpiando pool {pool_name}: {e}")
        
        self.pools.clear()
        self.active_connections.clear()
    
    def get_pool_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de los pools"""
        return {
            **self.metrics,
            "active_pools": len(self.pools),
            "total_active_connections": sum(len(conns) for conns in self.active_connections.values()),
            "pool_details": {
                name: {
                    "active_connections": len(connections),
                    "pool_size": getattr(pool, '_limit', 'unknown') if pool else 'unknown'
                }
                for name, pool in self.pools.items()
                for connections in [self.active_connections[name]]
            }
        }


# Instancia global del rate limiter
rate_limiter: Optional[AdvancedRateLimiter] = None
connection_pool: Optional[ConnectionPool] = None


async def initialize_enterprise_resilience(config: Dict[str, Any]) -> None:
    """Inicializar componentes enterprise de resilencia"""
    global rate_limiter, connection_pool
    
    # Inicializar rate limiter
    rate_limiter = AdvancedRateLimiter(config)
    await rate_limiter.initialize()
    
    # Inicializar connection pool
    connection_pool = ConnectionPool(config)
    
    pool_configs = [
        {
            "name": "http_pool",
            "type": "http",
            "max_connections": 200,
            "max_connections_per_host": 20
        },
        {
            "name": "database_pool", 
            "type": "database",
            "max_connections": 50,
            "max_connections_per_host": 10
        },
        {
            "name": "redis_pool",
            "type": "redis", 
            "max_connections": 100,
            "max_connections_per_host": 10
        }
    ]
    
    await connection_pool.initialize_pools(pool_configs)


async def get_rate_limiter() -> AdvancedRateLimiter:
    """Obtener instancia del rate limiter"""
    if not rate_limiter:
        raise RuntimeError("Rate Limiter no inicializado")
    return rate_limiter


async def get_connection_pool() -> ConnectionPool:
    """Obtener instancia del connection pool"""
    if not connection_pool:
        raise RuntimeError("Connection Pool no inicializado")
    return connection_pool