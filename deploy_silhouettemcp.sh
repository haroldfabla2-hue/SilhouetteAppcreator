#!/bin/bash

# ============================================================================
# Script de Despliegue Automático - SilhouetteMCP Server
# Servidor MCP Superior para silhouettemcp.albertofarah.com
# Desarrollado para: Alberto Farah
# ============================================================================

set -e  # Salir en caso de error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuración
DOMAIN="silhouettemcp.albertofarah.com"
EMAIL="alberto.farahb@hotmail.com"
SERVER_PORT=8000
PROJECT_DIR="/opt/silhouettemcp"
BACKUP_DIR="/opt/silhouettemcp/backups"
LOG_FILE="/var/log/silhouettemcp_deploy.log"

# Funciones de utilidad
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}" | tee -a "$LOG_FILE"
}

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Función para verificar si un puerto está en uso
port_in_use() {
    netstat -tuln | grep -q ":$1 "
}

# Verificar permisos de root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Este script debe ejecutarse como root (usa sudo)"
        exit 1
    fi
}

# Verificar requisitos del sistema
check_requirements() {
    log "Verificando requisitos del sistema..."
    
    # Verificar sistema operativo
    if ! [[ -f /etc/os-release ]]; then
        error "No se puede determinar el sistema operativo"
        exit 1
    fi
    
    source /etc/os-release
    
    case "$ID" in
        ubuntu|debian)
            log "Sistema operativo detectado: $PRETTY_NAME"
            ;;
        *)
            warning "Sistema operativo no probado: $PRETTY_NAME"
            ;;
    esac
    
    # Verificar Docker
    if ! command_exists docker; then
        log "Docker no encontrado. Instalando Docker..."
        install_docker
    else
        log "Docker ya está instalado: $(docker --version)"
    fi
    
    # Verificar Docker Compose
    if ! command_exists docker-compose; then
        log "Docker Compose no encontrado. Instalando Docker Compose..."
        install_docker_compose
    else
        log "Docker Compose ya está instalado: $(docker-compose --version)"
    fi
    
    # Verificar puerto disponible
    if port_in_use 80 || port_in_use 443; then
        warning "Los puertos 80 o 443 están en uso. El despliegue podría fallar."
        log "Procesos que usan los puertos:"
        netstat -tuln | grep -E ':(80|443) '
    fi
    
    # Verificar memoria
    MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    if [[ $MEMORY_GB -lt 1 ]]; then
        error "Memoria insuficiente. Se requiere al menos 1GB de RAM."
        exit 1
    fi
    
    # Verificar espacio en disco
    DISK_GB=$(df -BG / | awk 'NR==2{print $4}' | sed 's/G//')
    if [[ $DISK_GB -lt 5 ]]; then
        error "Espacio en disco insuficiente. Se requieren al menos 5GB libres."
        exit 1
    fi
    
    log "Requisitos verificados correctamente"
}

# Instalar Docker
install_docker() {
    log "Instalando Docker..."
    
    apt-get update
    apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Agregar GPG key de Docker
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Agregar repositorio
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Iniciar y habilitar Docker
    systemctl start docker
    systemctl enable docker
    
    # Agregar usuario actual al grupo docker
    if [[ -n "$SUDO_USER" ]]; then
        usermod -aG docker "$SUDO_USER"
        warning "Usuario $SUDO_USER agregado al grupo docker. Puede requerir reinicio de sesión."
    fi
    
    log "Docker instalado exitosamente"
}

# Instalar Docker Compose
install_docker_compose() {
    log "Instalando Docker Compose..."
    
    DOCKER_COMPOSE_VERSION="2.23.0"
    curl -L "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    log "Docker Compose instalado: $(docker-compose --version)"
}

# Configurar firewall
setup_firewall() {
    log "Configurando firewall..."
    
    # Instalar UFW si no está presente
    if ! command_exists ufw; then
        apt-get update
        apt-get install -y ufw
    fi
    
    # Configurar reglas
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    
    # Permitir SSH
    ufw allow 22/tcp
    
    # Permitir HTTP y HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Permitir puerto para monitoreo interno
    ufw allow 8080/tcp
    
    # Habilitar firewall
    ufw --force enable
    
    log "Firewall configurado: SSH(22), HTTP(80), HTTPS(443), Monitor(8080)"
}

