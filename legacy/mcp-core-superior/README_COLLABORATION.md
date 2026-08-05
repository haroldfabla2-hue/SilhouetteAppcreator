# Sistema de Colaboración en Tiempo Real Multi-usuario

## 📖 Descripción General

El Sistema de Colaboración en Tiempo Real de MCP Core Superior es una solución completa que permite la colaboración multi-usuario en tiempo real con capacidades avanzadas de sincronización de estados de agentes, gestión de tareas colaborativas, resolución de conflictos y monitoreo en vivo.

## ✨ Características Principales

### 🔗 Core Features
- **Multi-user session management** - Gestión completa de sesiones con Redis
- **Real-time agent state synchronization** - Sincronización en tiempo real de estados de agentes
- **Collaborative task execution** - Ejecución colaborativa con resolución de conflictos
- **Shared context management** - Contexto compartido entre usuarios
- **Live agent utilization monitoring** - Monitoreo de utilización de agentes en vivo
- **Role-based access control** - Control de acceso granular basado en roles
- **Real-time notifications** - Sistema de notificaciones en tiempo real
- **Conflict resolution algorithms** - Algoritmos avanzados de resolución de conflictos
- **Session persistence and recovery** - Persistencia y recuperación de sesiones
- **Scalable WebSocket management** - Gestión escalable de conexiones WebSocket

### 🛠️ Componentes Técnicos
- **WebSockets** para comunicación bidireccional
- **Redis** para gestión de sesiones y cache
- **AsyncIO** para operaciones asíncronas
- **Pydantic** para validación de datos
- **Sistema de roles** completo (Owner, Admin, Collaborator, Viewer, Guest)

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    Collaboration Engine                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Session   │  │    User     │  │   Agent     │          │
│  │  Management │  │ Management  │  │ Management  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Task      │  │  Conflict   │  │Notification │          │
│  │ Management  │  │ Resolution  │  │   System    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  WebSocket  │  │    Redis    │  │  Message    │          │
│  │   Server    │  │   Storage   │  │   Queue     │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Estructura de Archivos

```
src/core/
├── collaboration_engine.py      # Motor principal de colaboración
├── collaboration_config.py      # Configuración específica
├── collaboration_utils.py       # Utilidades y herramientas
└── examples/
    └── collaboration_example.py # Ejemplo completo de uso
```

## 🚀 Instalación y Configuración

### Requisitos Previos

```bash
# Instalar dependencias
pip install redis asyncio websockets pydantic

# O instalar desde requirements.txt
pip install -r requirements.txt
```

### Configuración Básica

El sistema utiliza la configuración centralizada de `src/core/config.py` y configuraciones específicas en `src/core/collaboration_config.py`.

#### Variables de Entorno Principales

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379
MCP_CORE_REDIS_POOL_SIZE=10

# WebSocket Configuration
MCP_CORE_WS_HOST=0.0.0.0
MCP_CORE_WS_PORT=8083
MCP_CORE_MAX_WEBSOCKET_CONNECTIONS=1000

# Security Configuration
MCP_CORE_JWT_SECRET=your-secret-key
MCP_CORE_RATE_LIMIT_ENABLED=true
```

## 💻 Uso Básico

### Inicio Rápido

```python
import asyncio
from src.core.collaboration_engine import get_collaboration_engine

async def start_collaboration():
    # Obtener instancia del motor
    engine = await get_collaboration_engine()
    
    # Crear sesión de colaboración
    session_id = await engine.create_session(
        owner_id="user_123",
        session_data=SessionCreateRequest(
            name="Mi Proyecto",
            description="Proyecto colaborativo",
            initial_participants=["user_456", "user_789"]
        )
    )
    
    return engine, session_id

# Ejecutar
asyncio.run(start_collaboration())
```

### Gestión de Sesiones

```python
# Crear nueva sesión
session_id = await engine.create_session(
    owner_id="alice",
    session_data=SessionCreateRequest(
        name="Proyecto de Desarrollo",
        description="Desarrollo de sistema multi-agente",
        initial_participants=["bob", "charlie"]
    )
)

