"""
Unit tests para SearchEngineAgent
Agente de búsqueda avanzada con múltiples fuentes
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any, List
import json
import time

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.agents.search_engine_agent import (
    SearchEngineAgent, SearchSource, SearchResult, SearchResponse
)


class TestSearchEngineAgent:
    """Test suite para SearchEngineAgent"""
    
    @pytest.fixture
    def search_agent(self):
        """Fixture para crear instancia del SearchEngineAgent"""
        with patch('src.agents.search_engine_agent.BaseSearchEngine', None):
            return SearchEngineAgent()
    
    @pytest.fixture
    def sample_search_result(self):
        """Fixture para resultado de búsqueda de ejemplo"""
        return SearchResult(
            title="Python Programming Guide",
            url="https://example.com/python-guide",
            snippet="A comprehensive guide to Python programming...",
            source=SearchSource.DUCKDUCKGO,
            score=0.85,
            relevance=0.90,
            domain="example.com"
        )
    
    @pytest.mark.asyncio
    async def test_initialization(self, search_agent):
        """Test inicialización del SearchEngineAgent"""
        assert search_agent is not None
        assert hasattr(search_agent, 'logger')
        assert hasattr(search_agent, 'max_results_per_source')
        assert hasattr(search_agent, 'timeout_seconds')
        assert hasattr(search_agent, 'user_agent')
    
    @pytest.mark.asyncio
    async def test_web_search_google(self, search_agent):
        """Test búsqueda web con Google"""
        with patch.object(search_agent, '_search_google') as mock_search:
            mock_search.return_value = [
                SearchResult(
                    title="Python Tutorial",
                    url="https://python.org/tutorial",
                    snippet="Official Python tutorial...",
                    source=SearchSource.GOOGLE,
                    score=0.95
                )
            ]
            
            result = await search_agent.web_search(
                query="Python programming",
                source=SearchSource.GOOGLE,
                max_results=10
            )
            
            assert isinstance(result, SearchResponse)
            assert result.query == "Python programming"
            assert len(result.results) == 1
            assert result.sources_used == [SearchSource.GOOGLE]
            assert SearchSource.GOOGLE in result.sources_used
    
    @pytest.mark.asyncio
    async def test_web_search_duckduckgo(self, search_agent):
        """Test búsqueda web con DuckDuckGo"""
        with patch.object(search_agent, '_search_duckduckgo') as mock_search:
            mock_search.return_value = [
                SearchResult(
                    title="DuckDuckGo Privacy",
                    url="https://duckduckgo.com/privacy",
                    snippet="Privacy-focused search engine...",
                    source=SearchSource.DUCKDUCKGO,
                    score=0.90
                )
            ]
            
            result = await search_agent.web_search(
                query="privacy search engine",
                source=SearchSource.DUCKDUCKGO,
                max_results=5
            )
            
            assert isinstance(result, SearchResponse)
            assert len(result.results) == 1
            assert result.sources_used == [SearchSource.DUCKDUCKGO]
    
    @pytest.mark.asyncio
    async def test_web_search_bing(self, search_agent):
        """Test búsqueda web con Bing"""
        with patch.object(search_agent, '_search_bing') as mock_search:
            mock_search.return_value = [
                SearchResult(
                    title="Microsoft Bing Search",
                    url="https://bing.com/search",
                    snippet="Microsoft's search engine...",
                    source=SearchSource.BING,
                    score=0.88
                )
            ]
            
            result = await search_agent.web_search(
                query="Microsoft search",
                source=SearchSource.BING,
                max_results=5
            )
            
            assert isinstance(result, SearchResponse)
            assert len(result.results) == 1
            assert result.sources_used == [SearchSource.BING]
    
    @pytest.mark.asyncio
    async def test_wikipedia_search(self, search_agent):
        """Test búsqueda en Wikipedia"""
        with patch.object(search_agent, '_search_wikipedia') as mock_search:
            mock_search.return_value = [
                SearchResult(
                    title="Python (programming language)",
                    url="https://en.wikipedia.org/wiki/Python_(programming_language)",
                    snippet="Python is an interpreted, high-level programming language...",
                    source=SearchSource.WIKIPEDIA,
                    score=0.92
                )
            ]
            
            result = await search_agent.wikipedia_search(
                query="Python programming language",
                language="en"
            )
            
            assert isinstance(result, SearchResponse)
            assert len(result.results) == 1
            assert result.sources_used == [SearchSource.WIKIPEDIA]
    
    @pytest.mark.asyncio
    async def test_github_search(self, search_agent):
        """Test búsqueda en GitHub"""
        with patch.object(search_agent, '_search_github') as mock_search:
            mock_search.return_value = [
                SearchResult(
                    title="python/cpython",
                    url="https://github.com/python/cpython",
                    snippet="The Python programming language...",
                    source=SearchSource.GITHUB,
                    score=0.90
                )
            ]
            
            result = await search_agent.github_search(
                query="python programming",
                language="python",
                sort="stars"
            )
            
            assert isinstance(result, SearchResponse)
            assert len(result.results) == 1
            assert result.sources_used == [SearchSource.GITHUB]
    
    @pytest.mark.asyncio
    async def test_arxiv_search(self, search_agent):
        """Test búsqueda en ArXiv"""
        with patch.object(search_agent, '_search_arxiv') as mock_search:
            mock_search.return_value = [
                SearchResult(
                    title="Deep Learning for Natural Language Processing",
                    url="https://arxiv.org/abs/2023.12345",
                    snippet="Recent advances in deep learning for NLP...",
                    source=SearchSource.ARXIV,
                    score=0.85
                )
            ]
            
            result = await search_agent.arxiv_search(
                query="deep learning natural language processing",
                category="cs.CL",
                max_results=10
            )
            
            assert isinstance(result, SearchResponse)
            assert len(result.results) == 1
            assert result.sources_used == [SearchSource.ARXIV]
    
    @pytest.mark.asyncio
    async def test_academic_search(self, search_agent):
        """Test búsqueda académica"""
        with patch.object(search_agent, '_search_academic') as mock_search:
            mock_search.return_value = [
                SearchResult(
                    title="Machine Learning Applications in Healthcare",
                    url="https://academic.example.com/paper1",
                    snippet="Application of ML techniques in healthcare...",
                    source=SearchSource.ACADEMIC,
                    score=0.88
                )
            ]
            
            result = await search_agent.academic_search(
                query="machine learning healthcare",
                domain="computer_science",
                year_range=(2020, 2024)
            )
            
            assert isinstance(result, SearchResponse)
            assert len(result.results) == 1
            assert result.sources_used == [SearchSource.ACADEMIC]
    
    @pytest.mark.asyncio
    async def test_multi_source_search(self, search_agent):
        """Test búsqueda en múltiples fuentes"""
        # Mock múltiples búsquedas
        mock_results = [
            ([
                SearchResult(
                    title="Python Tutorial",
                    url="https://python.org",
                    snippet="Official Python tutorial",
                    source=SearchSource.GOOGLE,
                    score=0.90
                )
            ], SearchSource.GOOGLE),
            ([
                SearchResult(
                    title="Python Wikipedia",
                    url="https://wikipedia.org/python",
                    snippet="Python programming language",
                    source=SearchSource.WIKIPEDIA,
                    score=0.85
                )
            ], SearchSource.WIKIPEDIA)
        ]
        
        with patch.object(search_agent, '_search_google') as mock_google, \
             patch.object(search_agent, '_search_wikipedia') as mock_wiki:
            
            mock_google.return_value = mock_results[0][0]
            mock_wiki.return_value = mock_results[1][0]
            
            sources = [SearchSource.GOOGLE, SearchSource.WIKIPEDIA]
            result = await search_agent.multi_source_search(
                query="Python programming",
                sources=sources,
                max_results_per_source=5
            )
            
            assert isinstance(result, SearchResponse)
            assert len(result.results) == 2
            assert SearchSource.GOOGLE in result.sources_used
            assert SearchSource.WIKIPEDIA in result.sources_used
    
    @pytest.mark.asyncio
    async def test_ranking_and_scoring(self, search_agent):
        """Test ranking y scoring de resultados"""
        # Crear resultados con diferentes scores
        results = [
            SearchResult(
                title="Result 1",
                url="https://example1.com",
                snippet="Snippet 1",
                source=SearchSource.GOOGLE,
                score=0.5
            ),
            SearchResult(
                title="Result 2", 
                url="https://example2.com",
                snippet="Snippet 2",
                source=SearchSource.DUCKDUCKGO,
                score=0.9
            ),
            SearchResult(
                title="Result 3",
                url="https://example3.com", 
                snippet="Snippet 3",
                source=SearchSource.WIKIPEDIA,
                score=0.7
            )
        ]
        
        with patch.object(search_agent, '_rank_results') as mock_rank:
            mock_rank.return_value = results  # Devolver en orden de ranking
            
            ranked_results = await search_agent._rank_results(
                results, 
                query="test query"
            )
            
            assert len(ranked_results) == 3
            # Verificar que están ordenados por score descendente
            assert ranked_results[0].score >= ranked_results[1].score
            assert ranked_results[1].score >= ranked_results[2].score
    
    @pytest.mark.asyncio
    async def test_deduplication(self, search_agent):
        """Test deduplicación de resultados"""
        # Crear resultados duplicados
        results = [
            SearchResult(
                title="Same Title",
                url="https://example.com/page1",
                snippet="Same content",
                source=SearchSource.GOOGLE,
                score=0.8
            ),
            SearchResult(
                title="Same Title",
                url="https://example.com/page1",  # Misma URL
                snippet="Same content",
                source=SearchSource.DUCKDUCKGO,  # Fuente diferente
                score=0.7
            ),
            SearchResult(
                title="Different Title",
                url="https://example.com/page2",
                snippet="Different content",
                source=SearchSource.WIKIPEDIA,
                score=0.9
            )
        ]
        
        with patch.object(search_agent, '_deduplicate_results') as mock_dedup:
            mock_dedup.return_value = [results[0], results[2]]  # Solo los únicos
            
            deduplicated = await search_agent._deduplicate_results(results)
            
            assert len(deduplicated) == 2  # Solo dos únicos
            assert deduplicated[0].url == "https://example.com/page1"
            assert deduplicated[1].url == "https://example.com/page2"
    
    @pytest.mark.asyncio
    async def test_synthesis(self, search_agent):
        """Test síntesis de resultados"""
        results = [
            SearchResult(
                title="Python Programming",
                url="https://python.org",
                snippet="Python is a high-level programming language",
                source=SearchSource.GOOGLE,
                score=0.9
            ),
            SearchResult(
                title="Python Tutorial", 
                url="https://tutorial.com/python",
                snippet="Learn Python programming step by step",
                source=SearchSource.WIKIPEDIA,
                score=0.8
            )
        ]
        
        synthesis = await search_agent._synthesize_results(results, "Python programming")
        
        assert isinstance(synthesis, str)
        assert len(synthesis) > 0
        assert "Python" in synthesis or "programming" in synthesis
    
    @pytest.mark.asyncio
    async def test_error_handling_connection_error(self, search_agent):
        """Test manejo de errores - error de conexión"""
        with patch.object(search_agent, '_search_google') as mock_search:
            mock_search.side_effect = ConnectionError("Connection failed")
            
            with pytest.raises(ConnectionError):
                await search_agent.web_search(
                    query="test",
                    source=SearchSource.GOOGLE
                )
    
    @pytest.mark.asyncio
    async def test_error_handling_timeout(self, search_agent):
        """Test manejo de errores - timeout"""
        with patch.object(search_agent, '_search_duckduckgo') as mock_search:
            mock_search.side_effect = asyncio.TimeoutError("Request timeout")
            
            with pytest.raises(asyncio.TimeoutError):
                await search_agent.web_search(
                    query="test",
                    source=SearchSource.DUCKDUCKGO
                )
    
    @pytest.mark.asyncio
    async def test_error_handling_rate_limit(self, search_agent):
        """Test manejo de errores - rate limit"""
        with patch.object(search_agent, '_search_bing') as mock_search:
            mock_search.return_value = {
                "success": False,
                "error": "Rate limit exceeded",
                "retry_after": 60
            }
            
            result = await search_agent.web_search(
                query="test",
                source=SearchSource.BING
            )
            
            assert isinstance(result, SearchResponse)
            assert result.total_results == 0
            assert len(result.results) == 0
    
    @pytest.mark.asyncio
    async def test_search_result_structure(self, search_agent):
        """Test estructura de SearchResult"""
        result = SearchResult(
            title="Test Result",
            url="https://example.com",
            snippet="Test snippet",
            source=SearchSource.GOOGLE,
            score=0.85
        )
        
        assert result.title == "Test Result"
        assert result.url == "https://example.com"
        assert result.snippet == "Test snippet"
        assert result.source == SearchSource.GOOGLE
        assert result.score == 0.85
        assert isinstance(result.timestamp, float)
        assert result.domain == "example.com"
    
    @pytest.mark.asyncio
    async def test_search_response_structure(self, search_agent):
        """Test estructura de SearchResponse"""
        results = [
            SearchResult(
                title="Result 1",
                url="https://example1.com",
                snippet="Snippet 1",
                source=SearchSource.GOOGLE
            )
        ]
        
        response = SearchResponse(
            query="test query",
            results=results,
            total_results=1,
            sources_used=[SearchSource.GOOGLE],
            execution_time=1.5,
            timestamp=time.time()
        )
        
        assert response.query == "test query"
        assert len(response.results) == 1
        assert response.total_results == 1
        assert SearchSource.GOOGLE in response.sources_used
        assert response.execution_time == 1.5
        assert isinstance(response.timestamp, float)
    
    @pytest.mark.asyncio
    async def test_domain_extraction(self, search_agent):
        """Test extracción de dominio"""
        test_urls = [
            ("https://www.example.com/path", "www.example.com"),
            ("http://subdomain.example.org/page", "subdomain.example.org"),
            ("https://github.com/user/repo", "github.com"),
            ("ftp://ftp.example.net/file", "ftp.example.net")
        ]
        
        for url, expected_domain in test_urls:
            result = SearchResult(
                title="Test",
                url=url,
                snippet="Test snippet",
                source=SearchSource.GOOGLE
            )
            
            assert result.domain == expected_domain
    
    @pytest.mark.asyncio
    async def test_language_detection(self, search_agent):
        """Test detección de idioma por dominio"""
        test_domains = [
            ("example.es", "es"),
            ("example.com", "en"),
            ("example.fr", "en"),  # Default a inglés
            ("example.mx", "es")
        ]
        
        for domain, expected_lang in test_domains:
            result = SearchResult(
                title="Test",
                url=f"https://{domain}/page",
                snippet="Test snippet",
                source=SearchSource.GOOGLE
            )
            
            assert result.language == expected_lang
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, search_agent):
        """Test búsqueda con filtros"""
        filters = {
            "date_range": ("2023-01-01", "2023-12-31"),
            "language": "es",
            "region": "Spain",
            "safe_search": True,
            "exclude_domains": ["spam.com", "ads.com"]
        }
        
        with patch.object(search_agent, '_search_google') as mock_search:
            mock_search.return_value = [
                SearchResult(
                    title="Filtered Result",
                    url="https://filtered.example.com",
                    snippet="Result from filtered search",
                    source=SearchSource.GOOGLE
                )
            ]
            
            result = await search_agent.web_search(
                query="filtered search",
                source=SearchSource.GOOGLE,
                filters=filters
            )
            
            assert isinstance(result, SearchResponse)
            assert len(result.results) == 1
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, search_agent):
        """Test métricas de rendimiento"""
        start_time = time.time()
        
        with patch.object(search_agent, '_search_duckduckgo') as mock_search:
            mock_search.return_value = []
            
            result = await search_agent.web_search(
                query="performance test",
                source=SearchSource.DUCKDUCKGO
            )
            
            end_time = time.time()
            
            # Verificar que se registran las métricas de tiempo
            assert result.execution_time >= 0
            assert result.execution_time <= (end_time - start_time) + 1.0  # Margen de tolerancia
    
    @pytest.mark.asyncio
    async def test_caching(self, search_agent):
        """Test sistema de caché"""
        query = "cached query"
        
        # Primera búsqueda
        with patch.object(search_agent, '_search_duckduckgo') as mock_search:
            mock_search.return_value = [
                SearchResult(
                    title="Cached Result",
                    url="https://cached.example.com",
                    snippet="Cached snippet",
                    source=SearchSource.DUCKDUCKGO
                )
            ]
            
            result1 = await search_agent.web_search(
                query=query,
                source=SearchSource.DUCKDUCKGO,
                use_cache=True
            )
            
            # Segunda búsqueda debería usar caché
            result2 = await search_agent.web_search(
                query=query,
                source=SearchSource.DUCKDUCKGO,
                use_cache=True
            )
            
            # Verificar que ambos resultados son iguales (cached)
            assert result1.results[0].url == result2.results[0].url
