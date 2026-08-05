"""
AI-Powered Intelligent Router
Sistema de routing inteligente con Machine Learning para optimización de agentes
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import logging
import json
import pickle
import hashlib
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import threading
import time
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

from ..core.config import settings
from ..core.exceptions import MCPCoreException, AgentException
from ..services.embedding_service import EmbeddingService
from ..agents.base_agent_wrapper import BaseAgentWrapper, AgentCapability, AgentStatus


class RoutingStrategy(Enum):
    """Estrategias de routing disponibles"""
    STATIC = "static"
    PERFORMANCE_BASED = "performance_based"
    SEMANTIC_MATCHING = "semantic_matching"
    LOAD_BALANCED = "load_balanced"
    CONTEXT_AWARE = "context_aware"
    AI_OPTIMIZED = "ai_optimized"  # Estrategia principal con ML


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


class ABTestManager:
    """Gestor de experimentos A/B para routing strategies"""
    
    def __init__(self, max_experiments: int = 5):
        self.experiments = {}
        self.max_experiments = max_experiments
        self.logger = logging.getLogger("mcp.router.abtest")
    
    def create_experiment(
        self,
        name: str,
        variants: Dict[str, RoutingStrategy],
        traffic_split: Dict[str, float],
        metric_to_optimize: str = "success_rate",
        duration_days: int = 7
    ) -> str:
        """Crear nuevo experimento A/B"""
        experiment_id = hashlib.md5(f"{name}_{time.time()}".encode()).hexdigest()[:8]
        
        # Validar que las proporciones sumen 1
        total_split = sum(traffic_split.values())
        if abs(total_split - 1.0) > 0.001:
            raise ValueError("Traffic split debe sumar 1.0")
        
        self.experiments[experiment_id] = {
            "name": name,
            "variants": variants,
            "traffic_split": traffic_split,
            "metric_to_optimize": metric_to_optimize,
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=duration_days),
            "results": defaultdict(lambda: {"total": 0, "successes": 0, "metrics": []}),
            "active": True
        }
        
        self.logger.info(f"Experimento A/B creado: {name} (ID: {experiment_id})")
        return experiment_id
    
    def get_strategy_for_user(
        self,
        experiment_id: str,
        user_id: str
    ) -> Optional[RoutingStrategy]:
        """Obtener estrategia para usuario basado en A/B test"""
        if experiment_id not in self.experiments:
            return None
        
        experiment = self.experiments[experiment_id]
        if not experiment["active"]:
            return None
        
        # Hash user_id para asignación consistente
        user_hash = int(hashlib.md5(user_id.encode()).hexdigest()[:8], 16)
        
        # Asignar variante basado en hash
        cumulative = 0
        for variant_name, split in experiment["traffic_split"].items():
            cumulative += split
            if (user_hash % 10000) / 10000 < cumulative:
                return experiment["variants"][variant_name]
        
        # Fallback a primera variante
        return list(experiment["variants"].values())[0]
    
    def record_result(
        self,
        experiment_id: str,
        user_id: str,
        strategy: RoutingStrategy,
        metric_value: float,
        additional_metrics: Optional[Dict] = None
    ) -> None:
        """Registrar resultado de experimento"""
        if experiment_id not in self.experiments:
            return
        
        strategy_key = strategy.value
        results = self.experiments[experiment_id]["results"]
        results[strategy_key]["total"] += 1
        results[strategy_key]["successes"] += 1 if metric_value > 0.5 else 0
        results[strategy_key]["metrics"].append(metric_value)
        
        if additional_metrics:
            results[strategy_key]["metrics"].append(
                additional_metrics.get("composite_score", metric_value)
            )
    
    def get_experiment_results(self, experiment_id: str) -> Dict[str, Any]:
        """Obtener resultados de experimento"""
        if experiment_id not in self.experiments:
            return {}
        
        experiment = self.experiments[experiment_id]
        results = {}
        
        for strategy_key, data in experiment["results"].items():
            if data["total"] > 0:
                results[strategy_key] = {
                    "success_rate": data["successes"] / data["total"],
                    "sample_size": data["total"],
                    "avg_metric": np.mean(data["metrics"]) if data["metrics"] else 0,
                    "std_metric": np.std(data["metrics"]) if data["metrics"] else 0
                }
        
        return results


class PerformancePredictor:
    """Modelo de ML para predicción de performance de agentes"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = []
        self.is_trained = False
        self.training_data = deque(maxlen=10000)  # Máximo 10k registros
        self.lock = threading.Lock()
        
        self.logger = logging.getLogger("mcp.router.ml.predictor")
        
        if model_path:
            self.load_model(model_path)
    
    def add_training_sample(self, metrics: AgentMetrics) -> None:
        """Agregar muestra de entrenamiento"""
        with self.lock:
            self.training_data.append(metrics)
            
            # Auto-entrenar si hay suficientes datos
            if len(self.training_data) >= 100 and not self.is_trained:
                asyncio.create_task(self._train_model())
    
    def _extract_features(self, metrics: AgentMetrics) -> np.ndarray:
        """Extraer features para ML de métricas de agente"""
        features = []
        
        # Features temporales
        hour = metrics.timestamp.hour
        features.extend([
            hour / 24.0,  # Normalized hour
            np.sin(2 * np.pi * hour / 24),  # Cyclical encoding
            np.cos(2 * np.pi * hour / 24)
        ])
        
        # Features de contexto
        context = metrics.context_features
        features.extend([
            metrics.complexity_score,
            context.get("user_tier", "standard") == "premium",
            context.get("request_size", 0) / 10000.0,  # Normalized request size
            context.get("language_complexity", 0.5)
        ])
        
        # Features de capacidades del agente
        agent_name_features = hashlib.md5(metrics.agent_name.encode()).digest()
        features.extend([b / 255.0 for b in agent_name_features[:5]])
        
        # Features de capacidad específica
        capability_features = hashlib.md5(metrics.capability.encode()).digest()
        features.extend([b / 255.0 for b in capability_features[:3]])
        
        return np.array(features)
    
    async def _train_model(self) -> None:
        """Entrenar modelo ML con datos actuales"""
        with self.lock:
            if len(self.training_data) < 50:
                return
            
            try:
                # Preparar datos
                X, y_response_time, y_success = [], [], []
                
                for metrics in self.training_data:
                    features = self._extract_features(metrics)
                    X.append(features)
                    y_response_time.append(metrics.response_time)
                    y_success.append(1.0 if metrics.success else 0.0)
                
                X = np.array(X)
                y_response_time = np.array(y_response_time)
                y_success = np.array(y_success)
                
                # Escalar features
                X_scaled = self.scaler.fit_transform(X)
                
                # Entrenar modelos
                self.model = {
                    "response_time": RandomForestRegressor(
                        n_estimators=100, 
                        random_state=42,
                        max_depth=10
                    ),
                    "success_probability": GradientBoostingRegressor(
                        n_estimators=100,
                        random_state=42,
                        learning_rate=0.1
                    )
                }
                
                self.model["response_time"].fit(X_scaled, y_response_time)
                self.model["success_probability"].fit(X_scaled, y_success)
                
                self.feature_columns = [
                    "hour_norm", "hour_sin", "hour_cos", "complexity_score",
                    "is_premium", "request_size_norm", "language_complexity",
                    "agent_name_1", "agent_name_2", "agent_name_3", 
                    "agent_name_4", "agent_name_5", "capability_1",
                    "capability_2", "capability_3"
                ]
                
                self.is_trained = True
                self.logger.info("Modelo ML entrenado exitosamente")
                
            except Exception as e:
                self.logger.error(f"Error entrenando modelo ML: {e}")
    
    def predict_performance(
        self,
        agent_name: str,
        capability: str,
        context: Dict[str, Any],
        complexity_score: float = 0.5
    ) -> Dict[str, float]:
        """Predecir performance de agente"""
        if not self.is_trained:
            # Predicción simple basada en datos históricos
            return self._fallback_prediction(agent_name, capability, complexity_score)
        
        try:
            # Crear métrica dummy para feature extraction
            dummy_metrics = AgentMetrics(
                agent_name=agent_name,
                capability=capability,
                response_time=1.0,
                success=True,
                cost=0.0,
                user_satisfaction=None,
                timestamp=datetime.now(),
                context_features=context,
                complexity_score=complexity_score
            )
            
            features = self._extract_features(dummy_metrics).reshape(1, -1)
            features_scaled = self.scaler.transform(features)
            
            # Predicciones
            predicted_time = self.model["response_time"].predict(features_scaled)[0]
            predicted_success = self.model["success_probability"].predict(features_scaled)[0]
            
            # Clamp predictions to reasonable ranges
            predicted_time = max(0.1, min(predicted_time, 300))
            predicted_success = max(0.0, min(predicted_success, 1.0))
            
            return {
                "expected_response_time": float(predicted_time),
                "expected_success_probability": float(predicted_success),
                "expected_cost": self._estimate_cost(predicted_time, predicted_success)
            }
            
        except Exception as e:
            self.logger.error(f"Error en predicción ML: {e}")
            return self._fallback_prediction(agent_name, capability, complexity_score)
    
    def _fallback_prediction(
        self,
        agent_name: str,
        capability: str,
        complexity_score: float
    ) -> Dict[str, float]:
        """Predicción de fallback sin ML"""
        # Predicción heurística simple
        base_time = {
            "reasoner": 2.0,
            "planner": 1.5,
            "executor": 3.0,
            "verifier": 1.0,
            "memory": 0.5
        }
        
        agent_type = next((t for t in base_time if t in agent_name.lower()), "executor")
        expected_time = base_time.get(agent_type, 2.0) * (1 + complexity_score)
        
        return {
            "expected_response_time": expected_time,
            "expected_success_probability": 0.85,
            "expected_cost": expected_time * 0.1
        }
    
    def _estimate_cost(self, response_time: float, success_probability: float) -> float:
        """Estimar costo basado en performance"""
        base_cost = response_time * 0.05  # Costo base por segundo
        success_bonus = success_probability * 0.02  # Bonus por alta probabilidad de éxito
        return base_cost + success_bonus
    
    def save_model(self, path: str) -> None:
        """Guardar modelo entrenado"""
        if self.is_trained:
            model_data = {
                "model": self.model,
                "scaler": self.scaler,
                "feature_columns": self.feature_columns,
                "is_trained": self.is_trained
            }
            
            with open(path, "wb") as f:
                pickle.dump(model_data, f)
            
            self.logger.info(f"Modelo guardado en {path}")
    
    def load_model(self, path: str) -> None:
        """Cargar modelo entrenado"""
        try:
            with open(path, "rb") as f:
                model_data = pickle.load(f)
            
            self.model = model_data["model"]
            self.scaler = model_data["scaler"]
            self.feature_columns = model_data["feature_columns"]
            self.is_trained = model_data["is_trained"]
            
            self.logger.info(f"Modelo cargado desde {path}")
            
        except Exception as e:
            self.logger.error(f"Error cargando modelo: {e}")


