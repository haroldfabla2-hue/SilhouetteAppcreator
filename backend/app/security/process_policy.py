"""Política de lanzamiento de procesos.

`OSControlAgent.launch_application` recibía un nombre arbitrario y lo pasaba a
`subprocess.Popen`, aceptando además rutas absolutas. Aquí se define una lista
blanca explícita: si una aplicación no está declarada, no se lanza.

Por defecto la lista está **vacía y la capacidad desactivada**. Se habilita con:

    SILHOUETTE_ALLOWED_APPS=code,notepad,blender

El nombre lógico se resuelve contra el PATH con `shutil.which`; nunca se ejecuta
una ruta suministrada por quien llama.
"""
from __future__ import annotations

import os
import shlex
import shutil
from dataclasses import dataclass

ENV_ALLOWED_APPS = "SILHOUETTE_ALLOWED_APPS"

# Caracteres que no tienen sentido en argumentos legítimos y sí en inyección de
# shell. Aunque Popen se invoca sin shell=True, rechazarlos evita sorpresas con
# intérpretes que sí reexpanden (cmd.exe, .bat).
SHELL_METACHARACTERS = frozenset('&|;<>$`\n\r"\'')

MAX_ARGS = 16
MAX_ARG_LENGTH = 512


class AppNotAllowed(ValueError):
    """La aplicación solicitada no está en la lista blanca."""


class ArgumentRejected(ValueError):
    """Los argumentos suministrados no superan la validación."""


@dataclass(frozen=True)
class LaunchPlan:
    """Comando validado y listo para ejecutarse."""

    app_name: str
    executable: str
    args: list[str]

    @property
    def argv(self) -> list[str]:
        return [self.executable, *self.args]


def allowed_apps() -> frozenset[str]:
    raw = os.getenv(ENV_ALLOWED_APPS, "")
    return frozenset(name.strip().lower() for name in raw.split(",") if name.strip())


def is_enabled() -> bool:
    return bool(allowed_apps())


def validate_args(args: str | None) -> list[str]:
    """Divide y valida los argumentos. Cadena vacía o None devuelve []."""
    if not args or not args.strip():
        return []

    # Los saltos de línea se comprueban sobre la cadena cruda: `shlex.split` los
    # trata como separadores, así que después de dividir ya no aparecen en
    # ninguna parte y la comprobación por argumento no los vería.
    if "\n" in args or "\r" in args:
        raise ArgumentRejected("Los argumentos no pueden contener saltos de línea.")

    try:
        parts = shlex.split(args, posix=False)
    except ValueError as exc:
        raise ArgumentRejected(f"No se pudieron interpretar los argumentos: {exc}") from exc

    if len(parts) > MAX_ARGS:
        raise ArgumentRejected(f"Demasiados argumentos (máximo {MAX_ARGS}).")

    for part in parts:
        if len(part) > MAX_ARG_LENGTH:
            raise ArgumentRejected(f"Argumento demasiado largo (máximo {MAX_ARG_LENGTH} caracteres).")
        offending = SHELL_METACHARACTERS.intersection(part)
        if offending:
            raise ArgumentRejected(
                "El argumento contiene caracteres no permitidos: " + "".join(sorted(offending))
            )
    return parts


def plan_launch(app_name: str, args: str | None = None) -> LaunchPlan:
    """Valida la solicitud y devuelve un plan de ejecución, o lanza excepción."""
    name = (app_name or "").strip().lower()
    if not name:
        raise AppNotAllowed("No se indicó ninguna aplicación.")

    permitted = allowed_apps()
    if not permitted:
        raise AppNotAllowed(
            "El lanzamiento de aplicaciones está desactivado. "
            f"Para habilitarlo, defina {ENV_ALLOWED_APPS} con una lista separada por comas."
        )
    if name not in permitted:
        raise AppNotAllowed(
            f"'{app_name}' no está en la lista de aplicaciones permitidas "
            f"({', '.join(sorted(permitted))})."
        )

    # La ruta se resuelve aquí, no la suministra quien llama.
    executable = shutil.which(name)
    if not executable:
        raise AppNotAllowed(f"'{app_name}' está permitida pero no se encontró en el PATH del sistema.")

    return LaunchPlan(app_name=name, executable=executable, args=validate_args(args))
