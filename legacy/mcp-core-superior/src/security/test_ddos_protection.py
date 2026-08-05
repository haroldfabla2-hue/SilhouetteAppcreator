"""
Tests para el sistema de protección DDoS
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from .ddos_protection import (
    DDoSProtectionSystem, 
    TokenBucket, 
    SlidingWindow, 
    ThreatDetector,
    GeographicBlocker,
    WAFIntegrator,
    ThreatLevel,
    RateLimitConfig,
    RateLimitScope
)
from .ddos_config import get_config_for_environment


class TestTokenBucket:
    """Tests para el algoritmo Token Bucket"""
    
    def test_token_bucket_basic(self):
        """Test básico del token bucket"""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)  # 1 token per second
        
        # Should allow initial requests
        assert bucket.consume() == True
        assert bucket.consume() == True
        assert bucket.remaining_tokens() >= 0
        
        # Fill to capacity
        time.sleep(1)
        assert bucket.remaining_tokens() > 0
    
    def test_token_bucket_refill(self):
        """Test de refill de tokens"""
        bucket = TokenBucket(capacity=5, refill_rate=2.0)
        
        # Consume all tokens
        for _ in range(5):
            assert bucket.consume() == True
        
        # Should be empty now
        assert bucket.consume() == False
        
        # Wait for refill
        time.sleep(1)
        assert bucket.consume() == True


class TestSlidingWindow:
    """Tests para el contador de ventana deslizante"""
    
    def test_sliding_window_basic(self):
        """Test básico del sliding window"""
        window = SlidingWindow(window_size=60)
        
        # Should allow initial requests
        for _ in range(10):
            window.add_request()
            assert not window.is_rate_limited()
    
    def test_sliding_window_cleanup(self):
        """Test de limpieza de ventana deslizante"""
        window = SlidingWindow(window_size=1)  # 1 second window
        
        # Add request
        window.add_request()
        assert not window.is_rate_limited()
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Window should be clean
        assert window.get_request_count() == 0


class TestThreatDetector:
    """Tests para el detector de amenazas"""
    
    def setUp(self):
        self.detector = ThreatDetector()
    
    def test_sql_injection_detection(self):
        """Detección de inyección SQL"""
        payload = "'; DROP TABLE users; --"
        headers = {}
        
        threat_level = self.detector.analyze_request(
            ip="192.168.1.1",
            user_agent="test",
            endpoint="/api/test",
            headers=headers,
            payload=payload
        )
        
        assert threat_level in [ThreatLevel.MEDIUM, ThreatLevel.HIGH]
    
    def test_xss_detection(self):
        """Detección de XSS"""
        payload = "<script>alert('xss')</script>"
        headers = {}
        
        threat_level = self.detector.analyze_request(
            ip="192.168.1.1", 
            user_agent="test",
            endpoint="/api/test",
            headers=headers,
            payload=payload
        )
        
        assert threat_level in [ThreatLevel.MEDIUM, ThreatLevel.HIGH]
    
    def test_path_traversal_detection(self):
        """Detección de path traversal"""
        payload = "../../../etc/passwd"
        headers = {}
        
        threat_level = self.detector.analyze_request(
            ip="192.168.1.1",
            user_agent="test", 
            endpoint="/api/test",
            headers=headers,
            payload=payload
        )
        
        assert threat_level in [ThreatLevel.MEDIUM, ThreatLevel.HIGH]


class TestDDoSProtectionSystem:
    """Tests para el sistema principal de protección DDoS"""
    
    def setUp(self):
        self.config = {
            "redis": {"host": "localhost", "port": 6379},
            "geoip": {"database_path": None},
            "waf": {"cloudflare": {"enabled": False}},
            "rate_limits": {
                "default": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "burst_limit": 50,
                    "scope": "per_ip"
                }
            }
        }
        self.ddos_system = DDoSProtectionSystem(self.config)
    
    def test_system_initialization(self):
        """Test de inicialización del sistema"""
        assert self.ddos_system is not None
        assert len(self.ddos_system.endpoint_configs) > 0
    
    def test_basic_request_allowed(self):
        """Test de request básica permitida"""
        allowed, reason, details = self.ddos_system.check_request(
            ip="192.168.1.100",
            user_agent="test-browser",
            endpoint="/api/agents",
            method="GET"
        )
        
        assert allowed == True
        assert reason == "Allowed"
        assert details['action'] == 'allow'
    
    def test_request_from_whitelisted_ip(self):
        """Test de request desde IP whitelist"""
        # Add IP to whitelist
        self.ddos_system.add_to_whitelist("192.168.1.100")
        
        allowed, reason, details = self.ddos_system.check_request(
            ip="192.168.1.100",
            user_agent="test-browser", 
            endpoint="/api/agents",
            method="GET"
        )
        
        assert allowed == True
        assert reason == "Whitelisted"
        assert details['action'] == 'allow'
    
    def test_request_from_blacklisted_ip(self):
        """Test de request desde IP blacklist"""
        # Add IP to blacklist
        self.ddos_system.block_ip("192.168.1.100")
        
        allowed, reason, details = self.ddos_system.check_request(
            ip="192.168.1.100",
            user_agent="test-browser",
            endpoint="/api/agents", 
            method="GET"
        )
        
        assert allowed == False
        assert reason == "IP blacklisted"
        assert details['action'] == 'block'
    
    def test_malicious_request_detection(self):
        """Test de detección de request maliciosa"""
        allowed, reason, details = self.ddos_system.check_request(
            ip="192.168.1.100",
            user_agent="sqlmap/1.0",  # Known malicious UA
            endpoint="/api/agents",
            method="POST",
            payload="'; DROP TABLE users; --"
        )
        
        # Should be blocked or rate limited
        assert allowed == False or details.get('action') == 'monitor'
    
    def test_rate_limiting_per_ip(self):
        """Test de rate limiting por IP"""
        # Configure very restrictive limits
        config = RateLimitConfig(
            endpoint="/api/test",
            method="POST",
            requests_per_minute=2,
            scope=RateLimitScope.PER_IP
        )
        self.ddos_system.add_rate_limit_config(config)
        
        # First request should be allowed
        allowed1, _, _ = self.ddos_system.check_request(
            ip="192.168.1.100",
            user_agent="test",
            endpoint="/api/test",
            method="POST"
        )
        assert allowed1 == True
        
        # Second request should be allowed
        allowed2, _, _ = self.ddos_system.check_request(
            ip="192.168.1.100", 
            user_agent="test",
            endpoint="/api/test",
            method="POST"
        )
        assert allowed2 == True
        
        # Mock Redis failure to test local rate limiting
        with patch.object(self.ddos_system.distributed_limiter, 'check_rate_limit', return_value=False):
            allowed3, reason, details = self.ddos_system.check_request(
                ip="192.168.1.100",
                user_agent="test", 
                endpoint="/api/test",
                method="POST"
            )
            assert allowed3 == False or "Rate limit" in reason
    
    def test_metrics_tracking(self):
        """Test de seguimiento de métricas"""
        initial_metrics = self.ddos_system.get_metrics()
        initial_total = initial_metrics['total_requests']
        
        # Make some requests
        for _ in range(5):
            self.ddos_system.check_request(
                ip="192.168.1.100",
                user_agent="test",
                endpoint="/api/test"
            )
        
        final_metrics = self.ddos_system.get_metrics()
        assert final_metrics['total_requests'] == initial_total + 5
    
    def test_health_check(self):
        """Test de health check del sistema"""
        health = self.ddos_system.health_check()
        
        assert 'status' in health
        assert 'components' in health
        assert 'redis' in health['components']
        assert 'geoip' in health['components']


class TestGeographicBlocker:
    """Tests para el bloqueador geográfico"""
    
    def setUp(self):
        self.blocker = GeographicBlocker()
    
    def test_blocker_initialization(self):
        """Test de inicialización del bloqueador"""
        assert self.blocker is not None
        assert len(self.blocker.country_rules) == 0
    
    def test_add_geographic_rule(self):
        """Test de añadir regla geográfica"""
        from .ddos_protection import GeographicRule
        
        rule = GeographicRule(
            country_code="CN",
            action="block"
        )
        
        self.blocker.add_geographic_rule(rule)
        assert "CN" in self.blocker.country_rules
    
    def test_check_geographic_block_no_rule(self):
        """Test de verificación sin reglas"""
        is_blocked, reason = self.blocker.check_geographic_block("192.168.1.1")
        assert is_blocked == False
        assert reason is None


class TestWAFIntegrator:
    """Tests para el integrador WAF"""
    
    def setUp(self):
        config = {
            'cloudflare_api_key': None,
            'aws_waf': {}
        }
        self.waf = WAFIntegrator(config)
    
    def test_waf_initialization(self):
        """Test de inicialización WAF"""
        assert self.waf is not None
    
    def test_send_threat_to_cloudflare_no_key(self):
        """Test de envío sin API key"""
        result = self.waf.send_threat_to_cloudflare("192.168.1.1", ThreatLevel.HIGH)
        assert result == False


class TestConfiguration:
    """Tests para configuraciones"""
    
    def test_default_config_loading(self):
        """Test de carga de configuración por defecto"""
        config = get_config_for_environment("development")
        
        assert "redis" in config
        assert "rate_limits" in config
        assert "geographic_rules" in config
        assert config['rate_limits']['default']['requests_per_minute'] == 1000
    
    def test_environment_specific_config(self):
        """Test de configuración específica por entorno"""
        dev_config = get_config_for_environment("development")
        prod_config = get_config_for_environment("production")
        test_config = get_config_for_environment("testing")
        
        assert dev_config['rate_limits']['default']['requests_per_minute'] > prod_config['rate_limits']['default']['requests_per_minute']
        assert test_config['threat_detection']['enabled'] == False


class TestIntegrationScenarios:
    """Tests de escenarios de integración"""
    
    def test_bot_detection_scenario(self):
        """Test de escenario de detección de bot"""
        config = {
            "redis": {"host": "localhost", "port": 6379},
            "geoip": {"database_path": None},
            "waf": {"cloudflare": {"enabled": False}},
            "rate_limits": {
                "default": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "burst_limit": 50,
                    "scope": "per_ip"
                }
            }
        }
        
        ddos_system = DDoSProtectionSystem(config)
        
        # Simular tráfico de bot
        bot_ua = "python-requests/2.28.1"
        
        # Multiple rapid requests from same IP
        for i in range(10):
            allowed, reason, details = ddos_system.check_request(
                ip="192.168.1.100",
                user_agent=bot_ua,
                endpoint="/api/agents/execute",
                method="POST",
                payload='{"action": "execute"}'
            )
            
            if i > 5:  # Should eventually be rate limited
                assert not allowed or "rate_limit" in reason.lower()
    
    def test_ddos_attack_simulation(self):
        """Test de simulación de ataque DDoS"""
        config = {
            "redis": {"host": "localhost", "port": 6379},
            "geoip": {"database_path": None},
            "waf": {"cloudflare": {"enabled": False}},
            "rate_limits": {
                "/api/agents/execute": {
                    "method": "POST",
                    "requests_per_minute": 30,
                    "requests_per_hour": 500,
                    "burst_limit": 10,
                    "scope": "per_ip"
                }
            }
        }
        
        ddos_system = DDoSProtectionSystem(config)
        
        # Simular ataque DDoS
        malicious_ips = ["192.168.1.{}".format(i) for i in range(1, 20)]
        
        blocked_count = 0
        for ip in malicious_ips:
            for _ in range(20):  # 20 requests per IP
                allowed, reason, details = ddos_system.check_request(
                    ip=ip,
                    user_agent="bot/1.0",
                    endpoint="/api/agents/execute",
                    method="POST"
                )
                
                if not allowed:
                    blocked_count += 1
        
        # Should have blocked a significant number of requests
        assert blocked_count > 50


if __name__ == "__main__":
    # Run basic tests
    print("Running DDoS Protection System Tests...")
    
    # Test token bucket
    test_bucket = TestTokenBucket()
    test_bucket.test_token_bucket_basic()
    print("✓ Token bucket tests passed")
    
    # Test sliding window
    test_window = TestSlidingWindow()
    test_window.test_sliding_window_basic()
    print("✓ Sliding window tests passed")
    
    # Test threat detection
    test_detector = TestThreatDetector()
    test_detector.setUp()
    test_detector.test_sql_injection_detection()
    test_detector.test_xss_detection()
    test_detector.test_path_traversal_detection()
    print("✓ Threat detection tests passed")
    
    # Test DDoS system
    test_system = TestDDoSProtectionSystem()
    test_system.setUp()
    test_system.test_system_initialization()
    test_system.test_basic_request_allowed()
    test_system.test_request_from_whitelisted_ip()
    test_system.test_malicious_request_detection()
    test_system.test_metrics_tracking()
    test_system.test_health_check()
    print("✓ DDoS system tests passed")
    
    print("\nAll tests completed successfully! 🎉")