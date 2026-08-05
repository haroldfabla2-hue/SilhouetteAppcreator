"""
Servicio de Autenticación
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json

from ..core.config import settings
from ..core.exceptions import MCPCoreException, UnauthorizedException


class AuthService:
    """Servicio de autenticación y autorización"""
    
    def __init__(self):
        self.logger = logging.getLogger("mcp.services.auth")
        self.jwt_secret = settings.jwt_secret
        self.jwt_algorithm = settings.jwt_algorithm
        self.jwt_expiration_hours = settings.jwt_expiration_hours
        self.is_initialized = False
        
        # Mock users para desarrollo
        self._users = {
            "admin@example.com": {
                "user_id": "admin_001",
                "password": "admin123",  # Solo para desarrollo
                "roles": ["admin", "user"],
                "active": True
            },
            "user@example.com": {
                "user_id": "user_001", 
                "password": "user123",  # Solo para desarrollo
                "roles": ["user"],
                "active": True
            }
        }
    
    async def initialize(self) -> None:
        """Inicializar servicio de autenticación"""
        if not self.jwt_secret:
            raise MCPCoreException("JWT_SECRET no configurado")
        
        self.is_initialized = True
        self.logger.info("Auth service initialized")
    
    async def cleanup(self) -> None:
        """Limpiar recursos"""
        self.is_initialized = False
        self.logger.info("Auth service cleaned up")
    
    async def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """Autenticar usuario"""
        if not self.is_initialized:
            raise MCPCoreException("Auth service no inicializado")
        
        try:
            user = self._users.get(username)
            
            if not user:
                raise UnauthorizedException("Usuario no encontrado")
            
            if not user["active"]:
                raise UnauthorizedException("Usuario desactivado")
            
            if user["password"] != password:  # Solo para desarrollo
                raise UnauthorizedException("Credenciales incorrectas")
            
            # Generar token JWT simplificado
            token_data = {
                "user_id": user["user_id"],
                "username": username,
                "roles": user["roles"],
                "iat": datetime.now().timestamp(),
                "exp": (datetime.now() + timedelta(hours=self.jwt_expiration_hours)).timestamp()
            }
            
            # Simular JWT token (en producción usar pyjwt)
            import base64
            token_payload = base64.b64encode(json.dumps(token_data).encode()).decode()
            token = f"{token_payload}.{base64.b64encode(b'mock_signature').decode()}"
            
            self.logger.info(f"User authenticated: {username}")
            
            return {
                "success": True,
                "user": {
                    "user_id": user["user_id"],
                    "username": username,
                    "roles": user["roles"]
                },
                "token": token,
                "expires_at": datetime.fromtimestamp(token_data["exp"]).isoformat()
            }
            
        except UnauthorizedException:
            raise
        except Exception as e:
            self.logger.error(f"Error en autenticación: {e}")
            raise MCPCoreException("Error en autenticación")
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validar token JWT"""
        if not self.is_initialized:
            raise MCPCoreException("Auth service no inicializado")
        
        try:
            # Simular validación de token
            # En producción: usar pyjwt para validar JWT real
            
            # Parse token
            parts = token.split('.')
            if len(parts) != 2:
                raise UnauthorizedException("Token inválido")
            
            # Decodificar payload
            import base64
            try:
                payload_data = json.loads(base64.b64decode(parts[0]))
            except Exception:
                raise UnauthorizedException("Token corrupto")
            
            # Verificar expiración
            exp_timestamp = payload_data.get("exp", 0)
            if datetime.now().timestamp() > exp_timestamp:
                raise UnauthorizedException("Token expirado")
            
            return {
                "valid": True,
                "user_id": payload_data["user_id"],
                "username": payload_data["username"],
                "roles": payload_data["roles"],
                "expires_at": datetime.fromtimestamp(exp_timestamp).isoformat()
            }
            
        except UnauthorizedException:
            raise
        except Exception as e:
            self.logger.error(f"Error validando token: {e}")
            raise UnauthorizedException("Error validando token")
    
    async def check_permission(self, token: str, required_role: str) -> bool:
        """Verificar permiso para rol específico"""
        try:
            token_data = await self.validate_token(token)
            roles = token_data.get("roles", [])
            return required_role in roles or "admin" in roles
        except Exception:
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar salud del servicio de autenticación"""
        if not self.is_initialized:
            return {"status": "not_initialized"}
        
        return {
            "status": "healthy",
            "users_count": len(self._users),
            "algorithm": self.jwt_algorithm,
            "token_expiration_hours": self.jwt_expiration_hours
        }
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtener información de usuario por ID"""
        for username, user in self._users.items():
            if user["user_id"] == user_id:
                return {
                    "user_id": user_id,
                    "username": username,
                    "roles": user["roles"],
                    "active": user["active"]
                }
        return None
