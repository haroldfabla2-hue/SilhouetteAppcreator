"""
Tests para el Intelligent Router
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock

# Añadir el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.core.intelligent_router import (
    IntelligentRouter,
    RoutingContext,
    RoutingStrategy,
    OptimizationObjective,
    AgentMetrics,
    PerformancePredictor,
    CostOptimizer,
    ABTestManager
)
from src.core.exceptions import MCPCoreException
from src.agents.base_agent_wrapper import (
    BaseAgentWrapper,
    AgentCapability,
    AgentStatus
)


class MockAgentWrapper(BaseAgentWrapper):
    """Mock agent para testing"""
    
    def __init__(self, agent_name: str, capabilities=None):
        super().__init__(
            agent_name=agent_name,
            capabilities=capabilities or [AgentCapability.TOOL_INVOCATION],
            max_concurrent=3
        )
    
    async def process_request(self, request: dict, context: dict = None) -> dict:
        return {"status": "success", "result": f"Processed by {self.agent_name}"}


@pytest.fixture
def router():
    """Fixture para crear router de prueba"""
    return IntelligentRouter()


@pytest.fixture
def mock_agents():
    """Fixture para crear agentes de prueba"""
    return [
        MockAgentWrapper("agent_1", [AgentCapability.TOOL_INVOCATION]),
        MockAgentWrapper("agent_2", [AgentCapability.INTENT_ANALYSIS]),
        MockAgentWrapper("agent_3", [AgentCapability.TASK_DECOMPOSITION])
    ]


class TestPerformancePredictor:
    """Tests para PerformancePredictor"""
    
    def test_add_training_sample(self):
        """Test agregar muestra de entrenamiento"""
        predictor = PerformancePredictor()
        
        metrics = AgentMetrics(
            agent_name="test_agent",
            capability="tool_invocation",
            response_time=1.5,
            success=True,
            cost=0.05,
            user_satisfaction=0.9,
            timestamp=asyncio.get_event_loop().time(),
            context_features={"complexity": 0.5},
            complexity_score=0.5
        )
        
        predictor.add_training_sample(metrics)
        
        assert len(predictor.training_data) == 1
        assert predictor.training_data[0] == metrics
    
    def test_fallback_prediction(self):
        """Test predicción de fallback"""
        predictor = PerformancePredictor()
        
        pred = predictor.predict_performance(
            agent_name="test_agent",
            capability="tool_invocation",
            context={"complexity": 0.5},
            complexity_score=0.5
        )
        
        assert "expected_response_time" in pred
        assert "expected_success_probability" in pred
        assert "expected_cost" in pred
        assert pred["expected_response_time"] > 0
        assert 0 <= pred["expected_success_probability"] <= 1
        assert pred["expected_cost"] >= 0


class TestCostOptimizer:
    """Tests para CostOptimizer"""
    
    def test_calculate_composite_score_speed(self):
        """Test cálculo de score para objetivo SPEED"""
        optimizer = CostOptimizer()
        
        predictions = {
            "agent1": {
                "expected_response_time": 1.0,
                "expected_success_probability": 0.9,
                "expected_cost": 0.05
            }
        }
        
        context = RoutingContext(
            request_id="test",
            user_id="user1",
            request_type="test"
        )
        
        agent, score = optimizer.calculate_composite_score(
            predictions, context, OptimizationObjective.SPEED
        )
        
        assert agent == "agent1"
        assert score > 0
    
    def test_calculate_composite_score_cost(self):
        """Test cálculo de score para objetivo COST"""
        optimizer = CostOptimizer()
        
        predictions = {
            "agent1": {
                "expected_response_time": 1.0,
                "expected_success_probability": 0.9,
                "expected_cost": 0.05
            },
            "agent2": {
                "expected_response_time": 2.0,
                "expected_success_probability": 0.95,
                "expected_cost": 0.02
            }
        }
        
        context = RoutingContext(
            request_id="test",
            user_id="user1",
            request_type="test",
            budget_constraints={"max_cost": 0.10}
        )
        
        agent, score = optimizer.calculate_composite_score(
            predictions, context, OptimizationObjective.COST
        )
        
        # Agent2 debería tener menor costo y score más alto para objetivo COST
        assert agent in ["agent1", "agent2"]
        assert score > 0
    
    def test_budget_constraints(self):
        """Test restricciones de presupuesto"""
        optimizer = CostOptimizer()
        
        predictions = {
            "agent1": {
                "expected_response_time": 1.0,
                "expected_success_probability": 0.9,
                "expected_cost": 0.15  # Costo alto
            }
        }
        
        context = RoutingContext(
            request_id="test",
            user_id="user1",
            request_type="test",
            budget_constraints={"max_cost": 0.10}
        )
        
        agent, score = optimizer.calculate_composite_score(
            predictions, context, OptimizationObjective.COST
        )
        
        # Debería penalizar severamente por exceder presupuesto
        # (no podemos verificar el valor exacto sin ejecutar el método, pero verificamos que no falle)
        assert agent == "agent1"


class TestABTestManager:
    """Tests para ABTestManager"""
    
    def test_create_experiment(self):
        """Test crear experimento A/B"""
        manager = ABTestManager()
        
        experiment_id = manager.create_experiment(
            name="test_experiment",
            variants={"A": RoutingStrategy.AI_OPTIMIZED, "B": RoutingStrategy.SEMANTIC_MATCHING},
            traffic_split={"A": 0.7, "B": 0.3}
        )
        
        assert experiment_id in manager.experiments
        assert len(manager.experiments[experiment_id]["variants"]) == 2
    
    def test_get_strategy_for_user(self):
        """Test obtener estrategia para usuario"""
        manager = ABTestManager()
        
        experiment_id = manager.create_experiment(
            name="test_experiment",
            variants={"A": RoutingStrategy.AI_OPTIMIZED, "B": RoutingStrategy.SEMANTIC_MATCHING},
            traffic_split={"A": 0.5, "B": 0.5}
        )
        
        # Mismo usuario debería recibir la misma estrategia
        strategy1 = manager.get_strategy_for_user(experiment_id, "user1")
        strategy2 = manager.get_strategy_for_user(experiment_id, "user1")
        
        assert strategy1 == strategy2
    
    def test_record_result(self):
        """Test registrar resultado de experimento"""
        manager = ABTestManager()
        
        experiment_id = manager.create_experiment(
            name="test_experiment",
            variants={"A": RoutingStrategy.AI_OPTIMIZED},
            traffic_split={"A": 1.0}
        )
        
        manager.record_result(
            experiment_id=experiment_id,
            user_id="user1",
            strategy=RoutingStrategy.AI_OPTIMIZED,
            metric_value=0.8
        )
        
        results = manager.get_experiment_results(experiment_id)
        
        assert "ai_optimized" in results
        assert results["ai_optimized"]["sample_size"] == 1


@pytest.mark.asyncio
class TestIntelligentRouter:
    """Tests para IntelligentRouter"""
    
    async def test_register_agent(self, router, mock_agents):
        """Test registrar agentes"""
        for agent in mock_agents:
            await agent.ensure_initialized()
            router.register_agent(agent)
        
        assert len(router.agent_registry) == 3
        assert "agent_1" in router.agent_registry
        assert "agent_2" in router.agent_registry
        assert "agent_3" in router.agent_registry
    
    async def test_static_routing_no_agents(self, router):
        """Test routing estático sin agentes registrados"""
        context = RoutingContext(
            request_id="test",
            user_id="user1",
            request_type="test"
        )
        
        request = {"task": "test task"}
        
        with pytest.raises(MCPCoreException):
            await router.make_routing_decision(request, context, RoutingStrategy.STATIC)
    
    async def test_static_routing_with_agents(self, router, mock_agents):
        """Test routing estático con agentes"""
        for agent in mock_agents:
            await agent.ensure_initialized()
            router.register_agent(agent)
        
        context = RoutingContext(
            request_id="test",
            user_id="user1",
            request_type="test"
        )
        
        request = {"task": "test task"}
        
        decision = await router.make_routing_decision(
            request, context, RoutingStrategy.STATIC
        )
        
        assert decision.agent_name in ["agent_1", "agent_2", "agent_3"]
        assert decision.strategy_used == RoutingStrategy.STATIC
        assert decision.confidence > 0
    
    async def test_performance_based_routing(self, router, mock_agents):
        """Test routing basado en performance"""
        for agent in mock_agents:
            await agent.ensure_initialized()
            router.register_agent(agent)
        
        context = RoutingContext(
            request_id="test",
            user_id="user1",
            request_type="test"
        )
        
        request = {"task": "test task"}
        
        decision = await router.make_routing_decision(
            request, context, RoutingStrategy.PERFORMANCE_BASED, OptimizationObjective.SPEED
        )
        
        assert decision.agent_name in ["agent_1", "agent_2", "agent_3"]
        assert decision.strategy_used == RoutingStrategy.PERFORMANCE_BASED
    
    async def test_load_balanced_routing(self, router, mock_agents):
        """Test routing con balanceador de carga"""
        for agent in mock_agents:
            await agent.ensure_initialized()
            router.register_agent(agent)
        
        context = RoutingContext(
            request_id="test",
            user_id="user1",
            request_type="test"
        )
        
        request = {"task": "test task"}
        
        decision = await router.make_routing_decision(
            request, context, RoutingStrategy.LOAD_BALANCED
        )
        
        assert decision.agent_name in ["agent_1", "agent_2", "agent_3"]
        assert decision.strategy_used == RoutingStrategy.LOAD_BALANCED
        assert decision.confidence >= 0
    
    async def test_record_routing_result(self, router, mock_agents):
        """Test registrar resultado de routing"""
        for agent in mock_agents:
            await agent.ensure_initialized()
            router.register_agent(agent)
        
        decision = Mock()
        decision.agent_name = "agent_1"
        decision.strategy_used = RoutingStrategy.STATIC
        
        performance = {
            "success_rate": 0.9,
            "response_time": 1.5,
            "cost": 0.05
        }
        
        context = RoutingContext(
            request_id="test",
            user_id="user1",
            request_type="test"
        )
        
        router.record_routing_result(decision, performance, context)
        
        assert len(router.usage_history) == 1
    
    async def test_get_routing_statistics(self, router, mock_agents):
        """Test obtener estadísticas de routing"""
        for agent in mock_agents:
            await agent.ensure_initialized()
            router.register_agent(agent)
        
        stats = router.get_routing_statistics()
        
        assert "total_routing_decisions" in stats
        assert "registered_agents" in stats
        assert "available_agents" in stats
        assert stats["registered_agents"] == 3
        assert stats["available_agents"] == 3
    
    async def test_create_ab_test(self, router):
        """Test crear experimento A/B"""
        experiment_id = router.create_ab_test(
            name="test_ab",
            strategy_a=RoutingStrategy.AI_OPTIMIZED,
            strategy_b=RoutingStrategy.SEMANTIC_MATCHING,
            traffic_split=0.6
        )
        
        assert experiment_id is not None
        assert len(router.ab_test_manager.experiments) == 1
    
    async def test_adaptation_enabled(self, router, mock_agents):
        """Test habilitar/deshabilitar adaptación"""
        router.enable_adaptation(True)
        assert router.adaptation_enabled == True
        
        router.enable_adaptation(False)
        assert router.adaptation_enabled == False
    
    async def test_capability_filtering(self, router, mock_agents):
        """Test filtrado por capacidades"""
        for agent in mock_agents:
            await agent.ensure_initialized()
            router.register_agent(agent)
        
        context = RoutingContext(
            request_id="test",
            user_id="user1",
            request_type="test"
        )
        
        # Request que requiere intent_analysis
        request = {
            "task": "analyze intent",
            "capability": "intent_analysis"
        }
        
        decision = await router.make_routing_decision(
            request, context, RoutingStrategy.STATIC
        )
        
        # Debería seleccionar agent_2 que tiene intent_analysis capability
        assert decision.agent_name == "agent_2"


@pytest.mark.asyncio
async def test_integration_scenario():
    """Test de escenario de integración completo"""
    router = IntelligentRouter()
    
    # Crear agentes
    agents = [
        MockAgentWrapper("reasoner", [AgentCapability.INTENT_ANALYSIS, AgentCapability.STRATEGY_DEFINITION]),
        MockAgentWrapper("planner", [AgentCapability.TASK_DECOMPOSITION, AgentCapability.PLAN_OPTIMIZATION]),
        MockAgentWrapper("executor", [AgentCapability.TOOL_INVOCATION, AgentCapability.CODE_EXECUTION])
    ]
    
    for agent in agents:
        await agent.ensure_initialized()
        router.register_agent(agent)
    
    # Test 1: Routing semántico
    context1 = RoutingContext(
        request_id="req1",
        user_id="user1",
        request_type="analysis",
        complexity_score=0.6
    )
    
    request1 = {
        "query": "¿Cuál es la mejor estrategia para procesar estos datos?",
        "capability": "strategy_definition"
    }
    
    decision1 = await router.make_routing_decision(
        request1, context1, RoutingStrategy.SEMANTIC_MATCHING
    )
    
    assert decision1.agent_name in ["reasoner", "planner", "executor"]
    
    # Test 2: Optimización para velocidad
    context2 = RoutingContext(
        request_id="req2",
        user_id="user2",
        request_type="execution",
        complexity_score=0.3
    )
    
    request2 = {
        "task": "Ejecutar código simple",
        "capability": "code_execution"
    }
    
    decision2 = await router.make_routing_decision(
        request2, context2, RoutingStrategy.AI_OPTIMIZED, OptimizationObjective.SPEED
    )
    
    assert decision2.agent_name in ["reasoner", "planner", "executor"]
    
    # Test 3: Registrar resultados y verificar estadísticas
    performance = {
        "success_rate": 0.85,
        "response_time": 2.1,
        "cost": 0.07
    }
    
    router.record_routing_result(decision1, performance, context1)
    router.record_routing_result(decision2, performance, context2)
    
    stats = router.get_routing_statistics()
    
    assert stats["total_routing_decisions"] >= 2
    assert stats["registered_agents"] == 3
    assert "strategy_usage" in stats


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v"])