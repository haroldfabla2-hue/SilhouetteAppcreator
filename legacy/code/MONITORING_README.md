# Sistema de Monitoreo Integrado SilhouetteMCP

Sistema completo de monitoreo en tiempo real que observa todos los componentes de SilhouetteMCP (originales y mejorados) con métricas unificadas, alertas automáticas, dashboard de estado, predicciones de escalabilidad y reportes automáticos.

## 🚀 Características Principales

### ✨ Monitoreo en Tiempo Real
- **Observación continua** de todos los sistemas SilhouetteMCP
- **Métricas unificadas**: CPU, memoria, disco, tiempo de respuesta, tasa de errores
- **Estado de salud** automático para cada componente

### 🚨 Sistema de Alertas Inteligente
- **Alertas automáticas** basadas en umbrales configurables
- **Notificaciones por email** para alertas críticas
- **Integración con orquestador** para acciones de recuperación
- **Clasificación de severidad**: info, warning, error, critical

### 📊 Dashboard Dinámico
- **Vista unificada** del estado de todos los sistemas
- **Actualización automática** cada 30 segundos
- **Métricas en tiempo real** con gráficos de tendencia
- **Alertas activas** con detalles completos

### 🔮 Predicciones de Escalabilidad
- **Análisis predictivo** basado en tendencias históricas
- **Predicción de carga** para las próximas 24 horas
- **Evaluación de capacidad** con niveles de confianza
- **Recomendaciones automáticas** de escalamiento

### 📈 Reportes Automáticos
- **Reportes de rendimiento** automáticos cada 24 horas
- **Análisis de tendencias** con datos históricos
- **Métricas de disponibilidad** y uptime
- **Exportación en JSON** para análisis posterior

### 🔄 Auto-Recuperación
- **Detección automática** de fallos críticos
- **Notificación al orquestador** para recuperación
- **Políticas de recuperación** configurables
- **Escalamiento automático** basado en predicciones

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│              Sistema de Monitoreo Integrado             │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐│
│  │  SystemMonitor  │  │  AlertManager   │  │  Dashboard  ││
│  │   (Individual)  │  │   (Alertas)     │  │  (Tiempo   ││
│  └─────────────────┘  └─────────────────┘  │   Real)    ││
│           │                      │          └─────────────┘│
│  ┌─────────────────┐  ┌─────────────────┐                │
│  │ScalabilityPred. │  │PerformanceRep.  │                │
│  │   (Predicciones)│  │   (Reportes)    │                │
│  └─────────────────┘  └─────────────────┘                │
├─────────────────────────────────────────────────────────┤
│              IntegratedMonitoringSystem                  │
│                  (Orquestador)                          │
├─────────────────────────────────────────────────────────┤
│        SilhouetteMCP Core    │   SilhouetteMCP Cache    │
│      SilhouetteMCP Improved  │   SilhouetteMCP API      │
│      SilhouetteMCP Database  │   ...otros sistemas      │
└─────────────────────────────────────────────────────────┘
```

## 🛠️ Instalación y Configuración

### Requisitos Previos
```bash
# Python 3.8+
pip install psutil requests

# Para notificaciones por email (opcional)
pip install secure-smtplib  # Incluido en Python estándar
```

### Instalación Rápida
```bash
# Clonar o descargar los archivos
cp silhouettemcp_integrated_monitoring.py /ruta/a/proyecto/
cp monitoring_config.json /ruta/a/proyecto/
cp monitoring_utils.py /ruta/a/proyecto/

