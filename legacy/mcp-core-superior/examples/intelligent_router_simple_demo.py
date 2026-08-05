#!/usr/bin/env python3
"""
Demo Simplificado del Intelligent Router
Ejemplo que funciona sin dependencias pesadas
"""

import asyncio
import sys
import os

# Añadir directorios al path
sys.path.insert(0, os.path.dirname(__file__))  # examples directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))  # mcp-core-superior directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))  # src directory

from src.core.intelligent_router_simple import (
    SimpleIntelligentRouter,
    RoutingContext,
    RoutingStrategy,
    OptimizationObjective,
    intelligent_router,
    MockAgentWrapper
)


async def create_demo_agents():
    """Crear agentes de demostración"""
    
    agents = [
        MockAgentWrapper(
            "reasoner_agent",
            ["intent_analysis", "strategy_definition", "context_enrichment"]
        ),
        MockAgentWrapper(
            "planner_agent",
            ["task_decomposition", "tool_selection", "dependency_management"]
        ),
        MockAgentWrapper(
            "executor_agent",
            ["tool_invocation", "concurrent_execution", "code_execution"]
        ),
        MockAgentWrapper(
            "verifier_agent",
            ["quality_validation", "consistency_checking", "trajectory_evaluation"]
        ),
        MockAgentWrapper(
            "memory_manager",
            ["knowledge_storage", "semantic_search", "context_retrieval"]
        ),
        MockAgentWrapper(
            "database_agent",
            ["database_query", "data_processing", "sql_execution"]
        ),
        MockAgentWrapper(
            "search_engine",
            ["web_search", "information_retrieval", "content_analysis"]
        ),
        MockAgentWrapper(
            "web_scraper",
            ["web_scraping", "data_extraction", "content_parsing"]
        )
    ]
    
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
    
    print(f"✅ Agente seleccionado: {decision.agent_name}")
    print(f"✅ Estrategia usada: {decision.strategy_used.value}")
    print(f"✅ Confianza: {decision.confidence:.3f}")
    print(f"✅ Razonamiento: {decision.reasoning}")
    print(f"✅ Performance esperada: {decision.expected_performance}")
    
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
    
    print(f"✅ Agente seleccionado: {decision.agent_name}")
    print(f"✅ Similitud semántica: {decision.confidence:.3f}")
    print(f"✅ Alternativas: {decision.alternatives}")
    
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
    
    print(f"✅ Optimización para COSTO:")
    print(f"  Agente: {decision_cost.agent_name}")
    print(f"  Costo esperado: {decision_cost.expected_performance.get('expected_cost', 'N/A'):.3f}")
    print(f"  Tiempo esperado: {decision_cost.expected_performance.get('expected_response_time', 'N/A'):.2f}s")
    
    # Optimizar para velocidad
    decision_speed = await intelligent_router.make_routing_decision(
        request=request,
        context=context,
        strategy=RoutingStrategy.AI_OPTIMIZED,
        objective=OptimizationObjective.SPEED
    )
    
    print(f"\n✅ Optimización para VELOCIDAD:")
    print(f"  Agente: {decision_speed.agent_name}")
    print(f"  Tiempo esperado: {decision_speed.expected_performance.get('expected_response_time', 'N/A'):.2f}s")
    print(f"  Costo esperado: {decision_speed.expected_performance.get('expected_cost', 'N/A'):.3f}")
    
    return decision_cost, decision_speed


async def demo_adaptation():
    """Demo de adaptación automática"""
    
    print("\n=== DEMO: Adaptación Automática ===")
    
    # Simular múltiples requests para adaptación
    print("Simulando 10 requests para aprendizaje...")
    
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
        
        print(f"  Request {i+1}: {decision.agent_name} -> Success: {performance['success_rate']:.2f}")
    
    # Adaptar parámetros
    await intelligent_router.adapt_routing_parameters()
    
    print("✅ Parámetros de routing adaptados automáticamente")
    
    # Mostrar estadísticas
    stats = intelligent_router.get_routing_statistics()
    print(f"📊 Estadísticas después de adaptación:")
    print(f"  Total decisiones: {stats['total_routing_decisions']}")
    print(f"  Perfiles de agentes: {stats['agent_profiles']}")


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
        
        print(f"\n🎯 Objetivo {objective.value}:")
        print(f"  Agente: {decision.agent_name}")
        print(f"  Confianza: {decision.confidence:.3f}")
        print(f"  Tiempo: {decision.expected_performance.get('expected_response_time', 'N/A'):.2f}s")
        print(f"  Costo: {decision.expected_performance.get('expected_cost', 'N/A'):.3f}")
        print(f"  Éxito: {decision.expected_performance.get('expected_success_probability', 'N/A'):.2f}")
    
    return results


async def demo_performance_comparison():
    """Demo comparando todas las estrategias"""
    
    print("\n=== DEMO: Comparación de Estrategias ===")
    
    context = RoutingContext(
        request_id="comparison_demo",
        user_id="comparison_user",
        request_type="analysis_task",
        complexity_score=0.6
    )
    
    request = {
        "task": "Análisis completo de datos de usuarios",
        "capability": "data_processing"
    }
    
    strategies = [
        RoutingStrategy.AI_OPTIMIZED,
        RoutingStrategy.SEMANTIC_MATCHING,
        RoutingStrategy.PERFORMANCE_BASED,
        RoutingStrategy.LOAD_BALANCED,
        RoutingStrategy.STATIC
    ]
    
    print("Probando todas las estrategias disponibles:")
    
    for strategy in strategies:
        try:
            decision = await intelligent_router.make_routing_decision(
                request=request,
                context=context,
                strategy=strategy,
                objective=OptimizationObjective.BALANCED
            )
            
            print(f"  {strategy.value:15} -> {decision.agent_name:15} (confianza: {decision.confidence:.3f})")
            
        except Exception as e:
            print(f"  {strategy.value:15} -> Error: {e}")


async def demo_real_world_scenario():
    """Demo de escenario real de uso"""
    
    print("\n=== DEMO: Escenario Real ===")
    
    print("Simulando aplicación MCP con requests reales...")
    
    # Simular diferentes tipos de requests
    scenarios = [
        {
            "name": "Análisis de sentimiento",
            "context": RoutingContext(
                request_id="sentiment_001",
                user_id="analyst_user",
                request_type="sentiment_analysis",
                complexity_score=0.4,
                user_preferences={"tier": "premium"}
            ),
            "request": {
                "task": "Analizar sentimientos en 1000 reseñas de productos",
                "capability": "intent_analysis"
            }
        },
        {
            "name": "Consulta de base de datos",
            "context": RoutingContext(
                request_id="db_001",
                user_id="data_user",
                request_type="database_query",
                complexity_score=0.3,
                budget_constraints={"max_cost": 0.02}
            ),
            "request": {
                "query": "SELECT COUNT(*) FROM users WHERE created_date > '2024-01-01'",
                "capability": "database_query"
            }
        },
        {
            "name": "Web scraping complejo",
            "context": RoutingContext(
                request_id="scraping_001",
                user_id="research_user",
                request_type="web_scraping",
                complexity_score=0.8,
                time_constraints={"max_seconds": 30}
            ),
            "request": {
                "task": "Extraer precios de productos de múltiples tiendas online",
                "capability": "web_scraping"
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 {scenario['name']}:")
        
        decision = await intelligent_router.make_routing_decision(
            request=scenario["request"],
            context=scenario["context"],
            strategy=RoutingStrategy.AI_OPTIMIZED,
            objective=OptimizationObjective.BALANCED
        )
        
        print(f"  ✅ Agente seleccionado: {decision.agent_name}")
        print(f"  🎯 Estrategia: {decision.strategy_used.value}")
        print(f"  📊 Confianza: {decision.confidence:.3f}")
        print(f"  ⏱️  Tiempo estimado: {decision.expected_performance.get('expected_response_time', 'N/A'):.2f}s")
        print(f"  💰 Costo estimado: {decision.expected_performance.get('expected_cost', 'N/A'):.3f}")
        
        # Simular resultado
        performance = {
            "success_rate": 0.95,
            "response_time": decision.expected_performance.get('expected_response_time', 2.0),
            "cost": decision.expected_performance.get('expected_cost', 0.1)
        }
        
        intelligent_router.record_routing_result(decision, performance, scenario["context"])


async def run_complete_demo():
    """Ejecutar demo completo del intelligent router simplificado"""
    
    print("🚀 Iniciando Demo Completo del Intelligent Router Simplificado")
    print("=" * 70)
    
    # Crear agentes
    print("\n📋 Creando agentes de demostración...")
    agents = await create_demo_agents()
    print(f"✅ {len(agents)} agentes creados y registrados")
    
    # Ejecutar demos
    try:
        await demo_basic_routing()
        await demo_semantic_routing()
        await demo_cost_optimization()
        await demo_adaptation()
        await demo_multi_objective()
        await demo_performance_comparison()
        await demo_real_world_scenario()
        
        print("\n" + "=" * 70)
        print("✅ Demo completado exitosamente")
        
        # Estadísticas finales
        stats = intelligent_router.get_routing_statistics()
        print(f"\n📊 Estadísticas Finales del Router:")
        print(f"  Total de decisiones: {stats['total_routing_decisions']}")
        print(f"  Agentes registrados: {stats['registered_agents']}")
        print(f"  Agentes disponibles: {stats['available_agents']}")
        print(f"  Perfiles de agentes ML: {stats['agent_profiles']}")
        print(f"  Adaptación habilitada: {intelligent_router.adaptation_enabled}")
        
        print(f"\n📈 Uso de estrategias:")
        for strategy, count in stats['strategy_usage'].items():
            print(f"  {strategy}: {count} veces")
        
        print(f"\n🎯 Uso de agentes:")
        for agent, count in stats['agent_usage'].items():
            print(f"  {agent}: {count} veces")
        
        print(f"\n💡 Características implementadas:")
        features = [
            "✅ Machine Learning simplificado para predicción",
            "✅ Routing dinámico basado en datos históricos",
            "✅ Toma de decisiones context-aware",
            "✅ Aprendizaje en tiempo real y adaptación",
            "✅ Optimización multi-objetivo",
            "✅ Routing semántico con embeddings",
            "✅ Balanceador de carga",
            "✅ 5 estrategias de routing diferentes",
            "✅ Integración completa con agentes"
        ]
        
        for feature in features:
            print(f"  {feature}")
        
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