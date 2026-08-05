# Security Guide - Best Practices

## Overview

La seguridad es una prioridad crítica en MCP Core Superior. Esta guía cubre todos los aspectos de seguridad desde la arquitectura hasta la implementación, incluyendo configuraciones recomendadas, mejores prácticas y consideraciones específicas para entornos de producción.

## 🏛️ Security Architecture

### Security-by-Design Principles

1. **Defense in Depth**: Múltiples capas de seguridad
2. **Zero Trust**: Verificar siempre, confiar nunca
3. **Least Privilege**: Permisos mínimos necesarios
4. **Fail Secure**: Fallos deben ser seguros por defecto
5. **Secure by Default**: Configuraciones seguras por defecto

### Security Layers

```
┌─────────────────────────────────────────────────────────┐
│                    External Security Layer               │
├─────────────────────────────────────────────────────────┤
│ • WAF (Web Application Firewall)                        │
│ • DDoS Protection                                       │
│ • Rate Limiting                                         │
│ • IP Blacklisting                                       │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                     Network Security Layer               │
├─────────────────────────────────────────────────────────┤
│ • TLS 1.3 Encryption                                    │
│ • VPN for Internal Communication                        │
│ • Network Segmentation                                  │
│ • Firewall Rules                                        │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                    Gateway Security Layer                │
├─────────────────────────────────────────────────────────┤
│ • API Gateway Authentication                            │
│ • JWT Token Validation                                  │
│ • Request Filtering                                     │
│ • SSL Termination                                       │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   Application Security Layer             │
├─────────────────────────────────────────────────────────┤
│ • Input Validation                                      │
│ • Output Sanitization                                   │
│ • Authorization Checks                                  │
│ • Session Management                                    │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                    Data Security Layer                   │
├─────────────────────────────────────────────────────────┤
│ • Encryption at Rest                                    │
│ • Encryption in Transit                                 │
│ • Data Masking                                          │
│ • Secure Key Management                                 │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   Infrastructure Security Layer          │
├─────────────────────────────────────────────────────────┤
│ • Container Security                                    │
│ • Secret Management                                     │
│ • Access Controls                                       │
│ • Audit Logging                                         │
└─────────────────────────────────────────────────────────┘
```

## 🔐 Authentication & Authorization

### JWT Token Implementation

**Authentication Flow**
```python
# src/security/auth_service.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from pydantic import BaseModel

class AuthenticationService:
    """Servicio de autenticación con JWT tokens"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Crear token de acceso JWT"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Crear token de refresh"""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode = data.copy()
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verificar y decodificar token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verificar tipo de token
            if payload.get("type") not in ["access", "refresh"]:
                return None
            
            return payload
        except JWTError:
            return None
    
    def hash_password(self, password: str) -> str:
        """Hashear password con bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verificar password"""
        return self.pwd_context.verify(plain_password, hashed_password)
```

**Token Models**
```python
# src/security/token_models.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Token(BaseModel):
    """Modelo de token JWT"""
    access_token: str = Field(..., description="Token de acceso JWT")
    refresh_token: str = Field(..., description="Token de refresh")
    token_type: str = Field(default="bearer", description="Tipo de token")
    expires_in: int = Field(..., description="Tiempo de expiración en segundos")

class TokenPayload(BaseModel):
    """Payload del token JWT"""
    sub: str = Field(..., description="Sujeto (user_id)")
    username: Optional[str] = Field(None, description="Nombre de usuario")
    email: Optional[str] = Field(None, description="Email del usuario")
    role: str = Field(..., description="Rol del usuario")
    permissions: List[str] = Field(default_factory=list, description="Permisos específicos")
    iat: Optional[datetime] = Field(None, description="Issued at")
    exp: Optional[datetime] = Field(None, description="Expiration")
    type: str = Field(..., description="Tipo de token")

class UserCredentials(BaseModel):
    """Credenciales de usuario para login"""
    username: str = Field(..., description="Nombre de usuario")
    password: str = Field(..., description="Password")
    client_id: Optional[str] = Field(None, description="ID del cliente (para OAuth)")

class RefreshRequest(BaseModel):
    """Request para refresh de token"""
    refresh_token: str = Field(..., description="Token de refresh")
```

### API Key Management

**API Key Service**
```python
# src/security/api_key_service.py
import secrets
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

class APIKeyService:
    """Servicio de gestión de API keys"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_api_key(self, user_id: str, permissions: List[str], name: str) -> Dict[str, str]:
        """Generar nueva API key"""
        # Generar key y secret
        key = f"mcp_{secrets.token_urlsafe(32)}"
        secret = secrets.token_urlsafe(64)
        
        # Hashear secret para almacenamiento
        secret_hash = hashlib.sha256(secret.encode()).hexdigest()
        
        # Crear registro en BD
        # TODO: Implementar modelo APIKey en BD
        
        return {
            "api_key": key,
            "api_secret": secret,  # Solo mostrar una vez
            "key_id": key[:16],    # ID para tracking
            "created_at": datetime.utcnow().isoformat()
        }
    
    def validate_api_key(self, api_key: str, required_permissions: List[str] = None) -> Optional[Dict[str, Any]]:
        """Validar API key y verificar permisos"""
        if not api_key or not api_key.startswith("mcp_"):
            return None
        
        # TODO: Consultar BD para validar key y obtener permisos
        # if not api_key_record:
        #     return None
        
        # Verificar permisos si se requieren
        if required_permissions:
            # TODO: Verificar que la API key tenga los permisos necesarios
            pass
        
        return {
            "user_id": "user_123",
            "permissions": ["read", "write", "execute"],
            "rate_limit": 1000,
            "expires_at": datetime.utcnow() + timedelta(days=365)
        }
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revocar API key"""
        # TODO: Marcar API key como revocada en BD
        return True
```

### Role-Based Access Control (RBAC)

**Permission System**
```python
# src/security/rbac.py
from enum import Enum
from typing import Set, List, Dict, Any
from functools import wraps

class Permission(Enum):
    """Permisos del sistema"""
    # Herramientas MCP
    TOOL_EXECUTE = "tool:execute"
    TOOL_READ = "tool:read"
    TOOL_WRITE = "tool:write"
    
    # Agentes
    AGENT_MANAGE = "agent:manage"
    AGENT_MONITOR = "agent:monitor"
    
    # Orquestación
    ORCHESTRATE_CREATE = "orchestrate:create"
    ORCHESTRATE_VIEW = "orchestrate:view"
    ORCHESTRATE_CANCEL = "orchestrate:cancel"
    
    # Administración
    ADMIN_USERS = "admin:users"
    ADMIN_SYSTEM = "admin:system"
    ADMIN_CONFIG = "admin:config"
    
    # Base de datos
    DB_READ = "db:read"
    DB_WRITE = "db:write"
    DB_ADMIN = "db:admin"

class Role(Enum):
    """Roles del sistema"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    API_CLIENT = "api_client"

# Definición de roles y permisos
ROLE_PERMISSIONS = {
    Role.ADMIN: {
        Permission.ADMIN_USERS,
        Permission.ADMIN_SYSTEM,
        Permission.ADMIN_CONFIG,
        Permission.TOOL_EXECUTE,
        Permission.TOOL_READ,
        Permission.TOOL_WRITE,
        Permission.AGENT_MANAGE,
        Permission.AGENT_MONITOR,
        Permission.ORCHESTRATE_CREATE,
        Permission.ORCHESTRATE_VIEW,
        Permission.ORCHESTRATE_CANCEL,
        Permission.DB_READ,
        Permission.DB_WRITE,
        Permission.DB_ADMIN,
    },
    Role.USER: {
        Permission.TOOL_EXECUTE,
        Permission.TOOL_READ,
        Permission.ORCHESTRATE_CREATE,
        Permission.ORCHESTRATE_VIEW,
        Permission.AGENT_MONITOR,
        Permission.DB_READ,
    },
    Role.VIEWER: {
        Permission.TOOL_READ,
        Permission.ORCHESTRATE_VIEW,
        Permission.AGENT_MONITOR,
        Permission.DB_READ,
    },
    Role.API_CLIENT: {
        Permission.TOOL_EXECUTE,
        Permission.ORCHESTRATE_CREATE,
    }
}

class RBACService:
    """Servicio de control de acceso basado en roles"""
    
    def __init__(self):
        self.role_permissions = ROLE_PERMISSIONS
    
    def has_permission(self, user_permissions: Set[Permission], required_permission: Permission) -> bool:
        """Verificar si usuario tiene permiso específico"""
        return required_permission in user_permissions
    
    def has_any_permission(self, user_permissions: Set[Permission], required_permissions: List[Permission]) -> bool:
        """Verificar si usuario tiene al menos uno de los permisos"""
        return any(perm in user_permissions for perm in required_permissions)
    
    def has_all_permissions(self, user_permissions: Set[Permission], required_permissions: List[Permission]) -> bool:
        """Verificar si usuario tiene todos los permisos"""
        return all(perm in user_permissions for perm in required_permissions)
    
    def get_role_permissions(self, role: Role) -> Set[Permission]:
        """Obtener permisos para un rol"""
        return self.role_permissions.get(role, set())
    
    def permission_required(permission: Permission):
        """Decorator para requerir permisos específicos"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # TODO: Obtener usuario actual del contexto
                # user = get_current_user()
                # if not user or not user.permissions.has_permission(permission):
                #     raise HTTPException(status_code=403, detail="Insufficient permissions")
                return await func(*args, **kwargs)
            return wrapper
        return decorator
```

