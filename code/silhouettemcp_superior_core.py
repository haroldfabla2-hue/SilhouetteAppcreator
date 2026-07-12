#!/usr/bin/env python3
"""
SilhouetteMCP Superior Core - Núcleo Jerárquico de 5 Niveles
Implementa sistema de coordinación jerárquica avanzada con algoritmos RAFT, CBBA y ML
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import numpy as np
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import jwt
import uvicorn

# ================================
# CONFIGURACIÓN Y CONSTANTES
# ================================

class TaskPriority(Enum):
    """Prioridades de tareas en la jerarquía"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

class TeamType(Enum):
    """Tipos de equipos jerárquicos"""
    MAPS = "maps"
    FINANCIAL = "financial" 
    SOCIAL_TRAVEL = "social_travel"
    CONTENT = "content"
    DATABASE = "database"
    RESEARCH = "research"

class CoordinatorState(Enum):
    """Estados del coordinador"""
    LEADER = "leader"
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    OFFLINE = "offline"

# ================================
# MODELOS DE DATOS
# ================================

@dataclass
class Task:
    """Modelo de tarea en la jerarquía"""
    id: str
    title: str
    description: str
    priority: TaskPriority
    team_type: TeamType
    created_at: datetime
    deadline: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    assigned_to: Optional[str] = None
    status: str = "pending"
    progress: float = 0.0
    estimated_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.deadline:
            data['deadline'] = self.deadline.isoformat()
        data['priority'] = self.priority.value
        data['team_type'] = self.team_type.value
        return data

@dataclass
class Resource:
    """Modelo de recursos del sistema"""
    id: str
    name: str
    type: str
    capacity: float
    current_load: float = 0.0
    team_affinity: Optional[TeamType] = None
    is_available: bool = True
    
    @property
    def utilization(self) -> float:
        return self.current_load / self.capacity if self.capacity > 0 else 0.0

@dataclass
class Team:
    """Modelo de equipo jerárquico"""
    id: str
    name: str
    type: TeamType
    leader_id: str
    members: List[str] = field(default_factory=list)
    capacity: int = 10
    current_workload: float = 0.0
    performance_score: float = 0.0
    status: str = "active"
    
    @property
    def workload_ratio(self) -> float:
        return self.current_workload / self.capacity if self.capacity > 0 else 0.0

@dataclass
class HierarchicalState:
    """Estado completo de la jerarquía"""
    coordinator_id: str
    leader_term: int
    leader_commit_index: int
    last_applied: int
    peers: List[str] = field(default_factory=list)
    teams: Dict[str, Team] = field(default_factory=dict)
    resources: Dict[str, Resource] = field(default_factory=dict)
    pending_tasks: List[Task] = field(default_factory=list)
    active_connections: Dict[str, WebSocket] = field(default_factory=dict)

# ================================
# ALGORITMOS CORE
# ================================

class HungarianAlgorithm:
    """Implementación del algoritmo Húngaro para asignación óptima"""
    
    @staticmethod
    def assign_tasks(tasks: List[Task], resources: List[Resource]) -> Dict[str, str]:
        """Asigna tareas a recursos usando algoritmo húngaro"""
        if not tasks or not resources:
            return {}
        
        # Construir matriz de costos (performance score inversa)
        cost_matrix = []
        for task in tasks:
            row = []
            for resource in resources:
                # Costo basado en afinidad de equipo y carga actual
                affinity_cost = 0.0 if task.team_type == resource.team_affinity else 10.0
                load_cost = resource.utilization * 5.0
                priority_cost = (5 - task.priority.value) * 2.0
                total_cost = affinity_cost + load_cost + priority_cost
                row.append(total_cost)
            cost_matrix.append(row)
        
        # Implementación simplificada del algoritmo húngaro
        assignment = {}
        used_resources = set()
        
        # Ordenar tareas por prioridad y deadline
        sorted_tasks = sorted(tasks, key=lambda t: (t.priority.value, t.deadline or datetime.max))
        
        for task in sorted_tasks:
            best_resource = None
            best_cost = float('inf')
            
            for resource in resources:
                if resource.id not in used_resources and resource.is_available:
                    resource_idx = resources.index(resource)
                    cost = cost_matrix[sorted_tasks.index(task)][resource_idx]
                    if cost < best_cost:
                        best_cost = cost
                        best_resource = resource
            
            if best_resource:
                assignment[task.id] = best_resource.id
                used_resources.add(best_resource.id)
        
        return assignment

class CBBA:
    """Consensus-based Bundle Algorithm para distribución de tareas"""
    
    def __init__(self, teams: List[Team]):
        self.teams = teams
        self.bundles = {team.id: [] for team in teams}
        self.scores = {team.id: [] for team in teams}
        self.own_bids = {}
        self.winning_bids = {}
    
    def run_consensus(self, tasks: List[Task]) -> Dict[str, List[str]]:
        """Ejecuta consenso CBBA para distribución de tareas"""
        # Fase de bidding
        for team in self.teams:
            self._bidding_phase(team, tasks)
        
        # Fase de consensus
        for team in self.teams:
            self._consensus_phase(team)
        
        # Generar bundles finales
        final_assignment = {}
        for team in self.teams:
            final_assignment[team.id] = self.bundles[team.id]
        
        return final_assignment
    
    def _bidding_phase(self, team: Team, tasks: List[Task]):
        """Fase de bidding para un equipo específico"""
        for task in tasks:
            score = self._calculate_task_score(team, task)
            self.own_bids[(team.id, task.id)] = score
    
    def _consensus_phase(self, team: Team):
        """Fase de consenso para un equipo específico"""
        # Implementación simplificada del consenso
        for task_id, bid in self.own_bids.items():
            team_id, _ = task_id
            if team_id == team.id:
                # Equipo获胜
                self.winning_bids[task_id] = bid
                if task_id not in self.bundles[team.id]:
                    self.bundles[team.id].append(task_id)
    
    def _calculate_task_score(self, team: Team, task: Task) -> float:
        """Calcula score de una tarea para un equipo"""
        base_score = 10.0 - task.priority.value
        affinity_bonus = 5.0 if task.team_type == team.type else 0.0
        performance_factor = team.performance_score / 10.0
        return (base_score + affinity_bonus) * performance_factor

class MLPredictor:
    """Predictor de performance usando ML básico"""
    
    def __init__(self):
        self.historical_data = deque(maxlen=1000)
        self.feature_weights = {
            'priority': 0.3,
            'team_affinity': 0.25,
            'team_performance': 0.2,
            'resource_utilization': 0.15,
            'deadline_urgency': 0.1
        }
    
    def predict_completion_time(self, task: Task, team: Team, resource: Resource) -> float:
        """Predice tiempo de finalización de una tarea"""
        features = self._extract_features(task, team, resource)
        prediction = self._weighted_prediction(features)
        return max(1.0, prediction)  # Mínimo 1 hora
    
    def _extract_features(self, task: Task, team: Team, resource: Resource) -> Dict[str, float]:
        """Extrae características para la predicción"""
        features = {
            'priority': 5.0 - task.priority.value,
            'team_affinity': 1.0 if task.team_type == team.type else 0.0,
            'team_performance': team.performance_score / 10.0,
            'resource_utilization': 1.0 - resource.utilization,
            'deadline_urgency': self._calculate_deadline_urgency(task)
        }
        return features
    
    def _weighted_prediction(self, features: Dict[str, float]) -> float:
        """Predicción ponderada basada en características"""
        prediction = 0.0
        for feature, weight in self.feature_weights.items():
            prediction += features.get(feature, 0.0) * weight
        return prediction * 10  # Escalar a horas estimadas
    
    def _calculate_deadline_urgency(self, task: Task) -> float:
        """Calcula urgencia del deadline"""
        if not task.deadline:
            return 0.5
        time_to_deadline = (task.deadline - datetime.now()).total_seconds() / 3600  # horas
        if time_to_deadline <= 0:
            return 1.0
        return min(1.0, 24.0 / time_to_deadline)  # Urgencia máxima si es menos de 24h

class DynamicLoadBalancer:
    """Balanceador de carga dinámico con CBBA"""
    
    def __init__(self, teams: List[Team]):
        self.teams = teams
        self.cbba = CBBA(teams)
        self.load_history = defaultdict(deque)
        self.rebalancing_threshold = 0.8
    
    def balance_load(self, tasks: List[Task]) -> Dict[str, List[Task]]:
        """Balancea carga entre equipos usando CBBA"""
        # Ejecutar CBBA para asignación inicial
        assignment = self.cbba.run_consensus(tasks)
        
        # Aplicar balanceo dinámico
        balanced_assignment = self._apply_dynamic_balancing(assignment, tasks)
        
        # Convertir a formato de tareas por equipo
        team_tasks = defaultdict(list)
        for team_id, task_ids in balanced_assignment.items():
            for task_id in task_ids:
                task = next(t for t in tasks if t.id == task_id)
                team_tasks[team_id].append(task)
        
        return dict(team_tasks)
    
    def _apply_dynamic_balancing(self, assignment: Dict[str, List[str]], tasks: List[Task]) -> Dict[str, List[str]]:
        """Aplica balanceo dinámico basado en cargas actuales"""
        # Calcular cargas actuales
        current_loads = {}
        for team_id, task_ids in assignment.items():
            team = next(t for t in self.teams if t.id == team_id)
            total_load = sum(self._estimate_task_load(task) for task_id in task_ids 
                           for task in tasks if task.id == task_id)
            current_loads[team_id] = team.capacity - total_load
        
        # Identificar sobrecargados y subcargados
        overloaded = {tid: load for tid, load in current_loads.items() if load < 0}
        underloaded = {tid: -load for tid, load in current_loads.items() if load > 0}
        
        # Redistar tareas si es necesario
        balanced_assignment = assignment.copy()
        for overloaded_team, excess_load in overloaded.items():
            task_ids = balanced_assignment[overloaded_team]
            tasks_to_move = []
            
            for task_id in task_ids:
                if excess_load <= 0:
                    break
                task = next(t for t in tasks if t.id == task_id)
                task_load = self._estimate_task_load(task)
                if task_load <= excess_load:
                    tasks_to_move.append(task_id)
                    excess_load -= task_load
            
            # Mover tareas a equipos subcargados
            for task_id in tasks_to_move:
                balanced_assignment[overloaded_team].remove(task_id)
                target_team = min(underloaded.items(), key=lambda x: x[1])[0]
                balanced_assignment[target_team].append(task_id)
                underloaded[target_team] -= self._estimate_task_load(
                    next(t for t in tasks if t.id == task_id)
                )
        
        return balanced_assignment
    
    def _estimate_task_load(self, task: Task) -> float:
        """Estima la carga de una tarea"""
        base_load = task.estimated_duration or 4.0  # 4 horas por defecto
        priority_factor = 1.0 + (5 - task.priority.value) * 0.2
        return base_load * priority_factor

# ================================
# SISTEMA RAFT
# ================================

class RAFTCoordinator:
    """Coordinador usando algoritmo RAFT para consenso"""
    
    def __init__(self, node_id: str, peers: List[str]):
        self.node_id = node_id
        self.peers = peers
        self.state = CoordinatorState.FOLLOWER
        self.current_term = 0
        self.voted_for = None
        self.log = []
        self.commit_index = 0
        self.last_applied = 0
        self.next_index = {peer: len(self.log) + 1 for peer in peers}
        self.match_index = {peer: 0 for peer in peers}
        self.heartbeat_timeout = 150  # ms
        self.election_timeout = 500  # ms
        self.last_heartbeat = time.time() * 1000
        
    async def start_election(self):
        """Inicia una elección"""
        self.state = CoordinatorState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        votes_received = 1
        
        # Votar a sí mismo
        for peer in self.peers:
            if await self._request_vote(peer):
                votes_received += 1
        
        if votes_received > len(self.peers) // 2:
            self.become_leader()
    
    async def _request_vote(self, peer: str) -> bool:
        """Solicita voto a un peer"""
        # Implementación simplificada - en producción sería RPC
        return True
    
    def become_leader(self):
        """Se convierte en líder"""
        self.state = CoordinatorState.LEADER
        # Resetear índices de replicación
        self.next_index = {peer: len(self.log) + 1 for peer in self.peers}
        self.match_index = {peer: 0 for peer in self.peers}
        # Iniciar heartbeat
        asyncio.create_task(self._send_heartbeats())
    
    async def _send_heartbeats(self):
        """Envía heartbeats a todos los peers"""
        while self.state == CoordinatorState.LEADER:
            for peer in self.peers:
                await self._send_append_entries(peer)
            await asyncio.sleep(self.heartbeat_timeout / 1000)
    
    async def _send_append_entries(self, peer: str):
        """Envía entries a un peer"""
        # Implementación simplificada
        pass
    
    def append_entry(self, entry: Dict[str, Any]):
        """Agrega entrada al log"""
        self.log.append(entry)
        if self.state == CoordinatorState.LEADER:
            # Intentar commitear
            self._try_commit_entries()
    
    def _try_commit_entries(self):
        """Intenta commitear entradas"""
        if self.match_index.values():
            max_match = max(self.match_index.values())
            if max_match > self.commit_index:
                self.commit_index = max_match

# ================================
# TEAM LEADERS
# ================================

