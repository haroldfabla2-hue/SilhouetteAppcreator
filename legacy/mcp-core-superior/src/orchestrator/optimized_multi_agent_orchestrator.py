"""
Sistema de Orquestación Multi-Agente Optimizado
Integra routing inteligente, load balancing, fault tolerance y 20+ agentes especializados
Capaz de manejar hasta 100+ tareas concurrentes
"""
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import uuid
import statistics
from collections import defaultdict, deque
import json

from ..core.exceptions import OrchestrationException, OptimizationException
from ..orchestrator.intelligent_routing_system import IntelligentRoutingSystem, RoutingStrategy
from ..orchestrator.advanced_load_balancer import AdvancedLoadBalancer, LoadBalancingStrategy
from .intelligent_routing_system import AgentCapabilities


class OrchestrationMode(Enum):
    """Modos de orquestación"""
    SINGLE_AGENT = "single_agent"
    MULTI_AGENT = "multi_agent"
    PARALLEL = "parallel"
    CASCADING = "cascading"
    ADAPTIVE = "adaptive"


class TaskComplexity(Enum):
    """Niveles de complejidad de tareas"""
    SIMPLE = "simple"           # 1 agente, < 5 segundos
    MODERATE = "moderate"       # 1-3 agentes, 5-30 segundos  
    COMPLEX = "complex"         # 3-7 agentes, 30-300 segundos
    ENTERPRISE = "enterprise"   # 7-20 agentes, > 5 minutos


@dataclass
class TaskRequirements:
    """Requisitos de una tarea"""
    task_id: str
    task_type: str
    complexity: TaskComplexity
    required_skills: List[str]
    domain: str
    priority: int
    max_duration: float
    fallback_agents: List[str]
    dependencies: Set[str]
    resource_requirements: Dict[str, Any]
    quality_threshold: float
    max_concurrent_tasks: int
    routing_strategy: RoutingStrategy
    load_balancing_strategy: LoadBalancingStrategy


@dataclass
class OrchestrationMetrics:
    """Métricas de orquestación"""
    total_orchestrations: int = 0
    successful_orchestrations: int = 0
    failed_orchestrations: int = 0
    average_duration: float = 0.0
    throughput: float = 0.0
    resource_utilization: float = 0.0
    agent_efficiency: Dict[str, float] = None
    optimization_suggestions: List[str] = None
    
    def __post_init__(self):
        if self.agent_efficiency is None:
            self.agent_efficiency = {}
        if self.optimization_suggestions is None:
            self.optimization_suggestions = []


