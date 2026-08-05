# Web Scraping & Playwright Agent

## Descripción

El WebScrapingAgent es un agente especializado en web scraping avanzado que combina las capacidades de Playwright para manejar JavaScript con herramientas tradicionales de scraping HTTP. Proporciona capacidades de extracción de datos estructurados, capturas de pantalla, mitigación de detección de bots y rate limiting.

## Características Principales

### 🚀 Capacidades de Scraping
- **Modos múltiples**: Fast, Standard, JavaScript, Stealth
- **Integración con Playwright**: Soporte completo para JavaScript y SPAs
- **Extracción de datos estructurados**: Meta tags, Open Graph, JSON-LD, tablas
- **Capturas de pantalla**: PNG, JPEG, WEBP con control de calidad

### 🛡️ Anti-Detección de Bots
- **Rotación de User Agents**: Pool de 8+ user agents reales
- **Rate Limiting**: Control automático de frecuencia de requests
- **Delays human-like**: Simulación de comportamiento humano
- **Configuración flexible**: Estrategias personalizables

### 🔧 Funcionalidades Avanzadas
- **Scraping interactivo**: Clicks, formularios, scroll
- **Shadow DOM**: Extracción de contenido en Shadow DOM
- **Batch processing**: Múltiples URLs con concurrencia controlada
- **Manejo de errores**: Recovery automático y logging detallado

## Instalación

### Dependencias
```bash
pip install playwright beautifulsoup4 requests pydantic
playwright install chromium
```

### Dependencias del Sistema
```bash
# Ubuntu/Debian
sudo apt-get install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2

# macOS
brew install playwright

# Windows
# Playwright maneja la instalación automáticamente
```

## Uso Básico

### Scraping Simple
```python
from agents.web_scraping_agent import WebScrapingAgentWrapper

# Crear agente
agent = WebScrapingAgentWrapper()
await agent.ensure_initialized()

# Scraping básico
request = {
    "operation": "single_url",
    "url": "https://ejemplo.com",
    "mode": "fast",
    "extract_options": {
        "text": True,
        "structured": True,
        "links": True
    }
}

result = await agent.process_request(request)
```

### Scraping con Playwright
```python
# Scraping con JavaScript
request = {
    "operation": "single_url",
    "url": "https://single-page-app.com",
    "mode": "javascript",
    "extract_options": {
        "text": True,
        "structured": True
    },
    "playwright_options": {
        "wait_for_selector": ".content-loaded",
        "wait_time": 3.0,
        "take_screenshot": True
    }
}
```

### Batch Scraping
```python
# Múltiples URLs
request = {
    "operation": "batch_urls",
    "urls": [
        "https://sitio.com/page1",
        "https://sitio.com/page2",
        "https://sitio.com/page3"
    ],
    "shared_options": {
        "mode": "fast",
        "extract_options": {"text": True}
    },
    "rate_limit": 2.0,
    "parallel_requests": 3
}
```

### Modo Stealth (Anti-Detección)
```python
from agents.web_scraping_agent import BotDetectionStrategy, BotMitigationConfig

# Configuración anti-bot
bot_config = BotMitigationConfig(
    strategies=[
        BotDetectionStrategy.USER_AGENT_ROTATION,
        BotDetectionStrategy.REQUEST_DELAY,
        BotDetectionStrategy.HUMAN_LIKE_DELAY
    ],
    min_delay=1.0,
    max_delay=5.0
)

request = {
    "operation": "stealth_scrape",
    "url": "https://sitio-protegido.com",
    "bot_config": bot_config.dict()
}
```

## Configuración Avanzada

### Schemas Pydantic

#### ScrapingRequest
```python
from agents.web_scraping_agent import ScrapingRequest, ScrapingMode

request = ScrapingRequest(
    url="https://ejemplo.com",
    mode=ScrapingMode.JAVASCRIPT,
    extract_text=True,
    extract_structured=True,
    wait_for_selector=".dynamic-content",
    wait_time=5.0,
    take_screenshot=True,
    screenshot_format=ScreenshotFormat.PNG,
    click_elements=[".load-more", ".show-details"],
    fill_forms={"input[name=search]": "término de búsqueda"},
    scroll_pages=3
)
```

#### StructuredDataExtractor
```python
from agents.web_scraping_agent import StructuredDataExtractor

extractor = StructuredDataExtractor(
    extract_tables=True,
    extract_json_ld=True,
    extract_microdata=True,
    extract_og_tags=True,
    extract_meta_tags=True,
    custom_selectors={
        "precios": ".price-list .item",
        "categorías": ".category-links a"
    }
)
```

## Integración con el Sistema MCP

### Registro en ExecutorAgent
El WebScrapingAgent se integra automáticamente con el ExecutorAgent:

```python
# En executor_wrapper.py
self.available_tools = [
    "web_scraping_agent",
    "web_scraper",  # Herramienta básica
    # ... otras herramientas
]
```