## 🔒 Input Validation & Sanitization

### Input Validation

**Validation Schema**
```python
# src/security/validation.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re
import html

class SecureRequest(BaseModel):
    """Schema base para requests seguros"""
    pass

class AnalyzeIntentRequest(SecureRequest):
    """Schema para analyze_intent"""
    objective: str = Field(..., min_length=10, max_length=1000, description="Objetivo a analizar")
    context: Optional[Dict[str, Any]] = Field(None, description="Contexto adicional")
    conversation_id: Optional[str] = Field(None, min_length=8, max_length=64, description="ID de conversación")
    user_id: Optional[str] = Field(None, min_length=8, max_length=64, description="ID de usuario")
    
    @validator('objective')
    def validate_objective(cls, v):
        """Validar objetivo"""
        if not v or not v.strip():
            raise ValueError('Objective cannot be empty')
        
        # Remover caracteres peligrosos
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'eval\s*\(',
            r'exec\s*\(',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Objective contains potentially dangerous content')
        
        return v.strip()
    
    @validator('conversation_id', 'user_id')
    def validate_ids(cls, v):
        """Validar IDs"""
        if v:
            # Solo alfanuméricos y guiones
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('ID contains invalid characters')
        return v

class CreateExecutionPlanRequest(SecureRequest):
    """Schema para create_execution_plan"""
    objective: str = Field(..., min_length=10, max_length=1000)
    analysis: Dict[str, Any] = Field(..., description="Análisis del ReasonerAgent")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Restricciones de ejecución")
    parallel_agents: bool = Field(True, description="Permitir ejecución paralela")
    optimization_criteria: str = Field("balanced", description="Criterio de optimización")
    
    @validator('optimization_criteria')
    def validate_optimization(cls, v):
        """Validar criterio de optimización"""
        valid_criteria = ['speed', 'cost', 'quality', 'balanced']
        if v not in valid_criteria:
            raise ValueError(f'Optimization criteria must be one of: {valid_criteria}')
        return v

class OrchestrateRequest(SecureRequest):
    """Schema para orquestación multi-agente"""
    objective: str = Field(..., min_length=10, max_length=2000)
    context: Optional[Dict[str, Any]] = Field(None)
    streaming_enabled: bool = Field(True)
    quality_threshold: float = Field(0.8, ge=0.0, le=1.0)
    max_execution_time: int = Field(1800, ge=30, le=7200)
    optimization_preference: str = Field("balanced")
    
    @validator('objective')
    def validate_objective(cls, v):
        """Validar objetivo de orquestación"""
        # Validaciones adicionales para objetivos complejos
        if len(v.split('\n')) > 50:  # Limitar número de líneas
            raise ValueError('Objective too complex (max 50 lines)')
        
        # Validar longitud de palabras
        words = v.split()
        if len(words) > 500:  # Limitar número de palabras
            raise ValueError('Objective too long (max 500 words)')
        
        return v

# Validadores de entrada generales
class InputValidator:
    """Validador de entrada general"""
    
    @staticmethod
    def sanitize_html(content: str) -> str:
        """Sanitizar contenido HTML"""
        if not content:
            return ""
        
        # Remover tags peligrosos
        dangerous_tags = ['script', 'object', 'embed', 'link', 'style', 'iframe', 'frameset', 'frame']
        for tag in dangerous_tags:
            pattern = f'<{tag}[^>]*>.*?</{tag}>'
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # Escapar HTML
        return html.escape(content)
    
    @staticmethod
    def validate_file_path(path: str) -> bool:
        """Validar que path de archivo sea seguro"""
        if not path:
            return False
        
        # No permitir paths absolutos
        if path.startswith('/'):
            return False
        
        # No permitir directory traversal
        if '..' in path or path.startswith('.'):
            return False
        
        # Solo caracteres alfanuméricos, guiones, guiones bajos y puntos
        if not re.match(r'^[a-zA-Z0-9._-]+$', path):
            return False
        
        return True
    
    @staticmethod
    def validate_json_size(data: Dict[str, Any], max_size: int = 1024 * 1024) -> bool:
        """Validar tamaño de JSON"""
        import json
        json_str = json.dumps(data)
        return len(json_str) <= max_size
    
    @staticmethod
    def check_sql_injection(query: str) -> bool:
        """Verificar posible inyección SQL"""
        sql_patterns = [
            r'(\bunion\b|\bselect\b|\binsert\b|\bupdate\b|\bdelete\b|\bdrop\b|\bcreate\b|\balter\b)',
            r'(\bexec\b|\bexecute\b|\bsp_\b)',
            r"('|\")",
            r'(--|\/\*|\*\/)',
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        return False
```

### Output Sanitization

**Output Sanitizer**
```python
# src/security/output_sanitizer.py
import json
import html
from typing import Any, Dict, List, Union
from datetime import datetime
import re

class OutputSanitizer:
    """Sanitizador de salida para prevenir XSS y data leakage"""
    
    def __init__(self):
        # PII patterns para detección
        self.pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        }
    
    def sanitize_output(self, data: Any, config: Dict[str, Any] = None) -> Any:
        """Sanitizar datos de salida"""
        if config is None:
            config = {
                'escape_html': True,
                'mask_pii': True,
                'mask_secrets': True,
                'remove_metadata': False
            }
        
        if isinstance(data, dict):
            return self._sanitize_dict(data, config)
        elif isinstance(data, list):
            return [self.sanitize_output(item, config) for item in data]
        elif isinstance(data, str):
            return self._sanitize_string(data, config)
        else:
            return data
    
    def _sanitize_dict(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitizar diccionario"""
        sanitized = {}
        
        for key, value in data.items():
            # Remover metadatos sensibles si está configurado
            if config.get('remove_metadata', False) and key.startswith('_'):
                continue
            
            sanitized_key = self._sanitize_string(key, config)
            sanitized_value = self.sanitize_output(value, config)
            sanitized[sanitized_key] = sanitized_value
        
        return sanitized
    
    def _sanitize_string(self, data: str, config: Dict[str, Any]) -> str:
        """Sanitizar string"""
        if not isinstance(data, str):
            return data
        
        sanitized = data
        
        # Escapar HTML
        if config.get('escape_html', True):
            sanitized = html.escape(sanitized)
        
        # Enmascarar PII
        if config.get('mask_pii', True):
            sanitized = self._mask_pii(sanitized)
        
        # Enmascarar secrets
        if config.get('mask_secrets', True):
            sanitized = self._mask_secrets(sanitized)
        
        return sanitized
    
    def _mask_pii(self, text: str) -> str:
        """Enmascarar información personal identificable"""
        masked = text
        
        for pii_type, pattern in self.pii_patterns.items():
            if pii_type == 'email':
                masked = re.sub(
                    pattern, 
                    lambda m: f"{m.group(0)[:2]}***@{m.group(0).split('@')[1]}", 
                    masked
                )
            elif pii_type == 'phone':
                masked = re.sub(pattern, '***-***-****', masked)
            elif pii_type == 'ssn':
                masked = re.sub(pattern, '***-**-****', masked)
            elif pii_type == 'credit_card':
                masked = re.sub(pattern, '****-****-****-****', masked)
            elif pii_type == 'ip_address':
                masked = re.sub(pattern, 'xxx.xxx.xxx.xxx', masked)
        
        return masked
    
    def _mask_secrets(self, text: str) -> str:
        """Enmascarar secrets y claves"""
        # Patterns para diferentes tipos de secrets
        secret_patterns = [
            r'(password["\s]*[:=]["\s]*)([^"\'\s,}]+)',
            r'(api_key["\s]*[:=]["\s]*)([^"\'\s,}]+)',
            r'(secret["\s]*[:=]["\s]*)([^"\'\s,}]+)',
            r'(token["\s]*[:=]["\s]*)([^"\'\s,}]+)',
            r'(key["\s]*[:=]["\s]*)([^"\'\s,}]+)',
        ]
        
        masked = text
        for pattern in secret_patterns:
            masked = re.sub(pattern, r'\1********', masked, flags=re.IGNORECASE)
        
        return masked
    
    def create_safe_response(self, data: Any, include_metadata: bool = True) -> Dict[str, Any]:
        """Crear respuesta segura"""
        config = {
            'escape_html': True,
            'mask_pii': True,
            'mask_secrets': True,
            'remove_metadata': not include_metadata
        }
        
        sanitized_data = self.sanitize_output(data, config)
        
        response = {
            'data': sanitized_data,
            'timestamp': datetime.utcnow().isoformat(),
            'version': '2.0.0'
        }
        
        if include_metadata:
            response['metadata'] = {
                'sanitized': True,
                'pii_masked': True,
                'secrets_masked': True
            }
        
        return response
```

