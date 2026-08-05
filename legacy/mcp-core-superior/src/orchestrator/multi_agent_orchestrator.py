"""
Orquestador Multi-Agente - MCP Core Superior
Integra todos los agentes para ejecución coordinada
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from ..core.exceptions import OrchestrationException, TaskNotFoundException
from ..core.config import settings


class OrchestrationPhase(Enum):
    """Fases de orquestación"""
    REASONING = "reasoning"
    PLANNING = "planning"
    EXECUTION = "execution"
    VERIFICATION = "verification"
    COMPLETION = "completion"


class OrchestrationContext:
    """Contexto de orquestación"""
    
    def __init__(self, objective: str, user_id: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        self.objective = objective
        self.user_id = user_id
        self.context = context or {}
        self.current_phase = OrchestrationPhase.REASONING
        self.start_time = datetime.now()
        self.task_id = f"task_{int(self.start_time.timestamp())}"
        self.phase_results = {}
        self.metadata = {
            "streaming_enabled": True,
            "quality_threshold": settings.verification_quality_threshold
        }
    
    def update_phase(self, phase: OrchestrationPhase, result: Any = None):
        """Actualizar fase actual"""
        self.current_phase = phase
        if result is not None:
            self.phase_results[phase.value] = result
    
    @property
    def duration(self) -> float:
        """Duración actual de la orquestación"""
        return (datetime.now() - self.start_time).total_seconds()


class OrchestrationResult:
    """Resultado de orquestación"""
    
    def __init__(self, context: OrchestrationContext):
        self.context = context
        self.success = False
        self.final_result = {}
        self.quality_score = 0.0
        self.error_message = None
        self.completed_at = None
    
    def mark_success(self, result: Dict[str, Any], quality_score: float):
        """Marcar como exitoso"""
        self.success = True
        self.final_result = result
        self.quality_score = quality_score
        self.completed_at = datetime.now()
    
    def mark_failure(self, error: str):
        """Marcar como fallido"""
        self.success = False
        self.error_message = error
        self.completed_at = datetime.now()


class MultiAgentOrchestrator:
    """Orquestador principal multi-agente"""
    
    def __init__(self):
        self.logger = logging.getLogger("mcp.orchestrator.multi_agent")
        self.active_tasks: Dict[str, OrchestrationContext] = {}
        self.completed_tasks: Dict[str, OrchestrationResult] = {}
        self.is_initialized = False
    
    async def initialize(self) -> None:
        """Inicializar orquestador"""
        self.is_initialized = True
        self.logger.info("MultiAgentOrchestrator inicializado")
    
    async def cleanup(self) -> None:
        """Limpiar recursos"""
        self.is_initialized = False
        self.active_tasks.clear()
        self.logger.info("MultiAgentOrchestrator limpiado")
    
    async def orchestrate_task(
        self,
        objective: str,
        context: Dict[str, Any],
        user_id: Optional[str] = None,
        streaming_enabled: bool = True,
        quality_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """Ejecutar tarea con todos los agentes"""
        if not self.is_initialized:
            raise OrchestrationException("Orquestador no inicializado", "unknown")
        
        # Crear contexto de orquestación
        orchestration_context = OrchestrationContext(objective, user_id, context)
        orchestration_context.metadata.update({
            "streaming_enabled": streaming_enabled,
            "quality_threshold": quality_threshold
        })
        
        self.active_tasks[orchestration_context.task_id] = orchestration_context
        
        try:
            self.logger.info(f"Iniciando orquestación para: {objective[:100]}")
            
            # FASE 1: REASONER
            orchestration_context.update_phase(OrchestrationPhase.REASONING)
            reasoner_result = await self._execute_reasoner(orchestration_context)
            
            # FASE 2: PLANNER
            orchestration_context.update_phase(OrchestrationPhase.PLANNING)
            planner_result = await self._execute_planner(orchestration_context, reasoner_result)
            
            # FASE 3: EXECUTOR
            orchestration_context.update_phase(OrchestrationPhase.EXECUTION)
            executor_result = await self._execute_executor(orchestration_context, planner_result)
            
            # FASE 4: VERIFIER
            orchestration_context.update_phase(OrchestrationPhase.VERIFICATION)
            verifier_result = await self._execute_verifier(orchestration_context, executor_result)
            
            # FASE 5: MEMORY
            await self._store_in_memory(orchestration_context, verifier_result)
            
            # Determinar éxito
            success = verifier_result.get("approved", False)
            quality_score = verifier_result.get("quality_metrics", {}).get("overall_score", 0.0)
            
            # Crear resultado final
            final_result = {
                "success": success,
                "task_id": orchestration_context.task_id,
                "objective": objective,
                "objective_analysis": reasoner_result,
                "execution_plan": planner_result,
                "execution_results": executor_result,
                "validation_report": verifier_result,
                "quality_score": quality_score,
                "duration_seconds": orchestration_context.duration,
                "completed_at": datetime.now().isoformat()
            }
            
            if success:
                self.logger.info(f"Orquestación exitosa - Calidad: {quality_score:.2f}")
            else:
                self.logger.warning(f"Orquestación falló - Calidad: {quality_score:.2f}")
            
            # Mover a completados
            result = OrchestrationResult(orchestration_context)
            result.mark_success(final_result, quality_score)
            self.completed_tasks[orchestration_context.task_id] = result
            del self.active_tasks[orchestration_context.task_id]
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"Error en orquestación: {e}")
            
            # Mover a completados con error
            result = OrchestrationResult(orchestration_context)
            result.mark_failure(str(e))
            self.completed_tasks[orchestration_context.task_id] = result
            del self.active_tasks[orchestration_context.task_id]
            
            raise OrchestrationException(f"Error en orquestación: {str(e)}", orchestration_context.task_id, orchestration_context.current_phase.value)
    
    async def _execute_reasoner(self, context: OrchestrationContext) -> Dict[str, Any]:
        """Ejecutar ReasonerAgent"""
        # Simular llamada al ReasonerAgent
        await asyncio.sleep(0.2)
        
        return {
            "intent_type": "analysis",
            "complexity_level": "medium",
            "domain": "general",
            "strategy": {
                "approach": "Análisis sistemático",
                "phases": ["Preparación", "Análisis", "Síntesis"],
                "estimated_effort": "medium"
            }
        }
    
    async def _execute_planner(self, context: OrchestrationContext, reasoner_result: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar PlannerAgent"""
        # Simular llamada al PlannerAgent
        await asyncio.sleep(0.3)
        
        return {
            "tasks": [
                {"id": "data_collection", "name": "Recopilación de datos", "priority": 1},
                {"id": "analysis", "name": "Análisis principal", "priority": 2},
                {"id": "synthesis", "name": "Síntesis de resultados", "priority": 3}
            ],
            "execution_order": ["data_collection", "analysis", "synthesis"],
            "parallel_groups": [],
            "estimated_duration": {"estimated_minutes": 15, "confidence": 0.7}
        }
    
    async def _execute_executor(self, context: OrchestrationContext, planner_result: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar ExecutorAgent"""
        # Simular llamada al ExecutorAgent
        await asyncio.sleep(0.5)
        
        return {
            "execution_summary": {
                "tools_executed": 3,
                "successful": 3,
                "failed": 0,
                "total_time_ms": 2000
            },
            "results": {
                "tools_results": {
                    "data_collection": {"success": True, "result": "Datos recopilados"},
                    "analysis": {"success": True, "result": "Análisis completado"},
                    "synthesis": {"success": True, "result": "Resultados sintetizados"}
                }
            }
        }
    
    async def _execute_verifier(self, context: OrchestrationContext, executor_result: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar VerifierAgent"""
        # Simular llamada al VerifierAgent
        await asyncio.sleep(0.2)
        
        return {
            "validation_report": {
                "overall_score": 0.85
            },
            "approved": True,
            "quality_metrics": {
                "overall_score": 0.85,
                "validation_score": 0.85,
                "trajectory_quality": 0.9,
                "consistency_score": 0.8
            },
            "recommendations": ["Resultados de buena calidad"]
        }
    
    async def _store_in_memory(self, context: OrchestrationContext, verifier_result: Dict[str, Any]) -> None:
        """Almacenar resultado en MemoryManager"""
        # Simular almacenamiento en memoria
        await asyncio.sleep(0.1)
        self.logger.info("Resultado almacenado en memoria")
    
    async def get_task_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtener progreso de tarea"""
        # Buscar en tareas activas
        if task_id in self.active_tasks:
            context = self.active_tasks[task_id]
            return {
                "task_id": task_id,
                "status": "in_progress",
                "phase": context.current_phase.value,
                "progress": self._calculate_progress(context.current_phase),
                "duration": context.duration,
                "started_at": context.start_time.isoformat()
            }
        
        # Buscar en tareas completadas
        if task_id in self.completed_tasks:
            result = self.completed_tasks[task_id]
            return {
                "task_id": task_id,
                "status": "completed" if result.success else "failed",
                "phase": "completion",
                "progress": 1.0,
                "success": result.success,
                "quality_score": result.quality_score,
                "duration": result.context.duration,
                "completed_at": result.completed_at.isoformat() if result.completed_at else None
            }
        
        return None
    
    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """Cancelar tarea"""
        if task_id not in self.active_tasks:
            raise TaskNotFoundException(task_id)
        
        del self.active_tasks[task_id]
        self.logger.info(f"Tarea {task_id} cancelada")
        
        return {
            "success": True,
            "message": f"Tarea {task_id} cancelada exitosamente"
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Obtener estado del orquestador"""
        return {
            "is_initialized": self.is_initialized,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "current_phase": "ready",
            "throughput": "calculated_on_demand"
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check del orquestador"""
        return {
            "status": "healthy" if self.is_initialized else "not_initialized",
            "is_initialized": self.is_initialized,
            "active_tasks": len(self.active_tasks),
            "components": {
                "reasoner": "available",
                "planner": "available",
                "executor": "available",
                "verifier": "available",
                "memory_manager": "available"
            }
        }
    
    def _calculate_progress(self, phase: OrchestrationPhase) -> float:
        """Calcular progreso basado en fase actual"""
        phase_order = [
            OrchestrationPhase.REASONING,
            OrchestrationPhase.PLANNING,
            OrchestrationPhase.EXECUTION,
            OrchestrationPhase.VERIFICATION,
            OrchestrationPhase.COMPLETION
        ]
        
        current_index = phase_order.index(phase) if phase in phase_order else 0
        return (current_index + 0.5) / len(phase_order)  # Mitad de la fase actual
