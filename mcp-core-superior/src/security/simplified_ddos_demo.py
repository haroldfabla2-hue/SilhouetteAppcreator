#!/usr/bin/env python3
"""
Ejemplo simplificado de integración del Sistema DDoS Protection con MCP Core Superior

Este ejemplo demuestra el funcionamiento básico del sistema sin dependencias externas
"""

import time
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Importar componentes del sistema
from ddos_protection import (
    DDoSProtectionSystem,
    TokenBucket,
    SlidingWindow,
    ThreatDetector,
    GeographicBlocker,
    ThreatLevel,
    RateLimitConfig,
    RateLimitScope
)

# Configuración de logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SimplifiedMCPExample:
    """Ejemplo simplificado del sistema DDoS para MCP"""
    
    def __init__(self):
        # Configuración básica sin Redis
        self.config = {
            "redis": None,  # Sin Redis para este ejemplo
            "geoip": {"database_path": None},
            "waf": {"cloudflare": {"enabled": False}},
            "rate_limits": {
                "default": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "burst_limit": 50,
                    "scope": "per_ip"
                },
                # Endpoints MCP específicos
                "/api/agents/execute": {
                    "method": "POST",
                    "requests_per_minute": 30,
                    "requests_per_hour": 500,
                    "burst_limit": 10,
                    "scope": "per_user"
                },
                "/api/orchestrator/execute": {
                    "method": "POST",
                    "requests_per_minute": 20,
                    "requests_per_hour": 300,
                    "burst_limit": 5,
                    "scope": "per_user"
                },
                "/api/search": {
                    "method": "POST",
                    "requests_per_minute": 60,
                    "requests_per_hour": 1000,
                    "burst_limit": 20,
                    "scope": "per_ip"
                }
            },
            "geographic_rules": [
                {
                    "country_code": "CN",
                    "action": "rate_limit",
                    "rate_limit_factor": 0.1
                }
            ],
            "threat_detection": {"enabled": True},
            "auto_response": {"enabled": True}
        }
        
        # Inicializar sistema
        self.ddos_system = DDoSProtectionSystem(self.config)
        
        # Configurar rate limits específicos
        self._setup_mcp_rate_limits()
        
        logger.info("Sistema DDoS inicializado para MCP Core Superior")
    
    def _setup_mcp_rate_limits(self):
        """Configura rate limits específicos para MCP"""
        
        # Rate limit específico para ejecución de agentes
        agent_config = RateLimitConfig(
            endpoint="/api/agents/execute",
            method="POST",
            requests_per_minute=25,
            requests_per_hour=400,
            burst_limit=8,
            scope=RateLimitScope.PER_USER
        )
        self.ddos_system.add_rate_limit_config(agent_config)
        
        # Rate limit para orquestador
        orchestrator_config = RateLimitConfig(
            endpoint="/api/orchestrator/execute",
            method="POST",
            requests_per_minute=15,
            requests_per_hour=200,
            burst_limit=3,
            scope=RateLimitScope.PER_USER
        )
        self.ddos_system.add_rate_limit_config(orchestrator_config)
        
        logger.info("Rate limits específicos para MCP configurados")
    
    def test_token_bucket(self):
        """Test del algoritmo Token Bucket"""
        print("\n🔄 Test de Token Bucket Algorithm")
        print("-" * 50)
        
        # Crear bucket con capacidad 10 y refill rate 2 tokens/segundo
        bucket = TokenBucket(capacity=10, refill_rate=2.0)
        
        print(f"Capacidad: {bucket.capacity} tokens")
        print(f"Refill rate: {bucket.refill_rate} tokens/segundo")
        print(f"Tokens iniciales: {bucket.remaining_tokens():.2f}")
        
        # Consumir tokens
        for i in range(12):
            can_consume = bucket.consume()
            remaining = bucket.remaining_tokens()
            print(f"Intento {i+1}: {'✓ Consumido' if can_consume else '✗ Rechazado'}, "
                  f"Restantes: {remaining:.2f}")
            
            if i == 6:  # Esperar 1 segundo en el medio
                time.sleep(1)
                print("   (Esperando 1 segundo para refill)")
    
    def test_sliding_window(self):
        """Test del contador de ventana deslizante"""
        print("\n📊 Test de Sliding Window Counter")
        print("-" * 50)
        
        # Crear ventana de 3 segundos
        window = SlidingWindow(window_size=3)
        
        print("Añadiendo requests cada 1 segundo...")
        
        for i in range(8):
            window.add_request()
            is_limited = window.is_rate_limited()
            count = window.get_request_count()
            
            print(f"Request {i+1}: Count={count}, Limited={is_limited}")
            
            time.sleep(1)  # Esperar 1 segundo entre requests
    
    def test_threat_detection(self):
        """Test de detección de amenazas"""
        print("\n🛡️ Test de Threat Detection")
        print("-" * 50)
        
        test_cases = [
            {
                "name": "Normal Request",
                "payload": '{"action": "execute", "command": "ls"}',
                "headers": {"user-agent": "MCP-Client/1.0"}
            },
            {
                "name": "SQL Injection Attempt",
                "payload": "'; DROP TABLE users; --",
                "headers": {"user-agent": "sqlmap/1.0"}
            },
            {
                "name": "XSS Attempt",
                "payload": "<script>alert('xss')</script>",
                "headers": {"user-agent": "browser"}
            },
            {
                "name": "Path Traversal",
                "payload": "../../../etc/passwd",
                "headers": {"user-agent": "wget"}
            },
            {
                "name": "Command Injection",
                "payload": "; rm -rf /",
                "headers": {"user-agent": "bash"}
            }
        ]
        
        for test_case in test_cases:
            threat_level = self.ddos_system.threat_detector.analyze_request(
                ip="192.168.1.100",
                user_agent=test_case["headers"]["user-agent"],
                endpoint="/api/agents/execute",
                headers=test_case["headers"],
                payload=test_case["payload"]
            )
            
            print(f"{test_case['name']:25} -> {threat_level.value.upper()}")
    
    def test_rate_limiting_scenarios(self):
        """Test de escenarios de rate limiting"""
        print("\n⏱️ Test de Rate Limiting Scenarios")
        print("-" * 50)
        
        scenarios = [
            {
                "name": "Usuario Normal",
                "user_id": "user_123",
                "endpoint": "/api/agents/execute",
                "method": "POST",
                "requests": 5,
                "ip": "192.168.1.100"
            },
            {
                "name": "Usuario Frecuente",
                "user_id": "user_456", 
                "endpoint": "/api/agents/execute",
                "method": "POST",
                "requests": 30,  # Más que el límite
                "ip": "192.168.1.101"
            },
            {
                "name": "Multiple IPs",
                "endpoint": "/api/search",
                "method": "POST",
                "requests": 10,
                "ips": ["10.0.0.1", "10.0.0.2", "10.0.0.3"]
            }
        ]
        
        for scenario in scenarios:
            print(f"\n📝 Escenario: {scenario['name']}")
            allowed_count = 0
            blocked_count = 0
            
            if "ips" in scenario:
                # Escenario con múltiples IPs
                for ip in scenario["ips"]:
                    for i in range(scenario["requests"]):
                        allowed, reason, details = self.ddos_system.check_request(
                            ip=ip,
                            user_agent="MCP-Client/1.0",
                            endpoint=scenario["endpoint"],
                            method=scenario["method"]
                        )
                        
                        if allowed:
                            allowed_count += 1
                        else:
                            blocked_count += 1
            else:
                # Escenario con usuario específico
                for i in range(scenario["requests"]):
                    allowed, reason, details = self.ddos_system.check_request(
                        ip=scenario["ip"],
                        user_agent="MCP-Client/1.0",
                        endpoint=scenario["endpoint"],
                        method=scenario["method"],
                        user_id=scenario.get("user_id")
                    )
                    
                    if allowed:
                        allowed_count += 1
                    else:
                        blocked_count += 1
            
            total = scenario["requests"] * len(scenario.get("ips", [1]))
            print(f"   Permitidas: {allowed_count}/{total}")
            print(f"   Bloqueadas: {blocked_count}/{total}")
            print(f"   Tasa de bloqueo: {(blocked_count/total)*100:.1f}%")
    
    def test_geographic_blocking(self):
        """Test de bloqueo geográfico"""
        print("\n🌍 Test de Geographic Blocking")
        print("-" * 50)
        
        # Añadir regla para China
        from ddos_protection import GeographicRule
        rule = GeographicRule(
            country_code="CN",
            action="rate_limit",
            rate_limit_factor=0.1
        )
        self.ddos_system.geo_blocker.add_geographic_rule(rule)
        
        # Simular IPs de diferentes países
        test_ips = [
            ("192.168.1.100", "Local", False),
            ("203.0.113.1", "China", True),  # IP simulada
            ("198.51.100.1", "US", False)
        ]
        
        for ip, country, should_be_limited in test_ips:
            is_blocked, reason = self.ddos_system.geo_blocker.check_geographic_block(ip)
            
            print(f"{country:10} ({ip:15}) -> "
                  f"{'BLOQUEADO' if is_blocked else 'PERMITIDO'} - {reason}")
    
    def test_admin_tools(self):
        """Test de herramientas administrativas"""
        print("\n🔧 Test de Herramientas Administrativas")
        print("-" * 50)
        
        # Simular herramientas administrativas
        print("1. Bloquear IP manualmente")
        self.ddos_system.block_ip("10.0.0.100", 1800, "Suspicious activity")
        
        print("2. Añadir IP a whitelist")
        self.ddos_system.add_to_whitelist("192.168.1.200", 3600)
        
        print("3. Verificar listas")
        print(f"   Blacklist: {list(self.ddos_system.blacklist)}")
        print(f"   Whitelist: {list(self.ddos_system.whitelist)}")
        
        print("4. Generar métricas")
        metrics = self.ddos_system.get_metrics()
        for key, value in metrics.items():
            print(f"   {key}: {value}")
    
    def run_comprehensive_simulation(self):
        """Ejecuta simulación comprehensiva del sistema MCP"""
        print("\n🎯 Simulación Comprehensiva MCP Core Superior")
        print("=" * 60)
        
        # Simular diferentes tipos de tráfico
        traffic_scenarios = [
            {
                "name": "Desarrollo Normal",
                "duration": 30,
                "requests_per_minute": 20,
                "malicious_ratio": 0.05
            },
            {
                "name": "Hora Pico",
                "duration": 60,
                "requests_per_minute": 100,
                "malicious_ratio": 0.02
            },
            {
                "name": "Posible Ataque",
                "duration": 30,
                "requests_per_minute": 200,
                "malicious_ratio": 0.30
            }
        ]
        
        for scenario in traffic_scenarios:
            print(f"\n🚦 Simulando: {scenario['name']}")
            print(f"   Duración: {scenario['duration']} segundos")
            print(f"   Requests/min: {scenario['requests_per_minute']}")
            print(f"   Ratio malicioso: {scenario['malicious_ratio']*100}%")
            
            # Reset metrics
            initial_metrics = self.ddos_system.get_metrics()
            
            # Simulate traffic
            start_time = time.time()
            request_count = 0
            allowed_count = 0
            blocked_count = 0
            
            while time.time() - start_time < scenario['duration']:
                # Generate request
                is_malicious = (request_count % int(1/scenario['malicious_ratio'])) == 0
                
                if is_malicious:
                    # Malicious request
                    allowed, reason, details = self.ddos_system.check_request(
                        ip="10.0.0." + str(1 + (request_count % 100)),
                        user_agent="malicious-bot/1.0",
                        endpoint="/api/agents/execute",
                        method="POST",
                        payload="'; DROP TABLE users; --"  # SQL injection
                    )
                else:
                    # Normal request
                    allowed, reason, details = self.ddos_system.check_request(
                        ip="192.168.1." + str(100 + (request_count % 50)),
                        user_agent="MCP-Client/1.0",
                        endpoint="/api/agents/execute",
                        method="POST",
                        user_id="user_" + str(request_count % 20)
                    )
                
                request_count += 1
                
                if allowed:
                    allowed_count += 1
                else:
                    blocked_count += 1
                
                # Simulate request rate
                time.sleep(60.0 / scenario['requests_per_minute'])
            
            # Results
            final_metrics = self.ddos_system.get_metrics()
            print(f"   Requests totales: {request_count}")
            print(f"   Permitidas: {allowed_count}")
            print(f"   Bloqueadas: {blocked_count}")
            print(f"   Tasa de bloqueo: {(blocked_count/request_count)*100:.1f}%")
            print(f"   Eventos de amenaza: {final_metrics['threat_events']}")


def main():
    """Función principal"""
    print("=" * 60)
    print("   SISTEMA DDoS PROTECTION - MCP CORE SUPERIOR")
    print("   Demostración Completa")
    print("=" * 60)
    
    # Inicializar sistema
    example = SimplifiedMCPExample()
    
    try:
        # Ejecutar tests básicos
        example.test_token_bucket()
        example.test_sliding_window()
        example.test_threat_detection()
        example.test_rate_limiting_scenarios()
        example.test_geographic_blocking()
        example.test_admin_tools()
        
        # Ejecutar simulación comprehensiva
        example.run_comprehensive_simulation()
        
        print("\n✅ Todos los tests completados exitosamente!")
        print("🎉 Sistema DDoS Protection funcionando correctamente!")
        
    except Exception as e:
        print(f"\n❌ Error durante la ejecución: {e}")
        logger.exception("Error in demonstration")


if __name__ == "__main__":
    main()