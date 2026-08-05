"""
Módulo de Agentes Especializados
=================================

Este módulo contiene agentes especializados para tareas avanzadas de investigación
y análisis de datos web. Los agentes incluidos son:

1. ResearchAgent - Investigación web inteligente con análisis contextual
2. DataMiningAgent - Extracción y análisis avanzado de datos
3. NewsIntelligenceAgent - Agregación y análisis de noticias con detección de sesgos

Cada agente está diseñado para integrarse perfectamente con el sistema MCP Superior
y proporcionar capacidades avanzadas de búsqueda web y análisis de datos.

Autor: MCP Superior Team
Versión: 1.0.0
"""

from .research_agent import (
    ResearchAgent,
    ResearchMethod,
    CredibilityLevel,
    ResearchInsight,
    SourceCredibility,
    ResearchReport,
    create_research_agent
)

from .data_mining_agent import (
    DataMiningAgent,
    DataSourceType,
    DataFormat,
    DataQuality,
    DataRecord,
    DataSet,
    ExtractionJob,
    create_data_mining_agent
)

from .news_intelligence_agent import (
    NewsIntelligenceAgent,
    NewsCategory,
    NewsSource,
    BiasDirection,
    Sentiment,
    NewsArticle,
    NewsStory,
    NewsTrend,
    NewsIntelligenceReport,
    create_news_intelligence_agent
)

__version__ = "1.0.0"
__author__ = "MCP Superior Team"

# Mapeo de agentes especializados
SPECIALIZED_AGENTS = {
    "research_agent": {
        "class": ResearchAgent,
        "factory": create_research_agent,
        "description": "Agente de investigación web inteligente con análisis contextual",
        "capabilities": [
            "Investigación multi-fuente",
            "Análisis de credibilidad",
            "Detección de tendencias",
            "Síntesis de información",
            "Verificación de hechos"
        ]
    },
    "data_mining_agent": {
        "class": DataMiningAgent,
        "factory": create_data_mining_agent,
        "description": "Agente de extracción y análisis avanzado de datos",
        "capabilities": [
            "Extracción de datos estructurados",
            "Transformación y limpieza",
            "Análisis estadístico",
            "Exportación múltiple formato",
            "Programación de extracciones"
        ]
    },
    "news_intelligence_agent": {
        "class": NewsIntelligenceAgent,
        "factory": create_news_intelligence_agent,
        "description": "Agente de inteligencia de noticias con análisis de sesgos",
        "capabilities": [
            "Agregación multi-fuente",
            "Detección de sesgos mediáticos",
            "Análisis de sentimiento",
            "Seguimiento de tendencias",
            "Verificación de credibilidad"
        ]
    }
}

def get_specialized_agent(agent_type: str):
    """
    Obtiene una instancia de agente especializado
    
    Args:
        agent_type: Tipo de agente ("research", "data_mining", "news_intelligence")
        
    Returns:
        Instancia del agente especializado o None si no existe
    """
    agent_key = f"{agent_type}_agent"
    
    if agent_key in SPECIALIZED_AGENTS:
        factory = SPECIALIZED_AGENTS[agent_key]["factory"]
        return factory()
    
    return None

def list_specialized_agents():
    """
    Lista todos los agentes especializados disponibles
    
    Returns:
        Dict con información de todos los agentes
    """
    return {
        agent_key: {
            "name": agent_key,
            "description": agent_info["description"],
            "capabilities": agent_info["capabilities"],
            "class_name": agent_info["class"].__name__
        }
        for agent_key, agent_info in SPECIALIZED_AGENTS.items()
    }

def get_agent_capabilities(agent_type: str):
    """
    Obtiene las capacidades de un agente específico
    
    Args:
        agent_type: Tipo de agente
        
    Returns:
        Lista de capacidades del agente
    """
    agent_key = f"{agent_type}_agent"
    
    if agent_key in SPECIALIZED_AGENTS:
        return SPECIALIZED_AGENTS[agent_key]["capabilities"]
    
    return []

# Versiones y compatibilidad
MIN_PYTHON_VERSION = (3, 7)
SUPPORTED_FORMATS = ["json", "csv", "xml", "excel", "database", "parquet"]
SUPPORTED_METHODS = [method.value for method in ResearchMethod]
SUPPORTED_CATEGORIES = [category.value for category in NewsCategory]

# Configuración por defecto para agentes
DEFAULT_CONFIG = {
    "research_agent": {
        "max_research_queries": 10,
        "sources_per_query": 8,
        "confidence_threshold": 0.7,
        "enable_bias_detection": True,
        "enable_fact_checking": True
    },
    "data_mining_agent": {
        "max_concurrent_extractions": 5,
        "timeout_seconds": 30,
        "batch_size": 100,
        "quality_threshold": 0.7,
        "enable_data_validation": True
    },
    "news_intelligence_agent": {
        "max_articles_per_source": 50,
        "credibility_threshold": 0.6,
        "bias_detection_enabled": True,
        "trend_analysis_enabled": True,
        "fake_news_detection": True
    }
}

