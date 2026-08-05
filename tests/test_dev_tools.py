"""Tests de las herramientas del agente de desarrollo.

Editar código, ejecutar los tests y entender el repositorio. Son las tres
capacidades que separan un agente de desarrollo de un generador de texto que
escribe archivos.

La garantía que más importa aquí: **una edición que rompería el archivo no se
escribe**. Un agente que deja el árbol roto es peor que uno que no edita.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.tools.code_editor import (
    AmbiguousMatch,
    CodeEditor,
    EditError,
    NoMatch,
    ValidationFailed,
)
from backend.app.tools.repo_index import RepoIndex
from backend.app.tools.suite_runner import SuiteRunner, SuiteRunnerUnavailable


@pytest.fixture()
def editor(tmp_path: Path) -> CodeEditor:
    return CodeEditor(backup_dir=tmp_path / "backups")


@pytest.fixture()
def archivo() -> str:
    """Ruta dentro del workspace, que es donde el editor puede operar."""
    return "data/_prueba_editor.py"


@pytest.fixture(autouse=True)
def _limpiar(archivo: str):
    yield
    from backend.app.security.workspace import workspace_root

    (workspace_root() / archivo).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Editor de código
# ---------------------------------------------------------------------------
class TestValidacionAntesDeEscribir:
    def test_no_escribe_python_roto(self, editor: CodeEditor, archivo: str) -> None:
        editor.write(archivo, "def suma(a, b):\n    return a + b\n")
        with pytest.raises(ValidationFailed, match="Python"):
            editor.replace(archivo, "return a + b", "return a +")

    def test_el_archivo_queda_intacto_tras_un_rechazo(
        self, editor: CodeEditor, archivo: str
    ) -> None:
        original = "def suma(a, b):\n    return a + b\n"
        editor.write(archivo, original)
        with pytest.raises(ValidationFailed):
            editor.replace(archivo, "return a + b", "return a +")
        assert editor.read(archivo).content == original

    def test_no_escribe_json_roto(self, editor: CodeEditor) -> None:
        ruta = "data/_prueba.json"
        try:
            editor.write(ruta, '{"a": 1}')
            with pytest.raises(ValidationFailed, match="JSON"):
                editor.replace(ruta, '{"a": 1}', '{"a": 1,}')
        finally:
            from backend.app.security.workspace import workspace_root

            (workspace_root() / ruta).unlink(missing_ok=True)

    def test_declara_con_que_valido(self, editor: CodeEditor, archivo: str) -> None:
        assert editor.write(archivo, "x = 1\n").validated_as == "python-ast"


class TestEdicionExacta:
    def test_sustituye_un_fragmento(self, editor: CodeEditor, archivo: str) -> None:
        editor.write(archivo, "valor = 1\n")
        resultado = editor.replace(archivo, "valor = 1", "valor = 2")
        assert resultado.applied
        assert editor.read(archivo).content.strip() == "valor = 2"

    def test_rechaza_coincidencias_ambiguas(self, editor: CodeEditor, archivo: str) -> None:
        """Adivinar cuál era la correcta es cómo se corrompe un archivo."""
        editor.write(archivo, "x = 1\ny = 1\n")
        with pytest.raises(AmbiguousMatch, match="2 veces"):
            editor.replace(archivo, "= 1", "= 2")

    def test_replace_all_permite_lo_ambiguo(self, editor: CodeEditor, archivo: str) -> None:
        editor.write(archivo, "x = 1\ny = 1\n")
        editor.replace(archivo, "= 1", "= 2", replace_all=True)
        assert editor.read(archivo).content.count("= 2") == 2

    def test_sin_coincidencia_lo_dice(self, editor: CodeEditor, archivo: str) -> None:
        editor.write(archivo, "x = 1\n")
        with pytest.raises(NoMatch, match="no aparece"):
            editor.replace(archivo, "no existe este texto", "y")

    def test_produce_un_diff_real(self, editor: CodeEditor, archivo: str) -> None:
        editor.write(archivo, "a = 1\n")
        resultado = editor.replace(archivo, "a = 1", "a = 2")
        assert "-a = 1" in resultado.diff
        assert "+a = 2" in resultado.diff
        assert resultado.lines_added == 1
        assert resultado.lines_removed == 1


class TestRespaldoYReversion:
    def test_revertir_restaura_el_contenido(self, editor: CodeEditor, archivo: str) -> None:
        editor.write(archivo, "original = True\n")
        editor.replace(archivo, "original = True", "modificado = True")
        assert "modificado" in editor.read(archivo).content

        editor.revert(archivo)
        assert "original = True" in editor.read(archivo).content

    def test_sin_copias_lo_dice(self, editor: CodeEditor, archivo: str) -> None:
        editor.create(archivo, "x = 1\n")
        with pytest.raises(EditError, match="No hay copias"):
            editor.revert(archivo)

    def test_lista_las_copias(self, editor: CodeEditor, archivo: str) -> None:
        editor.write(archivo, "v = 1\n")
        editor.write(archivo, "v = 2\n")
        assert len(editor.backups(archivo)) >= 1


class TestConfinamiento:
    @pytest.mark.parametrize("ruta", ["../../../etc/passwd", ".env", "security/master.key"])
    def test_no_escribe_fuera_del_workspace(self, editor: CodeEditor, ruta: str) -> None:
        with pytest.raises(EditError):
            editor.write(ruta, "contenido")

    def test_no_lee_secretos(self, editor: CodeEditor) -> None:
        with pytest.raises(EditError):
            editor.read(".env")


class TestLecturaConEstructura:
    def test_extrae_los_simbolos(self, editor: CodeEditor, archivo: str) -> None:
        editor.write(
            archivo,
            "class Motor:\n"
            "    def arranca(self):\n"
            "        pass\n"
            "\n"
            "async def principal():\n"
            "    pass\n",
        )
        vista = editor.read(archivo)
        nombres = {s["name"] for s in vista.symbols}
        assert nombres == {"Motor", "arranca", "principal"}
        assert vista.language == "python"

    def test_un_archivo_inexistente_se_reporta(self, editor: CodeEditor) -> None:
        with pytest.raises(EditError, match="No existe"):
            editor.read("data/_no_existe_12345.py")


# ---------------------------------------------------------------------------
# Índice del repositorio
# ---------------------------------------------------------------------------
class TestRepoIndex:
    @pytest.fixture(scope="class")
    def indice(self) -> RepoIndex:
        idx = RepoIndex()
        idx.build()
        return idx

    def test_indexa_el_repositorio_real(self, indice: RepoIndex) -> None:
        s = indice.stats()
        assert s["files"] > 50
        assert s["symbols"] > 100
        assert "py" in s["by_language"]

    def test_todo_el_python_activo_parsea(self, indice: RepoIndex) -> None:
        """Un archivo que no parsea es un archivo roto, y hay que saberlo.

        El índice encontró así `health_check.py`, cuyo contenido estaba volcado
        en una sola línea con `\\n` literales: no podía ejecutarse.
        """
        assert indice.stats()["unparsed"] == []

    def test_localiza_una_clase_conocida(self, indice: RepoIndex) -> None:
        coincidencias = indice.find_symbol("VitalDaemon", exact=True)
        assert coincidencias
        assert coincidencias[0]["kind"] == "class"
        assert coincidencias[0]["file"].endswith("vital_daemon.py")

    def test_la_busqueda_parcial_encuentra(self, indice: RepoIndex) -> None:
        assert indice.find_symbol("Daemon")

    def test_distingue_definicion_de_uso(self, indice: RepoIndex) -> None:
        r = indice.find_references("CognitiveOrgans")
        assert r["definition_count"] >= 1
        assert r["reference_count"] >= 1
        lineas_def = {(d["file"], d["line"]) for d in r["definitions"]}
        for uso in r["references"]:
            assert (uso["file"], uso["line"]) not in lineas_def

    def test_busca_texto_con_ubicacion(self, indice: RepoIndex) -> None:
        hits = indice.search_text("NoProviderAvailable")
        assert hits
        assert all(h["file"] and h["line"] > 0 for h in hits)

    def test_una_regex_invalida_se_reporta(self, indice: RepoIndex) -> None:
        with pytest.raises(ValueError, match="inválida"):
            indice.search_text("[sin cerrar", regex=True)

    def test_no_indexa_legacy(self, indice: RepoIndex) -> None:
        """El código archivado no forma parte del repositorio activo."""
        for hit in indice.search_text("def "):
            assert not hit["file"].startswith("legacy/")

    def test_esquema_de_un_archivo(self, indice: RepoIndex) -> None:
        esquema = indice.outline("backend/app/organism/circadian.py")
        assert esquema["parsed"] is True
        assert any(s["name"] == "CircadianRhythm" for s in esquema["symbols"])


# ---------------------------------------------------------------------------
# Ejecutor de tests
# ---------------------------------------------------------------------------
class TestEjecutorDeSuite:
    async def test_ejecuta_una_suite_real(self) -> None:
        resultado = await SuiteRunner().run("tests/test_organism.py")
        assert resultado.passed > 0
        assert resultado.ok is True
        assert resultado.exit_code == 0
        assert resultado.duration_s > 0

    async def test_el_exito_lo_decide_pytest(self) -> None:
        """`ok` sale del código de salida, no de una interpretación."""
        resultado = await SuiteRunner().run("tests/test_organism.py")
        assert resultado.ok == (resultado.exit_code == 0)

    async def test_un_objetivo_inexistente_se_reporta(self) -> None:
        with pytest.raises(SuiteRunnerUnavailable, match="No existe"):
            await SuiteRunner().run("tests/no_existe_12345.py")

    async def test_una_ruta_fuera_del_workspace_se_rechaza(self) -> None:
        with pytest.raises(SuiteRunnerUnavailable):
            await SuiteRunner().run("../../../tmp/test_x.py")

    async def test_sin_tests_recogidos_no_es_exito(self) -> None:
        """pytest devuelve 5 cuando no recoge nada. No es «todo verde»."""
        with pytest.raises(SuiteRunnerUnavailable, match="ningún test"):
            await SuiteRunner().run(keyword="palabra_que_no_coincide_con_nada_12345")

    async def test_reporta_el_comando_ejecutado(self) -> None:
        resultado = await SuiteRunner().run("tests/test_organism.py")
        assert resultado.command.startswith("pytest")
        assert resultado.summary_line
