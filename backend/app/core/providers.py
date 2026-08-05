"""Registro unificado de proveedores de IA y validación real de credenciales.

Conectar una IA era el punto más frágil del sistema: había que saber qué
variable de entorno tocaba, editar un archivo a mano y reiniciar, sin ninguna
señal de si la clave servía. Aquí cada proveedor declara:

- cómo se llama su variable de entorno,
- cómo comprobar **de verdad** que la credencial funciona (una llamada real),
- dónde se obtiene, si hace falta,
- y qué tipo de autenticación usa (clave, OAuth de navegador o ninguna).

`check_provider()` no mira si la variable existe: hace una petición y mira si el
proveedor la acepta. La diferencia importa — una clave caducada «existe».
"""
from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import httpx

logger = logging.getLogger("Providers")

VALIDATION_TIMEOUT_S = 15.0


class AuthKind(str, Enum):
    """Cómo se autentica un proveedor."""

    API_KEY = "api_key"        # Se pega una clave.
    OAUTH_BROWSER = "oauth"    # Se abre el navegador (Google, GitHub…).
    NONE = "none"              # Servidor local sin credencial.


class ProviderKind(str, Enum):
    CLOUD = "cloud"
    LOCAL = "local"
    CLI = "cli"


class Status(str, Enum):
    READY = "ready"                  # Configurado y verificado.
    INVALID = "invalid"              # Configurado pero la credencial no sirve.
    NOT_CONFIGURED = "not_configured"
    UNREACHABLE = "unreachable"      # No se pudo comprobar (red, servicio caído).


@dataclass(frozen=True)
class ProviderSpec:
    """Todo lo necesario para conectar y verificar un proveedor."""

    name: str
    label: str
    kind: ProviderKind
    auth: AuthKind
    #: Variable de entorno con la credencial.
    env_var: str = ""
    base_url: str = ""
    #: Ruta que se consulta para validar; suele listar modelos.
    validate_path: str = "/models"
    #: Cabecera de autorización. `{key}` se sustituye por la credencial.
    auth_header: str = "Authorization"
    auth_format: str = "Bearer {key}"
    #: Dónde consigue el usuario la credencial.
    signup_url: str = ""
    #: Instrucción corta y accionable para conectarlo.
    how_to: str = ""
    aliases: tuple[str, ...] = field(default_factory=tuple)

    @property
    def configured(self) -> bool:
        if self.auth is AuthKind.NONE:
            return True
        return bool(self.credential)

    @property
    def credential(self) -> str:
        if not self.env_var:
            return ""
        valor = os.getenv(self.env_var, "").strip()
        # Los marcadores de las plantillas no son credenciales.
        if valor.lower().startswith(("tu_", "your_", "[insertar", "xxx", "<")):
            return ""
        return valor


