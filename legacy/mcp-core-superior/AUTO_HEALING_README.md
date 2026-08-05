# Sistema de Auto-Healing para MCP Core Superior

Sistema avanzado de recuperación automática y manejo inteligente de errores para MCP Core Superior.

## 🎯 Características Principales

### 1. Circuit Breaker Patterns
- **CircuitBreaker**: Implementación del patrón Circuit Breaker para prevenir cascadas de fallos
- **Estados**: CLOSED, OPEN, HALF_OPEN con transiciones automáticas
- **Fallback Strategies**: Respuestas de respaldo cuando el servicio está disponible
- **Configuración por Agente**: Umbrales y timeouts específicos por agente

### 2. Automatic Agent Restart y Health Recovery
- **Restart Automático**: Reinicio inteligente de agentes fallidos
- **Health Monitoring**: Monitoreo continuo del estado de salud de agentes
- **Recovery Strategies**: Múltiples estrategias de recuperación (restart, graceful degradation, circuit breaker)
- **Cooldown Management**: Gestión inteligente de tiempos de espera entre recuperaciones

### 3. Predictive Failure Detection con ML
- **PredictiveFailureDetector**: Detector de fallos predictivo usando análisis de métricas
- **Pattern Analysis**: Análisis de tendencias y patrones en métricas históricas
- **Risk Scoring**: Cálculo de scores de riesgo para diferentes métricas
- **Anomaly Detection**: Detección automática de anomalías en rendimiento

### 4. Intelligent Fallback Strategies
- **Graceful Degradation**: Degradación elegante cuando los servicios están degradados
- **Backup Systems**: Activación automática de sistemas de respaldo
- **Configuration Adjustment**: Ajuste dinámico de configuraciones para operación degradada
- **Priority-based Recovery**: Recuperación basada en prioridades de agentes

### 5. Self-healing Configuration Adjustments
- **Dynamic Thresholds**: Umbrales dinámicos que se ajustan automáticamente
- **Runtime Configuration**: Configuración en tiempo real sin reinicio
- **Configuration Validation**: Validación automática de configuraciones
- **Environment-aware Settings**: Configuraciones específicas por entorno

### 6. Automatic Resource Rebalancing
- **Auto Scaling**: Escalado automático basado en métricas de uso
- **Load Distribution**: Distribución inteligente de carga entre instancias
- **Resource Monitoring**: Monitoreo continuo de uso de recursos
- **Cost Optimization**: Optimización automática de costos de recursos

### 7. Error Pattern Analysis y Prevention
- **Pattern Recognition**: Reconocimiento de patrones en errores
- **Root Cause Analysis**: Análisis automático de causas raíz
- **Prevention Strategies**: Estrategias preventivas basadas en patrones históricos
- **Alert Management**: Gestión inteligente de alertas

### 8. Graceful Degradation
- **Service Levels**: Múltiples niveles de degradación (healthy, degraded, critical)
- **Feature Toggling**: Activación/desactivación dinámica de características
- **Performance Scaling**: Escalado de rendimiento según capacidad disponible
- **User Impact Minimization**: Minimización del impacto en usuarios finales

### 9. Performance Anomaly Detection
- **Real-time Monitoring**: Monitoreo en tiempo real de métricas de rendimiento
- **Statistical Analysis**: Análisis estadístico de tendencias de rendimiento
- **Baseline Comparison**: Comparación con líneas base de rendimiento
- **Automated Response**: Respuesta automática a anomalías detectadas

### 10. Automated Scaling Basada en Health Metrics
- **Health-based Scaling**: Escalado basado en métricas de salud
- **Multi-metric Decisions**: Decisiones de escalado basadas en múltiples métricas
- **Predictive Scaling**: Escalado predictivo basado en tendencias
- **Cooldown Management**: Gestión de tiempos de espera entre escalados

## 📁 Estructura del Sistema

