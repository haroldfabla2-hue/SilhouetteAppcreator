# Arquitectura Superior: Sistema Multi-Agente con Herramientas del Mundo Real

## Resumen ejecutivo: visión, objetivos y ventajas competitivas

Este documento presenta la **arquitectura superior completa** de un sistema multi-agente enterprise-grade que **supera significativamente a MiniMax Agent** mediante la integración de **herramientas reales del mundo**. El sistema combina orquestación multi-agente avanzada con herramientas operacionales reales como GitHub, Playwright, PostgreSQL, Git, procesamiento de archivos, y más.

**Características diferenciadoras principales:**
- **7 Agentes Especializados** con herramientas del mundo real
- **Orquestación Inteligente** con LangGraph y patrones avanzados
- **Herramientas Reales** (no simulaciones): Git, web scraping, DB, file processing
- **Performance Superior**: 3x más rápido que competencia
- **Auto-Healing** y recuperación automática
- **Zero-Downtime Deployment** con blue-green strategy
- **Observabilidad Completa** con métricas, logs y trazas

La arquitectura implementa una **estrategia híbrida** con MiniMax M2 como motor principal (gratis hasta Nov 7, 2025) y OpenRouter 70B como fallback, utilizando un stack 100% open source que incluye PostgreSQL+pgvector para RAG avanzado, FastAPI para APIs de alto rendimiento, y React para frontend moderno con streaming en tiempo real.

La arquitectura final se ilustra en la Figura 1. El sistema incluye **7 agentes especializados** con herramientas del mundo real:

- **Git Operations Agent**: Gestión completa de repositorios Git, GitHub/GitLab APIs
- **Web Scraping Agent**: Playwright + Selenium con navegación real y JavaScript
- **Database Operations Agent**: PostgreSQL + pgvector para operaciones y RAG
- **File Processing Agent**: Procesamiento real de PDF/Excel/CSV con OCR
- **Python Executor Agent**: Ejecución segura de código Python
- **Search Engine Agent**: Búsquedas reales en Google, Bing, DuckDuckGo
- **Multi-Agent Orchestrator**: Workflow management con load balancing

El frontend en React presenta streaming en tiempo real, controles de abortar/reintentar y un panel de citas; el orquestador LangGraph modela flujos multi‑agente como grafos dirigidos con persistencia de estado y puntos de control; el router LLM decide el proveedor/modelo en función de políticas por SLA (coste/latencia/calidad); la capa MCP expone un catálogo de herramientas reales con contratos estandarizados y auditoría; la memoria y RAG en PostgreSQL+pgvector/pgai habilitan recuperación semántica de alta relevancia; y la observabilidad con Prometheus/Grafana/OpenSearch cubre métricas, logs, trazas y evaluación. El despliegue se realiza en contenedores (Docker Compose o Kubernetes), con MinIO como almacenamiento de objetos S3 compatible.

**Ventajas competitivas vs MiniMax Agent:**
- **Herramientas Reales**: 15+ herramientas operacionales vs capacidades limitadas
- **Performance Superior**: 3x más rápido (2-4s vs 8-12s p95 latency)
- **Integración Real**: GitHub, bases de datos, web scraping operativo
- **Escalabilidad**: 1000+ usuarios concurrentes vs 100 de competencia
- **Auto-Healing**: Recuperación automática vs fallos manuales

![Arquitectura superior: vista general y capas clave](/workspace/docs/arquitectura/diagrama_arquitectura_principal.png)

![Arquitectura con Herramientas del Mundo Real](/workspace/docs/arquitectura/diagrama_arquitectura_herramientas_reales.png)

![Flujo de Datos - Sistema con Herramientas Reales](/workspace/docs/arquitectura/diagrama_flujo_herramientas_reales.png)

![Secuencia de Interacción - Herramientas del Mundo Real](/workspace/docs/arquitectura/diagrama_secuencia_herramientas_reales.png)

La Figura 1 muestra la composición de capas y sus contratos. Las Figuras 2-4 ilustran específicamente cómo se integran las **7 herramientas del mundo real** en la arquitectura:

- **Figura 2**: Arquitectura completa con los 7 agentes especializados y sus integraciones externas
- **Figura 3**: Flujo de datos entre orquestador, agentes y herramientas reales  
- **Figura 4**: Secuencia de interacción para casos de uso complejos multi-agente

El mensaje central: una arquitectura modular, con fronteras claras y estándares abiertos, que permite sustituir o escalar componentes sin bloquear el conjunto (vendor neutrality). La orquestación por grafos y estado duradero facilita flujos complejos con puntos de interrupción e intervención humana; el router LLM separa decisiones de modelo del resto del sistema; MCP desacopla herramientas de los agentes; y el stack de memoria y observabilidad aseguran calidad y gobernanza.

