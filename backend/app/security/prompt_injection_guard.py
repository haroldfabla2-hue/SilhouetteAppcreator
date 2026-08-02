import logging
import re
from typing import Dict, Any

logger = logging.getLogger("PromptInjectionGuard")

class PromptInjectionGuard:
    """
    Filtro de Seguridad Anti-Prompt Injection & Guardián Omnicanal (Telegram, WhatsApp, Discord).
    Normaliza el texto de entrada, aplica patrones heurísticos Regex para firmas de jailbreak
    y clasifica amenazas vectoriales antes de enviar el prompt al orquestador principal.
    """

    JAILBREAK_PATTERNS = [
        r"ignore\s+all\s+previous\s+instructions",
        r"ignore\s+above\s+instructions",
        r"you\s+are\s+now\s+dan",
        r"system\s+prompt\s+override",
        r"disregard\s+safety\s+guidelines"
    ]

    def sanitize_and_validate(self, text: str) -> Dict[str, Any]:
        clean_text = text.strip()
        lower_text = clean_text.lower()

        for pattern in self.JAILBREAK_PATTERNS:
            if re.search(pattern, lower_text):
                logger.warning(f"[Security Guard] Prompt Injection detectado y bloqueado: {pattern}")
                return {
                    "safe": False,
                    "reason": "Patrón de ataque de inyección de prompt (Jailbreak) detectado.",
                    "sanitized_text": ""
                }

        return {
            "safe": True,
            "reason": "Prompt limpio y seguro para procesamiento.",
            "sanitized_text": clean_text
        }
