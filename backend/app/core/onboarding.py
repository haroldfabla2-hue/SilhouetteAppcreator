"""Conexión asistida de proveedores de IA.

Este módulo existe para que conectar una IA sea una acción, no un procedimiento.
Cubre las tres formas de conectar y las trata igual:

- **Clave de API** — se pega, se valida con una llamada real y sólo si el
  proveedor la acepta se guarda en `.env`.
- **Sesión de navegador** (Google, GitHub…) — se lanza el propio flujo de login
  del CLI, que abre el navegador. No se manipulan tokens de terceros.
- **Servidor local** — se detecta solo.

Además diagnostica los bloqueos que impiden usar algo ya instalado, como una
configuración corrupta del CLI de Gemini, y ofrece la reparación exacta en lugar
de un mensaje genérico.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from backend.app.core.cli_adapters import (
    CLI_SPECS,
    discover_installed,
    resolve_executable,
)
from backend.app.core.env_loader import REPO_ROOT
from backend.app.core.providers import (
    PROVIDERS,
    AuthKind,
    Status,
    check_all,
    check_provider,
)

logger = logging.getLogger("Onboarding")

ENV_PATH = REPO_ROOT / ".env"

# CLIs que se autentican abriendo el navegador, y con qué orden.
BROWSER_LOGIN: dict[str, dict[str, str]] = {
    "claude": {
        "command": "/login",
        "interactive": "true",
        "hint": "Ejecute `claude` y escriba /login. Se abrirá el navegador.",
    },
    "gemini": {
        "command": "",
        "interactive": "true",
        "hint": (
            "Ejecute `gemini` y elija «Login with Google» en el primer arranque. "
            "Se abrirá el navegador y quedará autenticado con su cuenta de Google."
        ),
    },
    "codex": {
        "command": "login",
        "interactive": "false",
        "hint": "Ejecute `codex login`.",
    },
    "copilot": {
        "command": "/login",
        "interactive": "true",
        "hint": "Ejecute `copilot` y escriba /login.",
    },
    "cursor": {
        "command": "login",
        "interactive": "false",
        "hint": "Ejecute `cursor-agent login`.",
    },
}


@dataclass
class Issue:
    """Un problema concreto con su reparación."""

    target: str
    severity: str          # "blocker" | "warning"
    summary: str
    fix_hint: str
    auto_fixable: bool = False
    fix_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SetupReport:
    """Estado completo de conectividad con IAs."""

    providers: list[dict[str, Any]] = field(default_factory=list)
    cli_agents: list[dict[str, Any]] = field(default_factory=list)
    issues: list[dict[str, Any]] = field(default_factory=list)
    ready_count: int = 0
    env_file: str = str(ENV_PATH)

    @property
    def has_any_llm(self) -> bool:
        return self.ready_count > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "has_any_llm": self.has_any_llm,
            "next_step": self._next_step(),
        }

    def _next_step(self) -> str:
        if self.has_any_llm:
            return "El sistema tiene al menos un modelo utilizable. Ya puede lanzarlo."
        bloqueos = [i for i in self.issues if i["severity"] == "blocker"]
        if bloqueos:
            return bloqueos[0]["fix_hint"]
        return (
            "No hay ningún modelo conectado. La vía más rápida: obtenga una clave en "
            "https://openrouter.ai/keys y guárdela con "
            "POST /api/setup/credential {\"provider\":\"openrouter\",\"credential\":\"sk-or-...\"}"
        )


# ---------------------------------------------------------------------------
# Diagnóstico
# ---------------------------------------------------------------------------
def _gemini_settings_path() -> Path:
    return Path.home() / ".gemini" / "settings.json"


def diagnose_gemini_config() -> Issue | None:
    """Detecta la configuración de Gemini que impide arrancar el CLI.

    El CLI aborta con código 55 si un servidor MCP declara `serverUrl`, que es
    un nombre que ya no reconoce. El síntoma —«Invalid configuration»— no dice
    cuál es la clave correcta; aquí sí.
    """
    ruta = _gemini_settings_path()
    if not ruta.is_file():
        return None

    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return Issue(
            target="gemini",
            severity="blocker",
            summary=f"{ruta} no es JSON válido: {exc}",
            fix_hint=f"Corrija o borre {ruta} para que el CLI de Gemini pueda arrancar.",
        )

    servidores = datos.get("mcpServers") or {}
    afectados = [
        nombre
        for nombre, conf in servidores.items()
        if isinstance(conf, dict) and "serverUrl" in conf
    ]
    if not afectados:
        return None

    return Issue(
        target="gemini",
        severity="blocker",
        summary=(
            f"El CLI de Gemini no arranca: {', '.join(afectados)} usa la clave "
            "'serverUrl', que ya no se reconoce."
        ),
        fix_hint=(
            f"Renombre 'serverUrl' a 'httpUrl' en {ruta}. "
            "Puede hacerlo automáticamente con POST /api/setup/fix/gemini_mcp_url."
        ),
        auto_fixable=True,
        fix_id="gemini_mcp_url",
    )


def fix_gemini_config() -> dict[str, Any]:
    """Renombra `serverUrl` a `httpUrl`, guardando una copia de seguridad."""
    ruta = _gemini_settings_path()
    if not ruta.is_file():
        return {"applied": False, "reason": f"No existe {ruta}."}

    datos = json.loads(ruta.read_text(encoding="utf-8"))
    servidores = datos.get("mcpServers") or {}
    cambiados: list[str] = []

    for nombre, conf in servidores.items():
        if isinstance(conf, dict) and "serverUrl" in conf:
            conf["httpUrl"] = conf.pop("serverUrl")
            cambiados.append(nombre)

    if not cambiados:
        return {"applied": False, "reason": "No había ninguna clave 'serverUrl'."}

    copia = ruta.with_suffix(".json.bak")
    shutil.copy2(ruta, copia)
    ruta.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")

    logger.info("[Onboarding] settings.json de Gemini reparado (%s)", ", ".join(cambiados))
    return {
        "applied": True,
        "servers_fixed": cambiados,
        "backup": str(copia),
        "detail": "Se renombró 'serverUrl' a 'httpUrl'.",
    }


AUTO_FIXES = {"gemini_mcp_url": fix_gemini_config}


# ---------------------------------------------------------------------------
# Informe de estado
# ---------------------------------------------------------------------------
async def probe_cli(cli_name: str, *, timeout_s: float = 45.0) -> tuple[bool, str]:
    """Ejecuta un CLI de verdad para saber si responde.

    Estar instalado no es estar operativo: un agente sin sesión iniciada
    responde al instante con «Not logged in» y no sirve para nada. Contarlo como
    modelo disponible era optimismo, no medición.
    """
    from backend.app.core.cli_adapters import (
        CLIInvocationError,
        CLINotAuthenticated,
        CLIUnavailable,
        run_cli,
    )

    try:
        await run_cli(cli_name, "Responde unicamente: OK", timeout_s=timeout_s)
    except CLIUnavailable as exc:
        return False, str(exc)
    except CLINotAuthenticated as exc:
        return False, str(exc)
    except CLIInvocationError as exc:
        return False, str(exc)
    except Exception as exc:  # noqa: BLE001 - un sondeo nunca debe tumbar el informe
        return False, f"Fallo inesperado al sondear: {exc}"
    return True, "Responde correctamente."


async def build_report(*, verify_clis: bool = True) -> SetupReport:
    """Estado real de todo lo que puede darle un modelo al sistema.

    Con `verify_clis` se ejecuta cada agente instalado para comprobar que
    realmente responde. Es más lento, pero un recuento que incluya agentes sin
    sesión no informa de nada.
    """
    informe = SetupReport()

    salud = await check_all()
    informe.providers = [s.to_dict() for s in salud]
    informe.ready_count = sum(1 for s in salud if s.usable)

    inventario = discover_installed()
    instalados = [n for n, i in inventario.items() if i["available"]]

    sondeos: dict[str, tuple[bool, str]] = {}
    if verify_clis and instalados:
        resultados = await asyncio.gather(
            *(probe_cli(n) for n in instalados), return_exceptions=True
        )
        for nombre, resultado in zip(instalados, resultados, strict=True):
            sondeos[nombre] = (
                (False, f"Fallo al sondear: {resultado}")
                if isinstance(resultado, BaseException)
                else resultado
            )

    for nombre, info in inventario.items():
        entrada = dict(info)
        entrada["login_hint"] = BROWSER_LOGIN.get(nombre, {}).get("hint", "")
        entrada["browser_login"] = nombre in BROWSER_LOGIN
        if nombre in sondeos:
            entrada["usable"], entrada["probe_detail"] = sondeos[nombre]
        else:
            # Sin sondear no se afirma nada: `None` es «no comprobado».
            entrada["usable"] = None if info["available"] else False
            entrada["probe_detail"] = "" if info["available"] else "No instalado."
        informe.cli_agents.append(entrada)

    informe.ready_count += sum(1 for ok, _ in sondeos.values() if ok)

    # -- Problemas concretos ---------------------------------------------
    problema_gemini = diagnose_gemini_config()
    if problema_gemini:
        informe.issues.append(problema_gemini.to_dict())

    for nombre in instalados:
        sondeo = sondeos.get(nombre)
        if sondeo is not None and sondeo[0]:
            continue  # Funciona: no hay nada que reportar.

        detalle = sondeo[1] if sondeo else "Sin comprobar."
        informe.issues.append(
            Issue(
                target=nombre,
                severity="warning",
                summary=f"{CLI_SPECS[nombre].display_name} está instalado pero no responde: {detalle[:160]}",
                fix_hint=BROWSER_LOGIN.get(nombre, {}).get(
                    "hint", f"Compruebe la instalación de {CLI_SPECS[nombre].display_name}."
                ),
            ).to_dict()
        )

    for estado in salud:
        if estado.status is Status.INVALID:
            informe.issues.append(
                Issue(
                    target=estado.name,
                    severity="blocker",
                    summary=f"{estado.label}: {estado.detail}",
                    fix_hint=f"Genere una clave nueva en {estado.signup_url} y vuelva a guardarla.",
                ).to_dict()
            )

    if not informe.has_any_llm:
        informe.issues.insert(
            0,
            Issue(
                target="system",
                severity="blocker",
                summary="No hay ningún modelo utilizable: el sistema no puede razonar.",
                fix_hint=(
                    "Conecte al menos uno. Lo más rápido: una clave de OpenRouter "
                    "(https://openrouter.ai/keys), o iniciar sesión en el CLI de Gemini "
                    "con su cuenta de Google."
                ),
            ).to_dict(),
        )

    return informe


# ---------------------------------------------------------------------------
# Guardado de credenciales
# ---------------------------------------------------------------------------
def write_env_var(clave: str, valor: str, *, path: Path = ENV_PATH) -> None:
    """Escribe o actualiza una variable en `.env`, conservando el resto.

    El archivo se escribe siempre en UTF-8: este repositorio ya sufrió que un
    archivo guardado en UTF-16 dejara de ser interpretable.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    lineas: list[str] = []
    if path.is_file():
        try:
            lineas = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            lineas = path.read_text(encoding="utf-16").splitlines()

    prefijo = f"{clave}="
    reemplazada = False
    for i, linea in enumerate(lineas):
        if linea.strip().startswith(prefijo) or linea.strip().startswith(f"export {prefijo}"):
            lineas[i] = f"{clave}={valor}"
            reemplazada = True
            break

    if not reemplazada:
        if lineas and lineas[-1].strip():
            lineas.append("")
        lineas.append(f"{clave}={valor}")

    path.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    # Disponible de inmediato, sin reiniciar el proceso.
    os.environ[clave] = valor


