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
        print(f"{Colors.BLUE}{Colors.BOLD}🔍 {title}{Colors.END}")
        print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    
    def check_item(self, description: str, success: bool, details: str = "") -> bool:
        """Verificar un item y mostrar resultado"""
        self.total_checks += 1
        
        if success:
            self.passed_checks += 1
            icon = f"{Colors.GREEN}✅{Colors.END}"
            status = f"{Colors.GREEN}PASS{Colors.END}"
        else:
            icon = f"{Colors.RED}❌{Colors.END}"
            status = f"{Colors.RED}FAIL{Colors.END}"
        
        print(f"{icon} {description:<50} [{status}]")
        if details:
            print(f"   {Colors.YELLOW}└─ {details}{Colors.END}")
        
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
                        env_vars[key] = value.strip('\"').strip(\"'\")\n        except Exception as e:\n            self.check_item(\"Lectura de .env\", False, f\"Error: {e}\")\n            return results\n        \n        # Verificar keys críticas\n        critical_keys = {\n            \"OPENROUTER_API_KEY\": \"OpenRouter (MiniMax M2 gratuito)\",\n            \"MINIMAX_MODEL_NAME\": \"Modelo MiniMax M2\"\n        }\n        \n        for key, description in critical_keys.items():\n            value = env_vars.get(key, \"\")\n            is_configured = bool(value and not value.startswith(\"[INSERTAR\") and len(value) > 10)\n            results[key] = self.check_item(f\"{description}\", is_configured,\n                                         \"Configurado\" if is_configured else \"Falta configurar\")\n        \n        # Verificar keys opcionales importantes\n        optional_keys = {\n            \"GOOGLE_MAPS_API_KEY\": \"Google Maps\",\n            \"OPENAI_API_KEY\": \"OpenAI (backup)\",\n            \"MINIMAX_API_KEY\": \"MiniMax directo (backup)\"\n        }\n        \n        for key, description in optional_keys.items():\n            value = env_vars.get(key, \"\")\n            is_configured = bool(value and not value.startswith(\"[INSERTAR\") and len(value) > 10)\n            results[f\"optional_{key}\"] = is_configured\n            status_text = \"Configurado\" if is_configured else \"Opcional (no configurado)\"\n            color = Colors.GREEN if is_configured else Colors.YELLOW\n            print(f\"  {color}{'✓' if is_configured else '⚠'}{Colors.END} {description:<50} [{color}{status_text}{Colors.END}]\")\n        \n        return results\n    \n    def check_connectivity(self) -> Dict[str, bool]:\n        \"\"\"Verificar conectividad a servicios externos\"\"\"\n        self.print_header(\"CONECTIVIDAD A SERVICIOS\")\n        \n        results = {}\n        \n        # Verificar conectividad a internet\n        try:\n            result = subprocess.run([\"ping\", \"-c\", \"1\", \"-W\", \"3\", \"8.8.8.8\"], \n                                  capture_output=True, timeout=10)\n            internet_ok = result.returncode == 0\n            results[\"internet\"] = self.check_item(\"Conectividad a internet\", internet_ok)\n        except subprocess.TimeoutExpired:\n            results[\"internet\"] = self.check_item(\"Conectividad a internet\", False, \"Timeout\")\n        \n        # Verificar servicios específicos\n        services_to_check = [\n            (\"openrouter.ai\", \"OpenRouter API\"),\n            (\"api.openai.com\", \"OpenAI API\"),\n            (\"maps.googleapis.com\", \"Google Maps API\")\n        ]\n        \n        for host, description in services_to_check:\n            try:\n                import socket\n                sock = socket.create_connection((host, 443), timeout=5)\n                sock.close()\n                results[host] = self.check_item(f\"Acceso a {description}\", True)\n            except (socket.error, socket.timeout):\n                results[host] = self.check_item(f\"Acceso a {description}\", False, \"No accesible\")\n        \n        return results\n    \n    def check_project_structure(self) -> Dict[str, bool]:\n        \"\"\"Verificar estructura del proyecto\"\"\"\n        self.print_header(\"ESTRUCTURA DEL PROYECTO\")\n        \n        results = {}\n        \n        # Directorios críticos\n        critical_dirs = [\n            \"backend\",\n            \"frontend\", \n            \"mcp-core-superior\",\n            \"docs\",\n            \"enterprise_testing_suite\"\n        ]\n        \n        for directory in critical_dirs:\n            dir_path = self.workspace_path / directory\n            results[directory] = self.check_item(f\"Directorio {directory}/\", dir_path.exists())\n        \n        # Archivos críticos\n        critical_files = [\n            \"main.py\",\n            \"docker-compose.yml\",\n            \"requirements.txt\",\n            \"README.md\",\n            \"CONFIGURACION_RAPIDA.md\"\n        ]\n        \n        for file_name in critical_files:\n            file_path = self.workspace_path / file_name\n            results[file_name] = self.check_item(f\"Archivo {file_name}\", file_path.exists())\n        \n        return results\n    \n    def run_basic_tests(self) -> Dict[str, bool]:\n        \"\"\"Ejecutar tests básicos\"\"\"\n        self.print_header(\"TESTS BÁSICOS\")\n        \n        results = {}\n        \n        # Test de importaciones del backend\n        backend_test = self.workspace_path / \"backend\" / \"test_imports.py\"\n        if backend_test.exists():\n            try:\n                result = subprocess.run([sys.executable, str(backend_test)], \n                                      capture_output=True, text=True, timeout=30,\n                                      cwd=str(self.workspace_path / \"backend\"))\n                success = result.returncode == 0 and \"✅\" in result.stdout\n                results[\"imports\"] = self.check_item(\"Test de importaciones\", success,\n                                                    \"Exitoso\" if success else \"Falló\")\n            except subprocess.TimeoutExpired:\n                results[\"imports\"] = self.check_item(\"Test de importaciones\", False, \"Timeout\")\n        else:\n            results[\"imports\"] = self.check_item(\"Test de importaciones\", False, \"Archivo no encontrado\")\n        \n        return results\n    \n    def generate_report(self) -> str:\n        \"\"\"Generar reporte final\"\"\"\n        self.print_header(\"REPORTE FINAL\")\n        \n        percentage = (self.passed_checks / self.total_checks * 100) if self.total_checks > 0 else 0\n        \n        if percentage >= 90:\n            status_color = Colors.GREEN\n            status_icon = \"✅\"\n            status_text = \"EXCELENTE\"\n        elif percentage >= 75:\n            status_color = Colors.YELLOW\n            status_icon = \"⚠️\"\n            status_text = \"BUENO\"\n        else:\n            status_color = Colors.RED\n            status_icon = \"❌\"\n            status_text = \"NECESITA ATENCIÓN\"\n        \n        print(f\"\\n{status_color}{Colors.BOLD}{status_icon} ESTADO GENERAL: {status_text}{Colors.END}\")\n        print(f\"{status_color}📊 Verificaciones: {self.passed_checks}/{self.total_checks} ({percentage:.1f}%){Colors.END}\")\n        \n        # Recomendaciones\n        print(f\"\\n{Colors.BLUE}{Colors.BOLD}📋 RECOMENDACIONES:{Colors.END}\")\n        \n        if percentage < 90:\n            print(f\"  {Colors.YELLOW}1. Configurar API keys faltantes en .env{Colors.END}\")\n            print(f\"  {Colors.YELLOW}2. Verificar servicios Docker detenidos{Colors.END}\")\n            print(f\"  {Colors.YELLOW}3. Instalar dependencias faltantes{Colors.END}\")\n        \n        print(f\"\\n{Colors.GREEN}🚀 Para iniciar el sistema:{Colors.END}\")\n        print(f\"  {Colors.BLUE}python main.py --verify{Colors.END} (verificar configuración)\")\n        print(f\"  {Colors.BLUE}python main.py{Colors.END} (modo desarrollo)\")\n        print(f\"  {Colors.BLUE}python main.py --mode production{Colors.END} (modo producción)\")\n        \n        return status_text\n\ndef main():\n    \"\"\"Función principal\"\"\"\n    print(f\"{Colors.BLUE}{Colors.BOLD}\")\n    print(\"=\"*80)\n    print(\"🔍 VERIFICACIÓN COMPLETA DEL SISTEMA MCP SERVER SUPERIOR\")\n    print(\"   Ecosistema Universal con MiniMax M2 Integration\")\n    print(\"=\"*80)\n    print(f\"{Colors.END}\")\n    \n    verifier = SystemVerifier()\n    \n    try:\n        # Ejecutar todas las verificaciones\n        verifier.check_dependencies()\n        verifier.check_project_structure()\n        verifier.check_api_keys()\n        verifier.check_docker_services()\n        verifier.check_connectivity()\n        verifier.run_basic_tests()\n        \n        # Generar reporte final\n        status = verifier.generate_report()\n        \n        # Exit code basado en el resultado\n        return 0 if status in [\"EXCELENTE\", \"BUENO\"] else 1\n        \n    except KeyboardInterrupt:\n        print(f\"\\n{Colors.YELLOW}⏹️  Verificación interrumpida por usuario{Colors.END}\")\n        return 1\n    except Exception as e:\n        print(f\"\\n{Colors.RED}❌ Error durante verificación: {e}{Colors.END}\")\n        return 1\n\nif __name__ == \"__main__\":\n    sys.exit(main())"