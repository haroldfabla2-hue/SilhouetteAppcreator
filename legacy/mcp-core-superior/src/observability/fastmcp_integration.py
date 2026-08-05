"""
Integración específica con FastMCP Server para OpenTelemetry

Este módulo proporciona integración directa con el servidor FastMCP
para instrumentación automática de todas las operaciones MCP.
"""

import asyncio
import functools
import logging
import time
from typing import Any, Dict, List, Optional, Callable, Union

from fastapi import FastAPI, Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestHandlerEndpoint
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from .opentelemetry_system import (
    get_otel_system, 
    trace_function, 
    trace_async_function,
    create_span,
    add_span_event,
    set_correlation_id,
    get_correlation_id
)
from ..core.fastmcp_local import FastMCP


class MCPMiddleware(BaseHTTPMiddleware):
    """Middleware de OpenTelemetry para FastMCP Server"""
    
    def __init__(self, app: ASGIApp, include_paths: List[str] = None, exclude_paths: List[str] = None):
        super().__init__(app)
        self.include_paths = include_paths or ["/mcp/", "/tools/", "/agents/"]
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/docs", "/openapi.json"]
        self.logger = logging.getLogger(__name__)
    
    async def dispatch(self, request: Request, call_next: RequestHandlerEndpoint) -> Response:
        """Procesar request con tracing"""
        # Verificar si debemos instrumentar esta ruta
        path = request.url.path
        if not self._should_instrument(path):
            return await call_next(request)
        
        # Extraer información del request
        method = request.method
        correlation_id = request.headers.get("X-Correlation-ID") or self._generate_correlation_id()
        
        # Establecer correlation ID en contexto
        set_correlation_id(correlation_id)
        
        # Crear span para la request HTTP
        with get_otel_system().trace_operation(f"http.{method.lower()}.{path}", "http_request") as span:
            # Atributos del span HTTP
            span.set_attribute("http.method", method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.path", path)
            span.set_attribute("http.scheme", request.url.scheme)
            span.set_attribute("http.host", request.url.hostname)
            span.set_attribute("http.user_agent", request.headers.get("user-agent", ""))
            
            # Headers de correlación
            span.set_attribute("correlation.id", correlation_id)
            
            # Query parameters
            query_params = dict(request.query_params)
            if query_params:
                span.set_attribute("http.query_params", str(query_params))
            
            # Headers (excluyendo sensibles)
            headers = {k: v for k, v in request.headers.items() 
                      if k.lower() not in ['authorization', 'cookie']}
            if headers:
                span.set_attribute("http.headers", str(headers))
            
            try:
                # Procesar request
                start_time = time.time()
                response = await call_next(request)
                duration = time.time() - start_time
                
                # Atributos de respuesta
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("http.response_size", len(response.body) if hasattr(response, 'body') else 0)
                span.set_attribute("response.duration", duration)
                span.set_attribute("response.status", "success")
                
                # Headers de respuesta
                response_headers = dict(response.headers)
                if "X-Correlation-ID" not in response_headers:
                    response.headers["X-Correlation-ID"] = correlation_id
                
                return response
                
            except Exception as e:
                # Registrar error
                span.set_attribute("response.status", "error")
                span.set_attribute("error.type", e.__class__.__name__)
                span.set_attribute("error.message", str(e))
                span.set_attribute("error.captured", "true")
                
                # Agregar evento de error
                add_span_event("http_request.error", 
                             error_type=e.__class__.__name__,
                             error_message=str(e))
                
                # Re-lanzar excepción
                raise
    
    def _should_instrument(self, path: str) -> bool:
        """Determinar si debemos instrumentar esta ruta"""
        # Verificar exclusiones primero
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return False
        
        # Verificar inclusiones
        for include_path in self.include_paths:
            if path.startswith(include_path):
                return True
        
        return False
    
    def _generate_correlation_id(self) -> str:
        """Generar correlation ID"""
        import uuid
        return str(uuid.uuid4())


class MCPEndpointInstrumentor:
    """Instrumentor para endpoints específicos de MCP"""
    
    def __init__(self, otel_system=None):
        self.otel_system = otel_system or get_otel_system()
        self.logger = logging.getLogger(__name__)
    
    def instrument_mcp_endpoint(self, endpoint_func: Callable):
        """Instrumentar endpoint MCP con tracing automático"""
        @functools.wraps(endpoint_func)
        async def async_wrapper(*args, **kwargs):
            # Extraer request si es el primer argumento
            request = None
            if args and hasattr(args[0], 'method'):
                request = args[0]
            
            endpoint_name = f"mcp.endpoint.{endpoint_func.__name__}"
            
            with self.otel_system.trace_operation(endpoint_name, "mcp_endpoint") as span:
                span.set_attribute("endpoint.name", endpoint_func.__name__)
                span.set_attribute("endpoint.module", endpoint_func.__module__)
                
                if request:
                    span.set_attribute("request.correlation_id", get_correlation_id())
                    span.set_attribute("request.method", request.method)
                    span.set_attribute("request.path", str(request.url.path))
                
                try:
                    # Agregar evento de inicio
                    add_span_event("mcp.endpoint.started", endpoint=endpoint_func.__name__)
                    
                    # Ejecutar endpoint
                    result = await endpoint_func(*args, **kwargs)
                    
                    # Agregar evento de finalización exitosa
                    add_span_event("mcp.endpoint.completed", endpoint=endpoint_func.__name__)
                    
                    return result
                    
                except Exception as e:
                    # Registrar error
                    add_span_event("mcp.endpoint.failed", 
                                 endpoint=endpoint_func.__name__,
                                 error_type=e.__class__.__name__,
                                 error_message=str(e))
                    
                    raise
        
        return async_wrapper
    
    def instrument_tool_call(self, tool_name: str):
        """Decorador para instrumentar llamadas a herramientas MCP"""
        def decorator(func: Callable):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                span_name = f"mcp.tool.{tool_name}"
                
                with create_span(span_name) as span:
                    span.set_attribute("tool.name", tool_name)
                    span.set_attribute("tool.func", func.__name__)
                    span.set_attribute("tool.module", func.__module__)
                    span.set_attribute("correlation.id", get_correlation_id())
                    
                    # Parámetros de la herramienta
                    if len(args) > 1:
                        span.set_attribute("tool.args", str(args[1:]))
                    if kwargs:
                        span.set_attribute("tool.kwargs", str(kwargs))
                    
                    try:
                        add_span_event("mcp.tool.started", tool=tool_name)
                        
                        # Ejecutar herramienta
                        result = await func(*args, **kwargs)
                        
                        # Registrar resultado
                        add_span_event("mcp.tool.completed", 
                                     tool=tool_name,
                                     result_type=type(result).__name__)
                        
                        # Atributos del resultado
                        if isinstance(result, dict):
                            span.set_attribute("result.keys", str(list(result.keys())))
                        
                        return result
                        
                    except Exception as e:
                        add_span_event("mcp.tool.failed",
                                     tool=tool_name,
                                     error_type=e.__class__.__name__)
                        
                        span.set_attribute("error.type", e.__class__.__name__)
                        span.set_attribute("error.message", str(e))
                        
                        raise
            
            return async_wrapper
        return decorator
    
    def instrument_agent_execution(self, agent_type: str):
        """Decorador para instrumentar ejecución de agentes MCP"""
        def decorator(func: Callable):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                span_name = f"mcp.agent.{agent_type}.execution"
                
                with create_span(span_name) as span:
                    span.set_attribute("agent.type", agent_type)
                    span.set_attribute("agent.func", func.__name__)
                    span.set_attribute("correlation.id", get_correlation_id())
                    
                    # Información del agente si está en args
                    agent_instance = args[0] if args else None
                    if agent_instance:
                        span.set_attribute("agent.class", agent_instance.__class__.__name__)
                        span.set_attribute("agent.module", agent_instance.__class__.__module__)
                    
                    try:
                        add_span_event("mcp.agent.started", 
                                     agent_type=agent_type,
                                     correlation_id=get_correlation_id())
                        
                        # Ejecutar agente
                        result = await func(*args, **kwargs)
                        
                        add_span_event("mcp.agent.completed",
                                     agent_type=agent_type)
                        
                        return result
                        
                    except Exception as e:
                        add_span_event("mcp.agent.failed",
                                     agent_type=agent_type,
                                     error_type=e.__class__.__name__)
                        
                        span.set_attribute("error.type", e.__class__.__name__)
                        span.set_attribute("error.message", str(e))
                        
                        raise
            
            return async_wrapper
        return decorator


class FastMCPServerInstrumentor:
    """Instrumentor específico para FastMCP Server"""
    
    def __init__(self, server: FastMCP):
        self.server = server
        self.endpoint_instrumentor = MCPEndpointInstrumentor()
        self.logger = logging.getLogger(__name__)
    
    def instrument_server(self):
        """Instrumentar servidor MCP completo"""
        self.logger.info("Instrumenting FastMCP Server with OpenTelemetry")
        
        # Agregar middleware de OpenTelemetry
        self.server.app.add_middleware(MCPMiddleware)
        
        # Instrumentar endpoints existentes
        self._instrument_existing_endpoints()
        
        # Instrumentar agentes registrados
        self._instrument_registered_agents()
        
        # Agregar endpoints de observabilidad
        self._add_observability_endpoints()
        
        self.logger.info("FastMCP Server instrumented successfully")
    
    def _instrument_existing_endpoints(self):
        """Instrumentar endpoints existentes del servidor"""
        # Obtener rutas definidas en el servidor
        for route in self.server.app.routes:
            if hasattr(route, 'endpoint') and hasattr(route, 'path'):
                try:
                    # Verificar si es un endpoint MCP
                    if any(keyword in route.path for keyword in ['/mcp/', '/tools/', '/agents/']):
                        instrumented_endpoint = self.endpoint_instrumentor.instrument_mcp_endpoint(
                            route.endpoint
                        )
                        route.endpoint = instrumented_endpoint
                        self.logger.debug(f"Instrumented endpoint: {route.path}")
                except Exception as e:
                    self.logger.warning(f"Failed to instrument endpoint {route.path}: {e}")
    
    def _instrument_registered_agents(self):
        """Instrumentar agentes registrados en el servidor"""
        # Esto dependerá de cómo estén estructurados los agentes en FastMCP
        # Placeholder para implementación específica
        pass
    
    def _add_observability_endpoints(self):
        """Agregar endpoints de observabilidad al servidor"""
        from fastapi import Router
        
        router = Router()
        
        @router.get("/health/otel")
        async def otel_health():
            """Health check para OpenTelemetry"""
            otel_system = get_otel_system()
            summary = otel_system.get_trace_summary()
            return {
                "status": "healthy" if summary.get("status") == "initialized" else "unhealthy",
                "tracing_enabled": otel_system.config.enabled,
                "correlation_id": get_correlation_id(),
                "summary": summary
            }
        
        @router.get("/metrics/otel")
        async def otel_metrics():
            """Endpoints de métricas OpenTelemetry"""
            otel_system = get_otel_system()
            trace_summary = otel_system.get_trace_summary()
            
            return {
                "tracing_summary": trace_summary,
                "correlation_id": get_correlation_id(),
                "timestamp": time.time()
            }
        
        @router.get("/traces/correlation/{correlation_id}")
        async def get_trace_by_correlation(correlation_id: str):
            """Obtener trace por correlation ID"""
            # Placeholder - requeriría consulta real al backend de tracing
            return {
                "correlation_id": correlation_id,
                "traces": [],
                "message": "Feature requires backend integration"
            }
        
        # Agregar router a la aplicación
        self.server.app.include_router(router, prefix="/observability")


# Funciones de conveniencia para integrar con FastMCP Server
def instrument_fastmcp_server(app: FastAPI, otel_system=None) -> MCPMiddleware:
    """Instrumentar servidor FastMCP con middleware de OpenTelemetry"""
    otel = otel_system or get_otel_system()
    
    # Crear y configurar middleware
    middleware = MCPMiddleware(app)
    
    # Configurar integración automática
    instrumentor = MCPEndpointInstrumentor(otel)
    
    return middleware


def instrument_mcp_tool(tool_name: str):
    """Decorador para instrumentar herramientas MCP específicas"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            span_name = f"mcp.tool.{tool_name}"
            
            with create_span(span_name) as span:
                span.set_attribute("tool.name", tool_name)
                span.set_attribute("correlation.id", get_correlation_id())
                
                try:
                    add_span_event("mcp.tool.started", tool=tool_name)
                    result = await func(*args, **kwargs)
                    add_span_event("mcp.tool.completed", tool=tool_name)
                    return result
                except Exception as e:
                    add_span_event("mcp.tool.failed", 
                                 tool=tool_name,
                                 error_type=e.__class__.__name__)
                    span.set_attribute("error.type", e.__class__.__name__)
                    span.set_attribute("error.message", str(e))
                    raise
        
        return wrapper
    return decorator


def trace_mcp_workflow(workflow_name: str, user_id: str = None):
    """Decorador para rastrear workflows MCP completos"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            otel = get_otel_system()
            
            with otel.create_workflow_span(workflow_name, user_id=user_id) as span:
                try:
                    otel.track_workflow_progress(
                        span.get_span_context().trace_id.hex[:16],
                        "workflow_started",
                        function=func.__name__
                    )
                    
                    result = await func(*args, **kwargs)
                    
                    otel.track_workflow_progress(
                        span.get_span_context().trace_id.hex[:16],
                        "workflow_completed",
                        status="success"
                    )
                    
                    otel.complete_workflow(
                        span.get_span_context().trace_id.hex[:16],
                        status="completed",
                        function=func.__name__
                    )
                    
                    return result
                    
                except Exception as e:
                    otel.track_workflow_progress(
                        span.get_span_context().trace_id.hex[:16],
                        "workflow_failed",
                        status="error",
                        error_type=e.__class__.__name__
                    )
                    
                    otel.complete_workflow(
                        span.get_span_context().trace_id.hex[:16],
                        status="failed",
                        error_type=e.__class__.__name__,
                        function=func.__name__
                    )
                    
                    raise
        
        return async_wrapper
    return decorator


# Ejemplo de uso
if __name__ == "__main__":
    from fastapi import FastAPI
    from .opentelemetry_system import initialize_opentelemetry
    
    # Inicializar OpenTelemetry
    otel = initialize_opentelemetry()
    
    # Crear aplicación FastAPI
    app = FastAPI()
    
    # Instrumentar servidor
    middleware = instrument_fastmcp_server(app)
    app.add_middleware(MCPMiddleware)
    
    # Endpoint de ejemplo instrumentado
    @instrument_mcp_tool("sample_tool")
    async def sample_tool(data: str):
        """Herramienta MCP de ejemplo"""
        return {"result": f"Processed: {data}"}
    
    @app.post("/mcp/sample")
    @trace_function(operation_type="mcp_request")
    async def mcp_endpoint(data: dict):
        """Endpoint MCP de ejemplo"""
        result = await sample_tool(data.get("input", ""))
        return result
    
    @app.get("/health")
    async def health():
        """Health check"""
        return {"status": "healthy"}