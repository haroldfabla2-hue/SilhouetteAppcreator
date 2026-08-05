"""
Tests unitarios para Content Creation Agent
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# Añadir el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.content_creation_agent import (
    ContentCreationAgent, ContentPiece, ImageContent, VideoContent, AudioContent,
    ContentTemplate, ContentType, ContentStatus, Platform
)


class TestContentCreationAgent:
    """Tests para ContentCreationAgent"""
    
    @pytest.fixture
    async def agent(self):
        """Fixture para crear agente de prueba"""
        agent = ContentCreationAgent()
        await agent._initialize()
        return agent
    
    def test_agent_initialization(self, agent):
        """Test inicialización del agente"""
        assert agent.agent_name == "ContentCreationAgent"
        assert agent.is_ready
        assert len(agent.capabilities) > 0
        assert len(agent._content_pieces) > 0  # Debe cargar contenido de ejemplo
        assert len(agent._templates) > 0  # Debe cargar plantillas de ejemplo
    
    @pytest.mark.asyncio
    async def test_generate_image_basic(self, agent):
        """Test generación básica de imagen"""
        image_data = {
            "prompt": "Un hermoso paisaje de montañas al atardecer",
            "content_type": "social_media",
            "platform": "instagram",
            "style": "photorealistic"
        }
        
        image = await agent.generate_image(**image_data)
        
        assert isinstance(image, ImageContent)
        assert image.prompt == image_data["prompt"]
        assert image.platform == Platform.INSTAGRAM
        assert image.content_type == ContentType.SOCIAL_MEDIA
        assert image.status == ContentStatus.GENERATED
        assert image.file_path is not None
    
    @pytest.mark.asyncio
    async def test_generate_image_with_dimensions(self, agent):
        """Test generación de imagen con dimensiones específicas"""
        image_data = {
            "prompt": "Logo empresarial moderno",
            "content_type": "branding",
            "platform": "website",
            "width": 800,
            "height": 600,
            "style": "vector"
        }
        
        image = await agent.generate_image(**image_data)
        
        assert isinstance(image, ImageContent)
        assert image.width == 800
        assert image.height == 600
        assert image.style == "vector"
    
    @pytest.mark.asyncio
    async def test_generate_video_basic(self, agent):
        """Test generación básica de video"""
        video_data = {
            "prompt": "Demostración de producto tecnológico",
            "content_type": "marketing",
            "platform": "youtube",
            "duration": 30
        }
        
        video = await agent.generate_video(**video_data)
        
        assert isinstance(video, VideoContent)
        assert video.prompt == video_data["prompt"]
        assert video.platform == Platform.YOUTUBE
        assert video.content_type == ContentType.MARKETING
        assert video.duration == 30
        assert video.status == ContentStatus.GENERATED
    
    @pytest.mark.asyncio
    async def test_generate_video_from_image(self, agent):
        """Test generación de video a partir de imagen"""
        # Primero generar una imagen
        image_data = {
            "prompt": "Imagen base para video",
            "content_type": "social_media",
            "platform": "instagram"
        }
        
        image = await agent.generate_image(**image_data)
        
        # Luego generar video a partir de la imagen
        video_data = {
            "image_path": image.file_path,
            "prompt": "Agregar movimiento y efectos",
            "duration": 15
        }
        
        video = await agent.generate_video_from_image(**video_data)
        
        assert isinstance(video, VideoContent)
        assert video.source_image == image.file_path
        assert video.duration == 15
        assert video.status == ContentStatus.GENERATED
    
    @pytest.mark.asyncio
    async def test_edit_image_basic(self, agent):
        """Test edición básica de imagen"""
        # Primero generar una imagen
        image_data = {
            "prompt": "Foto de paisaje natural",
            "content_type": "photography",
            "platform": "website"
        }
        
        original_image = await agent.generate_image(**image_data)
        
        # Editar la imagen
        edit_prompt = "Cambiar el cielo a un tono más azul"
        edited_image = await agent.edit_image(original_image.file_path, edit_prompt)
        
        assert isinstance(edited_image, ImageContent)
        assert edited_image.original_path == original_image.file_path
        assert edited_image.prompt == edit_prompt
        assert edited_image.status == ContentStatus.EDITED
    
    @pytest.mark.asyncio
    async def test_create_social_media_post(self, agent):
        """Test creación de post para redes sociales"""
        post_data = {
            "content": "¡Nuevo producto lanzado! 🚀 #innovación #tecnología",
            "platform": "instagram",
            "content_type": "announcement"
        }
        
        post = await agent.create_social_media_post(**post_data)
        
        assert isinstance(post, ContentPiece)
        assert post.content == post_data["content"]
        assert post.platform == Platform.INSTAGRAM
        assert post.content_type == ContentType.ANNOUNCEMENT
        assert post.status == ContentStatus.CREATED
    
    @pytest.mark.asyncio
    async def test_create_blog_article(self, agent):
        """Test creación de artículo de blog"""
        article_data = {
            "title": "Guía Completa de Marketing Digital",
            "topic": "marketing digital",
            "target_audience": "empresarios",
            "word_count": 1500,
            "tone": "profesional"
        }
        
        article = await agent.create_blog_article(**article_data)
        
        assert isinstance(article, ContentPiece)
        assert article.title == article_data["title"]
        assert article.topic == article_data["topic"]
        assert article.target_audience == article_data["target_audience"]
        assert article.content_type == ContentType.ARTICLE
        assert len(article.content) > 0  # Debe tener contenido generado
    
    @pytest.mark.asyncio
    async def test_generate_script(self, agent):
        """Test generación de guión"""
        script_data = {
            "type": "commercial",
            "product": "Smartphone X1",
            "duration": 60,
            "target_audience": "jóvenes adultos"
        }
        
        script = await agent.generate_script(**script_data)
        
        assert isinstance(script, ContentPiece)
        assert script.title == "Guión Comercial - Smartphone X1"
        assert script.topic == "commercial"
        assert script.content_type == ContentType.SCRIPT
        assert len(script.content) > 0  # Debe tener el guión generado
        assert script.duration == 60
    
    @pytest.mark.asyncio
    async def test_process_audio_basic(self, agent):
        """Test procesamiento básico de audio"""
        audio_data = {
            "text": "Bienvenidos a nuestro podcast semanal",
            "voice": "professional_male",
            "language": "spanish",
            "output_format": "mp3"
        }
        
        audio = await agent.process_audio(**audio_data)
        
        assert isinstance(audio, AudioContent)
        assert audio.text == audio_data["text"]
        assert audio.voice == "professional_male"
        assert audio.language == "spanish"
        assert audio.output_format == "mp3"
        assert audio.status == ContentStatus.PROCESSED
        assert audio.file_path is not None
    
    @pytest.mark.asyncio
    async def test_apply_template_basic(self, agent):
        """Test aplicación básica de plantilla"""
        # Primero seleccionar una plantilla existente
        template = agent._templates[0]
        
        template_data = {
            "template_id": template.id,
            "title": "Mi Post Personalizado",
            "content": "Contenido específico para el post",
            "brand_colors": ["#FF5733", "#33FF57"]
        }
        
        templated_content = await agent.apply_template(**template_data)
        
        assert isinstance(templated_content, ContentPiece)
        assert templated_content.template_id == template.id
        assert templated_content.title == template_data["title"]
        assert templated_content.status == ContentStatus.TEMPLATED
    
    @pytest.mark.asyncio
    async def test_apply_template_nonexistent(self, agent):
        """Test aplicación de plantilla inexistente"""
        with pytest.raises(ValueError, match="Plantilla no encontrada"):
            await agent.apply_template(
                template_id="nonexistent_template",
                title="Test",
                content="Test Content"
            )
    
    @pytest.mark.asyncio
    async def test_optimize_content_for_platform(self, agent):
        """Test optimización de contenido para plataforma"""
        # Crear contenido primero
        content_data = {
            "content": "Este es un contenido muy largo que necesita ser optimizado para diferentes plataformas y adaptaciones específicas de cada red social.",
            "content_type": "social_media",
            "platform": "facebook"
        }
        
        content = await agent.create_social_media_post(**content_data)
        
        # Optimizar para Instagram
        optimized = await agent.optimize_content_for_platform(content.id, "instagram")
        
        assert isinstance(optimized, ContentPiece)
        assert optimized.id != content.id  # Debe ser una copia nueva
        assert optimized.platform == Platform.INSTAGRAM
        # El contenido debe estar optimizado (más corto)
        assert len(optimized.content) <= len(content.content)
    
    @pytest.mark.asyncio
    async def test_create_content_calendar(self, agent):
        """Test creación de calendario de contenido"""
        calendar_data = {
            "start_date": "2024-12-01",
            "end_date": "2024-12-31",
            "platform": "instagram",
            "content_types": ["announcement", "educational", "entertainment"],
            "posts_per_week": 3
        }
        
        calendar = await agent.create_content_calendar(**calendar_data)
        
        assert isinstance(calendar, list)
        assert len(calendar) > 0
        
        # Verificar que los elementos son ContentPiece
        first_item = calendar[0]
        assert isinstance(first_item, ContentPiece)
        
        # Verificar que están en el rango de fechas
        start_range = datetime.strptime(calendar_data["start_date"], "%Y-%m-%d")
        end_range = datetime.strptime(calendar_data["end_date"], "%Y-%m-%d")
        
        for item in calendar:
            item_date = datetime.fromisoformat(item.created_at.replace('Z', '+00:00'))
            assert start_range <= item_date <= end_range
    
    @pytest.mark.asyncio
    async def test_batch_generate_content(self, agent):
        """Test generación por lotes de contenido"""
        batch_data = {
            "content_list": [
                {
                    "type": "image",
                    "prompt": "Paisaje de montañas",
                    "platform": "instagram"
                },
                {
                    "type": "video",
                    "prompt": "Demo de producto",
                    "platform": "youtube"
                },
                {
                    "type": "text",
                    "content": "Post informativo",
                    "platform": "facebook"
                }
            ]
        }
        
        results = await agent.batch_generate_content(**batch_data)
        
        assert isinstance(results, list)
        assert len(results) == len(batch_data["content_list"])
        
        # Verificar que cada resultado es del tipo correcto
        for i, result in enumerate(results):
            content_type = batch_data["content_list"][i]["type"]
            if content_type == "image":
                assert isinstance(result, ImageContent)
            elif content_type == "video":
                assert isinstance(result, VideoContent)
            elif content_type == "text":
                assert isinstance(result, ContentPiece)
    
    @pytest.mark.asyncio
    async def test_translate_content(self, agent):
        """Test traducción de contenido"""
        # Crear contenido en español
        content_data = {
            "content": "Este es un contenido en español que necesita ser traducido al inglés",
            "content_type": "social_media",
            "platform": "instagram"
        }
        
        content = await agent.create_social_media_post(**content_data)
        
        # Traducir al inglés
        translated = await agent.translate_content(content.id, "english")
        
        assert isinstance(translated, ContentPiece)
        assert translated.id != content.id  # Debe ser una nueva pieza
        assert translated.language == "english"
        assert translated.content != content.content  # El contenido debe ser diferente
    
    @pytest.mark.asyncio
    async def test_add_brand_elements(self, agent):
        """Test adición de elementos de marca"""
        # Crear imagen primero
        image_data = {
            "prompt": "Imagen corporativa",
            "content_type": "branding",
            "platform": "website"
        }
        
        image = await agent.generate_image(**image_data)
        
        # Agregar elementos de marca
        brand_data = {
            "logo_path": "path/to/logo.png",
            "brand_colors": ["#FF0000", "#00FF00", "#0000FF"],
            "brand_font": "Arial"
        }
        
        branded_image = await agent.add_brand_elements(image.id, **brand_data)
        
        assert isinstance(branded_image, ImageContent)
        assert branded_image.logo_path == brand_data["logo_path"]
        assert branded_image.brand_colors == brand_data["brand_colors"]
        assert branded_image.brand_font == brand_data["brand_font"]
    
    @pytest.mark.asyncio
    async def test_generate_content_ideas(self, agent):
        """Test generación de ideas de contenido"""
        ideas_data = {
            "topic": "tecnología",
            "platform": "instagram",
            "content_type": "educational",
            "count": 5
        }
        
        ideas = await agent.generate_content_ideas(**ideas_data)
        
        assert isinstance(ideas, list)
        assert len(ideas) == ideas_data["count"]
        
        # Verificar que cada idea es un ContentPiece
        for idea in ideas:
            assert isinstance(idea, ContentPiece)
            assert idea.topic == ideas_data["topic"]
            assert idea.platform == Platform.INSTAGRAM
            assert idea.content_type == ContentType.EDUCATIONAL
    
    @pytest.mark.asyncio
    async def test_analyze_content_performance(self, agent):
        """Test análisis de rendimiento de contenido"""
        # Usar contenido existente del setup
        content_id = agent._content_pieces[0].id
        
        analysis = await agent.analyze_content_performance(content_id)
        
        assert isinstance(analysis, dict)
        assert "engagement_score" in analysis
        assert "reach_potential" in analysis
        assert "optimization_suggestions" in analysis
        assert "content_quality_score" in analysis
        
        assert isinstance(analysis["engagement_score"], (int, float))
        assert isinstance(analysis["reach_potential"], (int, float))
        assert isinstance(analysis["content_quality_score"], (int, float))
        assert isinstance(analysis["optimization_suggestions"], list)
    
    @pytest.mark.asyncio
    async def test_get_content_by_platform(self, agent):
        """Test obtención de contenido por plataforma"""
        platform = "instagram"
        content = await agent.get_content_by_platform(platform)
        
        assert isinstance(content, list)
        
        # Verificar que todo el contenido pertenece a la plataforma
        for piece in content:
            assert piece.platform == Platform.INSTAGRAM
    
    @pytest.mark.asyncio
    async def test_get_content_by_type(self, agent):
        """Test obtención de contenido por tipo"""
        content_type = ContentType.SOCIAL_MEDIA
        content = await agent.get_content_by_type(content_type)
        
        assert isinstance(content, list)
        
        # Verificar que todo el contenido es del tipo especificado
        for piece in content:
            assert piece.content_type == content_type
    
    @pytest.mark.asyncio
    async def test_schedule_content(self, agent):
        """Test programación de contenido"""
        # Crear contenido primero
        content_data = {
            "content": "Post programado",
            "platform": "instagram",
            "content_type": "announcement"
        }
        
        content = await agent.create_social_media_post(**content_data)
        
        # Programar para una fecha futura
        schedule_data = {
            "content_id": content.id,
            "schedule_time": "2024-12-15T10:00:00"
        }
        
        scheduled_content = await agent.schedule_content(**schedule_data)
        
        assert isinstance(scheduled_content, ContentPiece)
        assert scheduled_content.scheduled_time == schedule_data["schedule_time"]
        assert scheduled_content.status == ContentStatus.SCHEDULED
    
    @pytest.mark.asyncio
    async def test_duplicate_content(self, agent):
        """Test duplicación de contenido"""
        # Usar contenido existente
        original_content = agent._content_pieces[0]
        
        duplicate = await agent.duplicate_content(original_content.id)
        
        assert isinstance(duplicate, ContentPiece)
        assert duplicate.id != original_content.id  # Debe tener ID diferente
        assert duplicate.title == f"Copia de {original_content.title}"
        assert duplicate.content == original_content.content
        assert duplicate.platform == original_content.platform
    
    @pytest.mark.asyncio
    async def test_delete_content(self, agent):
        """Test eliminación de contenido"""
        # Crear contenido primero
        content_data = {
            "content": "Contenido a eliminar",
            "platform": "facebook",
            "content_type": "social_media"
        }
        
        content = await agent.create_social_media_post(**content_data)
        content_id = content.id
        
        result = await agent.delete_content(content_id)
        assert result == True
        
        # Verificar que ya no existe
        all_content = await agent.get_content_by_platform("facebook")
        assert not any(c.id == content_id for c in all_content)
    
    @pytest.mark.asyncio
    async def test_export_content(self, agent):
        """Test exportación de contenido"""
        # Usar contenido existente
        content_id = agent._content_pieces[0].id
        
        exported = await agent.export_content(content_id, "pdf")
        
        assert isinstance(exported, dict)
        assert "file_path" in exported
        assert "format" in exported
        assert exported["format"] == "pdf"
        assert exported["file_path"] is not None
    
    @pytest.mark.asyncio
    async def test_get_content_analytics(self, agent):
        """Test obtención de análisis de contenido"""
        platform = "instagram"
        date_range = "2024-12-01,2024-12-31"
        
        analytics = await agent.get_content_analytics(platform, date_range)
        
        assert isinstance(analytics, dict)
        assert "total_posts" in analytics
        assert "engagement_rate" in analytics
        assert "top_performing_content" in analytics
        assert "content_types_distribution" in analytics
        assert "posting_frequency" in analytics
        
        assert isinstance(analytics["total_posts"], int)
        assert isinstance(analytics["engagement_rate"], (int, float))
        assert isinstance(analytics["top_performing_content"], list)
        assert isinstance(analytics["content_types_distribution"], dict)
    
    @pytest.mark.asyncio
    async def test_optimize_hashtags(self, agent):
        """Test optimización de hashtags"""
        content = "Lanzamos nuestro nuevo producto #innovación #tecnología"
        platform = "instagram"
        
        optimized = await agent.optimize_hashtags(content, platform)
        
        assert isinstance(optimized, str)
        # Debe incluir hashtags optimizados
        assert "#" in optimized
        assert len(optimized) > len(content)  # Debe tener más hashtags
    
    @pytest.mark.asyncio
    async def test_handle_exceptions_invalid_content_type(self, agent):
        """Test manejo de excepciones con tipo de contenido inválido"""
        with pytest.raises(ValueError, match="Tipo de contenido no soportado"):
            await agent.generate_image(
                prompt="Test Image",
                content_type="invalid_type",
                platform="instagram"
            )
    
    @pytest.mark.asyncio
    async def test_handle_exceptions_network_error(self, agent):
        """Test manejo de excepciones de red"""
        # Simular un error de red mockeando requests
        with patch('agents.content_creation_agent.requests.post') as mock_post:
            mock_post.side_effect = Exception("Error de red simulado")
            
            with pytest.raises(Exception):
                await agent.generate_image(
                    prompt="Test Image",
                    content_type="social_media",
                    platform="instagram"
                )


class TestContentDataClasses:
    """Tests para las clases de datos del agente de creación de contenido"""
    
    def test_content_piece_creation(self):
        """Test creación de objeto ContentPiece"""
        content = ContentPiece(
            id="content_test",
            title="Test Content",
            content="This is test content",
            content_type=ContentType.SOCIAL_MEDIA,
            platform=Platform.INSTAGRAM,
            status=ContentStatus.CREATED,
            created_at=datetime.now(),
            metadata={"test": "data"}
        )
        
        assert content.id == "content_test"
        assert content.title == "Test Content"
        assert content.content_type == ContentType.SOCIAL_MEDIA
        assert content.platform == Platform.INSTAGRAM
        assert content.status == ContentStatus.CREATED
    
    def test_image_content_creation(self):
        """Test creación de objeto ImageContent"""
        image = ImageContent(
            id="image_test",
            prompt="Test image prompt",
            content_type=ContentType.SOCIAL_MEDIA,
            platform=Platform.INSTAGRAM,
            status=ContentStatus.GENERATED,
            created_at=datetime.now(),
            file_path="/path/to/image.png",
            width=800,
            height=600,
            style="photorealistic"
        )
        
        assert image.id == "image_test"
        assert image.prompt == "Test image prompt"
        assert image.file_path == "/path/to/image.png"
        assert image.width == 800
        assert image.height == 600
        assert image.style == "photorealistic"
    
    def test_video_content_creation(self):
        """Test creación de objeto VideoContent"""
        video = VideoContent(
            id="video_test",
            prompt="Test video prompt",
            content_type=ContentType.MARKETING,
            platform=Platform.YOUTUBE,
            status=ContentStatus.GENERATED,
            created_at=datetime.now(),
            file_path="/path/to/video.mp4",
            duration=30,
            resolution="1080p",
            source_image="/path/to/source.jpg"
        )
        
        assert video.id == "video_test"
        assert video.prompt == "Test video prompt"
        assert video.file_path == "/path/to/video.mp4"
        assert video.duration == 30
        assert video.resolution == "1080p"
        assert video.source_image == "/path/to/source.jpg"
    
    def test_audio_content_creation(self):
        """Test creación de objeto AudioContent"""
        audio = AudioContent(
            id="audio_test",
            text="This is test audio text",
            content_type=ContentType.PODCAST,
            platform=Platform.SPOTIFY,
            status=ContentStatus.PROCESSED,
            created_at=datetime.now(),
            file_path="/path/to/audio.mp3",
            duration=120,
            voice="professional_male",
            language="spanish"
        )
        
        assert audio.id == "audio_test"
        assert audio.text == "This is test audio text"
        assert audio.file_path == "/path/to/audio.mp3"
        assert audio.duration == 120
        assert audio.voice == "professional_male"
        assert audio.language == "spanish"
    
    def test_content_template_creation(self):
        """Test creación de objeto ContentTemplate"""
        template = ContentTemplate(
            id="template_test",
            name="Test Template",
            description="Test template description",
            template_type="social_media_post",
            platform=Platform.INSTAGRAM,
            structure={"format": "post", "sections": ["header", "content", "footer"]},
            variables=["title", "content", "hashtags"]
        )
        
        assert template.id == "template_test"
        assert template.name == "Test Template"
        assert template.template_type == "social_media_post"
        assert template.platform == Platform.INSTAGRAM
        assert "format" in template.structure
        assert "title" in template.variables


if __name__ == "__main__":
    # Ejecutar tests específicos si se ejecuta directamente
    pytest.main([__file__, "-v"])