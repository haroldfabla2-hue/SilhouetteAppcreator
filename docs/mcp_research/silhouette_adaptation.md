# Blueprint de adaptación y mejoras de la arquitectura MCP en Silhouette

## Resumen ejecutivo y objetivos

Silhouette se propone evolucionar hacia un sistema multiagente construido sobre el Model Context Protocol (MCP). La ambición es razonable y actual: estandarizar la conectividad con herramientas y datos, habilitar automatizaciones en entornos Windows y ofrecer un plano de seguridad y observabilidad de nivel enterprise. Para lograrlo, la arquitectura debe madurar cinco ejes interdependientes: el contrato de mensaje (McpMessage), el enrutamiento y la delegación (McpRouter), el registro de capacidades dinámico (Capability Registry), la observabilidad de extremo a extremo con OpenTelemetry (OTel) y la seguridad con redacción y políticas.

La propuesta que se presenta a continuación persigue tres resultados tangibles. Primero, trazabilidad robusta: cada solicitud debe poder seguirse desde el primer contacto hasta la ejecución final, con contextos distribuidos y correlación consistente entre logs, métricas y trazas. Segundo, delegación inteligente: el router debe comprender políticas (alcance, TTL, RPS, aprobación), ejecutar validaciones en el camino feliz y aplicar mitigaciones graduadas bajo estrés. Tercero, seguridad de datos y cumplimiento: la información sensible debe minimizarse, redactarse y gobernarse por políticas, con identidad, autorización y residencia de datos como principios rectores.

Nuestra estrategia de adopción por fases (Fase 0–4) encaja con el roadmap existente del proyecto. En Fase 0 se consolidan los contratos y la configuración; en Fase 1 se implementa el router y el registro de capacidades; en Fase 2 se habilitan agentes Windows como adaptadores seguros; en Fase 3 se activa el modo offline-first y la observabilidad; y en Fase 4 se refuerzan los controles de seguridad, redacción y políticas. Para acelerar el “time-to-value”, el plan sugiere comenzar con un MVP de routing con políticas base y trazabilidad mínima viable, seguido de la integración del registro de capacidades, la instrumentación OTel y el endurecimiento progresivo del plano de seguridad.

Los riesgos más relevantes están asociados a la latencia añadida por validaciones y redacción, la complejidad de la correlación de telemetría, la gobernanza de datos sensibles y la fricción operacional de agentes locales en Windows (PowerShell restringido, UI automation, Playwright). A medida que se avanza de MVP a producción, cada mitigación propuesta —cachés, batch de validaciones, propagación de contexto, aprobación humana, separación de dominios de claves— se introduce de manera controlada y orientada a métricas.

Para orientar la ejecución, la siguiente tabla sintetiza objetivos por componente, métricas objetivo y dependencias principales.

Tabla 1. Mapa de objetivos por componente, métrica objetivo y dependencias

| Componente                   | Objetivo principal                                | Métrica objetivo                         | Dependencias clave                                         |
|-----------------------------|----------------------------------------------------|------------------------------------------|------------------------------------------------------------|
| McpMessage                  | Contrato estable y extensible                      | Compatibilidad MCP; cobertura de esquemas| JSON Schema; versionado; convenciones de campos            |
| McpRouter                   | Delegación segura con validaciones y mitigaciones  | P95 < 100 ms (ops simples); error < 0.1% | Políticas (policies.yaml); Capability Registry; OTel       |
| Capability Registry         | Descubrimiento y versionado consistente            | 99.9% disponibilidad del registry        | SQLite + índices; health checks; estrategias de registro   |
| Observabilidad (OTel)       | Trazabilidad y correlación multiagente             | 100% de trazas correlacionadas           | Propagación W3C; Baggage; Collector; métricas/logs         |
| Seguridad y políticas       | Minimización y redacción; identidad y autorización | 0 incidentes de fuga; cumplimiento       | RedactionRules; TLS/mTLS; WDAC/AppLocker; DPAPI            |

Esta tabla sirve como marco de seguimiento. A lo largo del documento se detallan prácticas para cumplir estos objetivos, apoyándonos en las guías de mejores prácticas de MCP, la arquitectura del OpenTelemetry Collector y patrones de seguridad enterprise aplicables a flujos de agentes y herramientas.[^1][^11]

## Contexto y baseline de Silhouette

Silhouette asume MCP como protocolo base para conectar agentes con herramientas y datos. MCP organiza la interacción entre un Host MCP, Clientes MCP y Servidores MCP, definiendo primitivos de capa de datos (tools, resources, prompts) y una capa de transporte para stdio o HTTP con streaming. El flujo se completa con inicialización, negociación de capacidades, notificaciones y cierre. En la práctica, esta estructura ofrece una forma estandarizada de invocar herramientas, consultar recursos y utilizar prompts, con controles de seguridad y consentimiento integrados.[^2]

El proyecto Silhouette define un DTO de mensajería llamado McpMessage con campos de correlación (trace_id, parent_id), identidad (sender, receiver), objetivo (intent), capacidad (capability), contexto (context), carga útil (payload), resultado (result), adjuntos (attachments) y error normalizado (McpError). Sobre este contrato, se promueve la generación de esquemas JSON determinísticos (Silhouette.Mcp.SchemaGen) y se establece un sistema de políticas por intent (policies.yaml), que fija scope, ttl_s, rps y requires_approval, entre otros. El McpRouter, aún en estado incipiente, debe evolucionar hacia un componente que valide políticas, resuelva capacidades desde un registro (SQLite), aplique límites de tasa y gestione persistencia, reintentos y fallback. La visión offline-first introduce un Context Broker y QueueWorker para persistir mensajes, orquestar colas y procesar reintentos con limpieza según TTL. En observabilidad, se añade EventSource (ETW) y OpenTelemetry para métricas y logs con correlaciones por trace_id. En seguridad, el enfoque enterprise contempla redacción (RedactionRules.yaml), restricciones de ejecución (WDAC/AppLocker), conexiones TLS/mTLS, gestión de secretos (DPAPI) y hardening de Windows (PowerShell Constrained Language Mode, deshabilitación de RDP/WinRM salvo protección).

