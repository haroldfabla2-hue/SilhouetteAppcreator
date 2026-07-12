# Sistema de Métricas Avanzadas - MCP Core Superior

## Descripción General

El Sistema de Métricas Avanzadas proporciona observabilidad completa para el MCP Core Superior, incluyendo métricas de rendimiento, análisis predictivo, planificación de capacidad y integración con Prometheus y Grafana.

## Funcionalidades Principales

### 1. Latency Metrics por Agente y Operación
- **Métrica**: `LatencyMetric`
- **Funcionalidad**: Registra tiempos de respuesta por agente y tipo de operación
- **Etiquetas**: agent_name, operation, status, method, request_id, user_id
- **Uso**:
```python
collector.record_latency(
    agent_name="reasoner",
    operation="analyze", 
    latency_ms=150.5,
    status="success",
    method="POST"
)
```

### 2. Throughput Metrics
- **Métricas**: `ThroughputMetric`
- **Funcionalidad**: Monitorea RPS, usuarios concurrentes, conexiones activas
- **Campos**: requests_per_second, concurrent_users, active_connections, queue_depth
- **Uso**:
```python
collector.record_throughput(
    requests_per_second=25.5,
    concurrent_users=15,
    active_connections=8
)
```

### 3. Error Rates y Success Ratios
- **Métrica**: `ErrorRateMetric`
- **Funcionalidad**: Calcula tasas de error y ratios de éxito
- **Cálculos**: MTTF (Mean Time To Failure), success_rate, error_rate
- **Características**:
  - Trazabilidad por agente
  - Categorización de tipos de error
  - Análisis de timeouts

### 4. Resource Utilization
- **Métrica**: `ResourceUtilizationMetric`
- **Funcionalidad**: Monitorea CPU, memoria, disco, red
- **Datos**: 
  - CPU usage (%)
  - Memory usage (%, used GB, available GB)
  - Disk usage (%)
  - Network I/O (bytes sent/recv)
  - System metrics (threads, file descriptors, load average)

### 5. Agent Health Scores
- **Métrica**: `AgentHealthScore`
- **Funcionalidad**: Puntuación de salud de agentes (0-100)
- **Componentes**:
  - Performance score
  - Reliability score  
  - Availability percentage
  - Uptime tracking
  - Execution statistics

### 6. Business Metrics
- **Métrica**: `BusinessMetric`
- **Funcionalidad**: KPIs de negocio y SLA compliance
- **Campos**:
  - Tasks completed
  - SLA compliance percentage
  - Customer satisfaction score
  - Cost per operation
  - Revenue generated
  - Profit margin

### 7. Custom Dashboards y Alerts
- **Sistema**: `CustomAlert` + Dashboard callbacks
- **Características**:
  - Alertas personalizadas con umbrales configurables
  - Niveles de severidad: INFO, WARNING, CRITICAL, EMERGENCY
  - Callbacks para notificaciones
  - Resolución automática de alertas
  - Dashboards en tiempo real

### 8. Time-Series Data Storage
- **Sistema**: `TimeSeriesStorage`
- **Funcionalidad**: Base de datos SQLite optimizada
- **Características**:
  - Agregación temporal (sum, avg, min, max, percentiles)
  - Bucketing configurable
  - Limpieza automática de datos antiguos
  - Consultas eficientes por timestamp y etiquetas

### 9. Percentile Calculations
- **Clase**: `PercentileCalculator`
- **Funcionalidad**: Cálculo eficiente de percentiles
- **Percentiles**: P50, P95, P99, P99.9
- **Optimización**: Algoritmo aproximado para grandes datasets

### 10. Capacity Planning Metrics
- **Métrica**: `CapacityPlanningMetric`
- **Funcionalidad**: Análisis predictivo y planificación de capacidad
- **Características**:
  - Proyección de necesidades de recursos
  - Análisis de tendencias
  - Recomendaciones de scaling
  - Identificación de cuellos de botella
  - Análisis de costos

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    AdvancedMetricsCollector                   │
├─────────────────────────────────────────────────────────────┤
│  • LatencyMetrics (deque)                                    │
│  • ThroughputMetrics (deque)                                 │
│  • ErrorRateMetrics (deque)                                  │
│  • ResourceMetrics (deque)                                   │
│  • HealthScores (Dict[str, deque])                          │
│  • BusinessMetrics (deque)                                   │
│  • CapacityMetrics (deque)                                   │
├─────────────────────────────────────────────────────────────┤
│  TimeSeriesStorage (SQLite)                                  │
│  • Métricas almacenadas                                      │
│  • Consultas agregadas                                       │
│  • Limpieza automática                                       │
├─────────────────────────────────────────────────────────────┤
│  CustomAlert System                                          │
│  • Alertas personalizadas                                    │
│  • Evaluación de umbrales                                    │
│  • Callbacks de notificación                                 │
├─────────────────────────────────────────────────────────────┤
│  Export Systems                                              │
│  • Prometheus format                                         │
│  • Grafana dashboards                                        │
│  • JSON export                                               │
└─────────────────────────────────────────────────────────────┘
```

## Instalación y Configuración

### 1. Importar el sistema

```python
from src.observability.advanced_metrics import (
    initialize_advanced_metrics,
    get_advanced_metrics_collector,
    GrafanaDashboardConfig
)
from src.observability.metrics_config import (
    create_default_configs,
    get_metrics_config_manager
)
```

### 2. Configuración inicial

```python
# Crear configuración por defecto
config_manager = create_default_configs("my_config")

