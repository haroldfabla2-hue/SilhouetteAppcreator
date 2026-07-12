# Integración del Sistema Multi‑Agente con un Servidor MCP: Blueprint Técnico

## 1. Propósito, alcance y contexto del sistema actual

Este documento define un blueprint de integración entre el sistema multi‑agente existente y un servidor MCP (Model Context Protocol). El objetivo es exponer, de forma segura y eficiente, las capacidades de los agentes, las herramientas del backend y la memoria vectorial (PostgreSQL + pgvector) como recursos y herramientas MCP, preservando el flujo operativo actual y potenciando la interoperabilidad con clientes y ecosistemas externos.

El alcance se circunscribe a los siguientes componentes y funciones:
- Cinco agentes especializados —Reasoner, Planner, Executors (general, code, web, docs), Verifier y MemoryManager— orquestados por un MultiAgentOrchestrator que implementa fan‑out/fan‑in.
- TaskManager y TaskOrchestratorIntegrator, que gestionan el ciclo de vida de las tareas, su estado y el streaming en tiempo real vía Server‑Sent Events (SSE).
- Herramientas del backend (PythonExecutor, WebScraper, FileProcessor, SearchEngine) registradas bajo un ToolManager, con políticas de seguridad, timeouts y sanitización.
- Endpoints REST y SSE para la creación, ejecución, seguimiento y consulta de tareas.
- Memoria vectorial con EmbeddingService y VectorStore para almacenamiento y búsqueda semántica en tablas documents, document_chunks, messages y conversations.

Restricciones de diseño:
- La integración debe ser no intrusiva, respetando el modelo de fases del orquestador (reasoning, planning, execution, verification, completion).
- Se deben mantener los mecanismos de actualización y streaming SSE del TaskManager.
- Las herramientas deben permanecer bajo el sandboxing y las validaciones ya establecidas.

Resultados esperados:
- Exposición controlada de herramientas y recursos vía MCP, con descubrimiento, ejecución y notificaciones en tiempo real.
- Traducción de eventos del orquestador a notificaciones MCP y actualizaciones SSE.
- Persistencia y búsqueda semántica a través de recursos MCP sobre PostgreSQL + pgvector.
- Observabilidad y trazabilidad mejoradas, con métricas, logs y health checks alineados con el flujo de tareas.

La narrativa avanza desde el estado actual, hacia la propuesta de mapeo MCP y, finalmente, a su implementación, validación, operación y riesgos.

## 2. Estado actual: arquitectura y capacidades existentes

El sistema combina una capa de orquestación multi‑agente con tracking de tareas, streaming SSE, catálogo de herramientas y memoria vectorial. Esta base funcional permite paralelizar ejecuciones, validar calidad y sintetizar resultados, al tiempo que conserva un registro de tareas y su progreso.

### 2.1 Multi‑agente y flujo fan‑out/fan‑in

El MultiAgentOrchestrator coordina las cinco fases —reasoning, planning, execution, verification y synthesis— de manera estructurada. En la fase de ejecución, el orquestador aplica fan‑out para tareas paralelas y fan‑in para consolidar resultados. La selección del executor adecuado se realiza con base en el mapa de herramientas requerido por cada delegación.

Para clarificar las entradas y salidas, la siguiente tabla resume el flujo por fase.

| Fase            | Entradas                                         | Salidas principales                                  |
|-----------------|---------------------------------------------------|------------------------------------------------------|
| Reasoning       | objetivo, contexto, historial                     | intent_analysis, strategy, enriched_context          |
| Planning        | strategy, enriched_context                        | plan, delegations, parallelizable_tasks              |
| Execution       | delegations, parallelizable_tasks                 | executions (paralelas/secuenciales), resultados      |
| Verification    | execution_results, trajectory                     | approval, quality_metrics, recommendations           |
| Synthesis       | reasoning, planning, execution, verification      | synthesis, quality_score, approved                   |

La selección de executor por herramienta:

| Herramienta          | Executor |
|----------------------|----------|
| python_executor      | code     |
| web_scraper          | web      |
| document_processor   | docs     |
| Otras               | general  |

Esta arquitectura permite controlar la concurrencia, balancear cargas y mantener criterios de calidad antes de la síntesis final.

### 2.2 TaskManager, streaming SSE e integrador

