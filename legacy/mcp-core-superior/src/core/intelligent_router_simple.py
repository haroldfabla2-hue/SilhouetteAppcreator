"""
AI-Powered Intelligent Router (Versión Simplificada)
Sistema de routing inteligente sin dependencias externas pesadas
"""

import asyncio
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import logging
import json
import hashlib
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import threading
import time
import warnings
warnings.filterwarnings('ignore')

from ..core.config import settings
from ..core.exceptions import MCPCoreException, AgentException


class RoutingStrategy(Enum):
    """Estrategias de routing disponibles"""
    STATIC = "static"
    PERFORMANCE_BASED = "performance_based"
    SEMANTIC_MATCHING = "semantic_matching"
    LOAD_BALANCED = "load_balanced"
    CONTEXT_AWARE = "context_aware"
    AI_OPTIMIZED = "ai_optimized"  # Estrategia principal con ML simplificado


class OptimizationObjective(Enum):
    """Objetivos de optimización"""
    SPEED = "speed"
    ACCURACY = "accuracy"
    COST = "cost"
    RELIABILITY = "reliability"
    BALANCED = "balanced"


@dataclass
class RoutingContext:
    """Contexto para toma de decisiones de routing"""
    request_id: str
    user_id: Optional[str]
    request_type: str
    priority: str = "normal"
    complexity_score: float = 0.5
    domain: Optional[str] = None
    language: str = "es"
    user_preferences: Optional[Dict] = None
    time_constraints: Optional[Dict] = None
    budget_constraints: Optional[Dict] = None
    historical_success_rate: Optional[float] = None
    embedding_vector: Optional[List[float]] = None


@dataclass
class AgentMetrics:
    """Métricas de performance de agente para ML"""
    agent_name: str
    capability: str
    response_time: float
    success: bool
    cost: float
    user_satisfaction: Optional[float]
    timestamp: datetime
    context_features: Dict[str, Any]
    complexity_score: float


@dataclass
class RoutingDecision:
    """Decisión de routing"""
    agent_name: str
    confidence: float
    expected_performance: Dict[str, float]
    strategy_used: RoutingStrategy
    reasoning: str
    alternatives: List[Tuple[str, float]]


