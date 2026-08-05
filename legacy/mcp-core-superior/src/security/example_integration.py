"""
Ejemplo de integración del sistema de Authentication & Authorization con FastAPI
Muestra cómo implementar endpoints protegidos y usar todas las funcionalidades
"""

from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

# Importar sistema de autenticación
from .auth_system import auth_system
from .auth_middleware import (
    AuthMiddleware,
    get_current_user,
    require_permission,
    require_role,
    check_resource_permission
)
from .auth_utils import password_validator, token_manager
from .config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="MCP Core Superior - Sistema de Autenticación",
    description="Ejemplo de integración completa del sistema de auth & authorization",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS.split(','),
    allow_credentials=True,
    allow_methods=settings.CORS_ALLOWED_METHODS.split(','),
    allow_headers=settings.CORS_ALLOWED_HEADERS.split(','),
)

# Agregar middleware de autenticación
app.add_middleware(AuthMiddleware, exclude_paths=[
    "/", "/login", "/register", "/auth/sso",
    "/docs", "/redoc", "/openapi.json",
    "/health", "/public"
])

# Configurar templates
templates = Jinja2Templates(directory="templates")

# Modelos Pydantic
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    phone_number: Optional[str] = None
    roles: Optional[List[str]] = ["user"]

class UserLogin(BaseModel):
    username: str
    password: str
    mfa_token: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class APIKeyCreate(BaseModel):
    permissions: List[str]
    scopes: Optional[List[str]] = []
    expires_days: Optional[int] = 365

class PermissionCheck(BaseModel):
    resource: str
    action: str
    context: Optional[Dict[str, Any]] = {}

