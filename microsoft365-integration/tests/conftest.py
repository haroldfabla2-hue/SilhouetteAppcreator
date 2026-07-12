"""
Configuración común para pytest fixtures y utilidades de test.
"""
import asyncio
import json
import os
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Generator, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import aiohttp
import pytest
import pytest_asyncio
from src.config.settings import Settings
from src.graph.client import GraphAPIClient
from src.auth.azure_ad import AzureADAuthenticator


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_azure_credentials():
    """Mock credentials para testing."""
    return {
        "tenant_id": "test-tenant-id",
        "client_id": "test-client-id", 
        "client_secret": "test-client-secret",
        "redirect_uri": "http://localhost:8000/callback"
    }


@pytest.fixture
def mock_access_token():
    """Mock access token."""
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwic2NvcGUiOiJzY29wZSJ9.signature"


@pytest.fixture
def mock_graph_api_response():
    """Mock respuesta de Graph API."""
    return {
        "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#users",
        "value": [
            {
                "id": "12345678-1234-1234-1234-123456789012",
                "displayName": "Test User",
                "mail": "test@example.com",
                "userPrincipalName": "test@contoso.onmicrosoft.com"
            }
        ]
    }


@pytest.fixture
def mock_settings(mock_azure_credentials):
    """Mock settings para testing."""
    settings = Mock(spec=Settings)
    settings.azure_tenant_id = mock_azure_credentials["tenant_id"]
    settings.azure_client_id = mock_azure_credentials["client_id"]
    settings.azure_client_secret = mock_azure_credentials["client_secret"]
    settings.redirect_uri = mock_azure_credentials["redirect_uri"]
    settings.graph_api_base_url = "https://graph.microsoft.com/v1.0"
    settings.graph_api_version = "v1.0"
    settings.rate_limit_requests_per_minute = 1000
    settings.rate_limit_requests_per_hour = 10000
    settings.max_retry_attempts = 3
    settings.retry_backoff_factor = 2.0
    settings.token_cache_enabled = True
    settings.webhook_validation_token = "validation-token"
    settings.redis_url = "redis://localhost:6379/0"
    return settings


