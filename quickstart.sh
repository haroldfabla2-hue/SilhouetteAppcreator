#!/bin/bash
# Quick Start - Sistema Multi-Agente
# Ejecuta este script para iniciar y probar el sistema automáticamente

echo "🚀 Iniciando Sistema Multi-Agente..."
echo ""

# 1. Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker no está instalado"
    echo "Instala Docker desde: https://docs.docker.com/get-docker/"
    exit 1
fi

# 2. Iniciar servicios
echo "📦 Iniciando servicios Docker Compose..."
docker compose up --build -d

# 3. Esperar a que estén listos
echo "⏳ Esperando a que los servicios estén listos (30 segundos)..."
sleep 30

# 4. Verificar salud
echo "🔍 Verificando servicios..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend OK"
else
    echo "❌ Backend no responde"
fi

if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend OK"
else
    echo "❌ Frontend no responde"
fi

# 5. Ejecutar prueba
echo ""
echo "🧪 Ejecutando prueba end-to-end..."
python3 test_end_to_end.py

# 6. Mostrar URLs
echo ""
echo "✅ Sistema activo en:"
echo "   Frontend: http://localhost:3000"
echo "   Backend: http://localhost:8000"
echo "   Prometheus: http://localhost:9090"
echo "   Grafana: http://localhost:3001"
echo ""
echo "📋 Para ver logs en tiempo real:"
echo "   docker compose logs -f backend"
echo ""
echo "⏹️  Para detener:"
echo "   docker compose down"
