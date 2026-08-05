#!/usr/bin/env python3
"""
Sistema de Monitoreo Integrado para SilhouetteMCP
Observa todos los sistemas en tiempo real con métricas unificadas y alertas automáticas
"""

import asyncio
import json
import time
import psutil
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
import requests
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SystemHealth:
    """Métricas de salud de un sistema"""
    system_id: str
    status: str  # healthy, warning, critical, offline
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    response_time: float
    error_rate: float
    uptime: float
    last_check: float
    timestamp: float

@dataclass
class Alert:
    """Alerta del sistema"""
    alert_id: str
    system_id: str
    severity: str  # info, warning, error, critical
    message: str
    timestamp: float
    resolved: bool = False
    resolved_at: Optional[float] = None

@dataclass
class MetricSnapshot:
    """Instantánea de métricas para análisis temporal"""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    response_time: float
    error_rate: float
    throughput: float

class SystemMonitor:
    """Monitor individual de un sistema"""
    
    def __init__(self, system_id: str, endpoint: str, check_interval: int = 30):
        self.system_id = system_id
        self.endpoint = endpoint
        self.check_interval = check_interval
        self.start_time = time.time()
        self.health_history = deque(maxlen=100)
        self.last_health = None
        
    async def check_health(self) -> SystemHealth:
        """Verifica la salud del sistema"""
        start_time = time.time()
        
        try:
            # Verificar respuesta HTTP
            response_time = await self._measure_response_time()
            
            # Obtener métricas del sistema
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Calcular tasa de errores (simulado)
            error_rate = await self._calculate_error_rate()
            
            # Determinar estado general
            status = self._determine_status(cpu_usage, memory.percent, error_rate, response_time)
            
            health = SystemHealth(
                system_id=self.system_id,
                status=status,
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                response_time=response_time,
                error_rate=error_rate,
                uptime=time.time() - self.start_time,
                last_check=time.time(),
                timestamp=time.time()
            )
            
            self.health_history.append(health)
            self.last_health = health
            
            return health
            
        except Exception as e:
            logger.error(f"Error checking health for {self.system_id}: {e}")
            
            # Sistema offline
            return SystemHealth(
                system_id=self.system_id,
                status="offline",
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                response_time=float('inf'),
                error_rate=100.0,
                uptime=time.time() - self.start_time,
                last_check=time.time(),
                timestamp=time.time()
            )
    
    async def _measure_response_time(self) -> float:
        """Mide tiempo de respuesta del endpoint"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.endpoint}/health", timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                return end_time - start_time
            else:
                return 30.0  # Respuesta lenta si hay error HTTP
                
        except requests.RequestException:
            return 30.0
    
    async def _calculate_error_rate(self) -> float:
        """Calcula tasa de errores (simulado)"""
        # En implementación real, esto consultaría logs/métricas
        # Por ahora simulamos basado en uso de recursos
        if self.last_health:
            return min(5.0 + (self.last_health.cpu_usage - 50) * 0.1, 100.0)
        return 0.0
    
    def _determine_status(self, cpu: float, memory: float, error_rate: float, response_time: float) -> str:
        """Determina el estado general del sistema"""
        if cpu > 90 or memory > 90 or error_rate > 20 or response_time > 25:
            return "critical"
        elif cpu > 70 or memory > 70 or error_rate > 10 or response_time > 15:
            return "warning"
        elif response_time > 5:
            return "warning"
        else:
            return "healthy"

class AlertManager:
    """Gestor de alertas del sistema"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.alerts = []
        self.alert_history = deque(maxlen=1000)
        self.email_config = config.get('email', {})
        
    def create_alert(self, system_id: str, severity: str, message: str) -> Alert:
        """Crea una nueva alerta"""
        alert_id = f"{system_id}_{int(time.time())}_{hash(message) % 10000}"
        
        alert = Alert(
            alert_id=alert_id,
            system_id=system_id,
            severity=severity,
            message=message,
            timestamp=time.time()
        )
        
        self.alerts.append(alert)
        self.alert_history.append(alert)
        
        # Enviar notificación
        self._send_notification(alert)
        
        logger.warning(f"ALERT [{severity.upper()}] {system_id}: {message}")
        
        return alert
    
    def resolve_alert(self, alert_id: str):
        """Resuelve una alerta"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolved_at = time.time()
                
                # Mover a historial
                self.alerts.remove(alert)
                
                logger.info(f"Alert resolved: {alert_id}")
                break
    
    def _send_notification(self, alert: Alert):
        """Envía notificación de alerta"""
        if not self.email_config:
            return
            
        try:
            subject = f"[{alert.severity.upper()}] SilhouetteMCP Alert - {alert.system_id}"
            body = f"""
            Alerta del Sistema SilhouetteMCP
            
            ID del Sistema: {alert.system_id}
            Severidad: {alert.severity.upper()}
            Mensaje: {alert.message}
            Timestamp: {datetime.fromtimestamp(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S')}
            
            ---
            Sistema de Monitoreo SilhouetteMCP
            """
            
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.email_config.get('from_email')
            msg['To'] = self.email_config.get('to_email')
            
            with smtplib.SMTP(self.email_config.get('smtp_server'), 
                            self.email_config.get('smtp_port', 587)) as server:
                server.starttls()
                server.login(self.email_config.get('username'), 
                           self.email_config.get('password'))
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")

class ScalabilityPredictor:
    """Predictor de escalabilidad basado en tendencias"""
    
    def __init__(self, history_size: int = 50):
        self.history_size = history_size
        self.metric_snapshots = defaultdict(lambda: deque(maxlen=history_size))
        
    def add_metric_snapshot(self, system_id: str, health: SystemHealth):
        """Añade una instantánea de métricas"""
        snapshot = MetricSnapshot(
            timestamp=health.timestamp,
            cpu_usage=health.cpu_usage,
            memory_usage=health.memory_usage,
            response_time=health.response_time,
            error_rate=health.error_rate,
            throughput=100.0  # Métrica simulada
        )
        
        self.metric_snapshots[system_id].append(snapshot)
    
    def predict_load(self, system_id: str, hours_ahead: int = 1) -> Dict:
        """Predice la carga futura del sistema"""
        if system_id not in self.metric_snapshots:
            return {'predicted': 'unknown', 'confidence': 0.0}
        
        snapshots = list(self.metric_snapshots[system_id])
        if len(snapshots) < 10:
            return {'predicted': 'insufficient_data', 'confidence': 0.0}
        
        # Calcular tendencia de CPU
        cpu_values = [s.cpu_usage for s in snapshots[-10:]]
        cpu_trend = self._calculate_trend(cpu_values)
        
        # Calcular tendencia de memoria
        memory_values = [s.memory_usage for s in snapshots[-10:]]
        memory_trend = self._calculate_trend(memory_values)
        
        # Predicción simple basada en tendencias
        predicted_cpu = cpu_values[-1] + (cpu_trend * hours_ahead)
        predicted_memory = memory_values[-1] + (memory_trend * hours_ahead)
        
        # Determinar capacidad
        if predicted_cpu < 60 and predicted_memory < 60:
            capacity_assessment = "adequate"
        elif predicted_cpu < 80 and predicted_memory < 80:
            capacity_assessment = "approaching_limit"
        else:
            capacity_assessment = "exceeding_capacity"
        
        # Calcular confianza basada en consistencia de tendencia
        confidence = self._calculate_confidence(cpu_values, memory_values)
        
        return {
            'predicted_cpu': min(100.0, max(0.0, predicted_cpu)),
            'predicted_memory': min(100.0, max(0.0, predicted_memory)),
            'capacity_assessment': capacity_assessment,
            'confidence': confidence,
            'recommendations': self._generate_recommendations(capacity_assessment, predicted_cpu, predicted_memory)
        }
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calcula la tendencia lineal simple"""
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        return slope
    
    def _calculate_confidence(self, cpu_values: List[float], memory_values: List[float]) -> float:
        """Calcula la confianza en la predicción"""
        cpu_variance = sum((x - sum(cpu_values)/len(cpu_values))**2 for x in cpu_values) / len(cpu_values)
        memory_variance = sum((x - sum(memory_values)/len(memory_values))**2 for x in memory_values) / len(memory_values)
        
        # Menor varianza = mayor confianza
        avg_variance = (cpu_variance + memory_variance) / 2
        confidence = max(0.0, min(1.0, 1.0 - (avg_variance / 100.0)))
        
        return confidence
    
    def _generate_recommendations(self, assessment: str, cpu: float, memory: float) -> List[str]:
        """Genera recomendaciones basadas en la predicción"""
        recommendations = []
        
        if assessment == "exceeding_capacity":
            recommendations.extend([
                "Escalamiento urgente requerido",
                "Considerar aumento de recursos",
                "Revisar rendimiento de aplicaciones"
            ])
        elif assessment == "approaching_limit":
            recommendations.extend([
                "Monitoreo cercano recomendado",
                "Preparar plan de escalamiento",
                "Optimizar uso de recursos"
            ])
        else:
            recommendations.extend([
                "Capacidad adecuada",
                "Continuar monitoreo regular",
                "Mantener niveles óptimos"
            ])
        
        if cpu > 70:
            recommendations.append("CPU crítico - optimizar procesos")
        if memory > 70:
            recommendations.append("Memoria crítica - revisar uso de memoria")
        
        return recommendations

class PerformanceReporter:
    """Generador de reportes de rendimiento"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_performance_report(self, systems: Dict[str, SystemMonitor]) -> str:
        """Genera reporte de rendimiento completo"""
        report_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"performance_report_{report_time}.json"
        filepath = self.output_dir / filename
        
        report = {
            'timestamp': time.time(),
            'generated_at': datetime.now().isoformat(),
            'systems': {}
        }
        
        for system_id, monitor in systems.items():
            if monitor.health_history:
                recent_health = list(monitor.health_history)[-10:]  # Últimos 10 checks
                
                system_report = {
                    'current_status': asdict(monitor.last_health) if monitor.last_health else None,
                    'average_metrics': self._calculate_averages(recent_health),
                    'availability': self._calculate_availability(recent_health),
                    'performance_trend': self._analyze_trend(recent_health),
                    'alerts_count': len([a for a in monitor.health_history 
                                       if a.status in ['warning', 'critical']])
                }
                
                report['systems'][system_id] = system_report
        
        # Guardar reporte
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Performance report generated: {filepath}")
        return str(filepath)
    
    def _calculate_averages(self, health_list: List[SystemHealth]) -> Dict:
        """Calcula métricas promedio"""
        if not health_list:
            return {}
        
        return {
            'cpu_usage': sum(h.cpu_usage for h in health_list) / len(health_list),
            'memory_usage': sum(h.memory_usage for h in health_list) / len(health_list),
            'response_time': sum(h.response_time for h in health_list) / len(health_list),
            'error_rate': sum(h.error_rate for h in health_list) / len(health_list)
        }
    
    def _calculate_availability(self, health_list: List[SystemHealth]) -> float:
        """Calcula disponibilidad basada en estados"""
        if not health_list:
            return 0.0
        
        healthy_checks = sum(1 for h in health_list if h.status in ['healthy', 'warning'])
        return (healthy_checks / len(health_list)) * 100.0
    
    def _analyze_trend(self, health_list: List[SystemHealth]) -> Dict:
        """Analiza tendencia de rendimiento"""
        if len(health_list) < 2:
            return {'trend': 'stable'}
        
        # Comparar primera y última medición
        first = health_list[0]
        last = health_list[-1]
        
        cpu_change = last.cpu_usage - first.cpu_usage
        memory_change = last.memory_usage - first.memory_usage
        
        if cpu_change > 10 or memory_change > 10:
            trend = 'degrading'
        elif cpu_change < -10 or memory_change < -10:
            trend = 'improving'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'cpu_change': cpu_change,
            'memory_change': memory_change
        }

class Dashboard:
    """Dashboard de estado del sistema"""
    
    def __init__(self, update_interval: int = 30):
        self.update_interval = update_interval
        self.last_update = 0
        
    def generate_dashboard(self, systems: Dict[str, SystemMonitor], alerts: List[Alert], 
                          predictions: Dict[str, Dict]) -> Dict:
        """Genera datos del dashboard"""
        dashboard = {
            'timestamp': time.time(),
            'last_update': self.last_update,
            'summary': {
                'total_systems': len(systems),
                'healthy_systems': 0,
                'warning_systems': 0,
                'critical_systems': 0,
                'offline_systems': 0,
                'active_alerts': len([a for a in alerts if not a.resolved])
            },
            'systems': {},
            'alerts': [],
            'predictions': predictions
        }
        
        # Procesar estado de sistemas
        for system_id, monitor in systems.items():
            if monitor.last_health:
                health = monitor.last_health
                
                # Contar por estado
                dashboard['summary'][f"{health.status}_systems"] += 1
                
                dashboard['systems'][system_id] = {
                    'status': health.status,
                    'metrics': {
                        'cpu': health.cpu_usage,
                        'memory': health.memory_usage,
                        'disk': health.disk_usage,
                        'response_time': health.response_time,
                        'error_rate': health.error_rate
                    },
                    'uptime_hours': health.uptime / 3600,
                    'last_check': health.last_check
                }
        
        # Procesar alertas activas
        for alert in alerts:
            if not alert.resolved:
                dashboard['alerts'].append({
                    'alert_id': alert.alert_id,
                    'system_id': alert.system_id,
                    'severity': alert.severity,
                    'message': alert.message,
                    'timestamp': alert.timestamp
                })
        
        self.last_update = time.time()
        return dashboard
    
    def save_dashboard(self, dashboard: Dict, filepath: str = "dashboard.json"):
        """Guarda dashboard en archivo"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dashboard, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Dashboard updated: {filepath}")

class IntegratedMonitoringSystem:
    """Sistema principal de monitoreo integrado"""
    
    def __init__(self, config_file: str = "monitoring_config.json"):
        self.config = self._load_config(config_file)
        self.systems = {}
        self.alert_manager = AlertManager(self.config)
        self.predictor = ScalabilityPredictor()
        self.reporter = PerformanceReporter()
        self.dashboard = Dashboard()
        self.orquestador_endpoint = self.config.get('orquestador', {}).get('endpoint', 'http://localhost:8025')
        
        self.running = False
        self.monitoring_thread = None
        
    def _load_config(self, config_file: str) -> Dict:
        """Carga configuración del sistema"""
        default_config = {
            'systems': [
                {
                    'id': 'silhouettemcp_core',
                    'endpoint': 'http://localhost:8025',
                    'check_interval': 30
                },
                {
                    'id': 'silhouettemcp_improved',
                    'endpoint': 'http://localhost:8001',
                    'check_interval': 30
                },
                {
                    'id': 'silhouettemcp_cache',
                    'endpoint': 'http://localhost:8002',
                    'check_interval': 45
                }
            ],
            'orquestador': {
                'endpoint': 'http://localhost:8025',
                'actions': {
                    'auto_recovery': True,
                    'escalate_on_critical': True,
                    'restart_failed_services': True
                }
            },
            'alerts': {
                'thresholds': {
                    'cpu_warning': 70,
                    'cpu_critical': 90,
                    'memory_warning': 70,
                    'memory_critical': 90,
                    'response_time_warning': 10,
                    'response_time_critical': 25
                },
                'email': {
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'from_email': '',
                    'to_email': '',
                    'username': '',
                    'password': ''
                }
            },
            'reports': {
                'auto_generate': True,
                'interval_hours': 24,
                'output_directory': 'reports'
            }
        }
        
        try:
            if Path(config_file).exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    
                # Combinar con configuración por defecto
                self._deep_merge(default_config, loaded_config)
                
            return default_config
            
        except Exception as e:
            logger.warning(f"Failed to load config {config_file}: {e}. Using defaults.")
            return default_config
    
    def _deep_merge(self, base: Dict, override: Dict):
        """Combina diccionarios profundamente"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def add_system(self, system_id: str, endpoint: str, check_interval: int = 30):
        """Añade un sistema al monitoreo"""
        self.systems[system_id] = SystemMonitor(system_id, endpoint, check_interval)
        logger.info(f"Added system to monitoring: {system_id}")
    
    def start_monitoring(self):
        """Inicia el monitoreo en segundo plano"""
        if self.running:
            logger.warning("Monitoring is already running")
            return
        
        self.running = True
        
        # Inicializar sistemas desde configuración
        for system_config in self.config['systems']:
            self.add_system(
                system_config['id'],
                system_config['endpoint'],
                system_config.get('check_interval', 30)
            )
        
        # Iniciar hilo de monitoreo
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("Integrated monitoring system started")
    
    def stop_monitoring(self):
        """Detiene el monitoreo"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        logger.info("Integrated monitoring system stopped")
    
    def _monitoring_loop(self):
        """Loop principal de monitoreo"""
        last_report_time = time.time()
        last_dashboard_update = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                
                # Verificar salud de sistemas
                system_alerts = []
                predictions = {}
                
                for system_id, monitor in self.systems.items():
                    try:
                        health = asyncio.run(monitor.check_health())
                        
                        # Añadir a predictor
                        self.predictor.add_metric_snapshot(system_id, health)
                        
                        # Generar predicciones
                        predictions[system_id] = self.predictor.predict_load(system_id, 1)
                        
                        # Verificar umbrales y generar alertas
                        alert = self._check_thresholds(health)
                        if alert:
                            system_alerts.append(alert)
                        
                        # Auto-recovery si está habilitado
                        if self.config['orquestador']['actions']['auto_recovery']:
                            self._check_auto_recovery(health)
                        
                    except Exception as e:
                        logger.error(f"Error monitoring {system_id}: {e}")
                
                # Actualizar dashboard cada 30 segundos
                if current_time - last_dashboard_update >= 30:
                    dashboard_data = self.dashboard.generate_dashboard(
                        self.systems, 
                        self.alert_manager.alerts, 
                        predictions
                    )
                    self.dashboard.save_dashboard(dashboard_data)
                    last_dashboard_update = current_time
                
                # Generar reporte automático cada 24 horas
                if (self.config['reports']['auto_generate'] and 
                    current_time - last_report_time >= (self.config['reports']['interval_hours'] * 3600)):
                    self.reporter.generate_performance_report(self.systems)
                    last_report_time = current_time
                
                # Esperar antes del siguiente ciclo
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)
    
    def _check_thresholds(self, health: SystemHealth) -> Optional[Alert]:
        """Verifica umbrales y genera alertas"""
        thresholds = self.config['alerts']['thresholds']
        
        # Verificar CPU
        if health.cpu_usage >= thresholds['cpu_critical']:
            return self.alert_manager.create_alert(
                health.system_id, 
                'critical',
                f"CPU usage critical: {health.cpu_usage:.1f}%"
            )
        elif health.cpu_usage >= thresholds['cpu_warning']:
            return self.alert_manager.create_alert(
                health.system_id,
                'warning',
                f"CPU usage high: {health.cpu_usage:.1f}%"
            )
        
        # Verificar memoria
        if health.memory_usage >= thresholds['memory_critical']:
            return self.alert_manager.create_alert(
                health.system_id,
                'critical',
                f"Memory usage critical: {health.memory_usage:.1f}%"
            )
        elif health.memory_usage >= thresholds['memory_warning']:
            return self.alert_manager.create_alert(
                health.system_id,
                'warning',
                f"Memory usage high: {health.memory_usage:.1f}%"
            )
        
        # Verificar tiempo de respuesta
        if health.response_time >= thresholds['response_time_critical']:
            return self.alert_manager.create_alert(
                health.system_id,
                'critical',
                f"Response time critical: {health.response_time:.1f}s"
            )
        elif health.response_time >= thresholds['response_time_warning']:
            return self.alert_manager.create_alert(
                health.system_id,
                'warning',
                f"Response time high: {health.response_time:.1f}s"
            )
        
        # Verificar sistema offline
        if health.status == 'offline':
            return self.alert_manager.create_alert(
                health.system_id,
                'critical',
                "System is offline - immediate attention required"
            )
        
        return None
    
    def _check_auto_recovery(self, health: SystemHealth):
        """Verifica condiciones para auto-recovery"""
        actions = self.config['orquestador']['actions']
        
        if not actions['auto_recovery']:
            return
        
        # Sistema crítico - intentar recuperación automática
        if health.status == 'critical' and actions['escalate_on_critical']:
            self._notify_orquestador(health.system_id, 'critical_alert', health)
        
        # Sistema offline - intentar restart
        if health.status == 'offline' and actions['restart_failed_services']:
            self._notify_orquestador(health.system_id, 'restart_service', health)
    
    def _notify_orquestador(self, system_id: str, action_type: str, health: SystemHealth):
        """Notifica al orquestador sobre acciones de recuperación"""
        try:
            payload = {
                'action': action_type,
                'system_id': system_id,
                'health_data': asdict(health),
                'timestamp': time.time()
            }
            
            response = requests.post(
                f"{self.orquestador_endpoint}/api/monitoring/alerts",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Recovery action sent to orquestador: {action_type} for {system_id}")
            else:
                logger.warning(f"Failed to send recovery action to orquestador: {response.status_code}")
                
        except requests.RequestException as e:
            logger.error(f"Failed to notify orquestador: {e}")
    
    def get_system_status(self) -> Dict:
        """Obtiene estado actual de todos los sistemas"""
        status = {
            'timestamp': time.time(),
            'systems': {}
        }
        
        for system_id, monitor in self.systems.items():
            if monitor.last_health:
                status['systems'][system_id] = asdict(monitor.last_health)
            else:
                status['systems'][system_id] = {'status': 'unknown', 'system_id': system_id}
        
        return status
    
    def get_alerts(self) -> List[Dict]:
        """Obtiene alertas activas"""
        return [asdict(alert) for alert in self.alert_manager.alerts]
    
    def get_predictions(self) -> Dict:
        """Obtiene predicciones de todos los sistemas"""
        predictions = {}
        for system_id in self.systems.keys():
            predictions[system_id] = self.predictor.predict_load(system_id, 1)
        return predictions
    
    def generate_report(self) -> str:
        """Genera reporte manual de rendimiento"""
        return self.reporter.generate_performance_report(self.systems)
    
    def get_dashboard_data(self) -> Dict:
        """Obtiene datos actuales del dashboard"""
        return self.dashboard.generate_dashboard(
            self.systems,
            self.alert_manager.alerts,
            self.get_predictions()
        )

def main():
    """Función principal para ejecutar el sistema de monitoreo"""
    print("🚀 Iniciando Sistema de Monitoreo Integrado SilhouetteMCP")
    
    # Crear instancia del sistema de monitoreo
    monitoring_system = IntegratedMonitoringSystem()
    
    # Iniciar monitoreo
    monitoring_system.start_monitoring()
    
    try:
        # Mantener el programa corriendo
        print("✅ Sistema de monitoreo activo. Presiona Ctrl+C para detener.")
        while True:
            time.sleep(60)
            
            # Mostrar estado cada minuto
            status = monitoring_system.get_system_status()
            active_alerts = len(monitoring_system.get_alerts())
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"Sistemas: {len(status['systems'])}, "
                  f"Alertas activas: {active_alerts}")
            
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo sistema de monitoreo...")
        monitoring_system.stop_monitoring()
        print("✅ Sistema de monitoreo detenido correctamente")

if __name__ == "__main__":
    main()