"""
Agente base abstracto
Define la interfaz común para todos los agentes especializados
"""
import asyncio
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import httpx

from ..core import settings
from ..core.llm_router import LLMRouter
from ..models import AgentMessage, AgentResponse, ErrorInfo, MessageStatus

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Clase base abstracta para todos los agentes
    
    Cada agente especializado debe implementar:
    - process_message: lógica de procesamiento principal
    - get_capabilities: capacidades que expone
    """

    def __init__(
        self,
        agent_id: str,
        llm_client: Any = None,
        timeout: int = settings.AGENT_TIMEOUT_SECONDS
    ):
        self.agent_id = agent_id
        self.llm_client = llm_client or self._init_llm_router()
        self.timeout = timeout
        self.logger = logging.getLogger(f"agent.{agent_id}")
        self._init_tools()

    def _init_llm_router(self):
        """Inicializa el router LLM con conectividad real"""
        try:
            return LLMRouter()
        except Exception as e:
            self.logger.warning(f"No se pudo inicializar LLMRouter: {e}")
            return None

    def _init_tools(self):
        """Inicializa herramientas del sistema"""
        try:
            # Las herramientas se inicializan de forma lazy cuando se necesitan
            # Esto evita importaciones de módulos que pueden no existir
            self.tools = {}
            self.logger.info("Sistema de herramientas preparado (inicialización lazy)")
        except Exception as e:
            self.logger.error(f"Error inicializando herramientas: {e}")
            self.tools = {}

    @abstractmethod
    async def process_message(self, message: AgentMessage) -> AgentResponse:
        """
        Procesa un mensaje y retorna una respuesta
        
        Args:
            message: Mensaje a procesar
            
        Returns:
            AgentResponse con el resultado o error
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """
        Retorna la lista de capacidades del agente
        
        Returns:
            Lista de strings describiendo capacidades
        """
        pass

    async def execute_with_timeout(
        self,
        message: AgentMessage
    ) -> AgentResponse:
        """
        Ejecuta el procesamiento del mensaje con timeout
        
        Args:
            message: Mensaje a procesar
            
        Returns:
            AgentResponse con resultado o error de timeout
        """
        start_time = datetime.utcnow()

        try:
            # Aplicar timeout
            result = await asyncio.wait_for(
                self.process_message(message),
                timeout=self.timeout
            )

            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time

            return result

        except asyncio.TimeoutError:
            self.logger.error(f"Timeout procesando mensaje {message.message_id}")

            return AgentResponse(
                message_id=f"resp_{message.message_id}",
                original_message_id=message.message_id,
                agent_id=self.agent_id,
                status=MessageStatus.TIMEOUT,
                errors=[ErrorInfo(
                    code="AGENT_TIMEOUT",
                    message=f"Agente {self.agent_id} excedió timeout de {self.timeout}s",
                    retryable=True,
                    retry_after=5
                )]
            )

        except Exception as e:
            self.logger.exception(f"Error procesando mensaje {message.message_id}")

            return AgentResponse(
                message_id=f"resp_{message.message_id}",
                original_message_id=message.message_id,
                agent_id=self.agent_id,
                status=MessageStatus.ERROR,
                errors=[ErrorInfo(
                    code="AGENT_ERROR",
                    message=str(e),
                    retryable=False
                )]
            )

    async def call_llm(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        model: str = "claude3_5",
        session: Any = None,
    ) -> str:
        """Llama al modelo respetando la política del agente y la sesión.

        Dos comportamientos nuevos, ambos porque antes se afirmaban sin existir:

        - **Modelo por agente.** Si hay una política declarada y su proveedor
          preferido está disponible, se usa ese. Antes los cinco agentes caían
          siempre en el mismo proveedor de la cadena general.
        - **Contexto de sesión.** Con `session`, el prompt se compone con lo que
          han aportado los demás agentes y con lo que la memoria recuerde del
          objetivo. Antes cada llamada partía de cero.
        """
        from backend.app.core.agent_models import agent_models

        politica = agent_models.policy_for(self.agent_id)
        temperatura = politica.temperature if temperature is None else temperature
        limite = politica.max_tokens if max_tokens is None else max_tokens

        try:
            if self.llm_client and hasattr(self.llm_client, 'chat_completion'):
                proveedor = agent_models.resolve_provider(self.agent_id, self.llm_client)

                if session is not None:
                    from backend.app.core.session import session_manager

                    async def _ejecutar(prompt_compuesto: str) -> str:
                        return await self.llm_client.chat_completion(
                            prompt=prompt_compuesto,
                            model=model,
                            temperature=temperatura,
                            max_tokens=limite,
                            provider=proveedor,
                            enable_fallback=politica.allow_fallback,
                        )

                    return await session_manager.run_with_context(
                        session,
                        self.agent_id,
                        prompt,
                        _ejecutar,
                        model=proveedor.value if proveedor is not None else model,
                    )

                response = await self.llm_client.chat_completion(
                    prompt=prompt,
                    model=model,
                    temperature=temperatura,
                    max_tokens=limite,
                    provider=proveedor,
                    enable_fallback=politica.allow_fallback,
                )
                self.logger.debug(f"LLM response received ({len(response)} chars)")
                return response
            else:
                # Fallback directo a OpenRouter
                return await self._call_openrouter_direct(prompt, temperature, max_tokens, model)

        except Exception as e:
            # Se propaga en lugar de devolver un texto de error como si fuera la
            # respuesta del modelo. Devolverlo hacía que el agente siguiera
            # trabajando sobre «[Error LLM - Fallback para: …]» tratándolo como
            # contenido válido, y el fallo acababa reportado como éxito.
            self.logger.exception("Error en llamada LLM: %s", e)
            raise

    async def _call_openrouter_direct(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        model: str
    ) -> str:
        """Llamada directa a OpenRouter como fallback"""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return f"[Fallback - Sin API key para: {prompt[:100]}...]"

        model_mapping = {
            "claude3_5": "anthropic/claude-3-5-sonnet",
            "claude3": "anthropic/claude-3-sonnet",
            "llama70b": "meta-llama/llama-3.3-70b-instruct",
            "gpt4": "openai/gpt-4",
            "gpt4_turbo": "openai/gpt-4-turbo"
        }

        actual_model = model_mapping.get(model, "anthropic/claude-3-5-sonnet")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://agents-backend",
            "X-Title": "Agents Backend"
        }

        payload = {
            "model": actual_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        timeout = httpx.Timeout(60.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            else:
                raise ValueError(f"Respuesta inesperada: {data}")

    async def call_tool(self, tool_name: str, **kwargs) -> dict[str, Any]:
        """
        Llama a una herramienta del sistema
        
        Args:
            tool_name: Nombre de la herramienta
            **kwargs: Argumentos para la herramienta
            
        Returns:
            Resultado de la herramienta
        """
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Herramienta no encontrada: {tool_name}",
                "available_tools": list(self.tools.keys())
            }

        try:
            tool = self.tools[tool_name]
            self.logger.info(f"Ejecutando herramienta {tool_name}")

            # Ejecutar herramienta según su interfaz
            if hasattr(tool, 'execute'):
                result = tool.execute(**kwargs)
                return {
                    "success": result.success if hasattr(result, 'success') else True,
                    "data": result.data if hasattr(result, 'data') else result,
                    "error": getattr(result, 'error', None),
                    "tool": tool_name
                }
            else:
                return {
                    "success": False,
                    "error": f"Herramienta {tool_name} no tiene método execute",
                    "tool": tool_name
                }

        except Exception as e:
            self.logger.exception(f"Error ejecutando herramienta {tool_name}")
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name
            }

    def log_trace(self, event: str, data: dict[str, Any] | None = None):
        """
        Registra evento de traza para observabilidad
        
        Args:
            event: Nombre del evento
            data: Datos adicionales opcionales
        """
        trace_data = {
            "agent_id": self.agent_id,
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
            **(data or {})
        }

        self.logger.info(f"TRACE: {trace_data}")
