"""
Mock FastMCP Local para demo enterprise
Permite ejecutar demos sin dependencias externas
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import json


class MCPServerStatus(str, Enum):
    """Estados del servidor MCP"""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"


class ToolStatus(str, Enum):
    """Estados de herramientas"""
    AVAILABLE = "available"
    BUSY = "busy"
    ERROR = "error"


@dataclass
class Context:
    """Contexto de ejecución"""
    request_id: str
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ToolInputSchema:
    """Esquema de entrada de herramienta"""
    type: str = "object"
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


@dataclass
class Content:
    """Contenido de respuesta"""
    type: str
    text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class FastMCP:
    """Mock de FastMCP Server"""
    
    def __init__(self):
        self.tools = {}
        self.status = MCPServerStatus.STOPPED
        self.context = None
    
    def tool(self, name: str = None):
        """Decorator para registrar herramientas"""
        def decorator(func):
            tool_name = name or func.__name__
            self.tools[tool_name] = func
            return func
        return decorator
    
    async def start(self):
        """Iniciar servidor"""
        self.status = MCPServerStatus.RUNNING
    
    async def stop(self):
        """Detener servidor"""
        self.status = MCPServerStatus.STOPPED


def create_fastmcp_server():
    """Factory para crear servidor FastMCP"""
    return FastMCP()


def mock_fastmcp_imports():
    """Mock de importaciones FastMCP"""
    return {
        'FastMCP': FastMCP,
        'Context': Context,
        'MCPServerStatus': MCPServerStatus,
        'ToolStatus': ToolStatus,
        'Content': Content,
        'ToolInputSchema': ToolInputSchema
    }


# Clases adicionales requeridas
@dataclass
class InitializeRequest:
    """Request de inicialización"""
    protocolVersion: str
    capabilities: Dict[str, Any]
    clientInfo: Dict[str, Any]


@dataclass
class InitializeResult:
    """Resultado de inicialización"""
    protocolVersion: str
    capabilities: Dict[str, Any]
    serverInfo: Dict[str, Any]


@dataclass
class CallToolRequest:
    """Request de llamada a herramienta"""
    name: str
    arguments: Dict[str, Any]


@dataclass
class CallToolResult:
    """Resultado de llamada a herramienta"""
    content: list
    isError: bool = False


@dataclass
class Tool:
    """Definición de herramienta"""
    name: str
    description: str
    inputSchema: Dict[str, Any]


@dataclass
class ToolArguments:
    """Argumentos de herramienta"""
    arguments: Dict[str, Any]


@dataclass
class MCPCapabilities:
    """Capacidades MCP"""
    capabilities: Dict[str, Any]


@dataclass
class ClientInfo:
    """Información del cliente"""
    name: str
    version: str


@dataclass
class ServerInfo:
    """Información del servidor"""
    name: str
    version: str


class ToolHandler:
    """Handler de herramientas"""
    pass


# Auto-exportar todas las clases
__all__ = [
    'FastMCP', 'Context', 'InitializeRequest', 'InitializeResult',
    'CallToolRequest', 'CallToolResult', 'Tool', 'ToolInputSchema',
    'Content', 'ToolArguments', 'MCPCapabilities', 'ClientInfo',
    'ServerInfo', 'MCPServerStatus', 'ToolStatus', 'ToolHandler',
    'create_fastmcp_server', 'mock_fastmcp_imports'
]
