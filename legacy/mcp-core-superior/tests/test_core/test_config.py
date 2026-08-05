"""
Unit tests para configuración centralizada (config.py)
Gestiona todas las configuraciones del sistema de manera type-safe
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from typing import Optional, List

import sys
import os as sys_os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.config import (
    MCPCoreSettings, LogLevel, Environment
)


class TestMCPCoreSettings:
    """Test suite para MCPCoreSettings"""
    
    def test_environment_enum_values(self):
        """Test valores del enum Environment"""
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.STAGING.value == "staging"
        assert Environment.PRODUCTION.value == "production"
    
    def test_log_level_enum_values(self):
        """Test valores del enum LogLevel"""
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARNING.value == "WARNING"
        assert LogLevel.ERROR.value == "ERROR"
        assert LogLevel.CRITICAL.value == "CRITICAL"
    
    @patch.dict(os.environ, {
        'MCP_CORE_ENVIRONMENT': 'production',
        'MCP_CORE_DEBUG': 'false',
        'MCP_CORE_HOST': '0.0.0.0',
        'MCP_CORE_PORT': '8080',
        'MCP_CORE_DATABASE_URL': 'postgresql://test:test@localhost:5432/test_db'
    })
    def test_environment_variables_loading(self):
        """Test carga de variables de entorno"""
        settings = MCPCoreSettings()
        
        assert settings.environment == Environment.PRODUCTION
        assert settings.debug is False
        assert settings.host == "0.0.0.0"
        assert settings.port == 8080
        assert settings.database_url == "postgresql://test:test@localhost:5432/test_db"
    
    def test_default_values(self):
        """Test valores por defecto"""
        with patch.dict(os.environ, {}, clear=True):
            settings = MCPCoreSettings()
            
            # Configuración básica
            assert settings.environment == Environment.DEVELOPMENT
            assert settings.debug is True
            assert settings.app_name == "MCP Core Superior"
            assert settings.app_version == "1.0.0"
            
            # Puertos y hosts
            assert settings.host == "0.0.0.0"
            assert settings.port == 8080
            assert settings.mcp_port == 8081
            
            # ContextForge Gateway
            assert settings.contextforge_url == "http://localhost:8001"
            assert settings.contextforge_timeout == 30
            
            # Base de datos
            assert "postgresql://user:password@localhost:5432/mcp_core" in settings.database_url
            assert settings.database_pool_size == 10
            assert settings.database_max_overflow == 20
            assert settings.database_pool_timeout == 30
            
            # Vector Store
            assert "postgresql://user:password@localhost:5432/vector_db" in settings.vector_db_url
            assert settings.vector_db_pool_size == 5
            assert settings.embedding_model == "text-embedding-ada-002"
            assert settings.embedding_dimension == 1536
            
            # Redis Cache
            assert settings.redis_url == "redis://localhost:6379"
            assert settings.redis_pool_size == 10
            assert settings.redis_timeout == 30
            
            # JWT
            assert settings.jwt_algorithm == "HS256"
            assert settings.jwt_expiration_hours == 24
            
            # Performance
            assert settings.max_concurrent_tasks == 10
            assert settings.max_concurrent_tools == 5
            assert settings.default_timeout_seconds == 300
            assert settings.streaming_buffer_size == 1000
            
            # Streaming
            assert settings.streaming_enabled is True
            assert settings.streaming_frequency == 1.0
            assert settings.streaming_max_duration == 3600
            
            # Rate Limiting
            assert settings.rate_limit_enabled is True
            assert settings.rate_limit_requests == 100
            assert settings.rate_limit_window == 60
            
            # Logging
            assert settings.log_level == LogLevel.INFO
    
    def test_required_fields(self):
        """Test campos requeridos"""
        with patch.dict(os.environ, {
            'MCP_CORE_JWT_SECRET': 'test-secret-key'
        }, clear=True):
            # JWT secret es requerido
            with pytest.raises(Exception):  # pydantic validation error
                MCPCoreSettings()
    
    def test_jwt_secret_required(self):
        """Test que JWT secret es requerido"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception):
                MCPCoreSettings()
    
    def test_integer_field_validation(self):
        """Test validación de campos enteros"""
        with patch.dict(os.environ, {
            'MCP_CORE_JWT_SECRET': 'test-secret',
            'MCP_CORE_PORT': 'not_an_integer',
            'MCP_CORE_DATABASE_POOL_SIZE': 'invalid'
        }, clear=True):
            with pytest.raises(Exception):  # pydantic validation error
                MCPCoreSettings()
    
    def test_boolean_field_validation(self):
        """Test validación de campos booleanos"""
        with patch.dict(os.environ, {
            'MCP_CORE_JWT_SECRET': 'test-secret',
            'MCP_CORE_DEBUG': 'not_a_boolean',
            'MCP_CORE_STREAMING_ENABLED': 'invalid_bool'
        }, clear=True):
            with pytest.raises(Exception):  # pydantic validation error
                MCPCoreSettings()
    
    def test_enum_field_validation(self):
        """Test validación de campos enum"""
        with patch.dict(os.environ, {
            'MCP_CORE_JWT_SECRET': 'test-secret',
            'MCP_CORE_ENVIRONMENT': 'invalid_environment',
            'MCP_CORE_LOG_LEVEL': 'INVALID_LEVEL'
        }, clear=True):
            with pytest.raises(Exception):  # pydantic validation error
                MCPCoreSettings()
    
    def test_environment_specific_configurations(self):
        """Test configuraciones específicas por entorno"""
        # Desarrollo
        with patch.dict(os.environ, {
            'MCP_CORE_JWT_SECRET': 'test-secret',
            'MCP_CORE_ENVIRONMENT': 'development'
        }, clear=True):
            settings = MCPCoreSettings()
            assert settings.environment == Environment.DEVELOPMENT
            assert settings.debug is True
        
        # Producción
        with patch.dict(os.environ, {
            'MCP_CORE_JWT_SECRET': 'test-secret',
            'MCP_CORE_ENVIRONMENT': 'production',
            'MCP_CORE_DEBUG': 'false'
        }, clear=True):
            settings = MCPCoreSettings()
            assert settings.environment == Environment.PRODUCTION
            assert settings.debug is False
    
    def test_database_configuration(self):
        """Test configuración de base de datos"""
        with patch.dict(os.environ, {
            'MCP_CORE_JWT_SECRET': 'test-secret',
            'MCP_CORE_DATABASE_URL': 'postgresql://user:pass@localhost:5432/custom_db',
            'MCP_CORE_DATABASE_POOL_SIZE': '20',
            'MCP_CORE_DATABASE_MAX_OVERFLOW': '30'
        }, clear=True):
            settings = MCPCoreSettings()
            assert settings.database_url == 'postgresql://user:pass@localhost:5432/custom_db'
            assert settings.database_pool_size == 20
            assert settings.database_max_overflow == 30
    
    def test_vector_db_configuration(self):
        """Test configuración de Vector DB"""
        with patch.dict(os.environ, {
            'MCP_CORE_JWT_SECRET': 'test-secret',
            'MCP_CORE_VECTOR_DB_URL': 'postgresql://user:pass@localhost:5432/vector_db_custom',
            'MCP_CORE_EMBEDDING_MODEL': 'custom-embedding-model',
            'MCP_CORE_EMBEDDING_DIMENSION': '2048'
        }, clear=True):
            settings = MCPCoreSettings()
            assert "vector_db_custom" in settings.vector_db_url
            assert settings.embedding_model == "custom-embedding-model"
            assert settings.embedding_dimension == 2048
    
    def test_redis_configuration(self):
        """Test configuración de Redis"""
        with patch.dict(os.environ, {
            'MCP_CORE_JWT_SECRET': 'test-secret',
            'MCP_CORE_REDIS_URL': 'redis://custom-redis:6379',
            'MCP_CORE_REDIS_POOL_SIZE': '15',
            'MCP_CORE_REDIS_TIMEOUT': '60'
        }, clear=True):
            settings = MCPCoreSettings()
            assert settings.redis_url == "redis://custom-redis:6379"
            assert settings.redis_pool_size == 15
            assert settings.redis_timeout == 60
    
    def test_performance_configuration(self):
        """Test configuración de performance"""
        with patch.dict(os.environ, {
            'MCP_CORE_JWT_SECRET': 'test-secret',
            'MCP_CORE_MAX_CONCURRENT_TASKS': '20',
            'MCP_CORE_MAX_CONCURRENT_TOOLS': '10',
            'MCP_CORE_DEFAULT_TIMEOUT_SECONDS': '600',
            'MCP_CORE_STREAMING_BUFFER_SIZE': '2000'
        }, clear=True):
            settings = MCPCoreSettings()
            assert settings.max_concurrent_tasks == 20
            assert settings.max_concurrent_tools == 10
            assert settings.default_timeout_seconds == 600
            assert settings.streaming_buffer_size == 2000
    
    def test_streaming_configuration(self):
        """Test configuración de streaming"""
        with patch.dict(os.environ, {
            'MCP_CORE_JWT_SECRET': 'test-secret',
            'MCP_CORE_STREAMING_ENABLED': 'false',
            'MCP_CORE_STREAMING_FREQUENCY': '2.5',
            'MCP_CORE_STREAMING_MAX_DURATION': '7200'
        }, clear=True):
            settings = MCPCoreSettings()
            assert settings.streaming_enabled is False
            assert settings.streaming_frequency == 2.5
            assert settings.streaming_max_duration == 7200
    
    def test_rate_limiting_configuration(self):
        """Test configuración de rate limiting"""
        with patch.dict(os.environ, {
            'MCP_CORE_JWT_SECRET': 'test-secret',
            'MCP_CORE_RATE_LIMIT_ENABLED': 'false',
            'MCP_CORE_RATE_LIMIT_REQUESTS': '200',
            'MCP_CORE_RATE_LIMIT_WINDOW': '120'
        }, clear=True):
            settings = MCPCoreSettings()
            assert settings.rate_limit_enabled is False
            assert settings.rate_limit_requests == 200
            assert settings.rate_limit_window == 120
    
    def test_contextforge_configuration(self):
        """Test configuración de ContextForge Gateway"""
        with patch.dict(os.environ, {
            'MCP_CORE_JWT_SECRET': 'test-secret',
            'MCP_CORE_CONTEXTFORGE_URL': 'https://custom-contextforge.com:8002',
            'MCP_CORE_CONTEXTFORGE_API_KEY': 'custom-api-key',
            'MCP_CORE_CONTEXTFORGE_TIMEOUT': '45'
        }, clear=True):
            settings = MCPCoreSettings()
            assert settings.contextforge_url == "https://custom-contextforge.com:8002"
            assert settings.contextforge_api_key == "custom-api-key"
            assert settings.contextforge_timeout == 45
    
    def test_jwt_configuration(self):
        """Test configuración de JWT"""
        with patch.dict(os.environ, {
            'MCP_CORE_JWT_SECRET': 'custom-jwt-secret',
            'MCP_CORE_JWT_ALGORITHM': 'RS256',
            'MCP_CORE_JWT_EXPIRATION_HOURS': '48'
        }, clear=True):
            settings = MCPCoreSettings()
            assert settings.jwt_secret == "custom-jwt-secret"
            assert settings.jwt_algorithm == "RS256"
            assert settings.jwt_expiration_hours == 48
    
    def test_settings_pydantic_validation(self):
        """Test que las configuraciones siguen las validaciones de Pydantic"""
        with patch.dict(os.environ, {
            'MCP_CORE_JWT_SECRET': 'test-secret',
            'MCP_CORE_PORT': '8080',  # Valor válido
            'MCP_CORE_DATABASE_POOL_SIZE': '10'  # Valor válido
        }, clear=True):
            settings = MCPCoreSettings()
            
            # Verificar que los tipos son correctos
            assert isinstance(settings.port, int)
            assert isinstance(settings.database_pool_size, int)
            assert isinstance(settings.debug, bool)
            assert isinstance(settings.environment, Environment)
    
    def test_environment_prefix_handling(self):
        """Test manejo del prefijo de entorno"""
        with patch.dict(os.environ, {
            'MCP_CORE_JWT_SECRET': 'test-secret',
            'MCP_CORE_APP_NAME': 'Custom App Name',
            'MCP_CORE_APP_VERSION': '2.0.0',
            'MCP_CORE_HOST': '127.0.0.1'
        }, clear=True):
            settings = MCPCoreSettings()
            assert settings.app_name == "Custom App Name"
            assert settings.app_version == "2.0.0"
            assert settings.host == "127.0.0.1"
    
    def test_settings_case_insensitive(self):
        """Test que las configuraciones son case-insensitive"""
        with patch.dict(os.environ, {
            'MCP_CORE_JWT_SECRET': 'test-secret',
            'MCP_CORE_ENVIRONMENT': 'PRODUCTION',
            'MCP_CORE_LOG_LEVEL': 'DEBUG',
            'MCP_CORE_DEBUG': 'TRUE'
        }, clear=True):
            settings = MCPCoreSettings()
            assert settings.environment == Environment.PRODUCTION
            assert settings.log_level == LogLevel.DEBUG
            assert settings.debug is True
    
    def test_settings_serialization(self):
        """Test serialización de configuraciones"""
        with patch.dict(os.environ, {
            'MCP_CORE_JWT_SECRET': 'test-secret'
        }, clear=True):
            settings = MCPCoreSettings()
            
            # Test que se puede convertir a dict
            settings_dict = settings.model_dump()
            assert isinstance(settings_dict, dict)
            assert "environment" in settings_dict
            assert "port" in settings_dict
            assert "database_url" in settings_dict
            
            # Test que no se exponen secretos en el dump
            settings_dict = settings.model_dump(exclude={"jwt_secret"})
            assert "jwt_secret" not in settings_dict
    
    def test_settings_validation_edge_cases(self):
        """Test casos extremos de validación"""
        with patch.dict(os.environ, {
            'MCP_CORE_JWT_SECRET': 'test-secret',
            'MCP_CORE_PORT': '0',  # Puerto mínimo válido
            'MCP_CORE_DATABASE_POOL_SIZE': '0',  # Pool size mínimo
            'MCP_CORE_RATE_LIMIT_REQUESTS': '0'  # Rate limit mínimo
        }, clear=True):
            settings = MCPCoreSettings()
            assert settings.port == 0
            assert settings.database_pool_size == 0
            assert settings.rate_limit_requests == 0
        
        # Valores negativos deberían fallar
        with patch.dict(os.environ, {
            'MCP_CORE_JWT_SECRET': 'test-secret',
            'MCP_CORE_PORT': '-1',
            'MCP_CORE_DATABASE_POOL_SIZE': '-5'
        }, clear=True):
            with pytest.raises(Exception):
                MCPCoreSettings()
