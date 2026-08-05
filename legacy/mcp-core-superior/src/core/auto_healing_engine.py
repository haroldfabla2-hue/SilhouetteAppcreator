"""
Advanced Auto-Healing Engine para MCP Core Superior
Implementa sistema completo de recuperación automática y manejo inteligente de errores
"""
import asyncio
import logging
import time
import numpy as np
import json
from typing import Dict, Any, List, Optional, Set, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor
import psutil
import weakref

from .config import settings, Environment
from .exceptions import (
    MCPCoreException, 
    AgentException, 
    AgentNotAvailableException,
    ErrorCode
)

# ==================== ENUMS Y DATA CLASSES ====================

class HealthStatus(Enum):
    """Estados de salud del sistema"""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    CRITICAL = "critical"
    RECOVERING = "recovering"
    FAILED = "failed"

class CircuitState(Enum):
    """Estados del circuit breaker"""
    CLOSED = "closed"     # Normal operation
    OPEN = "open"         # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery

class ScalingAction(Enum):
    """Acciones de escalado automático"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    SCALE_IN = "scale_in"
    SCALE_OUT = "scale_out"
    NO_ACTION = "no_action"

class RecoveryStrategy(Enum):
    """Estrategias de recuperación"""
    RESTART_AGENT = "restart_agent"
    RESTART_SERVICE = "restart_service"
    FALLBACK_TO_BACKUP = "fallback_to_backup"
    CIRCUIT_BREAKER = "circuit_breaker"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    ESCALATE = "escalate"

@dataclass
class HealthMetrics:
    """Métricas de salud del sistema"""
    timestamp: datetime
    agent_name: str
    cpu_usage: float
    memory_usage: float
    response_time: float
    error_rate: float
    throughput: float
    active_tasks: int
    queue_size: int
    health_score: float

@dataclass
class ErrorEvent:
    """Evento de error detectado"""
    timestamp: datetime
    error_type: str
    severity: str
    source: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None

@dataclass
class CircuitBreakerConfig:
    """Configuración del circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    expected_exception: type = Exception
    fallback_function: Optional[Callable] = None

@dataclass
class AutoScalingConfig:
    """Configuración de auto-scaling"""
    min_instances: int = 1
    max_instances: int = 10
    target_cpu_usage: float = 70.0
    target_memory_usage: float = 80.0
    scaling_cooldown: int = 300  # seconds
    metrics_window: int = 60  # seconds

# ==================== CIRCUIT BREAKER PATTERN ====================

class CircuitBreaker:
    """Implementación del patrón Circuit Breaker para prevenir cascadas de fallos"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.success_count = 0
        self.lock = threading.Lock()
        self.logger = logging.getLogger("mcp.core.circuit_breaker")
    
    def call(self, func: Callable, *args, **kwargs):
        """Ejecutar función con circuit breaker protection"""
        with self.lock:
            if self._should_attempt_call():
                try:
                    result = func(*args, **kwargs)
                    self._on_success()
                    return result
                except self.config.expected_exception as e:
                    self._on_failure()
                    raise e
            else:
                # Circuit is open, call fallback if available
                if self.config.fallback_function:
                    self.logger.warning(f"Circuit breaker OPEN, calling fallback for {func.__name__}")
                    return self.config.fallback_function(*args, **kwargs)
                else:
                    raise AgentNotAvailableException(
                        agent_name="circuit_breaker",
                        operation="call"
                    )
    
    def _should_attempt_call(self) -> bool:
        """Verificar si se debe intentar la llamada"""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.logger.info("Circuit breaker transitioning to HALF_OPEN")
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def _should_attempt_reset(self) -> bool:
        """Verificar si es tiempo de intentar reset"""
        if self.last_failure_time is None:
            return False
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.config.recovery_timeout
    
    def _on_success(self):
        """Manejar éxito"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 2:  # Need 2 successes to close
                self._reset()
        else:
            self.success_count = 0
    
    def _on_failure(self):
        """Manejar fallo"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.logger.warning("Circuit breaker transitioning to OPEN from HALF_OPEN")
        elif self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            self.logger.warning(f"Circuit breaker transitioning to OPEN after {self.failure_count} failures")
    
    def _reset(self):
        """Reset circuit breaker"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.logger.info("Circuit breaker reset to CLOSED")
    
    def get_state(self) -> Dict[str, Any]:
        """Obtener estado del circuit breaker"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None
        }

# ==================== PREDICTIVE FAILURE DETECTION ====================

class PredictiveFailureDetector:
    """Detector de fallos predictivo usando análisis de métricas"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.anomaly_thresholds = {
            "cpu_usage": 90.0,
            "memory_usage": 95.0,
            "response_time": 2.0,  # seconds
            "error_rate": 0.1,  # 10%
            "health_score": 0.5
        }
        self.logger = logging.getLogger("mcp.core.failure_detector")
    
    def record_metrics(self, agent_name: str, metrics: HealthMetrics):
        """Registrar métricas para análisis predictivo"""
        self.metrics_history[agent_name].append(metrics)
    
    def predict_failure_probability(self, agent_name: str) -> float:
        """Predecir probabilidad de fallo (0.0 - 1.0)"""
        if agent_name not in self.metrics_history:
            return 0.0
        
        metrics_window = list(self.metrics_history[agent_name])
        if len(metrics_window) < 10:
            return 0.0
        
        # Calcular scores de riesgo para diferentes métricas
        risk_scores = self._calculate_risk_scores(metrics_window)
        
        # Combinar scores usando weighted average
        weights = {
            "cpu_risk": 0.2,
            "memory_risk": 0.2,
            "response_time_risk": 0.3,
            "error_rate_risk": 0.2,
            "health_score_risk": 0.1
        }
        
        combined_risk = sum(risk_scores[key] * weights[key] for key in weights)
        return min(1.0, max(0.0, combined_risk))
    
    def _calculate_risk_scores(self, metrics_window: List[HealthMetrics]) -> Dict[str, float]:
        """Calcular scores de riesgo para diferentes métricas"""
        if len(metrics_window) < 5:
            return {key: 0.0 for key in ["cpu_risk", "memory_risk", "response_time_risk", "error_rate_risk", "health_score_risk"]}
        
        # Extraer arrays de métricas
        cpu_values = [m.cpu_usage for m in metrics_window]
        memory_values = [m.memory_usage for m in metrics_window]
        response_times = [m.response_time for m in metrics_window]
        error_rates = [m.error_rate for m in metrics_window]
        health_scores = [m.health_score for m in metrics_window]
        
        return {
            "cpu_risk": self._calculate_trend_risk(cpu_values, self.anomaly_thresholds["cpu_usage"]),
            "memory_risk": self._calculate_trend_risk(memory_values, self.anomaly_thresholds["memory_usage"]),
            "response_time_risk": self._calculate_trend_risk(response_times, self.anomaly_thresholds["response_time"]),
            "error_rate_risk": self._calculate_trend_risk(error_rates, self.anomaly_thresholds["error_rate"]),
            "health_score_risk": 1.0 - np.mean(health_scores)  # Lower health = higher risk
        }
    
    def _calculate_trend_risk(self, values: List[float], threshold: float) -> float:
        """Calcular riesgo basado en tendencia y umbrales"""
        if not values:
            return 0.0
        
        # Calcular tendencia (slope)
        x = np.arange(len(values))
        if len(values) > 1:
            slope = np.polyfit(x, values, 1)[0]
        else:
            slope = 0.0
        
        # Risk based on average value and trend
        avg_value = np.mean(values)
        trend_factor = max(0, slope)  # Only increasing trends are risky
        
        # Base risk from average
        base_risk = max(0, (avg_value - threshold * 0.8) / (threshold * 0.2))
        
        # Adjust for trend
        trend_multiplier = 1 + (trend_factor * 10)
        
        return min(1.0, base_risk * trend_multiplier)
    
    def detect_anomalies(self, agent_name: str) -> List[Dict[str, Any]]:
        """Detectar anomalías en métricas recientes"""
        if agent_name not in self.metrics_history:
            return []
        
        recent_metrics = list(self.metrics_history[agent_name])[-10:]
        anomalies = []
        
        if len(recent_metrics) < 3:
            return anomalies
        
        for metric in recent_metrics:
            metric_anomalies = []
            
            # Check each metric against statistical thresholds
            if metric.cpu_usage > self.anomaly_thresholds["cpu_usage"]:
                metric_anomalies.append(f"CPU usage critical: {metric.cpu_usage:.1f}%")
            
            if metric.memory_usage > self.anomaly_thresholds["memory_usage"]:
                metric_anomalies.append(f"Memory usage critical: {metric.memory_usage:.1f}%")
            
            if metric.response_time > self.anomaly_thresholds["response_time"]:
                metric_anomalies.append(f"Response time high: {metric.response_time:.2f}s")
            
            if metric.error_rate > self.anomaly_thresholds["error_rate"]:
                metric_anomalies.append(f"Error rate high: {metric.error_rate:.1%}")
            
            if metric.health_score < self.anomaly_thresholds["health_score"]:
                metric_anomalies.append(f"Health score low: {metric.health_score:.2f}")
            
            if metric_anomalies:
                anomalies.append({
                    "timestamp": metric.timestamp.isoformat(),
                    "agent_name": agent_name,
                    "anomalies": metric_anomalies,
                    "metrics": {
                        "cpu": metric.cpu_usage,
                        "memory": metric.memory_usage,
                        "response_time": metric.response_time,
                        "error_rate": metric.error_rate,
                        "health_score": metric.health_score
                    }
                })
        
        return anomalies

# ==================== AUTO-HEALING ENGINE PRINCIPAL ====================

class AutoHealingEngine:
    """Motor principal de auto-healing y recuperación automática"""
    
    def __init__(self):
        self.logger = logging.getLogger("mcp.core.auto_healing")
        
        # Configuración
        self.config = AutoScalingConfig()
        
        # Componentes del sistema
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.failure_detector = PredictiveFailureDetector()
        
        # Estado del sistema
        self.agent_health: Dict[str, HealthStatus] = {}
        self.agent_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=200))
        self.error_history: deque = deque(maxlen=1000)
        self.recovery_strategies: Dict[str, RecoveryStrategy] = {}
        
        # Auto-scaling
        self.agent_instances: Dict[str, int] = {}
        self.last_scaling_action: Dict[str, datetime] = {}
        
        # Control de ejecución
        self.is_running = False
        self._tasks: Set[asyncio.Task] = set()
        self._lock = asyncio.Lock()
        
        # Callbacks para integración externa
        self.health_change_callbacks: List[Callable] = []
        self.recovery_callbacks: List[Callable] = []
        self.scaling_callbacks: List[Callable] = []
        
        # Estadísticas
        self.stats = {
            "total_recoveries": 0,
            "successful_recoveries": 0,
            "circuit_breaker_activations": 0,
            "auto_scaling_events": 0,
            "anomalies_detected": 0
        }
    
    async def initialize(self):
        """Inicializar el motor de auto-healing"""
        self.logger.info("Inicializando AutoHealingEngine...")
        
        # Inicializar circuit breakers para todos los agentes
        agent_names = [
            "reasoner", "planner", "executor", "verifier", 
            "memory_manager", "orchestrator", "streaming"
        ]
        
        for agent_name in agent_names:
            self._setup_circuit_breaker(agent_name)
            self.agent_health[agent_name] = HealthStatus.HEALTHY
            self.agent_instances[agent_name] = 1
            self.last_scaling_action[agent_name] = datetime.now()
        
        # Iniciar tareas de monitoreo
        self.is_running = True
        self._tasks.add(asyncio.create_task(self._health_monitoring_loop()))
        self._tasks.add(asyncio.create_task(self._error_analysis_loop()))
        self._tasks.add(asyncio.create_task(self._auto_scaling_loop()))
        self._tasks.add(asyncio.create_task(self._predictive_analysis_loop()))
        
        self.logger.info("AutoHealingEngine inicializado exitosamente")
    
    def _setup_circuit_breaker(self, agent_name: str):
        """Configurar circuit breaker para un agente"""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=Exception,
            fallback_function=lambda *args, **kwargs: self._get_fallback_response(agent_name, *args, **kwargs)
        )
        
        self.circuit_breakers[agent_name] = CircuitBreaker(config)
    
    def _get_fallback_response(self, agent_name: str, *args, **kwargs):
        """Obtener respuesta de fallback para un agente"""
        # Lógica de fallback específica por agente
        fallback_strategies = {
            "reasoner": {"status": "fallback", "message": "Reasoner temporarily unavailable"},
            "planner": {"status": "fallback", "message": "Planner using simplified planning"},
            "executor": {"status": "degraded", "message": "Executor running in limited mode"},
            "verifier": {"status": "warning", "message": "Verification using basic checks"},
            "memory_manager": {"status": "cache_only", "message": "Using cache-only memory"}
        }
        
        return fallback_strategies.get(agent_name, {"status": "fallback", "message": f"{agent_name} unavailable"})
    
    async def record_error(self, error_event: ErrorEvent):
        """Registrar evento de error para análisis"""
        self.error_history.append(error_event)
        
        # Notificar circuit breaker si aplica
        if error_event.source in self.circuit_breakers:
            try:
                self.circuit_breakers[error_event.source]._on_failure()
            except Exception as e:
                self.logger.error(f"Error updating circuit breaker: {e}")
    
    async def record_health_metrics(self, agent_name: str, metrics: HealthMetrics):
        """Registrar métricas de salud"""
        self.agent_metrics[agent_name].append(metrics)
        self.failure_detector.record_metrics(agent_name, metrics)
        
        # Actualizar estado de salud
        await self._update_agent_health(agent_name, metrics)
    
    async def _update_agent_health(self, agent_name: str, metrics: HealthMetrics):
        """Actualizar estado de salud de un agente"""
        previous_health = self.agent_health.get(agent_name, HealthStatus.HEALTHY)
        
        # Calcular nuevo estado basado en métricas
        if metrics.health_score >= 0.8:
            new_health = HealthStatus.HEALTHY
        elif metrics.health_score >= 0.6:
            new_health = HealthStatus.DEGRADED
        elif metrics.health_score >= 0.4:
            new_health = HealthStatus.CRITICAL
        else:
            new_health = HealthStatus.FAILED
        
        # Verificar si el estado cambió
        if new_health != previous_health:
            self.agent_health[agent_name] = new_health
            self.logger.warning(f"Agent {agent_name} health changed: {previous_health.value} -> {new_health.value}")
            
            # Notificar callbacks
            for callback in self.health_change_callbacks:
                try:
                    await callback(agent_name, previous_health, new_health, metrics)
                except Exception as e:
                    self.logger.error(f"Error in health change callback: {e}")
            
            # Iniciar recuperación si es necesario
            if new_health in [HealthStatus.CRITICAL, HealthStatus.FAILED]:
                await self._initiate_recovery(agent_name, new_health)
    
    async def _initiate_recovery(self, agent_name: str, health_status: HealthStatus):
        """Iniciar proceso de recuperación para un agente"""
        self.logger.info(f"Iniciando recuperación para agente {agent_name} con estado {health_status.value}")
        
        # Determinar estrategia de recuperación
        strategy = await self._determine_recovery_strategy(agent_name, health_status)
        
        try:
            success = await self._execute_recovery_strategy(agent_name, strategy)
            
            if success:
                self.stats["successful_recoveries"] += 1
                self.logger.info(f"Recuperación exitosa para {agent_name} usando estrategia {strategy.value}")
                
                # Notificar callbacks de recuperación exitosa
                for callback in self.recovery_callbacks:
                    try:
                        await callback(agent_name, strategy, "success")
                    except Exception as e:
                        self.logger.error(f"Error in recovery callback: {e}")
            else:
                self.logger.error(f"Recuperación fallida para {agent_name} usando estrategia {strategy.value}")
                
                # Intentar siguiente estrategia si está disponible
                await self._try_fallback_recovery(agent_name)
                
        except Exception as e:
            self.logger.error(f"Error durante recuperación de {agent_name}: {e}")
        
        self.stats["total_recoveries"] += 1
    
    async def _determine_recovery_strategy(self, agent_name: str, health_status: HealthStatus) -> RecoveryStrategy:
        """Determinar la mejor estrategia de recuperación"""
        # Obtener probabilidad de fallo
        failure_probability = self.failure_detector.predict_failure_probability(agent_name)
        
        # Historial de errores para este agente
        agent_errors = [e for e in self.error_history if e.source == agent_name]
        recent_errors = [e for e in agent_errors if (datetime.now() - e.timestamp).seconds < 300]
        
        # Lógica de decisión basada en contexto
        if health_status == HealthStatus.FAILED:
            if failure_probability > 0.8:
                return RecoveryStrategy.CIRCUIT_BREAKER
            else:
                return RecoveryStrategy.RESTART_AGENT
        
        elif health_status == HealthStatus.CRITICAL:
            if len(recent_errors) > 5:
                return RecoveryStrategy.FALLBACK_TO_BACKUP
            elif failure_probability > 0.6:
                return RecoveryStrategy.GRACEFUL_DEGRADATION
            else:
                return RecoveryStrategy.RESTART_SERVICE
        
        else:  # DEGRADED
            return RecoveryStrategy.GRACEFUL_DEGRADATION
    
    async def _execute_recovery_strategy(self, agent_name: str, strategy: RecoveryStrategy) -> bool:
        """Ejecutar estrategia de recuperación"""
        try:
            if strategy == RecoveryStrategy.RESTART_AGENT:
                return await self._restart_agent(agent_name)
            
            elif strategy == RecoveryStrategy.RESTART_SERVICE:
                return await self._restart_service(agent_name)
            
            elif strategy == RecoveryStrategy.FALLBACK_TO_BACKUP:
                return await self._activate_fallback(agent_name)
            
            elif strategy == RecoveryStrategy.CIRCUIT_BREAKER:
                return await self._activate_circuit_breaker(agent_name)
            
            elif strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
                return await self._apply_graceful_degradation(agent_name)
            
            elif strategy == RecoveryStrategy.ESCALATE:
                return await self._escalate_issue(agent_name)
            
            else:
                self.logger.warning(f"Unknown recovery strategy: {strategy}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing recovery strategy {strategy} for {agent_name}: {e}")
            return False
    
    async def _restart_agent(self, agent_name: str) -> bool:
        """Reiniciar agente específico"""
        try:
            self.logger.info(f"Reiniciando agente {agent_name}")
            
            # Marcar como recovering
            self.agent_health[agent_name] = HealthStatus.RECOVERING
            
            # Simular reinicio del agente
            # En implementación real, esto llamaría a métodos específicos del agente
            await asyncio.sleep(2)  # Simular tiempo de reinicio
            
            # Verificar salud después del reinicio
            # En implementación real, se haría un health check real
            self.agent_health[agent_name] = HealthStatus.HEALTHY
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error restarting agent {agent_name}: {e}")
            self.agent_health[agent_name] = HealthStatus.FAILED
            return False
    
    async def _restart_service(self, agent_name: str) -> bool:
        """Reiniciar servicio completo"""
        try:
            self.logger.info(f"Reiniciando servicio {agent_name}")
            
            self.agent_health[agent_name] = HealthStatus.RECOVERING
            
            # Reinicio más complejo, potencialmente incluyendo dependencias
            await asyncio.sleep(5)  # Simular tiempo de reinicio del servicio
            
            # Verificar salud del servicio
            self.agent_health[agent_name] = HealthStatus.HEALTHY
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error restarting service {agent_name}: {e}")
            self.agent_health[agent_name] = HealthStatus.FAILED
            return False
    
    async def _activate_fallback(self, agent_name: str) -> bool:
        """Activar fallback para agente"""
        try:
            self.logger.info(f"Activando fallback para agente {agent_name}")
            
            # Simular activación de sistema de respaldo
            await asyncio.sleep(1)
            
            # Cambiar a modo degradado pero funcional
            self.agent_health[agent_name] = HealthStatus.DEGRADED
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error activating fallback for {agent_name}: {e}")
            return False
    
    async def _activate_circuit_breaker(self, agent_name: str) -> bool:
        """Activar circuit breaker para agente"""
        try:
            if agent_name in self.circuit_breakers:
                # Forzar circuit breaker a OPEN
                self.circuit_breakers[agent_name].state = CircuitState.OPEN
                self.stats["circuit_breaker_activations"] += 1
                
                self.logger.info(f"Circuit breaker activated for {agent_name}")
                return True
            else:
                self.logger.error(f"No circuit breaker configured for {agent_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error activating circuit breaker for {agent_name}: {e}")
            return False
    
    async def _apply_graceful_degradation(self, agent_name: str) -> bool:
        """Aplicar degradación elegante"""
        try:
            self.logger.info(f"Aplicando degradación elegante para agente {agent_name}")
            
            # Reducir capacidad del agente
            current_instances = self.agent_instances.get(agent_name, 1)
            self.agent_instances[agent_name] = max(1, current_instances // 2)
            
            # Ajustar configuración para operación degradada
            await self._adjust_configuration_for_degradation(agent_name)
            
            self.agent_health[agent_name] = HealthStatus.DEGRADED
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying graceful degradation for {agent_name}: {e}")
            return False
    
    async def _adjust_configuration_for_degradation(self, agent_name: str):
        """Ajustar configuración para operación degradada"""
        # Ajustes específicos por agente
        degradation_configs = {
            "executor": {
                "max_concurrent_tasks": max(1, settings.max_concurrent_tasks // 2),
                "timeout_seconds": settings.default_timeout_seconds * 2
            },
            "planner": {
                "parallel_agents": False,
                "max_depth": 3
            },
            "reasoner": {
                "max_iterations": 5,
                "timeout_seconds": 30
            }
        }
        
        if agent_name in degradation_configs:
            # En implementación real, actualizaríamos la configuración activa
            self.logger.info(f"Ajustando configuración degradada para {agent_name}: {degradation_configs[agent_name]}")
    
    async def _escalate_issue(self, agent_name: str) -> bool:
        """Escalar problema a nivel superior"""
        try:
            self.logger.critical(f"Escalando problema crítico para agente {agent_name}")
            
            # En implementación real, esto enviaría alertas, abriría tickets, etc.
            await asyncio.sleep(1)
            
            # Cambiar estado a crítico y mantenerlo
            self.agent_health[agent_name] = HealthStatus.CRITICAL
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error escalating issue for {agent_name}: {e}")
            return False
    
    async def _try_fallback_recovery(self, agent_name: str):
        """Intentar estrategia de recuperación de respaldo"""
        fallback_strategies = [
            RecoveryStrategy.GRACEFUL_DEGRADATION,
            RecoveryStrategy.FALLBACK_TO_BACKUP,
            RecoveryStrategy.CIRCUIT_BREAKER
        ]
        
        for strategy in fallback_strategies:
            try:
                self.logger.info(f"Intentando estrategia fallback {strategy.value} para {agent_name}")
                success = await self._execute_recovery_strategy(agent_name, strategy)
                if success:
                    return
            except Exception as e:
                self.logger.error(f"Estrategia fallback {strategy.value} falló para {agent_name}: {e}")
        
        # Si todas fallan, dejar en estado crítico
        self.agent_health[agent_name] = HealthStatus.CRITICAL
    
    # ==================== LOOPS DE MONITOREO ====================
    
    async def _health_monitoring_loop(self):
        """Loop principal de monitoreo de salud"""
        while self.is_running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(10)  # Check every 10 seconds
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(30)
    
    async def _perform_health_checks(self):
        """Realizar health checks para todos los agentes"""
        for agent_name, health_status in self.agent_health.items():
            if health_status in [HealthStatus.CRITICAL, HealthStatus.FAILED]:
                # Agente problemático, verificar si se puede recuperar
                recovery_needed = await self._assess_recovery_need(agent_name)
                if recovery_needed:
                    await self._initiate_recovery(agent_name, health_status)
    
    async def _assess_recovery_need(self, agent_name: str) -> bool:
        """Evaluar si un agente necesita recuperación"""
        # Obtener métricas recientes
        if agent_name not in self.agent_metrics:
            return True
        
        recent_metrics = list(self.agent_metrics[agent_name])[-5:]
        if len(recent_metrics) < 2:
            return True
        
        # Verificar si las métricas mejoran
        latest_metrics = recent_metrics[-1]
        previous_metrics = recent_metrics[-2]
        
        health_improvement = latest_metrics.health_score - previous_metrics.health_score
        
        # Si el health score está mejorando, no necesita recuperación inmediata
        return health_improvement <= 0
    
    async def _error_analysis_loop(self):
        """Loop de análisis de errores"""
        while self.is_running:
            try:
                await self._analyze_error_patterns()
                await asyncio.sleep(60)  # Analyze every minute
            except Exception as e:
                self.logger.error(f"Error in error analysis loop: {e}")
                await asyncio.sleep(120)
    
    async def _analyze_error_patterns(self):
        """Analizar patrones de errores para prevención"""
        if len(self.error_history) < 10:
            return
        
        # Agrupar errores por tipo y fuente
        error_patterns = defaultdict(list)
        
        for error_event in list(self.error_history)[-100:]:  # Last 100 errors
            pattern_key = f"{error_event.error_type}_{error_event.source}"
            error_patterns[pattern_key].append(error_event)
        
        # Identificar patrones problemáticos
        for pattern_key, errors in error_patterns.items():
            if len(errors) > 5:  # More than 5 similar errors
                await self._handle_error_pattern(pattern_key, errors)
    
    async def _handle_error_pattern(self, pattern_key: str, errors: List[ErrorEvent]):
        """Manejar patrón de errores identificado"""
        error_type, source = pattern_key.split("_", 1)
        
        self.logger.warning(f"Error pattern detected: {pattern_key} - {len(errors)} occurrences")
        self.stats["anomalies_detected"] += 1
        
        # Estrategias específicas por patrón
        if error_type == "timeout" and source in self.circuit_breakers:
            # Para timeouts, activar circuit breaker con timeout más corto
            self.circuit_breakers[source].config.recovery_timeout = max(30, 
                self.circuit_breakers[source].config.recovery_timeout // 2)
        
        elif error_type == "memory" and source in self.agent_instances:
            # Para problemas de memoria, reducir instancias
            current_instances = self.agent_instances[source]
            if current_instances > 1:
                self.agent_instances[source] = current_instances // 2
                self.logger.info(f"Scaled down {source} due to memory errors")
    
    async def _auto_scaling_loop(self):
        """Loop de auto-scaling"""
        while self.is_running:
            try:
                await self._perform_auto_scaling()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error in auto scaling loop: {e}")
                await asyncio.sleep(120)
    
    async def _perform_auto_scaling(self):
        """Realizar auto-scaling basado en métricas"""
        for agent_name in self.agent_health.keys():
            if self.agent_health[agent_name] != HealthStatus.HEALTHY:
                continue  # Don't scale unhealthy agents
            
            await self._evaluate_scaling_for_agent(agent_name)
    
    async def _evaluate_scaling_for_agent(self, agent_name: str):
        """Evaluar necesidad de scaling para un agente específico"""
        if agent_name not in self.agent_metrics:
            return
        
        recent_metrics = list(self.agent_metrics[agent_name])[-10:]
        if len(recent_metrics) < 5:
            return
        
        # Calcular métricas promedio
        avg_cpu = np.mean([m.cpu_usage for m in recent_metrics])
        avg_memory = np.mean([m.memory_usage for m in recent_metrics])
        avg_response_time = np.mean([m.response_time for m in recent_metrics])
        avg_error_rate = np.mean([m.error_rate for m in recent_metrics])
        avg_throughput = np.mean([m.throughput for m in recent_metrics])
        
        # Decidir acción de scaling
        scaling_action = ScalingAction.NO_ACTION
        
        if avg_cpu > self.config.target_cpu_usage or avg_memory > self.config.target_memory_usage:
            if avg_error_rate < 0.05 and avg_throughput > 10:  # Good performance
                scaling_action = ScalingAction.SCALE_OUT
        elif avg_cpu < self.config.target_cpu_usage * 0.5 and avg_memory < self.config.target_memory_usage * 0.5:
            if avg_error_rate < 0.01:  # Low error rate
                scaling_action = ScalingAction.SCALE_IN
        
        # Ejecutar scaling si es necesario
        if scaling_action != ScalingAction.NO_ACTION:
            await self._execute_scaling(agent_name, scaling_action)
    
    async def _execute_scaling(self, agent_name: str, action: ScalingAction):
        """Ejecutar acción de scaling"""
        current_instances = self.agent_instances.get(agent_name, 1)
        
        # Verificar cooldown
        last_action = self.last_scaling_action.get(agent_name)
        if last_action and (datetime.now() - last_action).seconds < self.config.scaling_cooldown:
            return
        
        try:
            if action == ScalingAction.SCALE_OUT:
                new_instances = min(self.config.max_instances, current_instances + 1)
                self.logger.info(f"Scaling out {agent_name}: {current_instances} -> {new_instances}")
                
            elif action == ScalingAction.SCALE_IN:
                new_instances = max(self.config.min_instances, current_instances - 1)
                self.logger.info(f"Scaling in {agent_name}: {current_instances} -> {new_instances}")
            
            else:
                return
            
            self.agent_instances[agent_name] = new_instances
            self.last_scaling_action[agent_name] = datetime.now()
            self.stats["auto_scaling_events"] += 1
            
            # Notificar callbacks de scaling
            for callback in self.scaling_callbacks:
                try:
                    await callback(agent_name, action, current_instances, new_instances)
                except Exception as e:
                    self.logger.error(f"Error in scaling callback: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error executing scaling for {agent_name}: {e}")
    
    async def _predictive_analysis_loop(self):
        """Loop de análisis predictivo"""
        while self.is_running:
            try:
                await self._perform_predictive_analysis()
                await asyncio.sleep(120)  # Every 2 minutes
            except Exception as e:
                self.logger.error(f"Error in predictive analysis loop: {e}")
                await asyncio.sleep(300)
    
    async def _perform_predictive_analysis(self):
        """Realizar análisis predictivo para todos los agentes"""
        high_risk_agents = []
        
        for agent_name in self.agent_health.keys():
            failure_probability = self.failure_detector.predict_failure_probability(agent_name)
            
            if failure_probability > 0.7:  # High risk threshold
                high_risk_agents.append((agent_name, failure_probability))
                self.logger.warning(f"Agent {agent_name} at high failure risk: {failure_probability:.2f}")
        
        # Tomar acciones preventivas para agentes de alto riesgo
        for agent_name, probability in high_risk_agents:
            await self._preventive_action(agent_name, probability)
    
    async def _preventive_action(self, agent_name: str, failure_probability: float):
        """Tomar acción preventiva para agente de alto riesgo"""
        current_health = self.agent_health.get(agent_name, HealthStatus.HEALTHY)
        
        if current_health == HealthStatus.HEALTHY and failure_probability > 0.8:
            # Acción preventiva muy agresiva
            await self._apply_graceful_degradation(agent_name)
            self.logger.info(f"Applied preventive degradation to {agent_name} due to high failure risk")
    
    # ==================== MÉTODOS PÚBLICOS ====================
    
    def get_health_status(self) -> Dict[str, Any]:
        """Obtener estado completo de salud del sistema"""
        return {
            "overall_status": self._calculate_overall_health(),
            "agents": dict(self.agent_health),
            "circuit_breakers": {
                name: cb.get_state() 
                for name, cb in self.circuit_breakers.items()
            },
            "instances": dict(self.agent_instances),
            "stats": self.stats.copy()
        }
    
    def _calculate_overall_health(self) -> str:
        """Calcular estado general de salud del sistema"""
        if not self.agent_health:
            return "unknown"
        
        if any(status == HealthStatus.FAILED for status in self.agent_health.values()):
            return "critical"
        elif any(status == HealthStatus.CRITICAL for status in self.agent_health.values()):
            return "degraded"
        elif all(status == HealthStatus.HEALTHY for status in self.agent_health.values()):
            return "healthy"
        else:
            return "degraded"
    
    async def force_recovery(self, agent_name: str, strategy: Optional[RecoveryStrategy] = None) -> bool:
        """Forzar recuperación de un agente específico"""
        if agent_name not in self.agent_health:
            self.logger.error(f"Agent {agent_name} not found")
            return False
        
        if strategy is None:
            strategy = await self._determine_recovery_strategy(
                agent_name, 
                self.agent_health[agent_name]
            )
        
        return await self._execute_recovery_strategy(agent_name, strategy)
    
    def register_health_change_callback(self, callback: Callable):
        """Registrar callback para cambios de salud"""
        self.health_change_callbacks.append(callback)
    
    def register_recovery_callback(self, callback: Callable):
        """Registrar callback para eventos de recuperación"""
        self.recovery_callbacks.append(callback)
    
    def register_scaling_callback(self, callback: Callable):
        """Registrar callback para eventos de scaling"""
        self.scaling_callbacks.append(callback)
    
    def get_failure_predictions(self) -> Dict[str, float]:
        """Obtener predicciones de fallo para todos los agentes"""
        return {
            agent_name: self.failure_detector.predict_failure_probability(agent_name)
            for agent_name in self.agent_health.keys()
        }
    
    def get_anomalies(self) -> List[Dict[str, Any]]:
        """Obtener anomalías detectadas recientemente"""
        all_anomalies = []
        for agent_name in self.agent_health.keys():
            anomalies = self.failure_detector.detect_anomalies(agent_name)
            all_anomalies.extend(anomalies)
        
        return sorted(all_anomalies, key=lambda x: x["timestamp"], reverse=True)
    
    async def cleanup(self):
        """Limpiar recursos del motor de auto-healing"""
        self.logger.info("Cleaning up AutoHealingEngine...")
        
        self.is_running = False
        
        # Cancelar todas las tareas
        for task in self._tasks:
            if not task.done():
                task.cancel()
        
        # Esperar a que las tareas terminen
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        self.logger.info("AutoHealingEngine cleanup completed")


# ==================== INSTANCIA GLOBAL ====================

# Instancia global del motor de auto-healing
_auto_healing_engine: Optional[AutoHealingEngine] = None

async def get_auto_healing_engine() -> AutoHealingEngine:
    """Obtener instancia global del motor de auto-healing"""
    global _auto_healing_engine
    
    if _auto_healing_engine is None:
        _auto_healing_engine = AutoHealingEngine()
        await _auto_healing_engine.initialize()
    
    return _auto_healing_engine


# ==================== FACTORY FUNCTION ====================

def create_auto_healing_engine() -> AutoHealingEngine:
    """Factory para crear instancia del motor de auto-healing"""
    return AutoHealingEngine()


# ==================== INTEGRATION HELPERS ====================

class AutoHealingMixin:
    """Mixin para integrar auto-healing en otros componentes"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._auto_healing_engine: Optional[AutoHealingEngine] = None
    
    async def setup_auto_healing(self):
        """Configurar auto-healing para este componente"""
        if not self._auto_healing_engine:
            self._auto_healing_engine = await get_auto_healing_engine()
            
            # Registrar callbacks específicos
            await self._register_auto_healing_callbacks()
    
    async def _register_auto_healing_callbacks(self):
        """Registrar callbacks específicos del componente"""
        # Implementar en clases específicas
        pass
    
    async def report_error(self, error: Exception, context: Dict[str, Any] = None):
        """Reportar error al sistema de auto-healing"""
        if self._auto_healing_engine:
            error_event = ErrorEvent(
                timestamp=datetime.now(),
                error_type=type(error).__name__,
                severity="error",
                source=self.__class__.__name__,
                message=str(error),
                context=context or {}
            )
            await self._auto_healing_engine.record_error(error_event)
    
    async def report_metrics(self, metrics: Dict[str, float], agent_name: str = None):
        """Reportar métricas al sistema de auto-healing"""
        if self._auto_healing_engine:
            health_metrics = HealthMetrics(
                timestamp=datetime.now(),
                agent_name=agent_name or self.__class__.__name__,
                cpu_usage=metrics.get("cpu_usage", 0.0),
                memory_usage=metrics.get("memory_usage", 0.0),
                response_time=metrics.get("response_time", 0.0),
                error_rate=metrics.get("error_rate", 0.0),
                throughput=metrics.get("throughput", 0.0),
                active_tasks=metrics.get("active_tasks", 0),
                queue_size=metrics.get("queue_size", 0),
                health_score=metrics.get("health_score", 1.0)
            )
            await self._auto_healing_engine.record_health_metrics(
                agent_name or self.__class__.__name__, 
                health_metrics
            )


if __name__ == "__main__":
    # Ejemplo de uso del AutoHealingEngine
    async def main():
        engine = AutoHealingEngine()
        await engine.initialize()
        
        # Simular métricas de ejemplo
        import random
        
        for i in range(10):
            metrics = HealthMetrics(
                timestamp=datetime.now(),
                agent_name="reasoner",
                cpu_usage=random.uniform(10, 90),
                memory_usage=random.uniform(20, 80),
                response_time=random.uniform(0.1, 2.0),
                error_rate=random.uniform(0, 0.1),
                throughput=random.uniform(5, 50),
                active_tasks=random.randint(0, 10),
                queue_size=random.randint(0, 20),
                health_score=random.uniform(0.5, 1.0)
            )
            await engine.record_health_metrics("reasoner", metrics)
            await asyncio.sleep(1)
        
        # Mostrar estado final
        status = engine.get_health_status()
        print(json.dumps(status, indent=2, default=str))
        
        await engine.cleanup()
    
    asyncio.run(main())