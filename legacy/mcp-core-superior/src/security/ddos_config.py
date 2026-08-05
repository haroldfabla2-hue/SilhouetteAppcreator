"""
Configuración por defecto para el sistema de protección DDoS
"""

import os
from typing import Dict, Any

DEFAULT_DDOS_CONFIG: Dict[str, Any] = {
    # Configuración de Redis para rate limiting distribuido
    "redis": {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "password": os.getenv("REDIS_PASSWORD"),
        "db": int(os.getenv("REDIS_DB", "0")),
        "socket_timeout": 5,
        "socket_connect_timeout": 5,
        "retry_on_timeout": True
    },
    
    # Configuración de GeoIP para bloqueo geográfico
    "geoip": {
        "database_path": os.getenv("GEOIP_DATABASE_PATH", "/usr/share/GeoIP/GeoLite2-Country.mmdb"),
        "enabled": True
    },
    
    # Configuración de servicios WAF en la nube
    "waf": {
        "cloudflare": {
            "api_key": os.getenv("CLOUDFLARE_API_KEY"),
            "zone_id": os.getenv("CLOUDFLARE_ZONE_ID"),
            "enabled": False
        },
        "aws_waf": {
            "region": os.getenv("AWS_WAF_REGION", "us-east-1"),
            "web_acl_arn": os.getenv("AWS_WAF_WEB_ACL_ARN"),
            "enabled": False
        }
    },
    
    # Configuración de rate limits por endpoint
    "rate_limits": {
        # Rate limits por defecto para todos los endpoints
        "default": {
            "requests_per_minute": 100,
            "requests_per_hour": 1000,
            "burst_limit": 50,
            "scope": "per_ip"
        },
        
        # Endpoints específicos de la API de agentes
        "/api/agents/execute": {
            "method": "POST",
            "requests_per_minute": 30,
            "requests_per_hour": 500,
            "burst_limit": 10,
            "scope": "per_user"
        },
        
        "/api/agents/upload": {
            "method": "POST", 
            "requests_per_minute": 10,
            "requests_per_hour": 100,
            "burst_limit": 5,
            "scope": "per_user"
        },
        
        "/api/search": {
            "method": "POST",
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "burst_limit": 20,
            "scope": "per_ip"
        },
        
        "/api/orchestrator/execute": {
            "method": "POST",
            "requests_per_minute": 20,
            "requests_per_hour": 300,
            "burst_limit": 5,
            "scope": "per_user"
        },
        
        "/api/database/query": {
            "method": "POST",
            "requests_per_minute": 50,
            "requests_per_hour": 800,
            "burst_limit": 15,
            "scope": "per_user"
        },
        
        # Endpoints de streaming
        "/api/stream": {
            "method": "GET",
            "requests_per_minute": 100,
            "requests_per_hour": 2000,
            "burst_limit": 30,
            "scope": "per_ip"
        },
        
        # Endpoints de autenticación
        "/api/auth/login": {
            "method": "POST",
            "requests_per_minute": 5,
            "requests_per_hour": 50,
            "burst_limit": 3,
            "scope": "per_ip"
        },
        
        "/api/auth/refresh": {
            "method": "POST", 
            "requests_per_minute": 10,
            "requests_per_hour": 100,
            "burst_limit": 5,
            "scope": "per_user"
        }
    },
    
    # Reglas de bloqueo geográfico
    "geographic_rules": [
        {
            "country_code": "CN",  # China - rate limiting severo
            "action": "rate_limit",
            "rate_limit_factor": 0.1,
            "threat_score_multiplier": 3.0
        },
        {
            "country_code": "RU",  # Rusia - monitoreo
            "action": "monitor",
            "threat_score_multiplier": 2.0
        },
        {
            "country_code": "KP",  # Corea del Norte - bloqueo completo
            "action": "block",
            "threat_score_multiplier": 5.0
        }
    ],
    
    # Configuración de detección de amenazas
    "threat_detection": {
        "enabled": True,
        "ml_model_path": None,  # Ruta a modelo ML si está disponible
        "behavioral_analysis": True,
        "pattern_matching": True,
        "rate_anomaly_detection": True
    },
    
    # Configuración de respuesta automatizada
    "auto_response": {
        "enabled": True,
        "escalation_rules": {
            ThreatLevel.LOW: {
                "action": "monitor",
                "block_duration": 0
            },
            ThreatLevel.MEDIUM: {
                "action": "rate_limit",
                "rate_limit_factor": 0.5,
                "block_duration": 300  # 5 minutos
            },
            ThreatLevel.HIGH: {
                "action": "block",
                "block_duration": 3600  # 1 hora
            },
            ThreatLevel.CRITICAL: {
                "action": "block",
                "block_duration": 86400  # 24 horas
            }
        }
    },
    
    # Configuración de traffic shaping
    "traffic_shaping": {
        "enabled": True,
        "burst_protection": True,
        "slow_start": True,
        "congestion_control": True,
        "bandwidth_limits": {
            "per_ip": 1024 * 1024,  # 1MB/s por IP
            "per_user": 10 * 1024 * 1024,  # 10MB/s por usuario
            "global": 100 * 1024 * 1024  # 100MB/s global
        }
    },
    
    # Configuración de monitoreo y alertas
    "monitoring": {
        "metrics_enabled": True,
        "alert_thresholds": {
            "requests_per_second": 1000,
            "blocked_requests_ratio": 0.1,  # 10%
            "threat_level": "medium"
        },
        "alert_channels": {
            "email": {
                "enabled": False,
                "recipients": []
            },
            "slack": {
                "enabled": False,
                "webhook_url": None
            }
        }
    },
    
    # Configuración de integración con WAF
    "waf_integration": {
        "cloudflare": {
            "enabled": False,
            "auto_block_critical": True,
            "block_duration": 3600
        },
        "aws_waf": {
            "enabled": False,
            "rule_priority": 100,
            "rule_action": "BLOCK"
        }
    }
}


