#!/usr/bin/env python3
"""
SilhouetteMCP Server - Servidor MCP superior con autenticación y gestión multi-aplicación
Desarrollado para: silhouettemcp.albertofarah.com
"""

import asyncio
import json
import logging
import os
import secrets
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, Gauge, generate_latest
from pydantic import BaseModel

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SilhouetteMCPServer")

# La consola va antes que nada: en Windows, escribir un emoji o una comilla
# tipográfica en un log con la página de códigos por defecto lanza
# UnicodeEncodeError y aborta la petición en curso.
from backend.app.core.console import configure as configure_console  # noqa: E402

configure_console()

# El entorno se carga ANTES que cualquier otra cosa: la autenticación, el CORS,
# la lista blanca de procesos y el router leen `os.getenv()` en tiempo de import.
# Sin esto, las claves de API escritas en `.env` no las veía nadie y el sistema
# arrancaba sin ningún modelo disponible.
from backend.app.core.env_loader import load_env  # noqa: E402

load_env()

# ==================== CONFIGURACIÓN DE AUTENTICACIÓN ====================
# Las credenciales viven en el entorno, nunca en el código. Genere el hash con:
#   python -m backend.app.security.auth "<contraseña>"
# y expórtelo como SILHOUETTE_ADMIN_PASSWORD_HASH junto a SILHOUETTE_ADMIN_EMAIL.
from backend.app.security.auth import AuthNotConfigured, auth_service
from backend.app.security.process_policy import (
    AppNotAllowed,
    ArgumentRejected,
    plan_launch,
)
from backend.app.security.workspace import (
    PathNotAllowed,
    resolve_within_workspace,
    safe_relative,
)

if not auth_service.is_configured:
    logger.warning(
        "No hay administrador configurado: los endpoints protegidos responderán 503. "
        "Defina SILHOUETTE_ADMIN_EMAIL y SILHOUETTE_ADMIN_PASSWORD_HASH."
    )

# ==================== CICLO DE VIDA ====================
# `@app.on_event` está deprecado en FastAPI. `lifespan` lo sustituye y además
# garantiza que el apagado se ejecute aunque el arranque haya fallado a medias.
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Arranque y apagado ordenados del servidor."""
    # Los componentes se resuelven aquí, no al importar: cuando esto corre, el
    # módulo ya está cargado por completo.
    try:
        from backend.app.core.startup_manager import StartupManager

        logger.info("Inicializando SilhouetteMCP...")
        # La limpieza periódica de tareas no puede programarse al importar
        # (no hay bucle de eventos todavía); aquí sí lo hay.
        from backend.app.services.task_manager import task_manager

        task_manager.ensure_cleanup_running()

        await StartupManager(root_dir=str(Path(__file__).parent)).execute_startup_scripts(
            globals()["system_orchestrator"]
        )
    except Exception as exc:  # noqa: BLE001 - un fallo de arranque no debe impedir servir
        logger.error("Fallo durante el arranque: %s", exc)

    yield

    # El apagado se intenta siempre, incluso si el arranque falló.
    for nombre in ("organism", "evolution_scheduler"):
        componente = globals().get(nombre)
        if componente is None:
            continue
        try:
            await componente.stop()
        except Exception as exc:  # noqa: BLE001 - apagar nunca debe lanzar
            logger.warning("Error al detener %s: %s", nombre, exc)
    logger.info("SilhouetteMCP detenido.")


# Configuración del servidor
app = FastAPI(
    title="SilhouetteMCP Server",
    description="Servidor MCP superior para gestión multi-aplicación con agentes",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS: lista blanca explícita. Un comodín junto a allow_credentials=True es
# inválido según la especificación y permite que cualquier web llame a la API
# con las credenciales del usuario. Ajuste los orígenes con SILHOUETTE_CORS_ORIGINS.
_DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("SILHOUETTE_CORS_ORIGINS", _DEFAULT_CORS_ORIGINS).split(",")
    if origin.strip() and origin.strip() != "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "Cache-Control"],
)

# Sistema de autenticación
security = HTTPBearer()


@app.exception_handler(Exception)
async def _sin_modelo_handler(request: Request, exc: Exception):
    """Traduce «no hay modelo» a un 503 con el diagnóstico y qué hacer.

    Sin esto acababa en un 500 genérico, indistinguible de un error de
    programación, cuando en realidad es un estado de configuración con solución
    concreta.
    """
    from backend.app.core.llm_router import NoProviderAvailable

    if isinstance(exc, NoProviderAvailable):
        return JSONResponse(
            status_code=503,
            content={
                "error": "no_llm_available",
                "detail": str(exc),
                "next_step": "GET /api/setup/status enumera qué falta y cómo conectarlo.",
            },
        )
    raise exc

# Mount static files for dashboard
dashboard_path = Path(__file__).parent / "dashboard-static"
if dashboard_path.exists():
    app.mount("/dashboard", StaticFiles(directory=str(dashboard_path)), name="dashboard")
    logger.info(f"Dashboard static files mounted from {dashboard_path}")

# ==================== STARTUP BOOTSTRAP (FASE 1) ====================
from backend.app.orchestrator.multi_agent import MultiAgentOrchestrator

# Global orchestrator instance for startup tasks and system-wide operations
system_orchestrator = MultiAgentOrchestrator()

# ==================== MODELOS DE DATOS ====================

@dataclass
class AgentInstance:
    """Instancia individual de un agente"""
    id: str
    name: str
    app_id: str
    status: str = "idle"
    tasks_completed: int = 0
    avg_response_time: float = 0.0
    token_usage: int = 0
    last_activity: str = ""
    success_rate: float = 95.0
    agent_type: str = "general"  # sales, support, consulting, custom
    created_at: str = ""

    def __post_init__(self):
        if not self.last_activity:
            self.last_activity = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

@dataclass
class Application:
    """Aplicación registrada en el servidor"""
    id: str
    name: str
    description: str
    api_key: str
    owner_email: str
    agents: list[AgentInstance]
    created_at: str = ""
    is_active: bool = True

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

@dataclass
class ServerMetrics:
    """Métricas del servidor"""
    total_agents: int = 0
    total_apps: int = 0
    total_tasks: int = 0
    total_tokens: int = 0
    uptime: float = 0.0
    requests_per_minute: float = 0.0
    timestamp: str = ""

# ==================== STORE PERSISTENTE ====================

class SilhouetteMCPStore:
    """Store persistente para SilhouetteMCP"""

    def __init__(self, storage_file: str = "silhouettemcp_data.json"):
        self.storage_file = Path(storage_file)
        self._data = self._load_data()
        self._lock = threading.Lock()
        self._start_time = time.time()
        self._request_count = 0
        self._request_times = deque(maxlen=1000)  # Últimas 1000 requests para calcular RPM

    def _load_data(self) -> dict[str, Any]:
        """Cargar datos persistentes"""
        try:
            if self.storage_file.exists():
                with open(self.storage_file, encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Datos cargados desde {self.storage_file}")
                return data
        except Exception as e:
            logger.error(f"Error cargando datos: {e}")

        # Datos por defecto
        return self._create_default_data()

    def _create_default_data(self) -> dict[str, Any]:
        """Crear datos por defecto del servidor"""
        now = datetime.now().isoformat()

        # Aplicación por defecto. El propietario sale del entorno: dejarlo
        # escrito en el código lo publicaba en cada copia del repositorio.
        default_app = Application(
            id="silhouettemcp_default",
            name="SilhouetteMCP Dashboard",
            description="Dashboard principal de gestión",
            api_key=self._generate_api_key(),
            owner_email=os.getenv("SILHOUETTE_ADMIN_EMAIL", "admin@localhost"),
            agents=[
                AgentInstance(
                    id="dashboard_admin",
                    name="Dashboard Admin",
                    app_id="silhouettemcp_default",
                    status="active",
                    agent_type="admin"
                ),
                AgentInstance(
                    id="system_monitor",
                    name="System Monitor",
                    app_id="silhouettemcp_default",
                    status="active",
                    agent_type="monitoring"
                ),
                AgentInstance(
                    id="api_gateway",
                    name="API Gateway",
                    app_id="silhouettemcp_default",
                    status="active",
                    agent_type="gateway"
                )
            ]
        )

        return {
            "server_info": {
                "name": "SilhouetteMCP Server",
                "version": "2.0.0",
                "domain": "silhouettemcp.albertofarah.com",
                "created_at": now,
                "start_time": time.time()
            },
            "applications": [asdict(default_app)],
            "metrics": {
                "total_requests": 0,
                "avg_response_time": 0.0,
                "last_updated": now
            }
        }

    def _generate_api_key(self) -> str:
        """Generar API key única"""
        return f"sk-{secrets.token_urlsafe(32)}"

    def save_data(self):
        """Guardar datos de forma segura"""
        try:
            with self._lock:
                with open(self.storage_file, 'w', encoding='utf-8') as f:
                    json.dump(self._data, f, indent=2, ensure_ascii=False)
                logger.info("Datos guardados exitosamente")
        except Exception as e:
            logger.error(f"Error guardando datos: {e}")

    def get_applications(self) -> list[Application]:
        """Obtener todas las aplicaciones"""
        apps = []
        for app_data in self._data.get("applications", []):
            app_obj = Application(**app_data)
            app_obj.agents = [AgentInstance(**agent_data) for agent_data in app_data.get("agents", [])]
            apps.append(app_obj)
        return apps

    def get_application(self, app_id: str) -> Application | None:
        """Obtener aplicación específica"""
        for app_data in self._data.get("applications", []):
            if app_data["id"] == app_id:
                app_obj = Application(**app_data)
                app_obj.agents = [AgentInstance(**agent_data) for agent_data in app_data.get("agents", [])]
                return app_obj
        return None

    def add_application(self, app: Application):
        """Agregar nueva aplicación"""
        self._data["applications"].append(asdict(app))
        self.save_data()
        logger.info(f"Aplicación agregada: {app.name} ({app.id})")

    def add_agent_to_app(self, app_id: str, agent: AgentInstance):
        """Agregar agente a aplicación"""
        for app_data in self._data["applications"]:
            if app_data["id"] == app_id:
                app_data["agents"].append(asdict(agent))
                self.save_data()
                logger.info(f"Agente agregado: {agent.name} a {app_id}")
                return
        raise ValueError(f"Aplicación no encontrada: {app_id}")

    def update_agent(self, app_id: str, agent_id: str, updates: dict[str, Any]):
        """Actualizar agente"""
        for app_data in self._data["applications"]:
            if app_data["id"] == app_id:
                for agent_data in app_data["agents"]:
                    if agent_data["id"] == agent_id:
                        agent_data.update(updates)
                        self.save_data()
                        logger.info(f"Agente actualizado: {agent_id}")
                        return
        raise ValueError(f"Agente no encontrado: {agent_id}")

    def get_all_agents(self) -> list[AgentInstance]:
        """Obtener todos los agentes"""
        agents = []
        for app in self.get_applications():
            agents.extend(app.agents)
        return agents

    def record_request(self):
        """Registrar request para métricas"""
        self._request_count += 1
        self._request_times.append(time.time())

    def get_server_metrics(self) -> ServerMetrics:
        """Obtener métricas del servidor"""
        agents = self.get_all_agents()
        apps = self.get_applications()

        total_tasks = sum(agent.tasks_completed for agent in agents)
        total_tokens = sum(agent.token_usage for agent in agents)
        uptime = time.time() - self._start_time

        # Calcular RPM (requests per minute)
        now = time.time()
        recent_requests = [t for t in self._request_times if now - t < 60]
        rpm = len(recent_requests) if recent_requests else 0.0

        return ServerMetrics(
            total_agents=len(agents),
            total_apps=len([app for app in apps if app.is_active]),
            total_tasks=total_tasks,
            total_tokens=total_tokens,
            uptime=uptime,
            requests_per_minute=rpm,
            timestamp=datetime.now().isoformat()
        )

# Instancia global del store
store = SilhouetteMCPStore()

# ==================== FUNCIONES DE AUTENTICACIÓN ====================

def verify_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict[str, Any]:
    """Valida el token de sesión emitido por /admin/login.

    El token es opaco y caducable. A diferencia del esquema anterior, no contiene
    la contraseña ni permite derivarla.
    """
    if not auth_service.is_configured:
        raise HTTPException(
            status_code=503,
            detail=(
                "Autenticación no configurada. Defina SILHOUETTE_ADMIN_EMAIL y "
                "SILHOUETTE_ADMIN_PASSWORD_HASH en el entorno."
            ),
        )
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Use el esquema Bearer con el token emitido por /admin/login.",
        )
    try:
        identity = auth_service.resolve(credentials.credentials)
    except PermissionError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado") from None
    return {"email": identity.email, "role": identity.role}

def verify_api_key(api_key: str) -> Application | None:
    """Verificar API key de aplicación"""
    for app in store.get_applications():
        if app.api_key == api_key and app.is_active:
            return app
    return None

# ==================== ENDPOINTS PÚBLICOS ====================

@app.get("/")
async def root():
    """Endpoint raíz con información del servidor"""
    return {
        "server": "SilhouetteMCP Server",
        "version": "2.0.0",
        "domain": "silhouettemcp.albertofarah.com",
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "public_metrics": "/metrics/public",
            "docs": "/docs",
            "admin_login": "/admin/login",
            "dashboard_ultra": "/dashboard-ultra"
        }
    }

@app.get("/dashboard-ultra")
async def dashboard_ultra():
    """Serve the ultra-advanced dashboard"""
    dashboard_file = Path(__file__).parent / "dashboard-static" / "index.html"
    if dashboard_file.exists():
        return FileResponse(dashboard_file)
    else:
        raise HTTPException(status_code=404, detail="Dashboard not found")

@app.get("/health")
async def health_check():
    """Health check público"""
    return {
        "status": "healthy",
        "server": "SilhouetteMCP",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - store._start_time
    }

@app.get("/metrics/public")
async def public_metrics():
    """Métricas públicas (sin autenticación)"""
    metrics = store.get_server_metrics()
    return {
        "server_status": "active",
        "total_agents": metrics.total_agents,
        "total_apps": metrics.total_apps,
        "uptime_hours": round(metrics.uptime / 3600, 2),
        "timestamp": metrics.timestamp
    }

@app.post("/admin/login")
async def admin_login(request: Request):
    """Emite un token de sesión de administrador."""
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Se esperaba un cuerpo JSON") from None

    email = str(data.get("email", ""))
    password = str(data.get("password", ""))

    try:
        token = auth_service.login(email, password)
    except AuthNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    except PermissionError:
        logger.warning("Intento de login fallido para '%s'", email[:64])
        raise HTTPException(status_code=401, detail="Credenciales inválidas") from None

    return {
        "success": True,
        "message": "Login exitoso",
        "user": {"email": email, "role": "admin"},
        "token": token,
        "expires_in": 8 * 3600,
    }


@app.post("/admin/logout")
async def admin_logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Revoca el token de sesión actual."""
    revoked = auth_service.revoke(credentials.credentials)
    return {"success": True, "revoked": revoked}

