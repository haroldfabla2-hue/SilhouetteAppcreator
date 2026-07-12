# Mejores Prácticas y Estándares Avanzados para Servidores MCP (2025)

## Resumen Ejecutivo

El Model Context Protocol (MCP) se ha consolidado en 2025 como el estándar operativo para conectar de forma segura aplicaciones basadas en modelos de lenguaje (LLM) con datos y herramientas externas. La especificación vigente (2025-06-18) define un modelo claro de actores (Hosts, Clientes y Servidores), formaliza el transporte con JSON-RPC 2.0 e introduce capacidades clave que mejoran tanto la seguridad como la experiencia de desarrollo y operación: contenido estructurado con campos como outputSchema y structuredContent, primitivas de interacción que refuerzan el consentimiento explícito del usuario (elicitation, sampling), y una guía explícita de mejores prácticas de seguridad centrada en el control y privacidad de datos.[^1]

La relevancia de MCP en entornos enterprise no es anecdótica. A diferencia de integraciones ad hoc, MCP aporta un contrato estable, descubribilidad de capacidades, y un marco de seguridad que separa Autorización y Recursos, habilitando la orquestación de identidades, políticas y observabilidad en escenarios multi-tenant y multi-sistema. En la práctica, MCP se vuelve el “adaptador estandarizado” entre agentes de IA y sistemas corporativos, permitiendo escalar casos de uso sin sacrificar gobernanza ni trazabilidad.[^1]

Conclusiones clave:
- Protocolo: La versión 2025-06-18 reafirma transports (stdio y Streamable HTTP), fija reglas de versionado, e introduce primitives que posicionan la seguridad y el consentimiento del usuario como principios de primer orden. La comunidad considera a Streamable HTTP el transporte de primera clase para producción; SSE pasa a un rol heredado.[^1][^16]
- Arquitectura: La separación de Autorización y Recursos —alineada con OAuth 2.1 y la especificación de autorización MCP— reduce el acoplamiento y habilita gateways como plano de control para políticas, observabilidad y limitación de tasa.[^7][^8]
- Seguridad: El patrón recomendado en empresa combina Authorization Server externo, Resource Indicators (RFC 8707), y gestión moderna de secretos con vaults y identidades de carga de trabajo. La revocación y los controles de consentimiento se apoyan en tokens de corta duración y auditoría exhaustiva.[^7][^10][^30][^31][^32]
- Observabilidad: La visibilidad extremo a extremo requiere instrumentación con OpenTelemetry, logging estructurado con IDs de correlación y métricas por herramienta. En JavaScript, soluciones como Sentry facilitan monitoreo específico de MCP, con trazabilidad por método, cliente y transporte.[^12][^22]
- Operación: Tres estrategias de despliegue (Remoto, Gestionado, Estación de Trabajo) conviven en organizaciones maduras; gobernarlas de forma consistente implica SSO/SCIM, registro interno de servidores aprobados y kill-switches. El escalado automático y el manejo de cargas pesadas se benefician de backpressure y circuit breakers en el gateway.[^13][^17]

Recomendaciones ejecutivas:
- Estandarizar Streamable HTTP para producción, manteniendo stdio para entornos locales y pruebas.
- Implantar un gateway MCP como plano de control: validación de tokens, rate limiting, transformación de credenciales, auditoría y trazas.
- Operar con OAuth 2.1 y Resource Indicators; tokens cortos, ámbitos mínimos y gestión de secretos con vaults e identidades de carga de trabajo.
- Instrumentar con OTel desde el primer día y definir SLOs por herramienta; implementar paneles y alertas accionables.
- Adoptar una gobernanza de ciclo de vida con registro interno de servidores MCP, revisiones de seguridad y kill-switches.

Este informe detalla estándares, patrones de diseño, controles de seguridad, prácticas de observabilidad y despliegue para alcanzar un nivel enterprise en MCP. Se señalan, además, brechas de información pendientes: la especificación completa del changelog 2025-06-18, disponibilidad real de elicitation y sampling en hosts主流, y madurez de DCR e interoperabilidad del parámetro resource entre IdPs.

---

## Estándares del Protocolo MCP (2025-06-18 y roadmap)

