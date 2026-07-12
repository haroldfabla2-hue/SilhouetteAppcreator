"""
Ejemplo completo de uso del sistema OpenTelemetry para MCP Core Superior

Este archivo demuestra todas las funcionalidades implementadas:
1. Inicialización del sistema
2. Instrumentación automática de agentes MCP
3. Spans para operaciones de base de datos
4. Context propagation
5. Custom spans para workflows complejos
6. Exporters configurables
7. Sampling strategies
8. Trace correlation IDs
9. Performance metrics
10. Error tracking y Exception capturing
11. Integration con FastMCP Server
12. Dashboard configuration
13. Deployment utilities
"""

import asyncio
import logging
import random
import time
from typing import Dict, List, Any

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar sistema completo de OpenTelemetry
from src.observability import (
    # Configuración
    TraceConfig, ExportBackend, SamplingType, TraceLevel,
    
    # Sistema principal
    OpenTelemetrySystem, initialize_opentelemetry, get_otel_system,
    
    # Decoradores
    trace_function, trace_async_function, create_span, add_span_event,
    
    # Componentes específicos
    MCPAgentInstrumentor, DatabaseInstrumentor, CustomSpanFactory,
    
    # Context propagation
    set_correlation_id, get_correlation_id,
    
    # Dashboard
    DashboardConfig, DashboardType, setup_observability_dashboard,
    get_grafana_dashboard_config,
    
    # FastMCP integration
    MCPMiddleware, instrument_mcp_tool, trace_mcp_workflow,
    
    # Deployment
    deploy_observability, quick_setup_development
)


# Simulación de agentes MCP para demostración
class DatabaseAgent:
    """Simulación de agente de base de datos"""
    
    def __init__(self, name: str):
        self.name = name
        self.operations_count = 0
    
    @trace_function(operation_type="database_operation")
    def execute_query(self, query: str, params: Dict = None) -> Dict[str, Any]:
        """Ejecutar query de base de datos"""
        self.operations_count += 1
        
        # Simular tiempo de ejecución
        execution_time = random.uniform(0.1, 2.0)
        time.sleep(execution_time)
        
        # Simular resultados
        return {
            "rows_affected": random.randint(1, 100),
            "execution_time": execution_time,
            "query": query
        }
    
    async def execute_async_query(self, query: str) -> Dict[str, Any]:
        """Ejecutar query asíncrono"""
        await asyncio.sleep(random.uniform(0.1, 1.0))
        
        return {
            "rows_returned": random.randint(1, 50),
            "async": True,
            "query": query
        }


class SearchAgent:
    """Simulación de agente de búsqueda"""
    
    def __init__(self, name: str):
        self.name = name
        self.searches_count = 0
    
    @trace_async_function(operation_type="search_operation")
    async def search(self, query: str, filters: Dict = None) -> List[Dict[str, Any]]:
        """Realizar búsqueda"""
        self.searches_count += 1
        
        # Simular búsqueda asíncrona
        await asyncio.sleep(random.uniform(0.2, 1.5))
        
        # Simular resultados
        results = []
        for i in range(random.randint(1, 10)):
            results.append({
                "id": i,
                "title": f"Result {i} for {query}",
                "score": random.uniform(0.1, 1.0),
                "query": query
            })
        
        return results
    
    @trace_function(operation_type="indexing_operation")
    def index_document(self, document: Dict[str, Any]) -> bool:
        """Indexar documento"""
        time.sleep(random.uniform(0.1, 0.5))
        
        logger.info(f"Document indexed: {document.get('id', 'unknown')}")
        return True


