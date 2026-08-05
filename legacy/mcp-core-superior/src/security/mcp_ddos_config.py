"""
Configuración específica del sistema DDoS Protection para MCP Core Superior

Este archivo contiene la configuración optimizada para los endpoints y agentes
específicos de MCP Core Superior.
"""

import os
from typing import Dict, Any

# Configuración específica de MCP Core Superior
MCP_DDOS_CONFIG: Dict[str, Any] = {
    # Redis para rate limiting distribuido
    "redis": {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "password": os.getenv("REDIS_PASSWORD"),
        "db": int(os.getenv("REDIS_DB", "1")),  # DB diferente para MCP
        "socket_timeout": 3,
        "socket_connect_timeout": 3,
        "retry_on_timeout": True
    },
    
    # GeoIP para bloqueo geográfico
    "geoip": {
        "database_path": os.getenv("GEOIP_DATABASE_PATH", "/usr/share/GeoIP/GeoLite2-Country.mmdb"),
        "enabled": True
    },
    
    # Integración WAF
    "waf": {
        "cloudflare": {
            "api_key": os.getenv("CLOUDFLARE_API_KEY"),
            "zone_id": os.getenv("CLOUDFLARE_ZONE_ID"),
            "enabled": bool(os.getenv("CLOUDFLARE_ENABLED", "false").lower() == "true")
        },
        "aws_waf": {
            "region": os.getenv("AWS_WAF_REGION", "us-east-1"),
            "web_acl_arn": os.getenv("AWS_WAF_WEB_ACL_ARN"),
            "enabled": bool(os.getenv("AWS_WAF_ENABLED", "false").lower() == "true")
        }
    },
    
    # Rate limits específicos para MCP Core Superior
    "rate_limits": {
        "default": {
            "requests_per_minute": 100,
            "requests_per_hour": 1000,
            "burst_limit": 50,
            "scope": "per_ip"
        },
        
        # === AGENTES MCP ===
        "/api/agents/execute": {
            "method": "POST",
            "requests_per_minute": 30,
            "requests_per_hour": 500,
            "burst_limit": 10,
            "scope": "per_user",
            "description": "Ejecución de agentes MCP"
        },
        "/api/agents/upload": {
            "method": "POST", 
            "requests_per_minute": 10,
            "requests_per_hour": 100,
            "burst_limit": 5,
            "scope": "per_user",
            "description": "Subida de archivos para agentes"
        },
        "/api/agents/status": {
            "method": "GET",
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "burst_limit": 20,
            "scope": "per_ip",
            "description": "Estado de agentes MCP"
        },
        "/api/agents": {
            "method": "GET",
            "requests_per_minute": 120,
            "requests_per_hour": 2000,
            "burst_limit": 30,
            "scope": "per_ip",
            "description": "Listado de agentes MCP"
        },
        
        # === ORQUESTADOR MCP ===
        "/api/orchestrator/execute": {
            "method": "POST",
            "requests_per_minute": 20,
            "requests_per_hour": 300,
            "burst_limit": 5,
            "scope": "per_user",
            "description": "Ejecución orquestada de agentes"
        },
        "/api/orchestrator/status": {
            "method": "GET",
            "requests_per_minute": 120,
            "requests_per_hour": 2000,
            "burst_limit": 30,
            "scope": "per_ip",
            "description": "Estado del orquestador"
        },
        "/api/orchestrator/collaborate": {
            "method": "POST",
            "requests_per_minute": 15,
            "requests_per_hour": 200,
            "burst_limit": 5,
            "scope": "per_user",
            "description": "Colaboración entre agentes"
        },
        
        # === OPERACIONES DE BASE DE DATOS ===
        "/api/database/query": {
            "method": "POST",
            "requests_per_minute": 50,
            "requests_per_hour": 800,
            "burst_limit": 15,
            "scope": "per_user",
            "description": "Consultas a base de datos"
        },
        "/api/database/execute": {
            "method": "POST",
            "requests_per_minute": 30,
            "requests_per_hour": 500,
            "burst_limit": 10,
            "scope": "per_user",
            "description": "Ejecución de scripts SQL"
        },
        "/api/database/backups": {
            "method": "POST",
            "requests_per_minute": 5,
            "requests_per_hour": 50,
            "burst_limit": 2,
            "scope": "per_user",
            "description": "Backups de base de datos"
        },
        
        # === MOTOR DE BÚSQUEDA ===
        "/api/search": {
            "method": "POST",
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "burst_limit": 20,
            "scope": "per_ip",
            "description": "Búsquedas en motor"
        },
        "/api/search/stats": {
            "method": "GET",
            "requests_per_minute": 30,
            "requests_per_hour": 500,
            "burst_limit": 10,
            "scope": "per_ip",
            "description": "Estadísticas de búsqueda"
        },
        
        # === STREAMING ===
        "/api/stream": {
            "method": "GET",
            "requests_per_minute": 100,
            "requests_per_hour": 2000,
            "burst_limit": 30,
            "scope": "per_ip",
            "description": "Endpoints de streaming"
        },
        "/api/stream/subscribe": {
            "method": "POST",
            "requests_per_minute": 50,
            "requests_per_hour": 800,
            "burst_limit": 15,
            "scope": "per_user",
            "description": "Suscripción a streams"
        },
        
        # === WEB SCRAPING ===
        "/api/scraping/scrape": {
            "method": "POST",
            "requests_per_minute": 20,
            "requests_per_hour": 200,
            "burst_limit": 5,
            "scope": "per_user",
            "description": "Operaciones de web scraping"
        },
        "/api/scraping/status": {
            "method": "GET",
            "requests_per_minute": 40,
            "requests_per_hour": 600,
            "burst_limit": 15,
            "scope": "per_ip",
            "description": "Estado de scraping"
        },
        
        # === PROCESAMIENTO DE ARCHIVOS ===
        "/api/files/upload": {
            "method": "POST",
            "requests_per_minute": 15,
            "requests_per_hour": 150,
            "burst_limit": 5,
            "scope": "per_user",
            "description": "Subida de archivos"
        },
        "/api/files/process": {
            "method": "POST",
            "requests_per_minute": 25,
            "requests_per_hour": 250,
            "burst_limit": 8,
            "scope": "per_user",
            "description": "Procesamiento de archivos"
        },
        "/api/files/download": {
            "method": "GET",
            "requests_per_minute": 40,
            "requests_per_hour": 600,
            "burst_limit": 15,
            "scope": "per_ip",
            "description": "Descarga de archivos"
        },
        
        # === OPERACIONES GIT ===
        "/api/git/clone": {
            "method": "POST",
            "requests_per_minute": 5,
            "requests_per_hour": 50,
            "burst_limit": 2,
            "scope": "per_user",
            "description": "Clonar repositorios"
        },
        "/api/git/push": {
            "method": "POST",
            "requests_per_minute": 10,
            "requests_per_hour": 100,
            "burst_limit": 3,
            "scope": "per_user",
            "description": "Push a repositorios"
        },
        "/api/git/pull": {
            "method": "POST",
            "requests_per_minute": 8,
            "requests_per_hour": 80,
            "burst_limit": 3,
            "scope": "per_user",
            "description": "Pull de repositorios"
        },
        
        # === PYTHON EXECUTOR ===
        "/api/python/execute": {
            "method": "POST",
            "requests_per_minute": 40,
            "requests_per_hour": 600,
            "burst_limit": 15,
            "scope": "per_user",
            "description": "Ejecución de código Python"
        },
        "/api/python/sandbox": {
            "method": "POST",
            "requests_per_minute": 20,
            "requests_per_hour": 300,
            "burst_limit": 8,
            "scope": "per_user",
            "description": "Ejecución en sandbox"
        },
        
        # === AUTENTICACIÓN ===
        "/api/auth/login": {
            "method": "POST",
            "requests_per_minute": 5,
            "requests_per_hour": 50,
            "burst_limit": 3,
            "scope": "per_ip",
            "description": "Inicio de sesión"
        },
        "/api/auth/refresh": {
            "method": "POST", 
            "requests_per_minute": 10,
            "requests_per_hour": 100,
            "burst_limit": 5,
            "scope": "per_user",
            "description": "Renovación de tokens"
        },
        "/api/auth/mfa": {
            "method": "POST",
            "requests_per_minute": 3,
            "requests_per_hour": 30,
            "burst_limit": 2,
            "scope": "per_ip",
            "description": "Autenticación multi-factor"
        }
    },
    
    # Reglas geográficas para MCP
    "geographic_rules": [
        {
            "country_code": "CN",  # China - rate limiting severo
            "action": "rate_limit",
            "rate_limit_factor": 0.1,  # 10% del límite normal
            "threat_score_multiplier": 3.0,
            "description": "Rate limiting severo para China"
        },
        {
            "country_code": "RU",  # Rusia - monitoreo intensivo
            "action": "monitor",
            "threat_score_multiplier": 2.0,
            "description": "Monitoreo intensivo para Rusia"
        },
        {
            "country_code": "KP",  # Corea del Norte - bloqueo completo
            "action": "block",
            "threat_score_multiplier": 5.0,
            "description": "Bloqueo completo para Corea del Norte"
        },
        {
            "country_code": "IR",  # Irán - rate limiting
            "action": "rate_limit",
            "rate_limit_factor": 0.2,
            "threat_score_multiplier": 2.5,
            "description": "Rate limiting para Irán"
        },
        {
            "country_code": "SY",  # Siria - bloqueo
            "action": "block",
            "threat_score_multiplier": 4.0,
            "description": "Bloqueo para Siria"
        }
    ],
    
    # Configuración de detección de amenazas para MCP
    "threat_detection": {
        "enabled": True,
        "ml_model_path": os.getenv("THREAT_DETECTION_MODEL_PATH"),
        "behavioral_analysis": True,
        "pattern_matching": True,
        "rate_anomaly_detection": True,
        "mcp_specific_patterns": {
            "agent_execution_abuse": [
                "infinite loop",
                "memory exhaustion",
                "recursive calls",
                "unauthorized system access"
            ],
            "orchestrator_abuse": [
                "agent cascade attacks",
                "resource exhaustion",
                "collaboration flood"
            ],
            "database_abuse": [
                "large data extraction",
                "schema reconnaissance",
                "query injection"
            ]
        }
    },
    
    # Respuesta automatizada específica para MCP
    "auto_response": {
        "enabled": True,
        "escalation_rules": {
            "low": {
                "action": "monitor",
                "block_duration": 0,
                "log_level": "info"
            },
            "medium": {
                "action": "rate_limit",
                "rate_limit_factor": 0.5,
                "block_duration": 300,  # 5 minutos
                "log_level": "warning"
            },
            "high": {
                "action": "block",
                "block_duration": 3600,  # 1 hora
                "log_level": "error",
                "notify_admin": True
            },
            "critical": {
                "action": "block",
                "block_duration": 86400,  # 24 horas
                "log_level": "critical",
                "notify_admin": True,
                "send_to_waf": True
            }
        }
    },
    
    # Traffic shaping específico para MCP
    "traffic_shaping": {
        "enabled": True,
        "burst_protection": True,
        "slow_start": True,
        "congestion_control": True,
        "mcp_specific_limits": {
            "per_ip": 1024 * 1024,  # 1MB/s por IP
            "per_user": 10 * 1024 * 1024,  # 10MB/s por usuario
            "agent_execution": 5 * 1024 * 1024,  # 5MB/s para ejecución de agentes
            "orchestrator_operations": 20 * 1024 * 1024,  # 20MB/s para orquestador
            "database_queries": 50 * 1024 * 1024,  # 50MB/s para queries DB
            "global": 100 * 1024 * 1024  # 100MB/s global
        }
    },
    
    # Monitoreo específico para MCP
    "monitoring": {
        "metrics_enabled": True,
        "mcp_specific_alerts": {
            "agent_execution_failures": 10,
            "orchestrator_overload": 0.8,  # 80% de carga
            "database_connection_pool": 0.9,  # 90% del pool de conexiones
            "memory_usage": 0.85,  # 85% de uso de memoria
            "disk_space": 0.9  # 90% de uso de disco
        },
        "alert_thresholds": {
            "requests_per_second": 500,
            "blocked_requests_ratio": 0.15,  # 15%
            "threat_level": "medium",
            "cpu_usage": 80,
            "memory_usage": 85
        },
        "alert_channels": {
            "email": {
                "enabled": bool(os.getenv("EMAIL_ALERTS_ENABLED", "false").lower() == "true"),
                "recipients": os.getenv("ALERT_EMAIL_RECIPIENTS", "").split(","),
                "smtp_server": os.getenv("SMTP_SERVER"),
                "smtp_port": int(os.getenv("SMTP_PORT", "587")),
                "smtp_username": os.getenv("SMTP_USERNAME"),
                "smtp_password": os.getenv("SMTP_PASSWORD")
            },
            "slack": {
                "enabled": bool(os.getenv("SLACK_ALERTS_ENABLED", "false").lower() == "true"),
                "webhook_url": os.getenv("SLACK_WEBHOOK_URL"),
                "channel": os.getenv("SLACK_CHANNEL", "#security-alerts")
            }
        }
    },
    
    # Integración WAF específica para MCP
    "waf_integration": {
        "cloudflare": {
            "enabled": bool(os.getenv("CLOUDFLARE_ENABLED", "false").lower() == "true"),
            "auto_block_critical": True,
            "block_duration": 3600,
            "rate_limit_rule_name": "MCP_Core_Rate_Limit"
        },
        "aws_waf": {
            "enabled": bool(os.getenv("AWS_WAF_ENABLED", "false").lower() == "true"),
            "rule_priority": 100,
            "rule_action": "BLOCK",
            "custom_headers": {
                "X-MCP-Request": "true",
                "X-MCP-Protection": "enabled"
            }
        }
    }
}


