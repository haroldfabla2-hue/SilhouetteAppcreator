#!/bin/bash
# Script para iniciar el Dashboard React IRIS MCP

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🌐 Iniciando Dashboard IRIS MCP${NC}"
echo "================================="

# Verificar Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js no encontrado${NC}"
    echo "Instala Node.js desde: https://nodejs.org/"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm no encontrado${NC}"
    echo "Instala npm (viene con Node.js)"
    exit 1
fi

# Verificar directorio del dashboard
if [ ! -d "dashboard" ]; then
    echo -e "${RED}Error: Directorio dashboard no encontrado${NC}"
    exit 1
fi

# Cambiar al directorio del dashboard
cd dashboard

# Verificar e instalar dependencias
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Instalando dependencias del dashboard...${NC}"
    npm install
fi

# Verificar variables de entorno
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creando archivo .env para dashboard...${NC}"
    cat > .env << EOF
VITE_API_BASE=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/metrics/stream
EOF
fi

# Configurar puerto
PORT=${1:-3000}

echo -e "${GREEN}📊 Dashboard iniciando en puerto $PORT${NC}"
echo -e "${YELLOW}🌐 Dashboard disponible en: http://localhost:$PORT${NC}"
echo -e "${YELLOW}🔗 API configurada para: http://localhost:8000${NC}"
echo ""
echo -e "${GREEN}Presiona Ctrl+C para detener${NC}"
echo ""

# Iniciar dashboard
npm run dev -- --port $PORT