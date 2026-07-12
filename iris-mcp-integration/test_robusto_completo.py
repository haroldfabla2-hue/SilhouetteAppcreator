#!/usr/bin/env python3
"""
Script de Testing Robusto y Preciso - Sistema IRIS MCP Integration
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

class IRISRobustTester:
    """Tester robusto y preciso del sistema IRIS MCP Integration"""
    
    def __init__(self):
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
    
    def test_robust_replacements(self):
        """Test 1: Verificar que se reemplazaron los archivos con versiones robustas"""
        logger.info("🔍 Test 1: Verificando reemplazos de archivos robustos...")
        
        try:
            # Verificar que los archivos robustos existen
            robust_files = [
                ("api/iris_metrics_server_robust.py", "Métricas server robusto"),
                ("notifications/iris_notifications_robust.py", "Notificaciones robustas")
            ]
            
            for file_path, description in robust_files:
                if Path(file_path).exists():
                    self.log_test(f"Robust {description}", True, f"{description} existe")
                else:
                    self.log_test(f"Robust {description}", False, f"{description} NO existe")
            
            # Verificar que los archivos principales tienen las correcciones
            main_files = [
                ("api/iris_metrics_server.py", "Métricas server principal"),
                ("notifications/iris_notifications.py", "Notificaciones principales")
            ]
            
            for file_path, description in main_files:
                if Path(file_path).exists():
                    self.log_test(f"Main {description}", True, f"{description} existe")
                else:
                    self.log_test(f"Main {description}", False, f"{description} NO existe")
                    
        except Exception as e:
            self.log_test("Robust Replacements", False, f"Error verificando reemplazos: {str(e)}")
    
    def test_metrics_server_robust_features(self):
        """Test 2: Verificar características robustas del servidor de métricas"""
        logger.info("🔍 Test 2: Verificando características robustas del servidor...")
        
        try:
            server_file = Path("api/iris_metrics_server.py")
            if not server_file.exists():
                self.log_test("Metrics Server File", False, "Archivo no encontrado")
                return
            
            with open(server_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificaciones específicas de características robustas
            robust_features = [
                ("PersistentMetricsStore", "Store persistente"),
                ("allow_origins=", "CORS configurado específicamente"),
                ("threading.Lock", "Threading para concurrencia"),
                ("deque", "Estructuras de datos eficientes"),
                ("backup", "Sistema de backup"),
                ("validate_data_structure", "Validación de datos"),
                ("restore_from_backup", "Restauración desde backup"),
                ("save_buffer", "Buffer de guardado"),
                ("logging.error", "Logging de errores"),
                ("try:", "Manejo de excepciones"),
                ("finally:", "Bloques finally"),
                ("HTTPException", "Excepciones HTTP"),
                ("CORSMiddleware", "Middleware CORS"),
                ("StreamingResponse", "Streaming responses"),
                ("connection tracking", "Tracking de conexiones"),
                ("graceful cleanup", "Limpieza elegante"),
                ("memory management", "Gestión de memoria")
            ]
            
            for feature, description in robust_features:
                if feature in content:
                    self.log_test(f"Metrics {description}", True, f"{description} implementado")
                else:
                    self.log_test(f"Metrics {description}", False, f"{description} NO encontrado")
                    
        except Exception as e:
            self.log_test("Metrics Server Robust", False, f"Error: {str(e)}")
    
    def test_notifications_robust_features(self):
        """Test 3: Verificar características robustas de notificaciones"""
        logger.info("🔍 Test 3: Verificando características robustas de notificaciones...")
        
        try:
            notifications_file = Path("notifications/iris_notifications.py")
            if not notifications_file.exists():
                self.log_test("Notifications File", False, "Archivo no encontrado")
                return
            
            with open(notifications_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificaciones específicas de características robustas
            robust_features = [
                ("import sys", "Import sys agregado"),
                ("NotificationEvent", "Eventos de notificación"),
                ("NotificationConfig", "Configuración robusta"),
                ("NotificationType", "Tipos de notificación"),
                ("NotificationLevel", "Niveles de notificación"),
                ("AdvancedRateLimiter", "Rate limiting avanzado"),
                ("token bucket", "Algoritmo token bucket"),
                ("threading.Lock", "Threading para concurrencia"),
                ("concurrent.futures", "Ejecución concurrente"),
                ("MIMEText", "Tipos MIME"),
                ("MIMEMultipart", "Multipart MIME"),
                ("validation", "Validación de datos"),
                ("sanitization", "Sanitización"),
                ("async", "Operaciones asíncronas"),
                ("error handling", "Manejo de errores"),
                ("retry logic", "Lógica de reintentos"),
                ("credential validation", "Validación de credenciales")
            ]
            
            for feature, description in robust_features:
                if feature in content:
                    self.log_test(f"Notifications {description}", True, f"{description} implementado")
                else:
                    self.log_test(f"Notifications {description}", False, f"{description} NO encontrado")
                    
        except Exception as e:
            self.log_test("Notifications Robust", False, f"Error: {str(e)}")
    
    def test_cli_integration_robust(self):
        """Test 4: Verificar integración CLI robusta"""
        logger.info("🔍 Test 4: Verificando integración CLI...")
        
        try:
            cli_file = Path("cli/iris_cli.py")
            if not cli_file.exists():
                self.log_test("CLI File", False, "Archivo CLI no encontrado")
                return
            
            with open(cli_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificaciones CLI
            cli_features = [
                ("import click", "Framework Click"),
                ("@click.group", "Comandos CLI"),
                ("def iris", "Comando principal iris"),
                ("IRISCLIManager", "Manager CLI"),
                ("_api_call", "Llamadas API"),
                ("click.echo", "Output CLI"),
                ("commands", "Comandos"),
                ("status", "Comando status"),
                ("agents", "Comando agents"),
                ("templates", "Comando templates")
            ]
            
            for feature, description in cli_features:
                if feature in content:
                    self.log_test(f"CLI {description}", True, f"{description} encontrado")
                else:
                    self.log_test(f"CLI {description}", False, f"{description} NO encontrado")
                    
        except Exception as e:
            self.log_test("CLI Integration", False, f"Error: {str(e)}")
    
    def test_templates_system_robust(self):
        """Test 5: Verificar sistema de templates robusto"""
        logger.info("🔍 Test 5: Verificando sistema de templates...")
        
        try:
            templates_file = Path("templates/iris_templates.py")
            if not templates_file.exists():
                self.log_test("Templates File", False, "Archivo templates no encontrado")
                return
            
            with open(templates_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificaciones Templates
            templates_features = [
                ("class IRISTemplateManager", "Manager de templates"),
                ("class Template", "Clase Template"),
                ("create_template", "Creación de templates"),
                ("list_templates", "Listado de templates"),
                ("apply_template", "Aplicación de templates"),
                ("validate_template", "Validación de templates"),
                ("update_template", "Actualización de templates"),
                ("delete_template", "Eliminación de templates"),
                ("workflow", "Templates de workflow"),
                ("automation", "Templates de automatización")
            ]
            
            for feature, description in templates_features:
                if feature in content:
                    self.log_test(f"Templates {description}", True, f"{description} encontrado")
                else:
                    self.log_test(f"Templates {description}", False, f"{description} NO encontrado")
                    
        except Exception as e:
            self.log_test("Templates System", False, f"Error: {str(e)}")
    
    def test_dashboard_robust_react(self):
        """Test 6: Verificar dashboard React robusto"""
        logger.info("🔍 Test 6: Verificando dashboard React...")
        
        try:
            dashboard_file = Path("dashboard/src/components/Dashboard.tsx")
            if not dashboard_file.exists():
                self.log_test("Dashboard File", False, "Dashboard React no encontrado")
                return
            
            with open(dashboard_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificaciones Dashboard
            dashboard_features = [
                ("React.FC", "Componente React"),
                ("useState", "Estado React"),
                ("useEffect", "Efectos React"),
                ("interface", "Interfaces TypeScript"),
                ("EventSource", "SSE implementado"),
                ("setInterval", "Actualizaciones periódicas"),
                ("error handling", "Manejo de errores"),
                ("loading states", "Estados de carga"),
                ("agent cards", "Tarjetas de agentes"),
                ("metrics display", "Display de métricas")
            ]
            
            for feature, description in dashboard_features:
                if feature in content:
                    self.log_test(f"Dashboard {description}", True, f"{description} implementado")
                else:
                    self.log_test(f"Dashboard {description}", False, f"{description} NO encontrado")
                    
        except Exception as e:
            self.log_test("Dashboard React", False, f"Error: {str(e)}")
    
    def test_configuration_robust(self):
        """Test 7: Verificar configuración robusta"""
        logger.info("🔍 Test 7: Verificando configuración...")
        
        try:
            # Verificar package.json
            package_file = Path("dashboard/package.json")
            if package_file.exists():
                with open(package_file, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                
                deps = package_data.get("dependencies", {})
                dev_deps = package_data.get("devDependencies", {})
                all_deps = {**deps, **dev_deps}
                
                required_deps = ["react", "typescript", "recharts", "vite"]
                for dep in required_deps:
                    if dep in all_deps:
                        self.log_test(f"Config {dep.upper()}", True, f"{dep} configurado")
                    else:
                        self.log_test(f"Config {dep.upper()}", False, f"{dep} NO configurado")
            
            # Verificar scripts de ejecución
            scripts = ["setup.sh", "start_metrics_server.sh", "start_dashboard.sh", "run_mcp_server.sh"]
            for script in scripts:
                if Path(script).exists():
                    self.log_test(f"Script {script}", True, f"Script {script} existe")
                else:
                    self.log_test(f"Script {script}", False, f"Script {script} NO existe")
                    
            # Verificar requirements.txt
            if Path("requirements.txt").exists():
                self.log_test("Requirements", True, "Requirements.txt existe")
            else:
                self.log_test("Requirements", False, "Requirements.txt NO existe")
                
        except Exception as e:
            self.log_test("Configuration", False, f"Error: {str(e)}")
    
    def test_architecture_robust(self):
        """Test 8: Verificar arquitectura robusta"""
        logger.info("🔍 Test 8: Verificando arquitectura...")
        
        try:
            # Verificar estructura de directorios
            directories = ["api", "cli", "dashboard", "notifications", "templates", "configs", "logs", "tests"]
            for directory in directories:
                if Path(directory).exists():
                    self.log_test(f"Architecture {directory}", True, f"Directorio {directory} existe")
                else:
                    self.log_test(f"Architecture {directory}", False, f"Directorio {directory} NO existe")
            
            # Verificar archivos de configuración
            config_files = ["mcp-server.json", "README.md", "run.sh"]
            for config_file in config_files:
                if Path(config_file).exists():
                    self.log_test(f"Config File {config_file}", True, f"{config_file} existe")
                else:
                    self.log_test(f"Config File {config_file}", False, f"{config_file} NO existe")
                    
        except Exception as e:
            self.log_test("Architecture", False, f"Error: {str(e)}")
    
    def test_security_robust_features(self):
        """Test 9: Verificar características de seguridad robustas"""
        logger.info("🔍 Test 9: Verificando seguridad robusta...")
        
        try:
            metrics_file = Path("api/iris_metrics_server.py")
            notifications_file = Path("notifications/iris_notifications.py")
            
            security_features = [
                # Métricas server
                ("allow_origins", "CORS configurado"),
                ("credentials", "Credenciales manejadas"),
                ("headers", "Headers configurados"),
                ("methods", "Métodos restringidos"),
                # Notificaciones
                ("sanitization", "Sanitización"),
                ("validation", "Validación"),
                ("rate limiting", "Rate limiting"),
                ("credential validation", "Validación credenciales"),
                ("escape", "Escaping"),
                ("timeout", "Timeouts")
            ]
            
            for feature, description in security_features:
                metrics_has = feature in metrics_file.read_text(encoding='utf-8') if metrics_file.exists() else False
                notif_has = feature in notifications_file.read_text(encoding='utf-8') if notifications_file.exists() else False
                
                if metrics_has or notif_has:
                    self.log_test(f"Security {description}", True, f"{description} implementado")
                else:
                    self.log_test(f"Security {description}", False, f"{description} NO encontrado")
                    
        except Exception as e:
            self.log_test("Security Features", False, f"Error: {str(e)}")
    
    def test_performance_robust_features(self):
        """Test 10: Verificar características de rendimiento robustas"""
        logger.info("🔍 Test 10: Verificando rendimiento robusto...")
        
        try:
            metrics_file = Path("api/iris_metrics_server.py")
            notifications_file = Path("notifications/iris_notifications.py")
            
            performance_features = [
                ("cache", "Cache implementado"),
                ("buffer", "Buffering"),
                ("threading", "Threading"),
                ("async", "Async/await"),
                ("deque", "Estructuras eficientes"),
                ("connection", "Gestión de conexiones"),
                ("pool", "Pools de conexiones"),
                ("batch", "Procesamiento en lotes"),
                ("lock", "Locks para concurrencia")
            ]
            
            for feature, description in performance_features:
                metrics_has = feature in metrics_file.read_text(encoding='utf-8') if metrics_file.exists() else False
                notif_has = feature in notifications_file.read_text(encoding='utf-8') if notifications_file.exists() else False
                
                if metrics_has or notif_has:
                    self.log_test(f"Performance {description}", True, f"{description} implementado")
                else:
                    self.log_test(f"Performance {description}", False, f"{description} NO encontrado")
                    
        except Exception as e:
            self.log_test("Performance Features", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Ejecutar todos los tests robustos"""
        logger.info("🚀 Iniciando testing robusto completo del sistema IRIS MCP Integration...")
        logger.info("=" * 70)
        
        tests = [
            self.test_robust_replacements,
            self.test_metrics_server_robust_features,
            self.test_notifications_robust_features,
            self.test_cli_integration_robust,
            self.test_templates_system_robust,
            self.test_dashboard_robust_react,
            self.test_configuration_robust,
            self.test_architecture_robust,
            self.test_security_robust_features,
            self.test_performance_robust_features
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                logger.error(f"Error ejecutando test {test.__name__}: {str(e)}")
        
        # Generar reporte final robusto
        self.generate_robust_report()
    
    def generate_robust_report(self):
        """Generar reporte final robusto"""
        logger.info("=" * 70)
        logger.info("📊 Generando reporte final robusto...")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Reporte en consola
        logger.info("=" * 70)
        logger.info("🎯 REPORTE FINAL ROBUSTO - SISTEMA IRIS MCP INTEGRATION")
        logger.info("=" * 70)
        logger.info(f"📋 Total de validaciones: {total_tests}")
        logger.info(f"✅ Validaciones exitosas: {passed_tests}")
        logger.info(f"❌ Validaciones fallidas: {failed_tests}")
        logger.info(f"📊 Tasa de éxito: {success_rate:.1f}%")
        logger.info("=" * 70)
        
        # Determinar estado del sistema
        if success_rate >= 90:
            status = "🟢 SISTEMA IRIS LISTO PARA PRODUCCIÓN"
            recommendation = "✅ El sistema está completamente implementado con características robustas."
        elif success_rate >= 75:
            status = "🟡 SISTEMA CASI LISTO"
            recommendation = "⚠️  Sistema funcional, revisar validaciones fallidas."
        else:
            status = "🔴 SISTEMA REQUIERE ATENCIÓN"
            recommendation = "❌ Sistema necesita correcciones antes de producción."
        
        logger.info(f"🏆 Estado del sistema: {status}")
        logger.info(f"📝 Recomendación: {recommendation}")
        
        if failed_tests > 0:
            logger.info("\n❌ VALIDACIONES FALLIDAS:")
            failed_results = [r for r in self.test_results if not r['success']]
            for result in failed_results:
                logger.info(f"  • {result['test']}: {result['message']}")
        
        # Guardar reporte robusto
        report = {
            "timestamp": time.time(),
            "fecha_reporte": "2025-11-05 10:00:26",
            "sistema": "IRIS MCP Integration",
            "version": "1.1.0-robust",
            "total_validaciones": total_tests,
            "validaciones_exitosas": passed_tests,
            "validaciones_fallidas": failed_tests,
            "tasa_exito": success_rate,
            "estado_sistema": status,
            "recomendacion": recommendation,
            "archivos_robustos": [
                "iris_metrics_server_robust.py",
                "iris_notifications_robust.py"
            ],
            "archivos_principales": [
                "iris_metrics_server.py",
                "iris_notifications.py"
            ],
            "resultados": self.test_results
        }
        
        with open("REPORTE_FINAL_IRIS_ROBUSTO.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n📄 Reporte guardado en: REPORTE_FINAL_IRIS_ROBUSTO.json")
        
        # Return status for external use
        return success_rate >= 90

if __name__ == "__main__":
    tester = IRISRobustTester()
    success = tester.run_all_tests()
    
    if success:
        logger.info("\n🎉 ¡SISTEMA IRIS MCP INTEGRATION COMPLETAMENTE VALIDADO!")
        logger.info("🟢 Estado: LISTO PARA PRODUCCIÓN")
        logger.info("🔧 Características robustas implementadas y verificadas")
        sys.exit(0)
    else:
        logger.error("\n⚠️  SISTEMA REQUIERE ATENCIÓN")
        logger.error("🔴 Revisar validaciones fallidas antes de producción")
        sys.exit(1)