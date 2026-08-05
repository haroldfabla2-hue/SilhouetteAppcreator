"""
Unit tests para VerifierAgent
Valida calidad y consistencia de resultados
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.agents.verifier_wrapper import VerifierAgentWrapper
from src.agents.base_agent_wrapper import AgentCapability
from src.core.exceptions import AgentException


class TestVerifierAgentWrapper:
    """Test suite para VerifierAgentWrapper"""
    
    @pytest.fixture
    def verifier_agent(self):
        """Fixture para crear instancia del VerifierAgent"""
        return VerifierAgentWrapper()
    
    @pytest.fixture
    def sample_execution_results(self):
        """Fixture para resultados de ejecución de ejemplo"""
        return {
            "tools_results": {
                "task1": {
                    "tool": "python_executor",
                    "success": True,
                    "result": "Código implementado correctamente",
                    "time_ms": 1500
                },
                "task2": {
                    "tool": "web_scraper",
                    "success": True,
                    "result": "Datos extraídos exitosamente",
                    "time_ms": 2300
                }
            },
            "combined_output": "Resultados consolidados del proceso",
            "success_rate": 1.0,
            "execution_summary": {
                "tools_executed": 2,
                "successful": 2,
                "failed": 0,
                "total_time_ms": 3800
            }
        }
    
    @pytest.fixture
    def sample_validation_criteria(self):
        """Fixture para criterios de validación"""
        return [
            "funcionalidad_completa",
            "calidad_codigo",
            "rendimiento_aceptable",
            "cumplimiento_requisitos"
        ]
    
    @pytest.fixture
    def sample_trajectory(self):
        """Fixture para trayectoria de ejemplo"""
        return [
            {"step": 1, "action": "initialize", "status": "success"},
            {"step": 2, "action": "analyze", "status": "success"},
            {"step": 3, "action": "plan", "status": "success"},
            {"step": 4, "action": "execute", "status": "success"},
            {"step": 5, "action": "verify", "status": "success"}
        ]
    
    @pytest.mark.asyncio
    async def test_initialization(self, verifier_agent):
        """Test inicialización del VerifierAgent"""
        assert verifier_agent.agent_name == "verifier"
        assert AgentCapability.QUALITY_VALIDATION in verifier_agent.capabilities
        assert AgentCapability.CONSISTENCY_CHECKING in verifier_agent.capabilities
        assert AgentCapability.TRAJECTORY_EVALUATION in verifier_agent.capabilities
        assert AgentCapability.GATE_QUALITY in verifier_agent.capabilities
        
        # Test que el logger está configurado
        assert verifier_agent.logger.name == "mcp.agents.verifier"
        
        # Verificar threshold de calidad
        assert hasattr(verifier_agent, 'quality_threshold')
    
    @pytest.mark.asyncio
    async def test_process_request_success(self, verifier_agent, sample_execution_results, 
                                          sample_validation_criteria, sample_trajectory):
        """Test procesamiento exitoso de request"""
        request = {
            "execution_results": sample_execution_results,
            "validation_criteria": sample_validation_criteria,
            "trajectory": sample_trajectory
        }
        
        result = await verifier_agent.process_request(request)
        
        # Verificar estructura del resultado
        assert "validation_report" in result
        assert "trajectory_score" in result
        assert "consistency_check" in result
        assert "approved" in result
        assert "verification_metadata" in result
        
        # Verificar reporte de validación
        validation_report = result["validation_report"]
        assert "eval_type" in validation_report
        assert "criterios_evaluated" in validation_report
        assert "scores" in validation_report
        assert "overall_score" in validation_report
        
        assert validation_report["eval_type"] == "llm_judge"
        assert len(validation_report["criterios_evaluated"]) == len(sample_validation_criteria)
        
        # Verificar scores de criterios
        for criterion in sample_validation_criteria:
            assert criterion in validation_report["scores"]
            score_data = validation_report["scores"][criterion]
            assert "score" in score_data
            assert "justification" in score_data
            assert "passed" in score_data
            assert "evidence" in score_data
            assert isinstance(score_data["score"], float)
            assert isinstance(score_data["passed"], bool)
        
        # Verificar score de trayectoria
        trajectory_score = result["trajectory_score"]
        assert "score" in trajectory_score
        assert "efficiency" in trajectory_score
        assert "convergence" in trajectory_score
        assert "num_steps" in trajectory_score
        assert "successful_steps" in trajectory_score
        
        assert trajectory_score["num_steps"] == len(sample_trajectory)
        assert trajectory_score["successful_steps"] == len(sample_trajectory)
        
        # Verificar verificación de consistencia
        consistency_check = result["consistency_check"]
        assert "score" in consistency_check
        assert "checks" in consistency_check
        assert "passed" in consistency_check
        
        checks = consistency_check["checks"]
        assert "structure_valid" in checks
        assert "no_contradictions" in checks
        assert "references_valid" in checks
        
        # Verificar approval
        assert isinstance(result["approved"], bool)
    
    @pytest.mark.asyncio
    async def test_process_request_minimal(self, verifier_agent):
        """Test procesamiento con request mínimo"""
        minimal_request = {
            "execution_results": {},
            "validation_criteria": [],
            "trajectory": []
        }
        
        result = await verifier_agent.process_request(minimal_request)
        
        # Debe manejar el caso mínimo
        assert "validation_report" in result
        assert "trajectory_score" in result
        assert "consistency_check" in result
        assert "approved" in result
        
        # Con criterios vacíos, los scores deberían estar vacíos
        validation_report = result["validation_report"]
        assert len(validation_report["criterios_evaluated"]) == 0
        assert len(validation_report["scores"]) == 0
    
    @pytest.mark.asyncio
    async def test_quality_threshold_approval(self, verifier_agent, sample_execution_results):
        """Test aprobación basada en threshold de calidad"""
        # Con high quality threshold (simulado)
        original_threshold = verifier_agent.quality_threshold
        verifier_agent.quality_threshold = 0.5  # Threshold bajo
        
        request = {
            "execution_results": sample_execution_results,
            "validation_criteria": ["quality"],
            "trajectory": [{"step": 1, "action": "test", "status": "success"}]
        }
        
        result = await verifier_agent.process_request(request)
        assert result["approved"] is True
        
        # Restaurar threshold original
        verifier_agent.quality_threshold = original_threshold
        
        # Con threshold muy alto
        verifier_agent.quality_threshold = 0.99  # Threshold muy alto
        
        result = await verifier_agent.process_request(request)
        # Podría no ser aprobado si el score es menor al threshold
        assert isinstance(result["approved"], bool)
        
        # Restaurar threshold original
        verifier_agent.quality_threshold = original_threshold
    
    @pytest.mark.asyncio
    async def test_validation_criteria_processing(self, verifier_agent):
        """Test procesamiento de diferentes criterios de validación"""
        criteria_sets = [
            ["funcionalidad"],
            ["calidad", "rendimiento"],
            ["seguridad", "usabilidad", "rendimiento", "funcionalidad", "mantenibilidad"]
        ]
        
        for criteria in criteria_sets:
            request = {
                "execution_results": {"result": "test"},
                "validation_criteria": criteria,
                "trajectory": []
            }
            
            result = await verifier_agent.process_request(request)
            
            validation_report = result["validation_report"]
            assert len(validation_report["criterios_evaluated"]) == len(criteria)
            assert len(validation_report["scores"]) == len(criteria)
            
            # Verificar que todos los criterios están en los scores
            for criterion in criteria:
                assert criterion in validation_report["scores"]
    
    @pytest.mark.asyncio
    async def test_trajectory_evaluation(self, verifier_agent):
        """Test evaluación de trayectoria"""
        trajectory_sets = [
            [],  # Vacía
            [{"step": 1, "action": "start", "status": "success"}],  # Una tarea
            [  # Múltiples tareas
                {"step": 1, "action": "init", "status": "success"},
                {"step": 2, "action": "process", "status": "success"},
                {"step": 3, "action": "verify", "status": "success"}
            ]
        ]
        
        for trajectory in trajectory_sets:
            request = {
                "execution_results": {"result": "test"},
                "validation_criteria": ["test"],
                "trajectory": trajectory
            }
            
            result = await verifier_agent.process_request(request)
            
            trajectory_score = result["trajectory_score"]
            assert "score" in trajectory_score
            assert "efficiency" in trajectory_score
            assert "convergence" in trajectory_score
            assert "num_steps" in trajectory_score
            assert "successful_steps" in trajectory_score
            
            assert trajectory_score["num_steps"] == len(trajectory)
            # Todas las tareas deben estar marcadas como exitosas en el simulación
            assert trajectory_score["successful_steps"] == len(trajectory)
    
    @pytest.mark.asyncio
    async def test_consistency_checks(self, verifier_agent):
        """Test verificaciones de consistencia"""
        test_cases = [
            {"result": "valid structure"},
            {"data": [1, 2, 3], "metadata": {"count": 3}},
            {"nested": {"deep": {"value": "test"}}}
        ]
        
        for execution_result in test_cases:
            request = {
                "execution_results": execution_result,
                "validation_criteria": ["consistency"],
                "trajectory": [{"step": 1, "action": "test", "status": "success"}]
            }
            
            result = await verifier_agent.process_request(request)
            
            consistency_check = result["consistency_check"]
            assert "score" in consistency_check
            assert "checks" in consistency_check
            assert "passed" in consistency_check
            
            checks = consistency_check["checks"]
            assert "structure_valid" in checks
            assert "no_contradictions" in checks
            assert "references_valid" in checks
            
            # En el escenario simulado, todas las verificaciones deberían pasar
            assert isinstance(checks["structure_valid"], bool)
            assert isinstance(checks["no_contradictions"], bool)
            assert isinstance(checks["references_valid"], bool)
    
    def test_has_required_capabilities(self, verifier_agent):
        """Test que el verifier tiene las capacidades necesarias"""
        required_capabilities = [
            AgentCapability.QUALITY_VALIDATION,
            AgentCapability.CONSISTENCY_CHECKING,
            AgentCapability.TRAJECTORY_EVALUATION,
            AgentCapability.GATE_QUALITY
        ]
        
        for capability in required_capabilities:
            assert capability in verifier_agent.capabilities
    
    @pytest.mark.asyncio
    async def test_validation_report_structure(self, verifier_agent):
        """Test estructura del reporte de validación"""
        request = {
            "execution_results": {"result": "test"},
            "validation_criteria": ["criterion1", "criterion2"],
            "trajectory": []
        }
        
        result = await verifier_agent.process_request(request)
        validation_report = result["validation_report"]
        
        # Verificar todos los campos requeridos
        required_fields = ["eval_type", "criterios_evaluated", "scores", "overall_score"]
        for field in required_fields:
            assert field in validation_report
        
        # Verificar tipos de datos
        assert isinstance(validation_report["eval_type"], str)
        assert isinstance(validation_report["criterios_evaluated"], list)
        assert isinstance(validation_report["scores"], dict)
        assert isinstance(validation_report["overall_score"], float)
    
    @pytest.mark.asyncio
    async def test_trajectory_score_structure(self, verifier_agent):
        """Test estructura del score de trayectoria"""
        trajectory = [
            {"step": 1, "action": "action1", "status": "success"},
            {"step": 2, "action": "action2", "status": "success"}
        ]
        
        request = {
            "execution_results": {"result": "test"},
            "validation_criteria": ["test"],
            "trajectory": trajectory
        }
        
        result = await verifier_agent.process_request(request)
        trajectory_score = result["trajectory_score"]
        
        # Verificar todos los campos requeridos
        required_fields = ["score", "efficiency", "convergence", "num_steps", "successful_steps"]
        for field in required_fields:
            assert field in trajectory_score
        
        # Verificar tipos y rangos
        assert 0.0 <= trajectory_score["score"] <= 1.0
        assert 0.0 <= trajectory_score["efficiency"] <= 1.0
        assert 0.0 <= trajectory_score["convergence"] <= 1.0
        assert isinstance(trajectory_score["num_steps"], int)
        assert isinstance(trajectory_score["successful_steps"], int)
    
    @pytest.mark.asyncio
    async def test_consistency_check_structure(self, verifier_agent):
        """Test estructura de verificación de consistencia"""
        request = {
            "execution_results": {"result": "test"},
            "validation_criteria": ["test"],
            "trajectory": []
        }
        
        result = await verifier_agent.process_request(request)
        consistency_check = result["consistency_check"]
        
        # Verificar todos los campos requeridos
        required_fields = ["score", "checks", "passed"]
        for field in required_fields:
            assert field in consistency_check
        
        # Verificar estructura de checks
        required_checks = ["structure_valid", "no_contradictions", "references_valid"]
        for check in required_checks:
            assert check in consistency_check["checks"]
            assert isinstance(consistency_check["checks"][check], bool)
        
        assert isinstance(consistency_check["score"], float)
        assert isinstance(consistency_check["passed"], bool)
    
    @pytest.mark.asyncio
    async def test_verification_metadata(self, verifier_agent):
        """Test metadata de verificación"""
        request = {
            "execution_results": {"result": "test"},
            "validation_criteria": ["test"],
            "trajectory": []
        }
        
        result = await verifier_agent.process_request(request)
        
        assert "verification_metadata" in result
        metadata = result["verification_metadata"]
        
        # Verificar campos típicos de metadata
        assert "verifier_version" in metadata
        assert "timestamp" in metadata
        assert "validation_id" in metadata
        
        assert isinstance(metadata["timestamp"], str)
        assert isinstance(metadata["verifier_version"], str)
        assert isinstance(metadata["validation_id"], str)
    
    @pytest.mark.asyncio
    async def test_different_score_ranges(self, verifier_agent):
        """Test diferentes rangos de scores"""
        request = {
            "execution_results": {"result": "test"},
            "validation_criteria": ["quality", "performance"],
            "trajectory": []
        }
        
        result = await verifier_agent.process_request(request)
        
        # Verificar que los scores están en rango válido
        validation_report = result["validation_report"]
        
        for criterion_score in validation_report["scores"].values():
            assert 0.0 <= criterion_score["score"] <= 1.0
        
        assert 0.0 <= validation_report["overall_score"] <= 1.0
        assert 0.0 <= result["trajectory_score"]["score"] <= 1.0
        assert 0.0 <= result["consistency_check"]["score"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, verifier_agent):
        """Test manejo de errores"""
        # Test con request que cause excepción interna
        with patch.object(verifier_agent, '_validate_results', side_effect=Exception("Test error")):
            with pytest.raises(AgentException):
                await verifier_agent.process_request({
                    "execution_results": {},
                    "validation_criteria": [],
                    "trajectory": []
                })
