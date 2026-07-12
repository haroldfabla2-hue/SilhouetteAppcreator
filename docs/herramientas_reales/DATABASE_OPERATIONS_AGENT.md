# 🗄️ Database Operations Agent - Guía Completa

## Descripción General

El **Database Operations Agent** es un agente especializado que proporciona capacidades avanzadas de gestión de bases de datos, operaciones CRUD, **RAG con PostgreSQL + pgvector**, y análisis de datos usando **herramientas reales** de base de datos. Es una herramienta **operacional real** que interactúa directamente con PostgreSQL, ejecuta SQL complejo, y maneja operaciones vectoriales.

**Estado**: ✅ **PRODUCCIÓN ACTIVA**  
**Tecnologías**: PostgreSQL, SQLAlchemy, asyncpg, pgvector  
**Capacidades**: CRUD operations, RAG vectorial, backup/restore, monitoring  
**Vector Dimensions**: 768 (OpenAI compatible)  
**Index Types**: HNSW, IVFFlat

## 🎯 Capacidades Principales

### Operaciones CRUD Avanzadas
- **Query Execution**: SQL complejo con optimización automática
- **Transaction Management**: ACID compliance con rollback automático
- **Connection Pooling**: Pool automático con métricas de performance
- **Bulk Operations**: Operaciones masivas optimizadas
- **Schema Management**: Creación y modificación de esquemas

### RAG (Retrieval-Augmented Generation)
- **Vector Embeddings**: Generación y almacenamiento de embeddings 768-dim
- **Vector Search**: Búsqueda semántica con pgvector
- **HNSW Indexing**: Índices de alto rendimiento para búsqueda rápida
- **Batch Operations**: Procesamiento de miles de documentos
- **Real-time Updates**: Actualización en tiempo real de vectores

### Monitoreo y Performance
- **Connection Monitoring**: Métricas de conexiones en tiempo real
- **Query Optimization**: Análisis y optimización automática de queries
- **Slow Query Detection**: Identificación de queries lentas
- **Index Analysis**: Recomendaciones de índices
- **Resource Monitoring**: CPU, memoria, disco por query

### Backup y Recovery
- **Automated Backups**: Backup automático programado
- **Point-in-time Recovery**: Recuperación hasta un punto específico
- **Cross-region Replication**: Replicación entre regiones
- **Incremental Backups**: Backups incrementales eficientes

## 🛠️ Instalación y Configuración

### Prerrequisitos del Sistema

```bash
# Instalar PostgreSQL 15+
sudo apt-get update
sudo apt-get install -y postgresql-15 postgresql-contrib-15

# Instalar extensión pgvector
sudo apt-get install -y postgresql-15-pgvector

# Verificar instalación
sudo -u postgres psql -c "SELECT version();"
```

### Configuración de PostgreSQL

```bash
# Crear usuario y base de datos
sudo -u postgres psql << EOF
CREATE USER multiagent WITH PASSWORD 'secure_password';
CREATE DATABASE multiagent_db OWNER multiagent;
GRANT ALL PRIVILEGES ON DATABASE multiagent_db TO multiagent;
EOF

# Habilitar pgvector
sudo -u postgres psql -d multiagent_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Variables de Entorno

```bash
# Configuración de base de datos
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=multiagent_db
export DB_USER=multiagent
export DB_PASSWORD=secure_password
export DB_SSL=require

# Pool de conexiones
export DB_POOL_SIZE=10
export DB_MAX_OVERFLOW=20
export DB_POOL_TIMEOUT=30
export DB_POOL_RECYCLE=3600

# Configuración RAG
export VECTOR_DIMENSIONS=768
export VECTOR_SIMILARITY=cosine
export HNSW_M=16
export HNSW_EF=200
```

### Configuración de la Base de Datos

```sql
-- Esquema principal
CREATE TABLE IF NOT EXISTS collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID REFERENCES collections(id),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    hash VARCHAR(64) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de chunks vectoriales
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id),
    collection_id UUID REFERENCES collections(id),
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding vector(768),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices vectoriales
CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw_idx 
ON document_chunks USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS documents_hash_idx ON documents(hash);
CREATE INDEX IF NOT EXISTS chunks_collection_idx ON document_chunks(collection_id);
```

## 📚 API Reference

### Operaciones Básicas de Base de Datos

#### 1. Ejecutar Query SQL

```http
POST /api/v1/tools/database
Content-Type: application/json

{
    "agent": "database_operations",
    "action": "execute_query",
    "query": "SELECT * FROM collections ORDER BY created_at DESC LIMIT 10",
    "params": {},
    "timeout": 30000,
    "explain": false,
    "output_format": "json"
}
```

**Respuesta:**
```json
{
    "status": "success",
    "data": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "knowledge_base",
            "description": "Base de conocimientos principal",
            "metadata": {"category": "technical"},
            "created_at": "2025-11-04T15:30:00Z"
        }
    ],
    "row_count": 1,
    "execution_time": 0.015,
    "query_plan": null
}
```

#### 2. Operaciones CRUD

```http
POST /api/v1/tools/database
Content-Type: application/json

{
    "agent": "database_operations",
    "action": "bulk_insert",
    "table": "collections",
    "data": [
        {
            "name": "research_papers",
            "description": "Papers de investigación",
            "metadata": {"domain": "ai", "language": "en"}
        },
        {
            "name": "technical_docs",
            "description": "Documentación técnica",
            "metadata": {"domain": "engineering", "language": "es"}
        }
    ],
    "on_conflict": "name",
    "return_data": true
}
```

#### 3. RAG: Búsqueda Vectorial

```http
POST /api/v1/tools/database
Content-Type: application/json

{
    "agent": "database_operations",
    "action": "vector_search",
    "query": "machine learning algorithms neural networks",
    "collection_name": "research_papers",
    "top_k": 10,
    "threshold": 0.7,
    "include_metadata": true,
    "include_embeddings": false,
    "similarity_metric": "cosine"
}
```

**Respuesta:**
```json
{
    "status": "success",
    "data": {
        "query": "machine learning algorithms neural networks",
        "results": [
            {
                "id": "chunk_123",
                "document_id": "doc_456",
                "content": "Neural networks are a fundamental component of modern machine learning...",
                "similarity": 0.89,
                "metadata": {
                    "source": "paper_001.pdf",
                    "page": 15,
                    "section": "3.2"
                },
                "document_metadata": {
                    "title": "Deep Learning Fundamentals",
                    "authors": ["Smith, J.", "Doe, A."],
                    "year": 2024
                }
            }
        ],
        "total_results": 1,
        "search_time": 0.032,
        "query_embedding": [0.123, 0.456, ...]
    }
}
```

#### 4. RAG: Almacenamiento de Documentos

```http
POST /api/v1/tools/database
Content-Type: application/json

{
    "agent": "database_operations",
    "action": "store_document_with_vectors",
    "collection_name": "technical_docs",
    "document": {
        "content": "Este es el contenido del documento que será procesado y vectorizado...",
        "metadata": {
            "title": "Guía de PostgreSQL",
            "author": "Equipo Técnico",
            "tags": ["database", "postgresql", "sql"]
        }
    },
    "chunking_config": {
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "separator": "\\n\\n"
    },
    "embedding_config": {
        "model": "text-embedding-ada-002",
        "dimensions": 768,
        "batch_size": 100
    }
}
```

#### 5. Gestión de Esquemas

```http
POST /api/v1/tools/database
Content-Type: application/json

{
    "agent": "database_operations",
    "action": "create_table_with_vectors",
    "table_name": "products_vector",
    "columns": [
        {
            "name": "id",
            "type": "UUID",
            "primary_key": true,
            "default": "gen_random_uuid()"
        },
        {
            "name": "name",
            "type": "VARCHAR(255)",
            "not_null": true
        },
        {
            "name": "description",
            "type": "TEXT"
        },
        {
            "name": "price",
            "type": "DECIMAL(10,2)"
        },
        {
            "name": "embedding",
            "type": "vector(768)",
            "not_null": false
        }
    ],
    "indexes": [
        {
            "name": "products_embedding_idx",
            "type": "hnsw",
            "columns": ["embedding"],
            "options": {"vector_cosine_ops": true}
        },
        {
            "name": "products_name_idx",
            "type": "btree",
            "columns": ["name"]
        }
    ],
    "constraints": [
        {
            "type": "check",
            "name": "price_positive",
            "condition": "price > 0"
        }
    ]
}
```

#### 6. Backup y Restore

```http
POST /api/v1/tools/database
Content-Type: application/json

