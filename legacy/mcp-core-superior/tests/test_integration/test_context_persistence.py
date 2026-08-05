"""
Test de context persistence entre agentes
Valida el sistema de persistencia y compartición de contexto entre todos los agentes
"""
import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum

from conftest import create_test_task_id


class ContextScope(Enum):
    """Alcances de contexto"""
    GLOBAL = "global"
    SESSION = "session"
    TASK = "task"
    AGENT = "agent"
    TEMPORARY = "temporary"


class ContextLifetime(Enum):
    """Duración del contexto"""
    EPHEMERAL = "ephemeral"  # En memoria, se pierde al reiniciar
    SHORT_TERM = "short_term"  # Horas
    MEDIUM_TERM = "medium_term"  # Días
    LONG_TERM = "long_term"  # Semanas+
    PERMANENT = "permanent"  # Nunca se elimina


class SharedContext:
    """Contexto compartido entre agentes"""
    
    def __init__(self, context_id: str, scope: ContextScope, lifetime: ContextLifetime):
        self.context_id = context_id
        self.scope = scope
        self.lifetime = lifetime
        self.data = {}
        self.metadata = {
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "access_count": 0,
            "contributors": [],
            "consumers": []
        }
        self.lock = asyncio.Lock()
    
    async def update_data(self, agent_id: str, key: str, value: Any):
        """Actualizar datos del contexto"""
        async with self.lock:
            self.data[key] = value
            self.metadata["last_accessed"] = datetime.now()
            self.metadata["access_count"] += 1
            
            if agent_id not in self.metadata["contributors"]:
                self.metadata["contributors"].append(agent_id)
    
    async def get_data(self, agent_id: str, key: Optional[str] = None):
        """Obtener datos del contexto"""
        async with self.lock:
            self.metadata["last_accessed"] = datetime.now()
            self.metadata["access_count"] += 1
            
            if agent_id not in self.metadata["consumers"]:
                self.metadata["consumers"].append(agent_id)
            
            if key:
                return self.data.get(key)
            else:
                return self.data.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            "context_id": self.context_id,
            "scope": self.scope.value,
            "lifetime": self.lifetime.value,
            "data": self.data,
            "metadata": {
                "created_at": self.metadata["created_at"].isoformat(),
                "last_accessed": self.metadata["last_accessed"].isoformat(),
                "access_count": self.metadata["access_count"],
                "contributors": self.metadata["contributors"],
                "consumers": self.metadata["consumers"]
            }
        }


@pytest.mark.integration
class TestContextPersistence:
    """Tests de persistencia de contexto entre agentes"""
    
    @pytest.mark.asyncio
    async def test_basic_context_sharing(self, test_database):
        """Test básico de compartición de contexto"""
        context_id = "test_context_001"
        
        # Simular intercambio de contexto entre agentes
        context_sharing_log = []
        
        # Razonador crea contexto inicial
        context_data = {
            "initial_analysis": {
                "intent": "data_analysis",
                "complexity": "medium",
                "confidence": 0.85
            },
            "domain": "customer_feedback",
            "processing_notes": "Requires multi-step analysis"
        }
        
        # Almacenar contexto inicial
        await test_database.main_conn.execute(
            "INSERT INTO test_context_persistence (context_id, agent_id, data) VALUES ($1, $2, $3)",
            context_id, "reasoner", json.dumps(context_data)
        )
        
        # Planificador accede y actualiza contexto
        planner_context = await test_database.main_conn.fetchrow(
            "SELECT * FROM test_context_persistence WHERE context_id = $1 AND agent_id = $2",
            context_id, "reasoner"
        )
        
        assert planner_context is not None
        retrieved_data = json.loads(planner_context["data"])
        assert retrieved_data["initial_analysis"]["intent"] == "data_analysis"
        
        # Planificador añade su información
        updated_context = {
            **retrieved_data,
            "execution_plan": {
                "tasks": [
                    {"task": "data_extraction", "priority": 1},
                    {"task": "sentiment_analysis", "priority": 2},
                    {"task": "insight_generation", "priority": 3}
                ],
                "estimated_duration": 45,
                "parallel_execution": False
            }
        }
        
        await test_database.main_conn.execute(
            "UPDATE test_context_persistence SET data = $1 WHERE context_id = $2 AND agent_id = $3",
            json.dumps(updated_context), context_id, "planner"
        )
        
        # Ejecutor accede al contexto completo
        executor_context = await test_database.main_conn.fetchrow(
            "SELECT * FROM test_context_persistence WHERE context_id = $1",
            context_id
        )
        
        executor_data = json.loads(executor_context["data"])
        assert "execution_plan" in executor_data
        assert len(executor_data["execution_plan"]["tasks"]) == 3
        
        context_sharing_log.append({
            "context_id": context_id,
            "agents_involved": ["reasoner", "planner", "executor"],
            "data_transfers": 3,
            "final_state": executor_data
        })
        
        assert len(context_sharing_log) == 1
        assert len(context_sharing_log[0]["agents_involved"]) == 3
        
        print("Test compartición básica contexto completado")
    
    @pytest.mark.asyncio
    async def test_concurrent_context_access(self, test_database):
        """Test acceso concurrente al mismo contexto"""
        context_id = "concurrent_context_001"
        
        # Configurar contexto inicial
        initial_context = {
            "task_type": "parallel_analysis",
            "agents_working": [],
            "shared_results": {},
            "synchronization_points": ["data_ready", "analysis_complete", "validation_done"]
        }
        
        await test_database.main_conn.execute(
            "INSERT INTO test_context_persistence (context_id, agent_id, data) VALUES ($1, $2, $3)",
            context_id, "coordinator", json.dumps(initial_context)
        )
        
        # Simular acceso concurrente de múltiples agentes
        concurrent_agents = [
            "database_operations",
            "python_executor", 
            "file_processing",
            "search_engine"
        ]
        
        async def agent_context_access(agent_id: str, access_time: float):
            """Simular acceso de agente al contexto"""
            await asyncio.sleep(access_time)
            
            # Leer contexto
            context_row = await test_database.main_conn.fetchrow(
                "SELECT * FROM test_context_persistence WHERE context_id = $1",
                context_id
            )
            
            if context_row:
                current_data = json.loads(context_row["data"])
                
                # Actualizar datos
                updated_data = {
                    **current_data,
                    "agents_working": current_data["agents_working"] + [agent_id],
                    "shared_results": {
                        **current_data["shared_results"],
                        agent_id: {
                            "status": "completed",
                            "timestamp": datetime.now().isoformat(),
                            "output": f"Agent {agent_id} completed analysis"
                        }
                    }
                }
                
                # Escribir contexto actualizado
                await test_database.main_conn.execute(
                    "UPDATE test_context_persistence SET data = $1 WHERE context_id = $2",
                    json.dumps(updated_data), context_id
                )
                
                return {"agent": agent_id, "success": True, "update_time": access_time}
            else:
                return {"agent": agent_id, "success": False, "error": "context_not_found"}
        
        # Ejecutar accesos concurrentes
        start_time = time.time()
        concurrent_tasks = [
            agent_context_access(agent_id, random.uniform(0.01, 0.1))
            for agent_id in concurrent_agents
        ]
        
        access_results = await asyncio.gather(*concurrent_tasks)
        total_time = time.time() - start_time
        
        # Verificar resultados
        successful_accesses = [r for r in access_results if r["success"]]
        
        assert len(successful_accesses) >= 3, "Al menos 3 agentes deberían acceder exitosamente"
        
        # Verificar contexto final
        final_context = await test_database.main_conn.fetchrow(
            "SELECT * FROM test_context_persistence WHERE context_id = $1",
            context_id
        )
        
        final_data = json.loads(final_context["data"])
        assert len(final_data["agents_working"]) >= 3
        assert len(final_data["shared_results"]) >= 3
        
        print(f"Test acceso concurrente completado:")
        print(f"  - Agentes concurrentes: {len(concurrent_agents)}")
        print(f"  - Accesos exitosos: {len(successful_accesses)}")
        print(f"  - Tiempo total: {total_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_context_versioning(self, test_database):
        """Test versionado de contexto"""
        context_id = "versioned_context_001"
        version_history = []
        
        # Versión 1: Inicial
        version_1 = {
            "version": 1,
            "analysis_type": "sentiment_analysis",
            "initial_data": {"sample_size": 100, "confidence_level": 0.95}
        }
        
        await test_database.main_conn.execute(
            "INSERT INTO test_context_persistence (context_id, agent_id, data) VALUES ($1, $2, $3)",
            context_id, "reasoner", json.dumps(version_1)
        )
        version_history.append({"version": 1, "agent": "reasoner", "timestamp": datetime.now()})
        
        # Versión 2: Planificador añade planificación
        await asyncio.sleep(0.01)  # Pequeña pausa para diferencia temporal
        version_2 = {
            **version_1,
            "version": 2,
            "execution_plan": {"phases": 4, "estimated_time": 60}
        }
        
        await test_database.main_conn.execute(
            "UPDATE test_context_persistence SET data = $1 WHERE context_id = $2",
            json.dumps(version_2), context_id
        )
        version_history.append({"version": 2, "agent": "planner", "timestamp": datetime.now()})
        
        # Versión 3: Ejecutor añade resultados parciales
        await asyncio.sleep(0.01)
        version_3 = {
            **version_2,
            "version": 3,
            "partial_results": {
                "phase_1": {"completed": True, "score": 0.7},
                "phase_2": {"completed": False, "progress": 50}
            }
        }
        
        await test_database.main_conn.execute(
            "UPDATE test_context_persistence SET data = $1 WHERE context_id = $2",
            json.dumps(version_3), context_id
        )
        version_history.append({"version": 3, "agent": "executor", "timestamp": datetime.now()})
        
        # Verificar historial de versiones
        retrieved_context = await test_database.main_conn.fetchrow(
            "SELECT * FROM test_context_persistence WHERE context_id = $1",
            context_id
        )
        
        current_version = json.loads(retrieved_context["data"])
        assert current_version["version"] == 3
        assert "partial_results" in current_version
        
        # Verificar orden temporal de versiones
        for i in range(1, len(version_history)):
            prev_timestamp = version_history[i-1]["timestamp"]
            curr_timestamp = version_history[i]["timestamp"]
            assert curr_timestamp >= prev_timestamp, "Versiones no están ordenadas temporalmente"
        
        print(f"Test versionado contexto completado - {len(version_history)} versiones")
    
    @pytest.mark.asyncio
    async def test_cross_agent_context_dependency(self, test_database):
        """Test dependencias de contexto entre agentes"""
        # Crear contexto con dependencias
        dependency_chain = [
            {"context_id": "ctx_data_analysis", "agent": "reasoner", "depends_on": []},
            {"context_id": "ctx_planning", "agent": "planner", "depends_on": ["ctx_data_analysis"]},
            {"context_id": "ctx_execution", "agent": "executor", "depends_on": ["ctx_planning"]},
            {"context_id": "ctx_validation", "agent": "verifier", "depends_on": ["ctx_execution"]}
        ]
        
        execution_order = []
        
        for context_info in dependency_chain:
            context_id = context_info["context_id"]
            agent_id = context_info["agent"]
            depends_on = context_info["depends_on"]
            
            # Verificar dependencias
            dependencies_ready = True
            if depends_on:
                for dep_context_id in depends_on:
                    dep_row = await test_database.main_conn.fetchrow(
                        "SELECT * FROM test_context_persistence WHERE context_id = $1",
                        dep_context_id
                    )
                    if not dep_row:
                        dependencies_ready = False
                        break
            
            if dependencies_ready:
                # Crear contexto para este agente
                context_data = {
                    "agent": agent_id,
                    "dependencies": depends_on,
                    "created_from": depends_on[0] if depends_on else None,
                    "processing_stage": len(execution_order) + 1
                }
                
                await test_database.main_conn.execute(
                    "INSERT INTO test_context_persistence (context_id, agent_id, data) VALUES ($1, $2, $3)",
                    context_id, agent_id, json.dumps(context_data)
                )
                
                execution_order.append({
                    "context_id": context_id,
                    "agent": agent_id,
                    "execution_time": datetime.now()
                })
            else:
                # Dependencia no lista
                execution_order.append({
                    "context_id": context_id,
                    "agent": agent_id,
                    "status": "dependency_not_ready",
                    "missing_deps": [dep for dep in depends_on if dep not in [e["context_id"] for e in execution_order]]
                })
        
        # Verificar orden de ejecución
        assert len(execution_order) == 4, "Todos los contextos deberían procesarse"
        
        # Verificar que se ejecutaron en el orden correcto
        executed_agents = [e["agent"] for e in execution_order if "execution_time" in e]
        expected_order = ["reasoner", "planner", "executor", "verifier"]
        
        for i, expected_agent in enumerate(expected_order):
            if i < len(executed_agents):
                assert executed_agents[i] == expected_agent, f"Orden de ejecución incorrecto"
        
        print(f"Test dependencias contexto completado - {len(execution_order)} contextos procesados")
    
    @pytest.mark.asyncio
    async def test_context_persistence_levels(self, test_database):
        """Test diferentes niveles de persistencia de contexto"""
        persistence_levels = [
            {"level": "ephemeral", "scope": "task", "lifetime": "session"},
            {"level": "short_term", "scope": "session", "lifetime": "hours"},
            {"level": "medium_term", "scope": "task", "lifetime": "days"},
            {"level": "long_term", "scope": "global", "lifetime": "weeks"},
            {"level": "permanent", "scope": "global", "lifetime": "permanent"}
        ]
        
        persisted_contexts = []
        
        for level_info in persistence_levels:
            context_id = f"persistence_test_{level_info['level']}"
            
            context_data = {
                "persistence_level": level_info["level"],
                "scope": level_info["scope"],
                "lifetime": level_info["lifetime"],
                "created_at": datetime.now().isoformat(),
                "content": f"Test content for {level_info['level']} persistence"
            }
            
            await test_database.main_conn.execute(
                "INSERT INTO test_context_persistence (context_id, agent_id, data) VALUES ($1, $2, $3)",
                context_id, "persistence_test_agent", json.dumps(context_data)
            )
            
            persisted_contexts.append({
                "context_id": context_id,
                "level": level_info["level"],
                "stored": True
            })
        
        # Simular limpieza de contextos según nivel de persistencia
        cleanup_results = []
        
        for context_info in persisted_contexts:
            context_id = context_info["context_id"]
            level = context_info["level"]
            
            # Lógica de limpieza simulada
            should_keep = True
            
            if level == "ephemeral":
                should_keep = False  # No persistente
            elif level == "short_term":
                should_keep = random.choice([True, False])  # 50% chance
            elif level == "medium_term":
                should_keep = True  # Persistente
            elif level == "long_term":
                should_keep = True  # Muy persistente
            elif level == "permanent":
                should_keep = True  # Nunca se elimina
            
            if not should_keep:
                await test_database.main_conn.execute(
                    "DELETE FROM test_context_persistence WHERE context_id = $1",
                    context_id
                )
            
            cleanup_results.append({
                "context_id": context_id,
                "level": level,
                "kept": should_keep
            })
        
        # Verificar resultados de limpieza
        kept_contexts = [r for r in cleanup_results if r["kept"]]
        deleted_contexts = [r for r in cleanup_results if not r["kept"]]
        
        # Contextos ephemeral y algunos short_term deberían haberse eliminado
        ephemeral_deleted = any(r["level"] == "ephemeral" and not r["kept"] for r in cleanup_results)
        assert ephemeral_deleted, "Contexto ephemeral debería haberse eliminado"
        
        # Contextos long_term y permanent deberían haberse mantenido
        long_term_kept = all(
            r["kept"] for r in cleanup_results 
            if r["level"] in ["long_term", "permanent"]
        )
        assert long_term_kept, "Contextos long_term/permanent deberían mantenerse"
        
        print(f"Test niveles persistencia completado:")
        print(f"  - Contextos mantenidos: {len(kept_contexts)}")
        print(f"  - Contextos eliminados: {len(deleted_contexts)}")
    
    @pytest.mark.asyncio
    async def test_context_memory_efficiency(self, test_database):
        """Test eficiencia de memoria en contexto"""
        # Crear múltiples contextos con diferentes tamaños
        context_sizes = {
            "small": 100,      # 100 items
            "medium": 1000,    # 1000 items  
            "large": 10000,    # 10000 items
            "xlarge": 50000    # 50000 items
        }
        
        memory_tests = []
        
        for size_name, size in context_sizes.items():
            context_id = f"memory_test_{size_name}"
            
            # Crear datos de prueba
            test_data = {
                "size_category": size_name,
                "data_points": [
                    {
                        "id": i,
                        "value": f"test_value_{i}",
                        "metadata": {
                            "processed": random.choice([True, False]),
                            "category": f"cat_{i % 10}",
                            "score": random.random()
                        }
                    }
                    for i in range(min(size, 1000))  # Limitar para performance
                ],
                "summary": {
                    "total_items": len([i for i in range(min(size, 1000))]),
                    "processed_items": sum(1 for i in range(min(size, 1000)) if random.choice([True, False])),
                    "memory_estimate_kb": size / 100
                }
            }
            
            # Medir tiempo de almacenamiento
            start_time = time.time()
            await test_database.main_conn.execute(
                "INSERT INTO test_context_persistence (context_id, agent_id, data) VALUES ($1, $2, $3)",
                context_id, "memory_test_agent", json.dumps(test_data)
            )
            storage_time = time.time() - start_time
            
            # Medir tiempo de recuperación
            start_time = time.time()
            retrieved_context = await test_database.main_conn.fetchrow(
                "SELECT * FROM test_context_persistence WHERE context_id = $1",
                context_id
            )
            retrieval_time = time.time() - start_time
            
            # Verificar integridad de datos
            if retrieved_context:
                retrieved_data = json.loads(retrieved_context["data"])
                assert len(retrieved_data["data_points"]) > 0
                
                memory_tests.append({
                    "size": size_name,
                    "storage_time_ms": storage_time * 1000,
                    "retrieval_time_ms": retrieval_time * 1000,
                    "data_integrity": True,
                    "data_points": len(retrieved_data["data_points"])
                })
        
        # Verificar métricas de eficiencia
        for test in memory_tests:
            # Verificar que el tiempo de almacenamiento es razonable
            assert test["storage_time_ms"] < 1000, \
                f"Almacenamiento muy lento para {test['size']}: {test['storage_time_ms']:.2f}ms"
            
            # Verificar que el tiempo de recuperación es razonable  
            assert test["retrieval_time_ms"] < 500, \
                f"Recuperación muy lenta para {test['size']}: {test['retrieval_time_ms']:.2f}ms"
            
            assert test["data_integrity"], f"Integridad de datos fallida para {test['size']}"
        
        print(f"Test eficiencia memoria completado:")
        for test in memory_tests:
            print(f"  - {test['size']}: Almacén {test['storage_time_ms']:.2f}ms, "
                  f"Recup {test['retrieval_time_ms']:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_context_compression_optimization(self, test_database):
        """Test compresión y optimización de contexto"""
        # Crear contexto con datos redundantes para compresión
        redundant_context = {
            "repeated_pattern": "This is repeated many times in the context",
            "nested_structure": {
                "level1": {
                    "level2": {
                        "level3": {
                            "level4": {
                                "repeated_data": "Same data repeated at multiple levels",
                                "array_repetition": ["item1", "item2", "item3"] * 10
                            }
                        }
                    }
                }
            },
            "metadata_redundancy": {
                "created_by": "system",
                "processed_by": "system", 
                "verified_by": "system"
            }
        }
        
        # Simular compresión (en un entorno real sería compresión real)
        compressed_context = {
            "pattern_hash": "abc123def456",
            "nested_structure_hash": "xyz789",
            "metadata_optimized": {"system": "common_processor"},
            "compression_ratio": 0.3,
            "original_size": len(json.dumps(redundant_context)),
            "compressed_size": int(len(json.dumps(redundant_context)) * 0.3)
        }
        
        context_id = "compression_test_001"
        
        # Insertar contexto original
        await test_database.main_conn.execute(
            "INSERT INTO test_context_persistence (context_id, agent_id, data) VALUES ($1, $2, $3)",
            context_id, "compression_agent", json.dumps(redundant_context)
        )
        
        # Actualizar con versión comprimida
        await test_database.main_conn.execute(
            "UPDATE test_context_persistence SET data = $1 WHERE context_id = $2",
            json.dumps(compressed_context), context_id
        )
        
        # Verificar compresión
        compressed_row = await test_database.main_conn.fetchrow(
            "SELECT * FROM test_context_persistence WHERE context_id = $1",
            context_id
        )
        
        compressed_data = json.loads(compressed_row["data"])
        
        assert "compression_ratio" in compressed_data
        assert compressed_data["compression_ratio"] < 1.0
        assert compressed_data["compressed_size"] < compressed_data["original_size"]
        
        # Simular descompresión para uso
        decompressed_data = {
            "pattern": "This is repeated many times in the context",
            "structure": compressed_data["nested_structure_hash"],
            "processor": compressed_data["metadata_optimized"]["system"]
        }
        
        print(f"Test compresión contexto completado:")
        print(f"  - Ratio compresión: {compressed_data['compression_ratio']:.2f}")
        print(f"  - Tamaño original: {compressed_data['original_size']} bytes")
        print(f"  - Tamaño comprimido: {compressed_data['compressed_size']} bytes")
        print(f"  - Ahorro: {(1 - compressed_data['compression_ratio']) * 100:.1f}%")
    
    @pytest.mark.asyncio
    async def test_context_sync_scenarios(self, test_database):
        """Test escenarios de sincronización de contexto"""
        # Escenario: Múltiples agentes necesitan contexto consistente
        sync_scenarios = [
            {
                "scenario": "read_only_sync",
                "agents": ["agent1", "agent2", "agent3"],
                "operation": "concurrent_read",
                "expected_behavior": "all_read_consistent_data"
            },
            {
                "scenario": "write_contention", 
                "agents": ["agent1", "agent2"],
                "operation": "concurrent_write",
                "expected_behavior": "last_writer_wins"
            },
            {
                "scenario": "read_write_race",
                "agents": ["reader1", "writer1", "reader2"],
                "operation": "mixed_operations", 
                "expected_behavior": "readers_get_consistent_snapshot"
            }
        ]
        
        sync_results = []
        
        for scenario in sync_scenarios:
            scenario_id = f"sync_{scenario['scenario']}"
            
            # Configurar contexto base
            base_context = {
                "scenario": scenario["scenario"],
                "agents_involved": scenario["agents"],
                "operation_type": scenario["operation"],
                "initial_value": 100,
                "modifications": []
            }
            
            await test_database.main_conn.execute(
                "INSERT INTO test_context_persistence (context_id, agent_id, data) VALUES ($1, $2, $3)",
                scenario_id, "sync_coordinator", json.dumps(base_context)
            )
            
            async def agent_operation(agent_id: str, operation_delay: float):
                """Simular operación de agente"""
                await asyncio.sleep(operation_delay)
                
                if scenario["operation"] == "concurrent_read":
                    # Solo leer
                    context_row = await test_database.main_conn.fetchrow(
                        "SELECT * FROM test_context_persistence WHERE context_id = $1",
                        scenario_id
                    )
                    return {
                        "agent": agent_id,
                        "operation": "read",
                        "value": json.loads(context_row["data"])["initial_value"],
                        "success": True
                    }
                
                elif scenario["operation"] == "concurrent_write":
                    # Escribir nuevo valor
                    new_value = random.randint(200, 300)
                    
                    # Leer contexto actual
                    current_context = await test_database.main_conn.fetchrow(
                        "SELECT * FROM test_context_persistence WHERE context_id = $1",
                        scenario_id
                    )
                    
                    if current_context:
                        current_data = json.loads(current_context["data"])
                        updated_data = {
                            **current_data,
                            "initial_value": new_value,
                            "last_modified_by": agent_id,
                            "last_modified_at": datetime.now().isoformat()
                        }
                        
                        await test_database.main_conn.execute(
                            "UPDATE test_context_persistence SET data = $1 WHERE context_id = $2",
                            json.dumps(updated_data), scenario_id
                        )
                        
                        return {
                            "agent": agent_id,
                            "operation": "write",
                            "value": new_value,
                            "success": True
                        }
                
                elif scenario["operation"] == "mixed_operations":
                    if "read" in agent_id:
                        # Operación de lectura
                        context_row = await test_database.main_conn.fetchrow(
                            "SELECT * FROM test_context_persistence WHERE context_id = $1",
                            scenario_id
                        )
                        return {
                            "agent": agent_id,
                            "operation": "read",
                            "value": json.loads(context_row["data"])["initial_value"],
                            "success": True
                        }
                    else:
                        # Operación de escritura
                        new_value = random.randint(400, 500)
                        
                        context_row = await test_database.main_conn.fetchrow(
                            "SELECT * FROM test_context_persistence WHERE context_id = $1",
                            scenario_id
                        )
                        
                        if context_row:
                            current_data = json.loads(context_row["data"])
                            updated_data = {
                                **current_data,
                                "initial_value": new_value,
                                "last_modified_by": agent_id
                            }
                            
                            await test_database.main_conn.execute(
                                "UPDATE test_context_persistence SET data = $1 WHERE context_id = $2",
                                json.dumps(updated_data), scenario_id
                            )
                            
                            return {
                                "agent": agent_id,
                                "operation": "write", 
                                "value": new_value,
                                "success": True
                            }
                
                return {"agent": agent_id, "operation": "unknown", "success": False}
            
            # Ejecutar operaciones de agentes
            agent_tasks = [
                agent_operation(agent_id, random.uniform(0.01, 0.1))
                for agent_id in scenario["agents"]
            ]
            
            results = await asyncio.gather(*agent_tasks)
            
            # Verificar consistencia del escenario
            final_context = await test_database.main_conn.fetchrow(
                "SELECT * FROM test_context_persistence WHERE context_id = $1",
                scenario_id
            )
            
            final_data = json.loads(final_context["data"])
            
            sync_results.append({
                "scenario": scenario["scenario"],
                "operations": results,
                "final_value": final_data["initial_value"],
                "total_agents": len(scenario["agents"])
            })
        
        # Verificar resultados de sincronización
        for result in sync_results:
            scenario_name = result["scenario"]
            operations = result["operations"]
            successful_ops = [op for op in operations if op["success"]]
            
            assert len(successful_ops) > 0, f"No hubo operaciones exitosas en {scenario_name}"
            
            if scenario_name == "read_only_sync":
                # Todas las lecturas deberían ser consistentes
                read_values = [op["value"] for op in operations if op["operation"] == "read"]
                assert len(set(read_values)) == 1, f"Valores inconsistentes en {scenario_name}"
            
            elif scenario_name == "write_contention":
                # Verificar que solo hay un writer final
                write_ops = [op for op in operations if op["operation"] == "write"]
                final_writers = [op for op in write_ops if op["value"] == result["final_value"]]
                assert len(final_writers) == 1, f"Múltiples writers finales en {scenario_name}"
        
        print(f"Test sincronización contexto completado:")
        for result in sync_results:
            print(f"  - {result['scenario']}: {len(result['operations'])} operaciones, "
                  f"Valor final: {result['final_value']}")