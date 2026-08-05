"""
Demo del Intelligent Router
Ejemplo de uso del sistema de AI-powered routing
"""

import asyncio
import sys
import os

# Añadir el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.core.intelligent_router import (
    IntelligentRouter,
    RoutingContext,
    RoutingStrategy,
    OptimizationObjective,
    intelligent_router
)
from src.agents.base_agent_wrapper import (
    BaseAgentWrapper,
    AgentCapability,
    AgentStatus
)


class DemoAgentWrapper(BaseAgentWrapper):
    """Wrapper de demostración para agentes"""
    
    async def process_request(self, request: dict, context: dict = None) -> dict:
        """Procesar request (implementación demo)"""
        
        # Simular procesamiento
        await asyncio.sleep(0.1)  # Simular tiempo de procesamiento
        
        return {
            "status": "success",
            "result": f"Procesado por {self.agent_name}",
            "request_id": request.get("id", "unknown"),
            "processing_time": 0.1
        }


async def create_demo_agents():
    """Crear agentes de demostración"""
    
    # Crear diferentes tipos de agentes con diferentes capacidades
    agents = []
    
    # Reasoner Agent
    reasoner = DemoAgentWrapper(
        agent_name="reasoner_agent",
        capabilities=[
            AgentCapability.INTENT_ANALYSIS,
            AgentCapability.STRATEGY_DEFINITION,
            AgentCapability.CONTEXT_ENRICHMENT
        ],
        max_concurrent=3,
        timeout_seconds=30
    )
    
    # Planner Agent
    planner = DemoAgentWrapper(
        agent_name="planner_agent",
        capabilities=[
            AgentCapability.TASK_DECOMPOSITION,
            AgentCapability.TOOL_SELECTION,
            AgentCapability.DEPENDENCY_MANAGEMENT,
            AgentCapability.PLAN_OPTIMIZATION
        ],
        max_concurrent=2,
        timeout_seconds=45
    )
    
    # Executor Agent
    executor = DemoAgentWrapper(
        agent_name="executor_agent",
        capabilities=[
            AgentCapability.TOOL_INVOCATION,
            AgentCapability.CONCURRENT_EXECUTION,
            AgentCapability.RESULT_COLLECTION,
            AgentCapability.CODE_EXECUTION
        ],
        max_concurrent=5,
        timeout_seconds=60
    )
    
    # Verifier Agent
    verifier = DemoAgentWrapper(
        agent_name="verifier_agent",
        capabilities=[
            AgentCapability.QUALITY_VALIDATION,
            AgentCapability.CONSISTENCY_CHECKING,
            AgentCapability.TRAJECTORY_EVALUATION
        ],
        max_concurrent=4,
        timeout_seconds=20
    )
    
    # Memory Manager Agent
    memory = DemoAgentWrapper(
        agent_name="memory_manager",
        capabilities=[
            AgentCapability.KNOWLEDGE_STORAGE,
            AgentCapability.SEMANTIC_SEARCH,
            AgentCapability.CONTEXT_RETRIEVAL
        ],
        max_concurrent=10,
        timeout_seconds=15
    )
    
    agents = [reasoner, planner, executor, verifier, memory]
    
    # Inicializar agentes
    for agent in agents:
        await agent.ensure_initialized()
        intelligent_router.register_agent(agent)
    
    return agents


async def demo_basic_routing():
    """Demo de routing básico"""
    
    print("=== DEMO: Routing Básico ===")
    
    # Crear contexto de routing
    context = RoutingContext(
        request_id="demo_001",
        user_id="user_123",
        request_type="query_analysis",
        priority="normal",
        complexity_score=0.3
    )
    
    # Request simple
    request = {
        "query": "Analizar la intención de este mensaje del usuario",
        "capability": "intent_analysis"
    }
    
    # Tomar decisión de routing
    decision = await intelligent_router.make_routing_decision(
        request=request,
        context=context,
        strategy=RoutingStrategy.AI_OPTIMIZED,
        objective=OptimizationObjective.SPEED
    )
    
    print(f"Agente seleccionado: {decision.agent_name}")
    print(f"Estrategia usada: {decision.strategy_used.value}")
    print(f"Confianza: {decision.confidence:.3f}")
    print(f"Razonamiento: {decision.reasoning}")
    print(f"Performance esperada: {decision.expected_performance}")
    
    return decision


async def demo_semantic_routing():
    """Demo de routing semántico"""
    
    print("\n=== DEMO: Routing Semántico ===")
    
    context = RoutingContext(
        request_id="demo_002",
        user_id="user_456",
        request_type="complex_task",
        complexity_score=0.8
    )
    
    # Request complejo
    request = {
        "task": "Crear un plan detallado para automatizar el procesamiento de documentos",
        "description": "Necesito analizar, clasificar y extraer información de múltiples documentos PDF",
        "capability": "task_decomposition"
    }
    
    decision = await intelligent_router.make_routing_decision(
        request=request,
        context=context,
        strategy=RoutingStrategy.SEMANTIC_MATCHING
    )
    
    print(f"Agente seleccionado: {decision.agent_name}")
    print(f"Similitud semántica: {decision.confidence:.3f}")
    print(f"Alternativas: {decision.alternatives}")
    
    return decision


async def demo_cost_optimization():
    """Demo de optimización de costos"""
    
    print("\n=== DEMO: Optimización de Costos ===")
    
    # Contexto con restricciones de presupuesto
    context = RoutingContext(
        request_id="demo_003",
        user_id="user_789",
        request_type="data_processing",
        complexity_score=0.5,
        budget_constraints={"max_cost": 0.05}  # Presupuesto limitado
    )
    
    request = {
        "task": "Procesar datos de ventas del último trimestre",
        "capability": "tool_invocation"
    }
    
    # Optimizar para costo
    decision_cost = await intelligent_router.make_routing_decision(
        request=request,
        context=context,
        strategy=RoutingStrategy.AI_OPTIMIZED,
        objective=OptimizationObjective.COST
    )
    
    print(f"Optimización para COSTO:")
    print(f"  Agente: {decision_cost.agent_name}")
    print(f"  Costo esperado: {decision_cost.expected_performance.get('expected_cost', 'N/A')}")
    
    # Optimizar para velocidad
    decision_speed = await intelligent_router.make_routing_decision(
        request=request,
        context=context,
        strategy=RoutingStrategy.AI_OPTIMIZED,
        objective=OptimizationObjective.SPEED
    )
    
    print(f"Optimización para VELOCIDAD:")
    print(f"  Agente: {decision_speed.agent_name}")
    print(f"  Tiempo esperado: {decision_speed.expected_performance.get('expected_response_time', 'N/A')}")
    
    return decision_cost, decision_speed


async def demo_ab_testing():
    """Demo de A/B testing para estrategias"""
    
    print("\n=== DEMO: A/B Testing ===")
    
    # Crear experimento A/B
    experiment_id = intelligent_router.create_ab_test(
        name="AI_vs_Semantic_Routing",
        strategy_a=RoutingStrategy.AI_OPTIMIZED,
        strategy_b=RoutingStrategy.SEMANTIC_MATCHING,
        traffic_split=0.5,
        duration_days=3
    )
    
    print(f"Experimento creado: {experiment_id}")
    
    # Simular usuarios con diferentes estrategias
    context = RoutingContext(
        request_id="demo_004",
        user_id="test_user",
        request_type="general_task"
    )
    
    request = {
        "task": "Realizar análisis de texto",
        "capability": "intent_analysis"
    }
    
    # Usuario A (AI-optimized)
    decision_a = await intelligent_router.make_routing_decision(
        request=request,
        context=context,
        strategy=RoutingStrategy.AI_OPTIMIZED
    )
    
    # Usuario B (semantic)
    decision_b = await intelligent_router.make_routing_decision(
        request=request,
        context=context,
        strategy=RoutingStrategy.SEMANTIC_MATCHING
    )
    
    print(f"Usuario A -> Agente: {decision_a.agent_name} (AI)")
    print(f"Usuario B -> Agente: {decision_b.agent_name} (Semantic)")
    
    # Registrar resultados
    performance_a = {
        "success_rate": 0.95,
        "response_time": 1.2,
        "cost": 0.03
    }
    
    performance_b = {
        "success_rate": 0.88,
        "response_time": 1.8,
        "cost": 0.04
    }
    
    intelligent_router.record_routing_result(decision_a, performance_a, context)
    intelligent_router.record_routing_result(decision_b, performance_b, context)
    
    return experiment_id


async def demo_adaptation():
    """Demo de adaptación automática"""
    
    print("\n=== DEMO: Adaptación Automática ===")
    
    # Simular múltiples requests para adaptación
    for i in range(10):
        context = RoutingContext(
            request_id=f"adapt_demo_{i}",
            user_id="adaptive_user",
            request_type="learning_task",
            complexity_score=0.4 + (i * 0.05)  # Incrementar complejidad
        )
        
        request = {
            "task": f"Tarea de aprendizaje número {i}",
            "capability": "knowledge_storage"
        }
        
        decision = await intelligent_router.make_routing_decision(
            request=request,
            context=context,
            strategy=RoutingStrategy.AI_OPTIMIZED
        )
        
        # Simular performance variable
        performance = {
            "success_rate": 0.8 + (0.1 * (i % 3)),  # Success rate variable
            "response_time": 1.0 + (i * 0.1),
            "cost": 0.02 + (i * 0.001)
        }
        
        intelligent_router.record_routing_result(decision, performance, context)
        
        print(f"Request {i+1}: {decision.agent_name} -> Success: {performance['success_rate']:.2f}")
    
    # Adaptar parámetros
    await intelligent_router.adapt_routing_parameters()
    
    print("Parámetros de routing adaptados automáticamente")
    
    # Mostrar estadísticas
    stats = intelligent_router.get_routing_statistics()
    print(f"Estadísticas finales: {json.dumps(stats, indent=2, default=str)}")


async def demo_multi_objective():
    """Demo de optimización multi-objetivo"""
    
    print("\n=== DEMO: Multi-Objetivo ===")
    
    # Contexto complejo
    context = RoutingContext(
        request_id="multi_demo",
        user_id="enterprise_user",
        request_type="enterprise_analysis",
        complexity_score=0.9,
        priority="high",
        budget_constraints={"max_cost": 0.10},
        time_constraints={"max_seconds": 5.0}
    )
    
    request = {
        "task": "Análisis empresarial completo con múltiples fuentes de datos",
        "description": "Análisis de rendimiento, predicciones de mercado, y recomendaciones estratégicas",
        "capability": "strategy_definition"
    }
    
    # Probar diferentes objetivos
    objectives = [
        OptimizationObjective.BALANCED,
        OptimizationObjective.SPEED,
        OptimizationObjective.ACCURACY,
        OptimizationObjective.COST,
        OptimizationObjective.RELIABILITY
    ]
    
    results = {}
    
    for objective in objectives:
        decision = await intelligent_router.make_routing_decision(
            request=request,
            context=context,
            strategy=RoutingStrategy.AI_OPTIMIZED,
            objective=objective
        )
        
        results[objective.value] = {
            "agent": decision.agent_name,
            "confidence": decision.confidence,
            "performance": decision.expected_performance
        }
        
        print(f"\nObjetivo {objective.value}:")
        print(f"  Agente: {decision.agent_name}")
        print(f"  Confianza: {decision.confidence:.3f}")
        print(f"  Tiempo: {decision.expected_performance.get('expected_response_time', 'N/A'):.2f}s")
        print(f"  Costo: {decision.expected_performance.get('expected_cost', 'N/A'):.3f}")
    
    return results


async def run_complete_demo():
    """Ejecutar demo completo del intelligent router"""
    
    print("🚀 Iniciando Demo Completo del Intelligent Router")
    print("=" * 60)
    
    # Crear agentes
    print("\n📋 Creando agentes de demostración...")
    agents = await create_demo_agents()
    print(f"✅ {len(agents)} agentes creados y registrados")
    
    # Ejecutar demos
    try:
        await demo_basic_routing()
        await demo_semantic_routing()
        await demo_cost_optimization()
        await demo_ab_testing()
        await demo_adaptation()
        await demo_multi_objective()
        
        print("\n" + "=" * 60)
        print("✅ Demo completado exitosamente")
        
        # Estadísticas finales
        stats = intelligent_router.get_routing_statistics()
        print(f"\n📊 Estadísticas del Router:")
        print(f"  Total de decisiones: {stats['total_routing_decisions']}")
        print(f"  Agentes registrados: {stats['registered_agents']}")
        print(f"  Agentes disponibles: {stats['available_agents']}")
        print(f"  Modelo ML entrenado: {stats['ml_model_trained']}")
        print(f"  Experimentos A/B activos: {stats['ab_experiments_active']}")
        
        print(f"\n📈 Uso de estrategias:")
        for strategy, count in stats['strategy_usage'].items():
            print(f"  {strategy}: {count} veces")
        
        print(f"\n🎯 Uso de agentes:")
        for agent, count in stats['agent_usage'].items():
            print(f"  {agent}: {count} veces")
        
    except Exception as e:
        print(f"\n❌ Error en el demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Configurar logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ejecutar demo
    asyncio.run(run_complete_demo())