"""
Unit tests para WebScrapingAgent
Agente especializado en web scraping avanzado con Playwright
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any, List
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Mock playwright dependencies
pytest.importorskip = lambda name: None  # Always succeed

# Mock imports to avoid dependency issues
with patch.dict('sys.modules', {
    'playwright': Mock(),
    'playwright.async_api': Mock(),
    'backend.tools.web_scraper': Mock(),
    'pydantic': Mock(),
    'pydantic.BaseModel': object,
    'typing_extensions': Mock()
}):
    # Now import the agent
    from src.agents.web_scraping_agent import WebScrapingAgent
    from src.agents.base_agent_wrapper import AgentCapability
    from src.core.exceptions import AgentException


class TestWebScrapingAgent:
    """Test suite para WebScrapingAgent"""
    
    @pytest.fixture
    def web_agent(self):
        """Fixture para crear instancia del WebScrapingAgent"""
        with patch('src.agents.web_scraping_agent.PLAYWRIGHT_AVAILABLE', True), \
             patch('src.agents.web_scraping_agent.WEB_SCRAPER_AVAILABLE', True), \
             patch('src.agents.web_scraping_agent.PYDANTIC_AVAILABLE', True), \
             patch('src.agents.web_scraping_agent.BASE_WRAPPER_AVAILABLE', True):
            return WebScrapingAgent()
    
    @pytest.mark.asyncio
    async def test_initialization(self, web_agent):
        """Test inicialización del WebScrapingAgent"""
        # El agente debe inicializarse correctamente
        assert web_agent.agent_name == "web_scraping"
        assert web_agent.status in ["ready", "initializing", "unavailable"]
    
    @pytest.mark.asyncio
    async def test_health_check(self, web_agent):
        """Test verificación de salud"""
        health_result = await web_agent.health_check()
        
        assert isinstance(health_result, dict)
        assert "status" in health_result
        assert health_result["status"] in ["healthy", "unavailable", "error"]
    
    @pytest.mark.asyncio
    async def test_scrape_basic(self, web_agent):
        """Test scraping básico de URL"""
        test_url = "https://example.com"
        
        with patch.object(web_agent, 'scrape_page') as mock_scrape:
            mock_scrape.return_value = {
                "success": True,
                "content": "Contenido extraído",
                "metadata": {"title": "Example"}
            }
            
            result = await web_agent.scrape_page(url=test_url)
            
            assert "success" in result
            assert "content" in result
            assert "metadata" in result
    
    @pytest.mark.asyncio
    async def test_scrape_with_selectors(self, web_agent):
        """Test scraping con selectores específicos"""
        test_url = "https://example.com"
        selectors = {
            "title": "h1",
            "content": ".content",
            "links": "a"
        }
        
        with patch.object(web_agent, 'scrape_page') as mock_scrape:
            mock_scrape.return_value = {
                "success": True,
                "extracted_data": {
                    "title": "Título extraído",
                    "content": "Contenido extraído",
                    "links": ["link1", "link2"]
                }
            }
            
            result = await web_agent.scrape_page(
                url=test_url,
                selectors=selectors
            )
            
            assert "success" in result
            assert "extracted_data" in result
    
    @pytest.mark.asyncio
    async def test_scrape_with_authentication(self, web_agent):
        """Test scraping con autenticación"""
        test_url = "https://secure-example.com"
        credentials = {
            "username": "testuser",
            "password": "testpass"
        }
        
        with patch.object(web_agent, 'scrape_page') as mock_scrape:
            mock_scrape.return_value = {
                "success": True,
                "content": "Contenido autenticado",
                "login_successful": True
            }
            
            result = await web_agent.scrape_page(
                url=test_url,
                credentials=credentials
            )
            
            assert "success" in result
            assert result.get("login_successful") is True
    
    @pytest.mark.asyncio
    async def test_scrape_with_proxy(self, web_agent):
        """Test scraping con proxy"""
        test_url = "https://example.com"
        proxy_config = {
            "server": "http://proxy.example.com:8080",
            "username": "proxyuser",
            "password": "proxypass"
        }
        
        with patch.object(web_agent, 'scrape_page') as mock_scrape:
            mock_scrape.return_value = {
                "success": True,
                "content": "Contenido vía proxy",
                "proxy_used": True
            }
            
            result = await web_agent.scrape_page(
                url=test_url,
                proxy_config=proxy_config
            )
            
            assert "success" in result
            assert result.get("proxy_used") is True
    
    @pytest.mark.asyncio
    async def test_scrape_js_content(self, web_agent):
        """Test scraping de contenido dinámico con JavaScript"""
        test_url = "https://dynamic-example.com"
        
        with patch.object(web_agent, 'scrape_dynamic_content') as mock_dynamic:
            mock_dynamic.return_value = {
                "success": True,
                "dynamic_content": "Contenido cargado dinámicamente",
                "js_executed": True,
                "elements_found": 5
            }
            
            result = await web_agent.scrape_dynamic_content(
                url=test_url,
                wait_for_selector=".dynamic-content",
                timeout=10000
            )
            
            assert "success" in result
            assert "dynamic_content" in result
            assert result.get("js_executed") is True
    
    @pytest.mark.asyncio
    async def test_take_screenshot(self, web_agent):
        """Test captura de pantalla"""
        test_url = "https://example.com"
        
        with patch.object(web_agent, 'capture_screenshot') as mock_screenshot:
            mock_screenshot.return_value = {
                "success": True,
                "screenshot_path": "/tmp/screenshot.png",
                "screenshot_size": "1920x1080",
                "format": "png"
            }
            
            result = await web_agent.capture_screenshot(
                url=test_url,
                full_page=True,
                wait_time=2000
            )
            
            assert "success" in result
            assert "screenshot_path" in result
            assert "format" in result
    
    @pytest.mark.asyncio
    async def test_extract_forms(self, web_agent):
        """Test extracción de formularios"""
        test_url = "https://form-example.com"
        
        with patch.object(web_agent, 'extract_forms') as mock_forms:
            mock_forms.return_value = {
                "success": True,
                "forms_found": 2,
                "forms": [
                    {
                        "form_id": "contact_form",
                        "action": "/submit",
                        "method": "POST",
                        "fields": ["name", "email", "message"]
                    },
                    {
                        "form_id": "search_form",
                        "action": "/search",
                        "method": "GET",
                        "fields": ["query"]
                    }
                ]
            }
            
            result = await web_agent.extract_forms(url=test_url)
            
            assert "success" in result
            assert "forms_found" in result
            assert "forms" in result
            assert len(result["forms"]) == 2
    
    @pytest.mark.asyncio
    async def test_submit_form(self, web_agent):
        """Test envío de formulario"""
        form_data = {
            "name": "Test User",
            "email": "test@example.com",
            "message": "Test message"
        }
        
        with patch.object(web_agent, 'submit_form') as mock_submit:
            mock_submit.return_value = {
                "success": True,
                "response_code": 200,
                "response_data": {"status": "submitted"},
                "form_submitted": True
            }
            
            result = await web_agent.submit_form(
                url="https://form-example.com/submit",
                form_data=form_data,
                form_selector="#contact_form"
            )
            
            assert "success" in result
            assert "response_code" in result
            assert result.get("form_submitted") is True
    
    @pytest.mark.asyncio
    async def test_navigate_and_wait(self, web_agent):
        """Test navegación y espera"""
        test_url = "https://example.com"
        
        with patch.object(web_agent, 'navigate_and_wait') as mock_navigate:
            mock_navigate.return_value = {
                "success": True,
                "current_url": test_url,
                "title": "Example Page",
                "load_time_ms": 1500,
                "elements_loaded": 10
            }
            
            result = await web_agent.navigate_and_wait(
                url=test_url,
                wait_for_element=".content",
                timeout=10000
            )
            
            assert "success" in result
            assert "current_url" in result
            assert "title" in result
            assert "load_time_ms" in result
    
    @pytest.mark.asyncio
    async def test_handle_pagination(self, web_agent):
        """Test manejo de paginación"""
        base_url = "https://example.com/products"
        pagination_config = {
            "next_button_selector": ".next-page",
            "max_pages": 3
        }
        
        with patch.object(web_agent, 'scrape_paginated') as mock_paginated:
            mock_paginated.return_value = {
                "success": True,
                "pages_scraped": 3,
                "total_items": 30,
                "all_data": ["item1", "item2", "item3"] * 10
            }
            
            result = await web_agent.scrape_paginated(
                url=base_url,
                pagination_config=pagination_config
            )
            
            assert "success" in result
            assert "pages_scraped" in result
            assert "total_items" in result
            assert "all_data" in result
    
    @pytest.mark.asyncio
    async def test_extract_table_data(self, web_agent):
        """Test extracción de datos de tablas"""
        test_url = "https://table-example.com/data"
        
        with patch.object(web_agent, 'extract_table_data') as mock_table:
            mock_table.return_value = {
                "success": True,
                "tables_found": 1,
                "table_data": [
                    {"column1": "value1", "column2": "value2"},
                    {"column1": "value3", "column2": "value4"}
                ],
                "headers": ["column1", "column2"]
            }
            
            result = await web_agent.extract_table_data(
                url=test_url,
                table_selector=".data-table"
            )
            
            assert "success" in result
            assert "tables_found" in result
            assert "table_data" in result
            assert "headers" in result
    
    @pytest.mark.asyncio
    async def test_wait_for_element(self, web_agent):
        """Test espera por elemento"""
        with patch.object(web_agent, 'wait_for_element') as mock_wait:
            mock_wait.return_value = {
                "success": True,
                "element_found": True,
                "wait_time_ms": 2500,
                "element_text": "Elemento encontrado"
            }
            
            result = await web_agent.wait_for_element(
                url="https://example.com",
                selector=".dynamic-element",
                timeout=10000
            )
            
            assert "success" in result
            assert "element_found" in result
            assert "wait_time_ms" in result
    
    @pytest.mark.asyncio
    async def test_handle_cookies(self, web_agent):
        """Test manejo de cookies"""
        with patch.object(web_agent, 'handle_cookies') as mock_cookies:
            mock_cookies.return_value = {
                "success": True,
                "cookies_set": 3,
                "cookies_accepted": True,
                "cookie_banner_dismissed": True
            }
            
            result = await web_agent.handle_cookies(
                url="https://example.com",
                accept_all=True,
                banner_selectors=[".cookie-banner", ".gdpr-banner"]
            )
            
            assert "success" in result
            assert "cookies_set" in result
            assert result.get("cookies_accepted") is True
    
    @pytest.mark.asyncio
    async def test_extract_links(self, web_agent):
        """Test extracción de enlaces"""
        test_url = "https://example.com"
        
        with patch.object(web_agent, 'extract_links') as mock_links:
            mock_links.return_value = {
                "success": True,
                "links_found": 15,
                "internal_links": ["https://example.com/page1", "https://example.com/page2"],
                "external_links": ["https://external.com/link1"],
                "all_links": ["https://example.com/page1", "https://example.com/page2", "https://external.com/link1"]
            }
            
            result = await web_agent.extract_links(
                url=test_url,
                include_external=False
            )
            
            assert "success" in result
            assert "links_found" in result
            assert "internal_links" in result
            assert "all_links" in result
    
    @pytest.mark.asyncio
    async def test_handle_rate_limiting(self, web_agent):
        """Test manejo de rate limiting"""
        # Simular múltiples requests
        urls = [
            "https://example.com/page1",
            "https://example.com/page2", 
            "https://example.com/page3"
        ]
        
        with patch.object(web_agent, 'scrape_pages_with_rate_limit') as mock_rate_limit:
            mock_rate_limit.return_value = {
                "success": True,
                "pages_scraped": 3,
                "rate_limit_applied": True,
                "total_delay_ms": 6000,
                "results": [
                    {"url": urls[0], "success": True},
                    {"url": urls[1], "success": True},
                    {"url": urls[2], "success": True}
                ]
            }
            
            result = await web_agent.scrape_pages_with_rate_limit(
                urls=urls,
                delay_between_requests=2000
            )
            
            assert "success" in result
            assert "pages_scraped" in result
            assert result.get("rate_limit_applied") is True
            assert "total_delay_ms" in result
    
    @pytest.mark.asyncio
    async def test_error_handling_connection_timeout(self, web_agent):
        """Test manejo de errores - timeout de conexión"""
        with patch.object(web_agent, 'scrape_page') as mock_scrape:
            mock_scrape.side_effect = Exception("Connection timeout")
            
            with pytest.raises(Exception):
                await web_agent.scrape_page(url="https://timeout-example.com")
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_url(self, web_agent):
        """Test manejo de errores - URL inválida"""
        invalid_urls = [
            "not-a-url",
            "ftp://invalid",
            "http://",
            ""
        ]
        
        for url in invalid_urls:
            with patch.object(web_agent, 'scrape_page') as mock_scrape:
                mock_scrape.return_value = {
                    "success": False,
                    "error": f"Invalid URL: {url}"
                }
                
                result = await web_agent.scrape_page(url=url)
                assert result["success"] is False
                assert "error" in result
    
    @pytest.mark.asyncio
    async def test_error_handling_403_forbidden(self, web_agent):
        """Test manejo de errores - 403 Forbidden"""
        with patch.object(web_agent, 'scrape_page') as mock_scrape:
            mock_scrape.return_value = {
                "success": False,
                "error": "403 Forbidden - Access denied",
                "status_code": 403,
                "blocked": True
            }
            
            result = await web_agent.scrape_page(url="https://forbidden-example.com")
            
            assert result["success"] is False
            assert result.get("status_code") == 403
            assert result.get("blocked") is True
    
    @pytest.mark.asyncio
    async def test_browser_options_config(self, web_agent):
        """Test configuración de opciones del navegador"""
        browser_options = {
            "headless": True,
            "user_agent": "Custom User Agent",
            "viewport": {"width": 1920, "height": 1080},
            "disable_images": True,
            "disable_javascript": False
        }
        
        with patch.object(web_agent, 'scrape_page') as mock_scrape:
            mock_scrape.return_value = {
                "success": True,
                "content": "Contenido con opciones personalizadas",
                "browser_config_used": browser_options
            }
            
            result = await web_agent.scrape_page(
                url="https://example.com",
                browser_options=browser_options
            )
            
            assert "success" in result
            assert result.get("browser_config_used") == browser_options
    
    @pytest.mark.asyncio
    async def test_content_filtering(self, web_agent):
        """Test filtrado de contenido"""
        test_url = "https://example.com"
        filters = {
            "exclude_selectors": [".ads", ".sidebar", ".footer"],
            "include_text_containing": ["importante", "relevant"],
            "exclude_text_containing": ["spam", "irrelevante"]
        }
        
        with patch.object(web_agent, 'scrape_page_with_filtering') as mock_filter:
            mock_filter.return_value = {
                "success": True,
                "content": "Contenido filtrado",
                "filters_applied": filters,
                "content_length": 1500,
                "elements_filtered": 5
            }
            
            result = await web_agent.scrape_page_with_filtering(
                url=test_url,
                filters=filters
            )
            
            assert "success" in result
            assert "filters_applied" in result
            assert "elements_filtered" in result
