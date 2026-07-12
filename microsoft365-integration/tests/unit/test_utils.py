"""
Tests unitarios para utilidades del sistema Microsoft 365.
"""
import asyncio
import pytest
import redis
import time
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Dict, Any

from src.utils.retry_handler import RetryHandler, CircuitBreaker, retry_with_backoff
from src.utils.rate_limiter import RateLimiter
from src.utils.sync_manager import SyncManager
from src.utils.license_manager import LicenseManager
from src.utils.notification_handler import NotificationHandler
from src.utils.logger import setup_logger


@pytest.mark.unit
@pytest.mark.utils
class TestRetryHandler:
    """Tests para el manejador de reintentos."""

    @pytest.fixture
    def retry_handler(self):
        """Fixture para crear instancia de RetryHandler."""
        return RetryHandler(
            max_attempts=3,
            backoff_factor=2.0,
            max_delay=30.0
        )

    @pytest.mark.asyncio
    async def test_retry_success_on_first_attempt(self, retry_handler):
        """Test éxito en el primer intento."""
        async def successful_func():
            return "success"
        
        result = await retry_handler.execute(successful_func)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self, retry_handler):
        """Test éxito después de algunos fallos."""
        call_count = 0
        
        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = await retry_handler.execute(flaky_func)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_max_attempts_exceeded(self, retry_handler):
        """Test cuando se excede el número máximo de intentos."""
        async def always_failing_func():
            raise Exception("Always failing")
        
        with pytest.raises(Exception) as exc_info:
            await retry_handler.execute(always_failing_func)
        
        assert "Always failing" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_custom_retry_config(self):
        """Test configuración personalizada de reintentos."""
        custom_handler = RetryHandler(
            max_attempts=5,
            backoff_factor=1.5,
            max_delay=10.0
        )
        
        assert custom_handler.max_attempts == 5
        assert custom_handler.backoff_factor == 1.5
        assert custom_handler.max_delay == 10.0

    @pytest.mark.asyncio
    async def test_exponential_backoff_calculation(self, retry_handler):
        """Test cálculo de backoff exponencial."""
        # Simular diferentes números de intento
        delays = []
        for attempt in range(1, 4):
            delay = retry_handler._calculate_delay(attempt)
            delays.append(delay)
        
        # Los delays deberían aumentar exponencialmente
        assert delays[1] > delays[0]
        assert delays[2] > delays[1]

    @pytest.mark.asyncio
    async def test_retry_with_custom_exception_types(self):
        """Test reintento con tipos de excepción personalizados."""
        retry_handler = RetryHandler(
            max_attempts=3,
            retryable_exceptions=(ValueError,)
        )
        
        async def raises_retryable():
            raise ValueError("Retryable error")
        
        async def raises_non_retryable():
            raise RuntimeError("Non-retryable error")
        
        # Debería reintentar para ValueError
        with pytest.raises(ValueError):
            await retry_handler.execute(raises_retryable)
        
        # No debería reintentar para RuntimeError
        with pytest.raises(RuntimeError):
            await retry_handler.execute(raises_non_retryable)

    @pytest.mark.asyncio
    async def test_jitter_in_backoff(self):
        """Test que el backoff incluye jitter."""
        handler = RetryHandler(max_attempts=3, add_jitter=True)
        
        delays = []
        for _ in range(10):
            delay = handler._calculate_delay(1)
            delays.append(delay)
        
        # Los delays deberían tener cierta variabilidad
        assert len(set(delays)) > 1


