"""
Script de validación para Multi-Agent Orchestrator Agent MCP
Verifica funcionalidad completa y capacidades avanzadas
"""

import asyncio
import json
import sys
import os
import traceback
from datetime import datetime

# Añadir el path del src para importaciones
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from agents.multiagent_orchestrator_agent import (
        MultiAgentOrchestratorAgentWrapper,
        WorkflowStep,
        AgentCapability,
        TaskPriority,
        WorkflowState,
        LoadBalancingStrategy
    )
    from agents import BaseAgentWrapper, AgentCapability as BaseCapability
    ORCHESTRATOR_IMPORTED = True
except ImportError as e:
    print(f"❌ Error importando MultiAgentOrchestratorAgent: {e}")
    ORCHESTRATOR_IMPORTED = False


class ValidationResults:
    """Resultados de validación"""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.tests_skipped = 0
        self.results = []
    
    def add_result(self, test_name: str, passed: bool, message: str = "", details: dict = None):
        """Añadir resultado de test"""
        if passed:
            self.tests_passed += 1
            status = "✅ PASS"
        else:
            self.tests_failed += 1
            status = "❌ FAIL"
        
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.results.append(result)
        print(f"{status} {test_name}: {message}")
    
    def skip_test(self, test_name: str, reason: str):
        """Omitir test"""
        self.tests_skipped += 1
        print(f"⏭️ SKIP {test_name}: {reason}")
        self.results.append({
            "test": test_name,
            "status": "⏭️ SKIP",
            "message": reason,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_summary(self) -> dict:
        """Obtener resumen"""
        total = self.tests_passed + self.tests_failed + self.tests_skipped
        
        return {
            "total_tests": total,
            "passed": self.tests_passed,
            "failed": self.tests_failed,
            "skipped": self.tests_skipped,
            "success_rate": (self.tests_passed / max(total - self.tests_skipped, 1)) * 100,
            "results": self.results
        }


async def test_basic_initialization():
    """Test: Inicialización básica del orquestrador"""
    results = ValidationResults()
    
    try:
        # Test 1: Crear instancia
        orchestrator = MultiAgentOrchestratorAgentWrapper()
        results.add_result(
            "Crear instancia del orquestrador",
            True,
            f"Orquestrador creado con nombre: {orchestrator.agent_name}"
        )
        
        # Test 2: Verificar capacidades
        capabilities = orchestrator.get_capabilities()
        expected_capabilities = [
            AgentCapability.TASK_DECOMPOSITION,
            AgentCapability.TOOL_SELECTION,
            AgentCapability.DEPENDENCY_MANAGEMENT,
            AgentCapability.CONCURRENT_EXECUTION,
            AgentCapability.QUALITY_VALIDATION,
            AgentCapability.KNOWLEDGE_STORAGE
        ]
        
        has_all_capabilities = all(cap in capabilities for cap in expected_capabilities)
        results.add_result(
            "Verificar capacidades del orquestrador",
            has_all_capabilities,
            f"Capacidades encontradas: {len(capabilities)}",
            {"capabilities": [cap.value for cap in capabilities]}
        )
        
        # Test 3: Estado inicial
        status = orchestrator.get_status()
        expected_initial = {
            "is_ready": False,  # No inicializado aún
            "is_busy": False,
            "utilization": 0.0
        }
        
        state_correct = (
            status.get("is_ready") == expected_initial["is_ready"] and
            status.get("is_busy") == expected_initial["is_busy"] and
            status.get("utilization") == expected_initial["utilization"]
        )
        
        results.add_result(
            "Estado inicial correcto",
            state_correct,
            f"Estado inicial verificado",
            {"status": status}
        )
        
        # Test 4: Health check inicial
        health = await orchestrator.health_check()
        health_ok = health.get("status") in ["healthy", "warning", "unhealthy"]
        results.add_result(
            "Health check inicial",
            health_ok,
            f"Health check: {health.get('status')}",
            {"health": health}
        )
        
        await orchestrator.cleanup()
        
    except Exception as e:
        results.add_result(
            "Inicialización básica",
            False,
            f"Error: {str(e)}",
            {"error": traceback.format_exc()}
        )
    
    return results


async def test_workflow_creation():
    """Test: Creación y gestión de workflows"""
    results = ValidationResults()
    
    try:
        orchestrator = MultiAgentOrchestratorAgentWrapper()
        
        # Test 1: Crear workflow simple
        simple_steps = [
            WorkflowStep(
                step_id="test_step_1",
                agent_type="reasoner",
                capability=AgentCapability.INTENT_ANALYSIS,
                task={"objective": "Test workflow"},
                priority=TaskPriority.NORMAL
            )
        ]
        
        workflow_id = await orchestrator.create_workflow(
            objective="Test workflow simple",
            workflow_steps=simple_steps,
            priority=TaskPriority.NORMAL
        )
        
        results.add_result(
            "Crear workflow simple",
            bool(workflow_id),
            f"Workflow ID: {workflow_id}",
            {"workflow_id": workflow_id}
        )
        
        # Test 2: Obtener estado del workflow
        status = await orchestrator.get_workflow_status(workflow_id)
        status_ok = status is not None and status.get("workflow_id") == workflow_id
        
        results.add_result(
            "Obtener estado de workflow",
            status_ok,
            f"Estado obtenido para workflow {workflow_id}",
            {"status": status}
        )
        
        # Test 3: Crear workflow con dependencias
        complex_steps = [
            WorkflowStep(
                step_id="step_1",
                agent_type="reasoner",
                capability=AgentCapability.INTENT_ANALYSIS,
                task={"objective": "Paso 1"}
            ),
            WorkflowStep(
                step_id="step_2", 
                agent_type="planner",
                capability=AgentCapability.TASK_DECOMPOSITION,
                task={"complexity": "medium"},
                dependencies=["step_1"]
            )
        ]
        
        complex_workflow_id = await orchestrator.create_workflow(
            objective="Test workflow con dependencias",
            workflow_steps=complex_steps,
            priority=TaskPriority.HIGH
        )
        
        results.add_result(
            "Crear workflow con dependencias",
            bool(complex_workflow_id),
            f"Workflow complejo creado: {complex_workflow_id}",
            {"workflow_id": complex_workflow_id}
        )
        
        # Test 4: Cancelar workflow
        cancelled = await orchestrator.cancel_workflow(complex_workflow_id)
        results.add_result(
            "Cancelar workflow",
            cancelled,
            f"Workflow {complex_workflow_id} cancelado"
        )
        
        await orchestrator.cleanup()
        
    except Exception as e:
        results.add_result(
            "Gestión de workflows",
            False,
            f"Error: {str(e)}",
            {"error": traceback.format_exc()}
        )
    
    return results


async def test_specialized_agents():
    """Test: Registro y gestión de agentes especializados"""
    results = ValidationResults()
    
    try:
        orchestrator = MultiAgentOrchestratorAgentWrapper()
        
        # Crear agente especializado de prueba
        class TestAgentWrapper(BaseAgentWrapper):
            def __init__(self):
                super().__init__(
                    agent_name="test_specialist",
                    capabilities=[BaseCapability.TOOL_INVOCATION],
                    max_concurrent=1
                )
            
            async def process_request(self, request, context=None):
                return {"test": "success", "data": request}
        
        test_agent = TestAgentWrapper()
        
        # Test 1: Registrar agente especializado
        registered = await orchestrator.register_specialized_agent(
            "test_specialist",
            test_agent,
            {"metadata": "test_agent"}
        )
        
        results.add_result(
            "Registrar agente especializado",
            registered,
            f"Agente test_specialist registrado",
            {"registered": registered}
        )
        
        # Test 2: Verificar agente registrado
        all_agents = orchestrator._get_all_agents()
        agent_found = any(agent.agent_name == "test_specialist" for agent in all_agents)
        
        results.add_result(
            "Verificar agente registrado",
            agent_found,
            f"Agente encontrado en lista de agentes",
            {"total_agents": len(all_agents)}
        )
        
        # Test 3: Workflow con agente especializado
        specialized_steps = [
            WorkflowStep(
                step_id="specialized_step",
                agent_type="test_specialist",
                capability=BaseCapability.TOOL_INVOCATION,
                task={"test_data": "specialized_workflow"},
                priority=TaskPriority.NORMAL
            )
        ]
        
        specialized_workflow_id = await orchestrator.create_workflow(
            objective="Test con agente especializado",
            workflow_steps=specialized_steps
        )
        
        results.add_result(
            "Workflow con agente especializado",
            bool(specialized_workflow_id),
            f"Workflow especializado creado: {specialized_workflow_id}"
        )
        
        await orchestrator.cleanup()
        
    except Exception as e:
        results.add_result(
            "Agentes especializados",
            False,
            f"Error: {str(e)}",
            {"error": traceback.format_exc()}
        )
    
    return results


async def test_mcp_requests():
    """Test: Requests MCP del orquestrador"""
    results = ValidationResults()
    
    try:
        orchestrator = MultiAgentOrchestratorAgentWrapper()
        
        # Test 1: Request get_status
        status_request = {"type": "get_status"}
        status_response = await orchestrator.process_request(status_request)
        
        results.add_result(
            "MCP request get_status",
            status_response.get("success", False),
            "Request get_status procesado",
            {"response_keys": list(status_response.keys())}
        )
        
        # Test 2: Request get_health
        health_request = {"type": "get_health"}
        health_response = await orchestrator.process_request(health_request)
        
        results.add_result(
            "MCP request get_health", 
            health_response.get("success", False),
            "Request get_health procesado",
            {"health_status": health_response.get("health", {}).get("status")}
        )
        
        # Test 3: Request list_agents
        list_request = {"type": "list_agents"}
        list_response = await orchestrator.process_request(list_request)
        
        results.add_result(
            "MCP request list_agents",
            list_response.get("success", False),
            f"Agentes listados: {list_response.get('total', 0)}",
            {"agents_count": list_response.get("total", 0)}
        )
        
        # Test 4: Request create_workflow
        create_request = {
            "type": "create_workflow",
            "objective": "Test MCP workflow creation",
            "steps": [
                {
                    "step_id": "mcp_step",
                    "agent_type": "reasoner",
                    "capability": "intent_analysis",
                    "task": {"objective": "MCP test"}
                }
            ],
            "priority": 2
        }
        
        create_response = await orchestrator.process_request(create_request)
        workflow_created = create_response.get("success", False)
        
        results.add_result(
            "MCP request create_workflow",
            workflow_created,
            f"Workflow creado via MCP: {create_response.get('workflow_id')}",
            {"workflow_id": create_response.get("workflow_id")}
        )
        
        await orchestrator.cleanup()
        
    except Exception as e:
        results.add_result(
            "Requests MCP",
            False,
            f"Error: {str(e)}",
            {"error": traceback.format_exc()}
        )
    
    return results


async def test_advanced_features():
    """Test: Características avanzadas del orquestrador"""
    results = ValidationResults()
    
    try:
        orchestrator = MultiAgentOrchestratorAgentWrapper()
        
        # Test 1: Load balancer
        load_balancer = orchestrator.load_balancer
        lb_strategy = load_balancer.strategy
        results.add_result(
            "Load Balancer configurado",
            lb_strategy in LoadBalancingStrategy,
            f"Estrategia: {lb_strategy.value}",
            {"strategy": lb_strategy.value}
        )
        
        # Test 2: Task Queue
        queue_size = await orchestrator.task_queue.get_queue_size()
        results.add_result(
            "Task Queue funcional",
            queue_size >= 0,
            f"Tamaño inicial de cola: {queue_size}"
        )
        
        # Test 3: Health Monitor
        health_monitor = orchestrator.health_monitor
        results.add_result(
            "Health Monitor configurado",
            health_monitor is not None,
            f"Monitor de salud inicializado con intervalo: {health_monitor.check_interval}s"
        )
        
        # Test 4: Métricas del workflow
        metrics = orchestrator.workflow_metrics
        required_metrics = [
            "total_workflows", "successful_workflows", "failed_workflows",
            "average_completion_time", "peak_concurrent_workflows"
        ]
        
        has_all_metrics = all(metric in metrics for metric in required_metrics)
        results.add_result(
            "Métricas del workflow",
            has_all_metrics,
            "Métricas configuradas correctamente",
            {"metrics": list(metrics.keys())}
        )
        
        await orchestrator.cleanup()
        
    except Exception as e:
        results.add_result(
            "Características avanzadas",
            False,
            f"Error: {str(e)}",
            {"error": traceback.format_exc()}
        )
    
    return results


async def run_validation():
    """Ejecutar validación completa"""
    print("🧪 Iniciando validación del Multi-Agent Orchestrator Agent MCP")
    print("=" * 70)
    
    if not ORCHESTRATOR_IMPORTED:
        print("❌ No se puede ejecutar validación - import fallido")
        return
    
    all_results = ValidationResults()
    
    # Ejecutar todos los tests
    test_suites = [
        ("Inicialización Básica", test_basic_initialization),
        ("Gestión de Workflows", test_workflow_creation), 
        ("Agentes Especializados", test_specialized_agents),
        ("Requests MCP", test_mcp_requests),
        ("Características Avanzadas", test_advanced_features)
    ]
    
    for suite_name, test_func in test_suites:
        print(f"\n📋 Ejecutando: {suite_name}")
        print("-" * 50)
        
        try:
            suite_results = await test_func()
            all_results.tests_passed += suite_results.tests_passed
            all_results.tests_failed += suite_results.tests_failed
            all_results.tests_skipped += suite_results.tests_skipped
            all_results.results.extend(suite_results.results)
            
        except Exception as e:
            all_results.add_result(
                suite_name,
                False,
                f"Error ejecutando suite: {str(e)}",
                {"error": traceback.format_exc()}
            )
    
    # Mostrar resumen final
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE VALIDACIÓN")
    print("=" * 70)
    
    summary = all_results.get_summary()
    
    print(f"Total de tests: {summary['total_tests']}")
    print(f"✅ Pasaron: {summary['passed']}")
    print(f"❌ Fallaron: {summary['failed']}")  
    print(f"⏭️ Omitidos: {summary['skipped']}")
    print(f"📈 Tasa de éxito: {summary['success_rate']:.1f}%")
    
    if summary['failed'] > 0:
        print(f"\n❌ TESTS FALLIDOS:")
        for result in summary['results']:
            if 'FAIL' in result['status']:
                print(f"  - {result['test']}: {result['message']}")
    
    if summary['success_rate'] >= 80:
        print(f"\n🎉 Validación EXITOSA - Orquestrador funcionando correctamente")
    else:
        print(f"\n⚠️ Validación con PROBLEMAS - Revisar tests fallidos")
    
    # Guardar reporte detallado
    report_file = "multiagent_orchestrator_validation_report.json"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Reporte detallado guardado en: {report_file}")
    except Exception as e:
        print(f"\n⚠️ No se pudo guardar reporte: {e}")
    
    return summary['success_rate'] >= 80


if __name__ == "__main__":
    try:
        success = asyncio.run(run_validation())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Validación interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error fatal en validación: {e}")
        traceback.print_exc()
        sys.exit(1)