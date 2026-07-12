# 🌐 Web Scraping Agent - Guía Completa

## Descripción General

El **Web Scraping Agent** es un agente especializado que proporciona capacidades avanzadas de web scraping, navegación automatizada y extracción de datos usando **herramientas reales** como Playwright, Selenium y BeautifulSoup. Es una herramienta **operacional real** que interactúa directamente con navegadores web, ejecuta JavaScript y maneja sitios web complejos.

**Estado**: ✅ **PRODUCCIÓN ACTIVA**  
**Tecnologías**: Playwright, Selenium, BeautifulSoup, aiohttp  
**Navegadores**: Chrome, Firefox, Safari WebKit (experimental)  
**Capacidades**: JavaScript execution, screenshots, data extraction, form automation

## 🎯 Capacidades Principales

### Navegación y Scraping Avanzado
- **JavaScript Execution**: Ejecuta JavaScript en páginas dinámicas
- **SPA Support**: Maneja Single Page Applications (React, Vue, Angular)
- **Infinite Scroll**: Automatización de scroll infinito
- **Lazy Loading**: Manejo de contenido lazy-loaded
- **AJAX/Fetch**: Intercepta y maneja requests asíncronos

### Automatización de Formularios
- **Login Automation**: Automatización de procesos de login
- **Form Submission**: Relleno y envío de formularios complejos
- **Multi-step Workflows**: Workflows de múltiples pasos
- **CAPTCHA Handling**: Detección y manejo de CAPTCHAs

### Capturas y Multimedia
- **Screenshots HD**: Capturas de pantalla de alta resolución
- **PDF Generation**: Generación de PDFs de páginas
- **Video Recording**: Grabación de sesiones de navegación
- **Asset Extraction**: Descarga de imágenes, videos, archivos

### Anti-Detection y Stealth
- **User Agent Rotation**: Rotación de user agents
- **Proxy Support**: Integración con proxies
- **Request Delays**: Delays inteligentes para evitar detección
- **Browser Fingerprinting**: Evasion de browser fingerprinting

## 🛠️ Instalación y Configuración

### Prerrequisitos del Sistema

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y wget gnupg

# Instalar navegadores
sudo wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
sudo apt-get update
sudo apt-get install -y google-chrome-stable

# Instalar Firefox
sudo apt-get install -y firefox-esr
```

### Instalación de Dependencias Python

```bash
# Instalar Playwright
pip install playwright

# Instalar navegadores para Playwright
playwright install chromium
playwright install firefox
playwright install webkit

# Instalar dependencias adicionales
pip install selenium beautifulsoup4 aiohttp requests-html lxml
```

### Configuración de Playwright

```bash
# Verificar instalación
python -m playwright --version

# Instalar navegadores del sistema
sudo playwright install-deps
sudo playwright install

# Verificar navegadores
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); print(p.chromium.version()); p.stop()"
```

## 📚 API Reference

### Operaciones Básicas de Scraping

#### 1. Scraping Básico

```http
POST /api/v1/tools/scraping
Content-Type: application/json

{
    "agent": "web_scraping",
    "action": "basic_scrape",
    "url": "https://ejemplo.com/productos",
    "method": "GET",
    "headers": {
        "User-Agent": "Mozilla/5.0 (compatible; MultiAgentBot/1.0)"
    },
    "extract": {
        "title": "title",
        "products": {
            "selector": ".product-item",
            "data": {
                "name": "h2.title",
                "price": ".price",
                "image": "img@src"
            }
        }
    },
    "save_response": true,
    "timeout": 30000
}
```

**Respuesta:**
```json
{
    "status": "success",
    "data": {
        "url": "https://ejemplo.com/productos",
        "title": "Catálogo de Productos",
        "products": [
            {
                "name": "Producto A",
                "price": "€29.99",
                "image": "https://ejemplo.com/img1.jpg"
            }
        ],
        "metadata": {
            "scraped_at": "2025-11-04T15:30:00Z",
            "response_time": 1.2,
            "status_code": 200
        }
    },
    "files": {
        "html": "/tmp/scraped_page.html",
        "screenshot": "/tmp/screenshot.png"
    }
}
```

#### 2. Navegación Avanzada con JavaScript

```http
POST /api/v1/tools/scraping
Content-Type: application/json

