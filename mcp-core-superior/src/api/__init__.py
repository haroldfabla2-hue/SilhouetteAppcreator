"""
MCP Core Superior - API Module
APIs REST complementarias
"""

from .tasks import router as tasks_router
from .streaming import router as streaming_router
from .agents import router as agents_router

__all__ = [
    "tasks_router",
    "streaming_router", 
    "agents_router"
]
