"""Supervisor ejecutivo multi-equipo.

La versión anterior devolvía puntuaciones fijas (0.98 / 0.96 / 0.97) y
`deadlock_detected: False` constante: no observaba nada, así que no podía
detectar nada.

Este supervisor mantiene un registro real de equipos y agentes, y calcula sus
métricas a partir de observaciones registradas por el orquestador:

- `record_task_start` / `record_task_end` alimentan la telemetría.
- Las puntuaciones salen de tasas de éxito y latencias medidas, no de constantes.
- El estancamiento se detecta comparando el tiempo en vuelo de cada tarea contra
  un umbral, con lo que un agente bloqueado sí aparece.

Cuando un equipo no tiene observaciones, su puntuación es `None` — "sin datos"
es una respuesta legítima; inventar 0.98 no lo era.
"""
from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("ExecutiveSupervisor")

# Una tarea que supere este tiempo en vuelo se considera estancada.
DEFAULT_STALL_THRESHOLD_S = 300.0
# Ventana de observaciones por agente para las métricas móviles.
OBSERVATION_WINDOW = 200


class TeamStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    STALLED = "stalled"
    IDLE = "idle"


@dataclass
class Observation:
    """Resultado de una tarea concreta."""

    agent: str
    success: bool
    duration_s: float
    timestamp: float = field(default_factory=time.time)
    error: str | None = None


@dataclass
class InFlightTask:
    task_id: str
    agent: str
    team: str
    started_at: float = field(default_factory=time.time)

    @property
    def elapsed_s(self) -> float:
        return time.time() - self.started_at


@dataclass
class AgentRecord:
    name: str
    team: str
    observations: deque[Observation] = field(
        default_factory=lambda: deque(maxlen=OBSERVATION_WINDOW)
    )

    @property
    def total(self) -> int:
        return len(self.observations)

    @property
    def successes(self) -> int:
        return sum(1 for o in self.observations if o.success)

    @property
    def success_rate(self) -> float | None:
        return self.successes / self.total if self.total else None

    @property
    def error_rate(self) -> float | None:
        rate = self.success_rate
        return None if rate is None else 1.0 - rate

    @property
    def avg_duration_s(self) -> float | None:
        if not self.observations:
            return None
        return sum(o.duration_s for o in self.observations) / len(self.observations)

    def recent_errors(self, limit: int = 3) -> list[str]:
        errors = [o.error for o in reversed(self.observations) if not o.success and o.error]
        return errors[:limit]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "team": self.team,
            "tasks_observed": self.total,
            "success_rate": round(self.success_rate, 4) if self.success_rate is not None else None,
            "error_rate": round(self.error_rate, 4) if self.error_rate is not None else None,
            "avg_duration_s": (
                round(self.avg_duration_s, 3) if self.avg_duration_s is not None else None
            ),
            "recent_errors": self.recent_errors(),
        }


@dataclass
class Team:
    team_id: str
    name: str
    agents: list[str] = field(default_factory=list)


# Composición por defecto de la jerarquía. Los agentes se registran solos al
# reportar su primera observación, así que esto es sólo el punto de partida.
DEFAULT_TEAMS: dict[str, Team] = {
    "research": Team("research", "Investigación y RAG", ["reasoner", "memory_manager"]),
    "engineering": Team("engineering", "Ingeniería y verificación", ["planner", "executor_code", "verifier"]),
    "design": Team("design", "Diseño e interfaz", ["executor_web", "executor_docs"]),
}


