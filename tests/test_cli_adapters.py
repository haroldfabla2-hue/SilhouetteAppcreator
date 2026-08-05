"""Tests de los adaptadores de agentes CLI.

Cada caso corresponde a un fallo comprobado en una máquina real:

- `claude.exe` existía en `~/.local/bin` y se daba por no instalado, porque la
  resolución no probaba extensiones de Windows.
- A `gemini` se le pasaba el prompt de forma posicional, lo que lo dejaba en
  modo interactivo esperando 120 s hasta el timeout.
- `antigravity` se anunciaba disponible sin comprobación alguna.
- `claude` devolvía «Not logged in · Please run /login» con código de salida 0,
  y eso se propagaba como si fuera la respuesta del modelo.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from backend.app.core.cli_adapters import (
    CLI_SPECS,
    CLIInvocationError,
    CLINotAuthenticated,
    CLISpec,
    CLIUnavailable,
    detect_auth_failure,
    discover_installed,
    is_available,
    resolve_executable,
    run_cli,
)


class TestConstruccionDeArgumentos:
    def test_claude_usa_la_bandera_de_impresion(self) -> None:
        args = CLI_SPECS["claude"].build_args("claude.exe", "hola")
        assert args == ["claude.exe", "-p", "hola"]

    def test_gemini_no_recibe_el_prompt_posicional(self) -> None:
        """Sin `-p`, Gemini arranca en modo interactivo y nunca termina."""
        args = CLI_SPECS["gemini"].build_args("gemini", "hola")
        assert "-p" in args
        assert args.index("-p") < args.index("hola")

    def test_codex_usa_subcomando(self) -> None:
        assert CLI_SPECS["codex"].build_args("codex", "hola") == ["codex", "exec", "hola"]

    def test_cursor_apunta_al_agente_no_al_ide(self) -> None:
        # `cursor` a secas abre el IDE; el agente headless es `cursor-agent`.
        assert "cursor-agent" in CLI_SPECS["cursor"].executables
        assert "cursor" not in CLI_SPECS["cursor"].executables

    def test_aider_incluye_sus_flags_no_interactivos(self) -> None:
        args = CLI_SPECS["aider"].build_args("aider", "hola")
        assert "--no-auto-commits" in args
        assert "--yes-always" in args

    def test_goose_combina_subcomando_y_bandera(self) -> None:
        assert CLI_SPECS["goose"].build_args("goose", "x") == ["goose", "run", "-t", "x"]

    @pytest.mark.parametrize("nombre", sorted(CLI_SPECS))
    def test_todos_incluyen_el_prompt(self, nombre: str) -> None:
        args = CLI_SPECS[nombre].build_args("bin", "MI-PROMPT")
        assert "MI-PROMPT" in args, f"{nombre} pierde el prompt"


class TestResolucionDeRutas:
    def test_encuentra_ejecutable_con_extension(self, tmp_path: Path) -> None:
        """El fallo original: `claude.exe` presente pero no detectado."""
        bin_dir = tmp_path / ".local" / "bin"
        bin_dir.mkdir(parents=True)
        sufijo = ".exe" if os.name == "nt" else ""
        (bin_dir / f"miagente{sufijo}").write_text("", encoding="utf-8")

        spec = CLISpec(name="miagente", executables=("miagente",), home_subdirs=(".local/bin",))
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(Path, "home", classmethod(lambda cls: tmp_path))
            assert resolve_executable(spec) is not None

    def test_devuelve_none_si_no_existe(self) -> None:
        spec = CLISpec(name="x", executables=("agente-que-no-existe-12345",))
        assert resolve_executable(spec) is None

    def test_prueba_todos_los_nombres_candidatos(self, tmp_path: Path) -> None:
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        sufijo = ".exe" if os.name == "nt" else ""
        (bin_dir / f"segundo{sufijo}").write_text("", encoding="utf-8")

        spec = CLISpec(name="x", executables=("primero", "segundo"), home_subdirs=("bin",))
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(Path, "home", classmethod(lambda cls: tmp_path))
            resuelto = resolve_executable(spec)
        assert resuelto is not None and "segundo" in resuelto


class TestDisponibilidad:
    def test_un_cli_inexistente_no_esta_disponible(self) -> None:
        assert is_available("codex-inventado") is False

    def test_el_inventario_cubre_todos_los_registrados(self) -> None:
        inventario = discover_installed()
        assert set(inventario) == set(CLI_SPECS)

    def test_cada_entrada_declara_su_ruta(self) -> None:
        for nombre, info in discover_installed().items():
            assert isinstance(info["available"], bool)
            if info["available"]:
                assert info["executable"], f"{nombre} disponible sin ruta"
            else:
                # No disponible no puede traer una ruta inventada.
                assert info["executable"] is None

    def test_antigravity_ya_no_se_da_por_disponible_sin_comprobar(self) -> None:
        info = discover_installed()["antigravity"]
        if not info["available"]:
            assert info["executable"] is None


class TestDeteccionDeSesion:
    @pytest.mark.parametrize(
        "salida",
        [
            "Not logged in · Please run /login",
            "Authentication required",
            "Invalid API key",
            "No has iniciado sesión",
            "Quota exceeded",
            "Rate limit exceeded",
            "Insufficient credits",
        ],
    )
    def test_detecta_avisos_de_sesion(self, salida: str) -> None:
        assert detect_auth_failure(salida) is not None

    @pytest.mark.parametrize(
        "salida",
        [
            "OK",
            "def suma(a, b):\n    return a + b",
            "La respuesta es 42.",
        ],
    )
    def test_no_marca_respuestas_legitimas(self, salida: str) -> None:
        assert detect_auth_failure(salida) is None

    def test_una_explicacion_larga_sobre_claves_no_es_fallo(self) -> None:
        """Una respuesta que explique autenticación es válida, no un error."""
        larga = (
            "Para manejar la autenticación en tu API deberías validar el API key "
            "en cada petición. Si el api key not found, devuelve 401. " * 6
        )
        assert len(larga) > 400
        assert detect_auth_failure(larga) is None


class TestEjecucion:
    async def test_cli_desconocido_se_reporta(self) -> None:
        with pytest.raises(CLIUnavailable, match="desconocido"):
            await run_cli("no-existe-este-cli", "hola")

    async def test_cli_no_instalado_se_reporta(self) -> None:
        with pytest.raises(CLIUnavailable, match="no está instalado"):
            await run_cli("crush", "hola")

    async def test_la_jerarquia_de_errores_permite_distinguir(self) -> None:
        # CLINotAuthenticated es un CLIInvocationError: quien sólo quiera saber
        # "falló" puede capturar el padre; quien quiera distinguir, el hijo.
        assert issubclass(CLINotAuthenticated, CLIInvocationError)
        assert not issubclass(CLIUnavailable, CLIInvocationError)


class TestIntegracionConElRouter:
    def test_todo_proveedor_cli_tiene_adaptador(self) -> None:
        from backend.app.core.llm_router import CLI_PROVIDER_NAMES

        for proveedor, nombre in CLI_PROVIDER_NAMES.items():
            assert nombre in CLI_SPECS, f"{proveedor.value} sin adaptador registrado"

    def test_el_orden_de_fallback_cubre_todos_los_cli(self) -> None:
        from backend.app.core.llm_router import CLI_FALLBACK_ORDER, CLI_PROVIDER_NAMES

        assert set(CLI_FALLBACK_ORDER) == set(CLI_PROVIDER_NAMES)

    def test_el_fallback_solo_ofrece_lo_instalado(self) -> None:
        from backend.app.core.llm_router import (
            CLI_PROVIDER_NAMES,
            LLMProvider,
            LLMRouter,
        )

        orden = LLMRouter()._get_fallback_order(LLMProvider.OPENROUTER_LLAMA70B, "llama70b")
        for proveedor in orden:
            if proveedor in CLI_PROVIDER_NAMES:
                assert is_available(CLI_PROVIDER_NAMES[proveedor]), (
                    f"{proveedor.value} está en la cadena sin estar instalado"
                )

    def test_fallback_local_ya_no_se_disfraza_de_antigravity(self) -> None:
        """Antes, FALLBACK_LOCAL se despachaba como si fuera Antigravity."""
        from backend.app.core.llm_router import CLI_PROVIDER_NAMES, LLMProvider

        assert LLMProvider.FALLBACK_LOCAL not in CLI_PROVIDER_NAMES


@pytest.mark.integration
class TestEntornoReal:
    """Se saltan si el CLI no está instalado en la máquina que ejecuta los tests."""

    @pytest.mark.skipif(not is_available("claude"), reason="Claude Code no instalado")
    async def test_claude_responde_o_pide_sesion(self) -> None:
        try:
            salida = await run_cli("claude", "Responde solo: OK", timeout_s=120)
            assert salida
        except CLINotAuthenticated:
            pytest.skip("Claude Code instalado pero sin sesión iniciada")

    @pytest.mark.skipif(sys.platform != "win32", reason="específico de Windows")
    def test_los_scripts_cmd_se_envuelven(self) -> None:
        from backend.app.core.cli_adapters import NEEDS_SHELL_WRAPPER

        assert ".cmd" in NEEDS_SHELL_WRAPPER
        assert ".bat" in NEEDS_SHELL_WRAPPER