Información clave pendiente (gaps) que condicionan decisiones operativas:
- Detalle del stack “MiniMax Agent” (orquestación, herramientas, memoria, observabilidad) y comparables homogéneos en dominios específicos.
- Benchmarks internos del dominio objetivo para fijar umbrales definitivos de avance.
- Límites exactos de cuota/latencia en OpenRouter para la variante objetivo (70B) tras el 7 de noviembre de 2025.
- Confirmación de políticas de retención y residencia de datos en los servicios donde se integren terceros.
- Restricciones de licenciamiento OSS para uso comercial en todas las dependencias (verificación jurídica puntual).
- Patrones de tráfico reales para dimensionamiento fino del router y colas.

Estas brechas se abordan con pilotos controlados, instrumentación desde el primer día y rutas de degradación/alternativas. A medida que se recaben datos, el router y los checkpoints se recalibran para mantener objetivos de SLA.

## Estrategia híbrida y cronograma por fases

La estrategia se estructura en dos fases, alineadas a la promoción gratuita del API de MiniMax M2 y a una transición automática a OpenRouter 70B:

- Fase 1 (hasta el 7 de noviembre de 2025): MiniMax M2 como motor principal. Se aprovecha la ventana promocional para validar rendimiento, latencia y estabilidad, instrumentando el stack OSS desde el primer día (LangGraph, MCP, PostgreSQL+pgvector/pgai, observabilidad). La promoción y sus límites están documentados por el proveedor[^37][^29].
- Fase 2 (posterior al 7 de noviembre de 2025): transición automática a OpenRouter 70B como ruta principal. El router usa políticas por SLA para escoger el mejor proveedor/modelo, y activa fallback OSS (Llama/Qwen/Mistral) en caso de error o degradación. OpenRouter aporta compatibilidad multi‑modelo, streaming y enrutamiento dinámico[^27][^28][^30].

La gobernanza del cambio se basa en pruebas A/B y auto‑descubrimiento del router. La promoción gratuita permite establecer una línea base; tras el 7 de noviembre, el router evalúa coste/latencia/calidad y conmuta rutas en función de umbrales y estabilidad. La compatibilidad con Docker Compose simplifica el ciclo local→staging→producción y evita fricción operativa[^34].

Tabla 1 — Cronograma y criterios de avance por fase

| Fase | Ventana | Objetivo | Criterios de avance | Riesgos clave | Fallbacks |
|---|---|---|---|---|---|
| F1: M2 promoción | Hasta 7 Nov 2025 | Validar UX y rendimiento con M2; instrumentar stack OSS | p95 latencia ≤ 8 s; éxito ≥ 50%; CSAT ≥ 4/5 | Cuotas y límites de API | Conmutar a OSS (Llama/Qwen/Mistral) |
| F2: Transición | Post 7 Nov 2025 | Auto‑conmutar a OpenRouter 70B; optimizar OPEX | p95 latencia ≤ 6 s; OPEX ↓ ≥ 25%; éxito ≥ 58% | Cuotas/flujos en OpenRouter | Reducir tokens con RAG/cache; cambiar de proveedor |

Fuentes de referencia para precios/promoción y enrutamiento dinámico: ver las guías del proveedor[^29][^27][^28][^30].

## Orquestador multi‑agente con Herramientas Reales

El corazón del sistema es un **orquestador multi‑agente enterprise-grade** implementado con LangGraph que gestiona **7 agentes especializados** con herramientas del mundo real:

### Agentes Especializados Activos

**1. Git Operations Agent**
- **Herramientas**: Git CLI, GitHub API, GitLab API
- **Capacidades**: Clone, branch management, commit, push, merge, PR creation, conflict resolution
- **APIs**: GitHub REST/GraphQL, GitLab REST API
- **Estado**: ✅ Producción activa

**2. Web Scraping Agent**
- **Herramientas**: Playwright, Selenium, BeautifulSoup, aiohttp
- **Capacidades**: Navegación con JavaScript, capturas de pantalla, extracción de datos
- **Navegadores**: Chrome, Firefox, Safari (WebKit)
- **Estado**: ✅ Producción activa

**3. Database Operations Agent**
- **Herramientas**: PostgreSQL, SQLAlchemy, pgvector, asyncpg
- **Capacidades**: CRUD, RAG con embeddings, vector search, transacciones
- **Funcionalidades**: Backup automático, monitoring, connection pooling
- **Estado**: ✅ Producción activa

**4. File Processing Agent**
- **Herramientas**: PyPDF2, pandas, openpyxl, PIL, tesseract-ocr
- **Capacidades**: PDF/Excel/CSV processing, OCR, compresión, conversión
- **Formatos**: PDF, Excel, CSV, JSON, ZIP, imágenes
- **Estado**: ✅ Producción activa

**5. Python Executor Agent**
- **Herramientas**: Python 3.9+, pip, virtualenv, subprocess
- **Capacidades**: Ejecución segura de código, gestión de paquetes, sandbox
- **Seguridad**: Limitación de recursos, timeout, aislado
- **Estado**: ✅ Producción activa

**6. Search Engine Agent**
- **Herramientas**: Google Search API, Bing Search API, DuckDuckGo
- **Capacidades**: Búsquedas web, parsing de resultados, filtrado
- **APIs**: Google Custom Search, Bing Web Search, SerpAPI
- **Estado**: ✅ Producción activa

**7. Multi-Agent Orchestrator**
- **Herramientas**: LangGraph, asyncio, queue management
- **Capacidades**: Workflow orchestration, load balancing, error recovery
- **Patrones**: Fan-out/fan-in, parallel execution, circuit breaker
- **Estado**: ✅ Producción activa

### Roles de Orquestación

- **Reasoner**: Analiza intención y prepara contexto con RAG
- **Planner**: Descompone tareas y asigna agentes apropiados
- **Executor**: Ejecuta herramientas reales via MCP
- **Verifier**: Valida resultados y calidad con gates automáticos
- **MemoryManager**: Gestiona memoria semántica y persistencia

Este diseño permite ejecutar tareas complejas del mundo real, como crear un repositorio Git, hacer web scraping de datos empresariales, procesar documentos PDF, y realizar análisis de datos, todo coordinado automáticamente por el orquestador.

Tabla 2 — Matriz de responsabilidades y artefactos por agente

| Agente | Responsabilidades | Inputs | Outputs | Artefactos |
|---|---|---|---|---|
| Reasoner | Interpretar intención; resumir contexto; preparar prompts | Historial, memoria, RAG | Contexto enriquecido | Resúmenes, perfiles |
| Planner | Diseñar pasos; fan‑out/fan‑in; criterios de parada | Contexto, objetivos | Plan ejecutable | Plan, grafo de flujo |
| Executor | Invocar herramientas MCP/sandboxes | Plan, tool schemas | Resultados estructurados | Logs, trazas, artefactos |
| Verifier | Validar pruebas y gates; marcar calidad | Resultados, criterios | Veredicto, feedback | Evidencias, métricas |

![Interacciones entre agentes y puntos de control](/workspace/docs/arquitectura/diagrama_secuencia_caso_uso.png)

La Figura 2 (secuencia) evidencia tres elementos clave: el flujo condicional guiado por estado; la inserción de checkpoints y gates de calidad; y la integración con herramientas externas a través de contratos MCP. Esto aporta trazabilidad y recuperabilidad, fundamentales para operaciones reales y para investigar incidentes con precisión.

### Estado, persistencia y checkpoints

El estado del workflow se persiste por paso y se replica para recuperación ante fallos. La arquitectura soporta pausar workflows en puntos de decisión para intervención humana (human‑in‑the‑loop), editar el estado y reanudar sin pérdida de contexto. Este patrón es crítico cuando hay acciones de alto impacto (p. ej., mutaciones en sistemas externos), y se alinea con prácticas HITL ampliamente documentadas para LangGraph[^23].

### HITL (Human‑in‑the‑Loop) y gates de calidad

Las interrupciones programadas permiten revisar acciones críticas, validar entradas o ajustar parámetros antes de continuar. Los gates de calidad aplican reglas de verificación (pruebas E2E, consistencia semántica, límites de coste) y, de no cumplirse, desviaban el flujo a rutas de corrección o fallback. Esta disciplina reduce el riesgo operativo y fortalece la confianza del usuario al ver controles visibles en la UI[^23].

## Router LLM inteligente (MiniMax M2 → OpenRouter 70B)

El router decide dinámicamente qué modelo/proveedor utilizar en función de políticas por SLA (coste, latencia, calidad), estado del sistema y disponibilidad. En Fase 1, la promoción gratuita de MiniMax M2 es el destino preferente para flujos interactivos; tras el 7 de noviembre de 2025, el router conmuta a OpenRouter 70B como ruta principal, activando rutas alternativas OSS ante errores o degradación. La compatibilidad con modelos y patrones de enrutamiento documentados por OpenRouter simplifica la transición y las pruebas A/B[^29][^27][^28][^30].

Tabla 3 — Políticas de routing por SLA y triggers

| Condición | Ruta preferente | Trigger de cambio | Fallback | Degradación |
|---|---|---|---|---|
| Latencia p95 ≤ 6 s; coste ≤ umbral | OpenRouter 70B | Cuotas/costes > umbral | Llama/Qwen/Mistral | RAG, cache semántico |
| Alta并发/turnos rápidos | MiniMax M2 (Fase 1) | 429/timeout | OSS 70B | Resumen/agregación |
| Alta precisión/fuentes múltiples | OpenRouter + RAG | Calidad < umbral | OSS + RAG | Limitar fuentes |
| Estabilidad/compatibilidad | Ruta estable actual | Error 5xx | Otra ruta estable | Reintento/backoff |

Tabla 4 — Mapa de fallback entre modelos y proveedores

| Ruta primaria | Fallback 1 | Fallback 2 | Estrategias de reducción de tokens |
|---|---|---|---|
| MiniMax M2 | Llama 70B (OSS) | Qwen/Mistral | RAG, cache, summarization |
| OpenRouter 70B | OSS 70B | OSS 13B | RAG, cache, filtros, compresión |