# Unirse a sesión existente
await engine.join_session(
    user_id="bob",
    session_id=session_id,
    join_request=SessionJoinRequest(
        session_id=session_id,
        user_permissions=["create_task", "update_task"]
    )
)
```

### Colaboración en Tareas

```python
# Crear tarea colaborativa
task_id = await engine.create_task(
    user_id="alice",
    session_id=session_id,
    task_data=TaskCreateRequest(
        title="Implementar motor de colaboración",
        description="Desarrollar el núcleo del sistema",
        assigned_users=["charlie"],
        priority=5
    )
)

# Actualizar estado de tarea
await engine.update_task_status(
    user_id="charlie",
    session_id=session_id,
    task_id=task_id,
    status=TaskStatus.IN_PROGRESS
)

# Completar tarea
await engine.update_task_status(
    user_id="charlie",
    session_id=session_id,
    task_id=task_id,
    status=TaskStatus.COMPLETED,
    results={"completion_percentage": 100}
)
```

### Monitoreo de Agentes

```python
# Actualizar estado de agente
await engine.update_agent_state(
    agent_id="python_agent",
    agent_type="python_executor",
    status="busy",
    current_task=task_id,
    utilization=85.0,
    performance_metrics={
        "execution_time": 2.5,
        "success_rate": 0.95
    },
    session_id=session_id
)

# Obtener métricas de utilización
utilization_data = await engine.get_agent_utilization(session_id)
for agent_id, data in utilization_data.items():
    print(f"Agente {agent_id}: {data['utilization_percentage']:.1f}%")
```

### Comunicación WebSocket

```python
from src.core.collaboration_engine import websocket_handler
import websockets

async def handle_websocket(websocket, path):
    user_id = "user_123"
    session_id = "session_456"
    
    await websocket_handler(websocket, path, user_id, session_id)

# Iniciar servidor WebSocket
start_server = websockets.serve(handle_websocket, "0.0.0.0", 8083)
asyncio.get_event_loop().run_until_complete(start_server)
```

### Resolución de Conflictos

```python
# Detectar conflictos
conflicts = await engine.detect_conflicts(session_id)

# Resolver conflicto
if conflicts:
    await engine.resolve_conflict(
        resolver_user_id="admin_user",
        conflict_id=conflicts[0].conflict_id,
        resolution_request=ConflictResolutionRequest(
            conflict_id=conflicts[0].conflict_id,
            resolution_strategy="reassign_tasks",
            resolution_data={
                "target_user_id": "charlie",
                "tasks": ["task_1", "task_2"]
            }
        )
    )
```

## 📊 API Reference

### Core Classes

#### `CollaborationEngine`
Motor principal del sistema de colaboración.

**Métodos principales:**
- `create_session()` - Crear nueva sesión
- `join_session()` - Unirse a sesión existente
- `create_task()` - Crear tarea colaborativa
- `update_agent_state()` - Actualizar estado de agente
- `resolve_conflict()` - Resolver conflicto
- `get_statistics()` - Obtener estadísticas del sistema

#### `User`
Representa un usuario en el sistema.

**Atributos:**
- `user_id` - Identificador único
- `username` - Nombre de usuario
- `role` - Rol del usuario (Owner, Admin, Collaborator, Viewer, Guest)
- `session_id` - ID de sesión actual
- `permissions` - Permisos específicos

#### `CollaborationSession`
Representa una sesión de colaboración.

**Atributos:**
- `session_id` - Identificador único
- `name` - Nombre de la sesión
- `participants` - Diccionario de participantes
- `shared_context` - Contexto compartido
- `task_assignments` - Asignaciones de tareas
- `locks` - Recursos bloqueados

#### `AgentState`
Representa el estado de un agente.

**Atributos:**
- `agent_id` - Identificador del agente
- `agent_type` - Tipo de agente
- `status` - Estado actual (idle, busy, overloaded)
- `utilization_percentage` - Porcentaje de utilización
- `active_sessions` - Sesiones activas

### Request/Response Models

#### `SessionCreateRequest`
```python
class SessionCreateRequest(BaseModel):
    name: str
    description: str = ""
    initial_participants: List[str] = []
