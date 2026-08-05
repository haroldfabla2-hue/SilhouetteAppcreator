# Sistema de Authentication & Authorization Layer

Sistema completo de seguridad que implementa autenticación y autorización robusta con soporte para múltiples proveedores, MFA, y auditoría avanzada.

## 🚀 Características Implementadas

### 1. JWT Token Management
- ✅ Generación de access tokens, refresh tokens e ID tokens
- ✅ Validación automática de tokens
- ✅ Rotación automática de tokens
- ✅ Tokens con claims personalizados
- ✅ Expiración configurable

### 2. OAuth 2.0 y OpenID Connect
- ✅ Integración con Google OAuth
- ✅ Integración con GitHub OAuth
- ✅ Integración con Microsoft OAuth
- ✅ Integración con Azure AD
- ✅ Soporte para scopes personalizados
- ✅ Validación automática de callbacks

### 3. Multi-Factor Authentication (MFA)
- ✅ TOTP (Time-based One-Time Password)
- ✅ Generación de códigos QR para TOTP
- ✅ Verificación SMS (Twilio/AWS SNS)
- ✅ Encriptación de secretos MFA
- ✅ Soporte para múltiples métodos MFA

### 4. Role-Based Access Control (RBAC)
- ✅ Definición de roles jerárquicos
- ✅ Herencia de permisos entre roles
- ✅ Asignación dinámica de roles
- ✅ Verificación de permisos en tiempo real
- ✅ Permisos granulares por recurso

### 5. Attribute-Based Access Control (ABAC)
- ✅ Políticas basadas en atributos de usuario
- ✅ Context-aware authorization
- ✅ Condiciones dinámicas
- ✅ Soporte para recursos complejos

### 6. Session Management
- ✅ Gestión de sesiones concurrentes
- ✅ Timeout automático de sesiones
- ✅ Invalidación de sesiones
- ✅ Tracking de actividad de usuario
- ✅ Cleanup automático de sesiones expiradas

### 7. API Key Management
- ✅ Generación de API keys seguras
- ✅ Permisos granulares por API key
- ✅ Rate limiting por API key
- ✅ Expiración configurable
- ✅ Rotación de API keys

### 8. Single Sign-On (SSO)
- ✅ Integración LDAP
- ✅ Integración Active Directory
- ✅ OAuth SSO providers
- ✅ Gestión centralizada de sesiones
- ✅ Configuración empresarial

### 9. Audit Logging
- ✅ Logging detallado de autenticación
- ✅ Logging de autorizaciones
- ✅ Tracking de cambios de permisos
- ✅ Almacenamiento estructurado de logs
- ✅ Detección de anomalías

### 10. Permission Inheritance y Resource-Level Security
- ✅ Herencia jerárquica de permisos
- ✅ Permisos por nivel de recurso
- ✅ Validación contextual
- ✅ Soporte para recursos anidados
- ✅ Políticas de seguridad avanzadas

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layer                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Auth System     │  │ Security Utils  │  │ Config       │ │
│  │ - JWT Tokens    │  │ - Validation    │  │ - LDAP       │ │
│  │ - OAuth         │  │ - Hashing       │  │ - OAuth      │ │
│  │ - MFA           │  │ - Encryption    │  │ - Database   │ │
│  │ - RBAC/ABAC     │  │ - Rate Limit    │  │ - Redis      │ │
│  │ - Sessions      │  │                 │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Auth Middleware │  │ Audit Logger    │  │ Providers    │ │
│  │ - FastAPI       │  │ - Events        │  │ - LDAP       │ │
│  │ - Dependencies  │  │ - Storage       │  │ - OAuth      │ │
│  │ - Guards        │  │ - Analytics     │  │ - SMS        │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Instalación

1. **Instalar dependencias:**
```bash
pip install -r requirements-security.txt
```

2. **Configurar variables de entorno:**
```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_EXPIRE_MINUTES=15
JWT_REFRESH_EXPIRE_DAYS=30

# OAuth Providers
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# LDAP Configuration
LDAP_SERVER=ldap://your-ldap-server
LDAP_DOMAIN=your-domain
LDAP_SEARCH_BASE=DC=your,DC=domain

# Database
DATABASE_URL=postgresql://user:pass@localhost/auth_db
REDIS_URL=redis://localhost:6379

# Email/SMS
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your-email
SMTP_PASSWORD=your-password
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
```

## 🚀 Uso Básico

### 1. Inicialización

```python
from src.security import auth_system

# Inicializar sistema
await auth_system.initialize()

# Verificar salud
health = await auth_system.health_check()
print(f"Sistema: {health['status']}")
```

### 2. Autenticación Básica

```python
# Login con username/password
result = await auth_system.authenticate(
    username="user@example.com",
    password="secure_password",
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0..."
)

if result["success"]:
    tokens = result["tokens"]
    user = result["user"]
    print(f"Usuario: {user['username']}")
    print(f"Access Token: {tokens['access_token']}")
```

### 3. OAuth Login

```python
# Iniciar OAuth con Google
auth_system.initiate_sso("google", "/dashboard")

# Callback OAuth
result = await auth_system.oauth_authenticate(
    provider="google",
    code="authorization_code",
    ip_address="192.168.1.100"
)
```

### 4. MFA Configuration

```python
# Configurar TOTP
mfa_data = await auth_system.enable_totp_mfa(user_id)
qr_code = mfa_data["qr_code"]  # Mostrar al usuario

# Verificar código TOTP
is_valid = await auth_system.verify_totp_setup(user_id, "123456")

# Enviar SMS
await auth_system.send_sms_verification(user_id)
```

### 5. Autorización

```python
# Verificar permiso RBAC
has_permission = await auth_system.check_permission(
    user_id="user_123",
    resource="user",
    action="create",
    context={"ip_address": "192.168.1.100"}
)

if has_permission:
    # Permitir acción
    pass
```

### 6. API Keys

```python
# Crear API Key
api_key = await auth_system.create_api_key(
    user_id="user_123",
    permissions=["perm_api_read", "perm_api_write"],
    scopes=["read", "write"],
    expires_at=datetime.now() + timedelta(days=365)
)

# Validar API Key
key_info = await auth_system.validate_api_key(
    api_key="key_id:generated_key",
    required_permission="perm_api_read"
)
```

## 🔒 Middleware FastAPI

### Integración Completa

```python
from fastapi import FastAPI
from src.security.auth_middleware import (
    AuthMiddleware,
    get_current_user,
    require_permission,
    require_role
)

app = FastAPI()

# Agregar middleware de autenticación
app.add_middleware(AuthMiddleware, exclude_paths=["/health", "/docs"])

# Endpoint protegido
@app.get("/protected")
async def protected_endpoint(
    current_user: dict = Depends(get_current_user)
):
    return {"message": f"Hello, {current_user['username']}"}

# Endpoint con rol requerido
@app.post("/admin/users")
async def create_user(
    user_data: dict,
    current_user: dict = Depends(require_role("admin"))
):
    return {"message": "User created", "by": current_user['username']}

# Endpoint con permiso específico
@app.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_permission("perm_user_delete"))
):
    return {"message": f"User {user_id} deleted"}
```

## 📊 Ejemplo de Respuesta de Login

```json
{
  "success": true,
  "user": {
    "user_id": "user_123",
    "username": "john.doe",
    "email": "john@example.com",
    "roles": ["user", "manager"],
    "permissions": ["perm_user_read", "perm_user_update"],
    "attributes": {
      "department": "IT",
      "validation_level": "verified"
    }
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "id_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 900,
    "expires_at": "2023-12-01T10:15:00Z"
  },
  "session_id": "sess_abc123...",
  "expires_at": "2023-12-01T10:15:00Z"
}
```

## 🔐 Configuración de Seguridad

### Políticas de Contraseñas

```python
from src.security.auth_utils import password_validator

# Validar contraseña
validation = password_validator.validate_password("MySecure123!")
if validation["valid"]:
    # Contraseña válida
    pass
else:
    # Mostrar errores
    for error in validation["errors"]:
        print(error)

# Generar contraseña segura
secure_password = password_validator.generate_secure_password(length=16)
```

### Rate Limiting

```python
from src.security.auth_utils import rate_limiter

# Verificar si está limitado
is_limited = rate_limiter.is_rate_limited(
    identifier="192.168.1.100",
    max_requests=5,
    window_seconds=60
)
```

