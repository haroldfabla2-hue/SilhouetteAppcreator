"""
Sistema de Métricas Avanzadas para MCP Core Superior
Implementa métricas completas para monitoreo, análisis y planificación de capacidad
Compatible con Prometheus y Grafana
"""
import asyncio
import time
import psutil
import logging
import json
import sqlite3
import threading
from typing import Dict, Any, List, Optional, Callable, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
import statistics
import math
import numpy as np
from pathlib import Path

# Importaciones locales
from ..core.health_metrics import HealthMetricsCollector
from ..core.config import settings


class MetricType(Enum):
    """Tipos de métricas disponibles"""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    RESOURCE_UTILIZATION = "resource_utilization"
    HEALTH_SCORE = "health_score"
    BUSINESS = "business"
    CAPACITY = "capacity"


class AlertSeverity(Enum):
    """Niveles de severidad para alertas"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class TimeSeriesAggregation(Enum):
    """Métodos de agregación para series de tiempo"""
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTILE = "percentile"


@dataclass
class LatencyMetric:
    """Métrica de latencia por agente y operación"""
    timestamp: datetime
    agent_name: str
    operation: str
    latency_ms: float
    status: str  # "success", "error", "timeout"
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    method: Optional[str] = None
    
    def to_prometheus_dict(self) -> Dict[str, Union[str, float]]:
        """Convierte a formato Prometheus"""
        return {
            "metric_name": "mcp_latency_milliseconds",
            "labels": {
                "agent": self.agent_name,
                "operation": self.operation,
                "status": self.status
            },
            "value": self.latency_ms,
            "timestamp": self.timestamp.timestamp()
        }


@dataclass
class ThroughputMetric:
    """Métrica de throughput del sistema"""
    timestamp: datetime
    requests_per_second: float
    concurrent_users: int
    active_connections: int
    queue_depth: int
    processing_rate: float
    response_rate: float
    throughput_type: str = "requests"  # requests, bytes, tasks
    
    def to_prometheus_dict(self) -> Dict[str, Union[str, float]]:
        return {
            "metric_name": "mcp_throughput_operations_per_second",
            "labels": {
                "type": self.throughput_type
            },
            "value": self.requests_per_second,
            "timestamp": self.timestamp.timestamp()
        }


@dataclass
class ErrorRateMetric:
    """Métrica de tasas de error y ratios de éxito"""
    timestamp: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    timeout_requests: int
    error_rate: float
    success_rate: float
    agent_name: Optional[str] = None
    error_types: Dict[str, int] = field(default_factory=dict)
    
    @property
    def mttf_minutes(self) -> float:  # Mean Time To Failure
        """Tiempo promedio entre fallos en minutos"""
        if self.failed_requests == 0:
            return float('inf')
        time_window = 1  # minuto actual
        return time_window / (self.failed_requests / self.total_requests) if self.total_requests > 0 else 0
    
    def to_prometheus_dict(self) -> Dict[str, Union[str, float]]:
        labels = {"agent": self.agent_name} if self.agent_name else {}
        return {
            "metric_name": "mcp_error_rate_ratio",
            "labels": labels,
            "value": self.error_rate,
            "timestamp": self.timestamp.timestamp()
        }


@dataclass
class ResourceUtilizationMetric:
    """Métrica de utilización de recursos del sistema"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_available_gb: float
    disk_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_bytes_sent: float
    network_io_bytes_recv: float
    thread_count: int
    file_descriptor_count: int
    load_average: List[float]
    
    def to_prometheus_dict(self) -> Dict[str, Union[str, float]]:
        metrics = [
            {
                "metric_name": "mcp_cpu_usage_percent",
                "labels": {},
                "value": self.cpu_percent,
                "timestamp": self.timestamp.timestamp()
            },
            {
                "metric_name": "mcp_memory_usage_percent", 
                "labels": {},
                "value": self.memory_percent,
                "timestamp": self.timestamp.timestamp()
            },
            {
                "metric_name": "mcp_disk_usage_percent",
                "labels": {},
                "value": self.disk_percent,
                "timestamp": self.timestamp.timestamp()
            }
        ]
        return metrics


@dataclass
class AgentHealthScore:
    """Puntuación de salud de agentes"""
    timestamp: datetime
    agent_name: str
    health_score: float  # 0-100
    availability_percent: float
    performance_score: float
    reliability_score: float
    last_health_check: datetime
    uptime_minutes: float
    total_executions: int
    successful_executions: int
    avg_response_time_ms: float
    error_count_last_hour: int
    
    @property
    def status_level(self) -> str:
        """Determina el nivel de estado basado en la puntuación"""
        if self.health_score >= 90:
            return "excellent"
        elif self.health_score >= 75:
            return "good"
        elif self.health_score >= 60:
            return "fair"
        elif self.health_score >= 40:
            return "poor"
        else:
            return "critical"
    
    def to_prometheus_dict(self) -> Dict[str, Union[str, float]]:
        return {
            "metric_name": "mcp_agent_health_score",
            "labels": {"agent": self.agent_name},
            "value": self.health_score,
            "timestamp": self.timestamp.timestamp()
        }


@dataclass
class BusinessMetric:
    """Métricas de negocio"""
    timestamp: datetime
    tasks_completed: int
    sla_compliance_percent: float
    customer_satisfaction_score: float
    cost_per_operation: float
    revenue_generated: float
    operational_cost: float
    profit_margin: float
    business_kpi: str
    kpi_value: float
    kpi_target: float
    
    @property
    def sla_compliant(self) -> bool:
        """Verifica si cumple SLA"""
        return self.sla_compliance_percent >= 95.0
    
    def to_prometheus_dict(self) -> Dict[str, Union[str, float]]:
        return {
            "metric_name": "mcp_sla_compliance_percent",
            "labels": {"kpi": self.business_kpi},
            "value": self.sla_compliance_percent,
            "timestamp": self.timestamp.timestamp()
        }