def get_mcp_config(environment: str = "production") -> Dict[str, Any]:
    """Obtiene configuración específica para el entorno MCP"""
    config = MCP_DDOS_CONFIG.copy()
    
    if environment == "development":
        # Configuración menos restrictiva para desarrollo
        config["rate_limits"]["default"]["requests_per_minute"] = 1000
        config["rate_limits"]["default"]["requests_per_hour"] = 10000
        
        # Ajustar límites específicos para desarrollo
        for endpoint, settings in config["rate_limits"].items():
            if endpoint != "default":
                settings["requests_per_minute"] *= 5
                settings["requests_per_hour"] *= 5
        
        config["monitoring"]["alert_thresholds"]["requests_per_second"] = 5000
        config["traffic_shaping"]["mcp_specific_limits"]["per_ip"] = 10 * 1024 * 1024
        
        # Desactivar algunas reglas geográficas en desarrollo
        config["geographic_rules"] = []
        
    elif environment == "staging":
        # Configuración intermedia para staging
        config["rate_limits"]["default"]["requests_per_minute"] = 500
        config["rate_limits"]["default"]["requests_per_hour"] = 5000
        config["monitoring"]["alert_thresholds"]["requests_per_second"] = 2000
        config["traffic_shaping"]["mcp_specific_limits"]["per_ip"] = 5 * 1024 * 1024
        
    elif environment == "testing":
        # Configuración muy permisiva para tests
        config["rate_limits"]["default"]["requests_per_minute"] = 10000
        config["rate_limits"]["default"]["requests_per_hour"] = 100000
        config["threat_detection"]["enabled"] = False
        config["auto_response"]["enabled"] = False
        config["geographic_rules"] = []
        
    return config