#!/usr/bin/env python3
"""
Ejemplo completo de uso del Sistema de Colaboración en Tiempo Real

Este ejemplo demuestra todas las funcionalidades principales del sistema:
- Creación y gestión de sesiones multi-usuario
- Comunicación en tiempo real via WebSockets
- Colaboración en tareas con resolución de conflictos
- Monitoreo de agentes en tiempo real
- Sistema de notificaciones
- Control de acceso basado en roles
"""

import asyncio
import json
import sys
import os
from typing import Dict, List, Any
from datetime import datetime
import logging

# Agregar src al path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.collaboration_engine import (
    CollaborationEngine,
    get_collaboration_engine,
    start_collaboration_engine,
    websocket_handler,
    UserRole,
    SessionStatus,
    TaskStatus,
    NotificationType
)
from src.core.collaboration_config import collaboration_settings
from src.core.collaboration_utils import (
    CollaborationTester,
    CollaborationBenchmark,
    quick_start_collaboration,
    get_collaboration_status,
    create_mock_collaboration_data
)


# === CONFIGURACIÓN DE LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# === EJEMPLO DE USUARIOS ===
class MockUsers:
    """Mock users para el ejemplo"""
    
    def __init__(self):
        self.users = {
            "alice": {"id": "alice", "name": "Alice Johnson", "role": UserRole.OWNER},
            "bob": {"id": "bob", "name": "Bob Smith", "role": UserRole.ADMIN},
            "charlie": {"id": "charlie", "name": "Charlie Brown", "role": UserRole.COLLABORATOR},
            "diana": {"id": "diana", "name": "Diana Prince", "role": UserRole.COLLABORATOR},
            "guest": {"id": "guest", "name": "Guest User", "role": UserRole.GUEST}
        }
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        return self.users.get(user_id, self.users["guest"])


# === EJEMPLO DE AGENTES ===
class MockAgents:
    """Mock agents para el ejemplo"""
    
    def __init__(self):
        self.agents = {
            "python_agent": {"type": "python_executor", "status": "idle"},
            "search_agent": {"type": "search_engine", "status": "busy"},
            "scraper_agent": {"type": "web_scraper", "status": "idle"},
            "git_agent": {"type": "git_operations", "status": "maintenance"}
        }


# === EJEMPLO DE WEBSOCKET CLIENTE ===
class MockWebSocketClient:
    """Mock WebSocket cliente para simular comunicación"""
    
    def __init__(self, user_id: str, session_id: str, engine: CollaborationEngine):
        self.user_id = user_id
        self.session_id = session_id
        self.engine = engine
        self.connection_id = None
        self.messages_sent = []
        self.messages_received = []
    
    async def connect(self):
        """Simular conexión WebSocket"""
        print(f"🔗 Conectando usuario {self.user_id} a sesión {self.session_id}")
        
        # Simular handshake de WebSocket
        self.connection_id = str(hash(self.user_id))[:8]
        
        # Notificar al motor de colaboración
        await self.engine.connect_websocket(
            self.user_id,
            self,  # Mock WebSocket
            self.session_id
        )
        
        print(f"✅ Usuario {self.user_id} conectado exitosamente")
    
    async def disconnect(self):
        """Simular desconexión"""
        if self.connection_id:
            await self.engine.disconnect_websocket(self.connection_id)
            print(f"👋 Usuario {self.user_id} desconectado")
    
    async def send(self, message: str):
        """Enviar mensaje (simula WebSocket.send)"""
        try:
            data = json.loads(message)
            self.messages_sent.append(data)
            
            print(f"📤 {self.user_id} envió: {data.get('type', 'unknown')}")
            
            # Procesar mensaje en el motor
            if self.connection_id:
                await self.engine.handle_websocket_message(self.connection_id, message)
                
        except json.JSONDecodeError:
            print(f"❌ Error: Mensaje JSON inválido de {self.user_id}")
    
    async def recv(self, message: str):
        """Recibir mensaje (simula WebSocket.recv)"""
        try:
            data = json.loads(message)
            self.messages_received.append(data)
            
            print(f"📥 {self.user_id} recibió: {data.get('type', 'unknown')}")
            
        except json.JSONDecodeError:
            print(f"❌ Error: Mensaje JSON inválido recibido por {self.user_id}")
    
    # Mock WebSocket interface
    def send_sync(self, message: str):
        """Sincrónico para compatibilidad"""
        asyncio.create_task(self.send(message))
    
    def close(self):
        """Cerrar conexión"""
        asyncio.create_task(self.disconnect())


