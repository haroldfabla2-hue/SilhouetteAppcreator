"""
Unit tests para PlannerAgent
Crea plan de ejecución con descomposición de tareas
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.agents.planner_wrapper import PlannerAgentWrapper
from src.agents.base_agent_wrapper import AgentCapability
from src.core.exceptions import AgentException


class TestPlannerAgentWrapper:
    """Test suite para PlannerAgentWrapper"""
    
    @pytest.fixture
    def planner_agent(self):
        """Fixture para crear instancia del PlannerAgent"""
        return PlannerAgentWrapper()
    
    @pytest.fixture
    def sample_analysis(self):
        """Fixture para análisis de ejemplo"""
        return {
            "intent_type": "development",
            "complexity_level": "medium",
            "domain": "technology",
            "requirements": ["app web", "base de datos"],
            "constraints": {"time_limit_hours": 24}
        }
    
    @pytest.fixture
    def sample_request(self):
        """Fixture para request de ejemplo"""
        return {
            "objective": "Desarrollar una aplicación web para gestión de tareas",
            "analysis": {
                "intent_type": "development",
                "complexity_level": "medium",
                "domain": "technology"
            },
            "constraints": {"time_limit_hours": 24},
            "parallel_agents": True
        }
    
    @pytest.mark.asyncio
    async def test_initialization(self, planner_agent):
        """Test inicialización del PlannerAgent"""
        assert planner_agent.agent_name == "planner"
        assert AgentCapability.TASK_DECOMPOSITION in planner_agent.capabilities
        assert AgentCapability.TOOL_SELECTION in planner_agent.capabilities
        assert AgentCapability.DEPENDENCY_MANAGEMENT in planner_agent.capabilities
        assert AgentCapability.PLAN_OPTIMIZATION in planner_agent.capabilities
        
        # Verificar herramientas disponibles
        assert "python_executor" in planner_agent.available_tools
        assert "web_scraper" in planner_agent.available_tools
        assert "search_engine" in planner_agent.available_tools
        assert "file_processor" in planner_agent.available_tools
        
        # Test que el logger está configurado
        assert planner_agent.logger.name == "mcp.agents.planner"
    
    @pytest.mark.asyncio
    async def test_process_request_success(self, planner_agent, sample_request):
        """Test procesamiento exitoso de request"""
        result = await planner_agent.process_request(sample_request)
        
        # Verificar estructura del resultado
        assert "objective" in result
        assert "execution_plan" in result
        assert "plan_metadata" in result
        assert "validation" in result
        
        # Verificar plan de ejecución
        execution_plan = result["execution_plan"]
        assert "tasks" in execution_plan
        assert "tool_assignments" in execution_plan
        assert "dependency_graph" in execution_plan
        assert "execution_order" in execution_plan
        assert "parallel_groups" in execution_plan
        assert "estimated_duration" in execution_plan
        assert "resource_requirements" in execution_plan
        
        # Verificar metadata
        metadata = result["plan_metadata"]
        assert "total_tasks" in metadata
        assert "total_tools" in metadata
        assert "parallelizable" in metadata
        assert "complexity_score" in metadata
        assert "created_at" in metadata
        assert "planner_version" in metadata
        
        # Verificar validación
        validation = result["validation"]
        assert "dependencies_resolved" in validation
        assert "tool_availability" in validation
        assert "resource_feasibility" in validation
        assert "timeline_feasibility" in validation
    
    @pytest.mark.asyncio
    async def test_process_request_invalid_objective(self, planner_agent):
        """Test procesamiento con objetivo inválido"""
        invalid_request = {
            "objective": "",  # Vacío
            "analysis": {}
        }
        
        with pytest.raises(AgentException) as exc_info:
            await planner_agent.process_request(invalid_request)
        
        assert exc_info.value.error_code == "INVALID_REQUEST"
        assert "Objective es requerido" in str(exc_info.value.message)
    
    @pytest.mark.asyncio
    async def test_create_execution_plan_method(self, planner_agent):
        """Test método público create_execution_plan"""
        analysis = {
            "intent_type": "research",
            "complexity_level": "high",
            "domain": "business"
        }
        
        result = await planner_agent.create_execution_plan(
            objective="Investigar mercado de software",
            analysis=analysis,
            constraints={"time_limit_hours": 12},
            parallel_agents=False
        )
        
        assert result["objective"] == "Investigar mercado de software"
        assert "execution_plan" in result
    
    def test_decompose_objective_analysis(self, planner_agent):
        """Test descomposición de objetivo - análisis"""
        analysis = {"intent_type": "analysis", "complexity_level": "medium"}
        
        tasks = planner_agent._decompose_objective("analizar datos de ventas", analysis)
        
        assert isinstance(tasks, list)
        assert len(tasks) == 4
        
        task_names = [task["name"] for task in tasks]
        expected_tasks = [
            "Recopilación de datos",
            "Procesamiento de datos", 
            "Análisis principal",
            "Síntesis de resultados"
        ]
        
        for expected_task in expected_tasks:
            assert expected_task in task_names
    
    def test_decompose_objective_development(self, planner_agent):
        """Test descomposición de objetivo - desarrollo"""
        analysis = {"intent_type": "development", "complexity_level": "high"}
        
        tasks = planner_agent._decompose_objective("desarrollar aplicación", analysis)
        
        assert isinstance(tasks, list)
        assert len(tasks) == 5
        
        task_names = [task["name"] for task in tasks]
        expected_tasks = [
            "Análisis de requisitos",
            "Diseño y arquitectura",
            "Implementación",
            "Testing y validación",
            "Documentación"
        ]
        
        for expected_task in expected_tasks:
            assert expected_task in task_names
    
    def test_decompose_objective_generic(self, planner_agent):
        """Test descomposición de objetivo - genérico"""
        analysis = {"intent_type": "general", "complexity_level": "low"}
        
        tasks = planner_agent._decompose_objective("realizar tarea", analysis)
        
        assert isinstance(tasks, list)
        assert len(tasks) == 4
        
        task_names = [task["name"] for task in tasks]
        expected_tasks = [
            "Preparación",
            "Ejecución principal",
            "Validación",
            "Entrega"
        ]
        
        for expected_task in expected_tasks:
            assert expected_task in task_names
    
    def test_assign_tools_web_data(self, planner_agent):
        """Test asignación de herramientas - datos web"""
        tasks = [
            {"id": "data_collection", "name": "Recopilación de datos web"},
            {"id": "processing", "name": "Procesamiento de datos"}
        ]
        analysis = {"intent_type": "analysis"}
        
        assignments = planner_agent._assign_tools(tasks, analysis)
        
        assert assignments["data_collection"] == "web_scraper"
        assert assignments["processing"] == "search_engine"
    
    def test_assign_tools_code(self, planner_agent):
        """Test asignación de herramientas - código"""
        tasks = [
            {"id": "implementation", "name": "Implementación de código"},
            {"id": "development", "name": "Desarrollo de funcionalidad"}
        ]
        analysis = {"intent_type": "development"}
        
        assignments = planner_agent._assign_tools(tasks, analysis)
        
        assert assignments["implementation"] == "python_executor"
        assert assignments["development"] == "python_executor"
    
    def test_assign_tools_files(self, planner_agent):
        """Test asignación de herramientas - archivos"""
        tasks = [
            {"id": "doc_generation", "name": "Generación de documento"},
            {"id": "file_processing", "name": "Procesamiento de archivo"}
        ]
        analysis = {"intent_type": "general"}
        
        assignments = planner_agent._assign_tools(tasks, analysis)
        
        assert assignments["doc_generation"] == "file_processor"
        assert assignments["file_processing"] == "file_processor"
    
    def test_assign_tools_api(self, planner_agent):
        """Test asignación de herramientas - API"""
        tasks = [
            {"id": "api_integration", "name": "Integración con API"},
            {"id": "api_call", "name": "Llamada a API externa"}
        ]
        analysis = {"intent_type": "general"}
        
        assignments = planner_agent._assign_tools(tasks, analysis)
        
        assert assignments["api_integration"] == "api_caller"
        assert assignments["api_call"] == "api_caller"
    
    def test_assign_tools_git(self, planner_agent):
        """Test asignación de herramientas - Git"""
        tasks = [
            {"id": "version_control", "name": "Control de versiones"},
            {"id": "git_ops", "name": "Operaciones Git"}
        ]
        analysis = {"intent_type": "general"}
        
        assignments = planner_agent._assign_tools(tasks, analysis)
        
        assert assignments["version_control"] == "git_ops"
        assert assignments["git_ops"] == "git_ops"
    
    def test_build_dependency_graph(self, planner_agent):
        """Test construcción de grafo de dependencias"""
        tasks = [
            {"id": "task1", "priority": 1},
            {"id": "task2", "priority": 2},
            {"id": "task3", "priority": 3}
        ]
        
        assignments = {"task1": "tool1", "task2": "tool2", "task3": "tool3"}
        
        dependencies = planner_agent._build_dependency_graph(tasks, assignments)
        
        assert isinstance(dependencies, dict)
        assert "task1" in dependencies
        assert "task2" in dependencies
        assert "task3" in dependencies
        
        # task2 debe depender de task1 (menor prioridad)
        assert "task1" in dependencies["task2"]
        # task3 debe depender de task1 y task2
        assert "task1" in dependencies["task3"]
        assert "task2" in dependencies["task3"]
    
    def test_optimize_plan_parallel(self, planner_agent):
        """Test optimización de plan - paralelización"""
        tasks = [
            {"id": "task1", "priority": 1},
            {"id": "task2", "priority": 1},
            {"id": "task3", "priority": 2}
        ]
        assignments = {"task1": "tool1", "task2": "tool2", "task3": "tool3"}
        dependency_graph = {
            "task1": [],
            "task2": [],
            "task3": ["task1", "task2"]
        }
        
        result = planner_agent._optimize_plan(
            tasks, assignments, dependency_graph, parallel_agents=True
        )
        
        assert "execution_order" in result
        assert "parallel_groups" in result
        assert "estimated_duration" in result
        assert "resource_requirements" in result
        assert "is_parallelizable" in result
    
    def test_topological_sort(self, planner_agent):
        """Test orden topológico"""
        tasks = [
            {"id": "task1", "priority": 1},
            {"id": "task2", "priority": 2},
            {"id": "task3", "priority": 3}
        ]
        dependencies = {
            "task1": [],
            "task2": ["task1"],
            "task3": ["task2"]
        }
        
        order = planner_agent._topological_sort(tasks, dependencies)
        
        assert isinstance(order, list)
        assert len(order) == 3
        # Verificar que el orden respeta las dependencias
        task1_index = order.index("task1")
        task2_index = order.index("task2")
        task3_index = order.index("task3")
        
        assert task1_index < task2_index < task3_index
    
    def test_find_parallel_groups(self, planner_agent):
        """Test encontrar grupos paralelos"""
        execution_order = ["task1", "task2", "task3", "task4"]
        dependencies = {
            "task1": [],
            "task2": [],
            "task3": ["task1"],
            "task4": ["task2"]
        }
        
        groups = planner_agent._find_parallel_groups(execution_order, dependencies)
        
        assert isinstance(groups, list)
        # task1 y task2 pueden ejecutarse en paralelo
        assert ["task1", "task2"] in groups
    
    def test_estimate_duration_single_task(self, planner_agent):
        """Test estimación de duración - una sola tarea"""
        tasks = [{"id": "task1"}]
        parallel_groups = []
        
        duration = planner_agent._estimate_duration(tasks, parallel_groups)
        
        assert "estimated_minutes" in duration
        assert "estimated_hours" in duration
        assert "confidence" in duration
        assert duration["estimated_minutes"] == 5  # Base duration per task
    
    def test_estimate_duration_parallel(self, planner_agent):
        """Test estimación de duración - tareas paralelas"""
        tasks = [{"id": "task1"}, {"id": "task2"}, {"id": "task3"}]
        parallel_groups = [["task1", "task2"]]
        
        duration = planner_agent._estimate_duration(tasks, parallel_groups)
        
        # Debe ser menos que el tiempo serial debido a paralelización
        base_duration = len(tasks) * 5
        assert duration["estimated_minutes"] < base_duration
    
    def test_calculate_resource_requirements(self, planner_agent):
        """Test cálculo de requerimientos de recursos"""
        tasks = [{"id": "task1"}, {"id": "task2"}]
        parallel_groups = [["task1", "task2"]]
        
        requirements = planner_agent._calculate_resource_requirements(tasks, parallel_groups)
        
        assert "max_concurrent_tools" in requirements
        assert "estimated_memory_mb" in requirements
        assert "estimated_cpu_cores" in requirements
        assert "network_bandwidth" in requirements
        assert "storage_requirements" in requirements
        
        assert requirements["max_concurrent_tools"] == 2  # Max parallel tasks
    
    def test_calculate_complexity_score(self, planner_agent):
        """Test cálculo de score de complejidad"""
        tasks = [
            {"id": "task1"},
            {"id": "task2"},
            {"id": "task3"}
        ]
        dependency_graph = {
            "task1": [],
            "task2": ["task1"],
            "task3": ["task1", "task2"]
        }
        
        score = planner_agent._calculate_complexity_score(tasks, dependency_graph)
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
    
    def test_validate_dependencies_no_cycles(self, planner_agent):
        """Test validación de dependencias - sin ciclos"""
        dependency_graph = {
            "task1": [],
            "task2": ["task1"],
            "task3": ["task2"]
        }
        
        is_valid = planner_agent._validate_dependencies(dependency_graph)
        assert is_valid is True
    
    def test_validate_dependencies_with_cycles(self, planner_agent):
        """Test validación de dependencias - con ciclos"""
        dependency_graph = {
            "task1": ["task2"],
            "task2": ["task3"],
            "task3": ["task1"]
        }
        
        is_valid = planner_agent._validate_dependencies(dependency_graph)
        assert is_valid is False
    
    def test_check_tool_availability_valid(self, planner_agent):
        """Test verificación de disponibilidad de herramientas - válido"""
        assignments = {
            "task1": "python_executor",
            "task2": "web_scraper",
            "task3": "search_engine"
        }
        
        is_available = planner_agent._check_tool_availability(assignments)
        assert is_available is True
    
    def test_check_tool_availability_invalid(self, planner_agent):
        """Test verificación de disponibilidad de herramientas - inválido"""
        assignments = {
            "task1": "python_executor",
            "task2": "nonexistent_tool"
        }
        
        is_available = planner_agent._check_tool_availability(assignments)
        assert is_available is False
    
    def test_estimate_task_effort(self, planner_agent):
        """Test estimación de esfuerzo por tarea"""
        task = {"name": "Implementación"}
        
        low_effort = planner_agent._estimate_task_effort(task, "low")
        medium_effort = planner_agent._estimate_task_effort(task, "medium")
        high_effort = planner_agent._estimate_task_effort(task, "high")
        
        assert low_effort == "low"
        assert medium_effort == "medium"
        assert high_effort == "high"
    
    def test_get_task_capabilities(self, planner_agent):
        """Test obtener capacidades requeridas para tarea"""
        task_data = {"name": "Análisis de datos"}
        intent_type = "analysis"
        
        capabilities = planner_agent._get_task_capabilities(task_data, intent_type)
        
        assert isinstance(capabilities, list)
        assert "data_processing" in capabilities
        assert "search" in capabilities
        assert "analysis" in capabilities
    
    def test_get_task_inputs(self, planner_agent):
        """Test obtener inputs requeridos para tarea"""
        task = {"name": "Análisis de datos"}
        
        inputs = planner_agent._get_task_inputs(task)
        
        assert isinstance(inputs, list)
        assert "data_sources" in inputs
        assert "query_parameters" in inputs
    
    def test_get_task_outputs(self, planner_agent):
        """Test obtener outputs esperados de tarea"""
        task = {"name": "Implementación de aplicación"}
        
        outputs = planner_agent._get_task_outputs(task)
        
        assert isinstance(outputs, list)
        assert "code" in outputs
        assert "documentation" in outputs
        assert "tests" in outputs
    
    @pytest.mark.asyncio
    async def test_get_status(self, planner_agent):
        """Test obtención de estado del agente"""
        status = await planner_agent.get_status()
        
        assert "agent_type" in status
        assert status["agent_type"] == "planner"
        assert "specialization" in status
        assert "available_tools" in status
        assert "input_format" in status
        assert "capabilities" in status
        
        # Verificar que las herramientas están en el status
        assert "python_executor" in status["available_tools"]
    
    @pytest.mark.asyncio
    async def test_error_handling(self, planner_agent):
        """Test manejo de errores"""
        # Test con request que cause excepción interna
        with patch.object(planner_agent, '_create_execution_plan', side_effect=Exception("Test error")):
            with pytest.raises(AgentException):
                await planner_agent.process_request({"objective": "test", "analysis": {}})
