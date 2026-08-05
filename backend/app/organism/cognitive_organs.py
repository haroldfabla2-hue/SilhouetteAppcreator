"""Motores cognitivos como órganos del organismo.

El paquete `silhouette-brain` trae cuatro motores implementados y probados que
hasta ahora no se ejecutaban nunca. Aquí se conectan al daemon vital para que
funcionen solos, en la fase del ciclo en que cada uno tiene sentido:

| Motor      | Qué hace                                              | Fase |
|------------|-------------------------------------------------------|------|
| Curiosity  | Detecta huecos en el grafo y formula preguntas         | DREAMING |
| Janitor    | Depura memoria: duplicados, ruido, registros caducados | DREAMING / DEEP_REST |
| Dreamer    | Consolida lo episódico en semántico y en el grafo      | DREAMING / DEEP_REST |
| Evolution  | Reevalúa importancias según el uso real                | DREAMING |

El paralelo biológico no es decorativo: la consolidación de memoria ocurre
durante el sueño porque es cuando no compite con la percepción. Aquí igual —
estos motores reescriben la memoria, así que ejecutarlos mientras el usuario
trabaja sería competir por el mismo recurso.

La Curiosidad merece una nota: **sólo genera preguntas, nunca hechos**. Es la
misma regla que rige este proyecto — si no lo sabe, lo pregunta, no lo inventa.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("CognitiveOrgans")

try:
    from silhouette.engines import DEFAULT_ENGINES

    ENGINES_AVAILABLE = True
except ImportError:  # pragma: no cover - depende del entorno
    ENGINES_AVAILABLE = False
    DEFAULT_ENGINES = {}
    logger.warning(
        "silhouette-brain no está instalado: los motores cognitivos quedan "
        "desactivados. Instale con: pip install -e '.[memory]'"
    )

# Cadencia base de cada motor, en segundos. La homeostasis y la fase circadiana
# la escalan después.
ENGINE_INTERVALS: dict[str, float] = {
    "curiosity": 30 * 60,   # cada 30 min: buscar huecos no es urgente
    "janitor": 60 * 60,     # cada hora: la limpieza puede esperar
    "dreamer": 45 * 60,     # cada 45 min: consolidar es el trabajo del sueño
    "evolution": 2 * 3600,  # cada 2 h: reevaluar importancias es lento por diseño
}


class CognitiveEnginesUnavailable(RuntimeError):
    """Los motores cognitivos no están disponibles en este entorno."""


@dataclass
class EngineRun:
    """Resultado de una ejecución de un motor cognitivo."""

    engine: str
    ok: bool
    summary: str = ""
    stats: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine": self.engine,
            "ok": self.ok,
            "summary": self.summary,
            "stats": self.stats,
            "duration_ms": round(self.duration_ms, 2),
            "error": self.error,
        }


class CognitiveOrgans:
    """Ejecuta los motores del brain sobre la memoria real del sistema."""

    def __init__(self, brain: Any = None) -> None:
        if brain is None:
            from backend.app.services.silhouette_brain_service import (
                SilhouetteBrainService,
            )

            brain = SilhouetteBrainService()
        self.brain = brain
        self._history: list[EngineRun] = []

    @property
    def available(self) -> bool:
        return ENGINES_AVAILABLE and getattr(self.brain, "available", False)

    @property
    def engine_names(self) -> list[str]:
        return sorted(DEFAULT_ENGINES) if ENGINES_AVAILABLE else []

    async def run_engine(self, name: str) -> EngineRun:
        """Ejecuta un motor concreto sobre la memoria.

        Los motores son síncronos (SQLite); se ejecutan en el executor para no
        bloquear el bucle de eventos.
        """
        if not ENGINES_AVAILABLE:
            raise CognitiveEnginesUnavailable(
                "silhouette-brain no está instalado; no hay motores cognitivos."
            )
        engine = DEFAULT_ENGINES.get(name)
        if engine is None:
            raise KeyError(
                f"Motor desconocido '{name}'. Disponibles: {', '.join(sorted(DEFAULT_ENGINES))}"
            )
        if not getattr(self.brain, "available", False):
            raise CognitiveEnginesUnavailable(
                "La memoria cognitiva no está disponible; los motores no tienen sobre qué operar."
            )

        memoria = self.brain._memory  # noqa: SLF001 - acceso deliberado al sistema real
        loop = asyncio.get_running_loop()
        resultado = await loop.run_in_executor(None, lambda: engine.run(memoria))

        ejecucion = EngineRun(
            engine=name,
            ok=bool(resultado.ok),
            summary=str(resultado.summary or ""),
            stats=dict(resultado.stats or {}),
            duration_ms=float(resultado.duration_ms or 0.0),
            error=resultado.error,
        )
        self._history.append(ejecucion)
        del self._history[:-100]  # el historial no crece sin límite

        if ejecucion.ok:
            logger.info("[Cognición] %s: %s", name, ejecucion.summary)
        else:
            # El motor aísla sus propios fallos; aquí sólo se reportan.
            logger.warning("[Cognición] %s falló: %s", name, ejecucion.error)
        return ejecucion

    async def run_all(self) -> list[EngineRun]:
        """Ejecuta los cuatro motores en secuencia.

        En secuencia y no en paralelo a propósito: todos reescriben la misma
        memoria, y el orden importa — Janitor limpia antes de que Dreamer
        consolide, y Evolution reevalúa sobre el resultado.
        """
        orden = ["janitor", "dreamer", "curiosity", "evolution"]
        return [await self.run_engine(n) for n in orden if n in DEFAULT_ENGINES]

    def register_with(self, organism: Any) -> list[str]:
        """Da de alta cada motor como órgano del daemon vital.

        Devuelve los nombres registrados. Si los motores no están disponibles no
        se registra nada y se dice — en lugar de registrar órganos que fallarían
        en cada latido.
        """
        if not self.available:
            logger.info("[Cognición] Motores no disponibles: no se registra ninguno.")
            return []

        registrados: list[str] = []
        for nombre in sorted(DEFAULT_ENGINES):
            intervalo = ENGINE_INTERVALS.get(nombre, 3600.0)
            organism.register(nombre, self._make_organ(nombre), intervalo)
            registrados.append(nombre)

        logger.info("[Cognición] %d motor(es) registrados: %s", len(registrados), ", ".join(registrados))
        return registrados

    def _make_organ(self, nombre: str):
        """Crea la función-órgano de un motor, con su nombre capturado."""

        async def organo() -> str:
            ejecucion = await self.run_engine(nombre)
            if not ejecucion.ok:
                # Que el órgano falle es información: el daemon lo registra y
                # marca la salud del motor.
                raise RuntimeError(ejecucion.error or f"{nombre} falló sin detalle")
            return ejecucion.summary

        organo.__name__ = f"organ_{nombre}"
        return organo

    def stats(self) -> dict[str, Any]:
        """Estado de los motores, contado desde ejecuciones reales."""
        if not self.available:
            return {
                "available": False,
                "reason": (
                    "silhouette-brain no instalado"
                    if not ENGINES_AVAILABLE
                    else "la memoria cognitiva no está disponible"
                ),
                "engines": [],
            }

        por_motor: dict[str, dict[str, Any]] = {}
        for nombre in sorted(DEFAULT_ENGINES):
            ejecuciones = [e for e in self._history if e.engine == nombre]
            exitos = sum(1 for e in ejecuciones if e.ok)
            por_motor[nombre] = {
                "runs": len(ejecuciones),
                "failures": len(ejecuciones) - exitos,
                # Sin ejecuciones no se afirma nada.
                "last_summary": ejecuciones[-1].summary if ejecuciones else None,
                "interval_s": ENGINE_INTERVALS.get(nombre),
            }

        return {
            "available": True,
            "engines": por_motor,
            "total_runs": len(self._history),
            "recent": [e.to_dict() for e in self._history[-10:]],
        }
