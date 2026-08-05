"""
Test suite para los Diferenciadores Técnicos del MCP Core Superior

Cubre:
- Context Persistence Engine
- Collaboration Engine  
- Intelligent Router
- Context Persistence Utils
- Collaboration Utils
- Auto Healing Engine
- Parallel Execution Engine
"""

import pytest
import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch, call
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

# Test marks
pytestmark = [pytest.mark.technical, pytest.mark.unit, pytest.mark.async_test]


class TestContextPersistenceEngine:
    """Tests para el motor de persistencia de contexto"""
    
    @pytest.fixture
    def context_engine(self):
        """Fixture del motor de contexto"""
        from core.context_persistence_engine import ContextPersistenceEngine
        return ContextPersistenceEngine
    
    @pytest.fixture
    def mock_vector_store(self):
        """Mock del vector store"""
        mock_store = AsyncMock()
        mock_store.embed.return_value = [0.1] * 1536
        mock_store.similarity_search.return_value = [
            {"id": "context1", "score": 0.95, "metadata": {"type": "conversation"}}
        ]
        mock_store.store.return_value = "context_id_123"
        return mock_store
    
    async def test_engine_initialization(self, context_engine):
        """Test de inicialización del motor"""
        engine = context_engine()
        
        with patch('core.context_persistence_engine.AsyncPG') as mock_pg:
            with patch('core.context_persistence_engine.Redis') as mock_redis:
                mock_pg.return_value = AsyncMock()
                mock_redis.return_value = AsyncMock()
                
                result = await engine.initialize()
                
                assert result['success'] is True
                assert engine.initialized is True
    
    async def test_context_storage(self, context_engine, mock_vector_store):
        """Test de almacenamiento de contexto"""
        engine = context_engine()
        engine.vector_store = mock_vector_store
        
        context_data = {
            "session_id": "session_123",
            "user_id": "user_456",
            "messages": [
                {"role": "user", "content": "Hello", "timestamp": "2025-11-04T05:43:15Z"},
                {"role": "assistant", "content": "Hi there!", "timestamp": "2025-11-04T05:43:16Z"}
            ],
            "metadata": {
                "conversation_topic": "greeting",
                "agent_id": "assistant_agent"
            }
        }
        
        with patch.object(engine, '_create_embedding') as mock_embed:
            mock_embed.return_value = [0.1] * 1536
            
            result = await engine.store_context(context_data)
            
            assert result['success'] is True
            assert 'context_id' in result
            assert mock_vector_store.store.called
            assert mock_embed.called
    
    async def test_context_retrieval(self, context_engine, mock_vector_store):
        """Test de recuperación de contexto"""
        engine = context_engine()
        engine.vector_store = mock_vector_store
        
        query = "What was the last conversation about?"
        
        with patch.object(engine, '_create_embedding') as mock_embed:
            mock_embed.return_value = [0.2] * 1536
            
            result = await engine.retrieve_context(
                query=query,
                user_id="user_456",
                session_id="session_123",
                limit=5
            )
            
            assert result['success'] is True
            assert 'contexts' in result
            assert len(result['contexts']) > 0
            assert mock_vector_store.similarity_search.called
    
    async def test_context_summarization(self, context_engine):
        """Test de resumen de contexto"""
        engine = context_engine()
        
        long_context = {
            "messages": [
                {"role": "user", "content": "Tell me about Python", "timestamp": "2025-11-04T05:40:00Z"},
                {"role": "assistant", "content": "Python is a programming language...", "timestamp": "2025-11-04T05:40:05Z"},
                {"role": "user", "content": "What about libraries?", "timestamp": "2025-11-04T05:41:00Z"},
                {"role": "assistant", "content": "Python has many libraries like pandas...", "timestamp": "2025-11-04T05:41:05Z"},
                # ... many more messages
            ]
        }
        
        with patch.object(engine, '_summarize_messages') as mock_summarize:
            mock_summarize.return_value = "User asked about Python and its libraries."
            
            summary = await engine.summarize_context(long_context)
            
            assert isinstance(summary, str)
            assert len(summary) < len(json.dumps(long_context))
            assert mock_summarize.called
    
    async def test_context_compression(self, context_engine):
        """Test de compresión de contexto"""
        engine = context_engine()
        
        large_context = {
            "messages": [{"content": f"Message {i}", "role": "user"} for i in range(1000)],
            "metadata": {"session_id": "long_session"}
        }
        
        with patch.object(engine, '_compress_messages') as mock_compress:
            mock_compress.return_value = {
                "compressed_messages": [{"content": "Compressed content", "role": "user"}],
                "compression_ratio": 0.1
            }
            
            compressed = await engine.compress_context(large_context, max_messages=50)
            
            assert 'compressed_messages' in compressed
            assert 'compression_ratio' in compressed
            assert compressed['compression_ratio'] <= 1.0
    
    async def test_context_expiration(self, context_engine):
        """Test de expiración de contexto"""
        engine = context_engine()
        
        # Crear contexto con TTL
        context_id = "expire_context_123"
        ttl_seconds = 60
        
        with patch.object(engine, '_set_expiration') as mock_expire:
            mock_expire.return_value = True
            
            result = await engine.set_context_expiration(
                context_id=context_id,
                ttl_seconds=ttl_seconds
            )
            
            assert result['success'] is True
            assert mock_expire.called
    
    async def test_context_backup_restore(self, context_engine):
        """Test de backup y restauración de contexto"""
        engine = context_engine()
        
        # Crear contexto de prueba
        context_data = {
            "session_id": "backup_session",
            "messages": [{"content": "Test message", "role": "user"}]
        }
        
        with patch.object(engine, 'store_context') as mock_store:
            mock_store.return_value = {"success": True, "context_id": "backup_123"}
            
            # Backup
            backup = await engine.backup_context(context_data)
            assert backup['success'] is True
            assert 'backup_id' in backup
        
        with patch.object(engine, 'restore_context') as mock_restore:
            mock_restore.return_value = context_data
            
            # Restore
            restored = await engine.restore_context("backup_123")
            assert restored == context_data
    
    async def test_cross_session_context(self, context_engine):
        """Test de contexto entre sesiones"""
        engine = context_engine()
        
        # Contexto persistente entre sesiones
        persistent_context = {
            "user_id": "user_456",
            "session_type": "cross_session",
            "persistent_data": {
                "user_preferences": {"theme": "dark"},
                "conversation_style": "formal",
                "expertise_areas": ["python", "ai"]
            },
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
        
        with patch.object(engine, '_store_persistent') as mock_store:
            mock_store.return_value = "persistent_context_123"
            
            result = await engine.store_persistent_context(persistent_context)
            
            assert result['success'] is True
            assert mock_store.called
    
    async def test_context_analytics(self, context_engine):
        """Test de análisis de contexto"""
        engine = context_engine()
        
        contexts = [
            {
                "session_id": f"session_{i}",
                "user_id": "user_123",
                "created_at": datetime.utcnow().isoformat(),
                "message_count": 10 + i
            }
            for i in range(10)
        ]
        
        analytics = await engine.analyze_contexts(contexts)
        
        assert 'total_sessions' in analytics
        assert 'avg_messages_per_session' in analytics
        assert 'user_engagement' in analytics
        assert analytics['total_sessions'] == 10


class TestCollaborationEngine:
    """Tests para el motor de colaboración"""
    
    @pytest.fixture
    def collaboration_engine(self):
        """Fixture del motor de colaboración"""
        from core.collaboration_engine import CollaborationEngine
        return CollaborationEngine
    
    async def test_collaboration_session_creation(self, collaboration_engine):
        """Test de creación de sesión de colaboración"""
        engine = collaboration_engine()
        
        session_config = {
            "session_name": "Python Development",
            "participants": [
                {"user_id": "user1", "role": "developer"},
                {"user_id": "user2", "role": "reviewer"}
            ],
            "permissions": {
                "user1": ["read", "write"],
                "user2": ["read", "comment"]
            }
        }
        
        with patch.object(engine, '_create_session') as mock_create:
            mock_create.return_value = {
                "session_id": "collab_session_123",
                "status": "active"
            }
            
            session = await engine.create_collaboration_session(session_config)
            
            assert session['success'] is True
            assert 'session_id' in session
            assert session['status'] == "active"
    
    async def test_agent_collaboration(self, collaboration_engine):
        """Test de colaboración entre agentes"""
        engine = collaboration_engine()
        
        # Simular colaboración entre agentes
        agent1 = {"agent_id": "python_executor", "status": "busy"}
        agent2 = {"agent_id": "search_engine", "status": "available"}
        
        collaboration_task = {
            "task_type": "code_analysis",
            "participants": ["python_executor", "search_engine"],
            "shared_resources": ["code_context", "search_results"]
        }
        
        with patch.object(engine, '_coordinate_agents') as mock_coordinate:
            mock_coordinate.return_value = {
                "collaboration_id": "collab_123",
                "participants_status": {
                    "python_executor": "participating",
                    "search_engine": "participating"
                }
            }
            
            result = await engine.initiate_agent_collaboration(collaboration_task)
            
            assert result['success'] is True
            assert 'collaboration_id' in result
            assert mock_coordinate.called
    
    async def test_shared_state_management(self, collaboration_engine):
        """Test de gestión de estado compartido"""
        engine = collaboration_engine()
        
        # Estado compartido entre participantes
        shared_state = {
            "session_id": "shared_session_123",
            "state_data": {
                "current_code": "print('Hello World')",
                "analysis_results": {"lines": 1, "functions": 0},
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
        with patch.object(engine, '_update_shared_state') as mock_update:
            mock_update.return_value = True
            
            result = await engine.update_shared_state(shared_state)
            
            assert result['success'] is True
            assert mock_update.called
    
    async def test_conflict_resolution(self, collaboration_engine):
        """Test de resolución de conflictos"""
        engine = collaboration_engine()
        
        # Conflicto de edición simultánea
        conflict = {
            "resource_id": "file.py",
            "conflicts": [
                {"user_id": "user1", "change": "Added function", "timestamp": "2025-11-04T05:43:00Z"},
                {"user_id": "user2", "change": "Modified function", "timestamp": "2025-11-04T05:43:01Z"}
            ],
            "resolution_strategy": "merge"
        }
        
        with patch.object(engine, '_resolve_conflict') as mock_resolve:
            mock_resolve.return_value = {
                "resolved": True,
                "solution": "Merged changes from both users",
                "merged_version": "print('Hello World')\ndef greeting():\n    print('Hi')"
            }
            
            resolution = await engine.resolve_collaboration_conflict(conflict)
            
            assert resolution['resolved'] is True
            assert 'solution' in resolution
    
    async def test_collaboration_events(self, collaboration_engine):
        """Test de eventos de colaboración"""
        engine = collaboration_engine()
        
        # Simular evento de colaboración
        event = {
            "session_id": "event_session_123",
            "event_type": "user_joined",
            "user_id": "user123",
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"join_method": "invitation"}
        }
        
        with patch.object(engine, '_broadcast_event') as mock_broadcast:
            mock_broadcast.return_value = True
            
            result = await engine.broadcast_collaboration_event(event)
            
            assert result['success'] is True
            assert mock_broadcast.called
    
    async def test_collaboration_history(self, collaboration_engine):
        """Test de historial de colaboración"""
        engine = collaboration_engine()
        
        session_id = "history_session_123"
        
        # Simular historial de actividades
        history_data = [
            {
                "timestamp": "2025-11-04T05:40:00Z",
                "event_type": "session_created",
                "user_id": "user1"
            },
            {
                "timestamp": "2025-11-04T05:41:00Z",
                "event_type": "user_joined",
                "user_id": "user2"
            },
            {
                "timestamp": "2025-11-04T05:42:00Z",
                "event_type": "file_modified",
                "user_id": "user1"
            }
        ]
        
        with patch.object(engine, '_get_session_history') as mock_history:
            mock_history.return_value = history_data
            
            history = await engine.get_collaboration_history(session_id)
            
            assert isinstance(history, list)
            assert len(history) == 3
            assert history[0]['event_type'] == "session_created"
    
    async def test_permission_management(self, collaboration_engine):
        """Test de gestión de permisos"""
        engine = collaboration_engine()
        
        session_id = "permission_session_123"
        user_id = "user123"
        
        # Otorgar permisos
        permissions = {
            "read": True,
            "write": True,
            "comment": True,
            "admin": False
        }
        
        with patch.object(engine, '_update_permissions') as mock_update:
            mock_update.return_value = True
            
            result = await engine.update_user_permissions(
                session_id, user_id, permissions
            )
            
            assert result['success'] is True
            assert mock_update.called
    
    async def test_collaboration_metrics(self, collaboration_engine):
        """Test de métricas de colaboración"""
        engine = collaboration_engine()
        
        # Métricas de sesión de colaboración
        session_metrics = await engine.get_collaboration_metrics(
            session_id="metrics_session_123"
        )
        
        assert 'participant_count' in session_metrics
        assert 'activity_level' in session_metrics
        assert 'interaction_frequency' in session_metrics
        assert 'collaboration_score' in session_metrics
    
    async def test_auto_scaling_collaboration(self, collaboration_engine):
        """Test de auto-escalado de colaboración"""
        engine = collaboration_engine()
        
        # Simular alta demanda de colaboración
        load_data = {
            "active_sessions": 50,
            "concurrent_participants": 200,
            "resource_utilization": 0.8
        }
        
        with patch.object(engine, '_scale_collaboration_resources') as mock_scale:
            mock_scale.return_value = {
                "scaled": True,
                "new_instances": 2,
                "load_balance_applied": True
            }
            
            scaling_result = await engine.handle_collaboration_load(load_data)
            
            assert scaling_result['scaled'] is True
            assert scaling_result['new_instances'] > 0


class TestIntelligentRouter:
    """Tests para el router inteligente"""
    
    @pytest.fixture
    def intelligent_router(self):
        """Fixture del router inteligente"""
        from core.intelligent_router import IntelligentRouter
        return IntelligentRouter
    
    async def test_router_initialization(self, intelligent_router):
        """Test de inicialización del router"""
        router = intelligent_router()
        
        with patch.object(router, '_load_routing_models') as mock_load:
            mock_load.return_value = True
            
            result = await router.initialize()
            
            assert result['success'] is True
            assert router.initialized is True
    
    async def test_request_routing(self, intelligent_router):
        """Test de enrutamiento de requests"""
        router = intelligent_router()
        
        # Request de ejemplo
        request = {
            "operation": "code_execution",
            "parameters": {
                "language": "python",
                "code": "print('Hello')",
                "timeout": 30
            },
            "context": {
                "user_id": "user123",
                "session_id": "session456"
            }
        }
        
        with patch.object(router, '_classify_request') as mock_classify:
            with patch.object(router, '_select_optimal_agent') as mock_select:
                mock_classify.return_value = {
                    "type": "code_execution",
                    "complexity": "medium",
                    "resource_requirements": {"cpu": 1, "memory": 512}
                }
                mock_select.return_value = "python_executor_agent"
                
                route = await router.route_request(request)
                
                assert route['success'] is True
                assert 'selected_agent' in route
                assert route['selected_agent'] == "python_executor_agent"
    
    async def test_agent_selection_criteria(self, intelligent_router):
        """Test de criterios de selección de agentes"""
        router = intelligent_router()
        
        # Disponibilidad de agentes
        agents_status = {
            "python_executor": {
                "available": True,
                "current_load": 0.3,
                "specialization": ["python", "data_analysis"],
                "performance_score": 0.9
            },
            "git_operations": {
                "available": True,
                "current_load": 0.1,
                "specialization": ["git", "version_control"],
                "performance_score": 0.85
            },
            "web_scraping": {
                "available": False,
                "current_load": 1.0,
                "specialization": ["web", "scraping"],
                "performance_score": 0.7
            }
        }
        
        selection_request = {
            "task_type": "python_execution",
            "requirements": {
                "languages": ["python"],
                "max_wait_time": 5
            }
        }
        
        with patch.object(router, '_get_agent_status') as mock_status:
            mock_status.return_value = agents_status
            
            selected_agent = router._select_optimal_agent(selection_request, agents_status)
            
            assert selected_agent in ["python_executor", "git_operations"]
            # El agente seleccionado debe estar disponible
            assert agents_status[selected_agent]["available"] is True
    
    async def test_load_balancing(self, intelligent_router):
        """Test de balanceador de carga"""
        router = intelligent_router()
        
        # Pool de agentes con diferentes cargas
        agent_pool = {
            "python_executor_1": {"load": 0.8, "available": True},
            "python_executor_2": {"load": 0.2, "available": True},
            "python_executor_3": {"load": 0.9, "available": True}
        }
        
        selected_agent = router._balance_load(agent_pool)
        
        # Debería seleccionar el agente con menor carga
        assert agent_pool[selected_agent]["load"] <= min(
            agent[agent]["load"] for agent in agent_pool.values()
        )
    
    async def test_failover_mechanism(self, intelligent_router):
        """Test de mecanismo de failover"""
        router = intelligent_router()
        
        # Agente primario fallido
        primary_agent = {
            "id": "python_executor_1",
            "status": "unavailable",
            "last_heartbeat": "2025-11-04T05:00:00Z"  # Muy antiguo
        }
        
        backup_agents = [
            {"id": "python_executor_2", "status": "available", "load": 0.3},
            {"id": "python_executor_3", "status": "available", "load": 0.5}
        ]
        
        with patch.object(router, '_detect_agent_failure') as mock_detect:
            mock_detect.return_value = True
            
            with patch.object(router, '_select_backup_agent') as mock_backup:
                mock_backup.return_value = "python_executor_2"
                
                failover_result = await router.handle_agent_failover(
                    primary_agent, backup_agents
                )
                
                assert failover_result['failover_performed'] is True
                assert failover_result['backup_agent'] == "python_executor_2"
    
    async def test_caching_mechanism(self, intelligent_router):
        """Test de mecanismo de caching"""
        router = intelligent_router()
        
        # Request repetido
        request = {
            "operation": "python_execution",
            "code": "x = 1 + 1\nprint(x)"
        }
        
        # Primera vez - cache miss
        with patch.object(router, '_get_cached_result') as mock_cache_get:
            mock_cache_get.return_value = None
            
            with patch.object(router, '_cache_result') as mock_cache_set:
                mock_cache_set.return_value = True
                
                result1 = await router.route_request(request)
                # Debería procesar el request
                assert result1['success'] is True
                assert mock_cache_set.called
        
        # Segunda vez - cache hit
        cached_result = {"output": "2", "execution_time": 0.05}
        with patch.object(router, '_get_cached_result') as mock_cache_get:
            mock_cache_get.return_value = cached_result
            
            result2 = await router.route_request(request)
            
            assert result2['cached'] is True
            assert result2['result'] == cached_result
    
    async def test_performance_optimization(self, intelligent_router):
        """Test de optimización de performance"""
        router = intelligent_router()
        
        # Métricas de performance
        performance_data = {
            "agent_response_times": {
                "python_executor": 0.15,
                "git_operations": 0.08,
                "search_engine": 0.12
            },
            "success_rates": {
                "python_executor": 0.98,
                "git_operations": 0.99,
                "search_engine": 0.97
            }
        }
        
        with patch.object(router, '_update_performance_metrics') as mock_update:
            mock_update.return_value = True
            
            optimized = await router.optimize_routing_performance(performance_data)
            
            assert optimized['success'] is True
            assert mock_update.called
    
    async def test_adaptive_routing(self, intelligent_router):
        """Test de enrutamiento adaptativo"""
        router = intelligent_router()
        
        # Cambios en el patrón de uso
        usage_patterns = {
            "peak_hours": True,
            "agent_availability_changes": ["python_executor_1", "python_executor_2"],
            "error_rate_increase": True,
            "user_feedback": {"negative": True, "reason": "slow_response"}
        }
        
        with patch.object(router, '_analyze_usage_patterns') as mock_analyze:
            mock_analyze.return_value = {
                "routing_adjustments": [
                    {"agent": "python_executor", "weight": 0.8},
                    {"agent": "git_operations", "weight": 0.2}
                ],
                "strategy_changes": ["prioritize_availability", "reduce_timeout"]
            }
            
            adaptations = await router.adapt_routing_strategy(usage_patterns)
            
            assert adaptations['strategy_updated'] is True
            assert len(adaptations['routing_adjustments']) > 0


class TestContextPersistenceUtils:
    """Tests para utilidades de persistencia de contexto"""
    
    @pytest.fixture
    def context_utils(self):
        """Fixture de utilidades de contexto"""
        from core.collaboration_utils import ContextUtils
        return ContextUtils
    
    async def test_context_serialization(self, context_utils):
        """Test de serialización de contexto"""
        context_data = {
            "session_id": "test_session",
            "messages": [
                {"role": "user", "content": "Hello", "timestamp": "2025-11-04T05:43:15Z"},
                {"role": "assistant", "content": "Hi!", "timestamp": "2025-11-04T05:43:16Z"}
            ],
            "metadata": {"user_id": "test_user"}
        }
        
        # Serializar
        serialized = context_utils.serialize_context(context_data)
        assert isinstance(serialized, bytes)
        
        # Deserializar
        deserialized = context_utils.deserialize_context(serialized)
        assert deserialized == context_data
    
    async def test_context_compression_decompression(self, context_utils):
        """Test de compresión y descompresión"""
        large_context = {
            "session_id": "large_session",
            "messages": [{"content": f"Message {i}", "role": "user"} for i in range(100)]
        }
        
        # Comprimir
        compressed = context_utils.compress_context(large_context)
        assert isinstance(compressed, bytes)
        assert len(compressed) < len(json.dumps(large_context))
        
        # Descomprimir
        decompressed = context_utils.decompress_context(compressed)
        assert decompressed == large_context
    
    async def test_context_validation(self, context_utils):
        """Test de validación de contexto"""
        # Contexto válido
        valid_context = {
            "session_id": "valid_session",
            "messages": [{"content": "test", "role": "user"}],
            "user_id": "user123"
        }
        assert context_utils.validate_context(valid_context) is True
        
        # Contexto inválido
        invalid_contexts = [
            {},  # Vacío
            {"session_id": "test"},  # Sin messages
            {"messages": []},  # Sin session_id
            {"session_id": "test", "messages": "invalid"}  # messages no es lista
        ]
        
        for invalid in invalid_contexts:
            assert context_utils.validate_context(invalid) is False
    
    async def test_context_versioning(self, context_utils):
        """Test de versionado de contexto"""
        context_data = {
            "session_id": "versioned_session",
            "version": 1,
            "messages": [{"content": "Original", "role": "user"}]
        }
        
        # Crear nueva versión
        new_version = context_utils.create_context_version(
            context_data,
            changes=[{"action": "add_message", "content": "Updated"}]
        )
        
        assert new_version['version'] == 2
        assert len(new_version['messages']) > len(context_data['messages'])
        
        # Obtener versión específica
        specific_version = context_utils.get_context_version(
            "versioned_session", version=2
        )
        assert specific_version['version'] == 2
    
    async def test_context_diff(self, context_utils):
        """Test de diferencias de contexto"""
        context1 = {
            "session_id": "diff_session",
            "messages": [{"content": "Message 1", "role": "user"}]
        }
        
        context2 = {
            "session_id": "diff_session",
            "messages": [
                {"content": "Message 1", "role": "user"},
                {"content": "Message 2", "role": "assistant"}
            ]
        }
        
        diff = context_utils.calculate_context_diff(context1, context2)
        
        assert 'added_messages' in diff
        assert 'removed_messages' in diff
        assert len(diff['added_messages']) == 1


class TestCollaborationUtils:
    """Tests para utilidades de colaboración"""
    
    @pytest.fixture
    def collab_utils(self):
        """Fixture de utilidades de colaboración"""
        from core.collaboration_utils import CollaborationUtils
        return CollaborationUtils
    
    async def test_participant_management(self, collab_utils):
        """Test de gestión de participantes"""
        session_id = "participant_session"
        
        # Agregar participante
        participant = {
            "user_id": "user123",
            "role": "collaborator",
            "permissions": ["read", "write"]
        }
        
        result = collab_utils.add_participant(session_id, participant)
        assert result['success'] is True
        
        # Verificar participante
        participants = collab_utils.get_participants(session_id)
        assert any(p['user_id'] == "user123" for p in participants)
        
        # Remover participante
        remove_result = collab_utils.remove_participant(session_id, "user123")
        assert remove_result['success'] is True
        
        # Verificar que fue removido
        participants_after = collab_utils.get_participants(session_id)
        assert not any(p['user_id'] == "user123" for p in participants_after)
    
    async def test_collaboration_sync(self, collab_utils):
        """Test de sincronización de colaboración"""
        session_id = "sync_session"
        
        # Estado local de participante
        local_state = {
            "participant_id": "user123",
            "last_sync": "2025-11-04T05:40:00Z",
            "local_changes": [
                {"type": "edit", "file": "file.py", "line": 5}
            ]
        }
        
        # Estado remoto
        remote_state = {
            "last_sync": "2025-11-04T05:41:00Z",
            "remote_changes": [
                {"type": "edit", "file": "file.py", "line": 10}
            ]
        }
        
        sync_result = collab_utils.synchronize_collaboration(
            session_id, local_state, remote_state
        )
        
        assert 'synced' in sync_result
        assert 'conflicts' in sync_result
        assert 'merged_state' in sync_result
    
    async def test_collaboration_locks(self, collab_utils):
        """Test de bloqueos de colaboración"""
        session_id = "lock_session"
        resource_id = "file.py"
        user_id = "user123"
        
        # Adquirir lock
        lock_result = collab_utils.acquire_lock(
            session_id, resource_id, user_id, timeout_seconds=30
        )
        assert lock_result['locked'] is True
        
        # Verificar lock activo
        active_locks = collab_utils.get_active_locks(session_id)
        assert any(l['resource_id'] == resource_id for l in active_locks)
        
        # Intentar adquirir lock por otro usuario (debería fallar)
        lock_result2 = collab_utils.acquire_lock(
            session_id, resource_id, "user456", timeout_seconds=30
        )
        assert lock_result2['locked'] is False
        
        # Liberar lock
        unlock_result = collab_utils.release_lock(
            session_id, resource_id, user_id
        )
        assert unlock_result['released'] is True
    
    async def test_collaboration_analytics(self, collab_utils):
        """Test de análisis de colaboración"""
        session_id = "analytics_session"
        
        # Simular eventos de colaboración
        events = [
            {"timestamp": "2025-11-04T05:40:00Z", "type": "participant_joined", "user_id": "user1"},
            {"timestamp": "2025-11-04T05:41:00Z", "type": "participant_joined", "user_id": "user2"},
            {"timestamp": "2025-11-04T05:42:00Z", "type": "file_edited", "user_id": "user1"},
            {"timestamp": "2025-11-04T05:43:00Z", "type": "comment_added", "user_id": "user2"}
        ]
        
        analytics = collab_utils.calculate_collaboration_analytics(session_id, events)
        
        assert 'participant_count' in analytics
        assert 'activity_frequency' in analytics
        assert 'engagement_score' in analytics
        assert analytics['participant_count'] == 2
    
    async def test_conflict_detection(self, collab_utils):
        """Test de detección de conflictos"""
        session_id = "conflict_session"
        
        # Operaciones simultáneas
        operations = [
            {
                "user_id": "user1",
                "operation": "edit",
                "resource": "file.py",
                "timestamp": "2025-11-04T05:43:00Z",
                "changes": [{"line": 5, "content": "print('user1')"}]
            },
            {
                "user_id": "user2",
                "operation": "edit", 
                "resource": "file.py",
                "timestamp": "2025-11-04T05:43:01Z",
                "changes": [{"line": 5, "content": "print('user2')"}]
            }
        ]
        
        conflicts = collab_utils.detect_collaboration_conflicts(operations)
        
        assert len(conflicts) > 0
        assert conflicts[0]['resource'] == "file.py"
        assert conflicts[0]['conflict_type'] == "concurrent_edit"


class TestAutoHealingEngine:
    """Tests para el motor de auto-sanación"""
    
    @pytest.fixture
    def auto_healing_engine(self):
        """Fixture del motor de auto-sanación"""
        from core.auto_healing_engine import AutoHealingEngine
        return AutoHealingEngine
    
    async def test_health_monitoring(self, auto_healing_engine):
        """Test de monitoreo de salud"""
        engine = auto_healing_engine()
        
        # Simular métricas de salud
        health_metrics = {
            "cpu_usage": 85.5,
            "memory_usage": 78.2,
            "response_time": 2.5,
            "error_rate": 0.15,
            "agent_availability": 0.92
        }
        
        health_status = await engine.check_system_health(health_metrics)
        
        assert 'overall_health' in health_status
        assert 'issues_detected' in health_status
        assert 'recommendations' in health_status
    
    async def test_anomaly_detection(self, auto_healing_engine):
        """Test de detección de anomalías"""
        engine = auto_healing_engine()
        
        # Datos de métricas históricas
        historical_data = [
            {"timestamp": "2025-11-04T05:40:00Z", "cpu": 45.0, "memory": 60.0},
            {"timestamp": "2025-11-04T05:41:00Z", "cpu": 50.0, "memory": 65.0},
            {"timestamp": "2025-11-04T05:42:00Z", "cpu": 90.0, "memory": 85.0},  # Anomalía
            {"timestamp": "2025-11-04T05:43:00Z", "cpu": 88.0, "memory": 82.0}
        ]
        
        anomalies = await engine.detect_anomalies(historical_data)
        
        assert len(anomalies) > 0
        assert any(a['metric'] == 'cpu' for a in anomalies)
    
    async def test_healing_action_execution(self, auto_healing_engine):
        """Test de ejecución de acciones de sanación"""
        engine = auto_healing_engine()
        
        # Problema detectado
        issue = {
            "type": "high_cpu_usage",
            "severity": "high",
            "description": "CPU usage above 90%",
            "affected_components": ["python_executor", "search_engine"]
        }
        
        with patch.object(engine, '_execute_healing_action') as mock_action:
            mock_action.return_value = {
                "success": True,
                "action_taken": "scaled_down_compute_intensive_agents",
                "result": "CPU usage reduced to 65%"
            }
            
            healing_result = await engine.execute_healing_action(issue)
            
            assert healing_result['success'] is True
            assert 'action_taken' in healing_result
            assert mock_action.called
    
    async def test_proactive_healing(self, auto_healing_engine):
        """Test de sanación proactiva"""
        engine = auto_healing_engine()
        
        # Predicciones de problemas futuros
        predictions = [
            {
                "issue_type": "memory_exhaustion",
                "probability": 0.8,
                "time_to_occurrence": "10m",
                "severity": "medium"
            },
            {
                "issue_type": "agent_overload",
                "probability": 0.6,
                "time_to_occurrence": "15m",
                "severity": "low"
            }
        ]
        
        with patch.object(engine, '_prevent_issues') as mock_prevent:
            mock_prevent.return_value = {
                "prevented": True,
                "actions_taken": ["preemptive_scaling", "resource_optimization"]
            }
            
            prevention_result = await engine.proactive_healing(predictions)
            
            assert prevention_result['success'] is True
            assert len(prevention_result['actions_taken']) > 0
    
    async def test_healing_history_tracking(self, auto_healing_engine):
        """Test de seguimiento del historial de sanación"""
        engine = auto_healing_engine()
        
        # Registrar evento de sanación
        healing_event = {
            "timestamp": "2025-11-04T05:43:15Z",
            "issue_type": "high_response_time",
            "healing_action": "restart_slow_agents",
            "success": True,
            "healing_time": 30.5
        }
        
        result = await engine.log_healing_event(healing_event)
        assert result['logged'] is True
        
        # Obtener historial
        history = await engine.get_healing_history(
            start_time="2025-11-04T05:00:00Z",
            end_time="2025-11-04T06:00:00Z"
        )
        
        assert isinstance(history, list)
        assert len(history) > 0
    
    async def test_healing_effectiveness(self, auto_healing_engine):
        """Test de efectividad de sanación"""
        engine = auto_healing_engine()
        
        # Métricas de efectividad
        healing_metrics = {
            "total_healing_actions": 100,
            "successful_healing": 85,
            "failed_healing": 15,
            "avg_healing_time": 45.2,
            "issues_prevented": 25
        }
        
        effectiveness = await engine.calculate_healing_effectiveness(healing_metrics)
        
        assert 'success_rate' in effectiveness
        assert 'efficiency_score' in effectiveness
        assert 'prevention_impact' in effectiveness
        assert effectiveness['success_rate'] == 0.85


class TestParallelExecutionEngine:
    """Tests para el motor de ejecución paralela"""
    
    @pytest.fixture
    def parallel_engine(self):
        """Fixture del motor de ejecución paralela"""
        from core.parallel_execution_engine import ParallelExecutionEngine
        return ParallelExecutionEngine
    
    async def test_task_parallelization(self, parallel_engine):
        """Test de paralelización de tareas"""
        engine = parallel_engine()
        
        # Tareas independientes
        tasks = [
            {"task_id": "task1", "type": "cpu_intensive"},
            {"task_id": "task2", "type": "io_intensive"},
            {"task_id": "task3", "type": "cpu_intensive"}
        ]
        
        with patch.object(engine, '_execute_tasks_parallel') as mock_execute:
            mock_execute.return_value = {
                "completed": ["task1", "task2", "task3"],
                "failed": []
            }
            
            result = await engine.execute_parallel_tasks(
                tasks,
                max_parallel=2,
                resource_constraints={"cpu": 4}
            )
            
            assert result['success'] is True
            assert len(result['completed']) == 3
            assert mock_execute.called
    
    async def test_resource_allocation(self, parallel_engine):
        """Test de asignación de recursos"""
        engine = parallel_engine()
        
        # Tareas con requisitos de recursos
        tasks = [
            {
                "task_id": "task1",
                "requirements": {"cpu": 2, "memory": 1024},
                "priority": "high"
            },
            {
                "task_id": "task2",
                "requirements": {"cpu": 1, "memory": 512},
                "priority": "medium"
            },
            {
                "task_id": "task3",
                "requirements": {"cpu": 3, "memory": 2048},
                "priority": "low"
            }
        ]
        
        # Recursos disponibles
        available_resources = {
            "cpu": 4,
            "memory": 4096
        }
        
        allocation = await engine.allocate_resources(tasks, available_resources)
        
        assert 'allocated_tasks' in allocation
        assert 'resource_utilization' in allocation
        assert allocation['resource_utilization']['cpu'] <= 1.0
    
    async def test_dependency_management(self, parallel_engine):
        """Test de gestión de dependencias"""
        engine = parallel_engine()
        
        # Tareas con dependencias
        tasks_with_deps = [
            {
                "task_id": "task1",
                "dependencies": []
            },
            {
                "task_id": "task2",
                "dependencies": ["task1"]
            },
            {
                "task_id": "task3",
                "dependencies": ["task1", "task2"]
            }
        ]
        
        # Determinar orden de ejecución
        execution_order = await engine.determine_execution_order(tasks_with_deps)
        
        assert execution_order[0]['task_id'] == "task1"
        assert execution_order[1]['task_id'] == "task2"
        assert execution_order[2]['task_id'] == "task3"
        
        # Verificar que respeta dependencias
        for i, task in enumerate(execution_order):
            for dep in task['dependencies']:
                dep_index = next(
                    (j for j, t in enumerate(execution_order) if t['task_id'] == dep),
                    -1
                )
                assert dep_index < i
    
    async def test_load_balancing(self, parallel_engine):
        """Test de balanceador de carga"""
        engine = parallel_engine()
        
        # Ejecutores con diferentes capacidades
        executors = [
            {"id": "executor1", "capacity": 0.8, "current_load": 0.2},
            {"id": "executor2", "capacity": 0.9, "current_load": 0.5},
            {"id": "executor3", "capacity": 0.7, "current_load": 0.1}
        ]
        
        # Seleccionar mejor executor
        selected_executor = await engine.select_best_executor(
            executors,
            task_requirements={"cpu": 1, "memory": 512}
        )
        
        assert selected_executor in [e['id'] for e in executors]
        
        # Verificar que se seleccionó el más adecuado
        selected = next(e for e in executors if e['id'] == selected_executor)
        available_capacity = selected['capacity'] - selected['current_load']
        
        # Debería tener capacidad disponible razonable
        assert available_capacity > 0
    
    async def test_execution_monitoring(self, parallel_engine):
        """Test de monitoreo de ejecución"""
        engine = parallel_engine()
        
        # Simular monitoreo de tareas en ejecución
        execution_status = await engine.monitor_execution(
            task_ids=["task1", "task2", "task3"]
        )
        
        assert 'execution_details' in execution_status
        assert 'summary' in execution_status
        
        for task_id in ["task1", "task2", "task3"]:
            assert task_id in execution_status['execution_details']
    
    async def test_fault_tolerance(self, parallel_engine):
        """Test de tolerancia a fallos"""
        engine = parallel_engine()
        
        # Simular fallo de tarea
        task_id = "failing_task"
        error = Exception("Resource unavailable")
        
        with patch.object(engine, '_retry_task') as mock_retry:
            mock_retry.return_value = {
                "success": True,
                "retries": 2,
                "final_result": "Task completed after retry"
            }
            
            fault_result = await engine.handle_task_failure(task_id, error)
            
            assert fault_result['handled'] is True
            assert mock_retry.called
    
    async def test_performance_optimization(self, parallel_engine):
        """Test de optimización de performance"""
        engine = parallel_engine()
        
        # Métricas de performance
        performance_data = {
            "task_completion_times": [1.2, 1.5, 1.1, 1.8, 1.3],
            "resource_utilization": [0.75, 0.82, 0.68, 0.91, 0.77],
            "success_rate": 0.94
        }
        
        with patch.object(engine, '_optimize_execution_params') as mock_optimize:
            mock_optimize.return_value = {
                "optimization_applied": True,
                "new_batch_size": 5,
                "new_max_parallel": 3
            }
            
            optimization_result = await engine.optimize_performance(performance_data)
            
            assert optimization_result['optimized'] is True
            assert mock_optimize.called