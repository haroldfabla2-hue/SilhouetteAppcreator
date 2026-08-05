import json
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
import random
import logging
import threading
import hashlib
import secrets
import re
import time
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import uvicorn

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IRISMetricsServer")

app = FastAPI(title="IRIS MCP Metrics Server", version="1.1.0")

# ✅ CORS configurado correctamente (no wildcard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # ✅ Específico
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Cache-Control"],
)

class PersistentMetricsStore:
    """Store persistente para métricas con backup automático"""
    
    def __init__(self, storage_file: str = "iris_metrics.json"):
        self.storage_file = Path(storage_file)
        self._backup_file = Path(f"{storage_file}.backup")
        self._data = self._load_persistent_data()
        self._lock = threading.Lock()
        self._save_buffer = deque(maxlen=10)  # ✅ Buffer de guardado
    
    def _load_persistent_data(self) -> Dict[str, Any]:
        """Cargar datos persistentes con validación"""
        try:
            if self.storage_file.exists():
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # ✅ Validar estructura de datos
                if not self._validate_data_structure(data):
                    self._restore_from_backup()
                    return self._create_default_data()
                
                return data
            
            return self._create_default_data()
            
        except Exception as e:
            logger.error(f"Error loading persistent data: {e}")
            return self._restore_from_backup()
    
    def _validate_data_structure(self, data: Dict[str, Any]) -> bool:
        """Validar estructura de datos persistente"""
        required_keys = ['agents', 'last_updated', 'version']
        return all(key in data for key in required_keys)
    
    def _restore_from_backup(self) -> Dict[str, Any]:
        """Restaurar desde backup en caso de corrupción"""
        try:
            if self._backup_file.exists():
                logger.info("Restoring from backup file")
                with open(self._backup_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error restoring from backup: {e}")
        
        logger.warning("Creating fresh data store")
        return self._create_default_data()
    
    def _create_default_data(self) -> Dict[str, Any]:
        """Crear datos por defecto"""
        return {
            "version": "1.1.0",
            "agents": {},
            "last_updated": datetime.now().isoformat(),
            "metrics_history": [],
            "system_stats": {
                "total_connections": 0,
                "requests_served": 0,
                "uptime_start": datetime.now().isoformat()
            }
        }
    
    def save_metrics(self, metrics: Dict[str, Any]):
        """Guardar métricas con backup automático"""
        with self._lock:
            try:
                # ✅ Crear backup antes de guardar
                if self.storage_file.exists():
                    self._copy_with_retry(self.storage_file, self._backup_file)
                
                # ✅ Guardar con escritura atómica
                temp_file = Path(f"{self.storage_file}.tmp")
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(metrics, f, indent=2, ensure_ascii=False)
                
                # ✅ Renombrar atómicamente
                temp_file.replace(self.storage_file)
                
                # ✅ Agregar a buffer de guardado
                self._save_buffer.append({
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                })
                
                logger.debug("Metrics saved successfully")
                
            except Exception as e:
                logger.error(f"Error saving metrics: {e}")
                # Limpiar archivo temporal en caso de error
                temp_file = Path(f"{self.storage_file}.tmp")
                if temp_file.exists():
                    temp_file.unlink()
                raise
    
    def _copy_with_retry(self, source: Path, destination: Path, max_retries: int = 3):
        """Copiar archivo con reintentos"""
        for attempt in range(max_retries):
            try:
                # ✅ Copia en chunks para archivos grandes
                with open(source, 'rb') as src, open(destination, 'wb') as dst:
                    while True:
                        chunk = src.read(8192)
                        if not chunk:
                            break
                        dst.write(chunk)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(0.1 * (attempt + 1))
    
    def get_data(self) -> Dict[str, Any]:
        """Obtener datos actuales"""
        return self._data.copy()
    
    def update_data(self, updates: Dict[str, Any]):
        """Actualizar datos de forma segura"""
        with self._lock:
            self._data.update(updates)
            self._data['last_updated'] = datetime.now().isoformat()

class IRISMetricsGenerator:
    """Generador de métricas con validación robusta"""
    
    def __init__(self, store: PersistentMetricsStore):
        self.store = store
        self.agents_data = {
            "sales_agent": {
                "id": "sales_agent",
                "agent": "Sales Agent",
                "status": "active",
                "tasksCompleted": 0,
                "avgResponseTime": 1.2,
                "tokenUsage": 0,
                "successRate": 0.94,
                "capabilities": ["lead_qualification", "proposal_generation", "follow_up_automation"]
            },
            "support_agent": {
                "id": "support_agent",
                "agent": "Support Agent",
                "status": "active",
                "tasksCompleted": 0,
                "avgResponseTime": 0.8,
                "tokenUsage": 0,
                "successRate": 0.96,
                "capabilities": ["ticket_classification", "response_generation", "escalation_management"]
            },
            "consulting_agent": {
                "id": "consulting_agent",
                "agent": "Consulting Agent",
                "status": "active",
                "tasksCompleted": 0,
                "avgResponseTime": 2.1,
                "tokenUsage": 0,
                "successRate": 0.91,
                "capabilities": ["data_analysis", "report_generation", "insight_generation"]
            }
        }
        
        self.base_tasks = {
            "sales_agent": 156,
            "support_agent": 89,
            "consulting_agent": 23
        }
        
        self.base_tokens = {
            "sales_agent": 45200,
            "support_agent": 32400,
            "consulting_agent": 67800
        }
        
        # ✅ Load persisted data
        persisted_data = self.store.get_data()
        if "agents" in persisted_data and persisted_data["agents"]:
            # Merge with persisted agent data
            for agent_id, agent_data in persisted_data["agents"].items():
                if agent_id in self.agents_data:
                    self.agents_data[agent_id].update(agent_data)

    def generate_metrics(self) -> Dict[str, Any]:
        """Generar métricas actuales con validación robusta"""
        current_time = datetime.now()
        
        agents = []
        total_tokens = 0
        total_tasks = 0
        
        for agent_id, agent_info in self.agents_data.items():
            try:
                # ✅ Validar datos del agente
                if not self._validate_agent_data(agent_info):
                    logger.warning(f"Invalid agent data for {agent_id}, using defaults")
                    agent_info = self._get_default_agent_data(agent_id)
                
                # Simular variaciones en métricas
                task_variance = random.randint(-5, 15)
                token_variance = random.randint(-1000, 3000)
                response_time_variance = random.uniform(-0.2, 0.4)
                
                updated_agent = agent_info.copy()
                updated_agent["tasksCompleted"] = self.base_tasks[agent_id] + task_variance
                updated_agent["tokenUsage"] = self.base_tokens[agent_id] + token_variance
                updated_agent["avgResponseTime"] = max(0.1, agent_info["avgResponseTime"] + response_time_variance)
                updated_agent["lastActivity"] = current_time.strftime("%Y-%m-%dT%H:%M:%S")
                
                # Simular estados ocasionales de error
                if random.random() < 0.05:  # 5% chance de error
                    updated_agent["status"] = "error"
                elif random.random() < 0.1:  # 10% chance de idle
                    updated_agent["status"] = "idle"
                else:
                    updated_agent["status"] = "active"
                
                # ✅ Validar valores finales
                updated_agent = self._validate_final_agent_data(updated_agent)
                    
                agents.append(updated_agent)
                total_tokens += updated_agent["tokenUsage"]
                total_tasks += updated_agent["tasksCompleted"]
                
                # Update stored data
                self.store.update_data({
                    f"agents.{agent_id}": {
                        "tasksCompleted": updated_agent["tasksCompleted"],
                        "tokenUsage": updated_agent["tokenUsage"],
                        "lastActivity": updated_agent["lastActivity"]
                    }
                })
                
            except Exception as e:
                logger.error(f"Error generating metrics for agent {agent_id}: {e}")
                # Use default data on error
                default_agent = self._get_default_agent_data(agent_id)
                agents.append(default_agent)
        
        metrics = {
            "timestamp": current_time.isoformat(),
            "agents": agents,
            "totalTokens": total_tokens,
            "totalTasks": total_tasks,
            "systemStatus": "operational",
            "version": "1.1.0"
        }
        
        # ✅ Save metrics persistently
        try:
            self.store.save_metrics(metrics)
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
        
        return metrics

    def _validate_agent_data(self, agent_data: Dict[str, Any]) -> bool:
        """Validar datos de agente"""
        required_fields = ['id', 'agent', 'status', 'tasksCompleted', 'avgResponseTime', 'tokenUsage', 'successRate']
        return all(field in agent_data for field in required_fields)

    def _get_default_agent_data(self, agent_id: str) -> Dict[str, Any]:
        """Obtener datos por defecto para un agente"""
        return {
            "id": agent_id,
            "agent": self.agents_data.get(agent_id, {}).get('agent', agent_id),
            "status": "active",
            "tasksCompleted": self.base_tasks.get(agent_id, 0),
            "avgResponseTime": 1.0,
            "tokenUsage": self.base_tokens.get(agent_id, 0),
            "successRate": 0.90,
            "capabilities": [],
            "lastActivity": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        }

    def _validate_final_agent_data(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validar y limpiar datos finales del agente"""
        # ✅ Sanitizar valores
        agent_data['tasksCompleted'] = max(0, int(agent_data['tasksCompleted']))
        agent_data['tokenUsage'] = max(0, int(agent_data['tokenUsage']))
        agent_data['avgResponseTime'] = max(0.1, float(agent_data['avgResponseTime']))
        agent_data['successRate'] = max(0.0, min(1.0, float(agent_data['successRate'])))
        
        # ✅ Validar status
        valid_statuses = ['active', 'idle', 'error', 'offline']
        if agent_data['status'] not in valid_statuses:
            agent_data['status'] = 'active'
        
        return agent_data

    def get_agent_details(self, agent_id: str) -> Dict[str, Any]:
        """Obtener detalles específicos de un agente"""
        if agent_id not in self.agents_data:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        agent_info = self.agents_data[agent_id].copy()
        agent_info["tasksCompleted"] = self.base_tasks.get(agent_id, 0)
        agent_info["tokenUsage"] = self.base_tokens.get(agent_id, 0)
        agent_info["lastActivity"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        
        # Agregar métricas adicionales
        agent_info["hourlyStats"] = self._generate_hourly_stats(agent_id)
        agent_info["recentTasks"] = self._generate_recent_tasks(agent_id)
        
        return agent_info

    def _generate_hourly_stats(self, agent_id: str) -> List[Dict[str, Any]]:
        """Generar estadísticas por hora para el agente"""
        stats = []
        current_time = datetime.now()
        
        for i in range(24):
            hour_time = current_time - timedelta(hours=23-i)
            stats.append({
                "hour": hour_time.strftime("%Y-%m-%dT%H:00:00"),
                "tasks": random.randint(10, 50),
                "tokens": random.randint(5000, 25000),
                "responseTime": round(random.uniform(0.5, 3.0), 1)
            })
        
        return stats

    def _generate_recent_tasks(self, agent_id: str) -> List[Dict[str, Any]]:
        """Generar lista de tareas recientes del agente"""
        tasks = []
        current_time = datetime.now()
        
        task_names = {
            "sales_agent": ["Lead Qualification", "Proposal Generation", "Follow-up Call", "Demo Setup"],
            "support_agent": ["Ticket Classification", "Customer Response", "Escalation Review", "Solution Documentation"],
            "consulting_agent": ["Data Analysis", "Report Generation", "Client Consultation", "Insight Generation"]
        }
        
        for i in range(10):
            task_time = current_time - timedelta(minutes=i*15)
            tasks.append({
                "id": f"{agent_id}_task_{i}",
                "name": random.choice(task_names.get(agent_id, ["General Task"])),
                "status": "completed" if i < 8 else "in_progress",
                "completedAt": task_time.strftime("%Y-%m-%dT%H:%M:%S") if i < 8 else None,
                "tokensUsed": random.randint(500, 5000)
            })
        
        return tasks

# ✅ Instancia global del store y generador con persistencia
metrics_store = PersistentMetricsStore()
metrics_generator = IRISMetricsGenerator(metrics_store)

class ConnectionManager:
    """Gestor de conexiones SSE con cleanup automático"""
    
    def __init__(self):
        self.active_connections = set()
        self.connection_stats = defaultdict(int)
        self._lock = threading.Lock()
    
    def add_connection(self, connection_id: str):
        """Agregar nueva conexión"""
        with self._lock:
            self.active_connections.add(connection_id)
            self.connection_stats[connection_id] = time.time()
    
    def remove_connection(self, connection_id: str):
        """Remover conexión"""
        with self._lock:
            self.active_connections.discard(connection_id)
    
    def get_active_count(self) -> int:
        """Obtener número de conexiones activas"""
        with self._lock:
            return len(self.active_connections)
    
    def cleanup_stale_connections(self, timeout: int = 300):
        """Limpiar conexiones stale"""
        current_time = time.time()
        stale_connections = []
        
        with self._lock:
            for conn_id, timestamp in list(self.connection_stats.items()):
                if current_time - timestamp > timeout:
                    stale_connections.append(conn_id)
        
        for conn_id in stale_connections:
            self.remove_connection(conn_id)
            del self.connection_stats[conn_id]
            logger.info(f"Cleaned up stale connection: {conn_id}")

connection_manager = ConnectionManager()

@app.get("/")
async def root():
    """Health check endpoint con información del sistema"""
    return {
        "message": "IRIS MCP Metrics Server",
        "version": "1.1.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "connections": connection_manager.get_active_count(),
        "features": ["persistent_storage", "robust_error_handling", "health_checks"]
    }

@app.get("/health")
async def health_check():
    """Health check detallado"""
    try:
        # ✅ Test métricas generator
        test_metrics = metrics_generator.generate_metrics()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "metrics_generator": "ok",
                "persistent_storage": "ok",
                "connections": f"{connection_manager.get_active_count()} active",
                "data_integrity": "ok" if test_metrics else "error"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )

@app.get("/agents")
async def get_agents():
    """Obtener lista de todos los agentes IRIS"""
    try:
        agents_list = []
        for agent_id, agent_info in metrics_generator.agents_data.items():
            agent_copy = agent_info.copy()
            agent_copy["tasksCompleted"] = metrics_generator.base_tasks.get(agent_id, 0)
            agent_copy["tokenUsage"] = metrics_generator.base_tokens.get(agent_id, 0)
            agent_copy["lastActivity"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            agents_list.append(agent_copy)
        
        return {"agents": agents_list}
    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agents")

@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Obtener detalles de un agente específico"""
    try:
        agent_details = metrics_generator.get_agent_details(agent_id)
        return agent_details
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve agent {agent_id}")

@app.get("/agents/{agent_id}/metrics")
async def get_agent_metrics(agent_id: str):
    """Obtener métricas detalladas de un agente específico"""
    try:
        agent_details = metrics_generator.get_agent_details(agent_id)
        return {
            "agent_id": agent_id,
            "metrics": {
                "tasks_completed": agent_details["tasksCompleted"],
                "avg_response_time": agent_details["avgResponseTime"],
                "token_usage": agent_details["tokenUsage"],
                "success_rate": agent_details["successRate"],
                "hourly_stats": agent_details["hourlyStats"],
                "recent_tasks": agent_details["recentTasks"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metrics for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics for agent {agent_id}")

@app.get("/metrics/stream")
async def metrics_stream(request: Request):
    """Stream de métricas en tiempo real (SSE) con gestión robusta"""
    connection_id = f"conn_{int(time.time() * 1000)}_{secrets.token_hex(4)}"
    connection_manager.add_connection(connection_id)
    
    logger.info(f"New SSE connection: {connection_id}")
    
    async def sse_generator():
        try:
            while True:
                # ✅ Cleanup stale connections periodically
                if random.random() < 0.01:  # 1% chance per iteration
                    connection_manager.cleanup_stale_connections()
                
                try:
                    # ✅ Generate metrics with error handling
                    metrics = metrics_generator.generate_metrics()
                    
                    # ✅ Update connection timestamp
                    connection_manager.connection_stats[connection_id] = time.time()
                    
                    # ✅ Format SSE data correctly
                    data = f"data: {json.dumps(metrics)}\n\n"
                    yield data
                    
                except Exception as e:
                    logger.error(f"Error generating metrics in SSE: {e}")
                    error_data = {
                        "error": "Failed to generate metrics",
                        "timestamp": datetime.now().isoformat(),
                        "version": "1.1.0"
                    }
                    yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
                    # ✅ Don't break the connection on metric generation errors
                
                await asyncio.sleep(2)  # Update every 2 seconds
                
        except asyncio.CancelledError:
            logger.info(f"SSE connection cancelled: {connection_id}")
            raise
        except Exception as e:
            logger.error(f"Unexpected SSE error for {connection_id}: {e}")
            error_data = {
                "event": "connection_error",
                "message": "Connection lost",
                "timestamp": datetime.now().isoformat()
            }
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
        finally:
            connection_manager.remove_connection(connection_id)
            logger.info(f"SSE connection closed: {connection_id}")
    
    # ✅ CORS headers configurados correctamente
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "http://localhost:3000",
        "Access-Control-Allow-Headers": "Cache-Control, Content-Type",
        "Access-Control-Allow-Credentials": "true"
    }
    
    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers=headers
    )

@app.get("/metrics/summary")
async def get_metrics_summary():
    """Obtener resumen de métricas del sistema"""
    try:
        current_metrics = metrics_generator.generate_metrics()
        
        # ✅ Calcular estadísticas con validación
        active_agents = len([a for a in current_metrics["agents"] if a["status"] == "active"])
        
        return {
            "timestamp": current_metrics["timestamp"],
            "summary": {
                "total_agents": len(current_metrics["agents"]),
                "active_agents": active_agents,
                "total_tasks": current_metrics["totalTasks"],
                "total_tokens": current_metrics["totalTokens"],
                "avg_response_time": round(
                    sum(a["avgResponseTime"] for a in current_metrics["agents"]) / len(current_metrics["agents"]), 2
                ),
                "system_health": "healthy" if active_agents > 0 else "warning",
                "connections_active": connection_manager.get_active_count()
            },
            "agents": current_metrics["agents"]
        }
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics summary")

@app.post("/agents/{agent_id}/deploy")
async def deploy_agent(agent_id: str):
    """Desplegar agente específico (simulado con validación)"""
    try:
        # ✅ Validar agent_id
        if not re.match(r'^[a-zA-Z0-9_-]+$', agent_id):
            raise HTTPException(status_code=400, detail="Invalid agent ID format")
        
        if agent_id not in metrics_generator.agents_data:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        # Simular proceso de despliegue
        await asyncio.sleep(1)
        
        # ✅ Update agent status
        metrics_generator.agents_data[agent_id]["status"] = "active"
        
        result = {
            "status": "deployed",
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "message": f"Agent {agent_id} deployed successfully"
        }
        
        logger.info(f"Agent deployed: {agent_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deploying agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to deploy agent {agent_id}")

@app.post("/agents/{agent_id}/stop")
async def stop_agent(agent_id: str):
    """Detener agente específico (simulado con validación)"""
    try:
        # ✅ Validar agent_id
        if not re.match(r'^[a-zA-Z0-9_-]+$', agent_id):
            raise HTTPException(status_code=400, detail="Invalid agent ID format")
        
        if agent_id not in metrics_generator.agents_data:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        # ✅ Update agent status
        metrics_generator.agents_data[agent_id]["status"] = "idle"
        
        result = {
            "status": "stopped",
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "message": f"Agent {agent_id} stopped successfully"
        }
        
        logger.info(f"Agent stopped: {agent_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop agent {agent_id}")

@app.get("/admin/stats")
async def get_admin_stats():
    """Estadísticas administrativas (solo para debugging)"""
    return {
        "connections": {
            "active": connection_manager.get_active_count(),
            "stats": dict(connection_manager.connection_stats)
        },
        "storage": {
            "data_size": len(json.dumps(metrics_store.get_data())),
            "backup_exists": metrics_store._backup_file.exists()
        },
        "version": "1.1.0"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Manejo global de excepciones"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat(),
            "version": "1.1.0"
        }
    )

if __name__ == "__main__":
    print("🚀 Iniciando IRIS MCP Metrics Server (v1.1.0)...")
    print("📊 Dashboard disponible en: http://localhost:3000")
    print("🔌 API disponible en: http://localhost:8000")
    print("📡 SSE Stream en: http://localhost:8000/metrics/stream")
    print("🔍 Health check: http://localhost:8000/health")
    print("⚡ Features: Persistent storage, Robust error handling, Health monitoring")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info",
        access_log=True
    )
