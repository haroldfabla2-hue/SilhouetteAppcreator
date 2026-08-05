"""
Wrapper MCP para MemoryManagerAgent
Gestiona memoria semántica y contexto
"""
from typing import Dict, Any, List, Optional
import asyncio
import logging
from datetime import datetime

from .base_agent_wrapper import BaseAgentWrapper, AgentCapability
from ..core.exceptions import AgentException, handle_exceptions
from ..core.config import settings


class MemoryManagerAgentWrapper(BaseAgentWrapper):
    """Wrapper para MemoryManagerAgent"""
    
    def __init__(self):
        capabilities = [
            AgentCapability.KNOWLEDGE_STORAGE,
            AgentCapability.SEMANTIC_SEARCH,
            AgentCapability.CONTEXT_RETRIEVAL,
            AgentCapability.CONVERSATION_MANAGEMENT
        ]
        
        super().__init__(
            agent_name="memory_manager",
            capabilities=capabilities,
            max_concurrent=settings.max_concurrent_tools,
            timeout_seconds=settings.agent_timeout_seconds,
            retry_attempts=settings.agent_retry_attempts,
            retry_delay=settings.agent_retry_delay
        )
        
        self.logger = logging.getLogger("mcp.agents.memory_manager")
        self.memory_cache = {}
    
    async def _initialize(self) -> None:
        await asyncio.sleep(0.1)
        self.logger.info("MemoryManagerAgent inicializado")
    
    async def process_request(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self.execute_operation(
            operation_name="manage_memory",
            capability=AgentCapability.KNOWLEDGE_STORAGE,
            operation_func=self._manage_memory,
            request=request,
            context=context
        )
    
    @handle_exceptions
    async def _manage_memory(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        operation = request.get("operation", "store")
        content = request.get("content")
        query = request.get("query")
        conversation_id = request.get("conversation_id")
        user_id = request.get("user_id")
        
        if operation == "store":
            if not content:
                raise AgentException("Content es requerido para operación store", self.agent_name, "manage_memory")
            
            memory_id = f"mem_{int(datetime.now().timestamp())}"
            self.memory_cache[memory_id] = {
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "conversation_id": conversation_id
            }
            
            return {
                "success": True,
                "operation": "store",
                "memory_id": memory_id,
                "message": "Memoria almacenada exitosamente"
            }
        
        elif operation == "search":
            if not query:
                raise AgentException("Query es requerido para operación search", self.agent_name, "manage_memory")
            
            # Simular búsqueda semántica
            results = []
            for memory_id, memory_data in list(self.memory_cache.items())[-5:]:  # Últimas 5 memorias
                similarity = 0.8 if query.lower() in memory_data["content"].lower() else 0.3
                results.append({
                    "memory_id": memory_id,
                    "content": memory_data["content"][:200] + "...",
                    "similarity_score": similarity,
                    "timestamp": memory_data["timestamp"]
                })
            
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            return {
                "success": True,
                "operation": "search",
                "query": query,
                "total_results": len(results),
                "results": results
            }
        
        elif operation == "get_context":
            if not conversation_id:
                raise AgentException("conversation_id es requerido para operación get_context", self.agent_name, "manage_memory")
            
            conversation_memories = [
                memory for memory in self.memory_cache.values()
                if memory.get("conversation_id") == conversation_id
            ]
            
            return {
                "success": True,
                "operation": "get_context",
                "conversation_id": conversation_id,
                "total_messages": len(conversation_memories),
                "context": [mem["content"] for mem in conversation_memories[-10:]]  # Últimos 10 mensajes
            }
        
        else:
            raise AgentException(f"Operación no soportada: {operation}", self.agent_name, "manage_memory")
    
    async def manage_memory(self, operation: str, content: Optional[str] = None, query: Optional[str] = None, conversation_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        request = {
            "operation": operation,
            "content": content,
            "query": query,
            "conversation_id": conversation_id,
            "user_id": user_id
        }
        return await self.process_request(request)
    
    async def get_status(self) -> Dict[str, Any]:
        base_status = super().get_status()
        base_status.update({
            "agent_type": "memory_manager",
            "specialization": "Gestión de memoria semántica y contexto",
            "cache_size": len(self.memory_cache),
            "cache_capacity": settings.memory_cache_size
        })
        return base_status
