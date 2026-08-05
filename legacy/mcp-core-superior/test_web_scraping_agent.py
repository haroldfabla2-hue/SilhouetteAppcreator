#!/usr/bin/env python3
"""
Script de prueba para WebScrapingAgent
Prueba las funcionalidades básicas del agente de web scraping
"""

import asyncio
import json
import sys
import os

# Añadir el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.web_scraping_agent import (
    WebScrapingAgentWrapper, 
    ScrapingMode, 
    ScrapingRequest,
    BatchScrapingRequest,
    BotDetectionStrategy,
    BotMitigationConfig
)


async def test_basic_scraping():
    """Probar scraping básico de una URL"""
    print("🧪 Probando scraping básico...")
    
    agent = WebScrapingAgentWrapper()
    await agent.ensure_initialized()
    
    # Test con URL simple
    request = {
        "operation": "single_url",
        "url": "https://httpbin.org/html",
        "mode": "fast",
        "extract_options": {
            "text": True,
            "structured": True,
            "links": True
        }
    }
    
    try:
        result = await agent.process_request(request)
        print(f"✅ Scraping básico exitoso: {result.get('success', False)}")
        
        if result.get('success') and result.get('data'):
            data = result['data']
            print(f"   📄 Título: {data.get('title', 'N/A')}")
            print(f"   📊 Status: {data.get('status_code', 'N/A')}")
            print(f"   ⏱️ Tiempo: {data.get('response_time', 0):.2f}s")
            print(f"   🔗 Enlaces encontrados: {len(data.get('links', []))}")
            
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Error en scraping básico: {e}")
        return False
    finally:
        await agent.cleanup()


async def test_playwright_scraping():
    """Probar scraping con Playwright (si está disponible)"""
    print("\n🧪 Probando scraping con Playwright...")
    
    agent = WebScrapingAgentWrapper()
    await agent.ensure_initialized()
    
    # Test con Playwright
    request = {
        "operation": "single_url",
        "url": "https://httpbin.org/forms/post",
        "mode": "javascript",
        "extract_options": {
            "text": True,
            "structured": True,
            "links": True,
            "images": True
        },
        "playwright_options": {
            "wait_time": 3.0,
            "take_screenshot": True,
            "extract_shadow_dom": False
        }
    }
    
    try:
        result = await agent.process_request(request)
        print(f"✅ Scraping con Playwright exitoso: {result.get('success', False)}")
        
        if result.get('success') and result.get('data'):
            data = result['data']
            print(f"   📄 Título: {data.get('title', 'N/A')}")
            print(f"   📱 JavaScript habilitado: {data.get('javascript_enabled', False)}")
            print(f"   📷 Screenshot tomado: {bool(data.get('screenshot_base64'))}")
            print(f"   ⏱️ Tiempo: {data.get('response_time', 0):.2f}s")
            
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Error en scraping con Playwright: {e}")
        return False
    finally:
        await agent.cleanup()


async def test_batch_scraping():
    """Probar scraping de múltiples URLs"""
    print("\n🧪 Probando batch scraping...")
    
    agent = WebScrapingAgentWrapper()
    await agent.ensure_initialized()
    
    # Test con múltiples URLs
    urls = [
        "https://httpbin.org/html",
        "https://httpbin.org/json",
        "https://httpbin.org/uuid"
    ]
    
    request = {
        "operation": "batch_urls",
        "urls": urls,
        "shared_options": {
            "mode": "fast",
            "extract_options": {
                "text": True,
                "structured": True
            }
        },
        "rate_limit": 1.0,
        "parallel_requests": 2
    }
    
    try:
        result = await agent.process_request(request)
        print(f"✅ Batch scraping exitoso: {result.get('success', False)}")
        
        if result.get('success') and result.get('data'):
            data = result['data']
            summary = data.get('summary', {})
            print(f"   📊 URLs procesadas: {summary.get('total_urls', 0)}")
            print(f"   ✅ Exitosas: {summary.get('successful_urls', 0)}")
            print(f"   ❌ Fallidas: {summary.get('failed_urls', 0)}")
            print(f"   📈 Tasa de éxito: {summary.get('success_rate', 0):.2%}")
            print(f"   ⏱️ Tiempo total: {summary.get('total_time', 0):.2f}s")
            
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Error en batch scraping: {e}")
        return False
    finally:
        await agent.cleanup()


