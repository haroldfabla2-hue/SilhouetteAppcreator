# Monitoring & Observability Guide

## Overview

El MCP Core Superior incluye un sistema completo de observabilidad diseñado para proporcionar visibilidad completa del rendimiento, salud y comportamiento del sistema. Esta guía cubre todos los aspectos del monitoreo desde métricas hasta alertas inteligentes.

## 🏛️ Observability Architecture

### Observability Stack

```
┌─────────────────────────────────────────────────────────┐
│                Application Layer                         │
├─────────────────────────────────────────────────────────┤
│ • Custom Application Metrics                            │
│ • Performance Tracing                                   │
│ • Security Event Logging                                │
│ • Business Logic Instrumentation                        │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│              Collection Layer                            │
├─────────────────────────────────────────────────────────┤
│ • OpenTelemetry Collector                               │
│ • Prometheus Metrics                                    │
│ • Fluentd Log Collection                                │
│ • Jaeger Distributed Tracing                            │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│             Storage Layer                                │
├─────────────────────────────────────────────────────────┤
│ • Prometheus Time-Series DB                             │
│ • Elasticsearch (Logs)                                  │
│ • Jaeger Span Storage                                   │
│ • Grafana Mimir (Metrics)                               │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│             Visualization Layer                          │
├─────────────────────────────────────────────────────────┤
│ • Grafana Dashboards                                    │
│ • Jaeger UI (Tracing)                                   │
│ • Kibana (Logs)                                         │
│ • AlertManager (Alertas)                                │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│             Intelligence Layer                           │
├─────────────────────────────────────────────────────────┤
│ • ML-based Anomaly Detection                            │
│ • Predictive Analytics                                  │
│ • Automated Root Cause Analysis                         │
│ • Intelligent Alerting                                  │
└─────────────────────────────────────────────────────────┘
```

## 📊 Metrics System

### Metrics Configuration

**Prometheus Configuration**
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'mcp-core-superior'
    environment: 'production'

rule_files:
  - "alert_rules.yml"
  - "recording_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  # MCP Core Superior Application
  - job_name: 'mcp-core-superior'
    static_configs:
      - targets: ['mcp-core-superior:9090']
    scrape_interval: 10s
    metrics_path: /metrics
    scrape_timeout: 5s
    
  # PostgreSQL Database
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 30s
    
  # Redis Cache
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
    scrape_interval: 30s
    
  # NGINX Load Balancer
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']
    scrape_interval: 30s
    
  # Node Exporter (System Metrics)
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 30s
    
  # cAdvisor (Container Metrics)
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
    scrape_interval: 30s