{
    "agent": "web_scraping",
    "action": "javascript_navigation",
    "url": "https://tienda.com/productos",
    "browser": "chromium",
    "headless": false,
    "viewport": {
        "width": 1920,
        "height": 1080
    },
    "wait_strategies": [
        {
            "type": "selector",
            "selector": ".product-list",
            "timeout": 10000
        },
        {
            "type": "network_idle",
            "timeout": 5000
        }
    ],
    "actions": [
        {
            "type": "click",
            "selector": ".filter-category",
            "index": 0
        },
        {
            "type": "select",
            "selector": ".sort-dropdown",
            "value": "price-asc"
        },
        {
            "type": "scroll",
            "direction": "down",
            "pixels": 500
        }
    ],
    "extract": {
        "products": {
            "selector": ".product-card",
            "type": "list",
            "data": {
                "title": ".product-title",
                "price": ".price-current",
                "old_price": ".price-old",
                "rating": ".rating-stars@data-rating",
                "reviews": ".review-count",
                "availability": ".stock-status",
                "image": ".product-image img@src"
            }
        }
    }
}
```

#### 3. Automatización de Formularios

```http
POST /api/v1/tools/scraping
Content-Type: application/json

{
    "agent": "web_scraping",
    "action": "form_automation",
    "url": "https://empresa.com/login",
    "browser": "firefox",
    "form_data": {
        "username": "usuario@empresa.com",
        "password": "password123",
        "remember_me": true
    },
    "form_selectors": {
        "username": "input[name='email']",
        "password": "input[name='password']",
        "submit": "button[type='submit']"
    },
    "workflow_steps": [
        {
            "action": "navigate",
            "url": "https://empresa.com/dashboard"
        },
        {
            "action": "click",
            "selector": ".profile-menu"
        },
        {
            "action": "click",
            "selector": "a[href='/settings']"
        },
        {
            "action": "extract",
            "data": {
                "user_info": ".user-profile",
                "settings": ".settings-panel"
            }
        }
    ],
    "captures": {
        "screenshots": true,
        "videos": false
    }
}
```

#### 4. Capturas de Pantalla Avanzadas

```http
POST /api/v1/tools/scraping
Content-Type: application/json

{
    "agent": "web_scraping",
    "action": "advanced_screenshots",
    "url": "https://dashboard.ejemplo.com",
    "browser": "chromium",
    "screenshot_config": {
        "full_page": true,
        "quality": 100,
        "format": "png",
        "device_scale": 2
    },
    "crop_options": {
        "selector": ".dashboard-main",
        "padding": 20
    },
    "annotations": [
        {
            "type": "text",
            "x": 100,
            "y": 50,
            "text": "Dashboard Principal",
            "font_size": 16
        },
        {
            "type": "rectangle",
            "x": 200,
            "y": 150,
            "width": 300,
            "height": 200,
            "color": "red"
        }
    ],
    "batch_urls": [
        "https://dashboard.ejemplo.com/page1",
        "https://dashboard.ejemplo.com/page2",
        "https://dashboard.ejemplo.com/page3"
    ]
}
```

#### 5. Manejo de SPA (Single Page Applications)

```http
POST /api/v1/tools/scraping
Content-Type: application/json

