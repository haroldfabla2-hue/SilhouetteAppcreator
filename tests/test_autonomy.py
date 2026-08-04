"""Tests de la jerarquía dinámica y el bucle autónomo.

Cubre las tres piezas portadas de Silhouette Agency OS: derivación de objetivos
desde la telemetría, formación de equipos por diseño del modelo, y el ciclo que
las une sin intervención humana.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.app.evolution.agent_improver import AgentImprover, ProfileStore
from backend.app.evolution.evolution_scheduler import EvolutionConfig, EvolutionScheduler
from backend.app.evolution.introspection import (
    GoalStatus,
    IntrospectionEngine,
    Priority,
)
from backend.app.orchestrator.executive_supervisor import ExecutiveSupervisor
from backend.app.orchestrator.squad_factory import (
    SquadDesignError,
    SquadFactory,
    SquadFactoryUnavailable,
    Tier,
)

BLUEPRINT_VALIDO = json.dumps(
    {
        "name": "Equipo Alfa de Refactorización",
        "description": "Equipo para limpiar deuda técnica",
        "strategy": "Analizar, proponer, verificar",
        "members": [
            {
                "role_name": "Arquitecto de Refactor",
                "category": "CODE",
                "tier": "SPECIALIST",
                "focus": "Diseñar el plan de refactor",
                "is_leader": True,
            },
            {
                "role_name": "Ejecutor de Cambios",
                "category": "CODE",
                "tier": "WORKER",
                "focus": "Aplicar los cambios",
                "is_leader": False,
            },
            {
                "role_name": "Verificador de Regresión",
                "category": "QA",
                "tier": "WORKER",
                "focus": "Ejecutar la suite",
                "is_leader": False,
            },
        ],
    }
)


class RouterFalso:
    def __init__(self, respuesta: str = BLUEPRINT_VALIDO) -> None:
        self.respuesta = respuesta
        self.llamadas: list[str] = []

    async def chat_completion(self, prompt: str, **kwargs: object) -> str:
        self.llamadas.append(prompt)
        return self.respuesta


@pytest.fixture()
def sup() -> ExecutiveSupervisor:
    return ExecutiveSupervisor(stall_threshold_s=0.05)


@pytest.fixture()
def intro(sup: ExecutiveSupervisor, tmp_path: Path) -> IntrospectionEngine:
    return IntrospectionEngine(supervisor=sup, path=tmp_path / "goals.json")


def observar(sup: ExecutiveSupervisor, agente: str, exitos: int, fallos: int) -> None:
    for i in range(exitos):
        sup.record_task_start(f"{agente}-ok{i}", agente)
        sup.record_task_end(f"{agente}-ok{i}", success=True)
    for i in range(fallos):
        sup.record_task_start(f"{agente}-ko{i}", agente)
        sup.record_task_end(f"{agente}-ko{i}", success=False, error="fallo")


# ---------------------------------------------------------------------------
# Introspección: objetivos derivados de señales reales
# ---------------------------------------------------------------------------
class TestDerivacionDeObjetivos:
    async def test_sin_datos_no_deriva_nada(self, intro: IntrospectionEngine) -> None:
        assert await intro.derive_goals() == []

    async def test_una_muestra_pequeña_no_genera_objetivo(
        self, intro: IntrospectionEngine, sup: ExecutiveSupervisor
    ) -> None:
        observar(sup, "reasoner", exitos=0, fallos=2)  # 100 % error pero n=2
        assert await intro.derive_goals() == []

    async def test_un_agente_degradado_genera_objetivo(
        self, intro: IntrospectionEngine, sup: ExecutiveSupervisor
    ) -> None:
        observar(sup, "reasoner", exitos=2, fallos=8)  # 80 % error, n=10
        objetivos = await intro.derive_goals()
        assert objetivos
        assert any("reasoner" in g.description for g in objetivos)

    async def test_el_objetivo_guarda_la_evidencia(
        self, intro: IntrospectionEngine, sup: ExecutiveSupervisor
    ) -> None:
        observar(sup, "planner", exitos=1, fallos=9)
        objetivos = await intro.derive_goals()
        agente = next(g for g in objetivos if g.evidence.get("agent") == "planner")
        assert agente.evidence["error_rate"] == 0.9

    async def test_error_muy_alto_es_prioridad_alta(
        self, intro: IntrospectionEngine, sup: ExecutiveSupervisor
    ) -> None:
        observar(sup, "verifier", exitos=1, fallos=9)
        objetivos = await intro.derive_goals()
        agente = next(g for g in objetivos if g.evidence.get("agent") == "verifier")
        assert agente.priority == Priority.HIGH.value

    async def test_un_estancamiento_genera_objetivo_urgente(
        self, intro: IntrospectionEngine, sup: ExecutiveSupervisor
    ) -> None:
        import time

        sup.record_task_start("colgada", "reasoner")
        time.sleep(0.06)
        objetivos = await intro.derive_goals()
        assert any(g.source == "introspection:stall" for g in objetivos)
        assert all(
            g.priority == Priority.HIGH.value
            for g in objetivos
            if g.source == "introspection:stall"
        )

    async def test_no_duplica_objetivos_iguales(
        self, intro: IntrospectionEngine, sup: ExecutiveSupervisor
    ) -> None:
        observar(sup, "reasoner", exitos=2, fallos=8)
        await intro.derive_goals()
        antes = len(intro.active_goals())
        await intro.derive_goals()
        assert len(intro.active_goals()) == antes


class TestGestionDeObjetivos:
    def test_prioriza_los_altos(self, intro: IntrospectionEngine) -> None:
        intro.add_goal("bajo", Priority.LOW.value)
        alto = intro.add_goal("alto", Priority.HIGH.value)
        assert intro.get_high_priority_goal().id == alto.id

    def test_completar_al_llegar_a_uno(self, intro: IntrospectionEngine) -> None:
        goal = intro.add_goal("algo")
        intro.update_goal_progress(goal.id, 1.0)
        assert intro.all_goals()[0]["status"] == GoalStatus.COMPLETED.value

    def test_los_completados_salen_de_los_activos(self, intro: IntrospectionEngine) -> None:
        goal = intro.add_goal("algo")
        intro.update_goal_progress(goal.id, 1.0)
        assert intro.active_goals() == []

    def test_persisten_entre_reinicios(self, sup: ExecutiveSupervisor, tmp_path: Path) -> None:
        ruta = tmp_path / "goals.json"
        IntrospectionEngine(supervisor=sup, path=ruta).add_goal("sobrevive", Priority.HIGH.value)
        recargado = IntrospectionEngine(supervisor=sup, path=ruta)
        assert recargado.get_high_priority_goal().description == "sobrevive"


# ---------------------------------------------------------------------------
# SquadFactory: el organigrama lo diseña el modelo
# ---------------------------------------------------------------------------
class TestFormacionDeEquipos:
    async def test_sin_router_falla_en_cerrado(self, sup: ExecutiveSupervisor) -> None:
        with pytest.raises(SquadFactoryUnavailable):
            await SquadFactory(None, supervisor=sup).spawn_squad("objetivo")

    async def test_forma_un_equipo_con_los_roles_diseñados(
        self, sup: ExecutiveSupervisor
    ) -> None:
        squad = await SquadFactory(RouterFalso(), supervisor=sup).spawn_squad("Refactorizar")
        assert squad.name == "Equipo Alfa de Refactorización"
        assert len(squad.members) == 3
        assert {m.role_name for m in squad.members} == {
            "Arquitecto de Refactor",
            "Ejecutor de Cambios",
            "Verificador de Regresión",
        }

    async def test_hay_exactamente_un_lider(self, sup: ExecutiveSupervisor) -> None:
        squad = await SquadFactory(RouterFalso(), supervisor=sup).spawn_squad("x")
        assert sum(1 for m in squad.members if m.is_leader) == 1
        assert squad.leader.role_name == "Arquitecto de Refactor"

    async def test_el_objetivo_llega_al_modelo(self, sup: ExecutiveSupervisor) -> None:
        router = RouterFalso()
        await SquadFactory(router, supervisor=sup).spawn_squad("Migrar la base de datos")
        assert "Migrar la base de datos" in router.llamadas[0]

    async def test_el_equipo_se_registra_en_el_supervisor(
        self, sup: ExecutiveSupervisor
    ) -> None:
        squad = await SquadFactory(RouterFalso(), supervisor=sup).spawn_squad("x")
        assert squad.id in sup.teams
        for agent_id in squad.agent_ids:
            assert sup.agent_metrics(agent_id) is not None

    async def test_recluta_en_vez_de_duplicar(self, sup: ExecutiveSupervisor) -> None:
        # `reasoner` ya existe en la jerarquía por defecto.
        blueprint = json.dumps(
            {
                "name": "Equipo",
                "description": "",
                "strategy": "",
                "members": [
                    {
                        "role_name": "reasoner",
                        "category": "RESEARCH",
                        "tier": "SPECIALIST",
                        "focus": "razonar",
                        "is_leader": True,
                    }
                ],
            }
        )
        squad = await SquadFactory(RouterFalso(blueprint), supervisor=sup).spawn_squad("x")
        assert squad.members[0].recruited is True
        assert squad.members[0].agent_id == "reasoner"

    async def test_el_presupuesto_limita_el_tamaño(self, sup: ExecutiveSupervisor) -> None:
        squad = await SquadFactory(RouterFalso(), supervisor=sup).spawn_squad("x", budget="ECO")
        assert len(squad.members) <= 3

    async def test_json_invalido_se_reporta(self, sup: ExecutiveSupervisor) -> None:
        with pytest.raises(SquadDesignError):
            await SquadFactory(RouterFalso("no soy json"), supervisor=sup).spawn_squad("x")

    async def test_corrige_si_el_modelo_marca_varios_lideres(
        self, sup: ExecutiveSupervisor
    ) -> None:
        blueprint = json.dumps(
            {
                "name": "E",
                "description": "",
                "strategy": "",
                "members": [
                    {"role_name": "A", "category": "CODE", "tier": "CORE", "focus": "a", "is_leader": True},
                    {"role_name": "B", "category": "CODE", "tier": "CORE", "focus": "b", "is_leader": True},
                ],
            }
        )
        squad = await SquadFactory(RouterFalso(blueprint), supervisor=sup).spawn_squad("x")
        assert sum(1 for m in squad.members if m.is_leader) == 1
        # Sólo se admite un CORE por equipo.
        assert sum(1 for m in squad.members if m.tier == Tier.CORE.value) == 1

    async def test_disolver_retira_el_equipo(self, sup: ExecutiveSupervisor) -> None:
        factory = SquadFactory(RouterFalso(), supervisor=sup)
        squad = await factory.spawn_squad("x")
        assert factory.disband(squad.id) is True
        assert squad.id not in sup.teams


# ---------------------------------------------------------------------------
# El bucle autónomo
# ---------------------------------------------------------------------------
@pytest.fixture()
def scheduler(sup: ExecutiveSupervisor, tmp_path: Path) -> EvolutionScheduler:
    return EvolutionScheduler(
        introspection=IntrospectionEngine(supervisor=sup, path=tmp_path / "goals.json"),
        improver=AgentImprover(store=ProfileStore(tmp_path / "profiles.json"), supervisor=sup),
        squad_factory=SquadFactory(RouterFalso(), supervisor=sup),
        supervisor=sup,
        config=EvolutionConfig(
            introspection_interval_s=0.01,
            calibration_interval_s=0.01,
            goal_interval_s=0.01,
        ),
    )


class TestBucleAutonomo:
    async def test_el_ciclo_deriva_objetivos_solo(
        self, scheduler: EvolutionScheduler, sup: ExecutiveSupervisor
    ) -> None:
        observar(sup, "reasoner", exitos=2, fallos=8)
        registro = await scheduler.run_introspection_cycle()
        assert registro.goals_derived > 0

    async def test_el_ciclo_recalibra_agentes_solo(
        self, scheduler: EvolutionScheduler, sup: ExecutiveSupervisor
    ) -> None:
        observar(sup, "reasoner", exitos=2, fallos=8)
        registro = await scheduler.run_calibration_cycle()
        assert "reasoner" in registro.agents_calibrated

    async def test_el_ciclo_forma_equipos_para_sus_objetivos(
        self, scheduler: EvolutionScheduler, sup: ExecutiveSupervisor
    ) -> None:
        observar(sup, "reasoner", exitos=2, fallos=8)
        await scheduler.run_introspection_cycle()
        registro = await scheduler.run_goal_cycle()
        assert registro.squads_spawned, "el bucle debe formar un equipo para el objetivo"

    async def test_ciclo_completo_encadenado(
        self, scheduler: EvolutionScheduler, sup: ExecutiveSupervisor
    ) -> None:
        observar(sup, "planner", exitos=1, fallos=9)
        resultado = await scheduler.trigger_now()
        assert resultado["introspection"]["goals_derived"] > 0
        assert resultado["calibration"]["agents_calibrated"]
        assert resultado["goal_execution"]["squads_spawned"]

    async def test_sin_señal_no_hace_nada(self, scheduler: EvolutionScheduler) -> None:
        resultado = await scheduler.trigger_now()
        assert resultado["introspection"]["goals_derived"] == 0
        assert resultado["goal_execution"]["squads_spawned"] == []

    async def test_respeta_el_limite_de_evoluciones_simultaneas(
        self, scheduler: EvolutionScheduler, sup: ExecutiveSupervisor
    ) -> None:
        observar(sup, "reasoner", exitos=2, fallos=8)
        await scheduler.run_introspection_cycle()
        scheduler._active_evolutions = scheduler.config.max_concurrent_evolutions
        registro = await scheduler.run_goal_cycle()
        assert registro.squads_spawned == []

    async def test_el_objetivo_se_cierra_cuando_la_metrica_mejora(
        self, scheduler: EvolutionScheduler, sup: ExecutiveSupervisor
    ) -> None:
        observar(sup, "reasoner", exitos=2, fallos=8)  # 80 % error
        await scheduler.run_introspection_cycle()
        objetivo = next(
            g for g in scheduler.introspection.active_goals() if g.evidence.get("agent") == "reasoner"
        )
        scheduler.introspection.update_goal_progress(objetivo.id, 0.5)

        # El agente mejora de verdad: 100 éxitos desplazan la ventana móvil.
        observar(sup, "reasoner", exitos=100, fallos=0)
        cerrados = await scheduler._close_resolved_goals()
        assert objetivo.id in cerrados

    async def test_un_objetivo_no_se_cierra_sin_mejora(
        self, scheduler: EvolutionScheduler, sup: ExecutiveSupervisor
    ) -> None:
        observar(sup, "reasoner", exitos=2, fallos=8)
        await scheduler.run_introspection_cycle()
        objetivo = next(
            g for g in scheduler.introspection.active_goals() if g.evidence.get("agent") == "reasoner"
        )
        scheduler.introspection.update_goal_progress(objetivo.id, 0.5)
        assert await scheduler._close_resolved_goals() == []


class TestControlDelBucle:
    async def test_arranca_y_para(self, scheduler: EvolutionScheduler) -> None:
        assert scheduler.is_running is False
        scheduler.start()
        assert scheduler.is_running is True
        await scheduler.stop()
        assert scheduler.is_running is False

    async def test_arrancar_dos_veces_es_inocuo(self, scheduler: EvolutionScheduler) -> None:
        scheduler.start()
        scheduler.start()
        assert len(scheduler._tasks) == 3
        await scheduler.stop()

    async def test_el_bucle_ejecuta_ciclos_de_verdad(
        self, scheduler: EvolutionScheduler, sup: ExecutiveSupervisor
    ) -> None:
        import asyncio

        observar(sup, "reasoner", exitos=2, fallos=8)
        scheduler.start()
        await asyncio.sleep(0.1)  # los intervalos son de 0.01 s
        await scheduler.stop()
        assert len(scheduler._cycles) > 0, "el bucle debe haber ejecutado ciclos solo"

    async def test_el_estado_expone_los_ciclos(
        self, scheduler: EvolutionScheduler, sup: ExecutiveSupervisor
    ) -> None:
        observar(sup, "reasoner", exitos=2, fallos=8)
        await scheduler.trigger_now()
        estado = scheduler.status()
        assert estado["cycles_recorded"] >= 3
        assert estado["goals"]["active"] > 0
