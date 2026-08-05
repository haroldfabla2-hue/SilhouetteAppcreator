#!/usr/bin/env python3
"""
Demostración Completa del Sistema de Métricas Avanzadas
MCP Core Superior - Observabilidad Avanzada

Este script demuestra todas las funcionalidades del sistema:
1. Latency metrics por agente y operación
2. Throughput metrics (RPS, concurrent users)
3. Error rates y success ratios
4. Resource utilization (CPU, memoria, disco)
5. Agent health scores y availability
6. Business metrics (tasks completed, SLA compliance)
7. Custom dashboards y alerts
8. Time-series data storage
9. Percentile calculations (P50, P95, P99)
10. Capacity planning metrics

Compatible con Prometheus y Grafana
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp.advanced.metrics.demo")

# Imports del sistema de métricas
try:
    from src.observability.advanced_metrics import (
        AdvancedMetricsCollector,
        get_advanced_metrics_collector,
        initialize_advanced_metrics,
        GrafanaDashboardConfig,
        CustomAlert,
        AlertSeverity,
        LatencyMetric,
        TimeSeriesStorage
    )
    from src.observability.metrics_config import (
        create_default_configs,
        get_metrics_config_manager,
        MetricsConfigurationManager,
        AlertConfig
    )
except ImportError:
    # Fallback para ejecución directa
    import sys
    sys.path.append(str(Path(__file__).parent))
    from advanced_metrics import (
        AdvancedMetricsCollector,
        get_advanced_metrics_collector,
        initialize_advanced_metrics,
        GrafanaDashboardConfig,
        CustomAlert,
        AlertSeverity,
        LatencyMetric,
        TimeSeriesStorage
    )
    from metrics_config import (
        create_default_configs,
        get_metrics_config_manager,
        MetricsConfigurationManager,
        AlertConfig
    )


class MetricsDemo:
    """Clase principal de demostración del sistema de métricas"""
    
    def __init__(self):
        self.collector: AdvancedMetricsCollector = None
        self.config_manager: MetricsConfigurationManager = None
        self.demo_duration_seconds = 60  # Duración de la demo
        self.collection_interval = 2  # Intervalo de recolección
        
    async def setup(self):
        """Configurar el sistema de métricas"""
        logger.info("🚀 Configurando sistema de métricas avanzadas...")
        
        # 1. Crear configuración por defecto
        self.config_manager = create_default_configs("demo_config")
        logger.info("✅ Configuración creada")
        
        # 2. Inicializar recolector de métricas
        self.collector = get_advanced_metrics_collector(
            collection_interval=self.collection_interval
        )
        await self.collector.start_collection()
        logger.info("✅ Recolector de métricas iniciado")
        
        # 3. Configurar callbacks de ejemplo
        self._setup_callbacks()
        
        # 4. Agregar alertas personalizadas
        self._setup_custom_alerts()
        
        logger.info("🎯 Sistema configurado correctamente")
    
    def _setup_callbacks(self):
        """Configurar callbacks para alertas y dashboards"""
        
        async def alert_callback(event_type: str, alert: CustomAlert):
            """Callback para manejo de alertas"""
            if event_type == "triggered":
                logger.warning(f"🚨 ALERTA ACTIVADA: {alert.title} - {alert.message}")
            elif event_type == "resolved":
                logger.info(f"✅ ALERTA RESUELTA: {alert.title} - {alert.message}")
        
        async def dashboard_callback(dashboard_data: dict):
            """Callback para actualización de dashboards"""
            logger.info(f"📊 Dashboard actualizado - Alertas activas: {dashboard_data.get('active_alerts', 0)}")
        
        self.collector.register_alert_callback(alert_callback)
        self.collector.register_dashboard_callback(dashboard_callback)
    
    def _setup_custom_alerts(self):
        """Configurar alertas personalizadas"""
        
        # Alerta personalizada para latencia alta
        latency_alert = CustomAlert(
            id="high_latency",
            timestamp=datetime.now(),
            severity=AlertSeverity.WARNING,
            title="High Request Latency",
            message="Request latency exceeds 500ms",
            metric_name="mcp_latency_milliseconds",
            current_value=0.0,
            threshold_value=500.0,
            operator=">"
        )
        self.collector.add_custom_alert(latency_alert)
        
        # Alerta personalizada para throughput bajo
        throughput_alert = CustomAlert(
            id="low_throughput",
            timestamp=datetime.now(),
            severity=AlertSeverity.WARNING,
            title="Low System Throughput",
            message="Throughput below 5 RPS",
            metric_name="mcp_throughput_operations_per_second",
            current_value=0.0,
            threshold_value=5.0,
            operator="<"
        )
        self.collector.add_custom_alert(throughput_alert)
        
        logger.info("🚨 Alertas personalizadas configuradas")
    
    async def simulate_metrics(self):
        """Simular métricas realistas del sistema"""
        logger.info("📈 Simulando métricas del sistema...")
        
        # Simular latencia de diferentes agentes
        agents = ["reasoner", "planner", "executor", "verifier", "memory_manager", "orchestrator"]
        operations = ["process_task", "analyze", "execute", "validate", "store", "route"]
        
        for i in range(30):  # 30 iteraciones
            # Latencia por agente y operación
            for agent in agents:
                # Simular variabilidad en latencia
                import random
                
                base_latency = {
                    "reasoner": 150,
                    "planner": 100,
                    "executor": 200,
                    "verifier": 80,
                    "memory_manager": 50,
                    "orchestrator": 120
                }.get(agent, 100)
                
                # Agregar variabilidad
                latency_variation = random.uniform(0.5, 2.0)
                current_latency = base_latency * latency_variation
                
                # Simular algunos errores ocasionales
                status = "success" if random.random() > 0.05 else "error"
                if status == "error":
                    current_latency *= random.uniform(1.5, 3.0)  # Errores son más lentos
                
                operation = random.choice(operations)
                self.collector.record_latency(
                    agent_name=agent,
                    operation=operation,
                    latency_ms=current_latency,
                    status=status,
                    method="POST" if random.random() > 0.5 else "GET"
                )
            
            # Simular throughput variable
            base_rps = 20
            current_rps = base_rps * random.uniform(0.7, 1.5)
            concurrent_users = int(current_rps * random.uniform(0.3, 0.8))
            
            self.collector.record_throughput(
                requests_per_second=current_rps,
                concurrent_users=concurrent_users,
                active_connections=int(concurrent_users * 0.6),
                queue_depth=int(random.randint(0, 15)),
                throughput_type="requests"
            )
            
            # Esperar antes de la siguiente iteración
            await asyncio.sleep(1)
        
        logger.info("✅ Simulación de métricas completada")
    
    async def demonstrate_features(self):
        """Demostrar todas las funcionalidades"""
        logger.info("🎯 Demostrando funcionalidades del sistema...")
        
        # 1. Métricas de Latencia por agente y operación
        await self._demo_latency_metrics()
        
        # 2. Métricas de Throughput
        await self._demo_throughput_metrics()
        
        # 3. Tasas de error y ratios de éxito
        await self._demo_error_rates()
        
        # 4. Utilización de recursos
        await self._demo_resource_utilization()
        
        # 5. Health scores de agentes
        await self._demo_agent_health_scores()
        
        # 6. Métricas de negocio
        await self._demo_business_metrics()
        
        # 7. Cálculos de percentiles
        await self._demo_percentile_calculations()
        
        # 8. Planificación de capacidad
        await self._demo_capacity_planning()
        
        # 9. Sistema de alertas
        await self._demo_alert_system()
        
        # 10. Exportación a Prometheus
        await self._demo_prometheus_export()
    
    async def _demo_latency_metrics(self):
        """Demostrar métricas de latencia"""
        print("\n" + "="*60)
        print("📊 1. MÉTRICAS DE LATENCIA POR AGENTE Y OPERACIÓN")
        print("="*60)
        
        percentiles = self.collector.get_percentile_metrics(
            time_range=timedelta(minutes=5)
        )
        
        print("Percentiles de latencia (últimos 5 minutos):")
        for p, value in percentiles.items():
            print(f"  {p}: {value:.2f}ms")
        
        # Mostrar latencia por agente específico
        reasoner_percentiles = self.collector.get_percentile_metrics(
            agent_name="reasoner",
            time_range=timedelta(minutes=5)
        )
        print(f"\nLatencia específica del agente 'reasoner':")
        for p, value in reasoner_percentiles.items():
            print(f"  {p}: {value:.2f}ms")
    
    async def _demo_throughput_metrics(self):
        """Demostrar métricas de throughput"""
        print("\n" + "="*60)
        print("🚀 2. MÉTRICAS DE THROUGHPUT")
        print("="*60)
        
        current_metrics = self.collector.get_current_metrics()
        throughput_data = current_metrics.get("throughput")
        
        if throughput_data:
            print(f"Requests por segundo: {throughput_data.get('requests_per_second', 0):.2f}")
            print(f"Usuarios concurrentes: {throughput_data.get('concurrent_users', 0)}")
            print(f"Conexiones activas: {throughput_data.get('active_connections', 0)}")
            print(f"Profundidad de cola: {throughput_data.get('queue_depth', 0)}")
            print(f"Tasa de procesamiento: {throughput_data.get('processing_rate', 0):.2f}")
        else:
            print("No hay datos de throughput disponibles")
    
    async def _demo_error_rates(self):
        """Demostrar tasas de error y ratios de éxito"""
        print("\n" + "="*60)
        print("⚠️  3. TASAS DE ERROR Y RATIOS DE ÉXITO")
        print("="*60)
        
        error_data = self.collector.get_current_metrics().get("error_rates", {})
        
        for agent, data in error_data.items():
            if data:
                print(f"\nAgente: {agent}")
                print(f"  Total requests: {data.get('total_requests', 0)}")
                print(f"  Successful: {data.get('successful_requests', 0)}")
                print(f"  Failed: {data.get('failed_requests', 0)}")
                print(f"  Timeouts: {data.get('timeout_requests', 0)}")
                print(f"  Success rate: {data.get('success_rate', 0)*100:.2f}%")
                print(f"  Error rate: {data.get('error_rate', 0)*100:.2f}%")
                print(f"  MTTF: {data.get('mttf_minutes', 0):.2f} minutes")
    
    async def _demo_resource_utilization(self):
        """Demostrar utilización de recursos"""
        print("\n" + "="*60)
        print("💻 4. UTILIZACIÓN DE RECURSOS DEL SISTEMA")
        print("="*60)
        
        resource_data = self.collector.get_current_metrics().get("system_resources")
        
        if resource_data:
            print(f"CPU: {resource_data.get('cpu_percent', 0):.2f}%")
            print(f"Memory: {resource_data.get('memory_percent', 0):.2f}%")
            print(f"Memory used: {resource_data.get('memory_used_gb', 0):.2f} GB")
            print(f"Memory available: {resource_data.get('memory_available_gb', 0):.2f} GB")
            print(f"Disk: {resource_data.get('disk_percent', 0):.2f}%")
            print(f"Thread count: {resource_data.get('thread_count', 0)}")
            print(f"File descriptors: {resource_data.get('file_descriptor_count', 0)}")
            print(f"Load average: {resource_data.get('load_average', [])}")
        else:
            print("No hay datos de recursos disponibles")
    
    async def _demo_agent_health_scores(self):
        """Demostrar health scores de agentes"""
        print("\n" + "="*60)
        print("🏥 5. HEALTH SCORES DE AGENTES")
        print("="*60)
        
        health_data = self.collector.get_current_metrics().get("health_scores", {})
        
        for agent, data in health_data.items():
            if data:
                print(f"\nAgente: {agent}")
                print(f"  Health Score: {data.get('health_score', 0):.2f}/100")
                print(f"  Status: {data.get('status_level', 'unknown')}")
                print(f"  Availability: {data.get('availability_percent', 0):.2f}%")
                print(f"  Performance Score: {data.get('performance_score', 0):.2f}")
                print(f"  Reliability Score: {data.get('reliability_score', 0):.2f}")
                print(f"  Total Executions: {data.get('total_executions', 0)}")
                print(f"  Success Rate: {data.get('successful_executions', 0) / max(data.get('total_executions', 1), 1) * 100:.2f}%")
                print(f"  Avg Response Time: {data.get('avg_response_time_ms', 0):.2f}ms")
    
    async def _demo_business_metrics(self):
        """Demostrar métricas de negocio"""
        print("\n" + "="*60)
        print("💼 6. MÉTRICAS DE NEGOCIO")
        print("="*60)
        
        business_data = self.collector.get_current_metrics().get("business")
        
        if business_data:
            print(f"Tareas completadas: {business_data.get('tasks_completed', 0)}")
            print(f"SLA Compliance: {business_data.get('sla_compliance_percent', 0):.2f}%")
            print(f"Customer Satisfaction: {business_data.get('customer_satisfaction_score', 0):.2f}/5.0")
            print(f"Cost per Operation: ${business_data.get('cost_per_operation', 0):.4f}")
            print(f"Revenue Generated: ${business_data.get('revenue_generated', 0):.2f}")
            print(f"Operational Cost: ${business_data.get('operational_cost', 0):.2f}")
            print(f"Profit Margin: {business_data.get('profit_margin', 0)*100:.2f}%")
            print(f"KPI: {business_data.get('business_kpi', 'N/A')}")
            print(f"KPI Value: {business_data.get('kpi_value', 0):.2f}")
            print(f"KPI Target: {business_data.get('kpi_target', 0):.2f}")
            print(f"SLA Compliant: {'✅' if business_data.get('sla_compliant') else '❌'}")
        else:
            print("No hay métricas de negocio disponibles")
    
    async def _demo_percentile_calculations(self):
        """Demostrar cálculos de percentiles"""
        print("\n" + "="*60)
        print("📈 7. CÁLCULOS DE PERCENTILES (P50, P95, P99)")
        print("="*60)
        
        # Obtener percentiles para diferentes agentes
        agents = ["reasoner", "executor", "orchestrator"]
        
        for agent in agents:
            percentiles = self.collector.get_percentile_metrics(
                agent_name=agent,
                time_range=timedelta(minutes=5)
            )
            
            print(f"\nAgent: {agent}")
            for p, value in percentiles.items():
                print(f"  {p}: {value:.2f}ms")
        
        # Percentiles generales
        general_percentiles = self.collector.get_percentile_metrics(
            time_range=timedelta(minutes=5)
        )
        
        print(f"\nGeneral System Percentiles:")
        for p, value in general_percentiles.items():
            print(f"  {p}: {value:.2f}ms")
    
    async def _demo_capacity_planning(self):
        """Demostrar planificación de capacidad"""
        print("\n" + "="*60)
        print("🔮 8. PLANIFICACIÓN DE CAPACIDAD")
        print("="*60)
        
        capacity_report = self.collector.generate_capacity_report(days_ahead=30)
        
        if capacity_report:
            print("Reporte de Capacidad (30 días):")
            print(f"  Uso actual de CPU: {capacity_report.get('current_usage', {}).get('cpu_percent', 0):.2f}%")
            print(f"  Uso actual de Memory: {capacity_report.get('current_usage', {}).get('memory_percent', 0):.2f}%")
            print(f"  Necesidad proyectada: {capacity_report.get('current_usage', {}).get('projected_need', 0):.2f}%")
            
            print(f"\nRecomendaciones:")
            for rec in capacity_report.get('recommendations', []):
                print(f"  • {rec}")
            
            print(f"\nCuellos de botella:")
            for bottleneck in capacity_report.get('bottlenecks', []):
                print(f"  • {bottleneck}")
            
            print(f"\nOportunidades de optimización:")
            for opportunity in capacity_report.get('optimization_opportunities', []):
                print(f"  • {opportunity}")
            
            print(f"\nAnálisis de costos:")
            cost_analysis = capacity_report.get('cost_analysis', {})
            print(f"  Costo actual/hora: ${cost_analysis.get('current_cost_per_hour', 0):.2f}")
            print(f"  Costo proyectado/hora: ${cost_analysis.get('projected_cost_per_hour', 0):.2f}")
            print(f"  Potencial de optimización: ${cost_analysis.get('cost_optimization_potential', 0):.2f}")
        else:
            print("No hay datos de capacidad disponibles")
    
    async def _demo_alert_system(self):
        """Demostrar sistema de alertas"""
        print("\n" + "="*60)
        print("🚨 9. SISTEMA DE ALERTAS PERSONALIZADAS")
        print("="*60)
        
        current_metrics = self.collector.get_current_metrics()
        active_alerts = current_metrics.get("alerts_detail", [])
        
        print(f"Alertas activas: {len(active_alerts)}")
        for alert in active_alerts:
            print(f"  • ID: {alert.get('id', 'N/A')}")
            print(f"    Timestamp: {alert.get('timestamp', 'N/A')}")
        
        print(f"\nAlertas configuradas:")
        for alert_id, alert in self.collector.custom_alerts.items():
            status = "ACTIVE" if alert_id in self.collector.active_alerts else "INACTIVE"
            print(f"  • {alert.title} ({status})")
            print(f"    Threshold: {alert.threshold_value} {alert.operator}")
            print(f"    Severity: {alert.severity}")
        
        print(f"\nConfiguración de alertas:")
        config = self.config_manager.get_metrics_config()
        print(f"  Alerts enabled: {config.alert_enabled}")
        print(f"  Check interval: {config.alert_check_interval_seconds}s")
        print(f"  Escalation enabled: {config.alert_escalation_enabled}")
    
    async def _demo_prometheus_export(self):
        """Demostrar exportación a Prometheus"""
        print("\n" + "="*60)
        print("📊 10. EXPORTACIÓN A PROMETHEUS")
        print("="*60)
        
        prometheus_metrics = self.collector.export_prometheus_metrics()
        
        print("Métricas en formato Prometheus:")
        print("```")
        print(prometheus_metrics)
        print("```")
        
        # Mostrar configuración de Grafana
        dashboard_config = GrafanaDashboardConfig.generate_dashboard_json()
        
        print(f"\nConfiguración de Dashboard de Grafana:")
        print(f"  Título: {dashboard_config['dashboard']['title']}")
        print(f"  Paneles: {len(dashboard_config['dashboard']['panels'])}")
        print(f"  Time range: {dashboard_config['dashboard']['time']}")
        
        # Configuración de Prometheus
        prometheus_config = self.config_manager.generate_prometheus_config()
        print(f"\nConfiguración de Prometheus:")
        print("```yaml")
        print(prometheus_config)
        print("```")
    
    async def demonstrate_time_series_storage(self):
        """Demostrar almacenamiento de series temporales"""
        print("\n" + "="*60)
        print("🗄️  ALMACENAMIENTO DE SERIES TEMPORALES")
        print("="*60)
        
        # Mostrar datos almacenados en la base de datos
        storage = self.collector.storage
        
        # Consultar datos de CPU de las últimas 2 horas
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=2)
        
        cpu_data = storage.query_metrics(
            "mcp_cpu_usage_percent",
            start_time,
            end_time,
            aggregation="avg",
            bucket_size_seconds=300  # 5 minutos
        )
        
        print(f"Datos de CPU (últimas 2 horas, buckets de 5 min):")
        for timestamp, value in cpu_data[-10:]:  # Últimos 10 buckets
            dt = datetime.fromtimestamp(timestamp)
            print(f"  {dt.strftime('%H:%M:%S')}: {value:.2f}%")
        
        # Limpiar datos antiguos
        print(f"\nLimpiando datos anteriores a 1 día...")
        storage.cleanup_old_metrics(retention_days=1)
        print("✅ Limpieza completada")
    
    async def show_integration_examples(self):
        """Mostrar ejemplos de integración"""
        print("\n" + "="*60)
        print("🔗 EJEMPLOS DE INTEGRACIÓN")
        print("="*60)
        
        print("1. Integración con FastAPI:")
        print("```python")
        print("""
from fastapi import FastAPI
from src.observability import initialize_advanced_metrics

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await initialize_advanced_metrics(collection_interval=5)

@app.get("/api/performance")
async def get_performance():
    collector = get_advanced_metrics_collector()
    return collector.get_current_metrics()
        """)
        print("```")
        
        print("\n2. Integración con Agentes MCP:")
        print("```python")
        print("""
from src.observability import get_advanced_metrics_collector

class MCPAgent:
    def __init__(self):
        self.metrics = get_advanced_metrics_collector()
    
    async def execute_task(self, task):
        start_time = time.time()
        
        try:
            result = await self._process_task(task)
            
            # Registrar métricas de éxito
            self.metrics.record_latency(
                agent_name="my_agent",
                operation="execute_task",
                latency_ms=(time.time() - start_time) * 1000,
                status="success"
            )
            
            return result
            
        except Exception as e:
            # Registrar métricas de error
            self.metrics.record_latency(
                agent_name="my_agent", 
                operation="execute_task",
                latency_ms=(time.time() - start_time) * 1000,
                status="error"
            )
            raise
        """)
        print("```")
        
        print("\n3. Alertas personalizadas:")
        print("```python")
        print("""
from src.observability import CustomAlert, AlertSeverity

# Crear alerta personalizada
custom_alert = CustomAlert(
    id="custom_threshold",
    timestamp=datetime.now(),
    severity=AlertSeverity.CRITICAL,
    title="Custom Business Alert",
    message="Business KPI below threshold",
    metric_name="custom_kpi_metric",
    current_value=0.0,
    threshold_value=100.0,
    operator="<"
)

collector.add_custom_alert(custom_alert)
        """)
        print("```")
    
    async def run_complete_demo(self):
        """Ejecutar demostración completa"""
        print("🚀 INICIANDO DEMOSTRACIÓN COMPLETA DEL SISTEMA DE MÉTRICAS AVANZADAS")
        print("="*80)
        print(f"Duración: {self.demo_duration_seconds} segundos")
        print(f"Intervalo de recolección: {self.collection_interval} segundos")
        print("="*80)
        
        try:
            # Configurar sistema
            await self.setup()
            
            # Simular métricas mientras demostramos funcionalidades
            simulation_task = asyncio.create_task(self.simulate_metrics())
            
            # Ejecutar demostraciones
            await asyncio.sleep(10)  # Esperar un poco de datos
            
            await self.demonstrate_features()
            
            # Demostrar almacenamiento de series temporales
            await self.demonstrate_time_series_storage()
            
            # Mostrar ejemplos de integración
            await self.show_integration_examples()
            
            # Esperar a que termine la simulación
            await simulation_task
            
            print("\n" + "="*80)
            print("✅ DEMOSTRACIÓN COMPLETADA EXITOSAMENTE")
            print("="*80)
            print("\nEl sistema de métricas avanzadas incluye:")
            print("• ✅ Latency metrics por agente y operación")
            print("• ✅ Throughput metrics (RPS, concurrent users)")
            print("• ✅ Error rates y success ratios")
            print("• ✅ Resource utilization (CPU, memoria, disco)")
            print("• ✅ Agent health scores y availability")
            print("• ✅ Business metrics (tasks completed, SLA compliance)")
            print("• ✅ Custom dashboards y alerts")
            print("• ✅ Time-series data storage")
            print("• ✅ Percentile calculations (P50, P95, P99)")
            print("• ✅ Capacity planning metrics")
            print("• ✅ Integración con Prometheus y Grafana")
            print("\nArchivos generados:")
            print(f"• {self.config_manager.config_dir / 'metrics_config.json'}")
            print(f"• {self.config_manager.config_dir / 'alerts_config.json'}")
            print(f"• {self.config_manager.config_dir / 'dashboards_config.json'}")
            print(f"• metrics_timeseries.db (base de datos de métricas)")
            
        except Exception as e:
            logger.error(f"Error en la demostración: {e}")
            raise
        finally:
            # Limpiar recursos
            if self.collector:
                await self.collector.stop_collection()
            print("\n🧹 Recursos limpiados")


async def main():
    """Función principal"""
    demo = MetricsDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    asyncio.run(main())