{
    "agent": "web_scraping",
    "action": "spa_navigation",
    "url": "https://app.ejemplo.com",
    "framework": "react", // react, vue, angular
    "wait_strategies": [
        {
            "type": "react_idle",
            "timeout": 15000
        },
        {
            "type": "custom_event",
            "event": "app-loaded"
        }
    ],
    "router_actions": [
        {
            "path": "/dashboard",
            "wait_for": "[data-testid='dashboard-content']"
        },
        {
            "path": "/reports",
            "wait_for": ".reports-grid"
        },
        {
            "path": "/settings",
            "wait_for": "[data-testid='settings-form']"
        }
    ],
    "data_extraction": {
        "dashboard_metrics": {
            "selector": ".metric-card",
            "type": "list"
        },
        "navigation_menu": {
            "selector": ".nav-item",
            "type": "list"
        }
    }
}
```

## 💻 Ejemplos de Uso

### Ejemplo 1: E-commerce Product Scraping

```python
import requests
import json

# Configuración
base_url = "http://localhost:8000/api/v1/tools/scraping"

headers = {
    "Content-Type": "application/json"
}

# Scraping completo de catálogo de productos
ecommerce_scraping = requests.post(base_url, headers=headers, json={
    "agent": "web_scraping",
    "action": "comprehensive_ecommerce_scrape",
    "url": "https://tienda.ejemplo.com/catalogo",
    "browser": "chromium",
    "categories": [
        "/electronica",
        "/ropa",
        "/hogar",
        "/deportes"
    ],
    "extraction_config": {
        "products": {
            "selector": ".product-item",
            "type": "list",
            "data": {
                "name": ".product-title",
                "price": ".price-current",
                "original_price": ".price-original",
                "discount": ".discount-badge",
                "rating": ".rating@data-rating",
                "review_count": ".review-count",
                "availability": ".stock-status",
                "image": ".product-image img@src",
                "url": "a@href"
            }
        },
        "pagination": {
            "selector": ".pagination a",
            "max_pages": 10
        }
    },
    "workflow": {
        "wait_for_products": true,
        "scroll_infinite": true,
        "click_load_more": true,
        "delay_between_actions": 1000
    },
    "output": {
        "save_html": True,
        "save_screenshots": True,
        "save_json": True,
        "format": "structured"
    }
})

result = ecommerce_scraping.json()
print(f"Productos extraídos: {len(result['data']['products'])}")
print(f"Categorías: {result['data']['categories_scraped']}")
```

### Ejemplo 2: Social Media Monitoring

```python
# Monitoreo de redes sociales
social_monitoring = requests.post(base_url, headers=headers, json={
    "agent": "web_scraping",
    "action": "social_media_monitoring",
    "platforms": [
        {
            "name": "twitter",
            "url": "https://twitter.com/search",
            "query": "@miempresa OR #miempresa",
            "login_required": True
        },
        {
            "name": "linkedin",
            "url": "https://www.linkedin.com/search",
            "query": "miempresa",
            "login_required": True
        }
    ],
    "authentication": {
        "twitter": {
            "username": "@usuario",
            "password": "password123"
        },
        "linkedin": {
            "email": "usuario@empresa.com",
            "password": "password123"
        }
    },
    "extraction": {
        "posts": {
            "selector": ".post-item",
            "data": {
                "content": ".post-text",
                "author": ".author-name",
                "timestamp": ".timestamp",
                "likes": ".like-count",
                "shares": ".share-count",
                "comments": ".comment-count"
            }
        }
    },
    "rate_limiting": {
        "requests_per_minute": 60,
        "random_delays": True
    }
})
```

### Ejemplo 3: Financial Data Extraction

```python
# Extracción de datos financieros
financial_scraping = requests.post(base_url, headers=headers, json={
    "agent": "web_scraping",
    "action": "financial_data_extraction",
    "sources": [
        {
            "name": "bank_statement",
            "url": "https://banco.ejemplo.com/statements",
            "requires_login": True
        },
        {
            "name": "investment_portfolio",
            "url": "https://inversiones.ejemplo.com/portfolio",
            "requires_login": True
        }
    ],
    "authentication": {
        "bank_statement": {
            "username": "12345678A",
            "password": "bank_password",
            "two_factor": True
        },
        "investment_portfolio": {
            "username": "inversor@empresa.com",
            "password": "investment_password"
        }
    },
    "data_extraction": {
        "transactions": {
            "selector": ".transaction-row",
            "type": "list",
            "data": {
                "date": ".transaction-date",
                "description": ".transaction-desc",
                "amount": ".transaction-amount",
                "balance": ".account-balance"
            }
        },
        "portfolio": {
            "holdings": {
                "selector": ".holding-row",
                "data": {
                    "symbol": ".stock-symbol",
                    "name": ".stock-name",
                    "shares": ".shares-owned",
                    "price": ".current-price",
                    "value": ".total-value",
                    "gain_loss": ".gain-loss"
                }
            }
        }
    },
    "output": {
        "format": "csv",
        "include_metadata": True,
        "anonymize_data": True
    }
})
```

## 🔧 Configuración Avanzada

### Configuración de Navegadores

```yaml
# browsers.yaml
chromium:
  enabled: true
  version: "latest"
  headless: false
  args:
    - "--no-sandbox"
    - "--disable-dev-shm-usage"
    - "--disable-web-security"
    - "--disable-features=VizDisplayCompositor"
  user_data_dir: "/tmp/chrome-profile"
  download_dir: "/tmp/downloads"