async def connect_provider(name: str, credential: str) -> dict[str, Any]:
    """Valida una credencial y, sólo si funciona, la guarda.

    Guardar primero y descubrir después que no sirve es cómo se acaba con un
    sistema «configurado» que no responde.
    """
    spec = PROVIDERS.get(name)
    if spec is None:
        raise KeyError(f"Proveedor desconocido '{name}'.")
    if spec.auth is AuthKind.NONE:
        return {
            "saved": False,
            "detail": f"{spec.label} no necesita credencial.",
            "health": (await check_provider(name)).to_dict(),
        }

    salud = await check_provider(name, credential=credential.strip())
    if not salud.usable:
        return {
            "saved": False,
            "detail": f"La credencial no se guardó porque no funciona: {salud.detail}",
            "health": salud.to_dict(),
        }

    write_env_var(spec.env_var, credential.strip())
    logger.info("[Onboarding] %s conectado y guardado en .env", spec.label)
    return {
        "saved": True,
        "detail": f"{spec.label} verificado y guardado en {ENV_PATH.name}.",
        "health": salud.to_dict(),
    }


# ---------------------------------------------------------------------------
# Login por navegador
# ---------------------------------------------------------------------------
async def start_browser_login(cli_name: str) -> dict[str, Any]:
    """Lanza el flujo de login propio del CLI (Google, GitHub…).

    No se tocan tokens ni credenciales de terceros: se ejecuta el comando del
    propio CLI, que abre el navegador y gestiona su sesión. Los flujos que
    requieren una terminal interactiva no se pueden lanzar desde la API, y se
    dice explícitamente en lugar de fingir que se inició.
    """
    spec = CLI_SPECS.get(cli_name)
    if spec is None:
        raise KeyError(f"CLI desconocido '{cli_name}'.")

    ejecutable = resolve_executable(spec)
    if not ejecutable:
        return {
            "started": False,
            "detail": f"{spec.display_name} no está instalado.",
            "hint": BROWSER_LOGIN.get(cli_name, {}).get("hint", ""),
        }

    conf = BROWSER_LOGIN.get(cli_name)
    if conf is None:
        return {
            "started": False,
            "detail": f"{spec.display_name} no usa login por navegador.",
        }

    if conf["interactive"] == "true":
        # Requiere una terminal real: se devuelve la instrucción exacta.
        return {
            "started": False,
            "requires_terminal": True,
            "command": Path(ejecutable).name,
            "detail": (
                f"{spec.display_name} necesita una terminal interactiva para iniciar sesión."
            ),
            "hint": conf["hint"],
        }

    try:
        proceso = await asyncio.create_subprocess_exec(
            ejecutable,
            conf["command"],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        salida, error = await asyncio.wait_for(proceso.communicate(), timeout=120.0)
    except (TimeoutError, asyncio.TimeoutError):
        return {
            "started": True,
            "detail": "El proceso de login sigue abierto; complete la autenticación en el navegador.",
            "hint": conf["hint"],
        }
    except OSError as exc:
        return {"started": False, "detail": f"No se pudo lanzar el login: {exc}"}

    texto = (salida or b"").decode("utf-8", errors="replace").strip()
    return {
        "started": proceso.returncode == 0,
        "detail": texto[:400] or (error or b"").decode("utf-8", errors="replace")[:400],
        "hint": conf["hint"],
    }