class TeamLeader:
    """Base para líderes de equipos"""
    
    def __init__(self, team: Team):
        self.team = team
        self.task_queue = deque()
        self.active_tasks = {}
        self.completed_tasks = []
        self.circuit_breaker_state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None
        self.failure_threshold = 5
        self.recovery_timeout = 60  # segundos
        
    async def handle_task(self, task: Task) -> Dict[str, Any]:
        """Maneja una tarea asignada"""
        if self.circuit_breaker_state == "OPEN":
            if self._should_attempt_reset():
                self.circuit_breaker_state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await self._execute_task(task)
            self._reset_circuit_breaker()
            return result
        except Exception as e:
            self._record_failure()
            raise e
    
    async def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Ejecuta la tarea específica"""
        self.active_tasks[task.id] = task
        task.status = "in_progress"
        
        # Simular ejecución
        await asyncio.sleep(0.1)
        
        task.status = "completed"
        task.progress = 100.0
        self.completed_tasks.append(task)
        del self.active_tasks[task.id]
        
        return {"task_id": task.id, "status": "completed", "result": f"Task {task.id} completed"}
    
    def _record_failure(self):
        """Registra una falla"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.circuit_breaker_state = "OPEN"
    
    def _reset_circuit_breaker(self):
        """Resetea el circuit breaker"""
        self.circuit_breaker_state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None
    
    def _should_attempt_reset(self) -> bool:
        """Verifica si debería intentar resetear el circuit breaker"""
        return (time.time() - self.last_failure_time) > self.recovery_timeout

class MapsTeamLeader(TeamLeader):
    """Líder especializado en mapas y localización"""
    
    def __init__(self, team: Team):
        super().__init__(team)
        self.specialization = "maps_geospatial"
    
    async def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Ejecuta tareas específicas de mapas"""
        if task.team_type != TeamType.MAPS:
            raise Exception("Task not assigned to Maps team")
        
        # Lógica específica para tareas de mapas
        result = await super()._execute_task(task)
        result["specialization"] = self.specialization
        return result

class FinancialTeamLeader(TeamLeader):
    """Líder especializado en análisis financiero"""
    
    def __init__(self, team: Team):
        super().__init__(team)
        self.specialization = "financial_analysis"
    
    async def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Ejecuta tareas específicas financieras"""
        if task.team_type != TeamType.FINANCIAL:
            raise Exception("Task not assigned to Financial team")
        
        result = await super()._execute_task(task)
        result["specialization"] = self.specialization
        return result

class SocialTravelTeamLeader(TeamLeader):
    """Líder especializado en redes sociales y viajes"""
    
    def __init__(self, team: Team):
        super().__init__(team)
        self.specialization = "social_travel"
    
    async def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Ejecuta tareas específicas de social + travel"""
        if task.team_type != TeamType.SOCIAL_TRAVEL:
            raise Exception("Task not assigned to Social+Travel team")
        
        result = await super()._execute_task(task)
        result["specialization"] = self.specialization
        return result

class ContentTeamLeader(TeamLeader):
    """Líder especializado en generación de contenido"""
    
    def __init__(self, team: Team):
        super().__init__(team)
        self.specialization = "content_creation"
    
    async def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Ejecuta tareas específicas de contenido"""
        if task.team_type != TeamType.CONTENT:
            raise Exception("Task not assigned to Content team")
        
        result = await super()._execute_task(task)
        result["specialization"] = self.specialization
        return result

class DatabaseTeamLeader(TeamLeader):
    """Líder especializado en gestión de bases de datos"""
    
    def __init__(self, team: Team):
        super().__init__(team)
        self.specialization = "database_management"
    
    async def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Ejecuta tareas específicas de base de datos"""
        if task.team_type != TeamType.DATABASE:
            raise Exception("Task not assigned to Database team")
        
        result = await super()._execute_task(task)
        result["specialization"] = self.specialization
        return result

class ResearchTeamLeader(TeamLeader):
    """Líder especializado en investigación y análisis"""
    
    def __init__(self, team: Team):
        super().__init__(team)
        self.specialization = "research_analysis"
    
    async def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Ejecuta tareas específicas de investigación"""
        if task.team_type != TeamType.RESEARCH:
            raise Exception("Task not assigned to Research team")
        
        result = await super()._execute_task(task)
        result["specialization"] = self.specialization
        return result

# ================================
# COORDINADOR MAESTRO
# ================================

