# Intelligent Router - Sistema de AI-Powered Routing

## Descripción General

El **Intelligent Router** es un sistema avanzado de enrutamiento inteligente que utiliza Machine Learning, análisis semántico y optimización multi-objetivo para seleccionar automáticamente el agente óptimo para cada solicitud. Supera significativamente los sistemas de routing estático básicos mediante capacidades de aprendizaje automático y adaptación en tiempo real.

## 🚀 Características Principales

### 1. Machine Learning para Predicción de Performance
- **Modelo Predictivo**: Random Forest + Gradient Boosting para predecir:
  - Tiempo de respuesta esperado
  - Probabilidad de éxito
  - Costo estimado
- **Aprendizaje Continuo**: Auto-entrenamiento con nuevos datos
- **Features Avanzadas**: 15+ características contextuales y temporales

### 2. Dynamic Routing Basado en Datos Históricos
- **Histórico Completo**: Almacena hasta 50,000 decisiones de routing
- **Análisis de Tendencias**: Identifica patrones en performance de agentes
- **Adaptación Automática**: Ajusta pesos de estrategias basado en resultados

### 3. Context-Aware Decision Making
- **Contexto Rico**: Considera prioridad, complejidad, restricciones de tiempo/costo
- **Preferencias de Usuario**: Incorpora perfil y historial del usuario
- **Dominio Especializado**: Adapta decisiones al dominio de la solicitud

### 4. Real-Time Learning y Adaptation
- **Aprendizaje Online**: Actualiza modelo con cada resultado
- **Adaptación de Parámetros**: Ajusta pesos de estrategias automáticamente
- **Feedback Loop**: Ciclo completo de predicción → ejecución → aprendizaje

### 5. A/B Testing Framework
- **Experimentos Controlados**: Testeo de estrategias de routing
- **Análisis Estadístico**: Métricas de significancia y performance
- **Despliegue Gradual**: Traffic splitting automático

### 6. Performance Prediction Models
- **Predicción Multi-dimensional**: Tiempo, costo, precisión, confiabilidad
- **Modelos Ensamblados**: Combinación de múltiples algoritmos ML
- **Validación Continua**: Validación de predicciones vs resultados reales

### 7. Cost Optimization Algorithms
- **Optimización Multi-objetivo**: Balancea velocidad, precisión y costo
- **Restricciones Contextuales**: Respeta límites de tiempo y presupuesto
- **Perfiles de Costo**: Modelos específicos por tipo de agente

### 8. Multi-Objective Optimization
- **5 Objetivos Disponibles**: Speed, Accuracy, Cost, Reliability, Balanced
- **Pesos Dinámicos**: Ajuste automático de importancia de objetivos
- **Score Compuesto**: Algoritmo inteligente para combinar métricas

### 9. Semantic Routing con Embeddings
- **Análisis Semántico**: Usar embeddings para matching request-agent
- **Similitud Coseno**: Cálculo preciso de relevancia semántica
- **Cache de Embeddings**: Optimización de performance

### 10. Integración Completa con 12 Agentes
- **Registro Automático**: Detecta y registra agentes automáticamente
- **Capacidad Matching**: Selecciona agentes por capacidades específicas
- **Load Balancing**: Distribuye carga inteligentemente

## 📋 Estrategias de Routing

### 1. AI_OPTIMIZED (Recomendada)
- **Machine Learning**: Usa modelos predictivos entrenados
- **Multi-objetivo**: Optimiza según objetivo especificado
- **Adaptativo**: Mejora con cada interacción

### 2. SEMANTIC_MATCHING
- **Embeddings**: Usa análisis semántico para matching
- **Contexto Linguístico**: Considera significado de la solicitud
- **Similitud Alta**: Encuentra agentes semánticamente relevantes

### 3. PERFORMANCE_BASED
- **Histórico**: Basado en métricas históricas de agentes
- **Success Rate**: Prioriza agentes con alta tasa de éxito
- **Response Time**: Considera tiempo promedio de respuesta

### 4. LOAD_BALANCED
- **Distribución**: Balancea carga entre agentes disponibles
- **Utilización**: Considera ocupación actual de agentes
- **Escalabilidad**: Evita sobrecarga de agentes individuales

### 5. STATIC (Fallback)
- **Simplicidad**: Selecciona primer agente disponible
- **Fiable**: Siempre funciona como último recurso
- **Performance**: Sin overhead computacional

## 🎯 Objetivos de Optimización

### SPEED
- **Prioridad**: Minimizar tiempo de respuesta
- **Pesos**: 70% velocidad, 20% éxito, 10% costo
- **Ideal para**: Requests urgentes, time-sensitive

### ACCURACY
- **Prioridad**: Maximizar precisión de resultados
- **Pesos**: 10% velocidad, 80% éxito, 10% costo
- **Ideal para**: Análisis críticos, decisiones importantes

