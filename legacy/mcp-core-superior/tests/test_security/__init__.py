"""
Test suite para el Sistema de Seguridad del MCP Core Superior

Cubre:
- Sistema de autenticación (JWT, OAuth)
- Rate limiting y DDoS protection
- Content scanning y security validation
- Auth middleware y utils
- Security configuration
"""

import pytest
import asyncio
import time
import hashlib
from unittest.mock import AsyncMock, MagicMock, patch, call
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json
import base64

# Test marks
pytestmark = [pytest.mark.security, pytest.mark.unit, pytest.mark.async_test]


class TestAuthSystem:
    """Tests para el sistema de autenticación"""
    
    @pytest.fixture
    def auth_system(self):
        """Fixture del sistema de autenticación"""
        from security.auth_system import AuthSystem
        return AuthSystem
    
    @pytest.fixture
    def mock_jwt(self):
        """Mock de JWT"""
        with patch('security.auth_system.jwt') as mock_jwt_module:
            mock_jwt_module.encode.return_value = "mock_jwt_token"
            mock_jwt_module.decode.return_value = {
                "user_id": "user123",
                "email": "test@example.com",
                "exp": int(time.time()) + 3600
            }
            yield mock_jwt_module
    
    async def test_auth_initialization(self, auth_system, mock_jwt):
        """Test de inicialización del sistema de auth"""
        system = auth_system()
        result = await system.initialize()
        
        assert result['success'] is True
        assert system.initialized is True
    
    async def test_user_authentication(self, auth_system, mock_jwt):
        """Test de autenticación de usuario"""
        system = auth_system()
        
        with patch.object(system, '_verify_password') as mock_verify:
            mock_verify.return_value = True
            
            with patch.object(system, '_create_user_session') as mock_session:
                mock_session.return_value = {
                    "session_id": "session123",
                    "token": "jwt_token",
                    "expires_at": "2025-11-04T06:43:15Z"
                }
                
                # Autenticar usuario
                result = await system.authenticate_user(
                    email="test@example.com",
                    password="password123"
                )
                
                assert result['success'] is True
                assert 'token' in result
                assert result['token'] == "jwt_token"
    
    async def test_jwt_token_generation(self, auth_system, mock_jwt):
        """Test de generación de tokens JWT"""
        system = auth_system()
        
        user_data = {
            "user_id": "user123",
            "email": "test@example.com",
            "role": "user"
        }
        
        token = system.generate_jwt_token(user_data)
        
        assert token == "mock_jwt_token"
        assert mock_jwt.encode.called
    
    async def test_jwt_token_validation(self, auth_system, mock_jwt):
        """Test de validación de tokens JWT"""
        system = auth_system()
        
        token = "valid_jwt_token"
        result = system.validate_jwt_token(token)
        
        assert result['valid'] is True
        assert 'user_id' in result
        assert result['user_id'] == "user123"
    
    async def test_token_expiration(self, auth_system, mock_jwt):
        """Test de expiración de tokens"""
        system = auth_system()
        
        # Simular token expirado
        expired_token_data = {
            "user_id": "user123",
            "exp": int(time.time()) - 3600  # Expirado hace 1 hora
        }
        
        with patch('security.auth_system.jwt.decode') as mock_decode:
            from jwt import ExpiredSignatureError
            mock_decode.side_effect = ExpiredSignatureError("Token expired")
            
            result = system.validate_jwt_token("expired_token")
            
            assert result['valid'] is False
            assert 'error' in result
            assert 'expired' in result['error'].lower()
    
    async def test_password_hashing(self, auth_system):
        """Test de hash de contraseñas"""
        system = auth_system()
        
        password = "password123"
        hash_result = system.hash_password(password)
        
        assert hash_result != password
        assert len(hash_result) == 64  # SHA-256 hash length
        assert hash_result == hashlib.sha256(password.encode()).hexdigest()
    
    async def test_password_verification(self, auth_system):
        """Test de verificación de contraseñas"""
        system = auth_system()
        
        password = "password123"
        hashed_password = system.hash_password(password)
        
        # Verificar contraseña correcta
        is_valid = system.verify_password(password, hashed_password)
        assert is_valid is True
        
        # Verificar contraseña incorrecta
        is_invalid = system.verify_password("wrongpassword", hashed_password)
        assert is_invalid is False
    
    async def test_session_management(self, auth_system):
        """Test de gestión de sesiones"""
        system = auth_system()
        
        # Crear sesión
        session_data = {
            "user_id": "user123",
            "email": "test@example.com",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0"
        }
        
        session = await system.create_session(session_data)
        
        assert 'session_id' in session
        assert 'token' in session
        assert 'expires_at' in session
        
        # Obtener sesión
        retrieved_session = await system.get_session(session['session_id'])
        assert retrieved_session is not None
        
        # Revocar sesión
        revoked = await system.revoke_session(session['session_id'])
        assert revoked is True
        
        # Verificar que se revocó
        revoked_session = await system.get_session(session['session_id'])
        assert revoked_session is None
    
    async def test_user_registration(self, auth_system):
        """Test de registro de usuarios"""
        system = auth_system()
        
        user_data = {
            "email": "newuser@example.com",
            "password": "securepass123",
            "name": "New User"
        }
        
        with patch.object(system, '_save_user') as mock_save:
            mock_save.return_value = True
            
            result = await system.register_user(user_data)
            
            assert result['success'] is True
            assert 'user_id' in result
            assert result['email'] == user_data['email']
    
    async def test_role_based_access(self, auth_system):
        """Test de control de acceso basado en roles"""
        system = auth_system()
        
        # Definir roles y permisos
        roles = {
            "admin": ["read", "write", "delete", "manage"],
            "user": ["read"],
            "guest": []
        }
        
        system.roles = roles
        
        # Verificar permisos
        assert system.check_permission("admin", "write") is True
        assert system.check_permission("user", "write") is False
        assert system.check_permission("guest", "read") is False
    
    async def test_multi_factor_auth(self, auth_system):
        """Test de autenticación de múltiples factores"""
        system = auth_system()
        
        # Simular setup de MFA
        with patch.object(system, '_generate_totp_secret') as mock_totp:
            mock_totp.return_value = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            
            mfa_setup = await system.setup_mfa("user123")
            
            assert mfa_setup['success'] is True
            assert 'secret' in mfa_setup
            assert 'qr_code' in mfa_setup
        
        # Simular verificación MFA
        with patch.object(system, '_verify_totp') as mock_verify:
            mock_verify.return_value = True
            
            mfa_result = await system.verify_mfa("user123", "123456")
            
            assert mfa_result['success'] is True
            assert mfa_result['verified'] is True


