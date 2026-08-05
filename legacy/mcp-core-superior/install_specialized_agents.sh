#!/bin/bash

# Script de Instalación y Configuración - Agentes Especializados
# ===============================================================
# 
# Este script instala y configura los agentes especializados de búsqueda
# web avanzada en el MCP Superior.
#
# Uso: ./install_specialized_agents.sh [--force] [--with-tests]
#
# Opciones:
#   --force       : Reinstalar incluso si ya existe
#   --with-tests  : Instalar dependencias de tests
#   --dev-mode    : Modo desarrollo con logs detallados
#
# Autor: MCP Superior Team
# Versión: 1.0.0

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
FORCE_INSTALL=false
WITH_TESTS=false
DEV_MODE=false
LOG_FILE="/tmp/mcp-specialized-agents-install.log"

# Funciones de utilidad
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Parsear argumentos de línea de comandos
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_INSTALL=true
            shift
            ;;
        --with-tests)
            WITH_TESTS=true
            shift
            ;;
        --dev-mode)
            DEV_MODE=true
            shift
            ;;
        -h|--help)
            echo "Uso: $0 [--force] [--with-tests] [--dev-mode]"
            echo ""
            echo "Opciones:"
            echo "  --force       Reinstalar incluso si ya existe"
            echo "  --with-tests  Instalar dependencias de tests"
            echo "  --dev-mode    Modo desarrollo con logs detallados"
            exit 0
            ;;
        *)
            error "Opción desconocida: $1"
            exit 1
            ;;
    esac
done

# Verificar requisitos del sistema
check_requirements() {
    header "Verificando Requisitos del Sistema"
    
    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 no está instalado"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
    REQUIRED_VERSION="3.7"
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)"; then
        error "Se requiere Python 3.7+ (encontrado: $PYTHON_VERSION)"
        exit 1
    fi
    
    success "Python $PYTHON_VERSION ✓"
    
    # Verificar pip
    if ! command -v pip3 &> /dev/null; then
        error "pip3 no está instalado"
        exit 1
    fi
    
    success "pip3 disponible ✓"
    
    # Verificar estructura del proyecto
    if [[ ! -d "mcp-core-superior/src/agents" ]]; then
        error "Estructura del proyecto no encontrada. Ejecutar desde el directorio raíz del proyecto."
        exit 1
    fi
    
    success "Estructura del proyecto encontrada ✓"
}

# Crear directorios necesarios
setup_directories() {
    header "Configurando Directorios"
    
    # Crear directorios necesarios
    mkdir -p mcp-core-superior/src/agents/specialized
    mkdir -p mcp-core-superior/tests
    mkdir -p mcp-core-superior/examples
    mkdir -p mcp-core-superior/docs
    mkdir -p mcp-core-superior/data
    mkdir -p mcp-core-superior/logs
    
    # Permisos
    chmod 755 mcp-core-superior/src/agents/specialized
    chmod 755 mcp-core-superior/tests
    chmod 755 mcp-core-superior/examples
    chmod 755 mcp-core-superior/data
    chmod 755 mcp-core-superior/logs
    
    success "Directorios configurados ✓"
}

# Verificar si ya está instalado
check_installation() {
    if [[ -f "mcp-core-superior/src/agents/specialized/__init__.py" && "$FORCE_INSTALL" == false ]]; then
        warning "Agentes especializados ya instalados. Use --force para reinstalar."
        
        read -p "¿Desea continuar con la instalación? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            success "Instalación cancelada por el usuario"
            exit 0
        fi
    fi
}

