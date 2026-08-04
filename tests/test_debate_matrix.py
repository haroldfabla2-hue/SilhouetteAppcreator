"""Tests de la matriz de debate.

El objetivo central: comprobar que el debate **usa** el router. La versión
anterior lo aceptaba y lo ignoraba.
"""
from __future__ import annotations

import pytest

from backend.app.swarm.debate_matrix import (
    DebateSwarmMatrix,
)

JUDGE_RESPONSE = """VEREDICTO: APROBADO
PUNTUACION: 0.82
JUSTIFICACION: La crítica sobre el manejo de errores era fundada y se incorporó.
SOLUCION_FINAL:
def dividir(a, b):
    if b == 0:
        raise ValueError("división por cero")
    return a / b
"""


class RouterFalso:
    """Router de prueba que registra cada llamada."""

    def __init__(self, respuestas: list[str] | None = None) -> None:
        self.llamadas: list[str] = []
        self.respuestas = respuestas or ["propuesta", "crítica", JUDGE_RESPONSE]

    async def chat_completion(self, prompt: str, **kwargs: object) -> str:
        self.llamadas.append(prompt)
        idx = min(len(self.llamadas) - 1, len(self.respuestas) - 1)
        return self.respuestas[idx]


class RouterQueFalla:
    def __init__(self, fallar_en: int) -> None:
        self.fallar_en = fallar_en
        self.llamadas = 0

    async def chat_completion(self, prompt: str, **kwargs: object) -> str:
        self.llamadas += 1
        if self.llamadas == self.fallar_en:
            raise RuntimeError("el proveedor no respondió")
        return "respuesta"


class TestUsaElRouter:
    async def test_llama_al_router_tres_veces(self) -> None:
        router = RouterFalso()
        await DebateSwarmMatrix(router).execute_debate_round("Escribe una función de división")
        assert len(router.llamadas) == 3, "creador, crítico y juez deben ser llamadas reales"

    async def test_cada_rol_recibe_su_prompt_de_sistema(self) -> None:
        router = RouterFalso()
        await DebateSwarmMatrix(router).execute_debate_round("problema")
        creador, critico, juez = router.llamadas
        assert "AGENTE CREADOR" in creador
        assert "AGENTE CRÍTICO" in critico
        assert "AGENTE JUEZ" in juez

    async def test_el_critico_ve_la_propuesta(self) -> None:
        router = RouterFalso(["mi propuesta única", "crítica", JUDGE_RESPONSE])
        await DebateSwarmMatrix(router).execute_debate_round("problema")
        assert "mi propuesta única" in router.llamadas[1]

    async def test_el_juez_ve_propuesta_y_critica(self) -> None:
        router = RouterFalso(["PROPUESTA-X", "CRITICA-Y", JUDGE_RESPONSE])
        await DebateSwarmMatrix(router).execute_debate_round("problema")
        assert "PROPUESTA-X" in router.llamadas[2]
        assert "CRITICA-Y" in router.llamadas[2]

    async def test_sin_router_falla_en_cerrado(self) -> None:
        resultado = await DebateSwarmMatrix(None).execute_debate_round("problema")
        assert resultado["debate_executed"] is False
        assert resultado["errors"]


class TestVeredicto:
    async def test_extrae_el_veredicto_del_modelo(self) -> None:
        resultado = await DebateSwarmMatrix(RouterFalso()).execute_debate_round("p")
        veredicto = resultado["judge_verdict"]
        assert veredicto["status"] == "APROBADO"
        assert veredicto["approved"] is True
        assert veredicto["quality_score"] == 0.82
        assert "división por cero" in veredicto["final_answer"]

    async def test_la_puntuacion_no_es_constante(self) -> None:
        # El fallo original: quality_score siempre 0.97.
        a = await DebateSwarmMatrix(
            RouterFalso(["p", "c", "VEREDICTO: APROBADO\nPUNTUACION: 0.30\nSOLUCION_FINAL:\nx"])
        ).execute_debate_round("p")
        b = await DebateSwarmMatrix(
            RouterFalso(["p", "c", "VEREDICTO: APROBADO\nPUNTUACION: 0.90\nSOLUCION_FINAL:\ny"])
        ).execute_debate_round("p")
        assert a["judge_verdict"]["quality_score"] == 0.30
        assert b["judge_verdict"]["quality_score"] == 0.90

    async def test_rechazo_se_refleja(self) -> None:
        resultado = await DebateSwarmMatrix(
            RouterFalso(["p", "c", "VEREDICTO: RECHAZADO\nPUNTUACION: 0.1\nSOLUCION_FINAL:\nz"])
        ).execute_debate_round("p")
        assert resultado["judge_verdict"]["approved"] is False

    async def test_formato_invalido_no_inventa_puntuacion(self) -> None:
        resultado = await DebateSwarmMatrix(
            RouterFalso(["p", "c", "texto libre sin formato"])
        ).execute_debate_round("p")
        assert resultado["judge_verdict"]["quality_score"] == 0.0
        assert resultado["judge_verdict"]["final_answer"] == "texto libre sin formato"

    @pytest.mark.parametrize("puntuacion,esperado", [("1.5", 1.0), ("-0.2", 0.0), ("0,75", 0.75)])
    async def test_la_puntuacion_se_acota(self, puntuacion: str, esperado: float) -> None:
        resultado = await DebateSwarmMatrix(
            RouterFalso(["p", "c", f"VEREDICTO: APROBADO\nPUNTUACION: {puntuacion}\nSOLUCION_FINAL:\nx"])
        ).execute_debate_round("p")
        assert resultado["judge_verdict"]["quality_score"] == esperado


class TestPropagacionDeFallos:
    @pytest.mark.parametrize("rol,posicion", [("creator", 1), ("critic", 2), ("judge", 3)])
    async def test_el_fallo_de_un_rol_se_reporta(self, rol: str, posicion: int) -> None:
        resultado = await DebateSwarmMatrix(RouterQueFalla(posicion)).execute_debate_round("p")
        assert resultado["debate_executed"] is False
        assert any(rol in e for e in resultado["errors"])