La arquitectura MCP distingue tres actores: el Host (aplicación LLM), el Cliente (conector embebido en el host) y el Servidor (proveedor de contexto y capacidades). La comunicación se realiza mediante JSON-RPC 2.0 sobre conexiones con estado, y la negociación de capacidades permite descubrir herramientas, recursos y prompts disponibles. La especificación define un esquema en TypeScript como referencia, e incorpora mejores prácticas de seguridad y consentimiento del usuario en el diseño de primitives y flows.[^1][^5][^25]

En cuanto a transports, stdio continúa siendo un camino universal para ejecución local y compatibilidad amplia. Para despliegues remotos y escalables, Streamable HTTP es el transporte recomendado por la comunidad y por la documentación de transports, sustituyendo el uso de SSE en producción. La propuesta de Streamable HTTP unifica streaming incremental y respuesta tradicional sobre un único endpoint, con soporte para cancelación y timeouts desde el lado del cliente.[^16][^3]

Versionado. MCP adopta identificadores de versión basados en fecha (formato YYYY-MM-DD), siguiendo convenciones de evolución compatibilidad-fecha como mecanismo de comunicación de cambios incompatibles. La especificación de versionado y las normas BCP/RFC (RFC 2119 y RFC 8174) guían la interpretación de palabras obligatorias y el proceso de deprecación.[^2][^26][^27]

Funciones introducidas o actualizadas en 2025:
- Elicitation y sampling: mecanismos para solicitar al usuario información adicional o aprobar explícitamente la generación de contenido del LLM, reforzando el control y la transparencia. Su adopción depende de capacidades del host, por lo que se recomienda degradación elegante cuando no estén disponibles.[^1][^3]
- structuredContent y outputSchema: salidas tipadas y legibles por máquina, combinadas con contenido legible por humanos. Esto mejora la interoperabilidad con LLMs y la experiencia del usuario.[^1][^3]
- Buenas prácticas de seguridad: consentimiento explícito, privacidad de datos y verificación estricta de herramientas, con descripciones que pueden considerarse no confiables si el servidor no es de confianza.[^1]

Para ilustrar la evolución de capacidades, la siguiente tabla sintetiza los cambios más relevantes entre la especificación 2025-06-18 y la de 2025-03-26, especialmente en autorización y transporte.

### Tabla 1. Cambios entre 2025-06-18 y 2025-03-26 por dominio

| Dominio               | 2025-06-18                                                                 | 2025-03-26                                           | Comentario                                                                                      |
|-----------------------|----------------------------------------------------------------------------|------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| Transporte            | Streamable HTTP recomendado para producción; stdio para desarrollo         | En transición; SSE presente en ecosistemas           | Streamable unifica streaming y request/response; SSE pasa a rol legado.[^16][^3]                |
| Autorización          | Separación explícita Autorización vs Recursos; uso de OAuth 2.1 y PRM/DCR | Mezcla de roles; OAuth recomendado                   | Refuerza el modelo de Resource Server para MCP; reliance en RFCs OAuth modernas.[^7][^8]        |
| Elicitation/Sampling  | Primitives formalizadas y guiadas por consentimiento                       | Soporte incipiente o limitado                        | Dependiente del host; requiere detección de capacidades y fallback.[^1][^3]                     |
| Contenido estructurado| structuredContent y outputSchema                                             | Parcial o no prescriptivo                            | Mejora precisión de salidas y comprensión por LLM; reduce ambigüedad.[^1][^3]                   |
| Versionado            | Esquema TypeScript 2025-06-18; guía de versionado por fecha               | Versión previa por fecha                             | Mantiene compatibilidad por ventana de deprecación y comunicación explícita.[^2][^5]            |

Mapa de transports: stdio vs Streamable HTTP. La selección no es trivial; influye en escalabilidad, latencia y compatibilidad.

### Tabla 2. Mapa de transports: stdio vs Streamable HTTP

| Aspecto                         | stdio                                              | Streamable HTTP                                                         |
|---------------------------------|----------------------------------------------------|-------------------------------------------------------------------------|
| Uso típico                      | Desarrollo local, pruebas, compatibilidad básica   | Producción remota, escalado horizontal, streaming incremental           |
| Escalabilidad                   | Limitada al host local                             | Alta; compatible con LB, proxies y gateways                            |
| Streaming incremental           | No aplicable                                       | Soportado nativamente en un único endpoint                             |
| Cancelación/timeout             | Limitado                                           | Recomendado a nivel de transporte y cliente                            |
| Compatibilidad con gateways     | Baja                                               | Alta; incluye manejo de CORS y encabezados de seguridad                |
| Observabilidad                  | Básica                                             | Rica; métricas por transporte, latencia por tramo y segmentación        |

Sub-sección: Cambios clave 2025-06-18 y su impacto

Autorización. La especificación de autorización publicada en junio de 2025 refuerza el patrón Resource Server: el servidor MCP valida tokens emitidos por un Authorization Server externo, con uso de metadatos PRM (RFC 9728) y, cuando aplica, registro dinámico de clientes (RFC 7591). Los Resource Indicators (RFC 8707) vinculan tokens a un recurso específico, mitigando ataques por reutilización y reduciendo el radio de explosión en caso de compromiso. Este enfoque favorece soluciones enterprise donde ya existen IdPs corporativos.[^7][^8][^10][^11]

Transporte. La recomendación de Streamable HTTP y el descenso de SSE optimiza el rendimiento en producción, al permitir resultados incrementales sin sobrecarga de conexiones múltiples. Asimismo, la cancelación y los timeouts en el transporte disminuyen la contención de recursos ante llamadas de larga duración.[^16][^3]

Capacidades del cliente/host. La elicitation y el sampling, al requerir confirmación explícita, establecen salvaguardas operativas y de privacidad. El contenido estructurado habilita contratos de salida verificables y la reducción de ambigüedad en la interacción LLM-servidor, clave para automatizar flujos críticos en empresa.[^1][^3]

---

## Patrones de Diseño para Escalabilidad y Rendimiento

Una arquitectura MCP robusta comienza con una separación disciplinada de responsabilidades y evoluciona hacia patrones de escalado y observabilidad que integran el plano de control (gateways) con la lógica de dominio.

DDD por dominio. Aplicar Domain-Driven Design (DDD) en servidores MCP clarifica límites, modelos y servicios, y reduce el acoplamiento entre lógica de negocio y preocupaciones de infraestructura. En un diseño por capas, los servicios de dominio encapsulan reglas y exponen capacidades que se mapean a herramientas MCP; los repositorios abstraen persistencia; y los servicios de aplicación orquestan casos de uso y traducen los requisitos del protocolo (descubrimiento, argumentos y esquemas, manejo de errores) al dominio y viceversa.[^14] Esta separación mejora testabilidad, flexibilidad de infraestructura y comprensión semántica por parte del LLM, dado que las herramientas reflejan intencionalidad de negocio con nombres claros y contratos bien definidos.[^14][^21]

Arquitectura de múltiples servidores MCP. Cuando el dominio crece, fragmentar capacidades en múltiples servidores —por área de producto, permisos o rendimiento— reduce la carga cognitiva y los riesgos operativos. AWS Labs muestra más de 30 servidores MCP para diferentes integraciones, evidenciando escalabilidad y gobernanza mediante separación de superficies y políticas.[^15] La gestión dinámica de conjuntos de herramientas, recomendada oficialmente, permite registrar sólo las capacidades relevantes por contexto, mejorando selección por el LLM y reduciendo coste de tokens.[^14][^15]

Gateway MCP y scaling horizontal. La incorporación de un gateway entre clientes y servidores MCP aporta una capa transversal que centraliza rate limiting, validación de tokens, transformación de solicitudes/respuestas, caching selectivo y circuit breakers. Sobre Kubernetes, el escalado horizontal y health endpoints facilitan políticas HPA basadas en latencia, colas y CPU/memoria, mientras que el manejo de cargas pesadas y respuestas de gran tamaño se realiza con fragmentación incremental y URIs de recursos en lugar de payloads gigantes.[^17]

Para sintetizar impactos y mitigaciones, se presenta una matriz de patrones y objetivos operativos.

### Tabla 3. Matriz de patrones vs objetivos operativos

