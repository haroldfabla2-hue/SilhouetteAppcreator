#!/bin/bash
# script_despliegue_iris.sh - Script automatizado para desplegar IRIS en servidor principal

set -e  # Salir si hay error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Desplegando IRIS en servidor principal${NC}"
echo "================================================="

# Función para logging
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar requisitos del sistema
check_requirements() {
    log "Verificando requisitos del sistema..."
    
    # Verificar SO
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        error "Este script está diseñado para Linux. SO detectado: $OSTYPE"
        exit 1
    fi
    
    # Verificar si es root o tiene sudo
    if [[ $EUID -ne 0 ]] && ! sudo -n true 2>/dev/null; then
        error "Este script requiere permisos de root o sudo"
        exit 1
    fi
    
    # Verificar herramientas necesarias
    command -v curl >/dev/null 2>&1 || { error "curl no está instalado"; exit 1; }
    command -v docker >/dev/null 2>&1 || { error "Docker no está instalado"; exit 1; }
    command -v docker-compose >/dev/null 2>&1 || { error "docker-compose no está instalado"; exit 1; }
    
    log "✅ Todos los requisitos verificados"
}

# Configurar firewall
setup_firewall() {
    log "Configurando firewall..."
    
    # Instalar y configurar ufw si no está
    if ! command -v ufw >/dev/null 2>&1; then
        sudo apt update
        sudo apt install -y ufw
    fi
    
    # Configurar reglas
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow ssh
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Preguntar si activar
    read -p "¿Activar firewall? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo ufw --force enable
        log "✅ Firewall activado"
    else
        warn "Firewall no activado (recomendado en producción)"
    fi
}

# Instalar y configurar Docker
setup_docker() {
    log "Configurando Docker..."
    
    # Crear directorio de instalación
    INSTALL_DIR="/opt/iris-server"
    sudo mkdir -p $INSTALL_DIR
    sudo chown $USER:$USER $INSTALL_DIR
    
    log "📁 Directorio de instalación: $INSTALL_DIR"
    
    # Crear archivos de configuración básicos
    cd $INSTALL_DIR
    
    # Crear docker-compose.yml
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  iris-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - IRIS_ENV=production
      - IRIS_LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./frontends:/var/www/html:ro
    depends_on:
      - iris-server
    restart: unless-stopped
EOF
    
    # Crear Dockerfile
    cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY iris-mcp-integration/ ./iris-mcp-integration/
COPY *.html ./frontends/

# Crear directorios necesarios
RUN mkdir -p /app/data /app/logs /app/frontends

# Puerto del servidor
EXPOSE 8000

# Comando de inicio
CMD ["python3", "iris-mcp-integration/api/iris_metrics_server.py"]
EOF
    
    # Crear nginx.conf
    cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream iris_backend {
        server iris-server:8000;
    }

    server {
        listen 80;
        server_name _;

        # API endpoints
        location /api/ {
            proxy_pass http://iris_backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Streaming SSE
        location /api/stream {
            proxy_pass http://iris_backend/;
            proxy_set_header Host $host;
            proxy_buffering off;
            proxy_cache off;
        }

        # Frontend estático
        location / {
            root /var/www/html;
            try_files $uri $uri/ /index.html;
        }
    }
}
EOF
    
    # Crear directorio para frontends
    mkdir -p frontends
    
    log "✅ Archivos de Docker creados en $INSTALL_DIR"
}

# Configurar como servicio systemd
setup_systemd_service() {
    log "Configurando servicio systemd..."
    
    # Crear archivo de servicio
    sudo tee /etc/systemd/system/iris-server.service > /dev/null << EOF
[Unit]
Description=IRIS Server
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/iris-server
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    
    # Recargar systemd
    sudo systemctl daemon-reload
    sudo systemctl enable iris-server
    
    log "✅ Servicio systemd configurado"
}

# Configurar backup automático
setup_backup() {
    log "Configurando backup automático..."
    
    # Crear script de backup
    cat > /opt/iris-server/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/iris-server/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/iris_backup_$DATE.tar.gz"

mkdir -p $BACKUP_DIR

# Crear backup de datos y configuración
tar -czf $BACKUP_FILE \
    --exclude='backups' \
    --exclude='*.log' \
    /opt/iris-server/

# Mantener solo los últimos 30 backups
ls -t $BACKUP_DIR/iris_backup_*.tar.gz | tail -n +31 | xargs rm -f 2>/dev/null || true

echo "Backup creado: $BACKUP_FILE"
EOF
    
    chmod +x /opt/iris-server/backup.sh
    
    # Agregar al crontab para backups diarios
    (crontab -l 2>/dev/null; echo "0 2 * * * /opt/iris-server/backup.sh") | crontab -
    
    log "✅ Backup automático configurado (diario a las 2:00 AM)"
}

# Desplegar aplicación
deploy_application() {
    log "Desplegando aplicación IRIS..."
    
    cd /opt/iris-server
    
    # Copiar archivos del workspace actual
    if [[ -d "/workspace/iris-mcp-integration" ]]; then
        cp -r /workspace/iris-mcp-integration ./
        cp /workspace/*.html ./frontends/ 2>/dev/null || true
        cp /workspace/requirements.iris.txt ./requirements.txt 2>/dev/null || true
    else
        warn "Workspace no encontrado, creando estructura básica..."
        mkdir -p iris-mcp-integration/api
    fi
    
    # Construir y ejecutar con Docker
    docker-compose build
    docker-compose up -d
    
    log "✅ Aplicación desplegada"
}

# Verificar funcionamiento
verify_deployment() {
    log "Verificando funcionamiento..."
    
    sleep 10  # Esperar a que inicie
    
    # Verificar servicios Docker
    if docker-compose ps | grep -q "Up"; then
        log "✅ Servicios Docker funcionando"
    else
        error "❌ Servicios Docker no están funcionando"
        docker-compose logs
        return 1
    fi
    
    # Verificar API
    if curl -s http://localhost:8000/health > /dev/null; then
        log "✅ API de IRIS respondiendo"
    else
        warn "⚠️ API no responde (verificar después)"
    fi
    
    # Mostrar URLs de acceso
    echo ""
    echo -e "${GREEN}🎯 IRIS desplegado exitosamente!${NC}"
    echo "=================================="
    echo "🌐 Acceso local: http://localhost"
    echo "🔧 API: http://localhost:8000"
    echo "📊 Métricas: http://localhost:8000/api/metrics/summary"
    echo ""
    echo -e "${YELLOW}Comandos útiles:${NC}"
    echo "  • Ver logs: docker-compose logs -f"
    echo "  • Reiniciar: sudo systemctl restart iris-server"
    echo "  • Backup: /opt/iris-server/backup.sh"
    echo ""
    echo -e "${BLUE}Para acceso externo, configura tu dominio en nginx.conf${NC}"
}

# Función principal
main() {
    echo -e "${BLUE}Script de Despliegue IRIS v1.0${NC}"
    echo "==========================================="
    
    check_requirements
    setup_firewall
    setup_docker
    setup_systemd_service
    setup_backup
    deploy_application
    verify_deployment
    
    echo ""
    echo -e "${GREEN}🎉 ¡Despliegue completado exitosamente!${NC}"
}

# Ejecutar solo si se llama directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi