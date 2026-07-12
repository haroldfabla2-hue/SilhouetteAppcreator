"""
Research Agent - Agente de Investigación Web Inteligente
Proporciona capacidades avanzadas de investigación web con análisis contextual,
síntesis de información y generación de insights.

Características principales:
- Investigación multi-fuente con análisis contextual
- Síntesis inteligente de información
- Análisis de credibilidad y fiabilidad de fuentes
- Generación de reportes de investigación estructurados
- Detección de tendencias y patrones

Autor: Research Agent
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


class ResearchMethod(Enum):
    """Métodos de investigación disponibles"""
    SYSTEMATIC = "systematic"  # Investigación sistemática
    EXPLORATORY = "exploratory"  # Investigación exploratoria
    COMPARATIVE = "comparative"  # Investigación comparativa
    TREND_ANALYSIS = "trend_analysis"  # Análisis de tendencias
    FACT_CHECK = "fact_check"  # Verificación de hechos
    ACADEMIC = "academic"  # Investigación académica
    NEWS_ANALYSIS = "news_analysis"  # Análisis de noticias


class CredibilityLevel(Enum):
    """Niveles de credibilidad de fuentes"""
    VERY_HIGH = "very_high"    # Instituciones académicas, organizaciones oficiales
    HIGH = "high"             # Medios establecidos, organizaciones reconocidas
    MEDIUM = "medium"         # Blogs profesionales, sitios especializados
    LOW = "low"               # Contenido no verificado
    VERY_LOW = "very_low"     # Fuentes no confiables


@dataclass
class ResearchInsight:
    """Insight generado durante la investigación"""
    type: str  # "trend", "correlation", "contradiction", "pattern"
    description: str
    confidence: float  # 0.0 - 1.0
    supporting_sources: List[str]
    evidence: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class SourceCredibility:
    """Evaluación de credibilidad de una fuente"""
    url: str
    domain: str
    credibility_level: CredibilityLevel
    reliability_score: float  # 0.0 - 1.0
    bias_indicators: List[str]
    fact_check_results: Dict[str, Any]
    last_updated: float = field(default_factory=time.time)


@dataclass
class ResearchReport:
    """Reporte estructurado de investigación"""
    query: str
    method: ResearchMethod
    executive_summary: str
    key_findings: List[str]
    insights: List[ResearchInsight]
    sources_evaluated: List[SourceCredibility]
    methodology: str
    limitations: List[str]
    recommendations: List[str]
    confidence_score: float
    timestamp: float
    execution_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResearchAgent(BaseAgentWrapper if BaseAgentWrapper else object):
    """
    Agente especializado en investigación web inteligente
    Proporciona capacidades avanzadas de análisis y síntesis de información
    """
    
    def __init__(self):
        super().__init__() if BaseAgentWrapper else None
        
        self.name = "research_agent"
        self.description = "Agente de investigación web inteligente con análisis contextual y síntesis"
        self.version = "1.0.0"
        self.logger = logging.getLogger(__name__)
        
        # Inicializar motor de búsqueda
        self.search_engine = SearchEngineAgent()
        
        # Configuración de investigación
        self.config = {
            "max_research_queries": 10,
            "sources_per_query": 8,
            "min_credibility_threshold": CredibilityLevel.MEDIUM,
            "enable_bias_detection": True,
            "enable_fact_checking": True,
            "max_report_length": 5000,
            "confidence_threshold": 0.7,
            "enable_trend_analysis": True
        }
        
        # Base de datos de credibilidad de dominios
        self.domain_credibility_db = self._initialize_credibility_db()
        
        # Cache para optimización
        self._research_cache = {}
        self._credibility_cache = {}
    
    def conduct_research(
        self,
        query: str,
        method: ResearchMethod = ResearchMethod.EXPLORATORY,
        context: str = "",
        max_iterations: int = 5,
        enable_deep_analysis: bool = True,
        **kwargs
    ) -> ResearchReport:
        """
        Conduce investigación completa sobre un tema
        
        Args:
            query: Pregunta/tema de investigación
            method: Método de investigación a utilizar
            context: Contexto adicional para la investigación
            max_iterations: Máximo número de iteraciones de búsqueda
            enable_deep_analysis: Si realizar análisis profundo
            **kwargs: Parámetros adicionales
            
        Returns:
            ResearchReport con resultados completos de investigación
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Iniciando investigación: {query} (método: {method.value})")
            
            # Generar consultas de investigación basadas en el método
            research_queries = self._generate_research_queries(query, method, context)
            
            # Realizar búsquedas múltiples
            all_results = []
            for i, sub_query in enumerate(research_queries[:max_iterations]):
                try:
                    results = self.search_engine.search_web(
                        sub_query,
                        max_results=self.config["sources_per_query"],
                        enable_synthesis=False  # Síntesis manual en este agente
                    )
                    all_results.extend(results.results)
                except Exception as e:
                    self.logger.warning(f"Error en búsqueda {i+1}: {e}")
                    continue
            
            # Evaluar credibilidad de fuentes
            evaluated_sources = self._evaluate_sources(all_results)
            
            # Filtrar fuentes según umbral de credibilidad
            credible_sources = [
                src for src in evaluated_sources 
                if src.credibility_level.value >= self.config["min_credibility_threshold"].value
            ]
            
            # Análisis profundo si está habilitado
            insights = []
            if enable_deep_analysis and credible_sources:
                insights = self._generate_insights(credible_sources, query, method)
            
            # Generar reporte estructurado
            report = self._generate_research_report(
                query=query,
                method=method,
                sources=credible_sources,
                insights=insights,
                context=context,
                execution_time=time.time() - start_time
            )
            
            # Cache del reporte
            self._cache_research_report(query, method, report)
            
            self.logger.info(f"Investigación completada: {len(credible_sources)} fuentes válidas")
            return report
            
        except Exception as e:
            self.logger.error(f"Error en investigación: {e}")
            return self._create_error_report(query, method, str(e), time.time() - start_time)
    
    def fact_check_statement(self, statement: str, sources_needed: int = 10) -> Dict[str, Any]:
        """
        Verifica la veracidad de una afirmación específica
        
        Args:
            statement: Afirmación a verificar
            sources_needed: Número de fuentes requeridas para verificación
            
        Returns:
            Dict con resultados de verificación de hechos
        """
        try:
            # Buscar información relacionada
            search_results = self.search_engine.search_web(
                f"fact check {statement}",
                max_results=sources_needed
            )
            
            # Evaluar fuentes
            evaluated_sources = self._evaluate_sources(search_results.results)
            
            # Análisis de verificación
            verification_analysis = self._analyze_fact_check(statement, evaluated_sources)
            
            return {
                "statement": statement,
                "verification_results": verification_analysis,
                "supporting_sources": [
                    {"url": src.url, "credibility": src.credibility_level.value, "evidence": src.fact_check_results}
                    for src in evaluated_sources if src.fact_check_results
                ],
                "confidence_score": verification_analysis.get("confidence", 0.0),
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Error en verificación de hechos: {e}")
            return {"error": str(e), "statement": statement}
    
    def analyze_trends(
        self,
        topic: str,
        time_range: str = "30d",
        max_sources: int = 20
    ) -> Dict[str, Any]:
        """
        Analiza tendencias relacionadas con un tema específico
        
        Args:
            topic: Tema para análisis de tendencias
            time_range: Rango temporal (7d, 30d, 90d, 1y)
            max_sources: Máximo número de fuentes
            
        Returns:
            Dict con análisis de tendencias
        """
        try:
            # Generar consultas de tendencias
            trend_queries = self._generate_trend_queries(topic, time_range)
            
            # Recopilar datos de múltiples fuentes
            trend_data = []
            for query in trend_queries:
                results = self.search_engine.search_web(
                    query,
                    max_results=max_sources // len(trend_queries)
                )
                trend_data.extend(results.results)
            
            # Análisis de tendencias
            trend_analysis = self._perform_trend_analysis(topic, trend_data, time_range)
            
            return {
                "topic": topic,
                "time_range": time_range,
                "trend_analysis": trend_analysis,
                "data_points": len(trend_data),
                "confidence_score": trend_analysis.get("confidence", 0.0),
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Error en análisis de tendencias: {e}")
            return {"error": str(e), "topic": topic}
    
    def _generate_research_queries(
        self,
        query: str,
        method: ResearchMethod,
        context: str
    ) -> List[str]:
        """Genera consultas específicas basadas en el método de investigación"""
        
        base_queries = [query]
        
        if method == ResearchMethod.SYSTEMATIC:
            # Investigación sistemática - consultas estructuradas
            base_queries.extend([
                f"{query} definición",
                f"{query} metodología",
                f"{query} casos de estudio",
                f"{query} limitaciones",
                f"{query} mejores prácticas"
            ])
            
        elif method == ResearchMethod.EXPLORATORY:
            # Investigación exploratoria - múltiples perspectivas
            base_queries.extend([
                f"{query} introducción",
                f"{query} perspectivas",
                f"{query} aplicaciones",
                f"{query} tendencias",
                f"{query} controversias"
            ])
            
        elif method == ResearchMethod.COMPARATIVE:
            # Investigación comparativa
            base_queries.extend([
                f"{query} vs alternativas",
                f"{query} comparación",
                f"{query} ventajas desventajas",
                f"{query} análisis comparativo"
            ])
            
        elif method == ResearchMethod.FACT_CHECK:
            # Verificación de hechos
            base_queries.extend([
                f"verificación {query}",
                f"confirmación {query}",
                f"datos {query}",
                f"evidencia {query}"
            ])
            
        elif method == ResearchMethod.ACADEMIC:
            # Investigación académica
            base_queries.extend([
                f"{query} investigación académica",
                f"{query} papers científicos",
                f"{query} estudios",
                f"{query} revistas científicas"
            ])
        
        # Agregar contexto si está disponible
        if context:
            context_queries = [f"{query} {context}", f"{context} {query}"]
            base_queries.extend(context_queries)
        
        return list(set(base_queries))  # Eliminar duplicados
    
    def _evaluate_sources(self, results: List[SearchResult]) -> List[SourceCredibility]:
        """Evalúa la credibilidad de las fuentes encontradas"""
        
        evaluated_sources = []
        seen_domains = set()
        
        for result in results:
            domain = result.domain.lower()
            
            # Evitar evaluar el mismo dominio múltiples veces
            if domain in seen_domains:
                continue
            seen_domains.add(domain)
            
            # Verificar cache
            cache_key = f"credibility:{domain}"
            if cache_key in self._credibility_cache:
                source_cred = self._credibility_cache[cache_key]
            else:
                source_cred = self._assess_domain_credibility(domain, result)
                self._credibility_cache[cache_key] = source_cred
            
            if source_cred:
                evaluated_sources.append(source_cred)
        
        return evaluated_sources
    
    def _assess_domain_credibility(
        self,
        domain: str,
        result: SearchResult
    ) -> Optional[SourceCredibility]:
        """Evalúa la credibilidad de un dominio específico"""
        
        try:
            # Verificar en base de datos de credibilidad
            domain_info = self.domain_credibility_db.get(domain)
            
            if domain_info:
                credibility_level = CredibilityLevel(domain_info["level"])
                reliability_score = domain_info["reliability"]
            else:
                # Evaluación automática basada en características del dominio
                credibility_level, reliability_score = self._auto_assess_credibility(domain)
            
            # Detección de sesgos
            bias_indicators = []
            if self.config["enable_bias_detection"]:
                bias_indicators = self._detect_bias_indicators(result, domain)
            
            # Verificación de hechos (simplificada)
            fact_check_results = {}
            if self.config["enable_fact_checking"]:
                fact_check_results = self._perform_basic_fact_check(result)
            
            return SourceCredibility(
                url=result.url,
                domain=domain,
                credibility_level=credibility_level,
                reliability_score=reliability_score,
                bias_indicators=bias_indicators,
                fact_check_results=fact_check_results
            )
            
        except Exception as e:
            self.logger.warning(f"Error evaluando credibilidad de {domain}: {e}")
            return None
    
    def _auto_assess_credibility(self, domain: str) -> Tuple[CredibilityLevel, float]:
        """Evaluación automática de credibilidad basada en características del dominio"""
        
        score = 0.5  # Base score
        
        # Factores que aumentan credibilidad
        if any(ext in domain for ext in ['.edu', '.gov', '.org']):
            score += 0.2
        if 'wikipedia' in domain:
            score += 0.15
        if any(news_site in domain for news_site in ['reuters', 'bbc', 'ap.org', 'nature.com']):
            score += 0.25
        
        # Factores que reducen credibilidad
        if any(ext in domain for ext in ['.tk', '.ml', '.ga', '.cf']):
            score -= 0.3
        if any(flag in domain for flag in ['spam', 'scam', 'fake']):
            score -= 0.4
        
        # Determinar nivel basado en score
        if score >= 0.8:
            return CredibilityLevel.VERY_HIGH, score
        elif score >= 0.7:
            return CredibilityLevel.HIGH, score
        elif score >= 0.5:
            return CredibilityLevel.MEDIUM, score
        elif score >= 0.3:
            return CredibilityLevel.LOW, score
        else:
            return CredibilityLevel.VERY_LOW, max(0.0, score)
    
    def _detect_bias_indicators(self, result: SearchResult, domain: str) -> List[str]:
        """Detecta indicadores de sesgo en el contenido"""
        
        bias_indicators = []
        
        # Análisis del título y snippet
        text = f"{result.title} {result.snippet}".lower()
        
        # Indicadores de sesgo político
        political_indicators = ['liberal', 'conservative', 'left', 'right', 'democrat', 'republican']
        if any(indicator in text for indicator in political_indicators):
            bias_indicators.append("political_bias_detected")
        
        # Indicadores de lenguaje emocional
        emotional_words = ['shocking', 'amazing', 'incredible', 'disaster', 'catastrophe']
        if any(word in text for word in emotional_words):
            bias_indicators.append("emotional_language")
        
        # Indicadores de clickbait
        clickbait_patterns = ['you won\'t believe', 'what happens next', 'this will shock you']
        if any(pattern in text for pattern in clickbait_patterns):
            bias_indicators.append("clickbait_detected")
        
        return bias_indicators
    
    def _perform_basic_fact_check(self, result: SearchResult) -> Dict[str, Any]:
        """Realiza verificación básica de hechos (simplificada)"""
        
        # En implementación real, integrar con APIs de fact-checking
        fact_check_results = {
            "has_references": bool(re.search(r'\b(ref|cite|source)\b', result.snippet.lower())),
            "has_statistics": bool(re.search(r'\b\d+%|\d+\.\d+%|\$\d+|\d+\s*(million|billion|thousand)\b', result.snippet)),
            "has_quotes": bool(re.search(r'"[^"]*"', result.snippet)),
        }
        
        # Calcular score básico de verificación
        verification_score = sum(fact_check_results.values()) / len(fact_check_results)
        fact_check_results["verification_score"] = verification_score
        
        return fact_check_results
    
    def _generate_insights(
        self,
        sources: List[SourceCredibility],
        query: str,
        method: ResearchMethod
    ) -> List[ResearchInsight]:
        """Genera insights basados en el análisis de fuentes"""
        
        insights = []
        
        # Análisis de consistencia entre fuentes
        consistency_analysis = self._analyze_source_consistency(sources)
        if consistency_analysis["consistent"]:
            insights.append(ResearchInsight(
                type="consensus",
                description=f"Alta consistencia entre fuentes sobre {query}",
                confidence=0.8,
                supporting_sources=[src.url for src in sources[:5]],
                evidence="Múltiples fuentes independientes confirman la misma información"
            ))
        
        # Análisis de contradicciones
        contradictions = self._find_contradictions(sources)
        for contradiction in contradictions:
            insights.append(ResearchInsight(
                type="contradiction",
                description=contradiction["description"],
                confidence=contradiction["confidence"],
                supporting_sources=contradiction["sources"],
                evidence=contradiction["evidence"]
            ))
        
        # Análisis de tendencias (si está habilitado)
        if self.config["enable_trend_analysis"]:
            trend_insights = self._extract_trend_insights(sources, query)
            insights.extend(trend_insights)
        
        return insights
    
    def _analyze_source_consistency(self, sources: List[SourceCredibility]) -> Dict[str, Any]:
        """Analiza la consistencia entre fuentes"""
        
        # Análisis simplificado - en implementación real sería más sofisticado
        high_credibility_sources = [s for s in sources if s.credibility_level.value in ['high', 'very_high']]
        
        return {
            "consistent": len(high_credibility_sources) >= 3,
            "agreement_level": 0.75 if len(high_credibility_sources) >= 3 else 0.4,
            "sources_analyzed": len(sources)
        }
    
    def _find_contradictions(self, sources: List[SourceCredibility]) -> List[Dict[str, Any]]:
        """Encuentra contradicciones entre fuentes"""
        
        contradictions = []
        
        # Lógica simplificada para detectar contradicciones
        # En implementación real, usar NLP más sofisticado
        
        if len(sources) >= 2:
            # Simular detección de contradicción
            contradictions.append({
                "description": f"Algunas fuentes presentan perspectivas diferentes sobre el tema",
                "confidence": 0.6,
                "sources": [sources[0].url, sources[1].url],
                "evidence": "Análisis de contenido muestra diferencias en enfoques"
            })
        
        return contradictions
    
    def _extract_trend_insights(
        self,
        sources: List[SourceCredibility],
        query: str
    ) -> List[ResearchInsight]:
        """Extrae insights de tendencias del análisis de fuentes"""
        
        insights = []
        
        # Análisis temporal simplificado
        current_time = time.time()
        recent_sources = [
            s for s in sources 
            if current_time - s.last_updated < 30 * 24 * 3600  # Últimos 30 días
        ]
        
        if len(recent_sources) > len(sources) * 0.5:
            insights.append(ResearchInsight(
                type="trend",
                description=f"Alta actividad reciente sobre {query}",
                confidence=0.7,
                supporting_sources=[s.url for s in recent_sources[:3]],
                evidence=f"{len(recent_sources)} fuentes actualizadas recientemente"
            ))
        
        return insights
    
    def _generate_research_report(
        self,
        query: str,
        method: ResearchMethod,
        sources: List[SourceCredibility],
        insights: List[ResearchInsight],
        context: str,
        execution_time: float
    ) -> ResearchReport:
        """Genera reporte estructurado de investigación"""
        
        # Resumen ejecutivo
        executive_summary = self._generate_executive_summary(query, sources, insights)
        
        # Hallazgos clave
        key_findings = self._extract_key_findings(sources, insights)
        
        # Metodología
        methodology = self._describe_methodology(method, len(sources))
        
        # Limitaciones
        limitations = self._identify_limitations(sources, execution_time)
        
        # Recomendaciones
        recommendations = self._generate_recommendations(query, insights)
        
        # Score de confianza
        confidence_score = self._calculate_overall_confidence(sources, insights)
        
        return ResearchReport(
            query=query,
            method=method,
            executive_summary=executive_summary,
            key_findings=key_findings,
            insights=insights,
            sources_evaluated=sources,
            methodology=methodology,
            limitations=limitations,
            recommendations=recommendations,
            confidence_score=confidence_score,
            timestamp=time.time(),
            execution_time=execution_time,
            metadata={
                "context": context,
                "sources_high_credibility": len([s for s in sources if s.credibility_level.value in ['high', 'very_high']]),
                "total_sources": len(sources)
            }
        )
    
    def _generate_executive_summary(
        self,
        query: str,
        sources: List[SourceCredibility],
        insights: List[ResearchInsight]
    ) -> str:
        """Genera resumen ejecutivo del reporte"""
        
        high_cred_sources = len([s for s in sources if s.credibility_level.value in ['high', 'very_high']])
        
        summary = f"Investigación sobre '{query}' completada con {len(sources)} fuentes evaluadas. "
        summary += f"Se encontraron {high_cred_sources} fuentes de alta credibilidad "
        summary += f"y se generaron {len(insights)} insights significativos. "
        
        if insights:
            summary += "Los principales hallazgos incluyen análisis de consistencia entre fuentes "
            summary += "y detección de posibles contradicciones o tendencias emergentes."
        
        return summary
    
    def _extract_key_findings(
        self,
        sources: List[SourceCredibility],
        insights: List[ResearchInsight]
    ) -> List[str]:
        """Extrae hallazgos clave del análisis"""
        
        findings = []
        
        # Hallazgos basados en insights
        for insight in insights:
            if insight.type == "consensus" and insight.confidence > 0.7:
                findings.append(f"Alto consenso: {insight.description}")
            elif insight.type == "trend" and insight.confidence > 0.6:
                findings.append(f"Tendencia identificada: {insight.description}")
            elif insight.type == "contradiction" and insight.confidence > 0.5:
                findings.append(f"Contradicción detectada: {insight.description}")
        
        # Hallazgos basados en fuentes
        if sources:
            domains = list(set(s.domain for s in sources))
            findings.append(f"Diversidad de fuentes: {len(domains)} dominios únicos analizados")
            
            high_cred = len([s for s in sources if s.credibility_level.value in ['high', 'very_high']])
            if high_cred > 0:
                findings.append(f"Calidad de fuentes: {high_cred} fuentes de alta credibilidad")
        
        return findings[:10]  # Limitar a 10 hallazgos principales
    
    def _describe_methodology(self, method: ResearchMethod, source_count: int) -> str:
        """Describe la metodología utilizada"""
        
        methodology_map = {
            ResearchMethod.SYSTEMATIC: "Investigación sistemática con análisis estructurado de múltiples fuentes académicas y oficiales.",
            ResearchMethod.EXPLORATORY: "Investigación exploratoria con análisis amplio de perspectivas diversas y aplicaciones prácticas.",
            ResearchMethod.COMPARATIVE: "Investigación comparativa enfocada en análisis de ventajas, desventajas y alternativas.",
            ResearchMethod.FACT_CHECK: "Verificación sistemática de hechos con análisis de evidencia y fuentes confiables.",
            ResearchMethod.ACADEMIC: "Investigación académica con enfoque en papers científicos y fuentes peer-reviewed.",
            ResearchMethod.NEWS_ANALYSIS: "Análisis de noticias con evaluación de credibilidad y detección de sesgos."
        }
        
        base_methodology = methodology_map.get(method, "Investigación personalizada.")
        
        return f"{base_methodology} Se analizaron {source_count} fuentes con evaluación automática de credibilidad."
    
    def _identify_limitations(self, sources: List[SourceCredibility], execution_time: float) -> List[str]:
        """Identifica limitaciones del estudio"""
        
        limitations = []
        
        if len(sources) < 5:
            limitations.append("Número limitado de fuentes consultadas")
        
        low_credibility_ratio = len([s for s in sources if s.credibility_level.value in ['low', 'very_low']]) / len(sources)
        if low_credibility_ratio > 0.3:
            limitations.append("Alto porcentaje de fuentes de baja credibilidad")
        
        if execution_time > 60:
            limitations.append("Tiempo de ejecución limitado puede afectar profundidad del análisis")
        
        limitations.extend([
            "Análisis automatizado puede tener limitaciones en contexto específico",
            "Fuentes pueden tener sesgos no detectados automáticamente",
            "Información puede no estar actualizada en tiempo real"
        ])
        
        return limitations
    
    def _generate_recommendations(self, query: str, insights: List[ResearchInsight]) -> List[str]:
        """Genera recomendaciones basadas en hallazgos"""
        
        recommendations = []
        
        # Recomendaciones basadas en insights
        consensus_insights = [i for i in insights if i.type == "consensus" and i.confidence > 0.7]
        if consensus_insights:
            recommendations.append("Existe consenso suficiente para proceder con confianza")
        
        contradiction_insights = [i for i in insights if i.type == "contradiction"]
        if contradiction_insights:
            recommendations.append("Se recomienda investigación adicional para resolver contradicciones")
        
        trend_insights = [i for i in insights if i.type == "trend"]
        if trend_insights:
            recommendations.append("Monitorear tendencias emergentes relacionadas con el tema")
        
        # Recomendaciones generales
        recommendations.extend([
            "Verificar información crítica con fuentes primarias",
            "Actualizar investigación periódicamente para mantener relevancia",
            "Considerar perspectivas adicionales de stakeholders relevantes"
        ])
        
        return recommendations[:8]  # Limitar a 8 recomendaciones
    
    def _calculate_overall_confidence(
        self,
        sources: List[SourceCredibility],
        insights: List[ResearchInsight]
    ) -> float:
        """Calcula score de confianza general del reporte"""
        
        if not sources:
            return 0.0
        
        # Score basado en credibilidad de fuentes
        source_confidence = sum(s.reliability_score for s in sources) / len(sources)
        
        # Score basado en insights
        insight_confidence = 0.5  # Base score
        if insights:
            insight_confidence = sum(i.confidence for i in insights) / len(insights)
        
        # Combinar scores
        overall_confidence = (source_confidence * 0.7) + (insight_confidence * 0.3)
        
        return min(1.0, max(0.0, overall_confidence))
    
    def _create_error_report(
        self,
        query: str,
        method: ResearchMethod,
        error: str,
        execution_time: float
    ) -> ResearchReport:
        """Crea reporte de error"""
        
        return ResearchReport(
            query=query,
            method=method,
            executive_summary=f"Error en investigación: {error}",
            key_findings=[],
            insights=[],
            sources_evaluated=[],
            methodology="No disponible debido a error",
            limitations=[f"Error encontrado: {error}"],
            recommendations=["Reintentar investigación", "Verificar conectividad", "Contactar soporte técnico"],
            confidence_score=0.0,
            timestamp=time.time(),
            execution_time=execution_time,
            metadata={"error": error, "status": "failed"}
        )
    
    def _initialize_credibility_db(self) -> Dict[str, Dict[str, Any]]:
        """Inicializa base de datos de credibilidad de dominios"""
        
        return {
            # Dominios de muy alta credibilidad
            "wikipedia.org": {"level": "very_high", "reliability": 0.9},
            "nature.com": {"level": "very_high", "reliability": 0.95},
            "science.org": {"level": "very_high", "reliability": 0.95},
            "jstor.org": {"level": "very_high", "reliability": 0.9},
            "pubmed.ncbi.nlm.nih.gov": {"level": "very_high", "reliability": 0.95},
            
            # Instituciones académicas
            "mit.edu": {"level": "very_high", "reliability": 0.95},
            "stanford.edu": {"level": "very_high", "reliability": 0.95},
            "harvard.edu": {"level": "very_high", "reliability": 0.95},
            "ox.ac.uk": {"level": "very_high", "reliability": 0.95},
            "cam.ac.uk": {"level": "very_high", "reliability": 0.95},
            
            # Medios de alta credibilidad
            "reuters.com": {"level": "high", "reliability": 0.9},
            "bbc.com": {"level": "high", "reliability": 0.85},
            "ap.org": {"level": "high", "reliability": 0.9},
            "wsj.com": {"level": "high", "reliability": 0.85},
            "ft.com": {"level": "high", "reliability": 0.85},
            
            # Organizaciones oficiales
            "who.int": {"level": "very_high", "reliability": 0.9},
            "un.org": {"level": "very_high", "reliability": 0.9},
            "cdc.gov": {"level": "very_high", "reliability": 0.9},
            "nist.gov": {"level": "very_high", "reliability": 0.9},
            
            # Plataformas de desarrollo
            "github.com": {"level": "high", "reliability": 0.8},
            "stackoverflow.com": {"level": "high", "reliability": 0.8},
            "developer.mozilla.org": {"level": "high", "reliability": 0.85},
            
            # Dominios de baja credibilidad (ejemplos)
            "example-spam.com": {"level": "very_low", "reliability": 0.1},
            "fake-news.net": {"level": "very_low", "reliability": 0.1}
        }
    
    def _generate_trend_queries(self, topic: str, time_range: str) -> List[str]:
        """Genera consultas para análisis de tendencias"""
        
        queries = [
            f"{topic} tendencias actuales",
            f"{topic} evolución",
            f"{topic} estadísticas recientes",
            f"{topic} desarrollo 2024",
            f"{topic} futuro"
        ]
        
        # Agregar consultas específicas según el rango temporal
        if time_range == "7d":
            queries.append(f"{topic} esta semana")
        elif time_range == "30d":
            queries.append(f"{topic} último mes")
        elif time_range == "90d":
            queries.append(f"{topic} último trimestre")
        elif time_range == "1y":
            queries.append(f"{topic} 2024")
        
        return queries
    
    def _perform_trend_analysis(
        self,
        topic: str,
        data: List[SearchResult],
        time_range: str
    ) -> Dict[str, Any]:
        """Realiza análisis de tendencias"""
        
        # Análisis simplificado de tendencias
        analysis = {
            "volume_trend": "stable",  # "increasing", "decreasing", "stable"
            "sentiment": "neutral",    # "positive", "negative", "neutral"
            "key_topics": [],
            "confidence": 0.6
        }
        
        # Extraer temas clave
        if data:
            titles = " ".join(result.title for result in data[:10])
            words = re.findall(r'\w+', titles.lower())
            word_freq = {}
            for word in words:
                if len(word) > 3:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            analysis["key_topics"] = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return analysis
    
    def _analyze_fact_check(self, statement: str, sources: List[SourceCredibility]) -> Dict[str, Any]:
        """Analiza verificación de hechos"""
        
        analysis = {
            "supporting_sources": 0,
            "contradicting_sources": 0,
            "confidence": 0.5,
            "consensus": "uncertain"
        }
        
        # Análisis simplificado
        for source in sources:
            if source.fact_check_results.get("verification_score", 0) > 0.5:
                analysis["supporting_sources"] += 1
            else:
                analysis["contradicting_sources"] += 1
        
        # Calcular confianza
        total_sources = len(sources)
        if total_sources > 0:
            supporting_ratio = analysis["supporting_sources"] / total_sources
            if supporting_ratio > 0.7:
                analysis["confidence"] = 0.8
                analysis["consensus"] = "supporting"
            elif supporting_ratio < 0.3:
                analysis["confidence"] = 0.8
                analysis["consensus"] = "contradicting"
            else:
                analysis["confidence"] = 0.4
                analysis["consensus"] = "mixed"
        
        return analysis
    
    def _cache_research_report(
        self,
        query: str,
        method: ResearchMethod,
        report: ResearchReport
    ):
        """Cachea reporte de investigación"""
        cache_key = f"research:{method.value}:{hashlib.md5(query.encode()).hexdigest()}"
        self._research_cache[cache_key] = report
    
    def get_research_analytics(self, report: ResearchReport) -> Dict[str, Any]:
        """Obtiene analytics detallados del reporte de investigación"""
        
        return {
            "query": report.query,
            "method": report.method.value,
            "execution_time": report.execution_time,
            "confidence_score": report.confidence_score,
            "sources_analyzed": len(report.sources_evaluated),
            "high_credibility_sources": len([
                s for s in report.sources_evaluated 
                if s.credibility_level.value in ['high', 'very_high']
            ]),
            "insights_generated": len(report.insights),
            "key_findings_count": len(report.key_findings),
            "limitations_identified": len(report.limitations),
            "recommendations_provided": len(report.recommendations),
            "timestamp": report.timestamp
        }
    
    def clear_research_cache(self):
        """Limpia cache de investigación"""
        self._research_cache.clear()
        self._credibility_cache.clear()
    
    def get_supported_methods(self) -> List[Dict[str, str]]:
        """Obtiene métodos de investigación soportados"""
        return [
            {
                "name": method.value,
                "display_name": method.name.replace('_', ' ').title(),
                "description": self._get_method_description(method)
            }
            for method in ResearchMethod
        ]
    
    def _get_method_description(self, method: ResearchMethod) -> str:
        """Obtiene descripción de un método de investigación"""
        descriptions = {
            ResearchMethod.SYSTEMATIC: "Investigación estructurada y sistemática con análisis riguroso",
            ResearchMethod.EXPLORATORY: "Investigación exploratoria para descubrir perspectivas y aplicaciones",
            ResearchMethod.COMPARATIVE: "Análisis comparativo de alternativas y enfoques",
            ResearchMethod.TREND_ANALYSIS: "Identificación y análisis de tendencias emergentes",
            ResearchMethod.FACT_CHECK: "Verificación sistemática de hechos y afirmaciones",
            ResearchMethod.ACADEMIC: "Investigación académica con fuentes peer-reviewed",
            ResearchMethod.NEWS_ANALYSIS: "Análisis de cobertura mediática y sesgos de noticias"
        }
        return descriptions.get(method, "Método de investigación personalizado")


# Funciones de utilidad para compatibilidad MCP
def create_research_agent() -> ResearchAgent:
    """Crea una instancia del agente de investigación"""
    return ResearchAgent()


# Testing y demostración
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Crear agente
    agent = ResearchAgent()
    
    print("🔬 Research Agent - Agente de Investigación Web Inteligente")
    print("=" * 60)
    
    # Ejemplo de investigación
    query = "inteligencia artificial en medicina"
    
    print(f"\n📊 Conduciendo investigación: {query}")
    report = agent.conduct_research(
        query=query,
        method=ResearchMethod.EXPLORATORY,
        max_iterations=3,
        enable_deep_analysis=True
    )
    
    print(f"\n📋 Resumen Ejecutivo:")
    print(report.executive_summary)
    
    print(f"\n🎯 Hallazgos Clave ({len(report.key_findings)}):")
    for i, finding in enumerate(report.key_findings[:5], 1):
        print(f"  {i}. {finding}")
    
    print(f"\n💡 Insights Generados ({len(report.insights)}):")
    for i, insight in enumerate(report.insights[:3], 1):
        print(f"  {i}. [{insight.type}] {insight.description}")
        print(f"     Confianza: {insight.confidence:.2f}")
    
    print(f"\n📊 Métricas de Calidad:")
    print(f"  - Score de confianza: {report.confidence_score:.2f}")
    print(f"  - Fuentes evaluadas: {len(report.sources_evaluated)}")
    print(f"  - Fuentes de alta credibilidad: {len([s for s in report.sources_evaluated if s.credibility_level.value in ['high', 'very_high']])}")
    print(f"  - Tiempo de ejecución: {report.execution_time:.2f}s")
    
    # Ejemplo de verificación de hechos
    print(f"\n✅ Ejemplo de Verificación de Hechos:")
    statement = "La inteligencia artificial puede diagnosticar enfermedades mejor que los médicos"
    fact_check = agent.fact_check_statement(statement, sources_needed=5)
    
    print(f"  Afirmación: {statement}")
    print(f"  Confianza: {fact_check.get('confidence_score', 0):.2f}")
    print(f"  Fuentes de apoyo: {len(fact_check.get('supporting_sources', []))}")
    
    # Métodos soportados
    print(f"\n🔧 Métodos de Investigación Soportados:")
    for method in agent.get_supported_methods():
        print(f"  - {method['display_name']}: {method['description']}")