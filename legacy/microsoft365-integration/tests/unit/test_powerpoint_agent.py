"""
Tests unitarios para PowerPoint Agent.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Dict, Any

from src.agents.powerpoint_agent import PowerPointAgent
from src.graph.client import GraphAPIClient
from src.auth.azure_ad import AzureADAuthenticator


@pytest.mark.unit
@pytest.mark.powerpoint
class TestPowerPointAgent:
    """Tests para PowerPointAgent."""

    @pytest.fixture
    def powerpoint_agent(self, mock_graph_client, mock_authenticator):
        """Fixture para crear instancia de PowerPointAgent."""
        return PowerPointAgent(
            graph_client=mock_graph_client,
            authenticator=mock_authenticator
        )

    @pytest.mark.asyncio
    async def test_init(self, powerpoint_agent):
        """Test inicialización de PowerPointAgent."""
        assert powerpoint_agent.graph_client is not None
        assert powerpoint_agent.authenticator is not None
        assert powerpoint_agent.base_url == "https://graph.microsoft.com/v1.0"

    @pytest.mark.asyncio
    async def test_create_presentation(self, powerpoint_agent, sample_pptx_content, mock_graph_client):
        """Test creación de presentación."""
        mock_response = {
            "id": "test-presentation-id",
            "name": "Test Presentation.pptx",
            "webUrl": "https://powerpoint.com/edit/test-presentation-id"
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await powerpoint_agent.create_presentation(
            title=sample_pptx_content["title"],
            slides=sample_pptx_content["slides"]
        )
        
        assert result["id"] == "test-presentation-id"
        assert result["name"] == "Test Presentation.pptx"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_presentation(self, powerpoint_agent, mock_graph_client):
        """Test obtención de presentación."""
        presentation_id = "test-presentation-id"
        mock_response = {
            "id": presentation_id,
            "name": "Test Presentation.pptx",
            "slides": [{"id": "slide-1", "layout": "title_slide"}]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await powerpoint_agent.get_presentation(presentation_id)
        
        assert result["id"] == presentation_id
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_slide(self, powerpoint_agent, mock_graph_client):
        """Test adición de diapositiva."""
        presentation_id = "test-presentation-id"
        slide_data = {
            "layout": "title_content",
            "title": "New Slide",
            "content": "Slide content here"
        }
        
        mock_response = {
            "id": "slide-2",
            "layout": "title_content",
            "position": 2
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await powerpoint_agent.add_slide(
            presentation_id=presentation_id,
            **slide_data
        )
        
        assert result["id"] == "slide-2"
        assert result["position"] == 2
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_slide(self, powerpoint_agent, mock_graph_client):
        """Test eliminación de diapositiva."""
        presentation_id = "test-presentation-id"
        slide_id = "slide-2"
        
        mock_response = {"status": "204"}
        mock_graph_client.delete.return_value = mock_response
        
        result = await powerpoint_agent.delete_slide(
            presentation_id=presentation_id,
            slide_id=slide_id
        )
        
        assert result["status"] == "204"
        mock_graph_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_slide_layout(self, powerpoint_agent, mock_graph_client):
        """Test actualización de diseño de diapositiva."""
        presentation_id = "test-presentation-id"
        slide_id = "slide-2"
        new_layout = "two_content"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await powerpoint_agent.update_slide_layout(
            presentation_id=presentation_id,
            slide_id=slide_id,
            layout=new_layout
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_slide_title(self, powerpoint_agent, mock_graph_client):
        """Test establecimiento de título de diapositiva."""
        presentation_id = "test-presentation-id"
        slide_id = "slide-2"
        title = "Updated Slide Title"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await powerpoint_agent.set_slide_title(
            presentation_id=presentation_id,
            slide_id=slide_id,
            title=title
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_text_box(self, powerpoint_agent, mock_graph_client):
        """Test adición de cuadro de texto."""
        presentation_id = "test-presentation-id"
        slide_id = "slide-2"
        text_data = {
            "text": "Text content",
            "position": {"x": 100, "y": 200},
            "size": {"width": 300, "height": 50}
        }
        
        mock_response = {
            "id": "textbox-1",
            "text": "Text content",
            "position": {"x": 100, "y": 200}
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await powerpoint_agent.add_text_box(
            presentation_id=presentation_id,
            slide_id=slide_id,
            **text_data
        )
        
        assert result["id"] == "textbox-1"
        assert result["text"] == "Text content"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_image(self, powerpoint_agent, mock_graph_client):
        """Test adición de imagen."""
        presentation_id = "test-presentation-id"
        slide_id = "slide-2"
        image_data = {
            "image_url": "https://example.com/image.png",
            "position": {"x": 50, "y": 100},
            "size": {"width": 200, "height": 150}
        }
        
        mock_response = {
            "id": "image-1",
            "name": "image.png",
            "position": {"x": 50, "y": 100}
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await powerpoint_agent.add_image(
            presentation_id=presentation_id,
            slide_id=slide_id,
            **image_data
        )
        
        assert result["id"] == "image-1"
        assert result["name"] == "image.png"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_shape(self, powerpoint_agent, mock_graph_client):
        """Test adición de forma."""
        presentation_id = "test-presentation-id"
        slide_id = "slide-2"
        shape_data = {
            "shape_type": "rectangle",
            "position": {"x": 100, "y": 150},
            "size": {"width": 100, "height": 80},
            "fill_color": "#FF0000"
        }
        
        mock_response = {
            "id": "shape-1",
            "shapeType": "rectangle",
            "position": {"x": 100, "y": 150}
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await powerpoint_agent.add_shape(
            presentation_id=presentation_id,
            slide_id=slide_id,
            **shape_data
        )
        
        assert result["id"] == "shape-1"
        assert result["shapeType"] == "rectangle"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_chart(self, powerpoint_agent, mock_graph_client):
        """Test adición de gráfico."""
        presentation_id = "test-presentation-id"
        slide_id = "slide-2"
        chart_data = {
            "chart_type": "column",
            "data": {
                "categories": ["Q1", "Q2", "Q3", "Q4"],
                "series": [{"name": "Sales", "values": [100, 150, 200, 175]}]
            },
            "position": {"x": 50, "y": 200},
            "size": {"width": 400, "height": 300}
        }
        
        mock_response = {
            "id": "chart-1",
            "chartType": "columnChart",
            "position": {"x": 50, "y": 200}
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await powerpoint_agent.add_chart(
            presentation_id=presentation_id,
            slide_id=slide_id,
            **chart_data
        )
        
        assert result["id"] == "chart-1"
        assert result["chartType"] == "columnChart"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_theme(self, powerpoint_agent, mock_graph_client):
        """Test aplicación de tema."""
        presentation_id = "test-presentation-id"
        theme_name = "corporate_blue"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await powerpoint_agent.apply_theme(
            presentation_id=presentation_id,
            theme_name=theme_name
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_master_slide(self, powerpoint_agent, mock_graph_client):
        """Test aplicación de diapositiva maestra."""
        presentation_id = "test-presentation-id"
        master_slide_id = "master-1"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await powerpoint_agent.apply_master_slide(
            presentation_id=presentation_id,
            master_slide_id=master_slide_id
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_slide_transition(self, powerpoint_agent, mock_graph_client):
        """Test establecimiento de transición de diapositiva."""
        presentation_id = "test-presentation-id"
        slide_id = "slide-2"
        transition_data = {
            "type": "fade",
            "duration": 0.5,
            "sound_effect": "applause"
        }
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await powerpoint_agent.set_slide_transition(
            presentation_id=presentation_id,
            slide_id=slide_id,
            **transition_data
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_animation(self, powerpoint_agent, mock_graph_client):
        """Test adición de animación."""
        presentation_id = "test-presentation-id"
        slide_id = "slide-2"
        shape_id = "textbox-1"
        animation_data = {
            "type": "fade_in",
            "duration": 1.0,
            "delay": 0.5
        }
        
        mock_response = {
            "id": "animation-1",
            "animationType": "fadeIn",
            "duration": 1.0
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await powerpoint_agent.add_animation(
            presentation_id=presentation_id,
            slide_id=slide_id,
            shape_id=shape_id,
            **animation_data
        )
        
        assert result["id"] == "animation-1"
        assert result["animationType"] == "fadeIn"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_video(self, powerpoint_agent, mock_graph_client):
        """Test adición de video."""
        presentation_id = "test-presentation-id"
        slide_id = "slide-2"
        video_data = {
            "video_url": "https://example.com/video.mp4",
            "position": {"x": 100, "y": 200},
            "size": {"width": 320, "height": 240},
            "auto_play": True
        }
        
        mock_response = {
            "id": "video-1",
            "name": "video.mp4",
            "position": {"x": 100, "y": 200}
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await powerpoint_agent.add_video(
            presentation_id=presentation_id,
            slide_id=slide_id,
            **video_data
        )
        
        assert result["id"] == "video-1"
        assert result["name"] == "video.mp4"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_audio(self, powerpoint_agent, mock_graph_client):
        """Test adición de audio."""
        presentation_id = "test-presentation-id"
        slide_id = "slide-2"
        audio_data = {
            "audio_url": "https://example.com/audio.mp3",
            "auto_play": False,
            "loop": True
        }
        
        mock_response = {
            "id": "audio-1",
            "name": "audio.mp3",
            "autoPlay": False
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await powerpoint_agent.add_audio(
            presentation_id=presentation_id,
            slide_id=slide_id,
            **audio_data
        )
        
        assert result["id"] == "audio-1"
        assert result["name"] == "audio.mp3"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_slide_notes(self, powerpoint_agent, mock_graph_client):
        """Test establecimiento de notas de diapositiva."""
        presentation_id = "test-presentation-id"
        slide_id = "slide-2"
        notes_text = "Speaker notes for this slide"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await powerpoint_agent.set_slide_notes(
            presentation_id=presentation_id,
            slide_id=slide_id,
            notes_text=notes_text
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_duplicate_slide(self, powerpoint_agent, mock_graph_client):
        """Test duplicación de diapositiva."""
        presentation_id = "test-presentation-id"
        source_slide_id = "slide-1"
        
        mock_response = {
            "id": "slide-3",
            "layout": "title_slide",
            "position": 3
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await powerpoint_agent.duplicate_slide(
            presentation_id=presentation_id,
            source_slide_id=source_slide_id
        )
        
        assert result["id"] == "slide-3"
        assert result["position"] == 3
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_reorder_slides(self, powerpoint_agent, mock_graph_client):
        """Test reordenamiento de diapositivas."""
        presentation_id = "test-presentation-id"
        slide_orders = [
            {"slide_id": "slide-2", "new_position": 1},
            {"slide_id": "slide-1", "new_position": 2}
        ]
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await powerpoint_agent.reorder_slides(
            presentation_id=presentation_id,
            slide_orders=slide_orders
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_presentation_statistics(self, powerpoint_agent, mock_graph_client):
        """Test obtención de estadísticas de presentación."""
        presentation_id = "test-presentation-id"
        mock_response = {
            "slide_count": 10,
            "total_shapes": 45,
            "images_count": 8,
            "charts_count": 3,
            "videos_count": 1,
            "animations_count": 12
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await powerpoint_agent.get_presentation_statistics(presentation_id)
        
        assert result["slide_count"] == 10
        assert result["total_shapes"] == 45
        assert result["images_count"] == 8

    @pytest.mark.asyncio
    async def test_export_to_pdf(self, powerpoint_agent, mock_graph_client):
        """Test exportación a PDF."""
        presentation_id = "test-presentation-id"
        
        mock_response = {"@microsoft.graph.downloadUrl": "https://download-url.pdf"}
        mock_graph_client.get.return_value = mock_response
        
        result = await powerpoint_agent.export_to_pdf(presentation_id)
        
        assert "@microsoft.graph.downloadUrl" in result
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_to_video(self, powerpoint_agent, mock_graph_client):
        """Test exportación a video."""
        presentation_id = "test-presentation-id"
        export_options = {
            "format": "mp4",
            "quality": "high",
            "include_animations": True
        }
        
        mock_response = {
            "id": "export-1",
            "status": "processing",
            "progress": 0
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await powerpoint_agent.export_to_video(
            presentation_id=presentation_id,
            **export_options
        )
        
        assert result["id"] == "export-1"
        assert result["status"] == "processing"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_share_presentation(self, powerpoint_agent, mock_graph_client):
        """Test compartir presentación."""
        presentation_id = "test-presentation-id"
        user_email = "user@example.com"
        permission = "view"
        
        mock_response = {"status": "201"}
        mock_graph_client.post.return_value = mock_response
        
        result = await powerpoint_agent.share_presentation(
            presentation_id=presentation_id,
            user_email=user_email,
            permission=permission
        )
        
        assert result["status"] == "201"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_template(self, powerpoint_agent, mock_graph_client):
        """Test creación de plantilla."""
        template_data = {
            "name": "Corporate Template",
            "description": "Professional corporate presentation template",
            "slides": [
                {
                    "layout": "title_slide",
                    "name": "Title Slide",
                    "locked": True
                },
                {
                    "layout": "content",
                    "name": "Content Slide",
                    "locked": False
                }
            ]
        }
        
        mock_response = {
            "id": "template-1",
            "name": "Corporate Template",
            "created": True
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await powerpoint_agent.create_template(**template_data)
        
        assert result["id"] == "template-1"
        assert result["name"] == "Corporate Template"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_template(self, powerpoint_agent, mock_graph_client):
        """Test aplicación de plantilla."""
        presentation_id = "test-presentation-id"
        template_id = "template-1"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await powerpoint_agent.apply_template(
            presentation_id=presentation_id,
            template_id=template_id
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_slide_number(self, powerpoint_agent, mock_graph_client):
        """Test adición de número de diapositiva."""
        presentation_id = "test-presentation-id"
        slide_id = "slide-2"
        position = "bottom_right"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await powerpoint_agent.add_slide_number(
            presentation_id=presentation_id,
            slide_id=slide_id,
            position=position
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_slide_background(self, powerpoint_agent, mock_graph_client):
        """Test establecimiento de fondo de diapositiva."""
        presentation_id = "test-presentation-id"
        slide_id = "slide-2"
        background_data = {
            "type": "gradient",
            "color1": "#FFFFFF",
            "color2": "#CCCCCC"
        }
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await powerpoint_agent.set_slide_background(
            presentation_id=presentation_id,
            slide_id=slide_id,
            **background_data
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_network_error(self, powerpoint_agent, error_scenarios):
        """Test manejo de errores de red."""
        powerpoint_agent.graph_client.get.side_effect = error_scenarios["network_error"]
        
        with pytest.raises(Exception) as exc_info:
            await powerpoint_agent.get_presentation("test-presentation-id")
        
        assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_error_handling_invalid_layout(self, powerpoint_agent, mock_graph_client):
        """Test manejo de layout inválido."""
        powerpoint_agent.graph_client.post.side_effect = Exception("Invalid layout")
        
        with pytest.raises(Exception) as exc_info:
            await powerpoint_agent.add_slide(
                presentation_id="test-id",
                layout="invalid_layout",
                title="Test"
            )
        
        assert "Invalid layout" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, powerpoint_agent, rate_limit_responses):
        """Test manejo de rate limiting."""
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return rate_limit_responses["rate_limited"]
            return rate_limit_responses["success"]
        
        powerpoint_agent.graph_client.get.side_effect = side_effect
        
        with patch.object(powerpoint_agent, '_retry_with_backoff') as mock_retry:
            mock_retry.return_value = rate_limit_responses["success"]
            
            result = await powerpoint_agent.get_presentation("test-presentation-id")
            
            assert mock_retry.called

    @pytest.mark.asyncio
    async def test_batch_slide_operations(self, powerpoint_agent, mock_graph_client):
        """Test operaciones en lote de diapositivas."""
        presentation_id = "test-presentation-id"
        operations = [
            {"method": "POST", "url": f"/presentations/{presentation_id}/slides", "body": {"layout": "title_content"}},
            {"method": "POST", "url": f"/presentations/{presentation_id}/slides", "body": {"layout": "content"}},
            {"method": "PATCH", "url": f"/presentations/{presentation_id}/slides/slide-1", "body": {"title": "Updated"}}
        ]
        
        mock_responses = [
            {"id": "slide-2", "status": "201"},
            {"id": "slide-3", "status": "201"},
            {"status": "204"}
        ]
        mock_graph_client.batch_request.return_value = mock_responses
        
        results = await powerpoint_agent.batch_slide_operations(operations)
        
        assert len(results) == 3
        assert results[0]["id"] == "slide-2"

    @pytest.mark.asyncio
    async def test_search_in_presentation(self, powerpoint_agent, mock_graph_client):
        """Test búsqueda en presentación."""
        presentation_id = "test-presentation-id"
        search_term = "Introduction"
        
        mock_response = {
            "matches": [
                {
                    "slide_id": "slide-1",
                    "text": "Introduction to the topic",
                    "position": "title"
                },
                {
                    "slide_id": "slide-3",
                    "text": "Introduction Summary",
                    "position": "content"
                }
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await powerpoint_agent.search_in_presentation(
            presentation_id=presentation_id,
            search_term=search_term
        )
        
        assert len(result["matches"]) == 2
        assert all("slide_id" in match for match in result["matches"])

    @pytest.mark.asyncio
    async def test_auto_layout_slides(self, powerpoint_agent, mock_graph_client):
        """Test auto-layout de diapositivas."""
        presentation_id = "test-presentation-id"
        layout_strategy = "balanced"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await powerpoint_agent.auto_layout_slides(
            presentation_id=presentation_id,
            layout_strategy=layout_strategy
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_text_content(self, powerpoint_agent, mock_graph_client):
        """Test extracción de contenido de texto."""
        presentation_id = "test-presentation-id"
        mock_response = {
            "slides": [
                {
                    "slide_id": "slide-1",
                    "title": "Welcome",
                    "content": ["Welcome to the presentation"]
                },
                {
                    "slide_id": "slide-2",
                    "title": "Agenda",
                    "content": ["Topic 1", "Topic 2", "Topic 3"]
                }
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await powerpoint_agent.extract_text_content(presentation_id)
        
        assert len(result["slides"]) == 2
        assert result["slides"][0]["title"] == "Welcome"
        assert "Welcome to the presentation" in result["slides"][0]["content"]