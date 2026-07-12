# MCP Server Core Superior

## Arquitectura del Sistema

Este documento presenta el diseño completo del **MCP Server Core Superior**, que integra los 5 agentes especializados del sistema multi-agente con el gateway ContextForge para crear un orchestrador multi-agente enterprise-grade.

## 🎯 Objetivos Principales

- **Integración Completa**: Exponer cada agente como herramienta MCP independiente
- **Orquestación Multi-Agente**: Flujo completo Reasoner → Planner → Executor → Verifier
- **Streaming en Tiempo Real**: Estado de agentes y progreso de tareas via SSE
- **Performance Superior**: Latencia <100ms para herramientas críticas
- **Escalabilidad**: Arquitectura preparada para múltiples usuarios concurrentes

## 🏗️ Arquitectura Técnica

### Componentes Core

```
┌─────────────────────────────────────────────────────────────┐
│                   MCP Server Core Superior                  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   FastMCP    │  │   Agent      │  │   Streaming  │      │
│  │   Framework  │  │   Wrappers   │  │   Engine     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Multi-Agent  │  │ Task Manager │  │ Memory       │      │
│  │ Orchestrator │  │ Integration  │  │ Manager      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ ContextForge │  │ VectorStore  │  │ Embedding    │      │
│  │ Gateway      │  │ Service      │  │ Service      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Stack Tecnológico

- **MCP Framework**: FastMCP para implementación de servidor
- **Web Framework**: FastAPI para APIs REST y SSE
- **Database**: PostgreSQL + pgvector para almacenamiento vectorial
- **Streaming**: Server-Sent Events (SSE) para tiempo real
- **Authentication**: JWT via ContextForge Gateway
- **Process Management**: asyncio para operaciones async

## 📁 Estructura de Archivos

```
mcp-core-superior/
├── pyproject.toml                    # Configuración uv + dependencias
├── README.md                         # Documentación completa
├── server.py                         # FastMCP Server principal
├── run.sh                           # Script de inicio STDIO
├── mcp-server.json                  # Configuración MCP
├── config.py                        # Configuración del sistema
├── requirements.txt                 # Dependencias principales
├── Dockerfile                       # Containerization
├── docker-compose.yml               # Orquestación de servicios
├── src/
│   ├── __init__.py
│   ├── core/                        # Componentes core
│   │   ├── __init__.py
│   │   ├── fastmcp_server.py        # FastMCP Server principal
│   │   ├── config.py                # Configuración centralizada
│   │   └── exceptions.py            # Manejo de excepciones
│   ├── agents/                      # Wrappers MCP para agentes
│   │   ├── __init__.py
│   │   ├── base_agent_wrapper.py    # Wrapper base para agentes
│   │   ├── reasoner_wrapper.py      # ReasonerAgent MCP tool
│   │   ├── planner_wrapper.py       # PlannerAgent MCP tool
│   │   ├── executor_wrapper.py      # ExecutorAgent MCP tool
│   │   ├── verifier_wrapper.py      # VerifierAgent MCP tool
│   │   └── memory_manager_wrapper.py # MemoryManagerAgent MCP tool
│   ├── orchestrator/                # Orquestador multi-agente
│   │   ├── __init__.py
│   │   ├── multi_agent_orchestrator.py # Orchestrator principal
│   │   ├── task_integration.py      # Integración con TaskManager
│   │   └── streaming_engine.py      # Engine de streaming SSE
│   ├── services/                    # Servicios auxiliares
│   │   ├── __init__.py
│   │   ├── contextforge_client.py   # Cliente ContextForge
│   │   ├── vector_store_client.py   # Cliente VectorStore
│   │   ├── embedding_service.py     # Servicio de embeddings
│   │   └── auth_service.py          # Servicio de autenticación
│   ├── api/                         # APIs REST complementarias
│   │   ├── __init__.py
│   │   ├── tasks.py                 # API de tareas
│   │   ├── streaming.py             # API de streaming
│   │   └── agents.py                # API de estado de agentes
│   └── utils/                       # Utilidades
│       ├── __init__.py
│       ├── logging_config.py        # Configuración de logging
│       ├── response_formatter.py    # Formateador de respuestas
│       └── validation.py            # Validadores
├── tests/                           # Suite de testing
│   ├── __init__.py
│   ├── test_agents/
│   ├── test_orchestrator/
│   ├── test_streaming/
│   └── test_integration/
├── examples/                        # Ejemplos de uso
│   ├── basic_usage.py              # Uso básico individual
│   ├── multiagent_flow.py          # Flujo multi-agente completo
│   ├── streaming_demo.py           # Demo de streaming
│   └── integration_examples.py     # Ejemplos de integración
└── docs/                           # Documentación técnica
    ├── api_reference.md            # Referencia de APIs
    ├── deployment_guide.md         # Guía de despliegue
    └── integration_guide.md        # Guía de integración