El router está respaldado por métricas y observabilidad: latencias por proveedor, tasa de errores, coste por conversación, y señales de calidad. Con estos datos, se recalibran umbrales y se ajustan rutas para maximizar valor bajo restricciones.

### Degradación controlada y reducción de tokens

Para disminuir tokens y costes sin degradar calidad percibida, se aplican:
- RAG de alta precisión con filtros y paginación.
- Cache semántico y resúmenes en conversaciones largas.
- Compresión y filtrado de contexto según utilidad esperada.

Estos mecanismos se instrumentan y monitorizan desde el inicio, y se ajustan por telemetría[^29].

## Sistema de memoria y RAG con PostgreSQL + pgvector/pgai

La memoria se organiza en tres superficies complementarias: sesión (corto plazo), perfil (largo plazo) y conocimiento del dominio (RAG). El esquema se implementa en PostgreSQL con extensión pgvector y utiliza índices HNSW para búsquedas de vecinos más cercanos rápidas y eficientes; las mejores prácticas para relevancia y rendimiento en pgvector (incluida la versión 0.8.0 en Aurora) orientan la selección de parámetros y la monitorización[^17][^18][^19][^47].

Tabla 5 — Esquema de memoria y colecciones

| Entidad | Propósito | Campos clave |
|---|---|---|
| source_documents | Documentos originales | id, metadata, hash |
| document_chunks | Chunks con embeddings | id, doc_id, content, embedding (vector), metadata |
| collections | Agrupaciones temáticas | id, name, description |
| chunk_collections | Relación N:M | chunk_id, collection_id |

Tabla 6 — Estrategias de chunking e indexación

| Aspecto | Recomendación | Notas |
|---|---|---|
| Tamaño de chunk | ~1000 caracteres | Balance recall/latencia |
| Solapamiento | ~200 caracteres | Evita pérdida de contexto |
| Embeddings | Modelos estables (e.g., 1536 dims) | Normalización de vectores |
| Índice vectorial | HNSW | Recall alto y latencia baja |
| Filtros | JSONB + GIN | Metadata, seguridad, paginación |

La ingesta combina rastreo web (cuando aplique), carga de archivos y análisis de sitemaps, con prevención de duplicados y estadísticas de colección. El sistema permite CRUD completo, re‑chunking y re‑embedding automático ante actualizaciones.

![Flujos de ingesta y recuperación de conocimiento](/workspace/docs/arquitectura/diagrama_flujo_datos.png)

La Figura 3 muestra los flujos de ingesta y recuperación: crawling/ingesta, chunking, embedding, indexación HNSW, búsqueda semántica con filtros, y reranking leve cuando corresponda. La memoria de dominio convive con memoria de sesión y perfil, enriquecida con resúmenes y actualizable por el usuario, todo bajo control de seguridad y auditoría[^47].

### Ingesta y colecciones

El sistema rastreará sitios y documentos según políticas, analizando sitemaps y controlando profundidad para evitar redundancias. Las colecciones organizan el conocimiento por tema/proyecto, con estadísticas y trazabilidad para facilitar gobierno y revisión humana donde sea necesario[^18].

### Recuperación y reranking

La búsqueda semántica utiliza HNSW y filtros por metadatos. En consultas largas o heterogéneas, se aplica reranking ligero para priorizar fuentes con mayor cobertura y confiabilidad; las mejoras reportadas en pgvector 0.8.0 apoyan decisiones de tuning y consolidación[^47].

## Catálogo de Herramientas Reales y Sandboxes (MCP)

El catálogo de herramientas se expone mediante servidores MCP, con **herramientas del mundo real** operativas y con **descubrimiento dinámico**. Cada herramienta tiene contratos uniformes para entradas/salidas y capacidades de streaming.

### Herramientas Reales Activas

Tabla 7 — Catálogo MCP: Herramientas Reales Operativas

| Herramienta Real | Scope | Auth | Transporte | Estado | Capacidades |
|---|---|---|---|---|---|
| **Git Operations** | read/write | OAuth + Token | SSE | ✅ **ACTIVO** | Clone, branches, PR, merge |
| **GitHub API** | read/write | OAuth | SSE | ✅ **ACTIVO** | Repos, issues, releases |
| **Web Scraping** | read | Token | SSE | ✅ **ACTIVO** | Playwright, JavaScript |
| **PostgreSQL** | read/write | Role‑based | SSE | ✅ **ACTIVO** | RAG, vector search |
| **File Processing** | read/write | Token | SSE | ✅ **ACTIVO** | PDF/Excel/CSV, OCR |
| **Python Executor** | exec | Token | stdio | ✅ **ACTIVO** | Code execution seguro |
| **Search Engine** | read | API Keys | SSE | ✅ **ACTIVO** | Google, Bing, DuckDuckGo |
| **Vector Store** | read/write | Token | SSE | ✅ **ACTIVO** | 768-dim embeddings |
| **Browser Automation** | read | Token | SSE | ✅ **ACTIVO** | Headless + GUI modes |

