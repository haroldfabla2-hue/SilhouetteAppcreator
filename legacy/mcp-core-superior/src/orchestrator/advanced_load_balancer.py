"""
Sistema de Load Balancing Avanzado y Fault Tolerance
Implementa estrategias sofisticadas de balanceo de carga y recuperación de errores
para el ecosistema de 20+ agentes
"""
import asyncio
import logging
import time
import random
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics
import hashlib
import json

from ..core.exceptions import LoadBalancingException, FaultToleranceException
from .intelligent_routing_system import IntelligentRoutingSystem, AgentCapabilities


class LoadBalancingStrategy(Enum):
    """Estrategias de balanceo de carga"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    RESOURCE_BASED = "resource_based"
    ADAPTIVE = "adaptive"
    PREDICTIVE = "predictive"


class CircuitBreakerState(Enum):
    """Estados del circuit breaker"""
    CLOSED = "closed"      # Normal
    OPEN = "open"          # Bloqueando requests
    HALF_OPEN = "half_open"  # Probando recuperación


@dataclass
class CircuitBreakerConfig:
    """Configuración del circuit breaker"""
    failure_threshold: int = 5  # Número de fallos antes de abrir
    recovery_timeout: float = 60.0  # Tiempo antes de intentar recuperación
    success_threshold: int = 3  # Éxitos necesarios para cerrar
    timeout_duration: float = 30.0  # Timeout para requests


@dataclass
class LoadBalancingMetrics:
    """Métricas de balanceo de carga"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    request_distribution: Dict[str, int] = field(default_factory=dict)
    performance_history: Dict[str, deque] = field(default_factory=lambda: defaultdict(lambda: deque(maxlen=50)))
    resource_utilization: Dict[str, float] = field(default_factory=dict)


@dataclass
class FaultToleranceConfig:
    """Configuración de tolerancia a fallos"""
    max_retries: int = 3
    retry_delay: float = 1.0
    exponential_backoff: bool = True
    timeout_multiplier: float = 1.5
    health_check_interval: float = 30.0
    failure_prediction_window: int = 10


class CircuitBreaker:
    """Circuit breaker para tolerancia a fallos"""
    
    def __init__(self, agent_type: str, config: CircuitBreakerConfig):
        self.agent_type = agent_type
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.request_times = deque(maxlen=100)
        
    async def can_execute(self) -> bool:
        """Verificar si se puede ejecutar"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            # Verificar si es tiempo de intentar recuperación
            if self.last_failure_time:
                time_since_failure = (datetime.now() - self.last_failure_time).total_seconds()
                if time_since_failure >= self.config.recovery_timeout:
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.success_count = 0
                    return True
            return False
        else:  # HALF_OPEN
            return True
    
    async def record_success(self) -> None:
        """Registrar éxito"""
        self.request_times.append(time.time())
        self.success_count += 1
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
    
    async def record_failure(self) -> None:
        """Registrar fallo"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
    
    async def get_average_response_time(self) -> float:
        """Obtener tiempo promedio de respuesta"""
        if len(self.request_times) < 2:
            return 0.0
        
        # Calcular diferencias entre requests consecutivos
        times = list(self.request_times)
        intervals = [times[i+1] - times[i] for i in range(len(times)-1)]
        return statistics.mean(intervals) if intervals else 0.0
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado del circuit breaker"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold
            }
        }


class AdvancedLoadBalancer:
    """Balanceador de carga avanzado con capacidades de fault tolerance"""
    
    def __init__(self, routing_system: IntelligentRoutingSystem):
        self.logger = logging.getLogger("mcp.load_balancer.advanced")
        self.routing_system = routing_system
        
        # Configuración de load balancing
        self.strategy = LoadBalancingStrategy.ADAPTIVE
        self.metrics = LoadBalancingMetrics()
        
        # Circuit breakers por agente
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.circuit_configs: Dict[str, CircuitBreakerConfig] = {}
        
        # Fault tolerance
        self.fault_config = FaultToleranceConfig()
        self.health_check_tasks: Dict[str, asyncio.Task] = {}
        self.failure_prediction: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        
        # Recursos y capacidad
        self.resource_tracking: Dict[str, Dict[str, float]] = defaultdict(lambda: {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "network_io": 0.0,
            "disk_io": 0.0
        })
        
        self.is_initialized = False
        
    async def initialize(self, agent_configs: Dict[str, Any]) -> None:
        """Inicializar balanceador de carga"""
        
        # Inicializar circuit breakers para cada agente
        for agent_type in agent_configs.keys():
            config = CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=60.0,
                success_threshold=3
            )
            self.circuit_configs[agent_type] = config
            self.circuit_breakers[agent_type] = CircuitBreaker(agent_type, config)
            
            # Inicializar tracking de recursos
            self.resource_tracking[agent_type] = {
                "cpu_usage": random.uniform(0.1, 0.8),
                "memory_usage": random.uniform(0.1, 0.7),
                "network_io": random.uniform(0.1, 0.9),
                "disk_io": random.uniform(0.1, 0.6)
            }
        
        # Inicializar sistema de health checking
        await self._start_health_monitoring()
        
        self.is_initialized = True
        self.logger.info(f"Balanceador de carga inicializado con {len(agent_configs)} agentes")
    
    async def _start_health_monitoring(self) -> None:
        """Iniciar monitoreo de salud de agentes"""
        for agent_type in self.routing_system.agent_registry.keys():
            task = asyncio.create_task(self._health_monitor_loop(agent_type))
            self.health_check_tasks[agent_type] = task
    
    async def _health_monitor_loop(self, agent_type: str) -> None:
        """Loop de monitoreo de salud para un agente específico"""
        while True:
            try:
                await self._check_agent_health(agent_type)
                await asyncio.sleep(self.fault_config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error en health monitor para {agent_type}: {e}")
                await asyncio.sleep(5)  # Retry en caso de error
    
    async def _check_agent_health(self, agent_type: str) -> None:
        """Verificar salud de un agente específico"""
        try:
            capabilities = self.routing_system.agent_registry.get(agent_type)
            if not capabilities:
                return
            
            # Simular health check - en implementación real sería una llamada real
            health_score = await self._simulate_health_check(agent_type)
            
            # Actualizar métricas de salud
            if health_score < 0.5:
                self.logger.warning(f"Agente {agent_type} tiene health score bajo: {health_score:.2f}")
                
                # Registrar predicción de fallo
                self.failure_prediction[agent_type].append({
                    "timestamp": datetime.now(),
                    "health_score": health_score,
                    "predicted_failure": health_score < 0.3
                })
        
        except Exception as e:
            self.logger.error(f"Error verificando salud de {agent_type}: {e}")
    
    async def _simulate_health_check(self, agent_type: str) -> float:
        """Simular health check - en implementación real sería real"""
        # Simular basado en circuit breaker y recursos
        circuit_breaker = self.circuit_breakers.get(agent_type)
        resources = self.resource_tracking[agent_type]
        
        if not circuit_breaker:
            return 0.5
        
        # Health score basado en estado del circuit breaker y recursos
        base_score = 1.0
        if circuit_breaker.state == CircuitBreakerState.OPEN:
            base_score *= 0.1
        elif circuit_breaker.state == CircuitBreakerState.HALF_OPEN:
            base_score *= 0.5
        
        # Penalizar por alto uso de recursos
        resource_penalty = (
            resources["cpu_usage"] + 
            resources["memory_usage"] + 
            resources["network_io"] + 
            resources["disk_io"]
        ) / 4
        base_score *= (1.0 - resource_penalty * 0.3)
        
        return max(0.0, min(1.0, base_score))
    
    async def select_optimal_agent(
        self,
        task_requirements: Dict[str, Any],
        fallback_agents: Optional[List[str]] = None
    ) -> Optional[str]:
        """Seleccionar agente óptimo con load balancing y fault tolerance"""
        
        if not self.is_initialized:
            raise LoadBalancingException("Load balancer no inicializado")
        
        self.metrics.total_requests += 1
        
        # Obtener candidatos del sistema de routing
        suitable_agents = self.routing_system._filter_suitable_agents(
            task_requirements, 
            constraints=task_requirements.get("constraints", {})
        )
        
        if not suitable_agents:
            suitable_agents = fallback_agents or list(self.routing_system.agent_registry.keys())
        
        if not suitable_agents:
            self.logger.error("No hay agentes disponibles")
            self.metrics.failed_requests += 1
            return None
        
        # Aplicar load balancing strategy
        selected_agent = await self._apply_load_balancing_strategy(suitable_agents, task_requirements)
        
        if selected_agent:
            # Verificar circuit breaker
            circuit_breaker = self.circuit_breakers.get(selected_agent)
            if circuit_breaker and not await circuit_breaker.can_execute():
                self.logger.warning(f"Circuit breaker abierto para {selected_agent}, buscando fallback")
                return await self._find_fallback_agent(suitable_agents, selected_agent)
            
            self.metrics.request_distribution[selected_agent] = self.metrics.request_distribution.get(selected_agent, 0) + 1
            return selected_agent
        
        self.metrics.failed_requests += 1
        return None
    
    async def _apply_load_balancing_strategy(
        self, 
        suitable_agents: List[str], 
        task_requirements: Dict[str, Any]
    ) -> Optional[str]:
        """Aplicar estrategia de load balancing"""
        
        if not suitable_agents:
            return None
        
        strategy_functions = {
            LoadBalancingStrategy.ROUND_ROBIN: self._round_robin_strategy,
            LoadBalancingStrategy.WEIGHTED: self._weighted_strategy,
            LoadBalancingStrategy.LEAST_CONNECTIONS: self._least_connections_strategy,
            LoadBalancingStrategy.LEAST_RESPONSE_TIME: self._least_response_time_strategy,
            LoadBalancingStrategy.RESOURCE_BASED: self._resource_based_strategy,
            LoadBalancingStrategy.ADAPTIVE: self._adaptive_strategy,
            LoadBalancingStrategy.PREDICTIVE: self._predictive_strategy
        }
        
        strategy_func = strategy_functions.get(self.strategy, self._adaptive_strategy)
        return await strategy_func(suitable_agents, task_requirements)
    
    async def _round_robin_strategy(self, suitable_agents: List[str], task_requirements: Dict[str, Any]) -> str:
        """Estrategia round-robin simple"""
        # Implementar round-robin con tracking
        if not suitable_agents:
            return None
        
        # Selección simple por ahora
        return random.choice(suitable_agents)
    
    async def _weighted_strategy(self, suitable_agents: List[str], task_requirements: Dict[str, Any]) -> str:
        """Estrategia basada en pesos"""
        if not suitable_agents:
            return None
        
        # Calcular pesos basado en capacidades
        weights = []
        for agent_type in suitable_agents:
            capabilities = self.routing_system.agent_registry[agent_type]
            # Peso = success_rate / (response_time * resource_cost)
            weight = capabilities.success_rate / (
                (capabilities.avg_response_time * capabilities.resource_cost) + 0.1
            )
            weights.append(weight)
        
        # Selección ponderada
        total_weight = sum(weights)
        if total_weight == 0:
            return suitable_agents[0]
        
        normalized_weights = [w / total_weight for w in weights]
        rand = random.random()
        
        cumulative = 0
        for i, weight in enumerate(normalized_weights):
            cumulative += weight
            if rand <= cumulative:
                return suitable_agents[i]
        
        return suitable_agents[-1]
    
    async def _least_connections_strategy(self, suitable_agents: List[str], task_requirements: Dict[str, Any]) -> str:
        """Estrategia de menos conexiones activas"""
        if not suitable_agents:
            return None
        
        # Ordenar por número de tareas activas (menor primero)
        sorted_agents = sorted(
            suitable_agents,
            key=lambda x: self.routing_system.agent_registry[x].active_tasks
        )
        return sorted_agents[0]
    
    async def _least_response_time_strategy(self, suitable_agents: List[str], task_requirements: Dict[str, Any]) -> str:
        """Estrategia de menor tiempo de respuesta"""
        if not suitable_agents:
            return None
        
        # Ordenar por tiempo de respuesta promedio
        sorted_agents = sorted(
            suitable_agents,
            key=lambda x: self.routing_system.agent_registry[x].avg_response_time
        )
        return sorted_agents[0]
    
    async def _resource_based_strategy(self, suitable_agents: List[str], task_requirements: Dict[str, Any]) -> str:
        """Estrategia basada en recursos disponibles"""
        if not suitable_agents:
            return None
        
        # Calcular score de recursos para cada agente
        resource_scores = {}
        for agent_type in suitable_agents:
            resources = self.resource_tracking[agent_type]
            capabilities = self.routing_system.agent_registry[agent_type]
            
            # Score de recursos: inverso de uso de CPU y memoria, proporcional a capacidad
            resource_score = (
                (1.0 - resources["cpu_usage"]) * 0.4 +
                (1.0 - resources["memory_usage"]) * 0.3 +
                (1.0 - resources["disk_io"]) * 0.3
            ) * (capabilities.max_concurrent_tasks / 5.0)
            
            resource_scores[agent_type] = resource_score
        
        # Seleccionar agente con mejor score de recursos
        return max(resource_scores.keys(), key=lambda x: resource_scores[x])
    
    async def _adaptive_strategy(self, suitable_agents: List[str], task_requirements: Dict[str, Any]) -> str:
        """Estrategia adaptativa que combina múltiples factores"""
        if not suitable_agents:
            return None
        
        # Calcular scores combinados
        combined_scores = {}
        
        for agent_type in suitable_agents:
            capabilities = self.routing_system.agent_registry[agent_type]
            resources = self.resource_tracking[agent_type]
            circuit_breaker = self.circuit_breakers[agent_type]
            
            # Score de capacidad
            capacity_score = (capabilities.max_concurrent_tasks - capabilities.active_tasks) / max(capabilities.max_concurrent_tasks, 1)
            
            # Score de calidad
            quality_score = capabilities.quality_score
            
            # Score de recursos
            resource_score = (1.0 - resources["cpu_usage"]) * (1.0 - resources["memory_usage"])
            
            # Score de circuit breaker
            circuit_score = 1.0 if circuit_breaker.state == CircuitBreakerState.CLOSED else 0.1
            
            # Score de performance histórico
            history = self.metrics.performance_history.get(agent_type, deque())
            history_score = statistics.mean(list(history)[-10:]) if history else capabilities.quality_score
            
            # Combinar scores con pesos
            combined_score = (
                capacity_score * 0.25 +
                quality_score * 0.25 +
                resource_score * 0.2 +
                circuit_score * 0.15 +
                history_score * 0.15
            )
            
            combined_scores[agent_type] = combined_score
        
        # Seleccionar agente con mejor score combinado
        return max(combined_scores.keys(), key=lambda x: combined_scores[x])
    
    async def _predictive_strategy(self, suitable_agents: List[str], task_requirements: Dict[str, Any]) -> str:
        """Estrategia predictiva basada en fallos históricos"""
        if not suitable_agents:
            return None
        
        # Analizar predicción de fallos para cada agente
        failure_predictions = {}
        
        for agent_type in suitable_agents:
            predictions = list(self.failure_prediction.get(agent_type, []))
            
            if predictions:
                recent_predictions = predictions[-10:]  # Últimas 10 predicciones
                failure_rate = sum(1 for p in recent_predictions if p["predicted_failure"]) / len(recent_predictions)
                failure_predictions[agent_type] = failure_rate
            else:
                failure_predictions[agent_type] = 0.0
        
        # Seleccionar agente con menor probabilidad de fallo
        return min(failure_predictions.keys(), key=lambda x: failure_predictions[x])
    
    async def _find_fallback_agent(self, suitable_agents: List[str], blocked_agent: str) -> Optional[str]:
        """Encontrar agente fallback cuando el principal está bloqueado"""
        fallback_candidates = [agent for agent in suitable_agents if agent != blocked_agent]
        
        for candidate in fallback_candidates:
            circuit_breaker = self.circuit_breakers.get(candidate)
            if circuit_breaker and await circuit_breaker.can_execute():
                return candidate
        
        self.logger.error("No hay agentes fallback disponibles")
        return None
    
    async def record_task_completion(
        self, 
        agent_type: str, 
        task_result: Dict[str, Any], 
        duration: float
    ) -> None:
        """Registrar completación de tarea"""
        
        # Actualizar métricas de load balancing
        if task_result.get("success", False):
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
        
        # Actualizar tiempo promedio de respuesta
        all_response_times = self.metrics.performance_history.get(agent_type, deque())
        all_response_times.append(duration)
        
        if len(self.metrics.performance_history) > 1:
            self.metrics.average_response_time = statistics.mean([
                time for agent_times in self.metrics.performance_history.values() 
                for time in agent_times
            ])
        
        # Actualizar circuit breaker
        circuit_breaker = self.circuit_breakers.get(agent_type)
        if circuit_breaker:
            if task_result.get("success", False):
                await circuit_breaker.record_success()
            else:
                await circuit_breaker.record_failure()
        
        # Actualizar en routing system
        await self.routing_system.complete_task(agent_type, task_result, duration)
        
        self.logger.debug(f"Tarea completada para {agent_type}, duración: {duration:.2f}s")
    
    async def execute_with_retry(
        self,
        task_requirements: Dict[str, Any],
        max_retries: Optional[int] = None
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """Ejecutar tarea con retry automático y fault tolerance"""
        
        max_retries = max_retries or self.fault_config.max_retries
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                # Seleccionar agente
                agent_type = await self.select_optimal_agent(task_requirements)
                if not agent_type:
                    raise LoadBalancingException("No se pudo seleccionar agente")
                
                start_time = time.time()
                return agent_type, {"success": True, "agent_selected": agent_type}
                
            except Exception as e:
                last_error = e
                self.logger.warning(f"Intento {attempt + 1} falló: {e}")
                
                if attempt < max_retries:
                    # Delay con exponential backoff
                    delay = self.fault_config.retry_delay * (
                        self.fault_config.timeout_multiplier ** attempt
                    )
                    await asyncio.sleep(delay)
                else:
                    break
        
        # Todos los intentos fallaron
        self.metrics.failed_requests += 1
        raise FaultToleranceException(f"Tarea falló después de {max_retries} intentos", str(last_error))
    
    async def get_load_balancing_status(self) -> Dict[str, Any]:
        """Obtener estado detallado del balanceador de carga"""
        
        agent_status = {}
        circuit_breaker_states = {}
        
        for agent_type in self.routing_system.agent_registry.keys():
            capabilities = self.routing_system.agent_registry[agent_type]
            circuit_breaker = self.circuit_breakers.get(agent_type)
            
            agent_status[agent_type] = {
                "active_tasks": capabilities.active_tasks,
                "max_capacity": capabilities.max_concurrent_tasks,
                "utilization": capabilities.active_tasks / max(capabilities.max_concurrent_tasks, 1),
                "resources": self.resource_tracking[agent_type],
                "performance_history": len(self.metrics.performance_history.get(agent_type, []))
            }
            
            if circuit_breaker:
                circuit_breaker_states[agent_type] = circuit_breaker.get_status()
        
        success_rate = self.metrics.successful_requests / max(self.metrics.total_requests, 1)
        
        return {
            "strategy": self.strategy.value,
            "is_initialized": self.is_initialized,
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "success_rate": success_rate,
            "average_response_time": self.metrics.average_response_time,
            "request_distribution": self.metrics.request_distribution,
            "agents": agent_status,
            "circuit_breakers": circuit_breaker_states,
            "failure_predictions": {
                agent_type: list(predictions)
                for agent_type, predictions in self.failure_prediction.items()
            }
        }
    
    async def optimize_strategies(self) -> Dict[str, str]:
        """Optimizar estrategias basado en métricas actuales"""
        
        recommendations = {}
        
        # Analizar distribución de requests
        total_distributed = sum(self.metrics.request_distribution.values())
        if total_distributed > 0:
            # Calcular coeficiente de variación para evaluar balance
            request_counts = list(self.metrics.request_distribution.values())
            if len(request_counts) > 1:
                cv = statistics.stdev(request_counts) / statistics.mean(request_counts)
                if cv > 0.5:
                    recommendations["load_balancing"] = "Considerar estrategia más equilibrada (weighted o adaptive)"
                else:
                    recommendations["load_balancing"] = "Distribución actual es buena"
        
        # Analizar circuit breakers
        open_circuits = sum(
            1 for cb in self.circuit_breakers.values() 
            if cb.state == CircuitBreakerState.OPEN
        )
        
        if open_circuits > len(self.circuit_breakers) * 0.2:
            recommendations["fault_tolerance"] = "Muchos circuit breakers abiertos, revisar configuración"
        else:
            recommendations["fault_tolerance"] = "Fault tolerance funcionando correctamente"
        
        return recommendations
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check del sistema de load balancing"""
        
        if not self.is_initialized:
            return {"status": "unhealthy", "reason": "not_initialized"}
        
        # Verificar health de routing system
        routing_health = await self.routing_system.health_check()
        
        # Verificar circuit breakers
        healthy_circuits = 0
        total_circuits = len(self.circuit_breakers)
        
        for circuit_breaker in self.circuit_breakers.values():
            if circuit_breaker.state in [CircuitBreakerState.CLOSED, CircuitBreakerState.HALF_OPEN]:
                healthy_circuits += 1
        
        # Verificar métricas generales
        success_rate = self.metrics.successful_requests / max(self.metrics.total_requests, 1)
        
        overall_health = (
            routing_health.get("status") == "healthy" and
            healthy_circuits / max(total_circuits, 1) > 0.7 and
            success_rate > 0.8
        )
        
        return {
            "status": "healthy" if overall_health else "degraded",
            "routing_system_health": routing_health,
            "circuit_breakers": {
                "total": total_circuits,
                "healthy": healthy_circuits,
                "health_ratio": healthy_circuits / max(total_circuits, 1)
            },
            "performance": {
                "success_rate": success_rate,
                "total_requests": self.metrics.total_requests,
                "average_response_time": self.metrics.average_response_time
            }
        }
    
    async def shutdown(self) -> None:
        """Shutdown del balanceador de carga"""
        
        # Cancelar tasks de health monitoring
        for task in self.health_check_tasks.values():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self.is_initialized = False
        self.logger.info("Balanceador de carga shutdown completado")