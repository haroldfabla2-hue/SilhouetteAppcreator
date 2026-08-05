#!/usr/bin/env python3
"""
Servidor MCP para File Processing Agent
Proporciona capacidades MCP para procesamiento avanzado de archivos multimedia
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Añadir el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Importar directamente el agente bypassing otros imports problemáticos
import importlib.util
spec = importlib.util.spec_from_file_location("file_processing_agent", os.path.join(os.path.dirname(__file__), 'src', 'agents', 'file_processing_agent.py'))
file_processing_agent = importlib.util.module_from_spec(spec)
sys.modules['file_processing_agent'] = file_processing_agent
spec.loader.exec_module(file_processing_agent)

FileProcessingAgentMCP = file_processing_agent.FileProcessingAgentMCP

class FileProcessingMCPServer:
    """Servidor MCP para procesamiento de archivos"""
    
    def __init__(self):
        self.agent = FileProcessingAgentMCP()
        self.tools = self.agent.get_tools()
        
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja la inicialización del servidor MCP"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {}
            },
            "serverInfo": {
                "name": "File Processing Agent MCP",
                "version": "1.0.0",
                "description": "Servidor MCP para procesamiento avanzado de archivos multimedia y documentos"
            }
        }
    
    async def handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Lista todas las herramientas disponibles"""
        return {
            "tools": self.tools
        }
    
    async def handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta una herramienta específica"""
        try:
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if not tool_name:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({
                                "success": False,
                                "error": "Nombre de herramienta requerido"
                            })
                        }
                    ]
                }
            
            # Ejecutar la herramienta
            result = await self.agent.call_tool(tool_name, arguments)
            
            # Formatear resultado para MCP
            if result.get("success", False):
                content = [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "success": True,
                            "data": result.get("data", {}),
                            "file_path": result.get("file_path", "")
                        }, ensure_ascii=False, indent=2)
                    }
                ]
            else:
                content = [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "success": False,
                            "error": result.get("error", "Error desconocido")
                        })
                    }
                ]
            
            return {
                "content": content
            }
            
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "success": False,
                            "error": f"Error ejecutando herramienta: {str(e)}"
                        })
                    }
                ]
            }
    
    async def run_server(self):
        """Ejecuta el servidor MCP"""
        print("🚀 File Processing Agent MCP Server iniciando...")
        
        # Mostrar herramientas disponibles
        print(f"📋 Herramientas disponibles: {len(self.tools)}")
        for tool in self.tools:
            print(f"   ✓ {tool['name']}")
        
        print("\n🔧 Servidor MCP listo para conexiones")
        print("📡 Esperando mensajes del cliente...")
        
        while True:
            try:
                # Leer mensaje del stdin
                line = sys.stdin.readline()
                if not line:
                    break
                
                message = json.loads(line.strip())
                method = message.get("method")
                params = message.get("params", {})
                request_id = message.get("id")
                
                # Manejar diferentes métodos
                if method == "initialize":
                    response = await self.handle_initialize(params)
                elif method == "tools/list":
                    response = await self.handle_list_tools(params)
                elif method == "tools/call":
                    response = await self.handle_call_tool(params)
                else:
                    response = {
                        "error": {
                            "code": -32601,
                            "message": f"Método no soportado: {method}"
                        }
                    }
                
                # Enviar respuesta
                response["id"] = request_id
                print(json.dumps(response, ensure_ascii=False))
                sys.stdout.flush()
                
            except json.JSONDecodeError as e:
                error_response = {
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Error decodificando JSON: {str(e)}"
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
            except KeyboardInterrupt:
                print("\n👋 Cerrando servidor...")
                break
            except Exception as e:
                error_response = {
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": f"Error interno: {str(e)}"
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()


async def main():
    """Función principal"""
    server = FileProcessingMCPServer()
    await server.run_server()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Servidor terminado por el usuario")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        sys.exit(1)