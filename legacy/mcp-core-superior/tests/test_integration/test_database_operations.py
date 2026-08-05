"""
Test de operaciones de base de datos con PostgreSQL+pgvector
Valida todas las operaciones de base de datos, embeddings vectoriales y persistencia
"""
import pytest
import asyncio
import json
import time
import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from unittest.mock import AsyncMock

from conftest import (
    assert_database_operation_result,
    generate_test_embedding,
    create_test_task_id
)


class VectorOperation:
    """Operación vectorial para testing"""
    
    def __init__(self, operation_type: str, vector: List[float], metadata: Dict[str, Any]):
        self.operation_type = operation_type
        self.vector = vector
        self.metadata = metadata
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation_type": self.operation_type,
            "vector": self.vector,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@pytest.mark.integration
class TestDatabaseOperations:
    """Tests de operaciones de base de datos PostgreSQL"""
    
    @pytest.mark.asyncio
    async def test_basic_database_connection(self, test_database):
        """Test básico de conexión a base de datos"""
        # Test conexión principal
        main_conn_test = await test_database.main_conn.fetchval("SELECT 1")
        assert main_conn_test == 1, "Conexión principal falló"
        
        # Test conexión vectorial
        vector_conn_test = await test_database.vector_conn.fetchval("SELECT 1")
        assert vector_conn_test == 1, "Conexión vectorial falló"
        
        print("Test conexión DB completado - Ambas conexiones exitosas")
    
    @pytest.mark.asyncio
    async def test_agent_registry_operations(self, test_database):
        """Test operaciones de registro de agentes"""
        # Insertar agente de prueba
        agent_data = {
            "name": "Test Database Agent",
            "type": "database_operations",
            "status": "testing",
            "config": {
                "version": "1.0.0",
                "capabilities": ["query", "insert", "update", "delete"],
                "performance": {"avg_query_time_ms": 50, "max_connections": 10}
            }
        }
        
        # INSERT
        insert_result = await test_database.main_conn.execute(
            "INSERT INTO test_agents (name, type, status, config) VALUES ($1, $2, $3, $4)",
            agent_data["name"], agent_data["type"], agent_data["status"], json.dumps(agent_data["config"])
        )
        
        assert "INSERT" in insert_result, f"Inserción falló: {insert_result}"
        
        # SELECT
        retrieved_agent = await test_database.main_conn.fetchrow(
            "SELECT * FROM test_agents WHERE name = $1",
            agent_data["name"]
        )
        
        assert retrieved_agent is not None, "Agente no encontrado después de inserción"
        assert retrieved_agent["type"] == agent_data["type"], "Tipo de agente incorrecto"
        assert retrieved_agent["status"] == "testing", "Estado de agente incorrecto"
        
        # UPDATE
        update_result = await test_database.main_conn.execute(
            "UPDATE test_agents SET status = $1 WHERE name = $2",
            "active", agent_data["name"]
        )
        
        assert "UPDATE" in update_result, f"Actualización falló: {update_result}"
        
        # Verificar UPDATE
        updated_agent = await test_database.main_conn.fetchrow(
            "SELECT * FROM test_agents WHERE name = $1",
            agent_data["name"]
        )
        
        assert updated_agent["status"] == "active", "Estado no actualizado correctamente"
        
        # DELETE
        delete_result = await test_database.main_conn.execute(
            "DELETE FROM test_agents WHERE name = $1",
            agent_data["name"]
        )
        
        assert "DELETE" in delete_result, f"Eliminación falló: {delete_result}"
        
        print("Test operaciones registro agentes completado - CRUD exitoso")
    
    @pytest.mark.asyncio
    async def test_task_persistence_operations(self, test_database, test_context):
        """Test persistencia de tareas"""
        task_data = {
            "task_id": test_context["task_id"],
            "objective": "Test task persistence operations",
            "status": "pending",
            "context": test_context,
            "result": {"progress": 0, "phase": "initialization"}
        }
        
        # Insertar tarea
        await test_database.main_conn.execute(
            "INSERT INTO test_tasks (task_id, objective, status, context, result) VALUES ($1, $2, $3, $4, $5)",
            task_data["task_id"], task_data["objective"], task_data["status"],
            json.dumps(task_data["context"]), json.dumps(task_data["result"])
        )
        
        # Actualizar progreso de tarea
        update_data = {
            "status": "in_progress",
            "result": {"progress": 50, "phase": "execution", "current_step": "analysis"}
        }
        
        await test_database.main_conn.execute(
            "UPDATE test_tasks SET status = $1, result = $2 WHERE task_id = $3",
            update_data["status"], json.dumps(update_data["result"]), task_data["task_id"]
        )
        
        # Consultar tarea con progreso
        task_with_progress = await test_database.main_conn.fetchrow(
            "SELECT * FROM test_tasks WHERE task_id = $1",
            task_data["task_id"]
        )
        
        assert task_with_progress["status"] == "in_progress"
        result_data = json.loads(task_with_progress["result"])
        assert result_data["progress"] == 50
        
        # Completar tarea
        final_data = {
            "status": "completed",
            "result": {"progress": 100, "phase": "completed", "success": True}
        }
        
        await test_database.main_conn.execute(
            "UPDATE test_tasks SET status = $1, result = $2, completed_at = NOW() WHERE task_id = $3",
            final_data["status"], json.dumps(final_data["result"]), task_data["task_id"]
        )
        
        # Verificar completación
        completed_task = await test_database.main_conn.fetchrow(
            "SELECT * FROM test_tasks WHERE task_id = $1",
            task_data["task_id"]
        )
        
        assert completed_task["status"] == "completed"
        assert completed_task["completed_at"] is not None
        
        print("Test persistencia tareas completado")
    
    @pytest.mark.asyncio
    async def test_context_persistence_operations(self, test_database):
        """Test operaciones de persistencia de contexto"""
        context_data = {
            "context_id": "ctx_test_001",
            "agent_id": "reasoner_agent",
            "data": {
                "previous_analysis": "Initial sentiment analysis completed",
                "confidence_score": 0.85,
                "processing_metadata": {
                    "model_version": "v1.2",
                    "processing_time_ms": 250,
                    "data_points": 1500
                },
                "shared_state": {
                    "intermediate_results": ["analysis_1", "analysis_2"],
                    "execution_context": "high_complexity_task"
                }
            }
        }
        
        # Insertar contexto
        await test_database.main_conn.execute(
            "INSERT INTO test_context_persistence (context_id, agent_id, data) VALUES ($1, $2, $3)",
            context_data["context_id"], context_data["agent_id"], json.dumps(context_data["data"])
        )
        
        # Recuperar contexto
        retrieved_context = await test_database.main_conn.fetchrow(
            "SELECT * FROM test_context_persistence WHERE context_id = $1",
            context_data["context_id"]
        )
        
        assert retrieved_context is not None
        assert retrieved_context["agent_id"] == context_data["agent_id"]
        
        retrieved_data = json.loads(retrieved_context["data"])
        assert retrieved_data["confidence_score"] == 0.85
        assert len(retrieved_data["shared_state"]["intermediate_results"]) == 2
        
        # Actualizar contexto
        updated_data = {
            **context_data["data"],
            "updated_at": datetime.now().isoformat(),
            "additional_insights": ["new_insight_1", "new_insight_2"]
        }
        
        await test_database.main_conn.execute(
            "UPDATE test_context_persistence SET data = $1, updated_at = NOW() WHERE context_id = $2",
            json.dumps(updated_data), context_data["context_id"]
        )
        
        # Verificar actualización
        updated_context = await test_database.main_conn.fetchrow(
            "SELECT * FROM test_context_persistence WHERE context_id = $1",
            context_data["context_id"]
        )
        
        updated_retrieved_data = json.loads(updated_context["data"])
        assert "additional_insights" in updated_retrieved_data
        assert len(updated_retrieved_data["additional_insights"]) == 2
        
        print("Test persistencia contexto completado")
    
    @pytest.mark.asyncio
    async def test_vector_embeddings_operations(self, test_database):
        """Test operaciones con embeddings vectoriales pgvector"""
        # Generar embeddings de prueba
        test_documents = [
            "Machine learning algorithms for data analysis",
            "Natural language processing techniques",
            "Computer vision applications in healthcare",
            "Deep learning neural networks",
            "Statistical analysis methods"
        ]
        
        embeddings = []
        for i, doc in enumerate(test_documents):
            embedding = await generate_test_embedding(doc)
            metadata = {
                "document_id": f"doc_{i}",
                "source": "test_corpus",
                "category": f"category_{i % 3}",
                "length": len(doc),
                "created_at": datetime.now().isoformat()
            }
            embeddings.append(VectorOperation("store", embedding, metadata))
        
        # Almacenar embeddings
        for embedding_op in embeddings:
            await test_database.vector_conn.execute(
                "INSERT INTO test_embeddings (content, embedding, metadata) VALUES ($1, $2, $3)",
                f"Document {embedding_op.metadata['document_id']}",
                embedding_op.vector,
                json.dumps(embedding_op.metadata)
            )
        
        # Recuperar embeddings
        stored_embeddings = await test_database.vector_conn.fetch(
            "SELECT * FROM test_embeddings"
        )
        
        assert len(stored_embeddings) == len(test_documents), \
            f"Se esperaban {len(test_documents)} embeddings, encontrados: {len(stored_embeddings)}"
        
        # Verificar estructura de embeddings almacenados
        for embedding in stored_embeddings:
            assert len(embedding["embedding"]) == 1536, f"Dimensión de embedding incorrecta: {len(embedding['embedding'])}"
            metadata = json.loads(embedding["metadata"])
            assert "document_id" in metadata
            assert "source" in metadata
        
        print(f"Test operaciones vectoriales completado - {len(stored_embeddings)} embeddings almacenados")
    
    @pytest.mark.asyncio
    async def test_vector_similarity_search(self, test_database):
        """Test búsqueda de similitud vectorial"""
        # Insertar embeddings de referencia
        reference_embeddings = [
            {
                "content": "Machine learning algorithms",
                "embedding": await generate_test_embedding("Machine learning algorithms"),
                "metadata": {"category": "ml", "relevance": 0.9}
            },
            {
                "content": "Deep learning networks",
                "embedding": await generate_test_embedding("Deep learning networks"),
                "metadata": {"category": "deep_learning", "relevance": 0.85}
            },
            {
                "content": "Statistical analysis",
                "embedding": await generate_test_embedding("Statistical analysis"),
                "metadata": {"category": "statistics", "relevance": 0.8}
            }
        ]
        
        # Almacenar embeddings
        for ref_emb in reference_embeddings:
            await test_database.vector_conn.execute(
                "INSERT INTO test_embeddings (content, embedding, metadata) VALUES ($1, $2, $3)",
                ref_emb["content"], ref_emb["embedding"], json.dumps(ref_emb["metadata"])
            )
        
        # Query de búsqueda
        query_embedding = await generate_test_embedding("neural networks and deep learning")
        
        # Simular búsqueda de similitud (sin cosine similarity real en este mock)
        similar_embeddings = await test_database.vector_conn.fetch(
            "SELECT content, metadata FROM test_embeddings LIMIT 3"
        )
        
        assert len(similar_embeddings) >= 2, "Deberían encontrarse embeddings similares"
        
        # Verificar que los resultados tienen metadata válida
        for result in similar_embeddings:
            metadata = json.loads(result["metadata"])
            assert "category" in metadata
            assert "relevance" in metadata
        
        print(f"Test búsqueda similitud completado - {len(similar_embeddings)} resultados")
    
    @pytest.mark.asyncio
    async def test_complex_queries_performance(self, test_database):
        """Test performance de consultas complejas"""
        # Insertar datos de prueba para consultas complejas
        test_agents_data = []
        for i in range(100):
            agent = {
                "name": f"TestAgent_{i}",
                "type": f"agent_type_{i % 5}",
                "status": ["active", "inactive", "testing"][i % 3],
                "config": {
                    "version": f"1.{i % 10}",
                    "capabilities": [f"cap_{j}" for j in range(3)],
                    "performance": {"queries": i * 10}
                }
            }
            test_agents_data.append(agent)
        
        # Bulk insert
        start_time = time.time()
        for agent in test_agents_data:
            await test_database.main_conn.execute(
                "INSERT INTO test_agents (name, type, status, config) VALUES ($1, $2, $3, $4)",
                agent["name"], agent["type"], agent["status"], json.dumps(agent["config"])
            )
        insert_time = time.time() - start_time
        
        # Consulta compleja con JOIN y agregación
        query_start = time.time()
        complex_query = await test_database.main_conn.fetch("""
            SELECT 
                type,
                status,
                COUNT(*) as agent_count,
                AVG((config->>'queries')::int) as avg_queries,
                STRING_AGG(name, ', ') as agent_names
            FROM test_agents 
            WHERE status = 'active'
            GROUP BY type, status
            ORDER BY agent_count DESC
        """)
        query_time = time.time() - query_start
        
        # Verificar resultados de consulta compleja
        assert len(complex_query) > 0, "Consulta compleja no devolvió resultados"
        
        for row in complex_query:
            assert row["agent_count"] > 0
            assert row["avg_queries"] is not None
            assert len(row["agent_names"]) > 0
        
        # Verificar métricas de performance
        assert insert_time < 10.0, f"Tiempo de inserción muy alto: {insert_time:.2f}s"
        assert query_time < 5.0, f"Tiempo de consulta muy alto: {query_time:.2f}s"
        
        print(f"Test consultas complejas completado:")
        print(f"  - Tiempo inserción: {insert_time:.2f}s")
        print(f"  - Tiempo consulta: {query_time:.2f}s")
        print(f"  - Resultados: {len(complex_query)} grupos")
    
    @pytest.mark.asyncio
    async def test_transaction_operations(self, test_database):
        """Test operaciones de transacciones"""
        # Iniciar transacción
        async with test_database.main_conn.transaction() as tx:
            try:
                # Insertar datos en transacción
                await tx.execute(
                    "INSERT INTO test_tasks (task_id, objective, status) VALUES ($1, $2, $3)",
                    "tx_task_1", "Transaction test task 1", "pending"
                )
                
                await tx.execute(
                    "INSERT INTO test_tasks (task_id, objective, status) VALUES ($1, $2, $3)",
                    "tx_task_2", "Transaction test task 2", "pending"
                )
                
                # Actualizar en transacción
                await tx.execute(
                    "UPDATE test_tasks SET status = 'completed' WHERE task_id = $1",
                    "tx_task_1"
                )
                
                # Confirmar transacción
                await tx.commit()
                
            except Exception as e:
                # Rollback en caso de error
                await tx.rollback()
                raise e
        
        # Verificar que la transacción se completó
        completed_task = await test_database.main_conn.fetchrow(
            "SELECT * FROM test_tasks WHERE task_id = $1",
            "tx_task_1"
        )
        
        assert completed_task["status"] == "completed", "Transacción no se completó correctamente"
        
        # Test rollback - insertar y rollback
        async with test_database.main_conn.transaction() as tx:
            await tx.execute(
                "INSERT INTO test_tasks (task_id, objective, status) VALUES ($1, $2, $3)",
                "tx_task_rollback", "Transaction rollback test", "pending"
            )
            
            # Forzar rollback
            await tx.rollback()
        
        # Verificar que el rollback funcionó
        rolled_back_task = await test_database.main_conn.fetchrow(
            "SELECT * FROM test_tasks WHERE task_id = $1",
            "tx_task_rollback"
        )
        
        assert rolled_back_task is None, "Rollback no funcionó correctamente"
        
        print("Test operaciones transacciones completado")
    
    @pytest.mark.asyncio
    async def test_concurrent_database_operations(self, test_database):
        """Test operaciones concurrentes de base de datos"""
        num_concurrent_operations = 10
        operations_per_thread = 5
        
        async def concurrent_task_writer(task_id: int):
            """Writer concurrente"""
            results = []
            for i in range(operations_per_thread):
                try:
                    await test_database.main_conn.execute(
                        "INSERT INTO test_tasks (task_id, objective, status) VALUES ($1, $2, $3)",
                        f"concurrent_task_{task_id}_{i}", f"Concurrent task {task_id}-{i}", "concurrent"
                    )
                    results.append("success")
                except Exception as e:
                    results.append(f"error: {str(e)}")
                
                # Pequeña pausa para permitir interleaving
                await asyncio.sleep(0.01)
            
            return results
        
        # Ejecutar operaciones concurrentes
        start_time = time.time()
        concurrent_tasks = [
            concurrent_task_writer(i) 
            for i in range(num_concurrent_operations)
        ]
        results = await asyncio.gather(*concurrent_tasks)
        total_time = time.time() - start_time
        
        # Verificar resultados
        total_operations = sum(len(result_list) for result_list in results)
        successful_operations = sum(
            len([r for r in result_list if r == "success"]) 
            for result_list in results
        )
        
        success_rate = successful_operations / total_operations if total_operations > 0 else 0
        
        # Verificar integridad de datos
        total_tasks = await test_database.main_conn.fetchval(
            "SELECT COUNT(*) FROM test_tasks WHERE status = 'concurrent'"
        )
        
        assert total_tasks > 0, "No se insertaron tareas concurrentes"
        assert total_tasks <= num_concurrent_operations * operations_per_thread, \
            "Demasiadas tareas insertadas (posible duplicación)"
        
        # Verificar que la concurrencia funcionó sin deadlock
        assert total_time < 10.0, f"Operaciones concurrentes muy lentas: {total_time:.2f}s"
        
        print(f"Test operaciones concurrentes completado:")
        print(f"  - Tareas concurrentes: {num_concurrent_operations}")
        print(f"  - Operaciones por tarea: {operations_per_thread}")
        print(f"  - Tasa de éxito: {success_rate:.2f}")
        print(f"  - Tareas insertadas: {total_tasks}")
        print(f"  - Tiempo total: {total_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_database_backup_and_restore(self, test_database):
        """Test backup y restore de base de datos"""
        # Insertar datos de prueba para backup
        backup_data = []
        for i in range(20):
            data = {
                "task_id": f"backup_task_{i}",
                "objective": f"Backup test objective {i}",
                "status": "backup_test",
                "context": {"backup_batch": "test_001", "created_by": "test_script"},
                "result": {"backup_timestamp": datetime.now().isoformat()}
            }
            backup_data.append(data)
        
        # Insertar datos
        for data in backup_data:
            await test_database.main_conn.execute(
                "INSERT INTO test_tasks (task_id, objective, status, context, result) VALUES ($1, $2, $3, $4, $5)",
                data["task_id"], data["objective"], data["status"],
                json.dumps(data["context"]), json.dumps(data["result"])
            )
        
        # Simular backup (en un entorno real sería pg_dump o similar)
        backup_start = time.time()
        
        # Exportar datos
        exported_data = await test_database.main_conn.fetch(
            "SELECT * FROM test_tasks WHERE status = 'backup_test' ORDER BY task_id"
        )
        
        backup_time = time.time() - backup_start
        
        # Verificar backup
        assert len(exported_data) == len(backup_data), "Backup incompleto"
        
        # Simular restauración
        restore_start = time.time()
        
        # Limpiar datos originales
        await test_database.main_conn.execute("DELETE FROM test_tasks WHERE status = 'backup_test'")
        
        # Restaurar desde backup
        for row in exported_data:
            await test_database.main_conn.execute(
                "INSERT INTO test_tasks (task_id, objective, status, context, result) VALUES ($1, $2, $3, $4, $5)",
                row["task_id"], row["objective"], row["status"], row["context"], row["result"]
            )
        
        restore_time = time.time() - restore_start
        
        # Verificar restauración
        restored_count = await test_database.main_conn.fetchval(
            "SELECT COUNT(*) FROM test_tasks WHERE status = 'backup_test'"
        )
        
        assert restored_count == len(backup_data), "Restauración incompleta"
        
        print(f"Test backup/restore completado:")
        print(f"  - Datos de backup: {len(backup_data)}")
        print(f"  - Tiempo backup: {backup_time:.3f}s")
        print(f"  - Tiempo restore: {restore_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_database_monitoring_queries(self, test_database):
        """Test queries de monitoreo de base de datos"""
        # Insertar algunos datos para monitoreo
        monitoring_data = [
            {"task_id": f"monitor_task_{i}", "status": ["active", "completed", "failed"][i % 3]}
            for i in range(15)
        ]
        
        for data in monitoring_data:
            await test_database.main_conn.execute(
                "INSERT INTO test_tasks (task_id, objective, status) VALUES ($1, $2, $3)",
                data["task_id"], "Monitoring test task", data["status"]
            )
        
        # Queries de monitoreo
        monitoring_queries = {
            "total_tasks": "SELECT COUNT(*) as total FROM test_tasks",
            "tasks_by_status": """
                SELECT status, COUNT(*) as count 
                FROM test_tasks 
                GROUP BY status 
                ORDER BY count DESC
            """,
            "recent_tasks": """
                SELECT task_id, status, created_at 
                FROM test_tasks 
                ORDER BY created_at DESC 
                LIMIT 5
            """,
            "task_statistics": """
                SELECT 
                    COUNT(*) as total,
                    AVG(CASE WHEN completed_at IS NOT NULL THEN EXTRACT(EPOCH FROM (completed_at - created_at)) END) as avg_duration_seconds,
                    MIN(created_at) as earliest_task,
                    MAX(created_at) as latest_task
                FROM test_tasks
            """
        }
        
        monitoring_results = {}
        
        for query_name, query in monitoring_queries.items():
            start_time = time.time()
            result = await test_database.main_conn.fetch(query)
            query_time = time.time() - start_time
            
            monitoring_results[query_name] = {
                "result": result,
                "execution_time_ms": query_time * 1000,
                "row_count": len(result)
            }
        
        # Verificar resultados de monitoreo
        assert monitoring_results["total_tasks"]["row_count"] == 1
        assert monitoring_results["total_tasks"]["result"][0]["total"] == 15
        
        assert monitoring_results["tasks_by_status"]["row_count"] == 3  # 3 statuses únicos
        
        assert monitoring_results["recent_tasks"]["row_count"] <= 5
        
        assert monitoring_results["task_statistics"]["row_count"] == 1
        assert monitoring_results["task_statistics"]["result"][0]["total"] == 15
        
        # Verificar que las queries de monitoreo son rápidas
        for query_name, result in monitoring_results.items():
            assert result["execution_time_ms"] < 100, \
                f"Query de monitoreo {query_name} muy lenta: {result['execution_time_ms']:.2f}ms"
        
        print(f"Test monitoreo DB completado:")
        for query_name, result in monitoring_results.items():
            print(f"  - {query_name}: {result['execution_time_ms']:.2f}ms")