firefox:
  enabled: true
  headless: false
  firefox_user_prefs:
    "network.cookie.cookieBehavior": 0
    "dom.webdriver.enabled": false
  download_dir: "/tmp/downloads"

webkit:
  enabled: false  # Experimental
  headless: true
```

### Configuración de Proxy

```python
# proxy_config.py
proxy_config = {
    "enabled": True,
    "rotation": True,
    "proxies": [
        {
            "url": "http://proxy1:8080",
            "username": "user1",
            "password": "pass1"
        },
        {
            "url": "http://proxy2:8080",
            "username": "user2", 
            "password": "pass2"
        }
    ],
    "health_check": True,
    "failure_threshold": 3
}
```

### Configuración de Anti-Detection

```python
# anti_detection.yaml
anti_detection:
  user_agent_rotation:
    enabled: true
    pool_size: 100
    rotation_strategy: "random"

  request_delays:
    enabled: true
    min_delay: 1000
    max_delay: 5000
    randomize: true

  fingerprint_protection:
    enabled: true
    options:
      - "webdriver"
      - "chrome"
      - "permissions"

  session_management:
    enabled: true
    cookies_persistence: true
    session_rotation: "daily"
```

## 📊 Monitoreo y Métricas

### Métricas de Performance

```python
# Métricas disponibles
metrics = {
    "page_load_time": "time to load page completely",
    "js_execution_time": "JavaScript execution time",
    "network_requests": "number of HTTP requests",
    "data_extraction_time": "time to extract data",
    "screenshot_quality": "quality metrics",
    "success_rate": "percentage of successful scrapes"
}
```

### Dashboard de Monitoreo

Las métricas del Web Scraping Agent están disponibles en:
- **Performance**: Tiempo de carga por sitio web
- **Success Rates**: Tasas de éxito por URL/categoría
- **Error Analysis**: Errores comunes y soluciones
- **Browser Usage**: Estadísticas de uso de navegadores

## 🚨 Troubleshooting

### Problemas Comunes

#### Error: Timeout al cargar página

```python
# Configurar timeouts más altos
scraping_config = {
    "timeout": 60000,
    "wait_strategies": [
        {
            "type": "network_idle",
            "timeout": 30000
        }
    ]
}
```

#### Error: JavaScript no se ejecuta

```python
# Habilitar JavaScript explícitamente
browser_config = {
    "javascript_enabled": True,
    "wait_for_console": True,
    "handle_popups": True
}
```

#### Error: CAPTCHAs detectados

```python
# Configurar anti-detection
anti_detection = {
    "random_delays": True,
    "user_agent_rotation": True,
    "proxy_rotation": True,
    "human_behavior": True
}
```

### Debugging Avanzado

```bash
# Ver logs del navegador
docker-compose logs web-scraping-agent

