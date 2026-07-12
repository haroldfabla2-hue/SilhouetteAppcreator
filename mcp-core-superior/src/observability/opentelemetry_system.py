"""
Sistema completo de OpenTelemetry con Distributed Tracing
para MCP Core Superior

Este módulo proporciona tracing distribuido avanzado que incluye:
- Tracing automático de agentes MCP
- Spans para operaciones de base de datos
- Context propagation entre servicios
- Custom spans para workflows complejos
- Exporters configurables (Jaeger, Zipkin, OTLP)
- Sampling strategies
- Trace correlation IDs
- Performance metrics collection
- Error tracking y Exception capturing
- Integration con FastMCP Server
"""

import asyncio
import contextlib
import functools
import logging
import os
import threading
import time
import uuid
import weakref
from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any, Callable, Dict, List, Optional, Union, Generator, Type, TypeVar,
    Awaitable, Set, Tuple
)
from collections import defaultdict, deque
from datetime import datetime, timezone

# OpenTelemetry imports
from opentelemetry import (
    trace, metrics, baggage, context as otel_context
)
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.auto_instrumentation import sitecustomize
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.textmap import (
    TextMapPropagator, HTTPHeaderFormat, HTTPTextFormat
)
from opentelemetry.metrics import MeterProvider, Meter, Counter, Histogram, ObservableGauge
from opentelemetry.sdk.trace import (
    TracerProvider, SamplingDecision, SamplingResult, Sampler
)
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor, SimpleSpanProcessor, ConsoleSpanExporter
)
from opentelemetry.sdk.metrics import MeterProvider as SDKMeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.util.instrumentation import InstrumentationInfo
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.semconv.trace import SpanAttributes

# FastMCP imports
from ..core.config import settings


# Type hints
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])
CoroutineFunc = TypeVar('CoroutineFunc', bound=Callable[..., Awaitable[Any]])


class ExportBackend(str, Enum):
    """Backends de exportación disponibles"""
    JAEGER = "jaeger"
    ZIPKIN = "zipkin"
    OTLP = "otlp"
    CONSOLE = "console"
    ALL = "all"


class SamplingType(str, Enum):
    """Tipos de sampling disponibles"""
    ALWAYS_ON = "always_on"
    ALWAYS_OFF = "always_off"
    RATIO_BASED = "ratio_based"
    ERROR_BASED = "error_based"
    DYNAMIC = "dynamic"


class TraceLevel(str, Enum):
    """Niveles de tracing"""
    NONE = "none"
    BASIC = "basic"
    DETAILED = "detailed"
    VERBOSE = "verbose"


@dataclass
class TraceConfig:
    """Configuración de tracing"""
    enabled: bool = True
    export_backend: ExportBackend = ExportBackend.JAEGER
    sampling_type: SamplingType = SamplingType.RATIO_BASED
    sampling_ratio: float = 0.1
    max_trace_length: int = 100
    correlation_id_header: str = "X-Correlation-ID"
    service_name: str = "mcp-core-superior"
    service_version: str = "1.0.0"
    environment: str = "development"
    trace_level: TraceLevel = TraceLevel.DETAILED
    custom_attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpanData:
    """Datos de un span"""
    name: str
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    status: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Exception] = None


class CorrelationContext:
    """Gestión de correlation IDs y contexto distribuido"""
    
    def __init__(self):
        self._correlation_id_var: ContextVar[str] = ContextVar('correlation_id')
        self._context_data: ContextVar[Dict[str, Any]] = ContextVar('context_data')
    
    def get_correlation_id(self) -> str:
        """Obtener o generar correlation ID"""
        try:
            return self._correlation_id_var.get()
        except LookupError:
            correlation_id = str(uuid.uuid4())
            self._correlation_id_var.set(correlation_id)
            return correlation_id
    
    def set_correlation_id(self, correlation_id: str) -> None:
        """Establecer correlation ID"""
        self._correlation_id_var.set(correlation_id)
    
    def get_context_data(self) -> Dict[str, Any]:
        """Obtener datos del contexto"""
        try:
            return self._context_data.get()
        except LookupError:
            return {}
    
    def set_context_data(self, data: Dict[str, Any]) -> None:
        """Establecer datos del contexto"""
        self._context_data.set(data)
    
    def update_context_data(self, **kwargs) -> None:
        """Actualizar datos del contexto"""
        current_data = self.get_context_data()
        current_data.update(kwargs)
        self.set_context_data(current_data)
    
    def clear_context(self) -> None:
        """Limpiar contexto"""
        try:
            correlation_id = self.get_correlation_id()
            self._correlation_id_var.set(correlation_id)  # Mantener correlation ID
            self._context_data.set({})
        except LookupError:
            pass


