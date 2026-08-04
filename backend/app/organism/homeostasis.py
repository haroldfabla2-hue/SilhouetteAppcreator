"""Homeostasis: adaptación al entorno sin pérdida de capacidades.

Portado del `homeostasis.py` de Silhouette Agency OS, cuya filosofía se conserva
literalmente:

    «Nunca perder capacidades, sólo adaptarlas al entorno.»

El análogo biológico es la homeostasis: mantener el equilibrio interno pese a
que el entorno cambie. Aquí eso significa que el organismo **nunca desactiva un
motor cognitivo por falta de recursos**; lo que hace es espaciar su cadencia.
Bajo presión el sistema piensa más despacio, no menos profundamente.

Si `psutil` no está disponible se asume un perfil BALANCED y se declara que la
medición no es real (`measured: False`), en lugar de inventar cifras.
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("Homeostasis")

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:  # pragma: no cover - depende del entorno
    PSUTIL_AVAILABLE = False
    logger.warning("psutil no disponible: la homeostasis usará el perfil BALANCED por defecto.")


class ResourceProfile(str, Enum):
    """Perfil de recursos disponibles."""

    CRITICAL = "critical"        # El anfitrión está ahogado
    CONSTRAINED = "constrained"  # Poco margen
    BALANCED = "balanced"        # Margen normal
    ABUNDANT = "abundant"        # Margen de sobra


# Multiplicador de cadencia por perfil. Mayor = los ciclos se espacian más.
# Ningún perfil desactiva nada: ese es el punto.
CADENCE_MULTIPLIER: dict[ResourceProfile, float] = {
    ResourceProfile.CRITICAL: 6.0,
    ResourceProfile.CONSTRAINED: 2.5,
    ResourceProfile.BALANCED: 1.0,
    ResourceProfile.ABUNDANT: 0.6,
}

# Cuántas tareas cognitivas simultáneas admite cada perfil.
CONCURRENCY: dict[ResourceProfile, int] = {
    ResourceProfile.CRITICAL: 1,
    ResourceProfile.CONSTRAINED: 2,
    ResourceProfile.BALANCED: 4,
    ResourceProfile.ABUNDANT: 8,
}

# Umbrales de saturación (porcentaje de uso).
CRITICAL_THRESHOLD = 92.0
CONSTRAINED_THRESHOLD = 78.0
ABUNDANT_THRESHOLD = 45.0


@dataclass
class EnvironmentState:
    """Estado medido del entorno de ejecución."""

    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    ram_available_gb: float = 0.0
    disk_percent: float = 0.0
    cpu_count: int = 1
    measured: bool = False
    measured_at: float = field(default_factory=time.time)

    @property
    def pressure(self) -> float:
        """Presión global: el recurso más saturado es el que manda."""
        return max(self.cpu_percent, self.ram_percent, self.disk_percent)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HomeostaticConfig:
    """Configuración sintetizada a partir del estado del entorno."""

    profile: str
    cadence_multiplier: float
    max_concurrency: int
    reason: str
    environment: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Homeostasis:
    """Mide el entorno y sintetiza la configuración adaptada."""

    def __init__(self, *, sample_interval_s: float = 30.0) -> None:
        self.sample_interval_s = sample_interval_s
        self._last_sample: EnvironmentState | None = None
        self._last_sample_at = 0.0
        self._forced_profile: ResourceProfile | None = None

    # -- medición ----------------------------------------------------------
    def measure(self, *, force: bool = False) -> EnvironmentState:
        """Mide el entorno, con caché para no penalizar cada tick."""
        ahora = time.time()
        if (
            not force
            and self._last_sample is not None
            and (ahora - self._last_sample_at) < self.sample_interval_s
        ):
            return self._last_sample

        if not PSUTIL_AVAILABLE:
            estado = EnvironmentState(measured=False, cpu_count=os.cpu_count() or 1)
        else:
            memoria = psutil.virtual_memory()
            try:
                disco = psutil.disk_usage(os.getcwd()).percent
            except OSError:
                disco = 0.0
            estado = EnvironmentState(
                # interval=None devuelve el uso desde la llamada anterior sin
                # bloquear; en la primera llamada da 0.0, que es aceptable.
                cpu_percent=psutil.cpu_percent(interval=None),
                ram_percent=memoria.percent,
                ram_available_gb=round(memoria.available / (1024**3), 2),
                disk_percent=disco,
                cpu_count=psutil.cpu_count() or 1,
                measured=True,
            )

        self._last_sample = estado
        self._last_sample_at = ahora
        return estado

    # -- síntesis ----------------------------------------------------------
    def classify(self, estado: EnvironmentState) -> tuple[ResourceProfile, str]:
        """Clasifica el entorno en un perfil, explicando por qué."""
        if self._forced_profile is not None:
            return self._forced_profile, "Perfil forzado manualmente"

        if not estado.measured:
            return ResourceProfile.BALANCED, "psutil no disponible; se asume perfil equilibrado"

        presion = estado.pressure
        if presion >= CRITICAL_THRESHOLD:
            return (
                ResourceProfile.CRITICAL,
                f"Recurso al {presion:.0f}%: el anfitrión está saturado",
            )
        if presion >= CONSTRAINED_THRESHOLD:
            return (
                ResourceProfile.CONSTRAINED,
                f"Recurso al {presion:.0f}%: margen reducido",
            )
        if presion <= ABUNDANT_THRESHOLD and estado.cpu_count >= 4:
            return (
                ResourceProfile.ABUNDANT,
                f"Recurso al {presion:.0f}% con {estado.cpu_count} núcleos: margen amplio",
            )
        return ResourceProfile.BALANCED, f"Recurso al {presion:.0f}%: margen normal"

    def synthesize(self, *, force: bool = False) -> HomeostaticConfig:
        """Devuelve la configuración adaptada al entorno actual."""
        estado = self.measure(force=force)
        perfil, motivo = self.classify(estado)
        return HomeostaticConfig(
            profile=perfil.value,
            cadence_multiplier=CADENCE_MULTIPLIER[perfil],
            max_concurrency=CONCURRENCY[perfil],
            reason=motivo,
            environment=estado.to_dict(),
        )

    def adapt_interval(self, base_interval_s: float) -> float:
        """Ajusta un intervalo base a la presión actual del entorno.

        Nunca devuelve infinito ni cero: bajo presión el organismo se ralentiza,
        pero no se detiene ni se acelera sin control.
        """
        multiplicador = self.synthesize().cadence_multiplier
        return max(1.0, base_interval_s * multiplicador)

    # -- control manual ----------------------------------------------------
    def force_profile(self, profile: str | None) -> None:
        """Fija un perfil manualmente. `None` devuelve el control a la medición."""
        if profile is None:
            self._forced_profile = None
            logger.info("[Homeostasis] Perfil automático restaurado")
            return
        try:
            self._forced_profile = ResourceProfile(profile.lower())
        except ValueError as exc:
            raise ValueError(
                f"Perfil desconocido '{profile}'. "
                f"Válidos: {', '.join(p.value for p in ResourceProfile)}"
            ) from exc
        logger.info("[Homeostasis] Perfil forzado a %s", self._forced_profile.value)

    @property
    def is_forced(self) -> bool:
        return self._forced_profile is not None
