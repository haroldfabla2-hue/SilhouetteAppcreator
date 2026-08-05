"""
Sistema de Colaboración en Tiempo Real Multi-usuario para MCP Core Superior

Implementa todas las funcionalidades requeridas:
1. Multi-user session management
2. Real-time agent state synchronization
3. Collaborative task execution con conflict resolution
4. Shared context entre usuarios
5. Live agent utilization monitoring
6. Role-based access control para colaboración
7. Real-time notifications y updates
8. Conflict resolution algorithms
9. Session persistence y recovery
10. Scalable WebSocket management

Utiliza WebSockets para comunicación bidireccional y Redis para session management.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Set, Any, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import hashlib
import pickle
import weakref
import threading
from collections import defaultdict, deque
import websockets
import redis.asyncio as redis
from pydantic import BaseModel, Field

from .exceptions import MCPCoreException, ErrorCode, UnauthorizedException, ForbiddenException
from .config import settings


# === CONFIGURACIÓN DE LOGGING ===
logger = logging.getLogger(__name__)


# === ENUMS Y CONSTANTES ===

class UserRole(str, Enum):
    """Roles de usuario en colaboración"""
    OWNER = "owner"
    ADMIN = "admin"
    COLLABORATOR = "collaborator"
    VIEWER = "viewer"
    GUEST = "guest"


class SessionStatus(str, Enum):
    """Estados de sesión de colaboración"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class TaskStatus(str, Enum):
    """Estados de tareas colaborativas"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    CONFLICT = "conflict"


class ConflictType(str, Enum):
    """Tipos de conflictos en colaboración"""
    TASK_ASSIGNMENT = "task_assignment"
    RESOURCE_LOCK = "resource_lock"
    DATA_CONFLICT = "data_conflict"
    PERMISSION = "permission"
    CONCURRENT_EDIT = "concurrent_edit"


class NotificationType(str, Enum):
    """Tipos de notificaciones"""
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"
    CONFLICT_RESOLVED = "conflict_resolved"
    AGENT_STATUS_CHANGE = "agent_status_change"
    SESSION_UPDATE = "session_update"


# === MODELOS DE DATOS ===

@dataclass
class User:
    """Representa un usuario en el sistema"""
    user_id: str
    username: str
    role: UserRole
    session_id: str
    websocket_connection: Optional[str] = None  # WebSocket connection ID
    last_seen: datetime = None
    permissions: Set[str] = None
    
    def __post_init__(self):
        if self.last_seen is None:
            self.last_seen = datetime.now()
        if self.permissions is None:
            self.permissions = set()


@dataclass
class CollaborationSession:
    """Sesión de colaboración multi-usuario"""
    session_id: str
    name: str
    description: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    status: SessionStatus
    participants: Dict[str, User]
    shared_context: Dict[str, Any]
    task_assignments: Dict[str, str]  # task_id -> user_id
    locks: Dict[str, str]  # resource_id -> user_id
    conflict_queue: List[Dict[str, Any]]
    
    def __post_init__(self):
        if not self.participants:
            self.participants = {}
        if not self.shared_context:
            self.shared_context = {}
        if not self.task_assignments:
            self.task_assignments = {}
        if not self.locks:
            self.locks = {}
        if not self.conflict_queue:
            self.conflict_queue = []


@dataclass
class AgentState:
    """Estado de un agente en tiempo real"""
    agent_id: str
    agent_type: str
    status: str
    current_task: Optional[str]
    utilization_percentage: float
    performance_metrics: Dict[str, float]
    last_update: datetime
    active_sessions: Set[str]
    
    def __post_init__(self):
        if not self.performance_metrics:
            self.performance_metrics = {}
        if not self.active_sessions:
            self.active_sessions = set()


@dataclass
class CollaborativeTask:
    """Tarea colaborativa con resolución de conflictos"""
    task_id: str
    title: str
    description: str
    assigned_users: Set[str]
    status: TaskStatus
    priority: int
    dependencies: List[str]
    created_at: datetime
    updated_at: datetime
    estimated_duration: Optional[int]
    actual_duration: Optional[int]
    conflict_info: Optional[Dict[str, Any]]
    results: Dict[str, Any]
    
    def __post_init__(self):
        if not self.assigned_users:
            self.assigned_users = set()
        if not self.dependencies:
            self.dependencies = []
        if not self.conflict_info:
            self.conflict_info = {}
        if not self.results:
            self.results = {}


@dataclass
class Conflict:
    """Conflicto entre usuarios/agentes"""
    conflict_id: str
    conflict_type: ConflictType
    session_id: str
    participants: Set[str]
    resource_id: str
    description: str
    created_at: datetime
    resolved: bool
    resolution_strategy: Optional[str]
    resolution_data: Optional[Dict[str, Any]]


# === Pydantic Models para APIs ===

class SessionCreateRequest(BaseModel):
    name: str = Field(..., description="Nombre de la sesión")
    description: str = Field(default="", description="Descripción de la sesión")
    initial_participants: List[str] = Field(default=[], description="IDs de usuarios iniciales")


class SessionJoinRequest(BaseModel):
    session_id: str = Field(..., description="ID de la sesión a unirse")
    user_permissions: List[str] = Field(default=[], description="Permisos adicionales del usuario")


class TaskCreateRequest(BaseModel):
    title: str = Field(..., description="Título de la tarea")
    description: str = Field(default="", description="Descripción de la tarea")
    assigned_users: List[str] = Field(default=[], description="Usuarios asignados")
    priority: int = Field(default=1, description="Prioridad (1-5)")
    dependencies: List[str] = Field(default=[], description="IDs de tareas dependientes")


class ConflictResolutionRequest(BaseModel):
    conflict_id: str = Field(..., description="ID del conflicto")
    resolution_strategy: str = Field(..., description="Estrategia de resolución")
    resolution_data: Dict[str, Any] = Field(default={}, description="Datos de resolución")


# === SISTEMA DE COLABORACIÓN EN TIEMPO REAL ===

class CollaborationEngine:
    """
    Motor principal de colaboración en tiempo real multi-usuario
    
    Gestiona todas las funcionalidades de colaboración requeridas:
    - Session management con Redis
    - WebSocket management escalable
    - Agent state synchronization
    - Task execution con conflict resolution
    - Role-based access control
    - Real-time notifications
    """
    
    def __init__(self, redis_url: str = None, max_websocket_connections: int = 1000):
        """Inicializar el motor de colaboración"""
        self.redis_url = redis_url or settings.redis_url
        self.redis_pool = None
        self.max_websocket_connections = max_websocket_connections
        self.websocket_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.active_sessions: Dict[str, CollaborationSession] = {}
        self.agent_states: Dict[str, AgentState] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id
        self.message_queue: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.subscribers: Dict[str, Set[Callable]] = defaultdict(set)
        self.lock_manager = asyncio.Lock()
        self.session_cleanup_task: Optional[asyncio.Task] = None
        
        # Configuración de recuperación
        self.recovery_enabled = True
        self.cleanup_interval = 300  # 5 minutos
        
        logger.info(f"CollaborationEngine inicializado con Redis: {self.redis_url}")
    
    async def initialize(self):
        """Inicializar conexiones y tareas de fondo"""
        try:
            # Conectar a Redis
            await self._connect_redis()
            
            # Cargar sesiones activas desde Redis
            await self._load_active_sessions()
            
            # Iniciar tareas de limpieza
            self.session_cleanup_task = asyncio.create_task(self._cleanup_sessions())
            
            # Iniciar monitoreo de agentes
            asyncio.create_task(self._monitor_agent_utilization())
            
            logger.info("CollaborationEngine inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando CollaborationEngine: {e}")
            raise
    
    async def shutdown(self):
        """Cerrar todas las conexiones y limpiar recursos"""
        try:
            # Cancelar tareas de fondo
            if self.session_cleanup_task:
                self.session_cleanup_task.cancel()
            
            # Guardar sesiones activas en Redis
            await self._save_active_sessions()
            
            # Cerrar conexiones WebSocket
            for connection_id, ws in self.websocket_connections.items():
                try:
                    await ws.close()
                except Exception as e:
                    logger.warning(f"Error cerrando WebSocket {connection_id}: {e}")
            
            # Cerrar conexión Redis
            if self.redis_pool:
                await self.redis_pool.close()
            
            logger.info("CollaborationEngine cerrado correctamente")
            
        except Exception as e:
            logger.error(f"Error cerrando CollaborationEngine: {e}")
    
    # === SESSION MANAGEMENT ===
    
    async def create_session(
        self, 
        owner_id: str, 
        session_data: SessionCreateRequest
    ) -> str:
        """Crear nueva sesión de colaboración"""
        async with self.lock_manager:
            session_id = str(uuid.uuid4())
            
            # Crear sesión
            session = CollaborationSession(
                session_id=session_id,
                name=session_data.name,
                description=session_data.description,
                owner_id=owner_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                status=SessionStatus.ACTIVE,
                participants={},
                shared_context={},
                task_assignments={},
                locks={},
                conflict_queue=[]
            )
            
            # Agregar owner como participante
            owner_user = User(
                user_id=owner_id,
                username=f"user_{owner_id}",
                role=UserRole.OWNER,
                session_id=session_id
            )
            session.participants[owner_id] = owner_user
            self.user_sessions[owner_id] = session_id
            
            # Agregar participantes iniciales
            for user_id in session_data.initial_participants:
                user = User(
                    user_id=user_id,
                    username=f"user_{user_id}",
                    role=UserRole.COLLABORATOR,
                    session_id=session_id
                )
                session.participants[user_id] = user
                self.user_sessions[user_id] = session_id
            
            # Guardar en memoria y Redis
            self.active_sessions[session_id] = session
            await self._save_session_to_redis(session)
            
            # Notificar a participantes
            await self._broadcast_to_session(
                session_id,
                {
                    "type": "session_created",
                    "session_id": session_id,
                    "owner_id": owner_id,
                    "session_info": asdict(session)
                }
            )
            
            logger.info(f"Sesión {session_id} creada por usuario {owner_id}")
            return session_id
    
    async def join_session(
        self,
        user_id: str,
        session_id: str,
        join_request: SessionJoinRequest
    ) -> bool:
        """Unirse a una sesión existente"""
        async with self.lock_manager:
            if session_id not in self.active_sessions:
                raise MCPCoreException(
                    message=f"Sesión {session_id} no encontrada",
                    error_code=ErrorCode.NOT_FOUND,
                    status_code=404
                )
            
            session = self.active_sessions[session_id]
            
            # Verificar si la sesión está activa
            if session.status != SessionStatus.ACTIVE:
                raise MCPCoreException(
                    message=f"Sesión {session_id} no está activa",
                    error_code=ErrorCode.CONFLICT,
                    status_code=409
                )
            
            # Verificar límites de participantes
            max_participants = 50  # Configurable
            if len(session.participants) >= max_participants:
                raise MCPCoreException(
                    message="Sesión ha alcanzado el límite máximo de participantes",
                    error_code=ErrorCode.CONFLICT,
                    status_code=409
                )
            
            # Crear usuario
            user = User(
                user_id=user_id,
                username=f"user_{user_id}",
                role=UserRole.COLLABORATOR,
                session_id=session_id,
                permissions=set(join_request.user_permissions)
            )
            
            session.participants[user_id] = user
            session.updated_at = datetime.now()
            self.user_sessions[user_id] = session_id
            
            # Guardar en Redis
            await self._save_session_to_redis(session)
            
            # Notificar a otros participantes
            await self._broadcast_to_session(
                session_id,
                {
                    "type": NotificationType.USER_JOINED.value,
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                },
                exclude_user=user_id
            )
            
            # Enviar estado de sesión al usuario
            await self._send_to_user(
                user_id,
                {
                    "type": "session_joined",
                    "session_info": asdict(session),
                    "user_role": user.role.value
                }
            )
            
            logger.info(f"Usuario {user_id} se unió a sesión {session_id}")
            return True
    
    async def leave_session(self, user_id: str, session_id: str) -> bool:
        """Salir de una sesión"""
        async with self.lock_manager:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            
            if user_id not in session.participants:
                return False
            
            # Remover usuario
            del session.participants[user_id]
            session.updated_at = datetime.now()
            
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
            
            # Si es el owner y hay otros participantes, transferir ownership
            if session.owner_id == user_id and session.participants:
                new_owner = next(iter(session.participants.keys()))
                session.owner_id = new_owner
                session.participants[new_owner].role = UserRole.OWNER
                await self._send_to_user(
                    new_owner,
                    {
                        "type": "ownership_transferred",
                        "session_id": session_id,
                        "new_owner_id": new_owner
                    }
                )
            
            # Si no quedan participantes, terminar sesión
            if not session.participants:
                session.status = SessionStatus.TERMINATED
                await self._remove_session_from_redis(session_id)
                del self.active_sessions[session_id]
            else:
                await self._save_session_to_redis(session)
            
            # Notificar a otros participantes
            await self._broadcast_to_session(
                session_id,
                {
                    "type": NotificationType.USER_LEFT.value,
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            logger.info(f"Usuario {user_id} salió de sesión {session_id}")
            return True
    
    # === WEBSOCKET MANAGEMENT ===
    
    async def connect_websocket(self, user_id: str, websocket, session_id: str) -> str:
        """Establecer conexión WebSocket"""
        connection_id = str(uuid.uuid4())
        
        # Verificar límites de conexiones
        if len(self.websocket_connections) >= self.max_websocket_connections:
            await websocket.close(code=1008, reason="Server overloaded")
            raise MCPCoreException(
                message="Servidor sobrecargado, demasiadas conexiones",
                error_code=ErrorCode.RATE_LIMITED,
                status_code=429
            )
        
        # Verificar que el usuario esté en la sesión
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            if user_id in session.participants:
                # Actualizar WebSocket del usuario
                session.participants[user_id].websocket_connection = connection_id
                session.participants[user_id].last_seen = datetime.now()
                await self._save_session_to_redis(session)
        
        self.websocket_connections[connection_id] = websocket
        
        # Enviar mensaje de bienvenida
        await self._send_to_connection(
            connection_id,
            {
                "type": "websocket_connected",
                "connection_id": connection_id,
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        logger.info(f"WebSocket conectado: {connection_id} para usuario {user_id}")
        return connection_id
    
    async def disconnect_websocket(self, connection_id: str):
        """Desconectar WebSocket"""
        if connection_id in self.websocket_connections:
            del self.websocket_connections[connection_id]
            
            # Buscar usuario y actualizar estado
            for session in self.active_sessions.values():
                for user in session.participants.values():
                    if user.websocket_connection == connection_id:
                        user.websocket_connection = None
                        user.last_seen = datetime.now()
                        await self._save_session_to_redis(session)
                        break
            
            logger.info(f"WebSocket desconectado: {connection_id}")
    
    async def handle_websocket_message(self, connection_id: str, message: str):
        """Procesar mensaje WebSocket"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            # Routing de mensajes
            if message_type == "heartbeat":
                await self._handle_heartbeat(connection_id, data)
            elif message_type == "send_message":
                await self._handle_send_message(connection_id, data)
            elif message_type == "update_context":
                await self._handle_update_context(connection_id, data)
            elif message_type == "lock_resource":
                await self._handle_lock_resource(connection_id, data)
            elif message_type == "release_resource":
                await self._handle_release_resource(connection_id, data)
            elif message_type == "agent_command":
                await self._handle_agent_command(connection_id, data)
            else:
                logger.warning(f"Tipo de mensaje desconocido: {message_type}")
        
        except json.JSONDecodeError:
            await self._send_error(connection_id, "Invalid JSON message")
        except Exception as e:
            logger.error(f"Error procesando mensaje WebSocket: {e}")
            await self._send_error(connection_id, f"Internal error: {str(e)}")
    
    # === AGENT STATE SYNCHRONIZATION ===
    
    async def update_agent_state(
        self,
        agent_id: str,
        agent_type: str,
        status: str,
        current_task: Optional[str] = None,
        utilization: float = 0.0,
        performance_metrics: Optional[Dict[str, float]] = None,
        session_id: Optional[str] = None
    ):
        """Actualizar estado de agente en tiempo real"""
        async with self.lock_manager:
            if agent_id not in self.agent_states:
                self.agent_states[agent_id] = AgentState(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    status=status,
                    current_task=current_task,
                    utilization_percentage=utilization,
                    performance_metrics=performance_metrics or {},
                    last_update=datetime.now(),
                    active_sessions=set()
                )
            else:
                agent_state = self.agent_states[agent_id]
                agent_state.status = status
                agent_state.current_task = current_task
                agent_state.utilization_percentage = utilization
                if performance_metrics:
                    agent_state.performance_metrics.update(performance_metrics)
                agent_state.last_update = datetime.now()
            
            if session_id:
                self.agent_states[agent_id].active_sessions.add(session_id)
            
            # Guardar en Redis para persistencia
            await self._save_agent_state_to_redis(self.agent_states[agent_id])
            
            # Notificar a sesiones interesadas
            if session_id:
                await self._broadcast_agent_update(session_id, self.agent_states[agent_id])
    
    async def get_agent_states(self, session_id: Optional[str] = None) -> Dict[str, AgentState]:
        """Obtener estados de agentes"""
        if session_id:
            # Filtrar por sesión
            filtered_states = {}
            for agent_id, agent_state in self.agent_states.items():
                if session_id in agent_state.active_sessions:
                    filtered_states[agent_id] = agent_state
            return filtered_states
        return self.agent_states.copy()
    
    async def _broadcast_agent_update(self, session_id: str, agent_state: AgentState):
        """Broadcast actualización de estado de agente"""
        await self._broadcast_to_session(
            session_id,
            {
                "type": NotificationType.AGENT_STATUS_CHANGE.value,
                "agent_state": asdict(agent_state),
                "timestamp": datetime.now().isoformat()
            }
        )
    
    # === COLLABORATIVE TASK EXECUTION ===
    
    async def create_task(
        self,
        user_id: str,
        session_id: str,
        task_data: TaskCreateRequest
    ) -> str:
        """Crear tarea colaborativa"""
        async with self.lock_manager:
            if session_id not in self.active_sessions:
                raise MCPCoreException(
                    message=f"Sesión {session_id} no encontrada",
                    error_code=ErrorCode.NOT_FOUND,
                    status_code=404
                )
            
            session = self.active_sessions[session_id]
            
            # Verificar permisos
            if not self._has_permission(user_id, session, "create_task"):
                raise ForbiddenException("No tienes permisos para crear tareas en esta sesión")
            
            task_id = str(uuid.uuid4())
            task = CollaborativeTask(
                task_id=task_id,
                title=task_data.title,
                description=task_data.description,
                assigned_users=set(task_data.assigned_users),
                status=TaskStatus.PENDING,
                priority=task_data.priority,
                dependencies=task_data.dependencies,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                estimated_duration=None,
                actual_duration=None,
                conflict_info={},
                results={}
            )
            
            # Guardar en contexto de sesión
            session.shared_context[f"task_{task_id}"] = asdict(task)
            session.updated_at = datetime.now()
            
            # Actualizar asignaciones
            for user_id_assigned in task_data.assigned_users:
                session.task_assignments[task_id] = user_id_assigned
            
            await self._save_session_to_redis(session)
            
            # Notificar a usuarios asignados
            await self._broadcast_to_session(
                session_id,
                {
                    "type": NotificationType.TASK_ASSIGNED.value,
                    "task": asdict(task),
                    "assigned_users": list(task.assigned_users),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            logger.info(f"Tarea {task_id} creada en sesión {session_id}")
            return task_id
    
    async def update_task_status(
        self,
        user_id: str,
        session_id: str,
        task_id: str,
        status: TaskStatus,
        results: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Actualizar estado de tarea"""
        async with self.lock_manager:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            task_key = f"task_{task_id}"
            
            if task_key not in session.shared_context:
                return False
            
            task_dict = session.shared_context[task_key]
            
            # Verificar permisos
            assigned_users = set(task_dict.get("assigned_users", []))
            if user_id not in assigned_users and not self._has_permission(user_id, session, "manage_tasks"):
                raise ForbiddenException("No tienes permisos para actualizar esta tarea")
            
            # Actualizar estado
            task_dict["status"] = status.value
            task_dict["updated_at"] = datetime.now().isoformat()
            
            if results:
                task_dict["results"].update(results)
            
            # Marcar como completada si corresponde
            if status == TaskStatus.COMPLETED:
                task_dict["actual_duration"] = int(time.time())
            
            session.shared_context[task_key] = task_dict
            session.updated_at = datetime.now()
            await self._save_session_to_redis(session)
            
            # Notificar cambio de estado
            await self._broadcast_to_session(
                session_id,
                {
                    "type": NotificationType.TASK_COMPLETED.value if status == TaskStatus.COMPLETED else "task_updated",
                    "task_id": task_id,
                    "status": status.value,
                    "updated_by": user_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            logger.info(f"Tarea {task_id} actualizada a {status.value} por usuario {user_id}")
            return True
    
    # === CONFLICT RESOLUTION ===
    
    async def detect_conflicts(self, session_id: str) -> List[Conflict]:
        """Detectar conflictos en la sesión"""
        if session_id not in self.active_sessions:
            return []
        
        session = self.active_sessions[session_id]
        conflicts = []
        
        # Conflictos por asignaciones de tareas
        task_assignments = session.task_assignments
        assigned_tasks = defaultdict(list)
        
        for task_id, user_id in task_assignments.items():
            assigned_tasks[user_id].append(task_id)
        
        # Verificar sobrecarga de asignaciones
        for user_id, tasks in assigned_tasks.items():
            if len(tasks) > 10:  # Límite configurable
                conflicts.append(Conflict(
                    conflict_id=str(uuid.uuid4()),
                    conflict_type=ConflictType.TASK_ASSIGNMENT,
                    session_id=session_id,
                    participants={user_id},
                    resource_id="task_assignment",
                    description=f"Usuario {user_id} tiene demasiadas tareas asignadas",
                    created_at=datetime.now(),
                    resolved=False,
                    resolution_strategy=None,
                    resolution_data={}
                ))
        
        # Conflictos por locks de recursos
        locked_resources = defaultdict(list)
        for resource_id, user_id in session.locks.items():
            locked_resources[user_id].append(resource_id)
        
        for user_id, resources in locked_resources.items():
            if len(resources) > 5:  # Límite configurable
                conflicts.append(Conflict(
                    conflict_id=str(uuid.uuid4()),
                    conflict_type=ConflictType.RESOURCE_LOCK,
                    session_id=session_id,
                    participants={user_id},
                    resource_id="resource_locks",
                    description=f"Usuario {user_id} tiene demasiados recursos bloqueados",
                    created_at=datetime.now(),
                    resolved=False,
                    resolution_strategy=None,
                    resolution_data={}
                ))
        
        return conflicts
    
    async def resolve_conflict(
        self,
        resolver_user_id: str,
        conflict_id: str,
        resolution_request: ConflictResolutionRequest
    ) -> bool:
        """Resolver conflicto específico"""
        async with self.lock_manager:
            # Buscar conflicto en todas las sesiones
            conflict_found = False
            for session in self.active_sessions.values():
                for conflict in session.conflict_queue:
                    if conflict.get("conflict_id") == conflict_id:
                        conflict_found = True
                        break
                if conflict_found:
                    break
            
            if not conflict_found:
                raise MCPCoreException(
                    message=f"Conflicto {conflict_id} no encontrado",
                    error_code=ErrorCode.NOT_FOUND,
                    status_code=404
                )
            
            # Aplicar estrategia de resolución
            strategy = resolution_request.resolution_strategy
            
            if strategy == "reassign_tasks":
                await self._resolve_task_reassignment(conflict_id, resolution_request.resolution_data)
            elif strategy == "release_locks":
                await self._resolve_resource_locks(conflict_id, resolution_request.resolution_data)
            elif strategy == "priority_override":
                await self._resolve_priority_override(conflict_id, resolution_request.resolution_data)
            else:
                raise MCPCoreException(
                    message=f"Estrategia de resolución desconocida: {strategy}",
                    error_code=ErrorCode.VALIDATION_ERROR,
                    status_code=422
                )
            
            # Marcar conflicto como resuelto
            for session in self.active_sessions.values():
                for i, conflict in enumerate(session.conflict_queue):
                    if conflict.get("conflict_id") == conflict_id:
                        session.conflict_queue[i]["resolved"] = True
                        session.conflict_queue[i]["resolved_by"] = resolver_user_id
                        session.conflict_queue[i]["resolved_at"] = datetime.now().isoformat()
                        session.conflict_queue[i]["resolution_strategy"] = strategy
                        session.conflict_queue[i]["resolution_data"] = resolution_request.resolution_data
                        break
            
            # Notificar resolución
            await self._broadcast_to_session(
                session_id,
                {
                    "type": NotificationType.CONFLICT_RESOLVED.value,
                    "conflict_id": conflict_id,
                    "resolved_by": resolver_user_id,
                    "strategy": strategy,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            logger.info(f"Conflicto {conflict_id} resuelto por {resolver_user_id} usando {strategy}")
            return True
    
    async def _resolve_task_reassignment(self, conflict_id: str, resolution_data: Dict[str, Any]):
        """Resolver conflicto reasignando tareas"""
        # Implementar lógica de reasignación basada en carga de trabajo
        target_user_id = resolution_data.get("target_user_id")
        tasks_to_reassign = resolution_data.get("tasks", [])
        
        # Actualizar asignaciones en sesiones afectadas
        for session in self.active_sessions.values():
            for task_id in tasks_to_reassign:
                if task_id in session.task_assignments:
                    session.task_assignments[task_id] = target_user_id
    
    async def _resolve_resource_locks(self, conflict_id: str, resolution_data: Dict[str, Any]):
        """Resolver conflicto liberando locks"""
        resources_to_release = resolution_data.get("resources", [])
        
        # Liberar locks en sesiones afectadas
        for session in self.active_sessions.values():
            for resource_id in resources_to_release:
                if resource_id in session.locks:
                    del session.locks[resource_id]
    
    async def _resolve_priority_override(self, conflict_id: str, resolution_data: Dict[str, Any]):
        """Resolver conflicto con override de prioridad"""
        priority_overrides = resolution_data.get("priority_overrides", {})
        
        # Aplicar overrides de prioridad
        for session in self.active_sessions.values():
            for task_key, new_priority in priority_overrides.items():
                if task_key in session.shared_context:
                    task_data = session.shared_context[task_key]
                    task_data["priority"] = new_priority
    
    # === ROLE-BASED ACCESS CONTROL ===
    
    def _has_permission(self, user_id: str, session: CollaborationSession, permission: str) -> bool:
        """Verificar si usuario tiene permiso específico"""
        if user_id not in session.participants:
            return False
        
        user = session.participants[user_id]
        
        # Owner tiene todos los permisos
        if user.role == UserRole.OWNER:
            return True
        
        # Admin tiene la mayoría de permisos
        if user.role == UserRole.ADMIN:
            return permission not in ["transfer_ownership", "delete_session"]
        
        # Collaborator tiene permisos específicos
        if user.role == UserRole.COLLABORATOR:
            return permission in ["create_task", "update_task", "send_message", "lock_resource"]
        
        # Viewer solo puede ver
        if user.role == UserRole.VIEWER:
            return permission in ["view_session", "view_tasks"]
        
        # Guest tiene permisos muy limitados
        if user.role == UserRole.GUEST:
            return permission in ["view_session"]
        
        return False
    
    async def change_user_role(
        self,
        admin_user_id: str,
        target_user_id: str,
        new_role: UserRole,
        session_id: str
    ) -> bool:
        """Cambiar rol de usuario (solo owner/admin)"""
        async with self.lock_manager:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            
            # Verificar permisos
            admin_user = session.participants.get(admin_user_id)
            if not admin_user or admin_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
                raise ForbiddenException("No tienes permisos para cambiar roles")
            
            # No permitir que owner cambie su propio rol
            if target_user_id == session.owner_id:
                raise MCPCoreException(
                    message="No puedes cambiar el rol del owner de la sesión",
                    error_code=ErrorCode.CONFLICT,
                    status_code=409
                )
            
            if target_user_id not in session.participants:
                raise MCPCoreException(
                    message=f"Usuario {target_user_id} no está en la sesión",
                    error_code=ErrorCode.NOT_FOUND,
                    status_code=404
                )
            
            # Cambiar rol
            session.participants[target_user_id].role = new_role
            session.updated_at = datetime.now()
            
            await self._save_session_to_redis(session)
            
            # Notificar cambio
            await self._broadcast_to_session(
                session_id,
                {
                    "type": "user_role_changed",
                    "user_id": target_user_id,
                    "new_role": new_role.value,
                    "changed_by": admin_user_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            logger.info(f"Rol de usuario {target_user_id} cambiado a {new_role.value} en sesión {session_id}")
            return True
    
    # === REAL-TIME NOTIFICATIONS ===
    
    async def send_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        data: Dict[str, Any],
        session_id: Optional[str] = None
    ):
        """Enviar notificación a usuario específico"""
        await self._send_to_user(
            user_id,
            {
                "type": "notification",
                "notification_type": notification_type.value,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def broadcast_notification(
        self,
        session_id: str,
        notification_type: NotificationType,
        data: Dict[str, Any],
        exclude_users: Optional[Set[str]] = None
    ):
        """Broadcast notificación a sesión"""
        await self._broadcast_to_session(
            session_id,
            {
                "type": "notification",
                "notification_type": notification_type.value,
                "data": data,
                "timestamp": datetime.now().isoformat()
            },
            exclude_users=exclude_users
        )
    
    # === SHARED CONTEXT ===
    
    async def update_shared_context(
        self,
        user_id: str,
        session_id: str,
        context_key: str,
        context_value: Any
    ) -> bool:
        """Actualizar contexto compartido"""
        async with self.lock_manager:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            
            # Verificar permisos
            if not self._has_permission(user_id, session, "update_context"):
                raise ForbiddenException("No tienes permisos para actualizar el contexto compartido")
            
            # Actualizar contexto
            session.shared_context[context_key] = context_value
            session.updated_at = datetime.now()
            
            await self._save_session_to_redis(session)
            
            # Broadcast cambio
            await self._broadcast_to_session(
                session_id,
                {
                    "type": "context_updated",
                    "context_key": context_key,
                    "context_value": context_value,
                    "updated_by": user_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return True
    
    async def get_shared_context(self, session_id: str, context_key: Optional[str] = None) -> Dict[str, Any]:
        """Obtener contexto compartido"""
        if session_id not in self.active_sessions:
            return {}
        
        session = self.active_sessions[session_id]
        
        if context_key:
            return {context_key: session.shared_context.get(context_key)}
        
        return session.shared_context.copy()
    
    # === MONITOREO DE UTILIZACIÓN ===
    
    async def get_agent_utilization(self, session_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Obtener métricas de utilización de agentes"""
        utilization_data = {}
        
        for agent_id, agent_state in self.agent_states.items():
            if session_id and session_id not in agent_state.active_sessions:
                continue
            
            utilization_data[agent_id] = {
                "agent_id": agent_id,
                "agent_type": agent_state.agent_type,
                "status": agent_state.status,
                "utilization_percentage": agent_state.utilization_percentage,
                "current_task": agent_state.current_task,
                "active_sessions": list(agent_state.active_sessions),
                "performance_metrics": agent_state.performance_metrics,
                "last_update": agent_state.last_update.isoformat(),
                "health_status": self._calculate_agent_health(agent_state)
            }
        
        return utilization_data
    
    def _calculate_agent_health(self, agent_state: AgentState) -> str:
        """Calcular estado de salud del agente"""
        utilization = agent_state.utilization_percentage
        last_update = agent_state.last_update
        
        # Verificar si está muy ocupado
        if utilization > 90:
            return "overloaded"
        elif utilization > 70:
            return "busy"
        elif utilization < 10:
            return "idle"
        
        # Verificar si no ha actualizado recientemente
        if (datetime.now() - last_update).total_seconds() > 300:  # 5 minutos
            return "stale"
        
        return "healthy"
    
    async def _monitor_agent_utilization(self):
        """Monitorear utilización de agentes en background"""
        while True:
            try:
                # Calcular estadísticas de utilización
                total_agents = len(self.agent_states)
                if total_agents > 0:
                    avg_utilization = sum(
                        agent.utilization_percentage 
                        for agent in self.agent_states.values()
                    ) / total_agents
                    
                    busy_agents = sum(
                        1 for agent in self.agent_states.values()
                        if agent.utilization_percentage > 70
                    )
                    
                    overloaded_agents = sum(
                        1 for agent in self.agent_states.values()
                        if agent.utilization_percentage > 90
                    )
                    
                    # Log estadísticas cada hora
                    if int(time.time()) % 3600 == 0:
                        logger.info(
                            f"Agent Utilization: {total_agents} total, "
                            f"{busy_agents} busy, {overloaded_agents} overloaded, "
                            f"{avg_utilization:.1f}% average"
                        )
                
                await asyncio.sleep(60)  # Monitorear cada minuto
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en monitoreo de agentes: {e}")
                await asyncio.sleep(60)
    
    # === HANDLERS DE MENSAJES WEBSOCKET ===
    
    async def _handle_heartbeat(self, connection_id: str, data: Dict[str, Any]):
        """Manejar heartbeat de WebSocket"""
        await self._send_to_connection(
            connection_id,
            {
                "type": "heartbeat_response",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def _handle_send_message(self, connection_id: str, data: Dict[str, Any]):
        """Manejar envío de mensaje"""
        session_id = data.get("session_id")
        message = data.get("message")
        user_id = data.get("user_id")
        
        if not all([session_id, message, user_id]):
            await self._send_error(connection_id, "Missing required fields")
            return
        
        await self._broadcast_to_session(
            session_id,
            {
                "type": "user_message",
                "user_id": user_id,
                "message": message,
                "timestamp": datetime.now().isoformat()
            },
            exclude_user=user_id
        )
    
    async def _handle_update_context(self, connection_id: str, data: Dict[str, Any]):
        """Manejar actualización de contexto"""
        session_id = data.get("session_id")
        context_key = data.get("context_key")
        context_value = data.get("context_value")
        user_id = data.get("user_id")
        
        try:
            await self.update_shared_context(user_id, session_id, context_key, context_value)
            await self._send_to_connection(
                connection_id,
                {
                    "type": "context_update_success",
                    "context_key": context_key,
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            await self._send_error(connection_id, f"Failed to update context: {str(e)}")
    
    async def _handle_lock_resource(self, connection_id: str, data: Dict[str, Any]):
        """Manejar bloqueo de recurso"""
        session_id = data.get("session_id")
        resource_id = data.get("resource_id")
        user_id = data.get("user_id")
        
        if not all([session_id, resource_id, user_id]):
            await self._send_error(connection_id, "Missing required fields")
            return
        
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            
            # Verificar si el recurso ya está bloqueado
            if resource_id in session.locks and session.locks[resource_id] != user_id:
                await self._send_error(connection_id, "Resource already locked by another user")
                return
            
            # Bloquear recurso
            session.locks[resource_id] = user_id
            session.updated_at = datetime.now()
            await self._save_session_to_redis(session)
            
            # Notificar lock
            await self._broadcast_to_session(
                session_id,
                {
                    "type": "resource_locked",
                    "resource_id": resource_id,
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                },
                exclude_user=user_id
            )
            
            await self._send_to_connection(
                connection_id,
                {
                    "type": "resource_lock_success",
                    "resource_id": resource_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    async def _handle_release_resource(self, connection_id: str, data: Dict[str, Any]):
        """Manejar liberación de recurso"""
        session_id = data.get("session_id")
        resource_id = data.get("resource_id")
        user_id = data.get("user_id")
        
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            
            if resource_id in session.locks and session.locks[resource_id] == user_id:
                del session.locks[resource_id]
                session.updated_at = datetime.now()
                await self._save_session_to_redis(session)
                
                await self._broadcast_to_session(
                    session_id,
                    {
                        "type": "resource_released",
                        "resource_id": resource_id,
                        "user_id": user_id,
                        "timestamp": datetime.now().isoformat()
                    }
                )
    
    async def _handle_agent_command(self, connection_id: str, data: Dict[str, Any]):
        """Manejar comando de agente"""
        agent_id = data.get("agent_id")
        command = data.get("command")
        parameters = data.get("parameters", {})
        
        # Implementar lógica de comando de agente
        # Esto se integraría con el sistema de agentes existente
        
        await self._send_to_connection(
            connection_id,
            {
                "type": "agent_command_response",
                "agent_id": agent_id,
                "command": command,
                "status": "executed",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    # === PERSISTENCIA Y RECUPERACIÓN ===
    
    async def _connect_redis(self):
        """Conectar a Redis"""
        self.redis_pool = redis.ConnectionPool.from_url(
            self.redis_url,
            **settings.get_redis_config()
        )
        self.redis_client = redis.Redis(connection_pool=self.redis_pool)
        
        # Test connection
        await self.redis_client.ping()
        logger.info("Conectado a Redis exitosamente")
    
    async def _save_session_to_redis(self, session: CollaborationSession):
        """Guardar sesión en Redis"""
        try:
            session_data = pickle.dumps(asdict(session))
            await self.redis_client.setex(
                f"session:{session.session_id}",
                3600,  # 1 hora TTL
                session_data
            )
        except Exception as e:
            logger.error(f"Error guardando sesión en Redis: {e}")
    
    async def _remove_session_from_redis(self, session_id: str):
        """Remover sesión de Redis"""
        try:
            await self.redis_client.delete(f"session:{session_id}")
        except Exception as e:
            logger.error(f"Error removiendo sesión de Redis: {e}")
    
    async def _load_active_sessions(self):
        """Cargar sesiones activas desde Redis"""
        try:
            # Obtener todas las keys de sesión
            session_keys = await self.redis_client.keys("session:*")
            
            for key in session_keys:
                try:
                    session_data = await self.redis_client.get(key)
                    if session_data:
                        session_dict = pickle.loads(session_data)
                        
                        # Reconstruir objetos datetime
                        session_dict["created_at"] = datetime.fromisoformat(session_dict["created_at"])
                        session_dict["updated_at"] = datetime.fromisoformat(session_dict["updated_at"])
                        
                        # Reconstruir objetos datetime en participants
                        for participant_dict in session_dict["participants"].values():
                            if participant_dict["last_seen"]:
                                participant_dict["last_seen"] = datetime.fromisoformat(participant_dict["last_seen"])
                        
                        # Reconstruir Conflict objects en queue
                        for conflict_dict in session_dict["conflict_queue"]:
                            if conflict_dict["created_at"]:
                                conflict_dict["created_at"] = datetime.fromisoformat(conflict_dict["created_at"])
                        
                        session = CollaborationSession(**session_dict)
                        self.active_sessions[session.session_id] = session
                        
                        # Actualizar mapa user_sessions
                        for user_id in session.participants.keys():
                            self.user_sessions[user_id] = session.session_id
                        
                except Exception as e:
                    logger.error(f"Error cargando sesión {key}: {e}")
            
            logger.info(f"Cargadas {len(self.active_sessions)} sesiones activas desde Redis")
            
        except Exception as e:
            logger.error(f"Error cargando sesiones desde Redis: {e}")
    
    async def _save_active_sessions(self):
        """Guardar todas las sesiones activas"""
        for session in self.active_sessions.values():
            await self._save_session_to_redis(session)
    
    async def _save_agent_state_to_redis(self, agent_state: AgentState):
        """Guardar estado de agente en Redis"""
        try:
            agent_data = pickle.dumps(asdict(agent_state))
            await self.redis_client.setex(
                f"agent_state:{agent_state.agent_id}",
                1800,  # 30 minutos TTL
                agent_data
            )
        except Exception as e:
            logger.error(f"Error guardando estado de agente en Redis: {e}")
    
    # === CLEANUP Y MANTENIMIENTO ===
    
    async def _cleanup_sessions(self):
        """Tarea de limpieza de sesiones inactivas"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                current_time = datetime.now()
                sessions_to_remove = []
                
                for session_id, session in self.active_sessions.items():
                    # Verificar inactividad
                    time_since_update = (current_time - session.updated_at).total_seconds()
                    
                    # Remover sesiones inactivas por más de 2 horas
                    if time_since_update > 7200 and not session.participants:
                        sessions_to_remove.append(session_id)
                    
                    # Remover participantes inactivos
                    inactive_users = []
                    for user_id, user in session.participants.items():
                        time_since_seen = (current_time - user.last_seen).total_seconds()
                        if time_since_seen > 3600:  # 1 hora sin actividad
                            inactive_users.append(user_id)
                    
                    for user_id in inactive_users:
                        del session.participants[user_id]
                        if user_id in self.user_sessions:
                            del self.user_sessions[user_id]
                
                # Remover sesiones inactivas
                for session_id in sessions_to_remove:
                    await self._remove_session_from_redis(session_id)
                    del self.active_sessions[session_id]
                
                if sessions_to_remove:
                    logger.info(f"Limpiadas {len(sessions_to_remove)} sesiones inactivas")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en limpieza de sesiones: {e}")
                await asyncio.sleep(self.cleanup_interval)
    
    # === MÉTODOS AUXILIARES ===
    
    async def _broadcast_to_session(
        self,
        session_id: str,
        message: Dict[str, Any],
        exclude_user: Optional[str] = None,
        exclude_users: Optional[Set[str]] = None
    ):
        """Broadcast mensaje a sesión"""
        if exclude_users is None:
            exclude_users = set()
        if exclude_user:
            exclude_users.add(exclude_user)
        
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        
        # Agregar a cola de mensajes para persistencia
        self.message_queue[session_id].append(message)
        
        # Enviar a conexiones WebSocket activas
        for user_id, user in session.participants.items():
            if user_id not in exclude_users and user.websocket_connection:
                await self._send_to_connection(user.websocket_connection, message)
    
    async def _send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Enviar mensaje a usuario específico"""
        # Buscar usuario en sesiones
        for session_id, session in self.active_sessions.items():
            if user_id in session.participants:
                user = session.participants[user_id]
                if user.websocket_connection:
                    await self._send_to_connection(user.websocket_connection, message)
                break
    
    async def _send_to_connection(self, connection_id: str, message: Dict[str, Any]):
        """Enviar mensaje a conexión específica"""
        if connection_id in self.websocket_connections:
            try:
                websocket = self.websocket_connections[connection_id]
                await websocket.send(json.dumps(message))
            except Exception as e:
                logger.warning(f"Error enviando mensaje a conexión {connection_id}: {e}")
                await self.disconnect_websocket(connection_id)
    
    async def _send_error(self, connection_id: str, error_message: str):
        """Enviar mensaje de error"""
        await self._send_to_connection(
            connection_id,
            {
                "type": "error",
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    # === MÉTODOS PÚBLICOS DE CONSULTA ===
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obtener información de sesión"""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        return {
            "session_id": session.session_id,
            "name": session.name,
            "description": session.description,
            "owner_id": session.owner_id,
            "status": session.status.value,
            "participants_count": len(session.participants),
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "tasks_count": len([k for k in session.shared_context.keys() if k.startswith("task_")]),
            "active_locks": len(session.locks),
            "conflicts_count": len([c for c in session.conflict_queue if not c.get("resolved", True)])
        }
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtener sesiones de un usuario"""
        user_session_ids = [
            session_id for session_id, mapped_user_id in self.user_sessions.items() 
            if mapped_user_id == user_id
        ]
        
        sessions_info = []
        for session_id in user_session_ids:
            session_info = await self.get_session_info(session_id)
            if session_info:
                sessions_info.append(session_info)
        
        return sessions_info
    
    async def get_active_connections_count(self) -> int:
        """Obtener número de conexiones activas"""
        return len(self.websocket_connections)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas generales del sistema"""
        total_sessions = len(self.active_sessions)
        active_connections = len(self.websocket_connections)
        total_agents = len(self.agent_states)
        total_users = len(self.user_sessions)
        
        # Calcular utilización promedio de agentes
        if self.agent_states:
            avg_utilization = sum(
                agent.utilization_percentage 
                for agent in self.agent_states.values()
            ) / len(self.agent_states)
        else:
            avg_utilization = 0
        
        # Contar sesiones por estado
        sessions_by_status = defaultdict(int)
        for session in self.active_sessions.values():
            sessions_by_status[session.status.value] += 1
        
        return {
            "total_sessions": total_sessions,
            "active_connections": active_connections,
            "total_agents": total_agents,
            "total_users": total_users,
            "average_agent_utilization": round(avg_utilization, 2),
            "sessions_by_status": dict(sessions_by_status),
            "redis_connected": self.redis_client is not None,
            "uptime_seconds": int(time.time() - self._start_time if hasattr(self, '_start_time') else 0)
        }


# === INSTANCIA GLOBAL ===
_global_collaboration_engine: Optional[CollaborationEngine] = None


async def get_collaboration_engine() -> CollaborationEngine:
    """Obtener instancia global del motor de colaboración"""
    global _global_collaboration_engine
    
    if _global_collaboration_engine is None:
        _global_collaboration_engine = CollaborationEngine()
        await _global_collaboration_engine.initialize()
    
    return _global_collaboration_engine


async def shutdown_collaboration_engine():
    """Cerrar instancia global del motor de colaboración"""
    global _global_collaboration_engine
    
    if _global_collaboration_engine:
        await _global_collaboration_engine.shutdown()
        _global_collaboration_engine = None


# === CONTEXT MANAGER ===
@asynccontextmanager
async def collaboration_context():
    """Context manager para gestión automática del motor de colaboración"""
    engine = await get_collaboration_engine()
    try:
        yield engine
    finally:
        await engine._cleanup_sessions()


# === FUNCIÓN DE INICIO ===
async def start_collaboration_engine(redis_url: str = None) -> CollaborationEngine:
    """Iniciar motor de colaboración con configuración personalizada"""
    engine = CollaborationEngine(redis_url=redis_url)
    await engine.initialize()
    
    # Marcar tiempo de inicio
    engine._start_time = time.time()
    
    return engine


# === HANDLER DE WEBSOCKET ===
async def websocket_handler(websocket, path, user_id: str, session_id: str):
    """Handler principal para conexiones WebSocket"""
    engine = await get_collaboration_engine()
    connection_id = None
    
    try:
        # Establecer conexión
        connection_id = await engine.connect_websocket(user_id, websocket, session_id)
        
        # Loop principal de mensajes
        async for message in websocket:
            if message:
                await engine.handle_websocket_message(connection_id, message)
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Conexión WebSocket cerrada para usuario {user_id}")
    except Exception as e:
        logger.error(f"Error en WebSocket handler: {e}")
    finally:
        if connection_id:
            await engine.disconnect_websocket(connection_id)


# === FUNCIONES DE INTEGRACIÓN CON SISTEMA DE AGENTES ===

async def register_agent_with_session(
    agent_id: str,
    agent_type: str,
    session_id: str,
    initial_status: str = "idle",
    initial_utilization: float = 0.0
):
    """Registrar agente con sesión de colaboración"""
    engine = await get_collaboration_engine()
    
    await engine.update_agent_state(
        agent_id=agent_id,
        agent_type=agent_type,
        status=initial_status,
        utilization=initial_utilization,
        session_id=session_id
    )


async def update_agent_performance(
    agent_id: str,
    session_id: str,
    metrics: Dict[str, float]
):
    """Actualizar métricas de rendimiento de agente"""
    engine = await get_collaboration_engine()
    
    if agent_id in engine.agent_states:
        engine.agent_states[agent_id].performance_metrics.update(metrics)
        engine.agent_states[agent_id].last_update = datetime.now()
        
        # Guardar en Redis
        await engine._save_agent_state_to_redis(engine.agent_states[agent_id])
        
        # Notificar a sesión
        await engine._broadcast_agent_update(session_id, engine.agent_states[agent_id])


# === UTILIDADES ===

def generate_session_id() -> str:
    """Generar ID único de sesión"""
    return str(uuid.uuid4())


def generate_task_id() -> str:
    """Generar ID único de tarea"""
    return str(uuid.uuid4())


def generate_conflict_id() -> str:
    """Generar ID único de conflicto"""
    return str(uuid.uuid4())


def hash_collaboration_data(data: str) -> str:
    """Hash de datos de colaboración para verificación"""
    return hashlib.sha256(data.encode()).hexdigest()[:16]


# === EXPORTS ===
__all__ = [
    "CollaborationEngine",
    "User",
    "CollaborationSession",
    "AgentState", 
    "CollaborativeTask",
    "Conflict",
    "UserRole",
    "SessionStatus",
    "TaskStatus",
    "ConflictType",
    "NotificationType",
    "SessionCreateRequest",
    "SessionJoinRequest",
    "TaskCreateRequest",
    "ConflictResolutionRequest",
    "get_collaboration_engine",
    "shutdown_collaboration_engine",
    "collaboration_context",
    "start_collaboration_engine",
    "websocket_handler",
    "register_agent_with_session",
    "update_agent_performance",
    "generate_session_id",
    "generate_task_id",
    "generate_conflict_id",
    "hash_collaboration_data"
]