class CustomSampler(Sampler):
    """Sampler personalizado con estrategias avanzadas"""
    
    def __init__(self, config: TraceConfig):
        self.config = config
        self.error_spans = 0
        self.total_spans = 0
        self._lock = threading.Lock()
    
    def should_sample(
        self,
        sampling_params: Dict[str, Any],
        **kwargs
    ) -> SamplingResult:
        """Decidir si muestrear basado en parámetros personalizados"""
        with self._lock:
            self.total_spans += 1
        
        # Decisión basada en el tipo de sampling
        if self.config.sampling_type == SamplingType.ALWAYS_ON:
            return SamplingDecision.RECORD_AND_SAMPLE
        
        elif self.config.sampling_type == SamplingType.ALWAYS_OFF:
            return SamplingDecision.DROP
        
        elif self.config.sampling_type == SamplingType.RATIO_BASED:
            # Sampling basado en ratio
            return SamplingDecision.RECORD_AND_SAMPLE if (
                self.total_spans % int(1 / self.config.sampling_ratio) == 0
            ) else SamplingDecision.DROP
        
        elif self.config.sampling_type == SamplingType.ERROR_BASED:
            # Más sampling cuando hay errores
            error_rate = self.error_spans / max(self.total_spans, 1)
            if error_rate > 0.1:  # Si hay > 10% de errores
                return SamplingDecision.RECORD_AND_SAMPLE
            return SamplingDecision.DROP
        
        elif self.config.sampling_type == SamplingType.DYNAMIC:
            # Sampling dinámico basado en contexto
            sampling_params.update(self.config.custom_attributes)
            if sampling_params.get('user_id') in ['admin', 'debug']:
                return SamplingDecision.RECORD_AND_SAMPLE
            return SamplingDecision.DROP
        
        return SamplingDecision.DROP
    
    def get_description(self) -> str:
        """Descripción del sampler"""
        return f"CustomSampler({self.config.sampling_type}, ratio={self.config.sampling_ratio})"


class PerformanceMetrics:
    """Recolección de métricas de performance"""
    
    def __init__(self, meter: Meter):
        self.meter = meter
        
        # Métricas de tracing
        self.span_duration = meter.create_histogram(
            name="mcp.trace.span.duration",
            description="Duration of spans in seconds",
            unit="s"
        )
        
        self.span_count = meter.create_counter(
            name="mcp.trace.span.count",
            description="Number of spans created",
            unit="1"
        )
        
        self.error_count = meter.create_counter(
            name="mcp.trace.errors.count",
            description="Number of errors in spans",
            unit="1"
        )
        
        self.active_traces = meter.create_up_down_counter(
            name="mcp.trace.active.traces",
            description="Number of active traces",
            unit="1"
        )
        
        # Métricas específicas de agentes MCP
        self.agent_execution_time = meter.create_histogram(
            name="mcp.agent.execution.time",
            description="Agent execution time",
            unit="s"
        )
        
        self.agent_success_rate = meter.create_counter(
            name="mcp.agent.success.rate",
            description="Agent execution success rate",
            unit="1"
        )
        
        self.database_operation_duration = meter.create_histogram(
            name="mcp.database.operation.duration",
            description="Database operation duration",
            unit="s"
        )
        
        # Métricas de contexto distribuido
        self.correlation_context_size = meter.create_observable_gauge(
            name="mcp.trace.correlation.context.size",
            description="Size of correlation context",
            unit="1"
        )
    
    def record_span_duration(self, duration: float, span_type: str = "general"):
        """Registrar duración de span"""
        self.span_duration.record(duration, attributes={"span.type": span_type})
    
    def record_span_created(self, span_type: str = "general"):
        """Registrar creación de span"""
        self.span_count.add(1, attributes={"span.type": span_type})
    
    def record_error(self, error_type: str, span_type: str = "general"):
        """Registrar error"""
        self.error_count.add(1, attributes={"error.type": error_type, "span.type": span_type})
    
    def record_agent_execution(self, duration: float, agent_name: str, success: bool):
        """Registrar ejecución de agente"""
        self.agent_execution_time.record(
            duration, 
            attributes={"agent.name": agent_name, "execution.success": success}
        )
        if success:
            self.agent_success_rate.add(1, attributes={"agent.name": agent_name})
    
    def record_database_operation(self, duration: float, operation: str):
        """Registrar operación de base de datos"""
        self.database_operation_duration.record(
            duration, 
            attributes={"db.operation": operation}
        )
    
    def update_correlation_context(self, size: int):
        """Actualizar tamaño del contexto de correlación"""
        # Este es un observable gauge, se actualizará automáticamente