## 🛡️ Rate Limiting & DDoS Protection

### Rate Limiting Implementation

**Rate Limiter Service**
```python
# src/security/rate_limiter.py
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
import json

class RateLimitTier(Enum):
    """Niveles de rate limiting"""
    FREE = "free"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

@dataclass
class RateLimitConfig:
    """Configuración de rate limiting"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10
    block_duration_minutes: int = 15

# Configuraciones por tier
RATE_LIMIT_CONFIGS = {
    RateLimitTier.FREE: RateLimitConfig(
        requests_per_minute=10,
        requests_per_hour=100,
        requests_per_day=1000,
        burst_limit=5,
        block_duration_minutes=30
    ),
    RateLimitTier.STANDARD: RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=2000,
        requests_per_day=50000,
        burst_limit=15,
        block_duration_minutes=15
    ),
    RateLimitTier.PREMIUM: RateLimitConfig(
        requests_per_minute=300,
        requests_per_hour=10000,
        requests_per_day=200000,
        burst_limit=50,
        block_duration_minutes=5
    ),
    RateLimitTier.ENTERPRISE: RateLimitConfig(
        requests_per_minute=1000,
        requests_per_hour=50000,
        requests_per_day=1000000,
        burst_limit=100,
        block_duration_minutes=1
    )
}

class RateLimiter:
    """Rate limiter con sliding window y token bucket"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        # Fallback en memoria para desarrollo
        self.memory_storage = defaultdict(lambda: {
            'requests': deque(),
            'blocked_until': None
        })
    
    def is_rate_limited(
        self, 
        identifier: str, 
        tier: RateLimitTier = RateLimitTier.FREE,
        endpoint: str = "default"
    ) -> Tuple[bool, Dict[str, Any]]:
        """Verificar si una solicitud está rate limited"""
        config = RATE_LIMIT_CONFIGS[tier]
        key = f"rate_limit:{identifier}:{endpoint}"
        
        now = datetime.utcnow()
        
        # Verificar si está bloqueado
        if self._is_blocked(key):
            return True, {
                'blocked': True,
                'reason': 'Rate limit exceeded',
                'retry_after': self._get_block_remaining_time(key)
            }
        
        # Contar requests en ventanas de tiempo
        current_minute = now.replace(second=0, microsecond=0)
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        current_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Obtener contador actual
        counters = self._get_counters(key)
        
        # Verificar límites
        rate_limit_info = self._check_limits(counters, config, now)
        
        if rate_limit_info['exceeded']:
            # Bloquear usuario
            self._block_user(key, config.block_duration_minutes)
            return True, {
                'blocked': True,
                'reason': 'Rate limit exceeded',
                'limit_type': rate_limit_info['limit_type'],
                'retry_after': config.block_duration_minutes * 60
            }
        
        # Registrar request
        self._record_request(key, now)
        
        return False, {
            'blocked': False,
            'remaining': {
                'minute': config.requests_per_minute - counters.get('minute', 0),
                'hour': config.requests_per_hour - counters.get('hour', 0),
                'day': config.requests_per_day - counters.get('day', 0)
            },
            'reset_times': {
                'minute': (current_minute + timedelta(minutes=1)).isoformat(),
                'hour': (current_hour + timedelta(hours=1)).isoformat(),
                'day': (current_day + timedelta(days=1)).isoformat()
            }
        }
    
    def _is_blocked(self, key: str) -> bool:
        """Verificar si usuario está bloqueado"""
        # TODO: Implementar con Redis
        memory_data = self.memory_storage[key]
        if memory_data['blocked_until']:
            return datetime.utcnow() < memory_data['blocked_until']
        return False
    
    def _get_block_remaining_time(self, key: str) -> int:
        """Obtener tiempo restante de bloqueo"""
        memory_data = self.memory_storage[key]
        if memory_data['blocked_until']:
            remaining = memory_data['blocked_until'] - datetime.utcnow()
            return max(0, int(remaining.total_seconds()))
        return 0
    
    def _get_counters(self, key: str) -> Dict[str, int]:
        """Obtener contadores actuales"""
        # TODO: Implementar con Redis
        memory_data = self.memory_storage[key]
        return {
            'minute': len([r for r in memory_data['requests'] 
                          if r >= datetime.utcnow() - timedelta(minutes=1)]),
            'hour': len([r for r in memory_data['requests'] 
                        if r >= datetime.utcnow() - timedelta(hours=1)]),
            'day': len([r for r in memory_data['requests'] 
                       if r >= datetime.utcnow() - timedelta(days=1)])
        }
    
    def _check_limits(
        self, 
        counters: Dict[str, int], 
        config: RateLimitConfig, 
        now: datetime
    ) -> Dict[str, Any]:
        """Verificar límites de rate limiting"""
        # Verificar burst limit
        burst_count = len([r for r in self.memory_storage[key]['requests'] 
                          if r >= now - timedelta(seconds=10)])
        
        if burst_count >= config.burst_limit:
            return {
                'exceeded': True,
                'limit_type': 'burst',
                'current': burst_count,
                'limit': config.burst_limit
            }
        
        # Verificar límites por tiempo
        for limit_type, current_count in counters.items():
            limit_value = getattr(config, f'requests_per_{limit_type}', 0)
            
            if current_count >= limit_value:
                return {
                    'exceeded': True,
                    'limit_type': limit_type,
                    'current': current_count,
                    'limit': limit_value
                }
        
        return {'exceeded': False}
    
    def _block_user(self, key: str, duration_minutes: int):
        """Bloquear usuario por duración específica"""
        # TODO: Implementar con Redis
        memory_data = self.memory_storage[key]
        memory_data['blocked_until'] = datetime.utcnow() + timedelta(minutes=duration_minutes)
    
    def _record_request(self, key: str, timestamp: datetime):
        """Registrar request en contador"""
        # TODO: Implementar con Redis
        memory_data = self.memory_storage[key]
        memory_data['requests'].append(timestamp)
        
        # Limpiar requests antiguos (más de 24 horas)
        cutoff = datetime.utcnow() - timedelta(days=1)
        while memory_data['requests'] and memory_data['requests'][0] < cutoff:
            memory_data['requests'].popleft()
```

### DDoS Protection

