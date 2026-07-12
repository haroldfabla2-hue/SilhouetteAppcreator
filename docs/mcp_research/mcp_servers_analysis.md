# Servidores MCP en 2025: Panorama, comparativa técnica y hoja de ruta de adopción

## Resumen ejecutivo

El Model Context Protocol (MCP) se ha consolidado en 2025 como la columna vertebral para conectar de forma segura y estandarizada modelos de lenguaje con herramientas y datos externos. Esta investigación analiza el ecosistema de servidores MCP desde la doble perspectiva técnica y de adopción, y propone una hoja de ruta pragmática para evolucionar hacia despliegues híbridos con controles de seguridad y observabilidad de nivel empresarial. La evidencia procede del repositorio oficial de servidores, la galería de ejemplos, los SDKs oficiales, documentación de autorización, análisis de seguridad de terceros y guías de clientes como VS Code y Claude Desktop, entre otros[^1][^2][^3][^5][^6][^7][^8][^9][^10][^11][^12][^18][^20][^21].

Principales hallazgos:
- El ecosistema ha madurado, con siete servidores oficiales de referencia activos (Everything, Fetch, Filesystem, Git, Memory, Sequential Thinking, Time) que ilustran las capacidades de herramientas, recursos y prompts. Además, existe un conjunto relevante de integraciones oficiales y comunitarias, y un bloque archivado por razones históricas o de transición[^2][^3].
- La autorización basada en OAuth 2.1 está definida en la especificación y las guías de MCP, con flujos explícitos de descubrimiento y protección de recursos (PRM, DCR, introspección de tokens). Aun así, la adopción real en la base instalada de servidores de código abierto es baja: 88% requiere credenciales, 53% usa credenciales estáticas (API keys/PATs) y apenas 8.5% implementa OAuth[^7][^8][^10].
- Los transportes han evolucionado. Mientras stdio sigue siendo idóneo para entornos locales, Streamable HTTP desplaza a SSE (deprecado) en despliegues remotos y gestionados, con soporte nativo en SDKs y clientes (VS Code, Claude Desktop, MCP Inspector), además de consideraciones de CORS para clientes basados en navegador[^5][^6][^18].
- La comparación funcional entre familias de servidores (navegador/automatización, datos/analytics, DevOps/Cloud, comunicación/colaboración, multimedia/creatividad) revela patrones consistentes: alta cobertura de tools, menor profundidad en prompts y sampling, y variaciones notables en seguridad/observabilidad según proveedor.
- La observabilidad y la gobernanza siguen siendo la frontera de madurez. Los modelos híbridos (remotos, gestionados, workstation) requieren trazabilidad, correlación de eventos y controles de riesgo como sandboxing, mínimos privilegios, listas blancas y circuit breakers. La evidencia empírica disponible exige reforzar políticas y automatización de seguridad[^10][^12][^20][^21].

Implicaciones para CTOs y líderes de plataforma: el mayor retorno se obtiene con una arquitectura híbrida que combine servidores remotos para SaaS populares, gestionados para cargas internas críticas y workstation para prototipado local. La pieza organizativa clave es un gateway MCP que acts as control plane: autorización unificada, políticas de herramientas, inventario y auditoría, y límites de coste/latencia. 

Recomendaciones ejecutivas:
- Consolidar un catálogo de servidores aprobados (registro interno) y un gateway MCP como plano de control.
- Forzar OAuth 2.1 con tokens de corta duración y scopes por herramienta/operación; priorizar DCR cuando tenga sentido operacional.
- Aplicar sandboxing para automatización de navegador y ejecución de comandos; fijar versiones de servidores y validar integridad.
- Establecer una línea base de observabilidad (traza, logs, métricas, coste) y SLOs por caso de uso; activar alertas de inyección de prompt y rug-pull.
- Adoptar Streamable HTTP en servidores remotos; mantener stdio para prototipos locales, con controles reforzados de identidad y sesión.

Hoja de ruta de 90 días (propuesta):
- Piloto (remoto): integrar GitHub MCP y uno o dos servidores de datos/analytics con OAuth y gateway.
- Gestiónados (core): desplegar Filesystem y Git en infraestructura controlada con Streamable HTTP, CORS, OTel y límites de coste/latencia.
- Workstation (prototipos): habilitar stdio local con políticas de desktop, red y secretos; activar guardarraíles.

El resto del informe desarrolla la metodología, el contexto normativo, la taxonomía del ecosistema, la comparativa técnica y de seguridad, y la hoja de ruta operativa.

## Metodología y alcance

Fuentes. Se han utilizado referencias primarias y secundarias con jerarquía clara: el sitio oficial de MCP (especificaciones, guías y ejemplos), los repositorios oficiales de servidores y SDKs, la documentación de clientes (VS Code, Claude Desktop), y el repositorio de GitHub con integraciones oficiales/comunitarias, complementados por análisis de seguridad de terceros[^1][^2][^3][^5][^6][^10][^11][^12][^16][^18][^19][^20][^21].

Criterios de inclusión. 
- Servidores: implementaciones activas oficiales (referencia), integraciones mantenidas por empresas y comunidades, y el bloque archivado. 
- Comunitarios: repositorios verificables con actividad y documentación. 
- Empresariales: servidores publicados por proveedores con soporte/SLAs o documentación de producto.
- Dimensiones de análisis: capacidades (tools/resources/prompts), transporte (stdio/Streamable HTTP), seguridad (credenciales, OAuth, scopes), observabilidad (logs/metrics/traces), mantenimiento y madurez.

Limitaciones. 
- La cobertura del repositorio “awesome” es amplia pero no exhaustiva; se revisó de forma selectiva y se citan ejemplos representativos[^22].
- El repositorio de servidores incluye integraciones empresariales en evolución; no todas exponen el mismo nivel de detalle técnico.
- No existen métricas comparables de rendimiento (latencia, throughput, coste por tool call) en repos públicos; se recomienda instrumentación local estandarizada.
- Falta un inventario completo y actualizado de estrategias de observabilidad por servidor; se propone una línea base que cada organización deberá adaptar.
- Los requisitos de cumplimiento varían por proveedor y no están normalizados.

## Contexto y fundamentos de MCP

Arquitectura. MCP define una arquitectura cliente‑servidor con tres actores: el host (p. ej., VS Code o Claude Desktop), el cliente MCP (que conecta con un único servidor en nombre del host) y el servidor MCP (que expone herramientas, recursos y prompts). La comunicación se rige por JSON‑RPC 2.0, con negociación de capacidades y ciclo de vida explícito (initialize/shutdown/exit)[^1][^2].

Capa de datos y transportes. La capa de datos define los métodos para descubrir e invocar herramientas (tools/list, tools/call), listar recursos y plantillas (resources/list, resources/templates/list), y gestionar prompts. Para el transporte, MCP soporta stdio (ideal para comunicación local de baja latencia) y HTTP con streaming; la especificación actual promueve Streamable HTTP sobre SSE (deprecado) en escenarios remotos y gestionados[^1][^5][^6].

Primitivos. 
- Tools: acciones invocables por el modelo, con esquemas JSON de entrada/salida y posibles barreras de aprobación por el usuario. 
- Resources: fuentes pasivas de contexto, con URIs y soporte para plantillas parametrizadas. 
- Prompts: plantillas reutilizables para guiar la interacción del modelo. 
- Sampling/complete: primitivos para pedir al cliente que complete texto con el LLM, bajo control del usuario y del host[^1][^2][^5].

Ecosistema de SDKs y clientes. Los SDKs oficiales (TypeScript y Python) implementan la especificación completa, mientras que clientes como VS Code y Claude Desktop integran MCP de forma nativa para descubrimiento, ejecución y autorización. MCP Inspector facilita la depuración extremo a extremo[^5][^6][^11][^18][^19][^20][^21].

Para visualizar el impacto de los transportes en despliegue y seguridad, la Tabla 1 resume su idoneidad.

Tabla 1. Matriz de transportes MCP vs escenarios de despliegue y seguridad
| Transporte        | Latencia esperada | Idoneidad (local/remoto/gestionado) | Seguridad de transporte | CORS | Notas relevantes |
|-------------------|-------------------|--------------------------------------|-------------------------|------|------------------|
| stdio             | Muy baja          | Local / Workstation                  | Canal local del proceso | N/A  | Ideal para prototipos y acceso a archivos; requiere controles en el host para secretos y ejecución. |
| Streamable HTTP   | Baja‑media        | Remoto / Gestionado                  | HTTPS                   | Sí   | Sustituye SSE; favorece control de sesión, autorización y observabilidad remota; soporte en SDKs TS/Python y clientes. |
| HTTP + SSE (legacy) | Variable        | Remoto (legacy)                      | HTTPS                   | Sí   | Deprecado; mantenido por compatibilidad en algunos clientes. |

La elección no es binaria; muchas organizaciones combinan stdio en estaciones de trabajo con Streamable HTTP en infraestructuras gestionadas. La clave es aplicar criterios de seguridad y trazabilidad homogéneos, incluyendo CORS cuando corresponda[^5][^6][^18].

## Taxonomía del ecosistema de servidores MCP

Mapa de categorías. El ecosistema puede agruparse en:
- Agregadores y meta‑servidores.
- Automatización de navegador.
- Bases de datos y analytics.
- DevOps y Cloud.
- Comunicación/colaboración.
- Multimedia y creatividad.
- Científico/biomédico.
- Otros (finanzas, mapas, observabilidad).

Ciclo de vida. El repositorio oficial distingue implementaciones de referencia activas, integraciones oficiales (por empresas) y servidores archivados por razones históricas o de reemplazo. GitHub mantiene una sección viva de integraciones oficiales/comunitarias con más de un centenar de entradas recientes[^2][^3].

Para situar el panorama, la Tabla 2 enumera categorías con ejemplos representativos.

Tabla 2. Mapa de categorías y ejemplos representativos
| Categoría                    | Ejemplos representativos | Fuente |
|-----------------------------|---------------------------|--------|
| Automatización de navegador | Puppeteer (archivado), Playwright (Microsoft), Browserbase | [^3][^13][^14][^25] |
| DevOps y Cloud              | AWS Labs, Azure, Cloudflare, k8s, Alibaba Cloud | [^15][^16][^17] |
| Datos y analytics           | ClickHouse, Apache Pinot, MongoDB, Chroma | [^17][^28][^29][^30] |
| Comunicación/colaboración   | GitHub MCP Server, Atlassian (Jira/Confluence), Slack (archivado) | [^23][^24][^27][^3] |
| Multimedia/creatividad      | Figma, Cloudinary, Cartesia | [^24][^32][^33] |
| Observabilidad/LLMops       | AgentOps, Phoenix (Arize), Axiom | [^31][^34][^35] |
| Agregadores/meta‑servidores | Agregadores y gateways diversos (comunitarios) | [^22] |

