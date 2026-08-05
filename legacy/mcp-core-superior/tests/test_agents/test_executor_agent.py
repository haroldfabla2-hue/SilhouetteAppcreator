"""
Unit tests para ExecutorAgent
Ejecuta herramientas según plan del PlannerAgent
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.agents.executor_wrapper import ExecutorAgentWrapper
from src.agents.base_agent_wrapper import AgentCapability
from src.core.exceptions import AgentException


class TestExecutorAgentWrapper:
    """Test suite para ExecutorAgentWrapper"""
    
    @pytest.fixture
    def executor_agent(self):
        """Fixture para crear instancia del ExecutorAgent"""
        return ExecutorAgentWrapper()
    
    @pytest.fixture
    def sample_plan(self):
        """Fixture para plan de ejecución de ejemplo"""
        return {
            "tasks": [
                {"id": "task1", "name": "Desarrollo de API", "tool": "python_executor"},
                {"id": "task2", "name": "Scraping de datos", "tool": "web_scraper"},
                {"id": "task3", "name": "Procesamiento de archivos", "tool": "file_processor"}
            ],
            "execution_order": ["task1", "task2", "task3"],
            "parallel_groups": [["task1"], ["task2"], ["task3"]],
            "estimated_duration": {"estimated_minutes": 15}
        }
    
    @pytest.fixture
    def sample_request(self):
        """Fixture para request de ejemplo"""
        return {
            "plan": {
                "tasks": [
                    {"id": "task1", "name": "Implementar funcionalidad"},
                    {"id": "task2", "name": "Probar código"}
                ],
                "execution_order": ["task1", "task2"],
                "parallel_groups": [["task1"], ["task2"]]
            },
            "objective": "Desarrollar aplicación web",
            "max_concurrent": 2,
            "timeout_seconds": 600
        }
    
    @pytest.mark.asyncio
    async def test_initialization(self, executor_agent):
        """Test inicialización del ExecutorAgent"""
        assert executor_agent.agent_name == "executor"
        assert AgentCapability.TOOL_INVOCATION in executor_agent.capabilities
        assert AgentCapability.CONCURRENT_EXECUTION in executor_agent.capabilities
        assert AgentCapability.RESULT_COLLECTION in executor_agent.capabilities
        assert AgentCapability.CODE_EXECUTION in executor_agent.capabilities
        assert AgentCapability.WEB_SCRAPING in executor_agent.capabilities
        assert AgentCapability.API_CALLING in executor_agent.capabilities
        
        # Verificar herramientas disponibles
        assert "python_executor" in executor_agent.available_tools
        assert "web_scraper" in executor_agent.available_tools
        assert "web_scraping_agent" in executor_agent.available_tools
        assert "search_engine" in executor_agent.available_tools
        assert "file_processor" in executor_agent.available_tools
        assert "git_ops" in executor_agent.available_tools
        assert "api_caller" in executor_agent.available_tools
        assert "advanced_python_executor" in executor_agent.available_tools
        
        # Test que el logger está configurado
        assert executor_agent.logger.name == "mcp.agents.executor"
    
    @pytest.mark.asyncio
    async def test_process_request_success(self, executor_agent, sample_request):
        """Test procesamiento exitoso de request"""
        result = await executor_agent.process_request(sample_request)
        
        # Verificar estructura del resultado
        assert "execution_summary" in result
        assert "results" in result
        assert "artifacts" in result
        assert "evidence" in result
        
        # Verificar resumen de ejecución
        summary = result["execution_summary"]
        assert "tools_executed" in summary
        assert "successful" in summary
        assert "failed" in summary
        assert "total_time_ms" in summary
        
        # Verificar resultados
        results = result["results"]
        assert "tools_results" in results
        assert "combined_output" in results
        assert "success_rate" in results
        
        # Verificar artifacts
        assert isinstance(result["artifacts"], list)
        
        # Verificar evidence
        assert isinstance(result["evidence"], list)
        assert len(result["evidence"]) > 0
        
        # Verificar que cada evidence tiene la estructura correcta
        for evidence in result["evidence"]:
            assert "tool" in evidence
            assert "timestamp" in evidence
            assert "summary" in evidence
            assert "reference" in evidence
    
    @pytest.mark.asyncio
    async def test_process_request_invalid_plan(self, executor_agent):
        """Test procesamiento con plan inválido"""
        invalid_request = {
            "plan": {},  # Plan vacío
            "objective": "test"
        }
        
        with pytest.raises(AgentException) as exc_info:
            await executor_agent.process_request(invalid_request)
        
        assert "Plan es requerido" in str(exc_info.value.message)
    
    @pytest.mark.asyncio
    async def test_process_request_empty_plan(self, executor_agent):
        """Test procesamiento con plan sin tareas"""
        empty_plan_request = {
            "plan": {
                "tasks": [],
                "execution_order": [],
                "parallel_groups": []
            },
            "objective": "test"
        }
        
        result = await executor_agent.process_request(empty_plan_request)
        
        # Debe manejar el caso de plan vacío
        assert "execution_summary" in result
        summary = result["execution_summary"]
        assert summary["tools_executed"] == 0
        assert summary["successful"] == 0
        assert summary["failed"] == 0
    
    @pytest.mark.asyncio
    async def test_execute_tasks_with_parallel_groups(self, executor_agent, sample_plan):
        """Test ejecución con grupos paralelos"""
        request = {
            "plan": sample_plan,
            "objective": "Desarrollo complejo",
            "max_concurrent": 3,
            "timeout_seconds": 300
        }
        
        result = await executor_agent.process_request(request)
        
        # Verificar que se ejecutó el plan
        assert "execution_summary" in result
        assert "results" in result
        assert len(result["artifacts"]) == len(sample_plan["tasks"])
        assert len(result["evidence"]) == len(sample_plan["tasks"])
    
    @pytest.mark.asyncio
    async def test_execute_tasks_single_task(self, executor_agent):
        """Test ejecución con una sola tarea"""
        single_task_plan = {
            "plan": {
                "tasks": [
                    {"id": "single_task", "name": "Tarea única", "tool": "python_executor"}
                ],
                "execution_order": ["single_task"],
                "parallel_groups": [["single_task"]]
            },
            "objective": "Tarea simple",
            "max_concurrent": 1,
            "timeout_seconds": 60
        }
        
        result = await executor_agent.process_request(single_task_plan)
        
        assert "execution_summary" in result
        summary = result["execution_summary"]
        assert summary["tools_executed"] == 1
        assert summary["successful"] == 1
        assert summary["failed"] == 0
        
        assert len(result["results"]["tools_results"]) == 1
        assert len(result["artifacts"]) == 1
        assert len(result["evidence"]) == 1
    
    @pytest.mark.asyncio
    async def test_execute_tasks_multiple_tools(self, executor_agent):
        """Test ejecución con múltiples herramientas"""
        multi_tool_plan = {
            "plan": {
                "tasks": [
                    {"id": "python_task", "name": "Ejecutar Python", "tool": "python_executor"},
                    {"id": "web_task", "name": "Scraping web", "tool": "web_scraper"},
                    {"id": "file_task", "name": "Procesar archivos", "tool": "file_processor"},
                    {"id": "search_task", "name": "Buscar información", "tool": "search_engine"},
                    {"id": "api_task", "name": "Llamar API", "tool": "api_caller"}
                ],
                "execution_order": ["python_task", "web_task", "file_task", "search_task", "api_task"],
                "parallel_groups": [["python_task", "web_task"], ["file_task", "search_task"], ["api_task"]]
            },
            "objective": "Procesamiento completo",
            "max_concurrent": 3,
            "timeout_seconds": 120
        }
        
        result = await executor_agent.process_request(multi_tool_plan)
        
        assert result["execution_summary"]["tools_executed"] == 5
        
        # Verificar que se generaron artifacts para cada tarea
        assert len(result["artifacts"]) == 5
        assert len(result["evidence"]) == 5
        
        # Verificar que cada resultado tiene la estructura correcta
        for task_id, tool_result in result["results"]["tools_results"].items():
            assert "tool" in tool_result
            assert "success" in tool_result
            assert "result" in tool_result
            assert "time_ms" in tool_result
            assert tool_result["success"] is True
    
    def test_executor_agent_has_required_capabilities(self, executor_agent):
        """Test que el executor tiene las capacidades necesarias"""
        required_capabilities = [
            AgentCapability.TOOL_INVOCATION,
            AgentCapability.CONCURRENT_EXECUTION,
            AgentCapability.RESULT_COLLECTION,
            AgentCapability.CODE_EXECUTION,
            AgentCapability.WEB_SCRAPING,
            AgentCapability.API_CALLING
        ]
        
        for capability in required_capabilities:
            assert capability in executor_agent.capabilities
    
    def test_executor_agent_available_tools(self, executor_agent):
        """Test herramientas disponibles del executor"""
        expected_tools = [
            "python_executor", "web_scraper", "web_scraping_agent",
            "search_engine", "file_processor", "git_ops", "api_caller",
            "advanced_python_executor"
        ]
        
        for tool in expected_tools:
            assert tool in executor_agent.available_tools
    
    @pytest.mark.asyncio
    async def test_execution_summary_structure(self, executor_agent):
        """Test estructura del resumen de ejecución"""
        request = {
            "plan": {
                "tasks": [
                    {"id": "test1", "name": "Test task 1"},
                    {"id": "test2", "name": "Test task 2"}
                ],
                "execution_order": ["test1", "test2"],
                "parallel_groups": [["test1"], ["test2"]]
            },
            "objective": "Test execution"
        }
        
        result = await executor_agent.process_request(request)
        summary = result["execution_summary"]
        
        # Verificar todos los campos requeridos
        assert "tools_executed" in summary
        assert "successful" in summary
        assert "failed" in summary
        assert "total_time_ms" in summary
        
        # Verificar tipos de datos
        assert isinstance(summary["tools_executed"], int)
        assert isinstance(summary["successful"], int)
        assert isinstance(summary["failed"], int)
        assert isinstance(summary["total_time_ms"], int)
    
    @pytest.mark.asyncio
    async def test_results_structure(self, executor_agent):
        """Test estructura de resultados"""
        request = {
            "plan": {
                "tasks": [{"id": "single", "name": "Test"}],
                "execution_order": ["single"],
                "parallel_groups": [["single"]]
            },
            "objective": "Test"
        }
        
        result = await executor_agent.process_request(request)
        results = result["results"]
        
        # Verificar estructura de results
        assert "tools_results" in results
        assert "combined_output" in results
        assert "success_rate" in results
        
        # Verificar tools_results
        tools_results = results["tools_results"]
        for task_id, tool_result in tools_results.items():
            assert isinstance(task_id, str)
            assert "tool" in tool_result
            assert "success" in tool_result
            assert "result" in tool_result
            assert "time_ms" in tool_result
        
        # Verificar success_rate
        assert isinstance(results["success_rate"], float)
        assert 0.0 <= results["success_rate"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_artifacts_generation(self, executor_agent):
        """Test generación de artifacts"""
        request = {
            "plan": {
                "tasks": [
                    {"id": "task1", "name": "Test 1"},
                    {"id": "task2", "name": "Test 2"},
                    {"id": "task3", "name": "Test 3"}
                ],
                "execution_order": ["task1", "task2", "task3"],
                "parallel_groups": [["task1"], ["task2"], ["task3"]]
            },
            "objective": "Test artifacts"
        }
        
        result = await executor_agent.process_request(request)
        
        assert isinstance(result["artifacts"], list)
        assert len(result["artifacts"]) == 3
        
        # Verificar formato de artifacts
        for artifact in result["artifacts"]:
            assert artifact.startswith("artifact://executor/")
            assert "/result.json" in artifact
    
    @pytest.mark.asyncio
    async def test_evidence_collection(self, executor_agent):
        """Test recolección de evidencia"""
        request = {
            "plan": {
                "tasks": [
                    {"id": "task1", "name": "Test 1"},
                    {"id": "task2", "name": "Test 2"}
                ],
                "execution_order": ["task1", "task2"],
                "parallel_groups": [["task1"], ["task2"]]
            },
            "objective": "Test evidence"
        }
        
        result = await executor_agent.process_request(request)
        
        assert isinstance(result["evidence"], list)
        assert len(result["evidence"]) == 2
        
        # Verificar estructura de evidence
        for evidence in result["evidence"]:
            assert "tool" in evidence
            assert "timestamp" in evidence
            assert "summary" in evidence
            assert "reference" in evidence
            assert evidence["timestamp"] is not None
            assert isinstance(evidence["timestamp"], str)
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, executor_agent):
        """Test manejo de timeout"""
        request = {
            "plan": {
                "tasks": [{"id": "long_task", "name": "Long running task"}],
                "execution_order": ["long_task"],
                "parallel_groups": [["long_task"]]
            },
            "objective": "Test timeout",
            "timeout_seconds": 5  # Timeout muy corto
        }
        
        # El executor debería manejar el timeout correctamente
        result = await executor_agent.process_request(request)
        
        assert "execution_summary" in result
        assert "results" in result
    
    @pytest.mark.asyncio
    async def test_max_concurrent_parameter(self, executor_agent):
        """Test parámetro max_concurrent"""
        test_concurrent_values = [1, 3, 5, 10]
        
        for concurrent_val in test_concurrent_values:
            request = {
                "plan": {
                    "tasks": [
                        {"id": f"task{i}", "name": f"Task {i}"}
                        for i in range(3)
                    ],
                    "execution_order": [f"task{i}" for i in range(3)],
                    "parallel_groups": [[["task0"]], [["task1"]], [["task2"]]]
                },
                "objective": f"Test concurrent {concurrent_val}",
                "max_concurrent": concurrent_val
            }
            
            result = await executor_agent.process_request(request)
            assert "execution_summary" in result
    
    @pytest.mark.asyncio
    async def test_error_handling(self, executor_agent):
        """Test manejo de errores"""
        # Test con request que cause excepción interna
        with patch.object(executor_agent, '_execute_tasks', side_effect=Exception("Test error")):
            with pytest.raises(AgentException):
                await executor_agent.process_request({
                    "plan": {"tasks": []},
                    "objective": "test"
                })
