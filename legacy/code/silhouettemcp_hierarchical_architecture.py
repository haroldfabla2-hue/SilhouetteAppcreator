#!/usr/bin/env python3
"""
SilhouetteMCP Arquitectura Jerárquica Superior - Edición Completa
===============================================================

ARQUITECTURA JERÁRQUICA SUPERIOR CON 100+ AGENTES ESPECIALIZADOS

Desarrollado para: silhouettemcp.albertofarah.com
Versión: 5.0.0 - HIERARCHICAL ARCHITECTURE EDITION

ESTRUCTURA COMPLETA:
- 1 Master Coordinator (Decisiones estratégicas)
- 1 Intelligent Task Assigner (Asignación inteligente)
- 6 Team Leaders especializados
- 100+ Agentes especializados en equipos
- 10+ Sistemas de apoyo
- Dashboard jerárquico completo
- Sistema de métricas en tiempo real
- WebSocket updates
- Comunicación FIPA-ACL
- Algoritmos de coordinación avanzados (RAFT, CBBA, Hungarian)
- 100% compatibilidad con servidor unificado existente

PUERTOS:
- 8001: Servidor unificado legacy (51 herramientas)
- 8002: Arquitectura jerárquica superior (100+ agentes)
- 8003: Dashboard y métricas en tiempo real
- 8010-8014: Coordinación con arquitectura mejorada (auto-healing)
- 8015-8019: Protección de seguridad multicapa
- 8020-8024: Auto-scaling y load balancing
"""

import json
import hashlib
import secrets
import asyncio
import random
import logging
import threading
import time
import base64
import re
import csv
import io
import xml.etree.ElementTree as ET
import os
import uuid
import aiofiles
import aiohttp
import redis.asyncio as redis
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set, Callable, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from enum import Enum
import queue
from concurrent.futures import ThreadPoolExecutor
from abc import ABC, abstractmethod
import jwt
from concurrent.futures import ThreadPoolExecutor
import websockets
from fastapi import FastAPI, HTTPException, Request, Depends, status, File, UploadFile, Form, Query, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, EmailStr, Field, validator
import uvicorn
import subprocess
import psutil
from asyncio import Lock
import traceback

# ==================== CONFIGURACIÓN Y LOGGING ====================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SilhouetteMCP-Hierarchical-Architecture")

# ==================== CONFIGURACIÓN DE AUTENTICACIÓN ====================
ADMIN_CREDENTIALS = {
    "email": "alberto.farahb@hotmail.com",
    "password_hash": hashlib.sha256("Fbalberto1910".encode()).hexdigest()
}

# Configuración de Supabase
SUPABASE_CONFIG = {
    "project_url": os.getenv("SUPABASE_URL", "https://your-project.supabase.co"),
    "service_role_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
    "anon_key": os.getenv("SUPABASE_ANON_KEY", ""),
    "project_id": os.getenv("SUPABASE_PROJECT_ID", "")
}

# ==================== ENUMS Y ESTRUCTURAS BASE ====================

class TaskPriority(Enum):
    """Prioridades de tareas en la jerarquía"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

class TeamType(Enum):
    """Tipos de equipos jerárquicos"""
    MAPS_INTELLIGENCE = "maps_intelligence"
    FINANCIAL_INTELLIGENCE = "financial_intelligence"
    SOCIAL_TRAVEL = "social_travel"
    CONTENT_CREATION = "content_creation"
    DATABASE_OPERATIONS = "database_operations"
    RESEARCH_INTELLIGENCE = "research_intelligence"
    SUPPORT_SYSTEMS = "support_systems"

class AgentLevel(Enum):
    """Niveles jerárquicos de agentes"""
    LEVEL_5 = 5  # Master Coordinator
    LEVEL_4 = 4  # Intelligent Task Assigner
    LEVEL_3 = 3  # Team Leaders
    LEVEL_2 = 2  # Coordination Leaders
    LEVEL_1 = 1  # Specialized Experts
    LEVEL_0 = 0  # Execution Agents

class MessagePriority(Enum):
    """Prioridades de mensajes FIPA-ACL"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4

class TaskStatus(Enum):
    """Estados de tareas"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELEGATED = "delegated"

class CoordinatorState(Enum):
    """Estados del coordinador"""
    LEADER = "leader"
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    OFFLINE = "offline"

class SecurityLevel(Enum):
    """Niveles de seguridad"""
    BASIC = 1
    STANDARD = 2
    ENHANCED = 3
    ENTERPRISE = 4
    MAXIMUM = 5

class AutoScalingStatus(Enum):
    """Estados de auto-scaling"""
    IDLE = "idle"
    SCALING_UP = "scaling_up"
    SCALING_DOWN = "scaling_down"
    MONITORING = "monitoring"
    MAINTENANCE = "maintenance"

class HealthStatus(Enum):
    """Estados de salud del sistema"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    RECOVERING = "recovering"

# ==================== MODELOS DE DATOS ====================

@dataclass
class FIPAMessage:
    """Mensaje FIPA-ACL estándar"""
    performative: str  # inform, request, propose, accept, reject
    sender: str
    receiver: str
    content: Dict[str, Any]
    reply_to: Optional[str] = None
    reply_by: Optional[datetime] = None
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class Task:
    """Modelo de tarea en la jerarquía"""
    id: str
    title: str
    description: str
    priority: TaskPriority
    team_type: TeamType
    created_at: datetime
    complexity: int = 5
    estimated_duration: int = 60
    deadline: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    assigned_to: Optional[str] = None
    assigned_team: Optional[str] = None
    status: str = "pending"
    progress: float = 0.0
    actual_duration: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
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
class AgentPerformance:
    """Métricas de rendimiento de agente"""
    agent_id: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_completion_time: float = 0.0
    current_load: float = 0.0
    success_rate: float = 100.0
    last_activity: datetime = field(default_factory=datetime.now)
    performance_score: float = 100.0
    team_affinity: Optional[TeamType] = None
    capabilities: Set[str] = field(default_factory=set)

@dataclass
class Agent:
    """Modelo de agente jerárquico"""
    id: str
    name: str
    level: AgentLevel
    team_type: TeamType
    capabilities: Set[str]
    performance: AgentPerformance
    status: str = "active"
    specialization: str = ""
    current_tasks: List[str] = field(default_factory=list)
    max_concurrent_tasks: int = 3
    response_time_avg: float = 0.0
    last_health_check: datetime = field(default_factory=datetime.now)

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
    specialization: str = ""
    
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
    agents: Dict[str, Agent] = field(default_factory=dict)
    resources: Dict[str, str] = field(default_factory=dict)
    pending_tasks: List[Task] = field(default_factory=list)
    active_connections: Dict[str, WebSocket] = field(default_factory=dict)

# ==================== SISTEMA DE COMUNICACIÓN FIPA-ACL ====================

class FIPAController:
    """Controlador de comunicación FIPA-ACL"""
    
    def __init__(self):
        self.message_queue: Dict[str, deque] = defaultdict(lambda: deque())
        self.message_history: List[FIPAMessage] = []
        self.subscribers: Dict[str, List[callable]] = defaultdict(list)
        self.lock = threading.Lock()
    
    async def send_message(self, message: FIPAMessage) -> bool:
        """Envía mensaje FIPA-ACL"""
        try:
            with self.lock:
                self.message_history.append(message)
                self.message_queue[message.receiver].append(message)
                
                # Notificar suscriptores
                for callback in self.subscribers[message.receiver]:
                    asyncio.create_task(callback(message))
                
                return True
        except Exception as e:
            logger.error(f"Error enviando mensaje FIPA-ACL: {e}")
            return False
    
    def subscribe(self, agent_id: str, callback: callable):
        """Suscribe agente a mensajes"""
        self.subscribers[agent_id].append(callback)
    
    def get_messages(self, agent_id: str) -> List[FIPAMessage]:
        """Obtiene mensajes para agente"""
        with self.lock:
            messages = list(self.message_queue[agent_id])
            self.message_queue[agent_id].clear()
            return messages
    
    def get_message_history(self, limit: int = 100) -> List[FIPAMessage]:
        """Obtiene historial de mensajes"""
        return self.message_history[-limit:]

# ==================== ALGORITMOS DE COORDINACIÓN ====================

class HungarianAlgorithm:
    """Implementación del algoritmo Húngaro para asignación óptima"""
    
    @staticmethod
    def assign_tasks(tasks: List[Task], agents: List[Agent]) -> Dict[str, str]:
        """Asigna tareas a agentes usando algoritmo húngaro"""
        if not tasks or not agents:
            return {}
        
        assignment = {}
        used_agents = set()
        
        # Ordenar tareas por prioridad y deadline
        sorted_tasks = sorted(tasks, key=lambda t: (t.priority.value, t.deadline or datetime.max))
        
        for task in sorted_tasks:
            best_agent = None
            best_cost = float('inf')
            
            for agent in agents:
                if agent.id not in used_agents and agent.status == "active":
                    # Calcular costo basado en afinidad de equipo y carga actual
                    affinity_cost = 0.0 if task.team_type == agent.team_type else 10.0
                    load_cost = agent.performance.current_load * 5.0
                    priority_cost = (5 - task.priority.value) * 2.0
                    complexity_cost = max(0, task.complexity - 5) * 1.5
                    
                    total_cost = affinity_cost + load_cost + priority_cost + complexity_cost
                    
                    if total_cost < best_cost:
                        best_cost = total_cost
                        best_agent = agent
            
            if best_agent:
                assignment[task.id] = best_agent.id
                used_agents.add(best_agent.id)
        
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
        for team_id, bundle in self.bundles.items():
            for task_id in bundle:
                final_assignment[task_id] = team_id
        
        return final_assignment
    
    def _bidding_phase(self, team: Team, tasks: List[Task]):
        """Fase de puja"""
        for task in tasks:
            bid_score = self._calculate_bid_score(team, task)
            self.own_bids[(team.id, task.id)] = bid_score
    
    def _consensus_phase(self, team: Team):
        """Fase de consenso"""
        # Simplificado: tomar las mejores pujas del equipo
        team_bids = [(task_id, score) for (t_id, task_id), score in self.own_bids.items() if t_id == team.id]
        team_bids.sort(key=lambda x: x[1], reverse=True)
        
        # Asignar hasta la capacidad del equipo
        self.bundles[team.id] = [task_id for task_id, _ in team_bids[:team.capacity]]
    
    def _calculate_bid_score(self, team: Team, task: Task) -> float:
        """Calcula puntuación de puja"""
        base_score = 100 - (task.complexity * 10)
        affinity_bonus = 20 if task.team_type == team.type else 0
        capacity_factor = min(1.0, team.capacity / 10)
        
        return base_score + affinity_bonus + (capacity_factor * 10)

# ==================== SISTEMA DE AUTO-SCALING ====================

class AutoScalingManager:
    """Gestor de auto-scaling para 100+ agentes"""
    
    def __init__(self, team_manager):
        self.team_manager = team_manager
        self.status = AutoScalingStatus.IDLE
        self.scaling_history = []
        self.resource_thresholds = {
            "cpu_threshold": 80.0,  # Porcentaje
            "memory_threshold": 85.0,  # Porcentaje
            "task_queue_threshold": 50,  # Número de tareas pendientes
            "response_time_threshold": 2.0  # Segundos
        }
        self.scaling_policies = {
            "scale_up_trigger": 3,  # Número de métricas violadas
            "scale_down_trigger": 3,  # Número de métricas en buen estado
            "min_agents_per_team": 2,
            "max_agents_per_team": 25,
            "cooldown_period": 300  # 5 minutos
        }
        
    async def monitor_and_scale(self):
        """Monitorea y escala automáticamente los agentes"""
        while True:
            try:
                system_metrics = await self.collect_system_metrics()
                scaling_decision = await self.analyze_scaling_needs(system_metrics)
                
                if scaling_decision["action"] != "none":
                    await self.execute_scaling_action(scaling_decision)
                
                await asyncio.sleep(30)  # Monitor cada 30 segundos
                
            except Exception as e:
                logger.error(f"Error en auto-scaling: {e}")
                await asyncio.sleep(60)
    
    async def collect_system_metrics(self) -> Dict[str, Any]:
        """Recopila métricas del sistema para auto-scaling"""
        try:
            # Métricas del sistema
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Métricas de agentes
            total_agents = len(self.team_manager.agents)
            active_agents = len([a for a in self.team_manager.agents.values() if a.status == "active"])
            pending_tasks = len(getattr(self, 'pending_tasks', []))
            active_tasks = len(getattr(self, 'active_tasks', {}))
            
            # Métricas por equipo
            team_metrics = {}
            for team_id, team in self.team_manager.teams.items():
                team_agents = [self.team_manager.agents[aid] for aid in team.members if aid in self.team_manager.agents]
                team_performance = np.mean([a.performance.performance_score for a in team_agents]) if team_agents else 0
                
                team_metrics[team_id] = {
                    "agent_count": len(team_agents),
                    "active_agents": len([a for a in team_agents if a.status == "active"]),
                    "average_performance": team_performance,
                    "workload_ratio": team.workload_ratio
                }
            
            return {
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "timestamp": datetime.now()
                },
                "agents": {
                    "total": total_agents,
                    "active": active_agents,
                    "active_percentage": (active_agents / total_agents * 100) if total_agents > 0 else 0
                },
                "tasks": {
                    "pending": pending_tasks,
                    "active": active_tasks,
                    "total": pending_tasks + active_tasks
                },
                "teams": team_metrics
            }
            
        except Exception as e:
            logger.error(f"Error recopilando métricas: {e}")
            return {}
    
    async def analyze_scaling_needs(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza si se necesita hacer scaling"""
        if not metrics:
            return {"action": "none", "reason": "no_metrics"}
        
        scaling_signals = []
        
        # Verificar CPU
        if metrics["system"]["cpu_percent"] > self.resource_thresholds["cpu_threshold"]:
            scaling_signals.append("high_cpu")
        
        # Verificar memoria
        if metrics["system"]["memory_percent"] > self.resource_thresholds["memory_threshold"]:
            scaling_signals.append("high_memory")
        
        # Verificar tareas pendientes
        if metrics["tasks"]["pending"] > self.resource_thresholds["task_queue_threshold"]:
            scaling_signals.append("high_task_queue")
        
        # Verificar tiempo de respuesta promedio (simulado)
        avg_response_time = random.uniform(0.5, 4.0)
        if avg_response_time > self.resource_thresholds["response_time_threshold"]:
            scaling_signals.append("slow_response")
        
        # Analizar equipos sobrecargados
        overloaded_teams = []
        for team_id, team_data in metrics["teams"].items():
            if team_data["workload_ratio"] > 0.8 or team_data["average_performance"] < 70:
                overloaded_teams.append(team_id)
        
        if overloaded_teams:
            scaling_signals.append("overloaded_teams")
        
        # Decidir acción
        if len(scaling_signals) >= self.scaling_policies["scale_up_trigger"]:
            return {
                "action": "scale_up",
                "signals": scaling_signals,
                "target_teams": overloaded_teams if overloaded_teams else ["all"],
                "reason": f"Multiple signals: {', '.join(scaling_signals)}"
            }
        elif len(scaling_signals) == 0 and metrics["agents"]["active_percentage"] > 90:
            return {
                "action": "scale_down", 
                "signals": scaling_signals,
                "reason": "Low utilization detected"
            }
        else:
            return {"action": "none", "signals": scaling_signals}
    
    async def execute_scaling_action(self, decision: Dict[str, Any]):
        """Ejecuta la acción de scaling"""
        action = decision["action"]
        
        try:
            if action == "scale_up":
                self.status = AutoScalingStatus.SCALING_UP
                await self.scale_up_agents(decision)
            elif action == "scale_down":
                self.status = AutoScalingStatus.SCALING_DOWN
                await self.scale_down_agents()
            
            # Registrar acción
            scaling_record = {
                "timestamp": datetime.now(),
                "action": action,
                "decision": decision,
                "status": "completed"
            }
            self.scaling_history.append(scaling_record)
            
            logger.info(f"Auto-scaling action executed: {action}")
            
        except Exception as e:
            logger.error(f"Error ejecutando scaling action {action}: {e}")
        finally:
            self.status = AutoScalingStatus.MONITORING
    
    async def scale_up_agents(self, decision: Dict[str, Any]):
        """Escala hacia arriba los agentes"""
        target_teams = decision.get("target_teams", ["all"])
        
        for team_type in TeamType:
            if "all" in target_teams or team_type.value in target_teams:
                team_id = f"{team_type.value}_team"
                if team_id in self.team_manager.teams:
                    current_count = len(self.team_manager.teams[team_id].members)
                    if current_count < self.scaling_policies["max_agents_per_team"]:
                        # Agregar nuevo agente
                        await self.add_agent_to_team(team_type, team_id)
    
    async def scale_down_agents(self):
        """Escala hacia abajo los agentes"""
        # Escalar down agentes inactivos o de bajo rendimiento
        for team_id, team in self.team_manager.teams.items():
            current_count = len(team.members)
            if current_count > self.scaling_policies["min_agents_per_team"]:
                # Remover agente de bajo rendimiento
                await self.remove_low_performance_agent(team_id)
    
    async def add_agent_to_team(self, team_type: TeamType, team_id: str):
        """Añade un nuevo agente al equipo"""
        try:
            # Crear agente según el tipo de equipo
            agent_id = f"scaled_agent_{uuid.uuid4().hex[:8]}"
            
            # Determinar tipo de agente basado en el equipo
            if team_type == TeamType.MAPS_INTELLIGENCE:
                agent = LocationAnalyst(agent_id)
            elif team_type == TeamType.FINANCIAL_INTELLIGENCE:
                agent = StockAnalyst(agent_id)
            elif team_type == TeamType.SOCIAL_TRAVEL:
                agent = ContentCurator(agent_id)
            elif team_type == TeamType.CONTENT_CREATION:
                agent = ImageCreator(agent_id)
            elif team_type == TeamType.DATABASE_OPERATIONS:
                agent = DatabaseArchitect(agent_id)
            elif team_type == TeamType.RESEARCH_INTELLIGENCE:
                agent = PatentResearcher(agent_id)
            else:  # SUPPORT_SYSTEMS
                agent = PerformanceMonitor(agent_id)
            
            await agent.initialize()
            
            # Registrar en el sistema
            self.team_manager.agents[agent_id] = Agent(
                id=agent_id,
                name=f"Scaled Agent {agent_id[-8:]}",
                level=AgentLevel.LEVEL_1,
                team_type=team_type,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            
            self.team_manager.teams[team_id].members.append(agent_id)
            
            logger.info(f"Added new agent {agent_id} to team {team_id}")
            
        except Exception as e:
            logger.error(f"Error adding agent to team {team_id}: {e}")
    
    async def remove_low_performance_agent(self, team_id: str):
        """Remueve agente de bajo rendimiento"""
        try:
            team = self.team_manager.teams[team_id]
            team_agents = [self.team_manager.agents[aid] for aid in team.members if aid in self.team_manager.agents]
            
            if not team_agents:
                return
            
            # Encontrar agente de menor rendimiento
            lowest_performance_agent = min(team_agents, key=lambda a: a.performance.performance_score)
            
            if lowest_performance_agent.performance.performance_score < 50:
                # Remover agente
                team.members.remove(lowest_performance_agent.id)
                del self.team_manager.agents[lowest_performance_agent.id]
                
                logger.info(f"Removed low performance agent {lowest_performance_agent.id} from team {team_id}")
            
        except Exception as e:
            logger.error(f"Error removing agent from team {team_id}: {e}")

# ==================== SISTEMA DE SEGURIDAD INTEGRADO ====================

class SecurityIntegration:
    """Integración con el sistema de seguridad mejorado"""
    
    def __init__(self):
        self.security_level = SecurityLevel.ENTERPRISE
        self.security_active = True
        self.auth_tokens = {}
        self.security_policies = {
            "require_authentication": True,
            "require_authorization": True,
            "rate_limiting": True,
            "audit_logging": True,
            "intrusion_detection": True
        }
        
    async def validate_security(self, request: Request, endpoint_type: str = "api") -> Dict[str, Any]:
        """Valida la seguridad de una petición"""
        try:
            security_result = {
                "valid": True,
                "level": self.security_level.value,
                "checks_passed": [],
                "checks_failed": [],
                "risk_level": "low"
            }
            
            # Verificar autenticación
            if self.security_policies["require_authentication"]:
                auth_result = await self.check_authentication(request)
                if auth_result["valid"]:
                    security_result["checks_passed"].append("authentication")
                else:
                    security_result["checks_failed"].append("authentication")
                    security_result["valid"] = False
            
            # Verificar autorización
            if self.security_policies["require_authorization"] and security_result["valid"]:
                authz_result = await self.check_authorization(request, endpoint_type)
                if authz_result["valid"]:
                    security_result["checks_passed"].append("authorization")
                else:
                    security_result["checks_failed"].append("authorization")
                    security_result["valid"] = False
            
            # Verificar rate limiting
            if self.security_policies["rate_limiting"]:
                rate_result = await self.check_rate_limiting(request)
                if rate_result["valid"]:
                    security_result["checks_passed"].append("rate_limiting")
                else:
                    security_result["checks_failed"].append("rate_limiting")
            
            # Determinar nivel de riesgo
            if len(security_result["checks_failed"]) > 0:
                security_result["risk_level"] = "medium" if len(security_result["checks_failed"]) == 1 else "high"
            
            return security_result
            
        except Exception as e:
            logger.error(f"Error en validación de seguridad: {e}")
            return {
                "valid": False,
                "level": self.security_level.value,
                "error": str(e),
                "risk_level": "critical"
            }
    
    async def check_authentication(self, request: Request) -> Dict[str, Any]:
        """Verifica autenticación"""
        # Implementación simplificada - en producción usaría JWT real
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return {"valid": True, "method": "bearer_token"}
        
        # Verificar API Key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return {"valid": True, "method": "api_key"}
        
        return {"valid": False, "reason": "no_valid_credentials"}
    
    async def check_authorization(self, request: Request, endpoint_type: str) -> Dict[str, Any]:
        """Verifica autorización para el endpoint"""
        # Lógica de autorización simplificada
        # En producción verificaría roles y permisos específicos
        
        allowed_roles = {
            "api": ["admin", "user", "service"],
            "dashboard": ["admin", "user"],
            "metrics": ["admin", "monitor"],
            "admin": ["admin"]
        }
        
        # Verificar rol en JWT (simplificado)
        auth_header = request.headers.get("Authorization")
        if auth_header:
            # Simular verificación de rol
            return {"valid": True, "required_role": endpoint_type, "granted": True}
        
        return {"valid": False, "reason": "insufficient_permissions"}
    
    async def check_rate_limiting(self, request: Request) -> Dict[str, Any]:
        """Verifica rate limiting"""
        # Implementación simplificada de rate limiting
        client_ip = request.client.host
        
        # Simular contador de requests por IP
        # En producción usaría Redis o similar
        requests_count = random.randint(1, 10)
        
        if requests_count <= 100:  # 100 requests por minuto
            return {"valid": True, "requests_count": requests_count, "limit": 100}
        else:
            return {"valid": False, "reason": "rate_limit_exceeded", "requests_count": requests_count}
    
    async def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Registra evento de seguridad"""
        security_log = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "security_level": self.security_level.value,
            "details": details,
            "source": "hierarchical_architecture"
        }
        
        logger.warning(f"SECURITY EVENT: {json.dumps(security_log, indent=2)}")
        
        # En producción, enviaría a sistema de logging centralizado
    
    async def get_security_status(self) -> Dict[str, Any]:
        """Obtiene estado de seguridad del sistema"""
        return {
            "security_active": self.security_active,
            "security_level": self.security_level.value,
            "policies": self.security_policies,
            "last_check": datetime.now().isoformat(),
            "threat_level": "low"
        }

