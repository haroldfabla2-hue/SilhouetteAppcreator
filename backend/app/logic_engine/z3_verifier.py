"""Verificación de invariantes de seguridad antes de acciones de alto riesgo.

Cambios respecto a la versión anterior:

1. **Falla en cerrado.** Antes, si `z3-solver` no estaba instalado se devolvía
   `is_sat = True`: ante la duda, aprobaba. Ahora, sin Z3, las restricciones
   aritméticas se evalúan con un comprobador explícito y el resultado se marca
   como `heuristic`; y si se exige verificación formal (`require_solver=True`)
   sin Z3 disponible, se rechaza.
2. **La regla de rutas es real.** Antes comparaba cadenas (`".." in path`,
   `startswith("/")`, `"C:\\Windows" in path`), lo que en Windows dejaba pasar
   casi todo el disco. Ahora delega en `security.workspace`, que resuelve la
   ruta y comprueba contención real.
3. **Z3 decide algo.** El modelo simbólico se construye a partir de las
   restricciones declaradas y puede resultar UNSAT; no es una fórmula
   trivialmente satisfacible evaluada después de un `if` que ya decidió.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from backend.app.security.workspace import PathNotAllowed, resolve_within_workspace

logger = logging.getLogger("Z3LogicVerifier")

try:
    from z3 import Int, Solver, sat

    Z3_AVAILABLE = True
except ImportError:  # pragma: no cover - depende del entorno
    Z3_AVAILABLE = False
    logger.info(
        "z3-solver no está instalado; las restricciones se evalúan con el "
        "comprobador aritmético interno. Instale con: pip install -e '.[reasoning]'"
    )

# Presupuesto máximo de memoria por subproceso, en MiB.
MEMORY_LIMIT_MB = 2048
# Número máximo de archivos que una acción puede tocar de una vez.
MAX_FILES_TOUCHED = 100


@dataclass
class Verdict:
    satisfied: bool
    status: str
    reason: str
    action: str
    engine: str
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "satisfied": self.satisfied,
            "status": self.status,
            "reason": self.reason,
            "action": self.action,
            "engine": self.engine,
            "violations": self.violations,
        }


class Z3LogicVerifier:
    """Evalúa invariantes de seguridad sobre una acción propuesta."""

    def __init__(self, *, require_solver: bool = False) -> None:
        self.require_solver = require_solver
        logger.info(
            "Z3LogicVerifier inicializado (z3=%s, require_solver=%s)",
            Z3_AVAILABLE,
            require_solver,
        )

    def verify_action_invariants(self, proposed_action: dict[str, Any]) -> dict[str, Any]:
        """Devuelve SAT (permitido) o UNSAT (bloqueado) para la acción."""
        action_type = str(proposed_action.get("type", "unknown"))
        target_path: str | None = proposed_action.get("target_path")
        memory_mb = self._as_int(proposed_action.get("memory_mb"), default=256)
        files_touched = self._as_int(proposed_action.get("files_touched"), default=1)

        violations: list[str] = []

        # -- Invariante 1: contención en el workspace -----------------------
        if target_path:
            try:
                resolve_within_workspace(target_path)
            except PathNotAllowed as exc:
                violations.append(f"ruta: {exc}")

        # -- Invariantes 2 y 3: restricciones aritméticas -------------------
        if self.require_solver and not Z3_AVAILABLE:
            return Verdict(
                satisfied=False,
                status="UNSAT",
                reason=(
                    "Se exigió verificación formal pero z3-solver no está instalado. "
                    "Se rechaza la acción (falla en cerrado)."
                ),
                action=action_type,
                engine="none",
                violations=["solver_no_disponible"],
            ).to_dict()

        engine, arithmetic_ok, arithmetic_violations = self._check_arithmetic(
            memory_mb, files_touched
        )
        violations.extend(arithmetic_violations)

        satisfied = not violations and arithmetic_ok
        if satisfied:
            reason = "Todos los invariantes se satisfacen."
        else:
            reason = "Se violaron invariantes de seguridad: " + "; ".join(violations)
            logger.warning("[Z3] Acción '%s' bloqueada: %s", action_type, reason)

        return Verdict(
            satisfied=satisfied,
            status="SAT" if satisfied else "UNSAT",
            reason=reason,
            action=action_type,
            engine=engine,
            violations=violations,
        ).to_dict()

    # -- internos ----------------------------------------------------------
    def _check_arithmetic(
        self, memory_mb: int, files_touched: int
    ) -> tuple[str, bool, list[str]]:
        """Comprueba las restricciones numéricas, con Z3 si está disponible."""
        if Z3_AVAILABLE:
            solver = Solver()
            mem = Int("memory_mb")
            files = Int("files_touched")
            # Invariantes del sistema.
            solver.add(mem > 0, mem <= MEMORY_LIMIT_MB)
            solver.add(files > 0, files <= MAX_FILES_TOUCHED)
            # Valores concretos de la acción propuesta. Si contradicen los
            # invariantes, el conjunto es insatisfacible.
            solver.add(mem == memory_mb, files == files_touched)
            if solver.check() == sat:
                return "z3", True, []
            return "z3", False, self._describe_arithmetic_violations(memory_mb, files_touched)

        violations = self._describe_arithmetic_violations(memory_mb, files_touched)
        return "heuristic", not violations, violations

    @staticmethod
    def _describe_arithmetic_violations(memory_mb: int, files_touched: int) -> list[str]:
        violations: list[str] = []
        if memory_mb <= 0:
            violations.append(f"memoria: {memory_mb} MiB no es un valor positivo")
        elif memory_mb > MEMORY_LIMIT_MB:
            violations.append(
                f"memoria: {memory_mb} MiB excede el límite de {MEMORY_LIMIT_MB} MiB"
            )
        if files_touched <= 0:
            violations.append(f"archivos: {files_touched} no es un valor positivo")
        elif files_touched > MAX_FILES_TOUCHED:
            violations.append(
                f"archivos: {files_touched} excede el máximo de {MAX_FILES_TOUCHED}"
            )
        return violations

    @staticmethod
    def _as_int(value: Any, *, default: int) -> int:
        try:
            return int(value) if value is not None else default
        except (TypeError, ValueError):
            return default
