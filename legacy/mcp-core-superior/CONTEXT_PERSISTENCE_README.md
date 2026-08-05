# Sistema Avanzado de Persistencia de Contexto

## Descripción General

El **Context Persistence Engine** es un sistema avanzado que proporciona persistencia inteligente de contexto para el MCP Core Superior. Implementa un enfoque jerárquico con clustering semántico, compresión automática y recuperación rápida de contexto entre sesiones.

## Características Principales

### 1. **Almacenamiento Jerárquico de Contexto**
- **Short-term** (0-30 min): Redis para acceso ultra-rápido
- **Medium-term** (30 min - 24h): PostgreSQL con índices optimizados
- **Long-term** (24h - 30d): PostgreSQL comprimido
- **Archive** (30+ días): Almacenamiento de bajo costo

### 2. **Snapshots Incrementales**
```python
# Crear snapshot de contexto
snapshot_id = await create_context_snapshot(
    context_type=ContextType.CONVERSATION,
    content={"messages": [...], "state": {...}},
    user_id="user123",
    session_id="session456",
    metadata={"topic": "technical_discussion"}
)
```

### 3. **Clustering Semántico Automático**
- Agrupa contextos similares usando embeddings
- Centroid dinámico que se actualiza automáticamente
- Búsqueda semántica por similitud coseno
- Umbrales de similitud configurables

### 4. **Compresión Inteligente**
- **LZ4**: Para acceso ultra-rápido (short-term)
- **Zlib**: Balance velocidad/compresión (medium-term)
- **Gzip**: Máxima compresión (long-term/archive)
- Selección automática según tier

### 5. **Control de Versiones**
```python
# Crear versión de snapshot
version_id = await context_persistence_engine.create_version(
    snapshot_id="snap123",
    changes={"messages": [...], "metadata": {...}},
    author="agent_001",
    message="Updated conversation context"
)
```

### 6. **Recuperación Cross-Session**
```python
# Recuperar contexto completo de sesión
session_contexts = await recover_session(
    user_id="user123",
    session_id="session456",
    max_age_hours=24
)
```

### 7. **Búsqueda Semántica Avanzada**
```python
# Búsqueda por contexto semántico
results = await search_context_semantic(
    query="technical discussion about database optimization",
    user_id="user123",
    limit=10,
    context_type=ContextType.CONVERSATION
)

for snapshot, similarity in results:
    print(f"Similarity: {similarity:.2f}")
    print(f"Content: {snapshot.content}")
```

### 8. **Inicialización Context-Aware de Agentes**
```python
# Inicializar agente con contexto relevante
agent_context = await initialize_agent_with_context(
    agent_name="python_executor",
    user_id="user123",
    session_id="session456",
    context_requirements={
        "context_types": [ContextType.TASK, ContextType.CONVERSATION],
        "max_contexts": 5
    }
)
```

## Arquitectura del Sistema

### Componentes Principales

1. **ContextPersistenceEngine**: Motor principal
2. **ContextSnapshot**: Estructura de datos para snapshots
3. **ContextCluster**: Agrupación semántica de contextos
4. **ContextVersion**: Control de versiones
5. **Indices**: Múltiples índices para recuperación rápida

### Flujo de Datos

```
User Input → Context Snapshot → Compression → Storage Layer → Index Update
     ↓              ↓              ↓              ↓             ↓
Embedding → Semantic Clustering → Version Control → Cache → Search Ready
```

## Esquemas de Base de Datos

### Tabla: context_snapshots
```sql
CREATE TABLE context_snapshots (
    snapshot_id UUID PRIMARY KEY,
    parent_id UUID REFERENCES context_snapshots(snapshot_id),
    context_type TEXT NOT NULL,
    tier TEXT NOT NULL,
    content BYTEA,
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(1536),
    compression_type TEXT DEFAULT 'none',
    compressed_size INTEGER DEFAULT 0,
    original_size INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id TEXT,
    session_id TEXT
);
```

### Tabla: context_clusters
```sql
CREATE TABLE context_clusters (
    cluster_id UUID PRIMARY KEY,
    snapshots UUID[] DEFAULT '{}',
    centroid_embedding VECTOR(1536),
    similarity_threshold FLOAT DEFAULT 0.7,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_merged TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);
```

### Tabla: context_versions
```sql
CREATE TABLE context_versions (
    version_id UUID PRIMARY KEY,
    snapshot_id UUID REFERENCES context_snapshots(snapshot_id),
    parent_version UUID REFERENCES context_versions(version_id),
    changes JSONB DEFAULT '{}',
    diff JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    author TEXT DEFAULT 'system',
    message TEXT DEFAULT ''
);
```

