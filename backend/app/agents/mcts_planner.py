import hashlib
import logging
import math
from typing import Any, Optional

logger = logging.getLogger("MCTSCodePlanner")

class MCTSNode:
    """
    Nodo de decisión en el Árbol de Búsqueda Monte Carlo (MCTS).
    """
    def __init__(self, state: dict[str, Any], parent: Optional['MCTSNode'] = None, action: str | None = None):
        self.state = state
        self.parent = parent
        self.action = action
        self.children: list[MCTSNode] = []
        self.visits = 0
        self.total_reward = 0.0
        self.untried_actions = self._generate_possible_actions(state)

    def _generate_possible_actions(self, state: dict[str, Any]) -> list[str]:
        """Genera estrategias/pasos de descomposición de código basados en la meta actual."""
        prompt = state.get("prompt", "").lower()
        actions = []
        if "api" in prompt or "endpoint" in prompt:
            actions.extend(["design_fastapi_route", "add_pydantic_validation", "implement_auth_middleware"])
        if "database" in prompt or "sql" in prompt:
            actions.extend(["create_sqlalchemy_model", "add_async_db_session", "write_migration_script"])
        if "agent" in prompt or "mcp" in prompt:
            actions.extend(["instantiate_subagent", "register_mcp_tool", "setup_redis_pubsub"])

        # Acciones universales de desarrollo seguro
        actions.extend(["write_unit_tests", "add_error_handling", "refactor_clean_code", "ast_security_scan"])
        return list(set(actions))

    def uct_value(self, c_param: float = 1.414) -> float:
        """Calcula el valor UCT (Upper Confidence Bound applied to Trees)."""
        if self.visits == 0:
            return float('inf')
        return (self.total_reward / self.visits) + c_param * math.sqrt(math.log(self.parent.visits) / self.visits)

    def is_fully_expanded(self) -> bool:
        return len(self.untried_actions) == 0

    def best_child(self, c_param: float = 1.414) -> 'MCTSNode':
        return max(self.children, key=lambda child: child.uct_value(c_param))


class MCTSCodePlanner:
    """
    Planificador de Código basado en Búsqueda de Árbol Monte Carlo (MCTS) Real.
    Simula ramas de arquitectura, evalúa el Reward Score mediante evaluación heurística
    y selecciona el plan óptimo minimizando riesgos.
    """

    def __init__(self, iterations: int = 15, exploration_constant: float = 1.414):
        self.iterations = iterations
        self.c_param = exploration_constant

    async def search_best_plan(self, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        logger.info(f"[MCTS Planner Real] Iniciando búsqueda MCTS con {self.iterations} iteraciones...")

        root_state = {"prompt": prompt, "context": context, "depth": 0}
        root_node = MCTSNode(state=root_state)

        for i in range(self.iterations):
            node = root_node

            # 1. SELECCIÓN
            while not node.is_fully_expanded() and len(node.children) > 0:
                node = node.best_child(self.c_param)

            # 2. EXPANSIÓN
            if node.untried_actions:
                action = node.untried_actions.pop()
                new_state = {
                    "prompt": prompt,
                    "last_action": action,
                    "depth": node.state["depth"] + 1,
                    "history": node.state.get("history", []) + [action]
                }
                child_node = MCTSNode(state=new_state, parent=node, action=action)
                node.children.append(child_node)
                node = child_node

            # 3. EVALUACIÓN del nodo alcanzado (determinista)
            reward = self._evaluate_state(node.state)

            # 4. RETROPROPAGACIÓN (BACKPROPAGATION)
            while node is not None:
                node.visits += 1
                node.total_reward += reward
                node = node.parent

        # Seleccionar la mejor trayectoria
        best_child = root_node.best_child(c_param=0.0) # c_param=0 para seleccionar pura explotación

        explored_branches = []
        for child in root_node.children:
            avg_reward = child.total_reward / child.visits if child.visits > 0 else 0.0
            explored_branches.append({
                "action": child.action,
                "visits": child.visits,
                "average_reward": round(avg_reward, 3),
                "risk_level": "low" if avg_reward > 0.8 else ("medium" if avg_reward > 0.6 else "high")
            })

        best_trajectory = best_child.state.get("history", [best_child.action])
        best_score = best_child.total_reward / best_child.visits if best_child.visits > 0 else 0.0

        return {
            "mcts_executed": True,
            "total_iterations": self.iterations,
            "explored_branches": len(explored_branches),
            "branches_detail": explored_branches,
            "best_plan": {
                "primary_action": best_child.action,
                "execution_trajectory": best_trajectory,
                "reward_score": round(best_score, 3)
            }
        }

    def _evaluate_state(self, state: dict[str, Any]) -> float:
        """Función de evaluación heurística de un plan candidato.

        Es una evaluación determinista, no una simulación: el mismo plan
        siempre obtiene la misma puntuación. Antes se le sumaba ruido aleatorio,
        lo que hacía que dos ejecuciones sobre la misma entrada dieran planes
        distintos y que ninguna decisión fuera reproducible ni depurable.

        El desempate entre planes de igual mérito se deriva del propio plan
        (hash estable), de modo que sigue habiendo diversidad de exploración
        sin sacrificar la reproducibilidad.
        """
        history = state.get("history", [])
        score = 0.5

        # Premiar planes que incluyen validación y manejo de errores
        if "add_error_handling" in history or "add_pydantic_validation" in history:
            score += 0.25
        if "write_unit_tests" in history or "ast_security_scan" in history:
            score += 0.20
        if len(history) > 4:
            score -= 0.15  # Penalizar sobre-ingeniería excesiva

        # Desempate determinista en ±0.05, derivado del contenido del plan.
        firma = hashlib.sha256("|".join(map(str, history)).encode("utf-8")).digest()
        desempate = (firma[0] / 255.0 - 0.5) * 0.1
        return min(max(score + desempate, 0.0), 1.0)
