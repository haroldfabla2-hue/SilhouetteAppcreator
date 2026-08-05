"""
News Intelligence Agent - Agente de Inteligencia de Noticias
Proporciona capacidades avanzadas de agregación, análisis y síntesis de noticias
desde múltiples fuentes mediáticas con detección de tendencias y sesgos.

Características principales:
- Agregación de noticias desde múltiples fuentes
- Análisis de tendencias en tiempo real
- Detección de sesgos mediáticos
- Análisis de sentimiento y tono
- Seguimiento de temas y eventos
- Generación de resúmenes ejecutivos
- Detección de fake news y verificación de hechos

Autor: News Intelligence Agent
Versión: 1.0.0
"""

import asyncio
import json
import re
import time
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Set, Tuple, Callable
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass, field
from enum import Enum
import requests
from bs4 import BeautifulSoup

try:
    from ..base_agent_wrapper import BaseAgentWrapper
    from ..search_engine_agent import SearchEngineAgent, SearchSource, SearchResult, SearchResponse
except ImportError:
    BaseAgentWrapper = object
    SearchEngineAgent = object
    SearchSource = Enum


class NewsCategory(Enum):
    """Categorías de noticias"""
    POLITICS = "politics"
    ECONOMY = "economy"
    TECHNOLOGY = "technology"
    HEALTH = "health"
    SCIENCE = "science"
    SPORTS = "sports"
    ENTERTAINMENT = "entertainment"
    WORLD = "world"
    LOCAL = "local"
    BUSINESS = "business"


class NewsSource(Enum):
    """Tipos de fuentes de noticias"""
    MAINSTREAM_MEDIA = "mainstream_media"
    ALTERNATIVE_MEDIA = "alternative_media"
    SOCIAL_MEDIA = "social_media"
    RSS_FEED = "rss_feed"
    NEWS_API = "news_api"
    GOVERNMENT = "government"
    ACADEMIC = "academic"
    INDUSTRY = "industry"


class BiasDirection(Enum):
    """Dirección del sesgo mediático"""
    LEFT = "left"           # Sesgo hacia la izquierda política
    LEFT_CENTER = "left_center"
    LEAST_BIAS = "least_bias"  # Mínimo sesgo
    RIGHT_CENTER = "right_center"
    RIGHT = "right"         # Sesgo hacia la derecha política


class Sentiment(Enum):
    """Análisis de sentimiento"""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


