"""
Configuración de Base de Datos para Testing Enterprise
"""

import asyncio
import psycopg2
import redis
import json
from datetime import datetime
from pathlib import Path

from utils.base_utils import TestLogger, TestDataGenerator
from config.test_config import *

class TestDatabaseManager:
    """Gestor de base de datos para testing"""
    
    def __init__(self):
        self.logger = TestLogger("TestDBManager", PROJECT_ROOT / "logs" / "test_db.log")
        self.test_db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "test_enterprise_db",
            "user": "test_user",
            "password": "test_password"
        }
        self.redis_config = {
            "host": "localhost",
            "port": 6379,
            "db": 0
        }
    
    def setup_test_database(self) -> bool:
        """Configura base de datos de testing"""
        try:
            self.logger.info("Setting up test database...")
            
            # Crear base de datos si no existe
            self._create_database()
            
            # Ejecutar migraciones
            self._run_migrations()
            
            # Insertar datos de prueba
            self._insert_test_data()
            
            # Configurar Redis
            self._setup_redis()
            
            self.logger.info("Test database setup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup test database: {str(e)}")
            return False
    
    def _create_database(self):
        """Crea base de datos de testing"""
        try:
            # Conectar a PostgreSQL como super usuario
            conn = psycopg2.connect(
                host=self.test_db_config["host"],
                port=self.test_db_config["port"],
                user="postgres",
                password="postgres"
            )
            conn.autocommit = True
            
            cursor = conn.cursor()
            
            # Verificar si la base de datos existe
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (self.test_db_config["database"],)
            )
            
            if not cursor.fetchone():
                self.logger.info(f"Creating database: {self.test_db_config['database']}")
                cursor.execute(f'CREATE DATABASE {self.test_db_config["database"]}')
            else:
                self.logger.info(f"Database {self.test_db_config['database']} already exists")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error creating database: {str(e)}")
            raise
    
    def _run_migrations(self):
        """Ejecuta migraciones de esquema"""
        try:
            conn = psycopg2.connect(**self.test_db_config)
            cursor = conn.cursor()
            
            # Crear tablas básicas
            migration_sql = """
            -- Tabla de usuarios
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                uuid VARCHAR(36) UNIQUE NOT NULL,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                role VARCHAR(20) DEFAULT 'user',
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Tabla de sesiones
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(128) UNIQUE NOT NULL,
                user_id INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT true
            );
            
            -- Tabla de logs de auditoría
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                action VARCHAR(100) NOT NULL,
                resource VARCHAR(100),
                details JSONB,
                ip_address VARCHAR(45),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Tabla de métricas
            CREATE TABLE IF NOT EXISTS system_metrics (
                id SERIAL PRIMARY KEY,
                metric_name VARCHAR(100) NOT NULL,
                metric_value NUMERIC,
                metric_unit VARCHAR(20),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tags JSONB
            );
            
            -- Índices
            CREATE INDEX IF NOT EXISTS idx_users_uuid ON users(uuid);
            CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
            CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp ON system_metrics(metric_name, timestamp);
            """
            
            cursor.execute(migration_sql)
            conn.commit()
            
            self.logger.info("Database migrations executed successfully")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error running migrations: {str(e)}")
            raise
    
    def _insert_test_data(self):
        """Inserta datos de prueba"""
        try:
            conn = psycopg2.connect(**self.test_db_config)
            cursor = conn.cursor()
            
            # Limpiar datos existentes
            cursor.execute("TRUNCATE TABLE users, sessions, audit_logs, system_metrics RESTART IDENTITY")
            
            # Insertar usuarios de prueba
            test_users = []
            for i in range(10):
                user_data = TestDataGenerator.generate_user_data()
                test_users.append(user_data)
                
                cursor.execute("""
                    INSERT INTO users (uuid, username, email, first_name, last_name, role, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_data["id"],
                    user_data["username"],
                    user_data["email"],
                    user_data["first_name"],
                    user_data["last_name"],
                    user_data["role"],
                    user_data["is_active"]
                ))
            
            # Insertar datos de auditoría simulados
            audit_actions = [
                "USER_LOGIN", "USER_LOGOUT", "DATA_ACCESS", "DATA_MODIFICATION",
                "SYSTEM_CONFIG", "PERMISSION_CHANGE", "BACKUP_CREATED"
            ]
            
            for i in range(50):
                cursor.execute("""
                    INSERT INTO audit_logs (user_id, action, resource, details, ip_address)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    (i % len(test_users)) + 1,
                    audit_actions[i % len(audit_actions)],
                    f"resource_{i}",
                    json.dumps({"action": f"test_action_{i}"}),
                    f"192.168.1.{100 + (i % 50)}"
                ))
            
            # Insertar métricas del sistema
            metric_names = ["cpu_usage", "memory_usage", "disk_usage", "response_time", "error_rate"]
            for i in range(100):
                metric_name = metric_names[i % len(metric_names)]
                metric_value = 10.0 + (i % 80)  # Valores entre 10-90
                
                cursor.execute("""
                    INSERT INTO system_metrics (metric_name, metric_value, metric_unit, tags)
                    VALUES (%s, %s, %s, %s)
                """, (
                    metric_name,
                    metric_value,
                    "%" if "usage" in metric_name else "ms" if metric_name == "response_time" else "count",
                    json.dumps({"environment": "test", "source": "load_generator"})
                ))
            
            conn.commit()
            
            self.logger.info(f"Test data inserted: {len(test_users)} users, 50 audit logs, 100 metrics")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error inserting test data: {str(e)}")
            raise
    
    def _setup_redis(self):
        """Configura Redis para testing"""
        try:
            client = redis.Redis(**self.redis_config)
            
            # Test connection
            client.ping()
            
            # Limpiar datos existentes
            client.flushdb()
            
            # Insertar datos de cache de prueba
            test_cache_data = {
                "session_test_001": json.dumps({"user_id": 1, "expires": 3600}),
                "api_cache_response": json.dumps({"data": "cached_response", "expires": 1800}),
                "metrics_cache": json.dumps({"last_update": datetime.now().isoformat()})
            }
            
            for key, value in test_cache_data.items():
                client.setex(key, 3600, value)  # 1 hora TTL
            
            self.logger.info("Redis setup completed successfully")
            
        except Exception as e:
            self.logger.warning(f"Redis setup failed (may not be running): {str(e)}")
            # Redis no es crítico, continuar sin él
    
    def teardown_test_database(self) -> bool:
        """Limpia base de datos de testing"""
        try:
            self.logger.info("Tearing down test database...")
            
            # Conectar a PostgreSQL
            conn = psycopg2.connect(**self.test_db_config)
            cursor = conn.cursor()
            
            # Limpiar datos
            cursor.execute("TRUNCATE TABLE users, sessions, audit_logs, system_metrics RESTART IDENTITY")
            conn.commit()
            
            cursor.close()
            conn.close()
            
            # Limpiar Redis
            try:
                client = redis.Redis(**self.redis_config)
                client.flushdb()
            except:
                pass  # Redis opcional
            
            self.logger.info("Test database teardown completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to teardown test database: {str(e)}")
            return False
    
    def get_database_status(self) -> dict:
        """Obtiene estado de la base de datos"""
        status = {
            "database": "unknown",
            "tables": [],
            "record_counts": {},
            "redis": "unknown"
        }
        
        try:
            conn = psycopg2.connect(**self.test_db_config)
            cursor = conn.cursor()
            
            # Verificar conexión
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            status["database"] = "connected"
            
            # Listar tablas
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            status["tables"] = [row[0] for row in cursor.fetchall()]
            
            # Contar registros en cada tabla
            for table in status["tables"]:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    status["record_counts"][table] = count
                except:
                    status["record_counts"][table] = "error"
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            status["database"] = f"error: {str(e)}"
        
        # Verificar Redis
        try:
            client = redis.Redis(**self.redis_config)
            client.ping()
            status["redis"] = "connected"
            
            # Obtener info de Redis
            info = client.info()
            status["redis_keys"] = client.dbsize()
            
        except Exception as e:
            status["redis"] = f"error: {str(e)}"
        
        return status

# Función de utilidad para setup automático
def setup_test_environment():
    """Configura entorno de testing completo"""
    db_manager = TestDatabaseManager()
    
    success = db_manager.setup_test_database()
    
    if success:
        status = db_manager.get_database_status()
        print("✅ Test environment setup completed:")
        print(f"   Database: {status['database']}")
        print(f"   Redis: {status['redis']}")
        print(f"   Tables: {len(status['tables'])}")
        print(f"   Records: {sum(count for count in status['record_counts'].values() if isinstance(count, int))}")
    else:
        print("❌ Test environment setup failed")
    
    return success

if __name__ == "__main__":
    setup_test_environment()
