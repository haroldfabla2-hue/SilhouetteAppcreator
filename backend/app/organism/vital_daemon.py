"""El daemon vital: el organismo que sigue vivo sin que nadie interactúe.

Portado del `UnifiedDaemon` de silhouette-brain y del bucle proactivo de
Silhouette Agency OS, con sus tres propiedades esenciales:

1. **Aislamiento de fallos.** Un motor que revienta jamás tumba al organismo.
   Se registra su fallo, se marca su salud y el resto sigue latiendo. Es la
   propiedad que separa un organismo de un script.
2. **Estado persistente.** Cuándo se ejecutó cada motor sobrevive al reinicio,
   así que reiniciar no borra el ritmo ni dispara todo a la vez.
3. **Instancia única.** Un fichero de bloqueo con el PID impide que dos
   organismos compitan por la misma memoria.

Sobre eso se añade lo que lo hace biomimético:

- La **homeostasis** ajusta la cadencia a los recursos del anfitrión: bajo
  presión piensa más despacio, nunca menos profundamente.
- El **ritmo circadiano** decide qué motores tienen sentido ahora: consolidar
  memoria mientras nadie mira, apartarse cuando el usuario está trabajando.

El resultado es un sistema que hace trabajo útil de madrugada y se aparta
cuando le hablas.
"""
from __future__ import annotations

import asyncio
import contextlib
import inspect
import json
import logging
import os
import time
from collections import deque
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from backend.app.organism.circadian import CircadianRhythm
from backend.app.organism.homeostasis import Homeostasis

logger = logging.getLogger("VitalDaemon")

DEFAULT_STATE_PATH = Path("data/organism_state.json")
DEFAULT_LOCK_PATH = Path("data/organism.lock")

# Cada cuánto despierta el planificador a comprobar qué toca.
TICK_INTERVAL_S = 10.0
MAX_EVENT_HISTORY = 200
# Fallos consecutivos tras los cuales un motor se considera enfermo.
UNHEALTHY_AFTER_FAILURES = 3


class OrganismAlreadyRunning(RuntimeError):
    """Ya hay otro organismo vivo sobre el mismo estado."""


# Bloqueos retenidos por este proceso. El fichero con el PID no distingue dos
# instancias dentro del mismo proceso, así que se lleva también en memoria.
_LOCKS_HELD_IN_PROCESS: set[str] = set()


@dataclass
class OrganCheck:
    """Resultado de una ejecución de un motor."""

    organ: str
    ok: bool
    duration_ms: float
    timestamp: float = field(default_factory=time.time)
    summary: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Organ:
    """Un motor del organismo, con su cadencia y su salud."""

    name: str
    fn: Callable[[], Any]
    base_interval_s: float
    last_run: float = 0.0
    runs: int = 0
    failures: int = 0
    consecutive_failures: int = 0
    last_error: str | None = None
    # Si es False, el motor sigue registrado pero no se ejecuta.
    enabled: bool = True

    @property
    def healthy(self) -> bool:
        return self.consecutive_failures < UNHEALTHY_AFTER_FAILURES

    def due(self, now: float, interval_s: float) -> bool:
        return self.enabled and (now - self.last_run) >= interval_s

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "base_interval_s": self.base_interval_s,
            "last_run": self.last_run,
            "runs": self.runs,
            "failures": self.failures,
            "consecutive_failures": self.consecutive_failures,
            "healthy": self.healthy,
            "enabled": self.enabled,
            "last_error": self.last_error,
        }


