#!/usr/bin/env python3
"""
Utilidades para el Sistema de Monitoreo SilhouetteMCP
Herramientas para gestionar y consultar el sistema de monitoreo
"""

import json
import argparse
import requests
import time
from pathlib import Path
from datetime import datetime
import sys
import os

# Añadir directorio actual al path para importar el módulo de monitoreo
sys.path.append(str(Path(__file__).parent))

try:
    from silhouettemcp_integrated_monitoring import IntegratedMonitoringSystem, asdict
except ImportError as e:
    print(f"Error importando módulo de monitoreo: {e}")
    print("Asegúrate de que silhouettemcp_integrated_monitoring.py esté en el mismo directorio")
    sys.exit(1)

class MonitoringCLI:
    """Interfaz de línea de comandos para el sistema de monitoreo"""
    
    def __init__(self):
        self.config_path = "monitoring_config.json"
        self.monitoring_system = None
    
    def load_system(self):
        """Carga el sistema de monitoreo"""
        if not self.monitoring_system:
            self.monitoring_system = IntegratedMonitoringSystem(self.config_path)
    
    def status_command(self, args):
        """Muestra el estado actual de todos los sistemas"""
        self.load_system()
        
        print("\n🔍 Estado del Sistema de Monitoreo SilhouetteMCP")
        print("=" * 60)
        
        try:
            status = self.monitoring_system.get_system_status()
            
            for system_id, system_status in status['systems'].items():
                status_icon = self._get_status_icon(system_status.get('status', 'unknown'))
                print(f"{status_icon} {system_id}: {system_status.get('status', 'unknown').upper()}")
                
                if 'cpu_usage' in system_status:
                    print(f"   CPU: {system_status['cpu_usage']:.1f}% | "
                          f"Memoria: {system_status['memory_usage']:.1f}% | "
                          f"Respuesta: {system_status['response_time']:.2f}s")
            
            # Mostrar alertas activas
            alerts = self.monitoring_system.get_alerts()
            if alerts:
                print(f"\n🚨 Alertas Activas: {len(alerts)}")
                for alert in alerts:
                    severity_icon = self._get_alert_icon(alert['severity'])
                    print(f"{severity_icon} [{alert['severity'].upper()}] {alert['system_id']}: {alert['message']}")
            else:
                print("\n✅ No hay alertas activas")
            
        except Exception as e:
            print(f"❌ Error obteniendo estado: {e}")
    
    def dashboard_command(self, args):
        """Muestra dashboard en tiempo real"""
        self.load_system()
        
        print("\n📊 Dashboard SilhouetteMCP - Actualización en tiempo real")
        print("Presiona Ctrl+C para salir")
        print("-" * 60)
        
        try:
            while True:
                os.system('clear' if os.name == 'posix' else 'cls')
                
                print(f"🕐 Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 60)
                
                dashboard_data = self.monitoring_system.get_dashboard_data()
                
                # Resumen general
                summary = dashboard_data['summary']
                print(f"📈 Resumen General:")
                print(f"   Total de sistemas: {summary['total_systems']}")
                print(f"   ✅ Sistemas saludables: {summary['healthy_systems']}")
                print(f"   ⚠️  Sistemas con advertencias: {summary['warning_systems']}")
                print(f"   🔴 Sistemas críticos: {summary['critical_systems']}")
                print(f"   ⚫ Sistemas offline: {summary['offline_systems']}")
                print(f"   🚨 Alertas activas: {summary['active_alerts']}")
                
                # Estado de cada sistema
                print(f"\n📊 Estado de Sistemas:")
                for system_id, system_data in dashboard_data['systems'].items():
                    status_icon = self._get_status_icon(system_data['status'])
                    metrics = system_data['metrics']
                    
                    print(f"{status_icon} {system_id}:")
                    print(f"   CPU: {metrics['cpu']:.1f}% | "
                          f"Mem: {metrics['memory']:.1f}% | "
                          f"Resp: {metrics['response_time']:.2f}s | "
                          f"Err: {metrics['error_rate']:.1f}%")
                
                # Alertas críticas
                if dashboard_data['alerts']:
                    print(f"\n🚨 Alertas Recientes:")
                    for alert in dashboard_data['alerts'][:5]:  # Mostrar solo las primeras 5
                        severity_icon = self._get_alert_icon(alert['severity'])
                        timestamp = datetime.fromtimestamp(alert['timestamp']).strftime('%H:%M:%S')
                        print(f"{severity_icon} [{alert['severity'].upper()}] {timestamp} - {alert['system_id']}: {alert['message']}")
                
                # Predicciones
                print(f"\n🔮 Predicciones (próxima hora):")
                for system_id, prediction in dashboard_data['predictions'].items():
                    capacity_icon = self._get_capacity_icon(prediction['capacity_assessment'])
                    confidence = prediction['confidence']
                    print(f"{capacity_icon} {system_id}: {prediction['capacity_assessment']} "
                          f"(confianza: {confidence:.2f})")
                
                time.sleep(30)  # Actualizar cada 30 segundos
                
        except KeyboardInterrupt:
            print("\n\n👋 Dashboard cerrado")
    
    def alerts_command(self, args):
        """Muestra las alertas del sistema"""
        self.load_system()
        
        print("\n🚨 Alertas del Sistema")
        print("=" * 40)
        
        try:
            alerts = self.monitoring_system.get_alerts()
            
            if not alerts:
                print("✅ No hay alertas activas")
                return
            
            for alert in alerts:
                severity_icon = self._get_alert_icon(alert['severity'])
                timestamp = datetime.fromtimestamp(alert['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"{severity_icon} [{alert['severity'].upper()}] {timestamp}")
                print(f"   Sistema: {alert['system_id']}")
                print(f"   Mensaje: {alert['message']}")
                print(f"   ID: {alert['alert_id']}")
                print()
                
        except Exception as e:
            print(f"❌ Error obteniendo alertas: {e}")
    
    def predictions_command(self, args):
        """Muestra predicciones de escalabilidad"""
        self.load_system()
        
        print("\n🔮 Predicciones de Escalabilidad")
        print("=" * 50)
        
        try:
            predictions = self.monitoring_system.get_predictions()
            
            for system_id, prediction in predictions.items():
                capacity_icon = self._get_capacity_icon(prediction['capacity_assessment'])
                
                print(f"{capacity_icon} {system_id}:")
                print(f"   Capacidad: {prediction['capacity_assessment']}")
                print(f"   CPU predicho: {prediction['predicted_cpu']:.1f}%")
                print(f"   Memoria predicha: {prediction['predicted_memory']:.1f}%")
                print(f"   Confianza: {prediction['confidence']:.2f}")
                
                if prediction['recommendations']:
                    print(f"   📝 Recomendaciones:")
                    for rec in prediction['recommendations']:
                        print(f"      • {rec}")
                print()
                
        except Exception as e:
            print(f"❌ Error obteniendo predicciones: {e}")
    
    def report_command(self, args):
        """Genera un reporte de rendimiento"""
        self.load_system()
        
        print("\n📊 Generando Reporte de Rendimiento")
        print("=" * 45)
        
        try:
            report_path = self.monitoring_system.generate_report()
            print(f"✅ Reporte generado: {report_path}")
            
            # Mostrar resumen del reporte
            if Path(report_path).exists():
                with open(report_path, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                
                print(f"\n📈 Resumen del Reporte:")
                print(f"   Generado: {report_data['generated_at']}")
                print(f"   Sistemas analizados: {len(report_data['systems'])}")
                
                for system_id, system_data in report_data['systems'].items():
                    print(f"\n   {system_id}:")
                    if system_data['current_status']:
                        status = system_data['current_status']['status']
                        print(f"      Estado: {status}")
                    
                    if system_data['average_metrics']:
                        metrics = system_data['average_metrics']
                        print(f"      CPU promedio: {metrics['cpu_usage']:.1f}%")
                        print(f"      Memoria promedio: {metrics['memory_usage']:.1f}%")
                        print(f"      Tiempo respuesta promedio: {metrics['response_time']:.2f}s")
                        print(f"      Disponibilidad: {system_data['availability']:.1f}%")
                        
        except Exception as e:
            print(f"❌ Error generando reporte: {e}")
    
    def start_command(self, args):
        """Inicia el sistema de monitoreo"""
        print("\n🚀 Iniciando Sistema de Monitoreo SilhouetteMCP")
        print("=" * 55)
        
        try:
            self.load_system()
            self.monitoring_system.start_monitoring()
            
            print("✅ Sistema de monitoreo iniciado")
            print("💡 Usa 'status' para ver el estado actual")
            print("💡 Usa 'dashboard' para ver el dashboard en tiempo real")
            
            # Mantener corriendo
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                print("\n🛑 Deteniendo sistema de monitoreo...")
                self.monitoring_system.stop_monitoring()
                print("✅ Sistema de monitoreo detenido")
                
        except Exception as e:
            print(f"❌ Error iniciando sistema: {e}")
    
    def stop_command(self, args):
        """Detiene el sistema de monitoreo"""
        print("\n🛑 Deteniendo Sistema de Monitoreo")
        
        try:
            self.load_system()
            self.monitoring_system.stop_monitoring()
            print("✅ Sistema de monitoreo detenido correctamente")
            
        except Exception as e:
            print(f"❌ Error deteniendo sistema: {e}")
    
    def _get_status_icon(self, status: str) -> str:
        """Retorna icono para el estado del sistema"""
        icons = {
            'healthy': '✅',
            'warning': '⚠️',
            'critical': '🔴',
            'offline': '⚫',
            'unknown': '❓'
        }
        return icons.get(status, '❓')
    
    def _get_alert_icon(self, severity: str) -> str:
        """Retorna icono para la severidad de alerta"""
        icons = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'critical': '🚨'
        }
        return icons.get(severity, '🔔')
    
    def _get_capacity_icon(self, assessment: str) -> str:
        """Retorna icono para la capacidad"""
        icons = {
            'adequate': '✅',
            'approaching_limit': '⚠️',
            'exceeding_capacity': '🔴',
            'unknown': '❓'
        }
        return icons.get(assessment, '❓')

def main():
    """Función principal del CLI"""
    parser = argparse.ArgumentParser(
        description="Utilidades del Sistema de Monitoreo SilhouetteMCP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python monitoring_utils.py status
  python monitoring_utils.py dashboard
  python monitoring_utils.py alerts
  python monitoring_utils.py predictions
  python monitoring_utils.py report
  python monitoring_utils.py start
  python monitoring_utils.py stop
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # Comando status
    status_parser = subparsers.add_parser('status', help='Mostrar estado de sistemas')
    
    # Comando dashboard
    dashboard_parser = subparsers.add_parser('dashboard', help='Dashboard en tiempo real')
    
    # Comando alerts
    alerts_parser = subparsers.add_parser('alerts', help='Mostrar alertas activas')
    
    # Comando predictions
    predictions_parser = subparsers.add_parser('predictions', help='Mostrar predicciones de escalabilidad')
    
    # Comando report
    report_parser = subparsers.add_parser('report', help='Generar reporte de rendimiento')
    
    # Comando start
    start_parser = subparsers.add_parser('start', help='Iniciar sistema de monitoreo')
    
    # Comando stop
    stop_parser = subparsers.add_parser('stop', help='Detener sistema de monitoreo')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = MonitoringCLI()
    
    # Ejecutar comando
    command_methods = {
        'status': cli.status_command,
        'dashboard': cli.dashboard_command,
        'alerts': cli.alerts_command,
        'predictions': cli.predictions_command,
        'report': cli.report_command,
        'start': cli.start_command,
        'stop': cli.stop_command
    }
    
    if args.command in command_methods:
        command_methods[args.command](args)
    else:
        print(f"❌ Comando desconocido: {args.command}")

if __name__ == "__main__":
    main()