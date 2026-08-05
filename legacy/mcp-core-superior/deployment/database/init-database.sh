#!/bin/bash

# Script de inicialización de base de datos para MCP Core Superior
# Ejecuta migraciones y configuración inicial

set -e

# Configuración
POSTGRES_USER=${POSTGRES_USER:-mcpuser}
POSTGRES_DB=${POSTGRES_DB:-mcp_core}
POSTGRES_HOST=${POSTGRES_HOST:-postgres}
POSTGRES_PORT=${POSTGRES_PORT:-5432}

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Función para esperar a que PostgreSQL esté listo
wait_for_postgres() {
    log "Esperando a que PostgreSQL esté listo..."
    
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" &> /dev/null; then
            log_success "PostgreSQL está listo"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log "Intento $attempt/$max_attempts - esperando PostgreSQL..."
        sleep 2
    done
    
    log_error "PostgreSQL no está disponible después de $max_attempts intentos"
    return 1
}

# Función para crear extensiones necesarias
create_extensions() {
    log "Creando extensiones de PostgreSQL..."
    
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" << 'EOF'
-- Extensiones básicas
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Configuración para el vector database (pgvector)
CREATE EXTENSION IF NOT EXISTS vector;

-- Configuración adicional para optimizar performance
SET shared_preload_libraries = 'pg_stat_statements';
SET pg_stat_statements.track = 'all';
SET max_connections = 200;
SET shared_buffers = '256MB';
SET effective_cache_size = '1GB';
SET work_mem = '4MB';
SET maintenance_work_mem = '64MB';
SET checkpoint_completion_target = 0.9;
SET wal_buffers = '16MB';
SET default_statistics_target = 100;
SET random_page_cost = 1.1;
SET effective_io_concurrency = 200;

-- Configuración específica para pgvector
SET vector.index = 'ivfflat';
SET vector.ivfflat.probes = 10;

COMMIT;
EOF
    
    log_success "Extensiones creadas"
}

# Función para crear schemas
create_schemas() {
    log "Creando schemas de la base de datos..."
    
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" << 'EOF'
-- Crear schemas organizacionales
CREATE SCHEMA IF NOT EXISTS mcp_core;
CREATE SCHEMA IF NOT EXISTS agents;
CREATE SCHEMA IF NOT EXISTS monitoring;
CREATE SCHEMA IF NOT EXISTS security;
CREATE SCHEMA IF NOT EXISTS tasks;
CREATE SCHEMA IF NOT EXISTS context;

-- Configurar búsqueda de path
ALTER DATABASE mcp_core SET search_path TO mcp_core, agents, monitoring, security, tasks, context, public;

COMMIT;
EOF
    
    log_success "Schemas creados"
}