```

### Application Metrics Implementation

**Metrics Service**
```python
# src/observability/metrics_service.py
from prometheus_client import (
    Counter, Histogram, Gauge, Summary,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
from typing import Dict, Any, Optional, List
from functools import wraps
import time
import threading
from contextlib import contextmanager

class MCPMetrics:
    """Métricas principales del MCP Core Superior"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        
        # === Request Metrics ===
        self.requests_total = Counter(
            'mcp_core_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'mcp_core_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint'],
            buckets=[0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0],
            registry=self.registry
        )
        
        self.request_size = Summary(
            'mcp_core_request_size_bytes',
            'Request size in bytes',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        self.response_size = Summary(
            'mcp_core_response_size_bytes',
            'Response size in bytes',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        # === Agent Metrics ===
        self.agent_executions_total = Counter(
            'mcp_core_agent_executions_total',
            'Total number of agent executions',
            ['agent_name', 'execution_type', 'status'],
            registry=self.registry
        )
        
        self.agent_execution_duration = Histogram(
            'mcp_core_agent_execution_duration_seconds',
            'Agent execution duration in seconds',
            ['agent_name', 'execution_type'],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0],
            registry=self.registry
        )
        
        self.agent_concurrent_executions = Gauge(
            'mcp_core_agent_concurrent_executions',
            'Number of concurrent agent executions',
            ['agent_name'],
            registry=self.registry
        )
        
        # === Multi-Agent Orchestration Metrics ===
        self.orchestrations_total = Counter(
            'mcp_core_orchestrations_total',
            'Total number of multi-agent orchestrations',
            ['status', 'quality_score_range'],
            registry=self.registry
        )
        
        self.orchestration_duration = Histogram(
            'mcp_core_orchestration_duration_seconds',
            'Multi-agent orchestration duration in seconds',
            ['phase'],
            buckets=[1, 2.5, 5, 10, 25, 50, 100, 250],
            registry=self.registry
        )
        
        self.orchestration_phases = Histogram(
            'mcp_core_orchestration_phase_duration_seconds',
            'Duration of each orchestration phase',
            ['phase', 'agent'],
            buckets=[0.1, 0.5, 1, 2.5, 5, 10, 25],
            registry=self.registry
        )
        
        # === Tool Execution Metrics ===
        self.tool_executions_total = Counter(
            'mcp_core_tool_executions_total',
            'Total number of tool executions',
            ['tool_name', 'status'],
            registry=self.registry
        )
        
        self.tool_execution_duration = Histogram(
            'mcp_core_tool_execution_duration_seconds',
            'Tool execution duration in seconds',
            ['tool_name'],
            buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )
        
        # === Streaming Metrics ===
        self.streaming_connections_total = Counter(
            'mcp_core_streaming_connections_total',
            'Total number of streaming connections',
            ['endpoint'],
            registry=self.registry
        )
        
        self.streaming_messages_total = Counter(
            'mcp_core_streaming_messages_total',
            'Total number of streaming messages',
            ['endpoint', 'message_type'],
            registry=self.registry
        )
        
        self.streaming_connection_duration = Histogram(
            'mcp_core_streaming_connection_duration_seconds',
            'Streaming connection duration in seconds',
            ['endpoint'],
            buckets=[1, 5, 10, 30, 60, 300, 600, 1800],
            registry=self.registry
        )
        
        # === Memory and Resource Metrics ===
        self.memory_usage_bytes = Gauge(
            'mcp_core_memory_usage_bytes',
            'Memory usage in bytes',
            ['component'],
            registry=self.registry
        )
        
        self.database_connections = Gauge(
            'mcp_core_database_connections',
            'Number of active database connections',
            ['database', 'state'],
            registry=self.registry
        )
        
        self.redis_connections = Gauge(
            'mcp_core_redis_connections',
            'Number of Redis connections',
            ['state'],
            registry=self.registry
        )
        
        # === Security Metrics ===
        self.authentication_failures_total = Counter(
            'mcp_core_authentication_failures_total',
            'Total authentication failures',
            ['failure_type'],
            registry=self.registry
        )
        
        self.rate_limit_violations_total = Counter(
            'mcp_core_rate_limit_violations_total',
            'Total rate limit violations',
            ['identifier_type', 'tier'],
            registry=self.registry
        )
        
        self.suspicious_requests_total = Counter(
            'mcp_core_suspicious_requests_total',
            'Total suspicious requests',
            ['threat_type'],
            registry=self.registry
        )
        
        # === Business Metrics ===
        self.active_sessions = Gauge(
            'mcp_core_active_sessions',
            'Number of active user sessions',
            registry=self.registry
        )
        
        self.user_requests_total = Counter(
            'mcp_core_user_requests_total',
            'Total user requests',
            ['user_id', 'endpoint'],
            registry=self.registry
        )
    
    @contextmanager
    def time_agent_execution(self, agent_name: str, execution_type: str):
        """Context manager para medir tiempo de ejecución de agente"""
        start_time = time.time()
        self.agent_concurrent_executions.labels(agent_name=agent_name).inc()
        
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.agent_execution_duration.labels(
                agent_name=agent_name,
                execution_type=execution_type
            ).observe(duration)
            
            self.agent_concurrent_executions.labels(agent_name=agent_name).dec()
    
    @contextmanager
    def time_orchestration_phase(self, phase: str, agent: str = None):
        """Context manager para medir tiempo de fases de orquestación"""
        start_time = time.time()
        
        try:
            yield
        finally:
            duration = time.time() - start_time
            labels = {'phase': phase}
            if agent:
                labels['agent'] = agent
            
            self.orchestration_phases.labels(**labels).observe(duration)
    
    def record_tool_execution(self, tool_name: str, duration: float, status: str):
        """Registrar ejecución de herramienta"""
        self.tool_executions_total.labels(tool_name=tool_name, status=status).inc()
        self.tool_execution_duration.labels(tool_name=tool_name).observe(duration)
    
    def record_authentication_failure(self, failure_type: str):
        """Registrar fallo de autenticación"""
        self.authentication_failures_total.labels(failure_type=failure_type).inc()
    
    def record_rate_limit_violation(self, identifier_type: str, tier: str):
        """Registrar violación de rate limiting"""
        self.rate_limit_violations_total.labels(
            identifier_type=identifier_type,
            tier=tier
        ).inc()

# Instancia global de métricas
metrics = MCPMetrics()

# Decoradores para métricas automáticas
def instrument_endpoint(func):
    """Decorador para instrumentar endpoints automáticamente"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        method = getattr(func, '__method__', 'POST')
        endpoint = getattr(func, '__endpoint__', func.__name__)
        
        try:
            result = await func(*args, **kwargs)
            status_code = getattr(result, 'status_code', 200)
            return result
        except Exception as e:
            status_code = getattr(e, 'status_code', 500)
            raise
        finally:
            duration = time.time() - start_time
            
            metrics.requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            metrics.request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
    
    return wrapper

def track_agent_execution(agent_name: str):
    """Decorador para tracking de agentes"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            with metrics.time_agent_execution(agent_name, func.__name__):
                return await func(*args, **kwargs)
        return wrapper
    return decorator

class MetricsMiddleware:
    """Middleware para colección automática de métricas"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        method = scope['method']
        path = scope['path']
        
        # Generar IDs únicos para request
        request_id = self._generate_request_id()
        scope['request_id'] = request_id
        
        status_code = 200
        
        try:
            await self.app(scope, receive, send)
        except Exception as e:
            status_code = getattr(e, 'status_code', 500)
            raise
        finally:
            duration = time.time() - start_time
            
            # Registrar métricas
            metrics.requests_total.labels(
                method=method,
                endpoint=path,
                status_code=status_code
            ).inc()
            
            metrics.request_duration.labels(
                method=method,
                endpoint=path
            ).observe(duration)
    
    def _generate_request_id(self) -> str:
        """Generar ID único para request"""
        import uuid
        return str(uuid.uuid4())

# Metrics endpoint
async def metrics_handler():
    """Endpoint para exponer métricas a Prometheus"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

### Custom Business Metrics

**Business Metrics Service**
```python
# src/observability/business_metrics.py
from typing import Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

class MetricCategory(Enum):
    """Categorías de métricas de negocio"""
    USER_ENGAGEMENT = "user_engagement"
    AGENT_PERFORMANCE = "agent_performance"
    SYSTEM_HEALTH = "system_health"
    BUSINESS_OUTCOMES = "business_outcomes"

@dataclass
class BusinessMetric:
    """Métrica de negocio"""
    name: str
    value: float
    category: MetricCategory
    timestamp: datetime
    labels: Dict[str, str]
    unit: str = "count"

class BusinessMetricsService:
    """Servicio de métricas de negocio"""
    
    def __init__(self):
        self.metrics_buffer = []
        self.aggregation_window = timedelta(hours=1)
        
        # Configuración de KPIs
        self.kpi_config = {
            'orchestration_success_rate': {
                'target': 0.95,
                'warning': 0.90,
                'critical': 0.85
            },
            'agent_response_time_p95': {
                'target': 2.0,  # seconds
                'warning': 5.0,
                'critical': 10.0
            },
            'user_satisfaction_score': {
                'target': 4.5,
                'warning': 4.0,
                'critical': 3.5
            },
            'system_uptime': {
                'target': 0.999,
                'warning': 0.995,
                'critical': 0.99
            }
        }
    
    def record_user_engagement(
        self, 
        user_id: str, 
        action: str, 
        session_id: str = None,
        metadata: Dict[str, Any] = None
    ):
        """Registrar engagement de usuario"""
        metric = BusinessMetric(
            name="user_engagement",
            value=1.0,
            category=MetricCategory.USER_ENGAGEMENT,
            timestamp=datetime.utcnow(),
            labels={
                'user_id': user_id,
                'action': action,
                'session_id': session_id or 'unknown'
            },
            unit="events"
        )
        
        self._store_metric(metric)
        
        # KPIs específicos
        if action == 'orchestration_completed':
            self._record_orchestration_outcome(user_id, metadata or {})
        elif action == 'user_feedback':
            self._record_user_feedback(user_id, metadata or {})
    
    def record_agent_performance(
        self,
        agent_name: str,
        metric_type: str,
        value: float,
        context: Dict[str, Any] = None
    ):
        """Registrar performance de agente"""
        metric = BusinessMetric(
            name=f"agent_{metric_type}",
            value=value,
            category=MetricCategory.AGENT_PERFORMANCE,
            timestamp=datetime.utcnow(),
            labels={
                'agent_name': agent_name,
                'metric_type': metric_type,
                **({f"context_{k}": str(v) for k, v in (context or {}).items()})
            }
        )
        
        self._store_metric(metric)
    
    def record_system_health(
        self,
        component: str,
        health_status: str,
        response_time: float = None,
        error_rate: float = None
    ):
        """Registrar health del sistema"""
        metric = BusinessMetric(
            name="system_health",
            value=1.0 if health_status == "healthy" else 0.0,
            category=MetricCategory.SYSTEM_HEALTH,
            timestamp=datetime.utcnow(),
            labels={
                'component': component,
                'status': health_status,
                'response_time': str(response_time) if response_time else 'unknown',
                'error_rate': str(error_rate) if error_rate else 'unknown'
            }
        )
        
        self._store_metric(metric)
    
    def calculate_kpis(self, time_window: timedelta = timedelta(hours=24)) -> Dict[str, Any]:
        """Calcular KPIs de negocio"""
        end_time = datetime.utcnow()
        start_time = end_time - time_window
        
        kpis = {}
        
        # Success Rate de orquestaciones
        orchestrations = self._get_metrics_by_name('orchestration_success_rate', start_time, end_time)
        if orchestrations:
            total = len(orchestrations)
            successful = sum(1 for m in orchestrations if m.labels.get('success') == 'true')
            kpis['orchestration_success_rate'] = {
                'value': successful / total if total > 0 else 0,
                'target': self.kpi_config['orchestration_success_rate']['target'],
                'status': self._get_kpi_status(
                    successful / total if total > 0 else 0,
                    'orchestration_success_rate'
                )
            }
        
        # Response Time P95
        response_times = self._get_metrics_by_name('agent_response_time', start_time, end_time)
        if response_times:
            sorted_times = sorted([m.value for m in response_times])
            p95_index = int(len(sorted_times) * 0.95)
            p95 = sorted_times[p95_index] if p95_index < len(sorted_times) else 0
            
            kpis['agent_response_time_p95'] = {
                'value': p95,
                'target': self.kpi_config['agent_response_time_p95']['target'],
                'status': self._get_kpi_status(p95, 'agent_response_time_p95')
            }
        
        # User Satisfaction Score
        feedback_scores = self._get_metrics_by_name('user_feedback_score', start_time, end_time)
        if feedback_scores:
            avg_score = sum(m.value for m in feedback_scores) / len(feedback_scores)
            kpis['user_satisfaction_score'] = {
                'value': avg_score,
                'target': self.kpi_config['user_satisfaction_score']['target'],
                'status': self._get_kpi_status(avg_score, 'user_satisfaction_score')
            }
        
        # System Uptime
        uptime = self._calculate_system_uptime(start_time, end_time)
        kpis['system_uptime'] = {
            'value': uptime,
            'target': self.kpi_config['system_uptime']['target'],
            'status': self._get_kpi_status(uptime, 'system_uptime')
        }
        
        return kpis
    
    def generate_business_report(self, time_window: timedelta = timedelta(days=7)) -> Dict[str, Any]:
        """Generar reporte de negocio"""
        end_time = datetime.utcnow()
        start_time = end_time - time_window
        
        # Recopilar métricas por categoría
        metrics_by_category = {}
        for category in MetricCategory:
            metrics_by_category[category.value] = self._get_metrics_by_category(
                category, start_time, end_time
            )
        
        # Calcular tendencias
        trends = self._calculate_business_trends(start_time, end_time)
        
        # Identificar oportunidades de mejora
        opportunities = self._identify_improvement_opportunities(metrics_by_category)
        
        return {
            'report_period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'duration_days': time_window.days
            },
            'kpis': self.calculate_kpis(time_window),
            'metrics_summary': {
                category: len(metrics) for category, metrics in metrics_by_category.items()
            },
            'trends': trends,
            'opportunities': opportunities,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _record_orchestration_outcome(self, user_id: str, metadata: Dict[str, Any]):
        """Registrar resultado de orquestación"""
        success = metadata.get('success', False)
        
        metric = BusinessMetric(
            name="orchestration_success_rate",
            value=1.0 if success else 0.0,
            category=MetricCategory.BUSINESS_OUTCOMES,
            timestamp=datetime.utcnow(),
            labels={
                'user_id': user_id,
                'success': str(success).lower(),
                'quality_score': str(metadata.get('quality_score', 'unknown'))
            }
        )
        
        self._store_metric(metric)
    
    def _record_user_feedback(self, user_id: str, metadata: Dict[str, Any]):
        """Registrar feedback de usuario"""
        score = metadata.get('score', 0)
        
        metric = BusinessMetric(
            name="user_feedback_score",
            value=score,
            category=MetricCategory.USER_ENGAGEMENT,
            timestamp=datetime.utcnow(),
            labels={
                'user_id': user_id,
                'feedback_type': metadata.get('type', 'general'),
                'rating': str(score)
            }
        )
        
        self._store_metric(metric)
    
    def _get_kpi_status(self, value: float, kpi_name: str) -> str:
        """Obtener status de KPI"""
        if kpi_name not in self.kpi_config:
            return "unknown"
        
        config = self.kpi_config[kpi_name]
        
        if kpi_name == 'orchestration_success_rate' or kpi_name == 'system_uptime' or kpi_name == 'user_satisfaction_score':
            # Para métricas donde mayor es mejor
            if value >= config['target']:
                return "good"
            elif value >= config['warning']:
                return "warning"
            else:
                return "critical"
        else:
            # Para métricas donde menor es mejor
            if value <= config['target']:
                return "good"
            elif value <= config['warning']:
                return "warning"
            else:
                return "critical"
    
    def _calculate_system_uptime(self, start_time: datetime, end_time: datetime) -> float:
        """Calcular uptime del sistema"""
        # TODO: Implementar con datos reales de health checks
        return 0.998  # 99.8% uptime por defecto
    
    def _get_metrics_by_name(
        self, 
        name: str, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[BusinessMetric]:
        """Obtener métricas por nombre"""
        # TODO: Implementar con base de datos
        return []
    
    def _get_metrics_by_category(
        self, 
        category: MetricCategory, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[BusinessMetric]:
        """Obtener métricas por categoría"""
        # TODO: Implementar con base de datos
        return []
    
    def _calculate_business_trends(self, start_time: datetime, end_time: datetime) -> Dict[str, str]:
        """Calcular tendencias de negocio"""
        # TODO: Implementar análisis de tendencias
        return {
            'user_engagement': 'increasing',
            'agent_performance': 'stable',
            'system_health': 'improving',
            'business_outcomes': 'increasing'
        }
    
    def _identify_improvement_opportunities(self, metrics_by_category: Dict[str, List]) -> List[Dict[str, Any]]:
        """Identificar oportunidades de mejora"""
        opportunities = []
        
        # Analizar patrones en las métricas
        # TODO: Implementar análisis de ML para identificar oportunidades
        
        return opportunities
    
    def _store_metric(self, metric: BusinessMetric):
        """Almacenar métrica temporalmente"""
        self.metrics_buffer.append(metric)
        
        # Limpiar buffer si es muy grande
        if len(self.metrics_buffer) > 10000:
            self._flush_metrics_to_storage()
    
    def _flush_metrics_to_storage(self):
        """Enviar métricas al almacenamiento permanente"""
        # TODO: Implementar envío a base de datos
        self.metrics_buffer.clear()

# Instancia global
business_metrics = BusinessMetricsService()
```

### Recording Rules

**Prometheus Recording Rules**
```yaml
# monitoring/recording_rules.yml
groups:
  - name: mcp_core_instantaneous
    interval: 30s
    rules:
      # Success rates
      - record: mcp_core:orchestration_success_rate:5m
        expr: |
          (
            sum(rate(mcp_core_orchestrations_total{status="completed"}[5m])) by (environment)
            /
            sum(rate(mcp_core_orchestrations_total[5m])) by (environment)
          )
      
      - record: mcp_core:agent_success_rate:5m
        expr: |
          (
            sum(rate(mcp_core_agent_executions_total{status="success"}[5m])) by (agent_name)
            /
            sum(rate(mcp_core_agent_executions_total[5m])) by (agent_name)
          )
      
      # Response times
      - record: mcp_core:agent_response_time_p95:5m
        expr: |
          histogram_quantile(
            0.95,
            sum(rate(mcp_core_agent_execution_duration_seconds_bucket[5m])) by (agent_name, le)
          )
      
      - record: mcp_core:orchestration_time_p95:5m
        expr: |
          histogram_quantile(
            0.95,
            sum(rate(mcp_core_orchestration_duration_seconds_bucket[5m])) by (le)
          )
      
      # Throughput metrics
      - record: mcp_core:requests_per_second:1m
        expr: sum(rate(mcp_core_requests_total[1m])) by (endpoint)
      
      - record: mcp_core:tool_executions_per_second:1m
        expr: sum(rate(mcp_core_tool_executions_total[1m])) by (tool_name)
      
      # Resource utilization
      - record: mcp_core:memory_usage_percent
        expr: |
          (
            mcp_core_memory_usage_bytes / 
            on() (node_memory_MemTotal_bytes)
          ) * 100
      
      - record: mcp_core:database_connections_utilization
        expr: |
          (
            mcp_core_database_connections{state="active"} /
            mcp_core_database_connections{state="total"}
          ) * 100

  - name: mcp_core_longterm
    interval: 5m
    rules:
      # 24h aggregations
      - record: mcp_core:total_requests_24h
        expr: sum(increase(mcp_core_requests_total[24h]))
      
      - record: mcp_core:total_orchestrations_24h
        expr: sum(increase(mcp_core_orchestrations_total[24h]))
      
      - record: mcp_core:unique_users_24h
        expr: count(count by (user_id) (mcp_core_user_requests_total[24h]))
      
      # Error rates
      - record: mcp_core:error_rate_24h
        expr: |
          (
            sum(increase(mcp_core_requests_total{status_code=~"5.."}[24h])) by (endpoint)
            /
            sum(increase(mcp_core_requests_total[24h])) by (endpoint)
          ) * 100
      
      # SLI calculations
      - record: mcp_core:availability_sli:30d
        expr: |
          (
            sum(increase(mcp_core_requests_total{status_code!~"5.."}[30d])) by (endpoint)
            /
            sum(increase(mcp_core_requests_total[30d])) by (endpoint)
          ) * 100

  - name: mcp_core_prediction
    interval: 10m
    rules:
      # Predictive alerts
      - record: mcp_core:predicted_memory_usage_1h
        expr: |
          predict_linear(
            mcp_core_memory_usage_percent[5m],
            3600
          )
      
      - record: mcp_core:predicted_requests_per_minute_1h
        expr: |
          predict_linear(
            sum(rate(mcp_core_requests_total[5m]))[5m],
            3600
          ) * 60
```

### Alert Rules

**Alert Rules**
```yaml
# monitoring/alert_rules.yml
groups:
  - name: mcp_core_critical
    rules:
      - alert: MCPServiceDown
        expr: up{job="mcp-core-superior"} == 0
        for: 1m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "MCP Core Superior service is down"
          description: "MCP Core Superior service has been down for more than 1 minute"
      
      - alert: HighErrorRate
        expr: |
          (
            sum(rate(mcp_core_requests_total{status_code=~"5.."}[5m])) by (endpoint)
            /
            sum(rate(mcp_core_requests_total[5m])) by (endpoint)
          ) > 0.05
        for: 2m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "High error rate on {{ $labels.endpoint }}"
          description: "Error rate is {{ $value | humanizePercentage }} for more than 2 minutes"
      
      - alert: DatabaseConnectionsHigh
        expr: mcp_core_database_connections_utilization > 90
        for: 3m
        labels:
          severity: critical
          team: database
        annotations:
          summary: "Database connection utilization is high"
          description: "Database connections utilization is {{ $value }}%"
      
      - alert: MemoryUsageHigh
        expr: mcp_core:memory_usage_percent > 90
        for: 5m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "Memory usage is critically high"
          description: "Memory usage is {{ $value }}%"
      
      - alert: OrchestrationFailureRate
        expr: |
          (
            sum(rate(mcp_core_orchestrations_total{status="failed"}[5m]))
            /
            sum(rate(mcp_core_orchestrations_total[5m]))
          ) > 0.15
        for: 2m
        labels:
          severity: critical
          team: ai
        annotations:
          summary: "High orchestration failure rate"
          description: "Orchestration failure rate is {{ $value | humanizePercentage }}"

  - name: mcp_core_warning
    rules:
      - alert: HighResponseTime
        expr: |
          histogram_quantile(
            0.95,
            sum(rate(mcp_core_request_duration_seconds_bucket[5m])) by (endpoint, le)
          ) > 2
        for: 5m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "High response time on {{ $labels.endpoint }}"
          description: "95th percentile response time is {{ $value }}s"
      
      - alert: AgentPerformanceDegraded
        expr: |
          (
            sum(rate(mcp_core_agent_executions_total{status="success"}[5m])) by (agent_name)
            /
            sum(rate(mcp_core_agent_executions_total[5m])) by (agent_name)
          ) < 0.90
        for: 3m
        labels:
          severity: warning
          team: ai
        annotations:
          summary: "Agent {{ $labels.agent_name }} performance degraded"
          description: "Success rate is {{ $value | humanizePercentage }}"
      
      - alert: RateLimitViolationsHigh
        expr: sum(rate(mcp_core_rate_limit_violations_total[5m])) > 50
        for: 5m
        labels:
          severity: warning
          team: security
        annotations:
          summary: "High rate limit violations"
          description: "{{ $value }} rate limit violations per second"
      
      - alert: StreamingConnectionsHigh
        expr: mcp_core_streaming_connections_total > 1000
        for: 2m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "High number of streaming connections"
          description: "{{ $value }} active streaming connections"

  - name: mcp_core_informational
    rules:
      - alert: CertificateExpiringSoon
        expr: probe_ssl_earliest_cert_expiry - time() < 86400 * 7
        for: 1h
        labels:
          severity: informational
          team: security
        annotations:
          summary: "SSL certificate expiring soon"
          description: "SSL certificate expires in {{ $value | humanizeDuration }}"
      
      - alert: LowUserEngagement
        expr: |
          (
            sum(rate(mcp_core_user_requests_total[1h])) by (user_id)
            < 5
          )
        for: 2h
        labels:
          severity: informational
          team: product
        annotations:
          summary: "Low user engagement detected"
          description: "User {{ $labels.user_id }} has low engagement"
```

## 📝 Structured Logging

### Logging Configuration

**Structured Logging Service**
```python
# src/observability/structured_logging.py
import structlog
import logging
import sys
from typing import Any, Dict, Optional
from datetime import datetime
import json
from pathlib import Path

class StructuredLoggingService:
    """Servicio de logging estructurado"""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.logger = self._setup_structured_logging()
    
    def _setup_structured_logging(self):
        """Configurar logging estructurado con structlog"""
        
        # Procesadores de structlog
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
        ]
        
        # Agregar processor adicional según entorno
        if self.environment == "development":
            processors.append(
                structlog.dev.ConsoleRenderer(colors=True)
            )
        else:
            processors.append(
                structlog.processors.JSONRenderer()
            )
        
        # Configurar structlog
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        # Configurar logging estándar
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=logging.INFO,
        )
        
        return structlog.get_logger()
    
    def get_logger(self, component: str = "mcp_core") -> structlog.BoundLogger:
        """Obtener logger para componente específico"""
        return self.logger.bind(component=component)
    
    def log_request(self, 
                   logger: structlog.BoundLogger,
                   method: str,
                   path: str,
                   status_code: int,
                   duration_ms: float,
                   request_id: str,
                   user_id: Optional[str] = None,
                   user_agent: Optional[str] = None,
                   ip_address: Optional[str] = None,
                   request_size: Optional[int] = None,
                   response_size: Optional[int] = None,
                   **kwargs):
        """Log request HTTP estructurado"""
        logger.info(
            "http_request",
            event="request_completed",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            request_id=request_id,
            user_id=user_id,
            user_agent=user_agent,
            ip_address=ip_address,
            request_size=request_size,
            response_size=response_size,
            timestamp=datetime.utcnow().isoformat(),
            **kwargs
        )
    
    def log_agent_execution(self,
                           logger: structlog.BoundLogger,
                           agent_name: str,
                           execution_type: str,
                           status: str,
                           duration_ms: float,
                           request_id: str,
                           input_data_size: int = None,
                           output_data_size: int = None,
                           error_message: str = None,
                           **kwargs):
        """Log ejecución de agente estructurado"""
        log_data = {
            "event": "agent_execution",
            "agent_name": agent_name,
            "execution_type": execution_type,
            "status": status,
            "duration_ms": duration_ms,
            "request_id": request_id,
            "input_data_size": input_data_size,
            "output_data_size": output_data_size,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        if error_message:
            log_data["error_message"] = error_message
            logger.error("agent_execution_failed", **log_data)
        else:
            logger.info("agent_execution_completed", **log_data)
    
    def log_orchestration(self,
                         logger: structlog.BoundLogger,
                         orchestration_id: str,
                         user_id: str,
                         status: str,
                         phases_completed: int,
                         total_phases: int,
                         total_duration_ms: float,
                         quality_score: float = None,
                         error_details: Dict[str, Any] = None,
                         **kwargs):
        """Log orquestación multi-agente estructurado"""
        log_data = {
            "event": "orchestration",
            "orchestration_id": orchestration_id,
            "user_id": user_id,
            "status": status,
            "phases_completed": phases_completed,
            "total_phases": total_phases,
            "total_duration_ms": total_duration_ms,
            "quality_score": quality_score,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        if error_details:
            log_data["error_details"] = error_details
        
        if status == "completed":
            logger.info("orchestration_completed", **log_data)
        elif status == "failed":
            logger.error("orchestration_failed", **log_data)
        else:
            logger.info("orchestration_in_progress", **log_data)
    
    def log_security_event(self,
                          logger: structlog.BoundLogger,
                          event_type: str,
                          severity: str,
                          user_id: str = None,
                          ip_address: str = None,
                          user_agent: str = None,
                          details: Dict[str, Any] = None,
                          **kwargs):
        """Log evento de seguridad estructurado"""
        log_data = {
            "event": "security",
            "event_type": event_type,
            "severity": severity,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        if details:
            log_data["details"] = details
        
        if severity == "critical":
            logger.critical("security_event_critical", **log_data)
        elif severity == "error":
            logger.error("security_event_error", **log_data)
        elif severity == "warning":
            logger.warning("security_event_warning", **log_data)
        else:
            logger.info("security_event_info", **log_data)
    
    def log_performance_metric(self,
                              logger: structlog.BoundLogger,
                              metric_name: str,
                              value: float,
                              unit: str,
                              component: str,
                              tags: Dict[str, str] = None,
                              **kwargs):
        """Log métrica de performance estructurado"""
        log_data = {
            "event": "performance_metric",
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "component": component,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        if tags:
            log_data["tags"] = tags
        
        logger.info("performance_metric_recorded", **log_data)
    
    def log_business_event(self,
                          logger: structlog.BoundLogger,
                          event_name: str,
                          user_id: str = None,
                          event_category: str = None,
                          properties: Dict[str, Any] = None,
                          **kwargs):
        """Log evento de negocio estructurado"""
        log_data = {
            "event": "business",
            "event_name": event_name,
            "user_id": user_id,
            "event_category": event_category,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        if properties:
            log_data["properties"] = properties
        
        logger.info("business_event", **log_data)

# Instancia global
logging_service = StructuredLoggingService()

def get_logger(component: str = "mcp_core") -> structlog.BoundLogger:
    """Obtener logger para componente"""
    return logging_service.get_logger(component)

# Context manager para logging de request
class RequestContext:
    """Context manager para logging de request con información contextual"""
    
    def __init__(self, logger: structlog.BoundLogger, request_id: str):
        self.logger = logger.bind(request_id=request_id)
        self.request_id = request_id
        self.start_time = datetime.utcnow()
    
    def __enter__(self):
        self.logger.info("request_started", request_id=self.request_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (datetime.utcnow() - self.start_time).total_seconds() * 1000
        
        if exc_type:
            self.logger.error(
                "request_failed",
                request_id=self.request_id,
                duration_ms=duration_ms,
                error_type=exc_type.__name__,
                error_message=str(exc_val)
            )
        else:
            self.logger.info(
                "request_completed",
                request_id=self.request_id,
                duration_ms=duration_ms
            )

def log_request_context(request_id: str, component: str = "mcp_core"):
    """Decorator para logging automático de request"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger = get_logger(component)
            
            with RequestContext(logger, request_id):
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator
```

### Log Processing Pipeline

**Fluentd Configuration**
```yaml
# monitoring/fluentd.conf
<source>
  @type tail
  @id http_access_log
  path /var/log/mcp-core-superior/http-access.log
  pos_file /var/log/fluentd-mcp-core-access.log.pos
  tag mcp_core.http_access
  
  <parse>
    @type json
    time_format %Y-%m-%dT%H:%M:%S.%NZ
  </parse>
</source>

<source>
  @type tail
  @id application_log
  path /var/log/mcp-core-superior/application.log
  pos_file /var/log/fluentd-mcp-core-app.log.pos
  tag mcp_core.application
  
  <parse>
    @type json
    time_format %Y-%m-%dT%H:%M:%S.%NZ
  </parse>
</source>

<source>
  @type tail
  @id security_log
  path /var/log/mcp-core-superior/security.log
  pos_file /var/log/fluentd-mcp-core-security.log.pos
  tag mcp_core.security
  
  <parse>
    @type json
    time_format %Y-%m-%dT%H:%M:%S.%NZ
  </parse>
</source>

<filter mcp_core.**>
  @type record_transformer
  <record>
    hostname "#{Socket.gethostname}"
    environment "#{ENV['ENVIRONMENT'] || 'development'}"
    service_name "mcp-core-superior"
    timestamp "#{Time.now.utc.strftime('%Y-%m-%dT%H:%M:%S.%NZ')}"
  </record>
</filter>

<match mcp_core.security>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name mcp-security-%Y.%m.%d
  type_name _doc
  
  <buffer>
    @type file
    path /var/log/fluentd-buffers/mcp-security.system.buffer
    flush_mode interval
    retry_type exponential_backoff
    flush_thread_count 2
    flush_interval 5s
    retry_forever
    retry_max_interval 30
    chunk_limit_size 2M
    queue_limit_length 8
    overflow_action block
  </buffer>
</match>

<match mcp_core.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name mcp-logs-%Y.%m.%d
  type_name _doc
  
  <buffer>
    @type file
    path /var/log/fluentd-buffers/mcp-logs.system.buffer
    flush_mode interval
    retry_type exponential_backoff
    flush_thread_count 2
    flush_interval 5s
    retry_forever
    retry_max_interval 30
    chunk_limit_size 2M
    queue_limit_length 8
    overflow_action block
  </buffer>
</match>
```

## 🔍 Distributed Tracing

### OpenTelemetry Configuration

**OpenTelemetry Service**
```python
# src/observability/tracing_service.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SqlAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.semconv.trace import SpanAttributes
from typing import Dict, Any, Optional
import time

class TracingService:
    """Servicio de tracing distribuido con OpenTelemetry"""
    
    def __init__(
        self,
        service_name: str = "mcp-core-superior",
        environment: str = "production",
        jaeger_endpoint: str = "http://jaeger-collector:14268/api/traces"
    ):
        self.service_name = service_name
        self.environment = environment
        self.jaeger_endpoint = jaeger_endpoint
        self.tracer = None
        
        self._setup_tracing()
    
    def _setup_tracing(self):
        """Configurar OpenTelemetry tracing"""
        
        # Configurar resource
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: self.service_name,
            ResourceAttributes.SERVICE_VERSION: "2.0.0",
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: self.environment,
            ResourceAttributes.CLOUD_PROVIDER: "generic"
        })
        
        # Crear trace provider
        trace.set_tracer_provider(TracerProvider(resource=resource))
        
        # Configurar Jaeger exporter
        jaeger_exporter = JaegerExporter(
            endpoint=self.jaeger_endpoint,
            agent_host_name="jaeger-agent",
            agent_port=6831,
        )
        
        # Agregar span processor
        span_processor = BatchSpanProcessor(jaeger_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        
        # Crear tracer
        self.tracer = trace.get_tracer(self.service_name)
    
    def get_tracer(self, component: str = None) -> trace.Tracer:
        """Obtener tracer para componente específico"""
        if component:
            return trace.get_tracer(f"{self.service_name}.{component}")
        return self.tracer
    
    def trace_agent_execution(
        self,
        agent_name: str,
        operation: str,
        attributes: Dict[str, Any] = None
    ):
        """Context manager para tracing de ejecución de agente"""
        tracer = self.get_tracer("agents")
        
        class AgentExecutionTracer:
            def __init__(self, agent_name: str, operation: str, attributes: Dict[str, Any]):
                self.agent_name = agent_name
                self.operation = operation
                self.attributes = attributes or {}
                self.span = None
            
            def __enter__(self):
                self.span = tracer.start_span(
                    f"agent.{self.operation}",
                    attributes={
                        SpanAttributes.COMPONENT: "mcp-agent",
                        SpanAttributes.DB_SYSTEM: "postgresql",
                        "agent.name": self.agent_name,
                        "agent.operation": self.operation,
                        **self.attributes
                    }
                )
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.span:
                    if exc_type:
                        self.span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
                    else:
                        self.span.set_status(trace.Status(trace.StatusCode.OK))
                    self.span.end()
        
        return AgentExecutionTracer(agent_name, operation, attributes)
    
    def trace_orchestration_phase(
        self,
        phase: str,
        agent: str = None,
        attributes: Dict[str, Any] = None
    ):
        """Context manager para tracing de fases de orquestación"""
        tracer = self.get_tracer("orchestrator")
        
        class OrchestrationPhaseTracer:
            def __init__(self, phase: str, agent: str, attributes: Dict[str, Any]):
                self.phase = phase
                self.agent = agent
                self.attributes = attributes or {}
                self.span = None
            
            def __enter__(self):
                span_name = f"orchestration.{self.phase}"
                if self.agent:
                    span_name += f".{self.agent}"
                
                self.span = tracer.start_span(
                    span_name,
                    attributes={
                        SpanAttributes.COMPONENT: "orchestration",
                        "orchestration.phase": self.phase,
                        "orchestration.agent": self.agent,
                        **self.attributes
                    }
                )
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.span:
                    if exc_type:
                        self.span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
                    else:
                        self.span.set_status(trace.Status(trace.StatusCode.OK))
                    self.span.end()
        
        return OrchestrationPhaseTracer(phase, agent, attributes)
    
    def trace_tool_execution(
        self,
        tool_name: str,
        parameters: Dict[str, Any] = None,
        attributes: Dict[str, Any] = None
    ):
        """Context manager para tracing de ejecución de herramientas"""
        tracer = self.get_tracer("tools")
        
        class ToolExecutionTracer:
            def __init__(self, tool_name: str, parameters: Dict[str, Any], attributes: Dict[str, Any]):
                self.tool_name = tool_name
                self.parameters = parameters or {}
                self.attributes = attributes or {}
                self.span = None
            
            def __enter__(self):
                self.span = tracer.start_span(
                    f"tool.{self.tool_name}",
                    attributes={
                        SpanAttributes.COMPONENT: "tool",
                        "tool.name": self.tool_name,
                        "tool.parameters": str(self.parameters),
                        **self.attributes
                    }
                )
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.span:
                    if exc_type:
                        self.span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
                    else:
                        self.span.set_status(trace.Status(trace.StatusCode.OK))
                    self.span.end()
        
        return ToolExecutionTracer(tool_name, parameters, attributes)
    
    def trace_database_operation(
        self,
        operation: str,
        table: str = None,
        query: str = None,
        attributes: Dict[str, Any] = None
    ):
        """Context manager para tracing de operaciones de base de datos"""
        tracer = self.get_tracer("database")
        
        class DatabaseOperationTracer:
            def __init__(self, operation: str, table: str, query: str, attributes: Dict[str, Any]):
                self.operation = operation
                self.table = table
                self.query = query
                self.attributes = attributes or {}
                self.span = None
            
            def __enter__(self):
                self.span = tracer.start_span(
                    f"db.{self.operation}",
                    attributes={
                        SpanAttributes.COMPONENT: "database",
                        SpanAttributes.DB_SYSTEM: "postgresql",
                        SpanAttributes.DB_OPERATION: self.operation,
                        SpanAttributes.DB_NAME: self.table,
                        "db.query": self.query,
                        **self.attributes
                    }
                )
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.span:
                    if exc_type:
                        self.span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
                    else:
                        self.span.set_status(trace.Status(trace.StatusCode.OK))
                    self.span.end()
        
        return DatabaseOperationTracer(operation, table, query, attributes)
    
    def trace_external_call(
        self,
        service_name: str,
        operation: str,
        url: str = None,
        method: str = None,
        attributes: Dict[str, Any] = None
    ):
        """Context manager para tracing de llamadas externas"""
        tracer = self.get_tracer("external")
        
        class ExternalCallTracer:
            def __init__(self, service_name: str, operation: str, url: str, method: str, attributes: Dict[str, Any]):
                self.service_name = service_name
                self.operation = operation
                self.url = url
                self.method = method
                self.attributes = attributes or {}
                self.span = None
            
            def __enter__(self):
                self.span = tracer.start_span(
                    f"external.{self.service_name}.{self.operation}",
                    attributes={
                        SpanAttributes.COMPONENT: "http",
                        SpanAttributes.HTTP_METHOD: self.method,
                        SpanAttributes.HTTP_URL: self.url,
                        "external.service": self.service_name,
                        "external.operation": self.operation,
                        **self.attributes
                    }
                )
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.span:
                    if exc_type:
                        self.span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
                    else:
                        self.span.set_status(trace.Status(trace.StatusCode.OK))
                    self.span.end()
        
        return ExternalCallTracer(service_name, operation, url, method, attributes)
    
    def add_custom_attributes(self, attributes: Dict[str, Any]):
        """Agregar atributos personalizados al span actual"""
        current_span = trace.get_current_span()
        if current_span:
            for key, value in attributes.items():
                current_span.set_attribute(key, str(value))

# Instancia global
tracing_service = TracingService()

# Decoradores para tracing automático
def trace_agent(agent_name: str, operation: str):
    """Decorador para tracing automático de agentes"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            with tracing_service.trace_agent_execution(agent_name, operation):
                return await func(*args, **kwargs)
        return wrapper
    return decorator

def trace_orchestration_phase(phase: str):
    """Decorador para tracing automático de fases de orquestación"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            with tracing_service.trace_orchestration_phase(phase):
                return await func(*args, **kwargs)
        return wrapper
    return decorator

def trace_tool(tool_name: str):
    """Decorador para tracing automático de herramientas"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            with tracing_service.trace_tool_execution(tool_name):
                return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### Auto-instrumentation Setup

**Auto-instrumentation Configuration**
```python
# src/observability/auto_instrumentation.py
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SqlAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
import logging

class AutoInstrumentation:
    """Configuración de auto-instrumentación para observabilidad"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self._instrumented = False
    
    def setup_instrumentation(self):
        """Configurar toda la auto-instrumentación"""
        if self._instrumented:
            return
        
        # Instrumentar FastAPI
        FastAPIInstrumentor.instrument_app(
            self.app,
            excluded_urls=[
                "/health",
                "/metrics",
                "/favicon.ico"
            ]
        )
        
        # Configurar logging de instrumentación
        logging.getLogger("opentelemetry").setLevel(logging.INFO)
        
        self._instrumented = True
    
    def instrument_database(self, engine):
        """Instrumentar SQLAlchemy"""
        SqlAlchemyInstrumentor.instrument(engine=engine)
    
    def instrument_redis(self, redis_client):
        """Instrumentar Redis"""
        RedisInstrumentor.instrument()
    
    def instrument_http_clients(self):
        """Instrumentar clientes HTTP"""
        AioHttpClientInstrumentor().instrument()
        HTTPXClientInstrumentor().instrument()
    
    def instrument_celery(self, celery_app):
        """Instrumentar Celery"""
        from opentelemetry.instrumentation.celery import CeleryInstrumentor
        CeleryInstrumentor().instrument(celery_app=celery_app)

# Configuración en main.py
def setup_observability(app: FastAPI, config: Dict[str, Any]):
    """Configurar toda la observabilidad en la aplicación"""
    
    # Auto-instrumentación
    auto_instrumentation = AutoInstrumentation(app)
    auto_instrumentation.setup_instrumentation()
    
    # Instrumentar servicios específicos
    if config.get('database_engine'):
        auto_instrumentation.instrument_database(config['database_engine'])
    
    if config.get('redis_client'):
        auto_instrumentation.instrument_redis(config['redis_client'])
    
    auto_instrumentation.instrument_http_clients()
    
    if config.get('celery_app'):
        auto_instrumentation.instrument_celery(config['celery_app'])
    
    return auto_instrumentation
```

## 📊 Grafana Dashboards

### Main Dashboard Configuration

**Grafana Dashboard JSON**
```json
{
  "dashboard": {
    "id": null,
    "title": "MCP Core Superior - Overview",
    "description": "Main dashboard for MCP Core Superior monitoring",
    "tags": ["mcp", "ai", "orchestration", "monitoring"],
    "timezone": "UTC",
    "refresh": "30s",
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "panels": [
      {
        "id": 1,
        "title": "System Health",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"mcp-core-superior\"}",
            "legendFormat": "Service Status"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "mappings": [
              {
                "options": {
                  "0": {"text": "DOWN", "color": "red"},
                  "1": {"text": "UP", "color": "green"}
                },
                "type": "value"
              }
            ],
            "color": {"mode": "thresholds"},
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "green", "value": 1}
              ]
            }
          }
        },
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Requests Per Second",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(mcp_core_requests_total[1m]))",
            "legendFormat": "Total RPS"
          },
          {
            "expr": "sum(rate(mcp_core_requests_total{status_code=~\"2..\"}[1m]))",
            "legendFormat": "Success RPS"
          },
          {
            "expr": "sum(rate(mcp_core_requests_total{status_code=~\"4..|5..\"}[1m]))",
            "legendFormat": "Error RPS"
          }
        ],
        "yAxes": [
          {"label": "Requests/sec", "min": 0}
        ],
        "gridPos": {"h": 8, "w": 12, "x": 6, "y": 0}
      },
      {
        "id": 3,
        "title": "Response Time (P95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(mcp_core_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "P95 Response Time"
          },
          {
            "expr": "histogram_quantile(0.50, sum(rate(mcp_core_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "P50 Response Time"
          }
        ],
        "yAxes": [
          {"label": "Seconds", "min": 0}
        ],
        "gridPos": {"h": 8, "w": 12, "x": 18, "y": 0}
      },
      {
        "id": 4,
        "title": "Agent Executions",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(mcp_core_agent_executions_total[5m])) by (agent_name)",
            "legendFormat": "{{agent_name}}"
          }
        ],
        "yAxes": [
          {"label": "Executions/sec", "min": 0}
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
      },
      {
        "id": 5,
        "title": "Orchestration Success Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "(\n  sum(rate(mcp_core_orchestrations_total{status=\"completed\"}[5m]))\n  /\n  sum(rate(mcp_core_orchestrations_total[5m]))\n) * 100",
            "legendFormat": "Success Rate"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "max": 100,
            "min": 0,
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 85},
                {"color": "green", "value": 95}
              ]
            }
          }
        },
        "gridPos": {"h": 4, "w": 6, "x": 12, "y": 8}
      },
      {
        "id": 6,
        "title": "Active Streaming Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "mcp_core_streaming_connections_total",
            "legendFormat": "Active Connections"
          }
        ],
        "yAxes": [
          {"label": "Connections", "min": 0}
        ],
        "gridPos": {"h": 4, "w": 6, "x": 18, "y": 8}
      },
      {
        "id": 7,
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "mcp_core:memory_usage_percent",
            "legendFormat": "Memory Usage %"
          }
        ],
        "yAxes": [
          {"label": "Percentage", "min": 0, "max": 100}
        ],
        "gridPos": {"h": 6, "w": 24, "x": 0, "y": 16}
      }
    ],
    "templating": {
      "list": [
        {
          "name": "environment",
          "type": "custom",
          "options": [
            {"text": "production", "value": "production", "selected": false},
            {"text": "staging", "value": "staging", "selected": false},
            {"text": "development", "value": "development", "selected": true}
          ]
        }
      ]
    },
    "annotations": {
      "list": [
        {
          "name": "Deployments",
          "datasource": "prometheus",
          "enable": true,
          "expr": "changes(process_start_time_seconds[1m]) > 0",
          "titleFormat": "Deployment",
          "textFormat": "Service was redeployed",
          "iconColor": "blue"
        }
      ]
    }
  }
}
```

### Alert Dashboard

**Alert Management Dashboard**
```json
{
  "dashboard": {
    "id": null,
    "title": "MCP Core Superior - Alerts",
    "description": "Alert management and overview dashboard",
    "tags": ["mcp", "alerts", "monitoring"],
    "timezone": "UTC",
    "refresh": "30s",
    "panels": [
      {
        "id": 1,
        "title": "Active Alerts",
        "type": "table",
        "targets": [
          {
            "expr": "ALERTS{alertstate=\"firing\"}",
            "format": "table"
          }
        ],
        "gridPos": {"h": 12, "w": 24, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Alert History (Last 24h)",
        "type": "graph",
        "targets": [
          {
            "expr": "changes(ALERTS{alertstate=\"firing\"}[1m])",
            "legendFormat": "Alert Changes"
          }
        ],
        "yAxes": [{"min": 0}],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 12}
      },
      {
        "id": 3,
        "title": "MTTR (Mean Time To Resolve)",
        "type": "stat",
        "targets": [
          {
            "expr": "avg_over_time(ALERTS_DURATION[24h])",
            "legendFormat": "MTTR"
          }
        ],
        "gridPos": {"h": 4, "w": 6, "x": 12, "y": 12}
      },
      {
        "id": 4,
        "title": "Alert Frequency by Severity",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum(increase(ALERTS{alertstate=\"firing\"}[24h])) by (severity)",
            "legendFormat": "{{severity}}"
          }
        ],
        "gridPos": {"h": 8, "w": 6, "x": 18, "y": 12}
      }
    ]
  }
}
```

## 🚨 Alerting System

### AlertManager Configuration

**AlertManager Configuration**
```yaml
# monitoring/alertmanager.yml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@mcp-core-superior.com'
  smtp_auth_username: 'alerts@mcp-core-superior.com'
  smtp_auth_password: '${SMTP_PASSWORD}'
  slack_api_url: '${SLACK_WEBHOOK_URL}'
  
route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default'
  routes:
    # Critical alerts - immediate notification
    - match:
        severity: critical
      receiver: 'critical-alerts'
      group_wait: 0s
      repeat_interval: 5m
    
    # Security alerts - immediate notification
    - match:
        team: security
      receiver: 'security-alerts'
      group_wait: 0s
      repeat_interval: 2m
    
    # Performance alerts - warnings
    - match:
        severity: warning
      receiver: 'warning-alerts'
      repeat_interval: 15m

receivers:
  - name: 'default'
    email_configs:
      - to: 'team@mcp-core-superior.com'
        subject: 'MCP Core Superior Alert: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Labels: {{ range .Labels.SortedPairs }} - {{ .Name }}: {{ .Value }}{{ end }}
          {{ end }}

  - name: 'critical-alerts'
    email_configs:
      - to: 'oncall@mcp-core-superior.com'
        subject: '🚨 CRITICAL: MCP Core Superior Alert'
        body: |
          🚨 CRITICAL ALERT 🚨
          
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Severity: {{ .Labels.severity }}
          {{ if .Labels.instance }}Instance: {{ .Labels.instance }}{{ end }}
          {{ if .Labels.description }}Details: {{ .Labels.description }}{{ end }}
          
          Runbook: {{ .Annotations.runbook_url }}
          {{ end }}
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#alerts-critical'
        title: '🚨 Critical Alert - MCP Core Superior'
        text: |
          {{ range .Alerts }}
          *Alert*: {{ .Annotations.summary }}
          *Description*: {{ .Annotations.description }}
          *Severity*: {{ .Labels.severity }}
          {{ if .Labels.instance }}*Instance*: {{ .Labels.instance }}{{ end }}
          {{ end }}
    pagerduty_configs:
      - routing_key: '${PAGERDUTY_INTEGRATION_KEY}'
        description: 'Critical MCP Core Superior alert'
        severity: 'critical'

  - name: 'security-alerts'
    email_configs:
      - to: 'security@mcp-core-superior.com'
        subject: '🔒 Security Alert: MCP Core Superior'
        body: |
          🔒 SECURITY ALERT 🔒
          
          {{ range .Alerts }}
          Event Type: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Severity: {{ .Labels.severity }}
          {{ if .Labels.ip_address }}IP Address: {{ .Labels.ip_address }}{{ end }}
          {{ if .Labels.user_id }}User ID: {{ .Labels.user_id }}{{ end }}
          {{ end }}
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#security-alerts'
        title: '🔒 Security Alert - MCP Core Superior'
        text: |
          {{ range .Alerts }}
          *Event*: {{ .Annotations.summary }}
          *Description*: {{ .Annotations.description }}
          *Severity*: {{ .Labels.severity }}
          {{ if .Labels.ip_address }}*IP*: {{ .Labels.ip_address }}{{ end }}
          {{ end }}

  - name: 'warning-alerts'
    email_configs:
      - to: 'team@mcp-core-superior.com'
        subject: '⚠️ Warning: MCP Core Superior Alert'
        body: |
          ⚠️ WARNING ⚠️
          
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          {{ end }}

inhibit_rules:
  # Inhibit warning alerts if critical alert is firing
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'cluster', 'instance']
  
  # Inhibit all alerts if service is down
  - source_match:
      alertname: 'MCPServiceDown'
    target_match_re:
      alertname: '.*'
    equal: ['instance']
