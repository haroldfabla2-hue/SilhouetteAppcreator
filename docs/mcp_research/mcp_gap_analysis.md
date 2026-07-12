# Análisis Profundo de Brechas Técnicas en Servidores MCP y Oportunidades con Arquitectura Silhouette

## Resumen ejecutivo

El Model Context Protocol (MCP) se ha consolidado como un estándar abierto para conectar modelos de lenguaje con herramientas y fuentes de datos externas. Su propuesta —una interfaz uniforme para descubrir recursos y ejecutar herramientas— reduce el acoplamiento y habilita casos de uso ricos en escenarios de copilotos y agentes. Sin embargo, al comparar sus capacidades con los requisitos de arquitecturas de agentes a escala empresarial, afloran brechas consistentes en descubrimiento y orquestación, características operativas, rendimiento y seguridad. La evidencia disponible, proveniente de análisis técnicos, incidencias en repositorios, guías de seguridad y evaluaciones comparativas, confirma que MCP, en su estado actual, resuelve el problema de interoperabilidad, pero no garantiza, por sí mismo, operación segura y escalable en producción[^1][^2].

En particular, destacan cuatro brechas sistémicas: (1) la ausencia de descubrimiento de servicios estandarizado, que obliga a configuraciones estáticas, debilita la modularidad e introduce puntos únicos de fallo; (2) la dependencia de sesiones con estado y transportes como HTTP/SSE y stdio, que complican el escalado horizontal y la tolerancia a fallos; (3) carencias en controles de seguridad de nivel empresarial (SSO, autorización granular, auditoría y gobernanza) y un modelo de autorización en evolución con críticas en su alineación con prácticas corporativas; y (4) limitaciones prácticas de rendimiento y fiabilidad bajo patrones de uso con proxies y concurrencia. La evidencia empírica en implementaciones populares muestra que el encadenamiento de “list_tools” por cada invocación de herramienta y la falta de sincronización de inicialización en stdio se traduce en latencias de cientos de milisegundos y tasas de fallo intermitentes en escenarios de paralelismo[^3][^4][^5].

Estas brechas no solo encarecen la operación (más viajes de ida y vuelta, sobrecarga de tokens, sesión afinidad), sino que amplifican riesgos de seguridad (inyección de prompt, “confused deputy”, supply chain), elevando los costes totales de propiedad. Para mitigarlas, se requieren patrones complementarios: un plano de orquestación con registro y descubrimiento, proxies selectivos con cachés de metadatos y políticas de autorización granular, observabilidad nativa y controles de riesgo y costes por herramienta. Sobre esa base, una arquitectura tipo Silhouette —centrada en un orquestador con state management robusto, enforcement de políticas, observabilidad y un plano de control desacoplado— puede superar a las implementaciones MCP actuales al ofrecer: descubrimiento de servicios, routing inteligente, balanceo y tolerancia a fallos; seguridad y gobernanza avanzadas; observabilidad detallada; y optimizaciones de transporte y caching de metadatos que reduzcan drásticamente latencias y volatilidad[^2][^5][^6].

Para ilustrar cómo las brechas impactan en los objetivos clave de una plataforma de agentes, el siguiente mapa sintetiza consecuencias operativas y de seguridad.

Tabla 1. Mapa de brechas MCP vs impacto (seguridad, escalabilidad, rendimiento, operación)

| Brecha MCP | Seguridad | Escalabilidad | Rendimiento | Operación |
|---|---|---|---|---|
| Sin descubrimiento de servicios | Riesgo de configuración errónea y acceso indebido | Dificulta el escalado horizontal y la alta disponibilidad | Rutas subóptimas y reintentos costosos | Cambios manuales, propensos a error |
| Sesiones con estado (afinidad) | Riesgos de “confused deputy” si se fuerza afinidad | Limita balanceo y failover | Latencia por serialización y bloqueos | Complejidad en despliegues y upgrades |
| Transporte HTTP/SSE/stdio | Amplía superficie de ataque y vectores de ejecución | Escalar requiere más conexiones y recursos | Overhead por múltiples list_tools y viajes extra | Hardening diferenciado por transporte |
| Falta de SSO/autorización granular | Exposición de datos y acciones sensibles | No mapea roles corporativos | N/A | Auditoría y cumplimiento deficientes |
| Observabilidad limitada | Detección tardía de abuso o fuga | Incapacidad de auto-remediación | Poca visibilidad de cuellos de botella | MTTR elevado |
| Gestión de riesgo/costes por herramienta inexistente | Acciones irreversibles o costosas | N/A | Coste por token/respuesta descontrolado | Sin controles de presupuesto |

