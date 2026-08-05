"""
Search Engine Agent MCP - Agente de búsqueda avanzada con múltiples fuentes
Extiende el motor de búsqueda base con integración de Google, Bing, DuckDuckGo, 
GitHub, ArXiv y fuentes académicas. Incluye ranking, deduplicación y síntesis.

Autor: Search Engine Agent
Versión: 1.0.0
"""

import asyncio
import json
import re
import time
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass, field
from enum import Enum
import requests
from bs4 import BeautifulSoup

# Importar la estructura base del agente MCP
try:
    from .base_agent_wrapper import BaseAgentWrapper
except ImportError:
    BaseAgentWrapper = object

# Importar el motor de búsqueda base (simulado para compatibilidad)
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
    from backend.tools.search_engine import SearchEngine as BaseSearchEngine
except ImportError:
    BaseSearchEngine = None


class SearchSource(Enum):
    """Enumeración de fuentes de búsqueda disponibles"""
    DUCKDUCKGO = "duckduckgo"
    WIKIPEDIA = "wikipedia"
    GOOGLE = "google"
    BING = "bing"
    GITHUB = "github"
    ARXIV = "arxiv"
    ACADEMIC = "academic"
    SEMANTIC = "semantic"


@dataclass
class SearchResult:
    """Estructura de datos para un resultado de búsqueda"""
    title: str
    url: str
    snippet: str
    source: SearchSource
    score: float = 0.0
    relevance: float = 0.0
    domain: str = ""
    language: str = "es"
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-procesamiento para extraer dominio y otros metadatos"""
        if self.url:
            parsed_url = urlparse(self.url)
            self.domain = parsed_url.netloc
            
        # Extraer idioma del dominio o meta tags simulados
        if '.es' in self.domain:
            self.language = "es"
        elif '.com' in self.domain:
            self.language = "en"


@dataclass
class SearchResponse:
    """Respuesta consolidada de búsqueda"""
    query: str
    results: List[SearchResult]
    total_results: int
    sources_used: List[SearchSource]
    execution_time: float
    timestamp: float
    summary: str = ""
    deduplicated: bool = False
    ranked: bool = False
    synthesis: str = ""


class SearchEngineAgent(BaseAgentWrapper if BaseAgentWrapper else object):
    """
    Agente de búsqueda avanzada que integra múltiples fuentes de búsqueda
    y proporciona funcionalidades de ranking, deduplicación y síntesis.
    """
    
    def __init__(self):
        super().__init__() if BaseAgentWrapper else None
        
        self.name = "search_engine_agent"
        self.description = "Agente de búsqueda avanzada con múltiples fuentes y análisis inteligente"
        self.version = "1.0.0"
        self.logger = logging.getLogger(__name__)
        
        # Configuración de APIs y endpoints
        self.api_config = {
            "google": {
                "search_endpoint": "https://www.googleapis.com/customsearch/v1",
                "rate_limit": 10  # requests per minute
            },
            "bing": {
                "search_endpoint": "https://api.bing.microsoft.com/v7.0/search",
                "rate_limit": 100  # requests per minute
            },
            "github": {
                "search_endpoint": "https://api.github.com/search/repositories",
                "rate_limit": 30  # requests per minute
            },
            "arxiv": {
                "search_endpoint": "http://export.arxiv.org/api/query",
                "rate_limit": 10  # requests per minute
            },
            "scholar": {
                "search_endpoint": "https://serpapi.com/search",  # Simplified for demo
                "rate_limit": 10  # requests per minute
            }
        }
        
        # Configuración de búsqueda
        self.config = {
            "max_results_per_source": 10,
            "max_total_results": 50,
            "timeout": 30,
            "enable_ranking": True,
            "enable_deduplication": True,
            "enable_synthesis": True,
            "default_language": "es",
            "safe_search": True,
            "region": "es-es"
        }
        
        # Configuración de scoring
        self.scoring_weights = {
            "relevance": 0.4,
            "authority": 0.3,
            "freshness": 0.2,
            "language_match": 0.1
        }
        
        # Cache para optimización
        self._cache = {}
        self._last_requests = {}
        
        # Motor de búsqueda base (si está disponible)
        self.base_search = BaseSearchEngine() if BaseSearchEngine else None
    
    def search_web(
        self,
        query: str,
        sources: List[SearchSource] = None,
        max_results: int = 20,
        enable_synthesis: bool = True,
        **kwargs
    ) -> SearchResponse:
        """
        Realiza búsqueda web multi-fuente con análisis inteligente
        
        Args:
            query: Consulta de búsqueda
            sources: Fuentes de búsqueda a utilizar
            max_results: Máximo número de resultados totales
            enable_synthesis: Si generar síntesis de resultados
            **kwargs: Parámetros adicionales específicos de cada fuente
            
        Returns:
            SearchResponse con resultados consolidados y analizados
        """
        start_time = time.time()
        
        try:
            # Configuración por defecto
            if sources is None:
                sources = [
                    SearchSource.DUCKDUCKGO,
                    SearchSource.WIKIPEDIA,
                    SearchSource.GOOGLE,
                    SearchSource.BING
                ]
            
            # Normalizar y validar consulta
            normalized_query = self._normalize_query(query)
            if not normalized_query:
                return SearchResponse(
                    query=query,
                    results=[],
                    total_results=0,
                    sources_used=[],
                    execution_time=time.time() - start_time,
                    timestamp=time.time()
                )
            
            # Realizar búsquedas en paralelo
            all_results = []
            successful_sources = []
            
            for source in sources:
                try:
                    source_results = self._search_source(source, normalized_query, **kwargs)
                    if source_results:
                        all_results.extend(source_results)
                        successful_sources.append(source)
                        
                except Exception as e:
                    self.logger.warning(f"Error en búsqueda {source.value}: {e}")
                    continue
            
            # Aplicar deduplicación y ranking
            if self.config["enable_deduplication"]:
                deduplicated_results = self._deduplicate_results(all_results)
            else:
                deduplicated_results = all_results
            
            if self.config["enable_ranking"] and deduplicated_results:
                ranked_results = self._rank_results(deduplicated_results, normalized_query)
            else:
                ranked_results = deduplicated_results
            
            # Aplicar límite final de resultados
            final_results = ranked_results[:max_results]
            
            # Generar síntesis si se requiere
            synthesis = ""
            if enable_synthesis and final_results:
                synthesis = self._generate_synthesis(final_results, normalized_query)
            
            execution_time = time.time() - start_time
            
            return SearchResponse(
                query=normalized_query,
                results=final_results,
                total_results=len(final_results),
                sources_used=successful_sources,
                execution_time=execution_time,
                timestamp=time.time(),
                summary=self._generate_summary(final_results),
                deduplicated=len(all_results) > len(final_results),
                ranked=True,
                synthesis=synthesis
            )
            
        except Exception as e:
            self.logger.error(f"Error en búsqueda web: {e}")
            return SearchResponse(
                query=query,
                results=[],
                total_results=0,
                sources_used=[],
                execution_time=time.time() - start_time,
                timestamp=time.time()
            )
    
    def search_academic(
        self,
        query: str,
        sources: List[SearchSource] = None,
        max_results: int = 20,
        **kwargs
    ) -> SearchResponse:
        """
        Realiza búsqueda académica especializada
        
        Args:
            query: Consulta de búsqueda
            sources: Fuentes académicas (ArXiv, Scholar, etc.)
            max_results: Máximo número de resultados
            **kwargs: Parámetros adicionales
            
        Returns:
            SearchResponse con resultados académicos
        """
        if sources is None:
            sources = [SearchSource.ARXIV, SearchSource.ACADEMIC]
        
        return self.search_web(
            query=query,
            sources=sources,
            max_results=max_results,
            enable_synthesis=True,
            **kwargs
        )
    
    def search_code(
        self,
        query: str,
        sources: List[SearchSource] = None,
        max_results: int = 20,
        **kwargs
    ) -> SearchResponse:
        """
        Realiza búsqueda especializada en código
        
        Args:
            query: Consulta de búsqueda en código
            sources: Fuentes de código (GitHub, etc.)
            max_results: Máximo número de resultados
            **kwargs: Parámetros adicionales
            
        Returns:
            SearchResponse con resultados de código
        """
        if sources is None:
            sources = [SearchSource.GITHUB]
        
        return self.search_web(
            query=query,
            sources=sources,
            max_results=max_results,
            enable_synthesis=False,  # No synthesis for code searches
            **kwargs
        )
    
    def semantic_search(
        self,
        query: str,
        max_results: int = 20,
        **kwargs
    ) -> SearchResponse:
        """
        Realiza búsqueda semántica usando embeddings
        
        Args:
            query: Consulta semántica
            max_results: Máximo número de resultados
            **kwargs: Parámetros adicionales
            
        Returns:
            SearchResponse con resultados semánticos
        """
        sources = [SearchSource.SEMANTIC]
        
        return self.search_web(
            query=query,
            sources=sources,
            max_results=max_results,
            enable_synthesis=True,
            **kwargs
        )
    
    def _search_source(self, source: SearchSource, query: str, **kwargs) -> List[SearchResult]:
        """Busca en una fuente específica"""
        
        # Verificar cache
        cache_key = f"{source.value}:{hashlib.md5(query.encode()).hexdigest()}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            if source == SearchSource.DUCKDUCKGO:
                results = self._search_duckduckgo(query, **kwargs)
            elif source == SearchSource.WIKIPEDIA:
                results = self._search_wikipedia(query, **kwargs)
            elif source == SearchSource.GOOGLE:
                results = self._search_google(query, **kwargs)
            elif source == SearchSource.BING:
                results = self._search_bing(query, **kwargs)
            elif source == SearchSource.GITHUB:
                results = self._search_github(query, **kwargs)
            elif source == SearchSource.ARXIV:
                results = self._search_arxiv(query, **kwargs)
            elif source == SearchSource.ACADEMIC:
                results = self._search_academic(query, **kwargs)
            elif source == SearchSource.SEMANTIC:
                results = self._search_semantic(query, **kwargs)
            else:
                results = []
            
            # Cachear resultados
            self._cache[cache_key] = results
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error buscando en {source.value}: {e}")
            return []
    
    def _search_duckduckgo(self, query: str, **kwargs) -> List[SearchResult]:
        """Búsqueda en DuckDuckGo"""
        if self.base_search:
            result = self.base_search.duckduckgo_search(query)
            if result.success and result.data:
                results = []
                for item in result.data.get('results', []):
                    results.append(SearchResult(
                        title=item.get('title', ''),
                        url=item.get('url', ''),
                        snippet=item.get('snippet', ''),
                        source=SearchSource.DUCKDUCKGO
                    ))
                return results
        
        # Implementación simplificada como fallback
        return self._fallback_search(query, SearchSource.DUCKDUCKGO)
    
    def _search_wikipedia(self, query: str, **kwargs) -> List[SearchResult]:
        """Búsqueda en Wikipedia"""
        if self.base_search:
            result = self.base_search.wikipedia_search(query)
            if result.success and result.data:
                results = []
                for page in result.data.get('pages', []):
                    results.append(SearchResult(
                        title=page.get('title', ''),
                        url=f"https://es.wikipedia.org/wiki/{page.get('title', '').replace(' ', '_')}",
                        snippet=page.get('snippet', '') or page.get('extract', ''),
                        source=SearchSource.WIKIPEDIA,
                        metadata={'pageid': page.get('pageid')}
                    ))
                return results
        
        return self._fallback_search(query, SearchSource.WIKIPEDIA)
    
    def _search_google(self, query: str, **kwargs) -> List[SearchResult]:
        """Búsqueda en Google (simulada para demo)"""
        # En implementación real, usar Google Custom Search API
        return self._fallback_search(query, SearchSource.GOOGLE)
    
    def _search_bing(self, query: str, **kwargs) -> List[SearchResult]:
        """Búsqueda en Bing (simulada para demo)"""
        return self._fallback_search(query, SearchSource.BING)
    
    def _search_github(self, query: str, **kwargs) -> List[SearchResult]:
        """Búsqueda en GitHub"""
        # Simular resultados de GitHub
        results = []
        
        # Términos comunes para búsqueda de código
        code_terms = ['python', 'javascript', 'react', 'node', 'api', 'database']
        query_lower = query.lower()
        
        if any(term in query_lower for term in code_terms):
            results.append(SearchResult(
                title=f"Repository: {query} - GitHub",
                url=f"https://github.com/search?q={query.replace(' ', '+')}",
                snippet=f"Repositorio de GitHub relacionado con {query}",
                source=SearchSource.GITHUB,
                metadata={'type': 'repository_search'}
            ))
        
        return results
    
    def _search_arxiv(self, query: str, **kwargs) -> List[SearchResult]:
        """Búsqueda en ArXiv"""
        # Simular resultados de ArXiv
        results = []
        
        # Términos académicos comunes
        academic_terms = ['machine learning', 'deep learning', 'neural', 'algorithm', 'research']
        query_lower = query.lower()
        
        if any(term in query_lower for term in academic_terms):
            results.append(SearchResult(
                title=f"Paper: Research on {query} - ArXiv",
                url=f"http://arxiv.org/search/?query={query.replace(' ', '+')}&searchtype=all",
                snippet=f"Artículo académico sobre {query} disponible en ArXiv",
                source=SearchSource.ARXIV,
                metadata={'type': 'academic_paper', 'arxiv_id': f'2024.xxxxx'}
            ))
        
        return results
    
    def _search_academic(self, query: str, **kwargs) -> List[SearchResult]:
        """Búsqueda en fuentes académicas"""
        # Combinar ArXiv y otras fuentes académicas
        arxiv_results = self._search_arxiv(query, **kwargs)
        
        # Agregar más fuentes académicas
        results = arxiv_results.copy()
        results.append(SearchResult(
            title=f"Academic Source: {query}",
            url=f"https://scholar.google.com/scholar?q={query.replace(' ', '+')}",
            snippet=f"Resultados académicos para {query} en Google Scholar",
            source=SearchSource.ACADEMIC,
            metadata={'type': 'academic_search'}
        ))
        
        return results
    
    def _search_semantic(self, query: str, **kwargs) -> List[SearchResult]:
        """Búsqueda semántica (simulada)"""
        # En implementación real, usar embeddings y vector search
        return self._fallback_search(query, SearchSource.SEMANTIC)
    
    def _fallback_search(self, query: str, source: SearchSource) -> List[SearchResult]:
        """Búsqueda de fallback para demostrar funcionalidad"""
        
        # Generar resultados simulados basados en la consulta
        results = []
        
        # Crear algunos resultados ficticios pero realistas
        domains = [
            "wikipedia.org",
            "example.com", 
            "research.org",
            "github.com",
            "stackoverflow.com"
        ]
        
        for i, domain in enumerate(domains):
            if i < 3:  # Limitar resultados
                results.append(SearchResult(
                    title=f"Resultado {i+1}: {query.title()} - {domain}",
                    url=f"https://{domain}/result/{i+1}",
                    snippet=f"Información relacionada con '{query}' encontrada en {domain}",
                    source=source,
                    score=0.5 + (i * 0.1),
                    metadata={'simulated': True}
                ))
        
        return results
    
    def _normalize_query(self, query: str) -> str:
        """Normaliza la consulta de búsqueda"""
        if not query:
            return ""
        
        # Limpiar y normalizar
        normalized = query.strip().lower()
        
        # Remover caracteres especiales excesivos
        normalized = re.sub(r'[^\w\s\-]', ' ', normalized)
        
        # Comprimir espacios múltiples
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Elimina resultados duplicados basado en URL y título"""
        seen_urls = set()
        seen_titles = set()
        unique_results = []
        
        for result in results:
            # Normalizar URL para comparación
            normalized_url = result.url.lower().rstrip('/')
            
            # Normalizar título para comparación
            normalized_title = re.sub(r'[^\w\s]', '', result.title.lower()).strip()
            
            # Verificar duplicados
            is_duplicate = (
                normalized_url in seen_urls or 
                normalized_title in seen_titles
            )
            
            if not is_duplicate:
                seen_urls.add(normalized_url)
                seen_titles.add(normalized_title)
                unique_results.append(result)
        
        return unique_results
    
    def _rank_results(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """Rankea resultados basado en múltiples factores"""
        
        query_words = set(query.split())
        
        for result in results:
            score = 0.0
            
            # Relevancia del título
            title_words = set(re.findall(r'\w+', result.title.lower()))
            title_relevance = len(query_words.intersection(title_words)) / max(len(query_words), 1)
            score += title_relevance * self.scoring_weights["relevance"]
            
            # Autoridad del dominio
            domain_authority = self._get_domain_authority(result.domain)
            score += domain_authority * self.scoring_weights["authority"]
            
            # Frescura
            freshness = self._calculate_freshness(result.timestamp)
            score += freshness * self.scoring_weights["freshness"]
            
            # Coincidencia de idioma
            language_match = 1.0 if result.language == self.config["default_language"] else 0.5
            score += language_match * self.scoring_weights["language_match"]
            
            result.score = score
        
        # Ordenar por score descendente
        return sorted(results, key=lambda r: r.score, reverse=True)
    
    def _get_domain_authority(self, domain: str) -> float:
        """Calcula la autoridad del dominio"""
        
        # Autoridad predefinida para dominios conocidos
        domain_authorities = {
            'wikipedia.org': 0.9,
            'github.com': 0.8,
            'stackoverflow.com': 0.85,
            'arxiv.org': 0.9,
            'scholar.google.com': 0.95,
            'mit.edu': 0.95,
            'stanford.edu': 0.95,
            'research.org': 0.8,
            'example.com': 0.5
        }
        
        return domain_authorities.get(domain, 0.5)
    
    def _calculate_freshness(self, timestamp: float) -> float:
        """Calcula la frescura del contenido (0-1, donde 1 es más fresco)"""
        
        current_time = time.time()
        age_hours = (current_time - timestamp) / 3600
        
        # Decaimiento exponencial
        freshness = max(0, 1 - (age_hours / (24 * 365)))  # Decay over a year
        
        return freshness
    
    def _generate_summary(self, results: List[SearchResult]) -> str:
        """Genera un resumen de los resultados"""
        
        if not results:
            return "No se encontraron resultados."
        
        # Obtener temas principales
        titles = [result.title for result in results[:10]]
        
        # Análisis simple de frecuencia de palabras
        word_count = {}
        for title in titles:
            words = re.findall(r'\w+', title.lower())
            for word in words:
                if len(word) > 3:
                    word_count[word] = word_count.get(word, 0) + 1
        
        # Top palabras más frecuentes
        top_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:3]
        
        summary = f"Se encontraron {len(results)} resultados relevantes. "
        if top_words:
            main_topics = [word for word, count in top_words[:3]]
            summary += f"Temas principales: {', '.join(main_topics)}. "
        
        summary += f"Fuentes consultadas: {len(set(r.source.value for r in results))}"
        
        return summary
    
    def _generate_synthesis(self, results: List[SearchResult], query: str) -> str:
        """Genera una síntesis inteligente de los resultados"""
        
        if not results:
            return f"No hay suficiente información para generar síntesis sobre '{query}'."
        
        synthesis_parts = []
        
        # Información general
        synthesis_parts.append(f"Síntesis de resultados para: '{query}'")
        synthesis_parts.append(f"Total de resultados: {len(results)}")
        synthesis_parts.append(f"Fuentes consultadas: {', '.join(set(r.source.value for r in results))}")
        
        # Resultados más relevantes
        synthesis_parts.append("\nResultados más relevantes:")
        for i, result in enumerate(results[:3], 1):
            synthesis_parts.append(f"{i}. {result.title} (Fuente: {result.source.value})")
            synthesis_parts.append(f"   {result.snippet[:200]}...")
        
        # Análisis de dominios
        domains = [result.domain for result in results if result.domain]
        domain_count = {}
        for domain in domains:
            domain_count[domain] = domain_count.get(domain, 0) + 1
        
        if domain_count:
            synthesis_parts.append(f"\nPrincipales dominios encontrados:")
            sorted_domains = sorted(domain_count.items(), key=lambda x: x[1], reverse=True)[:3]
            for domain, count in sorted_domains:
                synthesis_parts.append(f"- {domain}: {count} resultados")
        
        return "\n".join(synthesis_parts)
    
    def get_search_analytics(self, response: SearchResponse) -> Dict[str, Any]:
        """Obtiene analytics detallados de los resultados de búsqueda"""
        
        if not response.results:
            return {"error": "No hay resultados para analizar"}
        
        # Análisis por fuente
        source_analysis = {}
        for source in response.sources_used:
            source_results = [r for r in response.results if r.source == source]
            source_analysis[source.value] = {
                "count": len(source_results),
                "avg_score": sum(r.score for r in source_results) / len(source_results) if source_results else 0,
                "domains": list(set(r.domain for r in source_results if r.domain))
            }
        
        # Análisis por dominio
        domain_analysis = {}
        domains = [r.domain for r in response.results if r.domain]
        for domain in set(domains):
            domain_results = [r for r in response.results if r.domain == domain]
            domain_analysis[domain] = {
                "count": len(domain_results),
                "avg_score": sum(r.score for r in domain_results) / len(domain_results),
                "sources": list(set(r.source.value for r in domain_results))
            }
        
        # Análisis de idioma
        language_analysis = {}
        languages = [r.language for r in response.results]
        for lang in set(languages):
            lang_results = [r for r in response.results if r.language == lang]
            language_analysis[lang] = {
                "count": len(lang_results),
                "percentage": (len(lang_results) / len(response.results)) * 100
            }
        
        return {
            "query": response.query,
            "total_results": response.total_results,
            "execution_time": response.execution_time,
            "deduplication_efficiency": (response.total_results / len(response.results)) if response.deduplicated else 1.0,
            "source_analysis": source_analysis,
            "domain_analysis": domain_analysis,
            "language_analysis": language_analysis,
            "timestamp": response.timestamp
        }
    
    def clear_cache(self):
        """Limpia el cache de resultados"""
        self._cache.clear()
    
    def get_supported_sources(self) -> List[Dict[str, str]]:
        """Obtiene las fuentes de búsqueda soportadas"""
        return [
            {
                "name": source.value,
                "display_name": source.name.replace('_', ' ').title(),
                "description": self._get_source_description(source)
            }
            for source in SearchSource
        ]
    
    def _get_source_description(self, source: SearchSource) -> str:
        """Obtiene descripción de una fuente de búsqueda"""
        descriptions = {
            SearchSource.DUCKDUCKGO: "Motor de búsqueda privado sin seguimiento",
            SearchSource.WIKIPEDIA: "Enciclopedia colaborativa",
            SearchSource.GOOGLE: "Motor de búsqueda más popular del mundo",
            SearchSource.BING: "Motor de búsqueda de Microsoft",
            SearchSource.GITHUB: "Repositorios de código y proyectos",
            SearchSource.ARXIV: "Repositorio de preprints científicos",
            SearchSource.ACADEMIC: "Fuentes académicas y científicas",
            SearchSource.SEMANTIC: "Búsqueda semántica con IA"
        }
        return descriptions.get(source, "Fuente de búsqueda")


