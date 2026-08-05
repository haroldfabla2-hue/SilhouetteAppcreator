#!/bin/bash

# =========================================================
# SCRIPT DE DESPLIEGUE COMPLETO
# SilhouetteMCP Server - FINAL UNIFIED v4.0.0
# =========================================================

set -e  # Exit on any error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Variables de configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="/opt/silhouettemcp_v4_unified"
BACKUP_DIR="/var/backups/silhouettemcp"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DEPLOY_LOG="/var/log/silhouettemcp/deploy_${TIMESTAMP}.log"

# Opciones de instalación
INSTALL_MODE="full"  # full, basic, docker
INSTALL_SERVICES=true
CONFIGURE_SSL=false
CONFIGURE_BACKUP=true
RUN_TESTS=true

# Función para logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_info() {
    echo -e "${PURPLE}[INFO]${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1" | tee -a "$DEPLOY_LOG"
}

# Función para mostrar banner
show_banner() {
    clear
    echo "=============================================="
    echo "🚀 SILHOUETTEMCP DEPLOYMENT SCRIPT v4.0.0"
    echo "=============================================="
    echo "Instalación FINAL UNIFIED - 51 herramientas"
    echo "De 3 agentes → 6 agentes especializados"
    echo "=============================================="
    echo
}

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [OPCIONES]"
    echo
    echo "Opciones:"
    echo "  --mode MODE              Modo de instalación (full|basic|docker) [default: full]"
    echo "  --no-services            No configurar servicios del sistema"
    echo "  --ssl                    Configurar SSL"
    echo "  --no-backup              No configurar backup automático"
    echo "  --no-tests               No ejecutar tests de verificación"
    echo "  --help                   Mostrar esta ayuda"
    echo
    echo "Ejemplos:"
    echo "  $0                      # Instalación completa"
    echo "  $0 --mode basic         # Instalación básica"
    echo "  $0 --ssl                # Con SSL"
    echo "  $0 --mode docker        # Con Docker"
    echo
}

# Función para parsear argumentos
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --mode)
                INSTALL_MODE="$2"
                shift 2
                ;;
            --no-services)
                INSTALL_SERVICES=false
                shift
                ;;
            --ssl)
                CONFIGURE_SSL=true
                shift
                ;;
            --no-backup)
                CONFIGURE_BACKUP=false
                shift
                ;;
            --no-tests)
                RUN_TESTS=false
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Opción desconocida: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    log_info "Modo de instalación: $INSTALL_MODE"
    log_info "Configurar servicios: $INSTALL_SERVICES"
    log_info "Configurar SSL: $CONFIGURE_SSL"
    log_info "Configurar backup: $CONFIGURE_BACKUP"
    log_info "Ejecutar tests: $RUN_TESTS"
}

# Función para verificar sistema operativo
check_operating_system() {
    log_step "Verificando sistema operativo..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            OS="ubuntu"
            log_success "Sistema detectado: Ubuntu/Debian"
        elif command -v yum &> /dev/null; then
            OS="centos"
            log_success "Sistema detectado: CentOS/RHEL"
        else
            log_error "Sistema Linux no soportado"
            exit 1
        fi
    else
        log_error "Solo se soporta Linux para instalación completa"
        exit 1
    fi
}

# Función para verificar requisitos del sistema
check_system_requirements() {
    log_step "Verificando requisitos del sistema..."
    
    local cpu_cores=$(nproc)
    local memory_gb=$(free -g | awk '/^Mem:/{print $2}')
    local disk_gb=$(df -BG / | awk 'NR==2{print $4}' | sed 's/G//')
    
    log_info "CPU cores: $cpu_cores"
    log_info "RAM: ${memory_gb}GB"
    log_info "Espacio disponible: ${disk_gb}GB"
    
    if [ "$cpu_cores" -lt 2 ]; then
        log_warning "Se recomienda al menos 2 CPU cores"
    fi
    
    if [ "$memory_gb" -lt 2 ]; then
        log_warning "Se recomienda al menos 2GB de RAM"
    fi
    
    if [ "$disk_gb" -lt 5 ]; then
        log_error "Se requiere al menos 5GB de espacio libre"
        exit 1
    fi
    
    log_success "Requisitos del sistema verificados"
}

