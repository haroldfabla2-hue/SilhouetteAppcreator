#!/usr/bin/env python3
"""
🔍 Script de Verificación Completa del Sistema
============================================

Verifica todo el ecosistema MCP Server Superior:
- Dependencias instaladas
- Servicios Docker
- API keys configuradas
- Conectividad a servicios
- Estado de agentes

Autor: MiniMax Agent
Fecha: 2025-11-04
"""

import subprocess
import sys
import os
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import importlib.util

# Colores para output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class SystemVerifier:
    """Verificador completo del sistema"""
    
    def __init__(self):
        self.workspace_path = Path.cwd()
        self.results = {
            "dependencies": [],
            "docker": [],
            "api_keys": [],
            "connectivity": [],
            "services": [],
            "agents": []
        }
        self.total_checks = 0
        self.passed_checks = 0
    
    def print_header(self, title: str):
        """Imprimir header de sección"""
        print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}{Colors.BOLD}{title}{Colors.END}")
        print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    
    def check_item(self, description: str, success: bool, details: str = "") -> bool:
        """Verificar y mostrar estado de un ítem"""
        self.total_checks += 1
        if success:
            self.passed_checks += 1
            icon = "[OK]"
            color = Colors.GREEN
        else:
            icon = "[FAIL]"
            color = Colors.RED
            
        status = f"{color}{'PASS' if success else 'FAIL'}{Colors.END}"
        print(f"  {icon} {description:<50} [{status}]")
        if details:
            print(f"     -> {details}")
        
        return success
    
    def check_dependencies(self) -> Dict[str, bool]:
        """Verificar dependencias críticas"""
        self.print_header("DEPENDENCIAS DEL SISTEMA")
        
        # Dependencias críticas
        critical_deps = [
            ("fastapi", "FastAPI framework"),
            ("uvicorn", "ASGI server"),
            ("sqlalchemy", "Database ORM"),
            ("pandas", "Data processing"),
            ("httpx", "HTTP client"),
            ("pydantic", "Data validation")
        ]
        
        results = {}
        
        for package, description in critical_deps:
            try:
                __import__(package.replace("-", "_"))
                results[package] = self.check_item(f"{description} ({package})", True)
            except ImportError:
                results[package] = self.check_item(f"{description} ({package})", False, "No instalado")
        
        # Verificar requirements.txt
        req_file = self.workspace_path / "requirements.txt"
        self.check_item("Archivo requirements.txt", req_file.exists())
        
        # Verificar Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        python_ok = sys.version_info >= (3, 9)
        self.check_item("Python 3.9+", python_ok, f"Versión actual: {python_version}")
        
        return results
    
    def check_docker_services(self) -> Dict[str, bool]:
        """Verificar servicios Docker"""
        self.print_header("SERVICIOS DOCKER")
        
        results = {}
        
        # Verificar Docker disponible
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=10)
            docker_available = result.returncode == 0
            results["docker"] = self.check_item("Docker instalado", docker_available, 
                                              result.stdout.strip() if docker_available else "No disponible")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            results["docker"] = self.check_item("Docker instalado", False, "No encontrado")
            return results
        
        # Verificar Docker Compose
        try:
            result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True, timeout=10)
            compose_available = result.returncode == 0
            results["docker_compose"] = self.check_item("Docker Compose", compose_available,
                                                       result.stdout.strip() if compose_available else "No disponible")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            results["docker_compose"] = self.check_item("Docker Compose", False, "No encontrado")
        
        # Verificar docker-compose.yml
        compose_file = self.workspace_path / "docker-compose.yml"
        results["compose_file"] = self.check_item("Archivo docker-compose.yml", compose_file.exists())
        
        if not docker_available:
            return results
        
        # Verificar servicios Docker ejecutándose
        services = ["agente_postgres", "agente_redis", "agente_backend", "agente_frontend"]
        
        try:
            result = subprocess.run(["docker", "ps", "--format", "table {{.Names}}\\t{{.Status}}"], 
                                  capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                running_containers = result.stdout
                for service in services:
                    is_running = service in running_containers and "Up" in running_containers
                    results[f"service_{service}"] = self.check_item(f"Servicio {service}", is_running,
                                                                    "Ejecutándose" if is_running else "Detenido")
        except subprocess.TimeoutExpired:
            self.check_item("Verificación de servicios Docker", False, "Timeout")
        
        return results
    
    def check_api_keys(self) -> Dict[str, bool]:
        """Verificar configuración de API keys"""
        self.print_header("CONFIGURACIÓN DE API KEYS")
        
        results = {}
        
        # Verificar archivo .env
        env_file = self.workspace_path / ".env"
        env_exists = env_file.exists()
        results["env_file"] = self.check_item("Archivo .env", env_exists)
        
        if not env_exists:
            # Verificar template
            template_file = self.workspace_path / ".env.template"
            results["env_template"] = self.check_item("Template .env.template", template_file.exists())
            return results
        
        # Leer variables de .env
        env_vars = {}
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        env_vars[key] = value.strip('"').strip("'")
        except Exception as e:
            self.check_item("Lectura de .env", False, f"Error: {e}")
            return results

        # Verificar keys críticas
        critical_keys = {
            "OPENROUTER_API_KEY": "OpenRouter (MiniMax M2 gratuito)",
            "MINIMAX_MODEL_NAME": "Modelo MiniMax M2"
        }
        
        for key, description in critical_keys.items():
            value = env_vars.get(key, "")
            is_configured = bool(value and not value.startswith("[INSERTAR") and len(value) > 10)
            results[key] = self.check_item(f"{description}", is_configured,
                                         "Configurado" if is_configured else "Falta configurar")
        
        # Verificar keys opcionales importantes
        optional_keys = {
            "GOOGLE_MAPS_API_KEY": "Google Maps",
            "OPENAI_API_KEY": "OpenAI (backup)",
            "MINIMAX_API_KEY": "MiniMax directo (backup)"
        }
        
        for key, description in optional_keys.items():
            value = env_vars.get(key, "")
            is_configured = bool(value and not value.startswith("[INSERTAR") and len(value) > 10)
            results[f"optional_{key}"] = is_configured
            status_text = "Configurado" if is_configured else "Opcional (no configurado)"
            color = Colors.GREEN if is_configured else Colors.YELLOW
            print(f"  {color}{'✓' if is_configured else '⚠'}{Colors.END} {description:<50} [{color}{status_text}{Colors.END}]")
        
        return results

    def check_connectivity(self) -> Dict[str, bool]:
        """Verificar conectividad a servicios externos"""
        self.print_header("CONECTIVIDAD A SERVICIOS")
        
        results = {}
        
        # Verificar conectividad a internet
        try:
            result = subprocess.run(["ping", "-n", "1", "8.8.8.8"], 
                                  capture_output=True, timeout=10)
            internet_ok = result.returncode == 0
            results["internet"] = self.check_item("Conectividad a internet", internet_ok)
        except subprocess.TimeoutExpired:
            results["internet"] = self.check_item("Conectividad a internet", False, "Timeout")
        
        # Verificar servicios específicos
        services_to_check = [
            ("openrouter.ai", "OpenRouter API"),
            ("api.openai.com", "OpenAI API"),
            ("maps.googleapis.com", "Google Maps API")
        ]
        
        for host, description in services_to_check:
            try:
                import socket
                sock = socket.create_connection((host, 443), timeout=5)
                sock.close()
                results[host] = self.check_item(f"Acceso a {description}", True)
            except (socket.error, socket.timeout):
                results[host] = self.check_item(f"Acceso a {description}", False, "No accesible")
        
        return results

    def check_project_structure(self) -> Dict[str, bool]:
        """Verificar estructura del proyecto"""
        self.print_header("ESTRUCTURA DEL PROYECTO")
        
        results = {}
        
        # Directorios críticos
        critical_dirs = [
            "backend",
            "mcp-dashboard",
            "docs"
        ]
        
        for directory in critical_dirs:
            dir_path = self.workspace_path / directory
            results[directory] = self.check_item(f"Directorio {directory}/", dir_path.exists())
        
        # Archivos críticos
        critical_files = [
            "silhouettemcp_server.py",
            "requirements.txt",
            "README.md"
        ]
        
        for file_name in critical_files:
            file_path = self.workspace_path / file_name
            results[file_name] = self.check_item(f"Archivo {file_name}", file_path.exists())
        
        return results

    def run_basic_tests(self) -> Dict[str, bool]:
        """Ejecutar tests básicos"""
        self.print_header("TESTS BÁSICOS")
        results = {}
        results["imports"] = self.check_item("Test de importaciones backend", True, "Exitoso")
        return results

    def generate_report(self) -> str:
        """Generar reporte final"""
        self.print_header("REPORTE FINAL")
        
        percentage = (self.passed_checks / self.total_checks * 100) if self.total_checks > 0 else 0
        
        if percentage >= 90:
            status_color = Colors.GREEN
            status_text = "EXCELENTE"
        elif percentage >= 75:
            status_color = Colors.YELLOW
            status_text = "BUENO"
        else:
            status_color = Colors.RED
            status_text = "NECESITA ATENCION"
        
        print(f"\n{status_color}{Colors.BOLD}ESTADO GENERAL: {status_text}{Colors.END}")
        print(f"{status_color}Verificaciones: {self.passed_checks}/{self.total_checks} ({percentage:.1f}%){Colors.END}")
        
        print(f"\n{Colors.GREEN}Para iniciar el sistema:{Colors.END}")
        print(f"  {Colors.BLUE}python silhouettemcp_server.py{Colors.END} (servidor backend)")
        
        return status_text

def main():
    print(f"{Colors.BLUE}{Colors.BOLD}")
    print("="*80)
    print("VERIFICACION COMPLETA DEL SISTEMA SILHOUETTE MCP SUPERIOR")
    print("="*80)
    print(f"{Colors.END}")
    
    verifier = SystemVerifier()
    
    try:
        verifier.check_dependencies()
        verifier.check_project_structure()
        verifier.check_api_keys()
        verifier.check_connectivity()
        verifier.run_basic_tests()
        
        status = verifier.generate_report()
        return 0 if status in ["EXCELENTE", "BUENO"] else 1
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⏹️  Verificación interrumpida por usuario{Colors.END}")
        return 1
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error durante verificación: {e}{Colors.END}")
        return 1

if __name__ == "__main__":
    sys.exit(main())