#!/bin/bash
# Script de Validación Automatizada - Sistema Multi-Agente
# Fecha: 2025-11-04

set -e

echo "🔍 Iniciando validación del sistema multi-agente..."
echo "=================================================="

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir resultados
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

# 1. Verificar Docker
echo -e "\n${YELLOW}1. Verificando Docker...${NC}"
if command -v docker &> /dev/null; then
    print_result 0 "Docker está instalado"
    docker --version
else
    print_result 1 "Docker NO está instalado"
    exit 1
fi

if docker compose version &> /dev/null; then
    print_result 0 "Docker Compose está instalado"
    docker compose version
else
    print_result 1 "Docker Compose NO está instalado"
    exit 1
fi

# 2. Verificar archivos de configuración
echo -e "\n${YELLOW}2. Verificando configuración...${NC}"
if [ -f "backend/.env" ]; then
    print_result 0 "Archivo backend/.env existe"
    
    # Verificar API keys
    if grep -q "OPENROUTER_API_KEY=sk-" backend/.env; then
        print_result 0 "OPENROUTER_API_KEY configurada"
    else
        print_result 1 "OPENROUTER_API_KEY NO configurada"
    fi
    
    if grep -q "MINIMAX_API_KEY=.*[a-zA-Z0-9]" backend/.env && ! grep -q "MINIMAX_API_KEY=$" backend/.env; then
        print_result 0 "MINIMAX_API_KEY configurada"
    else
        echo -e "${YELLOW}⚠️  MINIMAX_API_KEY vacía (usará OpenRouter como fallback)${NC}"
    fi
else
    print_result 1 "Archivo backend/.env NO existe"
    echo "Ejecuta: cp backend/.env.example backend/.env"
    exit 1
fi

# 3. Iniciar servicios
echo -e "\n${YELLOW}3. Iniciando servicios Docker...${NC}"
echo "Esto puede tomar varios minutos en la primera ejecución..."
docker compose up --build -d

sleep 5

# 4. Verificar servicios activos
echo -e "\n${YELLOW}4. Verificando servicios activos...${NC}"

services=("backend" "frontend" "postgres" "redis" "prometheus" "grafana")
for service in "${services[@]}"; do
    if docker compose ps | grep -q "$service.*Up"; then
        print_result 0 "Servicio $service está activo"
    else
        print_result 1 "Servicio $service NO está activo"
        docker compose logs $service --tail=20
    fi
done

# 5. Esperar a que los servicios estén listos
echo -e "\n${YELLOW}5. Esperando a que los servicios estén listos...${NC}"

# Esperar PostgreSQL
echo "Esperando PostgreSQL..."
max_attempts=30
attempt=0
until docker compose exec -T postgres pg_isready -U postgres &> /dev/null || [ $attempt -eq $max_attempts ]; do
    echo -n "."
    sleep 1
    attempt=$((attempt + 1))
done
if [ $attempt -lt $max_attempts ]; then
    print_result 0 "PostgreSQL está listo"
else
    print_result 1 "PostgreSQL no respondió a tiempo"
fi

# Esperar Redis
echo "Esperando Redis..."
attempt=0
until docker compose exec -T redis redis-cli ping &> /dev/null || [ $attempt -eq $max_attempts ]; do
    echo -n "."
    sleep 1
    attempt=$((attempt + 1))
done
if [ $attempt -lt $max_attempts ]; then
    print_result 0 "Redis está listo"
else
    print_result 1 "Redis no respondió a tiempo"
fi

# Esperar Backend
echo "Esperando Backend API..."
attempt=0
until curl -s http://localhost:8000/health &> /dev/null || [ $attempt -eq $max_attempts ]; do
    echo -n "."
    sleep 1
    attempt=$((attempt + 1))
done
if [ $attempt -lt $max_attempts ]; then
    print_result 0 "Backend API está listo"
else
    print_result 1 "Backend API no respondió a tiempo"
    echo "Logs del backend:"
    docker compose logs backend --tail=50
fi

# Esperar Frontend
echo "Esperando Frontend..."
attempt=0
until curl -s http://localhost:3000 &> /dev/null || [ $attempt -eq $max_attempts ]; do
    echo -n "."
    sleep 1
    attempt=$((attempt + 1))
done
if [ $attempt -lt $max_attempts ]; then
    print_result 0 "Frontend está listo"
else
    print_result 1 "Frontend no respondió a tiempo"
fi

# 6. Probar API del backend
echo -e "\n${YELLOW}6. Probando API del backend...${NC}"

# Health check
health_response=$(curl -s http://localhost:8000/health)
if echo "$health_response" | grep -q "ok\|healthy"; then
    print_result 0 "Health check: OK"
else
    print_result 1 "Health check: ERROR"
    echo "Respuesta: $health_response"
fi

# 7. Ejecutar tarea de prueba
echo -e "\n${YELLOW}7. Ejecutando tarea de prueba...${NC}"
echo "Objetivo: 'Analiza las ventajas de usar sistemas multi-agente versus agentes individuales, incluyendo métricas de rendimiento'"

start_time=$(date +%s)

response=$(curl -s -X POST http://localhost:8000/api/v1/tasks \
    -H "Content-Type: application/json" \
    -d '{
        "objetivo": "Analiza las ventajas de usar sistemas multi-agente versus agentes individuales, incluyendo métricas de rendimiento",
        "contexto": {}
    }')

end_time=$(date +%s)
duration=$((end_time - start_time))

if echo "$response" | grep -q "task_id\|id"; then
    print_result 0 "Tarea creada exitosamente"
    echo "Duración: ${duration}s"
    
    # Extraer task_id
    task_id=$(echo "$response" | grep -o '"task_id":"[^"]*"' | cut -d'"' -f4 || echo "$response" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$task_id" ]; then
        echo "Task ID: $task_id"
        
        # Esperar a que se complete
        echo "Esperando a que la tarea se complete..."
        sleep 10
        
        # Obtener resultado
        result=$(curl -s "http://localhost:8000/api/v1/tasks/$task_id")
        if echo "$result" | grep -q "status\|resultado"; then
            print_result 0 "Resultado obtenido"
            echo "Resultado parcial:"
            echo "$result" | head -c 500
            echo "..."
        fi
    fi
else
    print_result 1 "Error al crear tarea"
    echo "Respuesta: $response"
fi

# 8. Verificar paralelización en logs
echo -e "\n${YELLOW}8. Verificando ejecución paralela de agentes...${NC}"

logs=$(docker compose logs backend --tail=100)

if echo "$logs" | grep -q "ReasonerAgent"; then
    print_result 0 "ReasonerAgent ejecutado"
fi

if echo "$logs" | grep -q "PlannerAgent"; then
    print_result 0 "PlannerAgent ejecutado"
fi

if echo "$logs" | grep -q "ExecutorAgent"; then
    print_result 0 "ExecutorAgent ejecutado"
fi

if echo "$logs" | grep -q "VerifierAgent"; then
    print_result 0 "VerifierAgent ejecutado"
fi

if echo "$logs" | grep -q "MemoryManagerAgent"; then
    print_result 0 "MemoryManagerAgent ejecutado"
fi

# Verificar timestamps para paralelización
echo -e "\n${YELLOW}Analizando timestamps de ejecución paralela...${NC}"
docker compose logs backend | grep "Agent.*started" | tail -10

# 9. Verificar métricas de Prometheus
echo -e "\n${YELLOW}9. Verificando métricas de Prometheus...${NC}"

prometheus_response=$(curl -s http://localhost:9090/-/healthy)
if [ "$prometheus_response" == "Prometheus is Healthy." ]; then
    print_result 0 "Prometheus está activo"
else
    print_result 1 "Prometheus no responde"
fi

# 10. Verificar Grafana
echo -e "\n${YELLOW}10. Verificando Grafana...${NC}"

grafana_response=$(curl -s http://localhost:3001/api/health)
if echo "$grafana_response" | grep -q "ok"; then
    print_result 0 "Grafana está activo"
else
    print_result 1 "Grafana no responde"
fi

# 11. Resumen final
echo -e "\n${YELLOW}=================================================="
echo "📊 RESUMEN DE VALIDACIÓN"
echo "==================================================${NC}"

echo -e "\n✅ Servicios accesibles:"
echo "   - Backend API: http://localhost:8000"
echo "   - Frontend UI: http://localhost:3000"
echo "   - Prometheus: http://localhost:9090"
echo "   - Grafana: http://localhost:3001 (admin/admin)"

echo -e "\n📋 Pasos siguientes:"
echo "   1. Abre http://localhost:3000 en tu navegador"
echo "   2. Ejecuta la prueba manual desde la UI"
echo "   3. Observa la ejecución paralela de los 5 agentes"
echo "   4. Verifica el streaming en tiempo real (<300ms latencia)"
echo "   5. Revisa métricas en Prometheus/Grafana"

echo -e "\n🔍 Para ver logs en tiempo real:"
echo "   docker compose logs -f backend"
echo "   docker compose logs -f frontend"

echo -e "\n⏹️  Para detener el sistema:"
echo "   docker compose down"

echo -e "\n${GREEN}✅ Validación completada${NC}"