class MCPAgentInstrumentor:
    """Instrumentación automática para agentes MCP"""
    
    def __init__(self, tracer: trace.Tracer, metrics: PerformanceMetrics):
        self.tracer = tracer
        self.metrics = metrics
        self.agent_wrappers: Set[object] = weakref.WeakSet()
    
    def wrap_agent_method(self, agent_instance: Any, method_name: str):
        """Envolver método de agente con tracing automático"""
        original_method = getattr(agent_instance, method_name)
        
        @functools.wraps(original_method)
        def traced_method(*args, **kwargs):
            with self.tracer.start_as_current_span(f"agent.{agent_instance.__class__.__name__}.{method_name}") as span:
                # Atributos básicos del span
                span.set_attribute("agent.class", agent_instance.__class__.__name__)
                span.set_attribute("agent.method", method_name)
                span.set_attribute("agent.module", agent_instance.__class__.__module__)
                
                # Datos del contexto de correlación
                context_data = correlation_context.get_context_data()
                if context_data:
                    span.set_attribute("agent.context", str(context_data))
                
                start_time = time.time()
                
                try:
                    # Ejecutar método original
                    result = original_method(*args, **kwargs)
                    
                    # Registrar éxito
                    duration = time.time() - start_time
                    self.metrics.record_agent_execution(
                        duration, 
                        agent_instance.__class__.__name__,
                        success=True
                    )
                    
                    span.set_attribute("execution.duration", duration)
                    span.set_attribute("execution.status", "success")
                    
                    return result
                    
                except Exception as e:
                    # Registrar error
                    duration = time.time() - start_time
                    self.metrics.record_agent_execution(
                        duration,
                        agent_instance.__class__.__name__,
                        success=False
                    )
                    
                    self.metrics.record_error(e.__class__.__name__)
                    
                    span.set_attribute("execution.duration", duration)
                    span.set_attribute("execution.status", "error")
                    span.set_attribute("error.type", e.__class__.__name__)
                    span.set_attribute("error.message", str(e))
                    
                    raise
        
        # Reemplazar método original
        setattr(agent_instance, method_name, traced_method)
        self.agent_wrappers.add(agent_instance)
    
    def wrap_async_agent_method(self, agent_instance: Any, method_name: str):
        """Envolver método asíncrono de agente con tracing"""
        original_method = getattr(agent_instance, method_name)
        
        @functools.wraps(original_method)
        async def traced_method(*args, **kwargs):
            with self.tracer.start_as_current_span(f"agent.{agent_instance.__class__.__name__}.{method_name}") as span:
                # Atributos básicos del span
                span.set_attribute("agent.class", agent_instance.__class__.__name__)
                span.set_attribute("agent.method", method_name)
                span.set_attribute("agent.module", agent_instance.__class__.__module__)
                
                # Datos del contexto de correlación
                context_data = correlation_context.get_context_data()
                if context_data:
                    span.set_attribute("agent.context", str(context_data))
                
                start_time = time.time()
                
                try:
                    # Ejecutar método original
                    result = await original_method(*args, **kwargs)
                    
                    # Registrar éxito
                    duration = time.time() - start_time
                    self.metrics.record_agent_execution(
                        duration,
                        agent_instance.__class__.__name__,
                        success=True
                    )
                    
                    span.set_attribute("execution.duration", duration)
                    span.set_attribute("execution.status", "success")
                    
                    return result
                    
                except Exception as e:
                    # Registrar error
                    duration = time.time() - start_time
                    self.metrics.record_agent_execution(
                        duration,
                        agent_instance.__class__.__name__,
                        success=False
                    )
                    
                    self.metrics.record_error(e.__class__.__name__)
                    
                    span.set_attribute("execution.duration", duration)
                    span.set_attribute("execution.status", "error")
                    span.set_attribute("error.type", e.__class__.__name__)
                    span.set_attribute("error.message", str(e))
                    
                    raise
        
        # Reemplazar método original
        setattr(agent_instance, method_name, traced_method)
        self.agent_wrappers.add(agent_instance)