class SimplePerformancePredictor:
    """Predictor simplificado sin scikit-learn"""
    
    def __init__(self):
        self.agent_profiles = defaultdict(lambda: {
            "avg_response_time": 2.0,
            "success_rate": 0.85,
            "avg_cost": 0.1,
            "sample_count": 0
        })
        self.usage_history = deque(maxlen=1000)
        self.lock = threading.Lock()
        
        self.logger = logging.getLogger("mcp.router.simple_predictor")
    
    def add_training_sample(self, metrics: AgentMetrics) -> None:
        """Agregar muestra de entrenamiento"""
        with self.lock:
            self.usage_history.append(metrics)
            
            # Actualizar perfil del agente
            profile = self.agent_profiles[metrics.agent_name]
            profile["sample_count"] += 1
            
            # Actualizar promedios ponderados
            alpha = 0.1  # Factor de aprendizaje
            profile["avg_response_time"] = (
                (1 - alpha) * profile["avg_response_time"] + 
                alpha * metrics.response_time
            )
            
            profile["avg_cost"] = (
                (1 - alpha) * profile["avg_cost"] + 
                alpha * metrics.cost
            )
            
            # Actualizar success rate
            if metrics.success:
                current_successes = profile["success_rate"] * (profile["sample_count"] - 1) + 1
            else:
                current_successes = profile["success_rate"] * (profile["sample_count"] - 1)
            
            profile["success_rate"] = current_successes / profile["sample_count"]
    
    def predict_performance(
        self,
        agent_name: str,
        capability: str,
        context: Dict[str, Any],
        complexity_score: float = 0.5
    ) -> Dict[str, float]:
        """Predecir performance de agente"""
        
        # Obtener perfil del agente o usar default
        if agent_name in self.agent_profiles:
            profile = self.agent_profiles[agent_name]
            avg_response_time = profile["avg_response_time"]
            success_rate = profile["success_rate"]
            avg_cost = profile["avg_cost"]
        else:
            # Perfiles por defecto por tipo de agente
            avg_response_time, success_rate, avg_cost = self._get_default_profile(agent_name)
        
        # Ajustar por complejidad del contexto
        complexity_factor = 1.0 + (complexity_score - 0.5) * 0.5
        
        predicted_time = avg_response_time * complexity_factor
        
        # Factors adicionales basados en contexto
        if context.get("user_tier") == "premium":
            success_rate = min(success_rate * 1.1, 1.0)  # Premium users get better service
            predicted_time *= 0.9  # Prioridad para premium
        
        if context.get("language_complexity", 0.5) > 0.7:
            predicted_time *= 1.2  # Más tiempo para язы сложный
        
        return {
            "expected_response_time": max(0.5, predicted_time),
            "expected_success_probability": max(0.1, min(success_rate, 1.0)),
            "expected_cost": max(0.01, avg_cost * complexity_factor)
        }
    
    def _get_default_profile(self, agent_name: str) -> Tuple[float, float, float]:
        """Obtener perfil por defecto basado en nombre del agente"""
        name_lower = agent_name.lower()
        
        if "reasoner" in name_lower:
            return 2.0, 0.88, 0.08
        elif "planner" in name_lower:
            return 1.5, 0.92, 0.06
        elif "executor" in name_lower:
            return 3.0, 0.85, 0.12
        elif "verifier" in name_lower:
            return 1.0, 0.95, 0.04
        elif "memory" in name_lower:
            return 0.5, 0.98, 0.02
        elif "database" in name_lower:
            return 1.8, 0.90, 0.07
        elif "search" in name_lower:
            return 2.2, 0.87, 0.09
        elif "web" in name_lower:
            return 4.0, 0.80, 0.15
        elif "git" in name_lower:
            return 1.2, 0.94, 0.05
        else:
            return 2.0, 0.85, 0.10  # Default


class SimpleCostOptimizer:
    """Optimizador de costos simplificado"""
    
    def __init__(self):
        self.objective_weights = {
            OptimizationObjective.SPEED: {"time": 0.7, "success": 0.2, "cost": 0.1},
            OptimizationObjective.ACCURACY: {"time": 0.1, "success": 0.8, "cost": 0.1},
            OptimizationObjective.COST: {"time": 0.2, "success": 0.2, "cost": 0.6},
            OptimizationObjective.RELIABILITY: {"time": 0.2, "success": 0.7, "cost": 0.1},
            OptimizationObjective.BALANCED: {"time": 0.3, "success": 0.4, "cost": 0.3}
        }
        self.logger = logging.getLogger("mcp.router.simple_optimizer")
    
    def calculate_composite_score(
        self,
        predictions: Dict[str, Dict[str, float]],
        context: RoutingContext,
        objective: OptimizationObjective
    ) -> Tuple[str, float]:
        """Calcular score compuesto para optimización multi-objetivo"""
        
        scores = {}
        weights = self.objective_weights.get(objective, self.objective_weights[OptimizationObjective.BALANCED])
        
        for agent_name, pred in predictions.items():
            score = self._calculate_single_score(pred, context, weights)
            scores[agent_name] = score
        
        # Seleccionar mejor agente
        best_agent = max(scores.keys(), key=lambda x: scores[x])
        return best_agent, scores[best_agent]
    
    def _calculate_single_score(
        self,
        predictions: Dict[str, float],
        context: RoutingContext,
        weights: Dict[str, float]
    ) -> float:
        """Calcular score para un agente específico"""
        
        response_time = predictions["expected_response_time"]
        success_prob = predictions["expected_success_probability"]
        cost = predictions["expected_cost"]
        
        # Normalización (invertir tiempo y costo para que menor sea mejor)
        time_score = 1.0 / (1.0 + response_time)
        success_score = success_prob
        cost_score = 1.0 / (1.0 + cost)
        
        # Aplicar restricciones de contexto
        penalty = 1.0
        if context.time_constraints:
            max_time = context.time_constraints.get("max_seconds", float('inf'))
            if response_time > max_time:
                penalty *= 0.1  # Penalización severa
        
        if context.budget_constraints:
            max_cost = context.budget_constraints.get("max_cost", float('inf'))
            if cost > max_cost:
                penalty *= 0.1  # Penalización severa
        
        # Score compuesto
        composite_score = (
            weights["time"] * time_score +
            weights["success"] * success_score +
            weights["cost"] * cost_score
        ) * penalty
        
        return composite_score


class SimpleEmbeddingService:
    """Servicio de embeddings simplificado"""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.cache = {}
        self.logger = logging.getLogger("mcp.router.simple_embeddings")
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generar embeddings para lista de textos"""
        embeddings = []
        
        for text in texts:
            embedding = await self._generate_single_embedding(text)
            embeddings.append(embedding)
        
        return embeddings
    
    async def _generate_single_embedding(self, text: str) -> List[float]:
        """Generar embedding para un texto individual"""
        # Hash del texto para cache
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        if text_hash in self.cache:
            return self.cache[text_hash]
        
        # Generar embedding determinístico basado en hash
        seed = int(text_hash[:8], 16) % (2**32)
        np.random.seed(seed)
        
        # Generar vector normalizado
        embedding = np.random.normal(0, 1, self.dimension)
        embedding = embedding / np.linalg.norm(embedding)
        embedding_list = embedding.tolist()
        
        # Cachear resultado
        self.cache[text_hash] = embedding_list
        
        # Limitar cache size
        if len(self.cache) > 1000:
            cache_items = list(self.cache.items())
            self.cache = dict(cache_items[-500:])
        
        return embedding_list
    
    async def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calcular similitud coseno entre dos embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0


class MockAgentWrapper:
    """Mock agent wrapper para demostración"""
    
    def __init__(self, agent_name: str, capabilities: List[str]):
        self.agent_name = agent_name
        self.capabilities = capabilities
        self.max_concurrent = 3
        self.timeout_seconds = 60
        self.status = "ready"
        self.current_operations = 0
        self.metrics = {
            "response_times": [],
            "success_rate": 0.9
        }
    
    async def ensure_initialized(self) -> None:
        await asyncio.sleep(0.01)  # Simular inicialización
    
    @property
    def is_ready(self) -> bool:
        return self.status == "ready"
    
    @property
    def is_busy(self) -> bool:
        return self.current_operations >= self.max_concurrent
    
    def get_capabilities(self) -> List[str]:
        return self.capabilities.copy()
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "metrics": self.metrics.copy(),
            "success_rate": self.metrics["success_rate"]
        }
    
    async def process_request(self, request: dict, context: dict = None) -> dict:
        return {
            "status": "success",
            "result": f"Processed by {self.agent_name}",
            "request_id": request.get("id", "unknown")
        }


class SimpleIntelligentRouter:
    """Router inteligente simplificado sin dependencias pesadas"""
    
    def __init__(self):
        self.embedding_service = SimpleEmbeddingService()
        self.predictor = SimplePerformancePredictor()
        self.cost_optimizer = SimpleCostOptimizer()
        
        # Estado del router
        self.agent_registry = {}
        self.usage_history = deque(maxlen=1000)
        self.adaptation_enabled = True
        
        # Configuración de estrategias
        self.strategy_weights = {
            RoutingStrategy.AI_OPTIMIZED: 0.4,
            RoutingStrategy.SEMANTIC_MATCHING: 0.3,
            RoutingStrategy.PERFORMANCE_BASED: 0.2,
            RoutingStrategy.LOAD_BALANCED: 0.1
        }
        
        # Lock para thread safety
        self.lock = threading.RLock()
        
        # Setup logging
        self.logger = logging.getLogger("mcp.router.simple")
        
        self.logger.info("Simple Intelligent Router inicializado")
    
    def register_agent(self, agent_wrapper) -> None:
        """Registrar agente en el router"""
        with self.lock:
            self.agent_registry[agent_wrapper.agent_name] = agent_wrapper
            self.logger.info(f"Agente registrado: {agent_wrapper.agent_name}")
    
    async def generate_request_embedding(self, request: Dict[str, Any]) -> List[float]:
        """Generar embedding semántico para request"""
        try:
            # Construir texto descriptivo del request
            request_text = self._build_request_text(request)
            
            # Generar embedding
            embeddings = await self.embedding_service.generate_embeddings([request_text])
            return embeddings[0] if embeddings else []
            
        except Exception as e:
            self.logger.error(f"Error generando embedding: {e}")
            return []
    
    def _build_request_text(self, request: Dict[str, Any]) -> str:
        """Construir texto descriptivo del request para embeddings"""
        parts = []
        
        if "query" in request:
            parts.append(request["query"])
        if "task" in request:
            parts.append(request["task"])
        if "description" in request:
            parts.append(request["description"])
        if "capability" in request:
            parts.append(request["capability"])
        
        return " ".join(parts)
    
    async def make_routing_decision(
        self,
        request: Dict[str, Any],
        context: RoutingContext,
        strategy: Optional[RoutingStrategy] = None,
        objective: Optional[OptimizationObjective] = None
    ) -> RoutingDecision:
        """Tomar decisión de routing inteligente"""
        
        with self.lock:
            # Generar embedding semántico si no existe
            if not context.embedding_vector:
                context.embedding_vector = await self.generate_request_embedding(request)
            
            # Seleccionar estrategia
            if strategy is None:
                strategy = self._select_strategy(context)
            
            if objective is None:
                objective = OptimizationObjective.BALANCED
            
            self.logger.info(f"Usando estrategia: {strategy.value}")
            
            # Ejecutar estrategia
            if strategy == RoutingStrategy.AI_OPTIMIZED:
                return await self._ai_optimized_routing(request, context, objective)
            elif strategy == RoutingStrategy.SEMANTIC_MATCHING:
                return await self._semantic_matching_routing(request, context)
            elif strategy == RoutingStrategy.PERFORMANCE_BASED:
                return await self._performance_based_routing(request, context, objective)
            elif strategy == RoutingStrategy.LOAD_BALANCED:
                return await self._load_balanced_routing(request, context)
            else:
                return await self._static_routing(request, context)
    
    def _select_strategy(self, context: RoutingContext) -> RoutingStrategy:
        """Seleccionar estrategia basada en contexto"""
        if context.embedding_vector and len(self.agent_registry) > 0:
            return RoutingStrategy.AI_OPTIMIZED
        elif context.complexity_score > 0.7:
            return RoutingStrategy.PERFORMANCE_BASED
        else:
            return RoutingStrategy.SEMANTIC_MATCHING
    
    async def _ai_optimized_routing(
        self,
        request: Dict[str, Any],
        context: RoutingContext,
        objective: OptimizationObjective
    ) -> RoutingDecision:
        """Routing optimizado con ML simplificado"""
        
        # Obtener candidatos de agentes
        candidates = self._get_candidate_agents(request, context)
        
        if not candidates:
            raise MCPCoreException("No hay agentes candidatos disponibles")
        
        # Predecir performance de cada candidato
        predictions = {}
        for agent_name in candidates:
            try:
                agent = self.agent_registry[agent_name]
                context_features = {
                    "user_tier": context.user_preferences.get("tier", "standard") if context.user_preferences else "standard",
                    "language_complexity": 0.5
                }
                
                pred = self.predictor.predict_performance(
                    agent_name,
                    request.get("capability", "unknown"),
                    context_features,
                    context.complexity_score
                )
                
                predictions[agent_name] = pred
                
            except Exception as e:
                self.logger.warning(f"Error prediciendo performance para {agent_name}: {e}")
                continue
        
        if not predictions:
            # Fallback a estrategia simple
            return await self._semantic_matching_routing(request, context)
        
        # Optimización multi-objetivo
        best_agent, best_score = self.cost_optimizer.calculate_composite_score(
            predictions, context, objective
        )
        
        # Obtener alternativas
        sorted_agents = sorted(
            predictions.keys(),
            key=lambda x: self.cost_optimizer.calculate_composite_score(
                {x: predictions[x]}, context, objective
            ),
            reverse=True
        )
        
        alternatives = [(agent, predictions[agent]["expected_success_probability"]) 
                       for agent in sorted_agents[1:4]]
        
        reasoning = f"AI-optimizado para {objective.value}: {best_agent}"
        
        return RoutingDecision(
            agent_name=best_agent,
            confidence=best_score,
            expected_performance=predictions.get(best_agent, {}),
            strategy_used=RoutingStrategy.AI_OPTIMIZED,
            reasoning=reasoning,
            alternatives=alternatives
        )
    
    async def _semantic_matching_routing(
        self,
        request: Dict[str, Any],
        context: RoutingContext
    ) -> RoutingDecision:
        """Routing basado en matching semántico"""
        
        request_embedding = context.embedding_vector
        if not request_embedding:
            return await self._static_routing(request, context)
        
        agent_similarities = {}
        
        # Calcular similitud con agentes
        for agent_name, agent in self.agent_registry.items():
            if not agent.is_ready:
                continue
            
            # Generar embedding del agente basado en capacidades
            agent_text = f"Agent {agent_name} capabilities: " + " ".join(agent.get_capabilities())
            
            try:
                agent_embeddings = await self.embedding_service.generate_embeddings([agent_text])
                agent_embedding = agent_embeddings[0] if agent_embeddings else []
                
                if agent_embedding:
                    similarity = await self.embedding_service.cosine_similarity(
                        request_embedding, agent_embedding
                    )
                    agent_similarities[agent_name] = similarity
                    
            except Exception as e:
                self.logger.warning(f"Error calculando similitud para {agent_name}: {e}")
        
        if not agent_similarities:
            return await self._static_routing(request, context)
        
        # Seleccionar agente más similar
        best_agent = max(agent_similarities.keys(), key=lambda x: agent_similarities[x])
        best_similarity = agent_similarities[best_agent]
        
        # Alternativas
        sorted_agents = sorted(
            agent_similarities.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        alternatives = [(agent, sim) for agent, sim in sorted_agents[1:4]]
        
        reasoning = f"Matching semántico: similitud {best_similarity:.3f}"
        
        return RoutingDecision(
            agent_name=best_agent,
            confidence=best_similarity,
            expected_performance={
                "expected_success_probability": best_similarity,
                "expected_response_time": 2.0,
                "expected_cost": 0.2
            },
            strategy_used=RoutingStrategy.SEMANTIC_MATCHING,
            reasoning=reasoning,
            alternatives=alternatives
        )
    
    async def _performance_based_routing(
        self,
        request: Dict[str, Any],
        context: RoutingContext,
        objective: OptimizationObjective
    ) -> RoutingDecision:
        """Routing basado en performance histórica"""
        
        agent_scores = {}
        
        for agent_name, agent in self.agent_registry.items():
            if not agent.is_ready:
                continue
            
            # Obtener métricas históricas del predictor
            if agent_name in self.predictor.agent_profiles:
                profile = self.predictor.agent_profiles[agent_name]
                success_rate = profile["success_rate"]
                avg_response_time = profile["avg_response_time"]
            else:
                success_rate = 0.85
                avg_response_time = 2.0
            
            # Calcular score basado en objetivo
            if objective == OptimizationObjective.SPEED:
                score = (1.0 / (1.0 + avg_response_time)) * 0.5 + success_rate * 0.5
            elif objective == OptimizationObjective.ACCURACY:
                score = success_rate * 0.8 + (1.0 / (1.0 + avg_response_time)) * 0.2
            else:
                score = success_rate * 0.6 + (1.0 / (1.0 + avg_response_time)) * 0.4
            
            agent_scores[agent_name] = score
        
        if not agent_scores:
            return await self._static_routing(request, context)
        
        # Seleccionar mejor agente
        best_agent = max(agent_scores.keys(), key=lambda x: agent_scores[x])
        best_score = agent_scores[best_agent]
        
        # Alternativas
        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
        alternatives = [(agent, score) for agent, score in sorted_agents[1:4]]
        
        reasoning = f"Performance-based para {objective.value}"
        
        return RoutingDecision(
            agent_name=best_agent,
            confidence=best_score,
            expected_performance={
                "expected_success_probability": best_score,
                "expected_response_time": 2.0,
                "expected_cost": 0.2
            },
            strategy_used=RoutingStrategy.PERFORMANCE_BASED,
            reasoning=reasoning,
            alternatives=alternatives
        )
    
    async def _load_balanced_routing(
        self,
        request: Dict[str, Any],
        context: RoutingContext
    ) -> RoutingDecision:
        """Routing con balanceador de carga"""
        
        agent_loads = {}
        
        for agent_name, agent in self.agent_registry.items():
            if not agent.is_ready:
                continue
            
            # Calcular utilización (simplificado)
            utilization = agent.current_operations / agent.max_concurrent
            agent_loads[agent_name] = 1.0 - utilization  # Menor utilización = mejor
        
        if not agent_loads:
            return await self._static_routing(request, context)
        
        # Seleccionar agente con menor carga
        best_agent = max(agent_loads.keys(), key=lambda x: agent_loads[x])
        best_load = agent_loads[best_agent]
        
        # Alternativas
        sorted_agents = sorted(agent_loads.items(), key=lambda x: x[1], reverse=True)
        alternatives = [(agent, load) for agent, load in sorted_agents[1:4]]
        
        reasoning = f"Balanceador de carga: utilización {1-best_load:.2%}"
        
        return RoutingDecision(
            agent_name=best_agent,
            confidence=best_load,
            expected_performance={
                "expected_success_probability": 0.8,
                "expected_response_time": 1.5,
                "expected_cost": 0.1
            },
            strategy_used=RoutingStrategy.LOAD_BALANCED,
            reasoning=reasoning,
            alternatives=alternatives
        )
    
    async def _static_routing(
        self,
        request: Dict[str, Any],
        context: RoutingContext
    ) -> RoutingDecision:
        """Routing estático (fallback)"""
        
        ready_agents = [
            name for name, agent in self.agent_registry.items() 
            if agent.is_ready
        ]
        
        if not ready_agents:
            raise MCPCoreException("No hay agentes disponibles")
        
        # Seleccionar primer agente disponible
        best_agent = ready_agents[0]
        
        return RoutingDecision(
            agent_name=best_agent,
            confidence=0.5,
            expected_performance={
                "expected_success_probability": 0.7,
                "expected_response_time": 2.0,
                "expected_cost": 0.2
            },
            strategy_used=RoutingStrategy.STATIC,
            reasoning="Routing estático (fallback)",
            alternatives=[(agent, 0.5) for agent in ready_agents[1:3]]
        )
    
    def _get_candidate_agents(
        self,
        request: Dict[str, Any],
        context: RoutingContext
    ) -> List[str]:
        """Obtener candidatos de agentes basado en request y contexto"""
        
        candidates = []
        
        # Filtrar por disponibilidad
        for agent_name, agent in self.agent_registry.items():
            if agent.is_ready and not agent.is_busy:
                candidates.append(agent_name)
        
        # Filtrar por capacidades requeridas si están especificadas
        required_capability = request.get("capability")
        if required_capability:
            filtered_candidates = []
            for agent_name in candidates:
                agent = self.agent_registry[agent_name]
                capabilities = agent.get_capabilities()
                if required_capability in capabilities:
                    filtered_candidates.append(agent_name)
            candidates = filtered_candidates
        
        return candidates[:10]  # Limitar a top 10 candidatos
    
    def record_routing_result(
        self,
        decision: RoutingDecision,
        actual_performance: Dict[str, float],
        context: RoutingContext
    ) -> None:
        """Registrar resultado para aprendizaje"""
        
        # Registrar en histórico
        self.usage_history.append({
            "timestamp": datetime.now(),
            "decision": decision,
            "actual_performance": actual_performance,
            "context": context
        })
        
        # Crear muestra de entrenamiento para ML
        if self.adaptation_enabled:
            # Seleccionar capacidades del agente elegido
            if decision.agent_name in self.agent_registry:
                agent = self.agent_registry[decision.agent_name]
                capabilities = agent.get_capabilities()
                primary_capability = capabilities[0] if capabilities else "unknown"
                
                # Crear métrica para entrenamiento
                metrics = AgentMetrics(
                    agent_name=decision.agent_name,
                    capability=primary_capability,
                    response_time=actual_performance.get("response_time", 1.0),
                    success=actual_performance.get("success_rate", 1.0) > 0.5,
                    cost=actual_performance.get("cost", 0.1),
                    user_satisfaction=actual_performance.get("user_satisfaction"),
                    timestamp=datetime.now(),
                    context_features={
                        "request_type": context.request_type,
                        "complexity": context.complexity_score,
                        "user_tier": context.user_preferences.get("tier", "standard") if context.user_preferences else "standard",
                        "language": context.language
                    },
                    complexity_score=context.complexity_score
                )
                
                # Agregar al predictor
                self.predictor.add_training_sample(metrics)
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas del router"""
        
        strategy_usage = defaultdict(int)
        agent_usage = defaultdict(int)
        recent_decisions = list(self.usage_history)[-100:]  # Últimas 100
        
        for entry in recent_decisions:
            decision = entry["decision"]
            strategy_usage[decision.strategy_used.value] += 1
            agent_usage[decision.agent_name] += 1
        
        return {
            "total_routing_decisions": len(self.usage_history),
            "strategy_usage": dict(strategy_usage),
            "agent_usage": dict(agent_usage),
            "registered_agents": len(self.agent_registry),
            "available_agents": len([
                name for name, agent in self.agent_registry.items() 
                if agent.is_ready
            ]),
            "ml_model_trained": len(self.predictor.agent_profiles) > 0,
            "agent_profiles": len(self.predictor.agent_profiles)
        }
    
    async def adapt_routing_parameters(self) -> None:
        """Adaptar parámetros de routing basado en performance"""
        
        if not self.adaptation_enabled:
            return
        
        # Analizar últimos resultados
        recent_performance = defaultdict(list)
        
        for entry in list(self.usage_history)[-50:]:  # Últimos 50
            decision = entry["decision"]
            actual = entry["actual_performance"]
            recent_performance[decision.strategy_used.value].append(
                actual.get("success_rate", 0.0)
            )
        
        # Ajustar pesos de estrategias basado en performance
        for strategy, performances in recent_performance.items():
            if len(performances) >= 5:  # Mínimo de samples
                avg_performance = sum(performances) / len(performances)
                if avg_performance > 0.9:  # Performance muy buena
                    # Aumentar peso
                    current_weight = self.strategy_weights.get(
                        RoutingStrategy(strategy), 0.1
                    )
                    self.strategy_weights[RoutingStrategy(strategy)] = min(
                        current_weight * 1.1, 0.6
                    )
                elif avg_performance < 0.7:  # Performance baja
                    # Reducir peso
                    current_weight = self.strategy_weights.get(
                        RoutingStrategy(strategy), 0.1
                    )
                    self.strategy_weights[RoutingStrategy(strategy)] = max(
                        current_weight * 0.9, 0.05
                    )
        
        self.logger.info("Parámetros de routing adaptados")
    
    def enable_adaptation(self, enabled: bool = True) -> None:
        """Habilitar/deshabilitar adaptación automática"""
        self.adaptation_enabled = enabled
        self.logger.info(f"Adaptación automática {'habilitada' if enabled else 'deshabilitada'}")


# Instancia global del router
intelligent_router = SimpleIntelligentRouter()