class MasterCoordinator:
    """Coordinador maestro del sistema jerárquico"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.raft = RAFTCoordinator(node_id, [])
        self.hierarchical_state = HierarchicalState(
            coordinator_id=node_id,
            leader_term=0,
            leader_commit_index=0,
            last_applied=0
        )
        
        # Componentes de algoritmos
        self.hungarian = HungarianAlgorithm()
        self.ml_predictor = MLPredictor()
        self.load_balancer = DynamicLoadBalancer([])
        
        # Team leaders
        self.team_leaders = {}
        
        # WebSocket connections
        self.websocket_connections = {}
        
        # Métricas en tiempo real
        self.metrics_buffer = deque(maxlen=1000)
        self.performance_history = defaultdict(deque)
        
        self.logger = logging.getLogger(__name__)
    
    async def initialize_system(self):
        """Inicializa el sistema jerárquico completo"""
        await self._create_initial_teams()
        await self._initialize_resources()
        await self._start_background_tasks()
        self.logger.info("Sistema jerárquico SilhouetteMCP Superior inicializado")
    
    async def _create_initial_teams(self):
        """Crea los equipos iniciales del sistema"""
        teams_config = [
            (TeamType.MAPS, "Equipo de Mapas", MapsTeamLeader),
            (TeamType.FINANCIAL, "Equipo Financiero", FinancialTeamLeader),
            (TeamType.SOCIAL_TRAVEL, "Equipo Social+Viajes", SocialTravelTeamLeader),
            (TeamType.CONTENT, "Equipo de Contenido", ContentTeamLeader),
            (TeamType.DATABASE, "Equipo de Base de Datos", DatabaseTeamLeader),
            (TeamType.RESEARCH, "Equipo de Investigación", ResearchTeamLeader)
        ]
        
        for team_type, team_name, leader_class in teams_config:
            team = Team(
                id=str(uuid.uuid4()),
                name=team_name,
                type=team_type,
                leader_id=str(uuid.uuid4()),
                capacity=10,
                performance_score=8.0
            )
            
            self.hierarchical_state.teams[team.id] = team
            self.team_leaders[team.id] = leader_class(team)
        
        # Actualizar load balancer
        self.load_balancer = DynamicLoadBalancer(list(self.hierarchical_state.teams.values()))
    
    async def _initialize_resources(self):
        """Inicializa recursos del sistema"""
        resource_types = ["compute", "storage", "network", "ml_gpu"]
        
        for resource_type in resource_types:
            for i in range(3):  # 3 recursos por tipo
                resource = Resource(
                    id=f"{resource_type}_{i}",
                    name=f"{resource_type.title()} Resource {i}",
                    type=resource_type,
                    capacity=100.0,
                    is_available=True
                )
                self.hierarchical_state.resources[resource.id] = resource
    
    async def _start_background_tasks(self):
        """Inicia tareas de background"""
        asyncio.create_task(self._health_monitor())
        asyncio.create_task(self._performance_monitor())
        asyncio.create_task(self._auto_scaling_monitor())
        asyncio.create_task(self._fault_detection())
    
    async def create_task(self, task_data: Dict[str, Any]) -> Task:
        """Crea una nueva tarea en el sistema"""
        task = Task(
            id=str(uuid.uuid4()),
            title=task_data["title"],
            description=task_data["description"],
            priority=TaskPriority(task_data["priority"]),
            team_type=TeamType(task_data["team_type"]),
            created_at=datetime.now(),
            deadline=datetime.fromisoformat(task_data["deadline"]) if "deadline" in task_data else None,
            estimated_duration=task_data.get("estimated_duration")
        )
        
        self.hierarchical_state.pending_tasks.append(task)
        
        # Intentar asignar inmediatamente si es crítico
        if task.priority == TaskPriority.CRITICAL:
            await self._assign_task_immediately(task)
        
        return task
    
    async def _assign_task_immediately(self, task: Task):
        """Asigna una tarea crítica inmediatamente"""
        # Usar algoritmo húngaro para asignación óptima
        resources = list(self.hierarchical_state.resources.values())
        assignment = self.hungarian.assign_tasks([task], resources)
        
        if task.id in assignment:
            resource_id = assignment[task.id]
            resource = self.hierarchical_state.resources[resource_id]
            
            # Encontrar equipo apropiado
            target_team = next(
                (team for team in self.hierarchical_state.teams.values() 
                 if team.type == task.team_type), 
                None
            )
            
            if target_team:
                task.assigned_to = target_team.leader_id
                await self._execute_task_with_team(task, target_team)
    
    async def assign_tasks(self) -> Dict[str, List[Task]]:
        """Asigna todas las tareas pendientes usando algoritmos optimizados"""
        if not self.hierarchical_state.pending_tasks:
            return {}
        
        # Usar CBBA para asignación jerárquica
        team_tasks = self.load_balancer.balance_load(self.hierarchical_state.pending_tasks)
        
        assignments = {}
        for team_id, tasks in team_tasks.items():
            team = self.hierarchical_state.teams[team_id]
            assignments[team.name] = tasks
            
            for task in tasks:
                task.assigned_to = team.leader_id
                task.status = "assigned"
                await self._execute_task_with_team(task, team)
        
        # Remover tareas asignadas de pendientes
        assigned_task_ids = {task.id for tasks in team_tasks.values() for task in tasks}
        self.hierarchical_state.pending_tasks = [
            task for task in self.hierarchical_state.pending_tasks 
            if task.id not in assigned_task_ids
        ]
        
        return assignments
    
    async def _execute_task_with_team(self, task: Task, team: Team):
        """Ejecuta una tarea con un equipo específico"""
        try:
            team_leader = self.team_leaders[team.id]
            result = await team_leader.handle_task(task)
            
            # Actualizar métricas
            await self._update_performance_metrics(team, task, True)
            
            self.logger.info(f"Tarea {task.id} completada por equipo {team.name}")
            
        except Exception as e:
            await self._update_performance_metrics(team, task, False)
            self.logger.error(f"Error ejecutando tarea {task.id}: {e}")
            raise
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas en tiempo real del sistema"""
        return {
            "coordinator_state": self.raft.state.value,
            "current_term": self.raft.current_term,
            "teams": {
                team_id: {
                    "name": team.name,
                    "type": team.type.value,
                    "workload_ratio": team.workload_ratio,
                    "performance_score": team.performance_score,
                    "status": team.status
                }
                for team_id, team in self.hierarchical_state.teams.items()
            },
            "resources": {
                res_id: {
                    "name": resource.name,
                    "utilization": resource.utilization,
                    "is_available": resource.is_available
                }
                for res_id, resource in self.hierarchical_state.resources.items()
            },
            "pending_tasks": len(self.hierarchical_state.pending_tasks),
            "active_connections": len(self.websocket_connections),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _health_monitor(self):
        """Monitoreo de salud del sistema"""
        while True:
            try:
                metrics = await self.get_system_metrics()
                
                # Verificar equipos sobrecargados
                for team_id, team_data in metrics["teams"].items():
                    if team_data["workload_ratio"] > 0.9:
                        await self._handle_team_overload(team_id)
                
                # Verificar recursos no disponibles
                for res_id, res_data in metrics["resources"].items():
                    if res_data["utilization"] > 0.95:
                        await self._handle_resource_saturation(res_id)
                
                await asyncio.sleep(30)  # Check cada 30 segundos
                
            except Exception as e:
                self.logger.error(f"Error en health monitor: {e}")
                await asyncio.sleep(60)
    
    async def _performance_monitor(self):
        """Monitoreo de performance del sistema"""
        while True:
            try:
                metrics = await self.get_system_metrics()
                self.metrics_buffer.append({
                    "timestamp": datetime.now(),
                    "metrics": metrics
                })
                
                # Auto-ajustar basado en tendencias
                await self._adjust_system_parameters(metrics)
                
                await asyncio.sleep(10)  # Check cada 10 segundos
                
            except Exception as e:
                self.logger.error(f"Error en performance monitor: {e}")
                await asyncio.sleep(30)
    
    async def _auto_scaling_monitor(self):
        """Monitor de auto-scaling"""
        while True:
            try:
                metrics = await self.get_system_metrics()
                
                # Determinar si se necesita scaling
                avg_workload = np.mean([
                    team["workload_ratio"] for team in metrics["teams"].values()
                ])
                
                if avg_workload > 0.8:
                    await self._scale_up()
                elif avg_workload < 0.3:
                    await self._scale_down()
                
                await asyncio.sleep(60)  # Check cada minuto
                
            except Exception as e:
                self.logger.error(f"Error en auto-scaling monitor: {e}")
                await asyncio.sleep(120)
    
    async def _fault_detection(self):
        """Detección y recuperación de fallas"""
        while True:
            try:
                # Verificar circuit breakers de equipos
                for team_id, leader in self.team_leaders.items():
                    if leader.circuit_breaker_state == "OPEN":
                        await self._handle_team_failure(team_id)
                
                await asyncio.sleep(15)  # Check cada 15 segundos
                
            except Exception as e:
                self.logger.error(f"Error en fault detection: {e}")
                await asyncio.sleep(30)
    
    async def _update_performance_metrics(self, team: Team, task: Task, success: bool):
        """Actualiza métricas de performance"""
        if success:
            team.performance_score = min(10.0, team.performance_score + 0.1)
        else:
            team.performance_score = max(1.0, team.performance_score - 0.2)
    
    async def _handle_team_overload(self, team_id: str):
        """Maneja sobrecarga de equipo"""
        team = self.hierarchical_state.teams[team_id]
        self.logger.warning(f"Equipo {team.name} sobrecargado ({team.workload_ratio:.2%})")
        
        # Redistribuir tareas si es posible
        # En una implementación completa, mover tareas a otros equipos
    
    async def _handle_resource_saturation(self, resource_id: str):
        """Maneja saturación de recursos"""
        resource = self.hierarchical_state.resources[resource_id]
        self.logger.warning(f"Recurso {resource.name} saturado ({resource.utilization:.2%})")
        
        # Marcar como no disponible temporalmente
        resource.is_available = False
        
        # Programar recuperación
        asyncio.create_task(self._schedule_resource_recovery(resource_id))
    
    async def _schedule_resource_recovery(self, resource_id: str):
        """Programa recuperación de recurso"""
        await asyncio.sleep(300)  # 5 minutos
        resource = self.hierarchical_state.resources[resource_id]
        resource.is_available = True
        self.logger.info(f"Recurso {resource.name} recuperado")
    
    async def _handle_team_failure(self, team_id: str):
        """Maneja falla de equipo"""
        team = self.hierarchical_state.teams[team_id]
        self.logger.error(f"Falla detectada en equipo {team.name}")
        
        # Redistribuir tareas críticas
        pending_tasks = [t for t in self.hierarchical_state.pending_tasks if t.team_type == team.type]
        self.hierarchical_state.pending_tasks.extend(pending_tasks)
    
    async def _adjust_system_parameters(self, metrics: Dict[str, Any]):
        """Ajusta parámetros del sistema basado en performance"""
        avg_performance = np.mean([
            team["performance_score"] for team in metrics["teams"].values()
        ])
        
        # Ajustar thresholds basado en performance
        if avg_performance > 8.0:
            self.load_balancer.rebalancing_threshold = 0.9
        elif avg_performance < 5.0:
            self.load_balancer.rebalancing_threshold = 0.7
    
    async def _scale_up(self):
        """Escala el sistema hacia arriba"""
        self.logger.info("Scaling up system capacity")
        # Agregar recursos o equipos temporales
    
    async def _scale_down(self):
        """Escala el sistema hacia abajo"""
        self.logger.info("Scaling down system capacity")
        # Liberar recursos no utilizados
    
    async def register_websocket(self, websocket: WebSocket, client_id: str):
        """Registra una conexión WebSocket"""
        await websocket.accept()
        self.websocket_connections[client_id] = websocket
    
    async def broadcast_metrics(self):
        """Envía métricas a todas las conexiones WebSocket"""
        if not self.websocket_connections:
            return
        
        metrics = await self.get_system_metrics()
        message = {
            "type": "metrics_update",
            "data": metrics
        }
        
        disconnected = []
        for client_id, websocket in self.websocket_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except:
                disconnected.append(client_id)
        
        # Limpiar conexiones desconectadas
        for client_id in disconnected:
            del self.websocket_connections[client_id]

# ================================
# SERVIDOR FASTAPI
# ================================

# Configuración de autenticación
SECRET_KEY = "silhouette-mcp-superior-2025"
ALGORITHM = "HS256"

security = HTTPBearer()

def create_app() -> FastAPI:
    """Crea la aplicación FastAPI"""
    app = FastAPI(
        title="SilhouetteMCP Superior Core",
        description="Núcleo jerárquico SilhouetteMCP Superior con arquitectura de 5 niveles",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Coordinador maestro
    coordinator = MasterCoordinator("coordinator_001")
    
    @app.on_event("startup")
    async def startup_event():
        await coordinator.initialize_system()
    
    # Dependency para autenticación jerárquica
    async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            user_level = payload.get("level")
            return {"level": user_level}
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    # Endpoints de autenticación jerárquica
    @app.post("/auth/login")
    async def login_hierarchical(credentials: Dict[str, Any]):
        """Login con autenticación jerárquica"""
        # Verificar credenciales jerárquicas
        user_level = credentials.get("level", 1)
        
        # Generar JWT con nivel jerárquico
        token = jwt.encode(
            {
                "sub": credentials.get("username"),
                "level": user_level,
                "exp": datetime.utcnow() + timedelta(hours=24)
            },
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        
        return {"access_token": token, "token_type": "bearer", "level": user_level}
    
    # Endpoints de gestión de tareas
    @app.post("/tasks/create")
    async def create_task_endpoint(
        task_data: Dict[str, Any],
        current_user: Dict = Depends(get_current_user)
    ):
        """Crea una nueva tarea en el sistema jerárquico"""
        try:
            task = await coordinator.create_task(task_data)
            return {"task": task.to_dict(), "message": "Tarea creada exitosamente"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/tasks/assign")
    async def assign_tasks_endpoint(
        current_user: Dict = Depends(get_current_user)
    ):
        """Asigna todas las tareas pendientes usando algoritmos optimizados"""
        try:
            assignments = await coordinator.assign_tasks()
            return {
                "assignments": {team: [task.to_dict() for task in tasks] 
                              for team, tasks in assignments.items()},
                "message": "Tareas asignadas exitosamente"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/tasks/pending")
    async def get_pending_tasks(
        current_user: Dict = Depends(get_current_user)
    ):
        """Obtiene todas las tareas pendientes"""
        return {
            "tasks": [task.to_dict() for task in coordinator.hierarchical_state.pending_tasks],
            "count": len(coordinator.hierarchical_state.pending_tasks)
        }
    
    # Endpoints de métricas y monitoreo
    @app.get("/metrics/system")
    async def get_system_metrics_endpoint(
        current_user: Dict = Depends(get_current_user)
    ):
        """Obtiene métricas en tiempo real del sistema"""
        try:
            metrics = await coordinator.get_system_metrics()
            return metrics
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/metrics/stream")
    async def stream_metrics():
        """Stream de métricas en tiempo real usando SSE"""
        async def generate():
            while True:
                try:
                    metrics = await coordinator.get_system_metrics()
                    yield f"data: {json.dumps(metrics)}\n\n"
                    await asyncio.sleep(5)  # Update cada 5 segundos
                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    await asyncio.sleep(5)
        
        return StreamingResponse(generate(), media_type="text/event-stream")
    
    # Endpoints de equipos
    @app.get("/teams")
    async def get_teams(
        current_user: Dict = Depends(get_current_user)
    ):
        """Obtiene información de todos los equipos"""
        teams = {}
        for team_id, team in coordinator.hierarchical_state.teams.items():
            teams[team_id] = {
                "id": team.id,
                "name": team.name,
                "type": team.type.value,
                "capacity": team.capacity,
                "current_workload": team.current_workload,
                "workload_ratio": team.workload_ratio,
                "performance_score": team.performance_score,
                "status": team.status,
                "leader_id": team.leader_id,
                "members": team.members
            }
        return {"teams": teams}
    
    @app.post("/teams/{team_id}/scale")
    async def scale_team(
        team_id: str,
        scale_data: Dict[str, Any],
        current_user: Dict = Depends(get_current_user)
    ):
        """Escala un equipo específico"""
        if team_id not in coordinator.hierarchical_state.teams:
            raise HTTPException(status_code=404, detail="Equipo no encontrado")
        
        team = coordinator.hierarchical_state.teams[team_id]
        new_capacity = scale_data.get("capacity", team.capacity)
        
        team.capacity = max(1, min(50, new_capacity))  # Límites razonables
        
        return {
            "team_id": team_id,
            "new_capacity": team.capacity,
            "message": "Equipo escalado exitosamente"
        }
    
    # Endpoints de recursos
    @app.get("/resources")
    async def get_resources(
        current_user: Dict = Depends(get_current_user)
    ):
        """Obtiene información de recursos"""
        resources = {}
        for res_id, resource in coordinator.hierarchical_state.resources.items():
            resources[res_id] = {
                "id": resource.id,
                "name": resource.name,
                "type": resource.type,
                "capacity": resource.capacity,
                "current_load": resource.current_load,
                "utilization": resource.utilization,
                "team_affinity": resource.team_affinity.value if resource.team_affinity else None,
                "is_available": resource.is_available
            }
        return {"resources": resources}
    
    # WebSocket para comunicación en tiempo real
    @app.websocket("/ws/metrics")
    async def websocket_metrics(websocket: WebSocket):
        """WebSocket para métricas en tiempo real"""
        client_id = str(uuid.uuid4())
        await coordinator.register_websocket(websocket, client_id)
        
        try:
            while True:
                await coordinator.broadcast_metrics()
                await asyncio.sleep(5)
        except WebSocketDisconnect:
            if client_id in coordinator.websocket_connections:
                del coordinator.websocket_connections[client_id]
        except Exception as e:
            print(f"WebSocket error: {e}")
    
    # Endpoints de administración del coordinador
    @app.get("/coordinator/status")
    async def get_coordinator_status(
        current_user: Dict = Depends(get_current_user)
    ):
        """Estado del coordinador RAFT"""
        return {
            "node_id": coordinator.node_id,
            "state": coordinator.raft.state.value,
            "current_term": coordinator.raft.current_term,
            "commit_index": coordinator.raft.commit_index,
            "last_applied": coordinator.raft.last_applied,
            "peer_count": len(coordinator.raft.peers)
        }
    
    @app.post("/coordinator/rebalance")
    async def rebalance_system(
        current_user: Dict = Depends(get_current_user)
    ):
        """Fuerza rebalanceo del sistema"""
        try:
            assignments = await coordinator.assign_tasks()
            return {
                "message": "Rebalanceo completado",
                "assignments": len(assignments)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # Health check
    @app.get("/health")
    async def health_check():
        """Health check del sistema"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "components": {
                "coordinator": "active",
                "raft": coordinator.raft.state.value,
                "teams": len(coordinator.hierarchical_state.teams),
                "resources": len(coordinator.hierarchical_state.resources),
                "pending_tasks": len(coordinator.hierarchical_state.pending_tasks)
            }
        }
    
    return app

# ================================
# FUNCIÓN PRINCIPAL
# ================================

async def main():
    """Función principal para ejecutar el servidor"""
    app = create_app()
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ejecutar servidor
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info",
        access_log=True
    )
    server = uvicorn.Server(config)
    
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())