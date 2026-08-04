"""Formación dinámica de equipos de agentes.

Portado del `SquadFactory` de Silhouette Agency OS
(https://github.com/haroldfabla2-hue/Silhouette-Agency-OS-OpenSource).

La diferencia con la jerarquía estática de `ExecutiveSupervisor` (3 equipos
fijos) es que aquí **la composición del equipo la diseña un modelo a partir del
objetivo**: qué roles hacen falta, en qué nivel, y quién lidera.

El ciclo es el del original:

    objetivo -> el LLM diseña el organigrama -> por cada rol:
        1. RECLUTAR un agente existente que ya encaje (evita duplicados)
        2. si no hay, CREAR uno nuevo con su instrucción de sistema
    -> registrar el equipo en el supervisor para que su telemetría se mida

El reclutamiento usa la memoria semántica de `silhouette-brain` cuando está
disponible. Sin router de modelos no se puede diseñar nada, así que la fábrica
falla en cerrado en lugar de devolver un equipo inventado.
"""
from __future__ import annotations

import json
import logging
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("SquadFactory")


class Tier(str, Enum):
    """Nivel del agente dentro del equipo."""

    CORE = "CORE"           # Crítico, siempre activo. Máximo 1 por equipo.
    SPECIALIST = "SPECIALIST"  # Experto, alta capacidad. Roles clave.
    WORKER = "WORKER"       # Ejecución, orientado a tarea.


class Category(str, Enum):
    CODE = "CODE"
    RESEARCH = "RESEARCH"
    DATA = "DATA"
    CREATIVE = "CREATIVE"
    WORKFLOW = "WORKFLOW"
    QA = "QA"
    SECURITY = "SECURITY"
    CORE = "CORE"


class Budget(str, Enum):
    ECO = "ECO"
    BALANCED = "BALANCED"
    HIGH = "HIGH"


# Cuántos miembros admite cada presupuesto.
BUDGET_LIMITS = {Budget.ECO: 3, Budget.BALANCED: 5, Budget.HIGH: 8}

DESIGN_SYSTEM_PROMPT = """ROL: Arquitecto organizativo de equipos de agentes de IA.
TAREA: Diseñar el equipo mínimo suficiente para alcanzar un objetivo.

NIVELES DISPONIBLES:
- CORE: crítico, siempre activo. Como máximo 1.
- SPECIALIST: experto en un dominio. Para los roles clave.
- WORKER: ejecución orientada a tarea. Para el grueso del trabajo.

CATEGORÍAS: CODE, RESEARCH, DATA, CREATIVE, WORKFLOW, QA, SECURITY, CORE

INSTRUCCIONES:
1. Define un nombre para el equipo.
2. Define la estrategia de ejecución en una frase.
3. Descompón el objetivo en {min_members}-{max_members} roles distintos y no solapados.
4. Exactamente un miembro debe ser el líder (nivel CORE o SPECIALIST).

Responde ÚNICAMENTE con este JSON, sin texto alrededor:
{{
  "name": "Nombre del equipo",
  "description": "Descripción breve",
  "strategy": "Estrategia de ejecución",
  "members": [
    {{
      "role_name": "Título específico del rol",
      "category": "UNA_DE_LAS_CATEGORIAS",
      "tier": "CORE|SPECIALIST|WORKER",
      "focus": "Responsabilidad principal",
      "is_leader": true
    }}
  ]
}}"""


class SquadDesignError(RuntimeError):
    """No se pudo diseñar el equipo."""


class SquadFactoryUnavailable(RuntimeError):
    """No hay router de modelos para diseñar equipos."""


@dataclass
class SquadMember:
    role_name: str
    category: str
    tier: str
    focus: str
    agent_id: str
    is_leader: bool = False
    recruited: bool = False  # True si se reutilizó un agente existente
    system_instruction: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Squad:
    id: str
    name: str
    goal: str
    description: str
    strategy: str
    members: list[SquadMember] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    @property
    def leader(self) -> SquadMember | None:
        return next((m for m in self.members if m.is_leader), None)

    @property
    def agent_ids(self) -> list[str]:
        return [m.agent_id for m in self.members]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "goal": self.goal,
            "description": self.description,
            "strategy": self.strategy,
            "leader_id": self.leader.agent_id if self.leader else None,
            "members": [m.to_dict() for m in self.members],
            "recruited_count": sum(1 for m in self.members if m.recruited),
            "spawned_count": sum(1 for m in self.members if not m.recruited),
            "created_at": self.created_at,
        }