Para consolidar los requisitos mínimos de producción, el baseline sugiere que Silhouette:

- Mantenga mensajes en formato JSON sobre transports compatibles (stdio/HTTP SSE).
- Valide TTL, scopes y límites de tasa en el punto de entrada del router.
- Descubra capacidades con un registro y versionado explícito.
- Propague contextos de traza y baggage para correlación multiagente.
- Redacte datos sensibles antes de cualquier salida, con trazabilidad de decisiones.

Estas decisiones se alinean con la especificación de MCP y su visión como estándar abierto, así como con buenas prácticas de seguridad y despliegue multiagente.

Tabla 2. Resumen de campos de McpMessage y reglas de validación propuestas

| Campo        | Tipo         | Obligatorio | Descripción                                                      | Reglas de validación propuestas                                               |
|--------------|--------------|-------------|------------------------------------------------------------------|-------------------------------------------------------------------------------|
| trace_id     | GUID/string  | Sí          | Identificador de traza end-to-end                               | Formato UUID; uniqueness; presente en logs/métricas/trazas                    |
| parent_id    | string       | No          | Referencia al span/mensaje padre                                 | Si presente, debe existir en almacenamiento local                             |
| sender       | string       | Sí          | Identidad del emisor (agente/servicio)                           | Longitud máxima; listado permitido; formato “tipo.nombre”                     |
| receiver     | string       | Sí          | Identidad del receptor (agente/servicio)                         | Debe existir en Capability Registry; estado “HEALTHY”                         |
| intent       | string       | Sí          | Objetivo de alto nivel (p. ej., tool.exec.ps, plan.create)       | Debe existir en policies.yaml; validar scope y ttl_s                          |
| capability   | string       | No          | Herramienta/capacidad específica                                 | Debe existir en registry y ser compatible con intent                          |
| context      | JSON         | Sí          | Contexto (configuraciones, preferencias, identidad)              | Esquema por intent; campos sensibles opacos (tokenized)                       |
| payload      | JSON         | Sí          | Entrada principal de la operación                                | Validación por JSON Schema de capability/intent                               |
| result       | JSON         | No          | Resultado de la operación                                        | Estructura por JSON Schema; redacción aplicada según RedactionRules           |
| attachments  | map<string>  | No          | Referencias o metadatos complementarios                          | Validar URIs; sizes; sanitizar nombres de archivos                            |
| error        | McpError     | No          | Error normalizado (code, message, details)                       | Códigos alineados con MCP; incluir retry_after en errores recuperables        |

Tabla 3. Políticas por intent: scope, TTL, RPS y requires_approval

| Intent           | Scope             | ttl_s | rps  | requires_approval | Notas de seguridad                            |
|------------------|-------------------|-------|------|-------------------|-----------------------------------------------|
| plan.create      | agent.plan        | 60    | 10   | No                | Validar tamaño del plan; cost budget          |
| plan.review      | agent.critique    | 60    | 10   | No                | Versionar plantillas de prompt                 |
| tool.exec.ps     | tool.powershell   | 300   | 1    | Sí                | PowerShell restringido; aprobada por usuario   |
| tool.exec.fs.read| tool.filesystem   | 60    | 100  | No                | Limitar rutas; sanitizar nombres               |

Estas reglas se derivan del baseline y constituyen la base para la fase de hardening. Su instrumentación y enforcement deberán reflejarse en trazas y métricas, de modo que cualquier violación sea visible y auditable.[^2]

## 1) Estructura McpMessage y sistemas de routing

El contrato McpMessage debe consolidarse como un DTO estable y extensible. Para ello, recomendamos una taxonomía de campos explícita (identidad, correlación, seguridad, semántica de negocio, compliance), un versionado que preserve compatibilidad hacia atrás y reglas de validación por intent/capability. La clave es separar lo que es “contexto de ejecución” de lo que es “contenido operativo”, minimizando la presencia de datos sensibles en campos generales y permitiendo adjuntos para artefactos grandes. En paralelo, el sistema de routing debe evolucionar desde un registro mínimo hacia un pipeline de validaciones y despacho con mitigaciones graduadas (rate limiting, circuit breaker, backoff, fallback y cache).

Tabla 4. Campos de McpMessage con propósito, obligatoriedad y origen (baseline vs propuesto)

