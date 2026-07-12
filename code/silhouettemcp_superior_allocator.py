"""
SilhouetteMCP Superior - Intelligent Task Allocation System
Sistema de Asignación Inteligente Central

Características:
- Hungarian Algorithm para matching óptimo
- Machine Learning para predicción de performance
- Load balancing dinámico con CBBA
- Priority queues inteligentes
- Task decomposition automático
- Real-time optimization

Autor: SilhouetteMCP Superior Team
Fecha: 2025-11-06
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import threading
import heapq
import pickle
from scipy.optimize import linear_sum_assignment
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """Enumeración de prioridades de tareas"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BATCH = 5

class TaskType(Enum):
    """Tipos de tareas del sistema"""
    DATA_PROCESSING = "data_processing"
    MACHINE_LEARNING = "machine_learning"
    WEB_SCRAPING = "web_scraping"
    FILE_ANALYSIS = "file_analysis"
    API_INTEGRATION = "api_integration"
    VISUALIZATION = "visualization"
    REPORT_GENERATION = "report_generation"
    CUSTOM = "custom"

class AgentStatus(Enum):
    """Estados de agentes"""
    ACTIVE = "active"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"

@dataclass
class Task:
    """Representación de una tarea"""
    id: str
    type: TaskType
    priority: TaskPriority
    complexity: float  # 0.0 - 1.0
    estimated_duration: float  # minutos
    required_skills: List[str]
    dependencies: List[str] = field(default_factory=list)
    data_size: float = 1.0  # MB
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    decomposition_depth: int = 0  # Nivel de descomposición (0 = tarea original)
    
    @property
    def urgency_score(self) -> float:
        """Calcula score de urgencia basado en deadline y prioridad"""
        if not self.deadline:
            return 0.0
        
        time_remaining = (self.deadline - datetime.now()).total_seconds() / 3600  # horas
        priority_weight = {
            TaskPriority.CRITICAL: 1.0,
            TaskPriority.HIGH: 0.8,
            TaskPriority.MEDIUM: 0.5,
            TaskPriority.LOW: 0.2,
            TaskPriority.BATCH: 0.1
        }
        
        urgency = priority_weight[self.priority] * min(1.0, time_remaining / 24.0)
        return urgency
    
    @property
    def resource_requirement(self) -> float:
        """Calcula requerimiento de recursos basado en complejidad y tamaño"""
        return (self.complexity * 0.6 + self.data_size / 100.0 * 0.4) * 100

@dataclass
class Agent:
    """Representación de un agente"""
    id: str
    name: str
    status: AgentStatus
    skills: List[str]
    current_workload: float = 0.0  # 0.0 - 1.0
    max_capacity: float = 1.0
    average_performance: float = 0.8  # 0.0 - 1.0
    response_time_avg: float = 2.0  # minutos
    accuracy_rate: float = 0.9
    specialization_score: Dict[TaskType, float] = field(default_factory=dict)
    historical_data: List[Dict] = field(default_factory=list)
    last_active: datetime = field(default_factory=datetime.now)
    location: str = "default"
    
    @property
    def available_capacity(self) -> float:
        """Capacidad disponible del agente"""
        return max(0.0, self.max_capacity - self.current_workload)
    
    @property
    def performance_score(self) -> float:
        """Score de performance general"""
        return (self.average_performance * 0.4 + 
                self.accuracy_rate * 0.3 + 
                (1.0 - self.current_workload) * 0.2 + 
                min(1.0, self.response_time_avg / 10.0) * 0.1)

class HungarianAlgorithm:
    """Implementación del algoritmo húngaro para matching óptimo"""
    
    @staticmethod
    def solve(cost_matrix: np.ndarray) -> Tuple[List[int], List[int]]:
        """
        Resuelve el problema de asignación usando el algoritmo húngaro
        Retorna listas de tareas y agentes asignados
        """
        try:
            task_indices, agent_indices = linear_sum_assignment(cost_matrix)
            return task_indices.tolist(), agent_indices.tolist()
        except Exception as e:
            logger.error(f"Error en Hungarian Algorithm: {e}")
            return [], []
    
    @staticmethod
    def calculate_cost_matrix(tasks: List[Task], agents: List[Agent]) -> np.ndarray:
        """
        Calcula matriz de costos para asignación óptima
        Considera múltiples factores: skills, workload, performance, etc.
        """
        n_tasks = len(tasks)
        n_agents = len(agents)
        
        if n_tasks == 0 or n_agents == 0:
            return np.array([])
        
        # Asegurar matriz cuadrada
        max_size = max(n_tasks, n_agents)
        cost_matrix = np.full((max_size, max_size), 1000.0)  # Costo alto para no asignación
        
        for i, task in enumerate(tasks):
            for j, agent in enumerate(agents):
                if agent.status == AgentStatus.OFFLINE:
                    continue
                
                # Factores de costo
                skill_match = HungarianAlgorithm._calculate_skill_match(task, agent)
                workload_penalty = agent.current_workload
                performance_factor = 1.0 - agent.performance_score
                specialization_bonus = HungarianAlgorithm._get_specialization_score(task, agent)
                
                # Costo final (menor es mejor)
                cost = (workload_penalty * 0.3 + 
                       performance_factor * 0.2 + 
                       (1.0 - skill_match) * 0.3 +
                       (1.0 - specialization_bonus) * 0.2)
                
                # Aplicar urgencia si es muy urgente
                if task.urgency_score > 0.8 and agent.available_capacity > 0.3:
                    cost *= 0.5  # Reducir costo para tareas urgentes
                
                cost_matrix[i][j] = cost
        
        return cost_matrix
    
    @staticmethod
    def _calculate_skill_match(task: Task, agent: Agent) -> float:
        """Calcula match de skills entre tarea y agente"""
        if not task.required_skills:
            return 1.0
        
        if not agent.skills:
            return 0.0
        
        matching_skills = set(task.required_skills) & set(agent.skills)
        return len(matching_skills) / len(task.required_skills) if task.required_skills else 1.0
    
    @staticmethod
    def _get_specialization_score(task: Task, agent: Agent) -> float:
        """Obtiene score de especialización del agente para el tipo de tarea"""
        if task.type not in agent.specialization_score:
            return 0.5  # Score neutral si no hay especialización
        
        return max(0.0, min(1.0, agent.specialization_score[task.type]))

class PerformancePredictor:
    """Sistema de predicción ML para performance de agentes"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_columns = [
            'task_complexity', 'agent_workload', 'agent_performance', 
            'agent_accuracy', 'skill_match', 'specialization_score',
            'data_size', 'task_type_encoded'
        ]
        self.performance_history = []
        
    def train(self, training_data: List[Dict]) -> Dict[str, float]:
        """Entrena el modelo predictivo con datos históricos"""
        if len(training_data) < 10:
            logger.warning("Insuficientes datos para entrenamiento")
            return {}
        
        try:
            # Preparar datos
            X, y = self._prepare_training_data(training_data)
            
            if len(X) == 0:
                return {}
            
            # Escalar características
            X_scaled = self.scaler.fit_transform(X)
            
            # Entrenar modelo ensemble
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
            
            self.model.fit(X_scaled, y)
            
            # Evaluar modelo
            predictions = self.model.predict(X_scaled)
            mae = mean_absolute_error(y, predictions)
            rmse = np.sqrt(mean_squared_error(y, predictions))
            
            self.is_trained = True
            
            metrics = {
                'mae': mae,
                'rmse': rmse,
                'samples': len(X)
            }
            
            logger.info(f"Modelo entrenado - MAE: {mae:.3f}, RMSE: {rmse:.3f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error entrenando modelo: {e}")
            return {}
    
    def predict_performance(self, task: Task, agent: Agent) -> Dict[str, float]:
        """Predice performance para una tarea-agente específica"""
        if not self.is_trained:
            return self._heuristic_prediction(task, agent)
        
        try:
            features = self._extract_features(task, agent)
            features_scaled = self.scaler.transform([features])
            
            prediction = self.model.predict(features_scaled)[0]
            
            # Añadir información adicional
            confidence = self._calculate_confidence(features)
            estimated_time = self._estimate_time(prediction, task, agent)
            
            return {
                'performance_score': max(0.0, min(1.0, prediction)),
                'confidence': confidence,
                'estimated_time_minutes': estimated_time,
                'success_probability': self._calculate_success_probability(prediction)
            }
            
        except Exception as e:
            logger.error(f"Error en predicción: {e}")
            return self._heuristic_prediction(task, agent)
    
    def _prepare_training_data(self, training_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepara datos de entrenamiento"""
        X, y = [], []
        
        for record in training_data:
            try:
                task = Task(**record['task'])
                agent = Agent(**record['agent'])
                actual_performance = record['actual_performance']
                
                features = self._extract_features(task, agent)
                X.append(features)
                y.append(actual_performance)
                
            except Exception as e:
                logger.warning(f"Error procesando record de entrenamiento: {e}")
                continue
        
        return np.array(X), np.array(y)
    
    def _extract_features(self, task: Task, agent: Agent) -> List[float]:
        """Extrae características para el modelo"""
        skill_match = HungarianAlgorithm._calculate_skill_match(task, agent)
        specialization = HungarianAlgorithm._get_specialization_score(task, agent)
        
        features = [
            task.complexity,
            agent.current_workload,
            agent.performance_score,
            agent.accuracy_rate,
            skill_match,
            specialization,
            task.data_size / 100.0,  # Normalizado
            hash(task.type.value) % 1000 / 1000.0  # Encoded task type
        ]
        
        return features
    
    def _heuristic_prediction(self, task: Task, agent: Agent) -> Dict[str, float]:
        """Predicción heurística cuando el modelo no está entrenado"""
        skill_match = HungarianAlgorithm._calculate_skill_match(task, agent)
        specialization = HungarianAlgorithm._get_specialization_score(task, agent)
        
        base_score = (agent.performance_score * 0.4 + 
                     skill_match * 0.3 + 
                     specialization * 0.2 + 
                     agent.accuracy_rate * 0.1)
        
        confidence = min(1.0, len(self.performance_history) / 50.0)
        estimated_time = task.estimated_duration * (2.0 - base_score)
        
        return {
            'performance_score': base_score,
            'confidence': confidence,
            'estimated_time_minutes': estimated_time,
            'success_probability': base_score * confidence
        }
    
    def _calculate_confidence(self, features: List[float]) -> float:
        """Calcula nivel de confianza de la predicción"""
        # Simplificado - basado en rango de características
        complexity = features[0]
        workload = features[1]
        
        if 0.2 <= complexity <= 0.8 and 0.0 <= workload <= 0.7:
            return 0.8
        elif 0.0 <= complexity <= 0.3 and 0.0 <= workload <= 0.5:
            return 0.9
        else:
            return 0.6
    
    def _estimate_time(self, performance_score: float, task: Task, agent: Agent) -> float:
        """Estima tiempo basado en score de performance"""
        base_time = task.estimated_duration
        performance_factor = 2.0 - performance_score
        specialization_factor = 1.0 - HungarianAlgorithm._get_specialization_score(task, agent)
        
        estimated_time = base_time * performance_factor * (1.0 + specialization_factor * 0.2)
        return max(base_time * 0.5, estimated_time)
    
    def _calculate_success_probability(self, performance_score: float) -> float:
        """Calcula probabilidad de éxito basada en performance score"""
        return max(0.1, min(0.95, performance_score * 0.9 + 0.1))