## Configuración

### Variables de Entorno
```bash
# Base de datos
MCP_CORE_DATABASE_URL=postgresql://user:password@localhost:5432/mcp_core
MCP_CORE_VECTOR_DB_URL=postgresql://user:password@localhost:5432/vector_db

# Redis
MCP_CORE_REDIS_URL=redis://localhost:6379

# Embeddings
MCP_CORE_EMBEDDING_MODEL=text-embedding-ada-002
MCP_CORE_EMBEDDING_DIMENSION=1536
```

### Configuración de Tiers
```python
tier_config = {
    ContextTier.SHORT_TERM: {
        "max_size_mb": 100,
        "max_age_hours": 0.5,
        "compression": CompressionType.LZ4,
        "storage": "redis"
    },
    ContextTier.MEDIUM_TERM: {
        "max_size_mb": 500,
        "max_age_hours": 24,
        "compression": CompressionType.ZLIB,
        "storage": "postgresql"
    },
    ContextTier.LONG_TERM: {
        "max_size_mb": 5000,
        "max_age_hours": 720,
        "compression": CompressionType.GZIP,
        "storage": "postgresql"
    }
}
```

## Uso Básico

### 1. Inicialización
```python
from src.core.context_persistence_engine import initialize_context_persistence

# Inicializar el sistema
await initialize_context_persistence()
```

### 2. Crear y Recuperar Contexto
```python
from src.core.context_persistence_engine import (
    create_context_snapshot,
    retrieve_context_snapshot,
    ContextType
)

# Crear contexto
snapshot_id = await create_context_snapshot(
    context_type=ContextType.TASK,
    content={
        "task_id": "task_123",
        "description": "Implementar sistema de autenticación",
        "requirements": ["JWT", "OAuth2"],
        "status": "in_progress"
    },
    user_id="user123",
    session_id="session456"
)

# Recuperar contexto
snapshot = await retrieve_context_snapshot(snapshot_id)
if snapshot:
    print(f"Tarea: {snapshot.content['description']}")
    print(f"Estado: {snapshot.content['status']}")
```

### 3. Búsqueda Semántica
```python
from src.core.context_persistence_engine import search_context_semantic

# Buscar contextos similares
results = await search_context_semantic(
    query="autenticación JWT OAuth",
    user_id="user123",
    limit=5
)

for snapshot, similarity in results:
    print(f"Contexto similar (similitud: {similarity:.2f}):")
    print(f"  - {snapshot.content}")
```

## Optimización Automática

El sistema incluye optimización automática que se ejecuta cada hora:

### Funciones de Optimización

1. **Limpieza de Expirados**: Elimina snapshots con TTL vencido
2. **Optimización de Tiers**: Mueve contextos entre tiers según patrones de acceso
3. **Recompresión**: Aplica algoritmos de compresión más eficientes
4. **Rebuild de Índices**: Reconstruye índices para mantener performance
5. **Limpieza de Cache**: Libera memoria removiendo contextos poco accedidos

### Ejecutar Optimización Manual
```python
from src.core.context_persistence_engine import optimize_context_storage

# Ejecutar optimización manual
results = await optimize_context_storage()
print(f"Optimización completada: {results}")
```

## Monitoreo y Estadísticas

### Obtener Estadísticas
```python
from src.core.context_persistence_engine import get_context_engine_stats

stats = await get_context_engine_stats()
print(f"Total snapshots: {stats['database']['total_snapshots']}")
print(f"Clusters activos: {stats['database']['total_clusters']}")
print(f"Uso de Redis: {stats['redis']['memory_usage_mb']:.2f} MB")
```

### Health Check
```python
health = await context_persistence_engine._health_check()
print(f"Redis: {'✓' if health['redis'] else '✗'}")
print(f"PostgreSQL: {'✓' if health['postgresql'] else '✗'}")
print(f"Embedding Service: {'✓' if health['embedding_service'] else '✗'}")
```

## Casos de Uso Avanzados

### 1. **Workflow de Desarrollo Continuo**
```python
# Snapshot por fase de desarrollo
phases = ["design", "implementation", "testing", "deployment"]
for phase in phases:
    await create_context_snapshot(
        context_type=ContextType.WORKFLOW,
        content={"phase": phase, "decisions": [...], "artifacts": [...]},
        metadata={"workflow_id": "dev_flow_001", "phase": phase}
    )
```

