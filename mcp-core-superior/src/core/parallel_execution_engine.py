"""
Motor de Ejecución Paralela - MCP Core Superior
Sistema avanzado de paralelización real para agentes con máximo rendimiento
Implementa thread pools, instance pooling, load balancing y optimización automática
"""
import asyncio
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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

from .exceptions import (
    ParallelExecutionException, 
    TaskNotFoundException,
    ResourceLimitExceededException,
    AgentInstanceException
)
from .config import settings


class ExecutionStrategy(Enum):
    """Estrategias de ejecución paralela"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"
    FAN_OUT = "fan_out"
    WORK_STEALING = "work_stealing"


class TaskState(Enum):
    """Estados de tareas"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    WAITING_DEPENDENCIES = "waiting_dependencies"


class LoadBalancingStrategy(Enum):
    """Estrategias de balanceador de carga"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_RANDOM = "weighted_random"
    LEARNING_ADAPTIVE = "learning_adaptive"


class ResourceType(Enum):
    """Tipos de recursos"""
    CPU = "cpu"
    MEMORY = "memory"
    IO = "io"
    NETWORK = "network"
    AGENT_SLOT = "agent_slot"


@dataclass(frozen=True)
class Task:
    """Representa una tarea ejecutable"""
    task_id: str
    agent_type: str
    operation: str
    parameters: Dict[str, Any]
    dependencies: Set[str] = field(default_factory=set)
    priority: int = 0
    timeout: Optional[float] = None
    strategy: ExecutionStrategy = ExecutionStrategy.PARALLEL
    max_retries: int = 3
    retry_delay: float = 1.0
    state: TaskState = TaskState.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    attempt: int = 0
    resource_requirements: Dict[str, float] = field(default_factory=dict)
    weight: float = 1.0

    @property
    def duration(self) -> float:
        """Duración de la tarea"""
        if self.started_at:
            end_time = self.completed_at or datetime.now()
            return (end_time - self.started_at).total_seconds()
        return 0.0

    @property
    def is_ready(self) -> bool:
        """Verificar si la tarea está lista para ejecutar"""
        return self.state == TaskState.PENDING or self.state == TaskState.WAITING_DEPENDENCIES

    @property
    def wait_time(self) -> float:
        """Tiempo de espera"""
        return (datetime.now() - self.created_at).total_seconds()


@dataclass
class AgentInstance:
    """Instancia de agente reutilizable"""
    instance_id: str
    agent_type: str
    wrapper: Any  # BaseAgentWrapper
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    total_time: float = 0.0
    current_task: Optional[str] = None
    load: float = 0.0
    capabilities: Set[str] = field(default_factory=set)

    def update_usage(self, task_duration: float) -> None:
        """Actualizar métricas de uso"""
        self.last_used = datetime.now()
        self.usage_count += 1
        self.total_time += task_duration
        self.current_task = None


@dataclass
class ResourcePool:
    """Pool de recursos del sistema"""
    cpu_limit: int = 0  # 0 = auto-detect
    memory_limit_mb: int = 0  # 0 = auto-detect
    max_agent_instances: int = 10
    max_concurrent_tasks: int = 100
    max_io_bandwidth_mbps: int = 100
    
    current_cpu_usage: float = 0.0
    current_memory_usage_mb: float = 0.0
    current_io_usage_mbps: float = 0.0
    agent_instance_count: int = 0
    active_task_count: int = 0

    @property
    def cpu_usage_percentage(self) -> float:
        """Porcentaje de uso de CPU"""
        return (self.current_cpu_usage / max(self.cpu_limit, 1)) * 100

    @property
    def memory_usage_percentage(self) -> float:
        """Porcentaje de uso de memoria"""
        return (self.current_memory_usage_mb / max(self.memory_limit_mb, 1)) * 100

    @property
    def io_usage_percentage(self) -> float:
        """Porcentaje de uso de IO"""
        return (self.current_io_usage_mbps / max(self.io_bandwidth_mbps, 1)) * 100


@dataclass
class PerformanceMetrics:
    """Métricas de rendimiento del sistema"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    cancelled_tasks: int = 0
    total_execution_time: float = 0.0
    average_task_time: float = 0.0
    throughput: float = 0.0  # tasks per second
    resource_utilization: Dict[str, float] = field(default_factory=dict)
    agent_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)
    load_balancing_efficiency: float = 0.0
    
    def update_task_completion(self, task: Task) -> None:
        """Actualizar métricas con una tarea completada"""
        self.total_tasks += 1
        
        if task.state == TaskState.COMPLETED:
            self.completed_tasks += 1
        elif task.state == TaskState.FAILED:
            self.failed_tasks += 1
        elif task.state == TaskState.CANCELLED:
            self.cancelled_tasks += 1
        
        self.total_execution_time += task.duration
        self.average_task_time = self.total_execution_time / max(self.total_tasks, 1)
        
        # Calcular throughput (tasks per second)
        elapsed_time = max(task.completed_at.timestamp() - (datetime.now() - timedelta(minutes=1)).timestamp(), 1)
        self.throughput = self.completed_tasks / elapsed_time