class CostOptimizer:
    """Optimizador de costos para routing"""
    
    def __init__(self):
        self.cost_weights = {
            "response_time": 0.3,
            "success_probability": 0.4,
            "actual_cost": 0.3
        }
        self.agent_cost_profiles = {}
        self.logger = logging.getLogger("mcp.router.cost")
    
    def calculate_composite_score(
        self,
        predictions: Dict[str, Dict[str, float]],
        context: RoutingContext,
        objective: OptimizationObjective
    ) -> Tuple[str, float]:
        """Calcular score compuesto para optimización multi-objetivo"""
        
        scores = {}
        for agent_name, pred in predictions.items():
            score = self._calculate_single_score(pred, context, objective)
            scores[agent_name] = score
        
        # Seleccionar mejor agente
        best_agent = max(scores.keys(), key=lambda x: scores[x])
        return best_agent, scores[best_agent]
    
    def _calculate_single_score(
        self,
        predictions: Dict[str, float],
        context: RoutingContext,
        objective: OptimizationObjective
    ) -> float:
        """Calcular score para un agente específico"""
        
        response_time = predictions["expected_response_time"]
        success_prob = predictions["expected_success_probability"]
        cost = predictions["expected_cost"]
        
        # Normalización para comparación (invertir tiempo y costo)
        time_score = 1.0 / (1.0 + response_time)
        success_score = success_prob
        cost_score = 1.0 / (1.0 + cost)
        
        # Pesos según objetivo
        if objective == OptimizationObjective.SPEED:
            weights = {"time": 0.7, "success": 0.2, "cost": 0.1}
        elif objective == OptimizationObjective.ACCURACY:
            weights = {"time": 0.1, "success": 0.8, "cost": 0.1}
        elif objective == OptimizationObjective.COST:
            weights = {"time": 0.2, "success": 0.2, "cost": 0.6}
        elif objective == OptimizationObjective.RELIABILITY:
            weights = {"time": 0.2, "success": 0.7, "cost": 0.1}
        else:  # BALANCED
            weights = {"time": 0.3, "success": 0.4, "cost": 0.3}
        
        # Considerar restricciones de contexto
        if context.time_constraints:
            max_time = context.time_constraints.get("max_seconds", float('inf'))
            if response_time > max_time:
                time_score *= 0.1  # Penalización severa
        
        if context.budget_constraints:
            max_cost = context.budget_constraints.get("max_cost", float('inf'))
            if cost > max_cost:
                cost_score *= 0.1  # Penalización severa
        
        # Score compuesto
        composite_score = (
            weights["time"] * time_score +
            weights["success"] * success_score +
            weights["cost"] * cost_score
        )
        
        return composite_score


