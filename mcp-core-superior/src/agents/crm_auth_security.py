"""
Sistema de Autenticación y Seguridad CRM
Gestión completa de credenciales, tokens, OAuth2, JWT y seguridad empresarial
"""

import asyncio
import logging
import json
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urljoin, urlencode
import aiohttp
import jwt
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from passlib.context import CryptContext
import redis
import os


class AuthMethod(Enum):
    """Métodos de autenticación soportados"""
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    JWT = "jwt"
    BASIC_AUTH = "basic_auth"
    BEARER_TOKEN = "bearer_token"
    OAUTH1 = "oauth1"
    CUSTOM = "custom"


class TokenStatus(Enum):
    """Estados del token"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING_REFRESH = "pending_refresh"


@dataclass
class SecurityConfig:
    """Configuración de seguridad"""
    encryption_key: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    token_expiry_hours: int = 24
    max_login_attempts: int = 5
    session_timeout_minutes: int = 30
    enable_mfa: bool = True
    redis_url: Optional[str] = None
    allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    rate_limit_requests: int = 1000
    rate_limit_window: int = 3600  # seconds


@dataclass
class AuthCredentials:
    """Credenciales de autenticación cifradas"""
    platform: str
    username: Optional[str] = None
    email: Optional[str] = None
    password_hash: Optional[str] = None
    api_key: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    token_type: Optional[str] = None
    scope: Optional[str] = None
    instance_url: Optional[str] = None
    custom_headers: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None


@dataclass
class AuthSession:
    """Sesión de autenticación"""
    session_id: str
    user_id: str
    platform: str
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    is_active: bool = True


class EncryptionManager:
    """Gestor de cifrado para credenciales"""
    
    def __init__(self, encryption_key: str):
        self.encryption_key = encryption_key
        self.fernet = Fernet(self._generate_key())
        self.logger = logging.getLogger("encryption_manager")
    
    def _generate_key(self) -> bytes:
        """Generar clave de cifrado"""
        password = self.encryption_key.encode()
        salt = b'salt_123'  # En producción usar salt único por credencial
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(password))
    
    def encrypt(self, data: str) -> str:
        """Cifrar datos"""
        try:
            encrypted = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            self.logger.error(f"Error cifrando datos: {str(e)}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Descifrar datos"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            self.logger.error(f"Error descifrando datos: {str(e)}")
            raise


class PasswordManager:
    """Gestor de contraseñas"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.logger = logging.getLogger("password_manager")
    
    def hash_password(self, password: str) -> str:
        """Hashear contraseña"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verificar contraseña"""
        try:
            return self.pwd_context.verify(password, password_hash)
        except Exception:
            return False
    
    def generate_password(self, length: int = 16) -> str:
        """Generar contraseña segura"""
        return secrets.token_urlsafe(length)
    
    def generate_api_key(self, prefix: str = "crm") -> str:
        """Generar API key"""
        return f"{prefix}_{secrets.token_hex(32)}"


class TokenManager:
    """Gestor de tokens de autenticación"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.logger = logging.getLogger("token_manager")
    
    def generate_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Generar token de acceso JWT"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def generate_refresh_token(self, data: Dict[str, Any]) -> str:
        """Generar token de renovación"""
        data.update({"type": "refresh"})
        return self.generate_access_token(data, timedelta(days=7))
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verificar token JWT"""
        try:
            decoded = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return decoded
        except jwt.ExpiredSignatureError:
            self.logger.warning("Token expirado")
            return None
        except jwt.JWTError as e:
            self.logger.error(f"Error verificando token: {str(e)}")
            return None
    
    def get_token_remaining_time(self, token: str) -> int:
        """Obtener tiempo restante de token en segundos"""
        decoded = self.verify_token(token)
        if not decoded:
            return 0
        
        exp = datetime.fromtimestamp(decoded.get("exp", 0))
        remaining = exp - datetime.utcnow()
        return max(0, int(remaining.total_seconds()))


