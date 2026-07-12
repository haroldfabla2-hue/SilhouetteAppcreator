#!/bin/bash
# SilhouetteMCP Production Deployment Script 110/100

set -e

echo "🚀 Iniciando despliegue de SilhouetteMCP en producción..."

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado"
    exit 1
fi

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado"
    exit 1
fi

# Construir imagen
echo "🔨 Construyendo imagen de producción..."
docker build -t silhouettemcp:110.0.0-ultra .

# Desplegar servicios
echo "📦 Desplegando servicios..."
docker-compose up -d

# Verificar estado
echo "🔍 Verificando estado de servicios..."
docker-compose ps

# Configurar SSL
echo "🔒 Configurando certificado SSL..."
certbot --nginx -d silhouettemcp.albertofarah.com

# Verificar endpoints
echo "🧪 Verificando endpoints..."
sleep 10
curl -f https://silhouettemcp.albertofarah.com/health || echo "Health check failed"

echo "✅ Despliegue completado"
echo "🌐 URL de producción: https://silhouettemcp.albertofarah.com"
