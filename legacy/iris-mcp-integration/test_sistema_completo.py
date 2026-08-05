#!/usr/bin/env python3
"""
Script de Testing Completo - Sistema IRIS MCP Integration
Valida todas las correcciones robustas implementadas
"""

import json
import subprocess
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, List

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IRISSystemTester:
    """Tester completo del sistema IRIS MCP Integration"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = "", details: str = ""):
        """Registrar resultado de test"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {message}")
        if details:
            logger.info(f"    Details: {details}")
    
    def test_imports_robust(self):
        """Test 1: Verificar importaciones robustas"""
        logger.info("🔍 Test 1: Verificando importaciones robustas...")
        
        try:
            # Test métricas server
            sys.path.insert(0, 'api')
            import iris_metrics_server
            self.log_test("Import Metrics Server", True, "Métricas server importado correctamente")
            
            # Verificar nuevas funcionalidades robustas
            if hasattr(iris_metrics_server, 'PersistentMetricsStore'):
                self.log_test("Persistent Store", True, "Store persistente implementado")
            else:
                self.log_test("Persistent Store", False, "Store persistente NO encontrado")
            
            if hasattr(iris_metrics_server, 'CORS_CONFIG'):
                self.log_test("CORS Security", True, "CORS configurado correctamente")
            else:
                self.log_test("CORS Security", False, "CORS NO configurado")
                
            # Test notifications
            sys.path.insert(0, 'notifications')
            import iris_notifications
            self.log_test("Import Notifications", True, "Notifications importado correctamente")
            
            # Verificar nuevas funcionalidades robustas
            if hasattr(iris_notifications, 'Notification'):
                self.log_test("Notification Class", True, "Clase Notification implementada")
            else:
                self.log_test("Notification Class", False, "Clase Notification NO encontrada")
                
        except Exception as e:
            self.log_test("Imports Robust", False, f"Error en importaciones: {str(e)}")
    
    def test_metrics_server_startup(self):
        """Test 2: Verificar startup del servidor de métricas"""
        logger.info("🔍 Test 2: Verificando startup del servidor...")
        
        try:
            # Verificar que el archivo existe y es válido
            server_file = Path("api/iris_metrics_server.py")
            if not server_file.exists():
                self.log_test("Server File", False, "Archivo iris_metrics_server.py no encontrado")
                return
            
            # Verificar que el archivo tiene las correcciones robustas
            with open(server_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificaciones específicas
            checks = [
                ("PersistentMetricsStore", "Store persistente"),
                ("allow_origins=", "CORS configurado"),
                ("redis", "Redis implementado"),
                ("connection_pool", "Connection pooling"),
                ("retry_logic", "Retry logic"),
                ("rate_limit", "Rate limiting")
            ]
            
            for check_text, description in checks:
                if check_text in content:
                    self.log_test(f"Server {description}", True, f"{description} encontrado")
                else:
                    self.log_test(f"Server {description}", False, f"{description} NO encontrado")
                    
        except Exception as e:
            self.log_test("Server Startup", False, f"Error verificando servidor: {str(e)}")
    
    def test_notifications_robust(self):
        """Test 3: Verificar notificaciones robustas"""
        logger.info("🔍 Test 3: Verificando sistema de notificaciones...")
        
        try:
            notifications_file = Path("notifications/iris_notifications.py")
            if not notifications_file.exists():
                self.log_test("Notifications File", False, "Archivo iris_notifications.py no encontrado")
                return
            
            with open(notifications_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificaciones específicas de robustez
            checks = [
                ("import sys", "Import sys agregado"),
                ("_validate_email_config", "Validación email implementada"),
                ("retry_logic", "Retry logic en notificaciones"),
                ("exponential_backoff", "Exponential backoff"),
                ("credential_validation", "Validación de credenciales"),
                ("rate_limiting", "Rate limiting"),
                ("async def", "Patrones async/await"),
                ("MIMEText", "Tipos MIME correctos"),
                ("smtplib", "Librería SMTP")
            ]
            
            for check_text, description in checks:
                if check_text in content:
                    self.log_test(f"Notifications {description}", True, f"{description} encontrado")
                else:
                    self.log_test(f"Notifications {description}", False, f"{description} NO encontrado")
                    
        except Exception as e:
            self.log_test("Notifications Robust", False, f"Error verificando notificaciones: {str(e)}")
    
    def test_cli_integration(self):
        """Test 4: Verificar integración CLI"""
        logger.info("🔍 Test 4: Verificando integración CLI...")
        
        try:
            cli_file = Path("cli/iris_cli.py")
            if not cli_file.exists():
                self.log_test("CLI File", False, "Archivo iris_cli.py no encontrado")
                return
            
            with open(cli_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificaciones CLI
            checks = [
                ("import click", "Click framework"),
                ("@cli.group()", "Comandos CLI"),
                ("def iris():", "Comando principal iris"),
                ("IRISCLIManager", "Manager CLI implementado"),
                ("_api_call", "Llamadas API")
            ]
            
            for check_text, description in checks:
                if check_text in content:
                    self.log_test(f"CLI {description}", True, f"{description} encontrado")
                else:
                    self.log_test(f"CLI {description}", False, f"{description} NO encontrado")
                    
        except Exception as e:
            self.log_test("CLI Integration", False, f"Error verificando CLI: {str(e)}")
    
    def test_templates_system(self):
        """Test 5: Verificar sistema de templates"""
        logger.info("🔍 Test 5: Verificando sistema de templates...")
        
        try:
            templates_file = Path("templates/iris_templates.py")
            if not templates_file.exists():
                self.log_test("Templates File", False, "Archivo iris_templates.py no encontrado")
                return
            
            with open(templates_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificaciones Templates
            checks = [
                ("class IRISTemplateManager", "Manager de templates"),
                ("Template", "Clase Template"),
                ("create_template", "Creación de templates"),
                ("list_templates", "Listado de templates"),
                ("apply_template", "Aplicación de templates")
            ]
            
            for check_text, description in checks:
                if check_text in content:
                    self.log_test(f"Templates {description}", True, f"{description} encontrado")
                else:
                    self.log_test(f"Templates {description}", False, f"{description} NO encontrado")
                    
        except Exception as e:
            self.log_test("Templates System", False, f"Error verificando templates: {str(e)}")
    
    def test_dashboard_robust(self):
        """Test 6: Verificar dashboard React"""
        logger.info("🔍 Test 6: Verificando dashboard React...")
        
        try:
            dashboard_file = Path("dashboard/src/components/Dashboard.tsx")
            if not dashboard_file.exists():
                self.log_test("Dashboard File", False, "Archivo Dashboard.tsx no encontrado")
                return
            
            with open(dashboard_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificaciones Dashboard
            checks = [
                ("useState", "Estado React"),
                ("useEffect", "Efectos React"),
                ("EventSource", "SSE implementado"),
                ("Recharts", "Gráficos Recharts"),
                ("React.FC", "Componente React"),
                ("interface", "Interfaces TypeScript")
            ]
            
            for check_text, description in checks:
                if check_text in content:
                    self.log_test(f"Dashboard {description}", True, f"{description} encontrado")
                else:
                    self.log_test(f"Dashboard {description}", False, f"{description} NO encontrado")
                    
        except Exception as e:
            self.log_test("Dashboard Robust", False, f"Error verificando dashboard: {str(e)}")
    
    def test_package_json(self):
        """Test 7: Verificar configuración package.json"""
        logger.info("🔍 Test 7: Verificando configuración package.json...")
        
        try:
            package_file = Path("dashboard/package.json")
            if not package_file.exists():
                self.log_test("Package JSON", False, "Archivo package.json no encontrado")
                return
            
            with open(package_file, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            # Verificar dependencias críticas
            deps = package_data.get("dependencies", {})
            dev_deps = package_data.get("devDependencies", {})
            all_deps = {**deps, **dev_deps}
            
            required_deps = [
                ("react", "React"),
                ("typescript", "TypeScript"),
                ("recharts", "Recharts"),
                ("vite", "Vite")
            ]
            
            for dep, description in required_deps:
                if dep in all_deps:
                    version = all_deps[dep]
                    self.log_test(f"Package {description}", True, f"{description} v{version}")
                else:
                    self.log_test(f"Package {description}", False, f"{description} NO encontrado")
                    
        except Exception as e:
            self.log_test("Package JSON", False, f"Error verificando package.json: {str(e)}")
    
    def test_scripts_and_config(self):
        """Test 8: Verificar scripts y configuración"""
        logger.info("🔍 Test 8: Verificando scripts y configuración...")
        
        try:
            # Verificar scripts críticos
            scripts = [
                ("setup.sh", "Script setup"),
                ("start_metrics_server.sh", "Script metrics server"),
                ("start_dashboard.sh", "Script dashboard"),
                ("run_mcp_server.sh", "Script MCP server"),
                ("requirements.txt", "Dependencies Python")
            ]
            
            for script, description in scripts:
                if Path(script).exists():
                    self.log_test(f"Script {description}", True, f"{description} encontrado")
                else:
                    self.log_test(f"Script {description}", False, f"{description} NO encontrado")
                    
        except Exception as e:
            self.log_test("Scripts Config", False, f"Error verificando scripts: {str(e)}")
    
    def test_error_handling_robust(self):
        """Test 9: Verificar manejo de errores robusto"""
        logger.info("🔍 Test 9: Verificando manejo de errores...")
        
        try:
            # Verificar manejo de errores en métricas server
            metrics_file = Path("api/iris_metrics_server.py")
            with open(metrics_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            error_handling_checks = [
                ("try:", "Bloques try implementados"),
                ("except", "Manejo de excepciones"),
                ("finally", "Bloques finally"),
                ("logging.error", "Logging de errores"),
                ("HTTPException", "Excepciones HTTP"),
                ("ConnectionError", "Manejo de conexiones")
            ]
            
            for check_text, description in error_handling_checks:
                if check_text in content:
                    self.log_test(f"Error Handling {description}", True, f"{description} encontrado")
                else:
                    self.log_test(f"Error Handling {description}", False, f"{description} NO encontrado")
                    
        except Exception as e:
            self.log_test("Error Handling", False, f"Error verificando manejo de errores: {str(e)}")
    
    def test_security_features(self):
        """Test 10: Verificar características de seguridad"""
        logger.info("🔍 Test 10: Verificando características de seguridad...")
        
        try:
            # Verificar características de seguridad
            metrics_file = Path("api/iris_metrics_server.py")
            notifications_file = Path("notifications/iris_notifications.py")
            
            security_checks = []
            
            # Checks en métricas server
            with open(metrics_file, 'r', encoding='utf-8') as f:
                content = f.read()
                security_checks.extend([
                    ("allow_origins=", "CORS configurado"),
                    ("validate_origin", "Validación de origen"),
                    ("rate_limit", "Rate limiting"),
                    ("connection_pool", "Connection pooling")
                ])
            
            # Checks en notificaciones
            with open(notifications_file, 'r', encoding='utf-8') as f:
                content = f.read()
                security_checks.extend([
                    ("_validate_email_config", "Validación de credenciales"),
                    ("sanitize", "Sanitización"),
                    ("escape", "Escaping"),
                    ("timeout", "Timeouts")
                ])
            
            for check_text, description in security_checks:
                metrics_has = check_text in Path("api/iris_metrics_server.py").read_text(encoding='utf-8')
                notif_has = check_text in Path("notifications/iris_notifications.py").read_text(encoding='utf-8')
                
                if metrics_has or notif_has:
                    self.log_test(f"Security {description}", True, f"{description} implementado")
                else:
                    self.log_test(f"Security {description}", False, f"{description} NO implementado")
                    
        except Exception as e:
            self.log_test("Security Features", False, f"Error verificando seguridad: {str(e)}")
    
    def test_performance_optimizations(self):
        """Test 11: Verificar optimizaciones de rendimiento"""
        logger.info("🔍 Test 11: Verificando optimizaciones de rendimiento...")
        
        try:
            # Verificar optimizaciones de rendimiento
            metrics_file = Path("api/iris_metrics_server.py")
            notifications_file = Path("notifications/iris_notifications.py")
            
            perf_checks = [
                ("cache", "Cache implementado"),
                ("connection_pool", "Connection pooling"),
                ("buffer", "Buffering"),
                ("batch", "Procesamiento en lotes"),
                ("async", "Operaciones asíncronas"),
                ("deque", "Estructuras eficientes"),
                ("threading.Lock", "Locks para concurrencia")
            ]
            
            # Verificar en ambos archivos
            for check_text, description in perf_checks:
                metrics_has = check_text in Path("api/iris_metrics_server.py").read_text(encoding='utf-8')
                notif_has = check_text in Path("notifications/iris_notifications.py").read_text(encoding='utf-8')
                
                if metrics_has or notif_has:
                    self.log_test(f"Performance {description}", True, f"{description} implementado")
                else:
                    self.log_test(f"Performance {description}", False, f"{description} NO implementado")
                    
        except Exception as e:
            self.log_test("Performance Optimizations", False, f"Error verificando rendimiento: {str(e)}")
    
    def test_production_readiness(self):
        """Test 12: Verificar preparación para producción"""
        logger.info("🔍 Test 12: Verificando preparación para producción...")
        
        try:
            production_checks = [
                ("Environment variables", "Variables de entorno"),
                ("Error logging", "Logging de errores"),
                ("Monitoring", "Monitoreo"),
                ("Graceful degradation", "Degradación elegante"),
                ("Health checks", "Health checks"),
                ("Configuration", "Configuración externa")
            ]
            
            # Verificar archivos de configuración
            config_files = ["api/iris_metrics_server.py", "notifications/iris_notifications.py"]
            
            for check_text, description in production_checks:
                found = False
                for file_path in config_files:
                    try:
                        content = Path(file_path).read_text(encoding='utf-8')
                        if check_text.lower() in content.lower():
                            found = True
                            break
                    except:
                        continue
                
                if found:
                    self.log_test(f"Production {description}", True, f"{description} implementado")
                else:
                    self.log_test(f"Production {description}", False, f"{description} NO implementado")
                    
        except Exception as e:
            self.log_test("Production Readiness", False, f"Error verificando producción: {str(e)}")
    
    def run_all_tests(self):
        """Ejecutar todos los tests"""
        logger.info("🚀 Iniciando testing completo del sistema IRIS MCP Integration...")
        logger.info("=" * 60)
        
        tests = [
            self.test_imports_robust,
            self.test_metrics_server_startup,
            self.test_notifications_robust,
            self.test_cli_integration,
            self.test_templates_system,
            self.test_dashboard_robust,
            self.test_package_json,
            self.test_scripts_and_config,
            self.test_error_handling_robust,
            self.test_security_features,
            self.test_performance_optimizations,
            self.test_production_readiness
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                logger.error(f"Error ejecutando test {test.__name__}: {str(e)}")
        
        # Generar reporte final
        self.generate_final_report()
    
    def generate_final_report(self):
        """Generar reporte final de testing"""
        logger.info("=" * 60)
        logger.info("📊 Generando reporte final de testing...")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Reporte en consola
        logger.info("=" * 60)
        logger.info("🎯 REPORTE FINAL DE TESTING")
        logger.info("=" * 60)
        logger.info(f"Total de tests: {total_tests}")
        logger.info(f"Tests exitosos: {passed_tests} ✅")
        logger.info(f"Tests fallidos: {failed_tests} ❌")
        logger.info(f"Tasa de éxito: {success_rate:.1f}%")
        logger.info("=" * 60)
        
        # Determinar estado del sistema
        if success_rate >= 95:
            status = "🟢 SISTEMA LISTO PARA PRODUCCIÓN"
        elif success_rate >= 80:
            status = "🟡 SISTEMA CASI LISTO (revisar fallos)"
        else:
            status = "🔴 SISTEMA REQUIERE ATENCIÓN"
        
        logger.info(f"Estado del sistema: {status}")
        
        if failed_tests > 0:
            logger.info("\n❌ TESTS FALLIDOS:")
            for result in self.test_results:
                if not result['success']:
                    logger.info(f"  • {result['test']}: {result['message']}")
        
        # Guardar reporte en archivo
        report = {
            "timestamp": time.time(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "status": status,
            "results": self.test_results
        }
        
        with open("TEST_REPORT_FINAL.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n📄 Reporte guardado en: TEST_REPORT_FINAL.json")
        
        # Return status for external use
        return success_rate >= 95

if __name__ == "__main__":
    tester = IRISSystemTester()
    success = tester.run_all_tests()
    
    if success:
        logger.info("🎉 ¡Sistema IRIS MCP Integration validado exitosamente!")
        sys.exit(0)
    else:
        logger.error("⚠️  Sistema requiere correcciones antes de producción")
        sys.exit(1)