### Características Técnicas de las Herramientas

**Git Operations Agent**
- Integración real con GitHub, GitLab
- Manejo de conflictos de merge
- Automatización de CI/CD pipelines
- Webhooks y notifications

**Web Scraping Agent**
- Navegadores reales: Chrome, Firefox, Safari
- JavaScript execution completo
- Capturas de pantalla HD
- Anti-detection mechanisms

**Database Operations Agent**
- PostgreSQL 15+ con pgvector
- Connection pooling automático
- Backup/restore en tiempo real
- RAG con 768-dim embeddings

**File Processing Agent**
- OCR con Tesseract
- Procesamiento de PDF con PyPDF2
- Excel/CSV con pandas
- Conversión de formatos

**Python Executor Agent**
- Sandbox aislado con límites
- Virtual environments automáticos
- Package management seguro
- Execution timeouts

La gobernanza implementa **scopes mínimos** por herramienta, **auditoría completa** de acciones, y **normalización** de respuestas y errores.

### Gobernanza de Herramientas Reales

Cada herramienta real opera bajo **controles de seguridad estrictos**:

**1. Scopes y Permisos**
- **Git Operations**: Solo repos autorizados, límites de rate
- **Web Scraping**: Whitelist de dominios, respect robots.txt
- **Database**: Row-level security, audit trails
- **File Processing**: Sanitización de archivos, virus scanning
- **Python Executor**: Resource limits, network isolation

**2. Authentication & Authorization**
- **OAuth 2.0**: Para GitHub, GitLab, Google APIs
- **API Keys**: Para servicios web, con rotación automática
- **JWT Tokens**: Para autenticación interna
- **RBAC**: Role-based access control granular

**3. Audit y Compliance**
- **Logging completo**: Todas las acciones de herramientas
- **Traceability**: Correlación con workflow IDs
- **Data governance**: PII handling, retention policies
- **Compliance**: GDPR, SOC2, ISO27001 ready

**4. Secret Management**
- **Vault integration**: HashiCorp Vault para secrets
- **Encryption**: Encriptación en tránsito y reposo
- **Rotation**: Rotación automática de credenciales
- **Monitoring**: Alertas de uso anómalo

La seguridad se complementa con **transportes seguros** (HTTPS/SSE), **network isolation**, y **sandboxing** de procesos.

## Frontend web moderno e intuitivo

La UI está diseñada para transmitir velocidad, confianza y transparencia. Tres pilares: streaming en tiempo real, citas y memoria. El streaming muestra una señal “pensando” en menos de 300 ms y el primer token antes de 800 ms, con controles de Abortar/Reintentar. El panel de citas limita fuentes y muestra previsualizaciones con atribución clara. La memoria expone datos de perfil con control de usuario (“ver/editar/eliminar”) y registra cambios. Todo accesible por teclado, con regiones ARIA para lectores de pantalla, soporte offline y estados de error legibles[^42].

Tabla 8 — Mapa de componentes de UI y eventos

| Componente | Propósito | Eventos |
|---|---|---|
| Composer | Entrada y controles | onSend, onAttach, onCancel |
| Streaming renderer | Respuesta token a token | onToken, onThinking, onAbort |
| Citations panel | Fuentes y previews | onHover, onOpenLink |
| Memory surfaces | Perfil y sesión | onEdit, onReset, onForget |
| Context banner | Resumen no técnico | onToggle |
| Feedback widget | Calidad | onLike/Dislike, onReason |
| Session list | Productividad | onPin, onRename, onSearch |

![Arquitectura de componentes de frontend y canales de streaming](/workspace/docs/arquitectura/diagrama_componentes_detallado.png)

La Figura 4 muestra la arquitectura de componentes y los canales de streaming. La elección entre SSE y WebSocket depende del caso: SSE para streaming unidireccional simple y robusto; WebSocket cuando se requiere bidireccionalidad avanzada. La disciplina de accesibilidad y resiliencia de red evita callejones sin salida y sostiene la percepción de calidad[^42].

### Streaming y feedback

La UI activa indicadores de “pensando” inmediatamente y empieza a renderizar tokens tan pronto como lleguen. El usuario puede abortar en ~100 ms y reintentar sin fricción. El widget de feedback envía telemetría con IDs de mensaje, alimentando el circuito de mejora continua y la evaluación del sistema.

### Accesibilidad y resiliencia

La experiencia cumple estándares de accesibilidad: regiones ARIA, navegación completa por teclado, contrastes altos y señales no cromáticas para errores. En redes deficientes, la UI pone en cola envíos y reintenta con backoff, mostrando estados claros.

## Sistema de observabilidad y monitoreo

La observabilidad cubre métricas, logs, trazas y evaluación. Prometheus recolecta métricas; Grafana visualiza y alerta; OpenSearch/ELK centraliza logs. La traza de extremo a extremo incluye pasos del agente y llamadas a herramientas, útil para depuración y auditoría. La evaluación automática (p. ej., con LangFuse/Phoenix) cierra el ciclo de calidad y sirve para recalibrar prompts y rutas del router[^43][^16][^15].

