"""
MCP Core Superior - Servidor Principal
Punto de entrada para el servidor MCP usando FastMCP
"""
import asyncio
import logging
import signal
import sys
from typing import Optional
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.fastmcp_local import FastMCP, Context, InitializeRequest, InitializeResult, CallToolRequest, CallToolResult, Tool

from src.core.fastmcp_server import create_mcp_server
from src.core.config import settings, get_environment_config
from src.utils.logging_config import setup_logging


class MCPProtocolServer:
    """
    Servidor MCP Protocol que integra con FastMCP
    """
    
    def __init__(self):
        self.logger = logging.getLogger("mcp.protocol.server")
        self.server = create_mcp_server()
        self.is_running = False
    
    async def initialize(self, request: InitializeRequest) -> InitializeResult:
        """Manejar request de inicialización"""
        self.logger.info(f"Inicializando servidor MCP para cliente: {request.client_info.name}")
        
        await self.server.start()
        
        return InitializeResult(
            protocolVersion="2024-11-05",
            serverInfo={
                "name": "MCP Core Superior",
                "version": settings.app_version
            },
            capabilities={
                "tools": {"listChanged": True},
                "resources": {"listChanged": True},
                "prompts": {"listChanged": True},
                "logging": {}
            }
        )
    
    async def list_tools(self) -> list[Tool]:
        """Listar herramientas disponibles"""
        tools = []
        
        try:
            # Obtener herramientas del servidor interno
            internal_tools = self.server.mcp._tools
            
            for tool in internal_tools:
                tools.append(Tool(
                    name=tool.name,
                    description=tool.description,
                    inputSchema=tool.inputSchema
                ))
            
            self.logger.info(f"Listando {len(tools)} herramientas MCP")
            
        except Exception as e:
            self.logger.error(f"Error listando herramientas: {e}")
            tools = []
        
        return tools
    
    async def call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Ejecutar herramienta MCP"""
        tool_name = request.params.name
        arguments = request.params.arguments or {}
        
        self.logger.info(f"Ejecutando herramienta: {tool_name}")
        
        try:
            # Obtener herramienta del servidor interno
            internal_tool = None
            for tool in self.server.mcp._tools:
                if tool.name == tool_name:
                    internal_tool = tool
                    break
            
            if internal_tool is None:
                return CallToolResult(
                    content=[
                        {
                            "type": "text",
                            "text": f"Tool '{tool_name}' not found"
                        }
                    ],
                    isError=True
                )
            
            # Ejecutar herramienta
            result = await internal_tool.handler(arguments)
            
            # Formatear resultado
            if isinstance(result, dict):
                content = [{
                    "type": "text",
                    "text": f"```json\\n{str(result)}\\n```"
                }]
            else:
                content = [{
                    "type": "text",
                    "text": str(result)
                }]
            
            return CallToolResult(content=content, isError=False)
            
        except Exception as e:
            self.logger.error(f"Error ejecutando herramienta {tool_name}: {e}")
            
            return CallToolResult(
                content=[
                    {
                        "type": "text",
                        "text": f"Error executing tool '{tool_name}': {str(e)}"
                    }
                ],
                isError=True
            )
    
    async def run(self) -> None:
        """Ejecutar servidor MCP"""
        self.is_running = True
        self.logger.info("MCP Protocol Server iniciado")
        
        try:
            while self.is_running:
                await asyncio.sleep(0.1)
                
        except KeyboardInterrupt:
            self.logger.info("Recibida señal de interrupción")
        except Exception as e:
            self.logger.error(f"Error en servidor: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self) -> None:
        """Apagar servidor"""
        self.logger.info("Apagando servidor MCP...")
        self.is_running = False
        await self.server.stop()


async def main():
    """Función principal"""
    # Configurar logging
    env_config = get_environment_config()
    setup_logging(
        level=env_config["log_level"],
        format=env_config.get("log_format", "text"),
        file=env_config.get("log_file")
    )
    
    logger = logging.getLogger("mcp.main")
    logger.info("Iniciando MCP Core Superior...")
    
    # Configurar manejo de señales
    def signal_handler(signum, frame):
        logger.info(f"Recibida señal {signum}")
        raise KeyboardInterrupt()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Crear y ejecutar servidor
    protocol_server = MCPProtocolServer()
    
    try:
        await protocol_server.run()
    except KeyboardInterrupt:
        logger.info("Interrupción de teclado recibida")
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)
    finally:
        await protocol_server.shutdown()
        logger.info("MCP Core Superior detenido")


if __name__ == "__main__":
    # Configurar event loop policy para Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Ejecutar servidor
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\nMCP Core Superior detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"Error fatal: {e}")
        sys.exit(1)