@pytest.fixture
async def mock_session():
    """Mock aiohttp session."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    session.close = AsyncMock()
    return session


@pytest.fixture
async def mock_authenticator(mock_settings, mock_access_token, mock_session):
    """Mock autenticador Azure AD."""
    authenticator = Mock(spec=AzureADAuthenticator)
    authenticator.get_access_token = AsyncMock(return_value=mock_access_token)
    authenticator.validate_token = AsyncMock(return_value=True)
    authenticator.refresh_token = AsyncMock(return_value=mock_access_token)
    return authenticator


@pytest.fixture
async def mock_graph_client(mock_settings, mock_authenticator, mock_session, mock_graph_api_response):
    """Mock Graph API client."""
    client = AsyncMock(spec=GraphAPIClient)
    
    # Mock métodos comunes
    client.get = AsyncMock(return_value=mock_graph_api_response)
    client.post = AsyncMock(return_value=mock_graph_api_response)
    client.put = AsyncMock(return_value=mock_graph_api_response)
    client.patch = AsyncMock(return_value=mock_graph_api_response)
    client.delete = AsyncMock(return_value={"status": "204"})
    client.batch_request = AsyncMock(return_value=[mock_graph_api_response, mock_graph_api_response])
    
    # Mock rate limiting
    client.rate_limited = AsyncMock(return_value=False)
    client.acquire_rate_limit = AsyncMock(return_value=True)
    client.release_rate_limit = AsyncMock()
    
    return client


@pytest.fixture
def sample_docx_content():
    """Contenido de ejemplo para documento Word."""
    return {
        "title": "Test Document",
        "paragraphs": [
            {"text": "This is a test paragraph.", "style": "Normal"},
            {"text": "This is a bold paragraph.", "style": "Heading1"}
        ],
        "tables": [
            {
                "rows": [["Header1", "Header2"], ["Value1", "Value2"]],
                "style": "Table Grid"
            }
        ]
    }


@pytest.fixture
def sample_xlsx_content():
    """Contenido de ejemplo para hoja de cálculo Excel."""
    return {
        "worksheets": [
            {
                "name": "Sheet1",
                "data": [
                    ["Product", "Price", "Quantity"],
                    ["Widget A", 10.99, 100],
                    ["Widget B", 15.99, 50]
                ],
                "formulas": {
                    "D2": "=B2*C2",
                    "D3": "=B3*C3"
                },
                "charts": [
                    {
                        "type": "column",
                        "data_range": "A1:C3",
                        "title": "Product Sales"
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_pptx_content():
    """Contenido de ejemplo para presentación PowerPoint."""
    return {
        "title": "Test Presentation",
        "slides": [
            {
                "layout": "title_slide",
                "title": "Welcome",
                "content": "This is a test presentation."
            },
            {
                "layout": "title_content",
                "title": "Introduction",
                "content": "Here is the introduction content."
            }
        ],
        "theme": "corporate_blue"
    }


@pytest.fixture
def sample_email_content():
    """Contenido de ejemplo para email."""
    return {
        "subject": "Test Email",
        "body": {
            "content_type": "HTML",
            "content": "<h1>Test Email</h1><p>This is a test email.</p>"
        },
        "to_recipients": [{"email_address": {"address": "recipient@example.com"}}],
        "attachments": [
            {
                "name": "test.txt",
                "content_type": "text/plain",
                "content": "Test attachment content"
            }
        ]
    }


@pytest.fixture
def sample_calendar_event():
    """Contenido de ejemplo para evento de calendario."""
    return {
        "subject": "Test Meeting",
        "start": {
            "date_time": "2024-01-15T10:00:00",
            "time_zone": "Pacific Standard Time"
        },
        "end": {
            "date_time": "2024-01-15T11:00:00", 
            "time_zone": "Pacific Standard Time"
        },
        "attendees": [
            {
                "email_address": {
                    "address": "attendee@example.com",
                    "name": "Test Attendee"
                },
                "type": "required"
            }
        ],
        "location": {
            "display_name": "Conference Room"
        }
    }


@pytest.fixture
def sample_file_content():
    """Contenido de ejemplo para archivo."""
    return {
        "name": "test_document.txt",
        "content": "This is test file content.",
        "mime_type": "text/plain",
        "size": 1024
    }


@pytest.fixture
def sample_team_content():
    """Contenido de ejemplo para equipo de Teams."""
    return {
        "template": "standard",
        "display_name": "Test Team",
        "description": "A test team for unit testing",
        "visibility": "private",
        "channels": [
            {
                "display_name": "General",
                "description": "General channel"
            },
            {
                "display_name": "Development",
                "description": "Development discussions"
            }
        ]
    }


@pytest.fixture
def rate_limit_responses():
    """Respuestas simuladas de rate limiting."""
    return {
        "success": {"status": 200, "data": {"success": True}},
        "rate_limited": {"status": 429, "data": {"error": "Rate limit exceeded"}},
        "server_error": {"status": 500, "data": {"error": "Internal server error"}},
        "unauthorized": {"status": 401, "data": {"error": "Unauthorized"}},
        "forbidden": {"status": 403, "data": {"error": "Forbidden"}}
    }


@pytest.fixture
def error_scenarios():
    """Escenarios de error para testing."""
    return {
        "network_error": aiohttp.ClientError("Network error"),
        "timeout_error": asyncio.TimeoutError("Request timeout"),
        "json_decode_error": json.JSONDecodeError("Invalid JSON", "", 0),
        "auth_error": Exception("Authentication failed"),
        "permission_error": Exception("Insufficient permissions"),
        "not_found_error": Exception("Resource not found"),
        "validation_error": Exception("Invalid input data")
    }


@pytest.fixture
def mock_redis():
    """Mock Redis client para rate limiting."""
    redis_mock = Mock()
    redis_mock.get = Mock(return_value=None)
    redis_mock.set = Mock(return_value=True)
    redis_mock.incr = Mock(return_value=1)
    redis_mock.expire = Mock(return_value=True)
    redis_mock.delete = Mock(return_value=True)
    redis_mock.exists = Mock(return_value=False)
    redis_mock.ping = Mock(return_value=True)
    return redis_mock


@pytest.fixture
def temp_files(tmp_path):
    """Archivos temporales para testing."""
    return {
        "docx_file": tmp_path / "test_document.docx",
        "xlsx_file": tmp_path / "test_spreadsheet.xlsx", 
        "pptx_file": tmp_path / "test_presentation.pptx",
        "txt_file": tmp_path / "test_file.txt",
        "json_file": tmp_path / "test_data.json"
    }


@pytest.fixture
def logger_mock():
    """Mock logger."""
    logger = Mock()
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.critical = Mock()
    return logger


@pytest.fixture
def test_config():
    """Configuración específica para tests."""
    return {
        "test_user_id": "test-user-123",
        "test_team_id": "test-team-456",
        "test_channel_id": "test-channel-789",
        "test_document_id": "test-doc-abc",
        "test_folder_id": "test-folder-def",
        "timeout_seconds": 30,
        "max_retries": 3,
        "batch_size": 20
    }


# Autouse fixtures para patches globales
@pytest.fixture(autouse=True)
def patch_azure_client():
    """Patch automáticamente el cliente MSAL para tests."""
    with patch('msal.ConfidentialClientApplication') as mock_app:
        mock_instance = Mock()
        mock_instance.acquire_token_silent = Mock(return_value={
            'access_token': 'mock-token',
            'expires_in': 3600
        })
        mock_instance.acquire_token_for_client = Mock(return_value={
            'access_token': 'mock-client-token',
            'expires_in': 3600
        })
        mock_app.return_value = mock_instance
        yield mock_app


@pytest.fixture(autouse=True)
def patch_redis():
    """Patch automáticamente Redis para tests."""
    with patch('redis.Redis') as mock_redis:
        mock_instance = Mock()
        mock_instance.get = Mock(return_value=None)
        mock_instance.set = Mock(return_value=True)
        mock_instance.expire = Mock(return_value=True)
        mock_redis.return_value = mock_instance
        yield mock_redis


# Helpers para creación de objetos mocks
def create_mock_user(user_id: str = "test-user", display_name: str = "Test User") -> Dict[str, Any]:
    """Crear mock de usuario."""
    return {
        "id": user_id,
        "displayName": display_name,
        "mail": f"{display_name.lower().replace(' ', '.')}@example.com",
        "userPrincipalName": f"{display_name.lower().replace(' ', '.')}@contoso.onmicrosoft.com"
    }


def create_mock_file(file_id: str = "test-file", file_name: str = "test.txt") -> Dict[str, Any]:
    """Crear mock de archivo."""
    return {
        "id": file_id,
        "name": file_name,
        "size": 1024,
        "createdDateTime": "2024-01-01T00:00:00Z",
        "lastModifiedDateTime": "2024-01-01T00:00:00Z",
        "webUrl": f"https://onedrive.live.com/redir?resid={file_id}",
        "file": {
            "mimeType": "text/plain"
        }
    }


def create_mock_team(team_id: str = "test-team") -> Dict[str, Any]:
    """Crear mock de equipo."""
    return {
        "id": team_id,
        "displayName": "Test Team",
        "description": "Test team description",
        "isArchived": False,
        "createdDateTime": "2024-01-01T00:00:00Z"
    }


# Marcadores personalizados para pytest
def pytest_configure(config):
    """Configurar marcadores personalizados para pytest."""
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )