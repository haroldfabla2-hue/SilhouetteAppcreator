"""
Tests unitarios para Social Media Agent
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# Añadir el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.social_media_agent import (
    SocialMediaAgent, SocialPost, SocialMetrics, SocialPlatform, ContentType, PostStatus
)


class TestSocialMediaAgent:
    """Tests para SocialMediaAgent"""
    
    @pytest.fixture
    async def agent(self):
        """Fixture para crear agente de prueba"""
        agent = SocialMediaAgent()
        await agent._initialize()
        return agent
    
    def test_agent_initialization(self, agent):
        """Test inicialización del agente"""
        assert agent.agent_name == "SocialMediaAgent"
        assert agent.is_ready
        assert len(agent.capabilities) > 0
        assert len(agent._posts) > 0  # Debe cargar posts de ejemplo
        assert len(agent._metrics) > 0  # Debe cargar métricas de ejemplo
    
    def test_generate_hashtag_suggestions(self, agent):
        """Test generación de sugerencias de hashtags"""
        content = "Lanzamos nuestro nuevo producto de tecnología"
        hashtags = agent._generate_hashtag_suggestions(content, SocialPlatform.TWITTER)
        
        assert isinstance(hashtags, list)
        assert len(hashtags) > 0
        # Debe contener hashtags relevantes
        assert any("tech" in tag.lower() for tag in hashtags)
    
    @pytest.mark.asyncio
    async def test_create_post_basic(self, agent):
        """Test creación básica de post"""
        response = await agent.create_post(
            platform=SocialPlatform.TWITTER,
            content="¡Gran noticia! Acabamos de lanzar nuestro nuevo producto 🚀",
            content_type=ContentType.TEXT
        )
        
        assert response.success
        assert response.action == "create_post"
        assert response.platform == SocialPlatform.TWITTER
        assert response.post_id is not None
        assert len(response.details["hashtags_count"]) > 0  # Hashtags automáticos
    
    @pytest.mark.asyncio
    async def test_create_post_with_hashtags(self, agent):
        """Test creación de post con hashtags específicos"""
        hashtags = ["#lanzamiento", "#innovación", "#tech"]
        
        response = await agent.create_post(
            platform=SocialPlatform.INSTAGRAM,
            content="Nuestro nuevo producto revolucionará el mercado",
            content_type=ContentType.IMAGE,
            hashtags=hashtags
        )
        
        assert response.success
        post = agent._posts[response.post_id]
        assert post.hashtags == hashtags
        assert post.content_type == ContentType.IMAGE
    
    @pytest.mark.asyncio
    async def test_create_post_scheduled(self, agent):
        """Test creación de post programado"""
        scheduled_time = datetime.now() + timedelta(hours=2)
        
        response = await agent.create_post(
            platform=SocialPlatform.LINKEDIN,
            content="Contenido profesional para LinkedIn",
            scheduled_time=scheduled_time
        )
        
        assert response.success
        post = agent._posts[response.post_id]
        assert post.scheduled_time == scheduled_time
        assert post.status == PostStatus.SCHEDULED
    
    @pytest.mark.asyncio
    async def test_publish_post(self, agent):
        """Test publicación de post"""
        # Primero crear un post
        create_response = await agent.create_post(
            platform=SocialPlatform.TWITTER,
            content="Post para publicar"
        )
        
        post_id = create_response.post_id
        
        # Luego publicarlo
        publish_response = await agent.publish_post(post_id)
        
        assert publish_response.success
        assert publish_response.action == "publish_post"
        
        # Verificar que el post fue publicado
        post = agent._posts[post_id]
        assert post.status == PostStatus.PUBLISHED
        assert post.published_time is not None
        assert len(post.engagement_metrics) > 0
    
    @pytest.mark.asyncio
    async def test_publish_post_not_found(self, agent):
        """Test publicación de post inexistente"""
        response = await agent.publish_post("nonexistent_post_id")
        
        assert not response.success
        assert "no encontrado" in response.error
    
    @pytest.mark.asyncio
    async def test_schedule_posts_batch(self, agent):
        """Test programación de múltiples posts"""
        posts_data = [
            {
                "platform": "twitter",
                "content": "Post 1 para Twitter",
                "content_type": "text"
            },
            {
                "platform": "instagram", 
                "content": "Post 2 para Instagram",
                "content_type": "image"
            },
            {
                "platform": "linkedin",
                "content": "Post 3 para LinkedIn",
                "content_type": "text"
            }
        ]
        
        response = await agent.schedule_posts(posts_data, schedule_type="optimal")
        
        assert response.success
        assert response.action == "schedule_posts"
        assert len(response.details["post_ids"]) == 3
        assert response.details["posts_created"] == 3
    
    @pytest.mark.asyncio
    async def test_get_analytics_single_platform(self, agent):
        """Test obtención de analíticas de una plataforma"""
        response = await agent.get_analytics(
            platform=SocialPlatform.INSTAGRAM,
            date_range=30
        )
        
        assert response.success
        assert response.action == "get_analytics"
        assert SocialPlatform.INSTAGRAM.value in response.details["analytics"]
        
        analytics_data = response.details["analytics"][SocialPlatform.INSTAGRAM.value]
        assert "current_metrics" in analytics_data
        assert "historical_data" in analytics_data
        assert "trends" in analytics_data
        
        # Verificar métricas actuales
        current_metrics = analytics_data["current_metrics"]
        assert "followers" in current_metrics
        assert "engagement_rate" in current_metrics
        assert current_metrics["followers"] > 0
    
    @pytest.mark.asyncio
    async def test_get_analytics_all_platforms(self, agent):
        """Test obtención de analíticas de todas las plataformas"""
        response = await agent.get_analytics(date_range=7)
        
        assert response.success
        # Debe incluir datos de todas las plataformas
        analytics = response.details["analytics"]
        assert len(analytics) == len(agent._metrics)
    
    @pytest.mark.asyncio
    async def test_analyze_hashtags(self, agent):
        """Test análisis de hashtags"""
        hashtags = ["#tech", "#innovation", "#startup"]
        platforms = [SocialPlatform.TWITTER, SocialPlatform.INSTAGRAM]
        
        response = await agent.analyze_hashtags(hashtags, platforms)
        
        assert response.success
        assert response.action == "analyze_hashtags"
        assert response.details["hashtags_analyzed"] == len(hashtags)
        
        analysis = response.details["analysis"]
        assert "#tech" in analysis
        
        tech_analysis = analysis["#tech"]
        assert "popularity_score" in tech_analysis
        assert "competition_level" in tech_analysis
        assert "engagement_potential" in tech_analysis
        assert "related_hashtags" in tech_analysis
    
    @pytest.mark.asyncio
    async def test_analyze_hashtags_default_platforms(self, agent):
        """Test análisis de hashtags con plataformas por defecto"""
        hashtags = ["#marketing", "#digital"]
        
        response = await agent.analyze_hashtags(hashtags)
        
        assert response.success
        # Debe usar plataformas por defecto (Instagram y Twitter)
        assert response.details["platforms"] == ["instagram", "twitter"]
    
    @pytest.mark.asyncio
    async def test_process_request_create_post(self, agent):
        """Test procesamiento de request de creación de post"""
        request = {
            "action": "create_post",
            "platform": "twitter",
            "content": "Test post content",
            "content_type": "text",
            "hashtags": ["#test", "#social"]
        }
        
        response = await agent.process_request(request)
        
        assert response["success"]
        assert "post_id" in response
        assert "details" in response
    
    @pytest.mark.asyncio
    async def test_process_request_publish_post(self, agent):
        """Test procesamiento de request de publicación"""
        # Primero crear un post
        create_request = {
            "action": "create_post",
            "platform": "twitter",
            "content": "Post to publish"
        }
        create_response = await agent.process_request(create_request)
        
        # Luego publicarlo
        publish_request = {
            "action": "publish_post",
            "post_id": create_response["post_id"]
        }
        publish_response = await agent.process_request(publish_request)
        
        assert publish_response["success"]
        assert "post_id" in publish_response
    
    @pytest.mark.asyncio
    async def test_process_request_schedule_posts(self, agent):
        """Test procesamiento de request de programación de posts"""
        request = {
            "action": "schedule_posts",
            "posts": [
                {
                    "platform": "twitter",
                    "content": "Scheduled post 1"
                },
                {
                    "platform": "instagram",
                    "content": "Scheduled post 2",
                    "content_type": "image"
                }
            ],
            "schedule_type": "optimal"
        }
        
        response = await agent.process_request(request)
        
        assert response["success"]
        assert "post_ids" in response
        assert "created_count" in response
        assert response["created_count"] == 2
    
    @pytest.mark.asyncio
    async def test_process_request_get_analytics(self, agent):
        """Test procesamiento de request de analíticas"""
        request = {
            "action": "get_analytics",
            "platform": "instagram",
            "date_range": 30
        }
        
        response = await agent.process_request(request)
        
        assert response["success"]
        assert "analytics" in response
        assert "platforms_count" in response
    
    @pytest.mark.asyncio
    async def test_process_request_analyze_hashtags(self, agent):
        """Test procesamiento de request de análisis de hashtags"""
        request = {
            "action": "analyze_hashtags",
            "hashtags": ["#tech", "#ai", "#startup"],
            "platforms": ["twitter", "linkedin"]
        }
        
        response = await agent.process_request(request)
        
        assert response["success"]
        assert "analysis" in response
        assert "hashtags_analyzed" in response
        assert response["hashtags_analyzed"] == 3
    
    def test_get_stats(self, agent):
        """Test obtención de estadísticas"""
        stats = agent.get_stats()
        
        assert "agent_name" in stats
        assert "total_posts" in stats
        assert "scheduled_posts" in stats
        assert "platforms_count" in stats
        assert "supported_platforms" in stats
        assert "available_actions" in stats
        
        # Verificar plataformas soportadas
        platforms = stats["supported_platforms"]
        assert "twitter" in platforms
        assert "instagram" in platforms
        assert "linkedin" in platforms
        
        # Verificar acciones disponibles
        actions = stats["available_actions"]
        assert "create_post" in actions
        assert "publish_post" in actions
        assert "schedule_posts" in actions
        assert "get_analytics" in actions
        assert "analyze_hashtags" in actions


class TestSocialPost:
    """Tests para SocialPost"""
    
    def test_social_post_creation(self):
        """Test creación de post social"""
        post = SocialPost(
            id="post_123",
            platform=SocialPlatform.TWITTER,
            content_type=ContentType.TEXT,
            text="Test post content",
            hashtags=["#test", "#social"],
            mentions=["@user1"]
        )
        
        assert post.id == "post_123"
        assert post.platform == SocialPlatform.TWITTER
        assert post.content_type == ContentType.TEXT
        assert post.text == "Test post content"
        assert "#test" in post.hashtags
        assert "@user1" in post.mentions
        assert post.status == PostStatus.DRAFT
    
    def test_social_post_with_media(self):
        """Test creación de post con medios"""
        post = SocialPost(
            id="post_456",
            platform=SocialPlatform.INSTAGRAM,
            content_type=ContentType.IMAGE,
            text="Beautiful sunset photo",
            media_urls=["https://example.com/sunset.jpg"]
        )
        
        assert post.content_type == ContentType.IMAGE
        assert "https://example.com/sunset.jpg" in post.media_urls


class TestSocialMetrics:
    """Tests para SocialMetrics"""
    
    def test_social_metrics_creation(self):
        """Test creación de métricas sociales"""
        metrics = SocialMetrics(
            platform=SocialPlatform.TWITTER,
            followers=10000,
            following=500,
            posts_count=200,
            engagement_rate=4.5
        )
        
        assert metrics.platform == SocialPlatform.TWITTER
        assert metrics.followers == 10000
        assert metrics.following == 500
        assert metrics.posts_count == 200
        assert metrics.engagement_rate == 4.5
        assert metrics.last_updated is not None


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v"])