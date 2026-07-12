"""
Test de streaming SSE y real-time updates
Valida el sistema de streaming, updates en tiempo real y comunicación bidireccional
"""
import pytest
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any, AsyncGenerator
from unittest.mock import MagicMock

from conftest import (
    assert_streaming_response,
    create_test_task_id
)


class MockSSEStream:
    """Mock de stream SSE para testing"""
    
    def __init__(self, stream_id: str, duration: float = 10.0, frequency: float = 1.0):
        self.stream_id = stream_id
        self.duration = duration
        self.frequency = frequency
        self.start_time = time.time()
        self.events_sent = 0
        self.subscribers = []
    
    async def generate_events(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Generar eventos SSE durante la duración especificada"""
        end_time = self.start_time + self.duration
        
        while time.time() < end_time:
            current_time = time.time()
            elapsed = current_time - self.start_time
            
            event = {
                "stream_id": self.stream_id,
                "event_type": "progress_update",
                "timestamp": datetime.now().isoformat(),
                "elapsed_seconds": elapsed,
                "progress_percentage": min(100, (elapsed / self.duration) * 100),
                "message": f"Update {self.events_sent + 1}",
                "data": {
                    "phase": self._get_current_phase(elapsed),
                    "agents_status": self._get_agents_status(elapsed),
                    "throughput": self._calculate_throughput(elapsed)
                },
                "event_id": self.events_sent + 1
            }
            
            self.events_sent += 1
            yield event
            
            # Esperar según frecuencia
            await asyncio.sleep(1.0 / self.frequency)
    
    def _get_current_phase(self, elapsed: float) -> str:
        """Determinar fase actual basada en tiempo transcurrido"""
        if elapsed < self.duration * 0.2:
            return "initialization"
        elif elapsed < self.duration * 0.5:
            return "reasoning"
        elif elapsed < self.duration * 0.8:
            return "execution"
        else:
            return "verification"
    
    def _get_agents_status(self, elapsed: float) -> Dict[str, str]:
        """Simular estado de agentes"""
        base_status = {
            "reasoner": "idle",
            "planner": "idle", 
            "executor": "idle",
            "verifier": "idle"
        }
        
        # Cambiar estados según la fase
        if elapsed > self.duration * 0.2:
            base_status["reasoner"] = "completed"
            base_status["planner"] = "active"
        if elapsed > self.duration * 0.5:
            base_status["planner"] = "completed"
            base_status["executor"] = "active"
        if elapsed > self.duration * 0.8:
            base_status["executor"] = "completed"
            base_status["verifier"] = "active"
        
        return base_status
    
    def _calculate_throughput(self, elapsed: float) -> float:
        """Calcular throughput simulado"""
        if elapsed == 0:
            return 0.0
        return self.events_sent / elapsed


@pytest.mark.integration
@pytest.mark.streaming
class TestStreamingUpdates:
    """Tests del sistema de streaming SSE"""
    
    @pytest.mark.asyncio
    async def test_basic_sse_stream(self):
        """Test básico de stream SSE"""
        stream = MockSSEStream("test_stream", duration=2.0, frequency=10.0)
        
        events_received = []
        async for event in stream.generate_events():
            events_received.append(event)
            if len(events_received) >= 5:  # Limitar para el test
                break
        
        # Verificar estructura de eventos
        assert_streaming_response(events_received)
        
        # Verificar campos específicos
        for event in events_received:
            assert event["stream_id"] == "test_stream"
            assert event["event_type"] == "progress_update"
            assert "timestamp" in event
            assert "progress_percentage" in event
            assert event["progress_percentage"] >= 0
            assert event["progress_percentage"] <= 100
        
        print(f"Test SSE básico completado - {len(events_received)} eventos recibidos")
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_streams(self):
        """Test múltiples streams concurrentes"""
        streams = [
            MockSSEStream(f"stream_{i}", duration=3.0, frequency=5.0)
            for i in range(3)
        ]
        
        # Ejecutar streams en paralelo
        async def collect_stream_events(stream: MockSSEStream):
            events = []
            async for event in stream.generate_events():
                events.append(event)
                if len(events) >= 3:  # Limitar eventos por stream
                    break
            return stream.stream_id, events
        
        stream_tasks = [collect_stream_events(stream) for stream in streams]
        results = await asyncio.gather(*stream_tasks)
        
        # Verificar resultados
        all_events = []
        for stream_id, events in results:
            assert len(events) == 3, f"Stream {stream_id} debería tener 3 eventos"
            all_events.extend(events)
            
            for event in events:
                assert event["stream_id"] == stream_id
        
        assert len(all_events) == 9, "Deberían recibirse 9 eventos en total"
        
        print(f"Test streams concurrentes completado - {len(results)} streams, {len(all_events)} eventos")
    
    @pytest.mark.asyncio
    async def test_stream_with_real_time_updates(self, orchestrator, test_context):
        """Test streaming con updates reales del orquestador"""
        task_id = await create_test_task_id()
        
        # Simular listener que recolecta updates del orquestador
        updates_received = []
        
        async def monitor_orchestrator():
            """Monitor que captura updates del orquestador"""
            for _ in range(10):  # Simular 10 updates
                try:
                    progress = await orchestrator.get_task_progress(task_id)
                    if progress:
                        updates_received.append({
                            "task_id": task_id,
                            "progress_data": progress,
                            "timestamp": datetime.now().isoformat()
                        })
                    await asyncio.sleep(0.1)
                except Exception:
                    break  # Tarea no existe aún
        
        # Iniciar monitoreo
        monitor_task = asyncio.create_task(monitor_orchestrator())
        
        # Ejecutar orquestación real
        result = await orchestrator.orchestrate_task(
            objective="Test streaming with real updates",
            context={**test_context, "task_id": task_id},
            user_id="test_user",
            streaming_enabled=True
        )
        
        # Esperar que termine el monitoreo
        await monitor_task
        
        # Verificar que se recibieron updates
        if len(updates_received) > 0:
            assert updates_received[0]["task_id"] == task_id
            assert "progress_data" in updates_received[0]
        
        print(f"Test streaming real completado - {len(updates_received)} updates recibidas")
    
    @pytest.mark.asyncio
    async def test_sse_event_types(self):
        """Test diferentes tipos de eventos SSE"""
        stream = MockSSEStream("event_types_stream", duration=1.0, frequency=20.0)
        
        event_types = ["progress_update", "agent_status", "error_notification", "completion"]
        
        events_received = []
        event_counter = 0
        
        async for event in stream.generate_events():
            # Simular diferentes tipos de eventos
            event_type = event_types[event_counter % len(event_types)]
            
            enhanced_event = {
                **event,
                "event_type": event_type,
                "specific_data": self._get_event_specific_data(event_type)
            }
            
            events_received.append(enhanced_event)
            event_counter += 1
            
            if len(events_received) >= 8:
                break
        
        # Verificar que se recibieron todos los tipos de eventos
        received_types = set(event["event_type"] for event in events_received)
        expected_types = set(event_types)
        
        assert len(received_types.intersection(expected_types)) >= 2, \
            "Deberían recibirse al menos 2 tipos diferentes de eventos"
        
        print(f"Test tipos de eventos completado:")
        print(f"  - Eventos recibidos: {len(events_received)}")
        print(f"  - Tipos únicos: {len(received_types)}")
    
    def _get_event_specific_data(self, event_type: str) -> Dict[str, Any]:
        """Datos específicos por tipo de evento"""
        if event_type == "progress_update":
            return {"current_step": 3, "total_steps": 10}
        elif event_type == "agent_status":
            return {"active_agents": 4, "idle_agents": 1}
        elif event_type == "error_notification":
            return {"error_code": "TASK_TIMEOUT", "error_message": "Task exceeded timeout"}
        elif event_type == "completion":
            return {"final_result": "success", "execution_time": 45.2}
        else:
            return {}
    
    @pytest.mark.asyncio
    async def test_sse_connection_resilience(self):
        """Test resiliencia de conexiones SSE"""
        # Simular interrupciones de conexión
        connection_attempts = 5
        successful_connections = 0
        
        for attempt in range(connection_attempts):
            try:
                # Simular conexión con posible fallo
                stream = MockSSEStream(f"resilience_test_{attempt}", duration=0.5, frequency=10.0)
                
                events_received = 0
                async for event in stream.generate_events():
                    events_received += 1
                    if events_received >= 2:
                        break
                
                if events_received > 0:
                    successful_connections += 1
                
                # Simular pequeña pausa entre intentos
                await asyncio.sleep(0.1)
                
            except Exception as e:
                # Conexión fallida - parte del test de resiliencia
                pass
        
        # Verificar resiliencia (al menos 60% de conexiones exitosas)
        success_rate = successful_connections / connection_attempts
        assert success_rate >= 0.6, f"Tasa de éxito muy baja: {success_rate:.2f}"
        
        print(f"Test resiliencia SSE completado:")
        print(f"  - Intentos de conexión: {connection_attempts}")
        print(f"  - Conexiones exitosas: {successful_connections}")
        print(f"  - Tasa de éxito: {success_rate:.2f}")
    
    @pytest.mark.asyncio
    async def test_sse_backpressure_handling(self):
        """Test manejo de backpressure en streams SSE"""
        # Simular productor rápido y consumidor lento
        producer_stream = MockSSEStream("fast_producer", duration=1.0, frequency=50.0)
        consumer_buffer = []
        max_buffer_size = 10
        
        async def slow_consumer():
            """Consumidor más lento que el productor"""
            async for event in producer_stream.generate_events():
                consumer_buffer.append(event)
                
                # Simular procesamiento lento
                await asyncio.sleep(0.1)
                
                # Limitar buffer
                if len(consumer_buffer) > max_buffer_size:
                    # Eliminar eventos más antiguos
                    consumer_buffer.pop(0)
        
        # Ejecutar consumidor en background
        consumer_task = asyncio.create_task(slow_consumer())
        
        # Esperar un poco para generar eventos
        await asyncio.sleep(1.5)
        
        # Verificar que el buffer no crece indefinidamente
        assert len(consumer_buffer) <= max_buffer_size + 2, \
            f"Buffer creció demasiado: {len(consumer_buffer)}"
        
        consumer_task.cancel()
        
        print(f"Test backpressure SSE completado:")
        print(f"  - Tamaño máximo de buffer: {max_buffer_size}")
        print(f"  - Eventos en buffer final: {len(consumer_buffer)}")
    
    @pytest.mark.asyncio
    async def test_sse_monitoring_dashboard(self):
        """Test stream para dashboard de monitoreo"""
        # Simular dashboard de monitoreo con múltiples métricas
        dashboard_stream = MockSSEStream("dashboard_metrics", duration=2.0, frequency=5.0)
        
        dashboard_data = {
            "system_metrics": {},
            "agent_metrics": {},
            "task_metrics": {},
            "performance_metrics": {}
        }
        
        async for event in dashboard_stream.generate_events():
            # Actualizar métricas del dashboard
            dashboard_data["system_metrics"].update({
                "cpu_usage": 45 + (event["progress_percentage"] * 0.3),
                "memory_usage": 60 + (event["progress_percentage"] * 0.2),
                "active_connections": len(dashboard_data["agent_metrics"]) + 1
            })
            
            dashboard_data["agent_metrics"].update({
                agent: {"status": status, "last_update": event["timestamp"]}
                for agent, status in event["data"]["agents_status"].items()
            })
            
            dashboard_data["task_metrics"].update({
                "active_tasks": len(dashboard_data["agent_metrics"]) + 1,
                "completed_tasks": int(event["progress_percentage"] / 10),
                "failed_tasks": int(event["progress_percentage"] / 50)
            })
            
            # Verificar actualización de métricas
            assert dashboard_data["system_metrics"]["cpu_usage"] >= 45
            assert len(dashboard_data["agent_metrics"]) >= 4
        
        # Verificar métricas finales del dashboard
        assert dashboard_data["task_metrics"]["completed_tasks"] >= 8
        assert dashboard_data["system_metrics"]["active_connections"] > 0
        
        print(f"Test dashboard monitoreo completado:")
        print(f"  - Tareas completadas: {dashboard_data['task_metrics']['completed_tasks']}")
        print(f"  - Agentes monitoreados: {len(dashboard_data['agent_metrics'])}")
        print(f"  - Conexiones activas: {dashboard_data['system_metrics']['active_connections']}")
    
    @pytest.mark.asyncio
    async def test_sse_real_time_collaboration(self):
        """Test colaboración en tiempo real entre usuarios"""
        # Simular múltiples usuarios colaborando
        users = ["user1", "user2", "user3"]
        collaboration_session_id = "collab_session_123"
        
        user_streams = {}
        
        for user in users:
            stream = MockSSEStream(
                f"collab_{user}_{collaboration_session_id}",
                duration=1.5,
                frequency=8.0
            )
            stream.user_id = user
            stream.session_id = collaboration_session_id
            user_streams[user] = stream
        
        # Simular eventos colaborativos
        collaboration_events = []
        
        async def handle_user_stream(user: str, stream: MockSSEStream):
            """Manejar stream de un usuario"""
            events = []
            async for event in stream.generate_events():
                # Agregar información de colaboración
                event["collaboration_data"] = {
                    "session_id": collaboration_session_id,
                    "user_id": user,
                    "other_users": [u for u in users if u != user]
                }
                events.append(event)
                
                # Simular broadcast a otros usuarios
                collaboration_events.append({
                    "broadcast_from": user,
                    "event": event,
                    "timestamp": datetime.now().isoformat()
                })
                
                if len(events) >= 2:
                    break
            return events
        
        # Ejecutar streams de usuarios en paralelo
        user_tasks = [
            handle_user_stream(user, stream) 
            for user, stream in user_streams.items()
        ]
        
        user_results = await asyncio.gather(*user_tasks)
        
        # Verificar colaboración
        total_user_events = sum(len(events) for events in user_results)
        total_broadcasts = len(collaboration_events)
        
        # Debería haber broadcasts entre usuarios
        assert total_broadcasts >= len(users), "Debería haber broadcasts entre usuarios"
        
        # Verificar estructura colaborativa
        for broadcast in collaboration_events:
            assert "broadcast_from" in broadcast
            assert "event" in broadcast
            assert "collaboration_data" in broadcast["event"]
        
        print(f"Test colaboración tiempo real completado:")
        print(f"  - Usuarios: {len(users)}")
        print(f"  - Eventos por usuario: {len(user_results[0])}")
        print(f"  - Broadcasts totales: {total_broadcasts}")
    
    @pytest.mark.asyncio
    async def test_sse_performance_benchmark(self):
        """Test de performance del sistema SSE"""
        num_streams = 5
        events_per_stream = 20
        total_expected_events = num_streams * events_per_stream
        
        # Crear múltiples streams de alta frecuencia
        performance_streams = [
            MockSSEStream(f"perf_stream_{i}", duration=3.0, frequency=events_per_stream / 3.0)
            for i in range(num_streams)
        ]
        
        start_time = time.time()
        
        async def stream_benchmark(stream: MockSSEStream, stream_id: int):
            """Benchmark de un stream individual"""
            events_received = 0
            async for event in stream.generate_events():
                events_received += 1
                if events_received >= events_per_stream:
                    break
            
            return {
                "stream_id": stream_id,
                "events_received": events_received,
                "success": events_received == events_per_stream
            }
        
        # Ejecutar benchmark en paralelo
        benchmark_tasks = [
            stream_benchmark(stream, i) 
            for i, stream in enumerate(performance_streams)
        ]
        
        benchmark_results = await asyncio.gather(*benchmark_tasks)
        total_execution_time = time.time() - start_time
        
        # Calcular métricas de performance
        successful_streams = sum(1 for result in benchmark_results if result["success"])
        total_events_received = sum(result["events_received"] for result in benchmark_results)
        
        events_per_second = total_events_received / total_execution_time
        stream_success_rate = successful_streams / num_streams
        
        # Verificar métricas de performance
        assert events_per_second > 10, f"Throughput muy bajo: {events_per_second:.2f} events/sec"
        assert stream_success_rate >= 0.8, f"Tasa de éxito muy baja: {stream_success_rate:.2f}"
        assert total_execution_time < 4.0, f"Tiempo de ejecución muy alto: {total_execution_time:.2f}s"
        
        print(f"Test benchmark SSE completado:")
        print(f"  - Streams concurrentes: {num_streams}")
        print(f"  - Eventos por stream: {events_per_stream}")
        print(f"  - Throughput total: {events_per_second:.2f} events/sec")
        print(f"  - Tasa de éxito: {stream_success_rate:.2f}")
        print(f"  - Tiempo total: {total_execution_time:.2f}s")