### 2. **Memoria Persistente de Agentes**
```python
# Agente recuerda preferencias y conocimiento previo
agent_memory = {
    "preferred_models": ["gpt-4", "claude-3"],
    "specializations": ["python", "database_design"],
    "successful_patterns": [...],
    "failed_approaches": [...]
}

await create_context_snapshot(
    context_type=ContextType.AGENT_MEMORY,
    content=agent_memory,
    metadata={"agent_type": "code_generator", "version": "v2.1"}
)
```

### 3. **Recuperación de Sesión Completa**
```python
# Al re-conectar usuario, recuperar todo el contexto
session_contexts = await recover_session(
    user_id="user123",
    session_id="session456",
    max_age_hours=168  # 1 semana
)

# Reconstruir estado completo
complete_state = {
    "conversations": [],
    "tasks": [],
    "agent_memories": [],
    "preferences": {}
}

for snapshot in session_contexts:
    if snapshot.context_type == ContextType.CONVERSATION:
        complete_state["conversations"].append(snapshot.content)
    elif snapshot.context_type == ContextType.TASK:
        complete_state["tasks"].append(snapshot.content)
    # ... otros tipos
```

## Integración con Agentes

### Context-Aware Agent Wrapper
```python
class ContextAwareAgent:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.context_cache = {}
    
    async def initialize_with_context(self, user_id: str, session_id: str):
        # Obtener contexto relevante
        context = await initialize_agent_with_context(
            agent_name=self.agent_name,
            user_id=user_id,
            session_id=session_id,
            context_requirements={
                "context_types": [ContextType.TASK, ContextType.CONVERSATION],
                "max_contexts": 5
            }
        )
        
        # Cachear contexto para uso durante ejecución
        self.context_cache = context
        return context
    
    async def execute_with_context(self, task: dict, **kwargs):
        # Incluir contexto en la ejecución
        execution_context = {
            "task": task,
            "cached_context": self.context_cache,
            "session_info": {
                "user_id": kwargs.get("user_id"),
                "session_id": kwargs.get("session_id")
            }
        }
        
        # Ejecutar tarea con contexto
        result = await self.execute_task(execution_context)
        
        # Crear snapshot del resultado
        await create_context_snapshot(
            context_type=ContextType.TASK,
            content={"input": task, "output": result, "execution_time": time.time()},
            metadata={"agent_name": self.agent_name, "success": True}
        )
        
        return result
```

## Mejores Prácticas

### 1. **Gestión de Contexto**
- Mantener snapshots pequeños y específicos
- Usar metadatos descriptivos para mejorar búsqueda
- Limpiar contexto obsoleto regularmente

### 2. **Rendimiento**
- Configurar TTL apropiados para cada tier
- Usar compresión en snapshots grandes (>1KB)
- Monitorear métricas de cache hit ratio

### 3. **Escalabilidad**
- Particionar por usuario/tenant para multitenancy
- Implementar cleanup automático de datos antiguos
- Usar Redis Cluster para alta disponibilidad

### 4. **Seguridad**
- Cifrar contenido sensible en snapshots
- Implementar control de acceso por usuario
- Auditar acceso a contextos críticos

## Troubleshooting

### Problemas Comunes

**1. Error de conexión a PostgreSQL**
```python
# Verificar configuración
health = await context_persistence_engine._health_check()
if not health["postgresql"]:
    print("PostgreSQL desconectado, verificando pool...")
    # Reintentar conexión o usar fallback a Redis
```

**2. Alto uso de memoria**
```python
# Limpiar cache manualmente
await context_persistence_engine._cleanup_cache()

# Optimizar almacenamiento
await optimize_context_storage()
```

**3. Búsquedas lentas**
```python
# Rebuild índices
await context_persistence_engine._rebuild_indexes()

# Verificar salud de índices
stats = await get_context_engine_stats()
print(f"Tamaño de índices: {stats['performance']['indexes_size']}")
```

## API Reference

### Métodos Principales

#### `create_context_snapshot(context_type, content, ...)` → str
Crear snapshot incremental de contexto.

#### `retrieve_context_snapshot(snapshot_id)` → ContextSnapshot | None
Recuperar snapshot por ID.

#### `search_context_semantic(query, ...)` → List[Tuple[ContextSnapshot, float]]
Búsqueda semántica de contextos.

#### `recover_session(user_id, session_id, ...)` → List[ContextSnapshot]
Recuperar contexto completo de sesión.

#### `create_version(snapshot_id, changes, ...)` → str
Crear versión de control de snapshot.

#### `optimize_storage()` → Dict[str, Any]
Ejecutar optimización automática.

#### `get_stats()` → Dict[str, Any]
Obtener estadísticas del sistema.

---

Este sistema proporciona una base sólida para persistencia inteligente de contexto con capacidades avanzadas de búsqueda, clustering y optimización automática.