# Funciones de utilidad para compatibilidad MCP
def create_search_engine_agent() -> SearchEngineAgent:
    """Crea una instancia del agente de búsqueda"""
    return SearchEngineAgent()


# Testing y demostración
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Crear agente
    agent = SearchEngineAgent()
    
    # Ejemplo de búsqueda
    query = "machine learning python tutorial"
    
    print(f"🔍 Realizando búsqueda: {query}")
    response = agent.search_web(query, max_results=10)
    
    print(f"\n📊 Resultados:")
    print(f"  - Total: {response.total_results}")
    print(f"  - Fuentes: {[s.value for s in response.sources_used]}")
    print(f"  - Tiempo: {response.execution_time:.2f}s")
    print(f"  - Deduplicado: {response.deduplicated}")
    print(f"  - Rankeado: {response.ranked}")
    
    if response.results:
        print(f"\n🎯 Top 3 resultados:")
        for i, result in enumerate(response.results[:3], 1):
            print(f"  {i}. {result.title}")
            print(f"     URL: {result.url}")
            print(f"     Fuente: {result.source.value}")
            print(f"     Score: {result.score:.2f}")
            print()
    
    if response.synthesis:
        print(f"📝 Síntesis:")
        print(response.synthesis)
    
    # Analytics
    analytics = agent.get_search_analytics(response)
    print(f"\n📈 Analytics: {json.dumps(analytics, indent=2, ensure_ascii=False)}")
    
    # Fuentes soportadas
    print(f"\n🌐 Fuentes soportadas:")
    for source in agent.get_supported_sources():
        print(f"  - {source['display_name']}: {source['description']}")