class DatabaseInstrumentor:
    """Instrumentación para operaciones de base de datos"""
    
    def __init__(self, tracer: trace.Tracer, metrics: PerformanceMetrics):
        self.tracer = tracer
        self.metrics = metrics
        self.instrumented_engines = set()
    
    def instrument_sqlalchemy(self, engine, custom_attributes: Dict[str, Any] = None):
        """Instrumentar SQLAlchemy engine"""
        SQLAlchemyInstrumentor().instrument(
            engine=engine,
            tracer_provider=trace.get_tracer_provider()
        )
        self.instrumented_engines.add(engine)
    
    def create_db_span(self, operation: str, table: str = None, query: str = None):
        """Crear span para operación de base de datos"""
        span_name = f"db.{operation}"
        if table:
            span_name += f".{table}"
        
        with self.tracer.start_as_current_span(span_name) as span:
            span.set_attribute(SpanAttributes.DB_STATEMENT, query or "")
            span.set_attribute(SpanAttributes.DB_OPERATION, operation)
            if table:
                span.set_attribute(SpanAttributes.DB_NAME, table)
            
            # Atributos adicionales del contexto
            context_data = correlation_context.get_context_data()
            if context_data:
                span.set_attribute("db.context", str(context_data))
    
    @contextlib.contextmanager
    def db_operation_span(
        self, 
        operation: str, 
        table: str = None, 
        query: str = None,
        custom_attributes: Dict[str, Any] = None
    ):
        """Context manager para spans de operaciones de BD"""
        start_time = time.time()
        
        with self.tracer.start_as_current_span(f"db.{operation}") as span:
            span.set_attribute(SpanAttributes.DB_STATEMENT, query or "")
            span.set_attribute(SpanAttributes.DB_OPERATION, operation)
            if table:
                span.set_attribute(SpanAttributes.DB_NAME, table)
            
            if custom_attributes:
                for key, value in custom_attributes.items():
                    span.set_attribute(key, str(value))
            
            # Datos del contexto de correlación
            context_data = correlation_context.get_context_data()
            if context_data:
                span.set_attribute("db.context", str(context_data))
            
            try:
                yield span
            except Exception as e:
                span.set_attribute("error.type", e.__class__.__name__)
                span.set_attribute("error.message", str(e))
                raise
            finally:
                duration = time.time() - start_time
                self.metrics.record_database_operation(duration, operation)


class CustomSpanFactory:
    """Factory para crear spans personalizados para workflows complejos"""
    
    def __init__(self, tracer: trace.Tracer):
        self.tracer = tracer
        self.workflow_spans: Dict[str, trace.Span] = {}
        self.workflow_contexts: Dict[str, Dict[str, Any]] = {}
    
    def create_workflow_span(
        self, 
        workflow_name: str, 
        workflow_id: str = None,
        user_id: str = None,
        **attributes
    ) -> trace.Span:
        """Crear span para workflow complejo"""
        if not workflow_id:
            workflow_id = str(uuid.uuid4())
        
        span_name = f"workflow.{workflow_name}"
        
        with self.tracer.start_as_current_span(span_name) as span:
            span.set_attribute("workflow.name", workflow_name)
            span.set_attribute("workflow.id", workflow_id)
            if user_id:
                span.set_attribute("user.id", user_id)
            
            # Atributos personalizados
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
            
            # Contexto de correlación
            context_data = correlation_context.get_context_data()
            if context_data:
                span.set_attribute("workflow.context", str(context_data))
            
            # Guardar span para tracking
            self.workflow_spans[workflow_id] = span
        
        return span
    
    def create_nested_span(
        self, 
        parent_span: trace.Span,
        name: str,
        **attributes
    ) -> trace.Span:
        """Crear span anidado"""
        with self.tracer.start_as_current_span(name, context=parent_span.get_span_context()) as span:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
            return span
    
    def track_workflow_progress(
        self, 
        workflow_id: str, 
        step: str, 
        status: str = "running",
        **details
    ):
        """Registrar progreso de workflow"""
        if workflow_id in self.workflow_spans:
            span = self.workflow_spans[workflow_id]
            
            # Agregar evento de progreso
            span.add_event(
                name=f"workflow.step.{step}",
                attributes={
                    "workflow.step": step,
                    "workflow.status": status,
                    **{f"workflow.detail.{k}": str(v) for k, v in details.items()}
                }
            )
            
            # Actualizar estado
            span.set_attribute(f"workflow.step.{step}.status", status)
            span.set_attribute(f"workflow.step.{step}.timestamp", str(datetime.now(timezone.utc)))
    
    def complete_workflow(self, workflow_id: str, status: str = "completed", **summary):
        """Marcar workflow como completado"""
        if workflow_id in self.workflow_spans:
            span = self.workflow_spans[workflow_id]
            span.set_attribute("workflow.status", status)
            
            # Agregar resumen
            for key, value in summary.items():
                span.set_attribute(f"workflow.summary.{key}", str(value))
            
            # Finalizar span
            span.end()
            del self.workflow_spans[workflow_id]
    
    def get_workflow_context(self, workflow_id: str) -> Dict[str, Any]:
        """Obtener contexto de workflow"""
        return self.workflow_contexts.get(workflow_id, {})
    
    def set_workflow_context(self, workflow_id: str, context: Dict[str, Any]):
        """Establecer contexto de workflow"""
        self.workflow_contexts[workflow_id] = context


