"""
Integración con TaskManager para streaming
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..core.exceptions import MCPCoreException


class TaskIntegrationManager:
    """Manager de integración con TaskManager"""
    
    def __init__(self):
        self.logger = logging.getLogger("mcp.orchestrator.task_integration")
        self.task_progress_callbacks: Dict[str, list] = {}
    
    async def register_progress_callback(self, task_id: str, callback):
        """Registrar callback de progreso"""
        if task_id not in self.task_progress_callbacks:
            self.task_progress_callbacks[task_id] = []
        self.task_progress_callbacks[task_id].append(callback)
    
    async def notify_progress(self, task_id: str, phase: str, progress: float, message: str):
        """Notificar progreso a callbacks"""
        if task_id in self.task_progress_callbacks:
            for callback in self.task_progress_callbacks[task_id]:
                try:
                    await callback(task_id, phase, progress, message)
                except Exception as e:
                    self.logger.error(f"Error en callback de progreso: {e}")
    
    async def cleanup(self) -> None:
        """Limpiar callbacks"""
        self.task_progress_callbacks.clear()