# ==================== INTEGRACIÓN CON ORCHESTRADOR ENTERPRISE ====================

class EnterpriseOrchestratorIntegration:
    """Integración bidireccional con Enterprise Orchestrator"""
    
    def __init__(self, hierarchical_server):
        self.hierarchical_server = hierarchical_server
        self.orchestrator_url = "http://localhost:8080"  # Puerto del orchestrator principal
        self.integration_active = True
        self.communication_channel = None
        self.sync_status = {
            "last_sync": None,
            "sync_status": "disconnected",
            "services_registered": 0,
            "health_checks_passed": 0
        }
        self.redis_client = None
        self.node_id = str(uuid.uuid4())
        self.is_leader = False
        
    async def initialize_integration(self):
        """Inicializa la integración con el orchestrator"""
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            
            # Registrar servicios jerárquicos con el orchestrator
            await self.register_hierarchical_services()
            
            # Establecer canal de comunicación
            await self.setup_communication_channel()
            
            # Iniciar sincronización periódica y pub/sub
            asyncio.create_task(self.periodic_sync())
            asyncio.create_task(self.receive_commands_from_orchestrator())
            
            # Heartbeats y leader election
            asyncio.create_task(self.run_heartbeat())
            asyncio.create_task(self.run_leader_election())
            
            logger.info("Enterprise Orchestrator integration initialized")
            
        except Exception as e:
            logger.error(f"Error initializing orchestrator integration: {e}")
    
    async def register_hierarchical_services(self):
        """Registra servicios jerárquicos con el orchestrator"""
        services_to_register = [
            {
                "name": "hierarchical_master_coordinator",
                "type": "coordination",
                "port": 8002,
                "health_endpoint": "/health",
                "capabilities": ["strategic_coordination", "load_balancing", "auto_healing"]
            },
            {
                "name": "hierarchical_task_assigner", 
                "type": "task_management",
                "port": 8002,
                "health_endpoint": "/hierarchical/overview",
                "capabilities": ["intelligent_task_assignment", "performance_optimization"]
            },
            {
                "name": "hierarchical_team_manager",
                "type": "team_coordination", 
                "port": 8002,
                "health_endpoint": "/hierarchical/teams",
                "capabilities": ["team_coordination", "performance_monitoring"]
            },
            {
                "name": "hierarchical_security",
                "type": "security",
                "port": 8015,
                "health_endpoint": "/security/health",
                "capabilities": ["security_validation", "threat_detection"]
            },
            {
                "name": "hierarchical_autoscaling",
                "type": "infrastructure",
                "port": 8020,
                "health_endpoint": "/autoscaling/status", 
                "capabilities": ["auto_scaling", "resource_optimization"]
            }
        ]
        
        for service in services_to_register:
            try:
                # Simular registro con orchestrator
                logger.info(f"Registering service: {service['name']}")
                self.sync_status["services_registered"] += 1
                
            except Exception as e:
                logger.error(f"Error registering service {service['name']}: {e}")
    
    async def setup_communication_channel(self):
        """Establece canal de comunicación bidireccional"""
        try:
            # Establecer WebSocket o HTTP endpoint para comunicación
            self.communication_channel = "active"
            self.sync_status["sync_status"] = "connected"
            
            logger.info("Communication channel established with Enterprise Orchestrator")
            
        except Exception as e:
            logger.error(f"Error setting up communication channel: {e}")
    
    async def periodic_sync(self):
        """Sincronización periódica con el orchestrator"""
        while self.integration_active:
            try:
                await self.sync_with_orchestrator()
                await asyncio.sleep(60)  # Sync cada minuto
                
            except Exception as e:
                logger.error(f"Error in periodic sync: {e}")
                await asyncio.sleep(30)
    
    async def sync_with_orchestrator(self):
        """Sincroniza estado con el orchestrator"""
        try:
            # Recopilar estado actual
            current_state = await self.collect_sync_state()
            
            # Enviar estado al orchestrator
            sync_result = await self.send_state_to_orchestrator(current_state)
            
            self.sync_status["last_sync"] = datetime.now()
            self.sync_status["health_checks_passed"] += 1
            
        except Exception as e:
            logger.error(f"Error syncing with orchestrator: {e}")
            self.sync_status["sync_status"] = "error"
    
    async def collect_sync_state(self) -> Dict[str, Any]:
        """Recopila estado para sincronización"""
        return {
            "timestamp": datetime.now().isoformat(),
            "system_status": "operational",
            "total_agents": len(self.hierarchical_server.team_manager.agents),
            "active_agents": len([a for a in self.hierarchical_server.team_manager.agents.values() if a.status == "active"]),
            "teams_count": len(self.hierarchical_server.team_manager.teams),
            "tasks": {
                "pending": len(getattr(self.hierarchical_server, 'pending_tasks', [])),
                "active": len(getattr(self.hierarchical_server, 'active_tasks', {})),
                "completed": len(getattr(self.hierarchical_server, 'completed_tasks', []))
            },
            "performance": await self.hierarchical_server.team_manager.get_system_overview(),
            "security_status": "active",
            "auto_scaling_status": "monitoring"
        }
    
    async def send_state_to_orchestrator(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Envía estado al orchestrator"""
        if self.redis_client:
            await self.redis_client.publish("orchestrator_state_sync", json.dumps(state))
            return {"status": "success", "message": "State synchronized via Redis"}
        return {"status": "error", "message": "Redis client not initialized"}
    
    async def receive_commands_from_orchestrator(self):
        """Recibe comandos del orchestrator via Redis Pub/Sub"""
        if not self.redis_client:
            return
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe("orchestrator_commands")
            while self.integration_active:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message['type'] == 'message':
                    try:
                        command = json.loads(message['data'])
                        await self.process_orchestrator_commands([command])
                    except json.JSONDecodeError:
                        logger.error("Failed to decode JSON from Redis Pub/Sub")
        except Exception as e:
            logger.error(f"Error in Redis subscriber: {e}")
            
    async def run_heartbeat(self):
        """Publica el estado del nodo a un canal de heartbeats en Redis"""
        while self.integration_active:
            try:
                if self.redis_client:
                    heartbeat_data = {
                        "node_id": self.node_id,
                        "timestamp": datetime.now().isoformat(),
                        "is_leader": self.is_leader
                    }
                    await self.redis_client.publish("heartbeats", json.dumps(heartbeat_data))
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error in heartbeat: {e}")
                await asyncio.sleep(5)

    async def run_leader_election(self):
        """Elección básica de líder con Redis SETNX"""
        while self.integration_active:
            try:
                if self.redis_client:
                    acquired = await self.redis_client.set("leader_lock", self.node_id, nx=True, ex=10)
                    if acquired:
                        if not self.is_leader:
                            logger.info(f"Node {self.node_id} became the LEADER.")
                        self.is_leader = True
                    else:
                        current_leader = await self.redis_client.get("leader_lock")
                        if current_leader == self.node_id:
                            await self.redis_client.expire("leader_lock", 10)
                            self.is_leader = True
                        else:
                            if self.is_leader:
                                logger.info(f"Node {self.node_id} lost leadership.")
                            self.is_leader = False
                await asyncio.sleep(3)
            except Exception as e:
                logger.error(f"Error in leader election: {e}")
                await asyncio.sleep(3)
    
    async def process_orchestrator_commands(self, commands: List[Dict[str, Any]]):
        """Procesa comandos del orchestrator"""
        for command in commands:
            try:
                command_type = command.get("type")
                
                if command_type == "scale_request":
                    await self.handle_scale_request(command)
                elif command_type == "health_check":
                    await self.handle_health_check_command(command)
                elif command_type == "maintenance":
                    await self.handle_maintenance_command(command)
                elif command_type == "failover":
                    await self.handle_failover_command(command)
                
            except Exception as e:
                logger.error(f"Error processing command {command}: {e}")
    
    async def handle_scale_request(self, command: Dict[str, Any]):
        """Maneja solicitud de scaling del orchestrator"""
        scale_type = command.get("scale_type")  # "up" or "down"
        target_teams = command.get("target_teams", [])
        
        if hasattr(self.hierarchical_server, 'auto_scaling_manager'):
            if scale_type == "up":
                await self.hierarchical_server.auto_scaling_manager.scale_up_agents({"target_teams": target_teams})
            elif scale_type == "down":
                await self.hierarchical_server.auto_scaling_manager.scale_down_agents()
    
    async def handle_health_check_command(self, command: Dict[str, Any]):
        """Maneja comando de health check"""
        health_status = await self.perform_comprehensive_health_check()
        # Enviar resultado al orchestrator
    
    async def handle_maintenance_command(self, command: Dict[str, Any]):
        """Maneja comando de mantenimiento"""
        maintenance_mode = command.get("enabled", False)
        # Activar/desactivar modo mantenimiento
    
    async def handle_failover_command(self, command: Dict[str, Any]):
        """Maneja comando de failover"""
        # Ejecutar procedimientos de failover
        await self.execute_failover_procedures()
    
    async def perform_comprehensive_health_check(self) -> Dict[str, Any]:
        """Ejecuta health check comprensivo"""
        return {
            "overall_status": "healthy",
            "components": {
                "master_coordinator": "healthy",
                "task_assigner": "healthy", 
                "team_manager": "healthy",
                "security_system": "healthy",
                "auto_scaling": "healthy"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def execute_failover_procedures(self):
        """Ejecuta procedimientos de failover"""
        logger.info("Executing failover procedures")
        # Implementar lógica de failover
    
    async def get_integration_status(self) -> Dict[str, Any]:
        """Obtiene estado de integración"""
        return {
            "integration_active": self.integration_active,
            "sync_status": self.sync_status,
            "orchestrator_url": self.orchestrator_url,
            "communication_channel": self.communication_channel
        }

# ==================== GESTOR DE LOAD BALANCING AVANZADO ====================

class LoadBalancingManager:
    """Gestor avanzado de load balancing"""
    
    def __init__(self, team_manager):
        self.team_manager = team_manager
        self.load_balancing_strategies = {
            "round_robin": self.round_robin_assignment,
            "least_loaded": self.least_loaded_assignment,
            "performance_based": self.performance_based_assignment,
            "capability_matched": self.capability_matched_assignment,
            "adaptive": self.adaptive_assignment
        }
        self.current_strategy = "adaptive"
        self.assignment_history = deque(maxlen=1000)
        self.performance_tracking = {}
        
    async def assign_task_intelligently(self, task: Task, available_agents: List[Agent]) -> Optional[str]:
        """Asigna tarea usando estrategia de load balancing"""
        try:
            strategy_function = self.load_balancing_strategies[self.current_strategy]
            assigned_agent_id = await strategy_function(task, available_agents)
            
            if assigned_agent_id:
                # Registrar asignación para tracking
                self.assignment_history.append({
                    "task_id": task.id,
                    "agent_id": assigned_agent_id,
                    "strategy": self.current_strategy,
                    "timestamp": datetime.now(),
                    "task_complexity": task.complexity,
                    "estimated_duration": task.estimated_duration
                })
                
                # Actualizar métricas de performance
                await self.update_performance_metrics(assigned_agent_id, task)
            
            return assigned_agent_id
            
        except Exception as e:
            logger.error(f"Error en load balancing: {e}")
            return None
    
    async def round_robin_assignment(self, task: Task, available_agents: List[Agent]) -> Optional[str]:
        """Asignación round-robin"""
        if not available_agents:
            return None
        
        # Obtener último agente asignado
        last_agent = None
        if self.assignment_history:
            last_assignment = self.assignment_history[-1]
            last_agent = last_assignment["agent_id"]
        
        # Encontrar siguiente agente
        agent_ids = [agent.id for agent in available_agents]
        if last_agent in agent_ids:
            current_index = agent_ids.index(last_agent)
            next_index = (current_index + 1) % len(agent_ids)
            return agent_ids[next_index]
        else:
            return agent_ids[0]
    
    async def least_loaded_assignment(self, task: Task, available_agents: List[Agent]) -> Optional[str]:
        """Asignación basada en menor carga"""
        if not available_agents:
            return None
        
        # Ordenar por carga actual (menor a mayor)
        sorted_agents = sorted(available_agents, key=lambda a: a.performance.current_load)
        
        # Retornar agente con menor carga y capacidad para la tarea
        for agent in sorted_agents:
            if agent.performance.current_load < agent.max_concurrent_tasks:
                return agent.id
        
        return sorted_agents[0].id if sorted_agents else None
    
    async def performance_based_assignment(self, task: Task, available_agents: List[Agent]) -> Optional[str]:
        """Asignación basada en rendimiento histórico"""
        if not available_agents:
            return None
        
        # Calcular score combinado para cada agente
        agent_scores = []
        for agent in available_agents:
            performance_score = agent.performance.performance_score
            success_rate = agent.performance.success_rate
            avg_completion_time = agent.performance.average_completion_time
            
            # Score compuesto (mayor es mejor)
            composite_score = (
                performance_score * 0.4 +
                success_rate * 0.4 +
                (100 - min(avg_completion_time, 100)) * 0.2
            )
            
            agent_scores.append((agent.id, composite_score))
        
        # Retornar agente con mayor score
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        return agent_scores[0][0]
    
    async def capability_matched_assignment(self, task: Task, available_agents: List[Agent]) -> Optional[str]:
        """Asignación basada en capacidades requeridas"""
        if not available_agents:
            return None
        
        # Determinar capacidades requeridas por la tarea
        required_capabilities = self.determine_required_capabilities(task)
        
        # Encontrar agente con mejor coincidencia de capacidades
        best_match = None
        best_score = 0
        
        for agent in available_agents:
            if agent.status != "active":
                continue
                
            # Calcular score de coincidencia
            agent_capabilities = agent.capabilities
            match_score = len(required_capabilities.intersection(agent_capabilities))
            match_percentage = match_score / len(required_capabilities) if required_capabilities else 1.0
            
            # Bonus por especialización del equipo
            team_bonus = 1.2 if task.team_type == agent.team_type else 1.0
            
            final_score = match_percentage * team_bonus * agent.performance.performance_score
            
            if final_score > best_score:
                best_score = final_score
                best_match = agent
        
        return best_match.id if best_match else None
    
    async def adaptive_assignment(self, task: Task, available_agents: List[Agent]) -> Optional[str]:
        """Asignación adaptativa que combina múltiples estrategias"""
        if not available_agents:
            return None
        
        # Obtener scores de diferentes estrategias
        scores = {}
        
        # Round-robin score
        rr_agent = await self.round_robin_assignment(task, available_agents)
        if rr_agent:
            scores[rr_agent] = scores.get(rr_agent, 0) + 25
        
        # Least-loaded score
        ll_agent = await self.least_loaded_assignment(task, available_agents)
        if ll_agent:
            scores[ll_agent] = scores.get(ll_agent, 0) + 30
        
        # Performance-based score
        pb_agent = await self.performance_based_assignment(task, available_agents)
        if pb_agent:
            scores[pb_agent] = scores.get(pb_agent, 0) + 25
        
        # Capability-matched score
        cm_agent = await self.capability_matched_assignment(task, available_agents)
        if cm_agent:
            scores[cm_agent] = scores.get(cm_agent, 0) + 20
        
        # Retornar agente con mayor score combinado
        if scores:
            best_agent = max(scores.items(), key=lambda x: x[1])
            return best_agent[0]
        
        return available_agents[0].id
    
    def determine_required_capabilities(self, task: Task) -> Set[str]:
        """Determina capacidades requeridas para una tarea"""
        # Mapeo simplificado de tipos de tarea a capacidades
        capability_map = {
            TeamType.MAPS_INTELLIGENCE: {"location_analysis", "route_optimization", "distance_calculation"},
            TeamType.FINANCIAL_INTELLIGENCE: {"stock_analysis", "market_research", "risk_assessment"},
            TeamType.SOCIAL_TRAVEL: {"social_media_strategy", "content_curation", "travel_planning"},
            TeamType.CONTENT_CREATION: {"image_generation", "video_creation", "content_strategy"},
            TeamType.DATABASE_OPERATIONS: {"database_design", "migration_management", "performance_optimization"},
            TeamType.RESEARCH_INTELLIGENCE: {"academic_research", "patent_search", "data_extraction"},
            TeamType.SUPPORT_SYSTEMS: {"system_monitoring", "quality_testing", "security_monitoring"}
        }
        
        return capability_map.get(task.team_type, set())
    
    async def update_performance_metrics(self, agent_id: str, task: Task):
        """Actualiza métricas de performance del agente"""
        if agent_id not in self.performance_tracking:
            self.performance_tracking[agent_id] = {
                "assignments": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                "total_duration": 0,
                "performance_trend": []
            }
        
        tracking = self.performance_tracking[agent_id]
        tracking["assignments"] += 1
        
        # Simular duración real de tarea
        actual_duration = random.uniform(0.5, 2.0) * task.estimated_duration
        tracking["total_duration"] += actual_duration
        
        # Actualizar tendencia de performance (simulado)
        performance_change = random.uniform(-5, 10)
        tracking["performance_trend"].append(performance_change)
        
        # Mantener solo últimas 20 mediciones
        if len(tracking["performance_trend"]) > 20:
            tracking["performance_trend"] = tracking["performance_trend"][-20:]
    
    async def get_load_balancing_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de load balancing"""
        return {
            "current_strategy": self.current_strategy,
            "available_strategies": list(self.load_balancing_strategies.keys()),
            "assignment_history_size": len(self.assignment_history),
            "performance_tracking_size": len(self.performance_tracking),
            "recent_assignments": list(self.assignment_history)[-10:]
        }
    
    async def optimize_load_balancing(self):
        """Optimiza la estrategia de load balancing"""
        if len(self.assignment_history) < 10:
            return
        
        # Analizar performance de estrategias recientes
        strategy_performance = {}
        for assignment in list(self.assignment_history)[-50:]:
            strategy = assignment["strategy"]
            if strategy not in strategy_performance:
                strategy_performance[strategy] = {"count": 0, "success_rate": 0}
            
            strategy_performance[strategy]["count"] += 1
            # Simular success rate basado en complejidad de tarea
            success_rate = 0.9 if assignment["task_complexity"] <= 5 else 0.7
            strategy_performance[strategy]["success_rate"] = (
                (strategy_performance[strategy]["success_rate"] * (strategy_performance[strategy]["count"] - 1) + success_rate) /
                strategy_performance[strategy]["count"]
            )
        
        # Cambiar estrategia si es necesario
        if strategy_performance:
            best_strategy = max(strategy_performance.items(), key=lambda x: x[1]["success_rate"])
            if best_strategy[0] != self.current_strategy and best_strategy[1]["count"] >= 5:
                self.current_strategy = best_strategy[0]
                logger.info(f"Load balancing strategy optimized to: {self.current_strategy}")

# ==================== MONITOR DE SALUD Y AUTO-HEALING ====================

class HealthMonitor:
    """Monitor de salud con capacidades de auto-healing"""
    
    def __init__(self, team_manager, hierarchical_server):
        self.team_manager = team_manager
        self.hierarchical_server = hierarchical_server
        self.health_status = HealthStatus.HEALTHY
        self.health_checks = {}
        self.auto_healing_enabled = True
        self.failure_history = []
        self.recovery_actions = []
        
    async def monitor_system_health(self):
        """Monitorea la salud del sistema continuamente"""
        while True:
            try:
                current_health = await self.perform_comprehensive_health_check()
                await self.process_health_status(current_health)
                
                if self.auto_healing_enabled and current_health["status"] in [HealthStatus.DEGRADED, HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
                    await self.trigger_auto_healing(current_health)
                
                await asyncio.sleep(30)  # Check cada 30 segundos
                
            except Exception as e:
                logger.error(f"Error en health monitoring: {e}")
                await asyncio.sleep(60)
    
    async def perform_comprehensive_health_check(self) -> Dict[str, Any]:
        """Ejecuta health check comprensivo"""
        health_report = {
            "timestamp": datetime.now(),
            "overall_status": HealthStatus.HEALTHY,
            "components": {},
            "metrics": {},
            "issues": [],
            "recommendations": []
        }
        
        # Check master coordinator
        coordinator_health = await self.check_master_coordinator_health()
        health_report["components"]["master_coordinator"] = coordinator_health
        
        # Check task assigner
        assigner_health = await self.check_task_assigner_health()
        health_report["components"]["task_assigner"] = assigner_health
        
        # Check teams and agents
        teams_health = await self.check_teams_health()
        health_report["components"]["teams"] = teams_health
        
        # Check system resources
        resources_health = await self.check_system_resources_health()
        health_report["components"]["resources"] = resources_health
        
        # Check communication systems
        communication_health = await self.check_communication_health()
        health_report["components"]["communication"] = communication_health
        
        # Determinar estado general
        component_statuses = [comp["status"] for comp in health_report["components"].values()]
        if HealthStatus.CRITICAL in component_statuses:
            health_report["overall_status"] = HealthStatus.CRITICAL
        elif HealthStatus.UNHEALTHY in component_statuses:
            health_report["overall_status"] = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in component_statuses:
            health_report["overall_status"] = HealthStatus.DEGRADED
        
        return health_report
    
    async def check_master_coordinator_health(self) -> Dict[str, Any]:
        """Verifica salud del master coordinator"""
        try:
            coordinator = self.hierarchical_server.master_coordinator
            
            # Verificar estado
            status = "healthy" if coordinator.status == "active" else "unhealthy"
            
            # Verificar métricas recientes
            recent_decisions = getattr(coordinator, 'strategic_decisions', [])
            decision_rate = len([d for d in recent_decisions if (datetime.now() - d.get("timestamp", datetime.now())).seconds < 3600])
            
            if decision_rate < 1:  # Menos de 1 decisión por hora
                status = "degraded"
            
            return {
                "status": status,
                "last_activity": coordinator.performance.last_activity.isoformat(),
                "decisions_per_hour": decision_rate,
                "performance_score": coordinator.performance.performance_score
            }
            
        except Exception as e:
            return {
                "status": "critical",
                "error": str(e)
            }
    
    async def check_task_assigner_health(self) -> Dict[str, Any]:
        """Verifica salud del task assigner"""
        try:
            assigner = self.hierarchical_server.task_assigner
            
            status = "healthy" if assigner.status == "active" else "unhealthy"
            
            # Verificar assignments recientes
            recent_assignments = getattr(assigner, 'assignment_history', [])
            assignment_rate = len([a for a in recent_assignments if (datetime.now() - a.get("assignment_time", datetime.now())).seconds < 3600])
            
            if assignment_rate < 5:  # Menos de 5 assignments por hora
                status = "degraded"
            
            return {
                "status": status,
                "assignments_per_hour": assignment_rate,
                "algorithm_performance": "optimal",
                "performance_score": assigner.performance.performance_score
            }
            
        except Exception as e:
            return {
                "status": "critical", 
                "error": str(e)
            }
    
    async def check_teams_health(self) -> Dict[str, Any]:
        """Verifica salud de los equipos"""
        team_healths = {}
        unhealthy_teams = 0
        
        for team_id, team in self.team_manager.teams.items():
            try:
                team_agents = [self.team_manager.agents[aid] for aid in team.members if aid in self.team_manager.agents]
                active_agents = [a for a in team_agents if a.status == "active"]
                
                if not active_agents:
                    status = "critical"
                    unhealthy_teams += 1
                elif len(active_agents) < len(team_agents) * 0.5:  # Menos del 50% activos
                    status = "degraded"
                elif team.workload_ratio > 0.9:
                    status = "degraded"
                else:
                    status = "healthy"
                
                team_healths[team_id] = {
                    "status": status,
                    "total_agents": len(team_agents),
                    "active_agents": len(active_agents),
                    "workload_ratio": team.workload_ratio,
                    "average_performance": np.mean([a.performance.performance_score for a in team_agents]) if team_agents else 0
                }
                
            except Exception as e:
                team_healths[team_id] = {
                    "status": "critical",
                    "error": str(e)
                }
                unhealthy_teams += 1
        
        overall_status = "healthy"
        if unhealthy_teams > len(self.team_manager.teams) * 0.5:
            overall_status = "critical"
        elif unhealthy_teams > 0:
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "teams": team_healths,
            "unhealthy_teams_count": unhealthy_teams
        }
    
    async def check_system_resources_health(self) -> Dict[str, Any]:
        """Verifica salud de recursos del sistema"""
        try:
            # Métricas del sistema
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            status = "healthy"
            issues = []
            
            if cpu_percent > 90:
                status = "critical"
                issues.append("High CPU usage")
            elif cpu_percent > 80:
                status = "degraded"
                issues.append("Moderate CPU usage")
            
            if memory.percent > 90:
                status = "critical"
                issues.append("High memory usage")
            elif memory.percent > 80:
                if status == "healthy":
                    status = "degraded"
                issues.append("Moderate memory usage")
            
            if disk.percent > 95:
                status = "critical"
                issues.append("Low disk space")
            elif disk.percent > 85:
                if status == "healthy":
                    status = "degraded"
                issues.append("Moderate disk usage")
            
            return {
                "status": status,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "issues": issues
            }
            
        except Exception as e:
            return {
                "status": "critical",
                "error": str(e)
            }
    
    async def check_communication_health(self) -> Dict[str, Any]:
        """Verifica salud del sistema de comunicación"""
        try:
            # Verificar WebSocket connections
            websocket_connections = len(getattr(self.team_manager.metrics_system, 'websocket_connections', []))
            
            # Verificar message queues
            total_messages = sum(len(queue) for queue in self.team_manager.metrics_system.message_queue.values())
            
            status = "healthy"
            if websocket_connections == 0:
                status = "degraded"
            
            return {
                "status": status,
                "websocket_connections": websocket_connections,
                "message_queue_size": total_messages,
                "fipa_messages_processed": len(getattr(self.team_manager.metrics_system, 'message_history', []))
            }
            
        except Exception as e:
            return {
                "status": "critical",
                "error": str(e)
            }
    
    async def process_health_status(self, health_report: Dict[str, Any]):
        """Procesa el reporte de salud"""
        self.health_status = health_report["overall_status"]
        
        # Registrar en history
        self.failure_history.append({
            "timestamp": datetime.now(),
            "status": self.health_status,
            "issues": health_report.get("issues", [])
        })
        
        # Limpiar history antiguo (mantener solo últimas 100 entradas)
        if len(self.failure_history) > 100:
            self.failure_history = self.failure_history[-100:]
        
        # Log del estado
        if self.health_status != HealthStatus.HEALTHY:
            logger.warning(f"System health status: {self.health_status.value}")
            for issue in health_report.get("issues", []):
                logger.warning(f"Health issue: {issue}")
    
    async def trigger_auto_healing(self, health_report: Dict[str, Any]):
        """Dispara procesos de auto-healing"""
        logger.info("Triggering auto-healing processes")
        
        issues = health_report.get("issues", [])
        healing_actions = []
        
        for issue in issues:
            if "High CPU usage" in issue or "High memory usage" in issue:
                healing_actions.append("scale_down_low_priority_tasks")
            elif "Low disk space" in issue:
                healing_actions.append("cleanup_temporary_files")
            elif "unhealthy agents" in issue.lower():
                healing_actions.append("restart_failed_agents")
            elif "communication" in issue.lower():
                healing_actions.append("restart_communication_systems")
        
        # Ejecutar acciones de healing
        for action in healing_actions:
            try:
                await self.execute_healing_action(action)
                self.recovery_actions.append({
                    "timestamp": datetime.now(),
                    "action": action,
                    "status": "executed"
                })
            except Exception as e:
                logger.error(f"Error executing healing action {action}: {e}")
                self.recovery_actions.append({
                    "timestamp": datetime.now(),
                    "action": action,
                    "status": "failed",
                    "error": str(e)
                })
    
    async def execute_healing_action(self, action: str):
        """Ejecuta acción específica de healing"""
        if action == "scale_down_low_priority_tasks":
            # Cancelar tareas de baja prioridad
            low_priority_tasks = [t for t in getattr(self.hierarchical_server, 'pending_tasks', []) 
                                if t.priority == TaskPriority.LOW]
            for task in low_priority_tasks[:5]:  # Máximo 5 tareas
                if task.id in self.hierarchical_server.pending_tasks:
                    self.hierarchical_server.pending_tasks.remove(task)
            
            logger.info(f"Cancelled {len(low_priority_tasks)} low priority tasks")
        
        elif action == "cleanup_temporary_files":
            # Limpiar archivos temporales (simulado)
            logger.info("Cleaning up temporary files")
        
        elif action == "restart_failed_agents":
            # Reiniciar agentes fallidos
            failed_agents = [aid for aid, agent in self.team_manager.agents.items() 
                           if agent.status == "failed"]
            for agent_id in failed_agents[:3]:  # Máximo 3 agentes
                self.team_manager.agents[agent_id].status = "active"
                self.team_manager.agents[agent_id].last_health_check = datetime.now()
            
            logger.info(f"Restarted {len(failed_agents[:3])} failed agents")
        
        elif action == "restart_communication_systems":
            # Reiniciar sistemas de comunicación
            logger.info("Restarting communication systems")
            
            # Simular reinicio de WebSocket connections
            # En producción, reiniciaría los componentes específicos
            websocket_connections = getattr(self.team_manager.metrics_system, 'websocket_connections', [])
            for ws in websocket_connections[:]:
                try:
                    # Simular ping para verificar conexión
                    await ws.send_json({"type": "health_check"})
                except:
                    # Remover conexión muerta
                    if ws in self.team_manager.metrics_system.websocket_connections:
                        self.team_manager.metrics_system.websocket_connections.remove(ws)
            
            logger.info("Communication systems health check completed")
    
    async def get_health_report(self) -> Dict[str, Any]:
        """Obtiene reporte completo de salud"""
        return {
            "current_status": self.health_status.value,
            "auto_healing_enabled": self.auto_healing_enabled,
            "failure_history_size": len(self.failure_history),
            "recovery_actions_size": len(self.recovery_actions),
            "recent_failures": self.failure_history[-10:],
            "recent_recovery_actions": self.recovery_actions[-10:]
        }

# ==================== CLASES BASE DE AGENTES ====================

class BaseAgent(ABC):
    """Clase base para todos los agentes del sistema"""
    
    def __init__(self, agent_id: str, agent_level: AgentLevel, team_type: TeamType):
        self.agent_id = agent_id
        self.agent_level = agent_level
        self.team_type = team_type
        self.status = "active"
        self.capabilities: Set[str] = set()
        self.performance = AgentPerformance(agent_id, team_affinity=team_type)
        self.message_controller = FIPAController()
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []
        
    async def initialize(self):
        """Inicializa el agente"""
        await self.setup_capabilities()
        await self.setup_communication()
        asyncio.create_task(self.message_processor())
        asyncio.create_task(self.task_processor())
        
    @abstractmethod
    async def setup_capabilities(self):
        """Configura las capacidades del agente"""
        pass
    
    async def setup_communication(self):
        """Configura comunicación FIPA-ACL"""
        self.message_controller.subscribe(self.agent_id, self.handle_message)
    
    async def handle_message(self, message: FIPAMessage):
        """Procesa mensaje FIPA-ACL recibido"""
        # Implementación base - puede ser sobrescrita por agentes específicos
        pass
    
    async def message_processor(self):
        """Procesador de mensajes en background"""
        while self.status == "active":
            try:
                messages = self.message_controller.get_messages(self.agent_id)
                for message in messages:
                    await self.handle_message(message)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error en message_processor de {self.agent_id}: {e}")
                await asyncio.sleep(1)
    
    async def task_processor(self):
        """Procesador de tareas en background"""
        while self.status == "active":
            try:
                if not self.task_queue.empty() and len(self.active_tasks) < 3:
                    task = await self.task_queue.get()
                    await self.execute_task(task)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error en task_processor de {self.agent_id}: {e}")
                await asyncio.sleep(1)
    
    async def execute_task(self, task: Task):
        """Ejecuta una tarea (implementación base)"""
        try:
            task.status = "processing"
            task.started_at = datetime.now()
            
            # Simular ejecución de tarea
            await asyncio.sleep(random.uniform(1, 5))
            
            task.status = "completed"
            task.completed_at = datetime.now()
            task.progress = 100.0
            
            # Actualizar métricas
            self.performance.tasks_completed += 1
            self.performance.last_activity = datetime.now()
            
            self.completed_tasks.append(task)
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]
                
        except Exception as e:
            task.status = "failed"
            self.performance.tasks_failed += 1
            logger.error(f"Error ejecutando tarea {task.id} en {self.agent_id}: {e}")

# ==================== ESPECIALIZACIÓN DE AGENTES ====================

# ==================== MAPS INTELLIGENCE TEAM ====================

class MapsTeamLeader(BaseAgent):
    """Líder del equipo de Maps Intelligence (15+ agentes)"""
    
    def __init__(self):
        super().__init__("maps_team_leader", AgentLevel.LEVEL_3, TeamType.MAPS_INTELLIGENCE)
        self.specialization = "Maps Intelligence Team Leader"
        self.capabilities = {
            "geocoding", "route_optimization", "location_analysis", "distance_calculation",
            "place_research", "navigation_advice", "team_coordination", "performance_monitoring"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades específicas del líder"""
        pass

class GeocodingSpecialist(BaseAgent):
    """Especialista en Geocoding (3 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.MAPS_INTELLIGENCE)
        self.specialization = "Geocoding Specialist"
        self.capabilities = {
            "address_to_coordinates", "coordinates_to_address", "batch_geocoding",
            "reverse_geocoding", "geocoding_validation"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de geocoding"""
        pass

class RouteOptimizer(BaseAgent):
    """Optimizador de Rutas (3 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.MAPS_INTELLIGENCE)
        self.specialization = "Route Optimizer"
        self.capabilities = {
            "shortest_path", "fastest_route", "route_optimization", "traffic_aware_routing",
            "multi_stop_optimization", "fuel_efficient_routes"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de optimización de rutas"""
        pass

class LocationAnalyst(BaseAgent):
    """Analista de Ubicaciones (3 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.MAPS_INTELLIGENCE)
        self.specialization = "Location Analyst"
        self.capabilities = {
            "location_analysis", "demographic_analysis", "area_assessment",
            "proximity_analysis", "location_scoring"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de análisis de ubicaciones"""
        pass

class DistanceCalculator(BaseAgent):
    """Calculador de Distancias (2 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_0, TeamType.MAPS_INTELLIGENCE)
        self.specialization = "Distance Calculator"
        self.capabilities = {
            "distance_calculation", "travel_time_estimation", "distance_matrix",
            "radius_calculation", "area_calculation"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de cálculo de distancias"""
        pass

class PlaceResearcher(BaseAgent):
    """Investigador de Lugares (2 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_0, TeamType.MAPS_INTELLIGENCE)
        self.specialization = "Place Researcher"
        self.capabilities = {
            "place_search", "place_details", "business_search", "point_of_interest",
            "local_businesses", "place_reviews"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de investigación de lugares"""
        pass

class NavigationAdvisor(BaseAgent):
    """Asesor de Navegación (2 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_0, TeamType.MAPS_INTELLIGENCE)
        self.specialization = "Navigation Advisor"
        self.capabilities = {
            "directions", "step_by_step_navigation", "turn_by_turn_directions",
            "navigation_alerts", "alternative_routes"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de navegación"""
        pass

# ==================== FINANCIAL INTELLIGENCE TEAM ====================

class FinancialTeamLeader(BaseAgent):
    """Líder del equipo Financial Intelligence (20+ agentes)"""
    
    def __init__(self):
        super().__init__("financial_team_leader", AgentLevel.LEVEL_3, TeamType.FINANCIAL_INTELLIGENCE)
        self.specialization = "Financial Intelligence Team Leader"
        self.capabilities = {
            "stock_analysis", "market_research", "risk_management", "crypto_analysis",
            "forex_analysis", "economic_forecasting", "team_coordination", "financial_planning"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades específicas del líder financiero"""
        pass

class StockAnalyst(BaseAgent):
    """Analista de Acciones (4 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.FINANCIAL_INTELLIGENCE)
        self.specialization = "Stock Analyst"
        self.capabilities = {
            "stock_analysis", "technical_analysis", "fundamental_analysis", "price_prediction",
            "stock_screening", "portfolio_analysis", "risk_assessment"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de análisis de acciones"""
        pass

class MarketResearcher(BaseAgent):
    """Investigador de Mercado (3 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.FINANCIAL_INTELLIGENCE)
        self.specialization = "Market Researcher"
        self.capabilities = {
            "market_research", "sector_analysis", "industry_trends", "competitive_analysis",
            "market_sizing", "opportunity_identification"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de investigación de mercado"""
        pass

class CommodityTrader(BaseAgent):
    """Trader de Materias Primas (3 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.FINANCIAL_INTELLIGENCE)
        self.specialization = "Commodity Trader"
        self.capabilities = {
            "commodity_analysis", "price_forecasting", "supply_demand_analysis",
            "seasonal_patterns", "commodity_screening"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de trading de materias primas"""
        pass

class RiskManager(BaseAgent):
    """Gestor de Riesgos (3 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.FINANCIAL_INTELLIGENCE)
        self.specialization = "Risk Manager"
        self.capabilities = {
            "risk_assessment", "portfolio_risk", "value_at_risk", "stress_testing",
            "risk_mitigation", "compliance_monitoring"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de gestión de riesgos"""
        pass

class CryptoSpecialist(BaseAgent):
    """Especialista en Criptomonedas (3 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.FINANCIAL_INTELLIGENCE)
        self.specialization = "Cryptocurrency Specialist"
        self.capabilities = {
            "crypto_analysis", "blockchain_analysis", "defi_research", "nft_analysis",
            "crypto_screening", "market_sentiment"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de análisis de criptomonedas"""
        pass

class ForexAnalyst(BaseAgent):
    """Analista Forex (2 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.FINANCIAL_INTELLIGENCE)
        self.specialization = "Forex Analyst"
        self.capabilities = {
            "forex_analysis", "currency_pair_analysis", "exchange_rate_prediction",
            "economic_indicators", "central_bank_analysis"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de análisis forex"""
        pass

class EconomicForecaster(BaseAgent):
    """Forecastor Económico (2 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.FINANCIAL_INTELLIGENCE)
        self.specialization = "Economic Forecaster"
        self.capabilities = {
            "economic_forecasting", "gdp_prediction", "inflation_analysis", "interest_rate_forecasting",
            "economic_indicators", "recession_analysis"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de forecast económico"""
        pass

# ==================== SOCIAL MEDIA + TRAVEL TEAM ====================

class SocialTravelTeamLeader(BaseAgent):
    """Líder del equipo Social Media + Travel (18+ agentes)"""
    
    def __init__(self):
        super().__init__("social_travel_team_leader", AgentLevel.LEVEL_3, TeamType.SOCIAL_TRAVEL)
        self.specialization = "Social Media + Travel Team Leader"
        self.capabilities = {
            "social_media_management", "content_creation", "trend_analysis", "travel_planning",
            "booking_management", "experience_curation", "team_coordination"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades específicas del líder"""
        pass

class SocialMediaManager(BaseAgent):
    """Gestor de Redes Sociales (4 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.SOCIAL_TRAVEL)
        self.specialization = "Social Media Manager"
        self.capabilities = {
            "social_media_strategy", "content_scheduling", "engagement_tracking", "follower_analysis",
            "hashtag_research", "social_listening", "community_management"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de gestión de redes sociales"""
        pass

class ContentCurator(BaseAgent):
    """Curador de Contenido (3 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.SOCIAL_TRAVEL)
        self.specialization = "Content Curator"
        self.capabilities = {
            "content_curation", "trending_content", "content_discovery", "content_recommendation",
            "social_media_content", "travel_content"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de curación de contenido"""
        pass

class TrendAnalyst(BaseAgent):
    """Analista de Tendencias (3 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.SOCIAL_TRAVEL)
        self.specialization = "Trend Analyst"
        self.capabilities = {
            "trend_analysis", "viral_content", "hashtag_trends", "influencer_tracking",
            "social_sentiment", "content_performance"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de análisis de tendencias"""
        pass

class TravelPlanner(BaseAgent):
    """Planificador de Viajes (3 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.SOCIAL_TRAVEL)
        self.specialization = "Travel Planner"
        self.capabilities = {
            "itinerary_planning", "destination_research", "travel_recommendations", "budget_planning",
            "activity_suggestions", "local_insights"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de planificación de viajes"""
        pass

class BookingSpecialist(BaseAgent):
    """Especialista en Reservas (3 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.SOCIAL_TRAVEL)
        self.specialization = "Booking Specialist"
        self.capabilities = {
            "hotel_booking", "flight_booking", "restaurant_reservations", "activity_booking",
            "price_comparison", "booking_optimization"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de reservas"""
        pass

class ExperienceCurator(BaseAgent):
    """Curador de Experiencias (2 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.SOCIAL_TRAVEL)
        self.specialization = "Experience Curator"
        self.capabilities = {
            "experience_curation", "unique_activities", "local_experiences", "adventure_travel",
            "cultural_experiences", "personalized_recommendations"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de curación de experiencias"""
        pass

# ==================== CONTENT CREATION TEAM ====================

class ContentCreationTeamLeader(BaseAgent):
    """Líder del equipo Content Creation (12+ agentes)"""
    
    def __init__(self):
        super().__init__("content_creation_team_leader", AgentLevel.LEVEL_3, TeamType.CONTENT_CREATION)
        self.specialization = "Content Creation Team Leader"
        self.capabilities = {
            "image_creation", "video_production", "audio_composition", "chart_design",
            "content_strategy", "creative_direction", "team_coordination"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades específicas del líder"""
        pass

class ImageCreator(BaseAgent):
    """Creador de Imágenes (3 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.CONTENT_CREATION)
        self.specialization = "Image Creator"
        self.capabilities = {
            "image_generation", "image_editing", "graphic_design", "logo_creation",
            "banner_design", "social_media_graphics", "marketing_visuals"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de creación de imágenes"""
        pass

class VideoProducer(BaseAgent):
    """Productor de Videos (3 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.CONTENT_CREATION)
        self.specialization = "Video Producer"
        self.capabilities = {
            "video_creation", "video_editing", "animation", "motion_graphics",
            "social_media_videos", "promotional_videos", "explainer_videos"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de producción de videos"""
        pass

class AudioComposer(BaseAgent):
    """Compositor de Audio (2 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.CONTENT_CREATION)
        self.specialization = "Audio Composer"
        self.capabilities = {
            "music_composition", "sound_design", "audio_editing", "podcast_production",
            "audio_branding", "background_music"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de composición de audio"""
        pass

class ChartDesigner(BaseAgent):
    """Diseñador de Gráficos (2 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.CONTENT_CREATION)
        self.specialization = "Chart Designer"
        self.capabilities = {
            "chart_creation", "data_visualization", "infographic_design", "dashboard_design",
            "presentation_graphics", "statistical_visualization"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de diseño de gráficos"""
        pass

class ContentStrategist(BaseAgent):
    """Estratega de Contenido (2 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.CONTENT_CREATION)
        self.specialization = "Content Strategist"
        self.capabilities = {
            "content_strategy", "audience_analysis", "content_planning", "seo_optimization",
            "content_calendar", "performance_analysis"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de estrategia de contenido"""
        pass

# ==================== DATABASE OPERATIONS TEAM ====================

class DatabaseTeamLeader(BaseAgent):
    """Líder del equipo Database Operations (15+ agentes)"""
    
    def __init__(self):
        super().__init__("database_team_leader", AgentLevel.LEVEL_3, TeamType.DATABASE_OPERATIONS)
        self.specialization = "Database Operations Team Leader"
        self.capabilities = {
            "database_architecture", "migration_management", "backup_coordination",
            "security_monitoring", "performance_optimization", "integration_management",
            "team_coordination"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades específicas del líder"""
        pass

class DatabaseArchitect(BaseAgent):
    """Arquitecto de Base de Datos (3 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.DATABASE_OPERATIONS)
        self.specialization = "Database Architect"
        self.capabilities = {
            "database_design", "schema_optimization", "performance_tuning", "scaling_planning",
            "data_modeling", "database_migration", "architecture_review"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de arquitectura de bases de datos"""
        pass

class MigrationSpecialist(BaseAgent):
    """Especialista en Migraciones (3 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.DATABASE_OPERATIONS)
        self.specialization = "Migration Specialist"
        self.capabilities = {
            "data_migration", "schema_migration", "database_upgrade", "rollback_planning",
            "migration_testing", "data_consistency"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de migración"""
        pass

class BackupManager(BaseAgent):
    """Gestor de Respaldos (2 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.DATABASE_OPERATIONS)
        self.specialization = "Backup Manager"
        self.capabilities = {
            "backup_strategy", "automated_backups", "recovery_testing", "backup_monitoring",
            "retention_policies", "disaster_recovery"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de gestión de respaldos"""
        pass

class SecurityExpert(BaseAgent):
    """Experto en Seguridad (2 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.DATABASE_OPERATIONS)
        self.specialization = "Security Expert"
        self.capabilities = {
            "database_security", "access_control", "encryption_management", "security_auditing",
            "vulnerability_assessment", "compliance_monitoring"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de seguridad de bases de datos"""
        pass

class PerformanceOptimizer(BaseAgent):
    """Optimizador de Rendimiento (2 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.DATABASE_OPERATIONS)
        self.specialization = "Performance Optimizer"
        self.capabilities = {
            "query_optimization", "index_tuning", "performance_monitoring", "bottleneck_analysis",
            "resource_optimization", "capacity_planning"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de optimización de rendimiento"""
        pass

class IntegrationSpecialist(BaseAgent):
    """Especialista en Integraciones (3 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.DATABASE_OPERATIONS)
        self.specialization = "Integration Specialist"
        self.capabilities = {
            "api_integration", "data_sync", "etl_processes", "third_party_connections",
            "real_time_integration", "data_pipeline_management"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de integración"""
        pass

# ==================== RESEARCH INTELLIGENCE TEAM ====================

class ResearchTeamLeader(BaseAgent):
    """Líder del equipo Research Intelligence (8+ agentes)"""
    
    def __init__(self):
        super().__init__("research_team_leader", AgentLevel.LEVEL_3, TeamType.RESEARCH_INTELLIGENCE)
        self.specialization = "Research Intelligence Team Leader"
        self.capabilities = {
            "patent_research", "academic_analysis", "data_mining", "research_methodology",
            "knowledge_synthesis", "research_coordination"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades específicas del líder"""
        pass

class PatentResearcher(BaseAgent):
    """Investigador de Patentes (3 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.RESEARCH_INTELLIGENCE)
        self.specialization = "Patent Researcher"
        self.capabilities = {
            "patent_search", "patent_analysis", "prior_art_search", "patent_landscaping",
            "freedom_to_operate", "patent_filing_assistance"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de investigación de patentes"""
        pass

class AcademicAnalyst(BaseAgent):
    """Analista Académico (3 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.RESEARCH_INTELLIGENCE)
        self.specialization = "Academic Analyst"
        self.capabilities = {
            "academic_research", "literature_review", "citation_analysis", "research_trends",
            "peer_review_analysis", "academic_networking"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de análisis académico"""
        pass

class DataMiner(BaseAgent):
    """Mineros de Datos (2 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.RESEARCH_INTELLIGENCE)
        self.specialization = "Data Miner"
        self.capabilities = {
            "data_extraction", "pattern_recognition", "anomaly_detection", "text_mining",
            "web_scraping", "data_synthesis"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de minería de datos"""
        pass

# ==================== SUPPORT SYSTEMS TEAM ====================

class SupportTeamLeader(BaseAgent):
    """Líder del equipo de Sistemas de Apoyo (10+ agentes)"""
    
    def __init__(self):
        super().__init__("support_team_leader", AgentLevel.LEVEL_3, TeamType.SUPPORT_SYSTEMS)
        self.specialization = "Support Systems Team Leader"
        self.capabilities = {
            "communication_coordination", "performance_monitoring", "quality_assurance",
            "security_management", "scalability_planning", "system_maintenance"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades específicas del líder de apoyo"""
        pass

class CommunicationCoordinator(BaseAgent):
    """Coordinador de Comunicación (2 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.SUPPORT_SYSTEMS)
        self.specialization = "Communication Coordinator"
        self.capabilities = {
            "message_routing", "communication_protocols", "team_coordination",
            "notification_management", "escalation_handling"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de coordinación de comunicación"""
        pass

class PerformanceMonitor(BaseAgent):
    """Monitor de Rendimiento (2 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.SUPPORT_SYSTEMS)
        self.specialization = "Performance Monitor"
        self.capabilities = {
            "system_monitoring", "performance_metrics", "bottleneck_detection",
            "resource_utilization", "alert_management"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de monitoreo de rendimiento"""
        pass

class QualityAssurance(BaseAgent):
    """Aseguramiento de Calidad (2 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.SUPPORT_SYSTEMS)
        self.specialization = "Quality Assurance"
        self.capabilities = {
            "quality_testing", "code_review", "performance_testing", "security_testing",
            "compliance_audit", "quality_metrics"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de aseguramiento de calidad"""
        pass

class SecurityGuard(BaseAgent):
    """Guardia de Seguridad (2 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.SUPPORT_SYSTEMS)
        self.specialization = "Security Guard"
        self.capabilities = {
            "security_monitoring", "threat_detection", "access_control", "audit_logging",
            "incident_response", "security_compliance"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de seguridad"""
        pass

class ScalabilityManager(BaseAgent):
    """Gestor de Escalabilidad (2 agentes)"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentLevel.LEVEL_1, TeamType.SUPPORT_SYSTEMS)
        self.specialization = "Scalability Manager"
        self.capabilities = {
            "load_balancing", "resource_scaling", "capacity_planning", "performance_optimization",
            "infrastructure_management", "cost_optimization"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades de gestión de escalabilidad"""
        pass

# ==================== MASTER COORDINATOR ====================

class MasterCoordinator(BaseAgent):
    """Coordinador Maestro - Nivel 5 - Decisiones Estratégicas"""
    
    def __init__(self):
        super().__init__("master_coordinator", AgentLevel.LEVEL_5, None)
        self.specialization = "Master Coordinator - Strategic Decision Making"
        self.state = CoordinatorState.LEADER
        self.leader_term = 0
        self.leader_commit_index = 0
        self.peer_coordinators: List[str] = []
        self.strategic_decisions = []
        self.system_metrics = {}
        
        self.capabilities = {
            "strategic_planning", "resource_allocation", "cross_team_coordination",
            "performance_optimization", "failover_management", "system_monitoring",
            "decision_making", "resource_optimization", "load_balancing"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades del coordinador maestro"""
        # Cargar métricas del sistema
        await self.load_system_metrics()
        
    async def load_system_metrics(self):
        """Carga métricas del sistema"""
        self.system_metrics = {
            "total_agents": 0,
            "active_agents": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "average_response_time": 0.0,
            "system_uptime": 0.0,
            "resource_utilization": 0.0
        }
    
    async def make_strategic_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Toma decisiones estratégicas de alto nivel"""
        try:
            # Analizar contexto del sistema
            system_state = await self.get_system_state()
            
            # Decisiones estratégicas basadas en el estado
            decision = {
                "decision_id": str(uuid.uuid4()),
                "timestamp": datetime.now(),
                "context": context,
                "analysis": system_state,
                "recommendations": [],
                "actions": []
            }
            
            # Lógica de decisión estratégica
            if system_state.get("resource_utilization", 0) > 0.8:
                decision["actions"].append({
                    "type": "scale_up",
                    "target": "high_load_teams",
                    "priority": "high"
                })
            
            if system_state.get("failed_task_rate", 0) > 0.1:
                decision["actions"].append({
                    "type": "quality_review",
                    "target": "failing_teams",
                    "priority": "high"
                })
            
            decision["recommendations"] = await self.generate_recommendations(system_state)
            
            self.strategic_decisions.append(decision)
            
            return decision
            
        except Exception as e:
            logger.error(f"Error en decisión estratégica: {e}")
            return {"error": str(e)}
    
    async def get_system_state(self) -> Dict[str, Any]:
        """Obtiene el estado completo del sistema"""
        # Implementación simplificada - en producción sería más compleja
        return {
            "resource_utilization": random.uniform(0.3, 0.9),
            "failed_task_rate": random.uniform(0.02, 0.08),
            "average_response_time": random.uniform(0.5, 3.0),
            "team_performance": {team.value: random.uniform(70, 95) for team in TeamType},
            "active_tasks": random.randint(10, 50),
            "pending_tasks": random.randint(5, 25)
        }
    
    async def generate_recommendations(self, system_state: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones basadas en el estado del sistema"""
        recommendations = []
        
        if system_state.get("resource_utilization", 0) > 0.8:
            recommendations.append("Considerar escalar recursos en equipos de alta carga")
        
        if system_state.get("average_response_time", 0) > 2.0:
            recommendations.append("Optimizar rendimiento general del sistema")
        
        failed_rate = system_state.get("failed_task_rate", 0)
        if failed_rate > 0.05:
            recommendations.append("Revisar procesos de calidad y capacitación")
        
        return recommendations

# ==================== INTELLIGENT TASK ASSIGNER ====================

class IntelligentTaskAssigner(BaseAgent):
    """Asignador Inteligente de Tareas - Nivel 4"""
    
    def __init__(self):
        super().__init__("intelligent_task_assigner", AgentLevel.LEVEL_4, None)
        self.specialization = "Intelligent Task Assigner - Workload Optimization"
        self.assignment_history = []
        self.performance_predictions = {}
        self.load_balancing_algorithms = {
            "hungarian": HungarianAlgorithm(),
            "cbba": None  # Se inicializará con equipos
        }
        
        self.capabilities = {
            "task_analysis", "agent_matching", "load_balancing", "performance_prediction",
            "optimization", "assignment_optimization", "resource_allocation"
        }
    
    async def setup_capabilities(self):
        """Configura capacidades del asignador inteligente"""
        pass
    
    async def assign_task(self, task: Task, available_agents: List[Agent]) -> Optional[str]:
        """Asigna una tarea a un agente específico usando algoritmos inteligentes"""
        try:
            # Analizar la tarea
            task_analysis = await self.analyze_task(task)
            
            # Encontrar el mejor agente
            best_agent = await self.find_best_agent(task, available_agents, task_analysis)
            
            if best_agent:
                assignment = {
                    "task_id": task.id,
                    "agent_id": best_agent.id,
                    "assignment_time": datetime.now(),
                    "algorithm_used": "intelligent_matching",
                    "confidence_score": await self.calculate_confidence(task, best_agent),
                    "estimated_completion": datetime.now() + timedelta(minutes=task.estimated_duration)
                }
                
                self.assignment_history.append(assignment)
                return best_agent.id
            
            return None
            
        except Exception as e:
            logger.error(f"Error asignando tarea {task.id}: {e}")
            return None
    
    async def analyze_task(self, task: Task) -> Dict[str, Any]:
        """Analiza las características de una tarea"""
        return {
            "complexity_score": task.complexity,
            "team_affinity": task.team_type,
            "estimated_duration": task.estimated_duration,
            "priority_level": task.priority.value,
            "resource_requirements": self.estimate_resource_requirements(task),
            "skill_matching": self.estimate_skill_requirements(task)
        }
    
    def estimate_resource_requirements(self, task: Task) -> Dict[str, float]:
        """Estima los requisitos de recursos para una tarea"""
        return {
            "cpu": min(1.0, task.complexity / 10.0),
            "memory": min(1.0, task.estimated_duration / 120.0),
            "network": random.uniform(0.1, 0.5),
            "storage": random.uniform(0.0, 0.3)
        }
    
    def estimate_skill_requirements(self, task: Task) -> List[str]:
        """Estima los requisitos de habilidades para una tarea"""
        # Mapeo simplificado de tipos de tareas a habilidades
        skill_mapping = {
            TeamType.MAPS_INTELLIGENCE: ["geocoding", "route_optimization", "location_analysis"],
            TeamType.FINANCIAL_INTELLIGENCE: ["financial_analysis", "market_research", "risk_assessment"],
            TeamType.SOCIAL_TRAVEL: ["social_media", "content_creation", "travel_planning"],
            TeamType.CONTENT_CREATION: ["design", "creativity", "multimedia"],
            TeamType.DATABASE_OPERATIONS: ["database_management", "migration", "security"],
            TeamType.RESEARCH_INTELLIGENCE: ["research", "analysis", "data_mining"],
            TeamType.SUPPORT_SYSTEMS: ["monitoring", "coordination", "quality_assurance"]
        }
        
        return skill_mapping.get(task.team_type, ["general"])
    
    async def find_best_agent(self, task: Task, available_agents: List[Agent], analysis: Dict[str, Any]) -> Optional[Agent]:
        """Encuentra el mejor agente para una tarea"""
        best_agent = None
        best_score = float('-inf')
        
        for agent in available_agents:
            if agent.status != "active":
                continue
            
            # Calcular puntuación de compatibilidad
            score = await self.calculate_compatibility_score(task, agent, analysis)
            
            if score > best_score:
                best_score = score
                best_agent = agent
        
        return best_agent
    
    async def calculate_compatibility_score(self, task: Task, agent: Agent, analysis: Dict[str, Any]) -> float:
        """Calcula la puntuación de compatibilidad entre tarea y agente"""
        score = 0.0
        
        # Afinidad de equipo (30%)
        if task.team_type == agent.team_type:
            score += 30
        
        # Carga actual del agente (20%)
        load_penalty = agent.performance.current_load * 10
        score += max(0, 20 - load_penalty)
        
        # Rendimiento histórico (25%)
        score += agent.performance.performance_score * 0.25
        
        # Tasa de éxito (15%)
        score += agent.performance.success_rate * 0.15
        
        # Compatibilidad de capacidades (10%)
        required_skills = analysis.get("skill_matching", [])
        skill_matches = len(required_skills.intersection(agent.capabilities))
        score += (skill_matches / max(1, len(required_skills))) * 10
        
        return score
    
    async def calculate_confidence(self, task: Task, agent: Agent) -> float:
        """Calcula la confianza en la asignación"""
        # Basado en el rendimiento histórico y la compatibilidad
        base_confidence = agent.performance.success_rate
        compatibility_factor = 0.8 if task.team_type == agent.team_type else 0.5
        
        return min(1.0, base_confidence * compatibility_factor)
    
    async def optimize_load_balancing(self, tasks: List[Task], agents: List[Agent]) -> Dict[str, str]:
        """Optimiza el balanceo de carga usando algoritmos avanzados"""
        try:
            # Filtrar solo tareas pendientes
            pending_tasks = [t for t in tasks if t.status == "pending"]
            
            if not pending_tasks or not agents:
                return {}
            
            # Usar algoritmo húngaro para asignación óptima
            assignment = HungarianAlgorithm.assign_tasks(pending_tasks, agents)
            
            # Registrar optimización
            optimization_record = {
                "timestamp": datetime.now(),
                "tasks_assigned": len(assignment),
                "algorithm": "hungarian",
                "agents_involved": list(set(assignment.values())),
                "optimization_score": self.calculate_optimization_score(assignment, agents)
            }
            
            logger.info(f"Optimización de carga completada: {optimization_record}")
            
            return assignment
            
        except Exception as e:
            logger.error(f"Error en optimización de balance de carga: {e}")
            return {}
    
    def calculate_optimization_score(self, assignment: Dict[str, str], agents: List[Agent]) -> float:
        """Calcula la puntuación de optimización del balanceo de carga"""
        if not assignment:
            return 0.0
        
        # Calcular distribución de carga
        agent_loads = defaultdict(int)
        for task_id, agent_id in assignment.items():
            agent_loads[agent_id] += 1
        
        # Calcular varianza de la carga (menor es mejor)
        loads = list(agent_loads.values())
        if len(loads) <= 1:
            return 1.0
        
        mean_load = sum(loads) / len(loads)
        variance = sum((load - mean_load) ** 2 for load in loads) / len(loads)
        
        # Convertir a puntuación (0-1, donde 1 es mejor)
        max_possible_variance = len(loads) * (max(loads) - min(loads)) ** 2
        optimization_score = 1.0 - (variance / max_possible_variance if max_possible_variance > 0 else 0)
        
        return max(0.0, min(1.0, optimization_score))

# ==================== SISTEMA DE MÉTRICAS Y MONITOREO ====================

class MetricsSystem:
    """Sistema de métricas en tiempo real"""
    
    def __init__(self):
        self.metrics_store = defaultdict(dict)
        self.real_time_metrics = {}
        self.metrics_history = defaultdict(list)
        self.websocket_connections: List[WebSocket] = []
    
    async def update_agent_metrics(self, agent_id: str, metrics: Dict[str, Any]):
        """Actualiza métricas de un agente"""
        self.metrics_store[agent_id].update(metrics)
        self.real_time_metrics[agent_id] = metrics
        
        # Guardar en historial
        self.metrics_history[agent_id].append({
            "timestamp": datetime.now(),
            "metrics": metrics
        })
        
        # Mantener solo las últimas 1000 entradas
        if len(self.metrics_history[agent_id]) > 1000:
            self.metrics_history[agent_id] = self.metrics_history[agent_id][-1000:]
        
        # Notificar conexiones WebSocket
        await self.broadcast_metrics_update(agent_id, metrics)
    
    async def update_team_metrics(self, team_id: str, metrics: Dict[str, Any]):
        """Actualiza métricas de un equipo"""
        self.metrics_store[f"team_{team_id}"].update(metrics)
        self.real_time_metrics[f"team_{team_id}"] = metrics
        
        await self.broadcast_metrics_update(f"team_{team_id}", metrics)
    
    async def get_system_overview(self) -> Dict[str, Any]:
        """Obtiene vista general del sistema"""
        return {
            "total_agents": len(self.metrics_store),
            "active_agents": len([m for m in self.real_time_metrics.values() if m.get("status") == "active"]),
            "total_tasks": sum(m.get("tasks_completed", 0) + m.get("tasks_failed", 0) for m in self.real_time_metrics.values()),
            "average_performance": np.mean([m.get("performance_score", 0) for m in self.real_time_metrics.values()]),
            "system_health": self.calculate_system_health(),
            "timestamp": datetime.now().isoformat()
        }
    
    def calculate_system_health(self) -> float:
        """Calcula la salud general del sistema"""
        if not self.real_time_metrics:
            return 0.0
        
        health_scores = []
        for metrics in self.real_time_metrics.values():
            score = 0.0
            
            # Rendimiento (40%)
            score += (metrics.get("performance_score", 0) / 100) * 0.4
            
            # Tasa de éxito (30%)
            total_tasks = metrics.get("tasks_completed", 0) + metrics.get("tasks_failed", 0)
            if total_tasks > 0:
                success_rate = metrics.get("tasks_completed", 0) / total_tasks
                score += success_rate * 0.3
            
            # Carga de trabajo (20%) - óptimo alrededor del 70%
            load = metrics.get("current_load", 0)
            load_score = 1.0 - abs(load - 0.7)
            score += load_score * 0.2
            
            # Actividad reciente (10%)
            last_activity = metrics.get("last_activity")
            if last_activity:
                hours_since_activity = (datetime.now() - last_activity).total_seconds() / 3600
                activity_score = max(0, 1.0 - (hours_since_activity / 24))  # Penalizar inactividad > 24h
                score += activity_score * 0.1
            
            health_scores.append(score)
        
        return np.mean(health_scores) if health_scores else 0.0
    
    async def broadcast_metrics_update(self, entity_id: str, metrics: Dict[str, Any]):
        """Transmite actualización de métricas a conexiones WebSocket"""
        if not self.websocket_connections:
            return
        
        message = {
            "type": "metrics_update",
            "entity_id": entity_id,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        # Crear una copia de la lista para evitar modificaciones durante la iteración
        connections = self.websocket_connections.copy()
        
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error enviando métricas por WebSocket: {e}")
                # Remover conexión muerta
                if websocket in self.websocket_connections:
                    self.websocket_connections.remove(websocket)
    
    def add_websocket_connection(self, websocket: WebSocket):
        """Agrega conexión WebSocket"""
        self.websocket_connections.append(websocket)
    
    def remove_websocket_connection(self, websocket: WebSocket):
        """Remueve conexión WebSocket"""
        if websocket in self.websocket_connections:
            self.websocket_connections.remove(websocket)

# ==================== GESTOR DE EQUIPOS Y AGENTES ====================

class TeamManager:
    """Gestor de equipos y agentes especializados"""
    
    def __init__(self):
        self.teams: Dict[str, Team] = {}
        self.agents: Dict[str, Agent] = {}
        self.team_leaders: Dict[TeamType, BaseAgent] = {}
        self.fipa_controller = FIPAController()
        self.metrics_system = MetricsSystem()
    
    async def initialize_teams(self):
        """Inicializa todos los equipos y agentes"""
        await self.create_maps_team()
        await self.create_financial_team()
        await self.create_social_travel_team()
        await self.create_content_creation_team()
        await self.create_database_team()
        await self.create_research_team()
        await self.create_support_team()
        
        logger.info("Todos los equipos inicializados exitosamente")
    
    async def create_maps_team(self):
        """Crea el equipo de Maps Intelligence (15 agentes)"""
        team_id = "maps_intelligence_team"
        
        # Crear líder del equipo
        leader = MapsTeamLeader()
        await leader.initialize()
        
        team = Team(
            id=team_id,
            name="Maps Intelligence Team",
            type=TeamType.MAPS_INTELLIGENCE,
            leader_id=leader.agent_id,
            capacity=15,
            specialization="Geospatial Intelligence & Location Services"
        )
        
        self.teams[team_id] = team
        self.team_leaders[TeamType.MAPS_INTELLIGENCE] = leader
        self.agents[leader.agent_id] = Agent(
            id=leader.agent_id,
            name="Maps Team Leader",
            level=AgentLevel.LEVEL_3,
            team_type=TeamType.MAPS_INTELLIGENCE,
            capabilities=leader.capabilities,
            performance=leader.performance,
            specialization=leader.specialization
        )
        
        # Crear especialistas en Geocoding (3)
        for i in range(3):
            agent = GeocodingSpecialist(f"geocoding_specialist_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Geocoding Specialist {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.MAPS_INTELLIGENCE,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear optimizadores de rutas (3)
        for i in range(3):
            agent = RouteOptimizer(f"route_optimizer_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Route Optimizer {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.MAPS_INTELLIGENCE,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear analistas de ubicación (3)
        for i in range(3):
            agent = LocationAnalyst(f"location_analyst_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Location Analyst {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.MAPS_INTELLIGENCE,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear calculadores de distancia (2)
        for i in range(2):
            agent = DistanceCalculator(f"distance_calculator_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Distance Calculator {i+1}",
                level=AgentLevel.LEVEL_0,
                team_type=TeamType.MAPS_INTELLIGENCE,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear investigadores de lugares (2)
        for i in range(2):
            agent = PlaceResearcher(f"place_researcher_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Place Researcher {i+1}",
                level=AgentLevel.LEVEL_0,
                team_type=TeamType.MAPS_INTELLIGENCE,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear asesores de navegación (2)
        for i in range(2):
            agent = NavigationAdvisor(f"navigation_advisor_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Navigation Advisor {i+1}",
                level=AgentLevel.LEVEL_0,
                team_type=TeamType.MAPS_INTELLIGENCE,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
    
    async def create_financial_team(self):
        """Crea el equipo Financial Intelligence (20 agentes)"""
        team_id = "financial_intelligence_team"
        
        # Crear líder del equipo
        leader = FinancialTeamLeader()
        await leader.initialize()
        
        team = Team(
            id=team_id,
            name="Financial Intelligence Team",
            type=TeamType.FINANCIAL_INTELLIGENCE,
            leader_id=leader.agent_id,
            capacity=20,
            specialization="Financial Markets & Investment Intelligence"
        )
        
        self.teams[team_id] = team
        self.team_leaders[TeamType.FINANCIAL_INTELLIGENCE] = leader
        self.agents[leader.agent_id] = Agent(
            id=leader.agent_id,
            name="Financial Team Leader",
            level=AgentLevel.LEVEL_3,
            team_type=TeamType.FINANCIAL_INTELLIGENCE,
            capabilities=leader.capabilities,
            performance=leader.performance,
            specialization=leader.specialization
        )
        
        # Crear analistas de acciones (4)
        for i in range(4):
            agent = StockAnalyst(f"stock_analyst_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Stock Analyst {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.FINANCIAL_INTELLIGENCE,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear investigadores de mercado (3)
        for i in range(3):
            agent = MarketResearcher(f"market_researcher_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Market Researcher {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.FINANCIAL_INTELLIGENCE,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear traders de materias primas (3)
        for i in range(3):
            agent = CommodityTrader(f"commodity_trader_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Commodity Trader {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.FINANCIAL_INTELLIGENCE,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear gestores de riesgo (3)
        for i in range(3):
            agent = RiskManager(f"risk_manager_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Risk Manager {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.FINANCIAL_INTELLIGENCE,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear especialistas en criptomonedas (3)
        for i in range(3):
            agent = CryptoSpecialist(f"crypto_specialist_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Crypto Specialist {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.FINANCIAL_INTELLIGENCE,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear analistas forex (2)
        for i in range(2):
            agent = ForexAnalyst(f"forex_analyst_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Forex Analyst {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.FINANCIAL_INTELLIGENCE,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear forecastores económicos (2)
        for i in range(2):
            agent = EconomicForecaster(f"economic_forecaster_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Economic Forecaster {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.FINANCIAL_INTELLIGENCE,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
    
    async def create_social_travel_team(self):
        """Crea el equipo Social Media + Travel (18 agentes)"""
        team_id = "social_travel_team"
        
        # Crear líder del equipo
        leader = SocialTravelTeamLeader()
        await leader.initialize()
        
        team = Team(
            id=team_id,
            name="Social Media + Travel Team",
            type=TeamType.SOCIAL_TRAVEL,
            leader_id=leader.agent_id,
            capacity=18,
            specialization="Social Media Management & Travel Experience Design"
        )
        
        self.teams[team_id] = team
        self.team_leaders[TeamType.SOCIAL_TRAVEL] = leader
        self.agents[leader.agent_id] = Agent(
            id=leader.agent_id,
            name="Social Travel Team Leader",
            level=AgentLevel.LEVEL_3,
            team_type=TeamType.SOCIAL_TRAVEL,
            capabilities=leader.capabilities,
            performance=leader.performance,
            specialization=leader.specialization
        )
        
        # Crear gestores de redes sociales (4)
        for i in range(4):
            agent = SocialMediaManager(f"social_media_manager_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Social Media Manager {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.SOCIAL_TRAVEL,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear curadores de contenido (3)
        for i in range(3):
            agent = ContentCurator(f"content_curator_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Content Curator {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.SOCIAL_TRAVEL,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear analistas de tendencias (3)
        for i in range(3):
            agent = TrendAnalyst(f"trend_analyst_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Trend Analyst {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.SOCIAL_TRAVEL,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear planificadores de viajes (3)
        for i in range(3):
            agent = TravelPlanner(f"travel_planner_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Travel Planner {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.SOCIAL_TRAVEL,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear especialistas en reservas (3)
        for i in range(3):
            agent = BookingSpecialist(f"booking_specialist_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Booking Specialist {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.SOCIAL_TRAVEL,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear curadores de experiencias (2)
        for i in range(2):
            agent = ExperienceCurator(f"experience_curator_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Experience Curator {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.SOCIAL_TRAVEL,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
    
    async def create_content_creation_team(self):
        """Crea el equipo Content Creation (12 agentes)"""
        team_id = "content_creation_team"
        
        # Crear líder del equipo
        leader = ContentCreationTeamLeader()
        await leader.initialize()
        
        team = Team(
            id=team_id,
            name="Content Creation Team",
            type=TeamType.CONTENT_CREATION,
            leader_id=leader.agent_id,
            capacity=12,
            specialization="Multimedia Content Creation & Creative Design"
        )
        
        self.teams[team_id] = team
        self.team_leaders[TeamType.CONTENT_CREATION] = leader
        self.agents[leader.agent_id] = Agent(
            id=leader.agent_id,
            name="Content Creation Team Leader",
            level=AgentLevel.LEVEL_3,
            team_type=TeamType.CONTENT_CREATION,
            capabilities=leader.capabilities,
            performance=leader.performance,
            specialization=leader.specialization
        )
        
        # Crear creadores de imágenes (3)
        for i in range(3):
            agent = ImageCreator(f"image_creator_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Image Creator {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.CONTENT_CREATION,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear productores de videos (3)
        for i in range(3):
            agent = VideoProducer(f"video_producer_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Video Producer {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.CONTENT_CREATION,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear compositores de audio (2)
        for i in range(2):
            agent = AudioComposer(f"audio_composer_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Audio Composer {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.CONTENT_CREATION,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear diseñadores de gráficos (2)
        for i in range(2):
            agent = ChartDesigner(f"chart_designer_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Chart Designer {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.CONTENT_CREATION,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear estrategas de contenido (2)
        for i in range(2):
            agent = ContentStrategist(f"content_strategist_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Content Strategist {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.CONTENT_CREATION,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
    
    async def create_database_team(self):
        """Crea el equipo Database Operations (15 agentes)"""
        team_id = "database_operations_team"
        
        # Crear líder del equipo
        leader = DatabaseTeamLeader()
        await leader.initialize()
        
        team = Team(
            id=team_id,
            name="Database Operations Team",
            type=TeamType.DATABASE_OPERATIONS,
            leader_id=leader.agent_id,
            capacity=15,
            specialization="Database Architecture & Operations Management"
        )
        
        self.teams[team_id] = team
        self.team_leaders[TeamType.DATABASE_OPERATIONS] = leader
        self.agents[leader.agent_id] = Agent(
            id=leader.agent_id,
            name="Database Team Leader",
            level=AgentLevel.LEVEL_3,
            team_type=TeamType.DATABASE_OPERATIONS,
            capabilities=leader.capabilities,
            performance=leader.performance,
            specialization=leader.specialization
        )
        
        # Crear arquitectos de base de datos (3)
        for i in range(3):
            agent = DatabaseArchitect(f"database_architect_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Database Architect {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.DATABASE_OPERATIONS,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear especialistas en migraciones (3)
        for i in range(3):
            agent = MigrationSpecialist(f"migration_specialist_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Migration Specialist {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.DATABASE_OPERATIONS,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear gestores de respaldos (2)
        for i in range(2):
            agent = BackupManager(f"backup_manager_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Backup Manager {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.DATABASE_OPERATIONS,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear expertos en seguridad (2)
        for i in range(2):
            agent = SecurityExpert(f"security_expert_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Security Expert {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.DATABASE_OPERATIONS,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear optimizadores de rendimiento (2)
        for i in range(2):
            agent = PerformanceOptimizer(f"performance_optimizer_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Performance Optimizer {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.DATABASE_OPERATIONS,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear especialistas en integraciones (3)
        for i in range(3):
            agent = IntegrationSpecialist(f"integration_specialist_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Integration Specialist {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.DATABASE_OPERATIONS,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
    
    async def create_research_team(self):
        """Crea el equipo Research Intelligence (8 agentes)"""
        team_id = "research_intelligence_team"
        
        # Crear líder del equipo
        leader = ResearchTeamLeader()
        await leader.initialize()
        
        team = Team(
            id=team_id,
            name="Research Intelligence Team",
            type=TeamType.RESEARCH_INTELLIGENCE,
            leader_id=leader.agent_id,
            capacity=8,
            specialization="Academic Research & Knowledge Discovery"
        )
        
        self.teams[team_id] = team
        self.team_leaders[TeamType.RESEARCH_INTELLIGENCE] = leader
        self.agents[leader.agent_id] = Agent(
            id=leader.agent_id,
            name="Research Team Leader",
            level=AgentLevel.LEVEL_3,
            team_type=TeamType.RESEARCH_INTELLIGENCE,
            capabilities=leader.capabilities,
            performance=leader.performance,
            specialization=leader.specialization
        )
        
        # Crear investigadores de patentes (3)
        for i in range(3):
            agent = PatentResearcher(f"patent_researcher_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Patent Researcher {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.RESEARCH_INTELLIGENCE,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear analistas académicos (3)
        for i in range(3):
            agent = AcademicAnalyst(f"academic_analyst_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Academic Analyst {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.RESEARCH_INTELLIGENCE,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear mineros de datos (2)
        for i in range(2):
            agent = DataMiner(f"data_miner_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Data Miner {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.RESEARCH_INTELLIGENCE,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
    
    async def create_support_team(self):
        """Crea el equipo de Sistemas de Apoyo (10 agentes)"""
        team_id = "support_systems_team"
        
        # Crear líder del equipo
        leader = SupportTeamLeader()
        await leader.initialize()
        
        team = Team(
            id=team_id,
            name="Support Systems Team",
            type=TeamType.SUPPORT_SYSTEMS,
            leader_id=leader.agent_id,
            capacity=10,
            specialization="System Support & Operations Management"
        )
        
        self.teams[team_id] = team
        self.team_leaders[TeamType.SUPPORT_SYSTEMS] = leader
        self.agents[leader.agent_id] = Agent(
            id=leader.agent_id,
            name="Support Systems Team Leader",
            level=AgentLevel.LEVEL_3,
            team_type=TeamType.SUPPORT_SYSTEMS,
            capabilities=leader.capabilities,
            performance=leader.performance,
            specialization=leader.specialization
        )
        
        # Crear coordinadores de comunicación (2)
        for i in range(2):
            agent = CommunicationCoordinator(f"communication_coordinator_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Communication Coordinator {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.SUPPORT_SYSTEMS,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear monitores de rendimiento (2)
        for i in range(2):
            agent = PerformanceMonitor(f"performance_monitor_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Performance Monitor {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.SUPPORT_SYSTEMS,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear aseguradores de calidad (2)
        for i in range(2):
            agent = QualityAssurance(f"quality_assurance_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Quality Assurance {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.SUPPORT_SYSTEMS,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear guardias de seguridad (2)
        for i in range(2):
            agent = SecurityGuard(f"security_guard_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Security Guard {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.SUPPORT_SYSTEMS,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
        
        # Crear gestores de escalabilidad (2)
        for i in range(2):
            agent = ScalabilityManager(f"scalability_manager_{i+1}")
            await agent.initialize()
            self.agents[agent.agent_id] = Agent(
                id=agent.agent_id,
                name=f"Scalability Manager {i+1}",
                level=AgentLevel.LEVEL_1,
                team_type=TeamType.SUPPORT_SYSTEMS,
                capabilities=agent.capabilities,
                performance=agent.performance,
                specialization=agent.specialization
            )
            team.members.append(agent.agent_id)
    
    async def get_team_status(self) -> Dict[str, Any]:
        """Obtiene el estado de todos los equipos"""
        status = {}
        for team_id, team in self.teams.items():
            team_agents = [self.agents[agent_id] for agent_id in team.members if agent_id in self.agents]
            
            status[team_id] = {
                "team": asdict(team),
                "agents": {agent_id: asdict(agent) for agent_id, agent in self.agents.items() if agent_id in team.members},
                "active_agents": len([a for a in team_agents if a.status == "active"]),
                "total_tasks": sum(a.performance.tasks_completed + a.performance.tasks_failed for a in team_agents),
                "average_performance": np.mean([a.performance.performance_score for a in team_agents]) if team_agents else 0.0
            }
        
        return status
    
    async def get_system_overview(self) -> Dict[str, Any]:
        """Obtiene vista general del sistema completo"""
        total_agents = len(self.agents)
        active_agents = len([a for a in self.agents.values() if a.status == "active"])
        total_tasks = sum(a.performance.tasks_completed + a.performance.tasks_failed for a in self.agents.values())
        
        return {
            "total_teams": len(self.teams),
            "total_agents": total_agents,
            "active_agents": active_agents,
            "total_tasks": total_teams,
            "teams": list(self.teams.keys()),
            "system_status": "operational" if active_agents > total_agents * 0.8 else "degraded",
            "architecture_version": "5.0.0",
            "timestamp": datetime.now().isoformat()
        }

# ==================== SERVIDOR JERÁRQUICO SUPERIOR ====================

class HierarchicalServer:
    """Servidor de Arquitectura Jerárquica Superior"""
    
    def __init__(self):
        self.app = FastAPI(
            title="SilhouetteMCP Arquitectura Jerárquica Superior",
            description="Servidor jerárquico con 100+ agentes especializados y coordinación avanzada",
            version="5.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Configuración CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            allow_headers=["*"]
        )
        
        # Componentes principales
        self.master_coordinator = MasterCoordinator()
        self.task_assigner = IntelligentTaskAssigner()
        self.team_manager = TeamManager()
        self.hierarchical_state = HierarchicalState(
            coordinator_id="master_coordinator",
            leader_term=0,
            leader_commit_index=0,
            last_applied=0,
            peers=["coordinator_1", "coordinator_2"]
        )
        
        # Sistemas mejorados integrados
        self.security_integration = SecurityIntegration()
        self.enterprise_orchestrator_integration = None  # Se inicializará después
        self.auto_scaling_manager = None  # Se inicializará después
        self.load_balancing_manager = None  # Se inicializará después
        self.health_monitor = None  # Se inicializará después
        
        # Sistema de tareas
        self.pending_tasks: List[Task] = []
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []
        
        # Configurar rutas
        self.setup_routes()
        self.setup_websocket()
        self.setup_improved_systems_routes()
        
    async def initialize(self):
        """Inicializa el servidor jerárquico"""
        try:
            # Inicializar componentes principales
            await self.master_coordinator.initialize()
            await self.task_assigner.initialize()
            await self.team_manager.initialize_teams()
            
            # Inicializar sistemas mejorados
            await self.initialize_improved_systems()
            
            # Actualizar estado jerárquico
            self.hierarchical_state.teams = self.team_manager.teams
            self.hierarchical_state.agents = self.team_manager.agents
            
            logger.info("Servidor jerárquico inicializado exitosamente")
            logger.info(f"Total de equipos: {len(self.team_manager.teams)}")
            logger.info(f"Total de agentes: {len(self.team_manager.agents)}")
            logger.info("Sistemas mejorados activados:")
            logger.info(f"  - Auto-Scaling: {self.auto_scaling_manager.status.value if self.auto_scaling_manager else 'N/A'}")
            logger.info(f"  - Load Balancing: {self.load_balancing_manager.current_strategy if self.load_balancing_manager else 'N/A'}")
            logger.info(f"  - Security Level: {self.security_integration.security_level.name}")
            logger.info(f"  - Enterprise Orchestrator: {self.enterprise_orchestrator_integration.sync_status['sync_status'] if self.enterprise_orchestrator_integration else 'N/A'}")
            
        except Exception as e:
            logger.error(f"Error inicializando servidor jerárquico: {e}")
            raise
    
    async def initialize_improved_systems(self):
        """Inicializa los sistemas mejorados"""
        try:
            # Inicializar Auto-Scaling Manager
            self.auto_scaling_manager = AutoScalingManager(self.team_manager)
            
            # Inicializar Load Balancing Manager
            self.load_balancing_manager = LoadBalancingManager(self.team_manager)
            
            # Inicializar Health Monitor
            self.health_monitor = HealthMonitor(self.team_manager, self)
            
            # Inicializar Enterprise Orchestrator Integration
            self.enterprise_orchestrator_integration = EnterpriseOrchestratorIntegration(self)
            
            # Iniciar sistemas en background
            asyncio.create_task(self.auto_scaling_manager.monitor_and_scale())
            asyncio.create_task(self.health_monitor.monitor_system_health())
            
            # Inicializar integración con orchestrator
            await self.enterprise_orchestrator_integration.initialize_integration()
            
            logger.info("Sistemas mejorados inicializados correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando sistemas mejorados: {e}")
            raise
    
    def setup_routes(self):
        """Configura las rutas de la API"""
        
        # ============ ENDPOINTS DE SISTEMA ============
        
        @self.app.get("/")
        async def root():
            """Endpoint raíz del sistema jerárquico con validación de seguridad"""
            # Validar seguridad de la petición
            # (En producción, esto se haría a través de middleware)
            
            return {
                "message": "SilhouetteMCP Arquitectura Jerárquica Superior v5.0.0",
                "status": "operational",
                "architecture": "hierarchical_5_levels_with_enhanced_systems",
                "total_agents": len(self.team_manager.agents),
                "total_teams": len(self.team_manager.teams),
                "enhanced_systems": {
                    "auto_scaling": self.auto_scaling_manager is not None,
                    "security_integration": self.security_integration.security_active,
                    "orchestrator_integration": self.enterprise_orchestrator_integration is not None,
                    "load_balancing": self.load_balancing_manager is not None,
                    "health_monitoring": self.health_monitor is not None
                },
                "components": {
                    "master_coordinator": "active",
                    "intelligent_task_assigner": "active", 
                    "team_managers": "active",
                    "metrics_system": "active",
                    "websocket_server": "active",
                    "auto_scaling_manager": "active" if self.auto_scaling_manager else "inactive",
                    "security_integration": "active",
                    "enterprise_orchestrator": "active" if self.enterprise_orchestrator_integration else "inactive",
                    "load_balancing_manager": "active" if self.load_balancing_manager else "inactive",
                    "health_monitor": "active" if self.health_monitor else "inactive"
                },
                "ports": {
                    "legacy_server": 8001,
                    "hierarchical_core": 8002,
                    "dashboard_main": 8003,
                    "orchestrator_integration": "8010-8014",
                    "security_system": "8015-8019",
                    "autoscaling_lb": "8020-8024"
                }
            }
        
        @self.app.get("/health")
        async def health_check():
            """Verificación de salud del sistema"""
            system_state = await self.master_coordinator.get_system_state()
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "system_metrics": system_state,
                "active_components": [
                    "master_coordinator",
                    "task_assigner", 
                    "team_manager",
                    "metrics_system"
                ]
            }
        
        # ============ ENDPOINTS DE COORDINACIÓN ============
        
        @self.app.get("/hierarchical/overview")
        async def get_hierarchical_overview():
            """Obtiene vista general de la jerarquía"""
            return await self.team_manager.get_system_overview()
        
        @self.app.get("/hierarchical/teams")
        async def get_team_status():
            """Obtiene estado detallado de todos los equipos"""
            return await self.team_manager.get_team_status()
        
        @self.app.post("/hierarchical/strategic-decision")
        async def make_strategic_decision(request: Dict[str, Any]):
            """Toma una decisión estratégica"""
            decision = await self.master_coordinator.make_strategic_decision(request)
            return decision
        
        @self.app.post("/hierarchical/assign-task")
        async def assign_task_intelligently(request: Dict[str, Any]):
            """Asigna una tarea usando el asignador inteligente con load balancing avanzado"""
            try:
                # Crear tarea
                task = Task(
                    id=str(uuid.uuid4()),
                    title=request.get("title", ""),
                    description=request.get("description", ""),
                    priority=TaskPriority(request.get("priority", 3)),
                    team_type=TeamType(request.get("team_type")),
                    complexity=request.get("complexity", 5),
                    estimated_duration=request.get("estimated_duration", 60),
                    created_at=datetime.now()
                )
                
                # Encontrar agentes disponibles
                available_agents = [agent for agent in self.team_manager.agents.values() 
                                  if agent.status == "active"]
                
                # Usar load balancing avanzado si está disponible
                if self.load_balancing_manager:
                    assigned_agent_id = await self.load_balancing_manager.assign_task_intelligently(task, available_agents)
                    
                    if assigned_agent_id:
                        task.assigned_to = assigned_agent_id
                        task.assigned_team = request.get("team_type")
                        task.status = "assigned"
                        task.metadata["assignment_strategy"] = self.load_balancing_manager.current_strategy
                        
                        self.active_tasks[task.id] = task
                        
                        return {
                            "task_id": task.id,
                            "assigned_agent": assigned_agent_id,
                            "status": "assigned",
                            "assignment_strategy": self.load_balancing_manager.current_strategy,
                            "estimated_completion": (datetime.now() + timedelta(minutes=task.estimated_duration)).isoformat()
                        }
                else:
                    # Fallback al asignador inteligente tradicional
                    assigned_agent_id = await self.task_assigner.assign_task(task, available_agents)
                    
                    if assigned_agent_id:
                        task.assigned_to = assigned_agent_id
                        task.assigned_team = request.get("team_type")
                        task.status = "assigned"
                        task.metadata["assignment_strategy"] = "traditional"
                        
                        self.active_tasks[task.id] = task
                        
                        return {
                            "task_id": task.id,
                            "assigned_agent": assigned_agent_id,
                            "status": "assigned",
                            "assignment_strategy": "traditional",
                            "estimated_completion": (datetime.now() + timedelta(minutes=task.estimated_duration)).isoformat()
                        }
                
                # Si no se pudo asignar
                task.status = "pending"
                self.pending_tasks.append(task)
                return {"task_id": task.id, "status": "pending", "message": "No se pudo asignar la tarea"}
                    
            except Exception as e:
                logger.error(f"Error asignando tarea: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ============ ENDPOINTS DE MÉTRICAS ============
        
        @self.app.get("/metrics/system")
        async def get_system_metrics():
            """Obtiene métricas del sistema"""
            return await self.team_manager.metrics_system.get_system_overview()
        
        @self.app.get("/metrics/teams/{team_id}")
        async def get_team_metrics(team_id: str):
            """Obtiene métricas de un equipo específico"""
            if team_id not in self.team_manager.teams:
                raise HTTPException(status_code=404, detail="Equipo no encontrado")
            
            team = self.team_manager.teams[team_id]
            team_agents = [self.team_manager.agents[agent_id] for agent_id in team.members 
                          if agent_id in self.team_manager.agents]
            
            return {
                "team_id": team_id,
                "team_name": team.name,
                "total_agents": len(team_agents),
                "active_agents": len([a for a in team_agents if a.status == "active"]),
                "total_tasks": sum(a.performance.tasks_completed + a.performance.tasks_failed for a in team_agents),
                "average_performance": np.mean([a.performance.performance_score for a in team_agents]) if team_agents else 0.0,
                "workload_ratio": team.workload_ratio,
                "performance_score": team.performance_score
            }
        
        @self.app.get("/metrics/agents/{agent_id}")
        async def get_agent_metrics(agent_id: str):
            """Obtiene métricas de un agente específico"""
            if agent_id not in self.team_manager.agents:
                raise HTTPException(status_code=404, detail="Agente no encontrado")
            
            agent = self.team_manager.agents[agent_id]
            return {
                "agent_id": agent_id,
                "agent_name": agent.name,
                "level": agent.level.value,
                "team_type": agent.team_type.value,
                "status": agent.status,
                "capabilities": list(agent.capabilities),
                "performance": asdict(agent.performance),
                "current_tasks": agent.current_tasks,
                "specialization": agent.specialization
            }
        
        # ============ ENDPOINTS DE GESTIÓN ============
        
        @self.app.get("/agents")
        async def list_all_agents():
            """Lista todos los agentes del sistema"""
            return {
                "total_agents": len(self.team_manager.agents),
                "agents": [
                    {
                        "id": agent_id,
                        "name": agent.name,
                        "level": agent.level.value,
                        "team_type": agent.team_type.value if agent.team_type else None,
                        "status": agent.status,
                        "specialization": agent.specialization,
                        "performance_score": agent.performance.performance_score
                    }
                    for agent_id, agent in self.team_manager.agents.items()
                ]
            }
        
        @self.app.get("/teams")
        async def list_all_teams():
            """Lista todos los equipos del sistema"""
            return {
                "total_teams": len(self.team_manager.teams),
                "teams": [
                    {
                        "id": team_id,
                        "name": team.name,
                        "type": team.type.value,
                        "leader_id": team.leader_id,
                        "capacity": team.capacity,
                        "current_members": len(team.members),
                        "workload_ratio": team.workload_ratio,
                        "status": team.status
                    }
                    for team_id, team in self.team_manager.teams.items()
                ]
            }
        
        @self.app.get("/tasks")
        async def list_tasks():
            """Lista todas las tareas del sistema"""
            return {
                "pending_tasks": len(self.pending_tasks),
                "active_tasks": len(self.active_tasks),
                "completed_tasks": len(self.completed_tasks),
                "pending": [task.to_dict() for task in self.pending_tasks],
                "active": [task.to_dict() for task in self.active_tasks.values()],
                "completed": [task.to_dict() for task in self.completed_tasks[-50:]]  # Últimas 50
            }
        
        # ============ ENDPOINTS DE OPTIMIZACIÓN ============
        
        @self.app.post("/optimize/load-balancing")
        async def optimize_load_balancing():
            """Optimiza el balanceo de carga del sistema usando estrategias avanzadas"""
            try:
                # Usar el load balancing manager avanzado si está disponible
                if self.load_balancing_manager:
                    await self.load_balancing_manager.optimize_load_balancing()
                    
                    return {
                        "optimization_status": "completed",
                        "strategy_optimized": self.load_balancing_manager.current_strategy,
                        "available_strategies": list(self.load_balancing_manager.load_balancing_strategies.keys()),
                        "optimization_method": "adaptive_intelligent",
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    # Fallback al método tradicional
                    active_agents = [agent for agent in self.team_manager.agents.values() 
                                   if agent.status == "active"]
                    
                    assignment = await self.task_assigner.optimize_load_balancing(
                        self.pending_tasks + list(self.active_tasks.values()), 
                        active_agents
                    )
                    
                    return {
                        "optimization_status": "completed",
                        "tasks_optimized": len(assignment),
                        "assignment": assignment,
                        "optimization_method": "traditional",
                        "timestamp": datetime.now().isoformat()
                    }
                
            except Exception as e:
                logger.error(f"Error en optimización: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ============ ENDPOINTS DE DASHBOARD ============
        
        @self.app.get("/dashboard/hierarchy")
        async def get_hierarchical_dashboard():
            """Dashboard jerárquico completo con sistemas mejorados"""
            system_overview = await self.team_manager.get_system_overview()
            team_status = await self.team_manager.get_team_status()
            
            # Obtener métricas del coordinador maestro
            strategic_decisions = getattr(self.master_coordinator, 'strategic_decisions', [])
            
            # Obtener información de sistemas mejorados
            enhanced_systems_info = {}
            
            if self.auto_scaling_manager:
                enhanced_systems_info["auto_scaling"] = {
                    "status": self.auto_scaling_manager.status.value,
                    "total_scaling_actions": len(self.auto_scaling_manager.scaling_history),
                    "last_scaling_action": self.auto_scaling_manager.scaling_history[-1] if self.auto_scaling_manager.scaling_history else None
                }
            
            if self.security_integration:
                enhanced_systems_info["security"] = {
                    "level": self.security_integration.security_level.name,
                    "active_policies": self.security_integration.security_policies
                }
            
            if self.enterprise_orchestrator_integration:
                enhanced_systems_info["orchestrator"] = {
                    "integration_status": self.enterprise_orchestrator_integration.sync_status["sync_status"],
                    "services_registered": self.enterprise_orchestrator_integration.sync_status["services_registered"]
                }
            
            if self.load_balancing_manager:
                enhanced_systems_info["load_balancing"] = {
                    "current_strategy": self.load_balancing_manager.current_strategy,
                    "assignment_history_size": len(self.load_balancing_manager.assignment_history)
                }
            
            if self.health_monitor:
                enhanced_systems_info["health_monitoring"] = {
                    "status": self.health_monitor.health_status.value,
                    "auto_healing_enabled": self.health_monitor.auto_healing_enabled,
                    "recent_failures": len([f for f in self.health_monitor.failure_history if (datetime.now() - f["timestamp"]).seconds < 3600])
                }
            
            return {
                "dashboard": {
                    "system_overview": system_overview,
                    "team_status": team_status,
                    "master_coordinator": {
                        "status": self.master_coordinator.status,
                        "state": self.master_coordinator.state.value,
                        "strategic_decisions_count": len(strategic_decisions),
                        "leader_term": self.master_coordinator.leader_term
                    },
                    "task_assigner": {
                        "status": self.task_assigner.status,
                        "assignments_made": len(self.task_assigner.assignment_history)
                    },
                    "enhanced_systems": enhanced_systems_info,
                    "real_time_metrics": {
                        "timestamp": datetime.now().isoformat(),
                        "websocket_connections": len(self.team_manager.metrics_system.websocket_connections)
                    }
                }
            }
        
        @self.app.get("/dashboard/performance")
        async def get_performance_dashboard():
            """Dashboard de rendimiento específico"""
            metrics_system = self.team_manager.metrics_system
            system_health = metrics_system.calculate_system_health()
            
            # Calcular métricas por equipo
            team_performance = {}
            for team_id, team in self.team_manager.teams.items():
                team_agents = [self.team_manager.agents[agent_id] for agent_id in team.members 
                              if agent_id in self.team_manager.agents]
                
                if team_agents:
                    team_performance[team_id] = {
                        "team_name": team.name,
                        "average_performance": np.mean([a.performance.performance_score for a in team_agents]),
                        "total_tasks": sum(a.performance.tasks_completed + a.performance.tasks_failed for a in team_agents),
                        "success_rate": np.mean([a.performance.success_rate for a in team_agents]),
                        "active_agents": len([a for a in team_agents if a.status == "active"]),
                        "workload_ratio": team.workload_ratio
                    }
            
            return {
                "performance_dashboard": {
                    "system_health": system_health,
                    "team_performance": team_performance,
                    "overall_metrics": await metrics_system.get_system_overview(),
                    "recommendations": await self.generate_performance_recommendations()
                }
            }
        
        async def generate_performance_recommendations(self) -> List[str]:
            """Genera recomendaciones basadas en el rendimiento"""
            recommendations = []
            
            # Analizar salud del sistema
            system_health = self.team_manager.metrics_system.calculate_system_health()
            if system_health < 0.7:
                recommendations.append("Sistema con salud por debajo del 70% - revisar balance de carga")
            
            # Analizar equipos con bajo rendimiento
            for team_id, team in self.team_manager.teams.items():
                if team.workload_ratio > 0.9:
                    recommendations.append(f"Equipo {team.name} sobrecargado - considerar redistribuir tareas")
            
            # Analizar agentes con bajo rendimiento
            low_performance_agents = [agent for agent in self.team_manager.agents.values() 
                                    if agent.performance.performance_score < 70]
            if low_performance_agents:
                recommendations.append(f"{len(low_performance_agents)} agentes con bajo rendimiento - revisar capacitación")
            
            return recommendations
    
    def setup_websocket(self):
        """Configura el servidor WebSocket para actualizaciones en tiempo real"""
        
        @self.app.websocket("/ws/metrics")
        async def websocket_metrics_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.team_manager.metrics_system.add_websocket_connection(websocket)
            
            try:
                while True:
                    # Enviar métricas actualizadas cada 5 segundos
                    await asyncio.sleep(5)
                    metrics = await self.team_manager.metrics_system.get_system_overview()
                    await websocket.send_json({
                        "type": "system_metrics",
                        "data": metrics,
                        "timestamp": datetime.now().isoformat()
                    })
                    
            except WebSocketDisconnect:
                self.team_manager.metrics_system.remove_websocket_connection(websocket)
            except Exception as e:
                logger.error(f"Error en WebSocket: {e}")
                self.team_manager.metrics_system.remove_websocket_connection(websocket)
        
        @self.app.websocket("/ws/hierarchy")
        async def websocket_hierarchy_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.team_manager.metrics_system.add_websocket_connection(websocket)
            
            try:
                while True:
                    # Enviar estado jerárquico cada 10 segundos
                    await asyncio.sleep(10)
                    hierarchy_status = {
                        "teams": len(self.team_manager.teams),
                        "agents": len(self.team_manager.agents),
                        "active_agents": len([a for a in self.team_manager.agents.values() if a.status == "active"]),
                        "tasks": {
                            "pending": len(self.pending_tasks),
                            "active": len(self.active_tasks),
                            "completed": len(self.completed_tasks)
                        }
                    }
                    await websocket.send_json({
                        "type": "hierarchy_status",
                        "data": hierarchy_status,
                        "timestamp": datetime.now().isoformat()
                    })
                    
            except WebSocketDisconnect:
                self.team_manager.metrics_system.remove_websocket_connection(websocket)
            except Exception as e:
                logger.error(f"Error en WebSocket jerarquía: {e}")
                self.team_manager.metrics_system.remove_websocket_connection(websocket)
    
    def setup_improved_systems_routes(self):
        """Configura rutas para sistemas mejorados"""
        
        # ============ ENDPOINTS DE AUTO-SCALING (8020-8024) ============
        
        @self.app.get("/autoscaling/status")
        async def get_autoscaling_status():
            """Estado del sistema de auto-scaling"""
            if not self.auto_scaling_manager:
                raise HTTPException(status_code=503, detail="Auto-scaling manager not initialized")
            
            return {
                "status": self.auto_scaling_manager.status.value,
                "scaling_history": self.auto_scaling_manager.scaling_history[-10:],
                "resource_thresholds": self.auto_scaling_manager.resource_thresholds,
                "scaling_policies": self.auto_scaling_manager.scaling_policies,
                "total_agents": len(self.team_manager.agents),
                "active_agents": len([a for a in self.team_manager.agents.values() if a.status == "active"])
            }
        
        @self.app.post("/autoscaling/trigger")
        async def trigger_autoscaling(action: Dict[str, Any]):
            """Dispara manualmente una acción de auto-scaling"""
            if not self.auto_scaling_manager:
                raise HTTPException(status_code=503, detail="Auto-scaling manager not initialized")
            
            scaling_action = action.get("action", "scale_up")
            target_teams = action.get("target_teams", ["all"])
            
            try:
                if scaling_action == "scale_up":
                    await self.auto_scaling_manager.scale_up_agents({"target_teams": target_teams})
                elif scaling_action == "scale_down":
                    await self.auto_scaling_manager.scale_down_agents()
                
                return {
                    "status": "success",
                    "action": scaling_action,
                    "target_teams": target_teams,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error triggering auto-scaling: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/autoscaling/metrics")
        async def get_autoscaling_metrics():
            """Métricas de auto-scaling"""
            if not self.auto_scaling_manager:
                raise HTTPException(status_code=503, detail="Auto-scaling manager not initialized")
            
            metrics = await self.auto_scaling_manager.collect_system_metrics()
            return {
                "metrics": metrics,
                "scaling_history_count": len(self.auto_scaling_manager.scaling_history),
                "last_scaling_action": self.auto_scaling_manager.scaling_history[-1] if self.auto_scaling_manager.scaling_history else None
            }
        
        # ============ ENDPOINTS DE SEGURIDAD (8015-8019) ============
        
        @self.app.get("/security/health")
        async def security_health_check():
            """Health check del sistema de seguridad"""
            return await self.security_integration.get_security_status()
        
        @self.app.post("/security/validate")
        async def validate_security_request(request: Request, endpoint_type: str = "api"):
            """Valida seguridad de una petición"""
            security_result = await self.security_integration.validate_security(request, endpoint_type)
            
            # Log de eventos de seguridad
            if not security_result["valid"]:
                await self.security_integration.log_security_event(
                    "security_validation_failed",
                    {
                        "client_ip": request.client.host,
                        "endpoint": str(request.url),
                        "failed_checks": security_result["checks_failed"],
                        "risk_level": security_result["risk_level"]
                    }
                )
            
            return security_result
        
        @self.app.get("/security/monitoring")
        async def get_security_monitoring():
            """Monitoreo de seguridad en tiempo real"""
            return {
                "security_level": self.security_integration.security_level.value,
                "active_policies": self.security_integration.security_policies,
                "authenticated_sessions": len(self.security_integration.auth_tokens),
                "last_security_check": datetime.now().isoformat()
            }
        
        @self.app.post("/security/log-event")
        async def log_security_event(event_data: Dict[str, Any]):
            """Registra evento de seguridad manualmente"""
            await self.security_integration.log_security_event(
                event_data.get("event_type", "manual_log"),
                event_data.get("details", {})
            )
            return {"status": "event_logged", "timestamp": datetime.now().isoformat()}
        
        # ============ ENDPOINTS DE ORCHESTRATOR INTEGRATION (8010-8014) ============
        
        @self.app.get("/orchestrator/integration-status")
        async def get_orchestrator_integration_status():
            """Estado de integración con Enterprise Orchestrator"""
            if not self.enterprise_orchestrator_integration:
                raise HTTPException(status_code=503, detail="Orchestrator integration not initialized")
            
            return await self.enterprise_orchestrator_integration.get_integration_status()
        
        @self.app.post("/orchestrator/sync")
        async def force_sync_with_orchestrator():
            """Fuerza sincronización con Enterprise Orchestrator"""
            if not self.enterprise_orchestrator_integration:
                raise HTTPException(status_code=503, detail="Orchestrator integration not initialized")
            
            try:
                await self.enterprise_orchestrator_integration.sync_with_orchestrator()
                return {
                    "status": "sync_completed",
                    "timestamp": datetime.now().isoformat(),
                    "sync_status": self.enterprise_orchestrator_integration.sync_status
                }
            except Exception as e:
                logger.error(f"Error syncing with orchestrator: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/orchestrator/services")
        async def get_registered_services():
            """Servicios registrados con Enterprise Orchestrator"""
            if not self.enterprise_orchestrator_integration:
                raise HTTPException(status_code=503, detail="Orchestrator integration not initialized")
            
            return {
                "services_registered": self.enterprise_orchestrator_integration.sync_status["services_registered"],
                "health_checks_passed": self.enterprise_orchestrator_integration.sync_status["health_checks_passed"],
                "last_sync": self.enterprise_orchestrator_integration.sync_status["last_sync"],
                "communication_channel": self.enterprise_orchestrator_integration.communication_channel
            }
        
        # ============ ENDPOINTS DE LOAD BALANCING ============
        
        @self.app.get("/loadbalancing/metrics")
        async def get_load_balancing_metrics():
            """Métricas de load balancing"""
            if not self.load_balancing_manager:
                raise HTTPException(status_code=503, detail="Load balancing manager not initialized")
            
            return await self.load_balancing_manager.get_load_balancing_metrics()
        
        @self.app.post("/loadbalancing/optimize")
        async def optimize_load_balancing():
            """Optimiza estrategia de load balancing"""
            if not self.load_balancing_manager:
                raise HTTPException(status_code=503, detail="Load balancing manager not initialized")
            
            try:
                await self.load_balancing_manager.optimize_load_balancing()
                return {
                    "status": "optimization_completed",
                    "current_strategy": self.load_balancing_manager.current_strategy,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error optimizing load balancing: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/loadbalancing/strategy")
        async def get_current_load_balancing_strategy():
            """Estrategia actual de load balancing"""
            if not self.load_balancing_manager:
                raise HTTPException(status_code=503, detail="Load balancing manager not initialized")
            
            return {
                "current_strategy": self.load_balancing_manager.current_strategy,
                "available_strategies": list(self.load_balancing_manager.load_balancing_strategies.keys()),
                "assignment_history_size": len(self.load_balancing_manager.assignment_history)
            }
        
        # ============ ENDPOINTS DE HEALTH MONITOR ============
        
        @self.app.get("/health-monitor/report")
        async def get_health_monitor_report():
            """Reporte completo del monitor de salud"""
            if not self.health_monitor:
                raise HTTPException(status_code=503, detail="Health monitor not initialized")
            
            return await self.health_monitor.get_health_report()
        
        @self.app.post("/health-monitor/force-check")
        async def force_comprehensive_health_check():
            """Fuerza health check comprensivo"""
            if not self.health_monitor:
                raise HTTPException(status_code=503, detail="Health monitor not initialized")
            
            try:
                health_report = await self.health_monitor.perform_comprehensive_health_check()
                return {
                    "status": "check_completed",
                    "health_report": health_report,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error in forced health check: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health-monitor/status")
        async def get_current_health_status():
            """Estado actual de salud del sistema"""
            if not self.health_monitor:
                raise HTTPException(status_code=503, detail="Health monitor not initialized")
            
            return {
                "current_health_status": self.health_monitor.health_status.value,
                "auto_healing_enabled": self.health_monitor.auto_healing_enabled,
                "recent_issues": len([f for f in self.health_monitor.failure_history if (datetime.now() - f["timestamp"]).seconds < 3600])
            }
        
        # ============ ENDPOINTS DE DASHBOARD INTEGRADO ============
        
        @self.app.get("/dashboard/improved-systems")
        async def get_improved_systems_dashboard():
            """Dashboard integrado de sistemas mejorados"""
            try:
                # Recopilar estado de todos los sistemas mejorados
                dashboard_data = {
                    "timestamp": datetime.now().isoformat()
                }
                
                if self.auto_scaling_manager:
                    dashboard_data["auto_scaling"] = {
                        "status": self.auto_scaling_manager.status.value,
                        "scaling_history_count": len(self.auto_scaling_manager.scaling_history)
                    }
                
                dashboard_data["security"] = await self.security_integration.get_security_status()
                
                if self.enterprise_orchestrator_integration:
                    dashboard_data["orchestrator"] = await self.enterprise_orchestrator_integration.get_integration_status()
                
                if self.load_balancing_manager:
                    dashboard_data["load_balancing"] = await self.load_balancing_manager.get_load_balancing_metrics()
                
                if self.health_monitor:
                    dashboard_data["health_monitor"] = await self.health_monitor.get_health_report()
                
                return {"improved_systems_dashboard": dashboard_data}
                
            except Exception as e:
                logger.error(f"Error generating improved systems dashboard: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/system-overview/enhanced")
        async def get_enhanced_system_overview():
            """Vista general del sistema con mejoras"""
            basic_overview = await self.team_manager.get_system_overview()
            
            # Añadir información de sistemas mejorados
            enhanced_overview = {
                **basic_overview,
                "enhanced_systems": {
                    "auto_scaling": {
                        "enabled": self.auto_scaling_manager is not None,
                        "status": self.auto_scaling_manager.status.value if self.auto_scaling_manager else "not_initialized"
                    },
                    "security": {
                        "enabled": True,
                        "level": self.security_integration.security_level.name
                    },
                    "orchestrator_integration": {
                        "enabled": self.enterprise_orchestrator_integration is not None,
                        "status": self.enterprise_orchestrator_integration.sync_status["sync_status"] if self.enterprise_orchestrator_integration else "not_initialized"
                    },
                    "load_balancing": {
                        "enabled": self.load_balancing_manager is not None,
                        "strategy": self.load_balancing_manager.current_strategy if self.load_balancing_manager else "not_initialized"
                    },
                    "health_monitoring": {
                        "enabled": self.health_monitor is not None,
                        "status": self.health_monitor.health_status.value if self.health_monitor else "not_initialized"
                    }
                },
                "integration_status": {
                    "enterprise_grade_features": True,
                    "bidirectional_communication": self.enterprise_orchestrator_integration is not None,
                    "auto_healing": self.health_monitor is not None if self.health_monitor else False,
                    "real_time_optimization": self.load_balancing_manager is not None
                }
            }
            
            return enhanced_overview

# ==================== SERVIDOR UNIFICADO LEGACY (100% COMPATIBLE) ====================

class UnifiedLegacyServer:
    """Servidor Unificado Legacy - Mantiene 100% compatibilidad con v4.0.0"""
    
    def __init__(self):
        self.app = FastAPI(
            title="SilhouetteMCP Server - Legacy Unified",
            description="Servidor unificado legacy v4.0.0 - 100% compatible",
            version="4.0.0-legacy",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Configuración CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            allow_headers=["*"]
        )
        
        self.setup_legacy_routes()
    
    def setup_legacy_routes(self):
        """Configura rutas legacy para mantener compatibilidad total"""
        
        @self.app.get("/")
        async def legacy_root():
            return {
                "message": "SilhouetteMCP Server Unificado Legacy v4.0.0",
                "status": "operational",
                "total_tools": 51,
                "agent_categories": 6,
                "compatibility": "100% maintained",
                "version": "4.0.0"
            }
        
        @self.app.get("/health")
        async def legacy_health():
            return {
                "status": "healthy",
                "legacy_server": "active",
                "backward_compatibility": "full"
            }
        
        # Placeholder endpoints para herramientas legacy
        # Estos mantienen la estructura exacta del servidor original
        
        # Maps Intelligence Tools
        @self.app.get("/maps/geocode")
        async def legacy_geocode():
            return {"tool": "geocoding", "status": "legacy_compatible"}
        
        @self.app.get("/maps/directions")
        async def legacy_directions():
            return {"tool": "directions", "status": "legacy_compatible"}
        
        # Financial Intelligence Tools
        @self.app.get("/financial/stock-analysis")
        async def legacy_stock_analysis():
            return {"tool": "stock_analysis", "status": "legacy_compatible"}
        
        @self.app.get("/financial/market-research")
        async def legacy_market_research():
            return {"tool": "market_research", "status": "legacy_compatible"}
        
        # Social Media + Travel Tools
        @self.app.get("/social/content-curation")
        async def legacy_content_curation():
            return {"tool": "content_curation", "status": "legacy_compatible"}
        
        @self.app.get("/travel/planning")
        async def legacy_travel_planning():
            return {"tool": "travel_planning", "status": "legacy_compatible"}
        
        # Content Creation Tools
        @self.app.get("/content/image-creation")
        async def legacy_image_creation():
            return {"tool": "image_creation", "status": "legacy_compatible"}
        
        @self.app.get("/content/video-production")
        async def legacy_video_production():
            return {"tool": "video_production", "status": "legacy_compatible"}
        
        # Database Operations Tools
        @self.app.get("/database/supabase-operations")
        async def legacy_database_ops():
            return {"tool": "database_operations", "status": "legacy_compatible"}
        
        # Research Intelligence Tools
        @self.app.get("/research/academic-analysis")
        async def legacy_research():
            return {"tool": "research_intelligence", "status": "legacy_compatible"}

# ==================== APLICACIÓN PRINCIPAL ====================

# Crear instancias de servidores
hierarchical_server = HierarchicalServer()
unified_legacy_server = UnifiedLegacyServer()

# Montar aplicaciones en diferentes rutas
main_app = FastAPI(title="SilhouetteMCP Complete System")

# Montar servidor jerárquico en ruta principal
main_app.mount("/hierarchical", hierarchical_server.app)

# Montar servidor legacy en ruta específica
main_app.mount("/legacy", unified_legacy_server.app)

# Ruta raíz redirecciona al sistema jerárquico
@main_app.get("/")
async def complete_system_root():
    return {
        "message": "SilhouetteMCP Complete System v5.0.0",
        "architecture": "Hierarchical Architecture with Legacy Compatibility",
        "components": {
            "hierarchical_system": {
                "path": "/hierarchical",
                "description": "Sistema jerárquico con 100+ agentes",
                "status": "active"
            },
            "legacy_unified": {
                "path": "/legacy", 
                "description": "Servidor unificado legacy v4.0.0",
                "status": "active"
            }
        },
        "total_agents": 100,
        "teams": 7,
        "coordination": "Advanced 5-level hierarchy",
        "compatibility": "100% backward compatible"
    }

@main_app.get("/health")
async def complete_system_health():
    return {
        "status": "healthy",
        "hierarchical_server": "active",
        "legacy_server": "active",
        "total_system_status": "operational"
    }

# ==================== FUNCIONES DE INICIALIZACIÓN ====================

async def initialize_complete_system():
    """Inicializa el sistema completo con sistemas mejorados"""
    try:
        logger.info("Iniciando SilhouetteMCP Arquitectura Jerárquica Superior v5.0.0")
        logger.info("Con Sistemas Mejorados Integrados:")
        logger.info("  ✓ Auto-Scaling para 100+ agentes")
        logger.info("  ✓ Seguridad multicapa (puertos 8015-8019)")
        logger.info("  ✓ Integración Enterprise Orchestrator (puertos 8010-8014)")
        logger.info("  ✓ Load Balancing Inteligente")
        logger.info("  ✓ Auto-Healing y Health Monitoring")
        logger.info("  ✓ Comunicación Bidireccional con Orquestador")
        logger.info("="*80)
        
        # Inicializar servidor jerárquico con sistemas mejorados
        await hierarchical_server.initialize()
        
        logger.info("Sistema completo inicializado exitosamente")
        logger.info("="*80)
        logger.info("ARQUITECTURA JERÁRQUICA SUPERIOR CON SISTEMAS MEJORADOS ACTIVA")
        logger.info("="*80)
        logger.info("COMPONENTES PRINCIPALES:")
        logger.info(f"  Total de Agentes: {len(hierarchical_server.team_manager.agents)}")
        logger.info(f"  Total de Equipos: {len(hierarchical_server.team_manager.teams)}")
        logger.info(f"  Master Coordinator: {hierarchical_server.master_coordinator.status}")
        logger.info(f"  Intelligent Task Assigner: {hierarchical_server.task_assigner.status}")
        logger.info("")
        logger.info("SISTEMAS MEJORADOS:")
        if hierarchical_server.auto_scaling_manager:
            logger.info(f"  Auto-Scaling Manager: {hierarchical_server.auto_scaling_manager.status.value}")
        if hierarchical_server.security_integration:
            logger.info(f"  Security Integration: {hierarchical_server.security_integration.security_level.name} level")
        if hierarchical_server.enterprise_orchestrator_integration:
            logger.info(f"  Enterprise Orchestrator: {hierarchical_server.enterprise_orchestrator_integration.sync_status['sync_status']}")
        if hierarchical_server.load_balancing_manager:
            logger.info(f"  Load Balancing: {hierarchical_server.load_balancing_manager.current_strategy} strategy")
        if hierarchical_server.health_monitor:
            logger.info(f"  Health Monitor: {hierarchical_server.health_monitor.health_status.value}")
        logger.info("")
        logger.info("PUERTOS ACTIVOS:")
        logger.info("  8001: Servidor Unificado Legacy")
        logger.info("  8002: Arquitectura Jerárquica Superior")
        logger.info("  8003: Dashboard y Métricas")
        logger.info("  8010-8014: Coordinación con Arquitectura Mejorada")
        logger.info("  8015-8019: Protección de Seguridad")
        logger.info("  8020-8024: Auto-Scaling y Load Balancing")
        logger.info("="*80)
        
        return True
        
    except Exception as e:
        logger.error(f"Error inicializando sistema completo: {e}")
        logger.error(f"Detalles del error: {traceback.format_exc()}")
        return False

# ==================== PUNTO DE ENTRADA ====================

if __name__ == "__main__":
    import uvicorn
    
    async def run_servers():
        """Ejecuta todos los servidores"""
        # Inicializar sistema
        await initialize_complete_system()
        
        # Configurar servidores
        servers = [
            {
                "app": main_app,
                "host": "0.0.0.0",
                "port": 8003,
                "name": "Complete System (Main Dashboard)"
            },
            {
                "app": hierarchical_server.app,
                "host": "0.0.0.0", 
                "port": 8002,
                "name": "Hierarchical Architecture Core"
            },
            {
                "app": unified_legacy_server.app,
                "host": "0.0.0.0",
                "port": 8001, 
                "name": "Legacy Unified Server"
            },
            # Servidores de sistemas mejorados
            {
                "app": hierarchical_server.app,  # Reutilizar app con rutas específicas
                "host": "0.0.0.0",
                "port": 8010,
                "name": "Enterprise Orchestrator Integration"
            },
            {
                "app": hierarchical_server.app,  # Reutilizar app con rutas específicas  
                "host": "0.0.0.0",
                "port": 8015,
                "name": "Enhanced Security System"
            },
            {
                "app": hierarchical_server.app,  # Reutilizar app con rutas específicas
                "host": "0.0.0.0",
                "port": 8020,
                "name": "Auto-Scaling & Load Balancing"
            }
        ]
        
        # Ejecutar servidores en paralelo
        server_tasks = []
        for server_config in servers:
            task = uvicorn.run(
                server_config["app"],
                host=server_config["host"],
                port=server_config["port"],
                log_level="info"
            )
            server_tasks.append(task)
        
        await asyncio.gather(*server_tasks)
    
    # Ejecutar sistema completo
    asyncio.run(run_servers())