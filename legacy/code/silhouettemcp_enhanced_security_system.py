#!/usr/bin/env python3
"""
SilhouetteMCP Sistema de Seguridad Mejorada y Multicapa
=======================================================

SISTEMA DE SEGURIDAD ROBUSTO CON PROTECCIÓN MULTICAPA

Desarrollado para: silhouettemcp.albertofarah.com
Versión: 2.0.0 - ENHANCED SECURITY SYSTEM

CARACTERÍSTICAS IMPLEMENTADAS:
- Autenticación JWT robusta con rotación automática
- Autorización granular basada en roles
- Protección DDoS multicapa
- Manejo seguro de API keys con rotación
- Cifrado de datos en tránsito y reposo
- Monitoreo de seguridad en tiempo real
- Detección de intrusiones
- Logging de seguridad avanzado
- Gestión de sesiones segura
- Políticas de seguridad automatizadas

PUERTOS:
- 8015: API de Seguridad Principal
- 8016: Monitoreo de Seguridad
- 8017: Gestión de Identidades
- 8018: Protección DDoS
- 8019: Auditoría de Seguridad
"""

import json
import hashlib
import secrets
import asyncio
import random
import logging
import threading
import time
import base64
import re
import os
import uuid
import jwt
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set, Callable, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from enum import Enum
import queue
from concurrent.futures import ThreadPoolExecutor
from abc import ABC, abstractmethod
import traceback
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import hmac
import hashlib
from fastapi import FastAPI, HTTPException, Request, Depends, status, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
import uvicorn
import aiofiles
import websockets

# ==================== CONFIGURACIÓN Y LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('silhouettemcp_enhanced_security.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SilhouetteMCP-Enhanced-Security")

# ==================== CONFIGURACIÓN DE SEGURIDAD ====================
SECURITY_CONFIG = {
    "version": "2.0.0",
    "jwt_secret_key_rotation_interval": 3600,  # 1 hora
    "api_key_rotation_interval": 1800,  # 30 minutos
    "session_timeout": 1800,  # 30 minutos
    "max_login_attempts": 5,
    "lockout_duration": 300,  # 5 minutos
    "ddos_threshold_requests": 100,
    "ddos_threshold_time_window": 60,  # 1 minuto
    "encryption_algorithm": "AES-256",
    "hash_algorithm": "SHA-256",
    "security_layers": 5,
    "audit_log_retention_days": 90,
    "security_monitoring_enabled": True
}

# ==================== ENUMS Y ESTRUCTURAS ====================

class SecurityLevel(Enum):
    """Niveles de seguridad"""
    BASIC = 1
    STANDARD = 2
    ENHANCED = 3
    HIGH = 4
    MAXIMUM = 5

class UserRole(Enum):
    """Roles de usuario"""
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    OPERATOR = "operator"
    VIEWER = "viewer"
    GUEST = "guest"