@dataclass
class CapacityPlanningMetric:
    """Métricas para planificación de capacidad"""
    timestamp: datetime
    current_capacity_usage_percent: float
    projected_capacity_need: float
    scaling_recommendations: List[str]
    resource_bottlenecks: List[str]
    performance_trends: Dict[str, float]
    cost_analysis: Dict[str, float]
    optimization_opportunities: List[str]
    forecast_horizon_days: int = 30
    
    def to_prometheus_dict(self) -> Dict[str, Union[str, float]]:
        return {
            "metric_name": "mcp_capacity_usage_percent",
            "labels": {},
            "value": self.current_capacity_usage_percent,
            "timestamp": self.timestamp.timestamp()
        }


@dataclass
class CustomAlert:
    """Alerta personalizada del sistema"""
    id: str
    timestamp: datetime
    severity: AlertSeverity
    title: str
    message: str
    metric_name: str
    current_value: float
    threshold_value: float
    operator: str  # ">", "<", ">=", "<=", "==", "!="
    agent_name: Optional[str] = None
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    
    def is_triggered(self, value: float) -> bool:
        """Verifica si la alerta debe activarse"""
        if self.operator == ">":
            return value > self.threshold_value
        elif self.operator == "<":
            return value < self.threshold_value
        elif self.operator == ">=":
            return value >= self.threshold_value
        elif self.operator == "<=":
            return value <= self.threshold_value
        elif self.operator == "==":
            return value == self.threshold_value
        elif self.operator == "!=":
            return value != self.threshold_value
        return False


class TimeSeriesStorage:
    """Almacenamiento optimizado para series temporales"""
    
    def __init__(self, db_path: str = "metrics_timeseries.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Inicializa la base de datos SQLite para métricas"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS time_series_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    metric_type TEXT,
                    metric_name TEXT,
                    agent_name TEXT,
                    labels TEXT,
                    value REAL,
                    created_at REAL DEFAULT (julianday('now'))
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp_metric 
                ON time_series_metrics (timestamp, metric_name)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_timestamp 
                ON time_series_metrics (agent_name, timestamp)
            """)
    
    def store_metric(self, 
                    metric_type: str, 
                    metric_name: str, 
                    value: float, 
                    timestamp: datetime,
                    agent_name: Optional[str] = None,
                    labels: Optional[Dict[str, str]] = None):
        """Almacena una métrica en la base de datos"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO time_series_metrics 
                (timestamp, metric_type, metric_name, agent_name, labels, value)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                timestamp.timestamp(),
                metric_type,
                metric_name,
                agent_name,
                json.dumps(labels or {}),
                value
            ))
    
    def query_metrics(self,
                     metric_name: str,
                     start_time: datetime,
                     end_time: datetime,
                     agent_name: Optional[str] = None,
                     aggregation: TimeSeriesAggregation = TimeSeriesAggregation.AVG,
                     bucket_size_seconds: int = 60) -> List[Tuple[float, float]]:
        """Consulta métricas con agregación temporal"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            where_conditions = [
                "timestamp >= ? AND timestamp < ?",
                "metric_name = ?"
            ]
            params = [start_time.timestamp(), end_time.timestamp(), metric_name]
            
            if agent_name:
                where_conditions.append("agent_name = ?")
                params.append(agent_name)
            
            # Calcular buckets de tiempo
            total_seconds = (end_time - start_time).total_seconds()
            num_buckets = max(1, int(total_seconds / bucket_size_seconds))
            
            if aggregation == TimeSeriesAggregation.AVG:
                sql = f"""
                    SELECT 
                        (timestamp / {bucket_size_seconds}) * {bucket_size_seconds} as bucket_time,
                        AVG(value) as aggregated_value
                    FROM time_series_metrics
                    WHERE {' AND '.join(where_conditions)}
                    GROUP BY bucket_time
                    ORDER BY bucket_time
                """
            elif aggregation == TimeSeriesAggregation.MAX:
                sql = f"""
                    SELECT 
                        (timestamp / {bucket_size_seconds}) * {bucket_size_seconds} as bucket_time,
                        MAX(value) as aggregated_value
                    FROM time_series_metrics
                    WHERE {' AND '.join(where_conditions)}
                    GROUP BY bucket_time
                    ORDER BY bucket_time
                """
            elif aggregation == TimeSeriesAggregation.SUM:
                sql = f"""
                    SELECT 
                        (timestamp / {bucket_size_seconds}) * {bucket_size_seconds} as bucket_time,
                        SUM(value) as aggregated_value
                    FROM time_series_metrics
                    WHERE {' AND '.join(where_conditions)}
                    GROUP BY bucket_time
                    ORDER BY bucket_time
                """
            else:
                sql = f"""
                    SELECT timestamp, value
                    FROM time_series_metrics
                    WHERE {' AND '.join(where_conditions)}
                    ORDER BY timestamp
                """
            
            cursor.execute(sql, params)
            return [(row[0], row[1]) for row in cursor.fetchall()]
    
    def cleanup_old_metrics(self, retention_days: int = 30):
        """Limpia métricas antiguas según la retención"""
        cutoff_time = datetime.now() - timedelta(days=retention_days)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                DELETE FROM time_series_metrics 
                WHERE created_at < julianday(?) - ?
            """, (datetime.now(), retention_days))


