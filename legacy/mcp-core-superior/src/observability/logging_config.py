"""
Configuración del Sistema de Structured Logging

Proporciona configuraciones predefinidas para diferentes entornos y agentes MCP.
"""

from typing import Dict, Any, Optional
from .structured_logger import (
    StructuredLogger, 
    LogLevel, 
    create_mcp_logger,
    get_agent_logger,
    set_current_logger,
    get_current_logger
)


# Configuraciones por entorno
ENVIRONMENT_CONFIGS = {
    'development': {
        'level': LogLevel.DEBUG,
        'enable_console': True,
        'enable_file': True,
        'enable_elk': False,
        'enable_cloud': False,
        'log_dir': './logs/development'
    },
    
    'staging': {
        'level': LogLevel.INFO,
        'enable_console': True,
        'enable_file': True,
        'enable_elk': True,
        'enable_cloud': False,
        'elk_config': {
            'elasticsearch_url': 'http://localhost:9200',
            'index_prefix': 'mcp-staging-'
        },
        'log_dir': './logs/staging'
    },
    
    'production': {
        'level': LogLevel.INFO,
        'enable_console': False,
        'enable_file': True,
        'enable_elk': True,
        'enable_cloud': True,
        'elk_config': {
            'elasticsearch_url': 'https://elasticsearch.example.com:9200',
            'index_prefix': 'mcp-production-'
        },
        'cloud_config': {
            'provider': 'aws',
            'config': {
                'log_group': '/aws/mcp/production',
                'log_stream': 'mcp-logs'
            }
        },
        'log_dir': './logs/production'
    }
}


# Configuraciones específicas por agente
AGENT_SPECIFIC_CONFIGS = {
    'database_operations': {
        'level': LogLevel.DEBUG,
        'extra_fields': {
            'component_type': 'database',
            'sensitive_operation': True
        }
    },
    
    'file_processing': {
        'level': LogLevel.INFO,
        'extra_fields': {
            'component_type': 'file_processor'
        }
    },
    
    'git_operations': {
        'level': LogLevel.INFO,
        'extra_fields': {
            'component_type': 'version_control'
        }
    },
    
    'multiagent_orchestrator': {
        'level': LogLevel.DEBUG,
        'extra_fields': {
            'component_type': 'orchestrator'
        }
    },
    
    'python_executor': {
        'level': LogLevel.DEBUG,
        'extra_fields': {
            'component_type': 'executor',
            'high_performance': True
        }
    },
    
    'reasoner': {
        'level': LogLevel.INFO,
        'extra_fields': {
            'component_type': 'reasoning'
        }
    },
    
    'search_engine': {
        'level': LogLevel.INFO,
        'extra_fields': {
            'component_type': 'search'
        }
    },
    
    'verifier': {
        'level': LogLevel.DEBUG,
        'extra_fields': {
            'component_type': 'verification'
        }
    },
    
    'web_scraping': {
        'level': LogLevel.INFO,
        'extra_fields': {
            'component_type': 'web_scraper'
        }
    },
    
    'executor_wrapper': {
        'level': LogLevel.DEBUG,
        'extra_fields': {
            'component_type': 'wrapper'
        }
    },
    
    'planner_wrapper': {
        'level': LogLevel.DEBUG,
        'extra_fields': {
            'component_type': 'planner'
        }
    },
    
    'memory_manager': {
        'level': LogLevel.INFO,
        'extra_fields': {
            'component_type': 'memory'
        }
    }
}


def configure_logging_for_environment(environment: str = 'development') -> StructuredLogger:
    """
    Configura logging basado en el entorno
    
    Args:
        environment: development, staging, production
    
    Returns:
        StructuredLogger configurado
    """
    if environment not in ENVIRONMENT_CONFIGS:
        environment = 'development'
    
    env_config = ENVIRONMENT_CONFIGS[environment].copy()
    level = env_config.pop('level')
    
    logger = create_mcp_logger(
        component=f"mcp-{environment}",
        level=level,
        config=env_config
    )
    
    # Establecer como logger global
    set_current_logger(logger)
    
    return logger


