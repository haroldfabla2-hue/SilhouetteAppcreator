"""
Configuración global para pytest en MCP Core Superior
Proporciona fixtures y configuración común para todos los tests
"""

import pytest
import asyncio
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, Generator, AsyncGenerator
from dataclasses import dataclass

# Asegurar que src/ esté en el path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Configuración de pytest
pytest_plugins = []

@dataclass
class TestConfig:
    """Configuración de test"""
    test_data_dir: Path
    temp_dir: Path
    mock_responses: Dict[str, Any]
    test_user_id: str = "test-user-123"
    test_agent_id: str = "test-agent-456"
    test_session_id: str = "test-session-789"


@pytest.fixture(scope="session")
def event_loop():
    """Crear event loop para tests async"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config() -> TestConfig:
    """Configuración global de test"""
    # Crear directorio temporal para tests
    test_data_dir = Path(tempfile.mkdtemp(prefix="mcp_test_data_"))
    temp_dir = Path(tempfile.mkdtemp(prefix="mcp_test_temp_"))
    
    yield TestConfig(
        test_data_dir=test_data_dir,
        temp_dir=temp_dir,
        mock_responses={}
    )
    
    # Limpiar después de todos los tests
    try:
        shutil.rmtree(test_data_dir, ignore_errors=True)
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass


@pytest.fixture
def mock_settings():
    """Mock de configuración para tests"""
    from core.config import MCPCoreSettings, Environment, LogLevel
    
    settings = MagicMock(spec=MCPCoreSettings)
    settings.environment = Environment.DEVELOPMENT
    settings.debug = True
    settings.host = "localhost"
    settings.port = 8080
    settings.jwt_secret = "test-secret"
    settings.database_url = "postgresql://test:test@localhost:5432/test_db"
    settings.redis_url = "redis://localhost:6379/0"
    settings.contextforge_url = "http://localhost:8001"
    settings.max_concurrent_tasks = 5
    settings.agent_timeout_seconds = 30
    
    with patch("core.config.settings", settings):
        yield settings


@pytest.fixture
async def mock_database():
    """Mock de base de datos async"""
    from unittest.mock import AsyncMock
    
    db_mock = AsyncMock()
    db_mock.connect = AsyncMock(return_value=True)
    db_mock.disconnect = AsyncMock(return_value=True)
    db_mock.execute = AsyncMock(return_value={"success": True, "data": []})
    db_mock.fetch = AsyncMock(return_value=[])
    db_mock.fetchrow = AsyncMock(return_value=None)
    db_mock.fetchval = AsyncMock(return_value=None)
    
    yield db_mock


@pytest.fixture
async def mock_redis():
    """Mock de Redis"""
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.exists = AsyncMock(return_value=False)
    redis_mock.expire = AsyncMock(return_value=True)
    redis_mock.hgetall = AsyncMock(return_value={})
    redis_mock.hset = AsyncMock(return_value=1)
    redis_mock.lpush = AsyncMock(return_value=1)
    redis_mock.rpop = AsyncMock(return_value=None)
    redis_mock.flushall = AsyncMock(return_value=True)
    
    yield redis_mock


@pytest.fixture
async def mock_contextforge():
    """Mock de ContextForge client"""
    cf_mock = AsyncMock()
    cf_mock.health_check = AsyncMock(return_value={"status": "healthy"})
    cf_mock.store_context = AsyncMock(return_value={"context_id": "test-context"})
    cf_mock.retrieve_context = AsyncMock(return_value={"context": "test-data"})
    cf_mock.update_context = AsyncMock(return_value={"updated": True})
    cf_mock.delete_context = AsyncMock(return_value={"deleted": True})
    
    yield cf_mock


@pytest.fixture
async def mock_vector_store():
    """Mock de vector store"""
    vs_mock = AsyncMock()
    vs_mock.embed = AsyncMock(return_value=[0.1] * 1536)
    vs_mock.search = AsyncMock(return_value=[{"id": "doc1", "score": 0.9}])
    vs_mock.store = AsyncMock(return_value=True)
    vs_mock.delete = AsyncMock(return_value=True)
    
    yield vs_mock


@pytest.fixture
def sample_test_data():
    """Datos de prueba comunes"""
    return {
        "user_id": "test-user-123",
        "session_id": "test-session-456",
        "agent_id": "test-agent-789",
        "task_id": "task-001",
        "input_text": "Test input text",
        "expected_output": "Expected output",
        "metadata": {
            "timestamp": "2025-11-04T05:43:15Z",
            "source": "test_suite"
        }
    }


@pytest.fixture
def temp_file():
    """Crear archivo temporal para tests"""
    def _create_temp_file(content: str = "", suffix: str = ".txt") -> str:
        fd, path = tempfile.mkstemp(suffix=suffix)
        try:
            with os.fdopen(fd, 'w') as f:
                if content:
                    f.write(content)
        except:
            os.close(fd)
            os.unlink(path)
            raise
        return path
    
    yield _create_temp_file
    
    # Cleanup se maneja en el fixture si es necesario


@pytest.fixture
def temp_directory():
    """Crear directorio temporal para tests"""
    temp_dir = tempfile.mkdtemp(prefix="mcp_test_")
    
    yield temp_dir
    
    # Cleanup
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass


@pytest.fixture
def mock_agent_request():
    """Request mock para agentes"""
    return {
        "operation": "test_operation",
        "params": {"param1": "value1"},
        "context": {"user_id": "test-user"},
        "metadata": {
            "timestamp": "2025-11-04T05:43:15Z",
            "source": "pytest"
        }
    }


@pytest.fixture
async def mock_observability():
    """Mock del sistema de observabilidad"""
    obs_mock = AsyncMock()
    obs_mock.record_metric = AsyncMock(return_value=True)
    obs_mock.start_trace = AsyncMock(return_value="trace-id-123")
    obs_mock.end_trace = AsyncMock(return_value=True)
    obs_mock.log_event = AsyncMock(return_value=True)
    obs_mock.get_metrics = AsyncMock(return_value={})
    
    yield obs_mock


@pytest.fixture
async def mock_security_system():
    """Mock del sistema de seguridad"""
    security_mock = AsyncMock()
    security_mock.validate_token = AsyncMock(return_value={"valid": True, "user_id": "test-user"})
    security_mock.check_rate_limit = AsyncMock(return_value=True)
    security_mock.scan_content = AsyncMock(return_value={"safe": True, "threats": []})
    security_mock.authenticate = AsyncMock(return_value={"authenticated": True})
    
    yield security_mock


@pytest.fixture
async def mock_orchestrator():
    """Mock del orquestador"""
    orchestrator_mock = AsyncMock()
    orchestrator_mock.submit_task = AsyncMock(return_value={"task_id": "task-123"})
    orchestrator_mock.get_task_status = AsyncMock(return_value={"status": "running"})
    orchestrator_mock.cancel_task = AsyncMock(return_value=True)
    orchestrator_mock.get_agent_status = AsyncMock(return_value={"status": "idle"})
    
    yield orchestrator_mock


# Markers personalizados para tests
def pytest_configure(config):
    """Configurar markers personalizados"""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "agent: mark test as agent test")
    config.addinivalue_line("markers", "security: mark test as security test")
    config.addinivalue_line("markers", "observability: mark test as observability test")
    config.addinivalue_line("markers", "async_test: mark test as async test")


# Auto-fixtures para async tests
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Configurar ambiente de test automáticamente"""
    # Configurar variables de entorno de test
    os.environ["MCP_CORE_ENVIRONMENT"] = "test"
    os.environ["MCP_CORE_DEBUG"] = "true"
    os.environ["MCP_CORE_JWT_SECRET"] = "test-secret-for-unit-tests"
    os.environ["MCP_CORE_DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_db"
    os.environ["MCP_CORE_REDIS_URL"] = "redis://localhost:6379/0"
    
    yield
    
    # Cleanup después de cada test
    # (variables de entorno se limpian automáticamente)


# Helper functions para tests
def create_test_user_data() -> Dict[str, Any]:
    """Crear datos de usuario de test"""
    return {
        "id": "test-user-123",
        "email": "test@example.com",
        "name": "Test User",
        "created_at": "2025-11-04T05:43:15Z",
        "metadata": {"role": "tester"}
    }


def create_test_task_data() -> Dict[str, Any]:
    """Crear datos de tarea de test"""
    return {
        "id": "task-123",
        "type": "test_task",
        "status": "pending",
        "input": "test input",
        "output": None,
        "created_at": "2025-11-04T05:43:15Z",
        "agent_id": "test-agent-456",
        "user_id": "test-user-789"
    }


def create_test_context_data() -> Dict[str, Any]:
    """Crear datos de contexto de test"""
    return {
        "id": "context-123",
        "user_id": "test-user-123",
        "session_id": "session-456",
        "data": {"test": "data"},
        "metadata": {"created_by": "test"},
        "created_at": "2025-11-04T05:43:15Z"
    }


# Async context manager helper
class AsyncContextManagerHelper:
    """Helper para context managers async en tests"""
    
    def __init__(self, async_func):
        self.async_func = async_func
    
    async def __aenter__(self):
        return await self.async_func()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


def async_mock_context_manager(mock_func):
    """Convertir función async en context manager mockeable"""
    return AsyncContextManagerHelper(mock_func)


# Utility para verificar llamadas async
def assert_async_called_with(mock: AsyncMock, *args, **kwargs):
    """Verificar que mock async fue llamado con argumentos específicos"""
    assert mock.called
    call_args = mock.call_args
    assert call_args.args == args
    assert call_args.kwargs == kwargs


# Utility para medir tiempo de test
import time
from contextlib import contextmanager

@contextmanager
def measure_execution_time():
    """Context manager para medir tiempo de ejecución"""
    start = time.time()
    yield
    end = time.time()
    print(f"Tiempo de ejecución: {end - start:.3f}s")


# Fixtures específicas para tipos de test
@pytest.fixture
def unit_test_config():
    """Configuración específica para tests unitarios"""
    return {
        "run_async": True,
        "use_mocks": True,
        "isolated": True,
        "fast": True
    }


@pytest.fixture
def integration_test_config():
    """Configuración específica para tests de integración"""
    return {
        "run_async": True,
        "use_mocks": False,
        "isolated": False,
        "fast": False
    }