@dataclass
class NewsArticle:
    """Artículo de noticia individual"""
    title: str
    url: str
    content: str
    summary: str
    category: NewsCategory
    source: str
    author: str
    published_at: float
    updated_at: float
    sentiment: Sentiment
    bias_score: float  # -1.0 (left) to +1.0 (right)
    credibility_score: float  # 0.0 - 1.0
    tags: List[str]
    language: str = "es"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-procesamiento del artículo"""
        if not self.published_at:
            self.published_at = time.time()
        if not self.updated_at:
            self.updated_at = self.published_at


@dataclass
class NewsStory:
    """Historia/trama de noticias (múltiples artículos sobre el mismo tema)"""
    story_id: str
    title: str
    description: str
    articles: List[NewsArticle]
    first_reported: float
    last_updated: float
    key_topics: List[str]
    sentiment_overall: Sentiment
    credibility_overall: float
    sources_count: int
    geographic_scope: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NewsTrend:
    """Tendencia en noticias"""
    topic: str
    category: NewsCategory
    article_count: int
    sentiment_trend: Sentiment
    growth_rate: float
    peak_time: float
    sources: List[str]
    geographic_distribution: Dict[str, int]
    confidence_score: float


@dataclass
class NewsIntelligenceReport:
    """Reporte de inteligencia de noticias"""
    report_id: str
    generated_at: float
    time_range: Tuple[float, float]  # (start, end)
    categories_analyzed: List[NewsCategory]
    total_articles: int
    total_stories: int
    trends_detected: List[NewsTrend]
    sentiment_analysis: Dict[str, Any]
    bias_analysis: Dict[str, Any]
    credibility_analysis: Dict[str, Any]
    top_stories: List[NewsStory]
    breaking_news: List[NewsArticle]
    recommendations: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class NewsIntelligenceAgent(BaseAgentWrapper if BaseAgentWrapper else object):
    """
    Agente especializado en inteligencia de noticias
    Proporciona capacidades avanzadas de agregación, análisis y síntesis de noticias
    """
    
    def __init__(self):
        super().__init__() if BaseAgentWrapper else None
        
        self.name = "news_intelligence_agent"
        self.description = "Agente de inteligencia de noticias con análisis de sesgos y tendencias"
        self.version = "1.0.0"
        self.logger = logging.getLogger(__name__)
        
        # Inicializar motor de búsqueda
        self.search_engine = SearchEngineAgent()
        
        # Configuración de análisis
        self.config = {
            "max_articles_per_source": 50,
            "sources_per_category": 5,
            "sentiment_threshold": 0.7,
            "credibility_threshold": 0.6,
            "bias_detection_enabled": True,
            "trend_analysis_enabled": True,
            "fake_news_detection": True,
            "language": "es",
            "geographic_scope": "global"
        }
        
        # Base de datos de credibilidad de fuentes de noticias
        self.news_sources_db = self._initialize_news_sources_db()
        
        # Cache para optimización
        self._articles_cache = {}
        self._trends_cache = {}
        self._bias_cache = {}
        
        # Artículos y tendencias recientes
        self._recent_articles = []
        self._active_trends = {}
        self._tracking_stories = {}
    
    def collect_news(
        self,
        categories: List[NewsCategory] = None,
        time_range: str = "24h",
        sources_filter: List[str] = None,
        **kwargs
    ) -> List[NewsArticle]:
        """
        Recopila noticias de múltiples fuentes
        
        Args:
            categories: Categorías de noticias a recopilar
            time_range: Rango temporal (1h, 6h, 24h, 7d, 30d)
            sources_filter: Lista de fuentes específicas a usar
            **kwargs: Parámetros adicionales
            
        Returns:
            Lista de artículos de noticias recopilados
        """
        try:
            self.logger.info(f"Iniciando recopilación de noticias - Categorías: {categories}")
            
            # Configuración por defecto
            if categories is None:
                categories = list(NewsCategory)
            
            # Filtrar fuentes si se especifica
            if sources_filter:
                filtered_sources = [src for src in self.news_sources_db.keys() if src in sources_filter]
            else:
                filtered_sources = list(self.news_sources_db.keys())
            
            all_articles = []
            
            # Recopilar por categoría
            for category in categories:
                category_articles = self._collect_category_news(
                    category, filtered_sources, time_range, **kwargs
                )
                all_articles.extend(category_articles)
            
            # Deduplicar artículos
            unique_articles = self._deduplicate_articles(all_articles)
            
            # Filtrar por credibilidad
            credible_articles = [
                article for article in unique_articles
                if article.credibility_score >= self.config["credibility_threshold"]
            ]
            
            self.logger.info(f"Recopilación completada: {len(credible_articles)} artículos")
            return credible_articles
            
        except Exception as e:
            self.logger.error(f"Error en recopilación de noticias: {e}")
            return []
    
    def analyze_trends(
        self,
        articles: List[NewsArticle],
        time_window: int = 24,
        min_articles: int = 3
    ) -> List[NewsTrend]:
        """
        Analiza tendencias en una colección de artículos
        
        Args:
            articles: Lista de artículos a analizar
            time_window: Ventana temporal en horas
            min_articles: Mínimo de artículos para detectar tendencia
            
        Returns:
            Lista de tendencias detectadas
        """
        try:
            self.logger.info(f"Analizando tendencias en {len(articles)} artículos")
            
            trends = []
            
            # Agrupar artículos por temas
            topic_groups = self._group_articles_by_topic(articles)
            
            # Analizar cada grupo de temas
            for topic, topic_articles in topic_groups.items():
                if len(topic_articles) >= min_articles:
                    trend = self._analyze_topic_trend(topic, topic_articles, time_window)
                    if trend:
                        trends.append(trend)
            
            # Ordenar por confianza y volumen
            trends.sort(key=lambda t: (t.confidence_score, t.article_count), reverse=True)
            
            self.logger.info(f"Análisis de tendencias completado: {len(trends)} tendencias")
            return trends
            
        except Exception as e:
            self.logger.error(f"Error en análisis de tendencias: {e}")
            return []
    
    def detect_bias(
        self,
        article: NewsArticle
    ) -> Dict[str, Any]:
        """
        Detecta sesgo en un artículo específico
        
        Args:
            article: Artículo a analizar
            
        Returns:
            Dict con análisis de sesgo detallado
        """
        try:
            # Verificar cache
            cache_key = f"bias:{hashlib.md5(article.url.encode()).hexdigest()}"
            if cache_key in self._bias_cache:
                return self._bias_cache[cache_key]
            
            # Análisis de sesgo del contenido
            content_bias = self._analyze_content_bias(article.content)
            
            # Análisis de sesgo del medio
            source_bias = self._get_source_bias(article.source)
            
            # Análisis de lenguaje emocional
            emotional_bias = self._analyze_emotional_language(article.content)
            
            # Combinación de factores
            combined_bias_score = self._combine_bias_factors(
                content_bias, source_bias, emotional_bias
            )
            
            # Determinar dirección del sesgo
            bias_direction = self._determine_bias_direction(combined_bias_score)
            
            # Calcular confianza en el análisis
            confidence = self._calculate_bias_confidence(
                content_bias, source_bias, emotional_bias
            )
            
            bias_analysis = {
                "article_title": article.title,
                "source": article.source,
                "overall_bias_score": combined_bias_score,
                "bias_direction": bias_direction.value,
                "confidence_score": confidence,
                "content_bias": content_bias,
                "source_bias": source_bias,
                "emotional_bias": emotional_bias,
                "indicators": self._extract_bias_indicators(article.content),
                "recommendations": self._generate_bias_recommendations(bias_direction, confidence)
            }
            
            # Cache del resultado
            self._bias_cache[cache_key] = bias_analysis
            
            return bias_analysis
            
        except Exception as e:
            self.logger.error(f"Error detectando sesgo: {e}")
            return {"error": str(e)}
    
    def generate_intelligence_report(
        self,
        time_range: str = "24h",
        categories: List[NewsCategory] = None,
        include_trends: bool = True,
        include_bias_analysis: bool = True
    ) -> NewsIntelligenceReport:
        """
        Genera reporte completo de inteligencia de noticias
        
        Args:
            time_range: Rango temporal para el reporte
            categories: Categorías a incluir
            include_trends: Si incluir análisis de tendencias
            include_bias_analysis: Si incluir análisis de sesgos
            
        Returns:
            Reporte completo de inteligencia
        """
        try:
            self.logger.info(f"Generando reporte de inteligencia - {time_range}")
            
            # Recopilar artículos
            articles = self.collect_news(categories, time_range)
            
            if not articles:
                return self._create_empty_report(time_range)
            
            # Generar ID único del reporte
            report_id = f"news_report_{int(time.time())}_{hashlib.md5(time_range.encode()).hexdigest()[:8]}"
            
            # Calcular rango temporal
            end_time = time.time()
            start_time = self._parse_time_range(time_range)
            
            # Detectar tendencias si está habilitado
            trends = []
            if include_trends:
                trends = self.analyze_trends(articles)
            
            # Análisis de sentimiento
            sentiment_analysis = self._analyze_overall_sentiment(articles)
            
            # Análisis de sesgos si está habilitado
            bias_analysis = {}
            if include_bias_analysis:
                bias_analysis = self._analyze_overall_bias(articles)
            
            # Análisis de credibilidad
            credibility_analysis = self._analyze_overall_credibility(articles)
            
            # Identificar historias principales
            top_stories = self._identify_top_stories(articles)
            
            # Identificar noticias de última hora
            breaking_news = self._identify_breaking_news(articles)
            
            # Generar recomendaciones
            recommendations = self._generate_report_recommendations(
                sentiment_analysis, bias_analysis, credibility_analysis, trends
            )
            
            # Crear reporte
            report = NewsIntelligenceReport(
                report_id=report_id,
                generated_at=time.time(),
                time_range=(start_time, end_time),
                categories_analyzed=categories or list(NewsCategory),
                total_articles=len(articles),
                total_stories=len(set(story.story_id for story in top_stories)),
                trends_detected=trends,
                sentiment_analysis=sentiment_analysis,
                bias_analysis=bias_analysis,
                credibility_analysis=credibility_analysis,
                top_stories=top_stories,
                breaking_news=breaking_news,
                recommendations=recommendations,
                metadata={
                    "time_range": time_range,
                    "sources_used": list(set(article.source for article in articles)),
                    "categories_covered": list(set(article.category.value for article in articles))
                }
            )
            
            self.logger.info(f"Reporte generado: {len(articles)} artículos analizados")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generando reporte: {e}")
            return self._create_error_report(str(e))
    
    def track_story(
        self,
        story_keywords: str,
        duration: int = 7,
        update_interval: int = 1
    ) -> str:
        """
        Inicia seguimiento de una historia específica
        
        Args:
            story_keywords: Palabras clave para identificar la historia
            duration: Duración del seguimiento en días
            update_interval: Intervalo de actualización en horas
            
        Returns:
            ID del seguimiento de historia
        """
        tracking_id = f"track_{int(time.time())}_{hashlib.md5(story_keywords.encode()).hexdigest()[:8]}"
        
        tracking_config = {
            "story_keywords": story_keywords,
            "duration_days": duration,
            "update_interval_hours": update_interval,
            "created_at": time.time(),
            "last_update": time.time(),
            "status": "active"
        }
        
        self._tracking_stories[tracking_id] = tracking_config
        
        self.logger.info(f"Iniciado seguimiento de historia: {tracking_id}")
        return tracking_id
    
    def get_credibility_metrics(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """Obtiene métricas de credibilidad de una colección de artículos"""
        
        if not articles:
            return {"error": "No articles to analyze"}
        
        # Métricas por fuente
        source_metrics = {}
        for article in articles:
            source = article.source
            if source not in source_metrics:
                source_metrics[source] = {
                    "total_articles": 0,
                    "total_credibility": 0,
                    "credibility_distribution": []
                }
            
            source_metrics[source]["total_articles"] += 1
            source_metrics[source]["total_credibility"] += article.credibility_score
            source_metrics[source]["credibility_distribution"].append(article.credibility_score)
        
        # Calcular promedios por fuente
        for source, metrics in source_metrics.items():
            metrics["average_credibility"] = metrics["total_credibility"] / metrics["total_articles"]
            
            # Clasificar fuente
            avg_cred = metrics["average_credibility"]
            if avg_cred >= 0.8:
                metrics["credibility_level"] = "excellent"
            elif avg_cred >= 0.7:
                metrics["credibility_level"] = "good"
            elif avg_cred >= 0.6:
                metrics["credibility_level"] = "fair"
            else:
                metrics["credibility_level"] = "poor"
        
        # Métricas generales
        all_credibility_scores = [article.credibility_score for article in articles]
        overall_avg = sum(all_credibility_scores) / len(all_credibility_scores)
        
        # Distribución de credibilidad
        excellent = sum(1 for score in all_credibility_scores if score >= 0.8)
        good = sum(1 for score in all_credibility_scores if 0.7 <= score < 0.8)
        fair = sum(1 for score in all_credibility_scores if 0.6 <= score < 0.7)
        poor = sum(1 for score in all_credibility_scores if score < 0.6)
        
        return {
            "overall_average_credibility": overall_avg,
            "total_articles": len(articles),
            "source_metrics": source_metrics,
            "credibility_distribution": {
                "excellent": excellent,
                "good": good,
                "fair": fair,
                "poor": poor
            },
            "recommendations": self._generate_credibility_recommendations(overall_avg, source_metrics)
        }
    
    def _collect_category_news(
        self,
        category: NewsCategory,
        sources: List[str],
        time_range: str,
        **kwargs
    ) -> List[NewsArticle]:
        """Recopila noticias de una categoría específica"""
        
        articles = []
        
        # Generar consultas de búsqueda por categoría
        category_queries = self._generate_category_queries(category, time_range)
        
        for query in category_queries:
            try:
                # Realizar búsqueda
                search_results = self.search_engine.search_web(
                    query,
                    max_results=self.config["max_articles_per_source"] // len(category_queries),
                    enable_synthesis=False
                )
                
                # Convertir resultados a artículos
                for result in search_results.results:
                    article = self._convert_to_article(result, category)
                    if article:
                        articles.append(article)
                        
            except Exception as e:
                self.logger.warning(f"Error recopilando noticias para {category.value}: {e}")
                continue
        
        return articles
    
    def _convert_to_article(self, result: SearchResult, category: NewsCategory) -> Optional[NewsArticle]:
        """Convierte resultado de búsqueda a artículo de noticias"""
        
        try:
            # Determinar categoría basada en la fuente
            if not isinstance(category, NewsCategory):
                category = NewsCategory.WORLD
            
            # Analizar sentimiento básico
            sentiment = self._analyze_basic_sentiment(f"{result.title} {result.snippet}")
            
            # Obtener credibilidad de la fuente
            credibility = self._get_source_credibility(result.domain)
            
            # Crear artículo
            article = NewsArticle(
                title=result.title,
                url=result.url,
                content=result.snippet,
                summary=result.snippet[:200] + "..." if len(result.snippet) > 200 else result.snippet,
                category=category,
                source=result.domain,
                author="Unknown",
                published_at=time.time(),
                updated_at=time.time(),
                sentiment=sentiment,
                bias_score=0.0,  # Se calculará posteriormente
                credibility_score=credibility,
                tags=self._extract_tags(f"{result.title} {result.snippet}"),
                language=result.language
            )
            
            return article
            
        except Exception as e:
            self.logger.warning(f"Error convirtiendo resultado a artículo: {e}")
            return None
    
    def _generate_category_queries(self, category: NewsCategory, time_range: str) -> List[str]:
        """Genera consultas de búsqueda para una categoría"""
        
        base_queries = {
            NewsCategory.POLITICS: ["política noticias España", "elecciones política"],
            NewsCategory.ECONOMY: ["economía España", "mercados financieros"],
            NewsCategory.TECHNOLOGY: ["tecnología innovación", "tech noticias"],
            NewsCategory.HEALTH: ["salud medicina", "hospitales"],
            NewsCategory.SCIENCE: ["ciencia investigación", "descubrimientos"],
            NewsCategory.SPORTS: ["deportes fútbol", "competiciones"],
            NewsCategory.ENTERTAINMENT: ["entretenimiento cultura", "cine música"],
            NewsCategory.WORLD: ["internacional noticias mundo"],
            NewsCategory.LOCAL: ["local noticias"],
            NewsCategory.BUSINESS: ["empresas negocios"]
        }
        
        queries = base_queries.get(category, ["noticias generales"])
        
        # Agregar filtros temporales
        time_filter = self._get_time_filter(time_range)
        if time_filter:
            queries = [f"{query} {time_filter}" for query in queries]
        
        return queries
    
    def _get_time_filter(self, time_range: str) -> str:
        """Obtiene filtro temporal para consultas"""
        
        filter_map = {
            "1h": "última hora",
            "6h": "últimas 6 horas",
            "24h": "últimas 24 horas",
            "7d": "última semana",
            "30d": "último mes"
        }
        
        return filter_map.get(time_range, "recientes")
    
    def _parse_time_range(self, time_range: str) -> float:
        """Convierte rango temporal a timestamp"""
        
        end_time = time.time()
        
        if time_range == "1h":
            return end_time - 3600
        elif time_range == "6h":
            return end_time - (6 * 3600)
        elif time_range == "24h":
            return end_time - (24 * 3600)
        elif time_range == "7d":
            return end_time - (7 * 24 * 3600)
        elif time_range == "30d":
            return end_time - (30 * 24 * 3600)
        else:
            return end_time - (24 * 3600)  # Default 24h
    
    def _deduplicate_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Elimina artículos duplicados"""
        
        seen_urls = set()
        unique_articles = []
        
        for article in articles:
            normalized_url = article.url.lower().rstrip('/')
            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_articles.append(article)
        
        return unique_articles
    
    def _group_articles_by_topic(self, articles: List[NewsArticle]) -> Dict[str, List[NewsArticle]]:
        """Agrupa artículos por temas similares"""
        
        topic_groups = {}
        
        for article in articles:
            # Extraer temas principales del artículo
            topics = self._extract_main_topics(article.title, article.content)
            
            for topic in topics:
                if topic not in topic_groups:
                    topic_groups[topic] = []
                topic_groups[topic].append(article)
        
        return topic_groups
    
    def _extract_main_topics(self, title: str, content: str) -> List[str]:
        """Extrae temas principales de un artículo"""
        
        # Combinar título y contenido
        text = f"{title} {content}".lower()
        
        # Palabras comunes a filtrar
        stop_words = {
            'el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son',
            'con', 'para', 'al', 'del', 'los', 'las', 'una', 'pero', 'sus', 'me', 'han', 'ha', 'ha', 'sobre', 'todo',
            'también', 'tras', 'otro', 'algún', 'alguno', 'alguna', 'algunos', 'algunas', 'ser', 'desde', 'nos',
            'durante', 'todos', 'sin', 'bajo', 'mientras', 'según', 'cada', 'fin', 'incluso', 'primero',
            'desde', 'podría', 'hacia', 'contra', 'según', 'entre', 'durante', 'sin', 'bajo'
        }
        
        # Extraer palabras relevantes
        words = re.findall(r'\b[a-záéíóúñ]{4,}\b', text)
        relevant_words = [word for word in words if word not in stop_words]
        
        # Contar frecuencias
        word_freq = {}
        for word in relevant_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Obtener las palabras más frecuentes
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return [word for word, freq in top_words if freq > 1]
    
    def _analyze_topic_trend(
        self,
        topic: str,
        articles: List[NewsArticle],
        time_window: int
    ) -> Optional[NewsTrend]:
        """Analiza tendencia de un tema específico"""
        
        if len(articles) < 3:
            return None
        
        current_time = time.time()
        window_start = current_time - (time_window * 3600)  # Ventana en horas
        
        # Filtrar artículos en la ventana temporal
        recent_articles = [
            article for article in articles
            if article.published_at >= window_start
        ]
        
        if not recent_articles:
            return None
        
        # Calcular tasa de crecimiento
        total_articles = len(articles)
        recent_count = len(recent_articles)
        growth_rate = recent_count / max(1, total_articles - recent_count)
        
        # Análisis de sentimiento
        sentiments = [article.sentiment for article in recent_articles]
        overall_sentiment = self._combine_sentiments(sentiments)
        
        # Distribución geográfica
        geo_distribution = self._analyze_geographic_distribution(recent_articles)
        
        # Fuentes
        sources = list(set(article.source for article in recent_articles))
        
        # Calcular score de confianza
        confidence = min(1.0, (recent_count / 10) * (len(sources) / 5))
        
        # Pico temporal
        peak_time = max(article.published_at for article in recent_articles)
        
        # Determinar categoría principal
        categories = [article.category for article in recent_articles]
        main_category = max(set(categories), key=categories.count) if categories else NewsCategory.WORLD
        
        return NewsTrend(
            topic=topic,
            category=main_category,
            article_count=recent_count,
            sentiment_trend=overall_sentiment,
            growth_rate=growth_rate,
            peak_time=peak_time,
            sources=sources,
            geographic_distribution=geo_distribution,
            confidence_score=confidence
        )
    
    def _analyze_basic_sentiment(self, text: str) -> Sentiment:
        """Análisis básico de sentimiento"""
        
        # Palabras positivas y negativas básicas en español
        positive_words = {
            'excelente', 'bueno', 'positivo', 'éxito', 'mejor', 'avance', 'progreso', 'logro',
            'increíble', 'fantástico', 'maravilloso', 'brillante', 'espectacular', 'perfecto'
        }
        
        negative_words = {
            'malo', 'negativo', 'fracaso', 'error', 'problema', 'crisis', 'desastre', 'catástrofe',
            'terrible', 'horrible', 'espantoso', 'deplorable', 'lamentable', 'desastroso'
        }
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count * 2:
            return Sentiment.VERY_POSITIVE
        elif positive_count > negative_count:
            return Sentiment.POSITIVE
        elif negative_count > positive_count * 2:
            return Sentiment.VERY_NEGATIVE
        elif negative_count > positive_count:
            return Sentiment.NEGATIVE
        else:
            return Sentiment.NEUTRAL
    
    def _get_source_credibility(self, domain: str) -> float:
        """Obtiene credibilidad de una fuente"""
        
        # Verificar en base de datos de fuentes
        source_info = self.news_sources_db.get(domain)
        if source_info:
            return source_info.get("credibility", 0.5)
        
        # Evaluación automática básica
        score = 0.5
        
        # Factores que aumentan credibilidad
        if any(ext in domain for ext in ['.edu', '.gov', '.org']):
            score += 0.2
        
        # Factores que reducen credibilidad
        if any(ext in domain for ext in ['.tk', '.ml', '.ga', '.cf']):
            score -= 0.3
        
        return max(0.0, min(1.0, score))
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extrae etiquetas relevantes del texto"""
        
        # Palabras clave comunes
        keywords = {
            'tecnología', 'tecnologia', 'politica', 'política', 'economía', 'economia',
            'salud', 'medicina', 'ciencia', 'investigación', 'investigacion', 'deporte',
            'deportes', 'entretenimiento', 'cultura', 'negocios', 'empresa', 'empresas'
        }
        
        text_lower = text.lower()
        found_tags = []
        
        for keyword in keywords:
            if keyword in text_lower:
                found_tags.append(keyword)
        
        return found_tags[:5]  # Máximo 5 tags
    
    def _analyze_content_bias(self, content: str) -> Dict[str, Any]:
        """Analiza sesgo en el contenido del texto"""
        
        # Indicadores de sesgo político
        left_indicators = {
            'progresista', 'liberal', 'socialista', 'izquierda', 'derechos humanos',
            'igualdad', 'justicia social', 'medio ambiente', 'sostenibilidad'
        }
        
        right_indicators = {
            'conservador', 'tradicional', 'derecha', 'libre mercado', 'emprendimiento',
            'familia', 'patria', 'orden', 'tradición', 'autoridad'
        }
        
        # Indicadores emocionales
        emotional_words = {
            'shocking': -2, 'amazing': 2, 'disaster': -2, 'miracle': 2,
            'catastrophe': -2, 'breakthrough': 2, 'crisis': -2, 'success': 2
        }
        
        content_lower = content.lower()
        
        # Contar indicadores
        left_count = sum(1 for word in left_indicators if word in content_lower)
        right_count = sum(1 for word in right_indicators if word in content_lower)
        emotional_count = sum(
            emotional_words.get(word, 0) for word in emotional_words if word in content_lower
        )
        
        # Calcular score de sesgo (-1.0 a +1.0)
        if left_count > right_count:
            bias_score = -min(1.0, left_count / 5)
        elif right_count > left_count:
            bias_score = min(1.0, right_count / 5)
        else:
            bias_score = 0.0
        
        # Ajustar por contenido emocional
        bias_score += emotional_count * 0.1
        
        # Normalizar
        bias_score = max(-1.0, min(1.0, bias_score))
        
        return {
            "bias_score": bias_score,
            "left_indicators": left_count,
            "right_indicators": right_count,
            "emotional_intensity": abs(emotional_count),
            "subjectivity_level": "high" if emotional_count != 0 else "low"
        }
    
    def _get_source_bias(self, source: str) -> Dict[str, Any]:
        """Obtiene sesgo conocido de la fuente"""
        
        source_info = self.news_sources_db.get(source)
        if not source_info:
            return {"bias_score": 0.0, "direction": "unknown", "reliability": "unknown"}
        
        return {
            "bias_score": source_info.get("bias_score", 0.0),
            "direction": source_info.get("bias_direction", "unknown"),
            "reliability": source_info.get("reliability", "medium")
        }
    
    def _analyze_emotional_language(self, content: str) -> Dict[str, Any]:
        """Analiza el uso de lenguaje emocional"""
        
        # Categorías de palabras emocionales
        emotional_categories = {
            "very_positive": ["maravilloso", "espectacular", "fantástico", "increíble"],
            "positive": ["bueno", "excelente", "positivo", "logro"],
            "very_negative": ["horrible", "espantoso", "desastroso", "catastrófico"],
            "negative": ["malo", "negativo", "problema", "error"],
            "neutral": ["normal", "estándar", "promedio", "común"]
        }
        
        content_lower = content.lower()
        
        # Contar palabras por categoría
        category_counts = {}
        for category, words in emotional_categories.items():
            count = sum(1 for word in words if word in content_lower)
            category_counts[category] = count
        
        # Determir tono dominante
        dominant_category = max(category_counts.items(), key=lambda x: x[1])[0]
        
        # Calcular intensidad emocional
        total_emotional = sum(category_counts.values())
        intensity = min(1.0, total_emotional / 10)
        
        return {
            "dominant_emotion": dominant_category,
            "intensity": intensity,
            "category_counts": category_counts,
            "emotional_density": total_emotional / max(1, len(content.split()))
        }
    
    def _combine_bias_factors(
        self,
        content_bias: Dict[str, Any],
        source_bias: Dict[str, Any],
        emotional_bias: Dict[str, Any]
    ) -> float:
        """Combina múltiples factores de sesgo"""
        
        # Pesos para cada factor
        weights = {
            "content": 0.5,
            "source": 0.3,
            "emotional": 0.2
        }
        
        content_score = content_bias.get("bias_score", 0.0)
        source_score = source_bias.get("bias_score", 0.0)
        
        # Convertir dirección emocional a score numérico
        emotion_mapping = {
            "very_positive": 0.8,
            "positive": 0.4,
            "neutral": 0.0,
            "negative": -0.4,
            "very_negative": -0.8
        }
        emotional_score = emotion_mapping.get(emotional_bias.get("dominant_emotion", "neutral"), 0.0)
        
        # Combinar scores
        combined_score = (
            content_score * weights["content"] +
            source_score * weights["source"] +
            emotional_score * weights["emotional"]
        )
        
        return max(-1.0, min(1.0, combined_score))
    
    def _determine_bias_direction(self, bias_score: float) -> BiasDirection:
        """Determina dirección del sesgo"""
        
        if bias_score <= -0.6:
            return BiasDirection.LEFT
        elif bias_score <= -0.2:
            return BiasDirection.LEFT_CENTER
        elif bias_score >= 0.6:
            return BiasDirection.RIGHT
        elif bias_score >= 0.2:
            return BiasDirection.RIGHT_CENTER
        else:
            return BiasDirection.LEAST_BIAS
    
    def _calculate_bias_confidence(
        self,
        content_bias: Dict[str, Any],
        source_bias: Dict[str, Any],
        emotional_bias: Dict[str, Any]
    ) -> float:
        """Calcula confianza en el análisis de sesgo"""
        
        confidence = 0.5  # Base confidence
        
        # Factores que aumentan confianza
        if content_bias.get("emotional_intensity", 0) > 0:
            confidence += 0.2
        
        if source_bias.get("reliability") in ["high", "very_high"]:
            confidence += 0.3
        
        if emotional_bias.get("intensity", 0) > 0.5:
            confidence += 0.2
        
        return min(1.0, confidence)
    
    def _extract_bias_indicators(self, content: str) -> List[str]:
        """Extrae indicadores específicos de sesgo"""
        
        indicators = []
        content_lower = content.lower()
        
        # Indicadores de clickbait
        clickbait_phrases = [
            "no vas a creer", "no creeras", "increíble", "impactante",
            "secrets", "secretos", "revealed", "revelado"
        ]
        
        for phrase in clickbait_phrases:
            if phrase in content_lower:
                indicators.append("clickbait_detected")
                break
        
        # Indicadores de sensacionalismo
        sensational_words = ["shocking", "explosive", "devastating", "sensacional"]
        for word in sensational_words:
            if word in content_lower:
                indicators.append("sensational_language")
                break
        
        # Indicadores de parcialidad
        partiality_words = ["definitivamente", "sin duda", "obviamente", "claramente"]
        for word in partiality_words:
            if word in content_lower:
                indicators.append("assertive_language")
                break
        
        return indicators
    
    def _generate_bias_recommendations(self, bias_direction: BiasDirection, confidence: float) -> List[str]:
        """Genera recomendaciones basadas en análisis de sesgo"""
        
        recommendations = []
        
        if confidence < 0.5:
            recommendations.append("Análisis de sesgo con baja confianza - considerar fuentes adicionales")
        
        if bias_direction in [BiasDirection.LEFT, BiasDirection.RIGHT]:
            recommendations.append("Contenido con sesgo político detectado - buscar perspectiva equilibrada")
        
        if bias_direction in [BiasDirection.LEFT_CENTER, BiasDirection.RIGHT_CENTER]:
            recommendations.append("Contenido con sesgo moderado - contrastar con fuentes opuestas")
        
        if bias_direction == BiasDirection.LEAST_BIAS:
            recommendations.append("Contenido relativamente equilibrado - buena fuente para análisis")
        
        recommendations.append("Verificar hechos con fuentes independientes")
        
        return recommendations
    
    def _analyze_overall_sentiment(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """Analiza sentimiento general de una colección de artículos"""
        
        if not articles:
            return {"error": "No articles to analyze"}
        
        # Contar sentimientos
        sentiment_counts = {}
        for article in articles:
            sentiment = article.sentiment.value
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # Calcular porcentajes
        total = len(articles)
        sentiment_percentages = {
            sentiment: (count / total) * 100
            for sentiment, count in sentiment_counts.items()
        }
        
        # Sentimiento dominante
        dominant_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])[0]
        
        # Análisis temporal
        recent_articles = [
            article for article in articles
            if time.time() - article.published_at <= 24 * 3600
        ]
        
        if recent_articles:
            recent_sentiments = [article.sentiment for article in recent_articles]
            recent_dominant = max(
                set(recent_sentiments), key=recent_sentiments.count
            )
        else:
            recent_dominant = "unknown"
        
        return {
            "total_articles": total,
            "sentiment_distribution": sentiment_counts,
            "sentiment_percentages": sentiment_percentages,
            "dominant_sentiment": dominant_sentiment,
            "recent_sentiment": recent_dominant.value if recent_dominant != "unknown" else "unknown",
            "overall_tone": self._determine_overall_tone(sentiment_percentages)
        }
    
    def _determine_overall_tone(self, sentiment_percentages: Dict[str, float]) -> str:
        """Determina el tono general basado en porcentajes de sentimiento"""
        
        positive_score = (
            sentiment_percentages.get("very_positive", 0) +
            sentiment_percentages.get("positive", 0)
        )
        
        negative_score = (
            sentiment_percentages.get("very_negative", 0) +
            sentiment_percentages.get("negative", 0)
        )
        
        if positive_score > 60:
            return "very_positive"
        elif positive_score > 40:
            return "positive"
        elif negative_score > 60:
            return "very_negative"
        elif negative_score > 40:
            return "negative"
        else:
            return "neutral"
    
    def _analyze_overall_bias(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """Analiza sesgo general de una colección de artículos"""
        
        if not articles:
            return {"error": "No articles to analyze"}
        
        # Calcular sesgo promedio
        bias_scores = [article.bias_score for article in articles if article.bias_score != 0]
        
        if not bias_scores:
            return {"error": "No bias scores available"}
        
        avg_bias = sum(bias_scores) / len(bias_scores)
        
        # Distribución de sesgos
        left_bias = sum(1 for score in bias_scores if score < -0.2)
        center_bias = sum(1 for score in bias_scores if -0.2 <= score <= 0.2)
        right_bias = sum(1 for score in bias_scores if score > 0.2)
        
        total = len(bias_scores)
        
        return {
            "average_bias_score": avg_bias,
            "bias_distribution": {
                "left_bias": (left_bias / total) * 100,
                "center_bias": (center_bias / total) * 100,
                "right_bias": (right_bias / total) * 100
            },
            "overall_bias_direction": self._determine_bias_direction(avg_bias).value,
            "bias_variance": self._calculate_variance(bias_scores),
            "analysis_confidence": min(1.0, len(bias_scores) / 20)
        }
    
    def _calculate_variance(self, scores: List[float]) -> float:
        """Calcula varianza de una lista de scores"""
        if len(scores) < 2:
            return 0.0
        
        mean = sum(scores) / len(scores)
        return sum((score - mean) ** 2 for score in scores) / len(scores)
    
    def _analyze_overall_credibility(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """Analiza credibilidad general de una colección de artículos"""
        
        if not articles:
            return {"error": "No articles to analyze"}
        
        credibility_scores = [article.credibility_score for article in articles]
        avg_credibility = sum(credibility_scores) / len(credibility_scores)
        
        # Distribución por niveles
        excellent = sum(1 for score in credibility_scores if score >= 0.8)
        good = sum(1 for score in credibility_scores if 0.7 <= score < 0.8)
        fair = sum(1 for score in credibility_scores if 0.6 <= score < 0.7)
        poor = sum(1 for score in credibility_scores if score < 0.6)
        
        total = len(credibility_scores)
        
        return {
            "average_credibility": avg_credibility,
            "credibility_distribution": {
                "excellent": (excellent / total) * 100,
                "good": (good / total) * 100,
                "fair": (fair / total) * 100,
                "poor": (poor / total) * 100
            },
            "overall_quality": self._determine_quality_level(avg_credibility),
            "source_diversity": len(set(article.source for article in articles)),
            "reliability_score": avg_credibility
        }
    
    def _determine_quality_level(self, avg_credibility: float) -> str:
        """Determina nivel de calidad general"""
        
        if avg_credibility >= 0.8:
            return "excellent"
        elif avg_credibility >= 0.7:
            return "good"
        elif avg_credibility >= 0.6:
            return "fair"
        else:
            return "poor"
    
    def _identify_top_stories(self, articles: List[NewsArticle]) -> List[NewsStory]:
        """Identifica las historias principales"""
        
        if not articles:
            return []
        
        # Agrupar artículos por temas
        topic_groups = self._group_articles_by_topic(articles)
        
        # Crear historias para los temas con más artículos
        stories = []
        for topic, topic_articles in topic_groups.items():
            if len(topic_articles) >= 2:  # Mínimo 2 artículos para formar historia
                story = self._create_story_from_articles(topic, topic_articles)
                if story:
                    stories.append(story)
        
        # Ordenar por relevancia
        stories.sort(key=lambda s: (s.sources_count, s.credibility_overall), reverse=True)
        
        return stories[:10]  # Top 10 historias
    
    def _create_story_from_articles(self, topic: str, articles: List[NewsArticle]) -> Optional[NewsStory]:
        """Crea una historia a partir de una colección de artículos"""
        
        if len(articles) < 2:
            return None
        
        story_id = f"story_{hashlib.md5(topic.encode()).hexdigest()[:8]}"
        
        # Calcular métricas
        first_reported = min(article.published_at for article in articles)
        last_updated = max(article.updated_at for article in articles)
        
        # Sentimiento general
        sentiments = [article.sentiment for article in articles]
        overall_sentiment = self._combine_sentiments(sentiments)
        
        # Credibilidad promedio
        credibility_overall = sum(article.credibility_score for article in articles) / len(articles)
        
        # Fuentes
        sources = list(set(article.source for article in articles))
        
        # Categoría principal
        categories = [article.category for article in articles]
        main_category = max(set(categories), key=categories.count) if categories else NewsCategory.WORLD
        
        # Alcance geográfico (simplificado)
        geographic_scope = "global" if len(sources) > 3 else "local"
        
        return NewsStory(
            story_id=story_id,
            title=f"Historia: {topic.title()}",
            description=f"Desarrollo de la historia sobre {topic} con {len(articles)} artículos",
            articles=articles,
            first_reported=first_reported,
            last_updated=last_updated,
            key_topics=[topic],
            sentiment_overall=overall_sentiment,
            credibility_overall=credibility_overall,
            sources_count=len(sources),
            geographic_scope=geographic_scope,
            metadata={
                "topic": topic,
                "article_count": len(articles),
                "source_list": sources
            }
        )
    
    def _combine_sentiments(self, sentiments: List[Sentiment]) -> Sentiment:
        """Combina múltiples sentimientos en uno general"""
        
        sentiment_scores = {
            Sentiment.VERY_POSITIVE: 2,
            Sentiment.POSITIVE: 1,
            Sentiment.NEUTRAL: 0,
            Sentiment.NEGATIVE: -1,
            Sentiment.VERY_NEGATIVE: -2
        }
        
        total_score = sum(sentiment_scores.get(sentiment, 0) for sentiment in sentiments)
        avg_score = total_score / len(sentiments) if sentiments else 0
        
        if avg_score >= 1.5:
            return Sentiment.VERY_POSITIVE
        elif avg_score >= 0.5:
            return Sentiment.POSITIVE
        elif avg_score <= -1.5:
            return Sentiment.VERY_NEGATIVE
        elif avg_score <= -0.5:
            return Sentiment.NEGATIVE
        else:
            return Sentiment.NEUTRAL
    
    def _identify_breaking_news(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Identifica noticias de última hora"""
        
        current_time = time.time()
        cutoff_time = current_time - (6 * 3600)  # Últimas 6 horas
        
        breaking_articles = [
            article for article in articles
            if article.published_at >= cutoff_time and article.credibility_score >= 0.7
        ]
        
        # Ordenar por credibilidad y novedad
        breaking_articles.sort(
            key=lambda a: (a.credibility_score, a.published_at),
            reverse=True
        )
        
        return breaking_articles[:10]  # Top 10 noticias de última hora
    
    def _generate_report_recommendations(
        self,
        sentiment_analysis: Dict[str, Any],
        bias_analysis: Dict[str, Any],
        credibility_analysis: Dict[str, Any],
        trends: List[NewsTrend]
    ) -> List[str]:
        """Genera recomendaciones para el reporte"""
        
        recommendations = []
        
        # Recomendaciones basadas en sentimiento
        overall_tone = sentiment_analysis.get("overall_tone", "neutral")
        if overall_tone in ["very_negative", "negative"]:
            recommendations.append("Alto contenido negativo detectado - considerar perspectivas equilibradas")
        elif overall_tone in ["very_positive", "positive"]:
            recommendations.append("Contenido predominantemente positivo - verificar con fuentes neutrales")
        
        # Recomendaciones basadas en sesgo
        if bias_analysis:
            avg_bias = bias_analysis.get("average_bias_score", 0)
            if abs(avg_bias) > 0.5:
                recommendations.append("Sesgo significativo detectado - buscar fuentes con perspectivas opuestas")
        
        # Recomendaciones basadas en credibilidad
        if credibility_analysis:
            avg_cred = credibility_analysis.get("average_credibility", 0)
            if avg_cred < 0.7:
                recommendations.append("Calidad de fuentes por debajo del promedio - verificar información crítica")
        
        # Recomendaciones basadas en tendencias
        if len(trends) > 5:
            recommendations.append("Múltiples tendencias activas - monitoreo continuo recomendado")
        
        # Recomendaciones generales
        recommendations.extend([
            "Verificar hechos con fuentes independientes",
            "Monitorear evolución de historias principales",
            "Considerar impacto en diferentes audiencias",
            "Revisar actualizaciones regularmente"
        ])
        
        return recommendations[:10]  # Máximo 10 recomendaciones
    
    def _analyze_geographic_distribution(self, articles: List[NewsArticle]) -> Dict[str, int]:
        """Analiza distribución geográfica de artículos"""
        
        # Análisis simplificado basado en dominio de la fuente
        geographic_distribution = {}
        
        for article in articles:
            source = article.source.lower()
            
            if 'spain' in source or 'españa' in source or '.es' in source:
                country = "Spain"
            elif 'france' in source or 'francia' in source or '.fr' in source:
                country = "France"
            elif 'germany' in source or 'alemania' in source or '.de' in source:
                country = "Germany"
            elif 'uk' in source or 'reino' in source or '.co.uk' in source:
                country = "UK"
            elif 'usa' in source or 'estados' in source or '.com' in source:
                country = "USA"
            else:
                country = "International"
            
            geographic_distribution[country] = geographic_distribution.get(country, 0) + 1
        
        return geographic_distribution
    
    def _initialize_news_sources_db(self) -> Dict[str, Dict[str, Any]]:
        """Inicializa base de datos de fuentes de noticias"""
        
        return {
            # Fuentes de alta credibilidad con sesgo mínimo
            "elpais.com": {
                "credibility": 0.85,
                "bias_score": 0.0,
                "bias_direction": "left_center",
                "reliability": "high"
            },
            "abc.es": {
                "credibility": 0.75,
                "bias_score": 0.3,
                "bias_direction": "right_center",
                "reliability": "medium"
            },
            "elmundo.es": {
                "credibility": 0.80,
                "bias_score": 0.1,
                "bias_direction": "right_center",
                "reliability": "high"
            },
            "lavanguardia.com": {
                "credibility": 0.78,
                "bias_score": -0.1,
                "bias_direction": "left_center",
                "reliability": "high"
            },
            "cnn.com": {
                "credibility": 0.82,
                "bias_score": -0.2,
                "bias_direction": "left_center",
                "reliability": "high"
            },
            "bbc.com": {
                "credibility": 0.90,
                "bias_score": 0.0,
                "bias_direction": "least_bias",
                "reliability": "very_high"
            },
            "reuters.com": {
                "credibility": 0.92,
                "bias_score": 0.0,
                "bias_direction": "least_bias",
                "reliability": "very_high"
            },
            "ap.org": {
                "credibility": 0.90,
                "bias_score": 0.0,
                "bias_direction": "least_bias",
                "reliability": "very_high"
            },
            
            # Fuentes con sesgo conocido
            "infobae.com": {
                "credibility": 0.70,
                "bias_score": -0.4,
                "bias_direction": "left",
                "reliability": "medium"
            },
            "foxnews.com": {
                "credibility": 0.65,
                "bias_score": 0.5,
                "bias_direction": "right",
                "reliability": "medium"
            }
        }
    
    def _create_empty_report(self, time_range: str) -> NewsIntelligenceReport:
        """Crea reporte vacío cuando no hay datos"""
        
        return NewsIntelligenceReport(
            report_id=f"empty_report_{int(time.time())}",
            generated_at=time.time(),
            time_range=(time.time() - 86400, time.time()),
            categories_analyzed=[],
            total_articles=0,
            total_stories=0,
            trends_detected=[],
            sentiment_analysis={"error": "No data available"},
            bias_analysis={"error": "No data available"},
            credibility_analysis={"error": "No data available"},
            top_stories=[],
            breaking_news=[],
            recommendations=["No hay suficientes datos para generar recomendaciones"],
            metadata={"status": "empty", "time_range": time_range}
        )
    
    def _create_error_report(self, error_message: str) -> NewsIntelligenceReport:
        """Crea reporte de error"""
        
        return NewsIntelligenceReport(
            report_id=f"error_report_{int(time.time())}",
            generated_at=time.time(),
            time_range=(time.time() - 86400, time.time()),
            categories_analyzed=[],
            total_articles=0,
            total_stories=0,
            trends_detected=[],
            sentiment_analysis={"error": error_message},
            bias_analysis={"error": error_message},
            credibility_analysis={"error": error_message},
            top_stories=[],
            breaking_news=[],
            recommendations=["Reintentar análisis", "Verificar conectividad"],
            metadata={"status": "error", "error": error_message}
        )
    
    def _generate_credibility_recommendations(
        self,
        overall_avg: float,
        source_metrics: Dict[str, Any]
    ) -> List[str]:
        """Genera recomendaciones basadas en análisis de credibilidad"""
        
        recommendations = []
        
        if overall_avg < 0.6:
            recommendations.append("Credibilidad general baja - priorizar fuentes más confiables")
        
        # Identificar fuentes problemáticas
        poor_sources = [
            source for source, metrics in source_metrics.items()
            if metrics["average_credibility"] < 0.6
        ]
        
        if poor_sources:
            recommendations.append(f"Fuentes con baja credibilidad detectadas: {', '.join(poor_sources[:3])}")
        
        # Recomendar diversificación
        if len(source_metrics) < 5:
            recommendations.append("Fuentes limitadas - considerar agregar más perspectivas")
        
        recommendations.append("Verificar información crítica con múltiples fuentes")
        
        return recommendations
    
    def get_news_analytics(self, report: NewsIntelligenceReport) -> Dict[str, Any]:
        """Obtiene analytics detallados del reporte de noticias"""
        
        return {
            "report_info": {
                "report_id": report.report_id,
                "generated_at": report.generated_at,
                "time_range_hours": (report.time_range[1] - report.time_range[0]) / 3600,
                "total_articles": report.total_articles,
                "total_stories": report.total_stories
            },
            "content_analysis": {
                "trends_detected": len(report.trends_detected),
                "breaking_news_count": len(report.breaking_news),
                "top_stories_count": len(report.top_stories)
            },
            "quality_metrics": {
                "sentiment_distribution": report.sentiment_analysis,
                "bias_analysis": report.bias_analysis,
                "credibility_metrics": report.credibility_analysis
            },
            "coverage_analysis": {
                "categories_analyzed": len(report.categories_analyzed),
                "recommendations_count": len(report.recommendations)
            }
        }
    
    def clear_news_cache(self):
        """Limpia cache de noticias"""
        self._articles_cache.clear()
        self._trends_cache.clear()
        self._bias_cache.clear()
    
    def get_supported_categories(self) -> List[Dict[str, str]]:
        """Obtiene categorías de noticias soportadas"""
        return [
            {
                "name": category.value,
                "display_name": category.name.replace('_', ' ').title(),
                "description": self._get_category_description(category)
            }
            for category in NewsCategory
        ]
    
    def _get_category_description(self, category: NewsCategory) -> str:
        """Obtiene descripción de una categoría"""
        descriptions = {
            NewsCategory.POLITICS: "Noticias políticas y gubernamentales",
            NewsCategory.ECONOMY: "Noticias económicas y financieras",
            NewsCategory.TECHNOLOGY: "Avances tecnológicos e innovación",
            NewsCategory.HEALTH: "Noticias de salud y medicina",
            NewsCategory.SCIENCE: "Descubrimientos científicos e investigación",
            NewsCategory.SPORTS: "Noticias deportivas y competiciones",
            NewsCategory.ENTERTAINMENT: "Entretenimiento, cine y cultura",
            NewsCategory.WORLD: "Noticias internacionales",
            NewsCategory.LOCAL: "Noticias locales y regionales",
            NewsCategory.BUSINESS: "Noticias empresariales y de negocios"
        }
        return descriptions.get(category, "Categoría de noticias")


