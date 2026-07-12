"""
Ejemplo de uso del Multi-Agent Orchestrator Agent MCP Avanzado
Demuestra capacidades de workflow management, load balancing, y orchestración empresarial
"""

import asyncio
import json
import sys
import os

# Añadir el path del src para importaciones
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.multiagent_orchestrator_agent import (
    MultiAgentOrchestratorAgentWrapper,
    WorkflowStep,
    AgentCapability,
    TaskPriority
)
from agents import BaseAgentWrapper, AgentCapability as BaseCapability


async def create_example_specialized_agent():
    """Crear un agente especializado de ejemplo"""
    
    class DataAnalysisAgentWrapper(BaseAgentWrapper):
        """Agente especializado para análisis de datos"""
        
        def __init__(self):
            capabilities = [
                BaseCapability.TOOL_INVOCATION,
                BaseCapability.CODE_EXECUTION
            ]
            
            super().__init__(
                agent_name="data_analysis_specialist",
                capabilities=capabilities,
                max_concurrent=2,
                timeout_seconds=120
            )
        
        async def _initialize(self):
            """Inicializar agente especializado"""
            await asyncio.sleep(0.1)  # Simular inicialización
            self.logger.info("DataAnalysisAgent especializado inicializado")
        
        async def process_request(self, request, context=None):
            """Procesar request de análisis de datos"""
            await asyncio.sleep(0.5)  # Simular procesamiento
            
            return {
                "analysis_type": request.get("analysis_type", "basic"),
                "data_points": request.get("data_points", []),
                "results": {
                    "mean": sum(request.get("data_points", [1, 2, 3, 4, 5])) / 5,
                    "max": max(request.get("data_points", [1, 2, 3, 4, 5])),
                    "min": min(request.get("data_points", [1, 2, 3, 4, 5])),
                    "summary": "Análisis estadístico completado"
                }
            }
    
    return DataAnalysisAgentWrapper()


async def create_web_search_agent():
    """Crear agente de búsqueda web especializado"""
    
    class WebSearchAgentWrapper(BaseAgentWrapper):
        """Agente especializado para búsqueda web"""
        
        def __init__(self):
            capabilities = [
                BaseCapability.TOOL_INVOCATION,
                BaseCapability.WEB_SCRAPING
            ]
            
            super().__init__(
                agent_name="web_search_specialist", 
                capabilities=capabilities,
                max_concurrent=3,
                timeout_seconds=30
            )
        
        async def _initialize(self):
            """Inicializar agente de búsqueda web"""
            await asyncio.sleep(0.1)
            self.logger.info("WebSearchAgent especializado inicializado")
        
        async def process_request(self, request, context=None):
            """Procesar request de búsqueda web"""
            query = request.get("query", "")
            await asyncio.sleep(0.3)  # Simular búsqueda
            
            # Simular resultados de búsqueda
            simulated_results = [
                {"title": f"Resultado 1 para {query}", "url": "https://example1.com", "snippet": f"Información relevante sobre {query}"},
                {"title": f"Resultado 2 para {query}", "url": "https://example2.com", "snippet": f"Más datos sobre {query}"},
                {"title": f"Resultado 3 para {query}", "url": "https://example3.com", "snippet": f"Detalles adicionales de {query}"}
            ]
            
            return {
                "query": query,
                "results_count": len(simulated_results),
                "results": simulated_results
            }
    
    return WebSearchAgentWrapper()


async def demo_basic_orchestration():
    """Demostración de orquestación básica"""
    print("=== DEMO: Orquestación Básica ===")
    
    # Crear orquestrador
    orchestrator = MultiAgentOrchestratorAgentWrapper()
    
    # Crear workflow simple con agentes base
    steps = [
        WorkflowStep(
            step_id="analyze_requirement",
            agent_type="reasoner",
            capability=AgentCapability.INTENT_ANALYSIS,
            task={"objective": "Analizar requisito de usuario"},
            priority=TaskPriority.HIGH
        ),
        WorkflowStep(
            step_id="create_plan", 
            agent_type="planner",
            capability=AgentCapability.TASK_DECOMPOSITION,
            task={"complexity": "medium", "estimated_duration": 10.0},
            dependencies=["analyze_requirement"],
            priority=TaskPriority.NORMAL
        ),
        WorkflowStep(
            step_id="execute_tasks",
            agent_type="executor", 
            capability=AgentCapability.TOOL_INVOCATION,
            task={"tools": ["python_executor", "file_processor"]},
            dependencies=["create_plan"],
            priority=TaskPriority.NORMAL
        ),
        WorkflowStep(
            step_id="verify_results",
            agent_type="verifier",
            capability=AgentCapability.QUALITY_VALIDATION, 
            task={"quality_threshold": 0.8},
            dependencies=["execute_tasks"],
            priority=TaskPriority.HIGH
        )
    ]
    
    # Crear y ejecutar workflow
    workflow_id = await orchestrator.create_workflow(
        objective="Ejemplo de procesamiento con agentes base",
        workflow_steps=steps,
        priority=TaskPriority.NORMAL
    )
    
    print(f"Workflow creado: {workflow_id}")
    
    # Esperar a que complete y mostrar estado
    await asyncio.sleep(2)  # Dar tiempo para ejecución
    
    status = await orchestrator.get_workflow_status(workflow_id)
    print(f"Estado del workflow: {json.dumps(status, indent=2)}")
    
    await orchestrator.cleanup()


async def demo_parallel_workflow():
    """Demostración de workflow con ejecución paralela"""
    print("\n=== DEMO: Workflow con Ejecución Paralela ===")
    
    orchestrator = MultiAgentOrchestratorAgentWrapper()
    
    # Registrar agentes especializados
    data_agent = await create_example_specialized_agent()
    search_agent = await create_web_search_agent()
    
    await orchestrator.register_specialized_agent("data_analysis_specialist", data_agent)
    await orchestrator.register_specialized_agent("web_search_specialist", search_agent)
    
    print("Agentes especializados registrados")
    
    # Crear workflow con pasos paralelos
    steps = [
        WorkflowStep(
            step_id="search_data",
            agent_type="web_search_specialist",
            capability=BaseCapability.WEB_SCRAPING,
            task={"query": "análisis de datos machine learning"},
            parallel_group="data_collection",
            priority=TaskPriority.HIGH
        ),
        WorkflowStep(
            step_id="analyze_sample_data",
            agent_type="data_analysis_specialist", 
            capability=BaseCapability.CODE_EXECUTION,
            task={
                "analysis_type": "statistical",
                "data_points": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            },
            parallel_group="data_collection",
            priority=TaskPriority.HIGH
        ),
        WorkflowStep(
            step_id="verify_parallel_results",
            agent_type="verifier",
            capability=AgentCapability.QUALITY_VALIDATION,
            task={"check_parallel_consistency": True},
            dependencies=["search_data", "analyze_sample_data"], 
            priority=TaskPriority.NORMAL
        )
    ]
    
    # Crear workflow paralelo
    workflow_id = await orchestrator.create_workflow(
        objective="Ejemplo de procesamiento paralelo con agentes especializados",
        workflow_steps=steps,
        priority=TaskPriority.HIGH
    )
    
    print(f"Workflow paralelo creado: {workflow_id}")
    
    # Monitorear progreso
    for i in range(10):
        await asyncio.sleep(0.5)
        status = await orchestrator.get_workflow_status(workflow_id)
        if status and status.get("state") == "completed":
            print("¡Workflow paralelo completado!")
            break
        print(f"Progreso: {status.get('progress', 0):.2%} - Paso {status.get('current_step_index', 0) + 1}/{status.get('total_steps', 0)}")
    
    # Mostrar estado final
    final_status = await orchestrator.get_workflow_status(workflow_id)
    print(f"Estado final: {json.dumps(final_status, indent=2)}")
    
    await orchestrator.cleanup()


async def demo_load_balancing_and_scaling():
    """Demostración de load balancing y escalado"""
    print("\n=== DEMO: Load Balancing y Escalado ===")
    
    orchestrator = MultiAgentOrchestratorAgentWrapper()
    
    # Crear múltiples workflows para demostrar load balancing
    workflows = []
    
    # Crear 5 workflows simultáneos
    for i in range(5):
        steps = [
            WorkflowStep(
                step_id=f"reason_step_{i}",
                agent_type="reasoner",
                capability=AgentCapability.INTENT_ANALYSIS,
                task={"objective": f"Análisis de requerimiento {i}"}
            ),
            WorkflowStep(
                step_id=f"plan_step_{i}",
                agent_type="planner", 
                capability=AgentCapability.TASK_DECOMPOSITION,
                task={"complexity": "medium"},
                dependencies=[f"reason_step_{i}"]
            )
        ]
        
        workflow_id = await orchestrator.create_workflow(
            objective=f"Workflow de prueba {i}",
            workflow_steps=steps,
            priority=TaskPriority.NORMAL
        )
        workflows.append(workflow_id)
    
    print(f"Creados {len(workflows)} workflows para prueba de carga")
    
    # Monitorear estado durante ejecución
    for round_num in range(10):
        await asyncio.sleep(0.5)
        
        orchestrator_status = await orchestrator.get_orchestrator_status()
        active_workflows = orchestrator_status.get("active_workflows", 0)
        queued_tasks = orchestrator_status.get("queued_tasks", 0)
        
        print(f"Ronda {round_num + 1}: {active_workflows} activos, {queued_tasks} en cola")
        
        if active_workflows == 0 and queued_tasks == 0:
            print("Todos los workflows completados")
            break
    
    # Mostrar métricas finales
    final_status = await orchestrator.get_orchestrator_status()
    metrics = final_status.get("workflow_metrics", {})
    
    print("\nMétricas del orquestrador:")
    print(f"- Total workflows: {metrics.get('total_workflows', 0)}")
    print(f"- Exitosos: {metrics.get('successful_workflows', 0)}")
    print(f"- Fallidos: {metrics.get('failed_workflows', 0)}")
    print(f"- Tiempo promedio: {metrics.get('average_completion_time', 0):.2f}s")
    
    await orchestrator.cleanup()


async def demo_health_monitoring():
    """Demostración de health monitoring"""
    print("\n=== DEMO: Health Monitoring ===")
    
    orchestrator = MultiAgentOrchestratorAgentWrapper()
    
    # Obtener health check
    health = await orchestrator.health_check()
    print("Health check inicial:")
    print(json.dumps(health, indent=2))
    
    # Registrar agentes especializados
    data_agent = await create_example_specialized_agent()
    await orchestrator.register_specialized_agent("data_analysis_specialist", data_agent)
    
    # Obtener status detallado
    status = await orchestrator.get_orchestrator_status()
    
    print(f"\nAgentes registrados:")
    agents_info = status.get("registered_agents", {})
    print(f"- Agentes base: {agents_info.get('base', 0)}")
    print(f"- Agentes especializados: {agents_info.get('specialized', 0)}")
    
    print(f"\nCircuit breakers:")
    circuits = status.get("circuit_breakers", {})
    for agent_name, circuit_state in circuits.items():
        print(f"- {agent_name}: {circuit_state}")
    
    print(f"\nHealth status de agentes:")
    health_status = status.get("health_status", {})
    for agent_name, agent_health in health_status.items():
        print(f"- {agent_name}: {agent_health.get('status', 'unknown')}")
    
    await orchestrator.cleanup()


async def demo_mcp_requests():
    """Demostración de requests MCP"""
    print("\n=== DEMO: Requests MCP ===")
    
    orchestrator = MultiAgentOrchestratorAgentWrapper()
    
    # 1. Request: Listar agentes
    print("1. Listando agentes...")
    list_request = {"type": "list_agents"}
    response = await orchestrator.process_request(list_request)
    print(f"Response: {json.dumps(response, indent=2)}")
    
    # 2. Request: Estado del orquestrador
    print("\n2. Obteniendo estado del orquestrador...")
    status_request = {"type": "get_status"}
    response = await orchestrator.process_request(status_request)
    print(f"Estado: {response.get('status', {}).get('registered_agents', {})}")
    
    # 3. Request: Crear workflow via MCP
    print("\n3. Creando workflow via MCP...")
    create_request = {
        "type": "create_workflow",
        "objective": "Ejemplo MCP de workflow",
        "steps": [
            {
                "step_id": "step1",
                "agent_type": "reasoner",
                "capability": "intent_analysis",
                "task": {"objective": "Análisis MCP"}
            }
        ],
        "priority": 2
    }
    response = await orchestrator.process_request(create_request)
    workflow_id = response.get("workflow_id")
    print(f"Workflow ID: {workflow_id}")
    
    # 4. Request: Obtener estado del workflow
    if workflow_id:
        print(f"\n4. Obteniendo estado del workflow {workflow_id}...")
        status_request = {
            "type": "get_workflow_status",
            "workflow_id": workflow_id
        }
        response = await orchestrator.process_request(status_request)
        print(f"Estado del workflow: {json.dumps(response.get('status', {}), indent=2)}")
    
    await orchestrator.cleanup()


async def main():
    """Función principal - ejecutar todas las demostraciones"""
    print("🚀 Multi-Agent Orchestrator Agent MCP - Demostración Completa")
    print("=" * 60)
    
    try:
        # Demostraciones principales
        await demo_basic_orchestration()
        await demo_parallel_workflow() 
        await demo_load_balancing_and_scaling()
        await demo_health_monitoring()
        await demo_mcp_requests()
        
        print("\n✅ Todas las demostraciones completadas exitosamente")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error en demostración: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())