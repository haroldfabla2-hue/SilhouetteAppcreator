#!/bin/sh
# MCP Core Superior - Script de inicio STDIO
# Uso: sh run.sh

set -e

# Cambiar al directorio del script
cd "$(dirname "$0")"

echo "🚀 Iniciando MCP Core Superior..." >&2

# Verificar Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ Error: Python 3 no encontrado" >&2
    exit 1
fi

# Verificar que estamos en el directorio correcto
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml no encontrado. Ejecutar desde el directorio raíz del proyecto." >&2
    exit 1
fi

# Crear entorno virtual si no existe
if [ ! -d ".venv" ]; then
    echo "📦 Creando entorno virtual..." >&2
    python3 -m venv .venv
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..." >&2
. .venv/bin/activate

# Instalar/actualizar dependencias
echo "📚 Instalando dependencias..." >&2
echo "⏳ Esto puede tomar varios minutos. Por favor espera..." >&2

# Usar pip install directamente para evitar problemas con uv sync
pip install --upgrade pip setuptools wheel

# Instalar dependencias de desarrollo primero
pip install fastmcp fastapi uvicorn httpx pydantic pydantic-settings sqlalchemy asyncpg psycopg2-binary numpy python-multipart python-jose passlib redis structlog prometheus-client asyncio-throttle cachetools tenacity rich typer click

# Instalar dependencias opcionales
pip install sse-starlette websockets sse-starlette websockets

# Instalar dependencias específicas del File Processing Agent
echo "🖼️ Instalando dependencias para File Processing Agent..." >&2
pip install Pillow opencv-python pytesseract python-docx openpyxl python-pptx librosa mutagen ffmpeg-python qrcode pyzbar

# Instalar dependencias adicionales para procesamiento
pip install chardet PyPDF2 pypdf soundfile audioread piexif exifread

# Instalar dependencias de testing (opcional)
pip install pytest pytest-asyncio pytest-cov black isort flake8 mypy

echo "✅ Dependencias instaladas correctamente" >&2

# Verificar variables de entorno críticas
if [ -z "$MCP_CORE_JWT_SECRET" ] && [ -z "$JWT_SECRET" ]; then
    echo "⚠️  Warning: JWT_SECRET no configurado. Usando secreto por defecto para desarrollo." >&2
    export JWT_SECRET="mcp_core_dev_secret_$(date +%s)"
fi

if [ -z "$MCP_CORE_DATABASE_URL" ] && [ -z "$DATABASE_URL" ]; then
    echo "⚠️  Warning: DATABASE_URL no configurado. Usando SQLite para desarrollo." >&2
    export DATABASE_URL="sqlite:///./mcp_core_dev.db"
fi

if [ -z "$MCP_CORE_VECTOR_DB_URL" ] && [ -z "$VECTOR_DB_URL" ]; then
    echo "⚠️  Warning: VECTOR_DB_URL no configurado. Usando SQLite con soporte vectorial." >&2
    export VECTOR_DB_URL="sqlite:///./vector_db_dev.db"
fi

# Configurar variables de entorno por defecto para desarrollo
export MCP_CORE_ENVIRONMENT="${MCP_CORE_ENVIRONMENT:-development}"
export MCP_CORE_DEBUG="${MCP_CORE_DEBUG:-true}"
export MCP_CORE_HOST="${MCP_CORE_HOST:-0.0.0.0}"
export MCP_CORE_PORT="${MCP_CORE_PORT:-8080}"
export MCP_CORE_MCP_PORT="${MCP_CORE_MCP_PORT:-8081}"

echo "🔧 Configuración:" >&2
echo "   Entorno: $MCP_CORE_ENVIRONMENT" >&2
echo "   Debug: $MCP_CORE_DEBUG" >&2
echo "   Host: $MCP_CORE_HOST" >&2
echo "   Puerto: $MCP_CORE_PORT" >&2
echo "   Puerto MCP: $MCP_CORE_MCP_PORT" >&2
echo "   Base de datos: $(echo $DATABASE_URL | sed 's/:.*@/:\*\*\*@/')" >&2

# Verificar que el archivo server.py existe
if [ ! -f "server.py" ]; then
    echo "❌ Error: server.py no encontrado" >&2
    exit 1
fi

# Cambiar a directorio src para imports relativos
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "🏃 Iniciando servidor MCP en modo STDIO..." >&2

# Ejecutar servidor en modo STDIO
# Nota: Este script está diseñado para ser ejecutado por el ContextForge Gateway
# o cualquier cliente MCP que soporte el protocolo STDIO

exec python3 server.py
