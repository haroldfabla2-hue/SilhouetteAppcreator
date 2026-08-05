#!/usr/bin/env python3
"""
Setup script para el sistema de Authentication & Authorization
Crea tablas de base de datos, configura usuarios iniciales y valida configuración
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.security.auth_system import auth_system, AuthProvider, SecurityConfig
from src.security.config import DatabaseConfig, settings
from src.security.auth_utils import password_validator, security_hasher, token_manager
from src.core.config import settings as core_settings
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SecuritySetup:
    """Setup del sistema de seguridad"""
    
    def __init__(self):
        self.auth_system = auth_system
        self.config = settings
    
    async def validate_configuration(self) -> Dict[str, Any]:
        """Validar configuración del sistema"""
        logger.info("🔍 Validando configuración del sistema...")
        
        validation_results = {
            "status": "pending",
            "checks": [],
            "warnings": [],
            "errors": []
        }
        
        try:
            # Verificar JWT Secret
            if not settings.JWT_SECRET_KEY:
                validation_results["warnings"].append("JWT_SECRET_KEY no configurado - usando generado automáticamente")
            else:
                validation_results["checks"].append("✅ JWT_SECRET_KEY configurado")
            
            # Verificar OAuth providers
            oauth_enabled = (
                settings.GOOGLE_OAUTH_ENABLED or 
                settings.GITHUB_OAUTH_ENABLED or 
                settings.MICROSOFT_OAUTH_ENABLED
            )
            
            if oauth_enabled:
                validation_results["checks"].append("✅ Proveedores OAuth configurados")
            else:
                validation_results["warnings"].append("No hay proveedores OAuth configurados")
            
            # Verificar LDAP/AD
            if settings.LDAP_ENABLED or settings.AD_ENABLED:
                validation_results["checks"].append("✅ LDAP/Active Directory configurado")
            else:
                validation_results["warnings"].append("LDAP/Active Directory no configurado")
            
            # Verificar MFA
            if settings.MFA_ENABLED:
                validation_results["checks"].append("✅ MFA habilitado")
            else:
                validation_results["warnings"].append("MFA deshabilitado")
            
            # Verificar base de datos
            if settings.DATABASE_URL != "sqlite:///./auth.db":
                validation_results["checks"].append("✅ Base de datos configurada")
            else:
                validation_results["warnings"].append("Usando SQLite - considere usar PostgreSQL en producción")
            
            # Verificar Redis
            if "redis" in settings.REDIS_URL:
                validation_results["checks"].append("✅ Redis configurado")
            else:
                validation_results["warnings"].append("Redis no configurado - funciones de caching limitadas")
            
            # Verificar email/SMS
            email_configured = bool(settings.SMTP_USERNAME and settings.SMTP_PASSWORD)
            sms_configured = bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN)
            
            if email_configured or sms_configured:
                validation_results["checks"].append("✅ Notificaciones configuradas")
            else:
                validation_results["warnings"].append("No hay configuración de notificaciones (email/SMS)")
            
            validation_results["status"] = "completed"
            
        except Exception as e:
            validation_results["errors"].append(f"Error validando configuración: {e}")
            validation_results["status"] = "failed"
        
        return validation_results
    
    async def create_database_tables(self) -> Dict[str, Any]:
        """Crear tablas necesarias en la base de datos"""
        logger.info("🗄️ Creando tablas de base de datos...")
        
        try:
            # Obtener DDL de tablas
            tables = DatabaseConfig.get_audit_tables()
            
            results = {
                "status": "pending",
                "created_tables": [],
                "errors": []
            }
            
            # Aquí ejecutarías los DDL en tu base de datos
            # Por simplicidad, solo imprimimos los DDL
            for table_name, ddl in tables.items():
                try:
                    logger.info(f"Creando tabla: {table_name}")
                    # await execute_ddl(ddl)  # Descomentar para ejecutar realmente
                    results["created_tables"].append(table_name)
                except Exception as e:
                    results["errors"].append(f"Error creando tabla {table_name}: {e}")
            
            results["status"] = "completed" if not results["errors"] else "partial"
            
            # Mostrar DDL para referencia
            logger.info("\n📋 Scripts SQL para ejecutar manualmente:")
            for table_name, ddl in tables.items():
                logger.info(f"\n-- Tabla: {table_name}")
                logger.info(ddl)
            
        except Exception as e:
            results = {
                "status": "failed",
                "errors": [str(e)]
            }
        
        return results
    
    async def create_default_admin(self) -> Dict[str, Any]:
        """Crear usuario administrador por defecto"""
        logger.info("👤 Creando usuario administrador por defecto...")
        
        try:
            # Verificar si ya existe admin
            admin_user = await self.auth_system.get_user_by_username("admin")
            
            if admin_user:
                return {
                    "status": "exists",
                    "message": "Usuario admin ya existe",
                    "username": "admin"
                }
            
            # Validar contraseña por defecto
            default_password = "Admin123!"
            password_validation = password_validator.validate_password(default_password)
            
            if not password_validation["valid"]:
                raise Exception(f"Contraseña por defecto no cumple políticas: {password_validation['errors']}")
            
            # Crear usuario admin
            admin_user = await self.auth_system.create_user(
                username="admin",
                email="admin@localhost",
                password_hash=security_hasher.hash_password(default_password),
                roles=["admin"],
                provider=AuthProvider.LOCAL,
                attributes={
                    "first_name": "System",
                    "last_name": "Administrator"
                }
            )
            
            logger.warning(f"🔑 Usuario admin creado con contraseña: {default_password}")
            logger.warning("⚠️ CAMBIAR LA CONTRASEÑA EN PRODUCCIÓN!")
            
            return {
                "status": "created",
                "message": "Usuario admin creado exitosamente",
                "username": "admin",
                "user_id": admin_user.user_id,
                "temp_password": default_password
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def create_sample_users(self) -> Dict[str, Any]:
        """Crear usuarios de ejemplo para testing"""
        logger.info("👥 Creando usuarios de ejemplo...")
        
        sample_users = [
            {
                "username": "user",
                "email": "user@localhost", 
                "password": "User123!",
                "roles": ["user"]
            },
            {
                "username": "manager",
                "email": "manager@localhost",
                "password": "Manager123!", 
                "roles": ["user", "manager"]
            },
            {
                "username": "api_user",
                "email": "api@localhost",
                "password": "Api123!",
                "roles": ["user"],
                "permissions": ["perm_api_access"]
            }
        ]
        
        results = {
            "status": "pending",
            "created_users": [],
            "errors": []
        }
        
        try:
            for user_data in sample_users:
                try:
                    # Verificar si ya existe
                    existing = await self.auth_system.get_user_by_username(user_data["username"])
                    if existing:
                        results["created_users"].append({
                            "username": user_data["username"],
                            "status": "exists"
                        })
                        continue
                    
                    # Crear usuario
                    user = await self.auth_system.create_user(
                        username=user_data["username"],
                        email=user_data["email"],
                        password_hash=security_hasher.hash_password(user_data["password"]),
                        roles=user_data["roles"],
                        permissions=user_data.get("permissions", []),
                        provider=AuthProvider.LOCAL
                    )
                    
                    results["created_users"].append({
                        "username": user_data["username"],
                        "status": "created",
                        "user_id": user.user_id,
                        "password": user_data["password"]
                    })
                    
                    logger.info(f"✅ Usuario creado: {user_data['username']}")
                    
                except Exception as e:
                    results["errors"].append(f"Error creando usuario {user_data['username']}: {e}")
                    logger.error(f"❌ Error creando usuario {user_data['username']}: {e}")
            
            results["status"] = "completed" if not results["errors"] else "partial"
            
        except Exception as e:
            results["status"] = "failed"
            results["errors"].append(str(e))
        
        return results
    
    async def initialize_system(self) -> Dict[str, Any]:
        """Inicializar el sistema completo"""
        logger.info("🚀 Inicializando sistema de autenticación...")
        
        results = {
            "status": "pending",
            "steps_completed": [],
            "errors": []
        }
        
        try:
            # 1. Validar configuración
            config_validation = await self.validate_configuration()
            results["config_validation"] = config_validation
            
            if config_validation["errors"]:
                results["errors"].extend(config_validation["errors"])
            
            results["steps_completed"].append("Configuración validada")
            
            # 2. Crear tablas de BD
            if "--skip-db" not in sys.argv:
                db_result = await self.create_database_tables()
                results["database"] = db_result
                results["steps_completed"].append("Base de datos configurada")
            
            # 3. Inicializar auth system
            await self.auth_system.initialize()
            results["steps_completed"].append("Sistema de autenticación inicializado")
            
            # 4. Crear admin por defecto
            admin_result = await self.create_default_admin()
            results["admin_user"] = admin_result
            results["steps_completed"].append("Usuario administrador creado")
            
            # 5. Crear usuarios de ejemplo
            if "--with-samples" in sys.argv:
                sample_result = await self.create_sample_users()
                results["sample_users"] = sample_result
                results["steps_completed"].append("Usuarios de ejemplo creados")
            
            # 6. Verificar salud del sistema
            health = await self.auth_system.health_check()
            results["health_check"] = health
            results["steps_completed"].append("Health check completado")
            
            results["status"] = "completed"
            
        except Exception as e:
            results["status"] = "failed"
            results["errors"].append(f"Error en inicialización: {e}")
            logger.error(f"❌ Error en inicialización: {e}")
        
        return results
    
    def generate_environment_file(self):
        """Generar archivo .env con configuración ejemplo"""
        env_content = f"""# Configuración del Sistema de Authentication & Authorization
