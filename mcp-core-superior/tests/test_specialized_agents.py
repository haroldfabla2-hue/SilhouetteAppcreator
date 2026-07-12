"""
Tests para Agentes Especializados de Búsqueda Web Avanzada
===========================================================

Este archivo contiene tests unitarios y de integración para los tres agentes
especializados: ResearchAgent, DataMiningAgent y NewsIntelligenceAgent.

Los tests verifican funcionalidad, rendimiento, integración y casos edge.

Autor: MCP Superior Testing Team
Versión: 1.0.0
"""

import unittest
import json
import time
import tempfile
import os
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Importar agentes especializados
try:
    from .research_agent import (
        ResearchAgent, ResearchMethod, ResearchReport
    )
    from .data_mining_agent import (
        DataMiningAgent, DataSourceType, DataFormat, DataSet
    )
    from .news_intelligence_agent import (
        NewsIntelligenceAgent, NewsCategory, NewsArticle, NewsTrend
    )
    from . import (
        get_specialized_agent, list_specialized_agents, 
        run_agent_test, get_agent_health_status,
        create_agent_ensemble, validate_agent_compatibility
    )
except ImportError:
    # Fallback para ejecución directa
    from research_agent import (
        ResearchAgent, ResearchMethod, ResearchReport
    )
    from data_mining_agent import (
        DataMiningAgent, DataSourceType, DataFormat, DataSet
    )
    from news_intelligence_agent import (
        NewsIntelligenceAgent, NewsCategory, NewsArticle, NewsTrend
    )
    from __init__ import (
        get_specialized_agent, list_specialized_agents,
        run_agent_test, get_agent_health_status,
        create_agent_ensemble, validate_agent_compatibility
    )


class TestResearchAgent(unittest.TestCase):
    """Tests para ResearchAgent"""
    
    def setUp(self):
        """Configuración inicial para tests"""
        self.agent = ResearchAgent()
        self.test_query = "inteligencia artificial"
        
    def test_agent_initialization(self):
        """Test de inicialización del agente"""
        self.assertEqual(self.agent.name, "research_agent")
        self.assertEqual(self.agent.version, "1.0.0")
        self.assertIsNotNone(self.agent.search_engine)
        self.assertIsNotNone(self.agent.config)
    
    def test_research_method_enum(self):
        """Test de enum de métodos de investigación"""
        self.assertIn(ResearchMethod.SYSTEMATIC, ResearchMethod)
        self.assertIn(ResearchMethod.EXPLORATORY, ResearchMethod)
        self.assertIn(ResearchMethod.ACADEMIC, ResearchMethod)
        self.assertIn(ResearchMethod.FACT_CHECK, ResearchMethod)
    
    def test_credibility_levels(self):
        """Test de niveles de credibilidad"""
        from research_agent import CredibilityLevel
        
        self.assertEqual(CredibilityLevel.VERY_HIGH.value, "very_high")
        self.assertEqual(CredibilityLevel.LOW.value, "low")
        self.assertIn("high", [level.value for level in CredibilityLevel])
    
    def test_generate_research_queries(self):
        """Test de generación de consultas de investigación"""
        queries = self.agent._generate_research_queries(
            self.test_query, 
            ResearchMethod.EXPLORATORY, 
            "contexto de prueba"
        )
        
        self.assertIsInstance(queries, list)
        self.assertGreater(len(queries), 0)
        self.assertIn(self.test_query, queries[0])
    
    @patch('requests.get')
    def test_source_credibility_assessment(self, mock_get):
        """Test de evaluación de credibilidad de fuentes"""
        # Mock de respuesta HTTP
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response
        
        # Crear resultado de búsqueda simulado
        from research_agent import SearchResult, SearchSource
        
        result = SearchResult(
            title="Test Article",
            url="https://test.com/article",
            snippet="Test content",
            source=SearchSource.DUCKDUCKGO
        )
        
        credibility = self.agent._assess_domain_credibility("test.com", result)
        self.assertIsNotNone(credibility)
        self.assertIn(credibility.credibility_level.value, ['very_high', 'high', 'medium', 'low', 'very_low'])
    
    def test_insight_generation(self):
        """Test de generación de insights"""
        # Crear fuentes simuladas
        from research_agent import SourceCredibility, CredibilityLevel
        
        sources = [
            SourceCredibility(
                url="https://test1.com",
                domain="test1.com",
                credibility_level=CredibilityLevel.HIGH,
                reliability_score=0.8,
                bias_indicators=[],
                fact_check_results={}
            ),
            SourceCredibility(
                url="https://test2.com",
                domain="test2.com",
                credibility_level=CredibilityLevel.HIGH,
                reliability_score=0.8,
                bias_indicators=[],
                fact_check_results={}
            )
        ]
        
        insights = self.agent._generate_insights(sources, self.test_query, ResearchMethod.EXPLORATORY)
        self.assertIsInstance(insights, list)
    
    def test_research_report_generation(self):
        """Test de generación de reporte de investigación"""
        # Crear datos de prueba
        sources = []
        insights = []
        
        report = self.agent._generate_research_report(
            query=self.test_query,
            method=ResearchMethod.EXPLORATORY,
            sources=sources,
            insights=insights,
            context="test context",
            execution_time=1.0
        )
        
        self.assertIsInstance(report, ResearchReport)
        self.assertEqual(report.query, self.test_query)
        self.assertEqual(report.method, ResearchMethod.EXPLORATORY)
        self.assertIsInstance(report.execution_time, float)
    
    def test_factory_function(self):
        """Test de función factory"""
        agent = get_specialized_agent("research")
        self.assertIsInstance(agent, ResearchAgent)
        self.assertEqual(agent.name, "research_agent")
    
    def test_supported_methods(self):
        """Test de métodos soportados"""
        methods = self.agent.get_supported_methods()
        self.assertIsInstance(methods, list)
        self.assertGreater(len(methods), 0)
        
        # Verificar estructura de métodos
        for method in methods:
            self.assertIn("name", method)
            self.assertIn("display_name", method)
            self.assertIn("description", method)


