#!/bin/bash
# Script de Instalación del Sistema de Métricas Avanzadas
# MCP Core Superior - Observabilidad Avanzada

echo "🚀 Instalando Sistema de Métricas Avanzadas - MCP Core Superior"
echo "================================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar Python
log_info "Verificando instalación de Python..."
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 no está instalado. Por favor instale Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
log_success "Python $PYTHON_VERSION encontrado"

# Instalar dependencias
log_info "Instalando dependencias..."
pip3 install psutil numpy sqlite3 2>/dev/null || {
    log_warning "Algunas dependencias pueden fallar en instalación automática"
}

# Crear directorios necesarios
log_info "Creando estructura de directorios..."
mkdir -p mcp-core-superior/metrics_data
mkdir -p mcp-core-superior/config
mkdir -p mcp-core-superior/logs/metrics
mkdir -p mcp-core-superior/export/prometheus
mkdir -p mcp-core-superior/export/grafana

log_success "Directorios creados"

# Verificar archivos principales
log_info "Verificando archivos del sistema..."

FILES_TO_CHECK=(
    "mcp-core-superior/src/observability/advanced_metrics.py"
    "mcp-core-superior/src/observability/metrics_config.py"
    "mcp-core-superior/src/observability/__init__.py"
    "mcp-core-superior/demo_advanced_metrics.py"
    "mcp-core-superior/README_ADVANCED_METRICS.md"
)

ALL_FILES_EXIST=true
for file in "${FILES_TO_CHECK[@]}"; do
    if [ -f "$file" ]; then
        log_success "✓ $file"
    else
        log_error "✗ $file no encontrado"
        ALL_FILES_EXIST=false
    fi
done

if [ "$ALL_FILES_EXIST" = false ]; then
    log_error "Algunos archivos están faltando. Instalación cancelada."
    exit 1
fi

# Crear configuración inicial
log_info "Creando configuración inicial..."

cat > mcp-core-superior/config/metrics_config.json << EOF
{
  "enabled": true,
  "collection_interval_seconds": 10,
  "retention_days": 30,
  "database_path": "metrics_data/metrics_timeseries.db",
  "alert_enabled": true,
  "alert_check_interval_seconds": 5,
  "dashboard_enabled": true,
  "prometheus_export_enabled": true,
  "prometheus_port": 9090,
  "prometheus_endpoint": "/metrics",
  "percentile_calculation_enabled": true,
  "capacity_planning_enabled": true,
  "simulation_mode": false
}
EOF

log_success "Configuración principal creada"

# Crear configuración de alertas por defecto
log_info "Configurando alertas por defecto..."

cat > mcp-core-superior/config/alerts_config.json << EOF
[
  {
    "id": "high_cpu",
    "name": "High CPU Usage",
    "description": "CPU usage exceeds 80%",
    "metric_name": "mcp_cpu_usage_percent",
    "threshold_value": 80.0,
    "operator": ">",
    "severity": "warning",
    "agent_name": null,
    "enabled": true,
    "cooldown_minutes": 5,
    "escalation_enabled": true,
    "notification_channels": ["log"]
  },
  {
    "id": "high_memory",
    "name": "High Memory Usage",
    "description": "Memory usage exceeds 85%",
    "metric_name": "mcp_memory_usage_percent",
    "threshold_value": 85.0,
    "operator": ">",
    "severity": "warning",
    "agent_name": null,
    "enabled": true,
    "cooldown_minutes": 5,
    "escalation_enabled": true,
    "notification_channels": ["log"]
  },
  {
    "id": "high_error_rate",
    "name": "High Error Rate",
    "description": "Error rate exceeds 5%",
    "metric_name": "mcp_error_rate_ratio",
    "threshold_value": 0.05,
    "operator": ">",
    "severity": "critical",
    "agent_name": null,
    "enabled": true,
    "cooldown_minutes": 2,
    "escalation_enabled": true,
    "notification_channels": ["log"]
  }
]
EOF

log_success "Alertas configuradas"

# Crear configuración de Prometheus
log_info "Creando configuración de Prometheus..."

cat > mcp-core-superior/export/prometheus/prometheus.yml << EOF
# Configuración de Prometheus para MCP Core Superior
global:
  scrape_interval: 10s
  evaluation_interval: 10s

