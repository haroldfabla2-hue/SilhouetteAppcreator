#!/bin/bash

# =========================================================
# SCRIPT DE ACTUALIZACIÓN AUTOMÁTICA
# SilhouetteMCP Server - FINAL UNIFIED v4.0.0
# =========================================================

set -e  # Exit on any error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Variables de configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="/opt/silhouettemcp_v4_unified"
BACKUP_DIR="/var/backups/silhouettemcp"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
UPDATE_LOG="/var/log/silhouettemcp/update_${TIMESTAMP}.log"

# Función para logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$UPDATE_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$UPDATE_LOG"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$UPDATE_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$UPDATE_LOG"
}

log_info() {
    echo -e "${PURPLE}[INFO]${NC} $1" | tee -a "$UPDATE_LOG"
}

# Función para mostrar banner
show_banner() {
    echo "=========================================="
    echo "🚀 SILHOUETTEMCP UPDATE SCRIPT v4.0.0"
    echo "=========================================="
    echo "Actualización a versión FINAL UNIFIED"
    echo "De 3 agentes → 51 herramientas"
    echo "=========================================="
}

# Función para verificar permisos
check_permissions() {
    log_info "Verificando permisos..."
    
    if [ "$EUID" -ne 0 ]; then
        log_error "Este script debe ejecutarse como root"
        echo "Ejecuta: sudo $0"
        exit 1
    fi
    
    log_success "Permisos verificados"
}

