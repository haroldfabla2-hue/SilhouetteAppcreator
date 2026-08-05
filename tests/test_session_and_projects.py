"""Tests de lo que se afirmaba y no existía.

Una auditoría comparó lo que un agente describió con lo que el código hacía.
Nueve afirmaciones eran falsas. Cada clase aquí cubre una de las que se han
implementado, y el test comprueba justo lo que se daba por hecho sin serlo.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from backend.app.core.agent_models import AgentModelRegistry
from backend.app.core.cli_manager import (
    INSTALLERS,
    LOGIN_COMMANDS,
    catalog,
    login_instructions,
)
from backend.app.core.session import SessionManager
from backend.app.projects.registry import ProjectError, ProjectRegistry
from backend.app.projects.workspaces import WorkspaceError, WorkspaceManager


class EjecutorFalso:
    """Captura los prompts que recibe, para comprobar qué se le inyectó."""

    def __init__(self, respuesta: str = "resultado") -> None:
        self.prompts: list[str] = []
        self.respuesta = respuesta

    async def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return f"{self.respuesta}-{len(self.prompts)}"


class CerebroAusente:
    available = False


# ---------------------------------------------------------------------------
# Afirmación 3: «todos los CLI comparten el mismo session_id»
# ---------------------------------------------------------------------------
class TestSesionCompartida:
    @pytest.fixture()
    def manager(self) -> SessionManager:
        return SessionManager(brain=CerebroAusente())

    def test_una_sesion_tiene_identificador(self, manager: SessionManager) -> None:
        sesion = manager.create("Construir una API")
        assert sesion.session_id.startswith("ses_")

    def test_dos_sesiones_no_se_mezclan(self, manager: SessionManager) -> None:
        a = manager.create("Objetivo A")
        b = manager.create("Objetivo B")
        assert a.session_id != b.session_id

    def test_se_recupera_por_identificador(self, manager: SessionManager) -> None:
        sesion = manager.create("x")
        assert manager.get(sesion.session_id) is sesion
        assert manager.get_or_create(sesion.session_id, "otro") is sesion

    def test_registra_quien_aporto_que(self, manager: SessionManager) -> None:
        sesion = manager.create("x")
        sesion.add("planner", "el plan")
        sesion.add("executor_code", "el código")
        assert [c.agent for c in sesion.contributions] == ["planner", "executor_code"]


# ---------------------------------------------------------------------------
# Afirmación 2: «el prompt de cada CLI lleva el contexto de los demás agentes»
# ---------------------------------------------------------------------------
class TestContextoCompartido:
    @pytest.fixture()
    def manager(self) -> SessionManager:
        return SessionManager(brain=CerebroAusente())

    async def test_el_segundo_agente_ve_lo_del_primero(self, manager: SessionManager) -> None:
        """Era la carencia central: cada CLI trabajaba a ciegas."""
        sesion = manager.create("Construir una API de usuarios")
        ejecutor = EjecutorFalso()

        await manager.run_with_context(sesion, "planner", "Diseña el plan", ejecutor)
        await manager.run_with_context(sesion, "executor_code", "Implementa", ejecutor)

        assert "resultado-1" in ejecutor.prompts[1], "el ejecutor debe ver lo del planificador"

    async def test_el_prompt_lleva_el_objetivo_general(self, manager: SessionManager) -> None:
        sesion = manager.create("Migrar la base de datos a PostgreSQL")
        ejecutor = EjecutorFalso()
        await manager.run_with_context(sesion, "planner", "Empieza", ejecutor)
        assert "Migrar la base de datos" in ejecutor.prompts[0]

    async def test_el_prompt_lleva_el_identificador_de_sesion(
        self, manager: SessionManager
    ) -> None:
        sesion = manager.create("x")
        ejecutor = EjecutorFalso()
        await manager.run_with_context(sesion, "planner", "y", ejecutor)
        assert sesion.session_id in ejecutor.prompts[0]

    async def test_a_un_agente_no_se_le_repite_su_propia_salida(
        self, manager: SessionManager
    ) -> None:
        sesion = manager.create("x")
        ejecutor = EjecutorFalso()
        await manager.run_with_context(sesion, "planner", "primera", ejecutor)
        await manager.run_with_context(sesion, "planner", "segunda", ejecutor)
        # Gastar contexto repitiéndole lo suyo no le aporta nada.
        assert "resultado-1" not in ejecutor.prompts[1]

    def test_el_contexto_respeta_un_presupuesto(self, manager: SessionManager) -> None:
        sesion = manager.create("x")
        for i in range(50):
            sesion.add(f"agente{i}", "z" * 2000)
        assert len(sesion.shared_context()) <= 7000

    async def test_sin_memoria_sigue_funcionando(self, manager: SessionManager) -> None:
        """La memoria de largo plazo es un apoyo, no un requisito."""
        sesion = manager.create("x")
        ejecutor = EjecutorFalso()
        assert await manager.run_with_context(sesion, "a", "tarea", ejecutor)


# ---------------------------------------------------------------------------
# Afirmación 4: «la salida se guarda inmediatamente en memoria»
# ---------------------------------------------------------------------------
class TestPersistenciaDeContribuciones:
    async def test_lo_producido_se_guarda_en_memoria(self) -> None:
        guardado: list[dict] = []

        class CerebroEspia:
            available = True

            async def remember_event(self, content, importance=0.5, *, tags=None, source=""):
                guardado.append({"content": content, "tags": tags or []})
                return {"success": True, "memory_id": "m1"}

            async def assemble_context(self, *a, **k):
                return {"semantic": []}

        manager = SessionManager(brain=CerebroEspia())
        sesion = manager.create("Objetivo con memoria")
        await manager.run_with_context(sesion, "planner", "tarea", EjecutorFalso())

        assert guardado, "la contribución debe persistirse"
        assert sesion.session_id in guardado[0]["tags"]

    async def test_un_fallo_no_se_guarda_como_aportacion(self) -> None:
        manager = SessionManager(brain=CerebroAusente())
        sesion = manager.create("x")

        async def revienta(_: str) -> str:
            raise RuntimeError("el proveedor cayó")

        with pytest.raises(RuntimeError):
            await manager.run_with_context(sesion, "planner", "tarea", revienta)
        assert sesion.contributions == [], "un fallo no es una contribución"


# ---------------------------------------------------------------------------
# Afirmación 5: «cada agente usa un CLI distinto»
# ---------------------------------------------------------------------------
class TestModeloPorAgente:
    @pytest.fixture()
    def registro(self, tmp_path: Path) -> AgentModelRegistry:
        return AgentModelRegistry(path=tmp_path / "modelos.json")

    def test_los_agentes_tienen_preferencias_distintas(
        self, registro: AgentModelRegistry
    ) -> None:
        razonador = registro.policy_for("reasoner").preferred
        web = registro.policy_for("executor_web").preferred
        assert razonador and web
        assert razonador != web, "el reparto por agente debe ser real"

    def test_el_verificador_usa_la_temperatura_mas_baja(
        self, registro: AgentModelRegistry
    ) -> None:
        verificador = registro.policy_for("verifier").temperature
        creativo = registro.policy_for("executor_docs").temperature
        assert verificador < creativo

    def test_no_devuelve_un_proveedor_no_disponible(
        self, registro: AgentModelRegistry
    ) -> None:
        class RouterSinNada:
            def _is_provider_available(self, _proveedor) -> bool:
                return False

        assert registro.resolve_provider("reasoner", RouterSinNada()) is None

    def test_respeta_el_orden_de_preferencia(self, registro: AgentModelRegistry) -> None:
        from backend.app.core.llm_router import LLMProvider

        registro.set_policy("x", preferred=["cli_gemini", "cli_claude_code"])

        class SoloGemini:
            def _is_provider_available(self, proveedor) -> bool:
                return proveedor is LLMProvider.CLI_GEMINI

        assert registro.resolve_provider("x", SoloGemini()) is LLMProvider.CLI_GEMINI

    def test_la_politica_persiste(self, tmp_path: Path) -> None:
        ruta = tmp_path / "m.json"
        AgentModelRegistry(path=ruta).set_policy("reasoner", temperature=0.11)
        assert AgentModelRegistry(path=ruta).policy_for("reasoner").temperature == 0.11

    def test_declara_cuando_no_hay_preferido_disponible(
        self, registro: AgentModelRegistry
    ) -> None:
        class RouterSinNada:
            def _is_provider_available(self, _p) -> bool:
                return False

        asignacion = registro.effective_assignment(RouterSinNada())
        assert asignacion["reasoner"]["resolved"] is None
        assert "cadena general" in asignacion["reasoner"]["reason"]


# ---------------------------------------------------------------------------
# Proyectos: carpetas locales
# ---------------------------------------------------------------------------
class TestProyectos:
    @pytest.fixture()
    def registro(self, tmp_path: Path) -> ProjectRegistry:
        return ProjectRegistry(path=tmp_path / "proyectos.json")

    @pytest.fixture()
    def carpeta(self, tmp_path: Path) -> Path:
        destino = tmp_path / "mi-proyecto"
        destino.mkdir()
        (destino / "main.py").write_text("print('hola')", encoding="utf-8")
        return destino

    def test_registra_una_carpeta(self, registro: ProjectRegistry, carpeta: Path) -> None:
        proyecto = registro.register(carpeta)
        assert proyecto.name == "mi-proyecto"
        assert Path(proyecto.path) == carpeta.resolve()

    def test_no_duplica(self, registro: ProjectRegistry, carpeta: Path) -> None:
        a = registro.register(carpeta)
        b = registro.register(carpeta)
        assert a.id == b.id
        assert len(registro.list_all()) == 1

    def test_rechaza_carpetas_inexistentes(self, registro: ProjectRegistry) -> None:
        with pytest.raises(ProjectError, match="No existe"):
            registro.register("/no/existe/12345")

    def test_rechaza_la_carpeta_del_usuario(self, registro: ProjectRegistry) -> None:
        """Registrarla daría acceso efectivo a todo el disco."""
        with pytest.raises(ProjectError, match="raíz"):
            registro.register(Path.home())

    def test_detecta_si_es_repositorio_git(
        self, registro: ProjectRegistry, carpeta: Path, tmp_path: Path
    ) -> None:
        assert registro.register(carpeta).is_git is False

        con_git = tmp_path / "con-git"
        con_git.mkdir()
        (con_git / ".git").mkdir()
        assert registro.register(con_git).is_git is True

    def test_el_activo_se_puede_cambiar(
        self, registro: ProjectRegistry, carpeta: Path, tmp_path: Path
    ) -> None:
        primero = registro.register(carpeta)
        segundo_dir = tmp_path / "otro"
        segundo_dir.mkdir()
        segundo = registro.register(segundo_dir)

        assert registro.active_id == primero.id
        registro.set_active(segundo.id)
        assert registro.active_id == segundo.id

    def test_dar_de_baja_no_borra_la_carpeta(
        self, registro: ProjectRegistry, carpeta: Path
    ) -> None:
        proyecto = registro.register(carpeta)
        assert registro.unregister(proyecto.id)
        assert carpeta.exists(), "retirar del registro nunca debe borrar archivos"

    def test_persiste_entre_reinicios(self, tmp_path: Path, carpeta: Path) -> None:
        ruta = tmp_path / "p.json"
        ProjectRegistry(path=ruta).register(carpeta, name="Persistente")
        assert ProjectRegistry(path=ruta).list_all()[0]["name"] == "Persistente"

    def test_sin_proyectos_usa_la_raiz_del_repositorio(
        self, registro: ProjectRegistry
    ) -> None:
        from backend.app.security.workspace import workspace_root

        assert registro.resolve_root() == workspace_root()


# ---------------------------------------------------------------------------
# Afirmación 6: «cada agente trabaja en su rama aislada con worktrees»
# ---------------------------------------------------------------------------
def _repo_git(destino: Path) -> Path:
    """Crea un repositorio git real con un commit."""
    destino.mkdir(parents=True, exist_ok=True)
    correr = lambda *a: subprocess.run(  # noqa: E731
        ["git", *a], cwd=destino, check=True, capture_output=True
    )
    correr("init", "-b", "main")
    correr("config", "user.email", "prueba@local.test")
    correr("config", "user.name", "Prueba")
    (destino / "README.md").write_text("# proyecto\n", encoding="utf-8")
    correr("add", "-A")
    correr("commit", "-m", "inicial")
    return destino


class TestEspaciosAislados:
    @pytest.fixture()
    def manager(self, tmp_path: Path) -> WorkspaceManager:
        repo = _repo_git(tmp_path / "repo")
        registro = ProjectRegistry(path=tmp_path / "p.json")
        registro.register(repo, name="repo-prueba")
        return WorkspaceManager(registry=registro)

    async def test_lista_las_ramas_reales(self, manager: WorkspaceManager) -> None:
        info = await manager.list_branches()
        assert info["current"] == "main"
        assert any(b["name"] == "main" for b in info["branches"])

    async def test_crea_una_rama(self, manager: WorkspaceManager) -> None:
        resultado = await manager.create_branch("feature/nueva")
        assert resultado["created"]
        info = await manager.list_branches()
        assert any(b["name"] == "feature/nueva" for b in info["branches"])

    @pytest.mark.parametrize("nombre", ["--force", "con espacios", "../fuga", ""])
    async def test_rechaza_nombres_peligrosos(
        self, manager: WorkspaceManager, nombre: str
    ) -> None:
        with pytest.raises(WorkspaceError, match="inválido"):
            await manager.create_branch(nombre)

    async def test_reserva_un_worktree_de_verdad(self, manager: WorkspaceManager) -> None:
        espacio = await manager.reserve("t1", "executor_code")
        assert Path(espacio.path).is_dir(), "el worktree debe existir en disco"
        assert (Path(espacio.path) / "README.md").is_file()
        assert espacio.branch.startswith("silhouette/")

    async def test_dos_agentes_no_colisionan(self, manager: WorkspaceManager) -> None:
        """El punto de todo el mecanismo: trabajo concurrente sin pisarse."""
        a = await manager.reserve("t1", "executor_code")
        b = await manager.reserve("t2", "executor_web")

        (Path(a.path) / "a.txt").write_text("de A", encoding="utf-8")
        (Path(b.path) / "b.txt").write_text("de B", encoding="utf-8")

        assert not (Path(a.path) / "b.txt").exists(), "A no debe ver el trabajo de B"
        assert not (Path(b.path) / "a.txt").exists(), "B no debe ver el trabajo de A"
        assert a.branch != b.branch

    async def test_integra_el_trabajo_en_la_rama_base(
        self, manager: WorkspaceManager
    ) -> None:
        espacio = await manager.reserve("t1", "executor_code")
        (Path(espacio.path) / "nuevo.txt").write_text("contenido", encoding="utf-8")

        resultado = await manager.integrate("t1")
        assert resultado.merged, resultado.detail

        raiz = manager.registry.resolve_root()
        assert (raiz / "nuevo.txt").is_file(), "el trabajo debe llegar a la rama base"

    async def test_sin_cambios_no_finge_integracion(
        self, manager: WorkspaceManager
    ) -> None:
        await manager.reserve("t1", "executor_code")
        resultado = await manager.integrate("t1")
        assert resultado.merged is False
        assert "no produjo ningún cambio" in resultado.detail

    async def test_liberar_conserva_la_rama_sin_integrar(
        self, manager: WorkspaceManager
    ) -> None:
        """Borrar una rama con trabajo sin integrar perdería ese trabajo."""
        espacio = await manager.reserve("t1", "executor_code")
        (Path(espacio.path) / "x.txt").write_text("trabajo", encoding="utf-8")

        resultado = await manager.release("t1")
        assert resultado["released"]
        assert resultado["branch_deleted"] is False

        info = await manager.list_branches()
        assert any(b["name"] == espacio.branch for b in info["branches"])

    async def test_liberar_limpia_tras_integrar(self, manager: WorkspaceManager) -> None:
        espacio = await manager.reserve("t1", "executor_code")
        (Path(espacio.path) / "y.txt").write_text("trabajo", encoding="utf-8")
        await manager.integrate("t1")

        resultado = await manager.release("t1")
        assert resultado["branch_deleted"] is True
        assert not Path(espacio.path).exists()

    async def test_no_cambia_de_rama_con_cambios_sin_guardar(
        self, manager: WorkspaceManager
    ) -> None:
        raiz = manager.registry.resolve_root()
        await manager.create_branch("otra")
        (raiz / "sucio.txt").write_text("sin guardar", encoding="utf-8")

        with pytest.raises(WorkspaceError, match="sin guardar"):
            await manager.switch_branch("otra")

    async def test_una_carpeta_sin_git_se_reporta(self, tmp_path: Path) -> None:
        sin_git = tmp_path / "sin-git"
        sin_git.mkdir()
        registro = ProjectRegistry(path=tmp_path / "p2.json")
        registro.register(sin_git)

        with pytest.raises(WorkspaceError, match="no es un repositorio git"):
            await WorkspaceManager(registry=registro).reserve("t", "a")


# ---------------------------------------------------------------------------
# Afirmación 1: «conectar.py --instalar» / login desde la app
# ---------------------------------------------------------------------------
class TestGestionDeCLIs:
    def test_el_catalogo_cubre_todos_los_cli(self) -> None:
        from backend.app.core.cli_adapters import CLI_SPECS

        assert {c["cli"] for c in catalog()} == set(CLI_SPECS)

    def test_cada_entrada_dice_como_instalarse(self) -> None:
        for entrada in catalog():
            if entrada["installable"]:
                assert entrada["install_manager"] in ("npm", "pip", "brew", "winget")
                assert entrada["install_package"]
            else:
                assert entrada["docs_url"], "sin instalador automático debe haber documentación"

    def test_cada_entrada_dice_como_autenticarse(self) -> None:
        for entrada in catalog():
            assert entrada["login"]["hint"], f"{entrada['cli']} sin instrucción de login"

    @pytest.mark.parametrize("cli", ["claude", "gemini", "codex", "copilot"])
    def test_los_login_por_navegador_estan_marcados(self, cli: str) -> None:
        info = login_instructions(cli)
        assert info["supported"]
        assert info["opens_browser"]

    def test_aider_no_finge_oauth(self) -> None:
        """Aider usa claves de API; anunciarle un login sería inexacto."""
        assert login_instructions("aider")["opens_browser"] is False

    def test_un_cli_desconocido_se_reporta(self) -> None:
        assert login_instructions("inventado")["supported"] is False

    async def test_instalar_algo_desconocido_falla(self) -> None:
        from backend.app.core.cli_manager import CLIManagerError, install

        with pytest.raises(CLIManagerError, match="No hay instalador"):
            await install("cli-que-no-existe")

    async def test_login_de_un_cli_no_instalado_se_reporta(self) -> None:
        from backend.app.core.cli_manager import CLIManagerError, open_login_terminal

        with pytest.raises(CLIManagerError, match="no está instalado"):
            await open_login_terminal("crush")

    def test_todo_instalador_tiene_su_login(self) -> None:
        assert set(INSTALLERS).issubset(set(LOGIN_COMMANDS))