### COST
- **Prioridad**: Minimizar costo computacional
- **Pesos**: 20% velocidad, 20% éxito, 60% costo
- **Ideal para**: Presupuestos limitados, operaciones masivas

### RELIABILITY
- **Prioridad**: Maximizar confiabilidad y consistencia
- **Pesos**: 20% velocidad, 70% éxito, 10% costo
- **Ideal para**: Sistemas críticos, alta disponibilidad

### BALANCED (Por Defecto)
- **Prioridad**: Balance óptimo entre todas las métricas
- **Pesos**: 30% velocidad, 40% éxito, 30% costo
- **Ideal para**: Uso general, casos mixtos

## 🔧 Componentes Técnicos

### PerformancePredictor
```python
# Modelo ML que predice performance de agentes
class PerformancePredictor:
    - RandomForestRegressor: Predicción de tiempo de respuesta
    - GradientBoostingRegressor: Probabilidad de éxito
    - StandardScaler: Normalización de features
    - Auto-entrenamiento: Con datos de usage_history
```

### CostOptimizer
```python
# Optimizador multi-objetivo
class CostOptimizer:
    - calculate_composite_score: Score compuesto
    - _estimate_cost: Estimación de costos
    - _calculate_single_score: Score individual por agente
```

### ABTestManager
```python
# Gestor de experimentos A/B
class ABTestManager:
    - create_experiment: Crear nuevo experimento
    - get_strategy_for_user: Asignar variante a usuario
    - record_result: Registrar resultado de experimento
```

### IntelligentRouter
```python
# Router principal
class IntelligentRouter:
    - make_routing_decision: Decisión principal de routing
    - _ai_optimized_routing: Estrategia AI
    - _semantic_matching_routing: Matching semántico
    - record_routing_result: Registrar resultado
    - adapt_routing_parameters: Adaptación automática
```

## 📊 Métricas y Monitoring

### Métricas de Agente
- **Response Time**: Tiempo promedio de respuesta
- **Success Rate**: Tasa de éxito de operaciones
- **Utilization**: Utilización actual del agente
- **Error Rate**: Tasa de errores recientes

### Métricas de Routing
- **Total Decisions**: Número total de decisiones
- **Strategy Usage**: Frecuencia de uso por estrategia
- **Agent Usage**: Distribución de carga por agente
- **Confidence Scores**: Confianza promedio en decisiones

### Métricas de ML
- **Model Accuracy**: Precisión del modelo predictivo
- **Training Samples**: Muestras de entrenamiento
- **Prediction Errors**: Error de predicción vs realidad
- **Adaptation Events**: Eventos de adaptación de parámetros

## 🚀 Uso Básico

### Inicialización
```python
from src.core.intelligent_router import IntelligentRouter, intelligent_router

# Usar instancia global
router = intelligent_router

# O crear nueva instancia
router = IntelligentRouter()
```

### Registrar Agentes
```python
from src.agents.base_agent_wrapper import BaseAgentWrapper

# Registrar agente
await agent.ensure_initialized()
router.register_agent(agent)
```

### Realizar Decisión de Routing
```python
from src.core.intelligent_router import RoutingContext, RoutingStrategy, OptimizationObjective

# Crear contexto
context = RoutingContext(
    request_id="req_123",
    user_id="user_456",
    request_type="analysis",
    complexity_score=0.7,
    budget_constraints={"max_cost": 0.10}
)

# Request
request = {
    "query": "Análisis de sentimientos en reseñas",
    "capability": "intent_analysis"
}

# Tomar decisión
decision = await router.make_routing_decision(
    request=request,
    context=context,
    strategy=RoutingStrategy.AI_OPTIMIZED,
    objective=OptimizationObjective.ACCURACY
)

print(f"Agente: {decision.agent_name}")
print(f"Confianza: {decision.confidence:.3f}")
```

### Registrar Resultado
```python
performance = {
    "success_rate": 0.92,
    "response_time": 1.8,
    "cost": 0.05
}

router.record_routing_result(decision, performance, context)
```

### A/B Testing
```python
# Crear experimento
experiment_id = router.create_ab_test(
    name="AI_vs_Semantic",
    strategy_a=RoutingStrategy.AI_OPTIMIZED,
    strategy_b=RoutingStrategy.SEMANTIC_MATCHING,
    traffic_split=0.5,
    duration_days=7
)

# Obtener estrategia para usuario
strategy = ab_test_manager.get_strategy_for_user(
    experiment_id, "user_id"
)
```

## 🔄 Adaptación Automática

El router incluye un sistema de adaptación automática que:

1. **Monitorea Performance**: Analiza resultados de routing continuamente
2. **Detecta Degradación**: Identifica cuando estrategias específicas bajan su performance
3. **Ajusta Parámetros**: Modifica pesos de estrategias automáticamente
4. **Reentrena Modelos**: Actualiza modelos ML con nuevos datos

```python
# Habilitar adaptación
router.enable_adaptation(True)

# Adaptar manualmente
await router.adapt_routing_parameters()

# Obtener estadísticas
stats = router.get_routing_statistics()
```

## 📈 Configuración Avanzada

### Pesos de Estrategias
```python
# Ajustar pesos de estrategias
router.strategy_weights = {
    RoutingStrategy.AI_OPTIMIZED: 0.5,
    RoutingStrategy.SEMANTIC_MATCHING: 0.3,
    RoutingStrategy.PERFORMANCE_BASED: 0.15,
    RoutingStrategy.LOAD_BALANCED: 0.05
}
```

### Pesos de Costos
```python
router.cost_optimizer.cost_weights = {
    "response_time": 0.4,
    "success_probability": 0.4,
    "actual_cost": 0.2
}
```

### Persistencia
```python
# Guardar estado
router.save_state("/path/to/router_state")

# Cargar estado
router.load_state("/path/to/router_state")
```

## 🧪 Testing y Validación

El sistema incluye tests comprehensivos:

```bash
# Ejecutar tests del router
python -m pytest tests/test_intelligent_router.py -v

# Ejecutar demo completo
python examples/intelligent_router_demo.py
```

### Demo de Funcionalidades
```bash
python examples/intelligent_router_demo.py
```

El demo incluye:
- ✅ Routing básico con diferentes estrategias
- ✅ Matching semántico con embeddings
- ✅ Optimización multi-objetivo
- ✅ A/B testing de estrategias
- ✅ Adaptación automática
- ✅ Integración con agentes reales

## 🔍 Monitoreo y Debugging

### Logging
```python
import logging
logging.basicConfig(level=logging.INFO)

# Logs específicos del router
logger = logging.getLogger("mcp.router.intelligent")
```

### Métricas de Debug
```python
# Obtener estadísticas detalladas
stats = router.get_routing_statistics()

# Estado del modelo ML
print(f"ML entrenado: {router.predictor.is_trained}")
print(f"Muestras: {len(router.predictor.training_data)}")

# Cache de embeddings
print(f"Cache embeddings: {router.embedding_service.get_cache_stats()}")
```

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    Intelligent Router                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Performance    │  │  Cost           │  │   AB Test    │ │
│  │  Predictor      │  │  Optimizer      │  │   Manager    │ │
│  │  (ML Models)    │  │  (Multi-obj)    │  │  (Experiments│ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Embedding      │  │  Routing        │  │  Agent       │ │
│  │  Service        │  │  Strategies     │  │  Registry    │ │
│  │  (Semantic)     │  │  (5 types)      │  │  (12 agents) │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                 Core Components                             │
│  • Context Analysis  • Decision Making  • Result Recording │
│  • Adaptation Engine • Performance Tracking                │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 Casos de Uso Recomendados

### 1. Aplicaciones de Alto Volumen
- **Usar**: AI_OPTIMIZED + Balanced objective
- **Beneficio**: Maximiza throughput con calidad consistente

### 2. Análisis Críticos
- **Usar**: PERFORMANCE_BASED + Accuracy objective
- **Beneficio**: Asegura máxima precisión para decisiones importantes

### 3. Sistemas con Restricciones de Costo
- **Usar**: AI_OPTIMIZED + Cost objective
- **Beneficio**: Minimiza costos manteniendo calidad aceptable

### 4. Investigación y Desarrollo
- **Usar**: A/B testing entre estrategias
- **Beneficio**: Identifica estrategias óptimas para casos específicos

### 5. Sistemas Tiempo-Real
- **Usar**: LOAD_BALANCED + Speed objective
- **Beneficio**: Respeta constraints de latencia estricta

## 🚨 Consideraciones Importantes

### Performance
- **Memoria**: Mantiene hasta 50k decisiones en histórico
- **CPU**: Modelos ML requieren procesamiento adicional
- **Latencia**: +50ms overhead para decisiones AI-optimized

### Escalabilidad
- **Agentes**: Soporte nativo para 12+ agentes
- **Concurrent**: Thread-safe con locks por operación
- **Distribution**: Compatible con agentes distribuidos

### Monitoreo
- **ML Drift**: Monitorear accuracy del modelo predictivo
- **Strategy Performance**: Trackear performance por estrategia
- **Agent Health**: Verificar health de agentes registrados

## 🔮 Roadmap Futuro

### Versión 2.0
- [ ] **Deep Learning Models**: Transformer-based embeddings
- [ ] **Real-time Streaming**: Routing para streams de datos
- [ ] **Federated Learning**: Learning across multiple instances
- [ ] **Graph Neural Networks**: Modeling agent relationships

### Versión 2.1
- [ ] **Auto-scaling**: Dynamic agent provisioning
- [ ] **Predictive Routing**: Pre-emptive routing based on patterns
- [ ] **Multi-modal**: Support for image/audio requests
- [ ] **Edge Deployment**: Lightweight version for edge devices

---

**¡El Intelligent Router representa un salto cuántico en sistemas de routing para agentes AI!** 🚀

*Desarrollado con ❤️ para la comunidad MCP*