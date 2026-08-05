#!/bin/bash
# Script principal para ejecutar la suite completa de tests del MCP Core Superior
# Target: 90%+ code coverage

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
PYTEST_CMD="python -m pytest"
COVERAGE_MIN=90
TEST_DIR="tests"
REPORTS_DIR="test-reports"

# Función para logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para mostrar ayuda
show_help() {
    echo "MCP Core Superior - Test Suite Runner"
    echo ""
    echo "Uso: $0 [OPCIONES]"
    echo ""
    echo "OPCIONES:"
    echo "  -h, --help           Mostrar esta ayuda"
    echo "  -a, --all           Ejecutar todos los tests (por defecto)"
    echo "  -u, --unit          Ejecutar solo tests unitarios"
    echo "  -i, --integration   Ejecutar solo tests de integración"
    echo "  -c, --coverage      Ejecutar tests con cobertura"
    echo "  -s, --slow          Incluir tests lentos"
    echo "  -k, --keyword       Ejecutar tests que contengan keyword"
    echo "  -m, --marker        Ejecutar tests con marcador específico"
    echo "  -v, --verbose       Output verbose"
    echo "  -x, --failfast      Parar en el primer fallo"
    echo "  --parallel          Ejecutar tests en paralelo"
    echo "  --benchmark         Ejecutar tests de performance"
    echo "  --security          Ejecutar solo tests de seguridad"
    echo "  --observability     Ejecutar solo tests de observabilidad"
    echo "  --agents            Ejecutar solo tests de agentes"
    echo "  --core              Ejecutar solo tests del core"
    echo "  --integration-points EjECUTAR solo tests de integration points"
    echo "  --report            Generar reporte HTML"
    echo "  --clean             Limpiar archivos de test anteriores"
    echo "  --install-deps      Instalar dependencias de test"
    echo ""
    echo "EJEMPLOS:"
    echo "  $0 --all --coverage"
    echo "  $0 --unit --verbose"
    echo "  $0 --agents --parallel"
    echo "  $0 --security --failfast"
    echo "  $0 --keyword 'test_auth'"
    echo "  $0 --marker 'agent and unit'"
}

# Función para limpiar archivos anteriores
clean_tests() {
    log_info "Limpiando archivos de test anteriores..."
    
    # Limpiar reportes anteriores
    rm -rf htmlcov/ test-results.xml coverage.xml
    
    # Limpiar archivos __pycache__
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    # Limpiar archivos .pytest_cache
    rm -rf .pytest_cache/ 2>/dev/null || true
    
    log_success "Limpieza completada"
}

# Función para instalar dependencias
install_deps() {
    log_info "Instalando dependencias de test..."
    
    if [ -f "test-requirements.txt" ]; then
        pip install -r test-requirements.txt
        log_success "Dependencias instaladas"
    else
        log_warning "test-requirements.txt no encontrado, instalando dependencias básicas..."
        pip install pytest pytest-asyncio pytest-cov pytest-html
    fi
}

# Función para verificar cobertura mínima
check_coverage() {
    local coverage_file="coverage.xml"
    if [ -f "$coverage_file" ]; then
        local actual_coverage=$(grep -oP 'line-rate="\K[0-9.]+' "$coverage_file" | head -1)
        actual_coverage=$(echo "$actual_coverage * 100" | bc | cut -d. -f1)
        
        log_info "Cobertura actual: ${actual_coverage}%"
        
        if [ "$actual_coverage" -ge "$COVERAGE_MIN" ]; then
            log_success "✅ Cobertura cumple el objetivo de ${COVERAGE_MIN}%"
            return 0
        else
            log_error "❌ Cobertura $actual_coverage% < ${COVERAGE_MIN}% requerida"
            return 1
        fi
    else
        log_warning "Archivo de cobertura no encontrado"
        return 1
    fi
}

# Función para generar reporte HTML
generate_report() {
    log_info "Generando reporte HTML..."
    
    if [ -f "htmlcov/index.html" ]; then
        log_success "✅ Reporte generado en htmlcov/index.html"
        log_info "Abriendo reporte en navegador..."
        if command -v xdg-open > /dev/null; then
            xdg-open htmlcov/index.html
        elif command -v open > /dev/null; then
            open htmlcov/index.html
        else
            log_info "Por favor, abre manualmente: htmlcov/index.html"
        fi
    else
        log_warning "Reporte HTML no encontrado"
    fi
}

# Función para ejecutar tests
run_tests() {
    local test_command=""
    local args=()
    
    # Agregar opciones de pytest
    args+=("--tb=short" "--maxfail=10")
    
    # Agregar verbosidad si se solicita
    if [ "$VERBOSE" = "true" ]; then
        args+=("-v")
    fi
    
    # Agregar failfast si se solicita
    if [ "$FAILFAST" = "true" ]; then
        args+=("-x")
    fi
    
    # Agregar parallel si se solicita
    if [ "$PARALLEL" = "true" ]; then
        args+=("-n" "auto")
    fi
    
    # Agregar markers
    if [ -n "$MARKER" ]; then
        args+=("-m" "$MARKER")
    fi
    
    # Agregar keyword
    if [ -n "$KEYWORD" ]; then
        args+=("-k" "$KEYWORD")
    fi
    
    # Configurar directorio de tests
    args+=("$TEST_DIR")
    
    # Construir comando
    test_command="$PYTEST_CMD ${args[*]}"
    
    log_info "Ejecutando: $test_command"
    
    # Ejecutar tests
    eval "$test_command"
}

# Función principal para cada tipo de test
run_unit_tests() {
    log_info "Ejecutando tests unitarios..."
    MARKER="unit" run_tests
}

run_integration_tests() {
    log_info "Ejecutando tests de integración..."
    MARKER="integration" run_tests
}

run_agent_tests() {
    log_info "Ejecutando tests de agentes..."
    MARKER="agent" run_tests
}

run_security_tests() {
    log_info "Ejecutando tests de seguridad..."
    MARKER="security" run_tests
}

run_observability_tests() {
    log_info "Ejecutando tests de observabilidad..."
    MARKER="observability" run_tests
}

run_core_tests() {
    log_info "Ejecutando tests del core..."
    MARKER="core" run_tests
}

run_technical_tests() {
    log_info "Ejecutando tests de diferenciadores técnicos..."
    MARKER="technical" run_tests
}

run_integration_points_tests() {
    log_info "Ejecutando tests de integration points..."
    MARKER="integration" run_tests
}

run_benchmark_tests() {
    log_info "Ejecutando tests de performance..."
    MARKER="benchmark" run_tests
}

# Función para ejecutar todos los tests con cobertura
run_all_tests_with_coverage() {
    log_info "Ejecutando todos los tests con cobertura..."
    
    # Configurar comandos con cobertura
    local args=()
    args+=("--cov=src")
    args+=("--cov-report=term-missing")
    args+=("--cov-report=html")
    args+=("--cov-report=xml")
    args+=("--cov-fail-under=$COVERAGE_MIN")
    args+=("--junitxml=test-results.xml")
    
    # Agregar marcadores según qué tests incluir
    if [ "$INCLUDE_SLOW" = "true" ]; then
        args+=("--cov-append")
    else
        args+=("-m" "not slow")
    fi
    
    # Ejecutar tests
    log_info "Ejecutando: $PYTEST_CMD ${args[*]} $TEST_DIR"
    $PYTEST_CMD "${args[@]}" "$TEST_DIR"
    
    # Verificar cobertura
    check_coverage
}

# Función principal
main() {
    log_info "🚀 Iniciando suite de tests del MCP Core Superior"
    
    # Crear directorio de reportes
    mkdir -p "$REPORTS_DIR"
    
    case "${TEST_TYPE:-all}" in
        "unit")
            run_unit_tests
            ;;
        "integration")
            run_integration_tests
            ;;
        "agents")
            run_agent_tests
            ;;
        "security")
            run_security_tests
            ;;
        "observability")
            run_observability_tests
            ;;
        "core")
            run_core_tests
            ;;
        "technical")
            run_technical_tests
            ;;
        "integration-points")
            run_integration_points_tests
            ;;
        "benchmark")
            run_benchmark_tests
            ;;
        "all")
            if [ "$COVERAGE" = "true" ]; then
                run_all_tests_with_coverage
            else
                run_tests
            fi
            ;;
        *)
            log_error "Tipo de test no reconocido: $TEST_TYPE"
            show_help
            exit 1
            ;;
    esac
    
    # Generar reporte si se solicita
    if [ "$GENERATE_REPORT" = "true" ]; then
        generate_report
    fi
    
    log_success "✅ Suite de tests completada"
}

# Procesar argumentos de línea de comandos
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -a|--all)
            TEST_TYPE="all"
            shift
            ;;
        -u|--unit)
            TEST_TYPE="unit"
            shift
            ;;
        -i|--integration)
            TEST_TYPE="integration"
            shift
            ;;
        -c|--coverage)
            COVERAGE="true"
            shift
            ;;
        -s|--slow)
            INCLUDE_SLOW="true"
            shift
            ;;
        -k|--keyword)
            KEYWORD="$2"
            shift 2
            ;;
        -m|--marker)
            MARKER="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE="true"
            shift
            ;;
        -x|--failfast)
            FAILFAST="true"
            shift
            ;;
        --parallel)
            PARALLEL="true"
            shift
            ;;
        --benchmark)
            TEST_TYPE="benchmark"
            shift
            ;;
        --security)
            TEST_TYPE="security"
            shift
            ;;
        --observability)
            TEST_TYPE="observability"
            shift
            ;;
        --agents)
            TEST_TYPE="agents"
            shift
            ;;
        --core)
            TEST_TYPE="core"
            shift
            ;;
        --integration-points)
            TEST_TYPE="integration-points"
            shift
            ;;
        --report)
            GENERATE_REPORT="true"
            shift
            ;;
        --clean)
            clean_tests
            exit 0
            ;;
        --install-deps)
            install_deps
            exit 0
            ;;
        *)
            log_error "Opción desconocida: $1"
            show_help
            exit 1
            ;;
    esac
done

# Verificar dependencias básicas
if ! command -v python > /dev/null; then
    log_error "Python no está instalado"
    exit 1
fi

if ! command -v pip > /dev/null; then
    log_error "pip no está instalado"
    exit 1
fi

# Ejecutar función principal
main