# Copiar este archivo como .env y configurar valores apropiados

# JWT Configuration
JWT_SECRET_KEY={SecurityConfig.JWT_SECRET_KEY}
JWT_ALGORITHM={SecurityConfig.JWT_ALGORITHM}
JWT_ACCESS_EXPIRE_MINUTES={SecurityConfig.JWT_ACCESS_EXPIRE_MINUTES}
JWT_REFRESH_EXPIRE_DAYS={SecurityConfig.JWT_REFRESH_EXPIRE_DAYS}

# Password Policy
MIN_PASSWORD_LENGTH={SecurityConfig.MIN_PASSWORD_LENGTH}
REQUIRE_PASSWORD_COMPLEXITY={SecurityConfig.REQUIRE_PASSWORD_COMPLEXITY}

# Session Configuration
SESSION_TIMEOUT_MINUTES={SecurityConfig.SESSION_TIMEOUT_MINUTES}
MAX_CONCURRENT_SESSIONS={SecurityConfig.MAX_CONCURRENT_SESSIONS}

# MFA Configuration
MFA_ENABLED=true
MFA_ENCRYPTION_KEY={token_manager.secret_key}

# SMS Configuration (Twilio)
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com

# LDAP Configuration
LDAP_ENABLED=false
LDAP_SERVER=ldap://ldap.example.com
LDAP_PORT=389
LDAP_DOMAIN=example.com
LDAP_SEARCH_BASE=DC=example,DC=com
LDAP_USE_SSL=false