class ErrorTracker:
    """Sistema de tracking y captura de errores"""
    
    def __init__(self, tracer: trace.Tracer, metrics: PerformanceMetrics):
        self.tracer = tracer
        self.metrics = metrics
        self.error_history: deque = deque(maxlen=1000)
        self.error_patterns: defaultdict = defaultdict(int)
        self._lock = threading.Lock()
    
    def record_error(
        self, 
        error: Exception,
        context: Dict[str, Any] = None,
        span: trace.Span = None
    ):
        """Registrar error con contexto completo"""
        with self._lock:
            error_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error_type': error.__class__.__name__,
                'error_message': str(error),
                'traceback': self._get_traceback(error),
                'context': context or {},
                'correlation_id': correlation_context.get_correlation_id()
            }
            
            self.error_history.append(error_data)
            
            # Actualizar patrones de error
            pattern_key = f"{error.__class__.__name__}:{error.__class__.__module__}"
            self.error_patterns[pattern_key] += 1
            
            # Registrar métricas
            self.metrics.record_error(error.__class__.__name__)
        
        # Agregar información al span si existe
        if span:
            span.set_attribute("error.type", error.__class__.__name__)
            span.set_attribute("error.message", str(error))
            span.set_attribute("error.captured", "true")
            span.set_attribute("error.timestamp", error_data['timestamp'])
    
    def _get_traceback(self, error: Exception) -> str:
        """Obtener traceback como string"""
        import traceback
        return ''.join(traceback.format_exception(type(error), error, error.__traceback__))
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas de errores"""
        with self._lock:
            recent_errors = [e for e in self.error_history if e['timestamp'] > 
                           (datetime.now(timezone.utc).isoformat())]
        
        return {
            'total_errors': len(self.error_history),
            'recent_errors': len(recent_errors),
            'error_patterns': dict(self.error_patterns),
            'most_common_error': max(self.error_patterns.items(), 
                                   key=lambda x: x[1])[0] if self.error_patterns else None
        }
    
    def handle_exception(self, func: F) -> F:
        """Decorador para manejo automático de excepciones"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Crear span de error si hay contexto de tracing
                with self.tracer.start_as_current_span(f"error.{func.__name__}") as span:
                    self.record_error(e, {'function': func.__name__}, span)
                    span.set_attribute('error.handler', 'automatic')
                
                # Re-lanzar excepción
                raise
        
        return wrapper
    
    async def handle_async_exception(self, func: CoroutineFunc) -> CoroutineFunc:
        """Decorador para manejo automático de excepciones asíncronas"""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Crear span de error si hay contexto de tracing
                with self.tracer.start_as_current_span(f"error.{func.__name__}") as span:
                    self.record_error(e, {'function': func.__name__}, span)
                    span.set_attribute('error.handler', 'automatic')
                
                # Re-lanzar excepción
                raise
        
        return wrapper


