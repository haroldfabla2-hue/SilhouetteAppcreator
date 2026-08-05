# Database Operations Agent MCP

## 📋 Descripción General

El **Database Operations Agent MCP** es un agente especializado para PostgreSQL + pgvector que proporciona operaciones avanzadas de base de datos a través de una interfaz MCP unificada. Este agente maneja desde consultas SQL simples hasta búsquedas vectoriales complejas, gestión de esquemas, optimización de performance y monitoreo completo.

## 🚀 Características Principales

### ✨ Capacidades Core
- **Ejecución de Consultas SQL**: Ejecución segura y optimizada de consultas SQL
- **Búsqueda Vectorial**: Integración completa con pgvector para búsquedas semánticas
- **Gestión de Esquemas**: Creación, modificación y análisis de estructuras de base de datos
- **Migración de Datos**: Transferencia eficiente de datos entre tablas y esquemas
- **Backup/Restore**: Gestión completa de respaldos usando pg_dump/psql
- **Optimización de Performance**: Análisis y optimización automática de rendimiento
- **Gestión de Pool de Conexiones**: Monitoreo y optimización del pool de conexiones
- **Gestión de Índices**: Creación, análisis y optimización de índices
- **Monitoreo Completo**: Métricas de salud, performance y operaciones

### 🔧 Características Técnicas
- **Pool de Conexiones**: Implementación avanzada con QueuePool de SQLAlchemy
- **Retry Logic**: Manejo inteligente de fallos con reintentos configurables
- **Métricas Detalladas**: Tracking completo de performance y uso
- **Logging Avanzado**: Logs estructurados para debugging y monitoreo
- **Manejo de Errores**: Excepciones específicas y recovery automático
- **Async/Await**: Implementación completamente asíncrona
- **Type Safety**: Tipado completo con Pydantic y dataclasses

## 📦 Instalación y Configuración

### Dependencias Requeridas
```bash
# Dependencias principales
pip install sqlalchemy psycopg2-binary pgvector

# Para async support
pip install asyncpg aiosqlite

# Para monitoreo y métricas
pip install prometheus-client
```

### Configuración de PostgreSQL + pgvector

1. **Instalar PostgreSQL**:
```sql
-- Habilitar extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;
```

2. **Configuración recomendada**:
```sql
-- Configuración de memoria para pgvector
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
```

3. **Variables de Entorno**:
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=rag_database
export DB_USER=postgres
export DB_PASSWORD=your_password
export DB_POOL_SIZE=10
export DB_MAX_OVERFLOW=20
```

## 🔧 Uso del Agente

### Inicialización Básica

```python
from agents.database_operations_agent import (
    DatabaseOperationsAgentWrapper,
    DatabaseConnectionConfig
)

# Configuración de base de datos
db_config = DatabaseConnectionConfig(
    host="localhost",
    port=5432,
    database="rag_database",
    user="postgres",
    password="password",
    pool_size=10,
    max_overflow=20
)

# Crear agente
agent = DatabaseOperationsAgentWrapper(db_config)

# Inicializar
await agent.ensure_initialized()
```

### Ejemplo de Consulta SQL

```python
# Ejecutar consulta SQL
result = await agent.process_request({
    "operation_type": "sql_query",
    "query": "SELECT * FROM users WHERE created_at > $1",
    "parameters": {"created_at": "2024-01-01"}
})

print(f"Filas afectadas: {result['rows_affected']}")
print(f"Tiempo: {result['execution_time_ms']:.2f}ms")
print(f"Datos: {result['data']}")
```

### Ejemplo de Búsqueda Vectorial

```python
# Búsqueda vectorial semántica
result = await agent.process_request({
    "operation_type": "vector_search",
    "query_embedding": [0.1, 0.2, 0.3] + [0.0] * 1533,  # 1536 dimensiones
    "table_name": "knowledge_base",
    "limit": 10,
    "threshold": 0.7
})

print(f"Resultados encontrados: {result['total_matches']}")
for item in result['results']:
    print(f"Similitud: {item['similarity']:.3f} - {item['content']}")
```

### Ejemplo de Gestión de Esquemas

```python
# Listar todas las tablas
schema_result = await agent.process_request({
    "operation_type": "schema_management",
    "schema_operation": "list_tables"
})

print(f"Tablas encontradas: {len(schema_result['tables'])}")

# Describir tabla específica
table_result = await agent.process_request({
    "operation_type": "schema_management", 
    "schema_operation": "describe_table",
    "table_name": "users"
})

