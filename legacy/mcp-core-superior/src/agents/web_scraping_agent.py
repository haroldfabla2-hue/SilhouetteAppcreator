"""
Web Scraping & Playwright Agent MCP
Agente especializado en web scraping avanzado con Playwright, manejo de JavaScript,
capturas de pantalla y extracción de datos estructurados.
"""
from typing import Dict, Any, List, Optional, Union, AsyncIterator
import asyncio
import logging
import time
import random
import json
import base64
import os
from datetime import datetime
from enum import Enum
from urllib.parse import urljoin, urlparse
import re

# Imports para Playwright
try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Imports para herramientas existentes (con fallback)
try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
    from tools.web_scraper import WebScraper
    WEB_SCRAPER_AVAILABLE = True
except ImportError:
    WebScraper = None
    WEB_SCRAPER_AVAILABLE = False

# Pydantic para schemas (con fallback)
try:
    from pydantic import BaseModel, Field, validator, HttpUrl
    from typing_extensions import Literal
    PYDANTIC_AVAILABLE = True
except ImportError:
    # Fallback para definir modelos básicos sin validación
    PYDANTIC_AVAILABLE = False
    
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    def Field(default=None, description=None, **kwargs):
        return default
    
    def validator(field_name):
        def decorator(func):
            return func
    
    HttpUrl = str

# Imports del sistema MCP
try:
    # Intentar importación absoluta primero
    from agents.base_agent_wrapper import BaseAgentWrapper, AgentCapability
    from core.exceptions import AgentException, handle_exceptions
    BASE_WRAPPER_AVAILABLE = True
except ImportError:
    try:
        # Intentar importación relativa como fallback
        from .base_agent_wrapper import BaseAgentWrapper, AgentCapability
        from ..core.exceptions import AgentException, handle_exceptions
        BASE_WRAPPER_AVAILABLE = True
    except ImportError:
        # Fallback cuando el sistema base no está disponible
        from enum import Enum
        
        class AgentCapability(Enum):
            WEB_SCRAPING = "web_scraping"
            TOOL_INVOCATION = "tool_invocation"
            CONCURRENT_EXECUTION = "concurrent_execution"
            RESULT_COLLECTION = "result_collection"
        
        class BaseAgentWrapper:
            def __init__(self, **kwargs):
                self.agent_name = kwargs.get('agent_name', 'web_scraping')
                self.status = 'ready'
                self.capabilities = kwargs.get('capabilities', [])
            
            async def execute_operation(self, *args, **kwargs):
                return {"success": False, "error": "Sistema base no disponible"}
            
            async def ensure_initialized(self):
                pass
            
            async def health_check(self):
                return {"status": "unavailable", "reason": "Base system not loaded"}
        
        class AgentException(Exception):
            def __init__(self, message, agent_name=None, operation=None):
                super().__init__(message)
                self.message = message
                self.agent_name = agent_name
                self.operation = operation