PROVIDERS: dict[str, ProviderSpec] = {
    # -- Nube -------------------------------------------------------------
    "openrouter": ProviderSpec(
        name="openrouter",
        label="OpenRouter",
        kind=ProviderKind.CLOUD,
        auth=AuthKind.API_KEY,
        env_var="OPENROUTER_API_KEY",
        base_url="https://openrouter.ai/api/v1",
        # `/models` en OpenRouter es público: responde 200 aunque la clave esté
        # revocada, y validar contra él daba un falso «conectado» que sólo se
        # descubría al primer intento real de generación. `/auth/key` sí exige
        # credencial, que es justamente lo que hay que comprobar.
        validate_path="/auth/key",
        signup_url="https://openrouter.ai/keys",
        how_to="Da acceso a cientos de modelos con una sola clave. La opción más rápida para empezar.",
    ),
    "openai": ProviderSpec(
        name="openai",
        label="OpenAI",
        kind=ProviderKind.CLOUD,
        auth=AuthKind.API_KEY,
        env_var="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
        signup_url="https://platform.openai.com/api-keys",
        how_to="Clave de la plataforma de OpenAI.",
    ),
    "anthropic": ProviderSpec(
        name="anthropic",
        label="Anthropic",
        kind=ProviderKind.CLOUD,
        auth=AuthKind.API_KEY,
        env_var="ANTHROPIC_API_KEY",
        base_url="https://api.anthropic.com/v1",
        auth_header="x-api-key",
        auth_format="{key}",
        signup_url="https://console.anthropic.com/settings/keys",
        how_to="Clave de la consola de Anthropic.",
    ),
    "google": ProviderSpec(
        name="google",
        label="Google AI (Gemini)",
        kind=ProviderKind.CLOUD,
        auth=AuthKind.API_KEY,
        env_var="GEMINI_API_KEY",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        validate_path="/models",
        auth_header="x-goog-api-key",
        auth_format="{key}",
        signup_url="https://aistudio.google.com/apikey",
        how_to=(
            "Clave de Google AI Studio. Si prefiere entrar con su cuenta de Google "
            "sin gestionar claves, use el CLI de Gemini: se autentica por navegador."
        ),
        aliases=("gemini_api", "GOOGLE_API_KEY"),
    ),
    "groq": ProviderSpec(
        name="groq",
        label="Groq",
        kind=ProviderKind.CLOUD,
        auth=AuthKind.API_KEY,
        env_var="GROQ_API_KEY",
        base_url="https://api.groq.com/openai/v1",
        signup_url="https://console.groq.com/keys",
        how_to="Inferencia muy rápida sobre modelos abiertos.",
    ),
    "deepseek": ProviderSpec(
        name="deepseek",
        label="DeepSeek",
        kind=ProviderKind.CLOUD,
        auth=AuthKind.API_KEY,
        env_var="DEEPSEEK_API_KEY",
        base_url="https://api.deepseek.com/v1",
        signup_url="https://platform.deepseek.com/api_keys",
        how_to="Modelos de código a bajo coste.",
    ),
    "zhipu": ProviderSpec(
        name="zhipu",
        label="Zhipu AI (GLM)",
        kind=ProviderKind.CLOUD,
        auth=AuthKind.API_KEY,
        env_var="ZHIPU_API_KEY",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        signup_url="https://open.bigmodel.cn/usercenter/apikeys",
        how_to="Familia GLM.",
    ),
    "moonshot": ProviderSpec(
        name="moonshot",
        label="Moonshot (Kimi)",
        kind=ProviderKind.CLOUD,
        auth=AuthKind.API_KEY,
        env_var="MOONSHOT_API_KEY",
        base_url="https://api.moonshot.cn/v1",
        signup_url="https://platform.moonshot.cn/console/api-keys",
        how_to="Modelos Kimi, con ventana de contexto muy amplia.",
    ),
    "minimax": ProviderSpec(
        name="minimax",
        label="MiniMax",
        kind=ProviderKind.CLOUD,
        auth=AuthKind.API_KEY,
        env_var="MINIMAX_API_KEY",
        base_url="https://api.minimax.chat/v1",
        signup_url="https://platform.minimaxi.com/user-center/basic-information/interface-key",
        how_to="Familia MiniMax.",
    ),
    "xai": ProviderSpec(
        name="xai",
        label="xAI (Grok)",
        kind=ProviderKind.CLOUD,
        auth=AuthKind.API_KEY,
        env_var="XAI_API_KEY",
        base_url="https://api.x.ai/v1",
        signup_url="https://console.x.ai",
        how_to="Modelos Grok.",
    ),
    "mistral": ProviderSpec(
        name="mistral",
        label="Mistral",
        kind=ProviderKind.CLOUD,
        auth=AuthKind.API_KEY,
        env_var="MISTRAL_API_KEY",
        base_url="https://api.mistral.ai/v1",
        signup_url="https://console.mistral.ai/api-keys",
        how_to="Modelos Mistral.",
    ),
    # -- Locales ----------------------------------------------------------
    "ollama": ProviderSpec(
        name="ollama",
        label="Ollama (local)",
        kind=ProviderKind.LOCAL,
        auth=AuthKind.NONE,
        base_url="http://localhost:11434",
        validate_path="/api/tags",
        signup_url="https://ollama.com/download",
        how_to="Modelos en su propia máquina, sin clave ni coste. Arránquelo con `ollama serve`.",
    ),
    "lmstudio": ProviderSpec(
        name="lmstudio",
        label="LM Studio (local)",
        kind=ProviderKind.LOCAL,
        auth=AuthKind.NONE,
        base_url="http://localhost:1234/v1",
        signup_url="https://lmstudio.ai",
        how_to="Active el servidor local en LM Studio.",
    ),
    "vllm": ProviderSpec(
        name="vllm",
        label="vLLM (local)",
        kind=ProviderKind.LOCAL,
        auth=AuthKind.NONE,
        base_url="http://localhost:8000/v1",
        signup_url="https://docs.vllm.ai",
        how_to="Servidor vLLM compatible con la API de OpenAI.",
    ),
}


@dataclass
class ProviderHealth:
    """Resultado de comprobar un proveedor de verdad."""

    name: str
    label: str
    kind: str
    auth: str
    status: Status
    detail: str = ""
    models_seen: int = 0
    signup_url: str = ""
    how_to: str = ""
    env_var: str = ""

    @property
    def usable(self) -> bool:
        return self.status is Status.READY

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "kind": self.kind,
            "auth": self.auth,
            "status": self.status.value,
            "usable": self.usable,
            "detail": self.detail,
            "models_seen": self.models_seen,
            "signup_url": self.signup_url,
            "how_to": self.how_to,
            "env_var": self.env_var,
        }


