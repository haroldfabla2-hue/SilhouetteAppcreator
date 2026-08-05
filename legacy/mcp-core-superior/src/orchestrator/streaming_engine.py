"""
Motor de Streaming SSE para tiempo real
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, AsyncIterator
from datetime import datetime
from enum import Enum

from ..core.exceptions import StreamingException


class StreamEventType(str, Enum):
    """Tipos de eventos de streaming"""
    TASK_UPDATE = "task_update"
    AGENT_STATUS = "agent_status"
    PROGRESS = "progress"
    COMPLETE = "complete"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class StreamEvent:
    """Evento de streaming"""
    
    def __init__(self, event_type: StreamEventType, data: Dict[str, Any]):
        self.event_type = event_type
        self.data = data
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            "type": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp
        }


class StreamingEngine:
    """Motor de streaming SSE"""
    
    def __init__(self):
        self.logger = logging.getLogger("mcp.orchestrator.streaming")
        self.active_streams: Dict[str, Dict[str, Any]] = {}
        self.is_initialized = False
        self.stream_counter = 0
    
    async def initialize(self) -> None:
        """Inicializar motor de streaming"""
        self.is_initialized = True
        self.logger.info("StreamingEngine inicializado")
    
    async def cleanup(self) -> None:
        """Limpiar motor de streaming"""
        # Cerrar streams activos
        for stream_id in list(self.active_streams.keys()):
            await self.close_stream(stream_id)
        
        self.is_initialized = False
        self.logger.info("StreamingEngine limpiado")
    
    async def create_stream(self, task_id: str, duration: int = 300) -> str:
        """Crear nuevo stream"""
        if not self.is_initialized:
            raise StreamingException("StreamingEngine no inicializado", "unknown")
        
        self.stream_counter += 1
        stream_id = f"stream_{self.stream_counter}"
        
        self.active_streams[stream_id] = {
            "stream_id": stream_id,
            "task_id": task_id,
            "created_at": datetime.now(),
            "duration": duration,
            "active": True,
            "subscribers": []
        }
        
        self.logger.info(f"Stream creado: {stream_id} para tarea {task_id}")
        return stream_id
    
    async def close_stream(self, stream_id: str) -> None:
        """Cerrar stream"""
        if stream_id in self.active_streams:
            self.active_streams[stream_id]["active"] = False
            del self.active_streams[stream_id]
            self.logger.info(f"Stream cerrado: {stream_id}")
    
    async def emit_event(self, stream_id: str, event: StreamEvent) -> None:
        """Emitir evento a stream"""
        if stream_id not in self.active_streams:
            self.logger.warning(f"Stream no encontrado: {stream_id}")
            return
        
        stream = self.active_streams[stream_id]
        if not stream["active"]:
            return
        
        # Agregar evento a cola del stream
        if "events" not in stream:
            stream["events"] = asyncio.Queue()
        
        await stream["events"].put(event)
        
        self.logger.debug(f"Evento emitido a stream {stream_id}: {event.event_type.value}")
    
    async def get_stream_events(self, stream_id: str, timeout: float = 1.0) -> Optional[StreamEvent]:
        """Obtener siguiente evento del stream"""
        if stream_id not in self.active_streams:
            return None
        
        stream = self.active_streams[stream_id]
        if not stream["active"] or "events" not in stream:
            return None
        
        try:
            event = await asyncio.wait_for(stream["events"].get(), timeout=timeout)
            return event
        except asyncio.TimeoutError:
            return None
    
    async def stream_task_updates(self, task_id: str) -> AsyncIterator[str]:
        """Stream de updates de tarea"""
        stream_id = await self.create_stream(task_id)
        
        try:
            while stream_id in self.active_streams:
                event = await self.get_stream_events(stream_id)
                
                if event:
                    yield f"data: {json.dumps(event.to_dict())}\\n\\n"
                else:
                    # Enviar heartbeat si no hay eventos
                    heartbeat = StreamEvent(
                        StreamEventType.HEARTBEAT,
                        {"task_id": task_id, "message": "Alive"}
                    )
                    yield f"data: {json.dumps(heartbeat.to_dict())}\\n\\n"
                    
                await asyncio.sleep(1.0)  # Frecuencia de 1 segundo
                
        except asyncio.CancelledError:
            self.logger.info(f"Stream cancelado para tarea {task_id}")
        except Exception as e:
            self.logger.error(f"Error en stream para tarea {task_id}: {e}")
            error_event = StreamEvent(
                StreamEventType.ERROR,
                {"task_id": task_id, "error": str(e)}
            )
            yield f"data: {json.dumps(error_event.to_dict())}\\n\\n"
        finally:
            await self.close_stream(stream_id)
    
    async def notify_task_update(self, task_id: str, status: str, phase: str, progress: float, message: str):
        """Notificar update de tarea a todos los streams asociados"""
        event = StreamEvent(
            StreamEventType.TASK_UPDATE,
            {
                "task_id": task_id,
                "status": status,
                "phase": phase,
                "progress": progress,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Emitir a todos los streams de esta tarea
        for stream_id, stream in self.active_streams.items():
            if stream["task_id"] == task_id and stream["active"]:
                await self.emit_event(stream_id, event)
    
    async def notify_agent_status(self, agent_name: str, status_data: Dict[str, Any]):
        """Notificar cambio de estado de agente"""
        event = StreamEvent(
            StreamEventType.AGENT_STATUS,
            {
                "agent_name": agent_name,
                "status_data": status_data,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Emitir a todos los streams activos
        for stream_id, stream in self.active_streams.items():
            if stream["active"]:
                await self.emit_event(stream_id, event)
    
    async def get_status(self) -> Dict[str, Any]:
        """Obtener estado del motor de streaming"""
        return {
            "is_initialized": self.is_initialized,
            "active_streams": len(self.active_streams),
            "total_streams_created": self.stream_counter
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check del motor de streaming"""
        return {
            "status": "healthy" if self.is_initialized else "not_initialized",
            "is_initialized": self.is_initialized,
            "active_streams": len(self.active_streams),
            "components": {
                "event_emitter": "healthy",
                "stream_manager": "healthy"
            }
        }