print(f"Columnas: {table_result['columns']}")
print(f"Índices: {table_result['indexes']}")
```

## 📊 Operaciones Disponibles

### 1. SQL Query Execution

**Operación**: `sql_query`

**Parámetros**:
- `query` (str): Consulta SQL a ejecutar
- `parameters` (dict): Parámetros para la consulta

**Retorna**:
```json
{
  "success": true,
  "query": "SELECT * FROM users",
  "execution_time_ms": 45.2,
  "rows_affected": 100,
  "data": [...],
  "metadata": {
    "query_type": "SELECT",
    "timestamp": "2024-01-01T12:00:00"
  }
}
```

### 2. Vector Search

**Operación**: `vector_search`

**Parámetros**:
- `query_embedding` (List[float]): Vector de consulta
- `table_name` (str): Tabla donde buscar
- `limit` (int): Número máximo de resultados (default: 5)
- `threshold` (float): Umbral de similitud (default: 0.7)

**Retorna**:
```json
{
  "success": true,
  "query_embedding": [...],
  "table_name": "knowledge_base",
  "search_time_ms": 125.8,
  "results": [...],
  "total_matches": 10,
  "threshold_used": 0.7,
  "metadata": {
    "search_type": "vector_similarity",
    "timestamp": "2024-01-01T12:00:00"
  }
}
```

### 3. Schema Management

**Operación**: `schema_management`

**Sub-operaciones**:
- `list_tables`: Listar todas las tablas
- `describe_table`: Describir estructura de tabla específica
- `create_table`: Crear nueva tabla
- `drop_table`: Eliminar tabla

### 4. Data Migration

**Operación**: `data_migration`

**Parámetros**:
- `source_table` (str): Tabla origen
- `target_table` (str): Tabla destino
- `batch_size` (int): Tamaño de lote (default: 1000)

### 5. Backup/Restore

**Operación**: `backup_restore`

**Sub-operaciones**:
- `backup`: Crear backup usando pg_dump
- `restore`: Restaurar desde backup
- `list_backups`: Listar archivos de backup disponibles

### 6. Performance Optimization

**Operación**: `performance_optimization`

**Sub-operaciones**:
- `analyze`: Analizar performance actual
- `reindex`: Reindexar base de datos
- `vacuum`: Ejecutar VACUUM
- `update_stats`: Actualizar estadísticas

### 7. Connection Pool Management

**Operación**: `connection_pool`

**Sub-operaciones**:
- `status`: Obtener estado del pool
- `metrics`: Obtener métricas del pool
- `clear`: Limpiar todas las conexiones

### 8. Index Management

**Operación**: `index_management`

**Sub-operaciones**:
- `list`: Listar todos los índices
- `create`: Crear nuevo índice
- `drop`: Eliminar índice
- `analyze`: Analizar uso de índices
- `optimize`: Optimizar índices

### 9. Database Monitoring

**Operación**: `monitoring`

**Sub-tipos**:
- `health`: Verificar salud general
- `performance`: Monitorear métricas de performance
- `connections`: Monitorear conexiones
- `full`: Monitoreo completo

## 📈 Métricas y Monitoreo

### Métricas del Agente

```python
# Obtener estado completo
status = agent.get_status()

print(f"Estado: {status['status']}")
print(f"Utilización: {status['utilization']:.1%}")
print(f"Tasa de éxito: {status['success_rate']:.1%}")
print(f"Operaciones totales: {status['total_operations']}")
```

### Métricas de Performance

```python
# Obtener métricas de performance
metrics = agent.get_performance_metrics()

print(f"Conexiones activas: {metrics.active_connections}")
print(f"Cache hit ratio: {metrics.cache_hit_ratio:.1f}%")
print(f"Tiempo promedio: {metrics.query_avg_time_ms:.2f}ms")
print(f"Consultas lentas: {metrics.slow_queries_count}")
```

### Health Check

```python
# Verificar salud del agente
health = await agent.health_check()

print(f"Estado: {health['status']}")
print(f"Conexión DB: {health['database_connection']}")
print(f"Estado pool: {health['pool_status']}")
```

## ⚡ Optimización y Best Practices

### Configuración de Pool de Conexiones

```python
# Configuración optimizada para aplicaciones de alta concurrencia
db_config = DatabaseConnectionConfig(
    host="localhost",
    port=5432,
    database="rag_database",
    user="postgres",
    password="password",
    pool_size=20,        # Más conexiones base
    max_overflow=30,     # Más capacidad de overflow
    pool_timeout=30,     # Timeout razonable
    pool_recycle=3600    # Reciclar cada hora
)
```

### Búsquedas Vectoriales Eficientes

```python
# Optimizar búsqueda vectorial
result = await agent.process_request({
    "operation_type": "vector_search",
    "query_embedding": embedding,
    "table_name": "knowledge_base",
    "limit": 20,         # Más resultados para filtrar
    "threshold": 0.6     # Threshold más flexible
})

# Filtrar resultados por criterios adicionales
filtered_results = [
    r for r in result['results'] 
    if r['similarity'] > 0.8 and r['metadata']['verified']
]
```

### Gestión de Índices

```python
# Crear índice vectorial para búsqueda rápida
await agent.process_request({
    "operation_type": "index_management",
    "index_operation": "create",
    "index_spec": {
        "index_name": "idx_knowledge_embedding",
        "table_name": "knowledge_base",
        "columns": ["embedding"],
        "index_type": "ivfflat"  # Para pgvector
    }
})
```

### Monitoreo Continuo

```python
# Configurar monitoreo automático
async def monitor_database():
    while True:
        # Health check
        health = await agent.health_check()
        if health['status'] != 'healthy':
            print(f"⚠️ Problema de salud: {health}")
        
        # Performance check cada 5 minutos
        perf_result = await agent.process_request({
            "operation_type": "monitoring",
            "monitor_type": "performance"
        })
        
        cache_hit_ratio = perf_result['performance_metrics']['cache_hit_ratio']
        if cache_hit_ratio < 95:
            print(f"⚠️ Cache hit ratio bajo: {cache_hit_ratio}%")
        
        await asyncio.sleep(300)  # 5 minutos

# Ejecutar monitoreo
asyncio.create_task(monitor_database())
```

## 🔍 Troubleshooting

### Problemas Comunes

1. **Error de Conexión**:
```python
# Verificar configuración de base de datos
db_config = DatabaseConnectionConfig(
    host="localhost",
    port=5432,
    database="rag_database",
    user="postgres",
    password="password"  # Verificar credenciales
)

# Test manual de conexión
try:
    await agent._test_connection()
    print("✅ Conexión exitosa")
except Exception as e:
    print(f"❌ Error de conexión: {e}")
```

2. **Pool de Conexiones Saturado**:
```python
# Verificar estado del pool
pool_status = await agent.process_request({
    "operation_type": "connection_pool",
    "pool_operation": "status"
})

# Limpiar pool si es necesario
if pool_status['pool_metrics']['checked_out'] >= pool_status['pool_metrics']['total_connections']:
    await agent.process_request({
        "operation_type": "connection_pool", 
        "pool_operation": "clear"
    })
```

3. **Búsqueda Vectorial Lenta**:
```python
# Analizar uso de índices
index_analysis = await agent.process_request({
    "operation_type": "index_management",
    "index_operation": "analyze"
})

# Reindexar si es necesario
if index_analysis['recommendations']:
    await agent.process_request({
        "operation_type": "performance_optimization",
        "optimization_type": "reindex"
    })
```

### Logs y Debugging

```python
import logging

# Configurar logging detallado
logging.basicConfig(level=logging.DEBUG)
agent_logger = logging.getLogger("mcp.agents.database_operations")
agent_logger.setLevel(logging.DEBUG)

# Ver métricas de operación
def log_operation_metrics(result):
    if result['success']:
        print(f"✅ Operación completada en {result['execution_time_ms']:.2f}ms")
    else:
        print(f"❌ Operación falló: {result['error_message']}")
```

## 🧪 Testing

### Ejecutar Tests

```bash
# Tests básicos
python tests/test_database_operations_agent.py

# Tests con cobertura
python -m pytest tests/test_database_operations_agent.py --cov=agents.database_operations_agent

# Tests con integración real (requiere PostgreSQL)
DB_HOST=localhost python tests/test_database_operations_agent.py --integration
```

### Test de Conectividad

```python
# Test básico de conectividad
async def test_connectivity():
    try:
        health = await agent.health_check()
        assert health['status'] == 'healthy'
        print("✅ Conectividad OK")
    except Exception as e:
        print(f"❌ Error de conectividad: {e}")

asyncio.run(test_connectivity())
```

## 📚 API Reference

### Clases Principales

#### DatabaseOperationsAgentWrapper
Agente principal para operaciones de base de datos.

**Métodos principales**:
- `initialize()`: Inicializar conexión y pool
- `process_request(request, context)`: Procesar request MCP
- `get_status()`: Obtener estado del agente
- `health_check()`: Verificar salud

#### DatabaseConnectionConfig
Configuración de conexión a PostgreSQL.

**Propiedades**:
- `database_url`: URL de conexión generada
- `host`, `port`, `database`, `user`, `password`: Configuración básica
- `pool_size`, `max_overflow`: Configuración de pool

#### PerformanceMetrics
Métricas de performance de la base de datos.

**Campos**:
- `active_connections`: Conexiones activas
- `cache_hit_ratio`: Ratio de aciertos de cache
- `query_avg_time_ms`: Tiempo promedio de consultas
- `slow_queries_count`: Número de consultas lentas

### Tipos de Error

El agente usa excepciones específicas del paquete `..core.exceptions`:

- `AgentException`: Error general del agente
- `DATABASE_ERROR`: Error de base de datos
- `DATABASE_CONNECTION_FAILED`: Error de conexión
- `DATABASE_QUERY_ERROR`: Error en consulta SQL
- `VECTOR_DB_ERROR`: Error en operación vectorial

## 🤝 Contribución

### Desarrollo

1. Fork del repositorio
2. Crear branch para feature
3. Implementar tests
4. Ejecutar tests y linters
5. Crear pull request

### Estructura de Código

```
agents/
├── database_operations_agent.py    # Agente principal
├── base_agent_wrapper.py          # Clase base
└── __init__.py                     # Exports

examples/
└── database_operations_example.py  # Ejemplos de uso

tests/
└── test_database_operations_agent.py  # Tests unitarios
```

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver archivo LICENSE para más detalles.

## 🆘 Soporte

Para soporte y preguntas:

1. Revisar documentación y examples
2. Verificar logs y métricas
3. Consultar troubleshooting guide
4. Crear issue en el repositorio

---

**Database Operations Agent MCP** - Operando PostgreSQL + pgvector con excelencia 🚀