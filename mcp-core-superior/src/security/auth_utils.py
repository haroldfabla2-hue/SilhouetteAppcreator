"""
Utilidades para el sistema de Authentication & Authorization
Incluye funciones de validación, hashing, y herramientas de seguridad
"""

import re
import hashlib
import hmac
import secrets
import time
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from passlib.context import CryptContext
from passlib.hash import bcrypt
import bcrypt
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import uuid
import ipaddress

from .config import settings


class PasswordValidator:
    """Validador de contraseñas"""
    
    def __init__(self):
        self.min_length = settings.MIN_PASSWORD_LENGTH
        self.require_complexity = settings.REQUIRE_PASSWORD_COMPLEXITY
        
    def validate_password(self, password: str) -> Dict[str, Union[bool, List[str]]]:
        """Validar contraseña según políticas"""
        errors = []
        
        # Verificar longitud mínima
        if len(password) < self.min_length:
            errors.append(f"La contraseña debe tener al menos {self.min_length} caracteres")
        
        if self.require_complexity:
            # Verificar al menos una minúscula
            if not re.search(r'[a-z]', password):
                errors.append("La contraseña debe contener al menos una letra minúscula")
            
            # Verificar al menos una mayúscula
            if not re.search(r'[A-Z]', password):
                errors.append("La contraseña debe contener al menos una letra mayúscula")
            
            # Verificar al menos un número
            if not re.search(r'\d', password):
                errors.append("La contraseña debe contener al menos un número")
            
            # Verificar al menos un carácter especial
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                errors.append("La contraseña debe contener al menos un carácter especial")
        
        # Verificar que no sea una contraseña común
        common_passwords = [
            "123456", "password", "12345678", "qwerty", "123456789",
            "12345", "1234", "111111", "1234567", "dragon"
        ]
        
        if password.lower() in common_passwords:
            errors.append("La contraseña es demasiado común")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def generate_secure_password(self, length: int = 16) -> str:
        """Generar contraseña segura"""
        # Definir conjuntos de caracteres
        lowercase = "abcdefghijklmnopqrstuvwxyz"
        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        digits = "0123456789"
        special = "!@#$%^&*(),.?\":{}|<>"
        
        # Crear contraseña con al menos un carácter de cada tipo
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special)
        ]
        
        # Agregar caracteres aleatorios hasta alcanzar la longitud deseada
        all_chars = lowercase + uppercase + digits + special
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))
        
        # Mezclar y convertir a string
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)


