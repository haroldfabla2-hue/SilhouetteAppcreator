import asyncio
import json
import logging
import os
from typing import Any

logger = logging.getLogger("StartupManager")

class StartupManager:
    def __init__(self, root_dir: str = "."):
        self.root_dir = root_dir
        self.config_dir = os.path.join(root_dir, ".silhouettemcp")
        self.config_path = os.path.join(self.config_dir, "startup.json")

    async def execute_startup_scripts(self, orchestrator):
        """Lee el archivo startup.json y lanza las tareas de inicio automáticas."""
        if not os.path.exists(self.config_path):
            logger.info(f"No startup script found at {self.config_path}")
            # Opcional: Crear uno por defecto para guiar al usuario
            self._create_default_startup()
            return

        logger.info(f"Detected startup configuration at {self.config_path}")
        try:
            with open(self.config_path, encoding="utf-8") as f:
                startup_config: dict[str, Any] = json.load(f)

            commands = startup_config.get("commands", [])
            for cmd in commands:
                logger.info(f"Auto-starting workspace task: {cmd}")

                # Lanzar en background (fire and forget) para no bloquear el inicio de FastAPI
                asyncio.create_task(
                    orchestrator.process_request(
                        objetivo=cmd,
                        contexto={"source": "auto_startup", "priority": "high"},
                        user_id="system_startup"
                    )
                )

            logger.info("Startup scripts execution triggered successfully.")

        except Exception as e:
            logger.error(f"Failed to execute startup scripts: {e}")

    def _create_default_startup(self):
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            default_config = {
                "commands": [
                    "Verificar el estado del sistema y la base de datos PostgreSQL",
                    "Inicializar entorno de Sandbox Docker si está disponible"
                ]
            }
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default startup configuration at {self.config_path}")
        except Exception as e:
            logger.warning(f"Could not create default startup config: {e}")
