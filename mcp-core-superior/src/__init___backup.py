"""
MCP Core Superior - Sistema de Orquestación Multi-Agente
Versión 1.0.0

Este paquete implementa el MCP Server Core Superior que integra 
los 5 agentes especializados del sistema multi-agente con el 
gateway ContextForge para crear un orquestador enterprise-grade.

Componentes principales:
- Agents: Wrappers MCP para cada agente especializado
- Orchestrator: Orquestador multi-agente con streaming SSE
- Services: Integración con ContextForge, VectorStore, etc.
- API: APIs REST complementarias
- Utils: Utilidades y helpers del sistema
- Core: Configuración y excepciones
"""

from . import core
from . import agents
from . import orchestrator
from . import services
from . import api
from . import utils

__version__ = "1.0.0"
__author__ = "MiniMax Agent"
__description__ = "MCP Server Core Superior - Multi-Agent Orchestrator"

# Configuración global del paquete
PACKAGE_CONFIG = {
    "name": "mcp_core_superior",
    "version": __version__,
    "description": __description__,
    "components": {
        "core": core,
        "agents": agents,
        "orchestrator": orchestrator,
        "services": services,
        "api": api,
        "utils": utils
    }
}

def get_package_info() -> dict:
    """Obtener información del paquete"""
    return PACKAGE_CONFIG.copy()

def get_components() -> dict:
    """Obtener todos los componentes del paquete"""
    return PACKAGE_CONFIG["components"].copy()
