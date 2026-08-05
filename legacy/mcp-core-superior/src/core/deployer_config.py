"""
Configuración del Zero-Downtime Deployer para MCP Core Superior
Archivo de configuración centralizado para deployments
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

from .zero_downtime_deployer import DeploymentStrategy, HealthCheckConfig


@dataclass
class DeploymentEnvironment:
    """Configuración por entorno de deployment"""
    name: str
    strategy: DeploymentStrategy
    health_check_endpoint: str
    backup_enabled: bool
    monitoring_enabled: bool
    rollback_on_failure: bool
    notification_webhook: Optional[str] = None


# Configuraciones por entorno
DEPLOYMENT_ENVIRONMENTS = {
    "development": DeploymentEnvironment(
        name="development",
        strategy=DeploymentStrategy.IMMEDIATE,
        health_check_endpoint="http://localhost:8080/health",
        backup_enabled=False,
        monitoring_enabled=True,
        rollback_on_failure=False
    ),
    
    "staging": DeploymentEnvironment(
        name="staging",
        strategy=DeploymentStrategy.ROLLING_UPDATE,
        health_check_endpoint="http://localhost:8080/health",
        backup_enabled=True,
        monitoring_enabled=True,
        rollback_on_failure=True,
        notification_webhook="https://hooks.slack.com/services/staging-alerts"
    ),
    
    "production": DeploymentEnvironment(
        name="production",
        strategy=DeploymentStrategy.BLUE_GREEN,
        health_check_endpoint="http://localhost:8080/health",
        backup_enabled=True,
        monitoring_enabled=True,
        rollback_on_failure=True,
        notification_webhook="https://hooks.slack.com/services/production-alerts"
    )
}


@dataclass
class AgentDeploymentConfig:
    """Configuración de deployment para agentes"""
    agent_name: str
    command: List[str]
    environment_vars: Dict[str, str] = None
    resource_limits: Dict[str, Any] = None
    health_check_path: str = "/health"
    startup_timeout: int = 60
    graceful_shutdown_timeout: int = 30


# Configuraciones estándar de agentes
AGENT_DEPLOYMENT_CONFIGS = {
    "file_processing": AgentDeploymentConfig(
        agent_name="file_processing",
        command=["python", "-m", "file_processing_agent"],
        environment_vars={
            "MCP_AGENT_TYPE": "file_processing",
            "MCP_MAX_WORKERS": "4"
        },
        resource_limits={
            "memory_mb": 512,
            "cpu_cores": 1.0,
            "disk_gb": 5
        }
    ),
    
    "database_operations": AgentDeploymentConfig(
        agent_name="database_operations",
        command=["python", "-m", "database_operations_agent"],
        environment_vars={
            "MCP_AGENT_TYPE": "database_operations",
            "MCP_DB_POOL_SIZE": "10"
        },
        resource_limits={
            "memory_mb": 256,
            "cpu_cores": 0.5,
            "disk_gb": 2
        }
    ),
    
    "web_scraping": AgentDeploymentConfig(
        agent_name="web_scraping",
        command=["python", "-m", "web_scraping_agent"],
        environment_vars={
            "MCP_AGENT_TYPE": "web_scraping",
            "MCP_USER_AGENT": "MCP-WebScraper/1.0"
        },
        resource_limits={
            "memory_mb": 256,
            "cpu_cores": 0.5,
            "disk_gb": 2
        }
    ),
    
    "search_engine": AgentDeploymentConfig(
        agent_name="search_engine",
        command=["python", "-m", "search_engine_agent"],
        environment_vars={
            "MCP_AGENT_TYPE": "search_engine",
            "MCP_SEARCH_TIMEOUT": "30"
        },
        resource_limits={
            "memory_mb": 128,
            "cpu_cores": 0.5,
            "disk_gb": 1
        }
    ),
    
    "python_executor": AgentDeploymentConfig(
        agent_name="python_executor",
        command=["python", "-m", "python_executor_agent"],
        environment_vars={
            "MCP_AGENT_TYPE": "python_executor",
            "MCP_EXECUTION_TIMEOUT": "300"
        },
        resource_limits={
            "memory_mb": 1024,
            "cpu_cores": 2.0,
            "disk_gb": 10
        }
    ),
    
    "multiagent_orchestrator": AgentDeploymentConfig(
        agent_name="multiagent_orchestrator",
        command=["python", "-m", "multiagent_orchestrator_agent"],
        environment_vars={
            "MCP_AGENT_TYPE": "orchestrator",
            "MCP_MAX_CONCURRENT_TASKS": "10"
        },
        resource_limits={
            "memory_mb": 512,
            "cpu_cores": 1.0,
            "disk_gb": 5
        }
    )
}


# Configuraciones de health checks por agente
AGENT_HEALTH_CHECKS = {
    "file_processing": HealthCheckConfig(
        endpoint="http://localhost:8081/health/file_processing",
        method="GET",
        expected_status=200,
        timeout=5,
        interval=10,
        failure_threshold=3
    ),
    
    "database_operations": HealthCheckConfig(
        endpoint="http://localhost:8082/health/database_operations",
        method="GET",
        expected_status=200,
        timeout=5,
        interval=10,
        failure_threshold=3
    ),
    
    "web_scraping": HealthCheckConfig(
        endpoint="http://localhost:8083/health/web_scraping",
        method="GET",
        expected_status=200,
        timeout=5,
        interval=10,
        failure_threshold=3
    ),
    
    "search_engine": HealthCheckConfig(
        endpoint="http://localhost:8084/health/search_engine",
        method="GET",
        expected_status=200,
        timeout=5,
        interval=10,
        failure_threshold=3
    ),
    
    "python_executor": HealthCheckConfig(
        endpoint="http://localhost:8085/health/python_executor",
        method="GET",
        expected_status=200,
        timeout=10,
        interval=15,
        failure_threshold=5
    ),
    
    "multiagent_orchestrator": HealthCheckConfig(
        endpoint="http://localhost:8080/health/orchestrator",
        method="GET",
        expected_status=200,
        timeout=10,
        interval=15,
        failure_threshold=3
    )
}


# Configuraciones de migraciones de base de datos
DATABASE_MIGRATIONS = {
    "development": [
        "create_agents_table",
        "create_tasks_table",
        "create_metrics_table"
    ],
    
    "staging": [
        "add_agents_index",
        "add_tasks_status_column",
        "update_metrics_schema",
        "create_agent_health_table"
    ],
    
    "production": [
        "add_agents_index_production",
        "add_tasks_status_column_production", 
        "update_metrics_schema_production",
        "create_agent_health_table_production",
        "optimize_queries_performance"
    ]
}


# Configuraciones de monitoreo por entorno
MONITORING_CONFIG = {
    "development": {
        "metrics_collection_interval": 30,
        "resource_monitoring": True,
        "performance_tracking": True,
        "error_logging": True,
        "log_level": "DEBUG"
    },
    
    "staging": {
        "metrics_collection_interval": 60,
        "resource_monitoring": True,
        "performance_tracking": True,
        "error_logging": True,
        "log_level": "INFO"
    },
    
    "production": {
        "metrics_collection_interval": 30,
        "resource_monitoring": True,
        "performance_tracking": True,
        "error_logging": True,
        "log_level": "WARNING",
        "alerting_enabled": True,
        "slack_notifications": True,
        "email_alerts": True
    }
}


# Configuraciones de load balancer
LOAD_BALANCER_CONFIG = {
    "development": {
        "type": "simple",
        "check_interval": 10
    },
    
    "staging": {
        "type": "nginx",
        "nginx_config": "/etc/nginx/sites-available/staging",
        "nginx_reload_cmd": "nginx -s reload",
        "check_interval": 5
    },
    
    "production": {
        "type": "nginx",
        "nginx_config": "/etc/nginx/sites-available/production",
        "nginx_reload_cmd": "nginx -s reload",
        "check_interval": 3,
        "ssl_enabled": True,
        "health_check_routing": True
    }
}


def get_deployment_config(environment: str, agent_list: Optional[List[str]] = None) -> Dict[str, Any]:
    """Obtener configuración completa de deployment para un entorno"""
    
    if environment not in DEPLOYMENT_ENVIRONMENTS:
        raise ValueError(f"Entorno no válido: {environment}")
    
    env_config = DEPLOYMENT_ENVIRONMENTS[environment]
    
    # Seleccionar agentes a deployar
    if agent_list is None:
        agent_list = list(AGENT_DEPLOYMENT_CONFIGS.keys())
    
    # Configurar agentes
    agent_configs = []
    health_checks = []
    
    for agent_name in agent_list:
        if agent_name in AGENT_DEPLOYMENT_CONFIGS:
            agent_config = AGENT_DEPLOYMENT_CONFIGS[agent_name]
            agent_configs.append({
                "id": agent_name,
                "command": agent_config.command,
                "environment_vars": agent_config.environment_vars,
                "resource_limits": agent_config.resource_limits,
                "startup_timeout": agent_config.startup_timeout,
                "graceful_shutdown_timeout": agent_config.graceful_shutdown_timeout
            })
            
            # Health check para el agente
            if agent_name in AGENT_HEALTH_CHECKS:
                health_check = AGENT_HEALTH_CHECKS[agent_name]
                health_checks.append({
                    "endpoint": health_check.endpoint,
                    "method": health_check.method,
                    "expected_status": health_check.expected_status,
                    "timeout": health_check.timeout,
                    "interval": health_check.interval,
                    "failure_threshold": health_check.failure_threshold
                })
    
    # Configuración completa
    deployment_config = {
        "environment": environment,
        "strategy": env_config.strategy.value,
        "agent_configs": agent_configs,
        "health_checks": health_checks,
        "migrations": DATABASE_MIGRATIONS.get(environment, []),
        "backup_enabled": env_config.backup_enabled,
        "monitoring_enabled": env_config.monitoring_enabled,
        "rollback_on_failure": env_config.rollback_on_failure,
        "notification_webhook": env_config.notification_webhook,
        "monitoring_config": MONITORING_CONFIG.get(environment, {}),
        "load_balancer_config": LOAD_BALANCER_CONFIG.get(environment, {}),
        "health_check_attempts": 5,
        "health_check_interval": 5,
        "batch_size": 1 if env_config.strategy == DeploymentStrategy.BLUE_GREEN else 2,
        "canary_test_duration": 300 if environment == "production" else 60,
        "cleanup_interval": 300,
        "graceful_shutdown_timeout": 60,
        "resource_monitoring_interval": 60
    }
    
    return deployment_config


def get_agent_specific_config(agent_name: str, environment: str) -> Dict[str, Any]:
    """Obtener configuración específica para un agente"""
    
    base_config = AGENT_DEPLOYMENT_CONFIGS.get(agent_name, {})
    
    # Ajustar configuración según entorno
    env_overrides = {
        "development": {
            "timeout_multiplier": 2.0,
            "retry_attempts": 1,
            "log_level": "DEBUG"
        },
        "staging": {
            "timeout_multiplier": 1.5,
            "retry_attempts": 2,
            "log_level": "INFO"
        },
        "production": {
            "timeout_multiplier": 1.0,
            "retry_attempts": 3,
            "log_level": "WARNING",
            "resource_limits_tight": True
        }
    }.get(environment, {})
    
    config = {
        "agent_name": agent_name,
        "command": base_config.command,
        "environment_vars": base_config.environment_vars or {},
        "resource_limits": base_config.resource_limits or {},
        "health_check_path": base_config.health_check_path,
        "startup_timeout": base_config.startup_timeout * env_overrides.get("timeout_multiplier", 1.0),
        "graceful_shutdown_timeout": base_config.graceful_shutdown_timeout,
        "retry_attempts": env_overrides.get("retry_attempts", 3),
        "log_level": env_overrides.get("log_level", "INFO")
    }
    
    return config


def validate_deployment_config(config: Dict[str, Any]) -> bool:
    """Validar configuración de deployment"""
    
    required_fields = [
        "environment",
        "strategy", 
        "agent_configs",
        "health_checks"
    ]
    
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Campo requerido faltante: {field}")
    
    # Validar estrategia
    valid_strategies = [s.value for s in DeploymentStrategy]
    if config["strategy"] not in valid_strategies:
        raise ValueError(f"Estrategia inválida: {config['strategy']}")
    
    # Validar agentes
    if not config["agent_configs"]:
        raise ValueError("Debe especificarse al menos un agente")
    
    for agent_config in config["agent_configs"]:
        if "id" not in agent_config or "command" not in agent_config:
            raise ValueError("Configuración de agente inválida")
    
    # Validar health checks
    for health_check in config["health_checks"]:
        required_health_fields = ["endpoint", "method", "expected_status"]
        for field in required_health_fields:
            if field not in health_check:
                raise ValueError(f"Health check inválido: campo faltante {field}")
    
    return True


# Configuración por defecto para desarrollo
DEFAULT_DEV_CONFIG = get_deployment_config("development", [
    "file_processing",
    "database_operations", 
    "web_scraping",
    "search_engine"
])

# Configuración por defecto para staging
DEFAULT_STAGING_CONFIG = get_deployment_config("staging", [
    "file_processing",
    "database_operations",
    "web_scraping", 
    "search_engine",
    "python_executor"
])

# Configuración por defecto para producción
DEFAULT_PROD_CONFIG = get_deployment_config("production", [
    "file_processing",
    "database_operations",
    "web_scraping",
    "search_engine", 
    "python_executor",
    "multiagent_orchestrator"
])