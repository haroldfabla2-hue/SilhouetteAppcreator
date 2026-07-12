"""
Multi-Agent Orchestrator Agent MCP - Versión Avanzada
Orquestador empresarial que gestiona agentes base y especializados con capacidades avanzadas

Capacidades:
- Workflow Management avanzado
- Load Balancing inteligente
- Dependency Resolution automática
- Parallel Execution con control de concurrencia
- Error Recovery automático
- Horizontal Scaling
- Health Monitoring en tiempo real
- Dynamic Agent Registration
- Circuit Breaker pattern
- Task prioritization y queue management
"""

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Set, Callable, Awaitable
from datetime import datetime, timedelta
import heapq
import weakref

from .base_agent_wrapper import BaseAgentWrapper, AgentCapability, AgentStatus
# Importaciones relativas con manejo de errores para compatibilidad
try:
    from ..core.exceptions import AgentException, OrchestrationException
    from ..core.config import settings
except ImportError:
    # Fallback para testing directo y compatibilidad
    class AgentException(Exception):
        def __init__(self, message, agent_name=None, operation=None, error_code=None, original_error=None):
            super().__init__(message)
            self.agent_name = agent_name
            self.operation = operation
            self.error_code = error_code
            self.original_error = original_error
    
    class OrchestrationException(Exception):
        def __init__(self, message, workflow_id=None, step_id=None):
            super().__init__(message)
            self.workflow_id = workflow_id
            self.step_id = step_id
    
    # Mock settings para testing
    class MockSettings:
        max_concurrent_tools = 3
        agent_timeout_seconds = 60
        agent_retry_attempts = 3
        agent_retry_delay = 1.0
        verification_quality_threshold = 0.8
    
    settings = MockSettings()


class WorkflowState(Enum):
    """Estados de workflow"""
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(Enum):
    """Prioridades de tareas"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class LoadBalancingStrategy(Enum):
    """Estrategias de load balancing"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_RANDOM = "weighted_random"
    FASTEST_RESPONSE = "fastest_response"
    CAPABILITY_BASED = "capability_based"


class CircuitBreakerState(Enum):
    """Estados del circuit breaker"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class WorkflowStep:
    """Paso de workflow"""
    step_id: str
    agent_type: str
    capability: AgentCapability
    task: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    parallel_group: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: float = 60.0
    priority: TaskPriority = TaskPriority.NORMAL
    estimated_duration: float = 5.0


@dataclass
class WorkflowExecution:
    """Ejecución de workflow"""
    workflow_id: str
    steps: List[WorkflowStep]
    state: WorkflowState = WorkflowState.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_step_index: int = 0
    step_results: Dict[str, Any] = field(default_factory=dict)
    progress: float = 0.0
    error_message: Optional[str] = None
    priority: TaskPriority = TaskPriority.NORMAL
    
    def add_result(self, step_id: str, result: Any):
        """Añadir resultado de paso"""
        self.step_results[step_id] = result
    
    def is_completed(self) -> bool:
        """Verificar si workflow está completado"""
        return self.state == WorkflowState.COMPLETED
    
    def is_failed(self) -> bool:
        """Verificar si workflow falló"""
        return self.state == WorkflowState.FAILED


class CircuitBreaker:
    """Circuit Breaker para agentes"""
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.success_count = 0
    
    def can_execute(self) -> bool:
        """Verificar si se puede ejecutar"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if self.last_failure_time and datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Registrar éxito"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 2:  # 2 éxitos para cerrar
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
        elif self.state == CircuitBreakerState.CLOSED:
            self.success_count += 1
    
    def record_failure(self):
        """Registrar falla"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN


class LoadBalancer:
    """Load Balancer para agentes"""
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_CONNECTIONS):
        self.strategy = strategy
        self.agent_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "connections": 0,
            "response_times": deque(maxlen=100),
            "success_rate": 1.0,
            "total_requests": 0,
            "last_activity": datetime.now()
        })
        self.round_robin_counter = 0
    
    def select_agent(
        self,
        available_agents: List[BaseAgentWrapper],
        capability: Optional[AgentCapability] = None
    ) -> Optional[BaseAgentWrapper]:
        """Seleccionar mejor agente"""
        if not available_agents:
            return None
        
        # Filtrar por capability si se especifica
        if capability:
            available_agents = [
                agent for agent in available_agents
                if capability in agent.capabilities
            ]
        
        if not available_agents:
            return None
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            agent = available_agents[self.round_robin_counter % len(available_agents)]
            self.round_robin_counter += 1
            return agent
        
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return min(available_agents, key=lambda a: a.current_operations)
        
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_RANDOM:
            weights = []
            for agent in available_agents:
                # Peso basado en capacidad disponible y éxito
                weight = (1.0 - agent.utilization) * agent.get_status()["success_rate"]
                weights.append(max(weight, 0.1))  # Mínimo peso 0.1
            
            # Seleccionar con pesos
            total_weight = sum(weights)
            import random
            rand_val = random.uniform(0, total_weight)
            cumulative = 0
            for i, weight in enumerate(weights):
                cumulative += weight
                if rand_val <= cumulative:
                    return available_agents[i]
            return available_agents[-1]
        
        elif self.strategy == LoadBalancingStrategy.FASTEST_RESPONSE:
            # Ordenar por tiempo promedio de respuesta
            sorted_agents = sorted(
                available_agents,
                key=lambda a: self.agent_stats[a.agent_name]["response_times"]
            )
            return sorted_agents[0] if sorted_agents else None
        
        elif self.strategy == LoadBalancingStrategy.CAPABILITY_BASED:
            # Priorizar agentes con mejor success rate para esta capability
            best_agent = None
            best_score = 0
            
            for agent in available_agents:
                stats = self.agent_stats[agent.agent_name]
                # Score basado en success rate y baja utilización
                score = stats["success_rate"] * (1.0 - agent.utilization)
                if score > best_score:
                    best_score = score
                    best_agent = agent
            
            return best_agent
        
        return available_agents[0]
    
    def update_stats(self, agent_name: str, response_time: float, success: bool):
        """Actualizar estadísticas del agente"""
        stats = self.agent_stats[agent_name]
        stats["response_times"].append(response_time)
        stats["last_activity"] = datetime.now()
        stats["total_requests"] += 1
        
        # Actualizar success rate
        if success:
            # Incrementar éxitos gradualmente
            success_count = int(stats["success_rate"] * stats["total_requests"]) + 1
        else:
            # Decrementar éxitos
            success_count = int(stats["success_rate"] * stats["total_requests"])
        
        stats["success_rate"] = success_count / stats["total_requests"]


class HealthMonitor:
    """Monitor de salud de agentes"""
    
    def __init__(self, check_interval: float = 30.0):
        self.check_interval = check_interval
        self.agent_health: Dict[str, Dict[str, Any]] = {}
        self.monitoring_task: Optional[asyncio.Task] = None
        self.alert_callbacks: List[Callable] = []
    
    async def start_monitoring(self, agents: List[BaseAgentWrapper]):
        """Iniciar monitoreo de salud"""
        if self.monitoring_task:
            return
        
        async def monitor_loop():
            while True:
                try:
                    await self._check_all_agents(agents)
                    await asyncio.sleep(self.check_interval)
                except Exception as e:
                    logging.error(f"Error en health monitor: {e}")
                    await asyncio.sleep(self.check_interval)
        
        self.monitoring_task = asyncio.create_task(monitor_loop())
        logging.info("Health monitoring iniciado")
    
    async def stop_monitoring(self):
        """Detener monitoreo de salud"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
        logging.info("Health monitoring detenido")
    
    async def _check_all_agents(self, agents: List[BaseAgentWrapper]):
        """Verificar salud de todos los agentes"""
        for agent in agents:
            try:
                health = await agent.health_check()
                self.agent_health[agent.agent_name] = health
                
                # Verificar alertas
                if health.get("status") in ["unhealthy", "warning"]:
                    await self._trigger_alert(agent.agent_name, health)
                
            except Exception as e:
                logging.error(f"Error verificando salud de {agent.agent_name}: {e}")
                self.agent_health[agent.agent_name] = {
                    "agent_name": agent.agent_name,
                    "status": "unhealthy",
                    "error": str(e)
                }
    
    async def _trigger_alert(self, agent_name: str, health_data: Dict[str, Any]):
        """Disparar alerta de salud"""
        alert_data = {
            "agent_name": agent_name,
            "timestamp": datetime.now().isoformat(),
            "health_data": health_data
        }
        
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert_data)
                else:
                    callback(alert_data)
            except Exception as e:
                logging.error(f"Error ejecutando callback de alerta: {e}")
        
        logging.warning(f"Alerta de salud para {agent_name}: {health_data.get('status')}")
    
    def add_alert_callback(self, callback: Callable):
        """Añadir callback para alertas"""
        self.alert_callbacks.append(callback)
    
    def get_agent_health(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Obtener salud de un agente"""
        return self.agent_health.get(agent_name)
    
    def get_all_health(self) -> Dict[str, Dict[str, Any]]:
        """Obtener salud de todos los agentes"""
        return self.agent_health.copy()


class TaskQueue:
    """Cola de tareas prioritaria"""
    
    def __init__(self):
        self._queue: List[tuple] = []  # (priority, timestamp, task_id, task)
        self._tasks: Dict[str, WorkflowExecution] = {}
        self._lock = asyncio.Lock()
    
    async def add_task(self, task: WorkflowExecution):
        """Añadir tarea a la cola"""
        async with self._lock:
            priority_value = task.priority.value
            timestamp = task.created_at.timestamp()
            task_id = task.workflow_id
            
            heapq.heappush(self._queue, (priority_value, timestamp, task_id, task))
            self._tasks[task_id] = task
    
    async def get_next_task(self) -> Optional[WorkflowExecution]:
        """Obtener siguiente tarea"""
        async with self._lock:
            if not self._queue:
                return None
            
            priority_value, timestamp, task_id, task = heapq.heappop(self._queue)
            del self._tasks[task_id]
            return task
    
    async def remove_task(self, task_id: str) -> bool:
        """Remover tarea de la cola"""
        async with self._lock:
            if task_id not in self._tasks:
                return False
            
            # Remover de la cola interna (costoso pero necesario)
            new_queue = []
            found = False
            for item in self._queue:
                if item[2] == task_id:
                    found = True
                    continue
                new_queue.append(item)
            
            self._queue = new_queue
            heapq.heapify(self._queue)  # Re-heapify
            del self._tasks[task_id]
            return found
    
    async def get_queue_size(self) -> int:
        """Obtener tamaño de la cola"""
        async with self._lock:
            return len(self._queue)
    
    async def get_task(self, task_id: str) -> Optional[WorkflowExecution]:
        """Obtener tarea por ID"""
        async with self._lock:
            return self._tasks.get(task_id)


class MultiAgentOrchestratorAgentWrapper(BaseAgentWrapper):
    """Wrapper principal para el Multi-Agent Orchestrator Agent MCP"""
    
    def __init__(self):
        # Capacidades avanzadas del orquestrador
        capabilities = [
            AgentCapability.TASK_DECOMPOSITION,
            AgentCapability.TOOL_SELECTION,
            AgentCapability.DEPENDENCY_MANAGEMENT,
            AgentCapability.CONCURRENT_EXECUTION,
            AgentCapability.QUALITY_VALIDATION,
            AgentCapability.KNOWLEDGE_STORAGE
        ]
        
        super().__init__(
            agent_name="multiagent_orchestrator",
            capabilities=capabilities,
            max_concurrent=10,  # Alto número para manejar múltiples workflows
            timeout_seconds=300,  # 5 minutos timeout para workflows complejos
            retry_attempts=3,
            retry_delay=2.0
        )
        
        # Componentes avanzados
        self.load_balancer = LoadBalancer(LoadBalancingStrategy.LEAST_CONNECTIONS)
        self.health_monitor = HealthMonitor(check_interval=30.0)
        self.task_queue = TaskQueue()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self.completed_workflows: Dict[str, WorkflowExecution] = {}
        self.failed_workflows: Dict[str, WorkflowExecution] = {}
        
        # Agentes registrados
        self.base_agents: Dict[str, BaseAgentWrapper] = {}
        self.specialized_agents: Dict[str, BaseAgentWrapper] = {}
        self.agent_profiles: Dict[str, Dict[str, Any]] = {}
        
        # Métricas avanzadas
        self.workflow_metrics = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_completion_time": 0.0,
            "peak_concurrent_workflows": 0,
            "agent_utilization": defaultdict(float)
        }
        
        # Configuración de escalado
        self.max_concurrent_workflows = 20
        self.scaling_enabled = True
        self.auto_scaling_policies = {
            "high_load_threshold": 0.8,
            "low_load_threshold": 0.3,
            "scale_up_factor": 1.5,
            "scale_down_factor": 0.7
        }
        
        # Estado interno
        self.is_running = False
        self.worker_tasks: Set[asyncio.Task] = set()
        
        self.logger.info("MultiAgentOrchestratorAgent inicializado")
    
    async def _initialize(self) -> None:
        """Inicialización del orquestrador"""
        self.logger.info("Inicializando MultiAgentOrchestratorAgent...")
        
        # Registrar agentes base existentes
        await self._register_base_agents()
        
        # Iniciar componentes
        await self.health_monitor.start_monitoring(self._get_all_agents())
        
        # Iniciar worker de tareas
        self.is_running = True
        await self._start_worker_tasks()
        
        self.logger.info("MultiAgentOrchestratorAgent inicializado correctamente")
    
    async def _register_base_agents(self):
        """Registrar agentes base existentes"""
        try:
            # Importar wrappers de agentes base con manejo de errores
            try:
                from .reasoner_wrapper import ReasonerAgentWrapper
                from .planner_wrapper import PlannerAgentWrapper
                from .executor_wrapper import ExecutorAgentWrapper
                from .verifier_wrapper import VerifierAgentWrapper
                from .memory_manager_wrapper import MemoryManagerAgentWrapper
            except ImportError as e:
                self.logger.warning(f"Error importando agentes base: {e}")
                # Crear agentes mock si los reales no están disponibles
                ReasonerAgentWrapper = type('MockAgent', (), {'__init__': lambda s: None, 'ensure_initialized': lambda s: asyncio.sleep(0.1)})
            
            # Crear instancias
            self.base_agents["reasoner"] = ReasonerAgentWrapper()
            self.base_agents["planner"] = PlannerAgentWrapper()
            self.base_agents["executor"] = ExecutorAgentWrapper()
            self.base_agents["verifier"] = VerifierAgentWrapper()
            self.base_agents["memory_manager"] = MemoryManagerAgentWrapper()
            
            # Inicializar agentes
            for agent in self.base_agents.values():
                await agent.ensure_initialized()
            
            self.logger.info(f"Registrados {len(self.base_agents)} agentes base")
            
        except Exception as e:
            self.logger.error(f"Error registrando agentes base: {e}")
            raise
    
    def _get_all_agents(self) -> List[BaseAgentWrapper]:
        """Obtener todos los agentes registrados"""
        return list(self.base_agents.values()) + list(self.specialized_agents.values())
    
    async def _start_worker_tasks(self):
        """Iniciar tareas worker"""
        num_workers = min(5, self.max_concurrent_workflows // 4)
        
        for i in range(num_workers):
            task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.worker_tasks.add(task)
            task.add_done_callback(self.worker_tasks.discard)
        
        self.logger.info(f"Iniciados {num_workers} workers")
    
    async def _worker_loop(self, worker_id: str):
        """Loop principal del worker"""
        self.logger.debug(f"Worker {worker_id} iniciado")
        
        while self.is_running:
            try:
                # Obtener siguiente tarea
                task = await self.task_queue.get_next_task()
                if not task:
                    await asyncio.sleep(0.1)
                    continue
                
                # Ejecutar workflow
                await self._execute_workflow(task)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error en worker {worker_id}: {e}")
                await asyncio.sleep(1.0)
        
        self.logger.debug(f"Worker {worker_id} finalizado")
    
    async def register_specialized_agent(
        self,
        agent_name: str,
        agent_wrapper: BaseAgentWrapper,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Registrar agente especializado dinámicamente"""
        try:
            await agent_wrapper.ensure_initialized()
            
            self.specialized_agents[agent_name] = agent_wrapper
            self.agent_profiles[agent_name] = metadata or {}
            
            # Crear circuit breaker
            self.circuit_breakers[agent_name] = CircuitBreaker(
                failure_threshold=5,
                timeout=60.0
            )
            
            self.logger.info(f"Agente especializado registrado: {agent_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registrando agente {agent_name}: {e}")
            return False
    
    async def create_workflow(
        self,
        objective: str,
        workflow_steps: List[WorkflowStep],
        priority: TaskPriority = TaskPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Crear y encolar workflow"""
        workflow_id = f"workflow_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        workflow = WorkflowExecution(
            workflow_id=workflow_id,
            steps=workflow_steps,
            priority=priority
        )
        
        # Añadir a cola
        await self.task_queue.add_task(workflow)
        
        # Actualizar métricas
        self.workflow_metrics["total_workflows"] += 1
        
        self.logger.info(f"Workflow creado y encolado: {workflow_id} (pasos: {len(workflow_steps)})")
        
        return workflow_id
    
    async def _execute_workflow(self, workflow: WorkflowExecution):
        """Ejecutar workflow completo"""
        workflow.state = WorkflowState.RUNNING
        workflow.started_at = datetime.now()
        
        self.active_workflows[workflow.workflow_id] = workflow
        
        try:
            self.logger.info(f"Iniciando workflow: {workflow.workflow_id}")
            
            # Ejecutar pasos
            completed_steps = set()
            
            for step in workflow.steps:
                # Verificar dependencias
                if not await self._check_dependencies(step, completed_steps):
                    raise OrchestrationException(
                        f"Dependencias no cumplidas para paso {step.step_id}",
                        workflow.workflow_id
                    )
                
                # Ejecutar paso
                result = await self._execute_step(step)
                workflow.add_result(step.step_id, result)
                completed_steps.add(step.step_id)
                
                # Actualizar progreso
                workflow.progress = len(completed_steps) / len(workflow.steps)
                workflow.current_step_index += 1
            
            # Workflow completado
            workflow.state = WorkflowState.COMPLETED
            workflow.completed_at = datetime.now()
            workflow.progress = 1.0
            
            self.completed_workflows[workflow.workflow_id] = workflow
            
            # Actualizar métricas de éxito
            self.workflow_metrics["successful_workflows"] += 1
            
            # Actualizar tiempo promedio de completado
            completion_time = (workflow.completed_at - workflow.started_at).total_seconds()
            self._update_average_completion_time(completion_time)
            
            self.logger.info(f"Workflow completado exitosamente: {workflow.workflow_id}")
            
        except Exception as e:
            workflow.state = WorkflowState.FAILED
            workflow.error_message = str(e)
            workflow.completed_at = datetime.now()
            
            self.failed_workflows[workflow.workflow_id] = workflow
            self.workflow_metrics["failed_workflows"] += 1
            
            self.logger.error(f"Workflow falló: {workflow.workflow_id} - {e}")
            
        finally:
            # Limpiar de workflows activos
            if workflow.workflow_id in self.active_workflows:
                del self.active_workflows[workflow.workflow_id]
    
    async def _check_dependencies(self, step: WorkflowStep, completed_steps: Set[str]) -> bool:
        """Verificar si las dependencias del paso están completadas"""
        for dep in step.dependencies:
            if dep not in completed_steps:
                return False
        return True
    
    async def _execute_step(self, step: WorkflowStep) -> Any:
        """Ejecutar paso individual del workflow"""
        agent_name = step.agent_type
        
        # Verificar circuit breaker
        if agent_name in self.circuit_breakers:
            circuit_breaker = self.circuit_breakers[agent_name]
            if not circuit_breaker.can_execute():
                raise OrchestrationException(
                    f"Circuit breaker abierto para agente {agent_name}",
                    "circuit_breaker"
                )
        
        # Obtener agente
        agent = self._get_agent_by_name(agent_name)
        if not agent:
            raise OrchestrationException(f"Agente no encontrado: {agent_name}", agent_name)
        
        # Verificar capability
        if step.capability not in agent.capabilities:
            raise OrchestrationException(
                f"Agente {agent_name} no tiene capability {step.capability.value}",
                agent_name
            )
        
        # Seleccionar con load balancing
        available_agents = self._get_agents_by_capability(step.capability)
        selected_agent = self.load_balancer.select_agent(available_agents, step.capability)
        
        if not selected_agent:
            raise OrchestrationException(
                f"No hay agentes disponibles para capability {step.capability.value}",
                step.capability.value
            )
        
        # Ejecutar operación
        start_time = time.time()
        
        try:
            result = await agent.execute_operation(
                operation_name=f"workflow_step_{step.step_id}",
                capability=step.capability,
                operation_func=self._execute_agent_operation,
                agent=selected_agent,
                task=step.task,
                timeout=step.timeout
            )
            
            # Registrar éxito en circuit breaker
            if agent_name in self.circuit_breakers:
                self.circuit_breakers[agent_name].record_success()
            
            # Actualizar load balancer stats
            response_time = time.time() - start_time
            self.load_balancer.update_stats(selected_agent.agent_name, response_time, True)
            
            return result
            
        except Exception as e:
            # Registrar falla en circuit breaker
            if agent_name in self.circuit_breakers:
                self.circuit_breakers[agent_name].record_failure()
            
            # Actualizar load balancer stats
            response_time = time.time() - start_time
            self.load_balancer.update_stats(selected_agent.agent_name, response_time, False)
            
            # Incrementar retry count
            step.retry_count += 1
            
            if step.retry_count <= step.max_retries:
                self.logger.warning(
                    f"Reintentando paso {step.step_id} (intento {step.retry_count}/{step.max_retries})"
                )
                await asyncio.sleep(step.retry_count * 2)  # Backoff exponencial
                return await self._execute_step(step)
            else:
                raise OrchestrationException(
                    f"Paso {step.step_id} falló después de {step.max_retries} intentos: {str(e)}",
                    step.step_id
                )
    
    async def _execute_agent_operation(
        self,
        agent: BaseAgentWrapper,
        task: Dict[str, Any],
        timeout: float = 60.0
    ) -> Any:
        """Ejecutar operación en agente con timeout"""
        return await asyncio.wait_for(
            agent.process_request(task),
            timeout=timeout
        )
    
    def _get_agent_by_name(self, agent_name: str) -> Optional[BaseAgentWrapper]:
        """Obtener agente por nombre"""
        return self.base_agents.get(agent_name) or self.specialized_agents.get(agent_name)
    
    def _get_agents_by_capability(self, capability: AgentCapability) -> List[BaseAgentWrapper]:
        """Obtener agentes que soportan una capability"""
        agents = []
        
        for agent in self._get_all_agents():
            if capability in agent.capabilities:
                agents.append(agent)
        
        return agents
    
    def _update_average_completion_time(self, new_time: float):
        """Actualizar tiempo promedio de completado"""
        current_avg = self.workflow_metrics["average_completion_time"]
        total_workflows = self.workflow_metrics["successful_workflows"]
        
        if total_workflows == 1:
            self.workflow_metrics["average_completion_time"] = new_time
        else:
            # Promedio móvil
            self.workflow_metrics["average_completion_time"] = (
                (current_avg * (total_workflows - 1) + new_time) / total_workflows
            )
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de workflow"""
        # Buscar en workflows activos
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            return {
                "workflow_id": workflow.workflow_id,
                "state": workflow.state.value,
                "progress": workflow.progress,
                "current_step_index": workflow.current_step_index,
                "total_steps": len(workflow.steps),
                "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
                "duration": (datetime.now() - workflow.created_at).total_seconds(),
                "priority": workflow.priority.value
            }
        
        # Buscar en completados
        if workflow_id in self.completed_workflows:
            workflow = self.completed_workflows[workflow_id]
            return {
                "workflow_id": workflow.workflow_id,
                "state": workflow.state.value,
                "progress": 1.0,
                "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
                "duration": (workflow.completed_at - workflow.started_at).total_seconds() if workflow.completed_at else None
            }
        
        # Buscar en fallidos
        if workflow_id in self.failed_workflows:
            workflow = self.failed_workflows[workflow_id]
            return {
                "workflow_id": workflow.workflow_id,
                "state": workflow.state.value,
                "error_message": workflow.error_message,
                "failed_at": workflow.completed_at.isoformat() if workflow.completed_at else None
            }
        
        return None
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancelar workflow"""
        # Remover de cola si está pendiente
        if await self.task_queue.remove_task(workflow_id):
            self.logger.info(f"Workflow {workflow_id} removido de la cola")
            return True
        
        # Marcar como cancelado si está activo
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            workflow.state = WorkflowState.CANCELLED
            workflow.completed_at = datetime.now()
            
            self.logger.info(f"Workflow {workflow_id} cancelado")
            return True
        
        return False
    
    async def get_orchestrator_status(self) -> Dict[str, Any]:
        """Obtener estado completo del orquestrador"""
        all_agents = self._get_all_agents()
        
        return {
            "agent_name": self.agent_name,
            "status": self.status.value,
            "is_ready": self.is_ready,
            "active_workflows": len(self.active_workflows),
            "completed_workflows": len(self.completed_workflows),
            "failed_workflows": len(self.failed_workflows),
            "queued_tasks": await self.task_queue.get_queue_size(),
            "registered_agents": {
                "base": len(self.base_agents),
                "specialized": len(self.specialized_agents),
                "total": len(all_agents)
            },
            "workflow_metrics": self.workflow_metrics.copy(),
            "load_balancer": {
                "strategy": self.load_balancer.strategy.value,
                "agent_stats": dict(self.load_balancer.agent_stats)
            },
            "circuit_breakers": {
                agent_name: cb.state.value
                for agent_name, cb in self.circuit_breakers.items()
            },
            "health_status": self.health_monitor.get_all_health(),
            "scaling": {
                "enabled": self.scaling_enabled,
                "max_concurrent_workflows": self.max_concurrent_workflows,
                "current_concurrent": len(self.active_workflows),
                "utilization": len(self.active_workflows) / self.max_concurrent_workflows
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check completo del orquestrador"""
        try:
            # Verificar componentes
            health_status = {
                "agent_name": self.agent_name,
                "status": "healthy",
                "components": {
                    "task_queue": await self.task_queue.get_queue_size() >= 0,
                    "load_balancer": True,
                    "health_monitor": self.health_monitor.monitoring_task is not None,
                    "workers": len(self.worker_tasks),
                    "base_agents": len(self.base_agents),
                    "specialized_agents": len(self.specialized_agents)
                },
                "metrics": {
                    "active_workflows": len(self.active_workflows),
                    "success_rate": (
                        self.workflow_metrics["successful_workflows"] / 
                        max(self.workflow_metrics["total_workflows"], 1)
                    ),
                    "average_completion_time": self.workflow_metrics["average_completion_time"]
                }
            }
            
            # Verificar salud de agentes
            agent_health = self.health_monitor.get_all_health()
            unhealthy_agents = [
                name for name, health in agent_health.items()
                if health.get("status") == "unhealthy"
            ]
            
            if unhealthy_agents:
                health_status["status"] = "warning"
                health_status["unhealthy_agents"] = unhealthy_agents
            
            # Verificar circuit breakers abiertos
            open_circuits = [
                name for name, cb in self.circuit_breakers.items()
                if cb.state == CircuitBreakerState.OPEN
            ]
            
            if open_circuits:
                health_status["status"] = "warning"
                health_status["open_circuits"] = open_circuits
            
            return health_status
            
        except Exception as e:
            return {
                "agent_name": self.agent_name,
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def process_request(
        self,
        request: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Procesar request MCP del orquestrador
        
        Request tipos:
        - create_workflow: Crear y ejecutar workflow
        - register_agent: Registrar agente especializado
        - get_workflow_status: Obtener estado de workflow
        - cancel_workflow: Cancelar workflow
        - get_status: Obtener estado del orquestrador
        - get_health: Health check
        """
        request_type = request.get("type")
        
        try:
            await self.ensure_initialized()
            
            if request_type == "create_workflow":
                return await self._handle_create_workflow(request, context)
            
            elif request_type == "register_agent":
                return await self._handle_register_agent(request, context)
            
            elif request_type == "get_workflow_status":
                return await self._handle_get_workflow_status(request, context)
            
            elif request_type == "cancel_workflow":
                return await self._handle_cancel_workflow(request, context)
            
            elif request_type == "get_status":
                return await self._handle_get_status(request, context)
            
            elif request_type == "get_health":
                health = await self.health_check()
                return {"success": True, "health": health}
            
            elif request_type == "list_agents":
                return await self._handle_list_agents(request, context)
            
            elif request_type == "get_workflows":
                return await self._handle_get_workflows(request, context)
            
            else:
                raise OrchestrationException(f"Tipo de request no soportado: {request_type}", "unknown")
                
        except Exception as e:
            self.logger.error(f"Error procesando request {request_type}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def _handle_create_workflow(self, request: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Manejar creación de workflow"""
        objective = request.get("objective", "")
        steps_data = request.get("steps", [])
        priority = TaskPriority(request.get("priority", TaskPriority.NORMAL.value))
        
        # Convertir steps data a WorkflowStep objects
        steps = []
        for step_data in steps_data:
            step = WorkflowStep(
                step_id=step_data["step_id"],
                agent_type=step_data["agent_type"],
                capability=AgentCapability(step_data["capability"]),
                task=step_data["task"],
                dependencies=step_data.get("dependencies", []),
                parallel_group=step_data.get("parallel_group"),
                max_retries=step_data.get("max_retries", 3),
                timeout=step_data.get("timeout", 60.0),
                priority=TaskPriority(step_data.get("priority", TaskPriority.NORMAL.value))
            )
            steps.append(step)
        
        # Crear workflow
        workflow_id = await self.create_workflow(objective, steps, priority)
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "message": f"Workflow creado exitosamente con {len(steps)} pasos"
        }
    
    async def _handle_register_agent(self, request: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Manejar registro de agente"""
        agent_name = request.get("agent_name")
        agent_data = request.get("agent_data", {})
        
        if not agent_name:
            raise OrchestrationException("agent_name es requerido", "invalid_request")
        
        # Crear wrapper básico si no se proporciona
        agent_wrapper = agent_data.get("agent_wrapper")
        if not agent_wrapper:
            # Crear wrapper dinámico básico
            agent_wrapper = BaseAgentWrapper(
                agent_name=agent_name,
                capabilities=[AgentCapability(cap) for cap in agent_data.get("capabilities", [])],
                max_concurrent=agent_data.get("max_concurrent", 3),
                timeout_seconds=agent_data.get("timeout_seconds", 60)
            )
        
        # Registrar agente
        success = await self.register_specialized_agent(
            agent_name,
            agent_wrapper,
            agent_data.get("metadata")
        )
        
        return {
            "success": success,
            "agent_name": agent_name,
            "message": f"Agente {'registrado' if success else 'falló al registrarse'}"
        }
    
    async def _handle_get_workflow_status(self, request: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Manejar consulta de estado de workflow"""
        workflow_id = request.get("workflow_id")
        if not workflow_id:
            raise OrchestrationException("workflow_id es requerido", "invalid_request")
        
        status = await self.get_workflow_status(workflow_id)
        
        return {
            "success": True,
            "status": status
        }
    
    async def _handle_cancel_workflow(self, request: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Manejar cancelación de workflow"""
        workflow_id = request.get("workflow_id")
        if not workflow_id:
            raise OrchestrationException("workflow_id es requerido", "invalid_request")
        
        cancelled = await self.cancel_workflow(workflow_id)
        
        return {
            "success": cancelled,
            "workflow_id": workflow_id,
            "message": f"Workflow {'cancelado' if cancelled else 'no encontrado'}"
        }
    
    async def _handle_get_status(self, request: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Manejar consulta de estado"""
        status = await self.get_orchestrator_status()
        
        return {
            "success": True,
            "status": status
        }
    
    async def _handle_list_agents(self, request: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Manejar listado de agentes"""
        agents_info = {}
        
        for name, agent in self.base_agents.items():
            agents_info[name] = {
                "type": "base",
                "status": agent.status.value,
                "capabilities": [cap.value for cap in agent.capabilities]
            }
        
        for name, agent in self.specialized_agents.items():
            agents_info[name] = {
                "type": "specialized",
                "status": agent.status.value,
                "capabilities": [cap.value for cap in agent.capabilities],
                "metadata": self.agent_profiles.get(name, {})
            }
        
        return {
            "success": True,
            "agents": agents_info,
            "total": len(agents_info)
        }
    
    async def _handle_get_workflows(self, request: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Manejar listado de workflows"""
        status_filter = request.get("status", "all")
        limit = request.get("limit", 20)
        
        workflows = {}
        
        # Filtrar por estado
        if status_filter in ["active", "all"]:
            for workflow_id, workflow in list(self.active_workflows.items())[:limit]:
                workflows[workflow_id] = {
                    "state": workflow.state.value,
                    "progress": workflow.progress,
                    "created_at": workflow.created_at.isoformat(),
                    "started_at": workflow.started_at.isoformat() if workflow.started_at else None
                }
        
        if status_filter in ["completed", "all"]:
            for workflow_id, workflow in list(self.completed_workflows.items())[-limit:]:
                workflows[workflow_id] = {
                    "state": workflow.state.value,
                    "progress": 1.0,
                    "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
                    "duration": (workflow.completed_at - workflow.started_at).total_seconds() if workflow.completed_at else None
                }
        
        if status_filter in ["failed", "all"]:
            for workflow_id, workflow in list(self.failed_workflows.items())[-limit:]:
                workflows[workflow_id] = {
                    "state": workflow.state.value,
                    "error_message": workflow.error_message,
                    "failed_at": workflow.completed_at.isoformat() if workflow.completed_at else None
                }
        
        return {
            "success": True,
            "workflows": workflows,
            "count": len(workflows)
        }
    
    async def cleanup(self):
        """Limpiar recursos del orquestrador"""
        self.is_running = False
        
        # Cancelar workers
        for task in self.worker_tasks:
            task.cancel()
        
        # Esperar a que terminen
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        # Detener health monitor
        await self.health_monitor.stop_monitoring()
        
        self.worker_tasks.clear()
        self.active_workflows.clear()
        
        self.logger.info("MultiAgentOrchestratorAgent limpiado")
    
    def __str__(self) -> str:
        return f"MultiAgentOrchestratorAgent(status={self.status.value}, workflows={len(self.active_workflows)})"
    
    def __repr__(self) -> str:
        return (
            f"MultiAgentOrchestratorAgent("
            f"base_agents={len(self.base_agents)}, "
            f"specialized_agents={len(self.specialized_agents)}, "
            f"active_workflows={len(self.active_workflows)}, "
            f"status={self.status.value}"
            f")"
        )