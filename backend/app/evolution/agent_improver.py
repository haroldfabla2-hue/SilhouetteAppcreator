"""Auto-mejora de agentes mediante ajuste de perfiles persistidos.

La versión anterior devolvía `"prompt_enhancement": "Inyectadas restricciones…"`
sin modificar ningún prompt, temperatura ni parámetro: nada persistía y nada
cambiaba entre llamadas.

Aquí el ajuste es real y observable:

- Cada agente tiene un `AgentProfile` (temperatura, directivas de sistema,
  reintentos) guardado en disco.
- El improver lee las métricas medidas por `ExecutiveSupervisor` y ajusta el
  perfil cuando la tasa de error supera el umbral.
- Los agentes cargan su perfil al construir el prompt, de modo que el ajuste
  afecta a la siguiente ejecución.
- Cada ajuste queda en un historial con la métrica que lo motivó, de forma que
  se puede comprobar si mejoró algo o revertirlo.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("AgentImprover")

DEFAULT_PROFILE_PATH = Path("data/agent_profiles.json")

# Umbral de tasa de error a partir del cual se interviene.
ERROR_RATE_THRESHOLD = 0.15
# Mínimo de observaciones antes de ajustar: por debajo, la tasa no es señal.
MIN_OBSERVATIONS = 5
# Límites de temperatura.
MIN_TEMPERATURE = 0.05
MAX_TEMPERATURE = 1.0

# Directivas que se inyectan progresivamente según empeora la tasa de error.
REMEDIATION_DIRECTIVES = [
    "Verifica cada afirmación contra el contexto suministrado antes de responder.",
    "Si no tienes información suficiente, dilo explícitamente en lugar de suponer.",
    "Descompón el problema en pasos y valida cada uno antes de continuar.",
    "Revisa tu respuesta buscando errores antes de entregarla.",
]


@dataclass
class AgentProfile:
    """Parámetros ajustables de un agente."""

    name: str
    temperature: float = 0.7
    max_retries: int = 2
    directives: list[str] = field(default_factory=list)
    revision: int = 0
    updated_at: float = field(default_factory=time.time)
    # Observaciones acumuladas cuando se hizo el último ajuste. Sirve para no
    # recalibrar una y otra vez sobre la misma evidencia.
    observations_at_last_adjustment: int = 0

    def system_suffix(self) -> str:
        """Bloque a añadir al prompt de sistema del agente."""
        if not self.directives:
            return ""
        lines = "\n".join(f"- {d}" for d in self.directives)
        return f"\n\nDIRECTIVAS DE CALIBRACIÓN (revisión {self.revision}):\n{lines}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Adjustment:
    """Registro de un ajuste, con la métrica que lo motivó."""

    agent: str
    timestamp: float
    error_rate: float
    observations: int
    revision: int
    changes: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProfileStore:
    """Persistencia de perfiles en JSON, segura entre hilos."""

    def __init__(self, path: Path = DEFAULT_PROFILE_PATH) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()
        self._profiles: dict[str, AgentProfile] = {}
        self._history: list[Adjustment] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("No se pudo leer %s (%s); se parte de perfiles vacíos.", self.path, exc)
            return
        for name, data in raw.get("profiles", {}).items():
            data.pop("name", None)
            self._profiles[name] = AgentProfile(name=name, **data)
        self._history = [Adjustment(**a) for a in raw.get("history", [])]

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "profiles": {n: p.to_dict() for n, p in self._profiles.items()},
            "history": [a.to_dict() for a in self._history[-200:]],
        }
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)

    def get(self, agent: str) -> AgentProfile:
        with self._lock:
            if agent not in self._profiles:
                self._profiles[agent] = AgentProfile(name=agent)
            return self._profiles[agent]

    def put(self, profile: AgentProfile, adjustment: Adjustment | None = None) -> None:
        with self._lock:
            profile.updated_at = time.time()
            self._profiles[profile.name] = profile
            if adjustment:
                self._history.append(adjustment)
            self._save()

    def history(self, agent: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            items = self._history if agent is None else [a for a in self._history if a.agent == agent]
            return [a.to_dict() for a in items]

    def all_profiles(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return {n: p.to_dict() for n, p in self._profiles.items()}


class AgentImprover:
    """Ajusta perfiles de agentes a partir de métricas observadas."""

    def __init__(
        self,
        store: ProfileStore | None = None,
        supervisor: Any = None,
        *,
        threshold: float = ERROR_RATE_THRESHOLD,
    ) -> None:
        self.store = store or ProfileStore()
        self.threshold = threshold
        if supervisor is None:
            from backend.app.orchestrator.executive_supervisor import (
                supervisor as default_supervisor,
            )

            supervisor = default_supervisor
        self.supervisor = supervisor
        logger.info("AgentImprover inicializado (umbral de error=%.2f)", threshold)

    def get_profile(self, agent_name: str) -> AgentProfile:
        """Perfil vigente de un agente. Es lo que los agentes deben consultar."""
        return self.store.get(agent_name)

    async def evaluate_and_improve_agent(
        self,
        agent_name: str,
        error_rate: float | None = None,
    ) -> dict[str, Any]:
        """Evalúa un agente y ajusta su perfil si procede.

        Si no se pasa `error_rate`, se toma la medida real del supervisor. Si no
        hay observaciones suficientes, no se ajusta nada y se dice por qué.
        """
        metrics = self.supervisor.agent_metrics(agent_name) if self.supervisor else None
        observations = metrics["tasks_observed"] if metrics else 0

        if error_rate is None:
            error_rate = metrics["error_rate"] if metrics else None

        if error_rate is None:
            return {
                "improved": False,
                "agent_name": agent_name,
                "action": "sin_datos",
                "reason": "No hay observaciones registradas para este agente.",
                "observations": observations,
            }

        if observations and observations < MIN_OBSERVATIONS:
            return {
                "improved": False,
                "agent_name": agent_name,
                "action": "muestra_insuficiente",
                "reason": (
                    f"Sólo {observations} observación(es); se necesitan {MIN_OBSERVATIONS} "
                    "para que la tasa de error sea significativa."
                ),
                "error_rate": round(error_rate, 4),
                "observations": observations,
            }

        if error_rate <= self.threshold:
            return {
                "improved": False,
                "agent_name": agent_name,
                "action": "rendimiento_optimo",
                "error_rate": round(error_rate, 4),
                "observations": observations,
                "profile": self.store.get(agent_name).to_dict(),
            }

        # Un ajuste necesita evidencia nueva. Sin esta comprobación, el bucle
        # autónomo recalibraba el mismo agente en cada ciclo sobre las mismas
        # observaciones, agotando su margen antes de poder medir si el ajuste
        # anterior había servido de algo.
        perfil = self.store.get(agent_name)
        nuevas = observations - perfil.observations_at_last_adjustment
        if perfil.revision > 0 and nuevas < MIN_OBSERVATIONS:
            return {
                "improved": False,
                "agent_name": agent_name,
                "action": "esperando_evidencia",
                "reason": (
                    f"Sólo {nuevas} observación(es) desde la revisión "
                    f"{perfil.revision}; se necesitan {MIN_OBSERVATIONS} para "
                    "saber si el ajuste anterior funcionó."
                ),
                "error_rate": round(error_rate, 4),
                "observations": observations,
                "revision": perfil.revision,
            }

        return self._apply_adjustment(agent_name, error_rate, observations)

    def _apply_adjustment(
        self, agent_name: str, error_rate: float, observations: int
    ) -> dict[str, Any]:
        profile = self.store.get(agent_name)
        changes: dict[str, Any] = {}

        # 1. Bajar la temperatura proporcionalmente al exceso de error.
        severity = min(1.0, (error_rate - self.threshold) / max(self.threshold, 1e-6))
        new_temp = round(
            max(MIN_TEMPERATURE, min(MAX_TEMPERATURE, profile.temperature * (1.0 - 0.35 * severity))),
            3,
        )
        if new_temp != profile.temperature:
            changes["temperature"] = {"from": profile.temperature, "to": new_temp}
            profile.temperature = new_temp

        # 2. Añadir la siguiente directiva de remediación no aplicada aún.
        pending = [d for d in REMEDIATION_DIRECTIVES if d not in profile.directives]
        if pending:
            directive = pending[0]
            profile.directives.append(directive)
            changes["directive_added"] = directive

        # 3. Con error muy alto, dar un reintento más.
        if error_rate > 0.4 and profile.max_retries < 4:
            changes["max_retries"] = {"from": profile.max_retries, "to": profile.max_retries + 1}
            profile.max_retries += 1

        if not changes:
            return {
                "improved": False,
                "agent_name": agent_name,
                "action": "sin_margen",
                "reason": "El perfil ya está en su calibración más conservadora.",
                "error_rate": round(error_rate, 4),
                "profile": profile.to_dict(),
            }

        profile.revision += 1
        profile.observations_at_last_adjustment = observations
        adjustment = Adjustment(
            agent=agent_name,
            timestamp=time.time(),
            error_rate=round(error_rate, 4),
            observations=observations,
            revision=profile.revision,
            changes=changes,
        )
        self.store.put(profile, adjustment)

        logger.info(
            "[AgentImprover] %s ajustado a revisión %d (error=%.2f): %s",
            agent_name,
            profile.revision,
            error_rate,
            ", ".join(changes),
        )
        return {
            "improved": True,
            "agent_name": agent_name,
            "action": "perfil_ajustado",
            "error_rate": round(error_rate, 4),
            "observations": observations,
            "revision": profile.revision,
            "changes": changes,
            "profile": profile.to_dict(),
        }

    def history(self, agent_name: str | None = None) -> list[dict[str, Any]]:
        return self.store.history(agent_name)

    def revert(self, agent_name: str) -> dict[str, Any]:
        """Devuelve un agente a su perfil por defecto."""
        profile = AgentProfile(name=agent_name)
        self.store.put(profile)
        logger.info("[AgentImprover] Perfil de %s revertido a valores por defecto", agent_name)
        return {"reverted": True, "agent_name": agent_name, "profile": profile.to_dict()}