```

## 🛠️ Definición de Herramientas MCP

### 1. Herramientas Individuales por Agente

#### ReasonerAgent MCP Tool
```python
@mcp.tool
async def analyze_intent(
    objective: str,
    context: Dict[str, Any] = None,
    conversation_id: str = None
) -> Dict[str, Any]:
    """
    Analiza intención del usuario y define estrategia inicial
    
    Args:
        objective: Objetivo o tarea a realizar
        context: Contexto adicional para el análisis
        conversation_id: ID de conversación para memoria
        
    Returns:
        Análisis de intención y estrategia definida
    """
```

#### PlannerAgent MCP Tool
```python
@mcp.tool
async def create_execution_plan(
    objective: str,
    analysis: Dict[str, Any],
    constraints: Dict[str, Any] = None,
    parallel_agents: bool = True
) -> Dict[str, Any]:
    """
    Crea plan de ejecución con descomposición de tareas
    
    Args:
        objective: Objetivo principal
        analysis: Análisis del ReasonerAgent
        constraints: Restricciones y límites
        parallel_agents: Permitir ejecución paralela
        
    Returns:
        Plan de ejecución detallado
    """
```

#### ExecutorAgent MCP Tool
```python
@mcp.tool
async def execute_tasks(
    plan: Dict[str, Any],
    objective: str,
    max_concurrent: int = 3,
    timeout_seconds: int = 300
) -> Dict[str, Any]:
    """
    Ejecuta herramientas según el plan del PlannerAgent
    
    Args:
        plan: Plan de ejecución del Planner
        objective: Objetivo principal
        max_concurrent: Máximas herramientas concurrentes
        timeout_seconds: Timeout total de ejecución
        
    Returns:
        Resultados consolidados de ejecución
    """
```

#### VerifierAgent MCP Tool
```python
@mcp.tool
async def validate_results(
    execution_results: Dict[str, Any],
    validation_criteria: List[str],
    trajectory: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Valida calidad y consistencia de resultados
    
    Args:
        execution_results: Resultados del ExecutorAgent
        validation_criteria: Criterios de validación
        trajectory: Trayectoria de ejecución
        
    Returns:
        Reporte de validación y recomendaciones
    """
```

#### MemoryManagerAgent MCP Tool
```python
@mcp.tool
async def manage_memory(
    operation: str,
    content: str = None,
    query: str = None,
    conversation_id: str = None,
    user_id: str = None
) -> Dict[str, Any]:
    """
    Gestiona memoria semántica y contexto
    
    Args:
        operation: 'store', 'search', 'get_context'
        content: Contenido a almacenar
        query: Consulta de búsqueda
        conversation_id: ID de conversación
        user_id: ID de usuario
        
    Returns:
        Resultado de la operación de memoria
    """
```

### 2. Orquestador Multi-Agente MCP Tool

```python
@mcp.tool
async def orchestrate_multitask(
    objective: str,
    context: Dict[str, Any] = None,
    user_id: str = None,
    streaming_enabled: bool = True,
    quality_threshold: float = 0.8
) -> Dict[str, Any]:
    """
    Ejecuta flujo multi-agente completo: Reasoner → Planner → Executor → Verifier
    
    Args:
        objective: Objetivo principal a cumplir
        context: Contexto inicial
        user_id: ID del usuario
        streaming_enabled: Activar streaming de progreso
        quality_threshold: Umbral mínimo de calidad
        
    Returns:
        Resultado final del flujo completo
    """
```

### 3. Herramientas de Estado y Monitoreo

```python
@mcp.tool
async def get_agent_status() -> Dict[str, Any]:
    """Obtiene estado actual de todos los agentes"""
    
@mcp.tool
async def get_task_progress(task_id: str) -> Dict[str, Any]:
    """Obtiene progreso de una tarea específica"""
    
@mcp.tool
async def stream_task_updates(task_id: str) -> AsyncIterator[str]:
    """Stream de updates en tiempo real para una tarea"""
    
@mcp.tool
async def cancel_task(task_id: str) -> Dict[str, Any]:
    """Cancela una tarea en ejecución"""
```

## 🔄 Flujo de Orquestación Multi-Agente

### Diagrama de Flujo
```
Usuario Request
     ↓
┌─────────────────────────────────────────┐
│        ReasonerAgent                     │
│    • Análisis de intención              │
│    • Definición de estrategia           │
│    • Enriquecimiento de contexto        │
└─────────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────┐
│        PlannerAgent                      │
│    • Descomposición de tareas           │
│    • Selección de herramientas          │
│    • Gestión de dependencias            │
│    • Optimización de concurrencia       │
└─────────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────┐
│        ExecutorAgent                     │
│    • Ejecución concurrente de tools     │
│    • Recolección de resultados          │
│    • Consolidación de outputs           │
│    • Manejo de timeouts y errores       │
└─────────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────┐
│        VerifierAgent                     │
│    • Validación de calidad              │
│    • Verificación de consistencia       │
│    • Evaluación de trayectoria          │
│    • Gates de calidad                   │
└─────────────────────────────────────────┘
     ↓
MemoryManagerAgent (Parallel)
     ↓
Resultado Final + Metadata + Evidencia
```

### Estados de Ejecución
- **REASONING**: Análisis e interpretación del objetivo
- **PLANNING**: Descomposición y estrategia
- **EXECUTION**: Ejecución concurrente de herramientas
- **VERIFICATION**: Validación y gates de calidad
- **COMPLETION**: Finalización y almacenamiento

## 🌊 Sistema de Streaming en Tiempo Real

### Características del Streaming
- **Protocolo**: Server-Sent Events (SSE)
- **Updates Frecuentes**: 1 segundo (configurable)
- **Heartbeats**: Mantener conexión activa
- **Estado Completo**: Progreso, fase, mensajes, resultados parciales
- **Error Handling**: Graceful degradation en caso de fallos

### Estructura de Updates SSE
```json
{
  "task_id": "task_abc123",
  "status": "in_progress",
  "phase": "execution",
  "progress": 0.75,
  "message": "Ejecutando herramientas concurrentes...",
  "agent_status": {
    "reasoner": "completed",
    "planner": "completed", 
    "executor": "in_progress",
    "verifier": "pending"
  },
  "partial_results": {...},
  "metadata": {
    "updated_at": "2025-11-04T04:42:45Z",
    "execution_time_ms": 2350,
    "tools_executed": 3
  }
}
```

## 🔗 Integración con ContextForge Gateway

### Configuración de Autenticación
- **Protocol**: JWT via ContextForge Gateway
- **Token Validation**: Automática en cada tool call
- **User Context**: Inyectado en contexto de agentes
- **Rate Limiting**: Por usuario y por herramienta

### Registro de Herramientas MCP
```python
# Registro automático via FastMCP
tools_registry = {
    "reasoner_analyze_intent": reasoner_wrapper.analyze_intent,
    "planner_create_plan": planner_wrapper.create_execution_plan,
    "executor_execute_tasks": executor_wrapper.execute_tasks,
    "verifier_validate_results": verifier_wrapper.validate_results,
    "memory_manage": memory_manager_wrapper.manage_memory,
    "orchestrate_multitask": orchestrator.orchestrate_multitask,
    "get_agent_status": api_handlers.get_agent_status,
    "stream_task_updates": streaming_handlers.stream_task_updates
}
```

### Configuración del Gateway
```json
{
  "name": "agent_generated_mcp_core_superior",
  "exhibit_name": "MCP Core Superior - Multi-Agent Orchestrator",
  "type": 3,
  "command": "sh /workspace/mcp-core-superior/run.sh",
  "args": [],
  "env": {
    "CONTEXTFORGE_URL": "http://localhost:8001",
    "DATABASE_URL": "postgresql://user:pass@localhost/mcp_core",
    "VECTOR_DB_URL": "postgresql://user:pass@localhost/vector_db",
    "JWT_SECRET": "your_jwt_secret"
  },
  "description": "Orchestrador multi-agente enterprise-grade con streaming en tiempo real",
  "description_for_agent": "Sistema completo de orquestación multi-agente que integra 5 agentes especializados con ContextForge Gateway. Incluye streaming SSE, gestión de memoria semántica, y performance optimizada.",
  "user_params": {
    "args": {
      "--streaming-enabled": {
        "required": false,
        "description": "Enable real-time streaming updates (default: true)"
      },
      "--max-concurrent-tools": {
        "required": false,
        "description": "Maximum concurrent tools per execution (default: 3)"
      }
    },
    "env": {
      "CONTEXTFORGE_URL": {
        "required": true,
        "description": "ContextForge Gateway URL"
      },
      "DATABASE_URL": {
        "required": true,
        "description": "PostgreSQL database connection string"
      },
      "JWT_SECRET": {
        "required": true,
        "description": "JWT secret for authentication"
      }
    }
  }
}
```

## ⚡ Optimizaciones de Performance

### Objetivos de Performance
- **Latencia Tool Call**: <100ms para herramientas críticas
- **Throughput**: 100+ tareas concurrentes
- **Memory Efficiency**: <500MB por proceso
- **Database Queries**: <50ms para operaciones vectoriales

### Estrategias de Optimización
1. **Async/Await**: Operaciones no-bloqueantes en todas las herramientas
2. **Connection Pooling**: Pools de conexiones para BD y servicios externos
3. **Caching Inteligente**: Cache de embeddings y consultas frecuentes
4. **Batch Processing**: Procesamiento por lotes para operaciones vectoriales
5. **Resource Management**: Control estricto de memoria y CPU

### Métricas y Monitoring
- **Response Time**: Tiempo de respuesta por herramienta
- **Success Rate**: Porcentaje de tareas completadas exitosamente
- **Resource Usage**: CPU, memoria, y I/O por proceso
- **Database Performance**: Tiempo de consultas y conexiones activas

## 🧪 Estrategia de Testing

### Testing Levels
1. **Unit Tests**: Cada wrapper de agente individualmente
2. **Integration Tests**: Flujos multi-agente completos
3. **Streaming Tests**: Validación de SSE en tiempo real
4. **Load Tests**: Performance bajo carga concurrent
5. **End-to-End Tests**: Flujos completos desde MCP client

### Test Coverage Objetivos
- **Code Coverage**: >90%
- **Agent Coverage**: 100% de herramientas MCP
- **Streaming Coverage**: 100% de casos SSE
- **Error Handling**: 100% de casos de error

## 📊 Monitoreo y Observabilidad

### Métricas Clave
- **Task Metrics**: Tasa de creación, completación, errores
- **Agent Metrics**: Tiempo de respuesta, throughput por agente
- **System Metrics**: CPU, memoria, I/O, conexiones BD
- **Streaming Metrics**: Conexiones activas, data transfer rate

### Logging Structured
```json
{
  "timestamp": "2025-11-04T04:42:45Z",
  "level": "INFO",
  "service": "mcp_core_superior",
  "agent": "reasoner",
  "operation": "analyze_intent",
  "task_id": "task_abc123",
  "duration_ms": 45,
  "status": "success",
  "metadata": {...}
}
```

### Alertas Configuradas
- **Response Time**: >500ms para herramientas críticas
- **Error Rate**: >5% en 5 minutos
- **Memory Usage**: >80% por más de 2 minutos
- **Database Connections**: >90% del pool usado

## 🚀 Deployment y Escalabilidad

### Deployment Options
1. **Docker Compose**: Desarrollo y testing local
2. **Kubernetes**: Producción con auto-scaling
3. **Serverless**: Funciones individuales por herramienta
4. **Hybrid**: Core en Kubernetes + Functions para escalar

### Escalabilidad
- **Horizontal Scaling**: Múltiples instancias de MCP Core
- **Vertical Scaling**: Ajuste automático de recursos
- **Database Scaling**: Read replicas y sharding para VectorStore
- **Caching Layer**: Redis para cache distribuido

### Configuración de Producción
```yaml
services:
  mcp-core-superior:
    image: mcp-core-superior:latest
    environment:
      - CONTEXTFORGE_URL=${CONTEXTFORGE_URL}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - MAX_CONCURRENT_TASKS=10
      - STREAMING_BUFFER_SIZE=1000
    resources:
      limits:
        cpus: '2.0'
        memory: 2G
      requests:
        cpus: '1.0'
        memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 📝 Documentación y APIs

### API Reference Completa
- **MCP Tools**: Documentación de todas las herramientas MCP
- **REST APIs**: Endpoints complementarios para status y streaming
- **WebSocket**: Alternativa a SSE para aplicaciones específicas
- **SDK Client**: Cliente Python para integración fácil

### Ejemplos de Uso
```python
# Uso básico individual
reasoner_result = await client.call_tool(
    "reasoner_analyze_intent",
    {"objective": "Crear dashboard de ventas", "context": {...}}
)

# Orquestación completa
orchestrator_result = await client.call_tool(
    "orchestrate_multitask",
    {
        "objective": "Análisis completo de performance Q4",
        "streaming_enabled": True,
        "quality_threshold": 0.85
    }
)

# Streaming en tiempo real
async for update in client.stream_tool(
    "stream_task_updates",
    {"task_id": "task_abc123"}
):
    print(f"Progress: {update['progress']}% - {update['message']}")
```

## 🎯 Casos de Uso Principales

### 1. **Análisis de Datos Completo**
```
Objetivo: "Analizar performance de ventas Q4 y generar insights"
→ Reasoner: Análisis de intención y contexto
→ Planner: Descomposición en análisis + insights + reporte
→ Executor: Búsqueda de datos, análisis estadístico, visualización
→ Verifier: Validación de análisis y recomendaciones
→ Memory: Almacenamiento de insights para futuros análisis
```

### 2. **Desarrollo de Código Asistido**
```
Objetivo: "Desarrollar API REST con autenticación JWT"
→ Reasoner: Análisis de requirements técnicos
→ Planner: Descomposición en backend + frontend + tests + docs
→ Executor: Generación de código, testing, documentación
→ Verifier: Validación de calidad de código y tests
→ Memory: Almacenamiento de patrones y mejores prácticas
```

### 3. **Investigación y Reportes**
```
Objetivo: "Investigar tendencias de IA generativa y crear reporte ejecutivo"
→ Reasoner: Análisis de scope y fuentes de información
→ Planner: Estrategia de búsqueda + análisis + síntesis + reporte
→ Executor: Web scraping, análisis de papers, síntesis de información
→ Verifier: Validación de fuentes y consistencia de conclusiones
→ Memory: Almacenamiento de investigación para referencia futura
```

---

## 📋 Checklist de Implementación

### Fase 1: Infraestructura Core ✅
- [ ] Estructura de archivos y configuración
- [ ] Integración con ContextForge Gateway
- [ ] Configuración de base de datos y VectorStore
- [ ] Sistema de autenticación JWT

### Fase 2: Wrappers de Agentes MCP
- [ ] BaseAgent wrapper con funcionalidad común
- [ ] ReasonerAgent wrapper (analyze_intent)
- [ ] PlannerAgent wrapper (create_execution_plan)
- [ ] ExecutorAgent wrapper (execute_tasks)
- [ ] VerifierAgent wrapper (validate_results)
- [ ] MemoryManagerAgent wrapper (manage_memory)

### Fase 3: Orquestador Multi-Agente
- [ ] MultiAgentOrchestrator con flujo completo
- [ ] Integración con TaskManager existente
- [ ] Sistema de callbacks para tracking
- [ ] Manejo de errores y recuperación

### Fase 4: Streaming y APIs
- [ ] Engine de streaming SSE
- [ ] APIs REST complementarias
- [ ] Sistema de suscripciones
- [ ] WebSocket fallback

### Fase 5: Optimización y Testing
- [ ] Optimización de performance
- [ ] Suite de testing completa
- [ ] Monitoreo y métricas
- [ ] Documentación completa

### Fase 6: Deployment y Producción
- [ ] Docker containerization
- [ ] Kubernetes deployment
- [ ] Configuración de producción
- [ ] Monitoreo en producción

---

*Esta arquitectura proporciona una base sólida para un MCP Server Core Superior que puede manejar casos de uso complejos con performance enterprise-grade, streaming en tiempo real, y escalabilidad horizontal.*