class SquadFactory:
    """Diseña y materializa equipos de agentes para un objetivo concreto."""

    def __init__(
        self,
        llm_router: Any = None,
        supervisor: Any = None,
        brain: Any = None,
    ) -> None:
        self.llm_router = llm_router
        if supervisor is None:
            from backend.app.orchestrator.executive_supervisor import (
                supervisor as default_supervisor,
            )

            supervisor = default_supervisor
        self.supervisor = supervisor
        self.brain = brain
        self._squads: dict[str, Squad] = {}

    # -- diseño ------------------------------------------------------------
    async def design_squad(
        self, goal: str, *, budget: str = Budget.BALANCED.value, context: str = ""
    ) -> dict[str, Any]:
        """Pide al modelo el organigrama del equipo y lo valida."""
        if self.llm_router is None:
            raise SquadFactoryUnavailable(
                "SquadFactory necesita un LLMRouter para diseñar equipos."
            )

        max_members = BUDGET_LIMITS.get(Budget(budget), 5)
        prompt = DESIGN_SYSTEM_PROMPT.format(
            min_members=min(3, max_members), max_members=max_members
        )
        user = f"OBJETIVO: {goal}\nCONTEXTO: {context or 'Tarea general'}\nPRESUPUESTO: {budget}"

        raw = await self.llm_router.chat_completion(f"{prompt}\n\n---\n\n{user}", temperature=0.3)
        blueprint = self._parse_blueprint(raw)
        return self._validate_blueprint(blueprint, max_members)

    @staticmethod
    def _parse_blueprint(raw: str) -> dict[str, Any]:
        """Extrae el JSON de la respuesta, tolerando vallas de código."""
        texto = re.sub(r"```(?:json)?", "", raw).strip()
        match = re.search(r"\{.*\}", texto, re.DOTALL)
        if not match:
            raise SquadDesignError(
                f"El modelo no devolvió JSON con el organigrama. Respuesta: {raw[:200]}"
            )
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise SquadDesignError(f"El organigrama no es JSON válido: {exc}") from exc

    @staticmethod
    def _validate_blueprint(blueprint: dict[str, Any], max_members: int) -> dict[str, Any]:
        """Normaliza el diseño y aplica los límites del presupuesto."""
        miembros = blueprint.get("members") or []
        if not miembros:
            raise SquadDesignError("El organigrama no define ningún miembro.")

        normalizados: list[dict[str, Any]] = []
        for m in miembros[:max_members]:
            tier = str(m.get("tier", "")).upper()
            categoria = str(m.get("category", "")).upper()
            normalizados.append(
                {
                    "role_name": str(m.get("role_name") or m.get("roleName") or "Rol sin nombre"),
                    "category": categoria if categoria in Category.__members__ else Category.WORKFLOW.value,
                    "tier": tier if tier in Tier.__members__ else Tier.WORKER.value,
                    "focus": str(m.get("focus", "")),
                    "is_leader": bool(m.get("is_leader") or m.get("isLeader")),
                }
            )

        # Como máximo un CORE, como exige el diseño original.
        cores = [m for m in normalizados if m["tier"] == Tier.CORE.value]
        for extra in cores[1:]:
            extra["tier"] = Tier.SPECIALIST.value

        # Exactamente un líder: si el modelo marcó varios o ninguno, se corrige.
        lideres = [m for m in normalizados if m["is_leader"]]
        if len(lideres) != 1:
            for m in normalizados:
                m["is_leader"] = False
            elegido = next(
                (m for m in normalizados if m["tier"] == Tier.CORE.value),
                next(
                    (m for m in normalizados if m["tier"] == Tier.SPECIALIST.value),
                    normalizados[0],
                ),
            )
            elegido["is_leader"] = True

        blueprint["members"] = normalizados
        blueprint.setdefault("name", "Equipo sin nombre")
        blueprint.setdefault("description", "")
        blueprint.setdefault("strategy", "")
        return blueprint

    # -- reclutamiento -----------------------------------------------------
    async def _recruit(self, role_name: str, focus: str) -> str | None:
        """Busca un agente ya existente que encaje en el rol.

        Evita crear un agente nuevo para algo que el sistema ya sabe hacer, que
        es el propósito de la fase de reclutamiento del diseño original.
        """
        existentes = self.supervisor.all_agent_metrics()
        if not existentes:
            return None

        # Coincidencia directa por nombre de rol.
        objetivo = role_name.lower().replace(" ", "_")
        for nombre in existentes:
            if nombre.lower() == objetivo or objetivo in nombre.lower():
                return nombre

        # Coincidencia semántica sobre la memoria, si está disponible.
        if self.brain is not None and getattr(self.brain, "available", False):
            try:
                resultado = await self.brain.recall(
                    f"agente especializado en {role_name}: {focus}", limit=3, min_score=0.35
                )
                for item in resultado.get("results", []):
                    for nombre in existentes:
                        if nombre.lower() in item["content"].lower():
                            return nombre
            except Exception as exc:  # noqa: BLE001 - el reclutamiento es opcional
                logger.debug("Reclutamiento semántico no disponible: %s", exc)
        return None

    # -- materialización ---------------------------------------------------
    async def spawn_squad(
        self, goal: str, *, budget: str = Budget.BALANCED.value, context: str = ""
    ) -> Squad:
        """Diseña el equipo y lo materializa, reclutando o creando cada rol."""
        logger.info("[SquadFactory] Diseñando equipo para: %s", goal[:70])
        blueprint = await self.design_squad(goal, budget=budget, context=context)

        squad_id = f"SQ_{uuid.uuid4().hex[:8]}"
        miembros: list[SquadMember] = []

        for bp in blueprint["members"]:
            reclutado = await self._recruit(bp["role_name"], bp["focus"])
            if reclutado:
                agent_id = reclutado
                logger.info("[SquadFactory] Reclutado agente existente: %s", agent_id)
            else:
                agent_id = f"{squad_id}_{bp['role_name'].lower().replace(' ', '_')[:24]}"
                logger.info("[SquadFactory] Agente nuevo: %s", agent_id)

            miembros.append(
                SquadMember(
                    role_name=bp["role_name"],
                    category=bp["category"],
                    tier=bp["tier"],
                    focus=bp["focus"],
                    agent_id=agent_id,
                    is_leader=bp["is_leader"],
                    recruited=bool(reclutado),
                    system_instruction=self._build_instruction(blueprint, bp),
                )
            )

        squad = Squad(
            id=squad_id,
            name=blueprint["name"],
            goal=goal,
            description=blueprint["description"],
            strategy=blueprint["strategy"],
            members=miembros,
        )
        self._squads[squad_id] = squad
        self._register_with_supervisor(squad)

        # El equipo queda en la memoria para que futuros reclutamientos lo vean.
        if self.brain is not None and getattr(self.brain, "available", False):
            try:
                await self.brain.remember_event(
                    f"Equipo '{squad.name}' formado para: {goal}. "
                    f"Miembros: {', '.join(m.role_name for m in miembros)}.",
                    importance=0.7,
                    tags=["squad", squad_id],
                    source="squad_factory",
                )
            except Exception as exc:  # noqa: BLE001 - la memoria es opcional
                logger.debug("No se pudo memorizar el equipo: %s", exc)

        logger.info(
            "[SquadFactory] Equipo '%s' formado: %d miembro(s), líder %s",
            squad.name,
            len(miembros),
            squad.leader.agent_id if squad.leader else "ninguno",
        )
        return squad

    def _register_with_supervisor(self, squad: Squad) -> None:
        """Da de alta el equipo en el supervisor para que se mida su telemetría."""
        from backend.app.orchestrator.executive_supervisor import Team

        self.supervisor.teams[squad.id] = Team(
            team_id=squad.id, name=squad.name, agents=squad.agent_ids
        )
        for miembro in squad.members:
            self.supervisor._ensure_agent(miembro.agent_id)  # noqa: SLF001 - alta explícita

    @staticmethod
    def _build_instruction(blueprint: dict[str, Any], member: dict[str, Any]) -> str:
        return (
            f"Eres '{member['role_name']}', miembro del equipo '{blueprint['name']}'.\n"
            f"Nivel: {member['tier']}. Categoría: {member['category']}.\n"
            f"Tu responsabilidad: {member['focus']}.\n"
            f"Estrategia del equipo: {blueprint['strategy']}"
        )

    # -- consulta ----------------------------------------------------------
    def get_squad(self, squad_id: str) -> Squad | None:
        return self._squads.get(squad_id)

    def all_squads(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self._squads.values()]

    def disband(self, squad_id: str) -> bool:
        """Disuelve un equipo y lo retira del supervisor."""
        squad = self._squads.pop(squad_id, None)
        if squad is None:
            return False
        self.supervisor.teams.pop(squad_id, None)
        logger.info("[SquadFactory] Equipo '%s' disuelto", squad.name)
        return True