| Campo          | Baseline                       | Propuesto (extensión)                                           | Propósito                                          |
|----------------|--------------------------------|------------------------------------------------------------------|----------------------------------------------------|
| trace_id       | Identificador de traza         | Convertir en campo obligatorio y normalizado                     | Correlación end-to-end                             |
| parent_id      | Referencia a mensaje padre     | Se mantiene; validar existencia                                  | Construcción de spans jerárquicos                  |
| sender         | Identidad emisor               | Formato “tipo.nombre”; catálogo de emisores permitidos           | Identidad y autorización                           |
| receiver       | Identidad receptor             | Debe estar registrado y “HEALTHY”                                | Disponibilidad y health-check                      |
| intent         | Objetivo de alto nivel         | Esquemas por intent; validar scope y ttl                         | Semántica y política                               |
| capability     | Herramienta específica         | Debe existir y ser compatible; versionado explícito              | Ejecución y control                                |
| context        | JSON flexible                  | Subconjuntos por intent; tokenización de PII                     | Configuración y compliance                         |
| payload        | JSON                           | Validación con JSON Schema y sanitización                        | Integridad de datos                                |
| result         | JSON                           | Redacción obligatoria según RedactionRules                       | Seguridad de salida                                |
| attachments    | Diccionario opcional           | Validar URIs y tamaños; paths restringidos; escaneo DLP          | Metadatos/artefactos                               |
| error          | McpError                       | Códigos alineados MCP; incluir retry_after                       | Manejo de errores                                  |
| security_context (nuevo) | —                        | Identidad, scopes, purpose, audience, lineage                    | Autorización y auditoría                           |
| schema_version (nuevo) | —                      | Versionado semántico del mensaje                                 | Compatibilidad                                     |
| correlation_hints (nuevo) | —                     | tags, span attributes, linkage flags                             | Observabilidad                                     |
| redaction_state (nuevo) | —                      | Indicadores de redacción aplicada y razones                      | Compliance y trazabilidad                          |

Tabla 5. Pipeline de routing: etapas, entradas/salidas, errores y métricas

| Etapa                      | Entrada                   | Salida                     | Errores típicos                      | Métricas clave                            |
|---------------------------|---------------------------|----------------------------|--------------------------------------|-------------------------------------------|
| Recepción                 | McpMessage                | Mensaje normalizado        | INVALID_INPUT                        | REQUEST_COUNT, REQUEST_DURATION           |
| Decodificación y parsing  | bytes/JSON                | DTO                        | PARSING_ERROR                        | ERROR_RATE                                |
| Validación de políticas   | policies.yaml             | Autorización/denegación    | POLICY_VIOLATION, RATE_LIMITED       | POLICY_VIOLATIONS                         |
| Resolución de capability  | Capability Registry       | Agente/herramienta         | CAPABILITY_NOT_FOUND, UNAVAILABLE    | REGISTRY_LATENCY                          |
| Validación de esquemas    | JSON Schema               | Payload validado           | INVALID_SCHEMA                       | SCHEMA_VALIDATION_ERRORS                  |
| Dispatch                  | Agente destino            | Respuesta(result/error)    | TIMEOUT, CIRCUIT_OPEN                | DISPATCH_LATENCY, CIRCUIT_BREAKER_EVENTS  |
| Persistencia              | Storage                   | Confirmación               | STORAGE_ERROR                        | PERSISTENCE_LATENCY                       |
| Retry/Fallback            | Políticas de reintento    | Resultado final            | EXHAUSTED_RETRIES                    | RETRY_COUNT, FALLBACK_USED                |
| Redacción                 | Resultado                 | Resultado redactado        | REDACTION_ERROR                      | REDACTION_EVENTS                          |

Estas etapas están inspiradas en buenas prácticas MCP y patrones de resiliencia en arquitecturas distribuidas. La validación exhaustiva de entrada y la clasificación de errores son fundamentales para distinguir errores de cliente, servidor y dependencias externas.[^1][^2]

### 1.1 Estructura McpMessage: baseline y propuesta

En su estado actual, McpMessage cubre lo esencial: identidad (sender, receiver), objetivo (intent), operación (payload, result) y correlación (trace_id, parent_id). Para operar en producción, sugerimos:

- security_context: identidad, scopes, propósito y audiencia.
- schema_version: versión del contrato de mensaje.
- correlation_hints: etiquetas y atributos para spans.
- redaction_state: qué reglas se aplicaron y por qué.

La validación debe combinar JSON Schema (payload/result) y reglas de negocio (ttl_s, rps, requires_approval, compatibilidad intent–capability). La compatibilidad con transports MCP (stdio/HTTP SSE) debe preservarse, y el contrato debe ser estable y extensible por versión semántica.

Tabla 6. Matriz de compatibilidad: versiones de McpMessage vs campos

| Versión | Campos nuevos                    | Cambio breaking | Regla de compatibilidad                |
|---------|----------------------------------|-----------------|----------------------------------------|
| 1.0.0   | —                                | No              | Línea base                             |
| 1.1.0   | security_context, schema_version | No              | Campos opcionales, validación extensible|
| 2.0.0   | correlation_hints, redaction_state | Potencial     | Versionado semántico y migración guiada|

Este enfoque evita cambios disruptivos, manteniendo la interoperabilidad mientras enriquecemos capacidades de seguridad y observabilidad.[^2]

### 1.2 Sistema de routing: diseño y flujo

El routing debe instrumentarse como un pipeline claro: recepción → validación de políticas → resolución de capacidad → validación de esquema → dispatch → persistencia → respuesta → redacción. La normalización del error es clave: distinguiremos CLIENT_ERROR (4xx), SERVER_ERROR (5xx) y EXTERNAL_ERROR (502/503), con mensajes y detalles consistentes. El uso de propagate/receive de contexto (W3C Trace Context y Baggage) asegura continuidad de la traza cuando un flujo pasa de un agente a otro.

Tabla 7. Catálogo de errores normalizados: categoría y resolución