```
src/core/
├── auto_healing_engine.py          # Motor principal de auto-healing
├── health_metrics.py               # Sistema de métricas de salud
├── auto_healing_config.py          # Configuración avanzada
└── healing_integration.py          # Integración con FastMCP Server
```

### Componentes Principales

#### 1. AutoHealingEngine
```python
from src.core import AutoHealingEngine, get_auto_healing_engine

# Crear instancia
engine = AutoHealingEngine()
await engine.initialize()

# Obtener instancia global
engine = await get_auto_healing_engine()

# Estado del sistema
status = engine.get_health_status()
```

#### 2. HealthMetricsCollector
```python
from src.core import HealthMetricsCollector, get_metrics_collector

# Crear recolector
collector = HealthMetricsCollector(collection_interval=10)
await collector.start_collection()

# Métricas actuales
metrics = collector.get_current_metrics()

# Reporte de rendimiento
from src.core import MetricsAggregator
aggregator = MetricsAggregator(collector)
report = aggregator.generate_performance_report(timedelta(hours=1))
```

#### 3. ConfigurationManager
```python
from src.core import get_config_manager

# Obtener gestor
manager = await get_config_manager()
config = manager.get_config()

# Actualizar configuración
updates = {
    "global_thresholds": {
        "cpu_warning": 65.0,
        "memory_warning": 75.0
    }
}
await manager.update_config(updates)
```

## 🛠️ Uso Básico

### 1. Integración Simple
```python
from src.core import AutoHealingMixin

class MyAgent(AutoHealingMixin):
    async def process_task(self, task):
        try:
            # Lógica del agente
            result = await self._do_work(task)
            
            # Reportar métricas de éxito
            await self.report_metrics({
                "cpu_usage": 45.0,
                "memory_usage": 60.0,
                "response_time": 1.2,
                "error_rate": 0.02,
                "health_score": 0.95
            })
            
            return result
            
        except Exception as e:
            # Reportar error
            await self.report_error(e, {"task": task})
            raise
```

### 2. Integración Completa con Servidor
```python
from src.core import with_healing_integration

@with_healing_integration
class MyMCPServer:
    async def start(self):
        # El servidor se inicializa automáticamente con auto-healing
        pass
    
    def is_healing_active(self) -> bool:
        return self.healing_integration.is_active()
```

### 3. Herramientas MCP de Auto-Healing
```python
# El sistema añade automáticamente estas herramientas MCP:

# 1. get_healing_status() - Estado del sistema de auto-healing
# 2. force_agent_recovery(agent_name, strategy) - Forzar recuperación
# 3. get_failure_predictions() - Predicciones de fallo
# 4. update_healing_config(updates) - Actualizar configuración
# 5. get_performance_report(hours) - Reporte de rendimiento
```

## ⚙️ Configuración

### Archivo de Configuración (auto_healing_config.json)
```json
{
  "enabled": true,
  "debug_mode": false,
  "monitoring_interval": 10,
  "global_thresholds": {
    "cpu_warning": 70.0,
    "cpu_critical": 85.0,
    "memory_warning": 75.0,
    "memory_critical": 90.0,
    "response_time_warning": 1.0,
    "response_time_critical": 2.5,
    "error_rate_warning": 0.05,
    "error_rate_critical": 0.10
  },
  "agent_configs": {
    "executor": {
      "min_instances": 2,
      "max_instances": 8,
      "circuit_breaker_failure_threshold": 5,
      "recovery_strategies": ["restart_agent", "graceful_degradation"]
    }
  }
}
```

### Configuración por Entorno
- **Development**: Debug habilitado, thresholds más permisivos
- **Staging**: Configuración intermedia, logging detallado
- **Production**: Configuración optimizada, alertas habilitadas

## 📊 Monitoreo y Observabilidad

### Métricas Principales
- **System Metrics**: CPU, Memory, Disk, Network
- **Application Metrics**: Response Time, Throughput, Error Rate
- **Agent Metrics**: Execution Time, Success Rate, Queue Size
- **Health Scores**: Scores agregados de salud por componente

