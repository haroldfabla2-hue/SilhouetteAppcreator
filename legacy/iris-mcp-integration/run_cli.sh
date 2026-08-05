#!/bin/bash
# Script para ejecutar la CLI de IRIS MCP

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔮 IRIS MCP CLI${NC}"
echo "=================="

# Verificar entorno virtual
if [ ! -d "iris-mcp-env" ]; then
    echo -e "${RED}Error: Entorno virtual no encontrado. Ejecuta setup.sh primero${NC}"
    exit 1
fi

# Activar entorno virtual
source iris-mcp-env/bin/activate

# Instalar dependencias si no están instaladas
if ! python -c "import click, requests" 2>/dev/null; then
    echo -e "${YELLOW}Instalando dependencias...${NC}"
    pip install -r requirements.txt
fi

# Mostrar ayuda si no se proporcionan argumentos
if [ $# -eq 0 ]; then
    echo -e "${GREEN}Uso:${NC} $0 [comando] [opciones]"
    echo ""
    echo -e "${YELLOW}Comandos disponibles:${NC}"
    echo "  status agents    - Ver estado de agentes"
    echo "  status system    - Ver métricas del sistema"
    echo "  deploy agent     - Desplegar agente"
    echo "  deploy all       - Desplegar todos los agentes"
    echo "  metrics show     - Ver métricas"
    echo "  metrics monitor  - Monitoreo continuo"
    echo "  template list    - Listar templates"
    echo "  template create  - Crear template"
    echo "  template generate - Generar configuración"
    echo "  notify config    - Configurar notificaciones"
    echo "  log show         - Ver logs"
    echo "  health           - Verificar salud del sistema"
    echo "  version          - Mostrar versión"
    echo ""
    echo -e "${YELLOW}Ejemplos:${NC}"
    echo "  $0 status agents"
    echo "  $0 deploy sales_agent"
    echo "  $0 template list"
    echo "  $0 metrics show"
    echo ""
    echo -e "${GREEN}Ayuda completa: $0 --help${NC}"
    exit 0
fi

# Añadir directorio actual al PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Ejecutar CLI con argumentos
cd cli
python iris_cli.py "$@"