| Categoría       | Código ejemplo        | Causa típica                        | Acción recomendada                         |
|-----------------|-----------------------|-------------------------------------|--------------------------------------------|
| CLIENT_ERROR    | INVALID_INPUT         | Payload sin esquema                 | Corregir entrada; no reintentar             |
| CLIENT_ERROR    | ACCESS_DENIED         | Scope insuficiente                  | Solicitar aprobación; escalar si procede    |
| CLIENT_ERROR    | POLICY_VIOLATION      | RPS/TTL superados                   | Limitar tasa; aplicar backoff               |
| SERVER_ERROR    | INTERNAL_ERROR        | Error no controlado                 | Revisar logs; abrir issue; circuit breaker  |
| SERVER_ERROR    | DATABASE_UNAVAILABLE  | Registry/storage no disponible      | Reintentar con backoff; activar fallback    |
| EXTERNAL_ERROR  | TOOL_TIMEOUT          | Herramienta externa lenta           | Reintentar; degradar con caché              |
| EXTERNAL_ERROR  | RATE_LIMITED          | Dependencia impone límites          | Backoff exponencial; colas                  |

Este catálogo facilita el diagnóstico y la automatización de respuestas, siguiendo lineamientos de manejo de errores en entornos MCP.[^1]

## 2) McpRouter y políticas de delegación inteligente

El McpRouter debe convertirse en un servicio central con enforcement de políticas, resolución de capacidades, despacho, persistencia y reintentos con fallback. La delegación inteligente considera compatibilidad intent–capability, afinidad de agente, costes y estado de salud. Los límites de tasa y TTL evitan saturación y bloqueos; la aprobación humana introduce un control explícito para operaciones sensibles (p. ej., tool.exec.ps).

Tabla 8. Matriz de intents → capacidades → agentes → políticas

| Intent          | Capability            | Agente destino          | Políticas aplicadas                                   |
|-----------------|-----------------------|-------------------------|--------------------------------------------------------|
| plan.create     | plan.generate         | agent.plan              | ttl_s=60; rps=10; scope=agent.plan                    |
| plan.review     | plan.critique         | agent.critique          | ttl_s=60; rps=10; scope=agent.critique                |
| tool.exec.ps    | powershell.run        | HostPsAgent             | ttl_s=300; rps=1; requires_approval; CLM; WDAC        |
| tool.exec.fs.read| filesystem.read      | UiAutomationAgent       | ttl_s=60; rps=100; paths restringidos                 |
| web.scrape      | playwright.open       | WebPlaywrightAgent      | ttl_s=120; rps=5; sandbox; allowlist                  |

Tabla 9. Estrategias de mitigación: rate limiter, circuit breaker, cache, backoff, fallback

| Estrategia      | Condición de activación                       | Parámetros sugeridos                        | Observabilidad                         |
|-----------------|-----------------------------------------------|---------------------------------------------|----------------------------------------|
| Rate limiter    | rps > umbral del intent                       | Ventana deslizante; tokens por scope        | Métrica RATE_LIMITED; spans etiquetados|
| Circuit breaker | Fallos consecutivos / timeout                 | Umbral: 5 fallos en 30s; half-open: 3       | Evento CIRCUIT_OPEN/HALF_OPEN          |
| Cache           | Lecturas repetidas; resultados deterministas  | TTL de caché = min(ttl_s, política de freshness) | HIT/MISS ratio; cache_latency         |
| Backoff         | Errores recuperables (EXTERNAL_ERROR)         | 100ms → 800ms (exponencial); jitter         | RETRY_COUNT; spans de reintento        |
| Fallback        | Capability/Agente degradado                   | Degradar a cached/alternative tool          | FALLBACK_USED; outcome path            |

Este diseño se alinea con patrones MCP de resiliencia y con prácticas de descubrimiento y delegación propias de microservicios, donde el registro de capacidades es la fuente de verdad para resolver destinos y capacidades.[^1][^6]

### 2.1 Decisión de delegación y afinidad de agente

La selección de agente debe considerar:

- Compatibilidad intent–capability: el intent debe tener capacidades asociadas con esquema y políticas compatibles.
- Afinidad: mantener la misma sesión/contexto en flujos multiagente, evitando mezclar contextos de diferentes usuarios o tenants.
- Salud y coste: consultar health checks del agente y costes (tiempo, recursos). Preferir agentes con mejor salud y menor coste marginal según política.

Estos criterios se inspiran en patrones de service registry y descubrimiento del lado cliente o del lado servidor. El router puede actuar como servidor de descubrimiento, usando el registro de capacidades para decidir el destino con las mejores señales disponibles.[^6]

### 2.2 Resiliencia operativa en el router

La resiliencia se instrumenta con circuit breakers, rate limiting y backoff/fallback. La aplicación de estos mecanismos debe ser visible en trazas y métricas, permitiendo entender el comportamiento bajo diferentes escenarios. El modo offline-first se apoya en colas persistentes; si la operación no es bloqueante, se encola y se progresa asíncronamente. Los reintentos deben ser controlados por políticas con límites y jitter para evitar thundering herds.

Tabla 10. Parámetros de resiliencia por intent (umbrales y límites)

| Intent          | Circuit breaker umbral | Backoff (ms)     | Rate limit (rps) | Fallback permitido |
|-----------------|------------------------|------------------|------------------|--------------------|
| plan.create     | 5/30s                  | 100→800 (jitter) | 10               | Sí (caché)         |
| plan.review     | 5/30s                  | 100→800          | 10               | Sí                 |
| tool.exec.ps    | 3/30s                  | 200→1200         | 1                | No (aprobación)    |
| tool.exec.fs.read| 10/30s                | 50→400           | 100              | Sí (caché)         |
| web.scrape      | 5/30s                  | 200→1000         | 5                | Sí                 |

Estos parámetros deben afinarse con pruebas de carga y ingeniería del caos; su observabilidad es obligatoria para la gestión en producción.[^1]

