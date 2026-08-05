"""
FastMCP Local - Implementación Local del Framework FastMCP

Este módulo implementa una versión local y simplificada del framework FastMCP
para garantizar compatibilidad y funcionamiento sin dependencias externas.

Implementa las clases y funcionalidades necesarias para:
- FastMCP (clase principal del servidor)
- Context (contexto de request/response)
- Modelos de request/response (InitializeRequest, InitializeResult, etc.)
- Tipos MCP (CallToolRequest, CallToolResult, Tool)
- Decorador @mcp.tool para registro de herramientas
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Union, AsyncIterator
from datetime import datetime
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
import inspect
from functools import wraps
import traceback
import uuid


# === ENUMS Y CONSTANTES ===

class MCPServerStatus(Enum):
    """Estados del servidor MCP"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class ToolStatus(Enum):
    """Estados de herramientas"""
    AVAILABLE = "available"
    BUSY = "busy"
    ERROR = "error"
    DISABLED = "disabled"


# === MODELOS BASE ===

@dataclass
class MCPCapabilities:
    """Capacidades del servidor MCP"""
    tools: Dict[str, Any] = field(default_factory=dict)
    resources: Dict[str, Any] = field(default_factory=dict)
    prompts: Dict[str, Any] = field(default_factory=dict)
    logging: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ClientInfo:
    """Información del cliente MCP"""
    name: str
    version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"name": self.name}
        if self.version:
            result["version"] = self.version
        return result


@dataclass
class ServerInfo:
    """Información del servidor"""
    name: str
    version: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InitializeRequest:
    """Request de inicialización MCP"""
    protocolVersion: str
    capabilities: MCPCapabilities
    clientInfo: ClientInfo
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InitializeRequest':
        return cls(
            protocolVersion=data["protocolVersion"],
            capabilities=MCPCapabilities(**data.get("capabilities", {})),
            clientInfo=ClientInfo(**data["clientInfo"])
        )


@dataclass
class InitializeResult:
    """Result de inicialización MCP"""
    protocolVersion: str
    serverInfo: ServerInfo
    capabilities: MCPCapabilities
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "protocolVersion": self.protocolVersion,
            "serverInfo": self.serverInfo.to_dict(),
            "capabilities": self.capabilities.to_dict()
        }


@dataclass
class ToolInputSchema:
    """Schema de input de herramienta"""
    type: str = "object"
    properties: Dict[str, Any] = field(default_factory=dict)
    required: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Tool:
    """Definición de herramienta MCP"""
    name: str
    description: str
    inputSchema: ToolInputSchema
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.inputSchema.to_dict()
        }


@dataclass
class ToolArguments:
    """Argumentos de herramienta"""
    name: str
    arguments: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"name": self.name}
        if self.arguments:
            result["arguments"] = self.arguments
        return result


@dataclass
class Content:
    """Contenido de response"""
    type: str
    text: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CallToolRequest:
    """Request de llamada a herramienta"""
    params: ToolArguments
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CallToolRequest':
        return cls(params=ToolArguments(**data["params"]))


@dataclass
class CallToolResult:
    """Result de llamada a herramienta"""
    content: List[Content]
    isError: bool = False
    
    @classmethod
    def success(cls, content: List[Content]) -> 'CallToolResult':
        return cls(content=content, isError=False)
    
    @classmethod
    def error(cls, message: str) -> 'CallToolResult':
        return cls(
            content=[Content(type="text", text=message)],
            isError=True
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": [c.to_dict() for c in self.content],
            "isError": self.isError
        }


# === CLASE CONTEXT ===

