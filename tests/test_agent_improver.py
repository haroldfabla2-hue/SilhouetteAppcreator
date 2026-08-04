"""Tests del motor de auto-mejora.

El fallo original: devolvía texto que decía haber ajustado el prompt, pero nada
persistía ni cambiaba. Estos tests comprueban que el ajuste es observable.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.evolution.agent_improver import (
    AgentImprover,
    AgentProfile,
    ProfileStore,
)
from backend.app.orchestrator.executive_supervisor import ExecutiveSupervisor


@pytest.fixture()
def store(tmp_path: Path) -> ProfileStore:
    return ProfileStore(tmp_path / "profiles.json")


@pytest.fixture()
def sup() -> ExecutiveSupervisor:
    return ExecutiveSupervisor()


@pytest.fixture()
def improver(store: ProfileStore, sup: ExecutiveSupervisor) -> AgentImprover:
    return AgentImprover(store=store, supervisor=sup)


def observar(sup: ExecutiveSupervisor, agente: str, exitos: int, fallos: int) -> None:
    for i in range(exitos):
        sup.record_task_start(f"{agente}-ok{i}", agente)
        sup.record_task_end(f"{agente}-ok{i}", success=True)
    for i in range(fallos):
        sup.record_task_start(f"{agente}-ko{i}", agente)
        sup.record_task_end(f"{agente}-ko{i}", success=False, error="x")


class TestElAjusteEsReal:
    async def test_baja_la_temperatura(self, improver: AgentImprover) -> None:
        antes = improver.get_profile("reasoner").temperature
        await improver.evaluate_and_improve_agent("reasoner", error_rate=0.5)
        assert improver.get_profile("reasoner").temperature < antes

    async def test_añade_una_directiva(self, improver: AgentImprover) -> None:
        await improver.evaluate_and_improve_agent("reasoner", error_rate=0.5)
        assert improver.get_profile("reasoner").directives

    async def test_la_directiva_llega_al_prompt(self, improver: AgentImprover) -> None:
        await improver.evaluate_and_improve_agent("reasoner", error_rate=0.5)
        sufijo = improver.get_profile("reasoner").system_suffix()
        assert "DIRECTIVAS DE CALIBRACIÓN" in sufijo
        assert "Verifica cada afirmación" in sufijo

    async def test_incrementa_la_revision_con_evidencia_nueva(
        self, improver: AgentImprover, sup: ExecutiveSupervisor
    ) -> None:
        observar(sup, "reasoner", exitos=0, fallos=10)
        await improver.evaluate_and_improve_agent("reasoner")
        # Hacen falta observaciones nuevas para justificar otro ajuste.
        observar(sup, "reasoner", exitos=0, fallos=10)
        await improver.evaluate_and_improve_agent("reasoner")
        assert improver.get_profile("reasoner").revision == 2

    async def test_con_error_muy_alto_da_un_reintento_mas(self, improver: AgentImprover) -> None:
        antes = improver.get_profile("planner").max_retries
        await improver.evaluate_and_improve_agent("planner", error_rate=0.6)
        assert improver.get_profile("planner").max_retries == antes + 1


class TestPersistencia:
    async def test_el_ajuste_sobrevive_al_reinicio(self, tmp_path: Path, sup: ExecutiveSupervisor) -> None:
        ruta = tmp_path / "profiles.json"
        await AgentImprover(store=ProfileStore(ruta), supervisor=sup).evaluate_and_improve_agent(
            "reasoner", error_rate=0.5
        )
        # Un proceso nuevo lee el mismo archivo.
        recargado = AgentImprover(store=ProfileStore(ruta), supervisor=sup)
        assert recargado.get_profile("reasoner").revision == 1
        assert recargado.get_profile("reasoner").directives

    async def test_se_guarda_el_historial_con_su_metrica(self, improver: AgentImprover) -> None:
        await improver.evaluate_and_improve_agent("reasoner", error_rate=0.45)
        historial = improver.history("reasoner")
        assert len(historial) == 1
        assert historial[0]["error_rate"] == 0.45
        assert "temperature" in historial[0]["changes"]

    async def test_revertir_restaura_el_perfil(self, improver: AgentImprover) -> None:
        await improver.evaluate_and_improve_agent("reasoner", error_rate=0.5)
        improver.revert("reasoner")
        perfil = improver.get_profile("reasoner")
        assert perfil.revision == 0
        assert perfil.directives == []


class TestNoInterviene:
    async def test_con_buen_rendimiento_no_toca_nada(self, improver: AgentImprover) -> None:
        resultado = await improver.evaluate_and_improve_agent("reasoner", error_rate=0.05)
        assert resultado["improved"] is False
        assert resultado["action"] == "rendimiento_optimo"
        assert improver.get_profile("reasoner").revision == 0

    async def test_sin_datos_lo_dice(self, improver: AgentImprover) -> None:
        resultado = await improver.evaluate_and_improve_agent("agente_sin_historial")
        assert resultado["improved"] is False
        assert resultado["action"] == "sin_datos"

    async def test_muestra_pequeña_no_justifica_ajuste(
        self, improver: AgentImprover, sup: ExecutiveSupervisor
    ) -> None:
        observar(sup, "reasoner", exitos=0, fallos=2)  # 100 % error, pero n=2
        resultado = await improver.evaluate_and_improve_agent("reasoner")
        assert resultado["action"] == "muestra_insuficiente"

    async def test_la_temperatura_no_baja_de_su_minimo(
        self, improver: AgentImprover, sup: ExecutiveSupervisor
    ) -> None:
        for _ in range(30):
            observar(sup, "reasoner", exitos=0, fallos=10)
            await improver.evaluate_and_improve_agent("reasoner")
        assert improver.get_profile("reasoner").temperature >= 0.05

    async def test_no_recalibra_sin_evidencia_nueva(
        self, improver: AgentImprover, sup: ExecutiveSupervisor
    ) -> None:
        """Sin observaciones nuevas no se puede saber si el ajuste anterior sirvió.

        Sin esta barrera, el bucle autónomo agotaba el margen de calibración de
        un agente en segundos, ajustándolo una y otra vez sobre los mismos datos.
        """
        observar(sup, "reasoner", exitos=0, fallos=10)
        primero = await improver.evaluate_and_improve_agent("reasoner")
        assert primero["improved"] is True

        segundo = await improver.evaluate_and_improve_agent("reasoner")
        assert segundo["improved"] is False
        assert segundo["action"] == "esperando_evidencia"
        assert improver.get_profile("reasoner").revision == 1


class TestUsaMetricasMedidas:
    async def test_toma_la_tasa_de_error_del_supervisor(
        self, improver: AgentImprover, sup: ExecutiveSupervisor
    ) -> None:
        observar(sup, "verifier", exitos=2, fallos=8)  # 80 % de error, n=10
        resultado = await improver.evaluate_and_improve_agent("verifier")
        assert resultado["improved"] is True
        assert resultado["error_rate"] == 0.8
        assert resultado["observations"] == 10


class TestPerfilPorDefecto:
    def test_un_perfil_nuevo_no_altera_el_prompt(self) -> None:
        assert AgentProfile(name="x").system_suffix() == ""