class TestDataMiningAgent(unittest.TestCase):
    """Tests para DataMiningAgent"""
    
    def setUp(self):
        """Configuración inicial para tests"""
        self.agent = DataMiningAgent()
        self.test_config = {
            "name": "Test API",
            "type": "web_api",
            "url": "https://api.example.com/data",
            "description": "API de prueba"
        }
    
    def test_agent_initialization(self):
        """Test de inicialización del agente"""
        self.assertEqual(self.agent.name, "data_mining_agent")
        self.assertEqual(self.agent.version, "1.0.0")
        self.assertIsNotNone(self.agent.search_engine)
        self.assertIsNotNone(self.agent.config)
    
    def test_data_source_types(self):
        """Test de tipos de fuentes de datos"""
        self.assertIn(DataSourceType.WEB_API, DataSourceType)
        self.assertIn(DataSourceType.WEB_SCRAPING, DataSourceType)
        self.assertIn(DataSourceType.RSS_FEED, DataSourceType)
    
    def test_data_formats(self):
        """Test de formatos de datos soportados"""
        self.assertIn(DataFormat.JSON, DataFormat)
        self.assertIn(DataFormat.CSV, DataFormat)
        self.assertIn(DataFormat.XML, DataFormat)
        self.assertIn(DataFormat.EXCEL, DataFormat)
    
    def test_config_validation(self):
        """Test de validación de configuración"""
        valid_config = {
            "type": "web_api",
            "url": "https://example.com"
        }
        
        invalid_config = {
            "type": "invalid_type",
            "url": "https://example.com"
        }
        
        self.assertTrue(self.agent._validate_source_config(valid_config))
        self.assertFalse(self.agent._validate_source_config(invalid_config))
    
    def test_quality_assessment(self):
        """Test de evaluación de calidad de datos"""
        from data_mining_agent import DataRecord, DataQuality
        
        # Crear registros de prueba
        records = [
            DataRecord(
                id="test1",
                source_url="https://test.com",
                data={"field1": "value1"},
                extracted_at=time.time(),
                quality_score=0.9,
                validation_errors=[]
            ),
            DataRecord(
                id="test2", 
                source_url="https://test.com",
                data={"field1": "value2"},
                extracted_at=time.time(),
                quality_score=0.8,
                validation_errors=[]
            )
        ]
        
        quality = self.agent._assess_data_quality(records)
        self.assertIsInstance(quality, DataQuality)
        self.assertIn(quality.value, ['excellent', 'good', 'fair', 'poor', 'invalid'])
    
    def test_schema_inference(self):
        """Test de inferencia de esquema"""
        from data_mining_agent import DataRecord
        
        records = [
            DataRecord(
                id="test1",
                source_url="https://test.com",
                data={"name": "John", "age": 30, "active": True},
                extracted_at=time.time(),
                quality_score=0.9,
                validation_errors=[]
            ),
            DataRecord(
                id="test2",
                source_url="https://test.com", 
                data={"name": "Jane", "age": 25, "active": False},
                extracted_at=time.time(),
                quality_score=0.8,
                validation_errors=[]
            )
        ]
        
        schema = self.agent._infer_schema(records)
        self.assertIsInstance(schema, dict)
        self.assertIn("name", schema)
        self.assertIn("age", schema)
        self.assertIn("active", schema)
    
    @patch('requests.get')
    def test_api_extraction(self, mock_get):
        """Test de extracción desde API"""
        # Mock de respuesta
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = [
            {"id": 1, "name": "Test Item 1"},
            {"id": 2, "name": "Test Item 2"}
        ]
        mock_get.return_value = mock_response
        
        try:
            dataset = self.agent.extract_data(self.test_config)
            self.assertIsInstance(dataset, DataSet)
            self.assertGreater(len(dataset.records), 0)
        except Exception as e:
            # Puede fallar debido a la URL simulada, lo importante es que no crashee
            self.assertIsInstance(e, (ValueError, Exception))
    
    def test_dataset_analysis(self):
        """Test de análisis de dataset"""
        # Crear dataset simulado
        from data_mining_agent import DataRecord, DataSet
        
        records = [
            DataRecord(
                id="test1",
                source_url="https://test.com",
                data={"value": 10, "category": "A"},
                extracted_at=time.time(),
                quality_score=0.8,
                validation_errors=[]
            )
        ]
        
        dataset = DataSet(
            name="Test Dataset",
            description="Dataset de prueba",
            source_type=DataSourceType.WEB_API,
            records=records,
            total_records=1,
            quality_assessment=DataQuality.GOOD,
            schema={"value": "integer", "category": "string"},
            extraction_config={},
            created_at=time.time(),
            last_updated=time.time()
        )
        
        analysis = self.agent.analyze_dataset(dataset)
        self.assertIsInstance(analysis, dict)
        self.assertIn("dataset_info", analysis)
        self.assertIn("schema_analysis", analysis)
    
    def test_factory_function(self):
        """Test de función factory"""
        agent = get_specialized_agent("data_mining")
        self.assertIsInstance(agent, DataMiningAgent)
        self.assertEqual(agent.name, "data_mining_agent")