**DDoS Protection Service**
```python
# src/security/ddos_protection.py
from typing import Dict, List, Set, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re
import asyncio

class DDoSProtection:
    """Protección contra ataques DDoS"""
    
    def __init__(self):
        self.suspicious_patterns = [
            r'\b(?:127\.0\.0\.1|localhost)\b',
            r'\b(?:10\.|172\.(?:1[6-9]|2[0-9]|3[01])|192\.168\.)\b',
            r'bot|crawler|spider|scraper',
            r'(?i)(union|select|insert|update|delete|drop|create|alter)',
        ]
        
        self.ip_reputation = defaultdict(lambda: {
            'score': 100,
            'last_seen': datetime.utcnow(),
            'requests_count': 0,
            'blocked_until': None
        })
        
        self.request_patterns = defaultdict(list)
        self.geographic_blocks = set()  # Países bloqueados
        self.asn_blocks = set()  # ASN bloqueados
    
    async def analyze_request(
        self, 
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analizar request para detectar patrones DDoS"""
        analysis = {
            'threat_level': 'low',
            'risk_score': 0,
            'flags': [],
            'recommendations': []
        }
        
        # Analizar IP
        ip_analysis = await self._analyze_ip(request_data.get('client_ip'))
        if ip_analysis['risk_score'] > 0:
            analysis['risk_score'] += ip_analysis['risk_score']
            analysis['flags'].extend(ip_analysis['flags'])
        
        # Analizar User-Agent
        user_agent = request_data.get('user_agent', '')
        ua_analysis = await self._analyze_user_agent(user_agent)
        if ua_analysis['risk_score'] > 0:
            analysis['risk_score'] += ua_analysis['risk_score']
            analysis['flags'].extend(ua_analysis['flags'])
        
        # Analizar patrones de request
        request_pattern = request_data.get('request_pattern', {})
        pattern_analysis = await self._analyze_request_pattern(request_pattern)
        if pattern_analysis['risk_score'] > 0:
            analysis['risk_score'] += pattern_analysis['risk_score']
            analysis['flags'].extend(pattern_analysis['flags'])
        
        # Determinar nivel de amenaza
        if analysis['risk_score'] >= 80:
            analysis['threat_level'] = 'critical'
            analysis['action'] = 'block'
        elif analysis['risk_score'] >= 60:
            analysis['threat_level'] = 'high'
            analysis['action'] = 'challenge'
        elif analysis['risk_score'] >= 30:
            analysis['threat_level'] = 'medium'
            analysis['action'] = 'throttle'
        else:
            analysis['action'] = 'allow'
        
        return analysis
    
    async def _analyze_ip(self, ip: Optional[str]) -> Dict[str, Any]:
        """Analizar dirección IP"""
        if not ip:
            return {'risk_score': 10, 'flags': ['missing_ip']}
        
        ip_info = self.ip_reputation[ip]
        
        # Verificar si IP está bloqueada temporalmente
        if ip_info['blocked_until'] and datetime.utcnow() < ip_info['blocked_until']:
            return {
                'risk_score': 100, 
                'flags': ['temporarily_blocked'],
                'action': 'block'
            }
        
        risk_score = 0
        flags = []
        
        # Verificar patrones sospechosos en IP
        if re.search(r'^(?:0\.|127\.|255\.)', ip):
            risk_score += 30
            flags.append('suspicious_ip_range')
        
        # Verificar velocidad de requests
        if ip_info['requests_count'] > 1000:
            risk_score += 20
            flags.append('high_request_volume')
        
        # Verificar último acceso
        time_since_last = datetime.utcnow() - ip_info['last_seen']
        if time_since_last.total_seconds() < 1:  # Requests en menos de 1 segundo
            risk_score += 25
            flags.append('extremely_fast_requests')
        
        return {
            'risk_score': min(risk_score, 100),
            'flags': flags,
            'ip_info': ip_info
        }
    
    async def _analyze_user_agent(self, user_agent: str) -> Dict[str, Any]:
        """Analizar User-Agent"""
        if not user_agent:
            return {'risk_score': 15, 'flags': ['missing_user_agent']}
        
        risk_score = 0
        flags = []
        
        # Verificar User-Agent vacío o muy genérico
        if len(user_agent) < 10:
            risk_score += 10
            flags.append('generic_user_agent')
        
        # Verificar patrones de bots
        bot_patterns = [
            r'bot|crawler|spider|scraper',
            r'curl|wget|python-requests',
            r'postman|insomnia',
        ]
        
        for pattern in bot_patterns:
            if re.search(pattern, user_agent, re.IGNORECASE):
                risk_score += 20
                flags.append('potential_bot')
                break
        
        # Verificar User-Agent suspicious
        suspicious_patterns = [
            r'^Mozilla/5\.0\s*$',
            r'<script',
            r'eval\(',
            r'javascript:',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, user_agent, re.IGNORECASE):
                risk_score += 40
                flags.append('suspicious_user_agent')
                break
        
        return {
            'risk_score': min(risk_score, 100),
            'flags': flags,
            'user_agent': user_agent
        }
    
    async def _analyze_request_pattern(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Analizar patrón de request"""
        risk_score = 0
        flags = []
        
        # Verificar payload size
        payload_size = pattern.get('payload_size', 0)
        if payload_size > 10 * 1024 * 1024:  # 10MB
            risk_score += 30
            flags.append('large_payload')
        
        # Verificar frecuencia de requests similares
        request_hash = pattern.get('request_hash')
        if request_hash:
            frequency = len(self.request_patterns[request_hash])
            if frequency > 100:
                risk_score += 25
                flags.append('repeated_requests')
            
            self.request_patterns[request_hash].append(datetime.utcnow())
        
        # Verificar endpoints únicos
        endpoints_accessed = pattern.get('endpoints_accessed', [])
        if len(set(endpoints_accessed)) > 50:  # Muchos endpoints únicos
            risk_score += 20
            flags.append('endpoint_flooding')
        
        return {
            'risk_score': min(risk_score, 100),
            'flags': flags,
            'pattern': pattern
        }
    
    def block_ip(self, ip: str, duration_minutes: int = 60):
        """Bloquear IP temporalmente"""
        self.ip_reputation[ip]['blocked_until'] = datetime.utcnow() + timedelta(minutes=duration_minutes)
    
    def add_geographic_block(self, country_code: str):
        """Bloquear requests de un país específico"""
        self.geographic_blocks.add(country_code.lower())
    
    def add_asn_block(self, asn: str):
        """Bloquear requests de un ASN específico"""
        self.asn_blocks.add(asn)
    
    def get_threat_intelligence(self) -> Dict[str, Any]:
        """Obtener inteligencia de amenazas actual"""
        return {
            'blocked_ips': len([ip for ip, info in self.ip_reputation.items() 
                               if info.get('blocked_until')]),
            'suspicious_patterns_count': len(self.request_patterns),
            'geographic_blocks': list(self.geographic_blocks),
            'asn_blocks': list(self.asn_blocks),
            'top_attackers': sorted(
                self.ip_reputation.items(), 
                key=lambda x: x[1]['requests_count'], 
                reverse=True
            )[:10]
        }
```

## 🔐 Secure Configuration Management

### Environment Security

