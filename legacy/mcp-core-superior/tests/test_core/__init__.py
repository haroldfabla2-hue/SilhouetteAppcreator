"""
Test suite para el Core System del MCP Core Superior

Cubre:
- Configuración centralizada
- FastMCP Server
- Sistema de orquestación
- Excepciones del sistema
- Deployer system
- Health metrics
- Zero-downtime deployment
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch, call
from typing import Dict, Any, List
from pathlib import Path
import json

# Test marks
pytestmark = [pytest.mark.core, pytest.mark.unit, pytest.mark.async_test]


class TestConfigSystem:
    """Tests para el sistema de configuración"""
    
    @pytest.fixture
    def config_system(self):
        """Fixture del sistema de configuración"""
        from core.config import MCPCoreSettings, Environment, LogLevel
        return MCPCoreSettings
    
    def test_basic_configuration(self, config_system):
        """Test de configuración básica"""
        # Crear instancia de configuración
        settings = config_system(
            environment=Environment.DEVELOPMENT,
            debug=True,
            host="localhost",
            port=8080
        )
        
        assert settings.environment == Environment.DEVELOPMENT
        assert settings.debug is True
        assert settings.host == "localhost"
        assert settings.port == 8080
    
    def test_environment_specific_config(self, config_system):
        """Test de configuración específica por entorno"""
        # Configuración para desarrollo
        dev_settings = config_system(environment=Environment.DEVELOPMENT)
        assert dev_settings.debug is True
        assert dev_settings.log_level == LogLevel.DEBUG
        
        # Configuración para producción
        prod_settings = config_system(environment=Environment.PRODUCTION)
        assert prod_settings.debug is False
        assert prod_settings.log_level == LogLevel.WARNING
    
    def test_database_configuration(self, config_system):
        """Test de configuración de base de datos"""
        settings = config_system(
            database_url="postgresql://user:pass@localhost:5432/test_db",
            database_pool_size=20,
            database_max_overflow=10
        )
        
        db_config = settings.get_database_config()
        
        assert db_config["pool_size"] == 20
        assert db_config["max_overflow"] == 10
        assert "pool_recycle" in db_config
    
    def test_redis_configuration(self, config_system):
        """Test de configuración de Redis"""
        settings = config_system(
            redis_url="redis://localhost:6379/0",
            redis_pool_size=15,
            redis_timeout=20
        )
        
        redis_config = settings.get_redis_config()
        
        assert redis_config["max_connections"] == 15
        assert redis_config["socket_timeout"] == 20
        assert redis_config["retry_on_timeout"] is True
    
    def test_validation_rules(self, config_system):
        """Test de reglas de validación"""
        # Test validación de JWT secret
        with pytest.raises(ValueError):
            config_system(
                environment=Environment.PRODUCTION,
                jwt_secret=""  # Secret vacío en producción
            )
        
        # Test validación de URL de base de datos
        with pytest.raises(ValueError):
            config_system(
                database_url="invalid_url"
            )
        
        # Test validación de tareas concurrentes
        with pytest.raises(ValueError):
            config_system(
                max_concurrent_tasks=0  # Valor inválido
            )
    
    def test_validation_quality_threshold(self, config_system):
        """Test de validación de umbral de calidad"""
        # Test valores válidos
        valid_settings = config_system(verification_quality_threshold=0.8)
        assert valid_settings.verification_quality_threshold == 0.8
        
        # Test valores inválidos
        with pytest.raises(ValueError):
            config_system(verification_quality_threshold=1.5)  # > 1.0
        
        with pytest.raises(ValueError):
            config_system(verification_quality_threshold=-0.1)  # < 0.0
    
    def test_security_configuration(self, config_system):
        """Test de configuración de seguridad"""
        settings = config_system(
            jwt_secret="test_secret",
            jwt_algorithm="HS256",
            jwt_expiration_hours=24,
            rate_limit_enabled=True,
            rate_limit_requests=100
        )
        
        security_config = settings.get_security_config()
        
        assert security_config["jwt_secret"] == "test_secret"
        assert security_config["jwt_algorithm"] == "HS256"
        assert security_config["rate_limit_requests"] == 100
    
    def test_environment_detection(self, config_system):
        """Test de detección de entorno"""
        # Desarrollo
        dev_settings = config_system(environment=Environment.DEVELOPMENT)
        assert dev_settings.is_development() is True
        assert dev_settings.is_production() is False
        
        # Producción
        prod_settings = config_system(environment=Environment.PRODUCTION)
        assert prod_settings.is_development() is False
        assert prod_settings.is_production() is True
    
    def test_vector_db_configuration(self, config_system):
        """Test de configuración de Vector DB"""
        settings = config_system(
            vector_db_url="postgresql://user:pass@localhost:5432/vector_db",
            embedding_model="text-embedding-ada-002",
            embedding_dimension=1536
        )
        
        vector_config = settings.get_vector_db_config()
        
        assert "server_settings" in vector_config
        assert vector_config["server_settings"]["jit"] == "off"
    
    def test_streaming_configuration(self, config_system):
        """Test de configuración de streaming"""
        settings = config_system(
            streaming_enabled=True,
            streaming_frequency=2.0,
            streaming_max_duration=7200,
            streaming_buffer_size=2000
        )
        
        assert settings.streaming_enabled is True
        assert settings.streaming_frequency == 2.0
        assert settings.streaming_max_duration == 7200
    
    def test_cors_configuration(self, config_system):
        """Test de configuración de CORS"""
        settings = config_system(
            cors_enabled=True,
            cors_origins=["http://localhost:3000", "https://app.example.com"],
            cors_methods=["GET", "POST", "PUT", "DELETE"],
            cors_headers=["Authorization", "Content-Type"]
        )
        
        assert settings.cors_enabled is True
        assert len(settings.cors_origins) == 2
        assert "DELETE" in settings.cors_methods
        assert "Authorization" in settings.cors_headers
    
    def test_dependency_validation(self, config_system):
        """Test de validación de dependencias"""
        # Variables requeridas en producción
        with patch.dict(os.environ, {
            "MCP_CORE_JWT_SECRET": "production_secret",
            "MCP_CORE_DATABASE_URL": "postgresql://test:test@localhost:5432/test_db"
        }):
            # No debería lanzar excepción
            try:
                settings = config_system(environment=Environment.PRODUCTION)
                assert settings.jwt_secret == "production_secret"
            except ValueError:
                pytest.fail("No debería lanzar ValueError con variables configuradas")


class TestFastMCPServer:
    """Tests para el servidor FastMCP"""
    
    @pytest.fixture
    def fastmcp_server(self):
        """Fixture del servidor FastMCP"""
        from core.fastmcp_server import FastMCPServer
        return FastMCPServer
    
    async def test_server_initialization(self, fastmcp_server):
        """Test de inicialización del servidor"""
        server = fastmcp_server()
        
        with patch.object(server, '_setup_routes') as mock_routes:
            with patch.object(server, '_setup_middleware') as mock_middleware:
                with patch.object(server, '_initialize_agents') as mock_agents:
                    
                    result = await server.initialize()
                    
                    assert result['success'] is True
                    assert server.initialized is True
                    assert mock_routes.called
                    assert mock_middleware.called
                    assert mock_agents.called
    
    async def test_server_start_stop(self, fastmcp_server):
        """Test de inicio y parada del servidor"""
        server = fastmcp_server()
        
        with patch('asyncio.create_server') as mock_create_server:
            mock_server = AsyncMock()
            mock_create_server.return_value = mock_server
            
            # Iniciar servidor
            with patch.object(server, '_start_server') as mock_start:
                mock_start.return_value = {"server_started": True}
                
                start_result = await server.start()
                assert start_result['success'] is True
            
            # Parar servidor
            with patch.object(server, '_stop_server') as mock_stop:
                mock_stop.return_value = {"server_stopped": True}
                
                stop_result = await server.stop()
                assert stop_result['success'] is True
    
    async def test_request_handling(self, fastmcp_server):
        """Test de manejo de requests"""
        server = fastmcp_server()
        
        # Mock de request
        request_data = {
            "operation": "process_request",
            "agent_id": "python_executor",
            "parameters": {"code": "print('Hello')"}
        }
        
        with patch.object(server, '_route_request') as mock_route:
            mock_route.return_value = {
                "success": True,
                "result": {"output": "Hello", "execution_time": 0.05}
            }
            
            response = await server.handle_request(request_data)
            
            assert response['success'] is True
            assert 'result' in response
            assert mock_route.called
    
    async def test_agent_registration(self, fastmcp_server):
        """Test de registro de agentes"""
        server = fastmcp_server()
        
        agent_config = {
            "agent_id": "test_agent",
            "agent_type": "python_executor",
            "capabilities": ["code_execution", "data_analysis"],
            "configuration": {"timeout": 30, "memory_limit": 512}
        }
        
        with patch.object(server, '_register_agent') as mock_register:
            mock_register.return_value = {"registered": True}
            
            result = await server.register_agent(agent_config)
            
            assert result['success'] is True
            assert mock_register.called
    
    async def test_streaming_support(self, fastmcp_server):
        """Test de soporte de streaming"""
        server = fastmcp_server()
        
        # Mock de stream de datos
        async def generate_data():
            for i in range(5):
                yield {"data": f"chunk_{i}"}
        
        with patch.object(server, '_handle_stream') as mock_handle:
            mock_handle.return_value = {"streamed": True}
            
            stream_response = await server.handle_streaming_request(
                operation="long_running_task",
                stream_handler=generate_data
            )
            
            assert stream_response['success'] is True
            assert mock_handle.called
    
    async def test_health_check_endpoint(self, fastmcp_server):
        """Test de endpoint de health check"""
        server = fastmcp_server()
        
        with patch.object(server, '_check_health') as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "agents": {
                    "python_executor": "running",
                    "git_operations": "running",
                    "web_scraping": "stopped"
                },
                "uptime": 3600,
                "memory_usage": 256.5
            }
            
            health_result = await server.health_check()
            
            assert health_result['status'] in ["healthy", "degraded"]
            assert 'agents' in health_result
            assert 'uptime' in health_result
    
    async def test_metrics_endpoint(self, fastmcp_server):
        """Test de endpoint de métricas"""
        server = fastmcp_server()
        
        with patch.object(server, '_collect_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "requests_total": 1000,
                "requests_successful": 950,
                "requests_failed": 50,
                "avg_response_time": 0.15,
                "active_agents": 8,
                "memory_usage_mb": 512.0,
                "cpu_usage_percent": 25.5
            }
            
            metrics = await server.get_metrics()
            
            assert 'requests_total' in metrics
            assert 'avg_response_time' in metrics
            assert metrics['requests_total'] > 0
    
    async def test_error_handling(self, fastmcp_server):
        """Test de manejo de errores"""
        server = fastmcp_server()
        
        # Request que causa error
        invalid_request = {
            "operation": "nonexistent_operation",
            "agent_id": "invalid_agent"
        }
        
        with patch.object(server, '_handle_error') as mock_error:
            mock_error.return_value = {
                "success": False,
                "error": "Operation not found",
                "error_code": "OPERATION_NOT_FOUND"
            }
            
            error_response = await server.handle_request(invalid_request)
            
            assert error_response['success'] is False
            assert 'error' in error_response
            assert mock_error.called
    
    async def test_configuration_reload(self, fastmcp_server):
        """Test de recarga de configuración"""
        server = fastmcp_server()
        
        new_config = {
            "agents": {
                "python_executor": {"timeout": 60},
                "git_operations": {"max_concurrent": 5}
            },
            "server": {
                "max_requests": 1000,
                "timeout": 30
            }
        }
        
        with patch.object(server, '_reload_configuration') as mock_reload:
            mock_reload.return_value = {"reloaded": True}
            
            reload_result = await server.reload_configuration(new_config)
            
            assert reload_result['success'] is True
            assert mock_reload.called


class TestOrchestrationSystem:
    """Tests para el sistema de orquestación"""
    
    @pytest.fixture
    def orchestration_system(self):
        """Fixture del sistema de orquestación"""
        from orchestrator.multi_agent_orchestrator import MultiAgentOrchestrator
        return MultiAgentOrchestrator
    
    async def test_orchestrator_initialization(self, orchestration_system):
        """Test de inicialización del orquestador"""
        orchestrator = orchestration_system()
        
        with patch.object(orchestrator, '_initialize_agents') as mock_init:
            with patch.object(orchestrator, '_setup_communication') as mock_comm:
                mock_init.return_value = True
                mock_comm.return_value = True
                
                result = await orchestrator.initialize()
                
                assert result['success'] is True
                assert orchestrator.initialized is True
                assert mock_init.called
                assert mock_comm.called
    
    async def test_task_orchestration(self, orchestration_system):
        """Test de orquestación de tareas"""
        orchestrator = orchestration_system()
        
        # Tarea compleja que requiere múltiples agentes
        complex_task = {
            "task_id": "complex_task_123",
            "type": "document_processing",
            "steps": [
                {"agent": "file_processor", "operation": "read", "file": "document.pdf"},
                {"agent": "python_executor", "operation": "extract_text", "input": "{previous_result}"},
                {"agent": "search_engine", "operation": "analyze_content", "content": "{extract_text_result}"},
                {"agent": "reasoner", "operation": "generate_summary", "data": "{analyze_content_result}"}
            ],
            "dependencies": {
                "python_executor": ["file_processor"],
                "search_engine": ["python_executor"],
                "reasoner": ["search_engine"]
            }
        }
        
        with patch.object(orchestrator, '_execute_task_steps') as mock_execute:
            mock_execute.return_value = {
                "completed": True,
                "step_results": {
                    "file_processor": {"success": True, "data": "pdf_content"},
                    "python_executor": {"success": True, "extracted": "text_content"},
                    "search_engine": {"success": True, "analysis": "analysis_result"},
                    "reasoner": {"success": True, "summary": "final_summary"}
                }
            }
            
            result = await orchestrator.orchestrate_task(complex_task)
            
            assert result['success'] is True
            assert result['completed'] is True
            assert mock_execute.called
    
    async def test_agent_coordination(self, orchestration_system):
        """Test de coordinación de agentes"""
        orchestrator = orchestration_system()
        
        # Solicitud que requiere coordinación entre agentes
        coordination_request = {
            "request_id": "coord_request_123",
            "type": "collaborative_analysis",
            "participants": [
                {"agent": "python_executor", "role": "data_processor"},
                {"agent": "search_engine", "role": "information_gatherer"},
                {"agent": "reasoner", "role": "analyst"}
            ],
            "shared_state": {"context": "user_query", "data": "input_data"}
        }
        
        with patch.object(orchestrator, '_coordinate_agents') as mock_coordinate:
            mock_coordinate.return_value = {
                "coordinated": True,
                "results": {
                    "python_executor": {"processed": True},
                    "search_engine": {"gathered": True},
                    "reasoner": {"analyzed": True}
                }
            }
            
            coordination_result = await orchestrator.coordinate_agents(coordination_request)
            
            assert coordination_result['success'] is True
            assert coordination_result['coordinated'] is True
            assert mock_coordinate.called
    
    async def test_workflow_management(self, orchestration_system):
        """Test de gestión de workflows"""
        orchestrator = orchestration_system()
        
        # Definir workflow
        workflow = {
            "workflow_id": "data_pipeline_123",
            "name": "Data Analysis Pipeline",
            "description": "Complete data processing and analysis workflow",
            "steps": [
                {
                    "step_id": "data_ingestion",
                    "agent": "file_processor",
                    "operation": "load_data",
                    "parameters": {"source": "database"}
                },
                {
                    "step_id": "data_cleaning",
                    "agent": "python_executor",
                    "operation": "clean_data",
                    "parameters": {"methods": ["remove_duplicates", "handle_nulls"]}
                },
                {
                    "step_id": "analysis",
                    "agent": "reasoner",
                    "operation": "analyze_patterns",
                    "parameters": {"algorithms": ["statistical", "ml"]}
                },
                {
                    "step_id": "reporting",
                    "agent": "reasoner",
                    "operation": "generate_report",
                    "parameters": {"format": "comprehensive"}
                }
            ],
            "parallel_groups": [
                {
                    "group_id": "concurrent_analysis",
                    "steps": ["data_ingestion", "initial_validation"]
                }
            ]
        }
        
        with patch.object(orchestrator, '_execute_workflow') as mock_execute:
            mock_execute.return_value = {
                "workflow_completed": True,
                "execution_time": 145.6,
                "step_results": {
                    "data_ingestion": {"success": True, "rows_processed": 10000},
                    "data_cleaning": {"success": True, "rows_clean": 9500},
                    "analysis": {"success": True, "patterns_found": 15},
                    "reporting": {"success": True, "report_generated": "report.pdf"}
                }
            }
            
            workflow_result = await orchestrator.execute_workflow(workflow)
            
            assert workflow_result['success'] is True
            assert workflow_result['workflow_completed'] is True
            assert mock_execute.called
    
    async def test_resource_allocation(self, orchestration_system):
        """Test de asignación de recursos"""
        orchestrator = orchestration_system()
        
        # Solicitudes de agentes por recursos
        resource_requests = [
            {
                "agent": "python_executor",
                "request": {"cpu": 2, "memory": 1024, "gpu": 1},
                "priority": "high"
            },
            {
                "agent": "search_engine",
                "request": {"cpu": 1, "memory": 512},
                "priority": "medium"
            },
            {
                "agent": "file_processor",
                "request": {"cpu": 1, "memory": 2048, "disk": 10},
                "priority": "low"
            }
        ]
        
        # Recursos disponibles
        available_resources = {
            "cpu": 8,
            "memory": 8192,
            "gpu": 2,
            "disk": 100
        }
        
        allocation_result = await orchestrator.allocate_resources(
            resource_requests,
            available_resources
        )
        
        assert 'allocations' in allocation_result
        assert 'resource_utilization' in allocation_result
        assert allocation_result['resource_utilization']['cpu'] <= 1.0
    
    async def test_load_balancing(self, orchestration_system):
        """Test de balanceador de carga"""
        orchestrator = orchestration_system()
        
        # Distribución de carga entre agentes
        load_data = {
            "agents": {
                "python_executor": {
                    "current_tasks": 5,
                    "max_capacity": 10,
                    "queue_size": 3,
                    "response_time": 0.15
                },
                "search_engine": {
                    "current_tasks": 2,
                    "max_capacity": 8,
                    "queue_size": 1,
                    "response_time": 0.08
                },
                "web_scraping": {
                    "current_tasks": 8,
                    "max_capacity": 6,
                    "queue_size": 10,
                    "response_time": 2.5
                }
            }
        }
        
        balancing_result = await orchestrator.balance_agent_load(load_data)
        
        assert 'rebalancing_needed' in balancing_result
        assert 'actions_taken' in balancing_result
        if balancing_result['rebalancing_needed']:
            assert len(balancing_result['actions_taken']) > 0
    
    async def test_fault_recovery(self, orchestration_system):
        """Test de recuperación ante fallos"""
        orchestrator = orchestration_system()
        
        # Simular fallo de agente
        agent_failure = {
            "agent_id": "python_executor_2",
            "failure_type": "timeout",
            "timestamp": "2025-11-04T05:43:15Z",
            "affected_tasks": ["task_1", "task_2", "task_3"]
        }
        
        with patch.object(orchestrator, '_handle_agent_failure') as mock_handle:
            mock_handle.return_value = {
                "recovery_performed": True,
                "tasks_rescheduled": 3,
                "backup_agent": "python_executor_1"
            }
            
            recovery_result = await orchestrator.handle_agent_failure(agent_failure)
            
            assert recovery_result['success'] is True
            assert recovery_result['recovery_performed'] is True
            assert recovery_result['tasks_rescheduled'] > 0
            assert mock_handle.called
    
    async def test_performance_monitoring(self, orchestration_system):
        """Test de monitoreo de performance"""
        orchestrator = orchestration_system()
        
        # Métricas de performance
        performance_data = {
            "total_tasks": 1000,
            "completed_tasks": 950,
            "failed_tasks": 50,
            "avg_execution_time": 1.25,
            "agent_utilization": {
                "python_executor": 0.75,
                "search_engine": 0.60,
                "git_operations": 0.45
            },
            "resource_efficiency": 0.82
        }
        
        monitoring_result = await orchestrator.get_performance_metrics(performance_data)
        
        assert 'success_rate' in monitoring_result
        assert 'efficiency_score' in monitoring_result
        assert 'recommendations' in monitoring_result
        assert monitoring_result['success_rate'] == 0.95


class TestSystemExceptions:
    """Tests para excepciones del sistema"""
    
    @pytest.fixture
    def system_exceptions(self):
        """Fixture de excepciones del sistema"""
        from core.exceptions import (
            MCPException,
            AgentException,
            ConfigurationException,
            OrchestrationException,
            SecurityException
        )
        return {
            'mcp': MCPException,
            'agent': AgentException,
            'config': ConfigurationException,
            'orchestration': OrchestrationException,
            'security': SecurityException
        }
    
    def test_mcp_exception(self, system_exceptions):
        """Test de excepción MCP"""
        exception_class = system_exceptions['mcp']
        
        # Test con mensaje
        try:
            raise exception_class("MCP system error")
        except exception_class as e:
            assert str(e) == "MCP system error"
            assert e.error_code is None
        
        # Test con código de error
        try:
            raise exception_class("Invalid request", error_code="INVALID_REQUEST")
        except exception_class as e:
            assert str(e) == "Invalid request"
            assert e.error_code == "INVALID_REQUEST"
    
    def test_agent_exception(self, system_exceptions):
        """Test de excepción de agente"""
        exception_class = system_exceptions['agent']
        
        try:
            raise exception_class(
                "Agent timeout",
                agent_id="python_executor",
                operation="execute_code"
            )
        except exception_class as e:
            assert "Agent timeout" in str(e)
            assert e.agent_id == "python_executor"
            assert e.operation == "execute_code"
    
    def test_configuration_exception(self, system_exceptions):
        """Test de excepción de configuración"""
        exception_class = system_exceptions['config']
        
        try:
            raise exception_class(
                "Invalid database URL",
                config_key="database_url",
                config_value="invalid_url"
            )
        except exception_class as e:
            assert "Invalid database URL" in str(e)
            assert e.config_key == "database_url"
            assert e.config_value == "invalid_url"
    
    def test_orchestration_exception(self, system_exceptions):
        """Test de excepción de orquestación"""
        exception_class = system_exceptions['orchestration']
        
        try:
            raise exception_class(
                "Task coordination failed",
                task_id="task_123",
                failed_agents=["python_executor", "search_engine"]
            )
        except exception_class as e:
            assert "Task coordination failed" in str(e)
            assert e.task_id == "task_123"
            assert "python_executor" in e.failed_agents
    
    def test_security_exception(self, system_exceptions):
        """Test de excepción de seguridad"""
        exception_class = system_exceptions['security']
        
        try:
            raise exception_class(
                "Authentication failed",
                security_violation="invalid_token",
                severity="high"
            )
        except exception_class as e:
            assert "Authentication failed" in str(e)
            assert e.security_violation == "invalid_token"
            assert e.severity == "high"


class TestHealthMetrics:
    """Tests para métricas de salud"""
    
    @pytest.fixture
    def health_metrics(self):
        """Fixture de métricas de salud"""
        from core.health_metrics import HealthMetrics
        return HealthMetrics
    
    async def test_health_assessment(self, health_metrics):
        """Test de evaluación de salud"""
        metrics = health_metrics()
        
        # Métricas del sistema
        system_metrics = {
            "cpu_usage": 45.5,
            "memory_usage": 62.3,
            "disk_usage": 35.0,
            "network_io": {"sent": 1024, "received": 2048},
            "active_connections": 25,
            "response_time": 0.15
        }
        
        # Métricas de agentes
        agent_metrics = {
            "python_executor": {"status": "healthy", "tasks_completed": 100, "errors": 2},
            "git_operations": {"status": "healthy", "tasks_completed": 50, "errors": 0},
            "web_scraping": {"status": "degraded", "tasks_completed": 30, "errors": 5}
        }
        
        health_assessment = await metrics.assess_system_health(
            system_metrics,
            agent_metrics
        )
        
        assert 'overall_health' in health_assessment
        assert 'system_health' in health_assessment
        assert 'agent_health' in health_assessment
        assert 'recommendations' in health_assessment
    
    async def test_health_monitoring(self, health_metrics):
        """Test de monitoreo de salud continuo"""
        metrics = health_metrics()
        
        with patch.object(metrics, '_collect_health_data') as mock_collect:
            mock_collect.return_value = {
                "timestamp": "2025-11-04T05:43:15Z",
                "health_score": 0.85,
                "critical_issues": [],
                "warnings": ["web_scraping_degraded"]
            }
            
            health_data = await metrics.monitor_health()
            
            assert health_data['health_score'] >= 0
            assert health_data['health_score'] <= 1
            assert 'timestamp' in health_data
    
    async def test_threshold_monitoring(self, health_metrics):
        """Test de monitoreo de umbrales"""
        metrics = health_metrics()
        
        # Configurar umbrales
        thresholds = {
            "cpu_usage": {"warning": 70, "critical": 90},
            "memory_usage": {"warning": 80, "critical": 95},
            "response_time": {"warning": 1.0, "critical": 5.0}
        }
        
        current_values = {
            "cpu_usage": 75,
            "memory_usage": 85,
            "response_time": 2.5
        }
        
        violations = metrics.check_health_thresholds(current_values, thresholds)
        
        assert 'threshold_violations' in violations
        assert 'warnings' in violations
        assert 'critical_alerts' in violations
        assert any("cpu_usage" in str(v) for v in violations['warnings'])
    
    async def test_health_alerts(self, health_metrics):
        """Test de alertas de salud"""
        metrics = health_metrics()
        
        # Condiciones que deberían generar alertas
        alert_conditions = [
            {
                "condition": "high_error_rate",
                "value": 0.25,
                "threshold": 0.10,
                "severity": "critical"
            },
            {
                "condition": "slow_response_time",
                "value": 3.5,
                "threshold": 2.0,
                "severity": "warning"
            }
        ]
        
        alerts = await metrics.generate_health_alerts(alert_conditions)
        
        assert isinstance(alerts, list)
        assert len(alerts) > 0
        
        for alert in alerts:
            assert 'condition' in alert
            assert 'severity' in alert
            assert 'timestamp' in alert


class TestDeployerSystem:
    """Tests para el sistema de deployment"""
    
    @pytest.fixture
    def deployer_system(self):
        """Fixture del sistema de deployment"""
        from core.zero_downtime_deployer import ZeroDowntimeDeployer
        return ZeroDowntimeDeployer
    
    async def test_deployer_initialization(self, deployer_system):
        """Test de inicialización del deployer"""
        deployer = deployer_system()
        
        with patch.object(deployer, '_setup_deployment_environment') as mock_setup:
            mock_setup.return_value = True
            
            result = await deployer.initialize()
            
            assert result['success'] is True
            assert deployer.initialized is True
            assert mock_setup.called
    
    async def test_zero_downtime_deployment(self, deployer_system):
        """Test de deployment sin downtime"""
        deployer = deployer_system()
        
        # Configuración de deployment
        deployment_config = {
            "version": "1.2.0",
            "new_services": [
                {"name": "python_executor", "image": "mcp/python-executor:1.2.0"},
                {"name": "search_engine", "image": "mcp/search-engine:1.2.0"}
            ],
            "rollback_strategy": "blue_green",
            "health_check_timeout": 300
        }
        
        with patch.object(deployer, '_execute_zero_downtime_deploy') as mock_deploy:
            mock_deploy.return_value = {
                "deployment_successful": True,
                "deployment_time": 180.5,
                "services_deployed": 2,
                "rollback_available": True
            }
            
            deployment_result = await deployer.deploy_zero_downtime(deployment_config)
            
            assert deployment_result['success'] is True
            assert deployment_result['deployment_successful'] is True
            assert mock_deploy.called
    
    async def test_blue_green_deployment(self, deployer_system):
        """Test de deployment blue-green"""
        deployer = deployer_system()
        
        # Configuración blue-green
        blue_green_config = {
            "service_name": "mcp-core",
            "blue_version": "1.1.0",
            "green_version": "1.2.0",
            "switch_strategy": "gradual",
            "switch_duration": 300
        }
        
        with patch.object(deployer, '_execute_blue_green_deploy') as mock_blue_green:
            mock_blue_green.return_value = {
                "blue_green_deployment": True,
                "switch_completed": True,
                "traffic_switch_percentage": 100.0
            }
            
            bg_result = await deployer.deploy_blue_green(blue_green_config)
            
            assert bg_result['success'] is True
            assert bg_result['blue_green_deployment'] is True
            assert mock_blue_green.called
    
    async def test_rolling_update(self, deployer_system):
        """Test de actualización rolling"""
        deployer = deployer_system()
        
        # Configuración rolling update
        rolling_config = {
            "service_name": "mcp-agents",
            "instances": 5,
            "new_image": "mcp/agents:1.2.0",
            "update_strategy": "rolling",
            "max_unavailable": 1,
            "max_surge": 1
        }
        
        with patch.object(deployer, '_execute_rolling_update') as mock_rolling:
            mock_rolling.return_value = {
                "rolling_update_successful": True,
                "instances_updated": 5,
                "instances_remaining": 0,
                "average_update_time": 45.2
            }
            
            rolling_result = await deployer.deploy_rolling_update(rolling_config)
            
            assert rolling_result['success'] is True
            assert rolling_result['rolling_update_successful'] is True
            assert mock_rolling.called
    
    async def test_deployment_rollback(self, deployer_system):
        """Test de rollback de deployment"""
        deployer = deployer_system()
        
        # Configuración de rollback
        rollback_config = {
            "deployment_id": "deploy_123",
            "previous_version": "1.1.0",
            "reason": "Service instability detected",
            "rollback_strategy": "automatic"
        }
        
        with patch.object(deployer, '_execute_rollback') as mock_rollback:
            mock_rollback.return_value = {
                "rollback_successful": True,
                "rollback_time": 120.3,
                "services_rolled_back": 2,
                "traffic_restored": True
            }
            
            rollback_result = await deployer.rollback_deployment(rollback_config)
            
            assert rollback_result['success'] is True
            assert rollback_result['rollback_successful'] is True
            assert mock_rollback.called
    
    async def test_deployment_health_monitoring(self, deployer_system):
        """Test de monitoreo de salud durante deployment"""
        deployer = deployer_system()
        
        # Deployment en progreso
        deployment_id = "deploy_123"
        
        with patch.object(deployer, '_monitor_deployment_health') as mock_monitor:
            mock_monitor.return_value = {
                "deployment_healthy": True,
                "services_health": {
                    "python_executor": {"status": "healthy", "response_time": 0.12},
                    "search_engine": {"status": "healthy", "response_time": 0.08},
                    "web_scraping": {"status": "degraded", "response_time": 1.5}
                },
                "overall_score": 0.85,
                "issues_detected": ["web_scraping_degraded"]
            }
            
            health_status = await deployer.monitor_deployment_health(deployment_id)
            
            assert health_status['deployment_healthy'] is True
            assert 'services_health' in health_status
            assert 'overall_score' in health_status
            assert mock_monitor.called
    
    async def test_deployment_validation(self, deployer_system):
        """Test de validación de deployment"""
        deployer = deployer_system()
        
        # Configuración de validación
        validation_config = {
            "deployment_id": "deploy_123",
            "validation_tests": [
                {"test": "health_check", "timeout": 30},
                {"test": "load_test", "duration": 60},
                {"test": "integration_test", "timeout": 120}
            ],
            "success_criteria": {
                "health_check_passed": True,
                "load_test_max_response_time": 2.0,
                "integration_test_passed": True
            }
        }
        
        with patch.object(deployer, '_validate_deployment') as mock_validate:
            mock_validate.return_value = {
                "validation_successful": True,
                "tests_passed": 3,
                "tests_failed": 0,
                "validation_score": 1.0
            }
            
            validation_result = await deployer.validate_deployment(validation_config)
            
            assert validation_result['success'] is True
            assert validation_result['validation_successful'] is True
            assert mock_validate.called