class VitalDaemon:
    """Mantiene vivo el organismo: late, se adapta y trabaja mientras nadie mira."""

    def __init__(
        self,
        *,
        state_path: Path = DEFAULT_STATE_PATH,
        lock_path: Path = DEFAULT_LOCK_PATH,
        tick_interval_s: float = TICK_INTERVAL_S,
        homeostasis: Homeostasis | None = None,
        circadian: CircadianRhythm | None = None,
        single_instance: bool = True,
    ) -> None:
        self.state_path = Path(state_path)
        self.lock_path = Path(lock_path)
        self.tick_interval_s = tick_interval_s
        self.homeostasis = homeostasis or Homeostasis()
        self.circadian = circadian or CircadianRhythm()
        self.single_instance = single_instance

        self._organs: dict[str, Organ] = {}
        self._events: deque[OrganCheck] = deque(maxlen=MAX_EVENT_HISTORY)
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._ticks = 0
        self._born_at = 0.0
        self._holds_lock = False

        self.register("heartbeat", self._heartbeat, 60.0)
        self._load_state()

    # -- registro de órganos ----------------------------------------------
    def register(self, name: str, fn: Callable[[], Any], interval_s: float) -> Organ:
        """Da de alta un motor. `fn` puede ser síncrona o asíncrona."""
        organo = self._organs.get(name)
        if organo is not None:
            # Conserva la historia (last_run, contadores) al re-registrar.
            organo.fn = fn
            organo.base_interval_s = interval_s
            return organo

        organo = Organ(name=name, fn=fn, base_interval_s=interval_s)
        self._organs[name] = organo
        return organo

    def set_enabled(self, name: str, enabled: bool) -> bool:
        organo = self._organs.get(name)
        if organo is None:
            return False
        organo.enabled = enabled
        return True

    async def _heartbeat(self) -> str:
        """El latido: la señal mínima de que el organismo sigue vivo."""
        estado = self.circadian.current()
        return f"vivo en fase {estado.phase.value}"

    # -- ciclo de vida -----------------------------------------------------
    @property
    def is_alive(self) -> bool:
        return self._running

    def start(self) -> None:
        """Da vida al organismo. Requiere un bucle de eventos en marcha."""
        if self._running:
            return
        if self.single_instance:
            self._acquire_lock()

        self._running = True
        self._born_at = time.time()
        self._task = asyncio.create_task(self._live(), name="organism-vital-loop")

        # El diagnóstico de arranque es informativo: si la homeostasis falla,
        # el organismo nace igualmente. Nada que sea sólo un log puede impedir
        # que empiece a latir.
        try:
            config = self.homeostasis.synthesize()
            logger.info(
                "[Organismo] Vivo. Perfil %s (%s). %d órgano(s) registrado(s).",
                config.profile,
                config.reason,
                len(self._organs),
            )
        except Exception as exc:  # noqa: BLE001 - el arranque no puede fallar por un log
            logger.warning(
                "[Organismo] Vivo, pero la homeostasis no pudo medirse al arrancar: %s", exc
            )

    async def stop(self) -> None:
        """Detiene el organismo con orden, guardando su estado."""
        if not self._running:
            return
        self._running = False
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        self._save_state()
        self._release_lock()
        logger.info("[Organismo] Detenido tras %d tick(s)", self._ticks)

    async def _live(self) -> None:
        """El bucle vital. Sobrevive a cualquier fallo de cualquier órgano."""
        while self._running:
            try:
                await asyncio.sleep(self.tick_interval_s)
                if not self._running:
                    return
                await self.tick()
            except asyncio.CancelledError:
                raise
            except Exception:
                # Ni siquiera un fallo del propio planificador detiene la vida.
                logger.exception("[Organismo] Fallo en el bucle vital; continúa latiendo")

    async def tick(self) -> list[OrganCheck]:
        """Un latido: ejecuta los órganos que tocan según fase y recursos."""
        self._ticks += 1
        ahora = time.time()

        fase = self.circadian.current()
        config = self.homeostasis.synthesize()
        # La cadencia final combina presión de recursos y fase del ciclo.
        factor = config.cadence_multiplier * fase.cadence_multiplier

        pendientes = [
            organo
            for organo in self._organs.values()
            if fase.allows(organo.name) and organo.due(ahora, organo.base_interval_s * factor)
        ]
        if not pendientes:
            return []

        # La concurrencia la marca la homeostasis: en un anfitrión ahogado, uno.
        semaforo = asyncio.Semaphore(max(1, config.max_concurrency))

        async def ejecutar(organo: Organ) -> OrganCheck:
            async with semaforo:
                return await self._run_organ(organo)

        resultados = await asyncio.gather(*(ejecutar(o) for o in pendientes))
        self._save_state()
        return list(resultados)

    async def _run_organ(self, organo: Organ) -> OrganCheck:
        """Ejecuta un órgano con aislamiento total de fallos."""
        inicio = time.perf_counter()
        organo.last_run = time.time()
        organo.runs += 1

        try:
            resultado = organo.fn()
            if inspect.isawaitable(resultado):
                resultado = await resultado
            organo.consecutive_failures = 0
            organo.last_error = None
            check = OrganCheck(
                organ=organo.name,
                ok=True,
                duration_ms=(time.perf_counter() - inicio) * 1000,
                summary=str(resultado)[:200] if resultado is not None else "",
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            organo.failures += 1
            organo.consecutive_failures += 1
            organo.last_error = f"{type(exc).__name__}: {exc}"
            logger.warning(
                "[Organismo] Órgano '%s' falló (%d consecutivo/s): %s",
                organo.name,
                organo.consecutive_failures,
                exc,
            )
            if not organo.healthy:
                logger.error(
                    "[Organismo] Órgano '%s' enfermo tras %d fallos seguidos",
                    organo.name,
                    organo.consecutive_failures,
                )
            check = OrganCheck(
                organ=organo.name,
                ok=False,
                duration_ms=(time.perf_counter() - inicio) * 1000,
                error=organo.last_error,
            )

        self._events.append(check)
        return check

    # -- persistencia ------------------------------------------------------
    def _load_state(self) -> None:
        """Recupera el ritmo previo para no dispararlo todo al reiniciar."""
        if not self.state_path.exists():
            return
        try:
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("No se pudo leer el estado del organismo (%s)", exc)
            return

        for nombre, datos in raw.get("organs", {}).items():
            organo = self._organs.get(nombre)
            if organo is None:
                # El órgano aún no se ha registrado; se guarda para cuando llegue.
                organo = Organ(name=nombre, fn=lambda: None, base_interval_s=3600.0, enabled=False)
                self._organs[nombre] = organo
            organo.last_run = datos.get("last_run", 0.0)
            organo.runs = datos.get("runs", 0)
            organo.failures = datos.get("failures", 0)

    def _save_state(self) -> None:
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "saved_at": time.time(),
                "ticks": self._ticks,
                "organs": {
                    n: {"last_run": o.last_run, "runs": o.runs, "failures": o.failures}
                    for n, o in self._organs.items()
                },
            }
            tmp = self.state_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            tmp.replace(self.state_path)
        except OSError as exc:
            logger.warning("No se pudo guardar el estado del organismo: %s", exc)

    # -- instancia única ---------------------------------------------------
    def _acquire_lock(self) -> None:
        """Impide que dos organismos compitan por la misma memoria.

        Cubre los dos casos: otro proceso (vía el PID del fichero) y otra
        instancia dentro de este mismo proceso (vía el registro en memoria).
        El segundo caso es el más fácil de provocar por accidente — dos
        `VitalDaemon()` en el mismo servidor — y el PID no lo detectaría.
        """
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        clave = str(self.lock_path.resolve())

        if clave in _LOCKS_HELD_IN_PROCESS:
            raise OrganismAlreadyRunning(
                f"Ya hay un organismo vivo en este mismo proceso sobre {self.lock_path}."
            )

        if self.lock_path.exists():
            try:
                pid = int(self.lock_path.read_text(encoding="utf-8").strip())
            except (OSError, ValueError):
                pid = -1
            if pid > 0 and pid != os.getpid() and _process_alive(pid):
                raise OrganismAlreadyRunning(
                    f"Ya hay un organismo vivo con PID {pid}. "
                    f"Si es un residuo, borre {self.lock_path}."
                )
            if pid > 0 and pid != os.getpid():
                logger.info("[Organismo] Bloqueo huérfano de un PID muerto; se reclama")

        self.lock_path.write_text(str(os.getpid()), encoding="utf-8")
        _LOCKS_HELD_IN_PROCESS.add(clave)
        self._holds_lock = True

    def _release_lock(self) -> None:
        if not self._holds_lock:
            return
        _LOCKS_HELD_IN_PROCESS.discard(str(self.lock_path.resolve()))
        with contextlib.suppress(OSError):
            self.lock_path.unlink()
        self._holds_lock = False

    # -- introspección -----------------------------------------------------
    def vitals(self) -> dict[str, Any]:
        """Signos vitales del organismo."""
        fase = self.circadian.current()
        config = self.homeostasis.synthesize()
        organos = list(self._organs.values())
        enfermos = [o.name for o in organos if not o.healthy]
        total_ejecuciones = sum(o.runs for o in organos)
        total_fallos = sum(o.failures for o in organos)

        if enfermos:
            salud = "critical" if len(enfermos) > len(organos) / 2 else "degraded"
        else:
            salud = "healthy"

        return {
            "alive": self._running,
            "health": salud,
            "uptime_s": round(time.time() - self._born_at, 1) if self._born_at else 0.0,
            "ticks": self._ticks,
            "circadian": fase.to_dict(),
            "homeostasis": config.to_dict(),
            "organs": {
                "total": len(organos),
                "healthy": len(organos) - len(enfermos),
                "unhealthy": enfermos,
                "detail": [o.to_dict() for o in organos],
            },
            "activity": {
                "total_runs": total_ejecuciones,
                "total_failures": total_fallos,
                "failure_rate": (
                    round(total_fallos / total_ejecuciones, 4) if total_ejecuciones else None
                ),
            },
            "recent_events": [e.to_dict() for e in list(self._events)[-15:]],
        }

    def touch(self) -> None:
        """Señala que hubo interacción: devuelve el organismo a la vigilia."""
        self.circadian.touch()


def _process_alive(pid: int) -> bool:
    """Comprueba si un PID sigue vivo, sin depender de psutil."""
    try:
        import psutil

        return psutil.pid_exists(pid)
    except ImportError:
        pass
    if os.name == "nt":  # pragma: no cover - específico de Windows
        return True  # Sin psutil en Windows no se puede saber: se asume vivo.
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True
