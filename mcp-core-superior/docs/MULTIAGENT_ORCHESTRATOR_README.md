# Multi-Agent Orchestrator Agent MCP - Documentación Completa

## Descripción General

El **Multi-Agent Orchestrator Agent MCP** es un orquestrador empresarial avanzado que gestiona de forma inteligente múltiples agentes base y especializados, proporcionando capacidades de orquestación de nivel empresarial con workflows complejos, balanceador de carga, monitoreo de salud y escalado automático.

## Características Principales

### 🚀 Capacidades Avanzadas

#### 1. **Workflow Management**
- **Ejecución Secuencial**: Pasos ejecutados en orden con resolución automática de dependencias
- **Ejecución Paralela**: Pasos con el mismo `parallel_group` se ejecutan simultáneamente
- **Gestión de Prioridades**: 5 niveles de prioridad (LOW, NORMAL, HIGH, URGENT, CRITICAL)
- **Reintentos Automáticos**: Sistema de reintentos con backoff exponencial
- **Timeouts Configurables**: Control granular de tiempo de espera por paso

#### 2. **Load Balancing Inteligente**
- **Round Robin**: Distribución equitativa entre agentes
- **Least Connections**: Prioriza agentes con menos conexiones activas
- **Weighted Random**: Selección basada en rendimiento y capacidad disponible
- **Fastest Response**: Prioriza agentes con mejor tiempo de respuesta
- **Capability-Based**: Optimización basada en capacidades específicas

#### 3. **Dependency Resolution**
- **Resolución Automática**: Verifica dependencias antes de ejecutar cada paso
- **Detección de Ciclos**: Prevención de deadlocks en dependencias
- **Ejecución Condicional**: Pasos solo se ejecutan si todas las dependencias están completas

#### 4. **Parallel Execution**
- **Control de Concurrencia**: Límites configurables por agente
- **Semáforos Asíncronos**: Gestión thread-safe de concurrencia
- **Grupos Paralelos**: Ejecución simultánea de pasos independientes
- **Sincronización Automática**: Coordinación de finalización de pasos paralelos

#### 5. **Error Recovery**
- **Circuit Breaker Pattern**: Protección contra cascadas de errores
- **Reintentos Inteligentes**: Múltiples estrategias de reintento
- **Graceful Degradation**: Continúa ejecución con agentes alternativos
- **Rollback Automático**: Revertir cambios en caso de fallos

#### 6. **Horizontal Scaling**
- **Worker Pool**: Múltiples workers para procesar workflows
- **Auto-scaling**: Ajuste automático basado en carga
- **Queue Management**: Cola prioritaria para manejo de workflows
- **Resource Limits**: Límites configurables de recursos

#### 7. **Health Monitoring**
- **Monitoreo Continuo**: Verificación periódica de salud de agentes
- **Alertas Automáticas**: Notificaciones de problemas de salud
- **Métricas en Tiempo Real**: Estadísticas de rendimiento detalladas
- **Health Checks**: Endpoints de verificación de estado

#### 8. **Dynamic Agent Registration**
- **Registro en Tiempo Real**: Añadir agentes sin reiniciar
- **Auto-descubrimiento**: Detección automática de nuevas capacidades
- **Gestión de Metadatos**: Información contextual de agentes
- **Hot-swapping**: Reemplazo de agentes sin downtime

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                Multi-Agent Orchestrator Agent               │
├─────────────────────────────────────────────────────────────┤
│  Workflow Engine  │  Load Balancer  │  Health Monitor      │
├─────────────────────────────────────────────────────────────┤
│  Task Queue       │  Circuit Breaker│  Agent Registry     │
├─────────────────────────────────────────────────────────────┤
│              Base Agents            │  Specialized Agents │
│  • Reasoner    • Memory Manager     │  • Data Analyst     │
│  • Planner     • Verifier           │  • Web Scraper      │
│  • Executor                          │  • API Integrator  │
└─────────────────────────────────────────────────────────────┘
```

## Instalación y Configuración

### Importación Básica

```python
from agents import (
    MultiAgentOrchestratorAgentWrapper,
    WorkflowStep,
    AgentCapability,
    TaskPriority
)
```

### Inicialización

```python
# Crear instancia del orquestrador
orchestrator = MultiAgentOrchestratorAgentWrapper()

# Inicializar (se hace automáticamente en process_request)
await orchestrator.ensure_initialized()
```

## Uso Básico

### Crear un Workflow Simple

```python
from agents.multiagent_orchestrator_agent import WorkflowStep, AgentCapability

