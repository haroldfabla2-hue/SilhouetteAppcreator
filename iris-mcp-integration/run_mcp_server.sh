#!/bin/bash
# Script de inicio para IRIS MCP Server

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Iniciando IRIS MCP Superior Server${NC}"
echo "========================================"

# Verificar que estamos en el directorio correcto
if [ ! -f "run_mcp_server.py" ] || [ ! -f "mcp-server.json" ]; then
    echo -e "${RED}Error: Ejecuta este script desde el directorio raíz de IRIS MCP Integration${NC}"
    exit 1
fi

# Crear entorno virtual si no existe
if [ ! -d "iris-mcp-env" ]; then
    echo -e "${YELLOW}Creando entorno virtual...${NC}"
    python3 -m venv iris-mcp-env
fi

# Activar entorno virtual
source iris-mcp-env/bin/activate

# Instalar FastMCP si no está instalado
if ! python -c "import fastmcp" 2>/dev/null; then
    echo -e "${YELLOW}Instalando FastMCP...${NC}"
    pip install fastmcp
fi

# Instalar dependencias básicas si no están instaladas
if ! python -c "import click, requests" 2>/dev/null; then
    echo -e "${YELLOW}Instalando dependencias básicas...${NC}"
    pip install click requests
fi

# Crear directorios necesarios
mkdir -p logs iris_templates configs

# Verificar variables de entorno
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo -e "${GREEN}📋 Servidor MCP IRIS iniciando...${NC}"
echo -e "${YELLOW}🔮 Herramientas disponibles:${NC}"
echo "  • get_iris_agents_status - Ver estado de agentes"
echo "  • get_agent_metrics - Métricas de agente específico"
echo "  • deploy_agent - Desplegar agente"
echo "  • create_template - Crear template de automatización"
echo "  • generate_workflow_config - Generar configuración"
echo "  • send_notification - Enviar notificación"
echo "  • get_system_health - Verificar salud del sistema"
echo "  • list_available_templates - Listar templates"
echo "  • get_notification_stats - Estadísticas de notificaciones"
echo ""
echo -e "${YELLOW}📖 Prompts disponibles:${NC}"
echo "  • iris_agent_management_guide - Guía de gestión"
echo "  • iris_troubleshooting_guide - Guía de problemas"
echo ""

# Ejecutar servidor MCP
python run_mcp_server.py