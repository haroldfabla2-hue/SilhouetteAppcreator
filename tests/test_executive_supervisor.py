"""Tests del supervisor multi-equipo.

Antes devolvía puntuaciones constantes y `deadlock_detected: False` siempre.
Estos tests comprueban que las métricas responden a lo que ocurre.
"""
from __future__ import annotations

import pytest

from backend.app.orchestrator.executive_supervisor import ExecutiveSupervisor


@pytest.fixture()
def sup() -> ExecutiveSupervisor:
    return ExecutiveSupervisor(stall_threshold_s=0.05)


def registrar(sup: ExecutiveSupervisor, agente: str, exitos: int, fallos: int) -> None:
    for i in range(exitos):
        sup.record_task_start(f"{agente}-ok-{i}", agente)
        sup.record_task_end(f"{agente}-ok-{i}", success=True)
    for i in range(fallos):
        sup.record_task_start(f"{agente}-ko-{i}", agente)
        sup.record_task_end(f"{agente}-ko-{i}", success=False, error="fallo simulado")


class TestSinDatos:
    async def test_sin_observaciones_la_puntuacion_es_desconocida(self, sup: ExecutiveSupervisor) -> None:
        auditoria = await sup.audit_team_performance()
        # "sin datos" es None, no 0.98 inventado.
        assert all(t["performance_score"] is None for t in auditoria["teams"].values())
        assert auditoria["system_performance"] is None

    async def test_equipos_sin_trabajo_estan_idle(self, sup: ExecutiveSupervisor) -> None:
        auditoria = await sup.audit_team_performance()
        assert auditoria["teams"]["research"]["status"] == "idle"


class TestMetricasReales:
    async def test_la_puntuacion_refleja_los_resultados(self, sup: ExecutiveSupervisor) -> None:
        registrar(sup, "reasoner", exitos=8, fallos=2)
        auditoria = await sup.audit_team_performance()
        assert auditoria["teams"]["research"]["performance_score"] == 0.8

    async def test_la_puntuacion_cambia_al_cambiar_los_resultados(self, sup: ExecutiveSupervisor) -> None:
        registrar(sup, "reasoner", exitos=10, fallos=0)
        primera = (await sup.audit_team_performance())["teams"]["research"]["performance_score"]
        registrar(sup, "reasoner", exitos=0, fallos=10)
        segunda = (await sup.audit_team_performance())["teams"]["research"]["performance_score"]
        assert primera == 1.0
        assert segunda == 0.5
        assert primera != segunda

    async def test_equipo_con_mal_rendimiento_se_marca_degradado(self, sup: ExecutiveSupervisor) -> None:
        registrar(sup, "reasoner", exitos=5, fallos=5)
        auditoria = await sup.audit_team_performance()
        assert auditoria["teams"]["research"]["status"] == "degraded"

    async def test_la_tasa_de_error_por_agente_es_real(self, sup: ExecutiveSupervisor) -> None:
        registrar(sup, "planner", exitos=3, fallos=1)
        assert sup.agent_metrics("planner")["error_rate"] == 0.25

    async def test_registra_los_errores_recientes(self, sup: ExecutiveSupervisor) -> None:
        registrar(sup, "verifier", exitos=0, fallos=2)
        assert "fallo simulado" in sup.agent_metrics("verifier")["recent_errors"]


class TestDeteccionDeEstancamiento:
    async def test_detecta_una_tarea_estancada(self, sup: ExecutiveSupervisor) -> None:
        import time

        sup.record_task_start("colgada", "reasoner")
        time.sleep(0.06)  # supera el umbral de 0.05 s
        auditoria = await sup.audit_team_performance()
        assert auditoria["deadlock_detected"] is True
        assert auditoria["stalled_tasks"][0]["task_id"] == "colgada"

    async def test_una_tarea_rapida_no_es_estancamiento(self, sup: ExecutiveSupervisor) -> None:
        sup.record_task_start("rapida", "reasoner")
        sup.record_task_end("rapida", success=True)
        auditoria = await sup.audit_team_performance()
        assert auditoria["deadlock_detected"] is False

    async def test_resolver_libera_las_tareas(self, sup: ExecutiveSupervisor) -> None:
        import time

        sup.record_task_start("colgada", "reasoner")
        time.sleep(0.06)
        resultado = await sup.resolve_team_deadlock("research")
        assert resultado["success"] is True
        assert "colgada" in resultado["released_tasks"]
        assert (await sup.audit_team_performance())["deadlock_detected"] is False

    async def test_resolver_sin_estancamiento_no_finge(self, sup: ExecutiveSupervisor) -> None:
        resultado = await sup.resolve_team_deadlock("research")
        assert resultado["released_tasks"] == []
        assert "no se hizo nada" in resultado["message"]

    async def test_equipo_inexistente(self, sup: ExecutiveSupervisor) -> None:
        assert (await sup.resolve_team_deadlock("fantasma"))["success"] is False


class TestRegistroDeAgentes:
    async def test_un_agente_desconocido_se_registra_solo(self, sup: ExecutiveSupervisor) -> None:
        sup.record_task_start("t", "agente_nuevo")
        sup.record_task_end("t", success=True)
        assert sup.agent_metrics("agente_nuevo")["tasks_observed"] == 1

    async def test_cuenta_el_total_de_tareas(self, sup: ExecutiveSupervisor) -> None:
        registrar(sup, "reasoner", exitos=3, fallos=1)
        registrar(sup, "planner", exitos=2, fallos=0)
        assert (await sup.audit_team_performance())["total_tasks_observed"] == 6