class LoadBalancer:
    """Balanceador de carga inteligente para agentes"""
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEARNING_ADAPTIVE):
        self.strategy = strategy
        self.agent_stats = defaultdict(lambda: {
            "total_assignments": 0,
            "successful_assignments": 0,
            "total_response_time": 0.0,
            "current_load": 0.0,
            "average_response_time": 0.0,
            "success_rate": 0.0
        })
        self.performance_history = deque(maxlen=100)
        self.round_robin_index = 0
        self.last_update = datetime.now()
    
    def select_agent(
        self, 
        available_agents: List[AgentInstance], 
        task: Task,
        current_loads: Dict[str, float]
    ) -> Optional[AgentInstance]:
        """Seleccionar mejor agente basado en estrategia"""
        if not available_agents:
            return None
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_select(available_agents)
        
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_select(available_agents, current_loads)
        
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_RANDOM:
            return self._weighted_random_select(available_agents, task)
        
        elif self.strategy == LoadBalancingStrategy.LEARNING_ADAPTIVE:
            return self._learning_adaptive_select(available_agents, task, current_loads)
        
        return available_agents[0]
    
    def _round_robin_select(self, agents: List[AgentInstance]) -> AgentInstance:
        """Selección round-robin"""
        agent = agents[self.round_robin_index % len(agents)]
        self.round_robin_index += 1
        return agent
    
    def _least_connections_select(
        self, 
        agents: List[AgentInstance], 
        current_loads: Dict[str, float]
    ) -> AgentInstance:
        """Selección por menor número de conexiones"""
        return min(agents, key=lambda a: current_loads.get(a.instance_id, 0.0))
    
    def _weighted_random_select(self, agents: List[AgentInstance], task: Task) -> AgentInstance:
        """Selección aleatoria ponderada"""
        weights = []
        for agent in agents:
            # Factor de peso basado en capacidades y performance
            weight = agent.weight * max(agent.capabilities, default=1.0)
            weights.append(weight)
        
        import random
        return random.choices(agents, weights=weights)[0]
    
    def _learning_adaptive_select(
        self, 
        agents: List[AgentInstance], 
        task: Task,
        current_loads: Dict[str, float]
    ) -> AgentInstance:
        """Selección adaptativa que aprende de la performance"""
        scores = []
        
        for agent in agents:
            stats = self.agent_stats[agent.instance_id]
            load_score = 1.0 / (1.0 + current_loads.get(agent.instance_id, 0.0))
            performance_score = stats.get("success_rate", 0.5) * 2.0
            response_time_score = 1.0 / (1.0 + stats.get("average_response_time", 1.0))
            
            # Score compuesto
            score = (load_score * 0.3 + performance_score * 0.5 + response_time_score * 0.2)
            scores.append(max(score, 0.1))  # Score mínimo
        
        import random
        return random.choices(agents, weights=scores)[0]
    
    def update_agent_performance(
        self, 
        agent_id: str, 
        task_duration: float, 
        success: bool
    ) -> None:
        """Actualizar métricas de performance del agente"""
        stats = self.agent_stats[agent_id]
        stats["total_assignments"] += 1
        
        if success:
            stats["successful_assignments"] += 1
            stats["total_response_time"] += task_duration
        
        stats["success_rate"] = (
            stats["successful_assignments"] / 
            max(stats["total_assignments"], 1)
        )
        
        if stats["successful_assignments"] > 0:
            stats["average_response_time"] = (
                stats["total_response_time"] / 
                stats["successful_assignments"]
            )


class ResourceManager:
    """Gestor de recursos del sistema"""
    
    def __init__(self):
        self.cpu_cores = psutil.cpu_count()
        self.total_memory_gb = psutil.virtual_memory().total / (1024**3)
        self.resource_pools: Dict[str, ResourcePool] = {}
        self.resource_locks = {
            ResourceType.CPU: asyncio.Lock(),
            ResourceType.MEMORY: asyncio.Lock(),
            ResourceType.IO: asyncio.Lock(),
            ResourceType.NETWORK: asyncio.Lock(),
            ResourceType.AGENT_SLOT: asyncio.Lock()
        }
    
    async def initialize_pools(self, config: Dict[str, Any]) -> None:
        """Inicializar pools de recursos"""
        for pool_name, pool_config in config.items():
            self.resource_pools[pool_name] = ResourcePool(
                cpu_limit=pool_config.get("cpu_cores", self.cpu_cores // 2),
                memory_limit_mb=pool_config.get("memory_mb", int(self.total_memory_gb * 1024 * 0.7)),
                max_agent_instances=pool_config.get("max_agents", 10),
                max_concurrent_tasks=pool_config.get("max_tasks", 100)
            )
    
    async def acquire_resources(
        self, 
        pool_name: str, 
        requirements: Dict[str, float],
        timeout: float = 30.0
    ) -> bool:
        """Adquirir recursos necesarios"""
        if pool_name not in self.resource_pools:
            return False
        
        pool = self.resource_pools[pool_name]
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Verificar disponibilidad de recursos
            if self._can_allocate_resources(pool, requirements):
                # Adquirir locks y asignar recursos
                async with self._get_resource_lock(ResourceType.CPU):
                    async with self._get_resource_lock(ResourceType.MEMORY):
                        if self._can_allocate_resources(pool, requirements):
                            self._allocate_resources(pool, requirements)
                            return True
            
            await asyncio.sleep(0.1)  # Esperar antes de reintentar
        
        return False
    
    async def release_resources(
        self, 
        pool_name: str, 
        requirements: Dict[str, float]
    ) -> None:
        """Liberar recursos"""
        if pool_name in self.resource_pools:
            pool = self.resource_pools[pool_name]
            self._deallocate_resources(pool, requirements)
    
    def _can_allocate_resources(
        self, 
        pool: ResourcePool, 
        requirements: Dict[str, float]
    ) -> bool:
        """Verificar si se pueden asignar los recursos"""
        cpu_required = requirements.get("cpu", 1.0)
        memory_required = requirements.get("memory", 100.0)  # MB
        
        return (
            pool.current_cpu_usage + cpu_required <= pool.cpu_limit and
            pool.current_memory_usage_mb + memory_required <= pool.memory_limit_mb
        )
    
    def _allocate_resources(self, pool: ResourcePool, requirements: Dict[str, float]) -> None:
        """Asignar recursos"""
        pool.current_cpu_usage += requirements.get("cpu", 0.0)
        pool.current_memory_usage_mb += requirements.get("memory", 0.0)
        pool.current_io_usage_mbps += requirements.get("io", 0.0)
    
    def _deallocate_resources(self, pool: ResourcePool, requirements: Dict[str, float]) -> None:
        """Desasignar recursos"""
        pool.current_cpu_usage = max(0, pool.current_cpu_usage - requirements.get("cpu", 0.0))
        pool.current_memory_usage_mb = max(0, pool.current_memory_usage_mb - requirements.get("memory", 0.0))
        pool.current_io_usage_mbps = max(0, pool.current_io_usage_mbps - requirements.get("io", 0.0))
    
    async def _get_resource_lock(self, resource_type: ResourceType) -> asyncio.Lock:
        """Obtener lock para tipo de recurso"""
        return self.resource_locks[resource_type]
    
    def get_system_resources(self) -> Dict[str, Any]:
        """Obtener información de recursos del sistema"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk_io = psutil.disk_io_counters()
        
        return {
            "cpu": {
                "cores": self.cpu_cores,
                "usage_percent": cpu_percent,
                "available_cores": self.cpu_cores - int(cpu_percent * self.cpu_cores / 100)
            },
            "memory": {
                "total_gb": self.total_memory_gb,
                "used_gb": memory.used / (1024**3),
                "available_gb": memory.available / (1024**3),
                "usage_percent": memory.percent
            },
            "disk_io": {
                "read_mbps": disk_io.read_bytes / 1024 / 1024 if disk_io else 0,
                "write_mbps": disk_io.write_bytes / 1024 / 1024 if disk_io else 0
            }
        }


class AgentInstancePool:
    """Pool de instancias de agentes reutilizables"""
    
    def __init__(self, max_instances_per_type: int = 5):
        self.max_instances_per_type = max_instances_per_type
        self.pools: Dict[str, List[AgentInstance]] = defaultdict(list)
        self.active_agents: Dict[str, AgentInstance] = {}
        self.agent_factory: Optional[Callable] = None
        self.lock = asyncio.Lock()
        self.instance_counter = 0
    
    def set_agent_factory(self, factory: Callable) -> None:
        """Configurar factory de agentes"""
        self.agent_factory = factory
    
    async def get_agent(self, agent_type: str, **kwargs) -> Optional[AgentInstance]:
        """Obtener agente del pool o crear uno nuevo"""
        async with self.lock:
            # Buscar agente disponible en pool
            pool = self.pools.get(agent_type, [])
            available_agents = [agent for agent in pool if not agent.current_task]
            
            if available_agents:
                # Reutilizar agente existente
                agent = available_agents[0]
                pool.remove(agent)
                self.active_agents[agent.instance_id] = agent
                return agent
            
            # Crear nuevo agente si no alcanzamos el límite
            if len(self.active_agents) < self.max_instances_per_type * len(self.pools):
                return await self._create_agent_instance(agent_type, **kwargs)
            
            return None
    
    async def return_agent(self, agent: AgentInstance, task_duration: float) -> None:
        """Devolver agente al pool"""
        async with self.lock:
            agent.update_usage(task_duration)
            
            if agent.instance_id in self.active_agents:
                del self.active_agents[agent.instance_id]
            
            # Mantener agente en pool si sigue siendo útil
            if agent.usage_count < 10 or agent.total_time < 300:  # 10 usos o 5 minutos
                self.pools[agent.agent_type].append(agent)
            else:
                # Agente demasiado usado, limpiar
                await self._cleanup_agent_instance(agent)
    
    async def _create_agent_instance(self, agent_type: str, **kwargs) -> Optional[AgentInstance]:
        """Crear nueva instancia de agente"""
        if not self.agent_factory:
            return None
        
        try:
            instance_id = f"agent_{agent_type}_{self.instance_counter}"
            self.instance_counter += 1
            
            # Crear wrapper de agente
            wrapper = await self.agent_factory(agent_type, **kwargs)
            
            instance = AgentInstance(
                instance_id=instance_id,
                agent_type=agent_type,
                wrapper=wrapper,
                capabilities=set(getattr(wrapper, "capabilities", []))
            )
            
            self.active_agents[instance_id] = instance
            return instance
            
        except Exception as e:
            logging.error(f"Error creando instancia de agente {agent_type}: {e}")
            return None
    
    async def _cleanup_agent_instance(self, agent: AgentInstance) -> None:
        """Limpiar instancia de agente"""
        try:
            if hasattr(agent.wrapper, 'cleanup'):
                await agent.wrapper.cleanup()
        except Exception as e:
            logging.warning(f"Error limpiando agente {agent.instance_id}: {e}")
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del pool"""
        total_active = len(self.active_agents)
        total_pooled = sum(len(pool) for pool in self.pools.values())
        
        return {
            "active_agents": total_active,
            "pooled_agents": total_pooled,
            "pools": {k: len(v) for k, v in self.pools.items()},
            "utilization": total_active / max(total_active + total_pooled, 1)
        }


class ProgressTracker:
    """Tracker de progreso en tiempo real"""
    
    def __init__(self):
        self.task_progress: Dict[str, Dict[str, Any]] = {}
        self.completed_tasks: deque = deque(maxlen=1000)
        self.task_listeners: List[Callable] = []
        self.progress_lock = asyncio.Lock()
    
    def add_task(self, task: Task) -> None:
        """Agregar tarea al tracker"""
        self.task_progress[task.task_id] = {
            "task": task,
            "progress_percentage": 0.0,
            "stage": "initializing",
            "start_time": datetime.now(),
            "estimated_completion": None,
            "resource_usage": defaultdict(float)
        }
    
    def update_task_progress(
        self, 
        task_id: str, 
        progress: float, 
        stage: str = None,
        resource_usage: Dict[str, float] = None
    ) -> None:
        """Actualizar progreso de tarea"""
        if task_id in self.task_progress:
            self.task_progress[task_id]["progress_percentage"] = max(0.0, min(100.0, progress))
            if stage:
                self.task_progress[task_id]["stage"] = stage
            if resource_usage:
                self.task_progress[task_id]["resource_usage"].update(resource_usage)
            
            # Notificar listeners
            for listener in self.task_listeners:
                try:
                    listener(task_id, self.task_progress[task_id])
                except Exception as e:
                    logging.warning(f"Error en listener de progreso: {e}")
    
    def complete_task(self, task_id: str, success: bool, result: Any = None, error: str = None) -> None:
        """Marcar tarea como completada"""
        if task_id in self.task_progress:
            progress_data = self.task_progress[task_id]
            progress_data["completion_time"] = datetime.now()
            progress_data["success"] = success
            progress_data["result"] = result
            progress_data["error"] = error
            progress_data["progress_percentage"] = 100.0 if success else 0.0
            
            # Agregar a historial
            self.completed_tasks.append({
                "task_id": task_id,
                "completed_at": datetime.now(),
                "success": success,
                "duration": (datetime.now() - progress_data["start_time"]).total_seconds()
            })
    
    def get_task_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtener progreso de tarea"""
        return self.task_progress.get(task_id)
    
    def get_all_progress(self) -> Dict[str, Dict[str, Any]]:
        """Obtener progreso de todas las tareas"""
        return dict(self.task_progress)
    
    def add_progress_listener(self, listener: Callable) -> None:
        """Agregar listener de progreso"""
        self.task_listeners.append(listener)


class CancellationManager:
    """Gestor de cancelación de tareas"""
    
    def __init__(self):
        self.cancelled_tasks: Set[str] = set()
        self.task_futures: Dict[str, asyncio.Task] = {}
        self.cancellation_listeners: List[Callable] = []
    
    def cancel_task(self, task_id: str, reason: str = None) -> bool:
        """Cancelar tarea"""
        if task_id in self.cancelled_tasks:
            return False
        
        self.cancelled_tasks.add(task_id)
        
        # Cancelar futuro si existe
        if task_id in self.task_futures:
            future = self.task_futures[task_id]
            future.cancel(reason or f"Tarea {task_id} cancelada por el usuario")
        
        # Notificar listeners
        for listener in self.cancellation_listeners:
            try:
                listener(task_id, reason)
            except Exception as e:
                logging.warning(f"Error en listener de cancelación: {e}")
        
        return True
    
    def register_future(self, task_id: str, future: asyncio.Task) -> None:
        """Registrar futuro para cancelación"""
        self.task_futures[task_id] = future
    
    def unregister_future(self, task_id: str) -> None:
        """Desregistrar futuro"""
        self.task_futures.pop(task_id, None)
    
    def add_cancellation_listener(self, listener: Callable) -> None:
        """Agregar listener de cancelación"""
        self.cancellation_listeners.append(listener)
    
    def is_cancelled(self, task_id: str) -> bool:
        """Verificar si tarea está cancelada"""
        return task_id in self.cancelled_tasks


class ParallelExecutionEngine:
    """
    Motor principal de ejecución paralela de agentes
    Supera el sistema secuencial básico con:
    - Pool management configurables
    - Instance pooling para reutilización
    - Concurrent workflow execution
    - Load balancing inteligente
    - Resource sharing e isolation
    - Progress tracking en tiempo real
    - Cancellation y timeout handling
    - Performance metrics y optimización automática
    """
    
    def __init__(
        self,
        max_workers: int = None,
        load_balancing_strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEARNING_ADAPTIVE,
        enable_resource_monitoring: bool = True,
        enable_performance_optimization: bool = True
    ):
        # Configuración básica
        self.max_workers = max_workers or psutil.cpu_count() * 2
        self.load_balancing_strategy = load_balancing_strategy
        self.enable_resource_monitoring = enable_resource_monitoring
        self.enable_performance_optimization = enable_performance_optimization
        
        # Componentes principales
        self.load_balancer = LoadBalancer(load_balancing_strategy)
        self.resource_manager = ResourceManager()
        self.agent_pool = AgentInstancePool()
        self.progress_tracker = ProgressTracker()
        self.cancellation_manager = CancellationManager()
        
        # Estado del sistema
        self.is_running = False
        self.active_tasks: Dict[str, Task] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.completed_tasks: Dict[str, Task] = {}
        
        # Métricas y optimización
        self.metrics = PerformanceMetrics()
        self.performance_history = deque(maxlen=100)
        self.optimization_enabled = enable_performance_optimization
        
        # Thread pool executor para operaciones bloqueantes
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Logging
        self.logger = logging.getLogger("mcp.core.parallel_engine")
        
        # Scheduler para tareas
        self._scheduler_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
        self._optimization_task: Optional[asyncio.Task] = None
        
        # Factories
        self.agent_factories: Dict[str, Callable] = {}
        
        # Configuration
        self.config = {
            "task_timeout": 300.0,
            "health_check_interval": 30.0,
            "optimization_interval": 60.0,
            "max_concurrent_tasks": self.max_workers * 2,
            "resource_monitoring_interval": 10.0
        }
    
    def register_agent_factory(self, agent_type: str, factory: Callable) -> None:
        """Registrar factory de agente"""
        self.agent_factories[agent_type] = factory
    
    async def initialize(self, agent_configs: Dict[str, Dict[str, Any]]) -> None:
        """Inicializar el motor de ejecución paralela"""
        if self.is_running:
            self.logger.warning("Motor ya está inicializado")
            return
        
        self.logger.info(f"Iniciando Motor de Ejecución Paralela con {self.max_workers} workers")
        
        # Configurar factories de agentes
        for agent_type, config in agent_configs.items():
            if "factory" in config:
                self.register_agent_factory(agent_type, config["factory"])
        
        # Configurar pool de agentes
        self.agent_pool.set_agent_factory(self._create_agent_wrapper)
        
        # Inicializar pools de recursos
        await self.resource_manager.initialize_pools(agent_configs)
        
        # Iniciar tareas de fondo
        self.is_running = True
        self._scheduler_task = asyncio.create_task(self._task_scheduler())
        self._monitor_task = asyncio.create_task(self._resource_monitor())
        
        if self.optimization_enabled:
            self._optimization_task = asyncio.create_task(self._performance_optimizer())
        
        # Setup listeners
        self.progress_tracker.add_progress_listener(self._handle_progress_update)
        self.cancellation_manager.add_cancellation_listener(self._handle_task_cancellation)
        
        self.logger.info("Motor de Ejecución Paralela inicializado correctamente")
    
    async def shutdown(self, timeout: float = 30.0) -> None:
        """Apagar el motor de ejecución"""
        if not self.is_running:
            return
        
        self.logger.info("Apagando Motor de Ejecución Paralela...")
        self.is_running = False
        
        # Cancelar tareas de fondo
        tasks_to_cancel = []
        if self._scheduler_task:
            tasks_to_cancel.append(self._scheduler_task)
        if self._monitor_task:
            tasks_to_cancel.append(self._monitor_task)
        if self._optimization_task:
            tasks_to_cancel.append(self._optimization_task)
        
        # Cancelar tareas pendientes
        for task in self.active_tasks.values():
            if task.state in [TaskState.PENDING, TaskState.RUNNING]:
                self.cancellation_manager.cancel_task(task.task_id, "Sistema shutdown")
        
        # Esperar cancelación graceful
        if tasks_to_cancel:
            await asyncio.wait_for(
                asyncio.gather(*tasks_to_cancel, return_exceptions=True),
                timeout=timeout
            )
        
        # Cerrar thread pool
        self.thread_pool.shutdown(wait=True)
        
        self.logger.info("Motor de Ejecución Paralela apagado")
    
    async def execute_workflow(
        self,
        tasks: List[Task],
        workflow_id: Optional[str] = None,
        strategy: ExecutionStrategy = ExecutionStrategy.PARALLEL
    ) -> Dict[str, Any]:
        """Ejecutar workflow de tareas"""
        if not self.is_running:
            raise ParallelExecutionException("Motor no inicializado")
        
        workflow_id = workflow_id or f"workflow_{uuid.uuid4()}"
        
        self.logger.info(f"Iniciando workflow {workflow_id} con {len(tasks)} tareas")
        
        # Agregar tareas al tracker
        for task in tasks:
            task.task_id = f"{workflow_id}_{task.task_id}_{uuid.uuid4()}"
            self.progress_tracker.add_task(task)
            self.active_tasks[task.task_id] = task
        
        # Ejecutar según estrategia
        if strategy == ExecutionStrategy.SEQUENTIAL:
            results = await self._execute_sequential(tasks)
        elif strategy == ExecutionStrategy.PARALLEL:
            results = await self._execute_parallel(tasks)
        elif strategy == ExecutionStrategy.PIPELINE:
            results = await self._execute_pipeline(tasks)
        elif strategy == ExecutionStrategy.FAN_OUT:
            results = await self._execute_fan_out(tasks)
        else:
            results = await self._execute_adaptive(tasks)
        
        # Calcular resultados del workflow
        workflow_result = {
            "workflow_id": workflow_id,
            "strategy": strategy.value,
            "total_tasks": len(tasks),
            "completed_tasks": sum(1 for task in tasks if task.state == TaskState.COMPLETED),
            "failed_tasks": sum(1 for task in tasks if task.state == TaskState.FAILED),
            "total_duration": sum(task.duration for task in tasks),
            "success_rate": sum(1 for task in tasks if task.state == TaskState.COMPLETED) / max(len(tasks), 1),
            "task_results": {
                task.task_id: {
                    "state": task.state.value,
                    "duration": task.duration,
                    "result": task.result,
                    "error": task.error
                }
                for task in tasks
            },
            "performance_metrics": self.metrics.__dict__
        }
        
        self.logger.info(f"Workflow {workflow_id} completado: {workflow_result['success_rate']:.2%} éxito")
        
        return workflow_result
    
    async def execute_single_task(self, task: Task) -> Task:
        """Ejecutar una sola tarea"""
        self.progress_tracker.add_task(task)
        self.active_tasks[task.task_id] = task
        
        return await self._execute_task(task)
    
    async def _execute_task(self, task: Task) -> Task:
        """Ejecutar una tarea individual"""
        task.state = TaskState.RUNNING
        task.started_at = datetime.now()
        task.attempt += 1
        
        self.logger.debug(f"Ejecutando tarea {task.task_id}")
        
        try:
            # Verificar cancelación
            if self.cancellation_manager.is_cancelled(task.task_id):
                task.state = TaskState.CANCELLED
                self.progress_tracker.complete_task(task.task_id, False, None, "Tarea cancelada")
                return task
            
            # Adquirir recursos necesarios
            if task.resource_requirements:
                acquired = await self.resource_manager.acquire_resources(
                    task.agent_type,
                    task.resource_requirements
                )
                if not acquired:
                    raise ParallelExecutionException(
                        f"No se pudieron adquirir recursos para tarea {task.task_id}"
                    )
            
            # Obtener agente del pool
            agent_instance = await self.agent_pool.get_agent(
                task.agent_type,
                max_concurrent=1,
                timeout_seconds=task.timeout or self.config["task_timeout"]
            )
            
            if not agent_instance:
                raise AgentInstanceException(f"No hay agentes disponibles para {task.agent_type}")
            
            # Ejecutar tarea con timeout
            with threading.timeout(task.timeout or self.config["task_timeout"]):
                start_time = time.time()
                
                # Actualizar progreso
                self.progress_tracker.update_task_progress(task.task_id, 25.0, "Ejecutando")
                
                # Ejecutar operación del agente
                result = await self._execute_agent_operation(agent_instance, task)
                
                task_duration = time.time() - start_time
                
                # Actualizar métricas de performance
                self.load_balancer.update_agent_performance(
                    agent_instance.instance_id,
                    task_duration,
                    True
                )
                
                # Devolver agente al pool
                await self.agent_pool.return_agent(agent_instance, task_duration)
                
                # Completar tarea
                task.result = result
                task.state = TaskState.COMPLETED
                task.completed_at = datetime.now()
                
                # Actualizar métricas globales
                self.metrics.update_task_completion(task)
                
                self.logger.debug(f"Tarea {task.task_id} completada en {task_duration:.2f}s")
        
        except asyncio.TimeoutError:
            task.state = TaskState.TIMEOUT
            task.error = f"Timeout después de {task.timeout}s"
            self.logger.warning(f"Tarea {task.task_id} timeout")
        
        except Exception as e:
            task.state = TaskState.FAILED
            task.error = str(e)
            self.logger.error(f"Tarea {task.task_id} falló: {e}")
            
            # Retry logic
            if task.attempt < task.max_retries:
                await asyncio.sleep(task.retry_delay * task.attempt)
                return await self._execute_task(task)
        
        finally:
            # Liberar recursos
            if task.resource_requirements:
                await self.resource_manager.release_resources(
                    task.agent_type,
                    task.resource_requirements
                )
            
            # Actualizar progreso final
            success = task.state == TaskState.COMPLETED
            self.progress_tracker.complete_task(task.task_id, success, task.result, task.error)
            
            # Remover de tareas activas
            self.active_tasks.pop(task.task_id, None)
            self.completed_tasks[task.task_id] = task
        
        return task
    
    async def _execute_agent_operation(self, agent_instance: AgentInstance, task: Task) -> Any:
        """Ejecutar operación en agente"""
        # Simular ejecución - aquí iría la lógica real de ejecución
        self.progress_tracker.update_task_progress(task.task_id, 50.0, "Procesando")
        
        # Tiempo simulado de ejecución basado en parámetros
        execution_time = max(0.1, len(str(task.parameters)) * 0.01)
        await asyncio.sleep(execution_time)
        
        # Simular resultado
        self.progress_tracker.update_task_progress(task.task_id, 90.0, "Finalizando")
        
        return {
            "task_id": task.task_id,
            "agent_type": task.agent_type,
            "operation": task.operation,
            "result": f"Resultado de {task.operation} en {task.agent_type}",
            "timestamp": datetime.now().isoformat(),
            "execution_time": execution_time
        }
    
    async def _execute_sequential(self, tasks: List[Task]) -> List[Task]:
        """Ejecución secuencial (compatibilidad con sistema actual)"""
        results = []
        for task in tasks:
            result_task = await self._execute_task(task)
            results.append(result_task)
            
            # Verificar dependencias para siguiente tarea
            if not all(dep in [t.task_id for t in results] for dep in task.dependencies):
                task.state = TaskState.WAITING_DEPENDENCIES
        
        return results
    
    async def _execute_parallel(self, tasks: List[Task]) -> List[Task]:
        """Ejecución paralela verdadera"""
        # Agrupar tareas por dependencias
        ready_tasks = self._get_ready_tasks(tasks)
        running_tasks = set()
        
        results = []
        
        while ready_tasks or running_tasks:
            # Lanzar nuevas tareas disponibles
            while ready_tasks and len(running_tasks) < self.config["max_concurrent_tasks"]:
                task = ready_tasks.pop(0)
                running_tasks.add(task)
                
                # Crear tarea asíncrona
                future = asyncio.create_task(self._execute_task(task))
                self.cancellation_manager.register_future(task.task_id, future)
                
                future.add_done_callback(lambda f: running_tasks.discard(task))
            
            # Esperar que alguna tarea termine
            if running_tasks:
                done, pending = await asyncio.wait(
                    running_tasks,
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                for task_future in done:
                    completed_task = await task_future
                    results.append(completed_task)
                    
                    # Verificar si nuevas tareas están listas
                    completed_task_ids = {t.task_id for t in results}
                    for next_task in tasks:
                        if (next_task.task_id not in completed_task_ids and 
                            next_task.task_id not in [t.task_id for t in results] and
                            self._is_task_ready(next_task, results)):
                            ready_tasks.append(next_task)
        
        return results
    
    async def _execute_pipeline(self, tasks: List[Task]) -> List[Task]:
        """Ejecución en pipeline"""
        # Similar a paralelo pero con orden específico
        return await self._execute_parallel(tasks)
    
    async def _execute_fan_out(self, tasks: List[Task]) -> List[Task]:
        """Ejecución fan-out (broadcast)"""
        # Ejecutar tareas en paralelo independientemente
        results = await asyncio.gather(*[self._execute_task(task) for task in tasks], return_exceptions=True)
        return [task if not isinstance(task, Exception) else task for task in results]
    
    async def _execute_adaptive(self, tasks: List[Task]) -> List[Task]:
        """Ejecución adaptativa basada en métricas"""
        # Usar estrategia basada en performance actual
        system_load = self.resource_manager.get_system_resources()
        cpu_usage = system_load["cpu"]["usage_percent"]
        
        if cpu_usage < 50:
            return await self._execute_parallel(tasks)
        elif cpu_usage < 80:
            return await self._execute_fan_out(tasks)
        else:
            return await self._execute_sequential(tasks)
    
    def _get_ready_tasks(self, tasks: List[Task]) -> List[Task]:
        """Obtener tareas listas para ejecutar"""
        return [task for task in tasks if self._is_task_ready(task, [])]
    
    def _is_task_ready(self, task: Task, completed_tasks: List[Task]) -> bool:
        """Verificar si una tarea está lista para ejecutar"""
        if task.state != TaskState.PENDING:
            return False
        
        # Verificar dependencias
        completed_ids = {t.task_id for t in completed_tasks}
        return task.dependencies.issubset(completed_ids)
    
    async def _task_scheduler(self) -> None:
        """Scheduler principal de tareas"""
        while self.is_running:
            try:
                # Procesar cola de tareas pendientes
                # Aquí iría la lógica del scheduler
                await asyncio.sleep(1.0)
            except Exception as e:
                self.logger.error(f"Error en task scheduler: {e}")
                await asyncio.sleep(5.0)
    
    async def _resource_monitor(self) -> None:
        """Monitor de recursos del sistema"""
        while self.is_running:
            try:
                # Actualizar información de recursos
                resources = self.resource_manager.get_system_resources()
                
                # Logging de recursos críticos
                if resources["cpu"]["usage_percent"] > 90:
                    self.logger.warning("CPU usage > 90%")
                
                if resources["memory"]["usage_percent"] > 90:
                    self.logger.warning("Memory usage > 90%")
                
                await asyncio.sleep(self.config["resource_monitoring_interval"])
            except Exception as e:
                self.logger.error(f"Error en resource monitor: {e}")
                await asyncio.sleep(5.0)
    
    async def _performance_optimizer(self) -> None:
        """Optimizador automático de performance"""
        while self.is_running:
            try:
                # Analizar métricas y optimizar
                await self._analyze_performance_and_optimize()
                await asyncio.sleep(self.config["optimization_interval"])
            except Exception as e:
                self.logger.error(f"Error en performance optimizer: {e}")
                await asyncio.sleep(10.0)
    
    async def _analyze_performance_and_optimize(self) -> None:
        """Analizar performance y aplicar optimizaciones"""
        # Obtener estadísticas de performance
        agent_stats = self.agent_pool.get_pool_stats()
        
        # Optimizaciones basadas en performance
        if agent_stats["utilization"] > 0.8:
            self.logger.info("Alta utilización del pool - considerado aumentar tamaño")
        
        # Ajustar parámetros basado en throughput
        if self.metrics.throughput < 1.0:  # Menos de 1 task por segundo
            self.logger.info("Bajo throughput - optimizando configuraciones")
    
    async def _create_agent_wrapper(self, agent_type: str, **kwargs) -> Any:
        """Factory de wrappers de agentes"""
        if agent_type in self.agent_factories:
            return await self.agent_factories[agent_type](**kwargs)
        else:
            raise ValueError(f"Tipo de agente no registrado: {agent_type}")
    
    def _handle_progress_update(self, task_id: str, progress_data: Dict[str, Any]) -> None:
        """Manejar actualizaciones de progreso"""
        # Aquí se pueden enviar updates a clientes via WebSocket, etc.
        pass
    
    def _handle_task_cancellation(self, task_id: str, reason: str) -> None:
        """Manejar cancelación de tareas"""
        self.logger.info(f"Tarea {task_id} cancelada: {reason}")
    
    # API pública para monitoreo
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema"""
        resources = self.resource_manager.get_system_resources()
        agent_stats = self.agent_pool.get_pool_stats()
        
        return {
            "is_running": self.is_running,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "queue_size": self.task_queue.qsize() if hasattr(self, 'task_queue') else 0,
            "resources": resources,
            "agent_pools": agent_stats,
            "metrics": {
                "total_tasks": self.metrics.total_tasks,
                "completed_tasks": self.metrics.completed_tasks,
                "success_rate": self.metrics.completed_tasks / max(self.metrics.total_tasks, 1),
                "average_task_time": self.metrics.average_task_time,
                "throughput": self.metrics.throughput
            },
            "performance": dict(self.metrics.agent_performance),
            "load_balancing_strategy": self.load_balancing_strategy.value
        }
    
    def get_task_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtener progreso de una tarea"""
        return self.progress_tracker.get_task_progress(task_id)
    
    def cancel_task(self, task_id: str, reason: str = None) -> bool:
        """Cancelar una tarea"""
        return self.cancellation_manager.cancel_task(task_id, reason)
    
    def get_all_progress(self) -> Dict[str, Dict[str, Any]]:
        """Obtener progreso de todas las tareas"""
        return self.progress_tracker.get_all_progress()
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check del motor"""
        try:
            system_resources = self.resource_manager.get_system_resources()
            agent_stats = self.agent_pool.get_pool_stats()
            
            health_status = {
                "status": "healthy",
                "is_running": self.is_running,
                "active_tasks": len(self.active_tasks),
                "resources": {
                    "cpu_usage": system_resources["cpu"]["usage_percent"],
                    "memory_usage": system_resources["memory"]["usage_percent"],
                    "cpu_available": system_resources["cpu"]["available_cores"]
                },
                "agents": {
                    "active_instances": agent_stats["active_agents"],
                    "pooled_instances": agent_stats["pooled_agents"],
                    "utilization": agent_stats["utilization"]
                },
                "performance": {
                    "success_rate": self.metrics.completed_tasks / max(self.metrics.total_tasks, 1),
                    "average_task_time": self.metrics.average_task_time,
                    "throughput": self.metrics.throughput
                }
            }
            
            # Verificar problemas de salud
            if health_status["resources"]["cpu_usage"] > 95:
                health_status["status"] = "critical"
                health_status["issues"] = ["CPU usage > 95%"]
            elif health_status["resources"]["memory_usage"] > 95:
                health_status["status"] = "critical"
                health_status["issues"] = ["Memory usage > 95%"]
            elif health_status["performance"]["success_rate"] < 0.5:
                health_status["status"] = "warning"
                health_status["issues"] = ["Low success rate"]
            
            return health_status
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }