#!/usr/bin/env python3
"""
Script de Prueba para el Sistema de Monitoreo SilhouetteMCP
Verifica la funcionalidad completa del sistema de monitoreo
"""

import asyncio
import json
import time
import sys
from pathlib import Path

# Añadir directorio actual al path
sys.path.append(str(Path(__file__).parent))

from silhouettemcp_integrated_monitoring import (
    IntegratedMonitoringSystem, 
    SystemMonitor, 
    SystemHealth,
    AlertManager,
    ScalabilityPredictor,
    PerformanceReporter,
    Dashboard,
    asdict
)

class MonitoringTestSuite:
    """Suite completa de pruebas para el sistema de monitoreo"""
    
    def __init__(self):
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Registra resultado de prueba"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} - {test_name}"
        if message:
            result += f": {message}"
        
        print(result)
        self.test_results.append((test_name, success, message))
        
        if success:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
    
    def test_system_monitor(self):
        """Prueba el monitor individual de sistemas"""
        print("\n🔧 Probando SystemMonitor...")
        
        try:
            # Crear monitor de prueba
            monitor = SystemMonitor("test_system", "http://nonexistent.local", 1)
            
            # Verificar inicialización
            self.log_test("SystemMonitor Init", 
                         monitor.system_id == "test_system" and 
                         monitor.endpoint == "http://nonexistent.local")
            
            # Probar verificación de salud (con endpoint inexistente)
            start_time = time.time()
            health = asyncio.run(monitor.check_health())
            test_time = time.time() - start_time
            
            # Verificar que se crea el objeto de salud
            self.log_test("Health Check Creation", 
                         health is not None and isinstance(health, SystemHealth))
            
            # Verificar estructura de health
            self.log_test("Health Check Structure", 
                         all(hasattr(health, attr) for attr in [
                             'system_id', 'status', 'cpu_usage', 'memory_usage',
                             'response_time', 'error_rate', 'timestamp'
                         ]))
            
            # Verificar que el sistema se marca como offline
            self.log_test("Offline Detection", health.status == "offline")
            
            # Verificar que el historial se actualiza
            self.log_test("Health History Update", len(monitor.health_history) > 0)
            
        except Exception as e:
            self.log_test("SystemMonitor Exception", False, str(e))
    
    def test_alert_manager(self):
        """Prueba el gestor de alertas"""
        print("\n🚨 Probando AlertManager...")
        
        try:
            # Crear gestor de alertas
            alert_manager = AlertManager({"email": {}})
            
            # Crear alerta de prueba
            alert = alert_manager.create_alert("test_system", "warning", "Test warning message")
            
            # Verificar creación de alerta
            self.log_test("Alert Creation", 
                         alert.system_id == "test_system" and 
                         alert.severity == "warning")
            
            # Verificar que la alerta se añade a la lista
            self.log_test("Alert Storage", len(alert_manager.alerts) > 0)
            
            # Resolver alerta
            alert_manager.resolve_alert(alert.alert_id)
            
            # Verificar resolución
            self.log_test("Alert Resolution", 
                         alert.resolved and 
                         alert.resolved_at is not None)
            
            # Verificar que se movió del historial
            self.log_test("Alert History", len(alert_manager.alerts) == 0)
            
        except Exception as e:
            self.log_test("AlertManager Exception", False, str(e))
    
    def test_scalability_predictor(self):
        """Prueba el predictor de escalabilidad"""
        print("\n🔮 Probando ScalabilityPredictor...")
        
        try:
            predictor = ScalabilityPredictor(history_size=10)
            
            # Crear health de prueba
            test_health = SystemHealth(
                system_id="test_system",
                status="healthy",
                cpu_usage=50.0,
                memory_usage=60.0,
                disk_usage=30.0,
                response_time=0.5,
                error_rate=2.0,
                uptime=3600.0,
                last_check=time.time(),
                timestamp=time.time()
            )
            
            # Añadir snapshots
            for i in range(5):
                test_health.cpu_usage += 5.0
                test_health.memory_usage += 5.0
                test_health.timestamp += 60.0
                predictor.add_metric_snapshot("test_system", test_health)
            
            # Obtener predicción
            prediction = predictor.predict_load("test_system", 1)
            
            # Verificar estructura de predicción
            required_keys = ['predicted_cpu', 'predicted_memory', 'capacity_assessment', 'confidence']
            self.log_test("Prediction Structure", 
                         all(key in prediction for key in required_keys))
            
            # Verificar que las predicciones están en rango válido
            self.log_test("Prediction Values", 
                         0 <= prediction['predicted_cpu'] <= 100 and
                         0 <= prediction['predicted_memory'] <= 100)
            
            # Verificar confianza
            self.log_test("Confidence Range", 
                         0 <= prediction['confidence'] <= 1)
            
            # Verificar recomendaciones
            self.log_test("Recommendations", 
                         isinstance(prediction.get('recommendations', []), list))
            
        except Exception as e:
            self.log_test("ScalabilityPredictor Exception", False, str(e))
    
    def test_performance_reporter(self):
        """Prueba el generador de reportes"""
        print("\n📊 Probando PerformanceReporter...")
        
        try:
            reporter = PerformanceReporter("/tmp/test_reports")
            
            # Crear sistemas de prueba
            test_systems = {
                "system1": self._create_test_monitor("system1"),
                "system2": self._create_test_monitor("system2")
            }
            
            # Generar reporte
            report_path = reporter.generate_performance_report(test_systems)
            
            # Verificar que se crea el archivo
            self.log_test("Report File Creation", Path(report_path).exists())
            
            # Verificar contenido del reporte
            if Path(report_path).exists():
                with open(report_path, 'r') as f:
                    report_data = json.load(f)
                
                self.log_test("Report Structure", 
                             'timestamp' in report_data and 
                             'systems' in report_data)
                
                self.log_test("System Data", 
                             len(report_data['systems']) == 2)
                
                # Verificar que se incluye información de métricas
                for system_id in ['system1', 'system2']:
                    if system_id in report_data['systems']:
                        system_data = report_data['systems'][system_id]
                        self.log_test(f"{system_id} Metrics", 
                                     'average_metrics' in system_data and
                                     'availability' in system_data)
            
            # Limpiar archivo de prueba
            if Path(report_path).exists():
                Path(report_path).unlink()
            
        except Exception as e:
            self.log_test("PerformanceReporter Exception", False, str(e))
    
    def test_dashboard(self):
        """Prueba el dashboard"""
        print("\n📈 Probando Dashboard...")
        
        try:
            dashboard = Dashboard()
            
            # Crear datos de prueba
            test_systems = {
                "system1": self._create_test_monitor("system1"),
                "system2": self._create_test_monitor("system2")
            }
            
            # Crear alertas de prueba
            test_alerts = [
                type('Alert', (), {
                    'alert_id': 'alert1',
                    'system_id': 'system1',
                    'severity': 'warning',
                    'message': 'Test warning',
                    'timestamp': time.time(),
                    'resolved': False
                })()
            ]
            
            test_predictions = {
                "system1": {
                    "capacity_assessment": "adequate",
                    "confidence": 0.8,
                    "predicted_cpu": 45.0,
                    "predicted_memory": 55.0
                },
                "system2": {
                    "capacity_assessment": "approaching_limit",
                    "confidence": 0.7,
                    "predicted_cpu": 75.0,
                    "predicted_memory": 65.0
                }
            }
            
            # Generar dashboard
            dashboard_data = dashboard.generate_dashboard(
                test_systems, test_alerts, test_predictions
            )
            
            # Verificar estructura del dashboard
            required_sections = ['summary', 'systems', 'alerts', 'predictions']
            self.log_test("Dashboard Structure", 
                         all(section in dashboard_data for section in required_sections))
            
            # Verificar resumen
            summary = dashboard_data['summary']
            self.log_test("Dashboard Summary", 
                         'total_systems' in summary and
                         summary['total_systems'] == 2)
            
            # Verificar que el timestamp se actualiza
            self.log_test("Dashboard Timestamp Update", 
                         dashboard_data['last_update'] > 0)
            
        except Exception as e:
            self.log_test("Dashboard Exception", False, str(e))
    
    def test_integrated_monitoring_system(self):
        """Prueba el sistema de monitoreo integrado"""
        print("\n🚀 Probando IntegratedMonitoringSystem...")
        
        try:
            # Crear sistema de monitoreo
            monitoring_system = IntegratedMonitoringSystem()
            
            # Añadir sistema de prueba
            monitoring_system.add_system("test_integration", "http://test.local", 30)
            
            # Verificar que se añadió
            self.log_test("System Addition", "test_integration" in monitoring_system.systems)
            
            # Verificar que se puede obtener estado
            try:
                status = monitoring_system.get_system_status()
                self.log_test("Status Retrieval", isinstance(status, dict))
                
                if 'systems' in status:
                    self.log_test("Status Systems", isinstance(status['systems'], dict))
            except Exception:
                self.log_test("Status Retrieval", False, "Error en estado - esperado con endpoint de prueba")
            
            # Verificar obtención de alertas
            alerts = monitoring_system.get_alerts()
            self.log_test("Alerts Retrieval", isinstance(alerts, list))
            
            # Verificar predicciones
            predictions = monitoring_system.get_predictions()
            self.log_test("Predictions Retrieval", isinstance(predictions, dict))
            
            # Verificar dashboard data
            dashboard_data = monitoring_system.get_dashboard_data()
            self.log_test("Dashboard Data", isinstance(dashboard_data, dict))
            
        except Exception as e:
            self.log_test("IntegratedMonitoringSystem Exception", False, str(e))
    
    def test_configuration_loading(self):
        """Prueba la carga de configuración"""
        print("\n⚙️ Probando Carga de Configuración...")
        
        try:
            # Crear archivo de configuración de prueba
            test_config = {
                "systems": [
                    {
                        "id": "test_system",
                        "endpoint": "http://test.local",
                        "check_interval": 30
                    }
                ],
                "alerts": {
                    "thresholds": {
                        "cpu_warning": 75,
                        "cpu_critical": 95
                    }
                }
            }
            
            config_path = "/tmp/test_monitoring_config.json"
            with open(config_path, 'w') as f:
                json.dump(test_config, f)
            
            # Crear sistema de monitoreo con configuración de prueba
            monitoring_system = IntegratedMonitoringSystem(config_path)
            
            # Verificar que se carga la configuración personalizada
            custom_threshold = monitoring_system.config['alerts']['thresholds']['cpu_warning']
            self.log_test("Custom Config Loading", custom_threshold == 75)
            
            # Limpiar archivo de prueba
            Path(config_path).unlink()
            
        except Exception as e:
            self.log_test("Configuration Loading Exception", False, str(e))
    
    def test_end_to_end_flow(self):
        """Prueba flujo completo del sistema"""
        print("\n🔄 Probando Flujo Completo...")
        
        try:
            monitoring_system = IntegratedMonitoringSystem()
            
            # Añadir sistema de prueba
            monitoring_system.add_system("e2e_test", "http://nonexistent.local", 1)
            
            # Iniciar monitoreo por un tiempo breve
            monitoring_system.start_monitoring()
            time.sleep(2)  # Esperar un poco para que ejecute checks
            
            # Verificar que se está ejecutando
            self.log_test("Monitoring Start", monitoring_system.running)
            
            # Verificar que se generan datos
            status = monitoring_system.get_system_status()
            predictions = monitoring_system.get_predictions()
            
            # Verificar que se generan métricas
            self.log_test("Data Generation", len(status['systems']) > 0)
            
            # Detener monitoreo
            monitoring_system.stop_monitoring()
            time.sleep(1)  # Dar tiempo para que se detenga
            
            # Verificar que se detuvo
            self.log_test("Monitoring Stop", not monitoring_system.running)
            
        except Exception as e:
            self.log_test("End-to-End Flow Exception", False, str(e))
    
    def _create_test_monitor(self, system_id: str) -> SystemMonitor:
        """Crea un monitor de prueba con datos simulados"""
        monitor = SystemMonitor(system_id, "http://test.local", 60)
        
        # Añadir algunos health checks simulados
        for i in range(3):
            health = SystemHealth(
                system_id=system_id,
                status="healthy",
                cpu_usage=50.0 + i * 5.0,
                memory_usage=60.0 + i * 5.0,
                disk_usage=30.0,
                response_time=0.5 + i * 0.1,
                error_rate=2.0 + i * 0.5,
                uptime=3600.0 * (i + 1),
                last_check=time.time() - (60 * (3 - i)),
                timestamp=time.time() - (60 * (3 - i))
            )
            monitor.health_history.append(health)
            monitor.last_health = health
        
        return monitor
    
    def run_all_tests(self):
        """Ejecuta todas las pruebas"""
        print("🧪 INICIANDO SUITE DE PRUEBAS - SISTEMA DE MONITOREO SILHOUETTEMCP")
        print("=" * 80)
        
        start_time = time.time()
        
        # Ejecutar todas las pruebas
        self.test_system_monitor()
        self.test_alert_manager()
        self.test_scalability_predictor()
        self.test_performance_reporter()
        self.test_dashboard()
        self.test_integrated_monitoring_system()
        self.test_configuration_loading()
        self.test_end_to_end_flow()
        
        # Resumen de resultados
        total_time = time.time() - start_time
        
        print("\n" + "=" * 80)
        print("📊 RESUMEN DE PRUEBAS")
        print("=" * 80)
        print(f"✅ Pruebas exitosas: {self.passed_tests}")
        print(f"❌ Pruebas fallidas: {self.failed_tests}")
        print(f"📈 Tasa de éxito: {(self.passed_tests / (self.passed_tests + self.failed_tests)) * 100:.1f}%")
        print(f"⏱️  Tiempo total: {total_time:.2f} segundos")
        
        if self.failed_tests == 0:
            print("\n🎉 ¡TODAS LAS PRUEBAS PASARON CORRECTAMENTE!")
            print("✅ El sistema de monitoreo está funcionando correctamente")
        else:
            print(f"\n⚠️  {self.failed_tests} prueba(s) fallaron")
            print("🔧 Revisa los errores anteriores y la configuración")
        
        print("\n📝 PRUEBAS REALIZADAS:")
        for test_name, success, message in self.test_results:
            status = "✅" if success else "❌"
            print(f"   {status} {test_name}")
        
        return self.failed_tests == 0

def main():
    """Función principal"""
    test_suite = MonitoringTestSuite()
    success = test_suite.run_all_tests()
    
    # Código de salida
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()