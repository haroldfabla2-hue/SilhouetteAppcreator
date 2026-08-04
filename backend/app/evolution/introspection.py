"""Motor de introspección: objetivos derivados de la propia telemetría.

Portado del `IntrospectionEngine` de Silhouette Agency OS
(https://github.com/haroldfabla2-hue/Silhouette-Agency-OS-OpenSource).

Es la pieza que hace autónomo al sistema: en lugar de esperar instrucciones,
`derive_goals()` observa las métricas reales del supervisor y genera objetivos
accionables cuando detecta degradación. Esos objetivos alimentan al
`EvolutionScheduler`, que forma equipos para ejecutarlos.

Los objetivos se derivan de señales medidas, nunca inventadas: si no hay
observaciones suficientes, no se deriva ningún objetivo.
"""
from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger("IntrospectionEngine")

DEFAULT_GOALS_PATH = Path("data/goals.json")

# Umbrales que disparan la derivación de objetivos.
DEGRADED_SUCCESS_RATE = 0.85
CRITICAL_SUCCESS_RATE = 0.60
# Mínimo de observaciones para que una tasa sea señal y no ruido.
MIN_OBSERVATIONS = 5


class Priority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class GoalStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


_PRIORITY_ORDER = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}


@dataclass
class Goal:
    """Un objetivo accionable del sistema."""

    id: str
    description: str
    priority: str = Priority.MEDIUM.value
    progress: float = 0.0
    status: str = GoalStatus.PENDING.value
    source: str = "manual"
    # Señal que originó el objetivo, para poder comprobar si se resolvió.
    evidence: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    @property
    def is_actionable(self) -> bool:
        return self.status in (GoalStatus.PENDING.value, GoalStatus.IN_PROGRESS.value)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class IntrospectionEngine:
    """Mantiene los objetivos del sistema y los deriva de su propio estado."""

    def __init__(
        self,
        supervisor: Any = None,
        *,
        path: Path = DEFAULT_GOALS_PATH,
    ) -> None:
        if supervisor is None:
            from backend.app.orchestrator.executive_supervisor import (
                supervisor as default_supervisor,
            )

            supervisor = default_supervisor
        self.supervisor = supervisor
        self.path = Path(path)
        self._lock = threading.Lock()
        self._goals: dict[str, Goal] = {}
        self._load()

    # -- persistencia ------------------------------------------------------
    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("No se pudo leer %s (%s); se parte sin objetivos.", self.path, exc)
            return
        for data in raw.get("goals", []):
            goal = Goal(**data)
            self._goals[goal.id] = goal
        logger.info("IntrospectionEngine: %d objetivo(s) recuperado(s)", len(self._goals))

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"goals": [g.to_dict() for g in self._goals.values()]}
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)

    # -- gestión de objetivos ---------------------------------------------
    def add_goal(
        self,
        description: str,
        priority: str = Priority.MEDIUM.value,
        *,
        source: str = "manual",
        evidence: dict[str, Any] | None = None,
    ) -> Goal:
        """Registra un objetivo nuevo. Evita duplicar uno ya activo."""
        with self._lock:
            existing = next(
                (
                    g
                    for g in self._goals.values()
                    if g.description == description and g.is_actionable
                ),
                None,
            )
            if existing is not None:
                return existing

            goal = Goal(
                id=f"goal_{uuid.uuid4().hex[:12]}",
                description=description,
                priority=priority,
                source=source,
                evidence=evidence or {},
            )
            self._goals[goal.id] = goal
            self._save()

        logger.info("[Introspección] Objetivo nuevo (%s): %s", priority, description[:80])
        return goal

    def update_goal_progress(self, goal_id: str, progress: float) -> Goal | None:
        """Actualiza el progreso. Al llegar a 1.0 el objetivo se completa."""
        with self._lock:
            goal = self._goals.get(goal_id)
            if goal is None:
                return None
            goal.progress = max(0.0, min(1.0, progress))
            goal.updated_at = time.time()
            if goal.progress >= 1.0:
                goal.status = GoalStatus.COMPLETED.value
            elif goal.progress > 0.0:
                goal.status = GoalStatus.IN_PROGRESS.value
            self._save()
        return goal

    def fail_goal(self, goal_id: str, reason: str) -> Goal | None:
        with self._lock:
            goal = self._goals.get(goal_id)
            if goal is None:
                return None
            goal.status = GoalStatus.FAILED.value
            goal.evidence["failure_reason"] = reason
            goal.updated_at = time.time()
            self._save()
        logger.warning("[Introspección] Objetivo fallido %s: %s", goal_id, reason)
        return goal

    def active_goals(self) -> list[Goal]:
        """Objetivos accionables, ordenados por prioridad y luego por antigüedad."""
        with self._lock:
            activos = [g for g in self._goals.values() if g.is_actionable]
        return sorted(
            activos,
            key=lambda g: (_PRIORITY_ORDER.get(Priority(g.priority), 3), g.created_at),
        )

    def get_high_priority_goal(self) -> Goal | None:
        """El objetivo más urgente sin empezar. Es lo que consume el bucle."""
        return next((g for g in self.active_goals() if g.progress == 0.0), None)

    def all_goals(self) -> list[dict[str, Any]]:
        with self._lock:
            return [g.to_dict() for g in self._goals.values()]

    # -- derivación autónoma ----------------------------------------------
    async def derive_goals(self) -> list[Goal]:
        """Observa la telemetría real y genera objetivos donde haya degradación.

        Esta es la parte autónoma: nadie pide estos objetivos, el sistema los
        deduce de su propio rendimiento medido.
        """
        auditoria = await self.supervisor.audit_team_performance()
        nuevos: list[Goal] = []

        # 1. Tareas estancadas: la señal más urgente.
        for estancada in auditoria.get("stalled_tasks", []):
            nuevos.append(
                self.add_goal(
                    f"Resolver el estancamiento del agente '{estancada['agent']}' "
                    f"en el equipo '{estancada['team']}' "
                    f"(lleva {estancada['elapsed_s']:.0f} s sin terminar).",
                    Priority.HIGH.value,
                    source="introspection:stall",
                    evidence=estancada,
                )
            )

        # 2. Equipos degradados.
        for team_id, equipo in auditoria.get("teams", {}).items():
            score = equipo.get("performance_score")
            if score is None or equipo.get("tasks_observed", 0) < MIN_OBSERVATIONS:
                continue  # Sin datos suficientes no se deriva nada.
            if score < CRITICAL_SUCCESS_RATE:
                prioridad = Priority.HIGH.value
            elif score < DEGRADED_SUCCESS_RATE:
                prioridad = Priority.MEDIUM.value
            else:
                continue

            nuevos.append(
                self.add_goal(
                    f"Elevar la tasa de éxito del equipo '{equipo['name']}', "
                    f"actualmente en {score:.0%}.",
                    prioridad,
                    source="introspection:team_performance",
                    evidence={"team_id": team_id, "performance_score": score},
                )
            )

        # 3. Agentes concretos con mal rendimiento.
        for nombre, metricas in self.supervisor.all_agent_metrics().items():
            tasa_error = metricas.get("error_rate")
            if tasa_error is None or metricas.get("tasks_observed", 0) < MIN_OBSERVATIONS:
                continue
            if tasa_error <= (1 - DEGRADED_SUCCESS_RATE):
                continue

            errores = metricas.get("recent_errors") or []
            nuevos.append(
                self.add_goal(
                    f"Reducir la tasa de error del agente '{nombre}' "
                    f"(actualmente {tasa_error:.0%}).",
                    Priority.HIGH.value if tasa_error > 0.4 else Priority.MEDIUM.value,
                    source="introspection:agent_error_rate",
                    evidence={
                        "agent": nombre,
                        "error_rate": tasa_error,
                        "recent_errors": errores[:3],
                    },
                )
            )

        if nuevos:
            logger.info("[Introspección] %d objetivo(s) derivado(s) de la telemetría", len(nuevos))
        return nuevos

    def stats(self) -> dict[str, Any]:
        with self._lock:
            objetivos = list(self._goals.values())
        return {
            "total": len(objetivos),
            "active": sum(1 for g in objetivos if g.is_actionable),
            "completed": sum(1 for g in objetivos if g.status == GoalStatus.COMPLETED.value),
            "failed": sum(1 for g in objetivos if g.status == GoalStatus.FAILED.value),
            "by_priority": {
                p.value: sum(1 for g in objetivos if g.priority == p.value and g.is_actionable)
                for p in Priority
            },
        }
