"""
Cliente para ContextForge Gateway
"""
import asyncio
import logging
from typing import Dict, Any, Optional
import httpx
from datetime import datetime

from ..core.config import settings
from ..core.exceptions import MCPCoreException


class ContextForgeClient:
    """Cliente para integración con ContextForge Gateway"""
    
    def __init__(self):
        self.logger = logging.getLogger("mcp.services.contextforge")
        self.base_url = settings.contextforge_url
        self.api_key = settings.contextforge_api_key
        self.timeout = settings.contextforge_timeout
        self.client: Optional[httpx.AsyncClient] = None
        self.is_initialized = False
    
    async def initialize(self) -> None:
        """Inicializar cliente HTTP"""
        headers = {"User-Agent": "MCP-Core-Superior/1.0"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(self.timeout)
        )
        
        self.is_initialized = True
        self.logger.info(f"ContextForge client inicializado para {self.base_url}")
    
    async def cleanup(self) -> None:
        """Limpiar recursos"""
        if self.client:
            await self.client.aclose()
            self.is_initialized = False
            self.logger.info("ContextForge client cerrado")
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar salud del gateway"""
        if not self.is_initialized:
            return {"status": "not_initialized"}
        
        try:
            response = await self.client.get("/health")
            
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
        except Exception as e:
            self.logger.error(f"Error en health check: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validar token JWT"""
        if not self.is_initialized:
            raise MCPCoreException("ContextForge client no inicializado")
        
        try:
            # Por ahora simulamos validación
            return {
                "valid": True,
                "user_id": "user123",
                "roles": ["user"],
                "expires_at": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error validando token: {e}")
            return {"valid": False, "error": str(e)}
    
    async def register_mcp_tools(self, tools: Dict[str, Any]) -> Dict[str, Any]:
        """Registrar herramientas MCP"""
        if not self.is_initialized:
            raise MCPCoreException("ContextForge client no inicializado")
        
        try:
            # Por ahora simulamos registro
            self.logger.info(f"Registrando {len(tools)} herramientas MCP")
            
            return {
                "success": True,
                "registered_tools": len(tools),
                "registration_id": "reg_123456"
            }
        except Exception as e:
            self.logger.error(f"Error registrando herramientas: {e}")
            return {"success": False, "error": str(e)}
