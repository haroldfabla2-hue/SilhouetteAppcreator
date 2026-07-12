# 🚀 IRIS MCP Integration - Sistema Multiagente Avanzado

**Versión:** 1.0.0  
**Autor:** IRIS MCP Integration Team  
**Descripción:** Sistema completo de gestión, monitoreo y automatización para agentes IRIS

---

## 📋 ÍNDICE

1. [Descripción General](#descripción-general)
2. [Componentes del Sistema](#componentes-del-sistema)
3. [Instalación y Configuración](#instalación-y-configuración)
4. [Dashboard React](#dashboard-react)
5. [CLI Avanzada](#cli-avanzada)
6. [Sistema de Templates](#sistema-de-templates)
7. [Sistema de Notificaciones](#sistema-de-notificaciones)
8. [Servidor de Métricas](#servidor-de-métricas)
9. [API Reference](#api-reference)
10. [Desarrollo y Testing](#desarrollo-y-testing)
11. [Solución de Problemas](#solución-de-problemas)
12. [Contribución](#contribución)

---

## 🎯 DESCRIPCIÓN GENERAL

IRIS MCP Integration es un sistema completo de gestión multiagente que proporciona:

### ✅ **Características Principales**
- **Dashboard React** con métricas en tiempo real y visualización avanzada
- **CLI Avanzada** para gestión completa del sistema via línea de comandos
- **Sistema de Templates** predefinidos para automatización de agentes especializados
- **Sistema de Notificaciones Multi-Canal** (email, webhook, consola)
- **Servidor de Métricas FastAPI** con streaming de datos en tiempo real
- **Monitoreo Continuo** de agentes y sistema completo

### 🤖 **Agentes IRIS Soportados**
1. **Sales Agent** - Automatización de procesos de venta
2. **Support Agent** - Gestión de atención al cliente
3. **Consulting Agent** - Análisis avanzado y consultoría
4. **Multi-Agent** - Coordinación de múltiples agentes
5. **Optimization** - Optimización de flujos de trabajo

---

## 🛠️ COMPONENTES DEL SISTEMA

### **1. Dashboard React** (`dashboard/`)
- **Archivo Principal:** `src/components/Dashboard.tsx`
- **Puerto:** 3000 (configurable)
- **Funcionalidades:**
  - Métricas en tiempo real de todos los agentes
  - Gráficos interactivos con Recharts
  - Estado visual de agentes (activo/inactivo/error)
  - Stream de datos via Server-Sent Events (SSE)
  - Actualizaciones automáticas cada 2 segundos

### **2. Servidor de Métricas** (`api/iris_metrics_server.py`)
- **Puerto:** 8000 (configurable)
- **Funcionalidades:**
  - API REST completa para gestión de agentes
  - Streaming de métricas en tiempo real (SSE)
  - Endpoints para despliegue y control de agentes
  - Generación simulada de datos realistas
  - CORS habilitado para integración web

### **3. CLI Avanzada** (`cli/iris_cli.py`)
- **Framework:** Click con autocompletado
- **Comandos Disponibles:**
  - `iris status` - Consultar estado del sistema
  - `iris deploy` - Desplegar agentes
  - `iris metrics` - Ver métricas y monitoreo
  - `iris template` - Gestión de templates
  - `iris notify` - Configurar notificaciones
  - `iris log` - Ver logs del sistema

### **4. Sistema de Templates** (`templates/iris_templates.py`)
- **Templates Predefinidos:**
  - Sales Automation Template
  - Support Automation Template
  - Consulting Analysis Template
  - Multi-Agent Configuration Template
  - Workflow Optimization Template
- **Funcionalidades:**
  - Generación automática de configuraciones
  - Validación de templates
  - Personalización y customización
  - Integración con APIs externas

### **5. Sistema de Notificaciones** (`notifications/iris_notifications.py`)
- **Canales Soportados:**
  - Email (SMTP)
  - Webhook (HTTP POST)
  - Consola (colorizada)
- **Eventos Monitoreados:**
  - Cambios de estado de agentes
  - Métricas que exceden umbrales
  - Errores del sistema
  - Completado de tareas
  - Alertas críticas

---

## 🚀 INSTALACIÓN Y CONFIGURACIÓN

### **Requisitos del Sistema**
- **Python 3.8+** (recomendado 3.10+)
- **Node.js 16+** y **npm** (opcional, para dashboard)
- **Git** (para clonar el repositorio)

### **Instalación Rápida**

```bash
# 1. Clonar o descargar el proyecto
cd iris-mcp-integration

# 2. Ejecutar setup automático
chmod +x setup.sh
./setup.sh

# 3. Iniciar todos los servicios
chmod +x monitor_all.sh
./monitor_all.sh
```

### **Instalación Manual**

```bash
# Crear entorno virtual
python3 -m venv iris-mcp-env
source iris-mcp-env/bin/activate  # Linux/Mac
# iris-mcp-env\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar dashboard (opcional)
cd dashboard
npm install
cd ..

# Ejecutar setup de templates
python templates/iris_templates.py --setup

# Crear directorios
mkdir -p logs iris_templates configs
```

### **Configuración de Entorno**

Crear archivo `.env`:
```bash
# Configuración Principal
IRIS_API_BASE=http://localhost:8000
IRIS_DASHBOARD_PORT=3000
IRIS_METRICS_PORT=8000

# Configuración de Email (Opcional)
IRIS_SMTP_SERVER=smtp.gmail.com
IRIS_SMTP_PORT=587
IRIS_EMAIL_USER=tu_email@gmail.com
IRIS_EMAIL_PASSWORD=tu_app_password

# Configuración de Webhook (Opcional)
IRIS_WEBHOOK_URL=https://tu-webhook.com/notifications

# Logging
IRIS_LOG_LEVEL=INFO
IRIS_LOG_FILE=logs/iris_mcp.log
```

---

## 🌐 DASHBOARD REACT

### **Características del Dashboard**
- **Interfaz moderna** con Tailwind CSS
- **Métricas en tiempo real** via Server-Sent Events
- **Gráficos interactivos** con Recharts
- **Estado visual** de todos los agentes
- **Actualización automática** cada 2 segundos

### **Componentes Principales**

```typescript
// Dashboard principal
const IrisDashboard: React.FC<DashboardProps> = ({ apiBase }) => {
  const [agents, setAgents] = useState<AgentMetrics[]>([]);
  const [realTimeData, setRealTimeData] = useState<any[]>([]);
  
  // Conexión SSE para datos en tiempo real
  useEffect(() => {
    const eventSource = new EventSource(`${apiBase}/metrics/stream`);
    // ...
  }, [apiBase]);
};
```

### **Uso del Dashboard**

```bash
# Iniciar dashboard
cd dashboard
npm run dev

# Acceder a http://localhost:3000
```

### **API del Dashboard**

```javascript
// Configurar API base
const apiBase = process.env.VITE_API_BASE || 'http://localhost:8000';

// Datos en tiempo real via SSE
const eventSource = new EventSource(`${apiBase}/metrics/stream`);
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Actualizar estado con nuevos datos
};
```

---

## 🔮 CLI AVANZADA

### **Comandos Principales**

```bash
# Ver estado de agentes
./run_cli.sh status agents

# Desplegar agente específico
./run_cli.sh deploy sales_agent

# Ver métricas del sistema
./run_cli.sh metrics show

# Listar templates disponibles
./run_cli.sh template list

# Configurar notificaciones
./run_cli.sh notify config email

# Ver logs de un agente
./run_cli.sh log show support_agent

# Verificar salud del sistema
./run_cli.sh health
```

### **Comandos Avanzados**

```bash
# Monitoreo continuo (cada 5 segundos por 30 segundos)
./run_cli.sh metrics monitor --interval 5 --duration 30

# Generar configuración desde template
./run_cli.sh template generate sales --output configs/sales_config.json

# Desplegar todos los agentes
./run_cli.sh deploy all

# Ver métricas específicas de un agente
./run_cli.sh metrics show --agent sales_agent --format json
```

### **Personalización de CLI**

```python
# En cli/iris_cli.py
@iris_cli.group()
@click.option('--api-base', default='http://localhost:8000')
@click.pass_context
def iris_cli(ctx, api_base):
    """CLI Avanzada para Gestión de IRIS MCP Server"""
    ctx.obj['api_base'] = api_base
```

---

## 📋 SISTEMA DE TEMPLATES

### **Templates Disponibles**

#### **1. Sales Automation Template**
```python
sales_template = {
    "agents": {
        "lead_qualification_agent": {
            "capabilities": ["lead_scoring", "intent_detection"],
            "actions": ["score_lead", "route_to_sales"]
        },
        "proposal_generator_agent": {
            "capabilities": ["proposal_creation", "pricing_optimization"],
            "actions": ["create_proposal", "customize_pricing"]
        }
    },
    "workflow": ["lead_qualification", "proposal_generation", "follow_up"]
}
```

#### **2. Support Automation Template**
```python
support_template = {
    "agents": {
        "ticket_classifier_agent": {
            "capabilities": ["ticket_categorization", "priority_assessment"],
            "actions": ["categorize_ticket", "set_priority"]
        },
        "response_generator_agent": {
            "capabilities": ["response_composition", "solution_recommendation"],
            "actions": ["draft_response", "suggest_solutions"]
        }
    }
}
```

### **Uso del Template Manager**

```python
from templates.iris_templates import IRISTemplateManager

# Crear instancia
manager = IRISTemplateManager()

# Crear template
template = manager.create_sales_automation_template()

# Guardar template
file_path = manager.save_template(template)

# Cargar template
loaded_template = manager.load_template("iris_sales_automation")

# Generar configuración
config = manager.generate_workflow_config("iris_sales_automation", customizations)
```

### **Validación de Templates**

```python
# Validar template
validation_result = manager.validate_template(template)

if validation_result["valid"]:
    print("Template válido")
else:
    print("Errores encontrados:")
    for error in validation_result["errors"]:
        print(f"- {error}")
```

---

## 🔔 SISTEMA DE NOTIFICACIONES

### **Configuración de Canales**

#### **Email Notifications**
```python
from notifications.iris_notifications import IRISNotificationManager

manager = IRISNotificationManager()

# Configurar email
manager.configure_email(
    email="tu_email@gmail.com",
    password="tu_app_password",
    smtp_server="smtp.gmail.com",
    smtp_port=587
)
```

#### **Webhook Notifications**
```python
# Configurar webhook
manager.configure_webhook(
    url="https://tu-webhook.com/notifications",
    method="POST",
    headers={"Content-Type": "application/json"},
    auth_token="tu_token"
)
```

#### **Console Notifications**
```python
# Configurar consola
manager.configure_console(
    show_colors=True,
    timestamps=True,
    verbose=False
)
```

### **Envío de Notificaciones**

```python
# Notificación de estado de agente
manager.send_agent_status_notification(
    agent_id="sales_agent",
    status="error",
    details={"last_task": "failed", "error_message": "Timeout"}
)

# Notificación de métrica
manager.send_metric_threshold_notification(
    metric_name="response_time",
    value=5.2,
    threshold=2.0,
    agent_id="support_agent"
)

# Alerta del sistema
manager.send_system_alert(
    title="High CPU Usage",
    message="CPU usage above 90% for 5 minutes",
    level=NotificationLevel.WARNING
)
```

### **Eventos Soportados**

- `agent_status_change` - Cambio en estado de agentes
- `metric_threshold_exceeded` - Métrica excede umbral
- `system_alert` - Alerta general del sistema
- `task_completed` - Tarea completada
- `agent_error` - Error en agente

---

## 📊 SERVIDOR DE MÉTRICAS

### **API Endpoints**

#### **GET /agents**
```bash
curl http://localhost:8000/agents
```

**Respuesta:**
```json
{
  "agents": [
    {
      "id": "sales_agent",
      "agent": "Sales Agent",
      "status": "active",
      "tasksCompleted": 156,
      "avgResponseTime": 1.2,
      "tokenUsage": 45200,
      "successRate": 0.94,
      "capabilities": ["lead_qualification", "proposal_generation"]
    }
  ]
}
```

#### **GET /metrics/stream**
```javascript
// Conexión SSE para datos en tiempo real
const eventSource = new EventSource('http://localhost:8000/metrics/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Nuevas métricas:', data);
};
```

#### **POST /agents/{agent_id}/deploy**
```bash
curl -X POST http://localhost:8000/agents/sales_agent/deploy
```

#### **GET /metrics/summary**
```bash
curl http://localhost:8000/metrics/summary
```

**Respuesta:**
```json
{
  "summary": {
    "total_agents": 3,
    "active_agents": 2,
    "total_tasks": 268,
    "total_tokens": 145600,
    "avg_response_time": 1.4,
    "system_health": "healthy"
  }
}
```

### **Generación de Datos Simulados**

```python
class IRISMetricsGenerator:
    def generate_metrics(self) -> Dict[str, Any]:
        """Generar métricas realistas para agentes IRIS"""
        agents = []
        
        for agent_id, agent_info in self.agents_data.items():
            # Simular variaciones realistas
            updated_agent = agent_info.copy()
            updated_agent["tasksCompleted"] = self.base_tasks[agent_id] + random.randint(-5, 15)
            updated_agent["tokenUsage"] = self.base_tokens[agent_id] + random.randint(-1000, 3000)
            updated_agent["avgResponseTime"] = max(0.1, agent_info["avgResponseTime"] + random.uniform(-0.2, 0.4))
            
            agents.append(updated_agent)
        
        return {"timestamp": datetime.now().isoformat(), "agents": agents}
```

---

## 🔗 API REFERENCE

### **Base URL**
```
http://localhost:8000
```

### **Endpoints Disponibles**

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/agents` | Lista de agentes |
| GET | `/agents/{agent_id}` | Detalles de agente |
| GET | `/agents/{agent_id}/metrics` | Métricas de agente |
| POST | `/agents/{agent_id}/deploy` | Desplegar agente |
| POST | `/agents/{agent_id}/stop` | Detener agente |
| GET | `/metrics/stream` | Stream de métricas (SSE) |
| GET | `/metrics/summary` | Resumen de métricas |

### **Modelos de Datos**

```python
# AgentMetrics
class AgentMetrics(BaseModel):
    id: str
    agent: str
    status: str
    tasksCompleted: int
    avgResponseTime: float
    tokenUsage: int
    successRate: float
    lastActivity: str
    capabilities: List[str]

# NotificationEvent
class NotificationEvent(BaseModel):
    event_type: str
    level: NotificationLevel
    title: str
    message: str
    timestamp: datetime
    agent_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
```

---

## 🧪 DESARROLLO Y TESTING

### **Running Tests**
```bash
# Instalar dependencias de testing
pip install pytest pytest-asyncio

# Ejecutar tests
pytest tests/ -v

# Tests específicos
pytest tests/test_templates.py -v
pytest tests/test_notifications.py -v
```

### **Test de Integración Completa**

```python
# tests/test_integration.py
import asyncio
from api.iris_metrics_server import app
from templates.iris_templates import IRISTemplateManager
from notifications.iris_notifications import IRISNotificationManager
import httpx

async def test_full_integration():
    """Test de integración completa del sistema"""
    
    # Test servidor de métricas
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/agents")
        assert response.status_code == 200
        assert len(response.json()["agents"]) > 0
    
    # Test templates
    manager = IRISTemplateManager()
    template = manager.create_sales_automation_template()
    assert template["category"] == "sales"
    
    # Test notificaciones
    notifier = IRISNotificationManager()
    notifier.configure_console()
    
    event = NotificationEvent(
        event_type="test",
        level=NotificationLevel.INFO,
        title="Test",
        message="Test message",
        timestamp=datetime.now()
    )
    
    result = notifier.send_notification(event)
    assert result == True
```

### **Debugging**

```bash
# Logs detallados
export IRIS_LOG_LEVEL=DEBUG
./monitor_all.sh

# Logs específicos
tail -f logs/metrics.log
tail -f logs/dashboard.log
tail -f logs/notifications.log
```

---

## 🔧 SOLUCIÓN DE PROBLEMAS

### **Problemas Comunes**

#### **1. Puerto en uso**
```bash
# Error: Puerto 8000 ya está en uso
./start_metrics_server.sh 8001
./start_dashboard.sh 3001
```

#### **2. Python modules no encontrados**
```bash
# Activar entorno virtual
source iris-mcp-env/bin/activate

# Reinstalar dependencias
pip install -r requirements.txt
```

#### **3. Node.js no encontrado**
```bash
# Verificar instalación
node --version
npm --version

# Instalar Node.js desde https://nodejs.org/
```

#### **4. Permisos de archivos**
```bash
# Hacer scripts ejecutables
chmod +x *.sh
```

#### **5. Email no enviado**
```bash
# Verificar configuración SMTP
python notifications/iris_notifications.py test

# Configurar app password (Gmail)
# https://myaccount.google.com/apppasswords
```

### **Logs de Debugging**

```python
# En código Python
import logging
logging.basicConfig(level=logging.DEBUG)

# En código React
console.log('Debug info:', data);
```

### **Performance Issues**

```bash
# Monitorear recursos
top -p $(pgrep -f "iris_metrics_server")
htop

# Verificar memoria
free -h

# Verificar disco
df -h
```

---

## 🤝 CONTRIBUCIÓN

### **Estructura del Proyecto**
```
iris-mcp-integration/
├── api/                    # Servidor de métricas FastAPI
├── dashboard/              # Dashboard React
├── cli/                    # CLI avanzada
├── templates/              # Sistema de templates
├── notifications/          # Sistema de notificaciones
├── tests/                  # Tests unitarios e integración
├── logs/                   # Archivos de log
├── iris_templates/         # Templates guardados
├── setup.sh               # Script de instalación
├── start_*.sh             # Scripts de inicio
├── monitor_all.sh         # Monitoreo completo
└── README.md              # Este archivo
```

### **Estándares de Código**

#### **Python**
```python
# Docstrings estilo Google
def function_name(param1: str, param2: int) -> bool:
    """Descripción breve de la función.
    
    Args:
        param1: Descripción del primer parámetro
        param2: Descripción del segundo parámetro
    
    Returns:
        Descripción del valor de retorno
    
    Raises:
        ValueError: Descripción de cuándo se lanza
    """
    pass

# Type hints siempre
from typing import Dict, Any, List, Optional

def process_data(data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    pass
```

#### **TypeScript/React**
```typescript
// Props con type definitions
interface DashboardProps {
  apiBase: string;
  refreshInterval?: number;
}

// Componentes funcionales con hooks
const Dashboard: React.FC<DashboardProps> = ({ apiBase, refreshInterval = 5000 }) => {
  const [agents, setAgents] = useState<AgentMetrics[]>([]);
  
  useEffect(() => {
    // Implementation
  }, [apiBase]);
};
```

### **Proceso de Contribución**

1. **Fork** el repositorio
2. **Crear** branch de feature (`git checkout -b feature/nueva-funcionalidad`)
3. **Commit** cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. **Push** al branch (`git push origin feature/nueva-funcionalidad`)
5. **Crear** Pull Request

### **Guidelines de Código**

- **Python**: Seguir PEP 8, usar Black para formateo
- **TypeScript**: Usar ESLint y Prettier
- **Commits**: Mensajes descriptivos en español/inglés
- **Tests**: Incluir tests para nuevas funcionalidades
- **Documentación**: Actualizar README si es necesario

---

## 📞 SOPORTE

### **Documentación Adicional**
- **API Docs**: http://localhost:8000/docs (cuando el servidor está ejecutándose)
- **Template Examples**: Ver directorio `examples/`
- **Integration Guides**: Ver directorio `docs/`

### **Contact Information**
- **Email**: support@iris-mcp.com
- **Issues**: GitHub Issues
- **Documentation**: Este README y archivos en `docs/`

### **Versiones**
- **v1.0.0** - Lanzamiento inicial
- **Próximos releases**: Ver `CHANGELOG.md`

---

**🎉 ¡Gracias por usar IRIS MCP Integration!**

*Este sistema está diseñado para ser extensible, escalable y fácil de usar. Para cualquier pregunta o sugerencia, no dudes en contactarnos.*