**Secure Configuration**
```python
# src/security/secure_config.py
import os
from typing import Any, Dict, Optional
from cryptography.fernet import Fernet
from pydantic import BaseSettings, validator
import base64

class SecureSettings(BaseSettings):
    """Configuración segura con encriptación"""
    
    # Database
    database_url: str
    database_password: str
    
    # Redis
    redis_url: str
    redis_password: str
    
    # Security
    jwt_secret: str
    encryption_key: str
    
    # API Keys (encriptados)
    contextforge_api_key_encrypted: str
    
    # Development flags
    debug: bool = False
    environment: str = "production"
    
    @validator('database_password', 'redis_password', 'jwt_secret', 'encryption_key')
    def validate_sensitive_data(cls, v):
        """Validar que datos sensibles no estén vacíos"""
        if not v or len(v.strip()) < 8:
            raise ValueError('Sensitive data must be at least 8 characters')
        return v.strip()
    
    @validator('contextforge_api_key_encrypted')
    def validate_encrypted_api_key(cls, v):
        """Validar API key encriptada"""
        if not v:
            raise ValueError('ContextForge API key is required')
        
        try:
            # Intentar decodificar para verificar formato
            Fernet(base64.urlsafe_b64decode(v))
        except Exception:
            raise ValueError('Invalid encrypted API key format')
        
        return v
    
    def decrypt_api_key(self) -> str:
        """Desencriptar API key"""
        f = Fernet(base64.urlsafe_b64decode(self.encryption_key))
        decrypted = f.decrypt(base64.urlsafe_b64decode(self.contextforge_api_key_encrypted))
        return decrypted.decode()
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validar entorno"""
        valid_environments = ['development', 'staging', 'production']
        if v not in valid_environments:
            raise ValueError(f'Environment must be one of: {valid_environments}')
        return v
    
    @validator('debug')
    def validate_debug_mode(cls, v, values):
        """Validar modo debug"""
        if v and values.get('environment') == 'production':
            raise ValueError('Debug mode cannot be enabled in production')
        return v
    
    class Config:
        env_prefix = 'MCP_CORE_'
        case_sensitive = False
        env_file = '.env'
        env_file_encoding = 'utf-8'
        secrets_dir = '/var/run/secrets/mcp-core'  # Para Kubernetes

class SecurityConfig:
    """Configuración de seguridad"""
    
    @staticmethod
    def get_secure_headers() -> Dict[str, str]:
        """Headers de seguridad estándar"""
        return {
            'Strict-Transport-Security': 'max-age=63072000; includeSubDomains; preload',
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            'Content-Security-Policy': (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none';"
            ),
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    
    @staticmethod
    def get_cors_config() -> Dict[str, Any]:
        """Configuración CORS segura"""
        return {
            'allow_origins': os.getenv('CORS_ALLOW_ORIGINS', '').split(',') or ['https://yourdomain.com'],
            'allow_credentials': True,
            'allow_methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            'allow_headers': [
                'Authorization',
                'Content-Type',
                'X-API-Key',
                'X-Requested-With',
                'Accept',
                'Origin',
                'Access-Control-Request-Method',
                'Access-Control-Request-Headers'
            ],
            'expose_headers': [
                'X-Rate-Limit-Remaining',
                'X-Rate-Limit-Reset',
                'X-Request-ID'
            ],
            'max_age': 86400,  # 24 horas
            'allow_origin_regex': None  # Configurar específicamente si es necesario
        }
    
    @staticmethod
    def get_rate_limit_config() -> Dict[str, Any]:
        """Configuración de rate limiting"""
        return {
            'default_limits': ['100/hour', '1000/day'],
            'storage_url': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
            'strategy': 'moving-window',
            'check_your_ip': True,
            'headers_enabled': True,
            'method_whitelist': ['GET', 'HEAD', 'OPTIONS']
        }
```

## 📝 Security Monitoring & Audit

### Security Event Logging

**Security Logger**
```python
# src/security/security_logger.py
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pythonjsonlogger import jsonlogger
from enum import Enum

class SecurityEventType(Enum):
    """Tipos de eventos de seguridad"""
    LOGIN_ATTEMPT = "login_attempt"
    AUTHENTICATION_FAILURE = "auth_failure"
    AUTHORIZATION_FAILURE = "authz_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_ACCESS = "data_access"
    SYSTEM_CONFIG_CHANGE = "config_change"
    ERROR_INJECTION_ATTEMPT = "error_injection"
    SQL_INJECTION_ATTEMPT = "sql_injection"
    XSS_ATTEMPT = "xss_attempt"
    FILE_TRAVERSAL_ATTEMPT = "file_traversal"

class SecurityLogger:
    """Logger específico para eventos de seguridad"""
    
    def __init__(self, service_name: str = "mcp-core-superior"):
        self.service_name = service_name
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Configurar logger JSON"""
        logger = logging.getLogger(f"{self.service_name}.security")
        logger.setLevel(logging.INFO)
        
        # Handler para console en desarrollo
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # Handler para archivo JSON en producción
        file_handler = logging.FileHandler(f"/var/log/{self.service_name}/security.log")
        json_formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s'
        )
        file_handler.setFormatter(json_formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def log_security_event(
        self,
        event_type: SecurityEventType,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "INFO",
        **kwargs
    ):
        """Log evento de seguridad"""
        
        event_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'service': self.service_name,
            'event_type': event_type.value,
            'severity': severity,
            'user_id': user_id,
            'client_ip': ip_address,
            'user_agent': user_agent,
            'details': details or {},
            **kwargs
        }
        
        # Log según severidad
        if severity == "CRITICAL":
            self.logger.critical(json.dumps(event_data))
        elif severity == "ERROR":
            self.logger.error(json.dumps(event_data))
        elif severity == "WARNING":
            self.logger.warning(json.dumps(event_data))
        else:
            self.logger.info(json.dumps(event_data))
    
    def log_authentication_event(
        self,
        event_type: SecurityEventType,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        success: bool = True,
        failure_reason: Optional[str] = None,
        **kwargs
    ):
        """Log evento de autenticación"""
        details = {
            'username': username,
            'success': success,
            'failure_reason': failure_reason
        }
        details.update(kwargs)
        
        severity = "ERROR" if not success else "INFO"
        
        self.log_security_event(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            details=details,
            severity=severity
        )
    
    def log_rate_limit_event(
        self,
        identifier: str,
        limit_type: str,
        current_count: int,
        limit_value: int,
        ip_address: Optional[str] = None,
        **kwargs
    ):
        """Log evento de rate limiting"""
        details = {
            'identifier': identifier,
            'limit_type': limit_type,
            'current_count': current_count,
            'limit_value': limit_value
        }
        details.update(kwargs)
        
        self.log_security_event(
            event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
            ip_address=ip_address,
            details=details,
            severity="WARNING"
        )
    
    def log_suspicious_activity(
        self,
        activity_type: str,
        ip_address: str,
        user_agent: str,
        threat_score: int,
        indicators: list,
        **kwargs
    ):
        """Log actividad sospechosa"""
        details = {
            'activity_type': activity_type,
            'threat_score': threat_score,
            'indicators': indicators
        }
        details.update(kwargs)
        
        severity = "CRITICAL" if threat_score >= 80 else "WARNING"
        
        self.log_security_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            severity=severity
        )
    
    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        action: str = "read",
        ip_address: Optional[str] = None,
        **kwargs
    ):
        """Log acceso a datos"""
        details = {
            'resource_type': resource_type,
            'resource_id': resource_id,
            'action': action
        }
        details.update(kwargs)
        
        self.log_security_event(
            event_type=SecurityEventType.DATA_ACCESS,
            user_id=user_id,
            ip_address=ip_address,
            details=details,
            severity="INFO"
        )

# Instancia global
security_logger = SecurityLogger()
```

### Security Audit Service