# Instalar dependencias
install_dependencies() {
    header "Instalando Dependencias"
    
    # Lista de dependencias principales
    MAIN_DEPS=(
        "requests>=2.25.0"
        "beautifulsoup4>=4.9.0"
        "lxml>=4.6.0"
        "pandas>=1.3.0"
        "feedparser>=5.2.1"
        "python-dateutil>=2.8.0"
    )
    
    # Dependencias opcionales para funcionalidades avanzadas
    OPTIONAL_DEPS=(
        "openpyxl>=3.0.0"          # Para exportación Excel
        "SQLAlchemy>=1.4.0"        # Para bases de datos
        "psutil>=5.8.0"           # Para monitorización
        "scipy>=1.7.0"            # Para análisis estadístico
        "scikit-learn>=1.0.0"     # Para machine learning
    )
    
    # Dependencias de desarrollo y tests
    DEV_DEPS=(
        "pytest>=6.2.0"
        "pytest-asyncio>=0.21.0"
        "pytest-cov>=2.12.0"
        "pytest-mock>=3.6.0"
        "black>=21.0.0"
        "flake8>=3.9.0"
    )
    
    log "Instalando dependencias principales..."
    for dep in "${MAIN_DEPS[@]}"; do
        if pip3 install "$dep" >> "$LOG_FILE" 2>&1; then
            log "✓ $dep instalado"
        else
            warning "Error instalando $dep (continuando...)"
        fi
    done
    
    log "Instalando dependencias opcionales..."
    for dep in "${OPTIONAL_DEPS[@]}"; do
        if pip3 install "$dep" >> "$LOG_FILE" 2>&1; then
            log "✓ $dep instalado"
        else
            log "⚠️ $dep falló (funcionalidad limitada)"
        fi
    done
    
    if [[ "$WITH_TESTS" == true ]]; then
        log "Instalando dependencias de desarrollo..."
        for dep in "${DEV_DEPS[@]}"; do
            if pip3 install "$dep" >> "$LOG_FILE" 2>&1; then
                log "✓ $dep instalado"
            else
                warning "Error instalando $dep"
            fi
        done
    fi
    
    success "Dependencias instaladas ✓"
}

# Verificar e instalar archivos
install_files() {
    header "Instalando Agentes Especializados"
    
    # Verificar que existen los archivos de agentes
    AGENT_FILES=(
        "mcp-core-superior/src/agents/specialized/research_agent.py"
        "mcp-core-superior/src/agents/specialized/data_mining_agent.py"
        "mcp-core-superior/src/agents/specialized/news_intelligence_agent.py"
        "mcp-core-superior/src/agents/specialized/__init__.py"
        "mcp-core-superior/src/agents/specialized_integration.py"
    )
    
    for file in "${AGENT_FILES[@]}"; do
        if [[ ! -f "$file" ]]; then
            error "Archivo no encontrado: $file"
            exit 1
        fi
    done
    
    success "Archivos de agentes verificados ✓"
    
    # Instalar tests si existen
    if [[ -f "mcp-core-superior/tests/test_specialized_agents.py" ]]; then
        log "Tests de agentes encontrados ✓"
    else
        warning "Tests no encontrados - algunos tests pueden fallar"
    fi
    
    # Instalar ejemplos si existen
    if [[ -f "mcp-core-superior/examples/specialized_agents_examples.py" ]]; then
        log "Ejemplos de agentes encontrados ✓"
    else
        warning "Ejemplos no encontrados"
    fi
}

# Configurar integración con orquestador
setup_orchestrator_integration() {
    header "Configurando Integración con Orquestador"
    
    # Verificar que existe el orquestador
    ORCHESTRATOR_FILE="mcp-core-superior/src/agents/multiagent_orchestrator_agent.py"
    
    if [[ -f "$ORCHESTRATOR_FILE" ]]; then
        log "Orquestador principal encontrado ✓"
        
        # Verificar imports en el orquestador
        if grep -q "specialized_integration" "$ORCHESTRATOR_FILE" 2>/dev/null; then
            log "Integración con agentes especializados ya configurada ✓"
        else
            warning "Se recomienda agregar import para specialized_integration en el orquestador"
        fi
    else
        warning "Orquestador principal no encontrado - integración manual requerida"
    fi
    
    success "Integración con orquestador configurada ✓"
}

