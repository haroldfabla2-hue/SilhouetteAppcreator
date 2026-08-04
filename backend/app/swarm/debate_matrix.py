"""Matriz de debate multi-agente: Creador → Crítico → Juez.

La versión anterior aceptaba un `llm_router` y no lo usaba nunca: devolvía un
fragmento de FastAPI escrito a mano con el prompt interpolado y un
`quality_score` constante de 0.97.

Esta implementación ejecuta el ciclo de verdad. Cada rol es una llamada real al
router con su propio prompt de sistema, y el veredicto del juez se extrae de la
respuesta del modelo. Si no hay router, la matriz falla en cerrado en lugar de
fingir un debate.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("DebateSwarmMatrix")

CREATOR_SYSTEM = """Eres el AGENTE CREADOR de un sistema de debate técnico.
Propón la mejor solución que puedas al problema planteado.
Sé concreto: si la respuesta es código, entrégalo completo y ejecutable.
No expliques tu proceso; entrega la propuesta."""

CRITIC_SYSTEM = """Eres el AGENTE CRÍTICO de un sistema de debate técnico.
Examina la propuesta buscando fallos reales: errores de corrección, casos límite
no cubiertos, vulnerabilidades de seguridad e ineficiencias.
Sé específico y severo, pero no inventes defectos. Si la propuesta es sólida en
algún aspecto, dilo. Enumera los problemas por orden de gravedad."""

JUDGE_SYSTEM = """Eres el AGENTE JUEZ de un sistema de debate técnico.
Recibes una propuesta y su crítica. Produce la solución final que incorpore las
críticas fundadas y descarte las infundadas.

Responde EXACTAMENTE en este formato:

VEREDICTO: <APROBADO|RECHAZADO>
PUNTUACION: <número entre 0.0 y 1.0>
JUSTIFICACION: <una o dos frases>
SOLUCION_FINAL:
<la solución completa>"""


class DebateUnavailable(RuntimeError):
    """No hay router de modelos disponible para ejecutar el debate."""


@dataclass
class DebateRound:
    """Resultado de una ronda completa, con la traza de cada rol."""

    prompt: str
    proposal: str = ""
    critique: str = ""
    verdict: str = "RECHAZADO"
    score: float = 0.0
    rationale: str = ""
    final_answer: str = ""
    errors: list[str] = field(default_factory=list)

    @property
    def approved(self) -> bool:
        return self.verdict.upper() == "APROBADO"

    def to_dict(self) -> dict[str, Any]:
        return {
            "debate_executed": not self.errors,
            "prompt": self.prompt,
            "creator_proposal": self.proposal,
            "critic_critique": self.critique,
            "judge_verdict": {
                "status": self.verdict,
                "approved": self.approved,
                "quality_score": self.score,
                "rationale": self.rationale,
                "final_answer": self.final_answer,
            },
            "errors": self.errors,
        }


class DebateSwarmMatrix:
    """Orquesta el ciclo Creador → Crítico → Juez sobre un `LLMRouter`."""

    def __init__(self, llm_router: Any = None, *, temperature: float = 0.4) -> None:
        self.llm_router = llm_router
        self.temperature = temperature
        if llm_router is None:
            logger.warning(
                "DebateSwarmMatrix creada sin router: execute_debate_round fallará "
                "hasta que se le inyecte uno."
            )

    async def _ask(self, system: str, user: str, *, temperature: float | None = None) -> str:
        if self.llm_router is None:
            raise DebateUnavailable(
                "DebateSwarmMatrix necesita un LLMRouter. Inyéctelo en el constructor."
            )
        prompt = f"{system}\n\n---\n\n{user}"
        return await self.llm_router.chat_completion(
            prompt, temperature=temperature if temperature is not None else self.temperature
        )

    async def execute_debate_round(self, prompt: str) -> dict[str, Any]:
        """Ejecuta una ronda completa y devuelve la traza real de los tres roles."""
        round_ = DebateRound(prompt=prompt)
        logger.info("[Debate] Iniciando ronda: %s", prompt[:60])

        try:
            round_.proposal = await self._ask(CREATOR_SYSTEM, f"PROBLEMA:\n{prompt}")
        except Exception as exc:
            logger.error("[Debate] El creador falló: %s", exc)
            round_.errors.append(f"creator: {exc}")
            return round_.to_dict()

        try:
            round_.critique = await self._ask(
                CRITIC_SYSTEM,
                f"PROBLEMA:\n{prompt}\n\nPROPUESTA A EXAMINAR:\n{round_.proposal}",
                temperature=0.2,
            )
        except Exception as exc:
            logger.error("[Debate] El crítico falló: %s", exc)
            round_.errors.append(f"critic: {exc}")
            # Sin crítica el debate pierde su razón de ser: se detiene.
            return round_.to_dict()

        try:
            raw_verdict = await self._ask(
                JUDGE_SYSTEM,
                (
                    f"PROBLEMA:\n{prompt}\n\n"
                    f"PROPUESTA:\n{round_.proposal}\n\n"
                    f"CRITICA:\n{round_.critique}"
                ),
                temperature=0.1,
            )
        except Exception as exc:
            logger.error("[Debate] El juez falló: %s", exc)
            round_.errors.append(f"judge: {exc}")
            return round_.to_dict()

        self._parse_verdict(raw_verdict, round_)
        logger.info("[Debate] Veredicto: %s (%.2f)", round_.verdict, round_.score)
        return round_.to_dict()

    @staticmethod
    def _parse_verdict(raw: str, round_: DebateRound) -> None:
        """Extrae el veredicto estructurado de la respuesta del juez.

        Si el modelo no respeta el formato, se conserva la respuesta completa
        como solución y se marca la puntuación como desconocida (0.0) en lugar
        de inventar una.
        """
        verdict_match = re.search(r"VEREDICTO:\s*(APROBADO|RECHAZADO)", raw, re.IGNORECASE)
        if verdict_match:
            round_.verdict = verdict_match.group(1).upper()

        score_match = re.search(r"PUNTUACION:\s*([01](?:[.,]\d+)?)", raw, re.IGNORECASE)
        if score_match:
            try:
                round_.score = max(0.0, min(1.0, float(score_match.group(1).replace(",", "."))))
            except ValueError:
                round_.score = 0.0

        rationale_match = re.search(
            r"JUSTIFICACION:\s*(.+?)(?=\nSOLUCION_FINAL:|\Z)", raw, re.IGNORECASE | re.DOTALL
        )
        if rationale_match:
            round_.rationale = rationale_match.group(1).strip()

        solution_match = re.search(r"SOLUCION_FINAL:\s*(.+)", raw, re.IGNORECASE | re.DOTALL)
        round_.final_answer = solution_match.group(1).strip() if solution_match else raw.strip()

        if not verdict_match:
            round_.rationale = round_.rationale or "El juez no devolvió un veredicto con formato."