**Audit Service**
```python
# src/security/audit_service.py
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import asyncio

class SecurityAuditService:
    """Servicio de auditoría de seguridad"""
    
    def __init__(self, security_logger: SecurityLogger, db_session=None):
        self.logger = security_logger
        self.db = db_session
    
    async def audit_user_activity(
        self, 
        user_id: str, 
        time_window: timedelta = timedelta(hours=24)
    ) -> Dict[str, Any]:
        """Auditar actividad de usuario"""
        end_time = datetime.utcnow()
        start_time = end_time - time_window
        
        # Obtener eventos de seguridad del usuario
        user_events = await self._get_security_events(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time
        )
        
        # Analizar patrones
        analysis = self._analyze_user_patterns(user_events)
        
        # Verificar anomalías
        anomalies = self._detect_anomalies(user_events, analysis)
        
        return {
            'user_id': user_id,
            'time_window': str(time_window),
            'event_count': len(user_events),
            'analysis': analysis,
            'anomalies': anomalies,
            'risk_score': self._calculate_risk_score(analysis, anomalies)
        }
    
    async def audit_system_security(
        self,
        time_window: timedelta = timedelta(hours=24)
    ) -> Dict[str, Any]:
        """Auditar seguridad del sistema"""
        end_time = datetime.utcnow()
        start_time = end_time - time_window
        
        # Obtener todos los eventos de seguridad
        all_events = await self._get_all_security_events(start_time, end_time)
        
        # Estadísticas generales
        stats = self._calculate_security_stats(all_events)
        
        # Detectar amenazas
        threats = self._detect_system_threats(all_events)
        
        # Top fuentes de amenazas
        threat_sources = self._get_top_threat_sources(all_events)
        
        return {
            'time_window': str(time_window),
            'total_events': len(all_events),
            'statistics': stats,
            'threats': threats,
            'top_sources': threat_sources,
            'recommendations': self._generate_recommendations(stats, threats)
        }
    
    def _analyze_user_patterns(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analizar patrones de usuario"""
        ip_counter = Counter()
        endpoint_counter = Counter()
        hourly_activity = defaultdict(int)
        
        for event in events:
            ip_counter[event.get('client_ip', 'unknown')] += 1
            endpoint = event.get('details', {}).get('endpoint', 'unknown')
            endpoint_counter[endpoint] += 1
            
            event_time = datetime.fromisoformat(event['timestamp'])
            hourly_activity[event_time.hour] += 1
        
        return {
            'unique_ips': len(ip_counter),
            'top_ips': dict(ip_counter.most_common(10)),
            'unique_endpoints': len(endpoint_counter),
            'top_endpoints': dict(endpoint_counter.most_common(10)),
            'hourly_pattern': dict(hourly_activity),
            'average_events_per_hour': len(events) / 24 if events else 0
        }
    
    def _detect_anomalies(
        self, 
        events: List[Dict[str, Any]], 
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detectar anomalías en actividad"""
        anomalies = []
        
        # Detectar cambios de IP sospechosos
        unique_ips = analysis['unique_ips']
        if unique_ips > 5:  # Many different IPs
            anomalies.append({
                'type': 'suspicious_ip_diversity',
                'description': f'User accessed from {unique_ips} different IPs',
                'severity': 'medium',
                'count': unique_ips
            })
        
        # Detectar actividad fuera de horas normales
        nighttime_activity = sum(
            analysis['hourly_pattern'].get(h, 0) 
            for h in range(0, 6)  # 12 AM to 6 AM
        )
        total_activity = sum(analysis['hourly_pattern'].values())
        if total_activity > 0:
            nighttime_percentage = (nighttime_activity / total_activity) * 100
            if nighttime_percentage > 30:  # More than 30% activity at night
                anomalies.append({
                    'type': 'unusual_time_pattern',
                    'description': f'{nighttime_percentage:.1f}% of activity during nighttime hours',
                    'severity': 'low',
                    'percentage': nighttime_percentage
                })
        
        # Detectar bursts de actividad
        for hour, count in analysis['hourly_pattern'].items():
            if count > analysis['average_events_per_hour'] * 3:  # 3x average
                anomalies.append({
                    'type': 'activity_burst',
                    'description': f'Unusual burst of activity at {hour}:00 ({count} events)',
                    'severity': 'high',
                    'hour': hour,
                    'count': count
                })
        
        return anomalies
    
    def _calculate_risk_score(
        self, 
        analysis: Dict[str, Any], 
        anomalies: List[Dict[str, Any]]
    ) -> int:
        """Calcular score de riesgo"""
        score = 0
        
        # Base score por diversidad de IP
        unique_ips = analysis['unique_ips']
        if unique_ips > 10:
            score += 30
        elif unique_ips > 5:
            score += 20
        elif unique_ips > 2:
            score += 10
        
        # Score por anomalías
        for anomaly in anomalies:
            if anomaly['severity'] == 'high':
                score += 25
            elif anomaly['severity'] == 'medium':
                score += 15
            elif anomaly['severity'] == 'low':
                score += 5
        
        return min(score, 100)  # Cap at 100
    
    async def _get_security_events(
        self, 
        user_id: str, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Obtener eventos de seguridad para usuario"""
        # TODO: Implementar consulta a BD
        return []
    
    async def _get_all_security_events(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Obtener todos los eventos de seguridad"""
        # TODO: Implementar consulta a BD
        return []
    
    def _calculate_security_stats(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcular estadísticas de seguridad"""
        if not events:
            return {}
        
        event_types = Counter(event['event_type'] for event in events)
        severity_counts = Counter(event.get('severity', 'INFO') for event in events)
        daily_counts = defaultdict(int)
        
        for event in events:
            event_date = datetime.fromisoformat(event['timestamp']).date()
            daily_counts[event_date] += 1
        
        return {
            'event_types': dict(event_types),
            'severity_distribution': dict(severity_counts),
            'daily_volume': dict(daily_counts),
            'total_events': len(events),
            'unique_users': len(set(event.get('user_id') for event in events if event.get('user_id'))),
            'unique_ips': len(set(event.get('client_ip') for event in events if event.get('client_ip')))
        }
    
    def _detect_system_threats(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detectar amenazas del sistema"""
        threats = []
        
        # Detectar brute force attacks
        ip_attempts = defaultdict(list)
        for event in events:
            if event['event_type'] in ['auth_failure', 'login_attempt']:
                ip_attempts[event.get('client_ip', 'unknown')].append(event)
        
        for ip, attempts in ip_attempts.items():
            if len(attempts) > 50:  # More than 50 failed attempts
                threats.append({
                    'type': 'potential_brute_force',
                    'ip': ip,
                    'attempt_count': len(attempts),
                    'severity': 'high',
                    'time_window': '24h'
                })
        
        # Detectar SQL injection attempts
        sql_injection_events = [
            event for event in events 
            if event['event_type'] == 'sql_injection_attempt'
        ]
        
        if sql_injection_events:
            unique_ips = set(event.get('client_ip') for event in sql_injection_events)
            threats.append({
                'type': 'sql_injection_detected',
                'ip_count': len(unique_ips),
                'total_attempts': len(sql_injection_events),
                'severity': 'critical'
            })
        
        return threats
    
    def _get_top_threat_sources(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Obtener principales fuentes de amenazas"""
        ip_threat_scores = defaultdict(int)
        
        for event in events:
            ip = event.get('client_ip', 'unknown')
            severity = event.get('severity', 'INFO')
            
            # Asignar score por severidad
            if severity == 'CRITICAL':
                ip_threat_scores[ip] += 10
            elif severity == 'ERROR':
                ip_threat_scores[ip] += 5
            elif severity == 'WARNING':
                ip_threat_scores[ip] += 2
        
        # Retornar top 10
        return [
            {'ip': ip, 'threat_score': score}
            for ip, score in sorted(ip_threat_scores.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
    
    def _generate_recommendations(
        self, 
        stats: Dict[str, Any], 
        threats: List[Dict[str, Any]]
    ) -> List[str]:
        """Generar recomendaciones de seguridad"""
        recommendations = []
        
        # Recomendaciones basadas en estadísticas
        error_rate = stats.get('severity_distribution', {}).get('ERROR', 0)
        total_events = stats.get('total_events', 0)
        
        if total_events > 0 and (error_rate / total_events) > 0.1:
            recommendations.append("High error rate detected. Review error patterns and implement better input validation.")
        
        # Recomendaciones basadas en amenazas
        critical_threats = [t for t in threats if t.get('severity') == 'critical']
        if critical_threats:
            recommendations.append("Critical threats detected. Consider implementing additional security measures and blocking malicious IPs.")
        
        high_threats = [t for t in threats if t.get('severity') == 'high']
        if len(high_threats) > 5:
            recommendations.append("Multiple high-severity threats detected. Review security configuration and consider upgrading security policies.")
        
        return recommendations
```

## 📊 Security Metrics & Dashboards

### Security KPIs

**Security Metrics Service**
```python
# src/security/security_metrics.py
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

@dataclass
class SecurityMetric:
    """Métrica de seguridad"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    threshold: Optional[float] = None
    status: str = "normal"  # normal, warning, critical

class SecurityMetricsService:
    """Servicio de métricas de seguridad"""
    
    def __init__(self):
        self.metrics = []
        self.thresholds = {
            'failed_authentication_rate': {'warning': 0.05, 'critical': 0.10},
            'suspicious_activity_rate': {'warning': 0.02, 'critical': 0.05},
            'rate_limit_violations_per_hour': {'warning': 100, 'critical': 500},
            'unique_threat_ips': {'warning': 50, 'critical': 100},
            'security_events_per_hour': {'warning': 1000, 'critical': 5000}
        }
    
    def calculate_security_metrics(self, time_window: timedelta = timedelta(hours=1)) -> List[SecurityMetric]:
        """Calcular métricas de seguridad para ventana de tiempo"""
        end_time = datetime.utcnow()
        start_time = end_time - time_window
        
        metrics = []
        
        # Tasa de autenticación fallida
        failed_auth_rate = self._calculate_failed_auth_rate(start_time, end_time)
        metrics.append(SecurityMetric(
            name="failed_authentication_rate",
            value=failed_auth_rate,
            unit="percentage",
            timestamp=end_time,
            threshold=self.thresholds['failed_authentication_rate']['critical'],
            status=self._get_metric_status(failed_auth_rate, 'failed_authentication_rate')
        ))
        
        # Tasa de actividad sospechosa
        suspicious_rate = self._calculate_suspicious_activity_rate(start_time, end_time)
        metrics.append(SecurityMetric(
            name="suspicious_activity_rate",
            value=suspicious_rate,
            unit="percentage",
            timestamp=end_time,
            threshold=self.thresholds['suspicious_activity_rate']['critical'],
            status=self._get_metric_status(suspicious_rate, 'suspicious_activity_rate')
        ))
        
        # Violaciones de rate limiting por hora
        rate_limit_violations = self._get_rate_limit_violations_per_hour(start_time, end_time)
        metrics.append(SecurityMetric(
            name="rate_limit_violations_per_hour",
            value=rate_limit_violations,
            unit="count",
            timestamp=end_time,
            threshold=self.thresholds['rate_limit_violations_per_hour']['critical'],
            status=self._get_metric_status(rate_limit_violations, 'rate_limit_violations_per_hour')
        ))
        
        # IPs únicas amenazantes
        threat_ips = self._get_unique_threat_ips(start_time, end_time)
        metrics.append(SecurityMetric(
            name="unique_threat_ips",
            value=threat_ips,
            unit="count",
            timestamp=end_time,
            threshold=self.thresholds['unique_threat_ips']['critical'],
            status=self._get_metric_status(threat_ips, 'unique_threat_ips')
        ))
        
        # Eventos de seguridad por hora
        security_events = self._get_security_events_per_hour(start_time, end_time)
        metrics.append(SecurityMetric(
            name="security_events_per_hour",
            value=security_events,
            unit="count",
            timestamp=end_time,
            threshold=self.thresholds['security_events_per_hour']['critical'],
            status=self._get_metric_status(security_events, 'security_events_per_hour')
        ))
        
        return metrics
    
    def _get_metric_status(self, value: float, metric_name: str) -> str:
        """Determinar estado de métrica"""
        if metric_name not in self.thresholds:
            return "unknown"
        
        thresholds = self.thresholds[metric_name]
        
        if value >= thresholds['critical']:
            return "critical"
        elif value >= thresholds['warning']:
            return "warning"
        else:
            return "normal"
    
    def generate_security_dashboard_data(self) -> Dict[str, Any]:
        """Generar datos para dashboard de seguridad"""
        current_metrics = self.calculate_security_metrics()
        
        # Métricas de la última hora
        hourly_metrics = {metric.name: metric.value for metric in current_metrics}
        
        # Métricas del último día
        daily_metrics = self.calculate_security_metrics(timedelta(days=1))
        daily_metrics_dict = {metric.name: metric.value for metric in daily_metrics}
        
        # Tendencias (comparar con período anterior)
        trends = self._calculate_trends()
        
        # Alertas activas
        active_alerts = self._get_active_security_alerts()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'current_metrics': hourly_metrics,
            'daily_metrics': daily_metrics_dict,
            'trends': trends,
            'active_alerts': active_alerts,
            'security_score': self._calculate_security_score(current_metrics),
            'recommendations': self._get_security_recommendations(current_metrics)
        }
    
    def _calculate_failed_auth_rate(self, start_time: datetime, end_time: datetime) -> float:
        """Calcular tasa de autenticación fallida"""
        # TODO: Implementar con datos reales
        return 0.02  # 2%
    
    def _calculate_suspicious_activity_rate(self, start_time: datetime, end_time: datetime) -> float:
        """Calcular tasa de actividad sospechosa"""
        # TODO: Implementar con datos reales
        return 0.01  # 1%
    
    def _get_rate_limit_violations_per_hour(self, start_time: datetime, end_time: datetime) -> int:
        """Obtener violaciones de rate limiting por hora"""
        # TODO: Implementar con datos reales
        return 45
    
    def _get_unique_threat_ips(self, start_time: datetime, end_time: datetime) -> int:
        """Obtener número de IPs amenazantes únicas"""
        # TODO: Implementar con datos reales
        return 23
    
    def _get_security_events_per_hour(self, start_time: datetime, end_time: datetime) -> int:
        """Obtener eventos de seguridad por hora"""
        # TODO: Implementar con datos reales
        return 156
    
    def _calculate_trends(self) -> Dict[str, str]:
        """Calcular tendencias de métricas"""
        # TODO: Implementar con datos históricos
        return {
            'failed_authentication_rate': 'decreasing',
            'suspicious_activity_rate': 'stable',
            'rate_limit_violations_per_hour': 'increasing',
            'unique_threat_ips': 'stable',
            'security_events_per_hour': 'decreasing'
        }
    
    def _get_active_security_alerts(self) -> List[Dict[str, Any]]:
        """Obtener alertas de seguridad activas"""
        alerts = []
        current_metrics = self.calculate_security_metrics()
        
        for metric in current_metrics:
            if metric.status in ['warning', 'critical']:
                alerts.append({
                    'metric': metric.name,
                    'current_value': metric.value,
                    'threshold': metric.threshold,
                    'severity': metric.status,
                    'timestamp': metric.timestamp.isoformat(),
                    'message': f"{metric.name} is {metric.status}: {metric.value}"
                })
        
        return alerts
    
    def _calculate_security_score(self, metrics: List[SecurityMetric]) -> int:
        """Calcular score general de seguridad (0-100)"""
        if not metrics:
            return 0
        
        total_score = 0
        for metric in metrics:
            if metric.status == 'normal':
                total_score += 20  # 20 points per normal metric
            elif metric.status == 'warning':
                total_score += 10  # 10 points per warning metric
            # critical metrics add 0 points
        
        return min(total_score, 100)
    
    def _get_security_recommendations(self, metrics: List[SecurityMetric]) -> List[str]:
        """Obtener recomendaciones basadas en métricas"""
        recommendations = []
        
        for metric in metrics:
            if metric.status == 'critical':
                if metric.name == 'failed_authentication_rate':
                    recommendations.append("Investigate failed login attempts and consider implementing account lockout policies.")
                elif metric.name == 'suspicious_activity_rate':
                    recommendations.append("Review suspicious activity patterns and enhance monitoring.")
                elif metric.name == 'rate_limit_violations_per_hour':
                    recommendations.append("Consider adjusting rate limits or investigating potential abuse.")
                elif metric.name == 'unique_threat_ips':
                    recommendations.append("Review threat intelligence and consider implementing IP blocking.")
            
            elif metric.status == 'warning':
                recommendations.append(f"Monitor {metric.name} closely as it's approaching critical levels.")
        
        return recommendations
```

## 🔧 Security Implementation Guide

### Complete Security Middleware

