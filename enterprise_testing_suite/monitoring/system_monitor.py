"""
Sistema de Monitoreo y Alertas Automatizadas
"""

import asyncio
import time
import psutil
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Callable
from dataclasses import dataclass
from pathlib import Path

from utils.base_utils import TestLogger, MetricsCollector, TestResult
from config.test_config import *

@dataclass
class AlertRule:
    """Regla de alerta"""
    name: str
    metric: str
    threshold: float
    comparison: str  # "greater_than", "less_than", "equals"
    duration_seconds: int
    severity: str  # "info", "warning", "critical"
    enabled: bool = True

@dataclass
class Alert:
    """Alerta generada"""
    rule_name: str
    metric: str
    current_value: float
    threshold: float
    severity: str
    timestamp: str
    message: str
    resolved: bool = False

class SystemMonitor:
    """Monitor del sistema en tiempo real"""
    
    def __init__(self):
        self.logger = TestLogger("SystemMonitor", PROJECT_ROOT / "logs" / "monitor.log")
        self.metrics_collector = MetricsCollector()
        self.alert_rules = self._load_alert_rules()
        self.active_alerts: List[Alert] = []
        self.monitoring = False
        
    def _load_alert_rules(self) -> List[AlertRule]:
        """Carga reglas de alerta desde configuración"""
        rules = [
            AlertRule(
                name="high_cpu_usage",
                metric="cpu_usage_percent",
                threshold=MONITORING_CONFIG["alert_thresholds"]["cpu_usage"],
                comparison="greater_than",
                duration_seconds=60,
                severity="warning"
            ),
            AlertRule(
                name="high_memory_usage",
                metric="memory_usage_percent", 
                threshold=MONITORING_CONFIG["alert_thresholds"]["memory_usage"],
                comparison="greater_than",
                duration_seconds=60,
                severity="warning"
            ),
            AlertRule(
                name="critical_memory_usage",
                metric="memory_usage_percent",
                threshold=95.0,
                comparison="greater_than",
                duration_seconds=30,
                severity="critical"
            ),
            AlertRule(
                name="high_response_time",
                metric="response_time_seconds",
                threshold=MONITORING_CONFIG["alert_thresholds"]["response_time"],
                comparison="greater_than", 
                duration_seconds=120,
                severity="warning"
            ),
            AlertRule(
                name="high_error_rate",
                metric="error_rate_percent",
                threshold=MONITORING_CONFIG["alert_thresholds"]["error_rate"],
                comparison="greater_than",
                duration_seconds=60,
                severity="critical"
            ),
            AlertRule(
                name="disk_usage_high",
                metric="disk_usage_percent",
                threshold=MONITORING_CONFIG["alert_thresholds"]["disk_usage"],
                comparison="greater_than",
                duration_seconds=300,
                severity="warning"
            ),
            AlertRule(
                name="low_disk_space",
                metric="disk_usage_percent",
                threshold=95.0,
                comparison="greater_than",
                duration_seconds=60,
                severity="critical"
            )
        ]
        return rules
    
    def get_system_metrics(self) -> Dict[str, float]:
        """Obtiene métricas actuales del sistema"""
        metrics = {}
        
        try:
            # Métricas de CPU
            metrics["cpu_usage_percent"] = psutil.cpu_percent(interval=1)
            
            # Métricas de memoria
            memory = psutil.virtual_memory()
            metrics["memory_usage_percent"] = memory.percent
            metrics["memory_available_gb"] = memory.available / (1024**3)
            metrics["memory_used_gb"] = memory.used / (1024**3)
            
            # Métricas de disco
            disk = psutil.disk_usage('/')
            metrics["disk_usage_percent"] = (disk.used / disk.total) * 100
            metrics["disk_free_gb"] = disk.free / (1024**3)
            
            # Métricas de red
            network = psutil.net_io_counters()
            metrics["network_bytes_sent"] = network.bytes_sent
            metrics["network_bytes_recv"] = network.bytes_recv
            
            # Métricas de procesos
            processes = len(psutil.pids())
            metrics["process_count"] = processes
            
            # Métricas personalizadas (simuladas)
            if hasattr(self.metrics_collector, 'metrics'):
                custom_metrics = self.metrics_collector.metrics.get("response_times", {})
                if custom_metrics:
                    # Calcular tiempo promedio de respuesta
                    all_times = []
                    for endpoint_times in custom_metrics.values():
                        all_times.extend(endpoint_times)
                    if all_times:
                        metrics["response_time_seconds"] = sum(all_times) / len(all_times)
            
            # Métricas de error rate simuladas
            error_count = len([alert for alert in self.active_alerts if not alert.resolved])
            total_checks = 100  # Simular 100 checks
            metrics["error_rate_percent"] = (error_count / total_checks) * 100
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {str(e)}")
        
        return metrics
    
    def check_alert_conditions(self, metrics: Dict[str, float]) -> List[Alert]:
        """Verifica condiciones de alerta"""
        new_alerts = []
        
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            
            metric_value = metrics.get(rule.metric)
            if metric_value is None:
                continue
            
            # Verificar si la condición se cumple
            condition_met = self._evaluate_condition(metric_value, rule.threshold, rule.comparison)
            
            if condition_met:
                # Crear alerta
                alert = Alert(
                    rule_name=rule.name,
                    metric=rule.metric,
                    current_value=metric_value,
                    threshold=rule.threshold,
                    severity=rule.severity,
                    timestamp=datetime.now().isoformat(),
                    message=self._generate_alert_message(rule, metric_value)
                )
                
                # Verificar si ya existe una alerta similar activa
                existing_alert = self._find_existing_alert(rule.name, rule.metric)
                if not existing_alert:
                    new_alerts.append(alert)
                    self.active_alerts.append(alert)
                    self.logger.warning(f"Alert triggered: {alert.message}")
        
        return new_alerts
    
    def _evaluate_condition(self, value: float, threshold: float, comparison: str) -> bool:
        """Evalúa condición de alerta"""
        if comparison == "greater_than":
            return value > threshold
        elif comparison == "less_than":
            return value < threshold
        elif comparison == "equals":
            return abs(value - threshold) < 0.01
        return False
    
    def _generate_alert_message(self, rule: AlertRule, current_value: float) -> str:
        """Genera mensaje de alerta"""
        return f"{rule.name}: {rule.metric} is {current_value:.2f} (threshold: {rule.threshold})"
    
    def _find_existing_alert(self, rule_name: str, metric: str) -> Alert:
        """Busca alerta existente"""
        for alert in self.active_alerts:
            if not alert.resolved and alert.rule_name == rule_name:
                return alert
        return None
    
    async def start_monitoring(self, duration_minutes: int = 60):
        """Inicia monitoreo continuo"""
        self.monitoring = True
        monitoring_end = time.time() + (duration_minutes * 60)
        
        self.logger.info(f"Starting system monitoring for {duration_minutes} minutes")
        
        while self.monitoring and time.time() < monitoring_end:
            try:
                # Recolectar métricas
                metrics = self.get_system_metrics()
                
                # Verificar alertas
                new_alerts = self.check_alert_conditions(metrics)
                
                # Log métricas cada minuto
                if int(time.time()) % 60 == 0:
                    self.logger.info(f"System metrics: {metrics}")
                
                # Resolver alertas si es necesario
                self._resolve_alerts_if_needed(metrics)
                
                # Esperar 5 segundos antes de la siguiente verificación
                await asyncio.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(10)
        
        self.monitoring = False
        self.logger.info("System monitoring stopped")
    
    def _resolve_alerts_if_needed(self, metrics: Dict[str, float]):
        """Resuelve alertas si las condiciones mejoran"""
        for alert in self.active_alerts:
            if alert.resolved:
                continue
            
            rule = next((r for r in self.alert_rules if r.name == alert.rule_name), None)
            if rule:
                metric_value = metrics.get(rule.metric)
                if metric_value is not None:
                    condition_met = self._evaluate_condition(metric_value, rule.threshold, rule.comparison)
                    
                    # Si la condición ya no se cumple, marcar como resuelta
                    if not condition_met:
                        alert.resolved = True
                        alert.timestamp = datetime.now().isoformat()
                        self.logger.info(f"Alert resolved: {alert.rule_name}")

class AlertNotificationSystem:
    """Sistema de notificaciones de alertas"""
    
    def __init__(self):
        self.logger = TestLogger("AlertNotifications", PROJECT_ROOT / "logs" / "alerts.log")
        self.notification_channels = self._setup_notification_channels()
    
    def _setup_notification_channels(self) -> Dict[str, Callable]:
        """Configura canales de notificación"""
        return {
            "email": self._send_email_alert,
            "webhook": self._send_webhook_alert,
            "log": self._log_alert,
            "file": self._write_alert_to_file
        }
    
    def send_alert(self, alert: Alert, channels: List[str] = None):
        """Envía alerta por los canales especificados"""
        if channels is None:
            channels = ["log", "file"]  # Canales por defecto
        
        for channel in channels:
            if channel in self.notification_channels:
                try:
                    self.notification_channels[channel](alert)
                except Exception as e:
                    self.logger.error(f"Failed to send alert via {channel}: {str(e)}")
    
    def _send_email_alert(self, alert: Alert):
        """Simula envío de email"""
        self.logger.info(f"EMAIL ALERT [{alert.severity.upper()}]: {alert.message}")
        # En implementación real, aquí se enviaría el email
    
    def _send_webhook_alert(self, alert: Alert):
        """Simula envío de webhook"""
        webhook_data = {
            "alert": {
                "rule_name": alert.rule_name,
                "metric": alert.metric,
                "current_value": alert.current_value,
                "threshold": alert.threshold,
                "severity": alert.severity,
                "timestamp": alert.timestamp,
                "message": alert.message
            }
        }
        self.logger.info(f"WEBHOOK ALERT: {json.dumps(webhook_data, indent=2)}")
        # En implementación real, aquí se haría la llamada HTTP
    
    def _log_alert(self, alert: Alert):
        """Log de alerta"""
        log_level = "WARNING" if alert.severity == "warning" else "ERROR" if alert.severity == "critical" else "INFO"
        self.logger.warning(f"ALERT [{log_level}]: {alert.message}")
    
    def _write_alert_to_file(self, alert: Alert):
        """Escribe alerta a archivo"""
        alerts_file = PROJECT_ROOT / "logs" / "alerts.json"
        
        alert_data = {
            "timestamp": alert.timestamp,
            "rule_name": alert.rule_name,
            "metric": alert.metric,
            "current_value": alert.current_value,
            "threshold": alert.threshold,
            "severity": alert.severity,
            "message": alert.message,
            "resolved": alert.resolved
        }
        
        # Leer alertas existentes
        existing_alerts = []
        if alerts_file.exists():
            try:
                with open(alerts_file, 'r') as f:
                    existing_alerts = json.load(f)
            except:
                existing_alerts = []
        
        # Agregar nueva alerta
        existing_alerts.append(alert_data)
        
        # Escribir de vuelta al archivo
        with open(alerts_file, 'w') as f:
            json.dump(existing_alerts, f, indent=2)

class MonitoringDashboard:
    """Dashboard de monitoreo en tiempo real"""
    
    def __init__(self):
        self.logger = TestLogger("MonitoringDashboard", PROJECT_ROOT / "logs" / "dashboard.log")
        self.monitor = SystemMonitor()
        self.notification_system = AlertNotificationSystem()
    
    def generate_monitoring_report(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """Genera reporte de monitoreo"""
        report = {
            "report_timestamp": datetime.now().isoformat(),
            "monitoring_duration_minutes": duration_minutes,
            "system_metrics": {},
            "alerts_summary": {},
            "recommendations": []
        }
        
        # Recolectar métricas del sistema
        system_metrics = self.monitor.get_system_metrics()
        report["system_metrics"] = system_metrics
        
        # Resumen de alertas
        active_alerts = [alert for alert in self.monitor.active_alerts if not alert.resolved]
        resolved_alerts = [alert for alert in self.monitor.active_alerts if alert.resolved]
        
        report["alerts_summary"] = {
            "active_alerts": len(active_alerts),
            "resolved_alerts": len(resolved_alerts),
            "critical_alerts": len([a for a in active_alerts if a.severity == "critical"]),
            "warning_alerts": len([a for a in active_alerts if a.severity == "warning"]),
            "active_alert_details": [
                {
                    "rule_name": alert.rule_name,
                    "metric": alert.metric,
                    "current_value": alert.current_value,
                    "threshold": alert.threshold,
                    "severity": alert.severity
                } for alert in active_alerts
            ]
        }
        
        # Generar recomendaciones
        recommendations = self._generate_recommendations(system_metrics, active_alerts)
        report["recommendations"] = recommendations
        
        return report
    
    def _generate_recommendations(self, metrics: Dict[str, float], alerts: List[Alert]) -> List[str]:
        """Genera recomendaciones basadas en métricas y alertas"""
        recommendations = []
        
        # Recomendaciones basadas en CPU
        if metrics.get("cpu_usage_percent", 0) > 80:
            recommendations.append("CPU usage is high. Consider scaling resources or optimizing CPU-intensive processes.")
        
        # Recomendaciones basadas en memoria
        if metrics.get("memory_usage_percent", 0) > 85:
            recommendations.append("Memory usage is high. Consider increasing available memory or optimizing memory usage.")
        
        # Recomendaciones basadas en disco
        if metrics.get("disk_usage_percent", 0) > 90:
            recommendations.append("Disk space is low. Consider cleaning up logs or adding more storage.")
        
        # Recomendaciones basadas en alertas
        critical_alerts = [a for a in alerts if a.severity == "critical"]
        if critical_alerts:
            recommendations.append(f"System has {len(critical_alerts)} critical alerts requiring immediate attention.")
        
        # Recomendaciones de performance
        response_time = metrics.get("response_time_seconds", 0)
        if response_time > 2.0:
            recommendations.append("Response times are high. Consider optimizing database queries or increasing server capacity.")
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], output_file: Path):
        """Guarda reporte de monitoreo"""
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Monitoring report saved to {output_file}")

# Instancias globales
system_monitor = SystemMonitor()
alert_notifications = AlertNotificationSystem()
monitoring_dashboard = MonitoringDashboard()

async def run_monitoring_system(duration_minutes: int = 60):
    """Ejecuta el sistema de monitoreo completo"""
    # Iniciar monitoreo en background
    monitoring_task = asyncio.create_task(
        system_monitor.start_monitoring(duration_minutes)
    )
    
    # Ejecutar monitoreo por el tiempo especificado
    try:
        await monitoring_task
    except KeyboardInterrupt:
        system_monitor.monitoring = False
        monitoring_task.cancel()

if __name__ == "__main__":
    asyncio.run(run_monitoring_system(60))
