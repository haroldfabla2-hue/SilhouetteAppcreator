"""Bucle autónomo de auto-evolución.

Portado del `EvolutionScheduler` de Silhouette Agency OS
(https://github.com/haroldfabla2-hue/Silhouette-Agency-OS-OpenSource),
conservando su principio rector: **este servicio ORQUESTA, no duplica**.

El ciclo, ejecutándose en segundo plano sin intervención:

    1. INTROSPECCIÓN  El motor observa la telemetría real del supervisor y
                      deriva objetivos donde detecta degradación.
    2. CALIBRACIÓN    El AgentImprover ajusta los perfiles de los agentes cuya
                      tasa de error medida supera el umbral.
    3. EJECUCIÓN      Se toma el objetivo más prioritario y el SquadFactory
                      forma un equipo a medida para resolverlo.
    4. VERIFICACIÓN   Al cerrar un ciclo se comprueba si la señal que originó
                      el objetivo mejoró; si mejoró, el objetivo se completa.

Todo lo que hace queda registrado en `cycles`, con la métrica que lo motivó, de
modo que se puede comprobar si el sistema realmente mejoró — o no.
"""
from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any

logger = logging.getLogger("EvolutionScheduler")

# Intervalos por defecto, en segundos.
DEFAULT_INTROSPECTION_INTERVAL = 30 * 60   # 30 min
DEFAULT_CALIBRATION_INTERVAL = 60 * 60     # 1 h
DEFAULT_GOAL_INTERVAL = 30 * 60            # 30 min

MAX_CYCLE_HISTORY = 100


