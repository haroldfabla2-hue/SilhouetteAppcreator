#!/usr/bin/env python3
"""
Ejemplo de uso del Search Engine Agent MCP
Demuestra todas las funcionalidades principales del agente de búsqueda avanzada

Ejecutar: python examples/search_engine_demo.py
"""

import json
import time
import logging
from typing import Dict, List, Any

# Importar el agente
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.agents.search_engine_agent import (
    SearchEngineAgent, 
    SearchSource, 
    SearchResult,
    SearchResponse
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_basic_web_search():
    """Demostración de búsqueda web básica"""
    print("🔍 DEMO 1: Búsqueda Web Multi-Fuente")
    print("=" * 50)
    
    agent = SearchEngineAgent()
    
    query = "inteligencia artificial machine learning"
    print(f"Consultando: {query}")
    
    start_time = time.time()
    response = agent.search_web(
        query=query,
        sources=[SearchSource.DUCKDUCKGO, SearchSource.WIKIPEDIA, SearchSource.GOOGLE],
        max_results=8,
        enable_synthesis=True
    )
    
    print(f"⏱️  Tiempo de ejecución: {response.execution_time:.2f}s")
    print(f"📊 Total resultados: {response.total_results}")
    print(f"🌐 Fuentes consultadas: {[s.value for s in response.sources_used]}")
    print(f"🔍 Deduplicado: {response.deduplicated}")
    print(f"🏆 Rankeado: {response.ranked}")
    
    if response.results:
        print("\n🎯 Top 3 resultados:")
        for i, result in enumerate(response.results[:3], 1):
            print(f"  {i}. {result.title}")
            print(f"     📍 URL: {result.url}")
            print(f"     🏷️  Fuente: {result.source.value}")
            print(f"     ⭐ Score: {result.score:.3f}")
            print(f"     🏢 Dominio: {result.domain}")
            print()
    
    if response.synthesis:
        print("📝 Síntesis:")
        print(response.synthesis)
    
    return response


def demo_academic_search():
    """Demostración de búsqueda académica"""
    print("\n🎓 DEMO 2: Búsqueda Académica Especializada")
    print("=" * 50)
    
    agent = SearchEngineAgent()
    
    query = "deep learning neural networks transformer architecture"
    print(f"Buscando papers académicos: {query}")
    
    response = agent.search_academic(
        query=query,
        sources=[SearchSource.ARXIV, SearchSource.ACADEMIC],
        max_results=6
    )
    
    print(f"📚 Resultados académicos: {response.total_results}")
    print(f"🌐 Fuentes académicas: {[s.value for s in response.sources_used]}")
    
    if response.results:
        print("\n📖 Papers encontrados:")
        for i, result in enumerate(response.results, 1):
            print(f"  {i}. {result.title}")
            print(f"     📄 Fuente: {result.source.value}")
            print(f"     🔗 URL: {result.url}")
            if result.metadata:
                print(f"     🏷️  Metadatos: {json.dumps(result.metadata, indent=6, ensure_ascii=False)}")
            print()
    
    return response


def demo_code_search():
    """Demostración de búsqueda de código"""
    print("\n💻 DEMO 3: Búsqueda Especializada en Código")
    print("=" * 50)
    
    agent = SearchEngineAgent()
    
    query = "python rest api fastify javascript"
    print(f"Buscando código relacionado con: {query}")
    
    response = agent.search_code(
        query=query,
        sources=[SearchSource.GITHUB],
        max_results=5
    )
    
    print(f"🧠 Repositorios encontrados: {response.total_results}")
    print(f"🔧 Fuente de código: {[s.value for s in response.sources_used]}")
    
    if response.results:
        print("\n💡 Repositorios de código:")
        for i, result in enumerate(response.results, 1):
            print(f"  {i}. {result.title}")
            print(f"     📋 Descripción: {result.snippet}")
            print(f"     🏷️  Fuente: {result.source.value}")
            print(f"     🔗 URL: {result.url}")
            print()
    
    return response


def demo_semantic_search():
    """Demostración de búsqueda semántica"""
    print("\n🧠 DEMO 4: Búsqueda Semántica con IA")
    print("=" * 50)
    
    agent = SearchEngineAgent()
    
    query = "análisis de sentimientos en redes sociales"
    print(f"Realizando búsqueda semántica: {query}")
    
    response = agent.semantic_search(
        query=query,
        max_results=8
    )
    
    print(f"🔍 Resultados semánticos: {response.total_results}")
    print(f"🤖 Tipo: Búsqueda semántica con embeddings")
    
    if response.results:
        print("\n🎯 Resultados semánticos:")
        for i, result in enumerate(response.results[:4], 1):
            print(f"  {i}. {result.title}")
            print(f"     💬 Resumen: {result.snippet}")
            print(f"     ⭐ Relevancia: {result.score:.3f}")
            print()
    
    return response


def demo_analytics():
    """Demostración de analytics avanzados"""
    print("\n📊 DEMO 5: Análisis Avanzado de Resultados")
    print("=" * 50)
    
    agent = SearchEngineAgent()
    
    query = "blockchain cryptocurrency bitcoin ethereum"
    response = agent.search_web(
        query=query,
        sources=[SearchSource.DUCKDUCKGO, SearchSource.WIKIPEDIA, SearchSource.BING],
        max_results=10
    )
    
    # Obtener analytics detallados
    analytics = agent.get_search_analytics(response)
    
    print("📈 Analytics de la búsqueda:")
    print(f"  📝 Consulta: {analytics['query']}")
    print(f"  📊 Total resultados: {analytics['total_results']}")
    print(f"  ⏱️  Tiempo ejecución: {analytics['execution_time']:.2f}s")
    print(f"  🔄 Eficiencia deduplicación: {analytics['deduplication_efficiency']:.2f}")
    
    if 'source_analysis' in analytics:
        print("\n🌐 Análisis por fuente:")
        for source, data in analytics['source_analysis'].items():
            print(f"  • {source}: {data['count']} resultados (score promedio: {data['avg_score']:.3f})")
    
    if 'domain_analysis' in analytics:
        print("\n🏢 Análisis por dominio:")
        for domain, data in sorted(analytics['domain_analysis'].items(), 
                                  key=lambda x: x[1]['count'], reverse=True)[:3]:
            print(f"  • {domain}: {data['count']} resultados")
    
    if 'language_analysis' in analytics:
        print("\n🗣️  Análisis por idioma:")
        for lang, data in analytics['language_analysis'].items():
            print(f"  • {lang}: {data['count']} resultados ({data['percentage']:.1f}%)")
    
    return analytics


def demo_batch_search():
    """Demostración de búsquedas en lote"""
    print("\n🚀 DEMO 6: Búsquedas en Lote (Batch)")
    print("=" * 50)
    
    agent = SearchEngineAgent()
    
    # Múltiples consultas
    queries = [
        "python web scraping beautifulsoup",
        "react javascript hooks tutorial", 
        "database design normalization sql"
    ]
    
    print(f"Ejecutando {len(queries)} búsquedas en lote...")
    
    start_time = time.time()
    results = []
    
    for i, query in enumerate(queries, 1):
        print(f"  Búsqueda {i}: {query}")
        response = agent.search_web(
            query=query,
            sources=[SearchSource.DUCKDUCKGO, SearchSource.WIKIPEDIA],
            max_results=5
        )
        results.append(response)
    
    total_time = time.time() - start_time
    
    print(f"\n✅ Búsquedas completadas en {total_time:.2f}s")
    
    for i, response in enumerate(results, 1):
        print(f"  Consulta {i}: {response.total_results} resultados")
    
    return results


def demo_performance_comparison():
    """Demostración de comparación de performance entre fuentes"""
    print("\n⚡ DEMO 7: Comparación de Performance por Fuente")
    print("=" * 50)
    
    agent = SearchEngineAgent()
    query = "artificial intelligence programming"
    
    sources_performance = {}
    
    for source in [SearchSource.DUCKDUCKGO, SearchSource.WIKIPEDIA, SearchSource.GOOGLE]:
        start_time = time.time()
        response = agent.search_web(
            query=query,
            sources=[source],
            max_results=5
        )
        
        execution_time = time.time() - start_time
        sources_performance[source.value] = {
            "execution_time": response.execution_time,
            "results_count": response.total_results,
            "success": len(response.results) > 0
        }
        
        print(f"  {source.value.upper()}: {response.execution_time:.2f}s - {response.total_results} resultados")
    
    print(f"\n🏆 Mejor performance: {min(sources_performance.keys(), key=lambda x: sources_performance[x]['execution_time'])}")
    
    return sources_performance


def demo_configuration_options():
    """Demostración de opciones de configuración"""
    print("\n⚙️ DEMO 8: Opciones de Configuración")
    print("=" * 50)
    
    agent = SearchEngineAgent()
    
    # Mostrar fuentes soportadas
    supported_sources = agent.get_supported_sources()
    
    print("🌐 Fuentes de búsqueda soportadas:")
    for source in supported_sources:
        print(f"  • {source['display_name']}: {source['description']}")
    
    # Configuración actual
    print(f"\n⚙️  Configuración actual del agente:")
    for key, value in agent.config.items():
        print(f"  • {key}: {value}")
    
    # Scoring weights
    print(f"\n🏆 Pesos de ranking:")
    for key, value in agent.scoring_weights.items():
        print(f"  • {key}: {value}")
    
    return supported_sources


def run_all_demos():
    """Ejecuta todas las demostraciones"""
    print("🚀 BÚSQUEDA ENGINE AGENT MCP - DEMOSTRACIÓN COMPLETA")
    print("=" * 60)
    print("Este demo muestra todas las capacidades del Search Engine Agent")
    print("con múltiples fuentes, ranking, deduplicación y síntesis.")
    print()
    
    try:
        # Ejecutar todas las demos
        demo_basic_web_search()
        demo_academic_search()
        demo_code_search()
        demo_semantic_search()
        demo_analytics()
        demo_batch_search()
        demo_performance_comparison()
        demo_configuration_options()
        
        print("\n" + "=" * 60)
        print("✅ TODAS LAS DEMOSTRACIONES COMPLETADAS EXITOSAMENTE")
        print("🎉 El Search Engine Agent MCP está funcionando correctamente!")
        print("\n📋 Funcionalidades demostradas:")
        print("  ✅ Búsqueda web multi-fuente")
        print("  ✅ Búsqueda académica especializada") 
        print("  ✅ Búsqueda de código en GitHub")
        print("  ✅ Búsqueda semántica con IA")
        print("  ✅ Analytics y métricas avanzadas")
        print("  ✅ Búsquedas en lote (batch)")
        print("  ✅ Comparación de performance")
        print("  ✅ Configuración y personalización")
        print("  ✅ Ranking inteligente")
        print("  ✅ Deduplicación de resultados")
        print("  ✅ Síntesis automática de contenido")
        
    except Exception as e:
        print(f"❌ Error durante las demostraciones: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Ejecutar demos
    run_all_demos()
    
    # Información adicional
    print(f"\n📚 Documentación disponible en:")
    print(f"  • Código fuente: src/agents/search_engine_agent.py")
    print(f"  • Configuración: search-engine-agent.json")
    print(f"  • Ejemplos: examples/search_engine_demo.py")
    
    print(f"\n🔧 Para integrar en tu aplicación:")
    print(f"  1. from src.agents.search_engine_agent import SearchEngineAgent")
    print(f"  2. agent = SearchEngineAgent()")
    print(f"  3. response = agent.search_web('tu consulta')")