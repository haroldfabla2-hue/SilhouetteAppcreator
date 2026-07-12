#!/bin/bash

# SilhouetteMCP Dashboard Ultra - Script de Despliegue
# Autor: MiniMax Agent
# Fecha: 2025-11-06

set -e

echo "========================================="
echo "  SilhouetteMCP Dashboard Ultra  "
echo "  Despliegue Automatizado"
echo "========================================="
echo ""

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Directorio base
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_DIR="$SCRIPT_DIR/dashboard-static"
SERVER_FILE="$SCRIPT_DIR/silhouettemcp_server.py"

echo -e "${BLUE}[1/5]${NC} Verificando archivos del dashboard..."
if [ ! -d "$DASHBOARD_DIR" ]; then
    echo -e "${YELLOW}Error: Directorio dashboard-static no encontrado${NC}"
    exit 1
fi

if [ ! -f "$SERVER_FILE" ]; then
    echo -e "${YELLOW}Error: silhouettemcp_server.py no encontrado${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Archivos verificados correctamente"
echo ""

echo -e "${BLUE}[2/5]${NC} Verificando dependencias Python..."
python3 -c "import fastapi" 2>/dev/null || {
    echo -e "${YELLOW}Instalando FastAPI...${NC}"
    pip install fastapi uvicorn -q
}
echo -e "${GREEN}✓${NC} Dependencias instaladas"
echo ""

echo -e "${BLUE}[3/5]${NC} Verificando estructura del dashboard..."
ls -la "$DASHBOARD_DIR" | head -10
echo -e "${GREEN}✓${NC} Estructura verificada"
echo ""

echo -e "${BLUE}[4/5]${NC} Verificando configuración del servidor..."
grep -q "dashboard-ultra" "$SERVER_FILE" && echo -e "${GREEN}✓${NC} Dashboard configurado en el servidor" || echo -e "${YELLOW}⚠${NC} Puede requerir configuración adicional"
echo ""

echo -e "${BLUE}[5/5]${NC} Iniciando servidor SilhouetteMCP..."
echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  Dashboard Ultra Listo!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "${BLUE}URLs disponibles:${NC}"
echo -e "  • Dashboard Ultra: ${GREEN}http://localhost:8001/dashboard-ultra${NC}"
echo -e "  • API Docs:        ${GREEN}http://localhost:8001/docs${NC}"
echo -e "  • Health Check:    ${GREEN}http://localhost:8001/health${NC}"
echo ""
echo -e "${BLUE}Credenciales:${NC}"
echo -e "  • Email:    ${GREEN}alberto.farahb@hotmail.com${NC}"
echo -e "  • Password: ${GREEN}Fbalberto1910${NC}"
echo ""
echo -e "${YELLOW}Presiona Ctrl+C para detener el servidor${NC}"
echo ""

# Iniciar servidor
cd "$SCRIPT_DIR"
python3 silhouettemcp_server.py
