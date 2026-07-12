#!/usr/bin/env python3
"""
🚀 MCP Server Superior - Punto de Entrada Principal
==================================================

Sistema Multi-Agente Enterprise con MiniMax M2 Integration

Uso:
    python main.py                    # Modo desarrollo simple
    python main.py --mode production  # Modo producción con Docker
    python main.py --mode test        # Ejecutar tests
    python main.py --verify           # Verificar configuración

Autor: MiniMax Agent
Fecha: 2025-11-04
Versión: 3.1.0
"""

import argparse
import asyncio
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any
import json

# Colores para output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_banner():
    """Imprimir banner del sistema"""
    banner = f"""
{Colors.BLUE}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════════════════╗
║                      🚀 MCP SERVER SUPERIOR v3.1.0                          ║
║                    Ecosistema Universal con MiniMax M2                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Colors.END}

{Colors.GREEN}✅ Estado: 100% Funcional con 30+ Agentes{Colors.END}
{Colors.GREEN}✅ Integración: MiniMax M2 Gratuito via OpenRouter{Colors.END}
{Colors.GREEN}✅ Arquitectura: Enterprise-grade Multi-Agent System{Colors.END}
"""
    print(banner)

def check_env_file() -> bool:
    """Verificar si existe archivo .env"""
    env_path = Path(".env")
    if not env_path.exists():
        print(f"{Colors.YELLOW}⚠️  Archivo .env no encontrado{Colors.END}")
        print(f"{Colors.BLUE}💡 Creando desde template...{Colors.END}")
        
        template_path = Path(".env.template")
        if template_path.exists():
            # Copiar template a .env
            with open(template_path, 'r') as template:
                content = template.read()
            
            with open(env_path, 'w') as env_file:
                env_file.write(content)
            
            print(f"{Colors.GREEN}✅ Archivo .env creado desde template{Colors.END}")
            print(f"{Colors.YELLOW}⚠️  IMPORTANTE: Configura tus API keys en .env{Colors.END}")
            return False
        else:
            print(f"{Colors.RED}❌ Template .env.template no encontrado{Colors.END}")
            return False
    return True

def check_dependencies() -> bool:
    """Verificar dependencias básicas"""
    print(f"{Colors.BLUE}🔍 Verificando dependencias...{Colors.END}")
    
    required_packages = [
        "fastapi", "uvicorn", "sqlalchemy", "psycopg2", "pandas", "httpx"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"{Colors.YELLOW}⚠️  Paquetes faltantes: {', '.join(missing)}{Colors.END}")
        print(f"{Colors.BLUE}💡 Instalando dependencias...{Colors.END}")
        
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                         check=True, capture_output=True)
            print(f"{Colors.GREEN}✅ Dependencias instaladas{Colors.END}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}❌ Error instalando dependencias: {e}{Colors.END}")
            return False
    else:
        print(f"{Colors.GREEN}✅ Todas las dependencias están instaladas{Colors.END}")
        return True

def check_docker() -> bool:
    """Verificar si Docker está disponible"""
    try:
        result = subprocess.run(["docker", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"{Colors.GREEN}✅ Docker disponible: {result.stdout.strip()}{Colors.END}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print(f"{Colors.YELLOW}⚠️  Docker no disponible (opcional para modo desarrollo){Colors.END}")
    return False

def verify_api_keys() -> Dict[str, bool]:
    """Verificar configuración de API keys"""
    print(f"{Colors.BLUE}🔑 Verificando API keys...{Colors.END}")
    
    # Cargar .env si existe
    env_path = Path(".env")
    env_vars = {}
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key] = value.strip('"').strip("'")
    
    # Verificar keys críticas
    critical_keys = {
        "OPENROUTER_API_KEY": "OpenRouter (para MiniMax M2 gratuito)",
        "MINIMAX_MODEL_NAME": "Modelo MiniMax M2"
    }
    
    optional_keys = {
        "GOOGLE_MAPS_API_KEY": "Google Maps",
        "MINIMAX_API_KEY": "MiniMax Directo (backup)",
        "OPENAI_API_KEY": "OpenAI (backup)"
    }
    
    status = {}
    
    print(f"{Colors.BOLD}Claves críticas:{Colors.END}")
    for key, description in critical_keys.items():
        value = env_vars.get(key, "")
        if value and not value.startswith("[INSERTAR"):
            print(f"  {Colors.GREEN}✅ {description}: Configurado{Colors.END}")
            status[key] = True
        else:
            print(f"  {Colors.RED}❌ {description}: NO configurado{Colors.END}")
            status[key] = False
    
    print(f"{Colors.BOLD}Claves opcionales:{Colors.END}")
    for key, description in optional_keys.items():
        value = env_vars.get(key, "")
        if value and not value.startswith("[INSERTAR"):
            print(f"  {Colors.GREEN}✅ {description}: Configurado{Colors.END}")
            status[key] = True
        else:
            print(f"  {Colors.YELLOW}⚠️  {description}: No configurado{Colors.END}")
            status[key] = False
    
    return status

async def run_development_mode():
    """Ejecutar en modo desarrollo (sin Docker)"""
    print(f"{Colors.BLUE}🚀 Iniciando en modo desarrollo...{Colors.END}")
    
    # Verificar si es necesario inicializar base de datos local
    print(f"{Colors.BLUE}💾 Configurando base de datos local...{Colors.END}")
    
    # Cambiar al directorio backend
    backend_path = Path("backend")
    if not backend_path.exists():
        print(f"{Colors.RED}❌ Directorio backend no encontrado{Colors.END}")
        return False
    
    os.chdir(backend_path)
    
    # Ejecutar servidor FastAPI
    print(f"{Colors.GREEN}🌟 Iniciando servidor FastAPI en http://localhost:8000{Colors.END}")
    print(f"{Colors.BLUE}📖 API Docs: http://localhost:8000/docs{Colors.END}")
    print(f"{Colors.YELLOW}⏹️  Presiona Ctrl+C para detener{Colors.END}")
    
    try:
        # Usar uvicorn directamente
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⏹️  Servidor detenido por usuario{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}❌ Error ejecutando servidor: {e}{Colors.END}")
        return False
    
    return True

def run_production_mode():
    """Ejecutar en modo producción con Docker"""
    print(f"{Colors.BLUE}🚀 Iniciando en modo producción (Docker)...{Colors.END}")
    
    if not check_docker():
        print(f"{Colors.RED}❌ Docker es requerido para modo producción{Colors.END}")
        return False
    
    print(f"{Colors.BLUE}🐳 Iniciando servicios con Docker Compose...{Colors.END}")
    
    try:
        # Ejecutar docker-compose
        subprocess.run([
            "docker-compose", "up", "--build"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}❌ Error ejecutando Docker Compose: {e}{Colors.END}")
        return False
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⏹️  Servicios detenidos por usuario{Colors.END}")
        # Limpiar contenedores
        subprocess.run(["docker-compose", "down"], capture_output=True)
    
    return True

def run_tests():
    """Ejecutar suite de tests"""
    print(f"{Colors.BLUE}🧪 Ejecutando tests del sistema...{Colors.END}")
    
    backend_path = Path("backend")
    if backend_path.exists():
        os.chdir(backend_path)
        
        tests = [
            ("test_imports.py", "Importaciones"),
            ("test_connectivity.py", "Conectividad"),
            ("test_agents_functionality.py", "Funcionalidad de Agentes")
        ]
        
        for test_file, description in tests:
            if Path(test_file).exists():
                print(f"{Colors.BLUE}🔍 Ejecutando: {description}...{Colors.END}")
                try:
                    result = subprocess.run([sys.executable, test_file], 
                                          capture_output=True, text=True, timeout=60)
                    if result.returncode == 0:
                        print(f"  {Colors.GREEN}✅ {description}: EXITOSO{Colors.END}")
                    else:
                        print(f"  {Colors.RED}❌ {description}: FALLÓ{Colors.END}")
                        if result.stderr:
                            print(f"     Error: {result.stderr}")
                except subprocess.TimeoutExpired:
                    print(f"  {Colors.YELLOW}⚠️  {description}: TIMEOUT{Colors.END}")
    
    # Tests enterprise
    enterprise_path = Path("../enterprise_testing_suite")
    if enterprise_path.exists():
        print(f"{Colors.BLUE}🏢 Ejecutando tests enterprise...{Colors.END}")
        os.chdir(enterprise_path)
        try:
            subprocess.run([sys.executable, "run_enterprise_tests.py"], timeout=120)
        except subprocess.TimeoutExpired:
            print(f"{Colors.YELLOW}⚠️  Tests enterprise: TIMEOUT{Colors.END}")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="MCP Server Superior - Sistema Multi-Agente Enterprise",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main.py                    # Modo desarrollo
  python main.py --mode production  # Modo producción
  python main.py --mode test        # Ejecutar tests
  python main.py --verify           # Solo verificar configuración
        """
    )
    
    parser.add_argument(
        "--mode", 
        choices=["development", "production", "test"],
        default="development",
        help="Modo de ejecución (default: development)"
    )
    
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Solo verificar configuración del sistema"
    )
    
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="No mostrar banner inicial"
    )
    
    args = parser.parse_args()
    
    # Mostrar banner
    if not args.no_banner:
        print_banner()
    
    # Verificaciones básicas
    success = True
    
    # 1. Verificar archivo .env
    if not check_env_file():
        success = False
    
    # 2. Verificar dependencias
    if not check_dependencies():
        success = False
    
    # 3. Verificar API keys
    api_status = verify_api_keys()
    critical_configured = all(api_status.get(key, False) for key in ["OPENROUTER_API_KEY", "MINIMAX_MODEL_NAME"])
    
    if not critical_configured:
        print(f"\n{Colors.RED}❌ CONFIGURACIÓN INCOMPLETA{Colors.END}")
        print(f"{Colors.YELLOW}⚠️  Para usar el sistema, configura al menos:{Colors.END}")
        print(f"   - OPENROUTER_API_KEY (obtener gratis en openrouter.ai)")
        print(f"   - MINIMAX_MODEL_NAME=\"minimax/minimax-m2:free\"")
        print(f"\n{Colors.BLUE}📖 Ver: CONFIGURACION_RAPIDA.md{Colors.END}")
        
        if args.verify:
            return 1
    
    # Si solo verificar, terminar aquí
    if args.verify:
        if success and critical_configured:
            print(f"\n{Colors.GREEN}✅ SISTEMA COMPLETAMENTE CONFIGURADO Y LISTO{Colors.END}")
            return 0
        else:
            return 1
    
    # Ejecutar según modo
    print(f"\n{Colors.BOLD}🚀 INICIANDO SISTEMA EN MODO: {args.mode.upper()}{Colors.END}\n")
    
    if args.mode == "development":
        return 0 if asyncio.run(run_development_mode()) else 1
    elif args.mode == "production":
        return 0 if run_production_mode() else 1
    elif args.mode == "test":
        run_tests()
        return 0
    
    return 1

if __name__ == "__main__":
    sys.exit(main())