```

### Alert Notification Templates

**Alert Templates**
```go
{{ define "email.subject" -}}
{{ if eq .GroupLabels.severity "critical" }}🚨 CRITICAL: {{ .GroupLabels.alertname }}{{ end }}
{{ if eq .GroupLabels.severity "warning" }}⚠️ WARNING: {{ .GroupLabels.alertname }}{{ end }}
{{ if eq .GroupLabels.severity "info" }}ℹ️ INFO: {{ .GroupLabels.alertname }}{{ end }}
- {{ .GroupLabels.cluster }}
{{- end }}

{{ define "email.default.text" -}}
{{ range .Alerts }}
Alert: {{ .Annotations.summary }}
Description: {{ .Annotations.description }}
Labels:
{{ range .Labels.SortedPairs }} - {{ .Name }}: {{ .Value }}{{ end }}

{{ if .Annotations.runbook_url }}Runbook: {{ .Annotations.runbook_url }}{{ end }}
{{ if .Annotations.dashboard_url }}Dashboard: {{ .Annotations.dashboard_url }}{{ end }}
{{ if .Annotations.doc_url }}Documentation: {{ .Annotations.doc_url }}{{ end }}

Fired at: {{ .StartsAt }}
{{ end }}
{{- end }}

{{ define "slack.default.text" -}}
{{ range .Alerts }}
*Alert*: {{ .Annotations.summary }}
*Description*: {{ .Annotations.description }}
*Severity*: {{ .Labels.severity }}
{{ if .Labels.instance }}*Instance*: {{ .Labels.instance }}{{ end }}
{{ if .Labels.job }}*Job*: {{ .Labels.job }}{{ end }}
{{ if .Labels.instance }}*Instance*: {{ .Labels.instance }}{{ end }}

{{ if .Annotations.runbook_url }}*Runbook*: {{ .Annotations.runbook_url }}{{ end }}
{{ if .Annotations.dashboard_url }}*Dashboard*: {{ .Annotations.dashboard_url }}{{ end }}

Fired: {{ .StartsAt.Format "15:04 MST" }}
{{ end }}
{{- end }}

{{ define "pagerduty.default" -}}
{
  "routing_key": "{{ .RoutingKey }}",
  "event_action": "trigger",
  "dedup_key": "{{ .GroupLabels.alertname }}-{{ .GroupLabels.instance }}",
  "payload": {
    "summary": "{{ .GroupLabels.alertname }}: {{ .CommonAnnotations.summary }}",
    "severity": "{{ .GroupLabels.severity }}",
    "source": "{{ .GroupLabels.instance }}",
    "component": "mcp-core-superior",
    "group": "{{ .GroupLabels.cluster }}",
    "class": "application",
    "custom_details": {
      {{ range .Alerts }}
      "alert_description": "{{ .Annotations.description }}",
      "alert_labels": {{ .Labels | toJson }},
      {{ end }}
    }
  }
}
{{- end }}
```

---

## 🔧 Implementation Guide

### Complete Monitoring Setup

**monitoring_setup.py**
```python
# src/observability/monitoring_setup.py
from fastapi import FastAPI
from typing import Dict, Any
import logging

