"""
Adaptador de Integración - Motor de Paralelización
Integra el motor de paralelización con el orquestador multi-agente existente
Proporciona interfaz compatible con el sistema actual
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from ..core.parallel_execution_engine import (
    ParallelExecutionEngine,
    Task,
    TaskState,
    ExecutionStrategy,
    LoadBalancingStrategy
)
from ..core.config import settings


class ParallelizedOrchestratorAdapter:
    """Adaptador que proporciona interfaz compatible con el orquestador actual"""
    
    def __init__(self):
        self.logger = logging.getLogger("mcp.orchestrator.parallel_adapter")
        self.parallel_engine: Optional[ParallelExecutionEngine] = None
        self.is_initialized = False
        
        # Mapeo de fases antiguas a tipos de agentes
        self.agent_type_mapping = {
            "reasoning": "reasoner_agent",
            "planning": "planner_agent", 
            "execution": "executor_agent",
            "verification": "verifier_agent",
            "memory": "memory_manager"
        }
    
    async def initialize(self, agent_configs: Dict[str, Any]) -> None:
        """Inicializar adaptador y motor de paralelización"""
        self.parallel_engine = ParallelExecutionEngine(
            max_workers=settings.max_parallel_workers or 8,
            load_balancing_strategy=LoadBalancingStrategy.LEARNING_ADAPTIVE,
            enable_resource_monitoring=True,
            enable_performance_optimization=True
        )
        
        # Registrar factories de agentes
        for agent_type, config in agent_configs.items():
            if "wrapper_factory" in config:
                self.parallel_engine.register_agent_factory(
                    agent_type,
                    config["wrapper_factory"]
                )
        
        await self.parallel_engine.initialize(agent_configs)
        self.is_initialized = True
        self.logger.info("Adaptador de paralelización inicializado")
    
    async def cleanup(self) -> None:
        """Limpiar recursos"""
        if self.parallel_engine:
            await self.parallel_engine.shutdown()
        self.is_initialized = False
        self.logger.info("Adaptador de paralelización limpiado")
    
    async def orchestrate_task_enhanced(
        self,
        objective: str,
        context: Dict[str, Any],
        user_id: Optional[str] = None,
        execution_mode: str = "parallel",  # parallel, sequential, adaptive
        quality_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """Ejecutar tarea con paralelización avanzada"""
        
        if not self.is_initialized:
            raise Exception("Adaptador no inicializado")
        
        workflow_id = f"workflow_{uuid.uuid4()}"
        self.logger.info(f"Iniciando workflow mejorado: {objective[:100]}")
        
        # Crear tareas paralelizadas
        tasks = await self._create_optimized_task_chain(objective, context)
        
        # Seleccionar estrategia de ejecución
        if execution_mode == "parallel":
            strategy = ExecutionStrategy.PARALLEL
        elif execution_mode == "sequential":
            strategy = ExecutionStrategy.SEQUENTIAL
        else:  # adaptive
            strategy = ExecutionStrategy.PARALLEL
        
        # Ejecutar workflow
        result = await self.parallel_engine.execute_workflow(
            tasks=tasks,
            workflow_id=workflow_id,
            strategy=strategy
        )
        
        # Formatear resultado para compatibilidad
        return self._format_workflow_result(result, objective, quality_threshold)
    
    async def _create_optimized_task_chain(
        self, 
        objective: str, 
        context: Dict[str, Any]
    ) -> List[Task]:
        """Crear cadena optimizada de tareas para paralelización"""
        
        tasks = []
        
        # Tarea 1: Análisis y Razonamiento (ReasonerAgent)
        reasoner_task = Task(
            task_id="reasoning_analysis",
            agent_type="reasoner_agent",
            operation="analyze_objective",
            parameters={
                "objective": objective,
                "context": context,
                "analysis_depth": "comprehensive"
            },
            priority=1,
            timeout=30.0,
            strategy=ExecutionStrategy.PARALLEL
        )
        tasks.append(reasoner_task)
        
        # Tarea 2: Planificación (PlannerAgent) - Depende de razonamiento
        planner_task = Task(
            task_id="execution_planning",
            agent_type="planner_agent", 
            operation="create_execution_plan",
            parameters={
                "objective": objective,
                "analysis_result": "{{reasoning_analysis.result}}",  # Referencia a resultado anterior
                "resource_constraints": context.get("resource_constraints", {})
            },
            dependencies={"reasoning_analysis"},
            priority=2,
            timeout=45.0,
            strategy=ExecutionStrategy.SEQUENTIAL  # Debe esperar resultado del razonador
        )
        tasks.append(planner_task)
        
        # Tarea 3: Ejecución Paralela de Sub-tareas (ExecutorAgent)
        # Dividir la ejecución en sub-tareas paralelas si es posible
        subtasks = context.get("subtasks", [
            {"name": "data_collection", "priority": 3},
            {"name": "processing", "priority": 3},
            {"name": "synthesis", "priority": 3}
        ])
        
        for i, subtask in enumerate(subtasks):
            execution_task = Task(
                task_id=f"execution_{subtask['name']}_{i}",
                agent_type="executor_agent",
                operation="execute_subtask", 
                parameters={
                    "subtask": subtask,
                    "plan_result": "{{execution_planning.result}}",
                    "user_context": context
                },
                dependencies={"execution_planning"},
                priority=3 + i,
                timeout=60.0,
                strategy=ExecutionStrategy.PARALLEL,
                max_retries=2
            )
            tasks.append(execution_task)
        
        # Tarea 4: Verificación y Validación (VerifierAgent)
        # Espera a que todas las tareas de ejecución terminen
        execution_task_ids = {f"execution_{st['name']}_{i}" for i, st in enumerate(subtasks)}
        verification_task = Task(
            task_id="result_verification",
            agent_type="verifier_agent",
            operation="verify_results",
            parameters={
                "objective": objective,
                "execution_results": "{{execution_*_result}}",  # Resultados de todas las ejecuciones
                "quality_threshold": 0.8
            },
            dependencies=execution_task_ids,
            priority=10,
            timeout=30.0,
            strategy=ExecutionStrategy.SEQUENTIAL
        )
        tasks.append(verification_task)
        
        # Tarea 5: Almacenamiento en Memoria (MemoryManager)
        memory_task = Task(
            task_id="knowledge_storage",
            agent_type="memory_manager",
            operation="store_knowledge",
            parameters={
                "objective": objective,
                "verified_results": "{{result_verification.result}}",
                "user_id": context.get("user_id"),
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "quality_score": "{{result_verification.quality_score}}"
                }
            },
            dependencies={"result_verification"},
            priority=15,
            timeout=20.0,
            strategy=ExecutionStrategy.SEQUENTIAL
        )
        tasks.append(memory_task)
        
        return tasks
    
    def _format_workflow_result(
        self, 
        workflow_result: Dict[str, Any], 
        objective: str,
        quality_threshold: float
    ) -> Dict[str, Any]:
        """Formatear resultado del workflow para compatibilidad"""
        
        # Extraer resultados de fases específicas
        reasoning_result = None
        planning_result = None 
        execution_result = None
        verification_result = None
        memory_result = None
        
        task_results = workflow_result.get("task_results", {})
        
        for task_id, task_data in task_results.items():
            if "reasoning" in task_id and task_data["state"] == "completed":
                reasoning_result = task_data["result"]
            elif "planning" in task_id and task_data["state"] == "completed":
                planning_result = task_data["result"]
            elif "execution" in task_id and task_data["state"] == "completed":
                if execution_result is None:
                    execution_result = {"subtasks": []}
                execution_result["subtasks"].append(task_data["result"])
            elif "verification" in task_id and task_data["state"] == "completed":
                verification_result = task_data["result"]
            elif "memory" in task_id and task_data["state"] == "completed":
                memory_result = task_data["result"]
        
        # Calcular calidad general
        overall_success = workflow_result["success_rate"] >= quality_threshold
        quality_score = workflow_result["success_rate"]
        
        # Crear resultado formateado
        formatted_result = {
            "success": overall_success,
            "task_id": workflow_result["workflow_id"],
            "objective": objective,
            "objective_analysis": reasoning_result,
            "execution_plan": planning_result,
            "execution_results": execution_result,
            "validation_report": verification_result,
            "quality_score": quality_score,
            "duration_seconds": workflow_result["total_duration"],
            "completed_at": datetime.now().isoformat(),
            "enhanced_parallelization": {
                "strategy_used": workflow_result["strategy"],
                "parallel_efficiency": workflow_result["success_rate"],
                "resource_utilization": workflow_result.get("performance_metrics", {}),
                "improvements": {
                    "parallel_execution": workflow_result["total_tasks"] > 5,
                    "load_balancing": True,
                    "resource_optimization": True,
                    "adaptive_scheduling": True
                }
            }
        }
        
        self.logger.info(
            f"Workflow completado: {overall_success} (Calidad: {quality_score:.2%})"
        )
        
        return formatted_result
    
    # Métodos de compatibilidad con interfaz original
    
    async def get_task_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtener progreso de tarea"""
        if self.parallel_engine:
            return self.parallel_engine.get_task_progress(task_id)
        return None
    
    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """Cancelar tarea"""
        if self.parallel_engine:
            success = self.parallel_engine.cancel_task(task_id)
            return {
                "success": success,
                "message": f"Tarea {task_id} {'cancelada' if success else 'no encontrada'}"
            }
        return {"success": False, "message": "Motor no inicializado"}
    
    async def get_status(self) -> Dict[str, Any]:
        """Obtener estado del adaptador"""
        if self.parallel_engine:
            status = self.parallel_engine.get_system_status()
            status["adaptation_mode"] = "enhanced_parallelization"
            return status
        return {"is_initialized": False, "status": "not_initialized"}
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check del adaptador"""
        if self.parallel_engine:
            health = await self.parallel_engine.health_check()
            health["adapter_version"] = "2.0_parallel_enhanced"
            return health
        return {
            "status": "unhealthy",
            "error": "Adaptador no inicializado"
        }
    
    # Métodos específicos de paralelización avanzada
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtener métricas detalladas de performance"""
        if self.parallel_engine and self.parallel_engine.metrics:
            metrics = self.parallel_engine.metrics
            return {
                "throughput": metrics.throughput,
                "average_task_time": metrics.average_task_time,
                "success_rate": metrics.completed_tasks / max(metrics.total_tasks, 1),
                "resource_utilization": metrics.resource_utilization,
                "agent_performance": metrics.agent_performance,
                "load_balancing_efficiency": metrics.load_balancing_efficiency,
                "optimization_recommendations": self._get_optimization_recommendations(metrics)
            }
        return {}
    
    def _get_optimization_recommendations(self, metrics: Any) -> List[str]:
        """Generar recomendaciones de optimización"""
        recommendations = []
        
        if metrics.throughput < 1.0:
            recommendations.append("Considerar aumentar el número de workers paralelos")
        
        if metrics.load_balancing_efficiency < 0.7:
            recommendations.append("Optimizar estrategia de balanceador de carga")
        
        if metrics.average_task_time > 30.0:
            recommendations.append("Optimizar tiempo promedio de tareas")
        
        if not recommendations:
            recommendations.append("Sistema operando óptimamente")
        
        return recommendations
    
    async def execute_multi_agent_parallel_demo(self) -> Dict[str, Any]:
        """Demostración de ejecución paralela multi-agente"""
        demo_workflow_id = f"demo_{uuid.uuid4()}"
        
        # Crear múltiples tareas paralelas para demostrar capacidad
        demo_tasks = []
        
        for i in range(5):  # 5 tareas paralelas
            task = Task(
                task_id=f"demo_task_{i}",
                agent_type="python_executor_agent",
                operation="execute_demo_code",
                parameters={
                    "task_number": i,
                    "complexity": "medium",
                    "expected_duration": 2.0 + i * 0.5
                },
                priority=i,
                timeout=10.0,
                strategy=ExecutionStrategy.PARALLEL
            )
            demo_tasks.append(task)
        
        # Ejecutar demostración
        result = await self.parallel_engine.execute_workflow(
            tasks=demo_tasks,
            workflow_id=demo_workflow_id,
            strategy=ExecutionStrategy.PARALLEL
        )
        
        return {
            "demo_id": demo_workflow_id,
            "success": result["success_rate"] > 0.8,
            "metrics": {
                "tasks_executed": result["total_tasks"],
                "parallel_efficiency": result["success_rate"],
                "duration": result["total_duration"],
                "average_per_task": result["total_duration"] / max(result["total_tasks"], 1)
            },
            "status": "demo_completed"
        }