# Hacer ejecutable
chmod +x monitoring_utils.py
```

### Configuración

Edita `monitoring_config.json` según tus necesidades:

```json
{
  "systems": [
    {
      "id": "silhouettemcp_core",
      "endpoint": "http://localhost:8000",
      "check_interval": 30
    }
  ],
  "orquestador": {
    "endpoint": "http://localhost:8000",
    "actions": {
      "auto_recovery": true,
      "escalate_on_critical": true,
      "restart_failed_services": true
    }
  },
  "alerts": {
    "thresholds": {
      "cpu_warning": 70,
      "cpu_critical": 90,
      "memory_warning": 70,
      "memory_critical": 90
    },
    "email": {
      "smtp_server": "smtp.gmail.com",
      "from_email": "monitoring@tuempresa.com",
      "to_email": "admin@tuempresa.com",
      "username": "tu_email@gmail.com",
      "password": "tu_app_password"
    }
  }
}
```

## 📱 Uso del Sistema

### Inicio Rápido
```bash
# Iniciar sistema de monitoreo
python monitoring_utils.py start

# Ver estado en tiempo real
python monitoring_utils.py dashboard

# Ver estado actual
python monitoring_utils.py status
```

### Comandos Disponibles

#### 🔍 Estado del Sistema
```bash
python monitoring_utils.py status
```
Muestra el estado actual de todos los sistemas monitoreados con métricas en tiempo real.

#### 📊 Dashboard en Tiempo Real
```bash
python monitoring_utils.py dashboard
```
Abre el dashboard con actualización automática cada 30 segundos. Presiona Ctrl+C para salir.

#### 🚨 Alertas Activas
```bash
python monitoring_utils.py alerts
```
Muestra todas las alertas activas del sistema con detalles completos.

#### 🔮 Predicciones de Escalabilidad
```bash
python monitoring_utils.py predictions
```
Visualiza las predicciones de carga y capacidad para las próximas horas.

#### 📈 Generar Reporte
```bash
python monitoring_utils.py report
```
Genera un reporte completo de rendimiento en formato JSON.

#### 🚀 Iniciar/Detener Monitoreo
```bash
python monitoring_utils.py start
python monitoring_utils.py stop
```

### Uso Directo en Código

```python
from silhouettemcp_integrated_monitoring import IntegratedMonitoringSystem

# Crear sistema de monitoreo
monitoring = IntegratedMonitoringSystem("mi_config.json")

# Añadir sistemas específicos
monitoring.add_system("mi_api", "http://localhost:8000", 30)

# Iniciar monitoreo
monitoring.start_monitoring()

# Obtener estado actual
status = monitoring.get_system_status()
print(f"Sistemas activos: {len(status['systems'])}")

# Obtener alertas
alerts = monitoring.get_alerts()
print(f"Alertas activas: {len(alerts)}")

# Generar predicciones
predictions = monitoring.get_predictions()
for system_id, prediction in predictions.items():
    print(f"{system_id}: {prediction['capacity_assessment']}")

# Detener cuando sea necesario
monitoring.stop_monitoring()
```

## ⚙️ Configuración Avanzada

### Umbrales de Alertas
```json
"alerts": {
  "thresholds": {
    "cpu_warning": 70,           // % CPU para advertencia
    "cpu_critical": 90,          // % CPU para crítico
    "memory_warning": 70,        // % Memoria para advertencia
    "memory_critical": 90,       // % Memoria para crítico
    "response_time_warning": 10, // Segundos para advertencia
    "response_time_critical": 25,// Segundos para crítico
    "error_rate_warning": 5,     // % Error rate para advertencia
    "error_rate_critical": 20    // % Error rate para crítico
  }
}
```

### Configuración de Auto-Recuperación
```json
"orquestador": {
  "endpoint": "http://localhost:8000",
  "actions": {
    "auto_recovery": true,           // Habilitar recuperación automática
    "escalate_on_critical": true,    // Escalar alertas críticas
    "restart_failed_services": true, // Reiniciar servicios fallen
    "scale_up_resources": true,      // Escalar recursos automáticamente
    "notify_administrators": true    // Notificar administradores
  },
  "recovery_policies": {
    "max_retries": 3,               // Máximo de reintentos
    "retry_delay": 60,              // Delay entre reintentos (segundos)
    "escalate_after_failures": 5    // Escalar después de X fallos
  }
}
```

### Configuración de Predicciones
```json
"scalability": {
  "prediction_horizon_hours": 24,    // Horas hacia adelante a predecir
  "analysis_window_hours": 168,      // Ventana de análisis (7 días)
  "confidence_threshold": 0.7,       // Umbral de confianza mínimo
  "auto_scaling": {
    "enabled": true,
    "scale_up_threshold": 80,        // % para escalar hacia arriba
    "scale_down_threshold": 30,      // % para escalar hacia abajo
    "cooldown_minutes": 15           // Tiempo de espera entre escalamientos
  }
}
```

### Configuración de Reportes
```json
"reports": {
  "auto_generate": true,             // Generación automática
  "interval_hours": 24,              // Intervalo de generación
  "output_directory": "reports",     // Directorio de salida
  "include_predictions": true,       // Incluir predicciones
  "format": "json",                  // Formato de salida
  "retention_days": 30              // Días de retención
}
```

## 🔧 Personalización

### Añadir Nuevos Sistemas
```python
# Añadir sistema personalizado
monitoring_system.add_system(
    system_id="mi_servicio_custom",
    endpoint="http://localhost:9000",
    check_interval=60  # Check cada minuto
)
```

### Crear Monitores Personalizados
```python
from silhouettemcp_integrated_monitoring import SystemMonitor

