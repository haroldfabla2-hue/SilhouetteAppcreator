#!/usr/bin/env python3
"""
SilhouetteMCP Master Startup Script
Sistema maestro de inicialización para todos los componentes SilhouetteMCP

Coordina la inicialización de:
- Sistemas originales (8001-8002)
- Sistemas mejorados (8007-8024)
- Orquestador de integración
- Sistema de monitoreo

Autor: MiniMax Agent
Fecha: 2025-11-06
"""

import asyncio
import json
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import psutil
from dataclasses import dataclass
from enum import Enum

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('silhouettemcp_master.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('SilhouetteMCP-Master')

class SystemStatus(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    STOPPING = "stopping"

@dataclass
class SystemComponent:
    name: str
    port: int
    script_path: str
    status: SystemStatus = SystemStatus.STOPPED
    process: Optional[subprocess.Popen] = None
    health_check_url: str = ""
    critical: bool = True

class SilhouetteMCPMasterStartup:
    """Sistema maestro de inicialización para SilhouetteMCP"""
    
    def __init__(self):
        self.components: List[SystemComponent] = []
        self.running_processes: Dict[str, subprocess.Popen] = {}
        self.startup_order = [
            # Sistemas originales primero
            "diagnostic_system",
            "enhanced_architecture", 
            "enhanced_security",
            "enhanced_scalability",
            "monitoring_system",
            "integration_orchestrator",
            "server_unified_original",
            "hierarchical_architecture_original"
        ]
        
        self._initialize_components()
        
    def _initialize_components(self):
        """Inicializa todos los componentes del sistema"""
        
        # Sistemas originales
        self.components.extend([
            SystemComponent(
                name="server_unified_original",
                port=8001,
                script_path="silhouettemcp_server_unified.py",
                critical=True,
                health_check_url="http://localhost:8001/health"
            ),
            SystemComponent(
                name="hierarchical_architecture_original", 
                port=8002,
                script_path="silhouettemcp_hierarchical_architecture.py",
                critical=True,
                health_check_url="http://localhost:8002/health"
            )
        ])
        
        # Sistema de diagnóstico
        self.components.append(
            SystemComponent(
                name="diagnostic_system",
                port=8007,
                script_path="silhouettemcp_robust_diagnostic_system.py",
                critical=True,
                health_check_url="http://localhost:8007/health"
            )
        )
        
        # Sistemas mejorados - Arquitectura (8010-8014)
        for port in range(8010, 8015):
            self.components.append(
                SystemComponent(
                    name=f"enhanced_architecture_port_{port}",
                    port=port,
                    script_path="silhouettemcp_enhanced_architecture_system.py",
                    critical=True,
                    health_check_url=f"http://localhost:{port}/health"
                )
            )
        
        # Sistemas mejorados - Seguridad (8015-8019)
        for port in range(8015, 8020):
            self.components.append(
                SystemComponent(
                    name=f"enhanced_security_port_{port}",
                    port=port,
                    script_path="silhouettemcp_enhanced_security_system.py", 
                    critical=True,
                    health_check_url=f"http://localhost:{port}/health"
                )
            )
        
        # Sistemas mejorados - Escalabilidad (8020-8024)
        for port in range(8020, 8025):
            self.components.append(
                SystemComponent(
                    name=f"enhanced_scalability_port_{port}",
                    port=port,
                    script_path="silhouettemcp_enhanced_scalability_system.py",
                    critical=True,
                    health_check_url=f"http://localhost:{port}/health"
                )
            )
            
        # Orquestador de integración
        self.components.append(
            SystemComponent(
                name="integration_orchestrator",
                port=8025,
                script_path="silhouettemcp_integration_orchestrator.py",
                critical=True,
                health_check_url="http://localhost:8025/health"
            )
        )
        
        # Sistema de monitoreo
        self.components.append(
            SystemComponent(
                name="monitoring_system",
                port=8026,
                script_path="silhouettemcp_integrated_monitoring.py",
                critical=True,
                health_check_url="http://localhost:8026/health"
            )
        )
        
    def check_port_available(self, port: int) -> bool:
        """Verifica si un puerto está disponible"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return True
            except OSError:
                return False
                
    def start_component(self, component: SystemComponent) -> bool:
        """Inicia un componente específico"""
        try:
            logger.info(f"Iniciando componente: {component.name} en puerto {component.port}")
            
            # Verificar si el puerto está disponible
            if not self.check_port_available(component.port):
                logger.warning(f"Puerto {component.port} ya está en uso")
                return True  # Ya está corriendo
                
            # Cambiar al directorio correcto
            script_path = Path("code") / component.script_path
            if not script_path.exists():
                logger.error(f"Script no encontrado: {script_path}")
                return False
                
            # Iniciar el proceso
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd="code",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**subprocess.os.environ, 'PYTHONPATH': 'code'}
            )
            
            self.running_processes[component.name] = process
            component.process = process
            component.status = SystemStatus.STARTING
            
            # Esperar un momento para que inicie
            time.sleep(2)
            
            # Verificar si el proceso sigue corriendo
            if process.poll() is None:
                component.status = SystemStatus.RUNNING
                logger.info(f"✅ {component.name} iniciado exitosamente en puerto {component.port}")
                return True
            else:
                component.status = SystemStatus.FAILED
                logger.error(f"❌ Fallo al iniciar {component.name}")
                return False
                
        except Exception as e:
            component.status = SystemStatus.FAILED
            logger.error(f"Error iniciando {component.name}: {str(e)}")
            return False
            
    def stop_component(self, component: SystemComponent) -> bool:
        """Detiene un componente específico"""
        try:
            if component.name in self.running_processes:
                process = self.running_processes[component.name]
                component.status = SystemStatus.STOPPING
                
                # Terminar el proceso gracefulmente
                process.terminate()
                
                # Esperar un poco
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Si no termina gracefulmente, forzar
                    process.kill()
                    
                del self.running_processes[component.name]
                component.status = SystemStatus.STOPPED
                component.process = None
                
                logger.info(f"🛑 {component.name} detenido")
                return True
                
        except Exception as e:
            logger.error(f"Error deteniendo {component.name}: {str(e)}")
            return False
            
    def health_check(self, component: SystemComponent) -> bool:
        """Realiza health check de un componente"""
        try:
            import requests
            response = requests.get(component.health_check_url, timeout=5)
            return response.status_code == 200
        except:
            return False
            
    def start_all_systems(self, order: Optional[List[str]] = None) -> bool:
        """Inicia todos los sistemas en orden"""
        startup_order = order or self.startup_order
        
        logger.info("🚀 Iniciando SilhouetteMCP - Todos los sistemas")
        logger.info("=" * 60)
        
        success_count = 0
        total_count = len(self.components)
        
        for component_name in startup_order:
            component = next((c for c in self.components if c.name == component_name), None)
            if not component:
                continue
                
            if self.start_component(component):
                success_count += 1
                
        logger.info("=" * 60)
        logger.info(f"Inicialización completada: {success_count}/{total_count} componentes")
        
        if success_count == total_count:
            logger.info("🎉 Todos los sistemas iniciados exitosamente")
            return True
        else:
            logger.warning(f"⚠️ {total_count - success_count} componentes fallaron")
            return False
            
    def stop_all_systems(self):
        """Detiene todos los sistemas"""
        logger.info("🛑 Deteniendo SilhouetteMCP - Todos los sistemas")
        
        # Detener en orden inverso
        for component in reversed(self.components):
            if component.status == SystemStatus.RUNNING:
                self.stop_component(component)
                
        logger.info("🏁 Todos los sistemas detenidos")
        
    def get_system_status(self) -> Dict:
        """Obtiene el estado actual del sistema"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "total_components": len(self.components),
            "running": 0,
            "failed": 0,
            "stopped": 0,
            "components": []
        }
        
        for component in self.components:
            comp_status = {
                "name": component.name,
                "port": component.port,
                "status": component.status.value,
                "critical": component.critical,
                "pid": component.process.pid if component.process else None
            }
            
            status["components"].append(comp_status)
            
            if component.status == SystemStatus.RUNNING:
                status["running"] += 1
            elif component.status == SystemStatus.FAILED:
                status["failed"] += 1
            else:
                status["stopped"] += 1
                
        return status
        
    def save_startup_report(self, filename: str = "startup_report.json"):
        """Guarda reporte de inicialización"""
        report = {
            "startup_time": datetime.now().isoformat(),
            "system_status": self.get_system_status(),
            "environment": {
                "python_version": sys.version,
                "platform": sys.platform,
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"📊 Reporte guardado en {filename}")
        
    def run_verification(self):
        """Ejecuta verificación del sistema"""
        logger.info("🔍 Ejecutando verificación del sistema...")
        
        # Health checks de componentes críticos
        critical_components = [c for c in self.components if c.critical]
        healthy_count = 0
        
        for component in critical_components:
            if component.status == SystemStatus.RUNNING:
                if self.health_check(component):
                    healthy_count += 1
                    logger.info(f"✅ {component.name} - Health check OK")
                else:
                    logger.warning(f"⚠️ {component.name} - Health check FAILED")
            else:
                logger.warning(f"⚠️ {component.name} - No está corriendo")
                
        health_percentage = (healthy_count / len(critical_components)) * 100
        logger.info(f"🔍 Verificación completada: {healthy_count}/{len(critical_components)} componentes saludables ({health_percentage:.1f}%)")
        
        return health_percentage

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SilhouetteMCP Master Startup")
    parser.add_argument("action", choices=["start", "stop", "status", "verify", "health"], 
                       help="Acción a realizar")
    parser.add_argument("--components", nargs="*", help="Componentes específicos")
    
    args = parser.parse_args()
    startup = SilhouetteMCPMasterStartup()
    
    if args.action == "start":
        logger.info("🚀 Iniciando SilhouetteMCP...")
        success = startup.start_all_systems(args.components)
        
        if success:
            logger.info("✅ Inicialización exitosa")
            
            # Guardar reporte
            startup.save_startup_report()
            
            # Ejecutar verificación
            health_percentage = startup.run_verification()
            
            if health_percentage >= 80:
                logger.info("🎉 Sistema operativo y saludable")
                sys.exit(0)
            else:
                logger.warning("⚠️ Sistema con problemas de salud")
                sys.exit(1)
        else:
            logger.error("❌ Error en la inicialización")
            sys.exit(1)
            
    elif args.action == "stop":
        logger.info("🛑 Deteniendo SilhouetteMCP...")
        startup.stop_all_systems()
        logger.info("✅ Sistemas detenidos")
        
    elif args.action == "status":
        status = startup.get_system_status()
        print(json.dumps(status, indent=2))
        
    elif args.action == "verify":
        health_percentage = startup.run_verification()
        print(f"Health percentage: {health_percentage:.1f}%")
        
    elif args.action == "health":
        # Health checks de todos los componentes
        for component in startup.components:
            if component.status == SystemStatus.RUNNING:
                healthy = startup.health_check(component)
                status = "✅ HEALTHY" if healthy else "⚠️ UNHEALTHY"
                print(f"{component.name} (puerto {component.port}): {status}")
            else:
                print(f"{component.name} (puerto {component.port}): 🛑 STOPPED")

if __name__ == "__main__":
    main()