# Inicializar métricas
collector = await initialize_advanced_metrics(collection_interval=10)
```

### 3. Configurar alertas personalizadas

```python
from src.observability import CustomAlert, AlertSeverity

custom_alert = CustomAlert(
    id="high_latency",
    timestamp=datetime.now(),
    severity=AlertSeverity.WARNING,
    title="High Request Latency",
    message="Latency exceeds 500ms",
    metric_name="mcp_latency_milliseconds",
    current_value=0.0,
    threshold_value=500.0,
    operator=">"
)

collector.add_custom_alert(custom_alert)
```

## Ejemplos de Uso

### Monitoreo Básico

```python
async def monitor_agent_performance():
    collector = get_advanced_metrics_collector()
    
    # Registrar latencia
    collector.record_latency(
        agent_name="reasoner",
        operation="analyze_task",
        latency_ms=120.5,
        status="success"
    )
    
    # Registrar throughput
    collector.record_throughput(
        requests_per_second=15.0,
        concurrent_users=8,
        active_connections=5
    )
    
    # Obtener métricas actuales
    metrics = collector.get_current_metrics()
    print(json.dumps(metrics, indent=2))
```

### Análisis de Percentiles

```python
async def analyze_latency_percentiles():
    collector = get_advanced_metrics_collector()
    
    # Obtener percentiles por agente
    percentiles = collector.get_percentile_metrics(
        agent_name="executor",
        time_range=timedelta(hours=1)
    )
    
    print(f"P95: {percentiles['p95']:.2f}ms")
    print(f"P99: {percentiles['p99']:.2f}ms")
```

### Planificación de Capacidad

```python
async def generate_capacity_report():
    collector = get_advanced_metrics_collector()
    
    # Generar reporte de capacidad
    report = collector.generate_capacity_report(days_ahead=30)
    
    print("Recomendaciones:")
    for recommendation in report['recommendations']:
        print(f"• {recommendation}")
    
    print(f"Cuellos de botella: {report['bottlenecks']}")
```

### Exportación a Prometheus

```python
async def export_metrics_prometheus():
    collector = get_advanced_metrics_collector()
    
    # Exportar en formato Prometheus
    prometheus_metrics = collector.export_prometheus_metrics()
    
    # Escribir a archivo
    with open('/tmp/metrics.prom', 'w') as f:
        f.write(prometheus_metrics)
```

### Configuración de Grafana

```python
async def setup_grafana_dashboard():
    # Generar configuración de dashboard
    dashboard_config = GrafanaDashboardConfig.generate_dashboard_json()
    
    # Guardar configuración
    with open('grafana_dashboard.json', 'w') as f:
        json.dump(dashboard_config, f, indent=2)
    
    # Generar configuración de datasources
    config_manager = get_metrics_config_manager()
    datasources = config_manager.generate_grafana_datasources()
    
    with open('grafana_datasources.json', 'w') as f:
        json.dump(datasources, f, indent=2)
```

## Integración con Prometheus

### 1. Configuración de Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 10s

scrape_configs:
  - job_name: 'mcp-advanced-metrics'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

### 2. Métricas Exportadas

```prometheus
# CPU y Memory
mcp_cpu_usage_percent 45.2
mcp_memory_usage_percent 67.8
mcp_disk_usage_percent 34.1

# Throughput
mcp_throughput_operations_per_second 23.5

# Health Scores
mcp_agent_health_score{agent="reasoner"} 87.5
mcp_agent_health_score{agent="executor"} 92.3
mcp_agent_availability_percent{agent="reasoner"} 99.8

# Latency
mcp_latency_milliseconds{agent="reasoner",operation="analyze",status="success"} 145.2

