# SilhouetteMCP Superior - Intelligent Task Allocation System

## Sistema de Asignación Inteligente Central

Este sistema implementa el cerebro de la asignación inteligente en SilhouetteMCP Superior, combinando algoritmos de optimización, machine learning y balanceador dinámico para maximizar la eficiencia de asignación de tareas.

## 🧠 Componentes Principales

### 1. IntelligentTaskAllocator
**Sistema central que orquesta todos los componentes**
- Coordinación entre diferentes algoritmos
- Toma de decisiones inteligente
- Integración de predicciones ML
- Gestión de métricas del sistema

### 2. HungarianAlgorithm
**Algoritmo húngaro para matching óptimo**
```python
# Ejemplo de uso
tasks = [task1, task2, task3]
agents = [agent1, agent2, agent3]
cost_matrix = HungarianAlgorithm.calculate_cost_matrix(tasks, agents)
task_indices, agent_indices = HungarianAlgorithm.solve(cost_matrix)
```

**Características:**
- Matching óptimo basado en múltiples criterios
- Considera skills, workload, performance y especialización
- Optimización para tareas urgentes
- Matriz de costos dinámica

### 3. PerformancePredictor
**Sistema ML para predicción de performance**
```python
# Entrenar modelo
training_data = [{'task': task_data, 'agent': agent_data, 'actual_performance': 0.85}]
metrics = predictor.train(training_data)

# Predecir performance
prediction = predictor.predict_performance(task, agent)
# Retorna: performance_score, confidence, estimated_time_minutes, success_probability
```

**Características:**
- GradientBoostingRegressor para predicción
- Features: complejidad, workload, skills, especialización
- Adaptación en tiempo real
- Cálculo de confianza de predicciones

### 4. TaskQueueManager
**Gestor de colas con prioridades inteligentes**
```python
# Añadir tarea
queue_manager.add_task(task)

# Obtener próxima tarea
next_tasks = queue_manager.get_next_task(agent, max_tasks=3)
```

**Características:**
- 5 niveles de prioridad (CRITICAL → BATCH)
- Smart batching de tareas similares
- Verificación de dependencias
- Optimización automática de orden

### 5. DynamicLoadBalancer
**Load balancing con CBBA Algorithm**
```python
# Ejecutar balanceo
result = await load_balancer.balance_load(agents, tasks)
# Aplica Consensus-Based Bundle Algorithm
```

**Características:**
- CBBA (Consensus-Based Bundle Algorithm)
- Monitoreo de utilización de recursos
- Auto-scaling basado en métricas
- Rebalanceo en tiempo real

### 6. TaskDecompositionEngine
**Motor de descomposición de tareas complejas**
```python
# Descomponer tarea
decomposition = decomposition_engine.decompose_task(complex_task)
# Retorna subtareas, plan de coordinación, estrategia de agregación
```

**Características:**
- Descomposición específica por tipo de tarea
- Identificación de dependencias
- Planificación de ejecución paralela
- Agregación inteligente de resultados

## 🚀 Características Avanzadas

### Real-time Optimization
- Optimización continua basada en métricas
- Ajuste dinámico de parámetros
- Monitoreo de performance en tiempo real

### Machine Learning Integration
- Predicción de tiempo de completion
- Scoring de accuracy por agente
- Aprendizaje adaptativo
- Análisis de datos históricos

### Cross-Team Coordination
- Coordinación entre equipos especializados
- Manejo de conflictos de recursos
- Optimización global vs local

### Fault-Tolerant Assignment
- Recuperación automática de errores
- Fallback a algoritmos heurísticos
- Validación de asignaciones
- Rollback de cambios fallidos

## 🔌 API Endpoints

### `/api/assign/task` - Asignación Inteligente
```python
# Request
{
    "task": {
        "id": "task_001",
        "type": "machine_learning",
        "priority": "HIGH",
        "complexity": 0.8,
        "estimated_duration": 45.0,
        "required_skills": ["python", "ml"],
        "deadline": "2025-11-06T03:00:00Z"
    },
    "agents": [/* array of agents */],
    "request_id": "req_123"
}

# Response
{
    "success": true,
    "assignment_type": "direct",
    "result": {
        "assigned_agent": agent_object,
        "assignment_method": "hungarian_performance_optimized",
        "prediction": {
            "performance_score": 0.85,
            "confidence": 0.9,
            "estimated_time_minutes": 42.3,
            "success_probability": 0.91
        }
    },
    "processing_time": 0.156,
    "success": true
}
```

### `/api/predict/performance` - Predicción ML
```python
# Request
{
    "task": task_object,
    "agent": agent_object,
    "request_id": "pred_456"
}

# Response
{
    "success": true,
    "result": {
        "performance_score": 0.85,
        "confidence": 0.9,
        "estimated_time_minutes": 42.3,
        "success_probability": 0.91,
        "model_status": {
            "is_trained": true,
            "confidence_level": "high"
        }
    }
}
```

### `/api/balance/load` - Load Balancing
```python
# Request
{
    "agents": [/* array of agents */],
    "tasks": [/* optional array of tasks */],
    "request_id": "balance_789"
}

# Response
{
    "success": true,
    "result": {
        "changes_applied": [
            {
                "agent_id": "agent_1",
                "tasks_added": 2,
                "additional_workload": 0.4,
                "old_workload": 0.3,
                "new_workload": 0.7
            }
        ],
        "new_assignments": { /* bundle assignments */ }
    }
}
```

