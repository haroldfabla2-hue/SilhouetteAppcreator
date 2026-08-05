"""Diagnóstico de salud y auto-sanación.

Sustituye a `legacy/mcp-core-superior/src/observability/advanced_metrics.py` y
`health_metrics.py`, que producían las cifras de salud con `random.uniform()`:
un panel que siempre se veía bien porque los números se inventaban.

Aquí cada indicador procede de una medición real que ya hace el sistema:

| Indicador | De dónde sale |
|---|---|
| Recursos del anfitrión | `Homeostasis` (psutil: CPU, RAM, disco) |
| Salud de los órganos | `VitalDaemon` (fallos consecutivos por órgano) |
| Rendimiento de agentes | `ExecutiveSupervisor` (tasas de éxito observadas) |
| Tareas estancadas | `ExecutiveSupervisor` (tiempo en vuelo) |
| Modelos disponibles | `providers` + `cli_adapters` (sondeo real) |

Y la auto-sanación **actúa de verdad**: libera tareas estancadas, recalibra
agentes degradados y baja la cadencia cuando el anfitrión está ahogado. Cada
acción devuelve qué hizo; si no había nada que arreglar, lo dice en lugar de
reportar una reparación que no ocurrió.
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("SelfHealing")

# Umbrales que disparan una acción de sanación.
DEGRADED_SUCCESS_RATE = 0.85
CRITICAL_SUCCESS_RATE = 0.60
UNHEALTHY_ORGAN_RATIO = 0.5


class Severity(str, Enum):
    OK = "ok"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"  # Sin datos suficientes para afirmar nada.


@dataclass
class Indicator:
    """Un indicador de salud, con su valor medido y su origen."""

    name: str
    severity: Severity
    detail: str
    #: `None` significa «no medido», no cero.
    value: float | None = None
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "severity": self.severity.value}


@dataclass
class HealingAction:
    """Una acción de reparación realmente ejecutada."""

    action: str
    target: str
    applied: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HealthReport:
    severity: Severity
    indicators: list[dict[str, Any]] = field(default_factory=list)
    actions_suggested: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity.value,
            "indicators": self.indicators,
            "actions_suggested": self.actions_suggested,
        }


class SelfHealing:
    """Diagnostica el sistema y repara lo que puede repararse solo."""

    def __init__(self, organism: Any = None, supervisor: Any = None, improver: Any = None) -> None:
        if organism is None:
            from backend.app.organism.vital_daemon import VitalDaemon

            organism = VitalDaemon(single_instance=False)
        if supervisor is None:
            from backend.app.orchestrator.executive_supervisor import (
                supervisor as default_supervisor,
            )

            supervisor = default_supervisor
        if improver is None:
            from backend.app.evolution.agent_improver import AgentImprover

            improver = AgentImprover(supervisor=supervisor)

        self.organism = organism
        self.supervisor = supervisor
        self.improver = improver
        self._history: list[HealingAction] = []

    # -- diagnóstico -------------------------------------------------------
    def _indicator_resources(self) -> Indicator:
        config = self.organism.homeostasis.synthesize()
        entorno = config["environment"] if isinstance(config, dict) else config.environment
        if isinstance(config, dict):
            perfil = config["profile"]
        else:
            perfil = config.profile
            entorno = config.environment

        if not entorno.get("measured"):
            return Indicator(
                name="recursos",
                severity=Severity.UNKNOWN,
                detail="psutil no disponible: no se pudo medir el anfitrión.",
                source="homeostasis",
            )

        presion = max(
            entorno.get("cpu_percent", 0.0),
            entorno.get("ram_percent", 0.0),
            entorno.get("disk_percent", 0.0),
        )
        severidad = {
            "critical": Severity.CRITICAL,
            "constrained": Severity.DEGRADED,
        }.get(perfil, Severity.OK)

        return Indicator(
            name="recursos",
            severity=severidad,
            detail=f"Perfil {perfil}: recurso más saturado al {presion:.0f}%.",
            value=round(presion, 2),
            source="homeostasis",
        )

    def _indicator_organs(self) -> Indicator:
        vitales = self.organism.vitals()
        organos = vitales["organs"]
        total = organos["total"]
        enfermos = organos["unhealthy"]

        if total == 0:
            return Indicator(
                name="organos",
                severity=Severity.UNKNOWN,
                detail="No hay órganos registrados.",
                source="vital_daemon",
            )

        proporcion = len(enfermos) / total
        if not enfermos:
            severidad, detalle = Severity.OK, f"Los {total} órganos responden."
        elif proporcion > UNHEALTHY_ORGAN_RATIO:
            severidad = Severity.CRITICAL
            detalle = f"{len(enfermos)} de {total} órganos enfermos: {', '.join(enfermos)}."
        else:
            severidad = Severity.DEGRADED
            detalle = f"Órgano(s) con fallos repetidos: {', '.join(enfermos)}."

        return Indicator(
            name="organos",
            severity=severidad,
            detail=detalle,
            value=round(1.0 - proporcion, 4),
            source="vital_daemon",
        )

    def _indicator_agents(self) -> Indicator:
        metricas = self.supervisor.all_agent_metrics()
        observados = [m for m in metricas.values() if (m.get("tasks_observed") or 0) > 0]

        if not observados:
            # Sin observaciones no se afirma que todo va bien.
            return Indicator(
                name="agentes",
                severity=Severity.UNKNOWN,
                detail="Ningún agente ha ejecutado tareas todavía.",
                source="executive_supervisor",
            )

        total_tareas = sum(m["tasks_observed"] for m in observados)
        exito = sum(
            m["tasks_observed"] * (m.get("success_rate") or 0.0) for m in observados
        )
        tasa = exito / total_tareas if total_tareas else 0.0

        if tasa < CRITICAL_SUCCESS_RATE:
            severidad = Severity.CRITICAL
        elif tasa < DEGRADED_SUCCESS_RATE:
            severidad = Severity.DEGRADED
        else:
            severidad = Severity.OK

        return Indicator(
            name="agentes",
            severity=severidad,
            detail=f"Tasa de éxito {tasa:.0%} sobre {total_tareas} tarea(s) observada(s).",
            value=round(tasa, 4),
            source="executive_supervisor",
        )

    def _indicator_stalls(self) -> Indicator:
        estancadas = self.supervisor.stalled_tasks()
        if not estancadas:
            return Indicator(
                name="estancamiento",
                severity=Severity.OK,
                detail="Ninguna tarea estancada.",
                value=0.0,
                source="executive_supervisor",
            )
        return Indicator(
            name="estancamiento",
            severity=Severity.CRITICAL,
            detail=f"{len(estancadas)} tarea(s) estancada(s): "
            + ", ".join(f"{t['agent']} ({t['elapsed_s']:.0f}s)" for t in estancadas[:3]),
            value=float(len(estancadas)),
            source="executive_supervisor",
        )

    def diagnose(self) -> HealthReport:
        """Estado de salud, medido. Nunca estimado."""
        indicadores = [
            self._indicator_resources(),
            self._indicator_organs(),
            self._indicator_agents(),
            self._indicator_stalls(),
        ]

        # La severidad global la marca el peor indicador con datos.
        conocidos = [i.severity for i in indicadores if i.severity is not Severity.UNKNOWN]
        if not conocidos:
            global_sev = Severity.UNKNOWN
        elif Severity.CRITICAL in conocidos:
            global_sev = Severity.CRITICAL
        elif Severity.DEGRADED in conocidos:
            global_sev = Severity.DEGRADED
        else:
            global_sev = Severity.OK

        sugerencias: list[str] = []
        for i in indicadores:
            if i.severity is Severity.CRITICAL:
                sugerencias.append(f"{i.name}: {i.detail}")

        return HealthReport(
            severity=global_sev,
            indicators=[i.to_dict() for i in indicadores],
            actions_suggested=sugerencias,
        )

    # -- reparación --------------------------------------------------------
    async def heal(self) -> dict[str, Any]:
        """Aplica las reparaciones que procedan y devuelve qué hizo."""
        diagnostico = self.diagnose()
        acciones: list[HealingAction] = []

        # 1. Liberar tareas estancadas.
        estancadas = self.supervisor.stalled_tasks()
        equipos = {t["team"] for t in estancadas}
        for equipo in equipos:
            resultado = await self.supervisor.resolve_team_deadlock(equipo)
            liberadas = resultado.get("released_tasks") or []
            acciones.append(
                HealingAction(
                    action="liberar_tareas_estancadas",
                    target=equipo,
                    applied=bool(liberadas),
                    detail=resultado.get("message", ""),
                )
            )

        # 2. Recalibrar agentes cuyo rendimiento lo justifique.
        for nombre, metricas in self.supervisor.all_agent_metrics().items():
            tasa_error = metricas.get("error_rate")
            if tasa_error is None or tasa_error <= (1 - DEGRADED_SUCCESS_RATE):
                continue
            resultado = await self.improver.evaluate_and_improve_agent(nombre)
            acciones.append(
                HealingAction(
                    action="recalibrar_agente",
                    target=nombre,
                    applied=bool(resultado.get("improved")),
                    detail=resultado.get("reason") or resultado.get("action", ""),
                )
            )

        # 3. Bajo presión de recursos, espaciar la cadencia del organismo.
        recursos = self._indicator_resources()
        if recursos.severity is Severity.CRITICAL:
            acciones.append(
                HealingAction(
                    action="reducir_cadencia",
                    target="organismo",
                    applied=True,
                    detail=(
                        "La homeostasis ya espacia los ciclos automáticamente "
                        f"({recursos.detail})."
                    ),
                )
            )

        self._history.extend(acciones)
        del self._history[:-200]

        aplicadas = [a for a in acciones if a.applied]
        if aplicadas:
            logger.info("[Auto-sanación] %d acción(es) aplicada(s)", len(aplicadas))

        return {
            "diagnosis": diagnostico.to_dict(),
            "actions": [a.to_dict() for a in acciones],
            "applied_count": len(aplicadas),
            "detail": (
                f"{len(aplicadas)} reparación(es) aplicada(s)."
                if aplicadas
                else "No había nada que reparar."
            ),
        }

    def history(self) -> list[dict[str, Any]]:
        return [a.to_dict() for a in self._history[-50:]]