class TestAuthMiddleware:
    """Tests para middleware de autenticación"""
    
    @pytest.fixture
    def auth_middleware(self):
        """Fixture del middleware de autenticación"""
        from security.auth_middleware import AuthMiddleware
        return AuthMiddleware
    
    async def test_middleware_initialization(self, auth_middleware):
        """Test de inicialización del middleware"""
        middleware = auth_middleware()
        
        assert middleware is not None
        assert hasattr(middleware, 'auth_config')
    
    async def test_token_extraction(self, auth_middleware):
        """Test de extracción de tokens"""
        middleware = auth_middleware()
        
        # Simular request con token en header
        request = MagicMock()
        request.headers = {"Authorization": "Bearer test_token_123"}
        
        token = middleware.extract_token(request)
        
        assert token == "test_token_123"
    
    async def test_request_authentication(self, auth_middleware):
        """Test de autenticación de requests"""
        middleware = auth_middleware()
        
        with patch.object(middleware, '_validate_token') as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "user_id": "user123",
                "role": "user"
            }
            
            # Simular request autenticado
            request = MagicMock()
            request.headers = {"Authorization": "Bearer valid_token"}
            
            auth_result = await middleware.authenticate_request(request)
            
            assert auth_result['authenticated'] is True
            assert auth_result['user_id'] == "user123"
            assert auth_result['role'] == "user"
    
    async def test_request_authorization(self, auth_middleware):
        """Test de autorización de requests"""
        middleware = auth_middleware()
        
        # Configurar permisos
        middleware.role_permissions = {
            "admin": ["read", "write"],
            "user": ["read"]
        }
        
        # Request autorizado
        auth_context = {
            "user_id": "user123",
            "role": "user"
        }
        
        request_path = "/api/data"
        request_method = "GET"
        
        authorized = middleware.check_authorization(
            auth_context,
            request_path,
            request_method
        )
        
        assert authorized is True
        
        # Request no autorizado
        unauthorized = middleware.check_authorization(
            auth_context,
            "/api/admin",
            "POST"
        )
        
        assert unauthorized is False
    
    async def test_jwt_validation(self, auth_middleware):
        """Test de validación de JWT"""
        middleware = auth_middleware()
        
        with patch('security.auth_middleware.jwt') as mock_jwt:
            mock_jwt.decode.return_value = {
                "user_id": "user123",
                "exp": int(time.time()) + 3600
            }
            
            token = "valid_jwt_token"
            result = middleware._validate_jwt_token(token)
            
            assert result['valid'] is True
            assert 'user_id' in result
    
    async def test_authorization_header_handling(self, auth_middleware):
        """Test de manejo de headers de autorización"""
        middleware = auth_middleware()
        
        # Test diferentes formatos de Authorization header
        test_cases = [
            {"header": "Bearer token123", "expected": "token123"},
            {"header": "Basic dXNlcjpwYXNz", "expected": "Basic"},
            {"header": "Invalid format", "expected": None}
        ]
        
        for case in test_cases:
            request = MagicMock()
            request.headers = {"Authorization": case["header"]}
            
            if case["expected"]:
                token = middleware.extract_token(request)
                assert token == case["expected"]
            else:
                # Debería manejar formato inválido
                token = middleware.extract_token(request)
                assert token is None
    
    async def test_rate_limiting_integration(self, auth_middleware):
        """Test de integración con rate limiting"""
        middleware = auth_middleware()
        
        with patch.object(middleware, '_check_rate_limit') as mock_rate_limit:
            mock_rate_limit.return_value = True
            
            # Simular request con rate limiting
            auth_context = {"user_id": "user123", "ip": "192.168.1.100"}
            
            allowed = await middleware.check_rate_limit(auth_context)
            
            assert allowed is True
            mock_rate_limit.assert_called_once_with(auth_context)
    
    async def test_context_propagation(self, auth_middleware):
        """Test de propagación de contexto de autenticación"""
        middleware = auth_middleware()
        
        # Simular request autenticado
        request = MagicMock()
        request.headers = {"Authorization": "Bearer test_token"}
        request.client = MagicMock()
        request.client.host = "192.168.1.100"
        
        with patch.object(middleware, '_validate_token') as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "user_id": "user123",
                "role": "user",
                "permissions": ["read"]
            }
            
            # Procesar request
            auth_context = await middleware.process_request(request)
            
            # Verificar contexto propagado
            assert auth_context['authenticated'] is True
            assert auth_context['user_id'] == "user123"
            assert auth_context['role'] == "user"
            assert 'ip_address' in auth_context
            assert 'request_id' in auth_context