class PercentileCalculator:
    """Calculadora de percentiles optimizada"""
    
    @staticmethod
    def calculate_percentile_approximate(values: List[float], percentile: float) -> float:
        """Calcula percentil de forma aproximada pero eficiente"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        index = (percentile / 100.0) * (n - 1)
        
        lower = int(index)
        upper = min(lower + 1, n - 1)
        weight = index - lower
        
        if upper >= n:
            return sorted_values[n - 1]
        
        return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight
    
    @staticmethod
    def calculate_all_percentiles(values: List[float]) -> Dict[str, float]:
        """Calcula múltiples percentiles de una vez"""
        if not values:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "p99_9": 0.0}
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        return {
            "p50": PercentileCalculator.calculate_percentile_approximate(values, 50),
            "p95": PercentileCalculator.calculate_percentile_approximate(values, 95),
            "p99": PercentileCalculator.calculate_percentile_approximate(values, 99),
            "p99_9": PercentileCalculator.calculate_percentile_approximate(values, 99.9)
        }


class AdvancedMetricsCollector:
    """Recolector principal de métricas avanzadas"""
    
    def __init__(self, 
                 collection_interval: int = 10,
                 time_series_storage: Optional[TimeSeriesStorage] = None):
        self.collection_interval = collection_interval
        self.storage = time_series_storage or TimeSeriesStorage()
        self.logger = logging.getLogger("mcp.advanced.metrics")
        
        # Colas de métricas en memoria
        self.latency_metrics: deque = deque(maxlen=10000)
        self.throughput_metrics: deque = deque(maxlen=1000)
        self.error_rate_metrics: deque = deque(maxlen=1000)
        self.resource_metrics: deque = deque(maxlen=1000)
        self.health_scores: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.business_metrics: deque = deque(maxlen=500)
        self.capacity_metrics: deque = deque(maxlen=100)
        
        # Almacenamiento de muestras para cálculos
        self.response_time_samples: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.throughput_samples: deque = deque(maxlen=1000)
        self.error_samples: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Alertas personalizadas
        self.custom_alerts: Dict[str, CustomAlert] = {}
        self.active_alerts: Dict[str, datetime] = {}
        
        # Estado de recolección
        self.is_collecting = False
        self._collection_task: Optional[asyncio.Task] = None
        self._lock = threading.Lock()
        
        # Callbacks para integraciones
        self.alert_callbacks: List[Callable] = []
        self.dashboard_callbacks: List[Callable] = []
        
        # Recolector básico de salud
        self.health_collector = HealthMetricsCollector(collection_interval)
        
        # Configuración de alertas
        self._setup_default_alerts()
        
        self.logger.info("Advanced metrics collector initialized")
    
    def _setup_default_alerts(self):
        """Configura alertas por defecto del sistema"""
        default_alerts = [
            CustomAlert(
                id="high_cpu",
                timestamp=datetime.now(),
                severity=AlertSeverity.WARNING,
                title="High CPU Usage",
                message="CPU usage exceeds 80%",
                metric_name="mcp_cpu_usage_percent",
                current_value=0.0,
                threshold_value=80.0,
                operator=">"
            ),
            CustomAlert(
                id="high_memory",
                timestamp=datetime.now(),
                severity=AlertSeverity.WARNING,
                title="High Memory Usage",
                message="Memory usage exceeds 85%",
                metric_name="mcp_memory_usage_percent",
                current_value=0.0,
                threshold_value=85.0,
                operator=">"
            ),
            CustomAlert(
                id="high_error_rate",
                timestamp=datetime.now(),
                severity=AlertSeverity.CRITICAL,
                title="High Error Rate",
                message="Error rate exceeds 5%",
                metric_name="mcp_error_rate_ratio",
                current_value=0.0,
                threshold_value=0.05,
                operator=">"
            ),
            CustomAlert(
                id="agent_unhealthy",
                timestamp=datetime.now(),
                severity=AlertSeverity.CRITICAL,
                title="Agent Unhealthy",
                message="Agent health score below 60",
                metric_name="mcp_agent_health_score",
                current_value=100.0,
                threshold_value=60.0,
                operator="<"
            )
        ]
        
        for alert in default_alerts:
            self.custom_alerts[alert.id] = alert
    
    async def start_collection(self):
        """Iniciar recolección de métricas avanzadas"""
        if self.is_collecting:
            return
        
        self.is_collecting = True
        self._collection_task = asyncio.create_task(self._advanced_collection_loop())
        await self.health_collector.start_collection()
        
        self.logger.info("Advanced metrics collection started")
    
    async def stop_collection(self):
        """Detener recolección de métricas"""
        self.is_collecting = False
        
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        
        await self.health_collector.stop_collection()
        self.logger.info("Advanced metrics collection stopped")
    
    async def _advanced_collection_loop(self):
        """Loop principal de recolección de métricas avanzadas"""
        while self.is_collecting:
            start_time = time.time()
            
            try:
                # Recopilar todas las métricas avanzadas
                await self._collect_advanced_metrics()
                
                # Evaluar alertas
                await self._evaluate_alerts()
                
                # Actualizar dashboards
                await self._update_dashboards()
                
                # Notificar callbacks
                await self._notify_callbacks()
                
            except Exception as e:
                self.logger.error(f"Error in advanced metrics collection: {e}")
            
            # Esperar al próximo intervalo
            await asyncio.sleep(self.collection_interval)
    
    async def _collect_advanced_metrics(self):
        """Recopilar todas las métricas avanzadas"""
        # Recopilar métricas del sistema
        await self._collect_resource_metrics()
        
        # Recopilar métricas de latencia
        await self._collect_latency_metrics()
        
        # Recopilar métricas de throughput
        await self._collect_throughput_metrics()
        
        # Recopilar métricas de error rate
        await self._collect_error_rate_metrics()
        
        # Recopilar health scores
        await self._collect_health_scores()
        
        # Recopilar métricas de negocio
        await self._collect_business_metrics()
        
        # Recopilar métricas de capacidad
        await self._collect_capacity_metrics()
    
    async def _collect_resource_metrics(self):
        """Recopilar métricas de recursos del sistema"""
        loop = asyncio.get_event_loop()
        
        def collect_psutil_data():
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory": psutil.virtual_memory(),
                "disk": psutil.disk_usage('/'),
                "network": psutil.net_io_counters(),
                "threads": threading.active_count(),
                "fds": len(psutil.Process().open_files()) if hasattr(psutil.Process(), 'open_files') else 0,
                "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0.0, 0.0, 0.0]
            }
        
        data = await loop.run_in_executor(None, collect_psutil_data)
        
        metric = ResourceUtilizationMetric(
            timestamp=datetime.now(),
            cpu_percent=data["cpu_percent"],
            memory_percent=data["memory"].percent,
            memory_used_gb=data["memory"].used / (1024**3),
            memory_available_gb=data["memory"].available / (1024**3),
            disk_percent=data["disk"].percent,
            disk_io_read_mb=0.0,  # Se podría obtener con psutil.disk_io_counters()
            disk_io_write_mb=0.0,
            network_io_bytes_sent=data["network"].bytes_sent,
            network_io_bytes_recv=data["network"].bytes_recv,
            thread_count=data["threads"],
            file_descriptor_count=data["fds"],
            load_average=list(data["load_avg"])
        )
        
        self.resource_metrics.append(metric)
        
        # Almacenar en base de datos
        for prom_metric in metric.to_prometheus_dict():
            self.storage.store_metric(
                MetricType.RESOURCE_UTILIZATION.value,
                prom_metric["metric_name"],
                prom_metric["value"],
                metric.timestamp,
                labels=prom_metric["labels"]
            )
    
    async def _collect_latency_metrics(self):
        """Recopilar métricas de latencia simuladas"""
        # En implementación real, esto vendría de logs y trazas reales
        import random
        
        agents = ["reasoner", "planner", "executor", "verifier", "memory_manager", "orchestrator"]
        operations = ["process_task", "analyze", "execute", "validate", "store", "route"]
        
        for _ in range(random.randint(1, 5)):  # 1-5 métricas por ciclo
            agent = random.choice(agents)
            operation = random.choice(operations)
            
            metric = LatencyMetric(
                timestamp=datetime.now(),
                agent_name=agent,
                operation=operation,
                latency_ms=random.uniform(10, 1000),
                status="success" if random.random() > 0.05 else "error",
                request_id=f"req_{random.randint(1000, 9999)}"
            )
            
            self.latency_metrics.append(metric)
            
            # Almacenar en base de datos
            self.storage.store_metric(
                MetricType.LATENCY.value,
                "mcp_latency_milliseconds",
                metric.latency_ms,
                metric.timestamp,
                agent,
                {"operation": operation, "status": metric.status}
            )
            
            # Agregar a muestras para percentiles
            key = f"{agent}_{operation}"
            self.response_time_samples[key].append(metric.latency_ms)
    
    async def _collect_throughput_metrics(self):
        """Recopilar métricas de throughput"""
        import random
        
        # Simular métricas de throughput
        metric = ThroughputMetric(
            timestamp=datetime.now(),
            requests_per_second=random.uniform(1, 50),
            concurrent_users=random.randint(5, 100),
            active_connections=random.randint(3, 30),
            queue_depth=random.randint(0, 20),
            processing_rate=random.uniform(0.8, 1.2),
            response_rate=random.uniform(0.9, 1.0)
        )
        
        self.throughput_metrics.append(metric)
        
        # Almacenar en base de datos
        prom_metric = metric.to_prometheus_dict()
        self.storage.store_metric(
            MetricType.THROUGHPUT.value,
            prom_metric["metric_name"],
            prom_metric["value"],
            metric.timestamp,
            labels=prom_metric["labels"]
        )
        
        self.throughput_samples.append(metric.requests_per_second)
    
    async def _collect_error_rate_metrics(self):
        """Recopilar métricas de tasa de error"""
        import random
        
        agents = ["reasoner", "planner", "executor", "verifier", "memory_manager", "orchestrator"]
        agent = random.choice(agents)
        
        total_requests = random.randint(50, 200)
        failed_requests = random.randint(0, int(total_requests * 0.1))
        timeout_requests = random.randint(0, int(total_requests * 0.05))
        successful_requests = total_requests - failed_requests - timeout_requests
        
        metric = ErrorRateMetric(
            timestamp=datetime.now(),
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            timeout_requests=timeout_requests,
            error_rate=failed_requests / total_requests if total_requests > 0 else 0,
            success_rate=successful_requests / total_requests if total_requests > 0 else 1,
            agent_name=agent,
            error_types={
                "validation_error": random.randint(0, 5),
                "timeout_error": random.randint(0, 3),
                "system_error": random.randint(0, 2)
            }
        )
        
        self.error_rate_metrics.append(metric)
        
        # Almacenar en base de datos
        prom_metric = metric.to_prometheus_dict()
        self.storage.store_metric(
            MetricType.ERROR_RATE.value,
            prom_metric["metric_name"],
            prom_metric["value"],
            metric.timestamp,
            agent_name=agent
        )
        
        # Agregar a muestras
        error_rate_key = f"{agent}_error_rate"
        self.error_samples[error_rate_key].append(metric.error_rate)
    
    async def _collect_health_scores(self):
        """Recopilar health scores de agentes"""
        agents = ["reasoner", "planner", "executor", "verifier", "memory_manager", "orchestrator"]
        
        for agent in agents:
            # Simular cálculo de health score
            import random
            
            # Basado en métricas recientes del agente
            performance_score = random.uniform(70, 95)
            reliability_score = random.uniform(80, 98)
            availability = random.uniform(95, 99.9)
            
            health_score = (performance_score * 0.3 + reliability_score * 0.4 + availability * 0.3)
            
            metric = AgentHealthScore(
                timestamp=datetime.now(),
                agent_name=agent,
                health_score=health_score,
                availability_percent=availability,
                performance_score=performance_score,
                reliability_score=reliability_score,
                last_health_check=datetime.now() - timedelta(seconds=random.randint(1, 60)),
                uptime_minutes=random.uniform(60, 1440),
                total_executions=random.randint(100, 1000),
                successful_executions=random.randint(90, 980),
                avg_response_time_ms=random.uniform(100, 500),
                error_count_last_hour=random.randint(0, 10)
            )
            
            self.health_scores[agent].append(metric)
            
            # Almacenar en base de datos
            prom_metric = metric.to_prometheus_dict()
            self.storage.store_metric(
                MetricType.HEALTH_SCORE.value,
                prom_metric["metric_name"],
                prom_metric["value"],
                metric.timestamp,
                agent,
                {"status": metric.status_level}
            )
    
    async def _collect_business_metrics(self):
        """Recopilar métricas de negocio"""
        import random
        
        # Simular métricas de negocio realistas
        metric = BusinessMetric(
            timestamp=datetime.now(),
            tasks_completed=random.randint(10, 100),
            sla_compliance_percent=random.uniform(95, 99.8),
            customer_satisfaction_score=random.uniform(4.0, 5.0),
            cost_per_operation=random.uniform(0.10, 0.50),
            revenue_generated=random.uniform(100, 1000),
            operational_cost=random.uniform(50, 300),
            profit_margin=random.uniform(0.2, 0.6),
            business_kpi="tasks_per_hour",
            kpi_value=random.uniform(50, 200),
            kpi_target=150.0
        )
        
        self.business_metrics.append(metric)
        
        # Almacenar en base de datos
        prom_metric = metric.to_prometheus_dict()
        self.storage.store_metric(
            MetricType.BUSINESS.value,
            prom_metric["metric_name"],
            prom_metric["value"],
            metric.timestamp,
            labels=prom_metric["labels"]
        )
    
    async def _collect_capacity_metrics(self):
        """Recopilar métricas de planificación de capacidad"""
        import random
        
        # Obtener métricas de recursos recientes para análisis
        recent_resources = list(self.resource_metrics)[-10:] if self.resource_metrics else []
        
        cpu_trend = 0.0
        memory_trend = 0.0
        
        if len(recent_resources) >= 2:
            cpu_trend = (recent_resources[-1].cpu_percent - recent_resources[0].cpu_percent) / len(recent_resources)
            memory_trend = (recent_resources[-1].memory_percent - recent_resources[0].memory_percent) / len(recent_resources)
        
        # Proyectar necesidades de capacidad
        projected_cpu_need = max(0, cpu_trend * 60)  # Proyección a 60 minutos
        projected_memory_need = max(0, memory_trend * 60)
        
        # Generar recomendaciones
        recommendations = []
        bottlenecks = []
        
        if projected_cpu_need > 20:
            recommendations.append("Consider scaling up CPU resources")
            bottlenecks.append("CPU")
        
        if projected_memory_need > 15:
            recommendations.append("Consider scaling up memory resources")
            bottlenecks.append("Memory")
        
        if recent_resources:
            avg_cpu = sum(r.cpu_percent for r in recent_resources) / len(recent_resources)
            avg_memory = sum(r.memory_percent for r in recent_resources) / len(recent_resources)
            current_usage = max(avg_cpu, avg_memory)
        else:
            current_usage = random.uniform(30, 70)
        
        metric = CapacityPlanningMetric(
            timestamp=datetime.now(),
            current_capacity_usage_percent=current_usage,
            projected_capacity_need=projected_cpu_need + projected_memory_need,
            scaling_recommendations=recommendations,
            resource_bottlenecks=bottlenecks,
            performance_trends={
                "cpu_trend": cpu_trend,
                "memory_trend": memory_trend,
                "throughput_trend": random.uniform(-5, 10)
            },
            cost_analysis={
                "current_cost_per_hour": random.uniform(10, 50),
                "projected_cost_per_hour": random.uniform(15, 75),
                "cost_optimization_potential": random.uniform(5, 25)
            },
            optimization_opportunities=[
                "Implement caching layer",
                "Optimize database queries",
                "Scale horizontal services"
            ] if current_usage > 75 else []
        )
        
        self.capacity_metrics.append(metric)
        
        # Almacenar en base de datos
        prom_metric = metric.to_prometheus_dict()
        self.storage.store_metric(
            MetricType.CAPACITY.value,
            prom_metric["metric_name"],
            prom_metric["value"],
            metric.timestamp
        )
    
    async def _evaluate_alerts(self):
        """Evaluar y activar/desactivar alertas"""
        current_time = datetime.now()
        
        # Evaluar alertas con métricas recientes
        for alert_id, alert in self.custom_alerts.items():
            current_value = await self._get_current_metric_value(alert.metric_name, alert.agent_name)
            
            if current_value is not None:
                alert.current_value = current_value
                
                if alert.is_triggered(current_value) and alert_id not in self.active_alerts:
                    # Activar alerta
                    self.active_alerts[alert_id] = current_time
                    await self._trigger_alert(alert)
                
                elif not alert.is_triggered(current_value) and alert_id in self.active_alerts:
                    # Resolver alerta
                    alert.resolved = True
                    alert.resolution_time = current_time
                    del self.active_alerts[alert_id]
                    await self._resolve_alert(alert)
    
    async def _get_current_metric_value(self, metric_name: str, agent_name: Optional[str] = None) -> Optional[float]:
        """Obtener valor actual de una métrica"""
        if metric_name == "mcp_cpu_usage_percent" and self.resource_metrics:
            return self.resource_metrics[-1].cpu_percent
        elif metric_name == "mcp_memory_usage_percent" and self.resource_metrics:
            return self.resource_metrics[-1].memory_percent
        elif metric_name == "mcp_error_rate_ratio":
            if self.error_rate_metrics:
                recent_errors = [m for m in self.error_rate_metrics 
                               if (agent_name is None or m.agent_name == agent_name)]
                if recent_errors:
                    return sum(m.error_rate for m in recent_errors[-5:]) / min(5, len(recent_errors))
        elif metric_name == "mcp_agent_health_score" and agent_name and agent_name in self.health_scores:
            if self.health_scores[agent_name]:
                return self.health_scores[agent_name][-1].health_score
        
        return None
    
    async def _trigger_alert(self, alert: CustomAlert):
        """Activar una alerta"""
        self.logger.warning(f"ALERT TRIGGERED: {alert.title} - {alert.message}")
        
        # Notificar callbacks
        for callback in self.alert_callbacks:
            try:
                await callback("triggered", alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {e}")
    
    async def _resolve_alert(self, alert: CustomAlert):
        """Resolver una alerta"""
        self.logger.info(f"ALERT RESOLVED: {alert.title} - {alert.message}")
        
        # Notificar callbacks
        for callback in self.alert_callbacks:
            try:
                await callback("resolved", alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {e}")
    
    async def _update_dashboards(self):
        """Actualizar dashboards personalizados"""
        dashboard_data = self._generate_dashboard_data()
        
        for callback in self.dashboard_callbacks:
            try:
                await callback(dashboard_data)
            except Exception as e:
                self.logger.error(f"Error in dashboard callback: {e}")
    
    def _generate_dashboard_data(self) -> Dict[str, Any]:
        """Generar datos para dashboards"""
        current_time = datetime.now()
        hour_ago = current_time - timedelta(hours=1)
        
        return {
            "timestamp": current_time.isoformat(),
            "system_health": self._calculate_system_health_score(),
            "top_agents": self._get_top_performing_agents(),
            "resource_utilization": self._get_current_resource_utilization(),
            "active_alerts": len(self.active_alerts),
            "business_summary": self._get_business_summary(),
            "trends": self._calculate_recent_trends()
        }
    
    def _calculate_system_health_score(self) -> float:
        """Calcular puntuación general de salud del sistema"""
        if not self.resource_metrics:
            return 0.0
        
        recent_resources = list(self.resource_metrics)[-5:]
        avg_cpu = sum(r.cpu_percent for r in recent_resources) / len(recent_resources)
        avg_memory = sum(r.memory_percent for r in recent_resources) / len(recent_resources)
        
        # Score basado en utilización de recursos (0-100)
        cpu_score = max(0, 100 - avg_cpu)
        memory_score = max(0, 100 - avg_memory)
        
        return (cpu_score + memory_score) / 2
    
    def _get_top_performing_agents(self) -> List[Dict[str, Any]]:
        """Obtener mejores agentes por rendimiento"""
        top_agents = []
        
        for agent, metrics in self.health_scores.items():
            if metrics:
                recent_metrics = list(metrics)[-5:]
                avg_health = sum(m.health_score for m in recent_metrics) / len(recent_metrics)
                avg_response = sum(m.avg_response_time_ms for m in recent_metrics) / len(recent_metrics)
                
                top_agents.append({
                    "agent": agent,
                    "health_score": avg_health,
                    "avg_response_time": avg_response,
                    "status": metrics[-1].status_level
                })
        
        return sorted(top_agents, key=lambda x: x["health_score"], reverse=True)[:5]
    
    def _get_current_resource_utilization(self) -> Dict[str, float]:
        """Obtener utilización actual de recursos"""
        if not self.resource_metrics:
            return {}
        
        latest = self.resource_metrics[-1]
        return {
            "cpu_percent": latest.cpu_percent,
            "memory_percent": latest.memory_percent,
            "disk_percent": latest.disk_percent
        }
    
    def _get_business_summary(self) -> Dict[str, Any]:
        """Obtener resumen de métricas de negocio"""
        if not self.business_metrics:
            return {}
        
        recent_metrics = list(self.business_metrics)[-5:]
        return {
            "avg_tasks_completed": sum(m.tasks_completed for m in recent_metrics) / len(recent_metrics),
            "avg_sla_compliance": sum(m.sla_compliance_percent for m in recent_metrics) / len(recent_metrics),
            "total_revenue": sum(m.revenue_generated for m in recent_metrics),
            "avg_profit_margin": sum(m.profit_margin for m in recent_metrics) / len(recent_metrics)
        }
    
    def _calculate_recent_trends(self) -> Dict[str, float]:
        """Calcular tendencias recientes"""
        trends = {}
        
        # Tendencia de throughput
        if len(self.throughput_samples) >= 10:
            recent_throughput = list(self.throughput_samples)[-10:]
            trends["throughput_trend"] = (recent_throughput[-1] - recent_throughput[0]) / len(recent_throughput)
        
        # Tendencia de latencia por agente
        for agent, samples in self.response_time_samples.items():
            if len(samples) >= 10:
                recent_samples = list(samples)[-10:]
                trends[f"{agent}_latency_trend"] = (recent_samples[-1] - recent_samples[0]) / len(recent_samples)
        
        return trends
    
    async def _notify_callbacks(self):
        """Notificar a todos los callbacks registrados"""
        # Los callbacks se manejan en los métodos específicos
        pass
    
    # ==================== MÉTODOS PÚBLICOS ====================
    
    def record_latency(self, agent_name: str, operation: str, latency_ms: float, status: str = "success", **kwargs):
        """Registrar latencia manualmente"""
        metric = LatencyMetric(
            timestamp=datetime.now(),
            agent_name=agent_name,
            operation=operation,
            latency_ms=latency_ms,
            status=status,
            **kwargs
        )
        self.latency_metrics.append(metric)
        
        # Almacenar en base de datos
        self.storage.store_metric(
            MetricType.LATENCY.value,
            "mcp_latency_milliseconds",
            latency_ms,
            metric.timestamp,
            agent_name,
            {"operation": operation, "status": status}
        )
    
    def record_throughput(self, requests_per_second: float, **kwargs):
        """Registrar throughput manualmente"""
        metric = ThroughputMetric(
            timestamp=datetime.now(),
            requests_per_second=requests_per_second,
            concurrent_users=kwargs.get("concurrent_users", 0),
            active_connections=kwargs.get("active_connections", 0),
            queue_depth=kwargs.get("queue_depth", 0),
            processing_rate=kwargs.get("processing_rate", 1.0),
            response_rate=kwargs.get("response_rate", 1.0),
            throughput_type=kwargs.get("throughput_type", "requests")
        )
        
        self.throughput_metrics.append(metric)
        self.throughput_samples.append(requests_per_second)
        
        # Almacenar en base de datos
        prom_metric = metric.to_prometheus_dict()
        self.storage.store_metric(
            MetricType.THROUGHPUT.value,
            prom_metric["metric_name"],
            prom_metric["value"],
            metric.timestamp,
            labels=prom_metric["labels"]
        )
    
    def add_custom_alert(self, alert: CustomAlert):
        """Agregar alerta personalizada"""
        self.custom_alerts[alert.id] = alert
    
    def remove_custom_alert(self, alert_id: str):
        """Eliminar alerta personalizada"""
        if alert_id in self.custom_alerts:
            del self.custom_alerts[alert_id]
        if alert_id in self.active_alerts:
            del self.active_alerts[alert_id]
    
    def register_alert_callback(self, callback: Callable):
        """Registrar callback para alertas"""
        self.alert_callbacks.append(callback)
    
    def register_dashboard_callback(self, callback: Callable):
        """Registrar callback para dashboards"""
        self.dashboard_callbacks.append(callback)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Obtener métricas actuales"""
        return {
            "timestamp": datetime.now().isoformat(),
            "system_resources": self.resource_metrics[-1].to_dict() if self.resource_metrics else None,
            "throughput": self.throughput_metrics[-1].to_dict() if self.throughput_metrics else None,
            "error_rates": {
                agent: metrics[-1].to_dict() if metrics else None
                for agent, metrics in self._get_agent_error_rates().items()
            },
            "health_scores": {
                agent: metrics[-1].to_dict() if metrics else None
                for agent, metrics in self.health_scores.items()
            },
            "business": self.business_metrics[-1].to_dict() if self.business_metrics else None,
            "capacity": self.capacity_metrics[-1].to_dict() if self.capacity_metrics else None,
            "active_alerts": len(self.active_alerts),
            "alerts_detail": [
                {"id": aid, "timestamp": timestamp.isoformat()}
                for aid, timestamp in self.active_alerts.items()
            ]
        }
    
    def _get_agent_error_rates(self) -> Dict[str, ErrorRateMetric]:
        """Obtener últimas métricas de error rate por agente"""
        result = {}
        for metric in self.error_rate_metrics:
            if metric.agent_name:
                result[metric.agent_name] = metric
        return result
    
    def get_percentile_metrics(self, 
                             agent_name: Optional[str] = None,
                             operation: Optional[str] = None,
                             time_range: timedelta = timedelta(hours=1)) -> Dict[str, float]:
        """Obtener métricas de percentiles"""
        cutoff_time = datetime.now() - time_range
        
        # Filtrar métricas por rango de tiempo
        recent_latencies = [
            m.latency_ms for m in self.latency_metrics
            if m.timestamp >= cutoff_time and
            (agent_name is None or m.agent_name == agent_name) and
            (operation is None or m.operation == operation)
        ]
        
        if not recent_latencies:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "p99_9": 0.0}
        
        return PercentileCalculator.calculate_all_percentiles(recent_latencies)
    
    def export_prometheus_metrics(self) -> str:
        """Exportar métricas en formato Prometheus"""
        lines = []
        current_time = time.time()
        
        # Métricas de recursos
        if self.resource_metrics:
            latest_resource = self.resource_metrics[-1]
            lines.extend([
                f"# HELP mcp_cpu_usage_percent CPU usage percentage",
                f"# TYPE mcp_cpu_usage_percent gauge",
                f"mcp_cpu_usage_percent {latest_resource.cpu_percent} {current_time}",
                "",
                f"# HELP mcp_memory_usage_percent Memory usage percentage",
                f"# TYPE mcp_memory_usage_percent gauge", 
                f"mcp_memory_usage_percent {latest_resource.memory_percent} {current_time}",
                "",
                f"# HELP mcp_disk_usage_percent Disk usage percentage",
                f"# TYPE mcp_disk_usage_percent gauge",
                f"mcp_disk_usage_percent {latest_resource.disk_percent} {current_time}",
                ""
            ])
        
        # Métricas de throughput
        if self.throughput_metrics:
            latest_throughput = self.throughput_metrics[-1]
            lines.extend([
                f"# HELP mcp_throughput_operations_per_second Current throughput in operations per second",
                f"# TYPE mcp_throughput_operations_per_second gauge",
                f"mcp_throughput_operations_per_second {latest_throughput.requests_per_second} {current_time}",
                ""
            ])
        
        # Métricas de health scores
        for agent, metrics in self.health_scores.items():
            if metrics:
                latest_health = metrics[-1]
                lines.extend([
                    f"# HELP mcp_agent_health_score Agent health score (0-100)",
                    f"# TYPE mcp_agent_health_score gauge",
                    f"mcp_agent_health_score{{agent=\"{agent}\"}} {latest_health.health_score} {current_time}",
                    f"mcp_agent_availability_percent{{agent=\"{agent}\"}} {latest_health.availability_percent} {current_time}",
                    ""
                ])
        
        return "\n".join(lines)
    
    def generate_capacity_report(self, days_ahead: int = 30) -> Dict[str, Any]:
        """Generar reporte de planificación de capacidad"""
        if not self.capacity_metrics:
            return {}
        
        latest_capacity = self.capacity_metrics[-1]
        
        # Obtener datos históricos para tendencias
        cpu_history = self.storage.query_metrics(
            "mcp_cpu_usage_percent",
            datetime.now() - timedelta(days=7),
            datetime.now(),
            aggregation=TimeSeriesAggregation.AVG,
            bucket_size_seconds=3600  # 1 hora
        )
        
        memory_history = self.storage.query_metrics(
            "mcp_memory_usage_percent", 
            datetime.now() - timedelta(days=7),
            datetime.now(),
            aggregation=TimeSeriesAggregation.AVG,
            bucket_size_seconds=3600
        )
        
        return {
            "report_timestamp": datetime.now().isoformat(),
            "current_usage": {
                "cpu_percent": latest_capacity.current_capacity_usage_percent * 0.7,  # Estimación
                "memory_percent": latest_capacity.current_capacity_usage_percent * 0.6,
                "projected_need": latest_capacity.projected_capacity_need
            },
            "recommendations": latest_capacity.scaling_recommendations,
            "bottlenecks": latest_capacity.resource_bottlenecks,
            "optimization_opportunities": latest_capacity.optimization_opportunities,
            "cost_analysis": latest_capacity.cost_analysis,
            "trends": {
                "cpu_history": cpu_history[-24:],  # Últimas 24 horas
                "memory_history": memory_history[-24:],
                "forecast_days": days_ahead
            }
        }
    
    def cleanup_old_data(self, retention_days: int = 30):
        """Limpiar datos antiguos"""
        self.storage.cleanup_old_metrics(retention_days)
        
        # Limpiar colas en memoria
        cutoff_time = datetime.now() - timedelta(days=retention_days)
        
        # Filtrar métricas antiguas
        self.latency_metrics = deque(
            [m for m in self.latency_metrics if m.timestamp >= cutoff_time],
            maxlen=10000
        )
        
        self.throughput_metrics = deque(
            [m for m in self.throughput_metrics if m.timestamp >= cutoff_time],
            maxlen=1000
        )
        
        # etc. para otras colas...