class OpenTelemetrySystem:
    """Sistema principal de OpenTelemetry con distributed tracing"""
    
    def __init__(self, config: TraceConfig = None):
        self.config = config or self._load_default_config()
        self.logger = logging.getLogger(__name__)
        self._initialized = False
        
        # Componentes del sistema
        self.correlation_context = CorrelationContext()
        self.tracer: Optional[trace.Tracer] = None
        self.meter: Optional[Meter] = None
        self.metrics: Optional[PerformanceMetrics] = None
        self.agent_instrumentor: Optional[MCPAgentInstrumentor] = None
        self.db_instrumentor: Optional[DatabaseInstrumentor] = None
        self.span_factory: Optional[CustomSpanFactory] = None
        self.error_tracker: Optional[ErrorTracker] = None
        
        # Exporters configurables
        self.exporters: List[Any] = []
        self._setup_exporters()
        
        # Propagación de contexto
        self._setup_context_propagation()
    
    def _load_default_config(self) -> TraceConfig:
        """Cargar configuración por defecto desde settings"""
        return TraceConfig(
            enabled=settings.tracing_enabled,
            service_name=settings.app_name,
            service_version=settings.app_version,
            environment=settings.environment.value,
            custom_attributes={
                'app.name': settings.app_name,
                'app.version': settings.app_version,
                'environment': settings.environment.value
            }
        )
    
    def _setup_exporters(self):
        """Configurar exporters según backend especificado"""
        if self.config.export_backend == ExportBackend.JAEGER or self.config.export_backend == ExportBackend.ALL:
            self.exporters.append(JaegerExporter(
                agent_host_name="localhost",
                agent_port=6831
            ))
        
        if self.config.export_backend == ExportBackend.ZIPKIN or self.config.export_backend == ExportBackend.ALL:
            self.exporters.append(ZipkinExporter(
                endpoint="http://localhost:9411/api/v2/spans"
            ))
        
        if self.config.export_backend == ExportBackend.OTLP or self.config.export_backend == ExportBackend.ALL:
            self.exporters.append(OTLPSpanExporter(
                endpoint="http://localhost:4317/v1/traces"
            ))
        
        if self.config.export_backend == ExportBackend.CONSOLE:
            self.exporters.append(ConsoleSpanProcessor())
    
    def _setup_context_propagation(self):
        """Configurar propagación de contexto distribuido"""
        set_global_textmap(HTTPHeaderFormat())
    
    def initialize(self):
        """Inicializar sistema completo de OpenTelemetry"""
        if self._initialized:
            return
        
        try:
            # Configurar resource para información del servicio
            resource = Resource.create({
                ResourceAttributes.SERVICE_NAME: self.config.service_name,
                ResourceAttributes.SERVICE_VERSION: self.config.service_version,
                ResourceAttributes.DEPLOYMENT_ENVIRONMENT: self.config.environment,
                **self.config.custom_attributes
            })
            
            # Configurar tracer provider
            tracer_provider = TracerProvider(
                sampler=CustomSampler(self.config),
                resource=resource
            )
            
            # Agregar processors de spans
            for exporter in self.exporters:
                span_processor = BatchSpanProcessor(exporter)
                tracer_provider.add_span_processor(span_processor)
            
            # Configurar global tracer provider
            trace.set_tracer_provider(tracer_provider)
            
            # Configurar meter provider para métricas
            metric_reader = PeriodicExportingMetricReader(
                exporter=OTLPMetricExporter(
                    endpoint="http://localhost:4317/v1/metrics"
                ) if self.config.export_backend == ExportBackend.OTLP else None,
                export_interval_millis=5000
            )
            
            meter_provider = SDKMeterProvider(resource=resource)
            meter_provider.add_metric_reader(metric_reader)
            metrics.set_meter_provider(meter_provider)
            
            # Crear tracer y meter
            self.tracer = trace.get_tracer(
                name=self.config.service_name,
                version=self.config.service_version
            )
            
            self.meter = metrics.get_meter(
                name=self.config.service_name,
                version=self.config.service_version
            )
            
            # Inicializar componentes del sistema
            self.metrics = PerformanceMetrics(self.meter)
            self.agent_instrumentor = MCPAgentInstrumentor(self.tracer, self.metrics)
            self.db_instrumentor = DatabaseInstrumentor(self.tracer, self.metrics)
            self.span_factory = CustomSpanFactory(self.tracer)
            self.error_tracker = ErrorTracker(self.tracer, self.metrics)
            
            # Configurar instrumentación automática
            self._setup_auto_instrumentation()
            
            self._initialized = True
            self.logger.info("OpenTelemetry system initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenTelemetry system: {e}")
            raise
    
    def _setup_auto_instrumentation(self):
        """Configurar instrumentación automática de librerías comunes"""
        try:
            # Instrumentación de requests HTTP
            RequestsInstrumentor().instrument()
            
            # Instrumentación de aiohttp para cliente asíncrono
            AioHttpClientInstrumentor().instrument()
            
            # La instrumentación de FastAPI se hará a través del server
            # La instrumentación de Redis y SQLAlchemy será manual
            
        except Exception as e:
            self.logger.warning(f"Failed to setup some auto instrumentation: {e}")
    
    def instrument_fastmcp_server(self, app):
        """Integrar con FastMCP Server para instrumentación automática"""
        if not self._initialized:
            self.initialize()
        
        try:
            FastAPIInstrumentor.instrument_app(app, tracer_provider=trace.get_tracer_provider())
            self.logger.info("FastMCP Server instrumented successfully")
        except Exception as e:
            self.logger.error(f"Failed to instrument FastMCP Server: {e}")
    
    def instrument_database(self, engine, custom_attributes: Dict[str, Any] = None):
        """Instrumentar operaciones de base de datos"""
        if not self._initialized:
            self.initialize()
        
        self.db_instrumentor.instrument_sqlalchemy(engine, custom_attributes)
    
    def instrument_redis(self, redis_client):
        """Instrumentar operaciones de Redis"""
        if not self._initialized:
            self.initialize()
        
        try:
            RedisInstrumentor().instrument()
            self.logger.info("Redis instrumented successfully")
        except Exception as e:
            self.logger.error(f"Failed to instrument Redis: {e}")
    
    def instrument_agents(self, agent_instances: List[Any]):
        """Instrumentar múltiples agentes MCP automáticamente"""
        if not self._initialized:
            self.initialize()
        
        for agent in agent_instances:
            self.instrument_agent(agent)
    
    def instrument_agent(self, agent_instance: Any):
        """Instrumentar un agente MCP específico"""
        if not self._initialized:
            self.initialize()
        
        # Buscar métodos para instrumentar
        methods_to_wrap = []
        for attr_name in dir(agent_instance):
            attr = getattr(agent_instance, attr_name)
            
            # Solo instrumentar métodos públicos que sean callable
            if (not attr_name.startswith('_') and 
                callable(attr) and 
                hasattr(attr, '__name__')):
                methods_to_wrap.append(attr_name)
        
        # Envolver métodos síncronos y asíncronos
        for method_name in methods_to_wrap:
            try:
                method = getattr(agent_instance, method_name)
                if asyncio.iscoroutinefunction(method):
                    self.agent_instrumentor.wrap_async_agent_method(agent_instance, method_name)
                else:
                    self.agent_instrumentor.wrap_agent_method(agent_instance, method_name)
            except Exception as e:
                self.logger.warning(f"Failed to instrument method {method_name}: {e}")
        
        self.logger.info(f"Agent {agent_instance.__class__.__name__} instrumented successfully")
    
    def create_correlation_id(self) -> str:
        """Crear nuevo correlation ID"""
        correlation_id = str(uuid.uuid4())
        self.correlation_context.set_correlation_id(correlation_id)
        return correlation_id
    
    def get_correlation_id(self) -> str:
        """Obtener correlation ID actual"""
        return self.correlation_context.get_correlation_id()
    
    def set_correlation_id(self, correlation_id: str):
        """Establecer correlation ID específico"""
        self.correlation_context.set_correlation_id(correlation_id)
    
    def get_trace_context_headers(self) -> Dict[str, str]:
        """Obtener headers para propagar contexto de trace"""
        from opentelemetry.propagate import inject
        
        carrier = {}
        inject(carrier)
        return carrier
    
    def propagate_trace_context(self, headers: Dict[str, str]):
        """Propagar contexto de trace desde headers"""
        from opentelemetry.propagate import extract
        
        # Crear contexto desde headers
        extracted_context = extract(headers)
        
        # Ejecutar en contexto propagado
        with otel_context.use(extracted_context):
            yield
    
    def create_workflow_span(
        self, 
        workflow_name: str,
        workflow_id: str = None,
        **attributes
    ) -> trace.Span:
        """Crear span para workflow complejo"""
        if not self._initialized:
            self.initialize()
        
        return self.span_factory.create_workflow_span(
            workflow_name, 
            workflow_id, 
            **attributes
        )
    
    def track_workflow_progress(
        self, 
        workflow_id: str, 
        step: str,
        **details
    ):
        """Registrar progreso de workflow"""
        if not self._initialized:
            self.initialize()
        
        self.span_factory.track_workflow_progress(workflow_id, step, **details)
    
    def complete_workflow(self, workflow_id: str, **summary):
        """Marcar workflow como completado"""
        if not self._initialized:
            self.initialize()
        
        self.span_factory.complete_workflow(workflow_id, **summary)
    
    @contextlib.contextmanager
    def trace_operation(
        self,
        operation_name: str,
        operation_type: str = "general",
        **attributes
    ):
        """Context manager para operations con tracing automático"""
        if not self._initialized:
            self.initialize()
        
        start_time = time.time()
        
        with self.tracer.start_as_current_span(operation_name) as span:
            span.set_attribute("operation.type", operation_type)
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
            
            # Datos del contexto de correlación
            context_data = self.correlation_context.get_context_data()
            if context_data:
                span.set_attribute("operation.context", str(context_data))
            
            try:
                yield span
            except Exception as e:
                if self.error_tracker:
                    self.error_tracker.record_error(e, {'operation': operation_name}, span)
                raise
            finally:
                duration = time.time() - start_time
                if self.metrics:
                    self.metrics.record_span_duration(duration, operation_type)
    
    def get_trace_summary(self) -> Dict[str, Any]:
        """Obtener resumen de trace y métricas"""
        if not self._initialized:
            return {"status": "not_initialized"}
        
        summary = {
            "status": "initialized",
            "config": {
                "export_backend": self.config.export_backend.value,
                "sampling_type": self.config.sampling_type.value,
                "sampling_ratio": self.config.sampling_ratio,
                "service_name": self.config.service_name,
                "environment": self.config.environment
            },
            "instrumentation": {
                "agents_instrumented": len(self.agent_instrumentor.agent_wrappers) if self.agent_instrumentor else 0,
                "databases_instrumented": len(self.db_instrumentor.instrumented_engines) if self.db_instrumentor else 0
            }
        }
        
        if self.error_tracker:
            summary["error_statistics"] = self.error_tracker.get_error_statistics()
        
        return summary


