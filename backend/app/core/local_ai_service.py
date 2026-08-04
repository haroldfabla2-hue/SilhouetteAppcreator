"""
Servicio de Autodescubrimiento e Instalación de IAs Locales (Ollama, LM Studio)
"""
import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
LM_STUDIO_BASE_URL = "http://localhost:1234"

class LocalAIService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=5.0)

    async def check_ollama(self) -> dict[str, Any]:
        """Verifica si Ollama está activo y retorna la lista de modelos instalados."""
        try:
            res = await self.client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if res.status_code == 200:
                data = res.json()
                models = [m.get("name") for m in data.get("models", [])]
                return {"online": True, "provider": "ollama", "models": models, "base_url": OLLAMA_BASE_URL}
        except Exception as e:
            logger.debug(f"Ollama no disponible en {OLLAMA_BASE_URL}: {e}")
        return {"online": False, "provider": "ollama", "models": [], "base_url": OLLAMA_BASE_URL}

    async def check_lm_studio(self) -> dict[str, Any]:
        """Verifica si LM Studio está activo (API OpenAI compatible) y retorna los modelos."""
        try:
            res = await self.client.get(f"{LM_STUDIO_BASE_URL}/v1/models")
            if res.status_code == 200:
                data = res.json()
                models = [m.get("id") for m in data.get("data", [])]
                return {"online": True, "provider": "lm_studio", "models": models, "base_url": f"{LM_STUDIO_BASE_URL}/v1"}
        except Exception as e:
            logger.debug(f"LM Studio no disponible en {LM_STUDIO_BASE_URL}: {e}")
        return {"online": False, "provider": "lm_studio", "models": [], "base_url": f"{LM_STUDIO_BASE_URL}/v1"}

    async def discover_all(self) -> list[dict[str, Any]]:
        """Descubre todas las IAs locales disponibles simultáneamente."""
        results = await asyncio.gather(self.check_ollama(), self.check_lm_studio())
        return [r for r in results if r["online"]]

    async def pull_ollama_model(self, model_name: str):
        """Descarga e instala un nuevo modelo en Ollama en segundo plano."""
        try:
            async with httpx.AsyncClient(timeout=1800.0) as long_client:
                response = await long_client.post(
                    f"{OLLAMA_BASE_URL}/api/pull",
                    json={"name": model_name, "stream": False}
                )
                if response.status_code == 200:
                    return {"success": True, "message": f"Modelo {model_name} descargado e instalado en Ollama con éxito."}
                else:
                    return {"success": False, "error": f"Error {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

local_ai_service = LocalAIService()