{
    "agent": "database_operations",
    "action": "create_backup",
    "backup_type": "full", // full, incremental, selective
    "tables": ["collections", "documents", "document_chunks"],
    "compression": true,
    "encryption": true,
    "backup_path": "/backups/db_backup_2025_11_04.sql",
    "include_data": true,
    "include_schema": true
}
```

## 💻 Ejemplos de Uso

### Ejemplo 1: Sistema RAG Completo

```python
import requests
import json

# Configuración
base_url = "http://localhost:8000/api/v1/tools/database"
headers = {"Content-Type": "application/json"}

# Paso 1: Crear colección
create_collection = requests.post(base_url, headers=headers, json={
    "agent": "database_operations",
    "action": "create_collection",
    "name": "empresa_knowledge_base",
    "description": "Base de conocimientos de la empresa",
    "metadata": {
        "domain": "business",
        "language": "es",
        "priority": "high"
    }
})

print("Colección creada:", create_collection.json())

# Paso 2: Almacenar documento con vectors
store_doc = requests.post(base_url, headers=headers, json={
    "agent": "database_operations",
    "action": "store_document_with_vectors",
    "collection_name": "empresa_knowledge_base",
    "document": {
        "content": """
        Manual de políticas de seguridad de la empresa:
        
        1. Autenticación: Todos los empleados deben usar autenticación de dos factores.
        2. Contraseñas: Mínimo 12 caracteres con mayúsculas, minúsculas, números y símbolos.
        3. Acceso a datos: Solo personal autorizado puede acceder a datos sensibles.
        4. Backup: Los datos deben respaldarse diariamente.
        5. Incidentes: Reportar cualquier incidente de seguridad inmediatamente.
        """,
        "metadata": {
            "title": "Manual de Seguridad",
            "category": "policies",
            "department": "IT",
            "confidential": "internal"
        }
    },
    "chunking_config": {
        "chunk_size": 500,
        "chunk_overlap": 50
    },
    "embedding_config": {
        "model": "text-embedding-ada-002",
        "batch_size": 50
    }
})

print("Documento almacenado:", store_doc.json())

# Paso 3: Búsqueda RAG
search_results = requests.post(base_url, headers=headers, json={
    "agent": "database_operations",
    "action": "vector_search",
    "query": "políticas de seguridad y autenticación",
    "collection_name": "empresa_knowledge_base",
    "top_k": 5,
    "threshold": 0.8,
    "include_metadata": True,
    "similarity_metric": "cosine"
})

print("Resultados de búsqueda:", search_results.json())
```

### Ejemplo 2: Análisis de Datos Empresarial

```python
# Análisis de datos con métricas
data_analysis = requests.post(base_url, headers=headers, json={
    "agent": "database_operations",
    "action": "complex_data_analysis",
    "query": """
    SELECT 
        c.name as collection_name,
        COUNT(d.id) as document_count,
        COUNT(dc.id) as chunk_count,
        AVG(LENGTH(dc.content)) as avg_chunk_length,
        MAX(d.created_at) as latest_document,
        MIN(d.created_at) as oldest_document
    FROM collections c
    LEFT JOIN documents d ON c.id = d.collection_id
    LEFT JOIN document_chunks dc ON d.id = dc.document_id
    WHERE c.name = 'empresa_knowledge_base'
    GROUP BY c.id, c.name
    """,
    "output_format": "detailed",
    "include_execution_plan": True,
    "performance_metrics": True
})

print("Análisis completado:", data_analysis.json())

# Generar estadísticas de uso
usage_stats = requests.post(base_url, headers=headers, json={
    "agent": "database_operations", 
    "action": "generate_usage_statistics",
    "time_period": "last_30_days",
    "metrics": [
        "queries_per_hour",
        "top_searches",
        "collection_usage",
        "response_times"
    ],
    "output_format": "dashboard_json"
})

print("Estadísticas:", usage_stats.json())
```

### Ejemplo 3: Migración y Optimización

```python
# Optimización automática de índices
optimize_indexes = requests.post(base_url, headers=headers, json={
    "agent": "database_operations",
    "action": "optimize_indexes",
    "analysis_type": "performance",
    "recommendations": True,
    "apply_changes": False,
    "tables": ["document_chunks", "documents", "collections"]
})

print("Recomendaciones de optimización:", optimize_indexes.json())

# Migración de esquema
schema_migration = requests.post(base_url, headers=headers, json={
    "agent": "database_operations",
    "action": "migrate_schema",
    "migration_name": "add_document_tags",
    "sql_commands": [
        "ALTER TABLE documents ADD COLUMN tags TEXT[] DEFAULT '{}';",
        "CREATE INDEX documents_tags_idx ON documents USING GIN (tags);",
        "UPDATE documents SET tags = ARRAY['general'] WHERE tags IS NULL;"
    ],
    "rollback_sql": [
        "DROP INDEX documents_tags_idx;",
        "ALTER TABLE documents DROP COLUMN tags;"
    ],
    "validate_migration": True
})

print("Migración ejecutada:", schema_migration.json())
```

## 🔧 Configuración Avanzada

### Configuración de Conexiones

```yaml
# database_config.yaml
database:
  host: localhost
  port: 5432
  database: multiagent_db
  username: multiagent
  password: secure_password
  ssl_mode: require
  
  connection_pool:
    min_connections: 5
    max_connections: 20
    max_overflow: 10
    pool_timeout: 30
    pool_recycle: 3600
    pool_pre_ping: true
    
  execution_options:
    statement_timeout: 60000
    idle_in_transaction_session_timeout: 300000
    
vector_search:
  dimensions: 768
  similarity_metric: cosine
  hnsw:
    m: 16
    ef: 200
    ef_construction: 200
    
backup:
  enabled: true
  schedule: "0 2 * * *"  # Daily at 2 AM
  retention_days: 30
  compression: true
  encryption: true
  
monitoring:
  enabled: true
  slow_query_threshold: 1000  # ms
  connection_monitoring: true
  performance_metrics: true
```

### Configuración de Performance

```python
# performance_config.py
performance_settings = {
    "query_optimization": {
        "enable_parallelization": True,
        "batch_size": 1000,
        "async_operations": True,
        "connection_reuse": True
    },
    "vector_optimization": {
        "index_type": "hnsw",
        "chunk_prefetching": True,
        "embedding_cache_size": 10000,
        "compression": "fp16"
    },
    "resource_limits": {
        "max_memory_usage": "2GB",
        "max_cpu_cores": 4,
        "max_concurrent_queries": 10,
        "query_timeout": 300
    }
}
```

## 📊 Monitoreo y Métricas

### Métricas de Performance

```python
# Métricas disponibles
metrics = {
    "connection_pool": {
        "active_connections": "current active connections",
        "idle_connections": "idle connections in pool",
        "pool_size": "total pool size",
        "wait_time": "time waiting for connection"
    },
    "query_performance": {
        "avg_execution_time": "average query execution time",
        "slow_queries": "queries > threshold",
        "query_throughput": "queries per second",
        "error_rate": "percentage of failed queries"
    },
    "vector_operations": {
        "embedding_generation_time": "time to generate embeddings",
        "search_latency": "vector search response time",
        "index_efficiency": "HNSW index performance",
        "memory_usage": "memory used by vector operations"
    },
    "backup_status": {
        "last_backup": "timestamp of last backup",
        "backup_duration": "time to complete backup",
        "backup_size": "size of backup files",
        "restore_time": "time to restore from backup"
    }
}
```

### Dashboard de Monitoreo

Las métricas están disponibles en:
- **Performance Overview**: Tiempo de respuesta, throughput, errores
- **Connection Management**: Pool de conexiones, métricas de espera
- **Vector Search**: Performance de búsquedas RAG, índices
- **Backup Status**: Estado de backups, tiempo de restore

## 🚨 Troubleshooting

### Problemas Comunes

#### Error: Connection refused

```python
# Verificar configuración de conexión
connection_test = requests.post(base_url, headers=headers, json={
    "agent": "database_operations",
    "action": "test_connection",
    "connection_details": {
        "host": "localhost",
        "port": 5432,
        "database": "multiagent_db",
        "user": "multiagent"
    }
})

print("Test de conexión:", connection_test.json())
```

#### Error: Vector dimension mismatch

```python
# Verificar configuración de vectores
vector_check = requests.post(base_url, headers=headers, json={
    "agent": "database_operations",
    "action": "validate_vector_config",
    "expected_dimensions": 768,
    "check_indexes": True
})