# Definir pasos del workflow
steps = [
    WorkflowStep(
        step_id="analyze_requirement",
        agent_type="reasoner",
        capability=AgentCapability.INTENT_ANALYSIS,
        task={"objective": "Analizar requerimiento del usuario"},
        priority=TaskPriority.HIGH
    ),
    WorkflowStep(
        step_id="create_plan",
        agent_type="planner", 
        capability=AgentCapability.TASK_DECOMPOSITION,
        task={"complexity": "medium", "estimated_duration": 10.0},
        dependencies=["analyze_requirement"],
        priority=TaskPriority.NORMAL
    )
]

# Crear workflow
workflow_id = await orchestrator.create_workflow(
    objective="Procesar requerimiento de usuario",
    workflow_steps=steps,
    priority=TaskPriority.HIGH
)

print(f"Workflow creado: {workflow_id}")
```

### Monitorear Estado del Workflow

```python
# Obtener estado actual
status = await orchestrator.get_workflow_status(workflow_id)
print(f"Estado: {status['state']}")
print(f"Progreso: {status['progress']:.2%}")

# Monitorear hasta completar
while status['state'] not in ['completed', 'failed']:
    await asyncio.sleep(1.0)
    status = await orchestrator.get_workflow_status(workflow_id)
```

## Workflows Avanzados

### Workflows con Ejecución Paralela

```python
parallel_steps = [
    WorkflowStep(
        step_id="search_data",
        agent_type="web_search_specialist",
        capability=BaseCapability.WEB_SCRAPING,
        task={"query": "machine learning trends"},
        parallel_group="data_collection",
        priority=TaskPriority.HIGH
    ),
    WorkflowStep(
        step_id="analyze_dataset", 
        agent_type="data_analysis_specialist",
        capability=BaseCapability.CODE_EXECUTION,
        task={"analysis_type": "statistical"},
        parallel_group="data_collection", 
        priority=TaskPriority.HIGH
    ),
    WorkflowStep(
        step_id="verify_results",
        agent_type="verifier",
        capability=AgentCapability.QUALITY_VALIDATION,
        task={"quality_threshold": 0.8},
        dependencies=["search_data", "analyze_dataset"]
    )
]
```

### Agentes Especializados

```python
# Crear agente especializado
class DataAnalysisAgent(BaseAgentWrapper):
    def __init__(self):
        super().__init__(
            agent_name="data_analysis_specialist",
            capabilities=[AgentCapability.CODE_EXECUTION, AgentCapability.TOOL_INVOCATION],
            max_concurrent=2,
            timeout_seconds=120
        )
    
    async def process_request(self, request, context=None):
        # Lógica específica del agente
        return {"analysis": "completed", "results": [1, 2, 3, 4, 5]}

# Registrar agente especializado
data_agent = DataAnalysisAgent()
await orchestrator.register_specialized_agent(
    "data_analysis_specialist", 
    data_agent,
    {"version": "1.0", "capabilities": ["statistics", "visualization"]}
)
```

## Requests MCP

### Listar Agentes

```python
request = {"type": "list_agents"}
response = await orchestrator.process_request(request)
print(f"Agentes registrados: {response['total']}")
```

### Crear Workflow vía MCP

```python
request = {
    "type": "create_workflow",
    "objective": "Análisis de datos con ML",
    "steps": [
        {
            "step_id": "data_prep",
            "agent_type": "data_analysis_specialist",
            "capability": "code_execution", 
            "task": {"operation": "preprocess_data"},
            "priority": 2
        }
    ],
    "priority": 2
}
response = await orchestrator.process_request(request)
workflow_id = response["workflow_id"]
```

### Obtener Estado del Orquestrador

```python
request = {"type": "get_status"}
response = await orchestrator.process_request(request)
status = response["status"]

print(f"Workflows activos: {status['active_workflows']}")
print(f"Agentes registrados: {status['registered_agents']}")
print(f"Tasa de éxito: {status['workflow_metrics']['success_rate']:.2%}")
```

## Configuración Avanzada

### Configurar Load Balancer

```python
from agents.multiagent_orchestrator_agent import LoadBalancingStrategy

# Cambiar estrategia de load balancing
orchestrator.load_balancer.strategy = LoadBalancingStrategy.FASTEST_RESPONSE
```

### Configurar Circuit Breakers

```python
from agents.multiagent_orchestrator_agent import CircuitBreaker

