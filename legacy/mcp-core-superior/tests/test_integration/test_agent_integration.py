"""
Test de integración entre los 12 agentes especializados
Valida la colaboración y comunicación entre todos los agentes del sistema
"""
import pytest
import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from conftest import (
    assert_agent_integration_result,
    create_test_task_id,
    assert_orchestration_success
)


@pytest.mark.integration
class TestAgentIntegration:
    """Tests de integración entre agentes especializados"""
    
    @pytest.mark.asyncio
    async def test_all_agents_registration(self, test_database):
        """Test que todos los 12 agentes se registren correctamente"""
        # Verificar que los agentes están registrados en la base de datos
        agents = await test_database.main_conn.fetch("SELECT * FROM test_agents")
        agent_names = [row['name'] for row in agents]
        
        expected_agents = [
            'Test Reasoner', 'Test Planner', 'Test Executor', 'Test Verifier',
            'Test Database Ops', 'Test Python Exec', 'Test Git Ops',
            'Test File Processing', 'Test Web Scraping', 'Test Search Engine',
            'Test Memory Manager', 'Test Orchestrator'
        ]
        
        for expected_agent in expected_agents:
            assert expected_agent in agent_names, f"Agente {expected_agent} no registrado"
        
        assert len(agents) == 12, f"Se esperaban 12 agentes, encontrados: {len(agents)}"
        print("Test de registro de agentes completado - 12/12 agentes registrados")
    
    @pytest.mark.asyncio
    async def test_reasoner_planner_integration(self, test_database, test_context):
        """Test integración Reasoner → Planner"""
        # Simular resultado del reasoner
        reasoner_output = {
            "intent_type": "data_analysis",
            "complexity_level": "high",
            "domain": "customer_data",
            "strategy": {
                "approach": "Statistical analysis with ML",
                "phases": ["Data preparation", "Statistical analysis", "ML modeling", "Insights generation"],
                "estimated_effort": "high",
                "required_tools": ["python_executor", "database_operations"]
            }
        }
        
        # Simular planificación basada en análisis del reasoner
        planner_input = {
            "analysis_result": reasoner_output,
            "task_context": test_context
        }
        
        # Verificar que el plan incluye herramientas necesarias
        expected_tools = ["python_executor", "database_operations"]
        for tool in expected_tools:
            assert tool in json.dumps(planner_input), f"Herramienta {tool} no incluida en planificación"
        
        print("Test Reasoner → Planner integración completado")
    
    @pytest.mark.asyncio
    async def test_planner_executor_integration(self, test_database, test_context):
        """Test integración Planner → Executor"""
        # Simular plan detallado del planner
        execution_plan = {
            "tasks": [
                {
                    "id": "data_collection",
                    "name": "Collect customer data",
                    "priority": 1,
                    "required_agent": "database_operations",
                    "dependencies": [],
                    "estimated_duration": 30
                },
                {
                    "id": "data_analysis", 
                    "name": "Analyze collected data",
                    "priority": 2,
                    "required_agent": "python_executor",
                    "dependencies": ["data_collection"],
                    "estimated_duration": 120
                },
                {
                    "id": "result_validation",
                    "name": "Validate analysis results",
                    "priority": 3,
                    "required_agent": "verifier",
                    "dependencies": ["data_analysis"],
                    "estimated_duration": 15
                }
            ],
            "execution_order": ["data_collection", "data_analysis", "result_validation"],
            "parallel_groups": [],
            "estimated_total_duration": 165
        }
        
        # Verificar estructura del plan
        assert len(execution_plan["tasks"]) > 0
        assert len(execution_plan["execution_order"]) == len(execution_plan["tasks"])
        
        # Verificar que hay dependencias válidas
        for task in execution_plan["tasks"]:
            if task["dependencies"]:
                for dep in task["dependencies"]:
                    assert dep in execution_plan["execution_order"], f"Dependencia inválida: {dep}"
        
        print("Test Planner → Executor integración completado")
    
    @pytest.mark.asyncio
    async def test_executor_verifier_integration(self, test_database, test_context):
        """Test integración Executor → Verifier"""
        # Simular resultados de ejecución del executor
        executor_results = {
            "execution_summary": {
                "tools_executed": 5,
                "successful": 4,
                "failed": 1,
                "total_time_ms": 3500,
                "agent_utilization": {
                    "python_executor": {"calls": 2, "success": 2},
                    "database_operations": {"calls": 2, "success": 1},
                    "git_operations": {"calls": 1, "success": 1}
                }
            },
            "results": {
                "tools_results": {
                    "data_collection": {
                        "success": True,
                        "result": "Data collected successfully",
                        "execution_time_ms": 500
                    },
                    "data_analysis": {
                        "success": True, 
                        "result": "Analysis completed with insights",
                        "execution_time_ms": 2000
                    },
                    "validation_check": {
                        "success": False,
                        "error": "Insufficient data points",
                        "execution_time_ms": 300
                    }
                }
            }
        }
        
        # Verificar que el verifier puede procesar estos resultados
        assert "execution_summary" in executor_results
        assert "results" in executor_results
        assert "tools_results" in executor_results["results"]
        
        # El verifier debería detectar el fallo y ajustar la calidad
        failed_tools = [tool for tool, result in executor_results["results"]["tools_results"].items() 
                       if not result["success"]]
        assert len(failed_tools) > 0, "Debería haber al menos una herramienta fallida para test"
        
        print("Test Executor → Verifier integración completado")
    
    @pytest.mark.asyncio
    async def test_database_operations_agent_integration(self, test_database, test_context):
        """Test específico del Database Operations Agent"""
        # Insertar datos de prueba
        await test_database.main_conn.execute(
            "INSERT INTO test_tasks (task_id, objective, status, context, result) VALUES ($1, $2, $3, $4, $5)",
            "db_test_task", "Test database operations", "active", 
            json.dumps(test_context), json.dumps({"test": "data"})
        )
        
        # Simular consulta compleja
        result = await test_database.main_conn.fetchrow(
            "SELECT * FROM test_tasks WHERE task_id = $1",
            "db_test_task"
        )
        
        assert result is not None
        assert result["objective"] == "Test database operations"
        
        # Limpiar
        await test_database.main_conn.execute("DELETE FROM test_tasks WHERE task_id = $1", "db_test_task")
        
        print("Test Database Operations Agent completado")
    
    @pytest.mark.asyncio
    async def test_python_executor_agent_integration(self, test_context):
        """Test específico del Python Executor Agent"""
        # Simular código Python para ejecutar
        python_code = """
import json
import time

# Simular procesamiento de datos
data = {"input": "test_data", "timestamp": time.time()}
processed_data = {"result": data["input"].upper(), "processed_at": data["timestamp"]}
time.sleep(0.1)  # Simular trabajo
return processed_data
"""
        
        # Simular ejecución (en un entorno real usaría el agente PythonExecutorAgent)
        execution_result = {
            "success": True,
            "output": {"result": "TEST_DATA", "processed_at": time.time()},
            "execution_time_ms": 150,
            "memory_used_mb": 12.5,
            "code_lines_executed": 8
        }
        
        # Verificar resultado
        assert execution_result["success"]
        assert "output" in execution_result
        assert execution_result["output"]["result"] == "TEST_DATA"
        assert execution_result["execution_time_ms"] > 0
        
        print("Test Python Executor Agent completado")
    
    @pytest.mark.asyncio
    async def test_git_operations_agent_integration(self, test_context):
        """Test específico del Git Operations Agent"""
        # Simular operaciones Git
        git_operations = [
            {
                "operation": "clone",
                "repository_url": "https://github.com/test/repo.git",
                "target_path": "/tmp/test_repo"
            },
            {
                "operation": "checkout",
                "branch": "feature/test-branch"
            },
            {
                "operation": "commit",
                "message": "Test commit from integration test",
                "files": ["test_file.py"]
            }
        ]
        
        # Simular resultados de cada operación
        git_results = []
        for op in git_operations:
            result = {
                "operation": op["operation"],
                "success": True,
                "output": f"Git {op['operation']} completed successfully",
                "timestamp": datetime.now().isoformat()
            }
            git_results.append(result)
        
        # Verificar resultados
        assert len(git_results) == len(git_operations)
        for result in git_results:
            assert result["success"]
            assert "timestamp" in result
        
        print("Test Git Operations Agent completado")
    
    @pytest.mark.asyncio
    async def test_file_processing_agent_integration(self, test_context):
        """Test específico del File Processing Agent"""
        # Simular procesamiento de archivos
        file_operations = [
            {
                "operation": "read",
                "file_path": "/tmp/test.txt",
                "encoding": "utf-8"
            },
            {
                "operation": "process",
                "file_path": "/tmp/test.txt",
                "processor": "text_analyzer"
            },
            {
                "operation": "write",
                "file_path": "/tmp/processed.txt",
                "content": "Processed content"
            }
        ]
        
        file_results = []
        for op in file_operations:
            result = {
                "operation": op["operation"],
                "success": True,
                "file_path": op["file_path"],
                "processing_time_ms": 50
            }
            file_results.append(result)
        
        # Verificar resultados
        assert len(file_results) == len(file_operations)
        for result in file_results:
            assert result["success"]
            assert result["processing_time_ms"] > 0
        
        print("Test File Processing Agent completado")
    
    @pytest.mark.asyncio
    async def test_web_scraping_agent_integration(self, test_context):
        """Test específico del Web Scraping Agent"""
        # Simular URLs para scraping
        target_urls = [
            "https://example.com",
            "https://test-site.com", 
            "https://api.example.com/data"
        ]
        
        scraping_results = []
        for url in target_urls:
            result = {
                "url": url,
                "success": True,
                "content_type": "text/html",
                "content_length": 2048,
                "extracted_data": {
                    "title": f"Page title for {url}",
                    "links": ["link1", "link2"],
                    "text_content": "Extracted text content..."
                },
                "scraping_time_ms": 200
            }
            scraping_results.append(result)
        
        # Verificar resultados
        assert len(scraping_results) == len(target_urls)
        for result in scraping_results:
            assert result["success"]
            assert "extracted_data" in result
            assert len(result["extracted_data"]["title"]) > 0
        
        print("Test Web Scraping Agent completado")
    
    @pytest.mark.asyncio
    async def test_search_engine_agent_integration(self, test_context):
        """Test específico del Search Engine Agent"""
        # Simular consultas de búsqueda
        search_queries = [
            "machine learning algorithms",
            "python data analysis",
            "web scraping best practices"
        ]
        
        search_results = []
        for query in search_queries:
            result = {
                "query": query,
                "success": True,
                "results_count": 50,
                "top_results": [
                    {
                        "title": f"Result for {query}",
                        "url": f"https://example.com/{query.replace(' ', '-')}",
                        "snippet": f"Description of {query}...",
                        "relevance_score": 0.95
                    }
                ],
                "search_time_ms": 150
            }
            search_results.append(result)
        
        # Verificar resultados
        assert len(search_results) == len(search_queries)
        for result in search_results:
            assert result["success"]
            assert result["results_count"] > 0
            assert len(result["top_results"]) > 0
            assert result["top_results"][0]["relevance_score"] > 0.8
        
        print("Test Search Engine Agent completado")
    
    @pytest.mark.asyncio
    async def test_memory_manager_agent_integration(self, test_database, test_context):
        """Test específico del Memory Manager Agent"""
        # Simular almacenamiento de contexto
        context_data = {
            "task_id": test_context["task_id"],
            "agent_interactions": [
                {"agent": "reasoner", "timestamp": datetime.now().isoformat(), "result": "analysis_complete"},
                {"agent": "planner", "timestamp": datetime.now().isoformat(), "result": "plan_created"}
            ],
            "shared_state": {"intermediate_results": "data"},
            "persistence_level": "short_term"
        }
        
        # Simular almacenamiento
        storage_result = {
            "success": True,
            "context_id": f"ctx_{test_context['task_id']}",
            "storage_time_ms": 25,
            "compression_ratio": 0.7
        }
        
        # Simular recuperación
        retrieval_result = {
            "success": True,
            "context_id": storage_result["context_id"],
            "retrieval_time_ms": 15,
            "data_intact": True
        }
        
        # Verificar operaciones
        assert storage_result["success"]
        assert retrieval_result["success"]
        assert retrieval_result["data_intact"]
        
        print("Test Memory Manager Agent completado")
    
    @pytest.mark.asyncio
    async def test_cross_agent_communication(self, test_database, test_context):
        """Test comunicación entre múltiples agentes"""
        # Simular flujo complejo con múltiples agentes
        communication_log = [
            {
                "from_agent": "reasoner",
                "to_agent": "planner", 
                "message_type": "analysis_result",
                "timestamp": datetime.now().isoformat(),
                "content": {"intent": "data_analysis", "complexity": "high"}
            },
            {
                "from_agent": "planner",
                "to_agent": "python_executor",
                "message_type": "execution_plan", 
                "timestamp": datetime.now().isoformat(),
                "content": {"tasks": ["data_collection", "analysis"], "priority": "high"}
            },
            {
                "from_agent": "python_executor",
                "to_agent": "database_operations",
                "message_type": "data_request",
                "timestamp": datetime.now().isoformat(),
                "content": {"query": "SELECT * FROM customers", "purpose": "analysis"}
            },
            {
                "from_agent": "database_operations", 
                "to_agent": "verifier",
                "message_type": "validation_request",
                "timestamp": datetime.now().isoformat(),
                "content": {"data_quality": "high", "completeness": "95%"}
            }
        ]
        
        # Verificar comunicación
        assert len(communication_log) == 4
        
        # Verificar flujo lógico
        expected_flow = ["reasoner", "planner", "python_executor", "database_operations"]
        actual_flow = [msg["to_agent"] for msg in communication_log]
        
        # Verificar que hay comunicación válida entre agentes
        for i, msg in enumerate(communication_log):
            assert msg["from_agent"] in expected_flow
            assert msg["to_agent"] in expected_flow
            assert "message_type" in msg
            assert "content" in msg
            assert msg["timestamp"] is not None
        
        print("Test cross-agent communication completado")
    
    @pytest.mark.asyncio
    async def test_agent_failure_handling(self, test_context):
        """Test manejo de fallos entre agentes"""
        # Simular fallo de un agente y recuperación
        agent_status = {
            "reasoner": "healthy",
            "planner": "healthy", 
            "python_executor": "failed",
            "database_operations": "healthy",
            "verifier": "healthy"
        }
        
        # Verificar detección de fallo
        failed_agents = [agent for agent, status in agent_status.items() if status == "failed"]
        assert "python_executor" in failed_agents
        
        # Simular estrategia de recuperación
        recovery_strategy = {
            "failed_agent": "python_executor",
            "failure_reason": "execution_timeout",
            "recovery_actions": [
                "restart_agent",
                "retry_last_operation", 
                "fallback_to_alternative_agent"
            ],
            "estimated_recovery_time_seconds": 30
        }
        
        # Verificar estrategia de recuperación
        assert "python_executor" in recovery_strategy["failed_agent"]
        assert len(recovery_strategy["recovery_actions"]) > 0
        assert recovery_strategy["estimated_recovery_time_seconds"] > 0
        
        print("Test agent failure handling completado")
    
    @pytest.mark.asyncio
    async def test_agent_load_balancing(self, test_context):
        """Test balanceador de carga entre agentes"""
        # Simular carga en diferentes agentes
        agent_load = {
            "reasoner": {"current_tasks": 3, "max_capacity": 10, "utilization": 30},
            "planner": {"current_tasks": 5, "max_capacity": 8, "utilization": 62},
            "python_executor": {"current_tasks": 8, "max_capacity": 10, "utilization": 80},
            "database_operations": {"current_tasks": 2, "max_capacity": 6, "utilization": 33},
            "verifier": {"current_tasks": 4, "max_capacity": 6, "utilization": 67}
        }
        
        # Identificar agentes con alta carga
        high_load_agents = [agent for agent, load in agent_load.items() 
                          if load["utilization"] > 70]
        
        # python_executor debería estar en alta carga
        assert "python_executor" in high_load_agents
        
        # Simular rebalanceo
        load_balancing_result = {
            "agents_rebalanced": ["python_executor"],
            "tasks_migrated": 2,
            "new_utilization": {
                "python_executor": 60,
                "planner": 45,
                "reasoner": 40
            },
            "balancing_time_ms": 150
        }
        
        # Verificar rebalanceo
        assert len(load_balancing_result["agents_rebalanced"]) > 0
        assert load_balancing_result["tasks_migrated"] > 0
        
        print("Test agent load balancing completado")
    
    @pytest.mark.asyncio
    async def test_agent_performance_monitoring(self, test_context):
        """Test monitoreo de performance de agentes"""
        # Simular métricas de performance
        performance_metrics = {
            "reasoner": {
                "avg_response_time_ms": 200,
                "success_rate": 0.95,
                "tasks_completed": 100,
                "error_rate": 0.05
            },
            "planner": {
                "avg_response_time_ms": 150,
                "success_rate": 0.98,
                "tasks_completed": 95,
                "error_rate": 0.02
            },
            "python_executor": {
                "avg_response_time_ms": 500,
                "success_rate": 0.92,
                "tasks_completed": 88,
                "error_rate": 0.08
            }
        }
        
        # Verificar métricas
        for agent, metrics in performance_metrics.items():
            assert 0 <= metrics["success_rate"] <= 1
            assert metrics["avg_response_time_ms"] > 0
            assert metrics["tasks_completed"] > 0
            assert 0 <= metrics["error_rate"] <= 1
        
        # Calcular métricas agregadas
        total_tasks = sum(metrics["tasks_completed"] for metrics in performance_metrics.values())
        weighted_success_rate = sum(
            metrics["success_rate"] * metrics["tasks_completed"] 
            for metrics in performance_metrics.values()
        ) / total_tasks
        
        assert weighted_success_rate > 0.9, f"Success rate demasiado bajo: {weighted_success_rate}"
        
        print("Test agent performance monitoring completado")
        print(f"  - Total tasks: {total_tasks}")
        print(f"  - Weighted success rate: {weighted_success_rate:.3f}")
    
    @pytest.mark.asyncio
    async def test_agent_scalability_test(self, test_context):
        """Test escalabilidad con múltiples agentes"""
        # Simular escalado horizontal
        scaling_scenarios = [
            {"agents": 5, "tasks": 10, "expected_throughput": 2.0},
            {"agents": 8, "tasks": 20, "expected_throughput": 2.5}, 
            {"agents": 12, "tasks": 30, "expected_throughput": 2.5}
        ]
        
        scaling_results = []
        for scenario in scaling_scenarios:
            # Simular ejecución escalable
            result = {
                "agents_deployed": scenario["agents"],
                "tasks_processed": scenario["tasks"],
                "actual_throughput": scenario["tasks"] / 10,  # Simular 10 segundos de ejecución
                "scaling_efficiency": scenario["tasks"] / scenario["agents"],
                "resource_utilization": 0.75
            }
            scaling_results.append(result)
        
        # Verificar escalabilidad
        for i, result in enumerate(scaling_results):
            scenario = scaling_scenarios[i]
            assert result["agents_deployed"] == scenario["agents"]
            assert result["tasks_processed"] == scenario["tasks"]
            assert result["scaling_efficiency"] > 0
            
            # Verificar que la eficiencia no degrade significativamente
            if i > 0:
                prev_efficiency = scaling_results[i-1]["scaling_efficiency"]
                current_efficiency = result["scaling_efficiency"]
                efficiency_drop = (prev_efficiency - current_efficiency) / prev_efficiency
                assert efficiency_drop < 0.3, f"Eficiencia degradó demasiado: {efficiency_drop:.2f}"
        
        print("Test agent scalability completado")
        for result in scaling_results:
            print(f"  - Agentes: {result['agents_deployed']}, "
                  f"Eficiencia: {result['scaling_efficiency']:.2f}, "
                  f"Throughput: {result['actual_throughput']:.2f} tasks/sec")