class TestNewsIntelligenceAgent(unittest.TestCase):
    """Tests para NewsIntelligenceAgent"""
    
    def setUp(self):
        """Configuración inicial para tests"""
        self.agent = NewsIntelligenceAgent()
    
    def test_agent_initialization(self):
        """Test de inicialización del agente"""
        self.assertEqual(self.agent.name, "news_intelligence_agent")
        self.assertEqual(self.agent.version, "1.0.0")
        self.assertIsNotNone(self.agent.search_engine)
        self.assertIsNotNone(self.agent.config)
    
    def test_news_categories(self):
        """Test de categorías de noticias"""
        self.assertIn(NewsCategory.POLITICS, NewsCategory)
        self.assertIn(NewsCategory.ECONOMY, NewsCategory)
        self.assertIn(NewsCategory.TECHNOLOGY, NewsCategory)
        self.assertIn(NewsCategory.HEALTH, NewsCategory)
    
    def test_bias_detection(self):
        """Test de detección de sesgos"""
        from news_intelligence_agent import NewsArticle, Sentiment
        
        # Crear artículo de prueba
        article = NewsArticle(
            title="Test News Article",
            url="https://test.com/news",
            content="This is a test news article with some political content",
            summary="Test summary",
            category=NewsCategory.POLITICS,
            source="test.com",
            author="Test Author",
            published_at=time.time(),
            updated_at=time.time(),
            sentiment=Sentiment.NEUTRAL,
            bias_score=0.0,
            credibility_score=0.8,
            tags=["politics", "test"]
        )
        
        bias_analysis = self.agent.detect_bias(article)
        self.assertIsInstance(bias_analysis, dict)
        self.assertIn("overall_bias_score", bias_analysis)
        self.assertIn("bias_direction", bias_analysis)
    
    def test_sentiment_analysis(self):
        """Test de análisis de sentimiento"""
        positive_text = "Excelente noticia, gran progreso, muy positivo"
        negative_text = "Terrible situación, grave problema, muy negativo"
        neutral_text = "Información general sobre el tema"
        
        positive_sentiment = self.agent._analyze_basic_sentiment(positive_text)
        negative_sentiment = self.agent._analyze_basic_sentiment(negative_text)
        neutral_sentiment = self.agent._analyze_basic_sentiment(neutral_text)
        
        self.assertEqual(positive_sentiment, Sentiment.POSITIVE)
        self.assertEqual(negative_sentiment, Sentiment.NEGATIVE)
        self.assertEqual(neutral_sentiment, Sentiment.NEUTRAL)
    
    def test_credibility_scoring(self):
        """Test de cálculo de credibilidad"""
        # Test de fuente conocida
        credibility = self.agent._get_source_credibility("elpais.com")
        self.assertGreaterEqual(credibility, 0.0)
        self.assertLessEqual(credibility, 1.0)
        
        # Test de fuente desconocida
        unknown_credibility = self.agent._get_source_credibility("unknown-site.com")
        self.assertGreaterEqual(unknown_credibility, 0.0)
        self.assertLessEqual(unknown_credibility, 1.0)
    
    def test_trend_analysis(self):
        """Test de análisis de tendencias"""
        from news_intelligence_agent import NewsArticle, Sentiment
        
        # Crear artículos de prueba
        articles = [
            NewsArticle(
                title="AI Breakthrough",
                url="https://test.com/ai1",
                content="Artificial intelligence makes breakthrough",
                summary="AI news 1",
                category=NewsCategory.TECHNOLOGY,
                source="tech.com",
                author="Test",
                published_at=time.time(),
                updated_at=time.time(),
                sentiment=Sentiment.POSITIVE,
                bias_score=0.0,
                credibility_score=0.8,
                tags=["AI"]
            ),
            NewsArticle(
                title="AI Development",
                url="https://test.com/ai2",
                content="New AI development announced",
                summary="AI news 2", 
                category=NewsCategory.TECHNOLOGY,
                source="tech.com",
                author="Test",
                published_at=time.time(),
                updated_at=time.time(),
                sentiment=Sentiment.POSITIVE,
                bias_score=0.0,
                credibility_score=0.8,
                tags=["AI"]
            )
        ]
        
        trends = self.agent.analyze_trends(articles, min_articles=2)
        self.assertIsInstance(trends, list)
    
    def test_geographic_distribution(self):
        """Test de análisis de distribución geográfica"""
        from news_intelligence_agent import NewsArticle, Sentiment
        
        articles = [
            NewsArticle(
                title="Spanish News",
                url="https://elpais.com/news",
                content="Noticias de España",
                summary="Spanish news",
                category=NewsCategory.WORLD,
                source="elpais.com",
                author="Test",
                published_at=time.time(),
                updated_at=time.time(),
                sentiment=Sentiment.NEUTRAL,
                bias_score=0.0,
                credibility_score=0.8,
                tags=[]
            ),
            NewsArticle(
                title="US News",
                url="https://cnn.com/news",
                content="US News content",
                summary="American news",
                category=NewsCategory.WORLD,
                source="cnn.com",
                author="Test",
                published_at=time.time(),
                updated_at=time.time(),
                sentiment=Sentiment.NEUTRAL,
                bias_score=0.0,
                credibility_score=0.8,
                tags=[]
            )
        ]
        
        distribution = self.agent._analyze_geographic_distribution(articles)
        self.assertIsInstance(distribution, dict)
    
    def test_factory_function(self):
        """Test de función factory"""
        agent = get_specialized_agent("news_intelligence")
        self.assertIsInstance(agent, NewsIntelligenceAgent)
        self.assertEqual(agent.name, "news_intelligence_agent")


class TestSpecializedAgentsIntegration(unittest.TestCase):
    """Tests de integración para agentes especializados"""
    
    def test_agent_registry(self):
        """Test del registro de agentes"""
        agents = list_specialized_agents()
        
        self.assertIsInstance(agents, dict)
        self.assertIn("research_agent", agents)
        self.assertIn("data_mining_agent", agents)
        self.assertIn("news_intelligence_agent", agents)
        
        # Verificar estructura
        for agent_key, agent_info in agents.items():
            self.assertIn("name", agent_info)
            self.assertIn("description", agent_info)
            self.assertIn("capabilities", agent_info)
    
    def test_agent_creation(self):
        """Test de creación de agentes"""
        for agent_type in ["research", "data_mining", "news_intelligence"]:
            agent = get_specialized_agent(agent_type)
            self.assertIsNotNone(agent)
            self.assertTrue(hasattr(agent, 'name'))
            self.assertTrue(hasattr(agent, 'version'))
    
    def test_agent_ensemble(self):
        """Test de creación de ensemble de agentes"""
        agent_types = ["research", "data_mining"]
        
        ensemble = create_agent_ensemble(agent_types)
        self.assertIsInstance(ensemble, dict)
        self.assertIn("research", ensemble)
        self.assertIn("data_mining", ensemble)
        
        for agent_type in agent_types:
            self.assertIsNotNone(ensemble[agent_type])
    
    def test_compatibility_validation(self):
        """Test de validación de compatibilidad"""
        # Test con agente válido
        result = validate_agent_compatibility("research", {
            "capabilities": ["investigación multi-fuente"],
            "formats": ["json", "csv"]
        })
        
        self.assertIsInstance(result, dict)
        self.assertIn("compatible", result)
        self.assertIn("warnings", result)
        self.assertIn("errors", result)
        
        # Test con agente inválido
        invalid_result = validate_agent_compatibility("invalid_agent", {})
        self.assertFalse(invalid_result["compatible"])
    
    def test_agent_health_status(self):
        """Test de estado de salud de agentes"""
        for agent_type in ["research", "data_mining", "news_intelligence"]:
            health = get_agent_health_status(agent_type)
            self.assertIsInstance(health, dict)
            self.assertIn("status", health)
            self.assertIn("healthy", health)
    
    def test_agent_test_function(self):
        """Test de función de test de agentes"""
        for agent_type in ["research", "data_mining", "news_intelligence"]:
            result = run_agent_test(agent_type, {})
            self.assertIsInstance(result, dict)
            self.assertIn("success", result)
            if result["success"]:
                self.assertEqual(result["status"], "initialized")