# ==================== INSTANCIA GLOBAL Y FACTORY ====================

_advanced_metrics_collector: Optional[AdvancedMetricsCollector] = None

def get_advanced_metrics_collector(
    collection_interval: int = 10,
    db_path: str = "metrics_timeseries.db"
) -> AdvancedMetricsCollector:
    """Obtener instancia global del recolector avanzado de métricas"""
    global _advanced_metrics_collector
    
    if _advanced_metrics_collector is None:
        storage = TimeSeriesStorage(db_path)
        _advanced_metrics_collector = AdvancedMetricsCollector(collection_interval, storage)
    
    return _advanced_metrics_collector


async def initialize_advanced_metrics(collection_interval: int = 10) -> AdvancedMetricsCollector:
    """Inicializar recolección de métricas avanzadas"""
    collector = get_advanced_metrics_collector(collection_interval)
    await collector.start_collection()
    return collector


# ==================== DASHBOARD EXAMPLES ====================

class GrafanaDashboardConfig:
    """Configuración para dashboards de Grafana"""
    
    @staticmethod
    def generate_dashboard_json() -> Dict[str, Any]:
        """Generar configuración JSON para dashboard de Grafana"""
        return {
            "dashboard": {
                "id": None,
                "title": "MCP Core Superior - Advanced Metrics",
                "tags": ["mcp", "advanced", "metrics"],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "System Resource Utilization",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "mcp_cpu_usage_percent",
                                "refId": "A"
                            },
                            {
                                "expr": "mcp_memory_usage_percent", 
                                "refId": "B"
                            },
                            {
                                "expr": "mcp_disk_usage_percent",
                                "refId": "C"
                            }
                        ],
                        "gridPos": {
                            "h": 8,
                            "w": 12,
                            "x": 0,
                            "y": 0
                        }
                    },
                    {
                        "id": 2,
                        "title": "Agent Health Scores",
                        "type": "graph", 
                        "targets": [
                            {
                                "expr": "mcp_agent_health_score",
                                "refId": "A"
                            }
                        ],
                        "gridPos": {
                            "h": 8,
                            "w": 12,
                            "x": 12,
                            "y": 0
                        }
                    },
                    {
                        "id": 3,
                        "title": "Request Latency Percentiles",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "mcp_latency_milliseconds",
                                "refId": "A"
                            }
                        ],
                        "gridPos": {
                            "h": 8,
                            "w": 24,
                            "x": 0,
                            "y": 8
                        }
                    },
                    {
                        "id": 4,
                        "title": "Throughput",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "mcp_throughput_operations_per_second",
                                "refId": "A"
                            }
                        ],
                        "gridPos": {
                            "h": 8,
                            "w": 12,
                            "x": 0,
                            "y": 16
                        }
                    },
                    {
                        "id": 5,
                        "title": "Active Alerts",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "mcp_active_alerts",
                                "refId": "A"
                            }
                        ],
                        "gridPos": {
                            "h": 4,
                            "w": 12,
                            "x": 12,
                            "y": 16
                        }
                    }
                ],
                "time": {
                    "from": "now-1h",
                    "to": "now"
                },
                "refresh": "5s"
            }
        }


