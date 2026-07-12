"""
Tests unitarios para OneDrive Agent.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Dict, Any

from src.agents.onedrive_agent import OneDriveAgent
from src.graph.client import GraphAPIClient
from src.auth.azure_ad import AzureADAuthenticator


@pytest.mark.unit
@pytest.mark.onedrive
class TestOneDriveAgent:
    """Tests para OneDriveAgent."""

    @pytest.fixture
    def onedrive_agent(self, mock_graph_client, mock_authenticator):
        """Fixture para crear instancia de OneDriveAgent."""
        return OneDriveAgent(
            graph_client=mock_graph_client,
            authenticator=mock_authenticator
        )

    @pytest.mark.asyncio
    async def test_init(self, onedrive_agent):
        """Test inicialización de OneDriveAgent."""
        assert onedrive_agent.graph_client is not None
        assert onedrive_agent.authenticator is not None
        assert onedrive_agent.base_url == "https://graph.microsoft.com/v1.0"

    @pytest.mark.asyncio
    async def test_upload_file(self, onedrive_agent, sample_file_content, mock_graph_client):
        """Test subida de archivo."""
        parent_folder_id = "root"
        
        mock_response = {
            "id": "test-file-id",
            "name": sample_file_content["name"],
            "size": sample_file_content["size"],
            "webUrl": "https://onedrive.live.com/redir?resid=test-file-id"
        }
        mock_graph_client.put.return_value = mock_response
        
        result = await onedrive_agent.upload_file(
            file_name=sample_file_content["name"],
            file_content=sample_file_content["content"],
            parent_folder_id=parent_folder_id
        )
        
        assert result["id"] == "test-file-id"
        assert result["name"] == sample_file_content["name"]
        mock_graph_client.put.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_large_file(self, onedrive_agent, mock_graph_client):
        """Test subida de archivo grande (upload session)."""
        file_name = "large_file.zip"
        file_size = 104857600  # 100MB
        
        # Mock creación de sesión de subida
        session_response = {
            "uploadUrl": "https://upload.example.com/session/123",
            "expirationDateTime": "2024-01-01T12:00:00Z"
        }
        
        # Mock finalización de subida
        final_response = {
            "id": "large-file-id",
            "name": file_name,
            "size": file_size
        }
        
        mock_graph_client.post.return_value = session_response
        mock_graph_client.put.return_value = final_response
        
        result = await onedrive_agent.upload_large_file(
            file_name=file_name,
            file_content=b"large file content",
            file_size=file_size
        )
        
        assert result["id"] == "large-file-id"
        assert result["name"] == file_name
        mock_graph_client.post.assert_called_once()
        mock_graph_client.put.assert_called()

    @pytest.mark.asyncio
    async def test_download_file(self, onedrive_agent, mock_graph_client):
        """Test descarga de archivo."""
        file_id = "test-file-id"
        
        mock_response = {
            "@microsoft.graph.downloadUrl": "https://download.example.com/file/123",
            "name": "downloaded_file.txt",
            "size": 1024
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await onedrive_agent.download_file(file_id)
        
        assert "@microsoft.graph.downloadUrl" in result
        assert result["name"] == "downloaded_file.txt"
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_file_info(self, onedrive_agent, mock_graph_client):
        """Test obtención de información de archivo."""
        file_id = "test-file-id"
        
        mock_response = {
            "id": file_id,
            "name": "test_file.txt",
            "size": 1024,
            "createdDateTime": "2024-01-01T00:00:00Z",
            "lastModifiedDateTime": "2024-01-02T12:00:00Z",
            "webUrl": "https://onedrive.live.com/redir?resid=test-file-id"
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await onedrive_agent.get_file_info(file_id)
        
        assert result["id"] == file_id
        assert result["name"] == "test_file.txt"
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_file(self, onedrive_agent, mock_graph_client):
        """Test eliminación de archivo."""
        file_id = "test-file-id"
        
        mock_response = {"status": "204"}
        mock_graph_client.delete.return_value = mock_response
        
        result = await onedrive_agent.delete_file(file_id)
        
        assert result["status"] == "204"
        mock_graph_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_copy_file(self, onedrive_agent, mock_graph_client):
        """Test copia de archivo."""
        source_file_id = "source-file-id"
        destination_parent_id = "destination-folder-id"
        new_name = "copy_of_file.txt"
        
        mock_response = {
            "id": "copied-file-id",
            "name": new_name,
            "parentReference": {"id": destination_parent_id}
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await onedrive_agent.copy_file(
            source_file_id=source_file_id,
            destination_parent_id=destination_parent_id,
            new_name=new_name
        )
        
        assert result["id"] == "copied-file-id"
        assert result["name"] == new_name
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_move_file(self, onedrive_agent, mock_graph_client):
        """Test movimiento de archivo."""
        file_id = "test-file-id"
        destination_parent_id = "new-folder-id"
        
        mock_response = {
            "id": file_id,
            "parentReference": {"id": destination_parent_id}
        }
        mock_graph_client.patch.return_value = mock_response
        
        result = await onedrive_agent.move_file(
            file_id=file_id,
            destination_parent_id=destination_parent_id
        )
        
        assert result["parentReference"]["id"] == destination_parent_id
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_folder(self, onedrive_agent, mock_graph_client):
        """Test creación de carpeta."""
        folder_name = "New Folder"
        parent_folder_id = "root"
        
        mock_response = {
            "id": "new-folder-id",
            "name": folder_name,
            "folder": {},
            "parentReference": {"id": parent_folder_id}
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await onedrive_agent.create_folder(
            folder_name=folder_name,
            parent_folder_id=parent_folder_id
        )
        
        assert result["id"] == "new-folder-id"
        assert result["name"] == folder_name
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_folder_contents(self, onedrive_agent, mock_graph_client):
        """Test obtención de contenido de carpeta."""
        folder_id = "folder-id"
        
        mock_response = {
            "value": [
                {
                    "id": "file-1",
                    "name": "document.docx",
                    "file": {},
                    "size": 1024
                },
                {
                    "id": "folder-2",
                    "name": "Subfolder",
                    "folder": {},
                    "size": 0
                }
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await onedrive_agent.get_folder_contents(folder_id)
        
        assert len(result["value"]) == 2
        assert result["value"][0]["name"] == "document.docx"
        assert result["value"][1]["name"] == "Subfolder"
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_share_file(self, onedrive_agent, mock_graph_client):
        """Test compartir archivo."""
        file_id = "test-file-id"
        user_email = "user@example.com"
        permission = "read"
        
        mock_response = {
            "id": "permission-123",
            "link": {
                "webUrl": "https://onedrive.live.com/redir?resid=test-file-id&authkey=!abc123",
                "type": "view"
            }
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await onedrive_agent.share_file(
            file_id=file_id,
            user_email=user_email,
            permission=permission
        )
        
        assert result["id"] == "permission-123"
        assert "link" in result
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_share_link(self, onedrive_agent, mock_graph_client):
        """Test creación de enlace de compartir."""
        file_id = "test-file-id"
        link_type = "view"
        
        mock_response = {
            "link": {
                "webUrl": "https://onedrive.live.com/redir?resid=test-file-id&authkey=!def456",
                "type": link_type,
                "scope": "anonymous"
            }
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await onedrive_agent.create_share_link(
            file_id=file_id,
            link_type=link_type
        )
        
        assert "link" in result
        assert result["link"]["type"] == link_type
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_file_versions(self, onedrive_agent, mock_graph_client):
        """Test obtención de versiones de archivo."""
        file_id = "test-file-id"
        
        mock_response = {
            "value": [
                {
                    "id": "version-1",
                    "lastModifiedBy": {"user": {"displayName": "John Doe"}},
                    "lastModifiedDateTime": "2024-01-01T10:00:00Z",
                    "size": 2048
                },
                {
                    "id": "version-2",
                    "lastModifiedBy": {"user": {"displayName": "Jane Smith"}},
                    "lastModifiedDateTime": "2024-01-02T14:30:00Z",
                    "size": 3072
                }
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await onedrive_agent.get_file_versions(file_id)
        
        assert len(result["value"]) == 2
        assert result["value"][0]["id"] == "version-1"
        assert result["value"][1]["id"] == "version-2"
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_restore_file_version(self, onedrive_agent, mock_graph_client):
        """Test restauración de versión de archivo."""
        file_id = "test-file-id"
        version_id = "version-1"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await onedrive_agent.restore_file_version(
            file_id=file_id,
            version_id=version_id
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_files(self, onedrive_agent, mock_graph_client):
        """Test búsqueda de archivos."""
        search_query = "quarterly report"
        
        mock_response = {
            "value": [
                {
                    "id": "file-1",
                    "name": "Q1_2024_Report.pdf",
                    "webUrl": "https://onedrive.live.com/redir?resid=file-1"
                },
                {
                    "id": "file-2",
                    "name": "Quarterly_Summary.docx",
                    "webUrl": "https://onedrive.live.com/redir?resid=file-2"
                }
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await onedrive_agent.search_files(search_query)
        
        assert len(result["value"]) == 2
        assert all("quarterly" in file["name"].lower() for file in result["value"])

    @pytest.mark.asyncio
    async def test_get_file_metadata(self, onedrive_agent, mock_graph_client):
        """Test obtención de metadatos de archivo."""
        file_id = "test-file-id"
        
        mock_response = {
            "id": file_id,
            "name": "document.pdf",
            "size": 5120,
            "createdDateTime": "2024-01-01T00:00:00Z",
            "lastModifiedDateTime": "2024-01-02T12:00:00Z",
            "createdBy": {"user": {"displayName": "John Doe"}},
            "lastModifiedBy": {"user": {"displayName": "Jane Smith"}},
            "file": {
                "mimeType": "application/pdf",
                "hashes": {
                    "sha1Hash": "abc123def456"
                }
            }
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await onedrive_agent.get_file_metadata(file_id)
        
        assert result["id"] == file_id
        assert result["file"]["mimeType"] == "application/pdf"
        assert "hashes" in result["file"]
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_file_metadata(self, onedrive_agent, mock_graph_client):
        """Test actualización de metadatos de archivo."""
        file_id = "test-file-id"
        metadata = {
            "name": "Updated_Document.pdf",
            "description": "Updated document description"
        }
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await onedrive_agent.update_file_metadata(file_id, **metadata)
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_storage_quota(self, onedrive_agent, mock_graph_client):
        """Test obtención de cuota de almacenamiento."""
        mock_response = {
            "storage_plan_info": {
                "total_awesome_capacity": 536870912000,
                "used_awesome_capacity": 53687091200
            }
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await onedrive_agent.get_storage_quota()
        
        assert "storage_plan_info" in result
        assert result["storage_plan_info"]["total_awesome_capacity"] > 0
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_folder(self, onedrive_agent, mock_graph_client):
        """Test sincronización de carpeta."""
        folder_id = "folder-id"
        delta_token = "delta-token-123"
        
        # Mock estado inicial
        initial_response = {
            "value": [
                {"id": "file-1", "name": "new_file.txt"},
                {"id": "file-2", "name": "updated_file.docx"}
            ],
            "@odata.deltaLink": "https://graph.microsoft.com/v1.0/me/drive/root/delta(token='new-token-456')"
        }
        
        # Mock cambios delta
        delta_response = {
            "value": [
                {"id": "file-3", "name": "another_file.pdf"}
            ],
            "@odata.deltaLink": "https://graph.microsoft.com/v1.0/me/drive/root/delta(token='latest-token')"
        }
        
        mock_graph_client.get.side_effect = [initial_response, delta_response]
        
        result = await onedrive_agent.sync_folder(folder_id, delta_token)
        
        assert len(result["changes"]) == 3  # initial + delta
        assert result["next_delta_token"] == "latest-token"
        mock_graph_client.get.assert_called()

    @pytest.mark.asyncio
    async def test_preview_file(self, onedrive_agent, mock_graph_client):
        """Test previsualización de archivo."""
        file_id = "test-file-id"
        
        mock_response = {
            "get_url": "https://view.officeapps.live.com/op/embed.aspx?src=https://example.com/preview",
            "type": "word",
            "file_extension": "docx"
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await onedrive_agent.preview_file(file_id)
        
        assert "get_url" in result
        assert result["type"] == "word"
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_text_from_file(self, onedrive_agent, mock_graph_client):
        """Test extracción de texto de archivo."""
        file_id = "document-id"
        
        mock_response = {
            "content": "Extracted text content from document..."
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await onedrive_agent.extract_text_from_file(file_id)
        
        assert "content" in result
        assert isinstance(result["content"], str)
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_shared_files(self, onedrive_agent, mock_graph_client):
        """Test obtención de archivos compartidos."""
        mock_response = {
            "value": [
                {
                    "id": "shared-1",
                    "name": "Shared_Document.docx",
                    "shared_by": {"user": {"displayName": "Colleague"}},
                    "shared_datetime": "2024-01-01T00:00:00Z"
                },
                {
                    "id": "shared-2",
                    "name": "Shared_Spreadsheet.xlsx",
                    "shared_by": {"user": {"displayName": "Team Member"}},
                    "shared_datetime": "2024-01-02T00:00:00Z"
                }
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await onedrive_agent.get_shared_files()
        
        assert len(result["value"]) == 2
        assert all("shared_by" in file for file in result["value"])
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_follow_file(self, onedrive_agent, mock_graph_client):
        """Test seguimiento de archivo."""
        file_id = "test-file-id"
        
        mock_response = {
            "id": "followed-file",
            "relationship_type": "follow",
            "state": "followed"
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await onedrive_agent.follow_file(file_id)
        
        assert result["relationship_type"] == "follow"
        assert result["state"] == "followed"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_unfollow_file(self, onedrive_agent, mock_graph_client):
        """Test dejar de seguir archivo."""
        file_id = "test-file-id"
        
        mock_response = {"status": "204"}
        mock_graph_client.delete.return_value = mock_response
        
        result = await onedrive_agent.unfollow_file(file_id)
        
        assert result["status"] == "204"
        mock_graph_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recent_files(self, onedrive_agent, mock_graph_client):
        """Test obtención de archivos recientes."""
        mock_response = {
            "value": [
                {
                    "id": "recent-1",
                    "name": "Recent_Document.docx",
                    "lastAccessedDateTime": "2024-01-01T10:00:00Z"
                },
                {
                    "id": "recent-2",
                    "name": "Recent_Spreadsheet.xlsx",
                    "lastAccessedDateTime": "2024-01-01T09:30:00Z"
                }
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await onedrive_agent.get_recent_files()
        
        assert len(result["value"]) == 2
        assert all("lastAccessedDateTime" in file for file in result["value"])
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_network_error(self, onedrive_agent, error_scenarios):
        """Test manejo de errores de red."""
        onedrive_agent.graph_client.get.side_effect = error_scenarios["network_error"]
        
        with pytest.raises(Exception) as exc_info:
            await onedrive_agent.get_file_info("test-file-id")
        
        assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_error_handling_file_not_found(self, onedrive_agent, error_scenarios):
        """Test manejo de archivo no encontrado."""
        onedrive_agent.graph_client.get.side_effect = error_scenarios["not_found_error"]
        
        with pytest.raises(Exception) as exc_info:
            await onedrive_agent.get_file_info("non-existent-file-id")
        
        assert "Resource not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, onedrive_agent, rate_limit_responses):
        """Test manejo de rate limiting."""
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return rate_limit_responses["rate_limited"]
            return rate_limit_responses["success"]
        
        onedrive_agent.graph_client.get.side_effect = side_effect
        
        with patch.object(onedrive_agent, '_retry_with_backoff') as mock_retry:
            mock_retry.return_value = rate_limit_responses["success"]
            
            result = await onedrive_agent.get_file_info("test-file-id")
            
            assert mock_retry.called

    @pytest.mark.asyncio
    async def test_batch_file_operations(self, onedrive_agent, mock_graph_client):
        """Test operaciones en lote de archivos."""
        operations = [
            {"method": "DELETE", "url": "/me/drive/items/file-1"},
            {"method": "DELETE", "url": "/me/drive/items/file-2"},
            {"method": "DELETE", "url": "/me/drive/items/file-3"}
        ]
        
        mock_responses = [
            {"status": "204"},
            {"status": "204"},
            {"status": "204"}
        ]
        mock_graph_client.batch_request.return_value = mock_responses
        
        results = await onedrive_agent.batch_file_operations(operations)
        
        assert len(results) == 3
        assert all(r["status"] == "204" for r in results)

    @pytest.mark.asyncio
    async def test_upload_multiple_files(self, onedrive_agent, mock_graph_client):
        """Test subida múltiple de archivos."""
        files = [
            {"name": "file1.txt", "content": "Content 1"},
            {"name": "file2.txt", "content": "Content 2"},
            {"name": "file3.txt", "content": "Content 3"}
        ]
        
        mock_responses = [
            {"id": "file-1", "name": "file1.txt"},
            {"id": "file-2", "name": "file2.txt"},
            {"id": "file-3", "name": "file3.txt"}
        ]
        mock_graph_client.put.return_value = {"id": "mock-id", "name": "mock-name"}
        
        # Simular diferentes respuestas para cada llamada
        def side_effect(*args, **kwargs):
            for response in mock_responses:
                if response["name"] in str(args):
                    return response
            return mock_responses[0]
        
        mock_graph_client.put.side_effect = side_effect
        
        results = await onedrive_agent.upload_multiple_files(files)
        
        assert len(results) == 3
        assert all("id" in result for result in results)

    @pytest.mark.asyncio
    async def test_organize_files_by_date(self, onedrive_agent, mock_graph_client):
        """Test organización de archivos por fecha."""
        files_data = [
            {"id": "file-1", "createdDateTime": "2024-01-01T00:00:00Z"},
            {"id": "file-2", "createdDateTime": "2024-02-01T00:00:00Z"},
            {"id": "file-3", "createdDateTime": "2024-03-01T00:00:00Z"}
        ]
        
        organization_result = await onedrive_agent.organize_files_by_date(
            source_folder_id="source-folder",
            target_base_folder="organized"
        )
        
        # Verificar que se crearon carpetas por mes/año
        assert "2024" in organization_result["created_folders"]
        assert len(organization_result["moved_files"]) == 3
        assert organization_result["total_files"] == 3

    @pytest.mark.asyncio
    async def test_compress_folder(self, onedrive_agent, mock_graph_client):
        """Test compresión de carpeta."""
        folder_id = "folder-id"
        compression_format = "zip"
        
        mock_response = {
            "id": "compressed-folder-id",
            "name": "compressed_folder.zip",
            "size": 1024000,
            "createdDateTime": "2024-01-01T00:00:00Z"
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await onedrive_agent.compress_folder(
            folder_id=folder_id,
            compression_format=compression_format
        )
        
        assert result["name"].endswith(".zip")
        assert result["size"] > 0
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_compressed_file(self, onedrive_agent, mock_graph_client):
        """Test extracción de archivo comprimido."""
        zip_file_id = "zip-file-id"
        target_folder_id = "target-folder"
        
        mock_response = {
            "extracted_files": [
                {"id": "extracted-1", "name": "file1.txt"},
                {"id": "extracted-2", "name": "file2.txt"},
                {"id": "extracted-3", "name": "file3.txt"}
            ],
            "extraction_status": "completed"
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await onedrive_agent.extract_compressed_file(
            zip_file_id=zip_file_id,
            target_folder_id=target_folder_id
        )
        
        assert result["extraction_status"] == "completed"
        assert len(result["extracted_files"]) == 3
        mock_graph_client.post.assert_called_once()