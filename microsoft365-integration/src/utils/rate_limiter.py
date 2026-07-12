"""
Microsoft 365 - Rate Limiter Utility
Control de velocidad de llamadas a APIs
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import deque
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Limitador de velocidad para APIs con token bucket algorithm"""
    
    def __init__(self, requests_per_minute: int = 100, requests_per_day: int = 10000):
        self.requests_per_minute = requests_per_minute
        self.requests_per_day = requests_per_day
        
        # Token buckets
        self.minute_bucket = TokenBucket(requests_per_minute, 60)
        self.day_bucket = TokenBucket(requests_per_day, 86400)
        
        # Tracking de requests
        self.request_history: Dict[str, List[float]] = {
            'minute': deque(),
            'day': deque()
        }
        
        logger.info(f"Rate limiter initialized: {requests_per_minute}/min, {requests_per_day}/day")
    
    async def acquire(self, tokens: int = 1) -> bool:
        """Adquirir tokens para realizar request"""
        # Verificar tokens en bucket de minuto
        if not self.minute_bucket.consume(tokens):
            logger.warning(f"Rate limit exceeded for minute window")
            return False
        
        # Verificar tokens en bucket de día
        if not self.day_bucket.consume(tokens):
            logger.warning(f"Rate limit exceeded for day window")
            return False
        
        return True
    
    async def wait_for_tokens(self, tokens: int = 1) -> bool:
        """Esperar hasta que haya tokens disponibles"""
        max_wait = 300  # Máximo 5 minutos de espera
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            if await self.acquire(tokens):
                return True
            
            # Calcular tiempo de espera basado en el bucket más restrictivo
            minute_wait = self.minute_bucket.time_until_tokens_available(tokens)
            day_wait = self.day_bucket.time_until_tokens_available(tokens)
            wait_time = max(minute_wait, day_wait, 1.0)  # Mínimo 1 segundo
            
            logger.debug(f"Rate limit reached, waiting {wait_time:.2f} seconds")
            await asyncio.sleep(min(wait_time, 30))  # Esperar máximo 30 segundos por iteración
        
        logger.error("Maximum wait time exceeded for rate limiting")
        return False
    
    def get_remaining_tokens(self) -> Dict[str, int]:
        """Obtener tokens restantes en buckets"""
        return {
            'minute': self.minute_bucket.tokens,
            'day': self.day_bucket.tokens
        }
    
    def get_reset_times(self) -> Dict[str, datetime]:
        """Obtener tiempos de reset de buckets"""
        now = datetime.utcnow()
        return {
            'minute': now + timedelta(seconds=self.minute_bucket.time_to_full()),
            'day': now + timedelta(seconds=self.day_bucket.time_to_full())
        }

class TokenBucket:
    """Implementación de token bucket algorithm"""
    
    def __init__(self, capacity: int, refill_time: int):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_time = refill_time
        self.last_refill = time.time()
        
        logger.debug(f"Token bucket created: capacity={capacity}, refill_time={refill_time}s")
    
    def consume(self, tokens: int) -> bool:
        """Consumir tokens del bucket"""
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def time_until_tokens_available(self, tokens: int) -> float:
        """Calcular tiempo hasta que haya tokens disponibles"""
        self._refill()
        
        if self.tokens >= tokens:
            return 0
        
        tokens_needed = tokens - self.tokens
        time_per_token = self.refill_time / self.capacity
        
        return tokens_needed * time_per_token
    
    def time_to_full(self) -> float:
        """Calcular tiempo hasta que el bucket esté lleno"""
        if self.tokens >= self.capacity:
            return 0
        
        tokens_needed = self.capacity - self.tokens
        time_per_token = self.refill_time / self.capacity
        
        return tokens_needed * time_per_token
    
    def _refill(self):
        """Reabastecer bucket basado en tiempo transcurrido"""
        now = time.time()
        elapsed = now - self.last_refill
        
        if elapsed >= self.refill_time:
            tokens_to_add = int(elapsed / self.refill_time)
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now

class SlidingWindowRateLimiter:
    """Limitador con ventana deslizante"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: deque = deque()
        
        logger.debug(f"Sliding window rate limiter: {max_requests}/{window_seconds}s")
    
    async def acquire(self) -> bool:
        """Verificar si se puede realizar request"""
        now = time.time()
        
        # Remover requests fuera de la ventana
        while self.requests and now - self.requests[0] > self.window_seconds:
            self.requests.popleft()
        
        # Verificar si se puede hacer request
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        
        return False
    
    async def wait_for_slot(self) -> bool:
        """Esperar hasta que haya slot disponible"""
        max_wait = 300  # 5 minutos
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            if await self.acquire():
                return True
            
            # Calcular tiempo hasta que el request más antiguo expire
            if self.requests:
                oldest_request = self.requests[0]
                wait_time = self.window_seconds - (time.time() - oldest_request)
                wait_time = max(wait_time, 1.0)
            else:
                wait_time = 1.0
            
            await asyncio.sleep(min(wait_time, 30))
        
        logger.error("Maximum wait time exceeded for sliding window rate limit")
        return False

class LeakyBucketRateLimiter:
    """Limitador de bucket con fugas"""
    
    def __init__(self, capacity: int, leak_rate: float):
        self.capacity = capacity
        self.leak_rate = leak_rate  # requests per second
        self.current_level = 0
        self.last_leak = time.time()
        
        logger.debug(f"Leaky bucket rate limiter: capacity={capacity}, rate={leak_rate}/s")
    
    async def acquire(self) -> bool:
        """Intentar agregar request al bucket"""
        self._leak()
        
        if self.current_level < self.capacity:
            self.current_level += 1
            return True
        
        return False
    
    async def wait_for_capacity(self) -> bool:
        """Esperar hasta que haya capacidad disponible"""
        max_wait = 300  # 5 minutos
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            if await self.acquire():
                return True
            
            # Calcular tiempo hasta que se libere capacidad
            self._leak()
            if self.current_level >= self.capacity:
                wait_time = 1.0 / self.leak_rate  # Tiempo para liberar 1 request
            else:
                wait_time = 1.0
            
            await asyncio.sleep(min(wait_time, 30))
        
        logger.error("Maximum wait time exceeded for leaky bucket rate limit")
        return False
    
    def _leak(self):
        """Liberar requests del bucket basado en la tasa de fuga"""
        now = time.time()
        elapsed = now - self.last_leak
        
        # Calcular cuántos requests deben liberarse
        leaked_amount = elapsed * self.leak_rate
        self.current_level = max(0, self.current_level - leaked_amount)
        
        self.last_leak = now

class PriorityRateLimiter:
    """Limitador con prioridades de requests"""
    
    def __init__(self, base_rate: int, priority_boost: Dict[str, int]):
        self.base_rate = base_rate
        self.priority_boost = priority_boost
        
        # Buckets por prioridad
        self.priority_buckets: Dict[str, TokenBucket] = {}
        for priority in priority_boost.keys():
            boost = priority_boost[priority]
            bucket_capacity = base_rate + boost
            self.priority_buckets[priority] = TokenBucket(bucket_capacity, 60)
        
        logger.info(f"Priority rate limiter created with boosts: {priority_boost}")
    
    async def acquire(self, priority: str = "normal") -> bool:
        """Adquirir token basado en prioridad"""
        if priority not in self.priority_buckets:
            priority = "normal"
        
        bucket = self.priority_buckets[priority]
        return bucket.consume(1)
    
    async def wait_for_priority_slot(self, priority: str = "normal") -> bool:
        """Esperar slot basado en prioridad"""
        max_wait = 300
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            if await self.acquire(priority):
                return True
            
            bucket = self.priority_buckets.get(priority)
            if bucket:
                wait_time = bucket.time_until_tokens_available(1)
            else:
                wait_time = 1.0
            
            await asyncio.sleep(min(wait_time, 30))
        
        logger.error(f"Maximum wait time exceeded for priority {priority}")
        return False

class RateLimitMonitor:
    """Monitor para tracking de uso de rate limits"""
    
    def __init__(self):
        self.request_counts: Dict[str, Dict[str, int]] = {
            'minute': {},
            'hour': {},
            'day': {}
        }
        self.error_counts: Dict[str, int] = {}
        self.start_time = time.time()
        
        logger.info("Rate limit monitor initialized")
    
    def record_request(self, endpoint: str, status_code: Optional[int] = None):
        """Registrar request"""
        now = time.time()
        minute = int(now // 60)
        hour = int(now // 3600)
        day = int(now // 86400)
        
        # Incrementar contadores
        self.request_counts['minute'][endpoint] = self.request_counts['minute'].get(endpoint, 0) + 1
        self.request_counts['hour'][endpoint] = self.request_counts['hour'].get(endpoint, 0) + 1
        self.request_counts['day'][endpoint] = self.request_counts['day'].get(endpoint, 0) + 1
        
        # Contar errores
        if status_code and status_code >= 400:
            self.error_counts[endpoint] = self.error_counts.get(endpoint, 0) + 1
    
    def get_usage_stats(self, time_window: str = 'minute') -> Dict[str, Any]:
        """Obtener estadísticas de uso"""
        if time_window not in self.request_counts:
            return {}
        
        total_requests = sum(self.request_counts[time_window].values())
        unique_endpoints = len(self.request_counts[time_window])
        total_errors = sum(self.error_counts.values())
        
        return {
            'time_window': time_window,
            'total_requests': total_requests,
            'unique_endpoints': unique_endpoints,
            'total_errors': total_errors,
            'error_rate': (total_errors / total_requests * 100) if total_requests > 0 else 0,
            'endpoint_breakdown': self.request_counts[time_window],
            'monitoring_duration': time.time() - self.start_time
        }
    
    def reset_stats(self):
        """Resetear estadísticas"""
        self.request_counts = {
            'minute': {},
            'hour': {},
            'day': {}
        }
        self.error_counts = {}
        self.start_time = time.time()
        
        logger.info("Rate limit monitor statistics reset")

# Configuraciones predefinidas
RATE_LIMIT_CONFIGS = {
    'graph_api': RateLimiter(requests_per_minute=100, requests_per_day=10000),
    'word_api': RateLimiter(requests_per_minute=50, requests_per_day=5000),
    'excel_api': RateLimiter(requests_per_minute=30, requests_per_day=3000),
    'powerpoint_api': RateLimiter(requests_per_minute=25, requests_per_day=2500),
    'outlook_api': RateLimiter(requests_per_minute=75, requests_per_day=7500),
    'onedrive_api': RateLimiter(requests_per_minute=60, requests_per_day=6000),
    'teams_api': RateLimiter(requests_per_minute=40, requests_per_day=4000),
    'default': RateLimiter(requests_per_minute=100, requests_per_day=10000)
}

def get_rate_limiter(service: str = 'default') -> RateLimiter:
    """Obtener rate limiter preconfigurado"""
    return RATE_LIMIT_CONFIGS.get(service, RATE_LIMIT_CONFIGS['default'])