class CustomSystemMonitor(SystemMonitor):
    async def check_health(self):
        # Lógica personalizada de monitoreo
        health = await super().check_health()
        
        # Añadir métricas personalizadas
        health.custom_metric = await self._get_custom_metric()
        
        return health
    
    async def _get_custom_metric(self):
        # Implementar lógica para métrica personalizada
        return 42.0
```

### Integrar con Orquestador Existente
```python
# El sistema envía notificaciones automáticas al orquestador
# Endpoint: /api/monitoring/alerts
# Payload:
{
    "action": "critical_alert",
    "system_id": "silhouettemcp_core",
    "health_data": {...},
    "timestamp": 1234567890
}
```

## 📊 Métricas y Datos

### Métricas Recolectadas
- **CPU Usage**: Porcentaje de uso de CPU
- **Memory Usage**: Porcentaje de uso de memoria
- **Disk Usage**: Porcentaje de uso de disco
- **Response Time**: Tiempo de respuesta en segundos
- **Error Rate**: Porcentaje de errores
- **Uptime**: Tiempo de actividad en segundos
- **Throughput**: Solicitudes por segundo

### Estructura de Datos
```json
{
  "timestamp": 1234567890.123,
  "system_id": "silhouettemcp_core",
  "status": "healthy",
  "cpu_usage": 45.2,
  "memory_usage": 67.8,
  "disk_usage": 23.1,
  "response_time": 0.156,
  "error_rate": 2.1,
  "uptime": 86400.0
}
```

### Archivos Generados
- `dashboard.json`: Estado actual del dashboard
- `reports/performance_report_YYYY-MM-DD_HH-MM-SS.json`: Reportes automáticos
- `logs/monitoring.log`: Logs del sistema de monitoreo

## 🚨 Manejo de Alertas

### Tipos de Severidad
- **Info**: Información general
- **Warning**: Advertencias que requieren atención
- **Error**: Errores que afectan el rendimiento
- **Critical**: Errores críticos que requieren acción inmediata

### Acciones Automáticas
1. **Notificación Email**: Para alertas críticas
2. **Notificación Webhook**: Para integraciones externas
3. **Notificación Orquestador**: Para acciones de recuperación
4. **Auto-Recovery**: Reinicio de servicios caídos
5. **Escalamiento**: Aumento de recursos

### Resolución de Alertas
Las alertas se resuelven automáticamente cuando:
- Los valores vuelven a umbrales normales
- El sistema se recupera
- Se ejecuta acción de recuperación exitosa

## 🔮 Análisis Predictivo

### Algoritmo de Predicción
1. **Recolección de datos históricos** de las últimas 168 horas (7 días)
2. **Análisis de tendencias** usando regresión lineal simple
3. **Cálculo de confianza** basado en consistencia de datos
4. **Generación de recomendaciones** automáticas

### Tipos de Predicción
- **Capacidad Adecuada**: Recursos suficientes para carga esperada
- **Límite Apropiado**: Recursos cerca del límite (monitoreo cercano)
- **Excediendo Capacidad**: Recursos insuficientes (escalamiento requerido)

### Factores Considerados
- Tendencia de CPU
- Tendencia de Memoria
- Consistencia histórica
- Variabilidad de carga

## 🔧 Mantenimiento y Troubleshooting

### Logs del Sistema
```bash
# Ver logs en tiempo real
tail -f logs/monitoring.log