```

#### `TaskCreateRequest`
```python
class TaskCreateRequest(BaseModel):
    title: str
    description: str = ""
    assigned_users: List[str] = []
    priority: int = 1
    dependencies: List[str] = []
```

#### `ConflictResolutionRequest`
```python
class ConflictResolutionRequest(BaseModel):
    conflict_id: str
    resolution_strategy: str
    resolution_data: Dict[str, Any] = {}
```

## 🔧 Configuración Avanzada

### Configuración de WebSockets

```python
# src/core/collaboration_config.py
WebSocketConfig(
    max_connections=1000,
    connection_timeout=30,
    message_size_limit=1024*1024,
    heartbeat_interval=30,
    compression_enabled=True,
    ssl_enabled=False
)
```

### Configuración de Redis

```python
RedisCollaborationConfig(
    session_ttl_seconds=3600,
    agent_state_ttl_seconds=1800,
    max_sessions_per_user=5,
    max_session_participants=50,
    cleanup_interval_seconds=300
)
```

### Configuración de Resolución de Conflictos

```python
ConflictResolutionConfig(
    max_conflicts_per_session=10,
    conflict_timeout_seconds=3600,
    auto_resolution_enabled=False,
    escalation_threshold=3,
    resolution_strategies=[
        "reassign_tasks",
        "release_locks", 
        "priority_override"
    ]
)
```

## 📈 Monitoreo y Métricas

### Métricas Disponibles

- **Conexiones activas** - Número de conexiones WebSocket activas
- **Sesiones activas** - Número de sesiones de colaboración activas
- **Utilización de agentes** - Porcentaje de utilización por agente
- **Tareas completadas** - Número de tareas completadas
- **Conflictos resueltos** - Número de conflictos resueltos

### Health Checks

```python
# Obtener estado de salud del sistema
from src.core.collaboration_utils import get_system_health_status

health_status = get_system_health_status()
print(f"Estado: {health_status['overall_status']}")
```

### Métricas Prometheus

El sistema expone métricas en el puerto 9091:

```python
GET /metrics
# Métricas de colaboración en formato Prometheus
```

## 🧪 Testing y Desarrollo

### Ejecutar Ejemplo Completo

```bash
# Ejecutar ejemplo completo
python examples/collaboration_example.py

# Ejecutar demo rápida
python examples/collaboration_example.py quick
```

### Testing Automatizado

```python
from src.core.collaboration_utils import CollaborationTester

async def run_tests():
    tester = CollaborationTester()
    results = await tester.run_all_tests()
    print(f"Tests passed: {results['summary']['passed_tests']}")
    return results
```

### Benchmarking

```python
from src.core.collaboration_utils import CollaborationBenchmark

async def run_benchmarks():
    benchmark = CollaborationBenchmark()
    results = await benchmark.run_comprehensive_benchmark()
    print(f"Operations/second: {results['summary']['overall_operations_per_second']}")
    return results
```

## 🚨 Troubleshooting

### Problemas Comunes

#### 1. Error de Conexión Redis
```
Error: redis ConnectionError
```
**Solución:** Verificar que Redis esté ejecutándose y la URL sea correcta.

#### 2. Límite de Conexiones WebSocket
```
Error: Server overloaded, too many connections
```
**Solución:** Aumentar `max_connections` en la configuración o cerrar conexiones inactivas.

#### 3. Conflictos No Resueltos
```
Warning: Session has unresolved conflicts
```
**Solución:** Usar `detect_conflicts()` y `resolve_conflict()` para manejar conflictos.

#### 4. Sesiones Inactivas
```
Warning: Session cleanup triggered
```
**Solución:** Configurar `session_ttl_seconds` apropiadamente.

### Logs y Debugging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Logs específicos del sistema de colaboración
logger = logging.getLogger('src.core.collaboration_engine')
logger.setLevel(logging.DEBUG)
```

## 🔐 Seguridad

### Autenticación y Autorización

El sistema implementa múltiples capas de seguridad:

