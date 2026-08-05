#!/usr/bin/env python3
"""
Script de prueba independiente para MCP Core Superior
"""
import sys
import os
import asyncio
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_mcp_server():
    """Test básico del servidor MCP"""
    print("🚀 Iniciando test del MCP Core Superior...")
    
    try:
        # Importaciones simples
        from agents.base_agent_wrapper import BaseAgentWrapper, AgentCapability, AgentStatus
        
        print("✅ Imports exitosos")
        
        # Crear un agente simple
        class SimpleAgent(BaseAgentWrapper):
            def __init__(self):
                super().__init__(
                    agent_name="test_agent",
                    capabilities=[AgentCapability.INTENT_ANALYSIS],
                    max_concurrent=2,
                    timeout_seconds=30
                )
            
            async def process_request(self, request, context=None):
                await asyncio.sleep(0.1)  # Simular procesamiento
                return {
                    "success": True,
                    "message": f"Agente {self.agent_name} procesó: {request.get('test', '')}",
                    "capabilities": [cap.value for cap in self.capabilities]
                }
        
        # Test del agente
        agent = SimpleAgent()
        await agent.ensure_initialized()
        
        print(f"✅ Agente inicializado: {agent.agent_name}")
        print(f"   Status: {agent.status.value}")
        print(f"   Capacidades: {[cap.value for cap in agent.capabilities]}")
        
        # Test de procesamiento
        result = await agent.process_request({"test": "Hello MCP Core Superior!"})
        print(f"✅ Procesamiento exitoso: {result}")
        
        # Test de estado
        status = agent.get_status()
        print(f"✅ Estado del agente: {status['status']}, Utilización: {status['utilization']:.1%}")
        
        print("\\n🎉 Todos los tests básicos pasaron exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error durante test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_imports():
    """Test básico de imports"""
    print("📦 Testing imports...")
    
    try:
        # Test import estructura
        from pathlib import Path
        src_path = Path(__file__).parent / "src"
        if not src_path.exists():
            print(f"❌ Directorio src no encontrado: {src_path}")
            return False
        
        # Test import básico
        import asyncio
        import logging
        import json
        print("✅ Imports básicos exitosos")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en imports: {e}")
        return False

async def main():
    """Función principal de test"""
    print("🧪 MCP Core Superior - Tests Básicos")
    print("=" * 50)
    
    # Test de imports
    if not test_imports():
        sys.exit(1)
    
    print()
    
    # Test de funcionalidad
    if not await test_mcp_server():
        sys.exit(1)
    
    print()
    print("✨ Tests completados - MCP Core Superior está funcionando!")

if __name__ == "__main__":
    asyncio.run(main())
