"""
Sistema de Integración Auto-Healing con FastMCP Server
Integra el motor de auto-healing con el servidor principal
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta

from .auto_healing_engine import (
    AutoHealingEngine, HealthMetrics, ErrorEvent, HealthStatus, 
    RecoveryStrategy, get_auto_healing_engine
)
from .health_metrics import (
    HealthMetricsCollector, get_metrics_collector, 
    SystemResourceMetrics, ApplicationMetrics, AgentPerformanceMetrics
)
from .auto_healing_config import (
    get_config_manager, AutoHealingConfiguration, 
    DynamicThresholds, AgentSpecificConfig
)
from .exceptions import MCPCoreException, AgentException


class HealingIntegration:
    """Integración principal del sistema de auto-healing con FastMCP"""
    
    def __init__(self, mcp_server_instance):
        self.server = mcp_server_instance
        self.logger = logging.getLogger("mcp.healing.integration")
        
        # Componentes del sistema
        self.auto_healing_engine: Optional[AutoHealingEngine] = None
        self.metrics_collector: Optional[HealthMetricsCollector] = None
        self.config_manager = None
        
        # Estado de integración
        self.is_initialized = False
        self.integration_active = False
        self.health_check_interval = 30
        
        # Callbacks específicos
        self.server_startup_callbacks: List[Callable] = []
        self.server_shutdown_callbacks: List[Callable] = []
        self.agent_failure_callbacks: List[Callable] = []
        
        # Métricas de integración
        self.integration_stats = {
            "startup_time": None,
            "total_healing_events": 0,
            "successful_heals": 0,
            "failed_heals": 0,
            "last_healing_event": None
        }
    
    async def initialize(self):
        """Inicializar integración con el servidor MCP"""
        if self.is_initialized:
            return
        
        try:
            self.logger.info("Initializing Healing Integration...")
            start_time = datetime.now()
            
            # Inicializar componentes
            await self._initialize_components()
            
            # Configurar integración
            await self._setup_integration()
            
            # Registrar herramientas MCP de healing
            await self._register_healing_tools()
            
            # Configurar callbacks de lifecycle
            await self._setup_lifecycle_callbacks()
            
            # Configurar callbacks de agentes
            await self._setup_agent_callbacks()
            
            self.is_initialized = True
            self.integration_active = True
            
            # Actualizar estadísticas
            self.integration_stats["startup_time"] = (datetime.now() - start_time).total_seconds()
            
            self.logger.info("Healing Integration initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing Healing Integration: {e}")
            raise MCPCoreException(
                message=f"Failed to initialize auto-healing integration: {str(e)}",
                error_code="HEALING_INTEGRATION_ERROR"
            )
    
    async def _initialize_components(self):
        """Inicializar componentes del sistema de healing"""
        # Inicializar gestor de configuración
        self.config_manager = await get_config_manager()
        config = self.config_manager.get_config()
        
        if not config.enabled:
            self.logger.info("Auto-healing is disabled in configuration")
            return
        
        # Inicializar motor de auto-healing
        self.auto_healing_engine = await get_auto_healing_engine()
        
        # Inicializar recolector de métricas
        metrics_interval = config.monitoring_interval
        self.metrics_collector = get_metrics_collector(metrics_interval)
        
        # Configurar callbacks específicos
        self.auto_healing_engine.register_health_change_callback(self._on_health_change)
        self.auto_healing_engine.register_recovery_callback(self._on_recovery_event)
        self.auto_healing_engine.register_scaling_callback(self._on_scaling_event)
        
        # Registrar callbacks de métricas
        self.metrics_collector.register_metric_callback(self._on_metrics_update)
        
        self.logger.info("Auto-healing components initialized")
    
    async def _setup_integration(self):
        """Configurar integración específica con componentes del servidor"""
        # Integrar con agentes del servidor
        await self._integrate_with_server_agents()
        
        # Integrar con orquestador
        await self._integrate_with_orchestrator()
        
        # Integrar con streaming engine
        await self._integrate_with_streaming()
        
        self.logger.info("Integration setup completed")
    
    async def _integrate_with_server_agents(self):
        """Integrar con agentes del servidor"""
        agent_wrappers = [
            ("reasoner", self.server.reasoner_agent),
            ("planner", self.server.planner_agent),
            ("executor", self.server.executor_agent),
            ("verifier", self.server.verifier_agent),
            ("memory_manager", self.server.memory_manager_agent)
        ]
        
        for agent_name, agent_wrapper in agent_wrappers:
            if agent_wrapper:
                try:
                    # Obtener configuración específica del agente
                    agent_config = self.config_manager.get_agent_config(agent_name)
                    
                    # Configurar health checks para el agente
                    await self._setup_agent_health_monitoring(agent_name, agent_wrapper, agent_config)
                    
                    self.logger.info(f"Integrated with {agent_name} agent")
                    
                except Exception as e:
                    self.logger.error(f"Error integrating with {agent_name} agent: {e}")
    
    async def _integrate_with_orchestrator(self):
        """Integrar con el orquestador multi-agente"""
        try:
            if hasattr(self.server, 'orchestrator') and self.server.orchestrator:
                # Configurar monitoring del orquestrador
                orchestrator_config = self.config_manager.get_agent_config("orchestrator")
                
                # Integrar con callbacks del orquestrador
                original_orchestrate_task = self.server.orchestrator.orchestrate_task
                
                async def monitored_orchestrate_task(*args, **kwargs):
                    """Wrapper para monitorear ejecución del orquestrador"""
                    task_start = datetime.now()
                    try:
                        result = await original_orchestrate_task(*args, **kwargs)
                        
                        # Reportar métricas de ejecución exitosa
                        execution_time = (datetime.now() - task_start).total_seconds()
                        await self._report_agent_execution("orchestrator", True, execution_time)
                        
                        return result
                        
                    except Exception as e:
                        # Reportar métricas de ejecución fallida
                        execution_time = (datetime.now() - task_start).total_seconds()
                        await self._report_agent_execution("orchestrator", False, execution_time)
                        
                        # Registrar error para auto-healing
                        error_event = ErrorEvent(
                            timestamp=datetime.now(),
                            error_type=type(e).__name__,
                            severity="error",
                            source="orchestrator",
                            message=str(e),
                            context={"operation": "orchestrate_task"}
                        )
                        await self.auto_healing_engine.record_error(error_event)
                        
                        raise
                
                # Reemplazar método original
                self.server.orchestrator.orchestrate_task = monitored_orchestrate_task
                
                self.logger.info("Integrated with orchestrator")
                
        except Exception as e:
            self.logger.error(f"Error integrating with orchestrator: {e}")
    
    async def _integrate_with_streaming(self):
        """Integrar con el motor de streaming"""
        try:
            if hasattr(self.server, 'streaming_engine') and self.server.streaming_engine:
                # Configurar monitoring del streaming
                streaming_config = self.config_manager.get_agent_config("streaming")
                
                # Integrar con lifecycle del streaming
                original_create_stream = self.server.streaming_engine.create_stream
                
                async def monitored_create_stream(*args, **kwargs):
                    """Wrapper para monitorear creación de streams"""
                    try:
                        stream_id = await original_create_stream(*args, **kwargs)
                        
                        # Reportar métricas de stream creado
                        await self._report_agent_execution("streaming", True, 0.1)
                        
                        return stream_id
                        
                    except Exception as e:
                        # Reportar error en creación de stream
                        await self._report_agent_execution("streaming", False, 0.1)
                        
                        error_event = ErrorEvent(
                            timestamp=datetime.now(),
                            error_type=type(e).__name__,
                            severity="error",
                            source="streaming",
                            message=str(e),
                            context={"operation": "create_stream"}
                        )
                        await self.auto_healing_engine.record_error(error_event)
                        
                        raise
                
                # Reemplazar método original
                self.server.streaming_engine.create_stream = monitored_create_stream
                
                self.logger.info("Integrated with streaming engine")
                
        except Exception as e:
            self.logger.error(f"Error integrating with streaming: {e}")
    
    async def _setup_agent_health_monitoring(self, agent_name: str, agent_wrapper, agent_config: AgentSpecificConfig):
        """Configurar monitoreo de salud para un agente específico"""
        if not agent_config.health_check_interval:
            return
        
        async def health_check_wrapper():
            """Wrapper para health check del agente"""
            try:
                # Realizar health check del agente
                health_result = await agent_wrapper.health_check()
                
                # Convertir resultado a HealthMetrics
                metrics = self._convert_agent_health_to_metrics(agent_name, health_result)
                
                # Registrar métricas en el sistema de auto-healing
                await self.auto_healing_engine.record_health_metrics(agent_name, metrics)
                
            except Exception as e:
                self.logger.error(f"Error in health check for {agent_name}: {e}")
                
                # Registrar error en el sistema de auto-healing
                error_event = ErrorEvent(
                    timestamp=datetime.now(),
                    error_type=type(e).__name__,
                    severity="error",
                    source=agent_name,
                    message=str(e),
                    context={"operation": "health_check"}
                )
                await self.auto_healing_engine.record_error(error_event)
        
        # Programar health checks periódicos
        async def health_monitoring_loop():
            while self.integration_active:
                try:
                    await health_check_wrapper()
                    await asyncio.sleep(agent_config.health_check_interval)
                except Exception as e:
                    self.logger.error(f"Error in health monitoring loop for {agent_name}: {e}")
                    await asyncio.sleep(agent_config.health_check_interval)
        
        # Iniciar loop de monitoreo
        asyncio.create_task(health_monitoring_loop())
    
    def _convert_agent_health_to_metrics(self, agent_name: str, health_result: Dict[str, Any]) -> HealthMetrics:
        """Convertir resultado de health check de agente a HealthMetrics"""
        # Extraer métricas del resultado del health check
        status = health_result.get("status", "unknown")
        
        # Calcular health score basado en status
        health_score_map = {
            "healthy": 1.0,
            "degraded": 0.7,
            "critical": 0.4,
            "failed": 0.1,
            "unknown": 0.5
        }
        health_score = health_score_map.get(status, 0.5)
        
        # Extraer otras métricas si están disponibles
        metrics_data = health_result.get("metrics", {})
        
        return HealthMetrics(
            timestamp=datetime.now(),
            agent_name=agent_name,
            cpu_usage=metrics_data.get("cpu_usage", 0.0),
            memory_usage=metrics_data.get("memory_usage", 0.0),
            response_time=metrics_data.get("response_time", 0.0),
            error_rate=metrics_data.get("error_rate", 0.0),
            throughput=metrics_data.get("throughput", 0.0),
            active_tasks=metrics_data.get("active_tasks", 0),
            queue_size=metrics_data.get("queue_size", 0),
            health_score=health_score
        )
    
    async def _setup_lifecycle_callbacks(self):
        """Configurar callbacks de lifecycle del servidor"""
        # Callback de startup del servidor
        original_start = self.server.start
        async def healing_aware_start():
            """Wrapper para start con integración de healing"""
            try:
                result = await original_start()
                
                # Notificar startup a sistema de healing
                await self._on_server_startup()
                
                return result
            except Exception as e:
                self.logger.error(f"Error in server startup with healing: {e}")
                raise
        
        self.server.start = healing_aware_start
        
        # Callback de shutdown del servidor
        original_stop = self.server.stop
        async def healing_aware_stop():
            """Wrapper para stop con limpieza de healing"""
            try:
                # Notificar shutdown a sistema de healing
                await self._on_server_shutdown()
                
                result = await original_stop()
                return result
            except Exception as e:
                self.logger.error(f"Error in server shutdown with healing: {e}")
                raise
        
        self.server.stop = healing_aware_stop
        
        self.logger.info("Lifecycle callbacks configured")
    
    async def _setup_agent_callbacks(self):
        """Configurar callbacks específicos de agentes"""
        # Estos serían callbacks personalizados para cada tipo de agente
        pass
    
    async def _register_healing_tools(self):
        """Registrar herramientas MCP relacionadas con auto-healing"""
        
        @self.server.mcp.tool
        async def get_healing_status() -> Dict[str, Any]:
            """Obtener estado completo del sistema de auto-healing"""
            if not self.integration_active:
                return {"status": "disabled", "message": "Auto-healing is not active"}
            
            # Obtener estado del motor de auto-healing
            healing_status = self.auto_healing_engine.get_health_status()
            
            # Obtener métricas actuales
            current_metrics = self.metrics_collector.get_current_metrics() if self.metrics_collector else {}
            
            # Obtener configuración
            config = self.config_manager.get_config()
            
            return {
                "integration_status": "active",
                "healing_engine": healing_status,
                "metrics": current_metrics,
                "configuration": {
                    "enabled": config.enabled,
                    "debug_mode": config.debug_mode,
                    "monitoring_interval": config.monitoring_interval
                },
                "integration_stats": self.integration_stats
            }
        
        @self.server.mcp.tool
        async def force_agent_recovery(agent_name: str, strategy: Optional[str] = None) -> Dict[str, Any]:
            """Forzar recuperación de un agente específico"""
            if not self.integration_active or not self.auto_healing_engine:
                return {"status": "error", "message": "Auto-healing not active"}
            
            try:
                recovery_strategy = RecoveryStrategy(strategy) if strategy else None
                success = await self.auto_healing_engine.force_recovery(agent_name, recovery_strategy)
                
                return {
                    "status": "success" if success else "failed",
                    "agent": agent_name,
                    "strategy": strategy,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "message": str(e),
                    "agent": agent_name,
                    "timestamp": datetime.now().isoformat()
                }
        
        @self.server.mcp.tool
        async def get_failure_predictions() -> Dict[str, Any]:
            """Obtener predicciones de fallo de agentes"""
            if not self.integration_active or not self.auto_healing_engine:
                return {"status": "error", "message": "Auto-healing not active"}
            
            predictions = self.auto_healing_engine.get_failure_predictions()
            anomalies = self.auto_healing_engine.get_anomalies()
            
            return {
                "status": "success",
                "predictions": predictions,
                "anomalies": anomalies,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.server.mcp.tool
        async def update_healing_config(updates: Dict[str, Any]) -> Dict[str, Any]:
            """Actualizar configuración de auto-healing"""
            if not self.integration_active:
                return {"status": "error", "message": "Auto-healing not active"}
            
            try:
                success = await self.config_manager.update_config(updates)
                
                return {
                    "status": "success" if success else "failed",
                    "updates": updates,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        @self.server.mcp.tool
        async def get_performance_report(time_range_hours: int = 1) -> Dict[str, Any]:
            """Obtener reporte de rendimiento del sistema"""
            if not self.integration_active or not self.metrics_collector:
                return {"status": "error", "message": "Metrics collection not active"}
            
            try:
                from .health_metrics import MetricsAggregator
                from datetime import timedelta
                
                aggregator = MetricsAggregator(self.metrics_collector)
                report = aggregator.generate_performance_report(timedelta(hours=time_range_hours))
                
                return {
                    "status": "success",
                    "report": report,
                    "time_range_hours": time_range_hours,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        self.logger.info("Healing MCP tools registered")
    
    # ==================== CALLBACK HANDLERS ====================
    
    async def _on_health_change(self, agent_name: str, old_health: HealthStatus, new_health: HealthStatus, metrics: HealthMetrics):
        """Manejar cambios de salud de agentes"""
        self.logger.info(f"Health change for {agent_name}: {old_health.value} -> {new_health.value}")
        
        # Notificar al servidor sobre cambio de salud
        if hasattr(self.server, 'on_agent_health_change'):
            try:
                await self.server.on_agent_health_change(agent_name, old_health, new_health, metrics)
            except Exception as e:
                self.logger.error(f"Error notifying server about health change: {e}")
    
    async def _on_recovery_event(self, agent_name: str, strategy: RecoveryStrategy, result: str):
        """Manejar eventos de recuperación"""
        self.integration_stats["total_healing_events"] += 1
        self.integration_stats["last_healing_event"] = datetime.now().isoformat()
        
        if result == "success":
            self.integration_stats["successful_heals"] += 1
        else:
            self.integration_stats["failed_heals"] += 1
        
        self.logger.info(f"Recovery event for {agent_name}: {strategy.value} -> {result}")
        
        # Notificar al servidor sobre evento de recuperación
        if hasattr(self.server, 'on_recovery_event'):
            try:
                await self.server.on_recovery_event(agent_name, strategy, result)
            except Exception as e:
                self.logger.error(f"Error notifying server about recovery event: {e}")
    
    async def _on_scaling_event(self, agent_name: str, action, old_instances: int, new_instances: int):
        """Manejar eventos de escalado"""
        self.logger.info(f"Scaling event for {agent_name}: {action} from {old_instances} to {new_instances} instances")
        
        # Notificar al servidor sobre evento de escalado
        if hasattr(self.server, 'on_scaling_event'):
            try:
                await self.server.on_scaling_event(agent_name, action, old_instances, new_instances)
            except Exception as e:
                self.logger.error(f"Error notifying server about scaling event: {e}")
    
    async def _on_metrics_update(self):
        """Manejar actualizaciones de métricas"""
        # Procesar métricas actualizadas si es necesario
        pass
    
    async def _on_server_startup(self):
        """Manejar startup del servidor"""
        # Iniciar recolección de métricas si está habilitada
        if self.metrics_collector:
            await self.metrics_collector.start_collection()
        
        self.logger.info("Healing integration activated after server startup")
    
    async def _on_server_shutdown(self):
        """Manejar shutdown del servidor"""
        self.integration_active = False
        
        # Detener recolección de métricas
        if self.metrics_collector:
            await self.metrics_collector.stop_collection()
        
        # Limpiar motor de auto-healing
        if self.auto_healing_engine:
            await self.auto_healing_engine.cleanup()
        
        self.logger.info("Healing integration deactivated")
    
    async def _report_agent_execution(self, agent_name: str, success: bool, execution_time: float):
        """Reportar ejecución de agente para métricas"""
        if self.metrics_collector:
            # Registrar tiempo de ejecución
            self.metrics_collector.record_execution_time(agent_name, execution_time)
        
        # Actualizar métricas de agente en auto-healing si es necesario
        # Esto sería más detallado en una implementación completa
    
    # ==================== MÉTODOS PÚBLICOS ====================
    
    def is_active(self) -> bool:
        """Verificar si la integración está activa"""
        return self.integration_active and self.is_initialized
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de integración"""
        return self.integration_stats.copy()
    
    async def activate_healing(self) -> bool:
        """Activar sistema de auto-healing"""
        if not self.is_initialized:
            await self.initialize()
        
        config = self.config_manager.get_config()
        if not config.enabled:
            return False
        
        self.integration_active = True
        
        # Iniciar recolección de métricas
        if self.metrics_collector:
            await self.metrics_collector.start_collection()
        
        self.logger.info("Auto-healing activated")
        return True
    
    async def deactivate_healing(self):
        """Desactivar sistema de auto-healing"""
        self.integration_active = False
        
        # Detener recolección de métricas
        if self.metrics_collector:
            await self.metrics_collector.stop_collection()
        
        self.logger.info("Auto-healing deactivated")
    
    async def get_healing_recommendations(self) -> List[Dict[str, Any]]:
        """Obtener recomendaciones del sistema de auto-healing"""
        if not self.integration_active or not self.auto_healing_engine:
            return []
        
        recommendations = []
        
        # Obtener predicciones de fallo
        predictions = self.auto_healing_engine.get_failure_predictions()
        for agent_name, probability in predictions.items():
            if probability > 0.7:
                recommendations.append({
                    "type": "failure_prediction",
                    "agent": agent_name,
                    "probability": probability,
                    "recommendation": "Apply preventive measures",
                    "priority": "high" if probability > 0.8 else "medium"
                })
        
        # Obtener anomalías
        anomalies = self.auto_healing_engine.get_anomalies()
        for anomaly in anomalies[:5]:  # Top 5 anomalies
            recommendations.append({
                "type": "anomaly_detection",
                "agent": anomaly["agent_name"],
                "anomalies": anomaly["anomalies"],
                "recommendation": "Investigate performance anomalies",
                "priority": "medium"
            })
        
        return recommendations


# ==================== DECORADOR DE INTEGRACIÓN ====================

def with_healing_integration(server_class):
    """Decorador para integrar auto-healing con clase de servidor MCP"""
    
    class HealingIntegratedServer(server_class):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.healing_integration = None
            self._healing_enabled = True
        
        async def initialize(self):
            """Inicializar servidor con integración de healing"""
            await super().initialize()
            
            # Configurar integración de healing si está habilitada
            if self._healing_enabled:
                self.healing_integration = HealingIntegration(self)
                await self.healing_integration.initialize()
        
        async def start(self):
            """Iniciar servidor con integración de healing"""
            await super().start()
            
            # Activar healing si está configurado
            if self.healing_integration and self._healing_enabled:
                await self.healing_integration.activate_healing()
        
        async def stop(self):
            """Detener servidor con limpieza de healing"""
            if self.healing_integration:
                await self.healing_integration.deactivate_healing()
            
            await super().stop()
        
        def enable_healing(self):
            """Habilitar auto-healing"""
            self._healing_enabled = True
        
        def disable_healing(self):
            """Deshabilitar auto-healing"""
            self._healing_enabled = False
        
        def is_healing_active(self) -> bool:
            """Verificar si auto-healing está activo"""
            return self.healing_integration and self.healing_integration.is_active()
    
    return HealingIntegratedServer


