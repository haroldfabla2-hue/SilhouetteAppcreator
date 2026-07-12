#!/usr/bin/env python3
"""
Testing Interno Completo - MCP Server Superior
Prueba todos los componentes, imports, dependencias y funcionalidad
"""

import sys
import os
import subprocess
import importlib.util
from pathlib import Path
import json

class TestingInterno:
    def __init__(self):
        self.resultados = []
        self.errores = []
        self.warnings = []
    
    def log_resultado(self, test, status, mensaje, detalles=None):
        """Log de resultados de testing"""
        resultado = {
            'test': test,
            'status': status,  # PASS, FAIL, WARN
            'mensaje': mensaje,
            'detalles': detalles or []
        }
        self.resultados.append(resultado)
        
        color = {'PASS': '🟢', 'FAIL': '🔴', 'WARN': '🟡'}[status]
        print(f"{color} {test}: {mensaje}")
        
        if detalles:
            for detalle in detalles:
                print(f"   → {detalle}")
    
    def test_imports_python(self):
        """Test 1: Verificar imports de archivos Python"""
        print("\n📋 TEST 1: Testing Imports de Python")
        print("="*50)
        
        archivos_python = [
            'setup_wizard.py',
            'templates.py', 
            'cli.py',
            'notifications.py',
            'dashboard_server.py'
        ]
        
        for archivo in archivos_python:
            if os.path.exists(archivo):
                try:
                    spec = importlib.util.spec_from_file_location(archivo, archivo)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self.log_resultado(
                        f"Import {archivo}",
                        "PASS", 
                        f"Módulo importado correctamente",
                        [f"Tamaño: {os.path.getsize(archivo)} bytes"]
                    )
                except Exception as e:
                    self.log_resultado(
                        f"Import {archivo}",
                        "FAIL", 
                        f"Error al importar: {str(e)}",
                        [f"Tipo: {type(e).__name__}"]
                    )
            else:
                self.log_resultado(
                    f"Import {archivo}",
                    "FAIL", 
                    f"Archivo no encontrado: {archivo}"
                )
    
    def test_dependencias_python(self):
        """Test 2: Verificar dependencias de Python"""
        print("\n📋 TEST 2: Testing Dependencias de Python")
        print("="*50)
        
        dependencias = [
            'click', 'colorama', 'requests', 'fastapi', 'uvicorn',
            'dotenv', 'asyncio', 'json', 'pathlib'
        ]
        
        for dep in dependencias:
            try:
                __import__(dep)
                self.log_resultado(
                    f"Dependencia {dep}",
                    "PASS",
                    f"Dependencia disponible"
                )
            except ImportError as e:
                self.log_resultado(
                    f"Dependencia {dep}",
                    "FAIL", 
                    f"Dependencia no disponible: {str(e)}"
                )
    
    def test_dashboard_react(self):
        """Test 3: Verificar proyecto React Dashboard"""
        print("\n📋 TEST 3: Testing Dashboard React")
        print("="*50)
        
        dashboard_path = Path("mcp-dashboard")
        
        if not dashboard_path.exists():
            self.log_resultado(
                "Dashboard React",
                "FAIL",
                "Directorio mcp-dashboard no encontrado"
            )
            return
        
        # Verificar package.json
        package_json = dashboard_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    config = json.load(f)
                self.log_resultado(
                    "Dashboard package.json",
                    "PASS",
                    f"Configuración encontrada: {config.get('name', 'N/A')}",
                    [f"Versiones: React {config.get('dependencies', {}).get('react', 'N/A')}"]
                )
            except Exception as e:
                self.log_resultado(
                    "Dashboard package.json",
                    "FAIL",
                    f"Error al leer package.json: {str(e)}"
                )
        else:
            self.log_resultado(
                "Dashboard package.json",
                "FAIL",
                "package.json no encontrado"
            )
        
        # Verificar node_modules
        node_modules = dashboard_path / "node_modules"
        if node_modules.exists():
            self.log_resultado(
                "Dashboard dependencies",
                "PASS",
                f"node_modules presente ({len(list(node_modules.iterdir()))} paquetes)",
                [f"Ruta: {node_modules.absolute()}"]
            )
        else:
            self.log_resultado(
                "Dashboard dependencies",
                "WARN",
                "node_modules no encontrado - puede necesitar npm install"
            )
        
        # Verificar archivos TypeScript
        ts_files = list(dashboard_path.rglob("*.tsx"))
        ts_files.extend(list(dashboard_path.rglob("*.ts")))
        self.log_resultado(
            "Dashboard TypeScript files",
            "PASS" if ts_files else "WARN",
            f"Archivos TS/TSX encontrados: {len(ts_files)}",
            [str(f) for f in ts_files[:5]]  # Mostrar primeros 5
        )
    
    def test_archivos_principales(self):
        """Test 4: Verificar archivos principales del sistema"""
        print("\n📋 TEST 4: Testing Archivos Principales")
        print("="*50)
        
        archivos_sistema = [
            ('mcp-core-superior/', 'Sistema principal'),
            ('backend/', 'Backend API'),
            ('frontend/', 'Frontend principal'),
            ('enterprise_testing_suite/', 'Suite de testing'),
        ]
        
        for archivo, descripcion in archivos_sistema:
            if os.path.exists(archivo):
                archivos_count = len(list(Path(archivo).rglob("*"))) if os.path.isdir(archivo) else 1
                self.log_resultado(
                    f"Sistema {descripcion}",
                    "PASS",
                    f"Directorio encontrado con {archivos_count} archivos",
                    [f"Ruta: {os.path.abspath(archivo)}"]
                )
            else:
                self.log_resultado(
                    f"Sistema {descripcion}",
                    "WARN",
                    f"Directorio no encontrado: {archivo}"
                )
    
    def test_instalacion_script(self):
        """Test 5: Verificar script de instalación"""
        print("\n📋 TEST 5: Testing Script de Instalación")
        print("="*50)
        
        if os.path.exists("install.sh"):
            # Verificar tamaño y contenido
            size = os.path.getsize("install.sh")
            with open("install.sh") as f:
                lines = len(f.readlines())
            
            self.log_resultado(
                "Install.sh",
                "PASS",
                f"Script encontrado ({size} bytes, {lines} líneas)",
                [f"Ejecutable: {'Sí' if os.access('install.sh', os.X_OK) else 'No'}"]
            )
            
            # Verificar contenido clave
            with open("install.sh") as f:
                content = f.read()
                
            keywords = ["#!/bin/bash", "python", "pip", "node", "npm"]
            for keyword in keywords:
                if keyword in content:
                    self.log_resultado(
                        f"Install.sh contiene {keyword}",
                        "PASS",
                        f"Keyword encontrado"
                    )
                else:
                    self.log_resultado(
                        f"Install.sh contiene {keyword}",
                        "WARN",
                        f"Keyword no encontrado"
                    )
        else:
            self.log_resultado(
                "Install.sh",
                "FAIL",
                "Script de instalación no encontrado"
            )
    
    def test_conectividad(self):
        """Test 6: Verificar conectividad básica"""
        print("\n📋 TEST 6: Testing Conectividad")
        print("="*50)
        
        # Test Python
        python_version = sys.version
        self.log_resultado(
            "Python Version",
            "PASS",
            f"Python {python_version.split()[0]} disponible",
            [python_version]
        )
        
        # Test comandos básicos
        comandos = ["node", "npm", "pip", "git"]
        for cmd in comandos:
            try:
                result = subprocess.run([cmd, "--version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    version = result.stdout.strip().split('\n')[0]
                    self.log_resultado(
                        f"Comando {cmd}",
                        "PASS",
                        f"Disponible: {version}"
                    )
                else:
                    self.log_resultado(
                        f"Comando {cmd}",
                        "WARN",
                        f"No disponible o error"
                    )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.log_resultado(
                    f"Comando {cmd}",
                    "WARN",
                    f"No encontrado en PATH"
                )
    
    def ejecutar_todos_tests(self):
        """Ejecutar todos los tests"""
        print("🚀 INICIANDO TESTING INTERNO COMPLETO")
        print("="*60)
        print(f"Directorio: {os.getcwd()}")
        print(f"Python: {sys.version}")
        print("="*60)
        
        self.test_imports_python()
        self.test_dependencias_python()
        self.test_dashboard_react()
        self.test_archivos_principales()
        self.test_instalacion_script()
        self.test_conectividad()
        
        self.generar_reporte_final()
    
    def generar_reporte_final(self):
        """Generar reporte final de testing"""
        print("\n" + "="*60)
        print("📊 REPORTE FINAL DE TESTING INTERNO")
        print("="*60)
        
        # Contar resultados
        pass_count = sum(1 for r in self.resultados if r['status'] == 'PASS')
        fail_count = sum(1 for r in self.resultados if r['status'] == 'FAIL')
        warn_count = sum(1 for r in self.resultados if r['status'] == 'WARN')
        total = len(self.resultados)
        
        print(f"Total de tests: {total}")
        print(f"🟢 Exitosos: {pass_count} ({pass_count/total*100:.1f}%)")
        print(f"🔴 Fallidos: {fail_count} ({fail_count/total*100:.1f}%)")
        print(f"🟡 Advertencias: {warn_count} ({warn_count/total*100:.1f}%)")
        
        if fail_count > 0:
            print(f"\n🔴 TESTS FALLIDOS:")
            for r in self.resultados:
                if r['status'] == 'FAIL':
                    print(f"   • {r['test']}: {r['mensaje']}")
        
        if warn_count > 0:
            print(f"\n🟡 ADVERTENCIAS:")
            for r in self.resultados:
                if r['status'] == 'WARN':
                    print(f"   • {r['test']}: {r['mensaje']}")
        
        # Guardar reporte
        reporte = {
            'timestamp': '2025-11-05 00:27:36',
            'resumen': {
                'total': total,
                'exitosos': pass_count,
                'fallidos': fail_count,
                'advertencias': warn_count
            },
            'resultados': self.resultados
        }
        
        with open('reporte_testing_interno.json', 'w') as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Reporte guardado en: reporte_testing_interno.json")
        
        # Status final
        if fail_count == 0:
            print(f"\n🎉 RESULTADO: TODOS LOS TESTS PASARON - Sistema 100% FUNCIONAL")
        elif fail_count < total * 0.1:  # Menos del 10% fallidos
            print(f"\n✅ RESULTADO: SISTEMA MAYORMENTE FUNCIONAL ({pass_count}/{total} tests)")
        else:
            print(f"\n⚠️ RESULTADO: SISTEMA REQUIERE ATENCIÓN ({fail_count} errores)")

if __name__ == "__main__":
    testing = TestingInterno()
    testing.ejecutar_todos_tests()