class ExecutiveSupervisor:
    """Observa la jerarquía de equipos y reporta su estado real."""

    def __init__(
        self,
        teams: dict[str, Team] | None = None,
        *,
        stall_threshold_s: float = DEFAULT_STALL_THRESHOLD_S,
    ) -> None:
        self.teams: dict[str, Team] = dict(teams or DEFAULT_TEAMS)
        self.stall_threshold_s = stall_threshold_s
        self._agents: dict[str, AgentRecord] = {}
        self._in_flight: dict[str, InFlightTask] = {}
        self._recalibrations: dict[str, int] = {}

        for team in self.teams.values():
            for agent in team.agents:
                self._agents[agent] = AgentRecord(name=agent, team=team.team_id)

        logger.info("ExecutiveSupervisor inicializado con %d equipos", len(self.teams))

    # -- telemetría --------------------------------------------------------
    def team_of(self, agent: str) -> str:
        record = self._agents.get(agent)
        if record:
            return record.team
        for team in self.teams.values():
            if agent in team.agents:
                return team.team_id
        return "unassigned"

    def _ensure_agent(self, agent: str) -> AgentRecord:
        if agent not in self._agents:
            team = self.team_of(agent)
            self._agents[agent] = AgentRecord(name=agent, team=team)
            if team == "unassigned":
                self.teams.setdefault("unassigned", Team("unassigned", "Sin asignar"))
                self.teams["unassigned"].agents.append(agent)
        return self._agents[agent]

    def record_task_start(self, task_id: str, agent: str) -> None:
        record = self._ensure_agent(agent)
        self._in_flight[task_id] = InFlightTask(task_id=task_id, agent=agent, team=record.team)

    def record_task_end(
        self,
        task_id: str,
        *,
        success: bool,
        error: str | None = None,
        agent: str | None = None,
        duration_s: float | None = None,
    ) -> None:
        task = self._in_flight.pop(task_id, None)
        agent_name = agent or (task.agent if task else None)
        if agent_name is None:
            logger.debug("record_task_end sin agente identificable para %s", task_id)
            return

        elapsed = duration_s if duration_s is not None else (task.elapsed_s if task else 0.0)
        self._ensure_agent(agent_name).observations.append(
            Observation(agent=agent_name, success=success, duration_s=elapsed, error=error)
        )

    # -- supervisión -------------------------------------------------------
    def stalled_tasks(self) -> list[dict[str, Any]]:
        """Tareas cuyo tiempo en vuelo supera el umbral."""
        return [
            {
                "task_id": t.task_id,
                "agent": t.agent,
                "team": t.team,
                "elapsed_s": round(t.elapsed_s, 1),
            }
            for t in self._in_flight.values()
            if t.elapsed_s > self.stall_threshold_s
        ]

    def _team_metrics(self, team: Team) -> dict[str, Any]:
        members = [self._agents[a] for a in self._agents if self._agents[a].team == team.team_id]
        observed = [m for m in members if m.total > 0]
        stalled = [s for s in self.stalled_tasks() if s["team"] == team.team_id]

        if not observed:
            status = TeamStatus.STALLED if stalled else TeamStatus.IDLE
            score = None
        else:
            total_tasks = sum(m.total for m in observed)
            total_ok = sum(m.successes for m in observed)
            score = total_ok / total_tasks
            if stalled:
                status = TeamStatus.STALLED
            elif score < 0.85:
                status = TeamStatus.DEGRADED
            else:
                status = TeamStatus.HEALTHY

        return {
            "team_id": team.team_id,
            "name": team.name,
            "status": status.value,
            "performance_score": round(score, 4) if score is not None else None,
            "tasks_observed": sum(m.total for m in members),
            "agents": [m.to_dict() for m in members],
            "stalled_tasks": stalled,
            "recalibrations": self._recalibrations.get(team.team_id, 0),
        }

    async def audit_team_performance(self) -> dict[str, Any]:
        """Estado real de la jerarquía, calculado desde las observaciones."""
        teams = {tid: self._team_metrics(team) for tid, team in self.teams.items()}
        stalled = self.stalled_tasks()
        scored = [t["performance_score"] for t in teams.values() if t["performance_score"] is not None]

        return {
            "supervisor_status": "degraded" if stalled else "healthy",
            "active_teams": len(self.teams),
            "deadlock_detected": bool(stalled),
            "stalled_tasks": stalled,
            "tasks_in_flight": len(self._in_flight),
            "total_tasks_observed": sum(a.total for a in self._agents.values()),
            "system_performance": round(sum(scored) / len(scored), 4) if scored else None,
            "teams": teams,
        }

    async def resolve_team_deadlock(self, team_id: str) -> dict[str, Any]:
        """Cancela el seguimiento de las tareas estancadas de un equipo.

        Devuelve qué tareas se liberaron. Si no había ninguna estancada, lo dice
        en lugar de reportar una recalibración que no ocurrió.
        """
        if team_id not in self.teams:
            return {"success": False, "reason": f"El equipo '{team_id}' no existe."}

        stalled = [s for s in self.stalled_tasks() if s["team"] == team_id]
        if not stalled:
            return {
                "success": True,
                "team_id": team_id,
                "released_tasks": [],
                "message": "El equipo no tiene tareas estancadas; no se hizo nada.",
            }

        for task in stalled:
            self._in_flight.pop(task["task_id"], None)
            self._ensure_agent(task["agent"]).observations.append(
                Observation(
                    agent=task["agent"],
                    success=False,
                    duration_s=task["elapsed_s"],
                    error="liberada por el supervisor tras superar el umbral de estancamiento",
                )
            )

        self._recalibrations[team_id] = self._recalibrations.get(team_id, 0) + 1
        logger.info("[Supervisor] Equipo %s: %d tareas liberadas", team_id, len(stalled))
        return {
            "success": True,
            "team_id": team_id,
            "released_tasks": [t["task_id"] for t in stalled],
            "message": f"{len(stalled)} tarea(s) estancada(s) liberada(s).",
        }

    def agent_metrics(self, agent: str) -> dict[str, Any] | None:
        record = self._agents.get(agent)
        return record.to_dict() if record else None

    def all_agent_metrics(self) -> dict[str, dict[str, Any]]:
        return {name: rec.to_dict() for name, rec in self._agents.items()}


# Instancia compartida: el orquestador reporta aquí y la API la consulta.
supervisor = ExecutiveSupervisor()