# Función para actualizar sistema
update_system() {
    log_step "Actualizando sistema..."
    
    if [ "$OS" = "ubuntu" ]; then
        apt-get update
        apt-get upgrade -y
    elif [ "$OS" = "centos" ]; then
        yum update -y
    fi
    
    log_success "Sistema actualizado"
}

# Función para instalar dependencias base
install_base_dependencies() {
    log_step "Instalando dependencias base..."
    
    local packages=(
        "curl"
        "wget"
        "git"
        "software-properties-common"
        "apt-transport-https"
        "ca-certificates"
        "gnupg"
        "lsb-release"
    )
    
    if [ "$OS" = "ubuntu" ]; then
        packages+=("python3.9" "python3.9-venv" "python3-pip")
    elif [ "$OS" = "centos" ]; then
        packages+=("python39" "python3-pip")
    fi
    
    if [ "$INSTALL_MODE" = "full" ]; then
        packages+=(
            "nginx"
            "postgresql"
            "redis"
            "postgresql-contrib"
            "ufw"
            "fail2ban"
            "logrotate"
            "cron"
        )
    fi
    
    if [ "$OS" = "ubuntu" ]; then
        apt-get install -y "${packages[@]}"
    elif [ "$OS" = "centos" ]; then
        yum install -y "${packages[@]}"
    fi
    
    log_success "Dependencias base instaladas"
}

# Función para instalar Python 3.9 si no está disponible
install_python39() {
    log_step "Verificando Python 3.9..."
    
    if ! python3.9 --version &>/dev/null; then
        log_info "Instalando Python 3.9..."
        
        if [ "$OS" = "ubuntu" ]; then
            add-apt-repository ppa:deadsnakes/ppa -y
            apt-get update
            apt-get install -y python3.9 python3.9-venv python3.9-dev
        elif [ "$OS" = "centos" ]; then
            yum install -y python39 python39-devel
        fi
    fi
    
    log_success "Python 3.9 verificado"
}

# Función para instalar Docker (modo docker)
install_docker() {
    if [ "$INSTALL_MODE" != "docker" ]; then
        return
    fi
    
    log_step "Instalando Docker..."
    
    # Instalar Docker
    if [ "$OS" = "ubuntu" ]; then
        apt-get install -y docker.io docker-compose
    elif [ "$OS" = "centos" ]; then
        yum install -y docker docker-compose
    fi
    
    # Iniciar y habilitar Docker
    systemctl start docker
    systemctl enable docker
    
    # Agregar usuario al grupo docker
    usermod -aG docker www-data 2>/dev/null || true
    
    log_success "Docker instalado"
}

# Función para configurar firewall
configure_firewall() {
    if [ "$INSTALL_SERVICES" = false ]; then
        return
    fi
    
    log_step "Configurando firewall..."
    
    # Configurar UFW
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    
    # Permitir SSH (asegúrate de que no te bloquees)
    ufw allow ssh
    
    # Permitir HTTP y HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Puerto interno para el servidor
    ufw allow 8001/tcp
    
    # Docker (si está instalado)
    if command -v docker &> /dev/null; then
        ufw allow from 172.16.0.0/12  # Docker network
    fi
    
    # Habilitar firewall
    ufw --force enable
    
    log_success "Firewall configurado"
}

# Función para configurar Fail2Ban
configure_fail2ban() {
    if [ "$INSTALL_SERVICES" = false ] || [ "$INSTALL_MODE" = "basic" ]; then
        return
    fi
    
    log_step "Configurando Fail2Ban..."
    
    # Configuración básica para SilhouetteMCP
    cat > /etc/fail2ban/jail.d/silhouettemcp.conf << EOF
[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3
bantime = 3600

[silhouettemcp]
enabled = true
filter = silhouettemcp
logpath = /var/log/silhouettemcp/*.log
maxretry = 5
bantime = 1800
EOF
    
    systemctl restart fail2ban
    log_success "Fail2Ban configurado"
}

# Función para crear estructura de directorios
create_directory_structure() {
    log_step "Creando estructura de directorios..."
    
    local dirs=(
        "$INSTALL_DIR"
        "$INSTALL_DIR/data"
        "$INSTALL_DIR/logs"
        "$INSTALL_DIR/uploads"
        "$BACKUP_DIR"
        "/var/log/silhouettemcp"
        "/etc/silhouettemcp"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
    done
    
    log_success "Estructura de directorios creada"
}

# Función para instalar aplicación
install_application() {
    log_step "Instalando aplicación..."
    
    # Copiar archivos del servidor
    cp -r "$PROJECT_DIR/server/"* "$INSTALL_DIR/"
    
    # Configurar permisos
    chown -R www-data:www-data "$INSTALL_DIR"
    chmod -R 755 "$INSTALL_DIR"
    chmod 644 "$INSTALL_DIR"/*.py
    chmod 644 "$INSTALL_DIR"/*.html
    chmod 644 "$INSTALL_DIR"/*.txt
    
    # Directorios con permisos específicos
    chmod 755 "$INSTALL_DIR/data"
    chmod 755 "$INSTALL_DIR/logs"
    chmod 755 "$INSTALL_DIR/uploads"
    
    log_success "Aplicación instalada"
}

# Función para configurar entorno virtual
setup_virtual_environment() {
    log_step "Configurando entorno virtual..."
    
    local venv_path="$INSTALL_DIR/venv"
    
    # Crear entorno virtual
    python3.9 -m venv "$venv_path"
    source "$venv_path/bin/activate"
    
    # Actualizar pip
    pip install --upgrade pip wheel setuptools
    
    # Instalar dependencias
    if [ -f "$INSTALL_DIR/requirements.txt" ]; then
        pip install -r "$INSTALL_DIR/requirements.txt"
        log_success "Dependencias instaladas"
    else
        log_warning "Archivo requirements.txt no encontrado"
    fi
    
    deactivate
    log_success "Entorno virtual configurado"
}

# Función para configurar variables de entorno
setup_environment() {
    log_step "Configurando variables de entorno..."
    
    local env_file="$INSTALL_DIR/.env"
    
    # Crear desde template
    if [ -f "$PROJECT_DIR/.env.example" ]; then
        cp "$PROJECT_DIR/.env.example" "$env_file"
        log_success "Archivo .env creado desde template"
    else
        log_warning "Template .env.example no encontrado"
        return
    fi
    
    # Generar hash de contraseña por defecto
    default_password="Fbalberto1910"
    password_hash=$(echo -n "$default_password" | sha256sum | cut -d' ' -f1)
    
    # Actualizar valores por defecto
    sed -i "s|# ADMIN_PASSWORD_HASH=.*|ADMIN_PASSWORD_HASH=$password_hash|" "$env_file"
    sed -i "s|ADMIN_EMAIL=.*|ADMIN_EMAIL=alberto.farahb@hotmail.com|" "$env_file"
    
    chown www-data:www-data "$env_file"
    chmod 600 "$env_file"
    
    log_success "Variables de entorno configuradas"
    log_warning "IMPORTANTE: Revisa y actualiza las configuraciones en $env_file"
}

# Función para configurar servicios del sistema
setup_systemd_service() {
    if [ "$INSTALL_SERVICES" = false ]; then
        return
    fi
    
    log_step "Configurando servicio systemd..."
    
    local service_file="/etc/systemd/system/silhouettemcp.service"
    local service_template="$PROJECT_DIR/config/silhouettemcp.service"
    
    if [ -f "$service_template" ]; then
        cp "$service_template" "$service_file"
        
        # Actualizar rutas
        sed -i "s|/opt/silhouettemcp_v4_unified|$INSTALL_DIR|g" "$service_file"
        
        # Recargar daemon y habilitar servicio
        systemctl daemon-reload
        systemctl enable silhouettemcp.service
        
        log_success "Servicio systemd configurado"
    else
        log_warning "Template de servicio no encontrado"
    fi
}

# Función para configurar nginx
setup_nginx() {
    if [ "$INSTALL_SERVICES" = false ]; then
        return
    fi
    
    log_step "Configurando nginx..."
    
    local nginx_conf="/etc/nginx/sites-available/silhouettemcp"
    local nginx_template="$PROJECT_DIR/config/nginx.conf"
    
    if [ -f "$nginx_template" ]; then
        cp "$nginx_template" "$nginx_conf"
        
        # Habilitar sitio
        if [ ! -L "/etc/nginx/sites-enabled/silhouettemcp" ]; then
            ln -sf "$nginx_conf" "/etc/nginx/sites-enabled/silhouettemcp"
        fi
        
        # Deshabilitar sitio por defecto
        rm -f /etc/nginx/sites-enabled/default
        
        # Probar configuración
        if nginx -t; then
            log_success "Configuración de nginx válida"
        else
            log_error "Error en configuración de nginx"
            return 1
        fi
    else
        log_warning "Template de nginx no encontrado"
    fi
}

# Función para configurar SSL
setup_ssl() {
    if [ "$CONFIGURE_SSL" = false ]; then
        return
    fi
    
    log_step "Configurando SSL..."
    
    # Crear directorio SSL
    mkdir -p /etc/ssl/silhouettemcp
    
    log_warning "SSL configurado básicamente. Para Let's Encrypt:"
    echo "  1. Instalar certbot: apt install certbot python3-certbot-nginx"
    echo "  2. Obtener certificado: certbot --nginx -d your-domain.com"
    echo "  3. Configurar renovación automática"
    
    log_success "Configuración SSL básica completada"
}

# Función para configurar usuario del sistema
setup_system_user() {
    log_step "Configurando usuario del sistema..."
    
    # Crear usuario si no existe
    if ! id "silhouettemcp" &>/dev/null; then
        useradd -r -s /bin/false -d "$INSTALL_DIR" -M silhouettemcp
        log_success "Usuario 'silhouettemcp' creado"
    fi
    
    # Asignar permisos
    chown -R silhouettemcp:silhouettemcp "$INSTALL_DIR" 2>/dev/null || chown -R www-data:www-data "$INSTALL_DIR"
    chown -R silhouettemcp:silhouettemcp "/var/log/silhouettemcp" 2>/dev/null || chown -R www-data:www-data "/var/log/silhouettemcp"
}

# Función para configurar cron jobs
setup_cron_jobs() {
    if [ "$CONFIGURE_BACKUP" = false ] || [ "$INSTALL_SERVICES" = false ]; then
        return
    fi
    
    log_step "Configurando cron jobs..."
    
    local cron_file="/etc/cron.d/silhouettemcp"
    
    cat > "$cron_file" << EOF
# SilhouetteMCP Backup job
0 2 * * * root $SCRIPT_DIR/backup.sh >> /var/log/silhouettemcp/cron.log 2>&1

# Log rotation
0 0 * * * root logrotate /etc/logrotate.d/silhouettemcp >> /var/log/silhouettemcp/cron.log 2>&1
EOF
    
    chmod 644 "$cron_file"
    
    log_success "Cron jobs configurados"
}

# Función para configurar logrotate
setup_logrotate() {
    if [ "$INSTALL_SERVICES" = false ]; then
        return
    fi
    
    log_step "Configurando logrotate..."
    
    cat > /etc/logrotate.d/silhouettemcp << EOF
/var/log/silhouettemcp/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    postrotate
        systemctl reload silhouettemcp > /dev/null 2>&1 || true
    endscript
}
EOF
    
    log_success "Logrotate configurado"
}

# Función para configurar Docker (modo docker)
setup_docker() {
    if [ "$INSTALL_MODE" != "docker" ]; then
        return
    fi
    
    log_step "Configurando Docker..."
    
    # Copiar docker-compose.yml
    cp "$PROJECT_DIR/config/docker-compose.yml" "$INSTALL_DIR/"
    
    # Crear archivo .env para Docker
    cat > "$INSTALL_DIR/.env.docker" << EOF
COMPOSE_PROJECT_NAME=silhouettemcp_v4_unified
COMPOSE_FILE=docker-compose.yml
EOF
    
    # Configurar permisos
    chown -R www-data:www-data "$INSTALL_DIR"
    
    log_success "Docker configurado"
}

# Función para iniciar servicios
start_services() {
    if [ "$INSTALL_MODE" = "docker" ]; then
        log_step "Iniciando servicios Docker..."
        
        cd "$INSTALL_DIR"
        docker-compose --profile basic up -d
        
        log_success "Servicios Docker iniciados"
        return
    fi
    
    if [ "$INSTALL_SERVICES" = false ]; then
        return
    fi
    
    log_step "Iniciando servicios..."
    
    # Iniciar servicio principal
    if systemctl start silhouettemcp.service; then
        log_success "Servicio SilhouetteMCP iniciado"
    else
        log_error "Error iniciando servicio SilhouetteMCP"
        return 1
    fi
    
    # Reiniciar nginx
    if systemctl restart nginx.service; then
        log_success "Nginx reiniciado"
    else
        log_error "Error reiniciando nginx"
    fi
    
    # Iniciar servicios adicionales
    if [ "$INSTALL_MODE" = "full" ]; then
        systemctl start postgresql
        systemctl start redis
        systemctl start fail2ban
    fi
}

# Función para ejecutar tests de verificación
run_verification_tests() {
    if [ "$RUN_TESTS" = false ]; then
        return
    fi
    
    log_step "Ejecutando tests de verificación..."
    
    local tests_passed=0
    local total_tests=5
    
    # Test 1: Puerto 8001
    if netstat -tuln | grep -q ":8001 "; then
        log_success "✓ Puerto 8001 en uso"
        ((tests_passed++))
    else
        log_error "✗ Puerto 8001 no está en uso"
    fi
    
    # Test 2: Endpoint health
    if curl -s http://localhost:8001/health >/dev/null 2>&1; then
        log_success "✓ Endpoint /health respondiendo"
        ((tests_passed++))
    else
        log_warning "✗ Endpoint /health no responde"
    fi
    
    # Test 3: Servicio systemd
    if systemctl is-active --quiet silhouettemcp.service; then
        log_success "✓ Servicio SilhouetteMCP activo"
        ((tests_passed++))
    else
        log_error "✗ Servicio SilhouetteMCP no está activo"
    fi
    
    # Test 4: Nginx (si está configurado)
    if systemctl is-active --quiet nginx; then
        log_success "✓ Nginx activo"
        ((tests_passed++))
    else
        log_warning "✗ Nginx no está activo"
    fi
    
    # Test 5: Archivos de aplicación
    if [ -f "$INSTALL_DIR/silhouettemcp_server_unified.py" ]; then
        log_success "✓ Archivos de aplicación presentes"
        ((tests_passed++))
    else
        log_error "✗ Archivos de aplicación faltantes"
    fi
    
    log_info "Tests pasados: $tests_passed/$total_tests"
    
    if [ $tests_passed -ge 4 ]; then
        log_success "✅ Verificación completada exitosamente"
        return 0
    else
        log_error "❌ Verificación falló"
        return 1
    fi
}

# Función para mostrar información post-instalación
show_post_install_info() {
    log_success "=============================================="
    log_success "🚀 DESPLIEGUE COMPLETADO EXITOSAMENTE"
    log_success "=============================================="
    
    echo
    log_info "📊 INFORMACIÓN DEL SISTEMA:"
    echo "  • Versión: 4.0.0 FINAL UNIFIED"
    echo "  • Agentes: 6 (Maps, Financial, Social/Travel, Content, Database, Research)"
    echo "  • Herramientas: 51 total"
    echo "  • Instalación: $INSTALL_MODE"
    echo "  • Directorio: $INSTALL_DIR"
    echo
    
    if [ "$INSTALL_MODE" = "docker" ]; then
        log_info "🐳 COMANDOS DOCKER:"
        echo "  • Ver estado: docker-compose ps"
        echo "  • Ver logs: docker-compose logs -f"
        echo "  • Reiniciar: docker-compose restart"
        echo
    else
        log_info "🔧 COMANDOS DEL SISTEMA:"
        echo "  • Ver estado: systemctl status silhouettemcp"
        echo "  • Ver logs: journalctl -u silhouettemcp -f"
        echo "  • Reiniciar: systemctl restart silhouettemcp"
        echo "  • Backup: bash $SCRIPT_DIR/backup.sh"
        echo
    fi
    
    log_info "🌐 URLs IMPORTANTES:"
    echo "  • Servidor: http://localhost:8001"
    echo "  • Dashboard: http://localhost:8001/files/dashboard"
    echo "  • API docs: http://localhost:8001/docs"
    echo "  • Health: http://localhost:8001/health"
    echo "  • Stats: http://localhost:8001/stats"
    echo
    
    log_info "📁 ARCHIVOS IMPORTANTES:"
    echo "  • Configuración: $INSTALL_DIR/.env"
    echo "  • Logs: /var/log/silhouettemcp/"
    echo "  • Datos: $INSTALL_DIR/data"
    echo "  • Backups: $BACKUP_DIR"
    echo
    
    log_info "🔧 PRÓXIMOS PASOS:"
    echo "  1. Configurar variables de entorno en $INSTALL_DIR/.env"
    echo "  2. Configurar API keys externas si es necesario"
    echo "  3. Configurar SSL para producción (recomendado)"
    echo "  4. Revisar documentación en docs/"
    echo
    
    if [ "$CONFIGURE_SSL" = true ]; then
        log_warning "⚠️  SSL configurado básicamente. Configura certificados apropiados."
    fi
    
    log_success "📚 DOCUMENTACIÓN COMPLETA:"
    echo "  • README_ACTUALIZACION.md - Guía de actualización"
    echo "  • API_ENDPOINTS.md - Documentación de API"
    echo "  • GUIA_USUARIO.md - Manual de usuario"
    echo "  • CHANGELOG.md - Lista de cambios"
}

# Función para rollback en caso de error
rollback_deployment() {
    log_error "Iniciando rollback debido a error..."
    
    # Detener servicios
    if [ "$INSTALL_MODE" = "docker" ]; then
        cd "$INSTALL_DIR"
        docker-compose down 2>/dev/null || true
    else
        systemctl stop silhouettemcp 2>/dev/null || true
        systemctl stop nginx 2>/dev/null || true
    fi
    
    # Restaurar backup si existe
    if [ -d "$BACKUP_DIR" ] && [ "$(ls -A "$BACKUP_DIR")" ]; then
        local latest_backup=$(find "$BACKUP_DIR" -name "*backup*.tar.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
        
        if [ -n "$latest_backup" ]; then
            log_info "Restaurando backup: $latest_backup"
            cd "$BACKUP_DIR"
            tar -xzf "$(basename "$latest_backup")" 2>/dev/null || true
        fi
    fi
    
    # Limpiar instalación parcialmente creada
    if [ -d "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR"/*
    fi
    
    log_success "Rollback completado"
}

# Función principal
main() {
    # Mostrar banner
    show_banner
    
    # Crear log
    mkdir -p "$(dirname "$DEPLOY_LOG")"
    
    # Verificaciones iniciales
    if [ "$EUID" -ne 0 ]; then
        log_error "Este script debe ejecutarse como root"
        echo "Ejecuta: sudo $0"
        exit 1
    fi
    
    parse_arguments "$@"
    check_operating_system
    check_system_requirements
    
    # Proceso de instalación
    update_system
    install_base_dependencies
    install_python39
    install_docker
    configure_firewall
    configure_fail2ban
    create_directory_structure
    install_application
    setup_virtual_environment
    setup_environment
    setup_systemd_service
    setup_nginx
    setup_ssl
    setup_system_user
    setup_cron_jobs
    setup_logrotate
    setup_docker
    start_services
    
    # Verificación final
    if run_verification_tests; then
        show_post_install_info
        log_success "🎉 Despliegue completado exitosamente"
        exit 0
    else
        log_error "❌ Error durante la verificación"
        rollback_deployment
        exit 1
    fi
}

# Manejo de señales
cleanup() {
    log_error "Proceso interrumpido por señal"
    rollback_deployment
    exit 1
}

trap cleanup INT TERM

# Ejecutar función principal
main "$@"