Estas brechas no invalidan MCP; sitúan su alcance como protocolo necesario pero insuficiente. La evidencia sugiere que los sistemas basados en MCP requieren un plano de orquestación y control que provea descubrimiento, seguridad, observabilidad y gestión de estado de forma nativa para operar con fiabilidad y coste controlado en entornos corporativos[^1][^2][^7].

## Metodología y corpus de evidencia

Este análisis se basa en tres pilares: (1) documentación oficial de MCP y su SDK en Python, para fijar arquitectura, transports y modelo de interacción; (2) artículos técnicos y blogs con análisis crítico y recomendaciones; y (3) incidencias en repositorios de implementaciones populares (FastMCP), con métricas reproducibles y discusiones técnicas. En seguridad, se priorizaron guías de mejores prácticas y análisis de riesgos corporativos, así como reportes de vulnerabilidades y supply chain. En observabilidad, se consideraron recomendaciones de cloud-native monitoring y correlación con métricas SRE[^8][^9][^10][^11][^12].

Los criterios de evaluación aplicados incluyen: funcionalidad (descubrimiento, orquestación, seguridad), rendimiento (latencia, throughput, estabilidad), escalabilidad (sesiones con estado, transporte, partición), y seguridad/observabilidad (autenticación, autorización, auditoría y trazabilidad). Se identifican sesgos potenciales por madurez temprana del estándar y de la oferta de servidores, con variabilidad entre implementaciones y transportes. Las principales limitaciones de datos —inevitables en un ecosistema en evolución— son: ausencia de benchmarks oficiales y comparables entre transportes; métricas de producción replicables bajo carga y mixes realistas de herramientas; y detalle completo y estable de la especificación de autorización y su adopción.

Tabla 2. Inventario de fuentes por categoría y su rol en el análisis