# Habilitar modo debug
export SCRAPING_DEBUG=true
export PLAYWRIGHT_BROWSER_PATH=/usr/bin/chromium

# Verificar navegadores
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); print('Browsers:', list(p.chromium.executable_path, p.firefox.executable_path)); p.stop()"
```

## 🔒 Seguridad y Compliance

### Mejores Prácticas

1. **Rate Limiting**: Respetar límites de tasa
2. **Robots.txt**: Respetar directrices de robots.txt
3. **Legal Compliance**: Cumplir con regulaciones locales
4. **Data Protection**: Anonimizar datos sensibles
5. **Authentication**: Usar credenciales seguras

### Configuración de Seguridad

```python
# security_config.yaml
security:
  rate_limiting:
    max_requests_per_minute: 60
    max_requests_per_hour: 1000
    
  robots_compliance:
    respect_robots_txt: true
    user_agent: "MultiAgentBot/1.0 (+https://ejemplo.com/bot)"
    
  data_protection:
    anonymize_sensitive: true
    encrypt_storage: true
    retention_days: 30
    
  legal_compliance:
    terms_of_service_url: "https://ejemplo.com/terms"
    contact_email: "legal@ejemplo.com"
```

## 📈 Optimización

### Performance Tips

1. **Browser Caching**: Usar perfiles de navegador persistentes
2. **Connection Pooling**: Reutilizar conexiones
3. **Selective Loading**: Cargar solo recursos necesarios
4. **Parallel Execution**: Múltiples navegadores en paralelo
5. **Resource Management**: Limpiar recursos después de uso

### Configuración de Optimización

```python
# optimization.yaml
optimization:
  browser_pool:
    max_browsers: 5
    idle_timeout: 300
    
  caching:
    enable_cache: true
    cache_ttl: 3600
    
  parallel:
    max_concurrent: 3
    queue_size: 100
    
  resource_limits:
    max_memory: "512MB"
    max_cpu: "50%"
    timeout: 300
```

## 🎯 Casos de Uso Empresariales

### 1. Competitive Intelligence

```python
# Monitoreo de competencia
competitive_intel = {
    "targets": ["competidor1.com", "competidor2.com"],
    "data_points": [
        "product_catalog",
        "pricing_strategies", 
        "marketing_campaigns",
        "customer_reviews"
    ],
    "schedule": "daily",
    "alerts": {
        "price_changes": True,
        "new_products": True,
        "promotional_campaigns": True
    }
}
```

### 2. Lead Generation

```python
# Generación de leads automatizada
lead_generation = {
    "sources": ["directory1.com", "directory2.com"],
    "criterias": {
        "industry": "technology",
        "location": "spain",
        "employee_count": "10-50"
    },
    "data_fields": [
        "company_name",
        "contact_person",
        "email",
        "phone",
        "website"
    ],
    "validation": {
        "email_verification": True,
        "website_verification": True
    }
}
```

### 3. Market Research

```python
# Investigación de mercado automatizada
market_research = {
    "categories": ["fintech", "healthtech", "edtech"],
    "metrics": [
        "market_size",
        "growth_rate",
        "key_players",
        "investment_trends"
    ],
    "sources": [
        "industry_reports",
        "news_articles",
        "funding_announcements"
    ],
    "analysis": {
        "sentiment_analysis": True,
        "trend_detection": True,
        "competitor_mapping": True
    }
}
```

---

## 📞 Soporte

**Documentación API**: http://localhost:8000/docs#/Web%20Scraping  
**Issues**: GitHub Issues en el repositorio del proyecto  
**Logs**: http://localhost:8000/logs/web-scraping  
**Métricas**: http://localhost:3001 (Grafana dashboard)

---

**🚀 Estado**: **HERRAMIENTA REAL OPERATIVA**  
**📅 Última Actualización**: 2025-11-04  
**✅ Producción**: **READY FOR ENTERPRISE WEB SCRAPING**