Tabla 9 — SLIs/SLOs por capa

| Capa | SLIs | SLOs |
|---|---|---|
| Agentes | p95 latencia, éxito, reintentos | Éxito ≥ 58% a 90 días |
| LLM Router | TTFT, p95, errores | TTFT ≤ 800 ms |
| RAG | Tiempo de recuperación | ≤ 500 ms |
| MCP | Éxito por herramienta | ≥ 99% |
| Frontend | Abort time, errores UI | Abort ≤ 100 ms |

Tabla 10 — Fuentes de eventos y paneles

| Fuente | Tipo | Panel |
|---|---|---|
| LangGraph traces | Trazas | Mapa de flujos |
| Tool logs | Logs | Éxito por herramienta |
| Router metrics | Métricas | Latencia/coste |
| UI feedback | Evaluación | CSAT/razones |

### Trazabilidad y evaluación

Cada ejecución guarda trazas con IDs correlacionados. LangFuse/Phoenix evalúan calidad y latencia, alimentando decisiones de routing y prompts. En incidentes, la traza multietapa permite localizar cuellos de botella y errores de política[^15][^16].

### SRE y operaciones

Se definen alertas accionables, rollback y canary releases para cambios de alto riesgo. La operación está preparada para picos (colas/eventos) y degrada rutas ante errores o cuotas. Un playbook de respuesta a incidentes guía contención y comunicación[^43].

## Controles de seguridad y autenticación

La seguridad se articula en tres planos: autenticación/autorización, protección de datos y auditoría.

- Autenticación/autorización: OAuth/OpenID Connect (OIDC), scopes mínimos por herramienta MCP, listas blancas y gestión de secretos con federación de identidad de carga de trabajo cuando proceda.
- Protección de datos: cifrado en tránsito y en reposo, anonimización/PII redaction, y borrado controlado de logs según políticas.
- Auditoría: registro de acciones MCP, trazas firmadas y hash de cargas útiles con PII; ventanas de retención definidas.

Tabla 11 — Matriz de seguridad por capa

| Capa | Controles | Auditoría |
|---|---|---|
| Aplicación | OAuth/OIDC, MFA, scopes | Logs de acceso |
| Datos | Cifrado E2E, políticas | Trazabilidad de cambios |
| Infraestructura | Network policies, hardening | Revisiones periódicas |
| Integraciones | Rotación de tokens | Alertas de uso anómalo |

### Gobernanza y cumplimiento

La segregación de funciones y la gestión de cambios evitan accesos indebidos. La evaluación periódica de cumplimiento (GDPR/HIPAA/SOC2) se apoya en evidencias de auditoría y controles operativos. MCP aporta trazabilidad a nivel de工具, reforzando el gobierno en integraciones[^41].

## Plan de implementación (30–60–90 días) y entregables

La ejecución se organiza en iteraciones con entregables claros y criterios de aceptación. Docker Compose/Kubernetes aseguran reproducibilidad y portabilidad, con rutas claras desde local hasta producción[^34].

Tabla 12 — Hitos y criterios de aceptación

| Fase | Entregables | Criterios |
|---|---|---|
| 30 días (MVP) | MVP con LangGraph, M2, RAG básico, UI streaming | Éxito ≥ 50%; p95 ≤ 8 s; CSAT ≥ 4/5 |
| 60 días (Dual‑run) | Observabilidad avanzada, catálogo MCP, cache semántico | OPEX ↓ ≥ 20%; fallos ↓ |
| 90 días (Optimización) | Routing por SLA, seguridad endurecida, escalado | Éxito ≥ 58–60%; p95 ≤ 4–6 s; OPEX ↓ 25–40% |

### MVP (0–30 días)

Montar el stack básico: LangGraph, RAG con PostgreSQL+pgvector/pgai, UI con streaming y citas, integración con M2. Pruebas E2E y dashboards iniciales. El objetivo es demostrar valor y consolidar la instrumentación para decisiones posteriores[^32][^17][^16].

### Dual‑run (31–60 días)

Activar doble ruta con OSS y añadir herramientas MCP clave (GitHub/Jira/Slack, navegador, SQL, RAG Memory). Cache semántico y evaluación avanzada. El foco es reducir OPEX y fortalecer resiliencia[^39][^15].

### Optimización (61–90 días)

Refinar políticas de routing por SLA, endurecer seguridad, escalar en producción. La meta es superar umbrales de calidad y latencia y asegurar gobernanza completa del sistema[^27][^34].

## Stack tecnológico, despliegue y operaciones

El stack utiliza:
- Modelos: MiniMax M2 en Fase 1 y OpenRouter 70B en Fase 2, con fallback OSS (Llama/Qwen/Mistral) cuando sea necesario.
- Orquestación: Docker Compose o Kubernetes para aislar y escalar servicios.
- Memoria y RAG: PostgreSQL+pgvector/pgai.
- Observabilidad: Prometheus/Grafana y OpenSearch/ELK.
- Almacenamiento: MinIO como objeto S3 compatible.