class OptimizedMultiAgentOrchestrator:
    """Orquestador multi-agente optimizado para 20+ agentes"""
    
    def __init__(self):
        self.logger = logging.getLogger("mcp.orchestrator.optimized")
        
        # Componentes core del sistema
        self.routing_system: Optional[IntelligentRoutingSystem] = None
        self.load_balancer: Optional[AdvancedLoadBalancer] = None
        
        # Gestión de tareas y workflows
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.completed_workflows: Dict[str, Dict[str, Any]] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.workflow_history: deque = deque(maxlen=1000)
        
        # Métricas y optimización
        self.metrics = OrchestrationMetrics()
        self.performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.adaptation_cache: Dict[str, Any] = {}
        
        # Configuración de optimización
        self.enable_adaptive_routing = True
        self.enable_predictive_scaling = True
        self.auto_optimization_interval = 300  # 5 minutos
        self.max_concurrent_workflows = 50
        
        self.is_initialized = False
        self.optimization_task: Optional[asyncio.Task] = None
    
    async def initialize(self, agent_configs: Dict[str, Any]) -> None:
        """Inicializar orquestador optimizado"""
        
        # Inicializar sistemas base
        self.routing_system = IntelligentRoutingSystem()
        await self.routing_system.initialize(agent_configs)
        
        self.load_balancer = AdvancedLoadBalancer(self.routing_system)
        await self.load_balancer.initialize(agent_configs)
        
        # Iniciar optimización automática
        if self.enable_adaptive_routing:
            self.optimization_task = asyncio.create_task(self._auto_optimization_loop())
        
        self.is_initialized = True
        self.logger.info(
            f"Orquestador optimizado inicializado con {len(agent_configs)} agentes "
            f"y capacidad de {self.max_concurrent_workflows} workflows concurrentes"
        )
    
    async def orchestrate_complex_workflow(
        self,
        workflow_definition: Dict[str, Any],
        mode: OrchestrationMode = OrchestrationMode.ADAPTIVE,
        optimization_level: str = "balanced"  # fast, balanced, quality
    ) -> Dict[str, Any]:
        """Ejecutar workflow complejo con optimización automática"""
        
        if not self.is_initialized:
            raise OrchestrationException("Orquestador no inicializado")
        
        workflow_id = f"workflow_{uuid.uuid4()}"
        start_time = time.time()
        
        try:
            self.logger.info(f"Iniciando workflow complejo: {workflow_id[:8]}")
            
            # Analizar y optimizar workflow
            optimized_workflow = await self._optimize_workflow(workflow_definition, optimization_level)
            
            # Ejecutar según modo
            if mode == OrchestrationMode.SINGLE_AGENT:
                result = await self._execute_single_agent_workflow(workflow_id, optimized_workflow)
            elif mode == OrchestrationMode.PARALLEL:
                result = await self._execute_parallel_workflow(workflow_id, optimized_workflow)
            elif mode == OrchestrationMode.CASCADING:
                result = await self._execute_cascading_workflow(workflow_id, optimized_workflow)
            else:  # ADAPTIVE
                result = await self._execute_adaptive_workflow(workflow_id, optimized_workflow)
            
            # Actualizar métricas
            await self._update_metrics(result, time.time() - start_time)
            
            # Almacenar en historial
            self.workflow_history.append({
                "workflow_id": workflow_id,
                "timestamp": datetime.now(),
                "result": result,
                "duration": time.time() - start_time
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error en workflow {workflow_id}: {e}")
            raise OrchestrationException(f"Error ejecutando workflow: {str(e)}", workflow_id)
    
    async def _optimize_workflow(
        self, 
        workflow_definition: Dict[str, Any], 
        optimization_level: str
    ) -> Dict[str, Any]:
        """Optimizar workflow antes de ejecución"""
        
        # Extraer tareas del workflow
        tasks = workflow_definition.get("tasks", [])
        if not tasks:
            return workflow_definition
        
        # Crear TaskRequirements para cada tarea
        optimized_tasks = []
        
        for task_def in tasks:
            task_req = TaskRequirements(
                task_id=task_def.get("id", f"task_{uuid.uuid4()}"),
                task_type=task_def.get("type", "general"),
                complexity=self._determine_task_complexity(task_def),
                required_skills=task_def.get("required_skills", []),
                domain=task_def.get("domain", "general"),
                priority=task_def.get("priority", 5),
                max_duration=task_def.get("max_duration", 300.0),
                fallback_agents=task_def.get("fallback_agents", []),
                dependencies=set(task_def.get("dependencies", [])),
                resource_requirements=task_def.get("resource_requirements", {}),
                quality_threshold=task_def.get("quality_threshold", 0.8),
                max_concurrent_tasks=task_def.get("max_concurrent_tasks", 1),
                routing_strategy=self._select_routing_strategy(task_def, optimization_level),
                load_balancing_strategy=self._select_load_balancing_strategy(task_def, optimization_level)
            )
            optimized_tasks.append(task_req)
        
        # Optimizar dependencias y orden de ejecución
        optimized_order = self._optimize_task_execution_order(optimized_tasks)
        
        return {
            "tasks": [task.__dict__ for task in optimized_order],
            "optimization_level": optimization_level,
            "estimated_duration": self._estimate_workflow_duration(optimized_order),
            "parallel_groups": self._identify_parallel_groups(optimized_order)
        }
    
    def _determine_task_complexity(self, task_def: Dict[str, Any]) -> TaskComplexity:
        """Determinar complejidad de tarea"""
        
        # Factores de complejidad
        required_skills_count = len(task_def.get("required_skills", []))
        max_duration = task_def.get("max_duration", 300)
        has_dependencies = len(task_def.get("dependencies", [])) > 0
        priority = task_def.get("priority", 5)
        
        # Determinar complejidad
        if (required_skills_count <= 1 and max_duration < 5 and not has_dependencies):
            return TaskComplexity.SIMPLE
        elif (required_skills_count <= 3 and max_duration < 30 and not has_dependencies):
            return TaskComplexity.MODERATE
        elif (required_skills_count <= 7 and max_duration < 300):
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.ENTERPRISE
    
    def _select_routing_strategy(
        self, 
        task_def: Dict[str, Any], 
        optimization_level: str
    ) -> RoutingStrategy:
        """Seleccionar estrategia de routing óptima"""
        
        if optimization_level == "fast":
            return RoutingStrategy.LEAST_CONNECTIONS
        elif optimization_level == "quality":
            return RoutingStrategy.QUALITY_BASED
        else:  # balanced
            complexity = self._determine_task_complexity(task_def)
            if complexity == TaskComplexity.ENTERPRISE:
                return RoutingStrategy.LEARNING_BASED
            else:
                return RoutingStrategy.CAPACITY_BASED
    
    def _select_load_balancing_strategy(
        self, 
        task_def: Dict[str, Any], 
        optimization_level: str
    ) -> LoadBalancingStrategy:
        """Seleccionar estrategia de load balancing óptima"""
        
        if optimization_level == "fast":
            return LoadBalancingStrategy.LEAST_CONNECTIONS
        elif optimization_level == "quality":
            return LoadBalancingStrategy.WEIGHTED
        else:  # balanced
            return LoadBalancingStrategy.ADAPTIVE
    
    def _optimize_task_execution_order(self, tasks: List[TaskRequirements]) -> List[TaskRequirements]:
        """Optimizar orden de ejecución basado en dependencias y prioridades"""
        
        # Topological sort con prioridades
        task_dict = {task.task_id: task for task in tasks}
        in_degree = {task.task_id: 0 for task in tasks}
        
        # Calcular grados de entrada
        for task in tasks:
            for dep in task.dependencies:
                if dep in in_degree:
                    in_degree[task.task_id] += 1
        
        # Orden topológico con prioridad
        result = []
        ready_queue = [task for task in tasks if in_degree[task.task_id] == 0]
        ready_queue.sort(key=lambda x: x.priority, reverse=True)
        
        while ready_queue:
            current_task = ready_queue.pop(0)
            result.append(current_task)
            
            # Encontrar tareas que dependen de la actual
            for task in tasks:
                if current_task.task_id in task.dependencies:
                    in_degree[task.task_id] -= 1
                    if in_degree[task.task_id] == 0:
                        ready_queue.append(task)
                        ready_queue.sort(key=lambda x: x.priority, reverse=True)
        
        return result
    
    def _identify_parallel_groups(self, tasks: List[TaskRequirements]) -> List[List[str]]:
        """Identificar grupos de tareas que pueden ejecutarse en paralelo"""
        
        parallel_groups = []
        processed_tasks = set()
        
        for task in tasks:
            if task.task_id in processed_tasks:
                continue
            
            # Encontrar tareas paralelas (sin dependencias entre sí)
            parallel_group = []
            for other_task in tasks:
                if (other_task.task_id != task.task_id and 
                    other_task.task_id not in processed_tasks and
                    not task.dependencies.intersection({other_task.task_id}) and
                    not other_task.dependencies.intersection({task.task_id})):
                    
                    parallel_group.append(other_task.task_id)
                    processed_tasks.add(other_task.task_id)
            
            if parallel_group:
                parallel_groups.append(parallel_group)
            
            processed_tasks.add(task.task_id)
        
        return parallel_groups
    
    def _estimate_workflow_duration(self, tasks: List[TaskRequirements]) -> float:
        """Estimar duración del workflow"""
        
        # Estimación simplificada: suma de tareas en secuencia crítica
        # En implementación real sería más sofisticada
        
        max_duration = 0.0
        for task in tasks:
            # Buscar dependencias que aumenten la duración
            duration = task.max_duration
            if task.complexity == TaskComplexity.SIMPLE:
                duration *= 0.5
            elif task.complexity == TaskComplexity.MODERATE:
                duration *= 0.8
            elif task.complexity == TaskComplexity.COMPLEX:
                duration *= 1.2
            else:  # ENTERPRISE
                duration *= 1.5
            
            max_duration += duration
        
        return max_duration
    
    async def _execute_adaptive_workflow(
        self, 
        workflow_id: str, 
        workflow_definition: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ejecutar workflow en modo adaptativo"""
        
        tasks = workflow_definition.get("tasks", [])
        parallel_groups = workflow_definition.get("parallel_groups", [])
        results = {}
        
        # Ejecutar grupos paralelos en secuencia
        for group_idx, parallel_group in enumerate(parallel_groups):
            group_tasks = [task for task in tasks if task["task_id"] in parallel_group]
            
            # Ejecutar tareas del grupo en paralelo
            if group_tasks:
                group_results = await asyncio.gather(*[
                    self._execute_single_task(task["task_id"], task)
                    for task in group_tasks
                ], return_exceptions=True)
                
                # Procesar resultados del grupo
                for i, result in enumerate(group_results):
                    task_id = group_tasks[i]["task_id"]
                    if isinstance(result, Exception):
                        self.logger.error(f"Error en tarea {task_id}: {result}")
                        results[task_id] = {"success": False, "error": str(result)}
                    else:
                        results[task_id] = result
        
        # Procesar tareas restantes (sin dependencias paralelas)
        remaining_tasks = [task for task in tasks if task["task_id"] not in results]
        for task in remaining_tasks:
            result = await self._execute_single_task(task["task_id"], task)
            results[task["task_id"]] = result
        
        # Formatear resultado final
        success_rate = sum(1 for r in results.values() if r.get("success", False)) / max(len(results), 1)
        
        return {
            "workflow_id": workflow_id,
            "success": success_rate > 0.8,
            "success_rate": success_rate,
            "task_results": results,
            "execution_mode": "adaptive",
            "duration": time.time(),
            "optimization_applied": True
        }
    
    async def _execute_single_task(
        self, 
        task_id: str, 
        task_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ejecutar una sola tarea"""
        
        # Usar load balancer para seleccionar agente
        agent_type = await self.load_balancer.select_optimal_agent(
            task_requirements,
            fallback_agents=task_requirements.get("fallback_agents", [])
        )
        
        if not agent_type:
            return {"success": False, "error": "No agent available"}
        
        # Ejecutar tarea con fault tolerance
        try:
            result = await self._execute_task_with_agent(agent_type, task_requirements)
            
            # Registrar resultado
            await self.load_balancer.record_task_completion(
                agent_type, 
                result, 
                result.get("duration", 1.0)
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error ejecutando tarea {task_id} con agente {agent_type}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_task_with_agent(
        self, 
        agent_type: str, 
        task_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ejecutar tarea con agente específico"""
        
        # Simular ejecución - en implementación real sería llamada real al agente
        await asyncio.sleep(0.5 + random.uniform(0, 2))
        
        # Obtener métricas del agente
        capabilities = self.routing_system.agent_registry.get(agent_type)
        if not capabilities:
            raise Exception(f"Agente {agent_type} no encontrado")
        
        # Simular resultado basado en capacidades del agente
        success_probability = capabilities.success_rate
        quality_score = capabilities.quality_score * random.uniform(0.8, 1.2)
        
        return {
            "success": random.random() < success_probability,
            "agent_type": agent_type,
            "quality_score": min(1.0, quality_score),
            "duration": capabilities.avg_response_time * random.uniform(0.8, 1.5),
            "result": f"Task completed by {agent_type}",
            "performance_metrics": {
                "response_time": capabilities.avg_response_time,
                "success_rate": capabilities.success_rate,
                "resource_utilization": random.uniform(0.3, 0.9)
            }
        }
    
    async def _execute_single_agent_workflow(self, workflow_id: str, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecución secuencial simple (fallback)"""
        tasks = workflow_definition.get("tasks", [])
        results = {}
        
        for task in tasks:
            result = await self._execute_single_task(task["task_id"], task)
            results[task["task_id"]] = result
        
        success_rate = sum(1 for r in results.values() if r.get("success", False)) / max(len(results), 1)
        
        return {
            "workflow_id": workflow_id,
            "success": success_rate > 0.8,
            "success_rate": success_rate,
            "task_results": results,
            "execution_mode": "single_agent"
        }
    
    async def _execute_parallel_workflow(self, workflow_id: str, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecución completamente paralela"""
        tasks = workflow_definition.get("tasks", [])
        
        # Ejecutar todas las tareas en paralelo
        results = await asyncio.gather(*[
            self._execute_single_task(task["task_id"], task)
            for task in tasks
        ], return_exceptions=True)
        
        # Procesar resultados
        task_results = {}
        for i, result in enumerate(results):
            task_id = tasks[i]["task_id"]
            if isinstance(result, Exception):
                task_results[task_id] = {"success": False, "error": str(result)}
            else:
                task_results[task_id] = result
        
        success_rate = sum(1 for r in task_results.values() if r.get("success", False)) / max(len(task_results), 1)
        
        return {
            "workflow_id": workflow_id,
            "success": success_rate > 0.8,
            "success_rate": success_rate,
            "task_results": task_results,
            "execution_mode": "parallel"
        }
    
    async def _execute_cascading_workflow(self, workflow_id: str, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecución en cascada (todas las tareas secuenciales)"""
        # Similar a single agent pero con logging detallado
        return await self._execute_single_agent_workflow(workflow_id, workflow_definition)
    
    async def _update_metrics(self, result: Dict[str, Any], duration: float) -> None:
        """Actualizar métricas de orquestación"""
        
        self.metrics.total_orchestrations += 1
        
        if result.get("success", False):
            self.metrics.successful_orchestrations += 1
        else:
            self.metrics.failed_orchestrations += 1
        
        # Actualizar duración promedio
        durations = [duration] + [d for d in self.performance_history.get("durations", [])]
        self.metrics.average_duration = statistics.mean(durations[-10:])  # Últimas 10
        
        # Actualizar throughput (última hora)
        current_time = datetime.now()
        recent_orchestrations = [
            w for w in self.workflow_history 
            if (current_time - w["timestamp"]).total_seconds() < 3600
        ]
        self.metrics.throughput = len(recent_orchestrations) / 3600  # orchestrations per second
        
        # Actualizar eficiencia de agentes
        task_results = result.get("task_results", {})
        for task_id, task_result in task_results.items():
            agent_type = task_result.get("agent_type")
            if agent_type:
                success = 1.0 if task_result.get("success", False) else 0.0
                current_efficiency = self.metrics.agent_efficiency.get(agent_type, 0.0)
                # Moving average
                new_efficiency = current_efficiency * 0.8 + success * 0.2
                self.metrics.agent_efficiency[agent_type] = new_efficiency
    
    async def _auto_optimization_loop(self) -> None:
        """Loop de optimización automática"""
        while self.is_initialized:
            try:
                await self._optimize_system_performance()
                await asyncio.sleep(self.auto_optimization_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error en optimización automática: {e}")
                await asyncio.sleep(60)  # Retry más rápido en caso de error
    
    async def _optimize_system_performance(self) -> None:
        """Optimizar performance del sistema"""
        
        # Obtener métricas actuales
        routing_status = await self.routing_system.get_routing_status()
        load_balancer_status = await self.load_balancer.get_load_balancing_status()
        
        # Generar sugerencias de optimización
        suggestions = []
        
        # Analizar utilización de agentes
        agents = routing_status.get("agents", {})
        for agent_id, agent_info in agents.items():
            utilization = agent_info.get("utilization", 0)
            
            if utilization > 0.9:
                suggestions.append(f"Agente {agent_id}: Alta utilización ({utilization:.1%}) - considerar escalar")
            elif utilization < 0.2:
                suggestions.append(f"Agente {agent_id}: Baja utilización ({utilization:.1%}) - considerar redistribuir")
        
        # Analizar distribución de carga
        lb_status = load_balancer_status.get("request_distribution", {})
        if lb_status:
            max_requests = max(lb_status.values()) if lb_status else 0
            min_requests = min(lb_status.values()) if lb_status else 0
            
            if max_requests / max(min_requests, 1) > 3:
                suggestions.append("Distribución de carga desbalanceada - revisar estrategias")
        
        self.metrics.optimization_suggestions = suggestions
        
        if suggestions:
            self.logger.info(f"Optimización automática aplicada: {len(suggestions)} sugerencias generadas")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema"""
        
        routing_status = await self.routing_system.get_routing_status() if self.routing_system else {}
        load_balancer_status = await self.load_balancer.get_load_balancing_status() if self.load_balancer else {}
        
        # Calcular métricas agregadas
        total_capacity = sum(
            agent_info.get("max_capacity", 0) 
            for agent_info in routing_status.get("agents", {}).values()
        )
        used_capacity = sum(
            agent_info.get("active_tasks", 0) 
            for agent_info in routing_status.get("agents", {}).values()
        )
        
        system_utilization = used_capacity / max(total_capacity, 1)
        success_rate = self.metrics.successful_orchestrations / max(self.metrics.total_orchestrations, 1)
        
        return {
            "system_status": "healthy" if success_rate > 0.8 else "degraded",
            "initialization": self.is_initialized,
            "current_workflows": len(self.active_workflows),
            "completed_workflows": len(self.completed_workflows),
            "system_utilization": system_utilization,
            "total_agents": routing_status.get("total_agents", 0),
            "active_agents": routing_status.get("active_agents", 0),
            "routing_system": routing_status,
            "load_balancer": load_balancer_status,
            "metrics": {
                "total_orchestrations": self.metrics.total_orchestrations,
                "success_rate": success_rate,
                "average_duration": self.metrics.average_duration,
                "throughput": self.metrics.throughput,
                "agent_efficiency": self.metrics.agent_efficiency,
                "optimization_suggestions": self.metrics.optimization_suggestions
            }
        }
    
    async def execute_stress_test(self, concurrent_workflows: int = 10, tasks_per_workflow: int = 5) -> Dict[str, Any]:
        """Ejecutar test de estrés del sistema"""
        
        self.logger.info(f"Iniciando stress test: {concurrent_workflows} workflows, {tasks_per_workflow} tareas c/u")
        
        start_time = time.time()
        stress_test_id = f"stress_test_{uuid.uuid4()}"
        
        # Crear workflows de prueba
        test_workflows = []
        for i in range(concurrent_workflows):
            workflow = {
                "id": f"test_workflow_{i}",
                "tasks": []
            }
            
            for j in range(tasks_per_workflow):
                task = {
                    "id": f"task_{i}_{j}",
                    "type": "test_task",
                    "required_skills": ["test_execution"],
                    "priority": 5,
                    "max_duration": 5.0,
                    "fallback_agents": ["python_executor_agent"]
                }
                workflow["tasks"].append(task)
            
            test_workflows.append(workflow)
        
        # Ejecutar todos los workflows en paralelo
        start_execution = time.time()
        results = await asyncio.gather(*[
            self.orchestrate_complex_workflow(workflow, OrchestrationMode.ADAPTIVE, "balanced")
            for workflow in test_workflows
        ], return_exceptions=True)
        
        execution_time = time.time() - start_execution
        total_time = time.time() - start_time
        
        # Analizar resultados
        successful_workflows = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
        failed_workflows = len(results) - successful_workflows
        
        success_rate = successful_workflows / max(len(results), 1)
        avg_workflow_time = execution_time / len(test_workflows)
        
        stress_test_results = {
            "test_id": stress_test_id,
            "configuration": {
                "concurrent_workflows": concurrent_workflows,
                "tasks_per_workflow": tasks_per_workflow,
                "total_tasks": concurrent_workflows * tasks_per_workflow
            },
            "results": {
                "successful_workflows": successful_workflows,
                "failed_workflows": failed_workflows,
                "success_rate": success_rate,
                "total_execution_time": total_time,
                "workflow_execution_time": execution_time,
                "average_workflow_time": avg_workflow_time,
                "throughput": successful_workflows / max(execution_time, 0.1)
            },
            "performance_metrics": {
                "workflows_per_second": successful_workflows / max(execution_time, 0.1),
                "tasks_per_second": (successful_workflows * tasks_per_workflow) / max(execution_time, 0.1),
                "system_utilization": min(1.0, len(test_workflows) / 50)  # Max 50 workflows
            }
        }
        
        self.logger.info(f"Stress test completado: {success_rate:.1%} success rate")
        return stress_test_results
    
    async def shutdown(self) -> None:
        """Shutdown del orquestador"""
        
        self.logger.info("Iniciando shutdown del orquestador optimizado")
        
        # Cancelar optimization task
        if self.optimization_task:
            self.optimization_task.cancel()
            try:
                await self.optimization_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown componentes
        if self.load_balancer:
            await self.load_balancer.shutdown()
        
        self.is_initialized = False
        self.logger.info("Orquestador optimizado shutdown completado")


# Configuración optimizada para el sistema
def create_optimized_orchestrator_config() -> Dict[str, Any]:
    """Crear configuración optimizada del orquestador"""
    
    return {
        "orchestrator": {
            "enable_adaptive_routing": True,
            "enable_predictive_scaling": True,
            "max_concurrent_workflows": 50,
            "auto_optimization_interval": 300,
            "optimization_levels": {
                "fast": {"routing_strategy": "least_connections", "lb_strategy": "least_connections"},
                "balanced": {"routing_strategy": "adaptive", "lb_strategy": "adaptive"},
                "quality": {"routing_strategy": "quality_based", "lb_strategy": "weighted"}
            }
        },
        "routing": {
            "default_strategy": "learning_based",
            "fallback_strategies": ["capacity_based", "response_time"],
            "adaptation_cache_size": 1000
        },
        "load_balancing": {
            "default_strategy": "adaptive",
            "circuit_breaker": {
                "failure_threshold": 5,
                "recovery_timeout": 60.0,
                "success_threshold": 3
            },
            "fault_tolerance": {
                "max_retries": 3,
                "retry_delay": 1.0,
                "exponential_backoff": True
            }
        }
    }


if __name__ == "__main__":
    # Demo del orquestador optimizado
    import asyncio
    from .specialized_agents import get_specialized_agents_config, SpecializedAgentFactory
    
    async def demo_optimized_orchestrator():
        """Demostración del orquestador optimizado"""
        
        # Crear configuración de agentes
        agent_configs = get_specialized_agents_config()
        
        # Crear orquestador
        orchestrator = OptimizedMultiAgentOrchestrator()
        
        # Inicializar
        await orchestrator.initialize(agent_configs)
        
        # Crear workflow de ejemplo
        complex_workflow = {
            "tasks": [
                {
                    "id": "data_analysis",
                    "type": "data_processing",
                    "required_skills": ["data_analysis", "statistics"],
                    "priority": 10,
                    "max_duration": 30.0
                },
                {
                    "id": "model_training",
                    "type": "ml_training", 
                    "required_skills": ["machine_learning", "model_training"],
                    "priority": 9,
                    "max_duration": 300.0,
                    "dependencies": ["data_analysis"]
                },
                {
                    "id": "report_generation",
                    "type": "reporting",
                    "required_skills": ["report_generation", "visualization"],
                    "priority": 8,
                    "max_duration": 60.0,
                    "dependencies": ["model_training"]
                }
            ]
        }
        
        # Ejecutar workflow
        result = await orchestrator.orchestrate_complex_workflow(
            complex_workflow, 
            OrchestrationMode.ADAPTIVE, 
            "balanced"
        )
        
        print(f"Workflow resultado: {result['success']}")
        print(f"Success rate: {result['success_rate']:.2%}")
        
        # Ejecutar stress test
        stress_result = await orchestrator.execute_stress_test(5, 3)
        print(f"Stress test: {stress_result['results']['success_rate']:.2%}")
        
        # Shutdown
        await orchestrator.shutdown()
    
    asyncio.run(demo_optimized_orchestrator())