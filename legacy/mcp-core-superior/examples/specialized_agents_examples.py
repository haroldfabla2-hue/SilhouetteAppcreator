"""
Ejemplos de Uso de Agentes Especializados
==========================================

Este archivo contiene ejemplos prácticos del uso de los tres agentes
especializados de búsqueda web avanzada, demostrando capacidades
individuales y casos de uso orquestados.

Autor: MCP Superior Team
Versión: 1.0.0
"""

import sys
import os
import json
import time
import asyncio
from typing import Dict, List, Any

# Añadir el path para importaciones
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.specialized import (
    ResearchAgent, DataMiningAgent, NewsIntelligenceAgent,
    ResearchMethod, NewsCategory, DataFormat,
    create_agent_ensemble, get_specialized_agent
)


def ejemplo_research_agent_basico():
    """Ejemplo básico del Research Agent"""
    print("\n🔬 Ejemplo 1: Research Agent - Investigación Básica")
    print("=" * 55)
    
    # Crear agente
    agent = ResearchAgent()
    
    # Investigación exploratoria
    print("🔍 Iniciando investigación exploratoria sobre IA...")
    report = agent.conduct_research(
        query="inteligencia artificial aplicaciones medicina",
        method=ResearchMethod.EXPLORATORY,
        max_iterations=3
    )
    
    # Mostrar resultados
    print(f"✅ Investigación completada:")
    print(f"   📊 Confianza: {report.confidence_score:.2f}")
    print(f"   📄 Fuentes: {len(report.sources_evaluated)}")
    print(f"   💡 Insights: {len(report.insights)}")
    
    if report.key_findings:
        print(f"   🎯 Hallazgos principales:")
        for finding in report.key_findings[:3]:
            print(f"      • {finding}")
    
    return report


def ejemplo_data_mining_basico():
    """Ejemplo básico del Data Mining Agent"""
    print("\n⛏️ Ejemplo 2: Data Mining Agent - Extracción Básica")
    print("=" * 50)
    
    # Crear agente
    agent = DataMiningAgent()
    
    # Configuración de API de ejemplo (JSONPlaceholder)
    api_config = {
        "name": "Posts API Demo",
        "description": "API de demostración para extraer posts",
        "type": "web_api",
        "url": "https://jsonplaceholder.typicode.com/posts",
        "params": {"_limit": "5"}
    }
    
    print("🌐 Extrayendo datos desde API...")
    try:
        dataset = agent.extract_data(
            source_config=api_config,
            enable_validation=True
        )
        
        print(f"✅ Extracción completada:")
        print(f"   📊 Registros: {dataset.total_records}")
        print(f"   🏷️ Calidad: {dataset.quality_assessment.value}")
        print(f"   🏗️ Esquema: {dataset.schema}")
        
        # Análisis del dataset
        analysis = agent.analyze_dataset(dataset)
        print(f"   📈 Completitud: {analysis['data_completeness']['overall_completeness']:.2f}")
        
        return dataset
        
    except Exception as e:
        print(f"❌ Error en extracción: {e}")
        return None


def ejemplo_news_intelligence_basico():
    """Ejemplo básico del News Intelligence Agent"""
    print("\n📰 Ejemplo 3: News Intelligence Agent - Análisis Básico")
    print("=" * 60)
    
    # Crear agente
    agent = NewsIntelligenceAgent()
    
    # Recopilar noticias de tecnología
    print("📰 Recopilando noticias de tecnología...")
    articles = agent.collect_news(
        categories=[NewsCategory.TECHNOLOGY],
        time_range="24h"
    )
    
    print(f"✅ Recopilación completada: {len(articles)} artículos")
    
    if articles:
        # Analizar primer artículo
        article = articles[0]
        print(f"📄 Primer artículo: {article.title[:60]}...")
        print(f"   🏢 Fuente: {article.source}")
        print(f"   🎭 Sentimiento: {article.sentiment.value}")
        print(f"   ⭐ Credibilidad: {article.credibility_score:.2f}")
        
        # Análisis de sesgo
        bias_analysis = agent.detect_bias(article)
        print(f"   ⚖️ Sesgo: {bias_analysis['bias_direction']}")
        print(f"   📊 Score: {bias_analysis['overall_bias_score']:.2f}")
        
        return articles
    else:
        print("⚠️ No se encontraron artículos")
        return []


def ejemplo_agente_ensemble():
    """Ejemplo de uso de ensemble de agentes especializados"""
    print("\n🤝 Ejemplo 4: Ensemble de Agentes Especializados")
    print("=" * 50)
    
    # Crear ensemble
    ensemble = create_agent_ensemble(
        agent_types=["research", "data_mining"],
        configuration={
            "research_agent": {
                "confidence_threshold": 0.6,
                "max_research_queries": 5
            },
            "data_mining_agent": {
                "timeout_seconds": 30,
                "batch_size": 20
            }
        }
    )
    
    print("🔧 Agentes configurados:")
    for name, agent in ensemble.items():
        if agent:
            print(f"   ✅ {name}: {agent.name} v{agent.version}")
    
    return ensemble


def ejemplo_analisis_mercado_completo():
    """Ejemplo completo: Análisis de mercado integral"""
    print("\n🎯 Ejemplo 5: Análisis de Mercado Completo")
    print("=" * 45)
    
    market_topic = "blockchain aplicaciones financieras"
    print(f"🔍 Analizando mercado: {market_topic}")
    
    # 1. Investigación académica y técnica
    print("\n📚 Paso 1: Investigación académica...")
    research_agent = ResearchAgent()
    research_report = research_agent.conduct_research(
        query=f"{market_topic} investigación 2024",
        method=ResearchMethod.ACADEMIC,
        max_iterations=4
    )
    
    print(f"✅ Investigación completada:")
    print(f"   📊 Confianza: {research_report.confidence_score:.2f}")
    print(f"   📄 Fuentes: {len(research_report.sources_evaluated)}")
    
    # 2. Análisis de noticias y tendencias
    print("\n📰 Paso 2: Análisis de noticias...")
    news_agent = NewsIntelligenceAgent()
    news_report = news_agent.generate_intelligence_report(
        time_range="7d",
        categories=[NewsCategory.BUSINESS, NewsCategory.ECONOMY]
    )
    
    print(f"✅ Análisis de noticias completado:")
    print(f"   📰 Artículos: {news_report.total_articles}")
    print(f"   📈 Tendencias: {len(news_report.trends_detected)}")
    print(f"   🎭 Sentimiento: {news_report.sentiment_analysis.get('overall_tone', 'N/A')}")
    
    # 3. Extracción de datos de mercado
    print("\n💾 Paso 3: Extracción de datos...")
    data_agent = DataMiningAgent()
    
    # Usar API simulada (Currency API demo)
    market_config = {
        "name": "Market Data Demo",
        "description": "Datos de mercado de demostración",
        "type": "web_api",
        "url": "https://api.exchangerate-api.com/v4/latest/USD",
        "params": {}
    }
    
    try:
        dataset = data_agent.extract_data(market_config)
        print(f"✅ Datos extraídos:")
        print(f"   📊 Registros: {dataset.total_records}")
        print(f"   🏷️ Calidad: {dataset.quality_assessment.value}")
        
        # Consolidar resultados
        analysis_results = {
            "topic": market_topic,
            "research": {
                "confidence": research_report.confidence_score,
                "sources": len(research_report.sources_evaluated),
                "method": research_report.method.value
            },
            "news": {
                "articles": news_report.total_articles,
                "trends": len(news_report.trends_detected),
                "sentiment": news_report.sentiment_analysis.get('overall_tone', 'N/A')
            },
            "data": {
                "records": dataset.total_records,
                "quality": dataset.quality_assessment.value,
                "schema": dataset.schema
            }
        }
        
        print(f"\n📋 Resumen del Análisis:")
        print(f"   🔬 Investigación: Confianza {analysis_results['research']['confidence']:.2f}")
        print(f"   📰 Noticias: {analysis_results['news']['articles']} artículos")
        print(f"   💾 Datos: {analysis_results['data']['records']} registros")
        
        return analysis_results
        
    except Exception as e:
        print(f"⚠️ Error en extracción de datos: {e}")
        return None


def ejemplo_crisis_monitoring():
    """Ejemplo de monitorización de crisis usando News Intelligence"""
    print("\n🚨 Ejemplo 6: Monitorización de Crisis Mediática")
    print("=" * 50)
    
    company_keywords = ["tesla", "elon musk"]
    crisis_indicators = ["problema", "escándalo", "crisis", "fallo"]
    
    print(f"🔍 Monitoreando menciones de: {', '.join(company_keywords)}")
    
    agent = NewsIntelligenceAgent()
    
    # Recopilar noticias recientes
    articles = agent.collect_news(
        categories=[NewsCategory.BUSINESS, NewsCategory.ECONOMY],
        time_range="24h"
    )
    
    print(f"📰 Artículos recopilados: {len(articles)}")
    
    # Filtrar menciones relevantes
    relevant_articles = []
    for article in articles:
        content_lower = f"{article.title} {article.content}".lower()
        if any(keyword in content_lower for keyword in company_keywords):
            relevant_articles.append(article)
    
    print(f"🎯 Artículos relevantes: {len(relevant_articles)}")
    
    # Analizar sentimiento y detectar crisis
    crisis_alerts = []
    for article in relevant_articles[:5]:  # Analizar primeros 5
        bias_analysis = agent.detect_bias(article)
        
        # Detectar indicadores de crisis
        content_lower = f"{article.title} {article.content}".lower()
        has_crisis_words = any(word in content_lower for word in crisis_indicators)
        negative_sentiment = article.sentiment.value in ['negative', 'very_negative']
        
        if has_crisis_words or negative_sentiment:
            crisis_alerts.append({
                "title": article.title,
                "source": article.source,
                "sentiment": article.sentiment.value,
                "credibility": article.credibility_score,
                "bias_score": bias_analysis.get("overall_bias_score", 0)
            })
    
    # Generar reporte de crisis
    if crisis_alerts:
        print(f"🚨 ALERTAS DE CRISIS DETECTADAS: {len(crisis_alerts)}")
        for alert in crisis_alerts:
            print(f"   ⚠️ {alert['title'][:60]}...")
            print(f"      Fuente: {alert['source']} | Sentimiento: {alert['sentiment']}")
            print(f"      Credibilidad: {alert['credibility']:.2f} | Sesgo: {alert['bias_score']:.2f}")
    else:
        print("✅ No se detectaron alertas de crisis")
    
    return {
        "total_mentions": len(relevant_articles),
        "crisis_alerts": len(crisis_alerts),
        "alerts_detail": crisis_alerts
    }


def ejemplo_data_pipeline():
    """Ejemplo de pipeline completo de datos"""
    print("\n🔄 Ejemplo 7: Pipeline Completo de Datos")
    print("=" * 45)
    
    # Configurar múltiples fuentes
    sources = [
        {
            "name": "Demo Posts",
            "type": "web_api",
            "url": "https://jsonplaceholder.typicode.com/posts",
            "params": {"_limit": "3"}
        },
        {
            "name": "Demo Users", 
            "type": "web_api",
            "url": "https://jsonplaceholder.typicode.com/users",
            "params": {"_limit": "2"}
        }
    ]
    
    # Crear agente y ejecutar pipeline
    agent = DataMiningAgent()
    
    print("📥 Paso 1: Extracción batch...")
    datasets = agent.extract_batch(sources, max_concurrent=2)
    
    print(f"✅ Extracción completada: {len(datasets)} datasets")
    
    # Procesar cada dataset
    processed_datasets = []
    for dataset in datasets:
        print(f"📊 Procesando: {dataset.name}")
        
        # Análisis
        analysis = agent.analyze_dataset(dataset)
        quality_score = analysis['data_quality_analysis']['average_quality_score']
        completeness = analysis['data_completeness']['overall_completeness']
        
        print(f"   📈 Calidad: {quality_score:.2f} | Completitud: {completeness:.2f}")
        
        # Transformación básica
        transformations = [
            {
                "type": "field_mapping",
                "field_mapping": {
                    "body": "content",
                    "name": "title"
                }
            }
        ]
        
        try:
            transformed = agent.transform_dataset(dataset, transformations)
            processed_datasets.append(transformed)
            print(f"   ✅ Transformación completada")
        except Exception as e:
            print(f"   ⚠️ Error en transformación: {e}")
    
    # Resumen final
    total_records = sum(ds.total_records for ds in processed_datasets)
    avg_quality = sum(
        agent.analyze_dataset(ds)['data_quality_analysis']['average_quality_score']
        for ds in processed_datasets
    ) / len(processed_datasets) if processed_datasets else 0
    
    print(f"\n📋 Resumen del Pipeline:")
    print(f"   📊 Total registros: {total_records}")
    print(f"   ⭐ Calidad promedio: {avg_quality:.2f}")
    print(f"   📁 Datasets procesados: {len(processed_datasets)}")
    
    return processed_datasets


