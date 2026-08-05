"""Instalación y autenticación de agentes CLI desde la aplicación.

Se afirmó que `conectar.py --instalar claude` existía y mostraba un
`[INSTALACIÓN COMPLETADA]`. No existía: el asistente sólo aceptaba `--arreglar`
y `--clave`. Aquí se implementa de verdad, y además se resuelve el problema que
lo hacía difícil: **los logins de CLI son interactivos y abren el navegador**,
así que no se pueden completar dentro de una petición HTTP.

La solución es honesta con esa restricción: en lugar de fingir que se autentica
desde el servidor, se **abre una terminal real** en la máquina del usuario con
el comando de login ya escrito. El usuario completa el OAuth en su navegador —
que es donde tiene su sesión— y el sistema detecta el resultado sondeando el
CLI. Ni se manipulan tokens de terceros ni se piden contraseñas.

Cada instalación usa el gestor de paquetes oficial del CLI. Si no está el gestor
(npm, pip…), se dice cuál falta en lugar de intentar adivinar.
"""
from __future__ import annotations

import asyncio
import logging
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger("CLIManager")

INSTALL_TIMEOUT_S = 600.0


class CLIManagerError(RuntimeError):
    """No se pudo instalar o autenticar el CLI."""


@dataclass
class InstallSpec:
    """Cómo se instala un agente CLI."""

    cli: str
    manager: str          # npm | pip | brew | winget | manual
    package: str
    docs_url: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Instaladores oficiales de cada CLI. Cuando no hay uno automatizable, se
# declara `manual` con el enlace: preferible a inventar un comando que falle.
INSTALLERS: dict[str, InstallSpec] = {
    "claude": InstallSpec(
        cli="claude", manager="npm", package="@anthropic-ai/claude-code",
        docs_url="https://docs.claude.com/en/docs/claude-code",
    ),
    "gemini": InstallSpec(
        cli="gemini", manager="npm", package="@google/gemini-cli",
        docs_url="https://github.com/google-gemini/gemini-cli",
    ),
    "codex": InstallSpec(
        cli="codex", manager="npm", package="@openai/codex",
        docs_url="https://github.com/openai/codex",
    ),
    "copilot": InstallSpec(
        cli="copilot", manager="npm", package="@github/copilot",
        docs_url="https://docs.github.com/copilot",
    ),
    "opencode": InstallSpec(
        cli="opencode", manager="npm", package="opencode-ai",
        docs_url="https://opencode.ai",
    ),
    "qwen": InstallSpec(
        cli="qwen", manager="npm", package="@qwen-code/qwen-code",
        docs_url="https://github.com/QwenLM/qwen-code",
    ),
    "aider": InstallSpec(
        cli="aider", manager="pip", package="aider-install",
        docs_url="https://aider.chat/docs/install.html",
    ),
    "goose": InstallSpec(
        cli="goose", manager="manual", package="",
        docs_url="https://block.github.io/goose/docs/getting-started/installation",
        notes="Se instala con un script oficial; requiere confirmación del usuario.",
    ),
    "cursor": InstallSpec(
        cli="cursor", manager="manual", package="",
        docs_url="https://cursor.com/cli",
        notes="`cursor-agent` se instala desde el propio Cursor o su script oficial.",
    ),
    "crush": InstallSpec(
        cli="crush", manager="npm", package="@charmland/crush",
        docs_url="https://github.com/charmbracelet/crush",
    ),
    "amp": InstallSpec(
        cli="amp", manager="npm", package="@sourcegraph/amp",
        docs_url="https://ampcode.com",
    ),
    "antigravity": InstallSpec(
        cli="antigravity", manager="manual", package="",
        docs_url="https://antigravity.google",
        notes="Se instala con la aplicación de escritorio Antigravity.",
    ),
}

# Comando de login de cada CLI y si necesita una terminal interactiva.
LOGIN_COMMANDS: dict[str, dict[str, Any]] = {
    "claude": {"args": [], "type": "slash", "slash": "/login", "interactive": True},
    "gemini": {"args": [], "type": "menu", "interactive": True,
               "hint": "Elija «Login with Google» en el menú inicial."},
    "codex": {"args": ["login"], "type": "subcommand", "interactive": False},
    "copilot": {"args": [], "type": "slash", "slash": "/login", "interactive": True},
    "cursor": {"args": ["login"], "type": "subcommand", "interactive": False},
    "qwen": {"args": [], "type": "menu", "interactive": True},
    "opencode": {"args": ["auth", "login"], "type": "subcommand", "interactive": False},
    "goose": {"args": ["configure"], "type": "subcommand", "interactive": True},
    "crush": {"args": [], "type": "menu", "interactive": True},
    "amp": {"args": ["login"], "type": "subcommand", "interactive": False},
    "aider": {"args": [], "type": "api_key", "interactive": False,
              "hint": "Aider usa claves de API, no OAuth. Configúrelas con `conectar.py --clave`."},
    "antigravity": {"args": [], "type": "app", "interactive": True,
                    "hint": "La sesión se inicia desde la aplicación Antigravity."},
}


