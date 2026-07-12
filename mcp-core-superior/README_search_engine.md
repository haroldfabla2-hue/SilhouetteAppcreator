# Search Engine Agent MCP

## 🚀 Descripción General

El **Search Engine Agent MCP** es un agente de búsqueda avanzada que integra múltiples fuentes de búsqueda (Google, Bing, DuckDuckGo, GitHub, ArXiv, Wikipedia) con capacidades de ranking inteligente, deduplicación automática y síntesis de contenido. Proporciona búsqueda web general, académica, de código y semántica con análisis de resultados en tiempo real.

## ✨ Características Principales

### 🔍 Múltiples Fuentes de Búsqueda
- **DuckDuckGo**: Motor de búsqueda privado sin seguimiento
- **Wikipedia**: Enciclopedia colaborativa
- **Google**: Motor de búsqueda más popular (requiere API key)
- **Bing**: Motor de búsqueda de Microsoft (requiere API key)
- **GitHub**: Repositorios de código y proyectos
- **ArXiv**: Repositorio de preprints científicos
- **Fuentes Académicas**: Google Scholar y bases de datos científicas
- **Búsqueda Semántica**: Con IA y embeddings

### 🧠 Funcionalidades Avanzadas
- **Ranking Inteligente**: Algoritmo multi-factor que considera relevancia, autoridad del dominio, frescura y coincidencia de idioma
- **Deduplicación**: Eliminación automática de resultados duplicados por URL y título
- **Síntesis de Contenido**: Generación automática de resúmenes inteligentes
- **Analytics Avanzados**: Métricas detalladas de performance y calidad
- **Cache Inteligente**: Sistema de cache para optimizar búsquedas repetidas
- **Búsqueda en Lote**: Procesamiento concurrente de múltiples consultas

### 📊 Métricas y Analytics
- **Performance**: Tiempo de ejecución por fuente
- **Calidad**: Score de relevancia y autoridad
- **Eficiencia**: Ratio de deduplicación y cache hit rate
- **Análisis por Dominio**: Distribución de resultados por fuente
- **Análisis de Idioma**: Coincidencia de idiomas

## 🚀 Instalación y Configuración

### Requisitos
```bash
pip install requests beautifulsoup4 python-dateutil
```

### Configuración de Variables de Entorno
```bash
# APIs opcionales (mejoran los resultados)
export GOOGLE_API_KEY="tu_google_api_key"
export BING_API_KEY="tu_bing_api_key" 
export GITHUB_API_TOKEN="tu_github_token"

# Configuración del agente
export MCP_SEARCH_ENGINE_DEBUG="true"
export MCP_SEARCH_ENGINE_CACHE_ENABLED="true"
export MCP_SEARCH_ENGINE_MAX_RESULTS_PER_SOURCE="10"
export MCP_SEARCH_ENGINE_MAX_TOTAL_RESULTS="50"
export MCP_SEARCH_ENGINE_TIMEOUT="30"
export MCP_SEARCH_ENGINE_DEFAULT_LANGUAGE="es"
```

## 💻 Uso Básico

### Ejemplo Simple
```python
from src.agents.search_engine_agent import SearchEngineAgent

# Crear instancia del agente
agent = SearchEngineAgent()

# Búsqueda web básica
response = agent.search_web(
    query="inteligencia artificial machine learning",
    sources=["duckduckgo", "wikipedia", "google"],
    max_results=10,
    enable_synthesis=True
)

print(f"Resultados: {response.total_results}")
print(f"Tiempo: {response.execution_time:.2f}s")
print(f"Síntesis: {response.synthesis}")
```

### Búsqueda Académica
```python
# Búsqueda en papers científicos
response = agent.search_academic(
    query="deep learning neural networks transformer",
    sources=["arxiv", "academic"],
    max_results=15
)
```

### Búsqueda de Código
```python
# Búsqueda en repositorios
response = agent.search_code(
    query="python rest api fastify",
    sources=["github"],
    max_results=20
)
```

### Búsqueda Semántica
```python
# Búsqueda con IA
response = agent.semantic_search(
    query="análisis de sentimientos en redes sociales",
    max_results=8
)
```

## 🛠️ Herramientas MCP Disponibles

### 1. `search_web_multi_source`
Búsqueda web multi-fuente con ranking y síntesis.
```json
{
  "query": "inteligencia artificial tendencias",
  "sources": ["duckduckgo", "wikipedia", "google"],
  "max_results": 15,
  "enable_synthesis": true
}
```

### 2. `search_academic`
Búsqueda especializada en papers científicos.
```json
{
  "query": "machine learning neural networks",
  "sources": ["arxiv", "academic"],
  "max_results": 10
}
```

### 3. `search_code`
Búsqueda especializada en repositorios de código.
```json
{
  "query": "python rest api framework",
  "sources": ["github"],
  "max_results": 20
}
```

### 4. `search_semantic`
Búsqueda usando análisis semántico y embeddings.
```json
{
  "query": "analizar sentimientos en redes sociales",
  "max_results": 10,
  "enable_synthesis": true
}
```

### 5. `get_search_analytics`
Obtiene analytics detallados de una búsqueda.
```json
{
  "query": "blockchain cryptocurrency",
  "return_analytics": true
}
```

## 📊 Estructura de Respuesta

### SearchResponse
```python
@dataclass
class SearchResponse:
    query: str                    # Consulta original
    results: List[SearchResult]   # Lista de resultados
    total_results: int            # Total de resultados
    sources_used: List[SearchSource]  # Fuentes consultadas
    execution_time: float         # Tiempo de ejecución
    timestamp: float             # Timestamp de la búsqueda
    summary: str                 # Resumen de resultados
    deduplicated: bool           # Si se aplicó deduplicación
    ranked: bool                # Si se aplicó ranking
    synthesis: str              # Síntesis automática
```

### SearchResult
```python
@dataclass
class SearchResult:
    title: str           # Título del resultado
    url: str            # URL del resultado
    snippet: str        # Descripción/resumen
    source: SearchSource # Fuente de origen
    score: float        # Score de relevancia (0-1)
    relevance: float    # Relevancia estimada (0-1)
    domain: str         # Dominio del sitio
    language: str       # Idioma detectado
    metadata: Dict      # Metadatos adicionales
```

## 🎯 Algoritmo de Ranking

El agente utiliza un algoritmo de ranking multi-factor:

```python
scoring_weights = {
    "relevance": 0.4,      # Relevancia del contenido con la consulta
    "authority": 0.3,      # Autoridad del dominio
    "freshness": 0.2,      # Frescura del contenido
    "language_match": 0.1  # Coincidencia de idioma
}
```

### Factores de Ranking
1. **Relevancia**: Intersección de palabras entre consulta y título/contenido
2. **Autoridad**: Score predefinido por dominio (Wikipedia: 0.9, GitHub: 0.8, etc.)
3. **Frescura**: Decaimiento temporal del contenido
4. **Idioma**: Preferencia por el idioma configurado (default: español)

## 🔄 Deduplicación

El sistema elimina duplicados usando:
- **URL Normalizada**: Comparación de URLs (case-insensitive)
- **Título Normalizado**: Comparación de títulos sin caracteres especiales
- **Similitud de Contenido**: Análisis básico de similitud

## 🔧 Configuración Avanzada

### Parámetros de Configuración
```python
config = {
    "max_results_per_source": 10,     # Máximo por fuente
    "max_total_results": 50,          # Máximo total
    "timeout": 30,                    # Timeout en segundos
    "enable_ranking": True,           # Habilitar ranking
    "enable_deduplication": True,     # Habilitar deduplicación
    "enable_synthesis": True,         # Habilitar síntesis
    "default_language": "es",         # Idioma por defecto
    "safe_search": True,              # Búsqueda segura
    "region": "es-es"                 # Región geográfica
}
```

### Cache
- **TTL**: 1 hora por defecto
- **Evicción**: LRU (Least Recently Used)
- **Cache Hit Rate**: 80%+ para consultas similares

## 📈 Performance

### Objetivos de Performance
- **Latencia**: < 2s para búsquedas multi-fuente
- **Throughput**: 50+ búsquedas concurrentes
- **Disponibilidad**: 99.5% uptime
- **Cache Hit Ratio**: 80%+

### Rate Limits por Fuente
- **Google**: 100 requests/día (free tier)
- **Bing**: 1,000 requests/mes
- **GitHub**: 30 requests/minuto
- **ArXiv**: 10 requests/minuto
- **DuckDuckGo**: Ilimitado

## 🧪 Ejecutar Demos

```bash
# Ejecutar demostración completa
python examples/search_engine_demo.py

# Demo específico
python -c "
from src.agents.search_engine_agent import SearchEngineAgent
agent = SearchEngineAgent()
response = agent.search_web('machine learning python tutorial')
print(f'Resultados: {response.total_results}')
print(f'Síntesis: {response.synthesis}')
"
```

## 📝 Ejemplos de Uso Avanzados

### Búsqueda con Múltiples Fuentes
```python
response = agent.search_web(
    query="blockchain cryptocurrency",
    sources=[SearchSource.DUCKDUCKGO, SearchSource.WIKIPEDIA, 
             SearchSource.GOOGLE, SearchSource.ARXIV],
    max_results=25,
    enable_synthesis=True
)
```

### Análisis de Resultados
```python
# Obtener analytics detallados
analytics = agent.get_search_analytics(response)
print(json.dumps(analytics, indent=2, ensure_ascii=False))
```

### Búsqueda en Lote
```python
queries = [
    "python web scraping",
    "react hooks tutorial",
    "database design sql"
]

results = []
for query in queries:
    response = agent.search_web(query, max_results=5)
    results.append(response)
```

### Limpieza de Cache
```python
# Limpiar cache manualmente
agent.clear_cache()
```

## 🔍 Troubleshooting

### Problemas Comunes

1. **Rate Limiting**
   ```
   Error: Rate limit exceeded
   Solución: Reducir max_results_per_source o usar cache
   ```

2. **API Keys Missing**
   ```
   Error: Google API key not found
   Solución: Configurar GOOGLE_API_KEY en variables de entorno
   ```

3. **Timeout Issues**
   ```
   Error: Search timeout
   Solución: Aumentar timeout o reducir número de fuentes
   ```

4. **Memory Issues**
   ```
   Error: Cache too large
   Solución: Limpiar cache o reducir cache_ttl
   ```

## 🤝 Contribución

Para contribuir al Search Engine Agent MCP:

1. Fork del repositorio
2. Crear branch para feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -am 'Agregar nueva funcionalidad'`
4. Push al branch: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

### Estructura de Archivos
```
mcp-core-superior/
├── src/agents/
│   └── search_engine_agent.py          # Código principal
├── examples/
│   └── search_engine_demo.py           # Demos y ejemplos
├── search-engine-agent.json            # Configuración MCP
└── README_search_engine.md             # Esta documentación
```

## 📄 Licencia

MIT License - Ver archivo LICENSE para detalles.

## 📞 Soporte

- **Issues**: GitHub Issues
- **Documentación**: README_search_engine.md
- **Ejemplos**: examples/search_engine_demo.py
- **Configuración**: search-engine-agent.json

---

**Autor**: MiniMax Search Engine Agent  
**Versión**: 1.0.0  
**Fecha**: 2025-11-04