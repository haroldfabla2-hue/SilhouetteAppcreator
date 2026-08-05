#!/bin/bash

# Script para configurar y ejecutar la Suite de Testing Enterprise

set -e

echo "🚀 INICIANDO CONFIGURACIÓN DE SUITE DE TESTING ENTERPRISE"
echo "=========================================================="

# Crear directorios necesarios
echo "📁 Creando estructura de directorios..."
mkdir -p logs
mkdir -p reports/{coverage,performance,security,compliance}
mkdir -p tmp

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -q -r requirements.txt 2>/dev/null || echo "⚠️  Algunas dependencias pueden requerir instalación manual"

# Configurar base de datos de testing
echo "🗄️  Configurando base de datos de testing..."
python -c "from utils.test_database_setup import setup_test_environment; setup_test_environment()" 2>/dev/null || echo "⚠️  Base de datos no disponible, continuando..."

# Configurar pytest
echo "🧪 Configurando pytest..."
cp pytest.ini . 2>/dev/null || echo "⚠️  pytest.ini ya existe"

# Verificar archivos de testing
echo "🔍 Verificando archivos de testing..."
if [ -f "run_enterprise_tests.py" ]; then
    echo "   ✅ Executor principal encontrado"
else
    echo "   ❌ Executor principal no encontrado"
fi

if [ -f "demo_testing_suite.py" ]; then
    echo "   ✅ Demo encontrado"
else
    echo "   ❌ Demo no encontrado"
fi

# Listar archivos principales
echo "📋 Archivos de testing disponibles:"
for dir in unit_tests integration_tests performance_tests security_tests compliance_tests load_tests monitoring health_checks; do
    if [ -d "$dir" ]; then
        echo "   📂 $dir/"
        ls -1 "$dir"/*.py 2>/dev/null | head -5 | sed 's/^/      - /'
    fi
done

echo ""
echo "✅ CONFIGURACIÓN COMPLETADA"
echo ""
echo "🎯 COMANDOS PARA EJECUTAR:"
echo ""
echo "1. Ejecutar demo completo:"
echo "   python demo_testing_suite.py"
echo ""
echo "2. Ejecutar suite completa:"
echo "   python run_enterprise_tests.py"
echo ""
echo "3. Ejecutar solo tests específicos:"
echo "   pytest unit_tests/ -v"
echo "   pytest integration_tests/ -v"
echo "   pytest security_tests/ -v"
echo "   pytest performance_tests/ -v"
echo "   pytest compliance_tests/ -v"
echo ""
echo "4. Ejecutar load testing (requiere Locust):"
echo "   locust -f load_tests/load_tests.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 300s"
echo ""
echo "5. Health checks independientes:"
echo "   python health_checks/health_checker.py"
echo ""
echo "6. Monitoring independiente:"
echo "   python monitoring/system_monitor.py"
echo ""
echo "📊 REPORTES SE GUARDAN EN:"
echo "   - reports/ (reportes HTML/JSON)"
echo "   - logs/ (logs de ejecución)"
echo ""
echo "🔧 CONFIGURACIÓN PERSONALIZADA:"
echo "   Editar config/test_config.py para ajustar parámetros"
echo ""
echo "¡Listo para usar! 🎉"
