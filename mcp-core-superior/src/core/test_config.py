"""
Configuración simplificada para testing (sin variables de entorno)
"""

# Configuración hardcodeada para testing
test_settings = {
    "jwt_secret": "test_secret_key_for_development",
    "database_url": "sqlite:///./test.db",
    "vector_db_url": "sqlite:///./vector_test.db",
    "environment": "development",
    "debug": True,
    "streaming_enabled": True,
    "max_concurrent_tasks": 5,
    "max_concurrent_tools": 3,
    "agent_timeout_seconds": 30,
    "verification_quality_threshold": 0.8,
    "contextforge_url": "http://localhost:8001",
    "redis_url": "redis://localhost:6379",
    "log_level": "INFO"
}