# Función para verificar dependencias del sistema
check_system_dependencies() {
    log_info "Verificando dependencias del sistema..."
    
    local missing_packages=()
    
    # Verificar Python 3.8+
    if ! python3 --version 2>/dev/null | grep -qE "Python 3\.[89]|3\.1[0-9]"; then
        missing_packages+=("python3.9")
    fi
    
    # Verificar pip
    if ! command -v pip3 &> /dev/null; then
        missing_packages+=("python3-pip")
    fi
    
    # Verificar nginx
    if ! command -v nginx &> /dev/null; then
        missing_packages+=("nginx")
    fi
    
    # Verificar systemctl
    if ! command -v systemctl &> /dev/null; then
        missing_packages+=("systemd")
    fi
    
    # Verificar curl
    if ! command -v curl &> /dev/null; then
        missing_packages+=("curl")
    fi
    
    if [ ${#missing_packages[@]} -ne 0 ]; then
        log_info "Instalando paquetes faltantes: ${missing_packages[*]}"
        apt-get update
        apt-get install -y ${missing_packages[*]}
    fi
    
    log_success "Dependencias del sistema verificadas"
}

# Función para crear backup pre-actualización
create_pre_update_backup() {
    log_info "Creando backup antes de la actualización..."
    
    if [ -f "$SCRIPT_DIR/backup.sh" ]; then
        bash "$SCRIPT_DIR/backup.sh"
        log_success "Backup pre-actualización completado"
    else
        log_warning "Script de backup no encontrado, creando backup manual..."
        
        # Backup básico manual
        if [ -d "$INSTALL_DIR" ]; then
            mkdir -p "$BACKUP_DIR"
            local manual_backup="${BACKUP_DIR}/manual_backup_${TIMESTAMP}"
            cp -r "$INSTALL_DIR" "$manual_backup"
            log_success "Backup manual creado: $manual_backup"
        fi
    fi
}

# Función para detener servicios existentes
stop_existing_services() {
    log_info "Deteniendo servicios existentes..."
    
    # Detener servicio actual si existe
    if systemctl list-unit-files | grep -q silhouettemcp.service; then
        log "Deteniendo servicio silhouettemcp..."
        systemctl stop silhouettemcp.service
        log_success "Servicio detenido"
    fi
    
    # Detener procesos Python relacionados
    local pids=$(pgrep -f "silhouettemcp" || true)
    if [ -n "$pids" ]; then
        log "Terminando procesos Python existentes..."
        pkill -f "silhouettemcp"
        sleep 3
        log_success "Procesos Python terminados"
    fi
    
    log_success "Servicios existentes detenidos"
}

# Función para instalar nueva versión
install_new_version() {
    log_info "Instalando nueva versión..."
    
    # Crear directorio de instalación
    mkdir -p "$INSTALL_DIR"
    
    # Copiar archivos del servidor
    log "Copiando archivos del servidor..."
    cp -r "$PROJECT_DIR/server/"* "$INSTALL_DIR/"
    
    # Crear directorios adicionales
    mkdir -p "$INSTALL_DIR/data"
    mkdir -p "$INSTALL_DIR/logs"
    mkdir -p "/var/log/silhouettemcp"
    mkdir -p "/var/backups/silhouettemcp"
    
    # Configurar permisos
    chown -R www-data:www-data "$INSTALL_DIR"
    chmod -R 755 "$INSTALL_DIR"
    chmod 644 "$INSTALL_DIR"/*.py
    chmod 644 "$INSTALL_DIR"/*.html
    chmod 644 "$INSTALL_DIR"/*.txt
    
    # Configurar logs
    chown -R www-data:www-data "/var/log/silhouettemcp"
    chmod 755 "/var/log/silhouettemcp"
    
    log_success "Archivos instalados"
}

# Función para configurar entorno virtual
setup_virtual_environment() {
    log_info "Configurando entorno virtual..."
    
    local venv_path="$INSTALL_DIR/venv"
    
    # Crear entorno virtual si no existe
    if [ ! -d "$venv_path" ]; then
        log "Creando entorno virtual..."
        python3 -m venv "$venv_path"
    fi
    
    # Activar entorno virtual e instalar dependencias
    log "Instalando dependencias de Python..."
    source "$venv_path/bin/activate"
    
    # Actualizar pip
    pip install --upgrade pip
    
    # Instalar dependencias
    if [ -f "$INSTALL_DIR/requirements.txt" ]; then
        pip install -r "$INSTALL_DIR/requirements.txt"
        log_success "Dependencias instaladas"
    else
        log_warning "Archivo requirements.txt no encontrado"
    fi
    
    # Desactivar entorno virtual
    deactivate
}

# Función para configurar variables de entorno
setup_environment_variables() {
    log_info "Configurando variables de entorno..."
    
    local env_file="$INSTALL_DIR/.env"
    
    if [ ! -f "$env_file" ]; then
        # Crear archivo .env desde el template
        if [ -f "$PROJECT_DIR/.env.example" ]; then
            cp "$PROJECT_DIR/.env.example" "$env_file"
            log_success "Archivo .env creado desde template"
            
            # Solicitar configuraciones importantes
            log_warning "Configura las siguientes variables en $env_file:"
            echo "  - SUPABASE_URL"
            echo "  - SUPABASE_SERVICE_ROLE_KEY"
            echo "  - SUPABASE_ANON_KEY"
            echo "  - SUPABASE_PROJECT_ID"
            echo "  - ADMIN_EMAIL"
            echo "  - ADMIN_PASSWORD_HASH"
        else
            log_warning "Template .env.example no encontrado"
        fi
    else
        log "Archivo .env ya existe, manteniendo configuración"
    fi
}

# Función para configurar servicio systemd
setup_systemd_service() {
    log_info "Configurando servicio systemd..."
    
    local service_file="/etc/systemd/system/silhouettemcp.service"
    local service_template="$PROJECT_DIR/config/silhouettemcp.service"
    
    if [ -f "$service_template" ]; then
        cp "$service_template" "$service_file"
        
        # Actualizar rutas en el archivo de servicio
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
    log_info "Configurando nginx..."
    
    local nginx_conf="/etc/nginx/sites-available/silhouettemcp"
    local nginx_template="$PROJECT_DIR/config/nginx.conf"
    
    if [ -f "$nginx_template" ]; then
        cp "$nginx_template" "$nginx_conf"
        
        # Habilitar sitio
        if [ ! -L "/etc/nginx/sites-enabled/silhouettemcp" ]; then
            ln -s "$nginx_conf" "/etc/nginx/sites-enabled/silhouettemcp"
        fi
        
        # Probar configuración
        if nginx -t; then
            log_success "Configuración de nginx válida"
        else
            log_error "Error en configuración de nginx"
        fi
    else
        log_warning "Template de nginx no encontrado"
    fi
}

# Función para configurar SSL
setup_ssl() {
    log_info "Configurando SSL..."
    
    # Verificar si existe configuración SSL
    if grep -q "ssl_certificate" /etc/nginx/sites-available/silhouettemcp 2>/dev/null; then
        log_success "Configuración SSL ya configurada"
        return
    fi
    
    log_warning "SSL no configurado. Para configurar SSL:"
    echo "1. Obtén certificados SSL (Let's Encrypt u otro proveedor)"
    echo "2. Actualiza rutas en /etc/nginx/sites-available/silhouettemcp"
    echo "3. Reinicia nginx: systemctl restart nginx"
}

# Función para crear usuario del sistema
create_system_user() {
    log_info "Creando usuario del sistema..."
    
    if ! id "silhouettemcp" &>/dev/null; then
        useradd -r -s /bin/false -d "$INSTALL_DIR" -M silhouettemcp
        log_success "Usuario 'silhouettemcp' creado"
    else
        log "Usuario 'silhouettemcp' ya existe"
    fi
    
    # Asignar permisos
    chown -R silhouettemcp:silhouettemcp "$INSTALL_DIR"
}

# Función para configurar firewall
setup_firewall() {
    log_info "Configurando firewall..."
    
    if command -v ufw &> /dev/null; then
        # Habilitar puertos necesarios
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw allow 8001/tcp  # Puerto interno
        
        log_success "Firewall configurado"
    else
        log_warning "UFW no disponible, configuración manual requerida"
    fi
}

# Función para iniciar servicios
start_services() {
    log_info "Iniciando servicios..."
    
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
    
    # Verificar estado de los servicios
    sleep 5
    
    if systemctl is-active --quiet silhouettemcp.service; then
        log_success "Servicio SilhouetteMCP funcionando"
    else
        log_error "Servicio SilhouetteMCP no está funcionando"
        return 1
    fi
}

# Función para verificar instalación
verify_installation() {
    log_info "Verificando instalación..."
    
    local success=true
    
    # Verificar puerto 8001
    if netstat -tuln | grep -q ":8001 "; then
        log_success "Puerto 8001 en uso"
    else
        log_error "Puerto 8001 no está en uso"
        success=false
    fi
    
    # Verificar HTTP endpoint
    if curl -s http://localhost:8001/health >/dev/null 2>&1; then
        log_success "Endpoint /health respondiendo"
    else
        log_warning "Endpoint /health no responde (puede necesitar configuración)"
    fi
    
    # Verificar nginx
    if systemctl is-active --quiet nginx; then
        log_success "Nginx funcionando"
    else
        log_warning "Nginx no está funcionando"
    fi
    
    if [ "$success" = true ]; then
        log_success "✅ Instalación verificada exitosamente"
    else
        log_warning "⚠️  Instalación completada con advertencias"
    fi
    
    return $([ "$success" = true ] && echo 0 || echo 1)
}

# Función para mostrar información post-instalación
show_post_install_info() {
    log_success "=========================================="
    log_success "🚀 INSTALACIÓN COMPLETADA EXITOSAMENTE"
    log_success "=========================================="
    
    echo
    log_info "🌐 URLs importantes:"
    echo "  • Servidor local: http://localhost:8001"
    echo "  • Dashboard: http://localhost:8001/files/dashboard"
    echo "  • API docs: http://localhost:8001/docs"
    echo "  • Health check: http://localhost:8001/health"
    echo
    log_info "📊 Información del sistema:"
    echo "  • Agentes instalados: 6"
    echo "  • Total herramientas: 51"
    echo "  • Directorio: $INSTALL_DIR"
    echo "  • Logs: /var/log/silhouettemcp/"
    echo
    log_info "🔧 Comandos útiles:"
    echo "  • Ver estado: systemctl status silhouettemcp"
    echo "  • Ver logs: journalctl -u silhouettemcp -f"
    echo "  • Reiniciar: systemctl restart silhouettemcp"
    echo "  • Backup: bash $SCRIPT_DIR/backup.sh"
    echo
    log_warning "⚠️  Tareas pendientes:"
    echo "  • Configurar variables de entorno en $INSTALL_DIR/.env"
    echo "  • Configurar SSL (recomendado para producción)"
    echo "  • Configurar API keys externas si es necesario"
    echo
    log_info "📚 Documentación completa disponible en:"
    echo "  • README_ACTUALIZACION.md"
    echo "  • API_ENDPOINTS.md"
    echo "  • GUIA_USUARIO.md"
    echo
}

# Función para rollback en caso de error
rollback_installation() {
    log_error "Iniciando rollback debido a error..."
    
    # Restaurar backup si existe
    if [ -d "$BACKUP_DIR" ]; then
        local latest_backup=$(find "$BACKUP_DIR" -name "silhouettemcp_backup_*.tar.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
        
        if [ -n "$latest_backup" ]; then
            log_info "Restaurando backup: $latest_backup"
            cd "$BACKUP_DIR"
            tar -xzf "$latest_backup"
            
            # Restaurar archivos
            local backup_name=$(basename "$latest_backup" .tar.gz)
            if [ -d "$backup_name" ]; then
                cp -r "$backup_name"/* "$INSTALL_DIR/" 2>/dev/null || true
                log_success "Backup restaurado"
            fi
        fi
    fi
    
    # Reiniciar servicios
    systemctl daemon-reload
    systemctl restart silhouettemcp.service 2>/dev/null || true
    systemctl restart nginx 2>/dev/null || true
}

# Función principal
main() {
    # Mostrar banner
    show_banner
    
    # Verificaciones iniciales
    check_permissions
    check_system_dependencies
    
    # Crear backup
    create_pre_update_backup
    
    # Proceso de instalación
    stop_existing_services
    install_new_version
    setup_virtual_environment
    setup_environment_variables
    setup_systemd_service
    setup_nginx
    setup_ssl
    create_system_user
    setup_firewall
    start_services
    
    # Verificación final
    if verify_installation; then
        show_post_install_info
        log_success "🎉 Actualización completada exitosamente"
        exit 0
    else
        log_error "❌ Error durante la verificación"
        rollback_installation
        exit 1
    fi
}

# Manejo de señales para cleanup
cleanup() {
    log_error "Proceso interrumpido por señal"
    rollback_installation
    exit 1
}

trap cleanup INT TERM

# Ejecutar función principal
main "$@"