# === EJEMPLO PRINCIPAL ===
class CollaborationExample:
    """Ejemplo principal del sistema de colaboración"""
    
    def __init__(self):
        self.engine = None
        self.users = MockUsers()
        self.agents = MockAgents()
        self.clients = {}
        self.session_id = None
    
    async def setup(self):
        """Configurar ejemplo"""
        print("🚀 Configurando Sistema de Colaboración en Tiempo Real")
        print("=" * 60)
        
        # Inicializar motor de colaboración
        self.engine = await start_collaboration_engine()
        
        # Mostrar estado del sistema
        status = get_collaboration_status()
        print(status)
        print()
        
        # Crear sesión de ejemplo
        await self.create_example_session()
        
        # Configurar agentes
        await self.setup_agents()
    
    async def create_example_session(self):
        """Crear sesión de ejemplo"""
        print("📝 Creando sesión de colaboración de ejemplo...")
        
        session_data = type('SessionCreateRequest', (), {
            'name': 'Proyecto de Desarrollo Multi-Agente',
            'description': 'Colaboración en tiempo real para desarrollo de sistema multi-agente',
            'initial_participants': ['bob', 'charlie', 'diana']
        })()
        
        self.session_id = await self.engine.create_session('alice', session_data)
        print(f"✅ Sesión creada: {self.session_id}")
        
        # Unir otros usuarios
        for user_id in ['bob', 'charlie', 'diana']:
            await self.join_user_to_session(user_id)
        
        print()
    
    async def join_user_to_session(self, user_id: str):
        """Unir usuario a la sesión"""
        user_info = self.users.get_user(user_id)
        
        join_request = type('SessionJoinRequest', (), {
            'session_id': self.session_id,
            'user_permissions': ['create_task', 'update_task'] if user_info['role'] == UserRole.COLLABORATOR else []
        })()
        
        await self.engine.join_session(user_id, self.session_id, join_request)
        print(f"👤 Usuario {user_info['name']} se unió a la sesión")
    
    async def setup_agents(self):
        """Configurar agentes en el sistema"""
        print("🤖 Configurando agentes del sistema...")
        
        for agent_id, agent_info in self.agents.agents.items():
            await self.engine.update_agent_state(
                agent_id=agent_id,
                agent_type=agent_info['type'],
                status=agent_info['status'],
                utilization=30.0 if agent_info['status'] == 'idle' else 75.0,
                session_id=self.session_id
            )
        
        print("✅ Agentes configurados y registrados")
        print()
    
    async def demonstrate_basic_collaboration(self):
        """Demostrar colaboración básica"""
        print("🎯 Demostrando Colaboración Básica")
        print("-" * 40)
        
        # Conectar usuarios via WebSocket
        for user_id in ['alice', 'bob', 'charlie', 'diana']:
            await self.connect_user(user_id)
        
        # Simular comunicación
        await asyncio.sleep(1)
        
        # Enviar mensajes de chat
        await self.simulate_chat_messages()
        
        print("✅ Demostración de colaboración básica completada\n")
    
    async def connect_user(self, user_id: str):
        """Conectar usuario via WebSocket"""
        user_info = self.users.get_user(user_id)
        
        # Crear cliente mock
        client = MockWebSocketClient(user_id, self.session_id, self.engine)
        self.clients[user_id] = client
        
        await client.connect()
    
    async def simulate_chat_messages(self):
        """Simular mensajes de chat entre usuarios"""
        messages = [
            ("alice", "¡Hola equipo! Empecemos con el desarrollo del sistema."),
            ("bob", "Perfecto, Alice. ¿Por dónde comenzamos?"),
            ("charlie", "Creo que deberíamos empezar con el motor de colaboración."),
            ("diana", "Excelente idea. Yo puedo trabajar en la interfaz de usuario."),
            ("alice", "Genial. Charlie, el motor de colaboración es prioritario."),
        ]
        
        for user_id, message in messages:
            if user_id in self.clients:
                await self.clients[user_id].send(json.dumps({
                    "type": "send_message",
                    "session_id": self.session_id,
                    "user_id": user_id,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }))
                await asyncio.sleep(0.5)
    
    async def demonstrate_task_collaboration(self):
        """Demostrar colaboración en tareas"""
        print("📋 Demostrando Colaboración en Tareas")
        print("-" * 40)
        
        # Crear tareas colaborativas
        tasks = [
            {
                "title": "Implementar motor de colaboración",
                "description": "Desarrollar el núcleo del sistema de colaboración en tiempo real",
                "assigned_users": ["charlie"],
                "priority": 5
            },
            {
                "title": "Diseñar interfaz de usuario",
                "description": "Crear UI para gestión de sesiones y tareas colaborativas",
                "assigned_users": ["diana"],
                "priority": 4
            },
            {
                "title": "Configurar base de datos",
                "description": "Setup de Redis y PostgreSQL para el sistema",
                "assigned_users": ["bob"],
                "priority": 3
            }
        ]
        
        task_ids = []
        for i, task_data in enumerate(tasks):
            task_request = type('TaskCreateRequest', (), task_data)()
            task_id = await self.engine.create_task('alice', self.session_id, task_request)
            task_ids.append(task_id)
            print(f"📝 Tarea creada: {task_data['title']} (ID: {task_id[:8]})")
        
        print()
        
        # Simular actualizaciones de estado de tareas
        await asyncio.sleep(2)
        
        # Charlie empieza con su tarea
        await self.engine.update_task_status(
            'charlie', self.session_id, task_ids[0], TaskStatus.IN_PROGRESS
        )
        print(f"🔄 Charlie comenzó a trabajar en: {tasks[0]['title']}")
        
        # Diana también empieza
        await self.engine.update_task_status(
            'diana', self.session_id, task_ids[1], TaskStatus.IN_PROGRESS
        )
        print(f"🔄 Diana comenzó a trabajar en: {tasks[1]['title']}")
        
        # Simular progreso
        await asyncio.sleep(3)
        
        # Charlie completa su tarea
        await self.engine.update_task_status(
            'charlie', self.session_id, task_ids[0], TaskStatus.COMPLETED,
            results={"completion_percentage": 100, "deliverables": ["collaboration_engine.py"]}
        )
        print(f"✅ Charlie completó: {tasks[0]['title']}")
        
        print("✅ Demostración de colaboración en tareas completada\n")
    
    async def demonstrate_agent_monitoring(self):
        """Demostrar monitoreo de agentes"""
        print("📊 Demostrando Monitoreo de Agentes")
        print("-" * 40)
        
        # Simular trabajo de agentes
        await self.simulate_agent_work()
        
        # Mostrar estadísticas de utilización
        utilization_data = await self.engine.get_agent_utilization(self.session_id)
        
        print("📈 Estados actuales de agentes:")
        for agent_id, data in utilization_data.items():
            print(f"  🤖 {agent_id}:")
            print(f"     • Estado: {data['status']}")
            print(f"     • Utilización: {data['utilization_percentage']:.1f}%")
            print(f"     • Salud: {data['health_status']}")
            print(f"     • Tarea actual: {data['current_task'] or 'Ninguna'}")
        
        print("✅ Demostración de monitoreo de agentes completada\n")
    
    async def simulate_agent_work(self):
        """Simular trabajo de agentes"""
        # Simular que el agente Python está trabajando
        await self.engine.update_agent_state(
            agent_id="python_agent",
            agent_type="python_executor",
            status="busy",
            current_task="task_charlie_1",
            utilization=85.0,
            performance_metrics={
                "execution_time": 2.5,
                "success_rate": 0.95,
                "memory_usage": 120.5
            },
            session_id=self.session_id
        )
        
        # Simular que el agente Search está sobrecargado
        await self.engine.update_agent_state(
            agent_id="search_agent",
            agent_type="search_engine", 
            status="overloaded",
            utilization=95.0,
            performance_metrics={
                "response_time": 5.2,
                "success_rate": 0.88,
                "queries_per_second": 150.0
            },
            session_id=self.session_id
        )
        
        # Simular que el agente Scraper está inactivo
        await self.engine.update_agent_state(
            agent_id="scraper_agent",
            agent_type="web_scraper",
            status="idle",
            utilization=5.0,
            performance_metrics={
                "pages_scraped": 0,
                "success_rate": 0.0
            },
            session_id=self.session_id
        )
        
        await asyncio.sleep(1)
    
    async def demonstrate_conflict_resolution(self):
        """Demostrar resolución de conflictos"""
        print("⚠️  Demostrando Resolución de Conflictos")
        print("-" * 40)
        
        # Crear conflictos simulados
        await self.create_test_conflicts()
        
        # Detectar conflictos
        conflicts = await self.engine.detect_conflicts(self.session_id)
        
        print(f"🔍 Detectados {len(conflicts)} conflictos:")
        for conflict in conflicts:
            print(f"  • {conflict.conflict_type.value}: {conflict.description}")
        
        # Resolver conflicto de sobrecarga
        if conflicts:
            conflict = conflicts[0]
            
            resolution_request = type('ConflictResolutionRequest', (), {
                'conflict_id': conflict.conflict_id,
                'resolution_strategy': 'reassign_tasks',
                'resolution_data': {
                    'target_user_id': 'bob',
                    'tasks': ['task_overloaded_user_1', 'task_overloaded_user_2']
                }
            })()
            
            await self.engine.resolve_conflict('alice', conflict.conflict_id, resolution_request)
            print(f"🔧 Conflicto resuelto usando estrategia: reassign_tasks")
        
        print("✅ Demostración de resolución de conflictos completada\n")
    
    async def create_test_conflicts(self):
        """Crear conflictos de prueba"""
        session = self.engine.active_sessions.get(self.session_id)
        if session:
            # Simular sobrecarga de tareas para un usuario
            charlie_tasks = [f"task_{uuid.uuid4().hex[:8]}" for _ in range(15)]
            
            for task_id in charlie_tasks[:12]:  # Simular 12 tareas asignadas
                session.task_assignments[task_id] = 'charlie'
            
            print("⚠️  Conflicto simulado: Usuario sobrecargado con tareas")
    
    async def demonstrate_notifications(self):
        """Demostrar sistema de notificaciones"""
        print("🔔 Demostrando Sistema de Notificaciones")
        print("-" * 40)
        
        # Enviar notificaciones de prueba
        notifications = [
            (NotificationType.USER_JOINED, {"user_id": "guest", "user_name": "Guest User"}),
            (NotificationType.TASK_ASSIGNED, {"task_id": "task_new", "assigned_to": "bob"}),
            (NotificationType.AGENT_STATUS_CHANGE, {"agent_id": "python_agent", "new_status": "busy"}),
            (NotificationType.CONFLICT_RESOLVED, {"conflict_id": "conflict_123", "strategy": "reassign_tasks"})
        ]
        
        for notification_type, data in notifications:
            await self.engine.broadcast_notification(
                self.session_id,
                notification_type,
                data
            )
            print(f"📢 Notificación enviada: {notification_type.value}")
            await asyncio.sleep(0.5)
        
        print("✅ Demostración de notificaciones completada\n")
    
    async def demonstrate_shared_context(self):
        """Demostrar contexto compartido"""
        print("🗂️  Demostrando Contexto Compartido")
        print("-" * 40)
        
        # Actualizar contexto compartido
        context_updates = [
            ("project_status", "En desarrollo"),
            ("current_sprint", "Sprint 1"),
            ("team_velocity", 25),
            ("remaining_tasks", 8),
            ("blockers", ["Configuración de CI/CD"])
        ]
        
        for key, value in context_updates:
            await self.engine.update_shared_context(
                'alice', self.session_id, key, value
            )
            print(f"📝 Contexto actualizado: {key} = {value}")
        
        # Obtener contexto
        context = await self.engine.get_shared_context(self.session_id)
        
        print("\n📋 Contexto actual de la sesión:")
        for key, value in context.items():
            print(f"  • {key}: {value}")
        
        print("✅ Demostración de contexto compartido completada\n")
    
    async def run_performance_test(self):
        """Ejecutar test de rendimiento"""
        print("⚡ Ejecutando Test de Rendimiento")
        print("-" * 40)
        
        benchmark = CollaborationBenchmark()
        results = await benchmark.run_comprehensive_benchmark()
        
        print("📊 Resultados del benchmark:")
        for test_name, test_results in results["benchmarks"].items():
            print(f"  🔬 {test_name}:")
            print(f"     • Operaciones: {test_results['count']}")
            print(f"     • Duración: {test_results['duration_seconds']:.2f}s")
            print(f"     • Ops/segundo: {test_results['operations_per_second']:.1f}")
            print(f"     • Tiempo promedio: {test_results['avg_time_per_operation']:.4f}s")
        
        print(f"\n🎯 Resumen general:")
        summary = results["summary"]
        print(f"  • Total operaciones: {summary['total_operations']}")
        print(f"  • Duración total: {summary['total_duration_seconds']:.2f}s")
        print(f"  • Ops/segundo total: {summary['overall_operations_per_second']:.1f}")
        
        print("✅ Test de rendimiento completado\n")
    
    async def show_final_statistics(self):
        """Mostrar estadísticas finales"""
        print("📈 Estadísticas Finales del Sistema")
        print("-" * 40)
        
        stats = await self.engine.get_statistics()
        
        print("🔢 Estadísticas del sistema:")
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"  • {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    - {sub_key}: {sub_value}")
            else:
                print(f"  • {key}: {value}")
        
        # Información de la sesión
        session_info = await self.engine.get_session_info(self.session_id)
        if session_info:
            print("\n📋 Información de la sesión:")
            for key, value in session_info.items():
                print(f"  • {key}: {value}")
        
        print("✅ Estadísticas mostradas\n")
    
    async def cleanup(self):
        """Limpiar recursos"""
        print("🧹 Limpiando recursos...")
        
        # Desconectar clientes
        for client in self.clients.values():
            client.close()
        
        # Cerrar motor de colaboración
        if self.engine:
            await self.engine.shutdown()
        
        print("✅ Limpieza completada")
    
    async def run_example(self):
        """Ejecutar ejemplo completo"""
        try:
            # Configuración inicial
            await self.setup()
            
            # Demostraciones
            await self.demonstrate_basic_collaboration()
            await self.demonstrate_task_collaboration()
            await self.demonstrate_agent_monitoring()
            await self.demonstrate_conflict_resolution()
            await self.demonstrate_notifications()
            await self.demonstrate_shared_context()
            
            # Test de rendimiento
            await self.run_performance_test()
            
            # Estadísticas finales
            await self.show_final_statistics()
            
            print("🎉 ¡Ejemplo completado exitosamente!")
            print("=" * 60)
            
        except Exception as e:
            logger.error(f"Error en ejemplo: {e}")
            print(f"❌ Error: {e}")
        
        finally:
            await self.cleanup()


