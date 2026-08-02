import logging
import ast
import inspect
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger("DynamicMCPFactory")

# Importación resiliente de FastMCP
try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    logger.warning("Librería 'fastmcp' no encontrada. Se usará wrapper de compatibilidad FastMCP.")

class DynamicMCPFactory:
    """
    Fábrica y Registro Dinámico de Servidores FastMCP.
    Genera nuevos servidores MCP en runtime usando la API real de FastMCP,
    permite registrar herramientas dinámicamente mediante inspección AST y enrutamiento.
    """

    def __init__(self):
        self.servers: Dict[str, Any] = {}
        self.server_metadata: Dict[str, Dict[str, Any]] = {}
        logger.info("DynamicMCPFactory inicializado.")

    def create_server(self, name: str, description: str = "") -> Dict[str, Any]:
        """Crea e inicializa un servidor FastMCP en memoria."""
        server_id = f"mcp_{name.lower().replace(' ', '_')}"
        
        if FASTMCP_AVAILABLE:
            mcp_instance = FastMCP(name=name, instructions=description)
        else:
            # Fallback wrapper emulador de FastMCP
            class MockFastMCP:
                def __init__(self, name, instructions):
                    self.name = name
                    self.instructions = instructions
                    self._tools = {}
                def tool(self, func):
                    self._tools[func.__name__] = func
                    return func
            mcp_instance = MockFastMCP(name=name, instructions=description)

        self.servers[server_id] = mcp_instance
        self.server_metadata[server_id] = {
            "id": server_id,
            "name": name,
            "description": description,
            "transport": "sse",
            "tools": {},
            "status": "active"
        }
        
        logger.info(f"[FastMCP] Nuevo servidor MCP instanciado: {name} ({server_id})")
        return self.get_server_info(server_id)

    def register_tool_from_code(self, server_id: str, tool_name: str, code_str: str) -> Dict[str, Any]:
        """
        Analiza dinámicamente un bloque de código Python mediante AST,
        compila la función y la registra como una herramienta activa en el servidor FastMCP.
        """
        if server_id not in self.servers:
            return {"success": False, "error": f"Servidor MCP '{server_id}' no encontrado."}

        try:
            # Validar sintaxis con AST
            parsed_ast = ast.parse(code_str)
            func_nodes = [n for n in parsed_ast.body if isinstance(n, ast.FunctionDef)]
            if not func_nodes:
                return {"success": False, "error": "No se encontró ninguna definición de función (def) en el código proporcionado."}

            local_scope = {}
            exec(code_str, globals(), local_scope)
            
            target_func = local_scope.get(tool_name) or local_scope.get(func_nodes[0].name)
            if not callable(target_func):
                return {"success": False, "error": f"No se pudo compilar la función '{tool_name}'."}

            mcp_instance = self.servers[server_id]
            
            # Registrar en FastMCP
            if hasattr(mcp_instance, "tool"):
                mcp_instance.tool(target_func)
            
            # Registrar metadata de la herramienta
            doc = inspect.getdoc(target_func) or "Sin descripción"
            sig = str(inspect.signature(target_func))
            
            self.server_metadata[server_id]["tools"][target_func.__name__] = {
                "name": target_func.__name__,
                "signature": sig,
                "description": doc
            }

            logger.info(f"[FastMCP] Herramienta '{target_func.__name__}' registrada en '{server_id}'")
            return {
                "success": True,
                "server_id": server_id,
                "tool_name": target_func.__name__,
                "signature": sig,
                "description": doc
            }

        except Exception as e:
            logger.error(f"[FastMCP] Error registrando herramienta en {server_id}: {e}")
            return {"success": False, "error": str(e)}

    def get_server_info(self, server_id: str) -> Dict[str, Any]:
        """Devuelve la información detallada y herramientas de un servidor MCP."""
        if server_id not in self.server_metadata:
            return {"error": "Servidor no encontrado"}
        
        meta = self.server_metadata[server_id]
        meta["tools_count"] = len(meta["tools"])
        return meta

    def list_servers(self) -> List[Dict[str, Any]]:
        """Lista todos los servidores MCP dinámicos activos."""
        result = []
        for sid in self.server_metadata:
            result.append(self.get_server_info(sid))
        return result
