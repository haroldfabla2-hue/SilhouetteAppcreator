#!/bin/bash
# Script de monitoreo completo de IRIS MCP Integration

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Función para limpiar procesos al salir
cleanup() {
    echo -e "\n${YELLOW}Deteniendo todos los servicios...${NC}"
    
    # Matar procesos en background
    if [ ! -z "$METRICS_PID" ]; then
        kill $METRICS_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$DASHBOARD_PID" ]; then
        kill $DASHBOARD_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$NOTIFICATION_PID" ]; then
        kill $NOTIFICATION_PID 2>/dev/null || true
    fi
    
    echo -e "${GREEN}Servicios detenidos${NC}"
    exit 0
}

# Configurar trap para cleanup
trap cleanup SIGINT SIGTERM EXIT

# Verificar que estamos en el directorio correcto
if [ ! -f "setup.sh" ] || [ ! -d "api" ] || [ ! -d "dashboard" ]; then
    echo -e "${RED}Error: Ejecuta este script desde el directorio raíz de IRIS MCP Integration${NC}"
    exit 1
fi

echo -e "${GREEN}🔮 IRIS MCP Integration - Monitoreo Completo${NC}"
echo "============================================"
echo ""

# Verificar entorno virtual
if [ ! -d "iris-mcp-env" ]; then
    echo -e "${YELLOW}Entorno virtual no encontrado. Ejecutando setup...${NC}"
    ./setup.sh
fi

# Configurar puertos
METRICS_PORT=${1:-8000}
DASHBOARD_PORT=${2:-3000}

echo -e "${BLUE}Configuración:${NC}"
echo "  📊 Puerto de métricas: $METRICS_PORT"
echo "  🌐 Puerto de dashboard: $DASHBOARD_PORT"
echo ""

# Verificar puertos disponibles
check_port() {
    local port=$1
    local name=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ Puerto $port ($name) ya está en uso${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Puerto $port ($name) disponible${NC}"
        return 0
    fi
}

echo -e "${YELLOW}Verificando puertos...${NC}"
if ! check_port $METRICS_PORT "métricas"; then
    echo -e "${RED}Cambia el puerto: ./monitor_all.sh $((METRICS_PORT+1)) $DASHBOARD_PORT${NC}"
    exit 1
fi

if ! check_port $DASHBOARD_PORT "dashboard"; then
    echo -e "${RED}Cambia el puerto: ./monitor_all.sh $METRICS_PORT $((DASHBOARD_PORT+1))${NC}"
    exit 1
fi

echo ""

# Activar entorno virtual
source iris-mcp-env/bin/activate

# Función para verificar si un servicio está funcionando
check_service() {
    local name=$1
    local port=$2
    local expected_text=$3
    
    if curl -s http://localhost:$port/ >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $name funcionando en puerto $port${NC}"
        return 0
    else
        echo -e "${RED}❌ $name no disponible en puerto $port${NC}"
        return 1
    fi
}

# Función para mostrar el dashboard
show_dashboard() {
    echo ""
    echo -e "${GREEN}🌐 Dashboard IRIS MCP disponible en:${NC}"
    echo -e "${BLUE}   http://localhost:$DASHBOARD_PORT${NC}"
    echo ""
    echo -e "${YELLOW}Presiona Ctrl+C para detener todos los servicios${NC}"
    echo ""
}

# Iniciar servicios en background
echo -e "${YELLOW}Iniciando servicios...${NC}"

# Iniciar servidor de métricas
echo "📊 Iniciando servidor de métricas..."
./start_metrics_server.sh $METRICS_PORT > logs/metrics.log 2>&1 &
METRICS_PID=$!

# Esperar un poco para que el servidor de métricas inicie
sleep 3

# Verificar que el servidor de métricas esté funcionando
if ! check_service "Servidor de métricas" $METRICS_PORT; then
    echo -e "${RED}Error: Servidor de métricas no pudo iniciar${NC}"
    exit 1
fi

# Iniciar dashboard si Node.js está disponible
if command -v node &> /dev/null && command -v npm &> /dev/null; then
    echo "🌐 Iniciando dashboard..."
    cd dashboard
    npm run dev -- --port $DASHBOARD_PORT > ../../logs/dashboard.log 2>&1 &
    DASHBOARD_PID=$!
    cd ..
    
    # Esperar un poco para que el dashboard inicie
    sleep 5
    
    # Verificar que el dashboard esté funcionando
    if check_service "Dashboard" $DASHBOARD_PORT; then
        show_dashboard
    else
        echo -e "${YELLOW}Dashboard no pudo iniciar, continuando solo con API${NC}"
    fi
else
    echo -e "${YELLOW}Node.js/npm no encontrado. Dashboard no disponible${NC}"
fi

# Iniciar servicio de notificaciones en background (demo)
echo "🔔 Iniciando monitor de notificaciones..."
python notifications/iris_notifications.py monitor > logs/notifications.log 2>&1 &
NOTIFICATION_PID=$!

echo ""
echo -e "${GREEN}🎉 Todos los servicios iniciados exitosamente!${NC}"
echo ""

# Mostrar información de acceso
echo -e "${BLUE}📋 Información de Acceso:${NC}"
echo "  📊 API de Métricas: http://localhost:$METRICS_PORT"
echo "  🔌 SSE Stream: http://localhost:$METRICS_PORT/metrics/stream"
echo "  ❤️  Health Check: http://localhost:$METRICS_PORT/"

if [ ! -z "$DASHBOARD_PID" ]; then
    echo "  🌐 Dashboard: http://localhost:$DASHBOARD_PORT"
fi

echo "  🔮 CLI: ./run_cli.sh status"
echo ""

# Mostrar logs en tiempo real
echo -e "${YELLOW}Mostrando logs en tiempo real (Ctrl+C para salir):${NC}"
echo ""

# Crear directorio de logs si no existe
mkdir -p logs

# Función para mostrar logs
show_logs() {
    local service=$1
    local log_file=$2
    echo -e "${BLUE}=== $service Logs ===${NC}"
    if [ -f "logs/$log_file" ]; then
        tail -n 20 logs/$log_file 2>/dev/null || true
    else
        echo "Archivo de log no encontrado"
    fi
    echo ""
}

# Mostrar logs iniciales
show_logs "Métricas" "metrics.log"

if [ ! -z "$DASHBOARD_PID" ]; then
    show_logs "Dashboard" "dashboard.log"
fi

show_logs "Notificaciones" "notifications.log"

# Monitoreo continuo
echo -e "${YELLOW}Monitoreando servicios...${NC}"
while true; do
    sleep 30
    
    echo ""
    echo -e "${BLUE}--- Estado de Servicios ($(date)) ---${NC}"
    
    # Verificar servicios
    check_service "Servidor de métricas" $METRICS_PORT
    if [ ! -z "$DASHBOARD_PID" ]; then
        check_service "Dashboard" $DASHBOARD_PORT
    fi
    
    # Verificar si algún servicio murió y reiniciarlo
    if [ ! -z "$METRICS_PID" ] && ! kill -0 $METRICS_PID 2>/dev/null; then
        echo -e "${RED}Servidor de métricas se detuvo. Reiniciando...${NC}"
        ./start_metrics_server.sh $METRICS_PORT > logs/metrics.log 2>&1 &
        METRICS_PID=$!
    fi
    
    if [ ! -z "$DASHBOARD_PID" ] && ! kill -0 $DASHBOARD_PID 2>/dev/null; then
        echo -e "${RED}Dashboard se detuvo. Reiniciando...${NC}"
        cd dashboard
        npm run dev -- --port $DASHBOARD_PORT > ../../logs/dashboard.log 2>&1 &
        DASHBOARD_PID=$!
        cd ..
    fi
done