class TestAuthUtils:
    """Tests para utilidades de autenticación"""
    
    @pytest.fixture
    def auth_utils(self):
        """Fixture de utilidades de autenticación"""
        from security.auth_utils import AuthUtils
        return AuthUtils
    
    async def test_token_generation(self, auth_utils):
        """Test de generación de tokens"""
        payload = {
            "user_id": "user123",
            "email": "test@example.com",
            "role": "user"
        }
        
        token = auth_utils.generate_access_token(payload)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    async def test_token_validation(self, auth_utils):
        """Test de validación de tokens"""
        # Generar token válido
        payload = {"user_id": "user123"}
        token = auth_utils.generate_access_token(payload)
        
        # Validar token
        is_valid, payload_result = auth_utils.validate_token(token)
        
        assert is_valid is True
        assert payload_result['user_id'] == "user123"
    
    async def test_refresh_token(self, auth_utils):
        """Test de refresh tokens"""
        # Generar access token
        access_token = auth_utils.generate_access_token(
            {"user_id": "user123"},
            expires_delta=3600
        )
        
        # Generar refresh token
        refresh_token = auth_utils.generate_refresh_token(
            {"user_id": "user123"}
        )
        
        assert access_token != refresh_token
        
        # Usar refresh token para generar nuevo access token
        new_access_token = auth_utils.refresh_access_token(refresh_token)
        
        assert new_access_token != refresh_token
        assert isinstance(new_access_token, str)
    
    async def test_password_complexity(self, auth_utils):
        """Test de validación de complejidad de contraseñas"""
        # Contraseña válida
        valid_password = "SecurePass123!"
        assert auth_utils.validate_password_strength(valid_password) is True
        
        # Contraseñas inválidas
        weak_passwords = [
            "123456",  # Muy corta
            "password",  # Solo letras
            "12345678",  # Solo números
            "Password",  # Sin números
            "password123"  # Sin mayúsculas ni símbolos
        ]
        
        for weak_password in weak_passwords:
            result = auth_utils.validate_password_strength(weak_password)
            assert result is False
    
    async def test_session_token_generation(self, auth_utils):
        """Test de generación de tokens de sesión"""
        session_id = "session123"
        user_agent = "Mozilla/5.0"
        ip_address = "192.168.1.100"
        
        session_token = auth_utils.generate_session_token(
            session_id,
            user_agent,
            ip_address
        )
        
        assert isinstance(session_token, str)
        assert len(session_token) > 0
        
        # Verificar token
        is_valid, session_data = auth_utils.validate_session_token(
            session_token,
            user_agent,
            ip_address
        )
        
        assert is_valid is True
        assert session_data['session_id'] == session_id
    
    async def test_api_key_management(self, auth_utils):
        """Test de gestión de API keys"""
        # Generar API key
        api_key = auth_utils.generate_api_key(
            user_id="user123",
            permissions=["read", "write"],
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        assert isinstance(api_key, str)
        assert len(api_key) > 0
        
        # Validar API key
        is_valid, key_data = auth_utils.validate_api_key(api_key)
        
        assert is_valid is True
        assert key_data['user_id'] == "user123"
        assert 'read' in key_data['permissions']
    
    async def test_oauth_integration(self, auth_utils):
        """Test de integración OAuth"""
        # Simular datos de OAuth
        oauth_data = {
            "provider": "google",
            "provider_user_id": "google_user_123",
            "email": "test@example.com",
            "name": "Test User"
        }
        
        # Generar OAuth token
        oauth_token = auth_utils.generate_oauth_token(oauth_data)
        
        assert isinstance(oauth_token, str)
        
        # Validar OAuth token
        is_valid, oauth_result = auth_utils.validate_oauth_token(oauth_token)
        
        assert is_valid is True
        assert oauth_result['provider'] == "google"
    
    async def test_token_blacklisting(self, auth_utils):
        """Test de blacklisting de tokens"""
        # Generar token
        token = auth_utils.generate_access_token({"user_id": "user123"})
        
        # Agregar a blacklist
        auth_utils.blacklist_token(token)
        
        # Verificar que no se puede usar
        is_valid, _ = auth_utils.validate_token(token)
        assert is_valid is False
        
        # Verificar que está en blacklist
        assert auth_utils.is_token_blacklisted(token) is True


class TestDDOSProtection:
    """Tests para protección DDoS"""
    
    @pytest.fixture
    def ddos_protection(self):
        """Fixture de protección DDoS"""
        from security.ddos_protection import DDOSProtection
        return DDOSProtection
    
    async def test_protection_initialization(self, ddos_protection):
        """Test de inicialización de protección DDoS"""
        protection = ddos_protection()
        
        with patch('security.ddos_protection.redis') as mock_redis:
            mock_redis.Redis.return_value = MagicMock()
            
            result = await protection.initialize()
            
            assert result['success'] is True
            assert protection.initialized is True
    
    async def test_rate_limiting(self, ddos_protection):
        """Test de rate limiting"""
        protection = ddos_protection()
        
        with patch('security.ddos_protection.redis') as mock_redis:
            mock_client = MagicMock()
            mock_client.get.return_value = None  # No existe contador
            mock_client.set.return_value = True
            mock_client.incr.return_value = 1
            mock_redis.Redis.return_value = mock_client
            
            # Simular request
            client_ip = "192.168.1.100"
            result = await protection.check_rate_limit(
                client_ip,
                max_requests=100,
                window_seconds=60
            )
            
            assert result['allowed'] is True
            assert result['remaining'] == 99
    
    async def test_request_pattern_analysis(self, ddos_protection):
        """Test de análisis de patrones de request"""
        protection = ddos_protection()
        
        with patch('security.ddos_protection.redis') as mock_redis:
            mock_client = MagicMock()
            mock_redis.Redis.return_value = mock_client
            
            # Simular patrón sospechoso
            suspicious_requests = []
            for i in range(50):
                request = {
                    "ip": "192.168.1.100",
                    "endpoint": "/api/agents",
                    "timestamp": time.time() + i,
                    "user_agent": "suspicious-bot"
                }
                suspicious_requests.append(request)
            
            # Analizar patrón
            analysis = await protection.analyze_request_patterns(
                suspicious_requests
            )
            
            assert analysis['suspicious'] is True
            assert 'risk_score' in analysis
    
    async def test_ip_reputation_check(self, ddos_protection):
        """Test de verificación de reputación de IP"""
        protection = ddos_protection()
        
        with patch('security.ddos_protection.redis') as mock_redis:
            mock_client = MagicMock()
            mock_client.get.return_value = json.dumps({
                "reputation_score": 0.3,
                "last_reported": "2025-11-04T05:43:15Z",
                "threat_types": ["spam", "bot"]
            })
            mock_redis.Redis.return_value = mock_client
            
            # Verificar IP maliciosa
            reputation = await protection.check_ip_reputation("192.168.1.200")
            
            assert reputation['suspicious'] is True
            assert reputation['reputation_score'] < 0.5
            assert 'bot' in reputation['threat_types']
    
    async def test_challenge_verification(self, ddos_protection):
        """Test de verificación de challenges"""
        protection = ddos_protection()
        
        # Generar challenge
        challenge = protection.generate_challenge("192.168.1.100")
        
        assert 'challenge_id' in challenge
        assert 'question' in challenge
        assert 'answer_hash' in challenge
        
        # Resolver challenge correctamente
        correct_answer = protection.get_challenge_answer(challenge['challenge_id'])
        verification = protection.verify_challenge(
            challenge['challenge_id'],
            correct_answer
        )
        
        assert verification['valid'] is True
        
        # Intentar con respuesta incorrecta
        wrong_answer = "wrong_answer"
        invalid_verification = protection.verify_challenge(
            challenge['challenge_id'],
            wrong_answer
        )
        
        assert invalid_verification['valid'] is False
    
    async def test_traffic_blocking(self, ddos_protection):
        """Test de bloqueo de tráfico"""
        protection = ddos_protection()
        
        with patch('security.ddos_protection.redis') as mock_redis:
            mock_client = MagicMock()
            mock_redis.Redis.return_value = mock_client
            
            # Bloquear IP
            result = await protection.block_ip(
                "192.168.1.100",
                duration_seconds=3600,
                reason="Excessive requests"
            )
            
            assert result['blocked'] is True
            assert mock_client.setex.called
            
            # Verificar que IP está bloqueada
            is_blocked = protection.is_ip_blocked("192.168.1.100")
            assert is_blocked is True
    
    async def test_geographic_filtering(self, ddos_protection):
        """Test de filtrado geográfico"""
        protection = ddos_protection()
        
        # Configurar países bloqueados
        blocked_countries = ["CN", "RU", "KP"]
        protection.blocked_countries = blocked_countries
        
        # Simular IP de país bloqueado
        blocked_result = protection.check_geographic_filtering("203.0.113.1")
        assert blocked_result['blocked'] is True
        
        # Simular IP de país permitido
        with patch('security.ddos_protection.geoip') as mock_geoip:
            mock_geoip.country_code.return_value = "US"
            
            allowed_result = protection.check_geographic_filtering("198.51.100.1")
            assert allowed_result['blocked'] is False
    
    async def test_attack_detection(self, ddos_protection):
        """Test de detección de ataques"""
        protection = ddos_protection()
        
        # Simular flood de requests
        attack_data = []
        for i in range(1000):
            attack_data.append({
                "ip": "192.168.1.100",
                "timestamp": time.time(),
                "endpoint": "/api/agents",
                "method": "POST"
            })
        
        # Detectar ataque
        attack_detection = await protection.detect_attack(
            attack_data,
            threshold_requests=500,
            threshold_time=60
        )
        
        assert attack_detection['attack_detected'] is True
        assert 'attack_type' in attack_detection
        assert attack_detection['confidence'] > 0.8
    
    async def test_whitelist_management(self, ddos_protection):
        """Test de gestión de whitelist"""
        protection = ddos_protection()
        
        # Agregar IP a whitelist
        protection.add_to_whitelist("192.168.1.100", "Trusted server")
        
        assert protection.is_whitelisted("192.168.1.100") is True
        
        # Verificar que no se aplica rate limiting
        with patch.object(protection, 'check_rate_limit') as mock_check:
            # IP whitelisted debería pasar sin checks
            result = await protection.protect_request("192.168.1.100")
            
            assert result['protected'] is True
            # No debería llamar a rate limiting para IPs whitelisted
            mock_check.assert_not_called()


class TestSecuritySystem:
    """Tests para el sistema de seguridad general"""
    
    @pytest.fixture
    def security_system(self):
        """Fixture del sistema de seguridad"""
        from security.security_system import SecuritySystem
        return SecuritySystem
    
    async def test_system_initialization(self, security_system):
        """Test de inicialización del sistema de seguridad"""
        system = security_system()
        
        with patch.object(system, 'initialize_auth') as mock_auth:
            with patch.object(system, 'initialize_ddos_protection') as mock_ddos:
                with patch.object(system, 'initialize_middleware') as mock_middleware:
                    
                    result = await system.initialize()
                    
                    assert result['success'] is True
                    assert system.initialized is True
                    assert mock_auth.called
                    assert mock_ddos.called
                    assert mock_middleware.called
    
    async def test_security_configuration(self, security_system):
        """Test de configuración de seguridad"""
        system = security_system()
        
        config = {
            "auth": {
                "jwt_secret": "secret_key",
                "token_expiration": 3600,
                "password_policy": {
                    "min_length": 8,
                    "require_uppercase": True,
                    "require_numbers": True
                }
            },
            "ddos_protection": {
                "enabled": True,
                "max_requests_per_minute": 100,
                "blocked_countries": ["CN", "RU"]
            }
        }
        
        system.configure_security(config)
        
        assert system.auth_config['jwt_secret'] == "secret_key"
        assert system.ddos_config['max_requests_per_minute'] == 100
    
    async def test_comprehensive_security_check(self, security_system):
        """Test de verificación de seguridad integral"""
        system = security_system()
        
        # Mock de componentes
        with patch.object(system, 'authenticate_request') as mock_auth:
            with patch.object(system, 'check_rate_limit') as mock_rate:
                with patch.object(system, 'scan_content') as mock_scan:
                    
                    mock_auth.return_value = {"authenticated": True}
                    mock_rate.return_value = {"allowed": True}
                    mock_scan.return_value = {"safe": True}
                    
                    # Simular request de seguridad
                    security_result = await system.check_security(
                        request_data={
                            "headers": {"Authorization": "Bearer token"},
                            "body": {"content": "test content"}
                        }
                    )
                    
                    assert security_result['secure'] is True
                    assert mock_auth.called
                    assert mock_rate.called
                    assert mock_scan.called
    
    async def test_security_metrics(self, security_system):
        """Test de métricas de seguridad"""
        system = security_system()
        
        # Registrar eventos de seguridad
        system.record_security_event("authentication_attempt", {"success": True})
        system.record_security_event("rate_limit_triggered", {"ip": "192.168.1.100"})
        system.record_security_event("malicious_content_detected", {"content_type": "sql_injection"})
        
        # Obtener métricas
        metrics = system.get_security_metrics()
        
        assert 'authentication' in metrics
        assert 'rate_limiting' in metrics
        assert 'content_scanning' in metrics
        assert metrics['authentication']['total_attempts'] >= 1
    
    async def test_incident_response(self, security_system):
        """Test de respuesta a incidentes"""
        system = security_system()
        
        # Simular incidente de seguridad
        incident = {
            "type": "ddos_attack",
            "source_ip": "192.168.1.100",
            "severity": "high",
            "description": "High volume of requests detected"
        }
        
        # Simular respuesta automática
        with patch.object(system, 'auto_respond') as mock_respond:
            mock_respond.return_value = {"action": "ip_blocked", "success": True}
            
            response = await system.handle_security_incident(incident)
            
            assert response['handled'] is True
            assert mock_respond.called
    
    async def test_security_audit(self, security_system):
        """Test de auditoría de seguridad"""
        system = security_system()
        
        # Configurar logs de auditoría
        audit_events = [
            {"event": "login", "user_id": "user123", "timestamp": time.time()},
            {"event": "logout", "user_id": "user123", "timestamp": time.time() + 100},
            {"event": "permission_denied", "user_id": "user456", "timestamp": time.time() + 200}
        ]
        
        with patch.object(system, 'get_audit_logs') as mock_audit:
            mock_audit.return_value = audit_events
            
            audit_report = system.generate_audit_report(
                start_time=time.time() - 1000,
                end_time=time.time()
            )
            
            assert 'summary' in audit_report
            assert 'events' in audit_report
            assert len(audit_report['events']) == 3
    
    async def test_compliance_checking(self, security_system):
        """Test de verificación de cumplimiento"""
        system = security_system()
        
        # Verificar cumplimiento GDPR
        gdpr_compliance = system.check_compliance("gdpr")
        
        assert 'requirements' in gdpr_compliance
        assert 'compliance_score' in gdpr_compliance
        
        # Verificar cumplimiento de seguridad
        security_compliance = system.check_compliance("security")
        
        assert 'checks' in security_compliance
        assert 'overall_score' in security_compliance


class TestContentScanning:
    """Tests para escaneo de contenido"""
    
    @pytest.fixture
    def content_scanner(self):
        """Fixture del escáner de contenido"""
        from security.content_scanner import ContentScanner
        return ContentScanner
    
    async def test_sql_injection_detection(self, content_scanner):
        """Test de detección de inyección SQL"""
        scanner = content_scanner()
        
        # Contenido malicioso
        malicious_content = "'; DROP TABLE users; --"
        scan_result = await scanner.scan_content(malicious_content)
        
        assert scan_result['malicious'] is True
        assert 'sql_injection' in scan_result['threats']
    
    async def test_xss_detection(self, content_scanner):
        """Test de detección de XSS"""
        scanner = content_scanner()
        
        # Contenido con XSS
        xss_content = "<script>alert('xss')</script>"
        scan_result = await scanner.scan_content(xss_content)
        
        assert scan_result['malicious'] is True
        assert 'xss' in scan_result['threats']
    
    async def test_malware_detection(self, content_scanner):
        """Test de detección de malware"""
        scanner = content_scanner()
        
        # Simular contenido con patrón de malware
        malware_content = "eval(base64_decode('ZWNobyAnaGVsbG8gd29ybGQnKQ=='))"
        scan_result = await scanner.scan_content(malware_content)
        
        assert scan_result['malicious'] is True
        assert 'malware' in scan_result['threats']
    
    async def test_safe_content_validation(self, content_scanner):
        """Test de validación de contenido seguro"""
        scanner = content_scanner()
        
        # Contenido seguro
        safe_content = "This is a normal text content without any malicious patterns."
        scan_result = await scanner.scan_content(safe_content)
        
        assert scan_result['malicious'] is False
        assert scan_result['safe'] is True
    
    async def test_file_content_scanning(self, content_scanner):
        """Test de escaneo de archivos"""
        scanner = content_scanner()
        
        # Simular archivo con contenido sospechosos
        file_content = "virus_signature_pattern"
        
        scan_result = await scanner.scan_file_content(file_content)
        
        assert 'scan_result' in scan_result
        assert isinstance(scan_result['threats'], list)
    
    async def test_url_scanning(self, content_scanner):
        """Test de escaneo de URLs"""
        scanner = content_scanner()
        
        # URLs sospechosas
        suspicious_urls = [
            "http://malicious-site.com/payload",
            "https://phishing-site.com",
            "ftp://suspicious-upload.com"
        ]
        
        for url in suspicious_urls:
            scan_result = await scanner.scan_url(url)
            
            assert isinstance(scan_result, dict)
            assert 'safe' in scan_result
    
    async def test_regex_pattern_matching(self, content_scanner):
        """Test de coincidencia de patrones regex"""
        scanner = content_scanner()
        
        # Test de diferentes patrones maliciosos
        test_cases = [
            {
                "content": "SELECT * FROM users WHERE id = 1",
                "patterns": ["sql_injection"],
                "expected": True
            },
            {
                "content": "<img src=x onerror=alert('xss')>",
                "patterns": ["xss"],
                "expected": True
            },
            {
                "content": "Normal content without threats",
                "patterns": ["sql_injection", "xss"],
                "expected": False
            }
        ]
        
        for case in test_cases:
            matches = scanner._match_patterns(case['content'], case['patterns'])
            
            if case['expected']:
                assert len(matches) > 0
            else:
                assert len(matches) == 0


class TestSecurityConfig:
    """Tests para configuración de seguridad"""
    
    @pytest.fixture
    def security_config(self):
        """Fixture de configuración de seguridad"""
        from security.security_config import SecurityConfig
        return SecurityConfig
    
    async def test_auth_configuration(self, security_config):
        """Test de configuración de autenticación"""
        config = security_config()
        
        auth_settings = {
            "jwt_secret": "production_secret",
            "token_expiration": 3600,
            "password_policy": {
                "min_length": 12,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_numbers": True,
                "require_symbols": True,
                "max_age_days": 90
            },
            "session_timeout": 1800,
            "max_login_attempts": 3,
            "lockout_duration": 900
        }
        
        config.update_auth_config(auth_settings)
        
        assert config.jwt_secret == "production_secret"
        assert config.password_policy['min_length'] == 12
        assert config.max_login_attempts == 3
    
    async def test_rate_limiting_config(self, security_config):
        """Test de configuración de rate limiting"""
        config = security_config()
        
        rate_limit_settings = {
            "enabled": True,
            "global_limits": {
                "requests_per_minute": 1000,
                "requests_per_hour": 10000
            },
            "user_limits": {
                "requests_per_minute": 100,
                "requests_per_hour": 1000
            },
            "ip_limits": {
                "requests_per_minute": 50,
                "requests_per_hour": 500
            },
            "endpoint_limits": {
                "/api/auth/login": {"requests_per_minute": 5}
            }
        }
        
        config.update_rate_limit_config(rate_limit_settings)
        
        assert config.rate_limit_enabled is True
        assert config.global_limits['requests_per_minute'] == 1000
        assert config.endpoint_limits['/api/auth/login']['requests_per_minute'] == 5
    
    async def test_ddos_config(self, security_config):
        """Test de configuración DDoS"""
        config = security_config()
        
        ddos_settings = {
            "protection_level": "high",
            "thresholds": {
                "requests_per_second": 50,
                "concurrent_connections": 1000,
                "bandwidth_mbps": 100
            },
            "blocked_countries": ["CN", "RU", "KP"],
            "blocked_ips": ["192.168.1.100", "10.0.0.0/8"],
            "challenge_timeout": 30,
            "auto_block_duration": 3600
        }
        
        config.update_ddos_config(ddos_settings)
        
        assert config.ddos_protection_level == "high"
        assert config.thresholds['requests_per_second'] == 50
        assert "CN" in config.blocked_countries
    
    async def test_content_scanning_config(self, security_config):
        """Test de configuración de escaneo de contenido"""
        config = security_config()
        
        content_settings = {
            "enabled": True,
            "scan_types": ["sql_injection", "xss", "malware", "phishing"],
            "file_size_limit_mb": 50,
            "allowed_file_types": [".txt", ".pdf", ".doc", ".docx"],
            "blocked_domains": ["malicious-site.com", "phishing-site.net"],
            "threat_intelligence_feeds": [
                "feed1.json",
                "feed2.xml"
            ]
        }
        
        config.update_content_scanning_config(content_settings)
        
        assert config.content_scanning_enabled is True
        assert "xss" in config.scan_types
        assert "malicious-site.com" in config.blocked_domains
    
    async def test_audit_logging_config(self, security_config):
        """Test de configuración de auditoría"""
        config = security_config()
        
        audit_settings = {
            "enabled": True,
            "log_level": "INFO",
            "events_to_log": [
                "authentication",
                "authorization",
                "data_access",
                "admin_actions",
                "security_events"
            ],
            "log_retention_days": 90,
            "log_encryption": True,
            "real_time_alerts": True,
            "alert_channels": ["email", "slack", "pagerduty"]
        }
        
        config.update_audit_config(audit_settings)
        
        assert config.audit_logging_enabled is True
        assert "authentication" in config.events_to_log
        assert config.log_retention_days == 90
        assert "email" in config.alert_channels
    
    async def test_environment_specific_config(self, security_config):
        """Test de configuración específica por entorno"""
        config = security_config()
        
        # Configuración para desarrollo
        dev_config = config.get_env_config("development")
        assert dev_config['security']['debug'] is True
        assert dev_config['security']['rate_limit_enabled'] is False
        
        # Configuración para producción
        prod_config = config.get_env_config("production")
        assert prod_config['security']['debug'] is False
        assert prod_config['security']['rate_limit_enabled'] is True
        assert prod_config['security']['audit_logging_enabled'] is True
    
    async def test_configuration_validation(self, security_config):
        """Test de validación de configuración"""
        config = security_config()
        
        # Configuración válida
        valid_config = {
            "jwt_secret": "valid_secret_key_256_bits_long",
            "token_expiration": 3600,
            "rate_limit_enabled": True,
            "rate_limit_requests": 100
        }
        
        validation_result = config.validate_config(valid_config)
        assert validation_result['valid'] is True
        
        # Configuración inválida
        invalid_config = {
            "jwt_secret": "short",  # Muy corta
            "token_expiration": -1,  # Negativa
            "rate_limit_requests": 0  # Cero
        }
        
        validation_result = config.validate_config(invalid_config)
        assert validation_result['valid'] is False
        assert len(validation_result['errors']) > 0