# Instancia global del sistema
otel_system = None


def get_otel_system(config: TraceConfig = None) -> OpenTelemetrySystem:
    """Obtener instancia global del sistema OpenTelemetry"""
    global otel_system
    
    if otel_system is None:
        otel_system = OpenTelemetrySystem(config)
        otel_system.initialize()
    
    return otel_system


def initialize_opentelemetry(config: TraceConfig = None) -> OpenTelemetrySystem:
    """Inicializar sistema completo de OpenTelemetry"""
    global otel_system
    
    otel_system = OpenTelemetrySystem(config)
    otel_system.initialize()
    
    return otel_system


# Decoradores para uso fácil
def trace_function(operation_name: str = None, operation_type: str = "function"):
    """Decorador para rastrear funciones automáticamente"""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with get_otel_system().trace_operation(name, operation_type):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def trace_async_function(operation_name: str = None, operation_type: str = "async_function"):
    """Decorador para rastrear funciones asíncronas automáticamente"""
    def decorator(func: CoroutineFunc) -> CoroutineFunc:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with get_otel_system().trace_operation(name, operation_type):
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Funciones de conveniencia
def create_span(name: str, **attributes) -> trace.Span:
    """Crear span con nombre y atributos"""
    return get_otel_system().tracer.start_as_current_span(name, **attributes)