| Categoría | Fuente | Rol en el análisis |
|---|---|---|
| Oficial (arquitectura) | MCP Architecture Overview | Definir componentes, transportes y flujos de interacción[^8] |
| SDK/Implementación | Python SDK (GitHub) | Comportamiento del cliente/servidor, detalles prácticos[^9] |
| Crítica/Análisis | Thoughtworks; Flybridge; Dev.to | Enmarcar brechas funcionales, de seguridad y operación[^1][^2][^7] |
| Incidencias/Empiria | FastMCP issues (#1583, #1625) | Evidencia de latencias y fallos bajo proxy y concurrencia[^4][^5] |
| Seguridad | Red Hat; Descope; Datadog; Christian Posta; eSentire; Invariant Labs; Adversa; NCC Group | Riesgos, controles y madurez del modelo de autorización[^3][^12][^13][^14][^15][^16][^17][^18] |
| Benchmarks | LiveMCPBench; Tau-Bench | Metodología y retos de evaluación de herramientas[^6][^19] |
| Orquestación | Azure Architecture Center | Patrones aplicables de orquestación multiagente[^20] |

## Panorama actual de MCP y sus modelos de implementación

MCP articula una interacción cliente-servidor en la que un cliente coordina la conversación con el LLM y la ejecución de herramientas en servidores externos. El cliente expone al modelo las herramientas disponibles, captura su elección y parámetros, invoca el servidor MCP correspondiente y retorna los resultados al modelo para la respuesta final. Este diseño separa el “pensamiento” del LLM de la ejecución de herramientas, con el cliente como orquestador de mensajes y estado[^8].

En cuanto a transportes, conviven tres opciones: HTTP con Server-Sent Events (SSE) para streaming unidireccional, stdio para procesos locales y transports “streamable HTTP” que buscan simplificar flujos de datos y compatibilidad con SDKs. Cada transporte conlleva compromisos prácticos: HTTP/SSE facilita remote hosting pero añade viajes de ida y vuelta; stdio habilita integración local rápida pero introduce condiciones de carrera en concurrencia y acoplamiento al ciclo de vida del proceso; los nuevos transports streamable buscan reducir esta fricción pero su adopción y estandarización aún son incipientes[^8][^9].

El ecosistema de servidores crece con implementaciones de referencia y proyectos comunitarios. La diversidad va desde servidores de propósito general a wrappers de APIs tradicionales. Este diversidad es un strength en términos de cobertura, pero agrava las brechas que estamos analizando: sin un registro/discovery estandarizado, cada cliente debe conocer endpoints y credenciales; sin autorización granular y auditoría, cada servidor puede convertirse en un punto de control heterogéneo; y sin observabilidad y caching de metadatos, el rendimiento se degrada a medida que crece el número de herramientas y servidores[^10][^2].

Para contextualizar los compromisos de cada transporte en entornos de producción, la siguiente tabla resume riesgos y efectos.

Tabla 3. Comparativa de transportes MCP (HTTP/SSE, stdio, streamable)

| Transporte | Latencia esperada | Overhead | Escalabilidad | Observabilidad | Riesgos operativos |
|---|---|---|---|---|---|
| HTTP/SSE | Media (red, múltiples list_tools) | Alto (JSON, múltiples viajes) | Alta con infraestructura | Estándar (proxies, logs) | Gestión de tokens, 405/errores de transporte[^4] |
| stdio | Baja en local | Bajo (IPC) | Limitada (afinidad de proceso) | Local (proceso) | Condiciones de carrera en inicialización[^5] |
| Streamable HTTP | Media-baja ( menos hops) | Medio (streaming) | Potencialmente alta | En evolución | Madurez del SDK y adopción[^9] |

Estas diferencias no son meramente técnicas; inciden directamente en cómo estructuramos seguridad, costes y fiabilidad. En despliegues reales, el patrón de proxyización y el cacheo de “list_tools” adquiere un protagonismo que la especificación no resuelve por sí misma.

## Brechas de características en implementaciones actuales

La primera brecha, y quizás la más determinante para escalar, es la ausencia de un mecanismo de descubrimiento de servicios estandarizado en MCP. Sin él, los clientes deben configurar manualmente endpoints y credenciales, impidiendo el auto-registro, el escalado horizontal y el balanceo entre instancias. En la práctica, esto empuja a dos extremos: servidores monolíticos con demasiadas herramientas o clientes con configuración frágil y acoplada al ciclo de vida de cada servidor. Ninguno de los dos escala con gracia en entornos dinámicos[^21].

La segunda brecha es la falta de patrones de orquestación explícitos. Si bien MCP define cómo invocar herramientas, no prescribe cómo elegir entre múltiples servidores, cómo particionar herramientas por dominio o criticidad, ni cómo implementar rutas condicionales con políticas de acceso. Esta carencia traslada la complejidad al cliente, que debe resolver selección de herramienta, control de concurrencia y políticas de seguridad de manera ad hoc[^2].

La tercera brecha funcional es la integración con APIs REST y sistemas sin estado. El paradigma “por intenciones” de las herramientas MCP colisiona con endpoints deterministas; los wrappers que traducen entre ambos estilos suelen devolver errores ambiguos y datos complejos que confunden a los LLM, mientras el protocolo no aporta un mapeo canónico de intenciones, descripciones legibles para modelos, ni ejemplos parametrizados que reduzcan la alucinación de argumentos[^2].

La cuarta brecha se refiere a la gestión de riesgo y coste a nivel de herramienta. MCP no define metadatos estandarizados para clasificar el riesgo (inofensiva, costosa, irreversible) ni topes de coste o truncamiento de resultados. Esta ausencia, combinada con la dependencia de tokens y respuestas extensas, puede disparar costes y exponencia el riesgo operativo sin que el usuario sea consciente[^22].

Finalmente, persisten carencias de DX/SDK avanzadas: frameworks de prueba, fixtures de evaluación del uso correcto de herramientas y mecanismos de validación de esquemas que eviten errores repetitivos en producción. Aunque el SDK oficial ha avanzado, la madurez para pruebas y verificación sigue por detrás de lo que necesitan los equipos de plataforma[^2][^9].

Tabla 4. Matriz de funcionalidades faltantes vs impacto

| Funcionalidad faltante | Impacto en escalabilidad | Impacto en seguridad | Impacto en coste | Impacto en DX |
|---|---|---|---|---|
| Descubrimiento de servicios | Alto | Medio | Medio | Medio |
| Orquestación/routing | Alto | Alto | Alto | Alto |
| Integración por intenciones | Medio | Medio | Alto | Alto |
| Riesgo/costes por herramienta | N/A | Alto | Alto | Medio |
| Pruebas/validación | N/A | Medio | Medio | Alto |

### Descubrimiento y registro de servidores

El impacto de carecer de discovery es sistémico. Las direcciones estáticas traen acoplamiento, baja tolerancia a fallos y actualizaciones painful; a medida que crecen herramientas e instancias, la gestión se vuelve manual y frágil. La comparación con ecosistemas maduros como Kubernetes —donde servicios y endpoints se registran y resuelven dinámicamente— subraya la oportunidad para MCP: un registro escalable y políticas de resolución que permitan balanceo y failover sin reescribir clientes[^21][^23].

Tabla 5. Patrones de descubrimiento: estático vs dinámico (impacto)

| Enfoque | Pros | Contras | Riesgo operativo |
|---|---|---|---|
| Estático | Simplicidad inicial | Propenso a errores, sin HA | Alto (puntos únicos de fallo) |
| Dinámico | Alta disponibilidad, autoescalado | Mayor complejidad inicial | Bajo (tolerancia a fallos) |

### Integración con APIs y diferencias de paradigma

El error más común es creer que envolver endpoints REST en MCP resuelve la integración. En la práctica, el LLM necesita descripciones legibles, ejemplos y parámetros con restricciones claras; las APIs tradicionales rara vez proveen esa semántica. Además, mensajes de error genéricos y respuestas complejas se traducen en llamadas fallidas y tiempos desperdiciados. Las guías de adopción sugieren transformar endpoints en herramientas “por intenciones”, con validaciones y ejemplos, para elevar la tasa de éxito y reducir latencias por reintentos[^2].

## Limitaciones de rendimiento y escalabilidad

MCP ancla sesiones con estado; esto simplifica la interacción, pero tensiona el escalado horizontal. Bajo sesiones, el balanceo entre instancias requiere afinidad; sin un descubrimiento y reequilibrio automático, cualquier fallo o cambio de topología penaliza la disponibilidad. En transportes como stdio, la inicialización concurrente puede corromper el estado de la sesión y disparar condiciones de carrera, tal como documenta la comunidad. En HTTP/SSE y proxies, la repetición de “list_tools” por cada invocación añade latencias y variabilidad, especialmente cuando los resultados no se cachean eficazmente[^5][^4][^7].

La evidencia empírica de FastMCP es contundente: con proxies HTTP remotos, la latencia por llamada a herramienta pasa de milisegundos a cientos de milisegundos; y bajo stdio, múltiples clientes que inician la misma sesión generan fallos intermitentes, resueltos solo con sincronización explícita de inicialización y reutilización de clientes. Estos comportamientos, lejos de ser anomalías, exponen tensiones estructurales del protocolo y de su ecosistema de herramientas que deben abordarse con arquitectura y hardening[^4][^5].

Tabla 6. Benchmarks de latencia (ms) con y sin proxy

| Escenario | Promedio | Mín | Máx |
|---|---|---|---|
| Sin proxy (local) | 1.7 | 1.4 | 2.4 |
| Proxy stdio (local) | 3.0 | 2.6 | 3.9 |
| Proxy HTTP remoto (caso A) | 391.6 | 308.7 | 481.0 |
| Proxy HTTP remoto (caso B) | 325.7 | 169.6 | 507.6 |

Fuente: Incidencia #1583 en FastMCP. Se observa una degradación sustancial al introducir proxies HTTP remotos, acompañada de múltiples llamadas “list_tools” y cache inefectivo[^4].

Tabla 7. Tasas de éxito bajo concurrencia (stdio)

| Caso | Antes | Después |
|---|---|---|
| Transporte stdio directo (paralelismo) | Fallos intermitentes | 100% tras sincronización de inicialización |
| Proxy con múltiples Client.new() | 1–9 de cada 10 fallos | ~50/50 con sincronización de contexto |
| MCPConfig con creación de clientes | ~40% fallos | 100% con reutilización de instancia |

Fuente: Incidencia #1625 en FastMCP. La serialización de inicialización y la reutilización del cliente para stdio corrigen condiciones de carrera en escenarios de concurrencia[^5].

Más allá de los transportes, existe el coste del “ancho de banda de LLM”: respuestas extensas y metadatos de herramientas consumen tokens y se reflejan en la factura. Las estimaciones publicadas sitúan el coste de salida en aproximadamente un dólar por megabyte por solicitud; la ausencia de límites y truncamiento por herramienta agrava este efecto. La recomendación práctica es incorporar límites de tamaño, políticas de coste y mecanismos de truncamiento compatibles con la tarea[^22].

### Sesiones con estado y escalado horizontal

La afinidad de sesión complica el balanceo; sin discovery y health-checking, un failover o reubicación de instancias invalida rutas. El resultado es latencia adicional por reintentos, caída del throughput y mayor MTTR. Estas fricciones son evitables con un plano de orquestación que gestione el registro, la salud y el reenrutado dinámico, manteniendo los clientes agnósticos de la topología[^21].

### Proxies y transporte HTTP/SSE

En la práctica, los proxies añaden viajes de ida y vuelta para cada “list_tools”, y errores como HTTP 405 exacerban la latencia. Los mitigadores pasan por: espejo/importación de herramientas (reduce a milisegundos a costa de perder dinamismo), cachés locales de metadatos con invalidación controlada, y estrategias de prefetch que eviten consultas redundantes por cada invocación. La elección debe equilibrar frescura y rendimiento[^4].

## Deficiencias en seguridad y observabilidad

Las carencias de seguridad en MCP —reportadas por analistas y practitioners— no se deben ignorar. La autorización basada en OAuth está en evolución y ha recibido críticas por su alineación limitada con prácticas empresariales; su especificación ha sido calificada como problemática, y la comunidad trabaja en revisiones. Esto deja un vacío: sin un modelo consistente, cada servidor y cliente deben inventar controles, elevando el riesgo de acceso indebido y “confused deputy”[^3][^13].

En servidores locales, la ejecución vía stdio abre vectores de abuso si no se sandboxea y se valida el input; la inyección de comandos y la ejecución arbitraria son riesgos reales. En la capa de protocolo, la inyección de prompt y tool injection —incluyendo ataques de “rug pull” donde un servidor redefine dinámicamente el nombre y propósito de herramientas— amplía la superficie de ataque y puede derivar en exfiltración de datos y acciones maliciosas. La supply chain es otro flanco: servidores maliciosos o dependencias comprometidas pueden modificar tool definitions o sampler requests para abuso. Se suman riesgos en el uso del sampling del LLM por parte de servidores, que exige límites de tasa, timeouts y visualización al usuario. Todo ello debe abordarse con controles técnicos y de proceso (SAST, SCA, pinning, verificación criptográfica y auditoría)[^3][^14][^15][^16][^17][^18].

La observabilidad también adolece de原生 capacidades: logs y eventos estandarizados, correlación con trazas y métricas de latencia por herramienta, y detección de abuso. Sin ello, la investigación de incidentes se vuelve reactiva y lenta, y la gobernanza de costes y riesgo se diluye. En entornos cloud-native, la integración con sistemas de monitorización y alertas es imprescindible para mantener SLOs y reducir MTTR[^12].

Tabla 8. Riesgos de seguridad y controles

| Riesgo | Control recomendado |
|---|---|
| Inyección de prompt/tool injection | Confirmación de usuario, sanitización, validación de esquemas |
| “Confused deputy” | Políticas de mínimo privilegio, delegación controlada |
| Supply chain (servidores/dependencias) | SAST/SCA, firma de componentes, pinning, verificación |
| Ejecución de comandos local | Sandboxing, listas de permitidos, validación de args |
| Sampling (LLM) por servidores | Límites de tasa, timeouts, visualización y control de modelo |
| Gestión de tokens | Rotación, vault, separación de dominios |
| Logging/auditoría | Logs estandarizados, envío a SIEM, trazas y métricas[^3][^12][^14][^15][^18] |

Tabla 9. Madurez de autorización: estado actual vs requisitos

| Aspecto | Estado MCP | Requisito empresarial |
|---|---|---|
| OAuth en evolución | RFC y críticas | Estabilidad, mapeo de roles y scopes |
| Autorización granular | Inconsistente | Fine-grained (lectura/escritura/admin) |
| SSO | No nativo | Integración corporativa (SAML/OIDC) |
| Auditoría centralizada | Limitada | Trazabilidad completa, evidencias |

Estas brechas no son triviales; definen si MCP puede operar en industrias reguladas. Las recomendaciones publicadas insisten en combinar hardening de servidores, procesos de vulnerabilidad y controles de usuario para reducir el riesgo sistémico[^3][^12][^14].

### Autorización y autenticación

MCP requiere OAuth estable y alineado con SSO empresarial, scopes consistentes y autorización granular por herramienta/acción. La experiencia muestra que usar tokens de administrador sin segmentación aumenta la exposición y el riesgo de “confused deputy”. Un modelo robusto debe permitir delegación controlada, mapeo de roles y una auditoría exhaustiva[^3][^13].

### Inyección de prompt y tool injection

Los LLM confían en descripciones y metadatos de herramientas; si un servidor malicioso los manipula, puede redirigir acciones o exfiltrar datos. Las mitigaciones incluyen validaciones de esquema, confirmaciones de usuario para acciones sensibles y límites de exposición por contexto. La capacitación del usuario y políticas claras son tan importantes como la tecnología[^15].

### Observabilidad y auditoría

La adopción sin logs estandarizados y correlación con trazas y métricas deja a los equipos ciegos ante abusos y degradaciones. Integraciones con soluciones de monitorización y un modelo de eventos consistente permiten detectar patrones anómalos y reaccionar con rapidez[^12].

## Routing y orquestación: oportunidades de mejora

La ausencia de orquestación explícita en MCP es una oportunidad para introducir un plano de control que ofrezca registro y descubrimiento, balanceo y failover por health-checking, enrutado condicional y políticas de acceso. Patrones como “control plane as a tool” abstraen el routing detrás de una herramienta única, encapsulando lógica modular y escalable. Este enfoque, complementado con cachés de metadatos, prefetch de list_tools y backoff exponencial, reduce latencias y variabilidad sin sacrificar seguridad[^20][^21].

Tabla 10. Patrones de orquestación aplicables a MCP

| Patrón | Descripción | Beneficio |
|---|---|---|
| Control plane as a tool | Una herramienta encapsula routing y políticas | Simplicidad de cliente, modularidad[^20] |
| Discovery + health | Registro dinámico y health checks | HA y escalado horizontal |
| Routing condicional | Reglas por dominio, riesgo y coste | Seguridad y eficiencia |
| Caching de metadatos | list_tools cacheado e invalidación | Latencia reducida |
| Bulkhead/circuit breaker | Aislamiento y protección | Resiliencia operativa |

La combinación de estos patrones, aplicada a despliegues MCP, permite pasar de configuraciones estáticas a topologías dinámicas, con menor acoplamiento y mejor rendimiento.

## Dónde supera la arquitectura Silhouette a las implementaciones MCP actuales

La tesis central es que una arquitectura tipo Silhouette —con un orquestador y un plano de control desacoplado— puede cerrar las brechas de MCP. Sus ventajas competitivas se agrupan en cinco áreas: (1) descubrimiento de servicios con registro dinámico, health-checking y balanceo; (2) seguridad y gobernanza avanzadas (SSO, autorización granular, auditoría centralizada, política de riesgos y costes por herramienta); (3) observabilidad nativa (trazas, métricas, logs estructurados, correlación con SIEM); (4) orquestación inteligente (routing condicional, bulkheads, circuit breakers y políticas de rate limiting); y (5) optimización de transporte y caching de metadatos que reduzca latencias y elimine viajes redundantes[^2][^5][^3].

Estas capacidades no son “adornos”; abordan directamente los cuellos de botella y riesgos observados: condicionantes de carrera en stdio, degradación bajo proxies HTTP, fallos de autorización y falta de trazabilidad. Al mover la complejidad al plano de control, se reduce la carga en el cliente, se mejora la compatibilidad con transportes y se estabiliza el rendimiento[^21][^4][^5].

Tabla 11. Mapa comparativo: Silhouette vs MCP

| Dimensión | MCP actual | Silhouette (propuesta) |
|---|---|---|
| Descubrimiento | Estático/manual | Registro dinámico, health, balanceo |
| Seguridad | OAuth en evolución | SSO, scopes, granularidad y auditoría |
| Observabilidad | Ad hoc | Métricas, trazas, logs, SIEM |
| Orquestación | Cliente dependent | Control plane, políticas, circuit breakers |
| Transporte | HTTP/SSE/stdio | Optimización, caching de metadatos |

### Seguridad y gobernanza

Con SSO y autorización fine-grained, mapeando scopes por acción, y auditoría centralizada, Silhouette puede eliminar riesgos sistémicos como el “confused deputy” y la falta de trazabilidad. La política de riesgo/costes por herramienta introduce límites y confirmaciones que controlan exposición y gasto[^3].

### Observabilidad nativa

Instrumentación con métricas por herramienta, trazas de extremo a extremo y correlación con eventos de seguridad permite detectar abuso y degradación a tiempo. Sin esta base, la operación se vuelve reactiva y los costes impredecibles[^12].

## Recomendaciones técnicas y plan de mitigación

Primero, introducir discovery y orquestación: implementar un registro con health-checking, rutas condicionales y políticas de acceso. Segundo, hardening de seguridad: validar entradas, sandboxear servidores locales, integrar SAST/SCA, pinneado de versiones y verificación criptográfica de componentes. Tercero, optimizar rendimiento: consolidar transporte, cachear metadatos, reducir list_tools redundantes y evitar reintentos innecesarios. Cuarto, institucionalizar observabilidad: logs y métricas estandarizados, trazas y alertas con SLOs. Quinto, gestión de costes: límites por herramienta y truncamiento de respuestas. Estas recomendaciones sintetizan prácticas probadas y se alinean con guías de seguridad y orquestación[^3][^4][^5][^20].

Tabla 12. Matriz de mitigación: brecha → control → métrica de éxito

| Brecha | Control | Métrica de éxito |
|---|---|---|
| Sin discovery | Registro + health + balanceo | HA>99.9%, failover<1s |
| Afinidad sesión | Enrutado por políticas | Throughput +30% |
| list_tools redundante | Cache + prefetch | Latencia p50<10ms (local) |
| stdio race conditions | Sincronización + reutilización | Éxito paralelismo 100% |
| Riesgo/costes | Políticas + truncamiento | Coste/solicitud dentro de SLO |
| Observabilidad | Logs/trazas/métricas | MTTR<15min, detección<5min |

## Plan de evaluación y benchmarks

Definir un benchmark riguroso es crítico para evitar conclusiones anecdóticas. Debe cubrir latencia por herramienta, tasa de éxito bajo concurrencia, consumo de tokens y impacto en coste, y estabilidad en despliegue con proxies y diversidad de transportes. Las métricas p50/p95/p99 y el throughput deben observarse tanto en escenarios sin proxy como con proxy HTTP remoto y stdio, reflejando la variabilidad documentada. En evaluación de agentes y herramientas, referencias como LiveMCPBench y Tau-Bench ayudan a estructurar casos y medir fiabilidad del uso de herramientas en flujos complejos[^6][^19][^4][^5].

Tabla 13. Plan de benchmarks

| Métrica | Escenario | Objetivo |
|---|---|---|
| Latencia p50/p95/p99 | Sin proxy, proxy HTTP, stdio | p50<10ms local; p95 estable |
| Éxito paralelismo | stdio con múltiples clientes | 100% tras sincronización |
| Coste por solicitud | Respuestas con límites | Dentro de presupuesto |
| Throughput | Mix de herramientas | +30% con orquestación |
| Abuso/seguridad | Eventos y alertas | Detección<5min |

## Riesgos y trade-offs de adoptar una arquitectura tipo Silhouette

Introducir un plano de control añade complejidad: gestión de estado distribuido, consistencia y coordinación. El riesgo operativo reside en la sobrecarga de orquestación si se instrumentan demasiadas políticas sin métricas; se debe empezar con un subconjunto, medir y evolucionar. El vendor lock-in es un trade-off real; para mitigarlo, pueden adoptarse interfaces estándar y conectores que preserven interoperabilidad. La curva de adopción requiere inversión en seguridad y observabilidad; si se subestima, el sistema hereda las mismas brechas que decía resolver. Los patrones de orquestación ayudan a reducir esta complejidad con modularidad y control explícito[^20].

## Conclusión y próximos pasos

MCP cumple un rol clave en la integración de agentes con herramientas y datos. Sin embargo, para operar a escala y con seguridad, necesita un complemento arquitectónico: un orquestador y plano de control que provea descubrimiento, políticas de acceso, observabilidad y optimización de transporte. La arquitectura Silhouette —según las brechas identificadas y la evidencia disponible— está bien posicionada para cubrir estos huecos con mejoras sustanciales en rendimiento, escalabilidad, seguridad y gobernanza.

Los próximos pasos sugeridos son: (1) ejecutar un piloto de discovery y orquestación con cachés de metadatos y rutas condicionales; (2) instrumentar observabilidad nativa (logs, trazas, métricas) con integración a SIEM; (3) aplicar hardening de seguridad (SSO, autorización granular, SAST/SCA, pinning y auditoría); y (4) evaluar costes con límites por herramienta y truncamiento de respuestas. Para acelerar la entrega, se recomienda priorizar una fase de implementación del plano de control y sus conectores, con hitos de performance y seguridad medibles.

Finalmente, es esencial reconocer las lagunas de información existentes —como la falta de benchmarks oficiales comparables entre transportes y detalles públicos específicos sobre Silhouette— y abordarlas mediante campañas de pruebas y documentación técnica exhaustiva. Con una arquitectura y un plan de mitigación bien diseñado, MCP puede convertirse en la pieza de interoperabilidad de un sistema de agentes robusto, seguro y escalable.

---

## Referencias

[^1]: The Model Context Protocol: Getting beneath the hype — Thoughtworks. https://www.thoughtworks.com/en-us/insights/blog/generative-ai/model-context-protocol-beneath-hype  
[^2]: The 4 Big Myths Holding Back MCP Adoption (and How to Fix Them) — Flybridge. https://www.flybridge.com/ideas/the-bow/the-4-big-myths-holding-back-mcp-adoption-and-how-to-fix-them  
[^3]: Model Context Protocol (MCP): Understanding Security Risks and Controls — Red Hat. https://www.redhat.com/en/blog/model-context-protocol-mcp-understanding-security-risks-and-controls  
[^4]: as_proxy substantially slower — FastMCP Issue #1583. https://github.com/jlowin/fastmcp/issues/1583  
[^5]: Parallel calls to connected stdio server intermittently fail — FastMCP Issue #1625. https://github.com/jlowin/fastmcp/issues/1625  
[^6]: LiveMCPBench: Can Agents Navigate an Ocean of MCP Tools? — arXiv (2025). https://arxiv.org/html/2508.01780v1  
[^7]: Beyond the hype: Understanding the limitations of Anthropic's MCP — Dev.to. https://dev.to/ramkey982/beyond-the-hype-understanding-the-limitations-of-anthropics-model-context-protocol-for-tool-48kk  
[^8]: Architecture overview — Model Context Protocol. https://modelcontextprotocol.io/docs/learn/architecture  
[^9]: Official Python SDK for MCP servers and clients — GitHub. https://github.com/modelcontextprotocol/python-sdk  
[^10]: Model Context Protocol servers — GitHub. https://github.com/modelcontextprotocol/servers  
[^11]: What Is the Model Context Protocol (MCP) and How It Works — Descope. https://www.descope.com/learn/post/mcp  
[^12]: Understanding MCP security: Common risks to watch for — Datadog. https://www.datadoghq.com/blog/monitor-mcp-servers/  
[^13]: The MCP Authorization Spec Is a Mess for Enterprise — Christian Posta. https://blog.christianposta.com/the-updated-mcp-oauth-spec-is-a-mess/  
[^14]: Model Context Protocol Security: Critical Vulnerabilities Every CISO Should Address in 2025 — eSentire. https://www.esentire.com/blog/model-context-protocol-security-critical-vulnerabilities-every-ciso-should-address-in-2025  
[^15]: MCP Server: New Security Nightmare — Equixly. https://equixly.com/blog/2025/03/29/mcp-server-new-security-nightmare/  
[^16]: WhatsApp MCP Exploited: Exfiltrating your message history via MCP — Invariant Labs. https://invariantlabs.ai/blog/whatsapp-mcp-exploited  
[^17]: MCP Security: Top Vulnerabilities — Composio. https://composio.dev/blog/mcp-vulnerabilities-every-developer-should-know  
[^18]: 5 MCP Security Tips — NCC Group. https://www.nccgroup.com/us/research-blog/5-mcp-security-tips/  
[^19]: Tau-Bench: LLM Tool-Use Evaluation — GitHub. https://github.com/sierra-research/tau-bench  
[^20]: AI Agent Orchestration Patterns — Azure Architecture Center. https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns  
[^21]: Model Context Protocol (MCP) – Hype vs. Scalability without Service Discovery — LinkedIn. https://www.linkedin.com/pulse/model-context-protocol-mcp-hype-vs-scalability-srinivasanarasimhan-p1npc  
[^22]: Everything Wrong with MCP — Shrivu Shankar. https://blog.sshh.io/p/everything-wrong-with-mcp  
[^23]: Kubernetes DNS for Services and Pods. https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/