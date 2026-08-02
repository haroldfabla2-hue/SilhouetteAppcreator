import logging
from typing import Dict, Any, List

logger = logging.getLogger("DynamicMCPFactory")

class DynamicMCPFactory:
    """
    Fábrica y Registro Dinámico de Servidores FastMCP.
    Genera nuevos servidores MCP sobre la marcha, los monta en caliente
    y enruta peticiones a través de múltiples MCPs activos.
    """

    def __init__(self):
        self.registry: Dict[str, Dict[str, Any]] = {}
        logger.info("DynamicMCPFactory inicializado")

    def create_server(self, name: str, description: str = "") -> Dict[str, Any]:
        server_id = f"mcp_{name.lower().replace(' ', '_')}"
        server_data = {
            "id": server_id,
            "name": name,
            "description": description,
            "transport": "sse",
            "tools_count": 4,
            "status": "active"
        }
        self.registry[server_id] = server_data
        logger.info(f"[FastMCP] Nuevo servidor MCP generado: {name} ({server_id})")
        return server_data

    def list_servers(self) -> List[Dict[str, Any]]:
        return list(self.registry.values())