class SessionManager:
    """Gestor de sesiones"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_client = None
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
            except Exception as e:
                self.logger = logging.getLogger("session_manager")
                self.logger.warning(f"No se pudo conectar a Redis: {str(e)}")
        
        self.sessions: Dict[str, AuthSession] = {}
        self.logger = logging.getLogger("session_manager")
    
    def create_session(self, user_id: str, platform: str, ip_address: str, user_agent: str, 
                      config: SecurityConfig) -> AuthSession:
        """Crear nueva sesión"""
        session_id = f"session_{secrets.token_hex(32)}"
        expires_at = datetime.now() + timedelta(minutes=config.session_timeout_minutes)
        
        session = AuthSession(
            session_id=session_id,
            user_id=user_id,
            platform=platform,
            created_at=datetime.now(),
            expires_at=expires_at,
            last_activity=datetime.now(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Almacenar sesión
        self.sessions[session_id] = session
        
        if self.redis_client:
            try:
                session_data = {
                    "user_id": user_id,
                    "platform": platform,
                    "expires_at": expires_at.isoformat(),
                    "ip_address": ip_address,
                    "user_agent": user_agent
                }
                self.redis_client.setex(
                    f"session:{session_id}",
                    config.session_timeout_minutes * 60,
                    json.dumps(session_data, default=str)
                )
            except Exception as e:
                self.logger.warning(f"Error almacenando sesión en Redis: {str(e)}")
        
        self.logger.info(f"Sesión creada: {session_id}")
        return session
    
    def validate_session(self, session_id: str) -> Optional[AuthSession]:
        """Validar sesión"""
        session = self.sessions.get(session_id)
        
        if not session:
            return None
        
        if not session.is_active or datetime.now() > session.expires_at:
            self.invalidate_session(session_id)
            return None
        
        # Actualizar última actividad
        session.last_activity = datetime.now()
        return session
    
    def invalidate_session(self, session_id: str):
        """Invalidar sesión"""
        if session_id in self.sessions:
            self.sessions[session_id].is_active = False
            del self.sessions[session_id]
            
            if self.redis_client:
                try:
                    self.redis_client.delete(f"session:{session_id}")
                except Exception:
                    pass
        
        self.logger.info(f"Sesión invalidada: {session_id}")
    
    def cleanup_expired_sessions(self):
        """Limpiar sesiones expiradas"""
        current_time = datetime.now()
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if not session.is_active or current_time > session.expires_at
        ]
        
        for session_id in expired_sessions:
            self.invalidate_session(session_id)
        
        if expired_sessions:
            self.logger.info(f"Limpiadas {len(expired_sessions)} sesiones expiradas")


class OAuth2Client:
    """Cliente OAuth2 genérico"""
    
    def __init__(self, config: Dict[str, Any]):
        self.auth_url = config["auth_url"]
        self.token_url = config["token_url"]
        self.client_id = config["client_id"]
        self.client_secret = config["client_secret"]
        self.redirect_uri = config.get("redirect_uri")
        self.scope = config.get("scope", "")
        self.logger = logging.getLogger("oauth2_client")
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Obtener URL de autorización"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
            "response_type": "code"
        }
        
        if state:
            params["state"] = state
        
        return f"{self.auth_url}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, authorization_code: str) -> Dict[str, Any]:
        """Intercambiar código por token"""
        token_data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": authorization_code,
            "redirect_uri": self.redirect_uri
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.token_url, data=token_data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.info("Token OAuth2 obtenido exitosamente")
                    return result
                else:
                    error_text = await response.text()
                    self.logger.error(f"Error obteniendo token: {error_text}")
                    raise Exception(f"Error OAuth2: {response.status}")


class RateLimiter:
    """Limitador de tasa para APIs"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_client = None
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
            except Exception as e:
                pass
        
        self.limits: Dict[str, Dict[str, int]] = {}
        self.logger = logging.getLogger("rate_limiter")
    
    def is_rate_limited(self, identifier: str, limit: int, window: int = 3600) -> bool:
        """Verificar si la solicitud está limitada por tasa"""
        current_time = int(datetime.now().timestamp())
        window_start = current_time - window
        
        if identifier not in self.limits:
            self.limits[identifier] = {}
        
        # Limpiar entradas antiguas
        for timestamp in list(self.limits[identifier].keys()):
            if timestamp < window_start:
                del self.limits[identifier][timestamp]
        
        # Contar solicitudes en la ventana actual
        current_window_requests = sum(
            1 for timestamp in self.limits[identifier].keys()
            if timestamp >= window_start
        )
        
        if current_window_requests >= limit:
            return True
        
        # Registrar esta solicitud
        self.limits[identifier][current_time] = current_window_requests + 1
        
        return False
    
    async def async_rate_limit_check(self, identifier: str, limit: int, window: int = 3600) -> bool:
        """Verificación asíncrona de límite de tasa"""
        return self.is_rate_limited(identifier, limit, window)


class CRMAuthManager:
    """Gestor principal de autenticación CRM"""
    
    def __init__(self, security_config: SecurityConfig):
        self.security_config = security_config
        self.encryption_manager = EncryptionManager(security_config.encryption_key)
        self.password_manager = PasswordManager()
        self.token_manager = TokenManager(security_config.jwt_secret_key, security_config.jwt_algorithm)
        self.session_manager = SessionManager(security_config.redis_url)
        self.rate_limiter = RateLimiter(security_config.redis_url)
        
        # Almacenamiento de credenciales (en producción usar base de datos)
        self.credentials_store: Dict[str, AuthCredentials] = {}
        self.oauth_clients: Dict[str, OAuth2Client] = {}
        
        self.logger = logging.getLogger("crm_auth_manager")
    
    def register_platform(self, platform: str, auth_config: Dict[str, Any]):
        """Registrar plataforma CRM"""
        if auth_config.get("method") == "oauth2":
            oauth_client = OAuth2Client(auth_config)
            self.oauth_clients[platform] = oauth_client
        
        self.logger.info(f"Plataforma registrada: {platform}")
    
    async def authenticate_user(self, username: str, password: str, platform: str, 
                              ip_address: str, user_agent: str) -> Optional[AuthSession]:
        """Autenticar usuario"""
        # Verificar límite de tasa
        rate_key = f"login:{platform}:{username}"
        if self.rate_limiter.is_rate_limited(rate_key, 5, 300):  # 5 intentos cada 5 minutos
            self.logger.warning(f"Rate limit excedido para {username} en {platform}")
            return None
        
        # Buscar credenciales
        credential_key = f"{platform}:{username}"
        credentials = self.credentials_store.get(credential_key)
        
        if not credentials or not credentials.password_hash:
            return None
        
        # Verificar contraseña
        if not self.password_manager.verify_password(password, credentials.password_hash):
            self.logger.warning(f"Contraseña inválida para {username}")
            return None
        
        # Crear sesión
        session = self.session_manager.create_session(
            user_id=username,
            platform=platform,
            ip_address=ip_address,
            user_agent=user_agent,
            config=self.security_config
        )
        
        # Actualizar último uso
        credentials.last_used = datetime.now()
        
        self.logger.info(f"Usuario autenticado: {username} en {platform}")
        return session
    
    async def authenticate_with_token(self, token: str, platform: str) -> Optional[AuthCredentials]:
        """Autenticar con token"""
        # Verificar JWT
        decoded = self.token_manager.verify_token(token)
        if not decoded or decoded.get("platform") != platform:
            return None
        
        # Obtener credenciales
        credential_key = f"{platform}:{decoded.get('user_id')}"
        credentials = self.credentials_store.get(credential_key)
        
        if not credentials:
            return None
        
        # Verificar si el token coincide
        if credentials.access_token != token:
            return None
        
        # Actualizar último uso
        credentials.last_used = datetime.now()
        
        return credentials
    
    async def refresh_access_token(self, refresh_token: str, platform: str) -> Optional[str]:
        """Renovar token de acceso"""
        # Verificar refresh token
        decoded = self.token_manager.verify_token(refresh_token)
        if not decoded or decoded.get("platform") != platform:
            return None
        
        # Obtener credenciales
        credential_key = f"{platform}:{decoded.get('user_id')}"
        credentials = self.credentials_store.get(credential_key)
        
        if not credentials or credentials.refresh_token != refresh_token:
            return None
        
        # Renovar token (implementar lógica específica de plataforma)
        # Por ahora, generar nuevo token
        new_token = self.token_manager.generate_access_token({
            "user_id": decoded.get("user_id"),
            "platform": platform
        })
        
        # Actualizar token
        credentials.access_token = new_token
        credentials.expires_at = datetime.now() + timedelta(hours=self.security_config.token_expiry_hours)
        
        self.logger.info(f"Token renovado para {decoded.get('user_id')} en {platform}")
        return new_token
    
    def store_credentials(self, platform: str, user_id: str, credentials_data: Dict[str, Any]):
        """Almacenar credenciales de forma segura"""
        # Crear credenciales cifradas
        credentials = AuthCredentials(
            platform=platform,
            username=credentials_data.get("username"),
            email=credentials_data.get("email"),
            client_id=credentials_data.get("client_id"),
            client_secret=credentials_data.get("client_secret"),
            access_token=credentials_data.get("access_token"),
            refresh_token=credentials_data.get("refresh_token"),
            expires_at=credentials_data.get("expires_at"),
            token_type=credentials_data.get("token_type"),
            scope=credentials_data.get("scope"),
            instance_url=credentials_data.get("instance_url"),
            custom_headers=credentials_data.get("custom_headers", {})
        )
        
        # Hashear contraseña si existe
        if credentials_data.get("password"):
            credentials.password_hash = self.password_manager.hash_password(credentials_data["password"])
        
        # Cifrar tokens sensibles
        if credentials.client_secret:
            credentials.client_secret = self.encryption_manager.encrypt(credentials.client_secret)
        
        # Almacenar
        credential_key = f"{platform}:{user_id}"
        self.credentials_store[credential_key] = credentials
        
        self.logger.info(f"Credenciales almacenadas para {platform}:{user_id}")
    
    def get_credentials(self, platform: str, user_id: str) -> Optional[AuthCredentials]:
        """Obtener credenciales"""
        credential_key = f"{platform}:{user_id}"
        return self.credentials_store.get(credential_key)
    
    def validate_session(self, session_id: str) -> Optional[AuthSession]:
        """Validar sesión de usuario"""
        return self.session_manager.validate_session(session_id)
    
    def invalidate_session(self, session_id: str):
        """Invalidar sesión"""
        self.session_manager.invalidate_session(session_id)
    
    def check_rate_limit(self, identifier: str, limit: Optional[int] = None) -> bool:
        """Verificar límite de tasa"""
        rate_limit = limit or self.security_config.rate_limit_requests
        window = self.security_config.rate_limit_window
        return self.rate_limiter.is_rate_limited(identifier, rate_limit, window)
    
    def get_oauth_authorization_url(self, platform: str, state: Optional[str] = None) -> Optional[str]:
        """Obtener URL de autorización OAuth2"""
        oauth_client = self.oauth_clients.get(platform)
        if not oauth_client:
            return None
        
        return oauth_client.get_authorization_url(state)
    
    async def exchange_oauth_code(self, platform: str, code: str) -> Optional[Dict[str, Any]]:
        """Intercambiar código OAuth por tokens"""
        oauth_client = self.oauth_clients.get(platform)
        if not oauth_client:
            return None
        
        try:
            tokens = await oauth_client.exchange_code_for_token(code)
            return tokens
        except Exception as e:
            self.logger.error(f"Error en intercambio OAuth para {platform}: {str(e)}")
            return None
    
    def get_security_report(self) -> Dict[str, Any]:
        """Generar reporte de seguridad"""
        active_sessions = sum(1 for session in self.session_manager.sessions.values() if session.is_active)
        
        return {
            "security_status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "total_stored_credentials": len(self.credentials_store),
                "active_sessions": active_sessions,
                "configured_platforms": list(self.oauth_clients.keys()),
                "rate_limit_enabled": True,
                "encryption_enabled": True,
                "session_timeout_minutes": self.security_config.session_timeout_minutes
            },
            "recommendations": [
                "Rotar claves de cifrado regularmente",
                "Monitorear actividades de sesión",
                "Implementar MFA para cuentas críticas",
                "Revisar logs de acceso semanalmente"
            ]
        }


# Configuraciones de seguridad por plataforma
CRM_SECURITY_CONFIGS = {
    "salesforce": {
        "method": "oauth2",
        "auth_url": "https://login.salesforce.com/services/oauth2/authorize",
        "token_url": "https://login.salesforce.com/services/oauth2/token",
        "scope": "api refresh_token full",
        "required_fields": ["client_id", "client_secret"]
    },
    "hubspot": {
        "method": "oauth2",
        "auth_url": "https://app.hubspot.com/oauth/authorize",
        "token_url": "https://api.hubapi.com/oauth/v1/token",
        "scope": "contacts content deals companies",
        "required_fields": ["client_id", "client_secret"]
    },
    "pipedrive": {
        "method": "api_key",
        "required_fields": ["api_key"],
        "headers_format": {"Authorization": "Token {api_key}"}
    },
    "zoho": {
        "method": "oauth2",
        "auth_url": "https://accounts.zoho.com/oauth/v2/auth",
        "token_url": "https://accounts.zoho.com/oauth/v2/token",
        "scope": "ZohoCRM.modules.ALL ZohoCRM.users.READ",
        "required_fields": ["client_id", "client_secret"]
    }
}


# Ejemplo de uso
async def demo_auth_system():
    """Demostración del sistema de autenticación"""
    
    # Configuración de seguridad
    config = SecurityConfig(
        encryption_key="your_encryption_key_here",
        jwt_secret_key="your_jwt_secret_here",
        redis_url="redis://localhost:6379"
    )
    
    # Inicializar gestor
    auth_manager = CRMAuthManager(config)
    
    # Registrar plataformas
    for platform, security_config in CRM_SECURITY_CONFIGS.items():
        auth_manager.register_platform(platform, security_config)
    
    # Almacenar credenciales de prueba
    auth_manager.store_credentials("salesforce", "test_user", {
        "username": "test@salesforce.com",
        "password": "secure_password",
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token"
    })
    
    # Simular autenticación
    session = await auth_manager.authenticate_user(
        username="test@salesforce.com",
        password="secure_password",
        platform="salesforce",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0"
    )
    
    if session:
        print(f"Autenticación exitosa. Sesión: {session.session_id}")
        
        # Verificar sesión
        validated_session = auth_manager.validate_session(session.session_id)
        print(f"Sesión válida: {validated_session is not None}")
    
    # Generar reporte de seguridad
    security_report = auth_manager.get_security_report()
    print(f"Reporte de seguridad: {json.dumps(security_report, indent=2, default=str)}")


if __name__ == "__main__":
    asyncio.run(demo_auth_system())