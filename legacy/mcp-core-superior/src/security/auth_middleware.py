"""
Middleware de autenticación para FastAPI
Proporciona autenticación automática en endpoints
"""

import asyncio
from typing import Dict, Optional, List
from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .auth_system import auth_system


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware de autenticación automática"""
    
    def __init__(self, app, exclude_paths: List[str] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/login",
            "/auth/register",
            "/auth/refresh",
            "/auth/sso"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Procesar request con autenticación"""
        path = request.url.path
        
        # Excluir rutas que no requieren autenticación
        if any(path.startswith(exclude_path) for exclude_path in self.exclude_paths):
            return await call_next(request)
        
        # Obtener token de autorización
        auth_header = request.headers.get("Authorization")
        api_key_header = request.headers.get("X-API-Key")
        
        if not auth_header and not api_key_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de autorización requerido",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        try:
            user_info = None
            
            # Verificar Bearer token
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                user_info = await auth_system.validate_access_token(token)
            
            # Verificar API Key
            elif api_key_header:
                user_info = await auth_system.validate_api_key(api_key_header)
            
            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido"
                )
            
            # Agregar información del usuario al request state
            request.state.user = user_info
            
            # Crear nueva response con headers de seguridad
            response = await call_next(request)
            
            # Agregar headers de seguridad
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            
            return response
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )


def get_current_user(request: Request) -> Dict:
    """Dependencia para obtener usuario autenticado"""
    if not hasattr(request.state, 'user'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no autenticado"
        )
    return request.state.user


def require_permission(permission: str):
    """Dependencia para requerir permiso específico"""
    def dependency(user: Dict = Depends(get_current_user)):
        user_permissions = user.get('permissions', [])
        if permission not in user_permissions and 'admin' not in user.get('roles', []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso requerido: {permission}"
            )
        return user
    return dependency


def require_role(role: str):
    """Dependencia para requerir rol específico"""
    def dependency(user: Dict = Depends(get_current_user)):
        user_roles = user.get('roles', [])
        if role not in user_roles and 'admin' not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rol requerido: {role}"
            )
        return user
    return dependency


async def check_resource_permission(resource: str, action: str):
    """Dependencia para verificar permiso de recurso"""
    async def dependency(user: Dict = Depends(get_current_user), 
                        request: Request = None):
        user_id = user.get('user_id')
        context = {
            "ip_address": request.client.host if request else "",
            "user_agent": request.headers.get("User-Agent", "") if request else ""
        }
        
        has_permission = await auth_system.check_permission(
            user_id=user_id,
            resource=resource,
            action=action,
            context=context
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Sin permisos para {action} en {resource}"
            )
        
        return user
    return dependency