class Context:
    """
    Contexto para requests MCP
    
    Proporciona información del contexto de la request actual,
    incluyendo cliente, capabilities, y metadata adicional.
    """
    
    def __init__(
        self,
        request: Union[InitializeRequest, CallToolRequest],
        client_info: Optional[ClientInfo] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.request = request
        self.client_info = client_info or ClientInfo(name="unknown")
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        self.request_id = str(uuid.uuid4())
    
    def get_client_capabilities(self) -> MCPCapabilities:
        """Obtener capabilities del cliente"""
        if isinstance(self.request, InitializeRequest):
            return self.request.capabilities
        return MCPCapabilities()
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Añadir metadata al contexto"""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Obtener metadata del contexto"""
        return self.metadata.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir contexto a dict para logging/debug"""
        return {
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "client_info": self.client_info.to_dict(),
            "metadata": self.metadata,
            "request_type": type(self.request).__name__
        }


# === CLASE TOOL HANDLER ===

class ToolHandler:
    """Manejador de herramienta MCP"""
    
    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        schema: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.description = description
        self.func = func
        self.schema = schema or self._generate_schema(func)
        self.status = ToolStatus.AVAILABLE
        self.call_count = 0
        self.error_count = 0
        self.last_called = None
        self.logger = logging.getLogger(f"mcp.tool.{name}")
    
    def _generate_schema(self, func: Callable) -> Dict[str, Any]:
        """Generar schema automáticamente desde la función"""
        try:
            sig = inspect.signature(func)
            properties = {}
            required = []
            
            for param_name, param in sig.parameters.items():
                if param_name in ['self', 'ctx', 'context']:
                    continue
                
                # Determinar tipo
                param_type = "string"
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == float:
                    param_type = "number"
                elif hasattr(param.annotation, '__origin__'):
                    param_type = "array"
                elif param.default != inspect.Parameter.empty:
                    param_type = param_type
                
                properties[param_name] = {
                    "type": param_type,
                    "description": f"Parameter {param_name}"
                }
                
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)
            
            return {
                "type": "object",
                "properties": properties,
                "required": required
            }
            
        except Exception as e:
            self.logger.warning(f"Error generando schema para {self.name}: {e}")
            return {
                "type": "object",
                "properties": {},
                "required": []
            }
    
    async def execute(self, arguments: Optional[Dict[str, Any]] = None) -> Any:
        """Ejecutar la herramienta"""
        self.call_count += 1
        self.last_called = datetime.now()
        self.status = ToolStatus.BUSY
        
        try:
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(**(arguments or {}))
            else:
                result = self.func(**(arguments or {}))
            
            self.status = ToolStatus.AVAILABLE
            return result
            
        except Exception as e:
            self.error_count += 1
            self.status = ToolStatus.ERROR
            self.logger.error(f"Error ejecutando herramienta {self.name}: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la herramienta"""
        return {
            "name": self.name,
            "status": self.status.value,
            "call_count": self.call_count,
            "error_count": self.error_count,
            "success_rate": (
                (self.call_count - self.error_count) / max(self.call_count, 1)
            ) * 100,
            "last_called": self.last_called.isoformat() if self.last_called else None
        }


# === CLASE FASTMCP PRINCIPAL ===

class FastMCP:
    """
    Servidor FastMCP Local Optimizado para Sistema Multi-Agente
    
    Implementación simplificada del framework FastMCP para funcionar
    sin dependencias externas. Optimizado para manejar 20+ agentes especializados.
    """
    
    def __init__(self, name: str = "MCP Server", max_concurrent_tools: int = 50):
        self.name = name
        self._tools: List[ToolHandler] = []
        self._tool_map: Dict[str, ToolHandler] = {}
        self.status = MCPServerStatus.STOPPED
        self.logger = logging.getLogger(f"mcp.server.{name}")
        self.request_count = 0
        self.error_count = 0
        self.start_time = None
        
        # Optimizaciones para multi-agente
        self.max_concurrent_tools = max_concurrent_tools
        self.active_execution_count = 0
        self.execution_semaphore = asyncio.Semaphore(max_concurrent_tools)
        self.performance_metrics: Dict[str, Any] = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "peak_concurrent_execution": 0,
            "tool_performance": {},
            "system_optimization_level": "enhanced"
        }
    
    def tool(self, name: Optional[str] = None, description: str = "", schema: Optional[Dict[str, Any]] = None):
        """
        Decorador para registrar herramientas MCP
        
        Args:
            name: Nombre de la herramienta (usa nombre de función si no se especifica)
            description: Descripción de la herramienta
            schema: Schema de input (se genera automáticamente si no se proporciona)
        """
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            tool_description = description or func.__doc__ or f"Tool {tool_name}"
            
            handler = ToolHandler(tool_name, tool_description, func, schema)
            
            # Registrar herramienta
            self._tools.append(handler)
            self._tool_map[tool_name] = handler
            
            self.logger.debug(f"Herramienta registrada: {tool_name}")
            
            return func
        
        return decorator
    
    def get_tools(self) -> List[Tool]:
        """Obtener lista de herramientas como Tool objects"""
        tools = []
        for handler in self._tools:
            tool = Tool(
                name=handler.name,
                description=handler.description,
                inputSchema=ToolInputSchema(**handler.schema)
            )
            tools.append(tool)
        return tools
    
    async def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None, timeout: float = 30.0) -> CallToolResult:
        """Ejecutar herramienta por nombre con optimizaciones multi-agente"""
        start_time = datetime.now()
        self.request_count += 1
        self.performance_metrics["total_requests"] += 1
        
        # Control de concurrencia con semaforo
        async with self.execution_semaphore:
            self.active_execution_count += 1
            
            # Actualizar peak concurrent execution
            if self.active_execution_count > self.performance_metrics["peak_concurrent_execution"]:
                self.performance_metrics["peak_concurrent_execution"] = self.active_execution_count
        
        try:
            if name not in self._tool_map:
                error_msg = f"Herramienta '{name}' no encontrada"
                self._update_performance_metrics(name, False, 0)
                return CallToolResult.error(error_msg)
            
            handler = self._tool_map[name]
            
            # Ejecutar con timeout
            try:
                result = await asyncio.wait_for(
                    handler.execute(arguments),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                error_msg = f"Herramienta '{name}' timeout después de {timeout} segundos"
                self.logger.error(error_msg)
                self._update_performance_metrics(name, False, timeout)
                return CallToolResult.error(error_msg)
            
            # Calcular tiempo de ejecución
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Formatear resultado con métricas
            if isinstance(result, dict):
                result["_execution_metrics"] = {
                    "execution_time": execution_time,
                    "agent_type": getattr(handler, 'agent_type', 'unknown'),
                    "success": True,
                    "tool_name": name
                }
                content = [Content(
                    type="text",
                    text=f"```json\n{json.dumps(result, indent=2)}\n```"
                )]
            elif isinstance(result, str):
                content = [Content(type="text", text=result)]
            else:
                content = [Content(type="text", text=str(result))]
            
            # Actualizar métricas de performance
            self._update_performance_metrics(name, True, execution_time)
            self.performance_metrics["successful_requests"] += 1
            
            return CallToolResult.success(content)
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.error_count += 1
            self.performance_metrics["failed_requests"] += 1
            
            error_msg = f"Error ejecutando herramienta '{name}': {str(e)}\n{traceback.format_exc()}"
            self.logger.error(error_msg)
            
            # Actualizar métricas de fallo
            self._update_performance_metrics(name, False, execution_time)
            
            return CallToolResult.error(error_msg)
        
        finally:
            self.active_execution_count = max(0, self.active_execution_count - 1)
    
    def _update_performance_metrics(self, tool_name: str, success: bool, execution_time: float) -> None:
        """Actualizar métricas de performance de herramienta específica"""
        if tool_name not in self.performance_metrics["tool_performance"]:
            self.performance_metrics["tool_performance"][tool_name] = {
                "call_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "total_execution_time": 0.0,
                "average_execution_time": 0.0,
                "success_rate": 0.0
            }
        
        metrics = self.performance_metrics["tool_performance"][tool_name]
        metrics["call_count"] += 1
        metrics["total_execution_time"] += execution_time
        
        if success:
            metrics["success_count"] += 1
        else:
            metrics["failure_count"] += 1
        
        # Recalcular promedios
        metrics["average_execution_time"] = metrics["total_execution_time"] / metrics["call_count"]
        metrics["success_rate"] = metrics["success_count"] / metrics["call_count"]
        
        # Actualizar promedio global
        total_successful = self.performance_metrics["successful_requests"]
        total_requests = self.performance_metrics["total_requests"]
        if total_requests > 0:
            self.performance_metrics["average_response_time"] = sum(
                tool["average_execution_time"] * tool["call_count"]
                for tool in self.performance_metrics["tool_performance"].values()
            ) / total_requests
    
    async def batch_execute_tools(
        self, 
        tool_calls: List[Dict[str, Any]], 
        parallel: bool = True,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """Ejecutar múltiples herramientas en batch con optimizaciones"""
        
        if not tool_calls:
            return {"results": [], "success": False, "error": "No tool calls provided"}
        
        self.logger.info(f"Ejecutando {len(tool_calls)} herramientas en batch")
        
        if parallel:
            # Ejecución paralela con control de concurrencia
            semaphore = asyncio.Semaphore(self.max_concurrent_tools)
            
            async def execute_with_semaphore(tool_call):
                async with semaphore:
                    return await self.call_tool(
                        tool_call["name"],
                        tool_call.get("arguments"),
                        timeout
                    )
            
            results = await asyncio.gather(*[
                execute_with_semaphore(tool_call) for tool_call in tool_calls
            ], return_exceptions=True)
            
        else:
            # Ejecución secuencial
            results = []
            for tool_call in tool_calls:
                try:
                    result = await self.call_tool(
                        tool_call["name"],
                        tool_call.get("arguments"),
                        timeout
                    )
                    results.append(result)
                except Exception as e:
                    results.append(CallToolResult.error(f"Batch execution error: {str(e)}"))
        
        # Procesar resultados
        processed_results = []
        success_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "tool_index": i,
                    "success": False,
                    "error": str(result)
                })
            elif hasattr(result, 'isError'):
                processed_results.append({
                    "tool_index": i,
                    "success": not result.isError,
                    "content": result.content if not result.isError else None,
                    "error": result.content[0].text if result.isError else None
                })
                if not result.isError:
                    success_count += 1
            else:
                processed_results.append({
                    "tool_index": i,
                    "success": False,
                    "error": "Unexpected result type"
                })
        
        return {
            "batch_id": str(uuid.uuid4()),
            "total_tools": len(tool_calls),
            "successful_tools": success_count,
            "failed_tools": len(tool_calls) - success_count,
            "success_rate": success_count / len(tool_calls),
            "results": processed_results,
            "execution_mode": "parallel" if parallel else "sequential"
        }
    
    async def get_optimization_recommendations(self) -> Dict[str, Any]:
        """Obtener recomendaciones de optimización para el sistema"""
        recommendations = []
        alerts = []
        
        # Analizar métricas de performance
        metrics = self.performance_metrics
        
        # Verificar tasa de éxito
        total_requests = metrics["total_requests"]
        if total_requests > 10:
            success_rate = metrics["successful_requests"] / total_requests
            if success_rate < 0.8:
                recommendations.append("Considerar revisar herramientas con alta tasa de fallo")
                alerts.append(f"Tasa de éxito baja: {success_rate:.1%}")
        
        # Verificar concurrencia
        current_concurrent = self.active_execution_count
        max_concurrent = self.max_concurrent_tools
        if current_concurrent > max_concurrent * 0.8:
            recommendations.append("Alta concurrencia detectada - considerar aumentar max_concurrent_tools")
        
        # Verificar herramientas específicas
        for tool_name, tool_metrics in metrics["tool_performance"].items():
            if tool_metrics["call_count"] > 5:
                if tool_metrics["average_execution_time"] > 10.0:
                    recommendations.append(f"Tool '{tool_name}' tiene tiempo de ejecución alto: {tool_metrics['average_execution_time']:.2f}s")
                
                if tool_metrics["success_rate"] < 0.7:
                    alerts.append(f"Tool '{tool_name}' tiene baja tasa de éxito: {tool_metrics['success_rate']:.1%}")
        
        # Verificar recursos del sistema
        import psutil
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            if cpu_percent > 80:
                alerts.append(f"Alto uso de CPU: {cpu_percent:.1f}%")
            
            if memory.percent > 80:
                alerts.append(f"Alto uso de memoria: {memory.percent:.1f}%")
                
        except Exception:
            # psutil no disponible, omitir estas verificaciones
            pass
        
        return {
            "recommendations": recommendations,
            "alerts": alerts,
            "system_health": "healthy" if not alerts else "degraded",
            "optimization_level": metrics["system_optimization_level"]
        }
    
    async def list_tools(self) -> List[Tool]:
        """Listar herramientas disponibles"""
        return self.get_tools()
    
    def get_server_info(self) -> ServerInfo:
        """Obtener información del servidor"""
        return ServerInfo(
            name=self.name,
            version="1.0.0-local"
        )
    
    def get_server_status(self) -> Dict[str, Any]:
        """Obtener estado del servidor"""
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "name": self.name,
            "status": self.status.value,
            "uptime_seconds": uptime,
            "tools_count": len(self._tools),
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": (self.error_count / max(self.request_count, 1)) * 100,
            "tools": [handler.get_stats() for handler in self._tools]
        }
    
    async def start(self) -> None:
        """Iniciar servidor"""
        self.status = MCPServerStatus.STARTING
        self.start_time = datetime.now()
        self.status = MCPServerStatus.RUNNING
        self.logger.info(f"Servidor MCP iniciado: {self.name} con {len(self._tools)} herramientas")
    
    async def stop(self) -> None:
        """Detener servidor"""
        self.status = MCPServerStatus.STOPPING
        # Cleanup si es necesario
        self.status = MCPServerStatus.STOPPED
        self.logger.info(f"Servidor MCP detenido: {self.name}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check del servidor"""
        status = "healthy"
        issues = []
        
        if self.status != MCPServerStatus.RUNNING:
            status = "unhealthy"
            issues.append(f"Servidor en estado: {self.status.value}")
        
        # Verificar herramientas con errores
        error_tools = [h for h in self._tools if h.status == ToolStatus.ERROR]
        if error_tools:
            status = "degraded"
            issues.append(f"{len(error_tools)} herramientas con errores")
        
        # Verificar tasa de errores
        if self.request_count > 0:
            error_rate = (self.error_count / self.request_count) * 100
            if error_rate > 50:
                status = "unhealthy"
                issues.append(f"Tasa de errores muy alta: {error_rate:.1f}%")
        
        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "issues": issues,
            "server": self.get_server_status()
        }


