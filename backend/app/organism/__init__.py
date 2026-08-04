"""El organismo: la capa que mantiene al sistema vivo sin interacción.

- `homeostasis` — adapta la cadencia a los recursos, sin perder capacidades.
- `circadian`   — decide qué motores tienen sentido según cuánto hace que
                  nadie interactúa.
- `vital_daemon`— el bucle que late, aísla fallos y persiste su ritmo.
"""
from backend.app.organism.circadian import CircadianRhythm, Phase
from backend.app.organism.homeostasis import Homeostasis, ResourceProfile
from backend.app.organism.vital_daemon import (
    OrganismAlreadyRunning,
    VitalDaemon,
)

__all__ = [
    "CircadianRhythm",
    "Homeostasis",
    "OrganismAlreadyRunning",
    "Phase",
    "ResourceProfile",
    "VitalDaemon",
]
