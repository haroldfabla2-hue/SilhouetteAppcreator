"""
Circuit Breakers y Retry Policies para MCP Core Superior
Implementa patrones de resilencia enterprise con manejo avanzado de fallos
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable, Union, Type
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor
import random
import math


class CircuitBreakerState(Enum):
    """Estados del Circuit Breaker"""
    CLOSED = "closed"       # Normal - permite requests
    OPEN = "open"          # Fallo - bloquea requests
    HALF_OPEN = "half_open" # Recuperación - permite requests limitados


class RetryStrategy(Enum):
    """Estrategias de retry"""
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    EXPONENTIAL_JITTER = "exponential_jitter"
    ADAPTIVE = "adaptive"


@dataclass
class CircuitBreakerConfig:
    """Configuración del Circuit Breaker"""
    failure_threshold: int = 5          # Fallos consecutivos para abrir
    success_threshold: int = 3          # Éxitos consecutivos para cerrar
    timeout_seconds: float = 60.0       # Tiempo en estado OPEN antes de HALF_OPEN
    timeout_duration_seconds: float = 30.0  # Duración del timeout por request
    expected_exceptions: List[Type[Exception]] = field(default_factory=list)
    fallback_function: Optional[Callable] = None
    name: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryConfig:
    """Configuración de retry policies"""
    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0
    jitter: bool = True
    expected_exceptions: List[Type[Exception]] = field(default_factory=list)
    retry_condition: Optional[Callable[[Exception], bool]] = None
    timeout_total: Optional[float] = None
    name: str = "default"


@dataclass
class ServiceCall:
    """Registro de llamada a servicio"""
    timestamp: datetime
    duration: float
    success: bool
    exception: Optional[Exception] = None
    attempt: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


class CircuitBreaker:
    """Circuit Breaker Implementation"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{config.name}")
        
        # Estado del circuit breaker
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self.half_open_start: Optional[datetime] = None
        
        # Métricas
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.blocked_requests = 0
        
        # Historial de llamadas recientes (para cálculos)
        self.recent_calls: List[ServiceCall] = []
        self.max_history_size = 1000
    
    async def call(
        self, 
        func: Callable, 
        *args, 
        **kwargs
    ) -> Any:
        """Ejecutar función con circuit breaker protection"""
        
        # Verificar estado antes de la llamada
        if not self._can_execute():
            self.blocked_requests += 1
            if self.config.fallback_function:
                self.logger.warning(f"Circuit breaker OPEN, usando fallback para {self.config.name}")
                return await self._execute_fallback(*args, **kwargs)
            else:
                raise Exception(f"Circuit breaker is OPEN for {self.config.name}")
        
        self.total_requests += 1
        start_time = time.time()
        
        try:
            # Ejecutar función
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, func, *args, **kwargs
                )
            
            # Registrar éxito
            duration = time.time() - start_time
            self._record_success(duration)
            
            self.successful_requests += 1
            return result
            
        except Exception as e:
            # Registrar fallo
            duration = time.time() - start_time
            self._record_failure(e, duration)
            
            self.failed_requests += 1
            
            # Re-lanzar excepción si no es esperada
            if type(e) not in self.config.expected_exceptions:
                raise
            
            raise
    
    def _can_execute(self) -> bool:
        """Verificar si se puede ejecutar basado en el estado"""
        current_time = datetime.utcnow()
        
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        elif self.state == CircuitBreakerState.OPEN:
            # Verificar si es tiempo de intentar HALF_OPEN
            if self.last_failure_time:
                timeout_duration = timedelta(seconds=self.config.timeout_seconds)
                if current_time - self.last_failure_time > timeout_duration:
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.half_open_start = current_time
                    self.logger.info(f"Circuit breaker {self.config.name} transitioned to HALF_OPEN")
                    return True
            return False
        
        elif self.state == CircuitBreakerState.HALF_OPEN:
            # En HALF_OPEN, permitir una cantidad limitada de requests
            if self.half_open_start:
                timeout_duration = timedelta(seconds=self.config.timeout_duration_seconds)
                if current_time - self.half_open_start > timeout_duration:
                    self.state = CircuitBreakerState.OPEN
                    self.logger.warning(f"Circuit breaker {self.config.name} returned to OPEN from HALF_OPEN")
                    return False
            return True
        
        return False
    
    def _record_success(self, duration: float) -> None:
        """Registrar éxito"""
        current_time = datetime.utcnow()
        
        self.success_count += 1
        self.last_success_time = current_time
        
        # Agregar al historial
        self._add_to_history(ServiceCall(
            timestamp=current_time,
            duration=duration,
            success=True
        ))
        
        # Actualizar estado
        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.logger.info(f"Circuit breaker {self.config.name} closed successfully")
        
        elif self.state == CircuitBreakerState.CLOSED:
            # Reset contador en estado CLOSED
            if self.failure_count > 0:
                self.failure_count = max(0, self.failure_count - 1)
    
    def _record_failure(self, exception: Exception, duration: float) -> None:
        """Registrar fallo"""
        current_time = datetime.utcnow()
        
        self.failure_count += 1
        self.last_failure_time = current_time
        
        # Agregar al historial
        self._add_to_history(ServiceCall(
            timestamp=current_time,
            duration=duration,
            success=False,
            exception=exception
        ))
        
        # Actualizar estado
        if self.state == CircuitBreakerState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                self.logger.warning(f"Circuit breaker {self.config.name} opened due to failures")
        
        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Regresar a OPEN inmediatamente en HALF_OPEN
            self.state = CircuitBreakerState.OPEN
            self.success_count = 0
            self.logger.warning(f"Circuit breaker {self.config.name} returned to OPEN from HALF_OPEN")
    
    def _add_to_history(self, call: ServiceCall) -> None:
        """Agregar llamada al historial"""
        self.recent_calls.append(call)
        
        # Mantener tamaño del historial
        if len(self.recent_calls) > self.max_history_size:
            self.recent_calls.pop(0)
    
    async def _execute_fallback(self, *args, **kwargs) -> Any:
        """Ejecutar función de fallback"""
        if self.config.fallback_function:
            if asyncio.iscoroutinefunction(self.config.fallback_function):
                return await self.config.fallback_function(*args, **kwargs)
            else:
                return await asyncio.get_event_loop().run_in_executor(
                    None, self.config.fallback_function, *args, **kwargs
                )
        else:
            raise Exception("No fallback function configured")
    
    def get_state(self) -> Dict[str, Any]:
        """Obtener estado del circuit breaker"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "metrics": {
                "total_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "blocked_requests": self.blocked_requests,
                "success_rate": self.successful_requests / max(1, self.total_requests)
            }
        }
    
    def reset(self) -> None:
        """Resetear circuit breaker"""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        self.half_open_start = None
        
        self.logger.info(f"Circuit breaker {self.config.name} reset")


class RetryManager:
    """Gestor de retry policies avanzado"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_configs: Dict[str, RetryConfig] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    def register_circuit_breaker(self, name: str, config: CircuitBreakerConfig) -> None:
        """Registrar circuit breaker"""
        self.circuit_breakers[name] = CircuitBreaker(config)
        self.logger.info(f"Circuit breaker registered: {name}")
    
    def register_retry_config(self, name: str, config: RetryConfig) -> None:
        """Registrar configuración de retry"""
        self.retry_configs[name] = config
        self.logger.info(f"Retry config registered: {name}")
    
    async def execute_with_resilience(
        self,
        func: Callable,
        circuit_breaker_name: str,
        retry_config_name: str,
        *args,
        **kwargs
    ) -> Any:
        """Ejecutar función con circuit breaker y retry"""
        
        # Obtener configuraciones
        circuit_breaker = self.circuit_breakers.get(circuit_breaker_name)
        retry_config = self.retry_configs.get(retry_config_name)
        
        if not circuit_breaker:
            raise ValueError(f"Circuit breaker '{circuit_breaker_name}' not found")
        
        if not retry_config:
            raise ValueError(f"Retry config '{retry_config_name}' not found")
        
        # Ejecutar con circuit breaker
        return await circuit_breaker.call(
            self._execute_with_retry,
            func,
            retry_config,
            *args,
            **kwargs
        )
    
    async def _execute_with_retry(
        self,
        func: Callable,
        config: RetryConfig,
        *args,
        **kwargs
    ) -> Any:
        """Ejecutar función con retry policy"""
        last_exception = None
        start_time = time.time()
        
        for attempt in range(config.max_attempts):
            try:
                # Verificar timeout total si está configurado
                if config.timeout_total:
                    elapsed = time.time() - start_time
                    if elapsed >= config.timeout_total:
                        raise TimeoutError(f"Total timeout exceeded after {elapsed:.2f}s")
                
                # Ejecutar función
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = await asyncio.get_event_loop().run_in_executor(
                        self.executor, func, *args, **kwargs
                    )
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Verificar si la excepción es esperada
                should_retry = (
                    type(e) in config.expected_exceptions or
                    (config.retry_condition and config.retry_condition(e))
                )
                
                if not should_retry:
                    self.logger.warning(f"Not retrying for exception: {type(e).__name__}: {e}")
                    raise
                
                # Verificar si es el último intento
                if attempt == config.max_attempts - 1:
                    self.logger.error(f"Max retries ({config.max_attempts}) exceeded for {func.__name__}")
                    raise
                
                # Calcular delay
                delay = self._calculate_delay(config, attempt)
                
                self.logger.warning(
                    f"Attempt {attempt + 1}/{config.max_attempts} failed for {func.__name__}: {e}. "
                    f"Retrying in {delay:.2f}s"
                )
                
                # Esperar antes del siguiente retry
                await asyncio.sleep(delay)
        
        # Si llegamos aquí, todos los retries fallaron
        raise last_exception
    
    def _calculate_delay(self, config: RetryConfig, attempt: int) -> float:
        """Calcular delay para el siguiente retry"""
        if config.strategy == RetryStrategy.FIXED_DELAY:
            delay = config.base_delay
            
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * (attempt + 1)
            
        elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (config.multiplier ** attempt)
            
        elif config.strategy == RetryStrategy.EXPONENTIAL_JITTER:
            base_delay = config.base_delay * (config.multiplier ** attempt)
            jitter = random.uniform(-0.1, 0.1) * base_delay if config.jitter else 0
            delay = base_delay + jitter
            
        elif config.strategy == RetryStrategy.ADAPTIVE:
            # Adaptive retry - ajustar basado en métricas del sistema
            delay = self._calculate_adaptive_delay(config, attempt)
            
        else:
            delay = config.base_delay
        
        # Aplicar límites
        delay = max(0.1, min(config.max_delay, delay))
        
        return delay
    
    def _calculate_adaptive_delay(self, config: RetryConfig, attempt: int) -> float:
        """Calcular delay adaptivo basado en métricas del sistema"""
        # Obtener métricas del sistema
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            
            # Ajustar delay basado en carga del sistema
            system_load = (cpu_percent + memory_percent) / 200  # Normalizar a 0-1
            
            base_delay = config.base_delay * (config.multiplier ** attempt)
            adaptive_factor = 1 + system_load  # Incrementar delay bajo alta carga
            
            delay = base_delay * adaptive_factor
            
            # Aplicar jitter
            if config.jitter:
                jitter_range = delay * 0.2
                jitter = random.uniform(-jitter_range, jitter_range)
                delay += jitter
            
            return delay
            
        except ImportError:
            # Sin psutil, usar exponential backoff
            return config.base_delay * (config.multiplier ** attempt)
    
    def get_circuit_breaker_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de todos los circuit breakers"""
        return {
            name: breaker.get_state()
            for name, breaker in self.circuit_breakers.items()
        }
    
    def get_global_metrics(self) -> Dict[str, Any]:
        """Obtener métricas globales"""
        total_requests = sum(cb.total_requests for cb in self.circuit_breakers.values())
        total_successful = sum(cb.successful_requests for cb in self.circuit_breakers.values())
        total_failed = sum(cb.failed_requests for cb in self.circuit_breakers.values())
        total_blocked = sum(cb.blocked_requests for cb in self.circuit_breakers.values())
        
        return {
            "total_circuit_breakers": len(self.circuit_breakers),
            "circuit_breakers_by_state": self._get_circuit_breaker_state_counts(),
            "global_metrics": {
                "total_requests": total_requests,
                "successful_requests": total_successful,
                "failed_requests": total_failed,
                "blocked_requests": total_blocked,
                "overall_success_rate": total_successful / max(1, total_requests),
                "circuit_breaker_rate": total_blocked / max(1, total_requests)
            }
        }
    
    def _get_circuit_breaker_state_counts(self) -> Dict[str, int]:
        """Contar circuit breakers por estado"""
        counts = {state.value: 0 for state in CircuitBreakerState}
        
        for breaker in self.circuit_breakers.values():
            counts[breaker.state.value] += 1
        
        return counts


# Decorador para aplicar resilience patterns
def with_resilience(
    circuit_breaker_name: str = "default",
    retry_config_name: str = "default"
):
    """Decorador para aplicar circuit breaker y retry policies"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # En implementación real, usar el retry manager
            # Por simplicidad, ejecutar directamente
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Instancia global del retry manager
retry_manager: Optional[RetryManager] = None


