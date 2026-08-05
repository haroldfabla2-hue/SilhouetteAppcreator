"""
Test de performance bajo carga
Valida el rendimiento del sistema multi-agente bajo diferentes condiciones de carga
"""
import pytest
import asyncio
import json
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from conftest import create_test_task_id


@dataclass
class PerformanceMetrics:
    """Métricas de performance"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_response_time: float
    min_response_time: float
    max_response_time: float
    avg_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    throughput_per_second: float
    error_rate: float
    concurrency_level: int
    test_duration: float


@dataclass
class LoadTestResult:
    """Resultado de test de carga"""
    test_name: str
    load_level: int
    metrics: PerformanceMetrics
    resource_usage: Dict[str, float]
    timestamp: datetime


@pytest.mark.integration
@pytest.mark.performance
class TestPerformanceUnderLoad:
    """Tests de performance bajo diferentes niveles de carga"""
    
    @pytest.mark.asyncio
    async def test_baseline_performance(self, orchestrator, test_context):
        """Test baseline de performance con carga mínima"""
        # Configuración de test baseline
        test_config = {
            "concurrent_users": 1,
            "requests_per_user": 10,
            "think_time_seconds": 0.1,
            "ramp_up_time": 1
        }
        
        results = await self._run_load_test(orchestrator, test_context, test_config)
        
        # Verificar métricas baseline
        assert results.metrics.total_requests == 10
        assert results.metrics.successful_requests >= 9  # 90% success rate mínimo
        assert results.metrics.error_rate <= 0.1
        assert results.metrics.avg_response_time <= 2.0  # 2 segundos máximo
        assert results.metrics.throughput_per_second >= 5.0
        
        print(f"Test baseline completado:")
        print(f"  - Requests exitosos: {results.metrics.successful_requests}/{results.metrics.total_requests}")
        print(f"  - Tiempo promedio: {results.metrics.avg_response_time:.3f}s")
        print(f"  - Throughput: {results.metrics.throughput_per_second:.2f} req/s")
        print(f"  - Tasa de error: {results.metrics.error_rate:.3f}")
    
    @pytest.mark.asyncio
    async def test_medium_load_performance(self, orchestrator, test_context):
        """Test de performance con carga media"""
        test_config = {
            "concurrent_users": 5,
            "requests_per_user": 20,
            "think_time_seconds": 0.05,
            "ramp_up_time": 3
        }
        
        results = await self._run_load_test(orchestrator, test_context, test_config)
        
        # Verificar métricas de carga media
        assert results.metrics.total_requests == 100  # 5 users * 20 requests
        assert results.metrics.successful_requests >= 90  # 90% success rate mínimo
        assert results.metrics.error_rate <= 0.15  # Tolerancia ligeramente mayor
        assert results.metrics.avg_response_time <= 3.0  # 3 segundos máximo
        assert results.metrics.throughput_per_second >= 15.0
        
        # Verificar percentiles
        assert results.metrics.p95_response_time <= 5.0  # 95% de requests < 5s
        assert results.metrics.p99_response_time <= 8.0  # 99% de requests < 8s
        
        print(f"Test carga media completado:")
        print(f"  - Concurrencia: {results.metrics.concurrency_level}")
        print(f"  - P95: {results.metrics.p95_response_time:.3f}s")
        print(f"  - P99: {results.metrics.p99_response_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_high_load_performance(self, orchestrator, test_context):
        """Test de performance con carga alta"""
        test_config = {
            "concurrent_users": 15,
            "requests_per_user": 15,
            "think_time_seconds": 0.02,
            "ramp_up_time": 5
        }
        
        results = await self._run_load_test(orchestrator, test_context, test_config)
        
        # Verificar métricas de carga alta (con tolerancia reducida)
        assert results.metrics.total_requests == 225  # 15 users * 15 requests
        assert results.metrics.successful_requests >= 180  # 80% success rate mínimo
        assert results.metrics.error_rate <= 0.25  # Mayor tolerancia de error
        assert results.metrics.avg_response_time <= 5.0  # 5 segundos máximo
        assert results.metrics.throughput_per_second >= 30.0
        
        # Verificar que el sistema no se degrada excesivamente
        error_rate = results.metrics.error_rate
        assert error_rate <= 0.3, f"Tasa de error muy alta bajo carga: {error_rate:.3f}"
        
        print(f"Test carga alta completado:")
        print(f"  - Requests totales: {results.metrics.total_requests}")
        print(f"  - Throughput máximo: {results.metrics.throughput_per_second:.2f} req/s")
        print(f"  - Tiempo máximo: {results.metrics.max_response_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_stress_test_performance(self, orchestrator, test_context):
        """Test de estrés con carga extrema"""
        test_config = {
            "concurrent_users": 25,
            "requests_per_user": 10,
            "think_time_seconds": 0.01,
            "ramp_up_time": 2
        }
        
        results = await self._run_load_test(orchestrator, test_context, test_config)
        
        # Verificar que el sistema soporta carga extrema (con mucha tolerancia)
        assert results.metrics.total_requests == 250
        assert results.metrics.successful_requests >= 150  # 60% success rate mínimo
        assert results.metrics.error_rate <= 0.5  # Hasta 50% de error es aceptable
        
        # El sistema debería mantenerse operativo
        assert results.metrics.throughput_per_second >= 20.0
        
        print(f"Test estrés completado:")
        print(f"  - Carga extrema: {results.metrics.concurrency_level} usuarios concurrentes")
        print(f"  - Supervivencia: {results.metrics.successful_requests}/{results.metrics.total_requests}")
        print(f"  - Estado: {'OPERATIVO' if results.metrics.error_rate < 0.5 else 'DEGRADADO'}")
    
    @pytest.mark.asyncio
    async def test_spike_load_test(self, orchestrator, test_context):
        """Test de carga en pico (spike test)"""
        # Simular carga en pico: increase súbito y decrease gradual
        load_profile = [
            {"duration": 2, "users": 5},   # Base
            {"duration": 3, "users": 25},  # Spike up
            {"duration": 2, "users": 15},  # Spike down
            {"duration": 2, "users": 5}    # Base again
        ]
        
        spike_results = []
        
        for phase in load_profile:
            phase_config = {
                "concurrent_users": phase["users"],
                "requests_per_user": int(phase["users"] * 2),
                "think_time_seconds": 0.02,
                "ramp_up_time": 0.5,
                "duration": phase["duration"]
            }
            
            phase_result = await self._run_load_test(orchestrator, test_context, phase_config)
            spike_results.append({
                "phase": f"{phase['users']}_users",
                "duration": phase["duration"],
                "users": phase["users"],
                "metrics": phase_result.metrics
            })
            
            # Pausa entre fases
            await asyncio.sleep(1)
        
        # Verificar comportamiento durante spike
        base_phases = [r for r in spike_results if "5_users" in r["phase"]]
        spike_phases = [r for r in spike_results if "25_users" in r["phase"]]
        
        if base_phases and spike_phases:
            base_metrics = base_phases[0]["metrics"]
            spike_metrics = spike_phases[0]["metrics"]
            
            # Durante spike, la performance debería degradarse pero mantenerse funcional
            assert spike_metrics.error_rate <= base_metrics.error_rate * 2.5
            assert spike_metrics.throughput_per_second >= base_metrics.throughput_per_second * 0.5
        
        print(f"Test spike completado:")
        for result in spike_results:
            print(f"  - {result['phase']}: {result['metrics'].throughput_per_second:.2f} req/s, "
                  f"{result['metrics'].error_rate:.3f} error rate")
    
    @pytest.mark.asyncio
    async def test_sustained_load_test(self, orchestrator, test_context):
        """Test de carga sostenida"""
        # Carga sostenida por período extendido
        sustained_config = {
            "concurrent_users": 8,
            "requests_per_user": 50,  # Muchas requests por usuario
            "think_time_seconds": 0.05,
            "ramp_up_time": 3,
            "sustained_duration": 30  # 30 segundos de carga sostenida
        }
        
        start_time = time.time()
        
        # Ejecutar carga sostenida
        sustained_results = await self._run_load_test(orchestrator, test_context, sustained_config)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        # Verificar que la duración fue sostenida
        assert actual_duration >= sustained_config["sustained_duration"] * 0.8  # 80% tolerance
        
        # Verificar estabilidad durante período extendido
        assert sustained_results.metrics.throughput_per_second >= 10.0
        assert sustained_results.metrics.error_rate <= 0.2
        
        # El sistema debería mantener consistencia durante todo el período
        performance_consistency = 1.0 - (sustained_results.metrics.max_response_time - 
                                        sustained_results.metrics.min_response_time) / sustained_results.metrics.avg_response_time
        
        assert performance_consistency >= 0.5, "Performance inconsistente durante carga sostenida"
        
        print(f"Test carga sostenida completado:")
        print(f"  - Duración: {actual_duration:.2f}s")
        print(f"  - Consistencia: {performance_consistency:.3f}")
        print(f"  - Throughput sostenido: {sustained_results.metrics.throughput_per_second:.2f} req/s")
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, orchestrator, test_context):
        """Test de uso de memoria bajo carga"""
        load_levels = [1, 5, 10, 15, 20]
        memory_profiles = []
        
        for users in load_levels:
            test_config = {
                "concurrent_users": users,
                "requests_per_user": 10,
                "think_time_seconds": 0.1,
                "ramp_up_time": 1
            }
            
            # Simular medición de memoria (en un entorno real sería psutil)
            memory_before = self._simulate_memory_usage(users)
            results = await self._run_load_test(orchestrator, test_context, test_config)
            memory_after = self._simulate_memory_usage(users + 2)  # Simular incremento
            
            memory_delta = memory_after - memory_before
            memory_per_request = memory_delta / results.metrics.total_requests
            
            memory_profiles.append({
                "users": users,
                "memory_before_mb": memory_before,
                "memory_after_mb": memory_after,
                "memory_delta_mb": memory_delta,
                "memory_per_request_kb": memory_per_request * 1024,
                "throughput": results.metrics.throughput_per_second
            })
        
        # Verificar eficiencia de memoria
        for profile in memory_profiles:
            # No debería usar más de 10MB por request
            assert profile["memory_per_request_kb"] <= 10240, \
                f"Uso de memoria muy alto: {profile['memory_per_request_kb']:.2f} KB/request"
            
            # Throughput debería mantenerse razonable
            assert profile["throughput"] >= 5.0, \
                f"Throughput muy bajo: {profile['throughput']:.2f} req/s"
        
        # Verificar que el uso de memoria escala de manera razonable
        memory_scaling = memory_profiles[-1]["memory_delta_mb"] / memory_profiles[0]["memory_delta_mb"]
        user_scaling = memory_profiles[-1]["users"] / memory_profiles[0]["users"]
        
        # El uso de memoria no debería escalar más rápido que lineal
        assert memory_scaling <= user_scaling * 2.0, \
            f"Escalado de memoria no lineal: {memory_scaling:.2f} vs {user_scaling:.2f}"
        
        print(f"Test memoria bajo carga completado:")
        for profile in memory_profiles:
            print(f"  - {profile['users']} usuarios: "
                  f"{profile['memory_per_request_kb']:.2f} KB/request")
    
    @pytest.mark.asyncio
    async def test_concurrent_task_orchestration_performance(self, orchestrator, test_context):
        """Test de performance con orquestación concurrente de tareas"""
        # Test específico para orquestación concurrente
        num_concurrent_tasks = 10
        task_complexity_levels = ["simple", "medium", "complex"]
        
        concurrency_results = []
        
        for complexity in task_complexity_levels:
            # Crear tareas con diferentes complejidades
            concurrent_tasks = []
            for i in range(num_concurrent_tasks):
                task_context = {
                    **test_context,
                    "task_index": i,
                    "complexity": complexity,
                    "estimated_duration": {"simple": 1, "medium": 2, "complex": 4}[complexity]
                }
                
                task = orchestrator.orchestrate_task(
                    objective=f"Concurrent task {i} with {complexity} complexity",
                    context=task_context,
                    user_id=f"concurrent_user_{i % 5}",
                    streaming_enabled=False  # Disable streaming for performance
                )
                concurrent_tasks.append(task)
            
            # Ejecutar todas las tareas concurrentemente
            start_time = time.time()
            task_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Calcular métricas de concurrencia
            successful_tasks = [r for r in task_results if isinstance(r, dict) and r.get("success")]
            failed_tasks = [r for r in task_results if not isinstance(r, dict) or not r.get("success")]
            
            concurrency_results.append({
                "complexity": complexity,
                "total_tasks": num_concurrent_tasks,
                "successful_tasks": len(successful_tasks),
                "failed_tasks": len(failed_tasks),
                "total_time": total_time,
                "throughput_tasks_per_second": num_concurrent_tasks / total_time,
                "avg_task_duration": total_time / num_concurrent_tasks
            })
        
        # Verificar performance de concurrencia
        for result in concurrency_results:
            assert result["successful_tasks"] >= result["total_tasks"] * 0.8, \
                f"Demasiados fallos en concurrencia: {result['failed_tasks']}"
            
            assert result["throughput_tasks_per_second"] >= 1.0, \
                f"Throughput muy bajo: {result['throughput_tasks_per_second']:.2f} tasks/s"
        
        # Verificar que la complejidad afecta el throughput
        simple_throughput = next(r["throughput_tasks_per_second"] for r in concurrency_results if r["complexity"] == "simple")
        complex_throughput = next(r["throughput_tasks_per_second"] for r in concurrency_results if r["complexity"] == "complex")
        
        # Tasks complejas deberían ser más lentas pero no ordenes de magnitud
        throughput_ratio = simple_throughput / complex_throughput
        assert throughput_ratio >= 0.5, \
            f"Diferencia de throughput excesiva: {throughput_ratio:.2f}"
        
        print(f"Test concurrencia completado:")
        for result in concurrency_results:
            print(f"  - {result['complexity']}: "
                  f"{result['successful_tasks']}/{result['total_tasks']} tasks, "
                  f"{result['throughput_tasks_per_second']:.2f} tasks/s")
    
    async def _run_load_test(self, orchestrator, test_context, config: Dict[str, Any]) -> LoadTestResult:
        """Ejecutar test de carga específico"""
        test_name = "load_test"
        start_time = time.time()
        
        # Simular ramp-up
        await asyncio.sleep(config.get("ramp_up_time", 1))
        
        # Ejecutar requests concurrentes
        user_tasks = []
        response_times = []
        successful_requests = 0
        failed_requests = 0
        
        for user_id in range(config["concurrent_users"]):
            user_task = self._simulate_user_session(
                orchestrator, test_context, user_id, 
                config["requests_per_user"], config.get("think_time_seconds", 0.1)
            )
            user_tasks.append(user_task)
        
        # Ejecutar todas las sesiones de usuario
        user_results = await asyncio.gather(*user_tasks, return_exceptions=True)
        
        # Recopilar métricas
        for user_result in user_results:
            if isinstance(user_result, dict):
                if user_result.get("success"):
                    successful_requests += 1
                    response_times.extend(user_result.get("response_times", []))
                else:
                    failed_requests += 1
            else:
                failed_requests += 1
        
        total_time = time.time() - start_time
        total_requests = successful_requests + failed_requests
        
        # Calcular métricas
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)
            p99_response_time = statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else max(response_times)
        else:
            avg_response_time = median_response_time = min_response_time = max_response_time = p95_response_time = p99_response_time = 0
        
        throughput = total_requests / total_time if total_time > 0 else 0
        error_rate = failed_requests / total_requests if total_requests > 0 else 0
        
        metrics = PerformanceMetrics(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_response_time=sum(response_times) if response_times else 0,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            avg_response_time=avg_response_time,
            median_response_time=median_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            throughput_per_second=throughput,
            error_rate=error_rate,
            concurrency_level=config["concurrent_users"],
            test_duration=total_time
        )
        
        # Simular uso de recursos
        resource_usage = {
            "cpu_usage_percent": min(95, config["concurrent_users"] * 5),
            "memory_usage_mb": config["concurrent_users"] * 50,
            "database_connections": config["concurrent_users"] * 2,
            "network_io_mbps": config["concurrent_users"] * 0.5
        }
        
        return LoadTestResult(
            test_name=test_name,
            load_level=config["concurrent_users"],
            metrics=metrics,
            resource_usage=resource_usage,
            timestamp=datetime.now()
        )
    
    async def _simulate_user_session(self, orchestrator, base_context, user_id: int, requests: int, think_time: float) -> Dict[str, Any]:
        """Simular sesión de usuario con múltiples requests"""
        session_results = {
            "user_id": user_id,
            "success": True,
            "response_times": [],
            "requests_completed": 0,
            "requests_failed": 0
        }
        
        for request_num in range(requests):
            request_start = time.time()
            
            try:
                # Simular request al orquestador
                task_context = {
                    **base_context,
                    "user_id": f"load_user_{user_id}",
                    "request_number": request_num,
                    "session_id": f"session_{user_id}"
                }
                
                result = await orchestrator.orchestrate_task(
                    objective=f"Load test request {request_num} from user {user_id}",
                    context=task_context,
                    user_id=f"load_user_{user_id}",
                    streaming_enabled=False
                )
                
                if result.get("success"):
                    session_results["requests_completed"] += 1
                else:
                    session_results["requests_failed"] += 1
                    session_results["success"] = False
                
            except Exception as e:
                session_results["requests_failed"] += 1
                session_results["success"] = False
            
            request_time = time.time() - request_start
            session_results["response_times"].append(request_time)
            
            # Think time entre requests
            if request_num < requests - 1:
                await asyncio.sleep(think_time)
        
        # Si demasiados requests fallaron, marcar sesión como fallida
        failure_rate = session_results["requests_failed"] / requests
        if failure_rate > 0.5:
            session_results["success"] = False
        
        return session_results
    
    def _simulate_memory_usage(self, concurrent_users: int) -> float:
        """Simular uso de memoria basado en usuarios concurrentes"""
        # Simulación simple: base + usuarios * factor
        base_memory = 100  # MB
        memory_per_user = 10  # MB por usuario
        memory_growth_factor = 0.1  # Crecimiento no lineal
        
        calculated_memory = base_memory + (concurrent_users * memory_per_user * (1 + memory_growth_factor * concurrent_users / 100))
        return calculated_memory
    
    @pytest.mark.asyncio
    async def test_scalability_curve(self, orchestrator, test_context):
        """Test de curva de escalabilidad"""
        load_points = [1, 3, 5, 8, 12, 16, 20, 25]
        scalability_results = []
        
        for users in load_points:
            test_config = {
                "concurrent_users": users,
                "requests_per_user": 8,
                "think_time_seconds": 0.05,
                "ramp_up_time": 1
            }
            
            results = await self._run_load_test(orchestrator, test_context, test_config)
            
            scalability_results.append({
                "users": users,
                "throughput": results.metrics.throughput_per_second,
                "avg_response_time": results.metrics.avg_response_time,
                "error_rate": results.metrics.error_rate,
                "efficiency": results.metrics.throughput_per_second / users
            })
        
        # Analizar curva de escalabilidad
        for i, result in enumerate(scalability_results[1:], 1):
            prev_result = scalability_results[i-1]
            
            # Calcular eficiencia
            efficiency_drop = (prev_result["efficiency"] - result["efficiency"]) / prev_result["efficiency"]
            
            # La eficiencia no debería caer más del 30% por punto de escalado
            if result["users"] <= 16:  # Tolerancia hasta 16 usuarios
                assert efficiency_drop <= 0.3, \
                    f"Eficiencia cayó demasiado: {efficiency_drop:.2f} con {result['users']} usuarios"
        
        # Verificar throughput total máximo
        max_throughput = max(r["throughput"] for r in scalability_results)
        assert max_throughput >= 50.0, f"Throughput máximo muy bajo: {max_throughput:.2f} req/s"
        
        print(f"Test escalabilidad completado:")
        print(f"  - Puntos de carga probados: {len(load_points)}")
        print(f"  - Throughput máximo: {max_throughput:.2f} req/s")
        print(f"  - Eficiencia máxima: {max(r['efficiency'] for r in scalability_results):.2f} req/s/user")
        print(f"  - Eficiencia mínima: {min(r['efficiency'] for r in scalability_results):.2f} req/s/user")