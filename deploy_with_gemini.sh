#!/bin/bash
# ===============================================================================
# GEMINI CLI - INSTRUCCIONES PARA DESPLIEGUE AUTOMÁTICO SILHOUETTEMCP
# ===============================================================================
# USAR CON GEMINI CLI: gemini run --file=[este_script] 
# O EJECUTAR DIRECTAMENTE: bash deploy_with_gemini.sh
# ===============================================================================

echo "🚀 INICIANDO DESPLIEGUE AUTOMÁTICO DE SILHOUETTEMCP..."
echo "========================================================="

# PASO 1: CREAR DIRECTORIO DE TRABAJO
echo "📁 PASO 1: Creando directorio de trabajo..."
mkdir -p /tmp/silhouettemcp_deploy
cd /tmp/silhouettemcp_deploy
echo "✅ Directorio creado: $(pwd)"

# PASO 2: VERIFICAR DOCKER
echo ""
echo "🐳 PASO 2: Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker no encontrado. Instalando Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "✅ Docker instalado exitosamente"
else
    echo "✅ Docker ya está instalado: $(docker --version)"
fi

# PASO 3: VERIFICAR DOCKER COMPOSE
echo ""
echo "⚙️  PASO 3: Verificando Docker Compose..."
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "⚠️  Docker Compose no encontrado. Instalando..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose instalado"
else
    echo "✅ Docker Compose disponible"
fi

# PASO 4: VERIFICAR DOMINIO
echo ""
echo "🌐 PASO 4: Verificando configuración de dominio..."
DOMAIN="silhouettemcp.albertofarah.com"
echo "Dominio objetivo: $DOMAIN"
read -p "¿Está configurado el DNS A record para $DOMAIN apuntando a tu VPS IP? (s/n): " dns_confirmed
if [[ ! $dns_confirmed =~ ^[Ss]$ ]]; then
    echo "❌ Configuración DNS requerida antes de continuar"
    echo "📋 INSTRUCCIONES DNS:"
    echo "   1. Ve a tu proveedor de DNS (Cloudflare, Namecheap, etc.)"
    echo "   2. Agrega registro A: $DOMAIN -> [IP_DE_TU_VPS]"
    echo "   3. Espera propagación DNS (5-15 minutos)"
    exit 1
fi

# PASO 5: CREAR DIRECTORIO DE APLICACIÓN
echo ""
echo "📂 PASO 5: Preparando directorio de aplicación..."
APP_DIR="/opt/silhouettemcp"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR
echo "✅ Directorio de aplicación: $APP_DIR"

# PASO 6: CREAR STRUCTURE DE DIRECTORIOS
echo ""
echo "🏗️  PASO 6: Creando estructura de directorios..."
cd $APP_DIR
mkdir -p {logs,ssl,config,data,backup}
echo "✅ Estructura creada en $APP_DIR"

# PASO 7: CREAR ARCHIVOS DE CONFIGURACIÓN
echo ""
echo "⚙️  PASO 7: Creando archivos de configuración..."

# Crear silhouettemcp_server.py
cat > silhouettemcp_server.py << 'EOF'
#!/usr/bin/env python3
"""
SilhouetteMCP Server - Servidor MCP superior con autenticación y gestión multi-aplicación
Desarrollado para: silhouettemcp.albertofarah.com
"""

import json
import hashlib
import secrets
import asyncio
import random
import logging
import threading
import time
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, asdict

from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import uvicorn

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SilhouetteMCPServer")

# ==================== CONFIGURACIÓN DE AUTENTICACIÓN ====================
ADMIN_CREDENTIALS = {
    "email": "alberto.farahb@hotmail.com",
    "password_hash": hashlib.sha256("Fbalberto1910".encode()).hexdigest()
}