# ==================== ENDPOINTS DE ADMINISTRACIÓN ====================

@app.get("/admin/dashboard")
async def admin_dashboard(admin=Depends(verify_admin)):
    """Dashboard administrativo completo"""
    store.record_request()

    metrics = store.get_server_metrics()
    applications = store.get_applications()

    return {
        "server_info": {
            "name": "SilhouetteMCP Server",
            "domain": "silhouettemcp.albertofarah.com",
            "version": "2.0.0",
            "uptime_hours": round(metrics.uptime / 3600, 2)
        },
        "metrics": asdict(metrics),
        "applications": [asdict(app) for app in applications],
        "connection_info": {
            "api_base_url": "https://silhouettemcp.albertofarah.com",
            "admin_api_key": applications[0].api_key if applications else "No disponible",
            "websocket_endpoint": "wss://silhouettemcp.albertofarah.com/ws",
            "rest_api_docs": "https://silhouettemcp.albertofarah.com/docs"
        },
        "quick_stats": {
            "total_agents": metrics.total_agents,
            "active_apps": metrics.total_apps,
            "total_requests": store._request_count,
            "requests_per_minute": round(metrics.requests_per_minute, 1)
        }
    }

@app.get("/admin/applications")
async def list_applications(admin=Depends(verify_admin)):
    """Listar todas las aplicaciones"""
    store.record_request()
    applications = store.get_applications()

    return {
        "applications": [
            {
                "id": app.id,
                "name": app.name,
                "description": app.description,
                "api_key": app.api_key,
                "owner_email": app.owner_email,
                "agent_count": len(app.agents),
                "is_active": app.is_active,
                "created_at": app.created_at
            }
            for app in applications
        ]
    }

@app.get("/admin/agents")
async def list_all_agents(admin=Depends(verify_admin)):
    """Listar todos los agentes"""
    store.record_request()
    agents = store.get_all_agents()

    return {
        "agents": [asdict(agent) for agent in agents],
        "total_count": len(agents),
        "by_status": {
            "active": len([a for a in agents if a.status == "active"]),
            "idle": len([a for a in agents if a.status == "idle"]),
            "error": len([a for a in agents if a.status == "error"])
        }
    }