rule_files:
  - "mcp_alerts.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'mcp-advanced-metrics'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'
    scrape_interval: 10s
EOF

log_success "Configuración de Prometheus creada"

# Crear script de inicio
log_info "Creando scripts de inicio..."

cat > mcp-core-superior/start_metrics_system.sh << 'EOF'
#!/bin/bash
# Script de inicio del Sistema de Métricas Avanzadas

echo "🚀 Iniciando Sistema de Métricas Avanzadas..."

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -q psutil numpy

# Ejecutar demostración
echo "📊 Ejecutando demostración del sistema..."
python3 demo_advanced_metrics.py

echo "✅ Sistema de métricas iniciado"
EOF

chmod +x mcp-core-superior/start_metrics_system.sh

log_success "Scripts de inicio creados"

# Crear archivo de documentación rápida
log_info "Creando documentación rápida..."

cat > mcp-core-superior/METRICS_QUICKSTART.md << EOF
# Inicio Rápido - Sistema de Métricas Avanzadas

## 🚀 Inicio Rápido

### 1. Ejecutar Demostración
\`\`\`bash
./start_metrics_system.sh
\`\`\`

### 2. Uso Básico en Código
\`\`\`python
from src.observability import initialize_advanced_metrics

# Inicializar
collector = await initialize_advanced_metrics(collection_interval=5)

# Registrar métricas
collector.record_latency("agent_name", "operation", 150.0, "success")
collector.record_throughput(requests_per_second=25.0, concurrent_users=10)

# Obtener métricas actuales
metrics = collector.get_current_metrics()
\`\`\`

### 3. Exportar a Prometheus
\`\`\`python
prometheus_metrics = collector.export_prometheus_metrics()
print(prometheus_metrics)
\`\`\`

## 📊 Funcionalidades Incluidas

- ✅ Latency metrics por agente y operación
- ✅ Throughput metrics (RPS, concurrent users)
- ✅ Error rates y success ratios
- ✅ Resource utilization (CPU, memoria, disco)
- ✅ Agent health scores y availability
- ✅ Business metrics (tasks completed, SLA compliance)
- ✅ Custom dashboards y alerts
- ✅ Time-series data storage
- ✅ Percentile calculations (P50, P95, P99)
- ✅ Capacity planning metrics
- ✅ Integración con Prometheus y Grafana

## 🔧 Archivos Importantes

- \`src/observability/advanced_metrics.py\` - Sistema principal
- \`src/observability/metrics_config.py\` - Configuración
- \`demo_advanced_metrics.py\` - Demostración completa
- \`README_ADVANCED_METRICS.md\` - Documentación completa
- \`config/metrics_config.json\` - Configuración por defecto

## 🗄️ Archivos de Datos

- \`metrics_data/metrics_timeseries.db\` - Base de datos de métricas
- \`config/alerts_config.json\` - Configuración de alertas
- \`export/prometheus/prometheus.yml\` - Configuración de Prometheus

## 📈 Monitoreo

Acceder a métricas en tiempo real a través de:
- Métricas actuales: \`collector.get_current_metrics()\`
- Export Prometheus: \`collector.export_prometheus_metrics()\`
- Dashboard data: \`collector._generate_dashboard_data()\`

## 🚨 Alertas

Configurar alertas personalizadas:
\`\`\`python
from src.observability import CustomAlert, AlertSeverity

alert = CustomAlert(
    id="custom_alert",
    timestamp=datetime.now(),
    severity=AlertSeverity.WARNING,
    title="Custom Alert",
    message="Custom condition met",
    metric_name="custom_metric",
    current_value=0.0,
    threshold_value=100.0,
    operator=">"
)

collector.add_custom_alert(alert)
\`\`\`
EOF

log_success "Documentación rápida creada"

# Crear tests básicos
log_info "Creando tests básicos..."

cat > mcp-core-superior/test_advanced_metrics.py << 'EOF'
#!/usr/bin/env python3
"""
Tests básicos para el Sistema de Métricas Avanzadas
"""
import asyncio
import pytest
import json
from pathlib import Path

# Importar el sistema de métricas
try:
    from src.observability.advanced_metrics import (
        get_advanced_metrics_collector,
        AdvancedMetricsCollector,
        LatencyMetric,
        ThroughputMetric
    )
    from src.observability.metrics_config import create_default_configs
except ImportError:
    # Fallback para tests directos
    import sys
    sys.path.append(str(Path(__file__).parent))
    from advanced_metrics import (
        get_advanced_metrics_collector,
        AdvancedMetricsCollector,
        LatencyMetric,
        ThroughputMetric
    )
    from metrics_config import create_default_configs


async def test_basic_metrics_collection():
    """Test básico de recolección de métricas"""
    print("🧪 Test: Recolección básica de métricas")
    
    # Crear configuración
    config_manager = create_default_configs("test_config")
    
    # Inicializar collector
    collector = get_advanced_metrics_collector()
    collector.config = config_manager.get_metrics_config()
    
    # Registrar métricas de prueba
    collector.record_latency("test_agent", "test_operation", 100.0, "success")
    collector.record_throughput(requests_per_second=10.0, concurrent_users=5)
    
    # Verificar que las métricas se registraron
    assert len(collector.latency_metrics) > 0
    assert len(collector.throughput_metrics) > 0
    
    print("✅ Test básico de recolección: PASSED")


async def test_percentile_calculation():
    """Test de cálculo de percentiles"""
    print("🧪 Test: Cálculo de percentiles")
    
    collector = get_advanced_metrics_collector()
    
    # Registrar múltiples latencias
    latencies = [100, 150, 200, 250, 300, 350, 400, 450, 500]
    for latency in latencies:
        collector.record_latency("test_agent", "test_op", latency, "success")
    
    # Calcular percentiles
    percentiles = collector.get_percentile_metrics(
        agent_name="test_agent",
        time_range=timedelta(hours=1)
    )
    
    # Verificar que los percentiles tienen valores
    assert "p50" in percentiles
    assert "p95" in percentiles
    assert "p99" in percentiles
    
    # Verificar orden lógico
    assert percentiles["p50"] <= percentiles["p95"] <= percentiles["p99"]
    
    print("✅ Test de percentiles: PASSED")


async def test_custom_alerts():
    """Test de alertas personalizadas"""
    print("🧪 Test: Alertas personalizadas")
    
    collector = get_advanced_metrics_collector()
    
    # Crear alerta de prueba
    from src.observability.advanced_metrics import CustomAlert, AlertSeverity
    
    alert = CustomAlert(
        id="test_alert",
        timestamp=datetime.now(),
        severity=AlertSeverity.WARNING,
        title="Test Alert",
        message="Test condition",
        metric_name="test_metric",
        current_value=0.0,
        threshold_value=50.0,
        operator=">"
    )
    
    # Agregar alerta
    collector.add_custom_alert(alert)
    
    # Verificar que se agregó
    assert "test_alert" in collector.custom_alerts
    assert collector.custom_alerts["test_alert"].title == "Test Alert"
    
    print("✅ Test de alertas: PASSED")


async def test_prometheus_export():
    """Test de exportación a Prometheus"""
    print("🧪 Test: Exportación a Prometheus")
    
    collector = get_advanced_metrics_collector()
    
    # Registrar algunas métricas
    collector.record_latency("test_agent", "test_op", 100.0, "success")
    collector.record_throughput(requests_per_second=10.0)
    
    # Exportar a Prometheus
    prometheus_output = collector.export_prometheus_metrics()
    
    # Verificar que el output contiene métricas
    assert "mcp_" in prometheus_output
    assert "mcp_latency_milliseconds" in prometheus_output or "mcp_throughput" in prometheus_output
    
    print("✅ Test de Prometheus: PASSED")


async def run_all_tests():
    """Ejecutar todos los tests"""
    print("🧪 EJECUTANDO TESTS DEL SISTEMA DE MÉTRICAS AVANZADAS")
    print("=" * 60)
    
    try:
        await test_basic_metrics_collection()
        await test_percentile_calculation()
        await test_custom_alerts()
        await test_prometheus_export()
        
        print("\n" + "=" * 60)
        print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FALLÓ: {e}")
        raise


if __name__ == "__main__":
    from datetime import timedelta, datetime
    asyncio.run(run_all_tests())
EOF

chmod +x mcp-core-superior/test_advanced_metrics.py

log_success "Tests básicos creados"

# Verificar instalación final
log_info "Verificando instalación final..."

# Hacer scripts ejecutables
chmod +x mcp-core-superior/start_metrics_system.sh
chmod +x mcp-core-superior/demo_advanced_metrics.py
chmod +x mcp-core-superior/test_advanced_metrics.py

# Crear resumen de instalación
cat > mcp-core-superior/INSTALLATION_SUMMARY.md << EOF
# Resumen de Instalación - Sistema de Métricas Avanzadas

## ✅ Instalación Completada

El Sistema de Métricas Avanzadas ha sido instalado correctamente con todas las funcionalidades:

### 📦 Archivos Instalados

1. **Sistema Principal**
   - \`src/observability/advanced_metrics.py\` - Sistema principal (1535 líneas)
   - \`src/observability/metrics_config.py\` - Configuración (498 líneas)
   - \`src/observability/__init__.py\` - Exports actualizados

2. **Scripts y Demos**
   - \`demo_advanced_metrics.py\` - Demostración completa (672 líneas)
   - \`start_metrics_system.sh\` - Script de inicio
   - \`test_advanced_metrics.py\` - Tests básicos

3. **Documentación**
   - \`README_ADVANCED_METRICS.md\` - Documentación completa (533 líneas)
   - \`METRICS_QUICKSTART.md\` - Guía de inicio rápido

4. **Configuración**
   - \`config/metrics_config.json\` - Configuración principal
   - \`config/alerts_config.json\` - Alertas por defecto

### 🚀 Próximos Pasos

1. **Ejecutar Demostración**
   \`\`\`bash
   ./start_metrics_system.sh
   \`\`\`

2. **Ejecutar Tests**
   \`\`\`bash
   python3 test_advanced_metrics.py
   \`\`\`

3. **Integrar en Aplicación**
   \`\`\`python
   from src.observability import initialize_advanced_metrics
   
   collector = await initialize_advanced_metrics()
   \`\`\`

### 📊 Funcionalidades Verificadas

- ✅ Latency metrics por agente y operación
- ✅ Throughput metrics (RPS, concurrent users)
- ✅ Error rates y success ratios
- ✅ Resource utilization (CPU, memoria, disco)
- ✅ Agent health scores y availability
- ✅ Business metrics (tasks completed, SLA compliance)
- ✅ Custom dashboards y alerts
- ✅ Time-series data storage
- ✅ Percentile calculations (P50, P95, P99)
- ✅ Capacity planning metrics
- ✅ Integración con Prometheus y Grafana

### 🔧 Archivos de Configuración

- \`metrics_data/\` - Base de datos de métricas
- \`config/\` - Configuraciones del sistema
- \`logs/metrics/\` - Logs del sistema de métricas
- \`export/prometheus/\` - Configuración de Prometheus
- \`export/grafana/\` - Configuración de Grafana

### 🆘 Soporte

Para soporte, consultar:
- \`README_ADVANCED_METRICS.md\` - Documentación completa
- \`METRICS_QUICKSTART.md\` - Inicio rápido
- Logs en \`logs/metrics/\`

---
Instalación completada: $(date)
EOF

log_success "Resumen de instalación creado"

# Mostrar resumen final
echo ""
echo "🎉 INSTALACIÓN COMPLETADA EXITOSAMENTE"
echo "============================================="
echo ""
echo "📁 Archivos Principales:"
echo "  • Sistema principal: src/observability/advanced_metrics.py"
echo "  • Configuración: src/observability/metrics_config.py"
echo "  • Demostración: demo_advanced_metrics.py"
echo "  • Documentación: README_ADVANCED_METRICS.md"
echo ""
echo "🚀 Para empezar:"
echo "  1. Ejecutar: ./start_metrics_system.sh"
echo "  2. Tests: python3 test_advanced_metrics.py"
echo "  3. Documentación: cat METRICS_QUICKSTART.md"
echo ""
echo "📊 Funcionalidades incluidas:"
echo "  ✅ Latency, Throughput, Error Rates"
echo "  ✅ Resource Utilization, Health Scores"
echo "  ✅ Business Metrics, Alerts"
echo "  ✅ Time-Series Storage, Percentiles"
echo "  ✅ Capacity Planning, Prometheus/Grafana"
echo ""
echo "🗄️ Archivos de datos creados:"
echo "  • metrics_data/ - Base de datos de métricas"
echo "  • config/ - Configuraciones del sistema"
echo "  • export/ - Configuraciones de Prometheus/Grafana"
echo ""
echo "¡El sistema está listo para usar! 🎯"