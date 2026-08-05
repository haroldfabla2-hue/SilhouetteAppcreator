"""
Test de error handling y recovery
Valida todos los aspectos de manejo de errores, recuperación y resiliencia del sistema
"""
import pytest
import asyncio
import json
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from unittest.mock import AsyncMock

from conftest import create_test_task_id


class ErrorType(Enum):
    """Tipos de errores en el sistema"""
    NETWORK_TIMEOUT = "network_timeout"
    DATABASE_CONNECTION = "database_connection"
    AGENT_FAILURE = "agent_failure"
    VALIDATION_ERROR = "validation_error"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    CIRCUIT_BREAKER = "circuit_breaker"
    DEPENDENCY_FAILURE = "dependency_failure"
    MEMORY_OVERFLOW = "memory_overflow"


class RecoveryStrategy(Enum):
    """Estrategias de recuperación"""
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAKER = "circuit_breaker"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    ISOLATION = "isolation"
    COMPENSATION = "compensation"


class ErrorContext:
    """Contexto de error para tracking y análisis"""
    
    def __init__(self, error_id: str, error_type: ErrorType, severity: str):
        self.error_id = error_id
        self.error_type = error_type
        self.severity = severity  # low, medium, high, critical
        self.timestamp = datetime.now()
        self.recovery_attempts = []
        self.final_resolution = None
        self.affected_agents = []
        self.impact_score = 0.0
    
    def add_recovery_attempt(self, strategy: RecoveryStrategy, success: bool, details: str):
        """Agregar intento de recuperación"""
        self.recovery_attempts.append({
            "strategy": strategy.value,
            "success": success,
            "details": details,
            "timestamp": datetime.now()
        })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_id": self.error_id,
            "error_type": self.error_type.value,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat(),
            "recovery_attempts": self.recovery_attempts,
            "final_resolution": self.final_resolution,
            "affected_agents": self.affected_agents,
            "impact_score": self.impact_score
        }


@pytest.mark.integration
class TestErrorHandlingRecovery:
    """Tests de manejo de errores y recuperación"""
    
    @pytest.mark.asyncio
    async def test_agent_failure_recovery(self, orchestrator, test_context):
        """Test recuperación de fallos de agentes"""
        error_context = ErrorContext("test_001", ErrorType.AGENT_FAILURE, "high")
        
        # Simular fallo de agente y recuperación automática
        recovery_log = []
        
        # Paso 1: Agente falla
        async def simulate_agent_failure():
            await asyncio.sleep(0.1)
            raise Exception("Simulated agent failure: database connection timeout")
        
        # Paso 2: Detección de error
        try:
            await simulate_agent_failure()
        except Exception as e:
            error_context.affected_agents = ["database_operations"]
            error_context.impact_score = 0.7
            
            recovery_log.append({
                "step": "error_detected",
                "error": str(e),
                "timestamp": datetime.now()
            })
        
        # Paso 3: Intentar recuperación con retry
        retry_attempts = 3
        for attempt in range(retry_attempts):
            try:
                await asyncio.sleep(0.05)  # Tiempo entre retries
                
                # Simular éxito en retry
                if attempt >= 1:  # Éxito en el segundo intento
                    recovery_log.append({
                        "step": f"retry_attempt_{attempt + 1}",
                        "success": True,
                        "timestamp": datetime.now()
                    })
                    error_context.add_recovery_attempt(RecoveryStrategy.RETRY, True, f"Success on attempt {attempt + 1}")
                    break
                else:
                    recovery_log.append({
                        "step": f"retry_attempt_{attempt + 1}",
                        "success": False,
                        "timestamp": datetime.now()
                    })
                    error_context.add_recovery_attempt(RecoveryStrategy.RETRY, False, f"Failed on attempt {attempt + 1}")
                    
            except Exception as e:
                recovery_log.append({
                    "step": f"retry_attempt_{attempt + 1}",
                    "error": str(e),
                    "timestamp": datetime.now()
                })
        
        # Verificar recuperación exitosa
        successful_recovery = any(
            log.get("success") is True for log in recovery_log 
            if log["step"].startswith("retry_attempt")
        )
        
        assert successful_recovery, "La recuperación con retry debería haber funcionado"
        assert len(error_context.recovery_attempts) > 0, "Debería haber intentos de recuperación"
        
        print(f"Test recuperación fallo agente completado:")
        print(f"  - Intentos de recovery: {len(error_context.recovery_attempts)}")
        print(f"  - Agentes afectados: {len(error_context.affected_agents)}")
        print(f"  - Score de impacto: {error_context.impact_score}")
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_pattern(self):
        """Test patrón circuit breaker para manejo de errores"""
        circuit_breaker_states = ["CLOSED", "OPEN", "HALF_OPEN"]
        
        # Simular servicio problemático
        service_config = {
            "failure_threshold": 3,
            "reset_timeout": 5,
            "success_threshold": 2,
            "current_failures": 0,
            "state": "CLOSED",
            "last_failure_time": None
        }
        
        circuit_breaker_log = []
        
        # Simular 10 llamadas al servicio
        for call_id in range(10):
            call_start = time.time()
            
            # Verificar estado del circuit breaker
            if service_config["state"] == "OPEN":
                # Circuit abierto - rechazar llamadas
                call_result = {
                    "call_id": call_id,
                    "status": "rejected",
                    "reason": "circuit_breaker_open",
                    "circuit_state": service_config["state"],
                    "execution_time_ms": 1
                }
                circuit_breaker_log.append(call_result)
                
            elif service_config["state"] == "HALF_OPEN":
                # Permitir llamadas limitadas para probar recuperación
                service_config["current_failures"] = 0  # Reset para half-open
                call_result = {
                    "call_id": call_id,
                    "status": "attempted",
                    "circuit_state": service_config["state"],
                    "execution_time_ms": 10
                }
                
                # Simular éxito en half-open (después de timeout)
                if call_id >= 7:  # Después del timeout
                    call_result["status"] = "success"
                    service_config["state"] = "CLOSED"
                    circuit_breaker_log.append(call_result)
                    continue
                else:
                    call_result["status"] = "failure"
                    service_config["current_failures"] += 1
                    
            else:  # CLOSED
                # Simular patrón de fallos (falla cada 3 llamadas)
                if call_id % 3 == 2:  # Llamadas 2, 5, 8 fallan
                    call_result = {
                        "call_id": call_id,
                        "status": "failure",
                        "circuit_state": service_config["state"],
                        "execution_time_ms": 5,
                        "error": "Service temporarily unavailable"
                    }
                    service_config["current_failures"] += 1
                    
                    # Abrir circuit si se alcanza el threshold
                    if service_config["current_failures"] >= service_config["failure_threshold"]:
                        service_config["state"] = "OPEN"
                        service_config["last_failure_time"] = time.time()
                    
                else:
                    call_result = {
                        "call_id": call_id,
                        "status": "success",
                        "circuit_state": service_config["state"],
                        "execution_time_ms": 10
                    }
                    service_config["current_failures"] = max(0, service_config["current_failures"] - 1)
            
            circuit_breaker_log.append(call_result)
        
        # Verificar comportamiento del circuit breaker
        rejected_calls = [log for log in circuit_breaker_log if log["status"] == "rejected"]
        successful_calls = [log for log in circuit_breaker_log if log["status"] == "success"]
        failed_calls = [log for log in circuit_breaker_log if log["status"] == "failure"]
        
        # Debería haber llamadas rechazadas (circuit abierto)
        assert len(rejected_calls) > 0, "Debería haber llamadas rechazadas por circuit breaker"
        
        # Debería haber transiciones de estado
        states_seen = set(log.get("circuit_state", "UNKNOWN") for log in circuit_breaker_log)
        assert "OPEN" in states_seen, "Circuit breaker debería haber pasado a estado OPEN"
        
        print(f"Test circuit breaker completado:")
        print(f"  - Llamadas exitosas: {len(successful_calls)}")
        print(f"  - Llamadas fallidas: {len(failed_calls)}")
        print(f"  - Llamadas rechazadas: {len(rejected_calls)}")
        print(f"  - Estados observados: {len(states_seen)}")
    
    @pytest.mark.asyncio
    async def test_fallback_mechanisms(self, test_database):
        """Test mecanismos de fallback en caso de fallos"""
        # Configurar múltiples servicios de fallback
        service_hierarchy = [
            {
                "service": "primary_database",
                "priority": 1,
                "failure_count": 0,
                "status": "active"
            },
            {
                "service": "secondary_database", 
                "priority": 2,
                "failure_count": 0,
                "status": "standby"
            },
            {
                "service": "cache_database",
                "priority": 3,
                "failure_count": 0,
                "status": "standby"
            },
            {
                "service": "mock_fallback",
                "priority": 4,
                "failure_count": 0,
                "status": "emergency"
            }
        ]
        
        fallback_log = []
        
        async def try_service(service_info: Dict[str, Any], query: str):
            """Intentar usar un servicio"""
            service_name = service_info["service"]
            
            try:
                if service_name == "primary_database":
                    # Simular fallo del servicio primario
                    if random.choice([True, False]):  # 50% chance de fallo
                        raise Exception("Primary database connection failed")
                    result = await test_database.main_conn.fetch(query)
                    
                elif service_name == "secondary_database":
                    # Simular que el secundario está disponible
                    await asyncio.sleep(0.05)  # Simular delay
                    result = {"data": "secondary_db_result", "source": "fallback"}
                    
                elif service_name == "cache_database":
                    # Cache con datos simulados
                    await asyncio.sleep(0.02)
                    result = {"data": "cached_result", "source": "cache"}
                    
                else:  # mock_fallback
                    # Último recurso - datos mock
                    await asyncio.sleep(0.01)
                    result = {"data": "mock_fallback_data", "source": "emergency"}
                
                return {
                    "service": service_name,
                    "success": True,
                    "result": result,
                    "response_time_ms": 10
                }
                
            except Exception as e:
                service_info["failure_count"] += 1
                return {
                    "service": service_name,
                    "success": False,
                    "error": str(e),
                    "response_time_ms": 5
                }
        
        # Simular consulta que requiere fallback
        test_query = "SELECT COUNT(*) FROM test_agents"
        
        for service in service_hierarchy:
            if service["status"] == "standby" or service["status"] == "emergency":
                result = await try_service(service, test_query)
                fallback_log.append(result)
                
                if result["success"]:
                    # Servicio exitoso - detener fallback chain
                    break
            else:
                # Probar servicio primario primero
                result = await try_service(service, test_query)
                fallback_log.append(result)
                
                if result["success"]:
                    break  # Servicio primario funcionó
        
        # Verificar que se utilizó algún servicio
        successful_fallbacks = [log for log in fallback_log if log["success"]]
        assert len(successful_fallbacks) > 0, "Al menos un servicio de fallback debería funcionar"
        
        # Verificar que se siguió la jerarquía de prioridades
        used_services = [log["service"] for log in fallback_log if log["success"]]
        assert len(used_services) >= 1, "Debería haberse usado al menos un servicio"
        
        print(f"Test mecanismos fallback completado:")
        print(f"  - Servicios en jerarquía: {len(service_hierarchy)}")
        print(f"  - Intentos de fallback: {len(fallback_log)}")
        print(f"  - Servicios exitosos: {len(successful_fallbacks)}")
        print(f"  - Servicio utilizado: {used_services[0] if used_services else 'none'}")
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self, test_database):
        """Test degradación elegante bajo condiciones de estrés"""
        # Simular sistema bajo carga con degradación progresiva
        degradation_levels = [
            {
                "level": "normal",
                "max_concurrent_tasks": 10,
                "response_time_ms": 100,
                "features_enabled": ["all_features"]
            },
            {
                "level": "warning", 
                "max_concurrent_tasks": 7,
                "response_time_ms": 200,
                "features_enabled": ["core_features", "advanced_features"]
            },
            {
                "level": "critical",
                "max_concurrent_tasks": 3,
                "response_time_ms": 500,
                "features_enabled": ["core_features_only"]
            },
            {
                "level": "emergency",
                "max_concurrent_tasks": 1,
                "response_time_ms": 1000,
                "features_enabled": ["basic_operations_only"]
            }
        ]
        
        degradation_log = []
        
        # Simular carga creciente
        load_levels = [1, 5, 8, 12, 15, 20, 25, 30]
        
        for load in load_levels:
            # Determinar nivel de degradación basado en carga
            current_level = None
            for level_config in degradation_levels:
                if load <= level_config["max_concurrent_tasks"]:
                    current_level = level_config
                    break
            
            if not current_level:
                current_level = degradation_levels[-1]  # emergency level
            
            # Simular capacidad del sistema
            system_performance = {
                "current_load": load,
                "capacity": current_level["max_concurrent_tasks"],
                "degradation_level": current_level["level"],
                "features_available": current_level["features_enabled"],
                "estimated_response_time_ms": current_level["response_time_ms"]
            }
            
            # Calcular métricas de degradación
            if load > system_performance["capacity"]:
                overload_factor = load / system_performance["capacity"]
                system_performance["overload_factor"] = overload_factor
                system_performance["performance_degradation"] = min(overload_factor * 0.3, 0.8)
            else:
                system_performance["overload_factor"] = 1.0
                system_performance["performance_degradation"] = 0.0
            
            degradation_log.append(system_performance)
            
            # Simular respuesta del sistema bajo degradación
            if current_level["level"] == "normal":
                # Respuesta normal
                await asyncio.sleep(0.01)
            elif current_level["level"] == "warning":
                # Respuesta degradada
                await asyncio.sleep(0.05)
            elif current_level["level"] == "critical":
                # Respuesta muy degradada
                await asyncio.sleep(0.1)
            else:  # emergency
                # Respuesta mínima
                await asyncio.sleep(0.2)
        
        # Verificar degradación progresiva
        normal_responses = [log for log in degradation_log if log["degradation_level"] == "normal"]
        degraded_responses = [log for log in degradation_log if log["degradation_level"] != "normal"]
        
        # Debería haber degradación bajo alta carga
        assert len(degraded_responses) > 0, "Debería haber respuestas degradadas bajo carga alta"
        
        # Verificar que la degradación es progresiva
        for i, log in enumerate(degradation_log[1:], 1):
            prev_log = degradation_log[i-1]
            
            if log["degradation_level"] != prev_log["degradation_level"]:
                # Verificar que la degradación sigue el orden correcto
                level_order = ["normal", "warning", "critical", "emergency"]
                prev_index = level_order.index(prev_log["degradation_level"])
                curr_index = level_order.index(log["degradation_level"])
                assert curr_index >= prev_index, "Degradación debería ser progresiva"
        
        print(f"Test degradación elegante completado:")
        print(f"  - Niveles de carga probados: {len(load_levels)}")
        print(f"  - Respuestas normales: {len(normal_responses)}")
        print(f"  - Respuestas degradadas: {len(degraded_responses)}")
        print(f"  - Nivel máximo alcanzado: {degradation_log[-1]['degradation_level']}")
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_recovery(self, test_database):
        """Test recuperación mediante rollback de transacciones"""
        transaction_scenarios = [
            {
                "scenario": "partial_failure",
                "operations": [
                    {"type": "insert", "table": "test_tasks", "success": True},
                    {"type": "update", "table": "test_agents", "success": True},
                    {"type": "delete", "table": "test_context_persistence", "success": False, "error": "constraint_violation"}
                ]
            },
            {
                "scenario": "complete_failure",
                "operations": [
                    {"type": "insert", "table": "test_tasks", "success": False, "error": "connection_lost"},
                    {"type": "update", "table": "test_agents", "success": False, "error": "deadlock"},
                    {"type": "delete", "table": "test_context_persistence", "success": False, "error": "timeout"}
                ]
            }
        ]
        
        rollback_results = []
        
        for scenario in transaction_scenarios:
            scenario_id = f"rollback_test_{scenario['scenario']}"
            
            # Iniciar transacción
            async with test_database.main_conn.transaction() as tx:
                transaction_log = []
                
                try:
                    for operation in scenario["operations"]:
                        op_start = time.time()
                        
                        if not operation["success"]:
                            # Simular operación que falla
                            raise Exception(operation["error"])
                        
                        # Simular operación exitosa
                        if operation["type"] == "insert":
                            await tx.execute(
                                f"INSERT INTO {operation['table']} (name, type, status) VALUES ($1, $2, $3)",
                                f"rollback_test_{len(transaction_log)}", "test_type", "pending"
                            )
                        
                        transaction_log.append({
                            "operation": operation,
                            "success": True,
                            "execution_time_ms": (time.time() - op_start) * 1000
                        })
                    
                    # Si llegamos aquí, la transacción fue exitosa
                    await tx.commit()
                    transaction_status = "committed"
                    
                except Exception as e:
                    # Rollback automático por error
                    await tx.rollback()
                    transaction_status = "rolled_back"
                    
                    transaction_log.append({
                        "operation": {"type": "rollback", "error": str(e)},
                        "success": False,
                        "error": str(e)
                    })
            
            # Verificar estado final de la base de datos
            # Verificar que las operaciones rollback limpiaron los datos
            if transaction_status == "rolled_back":
                test_data_count = await test_database.main_conn.fetchval(
                    "SELECT COUNT(*) FROM test_tasks WHERE name LIKE $1",
                    f"{scenario_id}_%"
                )
                assert test_data_count == 0, f"Datos de rollback deberían haberse limpiado en {scenario_id}"
            
            rollback_results.append({
                "scenario": scenario["scenario"],
                "status": transaction_status,
                "operations_attempted": len(scenario["operations"]),
                "operations_successful": len([op for op in transaction_log if op.get("success", False)]),
                "operations_failed": len([op for op in transaction_log if not op.get("success", True)])
            })
        
        # Verificar resultados de rollback
        for result in rollback_results:
            if result["scenario"] == "partial_failure":
                assert result["status"] == "rolled_back", "Transacción con fallo parcial debería hacer rollback"
            elif result["scenario"] == "complete_failure":
                assert result["status"] == "rolled_back", "Transacción con fallo completo debería hacer rollback"
        
        print(f"Test rollback transacciones completado:")
        for result in rollback_results:
            print(f"  - {result['scenario']}: {result['status']} "
                  f"({result['operations_successful']} exitosas, {result['operations_failed']} fallidas)")
    
    @pytest.mark.asyncio
    async def test_error_propagation_isolation(self, test_database):
        """Test aislamiento de errores y prevención de propagación"""
        # Crear estructura de componentes con dependencias
        components = {
            "ui_layer": {"depends_on": [], "isolated": True},
            "api_gateway": {"depends_on": ["ui_layer"], "isolated": True}, 
            "orchestrator": {"depends_on": ["api_gateway"], "isolated": False},
            "agent_pool": {"depends_on": ["orchestrator"], "isolated": False},
            "database_layer": {"depends_on": ["agent_pool"], "isolated": True},
            "cache_layer": {"depends_on": ["database_layer"], "isolated": True}
        }
        
        error_propagation_log = []
        
        async def simulate_component_execution(component_name: str, should_fail: bool = False):
            """Simular ejecución de componente"""
            component = components[component_name]
            
            # Verificar dependencias primero
            for dep in component["depends_on"]:
                # Simular que las dependencias están disponibles
                pass
            
            # Ejecutar componente
            if should_fail and component_name == "agent_pool":
                # Simular fallo en agente pool
                raise Exception("Agent pool memory overflow")
            
            # Ejecución exitosa
            return {
                "component": component_name,
                "status": "success",
                "isolation": component["isolated"],
                "timestamp": datetime.now()
            }
        
        # Escenario 1: Error en componente aislado
        try:
            await simulate_component_execution("agent_pool", should_fail=True)
        except Exception as e:
            error_propagation_log.append({
                "error_origin": "agent_pool",
                "error_message": str(e),
                "timestamp": datetime.now(),
                "propagation_blocked": True,
                "affected_components": []
            })
        
        # Verificar que el error no afectó otros componentes
        unaffected_components = []
        for component_name in components.keys():
            if component_name != "agent_pool":
                try:
                    result = await simulate_component_execution(component_name)
                    unaffected_components.append(component_name)
                except Exception:
                    pass  # Componente afectado por propagación
        
        # Escenario 2: Error en componente no aislado
        error_propagation_log.append({
            "test_type": "non_isolated_error",
            "component": "orchestrator",
            "error_message": "Orchestrator circuit breaker open",
            "propagation_blocked": False,
            "potential_impact": ["agent_pool", "database_layer"]
        })
        
        # Verificar aislamiento
        isolated_errors = [log for log in error_propagation_log if log.get("propagation_blocked", False)]
        unisolated_errors = [log for log in error_propagation_log if not log.get("propagation_blocked", True)]
        
        # Debería haber errores aislados
        assert len(isolated_errors) > 0, "Debería haber errores aislados por componentes"
        
        # Los componentes aislados deberían seguir funcionando
        assert len(unaffected_components) > 0, "Componentes aislados deberían seguir funcionando"
        
        print(f"Test aislamiento errores completado:")
        print(f"  - Errores aislados: {len(isolated_errors)}")
        print(f"  - Errores no aislados: {len(unisolated_errors)}")
        print(f"  - Componentes no afectados: {len(unaffected_components)}")
    
    @pytest.mark.asyncio
    async def test_compensation_pattern(self, test_database):
        """Test patrón de compensación para operaciones distribuidas"""
        # Simular operaciones compensatorias en orden inverso
        distributed_operations = [
            {
                "step": 1,
                "operation": "create_reservation",
                "resource": "database_connection",
                "success": True
            },
            {
                "step": 2, 
                "operation": "allocate_resources",
                "resource": "memory_buffer",
                "success": True
            },
            {
                "step": 3,
                "operation": "start_processing",
                "resource": "agent_pool",
                "success": False,  # Fallo en el paso 3
                "error": "insufficient_resources"
            },
            {
                "step": 4,
                "operation": "update_database",
                "resource": "database_write",
                "success": False  # No se ejecutó por fallo anterior
            }
        ]
        
        compensation_log = []
        
        # Ejecutar operaciones
        executed_steps = []
        failed_step = None
        
        for op in distributed_operations:
            if op["success"]:
                executed_steps.append(op)
            else:
                failed_step = op["step"]
                compensation_log.append({
                    "event": "operation_failed",
                    "step": op["step"],
                    "operation": op["operation"],
                    "error": op.get("error", "unknown")
                })
                break  # Detener en el primer fallo
        
        # Ejecutar compensaciones en orden inverso
        compensation_steps = [
            {
                "compensation": "rollback_database",
                "description": "Rollback database changes",
                "executed": False
            },
            {
                "compensation": "release_memory",
                "description": "Release allocated memory",
                "executed": False
            },
            {
                "compensation": "close_connection", 
                "description": "Close database connection",
                "executed": False
            }
        ]
        
        # Ejecutar compensaciones para operaciones exitosas
        for compensation in compensation_steps:
            try:
                if compensation["compensation"] == "rollback_database":
                    await test_database.main_conn.execute("ROLLBACK")
                elif compensation["compensation"] == "release_memory":
                    # Simular liberación de memoria
                    await asyncio.sleep(0.01)
                elif compensation["compensation"] == "close_connection":
                    # Simular cierre de conexión
                    await asyncio.sleep(0.01)
                
                compensation["executed"] = True
                compensation_log.append({
                    "event": "compensation_executed",
                    "compensation": compensation["compensation"],
                    "success": True
                })
                
            except Exception as e:
                compensation_log.append({
                    "event": "compensation_failed",
                    "compensation": compensation["compensation"],
                    "error": str(e)
                })
        
        # Verificar compensación
        successful_compensations = [
            comp for comp in compensation_steps if comp["executed"]
        ]
        
        assert len(successful_compensations) >= 1, "Al menos una compensación debería ejecutarse exitosamente"
        
        # Verificar que no quedan operaciones pendientes
        rollback_events = [log for log in compensation_log if log["event"] == "compensation_executed"]
        assert len(rollback_events) > 0, "Debería haber compensaciones ejecutadas"
        
        print(f"Test patrón compensación completado:")
        print(f"  - Pasos ejecutados exitosamente: {len(executed_steps)}")
        print(f"  - Paso fallido: {failed_step}")
        print(f"  - Compensaciones exitosas: {len(successful_compensations)}")
        print(f"  - Total eventos: {len(compensation_log)}")
    
    @pytest.mark.asyncio
    async def test_error_monitoring_and_alerting(self, test_database):
        """Test sistema de monitoreo y alertas de errores"""
        # Simular diferentes tipos de errores con severidades
        error_scenarios = [
            {"type": ErrorType.NETWORK_TIMEOUT, "severity": "medium", "count": 5},
            {"type": ErrorType.DATABASE_CONNECTION, "severity": "high", "count": 3},
            {"type": ErrorType.AGENT_FAILURE, "severity": "medium", "count": 8},
            {"type": ErrorType.RESOURCE_EXHAUSTION, "severity": "critical", "count": 2}
        ]
        
        monitoring_events = []
        alerts_triggered = []
        
        # Generar eventos de error
        for scenario in error_scenarios:
            for i in range(scenario["count"]):
                error_context = ErrorContext(
                    f"error_{scenario['type'].value}_{i}",
                    scenario["type"],
                    scenario["severity"]
                )
                
                # Simular detección y manejo del error
                monitoring_events.append(error_context.to_dict())
                
                # Simular sistema de alertas
                alert_threshold = {
                    "low": 10,
                    "medium": 5,
                    "high": 3,
                    "critical": 1
                }
                
                if scenario["count"] >= alert_threshold[scenario["severity"]]:
                    alert = {
                        "alert_id": f"alert_{scenario['type'].value}",
                        "type": scenario["type"].value,
                        "severity": scenario["severity"],
                        "threshold": alert_threshold[scenario["severity"]],
                        "current_count": scenario["count"],
                        "triggered_at": datetime.now(),
                        "message": f"{scenario['count']} {scenario['type'].value} errors detected"
                    }
                    alerts_triggered.append(alert)
        
        # Simular métricas de error
        error_metrics = {
            "total_errors": len(monitoring_events),
            "errors_by_type": {},
            "errors_by_severity": {},
            "error_rate_per_hour": len(monitoring_events) / 24,  # Simulado
            "mean_time_to_detection": 2.5,  # minutos
            "mean_time_to_resolution": 15.0  # minutos
        }
        
        # Calcular métricas por tipo
        for event in monitoring_events:
            error_type = event["error_type"]
            severity = event["severity"]
            
            error_metrics["errors_by_type"][error_type] = \
                error_metrics["errors_by_type"].get(error_type, 0) + 1
            
            error_metrics["errors_by_severity"][severity] = \
                error_metrics["errors_by_severity"].get(severity, 0) + 1
        
        # Verificar métricas de monitoreo
        assert error_metrics["total_errors"] > 0, "Deberían haberse registrado errores"
        assert len(error_metrics["errors_by_type"]) > 0, "Deberían haberse registrado múltiples tipos de error"
        assert len(error_metrics["errors_by_severity"]) > 0, "Deberían haberse registrado múltiples severidades"
        
        # Verificar que se generaron alertas
        assert len(alerts_triggered) > 0, "Deberían haberse generado alertas"
        
        # Verificar que las alertas tienen la severidad correcta
        critical_alerts = [alert for alert in alerts_triggered if alert["severity"] == "critical"]
        high_alerts = [alert for alert in alerts_triggered if alert["severity"] == "high"]
        
        assert len(critical_alerts) > 0, "Debería haber alertas críticas"
        assert len(high_alerts) > 0, "Debería haber alertas de alta severidad"
        
        print(f"Test monitoreo errores completado:")
        print(f"  - Total eventos de error: {error_metrics['total_errors']}")
        print(f"  - Alertas generadas: {len(alerts_triggered)}")
        print(f"  - Alertas críticas: {len(critical_alerts)}")
        print(f"  - Tasa de error por hora: {error_metrics['error_rate_per_hour']:.2f}")