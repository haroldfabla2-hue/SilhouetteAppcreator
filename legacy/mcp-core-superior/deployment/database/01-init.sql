-- Script de inicialización automática para MCP Core Superior
-- Este archivo se ejecuta cuando se crea el contenedor de PostgreSQL

-- Establecer zona horaria
SET timezone = 'UTC';

-- Crear extensiones necesarias
\echo 'Creando extensiones...'
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Configuración para vector database
\echo 'Creando extensión vector...'
CREATE EXTENSION IF NOT EXISTS vector;

-- Crear usuario para la aplicación si no existe
\echo 'Creando usuario de aplicación...'
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'mcpuser') THEN
        CREATE USER mcpuser WITH PASSWORD 'devpassword123';
    END IF;
END
$$;

-- Otorgar permisos
\echo 'Otorgando permisos...'
GRANT ALL PRIVILEGES ON DATABASE mcp_core TO mcpuser;
GRANT ALL PRIVILEGES ON SCHEMA public TO mcpuser;

-- Crear schemas
\echo 'Creando schemas...'
CREATE SCHEMA IF NOT EXISTS mcp_core AUTHORIZATION mcpuser;
CREATE SCHEMA IF NOT EXISTS agents AUTHORIZATION mcpuser;
CREATE SCHEMA IF NOT EXISTS monitoring AUTHORIZATION mcpuser;
CREATE SCHEMA IF NOT EXISTS security AUTHORIZATION mcpuser;
CREATE SCHEMA IF NOT EXISTS tasks AUTHORIZATION mcpuser;
CREATE SCHEMA IF NOT EXISTS context AUTHORIZATION mcpuser;

-- Otorgar permisos en schemas
\echo 'Otorgando permisos en schemas...'
GRANT ALL ON SCHEMA mcp_core TO mcpuser;
GRANT ALL ON SCHEMA agents TO mcpuser;
GRANT ALL ON SCHEMA monitoring TO mcpuser;
GRANT ALL ON SCHEMA security TO mcpuser;
GRANT ALL ON SCHEMA tasks TO mcpuser;
GRANT ALL ON SCHEMA context TO mcpuser;

-- Configuración de PostgreSQL para producción
\echo 'Configurando PostgreSQL...'
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET pg_stat_statements.track = 'all';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Configuración específica para pgvector
ALTER SYSTEM SET vector.index = 'ivfflat';
ALTER SYSTEM SET vector.ivfflat.probes = 10;

-- Seleccionar base de datos
\c mcp_core

-- Crear tablas principales
\echo 'Creando tablas principales...'

-- Tabla de aplicaciones
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

-- Tabla de agentes
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

-- Tabla de tareas
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

-- Tabla de ejecuciones
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

-- Tabla de sesiones de contexto
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

-- Tabla de mensajes de contexto
CREATE TABLE IF NOT EXISTS context.messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES context.sessions(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de logs de auditoría
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

-- Tabla de health checks
CREATE TABLE IF NOT EXISTS monitoring.health_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(100) NOT NULL,
    check_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    response_time_ms INTEGER,
    error_message TEXT,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Tabla de archivos subidos
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

-- Otorgar permisos en tablas
\echo 'Otorgando permisos en tablas...'
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA mcp_core TO mcpuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA agents TO mcpuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA monitoring TO mcpuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA security TO mcpuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA context TO mcpuser;

-- Crear índices para performance
\echo 'Creando índices...'

-- Índices básicos
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

-- Insertar datos iniciales
\echo 'Insertando datos iniciales...'

-- Aplicación principal
INSERT INTO mcp_core.applications (name, version, description, config) VALUES 
('MCP Core Superior', '1.0.0', 'Sistema principal de MCP Core Superior', 
 '{"features": ["agents", "tasks", "context", "monitoring"], "max_concurrent_tasks": 50}')
ON CONFLICT (name) DO NOTHING;

-- Agentes del sistema
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

-- Crear funciones útiles
\echo 'Creando funciones útiles...'

-- Función para cleanup automático
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

-- Función para actualizar timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para updated_at
CREATE TRIGGER update_applications_updated_at BEFORE UPDATE ON mcp_core.applications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON mcp_core.agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON mcp_core.tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON context.sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Configurar búsqueda de path
ALTER DATABASE mcp_core SET search_path TO mcp_core, agents, monitoring, security, tasks, context, public;

\echo 'Inicialización de base de datos completada exitosamente!'
\echo 'Schema: mcp_core'
\echo 'Usuario: mcpuser'
\echo 'Extensiones creadas: uuid-ossp, pg_stat_statements, pg_trgm, vector'

-- Mostrar tablas creadas
\dt mcp_core.*
\dt agents.*
\dt monitoring.*
\dt security.*
\dt tasks.*
\dt context.*