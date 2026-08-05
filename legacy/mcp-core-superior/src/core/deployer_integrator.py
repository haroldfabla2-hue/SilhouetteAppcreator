"""
Integrador del Zero-Downtime Deployer con el sistema de orquestación
Conecta el sistema de deployment con MultiAgentOrchestrator existente
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum

from ..orchestrator.multi_agent_orchestrator import MultiAgentOrchestrator, OrchestrationContext
from .zero_downtime_deployer import ZeroDowntimeDeployer, DeploymentStrategy
from .deployer_config import get_deployment_config, DEFAULT_DEV_CONFIG
from .config import settings, Environment
from .exceptions import ConfigurationException

logger = logging.getLogger("mcp.deployer.integrator")


class IntegrationMode(Enum):
    """Modos de integración"""
    PASSIVE = "passive"  # Solo monitoreo
    ACTIVE = "active"    # Control total
    HYBRID = "hybrid"    # Control parcial


class DeployerOrchestratorIntegrator:
    """Integrador entre deployer y orquestador"""
    
    def __init__(self, orchestrator: MultiAgentOrchestrator, deployer: ZeroDowntimeDeployer):
        self.orchestrator = orchestrator
        self.deployer = deployer
        self.integration_mode = IntegrationMode.ACTIVE
        self.deployment_callbacks: List[Callable] = []
        self.agent_lifecycle_callbacks: List[Callable] = []
        self.deployment_history: List[Dict[str, Any]] = []
        self.running = False
        
    async def start_integration(self) -> None:
        """Iniciar integración"""
        logger.info("Iniciando integración deployer-orquestador")
        
        self.running = True
        
        # Iniciar monitoreo de orquestador
        self.monitoring_task = asyncio.create_task(self._orchestrator_monitoring_loop())
        
        # Configurar callbacks de deployment
        await self._setup_deployment_callbacks()
        
        logger.info("Integración deployer-orquestador iniciada")
    
    async def stop_integration(self) -> None:
        """Detener integración"""
        logger.info("Deteniendo integración deployer-orquestador")
        
        self.running = False
        
        if hasattr(self, 'monitoring_task'):
            self.monitoring_task.cancel()
        
        logger.info("Integración deployer-orquestador detenida")
    
    async def _orchestrator_monitoring_loop(self) -> None:
        """Loop de monitoreo del orquestador"""
        while self.running:
            try:
                await self._check_orchestrator_health()
                await self._monitor_active_tasks()
                await asyncio.sleep(30)  # Check cada 30 segundos
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en monitoreo de orquestador: {e}")
    
    async def _check_orchestrator_health(self) -> None:
        """Verificar salud del orquestador"""
        try:
            if not self.orchestrator.is_initialized:
                logger.warning("Orquestador no está inicializado")
                return
            
            # Verificar tareas activas
            active_count = len(self.orchestrator.active_tasks)
            completed_count = len(self.orchestrator.completed_tasks)
            
            logger.debug(f"Orquestador health: {active_count} activas, {completed_count} completadas")
            
            # Si hay muchos agentes activos, podría indicar problema
            if active_count > settings.max_concurrent_tasks * 2:
                logger.warning(f"Alto número de tareas activas: {active_count}")
                
        except Exception as e:
            logger.error(f"Error verificando salud del orquestador: {e}")
    
    async def _monitor_active_tasks(self) -> None:
        """Monitorear tareas activas"""
        try:
            current_time = datetime.now()
            
            for task_id, context in self.orchestrator.active_tasks.items():
                duration = (current_time - context.start_time).total_seconds()
                
                # Verificar timeout de tareas
                if duration > settings.default_timeout_seconds:
                    logger.warning(f"Tarea {task_id} excedió timeout: {duration}s")
                    await self._handle_task_timeout(task_id, context)
                
                # Verificar stuck tasks (sin progreso por mucho tiempo)
                if duration > 600:  # 10 minutos sin progreso
                    logger.warning(f"Tarea {task_id} podría estar atascada: {duration}s")
                    
        except Exception as e:
            logger.error(f"Error monitoreando tareas activas: {e}")
    
    async def _handle_task_timeout(self, task_id: str, context: OrchestrationContext) -> None:
        """Manejar timeout de tarea"""
        try:
            logger.info(f"Manejando timeout de tarea {task_id}")
            
            # Intentar cleanup graceful de la tarea
            if task_id in self.orchestrator.active_tasks:
                del self.orchestrator.active_tasks[task_id]
            
            # Notificar callback si existe
            for callback in self.agent_lifecycle_callbacks:
                try:
                    await callback("task_timeout", {
                        "task_id": task_id,
                        "context": context,
                        "timeout_seconds": settings.default_timeout_seconds
                    })
                except Exception as e:
                    logger.error(f"Error en callback de timeout: {e}")
                    
        except Exception as e:
            logger.error(f"Error manejando timeout de tarea: {e}")
    
    async def _setup_deployment_callbacks(self) -> None:
        """Configurar callbacks de deployment"""
        # Aquí se pueden configurar callbacks para eventos específicos
        # Por ejemplo, notificar al orquestador sobre cambios de agentes
        pass
    
    async def deploy_with_orchestrator_coordination(
        self,
        deployment_config: Dict[str, Any],
        coordination_level: str = "full"
    ) -> bool:
        """
        Deployer coordinado con el orquestador
        
        Args:
            deployment_config: Configuración del deployment
            coordination_level: Nivel de coordinación ("full", "partial", "none")
        """
        logger.info(f"Iniciando deployment coordinado (nivel: {coordination_level})")
        
        try:
            # 1. Pausar orquestador si es necesario
            if coordination_level in ["full", "partial"]:
                await self._pause_orchestrator_temporarily()
            
            # 2. Coordinar con orquestador durante deployment
            if coordination_level == "full":
                coordination_task = asyncio.create_task(
                    self._coordinate_with_orchestrator_during_deployment(deployment_config)
                )
            
            # 3. Ejecutar deployment
            success = await self.deployer.deploy(deployment_config)
            
            # 4. Cancelar coordinación si existe
            if coordination_level == "full":
                coordination_task.cancel()
                try:
                    await coordination_task
                except asyncio.CancelledError:
                    pass
            
            # 5. Reanudar orquestador
            if coordination_level in ["full", "partial"]:
                await self._resume_orchestrator()
            
            # 6. Registrar deployment
            self.deployment_history.append({
                "deployment_id": self.deployer.deployment_id,
                "timestamp": datetime.now(),
                "success": success,
                "coordination_level": coordination_level,
                "config": deployment_config
            })
            
            return success
            
        except Exception as e:
            logger.error(f"Error en deployment coordinado: {e}")
            
            # Rollback si es necesario
            if coordination_level in ["full", "partial"]:
                await self._resume_orchestrator()
            
            return False
    
    async def _pause_orchestrator_temporarily(self) -> None:
        """Pausar orquestador temporalmente"""
        logger.info("Pausando orquestador temporalmente")
        
        # Guardar estado actual
        self._original_orchestrator_state = {
            "is_initialized": self.orchestrator.is_initialized,
            "active_tasks": self.orchestrator.active_tasks.copy()
        }
        
        # En implementación real, se pausaría el orquestador
        # Por ahora, solo marcar que está pausado
        self._orchestrator_paused = True
    
    async def _resume_orchestrator(self) -> None:
        """Reanudar orquestador"""
        logger.info("Reanudando orquestador")
        
        # Restaurar estado original
        if hasattr(self, '_original_orchestrator_state'):
            self.orchestrator.is_initialized = self._original_orchestrator_state["is_initialized"]
            self.orchestrator.active_tasks = self._original_orchestrator_state["active_tasks"]
            delattr(self, '_original_orchestrator_state')
        
        self._orchestrator_paused = False
    
    async def _coordinate_with_orchestrator_during_deployment(
        self,
        deployment_config: Dict[str, Any]
    ) -> None:
        """Coordinar con orquestador durante deployment"""
        logger.info("Coordinando con orquestador durante deployment")
        
        # Monitorear estado del deployment y ajustar orquestador según necesidad
        while not self.shutdown_event.is_set():
            try:
                # Verificar estado del deployment
                deployer_status = self.deployer.get_status()
                
                if deployer_status["status"] in ["completed", "failed"]:
                    break
                
                # Ajustar comportamiento del orquestador según estado del deployment
                if deployer_status["status"] == "health_checking":
                    # Durante health checks, reducir carga del orquestador
                    await self._reduce_orchestrator_load()
                
                await asyncio.sleep(5)  # Check cada 5 segundos
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en coordinación: {e}")
                await asyncio.sleep(5)
    
    async def _reduce_orchestrator_load(self) -> None:
        """Reducir carga del orquestador temporalmente"""
        # En implementación real, se ajustarían parámetros del orquestador
        # como max_concurrent_tasks, etc.
        pass
    
    async def get_integrated_status(self) -> Dict[str, Any]:
        """Obtener estado integrado del sistema"""
        try:
            # Estado del deployer
            deployer_status = self.deployer.get_status()
            
            # Estado del orquestador
            orchestrator_status = {
                "is_initialized": self.orchestrator.is_initialized,
                "active_tasks_count": len(self.orchestrator.active_tasks),
                "completed_tasks_count": len(self.orchestrator.completed_tasks),
                "orchestrator_paused": getattr(self, '_orchestrator_paused', False)
            }
            
            # Estado integrado
            integrated_status = {
                "timestamp": datetime.now(),
                "integration_mode": self.integration_mode.value,
                "deployer": deployer_status,
                "orchestrator": orchestrator_status,
                "deployment_history_count": len(self.deployment_history),
                "last_deployment": self.deployment_history[-1] if self.deployment_history else None
            }
            
            return integrated_status
            
        except Exception as e:
            logger.error(f"Error obteniendo estado integrado: {e}")
            return {"error": str(e)}
    
    def add_deployment_callback(self, callback: Callable) -> None:
        """Agregar callback para eventos de deployment"""
        self.deployment_callbacks.append(callback)
    
    def add_agent_lifecycle_callback(self, callback: Callable) -> None:
        """Agregar callback para eventos de ciclo de vida de agentes"""
        self.agent_lifecycle_callbacks.append(callback)
    
    async def perform_health_check_integration(self) -> Dict[str, Any]:
        """Realizar health check integrado del sistema completo"""
        health_report = {
            "timestamp": datetime.now(),
            "overall_status": "unknown",
            "components": {}
        }
        
        try:
            # Health check del deployer
            deployer_status = self.deployer.get_status()
            health_report["components"]["deployer"] = deployer_status.get("health_status", {})
            
            # Health check del orquestador
            orchestrator_health = {
                "initialized": self.orchestrator.is_initialized,
                "active_tasks": len(self.orchestrator.active_tasks),
                "completed_tasks": len(self.orchestrator.completed_tasks)
            }
            health_report["components"]["orchestrator"] = orchestrator_health
            
            # Determinar estado general
            if deployer_status.get("status") == "completed" and orchestrator_health["initialized"]:
                health_report["overall_status"] = "healthy"
            elif deployer_status.get("status") == "failed":
                health_report["overall_status"] = "critical"
            else:
                health_report["overall_status"] = "degraded"
            
        except Exception as e:
            logger.error(f"Error en health check integrado: {e}")
            health_report["overall_status"] = "error"
            health_report["error"] = str(e)
        
        return health_report


class DeploymentCoordinator:
    """Coordinador principal para deployments"""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.integrator: Optional[DeployerOrchestratorIntegrator] = None
        self.deployer: Optional[ZeroDowntimeDeployer] = None
        self.orchestrator: Optional[MultiAgentOrchestrator] = None
        
    async def initialize(self) -> None:
        """Inicializar coordinador"""
        logger.info(f"Inicializando DeploymentCoordinator para entorno: {self.environment}")
        
        try:
            # Importar y configurar componentes
            from ..orchestrator import MultiAgentOrchestrator
            from .zero_downtime_deployer import initialize_deployer
            
            # Inicializar orquestador
            self.orchestrator = MultiAgentOrchestrator()
            await self.orchestrator.initialize()
            
            # Inicializar deployer
            deployment_config = get_deployment_config(self.environment)
            self.deployer = await initialize_deployer(deployment_config)
            
            # Crear integrador
            self.integrator = DeployerOrchestratorIntegrator(self.orchestrator, self.deployer)
            await self.integrator.start_integration()
            
            logger.info("DeploymentCoordinator inicializado exitosamente")
            
        except Exception as e:
            logger.error(f"Error inicializando DeploymentCoordinator: {e}")
            raise
    
    async def deploy_all_agents(self, agent_list: Optional[List[str]] = None) -> bool:
        """Deployer todos los agentes del sistema"""
        logger.info(f"Deploying todos los agentes - entorno: {self.environment}")
        
        try:
            # Obtener configuración de deployment
            deployment_config = get_deployment_config(self.environment, agent_list)
            
            # Deployer con coordinación
            if self.integrator:
                success = await self.integrator.deploy_with_orchestrator_coordination(
                    deployment_config,
                    coordination_level="full" if self.environment == "production" else "partial"
                )
            else:
                success = await self.deployer.deploy(deployment_config)
            
            return success
            
        except Exception as e:
            logger.error(f"Error en deployment de agentes: {e}")
            return False
    
    async def deploy_single_agent(self, agent_name: str) -> bool:
        """Deployer un agente específico"""
        logger.info(f"Deploying agente individual: {agent_name}")
        
        try:
            # Configuración para agente individual
            deployment_config = get_deployment_config(self.environment, [agent_name])
            
            # Deployer
            success = await self.deployer.deploy(deployment_config)
            
            return success
            
        except Exception as e:
            logger.error(f"Error en deployment de agente {agent_name}: {e}")
            return False
    
    async def perform_health_check(self) -> Dict[str, Any]:
        """Realizar health check completo del sistema"""
        try:
            if self.integrator:
                return await self.integrator.perform_health_check_integration()
            else:
                return {"error": "Sistema no inicializado"}
        except Exception as e:
            logger.error(f"Error en health check: {e}")
            return {"error": str(e)}
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema"""
        try:
            if self.integrator:
                return await self.integrator.get_integrated_status()
            else:
                return {"error": "Sistema no inicializado"}
        except Exception as e:
            logger.error(f"Error obteniendo estado del sistema: {e}")
            return {"error": str(e)}
    
    async def shutdown(self) -> None:
        """Shutdown del coordinador"""
        logger.info("Shutting down DeploymentCoordinator")
        
        try:
            if self.integrator:
                await self.integrator.stop_integration()
            
            if self.deployer:
                from .zero_downtime_deployer import shutdown_deployer
                await shutdown_deployer()
            
            if self.orchestrator:
                await self.orchestrator.cleanup()
            
            logger.info("DeploymentCoordinator shutdown completado")
            
        except Exception as e:
            logger.error(f"Error durante shutdown: {e}")


# Instancia global del coordinador
coordinator: Optional[DeploymentCoordinator] = None


async def initialize_deployment_coordinator(environment: str = "development") -> DeploymentCoordinator:
    """Inicializar coordinador global"""
    global coordinator
    
    if coordinator is None:
        coordinator = DeploymentCoordinator(environment)
        await coordinator.initialize()
    
    return coordinator


async def shutdown_deployment_coordinator() -> None:
    """Shutdown coordinador global"""
    global coordinator
    
    if coordinator:
        await coordinator.shutdown()
        coordinator = None


# Ejemplo de uso integrado
async def example_integrated_deployment():
    """Ejemplo de uso del sistema integrado"""
    
    # Inicializar coordinador
    coordinator = await initialize_deployment_coordinator("development")
    
    try:
        # Deployer todos los agentes
        success = await coordinator.deploy_all_agents()
        
        if success:
            print("✅ Deployment de todos los agentes exitoso")
        else:
            print("❌ Deployment falló")
        
        # Verificar estado
        status = await coordinator.get_system_status()
        print(f"Estado del sistema: {status}")
        
        # Health check
        health = await coordinator.perform_health_check()
        print(f"Health check: {health}")
        
        # Deployer agente individual
        individual_success = await coordinator.deploy_single_agent("file_processing")
        print(f"Deployment individual: {'✅' if individual_success else '❌'}")
        
        # Monitorear por un tiempo
        for i in range(5):
            status = await coordinator.get_system_status()
            print(f"Monitoreo {i+1}: {status['deployer']['status']}")
            await asyncio.sleep(30)
        
    except KeyboardInterrupt:
        print("Shutdown solicitado...")
    finally:
        await shutdown_deployment_coordinator()


if __name__ == "__main__":
    asyncio.run(example_integrated_deployment())