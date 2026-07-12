"""
Microsoft 365 - Azure AD Authentication System
Sistema de autenticación centralizado para Azure Active Directory
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from pathlib import Path

import aiohttp
import msal
from cryptography.fernet import Fernet
from passlib.context import CryptContext

from ..config.settings import settings, security_config
from ..utils.logger import get_logger

logger = get_logger(__name__)

class AzureADAuthentication:
    """Cliente de autenticación Azure AD para Microsoft 365"""
    
    def __init__(self):
        self.tenant_id = settings.tenant_id
        self.client_id = settings.client_id
        self.client_secret = settings.client_secret
        self.graph_scope = settings.graph_api_scope
        
        # Inicializar MSAL app
        self.app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            validate_authority=True
        )
        
        # Cache de tokens en memoria
        self._token_cache: Dict[str, Dict] = {}
        self._user_sessions: Dict[str, Dict] = {}
        
        # Configuración de cifrado
        self.cipher = Fernet(security_config.encryption_key.encode())
        self.password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    async def authenticate_application(self) -> str:
        """Autenticar aplicación usando client credentials flow"""
        try:
            # Verificar cache primero
            cache_key = f"{self.client_id}:{self.tenant_id}"
            if cache_key in self._token_cache:
                token_data = self._token_cache[cache_key]
                if token_data.get('expires_on', 0) > datetime.utcnow().timestamp():
                    logger.info("Token obtenido desde cache")
                    return token_data['access_token']
            
            # Solicitar nuevo token
            result = await asyncio.to_thread(
                self.app.acquire_token_for_client,
                scopes=[self.graph_scope]
            )
            
            if "access_token" in result:
                # Guardar en cache
                self._token_cache[cache_key] = {
                    'access_token': result['access_token'],
                    'expires_on': datetime.fromtimestamp(
                        result['expires_on']
                    ).timestamp(),
                    'scope': result.get('scope', ''),
                    'token_type': result.get('token_type', 'Bearer')
                }
                
                logger.info("Nuevo token obtenido exitosamente")
                return result['access_token']
            else:
                error_msg = result.get('error', 'Unknown error')
                error_description = result.get('error_description', 'No description')
                logger.error(f"Error de autenticación: {error_msg} - {error_description}")
                raise AuthenticationError(f"Azure AD authentication failed: {error_description}")
                
        except Exception as e:
            logger.error(f"Error en autenticación de aplicación: {str(e)}")
            raise AuthenticationError(f"Application authentication failed: {str(e)}")
    
    async def authenticate_user(self, username: str, password: str) -> Dict:
        """Autenticar usuario específico usando resource owner password credentials"""
        try:
            # Validar credenciales localmente
            if not await self._validate_user_credentials(username, password):
                raise AuthenticationError("Invalid user credentials")
            
            # Solicitar token para el usuario
            result = await asyncio.to_thread(
                self.app.acquire_token_by_username_password,
                username=username,
                password=password,
                scopes=[self.graph_scope]
            )
            
            if "access_token" in result:
                # Crear sesión de usuario
                session_data = {
                    'access_token': result['access_token'],
                    'refresh_token': result.get('refresh_token'),
                    'expires_on': datetime.fromtimestamp(result['expires_on']),
                    'user_id': result.get('id_token', {}).get('oid', username),
                    'tenant_id': result.get('id_token', {}).get('tid', self.tenant_id),
                    'username': username,
                    'scopes': result.get('scope', ''),
                    'created_at': datetime.utcnow(),
                    'last_accessed': datetime.utcnow()
                }
                
                # Guardar sesión cifrada
                self._user_sessions[username] = session_data
                
                logger.info(f"Usuario autenticado exitosamente: {username}")
                return {
                    'access_token': result['access_token'],
                    'user_id': session_data['user_id'],
                    'tenant_id': session_data['tenant_id'],
                    'expires_on': session_data['expires_on'],
                    'scopes': session_data['scopes']
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"Error de autenticación de usuario {username}: {error_msg}")
                raise AuthenticationError(f"User authentication failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error en autenticación de usuario {username}: {str(e)}")
            raise AuthenticationError(f"User authentication failed: {str(e)}")
    
    async def authenticate_with_code(self, authorization_code: str, redirect_uri: str) -> Dict:
        """Autenticar usando authorization code (OAuth 2.0 flow)"""
        try:
            result = await asyncio.to_thread(
                self.app.acquire_token_by_authorization_code,
                code=authorization_code,
                scopes=[self.graph_scope],
                redirect_uri=redirect_uri
            )
            
            if "access_token" in result:
                user_id = result.get('id_token', {}).get('oid', 'unknown')
                session_data = {
                    'access_token': result['access_token'],
                    'refresh_token': result.get('refresh_token'),
                    'expires_on': datetime.fromtimestamp(result['expires_on']),
                    'user_id': user_id,
                    'tenant_id': result.get('id_token', {}).get('tid', self.tenant_id),
                    'created_at': datetime.utcnow(),
                    'last_accessed': datetime.utcnow()
                }
                
                logger.info(f"Autenticación por código completada para usuario: {user_id}")
                return {
                    'access_token': result['access_token'],
                    'user_id': user_id,
                    'tenant_id': session_data['tenant_id'],
                    'expires_on': session_data['expires_on'],
                    'refresh_token': result.get('refresh_token')
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                raise AuthenticationError(f"Authorization code authentication failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error en autenticación por código: {str(e)}")
            raise AuthenticationError(f"Authorization code authentication failed: {str(e)}")
    
    async def refresh_user_token(self, username: str) -> str:
        """Renovar token de usuario usando refresh token"""
        try:
            if username not in self._user_sessions:
                raise AuthenticationError("User session not found")
            
            session = self._user_sessions[username]
            refresh_token = session.get('refresh_token')
            
            if not refresh_token:
                raise AuthenticationError("No refresh token available")
            
            # Solicitar nuevo token
            result = await asyncio.to_thread(
                self.app.acquire_token_by_refresh_token,
                refresh_token=refresh_token,
                scopes=[self.graph_scope]
            )
            
            if "access_token" in result:
                # Actualizar sesión
                session.update({
                    'access_token': result['access_token'],
                    'refresh_token': result.get('refresh_token', refresh_token),
                    'expires_on': datetime.fromtimestamp(result['expires_on']),
                    'last_accessed': datetime.utcnow()
                })
                
                logger.info(f"Token renovado para usuario: {username}")
                return result['access_token']
            else:
                logger.error(f"Error renovando token para usuario: {username}")
                raise AuthenticationError("Token refresh failed")
                
        except Exception as e:
            logger.error(f"Error renovando token para usuario {username}: {str(e)}")
            raise AuthenticationError(f"Token refresh failed: {str(e)}")
    
    async def validate_token(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """Validar token y extraer información"""
        try:
            # Decodificar JWT sin verificar firma (para obtener información)
            parts = token.split('.')
            if len(parts) != 3:
                return False, None
            
            payload = parts[1]
            # Agregar padding necesario
            payload += '=' * (4 - len(payload) % 4)
            
            import base64
            decoded = base64.b64decode(payload)
            claims = json.loads(decoded)
            
            # Verificar expiración
            exp = claims.get('exp', 0)
            if datetime.fromtimestamp(exp) < datetime.utcnow():
                logger.warning("Token expirado detectado")
                return False, claims
            
            # Verificar audiencia
            audience = claims.get('aud', '')
            if audience != self.client_id:
                logger.warning(f"Audiencia incorrecta: {audience}")
                return False, claims
            
            logger.info("Token validado exitosamente")
            return True, claims
            
        except Exception as e:
            logger.error(f"Error validando token: {str(e)}")
            return False, None
    
    async def get_user_sessions(self) -> List[Dict]:
        """Obtener información de todas las sesiones de usuario activas"""
        active_sessions = []
        current_time = datetime.utcnow()
        
        for username, session in self._user_sessions.items():
            # Filtrar sesiones activas
            if session.get('expires_on', datetime.min) > current_time:
                session_info = {
                    'username': session.get('username', username),
                    'user_id': session.get('user_id'),
                    'last_accessed': session.get('last_accessed'),
                    'expires_on': session.get('expires_on'),
                    'scopes': session.get('scopes', '').split()
                }
                active_sessions.append(session_info)
        
        return active_sessions
    
    async def logout_user(self, username: str) -> bool:
        """Cerrar sesión de usuario"""
        try:
            if username in self._user_sessions:
                del self._user_sessions[username]
                logger.info(f"Sesión cerrada para usuario: {username}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cerrando sesión para usuario {username}: {str(e)}")
            return False
    
    async def cleanup_expired_sessions(self) -> int:
        """Limpiar sesiones expiradas"""
        current_time = datetime.utcnow()
        expired_count = 0
        
        # Crear lista de usuarios a eliminar
        to_remove = []
        for username, session in self._user_sessions.items():
            if session.get('expires_on', datetime.max) <= current_time:
                to_remove.append(username)
        
        # Eliminar sesiones expiradas
        for username in to_remove:
            del self._user_sessions[username]
            expired_count += 1
        
        logger.info(f"Limpiadas {expired_count} sesiones expiradas")
        return expired_count
    
    async def _validate_user_credentials(self, username: str, password: str) -> bool:
        """Validar credenciales de usuario (implementación simplificada)"""
        # En un entorno real, esto debería validar contra Active Directory
        # o usar un servicio de autenticación empresarial
        try:
            # Simulación de validación
            return len(username) > 0 and len(password) >= 6
        except Exception as e:
            logger.error(f"Error validando credenciales para {username}: {str(e)}")
            return False
    
    async def get_authorization_url(self, redirect_uri: str, state: str = None) -> str:
        """Generar URL de autorización para OAuth 2.0"""
        try:
            auth_url = self.app.get_authorization_request_url(
                scopes=[self.graph_scope],
                redirect_uri=redirect_uri,
                state=state
            )
            return auth_url
        except Exception as e:
            logger.error(f"Error generando URL de autorización: {str(e)}")
            raise AuthenticationError(f"Authorization URL generation failed: {str(e)}")
    
    async def get_graph_permissions(self) -> Dict:
        """Obtener permisos disponibles para la aplicación"""
        try:
            # Obtener token para consultar Graph API
            token = await self.authenticate_application()
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                # Consultar permisos de la aplicación
                url = f"https://graph.microsoft.com/v1.0/applications/{self.client_id}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        app_info = await response.json()
                        return app_info.get('requiredResourceAccess', [])
                    else:
                        logger.warning(f"Error consultando permisos: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error obteniendo permisos de Graph: {str(e)}")
            return []


class AuthenticationError(Exception):
    """Excepción para errores de autenticación"""
    pass


class TokenManager:
    """Gestor de tokens con cache persistente"""
    
    def __init__(self, auth_client: AzureADAuthentication):
        self.auth_client = auth_client
        self.cache_file = Path(settings.cache_location)
        self._load_cache()
    
    def _load_cache(self):
        """Cargar cache de tokens desde archivo"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    self.auth_client._token_cache = cache_data.get('tokens', {})
                    self.auth_client._user_sessions = cache_data.get('sessions', {})
                    logger.info("Cache de tokens cargado exitosamente")
        except Exception as e:
            logger.error(f"Error cargando cache de tokens: {str(e)}")
    
    async def save_cache(self):
        """Guardar cache de tokens a archivo"""
        try:
            cache_data = {
                'tokens': self.auth_client._token_cache,
                'sessions': self.auth_client._user_sessions,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            # Cifrar datos sensibles
            encrypted_data = self.auth_client.cipher.encrypt(
                json.dumps(cache_data).encode()
            )
            
            with open(self.cache_file, 'wb') as f:
                f.write(encrypted_data)
                
            logger.info("Cache de tokens guardado exitosamente")
        except Exception as e:
            logger.error(f"Error guardando cache de tokens: {str(e)}")
    
    async def get_valid_token(self, token_type: str = "application") -> Optional[str]:
        """Obtener token válido según tipo"""
        if token_type == "application":
            cache_key = f"{self.auth_client.client_id}:{self.auth_client.tenant_id}"
            if cache_key in self.auth_client._token_cache:
                token_data = self.auth_client._token_cache[cache_key]
                if token_data.get('expires_on', 0) > datetime.utcnow().timestamp():
                    return token_data['access_token']
                
                # Intentar renovar
                return await self.auth_client.authenticate_application()
        
        return None


# Instancia global del cliente de autenticación
auth_client = AzureADAuthentication()
token_manager = TokenManager(auth_client)