# === FACTORY FUNCTIONS ===

def create_fastmcp_server(name: str = "MCP Server") -> FastMCP:
    """Crear instancia de servidor FastMCP"""
    return FastMCP(name)


def mock_fastmcp_imports():
    """Función para configurar mocks de FastMCP en tests"""
    import sys
    from unittest.mock import MagicMock
    
    # Mock del módulo fastmcp
    fastmcp_mock = MagicMock()
    fastmcp_mock.FastMCP = FastMCP
    fastmcp_mock.server = MagicMock()
    fastmcp_mock.server.Context = Context
    fastmcp_mock.server.models = MagicMock()
    fastmcp_mock.server.models.InitializeRequest = InitializeRequest
    fastmcp_mock.server.models.InitializeResult = InitializeResult
    fastmcp_mock.types = MagicMock()
    fastmcp_mock.types.CallToolRequest = CallToolRequest
    fastmcp_mock.types.CallToolResult = CallToolResult
    fastmcp_mock.types.Tool = Tool
    
    sys.modules['fastmcp'] = fastmcp_mock
    sys.modules['fastmcp.server'] = fastmcp_mock.server
    sys.modules['fastmcp.server.models'] = fastmcp_mock.server.models
    sys.modules['fastmcp.types'] = fastmcp_mock.types
    
    return fastmcp_mock


