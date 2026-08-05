"""Adaptadores para agentes de línea de comandos.

Cada CLI de agente se invoca distinto. Antes el router asumía que casi todos
aceptaban el prompt como argumento posicional, lo que en la práctica significaba
lanzar el CLI en **modo interactivo** y esperar 120 s a un timeout. Además la
resolución de rutas no probaba extensiones de Windows, así que un `claude.exe`
perfectamente instalado se daba por ausente.

Aquí cada CLI declara cómo se le habla:

    CLISpec(name="claude", executables=("claude",), prompt_flag="-p")
        -> claude -p "tu prompt"

Añadir un CLI nuevo es añadir un `CLISpec` a `CLI_SPECS`; no hay que tocar el
router. La detección es real: se comprueba que el ejecutable exista antes de
declarar el proveedor disponible.
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("CLIAdapters")

# Extensiones que Windows considera ejecutables. En POSIX sólo cuenta el nombre.
WINDOWS_EXTENSIONS: tuple[str, ...] = (".exe", ".cmd", ".bat", ".ps1", "")
POSIX_EXTENSIONS: tuple[str, ...] = ("",)

# Scripts que no arrancan solos: necesitan el intérprete de comandos.
NEEDS_SHELL_WRAPPER: tuple[str, ...] = (".cmd", ".bat")

DEFAULT_TIMEOUT_S = 180.0

# Banners y avisos que ensucian la salida de casi todos los CLIs.
COMMON_NOISE: tuple[str, ...] = (
    r"Update available!.*?\n",
    r"A new version of .*? is available.*?\n",
    r"^\s*npm notice.*?\n",
    r"^\s*Warning: .*deprecated.*\n",
)


class CLIUnavailable(RuntimeError):
    """El ejecutable del CLI no está instalado o no se encuentra."""


class CLIInvocationError(RuntimeError):
    """El CLI existe pero falló al ejecutarse."""


class CLINotAuthenticated(CLIInvocationError):
    """El CLI está instalado pero no tiene sesión iniciada o le falta cuota."""


# Muchos CLIs devuelven código de salida 0 al imprimir «no has iniciado sesión»
# o «cuota agotada». Sin esta detección, ese aviso se propagaría hacia arriba
# como si fuera la respuesta del modelo — el mismo defecto que este proyecto
# arrastraba en el router.
AUTH_FAILURE_PATTERNS: tuple[str, ...] = (
    r"not logged in",
    r"no has iniciado sesi[óo]n",
    r"please run\s+/?login",
    r"authentication (?:failed|required)",
    r"unauthorized",
    r"invalid api key",
    r"api key not found",
    r"missing api key",
    r"you are not signed in",
    r"sign in to continue",
    r"session (?:expired|not found)",
    r"quota exceeded",
    r"rate limit exceeded",
    r"insufficient credits",
    r"subscription required",
    # El CLI existe y arranca, pero la cuenta no da acceso: es un problema de
    # credenciales, no un fallo transitorio, y reintentar no lo arregla.
    r"ineligibletiererror",
    r"no longer supported for",
    r"upgrade (?:your|to a) (?:plan|tier)",
    r"error authenticating",
)

# Una respuesta legítima puede mencionar estas frases al explicar código. Sólo
# se considera fallo si el aviso domina una salida corta.
AUTH_DETECTION_MAX_CHARS = 400


@dataclass(frozen=True)
class CLISpec:
    """Cómo invocar un agente de línea de comandos concreto."""

    #: Identificador lógico usado por el router y la API.
    name: str
    #: Nombres de ejecutable a probar, en orden de preferencia.
    executables: tuple[str, ...]
    #: Nombre legible para la interfaz.
    label: str = ""
    #: Subcomando previo al prompt, p. ej. ("exec",) -> `codex exec "..."`.
    subcommand: tuple[str, ...] = ()
    #: Bandera que precede al prompt. Vacía = prompt posicional.
    prompt_flag: str = ""
    #: Argumentos fijos añadidos siempre (modo no interactivo, sin color…).
    extra_args: tuple[str, ...] = ()
    #: Directorios adicionales donde buscar, relativos a $HOME.
    home_subdirs: tuple[str, ...] = ()
    #: Variables de entorno impuestas a la ejecución.
    env: dict[str, str] = field(default_factory=dict)
    timeout_s: float = DEFAULT_TIMEOUT_S
    #: Patrones extra a limpiar de la salida.
    noise_patterns: tuple[str, ...] = ()

    @property
    def display_name(self) -> str:
        return self.label or self.name

    def build_args(self, executable: str, prompt: str) -> list[str]:
        """Construye la línea de comandos completa para este CLI."""
        args = [executable, *self.subcommand, *self.extra_args]
        if self.prompt_flag:
            args.extend([self.prompt_flag, prompt])
        else:
            args.append(prompt)
        return args


# ---------------------------------------------------------------------------
# Registro de CLIs soportados
#
# Los flags de `claude` y `gemini` se verificaron ejecutando `--help` en un
# equipo real: ambos usan `-p/--print` y `-p/--prompt` para el modo headless.
# Pasarles el prompt de forma posicional los deja en modo interactivo.
# ---------------------------------------------------------------------------
CLI_SPECS: dict[str, CLISpec] = {
    "claude": CLISpec(
        name="claude",
        label="Claude Code",
        executables=("claude",),
        prompt_flag="-p",
        home_subdirs=(".local/bin", ".claude/bin"),
        timeout_s=300.0,
    ),
    "gemini": CLISpec(
        name="gemini",
        label="Gemini CLI",
        executables=("gemini",),
        # Sin `-p` arranca la sesión interactiva y el proceso nunca termina.
        prompt_flag="-p",
        home_subdirs=(".gemini/bin",),
        noise_patterns=(r"Invalid configuration in .*?\n(?:.*?\n)*?Please fix the configuration\.\n",),
    ),
    "codex": CLISpec(
        name="codex",
        label="OpenAI Codex CLI",
        executables=("codex",),
        subcommand=("exec",),
        home_subdirs=(".codex/bin",),
    ),
    "cursor": CLISpec(
        name="cursor",
        label="Cursor Agent",
        # `cursor` a secas es el lanzador del IDE; el agente headless es
        # `cursor-agent`. Se prueba primero el correcto.
        executables=("cursor-agent",),
        prompt_flag="-p",
        home_subdirs=(".cursor/bin", ".local/bin"),
    ),
    "antigravity": CLISpec(
        name="antigravity",
        label="Antigravity",
        executables=("agy", "antigravity", "Antigravity"),
        subcommand=(),
        home_subdirs=(
            ".gemini/antigravity/bin",
            ".antigravity/bin",
            "AppData/Local/Programs/Antigravity",
            "AppData/Local/Programs/Antigravity/resources/app",
        ),
    ),
    "aider": CLISpec(
        name="aider",
        label="Aider",
        executables=("aider",),
        prompt_flag="--message",
        extra_args=("--no-auto-commits", "--yes-always"),
        home_subdirs=(".local/bin",),
    ),
    "qwen": CLISpec(
        name="qwen",
        label="Qwen Code",
        executables=("qwen",),
        prompt_flag="-p",
    ),
    "opencode": CLISpec(
        name="opencode",
        label="OpenCode",
        executables=("opencode",),
        subcommand=("run",),
        home_subdirs=(".opencode/bin", ".local/bin"),
    ),
    "crush": CLISpec(
        name="crush",
        label="Crush",
        executables=("crush",),
        subcommand=("run",),
        home_subdirs=(".local/bin",),
    ),
    "copilot": CLISpec(
        name="copilot",
        label="GitHub Copilot CLI",
        executables=("copilot",),
        prompt_flag="-p",
        extra_args=("--allow-all-tools",),
    ),
    "goose": CLISpec(
        name="goose",
        label="Goose",
        executables=("goose",),
        subcommand=("run",),
        prompt_flag="-t",
        home_subdirs=(".local/bin",),
    ),
    "amp": CLISpec(
        name="amp",
        label="Amp",
        executables=("amp",),
        prompt_flag="-x",
    ),
}


def _extensions() -> tuple[str, ...]:
    if os.name != "nt":
        return POSIX_EXTENSIONS
    # PATHEXT del sistema, más las que nos interesan siempre.
    pathext = tuple(
        e.lower() for e in os.getenv("PATHEXT", "").split(os.pathsep) if e.strip()
    )
    return tuple(dict.fromkeys((*WINDOWS_EXTENSIONS, *pathext)))


def _candidate_dirs(spec: CLISpec) -> list[Path]:
    """Directorios donde buscar el ejecutable, además del PATH."""
    home = Path.home()
    dirs: list[Path] = [home / sub for sub in spec.home_subdirs]

    if os.name == "nt":
        appdata = os.getenv("APPDATA")
        localappdata = os.getenv("LOCALAPPDATA")
        if appdata:
            dirs.append(Path(appdata) / "npm")
        if localappdata:
            dirs.append(Path(localappdata) / "Programs")
        for var in ("NVM_SYMLINK", "NVM_HOME"):
            root = os.getenv(var)
            if root:
                dirs.append(Path(root))
    else:
        dirs.extend([Path("/usr/local/bin"), Path("/opt/homebrew/bin"), home / ".local" / "bin"])

    return dirs


def resolve_executable(spec: CLISpec) -> str | None:
    """Localiza el ejecutable del CLI, o `None` si no está instalado.

    Prueba el PATH primero y, si falla, cada directorio candidato con cada
    extensión ejecutable. Este último paso es el que faltaba: `claude.exe` en
    `~/.local/bin` no se encontraba porque sólo se probaba `claude` sin
    extensión.
    """
    for nombre in spec.executables:
        encontrado = shutil.which(nombre)
        if encontrado:
            return encontrado

    extensiones = _extensions()
    for directorio in _candidate_dirs(spec):
        if not directorio.is_dir():
            continue
        for nombre in spec.executables:
            for ext in extensiones:
                candidato = directorio / f"{nombre}{ext}"
                if candidato.is_file():
                    return str(candidato)
    return None


def is_available(cli_name: str) -> bool:
    """Comprueba de verdad si un CLI está instalado."""
    spec = CLI_SPECS.get(cli_name)
    return bool(spec and resolve_executable(spec))


def discover_installed() -> dict[str, dict[str, object]]:
    """Inventario de qué CLIs hay realmente en esta máquina."""
    inventario: dict[str, dict[str, object]] = {}
    for nombre, spec in CLI_SPECS.items():
        ruta = resolve_executable(spec)
        inventario[nombre] = {
            "name": nombre,
            "label": spec.display_name,
            "available": ruta is not None,
            "executable": ruta,
            "candidates": list(spec.executables),
        }
    return inventario


def _clean_output(texto: str, spec: CLISpec) -> str:
    for patron in (*COMMON_NOISE, *spec.noise_patterns):
        texto = re.sub(patron, "", texto, flags=re.IGNORECASE | re.MULTILINE)
    return texto.strip()


def detect_auth_failure(texto: str) -> str | None:
    """Devuelve el motivo si la salida es un aviso de sesión o cuota, no una respuesta.

    Sólo se aplica a salidas cortas: una explicación larga que mencione «API key»
    es una respuesta legítima, no un fallo de autenticación.
    """
    if len(texto) > AUTH_DETECTION_MAX_CHARS:
        return None
    for patron in AUTH_FAILURE_PATTERNS:
        if re.search(patron, texto, re.IGNORECASE):
            return texto.strip()
    return None


async def run_cli(cli_name: str, prompt: str, *, timeout_s: float | None = None) -> str:
    """Ejecuta un agente CLI y devuelve su salida.

    Lanza `CLIUnavailable` si no está instalado y `CLIInvocationError` si falla,
    para que el router pase al siguiente proveedor. Nunca devuelve texto de
    relleno haciéndose pasar por una respuesta.
    """
    spec = CLI_SPECS.get(cli_name)
    if spec is None:
        raise CLIUnavailable(
            f"CLI desconocido '{cli_name}'. Registrados: {', '.join(sorted(CLI_SPECS))}"
        )

    ejecutable = resolve_executable(spec)
    if not ejecutable:
        raise CLIUnavailable(
            f"{spec.display_name} no está instalado (se buscó "
            f"{', '.join(spec.executables)} en el PATH y en rutas conocidas)."
        )

    argv = spec.build_args(ejecutable, prompt)
    # Los scripts .cmd/.bat de Windows no arrancan por sí solos.
    if os.name == "nt" and Path(ejecutable).suffix.lower() in NEEDS_SHELL_WRAPPER:
        argv = ["cmd.exe", "/c", *argv]

    entorno = {**os.environ, **spec.env}
    # Salida limpia: sin colores ANSI ni interactividad.
    entorno.setdefault("NO_COLOR", "1")
    entorno.setdefault("TERM", "dumb")
    entorno.setdefault("CI", "1")

    limite = timeout_s or spec.timeout_s
    logger.info("[CLI] Ejecutando %s: %s", spec.display_name, Path(ejecutable).name)

    try:
        proceso = await asyncio.create_subprocess_exec(
            *argv,
            stdin=asyncio.subprocess.DEVNULL,  # evita que se quede esperando entrada
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=entorno,
        )
    except OSError as exc:
        raise CLIInvocationError(
            f"No se pudo lanzar {spec.display_name}: {exc}"
        ) from exc

    try:
        salida, error = await asyncio.wait_for(proceso.communicate(), timeout=limite)
    except asyncio.TimeoutError:
        proceso.kill()
        await proceso.wait()
        raise CLIInvocationError(
            f"{spec.display_name} agotó el límite de {limite:.0f} s. "
            "Puede haber quedado esperando entrada interactiva."
        ) from None

    texto = _clean_output(salida.decode("utf-8", errors="replace"), spec)
    texto_error = error.decode("utf-8", errors="replace").strip()

    if proceso.returncode != 0 and not texto:
        # Se mira también la salida de error: varios CLIs escriben ahí el aviso
        # de sesión y devuelven un código genérico.
        motivo = detect_auth_failure(texto_error[:AUTH_DETECTION_MAX_CHARS])
        if motivo:
            raise CLINotAuthenticated(f"{spec.display_name}: {motivo}")
        raise CLIInvocationError(
            f"{spec.display_name} terminó con código {proceso.returncode}: "
            f"{texto_error[:500] or '(sin salida de error)'}"
        )
    if not texto:
        raise CLIInvocationError(
            f"{spec.display_name} terminó correctamente pero no devolvió salida."
        )

    # Código de salida 0 no basta: hay que mirar qué se imprimió.
    motivo = detect_auth_failure(texto)
    if motivo:
        raise CLINotAuthenticated(
            f"{spec.display_name} no tiene sesión iniciada: {motivo}"
        )

    return texto