# Filtrar errores
grep "ERROR" logs/monitoring.log

# Filtrar alertas
grep "ALERT" logs/monitoring.log
```

### Problemas Comunes

#### Sistema no detecta servicios
1. Verificar que los endpoints estén accesibles
2. Comprobar configuración de URLs
3. Verificar que los servicios tengan endpoints `/health`

#### Alertas no se envían por email
1. Verificar configuración SMTP
2. Comprobar credenciales de email
3. Verificar firewall y puertos

#### Dashboard no se actualiza
1. Verificar que el archivo `dashboard.json` tenga permisos de escritura
2. Comprobar espacio en disco
3. Verificar logs para errores de permisos

### Monitoreo de Salud del Sistema de Monitoreo
```bash
# Verificar que el proceso esté corriendo
ps aux | grep monitoring

# Verificar conexiones de red
netstat -tulpn | grep python

# Verificar archivos de configuración
python monitoring_utils.py status
```

## 📈 Optimización de Rendimiento

### Configuración para Alto Rendimiento
```json
{
  "monitoring": {
    "max_concurrent_checks": 10,    // Máximos checks concurrentes
    "check_timeout": 10,            // Timeout para cada check
    "batch_size": 5,                // Tamaño de lote para procesamiento
    "max_history_size": 1000        // Tamaño máximo del historial
  }
}
```

### Consideraciones de Escalabilidad
- **Monitoreo de 1-10 sistemas**: Configuración estándar
- **Monitoreo de 10-50 sistemas**: Optimizar intervalos de check
- **Monitoreo de 50+ sistemas**: Considerar distribución horizontal

## 🔒 Seguridad

### Mejores Prácticas
1. **Usar HTTPS** para todos los endpoints monitoreados
2. **Autenticación** para APIs críticas
3. **Logs seguros** sin exponer credenciales
4. **Backup regular** de configuraciones
5. **Acceso controlado** a archivos de configuración

### Configuración SSL/TLS
```json
{
  "security": {
    "verify_ssl": true,
    "ssl_ca_bundle": "/path/to/ca-bundle.crt",
    "client_cert": "/path/to/client.crt",
    "client_key": "/path/to/client.key"
  }
}
```

## 🤝 Integración con SilhouetteMCP

El sistema de monitoreo está diseñado específicamente para trabajar con SilhouetteMCP:

### Endpoints Monitoreados
- **Core System**: http://localhost:8000/health
- **Improved System**: http://localhost:8001/health  
- **Cache Layer**: http://localhost:8002/health
- **API Gateway**: http://localhost:8003/health
- **Database**: http://localhost:5432/health

### Integración con Orquestador
- **Auto-recovery** basado en decisiones del orquestador
- **Escalamiento automático** coordinado con el orquestador
- **Reportes de rendimiento** compartidos con el orquestador

### Datos Compartidos
- **Métricas de salud** compartidas con el orquestador
- **Predicciones de capacidad** para decisiones de escalamiento
- **Alertas críticas** para escalación automática

## 📞 Soporte

Para soporte técnico o preguntas:
1. Revisar la documentación completa
2. Consultar los logs del sistema
3. Ejecutar diagnósticos con `monitoring_utils.py status`
4. Verificar configuración y conectividad

---

**SilhouetteMCP Integrated Monitoring System v1.0**  
*Sistema de monitoreo completo para SilhouetteMCP*