| Patrón                         | Escalabilidad                          | Latencia                              | Disponibilidad                        | Complejidad Operativa                  | Mitigaciones Clave                                           |
|-------------------------------|----------------------------------------|----------------------------------------|----------------------------------------|----------------------------------------|--------------------------------------------------------------|
| DDD por dominio               | Alta (límites claros)                  | Media (mejor composición)              | Media (aislamiento por bounded context)| Media (disciplina arquitectónica)      | Testing por capas, contratos MCP bien definidos              |
| Múltiples servidores MCP      | Alta (fragmentación de carga)          | Media (evita cuellos por saturación)   | Alta (fallos contenidos)               | Alta (gestión de inventario y políticas)| Registro central, governance de herramientas                 |
| Gateway MCP                   | Alta (LB, rate limiting)               | Baja-Media (optimización y caching)    | Alta (circuit breakers, retries)       | Media (componente adicional)           | Endpoints de salud, OTel, auditoría exhaustiva               |
| Gestión dinámica de herramientas | Media (registro selectivo)          | Baja (menos tokens)                    | Media (menos superficie de ataque)     | Media (lógica condicional)             | Degradación elegante, bandas de características               |

Sub-sección: DDD y su mapeo a primitives de MCP

La claridad semántica de nombres y esquemas es crucial para la elección de herramientas por el LLM. Las entidades y servicios de dominio se traducen en herramientas con parámetros tipados, enumeraciones y modos de falla documentados; los recursos se modelan como superficies de lectura (con URIs y reglas de acceso), y los prompts como plantillas reutilizables. Este mapeo minimiza ambigüedad y favorece validaciones en tiempo de ejecución.[^14]

### Tabla 4. Mapeo DDD → primitives MCP

| Elemento DDD      | Primitive MCP | Reglas de Diseño                                                                       |
|-------------------|---------------|-----------------------------------------------------------------------------------------|
| Servicio de dominio | Herramienta   | Idempotencia, parámetros tipados, nombres significativos, modos de falla explícitos     |
| Recurso de dominio | Recurso       | Solo lectura o mínimamente mutable, URIs explícitas, paginación y caching              |
| Plantilla de interacción | Prompt     | Plantillas parametrizadas, separación de contexto sistema vs usuario                   |

---

## Sistemas de Seguridad Enterprise-Grade

Modelo de amenazas y principios. Los servidores MCP exponen superficies sensibles: acceso a datos arbitrarios y ejecución de herramientas con efectos secundarios. El modelo de amenazas debe cubrir inyección de prompt, confused deputy en entornos multi-tenant, fuga de datos, ataques de rug-pull (descripciones de herramientas que cambian tras aprobación) y abuso por clientes descontrolados. La especificación de seguridad de MCP exige consentimiento del usuario, privacidad de datos y tratamiento prudente de herramientas, incluyendo anotaciones y descripciones no confiables salvo servidores de confianza.[^1]

OAuth 2.1 para MCP. En línea con la especificación de autorización MCP, el servidor debe actuar como Resource Server y delegar autenticación/autorización a un Authorization Server externo. La interacción inicia con descubrimiento PRM (RFC 9728), continúa con registro dinámico de clientes (RFC 7591) cuando esté disponible, y culmina con un flujo Authorization Code + PKCE donde el parámetro resource (RFC 8707) vincula el token al servidor MCP concreto.[^7][^8][^10][^11] Los tokens deben ser de corta duración y auditarse exhaustivamente. Las respuestas no deben exponer secretos ni claims sensibles al LLM ni a los logs.

Gestión de secretos y identidades de carga de trabajo. La protección de credenciales requiere vaults (Azure Key Vault, AWS Secrets Manager, HashiCorp Vault) e identidades de carga de trabajo que eviten credenciales de larga duración en configuración. La rotación en tiempo de ejecución y startup validation reducen ventanas de exposición; el principio de mínimo privilegio acota el impacto en caso de incidente.[^30][^31][^32][^17]

Gateway con autorización basada en políticas. En escenarios enterprise, la decisión de acceso se desplaza al gateway: validación de tokens entrantes, enriquecimiento de contexto (usuario, agente, dispositivo), evaluación de políticas (motor OPA o plataforma cloud) y transformación de credenciales (emisión de aserciones efímeras para backends). Este patrón limita el “confused deputy”, centraliza auditoría y facilita gobernanza y trazabilidad de acciones MCP.[^9][^17]

La comparación de flujos OAuth en contexto MCP ayuda a elegir el enfoque más adecuado.

### Tabla 5. Comparativa de flujos OAuth en MCP

| Flujo                           | Cuándo usar                                     | Ventajas                                                   | Riesgos/Consideraciones                                  |
|---------------------------------|--------------------------------------------------|------------------------------------------------------------|----------------------------------------------------------|
| Authorization Code + PKCE       | Acceso a datos con ámbito de usuario            | Consentimiento explícito, tokens cortos, ámbitos finos     | DCR anónimo puede no ser aceptable en empresa            |
| Client Credentials (System)     | Operaciones de sistema sin contexto de usuario  | Simplicidad, principal claro, ámbitos por recurso          | Secreto de cliente es alto valor; rotación y scoping estrictos |

Mapa de controles de seguridad. La siguiente tabla sintetiza controles clave para mitigación de riesgos MCP.

### Tabla 6. Mapa de controles de seguridad para riesgos MCP

| Riesgo                | Control                                                         | Observación                                                                 |
|-----------------------|------------------------------------------------------------------|------------------------------------------------------------------------------|
| Inyección de prompt   | Consentimiento explícito, sanitización, límites de herramientas | Elicitation para acciones arriesgadas; logging sin secretos                  |
| Confused deputy       | Resource Indicators, validación de audiencia, gateway            | Transformación de credenciales y claims por gateway                         |
| Fuga de datos         | Tokens cortos, scoping mínimo, vaults                            | Auditoría y alertas por acceso anómalo                                      |
| Rug-pull              | Listas blancas, revisiones, versionado de capacidades            | Kill-switches; registro interno de servidores aprobados                     |
| Abuso por clientes    | Rate limiting, circuit breakers, CORS                            | Paneles de uso por cliente/herramienta; SLOs y alertas                      |

Sub-sección: Autorización basada en gateway vs. enfoques tradicionales

Un gateway centralizado evita duplicación de lógica de autorización y reduce deuda operativa al aplicar políticas consistentes. Frente a integraciones directas entre clientes y servidores MCP —donde cada servidor implementa su propia validación y reglas— el gateway introduce una línea de defensa común, con transformación de tokens y auditoría de decisiones. Las preocupaciones de interoperabilidad (DCR, parámetro resource) se mitigan desacoplando del proveedor y manteniendo políticas y registro centralizado.[^9][^17]

---

## Observabilidad y Monitoring

La operación confiable de servidores MCP exige visibilidad extremo a extremo. El marco recomendado incluye OpenTelemetry para trazado distribuido, logging estructurado con IDs de correlación y métricas clave por herramienta y transporte. La capa de gateway facilita trazabilidad y captura eventos específicos MCP (descubrimiento, invocación, errores de esquema), reduciendo el MTTR y proporcionando evidencia para auditorías y mejora continua.[^12][^22][^23]

Logging estructurado y trazabilidad. Registros con correlación por sesión/usuario/agente, tool_name, invocation_id y resultados permiten analizar comportamientos y aislar cuellos de botella. La instrumentación consciente del protocolo, disponible para SDKs JavaScript en servidores, segmenta por cliente, transporte y herramienta, revelando patrones de uso, herramientas más lentas y errores frecuentes.[^22]

Métricas. Se recomiendan métricas de latencia por herramienta y por percentiles (p95), tasas de error por método y transporte, throughput, popularidad de servidores/herramientas y consumo de tokens por usuario/servidor. Estas métricas informan escalado, refactorización de herramientas y optimización de costos operativos.[^23][^22]

Dashboards y alertas. Paneles que muestran distribución de transporte (stdio vs Streamable HTTP), llamadas por herramienta, duración y errores, y actividad por cliente. Las alertas deben cubrir SLOs de latencia, error rate, fallos de autorización y anomalías de uso.[^22][^23]

Para guiar la instrumentación, se propone un catálogo de métricas y un mapa de eventos de traza.

### Tabla 7. Catálogo de métricas recomendadas