def _manager_available(manager: str) -> bool:
    if manager == "pip":
        return True  # Se usa el intérprete actual.
    return shutil.which(manager) is not None


async def install(cli_name: str) -> dict[str, Any]:
    """Instala un agente CLI con su gestor oficial."""
    spec = INSTALLERS.get(cli_name)
    if spec is None:
        raise CLIManagerError(
            f"No hay instalador para '{cli_name}'. Conocidos: {', '.join(sorted(INSTALLERS))}"
        )

    from backend.app.core.cli_adapters import is_available

    if is_available(cli_name):
        return {
            "installed": True, "already_present": True, "cli": cli_name,
            "detail": f"{cli_name} ya estaba instalado.",
            "next_step": login_instructions(cli_name)["hint"],
        }

    if spec.manager == "manual":
        return {
            "installed": False, "cli": cli_name, "manual": True,
            "detail": f"{cli_name} no tiene instalación automatizable. {spec.notes}".strip(),
            "docs_url": spec.docs_url,
        }

    if not _manager_available(spec.manager):
        raise CLIManagerError(
            f"Para instalar {cli_name} hace falta '{spec.manager}', que no está en el PATH. "
            f"Instálelo primero. Documentación: {spec.docs_url}"
        )

    if spec.manager == "npm":
        argv = ["npm", "install", "-g", spec.package]
    elif spec.manager == "pip":
        argv = [sys.executable, "-m", "pip", "install", "--upgrade", spec.package]
    else:
        argv = [spec.manager, "install", spec.package]

    logger.info("[CLI] Instalando %s: %s", cli_name, " ".join(argv))
    try:
        proceso = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            stdin=asyncio.subprocess.DEVNULL,
        )
        salida_bytes, _ = await asyncio.wait_for(
            proceso.communicate(), timeout=INSTALL_TIMEOUT_S
        )
    except asyncio.TimeoutError:
        proceso.kill()
        await proceso.wait()
        raise CLIManagerError(
            f"La instalación de {cli_name} superó el límite de {INSTALL_TIMEOUT_S:.0f} s."
        ) from None
    except OSError as exc:
        raise CLIManagerError(f"No se pudo lanzar el instalador: {exc}") from None

    salida = salida_bytes.decode("utf-8", errors="replace")

    # El éxito lo decide la detección posterior, no el código de salida: npm
    # devuelve 0 en situaciones donde el binario no queda en el PATH.
    from backend.app.core.cli_adapters import CLI_SPECS, resolve_executable

    ejecutable = resolve_executable(CLI_SPECS[cli_name]) if cli_name in CLI_SPECS else None

    if ejecutable is None:
        return {
            "installed": False, "cli": cli_name,
            "detail": (
                f"El instalador terminó con código {proceso.returncode} pero "
                f"'{cli_name}' no aparece en el PATH. Puede requerir reiniciar la terminal."
            ),
            "output_tail": salida[-800:],
            "docs_url": spec.docs_url,
        }

    logger.info("[CLI] %s instalado en %s", cli_name, ejecutable)
    return {
        "installed": True, "cli": cli_name, "executable": ejecutable,
        "detail": f"{cli_name} instalado correctamente.",
        "next_step": login_instructions(cli_name)["hint"],
        "output_tail": salida[-400:],
    }


def login_instructions(cli_name: str) -> dict[str, Any]:
    """Qué hay que hacer para autenticar un CLI, con su comando exacto."""
    conf = LOGIN_COMMANDS.get(cli_name)
    if conf is None:
        return {"cli": cli_name, "supported": False, "hint": "CLI desconocido."}

    if conf["type"] == "slash":
        pista = f"Ejecute `{cli_name}` y escriba `{conf['slash']}`. Se abrirá el navegador."
    elif conf["type"] == "menu":
        pista = conf.get("hint") or f"Ejecute `{cli_name}` y elija la opción de inicio de sesión."
    elif conf["type"] == "subcommand":
        pista = f"Ejecute `{cli_name} {' '.join(conf['args'])}`."
    else:
        pista = conf.get("hint", "")

    return {
        "cli": cli_name,
        "supported": True,
        "interactive": conf["interactive"],
        "command": f"{cli_name} {' '.join(conf['args'])}".strip(),
        "hint": pista,
        "opens_browser": conf["type"] in ("slash", "menu", "subcommand"),
    }


async def open_login_terminal(cli_name: str) -> dict[str, Any]:
    """Abre una terminal real con el comando de login del CLI.

    Es la única forma honesta de resolverlo desde una interfaz web: el flujo
    OAuth necesita una terminal interactiva y el navegador del usuario. En
    lugar de simular el login o pedir credenciales —que el sistema nunca debe
    manejar—, se le abre la ventana con el comando puesto.
    """
    from backend.app.core.cli_adapters import CLI_SPECS, resolve_executable

    conf = LOGIN_COMMANDS.get(cli_name)
    if conf is None:
        raise CLIManagerError(f"CLI desconocido '{cli_name}'.")

    spec = CLI_SPECS.get(cli_name)
    ejecutable = resolve_executable(spec) if spec else None
    if ejecutable is None:
        raise CLIManagerError(
            f"{cli_name} no está instalado. Instálelo primero con "
            f"POST /api/cli/install/{cli_name}."
        )

    if conf["type"] == "api_key":
        return {
            "opened": False, "cli": cli_name,
            "detail": conf.get("hint", "Este CLI usa claves de API, no inicio de sesión."),
        }

    comando = f'"{ejecutable}" {" ".join(conf["args"])}'.strip()

    # `cli_name` ya se validó contra LOGIN_COMMANDS y `ejecutable` lo resolvió
    # `resolve_executable` desde el PATH: ninguno viene del usuario. Se lanza
    # sin shell salvo el `start` de Windows, que es la única forma de abrir
    # una ventana nueva.
    try:
        if os.name == "nt":
            # `start` abre una ventana nueva; `/k` la mantiene abierta para que
            # el usuario complete el flujo y vea el resultado.
            subprocess.Popen(  # noqa: S603 - entradas validadas arriba
                ["cmd.exe", "/c", "start", "cmd.exe", "/k", comando],  # noqa: S607
                shell=False,
            )
        elif sys.platform == "darwin":
            subprocess.Popen(  # noqa: S603, S607 - abre la terminal del sistema
                ["osascript", "-e", f'tell app "Terminal" to do script "{comando}"']  # noqa: S607
            )
        else:
            emulador = next(
                (t for t in ("x-terminal-emulator", "gnome-terminal", "konsole", "xterm")
                 if shutil.which(t)),
                None,
            )
            if emulador is None:
                return {
                    "opened": False, "cli": cli_name,
                    "detail": "No se encontró ningún emulador de terminal.",
                    "hint": login_instructions(cli_name)["hint"],
                }
            subprocess.Popen([emulador, "-e", comando])  # noqa: S603 - emulador del PATH
    except OSError as exc:
        raise CLIManagerError(f"No se pudo abrir la terminal: {exc}") from None

    instrucciones = login_instructions(cli_name)
    logger.info("[CLI] Terminal de login abierta para %s", cli_name)
    return {
        "opened": True,
        "cli": cli_name,
        "command": comando,
        "detail": (
            "Se abrió una terminal. Complete el inicio de sesión ahí; "
            "el navegador se abrirá solo si el CLI lo necesita."
        ),
        "next_step": instrucciones["hint"],
        "verify_with": f"POST /api/models/cli/probe con cli_name={cli_name}",
    }


def catalog() -> list[dict[str, Any]]:
    """Todos los CLIs con su estado real: instalado, cómo instalarlo, cómo autenticarlo."""
    from backend.app.core.cli_adapters import CLI_SPECS, resolve_executable

    entradas: list[dict[str, Any]] = []
    for nombre, spec in sorted(CLI_SPECS.items()):
        instalador = INSTALLERS.get(nombre)
        ejecutable = resolve_executable(spec)
        entradas.append(
            {
                "cli": nombre,
                "label": spec.display_name,
                "installed": ejecutable is not None,
                "executable": ejecutable,
                "installable": bool(instalador and instalador.manager != "manual"),
                "install_manager": instalador.manager if instalador else None,
                "install_package": instalador.package if instalador else None,
                "docs_url": instalador.docs_url if instalador else "",
                "login": login_instructions(nombre),
            }
        )
    return entradas
