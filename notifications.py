#!/usr/bin/env python3
"""
🔔 Sistema de Notificaciones y Alertas - MCP Server Superior
============================================================

Sistema de monitoreo y alertas en tiempo real

Autor: MiniMax Agent
Fecha: 2025-11-04
Versión: 1.0.0
"""

import os
import sys
import json
import time
import smtplib
import requests
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import queue
import schedule

# Colores
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'
    WHITE = '\033[97m'

@dataclass
class Alert:
    """Clase para representar una alerta"""
    id: str
    level: str  # info, warning, error, critical
    title: str
    message: str
    source: str
    timestamp: str
    resolved: bool = False
    action_required: bool = False

@dataclass
class NotificationConfig:
    """Configuración de notificaciones"""
    email_enabled: bool = False
    webhook_enabled: bool = False
    desktop_enabled: bool = False
    slack_enabled: bool = False
    
    # Email settings
    smtp_server: str = ""
    smtp_port: int = 587
    email_user: str = ""
    email_password: str = ""
    email_to: List[str] = None
    
    # Webhook settings
    webhook_url: str = ""
    slack_webhook_url: str = ""

class NotificationManager:
    """Gestor de notificaciones y alertas"""
    
    def __init__(self, config_file: str = "config/notifications.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(exist_ok=True)
        
        self.config = self.load_config()
        self.alerts_queue = queue.Queue()
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_handlers: List[Callable] = []
        
        # Configurar logging
        self.setup_logging()
        
        # Cargar alertas existentes
        self.load_alert_history()
    
    def load_config(self) -> NotificationConfig:
        """Cargar configuración de notificaciones"""
        default_config = NotificationConfig(
            email_to=[]
        )
        
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    data = json.load(f)
                    return NotificationConfig(**data)
            except Exception as e:
                logging.error(f"Error loading config: {e}")
        
        # Guardar configuración por defecto
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config: NotificationConfig):
        """Guardar configuración"""
        with open(self.config_file, "w") as f:
            json.dump(asdict(config), f, indent=2)
    
    def setup_logging(self):
        """Configurar sistema de logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "notifications.log"),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("MCPNotifications")
    
    def load_alert_history(self):
        """Cargar historial de alertas"""
        history_file = Path("data/alert_history.json")
        if history_file.exists():
            try:
                with open(history_file) as f:
                    alerts_data = json.load(f)
                    for alert_data in alerts_data:
                        alert = Alert(**alert_data)
                        if not alert.resolved:
                            self.active_alerts[alert.id] = alert
            except Exception as e:
                self.logger.error(f"Error loading alert history: {e}")
    
    def save_alert_history(self):
        """Guardar historial de alertas"""
        history_file = Path("data/alert_history.json")
        history_file.parent.mkdir(exist_ok=True)
        
        all_alerts = list(self.active_alerts.values())
        
        try:
            with open(history_file, "w") as f:
                json.dump([asdict(alert) for alert in all_alerts], f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving alert history: {e}")
    
    def add_alert_handler(self, handler: Callable):
        """Agregar handler de alertas personalizado"""
        self.alert_handlers.append(handler)
    
    def create_alert(self, level: str, title: str, message: str, source: str, 
                    action_required: bool = False) -> Alert:
        """Crear nueva alerta"""
        alert_id = f"{source}_{int(time.time())}"
        
        alert = Alert(
            id=alert_id,
            level=level,
            title=title,
            message=message,
            source=source,
            timestamp=datetime.now().isoformat(),
            action_required=action_required
        )
        
        # Agregar a alertas activas
        self.active_alerts[alert_id] = alert
        
        # Guardar historial
        self.save_alert_history()
        
        # Enviar notificaciones
        self.send_notifications(alert)
        
        # Ejecutar handlers personalizados
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Error in alert handler: {e}")
        
        return alert
    
    def send_notifications(self, alert: Alert):
        """Enviar notificaciones según configuración"""
        self.logger.info(f"Sending notifications for alert: {alert.title}")
        
        # Notificación por email
        if self.config.email_enabled:
            self.send_email_notification(alert)
        
        # Notificación por webhook
        if self.config.webhook_enabled:
            self.send_webhook_notification(alert)
        
        # Notificación por Slack
        if self.config.slack_enabled:
            self.send_slack_notification(alert)
        
        # Notificación de escritorio (si está disponible)
        if self.config.desktop_enabled:
            self.send_desktop_notification(alert)
        
        # Notificación a consola
        self.send_console_notification(alert)
    
    def send_email_notification(self, alert: Alert):
        """Enviar notificación por email"""
        try:
            if not self.config.email_to:
                return
            
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = self.config.email_user
            msg['To'] = ", ".join(self.config.email_to)
            msg['Subject'] = f"[MCP Alert] {alert.title}"
            
            # Cuerpo del mensaje
            body = f"""
Alerta del Sistema MCP Server Superior
=====================================

Nivel: {alert.level.upper()}
Título: {alert.title}
Fuente: {alert.source}
Tiempo: {alert.timestamp}

Mensaje:
{alert.message}

{'⚠️ ACCIÓN REQUERIDA' if alert.action_required else ''}

---
MCP Server Superior v3.1.0
Este es un mensaje automático del sistema de alertas.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Enviar email
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            server.login(self.config.email_user, self.config.email_password)
            server.send_message(msg)
            server.quit()
            
            self.logger.info("Email notification sent successfully")
            
        except Exception as e:
            self.logger.error(f"Error sending email notification: {e}")
    
    def send_webhook_notification(self, alert: Alert):
        """Enviar notificación por webhook"""
        try:
            payload = {
                "alert": asdict(alert),
                "timestamp": datetime.now().isoformat(),
                "system": "MCP Server Superior"
            }
            
            response = requests.post(
                self.config.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("Webhook notification sent successfully")
            else:
                self.logger.error(f"Webhook notification failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error sending webhook notification: {e}")
    
    def send_slack_notification(self, alert: Alert):
        """Enviar notificación a Slack"""
        try:
            color_map = {
                'info': '#36a64f',
                'warning': '#ff9f00',
                'error': '#ff0000',
                'critical': '#ff0000'
            }
            
            payload = {
                "attachments": [
                    {
                        "color": color_map.get(alert.level, '#36a64f'),
                        "title": f"🚨 {alert.title}",
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Nivel",
                                "value": alert.level.upper(),
                                "short": True
                            },
                            {
                                "title": "Fuente",
                                "value": alert.source,
                                "short": True
                            }
                        ],
                        "footer": "MCP Server Superior",
                        "ts": int(time.time())
                    }
                ]
            }
            
            response = requests.post(
                self.config.slack_webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("Slack notification sent successfully")
            else:
                self.logger.error(f"Slack notification failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error sending Slack notification: {e}")
    
    def send_desktop_notification(self, alert: Alert):
        """Enviar notificación de escritorio"""
        try:
            # Intentar usar plyer (biblioteca de notificaciones multiplataforma)
            import plyer
            
            plyer.notification.notify(
                title=f"MCP Alert: {alert.title}",
                message=alert.message,
                timeout=10
            )
            
        except ImportError:
            self.logger.warning("plyer not available for desktop notifications")
        except Exception as e:
            self.logger.error(f"Error sending desktop notification: {e}")
    
    def send_console_notification(self, alert: Alert):
        """Enviar notificación a consola"""
        timestamp = datetime.fromisoformat(alert.timestamp).strftime("%H:%M:%S")
        
        level_colors = {
            'info': Colors.BLUE,
            'warning': Colors.YELLOW,
            'error': Colors.RED,
            'critical': Colors.RED
        }
        
        level_symbols = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'critical': '🚨'
        }
        
        color = level_colors.get(alert.level, Colors.BLUE)
        symbol = level_symbols.get(alert.level, 'ℹ️')
        
        print(f"\n{color}{symbol} [{timestamp}] {alert.title}{Colors.END}")
        print(f"{Colors.WHITE}   {alert.message}{Colors.END}")
        print(f"{Colors.CYAN}   Fuente: {alert.source} | Nivel: {alert.level.upper()}{Colors.END}")
        
        if alert.action_required:
            print(f"{Colors.RED}   ⚠️ ACCIÓN REQUERIDA{Colors.END}")
    
    def resolve_alert(self, alert_id: str):
        """Marcar alerta como resuelta"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolved = True
            self.save_alert_history()
            self.logger.info(f"Alert {alert_id} marked as resolved")
    
    def get_active_alerts(self) -> List[Alert]:
        """Obtener alertas activas"""
        return [alert for alert in self.active_alerts.values() if not alert.resolved]
    
    def get_alert_summary(self) -> Dict[str, int]:
        """Obtener resumen de alertas"""
        summary = {'info': 0, 'warning': 0, 'error': 0, 'critical': 0}
        
        for alert in self.active_alerts.values():
            if not alert.resolved:
                summary[alert.level] += 1
        
        return summary

class SystemMonitor:
    """Monitor del sistema para generar alertas automáticas"""
    
    def __init__(self, notification_manager: NotificationManager):
        self.notifications = notification_manager
        self.running = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Iniciar monitoreo del sistema"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop)
        self.monitor_thread.start()
        self.notifications.logger.info("System monitoring started")
    
    def stop_monitoring(self):
        """Detener monitoreo del sistema"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        self.notifications.logger.info("System monitoring stopped")
    
    def monitor_loop(self):
        """Loop principal de monitoreo"""
        while self.running:
            try:
                # Verificar estado de agentes
                self.check_agents_status()
                
                # Verificar uso de recursos
                self.check_system_resources()
                
                # Verificar conectividad
                self.check_connectivity()
                
                time.sleep(60)  # Verificar cada minuto
                
            except Exception as e:
                self.notifications.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)  # Esperar menos tiempo en caso de error
    
    def check_agents_status(self):
        """Verificar estado de agentes"""
        # Simulación - en implementación real verificar estado real
        import random
        
        agents = ['git_operations', 'web_scraping', 'database_operations']
        
        for agent in agents:
            # Simular fallo ocasional
            if random.random() < 0.01:  # 1% de probabilidad
                self.notifications.create_alert(
                    level="error",
                    title=f"Agente {agent} no responde",
                    message=f"El agente {agent} no ha enviado señales de vida en los últimos 5 minutos",
                    source="System Monitor",
                    action_required=True
                )
    
    def check_system_resources(self):
        """Verificar recursos del sistema"""
        try:
            import psutil
            
            # Verificar CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                self.notifications.create_alert(
                    level="warning",
                    title="Alto uso de CPU",
                    message=f"El uso de CPU ha alcanzado el {cpu_percent:.1f}%",
                    source="System Monitor"
                )
            
            # Verificar memoria
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                self.notifications.create_alert(
                    level="warning",
                    title="Alto uso de memoria",
                    message=f"El uso de memoria ha alcanzado el {memory.percent:.1f}%",
                    source="System Monitor"
                )
            
            # Verificar disco
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                self.notifications.create_alert(
                    level="error",
                    title="Poco espacio en disco",
                    message=f"El disco está {disk.percent:.1f}% lleno",
                    source="System Monitor",
                    action_required=True
                )
                
        except ImportError:
            self.notifications.logger.warning("psutil not available for system monitoring")
        except Exception as e:
            self.notifications.logger.error(f"Error checking system resources: {e}")
    
    def check_connectivity(self):
        """Verificar conectividad a servicios externos"""
        try:
            import urllib.request
            
            # Verificar Google
            try:
                urllib.request.urlopen('https://www.google.com', timeout=5)
            except:
                self.notifications.create_alert(
                    level="warning",
                    title="Sin conectividad a internet",
                    message="No se puede acceder a servicios externos",
                    source="System Monitor"
                )
            
            # Verificar OpenRouter
            try:
                urllib.request.urlopen('https://openrouter.ai', timeout=5)
            except:
                self.notifications.create_alert(
                    level="error",
                    title="OpenRouter no disponible",
                    message="No se puede acceder a OpenRouter API",
                    source="System Monitor",
                    action_required=True
                )
                
        except Exception as e:
            self.notifications.logger.error(f"Error checking connectivity: {e}")

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sistema de Notificaciones y Alertas")
    parser.add_argument("--start", action="store_true", help="Iniciar monitoreo")
    parser.add_argument("--stop", action="store_true", help="Detener monitoreo")
    parser.add_argument("--config", help="Archivo de configuración")
    parser.add_argument("--test", action="store_true", help="Enviar alerta de prueba")
    
    args = parser.parse_args()
    
    if args.config:
        notification_manager = NotificationManager(args.config)
    else:
        notification_manager = NotificationManager()
    
    if args.start:
        monitor = SystemMonitor(notification_manager)
        monitor.start_monitoring()
        
        print(f"{Colors.GREEN}🔔 Sistema de alertas iniciado{Colors.END}")
        print(f"{Colors.CYAN}Presiona Ctrl+C para detener{Colors.END}")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            monitor.stop_monitoring()
            print(f"\n{Colors.YELLOW}🔔 Sistema de alertas detenido{Colors.END}")
    
    elif args.test:
        # Enviar alerta de prueba
        alert = notification_manager.create_alert(
            level="info",
            title="Alerta de Prueba",
            message="Esta es una alerta de prueba del sistema MCP Server Superior",
            source="Test"
        )
        print(f"{Colors.GREEN}✅ Alerta de prueba enviada: {alert.id}{Colors.END}")
    
    else:
        # Mostrar estado actual
        summary = notification_manager.get_alert_summary()
        print(f"\n{Colors.BOLD}📊 Resumen de Alertas{Colors.END}")
        print("=" * 30)
        for level, count in summary.items():
            if count > 0:
                print(f"{Colors.WHITE}{level:8}{Colors.END} {count}")
        
        active_alerts = notification_manager.get_active_alerts()
        if active_alerts:
            print(f"\n{Colors.BOLD}🚨 Alertas Activas{Colors.END}")
            print("=" * 30)
            for alert in active_alerts[:5]:  # Mostrar solo las primeras 5
                print(f"• {alert.title} ({alert.level})")
        
        return 0

if __name__ == "__main__":
    sys.exit(main())