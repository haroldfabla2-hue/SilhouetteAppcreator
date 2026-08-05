"""
Wrapper MCP para VerifierAgent
Valida calidad y consistencia de resultados
"""
from typing import Dict, Any, List, Optional
import asyncio
import logging
from datetime import datetime

from .base_agent_wrapper import BaseAgentWrapper, AgentCapability
from ..core.exceptions import AgentException, handle_exceptions
from ..core.config import settings


class VerifierAgentWrapper(BaseAgentWrapper):
    """Wrapper para VerifierAgent"""
    
    def __init__(self):
        capabilities = [
            AgentCapability.QUALITY_VALIDATION,
            AgentCapability.CONSISTENCY_CHECKING,
            AgentCapability.TRAJECTORY_EVALUATION,
            AgentCapability.GATE_QUALITY
        ]
        
        super().__init__(
            agent_name="verifier",
            capabilities=capabilities,
            max_concurrent=settings.max_concurrent_tools,
            timeout_seconds=settings.agent_timeout_seconds,
            retry_attempts=settings.agent_retry_attempts,
            retry_delay=settings.agent_retry_delay
        )
        
        self.logger = logging.getLogger("mcp.agents.verifier")
        self.quality_threshold = settings.verification_quality_threshold
    
    async def _initialize(self) -> None:
        await asyncio.sleep(0.1)
        self.logger.info("VerifierAgent inicializado")
    
    async def process_request(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self.execute_operation(
            operation_name="validate_results",
            capability=AgentCapability.QUALITY_VALIDATION,
            operation_func=self._validate_results,
            request=request,
            context=context
        )
    
    @handle_exceptions
    async def _validate_results(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        execution_results = request.get("execution_results", {})
        validation_criteria = request.get("validation_criteria", [])
        trajectory = request.get("trajectory", [])
        
        self.logger.info(f"Validando resultados con {len(validation_criteria)} criterios")
        
        await asyncio.sleep(0.2)  # Simular validación
        
        # Simular reporte de validación
        validation_report = {
            "eval_type": "llm_judge",
            "criterios_evaluated": validation_criteria,
            "scores": {
                criterion: {
                    "score": 0.85,
                    "justification": f"Evaluación automática para {criterion}",
                    "passed": True,
                    "evidence": "Evidencia válida encontrada"
                } for criterion in validation_criteria
            },
            "overall_score": 0.87
        }
        
        trajectory_score = {
            "score": 0.9,
            "efficiency": 0.95,
            "convergence": 0.85,
            "num_steps": len(trajectory),
            "successful_steps": len(trajectory)
        }
        
        consistency_check = {
            "score": 0.88,
            "checks": {
                "structure_valid": True,
                "no_contradictions": True,
                "references_valid": True
            },
            "passed": True
        }
        
        approved = validation_report["overall_score"] >= self.quality_threshold
        
        result = {
            "validation_report": validation_report,
            "trajectory_score": trajectory_score,
            "consistency_check": consistency_check,
            "approved": approved,
            "recommendations": [
                "Resultados de buena calidad",
                "Continuar con siguientes pasos"
            ] if approved else [
                "Mejorar calidad de resultados",
                "Revisar criterios de validación"
            ],
            "quality_metrics": {
                "overall_score": (validation_report["overall_score"] + trajectory_score["score"] + consistency_check["score"]) / 3,
                "validation_score": validation_report["overall_score"],
                "trajectory_quality": trajectory_score["score"],
                "consistency_score": consistency_check["score"]
            }
        }
        
        return result
    
    async def validate_results(self, execution_results: Dict[str, Any], validation_criteria: List[str], trajectory: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        request = {
            "execution_results": execution_results,
            "validation_criteria": validation_criteria,
            "trajectory": trajectory or []
        }
        return await self.process_request(request)
    
    async def get_status(self) -> Dict[str, Any]:
        base_status = super().get_status()
        base_status.update({
            "agent_type": "verifier",
            "specialization": "Validación de calidad y consistencia",
            "quality_threshold": self.quality_threshold
        })
        return base_status