class TaskQueueManager:
    """Gestor de colas de tareas con prioridades inteligentes"""
    
    def __init__(self):
        self.queues = {
            TaskPriority.CRITICAL: [],
            TaskPriority.HIGH: [],
            TaskPriority.MEDIUM: [],
            TaskPriority.LOW: [],
            TaskPriority.BATCH: []
        }
        self.task_index = {}  # Para acceso rápido
        self.batch_tasks = defaultdict(list)
        self.lock = threading.Lock()
        
    def add_task(self, task: Task) -> bool:
        """Añade tarea a la cola apropiada"""
        with self.lock:
            try:
                # Verificar dependencias
                if not self._check_dependencies(task):
                    logger.warning(f"Tarea {task.id} tiene dependencias pendientes")
                    return False
                
                # Si es tarea batch, agrupar con similares
                if task.priority == TaskPriority.BATCH:
                    batch_key = f"{task.type.value}_{task.complexity}"
                    self.batch_tasks[batch_key].append(task)
                    
                    # Procesar batch cuando tenga suficientes tareas
                    if len(self.batch_tasks[batch_key]) >= 3:
                        batched_task = self._create_batched_task(self.batch_tasks[batch_key])
                        heapq.heappush(self.queues[TaskPriority.BATCH], (0, batched_task.created_at, batched_task))
                        self.batch_tasks[batch_key] = []
                
                else:
                    priority_score = self._calculate_priority_score(task)
                    heapq.heappush(self.queues[task.priority], (priority_score, task.created_at, task))
                
                self.task_index[task.id] = task
                logger.info(f"Tarea {task.id} añadida a cola {task.priority.name}")
                return True
                
            except Exception as e:
                logger.error(f"Error añadiendo tarea {task.id}: {e}")
                return False
    
    def get_next_task(self, agent: Agent, max_tasks: int = 1) -> List[Task]:
        """Obtiene próxima(s) tarea(s) para un agente"""
        with self.lock:
            tasks = []
            
            # Determinar prioridad base del agente
            agent_priority = self._determine_agent_priority(agent)
            
            # Buscar tareas en orden de prioridad
            for priority in TaskPriority:
                if len(tasks) >= max_tasks:
                    break
                
                if priority.value < agent_priority.value:
                    continue
                
                while self.queues[priority] and len(tasks) < max_tasks:
                    _, _, task = heapq.heappop(self.queues[priority])
                    
                    # Verificar si el agente puede manejar la tarea
                    if self._is_task_suitable(agent, task):
                        tasks.append(task)
                        logger.info(f"Tarea {task.id} asignada a agente {agent.id}")
                    else:
                        # Volver a meter en cola
                        priority_score = self._calculate_priority_score(task)
                        heapq.heappush(self.queues[priority], (priority_score, task.created_at, task))
                        break
            
            return tasks
    
    def _check_dependencies(self, task: Task) -> bool:
        """Verifica si las dependencias de la tarea están completas"""
        # Simplificado - en implementación real verificarías estado de tareas dependientes
        return True
    
    def _create_batched_task(self, batch_tasks: List[Task]) -> Task:
        """Crea tarea batch de múltiples tareas similares"""
        batch_task = Task(
            id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            type=batch_tasks[0].type,
            priority=TaskPriority.BATCH,
            complexity=np.mean([t.complexity for t in batch_tasks]),
            estimated_duration=sum(t.estimated_duration for t in batch_tasks),
            required_skills=list(set().union(*[t.required_skills for t in batch_tasks])),
            metadata={'batch_tasks': [t.id for t in batch_tasks]}
        )
        
        return batch_task
    
    def _calculate_priority_score(self, task: Task) -> float:
        """Calcula score de prioridad para ordenamiento"""
        urgency = task.urgency_score
        complexity_weight = 1.0 - task.complexity * 0.5  # Tareas menos complejas primero
        
        # Recompensa para tareas críticas
        priority_multiplier = {
            TaskPriority.CRITICAL: 1.0,
            TaskPriority.HIGH: 0.8,
            TaskPriority.MEDIUM: 0.6,
            TaskPriority.LOW: 0.4,
            TaskPriority.BATCH: 0.2
        }[task.priority]
        
        return urgency * complexity_weight * priority_multiplier
    
    def _determine_agent_priority(self, agent: Agent) -> TaskPriority:
        """Determina prioridad base del agente basado en su estado"""
        if agent.status == AgentStatus.OVERLOADED:
            return TaskPriority.LOW
        elif agent.current_workload < 0.3:
            return TaskPriority.HIGH
        else:
            return TaskPriority.MEDIUM
    
    def _is_task_suitable(self, agent: Agent, task: Task) -> bool:
        """Determina si un agente es adecuado para una tarea"""
        # Verificar skills
        skill_match = HungarianAlgorithm._calculate_skill_match(task, agent)
        if skill_match < 0.3:
            return False
        
        # Verificar capacidad
        if agent.available_capacity < task.complexity * 0.5:
            return False
        
        # Verificar especialización
        specialization = HungarianAlgorithm._get_specialization_score(task, agent)
        if task.complexity > 0.7 and specialization < 0.5:
            return False
        
        return True