# Configurar circuit breaker personalizado
orchestrator.circuit_breakers["reasoner"] = CircuitBreaker(
    failure_threshold=3,  # Abrir después de 3 fallos
    timeout=30.0  # Intentar cerrar después de 30 segundos
)
```

### Configurar Health Monitoring

```python
# Añadir callback de alerta
async def alert_callback(alert_data):
    print(f"ALERTA: {alert_data['agent_name']} - {alert_data['health_data']['status']}")

orchestrator.health_monitor.add_alert_callback(alert_callback)

# Configurar intervalo de monitoreo
orchestrator.health_monitor.check_interval = 60.0  # Verificar cada minuto
```

### Configurar Auto-scaling

```python
# Habilitar auto-scaling
orchestrator.scaling_enabled = True
orchestrator.max_concurrent_workflows = 50

# Configurar políticas de scaling
orchestrator.auto_scaling_policies = {
    "high_load_threshold": 0.8,     # Scale up al 80% de utilización
    "low_load_threshold": 0.3,      # Scale down al 30% de utilización
    "scale_up_factor": 2.0,         # Duplicar capacidad
    "scale_down_factor": 0.5        # Reducir a la mitad
}
```

## Monitoring y Métricas

### Obtener Métricas del Sistema

```python
status = await orchestrator.get_orchestrator_status()
metrics = status["workflow_metrics"]

print(f"Total workflows: {metrics['total_workflows']}")
print(f"Tasa de éxito: {metrics['successful_workflows'] / max(metrics['total_workflows'], 1):.2%}")
print(f"Tiempo promedio: {metrics['average_completion_time']:.2f}s")
print(f"Peak concurrente: {metrics['peak_concurrent_workflows']}")
```

### Health Check Completo

```python
health = await orchestrator.health_check()
print(f"Estado general: {health['status']}")

if health.get("unhealthy_agents"):
    print(f"Agentes no saludables: {health['unhealthy_agents']}")

if health.get("open_circuits"):
    print(f"Circuits abiertos: {health['open_circuits']}")
```

### Estadísticas de Load Balancer

```python
lb_stats = status["load_balancer"]["agent_stats"]
for agent_name, stats in lb_stats.items():
    print(f"{agent_name}:")
    print(f"  Success rate: {stats['success_rate']:.2%}")
    print(f"  Avg response: {sum(stats['response_times']) / max(len(stats['response_times']), 1):.3f}s")
```

## Ejemplo Completo: Pipeline de Análisis de Datos

```python
async def create_data_analysis_pipeline():
    orchestrator = MultiAgentOrchestratorAgentWrapper()
    
    # Registrar agentes especializados
    await register_specialized_agents(orchestrator)
    
    # Crear pipeline de análisis completo
    pipeline_steps = [
        # Fase 1: Recolección de datos (paralela)
        WorkflowStep(
            step_id="collect_web_data",
            agent_type="web_search_specialist",
            capability=BaseCapability.WEB_SCRAPING,
            task={"query": "market trends 2024", "sources": 10},
            parallel_group="data_collection",
            priority=TaskPriority.HIGH
        ),
        WorkflowStep(
            step_id="collect_internal_data",
            agent_type="data_analysis_specialist", 
            capability=BaseCapability.CODE_EXECUTION,
            task={"operation": "load_internal_data", "source": "database"},
            parallel_group="data_collection",
            priority=TaskPriority.HIGH
        ),
        
        # Fase 2: Análisis (dependiente de fase 1)
        WorkflowStep(
            step_id="statistical_analysis",
            agent_type="data_analysis_specialist",
            capability=BaseCapability.CODE_EXECUTION,
            task={"analysis_type": "statistical", "variables": ["price", "volume"]},
            dependencies=["collect_web_data", "collect_internal_data"],
            priority=TaskPriority.HIGH
        ),
        WorkflowStep(
            step_id="ml_modeling",
            agent_type="data_analysis_specialist",
            capability=BaseCapability.CODE_EXECUTION,
            task={"model_type": "regression", "features": ["trend", "seasonality"]},
            dependencies=["collect_web_data", "collect_internal_data"],
            priority=TaskPriority.HIGH
        ),
        
        # Fase 3: Validación
        WorkflowStep(
            step_id="validate_analysis",
            agent_type="verifier",
            capability=AgentCapability.QUALITY_VALIDATION,
            task={"quality_threshold": 0.85, "validation_criteria": ["accuracy", "completeness"]},
            dependencies=["statistical_analysis", "ml_modeling"],
            priority=TaskPriority.HIGH
        )
    ]
    
    # Crear pipeline
    pipeline_id = await orchestrator.create_workflow(
        objective="Pipeline completo de análisis de datos de mercado",
        workflow_steps=pipeline_steps,
        priority=TaskPriority.CRITICAL
    )
    
    return pipeline_id

