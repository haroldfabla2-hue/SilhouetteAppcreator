"""Tests de la regla «un fallo debe parecer un fallo».

Todos los casos aquí devolvían antes `success: True` con datos inventados. Son
la misma clase de defecto que el `CLIExecutor` del router: una capacidad ausente
se reportaba hacia arriba como trabajo hecho.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.agents.executor import ExecutorAgent
from backend.app.agents.verifier import VerifierAgent


@pytest.fixture()
def executor() -> ExecutorAgent:
    return ExecutorAgent("general", llm_client=None)


@pytest.fixture()
def verifier() -> VerifierAgent:
    return VerifierAgent(llm_client=None)


class TestHerramientasAusentes:
    async def test_sin_buscador_no_declara_busqueda(self, executor: ExecutorAgent) -> None:
        executor.tools = {}
        r = await executor._tool_search_engine("clima en Madrid", {})
        assert r["success"] is False
        assert r["searched"] is False
        assert r["data"] == {}
        assert "no está disponible" in r["error"]

    async def test_sin_buscador_no_inventa_resultados(self, executor: ExecutorAgent) -> None:
        executor.tools = {}
        r = await executor._tool_search_engine("cualquier cosa", {})
        assert "mock_search" not in str(r)
        assert "simulad" not in str(r).lower()

    async def test_sin_procesador_no_inventa_contenido(self, executor: ExecutorAgent) -> None:
        executor.tools = {}
        r = await executor._tool_file_processor("procesa informe.txt", {})
        assert r["success"] is False
        assert r["extracted_text"] == ""
        assert r["files_processed"] == 0


class TestExitoDelegado:
    async def test_una_herramienta_fallida_no_se_reporta_como_exito(
        self, executor: ExecutorAgent
    ) -> None:
        async def herramienta_fallida(objetivo: str, limites: dict) -> dict:
            return {"success": False, "error": "el servicio no respondió"}

        executor.tools = {}
        executor.tools_registry = {"fake": herramienta_fallida}
        r = await executor._execute_single_tool("fake", "objetivo", {})
        assert r["success"] is False
        assert r["error"] == "el servicio no respondió"

    async def test_una_herramienta_correcta_se_reporta_como_exito(
        self, executor: ExecutorAgent
    ) -> None:
        async def herramienta_ok(objetivo: str, limites: dict) -> dict:
            return {"success": True, "data": {"x": 1}}

        executor.tools = {}
        executor.tools_registry = {"fake": herramienta_ok}
        r = await executor._execute_single_tool("fake", "objetivo", {})
        assert r["success"] is True


class TestPdfReal:
    async def test_archivo_inexistente_se_reporta(self, executor: ExecutorAgent) -> None:
        texto = await executor._process_pdf_file("no_existe_12345.pdf")
        assert "no se encontró" in texto.lower() or "error" in texto.lower()

    async def test_no_devuelve_marcador_de_posicion(self, executor: ExecutorAgent) -> None:
        texto = await executor._process_pdf_file("no_existe_12345.pdf")
        assert "[PDF content for" not in texto

    async def test_extrae_texto_de_un_pdf_real(
        self, executor: ExecutorAgent, tmp_path: Path
    ) -> None:
        pytest.importorskip("reportlab", reason="reportlab no instalado")
        from reportlab.pdfgen import canvas

        ruta = tmp_path / "prueba.pdf"
        c = canvas.Canvas(str(ruta))
        c.drawString(100, 750, "El orquestador coordina cinco agentes")
        c.save()

        texto = await executor._process_pdf_file(str(ruta))
        assert "orquestador" in texto.lower()


class TestConsistenciaDelVerificador:
    def test_detecta_paso_done_con_success_false(self, verifier: VerifierAgent) -> None:
        r = verifier._check_consistency(
            {"steps": [{"id": "s1", "status": "DONE", "success": False}]}
        )
        assert r["checks"]["no_contradictions"] is False
        assert r["contradictions"]

    def test_detecta_paso_fallido_con_success_true(self, verifier: VerifierAgent) -> None:
        r = verifier._check_consistency(
            {"steps": [{"id": "s1", "status": "FAILED", "success": True}]}
        )
        assert r["checks"]["no_contradictions"] is False

    def test_detecta_exito_global_con_pasos_fallidos(self, verifier: VerifierAgent) -> None:
        r = verifier._check_consistency(
            {"success": True, "steps": [{"id": "s1", "status": "ERROR"}]}
        )
        assert r["checks"]["no_contradictions"] is False

    def test_detecta_dependencia_inexistente(self, verifier: VerifierAgent) -> None:
        r = verifier._check_consistency(
            {"steps": [{"id": "s1", "depends_on": ["s0"], "status": "DONE"}]}
        )
        assert r["checks"]["references_valid"] is False
        assert r["dangling_references"]

    def test_acepta_un_resultado_coherente(self, verifier: VerifierAgent) -> None:
        r = verifier._check_consistency(
            {
                "success": True,
                "steps": [
                    {"id": "s1", "status": "DONE", "success": True},
                    {"id": "s2", "status": "DONE", "success": True, "depends_on": ["s1"]},
                ],
            }
        )
        assert r["checks"]["no_contradictions"] is True
        assert r["checks"]["references_valid"] is True
        assert r["score"] == 1.0

    def test_las_comprobaciones_ya_no_estan_fijadas_a_true(
        self, verifier: VerifierAgent
    ) -> None:
        """Antes devolvían `True` sin mirar los datos: era imposible fallar."""
        coherente = verifier._check_consistency({"steps": [{"id": "a", "status": "DONE"}]})
        incoherente = verifier._check_consistency(
            {"steps": [{"id": "a", "status": "DONE", "success": False}]}
        )
        assert coherente["score"] != incoherente["score"]
