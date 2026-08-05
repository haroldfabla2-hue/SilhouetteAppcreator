"""Asignación de modelo por agente.

Se afirmaba que el orquestador repartía los agentes entre CLIs distintos —
«Reasoner con Claude Code, Executor con Gemini CLI, Verifier con Antigravity».
No era así: los cinco agentes compartían un único router con la misma cadena de
fallback, de modo que todos acababan en el mismo proveedor.

Aquí eso pasa a ser cierto y configurable. Cada agente declara qué modelos
prefiere y en qué orden; el router respeta esa preferencia y sólo cae a la
cadena general cuando ninguno de los preferidos está disponible.

El reparto tiene sentido práctico, no es decorativo:

- El **razonador** y el **verificador** se benefician de modelos fuertes en
  análisis; se les da temperatura baja.
- El **ejecutor de código** va a un CLI con acceso al sistema de archivos.
- El **planificador** necesita coherencia estructural, no creatividad.

Sin configuración, todos usan el mismo router de siempre: la asignación es una
mejora, no un requisito.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("AgentModels")

CONFIG_PATH = Path("data/agent_models.json")


@dataclass
class AgentModelPolicy:
    """Qué modelos prefiere un agente y con qué parámetros trabaja."""

    agent: str
    #: Proveedores preferidos, en orden. Nombres de `LLMProvider` o de CLI.
    preferred: list[str] = field(default_factory=list)
    temperature: float = 0.7
    max_tokens: int = 2000
    #: Si es False, no se cae a la cadena general cuando fallan los preferidos.
    allow_fallback: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Reparto por defecto. Se aplica sólo sobre lo que esté realmente instalado.
DEFAULT_POLICIES: dict[str, AgentModelPolicy] = {
    "reasoner": AgentModelPolicy(
        agent="reasoner",
        preferred=["cli_claude_code", "openrouter_claude_3_5", "openrouter_gpt4_turbo"],
        temperature=0.3,
    ),
    "planner": AgentModelPolicy(
        agent="planner",
        preferred=["openrouter_gpt4_turbo", "cli_claude_code", "openrouter_llama70b"],
        temperature=0.2,
    ),
    "executor_code": AgentModelPolicy(
        agent="executor_code",
        preferred=["cli_claude_code", "cli_cursor", "cli_codex", "openrouter_deepseek_v4"],
        temperature=0.1,
    ),
    "executor_web": AgentModelPolicy(
        agent="executor_web",
        preferred=["cli_gemini", "openrouter_gemini", "openrouter_llama70b"],
        temperature=0.4,
    ),
    "executor_general": AgentModelPolicy(agent="executor_general", preferred=[], temperature=0.5),
    "executor_docs": AgentModelPolicy(agent="executor_docs", preferred=[], temperature=0.6),
    "verifier": AgentModelPolicy(
        agent="verifier",
        preferred=["cli_claude_code", "openrouter_claude_3_5"],
        # Verificar exige consistencia: la temperatura más baja del sistema.
        temperature=0.05,
    ),
    "memory_manager": AgentModelPolicy(agent="memory_manager", preferred=[], temperature=0.3),
}


class AgentModelRegistry:
    """Guarda y resuelve qué modelo usa cada agente."""

    def __init__(self, path: Path = CONFIG_PATH) -> None:
        self.path = Path(path)
        self._policies: dict[str, AgentModelPolicy] = dict(DEFAULT_POLICIES)
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("No se pudo leer %s (%s); se usan los valores por defecto.", self.path, exc)
            return
        for nombre, datos in raw.items():
            datos.pop("agent", None)
            self._policies[nombre] = AgentModelPolicy(agent=nombre, **datos)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {n: p.to_dict() for n, p in self._policies.items()}
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)

    # -- consulta ----------------------------------------------------------
    def policy_for(self, agent: str) -> AgentModelPolicy:
        return self._policies.get(agent, AgentModelPolicy(agent=agent))

    def resolve_provider(self, agent: str, router: Any) -> Any | None:
        """Primer proveedor preferido que esté realmente disponible.

        Devuelve `None` si ninguno lo está — entonces el router usa su cadena
        habitual. No se devuelve un proveedor no disponible sólo por respetar
        la preferencia: eso garantizaría un fallo.
        """
        from backend.app.core.llm_router import LLMProvider

        for nombre in self.policy_for(agent).preferred:
            try:
                proveedor = LLMProvider(nombre)
            except ValueError:
                logger.debug("Proveedor desconocido en la política de %s: %s", agent, nombre)
                continue
            if router._is_provider_available(proveedor):  # noqa: SLF001
                return proveedor
        return None

    def all_policies(self) -> dict[str, dict[str, Any]]:
        return {n: p.to_dict() for n, p in self._policies.items()}

    # -- modificación ------------------------------------------------------
    def set_policy(
        self,
        agent: str,
        *,
        preferred: list[str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        allow_fallback: bool | None = None,
    ) -> AgentModelPolicy:
        politica = self._policies.get(agent) or AgentModelPolicy(agent=agent)
        if preferred is not None:
            politica.preferred = list(preferred)
        if temperature is not None:
            politica.temperature = max(0.0, min(1.0, temperature))
        if max_tokens is not None:
            politica.max_tokens = max(1, max_tokens)
        if allow_fallback is not None:
            politica.allow_fallback = allow_fallback

        self._policies[agent] = politica
        self._save()
        logger.info("[Modelos] Política de %s actualizada: %s", agent, politica.preferred)
        return politica

    def effective_assignment(self, router: Any) -> dict[str, Any]:
        """Qué modelo usaría hoy cada agente, con lo que hay instalado.

        Es la respuesta honesta a «¿qué agente usa qué?»: se resuelve contra la
        disponibilidad real, no contra la lista de deseos.
        """
        asignacion: dict[str, Any] = {}
        for nombre, politica in self._policies.items():
            proveedor = self.resolve_provider(nombre, router)
            asignacion[nombre] = {
                "preferred": politica.preferred,
                "resolved": proveedor.value if proveedor is not None else None,
                "reason": (
                    "preferencia disponible"
                    if proveedor is not None
                    else (
                        "ningún preferido disponible; usa la cadena general"
                        if politica.preferred
                        else "sin preferencia declarada"
                    )
                ),
                "temperature": politica.temperature,
            }
        return asignacion


agent_models = AgentModelRegistry()
