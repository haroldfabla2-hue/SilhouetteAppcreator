#!/bin/bash

# =========================================================
# SCRIPT DE BACKUP AUTOMÁTICO
# SilhouetteMCP Server - FINAL UNIFIED v4.0.0
# =========================================================

set -e  # Exit on any error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables de configuración
BACKUP_DIR="/var/backups/silhouettemcp"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="silhouettemcp_backup_${TIMESTAMP}"
INSTALL_DIR="/opt/silhouettemcp_v4_unified"
DATA_DIR="${INSTALL_DIR}/data"
LOG_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.log"

# Función para logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Función para verificar dependencias
check_dependencies() {
    log "Verificando dependencias..."
    
    local missing_deps=()
    
    if ! command -v tar &> /dev/null; then
        missing_deps+=("tar")
    fi
    
    if ! command -v systemctl &> /dev/null; then
        missing_deps+=("systemctl")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Dependencias faltantes: ${missing_deps[*]}"
        log "Instalando dependencias faltantes..."
        sudo apt-get update
        sudo apt-get install -y ${missing_deps[*]}
    fi
    
    log_success "Dependencias verificadas"
}

# Función para crear directorios de backup
setup_backup_dirs() {
    log "Configurando directorios de backup..."
    
    # Crear directorio principal de backup
    if [ ! -d "$BACKUP_DIR" ]; then
        sudo mkdir -p "$BACKUP_DIR"
        sudo chmod 755 "$BACKUP_DIR"
        log "Directorio de backup creado: $BACKUP_DIR"
    fi
    
    # Crear directorio temporal de backup
    local temp_backup_dir="${BACKUP_DIR}/${BACKUP_NAME}"
    mkdir -p "$temp_backup_dir"
    
    log_success "Directorios configurados"
    echo "$temp_backup_dir"
}

# Función para detener servicios
stop_services() {
    log "Deteniendo servicios SilhouetteMCP..."
    
    # Detener servicio systemd si existe
    if systemctl list-unit-files | grep -q silhouettemcp.service; then
        sudo systemctl stop silhouettemcp.service
        log_success "Servicio systemd detenido"
    fi
    
    # Detener proceso Python si está ejecutándose
    if pgrep -f "silhouettemcp_server_unified.py" > /dev/null; then
        pkill -f "silhouettemcp_server_unified.py"
        log_success "Proceso Python detenido"
    fi
    
    # Esperar un momento para que los servicios se detengan completamente
    sleep 5
    
    log_success "Servicios detenidos"
}