async def initialize_enterprise_resilience_system(config: Dict[str, Any]) -> RetryManager:
    """Inicializar sistema enterprise de resilencia"""
    global retry_manager
    
    retry_manager = RetryManager()
    
    # Registrar circuit breakers por defecto
    default_breaker_configs = [
        CircuitBreakerConfig(
            name="database",
            failure_threshold=5,
            timeout_seconds=60.0,
            expected_exceptions=[ConnectionError, TimeoutError]
        ),
        CircuitBreakerConfig(
            name="external_api",
            failure_threshold=3,
            timeout_seconds=30.0,
            expected_exceptions=[ConnectionError, TimeoutError, 404]
        ),
        CircuitBreakerConfig(
            name="redis_cache",
            failure_threshold=10,
            timeout_seconds=30.0,
            expected_exceptions=[ConnectionError]
        )
    ]
    
    for config in default_breaker_configs:
        retry_manager.register_circuit_breaker(config.name, config)
    
    # Registrar configuraciones de retry por defecto
    default_retry_configs = [
        RetryConfig(
            name="default",
            max_attempts=3,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            max_delay=60.0,
            expected_exceptions=[ConnectionError, TimeoutError]
        ),
        RetryConfig(
            name="database",
            max_attempts=5,
            strategy=RetryStrategy.EXPONENTIAL_JITTER,
            base_delay=0.5,
            max_delay=30.0,
            expected_exceptions=[ConnectionError]
        ),
        RetryConfig(
            name="external_api",
            max_attempts=3,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=2.0,
            max_delay=120.0,
            expected_exceptions=[ConnectionError, TimeoutError]
        ),
        RetryConfig(
            name="fast_retry",
            max_attempts=2,
            strategy=RetryStrategy.FIXED_DELAY,
            base_delay=0.1,
            max_delay=1.0
        )
    ]
    
    for config in default_retry_configs:
        retry_manager.register_retry_config(config.name, config)
    
    return retry_manager


async def get_retry_manager() -> RetryManager:
    """Obtener instancia del retry manager"""
    if not retry_manager:
        raise RuntimeError("Retry manager no inicializado. Llamar initialize_enterprise_resilience_system primero.")
    return retry_manager