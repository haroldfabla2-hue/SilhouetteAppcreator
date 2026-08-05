#!/usr/bin/env python3
"""
Tests unitarios para Database Operations Agent
Verifican funcionalidad básica y manejo de errores
"""

import unittest
import asyncio
import os
import sys
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

# Agregar path del src al PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.database_operations_agent import (
    DatabaseOperationsAgentWrapper,
    DatabaseConnectionConfig,
    DatabaseOperationType,
    ConnectionPoolStatus,
    QueryExecutionResult,
    VectorSearchResult,
    PerformanceMetrics
)


class TestDatabaseOperationsAgent(unittest.TestCase):
    """Tests para Database Operations Agent"""
    
    def setUp(self):
        """Configurar tests"""
        self.db_config = DatabaseConnectionConfig(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_password",
            pool_size=5,
            max_overflow=10
        )
        
        self.agent = DatabaseOperationsAgentWrapper(self.db_config)
    
    def test_database_connection_config(self):
        """Test configuración de conexión"""
        # Test URL de conexión
        expected_url = "postgresql://test_user:test_password@localhost:5432/test_db"
        self.assertEqual(self.db_config.database_url, expected_url)
        
        # Test propiedades
        self.assertEqual(self.db_config.host, "localhost")
        self.assertEqual(self.db_config.port, 5432)
        self.assertEqual(self.db_config.database, "test_db")
        self.assertEqual(self.db_config.pool_size, 5)
    
    def test_agent_initialization(self):
        """Test inicialización del agente"""
        # Verificar nombre del agente
        self.assertEqual(self.agent.agent_name, "database_operations")
        
        # Verificar capacidades
        self.assertIn("database_operations", str(self.agent))
        
        # Verificar estado inicial
        self.assertFalse(self.agent.is_ready)
        self.assertEqual(self.agent.connection_pool_status, ConnectionPoolStatus.OFFLINE)
        
        # Verificar métricas iniciales
        self.assertEqual(self.agent.query_metrics["total_queries"], 0)
        self.assertEqual(self.agent.query_metrics["vector_searches"], 0)
    
    def test_performance_metrics_creation(self):
        """Test creación de métricas de performance"""
        metrics = PerformanceMetrics(
            active_connections=5,
            total_connections=10,
            cache_hit_ratio=95.5,
            query_avg_time_ms=150.0,
            slow_queries_count=2,
            table_sizes={"users": 1000000, "products": 500000}
        )
        
        self.assertEqual(metrics.active_connections, 5)
        self.assertEqual(metrics.cache_hit_ratio, 95.5)
        self.assertEqual(metrics.table_sizes["users"], 1000000)
    
    def test_format_bytes(self):
        """Test formateo de bytes"""
        # Test diferentes tamaños
        self.assertEqual(self.agent._format_bytes(1024), "1.00 KB")
        self.assertEqual(self.agent._format_bytes(1048576), "1.00 MB")
        self.assertEqual(self.agent._format_bytes(1073741824), "1.00 GB")
        
        # Test valores pequeños
        self.assertEqual(self.agent._format_bytes(512), "512.00 B")
    
    def test_update_query_metrics(self):
        """Test actualización de métricas de consultas"""
        # Test consulta exitosa
        self.agent._update_query_metrics(100.0, True)
        
        self.assertEqual(self.agent.query_metrics["total_queries"], 1)
        self.assertEqual(self.agent.query_metrics["successful_queries"], 1)
        self.assertEqual(self.agent.query_metrics["failed_queries"], 0)
        self.assertEqual(self.agent.query_metrics["avg_execution_time_ms"], 100.0)
        
        # Test consulta fallida
        self.agent._update_query_metrics(200.0, False)
        
        self.assertEqual(self.agent.query_metrics["total_queries"], 2)
        self.assertEqual(self.agent.query_metrics["successful_queries"], 1)
        self.assertEqual(self.agent.query_metrics["failed_queries"], 1)
        
        # Test consulta lenta (> 1000ms)
        self.agent._update_query_metrics(1500.0, True)
        
        self.assertEqual(len(self.agent.query_metrics["slow_queries"]), 1)
        self.assertEqual(self.agent.query_metrics["slow_queries"][0]["execution_time_ms"], 1500.0)
    
    @patch('agents.database_operations_agent.create_engine')
    @patch('agents.database_operations_agent.sessionmaker')
    async def test_initialize_agent(self, mock_sessionmaker, mock_create_engine):
        """Test inicialización del agente con mocks"""
        # Configurar mocks
        mock_engine = Mock()
        mock_connection = Mock()
        mock_connection.execute.return_value.fetchone.return_value = ("PostgreSQL 14.0",)
        
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_create_engine.return_value = mock_engine
        mock_sessionmaker.return_value = Mock()
        
        # Ejecutar inicialización
        await self.agent._initialize()
        
        # Verificar que se llamó create_engine
        mock_create_engine.assert_called_once()
        
        # Verificar que el estado cambió
        self.assertEqual(self.agent.connection_pool_status, ConnectionPoolStatus.HEALTHY)
    
    @patch('agents.database_operations_agent.create_engine')
    async def test_test_connection_success(self, mock_create_engine):
        """Test exitosa de conexión"""
        # Configurar mock
        mock_engine = Mock()
        mock_connection = Mock()
        mock_result = Mock()
        mock_result.fetchone.return_value = (1,)
        
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_create_engine.return_value = mock_engine
        self.agent.engine = mock_engine
        
        # Ejecutar test
        await self.agent._test_connection()
        
        # Verificar que se ejecutó la consulta
        mock_connection.execute.assert_called_once()
    
    @patch('agents.database_operations_agent.create_engine')
    async def test_test_connection_failure(self, mock_create_engine):
        """Test fallida de conexión"""
        # Configurar mock para generar error
        mock_engine = Mock()
        mock_engine.connect.side_effect = Exception("Connection failed")
        mock_create_engine.return_value = mock_engine
        self.agent.engine = mock_engine
        
        # Verificar que se lanza excepción
        with self.assertRaises(Exception):
            await self.agent._test_connection()
    
    async def test_dispatch_invalid_operation(self):
        """Test despacho de operación inválida"""
        request = {"operation_type": "invalid_operation"}
        
        with self.assertRaises(Exception):
            await self.agent._dispatch_operation(request)
    
    @patch('agents.database_operations_agent.create_engine')
    async def test_execute_sql_query_success(self, mock_create_engine):
        """Test ejecución exitosa de consulta SQL"""
        # Configurar mock
        mock_engine = Mock()
        mock_connection = Mock()
        mock_result = Mock()
        
        mock_result.returns_rows = True
        mock_result.fetchall.return_value = [("user1", "email1@example.com")]
        mock_result.keys.return_value = ["username", "email"]
        
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_create_engine.return_value = mock_engine
        self.agent.engine = mock_engine
        
        # Ejecutar consulta
        request = {"query": "SELECT username, email FROM users"}
        result = await self.agent._execute_sql_query(request)
        
        # Verificar resultado
        self.assertTrue(result["success"])
        self.assertEqual(result["query"], "SELECT username, email FROM users")
        self.assertEqual(len(result["data"]), 1)
        self.assertEqual(result["data"][0]["username"], "user1")
        self.assertGreater(result["execution_time_ms"], 0)
    
    @patch('agents.database_operations_agent.create_engine')
    async def test_perform_vector_search_success(self, mock_create_engine):
        """Test exitosa de búsqueda vectorial"""
        # Configurar mock
        mock_engine = Mock()
        mock_connection = Mock()
        mock_connection.connection = Mock()  # Para register_vector
        mock_result = Mock()
        
        # Simular resultado de búsqueda
        mock_result.fetchall.return_value = [
            (1, "Contenido relevante", 0.1),  # id, content, distance
            (2, "Otro contenido", 0.3)
        ]
        mock_result.keys.return_value = ["id", "content", "embedding", "distance"]
        
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_create_engine.return_value = mock_engine
        self.agent.engine = mock_engine
        
        # Ejecutar búsqueda vectorial
        request = {
            "query_embedding": [0.1, 0.2, 0.3] + [0.0] * 1533,  # 1536 dimensiones
            "table_name": "knowledge_base",
            "limit": 5,
            "threshold": 0.7
        }
        result = await self.agent._perform_vector_search(request)
        
        # Verificar resultado
        self.assertTrue(result["success"])
        self.assertEqual(result["table_name"], "knowledge_base")
        self.assertEqual(len(result["results"]), 2)
        self.assertGreater(result["search_time_ms"], 0)
    
    async def test_vector_search_missing_params(self):
        """Test búsqueda vectorial con parámetros faltantes"""
        # Test sin query_embedding
        request = {"table_name": "knowledge_base"}
        with self.assertRaises(Exception):
            await self.agent._perform_vector_search(request)
        
        # Test sin table_name
        request = {"query_embedding": [0.1, 0.2, 0.3]}
        with self.assertRaises(Exception):
            await self.agent._perform_vector_search(request)
    
    @patch('agents.database_operations_agent.inspect')
    @patch('agents.database_operations_agent.create_engine')
    async def test_list_tables_success(self, mock_create_engine, mock_inspect):
        """Test exitosa de listado de tablas"""
        # Configurar mocks
        mock_engine = Mock()
        mock_inspector = Mock()
        
        # Configurar datos de ejemplo
        mock_inspector.get_table_names.return_value = ["users", "products", "orders"]
        mock_inspector.get_schema_names.return_value = ["public", "information_schema"]
        mock_inspector.get_columns.side_effect = lambda table: [
            {"name": "id", "type": "INTEGER", "nullable": False},
            {"name": "name", "type": "VARCHAR(100)", "nullable": True}
        ] if table == "users" else []
        
        mock_inspector.get_indexes.return_value = [
            {"name": "users_pkey", "unique": True, "column_names": ["id"]}
        ]
        
        mock_inspect.return_value = mock_inspector
        mock_create_engine.return_value = mock_engine
        self.agent.engine = mock_engine
        
        # Ejecutar listado
        request = {"schema_operation": "list_tables"}
        result = await self.agent._manage_schema(request)
        
        # Verificar resultado
        self.assertTrue(result["success"])
        self.assertEqual(len(result["tables"]), 3)
        self.assertEqual(result["schemas"], ["public", "information_schema"])
    
    async def test_manage_schema_invalid_operation(self):
        """Test gestión de esquema con operación inválida"""
        request = {"schema_operation": "invalid_operation"}
        
        with self.assertRaises(Exception):
            await self.agent._manage_schema(request)
    
    def test_get_status(self):
        """Test obtención de estado del agente"""
        status = self.agent.get_status()
        
        # Verificar estructura del estado
        self.assertIn("agent_name", status)
        self.assertIn("status", status)
        self.assertIn("is_ready", status)
        self.assertIn("is_busy", status)
        self.assertIn("utilization", status)
        self.assertIn("capabilities", status)
        self.assertIn("metrics", status)
        
        # Verificar valores
        self.assertEqual(status["agent_name"], "database_operations")
        self.assertFalse(status["is_ready"])  # Sin inicializar
        self.assertIsInstance(status["utilization"], float)
    
    def test_agent_string_representation(self):
        """Test representación string del agente"""
        str_repr = str(self.agent)
        self.assertIn("DatabaseOperationsAgent", str_repr)
        self.assertIn("offline", str_repr)
        
        repr_repr = repr(self.agent)
        self.assertIn("agent_name=", repr_repr)
        self.assertIn("pool_status=", repr_repr)


class TestDatabaseOperationTypes(unittest.TestCase):
    """Tests para tipos de operaciones"""
    
    def test_database_operation_type_enum(self):
        """Test enum de tipos de operación"""
        # Verificar que todos los tipos están definidos
        expected_types = [
            "sql_query",
            "vector_search", 
            "schema_management",
            "data_migration",
            "backup_restore",
            "performance_optimization",
            "connection_pool",
            "index_management",
            "monitoring"
        ]
        
        for op_type in expected_types:
            self.assertIsNotNone(DatabaseOperationType(op_type))
    
    def test_connection_pool_status_enum(self):
        """Test enum de estados del pool"""
        # Verificar estados válidos
        statuses = ["healthy", "degraded", "critical", "offline"]
        for status in statuses:
            self.assertIsNotNone(ConnectionPoolStatus(status))


class TestQueryExecutionResult(unittest.TestCase):
    """Tests para QueryExecutionResult"""
    
    def test_query_execution_result_creation(self):
        """Test creación de resultado de ejecución"""
        result = QueryExecutionResult(
            query="SELECT * FROM users",
            execution_time_ms=150.5,
            rows_affected=10,
            result_data=[{"id": 1, "name": "John"}],
            success=True,
            error_message=None
        )
        
        self.assertEqual(result.query, "SELECT * FROM users")
        self.assertEqual(result.execution_time_ms, 150.5)
        self.assertEqual(result.rows_affected, 10)
        self.assertTrue(result.success)
        self.assertIsNone(result.error_message)
    
    def test_query_execution_result_failure(self):
        """Test resultado de ejecución fallida"""
        result = QueryExecutionResult(
            query="INVALID SQL",
            execution_time_ms=50.0,
            rows_affected=0,
            result_data=[],
            success=False,
            error_message="Syntax error"
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Syntax error")


class TestVectorSearchResult(unittest.TestCase):
    """Tests para VectorSearchResult"""
    
    def test_vector_search_result_creation(self):
        """Test creación de resultado de búsqueda vectorial"""
        embedding = [0.1, 0.2, 0.3] + [0.0] * 1533
        results = [
            {"id": 1, "content": "Texto relevante", "similarity": 0.95}
        ]
        
        result = VectorSearchResult(
            query_embedding=embedding,
            results=results,
            search_time_ms=75.2,
            total_matches=1,
            threshold_used=0.7
        )
        
        self.assertEqual(len(result.query_embedding), 1536)
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.search_time_ms, 75.2)
        self.assertEqual(result.total_matches, 1)
        self.assertEqual(result.threshold_used, 0.7)


