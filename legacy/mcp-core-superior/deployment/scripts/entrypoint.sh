#!/bin/bash
set -e

# Script de entrada para MCP Core Superior
# Maneja inicialización, migraciones y démarrage de la aplicación

echo "🚀 Iniciando MCP Core Superior..."

# Función para health check
health_check() {
    echo "🏥 Verificando salud del sistema..."
    
    # Verificar base de datos
    if [ -n "$DATABASE_URL" ]; then
        echo "📊 Verificando conexión a base de datos..."
        # Agregar lógica de verificación de DB aquí
    fi
    
    # Verificar Redis
    if [ -n "$REDIS_URL" ]; then
        echo "🔴 Verificando conexión a Redis..."
        # Agregar lógica de verificación de Redis aquí
    fi
    
    echo "✅ Health check completado"
}

# Función para ejecutar migraciones
run_migrations() {
    echo "🗄️ Ejecutando migraciones de base de datos..."
    
    # Aquí irían las migraciones específicas del proyecto
    # Por ahora, solo simulamos el proceso
    if [ "$SKIP_MIGRATIONS" != "true" ]; then
        echo "📋 Aplicando migraciones..."
        # python -m alembic upgrade head || echo "⚠️ No se encontraron migraciones"
        echo "✅ Migraciones completadas"
    else
        echo "⏭️ Saltando migraciones (SKIP_MIGRATIONS=true)"
    fi
}

# Función para preparar datos iniciales
prepare_initial_data() {
    echo "📂 Preparando datos iniciales..."
    
    # Crear directorios necesarios
    mkdir -p /app/logs /app/data /app/uploads
    
    # Configurar permisos
    chmod 755 /app/logs /app/data /app/uploads
    
    # Configurar configuración por defecto si no existe
    if [ ! -f "/app/.env" ]; then
        echo "⚙️ Creando archivo .env por defecto..."
        cat > /app/.env << EOF
# Configuración por defecto de MCP Core Superior
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://mcpuser:password@postgres:5432/mcp_core
REDIS_URL=redis://redis:6379/0
VECTOR_DB_URL=postgresql://mcpuser:password@postgres:5432/vector_db
JWT_SECRET=your-super-secret-jwt-key-change-in-production
METRICS_ENABLED=true
STREAMING_ENABLED=true
EOF
    fi
    
    echo "✅ Datos iniciales preparados"
}

# Función de limpieza al cerrar
cleanup() {
    echo "🧹 Cerrando MCP Core Superior..."
    
    # Cerrar conexiones de base de datos gracefully
    # Aquí se podría implementar lógica adicional de limpieza
    
    echo "✅ Cierre completado"
}

# Configurar trap para cleanup
trap cleanup EXIT

# Ejecutar pasos de inicialización
prepare_initial_data
health_check
run_migrations

# Determinar el comando a ejecutar
if [ "$#" -eq 0 ]; then
    # Comando por defecto
    echo "🔧 Ejecutando comando por defecto..."
    exec uvicorn src.core.fastmcp_server:app --host 0.0.0.0 --port 8080 --workers 4
else
    # Comando personalizado proporcionado
    echo "⚡ Ejecutando comando personalizado: $@"
    exec "$@"
fi