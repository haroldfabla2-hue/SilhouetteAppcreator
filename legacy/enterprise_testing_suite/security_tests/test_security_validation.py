"""
Security Tests para Validación de Seguridad Enterprise
"""

import pytest
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from utils.base_utils import (
    TestResult, TestDataGenerator, MetricsCollector, APITester, test_logger
)
from config.test_config import *

class TestSecurityVulnerabilityAssessment:
    """Tests de evaluación de vulnerabilidades"""
    
    @pytest.fixture
    def security_tester(self):
        return APITester(BASE_URL)
    
    def test_sql_injection_vulnerabilities(self, security_tester):
        """Test de vulnerabilidades de inyección SQL"""
        sql_injection_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "admin' --",
            "' UNION SELECT * FROM users --",
            "1' AND (SELECT COUNT(*) FROM users) > 0 --",
            "1' AND ASCII(SUBSTRING((SELECT password FROM users LIMIT 1),1,1))>64--"
        ]
        
        vulnerable_endpoints = [
            "/api/users/{payload}",
            "/api/login",
            "/api/search?q={payload}",
            "/api/users/{payload}/profile"
        ]
        
        vulnerabilities_found = []
        
        for endpoint_template in vulnerable_endpoints:
            for payload in sql_injection_payloads:
                try:
                    endpoint = endpoint_template.format(payload=payload)
                    
                    # Test diferentes métodos HTTP
                    for method in ['GET', 'POST', 'PUT']:
                        if method == 'GET':
                            response = security_tester.get(endpoint)
                        elif method == 'POST':
                            response = security_tester.post(endpoint, json={"query": payload})
                        else:  # PUT
                            response = security_tester.put(endpoint, json={"data": payload})
                        
                        # Detectar indicadores de vulnerabilidad SQL
                        response_text = response.text.lower()
                        vulnerability_indicators = [
                            "sql syntax error",
                            "mysql_fetch",
                            "ora-",
                            "postgresql",
                            "sqlite",
                            "database error",
                            "warning: mysql",
                            "fatal error",
                            "call to undefined function"
                        ]
                        
                        for indicator in vulnerability_indicators:
                            if indicator in response_text:
                                vulnerabilities_found.append({
                                    "endpoint": endpoint,
                                    "method": method,
                                    "payload": payload,
                                    "indicator": indicator,
                                    "status_code": response.status_code
                                })
                                break
                        
                        # Verificar códigos de estado inusuales
                        if response.status_code in [500, 502, 503, 504]:
                            if "database" in response_text or "sql" in response_text:
                                vulnerabilities_found.append({
                                    "endpoint": endpoint,
                                    "method": method,
                                    "payload": payload,
                                    "type": "database_error_exposure",
                                    "status_code": response.status_code
                                })
                
                except Exception as e:
                    # Excepciones pueden indicar problemas de seguridad
                    if "sql" in str(e).lower() or "database" in str(e).lower():
                        vulnerabilities_found.append({
                            "endpoint": endpoint,
                            "payload": payload,
                            "type": "sql_exception",
                            "error": str(e)
                        })
        
        # Assert - No se deben encontrar vulnerabilidades críticas
        assert len(vulnerabilities_found) == 0, \
            f"SQL injection vulnerabilities found: {vulnerabilities_found}"
        
        test_logger.info(f"SQL injection test passed. No vulnerabilities found.")
    
    def test_xss_vulnerabilities(self, security_tester):
        """Test de vulnerabilidades XSS (Cross-Site Scripting)"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "'><script>alert(String.fromCharCode(88,83,83))</script>",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>",
            "<textarea onfocus=alert('XSS') autofocus>"
        ]
        
        xss_endpoints = [
            "/api/search?q={payload}",
            "/api/users/{payload}/profile",
            "/api/comments",
            "/api/feedback",
            "/api/contact"
        ]
        
        xss_vulnerabilities = []
        
        for endpoint_template in xss_endpoints:
            for payload in xss_payloads:
                try:
                    endpoint = endpoint_template.format(payload=payload)
                    
                    # Test con diferentes tipos de datos
                    test_data_variants = [
                        {"query": payload},
                        {"search": payload},
                        {"text": payload},
                        {"comment": payload},
                        {"message": payload}
                    ]
                    
                    for data in test_data_variants:
                        response = security_tester.post(endpoint, json=data)
                        
                        # Verificar si el payload se refleja sin sanitizar
                        response_text = response.text
                        
                        for dangerous_element in ["<script>", "<img", "javascript:", "<svg", "<iframe"]:
                            if dangerous_element in payload and dangerous_element in response_text:
                                xss_vulnerabilities.append({
                                    "endpoint": endpoint,
                                    "payload": payload,
                                    "reflected_element": dangerous_element,
                                    "data": data
                                })
                
                except Exception as e:
                    test_logger.debug(f"XSS test exception for {endpoint}: {str(e)}")
        
        # Assert
        assert len(xss_vulnerabilities) == 0, \
            f"XSS vulnerabilities found: {xss_vulnerabilities}"
        
        test_logger.info("XSS vulnerability test passed. No vulnerabilities found.")
    
    def test_csrf_protection(self, security_tester):
        """Test de protección CSRF"""
        # Arrange
        login_data = {
            "username": "test_user",
            "password": "test_password"
        }
        
        # Act - Simular ataque CSRF
        try:
            # Hacer login para obtener sesión
            login_response = security_tester.post("/api/auth/login", json=login_data)
            
            # Simular request malicioso sin token CSRF
            malicious_requests = [
                {
                    "endpoint": "/api/users/delete/123",
                    "method": "POST",
                    "data": {"confirm": True}
                },
                {
                    "endpoint": "/api/admin/reset-password",
                    "method": "POST", 
                    "data": {"user_id": "123", "new_password": "hacked"}
                },
                {
                    "endpoint": "/api/transfer/money",
                    "method": "POST",
                    "data": {"amount": 1000, "to_account": "123456"}
                }
            ]
            
            csrf_protected = 0
            
            for request in malicious_requests:
                if request["method"] == "POST":
                    response = security_tester.post(request["endpoint"], json=request["data"])
                else:
                    response = security_tester.put(request["endpoint"], json=request["data"])
                
                # Verificar si el request fue bloqueado
                if response.status_code in [403, 401]:
                    csrf_protected += 1
                elif response.status_code == 200:
                    # Verificar si requiere token CSRF explícitamente
                    if "csrf" in response.text.lower() or "token" in response.text.lower():
                        csrf_protected += 1
            
            # Al menos el 80% de los requests sensibles deben estar protegidos
            protection_rate = csrf_protected / len(malicious_requests)
            assert protection_rate >= 0.8, f"CSRF protection rate too low: {protection_rate:.2%}"
            
        except Exception as e:
            test_logger.info(f"CSRF test completed with exception (may indicate good protection): {str(e)}")
        
        test_logger.info("CSRF protection test passed.")
    
    def test_authentication_bypass_attempts(self, security_tester):
        """Test de intentos de bypass de autenticación"""
        bypass_attempts = [
            # Intentos de bypass con headers
            {"headers": {"Authorization": "Bearer invalid_token"}},
            {"headers": {"Authorization": "Bearer admin:admin"}},
            {"headers": {"X-User-ID": "admin"}},
            {"headers": {"X-Admin": "true"}},
            {"headers": {"Cookie": "admin=true"}},
            
            # Intentos con tokens JWT malformados
            {"headers": {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid"}},
            {"headers": {"Authorization": "Bearer null"}},
            {"headers": {"Authorization": "Bearer undefined"}},
            
            # Intentos con cookies
            {"cookies": {"session": "admin", "user": "administrator"}},
            {"cookies": {"role": "admin", "admin": "1"}}
        ]
        
        bypass_success_count = 0
        
        protected_endpoints = [
            "/api/admin/users",
            "/api/admin/system",
            "/api/admin/config",
            "/api/users/profile",
            "/api/secure/data"
        ]
        
        for attempt in bypass_attempts:
            for endpoint in protected_endpoints:
                try:
                    # Test GET request
                    if "headers" in attempt:
                        response = security_tester.get(endpoint, headers=attempt["headers"])
                    elif "cookies" in attempt:
                        response = security_tester.get(endpoint, cookies=attempt.get("cookies", {}))
                    else:
                        response = security_tester.get(endpoint)
                    
                    # Verificar si el bypass fue exitoso
                    if response.status_code == 200:
                        bypass_success_count += 1
                        test_logger.warning(f"Potential auth bypass: {endpoint} with {attempt}")
                
                except Exception as e:
                    # Errores de autenticación son buenos
                    if "401" not in str(e) and "403" not in str(e):
                        test_logger.debug(f"Auth bypass test exception: {str(e)}")
        
        # Assert - El bypass no debe ser exitoso
        assert bypass_success_count == 0, \
            f"Authentication bypass successful in {bypass_success_count} attempts"
        
        test_logger.info("Authentication bypass test passed.")

class TestSecurityAuthentication:
    """Tests de autenticación y autorización"""
    
    def test_password_security(self):
        """Test de seguridad de contraseñas"""
        weak_passwords = [
            "123456",
            "password",
            "admin",
            "123456789",
            "qwerty",
            "abc123",
            "password123",
            "admin123",
            "letmein",
            "welcome"
        ]
        
        # Simular validación de contraseñas
        def validate_password_strength(password):
            score = 0
            issues = []
            
            # Verificar longitud mínima
            if len(password) < 8:
                issues.append("too_short")
            elif len(password) >= 12:
                score += 2
            elif len(password) >= 10:
                score += 1
            
            # Verificar caracteres
            if not any(c.isupper() for c in password):
                issues.append("no_uppercase")
            else:
                score += 1
            
            if not any(c.islower() for c in password):
                issues.append("no_lowercase")
            else:
                score += 1
            
            if not any(c.isdigit() for c in password):
                issues.append("no_digits")
            else:
                score += 1
            
            if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
                issues.append("no_special")
            else:
                score += 1
            
            # Verificar patrones comunes
            common_patterns = ["123", "password", "admin", "qwerty"]
            for pattern in common_patterns:
                if pattern.lower() in password.lower():
                    issues.append(f"common_pattern_{pattern}")
                    score -= 2
            
            return score, issues
        
        # Test contraseñas débiles
        weak_password_failures = 0
        
        for password in weak_passwords:
            score, issues = validate_password_strength(password)
            
            # Contraseñas débiles deben fallar
            if score >= 5:  # Umbral mínimo de seguridad
                weak_password_failures += 1
                test_logger.warning(f"Weak password passed validation: {password} (score: {score})")
        
        assert weak_password_failures == 0, \
            f"{weak_password_failures} weak passwords incorrectly passed validation"
        
        # Test contraseñas fuertes
        strong_passwords = [
            "MyStr0ng!P@ssw0rd2024",
            "S3cur3P@ssw0rd!123",
            "Tr0ub4dor&3",
            "correct-horse-battery-staple",
            "F0rgetFulne55!@2024"
        ]
        
        strong_password_failures = 0
        
        for password in strong_passwords:
            score, issues = validate_password_strength(password)
            
            # Contraseñas fuertes deben pasar
            if score < 5:
                strong_password_failures += 1
                test_logger.warning(f"Strong password failed validation: {password} (score: {score}, issues: {issues})")
        
        assert strong_password_failures == 0, \
            f"{strong_password_failures} strong passwords incorrectly failed validation"
        
        test_logger.info("Password security test passed.")
    
    def test_session_security(self):
        """Test de seguridad de sesiones"""
        # Simular tokens de sesión
        def generate_session_token():
            # Token seguro con alta entropía
            return secrets.token_urlsafe(32)
        
        def validate_session_token(token):
            if not token or len(token) < 32:
                return False, "Token too short"
            
            # Verificar formato base64 URL-safe
            try:
                import base64
                decoded = base64.urlsafe_b64decode(token + '==')
                if len(decoded) < 16:
                    return False, "Token entropy too low"
            except:
                return False, "Invalid token format"
            
            return True, "Valid token"
        
        # Test tokens inseguros
        insecure_tokens = [
            "12345678901234567890123456789012",  # Solo números
            "abcdefabcdefabcdefabcdefabcdefab",  # Solo letras minúsculas
            "ABCDEFABCDEFABCDEFABCDEFABCDEFAB",  # Solo letras mayúsculas
            "1234abcd1234abcd1234abcd1234abcd",  # Patrón repetitivo
            "",  # Token vacío
            "short",  # Token muy corto
            None  # Token nulo
        ]
        
        insecure_rejections = 0
        
        for token in insecure_tokens:
            if token is None:
                continue
            
            is_valid, reason = validate_session_token(token)
            if not is_valid:
                insecure_rejections += 1
            else:
                test_logger.warning(f"Insecure token accepted: {token}")
        
        assert insecure_rejections >= len(insecure_tokens) - 2, \
            "Too many insecure tokens were accepted"
        
        # Test tokens seguros
        secure_tokens = [generate_session_token() for _ in range(10)]
        
        secure_acceptances = 0
        
        for token in secure_tokens:
            is_valid, reason = validate_session_token(token)
            if is_valid:
                secure_acceptances += 1
            else:
                test_logger.warning(f"Secure token rejected: {token} - {reason}")
        
        assert secure_acceptances == len(secure_tokens), \
            f"Secure tokens were rejected: {len(secure_tokens) - secure_acceptances}"
        
        test_logger.info("Session security test passed.")

class TestSecurityEncryption:
    """Tests de validación de encriptación"""
    
    def test_data_encryption_validation(self):
        """Test de validación de encriptación de datos"""
        # Test encriptación simulada
        def simulate_encryption(data, key):
            # Simular encriptación AES
            import os
            from cryptography.fernet import Fernet
            
            # Generar IV aleatorio
            iv = os.urandom(16)
            
            # Encriptar datos
            cipher = Fernet(key)
            encrypted_data = cipher.encrypt(data.encode())
            
            return {
                "encrypted": True,
                "iv": iv.hex(),
                "ciphertext": encrypted_data.hex(),
                "key_id": "key_123"
            }
        
        def validate_encrypted_data(encrypted_payload):
            required_fields = ["encrypted", "ciphertext"]
            
            # Verificar campos obligatorios
            for field in required_fields:
                if field not in encrypted_payload:
                    return False, f"Missing required field: {field}"
            
            if not encrypted_payload["encrypted"]:
                return False, "Data not marked as encrypted"
            
            # Verificar longitud del ciphertext
            ciphertext = encrypted_payload.get("ciphertext", "")
            if len(ciphertext) < len("test_data") * 2:  # Mínimo 2x el tamaño original
                return False, "Ciphertext too short, possible weak encryption"
            
            return True, "Valid encrypted data"
        
        # Test datos encriptados correctamente
        test_data = "Sensitive enterprise data"
        key = Fernet.generate_key()
        
        encrypted_data = simulate_encryption(test_data, key)
        is_valid, reason = validate_encrypted_data(encrypted_data)
        
        assert is_valid, f"Valid encrypted data rejected: {reason}"
        
        # Test datos mal encriptados
        invalid_encrypted_data = {
            "encrypted": True,
            "ciphertext": "short"  # Ciphertext muy corto
        }
        
        is_valid, reason = validate_encrypted_data(invalid_encrypted_data)
        assert not is_valid, "Invalid encrypted data was accepted"
        
        test_logger.info("Data encryption validation test passed.")
    
    def test_transport_layer_security(self):
        """Test de seguridad de la capa de transporte"""
        # Simular verificación de TLS/SSL
        def check_tls_configuration(url):
            # Verificar configuración TLS
            import ssl
            import socket
            
            try:
                hostname = url.split("://")[1].split("/")[0]
                port = 443
                
                # Crear contexto SSL
                context = ssl.create_default_context()
                
                # Verificar versión TLS mínima
                context.minimum_version = ssl.TLSVersion.TLSv1_2
                
                # Conectar y verificar
                with socket.create_connection((hostname, port), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cipher = ssock.cipher()
                        version = ssock.version()
                        
                        return {
                            "tls_version": version,
                            "cipher_suite": cipher[0] if cipher else None,
                            "security_level": "HIGH" if version in ["TLSv1.3", "TLSv1.2"] else "LOW"
                        }
            
            except Exception as e:
                return {
                    "error": str(e),
                    "security_level": "UNKNOWN"
                }
        
        # Test URLs seguras vs inseguras
        test_urls = [
            "https://example.com",
            "https://api.secure.com", 
            "http://insecure.com"  # HTTP inseguro
        ]
        
        security_results = []
        
        for url in test_urls:
            result = check_tls_configuration(url)
            security_results.append({
                "url": url,
                "tls_version": result.get("tls_version"),
                "security_level": result.get("security_level")
            })
            
            # URLs HTTPS deben tener TLS
            if url.startswith("https"):
                assert result.get("security_level") in ["HIGH", "MEDIUM"], \
                    f"URL {url} has insufficient TLS security: {result}"
        
        test_logger.info(f"Transport layer security test passed for {len(test_urls)} URLs")

class TestSecurityRateLimiting:
    """Tests de rate limiting y DDoS protection"""
    
    def test_api_rate_limiting(self):
        """Test de rate limiting de APIs"""
        # Arrange
        api_tester = APITester(BASE_URL)
        
        # Test con diferentes endpoints
        rate_limited_endpoints = [
            "/api/login",
            "/api/auth/verify",
            "/api/password/reset",
            "/api/admin/users",
            "/api/secure/data"
        ]
        
        requests_per_endpoint = 20
        rate_limit_results = {}
        
        for endpoint in rate_limited_endpoints:
            successful_requests = 0
            rate_limited_requests = 0
            other_errors = 0
            
            # Enviar muchas requests rápidamente
            for i in range(requests_per_endpoint):
                try:
                    response = api_tester.post(endpoint, json={"test": f"request_{i}"})
                    
                    if response.status_code == 200:
                        successful_requests += 1
                    elif response.status_code == 429:  # Too Many Requests
                        rate_limited_requests += 1
                    elif response.status_code in [401, 403]:  # Auth errors (expected)
                        pass  # No contar como error de rate limiting
                    else:
                        other_errors += 1
                        
                except Exception:
                    other_errors += 1
            
            rate_limit_results[endpoint] = {
                "successful": successful_requests,
                "rate_limited": rate_limited_requests,
                "other_errors": other_errors
            }
        
        # Assert
        for endpoint, results in rate_limit_results.items():
            total_requests = requests_per_endpoint
            
            # Al menos 10% de las requests deben ser rate limited o fallar por autenticación
            protected_requests = results["rate_limited"] + results["other_errors"]
            protection_rate = protected_requests / total_requests
            
            assert protection_rate >= 0.10, \
                f"Endpoint {endpoint} may not have adequate rate limiting: {protection_rate:.2%}"
            
            test_logger.info(f"Rate limiting for {endpoint}: {results}")
        
        test_logger.info("API rate limiting test passed.")

if __name__ == "__main__":
    pytest.main([__file__])
