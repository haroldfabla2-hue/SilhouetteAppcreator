#!/bin/bash

# Script de configuración completa del entorno
# Sistema de Agentes con PostgreSQL, Redis, FastAPI y React

set -e  # Salir en caso de error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Función para mostrar mensajes con colores
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo -e "${PURPLE}===============================================================${NC}"
    echo -e "${WHITE}$1${NC}"
    print_message "$PURPLE" "===============================================================
"
}

print_success() {
    print_message "$GREEN" "✅ $1"
}

print_warning() {
    print_message "$YELLOW" "⚠️  $1"
}

print_error() {
    print_message "$RED" "❌ $1"
}

print_info() {
    print_message "$BLUE" "ℹ️  $1"
}

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Función para verificar si Docker está corriendo
docker_is_running() {
    docker info >/dev/null 2>&1
}

# Función para crear archivo .env si no existe
create_env_file() {
    local env_file=".env"
    
    if [ ! -f "$env_file" ]; then
        print_info "Creando archivo .env..."
        cat > "$env_file" << 'EOF'
# Configuración de la aplicación
DEBUG=True
ENVIRONMENT=development

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agente_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_secure_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# APIs Externas (opcional)
MINIMAX_API_KEY=
OPENROUTER_API_KEY=

# URLs de servicios
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3001
EOF
        print_success "Archivo .env creado con configuración por defecto"
        print_warning "Por favor edita el archivo .env con tus API keys reales"
    else
        print_info "Archivo .env ya existe"
    fi
}

# Función para verificar dependencias
check_dependencies() {
    print_header "VERIFICANDO DEPENDENCIAS"
    
    local missing_deps=0
    
    # Verificar Docker
    if command_exists docker; then
        if docker_is_running; then
            print_success "Docker está instalado y ejecutándose"
        else
            print_error "Docker está instalado pero no se está ejecutando"
            missing_deps=$((missing_deps + 1))
        fi
    else
        print_error "Docker no está instalado"
        print_info "Por favor instala Docker desde https://docker.com"
        missing_deps=$((missing_deps + 1))
    fi
    
    # Verificar Docker Compose
    if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
        print_success "Docker Compose está disponible"
    else
        print_error "Docker Compose no está disponible"
        missing_deps=$((missing_deps + 1))
    fi
    
    # Verificar Python (opcional para desarrollo local)
    if command_exists python3; then
        print_success "Python3 está disponible"
    else
        print_warning "Python3 no está instalado (opcional para desarrollo local)"
    fi
    
    # Verificar Node.js (opcional para desarrollo local)
    if command_exists node; then
        print_success "Node.js está disponible"
    else
        print_warning "Node.js no está instalado (opcional para desarrollo local)"
    fi
    
    if [ $missing_deps -gt 0 ]; then
        print_error "Dependencias faltantes detectadas. Instala las herramientas necesarias."
        exit 1
    fi
}

# Función para crear directorios necesarios
create_directories() {
    print_header "CREANDO DIRECTORIOS"
    
    local dirs=(
        "backend/logs"
        "backend/database/scripts"
        "infrastructure/postgres"
        "infrastructure/redis"
        "infrastructure/prometheus"
        "infrastructure/grafana/dashboards"
        "data/postgres"
        "data/redis"
        "data/prometheus"
        "data/grafana"
    )
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_success "Creado directorio: $dir"
        else
            print_info "Directorio ya existe: $dir"
        fi
    done
}

# Función para configurar PostgreSQL
setup_postgresql() {
    print_header "CONFIGURANDO POSTGRESQL"
    
    # Verificar si el contenedor de PostgreSQL ya está corriendo
    if docker ps --format 'table {{.Names}}' | grep -q "agente_postgres"; then
        print_info "Contenedor PostgreSQL ya está ejecutándose"
    else
        print_info "Iniciando PostgreSQL con pgvector..."
        
        # Crear archivo de inicialización si no existe
        if [ ! -f "infrastructure/postgres/init.sql" ]; then
            print_info "Creando script de inicialización de PostgreSQL..."
            cat > "infrastructure/postgres/init.sql" << 'EOF'
-- Inicialización de base de datos PostgreSQL con pgvector
-- Habilitar extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Crear tablas para el sistema de agentes
CREATE TABLE IF NOT EXISTS source_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    metadata JSONB,
    hash TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id UUID REFERENCES source_documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(768),
    metadata JSONB,
    chunk_index INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chunk_collections (
    chunk_id UUID REFERENCES document_chunks(id) ON DELETE CASCADE,
    collection_id UUID REFERENCES collections(id) ON DELETE CASCADE,
    PRIMARY KEY (chunk_id, collection_id)
);

CREATE TABLE IF NOT EXISTS agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id TEXT UNIQUE NOT NULL,
    user_id TEXT,
    status TEXT DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS state_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    state JSONB NOT NULL,
    checksum TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Crear índices
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
ON document_chunks USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_agent_sessions_conversation_id ON agent_sessions(conversation_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_user_id ON agent_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_state_snapshots_conversation_id ON state_snapshots(conversation_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_doc_id ON document_chunks(doc_id);

-- Función para actualizar timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers
CREATE TRIGGER update_source_documents_updated_at 
BEFORE UPDATE ON source_documents
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_sessions_updated_at 
BEFORE UPDATE ON agent_sessions
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insertar datos por defecto
INSERT INTO collections (name, description, metadata) 
VALUES (
    'default',
    'Colección por defecto para conocimiento general',
    '{"type": "default", "auto_created": true}'
) ON CONFLICT (name) DO NOTHING;

DO $$
BEGIN
    RAISE NOTICE 'Base de datos inicializada correctamente con pgvector';
END $$;
EOF
        fi
    fi
}

# Función para configurar Redis
setup_redis() {
    print_header "CONFIGURANDO REDIS"
    
    # Crear configuración de Redis si no existe
    if [ ! -f "infrastructure/redis/redis.conf" ]; then
        print_info "Creando configuración de Redis..."
        cat > "infrastructure/redis/redis.conf" << 'EOF'
# Configuración básica de Redis
bind 0.0.0.0
port 6379
timeout 300
tcp-keepalive 300

# Persistencia
save 900 1
save 300 10
save 60 10000

# Memoria
maxmemory 256mb
maxmemory-policy allkeys-lru

# Log
loglevel notice
logfile ""

# Seguridad
# requirepass tu_password_aqui

# Performance
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
EOF
        print_success "Configuración de Redis creada"
    else
        print_info "Configuración de Redis ya existe"
    fi
}

# Función para configurar Prometheus
setup_prometheus() {
    print_header "CONFIGURANDO PROMETHEUS"
    
    if [ ! -f "infrastructure/prometheus/prometheus.yml" ]; then
        print_info "Creando configuración de Prometheus..."
        cat > "infrastructure/prometheus/prometheus.yml" << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
EOF
        print_success "Configuración de Prometheus creada"
    else
        print_info "Configuración de Prometheus ya existe"
    fi
}

# Función para configurar Grafana
setup_grafana() {
    print_header "CONFIGURANDO GRAFANA"
    
    # Crear datasource
    mkdir -p infrastructure/grafana/datasources
    if [ ! -f "infrastructure/grafana/datasources/prometheus.yml" ]; then
        cat > "infrastructure/grafana/datasources/prometheus.yml" << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF
    fi
    
    # Crear dashboard básico
    mkdir -p infrastructure/grafana/dashboards
    print_success "Configuración de Grafana creada"
}

# Función para instalar dependencias de Python
setup_python_dependencies() {
    print_header "CONFIGURANDO DEPENDENCIAS PYTHON"
    
    if [ -f "backend/requirements.txt" ]; then
        print_info "Instalando dependencias de Python..."
        
        if command_exists pip3; then
            pip3 install -r backend/requirements.txt
            print_success "Dependencias de Python instaladas"
        elif command_exists python3 -m pip; then
            python3 -m pip install -r backend/requirements.txt
            print_success "Dependencias de Python instaladas"
        else
            print_warning "pip no encontrado. Instala las dependencias manualmente."
        fi
    else
        print_warning "requirements.txt no encontrado en backend/"
    fi
}

# Función para construir y levantar servicios
start_services() {
    print_header "INICIANDO SERVICIOS"
    
    print_info "Construyendo e iniciando contenedores..."
    
    # Construir y levantar servicios
    if command_exists docker-compose; then
        docker-compose up -d --build
    else
        docker compose up -d --build
    fi
    
    print_info "Esperando a que los servicios estén listos..."
    sleep 10
    
    # Verificar que los servicios estén corriendo
    print_info "Verificando estado de los servicios..."
    
    local services=("agente_postgres" "agente_redis" "agente_backend" "agente_frontend" "agente_prometheus" "agente_grafana")
    
    for service in "${services[@]}"; do
        if docker ps --format 'table {{.Names}}' | grep -q "$service"; then
            print_success "$service está ejecutándose"
        else
            print_warning "$service no está ejecutándose"
        fi
    done
}

# Función para inicializar la base de datos
initialize_database() {
    print_header "INICIALIZANDO BASE DE DATOS"
    
    print_info "Ejecutando script de inicialización de base de datos..."
    
    if [ -f "backend/database/init_db.py" ]; then
        if command_exists python3; then
            python3 backend/database/init_db.py
            print_success "Base de datos inicializada"
        else
            print_warning "Python3 no encontrado. Ejecuta manualmente: python3 backend/database/init_db.py"
        fi
    else
        print_warning "Script de inicialización no encontrado"
    fi
}

# Función para verificar conexiones
test_connections() {
    print_header "PROBANDO CONEXIONES"
    
    print_info "Ejecutando pruebas de conectividad..."
    
    if [ -f "backend/database/test_connection.py" ]; then
        if command_exists python3; then
            python3 backend/database/test_connection.py full
            print_success "Pruebas de conectividad completadas"
        else
            print_warning "Python3 no encontrado. Ejecuta manualmente: python3 backend/database/test_connection.py full"
        fi
    else
        print_warning "Script de pruebas no encontrado"
    fi
}

# Función para mostrar información de acceso
show_access_info() {
    print_header "INFORMACIÓN DE ACCESO"
    
    print_success "Sistema configurado y funcionando!"
    echo
    echo -e "${CYAN}🌐 SERVICIOS DISPONIBLES:${NC}"
    echo -e "${WHITE}├── Frontend (React):${NC}     http://localhost:3000"
    echo -e "${WHITE}├── Backend API (FastAPI):${NC} http://localhost:8000"
    echo -e "${WHITE}├── PostgreSQL:${NC}           localhost:5432"
    echo -e "${WHITE}├── Redis:${NC}                localhost:6379"
    echo -e "${WHITE}├── Prometheus:${NC}           http://localhost:9090"
    echo -e "${WHITE}└── Grafana:${NC}              http://localhost:3001"
    echo
    echo -e "${CYAN}📝 CREDENCIALES:${NC}"
    echo -e "${WHITE}├── Grafana: admin / admin"
    echo -e "${WHITE}└── PostgreSQL: postgres / postgres_secure_password"
    echo
    echo -e "${CYAN}🔧 COMANDOS ÚTILES:${NC}"
    echo -e "${WHITE}├── Ver logs:${NC}            docker-compose logs -f [servicio]"
    echo -e "${WHITE}├── Reiniciar servicio:${NC}  docker-compose restart [servicio]"
    echo -e "${WHITE}├── Parar sistema:${NC}       docker-compose down"
    echo -e "${WHITE}└── Probar conexiones:${NC}   python3 backend/database/test_connection.py"
    echo
}

# Función de ayuda
show_help() {
    echo "Script de configuración del Sistema de Agentes"
    echo
    echo "Uso: $0 [opción]"
    echo
    echo "Opciones:"
    echo "  setup          Configuración completa del entorno"
    echo "  deps           Solo verificar dependencias"
    echo "  services       Solo iniciar servicios"
    echo "  init-db        Solo inicializar base de datos"
    echo "  test           Solo probar conexiones"
    echo "  info           Mostrar información de acceso"
    echo "  help           Mostrar esta ayuda"
    echo
    echo "Ejemplo: $0 setup"
}

# Función principal
main() {
    local command=${1:-setup}
    
    case $command in
        setup)
            print_header "CONFIGURACIÓN COMPLETA DEL SISTEMA"
            check_dependencies
            create_env_file
            create_directories
            setup_postgresql
            setup_redis
            setup_prometheus
            setup_grafana
            setup_python_dependencies
            start_services
            initialize_database
            test_connections
            show_access_info
            ;;
        deps)
            check_dependencies
            ;;
        services)
            start_services
            ;;
        init-db)
            initialize_database
            ;;
        test)
            test_connections
            ;;
        info)
            show_access_info
            ;;
        help)
            show_help
            ;;
        *)
            print_error "Comando desconocido: $command"
            show_help
            exit 1
            ;;
    esac
}

# Manejar señales
trap 'print_warning "\n⏹️ Configuración cancelada por el usuario"; exit 1' INT

# Ejecutar función principal
main "$@"