# Función para crear tablas principales
create_main_tables() {
    log "Creando tablas principales..."
    
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" << 'EOF'
-- Tablas principales de MCP Core
CREATE TABLE IF NOT EXISTS mcp_core.applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    version VARCHAR(100) NOT NULL,
    description TEXT,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS mcp_core.agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    type VARCHAR(100) NOT NULL,
    description TEXT,
    config JSONB DEFAULT '{}',
    capabilities TEXT[],
    status VARCHAR(50) DEFAULT 'idle',
    last_heartbeat TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS mcp_core.tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID REFERENCES mcp_core.applications(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES mcp_core.agents(id) ON DELETE SET NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    timeout_seconds INTEGER DEFAULT 300,
    retry_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS agents.executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES mcp_core.tasks(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES mcp_core.agents(id) ON DELETE SET NULL,
    command TEXT NOT NULL,
    arguments JSONB DEFAULT '[]',
    environment JSONB DEFAULT '{}',
    working_directory VARCHAR(500),
    status VARCHAR(50) DEFAULT 'running',
    exit_code INTEGER,
    stdout TEXT,
    stderr TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    timeout_seconds INTEGER DEFAULT 300,
    memory_limit_mb INTEGER,
    cpu_limit_percent DECIMAL(5,2),
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS context.sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID REFERENCES mcp_core.applications(id) ON DELETE CASCADE,
    user_id VARCHAR(255),
    session_token VARCHAR(500) UNIQUE,
    context_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS context.messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES context.sessions(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS security.audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(500),
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    severity VARCHAR(20) DEFAULT 'info'
);

CREATE TABLE IF NOT EXISTS monitoring.health_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(100) NOT NULL,
    check_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'healthy', 'unhealthy', 'unknown'
    response_time_ms INTEGER,
    error_message TEXT,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS mcp_core.file_uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    original_filename VARCHAR(500) NOT NULL,
    stored_filename VARCHAR(500) NOT NULL UNIQUE,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(200),
    uploaded_by VARCHAR(255),
    application_id UUID REFERENCES mcp_core.applications(id) ON DELETE SET NULL,
    task_id UUID REFERENCES mcp_core.tasks(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

COMMIT;
EOF
    
    log_success "Tablas principales creadas"
}

# Función para crear índices
create_indexes() {
    log "Creando índices para optimizar performance..."
    
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" << 'EOF'
-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_tasks_status ON mcp_core.tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON mcp_core.tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_application_id ON mcp_core.tasks(application_id);
CREATE INDEX IF NOT EXISTS idx_tasks_agent_id ON mcp_core.tasks(agent_id);

CREATE INDEX IF NOT EXISTS idx_agents_status ON mcp_core.agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_type ON mcp_core.agents(type);
CREATE INDEX IF NOT EXISTS idx_agents_active ON mcp_core.agents(is_active);

CREATE INDEX IF NOT EXISTS idx_executions_task_id ON agents.executions(task_id);
CREATE INDEX IF NOT EXISTS idx_executions_status ON agents.executions(status);
CREATE INDEX IF NOT EXISTS idx_executions_started_at ON agents.executions(started_at DESC);

CREATE INDEX IF NOT EXISTS idx_sessions_token ON context.sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_application_id ON context.sessions(application_id);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON context.sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON context.sessions(expires_at);

CREATE INDEX IF NOT EXISTS idx_messages_session_id ON context.messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON context.messages(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON security.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON security.audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON security.audit_logs(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_health_checks_service ON monitoring.health_checks(service_name);
CREATE INDEX IF NOT EXISTS idx_health_checks_status ON monitoring.health_checks(status);
CREATE INDEX IF NOT EXISTS idx_health_checks_checked_at ON monitoring.health_checks(checked_at DESC);

CREATE INDEX IF NOT EXISTS idx_file_uploads_application_id ON mcp_core.file_uploads(application_id);
CREATE INDEX IF NOT EXISTS idx_file_uploads_task_id ON mcp_core.file_uploads(task_id);
CREATE INDEX IF NOT EXISTS idx_file_uploads_created_at ON mcp_core.file_uploads(created_at DESC);

-- Índices GIN para búsquedas JSON
CREATE INDEX IF NOT EXISTS idx_tasks_input_gin ON mcp_core.tasks USING GIN (input_data);
CREATE INDEX IF NOT EXISTS idx_tasks_output_gin ON mcp_core.tasks USING GIN (output_data);
CREATE INDEX IF NOT EXISTS idx_tasks_metadata_gin ON mcp_core.tasks USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_agents_config_gin ON mcp_core.agents USING GIN (config);
CREATE INDEX IF NOT EXISTS idx_context_data_gin ON context.sessions USING GIN (context_data);

COMMIT;
EOF
    
    log_success "Índices creados"
}

# Función para insertar datos iniciales
insert_initial_data() {
    log "Insertando datos iniciales..."
    
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" << 'EOF'
-- Insertar aplicación principal
INSERT INTO mcp_core.applications (name, version, description, config) VALUES 
('MCP Core Superior', '1.0.0', 'Sistema principal de MCP Core Superior', 
 '{"features": ["agents", "tasks", "context", "monitoring"], "max_concurrent_tasks": 50}')
ON CONFLICT (name) DO NOTHING;

-- Insertar agentes del sistema
INSERT INTO mcp_core.agents (name, type, description, capabilities) VALUES 
('Python Executor Agent', 'executor', 'Ejecuta código Python en entorno aislado', 
 ARRAY['code_execution', 'python', 'scripting']),
('Database Operations Agent', 'database', 'Operaciones de base de datos optimizadas', 
 ARRAY['database', 'crud', 'sql', 'migrations']),
('Git Operations Agent', 'git', 'Operaciones con repositorios Git', 
 ARRAY['git', 'version_control', 'branching', 'merging']),
('Web Scraping Agent', 'scraping', 'Extracción de datos web', 
 ARRAY['scraping', 'parsing', 'extraction']),
('File Processing Agent', 'file', 'Procesamiento de archivos', 
 ARRAY['file_processing', 'validation', 'conversion']),
('Intelligent Router', 'router', 'Enrutamiento inteligente de tareas', 
 ARRAY['routing', 'load_balancing', 'optimization'])
ON CONFLICT (name) DO NOTHING;

-- Crear función para cleanup automático
CREATE OR REPLACE FUNCTION cleanup_expired_data()
RETURNS void AS $$
BEGIN
    -- Limpiar sesiones expiradas
    DELETE FROM context.sessions 
    WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '1 day';
    
    -- Limpiar logs de auditoría antiguos
    DELETE FROM security.audit_logs 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
    
    -- Limpiar health checks antiguos
    DELETE FROM monitoring.health_checks 
    WHERE checked_at < CURRENT_TIMESTAMP - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

COMMIT;
EOF
    
    log_success "Datos iniciales insertados"
}

# Función principal de inicialización
init_database() {
    log "Iniciando inicialización de base de datos para MCP Core Superior"
    
    # Verificar variables de entorno
    if [ -z "$POSTGRES_PASSWORD" ]; then
        log_error "POSTGRES_PASSWORD no está configurado"
        exit 1
    fi
    
    # Esperar a que PostgreSQL esté listo
    wait_for_postgres || exit 1
    
    # Ejecutar pasos de inicialización
    create_extensions
    create_schemas
    create_main_tables
    create_indexes
    insert_initial_data
    
    log_success "Inicialización de base de datos completada exitosamente"
}

# Función para cleanup
cleanup_database() {
    log "Ejecutando cleanup de base de datos..."
    
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT cleanup_expired_data();"
    
    log_success "Cleanup completado"
}

# Función de backup
backup_database() {
    local backup_file=${1:-"backup_$(date +%Y%m%d_%H%M%S).sql"}
    
    log "Creando backup de base de datos: $backup_file"
    
    PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "$backup_file"
    
    log_success "Backup creado: $backup_file"
}

# Función para mostrar ayuda
show_help() {
    echo "Script de inicialización de base de datos para MCP Core Superior"
    echo
    echo "Uso: $0 [COMANDO]"
    echo
    echo "Comandos:"
    echo "  init        Inicializar base de datos completa"
    echo "  cleanup     Ejecutar cleanup de datos expirados"
    echo "  backup      Crear backup de la base de datos"
    echo "  help        Mostrar esta ayuda"
    echo
    echo "Variables de entorno:"
    echo "  POSTGRES_USER     Usuario de PostgreSQL (default: mcpuser)"
    echo "  POSTGRES_DB       Base de datos (default: mcp_core)"
    echo "  POSTGRES_HOST     Host de PostgreSQL (default: postgres)"
    echo "  POSTGRES_PORT     Puerto de PostgreSQL (default: 5432)"
    echo "  POSTGRES_PASSWORD Contraseña de PostgreSQL (requerido)"
}

# Función principal
main() {
    case "${1:-help}" in
        init)
            init_database
            ;;
        cleanup)
            cleanup_database
            ;;
        backup)
            backup_database "${2:-backup_$(date +%Y%m%d_%H%M%S).sql}"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Comando desconocido: $1"
            show_help
            exit 1
            ;;
    esac
}

# Verificar argumentos
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

# Ejecutar función principal
main "$@"