# ==================== EJEMPLO DE USO ====================

if __name__ == "__main__":
    async def demo_advanced_metrics():
        """Demostración del sistema de métricas avanzadas"""
        
        # Inicializar recolector
        collector = AdvancedMetricsCollector(collection_interval=2)
        await collector.start_collection()
        
        print("Advanced Metrics Collector started...")
        
        # Registrar algunas métricas manualmente
        collector.record_latency("reasoner", "analyze", 150.5, "success", method="POST")
        collector.record_latency("executor", "process", 89.3, "success") 
        collector.record_throughput(25.5, concurrent_users=15, active_connections=8)
        
        # Dejar que recolecte métricas
        await asyncio.sleep(10)
        
        # Mostrar métricas actuales
        current = collector.get_current_metrics()
        print("\n=== Current Metrics ===")
        print(json.dumps(current, indent=2, default=str))
        
        # Mostrar percentiles
        percentiles = collector.get_percentile_metrics()
        print("\n=== Latency Percentiles ===")
        print(json.dumps(percentiles, indent=2))
        
        # Exportar métricas para Prometheus
        prometheus_metrics = collector.export_prometheus_metrics()
        print("\n=== Prometheus Metrics ===")
        print(prometheus_metrics)
        
        # Generar reporte de capacidad
        capacity_report = collector.generate_capacity_report()
        print("\n=== Capacity Report ===")
        print(json.dumps(capacity_report, indent=2, default=str))
        
        # Mostrar configuración de dashboard
        dashboard_config = GrafanaDashboardConfig.generate_dashboard_json()
        print("\n=== Grafana Dashboard Config ===")
        print(json.dumps(dashboard_config, indent=2))
        
        await collector.stop_collection()
        print("\nAdvanced Metrics Collector stopped.")
    
    # Ejecutar demostración
    asyncio.run(demo_advanced_metrics())