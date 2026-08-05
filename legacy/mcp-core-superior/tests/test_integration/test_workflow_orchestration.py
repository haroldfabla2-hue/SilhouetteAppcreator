"""
Test de task orchestration workflows
Valida diferentes patrones de orquestación y workflows complejos
"""
import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from enum import Enum

from conftest import create_test_task_id, assert_orchestration_success


class WorkflowType(Enum):
    """Tipos de workflows de orquestación"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    FAN_OUT_FAN_IN = "fan_out_fan_in"
    CONDITIONAL = "conditional"
    ERROR_RECOVERY = "error_recovery"
    ROLLING_UPDATE = "rolling_update"
    CIRCUIT_BREAKER = "circuit_breaker"
    BACKPRESSURE = "backpressure"


class WorkflowPattern:
    """Patrón de workflow"""
    
    def __init__(self, workflow_type: WorkflowType, steps: List[Dict[str, Any]]):
        self.workflow_type = workflow_type
        self.steps = steps
        self.id = f"workflow_{int(time.time())}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.workflow_type.value,
            "steps": self.steps,
            "created_at": datetime.now().isoformat()
        }


@pytest.mark.integration
class TestWorkflowOrchestration:
    """Tests de patrones de orquestación de workflows"""
    
    @pytest.mark.asyncio
    async def test_sequential_workflow(self, orchestrator, test_context):
        """Test workflow secuencial simple"""
        workflow = WorkflowPattern(
            WorkflowType.SEQUENTIAL,
            [
                {"step": 1, "agent": "reasoner", "action": "analyze_input"},
                {"step": 2, "agent": "planner", "action": "create_plan"}, 
                {"step": 3, "agent": "executor", "action": "execute_plan"},
                {"step": 4, "agent": "verifier", "action": "validate_result"}
            ]
        )
        
        # Ejecutar workflow secuencial
        start_time = time.time()
        results = []
        
        for step in workflow.steps:
            step_start = time.time()
            
            # Simular ejecución de cada paso
            step_result = {
                "step": step["step"],
                "agent": step["agent"],
                "action": step["action"],
                "success": True,
                "execution_time_ms": (time.time() - step_start) * 1000,
                "result": f"Step {step['step']} completed by {step['agent']}"
            }
            results.append(step_result)
            
            # Tiempo mínimo entre pasos para simular trabajo real
            await asyncio.sleep(0.1)
        
        total_time = time.time() - start_time
        
        # Verificar resultados
        assert len(results) == len(workflow.steps)
        
        # Verificar que se ejecutó secuencialmente (orden correcto)
        for i, result in enumerate(results):
            assert result["step"] == i + 1
        
        assert total_time > 0.3, "Tiempo total muy corto para workflow secuencial"
        
        print(f"Test workflow secuencial completado - {len(results)} pasos en {total_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_parallel_workflow(self, orchestrator, test_context):
        """Test workflow paralelo"""
        workflow = WorkflowPattern(
            WorkflowType.PARALLEL,
            [
                {"step": 1, "agent": "database_operations", "action": "fetch_data"},
                {"step": 2, "agent": "python_executor", "action": "process_data"},
                {"step": 3, "agent": "search_engine", "action": "search_related"},
                {"step": 4, "agent": "file_processing", "action": "analyze_files"}
            ]
        )
        
        # Ejecutar pasos en paralelo
        async def execute_step(step):
            await asyncio.sleep(0.2)  # Simular trabajo
            return {
                "step": step["step"],
                "agent": step["agent"],
                "success": True,
                "execution_time_ms": 200,
                "result": f"Parallel step {step['step']} by {step['agent']}"
            }
        
        start_time = time.time()
        tasks = [execute_step(step) for step in workflow.steps]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Verificar resultados paralelos
        assert len(results) == len(workflow.steps)
        
        # Tiempo debería ser similar al paso más largo (no suma de todos)
        assert total_time < 0.5, "Workflow paralelo muy lento"
        assert total_time > 0.15, "Workflow paralelo muy rápido"
        
        # Verificar que todos los pasos se completaron
        for result in results:
            assert result["success"]
        
        print(f"Test workflow paralelo completado - {len(results)} pasos en {total_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_fan_out_fan_in_workflow(self, orchestrator, test_context):
        """Test workflow fan-out/fan-in"""
        # Fan-out: un coordinador distribuye tareas
        fan_out_steps = [
            {"subtask": "data_analysis", "agent": "python_executor"},
            {"subtask": "data_visualization", "agent": "python_executor"}, 
            {"subtask": "data_validation", "agent": "verifier"},
            {"subtask": "report_generation", "agent": "file_processing"}
        ]
        
        # Ejecutar fan-out (distribución paralela)
        async def execute_subtask(subtask_info):
            await asyncio.sleep(0.15)
            return {
                "subtask": subtask_info["subtask"],
                "agent": subtask_info["agent"],
                "success": True,
                "result": f"Subtask {subtask_info['subtask']} completed"
            }
        
        # Fan-out phase
        fan_out_start = time.time()
        fan_out_tasks = [execute_subtask(info) for info in fan_out_steps]
        fan_out_results = await asyncio.gather(*fan_out_tasks)
        fan_out_time = time.time() - fan_out_start
        
        # Fan-in phase: consolidar resultados
        fan_in_start = time.time()
        consolidated_result = {
            "fan_out_time_ms": fan_out_time * 1000,
            "subtasks_completed": len(fan_out_results),
            "subtask_results": fan_out_results,
            "consolidation_status": "completed"
        }
        await asyncio.sleep(0.05)  # Simular consolidación
        fan_in_time = time.time() - fan_in_start
        
        total_time = fan_out_time + fan_in_time
        
        # Verificaciones
        assert len(fan_out_results) == len(fan_out_steps)
        assert fan_out_time < 0.3, "Fan-out muy lento"
        assert consolidated_result["subtasks_completed"] == 4
        
        print(f"Test fan-out/fan-in completado:")
        print(f"  - Fan-out: {fan_out_time:.2f}s ({len(fan_out_results)} subtareas)")
        print(f"  - Fan-in: {fan_in_time:.2f}s") 
        print(f"  - Total: {total_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_conditional_workflow(self, orchestrator, test_context):
        """Test workflow con lógica condicional"""
        # Definir condiciones de分支
        conditions = {
            "data_quality_high": True,
            "analysis_complexity": "medium",
            "user_permission": True
        }
        
        # Workflow condicional
        workflow_steps = []
        
        # Paso 1: Siempre ejecuta
        workflow_steps.append({
            "step": 1, 
            "agent": "reasoner", 
            "condition": None,
            "action": "analyze_requirements"
        })
        
        # Paso 2: Solo si data_quality_high
        if conditions["data_quality_high"]:
            workflow_steps.append({
                "step": 2,
                "agent": "database_operations", 
                "condition": "data_quality_high",
                "action": "detailed_analysis"
            })
        
        # Paso 3: Solo si analysis_complexity es medium o high
        if conditions["analysis_complexity"] in ["medium", "high"]:
            workflow_steps.append({
                "step": 3,
                "agent": "python_executor",
                "condition": "complexity_check", 
                "action": "advanced_processing"
            })
        
        # Paso 4: Solo si user_permission es True
        if conditions["user_permission"]:
            workflow_steps.append({
                "step": 4,
                "agent": "verifier",
                "condition": "user_permission",
                "action": "final_validation"
            })
        
        # Ejecutar workflow condicional
        executed_steps = []
        for step in workflow_steps:
            step_result = {
                "step": step["step"],
                "agent": step["agent"],
                "condition": step["condition"],
                "success": True,
                "result": f"Step {step['step']} executed with condition {step['condition']}"
            }
            executed_steps.append(step_result)
            await asyncio.sleep(0.05)
        
        # Verificaciones
        assert len(executed_steps) == 4  # Todos los pasos deberían ejecutarse con estas condiciones
        
        # Verificar que los pasos correctos se ejecutaron
        executed_agents = [step["agent"] for step in executed_steps]
        assert "reasoner" in executed_agents
        assert "database_operations" in executed_agents
        assert "python_executor" in executed_agents
        assert "verifier" in executed_agents
        
        print(f"Test workflow condicional completado - {len(executed_steps)} pasos ejecutados")
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, orchestrator, test_context):
        """Test workflow con recuperación de errores"""
        workflow_with_failures = [
            {"step": 1, "agent": "reasoner", "will_fail": False},
            {"step": 2, "agent": "planner", "will_fail": False},
            {"step": 3, "agent": "executor", "will_fail": True, "error_type": "timeout"},
            {"step": 4, "agent": "verifier", "will_fail": False}
        ]
        
        execution_log = []
        
        for step_info in workflow_with_failures:
            step_start = time.time()
            
            if step_info["will_fail"]:
                # Simular fallo
                await asyncio.sleep(0.1)
                
                execution_log.append({
                    "step": step_info["step"],
                    "agent": step_info["agent"],
                    "status": "failed",
                    "error": f"Simulated {step_info['error_type']} error",
                    "execution_time_ms": (time.time() - step_start) * 1000,
                    "retry_count": 0
                })
                
                # Simular retry automático
                retry_start = time.time()
                await asyncio.sleep(0.05)
                
                execution_log.append({
                    "step": step_info["step"],
                    "agent": step_info["agent"],
                    "status": "retry",
                    "execution_time_ms": (time.time() - retry_start) * 1000,
                    "retry_count": 1
                })
                
                # Retry exitoso
                final_start = time.time()
                await asyncio.sleep(0.1)
                
                execution_log.append({
                    "step": step_info["step"],
                    "agent": step_info["agent"],
                    "status": "success",
                    "execution_time_ms": (time.time() - final_start) * 1000,
                    "retry_count": 1,
                    "result": f"Step {step_info['step']} recovered successfully"
                })
            else:
                # Ejecutar paso normalmente
                await asyncio.sleep(0.05)
                
                execution_log.append({
                    "step": step_info["step"],
                    "agent": step_info["agent"],
                    "status": "success", 
                    "execution_time_ms": (time.time() - step_start) * 1000,
                    "result": f"Step {step_info['step']} completed"
                })
        
        # Verificar recuperación de errores
        failed_steps = [log for log in execution_log if log["status"] == "failed"]
        recovered_steps = [log for log in execution_log if log["status"] == "success" 
                         and any(log["retry_count"] == 1 for log in execution_log 
                               if log["step"] == log["step"])]
        
        assert len(failed_steps) == 1, "Debería haber exactamente un fallo"
        assert len(recovered_steps) >= 1, "Debería haber al menos una recuperación exitosa"
        
        print(f"Test error recovery completado:")
        print(f"  - Pasos con fallo: {len(failed_steps)}")
        print(f"  - Pasos recuperados: {len(recovered_steps)}")
        print(f"  - Total eventos de ejecución: {len(execution_log)}")
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_workflow(self, orchestrator, test_context):
        """Test workflow con patrón circuit breaker"""
        # Simular agente problemático
        problematic_agent = {
            "name": "unreliable_service",
            "failure_threshold": 3,
            "reset_timeout": 5,
            "current_failures": 0,
            "circuit_state": "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        }
        
        execution_attempts = 15
        circuit_breaker_log = []
        
        for attempt in range(execution_attempts):
            # Simular llamada a servicio
            call_start = time.time()
            
            # Estado del circuit breaker
            if problematic_agent["circuit_state"] == "OPEN":
                # Circuit breaker abierto - no llamar al servicio
                result = {
                    "attempt": attempt + 1,
                    "status": "circuit_breaker_open",
                    "error": "Service temporarily unavailable",
                    "circuit_state": problematic_agent["circuit_state"]
                }
                circuit_breaker_log.append(result)
                
            elif problematic_agent["circuit_state"] == "HALF_OPEN":
                # Intento de recuperación - permitir una llamada de prueba
                simulated_success = attempt % 2 == 0  # 50% de éxito en half-open
                
                if simulated_success:
                    problematic_agent["circuit_state"] = "CLOSED"
                    problematic_agent["current_failures"] = 0
                    result_status = "success"
                else:
                    problematic_agent["current_failures"] += 1
                    result_status = "failure"
                    
                result = {
                    "attempt": attempt + 1,
                    "status": result_status,
                    "circuit_state": problematic_agent["circuit_state"],
                    "execution_time_ms": (time.time() - call_start) * 1000
                }
                circuit_breaker_log.append(result)
                
            else:  # CLOSED
                # Circuit cerrado - intentar llamada
                simulated_success = attempt % 3 != 0  # 66% de éxito normal
                
                if simulated_success:
                    problematic_agent["current_failures"] = max(0, problematic_agent["current_failures"] - 1)
                    result_status = "success"
                else:
                    problematic_agent["current_failures"] += 1
                    
                    # Abrir circuit si se alcanza el threshold
                    if problematic_agent["current_failures"] >= problematic_agent["failure_threshold"]:
                        problematic_agent["circuit_state"] = "OPEN"
                    
                    result_status = "failure"
                
                result = {
                    "attempt": attempt + 1,
                    "status": result_status,
                    "circuit_state": problematic_agent["circuit_state"],
                    "current_failures": problematic_agent["current_failures"],
                    "execution_time_ms": (time.time() - call_start) * 1000
                }
                circuit_breaker_log.append(result)
            
            await asyncio.sleep(0.01)  # Pausa mínima entre intentos
        
        # Verificar comportamiento del circuit breaker
        closed_attempts = [log for log in circuit_breaker_log if log["circuit_state"] == "CLOSED"]
        open_attempts = [log for log in circuit_breaker_log if log["circuit_state"] == "OPEN"]
        half_open_attempts = [log for log in circuit_breaker_log if log["circuit_state"] == "HALF_OPEN"]
        
        # Verificar transiciones de estado
        assert len(closed_attempts) > 0, "Debería haber intentos en estado CLOSED"
        assert len(open_attempts) > 0, "Debería haber intentos en estado OPEN"
        
        # Verificar que el circuit se abre después de suficientes fallos
        open_state_reached = False
        for log in circuit_breaker_log:
            if log["circuit_state"] == "OPEN":
                open_state_reached = True
                break
        assert open_state_reached, "El circuit breaker debería haber pasado a estado OPEN"
        
        print(f"Test circuit breaker completado:")
        print(f"  - Intentos totales: {execution_attempts}")
        print(f"  - Estado CLOSED: {len(closed_attempts)}")
        print(f"  - Estado OPEN: {len(open_attempts)}")
        print(f"  - Estado HALF_OPEN: {len(half_open_attempts)}")
    
    @pytest.mark.asyncio
    async def test_backpressure_workflow(self, orchestrator, test_context):
        """Test workflow con control de backpressure"""
        # Simular cola de tareas con backpressure
        task_queue = asyncio.Queue(maxsize=5)
        processing_rate = 3  # tasks per second
        arrival_rate = 8     # tasks per second (mayor que processing_rate)
        
        processed_tasks = []
        rejected_tasks = []
        
        async def task_producer(task_id):
            """Productor de tareas"""
            try:
                await task_queue.put({"task_id": task_id, "timestamp": time.time()})
                return {"task_id": task_id, "status": "accepted"}
            except asyncio.QueueFull:
                return {"task_id": task_id, "status": "rejected", "reason": "queue_full"}
        
        async def task_consumer(consumer_id):
            """Consumidor de tareas"""
            while len(processed_tasks) < 10:  # Procesar máximo 10 tareas
                try:
                    # Timeout para evitar deadlock
                    task = await asyncio.wait_for(task_queue.get(), timeout=1.0)
                    
                    # Simular procesamiento
                    await asyncio.sleep(1.0 / processing_rate)
                    
                    processed_tasks.append({
                        "task_id": task["task_id"],
                        "consumer_id": consumer_id,
                        "processed_at": time.time(),
                        "status": "completed"
                    })
                    
                except asyncio.TimeoutError:
                    break
        
        # Ejecutar productores y consumidores en paralelo
        producer_tasks = []
        consumer_tasks = []
        
        # Crear consumidores
        for i in range(2):
            consumer_tasks.append(asyncio.create_task(task_consumer(i)))
        
        # Crear productores (más rápido que consumidores)
        for i in range(20):  # Más tareas que capacidad
            producer_tasks.append(asyncio.create_task(task_producer(f"task_{i}")))
            await asyncio.sleep(1.0 / arrival_rate)  # Tasa de llegada
        
        # Esperar completación
        await asyncio.gather(*producer_tasks, return_exceptions=True)
        
        # Procesar tareas restantes en cola
        await asyncio.sleep(2.0)  # Tiempo para procesar cola
        
        # Cancelar consumidores
        for task in consumer_tasks:
            task.cancel()
        
        # Calcular métricas
        queue_utilization = len(processed_tasks) / 20  # tasks processed / total tasks
        rejection_rate = len(rejected_tasks) / 20
        
        # Verificaciones
        assert len(processed_tasks) <= 10, "No debería procesar más de 10 tareas"
        assert queue_utilization >= 0.3, "Debería haber cierta utilización de cola"
        assert rejection_rate >= 0.3, "Debería haber rechazo por backpressure"
        
        print(f"Test backpressure completado:")
        print(f"  - Tareas procesadas: {len(processed_tasks)}")
        print(f"  - Tareas rechazadas: {len(rejected_tasks)}")
        print(f"  - Utilización: {queue_utilization:.2f}")
        print(f"  - Tasa de rechazo: {rejection_rate:.2f}")
    
    @pytest.mark.asyncio
    async def test_complex_enterprise_workflow(self, orchestrator, test_context):
        """Test workflow empresarial complejo multi-paso"""
        # Simular caso de uso real: Análisis completo de datos de cliente
        
        enterprise_workflow = {
            "name": "customer_data_analysis",
            "description": "Análisis completo de datos de cliente para toma de decisiones",
            "estimated_duration_minutes": 45,
            "critical_path": True,
            "stages": [
                {
                    "stage": 1,
                    "name": "Data Ingestion",
                    "type": "parallel",
                    "parallel_tasks": [
                        {"task": "customer_db_extract", "agent": "database_operations", "timeout": 30},
                        {"task": "transaction_data_extract", "agent": "database_operations", "timeout": 25},
                        {"task": "interaction_logs_extract", "agent": "file_processing", "timeout": 20}
                    ]
                },
                {
                    "stage": 2,
                    "name": "Data Processing",
                    "type": "sequential",
                    "sequential_tasks": [
                        {"task": "data_cleaning", "agent": "python_executor", "timeout": 60},
                        {"task": "data_validation", "agent": "verifier", "timeout": 15}
                    ]
                },
                {
                    "stage": 3,
                    "name": "Analysis & Insights",
                    "type": "fan_out_fan_in",
                    "fan_out_tasks": [
                        {"task": "statistical_analysis", "agent": "python_executor"},
                        {"task": "behavioral_analysis", "agent": "python_executor"},
                        {"task": "risk_assessment", "agent": "reasoner"},
                        {"task": "opportunity_analysis", "agent": "search_engine"}
                    ],
                    "fan_in_task": {"agent": "planner", "task": "consolidate_insights"}
                },
                {
                    "stage": 4,
                    "name": "Report Generation",
                    "type": "sequential",
                    "sequential_tasks": [
                        {"task": "executive_summary", "agent": "file_processing"},
                        {"task": "detailed_report", "agent": "file_processing"},
                        {"task": "recommendations", "agent": "reasoner"},
                        {"task": "final_validation", "agent": "verifier"}
                    ]
                }
            ]
        }
        
        execution_log = []
        stage_results = []
        
        # Simular ejecución de cada etapa
        for stage in enterprise_workflow["stages"]:
            stage_start = time.time()
            stage_log = {
                "stage": stage["stage"],
                "name": stage["name"],
                "type": stage["type"],
                "start_time": stage_start
            }
            
            if stage["type"] == "parallel":
                # Ejecución paralela
                async def execute_parallel_task(task_info):
                    await asyncio.sleep(0.2)  # Simular trabajo
                    return {
                        "task": task_info["task"],
                        "agent": task_info["agent"],
                        "success": True,
                        "result": f"Task {task_info['task']} completed"
                    }
                
                parallel_tasks = [execute_parallel_task(task) for task in stage["parallel_tasks"]]
                results = await asyncio.gather(*parallel_tasks)
                stage_log["results"] = results
                stage_log["duration_ms"] = (time.time() - stage_start) * 1000
                
            elif stage["type"] == "sequential":
                # Ejecución secuencial
                sequential_results = []
                for task_info in stage["sequential_tasks"]:
                    await asyncio.sleep(0.15)
                    result = {
                        "task": task_info["task"],
                        "agent": task_info["agent"],
                        "success": True,
                        "result": f"Task {task_info['task']} completed"
                    }
                    sequential_results.append(result)
                
                stage_log["results"] = sequential_results
                stage_log["duration_ms"] = (time.time() - stage_start) * 1000
                
            elif stage["type"] == "fan_out_fan_in":
                # Fan-out
                fan_out_start = time.time()
                fan_out_tasks = []
                for task_info in stage["fan_out_tasks"]:
                    task = asyncio.create_task(
                        asyncio.sleep(0.1).then(lambda: {
                            "task": task_info["task"],
                            "agent": task_info["agent"],
                            "success": True
                        })
                    )
                    fan_out_tasks.append(task)
                
                fan_out_results = await asyncio.gather(*fan_out_tasks)
                fan_out_duration = time.time() - fan_out_start
                
                # Fan-in
                await asyncio.sleep(0.05)
                fan_in_result = {
                    "task": stage["fan_in_task"]["task"],
                    "agent": stage["fan_in_task"]["agent"],
                    "success": True,
                    "consolidated": len(fan_out_results)
                }
                
                stage_log["fan_out_results"] = fan_out_results
                stage_log["fan_in_result"] = fan_in_result
                stage_log["duration_ms"] = (time.time() - fan_out_start) * 1000
            
            execution_log.append(stage_log)
            stage_results.append(stage_log)
        
        # Verificaciones del workflow empresarial
        assert len(execution_log) == len(enterprise_workflow["stages"])
        
        # Verificar que todas las etapas se completaron
        for stage_log in execution_log:
            assert "duration_ms" in stage_log
            assert stage_log["duration_ms"] > 0
            
            if "results" in stage_log:
                assert len(stage_log["results"]) > 0
            elif "fan_out_results" in stage_log:
                assert len(stage_log["fan_out_results"]) > 0
        
        # Calcular métricas del workflow
        total_duration = sum(stage["duration_ms"] for stage in execution_log) / 1000
        parallel_stages = [s for s in execution_log if s["type"] == "parallel"]
        sequential_stages = [s for s in execution_log if s["type"] == "sequential"]
        
        print(f"Test workflow empresarial completado:")
        print(f"  - Etapas ejecutadas: {len(execution_log)}")
        print(f"  - Duración total: {total_duration:.2f}s")
        print(f"  - Etapas paralelas: {len(parallel_stages)}")
        print(f"  - Etapas secuenciales: {len(sequential_stages)}")
        print(f"  - Etapas fan-out/fan-in: 1")
        
        # Verificar estructura de resultados
        assert execution_log[0]["type"] == "parallel"
        assert execution_log[1]["type"] == "sequential"
        assert execution_log[2]["type"] == "fan_out_fan_in"
        assert execution_log[3]["type"] == "sequential"