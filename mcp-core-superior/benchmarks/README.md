# Performance Benchmarking Suite
## MCP-Core-Superior vs MiniMax Agent

### 🎯 Descripción General

Esta suite de benchmarking proporciona una evaluación completa y comparativa del rendimiento entre MCP-Core-Superior y MiniMax Agent. Incluye tests de performance, load testing, análisis estadístico y dashboards interactivos.

### 📊 Métricas Evaluadas

1. **Latencia de Respuesta** - Tiempo de respuesta por request
2. **Throughput** - Requests por segundo que puede manejar
3. **Memory Usage** - Consumo de memoria y recursos
4. **Escalabilidad** - Performance con múltiples usuarios concurrentes
5. **Success Rate** - Tasa de éxito en operaciones
6. **Cost Analysis** - Costo por operación
7. **Workflow Time** - Tiempo para completar workflows complejos
8. **Cold Start Time** - Tiempo de inicio en frío
9. **Database Performance** - Performance en consultas de base de datos
10. **Network Overhead** - Overhead de red

### 🏗️ Estructura del Proyecto

```
benchmarks/
├── configs/                    # Configuraciones de tests
│   ├── benchmark_config.yaml   # Configuración principal
│   ├── artillery_configs/      # Configs de Artillery
│   └── load_profiles/          # Perfiles de carga
├── scripts/                    # Scripts de orquestación
│   ├── benchmark_orchestrator.py  # Orquestador principal
│   └── performance_benchmarker.py # Benchmark principal
├── load_tests/                 # Tests de carga
│   ├── locust_load_test.py     # Tests con Locust
│   └── artillery_load_test.py  # Tests con Artillery
├── tools/                      # Herramientas de análisis
│   ├── comparative_analysis.py # Análisis comparativo
│   ├── data_processor.py       # Procesamiento de datos
│   └── visualization_gen.py    # Generación de gráficos
├── reports/                    # Reportes generados
│   ├── performance_benchmark_results.json
│   ├── comparative_analysis_report.json
│   ├── interactive_dashboard.html
│   └── executive_summary.md
├── dashboards/                 # Dashboards interactivos
├── analysis/                   # Análisis detallados
└── logs/                       # Logs de ejecución
```

### 🚀 Inicio Rápido

#### 1. Instalación de Dependencias

```bash
# Dependencias principales
pip install asyncio aiohttp psutil numpy pandas matplotlib seaborn

# Para load testing
pip install locust artillery

# Para análisis estadístico
pip install scipy scikit-learn
```

#### 2. Configuración

Editar `configs/benchmark_config.yaml`:

```yaml
global:
  test_duration: 300
  concurrent_users: [1, 5, 10, 25, 50, 100]

agents:
  mcp_core_superior:
    base_url: "http://localhost:8000"
    
  minimax_agent:
    base_url: "http://localhost:8001"
```

#### 3. Ejecutar Suite Completa

```bash
# Ejecutar todos los benchmarks (recomendado)
python scripts/benchmark_orchestrator.py

# Ejecutar solo benchmarks de performance (más rápido)
python scripts/benchmark_orchestrator.py --skip-load-tests

# Ejecutar solo load tests
python scripts/load_tests/locust_load_test.py
```

### 📈 Ejecución de Tests Específicos

#### Performance Benchmarks

```bash
# Ejecutar benchmarks de performance individuales
python scripts/performance_benchmarker.py

# Con configuración personalizada
python scripts/performance_benchmarker.py --config custom_config.yaml
```

#### Load Testing con Locust

```bash
# Load test básico
locust -f load_tests/locust_load_test.py --host=http://localhost:8000

# Load test distribuido
locust -f load_tests/locust_load_test.py --master
locust -f load_tests/locust_load_test.py --worker --master-host=192.168.1.100

# Load test headless
locust -f load_tests/locust_load_test.py --host=http://localhost:8000 \
  --headless --users=100 --spawn-rate=10 --run-time=5m
```

#### Load Testing con Artillery

```bash
# Generar configuraciones
python load_tests/artillery_load_test.py

# Ejecutar tests
artillery run configs/mcp_load_test.yml --output results/mcp_load.json

# Generar reporte HTML
artillery report results/mcp_load.json --output results/mcp_report.html
```

### 🔍 Análisis y Reportes

#### Generar Análisis Comparativo

```bash
# Análisis completo con visualizaciones
python tools/comparative_analysis.py
```

#### Ver Resultados

Los reportes se generan en `reports/`:

1. **Reporte Principal**: `reports/performance_benchmark_results.json`
2. **Dashboard Interactivo**: `reports/interactive_dashboard.html`
3. **Análisis Comparativo**: `analysis/comparative_analysis_report.json`
4. **Resumen Ejecutivo**: `analysis/executive_summary.md`
5. **Visualizaciones**: `analysis/*.png`

