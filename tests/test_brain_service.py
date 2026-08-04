"""Tests de la memoria cognitiva de 4 niveles.

Antes: `get_stats()` devolvía 334.994 conversaciones y 217.042 nodos escritos a
mano, y `remember_event()` no indexaba nada. Aquí se comprueba que los números
salen de datos reales y que crecen al almacenar.
"""
from __future__ import annotations

import pytest

from backend.app.services.silhouette_brain_service import (
    BRAIN_AVAILABLE,
    BrainUnavailable,
    SilhouetteBrainService,
)

pytestmark = pytest.mark.skipif(
    not BRAIN_AVAILABLE, reason="silhouette-brain no está instalado"
)


@pytest.fixture()
def brain(tmp_path, monkeypatch: pytest.MonkeyPatch) -> SilhouetteBrainService:
    # Aísla los almacenes SQLite en un directorio temporal por test.
    monkeypatch.setenv("SILHOUETTE_DATA_DIR", str(tmp_path))
    from silhouette.config import get_settings

    get_settings.cache_clear()  # type: ignore[attr-defined]
    service = SilhouetteBrainService()
    yield service
    service.close()


class TestEstadisticasReales:
    def test_una_memoria_vacia_reporta_ceros(self, brain: SilhouetteBrainService) -> None:
        stats = brain.get_stats()
        assert stats["available"] is True
        assert stats["tiers"]["episodic"] == 0
        assert stats["tiers"]["semantic"] == 0

    async def test_los_contadores_crecen_al_almacenar(self, brain: SilhouetteBrainService) -> None:
        antes = brain.get_stats()["tiers"]["episodic"]
        await brain.remember_event("El planificador descompone objetivos en pasos", 0.9)
        despues = brain.get_stats()["tiers"]["episodic"]
        assert despues == antes + 1

    async def test_los_cuatro_niveles_estan_presentes(self, brain: SilhouetteBrainService) -> None:
        tiers = brain.get_stats()["tiers"]
        assert set(tiers) == {"working", "episodic", "semantic", "deep_graph"}

    def test_declara_el_embedder_que_usa(self, brain: SilhouetteBrainService) -> None:
        assert brain.get_stats()["embedder"]


class TestIngestaYRecuperacion:
    async def test_remember_devuelve_un_identificador_real(self, brain: SilhouetteBrainService) -> None:
        resultado = await brain.remember_event("El verificador valida la salida del ejecutor")
        assert resultado["success"] is True
        assert resultado["memory_id"]

    async def test_lo_almacenado_se_recupera(self, brain: SilhouetteBrainService) -> None:
        await brain.remember_event("El orquestador coordina agentes especializados", 0.9)
        resultado = await brain.recall("orquestador agentes")
        assert resultado["count"] >= 1
        assert "orquestador" in resultado["results"][0]["content"].lower()

    async def test_lo_no_almacenado_no_aparece(self, brain: SilhouetteBrainService) -> None:
        await brain.remember_event("Contenido sobre bases de datos relacionales")
        resultado = await brain.recall("astronomía galaxias nebulosa", min_score=0.5)
        assert resultado["count"] == 0

    async def test_conserva_las_etiquetas(self, brain: SilhouetteBrainService) -> None:
        resultado = await brain.remember_event("Nota etiquetada", tags=["arquitectura", "adr"])
        assert set(resultado["tags"]) == {"arquitectura", "adr"}


class TestPresupuestoDeTokens:
    async def test_el_presupuesto_se_respeta(self, brain: SilhouetteBrainService) -> None:
        for i in range(10):
            await brain.remember_event(f"Registro número {i} sobre el sistema de agentes " * 10)
        paquete = await brain.assemble_context("sistema de agentes", token_budget=100)
        assert paquete["tokens_used"] <= 100, "el presupuesto debe podar de verdad"

    async def test_un_presupuesto_mayor_admite_mas_contexto(
        self, brain: SilhouetteBrainService
    ) -> None:
        for i in range(10):
            await brain.remember_event(f"Registro {i} sobre agentes cognitivos " * 10)
        pequeno = await brain.assemble_context("agentes cognitivos", token_budget=50)
        grande = await brain.assemble_context("agentes cognitivos", token_budget=2000)
        assert grande["tokens_used"] >= pequeno["tokens_used"]

    async def test_reporta_de_donde_sale_el_contexto(self, brain: SilhouetteBrainService) -> None:
        await brain.remember_event("Un dato recuperable sobre el planificador")
        paquete = await brain.assemble_context("planificador")
        assert isinstance(paquete["sources_used"], list)
        assert paquete["latency_ms"] >= 0


class TestFallaEnCerrado:
    async def test_sin_paquete_lanza_error_explicito(self) -> None:
        # Un servicio construido sin memoria no debe inventar estadísticas.
        huerfano = SilhouetteBrainService.__new__(SilhouetteBrainService)
        huerfano._memory = None  # type: ignore[attr-defined]
        huerfano._assembler = None  # type: ignore[attr-defined]
        assert huerfano.available is False
        assert huerfano.get_stats()["available"] is False
        with pytest.raises(BrainUnavailable):
            await huerfano.remember_event("x")
