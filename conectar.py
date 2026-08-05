#!/usr/bin/env python3
"""Asistente de conexión de IAs.

Un solo comando que dice qué modelos hay disponibles, qué falta y cómo
arreglarlo, y que deja el sistema listo para arrancar.

    python conectar.py            # diagnóstico y guía
    python conectar.py --arreglar # aplica las reparaciones automáticas
    python conectar.py --clave openrouter sk-or-v1-...

No guarda ninguna credencial sin comprobar antes que funciona.
"""
from __future__ import annotations

import argparse
import asyncio
import sys

from backend.app.core.env_loader import load_env


class C:
    VERDE = "\033[92m"
    ROJO = "\033[91m"
    AMARILLO = "\033[93m"
    AZUL = "\033[94m"
    GRIS = "\033[90m"
    NEGRITA = "\033[1m"
    FIN = "\033[0m"

    @classmethod
    def apagar(cls) -> None:
        for a in ("VERDE", "ROJO", "AMARILLO", "AZUL", "GRIS", "NEGRITA", "FIN"):
            setattr(cls, a, "")


ICONO = {
    "ready": f"{C.VERDE}[OK]{C.FIN}",
    "invalid": f"{C.ROJO}[CLAVE INVALIDA]{C.FIN}",
    "not_configured": f"{C.GRIS}[--]{C.FIN}",
    "unreachable": f"{C.AMARILLO}[SIN CONEXION]{C.FIN}",
}


def seccion(titulo: str) -> None:
    print(f"\n{C.AZUL}{C.NEGRITA}-- {titulo} {'-' * max(0, 54 - len(titulo))}{C.FIN}")


async def mostrar_estado() -> int:
    from backend.app.core.onboarding import build_report

    print(f"{C.NEGRITA}Conexión de IAs — SilhouetteAppcreator{C.FIN}")
    informe = await build_report()

    seccion("PROVEEDORES DE API")
    for p in informe.providers:
        icono = ICONO.get(p["status"], p["status"])
        print(f"  {icono} {p['label']:22} {C.GRIS}{p['detail']}{C.FIN}")

    seccion("AGENTES DE LINEA DE COMANDOS")
    for a in informe.cli_agents:
        if not a["available"]:
            continue
        # Instalado no es utilizable: se distinguen, porque un agente sin sesión
        # iniciada no sirve para nada aunque el ejecutable esté ahí.
        if a["usable"] is True:
            estado = f"{C.VERDE}[LISTO]{C.FIN}"
            nota = a["executable"]
        elif a["usable"] is False:
            estado = f"{C.AMARILLO}[SIN SESION]{C.FIN}"
            nota = a["probe_detail"][:80]
        else:
            estado = f"{C.GRIS}[SIN COMPROBAR]{C.FIN}"
            nota = a["executable"]
        print(f"  {estado} {a['label']:20} {C.GRIS}{nota}{C.FIN}")

    ausentes = [a["label"] for a in informe.cli_agents if not a["available"]]
    if ausentes:
        print(f"  {C.GRIS}[--] No instalados: {', '.join(ausentes)}{C.FIN}")

    if informe.issues:
        seccion("QUE HAY QUE HACER")
        for i in informe.issues:
            color = C.ROJO if i["severity"] == "blocker" else C.AMARILLO
            print(f"  {color}* {i['summary']}{C.FIN}")
            print(f"    {C.GRIS}{i['fix_hint']}{C.FIN}")
            if i["auto_fixable"]:
                print(f"    {C.VERDE}-> se arregla solo: python conectar.py --arreglar{C.FIN}")

    seccion("RESUMEN")
    if informe.has_any_llm:
        print(f"  {C.VERDE}{C.NEGRITA}{informe.ready_count} modelo(s) utilizables. El sistema puede arrancar.{C.FIN}")
        print(f"\n  {C.GRIS}Arranque:{C.FIN} python silhouettemcp_server.py")
        return 0

    print(f"  {C.ROJO}{C.NEGRITA}Ningún modelo utilizable.{C.FIN}")
    print(f"\n  {informe.to_dict()['next_step']}")
    print(f"\n  {C.NEGRITA}Las dos vías más rápidas:{C.FIN}")
    print(f"    1. {C.GRIS}Clave de OpenRouter (cientos de modelos, una sola clave):{C.FIN}")
    print("       python conectar.py --clave openrouter sk-or-v1-...")
    print(f"    2. {C.GRIS}Su cuenta de Google, sin gestionar claves:{C.FIN}")
    print("       gemini      (elija «Login with Google» en el primer arranque)")
    return 1


async def aplicar_reparaciones() -> int:
    from backend.app.core.onboarding import AUTO_FIXES, build_report

    informe = await build_report()
    pendientes = [i for i in informe.issues if i["auto_fixable"]]
    if not pendientes:
        print(f"{C.VERDE}No hay reparaciones automáticas pendientes.{C.FIN}")
        return 0

    for problema in pendientes:
        reparar = AUTO_FIXES.get(problema["fix_id"])
        if reparar is None:
            continue
        print(f"{C.AZUL}Reparando:{C.FIN} {problema['summary']}")
        resultado = reparar()
        if resultado.get("applied"):
            print(f"  {C.VERDE}[HECHO]{C.FIN} {resultado.get('detail', '')}")
            if resultado.get("backup"):
                print(f"  {C.GRIS}copia de seguridad: {resultado['backup']}{C.FIN}")
        else:
            print(f"  {C.AMARILLO}[SIN CAMBIOS]{C.FIN} {resultado.get('reason', '')}")

    print()
    return await mostrar_estado()


async def guardar_clave(proveedor: str, credencial: str) -> int:
    from backend.app.core.onboarding import connect_provider

    print(f"{C.AZUL}Verificando la credencial de {proveedor}...{C.FIN}")
    try:
        resultado = await connect_provider(proveedor, credencial)
    except KeyError as exc:
        print(f"{C.ROJO}{exc}{C.FIN}")
        return 2

    if resultado["saved"]:
        print(f"{C.VERDE}{C.NEGRITA}[OK]{C.FIN} {resultado['detail']}")
        return 0

    print(f"{C.ROJO}[RECHAZADA]{C.FIN} {resultado['detail']}")
    return 1


INSTALL_COMMANDS: dict[str, str] = {
    "claude": "npm install -g @anthropic-ai/claude-code",
    "codex": "npm install -g @openai/codex-cli",
    "gemini": "npm install -g @google/gemini-cli",
    "cursor": "npm install -g cursor-agent",
    "aider": "pip install aider-chat",
}


async def instalar_agente(agente: str) -> int:
    agente_key = agente.lower().strip()
    cmd = INSTALL_COMMANDS.get(agente_key)
    if not cmd:
        print(f"{C.ROJO}Agente desconocido '{agente}'. Opciónes soportadas: {', '.join(INSTALL_COMMANDS.keys())}{C.FIN}")
        return 1

    print(f"{C.AZUL}Ejecutando instalación para '{agente_key}': {cmd}...{C.FIN}")
    try:
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            print(f"{C.VERDE}{C.NEGRITA}[INSTALACIÓN COMPLETADA]{C.FIN} {agente_key} se instaló correctamente.")
            print()
            return await mostrar_estado()
        else:
            print(f"{C.ROJO}[ERROR EN INSTALACIÓN]{C.FIN} {stderr.decode(errors='replace')}")
            return 1
    except Exception as e:
        print(f"{C.ROJO}Error al ejecutar instalación: {e}{C.FIN}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Conecta y verifica proveedores de IA.")
    parser.add_argument("--arreglar", action="store_true", help="aplica las reparaciones automáticas")
    parser.add_argument(
        "--clave", nargs=2, metavar=("PROVEEDOR", "CREDENCIAL"), help="valida y guarda una clave"
    )
    parser.add_argument(
        "--instalar", metavar="AGENTE", help="instala automáticamente un agente CLI (claude, codex, gemini, cursor, aider)"
    )
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if not sys.stdout.isatty():
        C.apagar()

    load_env()

    if args.instalar:
        return asyncio.run(instalar_agente(args.instalar))
    if args.clave:
        return asyncio.run(guardar_clave(*args.clave))
    if args.arreglar:
        return asyncio.run(aplicar_reparaciones())
    return asyncio.run(mostrar_estado())


if __name__ == "__main__":
    raise SystemExit(main())