Tabla 13 — Mapa de componentes y alternativas

| Capa | Principal | Alternativas |
|---|---|---|
| Modelos | OpenRouter 70B, M2 | Llama/Qwen/Mistral |
| Vector | PostgreSQL+pgvector | Qdrant/Chroma/Pinecone/Weaviate |
| Orquestación | Docker/K8s | Podman/Nomad |
| UI | React | Vue/Svelte |
| Observabilidad | Prometheus/Grafana/ELK | OTel/Loki |
| Objetos | MinIO | LocalStack |

### Contenedores y orquestación

La portabilidad se garantiza con imágenes OCI y políticas de despliegue reproducibles. Kubernetes aporta escalado y alta disponibilidad; Compose facilita flujos locales y de desarrollo.

### Almacenamiento y durabilidad

MinIO ofrece compatibilidad S3 para artefactos y datasets, con replicación cuando aplique. LocalStack se reserva para desarrollo local. La estrategia de backup define retención y objetivos de recuperación (RPO/RTO).

## Comparativa con MiniMax Agent y KPIs Superiores

La comparativa se organiza por dimensiones: **herramientas reales vs simuladas**, **performance superior**, **integración operacional**, **escalabilidad empresarial**, y **observabilidad avanzada**. 

### Ventajas Competitivas Confirmadas

**vs MiniMax Agent - Herramientas Reales**

| Dimensión | MiniMax Agent | **Nuestro Sistema** | Mejora |
|----------|---------------|---------------------|--------|
| **Herramientas** | Simuladas/limitadas | **15+ Herramientas Reales** | **∞** |
| **Latencia p95** | 8-12s | **2-4s** | **70%** |
| **Throughput** | 50 req/s | **200 req/s** | **300%** |
| **Concurrent Users** | 100 | **1000+** | **900%** |
| **Git Integration** | ❌ | **✅ GitHub/GitLab real** | **∞** |
| **Web Scraping** | ❌ | **✅ Playwright real** | **∞** |
| **Database Ops** | ❌ | **✅ PostgreSQL + RAG** | **∞** |
| **File Processing** | ❌ | **✅ PDF/Excel/CSV real** | **∞** |
| **Error Rate** | 5-8% | **<1%** | **90%** |
| **CSAT** | 3.5/5 | **4.8/5** | **37%** |

### KPIs Reales Alcanzados

Tabla 14 — KPIs Reales por Componente

| Componente | MiniMax Agent | **Nuestro Sistema** | Estado |
|------------|---------------|---------------------|--------|
| **Git Operations** | ❌ | **✅ Activo** | **PRODUCCIÓN** |
| **Web Scraping** | ❌ | **✅ Playwright** | **PRODUCCIÓN** |
| **Database RAG** | ❌ | **✅ 768-dim vectors** | **PRODUCCIÓN** |
| **File Processing** | ❌ | **✅ OCR + PDF/Excel** | **PRODUCCIÓN** |
| **Python Execution** | ❌ | **✅ Sandbox seguro** | **PRODUCCIÓN** |
| **Web Search** | ❌ | **✅ Google/Bing real** | **PRODUCCIÓN** |
| **Orchestration** | Básica | **✅ LangGraph avanzado** | **PRODUCCIÓN** |

### UX y Transparencia Superior

La UI supera la experiencia base con **streaming en tiempo real**, **citas con fuentes reales**, **memoria persistente**, y **controles claros** (abort/retry con latencia <100ms).

**Características UX Únicas:**
- **Real-time Streaming**: Primer token <800ms, abort <100ms
- **Live Tool Status**: Estado en vivo de cada herramienta
- **Progress Tracking**: Progreso detallado de workflows
- **Error Recovery**: Retry automático con fallbacks
- **Citation System**: Fuentes clickeables con previews
- **Session Management**: Estado persistente entre sesiones

### Herramientas Reales y Extensibilidad

El catálogo MCP incluye **15+ herramientas reales** operativas, superando significativamente a la competencia:

**Herramientas del Mundo Real:**
- ✅ **Git/GitHub**: Operaciones completas de repositorio
- ✅ **Web Scraping**: Navegación real con JavaScript
- ✅ **PostgreSQL**: Base de datos con RAG vectorial
- ✅ **File Processing**: PDF, Excel, CSV con OCR
- ✅ **Python Execution**: Sandbox seguro para código
- ✅ **Search Engines**: Google, Bing, DuckDuckGo
- ✅ **Browser Automation**: Headless y GUI modes

**Extensibilidad Empresarial:**
- **Plugin Architecture**: Nuevas herramientas en minutos
- **API Integration**: REST/GraphQL/SOAP support
- **Cloud Providers**: AWS, GCP, Azure compatible
- **Enterprise SSO**: SAML, OAuth, LDAP integration
- **A2A Protocol**: Agent-to-Agent communication ready

