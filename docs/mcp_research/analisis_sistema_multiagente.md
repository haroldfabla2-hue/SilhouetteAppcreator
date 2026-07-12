# Análisis del Sistema Multi-Agente Existente

## Fase 1: Análisis del Sistema Multi-Agente Actual

### 1.1 Arquitectura Core: MultiAgentOrchestrator

El `MultiAgentOrchestrator` es el componente central que coordina toda la ejecución multi-agente. Características principales:

#### Responsabilidades Clave:
- **Coordinación de 5 agentes especializados**: Reasoner, Planner, Executor, Verifier, MemoryManager
- **Paralelización**: Soporta 3-5 agentes simultáneos con patrón fan-out/fan-in
- **Router LLM inteligente**: Integra con múltiples modelos de LLM
- **Checkpoints y recuperación**: Manejo de estado de sesiones
- **Observabilidad completa**: Logging detallado y métricas

#### Componentes Principales:
```python
# Agentes especializados
self.reasoner = ReasonerAgent(llm_client=llm_router)
self.planner = PlannerAgent(llm_client=llm_router)
self.verifier = VerifierAgent(llm_client=llm_router)
self.memory_manager = MemoryManagerAgent(
    llm_client=llm_router,
    vector_store=vector_store
)

# Pool de executors especializados
self.executors = {
    "general": ExecutorAgent("general", llm_client=llm_router),
    "code": ExecutorAgent("code", llm_client=llm_router),
    "web": ExecutorAgent("web", llm_client=llm_router),
    "docs": ExecutorAgent("docs", llm_client=llm_router)
}
```

#### Flujo de Ejecución (5 Fases):
1. **Reasoning**: Análisis de intención y preparación de contexto
2. **Planning**: Descomposición en subtareas ejecutables  
3. **Execution**: Paralelización de tareas (fan-out)
4. **Verification**: Validación y evaluación de calidad
5. **Synthesis**: Síntesis final y almacenamiento en memoria (fan-in)

### 1.2 Los 5 Agentes Especializados

#### 1.2.1 ReasonerAgent
**Responsabilidades**:
- Interpretar intención del usuario
- Resumir contexto relevante  
- Preparar prompts enriquecidos
- Definir estrategia de exploración

**Capacidades**:
```python
def get_capabilities(self) -> List[str]:
    return [
        "intent_analysis",
        "context_summarization", 
        "strategy_definition",
        "prompt_preparation"
    ]
```

**Funcionalidades Real**:
- Integración con OpenRouter API para LLM real
- Categorización automática de tareas (coding, research, analysis, web_interaction)
- Estimación de complejidad basada en heurísticas
- Estrategia adaptativa según tipo de tarea

#### 1.2.2 PlannerAgent  
**Responsabilidades**:
- Crear plan de pasos ejecutables (fan-out/fan-in)
- Definir tool calls necesarias
- Establecer criterios de terminación
- Gestionar dependencias entre subtareas

**Capacidades**:
```python
def get_capabilities(self) -> List[str]:
    return [
        "task_decomposition",
        "tool_selection",
        "dependency_management", 
        "plan_optimization"
    ]
```

**Funcionalidades Real**:
- Generación dinámica de subtareas según estrategia
- Asignación inteligente de herramientas por tipo de tarea
- Optimización de orden de ejecución
- Soporte para tareas paralelas y secuenciales

#### 1.2.3 ExecutorAgent (Pool Especializado)
**Pool de 4 Ejecutores Especializados**:
- **General**: Tareas básicas ymiscéneas
- **Code**: Ejecución y análisis de código Python
- **Web**: Web scraping e interacción con sitios web
- **Docs**: Procesamiento de documentos

**Herramientas Integradas**:
- Python Executor con sandbox de seguridad
- Web Scraper con HTTP real y parsing HTML
- Git Operations (status, commit, log, clone, pull, push)
- Document Processor (.txt, .md con aiofiles)
- API Caller (GET, POST, PUT, DELETE con JSON)

#### 1.2.4 VerifierAgent
**Responsabilidades**:
- Validación de resultados contra criterios de calidad
- Evaluación de completitud y consistencia
- Generación de métricas de calidad

**Capacidades**:
- LLM Judge como evaluador experto
- Parsing robusto de JSON con fallbacks
- Scores detallados (0.0-1.0) con justificaciones
- Fallback heurístico cuando falla LLM

