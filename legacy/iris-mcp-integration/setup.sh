#!/bin/bash
# Script de instalación y configuración inicial de IRIS MCP Integration

set -e

echo "🚀 IRIS MCP Integration - Setup Wizard"
echo "======================================"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para print coloreado
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Verificar Python
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_status "Python encontrado: $PYTHON_VERSION"
    else
        print_error "Python 3 no encontrado. Por favor instala Python 3.8+"
        exit 1
    fi
}

# Verificar pip
check_pip() {
    if command -v pip3 &> /dev/null; then
        print_status "pip3 encontrado"
    else
        print_error "pip3 no encontrado. Instala pip primero"
        exit 1
    fi
}

# Crear entorno virtual
create_venv() {
    if [ ! -d "iris-mcp-env" ]; then
        echo "📦 Creando entorno virtual..."
        python3 -m venv iris-mcp-env
        print_status "Entorno virtual creado"
    else
        print_status "Entorno virtual ya existe"
    fi
    
    source iris-mcp-env/bin/activate
    print_status "Entorno virtual activado"
}

# Instalar dependencias Python
install_python_deps() {
    echo "📦 Instalando dependencias Python..."
    pip install -r requirements.txt
    print_status "Dependencias Python instaladas"
}

# Verificar Node.js y npm (opcional)
check_nodejs() {
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        NPM_VERSION=$(npm --version)
        print_status "Node.js encontrado: $NODE_VERSION"
        print_status "npm encontrado: $NPM_VERSION"
        return 0
    else
        print_warning "Node.js no encontrado. Dashboard no estará disponible."
        return 1
    fi
}

# Instalar dependencias del dashboard
install_dashboard_deps() {
    if check_nodejs; then
        echo "📦 Instalando dependencias del dashboard..."
        cd dashboard
        npm install
        cd ..
        print_status "Dependencias del dashboard instaladas"
    else
        print_warning "Dashboard no configurado (Node.js requerido)"
    fi
}

# Configurar archivos de entorno
setup_environment() {
    echo "🔧 Configurando variables de entorno..."
    
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# IRIS MCP Integration Configuration
IRIS_API_BASE=http://localhost:8000
IRIS_DASHBOARD_PORT=3000
IRIS_METRICS_PORT=8000

# Email Configuration (optional)
IRIS_SMTP_SERVER=smtp.gmail.com
IRIS_SMTP_PORT=587
IRIS_EMAIL_USER=your_email@gmail.com
IRIS_EMAIL_PASSWORD=your_app_password

# Webhook Configuration (optional)
IRIS_WEBHOOK_URL=https://your-webhook.com/notifications

# Logging
IRIS_LOG_LEVEL=INFO
IRIS_LOG_FILE=logs/iris_mcp.log
EOF
        print_status "Archivo .env creado"
    else
        print_status "Archivo .env ya existe"
    fi
}

# Crear directorios necesarios
setup_directories() {
    echo "📁 Creando directorios..."
    
    mkdir -p logs
    mkdir -p iris_templates
    mkdir -p configs
    
    print_status "Directorios creados"
}

# Crear templates básicos
create_basic_templates() {
    echo "📋 Creando templates básicos..."
    
    # Activar entorno virtual
    source iris-mcp-env/bin/activate
    
    # Crear templates usando el template manager
    python3 -c "
import sys
sys.path.append('.')
from templates.iris_templates import IRISTemplateManager

manager = IRISTemplateManager()

# Crear templates básicos
templates = ['sales', 'support', 'consulting', 'multiagent', 'optimization']

for template_type in templates:
    try:
        if template_type == 'sales':
            template = manager.create_sales_automation_template()
        elif template_type == 'support':
            template = manager.create_support_template()
        elif template_type == 'consulting':
            template = manager.create_consulting_template()
        elif template_type == 'multiagent':
            template = manager.create_multiagent_template()
        elif template_type == 'optimization':
            template = manager.create_optimization_template()
        
        file_path = manager.save_template(template)
        print(f'Template {template_type} creado: {file_path}')
    except Exception as e:
        print(f'Error creando template {template_type}: {e}')
"
    
    print_status "Templates básicos creados"
}

# Hacer scripts ejecutables
make_executable() {
    chmod +x *.sh
    print_status "Scripts configurados como ejecutables"
}

# Mostrar configuración final
show_final_config() {
    echo ""
    echo "🎉 ¡Setup completado exitosamente!"
    echo "================================"
    echo ""
    echo "📊 Componentes configurados:"
    echo "  ✅ Servidor de métricas (FastAPI)"
    echo "  ✅ Dashboard React (si Node.js está disponible)"
    echo "  ✅ CLI avanzada (Click)"
    echo "  ✅ Sistema de notificaciones"
    echo "  ✅ Templates de agentes IRIS"
    echo ""
    echo "🚀 Para usar el sistema:"
    echo ""
    echo "1. Iniciar servidor de métricas:"
    echo "   ./start_metrics_server.sh"
    echo ""
    echo "2. Iniciar dashboard (opcional):"
    echo "   ./start_dashboard.sh"
    echo ""
    echo "3. Usar CLI:"
    echo "   source iris-mcp-env/bin/activate"
    echo "   python cli/iris_cli.py status"
    echo ""
    echo "4. Configurar notificaciones:"
    echo "   python notifications/iris_notifications.py"
    echo ""
    echo "📖 Ver README.md para documentación completa"
    echo ""
    echo "🔧 Para personalizar la configuración:"
    echo "   - Editar archivo .env"
    echo "   - Modificar templates en iris_templates/"
    echo "   - Configurar notificaciones"
}

# Ejecutar setup completo
main() {
    echo "Iniciando setup de IRIS MCP Integration..."
    echo ""
    
    check_python
    check_pip
    create_venv
    install_python_deps
    install_dashboard_deps
    setup_environment
    setup_directories
    create_basic_templates
    make_executable
    
    show_final_config
}

# Ejecutar solo si no se está importando
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi