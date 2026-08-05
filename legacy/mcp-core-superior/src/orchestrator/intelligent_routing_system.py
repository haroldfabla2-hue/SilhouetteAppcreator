"""
Sistema de Routing Inteligente para Orquestación Multi-Agente
Maneja 20+ agentes especializados con routing dinámico basado en ML
"""
import asyncio
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json
from dataclasses import dataclass
import statistics
from collections import defaultdict, deque

from ..core.exceptions import AgentRoutingException
from ..core.config import settings


class RoutingStrategy(Enum):
    """Estrategias de routing"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RESPONSE_TIME = "response_time"
    LEARNING_BASED = "learning_based"
    CAPACITY_BASED = "capacity_based"
    COST_OPTIMIZED = "cost_optimized"
    QUALITY_BASED = "quality_based"


@dataclass
class AgentCapabilities:
    """Capacidades de un agente"""
    agent_type: str
    skills: List[str]
    max_concurrent_tasks: int
    avg_response_time: float
    success_rate: float
    quality_score: float
    resource_cost: float
    domain_expertise: List[str]
    last_used: Optional[datetime] = None
    active_tasks: int = 0


@dataclass
class RoutingMetrics:
    """Métricas de routing"""
    total_requests: int = 0
    successful_routes: int = 0
    failed_routes: int = 0
    average_response_time: float = 0.0
    quality_scores: List[float] = None
    agent_utilization: Dict[str, float] = None
    
    def __post_init__(self):
        if self.quality_scores is None:
            self.quality_scores = []
        if self.agent_utilization is None:
            self.agent_utilization = {}


class IntelligentRoutingSystem:
    """Sistema de routing inteligente para agentes"""
    
    def __init__(self):
        self.logger = logging.getLogger("mcp.routing.intelligent")
        
        # Registro de agentes y sus capacidades
        self.agent_registry: Dict[str, AgentCapabilities] = {}
        self.routing_metrics: Dict[str, RoutingMetrics] = defaultdict(RoutingMetrics)
        
        # Estado de routing dinámico
        self.routing_round_robin: Dict[str, int] = defaultdict(int)
        self.performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.adaptation_cache: Dict[str, Any] = {}
        
        # Configuración de estrategias
        self.routing_strategies = {
            RoutingStrategy.ROUND_ROBIN: self._round_robin_select,
            RoutingStrategy.WEIGHTED_ROUND_ROBIN: self._weighted_round_robin_select,
            RoutingStrategy.LEAST_CONNECTIONS: self._least_connections_select,
            RoutingStrategy.RESPONSE_TIME: self._response_time_select,
            RoutingStrategy.LEARNING_BASED: self._learning_based_select,
            RoutingStrategy.CAPACITY_BASED: self._capacity_based_select,
            RoutingStrategy.COST_OPTIMIZED: self._cost_optimized_select,
            RoutingStrategy.QUALITY_BASED: self._quality_based_select
        }
        
        self.is_initialized = False
        
    async def initialize(self, agent_configs: Dict[str, Any]) -> None:
        """Inicializar sistema de routing"""
        
        # Registrar todos los agentes disponibles
        for agent_type, config in agent_configs.items():
            capabilities = AgentCapabilities(
                agent_type=agent_type,
                skills=config.get("skills", []),
                max_concurrent_tasks=config.get("max_concurrent_tasks", 5),
                avg_response_time=config.get("avg_response_time", 2.0),
                success_rate=config.get("success_rate", 0.9),
                quality_score=config.get("quality_score", 0.8),
                resource_cost=config.get("resource_cost", 1.0),
                domain_expertise=config.get("domain_expertise", [])
            )
            self.agent_registry[agent_type] = capabilities
            self.logger.info(f"Agente registrado: {agent_type}")
        
        self.is_initialized = True
        self.logger.info(f"Sistema de routing inicializado con {len(self.agent_registry)} agentes")
    
    async def register_agent(self, agent_type: str, capabilities: AgentCapabilities) -> None:
        """Registrar un nuevo agente dinámicamente"""
        self.agent_registry[agent_type] = capabilities
        self.routing_metrics[agent_type] = RoutingMetrics()
        self.logger.info(f"Agente registrado dinámicamente: {agent_type}")
    
    async def select_optimal_agent(
        self,
        task_requirements: Dict[str, Any],
        preferred_strategy: RoutingStrategy = RoutingStrategy.LEARNING_BASED,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Seleccionar el agente óptimo para una tarea"""
        
        if not self.is_initialized:
            raise AgentRoutingException("Sistema de routing no inicializado")
        
        # Filtrar agentes por requisitos de la tarea
        suitable_agents = self._filter_suitable_agents(task_requirements, constraints)
        
        if not suitable_agents:
            self.logger.warning("No hay agentes adecuados para la tarea")
            return None
        
        # Seleccionar usando la estrategia especificada
        select_function = self.routing_strategies.get(preferred_strategy, self._learning_based_select)
        selected_agent = await select_function(suitable_agents, task_requirements)
        
        if selected_agent:
            # Actualizar métricas de uso
            await self._update_agent_usage(selected_agent, task_requirements)
            self.logger.info(f"Agente seleccionado: {selected_agent} para estrategia {preferred_strategy.value}")
        
        return selected_agent
    
    def _filter_suitable_agents(
        self, 
        task_requirements: Dict[str, Any], 
        constraints: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Filtrar agentes que satisfacen los requisitos de la tarea"""
        
        suitable_agents = []
        required_skills = task_requirements.get("required_skills", [])
        domain = task_requirements.get("domain", "")
        
        for agent_type, capabilities in self.agent_registry.items():
            
            # Verificar capacidad de concurrencia
            if capabilities.active_tasks >= capabilities.max_concurrent_tasks:
                continue
            
            # Verificar skills requeridos
            if required_skills and not any(skill in capabilities.skills for skill in required_skills):
                continue
            
            # Verificar dominio de expertise
            if domain and domain not in capabilities.domain_expertise:
                continue
            
            # Verificar restricciones adicionales
            if constraints:
                if not self._check_constraints(capabilities, constraints):
                    continue
            
            suitable_agents.append(agent_type)
        
        return suitable_agents
    
    def _check_constraints(self, capabilities: AgentCapabilities, constraints: Dict[str, Any]) -> bool:
        """Verificar restricciones específicas"""
        
        max_response_time = constraints.get("max_response_time")
        if max_response_time and capabilities.avg_response_time > max_response_time:
            return False
        
        min_quality = constraints.get("min_quality")
        if min_quality and capabilities.quality_score < min_quality:
            return False
        
        max_cost = constraints.get("max_cost")
        if max_cost and capabilities.resource_cost > max_cost:
            return False
        
        return True
    
    async def _round_robin_select(self, suitable_agents: List[str], task_requirements: Dict[str, Any]) -> str:
        """Selección round-robin simple"""
        agent_type = suitable_agents[0] if suitable_agents else None
        if agent_type:
            self.routing_round_robin[agent_type] += 1
        return agent_type
    
    async def _weighted_round_robin_select(self, suitable_agents: List[str], task_requirements: Dict[str, Any]) -> str:
        """Selección weighted round-robin basada en performance"""
        if not suitable_agents:
            return None
        
        # Calcular pesos basado en success_rate y inverse response_time
        weights = []
        for agent_type in suitable_agents:
            capabilities = self.agent_registry[agent_type]
            weight = capabilities.success_rate / max(capabilities.avg_response_time, 0.1)
            weights.append(weight)
        
        # Seleccionar basado en pesos
        total_weight = sum(weights)
        if total_weight == 0:
            return suitable_agents[0]
        
        normalized_weights = [w / total_weight for w in weights]
        cumulative_weights = np.cumsum(normalized_weights)
        
        rand = np.random.random()
        selected_index = next(i for i, cw in enumerate(cumulative_weights) if rand <= cw)
        
        return suitable_agents[selected_index]
    
    async def _least_connections_select(self, suitable_agents: List[str], task_requirements: Dict[str, Any]) -> str:
        """Selección basada en menos conexiones activas"""
        if not suitable_agents:
            return None
        
        # Ordenar por número de tareas activas (menor primero)
        sorted_agents = sorted(suitable_agents, key=lambda x: self.agent_registry[x].active_tasks)
        return sorted_agents[0]
    
    async def _response_time_select(self, suitable_agents: List[str], task_requirements: Dict[str, Any]) -> str:
        """Selección basada en tiempo de respuesta"""
        if not suitable_agents:
            return None
        
        # Ordenar por tiempo de respuesta promedio (menor primero)
        sorted_agents = sorted(suitable_agents, key=lambda x: self.agent_registry[x].avg_response_time)
        return sorted_agents[0]
    
    async def _learning_based_select(self, suitable_agents: List[str], task_requirements: Dict[str, Any]) -> str:
        """Selección basada en aprendizaje automático"""
        if not suitable_agents:
            return None
        
        # Implementar selección basada en historial de performance
        scores = {}
        
        for agent_type in suitable_agents:
            capabilities = self.agent_registry[agent_type]
            history = self.performance_history[agent_type]
            
            if history:
                # Usar historial reciente para predecir performance
                recent_scores = list(history)[-10:]  # Últimas 10 mediciones
                predicted_score = np.mean(recent_scores) if recent_scores else capabilities.quality_score
            else:
                predicted_score = capabilities.quality_score
            
            # Combinar con factores actuales
            utilization_factor = 1.0 - (capabilities.active_tasks / max(capabilities.max_concurrent_tasks, 1))
            
            final_score = (predicted_score * 0.7) + (utilization_factor * 0.3)
            scores[agent_type] = final_score
        
        # Seleccionar agente con mejor score
        best_agent = max(scores.keys(), key=lambda x: scores[x])
        return best_agent
    
    async def _capacity_based_select(self, suitable_agents: List[str], task_requirements: Dict[str, Any]) -> str:
        """Selección basada en capacidad disponible"""
        if not suitable_agents:
            return None
        
        # Calcular capacidad disponible para cada agente
        capacities = {}
        for agent_type in suitable_agents:
            capabilities = self.agent_registry[agent_type]
            available_capacity = capabilities.max_concurrent_tasks - capabilities.active_tasks
            capacities[agent_type] = available_capacity / max(capabilities.max_concurrent_tasks, 1)
        
        # Seleccionar agente con mayor capacidad disponible
        best_agent = max(capacities.keys(), key=lambda x: capacities[x])
        return best_agent
    
    async def _cost_optimized_select(self, suitable_agents: List[str], task_requirements: Dict[str, Any]) -> str:
        """Selección optimizada por costo"""
        if not suitable_agents:
            return None
        
        # Combinar costo con calidad para optimización costo-beneficio
        cost_benefit_scores = {}
        
        for agent_type in suitable_agents:
            capabilities = self.agent_registry[agent_type]
            # Score costo-beneficio: calidad / costo
            cost_benefit_score = capabilities.quality_score / max(capabilities.resource_cost, 0.1)
            cost_benefit_scores[agent_type] = cost_benefit_score
        
        # Seleccionar agente con mejor costo-beneficio
        best_agent = max(cost_benefit_scores.keys(), key=lambda x: cost_benefit_scores[x])
        return best_agent
    
    async def _quality_based_select(self, suitable_agents: List[str], task_requirements: Dict[str, Any]) -> str:
        """Selección basada en calidad"""
        if not suitable_agents:
            return None
        
        # Seleccionar agente con mejor calidad
        sorted_agents = sorted(suitable_agents, key=lambda x: self.agent_registry[x].quality_score, reverse=True)
        return sorted_agents[0]
    
    async def _update_agent_usage(self, agent_type: str, task_requirements: Dict[str, Any]) -> None:
        """Actualizar métricas de uso de agente"""
        if agent_type in self.agent_registry:
            self.agent_registry[agent_type].active_tasks += 1
            self.agent_registry[agent_type].last_used = datetime.now()
    
    async def complete_task(self, agent_type: str, task_result: Dict[str, Any], duration: float) -> None:
        """Marcar tarea como completada y actualizar métricas"""
        
        if agent_type not in self.agent_registry:
            return
        
        capabilities = self.agent_registry[agent_type]
        capabilities.active_tasks = max(0, capabilities.active_tasks - 1)
        
        # Actualizar métricas de routing
        metrics = self.routing_metrics[agent_type]
        metrics.total_requests += 1
        
        if task_result.get("success", False):
            metrics.successful_routes += 1
        else:
            metrics.failed_routes += 1
        
        # Actualizar historial de performance
        quality_score = task_result.get("quality_score", 0.0)
        self.performance_history[agent_type].append(quality_score)
        
        # Actualizar response time promedio
        all_response_times = []
        for entry in self.performance_history[agent_type]:
            if hasattr(entry, 'response_time'):
                all_response_times.append(entry.response_time)
        
        if all_response_times:
            metrics.average_response_time = statistics.mean(all_response_times)
        
        self.logger.info(f"Tarea completada para agente {agent_type}, activas: {capabilities.active_tasks}")
    
    async def get_routing_status(self) -> Dict[str, Any]:
        """Obtener estado del sistema de routing"""
        
        agent_status = {}
        total_utilization = 0
        
        for agent_type, capabilities in self.agent_registry.items():
            utilization = capabilities.active_tasks / max(capabilities.max_concurrent_tasks, 1)
            total_utilization += utilization
            
            agent_status[agent_type] = {
                "active_tasks": capabilities.active_tasks,
                "max_capacity": capabilities.max_concurrent_tasks,
                "utilization": utilization,
                "success_rate": capabilities.success_rate,
                "avg_response_time": capabilities.avg_response_time,
                "quality_score": capabilities.quality_score,
                "last_used": capabilities.last_used.isoformat() if capabilities.last_used else None
            }
        
        avg_utilization = total_utilization / max(len(self.agent_registry), 1)
        
        return {
            "is_initialized": self.is_initialized,
            "total_agents": len(self.agent_registry),
            "active_agents": sum(1 for cap in self.agent_registry.values() if cap.active_tasks > 0),
            "average_utilization": avg_utilization,
            "routing_strategies": [strategy.value for strategy in RoutingStrategy],
            "agents": agent_status,
            "routing_metrics": {
                agent_type: {
                    "total_requests": metrics.total_requests,
                    "success_rate": metrics.successful_routes / max(metrics.total_requests, 1),
                    "average_response_time": metrics.average_response_time
                }
                for agent_type, metrics in self.routing_metrics.items()
            }
        }
    
    async def optimize_routing_strategies(self) -> Dict[str, str]:
        """Optimizar estrategias de routing basado en performance histórico"""
        
        recommendations = {}
        
        # Analizar performance de cada estrategia
        for agent_type, metrics in self.routing_metrics.items():
            if metrics.total_requests > 10:  # Solo analizar si hay suficientes datos
                success_rate = metrics.successful_routes / metrics.total_requests
                avg_response_time = metrics.average_response_time
                
                # Generar recomendaciones
                if success_rate < 0.8:
                    recommendations[agent_type] = "Considerar usar estrategia basada en calidad"
                elif avg_response_time > 5.0:
                    recommendations[agent_type] = "Considerar estrategia de tiempo de respuesta"
                else:
                    recommendations[agent_type] = "Performance actual es buena"
        
        self.logger.info(f"Generadas {len(recommendations)} recomendaciones de optimización")
        return recommendations
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check del sistema de routing"""
        
        if not self.is_initialized:
            return {"status": "unhealthy", "reason": "not_initialized"}
        
        # Verificar que todos los agentes registrados tengan métricas
        healthy_agents = 0
        total_capacity = 0
        used_capacity = 0
        
        for agent_type, capabilities in self.agent_registry.items():
            total_capacity += capabilities.max_concurrent_tasks
            used_capacity += capabilities.active_tasks
            
            if capabilities.active_tasks < capabilities.max_concurrent_tasks:
                healthy_agents += 1
        
        utilization = used_capacity / max(total_capacity, 1)
        health_percentage = healthy_agents / max(len(self.agent_registry), 1)
        
        return {
            "status": "healthy" if health_percentage > 0.5 else "degraded",
            "total_agents": len(self.agent_registry),
            "healthy_agents": healthy_agents,
            "utilization": utilization,
            "is_initialized": self.is_initialized
        }