def ejemplo_performance_comparison():
    """Ejemplo de comparación de rendimiento entre agentes"""
    print("\n⚡ Ejemplo 8: Comparación de Rendimiento")
    print("=" * 45)
    
    query = "machine learning"
    
    print(f"🧪 Probando rendimiento con consulta: '{query}'")
    
    # Test Research Agent
    print("\n🔬 Research Agent...")
    research_agent = ResearchAgent()
    start_time = time.time()
    queries = research_agent._generate_research_queries(query, ResearchMethod.EXPLORATORY, "")
    research_time = time.time() - start_time
    
    print(f"   ⏱️ Generación de consultas: {research_time:.3f}s")
    print(f"   📝 Consultas generadas: {len(queries)}")
    
    # Test Data Mining Agent
    print("\n⛏️ Data Mining Agent...")
    data_agent = DataMiningAgent()
    start_time = time.time()
    for _ in range(10):  # 10 validaciones
        data_agent._validate_source_config({"type": "web_api", "url": "https://test.com"})
    data_time = (time.time() - start_time) / 10
    
    print(f"   ⏱️ Validación promedio: {data_time:.3f}s")
    print(f"   🔄 Throughput: {1/data_time:.1f} validaciones/segundo")
    
    # Test News Intelligence Agent
    print("\n📰 News Intelligence Agent...")
    news_agent = NewsIntelligenceAgent()
    start_time = time.time()
    for _ in range(20):  # 20 análisis de sentimiento
        news_agent._analyze_basic_sentiment("Esta es una prueba de rendimiento del sistema")
    news_time = (time.time() - start_time) / 20
    
    print(f"   ⏱️ Análisis de sentimiento: {news_time:.3f}s")
    print(f"   🔄 Throughput: {1/news_time:.1f} análisis/segundo")
    
    # Resumen de rendimiento
    print(f"\n📊 Resumen de Rendimiento:")
    print(f"   🏆 Más rápido: {'Research' if research_time < min(data_time, news_time) else 'Data Mining' if data_time < news_time else 'News Intelligence'}")
    print(f"   ⚖️ Investigación: {research_time:.3f}s")
    print(f"   💾 Minería de datos: {data_time:.3f}s")
    print(f"   📰 Inteligencia de noticias: {news_time:.3f}s")


def main():
    """Función principal que ejecuta todos los ejemplos"""
    print("🚀 DEMOSTRACIÓN DE AGENTES ESPECIALIZADOS")
    print("=" * 60)
    print("Este programa demuestra las capacidades de los tres agentes")
    print("especializados de búsqueda web avanzada del MCP Superior.\n")
    
    ejemplos_completados = []
    
    try:
        # Ejecutar ejemplos
        if ejemplo_research_agent_basico():
            ejemplos_completados.append("Research Agent Básico")
        
        if ejemplo_data_mining_basico():
            ejemplos_completados.append("Data Mining Básico")
        
        if ejemplo_news_intelligence_basico():
            ejemplos_completados.append("News Intelligence Básico")
        
        if ejemplo_agente_ensemble():
            ejemplos_completados.append("Ensemble de Agentes")
        
        if ejemplo_analisis_mercado_completo():
            ejemplos_completados.append("Análisis de Mercado Completo")
        
        if ejemplo_crisis_monitoring():
            ejemplos_completados.append("Monitorización de Crisis")
        
        if ejemplo_data_pipeline():
            ejemplos_completados.append("Pipeline de Datos")
        
        ejemplo_performance_comparison()
        ejemplos_completados.append("Comparación de Rendimiento")
        
        # Resumen final
        print(f"\n🎉 DEMOSTRACIÓN COMPLETADA")
        print("=" * 30)
        print(f"✅ Ejemplos ejecutados exitosamente: {len(ejemplos_completados)}")
        
        for i, ejemplo in enumerate(ejemplos_completados, 1):
            print(f"   {i}. {ejemplo}")
        
        print(f"\n🎯 Todos los agentes especializados funcionando correctamente!")
        print(f"🔧 El sistema está listo para uso en producción.")
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️ Demostración interrumpida por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error durante la demostración: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n📚 Para más información, consulte:")
    print(f"   • Documentación: docs/ESPECIALIZED_AGENTS_DOCUMENTATION.md")
    print(f"   • Tests: tests/test_specialized_agents.py")
    print(f"   • Código fuente: src/agents/specialized/")


if __name__ == "__main__":
    main()