class IntelligentRouter:
    """Router inteligente principal con AI/ML"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.predictor = PerformancePredictor()
        self.cost_optimizer = CostOptimizer()
        self.ab_test_manager = ABTestManager()
        
        # Estado del router
        self.agent_registry = {}
        self.usage_history = deque(maxlen=50000)
        self.routing_cache = {}
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
        self.logger = logging.getLogger("mcp.router.intelligent")
        
        self.logger.info("Intelligent Router inicializado")
    
    def register_agent(self, agent_wrapper: BaseAgentWrapper) -> None:
        """Registrar agente en el router"""
        with self.lock:
            self.agent_registry[agent_wrapper.agent_name] = agent_wrapper
            self.logger.info(f"Agente registrado: {agent_wrapper.agent_name}")
    
    def get_agent_capabilities(self, agent_name: str) -> List[AgentCapability]:
        """Obtener capacidades de un agente"""
        if agent_name in self.agent_registry:
            return self.agent_registry[agent_name].get_capabilities()
        return []
    
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
        if "context" in request:
            context = request["context"]
            if isinstance(context, dict):
                for key, value in context.items():
                    parts.append(f"{key}: {value}")
        
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
        # Lógica para seleccionar estrategia óptima
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
        """Routing optimizado con AI/ML"""
        
        # Obtener candidatos de agentes
        candidates = self._get_candidate_agents(request, context)
        
        if not candidates:
            raise MCPCoreException("No hay agentes candidatos disponibles")
        
        # Predecir performance de cada candidato
        predictions = {}
        for agent_name in candidates:
            agent = self.agent_registry[agent_name]
            capabilities = agent.get_capabilities()
            
            # Predecir para cada capacidad relevante
            for capability in capabilities:
                try:
                    pred = self.predictor.predict_performance(
                        agent_name,
                        capability.value,
                        context.context_features or {},
                        context.complexity_score
                    )
                    
                    predictions[agent_name] = pred
                    break  # Tomar primera capacidad
                    
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
            agent_text = f"Agent {agent_name} capabilities: " + " ".join([
                cap.value for cap in agent.get_capabilities()
            ])
            
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
        
        # Obtener alternativas
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
            
            # Obtener métricas históricas
            metrics = agent.get_status()
            success_rate = metrics["success_rate"]
            avg_response_time = metrics["metrics"]["response_times"]
            
            if isinstance(avg_response_time, list) and avg_response_time:
                avg_response_time = sum(avg_response_time) / len(avg_response_time)
            else:
                avg_response_time = 2.0  # Default
            
            # Calcular score basado en objetivo
            if objective == OptimizationObjective.SPEED:
                score = 1.0 / (1.0 + avg_response_time) * 0.5 + success_rate * 0.5
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
            
            utilization = agent.utilization
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
                capabilities = [cap.value for cap in agent.get_capabilities()]
                if required_capability in capabilities:
                    filtered_candidates.append(agent_name)
            candidates = filtered_candidates
        
        # Filtrar por restricciones de contexto
        if context.budget_constraints:
            max_cost = context.budget_constraints.get("max_cost", float('inf'))
            # Filtrar agentes que típicamente exceden el presupuesto
            # (implementación simplificada)
        
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
                primary_capability = capabilities[0].value if capabilities else "unknown"
                
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
    
    def create_ab_test(
        self,
        name: str,
        strategy_a: RoutingStrategy,
        strategy_b: RoutingStrategy,
        traffic_split: float = 0.5,
        duration_days: int = 7
    ) -> str:
        """Crear experimento A/B para estrategias"""
        
        variants = {
            "A": strategy_a,
            "B": strategy_b
        }
        
        traffic_split_dict = {
            "A": traffic_split,
            "B": 1.0 - traffic_split
        }
        
        return self.ab_test_manager.create_experiment(
            name=name,
            variants=variants,
            traffic_split=traffic_split_dict,
            duration_days=duration_days
        )
    
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
            "ml_model_trained": self.predictor.is_trained,
            "ab_experiments_active": len([
                exp for exp in self.ab_test_manager.experiments.values()
                if exp["active"]
            ])
        }
    
    async def adapt_routing_parameters(self) -> None:
        """Adaptar parámetros de routing basado en performance"""
        
        if not self.adaptation_enabled or not self.predictor.is_trained:
            return
        
        # Analizar últimos resultados
        recent_performance = defaultdict(list)
        
        for entry in list(self.usage_history)[-200:]:  # Últimos 200
            decision = entry["decision"]
            actual = entry["actual_performance"]
            recent_performance[decision.strategy_used.value].append(
                actual.get("success_rate", 0.0)
            )
        
        # Ajustar pesos de estrategias basado en performance
        for strategy, performances in recent_performance.items():
            if len(performances) >= 10:  # Mínimo de samples
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
    
    def save_state(self, path: str) -> None:
        """Guardar estado del router"""
        
        state = {
            "strategy_weights": {
                k.value: v for k, v in self.strategy_weights.items()
            },
            "ml_model_path": f"{path}_ml_model.pkl",
            "timestamp": datetime.now().isoformat()
        }
        
        # Guardar modelo ML
        if self.predictor.is_trained:
            self.predictor.save_model(state["ml_model_path"])
        
        # Guardar configuración
        with open(f"{path}_config.json", "w") as f:
            json.dump(state, f, indent=2, default=str)
        
        self.logger.info(f"Estado del router guardado en {path}")
    
    def load_state(self, path: str) -> None:
        """Cargar estado del router"""
        
        try:
            # Cargar configuración
            with open(f"{path}_config.json", "r") as f:
                state = json.load(f)
            
            # Reconstruir pesos de estrategias
            self.strategy_weights = {
                RoutingStrategy(k): v for k, v in state["strategy_weights"].items()
            }
            
            # Cargar modelo ML
            ml_model_path = state.get("ml_model_path")
            if ml_model_path and os.path.exists(ml_model_path):
                self.predictor.load_model(ml_model_path)
            
            self.logger.info(f"Estado del router cargado desde {path}")
            
        except Exception as e:
            self.logger.error(f"Error cargando estado del router: {e}")


# Instancia global del router
intelligent_router = IntelligentRouter()