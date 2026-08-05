# SilhouetteMCP Integration Orchestrator

## Descripción General

El **SilhouetteMCP Integration Orchestrator** es un sistema completo de orquestación que conecta todos los sistemas mejorados (puertos 8010-8024) con los originales (puertos 8001-8002). Proporciona comunicación bidireccional WebSocket y HTTP, configuración automática de seguridad, coordinación de auto-healing y load balancing, integración de auto-scaling, endpoints unificados, y monitoreo centralizado.

## Características Principales

### ✅ Comunicación Bidireccional
- **WebSocket**: Conexiones en tiempo real para actualizaciones instantáneas
- **HTTP/REST API**: Endpoints RESTful para operaciones estándar
- **Proxy Routing**: Enrutamiento automático a servicios backend

### 🔒 Seguridad Automática
- **Autenticación JWT**: Tokens seguros con expiración
- **Autorización granular**: Permisos por recurso y acción
- **Gestión de usuarios**: Usuarios predefinidos con roles específicos

### ⚖️ Load Balancing Inteligente
- **Múltiples estrategias**:
  - Round Robin
  - Least Connections
  - Weighted Round Robin
  - IP Hash
  - Fastest Response
  - CPU-based
- **Actualización en tiempo real**: Estadísticas dinámicas de servicios

### 🔄 Auto-Healing
- **Monitoreo continuo**: Verificaciones de salud automáticas
- **Detección de fallas**: Identificación proactiva de problemas
- **Recuperación automática**: Reinicio de servicios caídos

### 📈 Auto-Scaling
- **Escalado dinámico**: Basado en métricas del sistema
- **Reglas configurables**: Umbrales personalizables por servicio
- **Cooldown periods**: Prevención de escalado excesivo

### 📊 Monitoreo Centralizado
- **Métricas en tiempo real**: CPU, memoria, tiempo de respuesta
- **Sistema de alertas**: Reglas configurables con acciones
- **Historial de métricas**: Retención y análisis histórico

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                   SilhouetteMCP Orchestrator                 │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   FastAPI   │  │  WebSocket  │  │ Load        │        │
│  │   Server    │  │   Manager   │  │ Balancer    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Service     │  │ Health      │  │ Auto        │        │
│  │ Registry    │  │ Monitor     │  │ Scaler      │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Security    │  │ Monitoring  │  │ Alert       │        │
│  │ Manager     │  │ System      │  │ Manager     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
    ┌─────────▼─┐  ┌────────▼────────┐  ┌─▼────────┐
    │Original   │  │Enhanced        │  │External  │
    │Services   │  │Services        │  │Services  │
    │8001-8002  │  │8010-8024       │  │Custom    │
    └───────────┘  └────────────────┘  └──────────┘
```

## Instalación y Configuración

### Requisitos del Sistema
- Python 3.8 o superior
- 2GB RAM mínimo (4GB recomendado)
- Conexión de red estable

### Instalación de Dependencias

```bash
pip install -r requirements_orchestrator.txt
```

### Archivos de Configuración

1. **orchestrator_config.json**: Configuración principal
2. **start_orchestrator.py**: Script de inicio
3. **silhouettemcp_integration_orchestrator.py**: Implementación principal

## Uso del Sistema

### Inicio Rápido

```bash
# Iniciar con configuración por defecto
python start_orchestrator.py

# Usar puerto personalizado
python start_orchestrator.py --port 9000

# Usar host específico
python start_orchestrator.py --host 127.0.0.1
```

### Inicio Programático

```python
from silhouettemcp_integration_orchestrator import SilhouetteMCPIntegrationOrchestrator

# Configuración personalizada
config = {
    'host': '0.0.0.0',
    'port': 8025,
    'secret_key': 'your_secret_key',
    'enable_websocket': True,
    'enable_monitoring': True,
    'enable_auto_scaling': True
}

