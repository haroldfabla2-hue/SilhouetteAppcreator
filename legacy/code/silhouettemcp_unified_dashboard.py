#!/usr/bin/env python3
"""
SilhouetteMCP Unified Dashboard - Vista Completa
Dashboard que muestra el estado de TODOS los sistemas integrados (originales + mejorados)

Autor: MiniMax Agent
Fecha: 2025-11-06
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import psutil

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SilhouetteMCP-Dashboard")

class SystemStatus(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    UNKNOWN = "unknown"

@dataclass
class SystemInfo:
    name: str
    port: int
    status: SystemStatus
    category: str  # original, improved, integration, monitoring
    url: str
    description: str
    uptime: str = "N/A"
    health: str = "N/A"

class SilhouetteMCPUnifiedDashboard:
    """Dashboard unificado para todo el ecosistema SilhouetteMCP"""
    
    def __init__(self):
        self.app = FastAPI(
            title="SilhouetteMCP Unified Dashboard",
            description="Dashboard completo del ecosistema integrado SilhouetteMCP",
            version="2.0.0"
        )
        
        # Configurar CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Definir todos los sistemas
        self.systems = self._define_systems()
        self._setup_routes()
        
    def _define_systems(self) -> List[SystemInfo]:
        """Define todos los sistemas del ecosistema"""
        return [
            # SISTEMAS ORIGINALES
            SystemInfo(
                name="Servidor Unificado Original",
                port=8001,
                status=SystemStatus.UNKNOWN,
                category="original",
                url="http://localhost:8001",
                description="Sistema base unificado SilhouetteMCP - 51 herramientas MCP"
            ),
            SystemInfo(
                name="Arquitectura Jerárquica Original", 
                port=8002,
                status=SystemStatus.UNKNOWN,
                category="original",
                url="http://localhost:8002",
                description="Arquitectura jerárquica con 100+ agentes especializados"
            ),
            
            # SISTEMA DE DIAGNÓSTICO
            SystemInfo(
                name="Sistema de Diagnóstico Robusto",
                port=8007,
                status=SystemStatus.RUNNING,  # Confirmado corriendo
                category="diagnostic",
                url="http://localhost:8007",
                description="Sistema de diagnóstico sin dependencias problemáticas"
            ),
            
            # SISTEMAS MEJORADOS - ARQUITECTURA
            SystemInfo(
                name="Arquitectura Mejorada - Principal",
                port=8010,
                status=SystemStatus.RUNNING,  # Confirmado corriendo
                category="improved_architecture",
                url="http://localhost:8010",
                description="Auto-healing, load balancing, circuit breakers"
            ),
            SystemInfo(
                name="Arquitectura Mejorada - Coordinación",
                port=8011,
                status=SystemStatus.RUNNING,
                category="improved_architecture", 
                url="http://localhost:8011",
                description="Coordinación de 30 agentes mejorados"
            ),
            SystemInfo(
                name="Arquitectura Mejorada - Auto-healing",
                port=8012,
                status=SystemStatus.RUNNING,
                category="improved_architecture",
                url="http://localhost:8012", 
                description="Sistema de recuperación automática"
            ),
            SystemInfo(
                name="Arquitectura Mejorada - Load Balancing",
                port=8013,
                status=SystemStatus.RUNNING,
                category="improved_architecture",
                url="http://localhost:8013",
                description="Balanceador de carga con múltiples estrategias"
            ),
            SystemInfo(
                name="Arquitectura Mejorada - Métricas",
                port=8014,
                status=SystemStatus.RUNNING,
                category="improved_architecture",
                url="http://localhost:8014",
                description="Métricas en tiempo real"
            ),
            
            # SISTEMAS MEJORADOS - SEGURIDAD
            SystemInfo(
                name="Seguridad Mejorada - Principal",
                port=8015,
                status=SystemStatus.RUNNING,  # Confirmado corriendo
                category="improved_security",
                url="http://localhost:8015",
                description="JWT robusto, protección DDoS"
            ),
            SystemInfo(
                name="Seguridad Mejorada - Monitoreo",
                port=8016,
                status=SystemStatus.RUNNING,
                category="improved_security",
                url="http://localhost:8016",
                description="Monitoreo de seguridad en tiempo real"
            ),
            SystemInfo(
                name="Seguridad Mejorada - Identidades",
                port=8017,
                status=SystemStatus.RUNNING,
                category="improved_security",
                url="http://localhost:8017",
                description="Gestión de identidades y permisos"
            ),
            SystemInfo(
                name="Seguridad Mejorada - DDoS Protection",
                port=8018,
                status=SystemStatus.RUNNING,
                category="improved_security",
                url="http://localhost:8018",
                description="Protección multicapa contra DDoS"
            ),
            SystemInfo(
                name="Seguridad Mejorada - Auditoría",
                port=8019,
                status=SystemStatus.RUNNING,
                category="improved_security", 
                url="http://localhost:8019",
                description="Sistema de auditoría y logging"
            ),
            
            # SISTEMAS MEJORADOS - ESCALABILIDAD
            SystemInfo(
                name="Escalabilidad Mejorada - Principal",
                port=8020,
                status=SystemStatus.RUNNING,  # Confirmado corriendo
                category="improved_scalability",
                url="http://localhost:8020",
                description="Auto-scaling hasta 128 workers"
            ),
            SystemInfo(
                name="Escalabilidad Mejorada - Auto-scaler",
                port=8021,
                status=SystemStatus.RUNNING,
                category="improved_scalability",
                url="http://localhost:8021",
                description="Sistema de escalado automático"
            ),
            SystemInfo(
                name="Escalabilidad Mejorada - Load Balancer",
                port=8022,
                status=SystemStatus.RUNNING,
                category="improved_scalability",
                url="http://localhost:8022",
                description="Balanceador de carga avanzado"
            ),
            SystemInfo(
                name="Escalabilidad Mejorada - Resource Manager",
                port=8023,
                status=SystemStatus.RUNNING,
                category="improved_scalability",
                url="http://localhost:8023",
                description="Gestión de recursos del sistema"
            ),
            SystemInfo(
                name="Escalabilidad Mejorada - Performance Monitor",
                port=8024,
                status=SystemStatus.RUNNING,
                category="improved_scalability",
                url="http://localhost:8024",
                description="Monitoreo de performance"
            ),
            
            # SISTEMAS DE INTEGRACIÓN
            SystemInfo(
                name="Orquestador de Integración",
                port=8025,
                status=SystemStatus.STOPPED,
                category="integration",
                url="http://localhost:8025",
                description="Coordinación bidireccional entre sistemas"
            ),
            SystemInfo(
                name="Sistema de Monitoreo Integrado",
                port=8026,
                status=SystemStatus.STOPPED,
                category="monitoring",
                url="http://localhost:8026",
                description="Monitoreo en tiempo real, alertas, predicciones"
            )
        ]
    
    async def check_system_health(self, system: SystemInfo) -> SystemStatus:
        """Verifica el estado de un sistema"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{system.url}/health", timeout=aiohttp.ClientTimeout(total=3)) as response:
                    if response.status == 200:
                        return SystemStatus.RUNNING
                    else:
                        return SystemStatus.ERROR
        except:
            return SystemStatus.STOPPED
    
    async def refresh_systems_status(self):
        """Actualiza el estado de todos los sistemas"""
        logger.info("🔄 Actualizando estado de sistemas...")
        
        # Actualizar sistemas en paralelo
        tasks = [self.check_system_health(system) for system in self.systems]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for system, result in zip(self.systems, results):
            if isinstance(result, Exception):
                system.status = SystemStatus.ERROR
            else:
                system.status = result
                
        logger.info(f"✅ Estado actualizado para {len(self.systems)} sistemas")
    
    def generate_dashboard_html(self) -> str:
        """Genera el HTML del dashboard"""
        # Calcular estadísticas
        total_systems = len(self.systems)
        running_systems = sum(1 for s in self.systems if s.status == SystemStatus.RUNNING)
        stopped_systems = sum(1 for s in self.systems if s.status == SystemStatus.STOPPED)
        error_systems = sum(1 for s in self.systems if s.status == SystemStatus.ERROR)
        
        # Agrupar sistemas por categoría
        categories = {
            "original": {"name": "🗂️ Sistemas Originales", "systems": [], "color": "#3498db"},
            "diagnostic": {"name": "🩺 Sistema de Diagnóstico", "systems": [], "color": "#e74c3c"},
            "improved_architecture": {"name": "🏛️ Arquitectura Mejorada", "systems": [], "color": "#2ecc71"},
            "improved_security": {"name": "🔒 Seguridad Mejorada", "systems": [], "color": "#f39c12"},
            "improved_scalability": {"name": "📈 Escalabilidad Mejorada", "systems": [], "color": "#9b59b6"},
            "integration": {"name": "🔗 Integración", "systems": [], "color": "#1abc9c"},
            "monitoring": {"name": "📊 Monitoreo", "systems": [], "color": "#34495e"}
        }
        
        for system in self.systems:
            if system.category in categories:
                categories[system.category]["systems"].append(system)
        
        # Generar HTML
        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SilhouetteMCP - Dashboard Unificado</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    <style>
        .status-running {{ background-color: #d4edda; border-color: #c3e6cb; }}
        .status-stopped {{ background-color: #f8d7da; border-color: #f5c6cb; }}
        .status-error {{ background-color: #fff3cd; border-color: #ffeaa7; }}
        .status-unknown {{ background-color: #e2e3e5; border-color: #d6d8db; }}
        .pulse {{
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: .5; }}
        }}
    </style>
</head>
<body class="bg-gray-100 font-sans">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="bg-white rounded-lg shadow-lg p-6 mb-6">
            <div class="flex justify-between items-center">
                <div>
                    <h1 class="text-3xl font-bold text-gray-800">🚀 SilhouetteMCP Dashboard Unificado</h1>
                    <p class="text-gray-600 mt-2">Ecosistema completo integrado - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                </div>
                <div class="text-right">
                    <div class="text-2xl font-bold text-green-600">{running_systems}/{total_systems}</div>
                    <div class="text-sm text-gray-500">Sistemas Activos</div>
                </div>
            </div>
        </div>
        
        <!-- Resumen Ejecutivo -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="p-3 rounded-full bg-green-100">
                        <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    </div>
                    <div class="ml-4">
                        <h3 class="text-lg font-semibold text-gray-700">Sistemas Corriendo</h3>
                        <p class="text-2xl font-bold text-green-600">{running_systems}</p>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="p-3 rounded-full bg-red-100">
                        <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    </div>
                    <div class="ml-4">
                        <h3 class="text-lg font-semibold text-gray-700">Sistemas Detenidos</h3>
                        <p class="text-2xl font-bold text-red-600">{stopped_systems}</p>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="p-3 rounded-full bg-yellow-100">
                        <svg class="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                        </svg>
                    </div>
                    <div class="ml-4">
                        <h3 class="text-lg font-semibold text-gray-700">Con Errores</h3>
                        <p class="text-2xl font-bold text-yellow-600">{error_systems}</p>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="p-3 rounded-full bg-blue-100">
                        <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                        </svg>
                    </div>
                    <div class="ml-4">
                        <h3 class="text-lg font-semibold text-gray-700">Total Sistemas</h3>
                        <p class="text-2xl font-bold text-blue-600">{total_systems}</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Sistemas por Categoría -->
        <div class="space-y-6">"""
        
        for category_key, category_info in categories.items():
            if category_info["systems"]:
                html += f"""
            <div class="bg-white rounded-lg shadow-lg">
                <div class="p-6 border-b border-gray-200" style="border-left: 4px solid {category_info['color']}">
                    <h2 class="text-xl font-semibold text-gray-800">{category_info['name']}</h2>
                    <p class="text-sm text-gray-600 mt-1">{len(category_info['systems'])} sistemas</p>
                </div>
                <div class="p-6">
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">"""
                
                for system in category_info["systems"]:
                    status_class = f"status-{system.status.value}"
                    status_text = system.status.value.upper().replace("_", " ")
                    status_icon = {
                        "RUNNING": "🟢",
                        "STOPPED": "🔴", 
                        "ERROR": "🟡",
                        "UNKNOWN": "⚪"
                    }.get(status_text, "⚪")
                    
                    html += f"""
                        <div class="border rounded-lg p-4 {status_class}">
                            <div class="flex justify-between items-start mb-2">
                                <h3 class="font-semibold text-gray-800 text-sm">{system.name}</h3>
                                <span class="text-xs px-2 py-1 rounded-full bg-gray-200">{status_icon} {status_text}</span>
                            </div>
                            <p class="text-xs text-gray-600 mb-3">{system.description}</p>
                            <div class="flex justify-between items-center text-xs text-gray-500">
                                <span>Puerto: {system.port}</span>
                                <span class="pulse" x-show="refreshing">🔄</span>
                            </div>
                            <div class="mt-2">
                                <a href="{system.url}/docs" target="_blank" class="text-blue-600 hover:text-blue-800 text-xs">📋 API Docs</a>
                            </div>
                        </div>"""
                
                html += """
                    </div>
                </div>
            </div>"""
        
        html += """
        </div>
        
        <!-- Footer -->
        <div class="mt-8 text-center text-gray-500 text-sm">
            <p>SilhouetteMCP Ecosystem Dashboard - Actualizado cada 30 segundos</p>
            <p class="mt-2">Desarrollado por MiniMax Agent | 2025-11-06</p>
        </div>
    </div>
    
    <script>
        // Auto-refresh cada 30 segundos
        setInterval(() => {
            window.location.reload();
        }, 30000);
    </script>
</body>
</html>"""
        return html
    
    def _setup_routes(self):
        """Configura las rutas del dashboard"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            """Página principal del dashboard"""
            await self.refresh_systems_status()
            return HTMLResponse(content=self.generate_dashboard_html())
        
        @self.app.get("/api/systems")
        async def get_systems_status():
            """API para obtener estado de sistemas"""
            await self.refresh_systems_status()
            
            systems_data = []
            for system in self.systems:
                systems_data.append({
                    "name": system.name,
                    "port": system.port,
                    "status": system.status.value,
                    "category": system.category,
                    "url": system.url,
                    "description": system.description
                })
            
            return {
                "timestamp": datetime.now().isoformat(),
                "total_systems": len(self.systems),
                "running_systems": sum(1 for s in self.systems if s.status == SystemStatus.RUNNING),
                "systems": systems_data
            }
        
        @self.app.get("/api/health")
        async def dashboard_health():
            """Health check del dashboard"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "2.0.0"
            }
        
        @self.app.get("/metrics")
        async def get_metrics():
            """Métricas del sistema"""
            await self.refresh_systems_status()
            
            # Métricas del host
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "timestamp": datetime.now().isoformat(),
                "systems": {
                    "total": len(self.systems),
                    "running": sum(1 for s in self.systems if s.status == SystemStatus.RUNNING),
                    "stopped": sum(1 for s in self.systems if s.status == SystemStatus.STOPPED),
                    "error": sum(1 for s in self.systems if s.status == SystemStatus.ERROR)
                },
                "host": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used_gb": round(memory.used / (1024**3), 2),
                    "memory_total_gb": round(memory.total / (1024**3), 2),
                    "disk_percent": disk.percent,
                    "disk_used_gb": round(disk.used / (1024**3), 2),
                    "disk_total_gb": round(disk.total / (1024**3), 2)
                }
            }

def main():
    """Función principal"""
    dashboard = SilhouetteMCPUnifiedDashboard()
    
    logger.info("🚀 Iniciando SilhouetteMCP Unified Dashboard...")
    logger.info("🌐 Dashboard disponible en: http://localhost:9000")
    logger.info("📊 API disponible en: http://localhost:9000/api/systems")
    
    uvicorn.run(
        dashboard.app,
        host="0.0.0.0",
        port=9000,
        log_level="info"
    )

if __name__ == "__main__":
    main()