### Servidores oficiales (referencia activa)

Los siete servidores de referencia activos cubren patrones comunes de integración y sirven como contrato de interoperabilidad para el resto del ecosistema.

Tabla 3. Servidores de referencia activos
| Servidor             | Primitivos soportados | Transporte | Casos de uso típicos | Observaciones |
|----------------------|-----------------------|-----------|----------------------|---------------|
| Everything           | Tools, Resources, Prompts, Sampling | stdio / Streamable HTTP | Demostración integral y pruebas | Expone el abanico de capacidades MCP. |
| Fetch                | Tools, Resources      | stdio / Streamable HTTP | Recuperación y transformación de contenido web | Útil para enriquecer contexto con fuentes públicas. |
| Filesystem           | Tools, Resources      | stdio / Streamable HTTP | Operaciones de archivo seguras (whitelists, sandbox) | Fomenta controles de acceso y rutas restringidas. |
| Git                  | Tools, Resources      | stdio / Streamable HTTP | Lectura/búsqueda/manipulación de repos | Piloto para flujos Dev y DevOps. |
| Memory               | Resources             | stdio / Streamable HTTP | Memoria persistente tipo grafo de conocimiento | Base para RAG/ontologías. |
| Sequential Thinking  | Prompts, Tools        | stdio / Streamable HTTP | Planificación/reflexión paso a paso | Mejora de calidad en tareas complejas. |
| Time                 | Tools                 | stdio / Streamable HTTP | Conversión de tiempo y zonas horarias | Utilidad transversal. |

Fuente: galería oficial de ejemplos[^2].

### Servidores archivados (legacy) y razones de archivado

El repositorio de servidores archivados agrupa integraciones que fueron relevantes en etapas tempranas o han sido sustituidas por implementaciones mantenidas por sus proveedores.

Tabla 4. Servidores archivados y razones
| Nombre         | Razón de archivado (indicativa) | Alternativa oficial/comunitaria |
|----------------|----------------------------------|----------------------------------|
| GitHub         | Reemplazo por servidor oficial mantenido por GitHub | GitHub MCP Server[^23][^24] |
| Slack          | Reemplazos comunitarios/empresariales | Integraciones de terceros |
| Google Drive   | Reemplazos comunitarios/empresariales | Integraciones de terceros |
| Google Maps    | Reemplazos comunitarios/empresariales | Integraciones de terceros |
| PostgreSQL/SQLite | Transición a nuevas implementaciones | Nuevos servidores en repos y comunidad |
| Brave Search   | Reemplazos comunitarios/empresariales | Integraciones de terceros |
| Sentry         | Reemplazos comunitarios/empresariales | Integraciones de terceros |
| Puppeteer      | Reemplazos por servidores mantenidos (p. ej., Playwright) | Playwright MCP[^25] |

Fuente: repositorio de servidores archivados y ejemplos oficiales[^3].

### Integraciones oficiales de empresas

El repositorio de servidores recoge una creciente lista de integraciones mantenidas por empresas. La Tabla 5 ilustra el abanico y su orientación.

Tabla 5. Integraciones oficiales por empresa (muestra)
| Empresa/Producto | Función principal | Transporte | Seguridad | Observabilidad |
|------------------|-------------------|-----------|-----------|----------------|
| GitHub           | Repos, Issues, PRs, búsqueda | Streamable HTTP | OAuth recomendado por guías | Logging y auditoría en cliente/host[^23][^24] |
| Microsoft (Azure, Playwright) | Cloud, DevOps, automatización navegador | stdio / Streamable HTTP | OAuth (Entra/GitHub), scopes | Logs en cliente/servidor[^25] |
| AWS Labs         | Integración con servicios AWS | Streamable HTTP | OAuth/credenciales temporales (según servicio) | Cloud observability[^15] |
| Figma            | Diseño/recursos de archivo | Streamable HTTP | OAuth | Logs/UI cliente[^24] |
| Cloudflare       | Workers/KV/R2/D1 | Streamable HTTP | OAuth | Logs/analytics[^17] |
| ClickHouse       | Consultas analíticas | Streamable HTTP | Auth por endpoint | Telemetría propia[^28] |
| MongoDB          | Operaciones de BD | Streamable HTTP | Auth + roles | Logging/host[^29] |
| Chroma           | Vector DB y búsquedas | Streamable HTTP | Auth (si configurado) | Observabilidad vía host[^30] |
| AgentOps, Phoenix, Axiom | Observabilidad LLM y eventos | Streamable HTTP | Auth (varía) | Trazas/métricas/logs[^31][^34][^35] |

Las integraciones empresariales suelen publicar guías operativas y límites de uso, pero difieren en mecanismos de autenticación y observabilidad. La estandarización vía OAuth 2.1, scopes por herramienta y métricas comunes sigue siendo una brecha a cerrar[^3][^16][^17][^23][^24].

### Servidores comunitarios (muestra representativa por categoría)

Además de las listas curadas, existen repositorios comunitarios que amplían rápidamente la cobertura funcional. Ejemplos: 
- Automatización/navegador: Browserbase (cloud), Playwright MCP (Microsoft). 
- Datos/analytics: ClickHouse, Apache Pinot. 
- Multimedia/creatividad: Cloudinary, Cartesia. 
- Observabilidad: AgentOps, Phoenix, Axiom[^13][^14][^25][^28][^32][^33][^34][^35].

## Implementaciones oficiales y SDKs

Los SDKs oficiales habilitan tanto servidores como clientes interoperables.

- TypeScript SDK. Implementa la especificación completa, soporta stdio y Streamable HTTP, y expone primitivos de tools, resources, prompts y sampling. Incluye utilidades para servidores dinámicos, notificaciones debounced y proxy de autorización OAuth. Requiere configuración CORS cuando se usa desde navegadores[^5].
- Python SDK. Soporta stdio y HTTP, con patrones equivalentes para tools/resources/prompts y compatibilidad con clientes y servidores MCP[^6].

Clientes de referencia:
- VS Code. Integra herramientas MCP, prompts y recursos; soporta autorización (OAuth 2.1, DCR, credenciales de cliente), streams http y stdio, instrucciones de servidor y manejo de CORS en clientes basados en navegador[^18][^19].
- Claude Desktop. Permite conectar servidores locales y remotos y utilizar las herramientas expuesta por el host, con guías de inicio y soporte para transportes compatibles[^20][^21].
- MCP Inspector. Facilita depuración, inspección de mensajes, trazas y pruebas de herramientas y recursos, útil en entornos de desarrollo[^11].

La Tabla 6 resume el soporte por SDK/cliente.

Tabla 6. Matriz de soporte SDKs y clientes
| SDK/Cliente           | stdio | Streamable HTTP | OAuth/DCR | CORS | Features clave |
|-----------------------|------:|----------------:|----------:|-----:|----------------|
| TypeScript SDK        | Sí    | Sí              | Sí (proxy/proveedor) | Sí (configurable) | Tools/resources/prompts/sampling, servidores dinámicos, debouncing[^5] |
| Python SDK            | Sí    | Sí              | Depende de implementación | N/A | Idem, interoperable con clientes[^6] |
| VS Code               | Sí    | Sí              | Sí (OAuth 2.1, DCR, cliente) | Sí | Herramientas, prompts, recursos, server instructions, debugging[^18][^19] |
| Claude Desktop        | Sí    | Sí              | Depende de servidor | Sí (para HTTP) | Conexión a servidores locales/remotos, uso de tools[^20][^21] |
| MCP Inspector         | Sí    | Sí              | N/A       | N/A | Depuración y observación de extremo a extremo[^11] |

## Análisis técnico comparativo

Patrones arquitectónicos. 
- Servidores locales (stdio) para prototipado y acceso a archivos/hardware. 
- Servidores remotos (Streamable HTTP) para integraciones SaaS y multiinquilino. 
- Servidores gestionados en la propia infraestructura (Docker/Kubernetes) para control de seguridad, costes y observabilidad, con variantes dedicadas/compartidas[^12][^20][^21].

Ecosistema de transportes. stdio se mantiene como primera opción para desarrollo local; Streamable HTTP emerge como estándar para producción remota; SSE queda como legado. Esta transición acompaña la necesidad de CORS, sesiones y autorización robusta en clientes web/IDE[^5][^6][^18].

Compatibilidad de clientes. VS Code y Claude Desktop soportan ambos transportes; Inspector acelera la depuración; los SDKs garantizan interoperabilidad. La principal fricción práctica radica en CORS y en la configuración de sesiones/tokens[^5][^6][^11][^18][^20][^21].

Tabla 7. Matriz de transportes y compatibilidad cliente/servidor
| Transport | Hosts/Clientes con soporte | Notas |
|-----------|----------------------------|-------|
| stdio     | VS Code, Claude Desktop, Inspector | Ideal para local-first; sin CORS; canal de proceso del host. |
| Streamable HTTP | VS Code, Claude Desktop, Inspector | Sustituye SSE; requiere CORS en navegador; sesiones y OAuth más naturales[^5][^18]. |
| SSE (legacy) | Algunos clientes con compatibilidad inversa | Deprecado; mantener solo por compatibilidad temporal[^5]. |

Limitaciones y restricciones. 
- CORS: necesario en clientes basados en navegador; exponer y permitir encabezados específicos (p. ej., identificadores de sesión)[^5][^18].
- SLOs: sin benchmarks públicos; se requieren métricas y acuerdos operativos por caso de uso.
- Coste por herramienta: no estandarizado; controlar límites de tokens y sampling.
- Gestión de sesión: depender de cabeceras/cookies y timeouts; reforzar revocación e idempotencia en herramientas de escritura.

## Comparativa de capacidades de herramientas, recursos y prompts

Las diferencias entre familias de servidores se observan mejor en la cobertura funcional y la profundidad de controles. A continuación, una matriz cualitativa basada en fuentes públicas.

