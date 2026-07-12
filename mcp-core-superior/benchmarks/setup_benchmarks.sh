#!/bin/bash

# Performance Benchmarking Suite - Script de Instalación y Configuración
# Configura automáticamente el entorno para ejecutar benchmarks MCP-Core-Superior vs MiniMax Agent

set -e  # Salir en caso de error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCHMARKS_DIR="$PROJECT_ROOT/benchmarks"
MIN_PYTHON_VERSION="3.8"

# Funciones de utilidad
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

check_python_version() {
    log_info "Verificando versión de Python..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 no está instalado"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (${MIN_PYTHON_VERSION%.*}, ${MIN_PYTHON_VERSION#*.}) else 1)"; then
        log_error "Python $MIN_PYTHON_VERSION o superior es requerido. Versión actual: $PYTHON_VERSION"
        exit 1
    fi
    
    log_success "Python $PYTHON_VERSION detectado"
}

install_dependencies() {
    log_info "Instalando dependencias de Python..."
    
    # Lista de dependencias principales
    local dependencies=(
        "asyncio"
        "aiohttp"
        "psutil"
        "numpy"
        "pandas"
        "matplotlib"
        "seaborn"
        "pyyaml"
        "requests"
        "jinja2"
        "plotly"
        "dash"
        "scipy"
        "scikit-learn"
    )
    
    # Dependencias de load testing
    local load_test_deps=(
        "locust"
        "artillery"
    )
    
    # Instalar dependencias principales
    for dep in "${dependencies[@]}"; do
        if ! python3 -c "import ${dep//-/_}" 2>/dev/null; then
            log_info "Instalando $dep..."
            pip3 install --user "$dep" || {
                log_error "Error instalando $dep"
                exit 1
            }
        else
            log_info "$dep ya está instalado"
        fi
    done
    
    # Instalar dependencias de load testing
    for dep in "${load_test_deps[@]}"; do
        if ! command -v "$dep" &> /dev/null && ! python3 -c "import ${dep//-/_}" 2>/dev/null; then
            log_info "Instalando $dep..."
            pip3 install --user "$dep" || {
                log_warning "Error instalando $dep, continuando..."
            }
        else
            log_info "$dep ya está disponible"
        fi
    done
    
    log_success "Dependencias instaladas correctamente"
}

setup_directories() {
    log_info "Creando estructura de directorios..."
    
    local directories=(
        "$BENCHMARKS_DIR/reports"
        "$BENCHMARKS_DIR/analysis"
        "$BENCHMARKS_DIR/dashboards"
        "$BENCHMARKS_DIR/logs"
        "$BENCHMARKS_DIR/configs/artillery"
        "$BENCHMARKS_DIR/configs/locust"
        "$BENCHMARKS_DIR/data"
        "$BENCHMARKS_DIR/results"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_info "Creado directorio: $dir"
        fi
    done
    
    log_success "Estructura de directorios creada"
}

create_sample_configs() {
    log_info "Creando configuraciones de ejemplo..."
    
    # Configuración de datos de prueba
    cat > "$BENCHMARKS_DIR/data/test_data.csv" << 'EOF'
username,email,priority
user1,user1@example.com,high
user2,user2@example.com,medium
user3,user3@example.com,low
user4,user4@example.com,high
user5,user5@example.com,medium
EOF
    
    # Configuración de logging
    cat > "$BENCHMARKS_DIR/logs/logging_config.conf" << 'EOF'
[loggers]
keys=root,benchmark

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter

[logger_root]
level=INFO
handlers=consoleHandler,fileHandler

[logger_benchmark]
level=DEBUG
handlers=fileHandler
qualname=benchmark
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=DEBUG
formatter=simpleFormatter
args=('benchmark.log',)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
EOF
    
    log_success "Configuraciones de ejemplo creadas"
}

setup_permissions() {
    log_info "Configurando permisos..."
    
    # Hacer ejecutables los scripts de Python
    find "$BENCHMARKS_DIR" -name "*.py" -exec chmod +x {} \;
    
    # Crear archivo .gitignore si no existe
    if [ ! -f "$PROJECT_ROOT/.gitignore" ]; then
        cat > "$PROJECT_ROOT/.gitignore" << 'EOF'
# Benchmarking outputs
benchmarks/reports/
benchmarks/analysis/
benchmarks/logs/
benchmarks/results/
benchmarks/data/*.csv

# Python cache
__pycache__/
*.py[cod]
*$py.class

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
EOF
    fi
    
    log_success "Permisos configurados"
}

validate_installation() {
    log_info "Validando instalación..."
    
    # Verificar que los scripts principales existen
    local scripts=(
        "$BENCHMARKS_DIR/scripts/benchmark_orchestrator.py"
        "$BENCHMARKS_DIR/scripts/performance_benchmarker.py"
        "$BENCHMARKS_DIR/load_tests/locust_load_test.py"
        "$BENCHMARKS_DIR/load_tests/artillery_load_test.py"
        "$BENCHMARKS_DIR/tools/comparative_analysis.py"
    )
    
    for script in "${scripts[@]}"; do
        if [ ! -f "$script" ]; then
            log_error "Script faltante: $script"
            exit 1
        fi
    done
    
    # Verificar que el archivo de configuración existe
    if [ ! -f "$BENCHMARKS_DIR/configs/benchmark_config.yaml" ]; then
        log_error "Archivo de configuración faltante: benchmark_config.yaml"
        exit 1
    fi
    
    # Verificar dependencias críticas
    local critical_deps=("numpy" "pandas" "asyncio")
    for dep in "${critical_deps[@]}"; do
        if ! python3 -c "import ${dep}" 2>/dev/null; then
            log_error "Dependencia crítica faltante: $dep"
            exit 1
        fi
    done
    
    log_success "Instalación validada correctamente"
}

create_startup_scripts() {
    log_info "Creando scripts de inicio rápido..."
    
    # Script de inicio rápido
    cat > "$BENCHMARKS_DIR/run_benchmarks.sh" << 'EOF'
#!/bin/bash
# Script de inicio rápido para benchmarks

cd "$(dirname "$0")"

echo "🚀 Iniciando Performance Benchmarking Suite..."
echo "============================================="

# Verificar que los agentes estén ejecutándose
echo "Verificando estado de agentes..."

if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ MCP-Core-Superior: Activo"
else
    echo "❌ MCP-Core-Superior: No disponible"
    echo "   Inicia el agente con: python src/core/fastmcp_server.py"
fi

if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ MiniMax Agent: Activo"
else
    echo "❌ MiniMax Agent: No disponible"
    echo "   Asegúrate de que el puerto 8001 esté disponible"
fi

echo ""
echo "Ejecutando benchmarks..."

# Ejecutar suite completa
python3 scripts/benchmark_orchestrator.py "$@"
EOF
    
    chmod +x "$BENCHMARKS_DIR/run_benchmarks.sh"
    
    # Script de limpieza
    cat > "$BENCHMARKS_DIR/clean_results.sh" << 'EOF'
#!/bin/bash
# Script para limpiar resultados anteriores

echo "🧹 Limpiando resultados anteriores..."

rm -rf reports/* analysis/* logs/* results/*

echo "✅ Limpieza completada"
EOF
    
    chmod +x "$BENCHMARKS_DIR/clean_results.sh"
    
    log_success "Scripts de inicio creados"
}

create_monitoring_setup() {
    log_info "Configurando monitoring del sistema..."
    
    # Script de monitoreo de recursos
    cat > "$BENCHMARKS_DIR/tools/system_monitor.py" << 'EOF'
#!/usr/bin/env python3
"""
Monitor del sistema durante benchmarks
Mide CPU, memoria, red y disco
"""

import psutil
import time
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def monitor_system(duration=300, interval=5):
    """Monitorear sistema durante duración específica"""
    start_time = time.time()
    end_time = start_time + duration
    
    monitoring_data = []
    
    logger.info(f"Iniciando monitoreo por {duration} segundos...")
    
    while time.time() < end_time:
        data = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_used_gb': psutil.virtual_memory().used / (1024**3),
            'disk_usage': psutil.disk_usage('/').percent,
            'network_io': psutil.net_io_counters()._asdict(),
            'process_count': len(psutil.pids())
        }
        
        monitoring_data.append(data)
        logger.info(f"CPU: {data['cpu_percent']:.1f}%, Memory: {data['memory_percent']:.1f}%")
        
        time.sleep(interval)
    
    # Guardar datos
    with open('system_monitoring.json', 'w') as f:
        json.dump(monitoring_data, f, indent=2)
    
    logger.info("Monitoreo completado. Datos guardados en system_monitoring.json")

if __name__ == "__main__":
    monitor_system()
EOF
    
    chmod +x "$BENCHMARKS_DIR/tools/system_monitor.py"
    
    log_success "Sistema de monitoreo configurado"
}

print_banner() {
    cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🚀 Performance Benchmarking Suite                         ║
║   MCP-Core-Superior vs MiniMax Agent                        ║
║                                                               ║
║   Configuración automática del entorno de benchmarking     ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
}

print_summary() {
    echo ""
    log_success "🎯 INSTALACIÓN COMPLETADA"
    echo "============================================="
    echo ""
    echo "📁 Estructura creada:"
    echo "  ├── benchmarks/reports/     # Reportes de resultados"
    echo "  ├── benchmarks/analysis/    # Análisis detallados"
    echo "  ├── benchmarks/logs/        # Logs de ejecución"
    echo "  └── benchmarks/configs/     # Configuraciones"
    echo ""
    echo "🚀 Inicio rápido:"
    echo "  ./run_benchmarks.sh                    # Ejecutar todos los tests"
    echo "  ./run_benchmarks.sh --skip-load-tests  # Solo performance tests"
    echo "  ./clean_results.sh                     # Limpiar resultados"
    echo ""
    echo "🔧 Comandos individuales:"
    echo "  python3 scripts/benchmark_orchestrator.py"
    echo "  python3 scripts/performance_benchmarker.py"
    echo "  python3 tools/comparative_analysis.py"
    echo ""
    echo "📖 Documentación completa:"
    echo "  cat benchmarks/README.md"
    echo ""
    echo "⚠️  Antes de ejecutar benchmarks:"
    echo "  1. Asegúrate de que los agentes estén ejecutándose"
    echo "  2. Verifica URLs en configs/benchmark_config.yaml"
    echo "  3. Revisa que tengas permisos suficientes"
    echo ""
}

main() {
    print_banner
    
    log_info "Iniciando instalación de Performance Benchmarking Suite..."
    echo ""
    
    check_python_version
    install_dependencies
    setup_directories
    create_sample_configs
    setup_permissions
    validate_installation
    create_startup_scripts
    create_monitoring_setup
    
    print_summary
}

# Verificar si se ejecuta como script principal
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi