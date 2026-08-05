"""
Security Module - MCP Core Superior
Sistema integral de seguridad con scanning, data redaction, authentication & authorization,
y protección DDoS avanzada

Funcionalidades:
- PII detection y redaction
- Code security scanning
- Input validation
- SQL injection prevention
- XSS protection
- Path traversal protection
- File upload security
- API rate limiting
- Security headers
- Vulnerability scanning
- Authentication & Authorization layer (JWT, OAuth 2.0, MFA, RBAC, ABAC, SSO)
- Sistema de Rate Limiting y Protección DDoS avanzado
"""

from .security_system import (
    SecuritySystem,
    PIIDetector,
    SecurityScanner,
    InputValidator,
    RateLimiter,
    SecurityHeaders,
    ComplianceManager,
    VulnerabilityScanner
)

from .auth_system import (
    AuthSystem,
    auth_system,
    User,
    Role,
    Permission,
    Session,
    APIKey,
    AuditLog,
    TokenType,
    AuthProvider,
    PermissionType,
    SessionStatus,
    SecurityConfig,
    LDAPAuthenticator,
    OAuthAuthenticator,
    MFAManager,
    AuditLogger
)

# Sistema de Rate Limiting y Protección DDoS
from .ddos_protection import (
    DDoSProtectionSystem,
    RateLimiter as DDOSRateLimiter,
    TokenBucket,
    SlidingWindow,
    ThreatDetector,
    GeographicBlocker,
    WAFIntegrator,
    ThreatLevel,
    ThreatEvent,
    GeographicRule,
    RateLimitConfig,
    RateLimitScope,
    ddos_protect
)

# Configuración y utilidades
from .ddos_config import (
    DEFAULT_DDOS_CONFIG,
    get_config_for_environment,
    load_config_from_file
)

from .ddos_middleware import (
    DDoSMiddleware,
    FlaskDDoSMiddleware,
    ASGIDDoSMiddleware,
    create_ddos_middleware
)

from .ddos_utils import (
    DDoSAdminTools,
    DDoSBulkOperations,
    DDoSMonitoring,
    ThreatReport,
    create_ddos_admin_interface
)

__all__ = [
    # Security system
    'SecuritySystem',
    'PIIDetector', 
    'SecurityScanner',
    'InputValidator',
    'RateLimiter',
    'SecurityHeaders',
    'ComplianceManager',
    'VulnerabilityScanner',
    
    # Auth & Authorization system
    'AuthSystem',
    'auth_system',
    'User',
    'Role', 
    'Permission',
    'Session',
    'APIKey',
    'AuditLog',
    'TokenType',
    'AuthProvider',
    'PermissionType',
    'SessionStatus',
    'SecurityConfig',
    'LDAPAuthenticator',
    'OAuthAuthenticator',
    'MFAManager',
    'AuditLogger',
    
    # DDoS Protection System
    'DDoSProtectionSystem',
    'DDOSRateLimiter',
    'TokenBucket',
    'SlidingWindow', 
    'ThreatDetector',
    'GeographicBlocker',
    'WAFIntegrator',
    'ThreatLevel',
    'ThreatEvent',
    'GeographicRule',
    'RateLimitConfig',
    'RateLimitScope',
    'ddos_protect',
    
    # Configuration
    'DEFAULT_DDOS_CONFIG',
    'get_config_for_environment',
    'load_config_from_file',
    
    # Middleware
    'DDoSMiddleware',
    'FlaskDDoSMiddleware', 
    'ASGIDDoSMiddleware',
    'create_ddos_middleware',
    
    # Administrative Tools
    'DDoSAdminTools',
    'DDoSBulkOperations',
    'DDoSMonitoring',
    'ThreatReport',
    'create_ddos_admin_interface'
]

__version__ = '2.0.0'