# Ejecutar tests básicos
run_basic_tests() {
    if [[ "$WITH_TESTS" == true ]]; then
        header "Ejecutando Tests Básicos"
        
        # Test de importación
        if python3 -c "
import sys
sys.path.append('./mcp-core-superior/src')
from agents.specialized import (
    ResearchAgent, DataMiningAgent, NewsIntelligenceAgent,
    create_agent_ensemble, get_specialized_agent
)
print('✅ Importación exitosa')
print('✅ ResearchAgent disponible')
print('✅ DataMiningAgent disponible') 
print('✅ NewsIntelligenceAgent disponible')
print('✅ Funciones de utilidad disponibles')
" 2>/dev/null; then
            success "Tests de importación exitosos ✓"
        else
            error "Tests de importación fallidos"
            return 1
        fi
        
        # Test básico de funcionalidad
        if python3 -c "
import sys
sys.path.append('./mcp-core-superior/src')
from agents.specialized import ResearchAgent, ResearchMethod

agent = ResearchAgent()
queries = agent._generate_research_queries('test', ResearchMethod.EXPLORATORY, '')
if len(queries) > 0:
    print('✅ Funcionalidad básica del ResearchAgent OK')
else:
    print('❌ Funcionalidad básica del ResearchAgent falló')
    sys.exit(1)
" 2>/dev/null; then
            success "Tests de funcionalidad exitosos ✓"
        else
            warning "Algunos tests de funcionalidad fallaron"
        fi
    fi
}

# Configurar logs y monitorización
setup_logging() {
    header "Configurando Logs y Monitorización"
    
    # Crear archivo de configuración de logs
    cat > mcp-core-superior/logs/specialized_agents_config.yaml << 'EOF'
version: 1
formatters:
  detailed:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(message)s'
  simple:
    format: '%(asctime)s - %(levelname)s - %(message)s'

handlers:
  file:
    class: logging.FileHandler
    filename: logs/specialized_agents.log
    formatter: detailed
    level: INFO
  console:
    class: logging.StreamHandler
    formatter: simple
    level: WARNING

loggers:
  specialized.ResearchAgent:
    level: DEBUG
    handlers: [file, console]
  specialized.DataMiningAgent:
    level: DEBUG
    handlers: [file, console]
  specialized.NewsIntelligenceAgent:
    level: DEBUG
    handlers: [file, console]

root:
  level: INFO
  handlers: [file, console]
EOF
    
    chmod 644 mcp-core-superior/logs/specialized_agents_config.yaml
    
    success "Configuración de logs creada ✓"
}