### Endpoints de Monitoreo
```python
# Estado del sistema
GET /mcp/tools/get_healing_status

# Predicciones de fallo
GET /mcp/tools/get_failure_predictions

# Reporte de rendimiento
GET /mcp/tools/get_performance_report

# Control de recovery
POST /mcp/tools/force_agent_recovery

# Configuración
POST /mcp/tools/update_healing_config
```

### Integración con Prometheus/Grafana
El sistema está preparado para exportar métricas a Prometheus:
```python
# Métricas exportadas automáticamente:
# - mcp_agent_health_score
# - mcp_agent_failure_probability
# - mcp_system_cpu_usage
# - mcp_system_memory_usage
# - mcp_recovery_attempts_total
# - mcp_circuit_breaker_state
```

## 🚀 Ejemplo Completo

```python
import asyncio
from src.core import (
    get_auto_healing_engine,
    get_metrics_collector,
    get_config_manager
)

async def main():
    # 1. Inicializar componentes
    engine = await get_auto_healing_engine()
    collector = await get_metrics_collector()
    config_manager = await get_config_manager()
    
    # 2. Activar auto-healing
    config = config_manager.get_config()
    if config.enabled:
        print("Auto-healing enabled")
    
    # 3. Simular métricas de agentes
    from src.core import HealthMetrics, ErrorEvent
    from datetime import datetime
    import random
    
    for i in range(10):
        for agent_name in ["reasoner", "planner", "executor"]:
            metrics = HealthMetrics(
                timestamp=datetime.now(),
                agent_name=agent_name,
                cpu_usage=random.uniform(20, 90),
                memory_usage=random.uniform(30, 80),
                response_time=random.uniform(0.1, 2.0),
                error_rate=random.uniform(0, 0.1),
                throughput=random.uniform(10, 50),
                active_tasks=random.randint(0, 5),
                queue_size=random.randint(0, 10),
                health_score=random.uniform(0.3, 1.0)
            )
            await engine.record_health_metrics(agent_name, metrics)
    
    # 4. Obtener estado y predicciones
    status = engine.get_health_status()
    predictions = engine.get_failure_predictions()
    
    print("Estado del sistema:", status["overall_status"])
    print("Predicciones:", predictions)
    
    # 5. Obtener reporte de rendimiento
    from src.core import MetricsAggregator
    aggregator = MetricsAggregator(collector)
    report = aggregator.generate_performance_report()
    print("Reporte:", report)

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔧 Integración con Sistema Existente

### 1. Modificar FastMCPServer
```python
# En fastmcp_server.py
from src.core import HealingIntegration

class MCPCoreServer:
    def __init__(self):
        # ... código existente ...
        self.healing_integration = None
    
    async def initialize(self):
        # ... inicialización existente ...
        
        # Inicializar auto-healing
        self.healing_integration = HealingIntegration(self)
        await self.healing_integration.initialize()
```

### 2. Health Checks en Agentes
```python
# En cada agent wrapper
async def health_check(self) -> Dict[str, Any]:
    """Health check con métricas para auto-healing"""
    try:
        # Lógica de health check existente
        status = await self._do_health_check()
        
        # Enriquecer con métricas
        status["metrics"] = {
            "cpu_usage": await self._get_cpu_usage(),
            "memory_usage": await self._get_memory_usage(),
            "response_time": await self._get_avg_response_time(),
            "error_rate": await self._get_error_rate(),
            "throughput": await self._get_throughput(),
            "active_tasks": len(self.active_tasks),
            "queue_size": len(self.task_queue)
        }
        
        return status
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "metrics": {}
        }
