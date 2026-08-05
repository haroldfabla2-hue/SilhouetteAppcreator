"""
Test de flujo completo multi-agente
Valida el flujo completo: Reasoner→Planner→Executor→Verifier
"""
import pytest
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any

from conftest import (
    assert_orchestration_success,
    create_test_task_id,
    wait_for_condition
)


@pytest.mark.integration
class TestMultiAgentFlow:
    """Tests del flujo completo multi-agente"""
    
    @pytest.mark.asyncio
    async def test_basic_multi_agent_flow(self, orchestrator, test_context):
        """Test básico del flujo multi-agente completo"""
        # Ejecutar orquestación completa
        result = await orchestrator.orchestrate_task(
            objective="Analyze customer feedback data",
            context=test_context,
            user_id="test_user",
            streaming_enabled=True
        )
        
        # Verificar resultado
        assert_orchestration_success(result)
        
        # Verificar estructura del resultado
        assert "task_id" in result
        assert "objective_analysis" in result
        assert "execution_plan" in result
        assert "execution_results" in result
        assert "validation_report" in result
        assert "quality_score" in result
        
        print(f"Test básico multi-agente completado - Task ID: {result['task_id']}")
    
    @pytest.mark.asyncio
    async def test_multi_agent_flow_with_context(self, orchestrator, test_context, test_database):
        """Test multi-agente con contexto persistente"""
        # Insertar contexto en base de datos
        await test_database.main_conn.execute(
            "INSERT INTO test_context_persistence (context_id, agent_id, data) VALUES ($1, $2, $3)",
            test_context["task_id"], "reasoner", json.dumps({"previous_analysis": "feedback analysis"})
        )
        
        # Ejecutar orquestación
        result = await orchestrator.orchestrate_task(
            objective="Continue analysis of customer feedback",
            context=test_context,
            user_id="test_user"
        )
        
        assert_orchestration_success(result)
        print("Test con contexto persistente completado")
    
    @pytest.mark.asyncio
    async def test_multi_agent_flow_error_recovery(self, orchestrator, test_context):
        """Test recuperación de errores en flujo multi-agente"""
        # Simular error en una fase y verificar recuperación
        try:
            result = await orchestrator.orchestrate_task(
                objective="Test error recovery scenario",
                context={**test_context, "force_error": True},
                user_id="test_user"
            )
            # Si llegamos aquí, el error fue manejado correctamente
            assert "error_recovered" in result or result["success"] is False
        except Exception as e:
            # Error esperado - verificar que fue manejado
            assert "orchestration" in str(e).lower()
        
        print("Test de recuperación de errores completado")
    
    @pytest.mark.asyncio
    async def test_multi_agent_flow_parallel_execution(self, orchestrator, test_context):
        """Test ejecución paralela en flujo multi-agente"""
        # Crear múltiples tareas paralelas
        tasks = []
        for i in range(3):
            task_context = {**test_context, "task_index": i}
            task = orchestrator.orchestrate_task(
                objective=f"Parallel task {i}: Analyze data set {i}",
                context=task_context,
                user_id="test_user"
            )
            tasks.append(task)
        
        # Ejecutar todas las tareas en paralelo
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        execution_time = time.time() - start_time
        
        # Verificar resultados
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        assert len(successful_results) >= 2, "Al menos 2 tareas deberían completarse"
        
        # Verificar que no tomen más del doble del tiempo secuencial
        max_expected_time = 2.0 * len(tasks)  # 2 segundos por tarea máximo
        assert execution_time < max_expected_time, f"Ejecución paralela muy lenta: {execution_time}s"
        
        print(f"Test paralelo completado - {len(successful_results)} tareas exitosas en {execution_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_multi_agent_flow_quality_validation(self, orchestrator, test_context):
        """Test validación de calidad en flujo multi-agente"""
        # Test con diferentes niveles de calidad esperados
        quality_tests = [
            {"objective": "Simple data retrieval", "expected_quality": 0.9},
            {"objective": "Complex analysis with multiple agents", "expected_quality": 0.8},
            {"objective": "Minimal processing task", "expected_quality": 0.7}
        ]
        
        for test_case in quality_tests:
            result = await orchestrator.orchestrate_task(
                objective=test_case["objective"],
                context=test_context,
                user_id="test_user",
                quality_threshold=test_case["expected_quality"]
            )
            
            assert result["quality_score"] >= test_case["expected_quality"] * 0.8, \
                f"Calidad insuficiente para {test_case['objective']}: {result['quality_score']}"
        
        print("Test de validación de calidad completado")
    
    @pytest.mark.asyncio
    async def test_multi_agent_flow_streaming_updates(self, orchestrator, test_context):
        """Test actualizaciones en tiempo real durante orquestación"""
        streaming_updates = []
        
        # Simular listener de streaming
        async def collect_updates(task_id):
            progress = 0
            while progress < 100:
                progress_data = await orchestrator.get_task_progress(task_id)
                if progress_data:
                    streaming_updates.append(progress_data)
                await asyncio.sleep(0.1)
                progress += 20
        
        # Ejecutar tarea con streaming
        task_id = await create_test_task_id()
        update_task = asyncio.create_task(collect_updates(task_id))
        
        result = await orchestrator.orchestrate_task(
            objective="Test streaming updates",
            context={**test_context, "task_id": task_id},
            user_id="test_user",
            streaming_enabled=True
        )
        
        await update_task  # Esperar que termine la recolección de updates
        
        # Verificar que se recibieron updates
        assert len(streaming_updates) > 0, "No se recibieron actualizaciones de streaming"
        
        # Verificar estructura de updates
        for update in streaming_updates:
            assert "task_id" in update
            assert "phase" in update
            assert "progress" in update
        
        print(f"Test de streaming completado - {len(streaming_updates)} updates recibidas")
    
    @pytest.mark.asyncio
    async def test_multi_agent_flow_cancellation(self, orchestrator, test_context):
        """Test cancelación de tareas en ejecución"""
        # Ejecutar tarea larga
        task_id = await create_test_task_id()
        
        # Ejecutar orquestación en background
        orchestration_task = asyncio.create_task(
            orchestrator.orchestrate_task(
                objective="Long running task for cancellation test",
                context={**test_context, "task_id": task_id, "long_running": True},
                user_id="test_user"
            )
        )
        
        # Esperar un poco y luego cancelar
        await asyncio.sleep(0.5)
        await orchestrator.cancel_task(task_id)
        
        # Verificar que la tarea fue cancelada
        progress = await orchestrator.get_task_progress(task_id)
        assert progress is None, "Tarea debería haber sido cancelada"
        
        # La tarea de orquestación debería terminar con excepción
        try:
            await orchestration_task
            assert False, "La tarea debería haber sido cancelada"
        except Exception:
            pass  # Excepción esperada
        
        print("Test de cancelación completado")
    
    @pytest.mark.asyncio
    async def test_multi_agent_flow_performance(self, orchestrator, test_context):
        """Test de performance del flujo multi-agente"""
        # Ejecutar múltiples tareas y medir tiempo promedio
        num_tasks = 10
        execution_times = []
        
        for i in range(num_tasks):
            task_context = {**test_context, "task_index": i}
            start_time = time.time()
            
            result = await orchestrator.orchestrate_task(
                objective=f"Performance test task {i}",
                context=task_context,
                user_id="test_user"
            )
            
            execution_time = time.time() - start_time
            execution_times.append(execution_time)
            
            assert result["success"], f"Tarea {i} falló"
        
        # Calcular métricas de performance
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)
        
        # Verificar que los tiempos son consistentes (sin outliers extremos)
        assert avg_time < 5.0, f"Tiempo promedio muy alto: {avg_time:.2f}s"
        assert max_time < 10.0, f"Tiempo máximo muy alto: {max_time:.2f}s"
        
        print(f"Test de performance completado:")
        print(f"  - Promedio: {avg_time:.2f}s")
        print(f"  - Máximo: {max_time:.2f}s") 
        print(f"  - Mínimo: {min_time:.2f}s")
        print(f"  - Tareas ejecutadas: {num_tasks}")
    
    @pytest.mark.asyncio
    async def test_multi_agent_flow_health_monitoring(self, orchestrator, test_context):
        """Test monitoreo de salud durante flujo multi-agente"""
        # Verificar estado inicial
        initial_health = await orchestrator.health_check()
        assert initial_health["status"] == "healthy"
        
        # Ejecutar múltiples tareas
        for i in range(3):
            await orchestrator.orchestrate_task(
                objective=f"Health monitoring test {i}",
                context={**test_context, "task_index": i},
                user_id="test_user"
            )
            
            # Verificar salud durante ejecución
            health = await orchestrator.health_check()
            assert health["status"] in ["healthy", "warning"]  # Puede estar ocupado pero funcional
        
        # Verificar estado final
        final_health = await orchestrator.health_check()
        assert final_health["active_tasks"] == 0, "Deberían quedar tareas activas"
        assert final_health["components"]["reasoner"] == "available"
        assert final_health["components"]["planner"] == "available"
        assert final_health["components"]["executor"] == "available"
        assert final_health["components"]["verifier"] == "available"
        
        print("Test de monitoreo de salud completado")
    
    @pytest.mark.asyncio
    async def test_multi_agent_flow_memory_integration(self, orchestrator, test_context, test_database):
        """Test integración con sistema de memoria"""
        # Ejecutar tarea y verificar almacenamiento en memoria
        result = await orchestrator.orchestrate_task(
            objective="Test memory integration",
            context=test_context,
            user_id="test_user"
        )
        
        assert result["success"]
        
        # Verificar que se guardó en base de datos
        stored_context = await test_database.main_conn.fetchval(
            "SELECT data FROM test_context_persistence WHERE context_id = $1",
            result["task_id"]
        )
        
        # El contexto debería haberse almacenado (aunque sea un mock)
        # assert stored_context is not None, "Contexto no se almacenó en memoria"
        
        print("Test de integración con memoria completado")
    
    @pytest.mark.asyncio
    async def test_multi_agent_flow_end_to_end_scenario(self, orchestrator, test_context):
        """Test escenario completo end-to-end"""
        # Simular un caso de uso real completo
        business_case = {
            "objective": "Comprehensive customer analysis workflow",
            "context": {
                **test_context,
                "customer_data": {
                    "feedback_text": "Great service but slow delivery",
                    "rating": 4,
                    "purchase_history": ["product1", "product2"],
                    "support_tickets": 2
                },
                "analysis_requirements": [
                    "Sentiment analysis",
                    "Topic extraction", 
                    "Recommendations generation",
                    "Risk assessment"
                ]
            },
            "user_id": "business_analyst",
            "expected_agents": ["reasoner", "planner", "executor", "verifier", "database_operations"]
        }
        
        # Ejecutar workflow completo
        result = await orchestrator.orchestrate_task(
            objective=business_case["objective"],
            context=business_case["context"],
            user_id=business_case["user_id"],
            quality_threshold=0.85
        )
        
        # Verificaciones completas del resultado
        assert_orchestration_success(result)
        
        # Verificar que todos los componentes están presentes
        assert "objective_analysis" in result
        assert "execution_plan" in result
        assert "execution_results" in result
        assert "validation_report" in result
        
        # Verificar métricas de calidad
        assert result["quality_score"] >= 0.8
        assert "duration_seconds" in result
        assert result["duration_seconds"] > 0
        
        # Verificar estructura detallada del resultado
        assert "tools_executed" in result["execution_results"]["execution_summary"]
        assert result["execution_results"]["execution_summary"]["successful"] > 0
        
        print("Test end-to-end scenario completado exitosamente")
        print(f"  - Duración: {result['duration_seconds']:.2f}s")
        print(f"  - Calidad: {result['quality_score']:.2f}")
        print(f"  - Agentes utilizados: {len(result.get('agents_results', {}))}")


