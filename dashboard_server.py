#!/usr/bin/env python3
"""
🌐 Dashboard Web - MCP Server Superior
=====================================

Servidor web para el dashboard de monitoreo en tiempo real

Autor: MiniMax Agent
Fecha: 2025-11-04
Versión: 1.0.0
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path
import threading
import json
from datetime import datetime

# Colores
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_banner():
    """Banner del dashboard"""
    banner = f"""
{Colors.BLUE}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════════════════╗
║                          🌐 DASHBOARD WEB EN TIEMPO REAL                     ║
║                         MCP Server Superior v3.1.0                           ║
║              Monitoreo y Gestión Visual del Ecosistema Multi-Agente          ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Colors.END}

{Colors.GREEN}✅ Métricas en tiempo real{Colors.END}
{Colors.GREEN}✅ Estado de agentes activos{Colors.END}
{Colors.GREEN}✅ Logs del sistema{Colors.END}
{Colors.GREEN}✅ Controles de gestión{Colors.END}
"""
    print(banner)

def check_dashboard_dependencies():
    """Verificar dependencias del dashboard"""
    print(f"{Colors.BLUE}🔍 Verificando dependencias del dashboard...{Colors.END}")
    
    dashboard_path = Path("mcp-dashboard")
    if not dashboard_path.exists():
        print(f"  {Colors.RED}❌ Directorio mcp-dashboard no encontrado{Colors.END}")
        return False
    
    # Verificar package.json
    package_json = dashboard_path / "package.json"
    if not package_json.exists():
        print(f"  {Colors.RED}❌ package.json no encontrado{Colors.END}")
        return False
    
    # Verificar node_modules
    node_modules = dashboard_path / "node_modules"
    if not node_modules.exists():
        print(f"  {Colors.YELLOW}⚠️  node_modules no encontrado. Instalando dependencias...{Colors.END}")
        
        os.chdir(dashboard_path)
        try:
            subprocess.run(["npm", "install"], check=True, capture_output=True)
            print(f"  {Colors.GREEN}✅ Dependencias instaladas{Colors.END}")
        except subprocess.CalledProcessError as e:
            print(f"  {Colors.RED}❌ Error instalando dependencias: {e}{Colors.END}")
            return False
    else:
        print(f"  {Colors.GREEN}✅ Dependencias ya instaladas{Colors.END}")
    
    return True

def start_backend_api():
    """Iniciar API backend para el dashboard"""
    print(f"\n{Colors.BLUE}🚀 Iniciando API backend...{Colors.END}")
    
    backend_path = Path("backend")
    if not backend_path.exists():
        print(f"  {Colors.RED}❌ Directorio backend no encontrado{Colors.END}")
        return None
    
    os.chdir(backend_path)
    
    # Verificar si main.py existe
    main_py = Path("main.py")
    if not main_py.exists():
        print(f"  {Colors.RED}❌ main.py no encontrado en backend{Colors.END}")
        return None
    
    try:
        # Iniciar backend en background
        print(f"  {Colors.GREEN}✅ Iniciando servidor backend en puerto 8000{Colors.END}")
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return process
    except Exception as e:
        print(f"  {Colors.RED}❌ Error iniciando backend: {e}{Colors.END}")
        return None

def start_frontend_dashboard():
    """Iniciar dashboard frontend"""
    print(f"\n{Colors.BLUE}🎨 Iniciando dashboard frontend...{Colors.END}")
    
    dashboard_path = Path("mcp-dashboard")
    os.chdir(dashboard_path)
    
    try:
        # Obtener puerto disponible
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            port = s.getsockname()[1]
        
        print(f"  {Colors.GREEN}✅ Puerto asignado: {port}{Colors.END}")
        
        # Iniciar servidor de desarrollo
        process = subprocess.Popen([
            "npm", "run", "dev", "--", "--port", str(port), "--host", "0.0.0.0"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return process, port
        
    except Exception as e:
        print(f"  {Colors.RED}❌ Error iniciando frontend: {e}{Colors.END}")
        return None, None

def generate_sample_data():
    """Generar datos de ejemplo para el dashboard"""
    print(f"\n{Colors.BLUE}📊 Generando datos de ejemplo...{Colors.END}")
    
    data_dir = Path("dashboard_data")
    data_dir.mkdir(exist_ok=True)
    
    # Datos de ejemplo de agentes
    agents_data = {
        "agents": [
            {"name": "Git Operations", "status": "active", "tasks": 127, "uptime": "2h 15m"},
            {"name": "Web Scraping", "status": "active", "tasks": 89, "uptime": "2h 15m"},
            {"name": "Database Ops", "status": "active", "tasks": 203, "uptime": "2h 15m"},
            {"name": "File Processing", "status": "idle", "tasks": 45, "uptime": "2h 15m"},
            {"name": "Search Engine", "status": "active", "tasks": 156, "uptime": "2h 15m"},
            {"name": "Python Executor", "status": "active", "tasks": 78, "uptime": "2h 15m"}
        ],
        "system_metrics": {
            "cpu": 45.2,
            "memory": 62.8,
            "active_agents": 5,
            "total_requests": 1247,
            "timestamp": datetime.now().isoformat()
        },
        "logs": [
            {"timestamp": "14:32:15", "level": "info", "message": "Agent Git Operations completed task #127", "source": "Git Agent"},
            {"timestamp": "14:32:10", "level": "info", "message": "Database connection established", "source": "Database Agent"},
            {"timestamp": "14:32:05", "level": "warning", "message": "High memory usage detected (78%)", "source": "System Monitor"},
            {"timestamp": "14:32:00", "level": "info", "message": "Web scraping task completed successfully", "source": "Web Agent"}
        ]
    }
    
    with open(data_dir / "sample_data.json", "w") as f:
        json.dump(agents_data, f, indent=2)
    
    print(f"  {Colors.GREEN}✅ Datos de ejemplo generados{Colors.END}")

def main():
    """Función principal"""
    try:
        print_banner()
        
        # Verificar dependencias
        if not check_dashboard_dependencies():
            print(f"\n{Colors.RED}❌ Error verificando dependencias del dashboard{Colors.END}")
            return 1
        
        # Generar datos de ejemplo
        generate_sample_data()
        
        # Iniciar backend API
        backend_process = start_backend_api()
        if not backend_process:
            print(f"\n{Colors.YELLOW}⚠️  Continuando solo con frontend (sin backend){Colors.END}")
        
        # Dar tiempo al backend para inicializar
        if backend_process:
            print(f"\n{Colors.YELLOW}⏳ Esperando inicialización del backend...{Colors.END}")
            time.sleep(3)
        
        # Iniciar frontend
        frontend_process, port = start_frontend_dashboard()
        if not frontend_process:
            print(f"\n{Colors.RED}❌ Error iniciando dashboard frontend{Colors.END}")
            if backend_process:
                backend_process.terminate()
            return 1
        
        # Mostrar información de acceso
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 DASHBOARD INICIADO EXITOSAMENTE!{Colors.END}")
        print(f"\n{Colors.CYAN}📱 ACCESOS DISPONIBLES:{Colors.END}")
        print(f"   {Colors.WHITE}Dashboard Web:     {Colors.BLUE}http://localhost:{port}{Colors.END}")
        print(f"   {Colors.WHITE}Backend API:       {Colors.BLUE}http://localhost:8000{Colors.END}")
        print(f"   {Colors.WHITE}API Documentation: {Colors.BLUE}http://localhost:8000/docs{Colors.END}")
        
        print(f"\n{Colors.YELLOW}💡 Características del Dashboard:{Colors.END}")
        print(f"   • Métricas en tiempo real del sistema")
        print(f"   • Estado de todos los agentes activos")
        print(f"   • Logs del sistema con colores por nivel")
        print(f"   • Gráficos de rendimiento y uso de recursos")
        print(f"   • Controles de gestión y monitoreo")
        
        print(f"\n{Colors.PURPLE}⏹️  Presiona Ctrl+C para detener el dashboard{Colors.END}")
        
        # Manejar cierre graceful
        def signal_handler(sig, frame):
            print(f"\n\n{Colors.YELLOW}🔄 Deteniendo dashboard...{Colors.END}")
            if frontend_process:
                frontend_process.terminate()
            if backend_process:
                backend_process.terminate()
            print(f"{Colors.GREEN}✅ Dashboard detenido correctamente{Colors.END}")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Mantener el script corriendo
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            signal_handler(None, None)
            
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error inesperado: {e}{Colors.END}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())