def setup_monitoring(app: FastAPI, config: Dict[str, Any]):
    """Configurar monitoreo completo para la aplicación"""
    
    # 1. Configurar métricas
    from .metrics_service import MCPMetrics, MetricsMiddleware
    metrics = MCPMetrics()
    
    # Agregar middleware de métricas
    app.add_middleware(MetricsMiddleware)
    
    # Endpoint de métricas
    @app.get("/metrics")
    async def metrics_endpoint():
        from prometheus_client import generate_latest
        return generate_latest()
    
    # 2. Configurar logging estructurado
    from .structured_logging import StructuredLoggingService
    logging_service = StructuredLoggingService(config.get('environment', 'development'))
    
    # 3. Configurar tracing
    from .tracing_service import TracingService
    tracing_service = TracingService(
        service_name=config.get('service_name', 'mcp-core-superior'),
        environment=config.get('environment', 'production'),
        jaeger_endpoint=config.get('jaeger_endpoint', 'http://jaeger-collector:14268/api/traces')
    )
    
    # 4. Configurar auto-instrumentación
    from .auto_instrumentation import AutoInstrumentation
    auto_instrumentation = AutoInstrumentation(app)
    auto_instrumentation.setup_instrumentation()
    
    # 5. Configurar métricas de negocio
    from .business_metrics import BusinessMetricsService
    business_metrics = BusinessMetricsService()
    
    return {
        'metrics': metrics,
        'logging_service': logging_service,
        'tracing_service': tracing_service,
        'auto_instrumentation': auto_instrumentation,
        'business_metrics': business_metrics
    }