# Crear estructura de directorios
create_directories() {
    log "Creando estructura de directorios..."
    
    mkdir -p "$PROJECT_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p /var/log/silhouettemcp
    mkdir -p /etc/silhouettemcp
    mkdir -p /var/www/certbot
    
    # Establecer permisos
    chown -R 1000:1000 "$PROJECT_DIR"  # Usuario docker
    chmod 755 "$PROJECT_DIR"
    
    log "Directorios creados en $PROJECT_DIR"
}

# Configurar DNS
setup_dns() {
    log "Configurando DNS..."
    
    echo ""
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}                    CONFIGURACIÓN DNS REQUERIDA                    ${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BLUE}Para completar el despliegue, debes configurar el DNS:${NC}"
    echo ""
    echo -e "${GREEN}Tipo: A Record${NC}"
    echo -e "${GREEN}Nombre: @ (o silhouettemcp)${NC}"
    echo -e "${GREEN}Valor: $(curl -s ifconfig.me)${NC}"
    echo -e "${GREEN}TTL: 300 (5 minutos)${NC}"
    echo ""
    echo -e "${YELLOW}Verifica la configuración DNS antes de continuar.${NC}"
    echo ""
    
    read -p "¿Has configurado el DNS correctamente? (y/n): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        warning "Despliegue pausado. Configura el DNS y ejecuta el script nuevamente."
        exit 1
    fi
}

# Preparar archivos de la aplicación
prepare_application() {
    log "Preparando archivos de la aplicación..."
    
    # Copiar archivos necesarios
    cp silhouettemcp_server.py "$PROJECT_DIR/"
    cp requirements.silhouettemcp.txt "$PROJECT_DIR/requirements.txt"
    cp Dockerfile.silhouettemcp "$PROJECT_DIR/Dockerfile"
    cp docker-compose.silhouettemcp.yml "$PROJECT_DIR/docker-compose.yml"
    cp nginx.silhouettemcp.conf "$PROJECT_DIR/nginx.conf"
    
    # Crear archivo de configuración de producción
    cat > "$PROJECT_DIR/.env" << EOF
# SilhouetteMCP Production Configuration
DOMAIN=$DOMAIN
EMAIL=$EMAIL
COMPOSE_PROJECT_NAME=silhouettemcp

# Server Configuration
PYTHONUNBUFFERED=1
HOST=0.0.0.0
PORT=$SERVER_PORT

# Security
ADMIN_EMAIL=$EMAIL
EOF
    
    log "Archivos preparados en $PROJECT_DIR"
}

# Configurar SSL con Let's Encrypt
setup_ssl() {
    log "Configurando SSL con Let's Encrypt..."
    
    # Instalar certbot
    if ! command_exists certbot; then
        apt-get update
        apt-get install -y certbot
    fi
    
    # Verificar que el dominio apunte a este servidor
    IP_SERVER=$(curl -s ifconfig.me)
    IP_DOMAIN=$(dig +short $DOMAIN)
    
    if [[ "$IP_SERVER" != "$IP_DOMAIN" ]]; then
        warning "El DNS podría no estar configurado correctamente."
        warning "IP del servidor: $IP_SERVER"
        warning "IP del dominio: $IP_DOMAIN"
        
        read -p "¿Continuar de todos modos? (y/n): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Crear certificado temporal para que nginx pueda iniciar
    mkdir -p /var/www/certbot
    
    # Crear contenedor temporal para nginx sin SSL
    cat > "$PROJECT_DIR/nginx-temp.conf" << 'EOF'
server {
    listen 80;
    server_name silhouettemcp.albertofarah.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 200 "SilhouetteMCP Server - Configuring SSL...";
        add_header Content-Type text/plain;
    }
}
EOF
    
    # Ejecutar certbot para obtener certificado inicial
    certbot certonly \
        --standalone \
        --preferred-challenges http \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --domains "$DOMAIN"
    
    if [[ $? -eq 0 ]]; then
        log "Certificado SSL inicial obtenido exitosamente"
    else
        error "Error obteniendo certificado SSL inicial"
        exit 1
    fi
}

# Construir y desplegar contenedores
deploy_containers() {
    log "Construyendo y desplegando contenedores..."
    
    cd "$PROJECT_DIR"
    
    # Construir imágenes
    docker-compose build --no-cache
    
    # Levantar servicios
    docker-compose up -d
    
    # Esperar a que los servicios estén listos
    log "Esperando a que los servicios estén listos..."
    sleep 30
    
    # Verificar estado de contenedores
    log "Estado de contenedores:"
    docker-compose ps
    
    # Verificar logs
    sleep 10
    log "Logs recientes del servidor:"
    docker-compose logs --tail=20 silhouettemcp-server
    
    log "Contenedores desplegados exitosamente"
}

# Configurar renovación automática de SSL
setup_ssl_renewal() {
    log "Configurando renovación automática de SSL..."
    
    # Crear script de renovación
    cat > /etc/cron.d/silhouettemcp-ssl-renew << EOF
# SilhouetteMCP SSL Renewal
# Renovar certificados SSL automáticamente

0 2 * * * root /usr/bin/certbot renew --quiet --deploy-hook "docker-compose -f $PROJECT_DIR/docker-compose.yml restart nginx"
EOF
    
    chmod 644 /etc/cron.d/silhouettemcp-ssl-renew
    
    # Probar renovación
    certbot renew --dry-run
    
    log "Renovación automática configurada"
}

# Configurar backup automático
setup_backup() {
    log "Configurando backup automático..."
    
    # Crear script de backup
    cat > /opt/silhouettemcp/backup.sh << 'EOF'
#!/bin/bash

# Script de backup para SilhouetteMCP
BACKUP_DIR="/opt/silhouettemcp/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/silhouettemcp_backup_$DATE.tar.gz"

# Crear backup de datos
tar -czf "$BACKUP_FILE" -C /opt/silhouettemcp silhouettemcp_data.json logs/ 2>/dev/null || true

# Mantener solo los últimos 7 backups
find "$BACKUP_DIR" -name "silhouettemcp_backup_*.tar.gz" -type f -mtime +7 -delete

echo "Backup completado: $BACKUP_FILE"
EOF
    
    chmod +x /opt/silhouettemcp/backup.sh
    
    # Programar backup diario a las 2:00 AM
    cat > /etc/cron.d/silhouettemcp-backup << 'EOF'
# SilhouetteMCP Daily Backup
0 2 * * * root /opt/silhouettemcp/backup.sh > /dev/null 2>&1
EOF
    
    chmod 644 /etc/cron.d/silhouettemcp-backup
    
    log "Backup automático configurado (diario a las 2:00 AM)"
}

# Configurar monitoreo
setup_monitoring() {
    log "Configurando sistema de monitoreo..."
    
    # Crear script de health check
    cat > /opt/silhouettemcp/health_check.sh << EOF
#!/bin/bash

# Health check para SilhouetteMCP
LOG_FILE="/var/log/silhouettemcp/health.log"
TIMESTAMP=\$(date '+%Y-%m-%d %H:%M:%S')

# Verificar estado de contenedores
if ! docker-compose -f $PROJECT_DIR/docker-compose.yml ps | grep -q "Up"; then
    echo "[\$TIMESTAMP] ERROR: Containers are down" >> \$LOG_FILE
    
    # Intentar reiniciar
    docker-compose -f $PROJECT_DIR/docker-compose.yml restart
    
    # Enviar notificación (opcional)
    # mail -s "SilhouetteMCP Alert" $EMAIL < /dev/null
else
    echo "[\$TIMESTAMP] OK: All services running" >> \$LOG_FILE
fi
EOF
    
    chmod +x /opt/silhouettemcp/health_check.sh
    
    # Health check cada 5 minutos
    cat > /etc/cron.d/silhouettemcp-health << EOF
# SilhouetteMCP Health Check
*/5 * * * * root /opt/silhouettemcp/health_check.sh
EOF
    
    chmod 644 /etc/cron.d/silhouettemcp-health
    
    log "Sistema de monitoreo configurado"
}

