#!/usr/bin/env python3
"""
Setup y Configuración del Intelligent Router
Script para inicializar y configurar el sistema de AI-powered routing
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Añadir el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.intelligent_router import intelligent_router
from src.agents.base_agent_wrapper import (
    BaseAgentWrapper,
    AgentCapability,
    AgentStatus
)


class MockAgentWrapper(BaseAgentWrapper):
    """Mock agent wrapper para demostración"""
    
    def __init__(self, agent_name: str, capabilities=None):
        super().__init__(
            agent_name=agent_name,
            capabilities=capabilities or [AgentCapability.TOOL_INVOCATION],
            max_concurrent=3,
            timeout_seconds=30
        )
    
    async def process_request(self, request: dict, context: dict = None) -> dict:
        """Procesar request (simulado)"""
        import time
        time.sleep(0.1)  # Simular procesamiento
        return {
            "status": "success",
            "result": f"Procesado por {self.agent_name}",
            "request_id": request.get("id", "unknown")
        }


async def create_real_agents():
    """Crear y registrar agentes reales del sistema"""
    
    agents = []
    
    # Intentar importar agentes reales
    try:
        # Database Operations Agent
        from src.agents.database_operations_agent import DatabaseOperationsAgent
        db_agent = DatabaseOperationsAgent()
        await db_agent.ensure_initialized()
        agents.append(db_agent)
        print("✅ Database Operations Agent cargado")
    except ImportError:
        print("⚠️  Database Operations Agent no disponible")
    
    try:
        # File Processing Agent  
        from src.agents.file_processing_agent import FileProcessingAgent
        file_agent = FileProcessingAgent()
        await file_agent.ensure_initialized()
        agents.append(file_agent)
        print("✅ File Processing Agent cargado")
    except ImportError:
        print("⚠️  File Processing Agent no disponible")
    
    try:
        # Git Operations Agent
        from src.agents.git_operations_agent import GitOperationsAgent
        git_agent = GitOperationsAgent()
        await git_agent.ensure_initialized()
        agents.append(git_agent)
        print("✅ Git Operations Agent cargado")
    except ImportError:
        print("⚠️  Git Operations Agent no disponible")
    
    try:
        # Python Executor Agent
        from src.agents.python_executor_agent import PythonExecutorAgent
        py_agent = PythonExecutorAgent()
        await py_agent.ensure_initialized()
        agents.append(py_agent)
        print("✅ Python Executor Agent cargado")
    except ImportError:
        print("⚠️  Python Executor Agent no disponible")
    
    try:
        # Search Engine Agent
        from src.agents.search_engine_agent import SearchEngineAgent
        search_agent = SearchEngineAgent()
        await search_agent.ensure_initialized()
        agents.append(search_agent)
        print("✅ Search Engine Agent cargado")
    except ImportError:
        print("⚠️  Search Engine Agent no disponible")
    
    try:
        # Web Scraping Agent
        from src.agents.web_scraping_agent import WebScrapingAgent
        scraping_agent = WebScrapingAgent()
        await scraping_agent.ensure_initialized()
        agents.append(scraping_agent)
        print("✅ Web Scraping Agent cargado")
    except ImportError:
        print("⚠️  Web Scraping Agent no disponible")
    
    # Si no hay agentes reales, crear mock agents
    if not agents:
        print("🔄 Creando agentes mock para demostración...")
        agents = await create_mock_agents()
    
    return agents


async def create_mock_agents():
    """Crear agentes mock para demostración"""
    
    agents = [
        MockAgentWrapper(
            "reasoner_agent",
            [AgentCapability.INTENT_ANALYSIS, AgentCapability.STRATEGY_DEFINITION]
        ),
        MockAgentWrapper(
            "planner_agent", 
            [AgentCapability.TASK_DECOMPOSITION, AgentCapability.TOOL_SELECTION]
        ),
        MockAgentWrapper(
            "executor_agent",
            [AgentCapability.TOOL_INVOCATION, AgentCapability.CODE_EXECUTION]
        ),
        MockAgentWrapper(
            "verifier_agent",
            [AgentCapability.QUALITY_VALIDATION, AgentCapability.CONSISTENCY_CHECKING]
        ),
        MockAgentWrapper(
            "memory_manager",
            [AgentCapability.KNOWLEDGE_STORAGE, AgentCapability.SEMANTIC_SEARCH]
        )
    ]
    
    for agent in agents:
        await agent.ensure_initialized()
    
    return agents


async def setup_intelligent_router():
    """Configurar e inicializar el intelligent router"""
    
    print("🚀 Configurando Intelligent Router...")
    print("=" * 50)
    
    # 1. Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('intelligent_router.log')
        ]
    )
    
    # 2. Crear y registrar agentes
    print("\n📋 Registrando agentes...")
    agents = await create_real_agents()
    
    for agent in agents:
        try:
            intelligent_router.register_agent(agent)
            print(f"✅ {agent.agent_name} registrado exitosamente")
        except Exception as e:
            print(f"❌ Error registrando {agent.agent_name}: {e}")
    
    # 3. Verificar estado del router
    stats = intelligent_router.get_routing_statistics()
    print(f"\n📊 Estado del Router:")
    print(f"  Agentes registrados: {stats['registered_agents']}")
    print(f"  Agentes disponibles: {stats['available_agents']}")
    print(f"  Modelo ML entrenado: {stats['ml_model_trained']}")
    
    # 4. Habilitar adaptación automática
    intelligent_router.enable_adaptation(True)
    print("✅ Adaptación automática habilitada")
    
    # 5. Crear experimento A/B por defecto
    try:
        experiment_id = intelligent_router.create_ab_test(
            name="Router_Strategy_Test",
            strategy_a=RoutingStrategy.AI_OPTIMIZED,
            strategy_b=RoutingStrategy.SEMANTIC_MATCHING,
            traffic_split=0.6
        )
        print(f"✅ Experimento A/B creado: {experiment_id}")
    except Exception as e:
        print(f"⚠️  Error creando experimento A/B: {e}")
    
    # 6. Test básico de routing
    print("\n🧪 Ejecutando test básico de routing...")
    try:
        from src.core.intelligent_router import RoutingContext, RoutingStrategy
        
        test_context = RoutingContext(
            request_id="setup_test_001",
            user_id="setup_user",
            request_type="setup_test",
            complexity_score=0.3
        )
        
        test_request = {
            "task": "Test de configuración del router",
            "capability": "tool_invocation"
        }
        
        decision = await intelligent_router.make_routing_decision(
            request=test_request,
            context=test_context,
            strategy=RoutingStrategy.AI_OPTIMIZED
        )
        
        print(f"✅ Test exitoso: {decision.agent_name} seleccionado")
        print(f"   Confianza: {decision.confidence:.3f}")
        print(f"   Estrategia: {decision.strategy_used.value}")
        
    except Exception as e:
        print(f"❌ Error en test básico: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Intelligent Router configurado exitosamente!")
    print("\n📝 Próximos pasos:")
    print("1. Ejecutar demo completo: python examples/intelligent_router_demo.py")
    print("2. Ejecutar tests: python -m pytest tests/test_intelligent_router.py -v")
    print("3. Integrar en tu aplicación usando intelligent_router instance")
    
    return True


async def test_advanced_features():
    """Test de características avanzadas del router"""
    
    print("\n🔬 Testing características avanzadas...")
    print("-" * 40)
    
    # Test 1: Routing con restricciones
    print("\n1. Test routing con restricciones de presupuesto...")
    try:
        from src.core.intelligent_router import RoutingContext, OptimizationObjective
        
        context = RoutingContext(
            request_id="budget_test",
            user_id="budget_user",
            request_type="budget_test",
            budget_constraints={"max_cost": 0.02}
        )
        
        request = {"task": "Operación costosa", "capability": "code_execution"}
        
        decision = await intelligent_router.make_routing_decision(
            request, context, RoutingStrategy.AI_OPTIMIZED, OptimizationObjective.COST
        )
        
        print(f"✅ Routing con presupuesto: {decision.agent_name}")
        
    except Exception as e:
        print(f"❌ Error en test de presupuesto: {e}")
    
    # Test 2: Optimización multi-objetivo
    print("\n2. Test optimización multi-objetivo...")
    try:
        objectives = [OptimizationObjective.SPEED, OptimizationObjective.ACCURACY]
        
        for obj in objectives:
            decision = await intelligent_router.make_routing_decision(
                {"task": "Test multi-objetivo"},
                RoutingContext(
                    request_id=f"multi_{obj.value}",
                    user_id="multi_user",
                    request_type="multi_test"
                ),
                RoutingStrategy.AI_OPTIMIZED,
                obj
            )
            print(f"   {obj.value}: {decision.agent_name}")
        
        print("✅ Test multi-objetivo completado")
        
    except Exception as e:
        print(f"❌ Error en test multi-objetivo: {e}")
    
    # Test 3: Semantic routing
    print("\n3. Test routing semántico...")
    try:
        decision = await intelligent_router.make_routing_decision(
            {
                "query": "Analiza los sentimientos de este texto",
                "capability": "intent_analysis"
            },
            RoutingContext(
                request_id="semantic_test",
                user_id="semantic_user",
                request_type="semantic_test"
            ),
            RoutingStrategy.SEMANTIC_MATCHING
        )
        
        print(f"✅ Routing semántico: {decision.agent_name}")
        print(f"   Similitud: {decision.confidence:.3f}")
        
    except Exception as e:
        print(f"❌ Error en test semántico: {e}")
    
    print("\n✅ Todas las características avanzadas testeadas")


def create_integration_example():
    """Crear ejemplo de integración"""
    
    example_code = '''
"""
Ejemplo de Integración del Intelligent Router
Uso básico en una aplicación MCP
"""

import asyncio
from src.core.intelligent_router import intelligent_router, RoutingContext
from src.agents.database_operations_agent import DatabaseOperationsAgent

async def integrate_intelligent_router():
    """Ejemplo de integración en aplicación real"""
    
    # 1. Crear y registrar agente real
    db_agent = DatabaseOperationsAgent()
    await db_agent.ensure_initialized()
    intelligent_router.register_agent(db_agent)
    
    # 2. Realizar routing inteligente
    context = RoutingContext(
        request_id="app_request_001",
        user_id="app_user",
        request_type="database_query",
        complexity_score=0.5,
        user_preferences={"tier": "premium"}
    )
    
    decision = await intelligent_router.make_routing_decision(
        request={
            "query": "SELECT * FROM users WHERE active = 1",
            "capability": "database_query"
        },
        context=context,
        # El router selecciona automáticamente la mejor estrategia
    )
    
    # 3. Ejecutar request con agente seleccionado
    agent = intelligent_router.agent_registry[decision.agent_name]
    result = await agent.process_request(
        request={"query": "SELECT * FROM users WHERE active = 1"},
        context={"user": "app_user"}
    )
    
    # 4. Registrar resultado para aprendizaje
    performance = {
        "success_rate": 1.0 if result.get("status") == "success" else 0.0,
        "response_time": 1.2,  # Medir tiempo real
        "cost": 0.03
    }
    
    intelligent_router.record_routing_result(decision, performance, context)
    
    return result

# Ejecutar ejemplo
if __name__ == "__main__":
    result = asyncio.run(integrate_intelligent_router())
    print(f"Resultado: {result}")
'''
    
    with open("examples/intelligent_router_integration.py", "w") as f:
        f.write(example_code)
    
    print("📄 Ejemplo de integración creado: examples/intelligent_router_integration.py")


def main():
    """Función principal"""
    
    async def run_setup():
        success = await setup_intelligent_router()
        
        if success:
            await test_advanced_features()
            create_integration_example()
            
            print("\n" + "=" * 50)
            print("🎊 SETUP COMPLETADO EXITOSAMENTE")
            print("=" * 50)
            print("\n✨ El Intelligent Router está listo para usar!")
            print("\n📖 Documentación completa en: docs/INTELLIGENT_ROUTER.md")
            print("🧪 Ejecutar demo: python examples/intelligent_router_demo.py")
            print("🧪 Ejecutar tests: python -m pytest tests/test_intelligent_router.py -v")
            print("🔧 Ejemplo de integración: examples/intelligent_router_integration.py")
            
            return True
        else:
            print("❌ Error durante la configuración")
            return False
    
    return asyncio.run(run_setup())


if __name__ == "__main__":
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("src"):
        print("❌ Error: Ejecutar desde el directorio raíz del proyecto")
        sys.exit(1)
    
    # Ejecutar setup
    success = main()
    sys.exit(0 if success else 1)