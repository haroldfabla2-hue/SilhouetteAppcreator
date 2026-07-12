# Guía Final de Uso - MCP Server Superior

**Versión**: v2.0.0  
**Fecha**: 2025-11-04  
**Estado**: ✅ Guía Completa y Lista para Producción

---

## 🎯 Introducción

Esta guía proporciona instrucciones completas para usar el **MCP Server Superior**, el sistema de orquestación multi-agente más avanzado de la industria. Incluye ejemplos prácticos, demos interactivos y casos de uso reales.

---

## 📋 Tabla de Contenidos

1. [Configuración Inicial](#configuración-inicial)
2. [Inicio Rápido](#inicio-rápido)
3. [Uso de Agentes](#uso-de-agentes)
4. [Orquestación Multi-Agente](#orquestación-multi-agente)
5. [Streaming en Tiempo Real](#streaming-en-tiempo-real)
6. [Casos de Uso Completos](#casos-de-uso-completos)
7. [APIs y Integración](#apis-y-integración)
8. [Performance y Optimización](#performance-y-optimización)
9. [Troubleshooting](#troubleshooting)
10. [Mejores Prácticas](#mejores-prácticas)

---

## 🚀 Configuración Inicial

### 1. Prerrequisitos

```bash
# Verificar versiones mínimas
python --version  # Debe ser 3.11+
docker --version  # Debe ser 24.0+
docker-compose --version  # Debe ser 2.0+

# Verificar puertos disponibles
netstat -tlnp | grep -E ":8000|:3000|:5432|:6379"
```

### 2. Instalación Rápida

#### Opción A: Docker Compose (Desarrollo)
```bash
# 1. Clonar repositorio
git clone https://github.com/mcp-core-superior/mcp-core-superior.git
cd mcp-core-superior

# 2. Configurar variables de entorno
cp .env.example .env

# 3. Editar .env con tus configuraciones
cat > .env << EOF
# Base de datos
DATABASE_URL=postgresql://user:pass@localhost/mcp_core
REDIS_URL=redis://localhost:6379

# Autenticación
JWT_SECRET=tu_jwt_secret_super_seguro_aqui_32_caracteres
CONTEXTFORGE_URL=http://localhost:8001

# API Keys (MiniMax M2 gratis hasta Nov 7, 2025)
MINIMAX_API_KEY=tu_clave_minimax_aqui
OPENROUTER_API_KEY=tu_clave_openrouter_aqui

# Configuración de desarrollo
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
EOF

# 4. Levantar stack completo
docker-compose up -d

# 5. Verificar que todo funciona
curl http://localhost:8000/health
```

#### Opción B: Kubernetes (Producción)
```bash
# 1. Instalar con Helm
helm repo add mcp-superior https://charts.mcp-superior.io
helm repo update

# 2. Crear namespace
kubectl create namespace mcp-system

# 3. Instalar con valores de producción
cat > values-production.yaml << EOF
# Configuración de producción
replicaCount: 3
image:
  tag: "v2.0.0"

database:
  url: "postgresql://user:pass@postgres:5432/mcp_core"
  poolSize: 25
  maxOverflow: 40

redis:
  url: "redis://redis:6379/0"

resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
EOF

# 4. Desplegar
helm install mcp-core mcp-superior/mcp-core-superior \
  --namespace mcp-system \
  --values values-production.yaml

# 5. Verificar deployment
kubectl get pods -n mcp-system
kubectl get services -n mcp-system
```

### 3. Verificación de Instalación

```bash
# Health check completo
./health_check.sh

# Verificar servicios individuales
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:9090/-/healthy

# Verificar base de datos
docker-compose exec backend python -c "
from src.core.database import engine
import asyncio
async def test():
    async with engine.begin() as conn:
        result = await conn.execute('SELECT version()')
        print('✅ Database:', result.scalar())
asyncio.run(test())
"

# Test de agentes
curl -X POST http://localhost:8000/api/v1/agents/test \
  -H "Content-Type: application/json" \
  -d '{"agent": "reasoner", "test_data": {"objective": "Hola mundo"}}'
```

---

## ⚡ Inicio Rápido

### Primer Uso - Análisis Simple

```bash
# Crear primera tarea
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "objetivo": "Analiza las tendencias actuales de inteligencia artificial",
    "user_id": "usuario_ejemplo",
    "context": {
      "dominio": "IA",
      "profundidad": "medio",
      "formato": "resumen"
    }
  }'

# Respuesta esperada:
# {
#   "task_id": "task_abc123",
#   "status": "created",
#   "estimated_duration": 45,
#   "streaming_url": "/api/v1/stream/tasks/task_abc123"
# }
```

### Uso con Streaming

```bash
# En una terminal, iniciar streaming
curl -N -H "Accept: text/event-stream" \
  -H "Cache-Control: no-cache" \
  http://localhost:8000/api/v1/stream/tasks/task_abc123

# En otra terminal, verificar estado
curl http://localhost:8000/api/v1/tasks/task_abc123/status
```

### Python Client Ejemplo

```python
import asyncio
import httpx
from typing import AsyncIterator

class MCPClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def create_task(self, objetivo: str, user_id: str = None):
        """Crear nueva tarea"""
        data = {
            "objetivo": objetivo,
            "user_id": user_id or "python_client"
        }
        response = await self.client.post(
            f"{self.base_url}/api/v1/tasks",
            json=data
        )
        return response.json()
    
    async def stream_updates(self, task_id: str) -> AsyncIterator[dict]:
        """Obtener updates en tiempo real"""
        async with self.client.stream(
            "GET",
            f"{self.base_url}/api/v1/stream/tasks/{task_id}"
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    if data != "heartbeat":
                        yield eval(data)  # Note: In production, use json.loads
    
    async def get_task_result(self, task_id: str):
        """Obtener resultado de tarea"""
        response = await self.client.get(
            f"{self.base_url}/api/v1/tasks/{task_id}"
        )
        return response.json()

# Ejemplo de uso
async def main():
    client = MCPClient()
    
    # Crear tarea
    result = await client.create_task(
        objetivo="Investiga las mejores prácticas de desarrollo con Python",
        user_id="dev_user"
    )
    
    task_id = result["task_id"]
    print(f"Task creada: {task_id}")
    
    # Stream de updates
    print("Streaming updates:")
    async for update in client.stream_updates(task_id):
        print(f"Progreso: {update.get('progress', 0)}% - {update.get('message', '')}")
        
        if update.get('status') == 'completed':
            break
    
    # Obtener resultado final
    result = await client.get_task_result(task_id)
    print(f"Resultado final: {result}")

# Ejecutar
asyncio.run(main())
```

---

## 🤖 Uso de Agentes

### ReasonerAgent - Análisis de Intención

```python
# Análisis básico de intención
curl -X POST http://localhost:8000/api/v1/agents/reasoner/analyze_intent \
  -H "Content-Type: application/json" \
  -d '{
    "objective": "Crear un dashboard de ventas con gráficos interactivos",
    "context": {
      "domain": "business_analytics",
      "complexity": "medium",
      "urgency": "normal"
    }
  }'

# Respuesta:
# {
#   "analysis": {
#     "intent": "create_dashboard",
#     "complexity_score": 0.7,
#     "required_agents": ["python_executor", "file_processing"],
#     "estimated_time": 120,
#     "recommended_approach": "parallel_execution"
#   },
#   "strategy": {
#     "primary_goal": "dashboard_creation",
#     "steps": ["data_analysis", "visualization", "interaction_design"]
#   }
# }
```

### PlannerAgent - Descomposición de Tareas

```python
# Crear plan de ejecución
curl -X POST http://localhost:8000/api/v1/agents/planner/create_plan \
  -H "Content-Type: application/json" \
  -d '{
    "objective": "Analizar ventas Q4 y generar insights",
    "analysis": {
      "intent": "sales_analysis",
      "complexity_score": 0.8
    },
    "constraints": {
      "max_time": 300,
      "parallel_execution": true,
      "data_sources": ["postgresql", "api"]
    }
  }'

# Respuesta:
# {
#   "plan": {
#     "id": "plan_xyz789",
#     "tasks": [
#       {
#         "id": "task_1",
#         "agent": "database_operations",
#         "description": "Extraer datos de ventas Q4",
#         "dependencies": [],
#         "estimated_duration": 30
#       },
#       {
#         "id": "task_2",
#         "agent": "python_executor",
#         "description": "Análisis estadístico de ventas",
#         "dependencies": ["task_1"],
#         "estimated_duration": 45
#       }
#     ],
#     "execution_strategy": "parallel_with_dependencies"
#   }
# }
```

### ExecutorAgent - Ejecución de Herramientas

```python
# Ejecutar múltiples herramientas en paralelo
curl -X POST http://localhost:8000/api/v1/agents/executor/execute \
  -H "Content-Type: application/json" \
  -d '{
    "plan": {
      "tasks": [
        {"id": "task_1", "tool": "python_executor", "command": "analyze_sales"},
        {"id": "task_2", "tool": "web_scraping", "url": "https://api.market-data.com"},
        {"id": "task_3", "tool": "file_processing", "file": "sales_data.csv"}
      ]
    },
    "max_concurrent": 3,
    "timeout_seconds": 300
  }'

# Respuesta:
# {
#   "execution_id": "exec_abc123",
#   "status": "completed",
#   "results": {
#     "task_1": {"status": "success", "result": "analysis_complete"},
#     "task_2": {"status": "success", "data": [...]},
#     "task_3": {"status": "success", "output": "processed"}
#   },
#   "execution_time": 67.5
# }
```

### VerifierAgent - Validación de Resultados

```python
# Validar calidad de resultados
curl -X POST http://localhost:8000/api/v1/agents/verifier/validate \
  -H "Content-Type: application/json" \
  -d '{
    "execution_results": {
      "analysis": "Completado con 95% confianza",
      "charts": ["sales_trend", "product_performance"],
      "insights": ["Crecimiento 15%", "Producto X lidera"]
    },
    "validation_criteria": [
      "accuracy > 90%",
      "completeness > 95%",
      "consistency = true"
    ],
    "quality_threshold": 0.85
  }'

# Respuesta:
# {
#   "validation_result": {
#     "overall_score": 0.92,
#     "passed": true,
#     "checks": [
#       {"criterion": "accuracy", "score": 0.95, "passed": true},
#       {"criterion": "completeness", "score": 0.89, "passed": true},
#       {"criterion": "consistency", "score": 0.92, "passed": true}
#     ]
#   },
#   "recommendations": [
#     "Considerar validar datos de entrada",
#     "Excelente análisis estadístico"
#   ]
# }
```

---

## 🔄 Orquestación Multi-Agente

### Flujo Completo Automático

```python
# Orquestación completa con streaming
import asyncio
import websockets
import json

async def orchestrate_complete_workflow():
    # 1. Crear tarea
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/tasks",
            json={
                "objetivo": "Crear reporte ejecutivo completo de performance Q4",
                "context": {
                    "department": "sales",
                    "format": "executive_report",
                    "include_charts": True
                },
                "streaming_enabled": True
            }
        )
    
    task_data = response.json()
    task_id = task_data["task_id"]
    
    print(f"Orquestación iniciada: {task_id}")
    
    # 2. Conectar a WebSocket para updates
    ws_url = f"ws://localhost:8000/ws/stream/tasks/{task_id}"
    
    async with websockets.connect(ws_url) as websocket:
        while True:
            try:
                # Recibir update
                message = await websocket.recv()
                update = json.loads(message)
                
                # Mostrar progreso
                status = update.get("status", "unknown")
                progress = update.get("progress", 0)
                current_agent = update.get("current_agent", "unknown")
                
                print(f"[{progress:3d}%] {current_agent}: {status}")
                
                # Si completó, obtener resultado
                if status == "completed":
                    result = await client.get(f"http://localhost:8000/api/v1/tasks/{task_id}")
                    print("\n🎉 ORQUESTACIÓN COMPLETADA")
                    print(f"Resultado: {result.json()}")
                    break
                    
            except websockets.exceptions.ConnectionClosed:
                print("Conexión cerrada")
                break

# Ejecutar ejemplo
asyncio.run(orchestrate_complete_workflow())
```

### MCP Client Integration

```python
# Integración directa con MCP
from mcp import ClientSession

async def mcp_orchestration_example():
    """Ejemplo usando MCP client directamente"""
    
    async with ClientSession("stdio", {
        "command": "python",
        "args": ["run.sh"]
    }) as session:
        
        # Initialize connection
        await session.initialize()
        
        # List available tools
        tools = await session.list_tools()
        print("Herramientas disponibles:", [tool.name for tool in tools.tools])
        
        # Orquestación completa
        result = await session.call_tool("orchestrate_multitask", {
            "objective": "Analiza datos de ventas y crea dashboard",
            "context": {
                "data_source": "postgresql://sales_db",
                "charts_required": ["trend", "pie", "bar"],
                "export_format": "html"
            },
            "streaming_enabled": True,
            "quality_threshold": 0.8
        })
        
        print("Resultado de orquestación:")
        print(result.content[0].text)
```

---

## 🌊 Streaming en Tiempo Real

### Server-Sent Events (SSE)

```javascript
// Frontend JavaScript - Cliente de streaming
class TaskStreamManager {
    constructor(taskId, onUpdate, onComplete) {
        this.taskId = taskId;
        this.onUpdate = onUpdate;
        this.onComplete = onComplete;
        this.eventSource = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }
    
    connect() {
        const url = `/api/v1/stream/tasks/${this.taskId}`;
        this.eventSource = new EventSource(url);
        
        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                // Reset reconnect attempts on successful message
                this.reconnectAttempts = 0;
                
                // Call update handler
                this.onUpdate(data);
                
                // Check if completed
                if (data.status === 'completed') {
                    this.onComplete(data);
                    this.disconnect();
                }
                
            } catch (error) {
                console.error('Error parsing stream data:', error);
            }
        };
        
        this.eventSource.onerror = (error) => {
            console.error('Stream error:', error);
            this.handleReconnection();
        };
        
        this.eventSource.onopen = () => {
            console.log('Stream connection opened');
        };
    }
    
    handleReconnection() {
        this.reconnectAttempts++;
        
        if (this.reconnectAttempts <= this.maxReconnectAttempts) {
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            console.log(`Reconnecting in ${delay}ms...`);
            
            setTimeout(() => {
                this.disconnect();
                this.connect();
            }, delay);
        } else {
            console.error('Max reconnection attempts reached');
            this.disconnect();
        }
    }
    
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
}

// Uso del manager
const streamManager = new TaskStreamManager(
    'task_abc123',
    (update) => {
        // Actualizar UI
        updateProgressBar(update.progress);
        updateStatusText(update.message);
        updateAgentStatus(update.agent_status);
        
        // Log detallado
        console.log(`[${update.progress}%] ${update.current_agent}: ${update.message}`);
    },
    (result) => {
        // Task completed
        showCompletionNotification(result);
        displayFinalResults(result);
    }
);

streamManager.connect();
```

### WebSocket Alternative

```python
# Backend - WebSocket handler
from fastapi import WebSocket
from starlette.websockets import WebSocketState

@app.websocket("/ws/stream/tasks/{task_id}")
async def websocket_stream(websocket: WebSocket, task_id: str):
    await websocket.accept()
    
    try:
        while True:
            # Get task status
            status = await get_task_status(task_id)
            
            # Send update
            await websocket.send_json({
                "task_id": task_id,
                "status": status.state,
                "progress": status.progress,
                "current_agent": status.current_agent,
                "message": status.message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Check if completed
            if status.state == "completed":
                break
            
            # Wait before next update
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for task {task_id}")
```

---

## 🎯 Casos de Uso Completos

### 1. Análisis de Datos Empresarial

```python
# Escenario: Análisis completo de ventas Q4
import asyncio
import httpx

async def sales_analysis_q4():
    client = httpx.AsyncClient(base_url="http://localhost:8000")
    
    # 1. Crear tarea de análisis
    task_response = await client.post("/api/v1/tasks", json={
        "objetivo": "Análisis completo de ventas Q4 con insights ejecutivos",
        "context": {
            "type": "business_analytics",
            "period": "Q4_2024",
            "scope": "global",
            "deliverables": ["report", "dashboard", "insights"],
            "stakeholders": ["executives", "sales_team", "finance"]
        },
        "streaming_enabled": True
    })
    
    task_data = task_response.json()
    task_id = task_data["task_id"]
    
    print(f"📊 Iniciando análisis de ventas Q4: {task_id}")
    
    # 2. Streaming de progreso
    async with client.stream("GET", f"/api/v1/stream/tasks/{task_id}") as response:
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = eval(line[6:])
                
                progress = data.get("progress", 0)
                agent = data.get("current_agent", "")
                message = data.get("message", "")
                
                print(f"  [{progress:3d}%] {agent}: {message}")
                
                # Mostrar resultados parciales
                if "partial_results" in data:
                    results = data["partial_results"]
                    if "charts_generated" in results:
                        print(f"    📈 Gráficos generados: {results['charts_generated']}")
    
    # 3. Obtener resultado final
    final_result = await client.get(f"/api/v1/tasks/{task_id}")
    result_data = final_result.json()
    
    print("\n🎉 ANÁLISIS COMPLETADO")
    print(f"📈 Reporte: {result_data['result']['report_path']}")
    print(f"📊 Dashboard: {result_data['result']['dashboard_url']}")
    print(f"💡 Insights clave: {len(result_data['result']['insights'])}")
    
    # Mostrar insights
    for i, insight in enumerate(result_data['result']['insights'], 1):
        print(f"  {i}. {insight}")
    
    return result_data

# Ejecutar análisis
result = asyncio.run(sales_analysis_q4())
```

### 2. Desarrollo de Software Asistido

```python
# Escenario: Desarrollo de API REST
async def api_development_assistant():
    client = httpx.AsyncClient(base_url="http://localhost:8000")
    
    # 1. Requerimientos
    requirements = """
    Crear API REST para gestión de usuarios con:
    - Autenticación JWT
    - CRUD de usuarios
    - Rate limiting
    - Documentación OpenAPI
    - Tests unitarios
    - Docker containerization
    """
    
    # 2. Crear tarea de desarrollo
    task = await client.post("/api/v1/tasks", json={
        "objetivo": requirements,
        "context": {
            "type": "software_development",
            "framework": "fastapi",
            "database": "postgresql",
            "authentication": "jwt",
            "testing": "pytest",
            "deployment": "docker"
        },
        "streaming_enabled": True
    })
    
    task_id = task.json()["task_id"]
    print(f"🚀 Iniciando desarrollo de API: {task_id}")
    
    # 3. Monitorear desarrollo
    async with client.stream("GET", f"/api/v1/stream/tasks/{task_id}") as response:
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = eval(line[6:])
                
                agent = data.get("current_agent", "")
                message = data.get("message", "")
                
                # Mapear agentes a actividades
                activities = {
                    "python_executor": "💻 Código",
                    "git_operations": "📁 Git",
                    "file_processing": "📄 Documentación",
                    "database_operations": "🗄️ Base de datos",
                    "verifier": "✅ Testing"
                }
                
                activity = activities.get(agent, f"🤖 {agent}")
                print(f"  {activity}: {message}")
                
                # Mostrar archivos creados
                if "files_created" in data.get("partial_results", {}):
                    files = data["partial_results"]["files_created"]
                    for file in files:
                        print(f"    ✨ {file}")
    
    print("\n🎉 DESARROLLO COMPLETADO")
    return await client.get(f"/api/v1/tasks/{task_id}")

# Ejecutar desarrollo
result = asyncio.run(api_development_assistant())
```

### 3. Investigación y Síntesis

```python
# Escenario: Investigación de mercado
async def market_research():
    client = httpx.AsyncClient(base_url="http://localhost:8000")
    
    # 1. Query de investigación
    research_query = """
    Investiga el mercado de IA generativa en healthcare para 2025:
    - Tendencias tecnológicas
    - Principales players
    - Oportunidades de inversión
    - Regulaciones emergentes
    - Proyecciones de mercado
    """
    
    # 2. Crear tarea de investigación
    task = await client.post("/api/v1/tasks", json={
        "objetivo": research_query,
        "context": {
            "type": "market_research",
            "industry": "healthcare_ai",
            "timeframe": "2025",
            "depth": "comprehensive",
            "sources": ["web", "academic", "industry_reports"]
        },
        "streaming_enabled": True
    })
    
    task_id = task.json()["task_id"]
    print(f"🔍 Iniciando investigación de mercado: {task_id}")
    
    # 3. Streaming de investigación
    async with client.stream("GET", f"/api/v1/stream/tasks/{task_id}") as response:
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = eval(line[6:])
                
                agent = data.get("current_agent", "")
                message = data.get("message", "")
                
                # Mapear agentes a fuentes
                sources = {
                    "search_engine": "🔍 Búsqueda web",
                    "web_scraping": "🕷️ Scraping",
                    "file_processing": "📊 Análisis de datos"
                }
                
                source = sources.get(agent, f"🤖 {agent}")
                print(f"  {source}: {message}")
                
                # Mostrar fuentes consultadas
                if "sources_consulted" in data.get("partial_results", {}):
                    sources_count = len(data["partial_results"]["sources_consulted"])
                    print(f"    📚 Fuentes consultadas: {sources_count}")
    
    print("\n🎉 INVESTIGACIÓN COMPLETADA")
    return await client.get(f"/api/v1/tasks/{task_id}")

# Ejecutar investigación
result = asyncio.run(market_research())
```

---

## 🔌 APIs y Integración

### REST API Reference

```python
# API Endpoints disponibles

# Health checks
GET /health                          # Estado general del sistema
GET /api/v1/status                   # Estado detallado de componentes
GET /api/v1/metrics                  # Métricas del sistema

# Task management
POST /api/v1/tasks                   # Crear nueva tarea
GET /api/v1/tasks/{task_id}          # Obtener tarea específica
GET /api/v1/tasks/{task_id}/status   # Estado de tarea
DELETE /api/v1/tasks/{task_id}       # Cancelar tarea

# Agents
POST /api/v1/agents/{agent}/analyze  # Usar agente específico
GET /api/v1/agents/status            # Estado de todos los agentes
GET /api/v1/agents/{agent}/metrics   # Métricas por agente

# Streaming
GET /api/v1/stream/tasks/{task_id}   # SSE stream de actualizaciones
WS /ws/stream/tasks/{task_id}        # WebSocket stream alternativo

# LLM Router
POST /api/v1/llm/test                # Test de conectividad LLM
GET /api/v1/llm/providers            # Estado de proveedores
POST /api/v1/llm/route               # Enrutamiento manual

# Admin
GET /api/v1/admin/stats              # Estadísticas administrativas
GET /api/v1/admin/logs               # Logs del sistema
POST /api/v1/admin/reset             # Reset del sistema
```

### Python SDK

```python
# SDK completo para integración
from mcp_superior import MCPClient, TaskManager, AgentManager

class MCPSuperiorSDK:
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        self.client = MCPClient(base_url, api_key)
        self.tasks = TaskManager(self.client)
        self.agents = AgentManager(self.client)
    
    async def analyze_data(self, data: dict, analysis_type: str = "general"):
        """Análisis de datos con agentes especializados"""
        return await self.tasks.create_task(
            objetivo=f"Analyze {analysis_type} data",
            context={
                "data": data,
                "analysis_type": analysis_type,
                "agents_required": ["reasoner", "planner", "executor"]
            }
        )
    
    async def generate_report(self, source: str, format: str = "pdf"):
        """Generar reporte completo"""
        return await self.tasks.create_task(
            objetivo=f"Generate comprehensive report from {source}",
            context={
                "source": source,
                "format": format,
                "streaming": True
            }
        )
    
    async def process_files(self, files: List[str], operations: List[str]):
        """Procesar archivos con FileProcessingAgent"""
        return await self.agents.call_tool("file_processing", {
            "operation": "batch_process",
            "files": files,
            "operations": operations
        })

# Uso del SDK
async def sdk_example():
    sdk = MCPSuperiorSDK()
    
    # Análisis de datos
    data_result = await sdk.analyze_data(
        data={"sales": [100, 150, 200]},
        analysis_type="trend_analysis"
    )
    
    print(f"Análisis creado: {data_result.task_id}")

# Instalar SDK
pip install mcp_superior_sdk
```

### JavaScript SDK

```javascript
// SDK para frontend JavaScript
class MCPSuperiorJS {
    constructor(baseUrl, options = {}) {
        this.baseUrl = baseUrl;
        this.options = options;
        this.eventSources = new Map();
    }
    
    // Crear y manejar tareas
    async createTask(objective, context = {}) {
        const response = await fetch(`${this.baseUrl}/api/v1/tasks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(this.options.apiKey && { 'Authorization': `Bearer ${this.options.apiKey}` })
            },
            body: JSON.stringify({ objective, context })
        });
        
        return await response.json();
    }
    
    // Streaming de updates
    streamTask(taskId, onUpdate, onComplete) {
        const url = `${this.baseUrl}/api/v1/stream/tasks/${taskId}`;
        
        const eventSource = new EventSource(url);
        this.eventSources.set(taskId, eventSource);
        
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            onUpdate(data);
            
            if (data.status === 'completed') {
                onComplete(data);
                this.disconnect(taskId);
            }
        };
        
        eventSource.onerror = (error) => {
            console.error('Stream error:', error);
            this.disconnect(taskId);
        };
        
        return eventSource;
    }
    
    // Usar agentes específicos
    async callAgent(agentName, parameters) {
        const response = await fetch(`${this.baseUrl}/api/v1/agents/${agentName}/call`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(parameters)
        });
        
        return await response.json();
    }
    
    // Desconectar stream
    disconnect(taskId) {
        const eventSource = this.eventSources.get(taskId);
        if (eventSource) {
            eventSource.close();
            this.eventSources.delete(taskId);
        }
    }
}

// Uso del SDK
const sdk = new MCPSuperiorJS('http://localhost:8000');

// Crear tarea con streaming
const task = await sdk.createTask(
    'Analyze user behavior data',
    { format: 'dashboard' }
);

sdk.streamTask(task.task_id, 
    (update) => {
        updateProgressBar(update.progress);
        showAgentStatus(update.current_agent);
    },
    (result) => {
        showCompletionNotification();
        displayResults(result);
    }
);
```

---

## ⚡ Performance y Optimización

### Métricas de Performance

```python
# Monitoring de performance
import time
import psutil
from prometheus_client import Counter, Histogram, Gauge

# Métricas custom
request_count = Counter('mcp_requests_total', 'Total requests', ['endpoint', 'method'])
request_duration = Histogram('mcp_request_duration_seconds', 'Request duration')
active_connections = Gauge('mcp_active_connections', 'Active connections')
memory_usage = Gauge('mcp_memory_usage_mb', 'Memory usage in MB')

class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
    
    @request_duration.time()
    async def measure_request(self, func, *args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        
        # Actualizar métricas
        active_connections.set(1)  # O usar pool de conexiones
        memory_usage.set(psutil.Process().memory_info().rss / 1024 / 1024)
        
        return result
    
    def get_stats(self):
        return {
            "uptime": time.time() - self.start_time,
            "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024,
            "cpu_percent": psutil.cpu_percent(),
            "active_connections": active_connections._value._value._value
        }

# Uso del monitor
monitor = PerformanceMonitor()

# En endpoint
@app.get("/api/v1/analytics/performance")
async def get_performance_stats():
    await monitor.measure_request(slow_operation)
    return monitor.get_stats()
```

### Optimización de Queries

```python
# Optimización de database queries
from sqlalchemy import text
import asyncio

class QueryOptimizer:
    @staticmethod
    async def optimize_vector_search(query_embedding, threshold=0.8, limit=10):
        """Búsqueda vectorial optimizada"""
        
        # Usar índices IVFFLAT para performance
        query = text("""
            SELECT id, content, 
                   1 - (embedding <=> :query_embedding) as similarity
            FROM documents 
            WHERE 1 - (embedding <=> :query_embedding) > :threshold
            ORDER BY embedding <=> :query_embedding
            LIMIT :limit
        """)
        
        # Cache de embeddings frecuentes
        cache_key = f"search:{hash(str(query_embedding))}"
        cached_result = await redis_client.get(cache_key)
        
        if cached_result:
            return json.loads(cached_result)
        
        # Ejecutar query optimizada
        async with engine.begin() as conn:
            result = await conn.execute(query, {
                "query_embedding": query_embedding,
                "threshold": threshold,
                "limit": limit
            })
            
            rows = result.fetchall()
            
            # Cache result
            await redis_client.setex(
                cache_key, 
                300,  # 5 minutos
                json.dumps([dict(row) for row in rows])
            )
            
            return rows
    
    @staticmethod
    async def batch_operations(operations):
        """Ejecutar operaciones en lote"""
        async with engine.begin() as conn:
            # Begin transaction
            trans = await conn.begin()
            
            try:
                results = []
                for operation in operations:
                    result = await conn.execute(operation)
                    results.append(result)
                
                await trans.commit()
                return results
                
            except Exception as e:
                await trans.rollback()
                raise e

# Uso del optimizador
optimizer = QueryOptimizer()
results = await optimizer.optimize_vector_search(
    query_embedding=embedding,
    threshold=0.85,
    limit=20
)
```

---

## 🔧 Troubleshooting

### Debugging Tools

```python
# Herramientas de debugging
import logging
import json
from datetime import datetime

class DebugManager:
    def __init__(self, log_level="DEBUG"):
        self.logger = self.setup_logging(log_level)
        self.debug_data = []
    
    def setup_logging(self, level):
        """Setup structured logging"""
        logging.basicConfig(
            level=getattr(logging, level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def log_agent_execution(self, agent_name, input_data, output_data, duration):
        """Log agent execution details"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent_name,
            "input_size": len(str(input_data)),
            "output_size": len(str(output_data)),
            "duration_ms": duration * 1000,
            "success": output_data is not None
        }
        
        self.debug_data.append(log_entry)
        self.logger.info(f"Agent {agent_name} execution", extra=log_entry)
    
    def get_debug_report(self):
        """Generate debug report"""
        return {
            "total_executions": len(self.debug_data),
            "agents_used": list(set(entry["agent"] for entry in self.debug_data)),
            "average_duration": sum(entry["duration_ms"] for entry in self.debug_data) / len(self.debug_data),
            "success_rate": sum(1 for entry in self.debug_data if entry["success"]) / len(self.debug_data),
            "detailed_logs": self.debug_data[-100:]  # Last 100 entries
        }

# Uso del debug manager
debug = DebugManager()

# En agentes
debug.log_agent_execution(
    agent_name="reasoner",
    input_data=objective,
    output_data=analysis_result,
    duration=execution_time
)
```

### Health Check Script

```bash
#!/bin/bash
# comprehensive_health_check.sh

echo "=== MCP Server Superior Health Check ==="
echo "Timestamp: $(date)"
echo ""

# 1. Service Status
echo "1. Service Status:"
docker-compose ps
echo ""

# 2. Database Health
echo "2. Database Health:"
if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL: Healthy"
else
    echo "❌ PostgreSQL: Unhealthy"
fi

# 3. Redis Health
echo "3. Redis Health:"
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis: Healthy"
else
    echo "❌ Redis: Unhealthy"
fi

# 4. API Health
echo "4. API Health:"
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API: Healthy"
else
    echo "❌ API: Unhealthy"
fi

# 5. LLM Router Test
echo "5. LLM Router Test:"
if curl -s -X POST "http://localhost:8000/api/v1/llm/test?prompt=test" > /dev/null; then
    echo "✅ LLM Router: Healthy"
else
    echo "❌ LLM Router: Unhealthy"
fi

# 6. Resource Usage
echo "6. Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# 7. Recent Errors
echo "7. Recent Errors:"
ERROR_COUNT=$(docker-compose logs --tail=100 backend | grep -i error | wc -l)
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "⚠️  Found $ERROR_COUNT errors in recent logs"
    docker-compose logs --tail=10 backend | grep -i error
else
    echo "✅ No recent errors found"
fi

echo ""
echo "=== Health Check Completed ==="
```

---

## 💡 Mejores Prácticas

### 1. Task Management

```python
# Mejores prácticas para gestión de tareas
class TaskBestPractices:
    @staticmethod
    def create_task_smart(objective, context=None, priority="normal"):
        """Crear tareas con configuración óptima"""
        
        # Auto-detect complexity
        complexity_indicators = [
            "análisis", "investigar", "crear", "desarrollar", "generar"
        ]
        
        is_complex = any(word in objective.lower() 
                        for word in complexity_indicators)
        
        # Auto-configure based on complexity
        optimal_config = {
            "normal": {
                "timeout": 300,
                "parallel_agents": True,
                "quality_threshold": 0.8
            },
            "complex": {
                "timeout": 600,
                "parallel_agents": True,
                "quality_threshold": 0.9,
                "detailed_logging": True
            }
        }
        
        config = optimal_config["complex" if is_complex else "normal"]
        
        return {
            "objective": objective,
            "context": context or {},
            "priority": priority,
            **config
        }
    
    @staticmethod
    async def monitor_task_health(task_id, check_interval=30):
        """Monitorear salud de tarea durante ejecución"""
        
        while True:
            status = await get_task_status(task_id)
            
            if status.state == "completed":
                return {"status": "completed", "result": status.result}
            elif status.state == "failed":
                return {"status": "failed", "error": status.error}
            elif status.state == "timeout":
                return {"status": "timeout", "message": "Task exceeded timeout"}
            
            # Check for stuck tasks
            if status.last_update < time.time() - (check_interval * 2):
                logger.warning(f"Task {task_id} may be stuck")
            
            await asyncio.sleep(check_interval)
```

### 2. Resource Management

```python
# Gestión eficiente de recursos
class ResourceManager:
    def __init__(self, max_concurrent_tasks=10):
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.active_tasks = {}
    
    async def execute_with_limit(self, task_func, *args, **kwargs):
        """Ejecutar tarea con límite de concurrencia"""
        
        async with self.semaphore:
            task_id = str(uuid.uuid4())
            self.active_tasks[task_id] = {
                "start_time": time.time(),
                "status": "running"
            }
            
            try:
                result = await task_func(*args, **kwargs)
                self.active_tasks[task_id]["status"] = "completed"
                return result
                
            except Exception as e:
                self.active_tasks[task_id]["status"] = "failed"
                self.active_tasks[task_id]["error"] = str(e)
                raise e
                
            finally:
                duration = time.time() - self.active_tasks[task_id]["start_time"]
                logger.info(f"Task {task_id} completed in {duration:.2f}s")
                del self.active_tasks[task_id]
    
    def get_active_tasks(self):
        """Obtener estado de tareas activas"""
        return self.active_tasks

# Uso del resource manager
resource_manager = ResourceManager(max_concurrent_tasks=5)

result = await resource_manager.execute_with_limit(
    expensive_analysis,
    data=large_dataset
)
```

### 3. Error Handling

```python
# Manejo robusto de errores
class ErrorHandler:
    @staticmethod
    def create_fallback_strategy(primary_func, fallback_funcs):
        """Crear estrategia de fallback"""
        
        async def execute_with_fallback(*args, **kwargs):
            # Intentar función principal
            try:
                return await primary_func(*args, **kwargs)
                
            except Exception as e:
                logger.warning(f"Primary function failed: {e}")
                
                # Intentar fallbacks en orden
                for fallback in fallback_funcs:
                    try:
                        result = await fallback(*args, **kwargs)
                        logger.info(f"Fallback {fallback.__name__} succeeded")
                        return result
                    except Exception as fallback_error:
                        logger.warning(f"Fallback {fallback.__name__} failed: {fallback_error}")
                        continue
                
                # Si todos fallan, usar respuesta por defecto
                logger.error("All functions failed, using default response")
                return {
                    "status": "error",
                    "message": "Service temporarily unavailable",
                    "fallback_used": True
                }
        
        return execute_with_fallback
    
    @staticmethod
    def handle_agent_failure(agent_name, error, retry_count=3):
        """Manejar fallos de agentes con retry"""
        
        if retry_count > 0:
            logger.warning(f"Agent {agent_name} failed, retrying... ({retry_count} attempts left)")
            time.sleep(2 ** (3 - retry_count))  # Exponential backoff
            
            return retry_with_fallback(
                agent_name, 
                error, 
                retry_count - 1
            )
        else:
            logger.error(f"Agent {agent_name} failed permanently: {error}")
            
            # Usar agente alternativo o respuesta por defecto
            return get_agent_fallback(agent_name)

# Uso del error handler
async def robust_analysis(data):
    error_handler = ErrorHandler()
    
    return await error_handler.create_fallback_strategy(
        primary_func=advanced_analysis,
        fallback_funcs=[
            basic_analysis,
            simple_summary,
            fallback_response
        ]
    )(data)
```

---

## 📞 Soporte y Contacto

### Recursos de Documentación
- **Documentación Técnica**: `/workspace/mcp-core-superior/docs/`
- **Ejemplos Interactivos**: `/workspace/mcp-core-superior/examples/`
- **Tests y Validación**: `/workspace/mcp-core-superior/tests/`
- **Arquitectura**: `/workspace/mcp-core-superior/docs/architecture/`

### Canales de Soporte
- **GitHub Issues**: Para bugs y feature requests
- **GitHub Discussions**: Para preguntas técnicas y soporte
- **Email**: support@mcp-superior.io
- **Slack**: #mcp-core-superior
- **Documentación**: http://localhost:8000/docs

### Scripts de Utilidad
```bash
# Scripts disponibles en el proyecto
./health_check.sh              # Verificación completa de salud
./quickstart.py                # Inicio rápido con Python
./quickstart.sh                # Inicio rápido con Shell
./setup.sh                     # Configuración inicial
./start.sh                     # Iniciar servicios
./validate_system.sh           # Validación de sistema
```

### Comandos Útiles
```bash
# Gestión de servicios
docker-compose up -d          # Iniciar servicios
docker-compose down           # Detener servicios
docker-compose logs -f backend # Ver logs
docker-compose exec backend bash # Shell en container

# Monitoreo
curl http://localhost:8000/metrics    # Métricas Prometheus
curl http://localhost:8000/health     # Health check
curl http://localhost:9090            # Grafana

# API Testing
curl -X POST http://localhost:8000/api/v1/llm/test?prompt=hello
```

---

## 🎉 Conclusión

Esta guía proporciona todo lo necesario para usar exitosamente el **MCP Server Superior**. Con estas herramientas y ejemplos, puedes:

1. **Configurar el sistema** en cualquier entorno
2. **Usar los 12 agentes especializados** eficientemente
3. **Implementar orquestación multi-agente** para casos complejos
4. **Monitorear performance** y optimizar uso
5. **Solucionar problemas** rápidamente
6. **Integrar en aplicaciones** existentes

El sistema está diseñado para ser **intuitivo, potente y escalable**, proporcionando capacidades únicas que no encontrarás en ninguna otra solución de la industria.

---

**MCP Server Superior v2.0.0**  
**Guía Final de Uso**: 2025-11-04  
**Estado**: ✅ Completa y Lista para Producción

*¡Disfruta usando el sistema de orquestación multi-agente más avanzado del mundo!* 🚀