def add_span_event(event_name: str, **attributes):
    """Agregar evento al span actual"""
    current_span = trace.get_current_span()
    if current_span:
        current_span.add_event(event_name, attributes)


def set_correlation_id(correlation_id: str):
    """Establecer correlation ID"""
    get_otel_system().set_correlation_id(correlation_id)


def get_correlation_id() -> str:
    """Obtener correlation ID actual"""
    return get_otel_system().get_correlation_id()


# Ejemplo de uso completo
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Configuración personalizada
    config = TraceConfig(
        export_backend=ExportBackend.ALL,
        sampling_type=SamplingType.RATIO_BASED,
        sampling_ratio=0.2,
        trace_level=TraceLevel.VERBOSE
    )
    
    # Inicializar sistema
    otel = initialize_opentelemetry(config)
    
    # Ejemplo de uso con FastMCP Server
    # otel.instrument_fastmcp_server(app)
    
    # Ejemplo de instrumentación de base de datos
    # from sqlalchemy import create_engine
    # engine = create_engine("postgresql://...")
    # otel.instrument_database(engine)
    
    # Ejemplo de uso con decoradores
    @trace_function(operation_type="business_logic")
    def business_operation(data: str) -> str:
        """Operación de negocio rastreada"""
        with get_otel_system().trace_operation("process_data", "data_processing"):
            # Simular procesamiento
            time.sleep(0.1)
            return f"Processed: {data}"
    
    # Ejemplo de workflow complejo
    with otel.create_workflow_span("user_registration", user_id="user123") as workflow_span:
        otel.track_workflow_progress(workflow_span.get_span_context().trace_id.hex[:16], "validate_input", status="running")
        
        # Validar datos
        time.sleep(0.05)
        
        otel.track_workflow_progress(workflow_span.get_span_context().trace_id.hex[:16], "save_to_database", status="running")
        
        # Guardar en BD
        with otel.db_instrumentor.db_operation_span("insert", "users", query="INSERT INTO users..."):
            time.sleep(0.1)
        
        otel.track_workflow_progress(workflow_span.get_span_context().trace_id.hex[:16], "send_notification", status="completed")
        
        # Enviar notificación
        time.sleep(0.05)
        
        otel.complete_workflow(workflow_span.get_span_context().trace_id.hex[:16], 
                             status="completed", 
                             steps_completed=3)
    
    # Ejecutar operaciones
    result = business_operation("test data")
    print(f"Result: {result}")
    
    # Obtener resumen
    summary = otel.get_trace_summary()
    print(f"Trace Summary: {summary}")