# === FUNCIÓN PRINCIPAL ===
async def main():
    """Función principal"""
    print("🌟 Ejemplo del Sistema de Colaboración en Tiempo Real")
    print("MCP Core Superior - Multi-User Real-Time Collaboration")
    print("=" * 60)
    
    # Crear y ejecutar ejemplo
    example = CollaborationExample()
    await example.run_example()


# === UTILIDADES ADICIONALES ===

async def quick_demo():
    """Demo rápida de funcionalidades"""
    print("🚀 Demo Rápida del Sistema de Colaboración")
    print("-" * 50)
    
    # Inicio rápido
    engine = await quick_start_collaboration()
    
    # Crear algunos usuarios y sesiones
    users = ["alice", "bob", "charlie"]
    
    # Unir usuarios
    for user in users:
        await engine.join_session(
            user, 
            list(engine.active_sessions.keys())[0],
            type('SessionJoinRequest', (), {
                'session_id': list(engine.active_sessions.keys())[0],
                'user_permissions': ['create_task', 'update_task']
            })()
        )
        print(f"👤 Usuario {user} joined")
    
    # Crear tarea
    await engine.create_task(
        "alice",
        list(engine.active_sessions.keys())[0],
        type('TaskCreateRequest', (), {
            'title': 'Tarea Demo',
            'description': 'Esta es una tarea de demostración',
            'assigned_users': ['bob', 'charlie'],
            'priority': 3
        })()
    )
    
    print("✅ Demo rápida completada")
    
    # Mostrar estadísticas
    stats = await engine.get_statistics()
    print(f"📊 Sesiones activas: {stats['total_sessions']}")
    print(f"🔗 Conexiones activas: {stats['active_connections']}")


# === EJECUCIÓN ===
if __name__ == "__main__":
    import uuid
    
    # Configurar event loop para Windows si es necesario
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Ejecutar ejemplo completo o demo rápida
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        asyncio.run(quick_demo())
    else:
        asyncio.run(main())