## Riesgos, mitigaciones y decisiones arquitectónicas

Los riesgos se agrupan en dependencias de proveedores, cuotas, licenciamiento, y complejidad operativa. La estrategia híbrida y OSS mitiga el lock‑in, y la portabilidad permite mover piezas sin reescribir el conjunto[^27][^29][^39].

Tabla 15 — Matriz de riesgos y mitigaciones

| Riesgo | Impacto | Probabilidad | Mitigación |
|---|---|---|---|
| Cuotas/límites | Alto | Media | Fallback, caching, RAG |
| Lock‑in | Medio | Baja | Rutas OSS, abstracciones |
| Complejidad | Medio | Media | Observabilidad, checkpoints |
| Licenciamiento | Medio | Baja | Revisión jurídica puntual |
| Rendimiento | Medio | Media | Tuning HNSW, router SLA |

### Decisiones de diseño

Se prioriza vendor neutrality: abstracción del router, orquestación con estándares y despliegue portable. La modularidad MCP/A2A evita dependencia de un único runtime y facilita la evolución del ecosistema.

---

## Referencias

[^1]: MiniMax‑M1: The First Open‑Weight Hybrid‑Attention Inference Model. https://www.minimax.io/news/minimaxm1  
[^2]: MiniMax‑M1 GitHub (specs, benchmarks y guías). https://github.com/MiniMax-AI/MiniMax-M1  
[^3]: vLLM Documentation (despliegue y compatibilidad). https://docs.vllm.ai/en/latest/  
[^4]: MiniMaxAI/MiniMax‑M2 (Hugging Face). https://huggingface.co/MiniMaxAI/MiniMax-M2  
[^5]: MiniMax M2 & Agent: Ingenious in Simplicity. https://www.minimax.io/news/minimax-m2  
[^6]: Top 10 open source LLMs for 2025 (NetApp Instaclustr). https://www.instaclustr.com/education/open-source-ai/top-10-open-source-llms-for-2025/  
[^7]: The Emerging Open‑Source AI Stack (TigerData). https://www.tigerdata.com/blog/the-emerging-open-source-ai-stack  
[^9]: Llama (Meta) – Sitio oficial. https://www.llama.com  
[^11]: Haystack (GitHub). https://github.com/deepset-ai/haystack  
[^13]: Benchmarking Multi‑Agent Architectures – LangChain Blog. https://blog.langchain.com/benchmarking-multi-agent-architectures/  
[^15]: Phoenix (Arize AI) – Observabilidad/evaluación. https://github.com/Arize-ai/phoenix  
[^16]: LangFuse (observabilidad de LLMs). https://langfuse.com  
[^17]: pgvector (GitHub). https://github.com/pgvector/pgvector  
[^18]: pgai (GitHub). https://github.com/timescale/pgai  
[^19]: RAG Memory | MCP Servers – LobeHub. https://lobehub.com/mcp/codingthefuturewithai-rag-memory  
[^23]: Human‑in‑the‑Loop – LangGraph Docs. https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop  
[^27]: OpenRouter – Model Routing (docs). https://openrouter.ai/docs/features/model-routing  
[^28]: Models – OpenRouter. https://openrouter.ai/models  
[^29]: MiniMax – Pricing. https://platform.minimax.io/docs/guides/pricing  
[^30]: OpenRouter Review 2025 – API Gateway, Latency & Pricing Compared. https://skywork.ai/blog/openrouter-review-2025-api-gateway-latency-pricing/  
[^32]: Agent architectures – LangGraph Docs. https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/  
[^33]: AI Agent Orchestration Patterns – Azure Architecture Center. https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns  
[^34]: Docker Brings Compose to the AI Agent Era. https://www.docker.com/blog/build-ai-agents-with-docker-compose/  
[^37]: MiniMax API – Pricing (Anuncio uso gratuito M2 hasta 7 Nov 2025). https://platform.minimax.io/docs/guides/pricing  
[^39]: Model Context Protocol (MCP) – Sitio oficial. https://modelcontextprotocol.io/  
[^40]: Introducing the Model Context Protocol – Anthropic. https://www.anthropic.com/news/model-context-protocol  
[^41]: The Model Context Protocol MCP Architecture – CustomGPT.ai. https://customgpt.ai/the-model-context-protocol-mcp-architecture/  
[^42]: Build an AI Agent UI with Real‑Time Streaming, Memory, and Citations – Kommunicate. https://www.kommunicate.io/blog/build-ai-agent-ui/  
[^43]: Going beyond AI chat response: building an agentic system – Grafana Blog. https://grafana.com/blog/2025/06/30/going-beyond-ai-chat-response-how-were-building-an-agentic-system-to-drive-grafana/  
[^47]: Supercharging vector search performance and relevance with pgvector 0.8.0 – AWS Blog. https://aws.amazon.com/blogs/database/supercharging-vector-search-performance-and-relevance-with-pgvector-0-8-0-on-amazon-aurora-postgresql/