# Context managers para uso en la aplicación
from .metrics_service import metrics
from .structured_logging import get_logger, log_request_context
from .tracing_service import tracing_service
from .business_metrics import business_metrics

# Usage examples
@app.post("/mcp-tools/analyze_intent")
@log_request_context("request_id_123", "reasoner_agent")
@trace_agent("reasoner_agent", "analyze_intent")
async def analyze_intent(request: AnalyzeIntentRequest):
    """Endpoint de análisis de intención con monitoreo completo"""
    logger = get_logger("reasoner_agent")
    
    # Logging contextual
    logger.info(
        "starting_intent_analysis",
        objective=request.objective,
        conversation_id=request.conversation_id
    )
    
    # Tracing
    with tracing_service.trace_agent_execution("reasoner_agent", "analyze_intent"):
        # Métricas automáticas via decorators
        
        # Búsqueda de contexto (con tracing)
        with tracing_service.trace_database_operation(
            operation="SELECT",
            table="conversation_contexts",
            query="SELECT * FROM contexts WHERE conversation_id = ?"
        ):
            context = await get_conversation_context(request.conversation_id)
        
        # Lógica de análisis
        result = await reasoner_agent.analyze_intent(request.objective, context)
        
        # Métricas de negocio
        business_metrics.record_agent_performance(
            agent_name="reasoner_agent",
            metric_type="execution_time",
            value=result.processing_time,
            context={"objective_type": result.objective_type}
        )
        
        # Logging de resultado
        logger.info(
            "intent_analysis_completed",
            intent=result.primary_intent,
            confidence=result.confidence_score
        )
        
        return result