# ==================== FACTORY FUNCTION ====================

async def create_healing_integrated_server(original_server_class):
    """Crear servidor integrado con auto-healing"""
    return with_healing_integration(original_server_class)


if __name__ == "__main__":
    # Ejemplo de uso
    async def main():
        # Este sería el uso en el servidor real
        print("Healing Integration Example")
        
        # Simular servidor
        class MockServer:
            def __init__(self):
                self.reasoner_agent = MockAgent("reasoner")
                self.planner_agent = MockAgent("planner")
                self.executor_agent = MockAgent("executor")
                self.verifier_agent = MockAgent("verifier")
                self.memory_manager_agent = MockAgent("memory_manager")
                self.orchestrator = MockAgent("orchestrator")
                self.streaming_engine = MockAgent("streaming")
                self.mcp = MockMCP()
        
        class MockAgent:
            def __init__(self, name):
                self.name = name
                self.health_check_called = False
            
            async def health_check(self):
                self.health_check_called = True
                return {
                    "status": "healthy",
                    "metrics": {
                        "cpu_usage": 45.0,
                        "memory_usage": 60.0,
                        "response_time": 0.5,
                        "error_rate": 0.02,
                        "throughput": 25.0,
                        "active_tasks": 3,
                        "queue_size": 1
                    }
                }
        
        class MockMCP:
            def tool(self, func):
                return func
        
        # Crear servidor simulado
        server = MockServer()
        
        # Inicializar integración
        integration = HealingIntegration(server)
        await integration.initialize()
        
        # Activar healing
        success = await integration.activate_healing()
        print(f"Healing activation: {success}")
        
        # Obtener estado
        status = await integration.get_healing_status()
        print(json.dumps(status, indent=2, default=str))
    
    asyncio.run(main())