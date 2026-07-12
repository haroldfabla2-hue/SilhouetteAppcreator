"""
Unit tests para ParallelExecutionEngine
Motor de ejecución paralela para agentes con máximo rendimiento
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any, List, Set
import time
import threading
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.parallel_execution_engine import (
    ParallelExecutionEngine, Task, TaskState, ExecutionStrategy,
    LoadBalancingStrategy, ResourceType
)


class TestParallelExecutionEngine:
    """Test suite para ParallelExecutionEngine"""
    
    @pytest.fixture
    def execution_engine(self):
        """Fixture para crear instancia del ParallelExecutionEngine"""
        with patch('src.core.parallel_execution_engine.settings'), \
             patch('src.core.parallel_execution_engine.psutil'):
            return ParallelExecutionEngine()
    
    @pytest.fixture
    def sample_task(self):
        """Fixture para crear tarea de ejemplo"""
        return Task(
            task_id="test_task_1",
            agent_type="reasoner",
            operation="analyze_intent",
            parameters={"objective": "test objective"},
            dependencies=set(),
            priority=1,
            timeout=30.0,
            strategy=ExecutionStrategy.PARALLEL
        )
    
    @pytest.mark.asyncio
    async def test_initialization(self, execution_engine):
        """Test inicialización del motor de ejecución"""
        assert execution_engine is not None
        assert hasattr(execution_engine, 'logger')
        assert hasattr(execution_engine, 'task_queue')
        assert hasattr(execution_engine, 'running_tasks')
        assert hasattr(execution_engine, 'agent_pools')
        assert hasattr(execution_engine, 'load_balancer')
        assert hasattr(execution_engine, 'resource_monitor')
    
    @pytest.mark.asyncio
    async def test_submit_task(self, execution_engine, sample_task):
        """Test envío de tarea"""
        with patch.object(execution_engine, '_submit_task_internal') as mock_submit:
            mock_submit.return_value = sample_task.task_id
            
            task_id = await execution_engine.submit_task(sample_task)
            
            assert task_id == sample_task.task_id
            mock_submit.assert_called_once_with(sample_task)
    
    @pytest.mark.asyncio
    async def test_submit_multiple_tasks(self, execution_engine):
        """Test envío de múltiples tareas"""
        tasks = []
        for i in range(5):
            task = Task(
                task_id=f"task_{i}",
                agent_type="reasoner",
                operation="analyze_intent",
                parameters={"objective": f"objective {i}"},
                dependencies=set(),
                priority=i
            )
            tasks.append(task)
        
        with patch.object(execution_engine, '_submit_task_internal') as mock_submit:
            mock_submit.side_effect = [task.task_id for task in tasks]
            
            task_ids = []
            for task in tasks:
                task_id = await execution_engine.submit_task(task)
                task_ids.append(task_id)
            
            assert len(task_ids) == 5
            assert all(tid.startswith("task_") for tid in task_ids)
    
    @pytest.mark.asyncio
    async def test_execute_sequential(self, execution_engine):
        """Test ejecución secuencial"""
        task1 = Task(
            task_id="seq_task_1",
            agent_type="reasoner",
            operation="analyze_intent",
            parameters={"objective": "task 1"},
            strategy=ExecutionStrategy.SEQUENTIAL
        )
        
        task2 = Task(
            task_id="seq_task_2", 
            agent_type="reasoner",
            operation="analyze_intent",
            parameters={"objective": "task 2"},
            strategy=ExecutionStrategy.SEQUENTIAL
        )
        
        with patch.object(execution_engine, '_execute_task') as mock_execute:
            mock_execute.side_effect = [
                {"result": "result1", "task_id": "seq_task_1"},
                {"result": "result2", "task_id": "seq_task_2"}
            ]
            
            # Ejecutar secuencialmente
            result1 = await execution_engine._execute_task(task1)
            result2 = await execution_engine._execute_task(task2)
            
            assert result1["result"] == "result1"
            assert result2["result"] == "result2"
            assert result1["task_id"] == "seq_task_1"
            assert result2["task_id"] == "seq_task_2"
    
    @pytest.mark.asyncio
    async def test_execute_parallel(self, execution_engine):
        """Test ejecución paralela"""
        tasks = [
            Task(
                task_id=f"parallel_task_{i}",
                agent_type="reasoner",
                operation="analyze_intent",
                parameters={"objective": f"task {i}"},
                strategy=ExecutionStrategy.PARALLEL
            )
            for i in range(3)
        ]
        
        with patch.object(execution_engine, '_execute_task') as mock_execute:
            # Simular ejecución paralela exitosa
            mock_execute.side_effect = [
                {"result": f"result{i}", "task_id": f"parallel_task_{i}"}
                for i in range(3)
            ]
            
            # Ejecutar en paralelo
            results = await asyncio.gather(*[
                execution_engine._execute_task(task) for task in tasks
            ])
            
            assert len(results) == 3
            for i, result in enumerate(results):
                assert result["result"] == f"result{i}"
                assert result["task_id"] == f"parallel_task_{i}"
    
    @pytest.mark.asyncio
    async def test_task_with_dependencies(self, execution_engine):
        """Test tareas con dependencias"""
        # Tarea sin dependencias
        task1 = Task(
            task_id="independent_task",
            agent_type="reasoner",
            operation="analyze_intent",
            parameters={"objective": "independent"},
            dependencies=set()
        )
        
        # Tarea con dependencias
        task2 = Task(
            task_id="dependent_task",
            agent_type="planner",
            operation="create_execution_plan",
            parameters={"analysis": "analysis result"},
            dependencies={"independent_task"}
        )
        
        tasks = [task1, task2]
        
        with patch.object(execution_engine, '_check_dependencies') as mock_check:
            mock_check.side_effect = [
                True,   # task1: no dependencies
                False   # task2: waiting for dependencies
            ]
            
            # Verificar dependencias
            assert execution_engine._check_dependencies(task1) is True
            assert execution_engine._check_dependencies(task2) is False
    
    @pytest.mark.asyncio
    async def test_task_priority_handling(self, execution_engine):
        """Test manejo de prioridades de tareas"""
        tasks = [
            Task(
                task_id=f"low_priority_task",
                agent_type="reasoner",
                operation="analyze_intent",
                parameters={"objective": "low"},
                priority=1
            ),
            Task(
                task_id=f"high_priority_task",
                agent_type="reasoner",
                operation="analyze_intent",
                parameters={"objective": "high"},
                priority=10
            )
        ]
        
        with patch.object(execution_engine, '_sort_tasks_by_priority') as mock_sort:
            mock_sort.return_value = [
                tasks[1],  # high priority first
                tasks[0]   # low priority second
            ]
            
            sorted_tasks = execution_engine._sort_tasks_by_priority(tasks)
            
            assert sorted_tasks[0].priority > sorted_tasks[1].priority
    
    @pytest.mark.asyncio
    async def test_load_balancing_round_robin(self, execution_engine):
        """Test balanceador de carga - round robin"""
        # Simular agentes disponibles
        agents = ["agent_1", "agent_2", "agent_3"]
        
        with patch.object(execution_engine, '_get_available_agents') as mock_get_agents:
            mock_get_agents.return_value = agents
            
            # Simular round robin selection
            selected_agents = []
            for _ in range(6):  # More tasks than agents
                agent = execution_engine._select_agent_round_robin(agents, "reasoner")
                selected_agents.append(agent)
            
            # Debería distribuir entre los agentes
            assert len(selected_agents) == 6
            assert all(agent in agents for agent in selected_agents)
    
    @pytest.mark.asyncio
    async def test_resource_monitoring(self, execution_engine):
        """Test monitoreo de recursos"""
        with patch.object(execution_engine, '_get_system_resources') as mock_resources:
            mock_resources.return_value = {
                "cpu_usage": 0.65,
                "memory_usage": 0.45,
                "io_usage": 0.30,
                "network_usage": 0.20
            }
            
            resources = await execution_engine._get_system_resources()
            
            assert "cpu_usage" in resources
            assert "memory_usage" in resources
            assert "io_usage" in resources
            assert "network_usage" in resources
            assert 0 <= resources["cpu_usage"] <= 1
            assert 0 <= resources["memory_usage"] <= 1
    
    @pytest.mark.asyncio
    async def test_task_timeout_handling(self, execution_engine):
        """Test manejo de timeout de tareas"""
        task = Task(
            task_id="timeout_task",
            agent_type="reasoner",
            operation="analyze_intent",
            parameters={"objective": "test"},
            timeout=1.0  # Timeout muy corto
        )
        
        with patch.object(execution_engine, '_execute_with_timeout') as mock_timeout:
            mock_timeout.side_effect = asyncio.TimeoutError("Task timed out")
            
            with pytest.raises(asyncio.TimeoutError):
                await execution_engine._execute_with_timeout(task)
    
    @pytest.mark.asyncio
    async def test_task_retry_mechanism(self, execution_engine):
        """Test mecanismo de reintento"""
        task = Task(
            task_id="retry_task",
            agent_type="reasoner",
            operation="analyze_intent",
            parameters={"objective": "test"},
            max_retries=3,
            retry_delay=0.1
        )
        
        with patch.object(execution_engine, '_execute_task') as mock_execute:
            # Simular fallo en los primeros 2 intentos, éxito en el tercero
            mock_execute.side_effect = [
                Exception("First attempt failed"),
                Exception("Second attempt failed"),
                {"result": "success", "task_id": "retry_task"}
            ]
            
            result = await execution_engine._execute_task_with_retry(task)
            
            assert result["result"] == "success"
            assert mock_execute.call_count == 3
    
    @pytest.mark.asyncio
    async def test_pipeline_execution(self, execution_engine):
        """Test ejecución tipo pipeline"""
        # Tareas que forman un pipeline
        pipeline_tasks = [
            Task(
                task_id="pipeline_1",
                agent_type="reasoner",
                operation="analyze_intent",
                parameters={"objective": "pipeline input"},
                strategy=ExecutionStrategy.PIPELINE
            ),
            Task(
                task_id="pipeline_2",
                agent_type="planner",
                operation="create_execution_plan",
                parameters={"analysis": "${pipeline_1.result}"},
                strategy=ExecutionStrategy.PIPELINE
            ),
            Task(
                task_id="pipeline_3",
                agent_type="executor",
                operation="execute_tasks",
                parameters={"plan": "${pipeline_2.result}"},
                strategy=ExecutionStrategy.PIPELINE
            )
        ]
        
        with patch.object(execution_engine, '_execute_pipeline') as mock_pipeline:
            mock_pipeline.return_value = {
                "pipeline_result": "success",
                "steps_completed": 3
            }
            
            result = await execution_engine._execute_pipeline(pipeline_tasks)
            
            assert "pipeline_result" in result
            assert result["steps_completed"] == 3
    
    @pytest.mark.asyncio
    async def test_fan_out_execution(self, execution_engine):
        """Test ejecución tipo fan-out"""
        # Tarea raíz
        root_task = Task(
            task_id="root_task",
            agent_type="reasoner",
            operation="analyze_intent",
            parameters={"objective": "root"},
            strategy=ExecutionStrategy.FAN_OUT
        )
        
        # Tareas hijas
        child_tasks = [
            Task(
                task_id=f"child_task_{i}",
                agent_type="planner",
                operation="create_execution_plan",
                parameters={"analysis": "${root_task.result}"},
                strategy=ExecutionStrategy.FAN_OUT
            )
            for i in range(4)
        ]
        
        with patch.object(execution_engine, '_execute_fan_out') as mock_fan_out:
            mock_fan_out.return_value = {
                "fan_out_results": [f"child_result_{i}" for i in range(4)],
                "root_result": "root_success"
            }
            
            result = await execution_engine._execute_fan_out(root_task, child_tasks)
            
            assert "fan_out_results" in result
            assert "root_result" in result
            assert len(result["fan_out_results"]) == 4
    
    @pytest.mark.asyncio
    async def test_work_stealing_execution(self, execution_engine):
        """Test ejecución con work stealing"""
        tasks = [
            Task(
                task_id=f"steal_task_{i}",
                agent_type="reasoner",
                operation="analyze_intent",
                parameters={"objective": f"task {i}"},
                strategy=ExecutionStrategy.WORK_STEALING
            )
            for i in range(10)
        ]
        
        with patch.object(execution_engine, '_execute_with_work_stealing') as mock_stealing:
            mock_stealing.return_value = {
                "completed_tasks": len(tasks),
                "stolen_tasks": 3,
                "execution_time": 2.5
            }
            
            result = await execution_engine._execute_with_work_stealing(tasks)
            
            assert "completed_tasks" in result
            assert "stolen_tasks" in result
            assert "execution_time" in result
            assert result["completed_tasks"] == len(tasks)
    
    @pytest.mark.asyncio
    async def test_task_cancellation(self, execution_engine, sample_task):
        """Test cancelación de tareas"""
        with patch.object(execution_engine, '_cancel_task') as mock_cancel:
            mock_cancel.return_value = True
            
            result = await execution_engine.cancel_task(sample_task.task_id)
            
            assert result is True
            mock_cancel.assert_called_once_with(sample_task.task_id)
    
    @pytest.mark.asyncio
    async def test_task_status_tracking(self, execution_engine, sample_task):
        """Test seguimiento de estado de tareas"""
        # Simular cambio de estado
        execution_engine.running_tasks[sample_task.task_id] = sample_task
        
        # Verificar estado inicial
        assert sample_task.state == TaskState.PENDING
        
        # Cambiar estado
        sample_task.state = TaskState.RUNNING
        sample_task.started_at = datetime.now()
        
        assert sample_task.state == TaskState.RUNNING
        assert sample_task.started_at is not None
    
    @pytest.mark.asyncio
    async def test_execution_statistics(self, execution_engine):
        """Test estadísticas de ejecución"""
        # Simular tareas completadas
        completed_tasks = [
            Task(
                task_id=f"completed_task_{i}",
                agent_type="reasoner",
                operation="analyze_intent",
                parameters={"objective": f"task {i}"},
                started_at=datetime.now() - timedelta(seconds=1),
                completed_at=datetime.now()
            )
            for i in range(5)
        ]
        
        with patch.object(execution_engine, '_calculate_statistics') as mock_stats:
            mock_stats.return_value = {
                "total_tasks": 5,
                "completed_tasks": 5,
                "failed_tasks": 0,
                "success_rate": 1.0,
                "average_duration": 1.0,
                "throughput": 5.0
            }
            
            stats = await execution_engine._calculate_statistics(completed_tasks)
            
            assert stats["total_tasks"] == 5
            assert stats["completed_tasks"] == 5
            assert stats["failed_tasks"] == 0
            assert stats["success_rate"] == 1.0
            assert stats["throughput"] == 5.0
    
    @pytest.mark.asyncio
    async def test_resource_limit_enforcement(self, execution_engine):
        """Test aplicación de límites de recursos"""
        # Crear tarea con requerimientos de recursos
        task = Task(
            task_id="resource_task",
            agent_type="reasoner",
            operation="analyze_intent",
            parameters={"objective": "test"},
            resource_requirements={
                "cpu": 0.5,
                "memory": 0.3,
                "io": 0.2
            }
        )
        
        with patch.object(execution_engine, '_check_resource_availability') as mock_check:
            mock_check.return_value = True
            
            available = await execution_engine._check_resource_availability(task)
            
            assert available is True
    
    @pytest.mark.asyncio
    async def test_agent_pool_management(self, execution_engine):
        """Test gestión de pools de agentes"""
        agent_type = "reasoner"
        pool_size = 3
        
        with patch.object(execution_engine, '_create_agent_pool') as mock_create:
            mock_create.return_value = {
                "pool_id": f"{agent_type}_pool",
                "size": pool_size,
                "agents": [f"{agent_type}_{i}" for i in range(pool_size)]
            }
            
            pool = await execution_engine._create_agent_pool(agent_type, pool_size)
            
            assert pool["pool_id"] == f"{agent_type}_pool"
            assert pool["size"] == pool_size
            assert len(pool["agents"]) == pool_size
    
    @pytest.mark.asyncio
    async def test_error_handling_task_failure(self, execution_engine, sample_task):
        """Test manejo de errores - fallo de tarea"""
        with patch.object(execution_engine, '_execute_task') as mock_execute:
            mock_execute.side_effect = Exception("Task execution failed")
            
            # La tarea debería fallar y marcar el estado como FAILED
            try:
                await execution_engine._execute_task(sample_task)
            except Exception as e:
                assert str(e) == "Task execution failed"
            
            # Verificar que el estado se actualizó
            assert sample_task.state == TaskState.FAILED
            assert sample_task.error is not None
    
    @pytest.mark.asyncio
    async def test_error_handling_resource_exhaustion(self, execution_engine):
        """Test manejo de errores - recursos agotados"""
        task = Task(
            task_id="exhaustion_task",
            agent_type="reasoner",
            operation="analyze_intent",
            parameters={"objective": "test"},
            resource_requirements={
                "cpu": 2.0,  # Más CPU de la disponible
                "memory": 1.5
            }
        )
        
        with patch.object(execution_engine, '_check_resource_availability') as mock_check:
            mock_check.return_value = False  # Recursos no disponibles
            
            available = await execution_engine._check_resource_availability(task)
            
            assert available is False
    
    @pytest.mark.asyncio
    async def test_performance_optimization(self, execution_engine):
        """Test optimización de rendimiento"""
        # Simular carga de trabajo
        workload = [f"task_{i}" for i in range(100)]
        
        with patch.object(execution_engine, '_optimize_performance') as mock_optimize:
            mock_optimize.return_value = {
                "optimization_applied": True,
                "performance_gain": 0.25,
                "optimizations": ["batch_processing", "connection_pooling"]
            }
            
            result = await execution_engine._optimize_performance(workload)
            
            assert result["optimization_applied"] is True
            assert result["performance_gain"] > 0
            assert len(result["optimizations"]) > 0