Tabla 8. Capacidades comparadas (muestra)
| Servidor/Categoría | Tools | Resources | Prompts | Sampling | Auth | Observabilidad |
|--------------------|:-----:|:---------:|:-------:|:--------:|:----:|:--------------:|
| Everything (ref.)  |  ✓    |    ✓      |   ✓     |    ✓     |  —   | — |
| Filesystem (ref.)  |  ✓    |    ✓      |   —     |    —     |  —   | — |
| Git (ref.)         |  ✓    |    ✓      |   —     |    —     |  —   | — |
| GitHub (empresarial) | ✓  |    ✓      |   —     |    —     |  ✓   | Medio (depende de host)[^23][^24] |
| Playwright (oficial) | ✓ |    —      |   —     |    —     |  —   | Bajo/medio (host + server)[^25] |
| Browserbase (cloud) | ✓  |    —      |   —     |    —     |  ✓   | Medio/alto (cloud)[^14] |
| ClickHouse (oficial) | ✓ |    ✓ (consulta) | — | — | ✓ | Medio (propio + host)[^28] |
| MongoDB (oficial)  |  ✓    |    ✓      |   —     |    —     |  ✓   | Medio/alto[^29] |
| Chroma (oficial)   |  ✓    |    ✓      |   —     |    —     |  ✓   | Medio (host + app)[^30] |
| Cloudflare (oficial) | ✓ |    ✓      |   —     |    —     |  ✓   | Alto (plataforma)[^17] |
| AgentOps (observ.) |  ✓    |    —      |   —     |    —     |  ✓   | Alto (LLM/trazas)[^31] |
| Phoenix (observ.)  |  ✓    |    —      |   —     |    —     |  ✓   | Alto (LLM/trazas)[^34] |
| Axiom (observ.)    |  ✓    |    —      |   —     |    —     |  ✓   | Alto (logs/metrics)[^35] |
| Figma (oficial)    |  ✓    |    ✓      |   —     |    —     |  ✓   | Medio (host + app)[^24] |
| Cartesia (multimodal) | ✓ |   —       |   —     |    —     |  ✓   | Medio[^33] |

Notas:
- “Auth” indica la disponibilidad de mecanismos modernos (OAuth) o alternativos, según documentación pública y guías del proveedor.
- “Observabilidad” refleja la capacidad de trazas/logs/metrics desde el servidor y la integración con el host.
- La profundidad de recursos varía: algunos servidores exponen resultados de consulta como resources; otros operan exclusivamente vía tools.

Familias representativas:

### Automatización de navegador
Playwright MCP (oficial) y Browserbase (cloud) habilitan navegación automatizada, scraping y formularios. Las diferencias clave incluyen la ubicación del navegador (local vs cloud), controles de sandbox y credenciales, y la facilidad de integración en IDEs y pipelines[^14][^25]. Consideraciones de seguridad: sanitizar entradas, sandboxing y límites de tasa; observabilidad: capturas de red/consola y registro estructurado.

### Datos y analytics
ClickHouse, MongoDB y Chroma cubren consultas analíticas, operaciones de documentos y búsqueda vectorial. El control de acceso es heterogéneo (endpoints autenticados, roles de BD, tokens de plataforma). Se recomienda instrumentar latencia, cardinalidad de resultados y coste por consulta para evitar sorpresas en costes y tiempos de respuesta[^28][^29][^30].

### DevOps y Cloud
AWS Labs, Azure y Cloudflare exponen primitivos cloud y DevOps (gestión de recursos, automatización y consulta). La autorización suele requerir scopes finos y tokens de corta duración. Observabilidad: integrar métricas de plataforma con trazas de herramientas para diagnósticos y auditoría[^15][^16][^17].

### Comunicación y colaboración
GitHub MCP Server facilita interacción con repos, issues y PRs. Atlassian ofrece acceso a Jira y Confluence, enfatizando el control de permisos y la trazabilidad en entornos corporativos[^23][^24][^27]. Riesgos típicos: exfiltración de metadatos sensibles y permisos excesivos; mitigación: scopes mínimos y flujos de aprobación.

### Multimedia y creatividad
Figma, Cloudinary y Cartesia cubren diseño, gestión de medios y voz. Las consideraciones principales son la protección de contenidos y PII en assets y los límites de coste en generación de contenido. Observabilidad: seguimiento de uso por herramienta y alertas por picos anómalos[^32][^33].

## Seguridad y gobernanza

La seguridad en MCP pivota sobre autorización, principio de mínimo privilegio, aislamiento y observabilidad. El ecosistema ha avanzado en especificaciones, pero la adopción real todavía adolece de credenciales estáticas y prácticas débiles.

Autorización (OAuth 2.1) en MCP. 
- Flujo con PRM (Protected Resource Metadata): el servidor responde 401 con un encabezado WWW‑Authenticate que apunta al PRM; el cliente descubre metadatos, el servidor de autorización (con OIDC/OAuth metadata), registra al cliente (DCR o pre‑registro), y completa la autorización con PKCE; el cliente usa access tokens de corta duración para invocar tools/resources, con introspección y validación de audiencia cuando aplica[^7][^8].
- Scopes recomendados: granularidad por primitivo (p. ej., mcp:tools, mcp:resources) y por operación.
- Proveedores: soporta integración con Keycloak y proveedores OIDC/OAuth 2.1 empresariales[^7][^8].

Riesgos principales y controles. 
- Confused deputy: el servidor ejecuta acciones fuera de alcance. Controles: scopes mínimos, aprobación humana para operaciones sensibles, y token de corta duración[^9].
- Cadena de suministro: dependencias y código malicioso. Controles: firma de artefatos, SAST/SCA, políticas de actualización y pinning de versiones[^9].
- Inyección de prompt y de herramientas: prompts maliciosos manipularán el flujo. Controles: validación/escape de entradas, confirmación de usuario, listas blancas de herramientas, y logging para auditoría[^9].
- Sampling malicioso: servidores que fuerzan completados del modelo. Controles: mostrar/editable completions, límites de tokens/tiempo, control de modelo y coste[^5][^9].
- Credenciales estáticas y exposición: keys en variables de entorno sin rotación. Controles: OAuth, vaults, rotación y revocación acelerada[^10].

Estado de credenciales (2025). La investigación de Astrix sobre 5.205 repositorios muestra que 88% requiere credenciales, 53% usa API keys/PATs estáticos y apenas 8.5% implementa OAuth; 79% de las API keys se manejan por variables de entorno[^10]. La Tabla 9 sintetiza.

