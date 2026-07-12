"""
Ejemplo Completo del Sistema de Auto-Healing para MCP Core Superior
Demuestra el uso de todos los componentes del sistema de auto-healing
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# Importar componentes del sistema de auto-healing
from src.core import (
    AutoHealingEngine,
    HealthMetrics,
    HealthStatus,
    ErrorEvent,
    RecoveryStrategy,
    CircuitBreaker,
    PredictiveFailureDetector,
    HealthMetricsCollector,
    MetricsAggregator,
    AutoHealingConfiguration,
    ConfigurationManager,
    HealingIntegration,
    with_healing_integration,
    get_auto_healing_engine,
    get_metrics_collector,
    get_config_manager
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class MockAgent:
    """Mock agent para demostrar el sistema"""
    
    def __init__(self, name: str):
        self.name = name
        self.health_status = HealthStatus.HEALTHY
        self.execution_count = 0
        self.error_count = 0
        self.total_execution_time = 0.0
    
    async def health_check(self) -> Dict[str, Any]:
        """Simular health check del agente"""
        # Simular métricas variables
        import random
        
        return {
            "status": self.health_status.value,
            "metrics": {
                "cpu_usage": random.uniform(20, 80),
                "memory_usage": random.uniform(30, 70),
                "response_time": random.uniform(0.1, 2.0),
                "error_rate": self.error_count / max(1, self.execution_count),
                "throughput": random.uniform(10, 50),
                "active_tasks": random.randint(0, 5),
                "queue_size": random.randint(0, 10)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def execute_task(self, task: str) -> Dict[str, Any]:
        """Simular ejecución de tarea"""
        import random
        import time
        
        self.execution_count += 1
        start_time = time.time()
        
        # Simular posibles fallos
        if random.random() < 0.1:  # 10% chance of failure
            self.error_count += 1
            error_msg = f"Task {task} failed"
            logger.error(f"{self.name}: {error_msg}")
            raise Exception(error_msg)
        
        # Simular tiempo de ejecución
        execution_time = random.uniform(0.5, 3.0)
        await asyncio.sleep(execution_time)
        
        self.total_execution_time += execution_time
        
        return {
            "agent": self.name,
            "task": task,
            "result": f"Task {task} completed successfully",
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }


class MockServer:
    """Mock servidor para demostrar integración"""
    
    def __init__(self):
        self.name = "Mock MCP Server"
        self.agents = {
            "reasoner": MockAgent("reasoner"),
            "planner": MockAgent("planner"),
            "executor": MockAgent("executor"),
            "verifier": MockAgent("verifier"),
            "memory_manager": MockAgent("memory_manager")
        }
        self.is_running = False
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check del servidor completo"""
        agent_statuses = {}
        for name, agent in self.agents.items():
            try:
                status = await agent.health_check()
                agent_statuses[name] = status
            except Exception as e:
                agent_statuses[name] = {"status": "error", "error": str(e)}
        
        return {
            "server_status": "healthy" if self.is_running else "stopped",
            "agents": agent_statuses,
            "timestamp": datetime.now().isoformat()
        }


async def demonstrate_basic_auto_healing():
    """Demostración básica del motor de auto-healing"""
    logger.info("=== DEMO: Auto-Healing Engine Básico ===")
    
    # Crear motor de auto-healing
    engine = AutoHealingEngine()
    await engine.initialize()
    
    # Simular algunos agentes
    agents = ["reasoner", "planner", "executor"]
    
    # Simular métricas de agentes
    for i in range(20):
        for agent_name in agents:
            # Crear métricas con variabilidad
            import random
            health_score = random.uniform(0.3, 1.0)
            
            # Simular degradación gradual
            if i > 15:
                health_score = random.uniform(0.1, 0.5)  # Agents getting worse
            
            metrics = HealthMetrics(
                timestamp=datetime.now(),
                agent_name=agent_name,
                cpu_usage=random.uniform(20, 90),
                memory_usage=random.uniform(30, 85),
                response_time=random.uniform(0.1, 3.0),
                error_rate=random.uniform(0, 0.15),
                throughput=random.uniform(5, 40),
                active_tasks=random.randint(0, 8),
                queue_size=random.randint(0, 15),
                health_score=health_score
            )
            
            await engine.record_health_metrics(agent_name, metrics)
        
        await asyncio.sleep(0.5)  # Pequeña pausa entre mediciones
    
    # Mostrar estado final
    status = engine.get_health_status()
    print("\n--- Estado Final del Sistema ---")
    print(json.dumps(status, indent=2, default=str))
    
    # Obtener predicciones de fallo
    predictions = engine.get_failure_predictions()
    print(f"\n--- Predicciones de Fallo ---")
    for agent, prob in predictions.items():
        print(f"{agent}: {prob:.2%}")
    
    # Obtener anomalías detectadas
    anomalies = engine.get_anomalies()
    print(f"\n--- Anomalías Detectadas ({len(anomalies)}) ---")
    for anomaly in anomalies[:5]:  # Mostrar solo las primeras 5
        print(f"  {anomaly['timestamp']} - {anomaly['agent_name']}: {', '.join(anomaly['anomalies'])}")
    
    await engine.cleanup()


async def demonstrate_metrics_collection():
    """Demostración del sistema de recolección de métricas"""
    logger.info("=== DEMO: Recolección de Métricas ===")
    
    # Crear recolector de métricas
    collector = HealthMetricsCollector(collection_interval=2)
    await collector.start_collection()
    
    # Simular datos de aplicación
    async def simulate_application_work():
        """Simular trabajo de la aplicación"""
        for i in range(15):
            # Simular requests con diferentes tiempos de respuesta
            response_time = 0.1 + (i * 0.1)  # Gradualmente más lento
            collector.record_response_time("api/request", response_time)
            
            # Simular ejecución de agentes
            for agent_name in ["reasoner", "planner", "executor"]:
                execution_time = 0.2 + (i * 0.05)
                collector.record_execution_time(agent_name, execution_time)
            
            await asyncio.sleep(1)
    
    # Ejecutar simulación
    await simulate_application_work()
    
    # Obtener métricas actuales
    current_metrics = collector.get_current_metrics()
    print("\n--- Métricas Actuales ---")
    print(json.dumps(current_metrics, indent=2, default=str))
    
    # Generar reporte de rendimiento
    aggregator = MetricsAggregator(collector)
    report = aggregator.generate_performance_report(timedelta(minutes=2))
    print("\n--- Reporte de Rendimiento ---")
    print(json.dumps(report, indent=2, default=str))
    
    await collector.stop_collection()


async def demonstrate_configuration_management():
    """Demostración del sistema de configuración"""
    logger.info("=== DEMO: Gestión de Configuración ===")
    
    # Crear gestor de configuración
    manager = await get_config_manager()
    config = manager.get_config()
    
    print("\n--- Configuración Actual ---")
    print(f"Auto-healing habilitado: {config.enabled}")
    print(f"Modo debug: {config.debug_mode}")
    print(f"Intervalo de monitoreo: {config.monitoring_interval}s")
    print(f"Umbrales globales:")
    print(f"  CPU warning: {config.global_thresholds.cpu_warning}%")
    print(f"  Memory warning: {config.global_thresholds.memory_warning}%")
    print(f"  Error rate warning: {config.global_thresholds.error_rate_warning:.1%}")
    
    # Mostrar configuración de agentes
    print(f"\n--- Configuración de Agentes ---")
    for agent_name, agent_config in config.agent_configs.items():
        print(f"{agent_name}:")
        print(f"  Min instances: {agent_config.min_instances}")
        print(f"  Max instances: {agent_config.max_instances}")
        print(f"  Circuit breaker threshold: {agent_config.circuit_breaker_failure_threshold}")
        print(f"  Recovery strategies: {[s.value for s in agent_config.recovery_strategies]}")
    
    # Actualizar configuración
    print(f"\n--- Actualizando Configuración ---")
    updates = {
        "enabled": True,
        "debug_mode": True,
        "global_thresholds": {
            "cpu_warning": 65.0,
            "memory_warning": 75.0,
            "error_rate_warning": 0.03
        }
    }
    
    success = await manager.update_config(updates)
    print(f"Actualización exitosa: {success}")
    
    if success:
        new_config = manager.get_config()
        print(f"Nuevo umbral de CPU: {new_config.global_thresholds.cpu_warning}%")
        print(f"Nuevo umbral de memoria: {new_config.global_thresholds.memory_warning}%")
        print(f"Nuevo umbral de error rate: {new_config.global_thresholds.error_rate_warning:.1%}")
    
    # Obtener configuración específica de agente
    executor_config = manager.get_agent_config("executor")
    print(f"\n--- Configuración Específica del Executor ---")
    print(json.dumps(executor_config.to_dict(), indent=2))


async def demonstrate_integration():
    """Demostración de la integración completa"""
    logger.info("=== DEMO: Integración Completa ===")
    
    # Crear servidor mock
    server = MockServer()
    server.is_running = True
    
    # Crear integración
    integration = HealingIntegration(server)
    await integration.initialize()
    
    # Activar healing
    activated = await integration.activate_healing()
    print(f"Healing activado: {activated}")
    
    # Simular trabajo del servidor con posibles fallos
    async def simulate_server_work():
        """Simular trabajo del servidor con fallos ocasionales"""
        tasks = [
            "analyze_request", "create_plan", "execute_task", 
            "validate_result", "store_memory"
        ]
        
        for i in range(10):
            task = tasks[i % len(tasks)]
            agent_name = ["reasoner", "planner", "executor", "verifier", "memory_manager"][i % 5]
            
            try:
                # Simular ejecución con posibilidad de fallo
                if i == 6:  # Fallo en el 6to intento
                    raise Exception(f"Simulated failure for {agent_name}")
                
                result = await server.agents[agent_name].execute_task(task)
                print(f"✓ {agent_name}: {result['result']}")
                
                # Reportar ejecución exitosa
                await integration._report_agent_execution(agent_name, True, 1.0)
                
            except Exception as e:
                print(f"✗ {agent_name}: {str(e)}")
                
                # Reportar error al sistema de auto-healing
                error_event = ErrorEvent(
                    timestamp=datetime.now(),
                    error_type="ExecutionError",
                    severity="error",
                    source=agent_name,
                    message=str(e),
                    context={"task": task, "attempt": i + 1}
                )
                await integration.auto_healing_engine.record_error(error_event)
                
                # Reportar ejecución fallida
                await integration._report_agent_execution(agent_name, False, 1.0)
            
            await asyncio.sleep(0.5)
    
    # Ejecutar simulación
    await simulate_server_work()
    
    # Obtener estado completo del sistema
    status = await integration.get_healing_status()
    print(f"\n--- Estado Completo del Sistema ---")
    print(json.dumps(status, indent=2, default=str))
    
    # Obtener recomendaciones
    recommendations = await integration.get_healing_recommendations()
    print(f"\n--- Recomendaciones del Sistema ---")
    if recommendations:
        for rec in recommendations:
            print(f"  {rec['priority'].upper()}: {rec['recommendation']} para {rec['agent']}")
    else:
        print("  No hay recomendaciones en este momento")
    
    # Obtener estadísticas de integración
    stats = integration.get_integration_stats()
    print(f"\n--- Estadísticas de Integración ---")
    print(f"Eventos de healing: {stats['total_healing_events']}")
    print(f"Healing exitoso: {stats['successful_heals']}")
    print(f"Healing fallido: {stats['failed_heals']}")
    
    # Desactivar healing
    await integration.deactivate_healing()
    print("\nHealing desactivado")


