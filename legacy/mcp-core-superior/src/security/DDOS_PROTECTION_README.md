# Sistema de Rate Limiting y Protección DDoS - MCP Core Superior

## Descripción General

Sistema avanzado de protección contra ataques DDoS y rate limiting implementado para MCP Core Superior. Proporciona una capa de seguridad robusta con múltiples algoritmos, detección de amenazas, y respuesta automatizada.

## Características Principales

### 🛡️ Funcionalidades Implementadas

1. **Token Bucket Algorithm** - Rate limiting eficiente con refill automático
2. **Sliding Window Counters** - Contadores de ventana deslizante para límites precisos  
3. **Rate Limiting Multi-Alcance** - Por usuario, IP, agente, endpoint y operación
4. **Rate Limiting Distribuido** - Soporte para Redis y sistemas distribuidos
5. **Protección contra Bursts** - Traffic shaping y control de congestión
6. **Gestión de Blacklist/Whitelist** - Control granular de acceso
7. **Bloqueo Geográfico** - Restricciones por país usando GeoIP
8. **Detección de Anomalías** - ML para patrones de ataque
9. **Respuesta Automatizada** - Escalación automática de amenazas
10. **Integración WAF** - Cloudflare, AWS WAF, y otros servicios
11. **Configuración Flexible** - Por endpoint y operación
12. **Monitoreo en Tiempo Real** - Métricas y alertas avanzadas

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    DDoSProtectionSystem                     │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │ TokenBucket  │ │SlidingWindow │ │ ThreatDetect │         │
│  └──────────────┘ └──────────────┘ └──────────────┘         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │ GeoBlocker   │ │  WAF Integr  │ │  Admin Tools │         │
│  └──────────────┘ └──────────────┘ └──────────────┘         │
├─────────────────────────────────────────────────────────────┤
│              DistributedRateLimiter (Redis)                │
└─────────────────────────────────────────────────────────────┘
```

## Instalación y Configuración

### Requisitos

```bash
pip install redis geoip2 numpy scikit-learn python-geoip-geolite2
```

### Configuración Básica

```python
from src.security import (
    DDoSProtectionSystem,
    get_config_for_environment
)

# Configuración para entorno de producción
config = get_config_for_environment("production")

# Inicializar sistema
ddos_system = DDoSProtectionSystem(config)
```

### Variables de Entorno

```bash
# Redis para rate limiting distribuido
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password
REDIS_DB=0

# GeoIP database
GEOIP_DATABASE_PATH=/usr/share/GeoIP/GeoLite2-Country.mmdb

# Cloudflare WAF
CLOUDFLARE_API_KEY=your_api_key
CLOUDFLARE_ZONE_ID=your_zone_id

# AWS WAF
AWS_WAF_REGION=us-east-1
AWS_WAF_WEB_ACL_ARN=arn:aws:wafv2:...
```

## Uso con FastAPI

### Integración como Middleware

```python
from fastapi import FastAPI
from src.security import (
    DDoSProtectionSystem, 
    create_ddos_middleware,
    get_config_for_environment
)

app = FastAPI()

# Inicializar sistema DDoS
config = get_config_for_environment("production")
ddos_system = DDoSProtectionSystem(config)

# Añadir middleware
app.add_middleware(
    create_ddos_middleware(
        app=app,
        ddos_system=ddos_system,
        exclude_paths=["/health", "/metrics"],
        get_user_from_token=lambda request: request.headers.get("Authorization", "").split(" ")[-1]
    )
)

@app.get("/api/agents")
async def get_agents():
    return {"agents": []}
```

### Uso Manual

```python
from src.security import ddos_protect

@ddos_protect(ddos_system)
async def protected_endpoint(request: Request):
    allowed, reason, details = ddos_system.check_request(
        ip=request.client.host,
        user_agent=request.headers.get("user-agent"),
        endpoint=str(request.url.path),
        method=request.method,
        user_id=extract_user_id(request)
    )
    
    if not allowed:
        raise HTTPException(status_code=429, detail=reason)
    
    return {"message": "Allowed"}
```

## Configuración de Rate Limits

### Rate Limits por Endpoint

```python
from src.security import RateLimitConfig, RateLimitScope

# Configuración específica
config = RateLimitConfig(
    endpoint="/api/agents/execute",
    method="POST",
    requests_per_minute=30,
    requests_per_hour=500,
    burst_limit=10,
    scope=RateLimitScope.PER_USER
)

