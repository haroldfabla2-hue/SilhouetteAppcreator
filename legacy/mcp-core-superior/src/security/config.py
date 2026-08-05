"""
Configuración del sistema de Authentication & Authorization
Incluye configuración para LDAP, OAuth, MFA, y servicios externos
"""

import os
from typing import Dict, Any, Optional
from pydantic import BaseSettings, Field
from enum import Enum


class AuthProvider(Enum):
    """Proveedores de autenticación soportados"""
    LOCAL = "local"
    LDAP = "ldap"
    ACTIVE_DIRECTORY = "active_directory"
    OAUTH_GOOGLE = "google"
    OAUTH_GITHUB = "github"
    OAUTH_MICROSOFT = "microsoft"
    OAUTH_AZURE_AD = "azure_ad"


class SecuritySettings(BaseSettings):
    """Configuración de seguridad"""
    
    # JWT Configuration
    JWT_SECRET_KEY: str = Field(default="", env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_EXPIRE_MINUTES: int = Field(default=15, env="JWT_ACCESS_EXPIRE_MINUTES")
    JWT_REFRESH_EXPIRE_DAYS: int = Field(default=30, env="JWT_REFRESH_EXPIRE_DAYS")
    JWT_ID_EXPIRE_MINUTES: int = Field(default=5, env="JWT_ID_EXPIRE_MINUTES")
    
    # Password Policy
    MIN_PASSWORD_LENGTH: int = Field(default=8, env="MIN_PASSWORD_LENGTH")
    REQUIRE_PASSWORD_COMPLEXITY: bool = Field(default=True, env="REQUIRE_PASSWORD_COMPLEXITY")
    PASSWORD_HISTORY_COUNT: int = Field(default=5, env="PASSWORD_HISTORY_COUNT")
    PASSWORD_EXPIRE_DAYS: int = Field(default=90, env="PASSWORD_EXPIRE_DAYS")
    
    # Session Configuration
    SESSION_TIMEOUT_MINUTES: int = Field(default=30, env="SESSION_TIMEOUT_MINUTES")
    MAX_CONCURRENT_SESSIONS: int = Field(default=5, env="MAX_CONCURRENT_SESSIONS")
    SESSION_CLEANUP_INTERVAL_HOURS: int = Field(default=1, env="SESSION_CLEANUP_INTERVAL_HOURS")
    
    # MFA Configuration
    MFA_ENABLED: bool = Field(default=True, env="MFA_ENABLED")
    MFA_ENCRYPTION_KEY: str = Field(default="", env="MFA_ENCRYPTION_KEY")
    TOTP_ISSUER: str = Field(default="mcp-core-superior", env="TOTP_ISSUER")
    
    # SMS Configuration
    SMS_PROVIDER: str = Field(default="twilio", env="SMS_PROVIDER")
    TWILIO_ACCOUNT_SID: str = Field(default="", env="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = Field(default="", env="TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: str = Field(default="", env="TWILIO_PHONE_NUMBER")
    
    # AWS SNS Configuration
    AWS_REGION: str = Field(default="us-east-1", env="AWS_REGION")
    AWS_ACCESS_KEY_ID: str = Field(default="", env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field(default="", env="AWS_SECRET_ACCESS_KEY")
    AWS_SNS_TOPIC_ARN: str = Field(default="", env="AWS_SNS_TOPIC_ARN")
    
    # Email Configuration
    SMTP_SERVER: str = Field(default="", env="SMTP_SERVER")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: str = Field(default="", env="SMTP_USERNAME")
    SMTP_PASSWORD: str = Field(default="", env="SMTP_PASSWORD")
    SMTP_USE_TLS: bool = Field(default=True, env="SMTP_USE_TLS")
    EMAIL_FROM: str = Field(default="", env="EMAIL_FROM")
    
    # LDAP Configuration
    LDAP_ENABLED: bool = Field(default=False, env="LDAP_ENABLED")
    LDAP_SERVER: str = Field(default="", env="LDAP_SERVER")
    LDAP_PORT: int = Field(default=389, env="LDAP_PORT")
    LDAP_DOMAIN: str = Field(default="", env="LDAP_DOMAIN")
    LDAP_SEARCH_BASE: str = Field(default="", env="LDAP_SEARCH_BASE")
    LDAP_USE_SSL: bool = Field(default=False, env="LDAP_USE_SSL")
    LDAP_BIND_USER: str = Field(default="", env="LDAP_BIND_USER")
    LDAP_BIND_PASSWORD: str = Field(default="", env="LDAP_BIND_PASSWORD")
    
    # Active Directory Configuration
    AD_ENABLED: bool = Field(default=False, env="AD_ENABLED")
    AD_SERVER: str = Field(default="", env="AD_SERVER")
    AD_DOMAIN: str = Field(default="", env="AD_DOMAIN")
    AD_SEARCH_BASE: str = Field(default="", env="AD_SEARCH_BASE")
    AD_GROUP_ATTRIBUTE: str = Field(default="memberOf", env="AD_GROUP_ATTRIBUTE")
    
    # OAuth Configuration
    OAUTH_ENABLED: bool = Field(default=False, env="OAUTH_ENABLED")
    OAUTH_REDIRECT_URI: str = Field(default="http://localhost:8000/auth/callback", env="OAUTH_REDIRECT_URI")
    OAUTH_SCOPES: str = Field(default="openid email profile", env="OAUTH_SCOPES")
    
    # Google OAuth
    GOOGLE_OAUTH_ENABLED: bool = Field(default=False, env="GOOGLE_OAUTH_ENABLED")
    GOOGLE_CLIENT_ID: str = Field(default="", env="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = Field(default="", env="GOOGLE_CLIENT_SECRET")
    
    # GitHub OAuth
    GITHUB_OAUTH_ENABLED: bool = Field(default=False, env="GITHUB_OAUTH_ENABLED")
    GITHUB_CLIENT_ID: str = Field(default="", env="GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET: str = Field(default="", env="GITHUB_CLIENT_SECRET")
    
    # Microsoft OAuth
    MICROSOFT_OAUTH_ENABLED: bool = Field(default=False, env="MICROSOFT_OAUTH_ENABLED")
    MICROSOFT_CLIENT_ID: str = Field(default="", env="MICROSOFT_CLIENT_ID")
    MICROSOFT_CLIENT_SECRET: str = Field(default="", env="MICROSOFT_CLIENT_SECRET")
    MICROSOFT_TENANT_ID: str = Field(default="common", env="MICROSOFT_TENANT_ID")
    
    # Azure AD OAuth
    AZURE_AD_ENABLED: bool = Field(default=False, env="AZURE_AD_ENABLED")
    AZURE_AD_CLIENT_ID: str = Field(default="", env="AZURE_AD_CLIENT_ID")
    AZURE_AD_CLIENT_SECRET: str = Field(default="", env="AZURE_AD_CLIENT_SECRET")
    AZURE_AD_TENANT_ID: str = Field(default="", env="AZURE_AD_TENANT_ID")
    
    # Rate Limiting
    RATE_LIMITING_ENABLED: bool = Field(default=True, env="RATE_LIMITING_ENABLED")
    MAX_LOGIN_ATTEMPTS: int = Field(default=5, env="MAX_LOGIN_ATTEMPTS")
    LOCKOUT_DURATION_MINUTES: int = Field(default=15, env="LOCKOUT_DURATION_MINUTES")
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=3600, env="RATE_LIMIT_WINDOW")
    
    # Redis Configuration (para caching y sesiones)
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    REDIS_PASSWORD: str = Field(default="", env="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    
    # Database Configuration (para auditoría)
    DATABASE_URL: str = Field(default="sqlite:///./auth.db", env="DATABASE_URL")
    
    # Audit Logging
    AUDIT_LOGGING_ENABLED: bool = Field(default=True, env="AUDIT_LOGGING_ENABLED")
    AUDIT_LOG_FILE: str = Field(default="./logs/audit.log", env="AUDIT_LOG_FILE")
    AUDIT_LOG_LEVEL: str = Field(default="INFO", env="AUDIT_LOG_LEVEL")
    
    # Security Headers
    SECURE_HEADERS_ENABLED: bool = Field(default=True, env="SECURE_HEADERS_ENABLED")
    CORS_ALLOWED_ORIGINS: str = Field(default="*", env="CORS_ALLOWED_ORIGINS")
    CORS_ALLOWED_METHODS: str = Field(default="GET,POST,PUT,DELETE,OPTIONS", env="CORS_ALLOWED_METHODS")
    CORS_ALLOWED_HEADERS: str = Field(default="*", env="CORS_ALLOWED_HEADERS")
    
    # API Configuration
    API_KEY_ENABLED: bool = Field(default=True, env="API_KEY_ENABLED")
    API_KEY_EXPIRE_DAYS: int = Field(default=365, env="API_KEY_EXPIRE_DAYS")
    API_KEY_RATE_LIMIT: int = Field(default=1000, env="API_KEY_RATE_LIMIT")
    
    # SSO Configuration
    SSO_ENABLED: bool = Field(default=True, env="SSO_ENABLED")
    SSO_SESSION_TIMEOUT: int = Field(default=1440, env="SSO_SESSION_TIMEOUT")  # 24 hours
    
    # Cryptography
    ENCRYPTION_KEY: str = Field(default="", env="ENCRYPTION_KEY")
    HASH_ALGORITHM: str = Field(default="sha256", env="HASH_ALGORITHM")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class OAuthProviderConfig:
    """Configuración de proveedores OAuth"""
    
    @staticmethod
    def get_google_config() -> Dict[str, Any]:
        """Configuración para Google OAuth"""
        return {
            "enabled": settings.GOOGLE_OAUTH_ENABLED,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_url": "https://accounts.google.com/o/oauth2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
            "scope": "openid email profile"
        }
    
    @staticmethod
    def get_github_config() -> Dict[str, Any]:
        """Configuración para GitHub OAuth"""
        return {
            "enabled": settings.GITHUB_OAUTH_ENABLED,
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "auth_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "userinfo_url": "https://api.github.com/user",
            "scope": "read:user user:email"
        }
    
    @staticmethod
    def get_microsoft_config() -> Dict[str, Any]:
        """Configuración para Microsoft OAuth"""
        return {
            "enabled": settings.MICROSOFT_OAUTH_ENABLED,
            "client_id": settings.MICROSOFT_CLIENT_ID,
            "client_secret": settings.MICROSOFT_CLIENT_SECRET,
            "tenant_id": settings.MICROSOFT_TENANT_ID,
            "auth_url": f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize",
            "token_url": f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/token",
            "userinfo_url": "https://graph.microsoft.com/v1.0/me",
            "scope": "openid email profile"
        }
    
    @staticmethod
    def get_azure_ad_config() -> Dict[str, Any]:
        """Configuración para Azure AD OAuth"""
        return {
            "enabled": settings.AZURE_AD_ENABLED,
            "client_id": settings.AZURE_AD_CLIENT_ID,
            "client_secret": settings.AZURE_AD_CLIENT_SECRET,
            "tenant_id": settings.AZURE_AD_TENANT_ID,
            "auth_url": f"https://login.microsoftonline.com/{settings.AZURE_AD_TENANT_ID}/oauth2/v2.0/authorize",
            "token_url": f"https://login.microsoftonline.com/{settings.AZURE_AD_TENANT_ID}/oauth2/v2.0/token",
            "userinfo_url": "https://graph.microsoft.com/v1.0/me",
            "scope": "openid email profile"
        }


class LDAPConfig:
    """Configuración LDAP"""
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Configuración LDAP/Active Directory"""
        return {
            "enabled": settings.LDAP_ENABLED or settings.AD_ENABLED,
            "ldap": {
                "server": settings.LDAP_SERVER,
                "port": settings.LDAP_PORT,
                "domain": settings.LDAP_DOMAIN,
                "search_base": settings.LDAP_SEARCH_BASE,
                "use_ssl": settings.LDAP_USE_SSL,
                "bind_user": settings.LDAP_BIND_USER,
                "bind_password": settings.LDAP_BIND_PASSWORD
            },
            "active_directory": {
                "server": settings.AD_SERVER,
                "domain": settings.AD_DOMAIN,
                "search_base": settings.AD_SEARCH_BASE,
                "group_attribute": settings.AD_GROUP_ATTRIBUTE
            }
        }


class DatabaseConfig:
    """Configuración de base de datos"""
    
    @staticmethod
    def get_connection_string() -> str:
        """Obtener string de conexión a BD"""
        return settings.DATABASE_URL
    
    @staticmethod
    def get_audit_tables() -> Dict[str, str]:
        """Definir tablas para auditoría"""
        return {
            "users": "CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT UNIQUE, email TEXT UNIQUE, password_hash TEXT, roles TEXT, permissions TEXT, attributes TEXT, mfa_enabled BOOLEAN, mfa_secret TEXT, provider TEXT, active BOOLEAN, created_at TIMESTAMP, updated_at TIMESTAMP)",
            "roles": "CREATE TABLE roles (id TEXT PRIMARY KEY, name TEXT UNIQUE, description TEXT, permissions TEXT, parent_roles TEXT, inherits_from TEXT, active BOOLEAN)",
            "permissions": "CREATE TABLE permissions (id TEXT PRIMARY KEY, name TEXT UNIQUE, resource TEXT, action TEXT, conditions TEXT, inherited BOOLEAN)",
            "sessions": "CREATE TABLE sessions (id TEXT PRIMARY KEY, user_id TEXT, token TEXT, ip_address TEXT, user_agent TEXT, created_at TIMESTAMP, last_activity TIMESTAMP, expires_at TIMESTAMP, status TEXT, mfa_verified BOOLEAN)",
            "api_keys": "CREATE TABLE api_keys (id TEXT PRIMARY KEY, user_id TEXT, key_hash TEXT, permissions TEXT, scopes TEXT, rate_limit INTEGER, expires_at TIMESTAMP, active BOOLEAN, created_at TIMESTAMP)",
            "audit_logs": "CREATE TABLE audit_logs (id TEXT PRIMARY KEY, user_id TEXT, action TEXT, resource TEXT, success BOOLEAN, ip_address TEXT, user_agent TEXT, timestamp TIMESTAMP, details TEXT)"
        }


# Crear instancia global de configuración
settings = SecuritySettings()