#!/bin/bash
# Script de inicio rápido para el Sistema Multi-Agente Superior

set -e

echo "=================================================="
echo "Sistema Multi-Agente Superior"
echo "MVP - Supera a MiniMax Agent"
echo "=================================================="
echo ""

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker no está instalado"
    echo "Instala Docker desde: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose no está instalado"
    echo "Instala Docker Compose desde: https://docs.docker.com/compose/install/"
    exit 1
fi

# Verificar archivo .env
if [ ! -f "backend/.env" ]; then
    echo "Creando archivo .env desde .env.example..."
    cp backend/.env.example backend/.env
    
    echo ""
    echo "IMPORTANTE: Edita backend/.env y añade tus API keys:"
    echo "  - MINIMAX_API_KEY (gratis hasta Nov 7, 2025)"
    echo "  - OPENROUTER_API_KEY (opcional, para fallback)"
    echo ""
    read -p "¿Quieres editar .env ahora? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} backend/.env
    fi
fi

echo ""
echo "Iniciando servicios con Docker Compose..."
echo ""

# Construir e iniciar servicios
docker-compose up --build -d

echo ""
echo "Esperando a que los servicios estén listos..."
sleep 10

# Verificar estado de servicios
echo ""
echo "Estado de servicios:"
docker-compose ps

echo ""
echo "=================================================="
echo "Sistema Multi-Agente Superior iniciado!"
echo "=================================================="
echo ""
echo "Servicios disponibles:"
echo "  - Backend API:  http://localhost:8000"
echo "  - API Docs:     http://localhost:8000/docs"
echo "  - Frontend:     http://localhost:3000"
echo "  - Prometheus:   http://localhost:9090"
echo "  - Grafana:      http://localhost:3001 (admin/admin)"
echo ""
echo "Ver logs:"
echo "  docker-compose logs -f"
echo ""
echo "Detener sistema:"
echo "  docker-compose down"
echo ""

# Verificar health del backend
echo "Verificando health del backend..."
sleep 5

if curl -s http://localhost:8000/health > /dev/null; then
    echo "Backend está funcionando correctamente!"
else
    echo "Advertencia: Backend aún no responde. Puede tardar unos segundos más."
    echo "Verifica los logs con: docker-compose logs backend"
fi

echo ""
echo "Para probar el sistema, abre: http://localhost:3000"
echo ""
