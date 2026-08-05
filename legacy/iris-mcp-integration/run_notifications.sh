#!/bin/bash
# Script para el Sistema de Notificaciones IRIS MCP

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔔 Sistema de Notificaciones IRIS MCP${NC}"
echo "======================================"

# Verificar entorno virtual
if [ ! -d "iris-mcp-env" ]; then
    echo -e "${RED}Error: Entorno virtual no encontrado. Ejecuta setup.sh primero${NC}"
    exit 1
fi

# Activar entorno virtual
source iris-mcp-env/bin/activate

# Instalar dependencias si no están instaladas
if ! python -c "import smtplib, requests" 2>/dev/null; then
    echo -e "${YELLOW}Instalando dependencias...${NC}"
    pip install -r requirements.txt
fi

# Añadir directorio actual al PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Mostrar menú interactivo si no se proporcionan argumentos
if [ $# -eq 0 ]; then
    echo ""
    echo -e "${GREEN}Opciones disponibles:${NC}"
    echo "  1) Configurar notificaciones por email"
    echo "  2) Configurar notificaciones por webhook"
    echo "  3) Configurar notificaciones por consola"
    echo "  4) Probar configuraciones"
    echo "  5) Ver estadísticas"
    echo "  6) Ver historial"
    echo "  7) Salir"
    echo ""
    read -p "Selecciona una opción (1-7): " choice
    
    case $choice in
        1)
            echo -e "${YELLOW}Configuración de Email${NC}"
            python notifications/iris_notifications.py configure email
            ;;
        2)
            echo -e "${YELLOW}Configuración de Webhook${NC}"
            python notifications/iris_notifications.py configure webhook
            ;;
        3)
            echo -e "${YELLOW}Configuración de Consola${NC}"
            python notifications/iris_notifications.py configure console
            ;;
        4)
            echo -e "${YELLOW}Probando configuraciones...${NC}"
            python notifications/iris_notifications.py test
            ;;
        5)
            echo -e "${YELLOW}Estadísticas de notificaciones${NC}"
            python notifications/iris_notifications.py stats
            ;;
        6)
            echo -e "${YELLOW}Historial de notificaciones${NC}"
            python notifications/iris_notifications.py history
            ;;
        7)
            echo "Saliendo..."
            exit 0
            ;;
        *)
            echo -e "${RED}Opción inválida${NC}"
            exit 1
            ;;
    esac
else
    # Ejecutar con argumentos
    python notifications/iris_notifications.py "$@"
fi