ddos_system.add_rate_limit_config(config)
```

### Configuración Global

```python
from src.security.ddos_config import DEFAULT_DDOS_CONFIG

# Personalizar configuración
custom_config = {
    "rate_limits": {
        "default": {
            "requests_per_minute": 100,
            "requests_per_hour": 1000,
            "scope": "per_ip"
        },
        "/api/agents/execute": {
            "method": "POST",
            "requests_per_minute": 20,
            "scope": "per_user"
        }
    }
}

# Aplicar configuración
ddos_system = DDoSProtectionSystem(custom_config)
```

## Bloqueo Geográfico

```python
from src.security import GeographicRule

# Bloquear país específico
rule = GeographicRule(
    country_code="CN",
    action="block"
)
ddos_system.geo_blocker.add_geographic_rule(rule)

# Rate limiting severo para otro país
rule2 = GeographicRule(
    country_code="RU", 
    action="rate_limit",
    rate_limit_factor=0.1  # 10% del límite normal
)
ddos_system.geo_blocker.add_geographic_rule(rule2)
```

## Gestión de Listas

### Whitelist (IPs Permitidas)

```python
# Añadir IP a whitelist
ddos_system.add_to_whitelist("192.168.1.100", duration=3600)  # 1 hora

# Verificar estado
whitelisted = ddos_system.whitelist

# Remover de whitelist
ddos_system.remove_from_whitelist("192.168.1.100")
```

### Blacklist (IPs Bloqueadas)

```python
# Bloquear IP
ddos_system.block_ip("192.168.1.200", duration=7200)  # 2 horas

# Desbloquear IP
ddos_system.unblock_ip("192.168.1.200")

# Verificar estado
blocked = ddos_system.blacklist
```

## Herramientas Administrativas

```python
from src.security import DDoSAdminTools, DDoSBulkOperations

admin = DDoSAdminTools(ddos_system)

# Monitoreo en tiempo real
stats = admin.get_real_time_stats()
print(f"Total requests: {stats['metrics']['total_requests']}")
print(f"Blocked: {stats['metrics']['blocked_requests']}")

# Operaciones en lote
bulk_ops = DDoSBulkOperations(ddos_system)

# Bloquear múltiples IPs
ips_to_block = ["192.168.1.100", "192.168.1.101", "192.168.1.102"]
bulk_ops.bulk_block_ips(ips_to_block, duration=3600)

# Generar reporte de amenazas
report = admin.generate_threat_report()
print(f"Top blocked IPs: {report.top_blocked_ips}")
```

## Integración con WAF

### Cloudflare

```python
# Configuración para Cloudflare
waf_config = {
    "cloudflare": {
        "api_key": "your_api_key",
        "zone_id": "your_zone_id",
        "enabled": True
    }
}

# El sistema automáticamente envía IPs críticas a Cloudflare
```

### AWS WAF

```python
# Configuración para AWS WAF
waf_config = {
    "aws_waf": {
        "region": "us-east-1",
        "web_acl_arn": "arn:aws:wafv2:...",
        "enabled": True
    }
}
```

## Detección de Amenazas

### Análisis Automático

```python
from src.security import ThreatLevel

# El sistema automáticamente detecta:
# - Inyecciones SQL
# - Ataques XSS  
# - Path traversal
# - Command injection
# - Traffic de bots
# - Patrones anómalos
```

### Respuesta Automatizada

```python
# Configurar respuesta automática
auto_response_config = {
    "auto_response": {
        "enabled": True,
        "escalation_rules": {
            ThreatLevel.LOW: {
                "action": "monitor"
            },
            ThreatLevel.MEDIUM: {
                "action": "rate_limit",
                "rate_limit_factor": 0.5
            },
            ThreatLevel.HIGH: {
                "action": "block", 
                "block_duration": 3600
            },
            ThreatLevel.CRITICAL: {
                "action": "block",
                "block_duration": 86400
            }
        }
    }
}
```

## Monitoreo y Alertas

```python
from src.security import DDoSMonitoring

monitoring = DDoSMonitoring(ddos_system, config)

# Verificar alertas
alerts = monitoring.check_alerts()
for alert in alerts:
    monitoring.send_alert(alert)

