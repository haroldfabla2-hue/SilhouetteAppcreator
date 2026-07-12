#!/usr/bin/env python3
"""
SilhouetteMCP WebSocket System - Sistema WebSocket
Puerto 8006: Comunicación en tiempo real para SilhouetteMCP
"""

import json
import time
import logging
import asyncio
import psutil
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Set
import uvicorn

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="SilhouetteMCP WebSocket System",
    description="Sistema WebSocket para comunicación en tiempo real",
    version="1.0.0"
)

class ConnectionManager:
    """Gestor de conexiones WebSocket"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_history: List[Dict] = []
        
    async def connect(self, websocket: WebSocket):
        """Aceptar conexión WebSocket"""
        await websocket.accept()
        self.active_connections.add(websocket)
        connection_info = {
            "connection_id": id(websocket),
            "connected_at": datetime.now().isoformat(),
            "status": "connected"
        }
        self.connection_history.append(connection_info)
        logger.info(f"WebSocket conectado: {connection_info['connection_id']}")
        return connection_info
        
    def disconnect(self, websocket: WebSocket):
        """Desconectar WebSocket"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket desconectado: {id(websocket)}")
            
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Enviar mensaje personal"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error enviando mensaje personal: {e}")
            self.disconnect(websocket)
            
    async def broadcast(self, message: dict):
        """Enviar mensaje a todas las conexiones activas"""
        if not self.active_connections:
            return
            
        disconnected = set()
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error en broadcast: {e}")
                disconnected.add(connection)
                
        # Limpiar conexiones desconectadas
        for connection in disconnected:
            self.disconnect(connection)

class SystemMonitor:
    """Monitor del sistema en tiempo real"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.monitoring = False
        self.monitor_task = None
        
    def collect_realtime_metrics(self) -> Dict[str, Any]:
        """Recolecta métricas en tiempo real"""
        try:
            return {
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "network_connections": len(psutil.net_connections()),
                "process_count": len(psutil.pids()),
                "boot_time": psutil.boot_time()
            }
        except Exception as e:
            logger.error(f"Error collecting realtime metrics: {e}")
            return {"error": str(e)}
            
    async def start_monitoring(self):
        """Iniciar monitoreo en tiempo real"""
        self.monitoring = True
        logger.info("🚀 Iniciando monitoreo WebSocket en tiempo real")
        
        while self.monitoring:
            try:
                metrics = self.collect_realtime_metrics()
                status_message = {
                    "type": "system_update",
                    "data": metrics
                }
                await self.connection_manager.broadcast(status_message)
                await asyncio.sleep(2)  # Actualizar cada 2 segundos
            except Exception as e:
                logger.error(f"Error en monitoreo: {e}")
                await asyncio.sleep(5)
                
    def stop_monitoring(self):
        """Detener monitoreo"""
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()

# Instancias globales
connection_manager = ConnectionManager()
system_monitor = SystemMonitor(connection_manager)

# Rutas de la API

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": "SilhouetteMCP WebSocket System",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "WebSocket connections",
            "Real-time system monitoring",
            "Broadcast messaging",
            "Connection management"
        ]
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(connection_manager.active_connections),
        "connection_history": len(connection_manager.connection_history)
    }

@app.get("/connections")
async def get_connections():
    """Obtener información de conexiones activas"""
    return {
        "active_connections": len(connection_manager.active_connections),
        "connection_history": connection_manager.connection_history[-10:],  # Últimas 10
        "timestamp": datetime.now().isoformat()
    }

@app.get("/metrics")
async def get_realtime_metrics():
    """Obtener métricas en tiempo real"""
    return system_monitor.collect_realtime_metrics()

@app.post("/broadcast")
async def broadcast_message(message: Dict[str, Any]):
    """Enviar mensaje de broadcast a todas las conexiones"""
    try:
        message["timestamp"] = datetime.now().isoformat()
        message["type"] = "broadcast"
        await connection_manager.broadcast(message)
        return {"status": "broadcast_sent", "recipients": len(connection_manager.active_connections)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket principal"""
    connection_info = await connection_manager.connect(websocket)
    
    try:
        # Enviar mensaje de bienvenida
        welcome_message = {
            "type": "welcome",
            "message": "Conectado al sistema WebSocket SilhouetteMCP",
            "connection_id": connection_info["connection_id"],
            "timestamp": datetime.now().isoformat(),
            "system_info": {
                "active_systems": "SilhouetteMCP V5.0.0",
                "monitoring_available": True
            }
        }
        await connection_manager.send_personal_message(welcome_message, websocket)
        
        # Enviar métricas iniciales
        initial_metrics = {
            "type": "initial_metrics",
            "data": system_monitor.collect_realtime_metrics()
        }
        await connection_manager.send_personal_message(initial_metrics, websocket)
        
        # Mantener conexión activa y procesar mensajes
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type", "unknown")
                
                if message_type == "ping":
                    # Responder a ping
                    await connection_manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                    
                elif message_type == "request_metrics":
                    # Enviar métricas bajo demanda
                    metrics = system_monitor.collect_realtime_metrics()
                    await connection_manager.send_personal_message({
                        "type": "metrics_response",
                        "data": metrics
                    }, websocket)
                    
                elif message_type == "broadcast":
                    # Reenviar mensaje como broadcast
                    broadcast_msg = {
                        "type": "broadcast",
                        "from": connection_info["connection_id"],
                        "message": message.get("message", ""),
                        "timestamp": datetime.now().isoformat()
                    }
                    await connection_manager.broadcast(broadcast_msg)
                    
                else:
                    # Echo de mensaje desconocido
                    await connection_manager.send_personal_message({
                        "type": "echo",
                        "original_message": message,
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                    
            except json.JSONDecodeError:
                await connection_manager.send_personal_message({
                    "type": "error",
                    "message": "Mensaje JSON inválido",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket desconectado: {connection_info['connection_id']}")
    except Exception as e:
        logger.error(f"Error en WebSocket: {e}")
    finally:
        connection_manager.disconnect(websocket)

@app.on_event("startup")
async def startup_event():
    """Evento de inicio"""
    logger.info("🚀 Iniciando SilhouetteMCP WebSocket System")
    # Iniciar monitoreo en segundo plano
    system_monitor.monitor_task = asyncio.create_task(system_monitor.start_monitoring())

@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre"""
    logger.info("🛑 Cerrando SilhouetteMCP WebSocket System")
    system_monitor.stop_monitoring()
    # Cerrar todas las conexiones
    for connection in list(connection_manager.active_connections):
        await connection.close()

if __name__ == "__main__":
    logger.info("🚀 Iniciando SilhouetteMCP WebSocket System en puerto 8006")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8006,
        log_level="info",
        access_log=True
    )