class DynamicLoadBalancer:
    """Sistema de load balancing dinámico con CBBA algorithm"""
    
    def __init__(self):
        self.bundle_agents = {}
        self.resource_utilization = {}
        self.scaling_thresholds = {
            'cpu': {'low': 0.3, 'high': 0.8},
            'memory': {'low': 0.4, 'high': 0.85},
            'tasks': {'low': 2, 'high': 10}
        }
        self.rebalancing_active = False
        
    async def balance_load(self, agents: List[Agent], tasks: List[Task]) -> Dict[str, Any]:
        """Equilibra la carga usando CBBA algorithm"""
        if self.rebalancing_active:
            logger.info("Rebalancing ya en progreso, saltando...")
            return {}
        
        self.rebalancing_active = True
        
        try:
            # Calcular métricas actuales
            current_metrics = self._calculate_current_metrics(agents)
            
            # Determinar necesidad de rebalanceo
            if not self._needs_rebalancing(current_metrics):
                logger.info("No se necesita rebalanceo")
                return {}
            
            # Ejecutar CBBA algorithm
            bundles = await self._run_cbba_algorithm(agents, tasks)
            
            # Aplicar cambios de asignación
            changes = await self._apply_rebalancing(bundles, agents)
            
            # Monitorear después del rebalanceo
            await self._post_rebalance_monitoring(agents)
            
            logger.info(f"Rebalanceo completado: {len(changes)} cambios aplicados")
            
            return {
                'changes_applied': changes,
                'metrics_before': current_metrics,
                'new_assignments': bundles
            }
            
        except Exception as e:
            logger.error(f"Error en load balancing: {e}")
            return {}
        finally:
            self.rebalancing_active = False
    
    def _calculate_current_metrics(self, agents: List[Agent]) -> Dict[str, float]:
        """Calcula métricas actuales de carga"""
        if not agents:
            return {}
        
        total_workload = sum(agent.current_workload for agent in agents)
        avg_workload = total_workload / len(agents)
        
        # Calcular desviación estándar para medir imbalance
        workloads = [agent.current_workload for agent in agents]
        std_workload = np.std(workloads)
        
        return {
            'avg_workload': avg_workload,
            'std_workload': std_workload,
            'max_workload': max(workloads),
            'min_workload': min(workloads),
            'total_agents': len(agents),
            'overloaded_agents': len([a for a in agents if a.current_workload > 0.8])
        }
    
    def _needs_rebalancing(self, metrics: Dict[str, float]) -> bool:
        """Determina si se necesita rebalanceo"""
        if not metrics:
            return False
        
        # Condiciones para rebalanceo
        high_std = metrics.get('std_workload', 0) > 0.3
        high_overload = metrics.get('overloaded_agents', 0) > 0
        extreme_range = (metrics.get('max_workload', 0) - metrics.get('min_workload', 0)) > 0.6
        
        return high_std or high_overload or extreme_range
    
    async def _run_cbba_algorithm(self, agents: List[Agent], tasks: List[Task]) -> Dict[str, List[Task]]:
        """Ejecuta Consensus-Based Bundle Algorithm"""
        bundles = {agent.id: [] for agent in agents}
        remaining_tasks = tasks.copy()
        
        # Iterar hasta que no se puedan asignar más tareas
        max_iterations = len(tasks) * 2
        iteration = 0
        
        while remaining_tasks and iteration < max_iterations:
            iteration += 1
            
            # Bidding phase: cada agente puja por tareas
            bids = self._calculate_bids(agents, remaining_tasks)
            
            # Consensus phase: resolver conflictos y crear bundles
            bundle_assignments = self._resolve_bidding_conflicts(bids, agents)
            
            # Update bundles
            for agent_id, task_assignments in bundle_assignments.items():
                if task_assignments:
                    for task in task_assignments:
                        if task in remaining_tasks:
                            bundles[agent_id].append(task)
                            remaining_tasks.remove(task)
            
            # Check convergence
            if all(len(bundle) == 0 for bundle in bundles.values()):
                break
        
        return bundles
    
    def _calculate_bids(self, agents: List[Agent], tasks: List[Task]) -> Dict[str, Dict[str, float]]:
        """Calcula pujas de cada agente por las tareas"""
        bids = {}
        
        for agent in agents:
            if agent.status in [AgentStatus.OFFLINE, AgentStatus.MAINTENANCE]:
                continue
            
            bids[agent.id] = {}
            
            for task in tasks:
                if not self._can_agent_handle_task(agent, task):
                    bids[agent.id][task.id] = 0.0
                    continue
                
                # Calcular bid basado en múltiples factores
                urgency_factor = task.urgency_score
                specialization = HungarianAlgorithm._get_specialization_score(task, agent)
                workload_factor = 1.0 - agent.current_workload
                performance_factor = agent.performance_score
                
                # Bid formula
                bid = (urgency_factor * 0.3 + 
                      specialization * 0.25 + 
                      workload_factor * 0.25 + 
                      performance_factor * 0.2)
                
                bids[agent.id][task.id] = bid
        
        return bids
    
    def _resolve_bidding_conflicts(self, bids: Dict[str, Dict[str, float]], agents: List[Agent]) -> Dict[str, List[Task]]:
        """Resuelve conflictos en las pujas y asigna tareas"""
        assignments = {}
        agent_map = {agent.id: agent for agent in agents}
        
        # Para cada tarea, encontrar el mejor bid
        task_bids = {}
        all_tasks = set()
        
        for agent_id, agent_bids in bids.items():
            for task_id, bid_value in agent_bids.items():
                all_tasks.add(task_id)
                if task_id not in task_bids:
                    task_bids[task_id] = []
                task_bids[task_id].append((agent_id, bid_value))
        
        # Asignar cada tarea al mejor bidder
        for task_id, agent_bids in task_bids.items():
            if not agent_bids:
                continue
            
            # Ordenar por bid value (descendente)
            agent_bids.sort(key=lambda x: x[1], reverse=True)
            best_agent_id, best_bid = agent_bids[0]
            
            if best_bid > 0.1:  # Threshold mínimo
                if best_agent_id not in assignments:
                    assignments[best_agent_id] = []
                # En implementación real, aquí encontrarías la tarea real
                assignments[best_agent_id].append(f"task_{task_id}")  # Placeholder
        
        return assignments
    
    def _can_agent_handle_task(self, agent: Agent, task: Task) -> bool:
        """Verifica si un agente puede manejar una tarea"""
        # Verificar capacidad
        if agent.available_capacity < task.complexity * 0.3:
            return False
        
        # Verificar skills básicos
        skill_match = HungarianAlgorithm._calculate_skill_match(task, agent)
        if skill_match < 0.2:
            return False
        
        return True
    
    async def _apply_rebalancing(self, bundles: Dict[str, List[Task]], agents: List[Agent]) -> List[Dict[str, Any]]:
        """Aplica los cambios de rebalanceo"""
        changes = []
        agent_map = {agent.id: agent for agent in agents}
        
        for agent_id, task_list in bundles.items():
            if agent_id not in agent_map:
                continue
            
            agent = agent_map[agent_id]
            
            # Actualizar carga de trabajo del agente
            additional_workload = sum(task.complexity for task in task_list if hasattr(task, 'complexity'))
            
            changes.append({
                'agent_id': agent_id,
                'tasks_added': len(task_list),
                'additional_workload': additional_workload,
                'old_workload': agent.current_workload,
                'new_workload': min(1.0, agent.current_workload + additional_workload)
            })
        
        return changes
    
    async def _post_rebalance_monitoring(self, agents: List[Agent]):
        """Monitorea el sistema después del rebalanceo"""
        metrics = self._calculate_current_metrics(agents)
        
        # Log métricas
        logger.info(f"Métricas post-rebalanceo: {metrics}")
        
        # Verificar si se necesitan más ajustes
        if metrics.get('std_workload', 0) > 0.4:
            logger.warning("Imbalance aún presente, se requieren más ajustes")
        
    async def trigger_scaling(self, utilization_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Dispara escalamiento automático basado en métricas"""
        scaling_decisions = []
        
        # Analizar métricas de utilización
        for resource, usage in utilization_metrics.items():
            if resource in self.scaling_thresholds:
                thresholds = self.scaling_thresholds[resource]
                
                if usage > thresholds['high']:
                    scaling_decisions.append({
                        'action': 'scale_up',
                        'resource': resource,
                        'current_usage': usage,
                        'threshold': thresholds['high']
                    })
                elif usage < thresholds['low']:
                    scaling_decisions.append({
                        'action': 'scale_down',
                        'resource': resource,
                        'current_usage': usage,
                        'threshold': thresholds['low']
                    })
        
        return {
            'scaling_decisions': scaling_decisions,
            'timestamp': datetime.now().isoformat(),
            'total_decisions': len(scaling_decisions)
        }

class TaskDecompositionEngine:
    """Motor de descomposición de tareas complejas"""
    
    def __init__(self, max_decomposition_depth: int = 3):
        self.max_decomposition_depth = max_decomposition_depth
        self.decomposition_strategies = {
            TaskType.DATA_PROCESSING: self._decompose_data_processing,
            TaskType.MACHINE_LEARNING: self._decompose_ml_task,
            TaskType.WEB_SCRAPING: self._decompose_scraping_task,
            TaskType.FILE_ANALYSIS: self._decompose_file_analysis,
            TaskType.API_INTEGRATION: self._decompose_api_integration,
            TaskType.VISUALIZATION: self._decompose_visualization,
            TaskType.REPORT_GENERATION: self._decompose_report_generation,
            TaskType.CUSTOM: self._decompose_custom_task
        }
        
    def _should_decompose(self, task: Task) -> bool:
        """Determina si una tarea debe descomponerse basándose en criterios específicos"""
        # Verificar límite de profundidad de descomposición
        if task.decomposition_depth >= self.max_decomposition_depth:
            return False
        
        # Criterios para descomposición
        high_complexity = task.complexity > 0.8
        large_data = task.data_size > 50  # MB
        long_duration = task.estimated_duration > 60  # minutos
        many_dependencies = len(task.dependencies) > 3
        
        return high_complexity or large_data or long_duration or many_dependencies
    
    def decompose_task(self, task: Task) -> Dict[str, Any]:
        """Descompone una tarea compleja en subtareas"""
        try:
            # Verificar si la tarea debe descomponerse
            if not self._should_decompose(task):
                logger.info(f"Tarea {task.id} no necesita descomposición (depth: {task.decomposition_depth})")
                return {'subtasks': [task], 'decomposition_applied': False}
            
            strategy = self.decomposition_strategies.get(task.type)
            if not strategy:
                return self._generic_decomposition(task)
            
            decomposition = strategy(task)
            subtasks = decomposition.get('subtasks', [])
            
            # Incrementar el nivel de descomposición de las subtareas
            for subtask in subtasks:
                subtask.decomposition_depth = task.decomposition_depth + 1
            
            # Añadir metadata de descomposición
            decomposition['original_task_id'] = task.id
            decomposition['decomposition_timestamp'] = datetime.now().isoformat()
            decomposition['strategy_used'] = task.type.value
            decomposition['decomposition_applied'] = True
            
            logger.info(f"Tarea {task.id} (depth {task.decomposition_depth}) descompuesta en {len(subtasks)} subtareas (depth {task.decomposition_depth + 1})")
            
            return decomposition
            
        except Exception as e:
            logger.error(f"Error descomponiendo tarea {task.id}: {e}")
            return {'subtasks': [task], 'decomposition_applied': False}
    
    def _decompose_data_processing(self, task: Task) -> Dict[str, Any]:
        """Descompone tareas de procesamiento de datos"""
        # Basado en tamaño de datos y complejidad
        data_size_gb = task.data_size / 1024.0
        num_chunks = max(1, int(data_size_gb * 2))  # 1 chunk por cada ~500MB
        
        subtasks = []
        for i in range(num_chunks):
            chunk_task = Task(
                id=f"{task.id}_chunk_{i+1}",
                type=TaskType.DATA_PROCESSING,
                priority=task.priority,
                complexity=min(1.0, task.complexity * 0.7),  # Menos complejo por chunk
                estimated_duration=task.estimated_duration / num_chunks,
                required_skills=task.required_skills,
                dependencies=[task.id],
                metadata={
                    'chunk_index': i + 1,
                    'total_chunks': num_chunks,
                    'data_size': task.data_size / num_chunks,
                    'parent_task': task.id,
                    'chunk_type': 'data_processing'  # Evitar palabras clave en el ID
                }
            )
            subtasks.append(chunk_task)
        
        # Tarea de consolidación
        consolidation_task = Task(
            id=f"{task.id}_final_1",  # Usar sufijo numérico para evitar "consolidate" como palabra clave
            type=TaskType.DATA_PROCESSING,
            priority=task.priority,
            complexity=0.3,
            estimated_duration=max(2.0, task.estimated_duration * 0.1),
            required_skills=task.required_skills,
            dependencies=[f"{task.id}_chunk_{i+1}" for i in range(num_chunks)],
            metadata={
                'consolidation': True,
                'aggregates_from': [f"{task.id}_chunk_{i+1}" for i in range(num_chunks)],
                'parent_task': task.id,
                'final_task': True
            }
        )
        subtasks.append(consolidation_task)
        
        return {
            'subtasks': subtasks,
            'parallel_execution': True,
            'aggregation_required': True,
            'estimated_total_time': task.estimated_duration * 0.9,  # Más eficiente en paralelo
            'resource_split': 'distributed'
        }
    
    def _decompose_ml_task(self, task: Task) -> Dict[str, Any]:
        """Descompone tareas de machine learning"""
        stages = ['data_preparation', 'feature_engineering', 'model_training', 'evaluation']
        
        subtasks = []
        stage_duration = task.estimated_duration / len(stages)
        
        for i, stage in enumerate(stages):
            stage_task = Task(
                id=f"{task.id}_stage_{i+1}",  # Usar sufijos numéricos en lugar del nombre del stage
                type=TaskType.MACHINE_LEARNING,
                priority=task.priority,
                complexity=task.complexity * (0.8 if i < 2 else 1.0),
                estimated_duration=stage_duration,
                required_skills=task.required_skills + ['ml_specialist'] if i >= 2 else task.required_skills,
                dependencies=[f"{task.id}_stage_{i}"] if i > 0 else [],
                metadata={
                    'ml_stage': stage,  # Mantener el nombre del stage en metadata
                    'stage_index': i,
                    'parent_task': task.id,
                    'stage_name': stage  # Evitar palabras clave en el ID de la tarea
                }
            )
            subtasks.append(stage_task)
        
        return {
            'subtasks': subtasks,
            'parallel_execution': False,  # ML tasks son secuenciales
            'aggregation_required': False,
            'estimated_total_time': task.estimated_duration * 1.1,  # Overhead por coordinación
            'resource_split': 'sequential'
        }
    
    def _decompose_scraping_task(self, task: Task) -> Dict[str, Any]:
        """Descompone tareas de web scraping"""
        # Basado en número de URLs o sitios (asumido en metadata)
        num_urls = task.metadata.get('num_urls', 10)
        urls_per_task = max(1, num_urls // 5)  # 5 URLs por subtarea
        
        subtasks = []
        current_url = 0
        chunk_index = 1
        
        while current_url < num_urls:
            end_url = min(current_url + urls_per_task, num_urls)
            url_range = f"urls_{current_url+1}-{end_url}"
            
            scraping_task = Task(
                id=f"{task.id}_scrape_{chunk_index}",  # Usar sufijo numérico
                type=TaskType.WEB_SCRAPING,
                priority=task.priority,
                complexity=task.complexity * 0.8,
                estimated_duration=task.estimated_duration * (end_url - current_url) / num_urls,
                required_skills=task.required_skills + ['web_scraping'],
                dependencies=[],
                metadata={
                    'url_range': url_range,
                    'url_count': end_url - current_url,
                    'parent_task': task.id,
                    'scraping_task': True
                }
            )
            subtasks.append(scraping_task)
            current_url = end_url
            chunk_index += 1
        
        # Tarea de consolidación de datos
        consolidation_task = Task(
            id=f"{task.id}_final_2",  # Usar sufijo numérico para evitar "consolidate" como palabra clave
            type=TaskType.DATA_PROCESSING,
            priority=task.priority,
            complexity=0.4,
            estimated_duration=max(3.0, task.estimated_duration * 0.15),
            required_skills=task.required_skills,
            dependencies=[st.id for st in subtasks],
            metadata={
                'consolidation': True,
                'aggregates_from': [st.id for st in subtasks],
                'parent_task': task.id,
                'final_task': True
            }
        )
        subtasks.append(consolidation_task)
        
        return {
            'subtasks': subtasks,
            'parallel_execution': True,
            'aggregation_required': True,
            'estimated_total_time': task.estimated_duration * 0.8,
            'resource_split': 'distributed'
        }
    
    def _decompose_file_analysis(self, task: Task) -> Dict[str, Any]:
        """Descompone tareas de análisis de archivos"""
        # Basado en tipo de archivo y tamaño
        file_type = task.metadata.get('file_type', 'unknown')
        
        if file_type == 'large_document':
            # Dividir documento en secciones
            num_sections = max(2, int(task.data_size / 10))  # 1 sección por cada ~10MB
            
            subtasks = []
            for i in range(num_sections):
                section_task = Task(
                    id=f"{task.id}_section_{i+1}",
                    type=TaskType.FILE_ANALYSIS,
                    priority=task.priority,
                    complexity=task.complexity * 0.7,
                    estimated_duration=task.estimated_duration / num_sections,
                    required_skills=task.required_skills,
                    dependencies=[],
                    metadata={
                        'section_index': i + 1,
                        'total_sections': num_sections,
                        'parent_task': task.id,
                        'section_analysis': True
                    }
                )
                subtasks.append(section_task)
            
            # Tarea de síntesis final
            synthesis_task = Task(
                id=f"{task.id}_final_3",  # Usar sufijo numérico para evitar "synthesize" como palabra clave
                type=TaskType.FILE_ANALYSIS,
                priority=task.priority,
                complexity=0.5,
                estimated_duration=max(5.0, task.estimated_duration * 0.2),
                required_skills=task.required_skills,
                dependencies=[st.id for st in subtasks],
                metadata={
                    'synthesis': True,
                    'aggregates_from': [st.id for st in subtasks],
                    'parent_task': task.id,
                    'final_task': True
                }
            )
            subtasks.append(synthesis_task)
        
        else:
            # Análisis secuencial
            stages = ['metadata_extraction', 'content_analysis', 'summary_generation']
            subtasks = []
            
            for i, stage in enumerate(stages):
                stage_task = Task(
                    id=f"{task.id}_stage_{i+1}",  # Usar sufijo numérico para evitar nombres de stages como palabras clave
                    type=TaskType.FILE_ANALYSIS,
                    priority=task.priority,
                    complexity=task.complexity * (0.8 + i * 0.1),
                    estimated_duration=task.estimated_duration / len(stages),
                    required_skills=task.required_skills,
                    dependencies=[f"{task.id}_stage_{i}"] if i > 0 else [],
                    metadata={
                        'analysis_stage': stage,  # Mantener el nombre del stage en metadata
                        'stage_index': i,
                        'parent_task': task.id,
                        'stage_name': stage
                    }
                )
                subtasks.append(stage_task)
        
        return {
            'subtasks': subtasks,
            'parallel_execution': len(subtasks) > 3,  # Paralelo si hay muchas subtareas
            'aggregation_required': True,
            'estimated_total_time': task.estimated_duration * 0.9,
            'resource_split': 'mixed'
        }
    
    def _decompose_api_integration(self, task: Task) -> Dict[str, Any]:
        """Descompone tareas de integración de APIs"""
        # Basado en número de endpoints o servicios
        num_services = task.metadata.get('num_services', 3)
        
        subtasks = []
        for i in range(num_services):
            service_task = Task(
                id=f"{task.id}_service_{i+1}",
                type=TaskType.API_INTEGRATION,
                priority=task.priority,
                complexity=task.complexity * 0.8,
                estimated_duration=task.estimated_duration / num_services,
                required_skills=task.required_skills + ['api_specialist'],
                dependencies=[],
                metadata={
                    'service_index': i + 1,
                    'total_services': num_services,
                    'parent_task': task.id,
                    'service_task': True
                }
            )
            subtasks.append(service_task)
        
        # Tarea de integración final
        integration_task = Task(
            id=f"{task.id}_final_4",  # Usar sufijo numérico para evitar "integrate" como palabra clave
            type=TaskType.API_INTEGRATION,
            priority=task.priority,
            complexity=0.6,
            estimated_duration=max(4.0, task.estimated_duration * 0.25),
            required_skills=task.required_skills,
            dependencies=[st.id for st in subtasks],
            metadata={
                'integration': True,
                'aggregates_from': [st.id for st in subtasks],
                'parent_task': task.id,
                'final_task': True
            }
        )
        subtasks.append(integration_task)
        
        return {
            'subtasks': subtasks,
            'parallel_execution': True,
            'aggregation_required': True,
            'estimated_total_time': task.estimated_duration * 0.85,
            'resource_split': 'distributed'
        }
    
    def _decompose_visualization(self, task: Task) -> Dict[str, Any]:
        """Descompone tareas de visualización"""
        # Las visualizaciones pueden ser paralelas por diferentes métricas/aspectos
        num_charts = task.metadata.get('num_charts', 5)
        charts_per_task = max(1, num_charts // 2)
        
        subtasks = []
        current_chart = 0
        chart_index = 1
        
        while current_chart < num_charts:
            end_chart = min(current_chart + charts_per_task, num_charts)
            chart_range = f"charts_{current_chart+1}-{end_chart}"
            
            viz_task = Task(
                id=f"{task.id}_viz_{chart_index}",  # Usar sufijo numérico
                type=TaskType.VISUALIZATION,
                priority=task.priority,
                complexity=task.complexity * 0.9,
                estimated_duration=task.estimated_duration * (end_chart - current_chart) / num_charts,
                required_skills=task.required_skills + ['visualization'],
                dependencies=[],
                metadata={
                    'chart_range': chart_range,
                    'chart_count': end_chart - current_chart,
                    'parent_task': task.id,
                    'visualization_task': True
                }
            )
            subtasks.append(viz_task)
            current_chart = end_chart
            chart_index += 1
        
        # Tarea de composición final
        composition_task = Task(
            id=f"{task.id}_final_5",  # Usar sufijo numérico para evitar "compose" como palabra clave
            type=TaskType.VISUALIZATION,
            priority=task.priority,
            complexity=0.4,
            estimated_duration=max(3.0, task.estimated_duration * 0.15),
            required_skills=task.required_skills,
            dependencies=[st.id for st in subtasks],
            metadata={
                'composition': True,
                'aggregates_from': [st.id for st in subtasks],
                'parent_task': task.id,
                'final_task': True
            }
        )
        subtasks.append(composition_task)
        
        return {
            'subtasks': subtasks,
            'parallel_execution': True,
            'aggregation_required': True,
            'estimated_total_time': task.estimated_duration * 0.9,
            'resource_split': 'distributed'
        }
    
    def _decompose_report_generation(self, task: Task) -> Dict[str, Any]:
        """Descompone tareas de generación de reportes"""
        sections = ['executive_summary', 'detailed_analysis', 'data_insights', 'recommendations']
        
        subtasks = []
        for i, section in enumerate(sections):
            section_task = Task(
                id=f"{task.id}_section_{i+1}",  # Usar sufijo numérico para evitar nombres de secciones como palabras clave
                type=TaskType.REPORT_GENERATION,
                priority=task.priority,
                complexity=task.complexity * 0.8,
                estimated_duration=task.estimated_duration / len(sections),
                required_skills=task.required_skills + ['report_writing'],
                dependencies=[],
                metadata={
                    'report_section': section,  # Mantener el nombre de la sección en metadata
                    'section_index': i,
                    'parent_task': task.id,
                    'section_name': section
                }
            )
            subtasks.append(section_task)
        
        # Tarea de compilación final
        compilation_task = Task(
            id=f"{task.id}_final_6",  # Usar sufijo numérico para evitar "compile" como palabra clave
            type=TaskType.REPORT_GENERATION,
            priority=task.priority,
            complexity=0.3,
            estimated_duration=max(2.0, task.estimated_duration * 0.15),
            required_skills=task.required_skills,
            dependencies=[st.id for st in subtasks],
            metadata={
                'compilation': True,
                'aggregates_from': [st.id for st in subtasks],
                'parent_task': task.id,
                'final_task': True
            }
        )
        subtasks.append(compilation_task)
        
        return {
            'subtasks': subtasks,
            'parallel_execution': len(subtasks) > 4,
            'aggregation_required': True,
            'estimated_total_time': task.estimated_duration * 0.95,
            'resource_split': 'mixed'
        }
    
    def _decompose_custom_task(self, task: Task) -> Dict[str, Any]:
        """Descomposición genérica para tareas personalizadas"""
        # Estrategia genérica basada en complejidad y tamaño
        num_subtasks = max(2, min(5, int(task.complexity * 5)))
        
        subtasks = []
        duration_per_subtask = task.estimated_duration / num_subtasks
        
        for i in range(num_subtasks):
            subtask = Task(
                id=f"{task.id}_subtask_{i+1}",
                type=TaskType.CUSTOM,
                priority=task.priority,
                complexity=task.complexity * 0.8,
                estimated_duration=duration_per_subtask,
                required_skills=task.required_skills,
                dependencies=[],
                metadata={
                    'subtask_index': i + 1,
                    'total_subtasks': num_subtasks,
                    'parent_task': task.id
                }
            )
            subtasks.append(subtask)
        
        return {
            'subtasks': subtasks,
            'parallel_execution': num_subtasks >= 3,
            'aggregation_required': num_subtasks > 1,
            'estimated_total_time': task.estimated_duration * 0.95,
            'resource_split': 'distributed'
        }
    
    def _generic_decomposition(self, task: Task) -> Dict[str, Any]:
        """Descomposición genérica cuando no hay estrategia específica"""
        return {
            'subtasks': [task],  # No descomponer
            'parallel_execution': False,
            'aggregation_required': False,
            'estimated_total_time': task.estimated_duration,
            'resource_split': 'single',
            'reason': 'No specific decomposition strategy available'
        }

class IntelligentTaskAllocator:
    """Sistema principal de asignación inteligente"""
    
    def __init__(self, max_decomposition_depth: int = 3):
        self.hungarian_algorithm = HungarianAlgorithm()
        self.performance_predictor = PerformancePredictor()
        self.task_queue_manager = TaskQueueManager()
        self.load_balancer = DynamicLoadBalancer()
        self.decomposition_engine = TaskDecompositionEngine(max_decomposition_depth)
        
        self.active_assignments = {}
        self.completed_tasks = []
        self.system_metrics = defaultdict(float)
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        logger.info("IntelligentTaskAllocator inicializado con max_decomposition_depth=%d", max_decomposition_depth)
    
    async def assign_task(self, task: Task, available_agents: List[Agent]) -> Dict[str, Any]:
        """Asigna una tarea usando todos los algoritmos disponibles"""
        try:
            start_time = datetime.now()
            
            # 1. Verificar si la tarea necesita descomposición
            if self._needs_decomposition(task):
                decomposition_result = await self._decompose_and_assign(task, available_agents)
                return {
                    'assignment_type': 'decomposed',
                    'result': decomposition_result,
                    'processing_time': (datetime.now() - start_time).total_seconds(),
                    'success': True
                }
            
            # 2. Añadir a cola
            if not self.task_queue_manager.add_task(task):
                return {
                    'assignment_type': 'queue_failed',
                    'error': 'Failed to add to queue',
                    'processing_time': (datetime.now() - start_time).total_seconds(),
                    'success': False
                }
            
            # 3. Obtener mejores candidatos
            candidates = self._get_candidate_agents(task, available_agents)
            
            if not candidates:
                return {
                    'assignment_type': 'no_candidates',
                    'error': 'No suitable agents available',
                    'processing_time': (datetime.now() - start_time).total_seconds(),
                    'success': False
                }
            
            # 4. Aplicar Hungarian Algorithm
            assignment_result = await self._apply_intelligent_assignment(task, candidates)
            
            # 5. Predecir performance
            if assignment_result.get('assigned_agent'):
                prediction = self.performance_predictor.predict_performance(
                    task, assignment_result['assigned_agent']
                )
                assignment_result['prediction'] = prediction
            
            # 6. Actualizar métricas
            self._update_assignment_metrics(assignment_result)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Tarea {task.id} asignada en {processing_time:.2f}s")
            
            return {
                'assignment_type': 'direct',
                'result': assignment_result,
                'processing_time': processing_time,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error asignando tarea {task.id}: {e}")
            return {
                'assignment_type': 'error',
                'error': str(e),
                'processing_time': (datetime.now() - start_time).total_seconds(),
                'success': False
            }
    
    async def _decompose_and_assign(self, task: Task, agents: List[Agent]) -> Dict[str, Any]:
        """Descompone y asigna tarea compleja"""
        # Descomponer tarea
        decomposition = self.decomposition_engine.decompose_task(task)
        subtasks = decomposition['subtasks']
        
        assignment_results = []
        
        # Asignar cada subtarea
        for subtask in subtasks:
            subtask_assignment = await self.assign_task(subtask, agents)
            assignment_results.append({
                'subtask_id': subtask.id,
                'assignment': subtask_assignment
            })
        
        # Crear plan de coordinación si es necesario
        coordination_plan = self._create_coordination_plan(decomposition, assignment_results)
        
        return {
            'original_task': task.id,
            'subtasks': assignment_results,
            'decomposition': decomposition,
            'coordination_plan': coordination_plan,
            'estimated_improvement': decomposition.get('estimated_total_time', 0) / task.estimated_duration
        }
    
    def _needs_decomposition(self, task: Task) -> bool:
        """Determina si una tarea necesita descomposición"""
        # Criterios para descomposición
        high_complexity = task.complexity > 0.8
        large_data = task.data_size > 50  # MB
        long_duration = task.estimated_duration > 60  # minutos
        many_dependencies = len(task.dependencies) > 3
        
        return high_complexity or large_data or long_duration or many_dependencies
    
    def _get_candidate_agents(self, task: Task, agents: List[Agent]) -> List[Agent]:
        """Obtiene agentes candidatos para una tarea"""
        candidates = []
        
        for agent in agents:
            if agent.status in [AgentStatus.OFFLINE, AgentStatus.MAINTENANCE]:
                continue
            
            # Verificar requisitos básicos
            skill_match = HungarianAlgorithm._calculate_skill_match(task, agent)
            if skill_match < 0.3:
                continue
            
            # Verificar capacidad
            if agent.available_capacity < task.complexity * 0.3:
                continue
            
            # Verificar especialización si es tarea compleja
            if task.complexity > 0.6:
                specialization = HungarianAlgorithm._get_specialization_score(task, agent)
                if specialization < 0.4:
                    continue
            
            candidates.append(agent)
        
        # Ordenar por score de performance
        candidates.sort(key=lambda x: x.performance_score, reverse=True)
        
        return candidates
    
    async def _apply_intelligent_assignment(self, task: Task, candidates: List[Agent]) -> Dict[str, Any]:
        """Aplica algoritmo de asignación inteligente"""
        if len(candidates) == 1:
            # Solo un candidato
            agent = candidates[0]
            return {
                'assigned_agent': agent,
                'assignment_method': 'single_candidate',
                'confidence': 0.7,
                'estimated_completion': self._calculate_estimated_completion(task, agent)
            }
        
        # Aplicar Hungarian Algorithm
        tasks = [task]
        cost_matrix = HungarianAlgorithm.calculate_cost_matrix(tasks, candidates)
        
        if cost_matrix.size == 0:
            return {
                'assigned_agent': None,
                'assignment_method': 'failed',
                'error': 'Empty cost matrix'
            }
        
        task_indices, agent_indices = HungarianAlgorithm.solve(cost_matrix)
        
        if not agent_indices:
            return {
                'assigned_agent': None,
                'assignment_method': 'hungarian_failed',
                'error': 'No valid assignment found'
            }
        
        assigned_agent = candidates[agent_indices[0]]
        
        # Aplicar load balancing si es necesario
        load_balance_adjustment = await self._apply_load_balance_adjustment(task, assigned_agent, candidates)
        
        final_agent = load_balance_adjustment.get('adjusted_agent', assigned_agent)
        balance_reason = load_balance_adjustment.get('reason', 'no_adjustment')
        
        return {
            'assigned_agent': final_agent,
            'assignment_method': f'hungarian_{balance_reason}',
            'original_agent': assigned_agent if final_agent != assigned_agent else None,
            'cost_matrix_values': {
                'original_cost': cost_matrix[0][agent_indices[0]] if agent_indices else 0,
                'adjusted_cost': load_balance_adjustment.get('adjusted_cost', 0)
            },
            'estimated_completion': self._calculate_estimated_completion(task, final_agent)
        }
    
    async def _apply_load_balance_adjustment(self, task: Task, assigned_agent: Agent, 
                                           candidates: List[Agent]) -> Dict[str, Any]:
        """Aplica ajuste de load balancing"""
        # Verificar si el agente asignado está sobrecargado
        if assigned_agent.current_workload > 0.8:
            # Buscar alternativa con menor carga
            better_candidates = [
                agent for agent in candidates 
                if agent.current_workload < assigned_agent.current_workload - 0.2
            ]
            
            if better_candidates:
                # Verificar que la alternativa aún sea adecuada
                alternative = better_candidates[0]
                skill_match = HungarianAlgorithm._calculate_skill_match(task, alternative)
                specialization = HungarianAlgorithm._get_specialization_score(task, alternative)
                
                if skill_match > 0.4 and specialization > 0.3:
                    return {
                        'adjusted_agent': alternative,
                        'reason': 'load_balancing',
                        'adjusted_cost': (1.0 - alternative.performance_score) * 0.7
                    }
        
        return {
            'adjusted_agent': assigned_agent,
            'reason': 'no_adjustment',
            'adjusted_cost': 0
        }
    
    def _create_coordination_plan(self, decomposition: Dict[str, Any], 
                                assignment_results: List[Dict]) -> Dict[str, Any]:
        """Crea plan de coordinación para subtareas"""
        subtasks = [r['assignment']['result'].get('assigned_task') or 
                   assignment_results[0]['assignment']['result'].get('assigned_task') 
                   for r in assignment_results]
        
        # Identificar dependencias entre subtareas
        dependency_graph = self._build_dependency_graph(subtasks)
        
        # Crear cronograma de ejecución
        execution_schedule = self._create_execution_schedule(subtasks, dependency_graph)
        
        return {
            'dependency_graph': dependency_graph,
            'execution_schedule': execution_schedule,
            'coordination_points': self._identify_coordination_points(subtasks),
            'aggregation_strategy': self._determine_aggregation_strategy(decomposition)
        }
    
    def _build_dependency_graph(self, subtasks: List[Task]) -> Dict[str, List[str]]:
        """Construye grafo de dependencias"""
        graph = {}
        for subtask in subtasks:
            graph[subtask.id] = subtask.dependencies.copy()
        return graph
    
    def _create_execution_schedule(self, subtasks: List[Task], 
                                 dependency_graph: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Crea cronograma de ejecución basado en dependencias"""
        # Implementación simplificada del algoritmo de scheduling
        schedule = []
        completed = set()
        available = [t for t in subtasks if not t.dependencies]
        
        while available or len(completed) < len(subtasks):
            if not available:
                # Encontrar próxima tarea disponible
                available = [t for t in subtasks 
                           if not set(t.dependencies) - completed and t.id not in completed]
            
            if not available:
                break
            
            # Ordenar por prioridad y duración
            available.sort(key=lambda x: (x.priority.value, x.estimated_duration))
            
            current_task = available.pop(0)
            schedule.append({
                'task_id': current_task.id,
                'estimated_start': len(schedule),  # Simplificado
                'estimated_duration': current_task.estimated_duration,
                'dependencies': current_task.dependencies
            })
            
            completed.add(current_task.id)
            
            # Actualizar disponibles
            available = [t for t in subtasks 
                        if not set(t.dependencies) - completed and t.id not in completed]
        
        return schedule
    
    def _identify_coordination_points(self, subtasks: List[Task]) -> List[Dict[str, Any]]:
        """Identifica puntos de coordinación entre subtareas"""
        coordination_points = []
        
        # Buscar subtareas que requieren agregación
        aggregating_tasks = [t for t in subtasks if 'aggregates_from' in t.metadata]
        
        for agg_task in aggregating_tasks:
            coordination_points.append({
                'type': 'aggregation',
                'task_id': agg_task.id,
                'depends_on': agg_task.metadata['aggregates_from'],
                'trigger': 'after_all_dependencies',
                'action': 'combine_results'
            })
        
        # Buscar puntos de sincronización
        for task in subtasks:
            if task.dependencies:
                coordination_points.append({
                    'type': 'synchronization',
                    'task_id': task.id,
                    'depends_on': task.dependencies,
                    'trigger': 'after_all_dependencies',
                    'action': 'unlock_execution'
                })
        
        return coordination_points
    
    def _determine_aggregation_strategy(self, decomposition: Dict[str, Any]) -> Dict[str, Any]:
        """Determina estrategia de agregación de resultados"""
        aggregation_required = decomposition.get('aggregation_required', False)
        
        if not aggregation_required:
            return {'type': 'none'}
        
        parallel_execution = decomposition.get('parallel_execution', False)
        resource_split = decomposition.get('resource_split', 'distributed')
        
        if parallel_execution:
            return {
                'type': 'parallel_aggregation',
                'strategy': 'reduce_collect',
                'timeout': 300,  # 5 minutos
                'retry_count': 3
            }
        else:
            return {
                'type': 'sequential_aggregation',
                'strategy': 'pipeline_collect',
                'timeout': 600,  # 10 minutos
                'retry_count': 5
            }
    
    def _calculate_estimated_completion(self, task: Task, agent: Agent) -> datetime:
        """Calcula tiempo estimado de finalización"""
        base_duration = task.estimated_duration
        
        # Ajustar basado en performance del agente
        performance_factor = 2.0 - agent.performance_score
        
        # Ajustar basado en especialización
        specialization = HungarianAlgorithm._get_specialization_score(task, agent)
        specialization_factor = 1.0 - specialization * 0.2
        
        estimated_minutes = base_duration * performance_factor * specialization_factor
        
        # Ajustar por carga actual
        load_factor = 1.0 + agent.current_workload
        
        final_minutes = estimated_minutes * load_factor
        
        return datetime.now() + timedelta(minutes=final_minutes)
    
    def _update_assignment_metrics(self, assignment_result: Dict[str, Any]):
        """Actualiza métricas del sistema"""
        self.system_metrics['total_assignments'] += 1
        
        if assignment_result.get('assigned_agent'):
            self.system_metrics['successful_assignments'] += 1
        
        # Métricas por método de asignación
        method = assignment_result.get('assignment_method', 'unknown')
        if 'hungarian' in method:
            self.system_metrics['hungarian_assignments'] += 1
        elif 'single_candidate' in method:
            self.system_metrics['direct_assignments'] += 1
        
        # Tasa de éxito
        success_rate = (self.system_metrics['successful_assignments'] / 
                       self.system_metrics['total_assignments'])
        self.system_metrics['success_rate'] = success_rate
    
    async def predict_performance(self, task: Task, agent: Agent) -> Dict[str, Any]:
        """Predice performance de una asignación específica"""
        return self.performance_predictor.predict_performance(task, agent)
    
    async def balance_load(self, agents: List[Agent], tasks: List[Task] = None) -> Dict[str, Any]:
        """Ejecuta balanceo de carga dinámico"""
        if tasks is None:
            # Obtener tareas de la cola
            tasks = []
            for priority_queue in self.task_queue_manager.queues.values():
                for _, _, task in priority_queue:
                    tasks.append(task)
        
        return await self.load_balancer.balance_load(agents, tasks)
    
    async def optimize_queue(self, optimization_strategy: str = 'performance') -> Dict[str, Any]:
        """Optimiza la cola de tareas"""
        try:
            start_time = datetime.now()
            
            optimization_results = {}
            
            if optimization_strategy == 'performance':
                optimization_results = await self._optimize_for_performance()
            elif optimization_strategy == 'throughput':
                optimization_results = await self._optimize_for_throughput()
            elif optimization_strategy == 'deadline':
                optimization_results = await self._optimize_for_deadlines()
            else:
                optimization_results = await self._optimize_for_performance()  # Default
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'optimization_strategy': optimization_strategy,
                'results': optimization_results,
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error optimizando cola: {e}")
            return {'error': str(e)}
    
    async def _optimize_for_performance(self) -> Dict[str, Any]:
        """Optimiza cola para máxima performance"""
        changes_made = []
        
        for priority in TaskPriority:
            queue = self.task_queue_manager.queues[priority]
            if not queue:
                continue
            
            # Reordenar cola basado en eficiencia predicted
            optimized_queue = []
            
            for _, _, task in queue:
                # Calcular eficiencia estimada
                efficiency_score = self._calculate_task_efficiency(task)
                heapq.heappush(optimized_queue, (efficiency_score, task.created_at, task))
            
            # Reemplazar cola
            self.task_queue_manager.queues[priority] = optimized_queue
            changes_made.append(f"Reordered {priority.name} queue")
        
        return {
            'strategy': 'performance_optimization',
            'changes_made': changes_made,
            'queues_optimized': len([q for q in self.task_queue_manager.queues.values() if q])
        }
    
    async def _optimize_for_throughput(self) -> Dict[str, Any]:
        """Optimiza cola para máximo throughput"""
        changes_made = []
        
        # Identificar tareas batchable
        batchable_tasks = []
        regular_tasks = []
        
        for priority, queue in self.task_queue_manager.queues.items():
            for _, _, task in queue:
                if self._is_batchable_task(task):
                    batchable_tasks.append(task)
                else:
                    regular_tasks.append(task)
        
        # Crear batch de tareas similares
        if batchable_tasks:
            batches = self._create_optimal_batches(batchable_tasks)
            changes_made.append(f"Created {len(batches)} optimal batches")
        
        return {
            'strategy': 'throughput_optimization',
            'changes_made': changes_made,
            'batchable_tasks_found': len(batchable_tasks),
            'regular_tasks': len(regular_tasks)
        }
    
    async def _optimize_for_deadlines(self) -> Dict[str, Any]:
        """Optimiza cola para cumplir deadlines"""
        changes_made = []
        
        # Reordenar todas las colas por urgencia de deadline
        for priority in TaskPriority:
            queue = self.task_queue_manager.queues[priority]
            if not queue:
                continue
            
            # Reordenar por urgencia
            deadline_optimized = []
            for _, _, task in queue:
                urgency = task.urgency_score
                deadline_factor = 1.0 if task.deadline else 0.0
                total_urgency = urgency * (1.0 + deadline_factor)
                heapq.heappush(deadline_optimized, (total_urgency, task.created_at, task))
            
            self.task_queue_manager.queues[priority] = deadline_optimized
            changes_made.append(f"Reordered {priority.name} by deadline urgency")
        
        return {
            'strategy': 'deadline_optimization',
            'changes_made': changes_made,
            'deadline_tasks_prioritized': len([t for _, _, t in self._get_all_queued_tasks() if t.deadline])
        }
    
    def _calculate_task_efficiency(self, task: Task) -> float:
        """Calcula score de eficiencia para una tarea"""
        # Tareas más simples y rápidas primero
        simplicity = 1.0 - task.complexity
        speed = max(0.1, 1.0 - task.estimated_duration / 60.0)  # Normalizado por 1 hora
        
        # Bonus por batch processing
        batch_bonus = 1.2 if task.priority == TaskPriority.BATCH else 1.0
        
        efficiency = (simplicity * 0.4 + speed * 0.6) * batch_bonus
        return efficiency
    
    def _is_batchable_task(self, task: Task) -> bool:
        """Determina si una tarea puede ser procesada en batch"""
        # Tareas simples, de baja prioridad y sin dependencias
        return (task.priority in [TaskPriority.LOW, TaskPriority.BATCH] and 
                task.complexity < 0.5 and 
                len(task.dependencies) == 0)
    
    def _create_optimal_batches(self, tasks: List[Task]) -> List[Dict[str, Any]]:
        """Crea batches óptimos de tareas"""
        # Agrupar tareas por tipo y complejidad similar
        batches = defaultdict(list)
        
        for task in tasks:
            batch_key = f"{task.type.value}_{int(task.complexity * 2) / 2}"  # Agrupar por complejidad
            batches[batch_key].append(task)
        
        # Crear batches con tamaño óptimo
        optimal_batches = []
        for batch_key, batch_tasks in batches.items():
            # Dividir en batches de tamaño 3-5 tareas
            batch_size = 4  # Tamaño óptimo
            for i in range(0, len(batch_tasks), batch_size):
                batch = batch_tasks[i:i + batch_size]
                if len(batch) >= 2:  # Solo crear batch si hay al menos 2 tareas
                    optimal_batches.append({
                        'tasks': batch,
                        'batch_size': len(batch),
                        'estimated_duration': sum(t.estimated_duration for t in batch),
                        'type': batch[0].type
                    })
        
        return optimal_batches
    
    def _get_all_queued_tasks(self) -> List[Tuple[float, datetime, Task]]:
        """Obtiene todas las tareas encoladas"""
        all_tasks = []
        for queue in self.task_queue_manager.queues.values():
            all_tasks.extend(queue)
        return all_tasks
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del sistema"""
        return {
            'assignment_metrics': dict(self.system_metrics),
            'queue_sizes': {priority.name: len(queue) 
                          for priority, queue in self.task_queue_manager.queues.items()},
            'performance_model': {
                'is_trained': self.performance_predictor.is_trained,
                'training_samples': len(self.performance_predictor.performance_history)
            },
            'load_balancer': {
                'rebalancing_active': self.load_balancer.rebalancing_active,
                'resource_thresholds': self.load_balancer.scaling_thresholds
            }
        }

# Sistema de API Endpoints
class IntelligentTaskAllocationAPI:
    """API para el sistema de asignación inteligente"""
    
    def __init__(self):
        self.allocator = IntelligentTaskAllocator()
        self.api_lock = asyncio.Lock()
    
    async def handle_assign_task(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint /api/assign/task - Asignación inteligente"""
        async with self.api_lock:
            try:
                # Parsear datos de entrada
                task_data = request_data.get('task')
                agents_data = request_data.get('agents', [])
                
                if not task_data:
                    return {
                        'success': False,
                        'error': 'Task data is required',
                        'endpoint': '/api/assign/task'
                    }
                
                # Crear objetos Task y Agent
                task = Task(**task_data)
                agents = [Agent(**agent_data) for agent_data in agents_data]
                
                # Ejecutar asignación
                result = await self.allocator.assign_task(task, agents)
                
                # Añadir metadata de respuesta
                result['endpoint'] = '/api/assign/task'
                result['timestamp'] = datetime.now().isoformat()
                result['request_id'] = request_data.get('request_id', 'unknown')
                
                return result
                
            except Exception as e:
                logger.error(f"Error en endpoint assign_task: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'endpoint': '/api/assign/task',
                    'timestamp': datetime.now().isoformat()
                }
    
    async def handle_predict_performance(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint /api/predict/performance - Predicción ML"""
        async with self.api_lock:
            try:
                # Parsear datos
                task_data = request_data.get('task')
                agent_data = request_data.get('agent')
                
                if not task_data or not agent_data:
                    return {
                        'success': False,
                        'error': 'Task and agent data are required',
                        'endpoint': '/api/predict/performance'
                    }
                
                task = Task(**task_data)
                agent = Agent(**agent_data)
                
                # Ejecutar predicción
                prediction = await self.allocator.predict_performance(task, agent)
                
                # Añadir información del modelo
                prediction.update({
                    'endpoint': '/api/predict/performance',
                    'timestamp': datetime.now().isoformat(),
                    'request_id': request_data.get('request_id', 'unknown'),
                    'model_status': {
                        'is_trained': self.allocator.performance_predictor.is_trained,
                        'confidence_level': 'high' if prediction.get('confidence', 0) > 0.7 else 'medium'
                    }
                })
                
                return {
                    'success': True,
                    'result': prediction
                }
                
            except Exception as e:
                logger.error(f"Error en endpoint predict_performance: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'endpoint': '/api/predict/performance',
                    'timestamp': datetime.now().isoformat()
                }
    
    async def handle_balance_load(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint /api/balance/load - Load balancing"""
        async with self.api_lock:
            try:
                # Parsear datos
                agents_data = request_data.get('agents', [])
                tasks_data = request_data.get('tasks', [])
                
                if not agents_data:
                    return {
                        'success': False,
                        'error': 'Agents data is required',
                        'endpoint': '/api/balance/load'
                    }
                
                agents = [Agent(**agent_data) for agent_data in agents_data]
                tasks = [Task(**task_data) for task_data in tasks_data] if tasks_data else []
                
                # Ejecutar balanceo
                result = await self.allocator.balance_load(agents, tasks)
                
                # Añadir metadata
                result.update({
                    'endpoint': '/api/balance/load',
                    'timestamp': datetime.now().isoformat(),
                    'request_id': request_data.get('request_id', 'unknown'),
                    'balancing_metrics': self.allocator.get_system_metrics()
                })
                
                return {
                    'success': True,
                    'result': result
                }
                
            except Exception as e:
                logger.error(f"Error en endpoint balance_load: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'endpoint': '/api/balance/load',
                    'timestamp': datetime.now().isoformat()
                }
    
    async def handle_optimize_queue(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint /api/optimize/queue - Optimización de colas"""
        async with self.api_lock:
            try:
                # Parsear estrategia
                strategy = request_data.get('strategy', 'performance')
                
                if strategy not in ['performance', 'throughput', 'deadline']:
                    return {
                        'success': False,
                        'error': f'Invalid strategy: {strategy}',
                        'endpoint': '/api/optimize/queue'
                    }
                
                # Ejecutar optimización
                result = await self.allocator.optimize_queue(strategy)
                
                # Añadir metadata
                result.update({
                    'endpoint': '/api/optimize/queue',
                    'timestamp': datetime.now().isoformat(),
                    'request_id': request_data.get('request_id', 'unknown'),
                    'system_metrics_after': self.allocator.get_system_metrics()
                })
                
                return {
                    'success': True,
                    'result': result
                }
                
            except Exception as e:
                logger.error(f"Error en endpoint optimize_queue: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'endpoint': '/api/optimize/queue',
                    'timestamp': datetime.now().isoformat()
                }

# Sistema de Monitoreo y Métricas
class SystemMonitor:
    """Sistema de monitoreo del allocator"""
    
    def __init__(self, allocator: IntelligentTaskAllocator):
        self.allocator = allocator
        self.monitoring_active = False
        self.metrics_history = []
        
    def start_monitoring(self, interval_seconds: int = 30):
        """Inicia monitoreo continuo del sistema"""
        self.monitoring_active = True
        
        def monitor_loop():
            while self.monitoring_active:
                try:
                    metrics = self.allocator.get_system_metrics()
                    self.metrics_history.append({
                        'timestamp': datetime.now(),
                        'metrics': metrics
                    })
                    
                    # Log métricas importantes
                    logger.info(f"System Metrics - Success Rate: {metrics['assignment_metrics'].get('success_rate', 0):.2%}")
                    
                    # Verificar alertas
                    self._check_alerts(metrics)
                    
                    time.sleep(interval_seconds)
                    
                except Exception as e:
                    logger.error(f"Error en monitoreo: {e}")
                    time.sleep(interval_seconds)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        logger.info("Sistema de monitoreo iniciado")
    
    def stop_monitoring(self):
        """Detiene el monitoreo"""
        self.monitoring_active = False
        logger.info("Sistema de monitoreo detenido")
    
    def _check_alerts(self, metrics: Dict[str, Any]):
        """Verifica y genera alertas"""
        success_rate = metrics['assignment_metrics'].get('success_rate', 1.0)
        
        if success_rate < 0.8:
            logger.warning(f"ALERT: Success rate below 80%: {success_rate:.2%}")
        
        # Verificar sobrecarga de colas
        total_queued = sum(metrics['queue_sizes'].values())
        if total_queued > 100:
            logger.warning(f"ALERT: Large queue size: {total_queued} tasks")
        
        # Verificar estado del modelo ML
        if not metrics['performance_model']['is_trained']:
            logger.warning("ALERT: Performance predictor model not trained")

# Función de utilidad para crear sistema completo
def create_intelligent_allocator_system():
    """Crea y configura el sistema completo de asignación inteligente"""
    
    # Crear componentes principales
    allocator = IntelligentTaskAllocator()
    api = IntelligentTaskAllocationAPI()
    monitor = SystemMonitor(allocator)
    
    # Configurar sistema
    system_config = {
        'allocator': allocator,
        'api': api,
        'monitor': monitor,
        'version': '1.0.0',
        'created_at': datetime.now().isoformat(),
        'features': [
            'Hungarian Algorithm Optimization',
            'ML-based Performance Prediction',
            'Dynamic Load Balancing (CBBA)',
            'Intelligent Task Decomposition',
            'Priority Queue Management',
            'Real-time Monitoring',
            'Auto-scaling Support',
            'Fault-tolerant Assignment'
        ]
    }
    
    logger.info("Sistema de Asignación Inteligente creado exitosamente")
    logger.info(f"Versión: {system_config['version']}")
    logger.info(f"Características: {', '.join(system_config['features'])}")
    
    return system_config

# Función de ejemplo para demostrar uso
def demo_intelligent_allocator():
    """Función de demostración del sistema"""
    print("=== SilhouetteMCP Superior - Intelligent Task Allocation Demo ===\n")
    
    # Crear sistema
    system = create_intelligent_allocator_system()
    allocator = system['allocator']
    
    # Crear agentes de ejemplo
    agents = [
        Agent(
            id="agent_1",
            name="Data Scientist Pro",
            status=AgentStatus.ACTIVE,
            skills=["python", "machine_learning", "data_analysis"],
            specialization_score={
                TaskType.MACHINE_LEARNING: 0.9,
                TaskType.DATA_PROCESSING: 0.8
            }
        ),
        Agent(
            id="agent_2",
            name="Web Scraper Expert",
            status=AgentStatus.ACTIVE,
            skills=["web_scraping", "python", "selenium"],
            specialization_score={
                TaskType.WEB_SCRAPING: 0.95,
                TaskType.DATA_PROCESSING: 0.6
            }
        ),
        Agent(
            id="agent_3",
            name="Report Generator",
            status=AgentStatus.BUSY,
            skills=["report_writing", "visualization", "data_analysis"],
            current_workload=0.6,
            specialization_score={
                TaskType.REPORT_GENERATION: 0.9,
                TaskType.VISUALIZATION: 0.8
            }
        )
    ]
    
    # Crear tareas de ejemplo
    tasks = [
        Task(
            id="task_ml_001",
            type=TaskType.MACHINE_LEARNING,
            priority=TaskPriority.HIGH,
            complexity=0.8,
            estimated_duration=45.0,
            required_skills=["python", "machine_learning"],
            deadline=datetime.now() + timedelta(hours=2)
        ),
        Task(
            id="task_web_001",
            type=TaskType.WEB_SCRAPING,
            priority=TaskPriority.MEDIUM,
            complexity=0.6,
            estimated_duration=30.0,
            required_skills=["web_scraping", "selenium"],
            data_size=25.0
        ),
        Task(
            id="task_report_001",
            type=TaskType.REPORT_GENERATION,
            priority=TaskPriority.LOW,
            complexity=0.4,
            estimated_duration=20.0,
            required_skills=["report_writing"]
        )
    ]
    
    print("Agentes creados:")
    for agent in agents:
        print(f"- {agent.name} (ID: {agent.id})")
        print(f"  Skills: {', '.join(agent.skills)}")
        print(f"  Estado: {agent.status.value}, Carga: {agent.current_workload:.1%}")
        print()
    
    print("Tareas creadas:")
    for task in tasks:
        print(f"- {task.id}: {task.type.value}")
        print(f"  Prioridad: {task.priority.name}, Complejidad: {task.complexity:.1f}")
        print(f"  Duración estimada: {task.estimated_duration} min")
        print()
    
    # Ejecutar asignaciones
    print("=== Ejecutando Asignaciones ===\n")
    
    # Test 1: Asignación directa
    print("Test 1: Asignación directa de tarea ML")
    result = asyncio.run(allocator.assign_task(tasks[0], agents))
    print(f"Resultado: {result['success']}")
    if result['success']:
        assigned_agent = result['result']['assigned_agent']
        print(f"Agente asignado: {assigned_agent.name}")
        if 'prediction' in result['result']:
            prediction = result['result']['prediction']
            print(f"Performance estimada: {prediction['performance_score']:.2f}")
    print()
    
    # Test 2: Predicción ML
    print("Test 2: Predicción de performance")
    prediction_result = asyncio.run(allocator.predict_performance(tasks[1], agents[1]))
    print(f"Predicción para agente Web Scraping:")
    print(f"- Performance: {prediction_result['performance_score']:.2f}")
    print(f"- Confianza: {prediction_result['confidence']:.2f}")
    print(f"- Tiempo estimado: {prediction_result['estimated_time_minutes']:.1f} min")
    print()
    
    # Test 3: Load balancing
    print("Test 3: Load balancing")
    balance_result = asyncio.run(allocator.balance_load(agents, [tasks[0], tasks[1]]))
    print(f"Load balancing: {balance_result}")
    print()
    
    # Test 4: Optimización de cola
    print("Test 4: Optimización de cola")
    # Añadir tareas a cola
    for task in tasks:
        allocator.task_queue_manager.add_task(task)
    
    optimize_result = asyncio.run(allocator.optimize_queue('performance'))
    print(f"Optimización completada: {optimize_result['success']}")
    print(f"Estrategia: {optimize_result['result']['optimization_strategy']}")
    print()
    
    # Mostrar métricas del sistema
    print("=== Métricas del Sistema ===")
    metrics = allocator.get_system_metrics()
    print(json.dumps(metrics, indent=2, default=str))
    
    print("\n=== Demo Completada ===")
    return system

if __name__ == "__main__":
    # Ejecutar demo
    demo_system = demo_intelligent_allocator()
    
    print(f"\nSistema disponible en: {demo_system}")
    print("Características implementadas:")
    for feature in demo_system['features']:
        print(f"✓ {feature}")