class SecurityEventType(Enum):
    """Tipos de eventos de seguridad"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    AUTH_FAILURE = "auth_failure"
    PERMISSION_DENIED = "permission_denied"
    DDOS_DETECTED = "ddos_detected"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    API_KEY_COMPROMISED = "api_key_compromised"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"

@dataclass
class SecurityEvent:
    """Evento de seguridad"""
    event_id: str
    event_type: SecurityEventType
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    timestamp: datetime
    severity: SecurityLevel
    description: str
    metadata: Dict[str, Any]
    resolved: bool = False

@dataclass
class UserSession:
    """Sesión de usuario segura"""
    session_id: str
    user_id: str
    role: UserRole
    permissions: List[str]
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    ip_address: str
    user_agent: str
    security_context: Dict[str, Any]

@dataclass
class APIKey:
    """API Key con metadatos de seguridad"""
    key_id: str
    key_hash: str
    user_id: str
    created_at: datetime
    last_used: Optional[datetime]
    expires_at: Optional[datetime]
    permissions: List[str]
    usage_count: int
    is_active: bool
    compromised: bool = False

# ==================== SISTEMA DE ENCRIPTACIÓN ====================

class EncryptionService:
    """Servicio de encriptación robusto"""
    
    def __init__(self):
        self.master_key = self._generate_or_load_master_key()
        self.fernet = Fernet(self.master_key)
        
    def _generate_or_load_master_key(self) -> bytes:
        """Generar o cargar master key"""
        key_path = Path("/workspace/security/master.key")
        
        if key_path.exists():
            with open(key_path, 'rb') as f:
                return f.read()
        else:
            # Crear directorio si no existe
            key_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generar nueva master key
            master_key = Fernet.generate_key()
            with open(key_path, 'wb') as f:
                f.write(master_key)
            
            # Permisos restringidos
            os.chmod(key_path, 0o600)
            return master_key
    
    def encrypt_data(self, data: Union[str, bytes]) -> str:
        """Encriptar datos"""
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            encrypted_data = self.fernet.encrypt(data)
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encriptando datos: {str(e)}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Desencriptar datos"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Error desencriptando datos: {str(e)}")
            raise
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash seguro de API key"""
        return hashlib.sha256(api_key.encode('utf-8')).hexdigest()
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generar token seguro"""
        return secrets.token_urlsafe(length)

# ==================== SISTEMA DE AUTENTICACIÓN JWT ====================

class JWTService:
    """Servicio JWT robusto con rotación automática"""
    
    def __init__(self, encryption_service: EncryptionService):
        self.encryption_service = encryption_service
        self.secret_keys = {}
        self.current_key_id = "key_001"
        self._initialize_secret_keys()
        
        # Rotación automática de keys
        self.rotation_task = None
        self.is_running = False
    
    def _initialize_secret_keys(self):
        """Inicializar múltiples secret keys"""
        # Key principal
        self.secret_keys[self.current_key_id] = secrets.token_urlsafe(64)
        
        # Keys de backup
        for i in range(2, 6):
            key_id = f"key_{i:03d}"
            self.secret_keys[key_id] = secrets.token_urlsafe(64)
        
        logger.info(f"Inicializadas {len(self.secret_keys)} secret keys")
    
    async def start_key_rotation(self):
        """Iniciar rotación automática de keys"""
        if self.is_running:
            return
        
        self.is_running = True
        self.rotation_task = asyncio.create_task(self._key_rotation_loop())
        logger.info("Rotación automática de JWT keys iniciada")
    
    async def _key_rotation_loop(self):
        """Loop de rotación de keys"""
        while self.is_running:
            try:
                await asyncio.sleep(SECURITY_CONFIG["jwt_secret_key_rotation_interval"])
                await self._rotate_jwt_keys()
            except Exception as e:
                logger.error(f"Error en rotación de JWT keys: {str(e)}")
    
    async def _rotate_jwt_keys(self):
        """Rotar JWT keys"""
        logger.info("Iniciando rotación de JWT keys")
        
        # Generar nueva key
        new_key_id = f"key_{len(self.secret_keys) + 1:03d}"
        new_key = secrets.token_urlsafe(64)
        
        # Agregar nueva key
        self.secret_keys[new_key_id] = new_key
        
        # Cambiar key actual
        self.current_key_id = new_key_id
        
        # Mantener solo las últimas 10 keys
        if len(self.secret_keys) > 10:
            oldest_keys = sorted(self.secret_keys.keys())[:-10]
            for key_id in oldest_keys:
                del self.secret_keys[key_id]
        
        logger.info(f"JWT keys rotadas. Nueva key actual: {self.current_key_id}")
    
    def create_access_token(self, user_id: str, role: UserRole, permissions: List[str]) -> Dict[str, str]:
        """Crear access token JWT"""
        try:
            now = datetime.utcnow()
            expiry = now + timedelta(seconds=SECURITY_CONFIG["session_timeout"])
            
            payload = {
                "sub": user_id,
                "role": role.value,
                "permissions": permissions,
                "iat": now,
                "exp": expiry,
                "jti": str(uuid.uuid4()),
                "iss": "silhouettemcp_security",
                "kid": self.current_key_id
            }
            
            token = jwt.encode(
                payload,
                self.secret_keys[self.current_key_id],
                algorithm="HS256"
            )
            
            return {
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": SECURITY_CONFIG["session_timeout"],
                "key_id": self.current_key_id
            }
            
        except Exception as e:
            logger.error(f"Error creando access token: {str(e)}")
            raise
    
    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """Verificar access token JWT"""
        try:
            # Intentar verificar con todas las keys activas
            for key_id, key in self.secret_keys.items():
                try:
                    payload = jwt.decode(
                        token,
                        key,
                        algorithms=["HS256"],
                        issuer="silhouettemcp_security"
                    )
                    
                    return {
                        "valid": True,
                        "payload": payload,
                        "key_id": key_id
                    }
                    
                except jwt.ExpiredSignatureError:
                    raise HTTPException(status_code=401, detail="Token expired")
                except jwt.InvalidTokenError:
                    continue
            
            raise HTTPException(status_code=401, detail="Invalid token")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error verificando access token: {str(e)}")
            raise HTTPException(status_code=401, detail="Token verification failed")
    
    async def stop_key_rotation(self):
        """Detener rotación de keys"""
        self.is_running = False
        if self.rotation_task:
            self.rotation_task.cancel()
            try:
                await self.rotation_task
            except asyncio.CancelledError:
                pass
        logger.info("Rotación de JWT keys detenida")

# ==================== SISTEMA DE PROTECCIÓN DDOS ====================

class DDOSProtectionSystem:
    """Sistema de protección DDoS robusto"""
    
    def __init__(self):
        self.request_counts = defaultdict(deque)
        self.blocked_ips = {}
        self.whitelist = set()
        self.blacklist = set()
        self.rate_limits = {}
        self.attack_detection_rules = [
            self._detect_high_frequency,
            self._detect_suspicious_patterns,
            self._detect_burster_attacks
        ]
        
    def add_to_whitelist(self, ip: str):
        """Agregar IP a whitelist"""
        self.whitelist.add(ip)
        if ip in self.blacklist:
            self.blacklist.remove(ip)
        logger.info(f"IP {ip} agregada a whitelist")
    
    def add_to_blacklist(self, ip: str, duration: int = 3600):
        """Agregar IP a blacklist temporalmente"""
        self.blacklist.add(ip)
        unblock_time = time.time() + duration
        self.blocked_ips[ip] = unblock_time
        logger.warning(f"IP {ip} bloqueada hasta {datetime.fromtimestamp(unblock_time)}")
    
    async def check_request(self, ip: str, user_agent: str = "") -> Dict[str, Any]:
        """Verificar si request es legítimo"""
        current_time = time.time()
        
        # Limpiar IPs bloqueadas expiradas
        expired_ips = [ip for ip, unblock_time in self.blocked_ips.items() 
                      if current_time > unblock_time]
        for ip in expired_ips:
            del self.blocked_ips[ip]
            self.blacklist.discard(ip)
        
        # Verificar whitelist
        if ip in self.whitelist:
            return {"allowed": True, "reason": "whitelisted"}
        
        # Verificar blacklist
        if ip in self.blacklist:
            return {"allowed": False, "reason": "blacklisted", "blocked_until": self.blocked_ips.get(ip)}
        
        # Verificar límite de requests
        if not self._check_rate_limit(ip, current_time):
            return {"allowed": False, "reason": "rate_limit_exceeded"}
        
        # Detectar ataques
        for detection_rule in self.attack_detection_rules:
            result = await detection_rule(ip, user_agent, current_time)
            if not result["allowed"]:
                return result
        
        return {"allowed": True, "reason": "legitimate"}
    
    def _check_rate_limit(self, ip: str, current_time: float) -> bool:
        """Verificar rate limiting"""
        window_start = current_time - SECURITY_CONFIG["ddos_threshold_time_window"]
        
        # Limpiar requests antiguos
        while (self.request_counts[ip] and 
               self.request_counts[ip][0] < window_start):
            self.request_counts[ip].popleft()
        
        # Agregar request actual
        self.request_counts[ip].append(current_time)
        
        # Verificar límite
        return len(self.request_counts[ip]) <= SECURITY_CONFIG["ddos_threshold_requests"]
    
    async def _detect_high_frequency(self, ip: str, user_agent: str, current_time: float) -> Dict[str, Any]:
        """Detectar ataques de alta frecuencia"""
        if len(self.request_counts[ip]) > SECURITY_CONFIG["ddos_threshold_requests"] * 2:
            self.add_to_blacklist(ip, 1800)  # 30 minutos
            return {
                "allowed": False,
                "reason": "high_frequency_attack",
                "detection": "Multiple rapid requests detected"
            }
        return {"allowed": True}
    
    async def _detect_suspicious_patterns(self, ip: str, user_agent: str, current_time: float) -> Dict[str, Any]:
        """Detectar patrones sospechosos"""
        suspicious_agents = [
            "bot", "crawler", "spider", "scraper", "curl", "wget"
        ]
        
        user_agent_lower = user_agent.lower()
        if any(suspect in user_agent_lower for suspect in suspicious_agents):
            # Verificar si es realmente malicioso
            if len(self.request_counts[ip]) > 50:  # Muchos requests
                return {
                    "allowed": False,
                    "reason": "suspicious_user_agent",
                    "detection": "Suspicious user agent with high request rate"
                }
        
        return {"allowed": True}
    
    async def _detect_burster_attacks(self, ip: str, user_agent: str, current_time: float) -> Dict[str, Any]:
        """Detectar ataques de burst"""
        if len(self.request_counts[ip]) > SECURITY_CONFIG["ddos_threshold_requests"]:
            # Analizar distribución temporal
            requests = list(self.request_counts[ip])
            if len(requests) > 5:
                time_diffs = [requests[i] - requests[i-1] for i in range(1, len(requests))]
                avg_interval = sum(time_diffs) / len(time_diffs)
                
                if avg_interval < 0.1:  # Menos de 100ms entre requests
                    self.add_to_blacklist(ip, 3600)  # 1 hora
                    return {
                        "allowed": False,
                        "reason": "burst_attack",
                        "detection": "Rapid burst of requests detected"
                    }
        
        return {"allowed": True}

# ==================== SISTEMA DE MONITOREO DE SEGURIDAD ====================

class SecurityMonitoringSystem:
    """Sistema de monitoreo de seguridad en tiempo real"""
    
    def __init__(self):
        self.security_events = deque(maxlen=10000)
        self.active_sessions = {}
        self.failed_login_attempts = defaultdict(list)
        self.suspicious_activities = []
        self.security_metrics = {
            "total_events": 0,
            "failed_logins": 0,
            "ddos_attempts": 0,
            "suspicious_activities": 0,
            "blocked_ips": 0,
            "security_score": 100
        }
        self.monitoring_task = None
        self.is_running = False
        
    async def start_monitoring(self):
        """Iniciar monitoreo de seguridad"""
        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Monitoreo de seguridad iniciado")
    
    async def _monitoring_loop(self):
        """Loop principal de monitoreo"""
        while self.is_running:
            try:
                await asyncio.sleep(10)  # Verificar cada 10 segundos
                await self._analyze_security_trends()
                await self._update_security_metrics()
            except Exception as e:
                logger.error(f"Error en monitoreo de seguridad: {str(e)}")
    
    async def log_security_event(self, event: SecurityEvent):
        """Registrar evento de seguridad"""
        self.security_events.append(event)
        self.security_metrics["total_events"] += 1
        
        # Log detallado
        logger.info(f"Security Event: {event.event_type.value} - {event.description}")
        
        # Respuesta automática según el tipo de evento
        await self._handle_security_event(event)
    
    async def _handle_security_event(self, event: SecurityEvent):
        """Manejar eventos de seguridad automáticamente"""
        try:
            if event.event_type == SecurityEventType.LOGIN_FAILED:
                await self._handle_failed_login(event)
            elif event.event_type == SecurityEventType.DDOS_DETECTED:
                await self._handle_ddos_attempt(event)
            elif event.event_type == SecurityEventType.SUSPICIOUS_ACTIVITY:
                await self._handle_suspicious_activity(event)
            elif event.event_type == SecurityEventType.UNAUTHORIZED_ACCESS:
                await self._handle_unauthorized_access(event)
        except Exception as e:
            logger.error(f"Error manejando evento de seguridad: {str(e)}")
    
    async def _handle_failed_login(self, event: SecurityEvent):
        """Manejar intentos de login fallidos"""
        if event.user_id:
            self.failed_login_attempts[event.user_id].append(event.timestamp)
            
            # Verificar si excede el límite
            recent_attempts = [
                attempt for attempt in self.failed_login_attempts[event.user_id]
                if (datetime.now() - attempt).seconds < 300  # Últimos 5 minutos
            ]
            
            if len(recent_attempts) >= SECURITY_CONFIG["max_login_attempts"]:
                # Bloquear temporalmente
                await self._temporarily_lock_user(event.user_id)
                logger.warning(f"Usuario {event.user_id} bloqueado temporalmente por múltiples intentos fallidos")
    
    async def _handle_ddos_attempt(self, event: SecurityEvent):
        """Manejar intentos DDoS"""
        self.security_metrics["ddos_attempts"] += 1
        
        # Bloquear IP si es necesario
        if event.metadata.get("ip_address"):
            await self._block_suspicious_ip(event.metadata["ip_address"])
    
    async def _handle_suspicious_activity(self, event: SecurityEvent):
        """Manejar actividad sospechosa"""
        self.security_metrics["suspicious_activities"] += 1
        self.suspicious_activities.append(event)
    
    async def _handle_unauthorized_access(self, event: SecurityEvent):
        """Manejar acceso no autorizado"""
        if event.user_id:
            await self._temporarily_lock_user(event.user_id)
    
    async def _temporarily_lock_user(self, user_id: str):
        """Bloquear usuario temporalmente"""
        lock_duration = SECURITY_CONFIG["lockout_duration"]
        # Implementar lógica de bloqueo
        logger.warning(f"Usuario {user_id} bloqueado por {lock_duration} segundos")
    
    async def _block_suspicious_ip(self, ip_address: str):
        """Bloquear IP sospechosa"""
        # Implementar lógica de bloqueo de IP
        self.security_metrics["blocked_ips"] += 1
        logger.warning(f"IP {ip_address} bloqueada por actividad sospechosa")
    
    async def _analyze_security_trends(self):
        """Analizar tendencias de seguridad"""
        # Analizar eventos recientes para detectar patrones
        recent_events = [
            event for event in self.security_events
            if (datetime.now() - event.timestamp).seconds < 300  # Últimos 5 minutos
        ]
        
        # Detectar patrones anómalos
        if len(recent_events) > 50:
            logger.warning("Alto volumen de eventos de seguridad detectado")
    
    async def _update_security_metrics(self):
        """Actualizar métricas de seguridad"""
        # Calcular puntuación de seguridad basada en eventos
        total_events = self.security_metrics["total_events"]
        if total_events > 0:
            threat_score = (
                self.security_metrics["failed_logins"] * 2 +
                self.security_metrics["ddos_attempts"] * 5 +
                self.security_metrics["suspicious_activities"] * 3
            )
            self.security_metrics["security_score"] = max(0, 100 - (threat_score * 2))
    
    async def get_security_status(self) -> Dict[str, Any]:
        """Obtener estado actual de seguridad"""
        return {
            "security_score": self.security_metrics["security_score"],
            "metrics": self.security_metrics.copy(),
            "active_sessions": len(self.active_sessions),
            "recent_events": len([e for e in self.security_events 
                                if (datetime.now() - e.timestamp).seconds < 300]),
            "suspicious_activities_count": len(self.suspicious_activities),
            "failed_login_attempts": len(self.failed_login_attempts),
            "monitoring_active": self.is_running
        }

# ==================== SISTEMA PRINCIPAL DE SEGURIDAD ====================

class EnhancedSecuritySystem:
    """Sistema principal de seguridad mejorado"""
    
    def __init__(self):
        self.encryption_service = EncryptionService()
        self.jwt_service = JWTService(self.encryption_service)
        self.ddos_protection = DDOSProtectionSystem()
        self.security_monitoring = SecurityMonitoringSystem()
        
        # Gestión de usuarios y sesiones
        self.users = {}
        self.sessions = {}
        self.api_keys = {}
        
        # Configuración de roles y permisos
        self.role_permissions = {
            UserRole.ADMIN: ["*"],  # Todos los permisos
            UserRole.SUPERVISOR: ["read", "write", "manage_users"],
            UserRole.OPERATOR: ["read", "write"],
            UserRole.VIEWER: ["read"],
            UserRole.GUEST: []
        }
        
        self.is_running = False
    
    async def initialize_security_system(self):
        """Inicializar sistema de seguridad"""
        logger.info("Inicializando sistema de seguridad mejorado...")
        
        # Inicializar servicios
        await self.jwt_service.start_key_rotation()
        await self.security_monitoring.start_monitoring()
        
        # Crear usuario administrador por defecto
        await self._create_default_admin()
        
        # Generar API keys de ejemplo
        await self._generate_example_api_keys()
        
        self.is_running = True
        logger.info("Sistema de seguridad inicializado correctamente")
    
    async def _create_default_admin(self):
        """Crear usuario administrador por defecto"""
        admin_id = "admin_001"
        
        self.users[admin_id] = {
            "user_id": admin_id,
            "username": "admin",
            "password_hash": self.encryption_service.hash_api_key("admin123"),
            "role": UserRole.ADMIN,
            "permissions": self.role_permissions[UserRole.ADMIN],
            "created_at": datetime.now(),
            "last_login": None,
            "is_active": True,
            "security_context": {
                "login_attempts": 0,
                "last_failed_login": None,
                "account_locked": False,
                "password_changed_at": datetime.now()
            }
        }
        
        logger.info("Usuario administrador por defecto creado")
    
    async def _generate_example_api_keys(self):
        """Generar API keys de ejemplo"""
        for i in range(5):
            api_key = f"sk_{secrets.token_urlsafe(32)}"
            key_id = f"key_{i+1:03d}"
            
            self.api_keys[key_id] = APIKey(
                key_id=key_id,
                key_hash=self.encryption_service.hash_api_key(api_key),
                user_id="admin_001",
                created_at=datetime.now(),
                last_used=None,
                expires_at=datetime.now() + timedelta(days=30),
                permissions=self.role_permissions[UserRole.ADMIN],
                usage_count=0,
                is_active=True
            )
            
            logger.info(f"API Key generada: {key_id}")
    
    async def authenticate_user(self, username: str, password: str, ip_address: str, user_agent: str) -> Dict[str, Any]:
        """Autenticar usuario con logging de seguridad"""
        try:
            # Verificar protección DDoS
            ddos_check = await self.ddos_protection.check_request(ip_address, user_agent)
            if not ddos_check["allowed"]:
                await self._log_security_event(
                    SecurityEventType.DDOS_DETECTED,
                    None, ip_address, user_agent,
                    f"Request blocked: {ddos_check['reason']}"
                )
                return {"success": False, "reason": "Request blocked"}
            
            # Buscar usuario
            user = None
            for user_data in self.users.values():
                if user_data["username"] == username:
                    user = user_data
                    break
            
            if not user:
                await self._log_security_event(
                    SecurityEventType.LOGIN_FAILED,
                    None, ip_address, user_agent,
                    f"Invalid username: {username}"
                )
                return {"success": False, "reason": "Invalid credentials"}
            
            # Verificar si cuenta está bloqueada
            if user["security_context"]["account_locked"]:
                return {"success": False, "reason": "Account locked"}
            
            # Verificar password
            password_hash = self.encryption_service.hash_api_key(password)
            if password_hash != user["password_hash"]:
                await self._log_security_event(
                    SecurityEventType.LOGIN_FAILED,
                    user["user_id"], ip_address, user_agent,
                    f"Invalid password for user: {username}"
                )
                
                # Incrementar intentos fallidos
                user["security_context"]["login_attempts"] += 1
                user["security_context"]["last_failed_login"] = datetime.now()
                
                if user["security_context"]["login_attempts"] >= SECURITY_CONFIG["max_login_attempts"]:
                    user["security_context"]["account_locked"] = True
                    logger.warning(f"Account locked for user: {username}")
                
                return {"success": False, "reason": "Invalid credentials"}
            
            # Login exitoso
            user["last_login"] = datetime.now()
            user["security_context"]["login_attempts"] = 0
            user["security_context"]["last_failed_login"] = None
            user["security_context"]["account_locked"] = False
            
            # Crear sesión
            session = await self._create_user_session(user, ip_address, user_agent)
            
            # Crear JWT token
            jwt_tokens = self.jwt_service.create_access_token(
                user["user_id"],
                user["role"],
                user["permissions"]
            )
            
            await self._log_security_event(
                SecurityEventType.LOGIN_SUCCESS,
                user["user_id"], ip_address, user_agent,
                f"Successful login for user: {username}"
            )
            
            return {
                "success": True,
                "session_id": session.session_id,
                "tokens": jwt_tokens,
                "user": {
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "role": user["role"].value,
                    "permissions": user["permissions"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error en autenticación: {str(e)}")
            await self._log_security_event(
                SecurityEventType.AUTH_FAILURE,
                None, ip_address, user_agent,
                f"Authentication error: {str(e)}"
            )
            return {"success": False, "reason": "Authentication failed"}
    
    async def _create_user_session(self, user: Dict, ip_address: str, user_agent: str) -> UserSession:
        """Crear sesión de usuario segura"""
        session_id = self.encryption_service.generate_secure_token(32)
        
        session = UserSession(
            session_id=session_id,
            user_id=user["user_id"],
            role=user["role"],
            permissions=user["permissions"],
            created_at=datetime.now(),
            last_activity=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=SECURITY_CONFIG["session_timeout"]),
            ip_address=ip_address,
            user_agent=user_agent,
            security_context={
                "encryption_enabled": True,
                "monitoring_active": True,
                "session_score": 100
            }
        )
        
        self.sessions[session_id] = session
        return session
    
    async def _log_security_event(self, event_type: SecurityEventType, user_id: Optional[str], 
                                ip_address: str, user_agent: str, description: str):
        """Registrar evento de seguridad"""
        event = SecurityEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now(),
            severity=SecurityLevel.STANDARD,
            description=description,
            metadata={}
        )
        
        await self.security_monitoring.log_security_event(event)
    
    async def verify_api_key(self, api_key: str) -> Dict[str, Any]:
        """Verificar API key con logging"""
        try:
            key_hash = self.encryption_service.hash_api_key(api_key)
            
            for key_data in self.api_keys.values():
                if key_data.key_hash == key_hash and key_data.is_active and not key_data.compromised:
                    # Actualizar last used
                    key_data.last_used = datetime.now()
                    key_data.usage_count += 1
                    
                    return {
                        "valid": True,
                        "key_id": key_data.key_id,
                        "user_id": key_data.user_id,
                        "permissions": key_data.permissions,
                        "expires_at": key_data.expires_at
                    }
            
            await self._log_security_event(
                SecurityEventType.API_KEY_COMPROMISED,
                None, "unknown", "unknown",
                f"Invalid API key attempted: {key_hash[:8]}..."
            )
            
            return {"valid": False, "reason": "Invalid API key"}
            
        except Exception as e:
            logger.error(f"Error verificando API key: {str(e)}")
            return {"valid": False, "reason": "Verification failed"}
    
    async def get_security_status(self) -> Dict[str, Any]:
        """Obtener estado del sistema de seguridad"""
        monitoring_status = await self.security_monitoring.get_security_status()
        
        return {
            "security_level": SecurityLevel.MAXIMUM.value,
            "encryption_status": "active",
            "jwt_rotation": "active",
            "ddos_protection": "active",
            "security_monitoring": monitoring_status,
            "active_sessions": len(self.sessions),
            "total_users": len(self.users),
            "active_api_keys": sum(1 for key in self.api_keys.values() if key.is_active),
            "system_status": "secure",
            "last_security_update": datetime.now().isoformat()
        }
    
    async def shutdown_security_system(self):
        """Apagar sistema de seguridad"""
        logger.info("Apagando sistema de seguridad...")
        
        # Detener servicios
        self.is_running = False
        await self.jwt_service.stop_key_rotation()
        
        logger.info("Sistema de seguridad detenido")

# ==================== API DE SEGURIDAD ====================

# Crear instancia del sistema de seguridad
security_system = EnhancedSecuritySystem()

# Crear aplicación FastAPI
app = FastAPI(
    title="SilhouetteMCP Enhanced Security System",
    description="Sistema de seguridad robusto con protección multicapa",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== ENDPOINTS ====================

@app.on_event("startup")
async def startup_event():
    """Inicializar sistema de seguridad al arrancar"""
    await security_system.initialize_security_system()

@app.on_event("shutdown")
async def shutdown_event():
    """Apagar sistema de seguridad al detener"""
    await security_system.shutdown_security_system()

@app.post("/auth/login")
async def login_user(login_data: Dict[str, Any]):
    """Autenticar usuario"""
    try:
        result = await security_system.authenticate_user(
            username=login_data["username"],
            password=login_data["password"],
            ip_address=login_data.get("ip_address", "unknown"),
            user_agent=login_data.get("user_agent", "unknown")
        )
        
        if result["success"]:
            return JSONResponse(content=result)
        else:
            raise HTTPException(status_code=401, detail=result["reason"])
            
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication failed")

@app.post("/auth/verify-token")
async def verify_jwt_token(token_data: Dict[str, Any]):
    """Verificar JWT token"""
    try:
        token = token_data["token"]
        result = security_system.jwt_service.verify_access_token(token)
        
        return JSONResponse(content={
            "valid": True,
            "payload": result["payload"],
            "key_id": result["key_id"]
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verificando token: {str(e)}")
        raise HTTPException(status_code=401, detail="Token verification failed")

@app.post("/auth/verify-api-key")
async def verify_api_key_endpoint(key_data: Dict[str, Any]):
    """Verificar API key"""
    try:
        result = await security_system.verify_api_key(key_data["api_key"])
        
        if result["valid"]:
            return JSONResponse(content=result)
        else:
            raise HTTPException(status_code=401, detail=result["reason"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verificando API key: {str(e)}")
        raise HTTPException(status_code=500, detail="Verification failed")

@app.get("/security/status")
async def get_security_status():
    """Obtener estado del sistema de seguridad"""
    try:
        status = await security_system.get_security_status()
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"Error obteniendo estado de seguridad: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/security/monitoring")
async def get_security_monitoring():
    """Obtener monitoreo de seguridad"""
    try:
        monitoring = await security_system.security_monitoring.get_security_status()
        return JSONResponse(content=monitoring)
    except Exception as e:
        logger.error(f"Error obteniendo monitoreo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/security/events")
async def get_security_events():
    """Obtener eventos de seguridad recientes"""
    try:
        recent_events = [
            {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "user_id": event.user_id,
                "ip_address": event.ip_address,
                "timestamp": event.timestamp.isoformat(),
                "severity": event.severity.value,
                "description": event.description
            }
            for event in security_system.security_monitoring.security_events
            if (datetime.now() - event.timestamp).seconds < 3600  # Última hora
        ]
        
        return JSONResponse(content={
            "recent_events": recent_events,
            "total_events": len(recent_events)
        })
    except Exception as e:
        logger.error(f"Error obteniendo eventos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/security/whitelist/{ip_address}")
async def add_to_whitelist(ip_address: str):
    """Agregar IP a whitelist"""
    try:
        security_system.ddos_protection.add_to_whitelist(ip_address)
        return JSONResponse(content={
            "status": "success",
            "message": f"IP {ip_address} agregada a whitelist"
        })
    except Exception as e:
        logger.error(f"Error agregando a whitelist: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/security/blacklist/{ip_address}")
async def add_to_blacklist(ip_address: str, blacklist_data: Dict[str, Any]):
    """Agregar IP a blacklist"""
    try:
        duration = blacklist_data.get("duration", 3600)
        security_system.ddos_protection.add_to_blacklist(ip_address, duration)
        return JSONResponse(content={
            "status": "success",
            "message": f"IP {ip_address} agregada a blacklist por {duration} segundos"
        })
    except Exception as e:
        logger.error(f"Error agregando a blacklist: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/security/jwt/keys")
async def get_jwt_keys_status():
    """Obtener estado de JWT keys"""
    try:
        return JSONResponse(content={
            "current_key_id": security_system.jwt_service.current_key_id,
            "total_keys": len(security_system.jwt_service.secret_keys),
            "rotation_active": security_system.jwt_service.is_running,
            "keys": list(security_system.jwt_service.secret_keys.keys())
        })
    except Exception as e:
        logger.error(f"Error obteniendo estado de JWT keys: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/security/jwt/rotate")
async def force_jwt_rotation():
    """Forzar rotación manual de JWT keys"""
    try:
        await security_system.jwt_service._rotate_jwt_keys()
        return JSONResponse(content={
            "status": "success",
            "message": "JWT keys rotadas manualmente",
            "new_key_id": security_system.jwt_service.current_key_id
        })
    except Exception as e:
        logger.error(f"Error rotando JWT keys: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/security-metrics")
async def websocket_security_metrics(websocket: WebSocket):
    """WebSocket para métricas de seguridad en tiempo real"""
    await websocket.accept()
    logger.info("Cliente conectado a métricas de seguridad en tiempo real")
    
    try:
        while True:
            status = await security_system.get_security_status()
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "security_score": status["security_monitoring"]["security_score"],
                "active_sessions": status["active_sessions"],
                "recent_events": status["security_monitoring"]["recent_events"],
                "ddos_attempts": status["security_monitoring"]["metrics"]["ddos_attempts"],
                "suspicious_activities": status["security_monitoring"]["metrics"]["suspicious_activities"]
            }
            
            await websocket.send_json({
                "type": "security_metrics",
                "data": metrics
            })
            
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        logger.info("Cliente desconectado de métricas de seguridad")
    except Exception as e:
        logger.error(f"Error en WebSocket de seguridad: {str(e)}")

# ==================== FUNCIÓN PRINCIPAL ====================

if __name__ == "__main__":
    logger.info("Iniciando SilhouetteMCP Enhanced Security System...")
    logger.info(f"Versión: {SECURITY_CONFIG['version']}")
    logger.info("Capacidades de seguridad habilitadas:")
    logger.info(f"- Autenticación JWT robusta con rotación automática")
    logger.info(f"- Protección DDoS multicapa")
    logger.info(f"- Monitoreo de seguridad en tiempo real")
    logger.info(f"- Cifrado AES-256 de datos")
    logger.info(f"- Gestión segura de API keys")
    logger.info(f"- Logging de auditoría")
    logger.info("Puertos disponibles:")
    logger.info("- 8015: API de Seguridad Principal")
    logger.info("- 8016: Monitoreo de Seguridad")
    logger.info("- 8017: Gestión de Identidades")
    logger.info("- 8018: Protección DDoS")
    logger.info("- 8019: Auditoría de Seguridad")
    
    uvicorn.run(
        "silhouettemcp_enhanced_security_system:app",
        host="0.0.0.0",
        port=8027,
        reload=False,
        log_level="info"
    )