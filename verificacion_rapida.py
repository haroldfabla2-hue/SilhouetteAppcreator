#!/usr/bin/env python3
"""
🔍 Script de Verificación Rápida del Sistema
==========================================

Diagnóstico rápido del ecosistema MCP Server Superior

Autor: MiniMax Agent
Fecha: 2025-11-04
"""

import sys
import os
import subprocess
from pathlib import Path

# Colores para output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_banner():
    print(f"""
{Colors.BLUE}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════════════════╗
║                     🔍 VERIFICACIÓN RÁPIDA DEL SISTEMA                      ║
║                    MCP Server Superior v3.1.0 - Optimizado                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Colors.END}
""")

def check_files():
    """Verificar archivos principales"""
    print(f"{Colors.BLUE}📁 Verificando estructura del proyecto...{Colors.END}")
    
    files_to_check = [
        ("main.py", "Punto de entrada principal"),
        ("verificar_sistema.py", "Script de verificación completa"),
        ("health_check.py", "Sistema de monitoreo"),
        (".env.template", "Template de configuración"),
        ("docker-compose.yml", "Configuración Docker"),
        ("README.md", "Documentación principal")
    ]
    
    all_good = True
    for file_path, description in files_to_check:
        if Path(file_path).exists():
            print(f"  {Colors.GREEN}✅ {description}{Colors.END}")
        else:
            print(f"  {Colors.RED}❌ {description} - FALTA{Colors.END}")
            all_good = False
    
    return all_good

def check_env_config():
    """Verificar configuración básica"""
    print(f"\n{Colors.BLUE}🔑 Verificando configuración...{Colors.END}")
    
    env_file = Path(".env")
    if not env_file.exists():
        print(f"  {Colors.YELLOW}⚠️  Archivo .env no encontrado (normal en primer uso){Colors.END}")
        template_file = Path(".env.template")
        if template_file.exists():
            print(f"  {Colors.GREEN}✅ Template .env.template disponible{Colors.END}")
            return True
        else:
            print(f"  {Colors.RED}❌ Template .env.template faltante{Colors.END}")
            return False
    else:
        print(f"  {Colors.GREEN}✅ Archivo .env encontrado{Colors.END}")
        return True

def check_dependencies():
    """Verificar dependencias básicas"""
    print(f"\n{Colors.BLUE}📦 Verificando dependencias críticas...{Colors.END}")
    
    critical_deps = ["fastapi", "uvicorn", "httpx", "pydantic"]
    missing = []
    
    for dep in critical_deps:
        try:
            __import__(dep)
            print(f"  {Colors.GREEN}✅ {dep}{Colors.END}")
        except ImportError:
            print(f"  {Colors.RED}❌ {dep} - NO INSTALADO{Colors.END}")
            missing.append(dep)
    
    if missing:
        print(f"\n  {Colors.YELLOW}💡 Para instalar dependencias:{Colors.END}")
        print(f"     pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Función principal"""
    print_banner()
    
    checks = [
        ("Estructura de archivos", check_files),
        ("Configuración", check_env_config),
        ("Dependencias", check_dependencies)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        try:
            result = check_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"  {Colors.RED}❌ Error en {check_name}: {e}{Colors.END}")
            all_passed = False
    
    # Resultado final
    print(f"\n{Colors.BLUE}{Colors.BOLD}📊 RESULTADO FINAL{Colors.END}")
    print("─" * 50)
    
    if all_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ SISTEMA LISTO PARA USAR{Colors.END}")
        print(f"\n{Colors.BLUE}🚀 Próximos pasos:{Colors.END}")
        print(f"  1. python main.py --verify    (verificación completa)")
        print(f"  2. python main.py             (iniciar sistema)")
        print(f"  3. python health_check.py     (monitoreo avanzado)")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ REQUIERE CONFIGURACIÓN{Colors.END}")
        print(f"\n{Colors.YELLOW}📋 Tareas pendientes:{Colors.END}")
        print(f"  1. Configurar API keys en .env")
        print(f"  2. Instalar dependencias faltantes")
        print(f"  3. Ejecutar verificación completa")
        return 1

if __name__ == "__main__":
    sys.exit(main())