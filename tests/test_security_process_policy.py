"""Tests de la lista blanca de procesos.

Antes del arreglo, `/api/system/os-launch` ejecutaba cualquier binario porque
`shutil.which(app_name) or app_name` aceptaba una ruta absoluta como respaldo.
"""
from __future__ import annotations

import sys

import pytest

from backend.app.security.process_policy import (
    ENV_ALLOWED_APPS,
    AppNotAllowed,
    ArgumentRejected,
    allowed_apps,
    is_enabled,
    plan_launch,
    validate_args,
)

# Un ejecutable que existe en el PATH de cualquier plataforma soportada.
BINARIO_REAL = "cmd" if sys.platform == "win32" else "sh"


@pytest.fixture()
def sin_lista(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_ALLOWED_APPS, raising=False)


@pytest.fixture()
def con_lista(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_ALLOWED_APPS, BINARIO_REAL)


class TestDesactivadoPorDefecto:
    def test_sin_configuracion_esta_desactivado(self, sin_lista: None) -> None:
        assert not is_enabled()
        assert allowed_apps() == frozenset()

    def test_sin_lista_no_lanza_nada(self, sin_lista: None) -> None:
        with pytest.raises(AppNotAllowed, match="desactivado"):
            plan_launch(BINARIO_REAL)


class TestListaBlanca:
    def test_permite_lo_declarado(self, con_lista: None) -> None:
        plan = plan_launch(BINARIO_REAL)
        assert plan.app_name == BINARIO_REAL
        assert plan.executable  # resuelto desde el PATH, no desde la petición

    def test_rechaza_lo_no_declarado(self, con_lista: None) -> None:
        with pytest.raises(AppNotAllowed):
            plan_launch("calc")

    def test_rechaza_ruta_absoluta_aunque_exista(self, con_lista: None) -> None:
        # El vector original: pasar la ruta completa de un ejecutable arbitrario.
        ruta = r"C:\Windows\System32\calc.exe" if sys.platform == "win32" else "/bin/sh"
        with pytest.raises(AppNotAllowed):
            plan_launch(ruta)

    def test_rechaza_nombre_vacio(self, con_lista: None) -> None:
        with pytest.raises(AppNotAllowed):
            plan_launch("")

    def test_el_ejecutable_no_viene_de_la_peticion(self, con_lista: None) -> None:
        import shutil

        plan = plan_launch(BINARIO_REAL.upper())  # el nombre se normaliza
        assert plan.executable == shutil.which(BINARIO_REAL)


class TestArgumentos:
    def test_sin_argumentos_devuelve_lista_vacia(self) -> None:
        assert validate_args(None) == []
        assert validate_args("   ") == []

    def test_acepta_argumentos_simples(self) -> None:
        assert validate_args("--version") == ["--version"]

    @pytest.mark.parametrize(
        "peligroso",
        [
            "archivo.txt & calc.exe",
            "a | whoami",
            "a; rm -rf /",
            "$(whoami)",
            "`id`",
            "a > salida.txt",
            "a\nsegunda-linea",
        ],
    )
    def test_rechaza_metacaracteres_de_shell(self, peligroso: str) -> None:
        with pytest.raises(ArgumentRejected):
            validate_args(peligroso)

    def test_rechaza_demasiados_argumentos(self) -> None:
        with pytest.raises(ArgumentRejected, match="Demasiados"):
            validate_args(" ".join(f"-a{i}" for i in range(50)))

    def test_rechaza_argumento_gigante(self) -> None:
        with pytest.raises(ArgumentRejected, match="demasiado largo"):
            validate_args("x" * 1000)