```

---

## 📋 Monitoring Checklist

### Pre-Production Monitoring Checklist

#### Metrics Collection
- [ ] Prometheus configurado con scraping intervals apropiados
- [ ] Métricas de aplicación instrumentadas
- [ ] Recording rules configuradas
- [ ] Alertas thresholds definidos y probados

#### Logging
- [ ] Structured logging configurado
- [ ] Log levels apropiados por ambiente
- [ ] Log retention policies implementadas
- [ ] Log aggregation funcionando

#### Tracing
- [ ] OpenTelemetry configurado
- [ ] Service mapping correcto
- [ ] Spans instrumentados en puntos críticos
- [ ] Sampling strategy definida

#### Dashboards
- [ ] Main dashboard completo y funcional
- [ ] Alert dashboard configurado
- [ ] Business metrics dashboard creado
- [ ] Panel permissions apropiadas

#### Alerting
- [ ] AlertManager configurado
- [ ] Notification channels configurados
- [ ] Alert templates personalizados
- [ ] Escalation policies definidas

#### Security Monitoring
- [ ] Security event logging habilitado
- [ ] Anomaly detection configurado
- [ ] Audit logging implementado
- [ ] Compliance metrics tracking

---

**Próximos pasos**: Después de configurar el monitoreo, revisar [Troubleshooting Guide](../troubleshooting/common-issues.md) para técnicas de diagnóstico.