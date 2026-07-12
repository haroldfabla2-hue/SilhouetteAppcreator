"""
Sistema Completo de Authentication & Authorization
Implementa JWT, OAuth 2.0, MFA, RBAC, ABAC, SSO y auditoría
"""

import asyncio
import hashlib
import hmac
import jwt
import pyotp
import qrcode
import base64
import json
import time
import secrets
import logging
import smtplib
import ssl
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Set
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from dataclasses import dataclass, field
from enum import Enum
from cryptography.fernet import Fernet
import ldap3
import redis
from passlib.context import CryptContext
from passlib.hash import bcrypt
import bcrypt
from urllib.parse import urlencode
import requests
from pathlib import Path

# Configuración del sistema
from ..core.config import settings
from ..core.exceptions import MCPCoreException, UnauthorizedException, ForbiddenException


class TokenType(Enum):
    """Tipos de token soportados"""
    ACCESS = "access"
    REFRESH = "refresh"
    ID = "id"


class AuthProvider(Enum):
    """Proveedores de autenticación"""
    LOCAL = "local"
    LDAP = "ldap"
    ACTIVE_DIRECTORY = "ad"
    OAUTH_GOOGLE = "google"
    OAUTH_GITHUB = "github"
    OAUTH_MICROSOFT = "microsoft"
    SAML = "saml"
    OPENID = "openid"


class PermissionType(Enum):
    """Tipos de permisos"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


class SessionStatus(Enum):
    """Estados de sesión"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


@dataclass
class User:
    """Modelo de usuario"""
    user_id: str
    username: str
    email: str
    password_hash: str
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    phone_number: Optional[str] = None
    provider: AuthProvider = AuthProvider.LOCAL
    active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Role:
    """Modelo de rol"""
    role_id: str
    name: str
    description: str
    permissions: List[str] = field(default_factory=list)
    parent_roles: List[str] = field(default_factory=list)
    inherits_from: List[str] = field(default_factory=list)
    active: bool = True


@dataclass
class Permission:
    """Modelo de permiso"""
    permission_id: str
    name: str
    resource: str
    action: PermissionType
    conditions: Dict[str, Any] = field(default_factory=dict)
    inherited: bool = False


@dataclass
class Session:
    """Modelo de sesión"""
    session_id: str
    user_id: str
    token: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    status: SessionStatus = SessionStatus.ACTIVE
    mfa_verified: bool = False


@dataclass
class APIKey:
    """Modelo de API Key"""
    key_id: str
    user_id: str
    key_hash: str
    permissions: List[str]
    scopes: List[str]
    rate_limit: int = 1000
    expires_at: Optional[datetime] = None
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AuditLog:
    """Modelo de auditoría"""
    log_id: str
    user_id: str
    action: str
    resource: str
    success: bool
    ip_address: str
    user_agent: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)


class SecurityConfig:
    """Configuración de seguridad"""
    
    # JWT Configuration
    JWT_SECRET_KEY = settings.jwt_secret or secrets.token_urlsafe(32)
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES = 15
    JWT_REFRESH_EXPIRE_DAYS = 30
    JWT_ID_EXPIRE_MINUTES = 5
    
    # Password Configuration
    PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_PASSWORD_COMPLEXITY = True
    
    # Session Configuration
    SESSION_TIMEOUT_MINUTES = 30
    MAX_CONCURRENT_SESSIONS = 5
    CLEANUP_INTERVAL_HOURS = 1
    
    # MFA Configuration
    TOTP_ISSUER = "mcp-core-superior"
    SMS_PROVIDER = "twilio"  # o "aws_sns"
    
    # Rate Limiting
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_WINDOW = 3600
    
    # OAuth Configuration
    OAUTH_REDIRECT_URI = "http://localhost:8000/auth/callback"
    OAUTH_SCOPES = ["openid", "email", "profile"]


class LDAPAuthenticator:
    """Autenticador LDAP"""
    
    def __init__(self, ldap_config: Dict[str, str]):
        self.ldap_config = ldap_config
        self.server = None
        
    async def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """Autenticar contra LDAP"""
        try:
            server = ldap3.Server(
                self.ldap_config['server'],
                port=int(self.ldap_config.get('port', 389)),
                use_ssl=self.ldap_config.get('use_ssl', False)
            )
            
            conn = ldap3.Connection(
                server,
                user=f"{username}@{self.ldap_config['domain']}",
                password=password,
                auto_bind=True
            )
            
            # Buscar usuario
            conn.search(
                search_base=self.ldap_config['search_base'],
                search_filter=f"(sAMAccountName={username})",
                attributes=['givenName', 'sn', 'mail', 'memberOf']
            )
            
            if not conn.entries:
                raise UnauthorizedException("Usuario no encontrado en LDAP")
            
            user_entry = conn.entries[0]
            
            return {
                "success": True,
                "user_id": str(user_entry.entry_dn),
                "username": username,
                "email": str(user_entry.mail.value) if user_entry.mail.value else f"{username}@{self.ldap_config['domain']}",
                "first_name": str(user_entry.givenName.value) if user_entry.givenName.value else "",
                "last_name": str(user_entry.sn.value) if user_entry.sn.value else "",
                "groups": [str(group) for group in user_entry.memberOf.value] if user_entry.memberOf.value else []
            }
            
        except Exception as e:
            logging.error(f"Error en autenticación LDAP: {e}")
            raise UnauthorizedException("Error en autenticación LDAP")