class TokenManager:
    """Gestor de tokens"""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
    
    def generate_reset_token(self, user_id: str, expires_in_hours: int = 24) -> str:
        """Generar token para reset de contraseña"""
        payload = {
            "user_id": user_id,
            "type": "password_reset",
            "exp": datetime.utcnow() + timedelta(hours=expires_in_hours),
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_reset_token(self, token: str) -> Optional[str]:
        """Verificar token de reset y retornar user_id"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get("type") != "password_reset":
                return None
            
            return payload.get("user_id")
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def generate_email_verification_token(self, user_id: str, email: str) -> str:
        """Generar token para verificación de email"""
        payload = {
            "user_id": user_id,
            "email": email,
            "type": "email_verification",
            "exp": datetime.utcnow() + timedelta(days=7),  # 7 días para verificar email
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_email_token(self, token: str) -> Optional[Dict[str, str]]:
        """Verificar token de email y retornar datos"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get("type") != "email_verification":
                return None
            
            return {
                "user_id": payload.get("user_id"),
                "email": payload.get("email")
            }
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


class SecurityHasher:
    """Hasher de contraseñas y datos sensibles"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def hash_password(self, password: str) -> str:
        """Hashear contraseña"""
        return bcrypt.hash(password.encode('utf-8')).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verificar contraseña"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
    
    def hash_api_key(self, api_key: str) -> str:
        """Hashear API key"""
        salt = secrets.token_bytes(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        key = base64.urlsafe_b64encode(kdf.derive(api_key.encode()))
        return base64.urlsafe_b64encode(salt + key).decode()
    
    def verify_api_key(self, api_key: str, key_hash: str) -> bool:
        """Verificar API key"""
        try:
            decoded_hash = base64.urlsafe_b64decode(key_hash.encode())
            salt = decoded_hash[:16]
            stored_key = decoded_hash[16:]
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000
            )
            computed_key = base64.urlsafe_b64encode(kdf.derive(api_key.encode()))
            
            return hmac.compare_digest(computed_key, stored_key)
        except Exception:
            return False
    
    def hash_sensitive_data(self, data: str, salt: str = None) -> Dict[str, str]:
        """Hashear datos sensibles con salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        salted_data = data + salt
        hash_value = hashlib.sha256(salted_data.encode()).hexdigest()
        
        return {
            "hash": hash_value,
            "salt": salt
        }
    
    def verify_sensitive_data(self, data: str, stored_hash: str, salt: str) -> bool:
        """Verificar datos sensibles"""
        salted_data = data + salt
        computed_hash = hashlib.sha256(salted_data.encode()).hexdigest()
        return hmac.compare_digest(computed_hash, stored_hash)


class DataEncryption:
    """Encriptación de datos sensibles"""
    
    def __init__(self):
        self.encryption_key = settings.ENCRYPTION_KEY.encode() if settings.ENCRYPTION_KEY else None
        if not self.encryption_key:
            # Generar clave temporal para desarrollo
            self.encryption_key = Fernet.generate_key()
            print("Warning: Using generated encryption key. Set ENCRYPTION_KEY in production!")
        
        self.cipher = Fernet(self.encryption_key)
    
    def encrypt(self, data: str) -> str:
        """Encriptar datos"""
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Desencriptar datos"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()


class SecurityValidator:
    """Validador de datos de seguridad"""
    
    @staticmethod
    def validate_username(username: str) -> Dict[str, Union[bool, List[str]]]:
        """Validar nombre de usuario"""
        errors = []
        
        if not username or len(username) < 3:
            errors.append("El nombre de usuario debe tener al menos 3 caracteres")
        
        if len(username) > 50:
            errors.append("El nombre de usuario no puede tener más de 50 caracteres")
        
        if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
            errors.append("El nombre de usuario solo puede contener letras, números, guiones, guiones bajos y puntos")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    @staticmethod
    def validate_email(email: str) -> Dict[str, Union[bool, List[str]]]:
        """Validar email"""
        errors = []
        
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not email:
            errors.append("El email es requerido")
        elif not re.match(email_regex, email):
            errors.append("Formato de email inválido")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validar dirección IP"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_phone_number(phone: str) -> Dict[str, Union[bool, List[str]]]:
        """Validar número de teléfono"""
        errors = []
        
        # Remover espacios y caracteres especiales
        phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Verificar que tenga entre 10 y 15 dígitos
        if not re.match(r'^\+?[1-9]\d{9,14}$', phone):
            errors.append("Formato de número de teléfono inválido")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    @staticmethod
    def sanitize_input(input_str: str, max_length: int = 255) -> str:
        """Sanitizar input del usuario"""
        if not input_str:
            return ""
        
        # Remover caracteres peligrosos
        sanitized = re.sub(r'[<>"\']', '', input_str)
        
        # Truncar a longitud máxima
        sanitized = sanitized[:max_length]
        
        # Remover espacios en blanco al inicio y final
        sanitized = sanitized.strip()
        
        return sanitized


class SessionValidator:
    """Validador de sesiones"""
    
    @staticmethod
    def is_session_valid(session_data: Dict[str, Any]) -> bool:
        """Verificar si una sesión es válida"""
        if not session_data:
            return False
        
        # Verificar expiración
        expires_at = session_data.get("expires_at")
        if expires_at:
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if datetime.now() > expires_at:
                return False
        
        # Verificar estado
        if session_data.get("status") != "active":
            return False
        
        return True
    
    @staticmethod
    def should_extend_session(last_activity: datetime, threshold_minutes: int = 5) -> bool:
        """Determinar si se debe extender la sesión"""
        if not last_activity:
            return False
        
        time_diff = datetime.now() - last_activity
        return time_diff.total_seconds() > (threshold_minutes * 60)


class RateLimiter:
    """Rate limiter simple"""
    
    def __init__(self):
        self.requests = {}
    
    def is_rate_limited(self, identifier: str, max_requests: int, window_seconds: int) -> bool:
        """Verificar si el identificador está limitado por rate"""
        now = time.time()
        window_start = now - window_seconds
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Filtrar requests dentro de la ventana
        requests_in_window = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        if len(requests_in_window) >= max_requests:
            return True
        
        # Agregar request actual
        requests_in_window.append(now)
        self.requests[identifier] = requests_in_window
        
        return False


# Instancias globales de utilidades
password_validator = PasswordValidator()
token_manager = TokenManager()
security_hasher = SecurityHasher()
data_encryption = DataEncryption()
security_validator = SecurityValidator()
session_validator = SessionValidator()
rate_limiter = RateLimiter()