async def demonstrate_circuit_breaker():
    """Demostración del patrón Circuit Breaker"""
    logger.info("=== DEMO: Circuit Breaker Pattern ===")
    
    from src.core.auto_healing_engine import CircuitBreakerConfig, CircuitState
    
    # Crear circuit breaker
    def failing_function():
        raise Exception("Simulated failure")
    
    def fallback_function(*args, **kwargs):
        return "Fallback response - service is down"
    
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=5,
        expected_exception=Exception,
        fallback_function=fallback_function
    )
    
    circuit_breaker = CircuitBreaker(config)
    
    print("Circuit Breaker estados:")
    print(f"Estado inicial: {circuit_breaker.state.value}")
    
    # Intentar llamadas que fallan
    for i in range(5):
        try:
            result = circuit_breaker.call(failing_function)
            print(f"Llamada {i+1}: {result}")
        except Exception as e:
            print(f"Llamada {i+1}: Falló - {str(e)}")
    
    # Mostrar estado después de fallos
    state = circuit_breaker.get_state()
    print(f"\nEstado después de fallos:")
    print(json.dumps(state, indent=2, default=str))
    
    # Esperar y probar recuperación
    print("\nEsperando tiempo de recuperación...")
    await asyncio.sleep(6)
    
    # Intentar llamada que funciona
    def working_function():
        return "Service is back online"
    
    try:
        result = circuit_breaker.call(working_function)
        print(f"Después de recuperación: {result}")
    except Exception as e:
        print(f"Después de recuperación falló: {str(e)}")
    
    # Estado final
    final_state = circuit_breaker.get_state()
    print(f"\nEstado final:")
    print(json.dumps(final_state, indent=2, default=str))


async def demonstrate_predictive_detection():
    """Demostración de detección predictiva de fallos"""
    logger.info("=== DEMO: Detección Predictiva de Fallos ===")
    
    detector = PredictiveFailureDetector(window_size=20)
    
    # Simular métricas de un agente que está degradándose
    print("Simulando degradación gradual de un agente...")
    
    import random
    
    for i in range(25):
        # Crear métricas que empeoran progresivamente
        degradation_factor = max(0, (i - 15) / 10)  # Empieza a degradar después del punto 15
        
        metrics = HealthMetrics(
            timestamp=datetime.now(),
            agent_name="degrading_agent",
            cpu_usage=50 + (degradation_factor * 40),  # CPU sube
            memory_usage=60 + (degradation_factor * 30),  # Memory sube
            response_time=0.5 + (degradation_factor * 2.0),  # Response time sube
            error_rate=0.01 + (degradation_factor * 0.1),  # Error rate sube
            throughput=30 - (degradation_factor * 20),  # Throughput baja
            active_tasks=5 + int(degradation_factor * 3),
            queue_size=2 + int(degradation_factor * 8),
            health_score=0.9 - (degradation_factor * 0.5)  # Health score baja
        )
        
        detector.record_metrics("degrading_agent", metrics)
        
        # Mostrar predicción cada 5 mediciones
        if i % 5 == 4:
            probability = detector.predict_failure_probability("degrading_agent")
            print(f"Después de {i+1} mediciones - Probabilidad de fallo: {probability:.1%}")
        
        await asyncio.sleep(0.1)
    
    # Detectar anomalías
    anomalies = detector.detect_anomalies("degrading_agent")
    print(f"\nAnomalías detectadas ({len(anomalies)}):")
    for anomaly in anomalies[-5:]:  # Últimas 5 anomalías
        print(f"  {anomaly['timestamp']}: {', '.join(anomaly['anomalies'])}")
    
    # Probabilidad final
    final_probability = detector.predict_failure_probability("degrading_agent")
    print(f"\nProbabilidad final de fallo: {final_probability:.1%}")


async def main():
    """Función principal que ejecuta todas las demostraciones"""
    print("🚀 Iniciando Demostración del Sistema de Auto-Healing MCP Core Superior")
    print("=" * 80)
    
    demonstrations = [
        ("Auto-Healing Engine Básico", demonstrate_basic_auto_healing),
        ("Recolección de Métricas", demonstrate_metrics_collection),
        ("Gestión de Configuración", demonstrate_configuration_management),
        ("Circuit Breaker Pattern", demonstrate_circuit_breaker),
        ("Detección Predictiva", demonstrate_predictive_detection),
        ("Integración Completa", demonstrate_integration)
    ]
    
    for demo_name, demo_function in demonstrations:
        print(f"\n{'=' * 20} {demo_name} {'=' * 20}")
        try:
            await demo_function()
            print(f"✅ {demo_name} completado exitosamente")
        except Exception as e:
            print(f"❌ Error en {demo_name}: {str(e)}")
            logger.exception(f"Error in {demo_name}")
        
        print("-" * 80)
    
    print("\n🎉 Todas las demostraciones completadas")
    print("El sistema de auto-healing está listo para integración con MCP Core Superior")


if __name__ == "__main__":
    asyncio.run(main())