## 3) Capability Registry y gestión dinámica

El Capability Registry es el núcleo de la descubribilidad y versionado. Proponemos un esquema SQLite con tablas para capabilities, versions, policies, health y cost. Los endpoints del registry permitirán registrar, actualizar, listar, consultar y retirar capacidades, con health checks y compatibilidad semántica. La disponibilidad debe ser alta; si el registry falla, el router debe degradar con fallback en caché o denegar nuevos dispatch en operaciones sensibles.

Tabla 11. Esquema SQLite propuesto: tablas y campos

| Tabla        | Campos principales                                                   | Índices sugeridos                                 |
|--------------|---------------------------------------------------------------------|---------------------------------------------------|
| capabilities | name, type (tool/resource/prompt), owner, created_at, updated_at    | name; type; owner                                 |
| versions     | capability_id, version, input_schema, output_schema, deprecates     | capability_id; version                            |
| policies     | capability_id, scope, ttl_s, rps, requires_approval                 | capability_id; scope                              |
| health       | capability_id, agent_id, status (HEALTHY/DEGRADED/UNHEALTHY), ts    | capability_id; agent_id; status                   |
| cost         | capability_id, cost_metric, unit, baseline, last_measured           | capability_id; cost_metric                        |

Tabla 12. Estrategias de registro (self vs third-party) y trade-offs

| Estrategia           | Pros                                              | Contras                                           | Uso recomendado                      |
|----------------------|---------------------------------------------------|---------------------------------------------------|--------------------------------------|
| Self-registration    | Autonomía de agentes; latencia baja               | Riesgo de desactualización; requiere disciplina   | Entornos controlados                 |
| Third-party registry | Consistencia y control central                   | Componente adicional; dependencia de un tercero   | Escala y gobernanza enterprise       |

Tabla 13. KPIs del Capability Registry

| KPI                      | Definición                                | Objetivo            |
|-------------------------|--------------------------------------------|---------------------|
| Disponibilidad          | % tiempo operativo                         | ≥ 99.9%             |
| Latencia P95            | Tiempo de consulta de capacidad            | < 30 ms             |
| Exactitud de health     | % de health que refleja estado real        | ≥ 98%               |
| Tiempos de propagación  | Tiempo de actualización a destinos         | < 5 s               |

Este diseño sigue patrones de service registry, con opciones de client-side o server-side discovery. El registro centralizado es un componente crítico y debe instrumentarse con alta disponibilidad.[^6]

### 3.1 Versionado y compatibilidad

El versionado debe ser explícito y semántico (MAJOR.MINOR.PATCH), con compatibilidad hacia atrás y políticas de deprecación. Los esquemas JSON (input/output) deben versionarse y validarse en runtime, evitando drift entre capacidades y su uso.

Tabla 14. Política de versionado: semver y reglas de compatibilidad

| Tipo de cambio | Ejemplo                   | Regla de compatibilidad                  |
|----------------|---------------------------|------------------------------------------|
| Major          | Cambiar esquema de input  | Requiere nueva versión major; migración   |
| Minor          | Añadir campo opcional     | Compatible hacia atrás                    |
| Patch          | Corregir documentación     | Compatible; no afecta runtime             |

Este enfoque reduce riesgos operativos y facilita evoluciones controladas.

### 3.2 Health checks y auto-recuperación

Definimos estados HEALTHY, DEGRADED y UNHEALTHY. La degradación gradual reduce tráfico, marca capacidades para fallback ynotifica al router para evitar dispatch. La auto-recuperación implica degradar bajo presión, con circuit breakers y colas asincrónicas cuando corresponda.

Tabla 15. Estados de health y acciones automáticas

| Estado       | Criterios principales                           | Acciones automáticas                       |
|--------------|--------------------------------------------------|--------------------------------------------|
| HEALTHY      | Latencia normal; errores bajos                   | Ninguna                                    |
| DEGRADED     | Latencia alta; errores moderados                 | Reducir tráfico; activar fallback/caché     |
| UNHEALTHY    | Timeouts; fallos repetidos                       | Abrir circuito; encolar; notificar          |

Estas prácticas se integran con el router y la observabilidad para una operación sostenible.[^6]

## 4) Observabilidad con OpenTelemetry y tracing distribuido

La observabilidad debe unificar trazas, métricas y logs en un solo SDK y Collector. La propagación de contexto W3C y Baggage asegura continuidad en flujos multiagente, transportando metadatos mínimos necesarios (por ejemplo, session_id) sin exponer datos sensibles. La instrumentación de McpMessage y McpRouter debe etiquetar spans con intent, capability, policy decisions, rate limiting y resultados de fallback, permitiendo reconstruir el recorrido completo.

Tabla 16. Mapeo de señales OTel: span attributes, métricas y logs por componente

| Componente   | Span attributes clave                      | Métricas principales                 | Logs estructurados                          |
|--------------|--------------------------------------------|--------------------------------------|---------------------------------------------|
| McpMessage   | trace_id, parent_id, schema_version        | REQUEST_COUNT, REQUEST_DURATION      | Parsing/validation outcomes                 |
| McpRouter    | intent, capability, policy decision        | POLICY_VIOLATIONS, CIRCUIT_EVENTS    | Dispatch/Retry/Fallback outcomes            |
| Registry     | capability, version, health status         | REGISTRY_LATENCY, HEALTH_EXACTITUDE  | Registration/unregistration events          |
| Agentes      | agent_id, tool invoked                     | DISPATCH_LATENCY, TOOL_ERRORS        | Tool execution results and errors           |

