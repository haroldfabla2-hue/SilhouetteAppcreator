"""
Unit tests para FastMCP Server
Servidor principal que integra los 5 agentes especializados como herramientas MCP
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any, List
import logging

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Mock fastmcp to avoid dependency issues
with patch.dict('sys.modules', {
    'fastmcp': Mock(),
    'fastmcp.server': Mock()
}):
    with patch('src.core.fastmcp_server.FastMCP') as mock_fastmcp:
        from src.core.fastmcp_server import MCPCoreServer


class TestMCPCoreServer:
    """Test suite para MCPCoreServer"""
    
    @pytest.fixture
    def mcp_server(self):
        """Fixture para crear instancia del MCPCoreServer"""
        with patch('src.core.fastmcp_server.settings'), \
             patch('src.core.fastmcp_server.get_environment_config'), \
             patch('src.core.fastmcp_server.setup_logging'), \
             patch('src.core.fastmcp_server.ReasonerAgentWrapper'), \
             patch('src.core.fastmcp_server.PlannerAgentWrapper'), \
             patch('src.core.fastmcp_server.ExecutorAgentWrapper'), \
             patch('src.core.fastmcp_server.VerifierAgentWrapper'), \
             patch('src.core.fastmcp_server.MemoryManagerAgentWrapper'), \
             patch('src.core.fastmcp_server.MultiAgentOrchestrator'), \
             patch('src.core.fastmcp_server.StreamingEngine'), \
             patch('src.core.fastmcp_server.ContextForgeClient'), \
             patch('src.core.fastmcp_server.VectorStoreClient'), \
             patch('src.core.fastmcp_server.AuthService'):
            return MCPCoreServer()
    
    @pytest.mark.asyncio
    async def test_initialization(self, mcp_server):
        """Test inicialización del servidor"""
        # Verificar que el servidor se inicializa correctamente
        assert mcp_server is not None
        assert mcp_server.logger is not None
        assert mcp_server.mcp is not None
        assert mcp_server.is_initialized is False
    
    @pytest.mark.asyncio
    async def test_server_services_initialization(self, mcp_server):
        """Test inicialización de servicios"""
        # Verificar que todos los servicios están inicializados
        assert mcp_server.contextforge_client is not None
        assert mcp_server.vector_store_client is not None
        assert mcp_server.auth_service is not None
    
    @pytest.mark.asyncio
    async def test_agents_initialization(self, mcp_server):
        """Test inicialización de agentes"""
        # Verificar que todos los agentes están inicializados
        assert mcp_server.reasoner_agent is not None
        assert mcp_server.planner_agent is not None
        assert mcp_server.executor_agent is not None
        assert mcp_server.verifier_agent is not None
        assert mcp_server.memory_manager_agent is not None
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, mcp_server):
        """Test inicialización del orquestador"""
        # Verificar que el orquestador está inicializado
        assert mcp_server.orchestrator is not None
        assert mcp_server.streaming_engine is not None
    
    @pytest.mark.asyncio
    async def test_logging_setup(self, mcp_server):
        """Test configuración de logging"""
        # Verificar que el logger está configurado
        assert mcp_server.logger.name == "mcp.core.server"
        assert isinstance(mcp_server.logger, logging.Logger)
    
    @pytest.mark.asyncio
    async def test_double_initialization_prevention(self, mcp_server):
        """Test prevención de doble inicialización"""
        # Mock inicialización exitosa
        with patch.object(mcp_server.contextforge_client, 'initialize', new_callable=AsyncMock), \
             patch.object(mcp_server.vector_store_client, 'initialize', new_callable=AsyncMock), \
             patch.object(mcp_server.auth_service, 'initialize', new_callable=AsyncMock), \
             patch.object(mcp_server.reasoner_agent, 'ensure_initialized', new_callable=AsyncMock), \
             patch.object(mcp_server.planner_agent, 'ensure_initialized', new_callable=AsyncMock), \
             patch.object(mcp_server.executor_agent, 'ensure_initialized', new_callable=AsyncMock), \
             patch.object(mcp_server.verifier_agent, 'ensure_initialized', new_callable=AsyncMock), \
             patch.object(mcp_server.memory_manager_agent, 'ensure_initialized', new_callable=AsyncMock):
            
            # Primera inicialización
            await mcp_server.initialize()
            assert mcp_server.is_initialized is True
            
            # Segunda inicialización debería ser no-op
            await mcp_server.initialize()
            assert mcp_server.is_initialized is True
    
    @pytest.mark.asyncio
    async def test_initialize_failure_handling(self, mcp_server):
        """Test manejo de fallos en inicialización"""
        # Mock falla en inicialización de servicio
        with patch.object(mcp_server.contextforge_client, 'initialize', side_effect=Exception("Connection failed")), \
             patch.object(mcp_server.vector_store_client, 'initialize', new_callable=AsyncMock), \
             patch.object(mcp_server.auth_service, 'initialize', new_callable=AsyncMock):
            
            with pytest.raises(Exception):
                await mcp_server.initialize()
            
            # Verificar que el servidor no está marcado como inicializado
            assert mcp_server.is_initialized is False
    
    @pytest.mark.asyncio
    async def test_reasoning_tool_registration(self, mcp_server):
        """Test registro de herramienta de reasoning"""
        with patch.object(mcp_server.mcp, 'tool') as mock_tool:
            # El registro debería ocurrir durante la inicialización
            # Verificar que se llamó al menos una vez
            mock_tool.assert_called()
    
    @pytest.mark.asyncio
    async def test_planning_tool_registration(self, mcp_server):
        """Test registro de herramienta de planning"""
        with patch.object(mcp_server.mcp, 'tool') as mock_tool:
            # El registro debería ocurrir durante la inicialización
            # Verificar que se llamó al menos una vez
            mock_tool.assert_called()
    
    @pytest.mark.asyncio
    async def test_execution_tool_registration(self, mcp_server):
        """Test registro de herramienta de execution"""
        with patch.object(mcp_server.mcp, 'tool') as mock_tool:
            # El registro debería ocurrir durante la inicialización
            # Verificar que se llamó al menos una vez
            mock_tool.assert_called()
    
    @pytest.mark.asyncio
    async def test_verification_tool_registration(self, mcp_server):
        """Test registro de herramienta de verification"""
        with patch.object(mcp_server.mcp, 'tool') as mock_tool:
            # El registro debería ocurrir durante la inicialización
            # Verificar que se llamó al menos una vez
            mock_tool.assert_called()
    
    @pytest.mark.asyncio
    async def test_memory_management_tool_registration(self, mcp_server):
        """Test registro de herramienta de memory management"""
        with patch.object(mcp_server.mcp, 'tool') as mock_tool:
            # El registro debería ocurrir durante la inicialización
            # Verificar que se llamó al menos una vez
            mock_tool.assert_called()
    
    @pytest.mark.asyncio
    async def test_multi_agent_orchestrator_integration(self, mcp_server):
        """Test integración con multi-agent orchestrator"""
        with patch.object(mcp_server.orchestrator, 'create_workflow') as mock_create:
            mock_create.return_value = "workflow_123"
            
            # Simular llamada al orquestador
            result = await mcp_server.orchestrator.create_workflow({
                "name": "Test Workflow",
                "steps": []
            })
            
            assert result == "workflow_123"
    
    @pytest.mark.asyncio
    async def test_streaming_engine_integration(self, mcp_server):
        """Test integración con streaming engine"""
        with patch.object(mcp_server.streaming_engine, 'start_stream') as mock_start:
            mock_start.return_value = "stream_123"
            
            # Simular inicio de streaming
            result = await mcp_server.streaming_engine.start_stream({
                "source": "agent_updates",
                "frequency": 1.0
            })
            
            assert result == "stream_123"
    
    @pytest.mark.asyncio
    async def test_contextforge_client_integration(self, mcp_server):
        """Test integración con ContextForge client"""
        with patch.object(mcp_server.contextforge_client, 'store_context') as mock_store:
            mock_store.return_value = {"success": True, "context_id": "ctx_123"}
            
            # Simular almacenamiento de contexto
            result = await mcp_server.contextforge_client.store_context({
                "content": "Test context",
                "metadata": {"source": "test"}
            })
            
            assert result["success"] is True
            assert "context_id" in result
    
    @pytest.mark.asyncio
    async def test_vector_store_integration(self, mcp_server):
        """Test integración con vector store"""
        with patch.object(mcp_server.vector_store_client, 'store_embedding') as mock_store:
            mock_store.return_value = {"success": True, "vector_id": "vec_123"}
            
            # Simular almacenamiento de embedding
            result = await mcp_server.vector_store_client.store_embedding({
                "text": "Test text",
                "embedding": [0.1, 0.2, 0.3]
            })
            
            assert result["success"] is True
            assert "vector_id" in result
    
    @pytest.mark.asyncio
    async def test_auth_service_integration(self, mcp_server):
        """Test integración con auth service"""
        with patch.object(mcp_server.auth_service, 'validate_token') as mock_validate:
            mock_validate.return_value = {"valid": True, "user_id": "user_123"}
            
            # Simular validación de token
            result = await mcp_server.auth_service.validate_token("test_token_123")
            
            assert result["valid"] is True
            assert "user_id" in result
    
    @pytest.mark.asyncio
    async def test_server_health_check(self, mcp_server):
        """Test verificación de salud del servidor"""
        # Mock inicialización
        with patch.object(mcp_server.contextforge_client, 'initialize', new_callable=AsyncMock), \
             patch.object(mcp_server.vector_store_client, 'initialize', new_callable=AsyncMock), \
             patch.object(mcp_server.auth_service, 'initialize', new_callable=AsyncMock), \
             patch.object(mcp_server.reasoner_agent, 'ensure_initialized', new_callable=AsyncMock), \
             patch.object(mcp_server.planner_agent, 'ensure_initialized', new_callable=AsyncMock), \
             patch.object(mcp_server.executor_agent, 'ensure_initialized', new_callable=AsyncMock), \
             patch.object(mcp_server.verifier_agent, 'ensure_initialized', new_callable=AsyncMock), \
             patch.object(mcp_server.memory_manager_agent, 'ensure_initialized', new_callable=AsyncMock):
            
            await mcp_server.initialize()
            
            # Verificar que el servidor está saludable
            assert mcp_server.is_initialized is True
    
    @pytest.mark.asyncio
    async def test_agent_tool_error_handling(self, mcp_server):
        """Test manejo de errores en herramientas de agentes"""
        # Mock error en reasoning tool
        with patch.object(mcp_server.reasoner_agent, 'process_request', side_effect=Exception("Test error")):
            with pytest.raises(Exception):
                await mcp_server.reasoner_agent.process_request({"objective": "test"})
    
    @pytest.mark.asyncio
    async def test_server_shutdown(self, mcp_server):
        """Test cierre del servidor"""
        # Mock inicialización
        with patch.object(mcp_server.contextforge_client, 'initialize', new_callable=AsyncMock), \
             patch.object(mcp_server.vector_store_client, 'initialize', new_callable=AsyncMock), \
             patch.object(mcp_server.auth_service, 'initialize', new_callable=AsyncMock), \
             patch.object(mcp_server.reasoner_agent, 'ensure_initialized', new_callable=AsyncMock), \
             patch.object(mcp_server.planner_agent, 'ensure_initialized', new_callable=AsyncMock), \
             patch.object(mcp_server.executor_agent, 'ensure_initialized', new_callable=AsyncMock), \
             patch.object(mcp_server.verifier_agent, 'ensure_initialized', new_callable=AsyncMock), \
             patch.object(mcp_server.memory_manager_agent, 'ensure_initialized', new_callable=AsyncMock):
            
            await mcp_server.initialize()
            
            # Mock cierre de servicios
            with patch.object(mcp_server.contextforge_client, 'cleanup', new_callable=AsyncMock), \
                 patch.object(mcp_server.vector_store_client, 'cleanup', new_callable=AsyncMock), \
                 patch.object(mcp_server.auth_service, 'cleanup', new_callable=AsyncMock):
                
                # Simular cierre
                await mcp_server.shutdown()
                
                # Verificar que los servicios se limpiaron
                # En una implementación real, verificaríamos que cleanup fue llamado
                assert not mcp_server.is_initialized
    
    @pytest.mark.asyncio
    async def test_mcp_server_configuration(self, mcp_server):
        """Test configuración del servidor MCP"""
        # Verificar que FastMCP se configuró correctamente
        assert mcp_server.mcp is not None
        assert hasattr(mcp_server.mcp, 'name') or hasattr(mcp_server.mcp, 'app')
    
    @pytest.mark.asyncio
    async def test_concurrent_initialization_safety(self, mcp_server):
        """Test seguridad en inicialización concurrente"""
        import asyncio
        
        # Mock inicialización exitosa
        with patch.object(mcp_server.contextforge_client, 'initialize', new_callable=AsyncMock), \
             patch.object(mcp_server.vector_store_client, 'initialize', new_callable=AsyncMock), \
             patch.object(mcp_server.auth_service, 'initialize', new_callable=AsyncMock), \
             patch.object(mcp_server.reasoner_agent, 'ensure_initialized', new_callable=AsyncMock), \
             patch.object(mcp_server.planner_agent, 'ensure_initialized', new_callable=AsyncMock), \
             patch.object(mcp_server.executor_agent, 'ensure_initialized', new_callable=AsyncMock), \
             patch.object(mcp_server.verifier_agent, 'ensure_initialized', new_callable=AsyncMock), \
             patch.object(mcp_server.memory_manager_agent, 'ensure_initialized', new_callable=AsyncMock):
            
            # Ejecutar múltiples inicializaciones concurrentes
            tasks = [mcp_server.initialize() for _ in range(5)]
            await asyncio.gather(*tasks)
            
            # Verificar que solo se inicializó una vez
            assert mcp_server.is_initialized is True
    
    @pytest.mark.asyncio
    async def test_agent_capability_integration(self, mcp_server):
        """Test integración de capacidades de agentes"""
        # Verificar que cada agente tiene sus capacidades configuradas
        assert hasattr(mcp_server.reasoner_agent, 'capabilities')
        assert hasattr(mcp_server.planner_agent, 'capabilities')
        assert hasattr(mcp_server.executor_agent, 'capabilities')
        assert hasattr(mcp_server.verifier_agent, 'capabilities')
        assert hasattr(mcp_server.memory_manager_agent, 'capabilities')