# Función para crear backup de archivos de aplicación
backup_application_files() {
    local temp_backup_dir="$1"
    log "Creando backup de archivos de aplicación..."
    
    local app_backup_dir="${temp_backup_dir}/application"
    mkdir -p "$app_backup_dir"
    
    # Backup del directorio de instalación si existe
    if [ -d "$INSTALL_DIR" ]; then
        log "Respaldando directorio de aplicación: $INSTALL_DIR"
        sudo cp -r "$INSTALL_DIR" "$app_backup_dir/"
        log_success "Archivos de aplicación respaldados"
    else
        log_warning "Directorio de aplicación no encontrado: $INSTALL_DIR"
    fi
    
    # Backup de configuración nginx si existe
    if [ -f "/etc/nginx/sites-available/silhouettemcp" ]; then
        log "Respaldando configuración nginx"
        sudo cp /etc/nginx/sites-available/silhouettemcp "$app_backup_dir/nginx.conf"
    fi
    
    # Backup de servicio systemd si existe
    if [ -f "/etc/systemd/system/silhouettemcp.service" ]; then
        log "Respaldando configuración de servicio systemd"
        sudo cp /etc/systemd/system/silhouettemcp.service "$app_backup_dir/silhouettemcp.service"
    fi
    
    # Backup de logs del sistema
    if [ -d "/var/log/silhouettemcp" ]; then
        log "Respaldando logs del sistema"
        mkdir -p "$app_backup_dir/logs"
        sudo cp -r /var/log/silhouettemcp/* "$app_backup_dir/logs/" 2>/dev/null || true
    fi
}

# Función para crear backup de base de datos
backup_database() {
    local temp_backup_dir="$1"
    log "Creando backup de base de datos..."
    
    local db_backup_dir="${temp_backup_dir}/database"
    mkdir -p "$db_backup_dir"
    
    # Backup de PostgreSQL si existe
    if command -v psql &> /dev/null && sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw silhouettemcp; then
        log "Respaldando base de datos PostgreSQL 'silhouettemcp'"
        sudo -u postgres pg_dump silhouettemcp > "${db_backup_dir}/silhouettemcp_backup.sql"
        log_success "Base de datos PostgreSQL respaldada"
    fi
    
    # Backup de archivos de datos en /opt/silhouettemcp_v4_unified/data
    if [ -d "$DATA_DIR" ]; then
        log "Respaldando archivos de datos locales"
        cp -r "$DATA_DIR" "${db_backup_dir}/local_data"
        log_success "Archivos de datos locales respaldados"
    fi
}

# Función para crear backup de configuraciones del sistema
backup_system_config() {
    local temp_backup_dir="$1"
    log "Creando backup de configuraciones del sistema..."
    
    local config_backup_dir="${temp_backup_dir}/system_config"
    mkdir -p "$config_backup_dir"
    
    # Backup de variables de entorno
    if [ -f "/opt/silhouettemcp_v4_unified/.env" ]; then
        log "Respaldando archivo .env"
        sudo cp /opt/silhouettemcp_v4_unified/.env "$config_backup_dir/.env.backup"
    fi
    
    # Backup de configuración SSL si existe
    if [ -d "/etc/ssl/silhouettemcp" ]; then
        log "Respaldando certificados SSL"
        sudo cp -r /etc/ssl/silhouettemcp "$config_backup_dir/ssl_certs"
    fi
    
    # Backup de crontabs si existen
    if crontab -l 2>/dev/null | grep -q silhouettemcp; then
        log "Respaldando crontab"
        crontab -l > "$config_backup_dir/crontab"
    fi
}

# Función para crear archivo de metadatos del backup
create_backup_metadata() {
    local temp_backup_dir="$1"
    log "Creando metadatos del backup..."
    
    local metadata_file="${temp_backup_dir}/backup_metadata.json"
    
    cat > "$metadata_file" << EOF
{
    "backup_name": "$BACKUP_NAME",
    "timestamp": "$(date -Iseconds)",
    "version": "4.0.0",
    "server_info": {
        "hostname": "$(hostname)",
        "os": "$(lsb_release -d 2>/dev/null | cut -f2 || uname -s)",
        "kernel": "$(uname -r)",
        "architecture": "$(uname -m)"
    },
    "installed_packages": {
        "python": "$(python3 --version 2>/dev/null || echo 'not found')",
        "nginx": "$(nginx -v 2>&1 || echo 'not installed')",
        "postgresql": "$(psql --version 2>/dev/null || echo 'not installed')"
    },
    "services": {
        "silhouettemcp_service": "$(systemctl list-unit-files | grep -q silhouettemcp.service && echo 'installed' || echo 'not installed')",
        "nginx_service": "$(systemctl list-unit-files | grep -q nginx.service && echo 'installed' || echo 'not installed')"
    },
    "network_ports": {
        "8001": "$(netstat -tuln | grep -q ':8001 ' && echo 'in_use' || echo 'free')"
    }
}
EOF
    
    log_success "Metadatos del backup creados"
}

# Función para comprimir backup
compress_backup() {
    local temp_backup_dir="$1"
    log "Comprimiendo backup..."
    
    local backup_file="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    
    cd "$BACKUP_DIR"
    tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
    
    # Verificar integridad del archivo comprimido
    if tar -tzf "${BACKUP_NAME}.tar.gz" > /dev/null 2>&1; then
        log_success "Backup comprimido exitosamente: $backup_file"
        # Limpiar directorio temporal
        rm -rf "$BACKUP_NAME"
        echo "$backup_file"
    else
        log_error "Error al comprimir backup"
        exit 1
    fi
}

# Función para limpiar backups antiguos
cleanup_old_backups() {
    log "Limpiando backups antiguos (manteniendo últimos 30 días)..."
    
    local retention_days=30
    local deleted_count=0
    
    find "$BACKUP_DIR" -name "silhouettemcp_backup_*.tar.gz" -type f -mtime +$retention_days -print0 | while IFS= read -r -d '' backup_file; do
        log "Eliminando backup antiguo: $(basename "$backup_file")"
        rm -f "$backup_file"
        ((deleted_count++))
    done
    
    if [ $deleted_count -gt 0 ]; then
        log_success "Se eliminaron $deleted_count backups antiguos"
    else
        log "No hay backups antiguos para eliminar"
    fi
}

# Función para mostrar resumen del backup
show_backup_summary() {
    local backup_file="$1"
    local file_size=$(du -h "$backup_file" | cut -f1)
    
    log_success "======================================"
    log_success "BACKUP COMPLETADO EXITOSAMENTE"
    log_success "======================================"
    log "Archivo: $backup_file"
    log "Tamaño: $file_size"
    log "Fecha: $(date)"
    log "Log: $LOG_FILE"
    log_success "======================================"
}

# Función para restaurar servicios
restore_services() {
    log "Restaurando servicios..."
    
    # Reiniciar daemon de systemd
    sudo systemctl daemon-reload
    
    # Habilitar servicio si existe
    if systemctl list-unit-files | grep -q silhouettemcp.service; then
        sudo systemctl enable silhouettemcp.service
        log_success "Servicio systemd habilitado"
    fi
    
    # Iniciar servicio si existe
    if systemctl list-unit-files | grep -q silhouettemcp.service; then
        sudo systemctl start silhouettemcp.service
        log_success "Servicio systemd iniciado"
    fi
    
    # Verificar estado del servicio
    if systemctl is-active --quiet silhouettemcp.service; then
        log_success "Servicio funcionando correctamente"
    else
        log_warning "Servicio no está funcionando correctamente"
    fi
}

# Función principal
main() {
    echo "======================================"
    echo "🔄 SILHOUETTEMCP BACKUP SCRIPT v4.0.0"
    echo "======================================"
    
    # Verificar si se ejecuta como root para backup completo
    if [ "$EUID" -ne 0 ]; then
        log_warning "Este script debe ejecutarse como root para un backup completo"
        log "Continuando con permisos de usuario (backup limitado)..."
    fi
    
    # Verificar dependencias
    check_dependencies
    
    # Configurar directorios
    temp_backup_dir=$(setup_backup_dirs)
    
    # Detener servicios
    stop_services
    
    # Crear backups
    backup_application_files "$temp_backup_dir"
    backup_database "$temp_backup_dir"
    backup_system_config "$temp_backup_dir"
    create_backup_metadata "$temp_backup_dir"
    
    # Comprimir backup
    backup_file=$(compress_backup "$temp_backup_dir")
    
    # Limpiar backups antiguos
    cleanup_old_backups
    
    # Restaurar servicios
    restore_services
    
    # Mostrar resumen
    show_backup_summary "$backup_file"
    
    log "✅ Proceso de backup completado"
}

# Manejo de señales
trap 'log_error "Backup interrumpido"; exit 1' INT TERM

# Ejecutar función principal
main "$@"
