#!/usr/bin/env python3
"""
Script para ejecutar la suite completa de tests de Microsoft 365 Integration.
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Ejecutar comando y mostrar salida."""
    print(f"\n{'='*60}")
    print(f"Ejecutando: {description}")
    print(f"Comando: {cmd}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=False)
        print(f"✅ {description} - EXITOSO")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FALLÓ (código: {e.returncode})")
        return False


def setup_test_environment():
    """Configurar entorno de testing."""
    print("🔧 Configurando entorno de testing...")
    
    # Crear directorio de coverage si no existe
    os.makedirs("htmlcov", exist_ok=True)
    os.makedirs("test-reports", exist_ok=True)
    
    # Configurar variables de entorno para tests
    env_vars = {
        "PYTHONPATH": str(Path.cwd()),
        "TESTING": "true",
        "LOG_LEVEL": "ERROR",  # Reducir output de logs en tests
        "DISABLE_REDIS": "true",  # Deshabilitar Redis en tests
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print("✅ Entorno configurado")


def install_test_dependencies():
    """Instalar dependencias de testing."""
    print("\n📦 Instalando dependencias de testing...")
    
    cmd = "pip install -r tests/requirements.txt"
    return run_command(cmd, "Instalación de dependencias")


def run_unit_tests():
    """Ejecutar tests unitarios."""
    print("\n🧪 Ejecutando tests unitarios...")
    
    cmd = (
        "python -m pytest tests/unit/ "
        "-v "
        "--tb=short "
        "--cov=src "
        "--cov-report=term-missing "
        "--cov-report=html:htmlcov/unit "
        "--cov-report=xml:coverage-unit.xml "
        "--cov-fail-under=85 "
        "--junitxml=test-reports/unit-tests.xml "
        "-m 'unit and not slow'"
    )
    
    return run_command(cmd, "Tests Unitarios")


def run_integration_tests():
    """Ejecutar tests de integración."""
    print("\n🔗 Ejecutando tests de integración...")
    
    cmd = (
        "python -m pytest tests/integration/ "
        "-v "
        "--tb=short "
        "--cov=src.graph "
        "--cov-report=term-missing "
        "--cov-report=html:htmlcov/integration "
        "--cov-report=xml:coverage-integration.xml "
        "--cov-fail-under=80 "
        "--junitxml=test-reports/integration-tests.xml "
        "-m 'integration and not slow'"
    )
    
    return run_command(cmd, "Tests de Integración")


def run_e2e_tests():
    """Ejecutar tests end-to-end."""
    print("\n🎯 Ejecutando tests end-to-end...")
    
    cmd = (
        "python -m pytest tests/e2e/ "
        "-v "
        "--tb=short "
        "--junitxml=test-reports/e2e-tests.xml "
        "-m 'e2e and not slow'"
    )
    
    return run_command(cmd, "Tests End-to-End")


def run_all_tests():
    """Ejecutar todos los tests."""
    print("\n🚀 Ejecutando suite completa de tests...")
    
    cmd = (
        "python -m pytest tests/ "
        "-v "
        "--tb=short "
        "--cov=src "
        "--cov-report=term-missing "
        "--cov-report=html:htmlcov "
        "--cov-report=xml:coverage.xml "
        "--cov-fail-under=85 "
        "--junitxml=test-reports/all-tests.xml "
        "--html=test-reports/test-report.html "
        "--self-contained-html "
        "-n auto"  # Ejecución paralela
    )
    
    return run_command(cmd, "Todos los Tests")


def run_specific_test_category(category):
    """Ejecutar tests de categoría específica."""
    category_map = {
        "word": "tests/unit/test_word_agent.py",
        "excel": "tests/unit/test_excel_agent.py", 
        "powerpoint": "tests/unit/test_powerpoint_agent.py",
        "outlook": "tests/unit/test_outlook_agent.py",
        "onedrive": "tests/unit/test_onedrive_agent.py",
        "teams": "tests/unit/test_teams_agent.py",
        "utils": "tests/unit/test_utils.py",
        "integration": "tests/integration/",
        "e2e": "tests/e2e/",
        "graph": "tests/integration/test_graph_client.py"
    }
    
    if category not in category_map:
        print(f"❌ Categoría '{category}' no reconocida")
        print(f"Categorías disponibles: {list(category_map.keys())}")
        return False
    
    target = category_map[category]
    print(f"\n🎯 Ejecutando tests de categoría: {category}")
    
    cmd = f"python -m pytest {target} -v --cov=src --cov-report=term-missing"
    
    return run_command(cmd, f"Tests de {category.title()}")


def run_performance_tests():
    """Ejecutar tests de rendimiento."""
    print("\n⚡ Ejecutando tests de rendimiento...")
    
    cmd = (
        "python -m pytest tests/ "
        "-v "
        "--benchmark-only "
        "--benchmark-html=test-reports/benchmark.html "
        "-m 'slow'"
    )
    
    return run_command(cmd, "Tests de Rendimiento")


def generate_coverage_report():
    """Generar reporte de cobertura."""
    print("\n📊 Generando reporte de cobertura...")
    
    cmd = (
        "python -m coverage combine "
        "&& python -m coverage report "
        "&& python -m coverage html"
    )
    
    return run_command(cmd, "Reporte de Cobertura")


def lint_code():
    """Ejecutar linter de código."""
    print("\n🔍 Ejecutando linting de código...")
    
    commands = [
        ("flake8 src/ --max-line-length=88 --extend-ignore=E203,W503", "Flake8"),
        ("black --check src/", "Black (formato)"),
        ("isort --check-only src/", "isort (imports)")
    ]
    
    all_passed = True
    for cmd, description in commands:
        if not run_command(cmd, description):
            all_passed = False
    
    return all_passed


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description="Ejecutor de tests para Microsoft 365 Integration")
    parser.add_argument(
        "category",
        nargs="?",
        choices=["unit", "integration", "e2e", "all", "word", "excel", "powerpoint", "outlook", "onedrive", "teams", "utils", "graph", "performance", "lint"],
        default="all",
        help="Categoría de tests a ejecutar"
    )
    parser.add_argument("--install-deps", action="store_true", help="Instalar dependencias antes de ejecutar")
    parser.add_argument("--no-coverage", action="store_true", help="Deshabilitar análisis de cobertura")
    parser.add_argument("--parallel", action="store_true", help="Ejecución paralela de tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Output verboso")
    
    args = parser.parse_args()
    
    print("🧪 Microsoft 365 Integration - Suite de Tests")
    print("=" * 50)
    
    # Configurar entorno
    setup_test_environment()
    
    # Instalar dependencias si se solicita
    if args.install_deps:
        if not install_test_dependencies():
            print("❌ Error instalando dependencias")
            sys.exit(1)
    
    # Configurar argumentos adicionales
    extra_args = []
    if args.verbose:
        extra_args.append("-s")  # Mostrar print statements
    if args.parallel:
        extra_args.append("-n auto")  # Ejecución paralela
    
    success = True
    
    try:
        if args.category == "all":
            success = run_all_tests()
        elif args.category == "unit":
            success = run_unit_tests()
        elif args.category == "integration":
            success = run_integration_tests()
        elif args.category == "e2e":
            success = run_e2e_tests()
        elif args.category == "performance":
            success = run_performance_tests()
        elif args.category == "lint":
            success = lint_code()
        else:
            success = run_specific_test_category(args.category)
        
        # Generar reporte de cobertura si no se deshabilitó
        if not args.no_coverage and success:
            generate_coverage_report()
        
        if success:
            print("\n✅ TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
            print("\n📁 Reportes generados:")
            print("   - test-reports/: Reportes XML y HTML")
            print("   - htmlcov/: Reporte de cobertura HTML")
            if args.category in ["all", "unit", "integration"]:
                print("   - coverage.xml: Reporte de cobertura XML")
        else:
            print("\n❌ ALGUNOS TESTS FALLARON")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrumpidos por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error ejecutando tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()