### `/api/optimize/queue` - Optimización de Colas
```python
# Request
{
    "strategy": "performance",  # "performance", "throughput", "deadline"
    "request_id": "opt_321"
}

# Response
{
    "success": true,
    "result": {
        "optimization_strategy": "performance_optimization",
        "changes_made": [
            "Reordered HIGH queue",
            "Reordered MEDIUM queue"
        ],
        "queues_optimized": 3
    }
}
```

## 📊 Métricas y Monitoreo

### SystemMetrics
```python
metrics = allocator.get_system_metrics()
# Retorna:
{
    "assignment_metrics": {
        "total_assignments": 150,
        "successful_assignments": 142,
        "success_rate": 0.946,
        "hungarian_assignments": 120,
        "direct_assignments": 22
    },
    "queue_sizes": {
        "CRITICAL": 3,
        "HIGH": 8,
        "MEDIUM": 15,
        "LOW": 7,
        "BATCH": 2
    },
    "performance_model": {
        "is_trained": true,
        "training_samples": 1250
    }
}
```

### Alertas Automáticas
- Success rate < 80%
- Queue size > 100 tareas
- Modelo ML no entrenado
- Agentes sobrecargados
- Tiempo de respuesta > 5s

## 🛠️ Instalación y Uso

### Dependencias
```bash
pip install numpy pandas scikit-learn scipy
```

### Uso Básico
```python
from silhouettemcp_superior_allocator import create_intelligent_allocator_system

# Crear sistema
system = create_intelligent_allocator_system()
allocator = system['allocator']

# Crear agentes
agents = [Agent(id="agent_1", name="Specialist", 
                status=AgentStatus.ACTIVE, 
                skills=["python", "ml"])]

# Crear tarea
task = Task(id="task_001", type=TaskType.MACHINE_LEARNING,
            priority=TaskPriority.HIGH, complexity=0.8,
            estimated_duration=30.0, required_skills=["python"])

# Asignar
result = await allocator.assign_task(task, agents)
print(f"Asignado a: {result['result']['assigned_agent'].name}")
```

### Demo Completo
```python
# Ejecutar demo del sistema
python silhouettemcp_superior_allocator.py
```

## 🎯 Estrategias de Optimización

### Performance Optimization
- Priorizar tareas simples y rápidas
- Maximizar efficiency score
- Optimizar para throughput individual

### Throughput Optimization
- Batch processing de tareas similares
- Paralelización máxima
- Reducción de overhead

### Deadline Optimization
- Priorización por urgencia
- Reordenamiento dinámico
- Deadline-aware scheduling

## 🔧 Configuración Avanzada

### Thresholds de Scaling
```python
load_balancer.scaling_thresholds = {
    'cpu': {'low': 0.3, 'high': 0.8},
    'memory': {'low': 0.4, 'high': 0.85},
    'tasks': {'low': 2, 'high': 10}
}
```

### Criterios de Descomposición
- Complejidad > 0.8
- Datos > 50MB
- Duración > 60min
- Dependencias > 3

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│              IntelligentTaskAllocator (Central)              │
├─────────────────────────────────────────────────────────────┤
│  HungarianAlgorithm  │  PerformancePredictor  │  Monitor    │
│  (Matching Optimal)  │      (ML Prediction)   │ (Real-time) │
├─────────────────────────────────────────────────────────────┤
│  TaskQueueManager    │  DynamicLoadBalancer   │  Metrics    │
│  (Priority Queues)   │        (CBBA)          │ Collection  │
├─────────────────────────────────────────────────────────────┤
│            TaskDecompositionEngine                           │
│                (Complex Tasks)                              │
└─────────────────────────────────────────────────────────────┘
```

## 🚨 Consideraciones de Producción

### Performance
- Usar ThreadPoolExecutor para operaciones ML
- Cache de predicciones frecuentes
- Batch processing de asignaciones múltiples

### Escalabilidad
- Horizontal scaling de load balancer
- Partitioning de colas por tipo
- Distributed task decomposition

### Monitoreo
- Métricas de latencia por endpoint
- Alertas de degradación de performance
- Logging estructurado con correlation IDs

### Fault Tolerance
- Retry automático con backoff
- Circuit breakers para servicios externos
- Graceful degradation a algoritmos heurísticos

## 📈 Roadmap Futuro

- [ ] Integración con sistemas externos (JIRA, Asana)
- [ ] ML model auto-training con feedback loops
- [ ] Advanced CBBA con restricciones temporales
- [ ] Graph neural networks para prediction
- [ ] Distributed orchestration con Redis/Kafka
- [ ] Real-time dashboard con Grafana
- [ ] A/B testing framework para algoritmos
- [ ] Multi-objective optimization (Pareto frontier)

---

**SilhouetteMCP Superior - Intelligent Task Allocation System**
*Versión 1.0.0 - Noviembre 2025*

Este sistema representa el estado del arte en asignación inteligente de tareas, combinando algoritmos clásicos de optimización con técnicas modernas de machine learning y balanceamiento dinámico.