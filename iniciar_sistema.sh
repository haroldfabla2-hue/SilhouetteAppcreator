#!/bin/bash

# Script de inicio del Sistema Multi-Agente Superior
# Corregido y optimizado - Solución robusta y escalable

echo "🚀 Iniciando Sistema Multi-Agente Superior"
echo "============================================"

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Ejecutar desde el directorio raíz del proyecto"
    exit 1
fi

# Función para verificar si un puerto está disponible
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0  # Puerto está en uso
    else
        return 1  # Puerto está libre
    fi
}

# Verificar si los puertos están libres
echo "🔍 Verificando puertos disponibles..."

# Verificar puerto 8000 (Backend)
if check_port 8000; then
    echo "⚠️  Puerto 8000 en uso. Deteniendo proceso existente..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
fi

# Verificar puerto 3000 (Frontend)
if check_port 3000; then
    echo "⚠️  Puerto 3000 en uso. Deteniendo proceso existente..."
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
fi

echo "✅ Puertos verificados y liberados"

# Verificar que las dependencias estén instaladas
echo "🔧 Verificando dependencias de Python..."
cd backend
if [ ! -d "node_modules" ] && [ ! -f "*.pyc" ]; then
    echo "📦 Instalando dependencias de Python..."
    pip install fastapi uvicorn pydantic pydantic-settings httpx asyncio redis psycopg2-binary pgvector python-dotenv --quiet
fi

cd ..

echo "🌐 Iniciando Backend FastAPI en puerto 8000..."
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Esperar que el backend esté listo
echo "⏳ Esperando que el backend esté listo..."
sleep 5

# Probar conectividad del backend
for i in {1..10}; do
    if curl -s http://localhost:8000/health >/dev/null; then
        echo "✅ Backend disponible en http://localhost:8000"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ Backend no responde después de 10 intentos"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    echo "⏳ Intento $i/10..."
    sleep 2
done

echo "🌐 Iniciando Frontend en puerto 3000..."
cd frontend_simple
python -m http.server 3000 &
FRONTEND_PID=$!
cd ..

# Esperar que el frontend esté listo
echo "⏳ Esperando que el frontend esté listo..."
sleep 3

# Verificar que el frontend responda
if curl -s http://localhost:3000 >/dev/null; then
    echo "✅ Frontend disponible en http://localhost:3000"
else
    echo "❌ Frontend no responde"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "🎉 ¡SISTEMA INICIADO EXITOSAMENTE!"
echo "================================="
echo "🔗 URLs de Acceso:"
echo "   • Frontend (Interfaz Web): http://localhost:3000"
echo "   • Backend API:            http://localhost:8000"
echo "   • API Documentation:      http://localhost:8000/docs"
echo ""
echo "📊 Estado del Sistema:"
curl -s http://localhost:8000/api/v1/stats | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'   • Sistema: {data[\"system\"][\"status\"]} (v{data[\"system\"][\"version\"]})')
print(f'   • LLM Router: {data[\"llm\"][\"total_calls\"]} llamadas')
print(f'   • MiniMax gratuito: {data[\"llm\"][\"minimax_free_days_remaining\"]} días restantes')
print(f'   • Agentes activos: {len(data[\"orchestrator\"][\"agents\"][\"executors\"]) + 4} agentes')
print(f'   • Sesiones activas: {data[\"orchestrator\"][\"active_sessions\"]}')
"
echo ""
echo "🚀 ¡Ya puedes ver la interfaz en http://localhost:3000!"
echo ""
echo "📝 Comandos útiles:"
echo "   • Detener sistema: Ctrl+C o matar procesos en puertos 3000 y 8000"
echo "   • Ver logs backend: curl http://localhost:8000/api/v1/stats"
echo "   • Test LLM: curl -X POST http://localhost:8000/api/v1/llm/test"
echo ""

# Guardar PIDs para limpieza posterior
echo $BACKEND_PID > backend.pid
echo $FRONTEND_PID > frontend.pid

echo "💾 PIDs guardados en backend.pid y frontend.pid para limpieza posterior"
echo ""

# Mantener el script ejecutándose
echo "🟢 Sistema en ejecución... Presiona Ctrl+C para detener"
trap 'echo ""; echo "🛑 Deteniendo sistema..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f backend.pid frontend.pid; echo "✅ Sistema detenido"; exit' INT

# Esperar indefinidamente
wait