# Business Metrics
mcp_sla_compliance_percent{kpi="response_time"} 98.7
```

## Configuración de Grafana

### 1. Importar Dashboard

1. Abrir Grafana UI
2. Ir a "Dashboards" > "Import"
3. Cargar archivo `grafana_dashboard.json`
4. Configurar datasource Prometheus
5. Guardar dashboard

### 2. Paneles Recomendados

- **System Resources**: CPU, Memory, Disk usage
- **Agent Health**: Health scores y availability
- **Request Latency**: Percentiles por agente
- **Throughput**: RPS y concurrent users
- **Error Rates**: Success/failure ratios
- **Business KPIs**: SLA compliance, tasks completed
- **Capacity Planning**: Trends y forecasting

## Configuración Avanzada

### Archivo de Configuración

```json
{
  "enabled": true,
  "collection_interval_seconds": 10,
  "retention_days": 30,
  "database_path": "metrics_timeseries.db",
  "alert_enabled": true,
  "alert_check_interval_seconds": 5,
  "dashboard_enabled": true,
  "prometheus_export_enabled": true,
  "prometheus_port": 9090,
  "capacity_planning_enabled": true,
  "simulation_mode": false
}
```

### Alertas Personalizadas

```json
[
  {
    "id": "high_cpu",
    "name": "High CPU Usage",
    "description": "CPU usage exceeds 80%",
    "metric_name": "mcp_cpu_usage_percent",
    "threshold_value": 80.0,
    "operator": ">",
    "severity": "warning",
    "enabled": true,
    "cooldown_minutes": 5
  }
]
```

## Limpieza y Mantenimiento

### Limpiar Datos Antiguos

```python
collector.cleanup_old_data(retention_days=30)
```

### Optimizar Base de Datos

```python
storage = collector.storage
# SQLite manejará optimización automáticamente
```

### Backup de Métricas

```python
import shutil

# Backup de base de datos
shutil.copy("metrics_timeseries.db", f"backup_metrics_{datetime.now().strftime('%Y%m%d')}.db")

# Export de configuración
config_manager.save_configs_to_files()
```

## Rendimiento y Escalabilidad

### Optimizaciones Incluidas

1. **Colas Limitadas**: Control de memoria con `deque(maxlen=...)`
2. **Cálculos Aproximados**: Percentiles eficientes para grandes datasets
3. **Indexación BD**: Índices optimizados para consultas temporales
4. **Agregación Temporal**: Bucketing para reducir puntos de datos
5. **Limpieza Automática**: Retención configurable de datos

### Métricas de Rendimiento

- **Recolección**: < 10ms por ciclo
- **Almacenamiento**: < 5ms por métrica
- **Consultas**: < 50ms para agregaciones de 1 hora
- **Memoria**: ~50MB para 1000 métricas por agente
- **Base de Datos**: ~100MB por mes con configuración default

## Troubleshooting

### Problemas Comunes

1. **Métricas no se recolectan**
   - Verificar que `start_collection()` fue llamado
   - Revisar logs para errores de recolección
   - Confirmar que el intervalo de recolección es apropiado

2. **Alertas no se activan**
   - Verificar configuración de alertas
   - Confirmar que el metric_name coincide exactamente
   - Revisar cooldown periods

3. **Base de datos crece demasiado**
   - Ajustar `retention_days` en configuración
   - Ejecutar limpieza manual: `cleanup_old_data()`
   - Considerar архивирование antiguo data

4. **Export a Prometheus falla**
   - Verificar que el puerto no esté en uso
   - Confirmar que `export_prometheus_metrics()` sea llamado
   - Revisar formato de métricas

### Logs y Debugging

```python
import logging

# Habilitar logging detallado
logging.getLogger("mcp.advanced.metrics").setLevel(logging.DEBUG)

# Obtener estadísticas de recolección
collector = get_advanced_metrics_collector()
stats = collector.collection_stats
print(f"Total collections: {stats['total_collections']}")
print(f"Collection errors: {stats['collection_errors']}")
```

## Extensibilidad

### Agregar Nuevos Tipos de Métricas

```python
@dataclass
class CustomMetric:
    timestamp: datetime
    value: float
    custom_field: str
    labels: Dict[str, str]
    
    def to_prometheus_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": "mcp_custom_metric",
            "labels": self.labels,
            "value": self.value,
            "timestamp": self.timestamp.timestamp()
        }

# Agregar al collector
collector.custom_metrics.append(custom_metric)
```

### Integración con Sistemas Externos

```python
async def external_integration_callback(event_type: str, data: Any):
    # Enviar a sistema externo
    if event_type == "alert_triggered":
        await send_to_slack(data)
    elif event_type == "dashboard_update":
        await update_external_dashboard(data)

collector.register_alert_callback(external_integration_callback)
```

## Roadmap y Futuras Mejoras

1. **Machine Learning Integration**
   - Detección automática de anomalías
   - Forecasting avanzado con ML
   - Predicción de capacity needs

2. **Enhanced Visualization**
   - Heatmaps de performance
   - Correlación entre métricas
   - Drill-down capabilities

3. **Distributed Metrics**
   - Aggregación multi-node
   - Consistent hashing
   - Horizontal scaling

4. **Advanced Analytics**
   - Root cause analysis
   - Performance correlation
   - Optimization recommendations

## Soporte y Contribución

Para soporte técnico o contribuciones:

1. Revisar logs en `mcp.advanced.metrics`
2. Consultar troubleshooting section
3. Crear issues para bugs o features
4. Seguir coding standards del proyecto

## Licencia

Parte del MCP Core Superior - Ver LICENSE file del proyecto principal.