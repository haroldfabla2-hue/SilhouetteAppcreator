"""Tests de confinamiento de rutas.

Cada caso corresponde a un vector que el endpoint `/api/system/file-content`
aceptaba antes del arreglo.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from backend.app.security.workspace import (
    PathNotAllowed,
    is_within_workspace,
    resolve_within_workspace,
    safe_relative,
)


@pytest.fixture()
def raiz(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('hola')", encoding="utf-8")
    (tmp_path / ".env").write_text("OPENROUTER_API_KEY=sk-secreto", encoding="utf-8")
    (tmp_path / "security").mkdir()
    (tmp_path / "security" / "master.key").write_text("clave", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("[core]", encoding="utf-8")
    return tmp_path


class TestRutasPermitidas:
    def test_acepta_ruta_relativa(self, raiz: Path) -> None:
        assert resolve_within_workspace("src/app.py", root=raiz) == (raiz / "src" / "app.py").resolve()

    def test_acepta_ruta_absoluta_dentro(self, raiz: Path) -> None:
        objetivo = raiz / "src" / "app.py"
        assert resolve_within_workspace(str(objetivo), root=raiz) == objetivo.resolve()

    def test_safe_relative_no_revela_el_disco(self, raiz: Path) -> None:
        assert safe_relative(raiz / "src" / "app.py", root=raiz) == "src/app.py"


class TestEscapeDelWorkspace:
    @pytest.mark.parametrize(
        "ruta",
        [
            "../../../etc/passwd",
            "..",
            "src/../../fuera.txt",
            "./src/../../../secreto",
        ],
    )
    def test_bloquea_recorrido_de_directorios(self, raiz: Path, ruta: str) -> None:
        with pytest.raises(PathNotAllowed):
            resolve_within_workspace(ruta, root=raiz)

    @pytest.mark.skipif(sys.platform != "win32", reason="rutas de Windows")
    def test_bloquea_rutas_absolutas_de_windows(self, raiz: Path) -> None:
        for ruta in [r"C:\Windows\System32\drivers\etc\hosts", r"C:\Users"]:
            with pytest.raises(PathNotAllowed):
                resolve_within_workspace(ruta, root=raiz)

    @pytest.mark.skipif(sys.platform == "win32", reason="rutas POSIX")
    def test_bloquea_rutas_absolutas_posix(self, raiz: Path) -> None:
        for ruta in ["/etc/passwd", "/root/.ssh/id_rsa"]:
            with pytest.raises(PathNotAllowed):
                resolve_within_workspace(ruta, root=raiz)

    def test_bloquea_symlink_que_apunta_fuera(self, raiz: Path, tmp_path: Path) -> None:
        fuera = tmp_path.parent / "fuera_del_workspace.txt"
        fuera.write_text("secreto", encoding="utf-8")
        enlace = raiz / "atajo.txt"
        try:
            enlace.symlink_to(fuera)
        except (OSError, NotImplementedError):
            pytest.skip("este entorno no permite crear enlaces simbólicos")
        with pytest.raises(PathNotAllowed):
            resolve_within_workspace("atajo.txt", root=raiz)


class TestArchivosBloqueados:
    @pytest.mark.parametrize(
        "ruta",
        [".env", ".env.template", "security/master.key", ".git/config"],
    )
    def test_bloquea_secretos_y_control_de_versiones(self, raiz: Path, ruta: str) -> None:
        with pytest.raises(PathNotAllowed):
            resolve_within_workspace(ruta, root=raiz)

    @pytest.mark.parametrize("nombre", ["servidor.pem", "cliente.p12", "id_rsa", "almacen.jks"])
    def test_bloquea_material_criptografico(self, raiz: Path, nombre: str) -> None:
        (raiz / nombre).write_text("x", encoding="utf-8")
        with pytest.raises(PathNotAllowed):
            resolve_within_workspace(nombre, root=raiz)

    def test_is_within_workspace_no_lanza(self, raiz: Path) -> None:
        assert is_within_workspace("src/app.py", root=raiz)
        assert not is_within_workspace("../fuera", root=raiz)