1. **JWT Authentication** - Autenticación basada en tokens
2. **Role-based Access Control** - Control de acceso por roles
3. **Session Validation** - Validación de sesiones activas
4. **Rate Limiting** - Limitación de requests
5. **Message Validation** - Validación de formato de mensajes

### Permisos por Rol

| Rol | Permisos |
|-----|----------|
| **Owner** | Todos los permisos |
| **Admin** | Gestión de usuarios, sesiones, tareas |
| **Collaborator** | Crear/actualizar tareas, mensajería |
| **Viewer** | Solo visualización |
| **Guest** | Acceso limitado a visualización |

## 🔄 Integración con Sistema MCP

### Registro de Agentes

```python
from src.core.collaboration_engine import register_agent_with_session

# Registrar agente con sesión
await register_agent_with_session(
    agent_id="python_executor_1",
    agent_type="python_executor", 
    session_id=session_id,
    initial_status="idle"
)
```

### Actualización de Métricas

```python
from src.core.collaboration_engine import update_agent_performance

# Actualizar métricas de rendimiento
await update_agent_performance(
    agent_id="python_executor_1",
    session_id=session_id,
    metrics={
        "execution_time": 2.5,
        "success_rate": 0.95,
        "memory_usage": 128.0
    }
)
```

## 📝 Ejemplos de Uso Avanzado

### Sistema de Notificaciones Custom

```python
# Enviar notificación personalizada
await engine.send_notification(
    user_id="charlie",
    notification_type=NotificationType.TASK_ASSIGNED,
    data={
        "task_id": task_id,
        "task_title": "Implementar feature X",
        "assigned_by": "alice",
        "priority": "high"
    }
)
```

### Contexto Compartido Dinámico

```python
# Actualizar contexto compartido
await engine.update_shared_context(
    user_id="alice",
    session_id=session_id,
    context_key="project_status",
    context_value={
        "phase": "development",
        "sprint": 3,
        "velocity": 25,
        "blockers": ["API integration"]
    }
)
```

### Monitoreo Personalizado

```python
# Obtener métricas personalizadas
utilization_data = await engine.get_agent_utilization(session_id)

# Filtrar agentes sobrecargados
overloaded_agents = {
    agent_id: data for agent_id, data in utilization_data.items()
    if data['utilization_percentage'] > 90
}

print(f"Agentes sobrecargados: {list(overloaded_agents.keys())}")
```

## 🏆 Mejores Prácticas

### 1. Gestión de Sesiones
- Siempre validar permisos antes de operaciones
- Cerrar sesiones inactivas apropiadamente
- Usar timeouts razonables para sesiones

### 2. Colaboración en Tareas
- Definir dependencias claras entre tareas
- Usar niveles de prioridad apropiados
- Actualizar estados regularmente

### 3. Monitoreo de Agentes
- Actualizar estados regularmente (cada 30-60 segundos)
- Monitorear utilización para optimizar rendimiento
- Configurar alertas para agentes sobrecargados

### 4. Resolución de Conflictos
- Detectar conflictos proactivamente
- Usar estrategias apropiadas según el tipo
- Escalar conflictos complejos a administradores

### 5. Seguridad
- Validar todos los inputs
- Implementar rate limiting apropiado
- Rotar secretos regularmente

## 🤝 Contribución

Para contribuir al sistema de colaboración:

1. Fork el repositorio
2. Crear branch para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

### Guidelines de Código

- Seguir PEP 8 para Python
- Documentar funciones y clases
- Escribir tests para nuevas funcionalidades
- Mantener compatibilidad con versiones existentes

## 📞 Soporte

Para obtener soporte:

- **Issues**: Crear issue en GitHub
- **Documentación**: Revisar este README
- **Ejemplos**: Revisar `examples/collaboration_example.py`
- **Tests**: Ejecutar `src/core/collaboration_utils.py`

## 📄 Licencia

Este sistema es parte de MCP Core Superior y está bajo la misma licencia del proyecto principal.

---

**Última actualización**: 2025-11-04  
**Versión**: 1.0.0  
**Mantenido por**: Equipo MCP Core Superior