#### 1.2.5 MemoryManagerAgent
**Responsabilidades**:
- Gestión de memoria persistente
- Búsqueda semántica en histórico
- Almacenamiento de conocimiento

**Funcionalidades Real**:
- PostgreSQL + pgvector para memoria vectorial
- Búsqueda semántica con similitud coseno
- Índices IVFFL para optimización
- Cache local como fallback

### 1.3 Componentes de Orquestación

#### 1.3.1 TaskManager
**Funcionalidades**:
- Gestión completa del ciclo de vida de tareas
- Estado de tareas con TaskStatus (CREATED, STARTED, IN_PROGRESS, COMPLETED, ERROR, CANCELLED)
- Sistema de fases TaskPhase (REASONING, PLANNING, EXECUTION, VERIFICATION, COMPLETION)
- Streaming de updates en tiempo real con SSE
- Limpieza automática de tareas completadas (>1 hora)

**Arquitectura**:
- Almacenamiento en memoria con diccionario `self.tasks`
- Sistema de suscriptores para notificaciones
- Locks asíncronos para concurrencia segura
- Cola de eventos para streaming

#### 1.3.2 TaskOrchestratorIntegrator
**Funcionalidades**:
- Bridge entre TaskManager y MultiAgentOrchestrator
- Ejecución con tracking completo de progreso
- Soporte para ejecución asíncrona y cancelable
- Callbacks para actualización de estado en tiempo real

**Integración con Orquestador**:
```python
async def execute_task_with_tracking(
    self,
    task_id: str,
    objective: str,
    user_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    # 1. Actualizar estado a in_progress
    await self.task_manager.update_task(
        task_id=task_id,
        status=TaskStatus.IN_PROGRESS,
        phase=TaskPhase.REASONING,
        progress=0.1,
        message="Iniciando razonamiento"
    )
    
    # 2. Ejecutar en orquestador
    result = await self.orchestrator.process_request(
        objetivo=objective,
        contexto=context or {}
    )
    
    # 3. Marcar como completada
    await self.task_manager.update_task(
        task_id=task_id,
        status=TaskStatus.COMPLETED,
        phase=TaskPhase.COMPLETION,
        progress=1.0,
        message="Tarea completada exitosamente",
        result=result
    )
```

### 1.4 Infraestructura de Comunicación: Sistema SSE y Endpoints API

#### 1.4.1 Server-Sent Events (SSE)
**Configuración en TaskManager**:
```python
async def stream_task_updates(
    self,
    task_id: str,
    update_frequency: float = 1.0,
    max_duration: int = 300
) -> AsyncGenerator[str, None]:
    # Heartbeat cada update_frequency segundos
    # Termina cuando tarea completa/error/cancelada
    # Formato: "data: {json.dumps(update)}\n\n"
```

**Endpoints de Streaming**:
- `POST /api/v1/tasks/create`: Crear nueva tarea
- `POST /api/v1/tasks/execute`: Ejecutar tarea (sync/async)
- `GET /api/v1/tasks/{task_id}/stream`: Stream de updates
- `GET /api/v1/tasks/{task_id}/status`: Estado actual
- `GET /api/v1/tasks/{task_id}/results`: Resultados finales
- `DELETE /api/v1/tasks/{task_id}`: Cancelar tarea

#### 1.4.2 Endpoints API Principales
**API REST con FastAPI**:
- **Creación/Ejecución**: `/api/v1/tasks`
- **Streaming**: `/api/v1/tasks/{id}/stream`
- **Estado**: `/api/v1/tasks/{id}/status`
- **Resultados**: `/api/v1/tasks/{id}/results`
- **Listado**: `/api/v1/tasks/list`
- **Sistema**: `/api/v1/stats`, `/health`

**Modelos de Request/Response**:
```python
class TaskRequest(BaseModel):
    objetivo: str
    contexto: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    stream: bool = False

class TaskResponse(BaseModel):
    conversation_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
```

### 1.5 Herramientas del Sistema (backend/tools/)

#### 1.5.1 Herramientas Disponibles (10+ herramientas)
1. **BaseTool**: Clase base abstracta con funcionalidades comunes
2. **ToolManager**: Gestor central de herramientas con:
   - Registro/desregistro dinámico
   - Ejecución paralela/secuencial
   - Estadísticas y monitoreo
   - Health check
   - Cache de resultados

3. **PythonExecutor**: 
   - Ejecución segura con sandboxing
   - Análisis AST para patrones peligrosos
   - Restricción de módulos/builtins
   - Timeout configurable
   - Captura de output y errores