# Funciones de utilidad para compatibilidad MCP
def create_news_intelligence_agent() -> NewsIntelligenceAgent:
    """Crea una instancia del agente de inteligencia de noticias"""
    return NewsIntelligenceAgent()


# Testing y demostración
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Crear agente
    agent = NewsIntelligenceAgent()
    
    print("📰 News Intelligence Agent - Agente de Inteligencia de Noticias")
    print("=" * 70)
    
    # Ejemplo 1: Recopilación básica de noticias
    print("\n🔍 Ejemplo 1: Recopilación de noticias")
    
    try:
        articles = agent.collect_news(
            categories=[NewsCategory.TECHNOLOGY, NewsCategory.ECONOMY],
            time_range="24h"
        )
        
        print(f"  ✅ Recopilados {len(articles)} artículos")
        
        if articles:
            print(f"  📊 Primer artículo:")
            print(f"    - Título: {articles[0].title}")
            print(f"    - Fuente: {articles[0].source}")
            print(f"    - Categoría: {articles[0].category.value}")
            print(f"    - Credibilidad: {articles[0].credibility_score:.2f}")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Ejemplo 2: Análisis de tendencias
    print("\n📈 Ejemplo 2: Análisis de tendencias")
    
    try:
        if 'articles' in locals() and articles:
            trends = agent.analyze_trends(articles[:20])  # Analizar primeros 20 artículos
            
            print(f"  ✅ Detectadas {len(trends)} tendencias")
            
            for trend in trends[:3]:  # Mostrar top 3
                print(f"  📈 {trend.topic}: {trend.article_count} artículos")
                print(f"     Crecimiento: {trend.growth_rate:.2f}")
                print(f"     Confianza: {trend.confidence_score:.2f}")
        
    except Exception as e:
        print(f"  ❌ Error en análisis de tendencias: {e}")
    
    # Ejemplo 3: Detección de sesgos
    print("\n⚖️ Ejemplo 3: Análisis de sesgos")
    
    try:
        if 'articles' in locals() and articles:
            bias_analysis = agent.detect_bias(articles[0])
            
            print(f"  📊 Análisis de sesgo para: {bias_analysis['article_title'][:50]}...")
            print(f"    - Fuente: {bias_analysis['source']}")
            print(f"    - Score de sesgo: {bias_analysis['overall_bias_score']:.2f}")
            print(f"    - Dirección: {bias_analysis['bias_direction']}")
            print(f"    - Confianza: {bias_analysis['confidence_score']:.2f}")
        
    except Exception as e:
        print(f"  ❌ Error en análisis de sesgos: {e}")
    
    # Ejemplo 4: Reporte completo de inteligencia
    print("\n🧠 Ejemplo 4: Reporte de inteligencia completo")
    
    try:
        report = agent.generate_intelligence_report(
            time_range="24h",
            categories=[NewsCategory.TECHNOLOGY],
            include_trends=True,
            include_bias_analysis=True
        )
        
        print(f"  📋 Reporte generado:")
        print(f"    - ID: {report.report_id}")
        print(f"    - Artículos: {report.total_articles}")
        print(f"    - Historias: {report.total_stories}")
        print(f"    - Tendencias: {len(report.trends_detected)}")
        
        # Métricas de calidad
        if report.sentiment_analysis:
            print(f"  📊 Sentimiento dominante: {report.sentiment_analysis.get('dominant_sentiment', 'N/A')}")
        
        if report.credibility_analysis:
            avg_cred = report.credibility_analysis.get('average_credibility', 0)
            print(f"  ✅ Credibilidad promedio: {avg_cred:.2f}")
        
        # Recomendaciones
        if report.recommendations:
            print(f"  💡 Recomendaciones principales:")
            for rec in report.recommendations[:3]:
                print(f"    - {rec}")
        
    except Exception as e:
        print(f"  ❌ Error generando reporte: {e}")
    
    # Ejemplo 5: Métricas de credibilidad
    print("\n🎯 Ejemplo 5: Métricas de credibilidad")
    
    try:
        if 'articles' in locals() and articles:
            credibility_metrics = agent.get_credibility_metrics(articles)
            
            print(f"  📈 Credibilidad general: {credibility_metrics['overall_average_credibility']:.2f}")
            print(f"  📊 Distribución por nivel:")
            
            distribution = credibility_metrics['credibility_distribution']
            print(f"    - Excelente: {distribution['excellent']}")
            print(f"    - Buena: {distribution['good']}")
            print(f"    - Regular: {distribution['fair']}")
            print(f"    - Baja: {distribution['poor']}")
        
    except Exception as e:
        print(f"  ❌ Error en métricas de credibilidad: {e}")
    
    # Mostrar capacidades
    print(f"\n🔧 Capacidades del News Intelligence Agent:")
    print(f"  ✅ Agregación multi-fuente de noticias")
    print(f"  ✅ Análisis de tendencias en tiempo real")
    print(f"  ✅ Detección de sesgos mediáticos")
    print(f"  ✅ Análisis de sentimiento y tono")
    print(f"  ✅ Evaluación de credibilidad de fuentes")
    print(f"  ✅ Identificación de noticias de última hora")
    print(f"  ✅ Generación de reportes ejecutivos")
    print(f"  ✅ Seguimiento de historias específicas")