print("Validación de vectores:", vector_check.json())
```

#### Error: Slow queries

```python
# Optimizar queries lentas
slow_query_analysis = requests.post(base_url, headers=headers, json={
    "agent": "database_operations",
    "action": "analyze_slow_queries",
    "time_threshold": 1000,  # ms
    "top_queries": 10,
    "recommendations": True,
    "create_indexes": True
})

print("Análisis de queries lentas:", slow_query_analysis.json())
```

### Debugging Avanzado

```bash
# Ver logs del agente
docker-compose logs database-operations-agent

# Habilitar SQL logging
export DATABASE_DEBUG_SQL=true
export DB_LOG_LEVEL=DEBUG

# Verificar extensiones
psql -d multiagent_db -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

## 🔒 Seguridad y Compliance

### Mejores Prácticas de Seguridad

1. **Connection Security**: SSL/TLS para todas las conexiones
2. **Authentication**: Usuarios con permisos mínimos
3. **Data Encryption**: Encriptación en reposo y tránsito
4. **Access Control**: Row Level Security (RLS)
5. **Audit Logging**: Logging completo de todas las operaciones

### Configuración de Seguridad

```sql
-- Row Level Security
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY chunk_access_policy ON document_chunks
    FOR ALL TO multiagent
    USING (metadata->>'access_level' = current_setting('app.current_user_level'));

-- Audit logging
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operation VARCHAR(50) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    record_id UUID,
    old_data JSONB,
    new_data JSONB,
    user_id VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 📈 Optimización

### Performance Tips

1. **Index Optimization**: Usar índices HNSW para vectores
2. **Connection Pooling**: Reutilizar conexiones
3. **Query Optimization**: Optimizar queries complejas
4. **Batch Operations**: Operaciones en lote
5. **Caching**: Cache de resultados frecuentes

### Configuración de Optimización

```sql
-- Optimizar configuración de PostgreSQL
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';

-- Optimizar pgvector
ALTER SYSTEM SET vector.index_type = 'hnsw';
ALTER SYSTEM SET vector.m = 16;
ALTER SYSTEM SET vector.ef = 200;
```

## 🎯 Casos de Uso Empresariales

### 1. Sistema de Conocimiento Empresarial

```python
# Implementación de sistema RAG empresarial
enterprise_rag = {
    "collections": [
        {
            "name": "policies",
            "description": "Políticas empresariales",
            "access_level": "internal"
        },
        {
            "name": "technical_docs", 
            "description": "Documentación técnica",
            "access_level": "engineering"
        },
        {
            "name": "marketing_materials",
            "description": "Materiales de marketing",
            "access_level": "marketing"
        }
    ],
    "features": {
        "semantic_search": True,
        "auto_summarization": True,
        "recommendations": True,
        "collaborative_annotations": True
    },
    "security": {
        "rls_enabled": True,
        "audit_logging": True,
        "data_encryption": True
    }
}
```

### 2. Analytics y Business Intelligence

```python
# Pipeline de analytics
analytics_pipeline = {
    "data_sources": ["web_scraping", "git_operations", "file_processing"],
    "processing": {
        "real_time": True,
        "batch_processing": "daily",
        "ml_enrichment": True
    },
    "outputs": {
        "executive_dashboard": True,
        "operational_reports": True,
        "predictive_analytics": True
    }
}
```

### 3. Data Lake y Warehouse

```python
# Arquitectura de datos empresarial
data_architecture = {
    "layers": {
        "raw_data": "unstructured and semi-structured",
        "processed_data": "cleaned and normalized",
        "analytics_data": "aggregated and optimized",
        "ml_data": "feature engineered and vectorized"
    },
    "features": {
        "scalability": "horizontal",
        "performance": "real-time queries",
        "governance": "full lineage tracking"
    }
}
```

---

## 📞 Soporte

**Documentación API**: http://localhost:8000/docs#/Database%20Operations  
**Issues**: GitHub Issues en el repositorio del proyecto  
**Logs**: http://localhost:8000/logs/database-operations  
**Métricas**: http://localhost:3001 (Grafana dashboard)

---

**🚀 Estado**: **HERRAMIENTA REAL OPERATIVA**  
**📅 Última Actualización**: 2025-11-04  
**✅ Producción**: **READY FOR ENTERPRISE DATABASE OPERATIONS**