```

## 📈 Escalabilidad y Rendimiento

### Optimizaciones Implementadas
- **Async/Await**: Todo el sistema usa async/await para no bloquear
- **Connection Pooling**: Reutilización de conexiones de base de datos
- **Memory Management**: Gestión eficiente de memoria con límites
- **Batched Operations**: Operaciones en lote para reducir overhead
- **Background Tasks**: Tareas en background para monitoreo no bloqueante

### Límites Configurables
- **Métricas**: Máximo 1000 mediciones del sistema, 500 por agente
- **Errores**: Máximo 1000 errores en historial
- **Recovery Attempts**: Máximo 5 intentos de recovery por agente
- **Circuit Breaker**: Timeout configurable (default: 60s)

## 🔒 Seguridad

### Características de Seguridad
- **Validation**: Validación de todas las configuraciones
- **Error Sanitization**: Sanitización de mensajes de error
- **Access Control**: Control de acceso a herramientas de healing
- **Audit Logging**: Logging detallado de todas las acciones

### Mejores Prácticas
- **Production Settings**: Usar configuraciones de producción específicas
- **Monitoring**: Monitoreo continuo del sistema de auto-healing
- **Backup**: Backups automáticos de configuraciones
- **Recovery Testing**: Testing regular de procedimientos de recovery

## 🐛 Troubleshooting

### Problemas Comunes

#### 1. Auto-healing no se activa
```bash
# Verificar configuración
cat auto_healing_config.json | jq .enabled

# Verificar logs
grep -i "auto.healing" logs/mcp-core.log
```

#### 2. Circuit breaker permanece abierto
```python
# Verificar estado
status = await get_auto_healing_engine()
circuit_state = status["circuit_breakers"]["agent_name"]

# Reset manual
await engine.force_recovery("agent_name", RecoveryStrategy.RESTART_AGENT)
```

#### 3. Métricas no se recopilan
```python
# Verificar recolector
collector = get_metrics_collector()
if not collector.is_collecting:
    await collector.start_collection()
```

### Logs Útiles
```bash
# Logs de auto-healing
tail -f logs/mcp-core.log | grep -E "(healing|circuit|recovery)"

# Logs de métricas
tail -f logs/mcp-core.log | grep -E "(metrics|collector)"

# Logs de configuración
tail -f logs/mcp-core.log | grep -E "(config|threshold)"
```

## 📚 API Reference

### AutoHealingEngine
```python
class AutoHealingEngine:
    async def initialize()
    async def record_health_metrics(agent_name, metrics)
    async def record_error(error_event)
    async def force_recovery(agent_name, strategy=None)
    def get_health_status() -> Dict[str, Any]
    def get_failure_predictions() -> Dict[str, float]
    def get_anomalies() -> List[Dict[str, Any]]
    async def cleanup()
```

### HealthMetricsCollector
```python
class HealthMetricsCollector:
    async def start_collection()
    async def stop_collection()
    def record_response_time(endpoint, time)
    def record_execution_time(agent, time)
    def get_current_metrics() -> Dict[str, Any]
    def get_metrics_history(type, agent=None, time_range=None)
    def get_performance_summary() -> Dict[str, Any]
```

### ConfigurationManager
```python
class ConfigurationManager:
    async def initialize()
    def get_config() -> AutoHealingConfiguration
    def get_agent_config(agent_name) -> AgentSpecificConfig
    async def update_config(updates) -> bool
    async def save_config(file_path=None) -> bool
    def register_config_watcher(callback)
```

## 🤝 Contribución

Para contribuir al sistema de auto-healing:

1. **Testing**: Asegurar que las pruebas pasen
2. **Documentation**: Actualizar documentación para nuevos features
3. **Performance**: Mantener el rendimiento del sistema
4. **Compatibility**: Mantener compatibilidad con versiones anteriores

### Ejecutar Tests
```bash
# Tests del sistema de auto-healing
python -m pytest tests/test_auto_healing/ -v

# Tests de integración
python -m pytest tests/test_integration/test_healing_integration.py -v

# Demo completa
python examples/auto_healing_example.py
```

## 📄 Licencia

Este sistema de auto-healing es parte de MCP Core Superior y mantiene la misma licencia.

---

**MCP Core Superior - Sistema de Auto-Healing Avanzado**  
*Recuperación automática, manejo inteligente de errores, y escalado predictivo para sistemas multi-agente*