Tabla 9. Estado de credenciales en el ecosistema (Astrix 2025)
| Métrica | Valor |
|--------|-------|
| Servidores que requieren credenciales | 88% |
| Credenciales estáticas (API keys/PATs) | 53% |
| OAuth implementado | 8.5% |
| API keys en variables de entorno | 79% |

Matriz de riesgo‑control. La Tabla 10 alinea riesgos y mitigaciones recomendadas.

Tabla 10. Riesgos y controles recomendados
| Riesgo | Impacto | Probabilidad | Controles clave |
|--------|---------|--------------|-----------------|
| Confused deputy | Alto | Medio | OAuth 2.1, scopes por herramienta, aprobación para operaciones de escritura |
| Cadena de suministro | Alto | Medio | SAST/SCA, firma de código, pinning de versiones, SBOM |
| Inyección de prompt | Medio/Alto | Alto | Validación de entradas, listas blancas, confirmación de usuario, logging |
| Inyección de herramientas | Alto | Medio | Fijar versiones, diffs controlados, aprobación de cambios |
| Sampling malicioso | Medio | Bajo/Medio | Límites de tokens/tiempo, control de modelo, revisión de completions |
| Exposición de credenciales | Alto | Medio | Vaults, rotación, expiración corta, mTLS donde aplique |
| Falta de logs | Medio | Alto | Logging estructurado, correlación con trace_id, envío a SIEM |

Controles empresariales. Un gateway MCP centraliza autenticación/autorización, políticas de herramientas, inventario/registro de servidores aprobados y observabilidad unificada. Se recomiendan:
- OAuth 2.1 en todas las conexiones remotas; tokens < 15 minutos; refresh controlado.
- Sandboxing (contenedores) para browser automation y ejecución de comandos; perfiles de sistema restringidos.
- Listas blancas por herramienta y por caso de uso; circuit breakers y límites de tasa.
- Rotación de credenciales y revocación acelerada; mTLS y CORS estrictos.
- Auditoría exhaustiva y correlación de eventos; alertas por patrones de inyección de prompt[^12][^18][^21].

## Observabilidad y cumplimiento

La observabilidad es el cimiento de confianza y seguridad en producción. Un diseño mínimo viable debe capturar quién hizo qué, cuándo, con qué herramientas y con qué resultado, con latencia y coste por tool call.

Trazabilidad y logs. El patrón trace_id/parent_id en cada interacción facilita la correlación entre herramientas, prompts y resultados. La persistencia offline (brokers/colas) y el envío asincrónico a sistemas centrales (SIEM, APM) aumentan resiliencia y cumplimiento. En hosts como VS Code, los logs del servidor MCP pueden consultarse y correlacionarse con eventos del chat/agente[^12][^18].

Métricas y SLOs. La Tabla 11 propone una línea base.

Tabla 11. Métricas de observabilidad por servidor/cliente
| Dominio | Métrica | Descripción | Objetivo (ejemplo) |
|--------|---------|-------------|---------------------|
| Latencia | P50/P95 tool call | Tiempo de ejecución por herramienta | P95 < 2s (lectura), < 5s (escritura) |
| Fiabilidad | Tasa de error | % de tool calls fallidas | < 1% por día |
| Coste | Tokens por tool call | Coste medio y máximo | Control por presupuesto mensual |
| Seguridad | Accesos denegados | Intentos con scopes insuficientes | Alertas si > 5% |
| Trazas | Cobertura de trazas | % de requests con trace_id correlado | > 99% |
| Incidentes | MTTR | Tiempo medio de recuperación | < 30 min |

Trazabilidad extremo a extremo. Debe existir una cadena de correlación que conecte el intent/prompt del usuario, la tool invocada, los recursos consultados, los side effects (p. ej., una creación de issue) y el resultado final, incluyendo el modelo y parámetros usados (sampling), con límites de tokens/tiempo.

Alertas y SLOs. Umbrales por tipo de operación, alertas por inyección de prompt, picos de coste y llamadas recurrentes fuera de patrón. En entornos de workstation, reforzar auditoría local y política de secretos.

## Patrones de despliegue y operación

Remotos, gestionados y workstation. La elección óptima suele ser híbrida[^12]:
- Remotos: integraciones SaaS con endpoints HTTPS y OAuth; fáciles de conectar, pero con posibles puntos ciegos de observabilidad y dependencia de políticas de datos del proveedor.
- Gestionados: infra propia con contenedores/orquestación; mayor control de seguridad, coste y SLOs; pueden ser dedicados (aislamiento por usuario/agente) o compartidos (eficiencia).
- Workstation: prototipos locales vía stdio; acceso directo a archivos/hardware; escalar y securizar es más difícil.

Gateway MCP. Un gateway centraliza políticas de herramientas, autorización, límites de coste/latencia, logging y registro interno de servidores aprobados. Simplifica el onboarding por equipo y reduce servidores en la sombra[^12].

Comparativa de despliegues (Tabla 12).

Tabla 12. Opciones de despliegue
| Opción | Ventajas | Riesgos | Controles recomendados |
|--------|----------|---------|------------------------|
| Remoto | Fácil conexión; actualización rápida | Puntos ciegos; cumplimiento externo | OAuth 2.1; scopes mínimos; SLOs y logs centralizados |
| Gestionado (dedicado) | Aislamiento; control total | Coste y complejidad | Orquestación; observabilidad y límites de coste |
| Gestionado (compartido) | Eficiencia; operación unificada | Riesgo de aislamiento | Namespaces, cuotas, límites de tasa |
| Workstation (stdio) | Baja latencia; local-first | Difícil de escalar; secretos locales | Políticas de desktop; vaults; auditoría local |