class ProcessingAgent:
    """Simulación de agente de procesamiento"""
    
    def __init__(self, name: str):
        self.name = name
        self.processing_count = 0
    
    @trace_function(operation_type="data_processing")
    def process_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Procesar datos"""
        self.processing_count += 1
        
        with create_span("data.transformation") as span:
            span.set_attribute("data.count", len(data))
            span.set_attribute("processing.agent", self.name)
            
            # Simular procesamiento
            time.sleep(random.uniform(0.5, 3.0))
            
            processed_data = []
            for item in data:
                # Procesar cada item
                processed_item = {
                    **item,
                    "processed": True,
                    "processed_at": time.time(),
                    "processing_agent": self.name
                }
                processed_data.append(processed_item)
            
            result = {
                "original_count": len(data),
                "processed_count": len(processed_data),
                "data": processed_data,
                "processing_time": sum(item["processed_at"] - item.get("created_at", time.time()) 
                                     for item in processed_data)
            }
            
            add_span_event("data.processing.completed", 
                         items_processed=len(processed_data))
            
            return result


# FastMCP Server integration example
def create_sample_fastmcp_server():
    """Crear servidor FastMCP de ejemplo"""
    from fastapi import FastAPI
    
    app = FastAPI(title="MCP Core Superior - Observability Demo")
    
    # Instrumentar servidor con middleware de OpenTelemetry
    app.add_middleware(MCPMiddleware)
    
    # Endpoint principal con instrumentación
    @app.post("/mcp/process")
    @trace_mcp_workflow("data_processing_workflow")
    async def process_workflow(request_data: Dict[str, Any]):
        """Workflow completo de procesamiento"""
        otel = get_otel_system()
        
        # Crear workflow span
        workflow_id = get_correlation_id()
        
        try:
            # Inicializar workflow
            otel.track_workflow_progress(workflow_id, "validate_input", status="running")
            
            # Validar datos de entrada
            data = request_data.get("data", [])
            if not data:
                raise ValueError("No data provided")
            
            # Simular procesamiento en diferentes agentes
            otel.track_workflow_progress(workflow_id, "database_operations", status="running")
            
            db_agent = DatabaseAgent("demo_db_agent")
            query_result = db_agent.execute_query(
                "SELECT * FROM users WHERE active = true",
                {"limit": 10}
            )
            
            otel.track_workflow_progress(workflow_id, "search_operations", status="running")
            
            search_agent = SearchAgent("demo_search_agent")
            search_results = await search_agent.search("machine learning", {"type": "article"})
            
            otel.track_workflow_progress(workflow_id, "data_processing", status="running")
            
            processing_agent = ProcessingAgent("demo_processing_agent")
            processed_data = processing_agent.process_data(search_results)
            
            # Finalizar workflow exitosamente
            otel.track_workflow_progress(workflow_id, "complete", status="completed")
            otel.complete_workflow(
                workflow_id,
                status="completed",
                data_processed=len(data),
                search_results_found=len(search_results),
                workflow_type="data_processing"
            )
            
            return {
                "status": "success",
                "correlation_id": workflow_id,
                "query_result": query_result,
                "search_count": len(search_results),
                "processed_data": processed_data
            }
            
        except Exception as e:
            # Marcar workflow como fallido
            otel.track_workflow_progress(workflow_id, "error", status="failed")
            otel.complete_workflow(
                workflow_id,
                status="failed",
                error_type=e.__class__.__name__,
                error_message=str(e)
            )
            raise
    
    @app.get("/health/observability")
    async def health_check():
        """Health check con métricas de observabilidad"""
        otel = get_otel_system()
        summary = otel.get_trace_summary()
        
        return {
            "status": "healthy",
            "correlation_id": get_correlation_id(),
            "trace_summary": summary,
            "timestamp": time.time()
        }
    
    @app.get("/metrics/observability")
    async def get_metrics():
        """Obtener métricas de observabilidad"""
        otel = get_otel_system()
        
        return {
            "correlation_id": get_correlation_id(),
            "trace_summary": otel.get_trace_summary(),
            "health_status": "healthy"
        }
    
    return app


# Función principal de demostración
async def main():
    """Función principal que demuestra todas las funcionalidades"""
    logger.info("=== INICIANDO DEMOSTRACIÓN COMPLETA DE OPENTELEMETRY ===")
    
    # 1. CONFIGURACIÓN INICIAL
    logger.info("1. Configurando sistema OpenTelemetry...")
    
    # Configuración personalizada
    config = TraceConfig(
        enabled=True,
        export_backend=ExportBackend.ALL,  # Jaeger, Zipkin, OTLP, Console
        sampling_type=SamplingType.RATIO_BASED,
        sampling_ratio=0.5,  # 50% de las requests para demostración
        service_name="mcp-core-observability-demo",
        service_version="1.0.0",
        environment="development",
        trace_level=TraceLevel.VERBOSE,
        custom_attributes={
            "demo.version": "1.0",
            "demo.features": "all"
        }
    )
    
    # Inicializar sistema
    otel_system = initialize_opentelemetry(config)
    logger.info("Sistema OpenTelemetry inicializado correctamente")
    
    # 2. DASHBOARD CONFIGURATION
    logger.info("2. Configurando dashboard de observabilidad...")
    
    dashboard_config = DashboardConfig(
        dashboard_type=DashboardType.GRAFANA,
        enabled=True,
        port=3000,
        jaeger_port=16686,
        prometheus_port=9090
    )
    
    dashboard = await setup_observability_dashboard(dashboard_config)
    logger.info("Dashboard configurado en http://localhost:3000")
    
    # 3. AGENT INSTRUMENTATION
    logger.info("3. Instrumentando agentes MCP...")
    
    # Crear agentes de ejemplo
    agents = [
        DatabaseAgent("production_db_agent"),
        SearchAgent("production_search_agent"),
        ProcessingAgent("production_processing_agent")
    ]
    
    # Instrumentar automáticamente
    for agent in agents:
        # Usar instrumentación manual
        db_agent = DatabaseAgent("production_db_agent")
        search_agent = SearchAgent("production_search_agent")
        processing_agent = ProcessingAgent("production_processing_agent")
        
        logger.info(f"Agente {agent.name} instrumentado")
    
    # 4. DATABASE OPERATIONS WITH TRACING
    logger.info("4. Ejecutando operaciones de base de datos con tracing...")
    
    db_agent = DatabaseAgent("demo_agent")
    
    # Operación simple
    result1 = db_agent.execute_query("SELECT COUNT(*) FROM users")
    logger.info(f"Query result: {result1}")
    
    # Operación con error
    try:
        with otel_system.db_instrumentor.db_operation_span(
            "insert", "users", 
            query="INSERT INTO users (name, email) VALUES (?, ?)",
            custom_attributes={"batch_size": 100}
        ) as span:
            # Simular operación de BD
            time.sleep(0.2)
            add_span_event("batch.insert.started", batch_size=100)
            
            # Simular error (comentado para evitar fallo)
            # raise Exception("Simulated database error")
            
            add_span_event("batch.insert.completed", rows_inserted=100)
    
    except Exception as e:
        logger.error(f"Database operation failed: {e}")
    
    # 5. ASYNC OPERATIONS WITH TRACING
    logger.info("5. Ejecutando operaciones asíncronas...")
    
    search_agent = SearchAgent("demo_search_agent")
    
    # Búsqueda simple
    results = await search_agent.search("OpenTelemetry tracing")
    logger.info(f"Found {len(results)} results")
    
    # Múltiples búsquedas en paralelo
    tasks = [
        search_agent.search("distributed tracing", {"type": "article"}),
        search_agent.search("performance monitoring", {"type": "documentation"}),
        search_agent.search("microservices architecture", {"type": "blog"})
    ]
    
    parallel_results = await asyncio.gather(*tasks)
    total_results = sum(len(results) for results in parallel_results)
    logger.info(f"Parallel search completed: {total_results} total results")
    
    # 6. WORKFLOW TRACKING
    logger.info("6. Demostrando tracking de workflows complejos...")
    
    # Workflow de procesamiento de datos
    with otel_system.create_workflow_span(
        "complex_data_workflow",
        workflow_id="demo_workflow_001",
        user_id="demo_user",
        data_type="machine_learning_dataset"
    ) as workflow_span:
        
        workflow_id = workflow_span.get_span_context().trace_id.hex[:16]
        
        # Etapa 1: Validación
        otel_system.track_workflow_progress(
            workflow_id, "data_validation", status="running", 
            data_samples=1000
        )
        await asyncio.sleep(0.5)
        
        otel_system.track_workflow_progress(
            workflow_id, "data_validation", status="completed",
            valid_samples=950, invalid_samples=50
        )
        
        # Etapa 2: Preprocessing
        otel_system.track_workflow_progress(
            workflow_id, "preprocessing", status="running",
            preprocessing_steps=["normalize", "encode", "split"]
        )
        
        processing_agent = ProcessingAgent("workflow_agent")
        mock_data = [{"id": i, "value": random.random()} for i in range(100)]
        processed_result = processing_agent.process_data(mock_data)
        
        otel_system.track_workflow_progress(
            workflow_id, "preprocessing", status="completed",
            processed_samples=len(processed_result["data"])
        )
        
        # Etapa 3: Model training
        otel_system.track_workflow_progress(
            workflow_id, "model_training", status="running",
            model_type="random_forest", hyperparameters={"n_estimators": 100}
        )
        
        await asyncio.sleep(1.0)  # Simular entrenamiento
        
        otel_system.track_workflow_progress(
            workflow_id, "model_training", status="completed",
            accuracy=0.85, training_time=1.0
        )
        
        # Completar workflow
        otel_system.complete_workflow(
            workflow_id,
            status="completed",
            total_duration=3.0,
            stages_completed=3,
            final_accuracy=0.85
        )
    
    # 7. ERROR TRACKING DEMONSTRATION
    logger.info("7. Demostrando error tracking...")
    
    def function_with_error():
        """Función que genera error para testing"""
        with create_span("error.demo.function") as span:
            span.set_attribute("demo.error.test", True)
            add_span_event("error.before_raise")
            
            raise ValueError("Demo error for tracing")
    
    try:
        function_with_error()
    except ValueError as e:
        logger.info(f"Error captured and tracked: {e}")
    
    # 8. CORRELATION ID DEMONSTRATION
    logger.info("8. Demostrando correlation IDs...")
    
    # Generar correlation ID específico
    custom_correlation_id = "demo-correlation-12345"
    set_correlation_id(custom_correlation_id)
    
    logger.info(f"Correlation ID set: {custom_correlation_id}")
    logger.info(f"Current correlation ID: {get_correlation_id()}")
    
    # 9. METRICS COLLECTION
    logger.info("9. Demostrando recolección de métricas...")
    
    # Registrar métricas manualmente
    otel_system.metrics.record_span_duration(0.5, "demo_operation")
    otel_system.metrics.record_span_created("demo_operation")
    otel_system.metrics.record_error("demo_error_type", "demo_operation")
    
    # Métricas de agentes
    otel_system.metrics.record_agent_execution(1.5, "DatabaseAgent", True)
    otel_system.metrics.record_agent_execution(2.0, "SearchAgent", False)
    otel_system.metrics.record_agent_execution(0.8, "ProcessingAgent", True)
    
    # 10. FASTMCP SERVER INTEGRATION
    logger.info("10. Creando servidor FastMCP de ejemplo...")
    
    fastmcp_app = create_sample_fastmcp_server()
    logger.info("Servidor FastMCP creado con instrumentación completa")
    
    # 11. DEPLOYMENT UTILITIES
    logger.info("11. Generando configuración de despliegue...")
    
    # Obtener configuraciones para dashboards
    grafana_config = get_grafana_dashboard_config()
    logger.info("Configuración de Grafana generada")
    
    prometheus_config = {
        "global": {
            "scrape_interval": "15s"
        },
        "scrape_configs": [
            {
                "job_name": "mcp-core-demo",
                "static_configs": [{"targets": ["localhost:8080"]}]
            }
        ]
    }
    logger.info("Configuración de Prometheus generada")
    
    # 12. SYSTEM SUMMARY
    logger.info("12. Generando resumen del sistema...")
    
    summary = otel_system.get_trace_summary()
    logger.info(f"Sistema configurado:")
    logger.info(f"  - Backend de exportación: {summary['config']['export_backend']}")
    logger.info(f"  - Tipo de sampling: {summary['config']['sampling_type']}")
    logger.info(f"  - Ratio de sampling: {summary['config']['sampling_ratio']}")
    logger.info(f"  - Servicios instrumentados: {summary['instrumentation']['agents_instrumented']}")
    
    # Health check del sistema
    health = await dashboard.get_system_health()
    logger.info(f"Estado de salud del sistema: {health['status']} (score: {health['score']})")
    
    logger.info("=== DEMOSTRACIÓN COMPLETADA ===")
    
    print("\n" + "="*80)
    print("RESUMEN DE LA DEMOSTRACIÓN DE OPENTELEMETRY")
    print("="*80)
    print(f"✅ Sistema OpenTelemetry inicializado")
    print(f"✅ Dashboard configurado: http://localhost:3000 (Grafana)")
    print(f"✅ Jaeger UI: http://localhost:16686")
    print(f"✅ Prometheus: http://localhost:9090")
    print(f"✅ Correlación ID actual: {get_correlation_id()}")
    print(f"✅ Agentes instrumentados: {summary['instrumentation']['agents_instrumented']}")
    print(f"✅ Workflows rastreados: {len([k for k in otel_system.span_factory.workflow_spans.keys()])}")
    print(f"✅ Errores capturados: {otel_system.error_tracker.get_error_statistics()['total_errors']}")
    print("="*80)
    
    print("\nPara acceder a las interfaces:")
    print("  - Grafana: http://localhost:3000 (admin/admin)")
    print("  - Jaeger: http://localhost:16686")
    print("  - Prometheus: http://localhost:9090")
    print("\nPara detener los servicios:")
    print("  cd observability && ./stop-observability.sh")


# Decorador de ejemplo para instrumentar funciones MCP
@trace_mcp_workflow("demo_mcp_workflow", user_id="demo_user")
@instrument_mcp_tool("demo_tool")
@trace_function(operation_type="mcp_demo")
def demo_mcp_tool(data: Dict[str, Any]) -> Dict[str, Any]:
    """Herramienta MCP de ejemplo con instrumentación completa"""
    result = {
        "processed": True,
        "input_data": data,
        "correlation_id": get_correlation_id(),
        "processing_time": random.uniform(0.1, 0.5)
    }
    
    time.sleep(result["processing_time"])
    return result


if __name__ == "__main__":
    # Ejecutar demostración
    asyncio.run(main())
    
    # Demostrar uso de decoradores
    print("\nDemostrando uso de decoradores:")
    sample_data = {"type": "demo", "value": "test"}
    result = demo_mcp_tool(sample_data)
    print(f"Resultado del MCP tool: {result}")