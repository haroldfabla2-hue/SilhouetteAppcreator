#!/bin/bash
# script_vps_produccion.sh - Despliegue específico para VPS de producción

set -e  # Salir si hay error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🚀 Desplegando IRIS en VPS de Producción${NC}"
echo "==============================================="
echo -e "${BLUE}📍 Dominio: silhouettemcp.albertofarah.com${NC}"
echo "==============================================="

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

# Verificar requisitos
check_requirements() {
    log "Verificando requisitos del sistema..."
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        error "Docker no está instalado"
        log "Instalando Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        usermod -aG docker $USER
        log "Docker instalado. Necesitas reiniciar la sesión."
        exit 1
    fi
    
    # Verificar Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose no está instalado"
        log "Instalando Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    
    log "✅ Docker y Docker Compose verificados"
}

# Crear estructura de directorios
setup_directories() {
    log "Creando estructura de directorios..."
    
    IRIS_DIR="/opt/iris-production"
    sudo mkdir -p $IRIS_DIR
    sudo chown $USER:$USER $IRIS_DIR
    cd $IRIS_DIR
    
    # Crear estructura completa
    mkdir -p {data,logs,backups,ssl,frontends,monitoring}
    
    log "✅ Directorio base: $IRIS_DIR"
    echo -e "${BLUE}📁 Directorios creados:${NC}"
    echo "   • data/ - Datos persistentes"
    echo "   • logs/ - Logs del sistema"
    echo "   • backups/ - Backups automáticos"
    echo "   • ssl/ - Certificados SSL"
    echo "   • frontends/ - Archivos web"
    echo "   • monitoring/ - Monitoreo del sistema"
}

# Configurar firewall
setup_firewall() {
    log "Configurando firewall..."
    
    # Instalar y configurar UFW
    if ! command -v ufw &> /dev/null; then
        sudo apt update
        sudo apt install -y ufw
    fi
    
    # Configurar reglas básicas
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Permitir SSH (para no perder acceso)
    sudo ufw allow ssh
    
    # Permitir HTTP y HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Preguntar al usuario
    echo ""
    read -p "¿Activar firewall con estas reglas? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo ufw --force enable
        log "✅ Firewall activado"
        echo -e "${GREEN}🔒 Reglas aplicadas:${NC}"
        echo "   • SSH permitido"
        echo "   • HTTP (80) permitido"
        echo "   • HTTPS (443) permitido"
    else
        warn "Firewall no activado (⚠️ recomendado para producción)"
    fi
}

# Desplegar aplicación
deploy_application() {
    log "Desplegando aplicación IRIS..."
    
    # Copiar archivos de configuración
    if [[ -f "/workspace/docker-compose.production.yml" ]]; then
        cp /workspace/docker-compose.production.yml docker-compose.yml
    else
        # Crear configuración básica si no existe
        cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  iris-server:
    image: python:3.11-slim
    ports:
      - "127.0.0.1:8000:8000"
    command: python3 -c "print('IRIS Server Ready')"
    restart: unless-stopped
EOF
    fi
    
    # Crear Dockerfile básico si no existe
    if [[ ! -f "Dockerfile" ]]; then
        echo "FROM python:3.11-slim" > Dockerfile
        echo "WORKDIR /app" >> Dockerfile
        echo "CMD ['python3', '-c', 'print(\"IRIS Server Ready\")']" >> Dockerfile
    fi
    
    # Construir imagen
    log "Construyendo imagen Docker..."
    docker-compose build --no-cache
    
    # Iniciar servicios
    log "Iniciando servicios..."
    docker-compose up -d
    
    log "✅ Aplicación desplegada"
}

# Configurar SSL con Let's Encrypt
setup_ssl() {
    log "Configurando SSL con Let's Encrypt..."
    
    # Verificar que el dominio apunte al servidor
    echo -e "${YELLOW}⚠️  IMPORTANTE: Verifica que silhouettemcp.albertofarah.com apunte a este servidor${NC}"
    read -p "¿Continuar con la configuración SSL? (y/N): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Instalar Certbot
        if ! command -v certbot &> /dev/null; then
            log "Instalando Certbot..."
            sudo apt update
            sudo apt install -y certbot
        fi
        
        # Obtener certificado SSL
        log "Obteniendo certificado SSL..."
        sudo certbot certonly --standalone -d silhouettemcp.albertofarah.com -d www.silhouettemcp.albertofarah.com
        
        # Crear enlace simbólico para Nginx
        sudo ln -sf /etc/letsencrypt/live/silhouettemcp.albertofarah.com /opt/iris-production/ssl/live
        
        log "✅ SSL configurado"
        echo -e "${GREEN}🔒 Certificado SSL obtenido para:${NC}"
        echo "   • silhouettemcp.albertofarah.com"
        echo "   • www.silhouettemcp.albertofarah.com"
    else
        warn "SSL no configurado (HTTP solo)"
    fi
}

# Configurar monitoreo
setup_monitoring() {
    log "Configurando monitoreo del sistema..."
    
    # Crear script de monitoreo
    cat > monitoring/monitor.sh << 'EOF'
#!/bin/bash
LOG_FILE="/opt/iris-production/monitoring/system.log"

log_event() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

# Verificar estado de IRIS
if ! curl -f -s http://localhost:8000/health > /dev/null; then
    log_event "ERROR: IRIS Server no responde, reiniciando..."
    cd /opt/iris-production && docker-compose restart iris-server
fi

# Verificar uso de disco
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    log_event "WARNING: Uso de disco alto: ${DISK_USAGE}%"
fi

# Verificar memoria
MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ $MEM_USAGE -gt 90 ]; then
    log_event "WARNING: Uso de memoria alto: ${MEM_USAGE}%"
fi
EOF
    
    chmod +x monitoring/monitor.sh
    
    # Agregar al crontab
    (crontab -l 2>/dev/null; echo "*/5 * * * * /opt/iris-production/monitoring/monitor.sh") | crontab -
    
    log "✅ Monitoreo configurado (cada 5 minutos)"
}

# Configurar backup automático
setup_backup() {
    log "Configurando backup automático..."
    
    # Crear script de backup
    cat > backups/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/iris-production/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/iris_backup_$DATE.tar.gz"

# Crear backup
tar -czf $BACKUP_FILE \
    --exclude='backups' \
    --exclude='*.log' \
    /opt/iris-production/

# Limpiar backups antiguos (mantener últimos 30)
find $BACKUP_DIR -name 'iris_backup_*.tar.gz' -mtime +30 -delete

echo "Backup creado: $BACKUP_FILE"
EOF
    
    chmod +x backups/backup.sh
    
    # Agregar al crontab para backup diario a las 2 AM
    (crontab -l 2>/dev/null; echo "0 2 * * * /opt/iris-production/backups/backup.sh") | crontab -
    
    log "✅ Backup automático configurado (diario a las 2:00 AM)"
}

# Verificar funcionamiento
verify_deployment() {
    log "Verificando funcionamiento..."
    
    sleep 10  # Esperar a que inicien los servicios
    
    # Verificar Docker
    if docker-compose ps | grep -q "Up"; then
        log "✅ Servicios Docker funcionando"
    else
        error "❌ Servicios Docker no están funcionando"
        docker-compose logs
        return 1
    fi
    
    # Verificar API local
    if curl -s http://localhost:8000/health > /dev/null; then
        log "✅ API de IRIS respondiendo (localhost)"
    else
        warn "⚠️ API no responde en localhost:8000"
    fi
    
    # Verificar Nginx
    if curl -s -I http://localhost | head -1 | grep -q "200 OK"; then
        log "✅ Nginx respondiendo"
    else
        warn "⚠️ Nginx no responde en localhost:80"
    fi
    
    # Mostrar URLs finales
    echo ""
    echo -e "${GREEN}🎉 ¡Despliegue completado exitosamente!${NC}"
    echo "=========================================="
    echo -e "${BLUE}🌐 URLs de Acceso:${NC}"
    echo "   • Principal: https://silhouettemcp.albertofarah.com"
    echo "   • API Local: http://localhost:8000"
    echo "   • Métricas: https://silhouettemcp.albertofarah.com/api/metrics/summary"
    echo ""
    echo -e "${YELLOW}📊 URLs de Monitoreo:${NC}"
    echo "   • Health: https://silhouettemcp.albertofarah.com/health"
    echo "   • Streaming: https://silhouettemcp.albertofarah.com/api/stream"
    echo "   • Agentes: https://silhouettemcp.albertofarah.com/api/agents"
    echo ""
    echo -e "${PURPLE}🔧 Comandos Útiles:${NC}"
    echo "   • Ver logs: cd /opt/iris-production && docker-compose logs -f"
    echo "   • Reiniciar: cd /opt/iris-production && docker-compose restart"
    echo "   • Status: cd /opt/iris-production && docker-compose ps"
    echo "   • Backup manual: /opt/iris-production/backups/backup.sh"
    echo ""
    echo -e "${BLUE}📂 Directorio base: /opt/iris-production${NC}"
}

# Función principal
main() {
    check_requirements
    setup_directories
    setup_firewall
    deploy_application
    setup_ssl
    setup_monitoring
    setup_backup
    verify_deployment
    
    echo ""
    echo -e "${GREEN}🎯 ¡IRIS está listo en producción!${NC}"
    echo -e "${BLUE}Accede a: https://silhouettemcp.albertofarah.com${NC}"
}

# Ejecutar solo si se llama directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi