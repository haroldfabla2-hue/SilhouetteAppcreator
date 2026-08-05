"""
Sistema de Métricas de Salud para Auto-Healing
Implementa métricas específicas para monitoreo y análisis predictivo
"""
import asyncio
import time
import psutil
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import threading
from concurrent.futures import ThreadPoolExecutor

from .auto_healing_engine import HealthMetrics, HealthStatus, ErrorEvent
from .config import settings


@dataclass
class SystemResourceMetrics:
    """Métricas de recursos del sistema"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_usage_percent: float
    network_io: Dict[str, int]
    process_count: int
    load_average: List[float]  # 1, 5, 15 minutes
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "memory_available_gb": self.memory_available_gb,
            "disk_usage_percent": self.disk_usage_percent,
            "network_io": self.network_io,
            "process_count": self.process_count,
            "load_average": self.load_average
        }


@dataclass
class ApplicationMetrics:
    """Métricas específicas de la aplicación"""
    timestamp: datetime
    active_connections: int
    request_rate: float
    response_time_p50: float
    response_time_p95: float
    response_time_p99: float
    error_rate: float
    throughput: float
    queue_depth: int
    cache_hit_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "active_connections": self.active_connections,
            "request_rate": self.request_rate,
            "response_time_p50": self.response_time_p50,
            "response_time_p95": self.response_time_p95,
            "response_time_p99": self.response_time_p99,
            "error_rate": self.error_rate,
            "throughput": self.throughput,
            "queue_depth": self.queue_depth,
            "cache_hit_rate": self.cache_hit_rate
        }


@dataclass
class AgentPerformanceMetrics:
    """Métricas de rendimiento por agente"""
    timestamp: datetime
    agent_name: str
    execution_count: int
    success_count: int
    error_count: int
    avg_execution_time: float
    p95_execution_time: float
    concurrent_executions: int
    queue_size: int
    memory_usage_mb: float
    cpu_usage_percent: float
    last_successful_execution: Optional[datetime] = None
    last_error_execution: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        if self.execution_count == 0:
            return 1.0
        return self.success_count / self.execution_count
    
    @property
    def error_rate(self) -> float:
        if self.execution_count == 0:
            return 0.0
        return self.error_count / self.execution_count
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "agent_name": self.agent_name,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": self.success_rate,
            "error_rate": self.error_rate,
            "avg_execution_time": self.avg_execution_time,
            "p95_execution_time": self.p95_execution_time,
            "concurrent_executions": self.concurrent_executions,
            "queue_size": self.queue_size,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "last_successful_execution": self.last_successful_execution.isoformat() if self.last_successful_execution else None,
            "last_error_execution": self.last_error_execution.isoformat() if self.last_error_execution else None
        }


class HealthMetricsCollector:
    """Recolector de métricas de salud del sistema"""
    
    def __init__(self, collection_interval: int = 10):
        self.collection_interval = collection_interval
        self.logger = logging.getLogger("mcp.metrics.collector")
        
        # Métricas almacenadas
        self.system_metrics_history: deque = deque(maxlen=1000)
        self.application_metrics_history: deque = deque(maxlen=1000)
        self.agent_metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=500))
        
        # Agregadores
        self.response_time_samples: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.execution_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Estado de monitoreo
        self.is_collecting = False
        self._collection_task: Optional[asyncio.Task] = None
        self._lock = threading.Lock()
        
        # Callbacks para integraciones externas
        self.metric_callbacks: List[Callable] = []
        
        # Estadísticas de recolección
        self.collection_stats = {
            "total_collections": 0,
            "collection_errors": 0,
            "last_collection_time": None,
            "average_collection_duration": 0.0
        }
    
    async def start_collection(self):
        """Iniciar recolección de métricas"""
        if self.is_collecting:
            return
        
        self.is_collecting = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        self.logger.info("Health metrics collection started")
    
    async def stop_collection(self):
        """Detener recolección de métricas"""
        self.is_collecting = False
        
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Health metrics collection stopped")
    
    async def _collection_loop(self):
        """Loop principal de recolección"""
        while self.is_collecting:
            start_time = time.time()
            
            try:
                # Recopilar todas las métricas
                await self._collect_all_metrics()
                
                # Notificar callbacks
                for callback in self.metric_callbacks:
                    try:
                        await callback()
                    except Exception as e:
                        self.logger.error(f"Error in metric callback: {e}")
                
                # Actualizar estadísticas
                self.collection_stats["total_collections"] += 1
                self.collection_stats["last_collection_time"] = datetime.now()
                
                collection_duration = time.time() - start_time
                self._update_avg_collection_duration(collection_duration)
                
            except Exception as e:
                self.collection_stats["collection_errors"] += 1
                self.logger.error(f"Error collecting metrics: {e}")
            
            # Esperar al próximo intervalo
            await asyncio.sleep(self.collection_interval)
    
    def _update_avg_collection_duration(self, duration: float):
        """Actualizar duración promedio de recolección"""
        total = self.collection_stats["total_collections"]
        current_avg = self.collection_stats["average_collection_duration"]
        
        # Calcular nuevo promedio
        new_avg = ((current_avg * (total - 1)) + duration) / total
        self.collection_stats["average_collection_duration"] = new_avg
    
    async def _collect_all_metrics(self):
        """Recopilar todas las métricas del sistema"""
        # Métricas del sistema
        system_metrics = await self._collect_system_metrics()
        self.system_metrics_history.append(system_metrics)
        
        # Métricas de la aplicación
        app_metrics = await self._collect_application_metrics()
        self.application_metrics_history.append(app_metrics)
        
        # Métricas de agentes (si están disponibles)
        agent_metrics = await self._collect_agent_metrics()
        for metrics in agent_metrics:
            self.agent_metrics_history[metrics.agent_name].append(metrics)
    
    async def _collect_system_metrics(self) -> SystemResourceMetrics:
        """Recopilar métricas del sistema"""
        # Usar thread pool para operaciones bloqueantes de psutil
        loop = asyncio.get_event_loop()
        
        def collect_psutil_data():
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory": psutil.virtual_memory(),
                "disk": psutil.disk_usage('/'),
                "network": psutil.net_io_counters(),
                "process_count": len(psutil.pids()),
                "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0.0, 0.0, 0.0]
            }
        
        data = await loop.run_in_executor(None, collect_psutil_data)
        
        return SystemResourceMetrics(
            timestamp=datetime.now(),
            cpu_percent=data["cpu_percent"],
            memory_percent=data["memory"].percent,
            memory_available_gb=data["memory"].available / (1024**3),
            disk_usage_percent=data["disk"].percent / 100 * 100,
            network_io={
                "bytes_sent": data["network"].bytes_sent,
                "bytes_recv": data["network"].bytes_recv,
                "packets_sent": data["network"].packets_sent,
                "packets_recv": data["network"].packets_recv
            },
            process_count=data["process_count"],
            load_average=list(data["load_avg"])
        )
    
    async def _collect_application_metrics(self) -> ApplicationMetrics:
        """Recopilar métricas de la aplicación"""
        # Estas métricas serían proporcionadas por la aplicación real
        # Por ahora, simularemos datos realistas
        
        # Simular conexiones activas (en implementación real, usar datos reales)
        active_connections = await self._get_active_connections()
        request_rate = await self._get_request_rate()
        response_times = await self._get_response_times()
        error_rate = await self._get_error_rate()
        throughput = await self._get_throughput()
        queue_depth = await self._get_queue_depth()
        cache_hit_rate = await self._get_cache_hit_rate()
        
        return ApplicationMetrics(
            timestamp=datetime.now(),
            active_connections=active_connections,
            request_rate=request_rate,
            response_time_p50=response_times["p50"],
            response_time_p95=response_times["p95"],
            response_time_p99=response_times["p99"],
            error_rate=error_rate,
            throughput=throughput,
            queue_depth=queue_depth,
            cache_hit_rate=cache_hit_rate
        )
    
    async def _collect_agent_metrics(self) -> List[AgentPerformanceMetrics]:
        """Recopilar métricas de rendimiento por agente"""
        agent_names = ["reasoner", "planner", "executor", "verifier", "memory_manager", "orchestrator", "streaming"]
        metrics = []
        
        for agent_name in agent_names:
            agent_metrics = await self._collect_single_agent_metrics(agent_name)
            if agent_metrics:
                metrics.append(agent_metrics)
        
        return metrics
    
    async def _collect_single_agent_metrics(self, agent_name: str) -> Optional[AgentPerformanceMetrics]:
        """Recopilar métricas para un agente específico"""
        # En implementación real, esto obtendría métricas del agente específico
        
        # Simular datos basados en el agente
        base_load = {
            "reasoner": 0.3,
            "planner": 0.4,
            "executor": 0.6,
            "verifier": 0.2,
            "memory_manager": 0.1,
            "orchestrator": 0.5,
            "streaming": 0.4
        }
        
        load_factor = base_load.get(agent_name, 0.3)
        
        # Simular métricas variables
        import random
        
        return AgentPerformanceMetrics(
            timestamp=datetime.now(),
            agent_name=agent_name,
            execution_count=int(random.randint(5, 20) * load_factor),
            success_count=int(random.randint(4, 18) * load_factor),
            error_count=int(random.randint(0, 3) * (1 - load_factor)),
            avg_execution_time=random.uniform(0.5, 2.0) * load_factor,
            p95_execution_time=random.uniform(1.0, 4.0) * load_factor,
            concurrent_executions=int(random.randint(0, 5) * load_factor),
            queue_size=int(random.randint(0, 10) * load_factor),
            memory_usage_mb=random.uniform(50, 200) * load_factor,
            cpu_usage_percent=random.uniform(10, 80) * load_factor,
            last_successful_execution=datetime.now() - timedelta(seconds=random.randint(1, 30)),
            last_error_execution=datetime.now() - timedelta(seconds=random.randint(10, 300)) if random.random() < 0.1 else None
        )
    
    # ==================== MÉTODOS DE RECOPILACIÓN SIMULADOS ====================
    
    async def _get_active_connections(self) -> int:
        """Obtener conexiones activas (simulado)"""
        import random
        return random.randint(5, 50)
    
    async def _get_request_rate(self) -> float:
        """Obtener tasa de requests (simulado)"""
        import random
        return random.uniform(0.5, 10.0)
    
    async def _get_response_times(self) -> Dict[str, float]:
        """Obtener tiempos de respuesta (simulado)"""
        import random
        return {
            "p50": random.uniform(0.1, 0.5),
            "p95": random.uniform(0.5, 2.0),
            "p99": random.uniform(1.0, 5.0)
        }
    
    async def _get_error_rate(self) -> float:
        """Obtener tasa de errores (simulado)"""
        import random
        return random.uniform(0, 0.05)
    
    async def _get_throughput(self) -> float:
        """Obtener throughput (simulado)"""
        import random
        return random.uniform(5, 50)
    
    async def _get_queue_depth(self) -> int:
        """Obtener profundidad de cola (simulado)"""
        import random
        return random.randint(0, 20)
    
    async def _get_cache_hit_rate(self) -> float:
        """Obtener tasa de aciertos de cache (simulado)"""
        import random
        return random.uniform(0.7, 0.95)
    
    # ==================== MÉTODOS PÚBLICOS ====================
    
    def record_response_time(self, endpoint: str, response_time: float):
        """Registrar tiempo de respuesta para un endpoint"""
        self.response_time_samples[endpoint].append(response_time)
    
    def record_execution_time(self, agent_name: str, execution_time: float):
        """Registrar tiempo de ejecución para un agente"""
        self.execution_times[agent_name].append(execution_time)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Obtener métricas actuales"""
        current_system = self.system_metrics_history[-1] if self.system_metrics_history else None
        current_app = self.application_metrics_history[-1] if self.application_metrics_history else None
        
        return {
            "system": current_system.to_dict() if current_system else None,
            "application": current_app.to_dict() if current_app else None,
            "agents": {
                name: metrics[-1].to_dict() if metrics else None
                for name, metrics in self.agent_metrics_history.items()
            },
            "collection_stats": self.collection_stats
        }
    
    def get_metrics_history(self, 
                          metric_type: str, 
                          agent_name: Optional[str] = None,
                          time_range: Optional[timedelta] = None) -> List[Dict[str, Any]]:
        """Obtener historial de métricas"""
        cutoff_time = datetime.now() - (time_range or timedelta(hours=1))
        
        if metric_type == "system":
            return [
                m.to_dict() for m in self.system_metrics_history 
                if m.timestamp >= cutoff_time
            ]
        elif metric_type == "application":
            return [
                m.to_dict() for m in self.application_metrics_history 
                if m.timestamp >= cutoff_time
            ]
        elif metric_type == "agent" and agent_name:
            return [
                m.to_dict() for m in self.agent_metrics_history[agent_name]
                if m.timestamp >= cutoff_time
            ]
        else:
            return []
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Obtener resumen de rendimiento"""
        summary = {
            "system_health": "unknown",
            "application_performance": "unknown",
            "agent_performance": {},
            "trends": {}
        }
        
        # Evaluar salud del sistema
        if self.system_metrics_history:
            recent_system = list(self.system_metrics_history)[-5:]
            avg_cpu = sum(m.cpu_percent for m in recent_system) / len(recent_system)
            avg_memory = sum(m.memory_percent for m in recent_system) / len(recent_system)
            
            if avg_cpu < 70 and avg_memory < 80:
                summary["system_health"] = "healthy"
            elif avg_cpu < 90 and avg_memory < 95:
                summary["system_health"] = "degraded"
            else:
                summary["system_health"] = "critical"
        
        # Evaluar rendimiento de la aplicación
        if self.application_metrics_history:
            recent_app = list(self.application_metrics_history)[-5:]
            avg_response_time = sum(m.response_time_p95 for m in recent_app) / len(recent_app)
            avg_error_rate = sum(m.error_rate for m in recent_app) / len(recent_app)
            
            if avg_response_time < 1.0 and avg_error_rate < 0.01:
                summary["application_performance"] = "excellent"
            elif avg_response_time < 2.0 and avg_error_rate < 0.05:
                summary["application_performance"] = "good"
            elif avg_response_time < 5.0 and avg_error_rate < 0.1:
                summary["application_performance"] = "fair"
            else:
                summary["application_performance"] = "poor"
        
        # Evaluar rendimiento de agentes
        for agent_name, metrics in self.agent_metrics_history.items():
            if metrics:
                recent_metrics = list(metrics)[-5:]
                avg_success_rate = sum(m.success_rate for m in recent_metrics) / len(recent_metrics)
                avg_execution_time = sum(m.avg_execution_time for m in recent_metrics) / len(recent_metrics)
                
                if avg_success_rate > 0.95 and avg_execution_time < 1.0:
                    performance = "excellent"
                elif avg_success_rate > 0.9 and avg_execution_time < 2.0:
                    performance = "good"
                elif avg_success_rate > 0.8 and avg_execution_time < 3.0:
                    performance = "fair"
                else:
                    performance = "poor"
                
                summary["agent_performance"][agent_name] = {
                    "status": performance,
                    "success_rate": avg_success_rate,
                    "avg_execution_time": avg_execution_time
                }
        
        return summary
    
    def register_metric_callback(self, callback: Callable):
        """Registrar callback para notificaciones de métricas"""
        self.metric_callbacks.append(callback)
    
    def export_metrics(self, format_type: str = "json") -> str:
        """Exportar métricas en formato especificado"""
        if format_type == "json":
            return json.dumps(self.get_current_metrics(), indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")


class MetricsAggregator:
    """Agregador de métricas para análisis y reporting"""
    
    def __init__(self, collector: HealthMetricsCollector):
        self.collector = collector
        self.logger = logging.getLogger("mcp.metrics.aggregator")
    
    def calculate_percentile(self, values: List[float], percentile: float) -> float:
        """Calcular percentil de una lista de valores"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(percentile * len(sorted_values) / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def calculate_trend(self, values: List[float]) -> Dict[str, float]:
        """Calcular tendencia de una serie de valores"""
        if len(values) < 2:
            return {"slope": 0.0, "correlation": 0.0}
        
        import numpy as np
        
        x = np.arange(len(values))
        y = np.array(values)
        
        # Calcular pendiente
        slope, intercept = np.polyfit(x, y, 1)
        
        # Calcular correlación
        correlation = np.corrcoef(x, y)[0, 1]
        
        return {
            "slope": slope,
            "correlation": correlation if not np.isnan(correlation) else 0.0
        }
    
    def generate_performance_report(self, time_range: timedelta = timedelta(hours=1)) -> Dict[str, Any]:
        """Generar reporte completo de rendimiento"""
        report = {
            "report_period": {
                "start": (datetime.now() - time_range).isoformat(),
                "end": datetime.now().isoformat()
            },
            "system_metrics": {},
            "application_metrics": {},
            "agent_metrics": {},
            "anomalies": [],
            "recommendations": []
        }
        
        # Analizar métricas del sistema
        system_metrics = self.collector.get_metrics_history("system", time_range=time_range)
        if system_metrics:
            cpu_values = [m["cpu_percent"] for m in system_metrics]
            memory_values = [m["memory_percent"] for m in system_metrics]
            
            report["system_metrics"] = {
                "avg_cpu": sum(cpu_values) / len(cpu_values),
                "max_cpu": max(cpu_values),
                "avg_memory": sum(memory_values) / len(memory_values),
                "max_memory": max(memory_values),
                "cpu_trend": self.calculate_trend(cpu_values),
                "memory_trend": self.calculate_trend(memory_values)
            }
            
            # Detectar anomalías
            if max(cpu_values) > 90:
                report["anomalies"].append("CPU usage exceeded 90%")
            if max(memory_values) > 95:
                report["anomalies"].append("Memory usage exceeded 95%")
        
        # Analizar métricas de aplicación
        app_metrics = self.collector.get_metrics_history("application", time_range=time_range)
        if app_metrics:
            response_times = [m["response_time_p95"] for m in app_metrics]
            error_rates = [m["error_rate"] for m in app_metrics]
            throughput_values = [m["throughput"] for m in app_metrics]
            
            report["application_metrics"] = {
                "avg_response_time": sum(response_times) / len(response_times),
                "p95_response_time": self.calculate_percentile(response_times, 95),
                "avg_error_rate": sum(error_rates) / len(error_rates),
                "avg_throughput": sum(throughput_values) / len(throughput_values),
                "response_time_trend": self.calculate_trend(response_times),
                "throughput_trend": self.calculate_trend(throughput_values)
            }
            
            # Detectar anomalías
            if self.calculate_percentile(response_times, 95) > 2.0:
                report["anomalies"].append("High response time detected")
            if max(error_rates) > 0.1:
                report["anomalies"].append("High error rate detected")
        
        # Generar recomendaciones
        recommendations = []
        
        if report["system_metrics"].get("avg_cpu", 0) > 80:
            recommendations.append("Consider scaling up CPU resources")
        
        if report["system_metrics"].get("avg_memory", 0) > 85:
            recommendations.append("Consider scaling up memory resources")
        
        if report["application_metrics"].get("avg_error_rate", 0) > 0.05:
            recommendations.append("Investigate high error rate - check application logs")
        
        if report["application_metrics"].get("avg_response_time", 0) > 2.0:
            recommendations.append("Optimize application performance - high response times")
        
        report["recommendations"] = recommendations
        
        return report


# ==================== INSTANCIA GLOBAL ====================

# Instancia global del recolector de métricas
_metrics_collector: Optional[HealthMetricsCollector] = None

def get_metrics_collector(collection_interval: int = 10) -> HealthMetricsCollector:
    """Obtener instancia global del recolector de métricas"""
    global _metrics_collector
    
    if _metrics_collector is None:
        _metrics_collector = HealthMetricsCollector(collection_interval)
    
    return _metrics_collector


async def initialize_metrics_collection(collection_interval: int = 10) -> HealthMetricsCollector:
    """Inicializar recolección de métricas"""
    collector = get_metrics_collector(collection_interval)
    await collector.start_collection()
    return collector


if __name__ == "__main__":
    # Ejemplo de uso
    async def main():
        collector = HealthMetricsCollector(collection_interval=5)
        await collector.start_collection()
        
        # Dejar que recolecte métricas por un tiempo
        await asyncio.sleep(30)
        
        # Mostrar métricas actuales
        current = collector.get_current_metrics()
        print(json.dumps(current, indent=2, default=str))
        
        # Generar reporte
        aggregator = MetricsAggregator(collector)
        report = aggregator.generate_performance_report(timedelta(minutes=5))
        print(json.dumps(report, indent=2, default=str))
        
        await collector.stop_collection()
    
    asyncio.run(main())