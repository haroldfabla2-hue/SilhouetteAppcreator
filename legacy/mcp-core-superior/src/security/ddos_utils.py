"""
Utilidades y herramientas de administración para el sistema de protección DDoS
"""

import json
import csv
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass
from pathlib import Path

from .ddos_protection import DDoSProtectionSystem, ThreatLevel


@dataclass
class ThreatReport:
    """Reporte de amenazas"""
    total_requests: int
    blocked_requests: int
    rate_limited_requests: int
    threat_events: int
    top_blocked_ips: List[Tuple[str, int]]
    top_threat_endpoints: List[Tuple[str, int]]
    geographic_blocks: int
    time_period: str


class DDoSAdminTools:
    """Herramientas administrativas para el sistema DDoS"""
    
    def __init__(self, ddos_system: DDoSProtectionSystem):
        self.ddos_system = ddos_system
        self.logger = logging.getLogger(__name__)
    
    def block_ip(self, ip: str, duration: int = 3600, reason: str = "Manual block"):
        """Bloquea una IP manualmente"""
        self.ddos_system.block_ip(ip, duration, reason)
        self.logger.info(f"IP {ip} bloqueada manualmente por {duration}s")
    
    def unblock_ip(self, ip: str):
        """Desbloquea una IP manualmente"""
        self.ddos_system.unblock_ip(ip)
        self.logger.info(f"IP {ip} desbloqueada manualmente")
    
    def add_whitelist_ip(self, ip: str, duration: Optional[int] = None):
        """Añade IP a whitelist"""
        self.ddos_system.add_to_whitelist(ip, duration)
        self.logger.info(f"IP {ip} añadida a whitelist")
    
    def remove_whitelist_ip(self, ip: str):
        """Remueve IP de whitelist"""
        self.ddos_system.remove_from_whitelist(ip)
        self.logger.info(f"IP {ip} removida de whitelist")
    
    def get_blocked_ips(self) -> List[str]:
        """Obtiene lista de IPs bloqueadas"""
        return list(self.ddos_system.blacklist)
    
    def get_whitelisted_ips(self) -> List[str]:
        """Obtiene lista de IPs en whitelist"""
        return list(self.ddos_system.whitelist)
    
    def get_threat_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas detalladas de amenazas"""
        metrics = self.ddos_system.get_metrics()
        
        # Calcular ratios
        if metrics['total_requests'] > 0:
            metrics['blocked_ratio'] = metrics['blocked_requests'] / metrics['total_requests']
            metrics['rate_limited_ratio'] = metrics['rate_limited_requests'] / metrics['total_requests']
            metrics['threat_ratio'] = metrics['threat_events'] / metrics['total_requests']
        else:
            metrics['blocked_ratio'] = 0.0
            metrics['rate_limited_ratio'] = 0.0
            metrics['threat_ratio'] = 0.0
        
        return metrics
    
    def generate_threat_report(self, 
                              start_time: Optional[datetime] = None,
                              end_time: Optional[datetime] = None) -> ThreatReport:
        """Genera reporte de amenazas"""
        if start_time is None:
            start_time = datetime.now() - timedelta(hours=24)
        if end_time is None:
            end_time = datetime.now()
        
        # En una implementación real, esto consultaría una base de datos
        # Por ahora, usamos las métricas actuales
        metrics = self.ddos_system.get_metrics()
        
        # Simular top blocked IPs y endpoints
        top_blocked_ips = [
            ("192.168.1.100", 150),
            ("10.0.0.50", 120),
            ("172.16.0.25", 80)
        ]
        
        top_threat_endpoints = [
            ("/api/agents/execute", 45),
            ("/api/search", 30),
            ("/api/database/query", 25)
        ]
        
        return ThreatReport(
            total_requests=metrics['total_requests'],
            blocked_requests=metrics['blocked_requests'],
            rate_limited_requests=metrics['rate_limited_requests'],
            threat_events=metrics['threat_events'],
            top_blocked_ips=top_blocked_ips,
            top_threat_endpoints=top_threat_endpoints,
            geographic_blocks=metrics['geographic_blocks'],
            time_period=f"{start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}"
        )
    
    def export_blocked_ips(self, filename: str):
        """Exporta lista de IPs bloqueadas a archivo CSV"""
        blocked_ips = self.get_blocked_ips()
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['IP Address', 'Blocked At', 'Reason'])
            
            # En implementación real, incluiría timestamp y razón
            for ip in blocked_ips:
                writer.writerow([ip, datetime.now().isoformat(), "Manual block"])
        
        self.logger.info(f"IPs bloqueadas exportadas a {filename}")
    
    def import_blocked_ips(self, filename: str):
        """Importa lista de IPs bloqueadas desde archivo CSV"""
        with open(filename, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                ip = row['IP Address']
                duration = int(row.get('Duration', 3600))
                reason = row.get('Reason', 'Import block')
                
                self.block_ip(ip, duration, reason)
        
        self.logger.info(f"IPs bloqueadas importadas desde {filename}")
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas en tiempo real"""
        health = self.ddos_system.health_check()
        metrics = self.get_threat_metrics()
        
        return {
            'system_health': health,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat(),
            'blocked_ips_count': len(self.get_blocked_ips()),
            'whitelisted_ips_count': len(self.get_whitelisted_ips()),
            'configured_endpoints': len(self.ddos_system.endpoint_configs)
        }
    
    def reset_statistics(self):
        """Reinicia todas las estadísticas"""
        self.ddos_system.metrics = {
            'total_requests': 0,
            'blocked_requests': 0,
            'rate_limited_requests': 0,
            'threat_events': 0,
            'ip_blocks': 0,
            'geographic_blocks': 0
        }
        self.logger.info("Estadísticas reiniciadas")


class DDoSBulkOperations:
    """Operaciones en lote para administración masiva"""
    
    def __init__(self, ddos_system: DDoSProtectionSystem):
        self.ddos_system = ddos_system
    
    def bulk_block_ips(self, ips: List[str], duration: int = 3600, reason: str = "Bulk block"):
        """Bloquea múltiples IPs en lote"""
        blocked_count = 0
        
        for ip in ips:
            try:
                self.ddos_system.block_ip(ip, duration, reason)
                blocked_count += 1
            except Exception as e:
                logging.error(f"Error blocking IP {ip}: {e}")
        
        logging.info(f"Bulk block completed: {blocked_count}/{len(ips)} IPs blocked")
        return blocked_count
    
    def bulk_whitelist_ips(self, ips: List[str]):
        """Añade múltiples IPs a whitelist en lote"""
        whitelisted_count = 0
        
        for ip in ips:
            try:
                self.ddos_system.add_to_whitelist(ip)
                whitelisted_count += 1
            except Exception as e:
                logging.error(f"Error whitelisting IP {ip}: {e}")
        
        logging.info(f"Bulk whitelist completed: {whitelisted_count}/{len(ips)} IPs whitelisted")
        return whitelisted_count
    
    def generate_threat_intelligence_report(self) -> Dict[str, Any]:
        """Genera reporte de inteligencia de amenazas"""
        # En implementación real, esto analizaría logs y patrones
        return {
            'threat_categories': {
                'sql_injection': {'count': 15, 'severity': 'high'},
                'xss_attempts': {'count': 8, 'severity': 'medium'},
                'bot_traffic': {'count': 45, 'severity': 'medium'},
                'rate_limit_abuse': {'count': 23, 'severity': 'low'}
            },
            'geographic_distribution': {
                'CN': 35,
                'RU': 28,
                'US': 20,
                'Other': 17
            },
            'attack_vectors': {
                'api_endpoints': 60,
                'file_uploads': 25,
                'auth_endpoints': 15
            },
            'recommendations': [
                "Considerar bloquear tráfico de CN y RU",
                "Implementar CAPTCHA en endpoints de autenticación",
                "Aumentar rate limiting en /api/agents/execute",
                "Revisar configuración de WAF para protección adicional"
            ]
        }


class DDoSMonitoring:
    """Sistema de monitoreo y alertas para DDoS"""
    
    def __init__(self, ddos_system: DDoSProtectionSystem, config: Dict[str, Any]):
        self.ddos_system = ddos_system
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Thresholds de alerta
        self.alert_thresholds = config.get('monitoring', {}).get('alert_thresholds', {})
        
        # Estado de alertas activas
        self.active_alerts = []
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Verifica condiciones de alerta"""
        alerts = []
        metrics = self.ddos_system.get_metrics()
        
        # Verificar ratio de requests bloqueadas
        if metrics['total_requests'] > 0:
            blocked_ratio = metrics['blocked_requests'] / metrics['total_requests']
            if blocked_ratio > self.alert_thresholds.get('blocked_requests_ratio', 0.1):
                alerts.append({
                    'type': 'high_block_ratio',
                    'message': f'High blocked requests ratio: {blocked_ratio:.2%}',
                    'severity': 'warning',
                    'timestamp': datetime.now().isoformat()
                })
        
        # Verificar número de eventos de amenaza
        if metrics['threat_events'] > self.alert_thresholds.get('threat_events', 100):
            alerts.append({
                'type': 'high_threat_activity',
                'message': f'High threat activity: {metrics["threat_events"]} events',
                'severity': 'warning',
                'timestamp': datetime.now().isoformat()
            })
        
        # Verificar health del sistema
        health = self.ddos_system.health_check()
        if health['status'] != 'healthy':
            alerts.append({
                'type': 'system_unhealthy',
                'message': f'System health degraded: {health}',
                'severity': 'critical',
                'timestamp': datetime.now().isoformat()
            })
        
        self.active_alerts.extend(alerts)
        return alerts
    
    def send_alert(self, alert: Dict[str, Any]):
        """Envía alerta por los canales configurados"""
        alert_channels = self.config.get('monitoring', {}).get('alert_channels', {})
        
        # Email alerts
        if alert_channels.get('email', {}).get('enabled'):
            self._send_email_alert(alert)
        
        # Slack alerts
        if alert_channels.get('slack', {}).get('enabled'):
            self._send_slack_alert(alert)
        
        self.logger.warning(f"Alert sent: {alert['message']}")
    
    def _send_email_alert(self, alert: Dict[str, Any]):
        """Envía alerta por email (implementación simplificada)"""
        # En implementación real, usaríamos smtplib o servicio de email
        self.logger.info(f"EMAIL ALERT: {alert}")
    
    def _send_slack_alert(self, alert: Dict[str, Any]):
        """Envía alerta por Slack (implementación simplificada)"""
        # En implementación real, usaríamos requests con webhook URL
        self.logger.info(f"SLACK ALERT: {alert}")


def create_ddos_admin_interface():
    """Crea interfaz administrativa básica para el sistema DDoS"""
    interface_code = '''
# Ejemplo de uso del sistema DDoS
from ddos_protection import DDoSProtectionSystem
from ddos_config import get_config_for_environment
from ddos_utils import DDoSAdminTools

# Inicializar sistema
config = get_config_for_environment("production")
ddos_system = DDoSProtectionSystem(config)

# Crear herramientas administrativas
admin = DDoSAdminTools(ddos_system)

# Monitoreo en tiempo real
import time
while True:
    stats = admin.get_real_time_stats()
    print(f"Requests: {stats['metrics']['total_requests']}")
    print(f"Blocked: {stats['metrics']['blocked_requests']}")
    
    alerts = ddos_monitoring.check_alerts()
    for alert in alerts:
        ddos_monitoring.send_alert(alert)
    
    time.sleep(60)  # Check every minute
'''
    return interface_code