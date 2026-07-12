#!/usr/bin/env python3
"""
Test simplificado del WebScrapingAgent sin dependencias del sistema MCP
"""

import asyncio
import json
import sys
import os
import time
import random
from datetime import datetime
from enum import Enum
from urllib.parse import urlparse

# Mock de dependencias faltantes
class MockLogger:
    def __init__(self, name):
        self.name = name
    
    def info(self, msg): print(f"INFO {self.name}: {msg}")
    def warning(self, msg): print(f"WARN {self.name}: {msg}")
    def error(self, msg): print(f"ERROR {self.name}: {msg}")
    def debug(self, msg): print(f"DEBUG {self.name}: {msg}")

class ScrapingMode(Enum):
    FAST = "fast"
    STANDARD = "standard"
    JAVASCRIPT = "javascript"
    STEALTH = "stealth"

class BotDetectionStrategy(Enum):
    USER_AGENT_ROTATION = "user_agent_rotation"
    REQUEST_DELAY = "request_delay"
    HUMAN_LIKE_DELAY = "human_like_delay"

# Simplified WebScrapingAgent for testing
class SimpleWebScrapingAgent:
    def __init__(self):
        self.agent_name = "web_scraping_simple"
        self.status = "ready"
        self.capabilities = ["web_scraping"]
        
        self.logger = MockLogger("web_scraping_simple")
        
        # User agents pool
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        # Rate limiting
        self.request_times = []
        self.min_request_interval = 1.0
        
        self.logger.info("SimpleWebScrapingAgent inicializado")
    
    async def ensure_initialized(self):
        """Simular inicialización"""
        await asyncio.sleep(0.1)
        self.logger.info("Agente inicializado")
    
    async def process_request(self, request):
        """Procesar request de scraping"""
        try:
            operation = request.get("operation", "single_url")
            
            if operation == "single_url":
                return await self._scrape_single_url(request)
            elif operation == "batch_urls":
                return await self._scrape_multiple_urls(request)
            else:
                return {
                    "success": False,
                    "error": f"Operación no soportada: {operation}",
                    "agent_name": self.agent_name
                }
                
        except Exception as e:
            self.logger.error(f"Error procesando request: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_name": self.agent_name
            }
    
    async def _scrape_single_url(self, request):
        """Scraping de una sola URL usando requests simple"""
        url = request.get("url")
        mode = request.get("mode", "fast")
        
        if not url:
            return {"success": False, "error": "URL requerida"}
        
        self.logger.info(f"Scraping URL: {url}")
        
        # Aplicar rate limiting
        await self._apply_rate_limiting()
        
        start_time = time.time()
        
        try:
            import requests
            from bs4 import BeautifulSoup
            
            # Headers con rotación de user agent
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            }
            
            # Realizar request
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extraer contenido
                text = None
                title = None
                links = []
                
                # Texto
                if request.get("extract_options", {}).get("text", True):
                    for script in soup(["script", "style"]):
                        script.decompose()
                    text = soup.get_text()
                
                # Título
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text().strip()
                
                # Enlaces
                if request.get("extract_options", {}).get("links", False):
                    for link in soup.find_all('a', href=True):
                        links.append({
                            "text": link.get_text().strip(),
                            "href": link['href']
                        })
                
                result = {
                    "success": True,
                    "data": {
                        "url": url,
                        "mode": mode,
                        "response_time": time.time() - start_time,
                        "status_code": response.status_code,
                        "content_length": len(response.text),
                        "title": title,
                        "text": text,
                        "links": links,
                        "user_agent_used": headers['User-Agent'],
                        "javascript_enabled": mode == "javascript"
                    },
                    "agent_name": self.agent_name,
                    "timestamp": datetime.now().isoformat()
                }
                
                self.logger.info(f"Scraping exitoso: {url}")
                return result
                
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "data": {
                        "url": url,
                        "status_code": response.status_code,
                        "response_time": time.time() - start_time
                    },
                    "agent_name": self.agent_name
                }
                
        except Exception as e:
            self.logger.error(f"Error en scraping: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": {
                    "url": url,
                    "response_time": time.time() - start_time
                },
                "agent_name": self.agent_name
            }
    
    async def _scrape_multiple_urls(self, request):
        """Scraping de múltiples URLs"""
        urls = request.get("urls", [])
        shared_options = request.get("shared_options", {})
        parallel_requests = request.get("parallel_requests", 3)
        
        if not urls:
            return {"success": False, "error": "URLs requeridas"}
        
        self.logger.info(f"Batch scraping: {len(urls)} URLs")
        
        start_time = time.time()
        results = {}
        
        # Procesar con límite de concurrencia
        semaphore = asyncio.Semaphore(parallel_requests)
        
        async def process_single_url(url):
            async with semaphore:
                single_request = {
                    "operation": "single_url",
                    "url": url,
                    **shared_options
                }
                return await self._scrape_single_url(single_request)
        
        # Crear tareas
        tasks = [asyncio.create_task(process_single_url(url)) for url in urls]
        
        # Esperar resultados
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(completed_tasks):
            if isinstance(result, dict):
                results[urls[i]] = result
            else:
                results[urls[i]] = {
                    "success": False,
                    "error": str(result)
                }
        
        # Estadísticas
        successful = sum(1 for r in results.values() if r.get("success", False))
        total_time = time.time() - start_time
        
        return {
            "success": True,
            "data": {
                "results": results,
                "summary": {
                    "total_urls": len(urls),
                    "successful_urls": successful,
                    "failed_urls": len(urls) - successful,
                    "success_rate": successful / len(urls),
                    "total_time": total_time
                }
            },
            "agent_name": self.agent_name,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _apply_rate_limiting(self):
        """Aplicar rate limiting básico"""
        now = time.time()
        
        # Limpiar requests antiguos
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # Delay mínimo
        if self.request_times:
            time_since_last = now - self.request_times[-1]
            if time_since_last < self.min_request_interval:
                await asyncio.sleep(self.min_request_interval - time_since_last)
        
        # Registrar request
        self.request_times.append(now)
    
    async def health_check(self):
        """Health check simplificado"""
        return {
            "agent_name": self.agent_name,
            "status": "healthy",
            "is_ready": True,
            "utilization": 0.0,
            "last_activity": datetime.now().isoformat(),
            "user_agents_pool_size": len(self.user_agents),
            "recent_requests": len([t for t in self.request_times if time.time() - t < 60])
        }
    
    async def cleanup(self):
        """Limpieza simplificada"""
        self.logger.info("Cleanup completado")


async def test_simple_scraping():
    """Test básico de scraping"""
    print("🧪 Probando WebScrapingAgent simplificado...")
    
    agent = SimpleWebScrapingAgent()
    await agent.ensure_initialized()
    
    # Test 1: Scraping simple
    print("\n📄 Test 1: Scraping básico")
    request1 = {
        "operation": "single_url",
        "url": "https://httpbin.org/html",
        "mode": "fast",
        "extract_options": {
            "text": True,
            "links": False
        }
    }
    
    result1 = await agent.process_request(request1)
    print(f"✅ Resultado: {result1.get('success', False)}")
    
    if result1.get("success"):
        data = result1["data"]
        print(f"   📊 Status: {data.get('status_code')}")
        print(f"   ⏱️ Tiempo: {data.get('response_time', 0):.2f}s")
        title = data.get('title', 'N/A')
        if title and title != 'N/A':
            print(f"   📄 Título: {title[:50]}...")
        else:
            print(f"   📄 Título: {title}")
    
    # Test 2: Batch scraping
    print("\n📋 Test 2: Batch scraping")
    request2 = {
        "operation": "batch_urls",
        "urls": [
            "https://httpbin.org/json",
            "https://httpbin.org/uuid"
        ],
        "shared_options": {
            "mode": "fast",
            "extract_options": {"text": False}
        },
        "parallel_requests": 2
    }
    
    result2 = await agent.process_request(request2)
    print(f"✅ Resultado: {result2.get('success', False)}")
    
    if result2.get("success"):
        summary = result2["data"]["summary"]
        print(f"   📊 URLs procesadas: {summary['total_urls']}")
        print(f"   ✅ Exitosas: {summary['successful_urls']}")
        print(f"   ⏱️ Tiempo total: {summary['total_time']:.2f}s")
    
    # Test 3: Health check
    print("\n🏥 Test 3: Health check")
    health = await agent.health_check()
    print(f"✅ Health: {health['status']}")
    print(f"   🔧 Pool UAs: {health['user_agents_pool_size']}")
    print(f"   📈 Requests recientes: {health['recent_requests']}")
    
    await agent.cleanup()
    
    return result1.get("success", False) and result2.get("success", False)


if __name__ == "__main__":
    # Configurar event loop para Windows
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    async def main():
        print("🚀 Iniciando test del WebScrapingAgent\n")
        
        try:
            success = await test_simple_scraping()
            
            if success:
                print("\n🎉 ¡Todos los tests pasaron!")
                return 0
            else:
                print("\n⚠️ Algunos tests fallaron")
                return 1
                
        except Exception as e:
            print(f"\n💥 Error crítico: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)