async def test_stealth_mode():
    """Probar modo stealth (anti-detección)"""
    print("\n🧪 Probando modo stealth...")
    
    agent = WebScrapingAgentWrapper()
    await agent.ensure_initialized()
    
    # Configuración de mitigación de bots
    bot_config = BotMitigationConfig(
        strategies=[
            BotDetectionStrategy.USER_AGENT_ROTATION,
            BotDetectionStrategy.REQUEST_DELAY,
            BotDetectionStrategy.HUMAN_LIKE_DELAY
        ],
        min_delay=1.0,
        max_delay=3.0
    )
    
    request = {
        "operation": "stealth_scrape",
        "url": "https://httpbin.org/html",
        "bot_config": bot_config.dict()
    }
    
    try:
        result = await agent.process_request(request)
        print(f"✅ Modo stealth exitoso: {result.get('success', False)}")
        
        if result.get('success') and result.get('data'):
            data = result['data']
            stealth_info = data.get('stealth_mode', False)
            mitigation = data.get('bot_mitigation', {})
            print(f"   🥷 Modo stealth activado: {stealth_info}")
            print(f"   🛡️ Estrategias aplicadas: {len(mitigation.get('stealth_strategies', []))}")
            print(f"   ⏱️ Delay aplicado: {mitigation.get('delay_applied', 0):.2f}s")
            
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Error en modo stealth: {e}")
        return False
    finally:
        await agent.cleanup()


async def test_health_check():
    """Probar health check del agente"""
    print("\n🧪 Probando health check...")
    
    agent = WebScrapingAgentWrapper()
    await agent.ensure_initialized()
    
    try:
        health = await agent.health_check()
        print(f"✅ Health check exitoso")
        print(f"   📊 Estado: {health.get('status', 'unknown')}")
        print(f"   🔧 Playwright disponible: {health.get('playwright_available', False)}")
        print(f"   🌐 User agents disponibles: {health.get('user_agents_pool_size', 0)}")
        print(f"   📈 Utilización: {health.get('utilization', 0):.2%}")
        print(f"   ✅ Tasa de éxito: {health.get('success_rate', 0):.2%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en health check: {e}")
        return False
    finally:
        await agent.cleanup()


async def run_all_tests():
    """Ejecutar todos los tests"""
    print("🚀 Iniciando pruebas del WebScrapingAgent\n")
    
    tests = [
        ("Health Check", test_health_check),
        ("Scraping Básico", test_basic_scraping),
        ("Scraping Playwright", test_playwright_scraping),
        ("Batch Scraping", test_batch_scraping),
        ("Modo Stealth", test_stealth_mode),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Error ejecutando {test_name}: {e}")
            results.append((test_name, False))
        
        # Pequeña pausa entre tests
        await asyncio.sleep(1)
    
    # Resumen de resultados
    print(f"\n📋 RESUMEN DE PRUEBAS")
    print(f"{'='*50}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<25} {status}")
    
    print(f"{'='*50}")
    print(f"Resultados: {passed}/{total} tests pasaron ({passed/total:.1%})")
    
    if passed == total:
        print("🎉 ¡Todos los tests pasaron exitosamente!")
        return True
    else:
        print(f"⚠️ {total - passed} tests fallaron")
        return False


if __name__ == "__main__":
    # Configurar event loop para Windows si es necesario
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Ejecutar tests
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Pruebas interrumpidas por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error crítico: {e}")
        sys.exit(1)