### Uso desde el Planificador
```python
# El PlannerAgent puede incluir tareas de web scraping
plan_task = {
    "tool": "web_scraping_agent",
    "parameters": {
        "operation": "single_url",
        "url": "https://fuente-datos.com/api",
        "mode": "javascript"
    }
}
```

## Manejo de Errores y Logging

### Logging Configurado
```python
import logging

# Configurar logging específico
logging.getLogger("mcp.agents.web_scraping").setLevel(logging.DEBUG)
```

### Manejo de Errores Comunes
```python
try:
    result = await agent.process_request(request)
    if not result["success"]:
        error = result.get("error")
        print(f"Error en scraping: {error}")
except Exception as e:
    print(f"Excepción: {e}")
```

## Rate Limiting y Performance

### Configuración de Rate Limits
```python
# Rate limiting personalizado
agent.min_request_interval = 2.0  # Mínimo 2 segundos entre requests
agent.request_times = []  # Resetear historial
```

### Optimización de Concurrencia
```python
# Configurar según capacidad del sistema
agent.max_concurrent = 5  # Máximo 5 requests simultáneos
```

## Capturas de Pantalla

### Formatos Soportados
- **PNG**: Calidad sin pérdida (por defecto)
- **JPEG**: Compresión configurable (1-100)
- **WEBP**: Formato moderno con buena compresión

### Ejemplo de Uso
```python
request = {
    "operation": "single_url",
    "url": "https://sitio.com/dashboard",
    "playwright_options": {
        "take_screenshot": True,
        "screenshot_format": "jpeg",
        "screenshot_quality": 85
    }
}
```

## Extracción de Datos Estructurados

### Meta Tags y Open Graph
```python
# Automáticamente extraído cuando extract_structured=True
structured_data = {
    "title": "Título de la página",
    "description": "Meta descripción",
    "og_title": "Título para redes sociales",
    "og_image": "Imagen de preview"
}
```

### JSON-LD
```python
# Extrae datos estructurados de scripts JSON-LD
json_ld_data = [
    {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Producto Ejemplo",
        "price": "29.99"
    }
]
```

## Consideraciones de Seguridad

### Validación de URLs
- Solo se permiten URLs HTTP/HTTPS
- Verificación de dominios permitidos configurables
- Sanitización de inputs

### Rate Limiting
- Prevención de sobrecarga de servidores
- Respeto por robots.txt (configurable)
- Delays automáticos entre requests

### Detección de Bots
- Rotación automática de user agents
- Headers realistas
- Comportamiento human-like

## Testing

### Ejecutar Tests
```bash
cd mcp-core-superior
python test_web_scraping_agent.py
```

### Tests Incluidos
- ✅ Health Check
- ✅ Scraping Básico
- ✅ Scraping con Playwright  
- ✅ Batch Scraping
- ✅ Modo Stealth

## Ejemplos de Integración

### Con Backend Tools
```python
# Usar tanto web_scraper como web_scraping_agent
from backend.tools.web_scraper import WebScraper

# WebScraper para contenido estático
static_scraper = WebScraper()
result1 = static_scraper.scrape_url("https://sitio-estatico.com")

# WebScrapingAgent para contenido dinámico
agent = WebScrapingAgentWrapper()
result2 = await agent.process_request({
    "operation": "single_url",
    "url": "https://spa-dinamica.com",
    "mode": "javascript"
})
```

### MCP Protocol Support
```python
from agents.web_scraping_agent import WebScrapingMCPSchema

# Schema de entrada para MCP
input_schema = WebScrapingMCPSchema.get_input_schema()

# Schema de salida para MCP  
output_schema = WebScrapingMCPSchema.get_output_schema()
```

## Limitaciones Conocidas

1. **Playwright**: Requiere dependencias del sistema adicionales
2. **Memoria**: Scraping de páginas muy grandes puede consumir RAM
3. **Rate Limits**: Algunos sitios tienen protecciones muy estrictas
4. **JavaScript Complejo**: Algunos SPAs requieren configuraciones especiales

## Troubleshooting

### Playwright no disponible
```python
# El agente fallará automáticamente a modo 'fast'
agent = WebScrapingAgentWrapper()
# Automáticamente usará requests en lugar de Playwright
```

### Timeouts frecuentes
```python
# Aumentar timeouts
request["playwright_options"]["timeout"] = 60.0
request["timeout"] = 60.0
```

### Errores de rate limiting
```python
# Aumentar delays
request["rate_limit"] = 5.0
# O usar modo stealth
request["operation"] = "stealth_scrape"
```

## Contribuir

Para añadir nuevas funcionalidades:

1. Extender las clases de schemas Pydantic
2. Añadir nuevos métodos de extracción
3. Implementar estrategias anti-bot adicionales
4. Actualizar tests en `test_web_scraping_agent.py`

## Licencia

Este agente sigue la misma licencia que el proyecto MCP Core Superior.