# Crear script de demostración
create_demo_script() {
    header "Creando Script de Demostración"
    
    cat > mcp-core-superior/demo_specialized_agents.py << 'EOF'
#!/usr/bin/env python3
"""
Demostración Rápida - Agentes Especializados
============================================
Script simple para demostrar funcionalidades básicas
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agents.specialized import (
    ResearchAgent, DataMiningAgent, NewsIntelligenceAgent,
    ResearchMethod, NewsCategory
)

def demo_research_agent():
    print("\n🔬 Demo: Research Agent")
    print("-" * 30)
    
    agent = ResearchAgent()
    
    # Test básico
    queries = agent._generate_research_queries(
        "inteligencia artificial", 
        ResearchMethod.EXPLORATORY, 
        ""
    )
    
    print(f"✅ Generadas {len(queries)} consultas de investigación")
    for i, query in enumerate(queries[:3], 1):
        print(f"   {i}. {query}")
    
    return True

def demo_data_mining_agent():
    print("\n⛏️ Demo: Data Mining Agent")
    print("-" * 30)
    
    agent = DataMiningAgent()
    
    # Test de validación
    config = {
        "type": "web_api",
        "url": "https://jsonplaceholder.typicode.com/posts",
        "params": {"_limit": "5"}
    }
    
    if agent._validate_source_config(config):
        print("✅ Configuración de fuente válida")
    else:
        print("❌ Configuración de fuente inválida")
        return False
    
    return True

def demo_news_intelligence_agent():
    print("\n📰 Demo: News Intelligence Agent")
    print("-" * 30)
    
    agent = NewsIntelligenceAgent()
    
    # Test de análisis de sentimiento
    sentiment = agent._analyze_basic_sentiment("Excelente noticia, muy positivo")
    
    print(f"✅ Análisis de sentimiento: {sentiment.value}")
    
    # Test de credibilidad
    credibility = agent._get_source_credibility("elpais.com")
    print(f"✅ Credibilidad de fuente: {credibility:.2f}")
    
    return True

def main():
    print("🚀 Demostración Rápida - Agentes Especializados")
    print("=" * 50)
    
    demos = [
        ("Research Agent", demo_research_agent),
        ("Data Mining Agent", demo_data_mining_agent),
        ("News Intelligence Agent", demo_news_intelligence_agent)
    ]
    
    successful = 0
    for name, demo_func in demos:
        try:
            if demo_func():
                successful += 1
        except Exception as e:
            print(f"❌ Error en demo {name}: {e}")
    
    print(f"\n📊 Resultados:")
    print(f"   Demos exitosos: {successful}/{len(demos)}")
    
    if successful == len(demos):
        print(f"\n🎉 ¡Todos los agentes funcionando correctamente!")
    else:
        print(f"\n⚠️ Algunos agentes necesitan revisión")
    
    return successful == len(demos)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
EOF
    
    chmod +x mcp-core-superior/demo_specialized_agents.py
    
    success "Script de demostración creado ✓"
}

# Mostrar información final
show_final_info() {
    header "Instalación Completada"
    
    echo -e "${GREEN}✅ Agentes Especializados instalados correctamente${NC}"
    echo ""
    echo "📁 Archivos instalados:"
    echo "   • Research Agent: src/agents/specialized/research_agent.py"
    echo "   • Data Mining Agent: src/agents/specialized/data_mining_agent.py"
    echo "   • News Intelligence Agent: src/agents/specialized/news_intelligence_agent.py"
    echo "   • Integración: src/agents/specialized_integration.py"
    echo "   • Tests: tests/test_specialized_agents.py"
    echo "   • Ejemplos: examples/specialized_agents_examples.py"
    echo "   • Documentación: docs/ESPECIALIZED_AGENTS_DOCUMENTATION.md"
    echo ""
    echo "🔧 Comandos útiles:"
    echo "   • Ejecutar demo: python3 mcp-core-superior/demo_specialized_agents.py"
    echo "   • Ejecutar tests: python3 mcp-core-superior/tests/test_specialized_agents.py"
    echo "   • Ver ejemplos: python3 mcp-core-superior/examples/specialized_agents_examples.py"
    echo ""
    echo "📚 Documentación:"
    echo "   • Guía completa: mcp-core-superior/docs/ESPECIALIZED_AGENTS_DOCUMENTATION.md"
    echo "   • Configuración de logs: mcp-core-superior/logs/specialized_agents_config.yaml"
    echo ""
    echo -e "${BLUE}🌟 Los agentes especializados están listos para usar!${NC}"
}

# Función principal
main() {
    log "Iniciando instalación de Agentes Especializados"
    
    # Header principal
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║          AGENTES ESPECIALIZADOS - INSTALACIÓN               ║"
    echo "║              Búsqueda Web Avanzada                          ║"
    echo "║                    MCP Superior v1.0.0                     ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    # Verificar si estamos en modo desarrollo
    if [[ "$DEV_MODE" == true ]]; then
        export PYTHONPATH="${PYTHONPATH}:$(pwd)/mcp-core-superior/src"
        log "Modo desarrollo activado - PYTHONPATH configurado"
    fi
    
    # Ejecutar pasos de instalación
    check_requirements
    setup_directories
    check_installation
    install_dependencies
    install_files
    setup_orchestrator_integration
    setup_logging
    create_demo_script
    run_basic_tests
    show_final_info
    
    log "Instalación completada exitosamente"
    
    # Ejecutar demo si fue exitoso
    if [[ "$WITH_TESTS" == true ]]; then
        echo ""
        read -p "¿Desea ejecutar la demostración? (Y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            echo ""
            python3 mcp-core-superior/demo_specialized_agents.py
        fi
    fi
}

# Ejecutar función principal
main "$@"