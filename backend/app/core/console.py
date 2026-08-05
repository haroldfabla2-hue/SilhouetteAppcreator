"""Salida de consola en UTF-8, para que un carácter no tumbe el proceso.

En Windows, `sys.stdout` usa la página de códigos del sistema (cp1252 en un
equipo en español). Cualquier carácter fuera de ese juego —un emoji en un
mensaje de registro, una comilla tipográfica en una respuesta del modelo— lanza
`UnicodeEncodeError` **en el momento de escribir el log**, y esa excepción se
propaga hasta abortar la petición.

Es un fallo especialmente traicionero porque no está en la lógica: el código es
correcto y aun así el proceso muere al intentar contar lo que hizo.

`configure()` deja la salida en UTF-8 y hace que los caracteres no representables
se sustituyan en lugar de reventar. Es idempotente y no hace nada en sistemas
donde ya sea correcto.
"""
from __future__ import annotations

import contextlib
import logging
import sys
from typing import TextIO

_configured = False


def _reconfigure_stream(stream: TextIO | None) -> None:
    if stream is None:
        return
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is None:
        return
    # `errors="replace"` es deliberado: perder un emoji en un log es aceptable;
    # perder la petición por un emoji no lo es. Un flujo redirigido o cerrado no
    # es motivo para impedir el arranque.
    with contextlib.suppress(ValueError, OSError):
        reconfigure(encoding="utf-8", errors="replace")


def _harden_logging() -> None:
    """Fuerza UTF-8 en los manejadores de registro ya instalados."""
    for handler in logging.getLogger().handlers:
        flujo = getattr(handler, "stream", None)
        _reconfigure_stream(flujo)


def configure() -> None:
    """Deja la consola y el registro en UTF-8. Seguro de llamar varias veces."""
    global _configured
    if _configured:
        return

    _reconfigure_stream(sys.stdout)
    _reconfigure_stream(sys.stderr)
    _harden_logging()

    _configured = True


def safe_text(valor: object, *, limit: int | None = None) -> str:
    """Convierte a texto imprimible en cualquier consola.

    Útil para incluir respuestas de modelos o rutas ajenas en un mensaje de
    registro sin depender de la codificación del terminal.
    """
    texto = str(valor)
    if limit is not None and len(texto) > limit:
        texto = texto[:limit] + "…"

    codificacion = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        texto.encode(codificacion)
    except (UnicodeEncodeError, LookupError):
        texto = texto.encode(codificacion, errors="replace").decode(codificacion, errors="replace")
    return texto