# Ejecutar pipeline
pipeline_id = await create_data_analysis_pipeline()
print(f"Pipeline iniciado: {pipeline_id}")

# Monitorear progreso
while True:
    status = await orchestrator.get_workflow_status(pipeline_id)
    print(f"Progreso: {status['progress']:.1%} - Paso {status['current_step_index'] + 1}/{status['total_steps']}")
    
    if status['state'] == 'completed':
        print("¡Pipeline completado exitosamente!")
        break
    elif status['state'] == 'failed':
        print(f"Pipeline falló: {status['error_message']}")
        break
    
    await asyncio.sleep(2)
```

## Mejores Prácticas

### 1. **Diseño de Workflows**
- Mantener pasos granulares para mejor paralelización
- Usar dependencias claras para control de flujo
- Establecer timeouts apropiados para cada paso
- Priorizar workflows críticos apropiadamente

### 2. **Gestión de Agentes**
- Registrar agentes especializados con metadatos útiles
- Monitorear health de agentes regularmente
- Configurar circuit breakers apropiadamente
- Usar load balancing según el caso de uso

### 3. **Monitoreo y Alertas**
- Configurar callbacks de alerta para problemas de salud
- Monitorear métricas de rendimiento regularmente
- Establecer thresholds apropiados para auto-scaling
- Revisar logs de errores para optimización

### 4. **Escalabilidad**
- Configurar límites apropiados de concurrencia
- Usar cola prioritaria para workflows críticos
- Implementar cleanup de workflows completados
- Optimizar资源配置 basada en patrones de uso

## Troubleshooting

### Problemas Comunes

#### Workflows No Se Ejecutan
```python
# Verificar estado del orquestrador
status = await orchestrator.get_orchestrator_status()
print(f"Workers activos: {len(orchestrator.worker_tasks)}")
print(f"Agentes disponibles: {len(orchestrator._get_all_agents())}")

# Verificar cola de tareas
queue_size = await orchestrator.task_queue.get_queue_size()
print(f"Tareas en cola: {queue_size}")
```

#### Agentes No Disponibles
```python
# Listar agentes registrados
response = await orchestrator.process_request({"type": "list_agents"})
print(f"Agentes: {response['agents']}")

# Verificar health de agentes
health = await orchestrator.health_check()
print(f"Health status: {health}")
```

#### Circuit Breakers Abiertos
```python
# Verificar circuit breakers
status = await orchestrator.get_orchestrator_status()
circuits = status["circuit_breakers"]

for agent, state in circuits.items():
    if state == "open":
        print(f"⚠️ Circuit breaker abierto para {agent}")
```

## API Reference

### Clases Principales

#### MultiAgentOrchestratorAgentWrapper
- `__init__()`: Inicializar orquestrador
- `register_specialized_agent()`: Registrar agente especializado
- `create_workflow()`: Crear y ejecutar workflow
- `get_workflow_status()`: Obtener estado de workflow
- `cancel_workflow()`: Cancelar workflow
- `get_orchestrator_status()`: Estado completo del orquestrador

#### WorkflowStep
- `step_id`: Identificador único del paso
- `agent_type`: Tipo de agente a ejecutar
- `capability`: Capacidad requerida del agente
- `task`: Datos de la tarea
- `dependencies`: Lista de dependencias
- `parallel_group`: Grupo para ejecución paralela
- `priority`: Prioridad del paso

#### WorkflowExecution
- Representación completa de un workflow en ejecución
- Estados: CREATED, QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED
- Progreso y métricas de ejecución

### Enums

#### TaskPriority
- LOW (1), NORMAL (2), HIGH (3), URGENT (4), CRITICAL (5)

#### WorkflowState
- CREATED, QUEUED, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED, RETRYING

#### LoadBalancingStrategy
- ROUND_ROBIN, LEAST_CONNECTIONS, WEIGHTED_RANDOM, FASTEST_RESPONSE, CAPABILITY_BASED

## Soporte y Contribución

Para problemas, características o contribuciones, consulte la documentación del proyecto MCP Core Superior.

---

**Multi-Agent Orchestrator Agent MCP** - Orquestación empresarial de agentes inteligentes 🚀