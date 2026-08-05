"""Carga de variables de entorno desde archivos `.env`.

Este módulo resuelve un fallo que dejaba el sistema entero sin modelos: **nada
cargaba los archivos `.env`**. `config.py` declaraba `env_file = ".env"` en la
configuración de Pydantic, pero eso sólo alimenta los campos de esa clase; el
resto del código —el router, la autenticación, el CORS, la lista blanca de
procesos— lee con `os.getenv()` y nunca veía esos valores.

El resultado práctico: se podía tener una clave de OpenRouter perfectamente
escrita en `backend/.env` y el router arrancaba con «MiniMax: ✗, OpenRouter: ✗».

Reglas de carga:

1. El entorno real **siempre gana**. Un `.env` nunca pisa una variable que ya
   viene definida desde fuera; así un despliegue con secretos inyectados no se
   ve alterado por un archivo olvidado en el disco.
2. Se cargan varios archivos en orden de precedencia, y el primero que define
   una variable la fija.
3. Sin dependencias nuevas: se usa `python-dotenv` si está, y si no un lector
   propio que cubre el formato habitual.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger("EnvLoader")

# Raíz del repositorio: backend/app/core/env_loader.py -> tres niveles arriba.
REPO_ROOT = Path(__file__).resolve().parents[3]

# Orden de precedencia: el primero que defina una variable, gana.
ENV_FILES: tuple[Path, ...] = (
    REPO_ROOT / ".env",
    REPO_ROOT / "backend" / ".env",
    REPO_ROOT / ".env.local",
)

_loaded = False


def parse_env_file(path: Path) -> dict[str, str]:
    """Lee un archivo `.env` y devuelve sus pares clave/valor.

    Admite comentarios, líneas vacías, el prefijo `export` y valores entre
    comillas simples o dobles.
    """
    valores: dict[str, str] = {}
    try:
        contenido = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Algunos editores de Windows guardan en UTF-16 (le pasó al .gitignore
        # de este mismo repositorio, y Git dejó de aplicar su primera regla).
        try:
            contenido = path.read_text(encoding="utf-16")
        except (OSError, UnicodeDecodeError):
            logger.warning("No se pudo decodificar %s", path)
            return valores
    except OSError as exc:
        logger.warning("No se pudo leer %s: %s", path, exc)
        return valores

    for linea in contenido.splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        if linea.startswith("export "):
            linea = linea[len("export ") :].strip()

        clave, _, valor = linea.partition("=")
        clave = clave.strip()
        if not clave:
            continue

        valor = valor.strip()
        # Quitar comillas envolventes, si las hay.
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in ("'", '"'):
            valor = valor[1:-1]
        valores[clave] = valor

    return valores


def load_env(*, override: bool = False, extra_files: tuple[Path, ...] = ()) -> dict[str, str]:
    """Carga los archivos `.env` en `os.environ`.

    Devuelve las variables efectivamente aplicadas. Con `override=False` (el
    valor por defecto) no se pisa nada que ya estuviera definido.
    """
    global _loaded
    aplicadas: dict[str, str] = {}

    for ruta in (*ENV_FILES, *extra_files):
        if not ruta.is_file():
            continue
        for clave, valor in parse_env_file(ruta).items():
            # Un valor vacío no sirve de nada y taparía otro archivo posterior.
            if not valor:
                continue
            if not override and clave in os.environ and os.environ[clave]:
                continue
            if clave in aplicadas:
                continue  # Ya lo fijó un archivo de mayor precedencia.
            os.environ[clave] = valor
            aplicadas[clave] = valor

        logger.debug("Variables leídas de %s", ruta)

    if aplicadas:
        # Nunca se registran los valores, sólo los nombres.
        logger.info(
            "Entorno cargado: %d variable(s) desde .env (%s)",
            len(aplicadas),
            ", ".join(sorted(aplicadas)[:8]) + ("…" if len(aplicadas) > 8 else ""),
        )
    else:
        logger.info("No se aplicó ninguna variable desde archivos .env")

    _loaded = True
    return aplicadas


def ensure_loaded() -> None:
    """Carga el entorno una sola vez. Seguro de llamar desde varios módulos."""
    if not _loaded:
        # La consola se prepara aquí también: cualquier punto de entrada que
        # use el router (tests, scripts, CLI) queda protegido del
        # UnicodeEncodeError al escribir registros en Windows.
        from backend.app.core.console import configure

        configure()
        load_env()


def describe_sources() -> list[dict[str, object]]:
    """Qué archivos existen y cuántas variables aporta cada uno, sin valores."""
    fuentes: list[dict[str, object]] = []
    for ruta in ENV_FILES:
        existe = ruta.is_file()
        fuentes.append(
            {
                "path": str(ruta),
                "exists": existe,
                "variables": sorted(parse_env_file(ruta)) if existe else [],
            }
        )
    return fuentes
