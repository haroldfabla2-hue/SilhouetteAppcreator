"""
Tests de integración para Graph API Client.
"""
import asyncio
import pytest
import aiohttp
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Dict, Any

from src.graph.client import GraphAPIClient
from src.auth.azure_ad import AzureADAuthenticator
from src.utils.retry_handler import RetryHandler
from src.utils.rate_limiter import RateLimiter


@pytest.mark.integration
@pytest.mark.graph_api
class TestGraphAPIClientIntegration:
    """Tests de integración para GraphAPIClient."""

    @pytest.fixture
    async def graph_client_integration(self, mock_settings, mock_authenticator, mock_redis):
        """Fixture para crear instancia de GraphAPIClient para integración."""
        with patch('redis.Redis', return_value=mock_redis):
            client = GraphAPIClient(
                authenticator=mock_authenticator,
                settings=mock_settings,
                retry_handler=RetryHandler(max_attempts=3),
                rate_limiter=RateLimiter(requests_per_minute=100)
            )
            return client

    @pytest.mark.asyncio
    async def test_authenticated_request_success(self, graph_client_integration, mock_access_token):
        """Test solicitud autenticada exitosa."""
        # Mock autenticación exitosa
        graph_client_integration.authenticator.get_access_token.return_value = mock_access_token
        
        # Mock respuesta de Graph API
        expected_response = {
            "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#users",
            "value": [
                {
                    "id": "user-123",
                    "displayName": "Test User",
                    "mail": "test@example.com"
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = expected_response
            mock_response.headers = {"Content-Type": "application/json"}
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await graph_client_integration.get("/users")
            
            assert result == expected_response
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_token_refresh_on_unauthorized(self, graph_client_integration):
        """Test renovación de token en respuesta 401."""
        # Mock token inicial inválido y token renovado
        graph_client_integration.authenticator.get_access_token.side_effect = [
            "invalid-token",
            "new-valid-token"
        ]
        
        # Mock respuestas: primero 401, luego éxito
        with patch('aiohttp.ClientSession.get') as mock_get:
            responses = [
                AsyncMock(status=401, json=lambda: {"error": "Invalid token"}),
                AsyncMock(
                    status=200,
                    json=lambda: {"value": [{"id": "user-123"}]},
                    headers={"Content-Type": "application/json"}
                )
            ]
            mock_get.return_value.__aenter__.side_effect = responses
            
            result = await graph_client_integration.get("/users")
            
            assert "value" in result
            assert len(graph_client_integration.authenticator.get_access_token.call_args_list) == 2

    @pytest.mark.asyncio
    async def test_rate_limiting_handling(self, graph_client_integration):
        """Test manejo de rate limiting (código 429)."""
        graph_client_integration.authenticator.get_access_token.return_value = "valid-token"
        
        # Mock respuestas: 429 (rate limited) luego 200 (éxito)
        with patch('aiohttp.ClientSession.get') as mock_get:
            responses = [
                AsyncMock(
                    status=429,
                    json=lambda: {
                        "error": {
                            "code": "TooManyRequests",
                            "message": "Rate limit exceeded"
                        }
                    },
                    headers={"Retry-After": "1"}
                ),
                AsyncMock(
                    status=200,
                    json=lambda: {"value": [{"id": "user-123"}]},
                    headers={"Content-Type": "application/json"}
                )
            ]
            mock_get.return_value.__aenter__.side_effect = responses
            
            # Debería reintentar automáticamente
            result = await graph_client_integration.get("/users")
            
            assert "value" in result
            assert len(responses) == 2

    @pytest.mark.asyncio
    async def test_batch_request_success(self, graph_client_integration):
        """Test solicitud en lote exitosa."""
        graph_client_integration.authenticator.get_access_token.return_value = "valid-token"
        
        batch_requests = [
            {
                "id": "1",
                "method": "GET",
                "url": "/users/user-1"
            },
            {
                "id": "2", 
                "method": "GET",
                "url": "/users/user-2"
            }
        ]
        
        expected_batch_response = {
            "responses": [
                {
                    "id": "1",
                    "status": 200,
                    "body": {"id": "user-1", "displayName": "User 1"}
                },
                {
                    "id": "2",
                    "status": 200,
                    "body": {"id": "user-2", "displayName": "User 2"}
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = expected_batch_response
            mock_response.headers = {"Content-Type": "application/json"}
            mock_post.return_value.__aenter__.return_value = mock_response
            
            results = await graph_client_integration.batch_request(batch_requests)
            
            assert len(results) == 2
            assert results[0]["id"] == "1"
            assert results[1]["id"] == "2"

    @pytest.mark.asyncio
    async def test_batch_request_partial_failure(self, graph_client_integration):
        """Test solicitud en lote con fallos parciales."""
        graph_client_integration.authenticator.get_access_token.return_value = "valid-token"
        
        batch_requests = [
            {
                "id": "1",
                "method": "GET",
                "url": "/users/valid-user"
            },
            {
                "id": "2",
                "method": "GET", 
                "url": "/users/invalid-user"
            },
            {
                "id": "3",
                "method": "GET",
                "url": "/users/another-valid-user"
            }
        ]
        
        expected_batch_response = {
            "responses": [
                {
                    "id": "1",
                    "status": 200,
                    "body": {"id": "valid-user", "displayName": "Valid User"}
                },
                {
                    "id": "2",
                    "status": 404,
                    "body": {"error": {"code": "ItemNotFound", "message": "User not found"}}
                },
                {
                    "id": "3",
                    "status": 200,
                    "body": {"id": "another-valid-user", "displayName": "Another User"}
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = expected_batch_response
            mock_response.headers = {"Content-Type": "application/json"}
            mock_post.return_value.__aenter__.return_value = mock_response
            
            results = await graph_client_integration.batch_request(batch_requests)
            
            assert len(results) == 3
            assert results[0]["status"] == 200
            assert results[1]["status"] == 404
            assert results[2]["status"] == 200

    @pytest.mark.asyncio
    async def test_upload_large_file(self, graph_client_integration):
        """Test subida de archivo grande usando upload session."""
        graph_client_integration.authenticator.get_access_token.return_value = "valid-token"
        
        file_content = b"Large file content" * 1000  # ~20KB
        file_size = len(file_content)
        
        # Mock creación de sesión de subida
        session_response = {
            "uploadUrl": "https://upload.example.com/session/123",
            "expirationDateTime": "2024-02-01T00:00:00Z"
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.put') as mock_put:
            
            # Mock respuestas
            post_response = AsyncMock()
            post_response.status = 201
            post_response.json.return_value = session_response
            
            put_response = AsyncMock()
            put_response.status = 201
            put_response.json.return_value = {
                "id": "uploaded-file-id",
                "name": "large_file.txt",
                "size": file_size
            }
            
            mock_post.return_value.__aenter__.return_value = post_response
            mock_put.return_value.__aenter__.return_value = put_response
            
            result = await graph_client_integration.upload_large_file(
                file_content=file_content,
                file_name="large_file.txt",
                folder_path="/me/drive/root"
            )
            
            assert result["id"] == "uploaded-file-id"
            assert result["size"] == file_size
            mock_post.assert_called_once()
            mock_put.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_large_file(self, graph_client_integration):
        """Test descarga de archivo grande."""
        graph_client_integration.authenticator.get_access_token.return_value = "valid-token"
        
        file_id = "large-file-id"
        expected_content = b"Large file content" * 1000
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.read.return_value = expected_content
            mock_response.headers = {
                "Content-Length": str(len(expected_content)),
                "Content-Type": "application/octet-stream"
            }
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await graph_client_integration.download_file(file_id)
            
            assert result == expected_content

    @pytest.mark.asyncio
    async def test_delta_sync_integration(self, graph_client_integration):
        """Test integración de sincronización delta."""
        graph_client_integration.authenticator.get_access_token.return_value = "valid-token"
        
        # Mock respuestas delta
        initial_response = {
            "value": [
                {"id": "item-1", "name": "Document 1"},
                {"id": "item-2", "name": "Document 2"}
            ],
            "@odata.deltaLink": "https://graph.microsoft.com/v1.0/me/drive/root/delta(token='initial')"
        }
        
        delta_response = {
            "value": [
                {"id": "item-3", "name": "Document 3", "@changeType": "created"},
                {"id": "item-1", "@changeType": "deleted"}
            ],
            "@odata.deltaLink": "https://graph.microsoft.com/v1.0/me/drive/root/delta(token='latest')"
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.side_effect = [
                AsyncMock(status=200, json=lambda: initial_response, headers={"Content-Type": "application/json"}),
                AsyncMock(status=200, json=lambda: delta_response, headers={"Content-Type": "application/json"})
            ]
            
            # Sincronización inicial
            initial_result = await graph_client_integration.delta_sync("/me/drive/root")
            assert len(initial_result["value"]) == 2
            assert "deltaLink" in initial_result
            
            # Sincronización delta
            delta_result = await graph_client_integration.delta_sync(
                "/me/drive/root",
                delta_token="initial"
            )
            assert len(delta_result["value"]) == 2

    @pytest.mark.asyncio
    async def test_webhook_subscription_management(self, graph_client_integration):
        """Test gestión de suscripciones webhook."""
        graph_client_integration.authenticator.get_access_token.return_value = "valid-token"
        
        subscription_data = {
            "resource": "/me/drive/root",
            "change_type": "created,updated,deleted",
            "notificationUrl": "https://example.com/webhook",
            "expirationDateTime": "2024-02-01T00:00:00Z"
        }
        
        expected_subscription = {
            "id": "subscription-123",
            "resource": "/me/drive/root",
            "changeType": "created,updated,deleted",
            "notificationUrl": "https://example.com/webhook",
            "expirationDateTime": "2024-02-01T00:00:00Z"
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 201
            mock_response.json.return_value = expected_subscription
            mock_response.headers = {"Content-Type": "application/json"}
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await graph_client_integration.create_subscription(**subscription_data)
            
            assert result["id"] == "subscription-123"
            assert result["resource"] == subscription_data["resource"]

    @pytest.mark.asyncio
    async def test_error_handling_network_failures(self, graph_client_integration):
        """Test manejo de errores de red."""
        graph_client_integration.authenticator.get_access_token.return_value = "valid-token"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Simular fallo de red
            mock_get.side_effect = aiohttp.ClientError("Network connection failed")
            
            with pytest.raises(Exception) as exc_info:
                await graph_client_integration.get("/users")
            
            assert "Network connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_error_handling_timeout(self, graph_client_integration):
        """Test manejo de timeouts."""
        graph_client_integration.authenticator.get_access_token.return_value = "valid-token"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Simular timeout
            mock_get.side_effect = asyncio.TimeoutError("Request timed out")
            
            with pytest.raises(asyncio.TimeoutError):
                await graph_client_integration.get("/users")

    @pytest.mark.asyncio
    async def test_error_handling_server_errors(self, graph_client_integration):
        """Test manejo de errores del servidor (5xx)."""
        graph_client_integration.authenticator.get_access_token.return_value = "valid-token"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Simular error del servidor
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.json.return_value = {
                "error": {
                    "code": "UnknownError",
                    "message": "An unexpected error occurred"
                }
            }
            mock_get.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(Exception) as exc_info:
                await graph_client_integration.get("/users")
            
            assert "UnknownError" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_concurrent_requests_handling(self, graph_client_integration):
        """Test manejo de solicitudes concurrentes."""
        graph_client_integration.authenticator.get_access_token.return_value = "valid-token"
        
        async def mock_api_call(endpoint: str, response_data: dict):
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = response_data
                mock_response.headers = {"Content-Type": "application/json"}
                mock_get.return_value.__aenter__.return_value = mock_response
                
                return await graph_client_integration.get(endpoint)
        
        # Ejecutar múltiples solicitudes concurrentes
        tasks = [
            mock_api_call("/users", {"value": [{"id": f"user-{i}"}]})
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result["value"][0]["id"] == f"user-{i}"

    @pytest.mark.asyncio
    async def test_retry_mechanism_integration(self, graph_client_integration):
        """Test mecanismo de reintento integrado."""
        graph_client_integration.authenticator.get_access_token.return_value = "valid-token"
        
        call_count = 0
        
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise aiohttp.ClientError("Temporary failure")
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"value": [{"id": "user-123"}]}
            mock_response.headers = {"Content-Type": "application/json"}
            return mock_response
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.side_effect = side_effect
            
            result = await graph_client_integration.get("/users")
            
            assert "value" in result
            assert call_count == 3

    @pytest.mark.asyncio
    async def test_api_versioning(self, graph_client_integration, mock_settings):
        """Test versionado de API."""
        graph_client_integration.authenticator.get_access_token.return_value = "valid-token"
        
        # Cambiar versión de API
        mock_settings.graph_api_version = "beta"
        graph_client_integration.settings = mock_settings
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"value": []}
            mock_response.headers = {"Content-Type": "application/json"}
            mock_get.return_value.__aenter__.return_value = mock_response
            
            await graph_client_integration.get("/users")
            
            # Verificar que la URL incluye la versión correcta
            called_url = mock_get.call_args[1]['url']
            assert "beta" in str(called_url)

    @pytest.mark.asyncio
    async def test_content_type_handling(self, graph_client_integration):
        """Test manejo de diferentes tipos de contenido."""
        graph_client_integration.authenticator.get_access_token.return_value = "valid-token"
        
        test_cases = [
            ("application/json", {"name": "test"}),
            ("application/octet-stream", b"binary data"),
            ("text/plain", "plain text content"),
            ("application/x-www-form-urlencoded", {"param1": "value1"})
        ]
        
        for content_type, test_data in test_cases:
            with patch('aiohttp.ClientSession.post') as mock_post:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {"status": "success"}
                mock_response.headers = {"Content-Type": "application/json"}
                mock_post.return_value.__aenter__.return_value = mock_response
                
                await graph_client_integration.post("/endpoint", data=test_data, content_type=content_type)
                
                # Verificar headers
                called_headers = mock_post.call_args[1]['headers']
                assert called_headers.get('Content-Type') == content_type

    @pytest.mark.asyncio
    async def test_odata_query_parameters(self, graph_client_integration):
        """Test parámetros de consulta OData."""
        graph_client_integration.authenticator.get_access_token.return_value = "valid-token"
        
        query_params = {
            "$select": "id,displayName",
            "$filter": "displayName eq 'Test User'",
            "$orderby": "displayName",
            "$top": "10",
            "$expand": "manager"
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"value": []}
            mock_response.headers = {"Content-Type": "application/json"}
            mock_get.return_value.__aenter__.return_value = mock_response
            
            await graph_client_integration.get("/users", params=query_params)
            
            # Verificar parámetros de consulta
            called_params = mock_get.call_args[1]['params']
            for key, value in query_params.items():
                assert called_params[key] == value

    @pytest.mark.asyncio
    async def test_cors_headers_handling(self, graph_client_integration):
        """Test manejo de headers CORS."""
        graph_client_integration.authenticator.get_access_token.return_value = "valid-token"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"value": []}
            mock_response.headers = {"Content-Type": "application/json"}
            mock_get.return_value.__aenter__.return_value = mock_response
            
            await graph_client_integration.get("/users")
            
            # Verificar headers CORS
            called_headers = mock_get.call_args[1]['headers']
            assert 'Authorization' in called_headers
            assert called_headers['Authorization'].startswith('Bearer ')

    @pytest.mark.asyncio
    async def test_response_validation(self, graph_client_integration):
        """Test validación de respuestas."""
        graph_client_integration.authenticator.get_access_token.return_value = "valid-token"
        
        # Respuesta inválida (sin estructura esperada)
        invalid_response = {"unexpected": "structure"}
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = invalid_response
            mock_response.headers = {"Content-Type": "application/json"}
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Debería procesar la respuesta aunque sea inesperada
            result = await graph_client_integration.get("/users")
            assert result == invalid_response

    @pytest.mark.asyncio
    async def test_large_batch_processing(self, graph_client_integration):
        """Test procesamiento de lotes grandes."""
        graph_client_integration.authenticator.get_access_token.return_value = "valid-token"
        
        # Crear 100 solicitudes en lote
        large_batch = [
            {
                "id": str(i),
                "method": "GET",
                "url": f"/users/user-{i}"
            }
            for i in range(100)
        ]
        
        # Mock respuesta de lote
        batch_responses = {
            "responses": [
                {
                    "id": str(i),
                    "status": 200,
                    "body": {"id": f"user-{i}", "displayName": f"User {i}"}
                }
                for i in range(100)
            ]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = batch_responses
            mock_response.headers = {"Content-Type": "application/json"}
            mock_post.return_value.__aenter__.return_value = mock_response
            
            results = await graph_client_integration.batch_request(large_batch)
            
            assert len(results) == 100
            assert all("id" in result for result in results)

    @pytest.mark.asyncio
    async def test_incremental_backoff_integration(self, graph_client_integration):
        """Test backoff incremental integrado."""
        graph_client_integration.authenticator.get_access_token.return_value = "valid-token"
        
        failure_count = 0
        
        def failing_side_effect(*args, **kwargs):
            nonlocal failure_count
            failure_count += 1
            
            if failure_count <= 3:
                mock_response = AsyncMock()
                mock_response.status = 429
                mock_response.json.return_value = {
                    "error": {"code": "TooManyRequests"}
                }
                return mock_response
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"value": [{"id": "success"}]}
            mock_response.headers = {"Content-Type": "application/json"}
            return mock_response
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.side_effect = failing_side_effect
            
            start_time = time.time()
            result = await graph_client_integration.get("/users")
            end_time = time.time()
            
            assert "value" in result
            # Debería haber esperado entre reintentos
            assert end_time - start_time > 1.0  # Al menos 1 segundo total