# Crear servicio systemd para gestión
setup_systemd_service() {
    log "Configurando servicio systemd..."
    
    cat > /etc/systemd/system/silhouettemcp.service << EOF
[Unit]
Description=SilhouetteMCP Server Management
Requires=docker.service
After=docker.service
Wants=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
ExecReload=/usr/local/bin/docker-compose restart
TimeoutStartSec=0
User=root

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable silhouettemcp
    
    log "Servicio systemd configurado"
}

# Verificar despliegue
verify_deployment() {
    log "Verificando despliegue..."
    
    # Esperar a que todo esté listo
    sleep 30
    
    # Verificar endpoints
    endpoints=(
        "https://$DOMAIN/health"
        "https://$DOMAIN/metrics/public"
        "https://$DOMAIN/"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -sf "$endpoint" >/dev/null 2>&1; then
            log "✅ $endpoint - OK"
        else
            warning "❌ $endpoint - FAILED"
        fi
    done
    
    # Verificar certificados SSL
    if openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" </dev/null 2>&1 | grep -q "Verify return code: 0"; then
        log "✅ SSL Certificate - Valid"
    else
        warning "❌ SSL Certificate - Invalid"
    fi
    
    # Mostrar información final
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}                    DESPLIEGUE COMPLETADO                       ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BLUE}URLs del Servidor:${NC}"
    echo -e "  🌐 Dashboard: ${GREEN}https://$DOMAIN${NC}"
    echo -e "  📡 API Status: ${GREEN}https://$DOMAIN/health${NC}"
    echo -e "  📊 Métricas: ${GREEN}https://$DOMAIN/metrics/public${NC}"
    echo -e "  📖 API Docs: ${GREEN}https://$DOMAIN/docs${NC}"
    echo ""
    echo -e "${BLUE}Credenciales de Administrador:${NC}"
    echo -e "  📧 Email: ${GREEN}alberto.farahb@hotmail.com${NC}"
    echo -e "  🔑 Contraseña: ${GREEN}Fbalberto1910${NC}"
    echo ""
    echo -e "${BLUE}Comandos Útiles:${NC}"
    echo -e "  📊 Ver estado: ${YELLOW}cd $PROJECT_DIR && docker-compose ps${NC}"
    echo -e "  📋 Ver logs: ${YELLOW}cd $PROJECT_DIR && docker-compose logs -f${NC}"
    echo -e "  🔄 Reiniciar: ${YELLOW}sudo systemctl restart silhouettemcp${NC}"
    echo -e "  💾 Backup: ${YELLOW}/opt/silhouettemcp/backup.sh${NC}"
    echo ""
    echo -e "${BLUE}Servicios Automáticos:${NC}"
    echo -e "  🔄 SSL Renewal: Diario a las 2:00 AM"
    echo -e "  💾 Backup: Diario a las 2:00 AM" 
    echo -e "  🏥 Health Check: Cada 5 minutos"
    echo ""
    log "Despliegue verificado exitosamente"
}

# Función principal de despliegue
main() {
    echo -e "${PURPLE}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                  SilhouetteMCP Server Deployer                ║${NC}"
    echo -e "${PURPLE}║                     Versión 2.0.0                            ║${NC}"
    echo -e "${PURPLE}║                   para $DOMAIN                       ║${NC}"
    echo -e "${PURPLE}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Crear log file
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"
    
    log "Iniciando despliegue de SilhouetteMCP Server..."
    
    # Ejecutar pasos de despliegue
    check_root
    check_requirements
    setup_firewall
    create_directories
    setup_dns
    prepare_application
    setup_ssl
    deploy_containers
    setup_ssl_renewal
    setup_backup
    setup_monitoring
    setup_systemd_service
    verify_deployment
    
    log "🎉 Despliegue completado exitosamente!"
    log "Dashboard disponible en: https://$DOMAIN"
    log "Revisa $LOG_FILE para más detalles"
}

# Ejecutar función principal
main "$@"