@dataclass
class EvolutionConfig:
    introspection_interval_s: float = DEFAULT_INTROSPECTION_INTERVAL
    calibration_interval_s: float = DEFAULT_CALIBRATION_INTERVAL
    goal_interval_s: float = DEFAULT_GOAL_INTERVAL
    # Si es False, se derivan objetivos pero no se forman equipos solos.
    auto_execute_goals: bool = True
    max_concurrent_evolutions: int = 2
    squad_budget: str = "BALANCED"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CycleRecord:
    """Registro de un ciclo, con lo que lo motivó y lo que produjo."""

    kind: str
    timestamp: float = field(default_factory=time.time)
    goals_derived: int = 0
    agents_calibrated: list[str] = field(default_factory=list)
    squads_spawned: list[str] = field(default_factory=list)
    goals_completed: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EvolutionScheduler:
    """Ejecuta el bucle cognitivo en segundo plano."""

    def __init__(
        self,
        *,
        introspection: Any = None,
        improver: Any = None,
        squad_factory: Any = None,
        supervisor: Any = None,
        config: EvolutionConfig | None = None,
    ) -> None:
        self.config = config or EvolutionConfig()

        if supervisor is None:
            from backend.app.orchestrator.executive_supervisor import (
                supervisor as default_supervisor,
            )

            supervisor = default_supervisor
        self.supervisor = supervisor

        if introspection is None:
            from backend.app.evolution.introspection import IntrospectionEngine

            introspection = IntrospectionEngine(supervisor=supervisor)
        self.introspection = introspection

        if improver is None:
            from backend.app.evolution.agent_improver import AgentImprover

            improver = AgentImprover(supervisor=supervisor)
        self.improver = improver

        self.squad_factory = squad_factory

        self._running = False
        self._tasks: list[asyncio.Task[None]] = []
        self._active_evolutions = 0
        self._cycles: deque[CycleRecord] = deque(maxlen=MAX_CYCLE_HISTORY)

    # -- control -----------------------------------------------------------
    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Arranca los bucles. Requiere un bucle de eventos en marcha."""
        if self._running:
            logger.info("[Evolución] El planificador ya estaba en marcha")
            return

        self._running = True
        self._tasks = [
            asyncio.create_task(
                self._loop(self.config.introspection_interval_s, self.run_introspection_cycle),
                name="evolution-introspection",
            ),
            asyncio.create_task(
                self._loop(self.config.calibration_interval_s, self.run_calibration_cycle),
                name="evolution-calibration",
            ),
            asyncio.create_task(
                self._loop(self.config.goal_interval_s, self.run_goal_cycle),
                name="evolution-goals",
            ),
        ]
        logger.info(
            "[Evolución] Bucle autónomo activo "
            "(introspección %.0f min, calibración %.0f min, objetivos %.0f min)",
            self.config.introspection_interval_s / 60,
            self.config.calibration_interval_s / 60,
            self.config.goal_interval_s / 60,
        )

    async def stop(self) -> None:
        """Detiene los bucles y espera a que terminen."""
        if not self._running:
            return
        self._running = False
        for tarea in self._tasks:
            tarea.cancel()
        for tarea in self._tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await tarea
        self._tasks.clear()
        logger.info("[Evolución] Bucle autónomo detenido")

    async def _loop(self, interval_s: float, cycle: Any) -> None:
        """Ejecuta un ciclo cada `interval_s`, sobreviviendo a sus fallos."""
        while self._running:
            try:
                await asyncio.sleep(interval_s)
                if not self._running:
                    return
                await cycle()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 - el bucle no debe morir
                logger.exception("[Evolución] Ciclo fallido: %s", exc)
                self._cycles.append(CycleRecord(kind="error", error=str(exc)))

    # -- ciclos ------------------------------------------------------------
    async def run_introspection_cycle(self) -> CycleRecord:
        """Deriva objetivos de la telemetría y cierra los que ya se resolvieron."""
        registro = CycleRecord(kind="introspection")
        nuevos = await self.introspection.derive_goals()
        registro.goals_derived = len(nuevos)
        registro.goals_completed = await self._close_resolved_goals()
        self._cycles.append(registro)
        return registro

    async def run_calibration_cycle(self) -> CycleRecord:
        """Ajusta los perfiles de los agentes con tasa de error alta."""
        registro = CycleRecord(kind="calibration")
        for nombre in self.supervisor.all_agent_metrics():
            resultado = await self.improver.evaluate_and_improve_agent(nombre)
            if resultado.get("improved"):
                registro.agents_calibrated.append(nombre)
        if registro.agents_calibrated:
            logger.info(
                "[Evolución] %d agente(s) recalibrado(s): %s",
                len(registro.agents_calibrated),
                ", ".join(registro.agents_calibrated),
            )
        self._cycles.append(registro)
        return registro

    async def run_goal_cycle(self) -> CycleRecord:
        """Toma el objetivo más urgente y forma un equipo para resolverlo."""
        registro = CycleRecord(kind="goal_execution")

        if not self.config.auto_execute_goals:
            self._cycles.append(registro)
            return registro
        if self._active_evolutions >= self.config.max_concurrent_evolutions:
            logger.debug("[Evolución] Límite de evoluciones simultáneas alcanzado")
            self._cycles.append(registro)
            return registro
        if self.squad_factory is None:
            registro.error = "No hay SquadFactory configurado"
            self._cycles.append(registro)
            return registro

        objetivo = self.introspection.get_high_priority_goal()
        if objetivo is None:
            self._cycles.append(registro)
            return registro

        self._active_evolutions += 1
        try:
            logger.info("[Evolución] Ejecutando objetivo: %s", objetivo.description[:70])
            self.introspection.update_goal_progress(objetivo.id, 0.1)

            squad = await self.squad_factory.spawn_squad(
                objetivo.description,
                budget=self.config.squad_budget,
                context=f"Auto-evolución — prioridad {objetivo.priority}",
            )
            registro.squads_spawned.append(squad.id)
            self.introspection.update_goal_progress(objetivo.id, 0.5)

        except Exception as exc:  # noqa: BLE001 - un objetivo fallido no para el bucle
            logger.error("[Evolución] El objetivo %s falló: %s", objetivo.id, exc)
            registro.error = str(exc)
            self.introspection.fail_goal(objetivo.id, str(exc))
        finally:
            self._active_evolutions -= 1

        self._cycles.append(registro)
        return registro

    async def _close_resolved_goals(self) -> list[str]:
        """Cierra los objetivos cuya señal original ya no se cumple.

        Es lo que permite saber si la evolución sirvió de algo: un objetivo sólo
        se completa cuando la métrica que lo motivó ha mejorado de verdad.
        """
        cerrados: list[str] = []
        metricas = self.supervisor.all_agent_metrics()

        for objetivo in self.introspection.active_goals():
            if objetivo.progress == 0.0:
                continue  # Aún no se ha intentado nada.

            agente = objetivo.evidence.get("agent")
            if agente and agente in metricas:
                actual = metricas[agente].get("error_rate")
                original = objetivo.evidence.get("error_rate")
                if actual is not None and original is not None and actual < original * 0.75:
                    self.introspection.update_goal_progress(objetivo.id, 1.0)
                    cerrados.append(objetivo.id)
                    logger.info(
                        "[Evolución] Objetivo %s completado: error de %.0f%% a %.0f%%",
                        objetivo.id,
                        original * 100,
                        actual * 100,
                    )

        return cerrados

    async def trigger_now(self) -> dict[str, Any]:
        """Ejecuta un ciclo completo de inmediato, sin esperar al temporizador."""
        logger.info("[Evolución] Ciclo manual disparado")
        introspeccion = await self.run_introspection_cycle()
        calibracion = await self.run_calibration_cycle()
        objetivos = await self.run_goal_cycle()
        return {
            "introspection": introspeccion.to_dict(),
            "calibration": calibracion.to_dict(),
            "goal_execution": objetivos.to_dict(),
        }

    # -- estado ------------------------------------------------------------
    def status(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "active_evolutions": self._active_evolutions,
            "config": self.config.to_dict(),
            "goals": self.introspection.stats(),
            "cycles_recorded": len(self._cycles),
            "recent_cycles": [c.to_dict() for c in list(self._cycles)[-10:]],
            "squad_factory_available": self.squad_factory is not None,
        }
