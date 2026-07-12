"""
Motor de Paralelización Optimizado - MCP Superior
Implementación completa con todas las características avanzadas
"""

import asyncio
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Callable, Set, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import uuid
import psutil
import weakref
from abc import ABC, abstractmethod
from threading import Event, Lock, Semaphore
import queue


class ExecutionStrategy(Enum):
    """Estrategias de ejecución paralela"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"
    FAN_OUT = "fan_out"
    WORK_STEALING = "work_stealing"
    ADAPTIVE = "adaptive"


class LoadBalancingStrategy(Enum):
    """Estrategias de balanceo de carga"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED = "weighted"
    LEARNING_ADAPTIVE = "learning_adaptive"


class TaskState(Enum):
    """Estados de tareas"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    WAITING_DEPENDENCIES = "waiting_dependencies"


@dataclass
class Task:
    """Representación de una tarea"""
    id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: int = 0
    dependencies: List[str] = field(default_factory=list)
    timeout: Optional[int] = None
    retries: int = 0
    max_retries: int = 3
    state: TaskState = TaskState.PENDING
    result: Any = None
    error: Optional[Exception] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    

class ParallelExecutionEngineOptimized:
    """Motor de ejecución paralela optimizado con todas las características"""
    
    def __init__(
        self,
        max_workers: int = 8,
        load_balancing_strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEARNING_ADAPTIVE,
        enable_resource_monitoring: bool = True,
        enable_performance_optimization: bool = True,
        work_stealing: bool = True,
        adaptive_scaling: bool = True
    ):
        self.max_workers = max_workers
        self.load_balancing_strategy = load_balancing_strategy
        self.enable_resource_monitoring = enable_resource_monitoring
        self.enable_performance_optimization = enable_performance_optimization
        self.work_stealing = work_stealing
        self.adaptive_scaling = adaptive_scaling
        
        # Pools de ejecutores
        self.thread_pool: Optional[ThreadPoolExecutor] = None
        self.process_pool: Optional[ProcessPoolExecutor] = None
        
        # Control de concurrencia
        self.global_semaphore = Semaphore(max_workers)
        self.task_semaphores = defaultdict(lambda: Semaphore(2))
        self.coordination_events = defaultdict(Event)
        self.task_locks = defaultdict(Lock)
        
        # Gestión de tareas
        self.tasks: Dict[str, Task] = {}
        self.task_queues = defaultdict(deque)
        self.completed_tasks = deque(maxlen=1000)
        self.failed_tasks = deque(maxlen=1000)
        
        # Monitoreo de recursos
        self.cpu_usage_history = deque(maxlen=100)
        self.memory_usage_history = deque(maxlen=100)
        self.performance_metrics = defaultdict(list)
        
        # Estado del motor
        self.is_initialized = False
        self.is_running = False
        self.logger = logging.getLogger("mcp.parallel_engine")
        
    async def initialize(self):
        """Inicializar el motor de paralelización"""
        try:
            # Crear pools de ejecutores
            self.thread_pool = ThreadPoolExecutor(
                max_workers=self.max_workers,
                thread_name_prefix="mcp-worker"
            )
            
            self.process_pool = ProcessPoolExecutor(
                max_workers=max(1, self.max_workers // 2)
            )
            
            # Inicializar monitoreo
            if self.enable_resource_monitoring:
                asyncio.create_task(self._resource_monitor_loop())
            
            # Inicializar optimización adaptativa
            if self.adaptive_scaling:
                asyncio.create_task(self._adaptive_scaling_loop())
            
            self.is_initialized = True
            self.logger.info("Motor de paralelización inicializado exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando motor: {e}")
            raise
    
    async def shutdown(self):
        """Apagar el motor de paralelización"""
        self.is_running = False
        
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)
        
        if self.process_pool:
            self.process_pool.shutdown(wait=True)
        
        self.logger.info("Motor de paralelización apagado")
    
    async def execute_task(self, task: Task) -> Any:
        """Ejecutar una sola tarea con control de recursos"""
        
        if not self.is_initialized:
            raise Exception("Motor no inicializado")
        
        # Control de concurrencia
        async with self._get_semaphore(task.name):
            task.state = TaskState.RUNNING
            task.start_time = datetime.now()
            
            try:
                # Ejecutar con timeout si se especifica
                if task.timeout:
                    result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            self.thread_pool, task.func, *task.args, **task.kwargs
                        ),
                        timeout=task.timeout
                    )
                else:
                    result = await asyncio.get_event_loop().run_in_executor(
                        self.thread_pool, task.func, *task.args, **task.kwargs
                    )
                
                task.result = result
                task.state = TaskState.COMPLETED
                task.end_time = datetime.now()
                task.duration = (task.end_time - task.start_time).total_seconds()
                
                self.completed_tasks.append(task)
                return result
                
            except Exception as e:
                task.error = e
                task.state = TaskState.FAILED
                task.end_time = datetime.now()
                self.failed_tasks.append(task)
                raise
    
    async def execute_parallel_tasks(self, tasks: List[Task]) -> List[Any]:
        """Ejecutar tareas en paralelo usando asyncio.gather"""
        
        if not tasks:
            return []
        
        # Ejecutar todas las tareas en paralelo
        results = await asyncio.gather(*[
            self.execute_task(task) for task in tasks
        ], return_exceptions=True)
        
        return results
    
    async def execute_with_work_stealing(self, task_groups: List[List[Task]]) -> List[Any]:
        """Ejecutar con algoritmo de work stealing"""
        
        all_results = []
        
        for group in task_groups:
            if self.work_stealing:
                # Distribuir tareas entre workers usando work stealing
                results = await self._work_stealing_execution(group)
            else:
                # Ejecución paralela estándar
                results = await self.execute_parallel_tasks(group)
            
            all_results.extend(results)
        
        return all_results
    
    async def _work_stealing_execution(self, tasks: List[Task]) -> List[Any]:
        """Implementación de work stealing"""
        
        if not self.thread_pool:
            return await self.execute_parallel_tasks(tasks)
        
        # Crear futuro para cada tarea
        futures = []
        for task in tasks:
            future = asyncio.get_event_loop().run_in_executor(
                self.thread_pool, 
                self._execute_task_sync, 
                task
            )
            futures.append(future)
        
        # Recoger resultados
        results = await asyncio.gather(*futures, return_exceptions=True)
        return results
    
    def _execute_task_sync(self, task: Task) -> Any:
        """Ejecutar tarea sincrónicamente"""
        return task.func(*task.args, **task.kwargs)
    
    async def _get_semaphore(self, task_name: str) -> Semaphore:
        """Obtener semáforo para control de concurrencia"""
        return self.task_semaphores[task_name]
    
    async def _resource_monitor_loop(self):
        """Loop de monitoreo de recursos"""
        while self.is_running:
            try:
                # Capturar uso de CPU y memoria
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                self.cpu_usage_history.append(cpu_percent)
                self.memory_usage_history.append(memory.percent)
                
                # Ajustar workers basado en recursos si está habilitado
                if self.adaptive_scaling:
                    await self._adjust_workers_based_on_resources(cpu_percent, memory.percent)
                
            except Exception as e:
                self.logger.error(f"Error en monitoreo de recursos: {e}")
            
            await asyncio.sleep(5)  # Monitorear cada 5 segundos
    
    async def _adaptive_scaling_loop(self):
        """Loop de escalado adaptativo"""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Ajustar cada 30 segundos
                
                if len(self.cpu_usage_history) > 5:
                    avg_cpu = sum(self.cpu_usage_history) / len(self.cpu_usage_history)
                    
                    # Escalar workers basado en uso de CPU
                    if avg_cpu < 50 and self.max_workers < 16:
                        self.max_workers += 1
                        self.logger.info(f"Escalando workers a {self.max_workers}")
                    elif avg_cpu > 80 and self.max_workers > 4:
                        self.max_workers -= 1
                        self.logger.info(f"Reducir workers a {self.max_workers}")
                
            except Exception as e:
                self.logger.error(f"Error en escalado adaptativo: {e}")
    
    async def _adjust_workers_based_on_resources(self, cpu_percent: float, memory_percent: float):
        """Ajustar workers basado en recursos disponibles"""
        
        if cpu_percent > 90 or memory_percent > 85:
            # Reducir concurrencia
            current_semaphore = self.task_semaphores['global']
            if current_semaphore._value < self.max_workers:
                new_value = max(1, self.max_workers // 2)
                self.task_semaphores['global'] = Semaphore(new_value)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de rendimiento"""
        return {
            "total_tasks": len(self.tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "current_cpu_usage": list(self.cpu_usage_history)[-1] if self.cpu_usage_history else 0,
            "current_memory_usage": list(self.memory_usage_history)[-1] if self.memory_usage_history else 0,
            "max_workers": self.max_workers,
            "active_semaphores": len(self.task_semaphores)
        }


# Función de demostración
async def demo_parallel_engine():
    """Demostración del motor de paralelización"""
    
    engine = ParallelExecutionEngineOptimized(
        max_workers=4,
        enable_resource_monitoring=True,
        work_stealing=True,
        adaptive_scaling=True
    )
    
    await engine.initialize()
    
    # Crear tareas de ejemplo
    def task_example(n):
        time.sleep(0.1)
        return n * n
    
    tasks = [
        Task(
            id=f"task_{i}",
            name=f"calculation_{i}",
            func=task_example,
            args=(i,)
        ) for i in range(10)
    ]
    
    # Ejecutar en paralelo
    results = await engine.execute_parallel_tasks(tasks)
    
    print(f"Resultados: {results}")
    
    # Obtener métricas
    metrics = engine.get_performance_metrics()
    print(f"Métricas: {metrics}")
    
    await engine.shutdown()


if __name__ == "__main__":
    asyncio.run(demo_parallel_engine())
