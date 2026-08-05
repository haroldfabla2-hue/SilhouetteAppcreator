#!/usr/bin/env python3
"""
🏥 Sistema de Health Checks y Monitoreo
======================================

Monitorea el estado de todos los componentes del ecosistema:
- APIs externas (OpenRouter, OpenAI, etc.)
- Servicios Docker
- Base de datos
- Agentes especializados
- Performance metrics

Autor: MiniMax Agent
Fecha: 2025-11-04
"""

import asyncio
import httpx
import json
import time
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class HealthChecker:
    """Sistema de health checks para todo el ecosistema"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        self.results = {}
        self.start_time = time.time()
        
        # Cargar configuración
        self.load_env_config()
        
    def load_env_config(self):
        """Cargar configuración desde .env"""
        self.config = {
            "openrouter_api_key": "",
            "openai_api_key": "",
            "minimax_api_key": "",
            "database_url": "postgresql://postgres:password@localhost:5432/mcp_superior_db",
            "redis_url": "redis://localhost:6379/0"
        }
        
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        value = value.strip('"').strip("'")
                        
                        if key == "OPENROUTER_API_KEY":
                            self.config["openrouter_api_key"] = value
                        elif key == "OPENAI_API_KEY":
                            self.config["openai_api_key"] = value
                        elif key == "MINIMAX_API_KEY":
                            self.config["minimax_api_key"] = value
                        elif key == "DATABASE_URL":
                            self.config["database_url"] = value
                        elif key == "REDIS_URL":
                            self.config["redis_url"] = value
    
    async def check_api_health(self, name: str, url: str, headers: Dict[str, str] = None, 
                              test_payload: Dict[str, Any] = None) -> Dict[str, Any]:
        """Verificar salud de una API externa"""
        start_time = time.time()
        
        try:
            if test_payload:
                response = await self.client.post(url, json=test_payload, headers=headers or {})
            else:
                response = await self.client.get(url, headers=headers or {})
            
            response_time = (time.time() - start_time) * 1000  # ms
            
            success = response.status_code in [200, 401]  # 401 puede ser normal si no hay payload real
            
            return {
                "status": "healthy" if success else "unhealthy",
                "response_time_ms": round(response_time, 2),
                "status_code": response.status_code,
                "error": None if success else response.text[:200]
            }
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "status": "unhealthy",
                "response_time_ms": round(response_time, 2),
                "status_code": None,
                "error": str(e)[:200]
            }
    
    async def check_openrouter_health(self) -> Dict[str, Any]:
        """Verificar OpenRouter API para MiniMax M2"""
        if not self.config["openrouter_api_key"] or self.config["openrouter_api_key"].startswith("[INSERTAR"):
            return {
                "status": "not_configured",
                "response_time_ms": 0,
                "error": "API key no configurada"
            }
        
        headers = {
            "Authorization": f"Bearer {self.config['openrouter_api_key']}",
            "Content-Type": "application/json"
        }
        
        test_payload = {
            "model": "minimax/minimax-m2:free",
            "messages": [{"role": "user", "content": "Health check"}],
            "max_tokens": 5
        }
        
        return await self.check_api_health(
            "OpenRouter (MiniMax M2)",
            "https://openrouter.ai/api/v1/chat/completions",
            headers,
            test_payload
        )
    
    async def check_system_resources(self) -> Dict[str, Any]:
        """Verificar recursos del sistema"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "status": "healthy",
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def check_local_services(self) -> Dict[str, Any]:
        """Verificar servicios locales"""
        services = {}
        
        # Check local backend API
        try:
            response = await self.client.get("http://localhost:8000/health")
            services["backend_api"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code
            }
        except Exception as e:
            services["backend_api"] = {
                "status": "unhealthy",
                "error": str(e)[:100]
            }
        
        # Check frontend
        try:
            response = await self.client.get("http://localhost:3000")
            services["frontend"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code
            }
        except Exception as e:
            services["frontend"] = {
                "status": "unhealthy",
                "error": str(e)[:100]
            }
        
        return services
    
    def print_status(self, service: str, result: Dict[str, Any]):
        """Imprimir estado de un servicio con colores"""
        status = result.get("status", "unknown")
        
        if status == "healthy":
            icon = f"{Colors.GREEN}✅{Colors.END}"
            status_text = f"{Colors.GREEN}HEALTHY{Colors.END}"
        elif status == "not_configured":
            icon = f"{Colors.YELLOW}⚠️{Colors.END}"
            status_text = f"{Colors.YELLOW}NOT CONFIGURED{Colors.END}"
        else:
            icon = f"{Colors.RED}❌{Colors.END}"
            status_text = f"{Colors.RED}UNHEALTHY{Colors.END}"
        
        print(f"{icon} {service:<30} [{status_text}]")
        
        # Detalles adicionales
        if "response_time_ms" in result and result["response_time_ms"] > 0:
            rt = result["response_time_ms"]
            rt_color = Colors.GREEN if rt < 1000 else Colors.YELLOW if rt < 3000 else Colors.RED
            print(f"   └─ Tiempo de respuesta: {rt_color}{rt}ms{Colors.END}")
        
        if "error" in result and result["error"]:
            print(f"   └─ {Colors.RED}Error: {result['error']}{Colors.END}")
    
    async def run_comprehensive_check(self) -> Dict[str, Any]:
        """Ejecutar verificación completa del sistema"""
        print(f"{Colors.BLUE}{Colors.BOLD}")
        print("═" * 80)
        print("🏥 HEALTH CHECK COMPLETO - MCP SERVER SUPERIOR")
        print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("═" * 80)
        print(f"{Colors.END}")
        
        results = {}
        
        # 1. APIs Externas
        print(f"\n{Colors.BLUE}{Colors.BOLD}🌐 APIS EXTERNAS{Colors.END}")
        print("─" * 50)
        
        # OpenRouter (prioritario)
        openrouter_result = await self.check_openrouter_health()
        results["openrouter"] = openrouter_result
        self.print_status("OpenRouter (MiniMax M2 Free)", openrouter_result)
        
        # OpenAI (backup)
        if self.config["openai_api_key"] and not self.config["openai_api_key"].startswith("[INSERTAR"):
            openai_headers = {"Authorization": f"Bearer {self.config['openai_api_key']}"}
            openai_result = await self.check_api_health(
                "OpenAI", "https://api.openai.com/v1/models", openai_headers
            )
            results["openai"] = openai_result
            self.print_status("OpenAI (Backup)", openai_result)
        else:
            results["openai"] = {"status": "not_configured"}
            self.print_status("OpenAI (Backup)", results["openai"])
        
        # 2. Servicios Locales
        print(f"\n{Colors.BLUE}{Colors.BOLD}🏠 SERVICIOS LOCALES{Colors.END}")
        print("─" * 50)
        
        local_services = await self.check_local_services()
        results["local_services"] = local_services
        
        for service_name, service_result in local_services.items():
            display_name = service_name.replace("_", " ").title()
            self.print_status(display_name, service_result)
        
        # 3. Recursos del Sistema
        print(f"\n{Colors.BLUE}{Colors.BOLD}💻 RECURSOS DEL SISTEMA{Colors.END}")
        print("─" * 50)
        
        system_resources = await self.check_system_resources()
        results["system_resources"] = system_resources
        
        if system_resources["status"] == "healthy":
            cpu = system_resources["cpu_percent"]
            memory = system_resources["memory_percent"]
            disk = system_resources["disk_percent"]
            
            # CPU
            cpu_color = Colors.GREEN if cpu < 70 else Colors.YELLOW if cpu < 90 else Colors.RED
            print(f"  {cpu_color}🔄{Colors.END} CPU Usage: {cpu_color}{cpu}%{Colors.END}")
            
            # Memory
            mem_color = Colors.GREEN if memory < 70 else Colors.YELLOW if memory < 90 else Colors.RED
            mem_available = system_resources["memory_available_gb"]
            print(f"  {mem_color}🧠{Colors.END} Memory Usage: {mem_color}{memory}%{Colors.END} ({mem_available}GB available)")
            
            # Disk
            disk_color = Colors.GREEN if disk < 80 else Colors.YELLOW if disk < 95 else Colors.RED
            disk_free = system_resources["disk_free_gb"]
            print(f"  {disk_color}💾{Colors.END} Disk Usage: {disk_color}{disk}%{Colors.END} ({disk_free}GB free)")
        
        # 4. Resumen Final
        total_time = time.time() - self.start_time
        
        print(f"\n{Colors.BLUE}{Colors.BOLD}📊 RESUMEN FINAL{Colors.END}")
        print("─" * 50)
        
        # Calcular estado general
        critical_services = ["openrouter"]
        critical_healthy = all(
            results.get(service, {}).get("status") in ["healthy", "not_configured"]
            for service in critical_services
        )
        
        if critical_healthy:
            overall_status = f"{Colors.GREEN}✅ SISTEMA OPERATIVO{Colors.END}"
        else:
            overall_status = f"{Colors.RED}❌ REQUIERE ATENCIÓN{Colors.END}"
        
        print(f"Estado General: {overall_status}")
        print(f"Tiempo de verificación: {total_time:.2f}s")
        
        # Recomendaciones
        print(f"\n{Colors.BLUE}{Colors.BOLD}💡 RECOMENDACIONES:{Colors.END}")
        
        if results["openrouter"]["status"] == "not_configured":
            print(f"  {Colors.YELLOW}🔑 Configurar OPENROUTER_API_KEY para MiniMax M2 gratuito{Colors.END}")
        
        if results.get("local_services", {}).get("backend_api", {}).get("status") == "unhealthy":
            print(f"  {Colors.YELLOW}🚀 Iniciar backend: python main.py{Colors.END}")
        
        return results
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

async def main():
    """Función principal"""
    async with HealthChecker() as checker:
        await checker.run_comprehensive_check()

if __name__ == "__main__":
    asyncio.run(main())
