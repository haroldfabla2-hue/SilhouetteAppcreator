"""
Microsoft 365 - Retry Handler Utility
Manejo inteligente de reintentos para operaciones
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Callable, Any, Optional, List, Dict
from functools import wraps

logger = logging.getLogger(__name__)

class RetryError(Exception):
    """Excepción para errores de reintento"""
    pass

class RetryHandler:
    """Manejador de reintentos con estrategias configurables"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, exponential_base: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.exponential_base = exponential_base
        
        # Errores que permiten reintento
        self.retryable_errors = [
            'timeout',
            'connection',
            'rate_limit',
            'server_error',
            'temporary_failure'
        ]
        
        # Errores que NO permiten reintento
        self.non_retryable_errors = [
            'authentication',
            'authorization',
            'validation',
            'not_found',
            'conflict'
        ]
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determinar si se debe reintentar basado en el error y el intento"""
        if attempt >= self.max_retries:
            return False
        
        error_message = str(error).lower()
        error_type = str(type(error).__name__).lower()
        
        # Verificar errores que permiten reintento
        for retry_error in self.retryable_errors:
            if retry_error in error_message or retry_error in error_type:
                return True
        
        # Verificar errores que NO permiten reintento
        for non_retry_error in self.non_retryable_errors:
            if non_retry_error in error_message or non_retry_error in error_type:
                return False
        
        # Por defecto, permitir reintento para errores de red/conexión
        return any(keyword in error_message for keyword in [
            'network', 'connection', 'timeout', 'temporary', 'server error'
        ])
    
    def calculate_delay(self, attempt: int) -> float:
        """Calcular delay para el siguiente intento"""
        if attempt == 0:
            return 0
        
        # Delay exponencial con jitter
        delay = self.base_delay * (self.exponential_base ** attempt)
        
        # Agregar jitter aleatorio para evitar thundering herd
        import random
        jitter = random.uniform(0.1, 0.9)
        final_delay = delay * jitter
        
        return min(final_delay, 60)  # Máximo 60 segundos
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        retry_on: Optional[List[type]] = None,
        **kwargs
    ) -> Any:
        """Ejecutar función con reintentos automáticos"""
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"Operation succeeded on attempt {attempt + 1}")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Verificar si es un tipo de error específico para reintentar
                if retry_on and type(e) not in retry_on:
                    logger.error(f"Non-retryable error: {type(e).__name__}: {str(e)}")
                    raise e
                
                # Verificar si debe reintentar
                if not self.should_retry(e, attempt):
                    logger.error(f"Max retries reached for error: {type(e).__name__}: {str(e)}")
                    raise e
                
                # Calcular delay
                delay = self.calculate_delay(attempt)
                
                logger.warning(
                    f"Attempt {attempt + 1} failed: {type(e).__name__}: {str(e)}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
                
                # Esperar antes del siguiente intento
                await asyncio.sleep(delay)
        
        # Si llegamos aquí, todos los intentos fallaron
        raise last_exception
    
    def retry_async(
        self,
        retry_on: Optional[List[type]] = None
    ):
        """Decorador para funciones asíncronas"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await self.execute_with_retry(func, *args, retry_on=retry_on, **kwargs)
            return wrapper
        return decorator
    
    def retry_sync(
        self,
        retry_on: Optional[List[type]] = None
    ):
        """Decorador para funciones síncronas"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Convertir a async para usar el método central
                async def async_func():
                    return func(*args, **kwargs)
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(
                        self.execute_with_retry(async_func, retry_on=retry_on)
                    )
                finally:
                    loop.close()
            return wrapper
        return decorator

class CircuitBreaker:
    """Circuit breaker para prevenir llamadas repetidas a servicios fallidos"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        
        logger.info(f"Circuit breaker initialized: threshold={failure_threshold}, timeout={recovery_timeout}s")
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Ejecutar función con protección de circuit breaker"""
        
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                logger.info("Circuit breaker moving to HALF_OPEN state")
                self.state = 'HALF_OPEN'
            else:
                raise RetryError("Circuit breaker is OPEN")
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Verificar si se debe intentar resetear el circuit breaker"""
        if self.last_failure_time is None:
            return True
        
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.recovery_timeout
    
    def _on_success(self):
        """Manejar éxito de operación"""
        if self.state != 'CLOSED':
            logger.info("Circuit breaker resetting to CLOSED state")
        
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        """Manejar falla de operación"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            logger.warning(f"Circuit breaker OPENED after {self.failure_count} failures")
        else:
            logger.warning(f"Circuit breaker failure count: {self.failure_count}/{self.failure_threshold}")

class ExponentialBackoff:
    """Utilidad para backoff exponencial personalizable"""
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0, factor: float = 2.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.factor = factor
    
    def calculate_delay(self, attempt: int) -> float:
        """Calcular delay exponencial"""
        delay = self.base_delay * (self.factor ** attempt)
        return min(delay, self.max_delay)

class LinearBackoff:
    """Utilidad para backoff lineal"""
    
    def __init__(self, base_delay: float = 1.0, increment: float = 1.0, max_delay: float = 60.0):
        self.base_delay = base_delay
        self.increment = increment
        self.max_delay = max_delay
    
    def calculate_delay(self, attempt: int) -> float:
        """Calcular delay lineal"""
        delay = self.base_delay + (attempt * self.increment)
        return min(delay, self.max_delay)

class JitterBackoff:
    """Utilidad para backoff con jitter aleatorio"""
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter_range = 0.1  # 10% de jitter
    
    def calculate_delay(self, attempt: int) -> float:
        """Calcular delay con jitter"""
        import random
        base = self.base_delay * (2 ** attempt)  # Exponential base
        jitter = base * self.jitter_range * random.uniform(-1, 1)
        delay = base + jitter
        return max(0.1, min(delay, self.max_delay))

# Configuraciones predefinidas para diferentes servicios
RETRY_CONFIGS = {
    'graph_api': RetryHandler(max_retries=3, base_delay=1.0),
    'file_upload': RetryHandler(max_retries=5, base_delay=2.0),
    'email_send': RetryHandler(max_retries=2, base_delay=3.0),
    'teams_api': RetryHandler(max_retries=4, base_delay=1.5),
    'default': RetryHandler(max_retries=3, base_delay=1.0)
}

def get_retry_handler(service_type: str = 'default') -> RetryHandler:
    """Obtener configuración de retry predefinida"""
    return RETRY_CONFIGS.get(service_type, RETRY_CONFIGS['default'])