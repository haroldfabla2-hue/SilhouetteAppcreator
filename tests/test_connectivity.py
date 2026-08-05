"""Tests de conectividad con proveedores de IA.

Cada caso corresponde a un fallo diagnosticado en la máquina real:

- El `.env` no lo cargaba nadie, así que las claves bien escritas no las veía
  ningún módulo y el sistema arrancaba sin ningún modelo.
- `core/__init__.py` importaba `config` antes de cargar el entorno, y las claves
  quedaban congeladas a cadena vacía para toda la vida del proceso.
- Validar OpenRouter contra `/models` daba «conectado» con una clave revocada,
  porque ese endpoint es público.
- Escribir un emoji en un registro reventaba el proceso en una consola cp1252.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from backend.app.core import console, env_loader, providers
from backend.app.core.onboarding import write_env_var
from backend.app.core.providers import PROVIDERS, AuthKind, Status


class TestCargaDeEntorno:
    def test_lee_pares_clave_valor(self, tmp_path: Path) -> None:
        f = tmp_path / "a.env"
        f.write_text("CLAVE=valor\nOTRA=2\n", encoding="utf-8")
        assert env_loader.parse_env_file(f) == {"CLAVE": "valor", "OTRA": "2"}

    def test_ignora_comentarios_y_lineas_sueltas(self, tmp_path: Path) -> None:
        f = tmp_path / "a.env"
        f.write_text("# comentario\n\nSIN_IGUAL\nOK=1\n", encoding="utf-8")
        assert env_loader.parse_env_file(f) == {"OK": "1"}

    @pytest.mark.parametrize(
        "linea,esperado",
        [
            ('K="entre comillas"', "entre comillas"),
            ("K='simples'", "simples"),
            ("export K=con-export", "con-export"),
            ("K=  con espacios  ", "con espacios"),
        ],
    )
    def test_formatos_admitidos(self, tmp_path: Path, linea: str, esperado: str) -> None:
        f = tmp_path / "a.env"
        f.write_text(linea + "\n", encoding="utf-8")
        assert env_loader.parse_env_file(f)["K"] == esperado

    def test_soporta_utf16(self, tmp_path: Path) -> None:
        """Un editor de Windows ya guardó el .gitignore de este repo en UTF-16."""
        f = tmp_path / "a.env"
        f.write_text("CLAVE=valor\n", encoding="utf-16")
        assert env_loader.parse_env_file(f) == {"CLAVE": "valor"}

    def test_el_entorno_real_tiene_prioridad(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Un `.env` olvidado no puede pisar un secreto inyectado en el despliegue."""
        f = tmp_path / "a.env"
        f.write_text("YA_DEFINIDA=del-archivo\n", encoding="utf-8")
        monkeypatch.setenv("YA_DEFINIDA", "del-entorno")
        monkeypatch.setattr(env_loader, "ENV_FILES", ())
        env_loader.load_env(extra_files=(f,))
        assert os.environ["YA_DEFINIDA"] == "del-entorno"

    def test_aplica_lo_que_falta(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        f = tmp_path / "a.env"
        f.write_text("SOLO_EN_ARCHIVO=valor\n", encoding="utf-8")
        monkeypatch.delenv("SOLO_EN_ARCHIVO", raising=False)
        monkeypatch.setattr(env_loader, "ENV_FILES", ())
        aplicadas = env_loader.load_env(extra_files=(f,))
        assert aplicadas["SOLO_EN_ARCHIVO"] == "valor"
        assert os.environ["SOLO_EN_ARCHIVO"] == "valor"

    def test_los_valores_vacios_no_tapan(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        f = tmp_path / "a.env"
        f.write_text("VACIA=\n", encoding="utf-8")
        monkeypatch.delenv("VACIA", raising=False)
        monkeypatch.setattr(env_loader, "ENV_FILES", ())
        assert "VACIA" not in env_loader.load_env(extra_files=(f,))


class TestConfiguracionTardia:
    def test_las_claves_reflejan_el_entorno_actual(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """El fallo original: la clave quedaba congelada al importar el módulo."""
        from backend.app.core.config import settings

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-definida-despues")
        assert settings.OPENROUTER_API_KEY == "sk-or-v1-definida-despues"

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-cambiada-otra-vez")
        assert settings.OPENROUTER_API_KEY == "sk-or-v1-cambiada-otra-vez"

    def test_el_router_ve_una_clave_puesta_despues(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from backend.app.core.llm_router import LLMRouter

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-nueva")
        assert LLMRouter().openrouter_api_key == "sk-or-v1-nueva"


class TestValidacionDeProveedores:
    def test_openrouter_no_valida_contra_un_endpoint_publico(self) -> None:
        """`/models` responde 200 con una clave revocada: no sirve para validar."""
        assert PROVIDERS["openrouter"].validate_path != "/models"

    @pytest.mark.parametrize("nombre", sorted(PROVIDERS))
    def test_cada_proveedor_esta_completo(self, nombre: str) -> None:
        spec = PROVIDERS[nombre]
        assert spec.label and spec.base_url and spec.how_to
        if spec.auth is AuthKind.API_KEY:
            assert spec.env_var, f"{nombre} sin variable de entorno"
            assert spec.signup_url, f"{nombre} sin sitio donde obtener la clave"

    def test_los_marcadores_de_plantilla_no_son_credenciales(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        for marcador in ("tu_clave_aqui", "your_key_here", "[INSERTAR]", "<clave>"):
            monkeypatch.setenv("GROQ_API_KEY", marcador)
            assert PROVIDERS["groq"].credential == ""
            assert PROVIDERS["groq"].configured is False

    def test_una_credencial_real_si_cuenta(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "gsk_credencialreal123")
        assert PROVIDERS["groq"].configured is True

    async def test_sin_clave_no_se_intenta_conectar(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        salud = await providers.check_provider("groq")
        assert salud.status is Status.NOT_CONFIGURED
        assert salud.usable is False
        assert "GROQ_API_KEY" in salud.detail

    async def test_un_proveedor_local_apagado_se_reporta(self) -> None:
        salud = await providers.check_provider("vllm", timeout_s=3)
        # No inventa disponibilidad: o conecta, o dice que no pudo.
        assert salud.status in (Status.READY, Status.UNREACHABLE)
        if salud.status is Status.UNREACHABLE:
            assert "conectar" in salud.detail.lower()

    async def test_proveedor_desconocido(self) -> None:
        with pytest.raises(KeyError):
            await providers.check_provider("proveedor-inventado")

    def test_los_locales_no_piden_credencial(self) -> None:
        for nombre in ("ollama", "lmstudio", "vllm"):
            assert PROVIDERS[nombre].auth is AuthKind.NONE
            assert PROVIDERS[nombre].configured is True


class TestGuardadoDeCredenciales:
    def test_escribe_una_variable_nueva(self, tmp_path: Path) -> None:
        destino = tmp_path / ".env"
        write_env_var("NUEVA_CLAVE", "valor-1", path=destino)
        assert "NUEVA_CLAVE=valor-1" in destino.read_text(encoding="utf-8")

    def test_actualiza_sin_duplicar(self, tmp_path: Path) -> None:
        destino = tmp_path / ".env"
        destino.write_text("OTRA=1\nCLAVE=vieja\n", encoding="utf-8")
        write_env_var("CLAVE", "nueva", path=destino)
        contenido = destino.read_text(encoding="utf-8")
        assert "CLAVE=nueva" in contenido
        assert "CLAVE=vieja" not in contenido
        assert contenido.count("CLAVE=") == 1
        assert "OTRA=1" in contenido, "no debe perder el resto del archivo"

    def test_queda_disponible_sin_reiniciar(self, tmp_path: Path) -> None:
        write_env_var("CLAVE_INMEDIATA", "ya-vale", path=tmp_path / ".env")
        assert os.environ["CLAVE_INMEDIATA"] == "ya-vale"

    def test_siempre_escribe_utf8(self, tmp_path: Path) -> None:
        destino = tmp_path / ".env"
        write_env_var("ACENTOS", "configuración", path=destino)
        assert destino.read_text(encoding="utf-8").count("configuración") == 1


class TestConsolaSegura:
    def test_configurar_es_idempotente(self) -> None:
        console.configure()
        console.configure()  # no debe lanzar

    def test_los_emojis_no_revientan(self) -> None:
        """Escribir un emoji en un log tumbaba el proceso en consolas cp1252."""
        assert console.safe_text("Sistema 🚀 iniciado")

    def test_recorta_respetando_el_limite(self) -> None:
        assert len(console.safe_text("x" * 500, limit=50)) <= 51

    def test_conserva_el_texto_normal(self) -> None:
        assert console.safe_text("respuesta normal") == "respuesta normal"


class TestDiagnosticoDeGemini:
    def test_detecta_la_clave_obsoleta(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import json

        from backend.app.core import onboarding

        conf = tmp_path / "settings.json"
        conf.write_text(
            json.dumps({"mcpServers": {"x": {"serverUrl": "http://a", "headers": {}}}}),
            encoding="utf-8",
        )
        monkeypatch.setattr(onboarding, "_gemini_settings_path", lambda: conf)

        problema = onboarding.diagnose_gemini_config()
        assert problema is not None
        assert problema.severity == "blocker"
        assert problema.auto_fixable is True

    def test_la_reparacion_renombra_y_respalda(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import json

        from backend.app.core import onboarding

        conf = tmp_path / "settings.json"
        conf.write_text(
            json.dumps({"mcpServers": {"x": {"serverUrl": "http://a"}}}), encoding="utf-8"
        )
        monkeypatch.setattr(onboarding, "_gemini_settings_path", lambda: conf)

        resultado = onboarding.fix_gemini_config()
        assert resultado["applied"] is True
        datos = json.loads(conf.read_text(encoding="utf-8"))
        assert datos["mcpServers"]["x"]["httpUrl"] == "http://a"
        assert "serverUrl" not in datos["mcpServers"]["x"]
        assert Path(resultado["backup"]).is_file(), "debe dejar copia de seguridad"

    def test_una_configuracion_correcta_no_se_toca(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import json

        from backend.app.core import onboarding

        conf = tmp_path / "settings.json"
        conf.write_text(json.dumps({"mcpServers": {"x": {"httpUrl": "http://a"}}}), encoding="utf-8")
        monkeypatch.setattr(onboarding, "_gemini_settings_path", lambda: conf)

        assert onboarding.diagnose_gemini_config() is None
        assert onboarding.fix_gemini_config()["applied"] is False
