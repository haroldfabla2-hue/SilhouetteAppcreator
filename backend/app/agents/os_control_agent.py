import asyncio
import logging
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

import psutil

if TYPE_CHECKING:
    from backend.app.security.process_policy import LaunchPlan

logger = logging.getLogger("OSControlAgent")

class OSControlAgent:
    """
    Agente de Control del Sistema Operativo & Aplicaciones Locales.
    Permite abrir y gestionar aplicaciones del SO (Windows/Linux/macOS),
    gestionar procesos en ejecución y automatizar navegación web mediante Playwright en vivo.
    """

    def __init__(self, artifacts_dir: str = "artifacts/browser"):
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"OSControlAgent inicializado. Artefactos web en: {self.artifacts_dir}")

    async def launch_plan(self, plan: "LaunchPlan") -> dict[str, Any]:
        """Ejecuta un `LaunchPlan` ya validado por `security.process_policy`.

        Este método NO valida: espera que la lista blanca y el saneado de
        argumentos se hayan aplicado antes. Es el único camino de lanzamiento.
        """
        logger.info("[OS Control] Lanzando '%s' (%s)", plan.app_name, plan.executable)
        try:
            process = subprocess.Popen(
                plan.argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False
            )
        except OSError as e:
            logger.error("[OS Control] Error lanzando %s: %s", plan.app_name, e)
            return {"success": False, "app": plan.app_name, "error": str(e)}

        return {
            "success": True,
            "app": plan.app_name,
            "pid": process.pid,
            "message": f"Aplicación '{plan.app_name}' lanzada con PID {process.pid}",
        }

    async def launch_application(self, app_name: str, args: str | None = None) -> dict[str, Any]:
        """Valida contra la lista blanca y lanza la aplicación.

        Conveniencia para quien llama desde dentro del proceso; la validación es
        la misma que aplica la API.
        """
        from backend.app.security.process_policy import (
            AppNotAllowed,
            ArgumentRejected,
            plan_launch,
        )

        try:
            plan = plan_launch(app_name, args)
        except (AppNotAllowed, ArgumentRejected) as exc:
            logger.warning("[OS Control] Lanzamiento rechazado (%s): %s", app_name, exc)
            return {"success": False, "app": app_name, "error": str(exc)}
        return await self.launch_plan(plan)

    async def inspect_web_browser(self, url: str, headless: bool = True, wait_seconds: int = 2) -> dict[str, Any]:
        """
        Inspecciona y automatiza navegación web en vivo mediante Playwright.
        Navega a la URL, extrae título real, métricas del DOM y genera una captura de pantalla.
        """
        logger.info(f"[OS Control - Playwright] Navegando a: {url}")

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("[OS Control] La librería 'playwright' no está instalada.")
            return {
                "success": False,
                "error": "La librería 'playwright' no está instalada. Ejecute 'pip install playwright && playwright install'"
            }

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=headless)
                context = await browser.new_context(viewport={"width": 1280, "height": 800})
                page = await context.new_page()

                # Navegar a la URL con timeout de 15s
                response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(wait_seconds)

                page_title = await page.title()
                status_code = response.status if response else 200

                # Contar elementos DOM reales
                dom_elements_count = await page.evaluate("() => document.querySelectorAll('*').length")
                links_count = await page.evaluate("() => document.querySelectorAll('a').length")
                inputs_count = await page.evaluate("() => document.querySelectorAll('input, button, select, textarea').length")

                # Generar captura de pantalla real
                screenshot_filename = f"screenshot_{int(asyncio.get_event_loop().time())}.png"
                screenshot_path = self.artifacts_dir / screenshot_filename
                await page.screenshot(path=str(screenshot_path), full_page=False)

                await browser.close()

                return {
                    "success": True,
                    "url": url,
                    "status_code": status_code,
                    "title": page_title,
                    "screenshot_path": str(screenshot_path.absolute()),
                    "dom_stats": {
                        "total_elements": dom_elements_count,
                        "links_count": links_count,
                        "interactive_inputs": inputs_count
                    }
                }
        except Exception as e:
            logger.error(f"[OS Control - Playwright] Error inspeccionando {url}: {e}")
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }

    def list_running_processes(self, filter_name: str | None = None) -> list[dict[str, Any]]:
        """Obtiene la lista de procesos activos en el sistema operativo local."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'status', 'memory_info']):
            try:
                pinfo = proc.info
                if filter_name:
                    if filter_name.lower() in pinfo['name'].lower():
                        processes.append(pinfo)
                else:
                    processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return processes[:50]  # Limitar a los primeros 50 para legibilidad

    def kill_process(self, pid: int) -> dict[str, Any]:
        """Finaliza un proceso por su PID."""
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=3)
            return {"success": True, "pid": pid, "message": f"Proceso {pid} finalizado exitosamente."}
        except Exception as e:
            return {"success": False, "pid": pid, "error": str(e)}