## Arquitectura avanzada参考: Silhouette (Windows)

El diseño Silhouette aporta un ejemplo de arquitectura de nivel empresarial aplicada a MCP, con decisiones coherentes con un entorno de escritorio Windows y necesidades de omnipotencia segura.

Componentes clave.
- Router central (McpRouter) con registro de capacidades en SQLite: resuelve intents/capabilities, aplica políticas (TTL, RPS, scopes), valida esquemas y gestiona reintentos/fallback.
- Mensajería estandarizada (McpMessage) con trace_id/parent_id para correlación.
- Agentes adaptadores: PowerShell restringido, Playwright para web, UI Automation para escritorio; orquestados por el router.
- Persistencia y colas offline: broker con estados PENDING y limpieza por TTL; QueueWorker para reintentos.
- Observabilidad: EventSource (ETW) y OpenTelemetry; métricas de latencias, costes y violaciones de políticas.
- Seguridad avanzada: redacción de datos sensibles (RedactionRules), políticas WDAC/AppLocker, TLS/mTLS, secretos con DPAPI, PowerShell en Constrained Language Mode.

Tabla 13. Políticas iniciales (muestra)
| Intent           | Scope              | TTL (s) | RPS | requires_approval |
|------------------|--------------------|---------|-----|--------------------|
| plan.create      | agent.plan         | 60      | 10  | No                 |
| plan.review      | agent.critique     | 60      | 10  | No                 |
| tool.exec.ps     | tool.powershell    | 300     | 1   | Sí                 |
| tool.exec.fs.read| tool.filesystem    | 60      | 100 | No                 |

Aplicabilidad. El patrón router + registro de capacidades + agentes adaptadores es extrapolable a otros entornos (Linux/macOS) con equivalentes de sandboxing (containers, profiles de sistema) y secrets management. La clave es la separación de concerns: plano de control (políticas y enrutamiento), plano de ejecución (agentes/servidores) y plano de observabilidad (trazas/logs/metrics).

## Recomendaciones y hoja de ruta de adopción

Estrategia por fases.
1) Piloto remoto. Seleccionar 2‑3 servidores con alto valor (GitHub, datos/analytics, observabilidad). Forzar OAuth 2.1, scopes por herramienta, límites de tokens/tiempo, logging estructurado y auditoría básica. Gateway MCP como plano de control.
2) Núcleo gestionado. Migrar Servers críticos (Filesystem, Git, DBs internas) a infraestructura controlada con Streamable HTTP, CORS, OTel y límites de coste/latencia. Circuit breakers y listas blancas por herramienta.
3) Workstation seguro. Habilitar stdio para prototipos con políticas de escritorio (AppLocker/WDAC), vault de secretos y auditoría local. Exportar trazas al backend corporativo.

Estandarización de seguridad.
- OAuth 2.1 con DCR cuando proceda; tokens < 15 min; scopes mcp:tools y mcp:resources por operación.
- Vaults y rotación de credenciales; mTLS en APIs internas.
- Fijar versiones de servidores; revisión de diffs; listas blancas; aprobación para operaciones de escritura.
- Sandboxing en browser automation y ejecución de comandos; perfiles de sistema restringidos.

Observabilidad.
- Trazas con trace_id/parent_id; logs estructurados; métricas por tool call y por modelo (sampling).
- Dashboards por servidor/categoría; alertas de inyección de prompt y picos de coste; SLOs por caso de uso.

Gobernanza.
- Registro interno de servidores aprobados con propietarios, políticas y alcance; evitar servidores en la sombra.
- Catálogo de herramientas por equipo; coste budgets; revisiones periódicas.

KPIs. Adopción por equipo; % servidores con OAuth; latencia P95; tasa de errores; coste por 1.000 tool calls; incidentes de seguridad; MTTR. 

Tabla 14. Plan de implementación por fases
| Fase | Objetivos | Entregables | Riesgos | Dependencias |
|------|-----------|-------------|---------|--------------|
| Piloto remoto | Validar valor y seguridad | 2‑3 servidores integrados con OAuth y gateway | Configuración de OAuth y CORS | Acceso a proveedores; gateway |
| Núcleo gestionado | Control y SLOs | Infra orquestada, OTel, límites de coste/latencia | Complejidad operativa | Orquestación; SIEM/APM |
| Workstation | Productividad dev | stdio + políticas desktop y vault | Escala y secreto local | Política de endpoints |

## Apéndices

Glosario.
- MCP: Model Context Protocol, estándar abierto para conectar LLMs con herramientas y datos. 
- Host/Cliente/Servidor: actores en la arquitectura MCP. 
- Tools/Resources/Prompts: primitivos de acción, contexto y plantillas. 
- Sampling/complete: peticiones al LLM desde servidores MCP. 
- OAuth 2.1/PRM/DCR: autorización moderna, metadatos de recurso protegido y registro dinámico de clientes. 
- stdio/Streamable HTTP/SSE: transportes de MCP; SSE es deprecado en favor de Streamable HTTP.

SDKs y herramientas. TypeScript SDK, Python SDK y MCP Inspector[^5][^6][^11].