**Security Middleware**
```python
# src/middleware/security_middleware.py
from fastapi import Request, Response, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from typing import Callable
import time
import uuid

class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware completo de seguridad"""
    
    def __init__(
        self,
        app,
        security_config: Dict[str, Any],
        rate_limiter,
        ddos_protector,
        security_logger
    ):
        super().__init__(app)
        self.security_config = security_config
        self.rate_limiter = rate_limiter
        self.ddos_protector = ddos_protector
        self.security_logger = security_logger
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # Agregar request ID
        request.state.request_id = request_id
        
        try:
            # 1. Verificar rate limiting
            rate_limit_result = await self._check_rate_limiting(request)
            if rate_limit_result['blocked']:
                self.security_logger.log_rate_limit_event(
                    identifier=self._get_client_identifier(request),
                    limit_type=rate_limit_result.get('limit_type', 'unknown'),
                    current_count=rate_limit_result.get('current_count', 0),
                    limit_value=rate_limit_result.get('limit_value', 0),
                    ip_address=request.client.host,
                    request_id=request_id
                )
                
                return self._create_rate_limit_response(rate_limit_result)
            
            # 2. Verificar DDoS protection
            ddos_analysis = await self.ddos_protector.analyze_request({
                'client_ip': request.client.host,
                'user_agent': request.headers.get('user-agent', ''),
                'request_pattern': {
                    'endpoint': str(request.url.path),
                    'method': request.method,
                    'headers': dict(request.headers),
                    'payload_size': 0  # TODO: calculate actual size
                }
            })
            
            if ddos_analysis['action'] == 'block':
                self.security_logger.log_suspicious_activity(
                    activity_type="ddos_protection_block",
                    ip_address=request.client.host,
                    user_agent=request.headers.get('user-agent', ''),
                    threat_score=ddos_analysis['risk_score'],
                    indicators=ddos_analysis['flags'],
                    request_id=request_id
                )
                
                return Response(
                    content="Request blocked by security policy",
                    status_code=429,
                    headers={'Retry-After': '3600'}
                )
            
            # 3. Validar headers de seguridad
            security_headers = self._validate_security_headers(request)
            if not security_headers['valid']:
                self.security_logger.log_security_event(
                    event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                    ip_address=request.client.host,
                    user_agent=request.headers.get('user-agent', ''),
                    details={'invalid_headers': security_headers['invalid']},
                    severity="WARNING",
                    request_id=request_id
                )
            
            # 4. Procesar request
            response = await call_next(request)
            
            # 5. Agregar headers de seguridad
            response.headers.update(self.security_config['secure_headers'])
            
            # 6. Log request de acceso a datos
            if self._is_data_access_endpoint(request.url.path):
                self.security_logger.log_data_access(
                    user_id=self._get_user_id(request),
                    resource_type=self._get_resource_type(request.url.path),
                    resource_id=self._get_resource_id(request),
                    action=self._get_action(request.method),
                    ip_address=request.client.host,
                    request_id=request_id
                )
            
            return response
            
        except Exception as e:
            # Log error de seguridad
            self.security_logger.log_security_event(
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                ip_address=request.client.host,
                user_agent=request.headers.get('user-agent', ''),
                details={'error': str(e), 'request_id': request_id},
                severity="ERROR",
                request_id=request_id
            )
            
            raise HTTPException(status_code=500, detail="Internal server error")
        
        finally:
            # Log tiempo de procesamiento
            processing_time = time.time() - start_time
            if processing_time > 5.0:  # Slow request
                self.security_logger.log_security_event(
                    event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                    ip_address=request.client.host,
                    details={
                        'slow_request': True,
                        'processing_time': processing_time,
                        'endpoint': str(request.url.path),
                        'request_id': request_id
                    },
                    severity="WARNING",
                    request_id=request_id
                )
    
    def _get_client_identifier(self, request: Request) -> str:
        """Obtener identificador de cliente para rate limiting"""
        # Prioridad: API Key > User ID > IP
        api_key = request.headers.get('X-API-Key')
        if api_key:
            return f"api_key:{api_key[:16]}"
        
        user_id = self._get_user_id(request)
        if user_id:
            return f"user:{user_id}"
        
        return f"ip:{request.client.host}"
    
    async def _check_rate_limiting(self, request: Request) -> Dict[str, Any]:
        """Verificar rate limiting"""
        identifier = self._get_client_identifier(request)
        
        # Determinar tier basado en autenticación
        tier = self._get_rate_limit_tier(request)
        
        endpoint = self._map_endpoint_for_rate_limiting(request.url.path)
        
        return await self.rate_limiter.is_rate_limited(
            identifier=identifier,
            tier=tier,
            endpoint=endpoint
        )
    
    def _get_rate_limit_tier(self, request: Request) -> RateLimitTier:
        """Determinar tier de rate limiting basado en autenticación"""
        # TODO: Implementar lógica para determinar tier
        return RateLimitTier.FREE
    
    def _map_endpoint_for_rate_limiting(self, path: str) -> str:
        """Mapear endpoint para rate limiting"""
        if path.startswith('/mcp-tools/'):
            return 'mcp_tools'
        elif path.startswith('/orchestrate'):
            return 'orchestration'
        elif path.startswith('/admin'):
            return 'admin'
        else:
            return 'default'
    
    def _validate_security_headers(self, request: Request) -> Dict[str, Any]:
        """Validar headers de seguridad"""
        invalid_headers = []
        
        # Verificar User-Agent
        user_agent = request.headers.get('user-agent', '')
        if len(user_agent) < 5:
            invalid_headers.append('user_agent_too_short')
        
        # Verificar headers sospechosos
        suspicious_headers = ['x-forwarded-for', 'x-real-ip']
        for header in suspicious_headers:
            if header in request.headers:
                invalid_headers.append(f'suspicious_header_{header}')
        
        return {
            'valid': len(invalid_headers) == 0,
            'invalid': invalid_headers
        }
    
    def _is_data_access_endpoint(self, path: str) -> bool:
        """Verificar si es endpoint de acceso a datos"""
        data_endpoints = [
            '/mcp-tools/analyze_intent',
            '/mcp-tools/create_execution_plan',
            '/orchestrate'
        ]
        return path in data_endpoints
    
    def _get_user_id(self, request: Request) -> Optional[str]:
        """Obtener user ID del request"""
        # TODO: Implementar extracción de user ID desde token JWT
        return None
    
    def _get_resource_type(self, path: str) -> str:
        """Obtener tipo de recurso"""
        if 'analyze_intent' in path:
            return 'analysis'
        elif 'create_execution_plan' in path:
            return 'execution_plan'
        elif 'orchestrate' in path:
            return 'orchestration'
        else:
            return 'unknown'
    
    def _get_resource_id(self, request: Request) -> Optional[str]:
        """Obtener ID de recurso"""
        # TODO: Extraer ID desde path o query params
        return None
    
    def _get_action(self, method: str) -> str:
        """Obtener acción HTTP"""
        method_actions = {
            'GET': 'read',
            'POST': 'create',
            'PUT': 'update',
            'DELETE': 'delete'
        }
        return method_actions.get(method, 'unknown')
    
    def _create_rate_limit_response(self, rate_limit_result: Dict[str, Any]) -> Response:
        """Crear respuesta de rate limiting"""
        headers = {
            'Retry-After': str(rate_limit_result.get('retry_after', 60)),
            'X-RateLimit-Limit': str(rate_limit_result.get('limit', 0)),
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': str(rate_limit_result.get('reset_time', 0))
        }
        
        return Response(
            content="Rate limit exceeded",
            status_code=429,
            headers=headers
        )
```

---

## 📋 Security Checklist

### Pre-Production Security Checklist

#### Authentication & Authorization
- [ ] JWT tokens configurados con expiración apropiada
- [ ] API Keys generadas con entropía suficiente
- [ ] Sistema RBAC implementado y probado
- [ ] Passwords hasheados con algoritmos seguros (bcrypt/argon2)
- [ ] Multi-factor authentication habilitado para admin users

#### Input Validation & Sanitization
- [ ] Todos los inputs validados con schemas Pydantic
- [ ] Output sanitization implementado para prevenir XSS
- [ ] SQL injection protection verificado
- [ ] File upload validation implementado
- [ ] Command injection protection verificado

#### Network Security
- [ ] TLS 1.3 habilitado en todos los endpoints
- [ ] Certificate pinning implementado donde sea apropiado
- [ ] HSTS headers configurados
- [ ] CORS policies configuradas correctamente
- [ ] VPN configurado para comunicación interna

#### Data Security
- [ ] Datos sensibles encriptados en reposo
- [ ] Backup encryption habilitado
- [ ] Key rotation policy implementada
- [ ] Database connection encryption habilitado
- [ ] PII detection y masking implementado

#### Infrastructure Security
- [ ] Containers ejecutándose como usuarios no-root
- [ ] Secret management implementado (K8s secrets, AWS Secrets Manager)
- [ ] Network policies configuradas en Kubernetes
- [ ] Container image scanning implementado
- [ ] Runtime security monitoring habilitado

#### Monitoring & Alerting
- [ ] Security event logging implementado
- [ ] Rate limiting configurado y monitoreado
- [ ] DDoS protection implementado
- [ ] Security metrics dashboard configurado
- [ ] Incident response procedures documentadas

#### Compliance
- [ ] GDPR compliance verificado (si aplica)
- [ ] Data retention policies implementadas
- [ ] Audit logging configurado
- [ ] Privacy policy actualizada
- [ ] Security training completado por el equipo

---

**Próximos pasos**: Después de implementar las medidas de seguridad, revisar [Monitoring Guide](../monitoring/overview.md) para configurar observabilidad completa.