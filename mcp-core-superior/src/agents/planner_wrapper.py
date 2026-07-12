"""
Wrapper MCP para PlannerAgent
Crea plan de ejecución con descomposición de tareas
"""
from typing import Dict, Any, List, Optional
import asyncio
import logging
from datetime import datetime

from .base_agent_wrapper import BaseAgentWrapper, AgentCapability
from ..core.exceptions import AgentException, handle_exceptions
from ..core.config import settings


class PlannerAgentWrapper(BaseAgentWrapper):
    """
    Wrapper para PlannerAgent
    
    Capacidades:
    - Descomposición de tareas
    - Selección de herramientas
    - Gestión de dependencias
    - Optimización de plan
    """
    
    def __init__(self):
        capabilities = [
            AgentCapability.TASK_DECOMPOSITION,
            AgentCapability.TOOL_SELECTION,
            AgentCapability.DEPENDENCY_MANAGEMENT,
            AgentCapability.PLAN_OPTIMIZATION
        ]
        
        super().__init__(
            agent_name="planner",
            capabilities=capabilities,
            max_concurrent=settings.max_concurrent_tools,
            timeout_seconds=settings.agent_timeout_seconds,
            retry_attempts=settings.agent_retry_attempts,
            retry_delay=settings.agent_retry_delay
        )
        
        self.logger = logging.getLogger("mcp.agents.planner")
        self.available_tools = [
            "python_executor", "web_scraper", "search_engine", 
            "file_processor", "git_ops", "api_caller"
        ]
    
    async def _initialize(self) -> None:
        """Inicialización del PlannerAgent"""
        self.logger.info("Inicializando PlannerAgent...")
        await asyncio.sleep(0.1)
        self.logger.info("PlannerAgent inicializado")
    
    async def process_request(
        self,
        request: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Procesar request de creación de plan"""
        return await self.execute_operation(
            operation_name="create_execution_plan",
            capability=AgentCapability.TASK_DECOMPOSITION,
            operation_func=self._create_execution_plan,
            request=request,
            context=context
        )
    
    @handle_exceptions
    async def _create_execution_plan(
        self,
        request: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Crear plan de ejecución detallado"""
        
        objective = request.get("objective", "")
        analysis = request.get("analysis", {})
        constraints = request.get("constraints", {})
        parallel_agents = request.get("parallel_agents", True)
        
        if not objective:
            raise AgentException(
                message="Objective es requerido para crear plan",
                agent_name=self.agent_name,
                operation="create_execution_plan",
                error_code="INVALID_REQUEST"
            )
        
        self.logger.info(f"Creando plan de ejecución para: {objective[:100]}...")
        
        # Simular procesamiento
        await asyncio.sleep(0.2)
        
        # Descomponer en tareas
        tasks = self._decompose_objective(objective, analysis)
        
        # Seleccionar herramientas
        tool_assignments = self._assign_tools(tasks, analysis)
        
        # Gestionar dependencias
        dependency_graph = self._build_dependency_graph(tasks, tool_assignments)
        
        # Optimizar plan
        optimized_plan = self._optimize_plan(
            tasks, tool_assignments, dependency_graph, parallel_agents
        )
        
        plan_result = {
            "objective": objective,
            "execution_plan": {
                "tasks": tasks,
                "tool_assignments": tool_assignments,
                "dependency_graph": dependency_graph,
                "execution_order": optimized_plan["execution_order"],
                "parallel_groups": optimized_plan["parallel_groups"],
                "estimated_duration": optimized_plan["estimated_duration"],
                "resource_requirements": optimized_plan["resource_requirements"]
            },
            "plan_metadata": {
                "total_tasks": len(tasks),
                "total_tools": len(set(tool_assignments.values())),
                "parallelizable": optimized_plan["is_parallelizable"],
                "complexity_score": self._calculate_complexity_score(tasks, dependency_graph),
                "created_at": datetime.now().isoformat(),
                "planner_version": "1.0.0"
            },
            "validation": {
                "dependencies_resolved": self._validate_dependencies(dependency_graph),
                "tool_availability": self._check_tool_availability(tool_assignments),
                "resource_feasibility": self._check_resource_feasibility(
                    optimized_plan["resource_requirements"]
                ),
                "timeline_feasibility": self._check_timeline_feasibility(
                    optimized_plan["estimated_duration"], constraints
                )
            }
        }
        
        self.logger.info(f"Plan creado: {len(tasks)} tareas, "
                        f"{len(optimized_plan['parallel_groups'])} grupos paralelos")
        
        return plan_result
    
    def _decompose_objective(self, objective: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Descomponer objetivo en tareas específicas"""
        tasks = []
        
        # Lógica básica de descomposición basada en el análisis
        complexity = analysis.get("complexity_level", "medium")
        intent_type = analysis.get("intent_type", "general")
        
        if intent_type == "analysis":
            tasks = [
                {"id": "data_collection", "name": "Recopilación de datos", "priority": 1},
                {"id": "data_processing", "name": "Procesamiento de datos", "priority": 2},
                {"id": "analysis_execution", "name": "Análisis principal", "priority": 3},
                {"id": "results_synthesis", "name": "Síntesis de resultados", "priority": 4}
            ]
        elif intent_type == "development":
            tasks = [
                {"id": "requirements_analysis", "name": "Análisis de requisitos", "priority": 1},
                {"id": "design_architecture", "name": "Diseño y arquitectura", "priority": 2},
                {"id": "implementation", "name": "Implementación", "priority": 3},
                {"id": "testing", "name": "Testing y validación", "priority": 4},
                {"id": "documentation", "name": "Documentación", "priority": 5}
            ]
        else:
            # Tareas genéricas
            tasks = [
                {"id": "preparation", "name": "Preparación", "priority": 1},
                {"id": "main_execution", "name": "Ejecución principal", "priority": 2},
                {"id": "validation", "name": "Validación", "priority": 3},
                {"id": "delivery", "name": "Entrega", "priority": 4}
            ]
        
        # Añadir metadatos
        for task in tasks:
            task.update({
                "estimated_effort": self._estimate_task_effort(task, complexity),
                "required_capabilities": self._get_task_capabilities(task, intent_type),
                "input_requirements": self._get_task_inputs(task),
                "output_specifications": self._get_task_outputs(task)
            })
        
        return tasks
    
    def _assign_tools(self, tasks: List[Dict[str, Any]], analysis: Dict[str, Any]) -> Dict[str, str]:
        """Asignar herramientas a tareas"""
        assignments = {}
        
        for task in tasks:
            task_id = task["id"]
            task_name = task["name"].lower()
            intent_type = analysis.get("intent_type", "general")
            
            # Asignación inteligente basada en la tarea
            if "datos" in task_name or "data" in task_name:
                if "web" in task_name:
                    assignments[task_id] = "web_scraper"
                else:
                    assignments[task_id] = "search_engine"
            elif "código" in task_name or "code" in task_name or "implementación" in task_name:
                assignments[task_id] = "python_executor"
            elif "documento" in task_name or "file" in task_name:
                assignments[task_id] = "file_processor"
            elif "api" in task_name:
                assignments[task_id] = "api_caller"
            elif "versión" in task_name or "git" in task_name:
                assignments[task_id] = "git_ops"
            else:
                # Default assignment
                if intent_type == "analysis":
                    assignments[task_id] = "search_engine"
                else:
                    assignments[task_id] = "python_executor"
        
        return assignments
    
    def _build_dependency_graph(self, tasks: List[Dict[str, Any]], 
                               tool_assignments: Dict[str, str]) -> Dict[str, List[str]]:
        """Construir grafo de dependencias"""
        dependencies = {task["id"]: [] for task in tasks}
        
        # Lógica básica de dependencias basada en prioridades
        task_dict = {task["id"]: task for task in tasks}
        
        for task in tasks:
            task_id = task["id"]
            priority = task["priority"]
            
            # Tareas de menor prioridad dependen de las de mayor prioridad
            for other_task in tasks:
                if (other_task["id"] != task_id and 
                    other_task["priority"] < priority):
                    dependencies[task_id].append(other_task["id"])
        
        return dependencies
    
    def _optimize_plan(self, tasks: List[Dict[str, Any]], tool_assignments: Dict[str, str],
                      dependency_graph: Dict[str, List[str]], parallel_agents: bool) -> Dict[str, Any]:
        """Optimizar plan de ejecución"""
        
        # Calcular orden topológico
        execution_order = self._topological_sort(tasks, dependency_graph)
        
        # Agrupar tareas paralelas
        parallel_groups = []
        if parallel_agents:
            parallel_groups = self._find_parallel_groups(execution_order, dependency_graph)
        
        # Estimar duración
        estimated_duration = self._estimate_duration(tasks, parallel_groups)
        
        # Requerimientos de recursos
        resource_requirements = self._calculate_resource_requirements(tasks, parallel_groups)
        
        return {
            "execution_order": execution_order,
            "parallel_groups": parallel_groups,
            "estimated_duration": estimated_duration,
            "resource_requirements": resource_requirements,
            "is_parallelizable": len(parallel_groups) > 1
        }
    
    def _topological_sort(self, tasks: List[Dict[str, Any]], 
                         dependencies: Dict[str, List[str]]) -> List[str]:
        """Orden topológico de tareas"""
        # Implementación simplificada del algoritmo de Kahn
        in_degree = {task["id"]: 0 for task in tasks}
        
        for task_id, deps in dependencies.items():
            for dep in deps:
                in_degree[task_id] += 1
        
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            # Reducir in_degree de tareas dependientes
            for task_id, deps in dependencies.items():
                if current in deps:
                    in_degree[task_id] -= 1
                    if in_degree[task_id] == 0:
                        queue.append(task_id)
        
        return result
    
    def _find_parallel_groups(self, execution_order: List[str], 
                             dependencies: Dict[str, List[str]]) -> List[List[str]]:
        """Encontrar grupos de tareas paralelas"""
        groups = []
        current_group = []
        remaining_tasks = set(execution_order)
        
        while remaining_tasks:
            # Encontrar tareas sin dependencias pendientes
            ready_tasks = [
                task_id for task_id in remaining_tasks
                if all(dep not in remaining_tasks for dep in dependencies.get(task_id, []))
            ]
            
            if ready_tasks:
                current_group = ready_tasks
                groups.append(current_group)
                remaining_tasks -= set(current_group)
            else:
                # Si no hay tareas listas, tomar la primera
                current_group = [list(remaining_tasks)[0]]
                groups.append(current_group)
                remaining_tasks -= set(current_group)
        
        return [group for group in groups if len(group) > 1]  # Solo grupos paralelos reales
    
    def _estimate_duration(self, tasks: List[Dict[str, Any]], parallel_groups: List[List[str]]) -> Dict[str, int]:
        """Estimar duración del plan"""
        base_duration = len(tasks) * 5  # 5 minutos por tarea base
        
        # Reducir por paralelización
        if parallel_groups:
            total_parallel_reduction = sum(
                (len(group) - 1) * 2 for group in parallel_groups  # 2 minutos saved per extra parallel task
            )
            base_duration = max(1, base_duration - total_parallel_reduction)
        
        return {
            "estimated_minutes": base_duration,
            "estimated_hours": round(base_duration / 60, 1),
            "confidence": 0.7
        }
    
    def _calculate_resource_requirements(self, tasks: List[Dict[str, Any]], 
                                       parallel_groups: List[List[str]]) -> Dict[str, Any]:
        """Calcular requerimientos de recursos"""
        max_parallel = len(max(parallel_groups, key=len)) if parallel_groups else 1
        
        return {
            "max_concurrent_tools": max_parallel,
            "estimated_memory_mb": 512 * max_parallel,
            "estimated_cpu_cores": max_parallel,
            "network_bandwidth": "standard",
            "storage_requirements": "minimal"
        }
    
    def _calculate_complexity_score(self, tasks: List[Dict[str, Any]], 
                                  dependency_graph: Dict[str, List[str]]) -> float:
        """Calcular score de complejidad"""
        num_tasks = len(tasks)
        num_dependencies = sum(len(deps) for deps in dependency_graph.values())
        
        # Score normalizado (0.0 - 1.0)
        complexity = (num_tasks * 0.3 + num_dependencies * 0.7) / 10
        return min(complexity, 1.0)
    
    def _validate_dependencies(self, dependency_graph: Dict[str, List[str]]) -> bool:
        """Validar que no hay ciclos en dependencias"""
        # Verificación simple de ciclos usando DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in dependency_graph.get(node, []):
                if has_cycle(neighbor):
                    return True
            
            rec_stack.remove(node)
            return False
        
        for task_id in dependency_graph:
            if task_id not in visited:
                if has_cycle(task_id):
                    return False
        
        return True
    
    def _check_tool_availability(self, tool_assignments: Dict[str, str]) -> bool:
        """Verificar disponibilidad de herramientas"""
        for tool in tool_assignments.values():
            if tool not in self.available_tools:
                return False
        return True
    
    def _check_resource_feasibility(self, requirements: Dict[str, Any]) -> bool:
        """Verificar factibilidad de recursos"""
        return (
            requirements["max_concurrent_tools"] <= settings.max_concurrent_tools and
            requirements["estimated_memory_mb"] <= settings.executor_memory_limit_mb * settings.max_concurrent_tools
        )
    
    def _check_timeline_feasibility(self, duration: Dict[str, Any], 
                                   constraints: Dict[str, Any]) -> bool:
        """Verificar factibilidad de timeline"""
        if "time_limit_hours" in constraints:
            return duration["estimated_hours"] <= constraints["time_limit_hours"]
        return True
    
    # Métodos auxiliares
    def _estimate_task_effort(self, task: Dict[str, Any], complexity: str) -> str:
        """Estimar esfuerzo de tarea individual"""
        base_effort = "medium"
        if complexity == "high":
            base_effort = "high"
        elif complexity == "low":
            base_effort = "low"
        return base_effort
    
    def _get_task_capabilities(self, task: Dict[str, Any], intent_type: str) -> List[str]:
        """Obtener capacidades requeridas para tarea"""
        capabilities = []
        
        task_name = task["name"].lower()
        
        if "datos" in task_name or "data" in task_name:
            capabilities.extend(["data_processing", "search"])
        if "análisis" in task_name or "analysis" in task_name:
            capabilities.append("analysis")
        if "código" in task_name or "code" in task_name:
            capabilities.append("programming")
        
        if not capabilities:
            capabilities.append("general")
        
        return capabilities
    
    def _get_task_inputs(self, task: Dict[str, Any]) -> List[str]:
        """Obtener inputs requeridos para tarea"""
        task_name = task["name"].lower()
        
        if "datos" in task_name or "data" in task_name:
            return ["data_sources", "query_parameters"]
        elif "análisis" in task_name:
            return ["input_data", "analysis_parameters"]
        else:
            return ["basic_parameters"]
    
    def _get_task_outputs(self, task: Dict[str, Any]) -> List[str]:
        """Obtener outputs esperados de tarea"""
        task_name = task["name"].lower()
        
        if "análisis" in task_name:
            return ["analysis_results", "insights", "recommendations"]
        elif "implementación" in task_name or "development" in task_name:
            return ["code", "documentation", "tests"]
        else:
            return ["results", "summary"]
    
    # Métodos de interfaz MCP
    async def create_execution_plan(
        self,
        objective: str,
        analysis: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None,
        parallel_agents: bool = True
    ) -> Dict[str, Any]:
        """Crear plan de ejecución"""
        request = {
            "objective": objective,
            "analysis": analysis,
            "constraints": constraints or {},
            "parallel_agents": parallel_agents
        }
        
        return await self.process_request(request)
    
    async def get_status(self) -> Dict[str, Any]:
        """Obtener estado del PlannerAgent"""
        base_status = super().get_status()
        base_status.update({
            "agent_type": "planner",
            "specialization": "Descomposición de tareas y planificación de ejecución",
            "available_tools": self.available_tools,
            "input_format": {
                "required": ["objective", "analysis"],
                "optional": ["constraints", "parallel_agents"]
            }
        })
        return base_status