Directorio (enlaces). La lista de servidores oficiales, integraciones empresariales y ejemplos activos se mantiene en los repositorios y sitios de referencia citados a lo largo del informe[^2][^3][^16].

Checklist de seguridad/observabilidad por servidor.
- ¿Usa OAuth 2.1? ¿Scopes finos por herramienta?
- ¿Tokens de corta duración? ¿Rotación y revocación?
- ¿Sandboxing para ejecución/comandos? ¿Perfilado de sistema?
- ¿Logging estructurado con trace_id? ¿Métricas de latencia y coste?
- ¿Límites de tasa y circuit breakers? ¿Listas blancas de herramientas?
- ¿CORS configurado? ¿Sesiones y timeouts definidos?
- ¿Versionado y verificación de integridad?

## Referencias

[^1]: Model Context Protocol – Sitio oficial. https://modelcontextprotocol.io  
[^2]: Example Servers – Model Context Protocol. https://modelcontextprotocol.io/examples  
[^3]: modelcontextprotocol/servers (Repositorio de servidores MCP). https://github.com/modelcontextprotocol/servers  
[^4]: Introducing the Model Context Protocol – Anthropic. https://www.anthropic.com/news/model-context-protocol  
[^5]: SDK oficial de TypeScript para MCP. https://github.com/modelcontextprotocol/typescript-sdk  
[^6]: SDK oficial de Python para MCP. https://github.com/modelcontextprotocol/python-sdk  
[^7]: Authorization (Borrador) – Especificación MCP. https://modelcontextprotocol.io/specification/draft/basic/authorization  
[^8]: Tutorial: Authorization en MCP (OAuth 2.1). https://modelcontextprotocol.io/docs/tutorials/security/authorization  
[^9]: Model Context Protocol: Security risks and controls – Red Hat. https://www.redhat.com/en/blog/model-context-protocol-mcp-understanding-security-risks-and-controls  
[^10]: State of MCP Server Security 2025 – Astrix. https://astrix.security/learn/blog/state-of-mcp-server-security-2025/  
[^11]: MCP Inspector. https://github.com/modelcontextprotocol/inspector  
[^12]: Secure MCP Server Deployment at Scale – MCP Manager. https://mcpmanager.ai/blog/secure-mcp-server-deployment-at-scale-the-complete-guide/  
[^13]: mcp-server-playwright – Automata Labs. https://github.com/Automata-Labs-team/MCP-Server-Playwright  
[^14]: Browserbase MCP Server. https://github.com/browserbase/mcp-server-browserbase  
[^15]: awslabs/mcp. https://github.com/awslabs/mcp  
[^16]: Azure MCP Server – Microsoft. https://github.com/microsoft/mcp/tree/main/servers/Azure.Mcp.Server  
[^17]: Cloudflare MCP Server. https://github.com/cloudflare/mcp-server-cloudflare  
[^18]: Guía MCP para VS Code. https://code.visualstudio.com/api/extension-guides/ai/mcp  
[^19]: Use MCP servers in VS Code. https://code.visualstudio.com/docs/copilot/customization/mcp-servers  
[^20]: Conectar a servidores MCP locales – MCP docs. https://modelcontextprotocol.io/docs/develop/connect-local-servers  
[^21]: Claude Desktop (descarga y contexto MCP). https://claude.ai/redirect/website.v1.511b92f9-8255-4545-abf4-9817c96cb7d2/download  
[^22]: awesome-mcp-servers – Lista curada. https://github.com/punkpeye/awesome-mcp-servers  
[^23]: A practical guide to the GitHub MCP server. https://github.blog/ai-and-ml/generative-ai/a-practical-guide-on-how-to-use-the-github-mcp-server/  
[^24]: Use the GitHub MCP server – GitHub Docs. https://docs.github.com/en/copilot/how-tos/provide-context/use-mcp/use-the-github-mcp-server  
[^25]: playwright-mcp – Microsoft. https://github.com/microsoft/playwright-mcp  
[^26]: Model Context Protocol Integrations – Neo4j. https://neo4j.com/developer/genai-ecosystem/model-context-protocol-mcp/  
[^27]: Atlassian Remote MCP Server. https://www.atlassian.com/platform/remote-mcp-server  
[^28]: ClickHouse MCP Server. https://github.com/ClickHouse/mcp-clickhouse  
[^29]: Announcing the MongoDB MCP Server. https://www.mongodb.com/company/blog/announcing-mongodb-mcp-server  
[^30]: Chroma MCP. https://github.com/chroma-core/chroma-mcp  
[^31]: AgentOps MCP. https://github.com/AgentOps-AI/agentops-mcp  
[^32]: Cloudinary MCP Servers. https://github.com/cloudinary/mcp-servers  
[^33]: Cartesia MCP. https://github.com/cartesia-ai/cartesia-mcp  
[^34]: Arize Phoenix MCP. https://github.com/Arize-ai/phoenix/tree/main/js/packages/phoenix-mcp  
[^35]: Axiom MCP Server. https://github.com/axiomhq/mcp-server-axiom  
[^36]: Awesome MCP Servers (otra lista curada). https://github.com/appcypher/awesome-mcp-servers

---

Nota sobre brechas de información: la cobertura y profundidad de listas curadas comunitarias y del repositorio de integraciones varía; faltan métricas de rendimiento comparables y un inventario exhaustivo de observabilidad por servidor. Se recomienda instrumentación local y un registro interno de servidores aprobados para garantizar seguridad y gobernanza consistentes.