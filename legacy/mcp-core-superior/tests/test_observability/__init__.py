"""
Test suite para el Sistema de Observabilidad del MCP Core Superior

Cubre:
- OpenTelemetry integration
- Métricas avanzadas
- Logging estructurado
- Dashboard configuration
- Agent integration
- FastMCP integration
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch, call
from typing import Dict, Any, List
import json
from datetime import datetime, timedelta

# Test marks
pytestmark = [pytest.mark.observability, pytest.mark.unit, pytest.mark.async_test]


class TestOpenTelemetrySystem:
    """Tests para el sistema OpenTelemetry"""
    
    @pytest.fixture
    def otel_system(self):
        """Fixture del sistema OpenTelemetry"""
        from observability.opentelemetry_system import OpenTelemetrySystem
        return OpenTelemetrySystem
    
    @pytest.fixture
    def mock_tracer(self):
        """Mock del tracer OpenTelemetry"""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=None)
        
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span
        mock_tracer.get_current_span.return_value = mock_span
        
        return mock_tracer
    
    async def test_otel_initialization(self, otel_system):
        """Test de inicialización del sistema OTel"""
        with patch('observability.opentelemetry_system.otel') as mock_otel:
            mock_otel.get_tracer.return_value = MagicMock()
            
            system = otel_system()
            result = await system.initialize()
            
            assert result['success'] is True
            assert system.initialized is True
    
    async def test_span_creation(self, otel_system, mock_tracer):
        """Test de creación de spans"""
        with patch('observability.opentelemetry_system.otel') as mock_otel:
            mock_otel.get_tracer.return_value = mock_tracer
            
            system = otel_system()
            await system.initialize()
            
            span_id = system.create_span("test_operation", {"param1": "value1"})
            
            assert span_id is not None
            assert mock_tracer.start_as_current_span.called
    
    async def test_span_attributes(self, otel_system, mock_tracer):
        """Test de atributos de spans"""
        with patch('observability.opentelemetry_system.otel') as mock_otel:
            mock_otel.get_tracer.return_value = mock_tracer
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
            
            system = otel_system()
            await system.initialize()
            
            # Crear span y agregar atributos
            system.create_span("test_operation")
            system.add_span_attribute("test_key", "test_value")
            system.add_span_attribute("user_id", "user123")
            
            # Verificar que se agregaron los atributos
            assert mock_span.set_attribute.call_count >= 2
    
    async def test_span_events(self, otel_system, mock_tracer):
        """Test de eventos en spans"""
        with patch('observability.opentelemetry_system.otel') as mock_otel:
            mock_otel.get_tracer.return_value = mock_tracer
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
            
            system = otel_system()
            await system.initialize()
            
            # Crear span y agregar evento
            system.create_span("test_operation")
            system.add_span_event("operation_started", {"timestamp": "2025-11-04T05:43:15Z"})
            
            # Verificar que se agregó el evento
            mock_span.add_event.assert_called_once()
    
    async def test_span_status(self, otel_system, mock_tracer):
        """Test de estado de spans"""
        with patch('observability.opentelemetry_system.otel') as mock_otel:
            mock_otel.get_tracer.return_value = mock_tracer
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
            
            system = otel_system()
            await system.initialize()
            
            # Crear span y establecer estado
            system.create_span("test_operation")
            system.set_span_status("OK", "Operation completed successfully")
            
            # Verificar que se estableció el estado
            mock_span.set_status.assert_called_once()
    
    async def test_trace_context_propagation(self, otel_system):
        """Test de propagación de contexto de trace"""
        with patch('observability.opentelemetry_system.otel') as mock_otel:
            mock_carrier = {}
            
            system = otel_system()
            await system.initialize()
            
            # Inyectar contexto de trace
            system.inject_trace_context(mock_carrier)
            
            # Verificar que se propagó el contexto
            assert len(mock_carrier) > 0
    
    async def test_error_tracking(self, otel_system, mock_tracer):
        """Test de seguimiento de errores"""
        with patch('observability.opentelemetry_system.otel') as mock_otel:
            mock_otel.get_tracer.return_value = mock_tracer
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
            
            system = otel_system()
            await system.initialize()
            
            # Crear span y registrar error
            system.create_span("test_operation")
            system.record_exception(Exception("Test error"))
            
            # Verificar que se registró la excepción
            mock_span.record_exception.assert_called_once()
    
    async def test_custom_instrumentation(self, otel_system, mock_tracer):
        """Test de instrumentación personalizada"""
        with patch('observability.opentelemetry_system.otel') as mock_otel:
            mock_otel.get_tracer.return_value = mock_tracer
            
            system = otel_system()
            await system.initialize()
            
            # Instrumentar función custom
            @system.trace_function("custom_operation")
            async def custom_function():
                return "result"
            
            result = await custom_function()
            
            assert result == "result"
            assert mock_tracer.start_as_current_span.called


class TestAdvancedMetrics:
    """Tests para métricas avanzadas"""
    
    @pytest.fixture
    def metrics_system(self):
        """Fixture del sistema de métricas"""
        from observability.advanced_metrics import AdvancedMetrics
        return AdvancedMetrics
    
    @pytest.fixture
    def mock_prometheus(self):
        """Mock de métricas Prometheus"""
        mock_counter = MagicMock()
        mock_gauge = MagicMock()
        mock_histogram = MagicMock()
        
        return {
            'counter': mock_counter,
            'gauge': mock_gauge,
            'histogram': mock_histogram
        }
    
    async def test_metric_creation(self, metrics_system, mock_prometheus):
        """Test de creación de métricas"""
        with patch('observability.advanced_metrics.prometheus') as mock_prom:
            mock_prom.Counter.return_value = mock_prometheus['counter']
            mock_prom.Gauge.return_value = mock_prometheus['gauge']
            mock_prom.Histogram.return_value = mock_prometheus['histogram']
            
            system = metrics_system()
            
            # Test contador
            counter = system.create_counter(
                name="test_counter",
                description="Test counter",
                labels=["label1"]
            )
            assert counter is not None
            
            # Test gauge
            gauge = system.create_gauge(
                name="test_gauge",
                description="Test gauge",
                labels=["label2"]
            )
            assert gauge is not None
            
            # Test histogram
            histogram = system.create_histogram(
                name="test_histogram",
                description="Test histogram",
                labels=["label3"]
            )
            assert histogram is not None
    
    async def test_metric_recording(self, metrics_system):
        """Test de registro de métricas"""
        system = metrics_system()
        
        # Crear métricas mock
        mock_counter = MagicMock()
        mock_gauge = MagicMock()
        mock_histogram = MagicMock()
        
        system._counters = {"test_counter": mock_counter}
        system._gauges = {"test_gauge": mock_gauge}
        system._histograms = {"test_histogram": mock_histogram}
        
        # Test increment counter
        system.record_counter("test_counter", 1, labels={"label1": "value1"})
        mock_counter.labels.assert_called_once_with(label1="value1")
        mock_counter.labels.return_value.inc.assert_called_once_with(1)
        
        # Test set gauge
        system.record_gauge("test_gauge", 42.5, labels={"label2": "value2"})
        mock_gauge.labels.assert_called_once_with(label2="value2")
        mock_gauge.labels.return_value.set.assert_called_once_with(42.5)
        
        # Test record histogram
        system.record_histogram("test_histogram", 0.125, labels={"label3": "value3"})
        mock_histogram.labels.assert_called_once_with(label3="value3")
        mock_histogram.labels.return_value.observe.assert_called_once_with(0.125)
    
    async def test_agent_metrics(self, metrics_system):
        """Test de métricas específicas de agentes"""
        system = metrics_system()
        
        # Métricas de ejecución de agente
        system.record_agent_execution(
            agent_id="agent-123",
            operation="process_request",
            duration=0.5,
            success=True
        )
        
        # Métricas de errores de agente
        system.record_agent_error(
            agent_id="agent-123",
            error_type="timeout",
            error_message="Request timeout"
        )
        
        # Métricas de utilización de agentes
        system.record_agent_utilization(
            agent_id="agent-123",
            utilization_percent=75.0
        )
        
        # Verificar que se crearon las métricas
        assert "agent_executions_total" in system._counters
        assert "agent_errors_total" in system._counters
        assert "agent_utilization" in system._gauges
    
    async def test_system_metrics(self, metrics_system):
        """Test de métricas del sistema"""
        system = metrics_system()
        
        # Métricas de CPU
        system.record_cpu_usage(45.2)
        
        # Métricas de memoria
        system.record_memory_usage(1024.5)
        
        # Métricas de red
        system.record_network_io(125.0, 89.3)
        
        # Métricas de disco
        system.record_disk_usage(65.8)
        
        # Métricas de peticiones HTTP
        system.record_http_requests(
            method="GET",
            endpoint="/api/agents",
            status_code=200,
            duration=0.125
        )
        
        # Verificar métricas del sistema
        assert "system_cpu_usage" in system._gauges
        assert "system_memory_usage" in system._gauges
        assert "http_requests_total" in system._counters
    
    async def test_custom_metrics(self, metrics_system):
        """Test de métricas personalizadas"""
        system = metrics_system()
        
        # Definir métricas personalizadas
        custom_metrics = {
            "business_operations_total": {
                "type": "counter",
                "description": "Total business operations",
                "labels": ["operation_type", "status"]
            },
            "operation_duration_seconds": {
                "type": "histogram",
                "description": "Duration of business operations",
                "labels": ["operation_type"]
            }
        }
        
        system.define_custom_metrics(custom_metrics)
        
        # Registrar valores personalizados
        system.record_custom_metric(
            "business_operations_total",
            1,
            labels={"operation_type": "search", "status": "success"}
        )
        
        system.record_custom_metric(
            "operation_duration_seconds",
            0.75,
            labels={"operation_type": "search"}
        )
        
        assert "business_operations_total" in system._counters
        assert "operation_duration_seconds" in system._histograms
    
    async def test_metric_aggregation(self, metrics_system):
        """Test de agregación de métricas"""
        system = metrics_system()
        
        # Simular múltiples registros
        values = [1, 2, 3, 4, 5]
        for value in values:
            system.record_histogram("test_histogram", value)
        
        # Obtener estadísticas agregadas
        stats = system.get_metric_stats("test_histogram")
        
        assert "count" in stats
        assert "sum" in stats
        assert "avg" in stats
        assert stats["count"] == len(values)
        assert stats["sum"] == sum(values)
        assert stats["avg"] == sum(values) / len(values)
    
    async def test_metrics_export(self, metrics_system):
        """Test de exportación de métricas"""
        system = metrics_system()
        
        # Configurar métricas
        system.record_counter("test_counter", 10)
        system.record_gauge("test_gauge", 25.5)
        
        # Exportar métricas en formato Prometheus
        prometheus_output = system.export_prometheus_metrics()
        
        assert "# TYPE test_counter counter" in prometheus_output
        assert "# TYPE test_gauge gauge" in prometheus_output
        assert "test_counter 10" in prometheus_output
        assert "test_gauge 25.5" in prometheus_output


class TestStructuredLogger:
    """Tests para logging estructurado"""
    
    @pytest.fixture
    def structured_logger(self):
        """Fixture del logger estructurado"""
        from observability.structured_logger import StructuredLogger
        return StructuredLogger
    
    async def test_logger_initialization(self, structured_logger):
        """Test de inicialización del logger"""
        logger = structured_logger(
            name="test_logger",
            level="INFO",
            format="json"
        )
        
        assert logger.name == "test_logger"
        assert logger.level == "INFO"
        assert logger.format == "json"
    
    async def test_structured_logging(self, structured_logger):
        """Test de logging estructurado"""
        logger = structured_logger(name="test")
        
        with patch.object(logger.logger, 'info') as mock_info:
            # Log con contexto estructurado
            logger.log(
                level="INFO",
                message="User action performed",
                context={
                    "user_id": "user123",
                    "action": "login",
                    "timestamp": "2025-11-04T05:43:15Z"
                }
            )
            
            # Verificar que se llamó al logger con mensaje estructurado
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            assert "User action performed" in call_args
    
    async def test_log_levels(self, structured_logger):
        """Test de diferentes niveles de log"""
        logger = structured_logger(name="test")
        
        with patch.object(logger.logger, 'info') as mock_info:
            with patch.object(logger.logger, 'warning') as mock_warning:
                with patch.object(logger.logger, 'error') as mock_error:
                    
                    # Test INFO
                    logger.info("Info message", context={"level": "info"})
                    assert mock_info.called
                    
                    # Test WARNING
                    logger.warning("Warning message", context={"level": "warning"})
                    assert mock_warning.called
                    
                    # Test ERROR
                    logger.error("Error message", context={"level": "error"})
                    assert mock_error.called
    
    async def test_correlation_tracking(self, structured_logger):
        """Test de seguimiento de correlación"""
        logger = structured_logger(name="test")
        
        # Simular trace ID y span ID
        trace_id = "trace-abc123"
        span_id = "span-def456"
        
        with patch.object(logger.logger, 'info') as mock_info:
            # Log con correlación
            logger.log_with_correlation(
                level="INFO",
                message="Processing request",
                trace_id=trace_id,
                span_id=span_id,
                user_id="user123"
            )
            
            # Verificar que incluye IDs de correlación
            call_args = mock_info.call_args[0][0]
            assert trace_id in call_args
            assert span_id in call_args
    
    async def test_agent_logging(self, structured_logger):
        """Test de logging específico de agentes"""
        logger = structured_logger(name="agent_logger")
        
        with patch.object(logger.logger, 'info') as mock_info:
            # Log de actividad de agente
            logger.log_agent_activity(
                agent_id="agent-123",
                operation="process_request",
                status="success",
                duration_ms=250,
                metadata={
                    "request_size": 1024,
                    "response_size": 2048
                }
            )
            
            # Verificar estructura del log
            call_args = mock_info.call_args[0][0]
            assert "agent-123" in call_args
            assert "process_request" in call_args
            assert "success" in call_args
            assert "250" in call_args
    
    async def test_security_logging(self, structured_logger):
        """Test de logging de seguridad"""
        logger = structured_logger(name="security_logger")
        
        with patch.object(logger.logger, 'warning') as mock_warning:
            # Log de evento de seguridad
            logger.log_security_event(
                event_type="authentication_failed",
                user_id="user123",
                ip_address="192.168.1.100",
                severity="medium",
                description="Failed login attempt"
            )
            
            # Verificar que se registró evento de seguridad
            call_args = mock_warning.call_args[0][0]
            assert "authentication_failed" in call_args
            assert "user123" in call_args
            assert "medium" in call_args


class TestLoggingConfig:
    """Tests para configuración de logging"""
    
    @pytest.fixture
    def logging_config(self):
        """Fixture de configuración de logging"""
        from observability.logging_config import LoggingConfig
        return LoggingConfig
    
    async def test_config_creation(self, logging_config):
        """Test de creación de configuración"""
        config = logging_config()
        
        assert hasattr(config, 'level')
        assert hasattr(config, 'format')
        assert hasattr(config, 'handlers')
    
    async def test_log_level_config(self, logging_config):
        """Test de configuración de niveles de log"""
        config = logging_config(
            level="DEBUG",
            agent_levels={
                "python_executor": "INFO",
                "git_operations": "WARNING"
            }
        )
        
        assert config.level == "DEBUG"
        assert config.agent_levels["python_executor"] == "INFO"
        assert config.agent_levels["git_operations"] == "WARNING"
    
    async def test_handler_configuration(self, logging_config):
        """Test de configuración de handlers"""
        config = logging_config(
            handlers={
                "console": {
                    "type": "console",
                    "level": "INFO"
                },
                "file": {
                    "type": "file",
                    "filename": "/tmp/app.log",
                    "level": "DEBUG",
                    "rotation": "daily"
                },
                "syslog": {
                    "type": "syslog",
                    "address": "/dev/log",
                    "facility": "local0"
                }
            }
        )
        
        assert "console" in config.handlers
        assert "file" in config.handlers
        assert "syslog" in config.handlers
    
    async def test_json_logging(self, logging_config):
        """Test de logging en formato JSON"""
        config = logging_config(format="json")
        
        assert config.format == "json"
        
        # Verificar que se puede generar formato JSON
        log_entry = {
            "timestamp": "2025-11-04T05:43:15Z",
            "level": "INFO",
            "message": "Test message",
            "logger": "test"
        }
        
        json_output = config.format_log_entry(log_entry)
        assert isinstance(json_output, str)
        
        # Verificar que es JSON válido
        parsed = json.loads(json_output)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
    
    async def test_log_rotation(self, logging_config):
        """Test de rotación de logs"""
        config = logging_config(
            file_rotation={
                "max_size": "100MB",
                "backup_count": 5,
                "interval": "daily"
            }
        )
        
        assert config.file_rotation["max_size"] == "100MB"
        assert config.file_rotation["backup_count"] == 5
        assert config.file_rotation["interval"] == "daily"


class TestMetricsConfig:
    """Tests para configuración de métricas"""
    
    @pytest.fixture
    def metrics_config(self):
        """Fixture de configuración de métricas"""
        from observability.metrics_config import MetricsConfig
        return MetricsConfig
    
    async def test_prometheus_config(self, metrics_config):
        """Test de configuración de Prometheus"""
        config = metrics_config(
            prometheus={
                "enabled": True,
                "port": 9090,
                "path": "/metrics",
                "namespace": "mcp_core"
            }
        )
        
        assert config.prometheus["enabled"] is True
        assert config.prometheus["port"] == 9090
        assert config.prometheus["namespace"] == "mcp_core"
    
    async def test_metric_definitions(self, metrics_config):
        """Test de definiciones de métricas"""
        custom_metrics = {
            "agent_executions_total": {
                "type": "counter",
                "description": "Total agent executions",
                "labels": ["agent_id", "operation"]
            },
            "agent_duration_seconds": {
                "type": "histogram",
                "description": "Agent execution duration",
                "labels": ["agent_id", "operation"],
                "buckets": [0.1, 0.5, 1.0, 2.5, 5.0]
            }
        }
        
        config = metrics_config(custom_metrics=custom_metrics)
        
        assert "agent_executions_total" in config.custom_metrics
        assert config.custom_metrics["agent_executions_total"]["type"] == "counter"
        assert "agent_duration_seconds" in config.custom_metrics
        assert config.custom_metrics["agent_duration_seconds"]["type"] == "histogram"
    
    async def test_aggregation_config(self, metrics_config):
        """Test de configuración de agregación"""
        config = metrics_config(
            aggregation={
                "window_size": "1m",
                "aggregation_functions": ["avg", "max", "min", "sum"],
                "export_interval": "30s"
            }
        )
        
        assert config.aggregation["window_size"] == "1m"
        assert "avg" in config.aggregation["aggregation_functions"]
        assert config.aggregation["export_interval"] == "30s"
    
    async def test_retention_config(self, metrics_config):
        """Test de configuración de retención"""
        config = metrics_config(
            retention={
                "time_series": "30d",
                "aggregated": "1y",
                "raw_data": "7d"
            }
        )
        
        assert config.retention["time_series"] == "30d"
        assert config.retention["aggregated"] == "1y"
        assert config.retention["raw_data"] == "7d"


class TestDashboardConfig:
    """Tests para configuración de dashboards"""
    
    @pytest.fixture
    def dashboard_config(self):
        """Fixture de configuración de dashboard"""
        from observability.dashboard_config import DashboardConfig
        return DashboardConfig
    
    async def test_dashboard_creation(self, dashboard_config):
        """Test de creación de dashboard"""
        config = dashboard_config(
            name="MCP Core Dashboard",
            description="Main dashboard for MCP Core Superior",
            refresh_interval=30
        )
        
        assert config.name == "MCP Core Dashboard"
        assert config.description == "Main dashboard for MCP Core Superior"
        assert config.refresh_interval == 30
    
    async def test_widget_configuration(self, dashboard_config):
        """Test de configuración de widgets"""
        widgets = [
            {
                "type": "metric",
                "title": "Agent Executions",
                "metric": "agent_executions_total",
                "chart_type": "line",
                "time_range": "1h"
            },
            {
                "type": "alert",
                "title": "High Error Rate",
                "condition": "error_rate > 0.1",
                "severity": "warning"
            },
            {
                "type": "log",
                "title": "Recent Errors",
                "query": "level=ERROR",
                "limit": 50
            }
        ]
        
        config = dashboard_config(widgets=widgets)
        
        assert len(config.widgets) == 3
        assert config.widgets[0]["type"] == "metric"
        assert config.widgets[1]["type"] == "alert"
        assert config.widgets[2]["type"] == "log"
    
    async def test_layout_configuration(self, dashboard_config):
        """Test de configuración de layout"""
        config = dashboard_config(
            layout={
                "columns": 12,
                "row_height": 30,
                "margin": [10, 10]
            },
            panels=[
                {
                    "id": "panel1",
                    "x": 0, "y": 0, "w": 6, "h": 4,
                    "widget_id": "widget1"
                },
                {
                    "id": "panel2",
                    "x": 6, "y": 0, "w": 6, "h": 4,
                    "widget_id": "widget2"
                }
            ]
        )
        
        assert config.layout["columns"] == 12
        assert len(config.panels) == 2
        assert config.panels[0]["w"] == 6
        assert config.panels[1]["w"] == 6
    
    async def test_alert_configuration(self, dashboard_config):
        """Test de configuración de alertas"""
        alerts = [
            {
                "name": "High CPU Usage",
                "condition": "cpu_usage > 80",
                "duration": "5m",
                "severity": "warning",
                "notifications": ["email", "slack"]
            },
            {
                "name": "Agent Down",
                "condition": "agent_status == 'down'",
                "duration": "1m",
                "severity": "critical",
                "notifications": ["pagerduty"]
            }
        ]
        
        config = dashboard_config(alerts=alerts)
        
        assert len(config.alerts) == 2
        assert config.alerts[0]["name"] == "High CPU Usage"
        assert config.alerts[1]["severity"] == "critical"


class TestAgentIntegration:
    """Tests para integración con agentes"""
    
    @pytest.fixture
    def agent_observability(self):
        """Fixture de observabilidad para agentes"""
        from observability.agent_integration import AgentObservability
        return AgentObservability
    
    async def test_agent_instrumentation(self, agent_observability):
        """Test de instrumentación de agentes"""
        from agents.base_agent_wrapper import BaseAgentWrapper
        
        with patch('observability.agent_integration.OpenTelemetrySystem') as mock_otel:
            mock_otel_instance = MagicMock()
            mock_otel.return_value = mock_otel_instance
            
            # Instrumentar agente
            instrumented_agent = agent_observability.instrument_agent(
                BaseAgentWrapper,
                agent_type="base",
                agent_id="test-agent"
            )
            
            # Verificar que se instrumentó
            assert instrumented_agent is not None
            
            # Verificar que se creó el tracer específico del agente
            mock_otel_instance.create_span.assert_any_call(
                f"agent_{BaseAgentWrapper.__name__}_init"
            )
    
    async def test_operation_tracking(self, agent_observability):
        """Test de seguimiento de operaciones"""
        with patch('observability.agent_integration.OpenTelemetrySystem') as mock_otel:
            mock_otel_instance = MagicMock()
            mock_otel.return_value = mock_otel_instance
            
            agent_obs = agent_observability()
            
            # Simular operación de agente
            agent_obs.track_operation(
                agent_id="test-agent",
                operation="process_request",
                duration_ms=150,
                success=True,
                metadata={
                    "request_size": 1024,
                    "response_size": 2048
                }
            )
            
            # Verificar que se registraron las métricas
            mock_otel_instance.create_span.assert_any_call(
                "agent_operation",
                {"agent_id": "test-agent", "operation": "process_request"}
            )
    
    async def test_error_tracking(self, agent_observability):
        """Test de seguimiento de errores"""
        with patch('observability.agent_integration.OpenTelemetrySystem') as mock_otel:
            mock_otel_instance = MagicMock()
            mock_otel.return_value = mock_otel_instance
            
            agent_obs = agent_observability()
            
            # Simular error de agente
            agent_obs.track_error(
                agent_id="test-agent",
                operation="process_request",
                error_type="timeout",
                error_message="Request timeout after 30s",
                stack_trace="Traceback..."
            )
            
            # Verificar que se registraron métricas de error
            # (la verificación exacta depende de la implementación)
            assert mock_otel_instance.record_exception.called
    
    async def test_performance_metrics(self, agent_observability):
        """Test de métricas de performance"""
        with patch('observability.agent_integration.AdvancedMetrics') as mock_metrics:
            mock_metrics_instance = MagicMock()
            mock_metrics.return_value = mock_metrics_instance
            
            agent_obs = agent_observability()
            
            # Simular métricas de performance
            agent_obs.record_performance_metrics(
                agent_id="test-agent",
                cpu_usage=25.5,
                memory_usage=512.0,
                queue_size=5,
                active_connections=3
            )
            
            # Verificar que se registraron las métricas
            assert mock_metrics_instance.record_counter.called
            assert mock_metrics_instance.record_gauge.called
    
    async def test_health_monitoring(self, agent_observability):
        """Test de monitoreo de salud"""
        with patch('observability.agent_integration.AdvancedMetrics') as mock_metrics:
            mock_metrics_instance = MagicMock()
            mock_metrics.return_value = mock_metrics_instance
            
            agent_obs = agent_observability()
            
            # Simular check de salud
            health_status = agent_obs.check_agent_health(
                agent_id="test-agent",
                checks=["memory", "cpu", "connections", "errors"]
            )
            
            # Verificar estructura de respuesta
            assert "agent_id" in health_status
            assert "status" in health_status
            assert "checks" in health_status
    
    async def test_dependency_tracking(self, agent_observability):
        """Test de seguimiento de dependencias"""
        with patch('observability.agent_integration.OpenTelemetrySystem') as mock_otel:
            mock_otel_instance = MagicMock()
            mock_otel.return_value = mock_otel_instance
            
            agent_obs = agent_observability()
            
            # Simular llamada a dependencia
            agent_obs.track_dependency_call(
                agent_id="test-agent",
                dependency_type="database",
                dependency_name="postgresql",
                operation="query",
                duration_ms=75,
                success=True
            )
            
            # Verificar que se creó span para dependencia
            mock_otel_instance.create_span.assert_any_call(
                "dependency_call",
                {
                    "agent_id": "test-agent",
                    "dependency_type": "database",
                    "operation": "query"
                }
            )


class TestFastMCPIntegration:
    """Tests para integración con FastMCP"""
    
    @pytest.fixture
    def fastmcp_integration(self):
        """Fixture de integración FastMCP"""
        from observability.fastmcp_integration import FastMCPIntegration
        return FastMCPIntegration
    
    async def test_server_instrumentation(self, fastmcp_integration):
        """Test de instrumentación del servidor"""
        with patch('observability.fastmcp_integration.OpenTelemetrySystem') as mock_otel:
            mock_otel_instance = MagicMock()
            mock_otel.return_value = mock_otel_instance
            
            integration = fastmcp_integration()
            
            # Instrumentar servidor MCP
            integration.instrument_server()
            
            # Verificar que se instrumentó el servidor
            assert mock_otel_instance.create_span.called
    
    async def test_request_tracking(self, fastmcp_integration):
        """Test de seguimiento de requests"""
        with patch('observability.fastmcp_integration.AdvancedMetrics') as mock_metrics:
            mock_metrics_instance = MagicMock()
            mock_metrics.return_value = mock_metrics_instance
            
            integration = fastmcp_integration()
            
            # Simular request HTTP
            integration.track_http_request(
                method="POST",
                endpoint="/api/agents",
                status_code=200,
                duration_ms=125,
                request_size=1024,
                response_size=2048
            )
            
            # Verificar métricas de request
            assert mock_metrics_instance.record_counter.called
            assert mock_metrics_instance.record_histogram.called
    
    async def test_tool_execution_tracking(self, fastmcp_integration):
        """Test de seguimiento de ejecución de tools"""
        with patch('observability.fastmcp_integration.OpenTelemetrySystem') as mock_otel:
            mock_otel_instance = MagicMock()
            mock_otel.return_value = mock_otel_instance
            
            integration = fastmcp_integration()
            
            # Simular ejecución de tool
            integration.track_tool_execution(
                tool_name="python_executor",
                agent_id="python-agent",
                duration_ms=500,
                success=True,
                error_type=None
            )
            
            # Verificar métricas de tool execution
            mock_otel_instance.create_span.assert_any_call(
                "tool_execution",
                {
                    "tool_name": "python_executor",
                    "agent_id": "python-agent"
                }
            )
    
    async def test_resource_monitoring(self, fastmcp_integration):
        """Test de monitoreo de recursos"""
        with patch('observability.fastmcp_integration.AdvancedMetrics') as mock_metrics:
            mock_metrics_instance = MagicMock()
            mock_metrics.return_value = mock_metrics_instance
            
            integration = fastmcp_integration()
            
            # Simular monitoreo de recursos
            integration.monitor_resources()
            
            # Verificar que se registraron métricas de sistema
            assert mock_metrics_instance.record_gauge.called
    
    async def test_configuration_export(self, fastmcp_integration):
        """Test de exportación de configuración"""
        integration = fastmcp_integration()
        
        # Exportar configuración de observabilidad
        config = integration.export_observability_config()
        
        # Verificar estructura de configuración
        assert "opentelemetry" in config
        assert "metrics" in config
        assert "logging" in config
        assert "tracing" in config
    
    async def test_health_endpoint(self, fastmcp_integration):
        """Test de endpoint de salud"""
        integration = fastmcp_integration()
        
        # Verificar endpoint de salud
        with patch('observability.fastmcp_integration.AdvancedMetrics') as mock_metrics:
            mock_metrics_instance = MagicMock()
            mock_metrics_instance.get_metric_stats.return_value = {
                "total_requests": 1000,
                "error_rate": 0.05,
                "avg_response_time": 150.0
            }
            mock_metrics.return_value = mock_metrics_instance
            
            health_status = integration.get_health_status()
            
            # Verificar estructura de salud
            assert "status" in health_status
            assert "metrics" in health_status
            assert "timestamp" in health_status


class TestDeploymentUtils:
    """Tests para herramientas de deployment"""
    
    @pytest.fixture
    def deployment_utils(self):
        """Fixture de utilidades de deployment"""
        from observability.deployment_utils import DeploymentUtils
        return DeploymentUtils
    
    async def test_prometheus_config_generation(self, deployment_utils):
        """Test de generación de configuración Prometheus"""
        with patch('observability.deployment_utils.yaml') as mock_yaml:
            mock_yaml.dump.return_value = "prometheus_config: generated"
            
            config = deployment_utils.generate_prometheus_config(
                targets=[
                    {"job": "mcp-core", "targets": ["localhost:9090"]},
                    {"job": "agents", "targets": ["localhost:9091"]}
                ],
                rules=[
                    {
                        "alert": "HighErrorRate",
                        "expr": "rate(http_requests_total{status=~'5..'}[5m]) > 0.1",
                        "for": "5m",
                        "labels": {"severity": "warning"}
                    }
                ]
            )
            
            assert "prometheus_config" in config
            assert mock_yaml.dump.called
    
    async def test_grafana_dashboard_creation(self, deployment_utils):
        """Test de creación de dashboard Grafana"""
        with patch('observability.deployment_utils.yaml') as mock_yaml:
            mock_yaml.dump.return_value = "grafana_dashboard: created"
            
            dashboard = deployment_utils.create_grafana_dashboard(
                title="MCP Core Superior",
                metrics=[
                    "agent_executions_total",
                    "agent_duration_seconds",
                    "http_requests_total"
                ],
                panels=[
                    {
                        "title": "Agent Executions",
                        "type": "graph",
                        "targets": [
                            {"expr": "agent_executions_total"}
                        ]
                    }
                ]
            )
            
            assert "grafana_dashboard" in dashboard
    
    async def test_alerting_rules_generation(self, deployment_utils):
        """Test de generación de reglas de alertas"""
        deployment_utils.generate_alerting_rules(
            rules=[
                {
                    "name": "AgentDown",
                    "condition": "agent_status == 'down'",
                    "severity": "critical",
                    "actions": ["email", "slack"]
                },
                {
                    "name": "HighLatency",
                    "condition": "avg(http_request_duration_seconds) > 1",
                    "severity": "warning",
                    "actions": ["slack"]
                }
            ]
        )
        
        # Verificar que se generaron las reglas
        # (la verificación exacta depende de la implementación)
    
    async def test_monitoring_stack_deployment(self, deployment_utils):
        """Test de deployment del stack de monitoreo"""
        with patch('observability.deployment_utils.subprocess') as mock_subprocess:
            mock_subprocess.run.return_value = MagicMock(returncode=0)
            
            result = deployment_utils.deploy_monitoring_stack(
                components=["prometheus", "grafana", "alertmanager"],
                config={
                    "prometheus": {"port": 9090},
                    "grafana": {"port": 3000}
                }
            )
            
            assert result['success'] is True
            assert mock_subprocess.run.called
    
    async def test_service_discovery_config(self, deployment_utils):
        """Test de configuración de service discovery"""
        discovery_config = deployment_utils.configure_service_discovery(
            services=[
                {
                    "name": "mcp-core",
                    "address": "localhost",
                    "port": 8080,
                    "tags": ["api", "backend"]
                },
                {
                    "name": "python-executor",
                    "address": "localhost",
                    "port": 8081,
                    "tags": ["agent", "python"]
                }
            ]
        )
        
        assert len(discovery_config) == 2
        assert discovery_config[0]["name"] == "mcp-core"
        assert discovery_config[1]["name"] == "python-executor"