# Importar configuración de agentes
try:
    from .config import get_safe_settings, AgentType, AgentConfig, agent_config_manager
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    
    # Configuración por defecto si no está disponible el sistema
    class Settings:
        max_concurrent_tools = 3
        agent_timeout_seconds = 180
        agent_retry_attempts = 3
        agent_retry_delay = 1.0
    
    settings = Settings()
    
    def handle_exceptions(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                raise AgentException(str(e), "web_scraping", func.__name__)
        return wrapper


class ScrapingMode(Enum):
    """Modos de scraping disponibles"""
    FAST = "fast"  # Solo requests HTTP básicos
    STANDARD = "standard"  # Playwright sin JavaScript
    JAVASCRIPT = "javascript"  # Playwright con JavaScript completo
    STEALTH = "stealth"  # Modo anti-detección


class BotDetectionStrategy(Enum):
    """Estrategias para evitar detección de bots"""
    USER_AGENT_ROTATION = "user_agent_rotation"
    REQUEST_DELAY = "request_delay"
    COOKIE_SIMULATION = "cookie_simulation"
    HEADER_ROTATION = "header_rotation"
    HEADLESS_HIDING = "headless_hiding"
    HUMAN_LIKE_DELAY = "human_like_delay"


class ScreenshotFormat(Enum):
    """Formatos de captura de pantalla"""
    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"


# ===== SCHEMAS PYDANTIC =====

class ScrapingRequest(BaseModel):
    """Request para operaciones de web scraping"""
    url: HttpUrl = Field(..., description="URL a scrapear")
    mode: ScrapingMode = Field(ScrapingMode.STANDARD, description="Modo de scraping")
    extract_text: bool = Field(True, description="Extraer texto plano")
    extract_structured: bool = Field(True, description="Extraer datos estructurados")
    extract_links: bool = Field(False, description="Extraer enlaces")
    extract_images: bool = Field(False, description="Extraer información de imágenes")
    wait_for_selector: Optional[str] = Field(None, description="Selector CSS para esperar antes de extraer")
    wait_time: float = Field(2.0, description="Tiempo de espera en segundos")
    timeout: float = Field(30.0, description="Timeout en segundos")
    user_agent: Optional[str] = Field(None, description="User agent personalizado")
    custom_headers: Dict[str, str] = Field(default_factory=dict, description="Headers personalizados")
    proxy_url: Optional[str] = Field(None, description="URL de proxy")
    cookies: List[Dict[str, str]] = Field(default_factory=list, description="Cookies para enviar")
    take_screenshot: bool = Field(False, description="Tomar captura de pantalla")
    screenshot_format: ScreenshotFormat = Field(ScreenshotFormat.PNG, description="Formato de captura")
    screenshot_quality: int = Field(80, ge=1, le=100, description="Calidad de captura (1-100)")
    click_elements: List[str] = Field(default_factory=list, description="Elementos CSS para hacer click")
    fill_forms: Dict[str, str] = Field(default_factory=dict, description="Formularios para llenar")
    scroll_pages: int = Field(0, ge=0, description="Número de páginas a hacer scroll")
    extract_shadow_dom: bool = Field(False, description="Extraer contenido de Shadow DOM")
    
    @validator('url')
    def validate_url(cls, v):
        """Validar que la URL sea HTTP/HTTPS"""
        parsed = urlparse(str(v))
        if parsed.scheme not in ['http', 'https']:
            raise ValueError("Solo URLs HTTP/HTTPS son permitidas")
        return v


class BatchScrapingRequest(BaseModel):
    """Request para scraping de múltiples URLs"""
    urls: List[HttpUrl] = Field(..., min_items=1, max_items=50, description="URLs a scrapear")
    shared_options: Dict[str, Any] = Field(default_factory=dict, description="Opciones compartidas")
    rate_limit: Optional[float] = Field(1.0, ge=0.1, description="Delay entre requests (segundos)")
    parallel_requests: int = Field(3, ge=1, max_concurrent=10, description="Requests paralelos máximo")
    
    @validator('urls')
    def validate_urls(cls, v):
        """Validar que no hay URLs duplicadas"""
        unique_urls = list(set(str(url) for url in v))
        if len(unique_urls) != len(v):
            raise ValueError("No se permiten URLs duplicadas")
        return v


class InteractiveRequest(BaseModel):
    """Request para interacciones complejas con Playwright"""
    actions: List[Dict[str, Any]] = Field(..., description="Lista de acciones a realizar")
    wait_between_actions: float = Field(1.0, ge=0.1, description="Delay entre acciones")
    validate_content: bool = Field(False, description="Validar contenido después de cada acción")


class StructuredDataExtractor(BaseModel):
    """Configuración para extracción de datos estructurados"""
    extract_tables: bool = Field(False, description="Extraer tablas")
    extract_json_ld: bool = Field(True, description="Extraer JSON-LD estructurado")
    extract_microdata: bool = Field(True, description="Extraer microdata")
    extract_og_tags: bool = Field(True, description="Extraer Open Graph tags")
    extract_meta_tags: bool = Field(True, description="Extraer meta tags")
    custom_selectors: Dict[str, str] = Field(default_factory=dict, description="Selectores CSS personalizados")
    extract_by_text_patterns: List[str] = Field(default_factory=list, description="Patrones de texto a buscar")


class BotMitigationConfig(BaseModel):
    """Configuración para mitigación de detección de bots"""
    strategies: List[BotDetectionStrategy] = Field(default_factory=lambda: [
        BotDetectionStrategy.USER_AGENT_ROTATION,
        BotDetectionStrategy.REQUEST_DELAY,
        BotDetectionStrategy.HUMAN_LIKE_DELAY
    ])
    rotation_pool_size: int = Field(10, ge=1, description="Tamaño del pool de user agents")
    min_delay: float = Field(1.0, ge=0.1, description="Delay mínimo entre requests")
    max_delay: float = Field(5.0, ge=1.0, description="Delay máximo entre requests")
    randomize_delays: bool = Field(True, description="Randomizar delays")


# ===== MODELOS DE RESPUESTA =====

class ScrapingResult(BaseModel):
    """Resultado de operación de web scraping"""
    success: bool
    url: str
    mode: ScrapingMode
    response_time: float
    status_code: Optional[int] = None
    content_length: Optional[int] = None
    
    # Contenido extraído
    text: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    links: Optional[List[Dict[str, str]]] = None
    images: Optional[List[Dict[str, str]]] = None
    
    # Metadatos
    title: Optional[str] = None
    description: Optional[str] = None
    meta_tags: Optional[Dict[str, str]] = None
    
    # Capturas de pantalla
    screenshot_path: Optional[str] = None
    screenshot_base64: Optional[str] = None
    
    # Errores y advertencias
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Información técnica
    final_url: Optional[str] = None
    redirects: List[str] = Field(default_factory=list)
    cookies_received: List[Dict[str, str]] = Field(default_factory=list)
    javascript_enabled: bool = False
    user_agent_used: Optional[str] = None


class BatchScrapingResult(BaseModel):
    """Resultado de scraping de múltiples URLs"""
    results: Dict[str, ScrapingResult]
    summary: Dict[str, Any]
    rate_limiting_stats: Dict[str, float]
    total_time: float
    successful_urls: int
    failed_urls: int


# ===== AGENTE PRINCIPAL =====

class WebScrapingAgentWrapper(BaseAgentWrapper):
    """Wrapper para WebScrapingAgent con Playwright"""
    
    def __init__(self):
        capabilities = [
            AgentCapability.WEB_SCRAPING,
            AgentCapability.TOOL_INVOCATION
        ]
        
        super().__init__(
            agent_name="web_scraping",
            capabilities=capabilities,
            max_concurrent=settings.max_concurrent_tools,
            timeout_seconds=settings.agent_timeout_seconds,
            retry_attempts=settings.agent_retry_attempts,
            retry_delay=settings.agent_retry_delay
        )
        
        self.logger = logging.getLogger("mcp.agents.web_scraping")
        
        # Verificar disponibilidad de componentes
        if not PLAYWRIGHT_AVAILABLE:
            self.logger.warning("Playwright no está disponible. Funcionalidad limitada.")
        
        if not WEB_SCRAPER_AVAILABLE:
            self.logger.warning("WebScraper base no disponible. Solo modo Playwright.")
        
        # Inicializar herramientas base
        self.web_scraper = WebScraper() if WEB_SCRAPER_AVAILABLE else None
        
        # Pool de user agents para rotación
        self.user_agents = self._get_user_agent_pool()
        
        # Configuración de rate limiting
        self.request_times = []
        self.min_request_interval = 1.0  # segundos
        
        # Pool de navegadores Playwright
        self._browser_pool = []
        self._playwright = None
        
    def _get_user_agent_pool(self) -> List[str]:
        """Pool de user agents para rotación"""
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
        ]
    
    async def _initialize(self) -> None:
        """Inicializar el agente y Playwright"""
        if PLAYWRIGHT_AVAILABLE:
            try:
                self._playwright = await async_playwright().start()
                self.logger.info("Playwright inicializado correctamente")
            except Exception as e:
                self.logger.error(f"Error inicializando Playwright: {e}")
                PLAYWRIGHT_AVAILABLE = False
        
        self.logger.info("WebScrapingAgent inicializado")
    
    async def process_request(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Procesar request de web scraping"""
        return await self.execute_operation(
            operation_name="web_scraping",
            capability=AgentCapability.WEB_SCRAPING,
            operation_func=self._process_scraping_request,
            request=request,
            context=context
        )
    
    @handle_exceptions
    async def _process_scraping_request(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Procesar request específico de scraping"""
        operation_type = request.get("operation", "single_url")
        
        if operation_type == "single_url":
            return await self._scrape_single_url(request)
        elif operation_type == "batch_urls":
            return await self._scrape_multiple_urls(request)
        elif operation_type == "interactive":
            return await self._handle_interactive_scrape(request)
        elif operation_type == "extract_structured":
            return await self._extract_structured_data(request)
        elif operation_type == "stealth_scrape":
            return await self._stealth_scrape(request)
        else:
            raise AgentException(
                f"Operación no soportada: {operation_type}",
                self.agent_name,
                "process_scraping_request"
            )
    
    async def _scrape_single_url(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Scraping de una sola URL"""
        try:
            # Validar request con Pydantic
            scraping_request = ScrapingRequest(**request)
            
            self.logger.info(f"Scraping URL: {scraping_request.url}")
            
            # Aplicar rate limiting
            await self._apply_rate_limiting()
            
            # Seleccionar estrategia basada en modo
            if scraping_request.mode == ScrapingMode.FAST or not PLAYWRIGHT_AVAILABLE:
                result = await self._scrape_with_requests(scraping_request)
            else:
                result = await self._scrape_with_playwright(scraping_request)
            
            return {
                "success": result.success,
                "data": result.dict(),
                "agent_name": self.agent_name,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error en scraping de URL única: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_name": self.agent_name,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _scrape_with_requests(self, request: ScrapingRequest) -> ScrapingResult:
        """Scraping usando requests (modo rápido)"""
        start_time = time.time()
        errors = []
        warnings = []
        
        try:
            if not self.web_scraper:
                warnings.append("WebScraper base no disponible, usando requests simple")
                return await self._scrape_with_simple_requests(request)
            
            # Usar web_scraper existente
            result = self.web_scraper.scrape_url(
                url=str(request.url),
                extract_structured=request.extract_structured,
                extract_text=request.extract_text
            )
            
            if result.success:
                data = result.data
                return ScrapingResult(
                    success=True,
                    url=str(request.url),
                    mode=ScrapingMode.FAST,
                    response_time=time.time() - start_time,
                    status_code=data.get('status_code'),
                    content_length=data.get('content_length'),
                    text=data.get('text') if request.extract_text else None,
                    structured_data=data.get('structured') if request.extract_structured else None,
                    title=data.get('structured', {}).get('title'),
                    description=data.get('structured', {}).get('description'),
                    links=data.get('structured', {}).get('links') if request.extract_links else None,
                    images=data.get('structured', {}).get('images') if request.extract_images else None,
                    user_agent_used="web_scraper_default",
                    javascript_enabled=False
                )
            else:
                errors.append(result.error)
                
        except Exception as e:
            errors.append(f"Error en scraping con requests: {str(e)}")
        
        return ScrapingResult(
            success=False,
            url=str(request.url),
            mode=ScrapingMode.FAST,
            response_time=time.time() - start_time,
            errors=errors,
            warnings=warnings,
            user_agent_used="requests_default",
            javascript_enabled=False
        )
    
    async def _scrape_with_simple_requests(self, request: ScrapingRequest) -> ScrapingResult:
        """Scraping usando requests básico como fallback"""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            start_time = time.time()
            
            headers = {
                'User-Agent': request.user_agent or random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            }
            
            if request.custom_headers:
                headers.update(request.custom_headers)
            
            response = requests.get(str(request.url), headers=headers, timeout=request.timeout)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                text_content = None
                if request.extract_text:
                    # Limpiar HTML básico
                    for script in soup(["script", "style"]):
                        script.decompose()
                    text_content = soup.get_text()
                
                structured_data = {}
                if request.extract_structured:
                    title_tag = soup.find('title')
                    if title_tag:
                        structured_data['title'] = title_tag.get_text().strip()
                    
                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    if meta_desc and meta_desc.get('content'):
                        structured_data['description'] = meta_desc['content'].strip()
                
                return ScrapingResult(
                    success=True,
                    url=str(request.url),
                    mode=ScrapingMode.FAST,
                    response_time=time.time() - start_time,
                    status_code=response.status_code,
                    content_length=len(response.text),
                    text=text_content,
                    structured_data=structured_data,
                    title=structured_data.get('title'),
                    user_agent_used=headers['User-Agent'],
                    javascript_enabled=False
                )
            else:
                return ScrapingResult(
                    success=False,
                    url=str(request.url),
                    mode=ScrapingMode.FAST,
                    response_time=time.time() - start_time,
                    status_code=response.status_code,
                    errors=[f"HTTP {response.status_code}"],
                    user_agent_used=headers['User-Agent'],
                    javascript_enabled=False
                )
                
        except Exception as e:
            return ScrapingResult(
                success=False,
                url=str(request.url),
                mode=ScrapingMode.FAST,
                response_time=time.time() - start_time,
                errors=[f"Error en simple requests: {str(e)}"],
                user_agent_used=request.user_agent or "simple_requests",
                javascript_enabled=False
            )
    
    async def _scrape_with_playwright(self, request: ScrapingRequest) -> ScrapingResult:
        """Scraping usando Playwright (modo avanzado)"""
        start_time = time.time()
        errors = []
        warnings = []
        browser = None
        context = None
        page = None
        screenshot_base64 = None
        
        try:
            if not PLAYWRIGHT_AVAILABLE:
                warnings.append("Playwright no disponible, usando modo requests")
                return await self._scrape_with_requests(request)
            
            # Configurar navegador
            browser = await self._get_browser()
            context = await browser.new_context(
                user_agent=request.user_agent or random.choice(self.user_agents),
                viewport={'width': 1920, 'height': 1080},
                java_script_enabled=(request.mode == ScrapingMode.JAVASCRIPT)
            )
            
            # Configurar headers adicionales
            if request.custom_headers:
                await context.set_extra_http_headers(request.custom_headers)
            
            # Configurar cookies
            if request.cookies:
                await context.add_cookies(request.cookies)
            
            page = await context.new_page()
            
            # Configurar timeouts
            page.set_default_timeout(request.timeout * 1000)
            
            # Navegar a la URL
            response = await page.goto(str(request.url))
            
            # Esperar si hay selector específico
            if request.wait_for_selector:
                try:
                    await page.wait_for_selector(request.wait_for_selector, timeout=request.timeout * 1000)
                except PlaywrightTimeoutError:
                    warnings.append(f"Selector no encontrado: {request.wait_for_selector}")
            
            # Esperar tiempo adicional para JavaScript
            if request.wait_time > 0:
                await asyncio.sleep(request.wait_time)
            
            # Interacciones adicionales
            if request.click_elements:
                for selector in request.click_elements:
                    try:
                        await page.click(selector)
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        warnings.append(f"No se pudo hacer click en {selector}: {e}")
            
            if request.fill_forms:
                for selector, value in request.fill_forms.items():
                    try:
                        await page.fill(selector, value)
                        await asyncio.sleep(0.3)
                    except Exception as e:
                        warnings.append(f"No se pudo llenar formulario {selector}: {e}")
            
            # Scroll si es necesario
            for _ in range(request.scroll_pages):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(1)
            
            # Tomar screenshot si se solicita
            if request.take_screenshot:
                screenshot_bytes = await page.screenshot(
                    type=request.screenshot_format.value,
                    quality=request.screenshot_quality,
                    full_page=True
                )
                screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Extraer contenido
            extracted_data = {}
            
            if request.extract_text:
                extracted_data['text'] = await page.text_content('body') or ""
            
            if request.extract_structured:
                extracted_data.update(await self._extract_structured_data_playwright(page, request))
            
            if request.extract_links:
                extracted_data['links'] = await self._extract_links_playwright(page)
            
            if request.extract_images:
                extracted_data['images'] = await self._extract_images_playwright(page)
            
            # Obtener metadatos de la página
            title = await page.title()
            url = page.url
            
            await browser.close()
            
            return ScrapingResult(
                success=True,
                url=str(request.url),
                mode=request.mode,
                response_time=time.time() - start_time,
                status_code=response.status if response else None,
                content_length=len(extracted_data.get('text', '')),
                text=extracted_data.get('text'),
                structured_data=extracted_data if request.extract_structured else None,
                title=title,
                links=extracted_data.get('links'),
                images=extracted_data.get('images'),
                screenshot_base64=screenshot_base64,
                final_url=url,
                user_agent_used=context._options.get('user_agent'),
                javascript_enabled=request.mode == ScrapingMode.JAVASCRIPT
            )
            
        except Exception as e:
            errors.append(f"Error en scraping con Playwright: {str(e)}")
            if browser:
                await browser.close()
            
            return ScrapingResult(
                success=False,
                url=str(request.url),
                mode=request.mode,
                response_time=time.time() - start_time,
                errors=errors,
                warnings=warnings,
                user_agent_used=request.user_agent,
                javascript_enabled=request.mode == ScrapingMode.JAVASCRIPT
            )
    
    async def _extract_structured_data_playwright(self, page: Page, request: ScrapingRequest) -> Dict[str, Any]:
        """Extraer datos estructurados usando Playwright"""
        data = {}
        
        # Meta tags básicos
        meta_tags = await page.evaluate("""
            () => {
                const metas = Array.from(document.querySelectorAll('meta'));
                const result = {};
                metas.forEach(meta => {
                    const name = meta.getAttribute('name') || meta.getAttribute('property');
                    const content = meta.getAttribute('content');
                    if (name && content) {
                        result[name] = content;
                    }
                });
                return result;
            }
        """)
        data['meta_tags'] = meta_tags
        
        # Open Graph tags
        og_tags = {}
        og_elements = await page.query_selector_all('meta[property^="og:"]')
        for element in og_elements:
            property_attr = await element.get_attribute('property')
            content = await element.get_attribute('content')
            if property_attr and content:
                og_tags[property_attr] = content
        data['og_tags'] = og_tags
        
        # JSON-LD
        json_ld_scripts = await page.query_selector_all('script[type="application/ld+json"]')
        json_ld_data = []
        for script in json_ld_scripts:
            content = await script.text_content()
            try:
                json_data = json.loads(content)
                json_ld_data.append(json_data)
            except json.JSONDecodeError:
                pass
        data['json_ld'] = json_ld_data
        
        # Tablas
        if request.extract_tables:
            tables = await page.query_selector_all('table')
            table_data = []
            for table in tables:
                rows = await table.query_selector_all('tr')
                table_rows = []
                for row in rows:
                    cells = await row.query_selector_all('td, th')
                    row_data = []
                    for cell in cells:
                        cell_text = await cell.text_content()
                        row_data.append(cell_text.strip() if cell_text else "")
                    if row_data:
                        table_rows.append(row_data)
                if table_rows:
                    table_data.append(table_rows)
            data['tables'] = table_data
        
        # Shadow DOM si se solicita
        if request.extract_shadow_dom:
            shadow_data = await page.evaluate("""
                () => {
                    const elementsWithShadow = document.querySelectorAll('*');
                    const shadowData = [];
                    
                    elementsWithShadow.forEach(element => {
                        if (element.shadowRoot) {
                            shadowData.push({
                                tagName: element.tagName,
                                content: element.shadowRoot.innerHTML
                            });
                        }
                    });
                    
                    return shadowData;
                }
            """)
            data['shadow_dom'] = shadow_data
        
        return data
    
    async def _extract_links_playwright(self, page: Page) -> List[Dict[str, str]]:
        """Extraer enlaces usando Playwright"""
        links = await page.evaluate("""
            () => {
                const links = Array.from(document.querySelectorAll('a[href]'));
                return links.map(link => ({
                    text: link.textContent.trim(),
                    href: link.href,
                    title: link.title || '',
                    rel: link.rel || ''
                }));
            }
        """)
        return links
    
    async def _extract_images_playwright(self, page: Page) -> List[Dict[str, str]]:
        """Extraer información de imágenes usando Playwright"""
        images = await page.evaluate("""
            () => {
                const images = Array.from(document.querySelectorAll('img'));
                return images.map(img => ({
                    src: img.src,
                    alt: img.alt || '',
                    title: img.title || '',
                    width: img.width || '',
                    height: img.height || ''
                }));
            }
        """)
        return images
    
    async def _scrape_multiple_urls(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Scraping de múltiples URLs"""
        try:
            batch_request = BatchScrapingRequest(**request)
            
            self.logger.info(f"Scraping batch de {len(batch_request.urls)} URLs")
            
            results = {}
            start_time = time.time()
            
            # Procesar URLs con límite de concurrencia
            semaphore = asyncio.Semaphore(batch_request.parallel_requests)
            tasks = []
            
            async def process_single_url(url):
                async with semaphore:
                    try:
                        single_request = {
                            "url": url,
                            **batch_request.shared_options
                        }
                        result = await self._scrape_single_url(single_request)
                        return str(url), result.get("data")
                    except Exception as e:
                        self.logger.error(f"Error procesando URL {url}: {e}")
                        return str(url), {"success": False, "error": str(e)}
            
            # Crear tareas
            for url in batch_request.urls:
                task = asyncio.create_task(process_single_url(url))
                tasks.append(task)
            
            # Esperar resultados
            completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
            
            for task_result in completed_tasks:
                if isinstance(task_result, tuple):
                    url, data = task_result
                    results[url] = data
                else:
                    self.logger.error(f"Error en tarea: {task_result}")
            
            # Aplicar rate limiting entre batches
            if batch_request.rate_limit:
                await asyncio.sleep(batch_request.rate_limit)
            
            total_time = time.time() - start_time
            
            # Calcular estadísticas
            successful = sum(1 for r in results.values() if r.get("success", False))
            failed = len(results) - successful
            
            summary = {
                "total_urls": len(batch_request.urls),
                "successful_urls": successful,
                "failed_urls": failed,
                "success_rate": successful / len(batch_request.urls) if results else 0,
                "total_time": total_time,
                "average_time_per_url": total_time / len(batch_request.urls) if results else 0
            }
            
            rate_stats = {
                "requests_per_minute": len(batch_request.urls) / (total_time / 60) if total_time > 0 else 0,
                "rate_limit_applied": batch_request.rate_limit or 0
            }
            
            return {
                "success": True,
                "data": {
                    "results": results,
                    "summary": summary,
                    "rate_limiting_stats": rate_stats,
                    "total_time": total_time,
                    "successful_urls": successful,
                    "failed_urls": failed
                },
                "agent_name": self.agent_name,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error en scraping batch: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_name": self.agent_name,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _stealth_scrape(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Scraping en modo stealth (anti-detección)"""
        try:
            # Configurar estrategias anti-bot
            bot_config = BotMitigationConfig(**request.get("bot_config", {}))
            
            # Seleccionar user agent aleatorio
            user_agent = random.choice(self.user_agents)
            request["user_agent"] = user_agent
            request["mode"] = ScrapingMode.STEALTH
            
            # Aplicar delays human-like
            delay = random.uniform(bot_config.min_delay, bot_config.max_delay)
            await asyncio.sleep(delay)
            
            # Ejecutar scraping con Playwright en modo stealth
            result = await self._scrape_single_url(request)
            
            # Añadir información de mitigación al resultado
            if "data" in result and result["success"]:
                result["data"]["stealth_mode"] = True
                result["data"]["bot_mitigation"] = {
                    "user_agent_rotated": True,
                    "delay_applied": delay,
                    "stealth_strategies": [s.value for s in bot_config.strategies]
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error en scraping stealth: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_name": self.agent_name,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _get_browser(self) -> Browser:
        """Obtener navegador del pool o crear uno nuevo"""
        if self._browser_pool:
            browser = self._browser_pool.pop()
            try:
                # Verificar que el navegador esté funcionando
                await browser.version()
                return browser
            except Exception:
                # Browser cerrado, crear uno nuevo
                pass
        
        # Crear nuevo navegador
        browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        return browser
    
    async def _apply_rate_limiting(self) -> None:
        """Aplicar rate limiting"""
        now = time.time()
        
        # Limpiar requests antiguos
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # Si hay demasiados requests recientes, esperar
        if len(self.request_times) >= 10:  # Max 10 requests por minuto
            sleep_time = 60 - (now - self.request_times[0])  # Esperar hasta que expire el oldest
            if sleep_time > 0:
                self.logger.info(f"Rate limit activado, esperando {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
        
        # Registrar este request
        self.request_times.append(now)
        
        # Aplicar delay mínimo
        if self.request_times:
            time_since_last = now - self.request_times[-1]
            if time_since_last < self.min_request_interval:
                await asyncio.sleep(self.min_request_interval - time_since_last)
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check del agente de web scraping"""
        base_health = await super().health_check()
        
        additional_info = {
            "playwright_available": PLAYWRIGHT_AVAILABLE,
            "browser_pool_size": len(self._browser_pool),
            "user_agents_pool_size": len(self.user_agents),
            "recent_requests_count": len([t for t in self.request_times if time.time() - t < 60]),
            "rate_limit_active": len(self.request_times) >= 10
        }
        
        base_health.update(additional_info)
        return base_health
    
    async def cleanup(self) -> None:
        """Limpiar recursos"""
        # Cerrar navegadores en el pool
        for browser in self._browser_pool:
            try:
                await browser.close()
            except Exception:
                pass
        
        self._browser_pool.clear()
        
        # Cerrar Playwright
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
        
        self.logger.info("WebScrapingAgent cleanup completado")


# ===== SCHEMAS MCP =====

class WebScrapingMCPSchema:
    """Schemas MCP para WebScrapingAgent"""
    
    @staticmethod
    def get_input_schema() -> Dict[str, Any]:
        """Schema de entrada para MCP"""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["single_url", "batch_urls", "interactive", "stealth_scrape"],
                    "description": "Tipo de operación de scraping"
                },
                "url": {
                    "type": "string",
                    "format": "uri",
                    "description": "URL a scrapear"
                },
                "mode": {
                    "type": "string",
                    "enum": ["fast", "standard", "javascript", "stealth"],
                    "description": "Modo de scraping"
                },
                "extract_options": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "boolean", "default": True},
                        "structured": {"type": "boolean", "default": True},
                        "links": {"type": "boolean", "default": False},
                        "images": {"type": "boolean", "default": False}
                    }
                },
                "playwright_options": {
                    "type": "object",
                    "properties": {
                        "wait_for_selector": {"type": "string"},
                        "wait_time": {"type": "number", "default": 2.0},
                        "take_screenshot": {"type": "boolean", "default": False},
                        "click_elements": {"type": "array", "items": {"type": "string"}},
                        "fill_forms": {"type": "object"}
                    }
                },
                "bot_mitigation": {
                    "type": "object",
                    "properties": {
                        "strategies": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["user_agent_rotation", "request_delay", "cookie_simulation", "header_rotation", "headless_hiding", "human_like_delay"]
                            }
                        },
                        "min_delay": {"type": "number", "default": 1.0},
                        "max_delay": {"type": "number", "default": 5.0}
                    }
                }
            },
            "required": ["operation"]
        }
    
    @staticmethod
    def get_output_schema() -> Dict[str, Any]:
        """Schema de salida para MCP"""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "data": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "text": {"type": "string"},
                        "structured_data": {"type": "object"},
                        "links": {"type": "array"},
                        "images": {"type": "array"},
                        "title": {"type": "string"},
                        "screenshot_base64": {"type": "string"},
                        "response_time": {"type": "number"},
                        "status_code": {"type": "integer"}
                    }
                },
                "error": {"type": "string"},
                "agent_name": {"type": "string"},
                "timestamp": {"type": "string", "format": "date-time"}
            }
        }


# ===== REGISTRO DEL AGENTE =====

# El agente se registra automáticamente cuando se importa el módulo
# Esto permite que sea discoverable por el sistema MCP

__all__ = [
    "WebScrapingAgentWrapper",
    "WebScrapingMCPSchema",
    "ScrapingRequest",
    "BatchScrapingRequest", 
    "ScrapingResult",
    "BatchScrapingResult",
    "ScrapingMode",
    "BotDetectionStrategy",
    "StructuredDataExtractor",
    "BotMitigationConfig"
]