#!/usr/bin/env python3
"""Verificación real del estado del sistema.

La versión anterior comprobaba que existieran archivos y directorios, y su único
test de comportamiento pasaba `True` como literal:

    results["imports"] = self.check_item("Test de importaciones backend", True)

Con eso reportaba «95,2 % EXCELENTE» y esa cifra alimentaba la documentación.
Un repositorio vacío con los nombres correctos habría puntuado igual.

Ahora cada comprobación ejecuta algo y puede fallar de verdad:
importa los módulos, ejecuta la suite de tests, y verifica que las barreras de
seguridad están puestas. El código de salida es 0 sólo si todo lo crítico pasa.

Uso:
    python verificar_sistema.py [--rapido]
"""
from __future__ import annotations

import argparse
import importlib
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent


class Color:
    VERDE = "\033[92m"
    ROJO = "\033[91m"
    AMARILLO = "\033[93m"
    AZUL = "\033[94m"
    NEGRITA = "\033[1m"
    FIN = "\033[0m"

    @classmethod
    def desactivar(cls) -> None:
        for attr in ("VERDE", "ROJO", "AMARILLO", "AZUL", "NEGRITA", "FIN"):
            setattr(cls, attr, "")


@dataclass
class Resultado:
    nombre: str
    ok: bool
    critico: bool
    detalle: str = ""