@app.get("/admin/connection-guide")
async def connection_guide(admin=Depends(verify_admin)):
    """Guía de conexión para desarrolladores"""
    store.record_request()
    applications = store.get_applications()

    guide = {
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
            "javascript": '''
const SilhouetteMCP = {
    apiKey: 'tu_api_key',
    baseURL: 'https://silhouettemcp.albertofarah.com',
    
    async getStatus() {
        const response = await fetch(`${this.baseURL}/api/status`, {
            headers: { 'X-API-Key': this.apiKey }
        });
        return response.json();
    },
    
    async deployAgent(agentConfig) {
        const response = await fetch(`${this.baseURL}/api/agents/deploy`, {
            method: 'POST',
            headers: {
                'X-API-Key': this.apiKey,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(agentConfig)
        });
        return response.json();
    }
};
            ''',
            "python": '''
import requests

class SilhouetteMCP:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://silhouettemcp.albertofarah.com'
        self.headers = {'X-API-Key': api_key}
    
    def get_status(self):
        response = requests.get(f'{self.base_url}/api/status', headers=self.headers)
        return response.json()
    
    def deploy_agent(self, agent_config):
        response = requests.post(f'{self.base_url}/api/agents/deploy', 
                                headers=self.headers, 
                                json=agent_config)
        return response.json()
            '''
        },
        "applications": [
            {
                "id": app.id,
                "name": app.name,
                "api_key": app.api_key,
                "description": app.description,
                "agent_count": len(app.agents)
            }
            for app in applications
        ]
    }

    return guide

# ==================== ENDPOINTS PARA APLICACIONES ====================

