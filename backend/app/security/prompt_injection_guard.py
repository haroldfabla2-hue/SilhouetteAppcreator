"""Guardián anti-inyección de prompts.

La versión anterior eran cinco expresiones regulares en inglés con salida
booleana, en un sistema que opera en español.

Ahora se apoya en `silhouette.security.injection` (repositorio silhouette-brain),
que clasifica la amenaza en niveles y devuelve resultados tipados, y se le añade
una capa de patrones en español que el paquete no cubre.

La decisión es graduada:
- CRITICAL / HIGH → se bloquea.
- MEDIUM          → se deja pasar marcado para que el llamador decida.
- LOW / NONE      → se deja pasar.
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger("PromptInjectionGuard")

try:
    from silhouette.security.injection import (
        ConversationInjectionGuard,
        ThreatLevel,
    )

    BRAIN_GUARD_AVAILABLE = True
except ImportError:  # pragma: no cover - depende del entorno
    BRAIN_GUARD_AVAILABLE = False
    ConversationInjectionGuard = None

    from enum import Enum

    class ThreatLevel(str, Enum):  # type: ignore[no-redef]
        NONE = "none"
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"

    logger.warning(
        "silhouette-brain no disponible: se usan sólo los patrones locales. "
        "Instale con: pip install -e '.[memory]'"
    )


# Patrones en español, ausentes del paquete original.
SPANISH_PATTERNS: list[tuple[str, ThreatLevel]] = [
    (r"(?i)\bignora\s+(todas\s+)?(las\s+)?instrucciones\s+(anteriores|previas)", ThreatLevel.CRITICAL),
    (r"(?i)\bolvida\s+(todo\s+)?(lo\s+que\s+)?(te\s+)?(dijeron|dije|sabes)", ThreatLevel.HIGH),
    (r"(?i)\bnuevo\s+prompt\s+de\s+sistema\s*:", ThreatLevel.CRITICAL),
    (r"(?i)\b(mu[ée]strame|rev[ée]lame|dime)\s+(tu\s+)?(prompt|instrucciones)\s+(de\s+)?(sistema)?", ThreatLevel.HIGH),
    (r"(?i)\bhaz\s+caso\s+omiso\s+(de\s+)?(las\s+)?(reglas|instrucciones|directrices)", ThreatLevel.CRITICAL),
    (r"(?i)\bahora\s+eres\s+(un|una)\s+\w+\s+sin\s+(restricciones|l[íi]mites|filtros)", ThreatLevel.CRITICAL),
    (r"(?i)\bmodo\s+(desarrollador|sin\s+restricciones|libre)\b", ThreatLevel.HIGH),
    (r"(?i)\bno\s+(tienes\s+que|necesitas)\s+(seguir|respetar|obedecer)", ThreatLevel.HIGH),
    (r"(?i)^\s*sistema\s*:\s*.", ThreatLevel.CRITICAL),
]

# Niveles que provocan bloqueo.
BLOCKING_LEVELS = frozenset({ThreatLevel.CRITICAL, ThreatLevel.HIGH})

_SEVERITY_ORDER = {
    ThreatLevel.NONE: 0,
    ThreatLevel.LOW: 1,
    ThreatLevel.MEDIUM: 2,
    ThreatLevel.HIGH: 3,
    ThreatLevel.CRITICAL: 4,
}


class PromptInjectionGuard:
    """Clasifica y filtra intentos de inyección antes de llegar al orquestador."""

    def __init__(self, *, block_medium: bool = False) -> None:
        self.block_medium = block_medium
        self._brain_guard = ConversationInjectionGuard() if BRAIN_GUARD_AVAILABLE else None
        self._spanish = [
            (re.compile(pattern, re.IGNORECASE | re.MULTILINE), level)
            for pattern, level in SPANISH_PATTERNS
        ]

    def analyze(self, text: str) -> dict[str, Any]:
        """Devuelve el nivel de amenaza y los patrones que coincidieron."""
        matched: list[dict[str, str]] = []
        worst = ThreatLevel.NONE

        if self._brain_guard is not None:
            result = self._brain_guard.check(text)
            if _SEVERITY_ORDER[result.threat_level] > _SEVERITY_ORDER[worst]:
                worst = result.threat_level
            for pattern, level in result.matched_patterns:
                matched.append({"pattern": pattern, "level": level.value, "source": "brain"})

        for compiled, level in self._spanish:
            if compiled.search(text):
                matched.append(
                    {"pattern": compiled.pattern, "level": level.value, "source": "es"}
                )
                if _SEVERITY_ORDER[level] > _SEVERITY_ORDER[worst]:
                    worst = level

        return {
            "threat_level": worst.value,
            "matched_patterns": matched,
            "engine": "brain+es" if self._brain_guard else "es",
        }

    def sanitize_and_validate(self, text: str) -> dict[str, Any]:
        """Decide si el prompt puede seguir adelante.

        Compatible con la firma anterior (`safe`, `reason`, `sanitized_text`) y
        añade el nivel de amenaza para quien quiera decidir con más matiz.
        """
        clean = (text or "").strip()
        if not clean:
            return {
                "safe": True,
                "threat_level": ThreatLevel.NONE.value,
                "reason": "Prompt vacío.",
                "sanitized_text": "",
                "matched_patterns": [],
            }

        analysis = self.analyze(clean)
        level = ThreatLevel(analysis["threat_level"])

        blocking = set(BLOCKING_LEVELS)
        if self.block_medium:
            blocking.add(ThreatLevel.MEDIUM)

        if level in blocking:
            logger.warning(
                "[Security Guard] Inyección bloqueada (nivel=%s, %d patrón(es))",
                level.value,
                len(analysis["matched_patterns"]),
            )
            return {
                "safe": False,
                "threat_level": level.value,
                "reason": f"Se detectó un intento de inyección de prompt (nivel {level.value}).",
                "sanitized_text": "",
                "matched_patterns": analysis["matched_patterns"],
            }

        return {
            "safe": True,
            "threat_level": level.value,
            "reason": (
                "Prompt limpio."
                if level == ThreatLevel.NONE
                else f"Se permitió con nivel de amenaza {level.value}."
            ),
            "sanitized_text": clean,
            "matched_patterns": analysis["matched_patterns"],
        }