Tabla 17. Convenciones semánticas: claves de baggage y reglas de privacidad

| Clave             | Uso                                    | Regla de privacidad                            |
|-------------------|----------------------------------------|-----------------------------------------------|
| session.id        | Afinidad de sesión                      | No incluir PII; sólo identificadores opacos    |
| traceparent       | Contexto de traza                       | Según especificación W3C; sin datos sensibles  |
| policy.decision   | Decisión de política aplicada           | Registrar código y reasons; no payloads        |

Tabla 18. Collector pipeline recomendada

| Tipo de señal | Procesadores                       | Exportadores                  |
|---------------|------------------------------------|-------------------------------|
| Traces        | batch, attributes, memory_limiter  | jaeger/tempo/grafana          |
| Métricas      | aggregation, transform             | prometheus                    |
| Logs          | include/exclude,attributes         | loki/elastic                  |

Estas recomendaciones se basan en guías de OTel para Collector y en prácticas de instrumentación multiagente que recomiendan mantener baggage ligero, propagar contexto y unificar la telemetría con un solo SDK. La trazabilidad distribuida en flujos complejos multiagente es esencial para depurar comportamientos no deterministas.[^11][^12][^4][^5][^14]

### 4.1 Trazabilidad y correlación

La continuidad de la traza entre agentes y herramientas se logra con W3C Trace Context y propagadores de Baggage. Los IDs de sesión y traceparent deben transportarse a través de llamadas, manteniendo la jerarquía de spans. La correlación entre logs, métricas y trazas requiere una convención semántica unificada, que asigne atributos consistentes por componente y evite datos sensibles en los registros.

Tabla 19. Mapa de correlación entre spans, logs y métricas

| Span                                | Log estructurado                          | Métrica asociada                         |
|-------------------------------------|-------------------------------------------|-------------------------------------------|
| router.dispatch                     | intent=…, capability=…, outcome=…         | DISPATCH_LATENCY, CIRCUIT_EVENTS          |
| registry.lookup                     | capability=…, version=…, health=…         | REGISTRY_LATENCY                          |
| agent.tool.invoke                   | tool=…, params=… (redacted), result=…     | TOOL_ERRORS, RETRY_COUNT                  |

Este mapa facilita la navegación end-to-end en dashboards, habilitando una depuración eficiente.[^14]

### 4.2 Métricas y objetivos (SLO/SLA)

Definimos KPIs de rendimiento, latencia, disponibilidad y errores. Estos objetivos deben alimentar alertas y paneles.

Tabla 20. Catálogo de KPIs y objetivos (P95, P99, tasa de error)

| KPI                | Objetivo                              |
|--------------------|---------------------------------------|
| Throughput         | > 1000 solicitudes/s por instancia     |
| Latencia P95       | < 100 ms (operaciones simples)        |
| Latencia P99       | < 500 ms (operaciones complejas)      |
| Tasa de error      | < 0.1% bajo condiciones normales      |
| Disponibilidad     | > 99.9% del tiempo de actividad       |

Estos objetivos reflejan buenas prácticas y pueden ajustarse con benchmarking y pruebas de carga.[^1]

## 5) Seguridad enterprise con redacción y políticas

El modelo de seguridad debe aplicar defensa en profundidad: red, autenticación, autorización, validación, monitorización. La redacción y minimización de datos se implementan como管道 que inspecciona payloads y resultados antes de cualquier salida. La identidad y autorización se gestionan con tokens de corta duración y controles por atributos (ABAC). Las conexiones usan TLS/mTLS, los secretos se protegen con DPAPI y se aplica hardening en Windows (AppLocker/WDAC, Constrained Language Mode). El cumplimiento se traduce en controles técnicos de retención, residencia y auditoría.

Tabla 21. Controles por capa (red, identidad, datos, ejecución) y estado propuesto

| Capa          | Controles                                     | Estado propuesto                   |
|---------------|-----------------------------------------------|------------------------------------|
| Red           | Firewall, allowlist, VPN/privado              | Endpoints del modelo allowlist     |
| Identidad     | Tokens de corta duración, mTLS                | Identidad de carga de trabajo      |
| Datos         | Redacción, cifrado en reposo, DLP             | RedactionRules; CMK/HSM            |
| Ejecución     | WDAC/AppLocker, CLM                           | Restricción de binarios y scripts  |

Tabla 22. RedactionRules: fuentes, métodos y trazabilidad

| Fuente          | Método (hash/tokenize/mask)   | Excepciones/allowlist           | Trazabilidad                          |
|-----------------|-------------------------------|----------------------------------|----------------------------------------|
| PII (nombre)    | Tokenize                      | Usuario autorizado               | policy.decision; redaction_state       |
| SSN             | Mask                          | Roles específicos                | Registro con IDs y etiquetas           |
| Secretos        | Hash                          | Ninguna                          | Auditoría con reasons                  |

Tabla 23. Matriz de cumplimiento (GDPR/HIPAA/ISO/SOC2) → controles técnicos

| Norma  | Controles técnicos                                   |
|--------|-------------------------------------------------------|
| GDPR   | Minimización, derecho al olvido, residencia          |
| HIPAA  | PHI protegida, BAAs, registros de acceso              |
| ISO27001| Gestión de riesgos, respuesta a incidentes            |
| SOC2   | Propiedad de controles, auditoría                     |

Estos patrones se apoyan en arquitectura RAG segura y estándares enterprise de seguridad y gobernanza.[^8][^9][^10]

### 5.1 Redacción y minimización de datos

