"""
Configuración del Sistema de Métricas Avanzadas
Permite personalizar todos los aspectos del sistema de métricas
"""
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class MetricsConfig:
    """Configuración principal de métricas"""
    # Configuración general
    enabled: bool = True
    collection_interval_seconds: int = 10
    retention_days: int = 30
    database_path: str = "metrics_timeseries.db"
    
    # Configuración de alertas
    alert_enabled: bool = True
    alert_check_interval_seconds: int = 5
    alert_escalation_enabled: bool = True
    alert_escalation_minutes: int = 15
    
    # Configuración de dashboards
    dashboard_enabled: bool = True
    dashboard_update_interval_seconds: int = 30
    grafana_integration: bool = True
    
    # Configuración de Prometheus
    prometheus_export_enabled: bool = True
    prometheus_port: int = 9090
    prometheus_endpoint: str = "/metrics"
    
    # Configuración de percentiles
    percentile_calculation_enabled: bool = True
    percentile_samples_limit: int = 1000
    percentile_calculation_interval: int = 60
    
    # Configuración de capacidad
    capacity_planning_enabled: bool = True
    capacity_forecast_days: int = 30
    capacity_trend_window_hours: int = 24
    
    # Configuración de simulación
    simulation_mode: bool = True
    simulation_data_realistic: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración a diccionario"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MetricsConfig':
        """Crea configuración desde diccionario"""
        return cls(**data)
    
    def save_to_file(self, file_path: str):
        """Guarda configuración a archivo"""
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'MetricsConfig':
        """Carga configuración desde archivo"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


@dataclass
class AlertConfig:
    """Configuración de alertas personalizadas"""
    id: str
    name: str
    description: str
    metric_name: str
    threshold_value: float
    operator: str  # ">", "<", ">=", "<=", "==", "!="
    severity: str  # "info", "warning", "critical", "emergency"
    agent_name: Optional[str] = None
    enabled: bool = True
    cooldown_minutes: int = 5
    escalation_enabled: bool = True
    notification_channels: List[str] = None
    
    def __post_init__(self):
        if self.notification_channels is None:
            self.notification_channels = ["log"]


@dataclass
class DashboardConfig:
    """Configuración de dashboards"""
    name: str
    description: str
    panels: List[Dict[str, Any]]
    refresh_interval: str = "5s"
    time_range: str = "1h"
    tags: List[str] = None
    variables: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = ["mcp", "metrics"]
        if self.variables is None:
            self.variables = []


@dataclass
class BusinessMetricsConfig:
    """Configuración de métricas de negocio"""
    kpis: Dict[str, Dict[str, Any]] = None
    sla_targets: Dict[str, float] = None
    cost_targets: Dict[str, float] = None
    revenue_targets: Dict[str, float] = None
    
    def __post_init__(self):
        if self.kpis is None:
            self.kpis = {
                "tasks_per_hour": {"target": 150, "unit": "tasks"},
                "response_time_p95": {"target": 1000, "unit": "ms"},
                "sla_compliance": {"target": 99.5, "unit": "percent"},
                "customer_satisfaction": {"target": 4.5, "unit": "score"}
            }
        if self.sla_targets is None:
            self.sla_targets = {
                "availability": 99.9,
                "response_time": 1.0,
                "throughput": 100.0
            }
        if self.cost_targets is None:
            self.cost_targets = {
                "cost_per_operation": 0.25,
                "monthly_operational_cost": 10000.0
            }
        if self.revenue_targets is None:
            self.revenue_targets = {
                "monthly_revenue": 50000.0,
                "profit_margin": 0.30
            }


class MetricsConfigurationManager:
    """Gestor de configuración del sistema de métricas"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.metrics_config = MetricsConfig()
        self.alerts_config: List[AlertConfig] = []
        self.dashboards_config: List[DashboardConfig] = []
        self.business_config = BusinessMetricsConfig()
        
        self._load_default_configs()
        self._load_configs_from_files()
    
    def _load_default_configs(self):
        """Carga configuraciones por defecto"""
        # Alertas por defecto
        default_alerts = [
            AlertConfig(
                id="high_cpu",
                name="High CPU Usage",
                description="CPU usage exceeds 80%",
                metric_name="mcp_cpu_usage_percent",
                threshold_value=80.0,
                operator=">",
                severity="warning",
                enabled=True,
                cooldown_minutes=5
            ),
            AlertConfig(
                id="high_memory",
                name="High Memory Usage", 
                description="Memory usage exceeds 85%",
                metric_name="mcp_memory_usage_percent",
                threshold_value=85.0,
                operator=">",
                severity="warning",
                enabled=True,
                cooldown_minutes=5
            ),
            AlertConfig(
                id="high_error_rate",
                name="High Error Rate",
                description="Error rate exceeds 5%", 
                metric_name="mcp_error_rate_ratio",
                threshold_value=0.05,
                operator=">",
                severity="critical",
                enabled=True,
                cooldown_minutes=2
            ),
            AlertConfig(
                id="agent_unhealthy",
                name="Agent Unhealthy",
                description="Agent health score below 60",
                metric_name="mcp_agent_health_score",
                threshold_value=60.0,
                operator="<",
                severity="critical",
                enabled=True,
                cooldown_minutes=3
            ),
            AlertConfig(
                id="sla_violation",
                name="SLA Violation",
                description="SLA compliance below 95%",
                metric_name="mcp_sla_compliance_percent",
                threshold_value=95.0,
                operator="<",
                severity="emergency",
                enabled=True,
                cooldown_minutes=1,
                escalation_enabled=True
            )
        ]
        self.alerts_config = default_alerts
        
        # Dashboards por defecto
        default_dashboards = [
            DashboardConfig(
                name="MCP System Overview",
                description="Main dashboard for system overview",
                panels=[
                    {
                        "title": "System Resources",
                        "type": "graph",
                        "targets": ["mcp_cpu_usage_percent", "mcp_memory_usage_percent", "mcp_disk_usage_percent"]
                    },
                    {
                        "title": "Agent Health",
                        "type": "graph", 
                        "targets": ["mcp_agent_health_score"]
                    },
                    {
                        "title": "Request Latency",
                        "type": "graph",
                        "targets": ["mcp_latency_milliseconds"]
                    },
                    {
                        "title": "Throughput",
                        "type": "graph",
                        "targets": ["mcp_throughput_operations_per_second"]
                    }
                ],
                refresh_interval="5s",
                time_range="1h"
            ),
            DashboardConfig(
                name="MCP Business Metrics",
                description="Dashboard for business KPIs",
                panels=[
                    {
                        "title": "SLA Compliance",
                        "type": "stat",
                        "targets": ["mcp_sla_compliance_percent"]
                    },
                    {
                        "title": "Tasks Completed",
                        "type": "graph",
                        "targets": ["mcp_business_tasks_completed"]
                    },
                    {
                        "title": "Cost Analysis",
                        "type": "graph",
                        "targets": ["mcp_business_cost_per_operation"]
                    }
                ],
                refresh_interval="1m",
                time_range="24h"
            ),
            DashboardConfig(
                name="MCP Capacity Planning",
                description="Dashboard for capacity planning",
                panels=[
                    {
                        "title": "Capacity Usage",
                        "type": "graph",
                        "targets": ["mcp_capacity_usage_percent"]
                    },
                    {
                        "title": "Resource Trends",
                        "type": "graph",
                        "targets": ["mcp_cpu_usage_percent", "mcp_memory_usage_percent"]
                    },
                    {
                        "title": "Scaling Recommendations",
                        "type": "table",
                        "targets": []
                    }
                ],
                refresh_interval="5m",
                time_range="24h"
            )
        ]
        self.dashboards_config = default_dashboards
    
    def _load_configs_from_files(self):
        """Carga configuraciones desde archivos"""
        # Cargar configuración principal
        metrics_file = self.config_dir / "metrics_config.json"
        if metrics_file.exists():
            self.metrics_config = MetricsConfig.load_from_file(str(metrics_file))
        
        # Cargar alertas
        alerts_file = self.config_dir / "alerts_config.json"
        if alerts_file.exists():
            with open(alerts_file, 'r') as f:
                alerts_data = json.load(f)
                self.alerts_config = [AlertConfig(**alert) for alert in alerts_data]
        
        # Cargar dashboards
        dashboards_file = self.config_dir / "dashboards_config.json"
        if dashboards_file.exists():
            with open(dashboards_file, 'r') as f:
                dashboards_data = json.load(f)
                self.dashboards_config = [DashboardConfig(**dashboard) for dashboard in dashboards_data]
        
        # Cargar configuración de negocio
        business_file = self.config_dir / "business_config.json"
        if business_file.exists():
            with open(business_file, 'r') as f:
                business_data = json.load(f)
                self.business_config = BusinessMetricsConfig(**business_data)
    
    def save_configs_to_files(self):
        """Guarda todas las configuraciones a archivos"""
        # Guardar configuración principal
        self.metrics_config.save_to_file(str(self.config_dir / "metrics_config.json"))
        
        # Guardar alertas
        alerts_data = [asdict(alert) for alert in self.alerts_config]
        with open(self.config_dir / "alerts_config.json", 'w') as f:
            json.dump(alerts_data, f, indent=2)
        
        # Guardar dashboards
        dashboards_data = [asdict(dashboard) for dashboard in self.dashboards_config]
        with open(self.config_dir / "dashboards_config.json", 'w') as f:
            json.dump(dashboards_data, f, indent=2)
        
        # Guardar configuración de negocio
        with open(self.config_dir / "business_config.json", 'w') as f:
            json.dump(asdict(self.business_config), f, indent=2)
    
    def add_custom_alert(self, alert: AlertConfig):
        """Agregar alerta personalizada"""
        # Verificar que no exista ya
        existing = next((a for a in self.alerts_config if a.id == alert.id), None)
        if existing:
            self.alerts_config.remove(existing)
        self.alerts_config.append(alert)
    
    def remove_alert(self, alert_id: str):
        """Eliminar alerta"""
        self.alerts_config = [a for a in self.alerts_config if a.id != alert_id]
    
    def add_custom_dashboard(self, dashboard: DashboardConfig):
        """Agregar dashboard personalizado"""
        # Verificar que no exista ya
        existing = next((d for d in self.dashboards_config if d.name == dashboard.name), None)
        if existing:
            self.dashboards_config.remove(existing)
        self.dashboards_config.append(dashboard)
    
    def get_metrics_config(self) -> MetricsConfig:
        """Obtener configuración de métricas"""
        return self.metrics_config
    
    def get_alerts_config(self) -> List[AlertConfig]:
        """Obtener configuración de alertas"""
        return self.alerts_config
    
    def get_dashboards_config(self) -> List[DashboardConfig]:
        """Obtener configuración de dashboards"""
        return self.dashboards_config
    
    def get_business_config(self) -> BusinessMetricsConfig:
        """Obtener configuración de negocio"""
        return self.business_config
    
    def generate_prometheus_config(self) -> str:
        """Generar configuración de Prometheus"""
        return f"""
# Configuración de Prometheus para MCP Core Superior
global:
  scrape_interval: {self.metrics_config.collection_interval_seconds}s
  evaluation_interval: {self.metrics_config.collection_interval_seconds}s

rule_files:
  - "mcp_alerts.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'mcp-advanced-metrics'
    static_configs:
      - targets: ['localhost:{self.metrics_config.prometheus_port}']
    metrics_path: '{self.metrics_config.prometheus_endpoint}'
    scrape_interval: {self.metrics_config.collection_interval_seconds}s
"""
    
    def generate_grafana_datasources(self) -> Dict[str, Any]:
        """Generar configuración de datasources para Grafana"""
        return {
            "apiVersion": 1,
            "datasources": [
                {
                    "name": "Prometheus",
                    "type": "prometheus",
                    "url": f"http://localhost:{self.metrics_config.prometheus_port}",
                    "access": "proxy",
                    "isDefault": True
                }
            ]
        }
    
    def update_metric_thresholds(self, metric_name: str, new_threshold: float, operator: str = ">"):
        """Actualizar umbral de una métrica"""
        for alert in self.alerts_config:
            if alert.metric_name == metric_name:
                alert.threshold_value = new_threshold
                alert.operator = operator


# Instancia global del gestor de configuración
_config_manager: Optional[MetricsConfigurationManager] = None

def get_metrics_config_manager(config_dir: str = "config") -> MetricsConfigurationManager:
    """Obtener instancia global del gestor de configuración"""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = MetricsConfigurationManager(config_dir)
    
    return _config_manager


def create_default_configs(config_dir: str = "config"):
    """Crear configuraciones por defecto"""
    manager = MetricsConfigurationManager(config_dir)
    manager.save_configs_to_files()
    return manager


if __name__ == "__main__":
    # Ejemplo de uso
    import asyncio
    
    async def demo_config():
        """Demostración de configuración"""
        
        # Crear configuración por defecto
        manager = create_default_configs()
        
        # Agregar alerta personalizada
        custom_alert = AlertConfig(
            id="custom_high_load",
            name="High System Load",
            description="Load average exceeds threshold",
            metric_name="mcp_load_average_1min",
            threshold_value=2.0,
            operator=">",
            severity="warning",
            notification_channels=["log", "email"]
        )
        manager.add_custom_alert(custom_alert)
        
        # Actualizar configuración
        manager.metrics_config.collection_interval_seconds = 5
        manager.metrics_config.simulation_mode = True
        
        # Guardar cambios
        manager.save_configs_to_files()
        
        # Mostrar configuración actual
        print("=== Metrics Configuration ===")
        print(json.dumps(manager.get_metrics_config().to_dict(), indent=2))
        
        print("\n=== Alerts Configuration ===")
        for alert in manager.get_alerts_config():
            print(f"- {alert.name}: {alert.threshold_value} {alert.operator}")
        
        print("\n=== Prometheus Config ===")
        print(manager.generate_prometheus_config())
        
        print("\n=== Grafana Datasources ===")
        print(json.dumps(manager.generate_grafana_datasources(), indent=2))
    
    asyncio.run(demo_config())