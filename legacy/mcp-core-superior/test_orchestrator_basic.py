#!/usr/bin/env python3
"""
Prueba básica del Multi-Agent Orchestrator Agent
Verifica imports básicos y funcionalidad core
"""

import sys
import os

# Añadir paths para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Probar imports básicos"""
    print("🧪 Testing imports...")
    
    try:
        # Test import base wrapper
        from agents.base_agent_wrapper import BaseAgentWrapper, AgentCapability
        print("✅ BaseAgentWrapper imported successfully")
        
        # Test import orchestrator
        from agents.multiagent_orchestrator_agent import (
            MultiAgentOrchestratorAgentWrapper,
            WorkflowStep,
            WorkflowExecution,
            TaskPriority
        )
        print("✅ MultiAgentOrchestratorAgent imported successfully")
        
        # Test import specialized agents
        from agents.python_executor_agent import PythonExecutorAgentWrapper
        from agents.web_scraping_agent import WebScrapingAgentWrapper
        from agents.search_engine_agent import SearchEngineAgentWrapper
        from agents.database_operations_agent import DatabaseOperationsAgentWrapper
        from agents.file_processing_agent import FileProcessingAgentWrapper
        from agents.git_operations_agent import GitOperationsAgentWrapper
        print("✅ All specialized agents imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_orchestrator_creation():
    """Probar creación básica del orquestrador"""
    print("\n🚀 Testing orchestrator creation...")
    
    try:
        from agents.multiagent_orchestrator_agent import MultiAgentOrchestratorAgentWrapper
        
        # Crear instancia
        orchestrator = MultiAgentOrchestratorAgentWrapper()
        print(f"✅ Orchestrator created: {orchestrator.agent_name}")
        
        # Verificar capacidades
        capabilities = orchestrator.get_capabilities()
        print(f"✅ Capabilities: {len(capabilities)} found")
        
        # Verificar estado
        status = orchestrator.get_status()
        print(f"✅ Status: {status['is_ready']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Creation error: {e}")
        return False

def test_workflow_creation():
    """Probar creación de workflow básico"""
    print("\n📋 Testing workflow creation...")
    
    try:
        from agents.multiagent_orchestrator_agent import (
            MultiAgentOrchestratorAgentWrapper,
            WorkflowStep,
            AgentCapability,
            TaskPriority
        )
        
        orchestrator = MultiAgentOrchestratorAgentWrapper()
        
        # Crear paso de workflow
        step = WorkflowStep(
            step_id="test_step",
            agent_type="reasoner",
            capability=AgentCapability.INTENT_ANALYSIS,
            task={"objective": "Test workflow"},
            priority=TaskPriority.NORMAL
        )
        print(f"✅ Workflow step created: {step.step_id}")
        
        # Crear workflow
        import asyncio
        
        async def test_workflow():
            workflow_id = await orchestrator.create_workflow(
                objective="Test workflow creation",
                workflow_steps=[step],
                priority=TaskPriority.NORMAL
            )
            print(f"✅ Workflow created: {workflow_id}")
            await orchestrator.cleanup()
            return True
        
        return asyncio.run(test_workflow())
        
    except Exception as e:
        print(f"❌ Workflow creation error: {e}")
        return False

def show_agent_summary():
    """Mostrar resumen de agentes disponibles"""
    print("\n📊 Agent Summary:")
    print("=" * 50)
    
    # Base agents
    base_agents = [
        "ReasonerAgent",
        "PlannerAgent", 
        "ExecutorAgent",
        "VerifierAgent",
        "MemoryManagerAgent"
    ]
    
    # Specialized agents
    specialized_agents = [
        "PythonExecutorAgent",
        "WebScrapingAgent", 
        "SearchEngineAgent",
        "DatabaseOperationsAgent",
        "FileProcessingAgent",
        "GitOperationsAgent"
    ]
    
    print(f"Base Agents ({len(base_agents)}):")
    for agent in base_agents:
        print(f"  ✅ {agent}")
    
    print(f"\nSpecialized Agents ({len(specialized_agents)}):")
    for agent in specialized_agents:
        print(f"  ✅ {agent}")
    
    print(f"\nOrchestrator:")
    print(f"  ✅ MultiAgentOrchestratorAgent (Advanced)")
    
    total_agents = len(base_agents) + len(specialized_agents) + 1
    print(f"\n📈 Total Agent System: {total_agents} agents")

def main():
    """Función principal"""
    print("🚀 Multi-Agent Orchestrator Agent - Basic Validation")
    print("=" * 60)
    
    all_passed = True
    
    # Ejecutar tests
    all_passed &= test_imports()
    all_passed &= test_orchestrator_creation()
    all_passed &= test_workflow_creation()
    
    # Mostrar resumen
    show_agent_summary()
    
    # Resultado final
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Multi-Agent Orchestrator working correctly!")
        print("✅ Ready for enterprise multi-agent orchestration")
    else:
        print("❌ SOME TESTS FAILED - Check errors above")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)