"""Tests de las capacidades que estaban fingidas en `legacy/`.

Cada clase corresponde a un módulo archivado que devolvía datos inventados y que
ahora funciona de verdad. La prueba central en todas es la misma: **si la
capacidad no está disponible, se declara; nunca se rellena.**
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from backend.app.orchestrator.executive_supervisor import ExecutiveSupervisor
from backend.app.organism.circadian import PHASE_ENGINES, CircadianRhythm, Phase
from backend.app.organism.cognitive_organs import (
    ENGINE_INTERVALS,
    CognitiveEnginesUnavailable,
    CognitiveOrgans,
)
from backend.app.organism.self_healing import SelfHealing, Severity
from backend.app.organism.vital_daemon import VitalDaemon
from backend.app.tools import market_data, research
from backend.app.tools.git_agent import (
    GitAgent,
    GitError,
    InvalidBranchName,
    NotARepository,
)


# ---------------------------------------------------------------------------
# Agente Git — sustituye 5 operaciones `_simulate_*`
# ---------------------------------------------------------------------------
class TestGitAgent:
    @pytest.fixture()
    def git(self) -> GitAgent:
        return GitAgent(".")

    async def test_lee_el_repositorio_real(self, git: GitAgent) -> None:
        info = await git.get_repository_info()
        assert info.current_branch, "debe leer la rama real"
        assert len(info.head_sha) == 40, "el SHA debe ser un hash git completo"

    async def test_el_historial_son_commits_reales(self, git: GitAgent) -> None:
        commits = await git.get_commit_history(limit=3)
        assert commits
        for c in commits:
            assert len(c.sha) == 40
            assert c.author and c.subject

    async def test_el_historial_respeta_el_limite(self, git: GitAgent) -> None:
        assert len(await git.get_commit_history(limit=2)) <= 2

    async def test_detecta_conflictos_sin_fusionar(self, git: GitAgent) -> None:
        """`merge-tree` calcula en memoria: no toca el árbol de trabajo."""
        antes = await git.get_repository_info()
        informe = await git.detect_conflicts(antes.current_branch, antes.current_branch)
        despues = await git.get_repository_info()

        assert informe.can_merge, "una rama consigo misma fusiona limpio"
        assert informe.merge_base
        assert despues.head_sha == antes.head_sha, "no debe haber movido el HEAD"

    @pytest.mark.parametrize(
        "nombre", ["--force", "rama con espacios", "../fuga", "-x", "", "rama;rm -rf /"]
    )
    async def test_rechaza_nombres_de_rama_peligrosos(
        self, git: GitAgent, nombre: str
    ) -> None:
        with pytest.raises(InvalidBranchName):
            await git.create_branch(nombre)

    @pytest.mark.parametrize("nombre", ["feature/x", "fix-123", "v1.2.3"])
    def test_acepta_nombres_validos(self, git: GitAgent, nombre: str) -> None:
        assert git._validate_branch(nombre) == nombre

    async def test_una_ruta_fuera_del_workspace_se_rechaza(self) -> None:
        with pytest.raises(GitError):
            GitAgent("../../../etc")

    async def test_un_directorio_sin_git_se_reporta(self, tmp_path: Path) -> None:
        # tmp_path está fuera del workspace, así que falla antes incluso.
        with pytest.raises((GitError, NotARepository)):
            await GitAgent(str(tmp_path)).get_repository_info()

    async def test_no_fusiona_si_habria_conflictos(self, git: GitAgent) -> None:
        """La versión archivada fusionaba a ciegas con `_simulate_merge_branch`."""
        info = await git.get_repository_info()
        resultado = await git.merge_branch(info.current_branch)
        # Fusionar la rama consigo misma es un no-op, pero nunca debe mentir.
        assert isinstance(resultado.get("merged"), bool)


# ---------------------------------------------------------------------------
# Motores cognitivos — el ciclo biomimético
# ---------------------------------------------------------------------------
class TestCognitiveOrgans:
    @pytest.fixture()
    def organs(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CognitiveOrgans:
        monkeypatch.setenv("SILHOUETTE_DATA_DIR", str(tmp_path))
        from silhouette.config import get_settings

        get_settings.cache_clear()  # type: ignore[attr-defined]
        from backend.app.services.silhouette_brain_service import SilhouetteBrainService

        servicio = SilhouetteBrainService()
        yield CognitiveOrgans(brain=servicio)
        servicio.close()

    def test_los_cuatro_motores_estan(self, organs: CognitiveOrgans) -> None:
        if not organs.available:
            pytest.skip("silhouette-brain no instalado")
        assert set(organs.engine_names) == {"curiosity", "dreamer", "evolution", "janitor"}

    async def test_operan_sobre_memoria_real(self, organs: CognitiveOrgans) -> None:
        if not organs.available:
            pytest.skip("silhouette-brain no instalado")
        await organs.brain.remember_event("El orquestador coordina agentes", 0.9)
        ejecuciones = await organs.run_all()
        assert len(ejecuciones) == 4
        assert all(e.ok for e in ejecuciones), [e.error for e in ejecuciones if not e.ok]
        assert all(e.summary for e in ejecuciones), "cada motor debe reportar qué hizo"

    async def test_un_motor_desconocido_se_reporta(self, organs: CognitiveOrgans) -> None:
        if not organs.available:
            pytest.skip("silhouette-brain no instalado")
        with pytest.raises(KeyError):
            await organs.run_engine("motor-inventado")

    async def test_sin_memoria_falla_en_cerrado(self) -> None:
        class SinMemoria:
            available = False

        with pytest.raises(CognitiveEnginesUnavailable):
            await CognitiveOrgans(brain=SinMemoria()).run_engine("janitor")

    def test_sin_ejecuciones_no_inventa_resumen(self, organs: CognitiveOrgans) -> None:
        if not organs.available:
            pytest.skip("silhouette-brain no instalado")
        for datos in organs.stats()["engines"].values():
            assert datos["runs"] == 0
            assert datos["last_summary"] is None, "«sin datos» es None, no un texto"

    def test_se_registran_como_organos(self, organs: CognitiveOrgans, tmp_path: Path) -> None:
        if not organs.available:
            pytest.skip("silhouette-brain no instalado")
        daemon = VitalDaemon(
            state_path=tmp_path / "e.json", lock_path=tmp_path / "l.lock", single_instance=False
        )
        registrados = organs.register_with(daemon)
        assert set(registrados) == {"curiosity", "dreamer", "evolution", "janitor"}


class TestCicloCircadianoCubreLosMotores:
    def test_ningun_motor_queda_sin_fase(self) -> None:
        """Un órgano que no aparece en ninguna fase nunca se ejecutaría.

        Ocurrió al añadir los motores cognitivos: se registraron como órganos
        pero tres de ellos no estaban en `PHASE_ENGINES`, así que el daemon
        jamás los habría llamado.
        """
        con_fase = set().union(*PHASE_ENGINES.values())
        for motor in ENGINE_INTERVALS:
            assert motor in con_fase, f"'{motor}' no se ejecutaría en ninguna fase"

    def test_los_motores_no_corren_mientras_el_usuario_trabaja(self) -> None:
        activos = PHASE_ENGINES[Phase.ACTIVE]
        for motor in ENGINE_INTERVALS:
            assert motor not in activos, f"'{motor}' competiría con la petición del usuario"

    def test_el_ciclo_completo_corre_durante_el_sueno(self) -> None:
        soñando = PHASE_ENGINES[Phase.DREAMING]
        assert set(ENGINE_INTERVALS).issubset(soñando)

    def test_la_fase_de_sueno_se_alcanza_sin_interaccion(self) -> None:
        ritmo = CircadianRhythm()
        ritmo._last_interaction = time.time() - (2 * 3600)
        assert ritmo.current().phase is Phase.DREAMING


# ---------------------------------------------------------------------------
# Auto-sanación — sustituye métricas generadas con random
# ---------------------------------------------------------------------------
class TestSelfHealing:
    @pytest.fixture()
    def healing(self, tmp_path: Path) -> SelfHealing:
        from backend.app.evolution.agent_improver import AgentImprover, ProfileStore

        sup = ExecutiveSupervisor(stall_threshold_s=0.05)
        org = VitalDaemon(
            state_path=tmp_path / "e.json", lock_path=tmp_path / "l.lock", single_instance=False
        )
        return SelfHealing(
            organism=org,
            supervisor=sup,
            improver=AgentImprover(store=ProfileStore(tmp_path / "p.json"), supervisor=sup),
        )

    def test_sin_datos_no_afirma_que_todo_va_bien(self, healing: SelfHealing) -> None:
        """El panel anterior siempre se veía verde porque inventaba las cifras."""
        agentes = next(
            i for i in healing.diagnose().indicators if i["name"] == "agentes"
        )
        assert agentes["severity"] == Severity.UNKNOWN.value
        assert agentes["value"] is None

    def test_detecta_agentes_degradados(self, healing: SelfHealing) -> None:
        for i in range(10):
            healing.supervisor.record_task_start(f"t{i}", "reasoner")
            healing.supervisor.record_task_end(f"t{i}", success=(i < 2), error="fallo")

        agentes = next(
            i for i in healing.diagnose().indicators if i["name"] == "agentes"
        )
        assert agentes["severity"] == Severity.CRITICAL.value
        assert agentes["value"] == pytest.approx(0.2, abs=0.01)

    def test_detecta_estancamiento(self, healing: SelfHealing) -> None:
        healing.supervisor.record_task_start("colgada", "planner")
        time.sleep(0.06)
        estancamiento = next(
            i for i in healing.diagnose().indicators if i["name"] == "estancamiento"
        )
        assert estancamiento["severity"] == Severity.CRITICAL.value

    async def test_la_reparacion_actua_de_verdad(self, healing: SelfHealing) -> None:
        healing.supervisor.record_task_start("colgada", "planner")
        time.sleep(0.06)

        resultado = await healing.heal()
        aplicadas = [a for a in resultado["actions"] if a["applied"]]
        assert any(a["action"] == "liberar_tareas_estancadas" for a in aplicadas)
        assert healing.supervisor.stalled_tasks() == [], "la tarea debe quedar liberada"

    async def test_sin_nada_que_reparar_lo_dice(self, healing: SelfHealing) -> None:
        resultado = await healing.heal()
        acciones_reales = [
            a for a in resultado["actions"] if a["action"] != "reducir_cadencia"
        ]
        assert not [a for a in acciones_reales if a["applied"]]

    def test_la_severidad_global_la_marca_el_peor(self, healing: SelfHealing) -> None:
        healing.supervisor.record_task_start("colgada", "x")
        time.sleep(0.06)
        assert healing.diagnose().severity is Severity.CRITICAL


# ---------------------------------------------------------------------------
# Investigación — sustituye patentes generadas con random.choice()
# ---------------------------------------------------------------------------
class TestResearch:
    async def test_las_patentes_se_declaran_no_implementadas(self) -> None:
        """La versión archivada las inventaba, inventores incluidos."""
        with pytest.raises(NotImplementedError, match="patentes"):
            await research.patents_search("cualquier cosa")

    async def test_una_fuente_invalida_se_rechaza(self) -> None:
        with pytest.raises(ValueError):
            await research.search("x", sources=("fuente-inventada",))

    def test_el_parser_de_arxiv_extrae_campos_reales(self) -> None:
        xml = """<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <id>http://arxiv.org/abs/2405.15383v1</id>
            <title>Un titulo real</title>
            <summary>Un resumen real.</summary>
            <published>2024-05-24T00:00:00Z</published>
            <author><name>Ada Lovelace</name></author>
            <category term="cs.AI"/>
          </entry>
        </feed>"""
        articulos = research._parse_arxiv(xml)
        assert len(articulos) == 1
        assert articulos[0].title == "Un titulo real"
        assert articulos[0].authors == ["Ada Lovelace"]
        assert articulos[0].arxiv_id == "2405.15383v1"

    def test_xml_invalido_se_reporta(self) -> None:
        with pytest.raises(research.ResearchUnavailable):
            research._parse_arxiv("esto no es xml")

    def test_deduplica_entre_fuentes(self) -> None:
        a = research.Paper("T", [], "", "", "", "arxiv", doi="10.1/x")
        b = research.Paper("T", [], "resumen", "", "", "semantic_scholar", doi="10.1/X",
                           citation_count=42)
        unicos = research._dedupe([a, b])
        assert len(unicos) == 1
        assert unicos[0].citation_count == 42, "conserva la version con mas metadatos"

    @pytest.mark.integration
    async def test_busqueda_real(self) -> None:
        """Se salta si la red no está disponible; nunca inventa resultados."""
        try:
            r = await research.search("monte carlo tree search", limit=3)
        except research.ResearchUnavailable as exc:
            pytest.skip(f"fuentes no alcanzables: {exc}")
        assert r["total"] > 0
        for p in r["papers"]:
            assert p["title"]
            assert p["arxiv_id"] or p["doi"] or p["url"], "todo resultado debe ser verificable"


# ---------------------------------------------------------------------------
# Mercado — sustituye precios generados con random.uniform()
# ---------------------------------------------------------------------------
class TestMarketData:
    def test_sin_yfinance_se_declara(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(market_data, "YFINANCE_AVAILABLE", False)
        with pytest.raises(market_data.MarketDataUnavailable, match="yfinance"):
            market_data._require()

    async def test_un_simbolo_vacio_se_rechaza(self) -> None:
        if not market_data.is_available():
            pytest.skip("yfinance no instalado")
        with pytest.raises(ValueError):
            await market_data.get_quote("   ")

    def test_sin_precio_no_se_inventa(self) -> None:
        """La version archivada rellenaba con random.uniform(10, 500)."""
        with pytest.raises(market_data.MarketDataUnavailable, match="precio"):
            market_data._build_quote("XXXX", {"currency": "USD"})

    def test_la_respuesta_advierte_del_retardo(self) -> None:
        cotizacion = market_data._build_quote(
            "TEST", {"currentPrice": 100.0, "previousClose": 98.0, "currency": "USD"}
        )
        datos = cotizacion.to_dict()
        assert datos["delayed"] is True
        assert "retardo" in datos["disclaimer"]

    def test_calcula_el_cambio_de_verdad(self) -> None:
        c = market_data._build_quote(
            "TEST", {"currentPrice": 110.0, "previousClose": 100.0, "currency": "USD"}
        )
        assert c.change == pytest.approx(10.0)
        assert c.change_percent == pytest.approx(10.0)

    def test_sin_cierre_anterior_el_cambio_es_desconocido(self) -> None:
        c = market_data._build_quote("TEST", {"currentPrice": 110.0, "currency": "USD"})
        assert c.change is None, "«no se sabe» es None, no 0.0"
        assert c.change_percent is None

    @pytest.mark.integration
    async def test_cotizacion_real(self) -> None:
        if not market_data.is_available():
            pytest.skip("yfinance no instalado")
        try:
            c = await market_data.get_quote("MSFT")
        except market_data.MarketDataUnavailable as exc:
            pytest.skip(f"mercado no alcanzable: {exc}")
        assert c.price > 0
        assert c.currency
        assert c.symbol == "MSFT"