4. **WebScraper**:
   - HTTP real con httpx
   - HTML parsing y limpieza
   - Búsqueda web con fallbacks
   - User-Agent spoofing
   - Content extraction hasta 5000 chars

5. **FileProcessor**:
   - Lectura asíncrona con aiofiles
   - Soporte .txt, .md, PDF simulado
   - Encoding UTF-8 completo
   - Preview limitado (1000 chars)

6. **SearchEngine**:
   - Integración con motores de búsqueda
   - DuckDuckGo, Wikipedia
   - Resultados estructurados
   - Rate limiting y cache

#### 1.5.2 Arquitectura de Herramientas
**Patrón de Diseño**:
- **BaseTool**: Clase abstracta con interface común
- **ToolResult**: Estructura estándar de resultados
- **ToolStatus**: Estados de ejecución (IDLE, RUNNING, COMPLETED, FAILED, TIMEOUT)
- **Sanitización**: Validación de inputs y URLs
- **Error Handling**: Manejo consistente de excepciones

### 1.6 Sistema de Memoria: PostgreSQL + pgvector

#### 1.6.1 Arquitectura de Base de Datos
**Esquema de Tablas**:

```sql
-- Tabla principal de documentos
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text',
    user_id VARCHAR(100),
    conversation_id VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_path TEXT,
    file_size INTEGER,
    mime_type VARCHAR(100)
);

-- Chunks con embeddings vectoriales
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    start_position INTEGER NOT NULL,
    end_position INTEGER NOT NULL,
    token_count INTEGER,
    metadata JSONB DEFAULT '{}',
    embedding vector(384),  -- all-MiniLM-L6-v2
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mensajes de conversación
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    agent_id VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    embedding vector(384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 1.6.2 Capacidades de Embeddings
**EmbeddingService**:
- **Modelo**: all-MiniLM-L6-v2 (384 dimensiones)
- **Performance**: Optimizado para velocidad
- **Cache**: Embeddings frecuentes en memoria
- **Fallback**: Embeddings determinísticos cuando falla servicio
- **Batch Processing**: Generación eficiente de múltiples embeddings

**VectorStore Service**:
- **PostgreSQL + pgvector**: Almacenamiento vectorial nativo
- **Índices HNSW**: Búsqueda vectorial ultra-rápida
- **Búsqueda Semántica**: Similitud coseno
- **Filtrado Avanzado**: Por metadatos, usuario, conversación, tiempo
- **Estrategias de Chunking**: Recursive, paragraph, sentence

#### 1.6.3 Modelos de Datos SQLAlchemy
**Conversations**: Gestión de sesiones de usuario
**Messages**: Mensajes con embeddings para búsqueda contextual
**AgentMessages**: Trazabilidad de interacciones entre agentes
**KnowledgeBase**: Base de conocimiento para RAG

### 1.7 Integraciones Externas

#### 1.7.1 LLM Router
- **OpenRouter Integration**: Claude 3.5 Sonnet, GPT-4, LLaMA 3.3-70B
- **Fallback Strategy**: Respuestas mock cuando falla API
- **Rate Limiting**: Control de consumo de tokens
- **Timeout Handling**: 60s timeout con 10s connect

#### 1.7.2 Redis
- **Cache de Sesiones**: Almacenamiento temporal de estado
- **Comunicación Inter-proceso**: Para escalabilidad horizontal
- **Rate Limiting**: Control de frecuencia de requests
- **Fallback**: Inicialización opcional

#### 1.7.3 Servicios de Embeddings
- **HuggingFace Transformers**: all-MiniLM-L6-v2, all-mpnet-base-v2
- **OpenAI Embeddings**: text-embedding-ada-002 (opcional)
- **Fallback Determinístico**: Cuando servicios no disponibles
- **GPU Support**: CUDA detection y acceleration

## Estado del Análisis - Fase 1
- ✅ **Arquitectura Core**: MultiAgentOrchestrator analizado
- ✅ **5 Agentes Especializados**: Funcionalidades documentadas
- ✅ **Orquestación**: TaskManager y TaskOrchestratorIntegrator
- ✅ **Comunicación**: Sistema SSE y endpoints API
- ✅ **Herramientas**: 10+ herramientas en backend/tools/
- ✅ **Memoria**: PostgreSQL + pgvector y embeddings
- ✅ **Integraciones**: LLM Router, Redis, servicios externos

**Próximo**: Fase 2 - Investigación del ecosistema MCP