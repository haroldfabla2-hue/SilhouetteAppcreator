import asyncio
import logging
import subprocess
import shutil
import os
import psutil
from typing import Dict, Any, Optional, List
from pathlib import Path

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

    async def launch_application(self, app_name: str, args: Optional[str] = None) -> Dict[str, Any]:
        """Abre una aplicación instalada en el sistema local (Windows / Linux / macOS)."""
        logger.info(f"[OS Control] Solicitando lanzamiento de app: {app_name}")
        
        executable_path = shutil.which(app_name) or app_name
        cmd = [executable_path]
        if args:
            cmd.extend(args.split())

        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return {
                "success": True,
                "app": app_name,
                "pid": process.pid,
                "executable_path": executable_path,
                "message": f"Aplicación '{app_name}' lanzada exitosamente con PID {process.pid}"
            }
        except Exception as e:
            logger.error(f"[OS Control] Error lanzando {app_name}: {e}")
            return {
                "success": False,
                "app": app_name,
                "error": str(e)
            }

    async def inspect_web_browser(self, url: str, headless: bool = True, wait_seconds: int = 2) -> Dict[str, Any]:
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

    def list_running_processes(self, filter_name: Optional[str] = None) -> List[Dict[str, Any]]:
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

    def kill_process(self, pid: int) -> Dict[str, Any]:
        """Finaliza un proceso por su PID."""
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=3)
            return {"success": True, "pid": pid, "message": f"Proceso {pid} finalizado exitosamente."}
        except Exception as e:
            return {"success": False, "pid": pid, "error": str(e)}