# Health check
health = ddos_system.health_check()
print(f"System status: {health['status']}")
```

## Métricas y Estadísticas

```python
# Obtener métricas completas
metrics = ddos_system.get_metrics()

# Métricas disponibles:
# - total_requests
# - blocked_requests  
# - rate_limited_requests
# - threat_events
# - ip_blocks
# - geographic_blocks

# Calcular ratios
if metrics['total_requests'] > 0:
    block_ratio = metrics['blocked_requests'] / metrics['total_requests']
    print(f"Blocked request ratio: {block_ratio:.2%}")
```

## Configuración por Entornos

### Desarrollo

```python
dev_config = get_config_for_environment("development")
# - Rate limits más permisivos
# - Menos alertas
```

### Staging

```python
staging_config = get_config_for_environment("staging")  
# - Rate limits intermedios
# - Monitoreo completo
```

### Producción

```python
prod_config = get_config_for_environment("production")
# - Rate limits restrictivos
# - Alertas completas
# - Integración WAF activa
```

## Ejemplo de Uso Completo

```python
#!/usr/bin/env python3
"""
Ejemplo completo de uso del sistema DDoS
"""

from src.security import (
    DDoSProtectionSystem,
    DDoSAdminTools,
    RateLimitConfig,
    RateLimitScope,
    get_config_for_environment
)

def main():
    # 1. Configurar sistema
    config = get_config_for_environment("production")
    ddos_system = DDoSProtectionSystem(config)
    
    # 2. Configurar rate limits específicos
    config = RateLimitConfig(
        endpoint="/api/agents/execute",
        method="POST", 
        requests_per_minute=20,
        scope=RateLimitScope.PER_USER
    )
    ddos_system.add_rate_limit_config(config)
    
    # 3. Configurar herramientas administrativas
    admin = DDoSAdminTools(ddos_system)
    
    # 4. Simular tráfico normal
    print("Testing normal traffic...")
    for i in range(5):
        allowed, reason, details = ddos_system.check_request(
            ip="192.168.1.100",
            user_agent="Mozilla/5.0",
            endpoint="/api/agents",
            method="GET"
        )
        print(f"Request {i+1}: {'Allowed' if allowed else 'Blocked'} - {reason}")
    
    # 5. Simular tráfico malicioso
    print("\nTesting malicious traffic...")
    malicious_ips = ["10.0.0.1", "10.0.0.2"]
    
    for ip in malicious_ips:
        for i in range(15):  # Intentar múltiples requests
            allowed, reason, details = ddos_system.check_request(
                ip=ip,
                user_agent="sqlmap/1.0",
                endpoint="/api/agents/execute", 
                method="POST",
                payload="'; DROP TABLE users; --"
            )
            if not allowed:
                print(f"Blocked malicious request from {ip}: {reason}")
                break
    
    # 6. Mostrar métricas finales
    print(f"\nFinal metrics:")
    metrics = ddos_system.get_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    # 7. Mostrar health status
    health = ddos_system.health_check()
    print(f"\nSystem health: {health['status']}")

if __name__ == "__main__":
    main()
```

## Testing

```bash
# Ejecutar tests
cd /workspace/mcp-core-superior/src/security
python test_ddos_protection.py

# Tests con pytest
pip install pytest
pytest test_ddos_protection.py -v
```

## Troubleshooting

### Redis no disponible
```python
# El sistema funciona en modo fail-open sin Redis
# Configurar alert para conectar Redis cuando esté disponible
```

### Base de datos GeoIP no encontrada
```python
# El sistema continúa funcionando sin bloqueo geográfico
# Descargar: wget https://geolite.maxmind.com/download/geoip/database/GeoLite2-Country.mmdb.gz
```

### Logs de debugging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
ddos_system.logger.setLevel(logging.DEBUG)
```

## Mejores Prácticas

1. **Configuración por endpoint**: Usar límites específicos para endpoints críticos
2. **Monitoreo continuo**: Configurar alertas para ratios de bloqueo altos
3. **Escalación gradual**: Implementar respuestas progresivas a amenazas
4. **Backup de configuración**: Exportar listas de IPs importantes
5. **Testing regular**: Ejecutar simulacros de ataques para validar configuraciones
6. **Logs detallados**: Mantener logs para análisis forense post-ataque

## Licencia

Este sistema forma parte de MCP Core Superior y sigue las mismas licencias de uso.