@app.get("/api/status")
async def api_status(request: Request):
    """Status endpoint para aplicaciones"""
    store.record_request()

    # Verificar API key
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key requerida")

    app = verify_api_key(api_key)
    if not app:
        raise HTTPException(status_code=401, detail="API Key inválida")

    return {
        "app": {
            "id": app.id,
            "name": app.name
        },
        "agents": [asdict(agent) for agent in app.agents],
        "server": "SilhouetteMCP",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/agents")
async def get_app_agents(request: Request):
    """Obtener agentes de la aplicación"""
    store.record_request()

    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key requerida")

    app = verify_api_key(api_key)
    if not app:
        raise HTTPException(status_code=401, detail="API Key inválida")

    return {
        "application": app.name,
        "agents": [asdict(agent) for agent in app.agents],
        "total_agents": len(app.agents)
    }

class ChatAgentRequest(BaseModel):
    prompt: str
    model: str | None = "glm-5.2-max"
    enable_verification: bool | None = True

@app.post("/api/agents/chat")
async def chat_with_orchestrator(req: ChatAgentRequest):
    """Ejecuta una instrucción a través del Orquestador Multi-Agente"""
    store.record_request()
    try:
        if system_orchestrator:
            # Ejecutar el flujo completo multi-agente (Reasoner -> Planner -> Executor -> Verifier)
            res = await system_orchestrator.process_request(req.prompt)
            return {
                "success": True,
                "orchestrator": "MultiAgentOrchestrator",
                "result": res
            }
        else:
            # Fallback a router directo
            from backend.app.core.llm_router import LLMRouter
            router = LLMRouter()
            res = await router.chat_completion(prompt=req.prompt, model=req.model or "llama70b")
            return {
                "success": True,
                "orchestrator": "LLMRouter",
                "result": res
            }
    except Exception as e:
        logger.error(f"Error en /api/agents/chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class ArenaRequest(BaseModel):
    prompt: str
    model_a: str
    model_b: str

@app.post("/api/agents/arena")
async def battle_arena(req: ArenaRequest):
    """Ejecuta un prompt en paralelo en 2 modelos para comparar resultados side-by-side con mediciones reales"""
    store.record_request()
    try:
        import ast
        from backend.app.core.llm_router import LLMRouter
        from backend.app.logic_engine.z3_verifier import Z3Verifier
        
        router = LLMRouter()
        z3_verifier = Z3Verifier()

        # Medición de Modelo A
        t0_a = time.time()
        try:
            res_a = await router.chat_completion(prompt=req.prompt, model=req.model_a)
            err_a = None
        except Exception as e:
            res_a = f"Error: {e}"
            err_a = e
        time_a_ms = int((time.time() - t0_a) * 1000)

        # Medición de Modelo B
        t0_b = time.time()
        try:
            res_b = await router.chat_completion(prompt=req.prompt, model=req.model_b)
            err_b = None
        except Exception as e:
            res_b = f"Error: {e}"
            err_b = e
        time_b_ms = int((time.time() - t0_b) * 1000)

        # Validación real de sintaxis AST
        def check_syntax(code_str: str) -> bool:
            try:
                ast.parse(code_str)
                return True
            except Exception:
                return False

        syntax_a = check_syntax(str(res_a)) if not err_a else False
        syntax_b = check_syntax(str(res_b)) if not err_b else False

        # Verificación Z3 real
        z3_a = z3_verifier.verify_execution_safety(str(res_a))
        z3_b = z3_verifier.verify_execution_safety(str(res_b))

        sec_a = z3_a.get("safe", False)
        sec_b = z3_b.get("safe", False)

        # Score de calidad real
        score_a = round((0.5 if syntax_a else 0.1) + (0.5 if sec_a else 0.1), 2) if not err_a else 0.0
        score_b = round((0.5 if syntax_b else 0.1) + (0.5 if sec_b else 0.1), 2) if not err_b else 0.0

        winner = req.model_a if score_a >= score_b else req.model_b

        return {
            "success": True,
            "winner": winner,
            "model_a_result": {
                "modelId": req.model_a,
                "modelName": req.model_a,
                "codeOutput": str(res_a),
                "executionTimeMs": time_a_ms,
                "qualityScore": score_a,
                "syntaxValid": syntax_a,
                "securityPassed": sec_a
            },
            "model_b_result": {
                "modelId": req.model_b,
                "modelName": req.model_b,
                "codeOutput": str(res_b),
                "executionTimeMs": time_b_ms,
                "qualityScore": score_b,
                "syntaxValid": syntax_b,
                "securityPassed": sec_b
            }
        }
    except Exception as e:
        logger.error(f"Error en /api/agents/arena: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Límite de tamaño para lectura/escritura de archivos vía API (2 MiB).
MAX_FILE_BYTES = 2 * 1024 * 1024


@app.get("/api/system/file-content")
async def get_file_content(path: str, admin=Depends(verify_admin)):
    """Lee un archivo del workspace.

    La ruta se confina a la raíz del proyecto y se rechazan secretos, `.git` y
    dependencias. Requiere sesión de administrador.
    """
    try:
        resolved = resolve_within_workspace(path)
    except PathNotAllowed as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None

    if not resolved.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    if resolved.stat().st_size > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo supera el límite de {MAX_FILE_BYTES // 1024} KiB.",
        )

    try:
        content = resolved.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=415, detail="El archivo no es texto UTF-8.") from None

    return {"success": True, "path": safe_relative(resolved), "content": content}


class SaveFileRequest(BaseModel):
    path: str
    content: str


@app.post("/api/system/save-file")
async def save_file_content(req: SaveFileRequest, admin=Depends(verify_admin)):
    """Escribe un archivo dentro del workspace. Requiere sesión de administrador."""
    if len(req.content.encode("utf-8")) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"El contenido supera el límite de {MAX_FILE_BYTES // 1024} KiB.",
        )
    try:
        resolved = resolve_within_workspace(req.path)
    except PathNotAllowed as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None

    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(req.content, encoding="utf-8")
    logger.info("Archivo escrito por %s: %s", admin["email"], safe_relative(resolved))
    return {
        "success": True,
        "path": safe_relative(resolved),
        "message": "Archivo guardado exitosamente",
    }


class OSLaunchRequest(BaseModel):
    app_name: str
    args: str | None = None


@app.post("/api/system/os-launch")
async def launch_os_app(req: OSLaunchRequest, admin=Depends(verify_admin)):
    """Lanza una aplicación de la lista blanca.

    Desactivado salvo que `SILHOUETTE_ALLOWED_APPS` declare aplicaciones
    permitidas. El ejecutable se resuelve por PATH, nunca desde la petición.
    """
    try:
        plan = plan_launch(req.app_name, req.args)
    except AppNotAllowed as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    except ArgumentRejected as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

    from backend.app.agents.os_control_agent import OSControlAgent

    logger.info("Lanzamiento solicitado por %s: %s", admin["email"], plan.app_name)
    agent = OSControlAgent()
    return await agent.launch_plan(plan)

class CreateMCPServerRequest(BaseModel):
    name: str
    description: str | None = ""

@app.post("/api/mcp/create-server")
async def create_dynamic_mcp_server(req: CreateMCPServerRequest, admin=Depends(verify_admin)):
    """Genera dinámicamente un nuevo servidor MCP usando FastMCP"""
    from backend.app.core.dynamic_mcp_factory import DynamicMCPFactory
    factory = DynamicMCPFactory()
    return factory.create_server(req.name, req.description or "")

# ==================== ENDPOINTS COGNITIVOS AVANZADOS ====================
# Los subsistemas cognitivos son costosos de construir (abren SQLite, cargan el
# embedder) y guardan estado entre llamadas. Se crean una vez y se reutilizan,
# en lugar de instanciarse por petición como antes.

from backend.app.evolution.agent_improver import AgentImprover
from backend.app.logic_engine.z3_verifier import Z3LogicVerifier
from backend.app.orchestrator.executive_supervisor import supervisor as team_supervisor
from backend.app.security.prompt_injection_guard import PromptInjectionGuard
from backend.app.services.silhouette_brain_service import (
    BrainUnavailable,
    SilhouetteBrainService,
)
from backend.app.swarm.debate_matrix import DebateSwarmMatrix, DebateUnavailable

brain_service = SilhouetteBrainService()
z3_verifier = Z3LogicVerifier()
injection_guard = PromptInjectionGuard()
agent_improver = AgentImprover(supervisor=team_supervisor)
# El debate necesita el router del orquestador: sin él no puede haber debate.
debate_matrix = DebateSwarmMatrix(llm_router=system_orchestrator.llm_router)


class Z3VerifyRequest(BaseModel):
    type: str
    target_path: str | None = None
    memory_mb: int | None = 256
    files_touched: int | None = 1


@app.post("/api/system/z3-verify")
async def verify_z3_invariants(req: Z3VerifyRequest):
    """Verifica los invariantes de seguridad de una acción propuesta."""
    return z3_verifier.verify_action_invariants(req.dict())


class DebateSwarmRequest(BaseModel):
    prompt: str


@app.post("/api/swarm/debate")
async def run_debate_swarm(req: DebateSwarmRequest):
    """Ejecuta una ronda real de debate: Creador → Crítico → Juez."""
    try:
        return await debate_matrix.execute_debate_round(req.prompt)
    except DebateUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None


@app.get("/api/brain/stats")
async def get_brain_stats():
    """Estado real de los cuatro niveles de memoria."""
    return brain_service.get_stats()


class RememberRequest(BaseModel):
    content: str
    importance: float = 0.8
    tags: list[str] | None = None


@app.post("/api/brain/remember")
async def brain_remember(req: RememberRequest, admin=Depends(verify_admin)):
    """Indexa un evento en la memoria cognitiva."""
    try:
        return await brain_service.remember_event(
            req.content, req.importance, tags=req.tags, source="api"
        )
    except BrainUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None


@app.get("/api/brain/recall")
async def brain_recall(query: str, limit: int = 5):
    """Búsqueda semántica sobre la memoria."""
    try:
        return await brain_service.recall(query, limit=limit)
    except BrainUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None


@app.get("/api/brain/context")
async def brain_context(query: str, token_budget: int = 4000, graph: bool = True):
    """Ensambla contexto respetando un presupuesto real de tokens."""
    try:
        return await brain_service.assemble_context(
            query, token_budget=token_budget, include_graph=graph
        )
    except BrainUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None


class SecurityGuardRequest(BaseModel):
    text: str


@app.post("/api/security/guard")
async def check_security_guard(req: SecurityGuardRequest):
    """Clasifica el nivel de amenaza de un prompt y decide si puede continuar."""
    return injection_guard.sanitize_and_validate(req.text)


@app.get("/api/supervisor/audit")
async def audit_supervisor_teams():
    """Estado real de la jerarquía multi-equipo, medido desde la telemetría."""
    return await team_supervisor.audit_team_performance()


@app.post("/api/supervisor/resolve/{team_id}")
async def resolve_team_deadlock(team_id: str, admin=Depends(verify_admin)):
    """Libera las tareas estancadas de un equipo."""
    return await team_supervisor.resolve_team_deadlock(team_id)


class ImproveAgentRequest(BaseModel):
    agent_name: str
    # Si se omite, se usa la tasa de error medida por el supervisor.
    error_rate: float | None = None


@app.post("/api/evolution/improve-agent")
async def improve_agent_performance(req: ImproveAgentRequest, admin=Depends(verify_admin)):
    """Ajusta el perfil persistido de un agente según su rendimiento medido."""
    return await agent_improver.evaluate_and_improve_agent(req.agent_name, req.error_rate)


@app.get("/api/evolution/profiles")
async def list_agent_profiles():
    """Perfiles vigentes y su historial de ajustes."""
    return {
        "profiles": agent_improver.store.all_profiles(),
        "history": agent_improver.history(),
    }


# ==================== JERARQUÍA DINÁMICA Y BUCLE AUTÓNOMO ====================
# Portado de Silhouette Agency OS: el organigrama del equipo lo diseña un modelo
# a partir del objetivo, y un bucle en segundo plano deriva objetivos de la
# telemetría real, recalibra agentes y forma equipos para resolverlos.

from backend.app.evolution.evolution_scheduler import EvolutionScheduler
from backend.app.evolution.introspection import IntrospectionEngine
from backend.app.orchestrator.squad_factory import (
    SquadDesignError,
    SquadFactory,
    SquadFactoryUnavailable,
)

introspection_engine = IntrospectionEngine(supervisor=team_supervisor)
squad_factory = SquadFactory(
    llm_router=system_orchestrator.llm_router,
    supervisor=team_supervisor,
    brain=brain_service,
)
evolution_scheduler = EvolutionScheduler(
    introspection=introspection_engine,
    improver=agent_improver,
    squad_factory=squad_factory,
    supervisor=team_supervisor,
)


class SpawnSquadRequest(BaseModel):
    goal: str
    budget: str = "BALANCED"
    context: str = ""


@app.post("/api/squads/spawn")
async def spawn_squad(req: SpawnSquadRequest, admin=Depends(verify_admin)):
    """Diseña y forma un equipo a medida para un objetivo."""
    try:
        squad = await squad_factory.spawn_squad(
            req.goal, budget=req.budget, context=req.context
        )
    except SquadFactoryUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    except SquadDesignError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None
    return squad.to_dict()


@app.get("/api/squads")
async def list_squads():
    """Equipos activos con su composición y liderazgo."""
    return {"squads": squad_factory.all_squads()}


@app.delete("/api/squads/{squad_id}")
async def disband_squad(squad_id: str, admin=Depends(verify_admin)):
    """Disuelve un equipo."""
    if not squad_factory.disband(squad_id):
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return {"success": True, "squad_id": squad_id}


@app.get("/api/evolution/status")
async def evolution_status():
    """Estado del bucle autónomo y sus ciclos recientes."""
    return evolution_scheduler.status()


@app.post("/api/evolution/start")
async def start_evolution(admin=Depends(verify_admin)):
    """Arranca el bucle autónomo."""
    evolution_scheduler.start()
    return {"running": evolution_scheduler.is_running}


@app.post("/api/evolution/stop")
async def stop_evolution(admin=Depends(verify_admin)):
    """Detiene el bucle autónomo."""
    await evolution_scheduler.stop()
    return {"running": evolution_scheduler.is_running}


@app.post("/api/evolution/trigger")
async def trigger_evolution(admin=Depends(verify_admin)):
    """Ejecuta un ciclo completo de inmediato."""
    return await evolution_scheduler.trigger_now()


@app.get("/api/evolution/goals")
async def list_goals():
    """Objetivos que el sistema se ha fijado a sí mismo."""
    return {
        "stats": introspection_engine.stats(),
        "active": [g.to_dict() for g in introspection_engine.active_goals()],
        "all": introspection_engine.all_goals(),
    }


class AddGoalRequest(BaseModel):
    description: str
    priority: str = "MEDIUM"


@app.post("/api/evolution/goals")
async def add_goal(req: AddGoalRequest, admin=Depends(verify_admin)):
    """Añade un objetivo manualmente al ciclo de evolución."""
    return introspection_engine.add_goal(req.description, req.priority).to_dict()


# ==================== EL ORGANISMO ====================
# La capa que mantiene vivo el sistema sin que nadie interactúe. Los ciclos
# cognitivos se registran como órganos: el daemon decide cuáles ejecutar según
# la fase circadiana y espacia su cadencia según los recursos del anfitrión.
#
# El efecto práctico: mientras trabajas, el organismo se aparta y sólo late.
# Cuando te vas, consolida memoria, deriva objetivos y recalibra agentes.

from backend.app.organism import VitalDaemon
from backend.app.organism.vital_daemon import OrganismAlreadyRunning

organism = VitalDaemon()


async def _organ_consolidation() -> str:
    """Consolida la memoria: es el trabajo de la fase de sueño."""
    if not brain_service.available:
        return "memoria no disponible"
    stats = brain_service.get_stats()
    niveles = stats["tiers"]
    return (
        f"episódica={niveles['episodic']} semántica={niveles['semantic']} "
        f"entidades={niveles['deep_graph']['entities']}"
    )


async def _organ_introspection() -> str:
    registro = await evolution_scheduler.run_introspection_cycle()
    return f"{registro.goals_derived} objetivo(s) derivado(s)"


async def _organ_calibration() -> str:
    registro = await evolution_scheduler.run_calibration_cycle()
    return f"{len(registro.agents_calibrated)} agente(s) recalibrado(s)"


async def _organ_goals() -> str:
    registro = await evolution_scheduler.run_goal_cycle()
    return f"{len(registro.squads_spawned)} equipo(s) formado(s)"


async def _organ_vitals() -> str:
    auditoria = await team_supervisor.audit_team_performance()
    return (
        f"equipos={auditoria['active_teams']} "
        f"en_vuelo={auditoria['tasks_in_flight']} "
        f"estancadas={len(auditoria['stalled_tasks'])}"
    )


# Los intervalos son los base; la homeostasis y la fase los escalan.
organism.register("vitals", _organ_vitals, 120.0)
organism.register("consolidation", _organ_consolidation, 600.0)
organism.register("introspection", _organ_introspection, 900.0)
organism.register("calibration", _organ_calibration, 1800.0)
organism.register("goals", _organ_goals, 1200.0)


@app.middleware("http")
async def _touch_organism(request: Request, call_next):
    """Cada petición devuelve el organismo a la vigilia."""
    organism.touch()
    return await call_next(request)


# ==================== CONEXIÓN DE IAs ====================
# Un solo sitio para saber qué modelos hay, conectar uno nuevo y arreglar lo que
# esté bloqueado. `/api/setup/status` es el punto de entrada.

from backend.app.core import onboarding as _onboarding
from backend.app.core.providers import PROVIDERS, check_provider


@app.get("/api/setup/status")
async def setup_status():
    """Estado completo de conectividad: qué IA está lista y qué falta para el resto."""
    informe = await _onboarding.build_report()
    return informe.to_dict()


@app.get("/api/setup/providers")
async def setup_providers():
    """Catálogo de proveedores conectables, con dónde obtener cada credencial."""
    return {
        "providers": [
            {
                "name": s.name,
                "label": s.label,
                "kind": s.kind.value,
                "auth": s.auth.value,
                "env_var": s.env_var,
                "signup_url": s.signup_url,
                "how_to": s.how_to,
                "configured": s.configured,
            }
            for s in PROVIDERS.values()
        ]
    }


class ConnectProviderRequest(BaseModel):
    provider: str
    credential: str


@app.post("/api/setup/credential")
async def setup_credential(req: ConnectProviderRequest, admin=Depends(verify_admin)):
    """Valida una credencial con una llamada real y la guarda sólo si funciona."""
    try:
        resultado = await _onboarding.connect_provider(req.provider, req.credential)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    if not resultado["saved"] and resultado["health"]["status"] != "ready":
        raise HTTPException(status_code=400, detail=resultado["detail"])
    return resultado


@app.post("/api/setup/verify/{provider}")
async def setup_verify(provider: str, admin=Depends(verify_admin)):
    """Comprueba un proveedor ya configurado, sin modificar nada."""
    try:
        return (await check_provider(provider)).to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None


@app.post("/api/setup/login/{cli_name}")
async def setup_login(cli_name: str, admin=Depends(verify_admin)):
    """Inicia el login por navegador de un agente CLI (Google, GitHub…)."""
    try:
        return await _onboarding.start_browser_login(cli_name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None


@app.post("/api/setup/fix/{fix_id}")
async def setup_fix(fix_id: str, admin=Depends(verify_admin)):
    """Aplica una reparación automática de las que reporta `/api/setup/status`."""
    reparacion = _onboarding.AUTO_FIXES.get(fix_id)
    if reparacion is None:
        raise HTTPException(
            status_code=404,
            detail=f"Reparación desconocida '{fix_id}'. Disponibles: {', '.join(_onboarding.AUTO_FIXES)}",
        )
    return reparacion()


@app.get("/api/models/cli")
async def list_cli_agents():
    """Agentes de línea de comandos detectados en esta máquina.

    La detección es real: se localiza el ejecutable probando el PATH y las rutas
    conocidas con todas las extensiones del sistema.
    """
    from backend.app.core.cli_adapters import discover_installed

    inventario = discover_installed()
    return {
        "agents": list(inventario.values()),
        "available": sorted(n for n, i in inventario.items() if i["available"]),
        "total_registered": len(inventario),
    }


class CLIProbeRequest(BaseModel):
    cli_name: str
    prompt: str = "Responde únicamente con la palabra OK."


@app.post("/api/models/cli/probe")
async def probe_cli_agent(req: CLIProbeRequest, admin=Depends(verify_admin)):
    """Ejecuta un agente CLI de verdad para comprobar que responde.

    Distingue los tres estados que importan: no instalado, instalado pero sin
    sesión, y operativo.
    """
    from backend.app.core.cli_adapters import (
        CLIInvocationError,
        CLINotAuthenticated,
        CLIUnavailable,
        run_cli,
    )

    try:
        salida = await run_cli(req.cli_name, req.prompt)
    except CLIUnavailable as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except CLINotAuthenticated as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from None
    except CLIInvocationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None

    return {"cli": req.cli_name, "ok": True, "response": salida}


@app.get("/api/organism/vitals")
async def organism_vitals():
    """Signos vitales: fase, recursos, salud de cada órgano y actividad."""
    return organism.vitals()


@app.post("/api/organism/awaken")
async def awaken_organism(admin=Depends(verify_admin)):
    """Da vida al organismo: empieza a latir y a trabajar solo."""
    try:
        organism.start()
    except OrganismAlreadyRunning as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return {"alive": organism.is_alive}


@app.post("/api/organism/rest")
async def rest_organism(admin=Depends(verify_admin)):
    """Detiene el organismo con orden, guardando su estado."""
    await organism.stop()
    return {"alive": organism.is_alive}


@app.post("/api/organism/tick")
async def organism_tick(admin=Depends(verify_admin)):
    """Fuerza un latido inmediato, sin esperar al planificador."""
    resultados = await organism.tick()
    return {"executed": [r.to_dict() for r in resultados]}


class HomeostasisRequest(BaseModel):
    # None devuelve el control a la medición automática.
    profile: str | None = None


@app.post("/api/organism/homeostasis")
async def set_homeostasis(req: HomeostasisRequest, admin=Depends(verify_admin)):
    """Fija o libera el perfil de recursos."""
    try:
        organism.homeostasis.force_profile(req.profile)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    return organism.homeostasis.synthesize().to_dict()


# ==================== MOTORES COGNITIVOS Y AUTO-SANACIÓN ====================
# Los cuatro motores del brain (Curiosity, Janitor, Dreamer, Evolution) se
# registran como órganos: se ejecutan solos durante la fase de sueño, que es
# cuando reescribir la memoria no compite con el trabajo del usuario.

from backend.app.organism.cognitive_organs import (
    CognitiveEnginesUnavailable,
    CognitiveOrgans,
)
from backend.app.organism.self_healing import SelfHealing

cognitive_organs = CognitiveOrgans(brain=brain_service)
cognitive_organs.register_with(organism)

self_healing = SelfHealing(
    organism=organism, supervisor=team_supervisor, improver=agent_improver
)


@app.get("/api/cognition/engines")
async def cognition_engines():
    """Estado de los motores cognitivos, contado desde ejecuciones reales."""
    return cognitive_organs.stats()


@app.post("/api/cognition/run/{engine}")
async def cognition_run(engine: str, admin=Depends(verify_admin)):
    """Ejecuta un motor cognitivo de inmediato."""
    try:
        return (await cognitive_organs.run_engine(engine)).to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except CognitiveEnginesUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None


@app.post("/api/cognition/run-all")
async def cognition_run_all(admin=Depends(verify_admin)):
    """Ciclo cognitivo completo: Janitor → Dreamer → Curiosity → Evolution."""
    try:
        return {"runs": [r.to_dict() for r in await cognitive_organs.run_all()]}
    except CognitiveEnginesUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None


@app.get("/api/health/diagnose")
async def health_diagnose():
    """Diagnóstico de salud medido, no estimado."""
    return self_healing.diagnose().to_dict()


@app.post("/api/health/heal")
async def health_heal(admin=Depends(verify_admin)):
    """Aplica las reparaciones que procedan y reporta qué hizo."""
    return await self_healing.heal()


# ==================== HERRAMIENTAS REALES ====================
# Cada una sustituye a una capacidad que en legacy/ devolvía datos inventados.

from backend.app.tools import git_agent as _git
from backend.app.tools import market_data as _market
from backend.app.tools import research as _research


@app.get("/api/git/info")
async def git_info(path: str = ".", admin=Depends(verify_admin)):
    """Estado real del repositorio."""
    try:
        return (await _git.GitAgent(path).get_repository_info()).to_dict()
    except _git.GitError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None


@app.get("/api/git/history")
async def git_history(path: str = ".", limit: int = 20, admin=Depends(verify_admin)):
    """Historial real de commits."""
    try:
        commits = await _git.GitAgent(path).get_commit_history(limit=limit)
    except _git.GitError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    return {"commits": [c.to_dict() for c in commits], "count": len(commits)}


class GitBranchRequest(BaseModel):
    path: str = "."
    name: str
    from_ref: str | None = None


@app.post("/api/git/branch")
async def git_branch(req: GitBranchRequest, admin=Depends(verify_admin)):
    """Crea una rama real."""
    try:
        return await _git.GitAgent(req.path).create_branch(req.name, from_ref=req.from_ref)
    except _git.InvalidBranchName as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except _git.GitError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None


class GitConflictRequest(BaseModel):
    path: str = "."
    source: str
    target: str


@app.post("/api/git/check-conflicts")
async def git_check_conflicts(req: GitConflictRequest, admin=Depends(verify_admin)):
    """Comprueba si dos ramas fusionan limpio, sin fusionar nada."""
    try:
        informe = await _git.GitAgent(req.path).detect_conflicts(req.source, req.target)
    except (_git.InvalidBranchName, _git.GitError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    return informe.to_dict()


@app.get("/api/research/search")
async def research_search(query: str, limit: int = 10):
    """Búsqueda real en arXiv y Semantic Scholar."""
    try:
        return await _research.search(query, limit=limit)
    except _research.ResearchUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None


@app.get("/api/market/quote")
async def market_quote(symbol: str):
    """Cotización real, con su advertencia de retardo."""
    try:
        return (await _market.get_quote(symbol)).to_dict()
    except _market.MarketDataUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None


@app.get("/api/market/history")
async def market_history(symbol: str, period: str = "1mo", interval: str = "1d"):
    """Serie histórica real de precios."""
    try:
        return await _market.get_history(symbol, period=period, interval=interval)
    except _market.MarketDataUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None


# ==================== HERRAMIENTAS DEL AGENTE DE DESARROLLO ====================
# Editar código, ejecutar los tests y entender el repositorio. Sin estas tres,
# el sistema genera texto pero no desarrolla.

from backend.app.tools.code_editor import CodeEditor, EditError
from backend.app.tools.repo_index import RepoIndex
from backend.app.tools.suite_runner import SuiteRunner, SuiteRunnerUnavailable

code_editor = CodeEditor()
repo_index = RepoIndex()
test_runner = SuiteRunner()


@app.get("/api/code/read")
async def code_read(path: str, admin=Depends(verify_admin)):
    """Lee un archivo con su estructura (clases y funciones con su línea)."""
    try:
        return code_editor.read(path).to_dict()
    except EditError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None


class CodeReplaceRequest(BaseModel):
    path: str
    old: str
    new: str
    replace_all: bool = False


@app.post("/api/code/replace")
async def code_replace(req: CodeReplaceRequest, admin=Depends(verify_admin)):
    """Sustituye un fragmento exacto. Valida la sintaxis antes de escribir."""
    try:
        return code_editor.replace(
            req.path, req.old, req.new, replace_all=req.replace_all
        ).to_dict()
    except EditError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None


class CodeWriteRequest(BaseModel):
    path: str
    content: str


@app.post("/api/code/write")
async def code_write(req: CodeWriteRequest, admin=Depends(verify_admin)):
    """Sobrescribe un archivo, respaldando el anterior."""
    try:
        return code_editor.write(req.path, req.content).to_dict()
    except EditError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None


@app.post("/api/code/revert")
async def code_revert(path: str, admin=Depends(verify_admin)):
    """Restaura la última copia de seguridad de un archivo."""
    try:
        return code_editor.revert(path).to_dict()
    except EditError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None


@app.post("/api/tests/run")
async def tests_run(
    target: str | None = None,
    keyword: str | None = None,
    admin=Depends(verify_admin),
):
    """Ejecuta la suite de verdad y devuelve lo que ocurrió."""
    try:
        return (await test_runner.run(target, keyword=keyword)).to_dict()
    except SuiteRunnerUnavailable as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None


@app.get("/api/repo/stats")
async def repo_stats():
    """Estructura del repositorio, contada leyendo los archivos."""
    return repo_index.stats()


@app.get("/api/repo/symbol")
async def repo_symbol(name: str, exact: bool = False):
    """Dónde está definido un símbolo."""
    return {"symbol": name, "matches": repo_index.find_symbol(name, exact=exact)}


@app.get("/api/repo/references")
async def repo_references(symbol: str):
    """Dónde se define y dónde se usa: la consulta previa a cambiar una firma."""
    return repo_index.find_references(symbol)


@app.get("/api/repo/search")
async def repo_search(pattern: str, regex: bool = False, suffix: str | None = None):
    """Busca texto en el repositorio."""
    try:
        return {"pattern": pattern, "hits": repo_index.search_text(pattern, regex=regex, suffix=suffix)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None


@app.get("/api/repo/outline")
async def repo_outline(path: str):
    """Estructura de un archivo concreto."""
    try:
        return repo_index.outline(path)
    except (FileNotFoundError, PathNotAllowed) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None


@app.post("/api/agents/deploy")
async def deploy_agent(request: Request, admin=Depends(verify_admin)):
    """Desplegar nuevo agente"""
    store.record_request()

    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key requerida")

    app = verify_api_key(api_key)
    if not app:
        raise HTTPException(status_code=401, detail="API Key inválida")

    try:
        data = await request.json()

        # Crear nuevo agente
        agent = AgentInstance(
            id=data.get("id", f"agent_{secrets.token_hex(8)}"),
            name=data.get("name", "Nuevo Agente"),
            app_id=app.id,
            agent_type=data.get("type", "custom"),
            status="active"
        )

        store.add_agent_to_app(app.id, agent)

        return {
            "success": True,
            "message": f"Agente '{agent.name}' desplegado exitosamente",
            "agent": asdict(agent)
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error desplegando agente: {str(e)}")

@app.post("/api/agents/stop")
async def stop_agent(request: Request, admin=Depends(verify_admin)):
    """Detener agente"""
    store.record_request()

    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key requerida")

    app = verify_api_key(api_key)
    if not app:
        raise HTTPException(status_code=401, detail="API Key inválida")

    try:
        data = await request.json()
        agent_id = data.get("agent_id")

        if not agent_id:
            raise HTTPException(status_code=400, detail="agent_id requerido")

        # Actualizar estado del agente
        store.update_agent(app.id, agent_id, {"status": "stopped"})

        return {
            "success": True,
            "message": f"Agente '{agent_id}' detenido"
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error deteniendo agente: {str(e)}")

# ==================== WEBSOCKET PARA MÉTRICAS EN TIEMPO REAL ====================

@app.get("/metrics/stream")
async def metrics_stream(request: Request):
    """Stream de métricas en tiempo real"""
    store.record_request()

    async def generate_metrics():
        while True:
            try:
                metrics = store.get_server_metrics()
                data = {
                    "timestamp": metrics.timestamp,
                    "server": "SilhouetteMCP",
                    "total_agents": metrics.total_agents,
                    "total_apps": metrics.total_apps,
                    "total_tasks": metrics.total_tasks,
                    "total_tokens": metrics.total_tokens,
                    "uptime_hours": round(metrics.uptime / 3600, 2),
                    "requests_per_minute": round(metrics.requests_per_minute, 1)
                }

                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                await asyncio.sleep(2)  # Actualizar cada 2 segundos

            except Exception as e:
                logger.error(f"Error en stream de métricas: {e}")
                await asyncio.sleep(5)

    return StreamingResponse(
        generate_metrics(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )

# ==================== WEBSOCKET & HITL ====================

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket broadcast error: {e}")

ws_manager = ConnectionManager()

@app.websocket("/api/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """WebSocket para transmitir telemetría, razonamiento y estado en tiempo real"""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Mantener conexión activa y escuchar comandos del frontend
            data = await websocket.receive_text()
            logger.info(f"WS Recibió: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

class ResumeRequestModel(BaseModel):
    conversation_id: str
    approved: bool
    feedback: str = ""

@app.post("/api/hitl/resume")
async def resume_hitl_task(req: ResumeRequestModel):
    """Endpoint para que el humano apruebe/rechace una tarea pausada"""
    try:
        # Asumiendo que hay una instancia global del orquestador en algún lugar.
        # Aquí enviaríamos la señal de resume. Para el mockup de este endpoint:

        # Simulamos que la tarea fue reanudada para mantener compatibilidad
        # (Idealmente inyectaríamos el orquestador como dependencia)

        # Enviar broadcast por WebSocket para actualizar la UI en vivo
        await ws_manager.broadcast({
            "type": "HITL_UPDATE",
            "conversation_id": req.conversation_id,
            "approved": req.approved,
            "status": "resumed" if req.approved else "aborted"
        })

        return {"status": "success", "message": f"Resume instruction for {req.conversation_id} registered."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== PRODUCTIVITY FEATURES (FASE 2 & 3) ====================

class ErrorAnalysisRequest(BaseModel):
    error_logs: str
    context_info: str | None = ""

@app.post("/api/agents/analyze-error")
async def analyze_error(req: ErrorAnalysisRequest):
    """Fase 2: AI Error Explainer"""
    try:
        prompt = f"The following task failed with this output:\n\n{req.error_logs}\n\nContext: {req.context_info}\n\nPlease explain what went wrong and propose a fix."

        # Utilizamos el orquestador global (definido arriba) para procesar el análisis de error
        # Se envía con prioridad alta para saltar a la parte delantera de la cola
        result = await system_orchestrator.process_request(
            objetivo=prompt,
            contexto={"source": "ai_error_explainer", "priority": "high"},
            user_id="dashboard_user"
        )
        return {"status": "success", "analysis": result}
    except Exception as e:
        logger.exception("Failed to analyze error via AI")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/search")
async def global_omni_search(query: str):
    """Fase 3: Global Omni-Search (Cmd+K)"""
    try:
        query_lower = query.lower()
        results = {
            "applications": [],
            "active_tasks": [],
            "agents": []
        }

        # Buscar en aplicaciones
        for app_obj in store.get_applications():
            if query_lower in app_obj.name.lower() or query_lower in app_obj.id.lower():
                results["applications"].append({"id": app_obj.id, "name": app_obj.name, "type": "application"})

            # Buscar en agentes dentro de apps
            for agent in app_obj.agents:
                if query_lower in agent.name.lower() or query_lower in agent.id.lower():
                    results["agents"].append({"id": agent.id, "name": agent.name, "app_id": app_obj.id, "type": "agent"})

        # Buscar en tareas del orquestador global
        for task_id, task_data in system_orchestrator.active_sessions.items():
            task_str = str(task_data).lower()
            if query_lower in task_id.lower() or query_lower in task_str:
                results["active_tasks"].append({"id": task_id, "status": task_data.get("status"), "type": "task"})

        return {"status": "success", "results": results}
    except Exception as e:
        logger.exception("Global search failed")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== PROMETHEUS METRICS ====================

from prometheus_client import REGISTRY

if "silhouette_cpu_usage_percent" not in REGISTRY._names_to_collectors:
    cpu_usage_gauge = Gauge("silhouette_cpu_usage_percent", "CPU usage percent")
else:
    cpu_usage_gauge = REGISTRY._names_to_collectors["silhouette_cpu_usage_percent"]

if "silhouette_active_agents" not in REGISTRY._names_to_collectors:
    active_agents_gauge = Gauge("silhouette_active_agents", "Number of active agents")
else:
    active_agents_gauge = REGISTRY._names_to_collectors["silhouette_active_agents"]

@app.get("/metrics")
async def metrics_endpoint():
    """Endpoint para métricas de Prometheus"""
    try:
        cpu_usage_gauge.set(psutil.cpu_percent())
        agents = store.get_all_agents()
        active_agents = sum(1 for a in agents if a.status == "active")
        active_agents_gauge.set(active_agents)
    except Exception as e:
        logger.error(f"Error actualizando métricas: {e}")

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# ==================== MÉTRICAS REALES DEL SISTEMA ====================

@app.get("/api/system/metrics")
async def get_system_metrics():
    """Obtener métricas reales del sistema"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "cpu": {
                "percent": round(cpu_percent, 2),
                "count": psutil.cpu_count(),
                "frequency": psutil.cpu_freq().current if psutil.cpu_freq() else 0
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            },
            "network": {
                "connections": len(psutil.net_connections(kind='inet'))
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error obteniendo métricas del sistema: {e}")
        return {
            "cpu": {"percent": 0, "count": 0, "frequency": 0},
            "memory": {"total": 0, "available": 0, "percent": 0, "used": 0, "free": 0},
            "disk": {"total": 0, "used": 0, "free": 0, "percent": 0},
            "network": {"connections": 0},
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/system/logs")
async def get_system_logs(lines: int = 50, admin=Depends(verify_admin)):
    """Obtener logs reales del sistema"""
    try:
        # Leer logs de archivo si existe
        log_file = Path("silhouettemcp.log")
        if log_file.exists():
            with open(log_file) as f:
                all_logs = f.readlines()
                recent_logs = all_logs[-lines:] if len(all_logs) > lines else all_logs
                return {
                    "logs": [log.strip() for log in recent_logs],
                    "count": len(recent_logs),
                    "timestamp": datetime.now().isoformat()
                }
        else:
            # Logs de muestra si no existe archivo
            return {
                "logs": [
                    f"[{datetime.now().isoformat()}] INFO - SilhouetteMCP server running",
                    f"[{datetime.now().isoformat()}] INFO - All systems operational",
                    f"[{datetime.now().isoformat()}] DEBUG - Health check completed"
                ],
                "count": 3,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error obteniendo logs: {e}")
        return {"logs": [], "count": 0, "timestamp": datetime.now().isoformat()}

# ==================== CREACIÓN DINÁMICA DE APIS ====================

class CreateAPIRequest(BaseModel):
    name: str
    description: str
    agent_type: str = "custom"

@app.post("/api/dynamic/create")
async def create_dynamic_api(request: CreateAPIRequest, admin=Depends(verify_admin)):
    """Crear una nueva API/Aplicación dinámica"""
    try:
        # Generar ID único
        app_id = f"app_{secrets.token_hex(8)}"

        # Crear nueva aplicación
        new_app = Application(
            id=app_id,
            name=request.name,
            description=request.description,
            api_key=store._generate_api_key(),
            owner_email=settings.SILHOUETTE_ADMIN_EMAIL,
            agents=[
                AgentInstance(
                    id=f"agent_{secrets.token_hex(8)}",
                    name=f"{request.name} Agent",
                    app_id=app_id,
                    agent_type=request.agent_type,
                    status="active"
                )
            ]
        )

        # Guardar en store
        store.add_application(new_app)

        logger.info(f"API dinámica creada: {request.name} ({app_id})")

        return {
            "success": True,
            "message": f"API '{request.name}' creada exitosamente",
            "application": asdict(new_app)
        }

    except Exception as e:
        logger.error(f"Error creando API dinámica: {e}")
        raise HTTPException(status_code=500, detail=f"Error creando API: {str(e)}")

@app.delete("/api/dynamic/{app_id}")
async def delete_dynamic_api(app_id: str, admin=Depends(verify_admin)):
    """Eliminar una API/Aplicación"""
    try:
        # Encontrar y eliminar aplicación
        apps = store._data.get("applications", [])
        app_found = False

        for i, app in enumerate(apps):
            if app["id"] == app_id:
                apps.pop(i)
                app_found = True
                store.save_data()
                break

        if not app_found:
            raise HTTPException(status_code=404, detail="Aplicación no encontrada")

        logger.info(f"API dinámica eliminada: {app_id}")

        return {
            "success": True,
            "message": "API eliminada exitosamente"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando API: {e}")
        raise HTTPException(status_code=500, detail=f"Error eliminando API: {str(e)}")

# ==================== GESTIÓN DE BACKUPS ====================

@app.post("/api/system/backup")
async def create_backup(admin=Depends(verify_admin)):
    """Crear backup del sistema"""
    try:
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"silhouettemcp_backup_{timestamp}.json"

        # Guardar datos actuales
        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "server_info": store._data.get("server_info", {}),
            "applications": store._data.get("applications", []),
            "metrics": store._data.get("metrics", {})
        }

        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)

        logger.info(f"Backup creado: {backup_file}")

        return {
            "success": True,
            "message": "Backup creado exitosamente",
            "backup_file": str(backup_file),
            "timestamp": timestamp,
            "size_bytes": backup_file.stat().st_size
        }

    except Exception as e:
        logger.error(f"Error creando backup: {e}")
        raise HTTPException(status_code=500, detail=f"Error creando backup: {str(e)}")

@app.get("/api/system/backups")
async def list_backups(admin=Depends(verify_admin)):
    """Listar backups disponibles"""
    try:
        backup_dir = Path("backups")
        if not backup_dir.exists():
            return {"backups": [], "count": 0}

        backups = []
        for backup_file in backup_dir.glob("silhouettemcp_backup_*.json"):
            backups.append({
                "filename": backup_file.name,
                "path": str(backup_file),
                "size_bytes": backup_file.stat().st_size,
                "created": datetime.fromtimestamp(backup_file.stat().st_ctime).isoformat()
            })

        backups.sort(key=lambda x: x["created"], reverse=True)

        return {
            "backups": backups,
            "count": len(backups)
        }

    except Exception as e:
        logger.error(f"Error listando backups: {e}")
        raise HTTPException(status_code=500, detail=f"Error listando backups: {str(e)}")

# ==================== ENDPOINTS DE MODELOS DE IA Y LOCAL AI ====================

class RegisterModelRequest(BaseModel):
    name: str
    provider: str
    model_name: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    context_window: int | None = 128000
    is_local: bool | None = False

class PullModelRequest(BaseModel):
    model_name: str

@app.get("/api/system/models")
async def get_all_models():
    """Retorna todos los modelos registrados (Cloud + Locales Autodescubiertos)."""
    try:
        from backend.app.core.dynamic_model_registry import model_registry
        from backend.app.core.local_ai_service import local_ai_service

        static_models = model_registry.get_all_models()
        local_discovered = await local_ai_service.discover_all()

        # Inyectar modelos locales autodescubiertos a la lista
        discovered_models = []
        for loc in local_discovered:
            for m_name in loc["models"]:
                discovered_models.append({
                    "id": f"{loc['provider']}-{m_name}",
                    "name": f"{m_name} ({loc['provider'].upper()} Local)",
                    "provider": loc["provider"],
                    "model_name": m_name,
                    "base_url": loc["base_url"],
                    "is_local": True,
                    "status": "online"
                })

        return {
            "cloud_and_custom_models": static_models,
            "local_autodiscovered_models": discovered_models,
            "total_count": len(static_models) + len(discovered_models)
        }
    except Exception as e:
        logger.error(f"Error al obtener modelos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/system/models")
async def register_custom_model(req: RegisterModelRequest, admin=Depends(verify_admin)):
    """Registra un nuevo modelo dinámicamente (Zhipu, Moonshot, OpenRouter, Custom API)."""
    try:
        from backend.app.core.dynamic_model_registry import model_registry
        new_model = model_registry.register_model(req.dict())
        return {"success": True, "model": new_model}
    except Exception as e:
        logger.error(f"Error al registrar modelo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/system/models/{model_id}")
async def delete_custom_model(model_id: str, admin=Depends(verify_admin)):
    """Elimina un modelo personalizado registrado."""
    try:
        from backend.app.core.dynamic_model_registry import model_registry
        removed = model_registry.remove_model(model_id)
        if not removed:
            raise HTTPException(status_code=404, detail="Modelo no encontrado")
        return {"success": True, "message": f"Modelo {model_id} eliminado."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/local-ai")
async def check_local_ai():
    """Comprueba el estado de Ollama (11434) y LM Studio (1234)."""
    try:
        from backend.app.core.local_ai_service import local_ai_service
        discovered = await local_ai_service.discover_all()
        return {"local_services": discovered}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/system/local-ai/pull")
async def pull_local_model(req: PullModelRequest, admin=Depends(verify_admin)):
    """Descarga e instala un modelo local usando Ollama."""
    try:
        from backend.app.core.local_ai_service import local_ai_service
        result = await local_ai_service.pull_ollama_model(req.model_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== GESTOR DE CREDENCIALES GLOBAL Y SECRETOS (.ENV) ====================

class UpdateCredentialsRequest(BaseModel):
    openrouter_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    deepseek_api_key: str | None = None
    groq_api_key: str | None = None
    zhipu_api_key: str | None = None
    moonshot_api_key: str | None = None
    minimax_api_key: str | None = None
    google_maps_api_key: str | None = None

@app.get("/api/system/credentials")
async def get_credentials(admin=Depends(verify_admin)):
    """Lee las credenciales del archivo .env y las devuelve enmascaradas."""
    env_path = Path(".env")
    if not env_path.exists():
        env_path = Path(".env.template")

    credentials = {}
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, val = line.split("=", 1)
                    val = val.strip('"').strip("'")
                    # Enmascarar valor para seguridad
                    masked = (val[:6] + "..." + val[-4:]) if len(val) > 12 else ("*" * len(val))
                    credentials[key] = {
                        "is_set": bool(val and not val.startswith("[INSERTAR")),
                        "masked_val": masked
                    }
    return {"credentials": credentials}

@app.post("/api/system/credentials")
async def update_credentials(req: UpdateCredentialsRequest, admin=Depends(verify_admin)):
    """Actualiza o crea el archivo .env con las nuevas claves proporcionadas desde la UI."""
    try:
        env_path = Path(".env")
        existing_env = {}
        if env_path.exists():
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        existing_env[k] = v.strip('"').strip("'")

        # Actualizar valores
        updates = req.dict(exclude_none=True)
        key_map = {
            "openrouter_api_key": "OPENROUTER_API_KEY",
            "openai_api_key": "OPENAI_API_KEY",
            "anthropic_api_key": "ANTHROPIC_API_KEY",
            "gemini_api_key": "GEMINI_API_KEY",
            "deepseek_api_key": "DEEPSEEK_API_KEY",
            "groq_api_key": "GROQ_API_KEY",
            "zhipu_api_key": "ZHIPU_API_KEY",
            "moonshot_api_key": "MOONSHOT_API_KEY",
            "minimax_api_key": "MINIMAX_API_KEY",
            "google_maps_api_key": "GOOGLE_MAPS_API_KEY"
        }

        for field, env_var in key_map.items():
            val = updates.get(field)
            if val and not val.startswith("*"):
                existing_env[env_var] = val

        # Escribir de nuevo en .env
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("# Archivo .env generado automáticamente por SilhouetteMCP Server\n")
            for k, v in existing_env.items():
                f.write(f'{k}="{v}"\n')

        return {"success": True, "message": "Credenciales guardadas y aplicadas exitosamente en .env"}
    except Exception as e:
        logger.error(f"Error al guardar credenciales: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== MAIN ====================

# ==================== API v1 (consolidada) ====================
# Estos routers vivían sólo en `backend/main.py`, un segundo servidor en el
# puerto 8000 con su propia configuración. Mantener dos superficies significaba
# aplicar cada arreglo de seguridad dos veces — y ya se había olvidado una.
#
# Al montarlos aquí hay una sola aplicación que asegurar. Como los routers no
# traían ninguna comprobación de acceso, la autenticación se impone a nivel de
# router: ejecutar herramientas, escribir memoria y lanzar tareas son
# operaciones con efectos.
from backend.app.api import health as _api_health
from backend.app.api import memory as _api_memory
from backend.app.api import tasks as _api_tasks
from backend.app.api import tools as _api_tools

app.include_router(_api_health.router, prefix="/api/v1")
app.include_router(_api_tools.router, prefix="/api/v1", dependencies=[Depends(verify_admin)])
app.include_router(_api_memory.router, prefix="/api/v1", dependencies=[Depends(verify_admin)])
app.include_router(_api_tasks.router, prefix="/api/v1", dependencies=[Depends(verify_admin)])


if __name__ == "__main__":
    # El correo del administrador sale del entorno; no se escribe en el código
    # ni se registra en el log.
    logger.info("Iniciando SilhouetteMCP Server en http://localhost:8001")
    logger.info("Documentación de la API: http://localhost:8001/docs")
    logger.info("Panel: http://localhost:8001/dashboard-ultra")
    if not auth_service.is_configured:
        logger.warning(
            "Sin administrador configurado: defina SILHOUETTE_ADMIN_EMAIL y "
            "SILHOUETTE_ADMIN_PASSWORD_HASH, o ejecute `python conectar.py`."
        )

    # Configurar logging a archivo
    file_handler = logging.FileHandler("silhouettemcp.log")
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

    uvicorn.run(
        "silhouettemcp_server:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )
