#!/usr/bin/env python3
"""
Script de prueba para verificar que todos los wrappers de agentes funcionan correctamente
"""

import asyncio
import sys
import os
from pathlib import Path

# Agregar el directorio de src al path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

async def test_imports():
    """Probar que todos los imports funcionan correctamente"""
    print("🔍 Probando imports de wrappers de agentes...")
    
    try:
        # Test import del sistema base
        from agents.base_agent_wrapper import BaseAgentWrapper, AgentCapability, AgentStatus
        print("✅ BaseAgentWrapper importado correctamente")
        
        # Test import de configuración
        from agents.config import agent_config_manager, validate_agent_setup
        print("✅ Configuración importada correctamente")
        
        # Test import de wrappers principales
        from agents.reasoner_wrapper import ReasonerAgentWrapper
        from agents.planner_wrapper import PlannerAgentWrapper
        from agents.executor_wrapper import ExecutorAgentWrapper
        from agents.verifier_wrapper import VerifierAgentWrapper
        from agents.memory_manager_wrapper import MemoryManagerAgentWrapper
        print("✅ Wrappers principales importados correctamente")
        
        # Test import de wrappers especializados
        try:
            from agents.python_executor_agent import AdvancedPythonExecutorAgent
            print("✅ PythonExecutorAgent importado correctamente")
        except ImportError:
            print("⚠️  PythonExecutorAgent no disponible (dependencias faltantes)")
        
        try:
            from agents.web_scraping_agent import WebScrapingAgentWrapper
            print("✅ WebScrapingAgent importado correctamente")
        except ImportError:
            print("⚠️  WebScrapingAgent no disponible (dependencias faltantes)")
        
        try:
            from agents.git_operations_agent import GitOperationsAgentWrapper
            print("✅ GitOperationsAgent importado correctamente")
        except ImportError:
            print("⚠️  GitOperationsAgent no disponible (dependencias faltantes)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en imports: {e}")
        return False

async def test_agent_instantiation():
    """Probar que los agentes se pueden instanciar correctamente"""
    print("\n🔧 Probando instanciación de agentes...")
    
    try:
        # Test ReasonerAgent
        reasoner = ReasonerAgentWrapper()
        await reasoner.ensure_initialized()
        health = await reasoner.health_check()
        print(f"✅ ReasonerAgent: {health['status']}")
        
        # Test ExecutorAgent
        executor = ExecutorAgentWrapper()
        await executor.ensure_initialized()
        health = await executor.health_check()
        print(f"✅ ExecutorAgent: {health['status']}")
        
        # Test MemoryManagerAgent
        memory_agent = MemoryManagerAgentWrapper()
        await memory_agent.ensure_initialized()
        health = await memory_agent.health_check()
        print(f"✅ MemoryManagerAgent: {health['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en instanciación: {e}")
        return False

async def test_agent_functionality():
    """Probar funcionalidad básica de los agentes"""
    print("\n🚀 Probando funcionalidad de agentes...")
    
    try:
        # Test ReasonerAgent
        reasoner = ReasonerAgentWrapper()
        result = await reasoner.analyze_intent(
            objective="Crear un análisis de datos de ventas"
        )
        print(f"✅ ReasonerAgent - Análisis completado: {result['analysis']['intent_type']}")
        
        # Test ExecutorAgent
        executor = ExecutorAgentWrapper()
        result = await executor.execute_tool(
            tool_name="python_executor",
            code="print('Hola desde executor')"
        )
        print(f"✅ ExecutorAgent - Tool ejecutado: {result.get('success', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en funcionalidad: {e}")
        return False

async def test_factory_functions():
    """Probar funciones factory del sistema"""
    print("\n🏭 Probando funciones factory...")
    
    try:
        # Test create_agent_wrapper
        from agents import create_agent_wrapper, AgentType
        
        reasoner = create_agent_wrapper(AgentType.REASONER)
        await reasoner.ensure_initialized()
        print("✅ Factory create_agent_wrapper funciona")
        
        # Test get_available_agent_types
        from agents import get_available_agent_types
        agent_types = get_available_agent_types()
        print(f"✅ Tipos de agentes disponibles: {len(agent_types)}")
        
        # Test get_all_agents_health_status
        from agents import get_all_agents_health_status
        health = get_all_agents_health_status()
        print(f"✅ Estado de agentes: {health['summary']['healthy_agents']}/{health['summary']['total_agents']} saludables")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en factory functions: {e}")
        return False

async def test_configuration():
    """Probar sistema de configuración"""
    print("\n⚙️ Probando sistema de configuración...")
    
    try:
        from agents.config import agent_config_manager, AgentType
        
        # Test obtener configuración
        reasoner_config = agent_config_manager.get_config(AgentType.REASONER)
        print(f"✅ Configuración Reasoner: timeout={reasoner_config.timeout_seconds}s")
        
        # Test validación de dependencias
        dep_check = agent_config_manager.validate_dependencies(AgentType.REASONER)
        print(f"✅ Validación dependencias: {dep_check['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en configuración: {e}")
        return False

async def main():
    """Función principal de prueba"""
    print("🧪 INICIANDO PRUEBAS DE WRAPPERS DE AGENTES MCP")
    print("="*60)
    
    tests = [
        ("Imports", test_imports),
        ("Configuración", test_configuration),
        ("Instanciación", test_agent_instantiation),
        ("Funcionalidad", test_agent_functionality),
        ("Factory Functions", test_factory_functions)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔸 Ejecutando test: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   Resultado: {status}")
        except Exception as e:
            results.append((test_name, False))
            print(f"   ❌ ERROR: {e}")
    
    # Resumen final
    print("\n" + "="*60)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Total: {passed}/{total} tests pasaron ({passed/total:.1%})")
    
    if passed == total:
        print("🎉 ¡TODOS LOS TESTS PASARON! Los wrappers están funcionando correctamente.")
    elif passed > 0:
        print(f"⚠️  {passed} tests pasaron, pero hay problemas que resolver.")
    else:
        print("❌ Todos los tests fallaron. Hay problemas críticos.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
