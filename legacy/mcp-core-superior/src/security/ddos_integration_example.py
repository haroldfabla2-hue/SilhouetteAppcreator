#!/usr/bin/env python3
"""
Ejemplo de Integración del Sistema DDoS Protection con MCP Core Superior

Este ejemplo muestra cómo integrar el sistema de protección DDoS con la aplicación
principal de MCP Core Superior, incluyendo configuración específica para los
endpoints de agentes y el orquestador.
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime

# Importar sistema DDoS
from ddos_protection import DDoSProtectionSystem
from ddos_config import get_config_for_environment, DEFAULT_DDOS_CONFIG
from ddos_middleware import create_ddos_middleware
from ddos_utils import DDoSAdminTools, DDoSMonitoring
from ddos_protection import RateLimitConfig, RateLimitScope

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MCPFastAPIDDoSIntegration:
    """
    Integración específica de DDoS protection con FastAPI para MCP Core Superior
    """
    
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.config = self._create_mcp_specific_config()
        self.ddos_system = DDoSProtectionSystem(self.config)
        self.admin_tools = DDoSAdminTools(self.ddos_system)
        self.monitoring = DDoSMonitoring(self.ddos_system, self.config)
        
        # Configurar rate limits específicos para MCP
        self._setup_mcp_rate_limits()
        
        logger.info("DDoS protection system initialized for MCP Core Superior")
    
    def _create_mcp_specific_config(self):
        """Crea configuración específica para MCP Core Superior"""
        config = get_config_for_environment(self.environment)
        
        # Rate limits específicos para endpoints MCP
        config["rate_limits"] = {
            "default": {
                "requests_per_minute": 100,
                "requests_per_hour": 1000,
                "burst_limit": 50,
                "scope": "per_ip"
            },
            
            # Endpoints de agentes MCP
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
            "/api/agents/status": {
                "method": "GET",
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
                "burst_limit": 20,
                "scope": "per_ip"
            },
            
            # Endpoints del orquestador
            "/api/orchestrator/execute": {
                "method": "POST",
                "requests_per_minute": 20,
                "requests_per_hour": 300,
                "burst_limit": 5,
                "scope": "per_user"
            },
            "/api/orchestrator/status": {
                "method": "GET",
                "requests_per_minute": 120,
                "requests_per_hour": 2000,
                "burst_limit": 30,
                "scope": "per_ip"
            },
            
            # Endpoints de database operations
            "/api/database/query": {
                "method": "POST",
                "requests_per_minute": 50,
                "requests_per_hour": 800,
                "burst_limit": 15,
                "scope": "per_user"
            },
            "/api/database/execute": {
                "method": "POST",
                "requests_per_minute": 30,
                "requests_per_hour": 500,
                "burst_limit": 10,
                "scope": "per_user"
            },
            
            # Endpoints de search engine
            "/api/search": {
                "method": "POST",
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
                "burst_limit": 20,
                "scope": "per_ip"
            },
            
            # Endpoints de streaming
            "/api/stream": {
                "method": "GET",
                "requests_per_minute": 100,
                "requests_per_hour": 2000,
                "burst_limit": 30,
                "scope": "per_ip"
            },
            
            # Endpoints de web scraping
            "/api/scraping/scrape": {
                "method": "POST",
                "requests_per_minute": 20,
                "requests_per_hour": 200,
                "burst_limit": 5,
                "scope": "per_user"
            },
            
            # Endpoints de file processing
            "/api/files/upload": {
                "method": "POST",
                "requests_per_minute": 15,
                "requests_per_hour": 150,
                "burst_limit": 5,
                "scope": "per_user"
            },
            "/api/files/process": {
                "method": "POST",
                "requests_per_minute": 25,
                "requests_per_hour": 250,
                "burst_limit": 8,
                "scope": "per_user"
            },
            
            # Endpoints de git operations
            "/api/git/clone": {
                "method": "POST",
                "requests_per_minute": 5,
                "requests_per_hour": 50,
                "burst_limit": 2,
                "scope": "per_user"
            },
            "/api/git/push": {
                "method": "POST",
                "requests_per_minute": 10,
                "requests_per_hour": 100,
                "burst_limit": 3,
                "scope": "per_user"
            },
            
            # Endpoints de Python executor
            "/api/python/execute": {
                "method": "POST",
                "requests_per_minute": 40,
                "requests_per_hour": 600,
                "burst_limit": 15,
                "scope": "per_user"
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
        }
        
        # Reglas geográficas específicas
        config["geographic_rules"] = [
            {
                "country_code": "CN",
                "action": "rate_limit",
                "rate_limit_factor": 0.1,  # 10% del límite normal
                "threat_score_multiplier": 3.0
            },
            {
                "country_code": "RU", 
                "action": "monitor",
                "threat_score_multiplier": 2.0
            },
            {
                "country_code": "KP",
                "action": "block",
                "threat_score_multiplier": 5.0
            }
        ]
        
        # Umbrales de alerta para MCP
        config["monitoring"]["alert_thresholds"] = {
            "requests_per_second": 500,
            "blocked_requests_ratio": 0.15,  # 15%
            "threat_level": "medium",
            "agent_execution_failures": 10,  # Fallos de ejecución de agentes
            "orchestrator_overload": 0.8  # 80% de carga
        }
        
        return config
    
    def _setup_mcp_rate_limits(self):
        """Configura rate limits específicos para MCP"""
        
        # Configuración específica para agentes críticos
        critical_agent_config = RateLimitConfig(
            endpoint="/api/agents/execute",
            method="POST",
            requests_per_minute=25,  # Más restrictivo
            requests_per_hour=400,
            burst_limit=8,
            scope=RateLimitScope.PER_USER
        )
        self.ddos_system.add_rate_limit_config(critical_agent_config)
        
        # Configuración para orquestador
        orchestrator_config = RateLimitConfig(
            endpoint="/api/orchestrator/execute", 
            method="POST",
            requests_per_minute=15,
            requests_per_hour=200,
            burst_limit=3,
            scope=RateLimitScope.PER_USER
        )
        self.ddos_system.add_rate_limit_config(orchestrator_config)
        
        logger.info("MCP-specific rate limits configured")
    
    def create_middleware_for_fastapi(self, app):
        """Crea middleware específico para FastAPI de MCP"""
        
        def get_user_from_token(request):
            """Extrae user ID del JWT token en MCP"""
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # En implementación real, decodificar JWT
                # Por ahora, simulación
                return "user_123"
            return None
        
        return create_ddos_middleware(
            app=app,
            ddos_system=self.ddos_system,
            exclude_paths=[
                "/health",
                "/metrics", 
                "/docs",
                "/redoc",
                "/openapi.json"
            ],
            get_user_from_token=get_user_from_token
        )
    
    def get_mcp_endpoint_health(self) -> dict:
        """Obtiene health check específico para endpoints MCP"""
        health = self.ddos_system.health_check()
        
        # Añadir información específica de MCP
        mcp_specific = {
            "mcp_endpoints_monitored": len(self.ddos_system.endpoint_configs),
            "agent_execution_protected": True,
            "orchestrator_protected": True,
            "database_operations_protected": True,
            "geographic_filtering_active": bool(self.ddos_system.geo_blocker.geoip_reader)
        }
        
        return {**health, "mcp_integration": mcp_specific}
    
    def get_mcp_metrics(self) -> dict:
        """Obtiene métricas específicas para MCP"""
        base_metrics = self.ddos_system.get_metrics()
        
        # Métricas específicas por endpoint MCP
        mcp_endpoints = [
            "/api/agents/execute",
            "/api/orchestrator/execute", 
            "/api/database/query",
            "/api/search"
        ]
        
        # Simular métricas por endpoint (en producción, usar BD real)
        endpoint_metrics = {}
        for endpoint in mcp_endpoints:
            endpoint_metrics[endpoint] = {
                "requests": base_metrics['total_requests'] // len(mcp_endpoints),
                "blocked": base_metrics['blocked_requests'] // len(mcp_endpoints),
                "rate_limited": base_metrics['rate_limited_requests'] // len(mcp_endpoints)
            }
        
        return {
            **base_metrics,
            "mcp_specific": {
                "protected_endpoints": len(mcp_endpoints),
                "endpoint_breakdown": endpoint_metrics,
                "total_protected_apis": len(self.ddos_system.endpoint_configs),
                "threat_level_distribution": {
                    "low": base_metrics['total_requests'] * 0.8,
                    "medium": base_metrics['total_requests'] * 0.15,
                    "high": base_metrics['total_requests'] * 0.04,
                    "critical": base_metrics['total_requests'] * 0.01
                }
            }
        }


def simulate_mcp_usage():
    """Simula uso del sistema MCP con diferentes tipos de tráfico"""
    
    print("🚀 Iniciando simulación de MCP Core Superior con DDoS Protection")
    
    # Inicializar sistema
    mcp_ddos = MCPFastAPIDDoSIntegration("development")
    
    # Simular diferentes tipos de tráfico
    test_scenarios = [
        {
            "name": "Normal User Traffic",
            "requests": 10,
            "ip": "192.168.1.100",
            "user_agent": "MCP-Client/1.0",
            "endpoint": "/api/agents",
            "method": "GET"
        },
        {
            "name": "Agent Execution",
            "requests": 5,
            "ip": "192.168.1.101", 
            "user_agent": "MCP-Agent-Client/2.0",
            "endpoint": "/api/agents/execute",
            "method": "POST",
            "user_id": "user_123"
        },
        {
            "name": "Orchestrator Task",
            "requests": 3,
            "ip": "192.168.1.102",
            "user_agent": "MCP-Orchestrator/1.0",
            "endpoint": "/api/orchestrator/execute",
            "method": "POST",
            "user_id": "admin_user"
        },
        {
            "name": "Malicious Traffic (SQL Injection)",
            "requests": 8,
            "ip": "10.0.0.50",
            "user_agent": "sqlmap/1.0",
            "endpoint": "/api/agents/execute",
            "method": "POST",
            "payload": "'; DROP TABLE users; --"
        },
        {
            "name": "Bot Traffic (High Volume)",
            "requests": 50,
            "ip": "203.0.113.100",
            "user_agent": "python-requests/2.28.1",
            "endpoint": "/api/search",
            "method": "POST"
        }
    ]
    
    # Ejecutar simulaciones
    for scenario in test_scenarios:
        print(f"\n📊 Simulando: {scenario['name']}")
        allowed_count = 0
        blocked_count = 0
        
        for i in range(scenario['requests']):
            allowed, reason, details = mcp_ddos.ddos_system.check_request(
                ip=scenario['ip'],
                user_agent=scenario['user_agent'],
                endpoint=scenario['endpoint'],
                method=scenario['method'],
                user_id=scenario.get('user_id'),
                payload=scenario.get('payload')
            )
            
            if allowed:
                allowed_count += 1
            else:
                blocked_count += 1
                print(f"   ❌ Request {i+1} blocked: {reason}")
        
        print(f"   ✅ Allowed: {allowed_count}/{scenario['requests']}")
        print(f"   🚫 Blocked: {blocked_count}/{scenario['requests']}")
    
    # Mostrar métricas finales
    print("\n📈 Métricas Finales:")
    metrics = mcp_ddos.get_mcp_metrics()
    for key, value in metrics.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for subkey, subvalue in value.items():
                print(f"    {subkey}: {subvalue}")
        else:
            print(f"  {key}: {value}")
    
    # Health check
    print("\n🏥 Health Check:")
    health = mcp_ddos.get_mcp_endpoint_health()
    print(f"  Status: {health['status']}")
    print(f"  Components: {health['components']}")
    print(f"  MCP Integration: {health.get('mcp_integration', {})}")
    
    print("\n✨ Simulación completada exitosamente!")


def demonstrate_admin_tools():
    """Demuestra el uso de herramientas administrativas"""
    
    print("\n🔧 Demostración de Herramientas Administrativas")
    
    mcp_ddos = MCPFastAPIDDoSIntegration("development")
    admin = mcp_ddos.admin_tools
    
    # Añadir IPs a listas
    print("📝 Añadiendo IPs a listas...")
    admin.add_whitelist_ip("192.168.1.200", duration=3600)
    admin.block_ip("10.0.0.100", duration=1800, reason="Suspicious activity")
    
    # Obtener listas actuales
    print(f"🌟 Whitelist: {admin.get_whitelisted_ips()}")
    print(f"🚫 Blacklist: {admin.get_blocked_ips()}")
    
    # Generar reporte de amenazas
    print("\n📊 Generando reporte de amenazas...")
    report = admin.generate_threat_report()
    print(f"  Total requests: {report.total_requests}")
    print(f"  Blocked requests: {report.blocked_requests}")
    print(f"  Rate limited requests: {report.rate_limited_requests}")
    print(f"  Threat events: {report.threat_events}")
    print(f"  Top blocked IPs: {report.top_blocked_ips}")
    
    # Estadísticas en tiempo real
    print("\n📱 Estadísticas en tiempo real:")
    stats = admin.get_real_time_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Reset estadísticas
    print("\n🔄 Reiniciando estadísticas...")
    admin.reset_statistics()
    print("  Estadísticas reiniciadas")


if __name__ == "__main__":
    print("=" * 60)
    print("   SISTEMA DDoS PROTECTION - MCP CORE SUPERIOR")
    print("   Ejemplo de Integración Completa")
    print("=" * 60)
    
    try:
        # Simular uso básico
        simulate_mcp_usage()
        
        # Demostrar herramientas administrativas
        demonstrate_admin_tools()
        
    except Exception as e:
        print(f"❌ Error durante la simulación: {e}")
        logger.exception("Simulation failed")