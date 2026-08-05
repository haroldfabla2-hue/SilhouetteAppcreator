"""
Configuración global para tests de integración
Configura el entorno de testing completo para el sistema multi-agente
"""
import asyncio
import pytest
import logging
from typing import AsyncGenerator, Dict, Any
from datetime import datetime, timedelta
import json
import random
import string
import psycopg2
import asyncpg
import redis.asyncio as redis
import os
from unittest.mock import AsyncMock, MagicMock

# Importar componentes del sistema
try:
    from src.orchestrator.multi_agent_orchestrator import (
        MultiAgentOrchestrator, 
        OrchestrationPhase,
        OrchestrationContext,
        OrchestrationResult
    )
    from src.agents.multiagent_orchestrator_agent import MultiAgentOrchestratorAgent
    from src.agents.database_operations_agent import DatabaseOperationsAgent
    from src.agents.python_executor_agent import PythonExecutorAgent
    from src.agents.git_operations_agent import GitOperationsAgent
    from src.agents.file_processing_agent import FileProcessingAgent
    from src.agents.web_scraping_agent import WebScrapingAgent
    from src.agents.search_engine_agent import SearchEngineAgent
    from src.agents.memory_manager_wrapper import MemoryManagerWrapper
    from src.agents.reasoner_wrapper import ReasonerWrapper
    from src.agents.planner_wrapper import PlannerWrapper
    from src.agents.executor_wrapper import ExecutorWrapper
    from src.agents.verifier_wrapper import VerifierWrapper
    from src.core.context_persistence_engine import ContextPersistenceEngine
    from src.observability.advanced_metrics import AdvancedMetrics
    from src.core.config import MCPCoreSettings
    from src.security.security_system import SecuritySystem
    from src.services.embedding_service import EmbeddingService
    from src.services.vector_store_client import VectorStoreClient
except ImportError as e:
    print(f"Advertencia: No se pudieron importar algunos módulos: {e}")

# Configurar logging para tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestDatabase:
    """Gestor de base de datos para testing"""
    
    def __init__(self):
        self.connection_params = {
            "host": os.getenv("TEST_DB_HOST", "localhost"),
            "port": int(os.getenv("TEST_DB_PORT", "5433")),
            "database": os.getenv("TEST_DB_NAME", "mcp_core_test"),
            "user": os.getenv("TEST_DB_USER", "test_user"),
            "password": os.getenv("TEST_DB_PASSWORD", "test_pass")
        }
        self.vector_connection_params = {
            "host": os.getenv("TEST_DB_HOST", "localhost"),
            "port": int(os.getenv("TEST_DB_PORT", "5433")),
            "database": os.getenv("TEST_DB_NAME", "mcp_core_vector_test"),
            "user": os.getenv("TEST_DB_USER", "test_user"),
            "password": os.getenv("TEST_DB_PASSWORD", "test_pass")
        }
    
    async def connect(self):
        """Crear conexiones"""
        try:
            self.main_conn = await asyncpg.connect(**self.connection_params)
            self.vector_conn = await asyncpg.connect(**self.vector_connection_params)
            return True
        except Exception as e:
            logger.warning(f"No se pudo conectar a DB de test: {e}")
            return False
    
    async def disconnect(self):
        """Cerrar conexiones"""
        if hasattr(self, 'main_conn'):
            await self.main_conn.close()
        if hasattr(self, 'vector_conn'):
            await self.vector_conn.close()
    
    async def setup_test_data(self):
        """Configurar datos de prueba"""
        try:
            # Crear tablas de test
            await self.main_conn.execute("""
                CREATE TABLE IF NOT EXISTS test_agents (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    type VARCHAR(100) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    config JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            await self.main_conn.execute("""
                CREATE TABLE IF NOT EXISTS test_tasks (
                    id SERIAL PRIMARY KEY,
                    task_id VARCHAR(255) UNIQUE NOT NULL,
                    objective TEXT NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    context JSONB,
                    result JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    completed_at TIMESTAMP
                )
            """)
            
            await self.main_conn.execute("""
                CREATE TABLE IF NOT EXISTS test_context_persistence (
                    id SERIAL PRIMARY KEY,
                    context_id VARCHAR(255) UNIQUE NOT NULL,
                    agent_id VARCHAR(255) NOT NULL,
                    data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Crear extensión pgvector si no existe
            try:
                await self.vector_conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            except:
                pass
            
            await self.vector_conn.execute("""
                CREATE TABLE IF NOT EXISTS test_embeddings (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding vector(1536),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Insertar datos de prueba
            await self.main_conn.execute("""
                INSERT INTO test_agents (name, type, status, config) VALUES
                ('Test Reasoner', 'reasoner', 'active', '{"version": "1.0"}'),
                ('Test Planner', 'planner', 'active', '{"version": "1.0"}'),
                ('Test Executor', 'executor', 'active', '{"version": "1.0"}'),
                ('Test Verifier', 'verifier', 'active', '{"version": "1.0"}'),
                ('Test Database Ops', 'database_operations', 'active', '{"version": "1.0"}'),
                ('Test Python Exec', 'python_executor', 'active', '{"version": "1.0"}'),
                ('Test Git Ops', 'git_operations', 'active', '{"version": "1.0"}'),
                ('Test File Processing', 'file_processing', 'active', '{"version": "1.0"}'),
                ('Test Web Scraping', 'web_scraping', 'active', '{"version": "1.0"}'),
                ('Test Search Engine', 'search_engine', 'active', '{"version": "1.0"}'),
                ('Test Memory Manager', 'memory_manager', 'active', '{"version": "1.0"}'),
                ('Test Orchestrator', 'orchestrator', 'active', '{"version": "1.0"}')
                ON CONFLICT (name) DO NOTHING
            """)
            
            logger.info("Base de datos de test configurada correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error configurando base de datos de test: {e}")
            return False
    
    async def cleanup_test_data(self):
        """Limpiar datos de prueba"""
        try:
            await self.main_conn.execute("DELETE FROM test_embeddings")
            await self.main_conn.execute("DELETE FROM test_context_persistence")
            await self.main_conn.execute("DELETE FROM test_tasks")
            await self.main_conn.execute("DELETE FROM test_agents")
            logger.info("Datos de test limpiados")
        except Exception as e:
            logger.error(f"Error limpiando datos de test: {e}")


class TestRedis:
    """Gestor de Redis para testing"""
    
    def __init__(self):
        self.connection_params = {
            "host": os.getenv("TEST_REDIS_HOST", "localhost"),
            "port": int(os.getenv("TEST_REDIS_PORT", "6380")),
            "decode_responses": True
        }
    
    async def connect(self):
        """Crear conexión"""
        try:
            self.redis_conn = redis.Redis(**self.connection_params)
            await self.redis_conn.ping()
            return True
        except Exception as e:
            logger.warning(f"No se pudo conectar a Redis de test: {e}")
            return False
    
    async def disconnect(self):
        """Cerrar conexión"""
        if hasattr(self, 'redis_conn'):
            await self.redis_conn.close()
    
    async def setup_test_data(self):
        """Configurar datos de prueba"""
        try:
            # Configurar datos de streaming test
            await self.redis_conn.set("test_stream_key", "test_value", ex=3600)
            await self.redis_conn.hset("test_agent_status", mapping={
                "reasoner": "ready",
                "planner": "ready", 
                "executor": "ready",
                "verifier": "ready",
                "memory_manager": "ready"
            })
            logger.info("Redis de test configurado correctamente")
            return True
        except Exception as e:
            logger.error(f"Error configurando Redis de test: {e}")
            return False
    
    async def cleanup_test_data(self):
        """Limpiar datos de prueba"""
        try:
            await self.redis_conn.flushall()
            logger.info("Redis de test limpiado")
        except Exception as e:
            logger.error(f"Error limpiando Redis de test: {e}")


class MockServices:
    """Servicios simulados para testing"""
    
    def __init__(self):
        self.security_system = MagicMock()
        self.security_system.authenticate = AsyncMock(return_value=True)
        self.security_system.authorize = AsyncMock(return_value=True)
        self.security_system.validate_token = AsyncMock(return_value={"valid": True, "user_id": "test_user"})
        
        self.embedding_service = MagicMock()
        self.embedding_service.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
        
        self.vector_store = MagicMock()
        self.vector_store.store_embedding = AsyncMock(return_value=True)
        self.vector_store.search_similar = AsyncMock(return_value=[])
        
        self.metrics = MagicMock()
        self.metrics.record_metric = AsyncMock()
        self.metrics.get_metrics = AsyncMock(return_value={})


# Instance global de test
test_db = TestDatabase()
test_redis = TestRedis()
mock_services = MockServices()


@pytest.fixture(scope="session")
def event_loop():
    """Crear event loop para tests asíncronos"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_database():
    """Fixture de base de datos de test"""
    await test_db.connect()
    await test_db.setup_test_data()
    yield test_db
    await test_db.cleanup_test_data()
    await test_db.disconnect()


@pytest.fixture
async def test_redis_client():
    """Fixture de Redis de test"""
    connected = await test_redis.connect()
    if connected:
        await test_redis.setup_test_data()
        yield test_redis
        await test_redis.cleanup_test_data()
        await test_redis.disconnect()
    else:
        # Mock Redis si no está disponible
        yield None


@pytest.fixture
async def orchestrator():
    """Fixture del orquestador multi-agente"""
    orchestrator = MultiAgentOrchestrator()
    await orchestrator.initialize()
    yield orchestrator
    await orchestrator.cleanup()


@pytest.fixture
async def test_context():
    """Contexto de test consistente"""
    return {
        "task_id": f"test_task_{random.randint(1000, 9999)}",
        "user_id": "test_user",
        "session_id": f"test_session_{random.randint(1000, 9999)}",
        "timestamp": datetime.now().isoformat(),
        "test_data": {
            "sample_text": "This is a sample text for testing",
            "sample_numbers": [1, 2, 3, 4, 5],
            "sample_dict": {"key1": "value1", "key2": 42}
        }
    }


@pytest.fixture
def mock_agents():
    """Mock de todos los agentes especializados"""
    return {
        "reasoner": MagicMock(),
        "planner": MagicMock(),
        "executor": MagicMock(),
        "verifier": MagicMock(),
        "database_operations": MagicMock(),
        "python_executor": MagicMock(),
        "git_operations": MagicMock(),
        "file_processing": MagicMock(),
        "web_scraping": MagicMock(),
        "search_engine": MagicMock(),
        "memory_manager": MagicMock(),
        "orchestrator": MagicMock()
    }


@pytest.fixture
def sample_tasks():
    """Tareas de ejemplo para tests"""
    return [
        {
            "objective": "Analyze data from customer feedback",
            "complexity": "medium",
            "agents_needed": ["reasoner", "planner", "executor", "verifier"],
            "expected_duration": 30,
            "test_data": {"source": "customer_survey"}
        },
        {
            "objective": "Process large dataset and generate insights",
            "complexity": "high",
            "agents_needed": ["reasoner", "planner", "executor", "database_operations", "python_executor", "verifier"],
            "expected_duration": 120,
            "test_data": {"dataset_size": "large", "analysis_type": "statistical"}
        },
        {
            "objective": "Web scraping and content analysis",
            "complexity": "medium",
            "agents_needed": ["web_scraping", "search_engine", "planner", "executor", "verifier"],
            "expected_duration": 45,
            "test_data": {"urls": ["example.com", "test.com"], "analysis_focus": "content"}
        }
    ]


@pytest.fixture
def load_test_config():
    """Configuración para tests de carga"""
    return {
        "concurrent_users": 10,
        "tasks_per_user": 5,
        "test_duration_minutes": 10,
        "ramp_up_time_seconds": 30,
        "success_threshold": 0.95,
        "max_response_time_seconds": 30
    }


@pytest.fixture
def security_test_config():
    """Configuración para tests de seguridad"""
    return {
        "test_attacks": [
            "sql_injection",
            "xss_attempt",
            "unauthorized_access",
            "rate_limit_bypass",
            "session_hijacking"
        ],
        "auth_tokens": {
            "valid_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.valid",
            "expired_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.expired",
            "invalid_token": "invalid.token.here"
        },
        "user_roles": {
            "admin": "all_permissions",
            "user": "limited_permissions",
            "guest": "minimal_permissions"
        }
    }


@pytest.fixture
def streaming_test_config():
    """Configuración para tests de streaming"""
    return {
        "stream_duration_seconds": 10,
        "update_frequency_hz": 2,
        "buffer_size": 100,
        "concurrent_streams": 5,
        "expected_events": 20
    }


@pytest.fixture
def database_test_config():
    """Configuración para tests de base de datos"""
    return {
        "test_queries": [
            "INSERT INTO test_agents VALUES (1, 'Test', 'test_type', 'active', '{}')",
            "SELECT * FROM test_agents WHERE status = 'active'",
            "UPDATE test_agents SET status = 'inactive' WHERE id = 1",
            "DELETE FROM test_agents WHERE id = 1"
        ],
        "vector_operations": [
            "Generate embedding for test text",
            "Store embedding in vector database",
            "Search for similar embeddings"
        ],
        "performance_thresholds": {
            "query_time_ms": 100,
            "connection_time_ms": 50,
            "throughput_ops_per_sec": 100
        }
    }


@pytest.fixture
def performance_test_data():
    """Datos para tests de performance"""
    return {
        "large_text": " ".join([f"word{i}" for i in range(10000)]),
        "complex_json": {
            f"key_{i}": {
                "nested_1": [random.random() for _ in range(100)],
                "nested_2": {"data": f"value_{i}"}
            } for i in range(100)
        },
        "heavy_computation": {
            "iterations": 1000,
            "complexity": "high"
        }
    }


def pytest_configure(config):
    """Configuración global de pytest"""
    config.addinivalue_line(
        "markers", "integration: marca tests de integración"
    )
    config.addinivalue_line(
        "markers", "slow: marca tests lentos"
    )
    config.addinivalue_line(
        "markers", "performance: marca tests de performance"
    )
    config.addinivalue_line(
        "markers", "security: marca tests de seguridad"
    )
    config.addinivalue_line(
        "markers", "streaming: marca tests de streaming"
    )


def pytest_collection_modifyitems(config, items):
    """Modificar colección de tests"""
    for item in items:
        # Agregar marcadores automáticamente
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        if "security" in item.nodeid:
            item.add_marker(pytest.mark.security)
        if "streaming" in item.nodeid:
            item.add_marker(pytest.mark.streaming)


# Funciones auxiliares para tests
async def generate_test_embedding(text: str = "test text") -> list:
    """Generar embedding de test"""
    return [random.uniform(-1, 1) for _ in range(1536)]


async def create_test_task_id() -> str:
    """Crear ID de tarea de test"""
    return f"test_task_{int(datetime.now().timestamp())}"


async def wait_for_condition(condition_func, timeout=10, interval=0.1):
    """Esperar a que se cumpla una condición"""
    start_time = datetime.now()
    while (datetime.now() - start_time).total_seconds() < timeout:
        if await condition_func() if asyncio.iscoroutinefunction(condition_func) else condition_func():
            return True
        await asyncio.sleep(interval)
    return False


def assert_orchestration_success(result: dict):
    """Verificar que una orquestación fue exitosa"""
    assert result["success"] is True, f"Orquestación falló: {result.get('error_message')}"
    assert result["quality_score"] > 0.7, f"Quality score muy bajo: {result['quality_score']}"
    assert "task_id" in result, "Falta task_id en resultado"
    assert "objective_analysis" in result, "Falta análisis de objetivo"


def assert_agent_integration_result(result: dict, expected_agents: list):
    """Verificar resultado de integración de agentes"""
    assert "agents_results" in result, "Falta resultados de agentes"
    for agent in expected_agents:
        assert agent in result["agents_results"], f"Agente {agent} no en resultados"
        assert result["agents_results"][agent]["success"], f"Agente {agent} falló"


def assert_streaming_response(response_data: list):
    """Verificar respuesta de streaming"""
    assert len(response_data) > 0, "Respuesta de streaming vacía"
    for item in response_data:
        assert "timestamp" in item, "Falta timestamp en item de streaming"
        assert "data" in item, "Falta data en item de streaming"


def assert_database_operation_result(result: dict):
    """Verificar resultado de operación de base de datos"""
    assert "success" in result, "Falta campo success en resultado"
    assert "execution_time_ms" in result, "Falta tiempo de ejecución"
    if result["success"]:
        assert "data" in result or "affected_rows" in result, "Falta data en resultado exitoso"


def assert_security_violation_result(result: dict):
    """Verificar resultado de test de seguridad"""
    assert "violation_detected" in result, "Falta campo violation_detected"
    assert "security_level" in result, "Falta nivel de seguridad"
    assert result["security_level"] in ["low", "medium", "high", "critical"]


def assert_performance_metrics(metrics: dict, thresholds: dict):
    """Verificar métricas de performance"""
    for metric, value in metrics.items():
        if metric in thresholds:
            assert value <= thresholds[metric], f"Métrica {metric} excede umbral: {value} > {thresholds[metric]}"


# Mock para servicios externos no disponibles
class MockContextForge:
    """Mock de ContextForge para testing"""
    
    async def generate_embedding(self, text: str) -> list:
        return await generate_test_embedding(text)
    
    async def store_context(self, context: dict) -> str:
        return f"context_{random.randint(1000, 9999)}"
    
    async def retrieve_context(self, context_id: str) -> dict:
        return {"id": context_id, "data": "mock context data"}