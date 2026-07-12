"""
Tests unitarios para Word Agent.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Dict, Any

from src.agents.word_agent import WordAgent
from src.graph.client import GraphAPIClient
from src.auth.azure_ad import AzureADAuthenticator


@pytest.mark.unit
@pytest.mark.word
class TestWordAgent:
    """Tests para WordAgent."""

    @pytest.fixture
    def word_agent(self, mock_graph_client, mock_authenticator):
        """Fixture para crear instancia de WordAgent."""
        return WordAgent(
            graph_client=mock_graph_client,
            authenticator=mock_authenticator
        )

    @pytest.mark.asyncio
    async def test_init(self, word_agent):
        """Test inicialización de WordAgent."""
        assert word_agent.graph_client is not None
        assert word_agent.authenticator is not None
        assert word_agent.base_url == "https://graph.microsoft.com/v1.0"

    @pytest.mark.asyncio
    async def test_create_document(self, word_agent, sample_docx_content, mock_graph_client):
        """Test creación de documento."""
        # Mock respuesta de Graph API
        mock_response = {
            "id": "test-doc-id",
            "name": "Test Document.docx",
            "webUrl": "https://word.com/edit/test-doc-id"
        }
        mock_graph_client.post.return_value = mock_response
        
        # Mock autenticación
        word_agent.authenticator.get_access_token.return_value = "test-token"
        
        # Ejecutar test
        result = await word_agent.create_document(
            title=sample_docx_content["title"],
            content=sample_docx_content
        )
        
        # Verificaciones
        assert result["id"] == "test-doc-id"
        assert result["name"] == "Test Document.docx"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_document_with_template(self, word_agent, mock_graph_client):
        """Test creación de documento desde plantilla."""
        template_id = "template-123"
        mock_response = {
            "id": "new-doc-id",
            "name": "New Document.docx"
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await word_agent.create_document_from_template(
            template_id=template_id,
            title="New Document"
        )
        
        assert result["id"] == "new-doc-id"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_document(self, word_agent, mock_graph_client):
        """Test obtención de documento."""
        doc_id = "test-doc-id"
        mock_response = {
            "id": doc_id,
            "name": "Test Document.docx",
            "content": "Document content"
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await word_agent.get_document(doc_id)
        
        assert result["id"] == doc_id
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_document_content(self, word_agent, mock_graph_client):
        """Test actualización de contenido de documento."""
        doc_id = "test-doc-id"
        new_content = {
            "paragraphs": [
                {"text": "Updated content", "style": "Normal"}
            ]
        }
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await word_agent.update_document_content(doc_id, new_content)
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_paragraph(self, word_agent, mock_graph_client):
        """Test adición de párrafo."""
        doc_id = "test-doc-id"
        paragraph_text = "New paragraph content"
        paragraph_style = "Normal"
        
        mock_response = {"status": "201"}
        mock_graph_client.post.return_value = mock_response
        
        result = await word_agent.add_paragraph(
            document_id=doc_id,
            text=paragraph_text,
            style=paragraph_style
        )
        
        assert result["status"] == "201"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_table(self, word_agent, mock_graph_client):
        """Test adición de tabla."""
        doc_id = "test-doc-id"
        table_data = {
            "rows": [["Header1", "Header2"], ["Value1", "Value2"]],
            "style": "Table Grid"
        }
        
        mock_response = {"status": "201"}
        mock_graph_client.post.return_value = mock_response
        
        result = await word_agent.add_table(document_id=doc_id, table_data=table_data)
        
        assert result["status"] == "201"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_image(self, word_agent, mock_graph_client):
        """Test adición de imagen."""
        doc_id = "test-doc-id"
        image_url = "https://example.com/image.png"
        
        mock_response = {"status": "201"}
        mock_graph_client.post.return_value = mock_response
        
        result = await word_agent.add_image(
            document_id=doc_id,
            image_url=image_url
        )
        
        assert result["status"] == "201"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_format_text(self, word_agent, mock_graph_client):
        """Test formato de texto."""
        doc_id = "test-doc-id"
        paragraph_id = "para-123"
        formatting_options = {
            "bold": True,
            "italic": True,
            "underline": True,
            "font_size": 14,
            "font_name": "Arial"
        }
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await word_agent.format_text(
            document_id=doc_id,
            paragraph_id=paragraph_id,
            **formatting_options
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_comment(self, word_agent, mock_graph_client):
        """Test adición de comentario."""
        doc_id = "test-doc-id"
        comment_text = "This needs review"
        range_start = 0
        range_end = 50
        
        mock_response = {"status": "201"}
        mock_graph_client.post.return_value = mock_response
        
        result = await word_agent.add_comment(
            document_id=doc_id,
            comment=comment_text,
            range_start=range_start,
            range_end=range_end
        )
        
        assert result["status"] == "201"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_track_changes(self, word_agent, mock_graph_client):
        """Test activar/desactivar seguimiento de cambios."""
        doc_id = "test-doc-id"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await word_agent.track_changes(document_id=doc_id, enabled=True)
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_document_versions(self, word_agent, mock_graph_client):
        """Test obtención de versiones de documento."""
        doc_id = "test-doc-id"
        mock_response = {
            "value": [
                {
                    "id": "version-1",
                    "lastModifiedBy": "User",
                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                    "size": 1024
                }
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await word_agent.get_document_versions(doc_id)
        
        assert len(result["value"]) == 1
        assert result["value"][0]["id"] == "version-1"
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_restore_version(self, word_agent, mock_graph_client):
        """Test restauración de versión."""
        doc_id = "test-doc-id"
        version_id = "version-1"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await word_agent.restore_version(doc_id, version_id)
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_share_document(self, word_agent, mock_graph_client):
        """Test compartir documento."""
        doc_id = "test-doc-id"
        user_email = "user@example.com"
        permission = "read"
        
        mock_response = {"status": "201"}
        mock_graph_client.post.return_value = mock_response
        
        result = await word_agent.share_document(
            document_id=doc_id,
            user_email=user_email,
            permission=permission
        )
        
        assert result["status"] == "201"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_collaborators(self, word_agent, mock_graph_client):
        """Test obtener colaboradores."""
        doc_id = "test-doc-id"
        mock_response = {
            "value": [
                {
                    "id": "user-1",
                    "displayName": "Collaborator 1",
                    "email": "collab1@example.com",
                    "role": "read"
                }
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await word_agent.get_collaborators(doc_id)
        
        assert len(result["value"]) == 1
        assert result["value"][0]["displayName"] == "Collaborator 1"
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_to_pdf(self, word_agent, mock_graph_client):
        """Test exportación a PDF."""
        doc_id = "test-doc-id"
        
        mock_response = {"@microsoft.graph.downloadUrl": "https://download-url.pdf"}
        mock_graph_client.get.return_value = mock_response
        
        result = await word_agent.export_to_pdf(doc_id)
        
        assert "@microsoft.graph.downloadUrl" in result
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_network_error(self, word_agent, error_scenarios):
        """Test manejo de errores de red."""
        word_agent.graph_client.get.side_effect = error_scenarios["network_error"]
        
        with pytest.raises(Exception) as exc_info:
            await word_agent.get_document("test-doc-id")
        
        assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_error_handling_unauthorized(self, word_agent, rate_limit_responses):
        """Test manejo de errores de autorización."""
        word_agent.graph_client.get.return_value = rate_limit_responses["unauthorized"]
        
        with pytest.raises(Exception) as exc_info:
            await word_agent.get_document("test-doc-id")
        
        assert "Unauthorized" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_error_handling_not_found(self, word_agent, error_scenarios):
        """Test manejo de errores de recurso no encontrado."""
        word_agent.graph_client.get.side_effect = error_scenarios["not_found_error"]
        
        with pytest.raises(Exception) as exc_info:
            await word_agent.get_document("non-existent-doc-id")
        
        assert "Resource not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, word_agent, rate_limit_responses):
        """Test manejo de rate limiting."""
        # Simular rate limit en primera llamada
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return rate_limit_responses["rate_limited"]
            return rate_limit_responses["success"]
        
        word_agent.graph_client.get.side_effect = side_effect
        
        # Debería reintentar automáticamente
        with patch.object(word_agent, '_retry_with_backoff') as mock_retry:
            mock_retry.return_value = rate_limit_responses["success"]
            
            result = await word_agent.get_document("test-doc-id")
            
            assert mock_retry.called

    @pytest.mark.asyncio
    async def test_batch_operations(self, word_agent, mock_graph_client):
        """Test operaciones en lote."""
        operations = [
            {"method": "POST", "url": "/documents/1/paragraphs", "body": {"text": "Text 1"}},
            {"method": "POST", "url": "/documents/1/paragraphs", "body": {"text": "Text 2"}},
            {"method": "POST", "url": "/documents/1/tables", "body": {"rows": [["A", "B"]]}}
        ]
        
        mock_responses = [
            {"status": "201", "id": "para-1"},
            {"status": "201", "id": "para-2"},
            {"status": "201", "id": "table-1"}
        ]
        mock_graph_client.batch_request.return_value = mock_responses
        
        results = await word_agent.batch_operations(operations)
        
        assert len(results) == 3
        assert all("id" in result for result in results)

    @pytest.mark.asyncio
    async def test_search_documents(self, word_agent, mock_graph_client):
        """Test búsqueda de documentos."""
        query = "test document"
        mock_response = {
            "value": [
                {
                    "id": "doc-1",
                    "name": "Test Document 1",
                    "webUrl": "https://word.com/edit/doc-1"
                },
                {
                    "id": "doc-2", 
                    "name": "Test Document 2",
                    "webUrl": "https://word.com/edit/doc-2"
                }
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await word_agent.search_documents(query)
        
        assert len(result["value"]) == 2
        assert all("name" in doc for doc in result["value"])

    @pytest.mark.asyncio
    async def test_get_document_statistics(self, word_agent, mock_graph_client):
        """Test obtener estadísticas de documento."""
        doc_id = "test-doc-id"
        mock_response = {
            "word_count": 500,
            "character_count": 2500,
            "paragraph_count": 25,
            "page_count": 2,
            "line_count": 100
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await word_agent.get_document_statistics(doc_id)
        
        assert result["word_count"] == 500
        assert result["paragraph_count"] == 25

    @pytest.mark.asyncio
    async def test_add_bookmark(self, word_agent, mock_graph_client):
        """Test adición de marcador."""
        doc_id = "test-doc-id"
        bookmark_name = "Chapter1"
        range_start = 100
        range_end = 200
        
        mock_response = {"status": "201"}
        mock_graph_client.post.return_value = mock_response
        
        result = await word_agent.add_bookmark(
            document_id=doc_id,
            bookmark_name=bookmark_name,
            range_start=range_start,
            range_end=range_end
        )
        
        assert result["status"] == "201"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_hyperlink(self, word_agent, mock_graph_client):
        """Test adición de hipervínculo."""
        doc_id = "test-doc-id"
        link_text = "Click here"
        url = "https://example.com"
        range_start = 0
        range_end = 10
        
        mock_response = {"status": "201"}
        mock_graph_client.post.return_value = mock_response
        
        result = await word_agent.add_hyperlink(
            document_id=doc_id,
            link_text=link_text,
            url=url,
            range_start=range_start,
            range_end=range_end
        )
        
        assert result["status"] == "201"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_document_template(self, word_agent, mock_graph_client):
        """Test aplicación de plantilla de documento."""
        doc_id = "test-doc-id"
        template_id = "template-123"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await word_agent.apply_document_template(doc_id, template_id)
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_merge_documents(self, word_agent, mock_graph_client):
        """Test fusión de documentos."""
        main_doc_id = "main-doc-id"
        source_doc_id = "source-doc-id"
        insertion_point = "end"
        
        mock_response = {"status": "204"}
        mock_graph_client.post.return_value = mock_response
        
        result = await word_agent.merge_documents(
            main_document_id=main_doc_id,
            source_document_id=source_doc_id,
            insertion_point=insertion_point
        )
        
        assert result["status"] == "204"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_protect_document(self, word_agent, mock_graph_client):
        """Test protección de documento."""
        doc_id = "test-doc-id"
        protection_type = "editing"
        password = "test-password"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await word_agent.protect_document(
            document_id=doc_id,
            protection_type=protection_type,
            password=password
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_header_footer(self, word_agent, mock_graph_client):
        """Test adición de encabezado/pie de página."""
        doc_id = "test-doc-id"
        header_text = "Company Name"
        footer_text = "Confidential"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await word_agent.add_header_footer(
            document_id=doc_id,
            header_text=header_text,
            footer_text=footer_text
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()