La redacción debe aplicarse tanto a payloads de entrada como a resultados. El principio es minimizar: no enviar más de lo necesario. Se tokeniza o hashea identificadores sensibles, se enmascaran campos restringidos y se deja un rastro truncado para auditoría con contenido sensible eliminado. Las excepciones se gestionan con allowlists y aprobación humana cuando corresponda.

Tabla 24. Política de redacción por tipo de dato y método

| Tipo de dato     | Método preferido           | Regla de excepción                       |
|------------------|----------------------------|-------------------------------------------|
| Email            | Mask (email[masked])       | Usuario con permiso específico            |
| Teléfono         | Tokenize                   | Allowlist de dominios                     |
| Cuenta bancaria  | Mask parcial               | Requerir aprobación                       |
| Secretos         | Hash irreversible          | Ninguna                                   |

Estas prácticas evitan fugas y mantienen trazabilidad sin exposición indebida.[^8]

### 5.2 Identidad, autorización y aislamiento de contexto

La autorización debe centralizarse y evaluarse en cada solicitud, con ABAC. Los tokens de corta duración reducen superficie de ataque. La mezcla de contextos se evita aislando sesiones, cachés y consultas por usuario/tenant; se permiten elevaciones “just-in-time” con caducidad automática.

Tabla 25. Roles/Atributos → permisos granulares por capability

| Rol/Atributo          | Permisos                                      |
|-----------------------|-----------------------------------------------|
| user.admin            | tool.exec.ps, web.scrape, plan.*              |
| user.viewer           | tool.exec.fs.read, resources.list             |
| service.agent         | capabilities.list, health.get                 |
| auditor               | logs.get (sin PII), policy.get                |

Este diseño asegura mínimo privilegio y gobernanza clara.

## Plan de implementación por fases y roadmap

La adopción propuesta respeta la visión Silhouette y prioriza un MVP con trazabilidad, políticas base y seguridad esencial. La madurez se incrementa en fases, con validación continua y hardening.

Tabla 26. Cronograma por fases: hitos, entregables y dependencias

| Fase | Hitos principales                                      | Entregables                                        | Dependencias                  |
|------|--------------------------------------------------------|----------------------------------------------------|-------------------------------|
| 0    | Contratos y configuración                              | McpMessage, SchemaGen, policies.yaml               | Alineación MCP                |
| 1    | Router + Registry                                      | McpRouter, SQLite Registry, endpoints, validación  | Políticas, OTel básico        |
| 2    | Agentes Windows                                        | HostPsAgent, WebPlaywrightAgent, UiAutomationAgent | Router + Registry             |
| 3    | Offline-first y observabilidad                         | Context Broker, QueueWorker, Collector OTel        | Router; agentes operativos    |
| 4    | Seguridad avanzada                                     | RedactionRules, TLS/mTLS, WDAC/AppLocker, DPAPI    | Observabilidad en producción  |

Este roadmap se alinea con la estrategia por fases descrita en el baseline y las mejores prácticas de operación MCP en producción.[^1]

### Fase 0–1 (MVP): contratos, router mínimo y registry

Entregables: McpMessage estable, validación básica de policies.yaml, registro mínimo de capacidades en SQLite y pipeline de routing con mitigaciones iniciales (rate limiting, backoff). Métricas mínimas: REQUEST_COUNT, REQUEST_DURATION, ERROR_RATE, POLICY_VIOLATIONS.

Estos elementos proporcionan visibilidad operativa básica y control de ejecución desde el principio.[^1]

### Fase 2–3: agentes Windows, offline-first y OTel

Entregables: agentes adaptadores (PowerShell restringido, Playwright sandboxed, UI automation), persistencia y colas, Collector OTel con pipeline de trazas/métricas/logs. Métricas: DISPATCH_LATENCY, CIRCUIT_EVENTS, HEALTH_EXACTITUDE, RETRY_COUNT, REDACTION_EVENTS.

La observabilidad integrada desde el diseño facilita depurar flujos multiagente y evaluar resiliencia.[^4]

### Fase 4: seguridad avanzada y cumplimiento

Entregables: redacción obligatoria, TLS/mTLS, AppLocker/WDAC, DPAPI, retención y auditoría. Métricas: disponibilidad >99.9%, violaciones de política y redacción auditables, tiempos de latencia P95/P99 estables.

El enfoque de seguridad en capas asegura que los requisitos enterprise se cumplan sin comprometer la operatividad.[^8]

## KPIs, SLOs y validación

La adopción de KPIs por componente y SLOs por dominio permite validar el diseño con evidencia. La validación se realiza con pruebas unitarias, de integración, contrato MCP, carga, caos y benchmarks. Los criterios de aceptación por fase alinean entregables con objetivos.

Tabla 27. Catálogo de KPIs con definiciones y objetivos

| Dominio        | KPI                       | Objetivo                          |
|----------------|---------------------------|-----------------------------------|
| Routing        | REQUEST_DURATION P95/P99  | <100 ms / <500 ms                 |
| Errores        | ERROR_RATE                | <0.1%                             |
| Registry       | REGISTRY_LATENCY P95      | <30 ms                            |
| Resiliencia    | RETRY_COUNT, CIRCUIT_EVENTS| Controlados y decrecientes        |
| Observabilidad | TRAZA_COMPLETA            | 100% trazas correlacionadas       |
| Seguridad      | POLICY_VIOLATIONS         | 0 incidentes críticos             |

Tabla 28. Matriz de pruebas por fase y criterios de aceptación

| Fase | Pruebas clave                               | Criterios de aceptación                             |
|------|----------------------------------------------|-----------------------------------------------------|
| 0    | Unitarias de contratos y políticas           | Esquemas válidos; políticas aplicadas               |
| 1    | Integración router–registry                  | Dispatch funcional; rate limiting efectivo          |
| 2    | Instrumentación OTel                         | Trazas correlacionadas; métricas visibles           |
| 3    | Carga y caos                                 | Resiliencia probada; fallback operativo             |
| 4    | Seguridad y cumplimiento                     | Redacción aplicada; auditoría trazable              |

La correlación de telemetría debe validarse de extremo a extremo: si una solicitud pasa por múltiples agentes, la traza debe mantener continuidad y permitir navegar logs y métricas con atributos comunes.[^13]

## Riesgos, mitigaciones y próximos pasos

Los riesgos identificados se agrupan en técnicos, operativos y cumplimiento. Las mitigaciones priorizadas reducen probabilidad e impacto; se proponen experimentos y métricas de validación.

Tabla 29. Matriz de riesgos (probabilidad/impacto), mitigaciones y propietarios

| Riesgo                                         | Probabilidad | Impacto | Mitigación principal                                 | Propietario        |
|------------------------------------------------|--------------|---------|------------------------------------------------------|--------------------|
| Latencia por validaciones/redacción            | Media        | Media   | Cachés; batch validaciones; OTel spans optimizados   | Arquitectura       |
| Complejidad de correlación multiagente         | Alta         | Alta    | Propagación W3C/Baggage; convenciones semánticas     | Observabilidad     |
| Gobernanza de PII y cumplimiento               | Alta         | Alta    | RedactionRules; ABAC; auditoría y retención          | Seguridad          |
| Disponibilidad del Capability Registry         | Media        | Alta    | HA; health checks; degradación controlada            | Plataforma         |
| Fallos de agentes Windows (PowerShell/UI)      | Media        | Media   | CLM; WDAC; sandboxing; approval workflows            | Ingeniería Windows |

Próximos pasos inmediatos:

1) Consolidar McpMessage con security_context, schema_version y correlación; activar validación por policies.yaml.  
2) Implementar McpRouter con pipeline mínimo: recepción → políticas → resolución de capability → dispatch → persistencia → respuesta, incluyendo manejo de errores y métricas básicas.  
3) Crear el Capability Registry en SQLite con tablas de capabilities, versions, policies, health y cost; instrumentar health checks y latencias.  
4) Integrar OTel SDK y Collector con propagadores W3C y Baggage; definir convenciones semánticas; activar trazas de router y agentes.  
5) Introducir RedactionRules mínima (PII, secretos); activar redacción en resultados y auditoría de decisiones.  
6) Definir y monitorear KPIs/SLOs por dominio; preparar pruebas de carga y caos en Fase 3.

Gaps de información relevantes:

- Implementación actual de McpRouter.cs (validación TTL/scopes/RPS, resolución de capabilities, persistencia, reintentos y fallback).  
- Detalle de policies.yaml (intents adicionales, scopes, límites de tasa, reglas de aprobación, casos edge).  
- Diseño físico de capabilities.sql (esquema SQLite completo, índices, transacciones, migración de datos).  
- Configuración de instrumentación EventSource/OTel (SDK, propagadores, exporter, Collector pipeline).  
- Reglas de RedactionRules.yaml (patrones, clasificadores, mapeos de PII, excepciones).  
- Inventario de agentes Windows (HostPsAgent, WebPlaywrightAgent, UiAutomationAgent), permisos y restricciones.  
- Políticas WDAC/AppLocker específicas y binarios permitidos; requisitos de cumplimiento aplicables.

Estos vacíos deben resolverse antes de cerrar Fase 1–2, preferiblemente con artefactos versionados y pruebas automatizadas.

---

## Referencias

[^1]: MCP Best Practices: Architecture & Implementation Guide. https://modelcontextprotocol.info/docs/best-practices/  
[^2]: Transports - Model Context Protocol. https://modelcontextprotocol.io/specification/2025-06-18/basic/transports  
[^4]: AI observability in multi-agent systems using OpenTelemetry. https://outshift.cisco.com/blog/ai-observability-multi-agent-systems-opentelemetry  
[^5]: OpenTelemetry | Observability primer. https://opentelemetry.io/docs/concepts/observability-primer/  
[^6]: Pattern: Service registry - Microservices.io. https://microservices.io/patterns/service-registry.html  
[^8]: Secure RAG: Enterprise Architecture Patterns for Accurate, Leak-Free AI. https://petronellatech.com/blog/secure-rag-enterprise-architecture-patterns-for-accurate-leak-free-ai/  
[^9]: Enterprise Security Architecture: A Framework and Template. https://pubs.opengroup.org/onlinepubs/9199929899/toc.pdf  
[^10]: Enterprise Architecture Patterns for GDPR Compliance. https://www.scitepress.org/Papers/2021/104413/104413.pdf  
[^11]: Architecture | OpenTelemetry Collector. https://opentelemetry.io/docs/collector/architecture/  
[^12]: OpenTelemetry tracing guide + best practices. https://vfunction.com/blog/opentelemetry-tracing-guide/  
[^13]: OpenTelemetry best practices: A user's guide. https://grafana.com/blog/2023/12/18/opentelemetry-best-practices-a-users-guide-to-getting-started-with-opentelemetry/  
[^14]: OpenTelemetry demystified: a deep dive into distributed tracing. https://www.cncf.io/blog/2023/05/03/opentelemetry-demystified-a-deep-dive-into-distributed-tracing/  
[^15]: Introducing the Model Context Protocol - Anthropic. https://www.anthropic.com/news/model-context-protocol