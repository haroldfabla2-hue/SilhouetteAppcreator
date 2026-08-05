"""
Configuración del Dashboard de Observabilidad para MCP Core Superior

Este módulo proporciona configuración para dashboards de observabilidad
que integran métricas de OpenTelemetry con visualizaciones avanzadas.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from .opentelemetry_system import get_otel_system, TraceConfig, ExportBackend


class DashboardType(str, Enum):
    """Tipos de dashboard disponibles"""
    GRAFANA = "grafana"
    PROMETHEUS = "prometheus"
    JAEGER_UI = "jaeger_ui"
    ZIPKIN = "zipkin"
    OPENTELEMETRY_COLLECTOR = "otel_collector"


@dataclass
class DashboardConfig:
    """Configuración del dashboard de observabilidad"""
    dashboard_type: DashboardType = DashboardType.GRAFANA
    enabled: bool = True
    host: str = "localhost"
    port: int = 3000  # Grafana default
    prometheus_port: int = 9090  # Prometheus default
    jaeger_port: int = 16686  # Jaeger UI default
    zipkin_port: int = 9411  # Zipkin default
    update_interval: int = 30  # seconds
    retention_days: int = 30
    metrics_retention: str = "30d"
    traces_retention: str = "30d"
    
    # Métricas específicas a mostrar
    key_metrics: Set[str] = field(default_factory=lambda: {
        "mcp.trace.span.duration",
        "mcp.trace.span.count", 
        "mcp.trace.errors.count",
        "mcp.agent.execution.time",
        "mcp.agent.success.rate",
        "mcp.database.operation.duration"
    })
    
    # Alertas configurables
    alerts: Dict[str, Any] = field(default_factory=lambda: {
        "error_rate_threshold": 10.0,  # percentage
        "response_time_threshold": 5.0,  # seconds
        "agent_execution_threshold": 30.0,  # seconds
        "database_query_threshold": 2.0  # seconds
    })
    
    # Paneles personalizados
    custom_panels: List[Dict[str, Any]] = field(default_factory=list)


class ObservabilityDashboard:
    """Dashboard unificado para métricas y tracing de MCP Core"""
    
    def __init__(self, config: DashboardConfig = None):
        self.config = config or DashboardConfig()
        self.logger = logging.getLogger(__name__)
        self.otel_system = get_otel_system()
        
        # Métricas en tiempo real
        self.real_time_metrics: Dict[str, Any] = {}
        self.trend_data: Dict[str, List[Dict[str, Any]]] = {}
        
        # Configuración de alertas
        self.alert_rules = self._setup_alert_rules()
        
    def _setup_alert_rules(self) -> Dict[str, Any]:
        """Configurar reglas de alertas"""
        return {
            "high_error_rate": {
                "metric": "mcp.trace.errors.count",
                "condition": "rate([5m]) > " + str(self.config.alerts["error_rate_threshold"] / 100),
                "severity": "warning",
                "message": "Error rate está por encima del umbral configurado"
            },
            "slow_agents": {
                "metric": "mcp.agent.execution.time",
                "condition": "quantile(0.95, rate([5m])) > " + str(self.config.alerts["agent_execution_threshold"]),
                "severity": "warning", 
                "message": "Tiempo de ejecución de agentes está degradado"
            },
            "slow_database": {
                "metric": "mcp.database.operation.duration",
                "condition": "quantile(0.95, rate([5m])) > " + str(self.config.alerts["database_query_threshold"]),
                "severity": "warning",
                "message": "Operaciones de base de datos están lentas"
            }
        }
    
    async def start_real_time_monitoring(self):
        """Iniciar monitoreo en tiempo real"""
        self.logger.info("Starting real-time monitoring dashboard")
        
        # Actualizar métricas cada interval configurado
        while True:
            try:
                await self._update_real_time_metrics()
                await self._check_alerts()
                await asyncio.sleep(self.config.update_interval)
            except Exception as e:
                self.logger.error(f"Error in real-time monitoring: {e}")
                await asyncio.sleep(5)
    
    async def _update_real_time_metrics(self):
        """Actualizar métricas en tiempo real"""
        trace_summary = self.otel_system.get_trace_summary()
        
        # Métricas básicas
        self.real_time_metrics.update({
            "timestamp": datetime.now().isoformat(),
            "traces_active": trace_summary.get("instrumentation", {}).get("agents_instrumented", 0),
            "error_count_last_hour": await self._get_error_count_last_hour(),
            "average_response_time": await self._get_average_response_time(),
            "agents_success_rate": await self._get_agents_success_rate(),
            "database_avg_duration": await self._get_database_avg_duration()
        })
        
        # Actualizar datos de tendencia
        await self._update_trend_data()
    
    async def _get_error_count_last_hour(self) -> int:
        """Obtener cantidad de errores en la última hora"""
        # Esto requeriría una consulta real al backend de tracing
        return 0  # Placeholder
    
    async def _get_average_response_time(self) -> float:
        """Obtener tiempo promedio de respuesta"""
        # Placeholder - requeriría consulta real
        return 0.0
    
    async def _get_agents_success_rate(self) -> float:
        """Obtener tasa de éxito de agentes"""
        # Placeholder - requeriría consulta real
        return 0.95
    
    async def _get_database_avg_duration(self) -> float:
        """Obtener duración promedio de operaciones de BD"""
        # Placeholder - requeriría consulta real
        return 0.1
    
    async def _update_trend_data(self):
        """Actualizar datos de tendencia"""
        timestamp = datetime.now()
        
        # Simular datos de tendencia (en implementación real, esto vendría de métricas reales)
        trends = {
            "error_rate": [0.05, 0.03, 0.07, 0.02, 0.04, 0.06, 0.03],
            "response_time": [0.5, 0.6, 0.4, 0.7, 0.5, 0.6, 0.4],
            "throughput": [100, 120, 90, 110, 105, 115, 95]
        }
        
        for metric_name, values in trends.items():
            if metric_name not in self.trend_data:
                self.trend_data[metric_name] = []
            
            self.trend_data[metric_name].append({
                "timestamp": timestamp.isoformat(),
                "value": values[-1]
            })
            
            # Mantener solo los últimos 24 datos
            if len(self.trend_data[metric_name]) > 24:
                self.trend_data[metric_name] = self.trend_data[metric_name][-24:]
    
    async def _check_alerts(self):
        """Verificar condiciones de alerta"""
        for alert_name, rule in self.alert_rules.items():
            try:
                condition_met = await self._evaluate_alert_condition(rule)
                if condition_met:
                    await self._trigger_alert(alert_name, rule)
            except Exception as e:
                self.logger.error(f"Error checking alert {alert_name}: {e}")
    
    async def _evaluate_alert_condition(self, rule: Dict[str, Any]) -> bool:
        """Evaluar condición de alerta"""
        # Placeholder - en implementación real, esto evaluaría la condición usando PromQL o similar
        metric = rule["metric"]
        condition = rule["condition"]
        
        # Simular evaluación de condición
        if "error_rate" in metric:
            return self.real_time_metrics.get("error_count_last_hour", 0) > 5
        elif "execution_time" in metric:
            return self.real_time_metrics.get("average_response_time", 0) > 2.0
        elif "database" in metric:
            return self.real_time_metrics.get("database_avg_duration", 0) > 1.0
        
        return False
    
    async def _trigger_alert(self, alert_name: str, rule: Dict[str, Any]):
        """Activar alerta"""
        alert_data = {
            "alert_name": alert_name,
            "severity": rule["severity"],
            "message": rule["message"],
            "timestamp": datetime.now().isoformat(),
            "metric": rule["metric"],
            "condition": rule["condition"]
        }
        
        self.logger.warning(f"ALERT TRIGGERED: {alert_data}")
        
        # En implementación real, aquí enviaríamos notificación (Slack, email, etc.)
    
    def get_dashboard_config(self) -> Dict[str, Any]:
        """Obtener configuración para dashboard específico"""
        config = {
            "dashboard_type": self.config.dashboard_type.value,
            "update_interval": self.config.update_interval,
            "key_metrics": list(self.config.key_metrics),
            "alerts": self.config.alerts,
            "custom_panels": self.config.custom_panels
        }
        
        if self.config.dashboard_type == DashboardType.GRAFANA:
            config.update(self._get_grafana_config())
        elif self.config.dashboard_type == DashboardType.PROMETHEUS:
            config.update(self._get_prometheus_config())
        elif self.config.dashboard_type == DashboardType.JAEGER_UI:
            config.update(self._get_jaeger_config())
        elif self.config.dashboard_type == DashboardType.ZIPKIN:
            config.update(self._get_zipkin_config())
        
        return config
    
    def _get_grafana_config(self) -> Dict[str, Any]:
        """Configuración específica para Grafana"""
        return {
            "host": self.config.host,
            "port": self.config.port,
            "data_sources": {
                "prometheus": f"http://{self.config.host}:{self.config.prometheus_port}",
                "jaeger": f"http://{self.config.host}:{self.config.jaeger_port}"
            },
            "dashboards": [
                {
                    "name": "MCP Core Performance",
                    "panels": [
                        {
                            "title": "Request Rate",
                            "query": "rate(mcp_trace_span_count[5m])",
                            "type": "graph",
                            "span": 6
                        },
                        {
                            "title": "Error Rate", 
                            "query": "rate(mcp_trace_errors_count[5m]) / rate(mcp_trace_span_count[5m]) * 100",
                            "type": "graph",
                            "span": 6
                        },
                        {
                            "title": "Response Time",
                            "query": "histogram_quantile(0.95, rate(mcp_trace_span_duration_bucket[5m]))",
                            "type": "graph", 
                            "span": 12
                        }
                    ]
                }
            ]
        }
    
    def _get_prometheus_config(self) -> Dict[str, Any]:
        """Configuración específica para Prometheus"""
        return {
            "host": self.config.host,
            "port": self.config.prometheus_port,
            "scrape_configs": [
                {
                    "job_name": "mcp-core-superior",
                    "static_configs": [{"targets": ["localhost:9090"]}],
                    "scrape_interval": "15s",
                    "metrics_path": "/metrics"
                }
            ],
            "alerting": {
                "alertmanagers": [
                    {
                        "static_configs": [{"targets": ["localhost:9093"]}]
                    }
                ],
                "rules": self._generate_prometheus_rules()
            }
        }
    
    def _get_jaeger_config(self) -> Dict[str, Any]:
        """Configuración específica para Jaeger"""
        return {
            "host": self.config.host,
            "port": self.config.jaeger_port,
            "storage": "elasticsearch",
            "es_server_urls": [f"http://{self.config.host}:9200"],
            "retention": self.config.traces_retention
        }
    
    def _get_zipkin_config(self) -> Dict[str, Any]:
        """Configuración específica para Zipkin"""
        return {
            "host": self.config.host,
            "port": self.config.zipkin_port,
            "storage": "elasticsearch", 
            "es_hosts": [f"{self.config.host}:9200"],
            "retention": self.config.traces_retention
        }
    
    def _generate_prometheus_rules(self) -> List[Dict[str, Any]]:
        """Generar reglas de Prometheus para alertas"""
        return [
            {
                "alert": "HighErrorRate",
                "expr": "rate(mcp_trace_errors_count[5m]) / rate(mcp_trace_span_count[5m]) > 0.1",
                "for": "2m",
                "labels": {
                    "severity": "warning"
                },
                "annotations": {
                    "summary": "High error rate detected",
                    "description": "Error rate is {{ $value }} which is above threshold"
                }
            },
            {
                "alert": "SlowResponseTime",
                "expr": "histogram_quantile(0.95, rate(mcp_trace_span_duration_bucket[5m])) > 5",
                "for": "3m",
                "labels": {
                    "severity": "warning"
                },
                "annotations": {
                    "summary": "Slow response time detected", 
                    "description": "95th percentile response time is {{ $value }}s"
                }
            }
        ]
    
    def export_dashboard_config(self, file_path: str):
        """Exportar configuración de dashboard a archivo"""
        config = self.get_dashboard_config()
        
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        self.logger.info(f"Dashboard config exported to {file_path}")
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Obtener estado de salud del sistema"""
        trace_summary = self.otel_system.get_trace_summary()
        
        # Evaluar estado de salud basado en métricas
        health_score = 100
        issues = []
        
        # Verificar tasa de errores
        error_rate = await self._get_error_count_last_hour()
        if error_rate > 10:
            health_score -= 20
            issues.append("High error rate detected")
        
        # Verificar tiempo de respuesta
        avg_response = await self._get_average_response_time()
        if avg_response > 3.0:
            health_score -= 15
            issues.append("Slow response times detected")
        
        # Verificar tasa de éxito de agentes
        success_rate = await self._get_agents_success_rate()
        if success_rate < 0.9:
            health_score -= 25
            issues.append("Low agent success rate")
        
        health_status = "healthy"
        if health_score < 70:
            health_status = "warning"
        elif health_score < 40:
            health_status = "critical"
        
        return {
            "status": health_status,
            "score": max(health_score, 0),
            "issues": issues,
            "metrics": self.real_time_metrics,
            "timestamp": datetime.now().isoformat()
        }


# Funciones de conveniencia para uso en FastMCP Server
async def setup_observability_dashboard(config: DashboardConfig = None) -> ObservabilityDashboard:
    """Configurar dashboard de observabilidad"""
    dashboard = ObservabilityDashboard(config)
    
    # Iniciar monitoreo en background
    asyncio.create_task(dashboard.start_real_time_monitoring())
    
    return dashboard


def get_grafana_dashboard_config() -> Dict[str, Any]:
    """Obtener configuración lista para Grafana"""
    dashboard = ObservabilityDashboard()
    return dashboard._get_grafana_config()


def get_prometheus_config() -> Dict[str, Any]:
    """Obtener configuración lista para Prometheus"""
    dashboard = ObservabilityDashboard()
    return dashboard._get_prometheus_config()


# Ejemplo de uso
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Configurar dashboard
        config = DashboardConfig(
            dashboard_type=DashboardType.GRAFANA,
            host="localhost",
            port=3000
        )
        
        dashboard = await setup_observability_dashboard(config)
        
        # Exportar configuración
        dashboard.export_dashboard_config("observability_dashboard_config.json")
        
        # Obtener estado de salud
        health = await dashboard.get_system_health()
        print(f"System Health: {health}")
    
    asyncio.run(main())