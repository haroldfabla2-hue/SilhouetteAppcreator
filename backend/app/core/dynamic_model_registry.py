"""
Registro Dinámico de Modelos de IA (Cloud + Locales + Custom APIs)
Guarda la configuración de modelos en backend/app/config/custom_models.json
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent / "config" / "custom_models.json"

DEFAULT_MODELS = [
    {
        "id": "glm-5.2-max",
        "name": "GLM-5.2 (Zhipu AI - 1M Context)",
        "provider": "openai",
        "model_name": "glm-5.2",
        "base_url": "https://api.z.ai/api/paas/v4",
        "api_key_env": "ZHIPU_API_KEY",
        "context_window": 1000000,
        "is_local": False
    },
    {
        "id": "minimax-m3",
        "name": "MiniMax M3 (Multimodal Agent)",
        "provider": "openai",
        "model_name": "minimax-m3",
        "base_url": "https://api.minimax.chat/v1",
        "api_key_env": "MINIMAX_API_KEY",
        "context_window": 1000000,
        "is_local": False
    },
    {
        "id": "kimi-k3",
        "name": "Kimi K3 (Moonshot AI)",
        "provider": "openai",
        "model_name": "kimi-k3",
        "base_url": "https://api.moonshot.ai/v1",
        "api_key_env": "MOONSHOT_API_KEY",
        "extra_params": {"reasoning_effort": "max"},
        "context_window": 1000000,
        "is_local": False
    },
    {
        "id": "openrouter-qwen-3-7",
        "name": "Qwen 3.7 Max (via OpenRouter)",
        "provider": "openrouter",
        "model_name": "qwen/qwen-3.7-max",
        "api_key_env": "OPENROUTER_API_KEY",
        "context_window": 128000,
        "is_local": False
    },
    {
        "id": "openrouter-claude-fable",
        "name": "Claude Fable 5 (via OpenRouter)",
        "provider": "openrouter",
        "model_name": "anthropic/claude-fable-5",
        "api_key_env": "OPENROUTER_API_KEY",
        "context_window": 200000,
        "is_local": False
    },
    {
        "id": "cli_claude_code",
        "name": "Claude Code (Local CLI App)",
        "provider": "cli",
        "model_name": "claude",
        "is_local": True,
        "context_window": 200000
    },
    {
        "id": "cli_antigravity",
        "name": "Antigravity AGY (Local CLI App)",
        "provider": "cli",
        "model_name": "agy",
        "is_local": True,
        "context_window": 200000
    },
    {
        "id": "cli_gemini",
        "name": "Gemini CLI (Local CLI App)",
        "provider": "cli",
        "model_name": "gemini",
        "is_local": True,
        "context_window": 1000000
    },
    {
        "id": "cli_codex",
        "name": "OpenAI Codex (Local CLI App)",
        "provider": "cli",
        "model_name": "codex",
        "is_local": True,
        "context_window": 128000
    }
]

class DynamicModelRegistry:
    def __init__(self):
        self.config_file = CONFIG_PATH
        self.models: Dict[str, Dict[str, Any]] = {}
        self._load_models()

    def _load_models(self):
        """Carga modelos guardados y modelos por defecto."""
        # Cargar por defecto
        for m in DEFAULT_MODELS:
            self.models[m["id"]] = m

        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    custom_models = json.load(f)
                    for m in custom_models:
                        self.models[m["id"]] = m
            except Exception as e:
                logger.error(f"Error al cargar custom_models.json: {e}")

    def _save_models(self):
        """Guarda la configuración personalizada."""
        os.makedirs(self.config_file.parent, exist_ok=True)
        custom_list = [m for m in self.models.values() if m not in DEFAULT_MODELS or m.get("user_added")]
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(custom_list, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error al guardar custom_models.json: {e}")

    def get_all_models(self) -> List[Dict[str, Any]]:
        return list(self.models.values())

    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        return self.models.get(model_id)

    def register_model(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Registra un nuevo modelo dinámicamente."""
        model_id = model_data.get("id") or model_data["name"].lower().replace(" ", "-")
        model_entry = {
            "id": model_id,
            "name": model_data["name"],
            "provider": model_data.get("provider", "openai"),
            "model_name": model_data.get("model_name", model_id),
            "base_url": model_data.get("base_url"),
            "api_key": model_data.get("api_key"),
            "api_key_env": model_data.get("api_key_env"),
            "context_window": model_data.get("context_window", 128000),
            "is_local": model_data.get("is_local", False),
            "user_added": True
        }
        self.models[model_id] = model_entry
        self._save_models()
        return model_entry

    def remove_model(self, model_id: str) -> bool:
        if model_id in self.models:
            del self.models[model_id]
            self._save_models()
            return True
        return False

model_registry = DynamicModelRegistry()