# Endpoints públicos (sin autenticación)
@app.get("/")
async def home():
    """Página de inicio"""
    return {
        "message": "Bienvenido al sistema de autenticación MCP Core Superior",
        "status": "online",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check del sistema"""
    auth_health = await auth_system.health_check()
    return {
        "status": "healthy",
        "auth_system": auth_health,
        "timestamp": datetime.now().isoformat()
    }

# Endpoints de autenticación
@app.post("/auth/login")
async def login(credentials: UserLogin, request: Request):
    """Login con username/password"""
    try:
        ip_address = request.client.host if request.client else ""
        user_agent = request.headers.get("User-Agent", "")
        
        result = await auth_system.authenticate(
            username=credentials.username,
            password=credentials.password,
            ip_address=ip_address,
            user_agent=user_agent,
            mfa_token=credentials.mfa_token
        )
        
        if result.get("mfa_required"):
            return {
                "success": False,
                "mfa_required": True,
                "mfa_methods": result["mfa_methods"],
                "message": result["message"]
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error en login: {e}")
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/auth/refresh")
async def refresh_token(data: RefreshTokenRequest):
    """Renovar tokens"""
    try:
        tokens = await auth_system.refresh_tokens(data.refresh_token)
        return tokens
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/auth/register")
async def register(user_data: UserCreate):
    """Registro de nuevo usuario"""
    try:
        # Validar contraseña
        password_validation = password_validator.validate_password(user_data.password)
        if not password_validation["valid"]:
            raise HTTPException(
                status_code=400,
                detail={"password_errors": password_validation["errors"]}
            )
        
        # Validar username
        username_validation = security_validator.validate_username(user_data.username)
        if not username_validation["valid"]:
            raise HTTPException(
                status_code=400,
                detail={"username_errors": username_validation["errors"]}
            )
        
        # Crear usuario
        user = await auth_system.create_user(
            username=user_data.username,
            email=str(user_data.email),
            password_hash=security_hasher.hash_password(user_data.password),
            roles=user_data.roles,
            provider=AuthProvider.LOCAL
        )
        
        # Enviar email de verificación (simulado)
        verification_token = token_manager.generate_email_verification_token(
            user.user_id, user.email
        )
        
        return {
            "success": True,
            "message": "Usuario registrado exitosamente",
            "user_id": user.user_id,
            "verification_token": verification_token  # En producción, no retornar esto
        }
        
    except Exception as e:
        logger.error(f"Error en registro: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/auth/sso/providers")
async def get_sso_providers():
    """Obtener proveedores SSO disponibles"""
    providers = auth_system.get_sso_providers()
    return {"providers": providers}

@app.get("/auth/sso/{provider}")
async def initiate_sso(provider: str, return_url: str = "/"):
    """Iniciar proceso SSO"""
    try:
        redirect_url = auth_system.initiate_sso(provider, return_url)
        return RedirectResponse(url=redirect_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/oauth/{provider}")
async def oauth_login(provider: str, code: str, request: Request):
    """Login OAuth"""
    try:
        ip_address = request.client.host if request.client else ""
        user_agent = request.headers.get("User-Agent", "")
        
        result = await auth_system.oauth_authenticate(
            provider=provider,
            code=code,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error en OAuth {provider}: {e}")
        raise HTTPException(status_code=401, detail=str(e))

# Endpoints de MFA
@app.post("/auth/mfa/totp/setup")
async def setup_totp_mfa(current_user: Dict = Depends(get_current_user)):
    """Configurar TOTP MFA"""
    try:
        mfa_data = await auth_system.enable_totp_mfa(current_user["user_id"])
        return mfa_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/mfa/totp/verify")
async def verify_totp_setup(token: str, current_user: Dict = Depends(get_current_user)):
    """Verificar configuración TOTP"""
    try:
        is_valid = await auth_system.verify_totp_setup(current_user["user_id"], token)
        if is_valid:
            return {"success": True, "message": "TOTP configurado correctamente"}
        else:
            raise HTTPException(status_code=400, detail="Código TOTP incorrecto")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/mfa/sms/send")
async def send_sms_mfa(current_user: Dict = Depends(get_current_user)):
    """Enviar código SMS para MFA"""
    try:
        code = await auth_system.send_sms_verification(current_user["user_id"])
        return {"success": True, "message": "Código SMS enviado"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Endpoints de gestión de usuarios
@app.get("/users/me")
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """Obtener información del usuario actual"""
    return {
        "user": current_user,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/users/me/sessions")
async def get_user_sessions(current_user: Dict = Depends(get_current_user)):
    """Obtener sesiones activas del usuario"""
    sessions = await auth_system.get_active_sessions(current_user["user_id"])
    return {
        "sessions": [
            {
                "session_id": s.session_id,
                "ip_address": s.ip_address,
                "user_agent": s.user_agent,
                "created_at": s.created_at.isoformat(),
                "last_activity": s.last_activity.isoformat(),
                "status": s.status.value
            }
            for s in sessions
        ]
    }

@app.delete("/users/me/sessions/{session_id}")
async def terminate_user_session(
    session_id: str, 
    current_user: Dict = Depends(get_current_user)
):
    """Terminar sesión específica"""
    success = await auth_system.terminate_session(session_id, current_user["user_id"])
    if success:
        return {"success": True, "message": "Sesión terminada"}
    else:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

# Endpoints de gestión de roles y permisos
@app.get("/roles")
async def list_roles(current_user: Dict = Depends(get_current_user)):
    """Listar todos los roles (requiere rol admin)"""
    if "admin" not in current_user["roles"]:
        raise HTTPException(status_code=403, detail="Se requiere rol admin")
    
    roles = []
    for role in auth_system._roles.values():
        roles.append({
            "role_id": role.role_id,
            "name": role.name,
            "description": role.description,
            "permissions": role.permissions,
            "parent_roles": role.parent_roles,
            "active": role.active
        })
    
    return {"roles": roles}

@app.post("/users/{user_id}/roles/{role_name}")
async def assign_role_to_user(
    user_id: str,
    role_name: str,
    current_user: Dict = Depends(get_current_user)
):
    """Asignar rol a usuario (requiere permiso admin)"""
    try:
        await auth_system.assign_role_to_user(user_id, role_name)
        return {"success": True, "message": f"Rol {role_name} asignado al usuario"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/users/{user_id}/roles/{role_name}")
async def remove_role_from_user(
    user_id: str,
    role_name: str,
    current_user: Dict = Depends(get_current_user)
):
    """Quitar rol de usuario (requiere permiso admin)"""
    try:
        await auth_system.remove_role_from_user(user_id, role_name)
        return {"success": True, "message": f"Rol {role_name} quitado del usuario"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Endpoints de autorización
@app.post("/auth/check-permission")
async def check_permission(
    permission_data: PermissionCheck,
    current_user: Dict = Depends(get_current_user)
):
    """Verificar si el usuario tiene permiso para una acción"""
    has_permission = await auth_system.check_permission(
        user_id=current_user["user_id"],
        resource=permission_data.resource,
        action=permission_data.action,
        context=permission_data.context
    )
    
    return {
        "has_permission": has_permission,
        "resource": permission_data.resource,
        "action": permission_data.action
    }

# Endpoints de API Keys
@app.post("/api-keys")
async def create_api_key(
    key_data: APIKeyCreate,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """Crear nueva API Key"""
    try:
        api_key = await auth_system.create_api_key(
            user_id=current_user["user_id"],
            permissions=key_data.permissions,
            scopes=key_data.scopes,
            expires_at=datetime.now() + timedelta(days=key_data.expires_days) if key_data.expires_days else None
        )
        
        # Log de auditoría
        background_tasks.add_task(
            logger.info,
            f"API Key creada para usuario {current_user['user_id']}"
        )
        
        return {
            "success": True,
            "api_key": api_key,  # En producción, mostrar solo una vez
            "message": "API Key creada exitosamente"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Ejemplos de endpoints protegidos con diferentes tipos de autorización
@app.get("/protected/basic")
async def basic_protected_endpoint(current_user: Dict = Depends(get_current_user)):
    """Endpoint protegido con autenticación básica"""
    return {
        "message": "Acceso autorizado",
        "user": current_user["username"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/protected/admin")
async def admin_protected_endpoint(
    current_user: Dict = Depends(require_role("admin"))
):
    """Endpoint protegido que requiere rol admin"""
    return {
        "message": "Acceso de administrador",
        "user": current_user["username"],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/protected/users")
async def create_user_endpoint(
    user_data: UserCreate,
    current_user: Dict = Depends(require_permission("perm_user_create"))
):
    """Endpoint protegido que requiere permiso específico"""
    return {
        "message": "Usuario creado",
        "data": user_data.dict(),
        "created_by": current_user["username"]
    }

@app.get("/protected/resource/{resource_id}")
async def get_resource_endpoint(
    resource_id: str,
    current_user: Dict = Depends(check_resource_permission("resource", "read"))
):
    """Endpoint con verificación de permiso contextual"""
    return {
        "resource_id": resource_id,
        "message": "Recurso accedido",
        "accessed_by": current_user["username"]
    }

# Endpoint para validar API Key
@app.get("/api/protected")
async def api_protected_endpoint(api_key: str):
    """Endpoint que valida API Key"""
    try:
        key_info = await auth_system.validate_api_key(api_key)
        return {
            "message": "API Key válida",
            "key_info": key_info
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# Ejemplo de webhook con validación de firma
@app.post("/webhooks/{webhook_id}")
async def webhook_endpoint(
    webhook_id: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """Ejemplo de webhook con validación de firma"""
    # Obtener signature del header
    signature = request.headers.get("X-Webhook-Signature")
    if not signature:
        raise HTTPException(status_code=401, detail="Signature requerida")
    
    # Leer body
    body = await request.body()
    
    # Validar signature (simplificado)
    expected_signature = hashlib.sha256(
        f"{webhook_id}:{body.decode()}".encode()
    ).hexdigest()
    
    if signature != expected_signature:
        raise HTTPException(status_code=401, detail="Signature inválida")
    
    # Procesar webhook
    background_tasks.add_task(
        logger.info,
        f"Webhook {webhook_id} procesado"
    )
    
    return {"status": "processed"}

# Inicialización del sistema
@app.on_event("startup")
async def startup_event():
    """Inicializar sistema al arrancar"""
    await auth_system.initialize()
    logger.info("Sistema de autenticación inicializado")

@app.on_event("shutdown")
async def shutdown_event():
    """Limpiar al cerrar"""
    await auth_system.cleanup()
    logger.info("Sistema de autenticación cerrado")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "example_integration:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )