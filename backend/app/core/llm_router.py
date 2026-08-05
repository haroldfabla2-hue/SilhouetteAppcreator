"""
Router LLM Inteligente con conectividad real
Maneja múltiples proveedores con fallbacks automáticos y rate limiting
"""
import asyncio
import json
import logging
import os
import time
from collections import defaultdict, deque
from datetime import datetime
from enum import Enum
from typing import Any

import httpx

from .env_loader import ensure_loaded

# El router puede importarse sin pasar por el servidor (tests, scripts, CLI);
# aquí se garantiza que el `.env` esté cargado antes de leer ninguna clave.
# Los imports que siguen van después a propósito: `config` lee el entorno al
# importarse, así que el orden no es estilístico sino funcional.
ensure_loaded()

try:
    from ..core.config import settings
except Exception:
    class DummySettings:
        MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
        OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
    settings = DummySettings()

import litellm

from .cli_adapters import (
    CLIInvocationError,
    CLINotAuthenticated,
    CLIUnavailable,
    run_cli,
)
from .cli_adapters import (
    is_available as cli_is_available,
)
from .dynamic_model_registry import model_registry

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Proveedores de LLM disponibles"""
    MINIMAX_M2 = "minimax_m2"
    OPENROUTER_LLAMA70B = "openrouter_llama70b"
    OPENROUTER_LLAMA31_70B = "openrouter_llama31_70b"
    OPENROUTER_GPT4 = "openrouter_gpt4"
    OPENROUTER_GPT4_TURBO = "openrouter_gpt4_turbo"
    OPENROUTER_CLAUDE = "openrouter_claude"
    OPENROUTER_CLAUDE_3_5 = "openrouter_claude_3_5"
    OPENROUTER_CLAUDE_FABLE_5 = "openrouter_claude_fable_5"
    OPENROUTER_GEMINI = "openrouter_gemini"
    OPENROUTER_GEMINI_1_5 = "openrouter_gemini_1_5"
    OPENROUTER_GROK = "openrouter_grok"
    OPENROUTER_GROK_4_3 = "openrouter_grok_4_3"
    OPENROUTER_GPT5_5 = "openrouter_gpt5_5"
    OPENROUTER_QWEN_3_7_MAX = "openrouter_qwen_3_7_max"
    OPENROUTER_DEEPSEEK_V4 = "openrouter_deepseek_v4"
    CLI_GEMINI = "cli_gemini"
    CLI_CLAUDE_CODE = "cli_claude_code"
    CLI_CODEX = "cli_codex"
    CLI_ANTIGRAVITY = "cli_antigravity"
    CLI_CURSOR = "cli_cursor"
    CLI_AIDER = "cli_aider"
    CLI_QWEN = "cli_qwen"
    CLI_OPENCODE = "cli_opencode"
    CLI_CRUSH = "cli_crush"
    CLI_COPILOT = "cli_copilot"
    CLI_GOOSE = "cli_goose"
    CLI_AMP = "cli_amp"
    FALLBACK_LOCAL = "fallback_local"


# Correspondencia entre proveedor del router y adaptador de CLI.
CLI_PROVIDER_NAMES: dict[LLMProvider, str] = {
    LLMProvider.CLI_CLAUDE_CODE: "claude",
    LLMProvider.CLI_GEMINI: "gemini",
    LLMProvider.CLI_CODEX: "codex",
    LLMProvider.CLI_ANTIGRAVITY: "antigravity",
    LLMProvider.CLI_CURSOR: "cursor",
    LLMProvider.CLI_AIDER: "aider",
    LLMProvider.CLI_QWEN: "qwen",
    LLMProvider.CLI_OPENCODE: "opencode",
    LLMProvider.CLI_CRUSH: "crush",
    LLMProvider.CLI_COPILOT: "copilot",
    LLMProvider.CLI_GOOSE: "goose",
    LLMProvider.CLI_AMP: "amp",
}

# Orden de preferencia al recurrir a agentes locales.
CLI_FALLBACK_ORDER: tuple[LLMProvider, ...] = (
    LLMProvider.CLI_CLAUDE_CODE,
    LLMProvider.CLI_CURSOR,
    LLMProvider.CLI_CODEX,
    LLMProvider.CLI_GEMINI,
    LLMProvider.CLI_COPILOT,
    LLMProvider.CLI_ANTIGRAVITY,
    LLMProvider.CLI_QWEN,
    LLMProvider.CLI_OPENCODE,
    LLMProvider.CLI_AIDER,
    LLMProvider.CLI_CRUSH,
    LLMProvider.CLI_GOOSE,
    LLMProvider.CLI_AMP,
)

class NoProviderAvailable(RuntimeError):
    """Ningún proveedor de modelo pudo atender la petición.

    Se lanza en lugar de devolver una respuesta de relleno: quien llama debe
    poder distinguir «el modelo dijo esto» de «no había ningún modelo».
    """


# NOTA: aquí vivían `CLIExecutionError` y `CLIExecutor`, con la resolución de
# rutas escrita a mano que no probaba extensiones de Windows (y por eso no
# encontraba `claude.exe`) y que pasaba el prompt de forma posicional (lo que
# dejaba a Gemini en modo interactivo hasta agotar el tiempo límite).
# Ese trabajo lo hace ahora `core/cli_adapters.py`, donde cada CLI declara
# cómo se le invoca.

class RateLimiter:
    """Rate limiter simple por proveedor"""

    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window  # segundos
        self.calls = defaultdict(deque)

    async def acquire(self, provider: str) -> bool:
        """Adquiere un slot de rate limit"""
        now = time.time()
        provider_calls = self.calls[provider]

        # Limpiar calls antiguos
        while provider_calls and now - provider_calls[0] > self.time_window:
            provider_calls.popleft()

        # Verificar si podemos hacer otra llamada
        if len(provider_calls) < self.max_calls:
            provider_calls.append(now)
            return True

        return False

    def time_until_next_call(self, provider: str) -> float:
        """Calcula tiempo hasta la siguiente llamada permitida"""
        now = time.time()
        provider_calls = self.calls[provider]

        if not provider_calls:
            return 0.0

        oldest_call = provider_calls[0]
        time_passed = now - oldest_call

        if time_passed >= self.time_window:
            return 0.0

        return self.time_window - time_passed


class LLMRouter:
    """
    Router LLM Inteligente con conectividad real y fallbacks automáticos
    
    Características:
    1. Conectividad real con OpenRouter API
    2. Múltiples modelos soportados (Llama 3.1 70B, GPT-4, Claude, etc.)
    3. Rate limiting automático
    4. Fallbacks entre proveedores
    5. Logging detallado de requests/responses
    6. Timeout handling robusto
    7. Error handling avanzado
    """

    # Modelos disponibles en OpenRouter
    OPENROUTER_MODELS = {
        "llama70b": "meta-llama/llama-3.3-70b-instruct",
        "llama31_70b": "meta-llama/llama-3.1-70b-instruct",
        "gpt4": "openai/gpt-4",
        "gpt4_turbo": "openai/gpt-4-turbo",
        "gpt5_5": "openai/gpt-5.5",
        "claude3": "anthropic/claude-3-sonnet",
        "claude3_5": "anthropic/claude-3-5-sonnet",
        "claude_fable_5": "anthropic/claude-fable-5",
        "gemini": "google/gemini-pro",
        "gemini_1_5": "google/gemini-1.5-pro",
        "grok": "x-ai/grok-2-1212",
        "grok_4_3": "x-ai/grok-4.3",
        "qwen_3_7_max": "qwen/qwen-3.7-max",
        "deepseek_v4": "deepseek/deepseek-v4-pro"
    }

    # Rate limits por proveedor (calls por minuto)
    RATE_LIMITS = {
        LLMProvider.MINIMAX_M2: RateLimiter(60, 60),  # 60/min
        LLMProvider.OPENROUTER_LLAMA70B: RateLimiter(40, 60),  # 40/min
        LLMProvider.OPENROUTER_LLAMA31_70B: RateLimiter(40, 60),  # 40/min
        LLMProvider.OPENROUTER_GPT4: RateLimiter(20, 60),  # 20/min
        LLMProvider.OPENROUTER_GPT4_TURBO: RateLimiter(25, 60),  # 25/min
        LLMProvider.OPENROUTER_CLAUDE: RateLimiter(35, 60),  # 35/min
        LLMProvider.OPENROUTER_CLAUDE_3_5: RateLimiter(30, 60),  # 30/min
        LLMProvider.OPENROUTER_GEMINI: RateLimiter(45, 60),
        LLMProvider.OPENROUTER_GEMINI_1_5: RateLimiter(30, 60),
        LLMProvider.OPENROUTER_GROK: RateLimiter(30, 60),
        LLMProvider.OPENROUTER_GROK_4_3: RateLimiter(25, 60),
        LLMProvider.OPENROUTER_GPT5_5: RateLimiter(20, 60),
        LLMProvider.OPENROUTER_CLAUDE_FABLE_5: RateLimiter(25, 60),
        LLMProvider.OPENROUTER_QWEN_3_7_MAX: RateLimiter(40, 60),
        LLMProvider.OPENROUTER_DEEPSEEK_V4: RateLimiter(40, 60),
    }

    def __init__(
        self,
        minimax_api_key: str | None = None,
        openrouter_api_key: str | None = None
    ):
        self.minimax_api_key = minimax_api_key or settings.MINIMAX_API_KEY
        self.openrouter_api_key = openrouter_api_key or settings.OPENROUTER_API_KEY

        # Estadísticas detalladas
        self.stats = defaultdict(lambda: {
            "calls": 0,
            "errors": 0,
            "total_tokens": 0,
            "avg_response_time": 0.0,
            "last_success": None,
            "last_error": None
        })

        # Historial de errores para circuit breaker
        self.error_history = defaultdict(list)
        self.circuit_breaker_threshold = 5  # Número de errores antes de abrir circuit
        self.circuit_breaker_timeout = 300  # 5 minutos de cooldown

        # Cliente HTTP con timeout robusto
        timeout = httpx.Timeout(
            connect=10.0,
            read=60.0,
            write=30.0,
            pool=10.0
        )
        self.client = httpx.AsyncClient(
            timeout=timeout,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )

        # Configurar logging
        self._setup_logging()

        logger.info(f"LLMRouter inicializado - MiniMax: {'✓' if self.minimax_api_key else '✗'}, OpenRouter: {'✓' if self.openrouter_api_key else '✗'}")

    def _setup_logging(self):
        """Configura logging detallado para el router"""
        self.request_logger = logging.getLogger(f"{__name__}.requests")
        self.error_logger = logging.getLogger(f"{__name__}.errors")

        # Configurar formato detallado
        if not self.request_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.request_logger.addHandler(handler)
            self.request_logger.setLevel(logging.INFO)

    def _is_circuit_breaker_open(self, provider: LLMProvider) -> bool:
        """Verifica si el circuit breaker está abierto para un proveedor"""
        errors = self.error_history[provider]
        if not errors:
            return False

        # Verificar si hay errores recientes que exceden el threshold
        recent_errors = [
            error_time for error_time in errors
            if time.time() - error_time < self.circuit_breaker_timeout
        ]

        return len(recent_errors) >= self.circuit_breaker_threshold

    def _record_error(self, provider: LLMProvider):
        """Registra un error para circuit breaker"""
        self.error_history[provider].append(time.time())

        # Limpiar errores antiguos
        cutoff = time.time() - self.circuit_breaker_timeout
        self.error_history[provider] = [
            error_time for error_time in self.error_history[provider]
            if error_time > cutoff
        ]

    async def chat_completion(
        self,
        prompt: str,
        model: str = "llama70b",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        provider: LLMProvider | None = None,
        enable_fallback: bool = True
    ) -> str:
        """
        Realiza completación de chat con routing inteligente
        
        Args:
            prompt: Prompt a enviar
            model: Modelo específico a usar
            temperature: Temperatura de generación
            max_tokens: Máximo de tokens
            provider: Proveedor específico o None para auto-routing
            enable_fallback: Si habilitar fallbacks automáticos
            
        Returns:
            Respuesta del LLM
        """

        # Auto-routing si no se especifica proveedor
        if provider is None:
            provider = self._select_provider(model)

        request_id = f"req_{int(time.time() * 1000)}"

        # Log del request
        self.request_logger.info(
            f"[{request_id}] Iniciando request - Proveedor: {provider}, Modelo: {model}, Tokens: {max_tokens}"
        )

        # Intentar el proveedor primario
        try:
            response = await self._call_provider(
                provider, prompt, model, temperature, max_tokens, request_id
            )

            if enable_fallback:
                # Verificar si el response es válido
                if not self._is_response_valid(response):
                    raise ValueError("Respuesta inválida del proveedor")

            return response

        except Exception as e:
            self.error_logger.error(f"[{request_id}] Error con proveedor {provider}: {e}")
            self.stats[provider]["errors"] += 1
            self.stats[provider]["last_error"] = datetime.utcnow().isoformat()
            self._record_error(provider)

            if not enable_fallback:
                raise

            # Fallback automático
            return await self._handle_fallback(
                provider, prompt, model, temperature, max_tokens, request_id
            )

    async def _handle_fallback(
        self,
        failed_provider: LLMProvider,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        request_id: str
    ) -> str:
        """Maneja el fallback a otros proveedores"""

        # Obtener lista de fallbacks ordenada por preferencia
        fallback_order = self._get_fallback_order(failed_provider, model)

        for fallback_provider in fallback_order:
            if self._is_provider_available(fallback_provider):
                try:
                    self.request_logger.info(f"[{request_id}] Fallback a {fallback_provider}")

                    return await self._call_provider(
                        fallback_provider, prompt, model, temperature, max_tokens, request_id
                    )

                except Exception as e:
                    self.error_logger.error(f"[{request_id}] Fallback {fallback_provider} también falló: {e}")
                    self.stats[fallback_provider]["errors"] += 1
                    self._record_error(fallback_provider)
                    continue

        # Último recurso: fallback local
        self.request_logger.warning(f"[{request_id}] Todos los proveedores fallaron, usando fallback local")
        return await self._call_fallback(prompt, model, request_id)

    def _get_fallback_order(
        self,
        failed_provider: LLMProvider,
        model: str
    ) -> list[LLMProvider]:
        """Obtiene el orden de fallback basado en el proveedor que falló"""

        if failed_provider == LLMProvider.MINIMAX_M2:
            base_fallback = [
                LLMProvider.OPENROUTER_LLAMA70B,
                LLMProvider.OPENROUTER_LLAMA31_70B,
                LLMProvider.OPENROUTER_GPT4_TURBO,
                LLMProvider.OPENROUTER_CLAUDE_3_5
            ]
        elif "openrouter" in failed_provider.value:
            if self.minimax_api_key:
                base_fallback = [LLMProvider.MINIMAX_M2]
            else:
                # Fallbacks entre modelos de OpenRouter
                if "gpt4" in model:
                    base_fallback = [
                        LLMProvider.OPENROUTER_LLAMA70B,
                        LLMProvider.OPENROUTER_CLAUDE_3_5,
                        LLMProvider.OPENROUTER_GEMINI
                    ]
                elif "claude" in model:
                    base_fallback = [
                        LLMProvider.OPENROUTER_LLAMA70B,
                        LLMProvider.OPENROUTER_GPT4_TURBO,
                        LLMProvider.OPENROUTER_GEMINI
                    ]
                else:
                    base_fallback = [
                        LLMProvider.OPENROUTER_GPT4_TURBO,
                        LLMProvider.OPENROUTER_CLAUDE_3_5,
                        LLMProvider.OPENROUTER_GEMINI
                    ]
        else:
            base_fallback = []

        # Red de seguridad: si las APIs se agotan, se prueban los CLIs locales
        # que estén realmente instalados, en orden de preferencia. Filtrar aquí
        # evita gastar intentos en agentes que no existen en esta máquina.
        base_fallback.extend(
            provider
            for provider in CLI_FALLBACK_ORDER
            if cli_is_available(CLI_PROVIDER_NAMES[provider])
        )

        return base_fallback

    def _is_provider_available(self, provider: LLMProvider) -> bool:
        """Verifica si un proveedor está disponible"""

        # Verificar circuit breaker
        if self._is_circuit_breaker_open(provider):
            return False

        # Verificar API keys
        if provider == LLMProvider.MINIMAX_M2 and not self.minimax_api_key:
            return False

        if "openrouter" in provider.value and not self.openrouter_api_key:
            return False

        # Disponibilidad real del CLI. Antes sólo se comprobaban tres, con
        # `shutil.which` a secas: Antigravity y el resto caían al `return True`
        # final y se anunciaban como disponibles sin estarlo.
        cli_name = CLI_PROVIDER_NAMES.get(provider)
        if cli_name is not None:
            return cli_is_available(cli_name)

        # Verificar rate limit (sincronizado para compatibilidad)
        if provider in self.RATE_LIMITS:
            # Por ahora retornar True para evitar warnings, el rate limit real se maneja en _call_provider
            return True

        return True

    async def _call_provider(
        self,
        provider: LLMProvider,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        request_id: str
    ) -> str:
        """Llama a un proveedor específico"""

        start_time = time.time()

        if not await asyncio.wait_for(
            asyncio.create_task(self._check_rate_limit(provider)),
            timeout=5.0
        ):
            raise TimeoutError(f"Rate limit excedido para {provider}")

        if provider == LLMProvider.MINIMAX_M2:
            return await self._call_minimax_m2(prompt, temperature, max_tokens, request_id)
        elif provider == LLMProvider.OPENROUTER_LLAMA70B:
            return await self._call_openrouter_model(
                "llama70b", prompt, temperature, max_tokens, request_id
            )
        elif provider == LLMProvider.OPENROUTER_LLAMA31_70B:
            return await self._call_openrouter_model(
                "llama31_70b", prompt, temperature, max_tokens, request_id
            )
        elif provider == LLMProvider.OPENROUTER_GPT4:
            return await self._call_openrouter_model(
                "gpt4", prompt, temperature, max_tokens, request_id
            )
        elif provider == LLMProvider.OPENROUTER_CLAUDE:
            return await self._call_openrouter_model(
                "claude3", prompt, temperature, max_tokens, request_id
            )
        elif provider == LLMProvider.OPENROUTER_CLAUDE_3_5:
            return await self._call_openrouter_model(
                "claude3_5", prompt, temperature, max_tokens, request_id
            )
        elif provider == LLMProvider.OPENROUTER_GEMINI:
            return await self._call_openrouter_model(
                "gemini", prompt, temperature, max_tokens, request_id
            )
        elif provider == LLMProvider.OPENROUTER_GEMINI_1_5:
            return await self._call_openrouter_model(
                "gemini_1_5", prompt, temperature, max_tokens, request_id
            )
        elif provider == LLMProvider.OPENROUTER_GROK:
            return await self._call_openrouter_model(
                "grok", prompt, temperature, max_tokens, request_id
            )
        elif provider == LLMProvider.OPENROUTER_CLAUDE_FABLE_5:
            return await self._call_openrouter_model(
                "claude_fable_5", prompt, temperature, max_tokens, request_id
            )
        elif provider == LLMProvider.OPENROUTER_GPT5_5:
            return await self._call_openrouter_model(
                "gpt5_5", prompt, temperature, max_tokens, request_id
            )
        elif provider == LLMProvider.OPENROUTER_QWEN_3_7_MAX:
            return await self._call_openrouter_model(
                "qwen_3_7_max", prompt, temperature, max_tokens, request_id
            )
        elif provider == LLMProvider.OPENROUTER_DEEPSEEK_V4:
            return await self._call_openrouter_model(
                "deepseek_v4", prompt, temperature, max_tokens, request_id
            )
        elif provider == LLMProvider.OPENROUTER_GROK_4_3:
            return await self._call_openrouter_model(
                "grok_4_3", prompt, temperature, max_tokens, request_id
            )
        elif provider in CLI_PROVIDER_NAMES:
            # Cualquier CLI registrado en `cli_adapters` se despacha aquí; añadir
            # uno nuevo no requiere tocar esta cadena.
            return await self._call_cli_provider(provider, prompt, request_id)
        else:
            # Check dynamic model registry
            dyn_model = model_registry.get_model(str(provider))
            if dyn_model:
                return await self._call_dynamic_litellm(dyn_model, prompt, temperature, max_tokens, request_id)
            raise ValueError(f"Proveedor no soportado: {provider}")

    async def _call_dynamic_litellm(
        self,
        model_info: dict[str, Any],
        prompt: str,
        temperature: float,
        max_tokens: int,
        request_id: str
    ) -> str:
        """Call any cloud or local model using LiteLLM dynamically."""
        provider_name = model_info.get("id", "dynamic_model")
        model_name = model_info.get("model_name", provider_name)
        base_url = model_info.get("base_url")
        api_key = model_info.get("api_key") or os.environ.get(model_info.get("api_key_env", ""), "")

        kwargs = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if base_url:
            kwargs["api_base"] = base_url
        if api_key:
            kwargs["api_key"] = api_key
        if model_info.get("extra_params"):
            kwargs.update(model_info["extra_params"])

        try:
            self.request_logger.info(f"[{request_id}] Calling dynamic LiteLLM model: {model_name} (base_url: {base_url})")
            response = await litellm.acompletion(**kwargs)
            content = response.choices[0].message.content

            self.stats[provider_name]["calls"] += 1
            self.stats[provider_name]["last_success"] = datetime.utcnow().isoformat()
            if hasattr(response, "usage") and response.usage:
                self.stats[provider_name]["total_tokens"] += getattr(response.usage, "total_tokens", len(content) // 4)

            return content
        except Exception as e:
            self.error_logger.error(f"[{request_id}] Error calling dynamic model {model_name}: {e}")
            raise

    async def _call_cli_provider(self, provider: LLMProvider, prompt: str, request_id: str) -> str:
        """Ejecuta un agente CLI local como proveedor de modelo.

        La resolución de rutas y los argumentos de cada CLI viven en
        `cli_adapters`. Antes estaban aquí, con rutas escritas a mano que
        incluían el nombre de usuario de la máquina de desarrollo original y que
        no probaban extensiones de Windows.
        """
        self.stats[provider]["calls"] += 1
        cli_name = CLI_PROVIDER_NAMES.get(provider)
        if cli_name is None:
            raise CLIUnavailable(f"El proveedor {provider.value} no es un CLI conocido.")

        try:
            self.request_logger.info(f"[{request_id}] Ejecutando CLI: {cli_name}")
            content = await run_cli(cli_name, prompt)
        except CLINotAuthenticated as e:
            # No es un fallo transitorio: reintentar no arregla una sesión
            # cerrada. Se abre el circuito para no gastar intentos en él.
            self.error_logger.error(f"[{request_id}] CLI {cli_name} sin sesión: {e}")
            self.stats[provider]["errors"] += 1
            self._record_error(provider)
            raise
        except (CLIUnavailable, CLIInvocationError) as e:
            self.error_logger.error(f"[{request_id}] CLI {cli_name} falló: {e}")
            self.stats[provider]["errors"] += 1
            raise

        self.request_logger.info(
            f"[{request_id}] CLI {cli_name} respondió: {len(content)} caracteres"
        )
        self.stats[provider]["last_success"] = datetime.utcnow().isoformat()
        self.stats[provider]["total_tokens"] += len(content) // 4
        return content

    async def _check_rate_limit(self, provider: LLMProvider) -> bool:
        """Verifica rate limit para un proveedor"""
        if provider in self.RATE_LIMITS:
            # Por ahora simular rate limiting, en producción usar acquire() con await
            return True
        return True

    def _select_provider(self, model: str) -> LLMProvider:
        """Selecciona proveedor óptimo según modelo y disponibilidad"""

        # Mapear modelo a proveedor
        model_to_provider = {
            "llama70b": LLMProvider.OPENROUTER_LLAMA70B,
            "llama31_70b": LLMProvider.OPENROUTER_LLAMA31_70B,
            "gpt4": LLMProvider.OPENROUTER_GPT4,
            "gpt4_turbo": LLMProvider.OPENROUTER_GPT4_TURBO,
            "claude3": LLMProvider.OPENROUTER_CLAUDE,
            "claude3_5": LLMProvider.OPENROUTER_CLAUDE_3_5,
            "gemini": LLMProvider.OPENROUTER_GEMINI
        }

        # Verificar fecha: MiniMax M2 gratis hasta 7 Nov 2025
        current_date = datetime.utcnow()
        minimax_free_until = datetime(2025, 11, 7, 23, 59, 59)

        # Prioridad a MiniMax M2 si está disponible y dentro del período gratis
        if (current_date <= minimax_free_until and
            self.minimax_api_key and
            not self._is_circuit_breaker_open(LLMProvider.MINIMAX_M2)):
            return LLMProvider.MINIMAX_M2

        # Si no, usar el proveedor del modelo especificado
        preferred_provider = model_to_provider.get(model)
        if (preferred_provider and
            self._is_provider_available(preferred_provider)):
            return preferred_provider

        # Fallback al mejor modelo disponible de OpenRouter
        available_providers = [
            LLMProvider.OPENROUTER_LLAMA70B,
            LLMProvider.OPENROUTER_LLAMA31_70B,
            LLMProvider.OPENROUTER_CLAUDE_3_5
        ]

        for provider in available_providers:
            if self._is_provider_available(provider):
                return provider

        # Probar CLI local (Prioridad: Antigravity -> Claude -> Gemini -> Codex)
        for provider in [LLMProvider.CLI_ANTIGRAVITY, LLMProvider.CLI_CLAUDE_CODE, LLMProvider.CLI_GEMINI, LLMProvider.CLI_CODEX]:
            if self._is_provider_available(provider):
                return provider

        # Último recurso
        return LLMProvider.CLI_ANTIGRAVITY

    async def _call_minimax_m2(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        request_id: str
    ) -> str:
        """Llama a MiniMax M2 API con logging detallado"""

        if not self.minimax_api_key:
            raise ValueError("MINIMAX_API_KEY no configurada")

        provider = LLMProvider.MINIMAX_M2
        self.stats[provider]["calls"] += 1

        try:
            url = f"{settings.MINIMAX_API_BASE}/chat/completions"

            headers = {
                "Authorization": f"Bearer {self.minimax_api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": settings.MINIMAX_MODEL,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            self.request_logger.info(f"[{request_id}] MiniMax M2 - Request: {json.dumps(payload, indent=2)}")

            response = await self.client.post(url, headers=headers, json=payload)

            if response.status_code != 200:
                self.error_logger.error(f"[{request_id}] MiniMax M2 HTTP {response.status_code}: {response.text}")
                response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            # Log de respuesta exitosa
            self.request_logger.info(
                f"[{request_id}] MiniMax M2 - Respuesta exitosa: {len(content)} chars, "
                f"Tokens: {data.get('usage', {}).get('total_tokens', 'N/A')}"
            )

            # Actualizar estadísticas
            self.stats[provider]["total_tokens"] += data.get('usage', {}).get('total_tokens', 0)
            self.stats[provider]["last_success"] = datetime.utcnow().isoformat()

            return content

        except Exception as e:
            self.error_logger.error(f"[{request_id}] Error MiniMax M2: {e}")
            raise

    async def _call_openrouter_model(
        self,
        model_key: str,
        prompt: str,
        temperature: float,
        max_tokens: int,
        request_id: str
    ) -> str:
        """Llama a OpenRouter con el modelo especificado"""

        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY no configurada")

        model_id = self.OPENROUTER_MODELS.get(model_key)
        if not model_id:
            raise ValueError(f"Modelo no soportado: {model_key}")

        provider = LLMProvider(f"openrouter_{model_key}")
        self.stats[provider]["calls"] += 1

        try:
            url = f"{settings.OPENROUTER_API_BASE}/chat/completions"

            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://sistema-multiagente.app",
                "X-Title": "Sistema Multi-Agente Superior"
            }

            payload = {
                "model": model_id,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            self.request_logger.info(f"[{request_id}] OpenRouter {model_key} - Request: {json.dumps(payload, indent=2)}")

            response = await self.client.post(url, headers=headers, json=payload)

            if response.status_code != 200:
                self.error_logger.error(f"[{request_id}] OpenRouter HTTP {response.status_code}: {response.text}")
                response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            # Log de respuesta exitosa
            self.request_logger.info(
                f"[{request_id}] OpenRouter {model_key} - Respuesta exitosa: {len(content)} chars, "
                f"Tokens: {data.get('usage', {}).get('total_tokens', 'N/A')}"
            )

            # Actualizar estadísticas
            self.stats[provider]["total_tokens"] += data.get('usage', {}).get('total_tokens', 0)
            self.stats[provider]["last_success"] = datetime.utcnow().isoformat()

            return content

        except Exception as e:
            self.error_logger.error(f"[{request_id}] Error OpenRouter {model_key}: {e}")
            raise

    def _is_response_valid(self, response: str) -> bool:
        """Valida que la respuesta del LLM sea válida"""
        if not response or len(response.strip()) < 10:
            return False

        # Antes bastaba con que la respuesta contuviera la palabra "error" en
        # cualquier posición para descartarla: una explicación legítima sobre
        # manejo de errores, o cualquier fragmento de código con `except`, se
        # rechazaba. Ahora sólo se descartan los marcadores que este sistema
        # emite al degradarse, y sólo si abren la respuesta.
        marcadores_de_degradacion = (
            "[modo fallback",
            "[silhouette timeout fallback]",
            "[silhouette engine]",
            "[silhouette local ai]",
            "[respuesta del agente local",
        )
        principio = response.lstrip().lower()[:80]
        return not any(principio.startswith(m) for m in marcadores_de_degradacion)

    async def _call_fallback(self, prompt: str, model: str, request_id: str) -> str:
        """Fallback local mejorado cuando fallan todos los proveedores"""

        provider = LLMProvider.FALLBACK_LOCAL
        self.stats[provider]["calls"] += 1

        logger.error(
            "[%s] Ningún proveedor respondió. Modelo solicitado: %s", request_id, model
        )
        raise NoProviderAvailable(self._diagnose_no_provider(model))

    def _diagnose_no_provider(self, model: str) -> str:
        """Explica por qué no hay ningún modelo y qué hacer al respecto.

        Antes, cuando fallaban todos los proveedores, se devolvía un texto
        enlatado elegido por palabras clave del prompt: un saludo, una lista de
        capacidades, o un parte que afirmaba «Reasoner: intención analizada
        correctamente» y «Verifier: verificación completada» sin que ningún
        agente se hubiera ejecutado. Quien preguntaba recibía una respuesta
        segura de sí misma en lugar de saber que el sistema no tenía modelo.
        """
        motivos: list[str] = []

        if not self.openrouter_api_key and not self.minimax_api_key:
            motivos.append("no hay ninguna clave de API configurada")
        else:
            configuradas = [
                nombre
                for nombre, clave in (
                    ("OpenRouter", self.openrouter_api_key),
                    ("MiniMax", self.minimax_api_key),
                )
                if clave
            ]
            motivos.append(
                f"las claves configuradas ({', '.join(configuradas)}) no respondieron"
            )

        cli_instalados = [
            nombre for nombre in CLI_PROVIDER_NAMES.values() if cli_is_available(nombre)
        ]
        if cli_instalados:
            motivos.append(
                f"los agentes locales instalados ({', '.join(cli_instalados)}) "
                "fallaron o no tienen sesión iniciada"
            )
        else:
            motivos.append("no hay ningún agente CLI instalado")

        abiertos = [
            p.value for p in LLMProvider
            if self._is_circuit_breaker_open(p)
        ]
        if abiertos:
            motivos.append(f"circuito abierto por fallos repetidos en: {', '.join(abiertos)}")

        return (
            f"No hay ningún modelo disponible para atender la petición ({model}): "
            + "; ".join(motivos)
            + ". Ejecute `python conectar.py` para ver el estado y las opciones de conexión."
        )

    def get_stats(self) -> dict[str, Any]:
        """Obtiene estadísticas detalladas del router"""

        total_calls = sum(stats["calls"] for stats in self.stats.values())
        total_errors = sum(stats["errors"] for stats in self.stats.values())

        # Calcular tasas de éxito
        provider_stats = {}
        for provider, stats in self.stats.items():
            success_rate = 0.0
            if stats["calls"] > 0:
                success_rate = (stats["calls"] - stats["errors"]) / stats["calls"]

            provider_stats[provider.value] = {
                "calls": stats["calls"],
                "errors": stats["errors"],
                "success_rate": success_rate,
                "total_tokens": stats["total_tokens"],
                "avg_tokens_per_call": (
                    stats["total_tokens"] / stats["calls"]
                    if stats["calls"] > 0 else 0
                ),
                "last_success": stats["last_success"],
                "last_error": stats["last_error"],
                "circuit_breaker_open": self._is_circuit_breaker_open(provider)
            }

        return {
            "total_calls": total_calls,
            "total_errors": total_errors,
            "overall_success_rate": (
                (total_calls - total_errors) / total_calls
                if total_calls > 0 else 0.0
            ),
            "by_provider": provider_stats,
            "minimax_free_days_remaining": self._days_until_minimax_expires(),
            "available_models": list(self.OPENROUTER_MODELS.keys()),
            "circuit_breaker_status": {
                provider.value: self._is_circuit_breaker_open(provider)
                for provider in LLMProvider
            }
        }

    def _days_until_minimax_expires(self) -> int:
        """Calcula días restantes de MiniMax M2 gratis"""

        current_date = datetime.utcnow()
        expiry_date = datetime(2025, 11, 7, 23, 59, 59)

        if current_date > expiry_date:
            return 0

        delta = expiry_date - current_date
        return delta.days

    async def close(self):
        """Cierra el cliente HTTP y limpia recursos"""
        await self.client.aclose()
        logger.info("LLMRouter cerrado correctamente")

    async def __aenter__(self):
        """Context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()