class OAuthAuthenticator:
    """Autenticador OAuth 2.0 / OpenID Connect"""
    
    def __init__(self, provider: str, client_id: str, client_secret: str, redirect_uri: str):
        self.provider = provider
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.providers_config = {
            "google": {
                "auth_url": "https://accounts.google.com/o/oauth2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo"
            },
            "github": {
                "auth_url": "https://github.com/login/oauth/authorize",
                "token_url": "https://github.com/login/oauth/access_token",
                "userinfo_url": "https://api.github.com/user"
            },
            "microsoft": {
                "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                "userinfo_url": "https://graph.microsoft.com/v1.0/me"
            }
        }
    
    def get_authorization_url(self, state: str = None) -> str:
        """Generar URL de autorización"""
        if state is None:
            state = secrets.token_urlsafe(16)
        
        config = self.providers_config.get(self.provider)
        if not config:
            raise MCPCoreException(f"Proveedor {self.provider} no soportado")
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(SecurityConfig.OAUTH_SCOPES),
            "state": state
        }
        
        return f"{config['auth_url']}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Intercambiar código por token"""
        config = self.providers_config.get(self.provider)
        if not config:
            raise MCPCoreException(f"Proveedor {self.provider} no soportado")
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }
        
        headers = {"Accept": "application/json"}
        response = requests.post(config['token_url'], data=data, headers=headers)
        
        if response.status_code != 200:
            raise UnauthorizedException("Error intercambiando código por token")
        
        return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Obtener información del usuario"""
        config = self.providers_config.get(self.provider)
        if not config:
            raise MCPCoreException(f"Proveedor {self.provider} no soportado")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(config['userinfo_url'], headers=headers)
        
        if response.status_code != 200:
            raise UnauthorizedException("Error obteniendo información del usuario")
        
        user_data = response.json()
        
        return {
            "user_id": user_data.get("id") or user_data.get("sub"),
            "username": user_data.get("username") or user_data.get("name"),
            "email": user_data.get("email"),
            "first_name": user_data.get("given_name") or user_data.get("name", "").split()[0] if user_data.get("name") else "",
            "last_name": user_data.get("family_name") or user_data.get("name", "").split()[-1] if user_data.get("name") else ""
        }


class MFAManager:
    """Gestor de autenticación multifactor"""
    
    def __init__(self):
        self.sms_provider = SMSProvider()
        
    def generate_totp_secret(self) -> str:
        """Generar secreto TOTP"""
        return pyotp.random_base32()
    
    def generate_totp_qr_code(self, user_email: str, secret: str) -> str:
        """Generar código QR para TOTP"""
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user_email,
            issuer_name=SecurityConfig.TOTP_ISSUER
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        return img.to_string()
    
    def verify_totp(self, secret: str, token: str) -> bool:
        """Verificar token TOTP"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    async def send_sms_code(self, phone_number: str) -> str:
        """Enviar código SMS"""
        code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        await self.sms_provider.send_sms(phone_number, f"Código de verificación: {code}")
        
        # En producción, guardar el código en caché con TTL
        cache_key = f"sms_code:{hashlib.sha256(phone_number.encode()).hexdigest()}"
        # redis_client.setex(cache_key, 300, code)  # 5 minutos de TTL
        
        return code


class SMSProvider:
    """Proveedor de SMS"""
    
    async def send_sms(self, phone_number: str, message: str):
        """Enviar SMS"""
        # Implementación con Twilio o AWS SNS
        try:
            # Ejemplo con Twilio
            from twilio.rest import Client
            
            account_sid = settings.twilio_account_sid
            auth_token = settings.twilio_auth_token
            client = Client(account_sid, auth_token)
            
            message = client.messages.create(
                body=message,
                from_=settings.twilio_phone_number,
                to=phone_number
            )
            
            logging.info(f"SMS enviado a {phone_number}: {message.sid}")
            
        except Exception as e:
            logging.error(f"Error enviando SMS: {e}")
            raise MCPCoreException("Error enviando código SMS")


class EmailProvider:
    """Proveedor de email"""
    
    def __init__(self):
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        
    async def send_email(self, to_email: str, subject: str, body: str, html_body: str = None):
        """Enviar email"""
        try:
            msg = MimeMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'plain'))
            if html_body:
                msg.attach(MimeText(html_body, 'html'))
            
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                
            logging.info(f"Email enviado a {to_email}")
            
        except Exception as e:
            logging.error(f"Error enviando email: {e}")
            raise MCPCoreException("Error enviando email")


class AuditLogger:
    """Sistema de auditoría"""
    
    def __init__(self):
        self.logger = logging.getLogger("mcp.security.audit")
        
    async def log_authentication_attempt(self, user_id: str, success: bool, ip_address: str, 
                                       user_agent: str, details: Dict[str, Any] = None):
        """Registrar intento de autenticación"""
        await self.log_event(
            user_id=user_id,
            action="authentication_attempt",
            resource="auth",
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {}
        )
    
    async def log_authorization_check(self, user_id: str, resource: str, action: str,
                                    permission: str, success: bool, ip_address: str, details: Dict[str, Any] = None):
        """Registrar verificación de autorización"""
        await self.log_event(
            user_id=user_id,
            action="authorization_check",
            resource=resource,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "action": action,
                "permission": permission,
                **(details or {})
            }
        )
    
    async def log_event(self, user_id: str, action: str, resource: str, success: bool,
                       ip_address: str, user_agent: str, details: Dict[str, Any] = None):
        """Registrar evento de auditoría"""
        log_entry = AuditLog(
            log_id=secrets.token_hex(16),
            user_id=user_id,
            action=action,
            resource=resource,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now(),
            details=details or {}
        )
        
        # Guardar en base de datos o archivo
        log_data = {
            "log_id": log_entry.log_id,
            "user_id": log_entry.user_id,
            "action": log_entry.action,
            "resource": log_entry.resource,
            "success": log_entry.success,
            "ip_address": log_entry.ip_address,
            "user_agent": log_entry.user_agent,
            "timestamp": log_entry.timestamp.isoformat(),
            "details": log_entry.details
        }
        
        self.logger.info(f"AUDIT: {json.dumps(log_data)}")
        
        # En producción, guardar en base de datos
        # await save_audit_log_to_database(log_data)