def validate_agent_compatibility(agent_type: str, requirements: dict) -> dict:
    """
    Valida compatibilidad de un agente con requisitos específicos
    
    Args:
        agent_type: Tipo de agente
        requirements: Requisitos a validar
        
    Returns:
        Dict con resultado de validación
    """
    result = {
        "compatible": True,
        "warnings": [],
        "errors": [],
        "recommendations": []
    }
    
    agent_key = f"{agent_type}_agent"
    
    if agent_key not in SPECIALIZED_AGENTS:
        result["compatible"] = False
        result["errors"].append(f"Agente {agent_type} no existe")
        return result
    
    # Verificar capacidades requeridas
    required_capabilities = requirements.get("capabilities", [])
    available_capabilities = SPECIALIZED_AGENTS[agent_key]["capabilities"]
    
    for capability in required_capabilities:
        if capability not in available_capabilities:
            result["compatible"] = False
            result["errors"].append(f"Capacidad requerida no disponible: {capability}")
    
    # Verificar formatos soportados
    required_formats = requirements.get("formats", [])
    for format_req in required_formats:
        if format_req not in SUPPORTED_FORMATS:
            result["warnings"].append(f"Formato no estándar: {format_req}")
    
    # Generar recomendaciones
    if result["compatible"]:
        result["recommendations"].extend([
            f"Usar configuración por defecto para {agent_type}",
            "Monitorear rendimiento en producción",
            "Validar resultados regularmente"
        ])
    
    return result

def create_agent_ensemble(agent_types: list, configuration: dict = None):
    """
    Crea un conjunto de agentes especializados que trabajen juntos
    
    Args:
        agent_types: Lista de tipos de agentes a incluir
        configuration: Configuración específica para cada agente
        
    Returns:
        Dict con instancias de agentes configurados
    """
    ensemble = {}
    
    for agent_type in agent_types:
        if configuration and agent_type in configuration:
            config = configuration[agent_type]
            # Aplicar configuración personalizada si está disponible
            agent = get_specialized_agent(agent_type)
            if agent and hasattr(agent, 'config'):
                for key, value in config.items():
                    if key in agent.config:
                        agent.config[key] = value
            ensemble[agent_type] = agent
        else:
            ensemble[agent_type] = get_specialized_agent(agent_type)
    
    return ensemble

# Funciones de utilidad para testing y desarrollo
def run_agent_test(agent_type: str, test_config: dict):
    """
    Ejecuta test básico de un agente
    
    Args:
        agent_type: Tipo de agente a testear
        test_config: Configuración del test
        
    Returns:
        Resultado del test
    """
    try:
        agent = get_specialized_agent(agent_type)
        if not agent:
            return {"success": False, "error": f"Agente {agent_type} no encontrado"}
        
        # Test básico de inicialización
        if hasattr(agent, 'name') and hasattr(agent, 'version'):
            return {
                "success": True,
                "agent_name": agent.name,
                "agent_version": agent.version,
                "status": "initialized"
            }
        else:
            return {
                "success": False,
                "error": "Agente no tiene estructura válida"
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "agent_type": agent_type
        }

def get_agent_health_status(agent_type: str) -> dict:
    """
    Obtiene estado de salud de un agente
    
    Args:
        agent_type: Tipo de agente
        
    Returns:
        Dict con estado de salud
    """
    try:
        agent = get_specialized_agent(agent_type)
        
        if not agent:
            return {
                "status": "error",
                "message": f"Agente {agent_type} no disponible",
                "healthy": False
            }
        
        # Verificar componentes críticos
        health_checks = {
            "initialized": hasattr(agent, 'name') and hasattr(agent, 'version'),
            "has_logger": hasattr(agent, 'logger'),
            "has_config": hasattr(agent, 'config') and isinstance(agent.config, dict)
        }
        
        all_healthy = all(health_checks.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "checks": health_checks,
            "healthy": all_healthy,
            "agent_name": agent.name if hasattr(agent, 'name') else "unknown"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "healthy": False,
            "agent_type": agent_type
        }

# Exportaciones principales
__all__ = [
    # Research Agent
    "ResearchAgent",
    "ResearchMethod", 
    "CredibilityLevel",
    "ResearchInsight",
    "SourceCredibility",
    "ResearchReport",
    "create_research_agent",
    
    # Data Mining Agent
    "DataMiningAgent",
    "DataSourceType",
    "DataFormat",
    "DataQuality",
    "DataRecord",
    "DataSet",
    "ExtractionJob",
    "create_data_mining_agent",
    
    # News Intelligence Agent
    "NewsIntelligenceAgent",
    "NewsCategory",
    "NewsSource", 
    "BiasDirection",
    "Sentiment",
    "NewsArticle",
    "NewsStory",
    "NewsTrend",
    "NewsIntelligenceReport",
    "create_news_intelligence_agent",
    
    # Funciones de utilidad
    "get_specialized_agent",
    "list_specialized_agents",
    "get_agent_capabilities",
    "validate_agent_compatibility",
    "create_agent_ensemble",
    "run_agent_test",
    "get_agent_health_status",
    
    # Constantes
    "DEFAULT_CONFIG",
    "SUPPORTED_FORMATS",
    "SUPPORTED_METHODS",
    "SUPPORTED_CATEGORIES"
]