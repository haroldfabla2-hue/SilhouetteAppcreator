"""
Unit tests para MemoryManagerAgent
Gestiona memoria semántica y contexto
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.agents.memory_manager_wrapper import MemoryManagerAgentWrapper
from src.agents.base_agent_wrapper import AgentCapability
from src.core.exceptions import AgentException


class TestMemoryManagerAgentWrapper:
    """Test suite para MemoryManagerAgentWrapper"""
    
    @pytest.fixture
    def memory_agent(self):
        """Fixture para crear instancia del MemoryManagerAgent"""
        return MemoryManagerAgentWrapper()
    
    @pytest.fixture
    def sample_content(self):
        """Fixture para contenido de ejemplo"""
        return "Este es un contenido importante sobre machine learning y análisis de datos que debe ser memorizado"
    
    @pytest.fixture
    def sample_query(self):
        """Fixture para query de ejemplo"""
        return "machine learning"
    
    @pytest.mark.asyncio
    async def test_initialization(self, memory_agent):
        """Test inicialización del MemoryManagerAgent"""
        assert memory_agent.agent_name == "memory_manager"
        assert AgentCapability.KNOWLEDGE_STORAGE in memory_agent.capabilities
        assert AgentCapability.SEMANTIC_SEARCH in memory_agent.capabilities
        assert AgentCapability.CONTEXT_RETRIEVAL in memory_agent.capabilities
        assert AgentCapability.CONVERSATION_MANAGEMENT in memory_agent.capabilities
        
        # Test que el logger está configurado
        assert memory_agent.logger.name == "mcp.agents.memory_manager"
        
        # Verificar que existe el cache de memoria
        assert hasattr(memory_agent, 'memory_cache')
        assert isinstance(memory_agent.memory_cache, dict)
    
    @pytest.mark.asyncio
    async def test_store_operation_success(self, memory_agent, sample_content):
        """Test operación store exitosa"""
        request = {
            "operation": "store",
            "content": sample_content,
            "conversation_id": "conv_123",
            "user_id": "user_456"
        }
        
        result = await memory_agent.process_request(request)
        
        # Verificar estructura del resultado
        assert "success" in result
        assert "operation" in result
        assert "memory_id" in result
        assert "message" in result
        
        assert result["success"] is True
        assert result["operation"] == "store"
        assert result["memory_id"].startswith("mem_")
        assert "almacenada exitosamente" in result["message"]
        
        # Verificar que el contenido se almacenó en el cache
        memory_id = result["memory_id"]
        assert memory_id in memory_agent.memory_cache
        
        stored_content = memory_agent.memory_cache[memory_id]
        assert stored_content["content"] == sample_content
        assert stored_content["user_id"] == "user_456"
        assert stored_content["conversation_id"] == "conv_123"
        assert "timestamp" in stored_content
    
    @pytest.mark.asyncio
    async def test_store_operation_missing_content(self, memory_agent):
        """Test operación store sin contenido"""
        request = {
            "operation": "store",
            "content": None,  # Sin contenido
            "conversation_id": "conv_123"
        }
        
        with pytest.raises(AgentException) as exc_info:
            await memory_agent.process_request(request)
        
        assert "Content es requerido" in str(exc_info.value.message)
    
    @pytest.mark.asyncio
    async def test_store_operation_empty_content(self, memory_agent):
        """Test operación store con contenido vacío"""
        request = {
            "operation": "store",
            "content": "",  # Contenido vacío
            "conversation_id": "conv_123"
        }
        
        with pytest.raises(AgentException) as exc_info:
            await memory_agent.process_request(request)
        
        assert "Content es requerido" in str(exc_info.value.message)
    
    @pytest.mark.asyncio
    async def test_search_operation_success(self, memory_agent, sample_content, sample_query):
        """Test operación search exitosa"""
        # Primero almacenar contenido
        store_request = {
            "operation": "store",
            "content": sample_content,
            "conversation_id": "conv_123",
            "user_id": "user_456"
        }
        await memory_agent.process_request(store_request)
        
        # Luego buscar
        search_request = {
            "operation": "search",
            "query": sample_query,
            "conversation_id": "conv_123"
        }
        
        result = await memory_agent.process_request(search_request)
        
        # Verificar estructura del resultado
        assert "success" in result
        assert "operation" in result
        assert "query" in result
        assert "total_results" in result
        assert "results" in result
        
        assert result["success"] is True
        assert result["operation"] == "search"
        assert result["query"] == sample_query
        assert isinstance(result["total_results"], int)
        assert isinstance(result["results"], list)
        
        # Verificar estructura de resultados
        for search_result in result["results"]:
            assert "memory_id" in search_result
            assert "content" in search_result
            assert "similarity_score" in search_result
            assert "timestamp" in search_result
            assert isinstance(search_result["similarity_score"], float)
    
    @pytest.mark.asyncio
    async def test_search_operation_missing_query(self, memory_agent):
        """Test operación search sin query"""
        request = {
            "operation": "search",
            "query": None,  # Sin query
            "conversation_id": "conv_123"
        }
        
        with pytest.raises(AgentException) as exc_info:
            await memory_agent.process_request(request)
        
        assert "Query es requerido" in str(exc_info.value.message)
    
    @pytest.mark.asyncio
    async def test_search_operation_empty_query(self, memory_agent):
        """Test operación search con query vacío"""
        request = {
            "operation": "search",
            "query": "",  # Query vacío
            "conversation_id": "conv_123"
        }
        
        with pytest.raises(AgentException) as exc_info:
            await memory_agent.process_request(request)
        
        assert "Query es requerido" in str(exc_info.value.message)
    
    @pytest.mark.asyncio
    async def test_search_no_results(self, memory_agent):
        """Test búsqueda sin resultados"""
        search_request = {
            "operation": "search",
            "query": "contenido inexistente",
            "conversation_id": "conv_123"
        }
        
        result = await memory_agent.process_request(search_request)
        
        assert result["success"] is True
        assert result["operation"] == "search"
        assert result["total_results"] == 0
        assert len(result["results"]) == 0
    
    @pytest.mark.asyncio
    async def test_search_with_results(self, memory_agent):
        """Test búsqueda con múltiples resultados"""
        # Almacenar varios contenidos
        contents = [
            "Python es un lenguaje de programación",
            "Machine learning con Python",
            "Análisis de datos en Python",
            "Desarrollo web con JavaScript",
            "Inteligencia artificial moderna"
        ]
        
        for i, content in enumerate(contents):
            store_request = {
                "operation": "store",
                "content": content,
                "conversation_id": f"conv_{i}",
                "user_id": "user_456"
            }
            await memory_agent.process_request(store_request)
        
        # Buscar contenido relacionado con Python
        search_request = {
            "operation": "search",
            "query": "Python",
            "conversation_id": "conv_search"
        }
        
        result = await memory_agent.process_request(search_request)
        
        assert result["success"] is True
        assert result["total_results"] > 0
        assert len(result["results"]) > 0
        
        # Los primeros resultados deberían tener mayor similitud
        results = result["results"]
        for i in range(len(results) - 1):
            assert results[i]["similarity_score"] >= results[i + 1]["similarity_score"]
    
    @pytest.mark.asyncio
    async def test_get_context_operation(self, memory_agent):
        """Test operación get_context"""
        # Almacenar algunos contenidos
        for i in range(3):
            store_request = {
                "operation": "store",
                "content": f"Contexto de conversación {i}",
                "conversation_id": "conv_test",
                "user_id": "user_456"
            }
            await memory_agent.process_request(store_request)
        
        context_request = {
            "operation": "get_context",
            "conversation_id": "conv_test",
            "limit": 5
        }
        
        result = await memory_agent.process_request(context_request)
        
        assert result["success"] is True
        assert result["operation"] == "get_context"
        assert "context_items" in result
        assert "total_items" in result
        
        assert isinstance(result["context_items"], list)
        assert isinstance(result["total_items"], int)
        
        for item in result["context_items"]:
            assert "content" in item
            assert "timestamp" in item
            assert "memory_id" in item
    
    @pytest.mark.asyncio
    async def test_clear_conversation_operation(self, memory_agent):
        """Test operación clear_conversation"""
        # Almacenar contenidos para una conversación específica
        for i in range(3):
            store_request = {
                "operation": "store",
                "content": f"Contenido conv1 {i}",
                "conversation_id": "conv1",
                "user_id": "user_456"
            }
            await memory_agent.process_request(store_request)
        
        # Almacenar contenido para otra conversación
        store_request = {
            "operation": "store",
            "content": "Contenido conv2",
            "conversation_id": "conv2",
            "user_id": "user_456"
        }
        await memory_agent.process_request(store_request)
        
        # Verificar que hay contenido
        initial_cache_size = len(memory_agent.memory_cache)
        assert initial_cache_size > 0
        
        # Limpiar conversación conv1
        clear_request = {
            "operation": "clear_conversation",
            "conversation_id": "conv1"
        }
        
        result = await memory_agent.process_request(clear_request)
        
        assert result["success"] is True
        assert result["operation"] == "clear_conversation"
        assert "cleared_items" in result
        
        # Verificar que el contenido de conv1 fue eliminado
        remaining_memory = memory_agent.memory_cache
        for memory_data in remaining_memory.values():
            assert memory_data["conversation_id"] != "conv1"
    
    @pytest.mark.asyncio
    async def test_invalid_operation(self, memory_agent):
        """Test operación inválida"""
        request = {
            "operation": "invalid_operation",
            "content": "test content"
        }
        
        result = await memory_agent.process_request(request)
        
        # Debería manejar la operación inválida
        assert "success" in result
        assert "error" in result
    
    def test_has_required_capabilities(self, memory_agent):
        """Test que el memory manager tiene las capacidades necesarias"""
        required_capabilities = [
            AgentCapability.KNOWLEDGE_STORAGE,
            AgentCapability.SEMANTIC_SEARCH,
            AgentCapability.CONTEXT_RETRIEVAL,
            AgentCapability.CONVERSATION_MANAGEMENT
        ]
        
        for capability in required_capabilities:
            assert capability in memory_agent.capabilities
    
    @pytest.mark.asyncio
    async def test_memory_persistence_during_session(self, memory_agent):
        """Test persistencia de memoria durante la sesión"""
        # Almacenar contenido
        content1 = "Primera memoria"
        store_request1 = {
            "operation": "store",
            "content": content1,
            "conversation_id": "conv_test",
            "user_id": "user_456"
        }
        result1 = await memory_agent.process_request(store_request1)
        memory_id1 = result1["memory_id"]
        
        # Almacenar más contenido
        content2 = "Segunda memoria"
        store_request2 = {
            "operation": "store",
            "content": content2,
            "conversation_id": "conv_test",
            "user_id": "user_456"
        }
        result2 = await memory_agent.process_request(store_request2)
        memory_id2 = result2["memory_id"]
        
        # Verificar que ambas memorias están en el cache
        assert memory_id1 in memory_agent.memory_cache
        assert memory_id2 in memory_agent.memory_cache
        assert memory_agent.memory_cache[memory_id1]["content"] == content1
        assert memory_agent.memory_cache[memory_id2]["content"] == content2
    
    @pytest.mark.asyncio
    async def test_search_similarity_scoring(self, memory_agent):
        """Test scoring de similitud en búsqueda"""
        # Almacenar contenido con palabras clave específicas
        contents = [
            "Python machine learning es muy útil",
            "JavaScript desarrollo web frontend",
            "Python análisis datos pandas",
            "Machine learning algoritmos"
        ]
        
        for content in contents:
            store_request = {
                "operation": "store",
                "content": content,
                "conversation_id": "conv_test",
                "user_id": "user_456"
            }
            await memory_agent.process_request(store_request)
        
        # Buscar "Python"
        search_request = {
            "operation": "search",
            "query": "Python",
            "conversation_id": "conv_test"
        }
        
        result = await memory_agent.process_request(search_request)
        
        # Verificar que los resultados están ordenados por similitud
        results = result["results"]
        for i in range(len(results) - 1):
            assert results[i]["similarity_score"] >= results[i + 1]["similarity_score"]
        
        # Verificar que los contenidos con "Python" tienen mayor score
        python_results = [r for r in results if "Python" in r["content"]]
        non_python_results = [r for r in results if "Python" not in r["content"]]
        
        if python_results and non_python_results:
            # Los resultados con Python deberían tener score >= 0.8
            for result in python_results:
                assert result["similarity_score"] >= 0.8
    
    @pytest.mark.asyncio
    async def test_search_content_truncation(self, memory_agent):
        """Test truncamiento de contenido en resultados de búsqueda"""
        long_content = "A" * 500  # Contenido muy largo
        store_request = {
            "operation": "store",
            "content": long_content,
            "conversation_id": "conv_test",
            "user_id": "user_456"
        }
        await memory_agent.process_request(store_request)
        
        search_request = {
            "operation": "search",
            "query": "A",
            "conversation_id": "conv_test"
        }
        
        result = await memory_agent.process_request(search_request)
        
        # Verificar que el contenido está truncado
        search_result = result["results"][0]
        assert len(search_result["content"]) < len(long_content)
        assert search_result["content"].endswith("...")
    
    @pytest.mark.asyncio
    async def test_conversation_filtering(self, memory_agent):
        """Test filtrado por conversación"""
        # Almacenar contenido para diferentes conversaciones
        conversations = ["conv1", "conv2", "conv3"]
        for conv_id in conversations:
            for i in range(2):
                store_request = {
                    "operation": "store",
                    "content": f"Contenido {conv_id}-{i}",
                    "conversation_id": conv_id,
                    "user_id": "user_456"
                }
                await memory_agent.process_request(store_request)
        
        # Buscar en conv1 debería devolver solo contenido de conv1
        search_request = {
            "operation": "search",
            "query": "Contenido",
            "conversation_id": "conv1"
        }
        
        result = await memory_agent.process_request(search_request)
        
        # Verificar que solo se devuelven resultados de conv1
        for search_result in result["results"]:
            memory_data = memory_agent.memory_cache[search_result["memory_id"]]
            assert memory_data["conversation_id"] == "conv1"
    
    @pytest.mark.asyncio
    async def test_error_handling(self, memory_agent):
        """Test manejo de errores"""
        # Test con request que cause excepción interna
        with patch.object(memory_agent, '_manage_memory', side_effect=Exception("Test error")):
            with pytest.raises(AgentException):
                await memory_agent.process_request({
                    "operation": "store",
                    "content": "test"
                })
