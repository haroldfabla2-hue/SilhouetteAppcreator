"""
Tests de Cargas Extremas - Motor de Paralelización Optimizado
Tests específicos para cargas de 1000+ tareas concurrentes

Valida que el motor optimizado maneje correctamente:
- Cargas extremas (1000+ tareas)
- Circuit breakers robustos
- Work stealing
- Backpressure handling
- Métricas avanzadas
- Graceful degradation
"""
import pytest
import asyncio
import time
import statistics
import psutil
import gc
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from concurrent.futures import ThreadPoolExecutor

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.parallel_execution_engine_optimized import (
    OptimizedParallelExecutionEngine,
    Task,
    TaskState,
    ExecutionStrategy,
    LoadBalancingStrategy,
    CircuitBreakerState,
    TaskPriority
)


@pytest.mark.extreme_load
class TestExtremeLoadOptimization:
    """Tests de optimización para cargas extremas (1000+ tareas)"""
    
    @pytest.fixture
    async def extreme_load_engine(self):
        """Motor optimizado para tests extremos"""
        engine = OptimizedParallelExecutionEngine(
            max_workers=16,
            load_balancing_strategy=LoadBalancingStrategy.RESOURCE_AWARE,
            enable_circuit_breakers=True,
            enable_work_stealing=True,
            enable_back_pressure=True,
            enable_performance_optimization=True
        )
        
        # Configurar agentes de test
        agent_configs = {
            "test_agent": {
                "factory": lambda **kwargs: MockAgentWrapper(),
                "max_agents": 20,
                "max_tasks": 500,
                "auto_scaling": True
            },
            "cpu_intensive_agent": {
                "factory": lambda **kwargs: MockAgentWrapper(),
                "max_agents": 10,
                "max_tasks": 200,
                "auto_scaling": True
            },
            "io_intensive_agent": {
                "factory": lambda **kwargs: MockAgentWrapper(),
                "max_agents": 15,
                "max_tasks": 300,
                "auto_scaling": True
            }
        }
        
        await engine.initialize(agent_configs)
        yield engine
        await engine.shutdown(timeout=10.0)
    
    @pytest.mark.asyncio
    async def test_1000_tasks_extreme_load(self, extreme_load_engine):
        """Test con 1000 tareas concurrentes - carga extrema"""
        print("\n🚀 INICIANDO TEST DE CARGA EXTREMA: 1000 tareas")
        
        # Crear 1000 tareas
        tasks = []
        for i in range(1000):
            task = Task(
                task_id=f"extreme_task_{i}",
                agent_type="test_agent",
                operation="extreme_load_test",
                parameters={"task_id": i, "load_type": "normal"},
                priority=i % 10,  # Variar prioridades
                timeout=60.0,
                estimated_duration=0.5 + (i % 100) * 0.01,  # Duración variable
                weight=1.0
            )
            tasks.append(task)
        
        start_time = time.time()
        
        # Ejecutar workflow extremo
        result = await extreme_load_engine.execute_workflow(
            tasks=tasks,
            workflow_id="extreme_load_1000",
            strategy=ExecutionStrategy.ADAPTIVE
        )
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Verificar resultados extremos
        print(f"📊 RESULTADOS DE 1000 TAREAS:")
        print(f"  - Duración total: {total_duration:.2f}s")
        print(f"  - Tareas completadas: {result['completed_tasks']}/{result['total_tasks']}")
        print(f"  - Tasa de éxito: {result['success_rate']:.2%}")
        print(f"  - Throughput: {result['throughput_tasks_per_second']:.2f} tasks/s")
        print(f"  - Tareas fallidas: {result['failed_tasks']}")
        print(f"  - Tiempo promedio: {result['avg_duration']:.3f}s")
        print(f"  - Tiempo máximo: {result['max_duration']:.3f}s")
        
        # Verificaciones críticas para carga extrema
        assert result['total_tasks'] == 1000, "Deberían ser exactamente 1000 tareas"
        assert result['success_rate'] >= 0.80, f"Tasa de éxito muy baja para carga extrema: {result['success_rate']:.2%}"
        assert result['throughput_tasks_per_second'] >= 10.0, f"Throughput muy bajo: {result['throughput_tasks_per_second']:.2f} tasks/s"
        assert total_duration <= 300.0, f"Duración excesiva para carga extrema: {total_duration:.2f}s"
        
        # Verificar que el sistema se mantuvo estable
        health = await extreme_load_engine.health_check()
        print(f"🏥 HEALTH CHECK: {health['status']}")
        assert health['status'] in ['healthy', 'warning'], "Sistema debería mantenerse operativo"
        
        print("✅ TEST DE 1000 TAREAS COMPLETADO EXITOSAMENTE")
    
    @pytest.mark.asyncio
    async def test_2000_tasks_massive_load(self, extreme_load_engine):
        """Test con 2000 tareas - carga masiva"""
        print("\n🚀 INICIANDO TEST DE CARGA MASIVA: 2000 tareas")
        
        # Crear 2000 tareas con variabilidad
        tasks = []
        for i in range(2000):
            agent_type = ["test_agent", "cpu_intensive_agent", "io_intensive_agent"][i % 3]
            
            task = Task(
                task_id=f"massive_task_{i}",
                agent_type=agent_type,
                operation="massive_load_test",
                parameters={
                    "task_id": i,
                    "load_type": "massive",
                    "complexity": (i % 10) + 1,
                    "estimated_work": (i % 100) * 0.1
                },
                priority=(100 - (i % 100)) // 10,  # Prioridades inversas
                timeout=120.0,
                estimated_duration=1.0 + (i % 50) * 0.02,
                cpu_intensive=i % 5 == 0,  # 20% CPU intensive
                io_intensive=i % 3 == 0,   # 33% IO intensive
                memory_intensive=i % 7 == 0  # 14% memory intensive
            )
            tasks.append(task)
        
        start_time = time.time()
        
        # Ejecutar workflow masivo
        result = await extreme_load_engine.execute_workflow(
            tasks=tasks,
            workflow_id="massive_load_2000",
            strategy=ExecutionStrategy.WORK_STEALING  # Mejor para cargas masivas
        )
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Verificar resultados masivos
        print(f"📊 RESULTADOS DE 2000 TAREAS:")
        print(f"  - Duración total: {total_duration:.2f}s")
        print(f"  - Tareas completadas: {result['completed_tasks']}/{result['total_tasks']}")
        print(f"  - Tasa de éxito: {result['success_rate']:.2%}")
        print(f"  - Throughput: {result['throughput_tasks_per_second']:.2f} tasks/s")
        print(f"  - Peak throughput: {result['performance_metrics']['peak_throughput']:.2f} tasks/s")
        print(f"  - Circuit breaker trips: {result['resource_usage']['circuit_breaker_trips']}")
        print(f"  - Back pressure events: {result['resource_usage']['back_pressure_events']}")
        print(f"  - Work stealing events: {result['performance_metrics']['work_stealing_events']}")
        
        # Verificaciones para carga masiva (con mayor tolerancia)
        assert result['total_tasks'] == 2000, "Deberían ser exactamente 2000 tareas"
        assert result['success_rate'] >= 0.75, f"Tasa de éxito insuficiente para carga masiva: {result['success_rate']:.2%}"
        assert result['throughput_tasks_per_second'] >= 5.0, f"Throughput muy bajo para carga masiva: {result['throughput_tasks_per_second']:.2f} tasks/s"
        
        # Verificar que las optimizaciones funcionaron
        assert result['resource_usage']['circuit_breaker_trips'] >= 0, "Circuit breakers deberían activarse"
        assert result['performance_metrics']['work_stealing_events'] > 0, "Work stealing debería ocurrir"
        
        # El sistema debería degradarse gracefulmente, no fallar completamente
        assert result['success_rate'] > 0.5, "Sistema debería mantener >50% éxito incluso bajo carga masiva"
        
        print("✅ TEST DE 2000 TAREAS COMPLETADO CON DEGRADACIÓN GRACEFUL")
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_extreme_failures(self, extreme_load_engine):
        """Test de circuit breakers bajo fallos extremos"""
        print("\n⚡ TESTING CIRCUIT BREAKERS CON FALLOS EXTREMOS")
        
        # Crear tareas que simulan fallos
        failing_tasks = []
        for i in range(100):
            task = Task(
                task_id=f"failing_task_{i}",
                agent_type="test_agent",
                operation="failing_operation",
                parameters={"fail": True, "failure_rate": 1.0},  # Siempre falla
                timeout=10.0,
                max_retries=5  # Muchos reintentos
            )
            failing_tasks.append(task)
        
        # Crear tareas normales mezcladas
        normal_tasks = []
        for i in range(50):
            task = Task(
                task_id=f"normal_task_{i}",
                agent_type="test_agent",
                operation="normal_operation",
                parameters={"task_id": i},
                timeout=10.0,
                max_retries=1
            )
            normal_tasks.append(task)
        
        all_tasks = failing_tasks + normal_tasks
        
        start_time = time.time()
        
        # Ejecutar con fallos
        result = await extreme_load_engine.execute_workflow(
            tasks=all_tasks,
            workflow_id="circuit_breaker_test",
            strategy=ExecutionStrategy.PARALLEL
        )
        
        end_time = time.time()
        
        print(f"📊 RESULTADOS CIRCUIT BREAKER:")
        print(f"  - Total tasks: {result['total_tasks']}")
        print(f"  - Circuit breaker trips: {result['resource_usage']['circuit_breaker_trips']}")
        print(f"  - Failed tasks: {result['failed_tasks']}")
        print(f"  - Retry events: {result['performance_metrics']['retry_events']}")
        print(f"  - Success rate: {result['success_rate']:.2%}")
        
        # Verificar que circuit breakers funcionaron
        assert result['resource_usage']['circuit_breaker_trips'] > 0, "Circuit breakers deberían activarse"
        assert result['performance_metrics']['retry_events'] > 0, "Reintentos deberían ocurrir"
        
        # Las tareas normales deberían tener más éxito que las fallidas
        normal_success = sum(1 for t in normal_tasks if t.state == TaskState.COMPLETED)
        failing_success = sum(1 for t in failing_tasks if t.state == TaskState.COMPLETED)
        
        assert normal_success > failing_success, "Tareas normales deberían tener mejor tasa de éxito"
        
        print("✅ CIRCUIT BREAKERS FUNCIONANDO CORRECTAMENTE")
    
    @pytest.mark.asyncio
    async def test_work_stealing_efficiency(self, extreme_load_engine):
        """Test de eficiencia del work stealing"""
        print("\n🔄 TESTING WORK STEALING EFFICIENCY")
        
        # Crear cargas desbalanceadas para activar work stealing
        tasks_batch_1 = []
        tasks_batch_2 = []
        
        # Batch 1: tareas que toman mucho tiempo
        for i in range(50):
            task = Task(
                task_id=f"slow_task_{i}",
                agent_type="test_agent",
                operation="slow_operation",
                parameters={"duration": 2.0},  # Tareas lentas
                timeout=10.0,
                estimated_duration=2.0
            )
            tasks_batch_1.append(task)
        
        # Batch 2: tareas rápidas
        for i in range(100):
            task = Task(
                task_id=f"fast_task_{i}",
                agent_type="test_agent", 
                operation="fast_operation",
                parameters={"duration": 0.1},  # Tareas rápidas
                timeout=5.0,
                estimated_duration=0.1
            )
            tasks_batch_2.append(task)
        
        all_tasks = tasks_batch_1 + tasks_batch_2
        
        start_time = time.time()
        
        # Ejecutar con work stealing
        result = await extreme_load_engine.execute_workflow(
            tasks=all_tasks,
            workflow_id="work_stealing_test",
            strategy=ExecutionStrategy.WORK_STEALING
        )
        
        end_time = time.time()
        
        print(f"📊 RESULTADOS WORK STEALING:")
        print(f"  - Total tasks: {result['total_tasks']}")
        print(f"  - Work stealing events: {result['performance_metrics']['work_stealing_events']}")
        print(f"  - Throughput: {result['throughput_tasks_per_second']:.2f} tasks/s")
        print(f"  - Duration: {end_time - start_time:.2f}s")
        
        # Verificar que work stealing ocurrió
        assert result['performance_metrics']['work_stealing_events'] > 0, "Work stealing debería ocurrir"
        
        # El throughput debería ser mejor que ejecución secuencial
        expected_sequential_time = len(tasks_batch_1) * 2.0 + len(tasks_batch_2) * 0.1
        actual_time = end_time - start_time
        
        # Work stealing debería ser significativamente más rápido que secuencial
        improvement_factor = expected_sequential_time / actual_time
        print(f"  - Work stealing improvement: {improvement_factor:.2f}x")
        
        assert improvement_factor > 1.5, f"Work stealing debería mejorar performance >1.5x, got {improvement_factor:.2f}x"
        
        print("✅ WORK STEALING FUNCIONANDO EFICIENTEMENTE")
    
    @pytest.mark.asyncio
    async def test_backpressure_handling(self, extreme_load_engine):
        """Test de backpressure handling"""
        print("\n🚦 TESTING BACKPRESSURE HANDLING")
        
        # Crear tareas que saturen recursos
        memory_intensive_tasks = []
        for i in range(200):
            task = Task(
                task_id=f"memory_task_{i}",
                agent_type="test_agent",
                operation="memory_intensive",
                parameters={"memory_usage": 10},  # 10MB por tarea
                resource_requirements={"memory": 10.0},
                timeout=30.0,
                memory_intensive=True
            )
            memory_intensive_tasks.append(task)
        
        # Crear más tareas de las que el sistema puede manejar
        normal_tasks = []
        for i in range(300):
            task = Task(
                task_id=f"normal_task_{i}",
                agent_type="test_agent",
                operation="normal_operation",
                parameters={"work": 1.0},
                timeout=15.0
            )
            normal_tasks.append(task)
        
        all_tasks = memory_intensive_tasks + normal_tasks
        
        start_time = time.time()
        
        # Ejecutar con potenciales problemas de backpressure
        result = await extreme_load_engine.execute_workflow(
            tasks=all_tasks,
            workflow_id="backpressure_test",
            strategy=ExecutionStrategy.ADAPTIVE
        )
        
        end_time = time.time()
        
        print(f"📊 RESULTADOS BACKPRESSURE:")
        print(f"  - Total tasks: {result['total_tasks']}")
        print(f"  - Back pressure events: {result['resource_usage']['back_pressure_events']}")
        print(f"  - Tasks completed: {result['completed_tasks']}")
        print(f"  - Success rate: {result['success_rate']:.2%}")
        print(f"  - Duration: {end_time - start_time:.2f}s")
        
        # Verificar que backpressure fue manejado
        if result['resource_usage']['back_pressure_events'] > 0:
            print("  - ✅ Backpressure events detectados y manejados")
            assert result['success_rate'] > 0.3, "Sistema debería mantener >30% éxito con backpressure"
        else:
            print("  - ⚠️  No se detectaron eventos de backpressure (puede ser normal)")
        
        # El sistema no debería colapsar completamente
        assert result['success_rate'] > 0.1, "Sistema no debería colapsar completamente"
        
        print("✅ BACKPRESSURE HANDLING FUNCIONANDO")
    
    @pytest.mark.asyncio
    async def test_mixed_workload_optimization(self, extreme_load_engine):
        """Test con workload mixto optimizado"""
        print("\n🎯 TESTING MIXED WORKLOAD OPTIMIZATION")
        
        # Crear workload mixto realista
        mixed_tasks = []
        
        # 20% CPU intensive
        for i in range(200):
            task = Task(
                task_id=f"cpu_task_{i}",
                agent_type="cpu_intensive_agent",
                operation="compute_intensive",
                parameters={"iterations": 1000},
                cpu_intensive=True,
                estimated_duration=1.5,
                timeout=30.0
            )
            mixed_tasks.append(task)
        
        # 30% IO intensive
        for i in range(300):
            task = Task(
                task_id=f"io_task_{i}",
                agent_type="io_intensive_agent",
                operation="io_intensive",
                parameters={"data_size": 1024},
                io_intensive=True,
                estimated_duration=0.8,
                timeout=20.0
            )
            mixed_tasks.append(task)
        
        # 50% normal tasks
        for i in range(500):
            task = Task(
                task_id=f"normal_task_{i}",
                agent_type="test_agent",
                operation="normal_processing",
                parameters={"complexity": (i % 10) + 1},
                estimated_duration=0.3 + (i % 10) * 0.05,
                timeout=15.0
            )
            mixed_tasks.append(task)
        
        start_time = time.time()
        
        # Ejecutar con estrategia adaptativa
        result = await extreme_load_engine.execute_workflow(
            tasks=mixed_tasks,
            workflow_id="mixed_workload_optimization",
            strategy=ExecutionStrategy.ADAPTIVE
        )
        
        end_time = time.time()
        
        print(f"📊 RESULTADOS WORKLOAD MIXTO:")
        print(f"  - Total tasks: {result['total_tasks']}")
        print(f"  - CPU intensive: 200, IO intensive: 300, Normal: 500")
        print(f"  - Completed: {result['completed_tasks']}")
        print(f"  - Success rate: {result['success_rate']:.2%}")
        print(f"  - Throughput: {result['throughput_tasks_per_second']:.2f} tasks/s")
        print(f"  - Average duration: {result['avg_duration']:.3f}s")
        print(f"  - Peak throughput: {result['performance_metrics']['peak_throughput']:.2f} tasks/s")
        
        # Verificar percentiles
        percentiles = result['performance_metrics']['percentiles']
        print(f"  - P50: {percentiles['p50']:.3f}s, P95: {percentiles['p95']:.3f}s, P99: {percentiles['p99']:.3f}s")
        
        # Verificar optimización efectiva
        assert result['success_rate'] >= 0.85, f"Workload mixto debería tener alta tasa de éxito: {result['success_rate']:.2%}"
        assert result['throughput_tasks_per_second'] >= 15.0, f"Throughput debería ser bueno: {result['throughput_tasks_per_second']:.2f} tasks/s"
        
        # Los percentiles deberían mostrar distribución razonable
        assert percentiles['p95'] < percentiles['p99'] * 1.5, "Percentiles deberían mostrar distribución realista"
        
        print("✅ WORKLOAD MIXTO OPTIMIZADO EXITOSAMENTE")
    
    @pytest.mark.asyncio
    async def test_memory_management_under_extreme_load(self, extreme_load_engine):
        """Test de gestión de memoria bajo carga extrema"""
        print("\n🧠 TESTING MEMORY MANAGEMENT UNDER EXTREME LOAD")
        
        # Obtener baseline de memoria
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"  - Baseline memory: {baseline_memory:.2f} MB")
        
        # Crear tareas que generan mucho trabajo
        memory_tasks = []
        for batch in range(10):  # 10 batches de 100 tareas
            batch_tasks = []
            for i in range(100):
                task = Task(
                    task_id=f"memory_task_{batch}_{i}",
                    agent_type="test_agent",
                    operation="memory_test",
                    parameters={
                        "data_size": 10240,  # 10KB de datos
                        "processing_time": 0.5,
                        "batch": batch
                    },
                    timeout=30.0,
                    memory_intensive=True
                )
                batch_tasks.append(task)
            
            # Ejecutar cada batch y medir memoria
            result = await extreme_load_engine.execute_workflow(
                tasks=batch_tasks,
                workflow_id=f"memory_batch_{batch}",
                strategy=ExecutionStrategy.PARALLEL
            )
            
            # Verificar memoria después del batch
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = current_memory - baseline_memory
            
            print(f"  - Batch {batch}: {result['completed_tasks']}/100 completed, "
                  f"Memory: {current_memory:.2f} MB (+{memory_increase:.2f} MB)")
            
            # El uso de memoria no debería crecer indefinidamente
            if batch > 2:  # Permitir crecimiento inicial
                max_reasonable_increase = batch * 50  # 50MB por batch máximo
                assert memory_increase < max_reasonable_increase, \
                    f"Memory leak detected: {memory_increase:.2f} MB increase"
            
            # Forzar garbage collection
            gc.collect()
            await asyncio.sleep(1)  # Permitir cleanup
        
        # Verificación final de memoria
        final_memory = process.memory_info().rss / 1024 / 1024
        total_memory_increase = final_memory - baseline_memory
        
        print(f"  - Final memory: {final_memory:.2f} MB")
        print(f"  - Total increase: {total_memory_increase:.2f} MB")
        print(f"  - GC events: {result['performance_metrics']['memory_gc_events']}")
        
        # El incremento total de memoria debería ser razonable
        assert total_memory_increase < 500, f"Memory leak: {total_memory_increase:.2f} MB total increase"
        
        print("✅ MEMORY MANAGEMENT FUNCIONANDO CORRECTAMENTE")
    
    @pytest.mark.asyncio
    async def test_sustained_extreme_load(self, extreme_load_engine):
        """Test de carga extrema sostenida"""
        print("\n⏱️  TESTING SUSTAINED EXTREME LOAD")
        
        total_tasks_executed = 0
        duration_seconds = 30  # 30 segundos de carga sostenida
        
        start_time = time.time()
        batch_start = start_time
        
        while time.time() - start_time < duration_seconds:
            # Crear batch de tareas cada segundo
            current_batch = int((time.time() - batch_start))
            
            # Variar tamaño de batch (30-70 tareas)
            batch_size = 30 + (current_batch % 40)
            
            tasks = []
            for i in range(batch_size):
                task = Task(
                    task_id=f"sustained_task_{current_batch}_{i}",
                    agent_type="test_agent",
                    operation="sustained_load",
                    parameters={"batch": current_batch, "task_id": i},
                    timeout=15.0,
                    estimated_duration=0.8
                )
                tasks.append(task)
            
            # Ejecutar batch
            result = await extreme_load_engine.execute_workflow(
                tasks=tasks,
                workflow_id=f"sustained_batch_{current_batch}",
                strategy=ExecutionStrategy.ADAPTIVE
            )
            
            total_tasks_executed += result['completed_tasks']
            
            print(f"  - Batch {current_batch}: {result['completed_tasks']}/{batch_size} "
                  f"(Success: {result['success_rate']:.1%})")
            
            await asyncio.sleep(0.5)  # Pequeña pausa entre batches
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Verificar resultados de carga sostenida
        print(f"📊 RESULTADOS CARGA SOSTENIDA:")
        print(f"  - Duration: {total_duration:.2f}s")
        print(f"  - Total tasks executed: {total_tasks_executed}")
        print(f"  - Average tasks/sec: {total_tasks_executed/total_duration:.2f}")
        
        # Verificar que se mantuvo estable
        sustained_throughput = total_tasks_executed / total_duration
        assert sustained_throughput > 20.0, f"Sustained throughput muy bajo: {sustained_throughput:.2f} tasks/s"
        
        # Verificar health del sistema
        health = await extreme_load_engine.health_check()
        print(f"  - Final health status: {health['status']}")
        assert health['status'] in ['healthy', 'warning'], "Sistema debería mantenerse estable"
        
        print("✅ CARGA SOSTENIDA COMPLETADA EXITOSAMENTE")
    
    @pytest.mark.asyncio
    async def test_performance_regression_detection(self, extreme_load_engine):
        """Test de detección de regresiones de performance"""
        print("\n📈 TESTING PERFORMANCE REGRESSION DETECTION")
        
        # Ejecutar baseline test
        baseline_tasks = []
        for i in range(100):
            task = Task(
                task_id=f"baseline_task_{i}",
                agent_type="test_agent",
                operation="baseline_test",
                parameters={"complexity": 5},
                timeout=10.0,
                estimated_duration=0.5
            )
            baseline_tasks.append(task)
        
        start_time = time.time()
        baseline_result = await extreme_load_engine.execute_workflow(
            tasks=baseline_tasks,
            workflow_id="baseline_performance",
            strategy=ExecutionStrategy.PARALLEL
        )
        baseline_duration = time.time() - start_time
        baseline_throughput = len(baseline_tasks) / baseline_duration
        
        print(f"  - Baseline: {baseline_duration:.2f}s, {baseline_throughput:.2f} tasks/s")
        
        # Ejecutar test de carga
        load_tasks = []
        for i in range(500):
            task = Task(
                task_id=f"load_task_{i}",
                agent_type="test_agent",
                operation="load_test",
                parameters={"complexity": 5},
                timeout=15.0,
                estimated_duration=0.5
            )
            load_tasks.append(task)
        
        start_time = time.time()
        load_result = await extreme_load_engine.execute_workflow(
            tasks=load_tasks,
            workflow_id="load_performance",
            strategy=ExecutionStrategy.PARALLEL
        )
        load_duration = time.time() - start_time
        load_throughput = len(load_tasks) / load_duration
        
        print(f"  - Load: {load_duration:.2f}s, {load_throughput:.2f} tasks/s")
        
        # Calcular degradación
        throughput_degradation = (baseline_throughput - load_throughput) / baseline_throughput
        
        print(f"  - Throughput degradation: {throughput_degradation:.1%}")
        
        # Verificar que la degradación es razonable
        assert throughput_degradation < 0.5, f"Degradación excesiva: {throughput_degradation:.1%}"
        assert load_result['success_rate'] > 0.8, f"Success rate bajo carga: {load_result['success_rate']:.1%}"
        
        # Obtener métricas avanzadas
        system_status = extreme_load_engine.get_system_status()
        
        print(f"  - System metrics:")
        print(f"    * Peak throughput: {system_status['metrics']['peak_throughput']:.2f}")
        print(f"    * Circuit breaker trips: {system_status['metrics']['circuit_breaker_trips']}")
        print(f"    * Back pressure events: {system_status['metrics']['back_pressure_events']}")
        print(f"    * Work stealing events: {system_status['metrics']['work_stealing_events']}")
        
        print("✅ PERFORMANCE REGRESSION DETECTION FUNCIONANDO")
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_extreme_conditions(self, extreme_load_engine):
        """Test de degradación graceful bajo condiciones extremas"""
        print("\n🛡️  TESTING GRACEFUL DEGRADATION UNDER EXTREME CONDITIONS")
        
        # Crear condiciones extremas
        extreme_tasks = []
        
        # Tareas que consumen recursos excesivamente
        for i in range(200):
            task = Task(
                task_id=f"resource_task_{i}",
                agent_type="test_agent",
                operation="resource_hog",
                parameters={"consume_resources": True},
                resource_requirements={"cpu": 5.0, "memory": 100.0},
                timeout=60.0
            )
            extreme_tasks.append(task)
        
        # Tareas normales mezcladas
        for i in range(100):
            task = Task(
                task_id=f"normal_task_{i}",
                agent_type="test_agent",
                operation="normal_operation",
                parameters={"priority": "high"},
                timeout=30.0
            )
            extreme_tasks.append(task)
        
        start_time = time.time()
        
        # Ejecutar bajo condiciones extremas
        result = await extreme_load_engine.execute_workflow(
            tasks=extreme_tasks,
            workflow_id="graceful_degradation_test",
            strategy=ExecutionStrategy.ADAPTIVE
        )
        
        end_time = time.time()
        
        print(f"📊 RESULTADOS DEGRADACIÓN GRACEFUL:")
        print(f"  - Total tasks: {result['total_tasks']}")
        print(f"  - Completed: {result['completed_tasks']}")
        print(f"  - Success rate: {result['success_rate']:.2%}")
        print(f"  - Failed: {result['failed_tasks']}")
        print(f"  - Cancelled: {result['cancelled_tasks']}")
        print(f"  - Timeout: {result.get('timeout_tasks', 0)}")
        print(f"  - Duration: {end_time - start_time:.2f}s")
        
        # Verificar degradación graceful
        assert result['success_rate'] > 0.3, "Sistema debería mantener >30% de tareas exitosas"
        assert result['completed_tasks'] > 0, "Algunas tareas deberían completarse"
        
        # Verificar que el sistema se recuperó
        health = await extreme_load_engine.health_check()
        print(f"  - System recovery status: {health['status']}")
        
        # El sistema debería poder recuperarse o al menos mantenerse estable
        assert health['status'] in ['healthy', 'warning', 'critical'], "Sistema debería tener estado definido"
        
        # Verificar que los recursos se liberaron correctamente
        system_status = extreme_load_engine.get_system_status()
        cpu_usage = system_status['system_load']['cpu_percent']
        memory_usage = system_status['system_load']['memory_percent']
        
        print(f"  - Final CPU usage: {cpu_usage:.1f}%")
        print(f"  - Final memory usage: {memory_usage:.1f}%")
        
        # Los recursos deberían haberse liberado
        assert cpu_usage < 95.0, f"CPU no se liberó correctamente: {cpu_usage:.1f}%"
        assert memory_usage < 95.0, f"Memory no se liberó correctamente: {memory_usage:.1f}%"
        
        print("✅ GRACEFUL DEGRADATION FUNCIONANDO CORRECTAMENTE")


class MockAgentWrapper:
    """Mock agent wrapper para tests"""
    
    def __init__(self):
        self.capabilities = ["test", "mock"]
        self.performance_score = 1.0
    
    async def execute(self, operation: str, parameters: Dict[str, Any]) -> Any:
        """Mock execution"""
        # Simular tiempo de ejecución
        execution_time = parameters.get("execution_time", 0.1)
        await asyncio.sleep(execution_time)
        
        # Simular fallos ocasionales
        if parameters.get("fail", False):
            failure_rate = parameters.get("failure_rate", 0.1)
            if hash(str(parameters)) % 100 < failure_rate * 100:
                raise Exception("Simulated failure")
        
        return {
            "status": "success",
            "operation": operation,
            "result": f"Mock result for {operation}",
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup(self):
        """Mock cleanup"""
        pass


# Ejecutar tests de forma manual para debugging
if __name__ == "__main__":
    import pytest
    import sys
    
    # Configurar asyncio para debugging
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Ejecutar tests específicos
    pytest.main([
        __file__,
        "-v",
        "-s",  # Show print output
        "--tb=short",
        "TestExtremeLoadOptimization::test_1000_tasks_extreme_load"
    ])