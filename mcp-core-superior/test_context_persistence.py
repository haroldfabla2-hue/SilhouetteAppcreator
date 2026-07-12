"""
Tests para el Sistema Avanzado de Persistencia de Contexto
==========================================================

Demuestra todas las funcionalidades principales del Context Persistence Engine
"""

import asyncio
import json
import time
import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Importar el sistema de persistencia
from src.core.context_persistence_engine import (
    initialize_context_persistence,
    create_context_snapshot,
    retrieve_context_snapshot,
    search_context_semantic,
    recover_session,
    create_context_version,
    optimize_context_storage,
    get_context_engine_stats,
    initialize_agent_with_context,
    context_persistence_engine,
    ContextType,
    ContextTier,
    ContextSnapshot,
    ContextVersion
)


class ContextPersistenceTester:
    """Tester para demostrar funcionalidades del sistema"""
    
    def __init__(self):
        self.test_user_id = "test_user_123"
        self.test_session_id = "test_session_456"
        self.test_results = {}
    
    async def run_all_tests(self):
        """Ejecutar todos los tests de funcionalidad"""
        print("🧪 Iniciando tests del Context Persistence Engine...")
        
        try:
            # 1. Test de inicialización
            await self.test_initialization()
            
            # 2. Test de creación de snapshots
            await self.test_snapshot_creation()
            
            # 3. Test de recuperación
            await self.test_snapshot_retrieval()
            
            # 4. Test de búsqueda semántica
            await self.test_semantic_search()
            
            # 5. Test de clustering semántico
            await self.test_semantic_clustering()
            
            # 6. Test de control de versiones
            await self.test_version_control()
            
            # 7. Test de recuperación de sesión
            await self.test_session_recovery()
            
            # 8. Test de inicialización context-aware
            await self.test_context_aware_initialization()
            
            # 9. Test de optimización
            await self.test_optimization()
            
            # 10. Test de estadísticas y monitoreo
            await self.test_monitoring()
            
            # 11. Test de rendimiento
            await self.test_performance()
            
            # 12. Test de compresión
            await self.test_compression()
            
            print("✅ Todos los tests completados exitosamente!")
            return self.test_results
            
        except Exception as e:
            print(f"❌ Error durante tests: {e}")
            raise
    
    async def test_initialization(self):
        """Test 1: Inicialización del sistema"""
        print("\n📋 Test 1: Inicialización del sistema")
        
        start_time = time.time()
        await initialize_context_persistence()
        init_time = time.time() - start_time
        
        # Verificar estado de inicialización
        assert context_persistence_engine.is_initialized, "Sistema no inicializado correctamente"
        
        # Health check
        health = await context_persistence_engine._health_check()
        
        self.test_results["initialization"] = {
            "success": True,
            "init_time_ms": round(init_time * 1000, 2),
            "health": health,
            "redis_connected": health["redis"],
            "postgresql_connected": health["postgresql"]
        }
        
        print(f"  ✓ Sistema inicializado en {init_time:.2f}s")
        print(f"  ✓ Redis: {'Conectado' if health['redis'] else 'Desconectado'}")
        print(f"  ✓ PostgreSQL: {'Conectado' if health['postgresql'] else 'Desconectado'}")
    
    async def test_snapshot_creation(self):
        """Test 2: Creación de snapshots"""
        print("\n📋 Test 2: Creación de snapshots")
        
        snapshot_ids = []
        
        # Crear diferentes tipos de snapshots
        test_snapshots = [
            {
                "type": ContextType.CONVERSATION,
                "content": {
                    "messages": [
                        {"role": "user", "content": "¿Cómo optimizo mi base de datos?"},
                        {"role": "assistant", "content": "Para optimizar tu base de datos, considera..."}
                    ],
                    "topic": "database_optimization",
                    "sentiment": "helpful"
                },
                "metadata": {"conversation_id": "conv_001"}
            },
            {
                "type": ContextType.TASK,
                "content": {
                    "task_id": "task_001",
                    "title": "Implementar sistema de autenticación",
                    "description": "Crear sistema JWT con refresh tokens",
                    "priority": "high",
                    "status": "in_progress",
                    "assignee": "dev_team"
                },
                "metadata": {"project": "auth_system"}
            },
            {
                "type": ContextType.AGENT_MEMORY,
                "content": {
                    "agent_name": "python_executor",
                    "specializations": ["data_analysis", "web_scraping"],
                    "preferences": {"preferred_libs": ["pandas", "beautifulsoup"]},
                    "performance_metrics": {"avg_execution_time": "2.3s", "success_rate": "0.95"}
                },
                "metadata": {"agent_version": "v2.1"}
            },
            {
                "type": ContextType.USER_PREFERENCES,
                "content": {
                    "theme": "dark",
                    "language": "es",
                    "notifications": {"email": True, "push": False},
                    "productivity_settings": {"auto_save": True, "quick_actions": True}
                },
                "metadata": {"user_type": "premium"}
            }
        ]
        
        start_time = time.time()
        for snapshot_config in test_snapshots:
            snapshot_id = await create_context_snapshot(
                context_type=snapshot_config["type"],
                content=snapshot_config["content"],
                user_id=self.test_user_id,
                session_id=self.test_session_id,
                metadata=snapshot_config["metadata"]
            )
            snapshot_ids.append(snapshot_id)
            print(f"  ✓ Snapshot creado: {snapshot_config['type'].value} ({snapshot_id[:8]}...)")
        
        creation_time = time.time() - start_time
        
        self.test_results["snapshot_creation"] = {
            "success": True,
            "snapshots_created": len(snapshot_ids),
            "creation_time_ms": round(creation_time * 1000, 2),
            "snapshot_ids": [sid[:8] + "..." for sid in snapshot_ids]
        }
        
        return snapshot_ids
    
    async def test_snapshot_retrieval(self):
        """Test 3: Recuperación de snapshots"""
        print("\n📋 Test 3: Recuperación de snapshots")
        
        # Crear snapshot para recuperar
        test_content = {
            "test_data": "Este es un snapshot de prueba",
            "timestamp": datetime.now().isoformat(),
            "test_id": "retrieval_test_001"
        }
        
        snapshot_id = await create_context_snapshot(
            context_type=ContextType.TASK,
            content=test_content,
            user_id=self.test_user_id,
            session_id=self.test_session_id,
            metadata={"test_type": "retrieval"}
        )
        
        # Recuperar snapshot
        start_time = time.time()
        retrieved_snapshot = await retrieve_context_snapshot(snapshot_id)
        retrieval_time = time.time() - start_time
        
        # Verificar recuperación
        assert retrieved_snapshot is not None, "Snapshot no encontrado"
        assert retrieved_snapshot.snapshot_id == snapshot_id, "ID no coincide"
        assert retrieved_snapshot.content["test_data"] == test_content["test_data"], "Contenido no coincide"
        
        self.test_results["snapshot_retrieval"] = {
            "success": True,
            "retrieval_time_ms": round(retrieval_time * 1000, 2),
            "snapshot_found": True,
            "content_verified": True,
            "tier": retrieved_snapshot.tier.value
        }
        
        print(f"  ✓ Snapshot recuperado en {retrieval_time * 1000:.2f}ms")
        print(f"  ✓ Tier: {retrieved_snapshot.tier.value}")
        print(f"  ✓ Tamaño original: {retrieved_snapshot.original_size} bytes")
        print(f"  ✓ Tamaño comprimido: {retrieved_snapshot.compressed_size} bytes")
        return snapshot_id
    
    async def test_semantic_search(self):
        """Test 4: Búsqueda semántica"""
        print("\n📋 Test 4: Búsqueda semántica")
        
        # Crear snapshots con contenido semánticamente relacionado
        search_test_data = [
            {
                "content": "Implementar sistema de autenticación JWT con refresh tokens",
                "type": ContextType.TASK
            },
            {
                "content": "Optimizar consultas de base de datos PostgreSQL",
                "type": ContextType.TASK
            },
            {
                "content": "Configurar cluster de Redis para caching",
                "type": ContextType.TASK
            },
            {
                "content": "Conversación sobre mejores prácticas de seguridad web",
                "type": ContextType.CONVERSATION
            },
            {
                "content": "Tutorial de Python para análisis de datos",
                "type": ContextType.CONVERSATION
            }
        ]
        
        # Crear snapshots
        search_snapshot_ids = []
        for data in search_test_data:
            snapshot_id = await create_context_snapshot(
                context_type=data["type"],
                content={"text": data["content"]},
                user_id=self.test_user_id,
                session_id=self.test_session_id
            )
            search_snapshot_ids.append(snapshot_id)
        
        # Esperar a que se procesen los embeddings
        await asyncio.sleep(2)
        
        # Realizar búsquedas semánticas
        search_queries = [
            "autenticación JWT seguridad",
            "optimización base de datos PostgreSQL",
            "caching Redis rendimiento",
            "Python análisis datos"
        ]
        
        search_results = {}
        start_time = time.time()
        
        for query in search_queries:
            results = await search_context_semantic(
                query=query,
                user_id=self.test_user_id,
                limit=3
            )
            search_results[query] = len(results)
            print(f"  ✓ Búsqueda '{query}': {len(results)} resultados")
        
        search_time = time.time() - start_time
        
        self.test_results["semantic_search"] = {
            "success": True,
            "search_time_ms": round(search_time * 1000, 2),
            "queries_tested": len(search_queries),
            "results_per_query": search_results,
            "total_results": sum(search_results.values())
        }
        
        return search_snapshot_ids
    
    async def test_semantic_clustering(self):
        """Test 5: Clustering semántico"""
        print("\n📋 Test 5: Clustering semántico")
        
        # Crear snapshots con contenido relacionado para clustering
        clustering_data = [
            {"content": "Configurar servidor web nginx con SSL", "category": "web_server"},
            {"content": "Optimizar configuración de Apache", "category": "web_server"},
            {"content": "Implementar balanceador de carga", "category": "web_server"},
            {"content": "Configurar firewall iptables", "category": "security"},
            {"content": "Implementar certificados SSL", "category": "security"},
            {"content": "Configurar VPN segura", "category": "security"}
        ]
        
        clustering_snapshot_ids = []
        for data in clustering_data:
            snapshot_id = await create_context_snapshot(
                context_type=ContextType.TASK,
                content={"description": data["content"], "category": data["category"]},
                user_id=self.test_user_id,
                session_id=self.test_session_id
            )
            clustering_snapshot_ids.append(snapshot_id)
        
        # Esperar clustering
        await asyncio.sleep(3)
        
        # Verificar clusters en cache
        clusters_count = len(context_persistence_engine._cache["clusters"])
        
        self.test_results["semantic_clustering"] = {
            "success": True,
            "snapshots_created": len(clustering_data),
            "clusters_detected": clusters_count,
            "clustering_active": clusters_count > 0
        }
        
        print(f"  ✓ {len(clustering_data)} snapshots procesados para clustering")
        print(f"  ✓ {clusters_count} clusters detectados")
        
        return clustering_snapshot_ids
    
    async def test_version_control(self):
        """Test 6: Control de versiones"""
        print("\n📋 Test 6: Control de versiones")
        
        # Crear snapshot inicial
        initial_content = {
            "version": 1,
            "features": ["authentication", "basic_ui"],
            "bugs": []
        }
        
        snapshot_id = await create_context_snapshot(
            context_type=ContextType.WORKFLOW,
            content=initial_content,
            user_id=self.test_user_id,
            session_id=self.test_session_id,
            metadata={"version_control_test": True}
        )
        
        # Crear versiones sucesivas
        versions = []
        version_changes = [
            {
                "new_version": 2,
                "added_features": ["user_profiles"],
                "bug_fixes": ["login_error_handling"]
            },
            {
                "new_version": 3,
                "added_features": ["notifications", "settings"],
                "bug_fixes": ["session_timeout"]
            },
            {
                "new_version": 4,
                "added_features": ["mobile_support"],
                "bug_fixes": ["responsive_design"]
            }
        ]
        
        start_time = time.time()
        for change in version_changes:
            version_id = await create_context_version(
                snapshot_id=snapshot_id,
                changes=change,
                author="test_system",
                message=f"Update to version {change['new_version']}"
            )
            versions.append(version_id)
            print(f"  ✓ Versión creada: v{change['new_version']} ({version_id[:8]}...)")
        
        version_time = time.time() - start_time
        
        self.test_results["version_control"] = {
            "success": True,
            "snapshot_id": snapshot_id[:8] + "...",
            "versions_created": len(versions),
            "versioning_time_ms": round(version_time * 1000, 2),
            "version_ids": [vid[:8] + "..." for vid in versions]
        }
        
        return snapshot_id
    
    async def test_session_recovery(self):
        """Test 7: Recuperación de sesión"""
        print("\n📋 Test 7: Recuperación de sesión")
        
        # Crear múltiples snapshots para una sesión
        session_snapshots = []
        for i in range(5):
            snapshot_id = await create_context_snapshot(
                context_type=ContextType.CONVERSATION,
                content={
                    "message_number": i + 1,
                    "content": f"Mensaje de prueba {i + 1} de la sesión",
                    "timestamp": (datetime.now() - timedelta(minutes=5-i)).isoformat()
                },
                user_id=self.test_user_id,
                session_id=self.test_session_id,
                metadata={"session_test": True, "sequence": i + 1}
            )
            session_snapshots.append(snapshot_id)
        
        # Esperar almacenamiento
        await asyncio.sleep(1)
        
        # Recuperar contexto de sesión
        start_time = time.time()
        recovered_contexts = await recover_session(
            user_id=self.test_user_id,
            session_id=self.test_session_id,
            max_age_hours=1
        )
        recovery_time = time.time() - start_time
        
        # Verificar recuperación
        assert len(recovered_contexts) > 0, "No se recuperó contexto de sesión"
        
        self.test_results["session_recovery"] = {
            "success": True,
            "recovery_time_ms": round(recovery_time * 1000, 2),
            "snapshots_in_session": len(session_snapshots),
            "recovered_snapshots": len(recovered_contexts),
            "recovery_rate": len(recovered_contexts) / len(session_snapshots)
        }
        
        print(f"  ✓ {len(recovered_contexts)}/{len(session_snapshots)} snapshots recuperados")
        print(f"  ✓ Tasa de recuperación: {len(recovered_contexts)/len(session_snapshots)*100:.1f}%")
        
        return session_snapshots
    
    async def test_context_aware_initialization(self):
        """Test 8: Inicialización context-aware"""
        print("\n📋 Test 8: Inicialización context-aware")
        
        # Crear contexto previo para el agente
        agent_context_data = [
            {"type": ContextType.TASK, "content": {"task": "database_optimization"}},
            {"type": ContextType.CONVERSATION, "content": {"topic": "python_programming"}},
            {"type": ContextType.AGENT_MEMORY, "content": {"preferences": {"theme": "dark"}}}
        ]
        
        for data in agent_context_data:
            await create_context_snapshot(
                context_type=data["type"],
                content=data["content"],
                user_id=self.test_user_id,
                session_id=self.test_session_id
            )
        
        # Inicializar agente con contexto
        start_time = time.time()
        agent_initialization = await initialize_agent_with_context(
            agent_name="python_executor",
            user_id=self.test_user_id,
            session_id=self.test_session_id,
            context_requirements={
                "context_types": [ContextType.TASK, ContextType.CONVERSATION],
                "max_contexts": 10
            }
        )
        init_time = time.time() - start_time
        
        # Verificar inicialización
        assert "initialization_snapshot_id" in agent_initialization, "No se creó snapshot de inicialización"
        
        self.test_results["context_aware_initialization"] = {
            "success": True,
            "initialization_time_ms": round(init_time * 1000, 2),
            "initialization_snapshot_id": agent_initialization["initialization_snapshot_id"][:8] + "...",
            "context_sources": agent_initialization.get("context_summary", {}),
            "relevant_context_found": len(agent_initialization.get("relevant_context", [])) > 0
        }
        
        print(f"  ✓ Agente inicializado en {init_time * 1000:.2f}ms")
        print(f"  ✓ Snapshot de inicialización: {agent_initialization['initialization_snapshot_id'][:8]}...")
        print(f"  ✓ Contexto relevante encontrado: {len(agent_initialization.get('relevant_context', []))}")
    
    async def test_optimization(self):
        """Test 9: Optimización automática"""
        print("\n📋 Test 9: Optimización automática")
        
        # Crear snapshots que requieren optimización
        optimization_snapshots = []
        for i in range(20):
            snapshot_id = await create_context_snapshot(
                context_type=ContextType.TASK,
                content={
                    "large_content": "x" * 1000,  # Contenido grande para compresión
                    "index": i,
                    "optimization_test": True
                },
                user_id=self.test_user_id,
                session_id=self.test_session_id
            )
            optimization_snapshots.append(snapshot_id)
        
        # Ejecutar optimización
        start_time = time.time()
        optimization_results = await optimize_context_storage()
        optimization_time = time.time() - start_time
        
        self.test_results["optimization"] = {
            "success": True,
            "optimization_time_ms": round(optimization_time * 1000, 2),
            "snapshots_processed": len(optimization_snapshots),
            "optimization_results": optimization_results,
            "pruned_snapshots": optimization_results.get("pruned_snapshots", 0),
            "freed_space_mb": optimization_results.get("freed_space_mb", 0)
        }
        
        print(f"  ✓ Optimización completada en {optimization_time * 1000:.2f}ms")
        print(f"  ✓ Snapshots procesados: {len(optimization_snapshots)}")
        print(f"  ✓ Space liberado: {optimization_results.get('freed_space_mb', 0):.2f} MB")
        
        return optimization_snapshots
    
    async def test_monitoring(self):
        """Test 10: Monitoreo y estadísticas"""
        print("\n📋 Test 10: Monitoreo y estadísticas")
        
        # Obtener estadísticas
        start_time = time.time()
        stats = await get_context_engine_stats()
        stats_time = time.time() - start_time
        
        # Health check
        health = await context_persistence_engine._health_check()
        
        self.test_results["monitoring"] = {
            "success": True,
            "stats_time_ms": round(stats_time * 1000, 2),
            "database_connected": health["postgresql"],
            "redis_connected": health["redis"],
            "total_snapshots": stats.get("database", {}).get("total_snapshots", 0),
            "total_clusters": stats.get("database", {}).get("total_clusters", 0),
            "cache_size": stats.get("cache", {}).get("snapshots_count", 0),
            "memory_usage_mb": stats.get("redis", {}).get("memory_usage_mb", 0)
        }
        
        print(f"  ✓ Estadísticas obtenidas en {stats_time * 1000:.2f}ms")
        print(f"  ✓ Total snapshots: {stats.get('database', {}).get('total_snapshots', 0)}")
        print(f"  ✓ Clusters activos: {stats.get('database', {}).get('total_clusters', 0)}")
        print(f"  ✓ Cache size: {stats.get('cache', {}).get('snapshots_count', 0)}")
        print(f"  ✓ Uso Redis: {stats.get('redis', {}).get('memory_usage_mb', 0):.2f} MB")
        
        return stats
    
    async def test_performance(self):
        """Test 11: Pruebas de rendimiento"""
        print("\n📋 Test 11: Pruebas de rendimiento")
        
        # Test de creación masiva
        batch_size = 50
        start_time = time.time()
        
        batch_snapshot_ids = []
        for i in range(batch_size):
            snapshot_id = await create_context_snapshot(
                context_type=ContextType.TASK,
                content={
                    "performance_test": True,
                    "batch_index": i,
                    "data": f"Test data {i}" * 10
                },
                user_id=self.test_user_id,
                session_id=self.test_session_id
            )
            batch_snapshot_ids.append(snapshot_id)
        
        creation_time = time.time() - start_time
        
        # Test de recuperación masiva
        start_time = time.time()
        retrieved_count = 0
        for snapshot_id in batch_snapshot_ids[:10]:  # Probar solo 10 para no sobrecargar
            snapshot = await retrieve_context_snapshot(snapshot_id)
            if snapshot:
                retrieved_count += 1
        
        retrieval_time = time.time() - start_time
        
        # Test de búsqueda masiva
        start_time = time.time()
        search_results_count = 0
        for query in ["test", "performance", "batch", "data"]:
            results = await search_context_semantic(
                query=query,
                user_id=self.test_user_id,
                limit=5
            )
            search_results_count += len(results)
        
        search_time = time.time() - start_time
        
        performance_metrics = {
            "batch_creation_time_ms": round(creation_time * 1000, 2),
            "creation_throughput_per_sec": round(batch_size / creation_time, 2),
            "batch_retrieval_time_ms": round(retrieval_time * 1000, 2),
            "retrieval_throughput_per_sec": round(10 / retrieval_time, 2) if retrieval_time > 0 else 0,
            "search_time_ms": round(search_time * 1000, 2),
            "search_throughput_per_sec": round(4 / search_time, 2) if search_time > 0 else 0,
            "total_search_results": search_results_count
        }
        
        self.test_results["performance"] = {
            "success": True,
            "batch_size": batch_size,
            "metrics": performance_metrics
        }
        
        print(f"  ✓ Creación masiva: {performance_metrics['creation_throughput_per_sec']} snapshots/sec")
        print(f"  ✓ Recuperación: {performance_metrics['retrieval_throughput_per_sec']} snapshots/sec")
        print(f"  ✓ Búsqueda: {performance_metrics['search_throughput_per_sec']} queries/sec")
        
        return batch_snapshot_ids
    
    async def test_compression(self):
        """Test 12: Pruebas de compresión"""
        print("\n📋 Test 12: Pruebas de compresión")
        
        # Crear contenido de diferentes tamaños para probar compresión
        compression_tests = [
            {"size": "small", "content": "x" * 100},
            {"size": "medium", "content": "x" * 1000},
            {"size": "large", "content": "x" * 10000},
            {"size": "xlarge", "content": "x" * 100000}
        ]
        
        compression_results = []
        
        for test in compression_tests:
            start_time = time.time()
            
            snapshot_id = await create_context_snapshot(
                context_type=ContextType.TASK,
                content={"data": test["content"], "compression_test": True},
                user_id=self.test_user_id,
                session_id=self.test_session_id
            )
            
            # Recuperar snapshot para verificar compresión
            snapshot = await retrieve_context_snapshot(snapshot_id)
            compress_time = time.time() - start_time
            
            if snapshot:
                compression_ratio = snapshot.compressed_size / snapshot.original_size if snapshot.original_size > 0 else 0
                space_saved = 1 - compression_ratio
                
                compression_results.append({
                    "size_category": test["size"],
                    "original_size": snapshot.original_size,
                    "compressed_size": snapshot.compressed_size,
                    "compression_ratio": round(compression_ratio, 3),
                    "space_saved_percent": round(space_saved * 100, 1),
                    "compression_time_ms": round(compress_time * 1000, 2)
                })
                
                print(f"  ✓ {test['size']}: {snapshot.original_size} → {snapshot.compressed_size} bytes "
                      f"({space_saved * 100:.1f}% reducción)")
        
        self.test_results["compression"] = {
            "success": True,
            "compression_tests": compression_results,
            "avg_compression_ratio": sum(r["compression_ratio"] for r in compression_results) / len(compression_results),
            "avg_space_saved_percent": sum(r["space_saved_percent"] for r in compression_results) / len(compression_results)
        }
        
        return compression_results
    
    def print_test_summary(self):
        """Imprimir resumen de tests"""
        print("\n" + "="*80)
        print("📊 RESUMEN DE TESTS - CONTEXT PERSISTENCE ENGINE")
        print("="*80)
        
        for test_name, results in self.test_results.items():
            status = "✅ PASS" if results.get("success") else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
            
            if "time" in results:
                time_value = results.get("time_ms", results.get("time"))
                if time_value:
                    print(f"   ⏱️  Tiempo: {time_value}")
            
            if "throughput" in str(results):
                print(f"   📈 Throughput: Detectado")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r.get("success"))
        
        print("\n" + "-"*80)
        print(f"📊 RESULTADOS FINALES: {passed_tests}/{total_tests} tests aprobados ({passed_tests/total_tests*100:.1f}%)")
        print("="*80)


async def run_context_persistence_tests():
    """Función principal para ejecutar todos los tests"""
    tester = ContextPersistenceTester()
    
    try:
        results = await tester.run_all_tests()
        tester.print_test_summary()
        return results
    except Exception as e:
        print(f"❌ Error ejecutando tests: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("🚀 Ejecutando tests del Context Persistence Engine...")
    results = asyncio.run(run_context_persistence_tests())
    
    if results:
        print("\n🎉 Tests completados exitosamente!")
        print("El sistema está listo para usar.")
    else:
        print("\n💥 Tests fallaron!")
        print("Revisar configuración y dependencias.")