# === EXPORTS ===

__all__ = [
    # Clases principales
    'FastMCP',
    'Context',
    'InitializeRequest',
    'InitializeResult',
    'CallToolRequest',
    'CallToolResult',
    'Tool',
    'ToolInputSchema',
    'Content',
    'ToolArguments',
    'MCPCapabilities',
    'ClientInfo',
    'ServerInfo',
    
    # Enums
    'MCPServerStatus',
    'ToolStatus',
    
    # Clases internas
    'ToolHandler',
    
    # Factories
    'create_fastmcp_server',
    'mock_fastmcp_imports'
]


# === EJEMPLO DE USO ===

if __name__ == "__main__":
    async def main():
        # Crear servidor
        server = FastMCP("Mi Servidor MCP")
        
        # Registrar herramientas
        @server.tool(description="Suma dos números")
        def suma(a: int, b: int) -> int:
            return a + b
        
        @server.tool(description="Obtener info del servidor")
        def get_info() -> Dict[str, Any]:
            return {
                "servidor": server.name,
                "herramientas": len(server._tools),
                "timestamp": datetime.now().isoformat()
            }
        
        # Iniciar servidor
        await server.start()
        
        # Listar herramientas
        tools = await server.list_tools()
        print(f"Heramientas disponibles: {len(tools)}")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")
        
        # Ejecutar herramienta
        result = await server.call_tool("suma", {"a": 5, "b": 3})
        print(f"Resultado: {result.content[0].text}")
        
        # Estado del servidor
        status = server.get_server_status()
        print(f"Estado: {json.dumps(status, indent=2)}")
        
        # Health check
        health = await server.health_check()
        print(f"Health: {json.dumps(health, indent=2)}")
        
        await server.stop()
    
    asyncio.run(main())