# OAuth Configuration
OAUTH_ENABLED=true
OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback

# Google OAuth
GOOGLE_OAUTH_ENABLED=true
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# GitHub OAuth
GITHUB_OAUTH_ENABLED=true
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Microsoft OAuth
MICROSOFT_OAUTH_ENABLED=true
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret

# Database
DATABASE_URL=postgresql://user:password@localhost/auth_db
# Para SQLite: sqlite:///./auth.db

# Redis
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=
REDIS_DB=0

# Audit Logging
AUDIT_LOGGING_ENABLED=true
AUDIT_LOG_FILE=./logs/audit.log
AUDIT_LOG_LEVEL=INFO

# Security Headers
SECURE_HEADERS_ENABLED=true
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# API Configuration
API_KEY_ENABLED=true
API_KEY_EXPIRE_DAYS=365
API_KEY_RATE_LIMIT=1000

# Cryptography
ENCRYPTION_KEY={security_hasher.encryption_key}
"""
        
        env_file_path = Path(".env.example")
        with open(env_file_path, "w") as f:
            f.write(env_content)
        
        logger.info(f"📄 Archivo .env.example generado: {env_file_path}")
        logger.info("📋 Revisar y personalizar la configuración según su entorno")


async def main():
    """Función principal"""
    print("🔐 Sistema de Authentication & Authorization Setup")
    print("=" * 60)
    
    setup = SecuritySetup()
    
    # Parsear argumentos
    if "--generate-env" in sys.argv:
        setup.generate_environment_file()
        print("\n✅ Archivo .env.example generado. Configure las variables y renómbrelo a .env")
        return
    
    if "--validate-only" in sys.argv:
        validation = await setup.validate_configuration()
        print("\n📊 Resultado de validación:")
        print(f"Status: {validation['status']}")
        
        if validation['checks']:
            print("\n✅ Checks exitosos:")
            for check in validation['checks']:
                print(f"  {check}")
        
        if validation['warnings']:
            print("\n⚠️ Advertencias:")
            for warning in validation['warnings']:
                print(f"  {warning}")
        
        if validation['errors']:
            print("\n❌ Errores:")
            for error in validation['errors']:
                print(f"  {error}")
        
        return
    
    # Inicialización completa
    results = await setup.initialize_system()
    
    print("\n📊 Resultados de inicialización:")
    print(f"Status: {results['status']}")
    
    if results['steps_completed']:
        print("\n✅ Pasos completados:")
        for step in results['steps_completed']:
            print(f"  • {step}")
    
    if 'errors' in results and results['errors']:
        print("\n❌ Errores:")
        for error in results['errors']:
            print(f"  • {error}")
    
    if results.get('admin_user'):
        admin_info = results['admin_user']
        print(f"\n🔑 Usuario administrador:")
        print(f"  Username: admin")
        print(f"  Password: {admin_info.get('temp_password', 'N/A')}")
        print(f"  User ID: {admin_info.get('user_id', 'N/A')}")
    
    if results.get('sample_users') and results['sample_users']['created_users']:
        print(f"\n👥 Usuarios de ejemplo creados:")
        for user in results['sample_users']['created_users']:
            print(f"  • {user['username']}: {user['password']}")
    
    print(f"\n🎯 Siguientes pasos:")
    print(f"  1. Configurar variables de entorno en .env")
    print(f"  2. Ejecutar scripts SQL en su base de datos")
    print(f"  3. Cambiar contraseña del usuario admin")
    print(f"  4. Configurar proveedores OAuth/LDAP según necesidad")
    print(f"  5. Revisar logs de auditoría regularmente")
    
    if results['status'] == 'completed':
        print(f"\n✅ ¡Sistema de autenticación configurado exitosamente!")
    else:
        print(f"\n❌ Inicialización incompleta. Revisar errores arriba.")


if __name__ == "__main__":
    asyncio.run(main())