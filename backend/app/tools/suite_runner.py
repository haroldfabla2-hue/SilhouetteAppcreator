"""Ejecución de tests con resultados reales.

Un agente que edita código y no puede comprobar si lo rompió no es un agente de
desarrollo: es un generador de texto que escribe archivos. Este módulo cierra
ese lazo.

Ejecuta `pytest` de verdad y devuelve lo que ocurrió: cuántos pasaron, cuáles
fallaron, con qué error y en qué línea. No interpreta ni resume el resultado —
lo transporta.

La regla del proyecto aplica igual aquí: si pytest no está instalado o la
ejecución falla, se dice. Nunca se devuelve «todo verde» sin haber ejecutado
nada, que es exactamente el defecto que tenía `verificar_sistema.py`.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import shutil
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from backend.app.security.workspace import (
    PathNotAllowed,
    resolve_within_workspace,
    workspace_root,
)

logger = logging.getLogger("SuiteRunner")

DEFAULT_TIMEOUT_S = 900.0
MAX_OUTPUT_CHARS = 40000

# Resumen final de pytest: "3 failed, 380 passed, 3 skipped in 36.44s"
SUMMARY_PATTERN = re.compile(
    r"(\d+)\s+(passed|failed|error|errors|skipped|xfailed|xpassed|deselected)", re.IGNORECASE
)


class SuiteRunnerUnavailable(RuntimeError):
    """No se puede ejecutar la suite en este entorno."""


@dataclass
class SuiteFailure:
    """Un test que falló, con dónde y por qué."""

    test_id: str
    file: str = ""
    line: int | None = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SuiteRun:
    """Resultado de ejecutar la suite."""

    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    duration_s: float = 0.0
    exit_code: int = -1
    failures: list[SuiteFailure] = field(default_factory=list)
    summary_line: str = ""
    output_tail: str = ""
    command: str = ""

    @property
    def ok(self) -> bool:
        """La suite pasó. Sólo el código de salida de pytest lo decide."""
        return self.exit_code == 0

    @property
    def total(self) -> int:
        return self.passed + self.failed + self.errors + self.skipped

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "ok": self.ok,
            "total": self.total,
            "failures": [f.to_dict() for f in self.failures],
        }


def _parse_report(ruta: Path) -> tuple[list[SuiteFailure], dict[str, int]]:
    """Lee el informe JSON de pytest, si el plugin está disponible."""
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [], {}

    fallos: list[SuiteFailure] = []
    for prueba in datos.get("tests", []):
        if prueba.get("outcome") not in ("failed", "error"):
            continue
        detalle = (prueba.get("call") or prueba.get("setup") or {})
        mensaje = str(detalle.get("longrepr") or "")
        fallos.append(
            SuiteFailure(
                test_id=prueba.get("nodeid", ""),
                file=(prueba.get("nodeid", "").split("::")[0]),
                line=prueba.get("lineno"),
                message=mensaje[-600:],
            )
        )

    resumen = datos.get("summary") or {}
    contadores = {
        k: int(resumen.get(k, 0))
        for k in ("passed", "failed", "error", "skipped")
    }
    return fallos, contadores


def _parse_output(salida: str) -> tuple[list[SuiteFailure], dict[str, int], str]:
    """Extrae resultados de la salida de texto de pytest.

    Es el camino que se usa cuando `pytest-json-report` no está instalado: no
    hay que exigir un plugin para poder ejecutar la suite.
    """
    contadores: dict[str, int] = {}
    linea_resumen = ""
    for linea in reversed(salida.splitlines()):
        coincidencias = SUMMARY_PATTERN.findall(linea)
        if coincidencias and ("passed" in linea or "failed" in linea or "error" in linea):
            linea_resumen = linea.strip()
            for cantidad, etiqueta in coincidencias:
                clave = etiqueta.lower().rstrip("s")
                clave = "error" if clave == "error" else clave
                contadores[clave] = contadores.get(clave, 0) + int(cantidad)
            break

    fallos: list[SuiteFailure] = []
    for linea in salida.splitlines():
        # "FAILED tests/test_x.py::TestY::test_z - AssertionError: ..."
        if linea.startswith(("FAILED ", "ERROR ")):
            resto = linea.split(" ", 1)[1]
            identificador, _, mensaje = resto.partition(" - ")
            fallos.append(
                SuiteFailure(
                    test_id=identificador.strip(),
                    file=identificador.split("::")[0],
                    message=mensaje.strip()[:600],
                )
            )

    return fallos, contadores, linea_resumen


class SuiteRunner:
    """Ejecuta la suite del proyecto y reporta lo que realmente ocurrió."""

    def __init__(self, *, timeout_s: float = DEFAULT_TIMEOUT_S) -> None:
        self.timeout_s = timeout_s

    async def run(
        self,
        target: str | None = None,
        *,
        keyword: str | None = None,
        markers: str | None = None,
        fail_fast: bool = False,
    ) -> SuiteRun:
        """Ejecuta pytest.

        `target` puede ser un archivo, un directorio o un nodo concreto
        (`tests/test_x.py::TestY::test_z`). Se confina al workspace.
        """
        raiz = workspace_root()

        args = [sys.executable, "-m", "pytest", "-q", "--no-header"]
        if target:
            # El nodo puede llevar `::`, que no forma parte de la ruta.
            ruta, _, nodo = str(target).partition("::")
            try:
                resuelto = resolve_within_workspace(ruta)
            except PathNotAllowed as exc:
                raise SuiteRunnerUnavailable(str(exc)) from None
            if not resuelto.exists():
                raise SuiteRunnerUnavailable(f"No existe '{ruta}'.")
            args.append(str(resuelto) + (f"::{nodo}" if nodo else ""))
        if keyword:
            args.extend(["-k", keyword])
        if markers:
            args.extend(["-m", markers])
        if fail_fast:
            args.append("-x")

        # El informe JSON da fallos estructurados; si el plugin falta, se cae
        # al análisis de la salida de texto, que siempre está disponible.
        informe = Path(tempfile.mkdtemp()) / "report.json"
        usar_json = _json_report_available()
        if usar_json:
            args.extend(["--json-report", f"--json-report-file={informe}"])

        logger.info("[Tests] Ejecutando: %s", " ".join(args[2:]))
        import time

        inicio = time.perf_counter()

        try:
            proceso = await asyncio.create_subprocess_exec(
                *args,
                cwd=str(raiz),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                stdin=asyncio.subprocess.DEVNULL,
            )
        except OSError as exc:
            raise SuiteRunnerUnavailable(f"No se pudo lanzar pytest: {exc}") from None

        try:
            salida_bytes, _ = await asyncio.wait_for(
                proceso.communicate(), timeout=self.timeout_s
            )
        except asyncio.TimeoutError:
            proceso.kill()
            await proceso.wait()
            raise SuiteRunnerUnavailable(
                f"La suite superó el límite de {self.timeout_s:.0f} s."
            ) from None

        duracion = time.perf_counter() - inicio
        salida = salida_bytes.decode("utf-8", errors="replace")

        fallos, contadores, linea_resumen = _parse_output(salida)
        if usar_json and informe.is_file():
            fallos_json, contadores_json = _parse_report(informe)
            if contadores_json:
                fallos, contadores = fallos_json or fallos, contadores_json
            shutil.rmtree(informe.parent, ignore_errors=True)

        ejecucion = SuiteRun(
            passed=contadores.get("passed", 0),
            failed=contadores.get("failed", 0),
            errors=contadores.get("error", 0),
            skipped=contadores.get("skipped", 0),
            duration_s=round(duracion, 2),
            exit_code=proceso.returncode if proceso.returncode is not None else -1,
            failures=fallos,
            summary_line=linea_resumen,
            output_tail=salida[-MAX_OUTPUT_CHARS:],
            command=" ".join(args[2:]),
        )

        # Código 5 de pytest = «no se recogió ningún test». No es un éxito.
        if ejecucion.exit_code == 5:
            raise SuiteRunnerUnavailable(
                f"pytest no encontró ningún test que ejecutar ({ejecucion.command})."
            )

        logger.info(
            "[Tests] %s en %.1fs (código %d)",
            linea_resumen or "sin resumen",
            duracion,
            ejecucion.exit_code,
        )
        return ejecucion

    async def check_file(self, path: str) -> SuiteRun:
        """Ejecuta los tests que cubren un archivo concreto.

        Busca `tests/test_<nombre>.py`; si no existe, ejecuta la suite filtrando
        por el nombre del módulo.
        """
        objetivo = Path(path)
        candidato = workspace_root() / "tests" / f"test_{objetivo.stem}.py"
        if candidato.is_file():
            return await self.run(str(candidato))
        return await self.run(keyword=objetivo.stem)


def _json_report_available() -> bool:
    try:
        import pytest_jsonreport  # noqa: F401
    except ImportError:
        return False
    return True
