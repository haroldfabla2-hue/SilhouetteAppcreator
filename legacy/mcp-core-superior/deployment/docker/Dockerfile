# Multi-stage Dockerfile optimizado para MCP Core Superior
# Etapa 1: Builder stage para dependencias
FROM python:3.11-slim as builder

# Configurar directorios de trabajo
WORKDIR /app

# Instalar dependencias del sistema para compilación
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Crear entorno virtual y instalar dependencias Python
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar archivos de dependencias
COPY file_processing_requirements.txt ./
COPY src/security/requirements.txt ./security_requirements.txt

# Instalar dependencias
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r file_processing_requirements.txt && \
    pip install --no-cache-dir -r security_requirements.txt && \
    pip install --no-cache-dir fastapi uvicorn psycopg2-binary redis prometheus-client

# Etapa 2: Runtime stage
FROM python:3.11-slim as runtime

# Etiquetas de metadatos
LABEL maintainer="MCP Core Superior Team"
LABEL version="1.0.0"
LABEL description="MCP Core Superior - Servidor de Protocolo de Contexto de Modelo Avanzado"
LABEL org.opencontainers.image.title="MCP Core Superior"
LABEL org.opencontainers.image.description="Sistema MCP con agentes especializados y capacidades avanzadas"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.revision="latest"

# Instalar dependencias mínimas del sistema
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Crear usuario no-root para seguridad
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser

# Configurar directorio de trabajo
WORKDIR /app

# Copiar entorno virtual desde builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Crear directorios necesarios
RUN mkdir -p /app/logs /app/data /app/static /app/uploads && \
    chown -R mcpuser:mcpuser /app

# Configurar directorio de usuario
USER mcpuser

# Variables de entorno por defecto
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Puertos de la aplicación
EXPOSE 8080 8081 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Script de inicialización
COPY --chown=mcpuser:mcpuser deployment/scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Directorio de logs y datos
VOLUME ["/app/logs", "/app/data"]

# Comando por defecto
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "src.core.fastmcp_server:app", "--host", "0.0.0.0", "--port", "8080"]