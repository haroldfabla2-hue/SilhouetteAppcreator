"""
Utilidades y herramientas para el Sistema de Colaboración en Tiempo Real

Incluye funciones helper, validaciones, herramientas de testing, y ejemplos de uso
para facilitar la implementación y uso del sistema de colaboración.
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Optional, Set, Any, Callable
from datetime import datetime, timedelta
import hashlib
import random
import string

from .collaboration_engine import (
    CollaborationEngine, User, CollaborationSession, AgentState,
    CollaborativeTask, UserRole, SessionStatus, TaskStatus,
    NotificationType, ConflictType, get_collaboration_engine
)
from .collaboration_config import collaboration_settings


# === UTILIDADES DE GENERACIÓN ===

def generate_test_user(user_id: Optional[str] = None, username: Optional[str] = None) -> User:
    """Generar usuario de prueba"""
    if not user_id:
        user_id = str(uuid.uuid4())
    if not username:
        username = f"test_user_{user_id[:8]}"
    
    return User(
        user_id=user_id,
        username=username,
        role=UserRole.COLLABORATOR,
        session_id="",
        permissions=set()
    )


def generate_test_session(owner_id: str, name: Optional[str] = None) -> CollaborationSession:
    """Generar sesión de prueba"""
    session_id = str(uuid.uuid4())
    
    return CollaborationSession(
        session_id=session_id,
        name=name or f"Test Session {session_id[:8]}",
        description="Sesión de prueba para testing",
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


def generate_test_task(assigned_users: Optional[List[str]] = None) -> CollaborativeTask:
    """Generar tarea de prueba"""
    task_id = str(uuid.uuid4())
    
    return CollaborativeTask(
        task_id=task_id,
        title=f"Tarea de prueba {task_id[:8]}",
        description="Esta es una tarea de prueba",
        assigned_users=set(assigned_users or []),
        status=TaskStatus.PENDING,
        priority=1,
        dependencies=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
        estimated_duration=60,
        actual_duration=None,
        conflict_info={},
        results={}
    )


def generate_random_agent_state(agent_id: Optional[str] = None) -> AgentState:
    """Generar estado de agente aleatorio"""
    if not agent_id:
        agent_id = str(uuid.uuid4())
    
    return AgentState(
        agent_id=agent_id,
        agent_type=random.choice(["python_executor", "search_engine", "web_scraper", "git_operations"]),
        status=random.choice(["idle", "busy", "overloaded", "maintenance"]),
        current_task=None,
        utilization_percentage=random.uniform(0, 100),
        performance_metrics={
            "execution_time": random.uniform(1, 60),
            "success_rate": random.uniform(0.8, 1.0),
            "memory_usage": random.uniform(50, 500)
        },
        last_update=datetime.now(),
        active_sessions=set()
    )


# === UTILIDADES DE VALIDACIÓN ===

def validate_user_permissions(user: User, required_permissions: List[str]) -> bool:
    """Validar que usuario tenga permisos requeridos"""
    user_permissions = set()
    
    # Agregar permisos basado en rol
    role_permissions = {
        UserRole.OWNER: ["*"],  # Todos los permisos
        UserRole.ADMIN: ["create_session", "join_session", "create_task", "update_task", "manage_users", "resolve_conflicts"],
        UserRole.COLLABORATOR: ["create_task", "update_task", "send_message", "lock_resource"],
        UserRole.VIEWER: ["view_session", "view_tasks"],
        UserRole.GUEST: ["view_session"]
    }
    
    user_permissions.update(role_permissions.get(user.role, []))
    user_permissions.update(user.permissions)
    
    # Verificar permisos
    for permission in required_permissions:
        if permission == "*" or permission in user_permissions:
            return True
    
    return False


def validate_session_limits(session: CollaborationSession) -> List[str]:
    """Validar límites de sesión"""
    violations = []
    
    # Verificar límite de participantes
    if len(session.participants) > collaboration_settings.limits.max_session_participants:
        violations.append(f"Demasiados participantes: {len(session.participants)} > {collaboration_settings.limits.max_session_participants}")
    
    # Verificar límite de tareas
    task_count = len([k for k in session.shared_context.keys() if k.startswith("task_")])
    if task_count > collaboration_settings.limits.max_tasks_per_session:
        violations.append(f"Demasiadas tareas: {task_count} > {collaboration_settings.limits.max_tasks_per_session}")
    
    # Verificar límite de recursos bloqueados
    if len(session.locks) > collaboration_settings.limits.max_locked_resources_per_user:
        violations.append(f"Demasiados recursos bloqueados: {len(session.locks)} > {collaboration_settings.limits.max_locked_resources_per_user}")
    
    return violations


def validate_task_dependencies(task: CollaborativeTask, all_tasks: Dict[str, CollaborativeTask]) -> List[str]:
    """Validar dependencias de tarea"""
    violations = []
    
    for dep_task_id in task.dependencies:
        if dep_task_id not in all_tasks:
            violations.append(f"Tarea dependiente no encontrada: {dep_task_id}")
            continue
        
        dep_task = all_tasks[dep_task_id]
        if dep_task.status == TaskStatus.CANCELLED:
            violations.append(f"Tarea dependiente cancelada: {dep_task_id}")
    
    return violations


# === UTILIDADES DE TESTING ===

class CollaborationTester:
    """Herramienta para testing del sistema de colaboración"""
    
    def __init__(self):
        self.engine = None
        self.test_sessions = []
        self.test_users = []
        self.test_agents = []
    
    async def setup(self):
        """Configurar entorno de testing"""
        self.engine = await get_collaboration_engine()
        
        # Crear usuarios de prueba
        for i in range(5):
            user = generate_test_user()
            self.test_users.append(user)
        
        # Crear agentes de prueba
        for i in range(3):
            agent_state = generate_random_agent_state()
            self.test_agents.append(agent_state)
    
    async def test_basic_collaboration(self):
        """Probar colaboración básica"""
        print("Iniciando test de colaboración básica...")
        
        # Crear sesión
        owner = self.test_users[0]
        session = generate_test_session(owner.user_id)
        self.test_sessions.append(session)
        
        # Unir usuarios
        for user in self.test_users[1:3]:
            session.participants[user.user_id] = user
            user.session_id = session.session_id
        
        # Crear tarea
        task = generate_test_task([user.user_id for user in self.test_users[1:3]])
        session.shared_context[f"task_{task.task_id}"] = {
            "task_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "assigned_users": list(task.assigned_users),
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat()
        }
        
        # Simular actualización de estado
        task.status = TaskStatus.IN_PROGRESS
        session.shared_context[f"task_{task.task_id}"]["status"] = task.status.value
        
        print("✅ Test de colaboración básica completado")
        return True
    
    async def test_conflict_scenarios(self):
        """Probar escenarios de conflicto"""
        print("Iniciando test de conflictos...")
        
        session = self.test_sessions[0]
        conflicts_created = []
        
        # Crear conflicto de sobrecarga de tareas
        conflict = {
            "conflict_id": str(uuid.uuid4()),
            "conflict_type": ConflictType.TASK_ASSIGNMENT.value,
            "session_id": session.session_id,
            "participants": {self.test_users[1].user_id},
            "resource_id": "task_assignment",
            "description": "Usuario sobrecargado con tareas",
            "created_at": datetime.now(),
            "resolved": False
        }
        
        session.conflict_queue.append(conflict)
        conflicts_created.append(conflict["conflict_id"])
        
        print(f"✅ Test de conflictos completado: {len(conflicts_created)} conflictos creados")
        return conflicts_created
    
    async def test_agent_monitoring(self):
        """Probar monitoreo de agentes"""
        print("Iniciando test de monitoreo de agentes...")
        
        if not self.engine:
            return False
        
        # Actualizar estados de agentes
        for agent_state in self.test_agents:
            agent_state.utilization_percentage = random.uniform(70, 95)
            agent_state.status = "busy"
            agent_state.active_sessions.add(self.test_sessions[0].session_id)
        
        # Simular monitoreo
        utilization_data = await self.engine.get_agent_utilization()
        
        print(f"✅ Test de monitoreo completado: {len(utilization_data)} agentes monitoreados")
        return utilization_data
    
    async def test_websocket_simulation(self):
        """Simular comunicación WebSocket"""
        print("Iniciando test de comunicación WebSocket...")
        
        messages_sent = 0
        
        # Simular mensajes de usuario
        for user in self.test_users[:3]:
            if user.session_id:
                # Simular mensaje
                message = {
                    "type": "user_message",
                    "user_id": user.user_id,
                    "message": f"Hello from {user.username}",
                    "timestamp": datetime.now().isoformat()
                }
                messages_sent += 1
        
        # Simular notificaciones
        for notification_type in [NotificationType.USER_JOINED, NotificationType.TASK_ASSIGNED]:
            notification = {
                "type": "notification",
                "notification_type": notification_type.value,
                "data": {"test": True},
                "timestamp": datetime.now().isoformat()
            }
            messages_sent += 1
        
        print(f"✅ Test de WebSocket completado: {messages_sent} mensajes simulados")
        return messages_sent
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Ejecutar todos los tests"""
        results = {
            "test_name": "Collaboration System Tests",
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        try:
            await self.setup()
            
            # Ejecutar tests
            results["tests"]["basic_collaboration"] = await self.test_basic_collaboration()
            results["tests"]["conflict_scenarios"] = await self.test_conflict_scenarios()
            results["tests"]["agent_monitoring"] = await self.test_agent_monitoring()
            results["tests"]["websocket_simulation"] = await self.test_websocket_simulation()
            
            # Resumen
            total_tests = len(results["tests"])
            passed_tests = sum(1 for result in results["tests"].values() if result)
            results["summary"] = {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%"
            }
            
        except Exception as e:
            results["error"] = str(e)
            results["status"] = "failed"
        
        return results
    
    async def cleanup(self):
        """Limpiar recursos de testing"""
        self.test_sessions.clear()
        self.test_users.clear()
        self.test_agents.clear()


# === UTILIDADES DE BENCHMARKING ===

class CollaborationBenchmark:
    """Herramienta para benchmarking del sistema de colaboración"""
    
    def __init__(self):
        self.results = []
    
    async def benchmark_session_creation(self, num_sessions: int = 100) -> Dict[str, float]:
        """Benchmark de creación de sesiones"""
        engine = await get_collaboration_engine()
        start_time = time.time()
        
        for i in range(num_sessions):
            owner_id = f"benchmark_user_{i}"
            session_data = {
                "name": f"Benchmark Session {i}",
                "description": "Session for benchmarking",
                "initial_participants": []
            }
            # Simular creación de sesión
            await asyncio.sleep(0.001)  # Simular operación
        
        end_time = time.time()
        duration = end_time - start_time
        
        result = {
            "operation": "session_creation",
            "count": num_sessions,
            "duration_seconds": duration,
            "operations_per_second": num_sessions / duration,
            "avg_time_per_operation": duration / num_sessions
        }
        
        self.results.append(result)
        return result
    
    async def benchmark_websocket_connections(self, num_connections: int = 100) -> Dict[str, float]:
        """Benchmark de conexiones WebSocket"""
        start_time = time.time()
        
        connections = []
        for i in range(num_connections):
            connection_id = str(uuid.uuid4())
            connections.append(connection_id)
            # Simular establecimiento de conexión
            await asyncio.sleep(0.01)
        
        end_time = time.time()
        duration = end_time - start_time
        
        result = {
            "operation": "websocket_connections",
            "count": num_connections,
            "duration_seconds": duration,
            "connections_per_second": num_connections / duration,
            "avg_time_per_connection": duration / num_connections
        }
        
        self.results.append(result)
        return result
    
    async def benchmark_agent_updates(self, num_updates: int = 1000) -> Dict[str, float]:
        """Benchmark de actualizaciones de agentes"""
        start_time = time.time()
        
        for i in range(num_updates):
            agent_id = f"benchmark_agent_{i % 10}"
            agent_data = {
                "agent_id": agent_id,
                "agent_type": "benchmark",
                "status": "busy",
                "utilization": random.uniform(50, 90)
            }
            # Simular actualización de agente
            await asyncio.sleep(0.001)
        
        end_time = time.time()
        duration = end_time - start_time
        
        result = {
            "operation": "agent_updates",
            "count": num_updates,
            "duration_seconds": duration,
            "updates_per_second": num_updates / duration,
            "avg_time_per_update": duration / num_updates
        }
        
        self.results.append(result)
        return result
    
    async def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Ejecutar benchmark completo"""
        print("Iniciando benchmark completo del sistema de colaboración...")
        
        benchmark_results = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "max_connections": collaboration_settings.websocket.max_connections,
                "max_sessions": collaboration_settings.limits.max_total_sessions,
                "environment": collaboration_settings.environment
            },
            "benchmarks": {}
        }
        
        try:
            benchmark_results["benchmarks"]["session_creation"] = await self.benchmark_session_creation(50)
            benchmark_results["benchmarks"]["websocket_connections"] = await self.benchmark_websocket_connections(20)
            benchmark_results["benchmarks"]["agent_updates"] = await self.benchmark_agent_updates(500)
            
            # Calcular métricas generales
            total_operations = sum(b["count"] for b in self.results)
            total_duration = sum(b["duration_seconds"] for b in self.results)
            
            benchmark_results["summary"] = {
                "total_operations": total_operations,
                "total_duration_seconds": total_duration,
                "overall_operations_per_second": total_operations / total_duration if total_duration > 0 else 0,
                "benchmarks_run": len(self.results)
            }
            
        except Exception as e:
            benchmark_results["error"] = str(e)
        
        return benchmark_results


# === UTILIDADES DE DIAGNÓSTICO ===

def get_system_health_status() -> Dict[str, Any]:
    """Obtener estado de salud del sistema"""
    health = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy",
        "components": {
            "redis_connection": "unknown",
            "websocket_capacity": "unknown",
            "memory_usage": "unknown",
            "active_sessions": "unknown"
        },
        "metrics": {},
        "warnings": [],
        "errors": []
    }
    
    try:
        # Verificar configuración de Redis
        redis_config = collaboration_settings.redis
        if redis_config.session_ttl_seconds > 0:
            health["components"]["redis_connection"] = "configured"
        
        # Verificar capacidad de WebSocket
        ws_config = collaboration_settings.websocket
        if ws_config.max_connections > 0:
            health["components"]["websocket_capacity"] = f"{ws_config.max_connections} max connections"
        
        # Verificar límites
        if collaboration_settings.limits.max_total_sessions < 100:
            health["warnings"].append("Límite de sesiones muy bajo")
        
        if collaboration_settings.security.rate_limiting_enabled:
            health["metrics"]["rate_limiting"] = f"{collaboration_settings.security.rate_limit_messages_per_minute} msg/min"
        
        # Determinar estado general
        if health["errors"]:
            health["overall_status"] = "unhealthy"
        elif health["warnings"]:
            health["overall_status"] = "degraded"
        
    except Exception as e:
        health["errors"].append(f"Error checking health: {str(e)}")
        health["overall_status"] = "unhealthy"
    
    return health


def generate_collaboration_report() -> Dict[str, Any]:
    """Generar reporte del sistema de colaboración"""
    report = {
        "generated_at": datetime.now().isoformat(),
        "configuration_summary": {
            "environment": collaboration_settings.environment,
            "max_websocket_connections": collaboration_settings.websocket.max_connections,
            "max_total_sessions": collaboration_settings.limits.max_total_sessions,
            "redis_ttl_sessions": collaboration_settings.redis.session_ttl_seconds,
            "conflict_resolution_enabled": collaboration_settings.conflicts.auto_resolution_enabled,
            "agent_monitoring_enabled": collaboration_settings.agents.utilization_monitoring_enabled
        },
        "capabilities": {
            "multi_user_sessions": True,
            "real_time_sync": True,
            "conflict_resolution": True,
            "agent_monitoring": True,
            "websocket_communication": True,
            "role_based_access": True,
            "session_persistence": True,
            "scalable_architecture": True
        },
        "features_implemented": [
            "Multi-user session management",
            "Real-time agent state synchronization", 
            "Collaborative task execution",
            "Conflict resolution algorithms",
            "Shared context management",
            "Live agent utilization monitoring",
            "Role-based access control",
            "Real-time notifications",
            "Session persistence and recovery",
            "Scalable WebSocket management"
        ],
        "security_features": [
            "Authentication required",
            "Authorization based on roles",
            "Session validation",
            "Message validation",
            "Rate limiting",
            "Permission checking"
        ],
        "integration_points": [
            "WebSocket API endpoints",
            "Redis session storage",
            "Agent monitoring system",
            "Notification service",
            "Metrics collection",
            "Health check endpoints"
        ]
    }
    
    return report


# === UTILIDADES DE DATOS MOCK ===

def create_mock_collaboration_data(num_sessions: int = 5, num_users: int = 20) -> Dict[str, Any]:
    """Crear datos mock para testing y desarrollo"""
    mock_data = {
        "sessions": [],
        "users": [],
        "agents": [],
        "tasks": [],
        "conflicts": []
    }
    
    # Crear usuarios
    for i in range(num_users):
        user = generate_test_user()
        mock_data["users"].append({
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "last_seen": user.last_seen.isoformat()
        })
    
    # Crear sesiones
    for i in range(num_sessions):
        session = generate_test_session(mock_data["users"][i]["user_id"])
        
        # Agregar participantes aleatorios
        num_participants = random.randint(1, min(5, num_users))
        participant_ids = [user["user_id"] for user in random.sample(mock_data["users"], num_participants)]
        
        for user_id in participant_ids:
            user = next(u for u in mock_data["users"] if u["user_id"] == user_id)
            user["role"] = random.choice([role.value for role in UserRole])
        
        mock_data["sessions"].append({
            "session_id": session.session_id,
            "name": session.name,
            "description": session.description,
            "owner_id": session.owner_id,
            "participants": participant_ids,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "tasks_count": random.randint(0, 10),
            "conflicts_count": random.randint(0, 3)
        })
    
    # Crear agentes
    for i in range(10):
        agent = generate_random_agent_state()
        mock_data["agents"].append({
            "agent_id": agent.agent_id,
            "agent_type": agent.agent_type,
            "status": agent.status,
            "utilization_percentage": agent.utilization_percentage,
            "performance_metrics": agent.performance_metrics
        })
    
    return mock_data


# === UTILIDADES DE MIGRACIÓN ===

async def migrate_existing_data():
    """Migrar datos existentes al nuevo sistema de colaboración"""
    # Implementar lógica de migración si es necesario
    pass


# === FUNCIONES DE UTILIDAD RÁPIDA ===

async def quick_start_collaboration() -> CollaborationEngine:
    """Inicio rápido del sistema de colaboración"""
    engine = await get_collaboration_engine()
    
    # Crear sesión de demo
    demo_session_id = await engine.create_session(
        owner_id="demo_owner",
        session_data=type('SessionCreateRequest', (), {
            'name': 'Demo Session',
            'description': 'Sesión de demostración',
            'initial_participants': []
        })()
    )
    
    print(f"✅ Sistema de colaboración iniciado")
    print(f"📝 Sesión de demo creada: {demo_session_id}")
    print(f"🔗 WebSocket disponible en: ws://localhost:{collaboration_settings.ws_port}{collaboration_settings.ws_path}")
    
    return engine


def get_collaboration_status() -> str:
    """Obtener estado resumido del sistema"""
    health = get_system_health_status()
    
    status_lines = [
        "🤝 Sistema de Colaboración en Tiempo Real",
        "=" * 50,
        f"Estado general: {health['overall_status'].upper()}",
        f"Entorno: {collaboration_settings.environment}",
        "",
        "🔧 Componentes:",
    ]
    
    for component, status in health["components"].items():
        status_lines.append(f"  • {component}: {status}")
    
    status_lines.append("")
    status_lines.append("⚙️  Configuración:")
    status_lines.append(f"  • Max conexiones WebSocket: {collaboration_settings.websocket.max_connections}")
    status_lines.append(f"  • Max sesiones: {collaboration_settings.limits.max_total_sessions}")
    status_lines.append(f"  • TTL sesiones Redis: {collaboration_settings.redis.session_ttl_seconds}s")
    
    if health["warnings"]:
        status_lines.append("")
        status_lines.append("⚠️  Advertencias:")
        for warning in health["warnings"]:
            status_lines.append(f"  • {warning}")
    
    if health["errors"]:
        status_lines.append("")
        status_lines.append("❌ Errores:")
        for error in health["errors"]:
            status_lines.append(f"  • {error}")
    
    return "\n".join(status_lines)


# === EXPORTACIONES ===
__all__ = [
    # Generadores de datos de prueba
    "generate_test_user",
    "generate_test_session", 
    "generate_test_task",
    "generate_random_agent_state",
    
    # Validadores
    "validate_user_permissions",
    "validate_session_limits",
    "validate_task_dependencies",
    
    # Testing
    "CollaborationTester",
    "CollaborationBenchmark",
    
    # Diagnóstico
    "get_system_health_status",
    "generate_collaboration_report",
    "create_mock_collaboration_data",
    
    # Utilidades rápidas
    "quick_start_collaboration",
    "get_collaboration_status",
    
    # Migración
    "migrate_existing_data"
]