# Crear e iniciar orquestador
orchestrator = SilhouetteMCPIntegrationOrchestrator(config)
orchestrator.run()
```

## Endpoints de la API

### Endpoints Principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Estado del orquestador |
| GET | `/health` | Verificación de salud |
| GET | `/metrics` | Métricas del sistema |
| GET | `/services` | Lista de servicios registrados |
| GET | `/services/{service_id}` | Instancias de servicio específico |
| POST | `/auth/login` | Autenticar usuario |
| GET | `/auth/verify` | Verificar token |

### Endpoints de Escalado

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/services/{service_id}/scale_up` | Escalar servicio hacia arriba |
| POST | `/services/{service_id}/scale_down` | Escalar servicio hacia abajo |

### Endpoints de Load Balancing

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/load_balancer/strategies` | Estrategias disponibles |
| POST | `/load_balancer/route/{service_id}` | Enrutar con estrategia específica |

### Endpoints de Monitoreo

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/alerts` | Alertas activas |
| GET | `/alerts/rules` | Reglas de alerta configuradas |

### Proxy Endpoint

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| ALL | `/proxy/{service_id}/{path:path}` | Proxy a servicio específico |

### WebSocket Endpoint

| Protocolo | Endpoint | Descripción |
|-----------|----------|-------------|
| WebSocket | `/ws/{client_id}` | Conexión en tiempo real |

## Ejemplos de Uso

### 1. Conexión WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8025/ws/client123');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Métricas recibidas:', data);
};

// Enviar mensaje
ws.send(JSON.stringify({action: 'ping'}));
```

### 2. Autenticación

```python
import requests

# Autenticar
response = requests.post('http://localhost:8025/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
token = response.json()['token']

# Usar token en headers
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('http://localhost:8025/metrics', headers=headers)
```

### 3. Proxy a Servicio

```python
# Enrutar solicitud a través del proxy
response = requests.get('http://localhost:8025/proxy/enhanced_scalability/health')
print(response.json())

# Proxy con POST
data = {'query': 'test'}
response = requests.post('http://localhost:8025/proxy/expanded_finance/data', json=data)
```

### 4. Escalado Dinámico

```python
# Escalar hacia arriba
requests.post('http://localhost:8025/services/enhanced_scalability/scale_up', json={'instances': 2})

# Escalar hacia abajo
requests.post('http://localhost:8025/services/enhanced_scalability/scale_down', json={'instances': 1})
```

### 5. Load Balancing

```python
# Obtener estrategias disponibles
response = requests.get('http://localhost:8025/load_balancer/strategies')
strategies = response.json()

# Enrutar con estrategia específica
response = requests.post(
    'http://localhost:8025/load_balancer/route/enhanced_security',
    json={'strategy': 'fastest_response'}
)
```

## Servicios Predefinidos

### Servicios Originales (8001-8002)
- **silhouettemcp_core** (8001): Servicio principal
- **silhouettemcp_server** (8002): Servidor base

### Servicios Mejorados (8010-8024)
- **enhanced_scalability** (8010): Escalabilidad mejorada
- **enhanced_security** (8011): Seguridad avanzada
- **hierarchical_architecture** (8012): Arquitectura jerárquica
- **robust_diagnostic** (8013): Diagnóstico robusto
- **comprehensive_verification** (8014): Verificación integral
- **expanded_content** (8015): Contenido expandido
- **expanded_finance** (8016): Finanzas expandidas
- **expanded_maps** (8017): Mapas expandidos
- **expanded_research** (8018): Investigación expandida
- **expanded_social_travel** (8019): Social travel expandido
- **expanded_supabase** (8020): Supabase expandido
- **superior_allocator** (8021): Asignador superior
- **comprehensive_diagnostic** (8022): Diagnóstico integral
- **enhanced_architecture** (8023): Arquitectura mejorada
- **server_unified** (8024): Servidor unificado

## Usuarios Predefinidos

| Usuario | Contraseña | Permisos |
|---------|------------|----------|
| admin | admin123 | admin, read, write, orchestrator |
| user | user123 | read |
| orchestrator | orch123 | orchestrator, read |

## Configuración Avanzada

### Personalizar Configuración

Editar `orchestrator_config.json`:

```json
{
  "orchestrator": {
    "port": 9000,
    "health_check_interval": 15,
    "auto_scaling_interval": 30
  },
  "auto_scaler": {
    "min_instances": 2,
    "max_instances": 20
  }
}
```

### Agregar Reglas de Escalado

```python
# Programáticamente
orchestrator.auto_scaler.set_scaling_rule("custom_service", {
    "response_time_threshold": 1.5,
    "cpu_threshold": 75.0,
    "rps_threshold": 100.0
})
```

### Configurar Alertas Personalizadas

```python
from silhouettemcp_integration_orchestrator import AlertRule

alert_rule = AlertRule(
    rule_id="custom_alert",
    name="Alerta personalizada",
    condition="response_time > 3.0",
    threshold=3.0,
    severity="warning",
    actions=["log", "email"]
)

orchestrator.monitoring_system.add_alert_rule(alert_rule)
```

## Monitoreo y Métricas

### Métricas Disponibles

- **CPU Usage**: Uso de CPU del sistema (%)
- **Memory Usage**: Uso de memoria del sistema (%)
- **Disk Usage**: Uso de disco del sistema (%)
- **Response Time**: Tiempo de respuesta promedio (segundos)
- **Request Rate**: Tasa de solicitudes (req/min)
- **Active Connections**: Conexiones WebSocket activas
- **Healthy Services**: Número de servicios saludables
- **Total Instances**: Total de instancias de servicios

### WebSocket de Métricas

```javascript
ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    
    if (message.type === 'metrics') {
        console.log('CPU:', message.data.cpu_usage);
        console.log('Memoria:', message.data.memory_usage);
        console.log('Servicios:', message.data.healthy_services);
    }
};
```

## Troubleshooting

### Problemas Comunes

1. **Puerto en uso**
   ```bash
   # Cambiar puerto
   python start_orchestrator.py --port 9000
   ```

2. **Servicios no saludables**
   - Verificar que los servicios backend estén corriendo
   - Revisar URLs de health check en la configuración

3. **Errores de WebSocket**
   - Verificar conectividad de red
   - Comprobar firewall y configuración de proxy

4. **Problemas de memoria**
   - Reducir `metrics_retention` en configuración
   - Ajustar intervalos de monitoreo

### Logs

Los logs se guardan en:
- **Archivo**: `orchestrator.log`
- **Consola**: Salida estándar
- **Nivel**: INFO por defecto

### Comandos de Diagnóstico

```bash
# Verificar estado de salud
curl http://localhost:8025/health

