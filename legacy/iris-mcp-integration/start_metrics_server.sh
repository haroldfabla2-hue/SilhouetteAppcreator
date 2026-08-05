#!/bin/bash
# Script para iniciar el servidor de métricas IRIS MCP

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Iniciando Servidor de Métricas IRIS MCP${NC}"
echo "==============================================="

# Verificar entorno virtual
if [ ! -d "iris-mcp-env" ]; then
    echo -e "${RED}Error: Entorno virtual no encontrado. Ejecuta setup.sh primero${NC}"
    exit 1
fi

# Activar entorno virtual
source iris-mcp-env/bin/activate

# Instalar dependencias si no están instaladas
if ! python -c "import fastapi, uvicorn" 2>/dev/null; then
    echo -e "${YELLOW}Instalando dependencias...${NC}"
    pip install -r requirements.txt
fi

# Verificar puerto disponible
PORT=${1:-8000}
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}Error: Puerto $PORT ya está en uso${NC}"
    echo "Usa un puerto diferente: ./start_metrics_server.sh 8001"
    exit 1
fi

echo -e "${GREEN}📊 Servidor de métricas iniciando en puerto $PORT${NC}"
echo -e "${YELLOW}🌐 API disponible en: http://localhost:$PORT${NC}"
echo -e "${YELLOW}📡 SSE Stream en: http://localhost:$PORT/metrics/stream${NC}"
echo -e "${YELLOW}📋 Health check en: http://localhost:$PORT/${NC}"
echo ""
echo -e "${GREEN}Presiona Ctrl+C para detener${NC}"
echo ""

# Iniciar servidor
cd api
python iris_metrics_server.py --port $PORT