async def run_async_tests():
    """Ejecutar tests asíncronos"""
    # Tests que requieren inicialización
    agent = DatabaseOperationsAgentWrapper()
    
    # Test de inicialización
    with patch('agents.database_operations_agent.create_engine'), \
         patch('agents.database_operations_agent.sessionmaker'):
        await agent._initialize()
        assert agent.is_ready
    
    print("✅ Tests asíncronos completados")


def test_basic_functionality():
    """Test funcionalidad básica sin async"""
    print("🧪 Ejecutando tests básicos...")
    
    # Test creación de configuración
    config = DatabaseConnectionConfig(
        host="localhost",
        database="test_db"
    )
    assert config.database_url == "postgresql://postgres:password@localhost:5432/test_db"
    print("✅ Configuración de BD correcta")
    
    # Test creación de agente
    agent = DatabaseOperationsAgentWrapper(config)
    assert agent.agent_name == "database_operations"
    assert not agent.is_ready
    print("✅ Agente creado correctamente")
    
    # Test métricas
    agent._update_query_metrics(100.0, True)
    assert agent.query_metrics["total_queries"] == 1
    assert agent.query_metrics["avg_execution_time_ms"] == 100.0
    print("✅ Métricas funcionando correctamente")
    
    print("🎉 Tests básicos completados exitosamente")


if __name__ == "__main__":
    print("🧪 Iniciando tests del Database Operations Agent")
    print("=" * 60)
    
    # Test funcionalidad básica
    try:
        test_basic_functionality()
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Error en tests básicos: {e}")
        sys.exit(1)
    
    # Ejecutar tests unitarios
    try:
        unittest.main(argv=[''], exit=False, verbosity=2)
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Error en tests unitarios: {e}")
        sys.exit(1)
    
    # Ejecutar tests asíncronos
    try:
        asyncio.run(run_async_tests())
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Error en tests asíncronos: {e}")
        sys.exit(1)
    
    print("🎉 Todos los tests completados exitosamente!")
    print("\n📝 Notas:")
    print("   - Algunos tests requieren PostgreSQL + pgvector ejecutándose")
    print("   - Los tests usan mocks para evitar dependencias externas")
    print("   - Verificar que las dependencias estén instaladas: psycopg2-binary, sqlalchemy, pgvector")