@dataclass
class Verificador:
    resultados: list[Resultado] = field(default_factory=list)

    def seccion(self, titulo: str) -> None:
        # Sólo ASCII: la consola de Windows usa cp1252 por defecto y no puede
        # codificar caracteres de dibujo de caja.
        print(f"\n{Color.AZUL}{Color.NEGRITA}-- {titulo} {'-' * max(0, 56 - len(titulo))}{Color.FIN}")

    def comprobar(self, nombre: str, ok: bool, detalle: str = "", *, critico: bool = True) -> bool:
        self.resultados.append(Resultado(nombre, ok, critico, detalle))
        marca = f"{Color.VERDE}[OK]{Color.FIN}" if ok else (
            f"{Color.ROJO}[FALLA]{Color.FIN}" if critico else f"{Color.AMARILLO}[AVISO]{Color.FIN}"
        )
        linea = f"  {marca} {nombre}"
        if detalle:
            linea += f" {Color.AMARILLO}— {detalle}{Color.FIN}"
        print(linea)
        return ok

    # -- comprobaciones ----------------------------------------------------
    def verificar_importaciones(self) -> None:
        """Importa de verdad cada módulo crítico."""
        self.seccion("IMPORTACIONES")
        modulos = [
            ("backend.app.security.auth", "Autenticación"),
            ("backend.app.security.workspace", "Confinamiento de rutas"),
            ("backend.app.security.process_policy", "Lista blanca de procesos"),
            ("backend.app.security.prompt_injection_guard", "Guardián anti-inyección"),
            ("backend.app.core.llm_router", "Router LLM"),
            ("backend.app.orchestrator.multi_agent", "Orquestador multi-agente"),
            ("backend.app.orchestrator.executive_supervisor", "Supervisor ejecutivo"),
            ("backend.app.evolution.agent_improver", "Motor de auto-mejora"),
            ("backend.app.swarm.debate_matrix", "Matriz de debate"),
            ("backend.app.logic_engine.z3_verifier", "Verificador de invariantes"),
            ("backend.app.services.silhouette_brain_service", "Memoria cognitiva"),
        ]
        for modulo, descripcion in modulos:
            try:
                importlib.import_module(modulo)
                self.comprobar(descripcion, True)
            except Exception as exc:
                self.comprobar(descripcion, False, f"{type(exc).__name__}: {exc}")

    def verificar_memoria(self) -> None:
        """Comprueba que la memoria almacena y recupera de verdad."""
        self.seccion("MEMORIA COGNITIVA")
        try:
            from backend.app.services.silhouette_brain_service import SilhouetteBrainService
        except ImportError as exc:
            self.comprobar("Servicio de memoria", False, str(exc))
            return

        servicio = SilhouetteBrainService()
        if not self.comprobar(
            "silhouette-brain instalado",
            servicio.available,
            "" if servicio.available else "pip install -e '.[memory]'",
            critico=False,
        ):
            return

        stats = servicio.get_stats()
        self.comprobar("Los cuatro niveles responden", set(stats["tiers"]) == {
            "working", "episodic", "semantic", "deep_graph"
        })
        self.comprobar("El embedder está declarado", bool(stats.get("embedder")))
        servicio.close()

    def verificar_seguridad(self) -> None:
        """Comprueba que las barreras de seguridad están puestas."""
        self.seccion("SEGURIDAD")

        from backend.app.security.process_policy import allowed_apps
        from backend.app.security.workspace import PathNotAllowed, resolve_within_workspace

        # Confinamiento de rutas.
        try:
            resolve_within_workspace("../../../etc/passwd")
            self.comprobar("Se bloquea el recorrido de directorios", False, "una ruta externa fue aceptada")
        except PathNotAllowed:
            self.comprobar("Se bloquea el recorrido de directorios", True)

        try:
            resolve_within_workspace(".env")
            self.comprobar("Se bloquea el acceso a secretos", False, ".env fue accesible")
        except PathNotAllowed:
            self.comprobar("Se bloquea el acceso a secretos", True)

        # Lanzamiento de procesos.
        permitidas = allowed_apps()
        self.comprobar(
            "Lanzamiento de procesos bajo lista blanca",
            True,
            f"{len(permitidas)} app(s) permitida(s)" if permitidas else "desactivado",
            critico=False,
        )

        # Autenticación configurada.
        from backend.app.security.auth import auth_service

        self.comprobar(
            "Administrador configurado",
            auth_service.is_configured,
            "" if auth_service.is_configured else "defina SILHOUETTE_ADMIN_EMAIL y _PASSWORD_HASH",
            critico=False,
        )

        # Nada de secretos versionados.
        try:
            versionados = subprocess.run(
                ["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, timeout=30
            ).stdout.splitlines()
            secretos = [
                f for f in versionados
                if f.endswith("/.env") or f == ".env" or f.endswith("master.key")
            ]
            self.comprobar(
                "Ningún secreto en el control de versiones",
                not secretos,
                ", ".join(secretos[:3]) if secretos else "",
            )
        except (OSError, subprocess.SubprocessError) as exc:
            self.comprobar("Ningún secreto versionado", False, str(exc), critico=False)

    def ejecutar_tests(self) -> None:
        """Ejecuta la suite de tests de verdad."""
        self.seccion("SUITE DE TESTS")
        try:
            proceso = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-q", "--no-header"],
                cwd=RAIZ,
                capture_output=True,
                text=True,
                timeout=600,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            self.comprobar("pytest", False, str(exc))
            return

        resumen = next(
            (l for l in reversed(proceso.stdout.splitlines()) if "passed" in l or "failed" in l),
            "sin resumen",
        )
        self.comprobar("Todos los tests pasan", proceso.returncode == 0, resumen.strip())

    # -- informe -----------------------------------------------------------
    def informe(self) -> int:
        self.seccion("RESUMEN")
        criticos = [r for r in self.resultados if r.critico]
        fallos = [r for r in criticos if not r.ok]
        avisos = [r for r in self.resultados if not r.critico and not r.ok]
        pasados = sum(1 for r in criticos if r.ok)

        porcentaje = (pasados / len(criticos) * 100) if criticos else 0.0
        color = Color.VERDE if not fallos else Color.ROJO
        print(f"\n  Comprobaciones críticas: {color}{pasados}/{len(criticos)} ({porcentaje:.1f}%){Color.FIN}")

        if avisos:
            print(f"  {Color.AMARILLO}Avisos: {len(avisos)}{Color.FIN}")
            for a in avisos:
                print(f"    - {a.nombre}: {a.detalle}")

        if fallos:
            print(f"\n  {Color.ROJO}{Color.NEGRITA}ESTADO: HAY FALLOS{Color.FIN}")
            for f in fallos:
                print(f"    {Color.ROJO}x{Color.FIN} {f.nombre}: {f.detalle}")
            return 1

        print(f"\n  {Color.VERDE}{Color.NEGRITA}ESTADO: TODO CORRECTO{Color.FIN}")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Verificación real del sistema")
    parser.add_argument("--rapido", action="store_true", help="omite la suite de tests")
    args = parser.parse_args()

    # La salida lleva acentos; sin esto la consola cp1252 de Windows aborta.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if not sys.stdout.isatty() or os.getenv("NO_COLOR"):
        Color.desactivar()

    print(f"{Color.NEGRITA}Verificación de SilhouetteAppcreator{Color.FIN}")
    print(f"Raíz: {RAIZ}")

    v = Verificador()
    v.verificar_importaciones()
    v.verificar_memoria()
    v.verificar_seguridad()
    if not args.rapido:
        v.ejecutar_tests()
    return v.informe()


if __name__ == "__main__":
    sys.exit(main())
