"""
MCP Core Superior - Agents Module
Wrappers MCP para todos los agentes especializados
"""

from typing import List, Dict, Any, Optional
from .base_agent_wrapper import BaseAgentWrapper, AgentCapability, AgentStatus
from .config import AgentType, AgentConfig, agent_config_manager, validate_agent_setup

# === IMPORTACIONES DE AGENTES PRINCIPALES ===
from .reasoner_wrapper import ReasonerAgentWrapper
from .planner_wrapper import PlannerAgentWrapper
from .executor_wrapper import ExecutorAgentWrapper
from .verifier_wrapper import VerifierAgentWrapper
from .memory_manager_wrapper import MemoryManagerAgentWrapper

# === IMPORTACIONES DE AGENTES ESPECIALIZADOS ===
from .database_operations_agent import (
    DatabaseOperationsAgentWrapper,
    DatabaseConnectionConfig,
    QueryExecutionResult,
    VectorSearchResult,
    PerformanceMetrics,
    DatabaseOperationType,
    ConnectionPoolStatus
)

from .multiagent_orchestrator_agent import (
    MultiAgentOrchestratorAgentWrapper,
    WorkflowStep,
    WorkflowExecution,
    WorkflowState,
    TaskPriority,
    CircuitBreaker,
    LoadBalancer,
    HealthMonitor,
    TaskQueue,
    LoadBalancingStrategy
)

# === IMPORTACIONES CON FALLBACKS ===
try:
    from .python_executor_agent import AdvancedPythonExecutorAgent, SecurityLevel, ResourceLimits
    HAS_PYTHON_EXECUTOR = True
except ImportError as e:
    HAS_PYTHON_EXECUTOR = False
    AdvancedPythonExecutorAgent = None
    SecurityLevel = None
    ResourceLimits = None

try:
    from .web_scraping_agent import WebScrapingAgentWrapper
    HAS_WEB_SCRAPING = True
except ImportError as e:
    HAS_WEB_SCRAPING = False
    WebScrapingAgentWrapper = None

try:
    from .git_operations_agent import GitOperationsAgentWrapper
    HAS_GIT_OPERATIONS = True
except ImportError as e:
    HAS_GIT_OPERATIONS = False
    GitOperationsAgentWrapper = None

# Clases de datos (siempre disponibles)
try:
    from .git_operations_agent import (
        GitRepository,
        CommitInfo,
        BranchInfo,
        PullRequest,
        WorkflowRun,
        GitProvider,
        MergeStrategy,
        ConflictResolution
    )
    HAS_GIT_DATA_CLASSES = True
except ImportError:
    HAS_GIT_DATA_CLASSES = False
    GitRepository = None
    CommitInfo = None
    BranchInfo = None
    PullRequest = None
    WorkflowRun = None
    GitProvider = None
    MergeStrategy = None
    ConflictResolution = None

# Agentes adicionales con fallbacks
try:
    from .file_processing_agent import FileProcessingAgentWrapper
    HAS_FILE_PROCESSING = True
except ImportError:
    HAS_FILE_PROCESSING = False
    FileProcessingAgentWrapper = None

try:
    from .search_engine_agent import SearchEngineAgentWrapper
    HAS_SEARCH_ENGINE = True
except ImportError:
    HAS_SEARCH_ENGINE = False
    SearchEngineAgentWrapper = None

# === AGENTES CRM EMPRESARIALES ===
try:
    from .crm_agents import (
        CRMIntegrationManager,
        SalesforceAgent,
        HubSpotAgent, 
        PipedriveAgent,
        ZohoCRMAgent,
        CRMDataSyncAgent,
        CRMAnalyticsAgent,
        CRMCredentials,
        CRMRecord,
        WebhookConfig,
        CRMClientFactory
    )
    HAS_CRM_INTEGRATION = True
except ImportError:
    HAS_CRM_INTEGRATION = False
    CRMIntegrationManager = None
    SalesforceAgent = None
    HubSpotAgent = None
    PipedriveAgent = None
    ZohoCRMAgent = None
    CRMDataSyncAgent = None
    CRMAnalyticsAgent = None
    CRMCredentials = None
    CRMRecord = None
    WebhookConfig = None
    CRMClientFactory = None

try:
    from .crm_enterprise_system import CRMEnterpriseSystem, CRMConfiguration, CRMPlatform
    HAS_CRM_ENTERPRISE = True
except ImportError:
    HAS_CRM_ENTERPRISE = False
    CRMEnterpriseSystem = None
    CRMConfiguration = None
    CRMPlatform = None

try:
    from .crm_workflows import WorkflowManager, WorkflowDefinition, WorkflowTrigger
    HAS_CRM_WORKFLOWS = True
except ImportError:
    HAS_CRM_WORKFLOWS = False
    WorkflowManager = None
    WorkflowDefinition = None
    WorkflowTrigger = None

try:
    from .crm_auth_security import CRMAuthManager, SecurityConfig, AuthCredentials
    HAS_CRM_AUTH = True
except ImportError:
    HAS_CRM_AUTH = False
    CRMAuthManager = None
    SecurityConfig = None
    AuthCredentials = None

# === DEFINICIÓN DE __all__ ===
__all__ = [
    # Sistema base
    "BaseAgentWrapper",
    "AgentCapability", 
    "AgentStatus",
    "AgentType",
    "AgentConfig",
    "agent_config_manager",
    "validate_agent_setup",
    
    # Agentes principales
    "ReasonerAgentWrapper",
    "PlannerAgentWrapper", 
    "ExecutorAgentWrapper",
    "VerifierAgentWrapper",
    "MemoryManagerAgentWrapper",
    
    # Agentes especializados
    "DatabaseOperationsAgentWrapper",
    "MultiAgentOrchestratorAgentWrapper",
    
    # Esquemas y clases de datos
    "DatabaseConnectionConfig",
    "QueryExecutionResult", 
    "VectorSearchResult",
    "PerformanceMetrics",
    "DatabaseOperationType",
    "ConnectionPoolStatus",
    "WorkflowStep",
    "WorkflowExecution", 
    "WorkflowState",
    "TaskPriority",
    "CircuitBreaker",
    "LoadBalancer",
    "HealthMonitor",
    "TaskQueue",
    "LoadBalancingStrategy"
]

# Agregar agentes especializados condicionalmente
if HAS_PYTHON_EXECUTOR:
    __all__.extend([
        "AdvancedPythonExecutorAgent",
        "SecurityLevel", 
        "ResourceLimits"
    ])

if HAS_WEB_SCRAPING:
    __all__.append("WebScrapingAgentWrapper")

if HAS_GIT_OPERATIONS:
    __all__.append("GitOperationsAgentWrapper")

if HAS_FILE_PROCESSING:
    __all__.append("FileProcessingAgentWrapper")

if HAS_SEARCH_ENGINE:
    __all__.append("SearchEngineAgentWrapper")

# Agregar agentes CRM si están disponibles
if HAS_CRM_INTEGRATION:
    __all__.extend([
        "CRMIntegrationManager",
        "SalesforceAgent", 
        "HubSpotAgent",
        "PipedriveAgent",
        "ZohoCRMAgent",
        "CRMDataSyncAgent",
        "CRMAnalyticsAgent",
        "CRMCredentials",
        "CRMRecord",
        "WebhookConfig",
        "CRMClientFactory"
    ])

if HAS_CRM_ENTERPRISE:
    __all__.extend([
        "CRMEnterpriseSystem",
        "CRMConfiguration",
        "CRMPlatform"
    ])

if HAS_CRM_WORKFLOWS:
    __all__.extend([
        "WorkflowManager",
        "WorkflowDefinition", 
        "WorkflowTrigger"
    ])

if HAS_CRM_AUTH:
    __all__.extend([
        "CRMAuthManager",
        "SecurityConfig",
        "AuthCredentials"
    ])

# Agregar clases de datos de Git si están disponibles
if HAS_GIT_DATA_CLASSES:
    __all__.extend([
        "GitRepository", 
        "CommitInfo",
        "BranchInfo",
        "PullRequest",
        "WorkflowRun",
        "GitProvider",
        "MergeStrategy",
        "ConflictResolution"
    ])


# === FUNCIONES HELPER PARA CREAR AGENTES ===

def create_agent_wrapper(agent_type: AgentType, **kwargs):
    """
    Factory function para crear wrappers de agentes
    
    Args:
        agent_type: Tipo de agente a crear
        **kwargs: Argumentos adicionales para el constructor
        
    Returns:
        Instancia del wrapper del agente
    """
    from .reasoner_wrapper import ReasonerAgentWrapper
    from .planner_wrapper import PlannerAgentWrapper
    from .executor_wrapper import ExecutorAgentWrapper
    from .verifier_wrapper import VerifierAgentWrapper
    from .memory_manager_wrapper import MemoryManagerAgentWrapper
    
    agents_map = {
        AgentType.REASONER: ReasonerAgentWrapper,
        AgentType.PLANNER: PlannerAgentWrapper,
        AgentType.EXECUTOR: ExecutorAgentWrapper,
        AgentType.VERIFIER: VerifierAgentWrapper,
        AgentType.MEMORY_MANAGER: MemoryManagerAgentWrapper,
    }
    
    # Agentes especializados (pueden no estar disponibles)
    if HAS_PYTHON_EXECUTOR:
        from .python_executor_agent import AdvancedPythonExecutorAgent
        agents_map[AgentType.PYTHON_EXECUTOR] = AdvancedPythonExecutorAgent
    
    if HAS_WEB_SCRAPING:
        from .web_scraping_agent import WebScrapingAgentWrapper
        agents_map[AgentType.WEB_SCRAPING] = WebScrapingAgentWrapper
    
    if HAS_GIT_OPERATIONS:
        from .git_operations_agent import GitOperationsAgentWrapper
        agents_map[AgentType.GIT_OPERATIONS] = GitOperationsAgentWrapper
    
    if HAS_FILE_PROCESSING:
        from .file_processing_agent import FileProcessingAgentWrapper
        agents_map[AgentType.FILE_PROCESSING] = FileProcessingAgentWrapper
    
    if HAS_SEARCH_ENGINE:
        from .search_engine_agent import SearchEngineAgentWrapper
        agents_map[AgentType.SEARCH_ENGINE] = SearchEngineAgentWrapper
    
    if agent_type not in agents_map:
        raise ValueError(f"Tipo de agente no soportado: {agent_type.value}")
    
    agent_class = agents_map[agent_type]
    return agent_class(**kwargs)


def get_available_agent_types() -> List[AgentType]:
    """Obtener lista de tipos de agentes disponibles"""
    available_types = [
        AgentType.REASONER,
        AgentType.PLANNER,
        AgentType.EXECUTOR,
        AgentType.VERIFIER,
        AgentType.MEMORY_MANAGER,
        AgentType.DATABASE_OPERATIONS,
        AgentType.MULTIAGENT_ORCHESTRATOR
    ]
    
    if HAS_PYTHON_EXECUTOR:
        available_types.append(AgentType.PYTHON_EXECUTOR)
    
    if HAS_WEB_SCRAPING:
        available_types.append(AgentType.WEB_SCRAPING)
    
    if HAS_GIT_OPERATIONS:
        available_types.append(AgentType.GIT_OPERATIONS)
    
    if HAS_FILE_PROCESSING:
        available_types.append(AgentType.FILE_PROCESSING)
    
    if HAS_SEARCH_ENGINE:
        available_types.append(AgentType.SEARCH_ENGINE)
    
    if HAS_CRM_ENTERPRISE:
        # Agregar tipos CRM específicos
        available_types.extend([
            AgentType.SALESFORCE_AGENT,
            AgentType.HUBSPOT_AGENT, 
            AgentType.PIPEDRIVE_AGENT,
            AgentType.ZOHO_CRM_AGENT,
            AgentType.CRM_DATA_SYNC_AGENT,
            AgentType.CRM_ANALYTICS_AGENT,
            AgentType.CRM_INTEGRATION_MANAGER,
            AgentType.CRM_WORKFLOW_MANAGER,
            AgentType.CRM_AUTH_MANAGER
        ])
    
    return available_types


def create_all_agent_wrappers() -> Dict[str, BaseAgentWrapper]:
    """
    Crear instancias de todos los agentes disponibles
    
    Returns:
        Diccionario con instancias de todos los agentes
    """
    agents = {}
    
    for agent_type in get_available_agent_types():
        try:
            agent = create_agent_wrapper(agent_type)
            agents[agent_type.value] = agent
        except Exception as e:
            print(f"Error creando agente {agent_type.value}: {e}")
    
    return agents


def get_agent_health_status(agent_type: AgentType) -> Dict[str, Any]:
    """
    Obtener estado de salud de un agente específico
    
    Args:
        agent_type: Tipo de agente
        
    Returns:
        Estado de salud del agente
    """
    try:
        agent = create_agent_wrapper(agent_type)
        return agent.health_check()
    except Exception as e:
        return {
            "agent_type": agent_type.value,
            "status": "error",
            "error": str(e)
        }


def get_all_agents_health_status() -> Dict[str, Any]:
    """Obtener estado de salud de todos los agentes"""
    health_status = {}
    
    for agent_type in get_available_agent_types():
        health_status[agent_type.value] = get_agent_health_status(agent_type)
    
    return {
        "agents_health": health_status,
        "summary": {
            "total_agents": len(health_status),
            "healthy_agents": sum(1 for status in health_status.values() 
                                if status.get("status") == "healthy"),
            "unhealthy_agents": sum(1 for status in health_status.values() 
                                  if status.get("status") != "healthy")
        }
    }