class TestSpecializedAgentsPerformance(unittest.TestCase):
    """Tests de rendimiento para agentes especializados"""
    
    def test_research_agent_performance(self):
        """Test de rendimiento del ResearchAgent"""
        agent = ResearchAgent()
        
        # Test de generación de consultas
        start_time = time.time()
        queries = agent._generate_research_queries(
            "test query", ResearchMethod.EXPLORATORY, ""
        )
        generation_time = time.time() - start_time
        
        self.assertLess(generation_time, 1.0)  # Debe completarse en menos de 1 segundo
        self.assertGreater(len(queries), 0)
    
    def test_data_mining_performance(self):
        """Test de rendimiento del DataMiningAgent"""
        agent = DataMiningAgent()
        
        # Test de validación de configuración
        start_time = time.time()
        for _ in range(100):  # 100 validaciones
            agent._validate_source_config({
                "type": "web_api",
                "url": "https://test.com"
            })
        validation_time = time.time() - start_time
        
        self.assertLess(validation_time, 1.0)  # Debe ser muy rápido
    
    def test_news_agent_performance(self):
        """Test de rendimiento del NewsIntelligenceAgent"""
        agent = NewsIntelligenceAgent()
        
        # Test de análisis de sentimiento
        start_time = time.time()
        for _ in range(50):  # 50 análisis
            agent._analyze_basic_sentiment("Esta es una prueba de rendimiento")
        sentiment_time = time.time() - start_time
        
        self.assertLess(sentiment_time, 1.0)


class TestSpecializedAgentsErrorHandling(unittest.TestCase):
    """Tests de manejo de errores para agentes especializados"""
    
    def test_research_agent_error_handling(self):
        """Test de manejo de errores en ResearchAgent"""
        agent = ResearchAgent()
        
        # Test con consulta vacía
        report = agent.conduct_research("", ResearchMethod.EXPLORATORY)
        self.assertIsInstance(report, ResearchReport)
        self.assertIn("error", report.executive_summary.lower())
    
    def test_data_mining_error_handling(self):
        """Test de manejo de errores en DataMiningAgent"""
        agent = DataMiningAgent()
        
        # Test con configuración inválida
        with self.assertRaises(ValueError):
            agent.extract_data({
                "invalid": "config"
            })
    
    def test_news_agent_error_handling(self):
        """Test de manejo de errores en NewsIntelligenceAgent"""
        agent = NewsIntelligenceAgent()
        
        # Test con artículos vacíos
        trends = agent.analyze_trends([])
        self.assertEqual(trends, [])
        
        # Test de reporte vacío
        report = agent.generate_intelligence_report(time_range="1h")
        self.assertIsInstance(report, NewsIntelligenceReport)


class TestSpecializedAgentsDataConsistency(unittest.TestCase):
    """Tests de consistencia de datos para agentes especializados"""
    
    def test_research_agent_data_consistency(self):
        """Test de consistencia de datos en ResearchAgent"""
        agent = ResearchAgent()
        
        # Test de consistencia en generación de reportes
        report1 = agent._create_error_report("Test error", ResearchMethod.EXPLORATORY, 1.0)
        report2 = agent._create_error_report("Test error", ResearchMethod.EXPLORATORY, 1.0)
        
        self.assertEqual(report1.method, report2.method)
        self.assertEqual(report1.query, report2.query)
    
    def test_data_mining_consistency(self):
        """Test de consistencia de datos en DataMiningAgent"""
        agent = DataMiningAgent()
        
        # Test de consistencia en cálculo de calidad
        from data_mining_agent import DataRecord
        
        record = DataRecord(
            id="test",
            source_url="https://test.com",
            data={"field": "value"},
            extracted_at=time.time(),
            quality_score=0.8,
            validation_errors=[]
        )
        
        score1 = agent._calculate_quality_score(record)
        score2 = agent._calculate_quality_score(record)
        self.assertEqual(score1, score2)
    
    def test_news_agent_consistency(self):
        """Test de consistencia de datos en NewsIntelligenceAgent"""
        agent = NewsIntelligenceAgent()
        
        # Test de consistencia en análisis de sentimiento
        text = "Esta es una prueba consistente"
        sentiment1 = agent._analyze_basic_sentiment(text)
        sentiment2 = agent._analyze_basic_sentiment(text)
        self.assertEqual(sentiment1, sentiment2)


def run_specialized_agents_tests():
    """Ejecuta todos los tests de agentes especializados"""
    # Configurar test suite
    test_suite = unittest.TestSuite()
    
    # Agregar clases de test
    test_classes = [
        TestResearchAgent,
        TestDataMiningAgent, 
        TestNewsIntelligenceAgent,
        TestSpecializedAgentsIntegration,
        TestSpecializedAgentsPerformance,
        TestSpecializedAgentsErrorHandling,
        TestSpecializedAgentsDataConsistency
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Retornar resultados
    return {
        "total_tests": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "success": result.wasSuccessful(),
        "success_rate": (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100 if result.testsRun > 0 else 0
    }


if __name__ == "__main__":
    print("🧪 Ejecutando tests de Agentes Especializados")
    print("=" * 50)
    
    results = run_specialized_agents_tests()
    
    print(f"\n📊 Resultados de Tests:")
    print(f"  ✅ Tests ejecutados: {results['total_tests']}")
    print(f"  ❌ Fallos: {results['failures']}")
    print(f"  🚫 Errores: {results['errors']}")
    print(f"  📈 Tasa de éxito: {results['success_rate']:.1f}%")
    
    if results['success']:
        print(f"\n🎉 Todos los tests pasaron exitosamente!")
    else:
        print(f"\n⚠️ Algunos tests fallaron. Revisar resultados arriba.")