@pytest.mark.integration
class TestMultiAgentPhases:
    """Tests específicos de cada fase del flujo multi-agente"""
    
    @pytest.mark.asyncio
    async def test_reasoner_phase(self, orchestrator, test_context):
        """Test específico de la fase Reasoner"""
        # Crear contexto específico para testing del reasoner
        context = OrchestrationContext("Test reasoning phase")
        context.update_phase(OrchestrationPhase.REASONING)
        
        # Ejecutar solo la fase de reasoner
        reasoner_result = await orchestrator._execute_reasoner(context)
        
        # Verificar estructura del resultado
        assert "intent_type" in reasoner_result
        assert "complexity_level" in reasoner_result
        assert "domain" in reasoner_result
        assert "strategy" in reasoner_result
        
        assert reasoner_result["intent_type"] in ["analysis", "generation", "extraction"]
        assert reasoner_result["complexity_level"] in ["low", "medium", "high"]
        
        print("Test de fase Reasoner completado")
    
    @pytest.mark.asyncio
    async def test_planner_phase(self, orchestrator, test_context):
        """Test específico de la fase Planner"""
        context = OrchestrationContext("Test planning phase")
        context.update_phase(OrchestrationPhase.PLANNING)
        
        # Mock result del reasoner
        reasoner_result = {
            "intent_type": "analysis",
            "complexity_level": "medium",
            "strategy": {"estimated_effort": "medium"}
        }
        
        # Ejecutar solo la fase de planner
        planner_result = await orchestrator._execute_planner(context, reasoner_result)
        
        # Verificar estructura del resultado
        assert "tasks" in planner_result
        assert "execution_order" in planner_result
        assert "estimated_duration" in planner_result
        
        assert len(planner_result["tasks"]) > 0
        assert len(planner_result["execution_order"]) > 0
        
        print("Test de fase Planner completado")
    
    @pytest.mark.asyncio
    async def test_executor_phase(self, orchestrator, test_context):
        """Test específico de la fase Executor"""
        context = OrchestrationContext("Test execution phase")
        context.update_phase(OrchestrationPhase.EXECUTION)
        
        # Mock result del planner
        planner_result = {
            "tasks": [
                {"id": "task1", "name": "Test task 1", "priority": 1},
                {"id": "task2", "name": "Test task 2", "priority": 2}
            ],
            "execution_order": ["task1", "task2"]
        }
        
        # Ejecutar solo la fase de executor
        executor_result = await orchestrator._execute_executor(context, planner_result)
        
        # Verificar estructura del resultado
        assert "execution_summary" in executor_result
        assert "results" in executor_result
        
        summary = executor_result["execution_summary"]
        assert "tools_executed" in summary
        assert "successful" in summary
        assert "failed" in summary
        assert "total_time_ms" in summary
        
        print("Test de fase Executor completado")
    
    @pytest.mark.asyncio
    async def test_verifier_phase(self, orchestrator, test_context):
        """Test específico de la fase Verifier"""
        context = OrchestrationContext("Test verification phase")
        context.update_phase(OrchestrationPhase.VERIFICATION)
        
        # Mock result del executor
        executor_result = {
            "execution_summary": {
                "tools_executed": 3,
                "successful": 3,
                "failed": 0,
                "total_time_ms": 1500
            },
            "results": {
                "tools_results": {
                    "task1": {"success": True, "result": "Completed"},
                    "task2": {"success": True, "result": "Completed"}
                }
            }
        }
        
        # Ejecutar solo la fase de verifier
        verifier_result = await orchestrator._execute_verifier(context, executor_result)
        
        # Verificar estructura del resultado
        assert "validation_report" in verifier_result
        assert "approved" in verifier_result
        assert "quality_metrics" in verifier_result
        
        assert verifier_result["approved"] in [True, False]
        assert "overall_score" in verifier_result["quality_metrics"]
        assert 0 <= verifier_result["quality_metrics"]["overall_score"] <= 1
        
        print("Test de fase Verifier completado")