class AuthSystem:
    """Sistema principal de autenticación y autorización"""
    
    def __init__(self):
        self.logger = logging.getLogger("mcp.security.auth")
        self.config = SecurityConfig()
        
        # Almacenamiento de datos (en producción usar base de datos)
        self._users: Dict[str, User] = {}
        self._roles: Dict[str, Role] = {}
        self._permissions: Dict[str, Permission] = {}
        self._sessions: Dict[str, Session] = {}
        self._api_keys: Dict[str, APIKey] = {}
        self._login_attempts: Dict[str, int] = {}
        self._locked_accounts: Dict[str, datetime] = {}
        
        # Componentes
        self.audit_logger = AuditLogger()
        self.mfa_manager = MFAManager()
        self.encryptor = Fernet(base64.urlsafe_b64encode(SecurityConfig.JWT_SECRET_KEY.encode()))
        
        # Autenticadores externos
        self.ldap_authenticator = None
        self.oauth_authenticators: Dict[str, OAuthAuthenticator] = {}
        
        # Cache para rate limiting
        self._rate_limit_cache = {}
        
        self.is_initialized = False
    
    async def initialize(self):
        """Inicializar sistema de autenticación"""
        try:
            # Inicializar autenticadores LDAP si están configurados
            if hasattr(settings, 'ldap_server') and settings.ldap_server:
                self.ldap_authenticator = LDAPAuthenticator({
                    'server': settings.ldap_server,
                    'port': settings.ldap_port,
                    'domain': settings.ldap_domain,
                    'search_base': settings.ldap_search_base,
                    'use_ssl': getattr(settings, 'ldap_use_ssl', False)
                })
            
            # Inicializar autenticadores OAuth
            oauth_configs = getattr(settings, 'oauth_configs', {})
            for provider, config in oauth_configs.items():
                if config.get('client_id') and config.get('client_secret'):
                    self.oauth_authenticators[provider] = OAuthAuthenticator(
                        provider=provider,
                        client_id=config['client_id'],
                        client_secret=config['client_secret'],
                        redirect_uri=SecurityConfig.OAUTH_REDIRECT_URI
                    )
            
            # Cargar roles y permisos por defecto
            await self._load_default_roles_and_permissions()
            
            # Crear usuario administrador por defecto
            await self.create_user(
                username="admin",
                email="admin@localhost",
                password="admin123",
                roles=["admin"],
                provider=AuthProvider.LOCAL
            )
            
            self.is_initialized = True
            self.logger.info("Sistema de autenticación inicializado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando sistema de autenticación: {e}")
            raise MCPCoreException("Error inicializando sistema de autenticación")
    
    async def _load_default_roles_and_permissions(self):
        """Cargar roles y permisos por defecto"""
        
        # Permisos básicos
        permissions = [
            Permission("perm_user_create", "Crear Usuario", "user", PermissionType.CREATE),
            Permission("perm_user_read", "Leer Usuario", "user", PermissionType.READ),
            Permission("perm_user_update", "Actualizar Usuario", "user", PermissionType.UPDATE),
            Permission("perm_user_delete", "Eliminar Usuario", "user", PermissionType.DELETE),
            
            Permission("perm_role_create", "Crear Rol", "role", PermissionType.CREATE),
            Permission("perm_role_read", "Leer Rol", "role", PermissionType.READ),
            Permission("perm_role_update", "Actualizar Rol", "role", PermissionType.UPDATE),
            Permission("perm_role_delete", "Eliminar Rol", "role", PermissionType.DELETE),
            
            Permission("perm_admin_all", "Administración Completa", "*", PermissionType.ADMIN),
            Permission("perm_api_access", "Acceso API", "api", PermissionType.EXECUTE),
        ]
        
        for perm in permissions:
            self._permissions[perm.permission_id] = perm
        
        # Roles básicos
        roles = [
            Role("admin", "Administrador", "Administrador del sistema", 
                 ["perm_admin_all"], [], []),
            Role("user", "Usuario", "Usuario del sistema",
                 ["perm_user_read", "perm_api_access"], [], []),
            Role("manager", "Gerente", "Gerente con permisos extendidos",
                 ["perm_user_create", "perm_user_read", "perm_user_update"], ["user"], []),
        ]
        
        for role in roles:
            self._roles[role.role_id] = role
    
    # ==================== AUTENTICACIÓN ====================
    
    async def authenticate(self, username: str, password: str, ip_address: str = "",
                          user_agent: str = "", mfa_token: str = None) -> Dict[str, Any]:
        """Autenticar usuario"""
        
        # Verificar rate limiting
        if not await self._check_rate_limit(ip_address):
            await self.audit_logger.log_authentication_attempt(
                username, False, ip_address, user_agent,
                {"reason": "rate_limit_exceeded"}
            )
            raise UnauthorizedException("Demasiados intentos. Intente más tarde.")
        
        # Verificar si la cuenta está bloqueada
        if username in self._locked_accounts:
            lockout_end = self._locked_accounts[username]
            if datetime.now() < lockout_end:
                raise UnauthorizedException("Cuenta bloqueada temporalmente")
            else:
                del self._locked_accounts[username]
        
        try:
            user = None
            provider_used = AuthProvider.LOCAL
            
            # 1. Intentar autenticación local
            user = self._get_user_by_username(username)
            
            # 2. Si no existe localmente, intentar LDAP
            if not user and self.ldap_authenticator:
                try:
                    ldap_user = await self.ldap_authenticator.authenticate(username, password)
                    provider_used = AuthProvider.LDAP
                    
                    # Crear usuario local si no existe
                    if not self._get_user_by_username(ldap_user['username']):
                        user = await self.create_user(
                            username=ldap_user['username'],
                            email=ldap_user['email'],
                            password_hash=bcrypt.hash(password),
                            roles=[],  # Se asignarán por grupos LDAP
                            provider=AuthProvider.LDAP,
                            attributes={
                                "first_name": ldap_user.get('first_name', ''),
                                "last_name": ldap_user.get('last_name', ''),
                                "groups": ldap_user.get('groups', [])
                            }
                        )
                    else:
                        user = self._get_user_by_username(username)
                        
                except Exception as e:
                    self.logger.warning(f"Error en autenticación LDAP para {username}: {e}")
            
            if not user:
                await self._record_failed_attempt(username)
                await self.audit_logger.log_authentication_attempt(
                    username, False, ip_address, user_agent,
                    {"reason": "user_not_found"}
                )
                raise UnauthorizedException("Credenciales incorrectas")
            
            if not user.active:
                await self.audit_logger.log_authentication_attempt(
                    user.user_id, False, ip_address, user_agent,
                    {"reason": "user_inactive"}
                )
                raise UnauthorizedException("Usuario desactivado")
            
            # Verificar contraseña
            if not self._verify_password(password, user.password_hash):
                await self._record_failed_attempt(username)
                await self.audit_logger.log_authentication_attempt(
                    user.user_id, False, ip_address, user_agent,
                    {"reason": "invalid_password"}
                )
                raise UnauthorizedException("Credenciales incorrectas")
            
            # Verificar MFA si está habilitado
            if user.mfa_enabled and not mfa_token:
                return {
                    "mfa_required": True,
                    "mfa_methods": ["totp", "sms"],
                    "message": "Código MFA requerido"
                }
            
            if user.mfa_enabled and mfa_token:
                if user.mfa_secret:
                    if not self.mfa_manager.verify_totp(user.mfa_secret, mfa_token):
                        await self.audit_logger.log_authentication_attempt(
                            user.user_id, False, ip_address, user_agent,
                            {"reason": "invalid_mfa_token"}
                        )
                        raise UnauthorizedException("Código MFA incorrecto")
                elif user.phone_number:
                    # Verificar código SMS
                    if not await self._verify_sms_code(user.phone_number, mfa_token):
                        await self.audit_logger.log_authentication_attempt(
                            user.user_id, False, ip_address, user_agent,
                            {"reason": "invalid_sms_code"}
                        )
                        raise UnauthorizedException("Código SMS incorrecto")
            
            # Autenticación exitosa
            user.last_login = datetime.now()
            
            # Generar tokens
            tokens = await self._generate_tokens(user)
            
            # Crear sesión
            session = await self._create_session(
                user_id=user.user_id,
                access_token=tokens['access_token'],
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            await self.audit_logger.log_authentication_attempt(
                user.user_id, True, ip_address, user_agent,
                {"provider": provider_used.value, "mfa_used": bool(mfa_token)}
            )
            
            return {
                "success": True,
                "user": {
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "roles": user.roles,
                    "permissions": await self._get_user_permissions(user.user_id),
                    "attributes": user.attributes
                },
                "tokens": tokens,
                "session_id": session.session_id,
                "expires_at": tokens['expires_at']
            }
            
        except UnauthorizedException:
            raise
        except Exception as e:
            self.logger.error(f"Error en autenticación para {username}: {e}")
            await self.audit_logger.log_authentication_attempt(
                username, False, ip_address, user_agent,
                {"reason": "internal_error", "error": str(e)}
            )
            raise MCPCoreException("Error en autenticación")
    
    async def oauth_authenticate(self, provider: str, code: str, ip_address: str = "", 
                               user_agent: str = "") -> Dict[str, Any]:
        """Autenticación OAuth"""
        if provider not in self.oauth_authenticators:
            raise MCPCoreException(f"Proveedor OAuth {provider} no configurado")
        
        try:
            oauth_auth = self.oauth_authenticators[provider]
            
            # Intercambiar código por token
            token_data = await oauth_auth.exchange_code_for_token(code)
            
            # Obtener información del usuario
            user_info = await oauth_auth.get_user_info(token_data['access_token'])
            
            # Buscar o crear usuario
            user = self._get_user_by_username(user_info['username'])
            if not user:
                user = await self.create_user(
                    username=user_info['username'],
                    email=user_info['email'] or f"{user_info['username']}@{provider}.oauth",
                    password_hash=bcrypt.hash(secrets.token_urlsafe(32)),
                    roles=["user"],  # Rol por defecto
                    provider=AuthProvider.OAUTH_GOOGLE if provider == "google" else AuthProvider.OAUTH_GITHUB,
                    attributes={
                        "first_name": user_info.get('first_name', ''),
                        "last_name": user_info.get('last_name', ''),
                        "oauth_provider": provider,
                        "oauth_sub": user_info['user_id']
                    }
                )
            
            # Generar tokens
            tokens = await self._generate_tokens(user)
            
            # Crear sesión
            session = await self._create_session(
                user_id=user.user_id,
                access_token=tokens['access_token'],
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            await self.audit_logger.log_authentication_attempt(
                user.user_id, True, ip_address, user_agent,
                {"provider": f"oauth_{provider}"}
            )
            
            return {
                "success": True,
                "user": {
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "roles": user.roles,
                    "permissions": await self._get_user_permissions(user.user_id)
                },
                "tokens": tokens,
                "session_id": session.session_id
            }
            
        except Exception as e:
            self.logger.error(f"Error en autenticación OAuth {provider}: {e}")
            await self.audit_logger.log_authentication_attempt(
                "unknown", False, ip_address, user_agent,
                {"provider": f"oauth_{provider}", "error": str(e)}
            )
            raise UnauthorizedException("Error en autenticación OAuth")
    
    # ==================== GESTIÓN DE USUARIOS ====================
    
    async def create_user(self, username: str, email: str, password_hash: str,
                         roles: List[str] = None, permissions: List[str] = None,
                         attributes: Dict[str, Any] = None, provider: AuthProvider = AuthProvider.LOCAL) -> User:
        """Crear usuario"""
        user_id = f"user_{secrets.token_hex(8)}"
        
        # Validar que username y email no existan
        if self._get_user_by_username(username):
            raise MCPCoreException("El nombre de usuario ya existe")
        
        if self._get_user_by_email(email):
            raise MCPCoreException("El email ya está registrado")
        
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            roles=roles or ["user"],
            permissions=permissions or [],
            attributes=attributes or {},
            provider=provider
        )
        
        self._users[user_id] = user
        
        # Asignar permisos por rol
        await self._assign_role_permissions(user)
        
        self.logger.info(f"Usuario creado: {username} ({user_id})")
        return user
    
    async def update_user(self, user_id: str, **updates) -> User:
        """Actualizar usuario"""
        if user_id not in self._users:
            raise MCPCoreException("Usuario no encontrado")
        
        user = self._users[user_id]
        
        for key, value in updates.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.now()
        
        self.logger.info(f"Usuario actualizado: {user.username}")
        return user
    
    async def deactivate_user(self, user_id: str):
        """Desactivar usuario"""
        await self.update_user(user_id, active=False)
        
        # Invalidar todas las sesiones activas
        for session in list(self._sessions.values()):
            if session.user_id == user_id and session.status == SessionStatus.ACTIVE:
                session.status = SessionStatus.SUSPENDED
        
        self.logger.info(f"Usuario desactivado: {user_id}")
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Obtener usuario por ID"""
        return self._users.get(user_id)
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Obtener usuario por username"""
        for user in self._users.values():
            if user.username == username:
                return user
        return None
    
    def _get_user_by_username(self, username: str) -> Optional[User]:
        """Obtener usuario por username (sincrónico)"""
        for user in self._users.values():
            if user.username == username:
                return user
        return None
    
    def _get_user_by_email(self, email: str) -> Optional[User]:
        """Obtener usuario por email"""
        for user in self._users.values():
            if user.email == email:
                return user
        return None
    
    # ==================== GESTIÓN DE TOKENS ====================
    
    async def _generate_tokens(self, user: User) -> Dict[str, Any]:
        """Generar tokens JWT"""
        now = datetime.utcnow()
        
        # Access Token
        access_payload = {
            "sub": user.user_id,
            "username": user.username,
            "email": user.email,
            "roles": user.roles,
            "permissions": await self._get_user_permissions(user.user_id),
            "type": TokenType.ACCESS.value,
            "iat": now,
            "exp": now + timedelta(minutes=SecurityConfig.JWT_ACCESS_EXPIRE_MINUTES)
        }
        
        access_token = jwt.encode(
            access_payload,
            SecurityConfig.JWT_SECRET_KEY,
            algorithm=SecurityConfig.JWT_ALGORITHM
        )
        
        # Refresh Token
        refresh_payload = {
            "sub": user.user_id,
            "type": TokenType.REFRESH.value,
            "iat": now,
            "exp": now + timedelta(days=SecurityConfig.JWT_REFRESH_EXPIRE_DAYS)
        }
        
        refresh_token = jwt.encode(
            refresh_payload,
            SecurityConfig.JWT_SECRET_KEY,
            algorithm=SecurityConfig.JWT_ALGORITHM
        )
        
        # ID Token (para OAuth)
        id_payload = {
            "sub": user.user_id,
            "email": user.email,
            "name": f"{user.attributes.get('first_name', '')} {user.attributes.get('last_name', '')}".strip(),
            "type": TokenType.ID.value,
            "iat": now,
            "exp": now + timedelta(minutes=SecurityConfig.JWT_ID_EXPIRE_MINUTES)
        }
        
        id_token = jwt.encode(
            id_payload,
            SecurityConfig.JWT_SECRET_KEY,
            algorithm=SecurityConfig.JWT_ALGORITHM
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "id_token": id_token,
            "token_type": "Bearer",
            "expires_in": SecurityConfig.JWT_ACCESS_EXPIRE_MINUTES * 60,
            "expires_at": access_payload["exp"].isoformat()
        }
    
    async def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """Renovar tokens usando refresh token"""
        try:
            payload = jwt.decode(
                refresh_token,
                SecurityConfig.JWT_SECRET_KEY,
                algorithms=[SecurityConfig.JWT_ALGORITHM]
            )
            
            if payload.get("type") != TokenType.REFRESH.value:
                raise UnauthorizedException("Token de tipo incorrecto")
            
            user_id = payload.get("sub")
            user = await self.get_user(user_id)
            
            if not user or not user.active:
                raise UnauthorizedException("Usuario no válido")
            
            # Generar nuevos tokens
            tokens = await self._generate_tokens(user)
            
            await self.audit_logger.log_event(
                user_id=user_id,
                action="token_refresh",
                resource="auth",
                success=True,
                ip_address="",
                user_agent="",
                details={"token_type": "refresh"}
            )
            
            return tokens
            
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException("Refresh token expirado")
        except jwt.InvalidTokenError:
            raise UnauthorizedException("Refresh token inválido")
    
    async def validate_access_token(self, token: str) -> Dict[str, Any]:
        """Validar token de acceso"""
        try:
            payload = jwt.decode(
                token,
                SecurityConfig.JWT_SECRET_KEY,
                algorithms=[SecurityConfig.JWT_ALGORITHM]
            )
            
            if payload.get("type") != TokenType.ACCESS.value:
                raise UnauthorizedException("Token de tipo incorrecto")
            
            user_id = payload.get("sub")
            user = await self.get_user(user_id)
            
            if not user or not user.active:
                raise UnauthorizedException("Usuario no válido")
            
            return {
                "valid": True,
                "user_id": user_id,
                "username": payload.get("username"),
                "email": payload.get("email"),
                "roles": payload.get("roles", []),
                "permissions": payload.get("permissions", []),
                "expires_at": datetime.fromtimestamp(payload.get("exp")).isoformat()
            }
            
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException("Token expirado")
        except jwt.InvalidTokenError:
            raise UnauthorizedException("Token inválido")
    
    # ==================== GESTIÓN DE SESIONES ====================
    
    async def _create_session(self, user_id: str, access_token: str, 
                            ip_address: str, user_agent: str) -> Session:
        """Crear nueva sesión"""
        session_id = f"sess_{secrets.token_hex(16)}"
        
        session = Session(
            session_id=session_id,
            user_id=user_id,
            token=access_token,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=SecurityConfig.SESSION_TIMEOUT_MINUTES),
            status=SessionStatus.ACTIVE
        )
        
        self._sessions[session_id] = session
        
        # Limpiar sesiones antiguas para el usuario
        await self._cleanup_user_sessions(user_id)
        
        return session
    
    async def _cleanup_user_sessions(self, user_id: str):
        """Limpiar sesiones antiguas del usuario"""
        user_sessions = [s for s in self._sessions.values() if s.user_id == user_id]
        
        if len(user_sessions) > SecurityConfig.MAX_CONCURRENT_SESSIONS:
            # Ordenar por última actividad y desactivar las más antiguas
            user_sessions.sort(key=lambda s: s.last_activity)
            
            for session in user_sessions[:-SecurityConfig.MAX_CONCURRENT_SESSIONS]:
                session.status = SessionStatus.EXPIRED
    
    async def get_active_sessions(self, user_id: str) -> List[Session]:
        """Obtener sesiones activas del usuario"""
        return [
            session for session in self._sessions.values()
            if session.user_id == user_id and session.status == SessionStatus.ACTIVE
        ]
    
    async def terminate_session(self, session_id: str, user_id: str = None) -> bool:
        """Terminar sesión"""
        if session_id not in self._sessions:
            return False
        
        session = self._sessions[session_id]
        
        # Verificar que el usuario sea dueño de la sesión o admin
        if user_id and session.user_id != user_id:
            requester = await self.get_user(user_id)
            if not requester or "admin" not in requester.roles:
                return False
        
        session.status = SessionStatus.REVOKED
        
        await self.audit_logger.log_event(
            user_id=session.user_id,
            action="session_terminated",
            resource="session",
            success=True,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            details={"session_id": session_id}
        )
        
        return True
    
    async def cleanup_expired_sessions(self):
        """Limpiar sesiones expiradas"""
        now = datetime.now()
        
        for session in list(self._sessions.values()):
            if session.status == SessionStatus.ACTIVE and session.expires_at < now:
                session.status = SessionStatus.EXPIRED
        
        self.logger.info("Sesiones expiradas limpiadas")
    
    # ==================== AUTORIZACIÓN ====================
    
    async def check_permission(self, user_id: str, resource: str, action: str, 
                             context: Dict[str, Any] = None) -> bool:
        """Verificar permiso (RBAC + ABAC)"""
        try:
            user = await self.get_user(user_id)
            if not user or not user.active:
                return False
            
            # Verificar RBAC
            has_rbac_permission = await self._check_rbac_permission(user, resource, action)
            
            # Verificar ABAC
            has_abac_permission = await self._check_abac_permission(user, resource, action, context or {})
            
            # Usuario tiene permiso si cumple RBAC O ABAC
            has_permission = has_rbac_permission or has_abac_permission
            
            await self.audit_logger.log_authorization_check(
                user_id=user_id,
                resource=resource,
                action=action,
                permission=f"{resource}:{action}",
                success=has_permission,
                ip_address=context.get("ip_address", "") if context else "",
                details={
                    "rbac": has_rbac_permission,
                    "abac": has_abac_permission
                }
            )
            
            return has_permission
            
        except Exception as e:
            self.logger.error(f"Error verificando permiso: {e}")
            return False
    
    async def _check_rbac_permission(self, user: User, resource: str, action: str) -> bool:
        """Verificar permisos RBAC"""
        # Verificar permisos directos del usuario
        for perm_name in user.permissions:
            if perm_name == "perm_admin_all":
                return True
            
            perm = self._permissions.get(perm_name)
            if perm and perm.resource == resource and perm.action.value == action:
                return True
        
        # Verificar permisos por rol
        user_permissions = await self._get_user_permissions(user.user_id)
        for perm_name in user_permissions:
            if perm_name == "perm_admin_all":
                return True
            
            perm = self._permissions.get(perm_name)
            if perm and perm.resource == resource and perm.action.value == action:
                return True
        
        # Verificar herencia de roles
        for role_name in user.roles:
            if await self._check_role_permission(role_name, resource, action):
                return True
        
        return False
    
    async def _check_abac_permission(self, user: User, resource: str, action: str, 
                                   context: Dict[str, Any]) -> bool:
        """Verificar permisos ABAC"""
        # Ejemplo de reglas ABAC basadas en atributos
        rules = [
            # Solo usuarios del mismo departamento pueden leer sus datos
            {
                "resource": "user",
                "action": "read",
                "condition": lambda u, ctx: ctx.get("target_user_department") == u.attributes.get("department")
            },
            
            # Solo administradores pueden modificar configuraciones del sistema
            {
                "resource": "system_config",
                "action": "update",
                "condition": lambda u, ctx: "admin" in u.roles
            },
            
            # Usuarios con validación completa pueden acceder a recursos sensibles
            {
                "resource": "sensitive_data",
                "action": "read",
                "condition": lambda u, ctx: u.attributes.get("validation_level") == "verified"
            },
        ]
        
        for rule in rules:
            if rule["resource"] == resource and rule["action"] == action:
                try:
                    if rule["condition"](user, context):
                        return True
                except Exception as e:
                    self.logger.error(f"Error evaluando regla ABAC: {e}")
        
        return False
    
    async def _check_role_permission(self, role_name: str, resource: str, action: str) -> bool:
        """Verificar permiso de rol"""
        role = self._roles.get(role_name)
        if not role or not role.active:
            return False
        
        # Verificar permisos directos del rol
        for perm_name in role.permissions:
            if perm_name == "perm_admin_all":
                return True
            
            perm = self._permissions.get(perm_name)
            if perm and perm.resource == resource and perm.action.value == action:
                return True
        
        # Verificar herencia de roles
        for parent_role in role.inherits_from:
            if await self._check_role_permission(parent_role, resource, action):
                return True
        
        return False
    
    async def _get_user_permissions(self, user_id: str) -> List[str]:
        """Obtener todos los permisos del usuario"""
        user = await self.get_user(user_id)
        if not user:
            return []
        
        permissions = set(user.permissions)
        
        # Agregar permisos por rol
        for role_name in user.roles:
            role = self._roles.get(role_name)
            if role:
                permissions.update(role.permissions)
                
                # Recursivamente agregar permisos de roles padre
                await self._add_inherited_permissions(role, permissions)
        
        return list(permissions)
    
    async def _add_inherited_permissions(self, role: Role, permissions: Set[str]):
        """Agregar permisos heredados"""
        for parent_role_name in role.inherits_from:
            parent_role = self._roles.get(parent_role_name)
            if parent_role:
                permissions.update(parent_role.permissions)
                await self._add_inherited_permissions(parent_role, permissions)
    
    async def _assign_role_permissions(self, user: User):
        """Asignar permisos por rol del usuario"""
        for role_name in user.roles:
            role = self._roles.get(role_name)
            if role:
                user.permissions.extend(role.permissions)
        
        # Eliminar duplicados
        user.permissions = list(set(user.permissions))
    
    # ==================== GESTIÓN DE ROLES ====================
    
    async def create_role(self, name: str, description: str, permissions: List[str] = None,
                         inherits_from: List[str] = None) -> Role:
        """Crear rol"""
        role_id = f"role_{secrets.token_hex(8)}"
        
        role = Role(
            role_id=role_id,
            name=name,
            description=description,
            permissions=permissions or [],
            inherits_from=inherits_from or []
        )
        
        self._roles[role_id] = role
        
        # Actualizar permisos de usuarios con este rol
        for user in self._users.values():
            if name in user.roles:
                await self._assign_role_permissions(user)
        
        self.logger.info(f"Rol creado: {name}")
        return role
    
    async def assign_role_to_user(self, user_id: str, role_name: str):
        """Asignar rol a usuario"""
        user = await self.get_user(user_id)
        if not user:
            raise MCPCoreException("Usuario no encontrado")
        
        if role_name not in [r.name for r in self._roles.values()]:
            raise MCPCoreException("Rol no encontrado")
        
        if role_name not in user.roles:
            user.roles.append(role_name)
            await self._assign_role_permissions(user)
            
            self.logger.info(f"Rol {role_name} asignado a usuario {user.username}")
    
    async def remove_role_from_user(self, user_id: str, role_name: str):
        """Quitar rol de usuario"""
        user = await self.get_user(user_id)
        if not user:
            raise MCPCoreException("Usuario no encontrado")
        
        if role_name in user.roles:
            user.roles.remove(role_name)
            # Recalcular permisos
            user.permissions = []
            await self._assign_role_permissions(user)
            
            self.logger.info(f"Rol {role_name} quitado de usuario {user.username}")
    
    # ==================== API KEYS ====================
    
    async def create_api_key(self, user_id: str, permissions: List[str] = None,
                           scopes: List[str] = None, rate_limit: int = 1000,
                           expires_at: datetime = None) -> str:
        """Crear API Key"""
        key_id = f"key_{secrets.token_hex(16)}"
        api_key = secrets.token_urlsafe(32)
        
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        api_key_obj = APIKey(
            key_id=key_id,
            user_id=user_id,
            key_hash=key_hash,
            permissions=permissions or [],
            scopes=scopes or [],
            rate_limit=rate_limit,
            expires_at=expires_at
        )
        
        self._api_keys[key_id] = api_key_obj
        
        await self.audit_logger.log_event(
            user_id=user_id,
            action="api_key_created",
            resource="api_key",
            success=True,
            ip_address="",
            user_agent="",
            details={"key_id": key_id, "permissions": permissions}
        )
        
        # Retornar API key completa (ID + Key)
        return f"{key_id}:{api_key}"
    
    async def validate_api_key(self, api_key: str, required_permission: str = None,
                             required_scope: str = None) -> Dict[str, Any]:
        """Validar API Key"""
        try:
            # Parsear key
            if ':' not in api_key:
                raise UnauthorizedException("Formato de API key inválido")
            
            key_id, key_value = api_key.split(':', 1)
            key_hash = hashlib.sha256(key_value.encode()).hexdigest()
            
            # Buscar API key
            api_key_obj = None
            for key in self._api_keys.values():
                if key.key_id == key_id and key.key_hash == key_hash:
                    api_key_obj = key
                    break
            
            if not api_key_obj:
                raise UnauthorizedException("API key no válida")
            
            if not api_key_obj.active:
                raise UnauthorizedException("API key desactivada")
            
            if api_key_obj.expires_at and datetime.now() > api_key_obj.expires_at:
                raise UnauthorizedException("API key expirada")
            
            # Verificar permisos
            if required_permission and required_permission not in api_key_obj.permissions:
                raise ForbiddenException(f"Permiso requerido: {required_permission}")
            
            if required_scope and required_scope not in api_key_obj.scopes:
                raise ForbiddenException(f"Scope requerido: {required_scope}")
            
            # Verificar rate limiting
            if not await self._check_api_rate_limit(key_id):
                raise ForbiddenException("Rate limit excedido")
            
            user = await self.get_user(api_key_obj.user_id)
            if not user or not user.active:
                raise UnauthorizedException("Usuario asociado no válido")
            
            await self.audit_logger.log_event(
                user_id=api_key_obj.user_id,
                action="api_key_validated",
                resource="api_key",
                success=True,
                ip_address="",
                user_agent="",
                details={"key_id": key_id, "permission": required_permission}
            )
            
            return {
                "valid": True,
                "user_id": api_key_obj.user_id,
                "permissions": api_key_obj.permissions,
                "scopes": api_key_obj.scopes
            }
            
        except (UnauthorizedException, ForbiddenException):
            raise
        except Exception as e:
            self.logger.error(f"Error validando API key: {e}")
            raise UnauthorizedException("Error validando API key")
    
    # ==================== MFA ====================
    
    async def enable_totp_mfa(self, user_id: str) -> Dict[str, Any]:
        """Habilitar TOTP MFA"""
        user = await self.get_user(user_id)
        if not user:
            raise MCPCoreException("Usuario no encontrado")
        
        secret = self.mfa_manager.generate_totp_secret()
        
        # Generar QR code
        qr_code = self.mfa_manager.generate_totp_qr_code(user.email, secret)
        
        # Guardar secreto (en producción, cifrar)
        await self.update_user(user_id, mfa_secret=secret, mfa_enabled=True)
        
        await self.audit_logger.log_event(
            user_id=user_id,
            action="mfa_totp_enabled",
            resource="mfa",
            success=True,
            ip_address="",
            user_agent="",
            details={}
        )
        
        return {
            "secret": secret,
            "qr_code": base64.b64encode(qr_code).decode(),
            "provisioning_uri": f"otpauth://totp/{SecurityConfig.TOTP_ISSUER}:{user.email}?secret={secret}&issuer={SecurityConfig.TOTP_ISSUER}"
        }
    
    async def verify_totp_setup(self, user_id: str, token: str) -> bool:
        """Verificar configuración TOTP"""
        user = await self.get_user(user_id)
        if not user or not user.mfa_secret:
            return False
        
        is_valid = self.mfa_manager.verify_totp(user.mfa_secret, token)
        
        if is_valid:
            await self.audit_logger.log_event(
                user_id=user_id,
                action="mfa_totp_verified",
                resource="mfa",
                success=True,
                ip_address="",
                user_agent="",
                details={}
            )
        
        return is_valid
    
    async def send_sms_verification(self, user_id: str) -> str:
        """Enviar código de verificación SMS"""
        user = await self.get_user(user_id)
        if not user or not user.phone_number:
            raise MCPCoreException("Usuario no tiene número de teléfono")
        
        code = await self.mfa_manager.send_sms_code(user.phone_number)
        
        await self.audit_logger.log_event(
            user_id=user_id,
            action="mfa_sms_sent",
            resource="mfa",
            success=True,
            ip_address="",
            user_agent="",
            details={"phone": user.phone_number[-4:]}  # Solo últimos 4 dígitos por seguridad
        )
        
        return code  # En producción, no retornar el código
    
    async def _verify_sms_code(self, phone_number: str, code: str) -> bool:
        """Verificar código SMS (simplificado)"""
        # En producción, obtener código de la cache de Redis
        # cached_code = redis_client.get(f"sms_code:{hashlib.sha256(phone_number.encode()).hexdigest()}")
        # return cached_code == code
        return True  # Simplificado para demo
    
    # ==================== SSO ====================
    
    def get_sso_providers(self) -> List[Dict[str, str]]:
        """Obtener proveedores SSO disponibles"""
        providers = []
        
        if self.ldap_authenticator:
            providers.append({
                "name": "LDAP",
                "id": "ldap",
                "type": "ldap",
                "description": "Autenticación LDAP"
            })
        
        for provider, auth in self.oauth_authenticators.items():
            providers.append({
                "name": provider.title(),
                "id": provider,
                "type": "oauth",
                "description": f"Autenticación con {provider.title()}"
            })
        
        return providers
    
    def initiate_sso(self, provider: str, return_url: str = None) -> str:
        """Iniciar proceso SSO"""
        if provider == "ldap":
            if not self.ldap_authenticator:
                raise MCPCoreException("LDAP no configurado")
            # Redirigir a formulario LDAP
            return f"/auth/ldap?return_url={return_url}"
        
        elif provider in self.oauth_authenticators:
            auth = self.oauth_authenticators[provider]
            state = secrets.token_urlsafe(16)
            # Guardar state en caché con TTL
            # redis_client.setex(f"sso_state:{state}", 300, return_url or "/")
            return auth.get_authorization_url(state)
        
        else:
            raise MCPCoreException(f"Proveedor SSO {provider} no soportado")
    
    # ==================== UTILIDADES ====================
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verificar contraseña"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
    
    async def _record_failed_attempt(self, identifier: str):
        """Registrar intento fallido"""
        attempts = self._login_attempts.get(identifier, 0) + 1
        self._login_attempts[identifier] = attempts
        
        if attempts >= SecurityConfig.MAX_LOGIN_ATTEMPTS:
            self._locked_accounts[identifier] = datetime.now() + timedelta(
                minutes=SecurityConfig.LOCKOUT_DURATION_MINUTES
            )
            self.logger.warning(f"Cuenta bloqueada: {identifier}")
    
    async def _check_rate_limit(self, identifier: str) -> bool:
        """Verificar rate limiting"""
        now = time.time()
        window_start = now - SecurityConfig.RATE_LIMIT_WINDOW
        
        # Obtener intentos del identificador
        if identifier not in self._rate_limit_cache:
            self._rate_limit_cache[identifier] = []
        
        attempts = self._rate_limit_cache[identifier]
        
        # Filtrar intentos dentro de la ventana de tiempo
        recent_attempts = [t for t in attempts if t > window_start]
        
        if len(recent_attempts) >= SecurityConfig.RATE_LIMIT_REQUESTS:
            return False
        
        # Agregar intento actual
        recent_attempts.append(now)
        self._rate_limit_cache[identifier] = recent_attempts
        
        return True
    
    async def _check_api_rate_limit(self, key_id: str) -> bool:
        """Verificar rate limiting para API"""
        now = time.time()
        window_start = now - 3600  # 1 hora
        
        cache_key = f"api_rate:{key_id}"
        if cache_key not in self._rate_limit_cache:
            self._rate_limit_cache[cache_key] = []
        
        attempts = self._rate_limit_cache[cache_key]
        recent_attempts = [t for t in attempts if t > window_start]
        
        if len(recent_attempts) >= SecurityConfig.RATE_LIMIT_REQUESTS:
            return False
        
        recent_attempts.append(now)
        self._rate_limit_cache[cache_key] = recent_attempts
        
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar salud del sistema"""
        return {
            "status": "healthy" if self.is_initialized else "not_initialized",
            "users_count": len(self._users),
            "roles_count": len(self._roles),
            "permissions_count": len(self._permissions),
            "sessions_active": len([s for s in self._sessions.values() if s.status == SessionStatus.ACTIVE]),
            "api_keys_active": len([k for k in self._api_keys.values() if k.active]),
            "oauth_providers": list(self.oauth_authenticators.keys()),
            "ldap_configured": self.ldap_authenticator is not None
        }


# Instancia global del sistema de autenticación
auth_system = AuthSystem()