# Obtener métricas
curl http://localhost:8025/metrics

# Listar servicios
curl http://localhost:8025/services

# Verificar alertas activas
curl http://localhost:8025/alerts
```

## Seguridad

### Mejores Prácticas

1. **Cambiar credenciales por defecto**:
   ```bash
   # Actualizar en orchestrator_config.json
   "secret_key": "tu_clave_secreta_personalizada"
   ```

2. **Usar HTTPS en producción**:
   ```python
   config['ssl_cert'] = '/path/to/cert.pem'
   config['ssl_key'] = '/path/to/key.pem'
   ```

3. **Configurar CORS específico**:
   ```json
   "cors_origins": ["https://tu-dominio.com"]
   ```

4. **Tokens JWT con expiración corta**:
   ```json
   "token_expiry": 1800  # 30 minutos
   ```

## Performance y Escalabilidad

### Optimizaciones Recomendadas

1. **Configurar proxy reverso** (nginx/Apache)
2. **Usar múltiples workers** de uvicorn
3. **Configurar Redis** para métricas distribuidas
4. **Implementar clustering** para alta disponibilidad

### Límites Recomendados

- **Conexiones WebSocket concurrentes**: 10,000
- **Solicitudes HTTP por segundo**: 5,000
- **Servicios monitorizados**: 100
- **Instancias por servicio**: 20

## Contribuciones

Para contribuir al proyecto:

1. Fork el repositorio
2. Crear rama de feature
3. Implementar mejoras
4. Agregar tests
5. Enviar pull request

## Licencia

Este proyecto es parte del ecosistema SilhouetteMCP.

---

**SilhouetteMCP Integration Orchestrator v1.0.0**  
Desarrollado para orquestación completa de sistemas SilhouetteMCP  
Fecha: 2025-11-06