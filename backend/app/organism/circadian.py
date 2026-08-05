"""Ritmo circadiano: qué hace el organismo según cuánto hace que nadie le habla.

Los sistemas biológicos no ejecutan las mismas funciones a todas horas: la
consolidación de memoria ocurre durante el sueño, no durante la vigilia. Aquí
pasa lo mismo — es lo que permite que el sistema **siga siendo útil sin que
nadie interactúe**, en lugar de limitarse a esperar.

Fases:

    ACTIVE    Alguien interactúa ahora. Prioridad absoluta a responder;
              el trabajo de fondo se aparta para no competir por recursos.
    ALERT     Interacción reciente. Se atiende y se hace mantenimiento ligero.
    DROWSY    Sin interacción hace un rato. Empieza el trabajo introspectivo.
    DREAMING  Nadie desde hace mucho. Consolidación, poda y sueño profundo:
              es cuando el organismo reorganiza lo que aprendió.
    DEEP_REST Inactividad prolongada. Sólo late; espera a que algo ocurra.

La fase no la fija un reloj de pared sino el tiempo transcurrido desde la última
interacción, para que el organismo se adapte al ritmo real de su usuario.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("Circadian")


class Phase(str, Enum):
    ACTIVE = "active"
    ALERT = "alert"
    DROWSY = "drowsy"
    DREAMING = "dreaming"
    DEEP_REST = "deep_rest"


# Segundos de silencio a partir de los cuales se entra en cada fase.
PHASE_THRESHOLDS: list[tuple[float, Phase]] = [
    (60, Phase.ACTIVE),          # < 1 min
    (10 * 60, Phase.ALERT),      # < 10 min
    (45 * 60, Phase.DROWSY),     # < 45 min
    (4 * 3600, Phase.DREAMING),  # < 4 h
]
# A partir de ahí, DEEP_REST.

# Qué motores tienen sentido en cada fase.
#
# Los cuatro motores cognitivos del brain (`janitor`, `dreamer`, `curiosity`,
# `evolution`) reescriben la memoria, así que sólo corren cuando nadie está
# usando el sistema. Es el mismo motivo por el que la consolidación biológica
# ocurre durante el sueño: no competir con la percepción.
PHASE_ENGINES: dict[Phase, frozenset[str]] = {
    # En ACTIVE sólo late: todo lo demás competiría con la petición del usuario.
    Phase.ACTIVE: frozenset({"heartbeat"}),
    Phase.ALERT: frozenset({"heartbeat", "vitals"}),
    Phase.DROWSY: frozenset(
        {"heartbeat", "vitals", "introspection", "calibration", "janitor"}
    ),
    Phase.DREAMING: frozenset(
        {
            "heartbeat", "vitals", "introspection", "calibration", "consolidation", "goals",
            # El ciclo cognitivo completo.
            "janitor", "dreamer", "curiosity", "evolution",
        }
    ),
    # En reposo profundo sólo lo que consolida y depura; nada que genere trabajo.
    Phase.DEEP_REST: frozenset(
        {"heartbeat", "vitals", "consolidation", "janitor", "dreamer"}
    ),
}

# Multiplicador de cadencia por fase: dormido se piensa más despacio.
PHASE_CADENCE: dict[Phase, float] = {
    Phase.ACTIVE: 3.0,
    Phase.ALERT: 1.5,
    Phase.DROWSY: 1.0,
    Phase.DREAMING: 0.7,
    Phase.DEEP_REST: 2.0,
}


@dataclass(frozen=True)
class CircadianState:
    phase: Phase
    seconds_since_interaction: float
    active_engines: frozenset[str]
    cadence_multiplier: float

    def allows(self, engine: str) -> bool:
        return engine in self.active_engines

    def to_dict(self) -> dict[str, object]:
        return {
            "phase": self.phase.value,
            "seconds_since_interaction": round(self.seconds_since_interaction, 1),
            "active_engines": sorted(self.active_engines),
            "cadence_multiplier": self.cadence_multiplier,
        }


class CircadianRhythm:
    """Determina la fase del organismo a partir de su actividad reciente."""

    def __init__(self) -> None:
        # Arrancar como si acabara de haber interacción evita que el sistema
        # se ponga a soñar en el mismo instante del arranque.
        self._last_interaction = time.time()
        self._phase = Phase.ACTIVE
        self._transitions = 0

    def touch(self) -> None:
        """Registra una interacción. Devuelve el organismo a la vigilia."""
        self._last_interaction = time.time()

    @property
    def seconds_since_interaction(self) -> float:
        return time.time() - self._last_interaction

    def current(self) -> CircadianState:
        """Fase actual, registrando la transición si ha cambiado."""
        silencio = self.seconds_since_interaction
        fase = Phase.DEEP_REST
        for umbral, candidata in PHASE_THRESHOLDS:
            if silencio < umbral:
                fase = candidata
                break

        if fase != self._phase:
            logger.info(
                "[Circadiano] %s -> %s (%.0f s sin interacción)",
                self._phase.value,
                fase.value,
                silencio,
            )
            self._phase = fase
            self._transitions += 1

        return CircadianState(
            phase=fase,
            seconds_since_interaction=silencio,
            active_engines=PHASE_ENGINES[fase],
            cadence_multiplier=PHASE_CADENCE[fase],
        )

    @property
    def transitions(self) -> int:
        return self._transitions