## 📝 Auditoría

### Eventos Automáticamente Registrados

- ✅ Intentos de autenticación (exitosos y fallidos)
- ✅ Verificaciones de autorización
- ✅ Creación/modificación de usuarios
- ✅ Asignación de roles y permisos
- ✅ Creación y uso de API keys
- ✅ Configuración de MFA
- ✅ Terminación de sesiones

### Consultar Logs

```python
# Los logs se almacenan automáticamente en:
# - Base de datos (tabla audit_logs)
# - Archivo de log (logs/audit.log)
# - Sistema de logging de Python

# Acceso programático
await auth_system.audit_logger.log_event(
    user_id="user_123",
    action="custom_action",
    resource="custom_resource",
    success=True,
    ip_address="192.168.1.100",
    user_agent="Custom App",
    details={"custom_field": "value"}
)
```

## 🔧 Configuración Avanzada

### Base de Datos

```python
# Crear tablas necesarias
from src.security.config import DatabaseConfig

# Obtener DDL para auditoría
audit_tables = DatabaseConfig.get_audit_tables()
for table_name, ddl in audit_tables.items():
    print(f"CREATE TABLE {table_name}:\n{ddl}\n")
```

### Redis para Caching

```python
# Configuración para sesiones y rate limiting
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=optional_password
REDIS_DB=0

# El sistema usa Redis automáticamente para:
# - Rate limiting
# - Cache de sesiones
# - Storage de códigos MFA temporales
# - Cache de tokens SSO
```

## 🚨 Seguridad y Cumplimiento

### Medidas Implementadas

- ✅ **Encriptación** de datos sensibles
- ✅ **Hashing** seguro de contraseñas
- ✅ **Rate limiting** para prevenir ataques
- ✅ **Input validation** y sanitización
- ✅ **Security headers** automáticos
- ✅ **Audit logging** completo
- ✅ **Session management** seguro
- ✅ **Token rotation** automática

### Compliance

- ✅ **OWASP Top 10** mitigations
- ✅ **GDPR** compliant audit logs
- ✅ **SOC 2** compatible controls
- ✅ **NIST** security framework
- ✅ **ISO 27001** security standards

## 🧪 Testing

### Pruebas Unitarias

```python
import pytest
from src.security import auth_system

@pytest.mark.asyncio
async def test_user_authentication():
    # Crear usuario de prueba
    user = await auth_system.create_user(
        username="testuser",
        email="test@example.com",
        password_hash=security_hasher.hash_password("TestPass123!"),
        roles=["user"]
    )
    
    # Autenticar
    result = await auth_system.authenticate(
        username="testuser",
        password="TestPass123!"
    )
    
    assert result["success"] is True
    assert result["user"]["username"] == "testuser"
```

### Pruebas de Integración

```bash
# Ejecutar pruebas del sistema de seguridad
pytest tests/security/ -v --cov=src/security/

# Tests específicos
pytest tests/security/test_auth_system.py -v
pytest tests/security/test_middleware.py -v
pytest tests/security/test_mfa.py -v
```

## 📚 Documentación Adicional

- [Configuración LDAP](docs/ldap-config.md)
- [Setup OAuth Providers](docs/oauth-setup.md)
- [MFA Implementation Guide](docs/mfa-guide.md)
- [RBAC Best Practices](docs/rbac-guide.md)
- [Security Audit Guide](docs/audit-guide.md)

## 🤝 Contribución

Para contribuir al sistema de seguridad:

1. Seguir las mejores prácticas de seguridad
2. Incluir tests para nuevas funcionalidades
3. Documentar cambios de seguridad
4. Validar con herramientas de análisis estático
5. Revisar compliance con estándares

## 📄 Licencia

Este sistema forma parte de MCP Core Superior y está sujeto a la misma licencia del proyecto.

---

**Nota de Seguridad**: Este sistema maneja datos sensibles. Asegúrate de:
- Mantener secretos seguros
- Usar HTTPS en producción
- Configurar apropiadamente la base de datos
- Monitorear logs de auditoría
- Realizar revisiones de seguridad regulares