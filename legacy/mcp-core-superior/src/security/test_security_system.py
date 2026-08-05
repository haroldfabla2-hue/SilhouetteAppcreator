"""
Pruebas del Sistema de Security Scanning y Data Redaction
Demuestra todas las funcionalidades implementadas
"""

import os
import sys
import json
import tempfile
from datetime import datetime
from typing import Dict, Any, List

# Agregar path para imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Importar directamente para evitar dependencias del __init__.py
from security_system import SecuritySystem, PIIDetector, SecurityScanner
from security_config import get_security_config, SecurityConfigManager


class SecuritySystemTester:
    """Suite de pruebas para el sistema de seguridad"""
    
    def __init__(self):
        self.config = get_security_config('testing')
        self.security_system = SecuritySystem({
            'rate_limit_db_path': '/tmp/security_test_ratelimit.db',
            'target_url': 'http://localhost:8080'
        })
        
        self.test_results = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'failures': []
        }
    
    def run_all_tests(self):
        """Ejecuta todas las pruebas del sistema"""
        print("=" * 80)
        print("INICIANDO PRUEBAS DEL SISTEMA DE SECURITY SCANNING Y DATA REDACTION")
        print("=" * 80)
        
        # Pruebas de PII Detection y Redaction
        self.test_pii_detection()
        self.test_pii_redaction()
        self.test_compliance_frameworks()
        
        # Pruebas de Code Security Scanning
        self.test_code_vulnerability_scanning()
        self.test_agent_security_scanning()
        
        # Pruebas de Input Validation
        self.test_input_validation_xss()
        self.test_input_validation_sql_injection()
        self.test_input_validation_path_traversal()
        
        # Pruebas de Rate Limiting
        self.test_rate_limiting()
        self.test_burst_protection()
        
        # Pruebas de File Upload Security
        self.test_file_upload_scanning()
        
        # Pruebas de Security Headers
        self.test_security_headers()
        
        # Pruebas de Vulnerability Scanning
        self.test_vulnerability_scanning()
        
        # Pruebas de Compliance
        self.test_compliance_assessment()
        
        # Pruebas de Integración
        self.test_end_to_end_security()
        
        # Generar reporte final
        self.generate_test_report()
    
    def test_pii_detection(self):
        """Prueba detección de PII"""
        print("\n🧪 Probando PII Detection...")
        
        test_data = """
        Contact Information:
        Email: john.doe@company.com
        Phone: +1 (555) 123-4567
        SSN: 123-45-6789
        Credit Card: 4111-1111-1111-1111
        IP Address: 192.168.1.100
        Passport: AB1234567
        Driver License: CD8765432
        """
        
        pii_detector = PIIDetector()
        detected_pii = pii_detector.detect_pii(test_data)
        
        expected_types = ['email', 'phone', 'ssn', 'credit_card', 'ip_address', 'passport', 'driver_license']
        detected_types = [p['type'] for p in detected_pii]
        
        self.test_results['tests_run'] += 1
        if all(pii_type in detected_types for pii_type in expected_types):
            print("✅ PII Detection: PASSED")
            print(f"   Detectados {len(detected_pii)} elementos PII: {detected_types}")
            self.test_results['tests_passed'] += 1
        else:
            print("❌ PII Detection: FAILED")
            print(f"   Esperados: {expected_types}")
            print(f"   Detectados: {detected_types}")
            self.test_results['tests_failed'] += 1
            self.test_results['failures'].append("PII Detection - Tipos no detectados correctamente")
    
    def test_pii_redaction(self):
        """Prueba redacción de PII"""
        print("\n🧪 Probando PII Redaction...")
        
        test_data = "User john.doe@email.com with phone (555) 123-4567"
        pii_detector = PIIDetector()
        
        # Redactar según GDPR
        redacted_gdpr = pii_detector.redact_pii(test_data, 'GDPR')
        
        # Verificar que los datos originales no están presentes
        self.test_results['tests_run'] += 1
        if 'john.doe@email.com' not in redacted_gdpr and '(555) 123-4567' not in redacted_gdpr:
            print("✅ PII Redaction: PASSED")
            print(f"   Original: {test_data}")
            print(f"   Redactado (GDPR): {redacted_gdpr}")
            self.test_results['tests_passed'] += 1
        else:
            print("❌ PII Redaction: FAILED")
            print(f"   Datos originales aún presentes: {redacted_gdpr}")
            self.test_results['tests_failed'] += 1
            self.test_results['failures'].append("PII Redaction - Datos originales no fueron redactados")
    
    def test_compliance_frameworks(self):
        """Prueba diferentes frameworks de compliance"""
        print("\n🧪 Probando Compliance Frameworks...")
        
        test_data = "Email: test@example.com, SSN: 123-45-6789"
        pii_detector = PIIDetector()
        
        frameworks = ['GDPR', 'CCPA', 'SOX']
        results = {}
        
        for framework in frameworks:
            redacted = pii_detector.redact_pii(test_data, framework)
            results[framework] = redacted
        
        self.test_results['tests_run'] += 1
        if len(set(results.values())) == len(frameworks):  # Todos diferentes
            print("✅ Compliance Frameworks: PASSED")
            for fw, redacted in results.items():
                print(f"   {fw}: {redacted}")
            self.test_results['tests_passed'] += 1
        else:
            print("❌ Compliance Frameworks: FAILED")
            print(f"   Resultados: {results}")
            self.test_results['tests_failed'] += 1
    
    def test_code_vulnerability_scanning(self):
        """Prueba escaneo de vulnerabilidades en código"""
        print("\n🧪 Probando Code Vulnerability Scanning...")
        
        vulnerable_code = """
        def unsafe_function(user_input):
            # SQL Injection vulnerability
            query = "SELECT * FROM users WHERE name = '" + user_input + "'"
            
            # XSS vulnerability  
            return "<h1>Welcome " + user_input + "</h1>"
            
            # Command injection vulnerability
            os.system("ping " + user_input)
        """
        
        scanner = SecurityScanner()
        scan_result = scanner.scan_code(vulnerable_code, 'test_agent')
        
        self.test_results['tests_run'] += 1
        if len(scan_result['vulnerabilities']) > 0:
            print("✅ Code Vulnerability Scanning: PASSED")
            print(f"   {len(scan_result['vulnerabilities'])} vulnerabilidades detectadas")
            for vuln in scan_result['vulnerabilities']:
                print(f"   - {vuln['type']}: {vuln['description']}")
            self.test_results['tests_passed'] += 1
        else:
            print("❌ Code Vulnerability Scanning: FAILED")
            print("   No se detectaron vulnerabilidades en código vulnerable")
            self.test_results['tests_failed'] += 1
            self.test_results['failures'].append("Code Vulnerability Scanning - No detectó vulnerabilidades")
    
    def test_agent_security_scanning(self):
        """Prueba escaneo específico para agents"""
        print("\n🧪 Probando Agent Security Scanning...")
        
        agent_code = """
        class DatabaseAgent:
            def execute_query(self, table_name, conditions):
                # Potentially dangerous direct query construction
                query = f"SELECT * FROM {table_name} WHERE {conditions}"
                return self.db.execute(query)
        """
        
        scanner = SecurityScanner()
        scan_result = scanner.scan_code(agent_code, 'database_operations_agent')
        
        self.test_results['tests_run'] += 1
        if scan_result['risk_score'] > 0:
            print("✅ Agent Security Scanning: PASSED")
            print(f"   Risk Score: {scan_result['risk_score']:.2f}")
            print(f"   Recommendations: {scan_result['recommendations']}")
            self.test_results['tests_passed'] += 1
        else:
            print("❌ Agent Security Scanning: FAILED")
            print(f"   Risk Score: {scan_result['risk_score']}")
            self.test_results['tests_failed'] += 1
    
    def test_input_validation_xss(self):
        """Prueba validación de entrada XSS"""
        print("\n🧪 Probando Input Validation (XSS)...")
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>"
        ]
        
        validator_results = []
        for payload in xss_payloads:
            result = self.security_system.validate_input(payload, 'html')
            validator_results.append(result)
        
        self.test_results['tests_run'] += 1
        if all(not result['is_valid'] for result in validator_results):
            print("✅ Input Validation (XSS): PASSED")
            print(f"   {len(xss_payloads)} payloads XSS bloqueados")
            self.test_results['tests_passed'] += 1
        else:
            print("❌ Input Validation (XSS): FAILED")
            print(f"   Algunos payloads XSS pasaron la validación")
            self.test_results['tests_failed'] += 1
            self.test_results['failures'].append("Input Validation XSS - Payloads no bloqueados")
    
    def test_input_validation_sql_injection(self):
        """Prueba validación de entrada SQL Injection"""
        print("\n🧪 Probando Input Validation (SQL Injection)...")
        
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "UNION SELECT password FROM users"
        ]
        
        validator_results = []
        for payload in sql_payloads:
            result = self.security_system.validate_input(payload, 'sql')
            validator_results.append(result)
        
        self.test_results['tests_run'] += 1
        if all(not result['is_valid'] for result in validator_results):
            print("✅ Input Validation (SQL Injection): PASSED")
            print(f"   {len(sql_payloads)} payloads SQL Injection bloqueados")
            self.test_results['tests_passed'] += 1
        else:
            print("❌ Input Validation (SQL Injection): FAILED")
            print(f"   Algunos payloads SQL Injection pasaron la validación")
            self.test_results['tests_failed'] += 1
    
    def test_input_validation_path_traversal(self):
        """Prueba validación de entrada Path Traversal"""
        print("\n🧪 Probando Input Validation (Path Traversal)...")
        
        path_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//....//etc/passwd"
        ]
        
        validator_results = []
        for payload in path_payloads:
            result = self.security_system.validate_input(payload, 'path')
            validator_results.append(result)
        
        self.test_results['tests_run'] += 1
        if all(not result['is_valid'] for result in validator_results):
            print("✅ Input Validation (Path Traversal): PASSED")
            print(f"   {len(path_payloads)} payloads Path Traversal bloqueados")
            self.test_results['tests_passed'] += 1
        else:
            print("❌ Input Validation (Path Traversal): FAILED")
            print(f"   Algunos payloads Path Traversal pasaron la validación")
            self.test_results['tests_failed'] += 1
    
    def test_rate_limiting(self):
        """Prueba rate limiting"""
        print("\n🧪 Probando Rate Limiting...")
        
        # Simular múltiples requests
        client_ip = "192.168.1.100"
        results = []
        
        for i in range(10):  # Hacer 10 requests
            result = self.security_system.rate_limiter.check_rate_limit(
                client_ip, 'ip', '/api/test', 'anonymous'
            )
            results.append(result)
        
        self.test_results['tests_run'] += 1
        
        # Verificar que algunos requests fueron bloqueados (límite por defecto: 100/min)
        allowed_requests = [r for r in results if r['allowed']]
        
        if len(allowed_requests) >= 10:  # Debería permitir todos
            print("✅ Rate Limiting: PASSED")
            print(f"   {len(allowed_requests)}/10 requests permitidos")
            self.test_results['tests_passed'] += 1
        else:
            print("❌ Rate Limiting: FAILED")
            print(f"   Solo {len(allowed_requests)}/10 requests permitidos")
            self.test_results['tests_failed'] += 1
            self.test_results['failures'].append("Rate Limiting - Requests bloqueados incorrectamente")
    
    def test_burst_protection(self):
        """Prueba protección contra ráfagas"""
        print("\n🧪 Probando Burst Protection...")
        
        client_ip = "192.168.1.101"
        
        # Simular ráfaga de requests
        burst_results = []
        for i in range(15):  # Más que el límite de burst (10)
            result = self.security_system.rate_limiter.check_burst_limit(client_ip)
            burst_results.append(result)
        
        self.test_results['tests_run'] += 1
        
        # Verificar que se detectaron bursts
        blocked_requests = [r for r in burst_results if not r['allowed'] or r['burst_exceeded']]
        
        if blocked_requests:
            print("✅ Burst Protection: PASSED")
            print(f"   {len(blocked_requests)} requests en burst detectados")
            self.test_results['tests_passed'] += 1
        else:
            print("❌ Burst Protection: FAILED")
            print("   No se detectó patrón de burst")
            self.test_results['tests_failed'] += 1
    
    def test_file_upload_scanning(self):
        """Prueba escaneo de archivos subidos"""
        print("\n🧪 Probando File Upload Security...")
        
        # Crear archivo de prueba
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test file with no threats.")
            test_file_path = f.name
        
        try:
            scan_result = self.security_system.scan_file_upload(
                test_file_path, 'text/plain', max_size=1024
            )
            
            self.test_results['tests_run'] += 1
            if scan_result['is_safe']:
                print("✅ File Upload Security: PASSED")
                print(f"   Archivo escaneado: {test_file_path}")
                print(f"   Metadatos: {scan_result['metadata']}")
                self.test_results['tests_passed'] += 1
            else:
                print("❌ File Upload Security: FAILED")
                print(f"   Amenazas detectadas: {scan_result['threats_detected']}")
                self.test_results['tests_failed'] += 1
                self.test_results['failures'].append("File Upload Security - Falso positivo")
        
        finally:
            # Limpiar archivo de prueba
            os.unlink(test_file_path)
    
    def test_security_headers(self):
        """Prueba generación de security headers"""
        print("\n🧪 Probando Security Headers...")
        
        headers = self.security_system.security_headers.get_security_headers()
        
        required_headers = [
            'Strict-Transport-Security',
            'X-XSS-Protection',
            'X-Content-Type-Options',
            'X-Frame-Options',
            'Content-Security-Policy'
        ]
        
        self.test_results['tests_run'] += 1
        if all(header in headers for header in required_headers):
            print("✅ Security Headers: PASSED")
            print(f"   Headers generados: {list(headers.keys())}")
            self.test_results['tests_passed'] += 1
        else:
            missing_headers = [h for h in required_headers if h not in headers]
            print("❌ Security Headers: FAILED")
            print(f"   Headers faltantes: {missing_headers}")
            self.test_results['tests_failed'] += 1
            self.test_results['failures'].append(f"Security Headers - Faltantes: {missing_headers}")
    
    def test_vulnerability_scanning(self):
        """Prueba escaneo de vulnerabilidades"""
        print("\n🧪 Probando Vulnerability Scanning...")
        
        target_url = "http://httpbin.org/get"  # URL de prueba
        scan_result = self.security_system.vulnerability_scanner.scan_target(
            target_url, 
            {'scan_types': ['basic']}
        )
        
        self.test_results['tests_run'] += 1
        if 'scan_id' in scan_result and 'vulnerabilities_found' in scan_result:
            print("✅ Vulnerability Scanning: PASSED")
            print(f"   Scan ID: {scan_result['scan_id']}")
            print(f"   Vulnerabilidades encontradas: {len(scan_result['vulnerabilities_found'])}")
            print(f"   Risk Score: {scan_result['scan_summary']['risk_score']}")
            self.test_results['tests_passed'] += 1
        else:
            print("❌ Vulnerability Scanning: FAILED")
            print(f"   Resultado: {scan_result}")
            self.test_results['tests_failed'] += 1
            self.test_results['failures'].append("Vulnerability Scanning - Error en scan")
    
    def test_compliance_assessment(self):
        """Prueba evaluación de compliance"""
        print("\n🧪 Probando Compliance Assessment...")
        
        data_processing_activity = {
            'id': 'test_activity_001',
            'data_types': ['personal_identifiers', 'financial_data'],
            'consent_obtained': True,
            'data_subject_rights_implemented': True,
            'internal_controls_tested': True,
            'audit_trail_maintained': True
        }
        
        assessment = self.security_system.compliance_manager.assess_compliance(
            data_processing_activity
        )
        
        self.test_results['tests_run'] += 1
        if 'compliance_results' in assessment:
            print("✅ Compliance Assessment: PASSED")
            print(f"   Risk Score: {assessment['risk_score']}")
            print(f"   Frameworks evaluados: {list(assessment['compliance_results'].keys())}")
            self.test_results['tests_passed'] += 1
        else:
            print("❌ Compliance Assessment: FAILED")
            print(f"   Assessment: {assessment}")
            self.test_results['tests_failed'] += 1
    
    def test_end_to_end_security(self):
        """Prueba integración end-to-end"""
        print("\n🧪 Probando End-to-End Security...")
        
        # Datos con PII
        user_data = """
        User Profile:
        Name: John Doe
        Email: john.doe@company.com
        Phone: +1-555-123-4567
        SSN: 123-45-6789
        Credit Card: 4111 1111 1111 1111
        """
        
        # Escanear datos
        scan_result = self.security_system.scan_data(user_data)
        
        # Validar entrada
        validation_result = self.security_system.validate_input(
            "<script>alert('xss')</script>", 'html'
        )
        
        # Verificar seguridad de API
        api_security = self.security_system.check_api_security(
            '/api/users', 'POST', 'user123', 'authenticated'
        )
        
        # Ejecutar auditoría
        audit_result = self.security_system.run_security_audit('full')
        
        self.test_results['tests_run'] += 1
        if all([
            scan_result.get('overall_risk_score', 0) >= 0,
            'allowed' in api_security,
            'audit_id' in audit_result
        ]):
            print("✅ End-to-End Security: PASSED")
            print(f"   Data Scan Risk Score: {scan_result['overall_risk_score']}")
            print(f"   API Security Allowed: {api_security['allowed']}")
            print(f"   Audit Completed: {len(audit_result)} sections")
            self.test_results['tests_passed'] += 1
        else:
            print("❌ End-to-End Security: FAILED")
            print(f"   Scan Result: {bool(scan_result)}")
            print(f"   API Security: {bool(api_security)}")
            print(f"   Audit Result: {bool(audit_result)}")
            self.test_results['tests_failed'] += 1
            self.test_results['failures'].append("End-to-End Security - Falla en integración")
    
    def generate_test_report(self):
        """Genera reporte final de pruebas"""
        print("\n" + "=" * 80)
        print("REPORTE FINAL DE PRUEBAS")
        print("=" * 80)
        
        total_tests = self.test_results['tests_run']
        passed_tests = self.test_results['tests_passed']
        failed_tests = self.test_results['tests_failed']
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Estadísticas:")
        print(f"   Total de pruebas: {total_tests}")
        print(f"   Pruebas pasadas: {passed_tests}")
        print(f"   Pruebas fallidas: {failed_tests}")
        print(f"   Tasa de éxito: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ Pruebas fallidas ({failed_tests}):")
            for i, failure in enumerate(self.test_results['failures'], 1):
                print(f"   {i}. {failure}")
        
        if success_rate >= 90:
            print(f"\n🎉 SISTEMA DE SEGURIDAD: EXCELENTE")
        elif success_rate >= 75:
            print(f"\n✅ SISTEMA DE SEGURIDAD: BUENO")
        elif success_rate >= 50:
            print(f"\n⚠️  SISTEMA DE SEGURIDAD: ACEPTABLE")
        else:
            print(f"\n🔴 SISTEMA DE SEGURIDAD: REQUIERE ATENCIÓN")
        
        print("\n" + "=" * 80)
        
        # Guardar reporte detallado
        self.save_detailed_report()
    
    def save_detailed_report(self):
        """Guarda reporte detallado en archivo"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"/tmp/security_test_report_{timestamp}.json"
        
        detailed_report = {
            'timestamp': datetime.now().isoformat(),
            'test_summary': self.test_results,
            'config_used': {
                'environment': self.config.environment,
                'pii_enabled': self.config.pii_config.enabled,
                'vulnerability_scanning': self.config.vulnerability_config.enabled,
                'rate_limiting': self.config.rate_limit_config.enabled,
                'compliance_frameworks': {
                    'gdpr': self.config.compliance_config.gdpr_enabled,
                    'ccpa': self.config.compliance_config.ccpa_enabled,
                    'sox': self.config.compliance_config.sox_enabled
                }
            },
            'recommendations': [
                "Ejecutar pruebas en entorno de producción",
                "Configurar monitoreo continuo de security events",
                "Implementar alerts para vulnerabilidades críticas",
                "Revisar y actualizar políticas de compliance",
                "Realizar penetration testing periódico"
            ]
        }
        
        try:
            with open(report_file, 'w') as f:
                json.dump(detailed_report, f, indent=2)
            print(f"📄 Reporte detallado guardado en: {report_file}")
        except Exception as e:
            print(f"⚠️  Error guardando reporte detallado: {e}")


def run_security_demo():
    """Función de demostración del sistema de seguridad"""
    print("🚀 DEMOSTRACIÓN DEL SISTEMA DE SEGURIDAD")
    print("=" * 50)
    
    # Crear sistema de seguridad
    security = SecuritySystem()
    
    # 1. Escanear datos con PII
    print("\n1️⃣  Escaneando datos con PII...")
    user_data = "Contact: john.doe@email.com, Phone: (555) 123-4567"
    scan_result = security.scan_data(user_data)
    
    print(f"   Datos originales: {user_data}")
    print(f"   PII detectado: {scan_result['pii_analysis']['pii_count']} elementos")
    print(f"   Datos redactados: {scan_result['pii_analysis']['redacted_data']}")
    
    # 2. Validar entrada maliciosa
    print("\n2️⃣  Validando entrada...")
    malicious_input = "<script>alert('XSS')</script>"
    validation_result = security.validate_input(malicious_input, 'html')
    
    print(f"   Entrada maliciosa: {malicious_input}")
    print(f"   ¿Es válida?: {validation_result['is_valid']}")
    print(f"   Security Score: {validation_result['security_score']}")
    
    # 3. Verificar API security
    print("\n3️⃣  Verificando seguridad de API...")
    api_security = security.check_api_security('/api/data', 'GET', 'user123')
    
    print(f"   ¿API permitida?: {api_security['allowed']}")
    print(f"   Rate limit restantes: {api_security['ip_rate_limit']['remaining_requests']}")
    
    # 4. Mostrar security headers
    print("\n4️⃣  Security Headers generados...")
    headers = security.security_headers.get_security_headers()
    
    for header, value in list(headers.items())[:3]:  # Mostrar primeros 3
        print(f"   {header}: {value}")
    
    print("\n✅ Demostración completada!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Pruebas del Sistema de Seguridad")
    parser.add_argument('--mode', choices=['test', 'demo'], default='test',
                       help='Modo de ejecución: test (pruebas completas) o demo (demostración)')
    
    args = parser.parse_args()
    
    if args.mode == 'test':
        # Ejecutar suite completa de pruebas
        tester = SecuritySystemTester()
        tester.run_all_tests()
    else:
        # Ejecutar demostración
        run_security_demo()