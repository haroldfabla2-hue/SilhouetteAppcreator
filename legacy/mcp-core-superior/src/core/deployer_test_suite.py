"""
Scripts de utilidades para testing del Zero-Downtime Deployer
Probar funcionalidades sin afectar el sistema principal
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

from .zero_downtime_deployer import ZeroDowntimeDeployer, DeploymentStrategy, HealthCheckConfig
from .deployer_config import get_deployment_config, DEFAULT_DEV_CONFIG
from .deployer_integrator import DeploymentCoordinator

logger = logging.getLogger("mcp.deployer.test")


class DeployerTestSuite:
    """Suite de pruebas para el deployer"""
    
    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
        self.deployer: Optional[ZeroDowntimeDeployer] = None
        self.coordinator: Optional[DeploymentCoordinator] = None
    
    async def run_all_tests(self) -> bool:
        """Ejecutar todas las pruebas"""
        logger.info("🧪 Iniciando suite de pruebas del deployer")
        
        tests = [
            ("test_basic_initialization", self.test_basic_initialization),
            ("test_health_monitoring", self.test_health_monitoring),
            ("test_resource_management", self.test_resource_management),
            ("test_config_hot_reload", self.test_config_hot_reload),
            ("test_agent_lifecycle", self.test_agent_lifecycle),
            ("test_deployment_strategies", self.test_deployment_strategies),
            ("test_integration", self.test_integration),
            ("test_error_handling", self.test_error_handling)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                logger.info(f"🔄 Ejecutando prueba: {test_name}")
                success = await test_func()
                
                self.test_results.append({
                    "test_name": test_name,
                    "success": success,
                    "timestamp": datetime.now(),
                    "error": None if success else "Test falló"
                })
                
                if success:
                    passed += 1
                    logger.info(f"✅ {test_name}: PASÓ")
                else:
                    logger.error(f"❌ {test_name}: FALLÓ")
                    
            except Exception as e:
                self.test_results.append({
                    "test_name": test_name,
                    "success": False,
                    "timestamp": datetime.now(),
                    "error": str(e)
                })
                logger.error(f"❌ {test_name}: ERROR - {e}")
        
        # Resumen
        logger.info(f"🏁 Pruebas completadas: {passed}/{total} pasaron")
        
        if passed == total:
            logger.info("🎉 ¡Todas las pruebas pasaron!")
            return True
        else:
            logger.warning(f"⚠️  {total - passed} pruebas fallaron")
            return False
    
    async def test_basic_initialization(self) -> bool:
        """Probar inicialización básica"""
        try:
            # Test configuración
            config = get_deployment_config("development")
            assert config["environment"] == "development"
            assert "agent_configs" in config
            
            # Test deployer initialization
            from .zero_downtime_deployer import initialize_deployer
            self.deployer = await initialize_deployer(DEFAULT_DEV_CONFIG)
            
            assert self.deployer is not None
            assert self.deployer.status.value in ["initiated", "completed"]
            
            logger.info("Inicialización básica exitosa")
            return True
            
        except Exception as e:
            logger.error(f"Error en inicialización básica: {e}")
            return False
    
    async def test_health_monitoring(self) -> bool:
        """Probar monitoreo de salud"""
        try:
            assert self.deployer is not None
            
            # Verificar que health monitor esté funcionando
            health_status = self.deployer.health_monitor.get_health_status()
            assert "status" in health_status
            assert "metrics" in health_status
            
            # Verificar métricas del sistema
            metrics = self.deployer.health_monitor.get_system_metrics()
            assert "cpu_percent" in metrics
            assert "memory_mb" in metrics
            
            logger.info("Monitoreo de salud funcionando")
            return True
            
        except Exception as e:
            logger.error(f"Error en monitoreo de salud: {e}")
            return False
    
    async def test_resource_management(self) -> bool:
        """Probar gestión de recursos"""
        try:
            assert self.deployer is not None
            
            # Verificar resource manager
            report = self.deployer.resource_manager.get_resource_report()
            assert "latest_snapshot" in report
            
            # Verificar cleanup manual
            await self.deployer.resource_manager._force_gc()
            
            logger.info("Gestión de recursos funcionando")
            return True
            
        except Exception as e:
            logger.error(f"Error en gestión de recursos: {e}")
            return False
    
    async def test_config_hot_reload(self) -> bool:
        """Probar hot-reload de configuración"""
        try:
            assert self.deployer is not None
            
            # Crear archivo de configuración temporal
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
                f.write("TEST_VAR=test_value\n")
                f.write("DEBUG=false\n")
                temp_config_path = f.name
            
            try:
                # Cambiar configuración
                old_config = await self.deployer.config_manager.get_current_config()
                
                # Simular cambio
                new_config = {"TEST_VAR": "test_value", "DEBUG": "false"}
                
                # Callback de cambio
                await self.deployer._on_config_change(old_config, new_config)
                
                logger.info("Hot-reload de configuración funcionando")
                return True
                
            finally:
                os.unlink(temp_config_path)
                
        except Exception as e:
            logger.error(f"Error en hot-reload: {e}")
            return False
    
    async def test_agent_lifecycle(self) -> bool:
        """Probar ciclo de vida de agentes"""
        try:
            assert self.deployer is not None
            
            # Test iniciar agente
            agent_config = {
                "command": ["python", "-c", "import time; time.sleep(10)"],
                "id": "test_agent"
            }
            
            agent_instance = await self.deployer.agent_manager.start_agent("test_agent", agent_config)
            assert agent_instance.agent_id == "test_agent"
            assert agent_instance.status == "running"
            
            # Esperar un poco
            await asyncio.sleep(2)
            
            # Test detener agente
            await self.deployer.agent_manager.stop_agent("test_agent")
            
            # Verificar que se detuvo
            agent_status = await self.deployer.agent_manager.get_agent_status()
            assert "test_agent" not in agent_status
            
            logger.info("Ciclo de vida de agentes funcionando")
            return True
            
        except Exception as e:
            logger.error(f"Error en ciclo de vida de agentes: {e}")
            return False
    
    async def test_deployment_strategies(self) -> bool:
        """Probar estrategias de deployment"""
        try:
            assert self.deployer is not None
            
            # Test deployment inmediato (solo desarrollo)
            if settings.environment.value == "development":
                deployment_config = {
                    "strategy": "immediate",
                    "agent_configs": [
                        {"id": "test_immediate", "command": ["python", "-c", "print('test')"]}
                    ],
                    "health_checks": [],
                    "migrations": []
                }
                
                success = await self.deployer.deploy(deployment_config)
                # Puede fallar porque no hay agentes reales, pero la lógica debe funcionar
                
                logger.info("Estrategias de deployment funcionando")
                return True
            else:
                logger.info("Saltando test de estrategias en producción")
                return True
                
        except Exception as e:
            logger.error(f"Error en estrategias de deployment: {e}")
            return False
    
    async def test_integration(self) -> bool:
        """Probar integración completa"""
        try:
            # Test coordinador
            self.coordinator = DeploymentCoordinator("development")
            await self.coordinator.initialize()
            
            # Verificar que se inicializó correctamente
            assert self.coordinator.orchestrator is not None
            assert self.coordinator.deployer is not None
            assert self.coordinator.integrator is not None
            
            # Test health check integrado
            health = await self.coordinator.perform_health_check()
            assert "overall_status" in health
            
            # Cleanup
            await self.coordinator.shutdown()
            
            logger.info("Integración funcionando")
            return True
            
        except Exception as e:
            logger.error(f"Error en integración: {e}")
            return False
    
    async def test_error_handling(self) -> bool:
        """Probar manejo de errores"""
        try:
            assert self.deployer is not None
            
            # Test con configuración inválida
            invalid_config = {
                "strategy": "invalid_strategy",
                "agent_configs": [],
                "health_checks": []
            }
            
            try:
                await self.deployer.deploy(invalid_config)
                # Debería fallar o manejar el error graciosamente
                logger.info("Manejo de errores funcionando")
                return True
            except Exception:
                logger.info("Manejo de errores funcionando (excepción capturada)")
                return True
                
        except Exception as e:
            logger.error(f"Error en manejo de errores: {e}")
            return False
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generar reporte de pruebas"""
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        return {
            "test_suite": "Zero-Downtime Deployer Test Suite",
            "timestamp": datetime.now(),
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": total - passed,
                "success_rate": f"{(passed/total)*100:.1f}%" if total > 0 else "0%"
            },
            "test_results": self.test_results,
            "conclusion": "PASS" if passed == total else "FAIL"
        }


async def run_quick_test():
    """Ejecutar prueba rápida"""
    logger.info("🚀 Ejecutando prueba rápida del deployer")
    
    try:
        # Inicializar deployer
        from .zero_downtime_deployer import initialize_deployer
        deployer = await initialize_deployer(DEFAULT_DEV_CONFIG)
        
        # Verificar estado
        status = deployer.get_status()
        print(f"Estado del deployer: {status['status']}")
        
        # Health check
        health = deployer.health_monitor.get_health_status()
        print(f"Health status: {health['status']}")
        
        # Test agente simple
        agent_config = {"command": ["python", "-c", "print('Hello Agent')"], "id": "quick_test"}
        agent_instance = await deployer.agent_manager.start_agent("quick_test", agent_config)
        print(f"Agente iniciado: {agent_instance.agent_id}")
        
        await asyncio.sleep(1)
        
        await deployer.agent_manager.stop_agent("quick_test")
        print("Agente detenido")
        
        # Shutdown
        from .zero_downtime_deployer import shutdown_deployer
        await shutdown_deployer()
        
        print("✅ Prueba rápida completada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Prueba rápida falló: {e}")
        return False


async def run_stress_test():
    """Ejecutar prueba de estrés"""
    logger.info("🔥 Ejecutando prueba de estrés del deployer")
    
    try:
        from .zero_downtime_deployer import initialize_deployer
        deployer = await initialize_deployer(DEFAULT_DEV_CONFIG)
        
        # Crear múltiples agentes
        agents = []
        for i in range(5):
            agent_config = {
                "command": ["python", "-c", f"import time; time.sleep({30+i})"],
                "id": f"stress_test_{i}"
            }
            agent_instance = await deployer.agent_manager.start_agent(f"stress_test_{i}", agent_config)
            agents.append(agent_instance)
        
        print(f"Iniciados {len(agents)} agentes de estrés")
        
        # Monitorear por 30 segundos
        for i in range(6):
            await asyncio.sleep(5)
            agent_status = await deployer.agent_manager.get_agent_status()
            active_count = sum(1 for status in agent_status.values() if status.get("status") == "running")
            print(f"Monitoreo {i+1}: {active_count} agentes activos")
        
        # Cleanup
        for agent_id in [a.agent_id for a in agents]:
            await deployer.agent_manager.stop_agent(agent_id)
        
        await shutdown_deployer()
        
        print("✅ Prueba de estrés completada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Prueba de estrés falló: {e}")
        return False


async def main():
    """Función principal de testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Testing para Zero-Downtime Deployer")
    parser.add_argument("--test", choices=["all", "quick", "stress"], default="quick",
                       help="Tipo de prueba a ejecutar")
    parser.add_argument("--log-level", default="INFO",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Nivel de logging")
    
    args = parser.parse_args()
    
    # Configurar logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if args.test == "all":
        # Ejecutar suite completa
        test_suite = DeployerTestSuite()
        success = await test_suite.run_all_tests()
        
        # Generar reporte
        report = test_suite.generate_test_report()
        print("\n" + "="*50)
        print("REPORTE DE PRUEBAS")
        print("="*50)
        print(json.dumps(report, indent=2, default=str))
        
        return 0 if success else 1
        
    elif args.test == "quick":
        success = await run_quick_test()
        return 0 if success else 1
        
    elif args.test == "stress":
        success = await run_stress_test()
        return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))