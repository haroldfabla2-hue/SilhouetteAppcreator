"""Sesiones compartidas entre agentes y CLIs concurrentes.

Resuelve tres carencias reales que una auditoría dejó en evidencia:

1. **No había identificador de sesión.** Cada invocación de CLI era un proceso
   aislado sin nada que lo ligara a las demás. Si el planificador descomponía
   una tarea en tres pasos, el ejecutor arrancaba sin saber qué había decidido
   el planificador.
2. **El prompt no llevaba contexto.** `run_cli(cli, prompt)` recibía texto
   plano; la memoria cognitiva existía y nadie la consultaba antes de invocar.
3. **Las respuestas no se guardaban.** Lo que producía un CLI se devolvía al
   llamador y se perdía: la sesión siguiente empezaba de cero.

Una `AgentSession` es el hilo conductor: agrupa las invocaciones de una misma
instrucción, acumula lo que cada agente aportó, y compone el prompt de cada
llamada con ese historial más lo que la memoria de largo plazo sepa del tema.

Coherencia real, no declarada: hay tests que ejecutan dos agentes en la misma
sesión y comprueban que el segundo ve lo que produjo el primero.
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

logger = logging.getLogger("AgentSession")

# Cuántas contribuciones previas se incluyen en el prompt de la siguiente llamada.
MAX_CONTEXT_ENTRIES = 12
# Presupuesto de caracteres para el bloque de contexto compartido.
MAX_CONTEXT_CHARS = 6000
# Presupuesto de tokens al consultar la memoria de largo plazo.
MEMORY_TOKEN_BUDGET = 1200


@dataclass
class Contribution:
    """Lo que un agente aportó a la sesión."""

    agent: str
    role: str
    content: str
    model: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def as_context(self, limit: int = 900) -> str:
        cuerpo = self.content.strip()
        if len(cuerpo) > limit:
            cuerpo = cuerpo[:limit] + " […]"
        origen = f"{self.agent}" + (f" vía {self.model}" if self.model else "")
        return f"[{origen}]\n{cuerpo}"


@dataclass
class AgentSession:
    """Hilo compartido por todos los agentes que atienden una misma instrucción."""

    goal: str
    session_id: str = field(default_factory=lambda: f"ses_{uuid.uuid4().hex[:12]}")
    contributions: list[Contribution] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    # -- acumulación -------------------------------------------------------
    def add(self, agent: str, content: str, *, role: str = "output", model: str = "") -> Contribution:
        """Registra lo que un agente produjo. Es lo que verán los siguientes."""
        contribucion = Contribution(agent=agent, role=role, content=content, model=model)
        self.contributions.append(contribucion)
        return contribucion

    def by_agent(self, agent: str) -> list[Contribution]:
        return [c for c in self.contributions if c.agent == agent]

    # -- composición del prompt -------------------------------------------
    def shared_context(self, *, exclude_agent: str | None = None) -> str:
        """Resumen de lo aportado hasta ahora, para inyectar en el prompt.

        Se excluye lo del propio agente: repetirle su salida anterior gasta
        contexto sin aportarle nada que no sepa.
        """
        relevantes = [
            c for c in self.contributions if exclude_agent is None or c.agent != exclude_agent
        ]
        if not relevantes:
            return ""

        bloques: list[str] = []
        usados = 0
        # De lo más reciente hacia atrás: lo último es lo que más importa.
        for contribucion in reversed(relevantes[-MAX_CONTEXT_ENTRIES:]):
            texto = contribucion.as_context()
            if usados + len(texto) > MAX_CONTEXT_CHARS:
                break
            bloques.append(texto)
            usados += len(texto)

        return "\n\n".join(reversed(bloques))

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "goal": self.goal,
            "created_at": self.created_at,
            "contributions": [c.to_dict() for c in self.contributions],
            "agents_involved": sorted({c.agent for c in self.contributions}),
            "metadata": self.metadata,
        }


class SessionManager:
    """Crea sesiones, compone prompts con contexto y persiste lo aprendido.

    Es el punto por el que pasa toda invocación que quiera ser coherente con
    las demás. Si la memoria de largo plazo no está disponible, se sigue
    funcionando con el contexto de la sesión en curso — y se dice, en lugar de
    fingir que hubo recuperación.
    """

    def __init__(self, brain: Any = None) -> None:
        if brain is None:
            from backend.app.services.silhouette_brain_service import (
                SilhouetteBrainService,
            )

            brain = SilhouetteBrainService()
        self.brain = brain
        self._sessions: dict[str, AgentSession] = {}
        self._lock = asyncio.Lock()

    # -- ciclo de vida -----------------------------------------------------
    def create(self, goal: str, **metadata: Any) -> AgentSession:
        sesion = AgentSession(goal=goal, metadata=dict(metadata))
        self._sessions[sesion.session_id] = sesion
        logger.info("[Sesión] %s abierta: %s", sesion.session_id, goal[:70])
        return sesion

    def get(self, session_id: str) -> AgentSession | None:
        return self._sessions.get(session_id)

    def get_or_create(self, session_id: str | None, goal: str, **metadata: Any) -> AgentSession:
        if session_id:
            existente = self._sessions.get(session_id)
            if existente is not None:
                return existente
        return self.create(goal, **metadata)

    def all_sessions(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self._sessions.values()]

    def close(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    # -- memoria de largo plazo -------------------------------------------
    async def recall_context(self, query: str) -> str:
        """Lo que la memoria sepa del tema. Cadena vacía si no hay nada o falla."""
        if not getattr(self.brain, "available", False):
            return ""
        try:
            paquete = await self.brain.assemble_context(
                query, token_budget=MEMORY_TOKEN_BUDGET, include_graph=False
            )
        except Exception as exc:  # noqa: BLE001 - la memoria es un apoyo, no un requisito
            logger.debug("[Sesión] No se pudo recuperar contexto: %s", exc)
            return ""

        piezas = [s["content"] for s in paquete.get("semantic", []) if s.get("content")]
        if not piezas:
            return ""
        return "\n".join(f"- {p[:300]}" for p in piezas[:5])

    async def remember(self, session: AgentSession, contribution: Contribution) -> None:
        """Persiste una contribución para que sobreviva a la sesión."""
        if not getattr(self.brain, "available", False):
            return
        try:
            await self.brain.remember_event(
                f"[{session.goal[:80]}] {contribution.agent}: {contribution.content[:800]}",
                importance=0.6,
                tags=["session", session.session_id, contribution.agent],
                source="session_manager",
            )
        except Exception as exc:  # noqa: BLE001 - no poder recordar no debe romper la tarea
            logger.debug("[Sesión] No se pudo guardar la contribución: %s", exc)

    # -- composición -------------------------------------------------------
    async def compose_prompt(
        self, session: AgentSession, agent: str, instruction: str, *, use_memory: bool = True
    ) -> str:
        """Construye el prompt que verá el agente: instrucción + contexto compartido.

        Es la pieza que faltaba. Sin ella, cada CLI trabajaba a ciegas y la
        «coherencia entre sesiones» era una descripción, no un mecanismo.
        """
        partes = [f"SESIÓN: {session.session_id}", f"OBJETIVO GENERAL: {session.goal}"]

        recuerdos = await self.recall_context(session.goal) if use_memory else ""
        if recuerdos:
            partes.append(f"\nLO QUE YA SE SABE (memoria de largo plazo):\n{recuerdos}")

        compartido = session.shared_context(exclude_agent=agent)
        if compartido:
            partes.append(f"\nLO QUE HAN APORTADO LOS DEMÁS AGENTES:\n{compartido}")

        partes.append(f"\nTU TAREA ({agent}):\n{instruction}")
        return "\n".join(partes)

    async def run_with_context(
        self,
        session: AgentSession,
        agent: str,
        instruction: str,
        executor: Any,
        *,
        model: str = "",
        use_memory: bool = True,
    ) -> str:
        """Ejecuta una llamada dentro de la sesión: compone, invoca y registra.

        `executor` es cualquier coroutine que reciba un prompt y devuelva texto
        (el router, un adaptador de CLI…). El registro ocurre **sólo si la
        llamada tuvo éxito**: un fallo no se guarda como si fuera una aportación.
        """
        prompt = await self.compose_prompt(session, agent, instruction, use_memory=use_memory)
        respuesta = await executor(prompt)

        async with self._lock:
            contribucion = session.add(agent, respuesta, model=model)
        await self.remember(session, contribucion)

        logger.info(
            "[Sesión] %s · %s aportó %d caracteres", session.session_id, agent, len(respuesta)
        )
        return respuesta


# Instancia compartida por el servidor.
session_manager = SessionManager()
