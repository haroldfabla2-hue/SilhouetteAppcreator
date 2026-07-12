"""
Unit tests para ReasonerAgent
Analiza intención del usuario y define estrategia inicial
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.agents.reasoner_wrapper import ReasonerAgentWrapper
from src.agents.base_agent_wrapper import AgentCapability
from src.core.exceptions import AgentException


class TestReasonerAgentWrapper:
    """Test suite para ReasonerAgentWrapper"""
    
    @pytest.fixture
    def reasoner_agent(self):
        """Fixture para crear instancia del ReasonerAgent"""
        return ReasonerAgentWrapper()
    
    @pytest.fixture
    def sample_request(self):
        """Fixture para request de ejemplo"""
        return {
            "objective": "Analizar el mercado de software para pequeñas empresas",
            "context": {"user_preferences": {"domain": "business"}},
            "conversation_id": "conv_123",
            "user_id": "user_456"
        }
    
    @pytest.mark.asyncio
    async def test_initialization(self, reasoner_agent):
        """Test inicialización del ReasonerAgent"""
        assert reasoner_agent.agent_name == "reasoner"
        assert AgentCapability.INTENT_ANALYSIS in reasoner_agent.capabilities
        assert AgentCapability.STRATEGY_DEFINITION in reasoner_agent.capabilities
        assert AgentCapability.CONTEXT_ENRICHMENT in reasoner_agent.capabilities
        
        # Test que el logger está configurado
        assert reasoner_agent.logger.name == "mcp.agents.reasoner"
    
    @pytest.mark.asyncio
    async def test_process_request_success(self, reasoner_agent, sample_request):
        """Test procesamiento exitoso de request"""
        result = await reasoner_agent.process_request(sample_request)
        
        # Verificar estructura del resultado
        assert "objective" in result
        assert "analysis" in result
        assert "strategy" in result
        assert "context" in result
        
        # Verificar análisis
        analysis = result["analysis"]
        assert "intent_type" in analysis
        assert "complexity_level" in analysis
        assert "domain" in analysis
        assert "requirements" in analysis
        assert "constraints" in analysis
        assert "success_criteria" in analysis
        assert "estimated_effort" in analysis
        
        # Verificar estrategia
        strategy = result["strategy"]
        assert "approach" in strategy
        assert "phases" in strategy
        assert "dependencies" in strategy
        assert "parallelization_possible" in strategy
        assert "resource_requirements" in strategy
        assert "risk_factors" in strategy
        
        # Verificar metadata
        context = result["context"]
        assert context["conversation_id"] == "conv_123"
        assert context["user_id"] == "user_456"
        assert "timestamp" in context
        assert "analysis_metadata" in context
    
    @pytest.mark.asyncio
    async def test_process_request_invalid_objective(self, reasoner_agent):
        """Test procesamiento con objetivo inválido"""
        invalid_request = {
            "objective": "",  # Vacío
            "context": {}
        }
        
        with pytest.raises(AgentException) as exc_info:
            await reasoner_agent.process_request(invalid_request)
        
        assert exc_info.value.error_code == "INVALID_REQUEST"
        assert "Objective es requerido" in str(exc_info.value.message)
    
    @pytest.mark.asyncio
    async def test_analyze_intent_method(self, reasoner_agent):
        """Test método público analyze_intent"""
        objective = "Crear una aplicación web para gestión de tareas"
        
        result = await reasoner_agent.analyze_intent(
            objective=objective,
            context={"priority": "high"},
            conversation_id="test_conv",
            user_id="test_user"
        )
        
        assert result["objective"] == objective
        assert "analysis" in result
        assert "strategy" in result
        assert result["context"]["conversation_id"] == "test_conv"
        assert result["context"]["user_id"] == "test_user"
    
    def test_classify_intent_analysis(self, reasoner_agent):
        """Test clasificación de intención - análisis"""
        test_cases = [
            ("analizar el mercado", "analysis"),
            ("análisis de datos", "analysis"),
            ("evaluar la situación", "analysis")
        ]
        
        for text, expected in test_cases:
            result = reasoner_agent._classify_intent(text)
            assert result == expected
    
    def test_classify_intent_creation(self, reasoner_agent):
        """Test clasificación de intención - creación"""
        test_cases = [
            ("crear una aplicación", "creation"),
            ("desarrollar un sistema", "creation"),
            ("generar código", "creation")
        ]
        
        for text, expected in test_cases:
            result = reasoner_agent._classify_intent(text)
            assert result == expected
    
    def test_classify_intent_research(self, reasoner_agent):
        """Test clasificación de intención - investigación"""
        test_cases = [
            ("investigar el mercado", "research"),
            ("buscar información", "research"),
            ("explorar opciones", "research")
        ]
        
        for text, expected in test_cases:
            result = reasoner_agent._classify_intent(text)
            assert result == expected
    
    def test_assess_complexity_low(self, reasoner_agent):
        """Test evaluación de complejidad - baja"""
        simple_objectives = [
            "crear un archivo",
            "hola mundo",
            "test básico"
        ]
        
        for objective in simple_objectives:
            result = reasoner_agent._assess_complexity(objective)
            assert result == "low"
    
    def test_assess_complexity_medium(self, reasoner_agent):
        """Test evaluación de complejidad - media"""
        medium_objectives = [
            "desarrollar una aplicación web básica con base de datos y autenticación usando Python y Flask con SQLite",
            "crear un sistema de análisis de datos con múltiples fuentes y visualizaciones"
        ]
        
        for objective in medium_objectives:
            result = reasoner_agent._assess_complexity(objective)
            assert result == "medium"
    
    def test_assess_complexity_high(self, reasoner_agent):
        """Test evaluación de complejidad - alta"""
        complex_objectives = [
            "desarrollar una aplicación web compleja con múltiples módulos, integración con APIs externas, base de datos distribuida, sistema de autenticación avanzado, y múltiples interfaces de usuario",
            "crear un sistema de análisis de big data con machine learning, procesamiento en tiempo real, múltiples fuentes de datos, y dashboards interactivos"
        ]
        
        for objective in complex_objectives:
            result = reasoner_agent._assess_complexity(objective)
            assert result == "high"
    
    def test_identify_domain_technology(self, reasoner_agent):
        """Test identificación de dominio - tecnología"""
        test_cases = [
            "desarrollo de software",
            "programación web",
            "API REST",
            "tech stack"
        ]
        
        for text in test_cases:
            result = reasoner_agent._identify_domain(text)
            assert result == "technology"
    
    def test_identify_domain_business(self, reasoner_agent):
        """Test identificación de dominio - negocio"""
        test_cases = [
            "estrategia de negocio",
            "plan de ventas",
            "marketing digital"
        ]
        
        for text in test_cases:
            result = reasoner_agent._identify_domain(text)
            assert result == "business"
    
    def test_identify_domain_data(self, reasoner_agent):
        """Test identificación de dominio - datos"""
        test_cases = [
            "análisis de datos",
            "estadísticas de ventas",
            "métricas de rendimiento"
        ]
        
        for text in test_cases:
            result = reasoner_agent._identify_domain(text)
            assert result == "data"
    
    def test_extract_requirements(self, reasoner_agent):
        """Test extracción de requisitos"""
        objective = "necesito crear una aplicación que maneje usuarios y datos"
        requirements = reasoner_agent._extract_requirements(objective)
        
        assert isinstance(requirements, list)
        assert len(requirements) <= 5
        # Debe haber encontrado al menos algunos requisitos
        assert len(requirements) > 0
    
    def test_extract_constraints_default(self, reasoner_agent):
        """Test extracción de restricciones - valores por defecto"""
        objective = "crear una aplicación"
        constraints = reasoner_agent._extract_constraints(objective, {})
        
        assert "time" in constraints
        assert "budget" in constraints
        assert "technology" in constraints
        assert "quality" in constraints
        assert constraints["time"] == "No especificado"
    
    def test_extract_constraints_with_context(self, reasoner_agent):
        """Test extracción de restricciones con contexto"""
        user_context = {
            "deadline": "2025-01-01",
            "budget": 10000,
            "tech_stack": ["Python", "React"]
        }
        
        constraints = reasoner_agent._extract_constraints("crear app", user_context)
        
        assert constraints["time"] == "2025-01-01"
        assert constraints["budget"] == 10000
        assert constraints["technology"] == "['Python', 'React']"
    
    def test_define_success_criteria(self, reasoner_agent):
        """Test definición de criterios de éxito"""
        criteria = reasoner_agent._define_success_criteria("desarrollar aplicación")
        
        assert isinstance(criteria, list)
        assert len(criteria) > 0
        assert "Código funcional y bien documentado" in criteria
    
    def test_estimate_effort(self, reasoner_agent):
        """Test estimación de esfuerzo"""
        test_cases = [
            ("simple task", "low"),
            ("medium complexity task with multiple steps", "medium"),
            ("very complex task with multiple advanced features, integrations, and high-performance requirements", "high")
        ]
        
        for objective, expected in test_cases:
            result = reasoner_agent._estimate_effort(objective)
            assert result == expected
    
    def test_define_approach(self, reasoner_agent):
        """Test definición de enfoque"""
        # Test enfoque para análisis complejo
        approach = reasoner_agent._define_approach("analizar el mercado complejo")
        assert "Análisis profundo iterativo" in approach
        
        # Test enfoque para desarrollo medio
        approach = reasoner_agent._define_approach("desarrollar aplicación simple")
        assert "Desarrollo estructurado" in approach
    
    def test_plan_phases_analysis(self, reasoner_agent):
        """Test planificación de fases - análisis"""
        phases = reasoner_agent._plan_phases("investigar mercado")
        
        assert isinstance(phases, list)
        assert len(phases) > 0
        assert "Recopilación de información" in phases
        assert "Análisis y síntesis" in phases
    
    def test_plan_phases_development(self, reasoner_agent):
        """Test planificación de fases - desarrollo"""
        phases = reasoner_agent._plan_phases("desarrollar aplicación")
        
        assert isinstance(phases, list)
        assert len(phases) > 0
        assert "Diseño y arquitectura" in phases
        assert "Implementación" in phases
        assert "Testing y QA" in phases
    
    def test_identify_dependencies(self, reasoner_agent):
        """Test identificación de dependencias"""
        dependencies = reasoner_agent._identify_dependencies("crear app web con API")
        
        assert isinstance(dependencies, list)
        assert len(dependencies) > 0
        # Debe identificar dependencias de API
        assert any("API" in dep for dep in dependencies)
    
    def test_assess_parallelization_possible(self, reasoner_agent):
        """Test evaluación de paralelización - posible"""
        objectives = [
            "crear múltiples módulos independientes",
            "desarrollar componentes separados"
        ]
        
        for objective in objectives:
            result = reasoner_agent._assess_parallelization(objective)
            assert result is True
    
    def test_assess_parallelization_not_possible(self, reasoner_agent):
        """Test evaluación de paralelización - no posible"""
        objectives = [
            "procesar de forma secuencial",
            "ejecutar paso a paso"
        ]
        
        for objective in objectives:
            result = reasoner_agent._assess_parallelization(objective)
            assert result is False
    
    def test_assess_resources_standard(self, reasoner_agent):
        """Test evaluación de recursos - estándar"""
        resources = reasoner_agent._assess_resources("crear aplicación simple")
        
        assert "computational" in resources
        assert "memory" in resources
        assert "storage" in resources
        assert "network" in resources
        assert "specialized" in resources
        assert resources["computational"] == "Standard"
    
    def test_assess_resources_high_requirements(self, reasoner_agent):
        """Test evaluación de recursos - altos requerimientos"""
        resources = reasoner_agent._assess_resources("crear aplicación con machine learning")
        
        assert resources["computational"] == "High"
        assert "GPU/TPU para ML" in resources["specialized"]
    
    def test_assess_risks_high_complexity(self, reasoner_agent):
        """Test evaluación de riesgos - alta complejidad"""
        risks = reasoner_agent._assess_risks("desarrollar sistema complejo con múltiples módulos avanzados")
        
        assert isinstance(risks, list)
        assert len(risks) > 0
        # Debe tener riesgo de complejidad técnica
        risk_types = [risk["factor"] for risk in risks]
        assert any("Complejidad técnica" in risk for risk in risk_types)
    
    @pytest.mark.asyncio
    async def test_get_status(self, reasoner_agent):
        """Test obtención de estado del agente"""
        status = await reasoner_agent.get_status()
        
        assert "agent_type" in status
        assert status["agent_type"] == "reasoner"
        assert "specialization" in status
        assert "input_format" in status
        assert "output_format" in status
        assert "capabilities" in status
    
    @pytest.mark.asyncio
    async def test_error_handling(self, reasoner_agent):
        """Test manejo de errores"""
        # Test con request que cause excepción interna
        with patch.object(reasoner_agent, '_analyze_intent', side_effect=Exception("Test error")):
            with pytest.raises(AgentException):
                await reasoner_agent.process_request({"objective": "test"})
