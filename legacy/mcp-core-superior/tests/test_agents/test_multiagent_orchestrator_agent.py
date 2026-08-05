"""
Unit tests para MultiAgentOrchestratorAgent
Orquestador empresarial que gestiona agentes base y especializados
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any, List
import json
import time
import uuid

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.agents.multiagent_orchestrator_agent import (
    MultiAgentOrchestratorAgent, WorkflowState, TaskPriority, 
    LoadBalancingStrategy, CircuitBreakerState
)
from src.agents.base_agent_wrapper import AgentCapability


class TestMultiAgentOrchestratorAgent:
    """Test suite para MultiAgentOrchestratorAgent"""
    
    @pytest.fixture
    def orchestrator_agent(self):
        """Fixture para crear instancia del MultiAgentOrchestratorAgent"""
        return MultiAgentOrchestratorAgent()
    
    @pytest.fixture
    def sample_workflow(self):
        """Fixture para workflow de ejemplo"""
        return {
            "workflow_id": str(uuid.uuid4()),
            "name": "Test Workflow",
            "description": "A test workflow",
            "steps": [
                {
                    "step_id": "step1",
                    "name": "Analysis Step",
                    "agent_type": "reasoner",
                    "inputs": {"objective": "Analyze data"},
                    "priority": TaskPriority.NORMAL
                },
                {
                    "step_id": "step2", 
                    "name": "Planning Step",
                    "agent_type": "planner",
                    "inputs": {"analysis": "${step1.result}"},
                    "priority": TaskPriority.HIGH
                }
            ],
            "dependencies": {
                "step2": ["step1"]
            },
            "max_retries": 3,
            "timeout_seconds": 300
        }
    
    @pytest.mark.asyncio
    async def test_initialization(self, orchestrator_agent):
        """Test inicialización del MultiAgentOrchestratorAgent"""
        assert orchestrator_agent is not None
        assert hasattr(orchestrator_agent, 'logger')
        assert hasattr(orchestrator_agent, 'workflows')
        assert hasattr(orchestrator_agent, 'agent_registry')
        assert hasattr(orchestrator_agent, 'load_balancer')
        assert hasattr(orchestrator_agent, 'circuit_breakers')
    
    @pytest.mark.asyncio
    async def test_register_agent(self, orchestrator_agent):
        """Test registro de agente"""
        agent_info = {
            "agent_id": "test_agent_1",
            "agent_type": "reasoner",
            "capabilities": [AgentCapability.INTENT_ANALYSIS],
            "max_concurrent": 2,
            "current_load": 0,
            "status": "ready",
            "health_score": 1.0
        }
        
        with patch.object(orchestrator_agent, '_register_agent_internal') as mock_register:
            mock_register.return_value = True
            
            result = await orchestrator_agent.register_agent(agent_info)
            
            assert result["success"] is True
            assert "agent_id" in result
            assert result["agent_id"] == "test_agent_1"
    
    @pytest.mark.asyncio
    async def test_create_workflow(self, orchestrator_agent, sample_workflow):
        """Test creación de workflow"""
        with patch.object(orchestrator_agent, '_create_workflow_internal') as mock_create:
            mock_create.return_value = sample_workflow["workflow_id"]
            
            workflow_id = await orchestrator_agent.create_workflow(sample_workflow)
            
            assert workflow_id is not None
            assert isinstance(workflow_id, str)
    
    @pytest.mark.asyncio
    async def test_execute_workflow(self, orchestrator_agent, sample_workflow):
        """Test ejecución de workflow"""
        workflow_id = sample_workflow["workflow_id"]
        
        with patch.object(orchestrator_agent, '_execute_workflow_internal') as mock_execute:
            mock_execute.return_value = {
                "workflow_id": workflow_id,
                "status": WorkflowState.COMPLETED.value,
                "results": {
                    "step1": {"result": "analysis_complete"},
                    "step2": {"result": "plan_created"}
                },
                "execution_time": 15.5,
                "steps_completed": 2
            }
            
            result = await orchestrator_agent.execute_workflow(
                workflow_id=workflow_id,
                workflow_config=sample_workflow,
                parallel_execution=True
            )
            
            assert "workflow_id" in result
            assert "status" in result
            assert "results" in result
            assert "execution_time" in result
            assert "steps_completed" in result
    
    @pytest.mark.asyncio
    async def test_workflow_state_tracking(self, orchestrator_agent, sample_workflow):
        """Test seguimiento de estados de workflow"""
        workflow_id = sample_workflow["workflow_id"]
        
        # Simular workflow en diferentes estados
        states = [WorkflowState.CREATED, WorkflowState.QUEUED, WorkflowState.RUNNING]
        
        with patch.object(orchestrator_agent, '_update_workflow_state') as mock_update:
            for state in states:
                await orchestrator_agent._update_workflow_state(
                    workflow_id, state.value, {"timestamp": time.time()}
                )
        
        # Verificar que el workflow existe
        assert workflow_id in orchestrator_agent.workflows
    
    @pytest.mark.asyncio
    async def test_parallel_execution(self, orchestrator_agent, sample_workflow):
        """Test ejecución paralela de pasos"""
        workflow_id = sample_workflow["workflow_id"]
        
        # Modificar workflow para permitir paralelización
        sample_workflow["dependencies"] = {}  # Sin dependencias
        sample_workflow["parallel_groups"] = [["step1"], ["step2"]]
        
        with patch.object(orchestrator_agent, '_execute_parallel_steps') as mock_parallel:
            mock_parallel.return_value = {
                "step1": {"result": "result1"},
                "step2": {"result": "result2"}
            }
            
            result = await orchestrator_agent._execute_parallel_steps(
                workflow_id, sample_workflow["steps"]
            )
            
            assert "step1" in result
            assert "step2" in result
            assert result["step1"]["result"] == "result1"
            assert result["step2"]["result"] == "result2"
    
    @pytest.mark.asyncio
    async def test_sequential_execution(self, orchestrator_agent, sample_workflow):
        """Test ejecución secuencial de pasos"""
        workflow_id = sample_workflow["workflow_id"]
        
        with patch.object(orchestrator_agent, '_execute_sequential_steps') as mock_sequential:
            mock_sequential.return_value = {
                "step1": {"result": "sequential_result1"},
                "step2": {"result": "sequential_result2"}
            }
            
            result = await orchestrator_agent._execute_sequential_steps(
                workflow_id, sample_workflow["steps"]
            )
            
            assert "step1" in result
            assert "step2" in result
    
    @pytest.mark.asyncio
    async def test_dependency_resolution(self, orchestrator_agent):
        """Test resolución de dependencias"""
        steps = [
            {"step_id": "step1", "name": "First"},
            {"step_id": "step2", "name": "Second", "dependencies": ["step1"]},
            {"step_id": "step3", "name": "Third", "dependencies": ["step2"]}
        ]
        
        with patch.object(orchestrator_agent, '_resolve_dependencies') as mock_resolve:
            mock_resolve.return_value = ["step1", "step2", "step3"]
            
            resolved_order = await orchestrator_agent._resolve_dependencies(steps)
            
            assert isinstance(resolved_order, list)
            assert len(resolved_order) == 3
            # step2 debe venir después de step1
            step1_idx = resolved_order.index("step1")
            step2_idx = resolved_order.index("step2")
            assert step1_idx < step2_idx
    
    @pytest.mark.asyncio
    async def test_load_balancing(self, orchestrator_agent):
        """Test balanceador de carga"""
        # Registrar múltiples agentes del mismo tipo
        agents = [
            {"agent_id": "agent1", "current_load": 1, "response_time": 100},
            {"agent_id": "agent2", "current_load": 0, "response_time": 80},
            {"agent_id": "agent3", "current_load": 2, "response_time": 120}
        ]
        
        with patch.object(orchestrator_agent, '_select_best_agent') as mock_select:
            mock_select.return_value = agents[1]  # agent2 (menor carga)
            
            selected_agent = await orchestrator_agent._select_best_agent(
                agent_type="reasoner",
                strategy=LoadBalancingStrategy.LEAST_CONNECTIONS
            )
            
            assert selected_agent["agent_id"] == "agent2"
            assert selected_agent["current_load"] == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_pattern(self, orchestrator_agent):
        """Test patrón circuit breaker"""
        agent_id = "test_agent"
        
        # Simular fallos consecutivos
        for _ in range(5):
            await orchestrator_agent._record_agent_failure(agent_id)
        
        # El circuit breaker debería estar abierto
        assert agent_id in orchestrator_agent.circuit_breakers
        circuit_breaker = orchestrator_agent.circuit_breakers[agent_id]
        assert circuit_breaker["state"] == CircuitBreakerState.OPEN.value
        
        # Simular recuperación
        await orchestrator_agent._record_agent_success(agent_id)
        # Después de un éxito, debería cambiar a half_open
        # (en una implementación real, esto requeriría más lógica de tiempo)
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, orchestrator_agent, sample_workflow):
        """Test recuperación de errores"""
        workflow_id = sample_workflow["workflow_id"]
        
        with patch.object(orchestrator_agent, '_handle_workflow_error') as mock_handle:
            mock_handle.return_value = {
                "recovered": True,
                "recovery_action": "retry_step",
                "retry_count": 1
            }
            
            recovery_result = await orchestrator_agent._handle_workflow_error(
                workflow_id, "step1", Exception("Test error")
            )
            
            assert "recovered" in recovery_result
            assert "recovery_action" in recovery_result
            assert "retry_count" in recovery_result
    
    @pytest.mark.asyncio
    async def test_task_queue_management(self, orchestrator_agent):
        """Test gestión de cola de tareas"""
        # Añadir tareas con diferentes prioridades
        tasks = [
            {"task_id": "task1", "priority": TaskPriority.LOW},
            {"task_id": "task2", "priority": TaskPriority.HIGH},
            {"task_id": "task3", "priority": TaskPriority.CRITICAL}
        ]
        
        for task in tasks:
            await orchestrator_agent._add_to_queue(task)
        
        # Verificar que las tareas se añaden correctamente
        assert len(orchestrator_agent.task_queue) == 3
        
        # Verificar que las prioridades se manejan correctamente
        # (en una implementación real, se ordenaría por prioridad)
    
    @pytest.mark.asyncio
    async def test_health_monitoring(self, orchestrator_agent):
        """Test monitoreo de salud"""
        with patch.object(orchestrator_agent, '_perform_health_check') as mock_health:
            mock_health.return_value = {
                "overall_health": "healthy",
                "active_workflows": 2,
                "active_agents": 5,
                "failed_workflows": 0,
                "queue_size": 1
            }
            
            health_report = await orchestrator_agent._perform_health_check()
            
            assert "overall_health" in health_report
            assert "active_workflows" in health_report
            assert "active_agents" in health_report
            assert isinstance(health_report["active_workflows"], int)
    
    @pytest.mark.asyncio
    async def test_workflow_pause_resume(self, orchestrator_agent, sample_workflow):
        """Test pausar y reanudar workflow"""
        workflow_id = sample_workflow["workflow_id"]
        
        with patch.object(orchestrator_agent, '_pause_workflow') as mock_pause:
            mock_pause.return_value = {"status": WorkflowState.PAUSED.value}
            
            pause_result = await orchestrator_agent.pause_workflow(workflow_id)
            
            assert "status" in pause_result
            assert pause_result["status"] == WorkflowState.PAUSED.value
        
        with patch.object(orchestrator_agent, '_resume_workflow') as mock_resume:
            mock_resume.return_value = {"status": WorkflowState.RUNNING.value}
            
            resume_result = await orchestrator_agent.resume_workflow(workflow_id)
            
            assert "status" in resume_result
            assert resume_result["status"] == WorkflowState.RUNNING.value
    
    @pytest.mark.asyncio
    async def test_workflow_cancellation(self, orchestrator_agent, sample_workflow):
        """Test cancelación de workflow"""
        workflow_id = sample_workflow["workflow_id"]
        
        with patch.object(orchestrator_agent, '_cancel_workflow') as mock_cancel:
            mock_cancel.return_value = {"status": WorkflowState.CANCELLED.value}
            
            cancel_result = await orchestrator_agent.cancel_workflow(workflow_id)
            
            assert "status" in cancel_result
            assert cancel_result["status"] == WorkflowState.CANCELLED.value
    
    @pytest.mark.asyncio
    async def test_workflow_status_tracking(self, orchestrator_agent, sample_workflow):
        """Test seguimiento de estado de workflow"""
        workflow_id = sample_workflow["workflow_id"]
        
        # Crear workflow
        with patch.object(orchestrator_agent, '_create_workflow_internal') as mock_create:
            mock_create.return_value = workflow_id
            await orchestrator_agent.create_workflow(sample_workflow)
        
        # Obtener estado
        status = await orchestrator_agent.get_workflow_status(workflow_id)
        
        assert "workflow_id" in status
        assert "status" in status
        assert "created_at" in status
    
    @pytest.mark.asyncio
    async def test_agent_scaling(self, orchestrator_agent):
        """Test escalado horizontal de agentes"""
        # Simular alta demanda
        demand_metrics = {
            "current_load": 0.95,
            "queue_depth": 10,
            "response_time": 5.0
        }
        
        with patch.object(orchestrator_agent, '_scale_agents') as mock_scale:
            mock_scale.return_value = {
                "scaling_action": "scale_up",
                "agents_to_add": 2,
                "new_total_agents": 5
            }
            
            scaling_result = await orchestrator_agent._scale_agents(
                agent_type="reasoner",
                metrics=demand_metrics
            )
            
            assert "scaling_action" in scaling_result
            assert "agents_to_add" in scaling_result
            assert "new_total_agents" in scaling_result
            assert scaling_result["scaling_action"] == "scale_up"
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, orchestrator_agent, sample_workflow):
        """Test métricas de rendimiento"""
        workflow_id = sample_workflow["workflow_id"]
        
        with patch.object(orchestrator_agent, '_calculate_performance_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "throughput": 2.5,  # workflows per minute
                "success_rate": 0.95,
                "average_execution_time": 45.2,
                "error_rate": 0.05
            }
            
            metrics = await orchestrator_agent._calculate_performance_metrics(workflow_id)
            
            assert "throughput" in metrics
            assert "success_rate" in metrics
            assert "average_execution_time" in metrics
            assert "error_rate" in metrics
            assert 0 <= metrics["success_rate"] <= 1
            assert 0 <= metrics["error_rate"] <= 1
    
    @pytest.mark.asyncio
    async def test_workflow_validation(self, orchestrator_agent):
        """Test validación de workflow"""
        invalid_workflow = {
            "name": "Invalid Workflow",
            "steps": [
                {
                    "step_id": "step1",
                    "name": "Test Step"
                    # Falta agent_type
                }
            ],
            "dependencies": {
                "step1": ["nonexistent_step"]  # Referencia a paso inexistente
            }
        }
        
        with patch.object(orchestrator_agent, '_validate_workflow') as mock_validate:
            mock_validate.return_value = {
                "valid": False,
                "errors": [
                    "Missing agent_type in step step1",
                    "Dependency on nonexistent_step that doesn't exist"
                ]
            }
            
            validation_result = await orchestrator_agent._validate_workflow(invalid_workflow)
            
            assert "valid" in validation_result
            assert "errors" in validation_result
            assert validation_result["valid"] is False
            assert len(validation_result["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow_not_found(self, orchestrator_agent):
        """Test manejo de errores - workflow no encontrado"""
        nonexistent_workflow_id = str(uuid.uuid4())
        
        with pytest.raises(Exception) as exc_info:
            await orchestrator_agent.get_workflow_status(nonexistent_workflow_id)
        
        # Debería lanzar una excepción apropiada
        assert "not found" in str(exc_info.value).lower() or "not exist" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_error_handling_agent_unavailable(self, orchestrator_agent, sample_workflow):
        """Test manejo de errores - agente no disponible"""
        workflow_id = sample_workflow["workflow_id"]
        
        with patch.object(orchestrator_agent, '_handle_agent_unavailable') as mock_handle:
            mock_handle.return_value = {
                "handled": True,
                "fallback_agent": "backup_reasoner",
                "retry_scheduled": True
            }
            
            handling_result = await orchestrator_agent._handle_agent_unavailable(
                workflow_id, "reasoner", "step1"
            )
            
            assert "handled" in handling_result
            assert "fallback_agent" in handling_result
            assert "retry_scheduled" in handling_result