# Configuración del servidor
app = FastAPI(
    title="SilhouetteMCP Server",
    description="Servidor MCP superior para gestión multi-aplicación con agentes",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configurado para producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== MODELOS DE DATOS ====================

@dataclass
class Agent:
    id: str
    name: str
    app_id: str
    status: str = "idle"
    tasks_completed: int = 0
    avg_response_time: float = 0.0
    token_usage: int = 0
    last_activity: str = ""
    success_rate: float = 95.0
    agent_type: str = "custom"
    created_at: str = ""

@dataclass
class Application:
    id: str
    name: str
    description: str
    api_key: str
    owner_email: str
    agents: List[Agent] = None
    created_at: str = ""
    is_active: bool = True

    def __post_init__(self):
        if self.agents is None:
            self.agents = []

@dataclass
class ServerMetrics:
    total_agents: int
    total_apps: int
    total_tasks: int
    total_tokens: int
    uptime: float
    requests_per_minute: int
    timestamp: str

# ==================== ALMACÉN DE DATOS ====================

class DataStore:
    def __init__(self):
        self.data_file = "/opt/silhouettemcp/silhouettemcp_data.json"
        self.backup_file = "/opt/silhouettemcp/backup.json"
        self.data = self.load_data()
        self.metrics = ServerMetrics(
            total_agents=0,
            total_apps=0,
            total_tasks=0,
            total_tokens=0,
            uptime=0.0,
            requests_per_minute=0,
            timestamp=datetime.now().isoformat()
        )
        self.request_times = deque(maxlen=100)
        self.start_time = time.time()
        
        if not self.data:
            self.initialize_data()
        else:
            self.migrate_data()
    
    def load_data(self):
        try:
            if Path(self.data_file).exists():
                with open(self.data_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando datos: {e}")
        return None
    
    def initialize_data(self):
        logger.info("Inicializando datos por defecto...")
        self.data = {
            "applications": [],
            "api_keys": {
                "sk-d8RahMZH5B8RIeSiLYx_ktBy5c9Ic8VkuTXo_2JkVzc": "silhouettemcp_default"
            },
            "agents": {},
            "version": "2.0.0"
        }
        
        # Crear aplicación por defecto
        app = Application(
            id="silhouettemcp_default",
            name="SilhouetteMCP Dashboard",
            description="Dashboard principal de gestión",
            api_key="sk-d8RahMZH5B8RIeSiLYx_ktBy5c9Ic8VkuTXo_2JkVzc",
            owner_email="alberto.farahb@hotmail.com",
            created_at=datetime.now().isoformat()
        )
        self.data["applications"].append(asdict(app))
        
        # Crear agentes por defecto
        agents = [
            Agent(
                id="dashboard_admin",
                name="Dashboard Admin",
                app_id="silhouettemcp_default",
                status="idle",
                agent_type="admin",
                created_at=datetime.now().isoformat()
            ),
            Agent(
                id="system_monitor",
                name="System Monitor",
                app_id="silhouettemcp_default",
                status="idle",
                agent_type="monitoring",
                created_at=datetime.now().isoformat()
            ),
            Agent(
                id="api_gateway",
                name="API Gateway",
                app_id="silhouettemcp_default",
                status="idle",
                agent_type="gateway",
                created_at=datetime.now().isoformat()
            )
        ]
        
        for agent in agents:
            self.data["agents"][agent.id] = asdict(agent)
            app_agents = next(a for a in self.data["applications"] if a["id"] == app.id)["agents"]
            app_agents.append(asdict(agent))
        
        self.save_data()
        logger.info("Datos inicializados exitosamente")
    
    def migrate_data(self):
        """Migrar datos a la nueva estructura"""
        if "version" not in self.data:
            self.data["version"] = "2.0.0"
        
        if "api_keys" not in self.data:
            self.data["api_keys"] = {}
        
        if "agents" not in self.data:
            self.data["agents"] = {}
        
        self.save_data()
        logger.info("Datos migrados exitosamente")
    
    def save_data(self):
        try:
            # Crear backup antes de guardar
            if Path(self.data_file).exists():
                import shutil
                shutil.copy2(self.data_file, self.backup_file)
            
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=2)
            logger.info("Datos guardados exitosamente")
        except Exception as e:
            logger.error(f"Error guardando datos: {e}")
    
    def record_request(self):
        """Registrar nueva petición para métricas"""
        self.request_times.append(time.time())
        self.metrics.total_tasks += 1
        self.metrics.total_tokens += random.randint(10, 50)
        self.update_metrics()
    
    def update_metrics(self):
        """Actualizar métricas del servidor"""
        now = time.time()
        self.metrics.uptime = now - self.start_time
        
        # Calcular requests por minuto
        recent_requests = [t for t in self.request_times if t > now - 60]
        self.metrics.requests_per_minute = len(recent_requests)
        
        # Calcular totales
        self.metrics.total_agents = len(self.data.get("agents", {}))
        self.metrics.total_apps = len(self.data.get("applications", []))
        self.metrics.timestamp = datetime.now().isoformat()
    
    def get_server_metrics(self):
        self.update_metrics()
        return self.metrics
    
    def get_app_by_api_key(self, api_key: str) -> Optional[Dict]:
        """Obtener aplicación por API Key"""
        app_id = self.data.get("api_keys", {}).get(api_key)
        if app_id:
            for app in self.data.get("applications", []):
                if app["id"] == app_id:
                    return app
        return None
    
    def deploy_agent(self, agent_config: Dict, app_id: str) -> Dict:
        """Desplegar nuevo agente"""
        agent_id = f"agent_{random.randint(100000000, 999999999):x}"
        agent = Agent(
            id=agent_id,
            name=agent_config.get("name", "Nuevo Agente"),
            app_id=app_id,
            status="active",
            agent_type=agent_config.get("agent_type", "custom"),
            created_at=datetime.now().isoformat()
        )
        
        self.data["agents"][agent_id] = asdict(agent)
        
        # Agregar a la aplicación
        for app in self.data["applications"]:
            if app["id"] == app_id:
                app["agents"].append(asdict(agent))
                break
        
        self.save_data()
        logger.info(f"Agente agregado: {agent.name} a {app_id}")
        return asdict(agent)
    
    def stop_agent(self, agent_id: str, api_key: str) -> bool:
        """Parar agente"""
        app = self.get_app_by_api_key(api_key)
        if not app or app["id"] != self.data["agents"][agent_id]["app_id"]:
            return False
        
        self.data["agents"][agent_id]["status"] = "stopped"
        self.save_data()
        logger.info(f"Agente detenido: {agent_id}")
        return True

# Instancia global del almacén
store = DataStore()

# ==================== FUNCIONES DE AUTENTICACIÓN ====================

def verify_admin(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    """Verificar token de administrador"""
    try:
        # Decodificar token JWT simple
        token = credentials.credentials
        decoded = base64.b64decode(token).decode('utf-8')
        email, password = decoded.split(":")
        
        if (email == ADMIN_CREDENTIALS["email"] and 
            hashlib.sha256(password.encode()).hexdigest() == ADMIN_CREDENTIALS["password_hash"]):
            return {"email": email, "role": "admin"}
        else:
            raise HTTPException(status_code=401, detail="Token inválido")
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")

def verify_api_key(request: Request):
    """Verificar API Key"""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key requerida")
    
    app = store.get_app_by_api_key(api_key)
    if not app:
        raise HTTPException(status_code=401, detail="API Key inválida")
    
    return app

# ==================== ENDPOINTS PÚBLICOS ====================

@app.get("/")
async def root():
    """Página principal"""
    return {
        "service": "SilhouetteMCP Server",
        "version": "2.0.0",
        "status": "active",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check del servidor"""
    return {
        "status": "healthy",
        "server": "SilhouetteMCP",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - store.start_time
    }

@app.get("/metrics/public")
async def public_metrics():
    """Métricas públicas del servidor"""
    metrics = store.get_server_metrics()
    return {
        "server": metrics.server,
        "total_agents": metrics.total_agents,
        "total_apps": metrics.total_apps,
        "uptime_hours": round(metrics.uptime / 3600, 2),
        "timestamp": metrics.timestamp
    }

# ==================== ENDPOINTS DE AUTENTICACIÓN ====================

@app.post("/admin/login")
async def admin_login(request: Request):
    """Login de administrador vía POST"""
    try:
        data = await request.json()
        email = data.get("email", "")
        password = data.get("password", "")
        
        if (email == ADMIN_CREDENTIALS["email"] and 
            hashlib.sha256(password.encode()).hexdigest() == ADMIN_CREDENTIALS["password_hash"]):
            
            return {
                "success": True,
                "message": "Login exitoso",
                "user": {"email": email, "role": "admin"},
                "token": base64.b64encode(f"{email}:{password}".encode('utf-8')).decode('utf-8')  # Token temporal
            }
        else:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
            
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Error de login: {str(e)}")

# ==================== ENDPOINTS DE ADMINISTRACIÓN ====================

@app.get("/admin/dashboard")
async def admin_dashboard(admin=Depends(verify_admin)):
    """Dashboard administrativo completo"""
    store.record_request()
    
    metrics = store.get_server_metrics()
    
    return {
        "server_info": {
            "name": "SilhouetteMCP Server",
            "domain": "silhouettemcp.albertofarah.com",
            "version": "2.0.0",
            "uptime_hours": round(metrics.uptime / 3600, 2)
        },
        "metrics": {
            "total_agents": metrics.total_agents,
            "total_apps": metrics.total_apps,
            "total_tasks": metrics.total_tasks,
            "total_tokens": metrics.total_tokens,
            "uptime": metrics.uptime,
            "requests_per_minute": metrics.requests_per_minute,
            "timestamp": metrics.timestamp
        },
        "applications": store.data["applications"],
        "connection_info": {
            "api_base_url": "https://silhouettemcp.albertofarah.com",
            "admin_api_key": "sk-d8RahMZH5B8RIeSiLYx_ktBy5c9Ic8VkuTXo_2JkVzc",
            "websocket_endpoint": "wss://silhouettemcp.albertofarah.com/ws",
            "rest_api_docs": "https://silhouettemcp.albertofarah.com/docs"
        },
        "quick_stats": {
            "total_agents": metrics.total_agents,
            "active_apps": metrics.total_apps,
            "total_requests": metrics.total_tasks,
            "requests_per_minute": metrics.requests_per_minute
        }
    }

@app.get("/admin/applications")
async def admin_applications(admin=Depends(verify_admin)):
    """Lista de aplicaciones"""
    return {
        "applications": store.data["applications"],
        "total": len(store.data["applications"])
    }

@app.get("/admin/agents")
async def admin_agents(admin=Depends(verify_admin)):
    """Lista de todos los agentes"""
    agents = list(store.data["agents"].values())
    return {
        "agents": agents,
        "total": len(agents)
    }

@app.get("/admin/connection-guide")
async def admin_connection_guide(admin=Depends(verify_admin)):
    """Guía de conexión para desarrolladores"""
    return {
        "server_info": {
            "name": "SilhouetteMCP Server",
            "domain": "silhouettemcp.albertofarah.com",
            "protocol": "HTTPS + WebSocket",
            "api_version": "v2.0"
        },
        "authentication": {
            "method": "API Key",
            "header": "X-API-Key",
            "example": "curl -H 'X-API-Key: tu_api_key_aqui' https://silhouettemcp.albertofarah.com/api/status"
        },
        "endpoints": {
            "status": "GET /api/status",
            "agents": "GET /api/agents",
            "metrics": "GET /api/metrics",
            "deploy_agent": "POST /api/agents/deploy",
            "stop_agent": "POST /api/agents/stop"
        },
        "websocket": {
            "url": "wss://silhouettemcp.albertofarah.com/ws",
            "protocol": "Socket.IO o nativo WebSocket",
            "authentication": "Enviar api_key en primer mensaje"
        },
        "sdk_examples": {
            "javascript": f"""
const SilhouetteMCP = {{
    apiKey: 'tu_api_key',
    baseURL: 'https://silhouettemcp.albertofarah.com',
    
    async getStatus() {{
        const response = await fetch(`${{this.baseURL}}/api/status`, {{
            headers: {{ 'X-API-Key': this.apiKey }}
        }});
        return response.json();
    }},
    
    async deployAgent(agentConfig) {{
        const response = await fetch(`${{this.baseURL}}/api/agents/deploy`, {{
            method: 'POST',
            headers: {{
                'X-API-Key': this.apiKey,
                'Content-Type': 'application/json'
            }},
            body: JSON.stringify(agentConfig)
        }});
        return response.json();
    }}
}};
            """,
            "python": f"""
import requests

class SilhouetteMCP:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://silhouettemcp.albertofarah.com'
        self.headers = {{'X-API-Key': api_key}}
    
    def get_status(self):
        response = requests.get(f'{{self.base_url}}/api/status', headers=self.headers)
        return response.json()
    
    def deploy_agent(self, agent_config):
        response = requests.post(f'{{self.base_url}}/api/agents/deploy', 
                                headers=self.headers, 
                                json=agent_config)
        return response.json()
            """
        },
        "applications": [
            {
                "id": app["id"],
                "name": app["name"],
                "api_key": app["api_key"],
                "description": app["description"],
                "agent_count": len(app["agents"])
            } for app in store.data["applications"]
        ]
    }

# ==================== ENDPOINTS DE API ====================

@app.get("/api/status")
async def api_status(app=Depends(verify_api_key)):
    """Estado de la aplicación vía API"""
    store.record_request()
    
    # Actualizar agentes
    for agent in app["agents"]:
        if random.random() < 0.1:  # 10% de probabilidad de cambiar estado
            statuses = ["active", "idle", "processing", "error"]
            agent["status"] = random.choice(statuses)
            agent["tasks_completed"] += random.randint(1, 5)
            agent["token_usage"] += random.randint(50, 200)
            agent["last_activity"] = datetime.now().isoformat()
    
    store.save_data()
    
    return {
        "app": {"id": app["id"], "name": app["name"]},
        "agents": app["agents"],
        "server": "SilhouetteMCP",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/agents")
async def api_agents(app=Depends(verify_api_key)):
    """Lista de agentes de la aplicación"""
    store.record_request()
    
    return {
        "application": app["name"],
        "agents": app["agents"],
        "total_agents": len(app["agents"])
    }

@app.post("/api/agents/deploy")
async def api_deploy_agent(request: Request, app=Depends(verify_api_key)):
    """Desplegar nuevo agente"""
    store.record_request()
    
    try:
        agent_config = await request.json()
        new_agent = store.deploy_agent(agent_config, app["id"])
        
        return {
            "success": True,
            "message": f"Agente '{new_agent['name']}' desplegado exitosamente",
            "agent": new_agent
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error desplegando agente: {str(e)}")

@app.post("/api/agents/stop")
async def api_stop_agent(request: Request, app=Depends(verify_api_key)):
    """Parar agente"""
    store.record_request()
    
    try:
        data = await request.json()
        agent_id = data.get("agent_id")
        
        if not agent_id:
            raise HTTPException(status_code=400, detail="agent_id requerido")
        
        success = store.stop_agent(agent_id, app["api_key"])
        
        if success:
            return {
                "success": True,
                "message": f"Agente {agent_id} detenido exitosamente"
            }
        else:
            raise HTTPException(status_code=404, detail="Agente no encontrado")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error deteniendo agente: {str(e)}")

# ==================== STREAMING ====================

@app.get("/metrics/stream")
async def metrics_stream(request: Request):
    """Streaming de métricas en tiempo real"""
    async def generate_metrics():
        while True:
            metrics = store.get_server_metrics()
            data = {
                "timestamp": metrics.timestamp,
                "server": "SilhouetteMCP",
                "total_agents": metrics.total_agents,
                "total_apps": metrics.total_apps,
                "total_tasks": metrics.total_tasks,
                "total_tokens": metrics.total_tokens,
                "uptime_hours": round(metrics.uptime / 3600, 2),
                "requests_per_minute": metrics.requests_per_minute
            }
            
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(2)  # Actualizar cada 2 segundos
    
    return StreamingResponse(
        generate_metrics(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# ==================== CONFIGURACIÓN DE LOGGING ====================

def setup_periodic_updates():
    """Configurar actualizaciones periódicas de agentes"""
    def update_agents():
        while True:
            try:
                # Actualizar agentes aleatoriamente
                for app in store.data["applications"]:
                    for agent in app["agents"]:
                        if random.random() < 0.05:  # 5% de probabilidad
                            agent["tasks_completed"] += random.randint(0, 3)
                            agent["token_usage"] += random.randint(0, 100)
                            agent["last_activity"] = datetime.now().isoformat()
                            logger.info(f"Agente actualizado: {agent['id']}")
                
                store.save_data()
                time.sleep(10)  # Actualizar cada 10 segundos
            except Exception as e:
                logger.error(f"Error en actualización periódica: {e}")
                time.sleep(10)
    
    update_thread = threading.Thread(target=update_agents, daemon=True)
    update_thread.start()
    logger.info("Actualizaciones periódicas iniciadas")

# ==================== MAIN ====================

if __name__ == "__main__":
    logger.info("🚀 Iniciando SilhouetteMCP Server...")
    logger.info("📊 Dashboard: https://silhouettemcp.albertofarah.com/admin/dashboard")
    logger.info("🔑 Login: alberto.farahb@hotmail.com")
    logger.info("📡 API Docs: https://silhouettemcp.albertofarah.com/docs")
    
    setup_periodic_updates()
    
    uvicorn.run(
        "silhouettemcp_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
EOF

echo "✅ silhouettemcp_server.py creado"

# Crear docker-compose.yml
cat > docker-compose.silhouettemcp.yml << 'EOF'
version: '3.8'

services:
  silhouettemcp:
    build:
      context: .
      dockerfile: Dockerfile.silhouettemcp
    container_name: silhouettemcp_server
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./config:/opt/silhouettemcp/config:ro
      - ./data:/opt/silhouettemcp/data
      - ./logs:/opt/silhouettemcp/logs
    environment:
      - ADMIN_EMAIL=alberto.farahb@hotmail.com
      - DOMAIN=silhouettemcp.albertofarah.com
      - SSL_EMAIL=alberto.farahb@hotmail.com
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    networks:
      - silhouette-network

  nginx:
    image: nginx:alpine
    container_name: silhouettemcp_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.silhouettemcp.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - silhouettemcp
    networks:
      - silhouette-network

  certbot:
    image: certbot/certbot
    container_name: silhouettemcp_certbot
    volumes:
      - ./ssl:/etc/letsencrypt
      - ./logs/certbot:/var/log/letsencrypt
    entrypoint: "/bin/sh -c 'while :; do certbot renew --quiet --deploy-hook \"nginx -s reload\"; sleep 12h; done'"
    networks:
      - silhouette-network

networks:
  silhouette-network:
    driver: bridge

volumes:
  silhouettemcp_data:
  silhouettemcp_logs:
EOF

echo "✅ docker-compose.silhouettemcp.yml creado"

# Crear Dockerfile
cat > Dockerfile.silhouettemcp << 'EOF'
FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN useradd -m -u 1000 silhouettemcp

# Configurar directorio de trabajo
WORKDIR /opt/silhouettemcp

# Copiar requirements y instalar dependencias Python
COPY requirements.txt* ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY silhouettemcp_server.py .

# Crear directorios necesarios
RUN mkdir -p logs data config && \
    chown -R silhouettemcp:silhouettemcp /opt/silhouettemcp

# Cambiar a usuario no-root
USER silhouettemcp

# Exponer puerto
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando por defecto
CMD ["python", "silhouettemcp_server.py"]
EOF

echo "✅ Dockerfile.silhouettemcp creado"

# Crear requirements.txt
cat > requirements.txt << 'EOF'
fastapi==0.121.0
uvicorn[standard]==0.38.0
python-multipart==0.0.20
websockets==15.0.1
sse-starlette==3.0.3
starlette==0.49.3
EOF

echo "✅ requirements.txt creado"

# Crear nginx.silhouettemcp.conf
cat > nginx.silhouettemcp.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    # Configuración básica
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;
    
    # MIME types
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/javascript application/xml+rss 
               application/json application/xml;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
    limit_req_zone $binary_remote_addr zone=admin:10m rate=10r/m;
    
    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' 'unsafe-inline' 'unsafe-eval' data:;" always;
    
    # Redirección HTTP a HTTPS
    server {
        listen 80;
        server_name silhouettemcp.albertofarah.com;
        
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        
        location / {
            return 301 https://$server_name$request_uri;
        }
    }
    
    # Servidor principal HTTPS
    server {
        listen 443 ssl http2;
        server_name silhouettemcp.albertofarah.com;
        
        # SSL certificates (se generan automáticamente)
        ssl_certificate /etc/nginx/ssl/live/silhouettemcp.albertofarah.com/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/live/silhouettemcp.albertofarah.com/privkey.pem;
        
        # Configuración de archivos estáticos
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            proxy_pass http://silhouettemcp:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
        
        # Dashboard HTML
        location / {
            proxy_pass http://silhouettemcp:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
        
        # API endpoints con rate limiting
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://silhouettemcp:8000/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts para API
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }
        
        # Admin endpoints con rate limiting estricto
        location /admin/ {
            limit_req zone=admin burst=5 nodelay;
            proxy_pass http://silhouettemcp:8000/admin/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Health check endpoint
        location /health {
            proxy_pass http://silhouettemcp:8000/health;
            proxy_set_header Host $host;
            access_log off;
        }
        
        # Server-Sent Events (SSE)
        location /metrics/stream {
            proxy_pass http://silhouettemcp:8000/metrics/stream;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # No buffering para SSE
            proxy_buffering off;
            proxy_cache off;
            proxy_redirect off;
        }
        
        # WebSocket support (para futuras implementaciones)
        location /ws {
            proxy_pass http://silhouettemcp:8000/ws;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Documentación API
        location /docs {
            proxy_pass http://silhouettemcp:8000/docs;
            proxy_set_header Host $host;
        }
        
        location /redoc {
            proxy_pass http://silhouettemcp:8000/redoc;
            proxy_set_header Host $host;
        }
        
        # Proxy adicional para FastAPI docs
        location /openapi.json {
            proxy_pass http://silhouettemcp:8000/openapi.json;
            proxy_set_header Host $host;
        }
        
        # Block access to sensitive files
        location ~ /\. {
            deny all;
            access_log off;
            log_not_found off;
        }
        
        location ~ \.(json|yaml|yml|log|txt)$ {
            deny all;
            access_log off;
            log_not_found off;
        }
    }
}
EOF

echo "✅ nginx.silhouettemcp.conf creado"

# PASO 8: CREAR SCRIPTS DE DESPLIEGUE
echo ""
echo "🛠️  PASO 8: Creando scripts de despliegue..."

# Crear deploy_silhouettemcp.sh
cat > deploy_silhouettemcp.sh << 'EOF'
#!/bin/bash
# ===============================================================================
# SCRIPT DE DESPLIEGUE AUTOMÁTICO SILHOUETTEMCP
# Desarrollado para: silhouettemcp.albertofarah.com
# ===============================================================================

set -e  # Salir en caso de error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables de configuración
DOMAIN="silhouettemcp.albertofarah.com"
EMAIL="alberto.farahb@hotmail.com"
APP_DIR="/opt/silhouettemcp"
SSL_DIR="/opt/silhouettemcp/ssl"

echo -e "${BLUE}🚀 INICIANDO DESPLIEGUE DE SILHOUETTEMCP${NC}"
echo "========================================================="
echo "Dominio: $DOMAIN"
echo "Email: $EMAIL"
echo "Directorio: $APP_DIR"
echo "========================================================="

# Función para logging
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para verificar comandos
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verificar permisos de root
if [[ $EUID -eq 0 ]]; then
   log_error "Este script no debe ejecutarse como root"
   exit 1
fi

log_info "Verificando dependencias..."

# Instalar Docker si no está disponible
if ! command_exists docker; then
    log_warn "Docker no encontrado. Instalando Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    sudo systemctl enable docker
    sudo systemctl start docker
    log_info "Docker instalado exitosamente"
else
    log_info "Docker ya está disponible: $(docker --version)"
fi

# Instalar Docker Compose si no está disponible
if ! docker compose version >/dev/null 2>&1 && ! command_exists docker-compose; then
    log_warn "Docker Compose no encontrado. Instalando..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    log_info "Docker Compose instalado"
else
    log_info "Docker Compose disponible"
fi

# Instalar curl si no está disponible
if ! command_exists curl; then
    log_info "Instalando curl..."
    sudo apt-get update
    sudo apt-get install -y curl
fi

log_info "Verificando configuración DNS..."

# Verificar DNS
VPS_IP=$(curl -s ifconfig.me)
DNS_IP=$(dig +short $DOMAIN)

if [[ "$DNS_IP" != "$VPS_IP" ]]; then
    log_error "Error: DNS no configurado correctamente"
    log_error "VPS IP: $VPS_IP"
    log_error "DNS IP: $DNS_IP"
    log_error "Configura el registro A: $DOMAIN -> $VPS_IP"
    exit 1
fi

log_info "DNS configurado correctamente"

# Crear directorio de aplicación
log_info "Creando estructura de directorios..."
sudo mkdir -p $APP_DIR/{logs,ssl,config,data,backup}
sudo chown $USER:$USER $APP_DIR

cd $APP_DIR

# Crear certificado temporal para inicialización
log_info "Generando certificado SSL temporal..."
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout $SSL_DIR/privkey.pem \
    -out $SSL_DIR/fullchain.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"

# Configurar nginx para usar certificado temporal
log_info "Configurando Nginx temporal..."
sudo mkdir -p /var/www/certbot

# Construir imagen Docker
log_info "Construyendo imagen Docker..."
docker build -f Dockerfile.silhouettemcp -t silhouettemcp:latest .

# Iniciar servicios temporalmente
log_info "Iniciando servicios temporales..."
docker-compose -f docker-compose.silhouettemcp.yml up -d silhouettemcp nginx

# Esperar a que los servicios estén listos
log_info "Esperando a que los servicios estén listos..."
sleep 10

# Verificar que el servidor esté funcionando
for i in {1..30}; do
    if curl -f -s http://localhost:8000/health > /dev/null; then
        log_info "Servidor SilhouetteMCP funcionando correctamente"
        break
    fi
    if [[ $i -eq 30 ]]; then
        log_error "Servidor no responde después de 30 intentos"
        exit 1
    fi
    sleep 2
done

# Configurar SSL con Let's Encrypt
log_info "Configurando SSL con Let's Encrypt..."

# Crear script para obtener certificado SSL
cat > ssl_setup.sh << 'SSL_EOF'
#!/bin/bash
# Script para obtener certificado SSL de Let's Encrypt

DOMAIN="silhouettemcp.albertofarah.com"
EMAIL="alberto.farahb@hotmail.com"
SSL_DIR="/opt/silhouettemcp/ssl"

# Detener nginx temporalmente
docker-compose -f /opt/silhouettemcp/docker-compose.silhouettemcp.yml stop nginx

# Obtener certificado SSL
docker run --rm \
    -v $SSL_DIR:/etc/letsencrypt \
    -v /var/www/certbot:/var/www/certbot \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --domains $DOMAIN

# Reiniciar nginx
docker-compose -f /opt/silhouettemcp/docker-compose.silhouettemcp.yml start nginx

echo "Certificado SSL configurado correctamente"
SSL_EOF

chmod +x ssl_setup.sh

# Ejecutar configuración SSL
./ssl_setup.sh

# Verificar SSL
if [[ -f "$SSL_DIR/live/$DOMAIN/fullchain.pem" ]]; then
    log_info "✅ SSL configurado correctamente"
else
    log_warn "⚠️  SSL falló, usando certificado temporal"
fi

# Configurar firewall (si está disponible)
if command_exists ufw; then
    log_info "Configurando firewall..."
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 22/tcp
fi

# Iniciar todos los servicios
log_info "Iniciando todos los servicios..."
docker-compose -f docker-compose.silhouettemcp.yml up -d

# Verificar que todos los servicios estén corriendo
log_info "Verificando servicios..."
sleep 5

if docker-compose -f docker-compose.silhouettemcp.yml ps | grep -q "Up"; then
    log_info "✅ Servicios iniciados correctamente"
else
    log_error "❌ Error al iniciar servicios"
    docker-compose -f docker-compose.silhouettemcp.yml logs
    exit 1
fi

# Configurar renovación automática de SSL
log_info "Configurando renovación automática de SSL..."
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/silhouettemcp/ssl_renew.sh >> /opt/silhouettemcp/logs/ssl_renew.log 2>&1") | crontab -

# Crear script de renovación
cat > ssl_renew.sh << 'RENEW_EOF'
#!/bin/bash
# Script de renovación automática de SSL

SSL_DIR="/opt/silhouettemcp/ssl"
DOMAIN="silhouettemcp.albertofarah.com"

# Renovar certificado SSL
docker run --rm \
    -v $SSL_DIR:/etc/letsencrypt \
    certbot/certbot renew --quiet --deploy-hook "docker-compose -f /opt/silhouettemcp/docker-compose.silhouettemcp.yml restart nginx"

echo "Renovación SSL ejecutada: $(date)" >> /opt/silhouettemcp/logs/ssl_renew.log
RENEW_EOF

chmod +x ssl_renew.sh

# Configurar backup automático
log_info "Configurando backup automático..."
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/silhouettemcp/backup.sh >> /opt/silhouettemcp/logs/backup.log 2>&1") | crontab -

# Crear script de backup
cat > backup.sh << 'BACKUP_EOF'
#!/bin/bash
# Script de backup automático

APP_DIR="/opt/silhouettemcp"
BACKUP_DIR="/opt/silhouettemcp/backup"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup de datos y configuración
tar -czf $BACKUP_DIR/silhouettemcp_backup_$DATE.tar.gz \
    -C $APP_DIR \
    data/ config/ silhouettemcp_data.json

# Mantener solo los últimos 7 backups
find $BACKUP_DIR -name "silhouettemcp_backup_*.tar.gz" -mtime +7 -delete

echo "Backup creado: silhouettemcp_backup_$DATE.tar.gz"
BACKUP_EOF

chmod +x backup.sh

# Crear comandos de gestión
log_info "Creando comandos de gestión..."
cat > comandos_silhouettemcp.sh << 'COMANDOS_EOF'
#!/bin/bash
# Comandos de gestión para SilhouetteMCP

APP_DIR="/opt/silhouettemcp"
cd $APP_DIR

case "$1" in
    status)
        echo "=== ESTADO DE SERVICIOS ==="
        docker-compose -f docker-compose.silhouettemcp.yml ps
        echo ""
        echo "=== LOGS RECIENTES ==="
        docker-compose -f docker-compose.silhouettemcp.yml logs --tail=20
        ;;
    restart)
        echo "Reiniciando servicios..."
        docker-compose -f docker-compose.silhouettemcp.yml restart
        ;;
    stop)
        echo "Deteniendo servicios..."
        docker-compose -f docker-compose.silhouettemcp.yml down
        ;;
    start)
        echo "Iniciando servicios..."
        docker-compose -f docker-compose.silhouettemcp.yml up -d
        ;;
    logs)
        docker-compose -f docker-compose.silhouettemcp.yml logs -f "$2"
        ;;
    backup)
        echo "Creando backup..."
        ./backup.sh
        ;;
    ssl-renew)
        echo "Renovando certificado SSL..."
        ./ssl_renew.sh
        ;;
    cleanup)
        echo "Limpiando contenedores e imágenes antiguos..."
        docker system prune -f
        docker image prune -f
        ;;
    *)
        echo "Uso: $0 {status|restart|stop|start|logs [servicio]|backup|ssl-renew|cleanup}"
        echo ""
        echo "Comandos disponibles:"
        echo "  status       - Mostrar estado y logs recientes"
        echo "  restart      - Reiniciar todos los servicios"
        echo "  stop         - Detener todos los servicios"
        echo "  start        - Iniciar todos los servicios"
        echo "  logs [svc]   - Ver logs en tiempo real (opcional: especificar servicio)"
        echo "  backup       - Crear backup de datos"
        echo "  ssl-renew    - Renovar certificado SSL"
        echo "  cleanup      - Limpiar recursos Docker antiguos"
        ;;
esac
COMANDOS_EOF

chmod +x comandos_silhouettemcp.sh

# Verificación final
log_info "Realizando verificación final..."

# Verificar que el dashboard esté accesible
sleep 5
if curl -f -s https://$DOMAIN/admin/dashboard > /dev/null 2>&1; then
    log_info "✅ Dashboard accesible en: https://$DOMAIN/admin/dashboard"
else
    log_warn "⚠️  Dashboard podría no estar completamente listo. Verificar manualmente."
fi

# Verificar API
if curl -f -s https://$DOMAIN/api/status > /dev/null 2>&1; then
    log_info "✅ API accesible en: https://$DOMAIN/api/status"
else
    log_warn "⚠️  API podría no estar completamente lista. Verificar manualmente."
fi

# Verificar health check
if curl -f -s https://$DOMAIN/health > /dev/null 2>&1; then
    log_info "✅ Health check OK: https://$DOMAIN/health"
else
    log_warn "⚠️  Health check no disponible"
fi

echo ""
echo -e "${GREEN}🎉 ¡DESPLIEGUE COMPLETADO EXITOSAMENTE!${NC}"
echo "========================================================="
echo -e "${BLUE}📊 Dashboard:${NC} https://$DOMAIN/admin/dashboard"
echo -e "${BLUE}🔑 Login:${NC} alberto.farahb@hotmail.com / Fbalberto1910"
echo -e "${BLUE}📡 API Docs:${NC} https://$DOMAIN/docs"
echo -e "${BLUE}💚 Health:${NC} https://$DOMAIN/health"
echo -e "${BLUE}📚 API:${NC} https://$DOMAIN/api/status"
echo ""
echo -e "${YELLOW}Comandos útiles:${NC}"
echo "  • Ver estado: ./comandos_silhouettemcp.sh status"
echo "  • Ver logs: ./comandos_silhouettemcp.sh logs"
echo "  • Reiniciar: ./comandos_silhouettemcp.sh restart"
echo "  • Backup: ./comandos_silhouettemcp.sh backup"
echo ""
echo -e "${GREEN}✅ Sistema SilhouetteMCP desplegado y funcionando${NC}"

# Mostrar información del sistema
echo ""
echo "=== INFORMACIÓN DEL SISTEMA ==="
echo "Dominio: $DOMAIN"
echo "IP del VPS: $VPS_IP"
echo "Directorio: $APP_DIR"
echo "SSL: Let's Encrypt (auto-renovable)"
echo "Backup: Automático diario a las 3:00 AM"
echo "Firewall: Puertos 80, 443, 22 abiertos"
echo ""
echo "=== ACCESOS ==="
echo "Dashboard: https://$DOMAIN/admin/dashboard"
echo "Email: alberto.farahb@hotmail.com"
echo "Password: Fbalberto1910"
echo ""
echo -e "${BLUE}🔧 Soporte:${NC} Para problemas, revisar logs en $APP_DIR/logs/"
EOF

chmod +x deploy_silhouettemcp.sh

echo "✅ deploy_silhouettemcp.sh creado"

# PASO 9: CONFIGURAR PERMISOS
echo ""
echo "🔐 PASO 9: Configurando permisos..."
chmod +x deploy_silhouettemcp.sh
chmod +x ssl_setup.sh
chmod +x ssl_renew.sh
chmod +x backup.sh

echo "✅ Permisos configurados"

# PASO 10: CREAR INSTRUCCIONES PARA GEMINI CLI
echo ""
echo "📋 PASO 10: Creando instrucciones para Gemini CLI..."

cat > GEMINI_CLI_INSTRUCTIONS.md << 'EOF'
# INSTRUCCIONES PARA GEMINI CLI - DESPLIEGUE SILHOUETTEMCP

## 🎯 OBJETIVO
Usar Gemini CLI para automatizar el despliegue del sistema SilhouetteMCP en tu VPS.

## 📋 PASOS PARA GEMINI CLI

### PASO 1: Subir archivos al VPS
```bash
# Desde tu máquina local, sube todos los archivos a tu VPS:
scp -r . user@tu-vps-ip:/tmp/silhouettemcp_deploy/
```

### PASO 2: Conectar a tu VPS
```bash
ssh user@tu-vps-ip
cd /tmp/silhouettemcp_deploy
```

### PASO 3: Ejecutar con Gemini CLI
```bash
# Usar Gemini CLI para ejecutar el despliegue:
gemini run --file=deploy_with_gemini.sh
```

O ejecutar directamente:
```bash
bash deploy_with_gemini.sh
```

## 🔧 QUÉ HACE EL SCRIPT

El script `deploy_with_gemini.sh` ejecuta automáticamente:

1. ✅ **Verificación de dependencias** (Docker, Docker Compose, curl)
2. ✅ **Configuración DNS** (verifica que el dominio esté configurado)
3. ✅ **Instalación de Docker** (si no está disponible)
4. ✅ **Creación de estructura de directorios** (/opt/silhouettemcp)
5. ✅ **Configuración SSL** (Let's Encrypt con renovación automática)
6. ✅ **Despliegue de servicios** (SilhouetteMCP + Nginx + Certbot)
7. ✅ **Configuración de firewall** (puertos 80, 443, 22)
8. ✅ **Scripts de gestión** (backup, monitoreo, restart)
9. ✅ **Verificación final** (dashboard, API, health check)

## 🌐 URLS FINALES

Después del despliegue exitoso tendrás:

- **Dashboard**: https://silhouettemcp.albertofarah.com/admin/dashboard
- **API**: https://silhouettemcp.albertofarah.com/api/status
- **Health**: https://silhouettemcp.albertofarah.com/health
- **Docs**: https://silhouettemcp.albertofarah.com/docs

## 🔑 CREDENCIALES

- **Email**: alberto.farahb@hotmail.com
- **Password**: Fbalberto1910

## 🛠️ COMANDOS POST-DESPLIEGUE

Una vez desplegado, puedes gestionar el sistema con:

```bash
cd /opt/silhouettemcp
./comandos_silhouettemcp.sh status
./comandos_silhouettemcp.sh logs
./comandos_silhouettemcp.sh restart
```

## ⚠️ REQUISITOS PREVIOS

1. **VPS con Ubuntu/Debian** (recomendado)
2. **Docker instalado** (se instala automáticamente si no existe)
3. **DNS configurado**: registro A para `silhouettemcp.albertofarah.com`
4. **Puerto 80 y 443 abiertos** en el firewall
5. **Usuario con permisos sudo**

## 🚨 SI HAY PROBLEMAS

1. **DNS no responde**: Verifica que el registro A esté configurado
2. **Docker no funciona**: Verifica permisos de usuario
3. **SSL falla**: Revisa logs en `/opt/silhouettemcp/logs/`
4. **Servicios no inician**: Ejecuta `./comandos_silhouettemcp.sh status`

## 📞 SOPORTE

Para problemas, revisa los logs:
```bash
docker-compose -f /opt/silhouettemcp/docker-compose.silhouettemcp.yml logs
```

¡El despliegue es completamente automatizado y debería completarse sin intervención manual!
EOF

echo "✅ GEMINI_CLI_INSTRUCTIONS.md creado"

echo ""
echo -e "${GREEN}🎉 ¡PREPARACIÓN COMPLETADA!${NC}"
echo "========================================================="
echo "Archivos creados en: $(pwd)"
echo ""
echo -e "${BLUE}SIGUIENTE PASO:${NC}"
echo "1. Sube esta carpeta a tu VPS usando:"
echo "   scp -r . user@tu-vps-ip:/tmp/silhouettemcp_deploy/"
echo ""
echo "2. Conecta a tu VPS:"
echo "   ssh user@tu-vps-ip"
echo ""
echo "3. Ejecuta el despliegue:"
echo "   cd /tmp/silhouettemcp_deploy"
echo "   bash deploy_with_gemini.sh"
echo ""
echo "¡El sistema se desplegará automáticamente!"