@pytest.mark.unit
@pytest.mark.utils
class TestCircuitBreaker:
    """Tests para el circuit breaker."""

    @pytest.fixture
    def circuit_breaker(self):
        """Fixture para crear instancia de CircuitBreaker."""
        return CircuitBreaker(
            failure_threshold=3,
            timeout=10.0
        )

    @pytest.mark.asyncio
    async def test_circuit_breaker_normal_operation(self, circuit_breaker):
        """Test operación normal del circuit breaker."""
        async def normal_func():
            return "success"
        
        result = await circuit_breaker.call(normal_func)
        assert result == "success"
        assert circuit_breaker.state == "closed"

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self, circuit_breaker):
        """Test que el circuit breaker se abre después de fallos."""
        async def failing_func():
            raise Exception("Failure")
        
        # Simular varios fallos
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        assert circuit_breaker.state == "open"
        
        # Debería fallar inmediatamente sin ejecutar la función
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_func)

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_after_timeout(self, circuit_breaker):
        """Test que el circuit breaker pasa a half-open después del timeout."""
        async def failing_func():
            raise Exception("Failure")
        
        # Abrir el circuit breaker
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        assert circuit_breaker.state == "open"
        
        # Esperar el timeout (simulado)
        circuit_breaker.last_failure_time = time.time() - 11
        circuit_breaker._update_state()
        
        assert circuit_breaker.state == "half_open"

    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_on_success(self, circuit_breaker):
        """Test que el circuit breaker se cierra después de éxito."""
        circuit_breaker.state = "half_open"
        
        async def success_func():
            return "success"
        
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state == "closed"

    @pytest.mark.asyncio
    async def test_circuit_breaker_metrics(self, circuit_breaker):
        """Test métricas del circuit breaker."""
        async def normal_func():
            return "success"
        
        await circuit_breaker.call(normal_func)
        assert circuit_breaker.success_count == 1
        
        circuit_breaker.failure_count = 2
        assert circuit_breaker.failure_count == 2


@pytest.mark.unit
@pytest.mark.utils
class TestRateLimiter:
    """Tests para el rate limiter."""

    @pytest.fixture
    def rate_limiter(self, mock_redis):
        """Fixture para crear instancia de RateLimiter."""
        with patch('redis.Redis', return_value=mock_redis):
            return RateLimiter(
                requests_per_minute=60,
                requests_per_hour=1000
            )

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests_within_limit(self, rate_limiter, mock_redis):
        """Test que permite solicitudes dentro del límite."""
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.incr.return_value = 1
        
        # Debería permitir 5 solicitudes
        for i in range(5):
            result = await rate_limiter.acquire()
            assert result is True

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_requests_over_limit(self, rate_limiter, mock_redis):
        """Test que bloquea solicitudes sobre el límite."""
        mock_redis.get.return_value = "100"  # Ya alcanzó el límite por minuto
        
        result = await rate_limiter.acquire()
        assert result is False

    @pytest.mark.asyncio
    async def test_rate_limiter_respects_different_limits(self, rate_limiter, mock_redis):
        """Test que respeta diferentes límites de tiempo."""
        # Límite por hora debería ser más permisivo
        mock_redis.get.side_effect = lambda key: "100" if "minute" in key else None
        mock_redis.incr.return_value = 50
        
        result = await rate_limiter.acquire()
        assert result is True

    @pytest.mark.asyncio
    async def test_rate_limiter_distributed_mode(self):
        """Test modo distribuido del rate limiter."""
        mock_redis = Mock()
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.incr.return_value = 1
        
        with patch('redis.Redis', return_value=mock_redis):
            distributed_limiter = RateLimiter(
                requests_per_minute=100,
                distributed=True,
                redis_key_prefix="distributed_test"
            )
            
            result = await distributed_limiter.acquire()
            assert result is True

    @pytest.mark.asyncio
    async def test_rate_limiter_release_tokens(self, rate_limiter, mock_redis):
        """Test liberación de tokens."""
        mock_redis.incr.return_value = 1
        mock_redis.decr.return_value = 1
        
        await rate_limiter.release()
        
        # Verificar que se llamó a decrement
        mock_redis.decr.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limiter_bucket_algorithm(self, rate_limiter, mock_redis):
        """Test algoritmo de bucket de tokens."""
        # Simular bucket con tokens disponibles
        mock_redis.get.return_value = str(rate_limiter.capacity - 1)
        mock_redis.incr.return_value = rate_limiter.capacity
        
        result = await rate_limiter.acquire()
        assert result is True

    @pytest.mark.asyncio
    async def test_rate_limiter_custom_limits(self):
        """Test límites personalizados."""
        custom_limiter = RateLimiter(
            requests_per_minute=30,
            requests_per_hour=500
        )
        
        assert custom_limiter.requests_per_minute == 30
        assert custom_limiter.requests_per_hour == 500


@pytest.mark.unit
@pytest.mark.utils
class TestSyncManager:
    """Tests para el gestor de sincronización."""

    @pytest.fixture
    def sync_manager(self):
        """Fixture para crear instancia de SyncManager."""
        return SyncManager(
            sync_interval=300,  # 5 minutos
            max_changes_per_sync=1000
        )

    @pytest.mark.asyncio
    async def test_delta_sync_initial(self, sync_manager):
        """Test sincronización delta inicial."""
        resource_type = "documents"
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "value": [
                {"id": "doc1", "name": "Document 1"},
                {"id": "doc2", "name": "Document 2"}
            ],
            "@odata.deltaLink": "https://example.com/delta(token='next')"
        }
        
        result = await sync_manager.delta_sync(
            resource_type=resource_type,
            client=mock_client
        )
        
        assert len(result["changes"]) == 2
        assert result["next_delta_token"] == "next"
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_delta_sync_with_existing_token(self, sync_manager):
        """Test sincronización delta con token existente."""
        resource_type = "documents"
        delta_token = "existing-token"
        
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "value": [
                {"id": "doc3", "name": "Document 3", "@changeType": "updated"}
            ],
            "@odata.deltaLink": "https://example.com/delta(token='new')"
        }
        
        result = await sync_manager.delta_sync(
            resource_type=resource_type,
            client=mock_client,
            delta_token=delta_token
        )
        
        assert len(result["changes"]) == 1
        assert result["changes"][0]["@changeType"] == "updated"
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_conflict_detection(self, sync_manager):
        """Test detección de conflictos."""
        local_changes = {
            "doc1": {
                "name": "Local Updated Name",
                "modified": "2024-01-01T12:00:00Z"
            }
        }
        
        remote_changes = {
            "doc1": {
                "name": "Remote Updated Name", 
                "modified": "2024-01-01T11:00:00Z"
            }
        }
        
        conflicts = await sync_manager.detect_conflicts(local_changes, remote_changes)
        
        assert "doc1" in conflicts
        assert conflicts["doc1"]["type"] == "concurrent_update"

    @pytest.mark.asyncio
    async def test_conflict_resolution_latest_wins(self, sync_manager):
        """Test resolución de conflictos con estrategia 'latest_wins'."""
        conflict = {
            "local": {"name": "Local", "modified": "2024-01-01T12:00:00Z"},
            "remote": {"name": "Remote", "modified": "2024-01-01T13:00:00Z"}
        }
        
        resolution = await sync_manager.resolve_conflict(
            conflict=conflict,
            strategy="latest_wins"
        )
        
        assert resolution["chosen"] == "remote"
        assert resolution["resolved_item"]["name"] == "Remote"

    @pytest.mark.asyncio
    async def test_conflict_resolution_manual(self, sync_manager):
        """Test resolución manual de conflictos."""
        conflict = {
            "local": {"name": "Local"},
            "remote": {"name": "Remote"}
        }
        
        manual_resolution = {"name": "Merged Name"}
        
        resolution = await sync_manager.resolve_conflict(
            conflict=conflict,
            strategy="manual",
            manual_resolution=manual_resolution
        )
        
        assert resolution["chosen"] == "manual"
        assert resolution["resolved_item"]["name"] == "Merged Name"

    @pytest.mark.asyncio
    async def test_batch_sync_operations(self, sync_manager):
        """Test operaciones de sincronización en lote."""
        resources = ["documents", "calendars", "contacts"]
        
        for resource in resources:
            await sync_manager.start_sync(resource)
        
        assert len(sync_manager.active_syncs) == 3
        assert all(resource in sync_manager.active_syncs for resource in resources)

    @pytest.mark.asyncio
    async def test_offline_queue_management(self, sync_manager):
        """Test manejo de cola offline."""
        # Agregar cambios offline
        offline_change = {
            "resource_type": "documents",
            "operation": "create",
            "data": {"name": "Offline Document"}
        }
        
        await sync_manager.add_offline_change(offline_change)
        
        assert len(sync_manager.offline_queue) == 1
        
        # Procesar cola offline
        mock_client = AsyncMock()
        mock_client.post.return_value = {"id": "new-doc-id"}
        
        results = await sync_manager.process_offline_queue(mock_client)
        
        assert len(results) == 1
        assert results[0]["operation"] == "create"

    @pytest.mark.asyncio
    async def test_sync_statistics(self, sync_manager):
        """Test estadísticas de sincronización."""
        sync_manager.total_syncs = 10
        sync_manager.successful_syncs = 8
        sync_manager.failed_syncs = 2
        sync_manager.total_changes_processed = 150
        
        stats = await sync_manager.get_sync_statistics()
        
        assert stats["total_syncs"] == 10
        assert stats["success_rate"] == 0.8
        assert stats["average_changes_per_sync"] == 15


@pytest.mark.unit
@pytest.mark.utils
class TestLicenseManager:
    """Tests para el gestor de licencias."""

    @pytest.fixture
    def license_manager(self):
        """Fixture para crear instancia de LicenseManager."""
        return LicenseManager(
            skus_to_monitor=[
                "Microsoft 365 Business Standard",
                "Office 365 E3",
                "Power Platform"
            ]
        )

    @pytest.mark.asyncio
    async def test_license_validation_valid(self, license_manager):
        """Test validación de licencia válida."""
        user_license = {
            "skuId": "12345",
            "skuPartNumber": "Microsoft 365 Business Standard",
            "consumedUnits": 1,
            "prepaidUnits": {"enabled": 100, "suspended": 0},
            "state": "Enabled"
        }
        
        result = await license_manager.validate_license(user_license)
        
        assert result["valid"] is True
        assert result["available_units"] == 100
        assert result["consumed_units"] == 1

    @pytest.mark.asyncio
    async def test_license_validation_expired(self, license_manager):
        """Test validación de licencia expirada."""
        expired_license = {
            "skuPartNumber": "Microsoft 365 Business Standard",
            "consumedUnits": 1,
            "prepaidUnits": {"enabled": 0, "suspended": 0},
            "state": "Suspended"
        }
        
        result = await license_manager.validate_license(expired_license)
        
        assert result["valid"] is False
        assert result["reason"] == "expired_or_suspended"

    @pytest.mark.asyncio
    async def test_license_usage_tracking(self, license_manager):
        """Test seguimiento de uso de licencias."""
        usage_data = {
            "date": "2024-01-15",
            "license_type": "Microsoft 365 Business Standard",
            "active_users": 45,
            "peak_concurrent": 38
        }
        
        await license_manager.track_usage(usage_data)
        
        assert license_manager.usage_data[-1]["date"] == "2024-01-15"
        assert license_manager.usage_data[-1]["active_users"] == 45

    @pytest.mark.asyncio
    async def test_license_compliance_check(self, license_manager):
        """Test verificación de cumplimiento de licencias."""
        user_licenses = [
            {"user_id": "user1", "licenses": ["Microsoft 365 Business Standard"]},
            {"user_id": "user2", "licenses": []},  # Usuario sin licencia
            {"user_id": "user3", "licenses": ["Office 365 E3"]}
        ]
        
        compliance_report = await license_manager.check_compliance(user_licenses)
        
        assert len(compliance_report["non_compliant_users"]) == 1
        assert "user2" in compliance_report["non_compliant_users"]

    @pytest.mark.asyncio
    async def test_license_recommendations(self, license_manager):
        """Test recomendaciones de licencias."""
        usage_history = [
            {"date": "2024-01-01", "active_users": 30},
            {"date": "2024-01-15", "active_users": 55},
            {"date": "2024-01-30", "active_users": 70}
        ]
        
        for usage in usage_history:
            await license_manager.track_usage(usage)
        
        recommendations = await license_manager.generate_recommendations()
        
        assert recommendations["suggested_additional_licenses"] > 0
        assert "growth_trend" in recommendations

    @pytest.mark.asyncio
    async def test_license_cost_optimization(self, license_manager):
        """Test optimización de costos de licencias."""
        current_licenses = [
            {"type": "Microsoft 365 Business Standard", "count": 50},
            {"type": "Office 365 E3", "count": 20}
        ]
        
        usage_data = [
            {"active_users": 45, "license_type": "Microsoft 365 Business Standard"},
            {"active_users": 5, "license_type": "Office 365 E3"}
        ]
        
        for usage in usage_data:
            await license_manager.track_usage(usage)
        
        optimization_plan = await license_manager.optimize_costs(current_licenses)
        
        assert optimization_plan["total_potential_savings"] > 0
        assert len(optimization_plan["recommendations"]) > 0


@pytest.mark.unit
@pytest.mark.utils
class TestNotificationHandler:
    """Tests para el manejador de notificaciones."""

    @pytest.fixture
    def notification_handler(self):
        """Fixture para crear instancia de NotificationHandler."""
        return NotificationHandler(
            webhook_secret="test-secret"
        )

    @pytest.mark.asyncio
    async def test_webhook_subscription_creation(self, notification_handler):
        """Test creación de suscripción webhook."""
        subscription_data = {
            "resource": "/me/drive/root",
            "change_type": "created,updated,deleted",
            "notification_url": "https://example.com/webhook",
            "expiration_date_time": "2024-02-01T00:00:00Z"
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "id": "subscription-123",
            "resource": subscription_data["resource"],
            "expirationDateTime": subscription_data["expiration_date_time"]
        }
        
        result = await notification_handler.create_subscription(
            client=mock_client,
            **subscription_data
        )
        
        assert result["id"] == "subscription-123"
        assert result["resource"] == subscription_data["resource"]
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_webhook_validation(self, notification_handler):
        """Test validación de webhook."""
        # Mock request con token de validación
        mock_request = Mock()
        mock_request.query_params = {
            "validationToken": "validation-token-123"
        }
        
        response = await notification_handler.validate_webhook(mock_request)
        
        assert response.status_code == 200
        assert response.body == "validation-token-123"

    @pytest.mark.asyncio
    async def test_notification_processing(self, notification_handler):
        """Test procesamiento de notificaciones."""
        notification_data = {
            "value": [
                {
                    "change_type": "created",
                    "resource": "/me/drive/root/files/document.docx",
                    "resource_data": {
                        "id": "file-123",
                        "name": "document.docx"
                    }
                }
            ]
        }
        
        mock_request = Mock()
        mock_request.json.return_value = notification_data
        
        processed_notifications = await notification_handler.process_notifications(
            mock_request
        )
        
        assert len(processed_notifications) == 1
        assert processed_notifications[0]["change_type"] == "created"
        assert processed_notifications[0]["resource"] == "/me/drive/root/files/document.docx"

    @pytest.mark.asyncio
    async def test_notification_filtering(self, notification_handler):
        """Test filtrado de notificaciones."""
        notification_handler.filter_config = {
            "include_resources": ["/me/drive/root"],
            "exclude_types": ["deleted"]
        }
        
        incoming_notifications = [
            {
                "change_type": "created",
                "resource": "/me/drive/root/files/document.docx"
            },
            {
                "change_type": "deleted",
                "resource": "/me/drive/root/files/old.txt"
            },
            {
                "change_type": "updated",
                "resource": "/me/messages/message-123"
            }
        ]
        
        filtered = await notification_handler.filter_notifications(
            incoming_notifications
        )
        
        # Solo debería incluir notificaciones que cumplan los criterios
        assert len(filtered) == 1
        assert filtered[0]["change_type"] == "created"

    @pytest.mark.asyncio
    async def test_notification_delivery(self, notification_handler):
        """Test entrega de notificaciones."""
        notifications = [
            {
                "change_type": "created",
                "resource": "/me/drive/root/files/new.docx",
                "timestamp": "2024-01-15T10:00:00Z"
            }
        ]
        
        delivery_targets = [
            "https://api.company.com/notifications",
            "https://webhook.site/notifications"
        ]
        
        mock_client = AsyncMock()
        mock_client.post.return_value = {"status": "delivered"}
        
        results = await notification_handler.deliver_notifications(
            client=mock_client,
            notifications=notifications,
            delivery_targets=delivery_targets
        )
        
        assert len(results) == len(delivery_targets)
        assert all(result["status"] == "delivered" for result in results)

    @pytest.mark.asyncio
    async def test_notification_retry_mechanism(self, notification_handler):
        """Test mecanismo de reintento para notificaciones."""
        notifications = [
            {
                "change_type": "created",
                "resource": "/me/drive/root/files/test.docx"
            }
        ]
        
        mock_client = AsyncMock()
        # Primera entrega falla, segunda tiene éxito
        mock_client.post.side_effect = [
            Exception("Delivery failed"),
            {"status": "delivered"}
        ]
        
        delivery_targets = ["https://example.com/webhook"]
        
        results = await notification_handler.deliver_notifications_with_retry(
            client=mock_client,
            notifications=notifications,
            delivery_targets=delivery_targets,
            max_retries=3
        )
        
        assert results[0]["status"] == "delivered"
        assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_notification_queue_management(self, notification_handler):
        """Test manejo de cola de notificaciones."""
        # Agregar notificaciones a la cola
        for i in range(10):
            await notification_handler.queue_notification({
                "id": f"notification-{i}",
                "change_type": "created",
                "resource": f"/me/files/file-{i}.docx"
            })
        
        assert len(notification_handler.notification_queue) == 10
        
        # Procesar cola
        mock_client = AsyncMock()
        mock_client.post.return_value = {"status": "processed"}
        
        processed_count = await notification_handler.process_queued_notifications(
            client=mock_client
        )
        
        assert processed_count == 10
        assert len(notification_handler.notification_queue) == 0


@pytest.mark.unit
@pytest.mark.utils
class TestLogger:
    """Tests para el sistema de logging."""

    @pytest.mark.asyncio
    async def test_logger_setup(self, tmp_path):
        """Test configuración del logger."""
        log_file = tmp_path / "test.log"
        
        logger = setup_logger(
            name="test_logger",
            log_file=str(log_file),
            level="INFO"
        )
        
        assert logger.name == "test_logger"
        assert logger.level == 20  # INFO level
        
        logger.info("Test log message")
        
        # Verificar que se escribió al archivo
        assert log_file.exists()

    @pytest.mark.asyncio
    async def test_structured_logging(self, tmp_path):
        """Test logging estructurado."""
        log_file = tmp_path / "structured.log"
        
        logger = setup_logger(
            name="structured_logger",
            log_file=str(log_file),
            structured=True
        )
        
        test_data = {
            "user_id": "user123",
            "action": "document_upload",
            "file_size": 1024
        }
        
        logger.info("Document uploaded", extra=test_data)
        
        # Verificar que el log está en formato JSON
        with open(log_file, 'r') as f:
            log_content = f.read()
            
        assert '"user_id": "user123"' in log_content
        assert '"action": "document_upload"' in log_content

    @pytest.mark.asyncio
    async def test_log_rotation(self, tmp_path):
        """Test rotación de logs."""
        logger = setup_logger(
            name="rotation_logger",
            log_file=str(tmp_path / "rotating.log"),
            max_bytes=100,  # Rotación frecuente
            backup_count=3
        )
        
        # Escribir múltiples mensajes para forzar rotación
        for i in range(10):
            logger.info("Test message " * 10)
        
        # Verificar que se crearon archivos de respaldo
        log_files = list(tmp_path.glob("rotating.log*"))
        assert len(log_files) >= 2  # log original + al menos 1 backup


@pytest.mark.unit
@pytest.mark.utils
class TestUtilityIntegration:
    """Tests de integración entre utilidades."""

    @pytest.mark.asyncio
    async def test_retry_with_rate_limiter(self, mock_redis):
        """Test integración de retry con rate limiter."""
        # Configurar rate limiter
        with patch('redis.Redis', return_value=mock_redis):
            rate_limiter = RateLimiter(requests_per_minute=60)
            retry_handler = RetryHandler(max_attempts=3)
            
            # Simular función que puede fallar por rate limiting
            call_count = 0
            async def rate_limited_function():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise Exception("Rate limited")
                return "success"
            
            # Ejecutar con reintentos
            result = await retry_handler.execute(rate_limited_function)
            assert result == "success"

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_rate_limiter(self, mock_redis):
        """Test integración de circuit breaker con rate limiter."""
        with patch('redis.Redis', return_value=mock_redis):
            rate_limiter = RateLimiter(requests_per_minute=60)
            circuit_breaker = CircuitBreaker(failure_threshold=2, timeout=5.0)
            
            # Simular función que siempre falla
            async def failing_function():
                raise Exception("Always failing")
            
            # El circuit breaker debería abrirse después de 2 fallos
            for _ in range(3):
                with pytest.raises(Exception):
                    await circuit_breaker.call(failing_function)
            
            assert circuit_breaker.state == "open"

    @pytest.mark.asyncio
    async def test_sync_manager_with_retry(self, mock_redis):
        """Test integración de SyncManager con retry."""
        retry_handler = RetryHandler(max_attempts=3)
        sync_manager = SyncManager(max_changes_per_sync=100)
        
        # Simular cliente que falla ocasionalmente
        mock_client = AsyncMock()
        mock_client.get.side_effect = [
            Exception("Temporary failure"),
            {
                "value": [{"id": "doc1", "name": "Document 1"}],
                "@odata.deltaLink": "token123"
            }
        ]
        
        result = await sync_manager.delta_sync(
            resource_type="documents",
            client=mock_client,
            retry_handler=retry_handler
        )
        
        assert len(result["changes"]) == 1
        assert mock_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_notification_with_retry_and_rate_limiter(self, mock_redis):
        """Test integración completa de notificaciones."""
        with patch('redis.Redis', return_value=mock_redis):
            rate_limiter = RateLimiter(requests_per_minute=60)
            retry_handler = RetryHandler(max_attempts=3)
            notification_handler = NotificationHandler()
            
            notifications = [
                {"change_type": "created", "resource": "/me/files/test.docx"}
            ]
            
            mock_client = AsyncMock()
            mock_client.post.side_effect = [
                Exception("Network error"),
                {"status": "delivered"}
            ]
            
            # La entrega debería tener éxito con reintentos
            results = await notification_handler.deliver_notifications_with_retry(
                client=mock_client,
                notifications=notifications,
                delivery_targets=["https://example.com/webhook"],
                retry_handler=retry_handler,
                rate_limiter=rate_limiter
            )
            
            assert results[0]["status"] == "delivered"