### 📊 Interpretación de Resultados

#### Métricas Clave

- **Latencia**: < 100ms = Excelente, 100-500ms = Bueno, > 500ms = Necesita optimización
- **Throughput**: > 100 req/s = Alto, 50-100 req/s = Medio, < 50 req/s = Bajo
- **Success Rate**: > 98% = Excelente, 95-98% = Bueno, < 95% = Crítico
- **Memory Usage**: Analizar trends durante carga sostenida

#### Criterios de Evaluación

```
Exceeds Expectations: 90% de métricas favor de un agente
Meets Expectations: 60-90% favor de un agente
Needs Improvement: <60% favor de un agente
```

### 🛠️ Configuración Avanzada

#### Perfiles de Carga Personalizados

```yaml
# configs/load_profiles/high_load.yml
phases:
  - duration: 60
    arrivalRate: 50
  - duration: 120
    arrivalRate: 100
  - duration: 60
    arrivalRate: 200
```

#### Métricas Customizadas

```python
# Agregar métrica personalizada en performance_benchmarker.py
async def _benchmark_custom_metric(self):
    # Implementar lógica de test customizado
    pass
```

### 📋 Troubleshooting

#### Problemas Comunes

1. **Connection Timeout**
   - Verificar que los agentes estén ejecutándose
   - Aumentar timeout en configuración
   - Verificar conectividad de red

2. **Memory Errors**
   - Reducir número de usuarios concurrentes
   - Aumentar timeout entre requests
   - Verificar configuración de memoria del sistema

3. **Load Test Failures**
   - Verificar configuración de URLs
   - Revisar logs de agentes
   - Verificar rate limiting

#### Logs de Debug

```bash
# Ver logs en tiempo real
tail -f logs/benchmark_execution.log

# Logs de load testing
tail -f reports/*_locust.log

# Debugging de configuración
python scripts/benchmark_orchestrator.py --verbose
```

### 🎯 Mejores Prácticas

#### Antes de Ejecutar Benchmarks

1. **Verificar Estado de Agentes**
   ```bash
   curl http://localhost:8000/api/health
   curl http://localhost:8001/health
   ```

2. **Configurar Ambiente Limpio**
   ```bash
   # Reiniciar servicios
   sudo systemctl restart mcp-core-superior
   sudo systemctl restart minimax-agent
   
   # Limpiar caches
   echo 3 | sudo tee /proc/sys/vm/drop_caches
   ```

3. **Configurar Monitoring**
   ```bash
   # Monitor de recursos
   htop
   iotop
   
   # Network monitoring
   iftop
   ```

#### Durante Ejecución

1. **Monitorear Recursos del Sistema**
2. **Revisar Logs de Agentes**
3. **Verificar Conectividad de Red**
4. **Documentar Anomalías**

#### Post-Benchmark

1. **Verificar Consistencia de Resultados**
2. **Analizar Logs de Errores**
3. **Comparar con Baselines Anteriores**
4. **Actualizar Configuraciones si Necesario**

### 📈 Casos de Uso

#### Evaluación de Release

```bash
# Antes y después de deploy
python scripts/benchmark_orchestrator.py --release-version="v2.1.0"
```

#### Monitoring Continuo

```bash
# Scheduled benchmarks (cron)
0 2 * * * /usr/bin/python3 /path/to/benchmarks/scripts/benchmark_orchestrator.py --schedule
```

#### Testing de Regresión

```bash
# Comparar con resultados previos
python tools/comparative_analysis.py --baseline=baseline_results.json
```

### 🤝 Contribuir

#### Agregar Nuevo Test

1. **Crear función en performance_benchmarker.py**
2. **Agregar configuración en benchmark_config.yaml**
3. **Actualizar orquestador principal**
4. **Documentar en este README**

#### Extender Análisis

1. **Modificar tools/comparative_analysis.py**
2. **Agregar nuevas visualizaciones**
3. **Actualizar métricas de evaluación**

### 📚 Documentación Adicional

- [Guía de Load Testing](docs/load_testing_guide.md)
- [API Reference](docs/api_reference.md)
- [Configuración Avanzada](docs/advanced_config.md)
- [Casos de Estudio](docs/case_studies.md)

### 🆘 Soporte

Para problemas o preguntas:

1. Revisar logs en `logs/`
2. Verificar configuración en `configs/`
3. Consultar troubleshooting section
4. Crear issue en el repositorio

---

**Nota**: Esta suite de benchmarking está diseñada para ser ejecutada en entornos controlados. Asegúrese de tener permisos adecuados y recursos suficientes antes de ejecutar tests de carga intensiva.