| Métrica                           | Dimensiones                                   | Fuente                         | Uso Operativo                                        |
|-----------------------------------|-----------------------------------------------|--------------------------------|------------------------------------------------------|
| Latencia por herramienta          | tool_name, client, transport                   | Logs/OTel                      | SLOs, optimización de rendimiento                    |
| Error rate por método             | method, status_code, transport                 | Logs/OTel                      | Incidentes, regresiones                              |
| Duración p95                      | tool_name, transport                           | OTel                           | Escalado, backpressure                               |
| Popularidad de herramientas       | tool_name, client                              | Logs                           | Priorización de mejoras                              |
| Consumo de tokens                 | user_id, server, tool                          | Logs/Gateway                   | Control de costos, límites de tasa                   |
| Autenticación/autorización fallos | client, status_code                            | Gateway                        | Detección temprana de problemas de identidad         |

### Tabla 8. Mapa de eventos de traza

| Evento                      | Span principal        | Atributos clave                                     | Correlación                        |
|----------------------------|-----------------------|------------------------------------------------------|------------------------------------|
| Descubrimiento de capacidades | client → server       | session_id, server_id, capabilities                  | Correlación con inicio de sesión   |
| tools/call                 | server_tool           | tool_name, invocation_id, args_schema_valid, latency | Vinculado a solicitud JSON-RPC     |
| resources/read             | server_resource       | resource_uri, cache_status, bytes_sent              | Correlación con secuencia cliente  |
| Autorización (token)       | gateway               | client_id, claims, decision, latency                 | Vinculado a solicitudes subsecuentes|
| Error de protocolo         | server                | method, error_code, transport                        | Correlación por session_id         |

Sub-sección: Instrumentación práctica con SDKs y gateways

Para SDKs JavaScript, envolver el McpServer con la instrumentación correspondiente habilita visibilidad por método, herramienta y transporte con una línea de código. Propagar IDs de correlación a servicios descendentes y a la capa de gateway asegura una vista holística del recorrido de la solicitud. Cuando existan convencionales semánticos OTel para MCP, se recomienda adoptarlos para estandarizar atributos y facilitar correlación multi-servicio.[^22]

---

## Estrategias de Deployment y Gestión del Lifecycle

Los despliegues de servidores MCP en empresa suelen combinar tres estrategias: Remoto (SaaS), Gestionado (infraestructura propia) y Estación de Trabajo (local). El modelo híbrido permite aprovechar integraciones externas, mantener control sobre cargas internas y dar soporte a desarrolladores con acceso a archivos locales, siempre bajo una gobernanza común.

Estrategias de despliegue. Remoto ofrece rapidez y bajo mantenimiento; Gestionado aporta control, seguridad y observabilidad; Estación de Trabajo habilita prototipado con stdio, pero escala mal y añade riesgos de seguridad. La solución operativacommon en empresas es un híbrido gobernado por gateways, SSO/SCIM y registros internos de servidores aprobados.[^13]

Gestión de ciclo de vida. Un registro interno de servidores MCP, kill-switches para desactivación inmediata y revisiones de seguridad obligatorias previenen el fenómeno de servidores “en la sombra”. La prohibición de DCR anónimo y el uso de identidades verificables para agentes (ej. SPIFFE/SPIRE en perfiles empresariales) fortalecen control de acceso y trazabilidad.[^13][^33]

CI/CD y compatibilidad. El versionado explícito de capacidades y negociación de backward compatibility reducen sorpresas en clientes; se recomienda mantener stdio como entorno mínimo viable y Streamable HTTP para producción. Gateways con manejo de CORS y encabezados de seguridad simplifican integración con clientes heterogéneos.[^17][^16]

Operación continua. Rotación de secretos, health endpoints y escalado automático —por métricas de latencia, tasa de solicitudes o colas de trabajo— mantienen resiliencia. Circuit breakers y backpressure evitan agotamiento de recursos ante agentes descontrolados o picos inesperados.[^17]

La siguiente tabla compara las estrategias de despliegue.

### Tabla 9. Comparativa de despliegue: Remoto vs Gestionado vs Estación de Trabajo

| Aspecto            | Remoto                                     | Gestionado                                        | Estación de Trabajo                          |
|--------------------|---------------------------------------------|---------------------------------------------------|----------------------------------------------|
| Seguridad          | Media (dependencia del proveedor)           | Alta (control total)                              | Baja (tokens locales, dispersion)            |
| Gobernanza         | Media (aprobación y auditoría de terceros)  | Alta (SSO/SCIM, registro interno)                 | Baja (por equipo, difícil estandarizar)      |
| Observabilidad     | Variable (datos del proveedor)              | Alta (OTel, gateways, paneles)                    | Baja (logs locales, difícil auditoría)       |
| Escalado           | Alto (infraestructura del proveedor)        | Alto (Kubernetes, autoscaling)                    | Bajo (por máquina)                            |
| Casos de uso       | Integraciones SaaS, tiempo de salida rápido | Cargas internas sensibles, control de cumplimiento| Prototipado, acceso a archivos/hardware      |

Checklist de readiness empresarial:

### Tabla 10. Checklist de readiness para MCP en empresa

| Dominio         | Ítems                                                                                 |
|-----------------|----------------------------------------------------------------------------------------|
| Seguridad       | OAuth 2.1, Resource Indicators, vaults, identidades de carga de trabajo, rotación      |
| Observabilidad  | OTel, logs estructurados, paneles por herramienta, alertas de SLO                      |
| Governance      | Registro interno, kill-switches, SSO/SCIM, listas blancas, revisiones de seguridad     |
| Operaciones     | Health endpoints, CI/CD con versionado de capacidades, circuit breakers, rate limiting |

Sub-sección: Governance y control operacional

La unificación de identidad con SSO y aprovisionamiento SCIM mapea usuarios/agentes a políticas y herramientas específicas. Un registro central de servidores MCP aprobados —con propietarios, notas de seguridad y estado— sirve como fuente de verdad y habilita kill-switches para mitigación rápida de incidentes. La detección y prevención de servidores “en la sombra” requiere auditorías periódicas y controles de configuración para evitar credenciales dispersas y ausencia de trazabilidad.[^13]

---

## Conclusiones y Recomendaciones Estratégicas

Prioridades 30-60-90 días:
- Seguridad: Establecer OAuth 2.1 con Resource Indicators, validar tokens de corta duración, instrumentar vaults y rotaciones; desplegar un gateway MCP que centralice políticas y auditoría.[^7][^10][^17]
- Observabilidad: Instrumentar con OpenTelemetry y logging estructurado; configurar paneles por herramienta y alertas de SLO (latencia p95, error rate); habilitar trazabilidad por sesión y cliente.[^12][^22][^23]
- Deployment: Adoptar Streamable HTTP en producción y stdio en desarrollo; definir health endpoints; configurar autoscaling y circuit breakers.[^16][^17]

Modelo de madurez y roadmap. Para pasar de inicial a optimizado, se recomienda una ruta con hitos claros.

### Tabla 11. Roadmap de madurez MCP

| Hito                          | Descripción                                                                | Métricas clave                                  |
|-------------------------------|----------------------------------------------------------------------------|-------------------------------------------------|
| Baseline controlado           | OAuth 2.1, vaults, OTel básico, Streamable HTTP en prod                   | Error auth < 0.5%, latencia p95 < objetivo      |
| Observabilidad ampliada       | Paneles por herramienta/cliente, alertas de SLO, trazas multi-servicio    | MTTR < objetivo, cobertura de trazas > 90%      |
| Gobernanza integral           | Registro interno, kill-switches, SSO/SCIM, listas blancas                 | Cumplimiento 100% de servidores aprobados       |
| Optimización y resiliencia    | Backpressure, circuit breakers, caching selectivo                         | Disponibilidad > objetivo, coste por llamada ↓  |

Al alinear la adopción MCP con prácticas enterprise —SSO/SCIM, OTel, CI/CD con versionado de capacidades, OPA/IdP integrados— se maximiza el retorno operativo y se minimiza el riesgo. La separación Autorización/Recursos, sumada a gateways como plano de control, es el cimiento para escalar con seguridad y observabilidad. El versionado explícito y la gestión dinámica de herramientas reducen costes de tokens y mejoran la calidad de interacción LLM-servidor. En definitiva, MCP deja de ser un “adaptador” para convertirse en una plataforma operativa con contrato, políticas y trazabilidad propios.

Brechas de información. Quedan pendientes: el detalle exhaustivo del changelog 2025-06-18 más allá de resúmenes; el grado de soporte real de elicitation/sampling en hosts主流; la definición final de semantic conventions de OTel para MCP; evidencia empírica pública de implementaciones en gran escala; y la madurez de DCR y del parámetro resource entre IdPs empresariales. Estas brechas deben gestionarse con pilotos controlados, pruebas de compatibilidad y acuerdos con proveedores.

---

## Referencias

[^1]: Specification - Model Context Protocol (2025-06-18). https://modelcontextprotocol.io/specification/2025-06-18
[^2]: Versioning - Model Context Protocol. https://modelcontextprotocol.io/specification/versioning
[^3]: 15 Best Practices for Building MCP Servers in Production. https://thenewstack.io/15-best-practices-for-building-mcp-servers-in-production/
[^4]: MCP Server Best Practices: Production-Grade Development Guide. https://mcpcat.io/blog/mcp-server-best-practices/
[^5]: Specification and documentation for the Model Context Protocol. https://github.com/modelcontextprotocol/modelcontextprotocol
[^7]: MCP Specification Authorization (2025-06-18/basic/authorization). https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization
[^8]: MCP Specification Security Best Practices (2025-06-18/basic/security_best_practices). https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices
[^9]: OAuth for MCP - Emerging Enterprise Patterns for Agent Authorization. https://blog.gitguardian.com/oauth-for-mcp-emerging-enterprise-patterns-for-agent-authorization/
[^10]: RFC 8707: Resource Indicators for OAuth 2.0. https://www.rfc-editor.org/rfc/rfc8707
[^11]: RFC 9728: OAuth 2.0 Protected Resource Metadata. https://datatracker.ietf.org/doc/html/rfc9728/
[^12]: OpenTelemetry. https://opentelemetry.io/
[^13]: Secure MCP Server Deployment at Scale: The Complete Guide. https://mcpmanager.ai/blog/secure-mcp-server-deployment-at-scale-the-complete-guide/
[^14]: Building Scalable MCP Servers with Domain-Driven Design. https://medium.com/@chris.p.hughes10/building-scalable-mcp-servers-with-domain-driven-design-fb9454d4c726
[^15]: AWS Labs - MCP (Available MCP servers). https://github.com/awslabs/mcp?tab=readme-ov-file#available-mcp-servers
[^16]: MCP Specification: Transports. https://modelcontextprotocol.io/specification/2025-06-18/basic/transports
[^17]: How to build secure and scalable remote MCP servers. https://github.blog/ai-and-ml/generative-ai/how-to-build-secure-and-scalable-remote-mcp-servers/
[^18]: Model Context Protocol TypeScript SDK. https://github.com/modelcontextprotocol/typescript-sdk
[^19]: PyJWT - Python library. https://github.com/jpadilla/pyjwt
[^20]: Azure Key Vault - Basic Concepts. https://learn.microsoft.com/azure/key-vault/general/basic-concepts
[^21]: AWS Secrets Manager - User Guide. https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html
[^22]: Introducing MCP server monitoring - Sentry. https://blog.sentry.io/introducing-mcp-server-monitoring/
[^23]: Mastering MCP Observability: Why It's Essential and How To Achieve It. https://mcpmanager.ai/blog/mcp-observability/
[^24]: MCP Authorization is a Non-Starter for Enterprise. https://www.solo.io/blog/mcp-authorization-is-a-non-starter-for-enterprise
[^25]: JSON-RPC 2.0 Specification. https://www.jsonrpc.org/
[^26]: RFC 2119: Key words for use in RFCs. https://datatracker.ietf.org/doc/html/rfc2119
[^27]: RFC 8174: Clarifying Requirements for Uppercase vs Lowercase. https://datatracker.ietf.org/doc/html/rfc8174
[^28]: BCP 14: RFC Style Guide. https://datatracker.ietf.org/doc/html/bcp14
[^29]: Language Server Protocol (LSP). https://microsoft.github.io/language-server-protocol/
[^30]: HashiCorp Vault: What is Vault. https://developer.hashicorp.com/vault/docs/about-vault/what-is-vault
[^31]: Roadmap - Model Context Protocol. https://modelcontextprotocol.io/development/roadmap
[^32]: Update on the Next MCP Protocol Release. https://modelcontextprotocol.info/blog/mcp-next-version-update/
[^33]: Unblocking enterprise MCP adoption with profiles - SGNL. https://sgnl.ai/2025/09/enterprise-mcp-adoption-with-profiles/