def get_config_for_environment(environment: str = "production") -> Dict[str, Any]:
    """Obtiene configuración específica para el entorno"""
    config = DEFAULT_DDOS_CONFIG.copy()
    
    if environment == "development":
        # Configuración menos restrictiva para desarrollo
        config["rate_limits"]["default"]["requests_per_minute"] = 1000
        config["rate_limits"]["default"]["requests_per_hour"] = 10000
        config["monitoring"]["alert_thresholds"]["requests_per_second"] = 5000
        config["traffic_shaping"]["bandwidth_limits"]["per_ip"] = 10 * 1024 * 1024
        
    elif environment == "staging":
        # Configuración intermedia para staging
        config["rate_limits"]["default"]["requests_per_minute"] = 500
        config["rate_limits"]["default"]["requests_per_hour"] = 5000
        config["monitoring"]["alert_thresholds"]["requests_per_second"] = 2000
        config["traffic_shaping"]["bandwidth_limits"]["per_ip"] = 5 * 1024 * 1024
        
    elif environment == "testing":
        # Configuración muy permisiva para tests
        config["rate_limits"]["default"]["requests_per_minute"] = 10000
        config["rate_limits"]["default"]["requests_per_hour"] = 100000
        config["threat_detection"]["enabled"] = False
        config["auto_response"]["enabled"] = False
        
    return config


def load_config_from_file(config_path: str) -> Dict[str, Any]:
    """Carga configuración desde archivo JSON"""
    import json
    try:
        with open(config_path, 'r') as f:
            file_config = json.load(f)
        
        # Merge con configuración por defecto
        config = DEFAULT_DDOS_CONFIG.copy()
        config.update(file_config)
        
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Archivo de configuración no encontrado: {config_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Error decodificando JSON en: {config_path}")