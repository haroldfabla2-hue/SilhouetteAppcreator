"""
Test suite para Integration Points del MCP Core Superior

Cubre:
- ContextForge Client
- Database Operations
- Vector Store Client
- Embedding Service
- Redis Cache Integration
- Service Integration Patterns
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch, call
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import aiohttp
import asyncpg

# Test marks
pytestmark = [pytest.mark.integration, pytest.mark.unit, pytest.mark.async_test]


class TestContextForgeClient:
    """Tests para ContextForge Client"""
    
    @pytest.fixture
    def contextforge_client(self):
        """Fixture del cliente ContextForge"""
        from services.contextforge_client import ContextForgeClient
        return ContextForgeClient
    
    @pytest.fixture
    def mock_contextforge_response(self):
        """Mock de respuesta de ContextForge"""
        return {
            "success": True,
            "context_id": "ctx_123",
            "data": {
                "session_id": "session_456",
                "messages": [
                    {"role": "user", "content": "Hello", "timestamp": "2025-11-04T05:43:15Z"},
                    {"role": "assistant", "content": "Hi there!", "timestamp": "2025-11-04T05:43:16Z"}
                ]
            },
            "metadata": {
                "created_at": "2025-11-04T05:43:15Z",
                "version": "1.0"
            }
        }
    
    async def test_client_initialization(self, contextforge_client):
        """Test de inicialización del cliente"""
        client = contextforge_client(
            base_url="http://localhost:8001",
            api_key="test_api_key",
            timeout=30
        )
        
        assert client.base_url == "http://localhost:8001"
        assert client.api_key == "test_api_key"
        assert client.timeout == 30
    
    async def test_health_check(self, contextforge_client, mock_contextforge_response):
        """Test de health check"""
        client = contextforge_client()
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-11-04T05:43:15Z"
            }
            mock_get.return_value.__aenter__.return_value = mock_response
            
            health_result = await client.health_check()
            
            assert health_result['healthy'] is True
            assert 'version' in health_result
            assert mock_get.called
    
    async def test_store_context(self, contextforge_client, mock_contextforge_response):
        """Test de almacenamiento de contexto"""
        client = contextforge_client()
        
        context_data = {
            "session_id": "session_123",
            "user_id": "user_456",
            "messages": [
                {"role": "user", "content": "Test message", "timestamp": "2025-11-04T05:43:15Z"}
            ],
            "metadata": {"source": "mcp_core"}
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_contextforge_response
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await client.store_context(context_data)
            
            assert result['success'] is True
            assert 'context_id' in result
            assert mock_post.called
    
    async def test_retrieve_context(self, contextforge_client, mock_contextforge_response):
        """Test de recuperación de contexto"""
        client = contextforge_client()
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_contextforge_response
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await client.retrieve_context(
                context_id="ctx_123",
                include_metadata=True
            )
            
            assert result['success'] is True
            assert 'data' in result
            assert mock_get.called
    
    async def test_context_search(self, contextforge_client):
        """Test de búsqueda de contexto"""
        client = contextforge_client()
        
        search_query = {
            "query": "Python programming",
            "filters": {
                "user_id": "user_456",
                "date_range": {
                    "start": "2025-11-01T00:00:00Z",
                    "end": "2025-11-04T23:59:59Z"
                }
            },
            "limit": 10
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "success": True,
                "results": [
                    {
                        "context_id": "ctx_123",
                        "score": 0.95,
                        "data": {"messages": [{"content": "Python tutorial"}]}
                    }
                ],
                "total_results": 1
            }
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await client.search_context(search_query)
            
            assert result['success'] is True
            assert 'results' in result
            assert len(result['results']) > 0
            assert result['total_results'] == 1
    
    async def test_update_context(self, contextforge_client, mock_contextforge_response):
        """Test de actualización de contexto"""
        client = contextforge_client()
        
        updates = {
            "context_id": "ctx_123",
            "updates": {
                "messages": [
                    {"role": "user", "content": "New message", "timestamp": "2025-11-04T05:44:00Z"}
                ],
                "metadata": {"last_updated": "2025-11-04T05:44:00Z"}
            }
        }
        
        with patch('aiohttp.ClientSession.put') as mock_put:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "success": True,
                "updated": True,
                "version": "1.1"
            }
            mock_put.return_value.__aenter__.return_value = mock_response
            
            result = await client.update_context(updates)
            
            assert result['success'] is True
            assert result['updated'] is True
            assert mock_put.called
    
    async def test_delete_context(self, contextforge_client):
        """Test de eliminación de contexto"""
        client = contextforge_client()
        
        with patch('aiohttp.ClientSession.delete') as mock_delete:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "success": True,
                "deleted": True
            }
            mock_delete.return_value.__aenter__.return_value = mock_response
            
            result = await client.delete_context("ctx_123")
            
            assert result['success'] is True
            assert result['deleted'] is True
            assert mock_delete.called
    
    async def test_batch_operations(self, contextforge_client):
        """Test de operaciones en lote"""
        client = contextforge_client()
        
        batch_operations = {
            "operations": [
                {"action": "store", "data": {"context_id": "ctx_1", "content": "Data 1"}},
                {"action": "store", "data": {"context_id": "ctx_2", "content": "Data 2"}},
                {"action": "store", "data": {"context_id": "ctx_3", "content": "Data 3"}}
            ]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "success": True,
                "results": [
                    {"operation": 0, "success": True, "context_id": "ctx_1"},
                    {"operation": 1, "success": True, "context_id": "ctx_2"},
                    {"operation": 2, "success": True, "context_id": "ctx_3"}
                ],
                "failed_operations": []
            }
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await client.batch_operations(batch_operations)
            
            assert result['success'] is True
            assert len(result['results']) == 3
            assert len(result['failed_operations']) == 0
    
    async def test_error_handling(self, contextforge_client):
        """Test de manejo de errores"""
        client = contextforge_client()
        
        # Simular error de API
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.json.return_value = {
                "error": "Internal server error",
                "error_code": "INTERNAL_ERROR"
            }
            mock_get.return_value.__aenter__.return_value = mock_response
            
            try:
                await client.health_check()
                assert False, "Should have raised exception"
            except Exception as e:
                assert "Internal server error" in str(e)


class TestDatabaseOperations:
    """Tests para operaciones de base de datos"""
    
    @pytest.fixture
    def mock_db_pool(self):
        """Mock del pool de conexiones de BD"""
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value = AsyncMock()
        mock_pool.release.return_value = None
        mock_pool.close.return_value = None
        return mock_pool
    
    @pytest.fixture
    def database_operations(self, mock_db_pool):
        """Fixture de operaciones de BD"""
        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_create_pool.return_value = mock_db_pool
            
            from database.database import DatabaseManager
            return DatabaseManager
    
    async def test_db_initialization(self, database_operations, mock_db_pool):
        """Test de inicialización de BD"""
        db = database_operations(
            database_url="postgresql://user:pass@localhost:5432/test_db"
        )
        
        result = await db.initialize()
        
        assert result['success'] is True
        assert db.initialized is True
        assert mock_db_pool.acquire.called
    
    async def test_execute_query(self, database_operations, mock_db_pool):
        """Test de ejecución de queries"""
        db = database_operations()
        
        query = "SELECT * FROM users WHERE id = $1"
        params = ["user_123"]
        
        # Mock de conexión y resultado
        mock_conn = AsyncMock()
        mock_result = AsyncMock()
        mock_result.fetch.return_value = [
            {"id": "user_123", "name": "Test User", "email": "test@example.com"}
        ]
        mock_conn.fetch.return_value = mock_result
        
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        result = await db.execute_query(query, params)
        
        assert result['success'] is True
        assert 'data' in result
        assert len(result['data']) > 0
        assert result['data'][0]['id'] == "user_123"
    
    async def test_execute_transaction(self, database_operations, mock_db_pool):
        """Test de ejecución de transacciones"""
        db = database_operations()
        
        operations = [
            {
                "query": "INSERT INTO users (id, name) VALUES ($1, $2)",
                "params": ["user_123", "Test User"]
            },
            {
                "query": "UPDATE users SET email = $1 WHERE id = $2",
                "params": ["newemail@example.com", "user_123"]
            }
        ]
        
        mock_conn = AsyncMock()
        mock_conn.executemany.return_value = None
        
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        result = await db.execute_transaction(operations)
        
        assert result['success'] is True
        assert result['committed'] is True
        mock_conn.executemany.assert_called()
    
    async def test_create_table(self, database_operations, mock_db_pool):
        """Test de creación de tablas"""
        db = database_operations()
        
        table_definition = {
            "name": "user_profiles",
            "columns": {
                "id": "UUID PRIMARY KEY DEFAULT gen_random_uuid()",
                "user_id": "VARCHAR(255) NOT NULL",
                "profile_data": "JSONB",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            }
        }
        
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "CREATE TABLE user_profiles..."
        
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        result = await db.create_table(table_definition)
        
        assert result['success'] is True
        assert 'table_created' in result
        mock_conn.execute.assert_called()
    
    async def test_migration_operations(self, database_operations, mock_db_pool):
        """Test de operaciones de migración"""
        db = database_operations()
        
        migration_sql = """
        ALTER TABLE users ADD COLUMN last_login TIMESTAMP;
        CREATE INDEX idx_users_last_login ON users(last_login);
        """
        
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "Migration applied"
        
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        result = await db.apply_migration(migration_sql)
        
        assert result['success'] is True
        assert result['applied'] is True
        mock_conn.execute.assert_called()
    
    async def test_backup_operations(self, database_operations, mock_db_pool):
        """Test de operaciones de backup"""
        db = database_operations()
        
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = MagicMock(returncode=0, stdout="Backup completed")
            
            result = await db.create_backup(
                database="test_db",
                backup_path="/backups/test_backup.sql"
            )
            
            assert result['success'] is True
            assert result['backup_path'] == "/backups/test_backup.sql"
            assert result['size_mb'] > 0
    
    async def test_connection_pooling(self, database_operations, mock_db_pool):
        """Test de pooling de conexiones"""
        db = database_operations(
            database_url="postgresql://user:pass@localhost:5432/test_db",
            pool_size=10,
            max_overflow=20
        )
        
        # Verificar configuración del pool
        pool_config = db.get_pool_config()
        
        assert pool_config['pool_size'] == 10
        assert pool_config['max_overflow'] == 20
        assert pool_config['pool_timeout'] == 30
    
    async def test_query_optimization(self, database_operations, mock_db_pool):
        """Test de optimización de queries"""
        db = database_operations()
        
        # Query compleja que necesita optimización
        complex_query = """
        SELECT u.id, u.name, p.profile_data 
        FROM users u 
        JOIN user_profiles p ON u.id = p.user_id 
        WHERE u.created_at > $1 AND p.status = 'active'
        ORDER BY u.last_login DESC
        LIMIT 100
        """
        
        mock_conn = AsyncMock()
        mock_result = AsyncMock()
        mock_result.fetch.return_value = []  # Empty result for performance test
        mock_conn.fetch.return_value = mock_result
        
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        # Analizar y optimizar query
        optimization_result = await db.optimize_query(complex_query)
        
        assert 'optimized' in optimization_result
        assert 'execution_plan' in optimization_result
        assert 'performance_score' in optimization_result


class TestVectorStoreClient:
    """Tests para Vector Store Client"""
    
    @pytest.fixture
    def vector_store_client(self):
        """Fixture del cliente de vector store"""
        from services.vector_store_client import VectorStoreClient
        return VectorStoreClient
    
    @pytest.fixture
    def mock_vector_store(self):
        """Mock del vector store"""
        mock_client = AsyncMock()
        mock_client.embed.return_value = [0.1] * 1536
        mock_client.similarity_search.return_value = [
            {
                "id": "doc_1",
                "score": 0.95,
                "metadata": {"title": "Python Tutorial", "source": "docs"},
                "content": "Python is a programming language..."
            }
        ]
        return mock_client
    
    async def test_embedding_generation(self, vector_store_client, mock_vector_store):
        """Test de generación de embeddings"""
        client = vector_store_client()
        client.client = mock_vector_store
        
        text = "Python is a powerful programming language for data science"
        
        embedding = await client.generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536  # Dimensión estándar
        assert all(isinstance(x, float) for x in embedding)
        mock_vector_store.embed.assert_called_once_with([text])
    
    async def test_similarity_search(self, vector_store_client, mock_vector_store):
        """Test de búsqueda por similitud"""
        client = vector_store_client()
        client.client = mock_vector_store
        
        query = "What is Python programming?"
        search_params = {
            "k": 5,
            "threshold": 0.7,
            "filters": {"source": "documentation"}
        }
        
        results = await client.similarity_search(query, **search_params)
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        for result in results:
            assert 'id' in result
            assert 'score' in result
            assert 'metadata' in result
            assert 'content' in result
    
    async def test_store_embeddings(self, vector_store_client, mock_vector_store):
        """Test de almacenamiento de embeddings"""
        client = vector_store_client()
        client.client = mock_vector_store
        
        documents = [
            {
                "id": "doc_1",
                "content": "Python tutorial for beginners",
                "metadata": {"category": "tutorial", "difficulty": "beginner"}
            },
            {
                "id": "doc_2", 
                "content": "Advanced Python concepts",
                "metadata": {"category": "tutorial", "difficulty": "advanced"}
            }
        ]
        
        with patch.object(client, 'generate_embedding') as mock_embed:
            mock_embed.return_value = [0.1] * 1536
            
            result = await client.store_embeddings(documents)
            
            assert result['success'] is True
            assert result['stored_count'] == 2
            assert mock_embed.call_count == 2  # Una vez por documento
    
    async def test_batch_operations(self, vector_store_client, mock_vector_store):
        """Test de operaciones en lote"""
        client = vector_store_client()
        client.client = mock_vector_store
        
        batch_requests = [
            {
                "operation": "similarity_search",
                "query": "Python basics",
                "params": {"k": 3}
            },
            {
                "operation": "similarity_search", 
                "query": "Advanced programming",
                "params": {"k": 3}
            }
        ]
        
        with patch.object(client, 'similarity_search') as mock_search:
            mock_search.return_value = [{"id": "doc_1", "score": 0.9}]
            
            results = await client.batch_operations(batch_requests)
            
            assert len(results) == 2
            assert all('result' in r for r in results)
            assert mock_search.call_count == 2
    
    async def test_collection_management(self, vector_store_client, mock_vector_store):
        """Test de gestión de colecciones"""
        client = vector_store_client()
        client.client = mock_vector_store
        
        # Crear colección
        collection_config = {
            "name": "python_documentation",
            "dimension": 1536,
            "distance_metric": "cosine",
            "metadata_schema": {
                "title": "text",
                "category": "text",
                "difficulty": "text"
            }
        }
        
        create_result = await client.create_collection(collection_config)
        assert create_result['success'] is True
        
        # Listar colecciones
        list_result = await client.list_collections()
        assert 'collections' in list_result
        
        # Eliminar colección
        delete_result = await client.delete_collection("python_documentation")
        assert delete_result['success'] is True
    
    async def test_vector_analytics(self, vector_store_client, mock_vector_store):
        """Test de análisis de vectores"""
        client = vector_store_client()
        client.client = mock_vector_store
        
        analytics = await client.get_collection_analytics("python_documentation")
        
        assert 'total_documents' in analytics
        assert 'embedding_stats' in analytics
        assert 'query_stats' in analytics
        assert 'last_updated' in analytics


class TestEmbeddingService:
    """Tests para el servicio de embeddings"""
    
    @pytest.fixture
    def embedding_service(self):
        """Fixture del servicio de embeddings"""
        from services.embedding_service import EmbeddingService
        return EmbeddingService
    
    async def test_model_loading(self, embedding_service):
        """Test de carga de modelo"""
        service = embedding_service(
            model_name="text-embedding-ada-002",
            api_key="test_api_key"
        )
        
        with patch.object(service, '_load_model') as mock_load:
            mock_load.return_value = True
            
            result = await service.initialize()
            
            assert result['success'] is True
            assert service.initialized is True
            mock_load.assert_called_once()
    
    async def test_single_embedding(self, embedding_service):
        """Test de embedding único"""
        service = embedding_service()
        
        text = "This is a test sentence for embedding generation"
        
        with patch.object(service, '_call_embedding_api') as mock_api:
            mock_api.return_value = {
                "embedding": [0.1] * 1536,
                "usage": {"prompt_tokens": 10, "total_tokens": 10}
            }
            
            result = await service.generate_embedding(text)
            
            assert 'embedding' in result
            assert 'usage' in result
            assert len(result['embedding']) == 1536
            mock_api.assert_called_once_with([text])
    
    async def test_batch_embeddings(self, embedding_service):
        """Test de embeddings en lote"""
        service = embedding_service()
        
        texts = [
            "First sentence about Python programming",
            "Second sentence about machine learning",
            "Third sentence about data analysis"
        ]
        
        with patch.object(service, '_call_embedding_api') as mock_api:
            mock_api.return_value = {
                "embeddings": [[0.1] * 1536 for _ in texts],
                "usage": {"prompt_tokens": 30, "total_tokens": 30}
            }
            
            result = await service.generate_batch_embeddings(texts)
            
            assert 'embeddings' in result
            assert 'usage' in result
            assert len(result['embeddings']) == 3
            assert len(result['embeddings'][0]) == 1536
            mock_api.assert_called_once_with(texts)
    
    async def test_embedding_quality_check(self, embedding_service):
        """Test de verificación de calidad de embeddings"""
        service = embedding_service()
        
        embedding = [0.1] * 1536
        reference_embedding = [0.1] * 1536
        
        quality_metrics = await service.check_embedding_quality(
            embedding,
            reference_embedding
        )
        
        assert 'cosine_similarity' in quality_metrics
        assert 'euclidean_distance' in quality_metrics
        assert 'quality_score' in quality_metrics
        assert 0 <= quality_metrics['quality_score'] <= 1
    
    async def test_model_switching(self, embedding_service):
        """Test de cambio de modelo"""
        service = embedding_service()
        
        new_model_config = {
            "model_name": "text-embedding-3-large",
            "dimension": 3072,
            "max_tokens": 8192
        }
        
        with patch.object(service, '_switch_model') as mock_switch:
            mock_switch.return_value = True
            
            result = await service.switch_model(new_model_config)
            
            assert result['success'] is True
            assert service.model_config == new_model_config
            mock_switch.assert_called_once_with(new_model_config)
    
    async def test_caching_mechanism(self, embedding_service):
        """Test de mecanismo de caché"""
        service = embedding_service()
        
        text = "Cached embedding test"
        
        # Primera vez - no cache
        with patch.object(service, '_call_embedding_api') as mock_api:
            mock_api.return_value = {"embedding": [0.1] * 1536}
            
            result1 = await service.generate_embedding(text)
            assert not mock_api.call_count == 0
        
        # Segunda vez - desde cache
        with patch.object(service, '_get_cached_embedding') as mock_cache:
            mock_cache.return_value = [0.1] * 1536
            
            result2 = await service.generate_embedding(text)
            assert mock_cache.called
    
    async def test_usage_tracking(self, embedding_service):
        """Test de seguimiento de uso"""
        service = embedding_service()
        
        # Simular uso del servicio
        await service.generate_embedding("Test 1")
        await service.generate_batch_embeddings(["Test 2", "Test 3"])
        
        usage_stats = service.get_usage_stats()
        
        assert 'total_requests' in usage_stats
        assert 'total_tokens' in usage_stats
        assert 'requests_today' in usage_stats
        assert usage_stats['total_requests'] == 2  # 1 single + 1 batch


class TestRedisCacheIntegration:
    """Tests para integración con Redis Cache"""
    
    @pytest.fixture
    def redis_cache(self):
        """Fixture del cache Redis"""
        from database.redis_cache import RedisCache
        return RedisCache
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock del cliente Redis"""
        mock_client = AsyncMock()
        mock_client.get.return_value = None
        mock_client.set.return_value = True
        mock_client.delete.return_value = 1
        mock_client.exists.return_value = False
        mock_client.expire.return_value = True
        return mock_client
    
    async def test_cache_initialization(self, redis_cache, mock_redis_client):
        """Test de inicialización del cache"""
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_from_url.return_value = mock_redis_client
            
            cache = redis_cache(
                redis_url="redis://localhost:6379/0",
                ttl_seconds=3600
            )
            
            result = await cache.initialize()
            
            assert result['success'] is True
            assert cache.initialized is True
            mock_from_url.assert_called_once()
    
    async def test_basic_cache_operations(self, redis_cache, mock_redis_client):
        """Test de operaciones básicas de cache"""
        cache = redis_cache()
        cache.client = mock_redis_client
        
        key = "test_key"
        value = {"data": "test_value"}
        
        # Set
        mock_redis_client.set.return_value = True
        result = await cache.set(key, value)
        assert result is True
        
        # Get (cache miss)
        mock_redis_client.get.return_value = None
        result = await cache.get(key)
        assert result is None
        
        # Get (cache hit)
        mock_redis_client.get.return_value = json.dumps(value).encode()
        result = await cache.get(key)
        assert result == value
    
    async def test_cache_expiration(self, redis_cache, mock_redis_client):
        """Test de expiración de cache"""
        cache = redis_cache()
        cache.client = mock_redis_client
        
        key = "expiring_key"
        value = {"data": "expires_soon"}
        ttl = 300  # 5 minutos
        
        mock_redis_client.set.return_value = True
        mock_redis_client.expire.return_value = True
        
        result = await cache.set_with_ttl(key, value, ttl)
        
        assert result is True
        mock_redis_client.set.assert_called()
        mock_redis_client.expire.assert_called()
    
    async def test_cache_invalidation(self, redis_cache, mock_redis_client):
        """Test de invalidación de cache"""
        cache = redis_cache()
        cache.client = mock_redis_client
        
        # Invalidar clave específica
        mock_redis_client.delete.return_value = 1
        result = await cache.invalidate("specific_key")
        assert result is True
        
        # Invalidar por patrón
        mock_redis_client.eval.return_value = 2  # Number of keys deleted
        result = await cache.invalidate_pattern("user:*")
        assert result == 2
    
    async def test_batch_operations(self, redis_cache, mock_redis_client):
        """Test de operaciones en lote"""
        cache = redis_cache()
        cache.client = mock_redis_client
        
        # Batch set
        key_values = {
            "key1": {"data": "value1"},
            "key2": {"data": "value2"},
            "key3": {"data": "value3"}
        }
        
        mock_redis_client.mset.return_value = True
        result = await cache.batch_set(key_values)
        assert result['success'] is True
        
        # Batch get
        mock_redis_client.mget.return_value = [
            json.dumps({"data": "value1"}).encode(),
            json.dumps({"data": "value2"}).encode(),
            None  # Key3 no existe
        ]
        
        result = await cache.batch_get(["key1", "key2", "key3"])
        assert len(result['values']) == 3
        assert result['values'][0] == {"data": "value1"}
        assert result['values'][1] == {"data": "value2"}
        assert result['values'][2] is None
    
    async def test_cache_statistics(self, redis_cache, mock_redis_client):
        """Test de estadísticas de cache"""
        cache = redis_cache()
        cache.client = mock_redis_client
        
        with patch.object(cache, '_get_cache_stats') as mock_stats:
            mock_stats.return_value = {
                "hits": 150,
                "misses": 25,
                "hit_ratio": 0.857,
                "total_keys": 50,
                "memory_usage": "2.5MB"
            }
            
            stats = await cache.get_statistics()
            
            assert stats['hits'] == 150
            assert stats['misses'] == 25
            assert stats['hit_ratio'] == 0.857
            assert stats['total_keys'] == 50
    
    async def test_cache_warming(self, redis_cache, mock_redis_client):
        """Test de cache warming"""
        cache = redis_cache()
        cache.client = mock_redis_client
        
        # Datos para pre-cargar
        warm_data = [
            {"key": "popular_item_1", "value": {"popular": True}},
            {"key": "popular_item_2", "value": {"popular": True}},
            {"key": "config_data", "value": {"app": "mcp_core", "version": "1.0"}}
        ]
        
        with patch.object(cache, '_load_warm_data') as mock_load:
            mock_load.return_value = True
            
            result = await cache.warm_cache(warm_data)
            
            assert result['success'] is True
            assert result['warmed_keys'] == 3
            mock_load.assert_called_once_with(warm_data)