TaskManager define estados (created, started, in_progress, completed, error, cancelled) y fases de ejecución, actualiza el progreso y distribuye eventos a suscriptores. El endpoint de streaming emite heartbeats para sostener la conexión y concluye al alcanzar completed, error o cancelled.

El integrador TaskOrchestratorIntegrator conecta el orquestador con el TaskManager, ejecutando tareas de forma asíncrona, propagando el progreso por fase y gestionando cancelaciones.

### 2.3 Herramientas y seguridad

La plataforma integra herramientas con registro centralizado, ejecución segura, estadísticas y health checks. BaseTool aporta sanitización de entradas y validación de URLs; PythonExecutor añade sandboxing, restricción de módulos y builtins, y límites de tiempo.

Inventario de herramientas y políticas:

| Herramienta      | Función principal                     | Políticas de seguridad clave                    |
|------------------|---------------------------------------|-------------------------------------------------|
| PythonExecutor   | Ejecución segura de código Python     | Sandboxing, módulos/builtins restringidos       |
| WebScraper       | Scraping y extracción de contenido web| Validación de URL, sanitización de entradas     |
| FileProcessor    | Procesamiento de archivos              | Validación de rutas/formatos, límites de tamaño |
| SearchEngine     | Búsqueda web                           | Rate limiting, validación de consultas          |
| ToolManager      | Registro/ejecución/estadísticas       | Health checks, listas permitidas, timeouts      |

Estas defensas reducen la superficie de ataque y permiten observabilidad operativa por herramienta.

### 2.4 Memoria vectorial: tablas y capacidades

La memoria vectorial utiliza PostgreSQL + pgvector con tablas para documents, document_chunks y messages. Se crean índices HNSW para búsqueda vectorial rápida y filtros por metadatos. La búsqueda semántica se basa en similitud coseno; las operaciones de almacenamiento y consulta se realizan con parámetros de usuario, conversación y tipo de contenido.

Resumen de tablas:

| Tabla              | Columna vectorial           | Índice         | Propósito                                |
|--------------------|-----------------------------|----------------|-------------------------------------------|
| documents          | —                           | —              | Metadatos de documentos                   |
| document_chunks    | embedding vector(384)       | HNSW           | Chunks con embeddings                     |
| messages           | embedding vector(384)       | —              | Mensajes con embeddings                   |
| conversations      | —                           | —              | Datos de conversación/sesión              |

Operaciones y parámetros típicos:

| Operación             | Parámetros principales                                        |
|----------------------|---------------------------------------------------------------|
| store_document       | title, content, metadata, chunk_strategy                      |
| store_message        | conversation_id, role, content, agent_id, user_id             |
| semantic_search      | query, limit, user_id, conversation_id, content_type, time_range |

## 3. Requisitos para integrar un servidor MCP

La integración con MCP debe formalizar contratos en torno a herramientas, recursos y prompts; definir mecanismos de transporte (stdio y HTTP + SSE) para compatibilidad local y remota; y establecer negociación de versión de protocolo y capacidades.

Matriz de capacidades MCP:

| Capacidad     | Descripción                                      | Métodos/Eventos principales     |
|---------------|--------------------------------------------------|----------------------------------|
| Tools         | Funciones ejecutables para acciones externas     | tools/list, tools/call           |
| Resources     | Datos de contexto accesibles por los clientes    | resources/list, resources/get    |
| Prompts       | Plantillas de interacción con LLMs               | prompts/list, prompts/get        |
| Notificaciones| Actualizaciones en tiempo real                   | notifications/*                  |
| Transporte    | Canales de comunicación                          | stdio, streamable HTTP + SSE     |

### 3.1 Primitivas MCP y contratos

Las herramientas deben declarar nombre, descripción y un inputSchema (JSON Schema) que valide argumentos. Los recursos exponen contenido con metadatos y deben soportar descubrimiento y recuperación. Las notificaciones permiten cambios dinámicos (por ejemplo, listChanged) sin polling. La gestión del ciclo de vida incluye initialize (negociación de capacidades) y notificaciones de estado.

Contratos de herramientas MCP:

| Campo         | Propósito                                         |
|---------------|----------------------------------------------------|
| name          | Identificador único de la herramienta              |
| title         | Nombre legible                                     |
| description   | Propósito y comportamiento                         |
| inputSchema   | Validación de argumentos de entrada                |

### 3.2 Transporte y negociación

Para entornos locales, stdio ofrece latencias mínimas; para despliegues remotos, HTTP con SSE habilita streaming y autenticación estándar. La negociación de versión (por ejemplo, una etiqueta de protocolo acordada) asegura compatibilidad entre cliente y servidor. La capa de datos se basa en JSON‑RPC 2.0 para solicitudes, respuestas y notificaciones, con semántica clara de métodos y errores.[^1][^2][^4]

La selección de transporte tiene implicaciones operativas:

| Entorno       | Transporte recomendado     | Ventajas                             | Consideraciones              |
|---------------|----------------------------|--------------------------------------|------------------------------|
| Local         | stdio                      | Bajo overhead, sin red               | Aislamiento por proceso      |
| Remoto        | HTTP + SSE                 | Streaming natural, auth HTTP         | Seguridad y escalabilidad    |

## 4. Diseño propuesto de integración MCP

El diseño se apoya en adaptadores que traducen llamadas MCP hacia el backend (TaskManager, ToolManager, VectorStore) y viceversa, con mapeos claros de herramientas y recursos, y correlación de eventos del orquestador con notificaciones MCP y actualizaciones SSE.

Mapeo backend → MCP:

| Componente        | Tipo MCP     | Operaciones principales                           |
|-------------------|--------------|---------------------------------------------------|
| ToolManager       | Tools        | list_tools, execute_tool, execute_multiple_tools  |
| TaskManager       | Resources    | create_task, get_status, list_tasks, stream       |
| Integrador        | Tools        | execute_task, cancel_task, get_progress           |
| VectorStore       | Resources    | store_document, store_message, semantic_search    |

### 4.1 Mapeo de herramientas backend → MCP

Cada herramienta se expone como tool MCP con inputSchema validado y límites de tiempo; los resultados se normalizan a una estructura tipo ToolResult (contenido, metadatos, éxito/fracaso).

Tabla de mapeo de herramientas:

| Herramienta     | Método MCP        | Input principal            | Output                                   |
|-----------------|-------------------|----------------------------|-------------------------------------------|
| PythonExecutor  | tools/call        | code, timeout              | contenido estructurado y logs             |
| WebScraper      | tools/call        | url, opciones              | texto limpio, metadatos de respuesta      |
| FileProcessor   | tools/call        | paths, encoding            | contenido de archivos, resumen            |
| SearchEngine    | tools/call        | query, sources             | resultados de búsqueda con enlaces        |
| ToolManager     | tools/list, call  | name, args                 | ToolResult y estadísticas de ejecución    |

### 4.2 Exposición de memoria vectorial como recurso MCP

Los recursos de vector store se presentan con capacidades de almacenamiento de documentos y mensajes, así como búsqueda semántica con filtros. Se exponen metadatos de operación (tiempo, resultados, scores) para mejorar la trazabilidad y el control de calidad.

Recursos de vector store:

| Recurso        | Métodos                 | Filtros soportados                                    |
|----------------|-------------------------|--------------------------------------------------------|
| documents      | resources/list, get     | user_id, conversation_id, content_type                 |
| messages       | resources/list, get     | conversation_id, role, agent_id, user_id               |
| search         | resources/get (query)   | user_id, conversation_id, content_type, time_range     |

### 4.3 Correlación de eventos del orquestador con MCP/SSE

Las fases del orquestador se traducen a notificaciones MCP y updates SSE. El heartbeat mantiene el stream vivo; la señal de fin se emite en estados completed, error o cancelled.

| Fase          | Notificación MCP             | Update SSE                              |
|---------------|------------------------------|-----------------------------------------|
| Reasoning     | notifications/reasoning      | {status, phase=reasoning, progress,…}   |
| Planning      | notifications/planning       | {status, phase=planning, progress,…}    |
| Execution     | notifications/execution      | {status, phase=execution, progress,…}   |
| Verification  | notifications/verification   | {status, phase=verification, progress,…}|
| Completion    | notifications/completion     | {status=completed, phase=completion,…}  |

La correlación asegura visibilidad uniforme del avance, tanto para clientes MCP como para consumidores SSE.

### 4.4 Seguridad y control de acceso

La seguridad se refuerza con autorización por usuario/sesión, sanitización sistemática de entradas, restricciones de módulos/builtins y timeouts en llamadas MCP. Se recomienda una política de lista de herramientas permitidas y auditorías de uso.

Controles de seguridad:

| Control                  | Aplicación                                  |
|--------------------------|----------------------------------------------|
| Autorización             | ACL por usuario/sesión                       |
| Sanitización             | BaseTool; validación de URLs                 |
| Sandboxing               | PythonExecutor (builtins/módulos restringidos) |
| Timeouts                 | Herramientas y llamadas MCP                  |
| Auditoría                | Logs por herramienta y recurso               |

### 4.5 Versionado, handshake y negociación de capacidades

El handshake inicial declara capacidades de servidor y cliente (por ejemplo, soporte de notificaciones listChanged), negocia la versión de protocolo y establece el canal de transporte. Un esquema de versionado semántico evita incompatibilidades y permite evolucionar la API sin romper clientes.[^2]

Secuencia de handshake:

| Paso                         | Acción                                           |
|-----------------------------|--------------------------------------------------|
| initialize                  | Cliente envía versión y capacidades              |
| capabilities exchange       | Servidor responde con serverInfo y capacidades   |
| notifications/initialized   | Cliente confirma listo para operar               |

## 5. Plan de implementación

Se propone un plan en fases que reduce riesgos y acelera la entrega de valor, combinando construcción de adapters, mapeos de herramientas, integración de streaming, pruebas y hardening.

Roadmap por hito:

| Hito                              | Entregables                                         | Dependencias                 |
|-----------------------------------|------------------------------------------------------|------------------------------|
| Adaptadores MCP                   | Módulos MCP→TaskManager/ToolManager/VectorStore      | Definición de contratos      |
| Mapeo de herramientas             | tools/list y tools/call con inputSchema              | Adaptadores base             |
| Streaming MCP↔SSE                | Notificaciones MCP y bridge con TaskManager          | Mapeo de herramientas        |
| Pruebas end‑to‑end                | Escenarios de tarea completa                         | Fases anteriores             |
| Observabilidad y health checks    | Métricas, logs, paneles                              | Integración de streaming     |

### 5.1 Hitos y tareas

- Definir contratos de herramientas y recursos MCP (nombres, descripciones, schemas).
- Implementar adapters MCP que traduzcan llamadas y eventos.
- Integrar el streaming MCP con SSE del TaskManager.
- Añadir métricas por fase/herramienta y paneles de salud.
- Ejecutar pruebas end‑to‑end con tareas reales.

### 5.2 Pruebas y validación

Tipos de prueba por componente:

| Tipo de prueba   | Componentes                              | Criterios                                 |
|------------------|------------------------------------------|-------------------------------------------|
| Unitarias        | Adapters MCP, ToolManager                 | Casos límite, validación de schemas       |
| Integración      | TaskManager, SSE                          | Consistencia de eventos y estados         |
| End‑to‑end       | Orquestador + MCP                         | Flujo completo fan‑out/fan‑in             |
| Seguridad        | Sanitización, autorización                | Bloqueos de patrones peligrosos           |
| Rendimiento      | Concurrencia, streaming                   | Latencia y estabilidad bajo carga         |

### 5.3 Observabilidad

Se definen métricas clave: latencia por fase, duración de streams, tasa de éxito por herramienta, tiempos de ejecución, uso de cache de embeddings y latencia de búsqueda semántica. Los logs estructurados incorporan IDs de tarea y conversación. Se habilita health check por componente (orquestador, TaskManager, ToolManager, VectorStore, servidor MCP).

Catálogo de métricas:

| Métrica                           | Descripción                                 | Fuente                   |
|-----------------------------------|---------------------------------------------|--------------------------|
| latency_phase_ms                  | Latencia por fase de agente                 | Orquestador              |
| streaming_duration_seconds        | Duración del stream SSE por tarea           | TaskManager              |
| tool_success_rate                 | Éxito por herramienta                       | ToolManager              |
| tool_avg_execution_time           | Tiempo medio de ejecución                   | ToolManager              |
| embeddings_cache_hit_ratio        | Aciertos del cache de embeddings            | EmbeddingService         |
| vector_search_latency_ms          | Latencia de búsqueda semántica              | VectorStore              |
| mcp_requests_per_minute           | Throughput de solicitudes MCP               | Servidor MCP             |
| mcp_error_rate                    | Tasa de errores por herramienta/endpoint    | Servidor MCP             |

## 6. Operación y escenarios de fallo

La operación debe anticipar fallos en embeddings, base de datos, herramientas y el propio servidor MCP. Se definen fallbacks determinísticos, degradación de capacidades y reintentos con backoff exponencial, junto con límites de concurrencia y políticas de cancelación.

Matriz de fallos y mitigaciones:

| Componente        | Fallo típico                         | Mitigación                                      |
|-------------------|--------------------------------------|-------------------------------------------------|
| Embeddings        | Servicio no disponible               | Vectores determinísticos; cache local           |
| VectorStore       | BD no disponible                     | Desactivar búsqueda; registrar para más tarde   |
| ToolManager       | Herramienta fallida                  | Reintentos; marcar como no disponible           |
| TaskManager       | Cliente desconecta                   | Heartbeats; cierre controlado                   |
| Servidor MCP      | Caída/sobrecarga                     | Modo degradado; limitar concurrencia            |

Backoff y reintentos:

| Estrategia             | Parámetro típico             | Aplicación                      |
|------------------------|------------------------------|---------------------------------|
| Exponencial            | 1s, 2s, 4s, máx. 30s         | Llamadas a herramientas        |
| Idempotencia           | task_id/conversation_id      | Creación de tareas             |
| Límite de concurrencia | N tareas simultáneas         | Fan‑out y MCP tools            |

## 7. Validación, KPIs y criterios de aceptación

Los KPIs miden latencia por fase, throughput, tasa de éxito de herramientas y calidad de resultados (scores del Verifier). Los criterios de aceptación se basan en no intrusión, trazabilidad completa y operación degradada controlada.

KPIs por componente:

| Componente       | KPI principal                         | Umbral objetivo               |
|------------------|---------------------------------------|-------------------------------|
| Orquestador      | latency_phase_ms                      | p95 < 2s por fase             |
| TaskManager      | streaming_duration_seconds            | < 300s por tarea típica       |
| ToolManager      | tool_success_rate                     | > 95%                          |
| VectorStore      | vector_search_latency_ms              | p95 < 500ms                   |
| Servidor MCP     | mcp_error_rate                        | < 1%                           |

Criterios de aceptación:
- Integración no intrusiva, sin modificar el contrato de fases del orquestador.
- Trazabilidad con IDs de tarea/conversación en todos los eventos MCP y SSE.
- Fallbacks operativos y degradación controlada cuando falten servicios.
- Observabilidad completa con métricas, logs y health checks.

## 8. Riesgos y mitigaciones

Riesgos técnicos:
- Sobrecarga por encadenamiento de llamadas MCP.
- Latencias adicionales por transporte HTTP + SSE.
- Compatibilidad de versiones y evolución de contratos MCP.

Riesgos de seguridad:
- Superficie de ataque ampliada en herramientas expuestas.
- Autorización insuficiente entre usuarios/sesiones.
- Sanitización incompleta de entradas a herramientas.

Riesgos operativos:
- Complejidad de mantenimiento y versionado.
- Dependencia del transporte (stdio/HTTP+SSE).
- Gestión de índices vectoriales y tuning de rendimiento.

Registro de riesgos:

| Riesgo                              | Prob. | Impacto | Mitigación                                      | Dueño         |
|-------------------------------------|-------|---------|-------------------------------------------------|---------------|
| Encadenamiento de llamadas          | Media | Media   | Límites de concurrencia y caching               | Backend Lead  |
| Latencia transporte HTTP+SSE        | Media | Media   | Selección adecuada de transporte; optimización  | Architect     |
| Compatibilidad MCP                  | Media | Media   | Handshake y versionado semántico                | Architect     |
| Seguridad de herramientas           | Media | Alta    | Sanitización, sandboxing, ACL, auditoría        | Security Lead |
| Tuneo de índices vectoriales        | Baja  | Media   | Revisión de esquemas e índices HNSW             | DBA           |
| Mantenimiento y versionado          | Media | Media   | Contratos documentados y pruebas contractuales  | Engineering Mgmt |

## 9. Apéndices técnicos

### A. Endpoints y contratos relevantes
- POST /api/v1/tasks/create, POST /api/v1/tasks/execute, GET /api/v1/tasks/{id}/stream, GET /api/v1/tasks/{id}/status, GET /api/v1/tasks/{id}/results, DELETE /api/v1/tasks/{id}, GET /api/v1/tasks/list.

### B. Tablas y columnas de la base de datos
- documents: metadatos de documentos.
- document_chunks: embedding vector(384), metadatos e índices HNSW.
- messages: embedding vector(384) y metadatos por conversación.
- conversations: datos de sesión y conversación.

### C. Modelos de request/response y eventos SSE
- TaskRequest, TaskResponse, TaskUpdate; eventos “data: …”, heartbeats y “data: [DONE]”.

### D. Lista y mapeo de herramientas
- PythonExecutor → tool MCP con inputSchema (code, timeout).
- WebScraper → tool MCP (url, opciones).
- FileProcessor → tool MCP (paths, encoding).
- SearchEngine → tool MCP (query, sources).
- ToolManager → tools/list y tools/call con estadísticas.

Inventario detallado:

| Herramienta     | Descripción                       | Seguridad                         | Timeouts         | Notas                 |
|-----------------|-----------------------------------|-----------------------------------|------------------|-----------------------|
| PythonExecutor  | Código Python seguro              | Módulos/builtins restringidos     | 30–60s           | Captura de stdout     |
| WebScraper      | Scraping y extracción             | Validación de URL, sanitización   | 30s              | Límite de contenido   |
| FileProcessor   | Lectura y procesamiento de archivos| Validación de rutas y formatos    | 30s              | Vista previa limitada |
| SearchEngine    | Búsqueda web                      | Validación de consultas           | 30s              | Rate limiting         |
| ToolManager     | Registro y ejecución central      | Health checks, listas permitidas  | N/A              | Estadísticas y auditoría |

Tablas y columnas con índices:

| Tabla            | Columna vectorial        | Índice             | Notas                         |
|------------------|--------------------------|--------------------|-------------------------------|
| document_chunks  | embedding vector(384)    | HNSW               | vector_cosine_ops             |
| messages         | embedding vector(384)    | —                  | Filtrado por conversación     |
| documents        | —                        | —                  | Metadatos de usuario/convers. |

Contratos SSE y modelos:

| Modelo         | Campos principales                                              |
|----------------|-----------------------------------------------------------------|
| TaskUpdate     | task_id, status, phase, progress, message, result, metadata, timestamp |
| TaskResponse   | conversation_id, status, result, error, metadata                |
| TaskRequest    | objetivo, contexto, user_id, stream                             |

## Brechas de información

- No se dispone de la especificación formal de API del servidor MCP objetivo ni del contrato detallado de sus recursos y herramientas.
- Falta el inventario definitivo de herramientas MCP disponibles y sus esquemas de entrada/salida.
- No hay una configuración de autenticación/autorización específica para el servidor MCP (tokens, scopes, políticas).
- No se conocen las métricas operativas actuales del orquestador bajo carga para calibrar límites de concurrencia MCP.
- Falta la estrategia de versionado MCP y handshake/negotiation de capacidades en el entorno objetivo.
- No se ha definido la compatibilidad exacta entre dimensiones de embeddings y tipos vectoriales de pgvector en el despliegue final.

## Conclusión

La integración propuesta convierte el ecosistema multi‑agente en un servidor MCP interoperable sin alterar su núcleo operativo. La clave del éxito reside en contratos claros de herramientas y recursos, una capa de adapters disciplinada, transporte adecuado al entorno, controles de seguridad en profundidad y una observabilidad que correlacione eventos MCP con las fases del orquestador. Con un plan de implementación incremental y validación rigurosa, el sistema podrá beneficiarse de la extensibilidad y estandarización de MCP, manteniendo la robustez y el rendimiento actuales.

## Referencias

[^1]: Model Context Protocol (sitio oficial). https://modelcontextprotocol.io/
[^2]: Especificación MCP: Transports (HTTP+SSE, stdio). https://modelcontextprotocol.io/specification/2025-06-18/basic/transports
[^3]: Google Cloud: ¿Qué es MCP? https://cloud.google.com/discover/what-is-model-context-protocol
[^4]: JSON‑RPC 2.0 Specification. https://www.jsonrpc.org/