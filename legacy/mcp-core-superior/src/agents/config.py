"""
Configuración específica para wrappers de agentes MCP
Maneja configuraciones y dependencias para todos los agentes especializados
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import os

class AgentType(Enum):
    """Tipos de agentes soportados"""
    REASONER = "reasoner"
    PLANNER = "planner"
    EXECUTOR = "executor"
    VERIFIER = "verifier"
    MEMORY_MANAGER = "memory_manager"
    PYTHON_EXECUTOR = "python_executor"
    WEB_SCRAPING = "web_scraping"
    GIT_OPERATIONS = "git_operations"
    DATABASE_OPERATIONS = "database_operations"
    FILE_PROCESSING = "file_processing"
    SEARCH_ENGINE = "search_engine"
    MULTIAGENT_ORCHESTRATOR = "multiagent_orchestrator"
    
    # Agentes CRM Empresariales
    SALESFORCE_AGENT = "salesforce_agent"
    HUBSPOT_AGENT = "hubspot_agent"
    PIPEDRIVE_AGENT = "pipedrive_agent"
    ZOHO_CRM_AGENT = "zoho_crm_agent"
    CRM_DATA_SYNC_AGENT = "crm_data_sync_agent"
    CRM_ANALYTICS_AGENT = "crm_analytics_agent"
    CRM_INTEGRATION_MANAGER = "crm_integration_manager"
    CRM_WORKFLOW_MANAGER = "crm_workflow_manager"
    CRM_AUTH_MANAGER = "crm_auth_manager"


@dataclass
class AgentConfig:
    """Configuración para un agente específico"""
    agent_type: AgentType
    enabled: bool = True
    timeout_seconds: int = 60
    retry_attempts: int = 3
    retry_delay: float = 1.0
    max_concurrent: int = 3
    dependencies: list = None
    environment_variables: Dict[str, str] = None
    resource_limits: Dict[str, Any] = None
    security_config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.environment_variables is None:
            self.environment_variables = {}
        if self.resource_limits is None:
            self.resource_limits = {}
        if self.security_config is None:
            self.security_config = {}


class AgentConfigManager:
    """Gestor de configuraciones para todos los agentes"""
    
    def __init__(self):
        self.configs = self._initialize_configs()
    
    def _initialize_configs(self) -> Dict[AgentType, AgentConfig]:
        """Inicializar configuraciones por defecto para todos los agentes"""
        return {
            AgentType.REASONER: AgentConfig(
                agent_type=AgentType.REASONER,
                timeout_seconds=int(os.getenv("REASONER_TIMEOUT", "60")),
                retry_attempts=int(os.getenv("REASONER_RETRIES", "3")),
                max_concurrent=int(os.getenv("REASONER_CONCURRENT", "3"))
            ),
            AgentType.PLANNER: AgentConfig(
                agent_type=AgentType.PLANNER,
                timeout_seconds=int(os.getenv("PLANNER_TIMEOUT", "60")),
                retry_attempts=int(os.getenv("PLANNER_RETRIES", "3")),
                max_concurrent=int(os.getenv("PLANNER_CONCURRENT", "3"))
            ),
            AgentType.EXECUTOR: AgentConfig(
                agent_type=AgentType.EXECUTOR,
                timeout_seconds=int(os.getenv("EXECUTOR_TIMEOUT", "120")),
                retry_attempts=int(os.getenv("EXECUTOR_RETRIES", "2")),
                max_concurrent=int(os.getenv("EXECUTOR_CONCURRENT", "5"))
            ),
            AgentType.VERIFIER: AgentConfig(
                agent_type=AgentType.VERIFIER,
                timeout_seconds=int(os.getenv("VERIFIER_TIMEOUT", "60")),
                retry_attempts=int(os.getenv("VERIFIER_RETRIES", "2")),
                max_concurrent=int(os.getenv("VERIFIER_CONCURRENT", "3"))
            ),
            AgentType.MEMORY_MANAGER: AgentConfig(
                agent_type=AgentType.MEMORY_MANAGER,
                timeout_seconds=int(os.getenv("MEMORY_TIMEOUT", "30")),
                retry_attempts=int(os.getenv("MEMORY_RETRIES", "2")),
                max_concurrent=int(os.getenv("MEMORY_CONCURRENT", "10")),
                resource_limits={
                    "cache_size": int(os.getenv("MEMORY_CACHE_SIZE", "1000")),
                    "max_age_hours": int(os.getenv("MEMORY_MAX_AGE", "24"))
                }
            ),
            AgentType.PYTHON_EXECUTOR: AgentConfig(
                agent_type=AgentType.PYTHON_EXECUTOR,
                timeout_seconds=int(os.getenv("PYTHON_EXECUTOR_TIMEOUT", "300")),
                retry_attempts=int(os.getenv("PYTHON_EXECUTOR_RETRIES", "2")),
                max_concurrent=int(os.getenv("PYTHON_EXECUTOR_CONCURRENT", "4")),
                dependencies=["playwright", "psutil", "memory_profiler"],
                resource_limits={
                    "max_memory_mb": int(os.getenv("PYTHON_MAX_MEMORY", "512")),
                    "max_cpu_seconds": int(os.getenv("PYTHON_MAX_CPU", "30"))
                },
                security_config={
                    "security_level": os.getenv("PYTHON_SECURITY_LEVEL", "RESTRICTED"),
                    "allowed_builtins": [
                        "int", "float", "str", "bool", "list", "dict", "tuple", "set",
                        "abs", "min", "max", "sum", "print", "len", "range"
                    ]
                }
            ),
            AgentType.WEB_SCRAPING: AgentConfig(
                agent_type=AgentType.WEB_SCRAPING,
                timeout_seconds=int(os.getenv("WEB_SCRAPING_TIMEOUT", "180")),
                retry_attempts=int(os.getenv("WEB_SCRAPING_RETRIES", "3")),
                max_concurrent=int(os.getenv("WEB_SCRAPING_CONCURRENT", "3")),
                dependencies=["playwright"],
                resource_limits={
                    "max_browser_instances": int(os.getenv("MAX_BROWSER_INSTANCES", "5")),
                    "screenshot_quality": int(os.getenv("SCREENSHOT_QUALITY", "80"))
                }
            ),
            AgentType.GIT_OPERATIONS: AgentConfig(
                agent_type=AgentType.GIT_OPERATIONS,
                timeout_seconds=int(os.getenv("GIT_OPERATIONS_TIMEOUT", "120")),
                retry_attempts=int(os.getenv("GIT_OPERATIONS_RETRIES", "2")),
                max_concurrent=int(os.getenv("GIT_OPERATIONS_CONCURRENT", "3")),
                dependencies=["gitpython", "aiohttp", "pyyaml"]
            ),
            AgentType.DATABASE_OPERATIONS: AgentConfig(
                agent_type=AgentType.DATABASE_OPERATIONS,
                timeout_seconds=int(os.getenv("DB_OPERATIONS_TIMEOUT", "180")),
                retry_attempts=int(os.getenv("DB_OPERATIONS_RETRIES", "3")),
                max_concurrent=int(os.getenv("DB_OPERATIONS_CONCURRENT", "5")),
                dependencies=["asyncpg", "sqlalchemy", "psycopg2"],
                resource_limits={
                    "max_connections": int(os.getenv("DB_MAX_CONNECTIONS", "20")),
                    "query_timeout": int(os.getenv("DB_QUERY_TIMEOUT", "30"))
                }
            ),
            AgentType.FILE_PROCESSING: AgentConfig(
                agent_type=AgentType.FILE_PROCESSING,
                timeout_seconds=int(os.getenv("FILE_PROCESSING_TIMEOUT", "180")),
                retry_attempts=int(os.getenv("FILE_PROCESSING_RETRIES", "2")),
                max_concurrent=int(os.getenv("FILE_PROCESSING_CONCURRENT", "4")),
                dependencies=["pillow", "pdfplumber", "openpyxl"]
            ),
            AgentType.SEARCH_ENGINE: AgentConfig(
                agent_type=AgentType.SEARCH_ENGINE,
                timeout_seconds=int(os.getenv("SEARCH_ENGINE_TIMEOUT", "90")),
                retry_attempts=int(os.getenv("SEARCH_ENGINE_RETRIES", "2")),
                max_concurrent=int(os.getenv("SEARCH_ENGINE_CONCURRENT", "3")),
                dependencies=["selenium", "beautifulsoup4", "requests"]
            ),
            AgentType.MULTIAGENT_ORCHESTRATOR: AgentConfig(
                agent_type=AgentType.MULTIAGENT_ORCHESTRATOR,
                timeout_seconds=int(os.getenv("ORCHESTRATOR_TIMEOUT", "600")),
                retry_attempts=int(os.getenv("ORCHESTRATOR_RETRIES", "2")),
                max_concurrent=int(os.getenv("ORCHESTRATOR_CONCURRENT", "10")),
                resource_limits={
                    "max_workflows": int(os.getenv("MAX_WORKFLOWS", "50")),
                    "max_tasks_per_workflow": int(os.getenv("MAX_TASKS_PER_WORKFLOW", "100"))
                }
            )
        }
    
    def get_config(self, agent_type: AgentType) -> Optional[AgentConfig]:
        """Obtener configuración para un tipo de agente"""
        return self.configs.get(agent_type)
    
    def update_config(self, agent_type: AgentType, config: AgentConfig) -> None:
        """Actualizar configuración de un agente"""
        self.configs[agent_type] = config
    
    def is_enabled(self, agent_type: AgentType) -> bool:
        """Verificar si un agente está habilitado"""
        config = self.get_config(agent_type)
        return config.enabled if config else False
    
    def get_enabled_agents(self) -> List[AgentType]:
        """Obtener lista de agentes habilitados"""
        return [agent_type for agent_type, config in self.configs.items() if config.enabled]
    
    def validate_dependencies(self, agent_type: AgentType) -> Dict[str, Any]:
        """Validar dependencias de un agente"""
        config = self.get_config(agent_type)
        if not config:
            return {"status": "error", "message": f"Configuración no encontrada para {agent_type.value}"}
        
        missing_deps = []
        available_deps = []
        
        for dep in config.dependencies:
            try:
                __import__(dep)
                available_deps.append(dep)
            except ImportError:
                missing_deps.append(dep)
        
        return {
            "status": "ok" if not missing_deps else "warning",
            "agent_type": agent_type.value,
            "available_dependencies": available_deps,
            "missing_dependencies": missing_deps,
            "dependency_check_passed": len(missing_deps) == 0
        }


# Instancia global del gestor de configuración
agent_config_manager = AgentConfigManager()


def get_agent_config(agent_type: AgentType) -> Optional[AgentConfig]:
    """Función helper para obtener configuración de agente"""
    return agent_config_manager.get_config(agent_type)


def get_safe_settings():
    """Obtener configuración segura, con fallbacks cuando el sistema base no está disponible"""
    try:
        # Intentar importar del sistema principal
        from ..core.config import settings
        return settings
    except ImportError:
        # Fallback a configuración por defecto
        return type('Settings', (), {
            'max_concurrent_tools': int(os.getenv('MAX_CONCURRENT_TOOLS', '5')),
            'agent_timeout_seconds': int(os.getenv('AGENT_TIMEOUT_SECONDS', '60')),
            'agent_retry_attempts': int(os.getenv('AGENT_RETRY_ATTEMPTS', '3')),
            'agent_retry_delay': float(os.getenv('AGENT_RETRY_DELAY', '1.0')),
            'executor_max_workers': int(os.getenv('EXECUTOR_MAX_WORKERS', '4')),
            'executor_timeout_seconds': int(os.getenv('EXECUTOR_TIMEOUT_SECONDS', '300'))
        })()


def validate_agent_setup() -> Dict[str, Any]:
    """Validar configuración completa del setup de agentes"""
    results = {}
    
    for agent_type in AgentType:
        config = agent_config_manager.get_config(agent_type)
        if config and config.enabled:
            dep_check = agent_config_manager.validate_dependencies(agent_type)
            results[agent_type.value] = dep_check
    
    return {
        "validation_results": results,
        "summary": {
            "total_agents": len([r for r in results.values() if r["status"] != "error"]),
            "ready_agents": len([r for r in results.values() if r["status"] == "ok"]),
            "warning_agents": len([r for r in results.values() if r["status"] == "warning"]),
            "error_agents": len([r for r in results.values() if r["status"] == "error"])
        }
    }