def _count_models(payload: Any) -> int:
    if isinstance(payload, dict):
        for clave in ("data", "models"):
            valor = payload.get(clave)
            if isinstance(valor, list):
                return len(valor)
    if isinstance(payload, list):
        return len(payload)
    return 0


async def check_provider(
    name: str, *, credential: str | None = None, timeout_s: float = VALIDATION_TIMEOUT_S
) -> ProviderHealth:
    """Comprueba un proveedor haciendo una petición real.

    `credential` permite validar una clave **antes** de guardarla, para no dejar
    el sistema configurado con algo que no funciona.
    """
    spec = PROVIDERS.get(name)
    if spec is None:
        raise KeyError(f"Proveedor desconocido '{name}'. Conocidos: {', '.join(sorted(PROVIDERS))}")

    salud = ProviderHealth(
        name=spec.name,
        label=spec.label,
        kind=spec.kind.value,
        auth=spec.auth.value,
        status=Status.NOT_CONFIGURED,
        signup_url=spec.signup_url,
        how_to=spec.how_to,
        env_var=spec.env_var,
    )

    clave = credential if credential is not None else spec.credential
    if spec.auth is not AuthKind.NONE and not clave:
        salud.detail = f"Falta la variable {spec.env_var}."
        return salud

    cabeceras: dict[str, str] = {"Accept": "application/json"}
    if spec.auth is not AuthKind.NONE and clave:
        cabeceras[spec.auth_header] = spec.auth_format.format(key=clave)
    if spec.name == "anthropic":
        cabeceras["anthropic-version"] = "2023-06-01"

    url = f"{spec.base_url.rstrip('/')}{spec.validate_path}"
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as cliente:
            respuesta = await cliente.get(url, headers=cabeceras)
    except httpx.ConnectError:
        salud.status = Status.UNREACHABLE
        salud.detail = (
            f"No se pudo conectar con {spec.base_url}."
            + (" ¿Está el servidor local arrancado?" if spec.kind is ProviderKind.LOCAL else "")
        )
        return salud
    except httpx.TimeoutException:
        salud.status = Status.UNREACHABLE
        salud.detail = f"Sin respuesta en {timeout_s:.0f} s."
        return salud
    except httpx.HTTPError as exc:
        salud.status = Status.UNREACHABLE
        salud.detail = f"Error de red: {exc}"
        return salud

    if respuesta.status_code in (401, 403):
        salud.status = Status.INVALID
        salud.detail = "El proveedor rechazó la credencial (¿caducada o incorrecta?)."
        return salud
    if respuesta.status_code >= 400:
        salud.status = Status.UNREACHABLE
        salud.detail = f"El proveedor respondió {respuesta.status_code}."
        return salud

    salud.status = Status.READY
    try:
        salud.models_seen = _count_models(respuesta.json())
    except ValueError:
        salud.models_seen = 0
    salud.detail = (
        f"Conectado; {salud.models_seen} modelo(s) visibles."
        if salud.models_seen
        else "Conectado."
    )
    return salud


async def check_all(*, only_configured: bool = False) -> list[ProviderHealth]:
    """Comprueba todos los proveedores en paralelo."""
    nombres = [
        n for n, s in PROVIDERS.items() if not only_configured or s.configured
    ]
    resultados = await asyncio.gather(
        *(check_provider(n) for n in nombres), return_exceptions=True
    )

    salidas: list[ProviderHealth] = []
    for nombre, resultado in zip(nombres, resultados, strict=True):
        if isinstance(resultado, BaseException):
            spec = PROVIDERS[nombre]
            salidas.append(
                ProviderHealth(
                    name=nombre,
                    label=spec.label,
                    kind=spec.kind.value,
                    auth=spec.auth.value,
                    status=Status.UNREACHABLE,
                    detail=f"Fallo al comprobar: {resultado}",
                    signup_url=spec.signup_url,
                    how_to=spec.how_to,
                    env_var=spec.env_var,
                )
            )
        else:
            salidas.append(resultado)
    return salidas


def resolve_env_var(name: str) -> str:
    """Variable de entorno de un proveedor, aceptando alias."""
    spec = PROVIDERS.get(name)
    if spec:
        return spec.env_var
    for candidato in PROVIDERS.values():
        if name in candidato.aliases:
            return candidato.env_var
    raise KeyError(f"Proveedor desconocido '{name}'.")