class TestServiceIntegrationPatterns:
    """Tests para patrones de integración de servicios"""
    
    @pytest.fixture
    def service_registry(self):
        """Fixture del registro de servicios"""
        from services.service_registry import ServiceRegistry
        return ServiceRegistry
    
    @pytest.fixture
    def integration_manager(self):
        """Fixture del manager de integración"""
        from services.integration_manager import IntegrationManager
        return IntegrationManager
    
    async def test_service_discovery(self, service_registry):
        """Test de descubrimiento de servicios"""
        registry = service_registry()
        
        # Registrar servicios
        services = [
            {
                "name": "contextforge",
                "version": "1.0.0",
                "endpoint": "http://localhost:8001",
                "capabilities": ["context_storage", "context_search"]
            },
            {
                "name": "vector_store",
                "version": "2.1.0", 
                "endpoint": "http://localhost:8002",
                "capabilities": ["embedding", "similarity_search"]
            }
        ]
        
        for service in services:
            await registry.register_service(service)
        
        # Descubrir servicios por capacidades
        context_services = await registry.find_services_by_capability("context_storage")
        assert len(context_services) == 1
        assert context_services[0]['name'] == "contextforge"
        
        # Descubrir todas las versiones de un servicio
        all_versions = await registry.get_service_versions("contextforge")
        assert len(all_versions) >= 1
    
    async def test_service_health_monitoring(self, service_registry):
        """Test de monitoreo de salud de servicios"""
        registry = service_registry()
        
        # Simular health check
        with patch.object(registry, '_check_service_health') as mock_health:
            mock_health.return_value = {
                "healthy": True,
                "response_time": 0.05,
                "last_check": "2025-11-04T05:43:15Z"
            }
            
            health_status = await registry.check_service_health("contextforge")
            
            assert health_status['healthy'] is True
            assert health_status['response_time'] <= 0.1
            mock_health.assert_called_once()
    
    async def test_circuit_breaker_pattern(self, integration_manager):
        """Test de patrón circuit breaker"""
        manager = integration_manager()
        
        # Configurar circuit breaker para servicio
        circuit_config = {
            "failure_threshold": 3,
            "recovery_timeout": 30,
            "expected_exception": Exception
        }
        
        await manager.configure_circuit_breaker("contextforge", circuit_config)
        
        # Simular fallos consecutivos
        for i in range(3):
            try:
                await manager.call_service("contextforge", "health_check")
            except Exception:
                pass  # Esperar fallos
        
        # Verificar que circuit breaker está abierto
        cb_status = manager.get_circuit_breaker_status("contextforge")
        assert cb_status['state'] == "open"
        assert cb_status['failure_count'] >= 3
    
    async def test_retry_pattern(self, integration_manager):
        """Test de patrón de retry"""
        # Configurar política de retry
        retry_policy = {
            "max_attempts": 3,
            "base_delay": 1.0,
            "max_delay": 10.0,
            "backoff_factor": 2.0,
            "jitter": True
        }
        
        await manager.configure_retry_policy("search_service", retry_policy)
        
        # Simular call con retry
        with patch.object(manager, '_make_service_call') as mock_call:
            mock_call.side_effect = [
                Exception("Temporary error"),
                Exception("Temporary error"), 
                {"success": True, "result": "data"}  # Éxito en tercer intento
            ]
            
            result = await manager.call_service_with_retry("search_service", "search", {})
            
            assert result['success'] is True
            assert mock_call.call_count == 3  # 2 fallos + 1 éxito
    
    async def test_service_composition(self, integration_manager):
        """Test de composición de servicios"""
        # Definir workflow de servicios
        workflow = {
            "name": "data_processing_pipeline",
            "steps": [
                {
                    "service": "contextforge",
                    "operation": "retrieve_context",
                    "input_field": "session_id",
                    "output_field": "context_data"
                },
                {
                    "service": "vector_store", 
                    "operation": "generate_embedding",
                    "input_field": "context_data.content",
                    "output_field": "embedding"
                },
                {
                    "service": "embedding_service",
                    "operation": "enhance_embedding",
                    "input_field": "embedding",
                    "output_field": "enhanced_embedding"
                }
            ],
            "data_flow": {
                "session_id": "user_session_123",
                "enhancement_params": {"model": "advanced", "dimensions": 3072}
            }
        }
        
        with patch.object(manager, '_execute_service_workflow') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "final_result": {
                    "enhanced_embedding": [0.1] * 3072,
                    "processing_time": 2.5
                }
            }
            
            result = await manager.execute_service_workflow(workflow)
            
            assert result['success'] is True
            assert 'final_result' in result
            assert len(result['final_result']['enhanced_embedding']) == 3072
            mock_execute.assert_called_once()
    
    async def test_load_balancing_across_services(self, integration_manager):
        """Test de balanceador de carga entre servicios"""
        # Configurar múltiples instancias de servicio
        service_instances = [
            {
                "name": "contextforge_primary",
                "endpoint": "http://contextforge-1:8001",
                "weight": 3,
                "health": True
            },
            {
                "name": "contextforge_secondary",
                "endpoint": "http://contextforge-2:8001", 
                "weight": 2,
                "health": True
            },
            {
                "name": "contextforge_backup",
                "endpoint": "http://contextforge-3:8001",
                "weight": 1,
                "health": False  # Instancia no saludable
            }
        ]
        
        await manager.register_service_instances("contextforge", service_instances)
        
        # Simular múltiples llamadas y verificar distribución
        call_distribution = {}
        for i in range(10):
            selected_instance = await manager.select_service_instance("contextforge")
            instance_name = selected_instance['name']
            call_distribution[instance_name] = call_distribution.get(instance_name, 0) + 1
        
        # Verificar que las instancias más pesadas reciben más llamadas
        assert call_distribution["contextforge_primary"] > call_distribution["contextforge_backup"]
        assert call_distribution["contextforge_secondary"] >= call_distribution["contextforge_backup"]
    
    async def test_service_monitoring_and_metrics(self, integration_manager):
        """Test de monitoreo y métricas de servicios"""
        # Simular métricas de servicios
        service_metrics = {
            "contextforge": {
                "total_requests": 1000,
                "successful_requests": 950,
                "failed_requests": 50,
                "avg_response_time": 0.15,
                "availability": 0.95
            },
            "vector_store": {
                "total_requests": 500,
                "successful_requests": 490,
                "failed_requests": 10,
                "avg_response_time": 0.08,
                "availability": 0.98
            }
        }
        
        with patch.object(manager, '_collect_service_metrics') as mock_collect:
            mock_collect.return_value = service_metrics
            
            aggregated_metrics = await manager.get_service_metrics()
            
            assert 'contextforge' in aggregated_metrics
            assert 'vector_store' in aggregated_metrics
            assert aggregated_metrics['contextforge']['availability'] == 0.95
    
    async def test_fallback_mechanism(self, integration_manager):
        """Test de mecanismo de fallback"""
        # Configurar servicios de fallback
        fallback_config = {
            "primary_service": "vector_store",
            "fallback_services": [
                {
                    "name": "redis_cache",
                    "operation": "cached_embedding_lookup"
                },
                {
                    "name": "file_storage", 
                    "operation": "precomputed_embedding"
                }
            ]
        }
        
        await manager.configure_fallback(fallback_config)
        
        # Simular fallo del servicio primario
        with patch.object(manager, '_make_service_call') as mock_call:
            mock_call.side_effect = Exception("Primary service unavailable")
            
            # Simular éxito en fallback
            mock_call.side_effect = [
                Exception("Primary unavailable"),
                {"success": True, "embedding": [0.1] * 1536}  # Fallback success
            ]
            
            result = await manager.call_service_with_fallback(
                "vector_store", 
                "generate_embedding", 
                {"text": "test"}
            )
            
            assert result['success'] is True
            assert 'embedding' in result