def configure_logging_for_agent(agent_name: str, 
                               environment: str = 'development') -> StructuredLogger:
    """
    Configura logging específico para un agente
    
    Args:
        agent_name: Nombre del agente
        environment: Entorno de ejecución
    
    Returns:
        StructuredLogger configurado
    """
    base_logger = get_agent_logger(agent_name)
    
    # Aplicar configuraciones específicas del entorno
    env_config = ENVIRONMENT_CONFIGS.get(environment, ENVIRONMENT_CONFIGS['development'])
    level = env_config['level']
    base_logger.set_level(level)
    
    # Aplicar configuraciones específicas del agente
    agent_config = AGENT_SPECIFIC_CONFIGS.get(agent_name, {})
    if 'extra_fields' in agent_config:
        # Los campos extra se aplicarán automáticamente en cada log
        pass
    
    return base_logger


def initialize_mcp_logging(environment: str = 'development') -> Dict[str, StructuredLogger]:
    """
    Inicializa logging para todo el sistema MCP
    
    Args:
        environment: Entorno de ejecución
    
    Returns:
        Diccionario con loggers por agente
    """
    logger = configure_logging_for_environment(environment)
    loggers = {'global': logger}
    
    # Inicializar loggers para todos los agentes
    for agent_name in AGENT_SPECIFIC_CONFIGS.keys():
        try:
            agent_logger = configure_logging_for_agent(agent_name, environment)
            loggers[agent_name] = agent_logger
        except Exception as e:
            logger.error(f"Failed to initialize logger for agent {agent_name}", 
                        exception=e)
    
    return loggers


def get_mcp_logger(agent_name: Optional[str] = None) -> StructuredLogger:
    """
    Obtiene logger MCP apropiado
    
    Args:
        agent_name: Nombre del agente (opcional)
    
    Returns:
        StructuredLogger configurado
    """
    if agent_name:
        return configure_logging_for_agent(agent_name)
    
    return get_current_logger()


# Configuración para diferentes tipos de operaciones
OPERATIONAL_CONFIGS = {
    'performance_critical': {
        'level': LogLevel.DEBUG,
        'enable_performance_logging': True,
        'sampling_rate': 1.0
    },
    
    'audit_required': {
        'level': LogLevel.INFO,
        'enable_audit_logging': True,
        'compliance_mode': True
    },
    
    'debug_session': {
        'level': LogLevel.TRACE,
        'enable_console': True,
        'enable_file': True,
        'detailed_tracing': True
    },
    
    'error_investigation': {
        'level': LogLevel.DEBUG,
        'enable_stack_traces': True,
        'enable_correlation_tracing': True
    }
}


def configure_operational_logging(operation_type: str, 
                                 agent_name: Optional[str] = None) -> StructuredLogger:
    """
    Configura logging para tipos específicos de operaciones
    
    Args:
        operation_type: Tipo de operación (performance_critical, audit_required, etc.)
        agent_name: Nombre del agente (opcional)
    
    Returns:
        StructuredLogger configurado
    """
    if operation_type not in OPERATIONAL_CONFIGS:
        operation_type = 'debug_session'
    
    op_config = OPERATIONAL_CONFIGS[operation_type]
    
    # Crear logger base
    if agent_name:
        logger = configure_logging_for_agent(agent_name)
    else:
        logger = get_current_logger()
    
    # Aplicar configuración específica
    level = op_config.get('level', LogLevel.INFO)
    logger.set_level(level)
    
    return logger


# Ejemplo de uso
if __name__ == "__main__":
    # Inicializar logging para desarrollo
    loggers = initialize_mcp_logging('development')
    print(f"Initialized loggers for {len(loggers)} agents")
    
    # Obtener logger específico
    db_logger = get_mcp_logger('database_operations')
    db_logger.info("Database logger initialized")
    
    # Configurar para operación específica
    perf_logger = configure_operational_logging('performance_critical', 'python_executor')
    perf_logger.info("Performance logging configured")