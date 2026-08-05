# Agentes Especializados de Búsqueda Web Avanzada

## 📋 Índice

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Research Agent](#research-agent)
4. [Data Mining Agent](#data-mining-agent)
5. [News Intelligence Agent](#news-intelligence-agent)
6. [Integración con el Orquestador](#integración-con-el-orquestador)
7. [Ejemplos de Uso](#ejemplos-de-uso)
8. [Configuración Avanzada](#configuración-avanzada)
9. [Tests y Validación](#tests-y-validación)
10. [Resolución de Problemas](#resolución-de-problemas)

## 📊 Resumen Ejecutivo

Los **Agentes Especializados de Búsqueda Web Avanzada** representan la evolución del MCP Superior hacia capacidades de investigación y análisis de datos más sofisticadas. Este módulo implementa tres agentes especializados que trabajan en conjunto para proporcionar capacidades de investigación, extracción de datos y análisis de noticias de nivel enterprise.

### 🎯 Objetivos Cumplidos

- ✅ **Research Agent**: Investigación web inteligente con análisis contextual
- ✅ **Data Mining Agent**: Extracción y análisis avanzado de datos
- ✅ **News Intelligence Agent**: Agregación y análisis de noticias con detección de sesgos
- ✅ **Integración completa** con el sistema de orquestación existente
- ✅ **Documentación exhaustiva** con ejemplos y casos de uso
- ✅ **Suite completa de tests** unitarios y de integración
- ✅ **Optimización de rendimiento** con caching y procesamiento concurrente

## 🏗️ Arquitectura del Sistema

```
mcp-core-superior/
├── src/agents/
│   └── specialized/
│       ├── __init__.py                 # Registro y factory de agentes
│       ├── research_agent.py           # Research Agent - Investigación inteligente
│       ├── data_mining_agent.py        # Data Mining Agent - Extracción de datos
│       └── news_intelligence_agent.py  # News Intelligence Agent - Análisis de noticias
└── tests/
    └── test_specialized_agents.py      # Suite completa de tests
```

### 🔗 Dependencias y Relaciones

```python
# Diagrama de dependencias
SearchEngineAgent (Base) ──┬── ResearchAgent
                           ├── DataMiningAgent
                           └── NewsIntelligenceAgent

BaseAgentWrapper (Interface) ──► Todos los agentes especializados
MultiagentOrchestrator (Orquestador) ──► Coordination
```

## 🔬 Research Agent

### Descripción General

El **Research Agent** es un agente especializado en investigación web inteligente que proporciona capacidades avanzadas de análisis contextual, síntesis de información y generación de insights. Utiliza múltiples fuentes de búsqueda y aplica algoritmos de análisis de credibilidad para generar reportes de investigación estructurados.

### Características Principales

#### 🎯 Capacidades Core

- **Investigación Multi-fuente**: Integra múltiples motores de búsqueda (Google, Bing, DuckDuckGo, Wikipedia, GitHub, ArXiv)
- **Análisis de Credibilidad**: Sistema de evaluación automática de fuentes con niveles de confianza
- **Síntesis Inteligente**: Generación automática de síntesis y resúmenes ejecutivos
- **Detección de Tendencias**: Identificación de patrones y tendencias emergentes
- **Verificación de Hechos**: Análisis automatizado para verificación de afirmaciones
- **Análisis de Sesgos**: Detección automática de sesgos políticos y mediáticos

#### 🛠️ Métodos de Investigación Soportados

1. **SYSTEMATIC** - Investigación estructurada y sistemática
2. **EXPLORATORY** - Exploración de perspectivas múltiples
3. **COMPARATIVE** - Análisis comparativo de alternativas
4. **TREND_ANALYSIS** - Identificación de tendencias
5. **FACT_CHECK** - Verificación de hechos
6. **ACADEMIC** - Investigación académica especializada
7. **NEWS_ANALYSIS** - Análisis de cobertura mediática

### 📖 Uso del Research Agent

#### Inicialización Básica

```python
from specialized import ResearchAgent, ResearchMethod

# Crear instancia del agente
agent = ResearchAgent()

# Configuración personalizada
agent.config.update({
    "max_research_queries": 15,
    "confidence_threshold": 0.8,
    "enable_bias_detection": True
})
```

#### Investigación Básica

```python
# Investigación exploratoria simple
report = agent.conduct_research(
    query="inteligencia artificial en medicina",
    method=ResearchMethod.EXPLORATORY,
    max_iterations=5,
    enable_deep_analysis=True
)

print(f"Reporte generado: {report.confidence_score:.2f} confianza")
print(f"Fuentes evaluadas: {len(report.sources_evaluated)}")
```

#### Investigación Sistemática

```python
# Investigación sistemática con contexto específico
report = agent.conduct_research(
    query="blockchain aplicaciones financieras",
    method=ResearchMethod.SYSTEMATIC,
    context="sector bancario español",
    max_iterations=8,
    enable_deep_analysis=True
)

# Acceder a resultados
print(f"Resumen: {report.executive_summary}")
print(f"Hallazgos clave: {report.key_findings}")
print(f"Insights: {insight.description for insight in report.insights}")
```

#### Verificación de Hechos

```python
# Verificar una afirmación específica
fact_check = agent.fact_check_statement(
    "La inteligencia artificial puede diagnosticar enfermedades con 95% de precisión"
)

print(f"Confianza: {fact_check['confidence_score']:.2f}")
print(f"Fuentes de apoyo: {len(fact_check['supporting_sources'])}")
```

#### Análisis de Tendencias

```python
# Analizar tendencias en un tema
trend_analysis = agent.analyze_trends(
    topic="metaverso",
    time_range="90d",
    max_sources=25
)

for trend in trend_analysis['trend_analysis']['key_topics']:
    print(f"Tema: {trend[0]}, Frecuencia: {trend[1]}")
```

### 📊 Estructura de Datos

#### ResearchReport

```python
@dataclass
class ResearchReport:
    query: str                    # Consulta original
    method: ResearchMethod        # Método usado
    executive_summary: str        # Resumen ejecutivo
    key_findings: List[str]       # Hallazgos principales
    insights: List[ResearchInsight] # Insights generados
    sources_evaluated: List[SourceCredibility] # Fuentes analizadas
    methodology: str              # Metodología aplicada
    limitations: List[str]        # Limitaciones identificadas
    recommendations: List[str]    # Recomendaciones
    confidence_score: float       # Score de confianza (0.0-1.0)
    timestamp: float             # Timestamp de generación
    execution_time: float        # Tiempo de ejecución
```

#### SourceCredibility

```python
@dataclass
class SourceCredibility:
    url: str                    # URL de la fuente
    domain: str                 # Dominio
    credibility_level: CredibilityLevel  # Nivel de credibilidad
    reliability_score: float    # Score de confiabilidad (0.0-1.0)
    bias_indicators: List[str]  # Indicadores de sesgo detectados
    fact_check_results: Dict[str, Any]  # Resultados de verificación
```

### ⚙️ Configuración Avanzada

#### Personalización de Credibilidad

```python
# Añadir fuente personalizada a la base de datos de credibilidad
agent.domain_credibility_db.update({
    "mi-sitio.com": {
        "level": "high",
        "reliability": 0.85
    },
    "sitio-desconocido.com": {
        "level": "medium", 
        "reliability": 0.65
    }
})
```

#### Configuración de Scoring

```python
# Personalizar pesos de scoring
agent.scoring_weights.update({
    "relevance": 0.5,    # Mayor peso a relevancia
    "authority": 0.2,    # Menor peso a autoridad
    "freshness": 0.2,    # Peso moderado a frescura
    "language_match": 0.1  # Peso mínimo a coincidencia de idioma
})
```

### 🎯 Casos de Uso Típicos

1. **Investigación de Mercado**: Análisis de tendencias en sectores específicos
2. **Due Diligence**: Verificación de información en procesos de inversión
3. **Análisis Competitivo**: Investigación de competidores y alternativas
4. **Verificación de Noticias**: Fact-checking en tiempo real
5. **Investigación Académica**: Búsqueda y síntesis de literatura científica

## ⛏️ Data Mining Agent

### Descripción General

El **Data Mining Agent** proporciona capacidades sofisticadas de extracción, transformación y análisis de datos desde múltiples fuentes web. Incluye procesamiento inteligente, validación automática, y exportación en múltiples formatos para análisis posterior.

### Características Principantes

#### 🎯 Capacidades Core

- **Extracción Multi-fuente**: APIs, web scraping, RSS, archivos
- **Transformación Inteligente**: Limpieza y normalización automática
- **Validación de Calidad**: Evaluación automática de integridad de datos
- **Análisis Estadístico**: Detección de patrones y análisis descriptivo
- **Exportación Múltiple**: JSON, CSV, XML, Excel, Database
- **Programación**: Extracciones periódicas y trabajos programados

#### 📊 Tipos de Fuentes Soportadas

1. **WEB_API** - APIs REST/JSON
2. **WEB_SCRAPING** - Scraping de sitios web
3. **RSS_FEED** - Feeds RSS/Atom
4. **FILE_DOWNLOAD** - Descarga y parsing de archivos
5. **DATABASE** - Conexión directa a bases de datos
6. **STREAMING** - Datos en tiempo real

### 📖 Uso del Data Mining Agent

#### Extracción Básica desde API

```python
from specialized import DataMiningAgent, DataFormat

agent = DataMiningAgent()

# Configuración de API
api_config = {
    "name": "GitHub API",
    "description": "API de repositorios de GitHub",
    "type": "web_api",
    "url": "https://api.github.com/search/repositories",
    "params": {"q": "machine learning", "sort": "stars", "order": "desc"},
    "headers": {"Accept": "application/vnd.github.v3+json"}
}

# Extraer datos
dataset = agent.extract_data(
    source_config=api_config,
    output_format=DataFormat.JSON,
    enable_validation=True
)

print(f"Registros extraídos: {dataset.total_records}")
print(f"Calidad: {dataset.quality_assessment.value}")
print(f"Esquema: {dataset.schema}")
```

#### Web Scraping Estructurado

```python
# Configuración de scraping
web_config = {
    "name": "News Website",
    "description": "Scraping de noticias",
    "type": "web_scraping",
    "url": "https://example-news.com",
    "selectors": {
        "article_title": {
            "css_selector": "article h2.title",
            "attributes": {}
        },
        "article_content": {
            "css_selector": "article .content",
            "attributes": {}
        },
        "publish_date": {
            "css_selector": "article .date",
            "attributes": {}
        }
    }
}

dataset = agent.extract_data(web_config, enable_validation=True)
```

#### Extracción Batch

```python
# Múltiples fuentes en paralelo
source_configs = [
    api_config,
    {
        "name": "Weather API",
        "type": "web_api", 
        "url": "https://api.weather.com/v1/current",
        "params": {"location": "Madrid"}
    },
    {
        "name": "RSS Feed",
        "type": "rss_feed",
        "url": "https://feeds.feedburner.com/oreilly/radar"
    }
]

# Extracción concurrente
datasets = agent.extract_batch(
    source_configs=source_configs,
    output_format=DataFormat.CSV,
    max_concurrent=3
)

for dataset in datasets:
    print(f"✅ {dataset.name}: {dataset.total_records} registros")
```

#### Análisis de Dataset

```python
# Análisis completo del dataset
analysis = agent.analyze_dataset(dataset)

print(f"📊 Análisis completo:")
print(f"  - Completitud general: {analysis['data_completeness']['overall_completeness']:.2f}")
print(f"  - Score promedio: {analysis['data_quality_analysis']['average_quality_score']:.2f}")
print(f"  - Patrones detectados: {len(analysis['pattern_detection'])}")

# Recomendaciones
for recommendation in analysis['recommendations']:
    print(f"💡 {recommendation}")
```

#### Transformación de Datos

```python
# Definir transformaciones
transformations = [
    {
        "type": "field_mapping",
        "field_mapping": {
            "article_title": "title",
            "article_content": "content"
        }
    },
    {
        "type": "data_type_conversion", 
        "conversions": {
            "publish_date": "date",
            "views": "integer"
        }
    },
    {
        "type": "data_cleaning",
        "cleaning_rules": {
            "title": {
                "remove_whitespace": True,
                "lowercase": False
            }
        }
    }
]

# Aplicar transformaciones
transformed_dataset = agent.transform_dataset(
    dataset=dataset,
    transformations=transformations,
    output_format=DataFormat.JSON
)
```

#### Exportación a Múltiples Formatos

```python
import tempfile

# JSON con metadatos completos
with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
    json_path = agent.export_dataset(dataset, f.name, DataFormat.JSON, indent=2)
    print(f"✅ JSON exportado: {json_path}")

# CSV para análisis
with tempfile.NamedTemporaryFile(mode='w', suffix='.csv') as f:
    csv_path = agent.export_dataset(dataset, f.name, DataFormat.CSV)
    print(f"✅ CSV exportado: {csv_path}")

# Excel con múltiples hojas
with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx') as f:
    excel_path = agent.export_dataset(dataset, f.name, DataFormat.EXCEL)
    print(f"✅ Excel exportado: {excel_path}")

# Base de datos SQLite
with tempfile.NamedTemporaryFile(mode='w', suffix='.db') as f:
    db_path = agent.export_dataset(dataset, f.name, DataFormat.DATABASE)
    print(f"✅ Base de datos exportada: {db_path}")
```

#### Programación de Extracciones

```python
# Programar extracción diaria
job_id = agent.schedule_extraction(
    source_config=api_config,
    schedule_config={
        "frequency": "daily",
        "time": "09:00",
        "timezone": "Europe/Madrid"
    }
)

print(f"Trabajo programado: {job_id}")

# El agente ejecutará automáticamente las extracciones según el cronograma
```

### 📊 Estructura de Datos

#### DataSet

```python
@dataclass
class DataSet:
    name: str                    # Nombre del dataset
    description: str             # Descripción
    source_type: DataSourceType  # Tipo de fuente
    records: List[DataRecord]    # Registros de datos
    total_records: int           # Total de registros
    quality_assessment: DataQuality  # Evaluación de calidad
    schema: Dict[str, str]       # Esquema inferido
    extraction_config: Dict[str, Any]  # Configuración original
    created_at: float           # Timestamp de creación
    last_updated: float         # Última actualización
```

#### DataRecord

```python
@dataclass
class DataRecord:
    id: str                    # ID único del registro
    source_url: str            # URL de origen
    data: Dict[str, Any]       # Datos extraídos
    extracted_at: float        # Timestamp de extracción
    quality_score: float       # Score de calidad (0.0-1.0)
    validation_errors: List[str]  # Errores de validación
    metadata: Dict[str, Any]   # Metadatos adicionales
```

### ⚙️ Configuración Avanzada

#### Configuración de Calidad

```python
# Personalizar umbrales de calidad
agent.config.update({
    "quality_threshold": 0.8,          # Umbral más estricto
    "enable_data_validation": True,    # Activar validación
    "enable_deduplication": True,      # Activar deduplicación
    "batch_size": 50,                  # Tamaño de lote reducido
    "timeout_seconds": 45              # Timeout más largo
})
```

#### Validaciones Personalizadas

```python
# Configurar validaciones específicas
validation_rules = {
    "email": {
        "required": True,
        "format": "email",
        "domain_allowlist": ["company.com", "partner.com"]
    },
    "age": {
        "type": "integer",
        "min_value": 0,
        "max_value": 120
    },
    "date": {
        "type": "date",
        "format": "YYYY-MM-DD",
        "range": {
            "start": "2020-01-01",
            "end": "2030-12-31"
        }
    }
}
```

### 🎯 Casos de Uso Típicos

1. **ETL de Fuentes Múltiples**: Consolidación de datos de APIs diversas
2. **Monitorización de Precios**: Extracción automática de precios de e-commerce
3. **Agregación de Feeds**: Consolidación de noticias RSS múltiples
4. **Análisis de Competidores**: Extracción de datos de sitios web competidores
5. **Data Warehouse**: Preparación de datos para análisis posterior

## 📰 News Intelligence Agent

### Descripción General

El **News Intelligence Agent** proporciona capacidades avanzadas de agregación, análisis y síntesis de noticias desde múltiples fuentes mediáticas. Incluye detección de sesgos, análisis de sentimiento, seguimiento de tendencias y verificación de credibilidad para proporcionar una perspectiva equilibrada del panorama informativo.

### Características Principales

#### 🎯 Capacidades Core

- **Agregación Multi-fuente**: Recopilación desde medios mainstream y alternativos
- **Análisis de Sesgos**: Detección automática de sesgos políticos y mediáticos
- **Análisis de Sentimiento**: Evaluación de tono y polaridad emocional
- **Seguimiento de Tendencias**: Identificación de temas emergentes
- **Verificación de Credibilidad**: Evaluación automática de fiabilidad de fuentes
- **Reportes Ejecutivos**: Generación automática de resúmenes de inteligencia

#### 📰 Categorías de Noticias Soportadas

1. **POLITICS** - Noticias políticas y gubernamentales
2. **ECONOMY** - Noticias económicas y financieras
3. **TECHNOLOGY** - Avances tecnológicos e innovación
4. **HEALTH** - Noticias de salud y medicina
5. **SCIENCE** - Descubrimientos científicos e investigación
6. **SPORTS** - Noticias deportivas y competiciones
7. **ENTERTAINMENT** - Entretenimiento, cine y cultura
8. **WORLD** - Noticias internacionales
9. **LOCAL** - Noticias locales y regionales
10. **BUSINESS** - Noticias empresariales y de negocios

### 📖 Uso del News Intelligence Agent

#### Recopilación Básica de Noticias

```python
from specialized import NewsIntelligenceAgent, NewsCategory

agent = NewsIntelligenceAgent()

# Recopilar noticias de categorías específicas
articles = agent.collect_news(
    categories=[NewsCategory.TECHNOLOGY, NewsCategory.ECONOMY],
    time_range="24h",
    sources_filter=["elpais.com", "elmundo.es", "bbc.com"]
)

print(f"Artículos recopilados: {len(articles)}")
for article in articles[:3]:
    print(f"📰 {article.title}")
    print(f"   Fuente: {article.source} | Credibilidad: {article.credibility_score:.2f}")
    print(f"   Sentimiento: {article.sentiment.value}")
```

#### Análisis de Tendencias en Noticias

```python
# Analizar tendencias emergentes
trends = agent.analyze_trends(
    articles=articles,
    time_window=24,  # horas
    min_articles=3
)

print(f"📈 Tendencias detectadas: {len(trends)}")
for trend in trends[:5]:
    print(f"🔍 {trend.topic}: {trend.article_count} artículos")
    print(f"   Crecimiento: {trend.growth_rate:.2f}")
    print(f"   Sentimiento: {trend.sentiment_trend.value}")
    print(f"   Confianza: {trend.confidence_score:.2f}")
```

#### Detección de Sesgos Mediáticos

```python
# Analizar sesgo de un artículo específico
if articles:
    bias_analysis = agent.detect_bias(articles[0])
    
    print(f"⚖️ Análisis de sesgo:")
    print(f"   Artículo: {bias_analysis['article_title'][:60]}...")
    print(f"   Fuente: {bias_analysis['source']}")
    print(f"   Score de sesgo: {bias_analysis['overall_bias_score']:.2f}")
    print(f"   Dirección: {bias_analysis['bias_direction']}")
    print(f"   Confianza: {bias_analysis['confidence_score']:.2f}")
    
    if bias_analysis['indicators']:
        print(f"   Indicadores: {', '.join(bias_analysis['indicators'])}")
```

#### Reporte Completo de Inteligencia

```python
# Generar reporte ejecutivo completo
report = agent.generate_intelligence_report(
    time_range="24h",
    categories=[NewsCategory.TECHNOLOGY, NewsCategory.POLITICS],
    include_trends=True,
    include_bias_analysis=True
)

print(f"🧠 Reporte de Inteligencia Generado:")
print(f"   ID: {report.report_id}")
print(f"   Artículos analizados: {report.total_articles}")
print(f"   Historias identificadas: {report.total_stories}")
print(f"   Tendencias detectadas: {len(report.trends_detected)}")

# Métricas de sentimiento
if report.sentiment_analysis:
    print(f"📊 Sentimiento dominante: {report.sentiment_analysis.get('dominant_sentiment')}")
    print(f"   Tono general: {report.sentiment_analysis.get('overall_tone')}")

# Métricas de credibilidad
if report.credibility_analysis:
    avg_cred = report.credibility_analysis.get('average_credibility', 0)
    print(f"✅ Credibilidad promedio: {avg_cred:.2f}")

# Recomendaciones
print(f"💡 Recomendaciones:")
for recommendation in report.recommendations[:3]:
    print(f"   - {recommendation}")
```

#### Seguimiento de Historias Específicas

```python
# Iniciar seguimiento de una historia
tracking_id = agent.track_story(
    story_keywords="inteligencia artificial regulación",
    duration=7,  # días
    update_interval=2  # horas
)

print(f"📍 Seguimiento iniciado: {tracking_id}")
print(f"   Palabras clave: inteligencia artificial regulación")
print(f"   Duración: 7 días")
print(f"   Actualizaciones: cada 2 horas")

# El agente monitoreará automáticamente esta historia
```

#### Métricas de Credibilidad

```python
# Análisis detallado de credibilidad
credibility_metrics = agent.get_credibility_metrics(articles)

print(f"📈 Métricas de Credibilidad:")
print(f"   Credibilidad general: {credibility_metrics['overall_average_credibility']:.2f}")
print(f"   Total de artículos: {credibility_metrics['total_articles']}")

print(f"   Distribución por nivel:")
for level, count in credibility_metrics['credibility_distribution'].items():
    percentage = (count / credibility_metrics['total_articles']) * 100
    print(f"     {level.title()}: {count} ({percentage:.1f}%)")

print(f"   Fuentes analizadas: {len(credibility_metrics['source_metrics'])}")
```

### 📊 Estructura de Datos

#### NewsIntelligenceReport

```python
@dataclass
class NewsIntelligenceReport:
    report_id: str                    # ID único del reporte
    generated_at: float              # Timestamp de generación
    time_range: Tuple[float, float]   # Rango temporal
    categories_analyzed: List[NewsCategory]  # Categorías analizadas
    total_articles: int              # Total de artículos
    total_stories: int               # Total de historias
    trends_detected: List[NewsTrend]  # Tendencias detectadas
    sentiment_analysis: Dict[str, Any]  # Análisis de sentimiento
    bias_analysis: Dict[str, Any]    # Análisis de sesgos
    credibility_analysis: Dict[str, Any]  # Análisis de credibilidad
    top_stories: List[NewsStory]     # Historias principales
    breaking_news: List[NewsArticle] # Noticias de última hora
    recommendations: List[str]       # Recomendaciones
    metadata: Dict[str, Any]         # Metadatos adicionales
```

#### NewsArticle

```python
@dataclass
class NewsArticle:
    title: str                      # Título del artículo
    url: str                       # URL del artículo
    content: str                   # Contenido completo
    summary: str                   # Resumen automático
    category: NewsCategory         # Categoría asignada
    source: str                    # Fuente de noticias
    author: str                    # Autor
    published_at: float            # Timestamp de publicación
    updated_at: float              # Timestamp de actualización
    sentiment: Sentiment           # Análisis de sentimiento
    bias_score: float              # Score de sesgo (-1.0 a +1.0)
    credibility_score: float       # Score de credibilidad (0.0-1.0)
    tags: List[str]                # Etiquetas extraídas
    language: str                  # Idioma detectado
    metadata: Dict[str, Any]       # Metadatos adicionales
```

### ⚙️ Configuración Avanzada

#### Personalización de Fuentes

```python
# Añadir fuente personalizada con configuración de credibilidad
agent.news_sources_db.update({
    "mi-medio.com": {
        "credibility": 0.75,
        "bias_score": -0.2,
        "bias_direction": "left_center",
        "reliability": "high"
    }
})
```

#### Configuración de Análisis

```python
# Personalizar parámetros de análisis
agent.config.update({
    "max_articles_per_source": 100,      # Más artículos por fuente
    "credibility_threshold": 0.7,        # Umbral más estricto
    "bias_detection_enabled": True,      # Activar detección de sesgos
    "trend_analysis_enabled": True,      # Activar análisis de tendencias
    "fake_news_detection": True,         # Activar detección de fake news
    "language": "es",                    # Idioma principal
    "geographic_scope": "spain"          # Alcance geográfico
})
```

#### Filtrado Avanzado

```python
# Configurar filtros de contenido
content_filters = {
    "exclude_domains": ["fake-news.com", "spam-site.net"],
    "exclude_keywords": ["clickbait", "publicidad", "spam"],
    "min_credibility_score": 0.6,
    "max_bias_score": 0.8,  # Excluir sesgos extremos
    "languages": ["es", "en"],
    "date_range": {
        "start": "2024-01-01",
        "end": "2024-12-31"
    }
}
```

### 🎯 Casos de Uso Típicos

1. **Monitorización de Marca**: Seguimiento de menciones en medios
2. **Inteligencia Competitiva**: Análisis de cobertura mediática de competidores
3. **Gestión de Crisis**: Detección temprana de crisis reputacionales
4. **Análisis de Mercado**: Seguimiento de tendencias sectoriales
5. **Fact-Checking**: Verificación de información en tiempo real
6. **Análisis Político**: Monitoreo de cobertura política
7. **Due Diligence**: Investigación de fuentes para decisiones de inversión

## 🔗 Integración con el Orquestador

### Registro en el Orquestador

Los agentes especializados se registran automáticamente con el sistema de orquestación:

```python
from specialized import SPECIALIZED_AGENTS, get_specialized_agent

# Registro automático con el orquestador
for agent_name, agent_info in SPECIALIZED_AGENTS.items():
    orchestrator.register_agent(
        name=agent_name,
        agent_class=agent_info["class"],
        factory=agent_info["factory"],
        capabilities=agent_info["capabilities"]
    )
```

### Orquestación de Tareas Complejas

```python
from specialized import create_agent_ensemble

# Crear ensemble de agentes para tarea compleja
ensemble = create_agent_ensemble(
    agent_types=["research", "data_mining", "news_intelligence"],
    configuration={
        "research_agent": {
            "confidence_threshold": 0.8,
            "enable_bias_detection": True
        },
        "data_mining_agent": {
            "quality_threshold": 0.7,
            "enable_validation": True
        }
    }
)

# Ejecución orquestada
def research_and_analyze_topic(topic):
    """Función que demuestra orquestación de agentes especializados"""
    
    # 1. Research Agent: Investigar el tema
    research_report = ensemble["research"].conduct_research(
        query=topic,
        method=ResearchMethod.EXPLORATORY
    )
    
    # 2. News Intelligence Agent: Analizar cobertura mediática
    news_report = ensemble["news_intelligence"].generate_intelligence_report(
        time_range="7d",
        categories=[NewsCategory.TECHNOLOGY]
    )
    
    # 3. Data Mining Agent: Extraer datos adicionales
    api_config = {
        "name": f"{topic} API",
        "type": "web_api",
        "url": f"https://api.example.com/{topic.replace(' ', '_')}"
    }
    dataset = ensemble["data_mining"].extract_data(api_config)
    
    return {
        "research": research_report,
        "news": news_report,
        "data": dataset
    }
```

### Ejecución Paralela

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def parallel_analysis(topics):
    """Análisis paralelo de múltiples temas"""
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Ejecutar análisis en paralelo
        futures = []
        for topic in topics:
            future = executor.submit(research_and_analyze_topic, topic)
            futures.append(future)
        
        # Recopilar resultados
        results = []
        for future in futures:
            result = future.result()
            results.append(result)
    
    return results

# Uso
topics = ["inteligencia artificial", "blockchain", "metaverso"]
results = asyncio.run(parallel_analysis(topics))
```

## 📚 Ejemplos de Uso

### Ejemplo 1: Investigación Completa de Mercado

```python
#!/usr/bin/env python3
"""
Ejemplo completo: Análisis de mercado para tecnología emergente
Utiliza los tres agentes especializados en conjunto
"""

from specialized import (
    ResearchAgent, DataMiningAgent, NewsIntelligenceAgent,
    ResearchMethod, NewsCategory, DataFormat
)

def comprehensive_market_analysis(technology):
    """Análisis completo de mercado usando múltiples agentes"""
    
    print(f"🔍 Iniciando análisis completo de mercado: {technology}")
    
    # 1. Research Agent: Investigación académica y técnica
    research_agent = ResearchAgent()
    research_report = research_agent.conduct_research(
        query=f"{technology} mercado aplicaciones",
        method=ResearchMethod.SYSTEMATIC,
        max_iterations=6
    )
    
    # 2. News Intelligence Agent: Análisis de cobertura mediática
    news_agent = NewsIntelligenceAgent()
    news_report = news_agent.generate_intelligence_report(
        time_range="30d",
        categories=[NewsCategory.TECHNOLOGY, NewsCategory.BUSINESS]
    )
    
    # 3. Data Mining Agent: Extracción de datos de mercado
    data_agent = DataMiningAgent()
    market_data = data_agent.extract_data({
        "name": "Market Data API",
        "type": "web_api",
        "url": "https://api.marketdata.com/v1/stocks/screener",
        "params": {"sector": technology}
    })
    
    # 4. Consolidación de resultados
    analysis_results = {
        "technology": technology,
        "research_confidence": research_report.confidence_score,
        "news_sentiment": news_report.sentiment_analysis.get("overall_tone"),
        "data_quality": market_data.quality_assessment.value,
        "key_findings": research_report.key_findings,
        "trends": news_report.trends_detected,
        "data_points": market_data.total_records
    }
    
    return analysis_results

# Ejecutar análisis
if __name__ == "__main__":
    technology = "inteligencia artificial"
    results = comprehensive_market_analysis(technology)
    
    print(f"\n📊 Resultados del Análisis:")
    print(f"  Tecnología: {results['technology']}")
    print(f"  Confianza investigación: {results['research_confidence']:.2f}")
    print(f"  Sentimiento mediático: {results['news_sentiment']}")
    print(f"  Calidad de datos: {results['data_quality']}")
    print(f"  Puntos de datos: {results['data_points']}")
```

### Ejemplo 2: Monitorización de Crisis Mediática

```python
#!/usr/bin/env python3
"""
Ejemplo: Detección y análisis de crisis reputacional
"""

from specialized import NewsIntelligenceAgent, NewsCategory, Sentiment

def crisis_monitoring(company_name, keywords):
    """Monitorización de crisis usando News Intelligence Agent"""
    
    print(f"🚨 Iniciando monitorización de crisis: {company_name}")
    
    agent = NewsIntelligenceAgent()
    
    # Buscar menciones recientes
    articles = agent.collect_news(
        categories=[NewsCategory.BUSINESS, NewsCategory.ECONOMY],
        time_range="24h"
    )
    
    # Filtrar artículos relevantes
    relevant_articles = []
    for article in articles:
        if any(keyword.lower() in article.content.lower() for keyword in keywords):
            relevant_articles.append(article)
    
    if not relevant_articles:
        print(f"✅ No se detectaron crisis potenciales")
        return {"status": "clear", "articles": []}
    
    # Analizar sentimiento y credibilidad
    crisis_indicators = []
    for article in relevant_articles:
        bias_analysis = agent.detect_bias(article)
        
        # Indicadores de crisis
        if article.sentiment in [Sentiment.NEGATIVE, Sentiment.VERY_NEGATIVE]:
            crisis_indicators.append({
                "article": article.title,
                "sentiment": article.sentiment.value,
                "credibility": article.credibility_score,
                "source": article.source,
                "bias_score": bias_analysis.get("overall_bias_score", 0)
            })
    
    # Generar alerta si hay indicadores críticos
    alert_level = "low"
    if len(crisis_indicators) >= 3:
        alert_level = "high"
    elif len(crisis_indicators) >= 1:
        alert_level = "medium"
    
    return {
        "status": "alert" if alert_level != "low" else "clear",
        "alert_level": alert_level,
        "indicators": crisis_indicators,
        "total_mentions": len(relevant_articles)
    }

# Uso del ejemplo
if __name__ == "__main__":
    company = "Mi Empresa"
    crisis_keywords = ["escándalo", "fraude", "crisis", "problema"]
    
    result = crisis_monitoring(company, crisis_keywords)
    
    if result["status"] == "alert":
        print(f"🚨 ALERTA DE CRISIS: {result['alert_level'].upper()}")
        for indicator in result["indicators"]:
            print(f"  ⚠️ {indicator['article']}")
            print(f"     Fuente: {indicator['source']} | Sentimiento: {indicator['sentiment']}")
    else:
        print(f"✅ Monitorización normal - No se detectaron crisis")
```

### Ejemplo 3: Data Pipeline Completo

```python
#!/usr/bin/env python3
"""
Ejemplo: Pipeline completo de datos desde múltiples fuentes
"""

from specialized import DataMiningAgent, DataSourceType, DataFormat
import json

def complete_data_pipeline():
    """Pipeline completo de extracción, transformación y análisis"""
    
    print(f"🚀 Iniciando pipeline completo de datos")
    
    # 1. Configurar múltiples fuentes
    sources = [
        {
            "name": "GitHub API",
            "type": "web_api",
            "url": "https://api.github.com/search/repositories",
            "params": {"q": "machine learning", "sort": "stars"}
        },
        {
            "name": "Hacker News",
            "type": "rss_feed",
            "url": "https://hnrss.org/frontpage"
        },
        {
            "name": "Product Hunt",
            "type": "web_scraping",
            "url": "https://www.producthunt.com/topics/ai",
            "selectors": {
                "name": {"css_selector": "h3"},
                "description": {"css_selector": ".fontWeight-600"}
            }
        }
    ]
    
    # 2. Extracción en paralelo
    agent = DataMiningAgent()
    datasets = agent.extract_batch(sources, max_concurrent=3)
    
    print(f"✅ Extracción completada:")
    for dataset in datasets:
        print(f"  📊 {dataset.name}: {dataset.total_records} registros")
    
    # 3. Transformación de datos
    transformations = [
        {
            "type": "field_mapping",
            "field_mapping": {
                "description": "content",
                "name": "title"
            }
        },
        {
            "type": "data_cleaning",
            "cleaning_rules": {
                "title": {
                    "remove_whitespace": True,
                    "lowercase": False
                }
            }
        }
    ]
    
    # 4. Procesamiento de cada dataset
    processed_datasets = []
    for dataset in datasets:
        processed = agent.transform_dataset(
            dataset=dataset,
            transformations=transformations
        )
        processed_datasets.append(processed)
        
        # Análisis inmediato
        analysis = agent.analyze_dataset(processed)
        print(f"  📈 {dataset.name}: Calidad {analysis['data_quality_analysis']['average_quality_score']:.2f}")
    
    # 5. Consolidación y exportación
    consolidated_data = {
        "pipeline_info": {
            "timestamp": agent.search_engine.search_web("test", max_results=1).timestamp,
            "sources_processed": len(sources),
            "datasets_created": len(datasets)
        },
        "datasets": processed_datasets
    }
    
    # Exportar resultado consolidado
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
        json.dump(consolidated_data, f, indent=2, default=str)
        print(f"  💾 Pipeline completado - Datos guardados en: {f.name}")
    
    return consolidated_data

# Ejecutar pipeline
if __name__ == "__main__":
    results = complete_data_pipeline()
    print(f"\n🎉 Pipeline completado exitosamente!")
```

## ⚙️ Configuración Avanzada

### Configuración de Entorno

```python
# config/specialized_agents_config.py
import os
from specialized import DEFAULT_CONFIG

SPECIALIZED_AGENTS_CONFIG = {
    **DEFAULT_CONFIG,
    
    # Configuración de logging
    "logging": {
        "level": os.getenv("AGENTS_LOG_LEVEL", "INFO"),
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": os.getenv("AGENTS_LOG_FILE", "/var/log/mcp-agents.log")
    },
    
    # Configuración de cachés
    "cache": {
        "research_cache_size": 1000,
        "news_cache_size": 500,
        "data_cache_size": 200,
        "cache_ttl": 3600  # 1 hora
    },
    
    # Configuración de seguridad
    "security": {
        "max_requests_per_minute": 60,
        "request_timeout": 30,
        "allowed_domains": [
            "*.edu", "*.gov", "*.org",
            "elpais.com", "elmundo.es", "bbc.com", "reuters.com"
        ],
        "blocked_domains": ["*.tk", "*.ml", "*.ga"]
    },
    
    # Configuración de rendimiento
    "performance": {
        "max_concurrent_agents": 5,
        "worker_threads": 10,
        "batch_processing": True,
        "parallel_requests": True
    }
}
```

### Configuración de Base de Datos

```python
# config/database_config.py
DATABASE_CONFIG = {
    "research_reports": {
        "table": "research_reports",
        "indexes": ["query", "method", "created_at"],
        "retention_days": 90
    },
    "news_articles": {
        "table": "news_articles", 
        "indexes": ["source", "category", "published_at"],
        "retention_days": 30
    },
    "datasets": {
        "table": "datasets",
        "indexes": ["name", "source_type", "created_at"],
        "retention_days": 180
    }
}
```

## 🧪 Tests y Validación

### Ejecución de Tests

```bash
# Ejecutar todos los tests
cd mcp-core-superior
python -m pytest tests/test_specialized_agents.py -v

# Tests específicos por agente
python -m pytest tests/test_specialized_agents.py::TestResearchAgent -v
python -m pytest tests/test_specialized_agents.py::TestDataMiningAgent -v
python -m pytest tests/test_specialized_agents.py::TestNewsIntelligenceAgent -v

# Tests de integración
python -m pytest tests/test_specialized_agents.py::TestSpecializedAgentsIntegration -v

# Tests de rendimiento
python -m pytest tests/test_specialized_agents.py::TestSpecializedAgentsPerformance -v
```

### Tests de Validación de Producción

```python
#!/usr/bin/env python3
"""
Tests de validación para entorno de producción
"""

from specialized import (
    ResearchAgent, DataMiningAgent, NewsIntelligenceAgent,
    get_specialized_agent, get_agent_health_status
)

def production_validation():
    """Validación completa del sistema para producción"""
    
    print("🔍 Iniciando validación de producción...")
    
    validation_results = {
        "agents_initialization": {},
        "health_checks": {},
        "functionality_tests": {},
        "performance_metrics": {}
    }
    
    # 1. Test de inicialización de agentes
    for agent_type in ["research", "data_mining", "news_intelligence"]:
        try:
            agent = get_specialized_agent(agent_type)
            validation_results["agents_initialization"][agent_type] = {
                "success": True,
                "agent_name": agent.name,
                "version": agent.version
            }
            print(f"  ✅ {agent_type}: Inicializado correctamente")
        except Exception as e:
            validation_results["agents_initialization"][agent_type] = {
                "success": False,
                "error": str(e)
            }
            print(f"  ❌ {agent_type}: Error - {e}")
    
    # 2. Health checks
    for agent_type in ["research", "data_mining", "news_intelligence"]:
        health = get_agent_health_status(agent_type)
        validation_results["health_checks"][agent_type] = health
        status_emoji = "✅" if health["healthy"] else "❌"
        print(f"  {status_emoji} {agent_type}: {health['status']}")
    
    # 3. Tests funcionales básicos
    try:
        research_agent = ResearchAgent()
        
        # Test de generación de consultas
        queries = research_agent._generate_research_queries(
            "test query", ResearchMethod.EXPLORATORY, ""
        )
        validation_results["functionality_tests"]["research_queries"] = {
            "success": len(queries) > 0,
            "query_count": len(queries)
        }
        
        print(f"  ✅ Research queries: {len(queries)} generadas")
        
    except Exception as e:
        validation_results["functionality_tests"]["research_queries"] = {
            "success": False,
            "error": str(e)
        }
        print(f"  ❌ Research queries: Error - {e}")
    
    try:
        data_agent = DataMiningAgent()
        
        # Test de validación de configuración
        valid_config = {"type": "web_api", "url": "https://test.com"}
        is_valid = data_agent._validate_source_config(valid_config)
        validation_results["functionality_tests"]["config_validation"] = {
            "success": is_valid,
            "validation_result": is_valid
        }
        
        print(f"  ✅ Config validation: {'Válida' if is_valid else 'Inválida'}")
        
    except Exception as e:
        validation_results["functionality_tests"]["config_validation"] = {
            "success": False,
            "error": str(e)
        }
        print(f"  ❌ Config validation: Error - {e}")
    
    try:
        news_agent = NewsIntelligenceAgent()
        
        # Test de análisis de sentimiento
        sentiment = news_agent._analyze_basic_sentiment("Excelente noticia")
        validation_results["functionality_tests"]["sentiment_analysis"] = {
            "success": sentiment is not None,
            "detected_sentiment": sentiment.value if sentiment else None
        }
        
        print(f"  ✅ Sentiment analysis: {sentiment.value if sentiment else 'Error'}")
        
    except Exception as e:
        validation_results["functionality_tests"]["sentiment_analysis"] = {
            "success": False,
            "error": str(e)
        }
        print(f"  ❌ Sentiment analysis: Error - {e}")
    
    # Resumen de validación
    total_tests = sum(
        len(category) for category in validation_results.values()
    )
    successful_tests = sum(
        sum(1 for test in category.values() if test.get("success", False))
        for category in validation_results.values()
    )
    
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"\n📊 Resumen de Validación:")
    print(f"  Tests ejecutados: {total_tests}")
    print(f"  Tests exitosos: {successful_tests}")
    print(f"  Tasa de éxito: {success_rate:.1f}%")
    
    if success_rate >= 95:
        print(f"  🎉 Sistema listo para producción!")
    elif success_rate >= 80:
        print(f"  ⚠️ Sistema funcional con advertencias")
    else:
        print(f"  🚨 Sistema no listo para producción")
    
    return validation_results

if __name__ == "__main__":
    production_validation()
```

## 🔧 Resolución de Problemas

### Problemas Comunes y Soluciones

#### 1. Error de Importación

**Problema**: `ImportError: cannot import name 'SpecializedAgent'`

**Solución**:
```bash
# Verificar estructura de archivos
ls -la src/agents/specialized/

# Verificar Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Reinstalar dependencias
pip install -e .
```

#### 2. Conexión de Red Falla

**Problema**: Timeouts o errores de conexión

**Solución**:
```python
# Aumentar timeouts
agent.config["timeout_seconds"] = 60
agent.config["retry_attempts"] = 5

# Verificar configuración de proxy
import os
os.environ["HTTP_PROXY"] = "http://proxy.company.com:8080"
os.environ["HTTPS_PROXY"] = "http://proxy.company.com:8080"
```

#### 3. Calidad de Datos Baja

**Problema**: Dataset con calidad_score < 0.5

**Solución**:
```python
# Ajustar umbrales de calidad
agent.config["quality_threshold"] = 0.4

# Revisar configuración de validación
agent.config["enable_data_validation"] = True

# Verificar fuentes de datos
credible_sources = [
    source for source in sources 
    if source_credibility >= 0.7
]
```

#### 4. Rendimiento Lento

**Problema**: Agents tardan mucho en responder

**Solución**:
```python
# Optimizar configuración de concurrencia
agent.config["max_concurrent_extractions"] = 3
agent.config["batch_size"] = 50

# Activar caché
agent.config["cache_extractions"] = True
agent.clear_research_cache()  # Limpiar caché corrupto

# Reducir volumen de datos
agent.config["max_articles_per_source"] = 20
```

### Debugging Avanzado

#### Logging Detallado

```python
import logging

# Configurar logging para debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/mcp-agents-debug.log'),
        logging.StreamHandler()
    ]
)

# Logger específico para agente
logger = logging.getLogger('specialized.ResearchAgent')
logger.setLevel(logging.DEBUG)
```

#### Monitorización de Memoria

```python
import psutil
import gc

def monitor_agent_memory(agent, operation_name):
    """Monitoriza uso de memoria durante operaciones"""
    
    process = psutil.Process()
    memory_before = process.memory_info().rss / 1024 / 1024  # MB
    
    print(f"💾 Memoria antes de {operation_name}: {memory_before:.2f} MB")
    
    # Ejecutar operación
    result = operation()
    
    # Forzar garbage collection
    gc.collect()
    
    memory_after = process.memory_info().rss / 1024 / 1024  # MB
    memory_diff = memory_after - memory_before
    
    print(f"💾 Memoria después de {operation_name}: {memory_after:.2f} MB")
    print(f"💾 Diferencia: {memory_diff:.2f} MB")
    
    if memory_diff > 100:  # Más de 100MB
        print(f"⚠️ Posible memory leak detectado")
    
    return result

# Uso
def my_operation():
    report = agent.conduct_research("test query")
    return report

result = monitor_agent_memory(agent, my_operation)
```

### Performance Optimization

#### Optimización de Caché

```python
from functools import lru_cache
import time

class OptimizedResearchAgent(ResearchAgent):
    """Versión optimizada del ResearchAgent"""
    
    def __init__(self):
        super().__init__()
        self._query_cache = {}
        self._cache_maxsize = 100
        self._cache_ttl = 300  # 5 minutos
    
    @lru_cache(maxsize=100)
    def _cached_search_method(self, query_hash, method):
        """Búsqueda con caché LRU"""
        # Implementación de búsqueda en caché
        pass
    
    def _is_cache_valid(self, cache_entry):
        """Verifica si entrada de caché es válida"""
        return time.time() - cache_entry["timestamp"] < self._cache_ttl
```

#### Paralelización Avanzada

```python
import concurrent.futures
import asyncio

class ParallelDataMiningAgent(DataMiningAgent):
    """Versión con paralelización optimizada"""
    
    def extract_data_parallel(self, source_configs, max_workers=None):
        """Extracción verdaderamente paralela"""
        
        if max_workers is None:
            max_workers = min(len(source_configs), self.config["max_concurrent_extractions"])
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit todas las tareas
            future_to_config = {
                executor.submit(self.extract_data, config): config 
                for config in source_configs
            }
            
            results = []
            for future in concurrent.futures.as_completed(future_to_config):
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                except Exception as e:
                    config = future_to_config[future]
                    print(f"Error en extracción {config.get('name')}: {e}")
        
        return results
```

---

## 📞 Soporte y Contacto

Para soporte técnico, reportar bugs o solicitar nuevas funcionalidades:

- **Documentación**: [Ver documentación completa]
- **Issues**: [Reportar problemas en GitHub]
- **Email**: [soporte@mcp-superior.com]
- **Wiki**: [Documentación extendida]

---

**Versión**: 1.0.0  
**Última actualización**: 2025-01-04  
**Autor**: MCP Superior Development Team