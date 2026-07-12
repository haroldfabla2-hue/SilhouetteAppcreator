# Stack tecnológico 100% gratuito para replicar y superar MiniMax Agent

## Resumen ejecutivo

Este informe diseña y evalúa un stack 100% gratuito y open source capaz de replicar y, en轴轴轴轴轴轴轴轴 轴轴轴轴轴轴轴轴轴轴 axis, superar las capacidades clave de MiniMax Agent en cinco dimensiones: desarrollo full‑stack con pruebas end‑to‑end (E2E), presentaciones (PPT), investigación profunda (deep research), multimodalidad y orquestación multiagente. La tesis central es que, con una selección cuidadosa de modelos de lenguaje de acceso gratuito, una base vectorial viable para recuperación aumentado por generación (RAG), colas/eventos resilientes, un runtime de agentes con persistencia y controles de calidad, más observabilidad y almacenamiento de objetos, se puede igualar la experiencia de MiniMax Agent a un coste marginal cero (solo infraestructura propia).

El stack recomendado se organiza en ocho capas y combina tecnologías maduras y gratuitas:

- Modelos de lenguaje (LLM): OpenRouter (acceso gratuito a Llama 3.3 70B Instruct, DeepSeek R1 Distill Llama 70B, Shisa V2 Llama 3.3 70B), Gemini 2.5 Flash (nivel gratuito con límites RPM/TPM/RPD), y despliegue autoalojado de Llama 3.1/3.3 70B bajo infraestructura propia.
- Bases vectoriales: Qdrant (cluster gratuito de 1 GB), Chroma (desarrollo local; cloud serverless con créditos), Pinecone Starter (2 GB) y Weaviate (prueba de 14 días; luego Flex).
- Colas y streaming: Redis (Streams, Pub/Sub, Lists, Sorted Sets), RabbitMQ, Kafka, NATS y NSQ, con una guía de selección por garantías de entrega, orden y rendimiento.
- Agentes y orquestación: LangGraph 1.0 (estado duradero, persistencia, human‑in‑the‑loop) y el emergente Microsoft Agent Framework (MAF) como runtime interoperable vía protocolos Agent‑to‑Agent (A2A) y Model Context Protocol (MCP).
- Contenedores y orquestación: Podman (sin daemon), Docker Desktop/Hub con límites de plan, Kubernetes (opciones gratuitas), Docker Swarm y Nomad.
- Frontend: React/Vue/Svelte con librerías UI gratuitas (MUI, Chakra UI, Ant Design, Radix/shadcn).
- Observabilidad: Prometheus (métricas), Grafana (visualización), ELK/OpenSearch (logs).
- Almacenamiento de objetos: MinIO (S3 compatible), LocalStack para desarrollo local.

MiniMax Agent representa hoy el estado del producto en agentes: planificación multi‑paso, despliegue de aplicaciones full‑stack con pruebas E2E, diseño de presentaciones, investigación profunda con herramientas (búsqueda, navegador, MCPs), multimodalidad de entrada y salida, e integración con un ecosistema de MCP preconstruidos y personalizados. Su pricing por tokens y créditos de APIs provee un marco de costes y límites de uso, pero con restricciones relevantes (p. ej., control limitado del gasto en créditos, no soporte de fine‑tuning de modelos open source) que un stack open source puede sortear con control total del entorno y estado durable del workflow[^1][^2][^3].

La combinación propuesta supera limitaciones de costo y vendor lock‑in, habilita portabilidad entre nubes/on‑prem y crea una base de extensibilidad vía MCP y A2A. Los riesgos principales se concentran en: gestión de colas/eventos, capacidad de vector DB gratuita, cuotas de LLMs gratuitos, y el esfuerzo operativo de observabilidad y seguridad. Se mitigan con diseño modular, fallback entre proveedores de modelos, persistencia y checkpoints, y un plan de despliegue iterativo que prioriza valor y aprendizaje continuo.

## Metodología y criterios de evaluación

Se ha seguido un proceso de evaluación pragmático y orientado a decisiones, con tres principios: replicar capacidades funcionales (qué), demostrar viabilidad operativa (cómo), y maximizar ventaja estratégica (so what). En cada categoría tecnológica se han ponderado criterios homogéneos: capacidades clave, limitaciones en niveles gratuitos, madurez y documentación, casos de uso típicos, compatibilidad con el ecosistema, y portabilidad (self‑hosted vs cloud gratuito).

Para la selección de componentes se priorizó: 1) libertad de uso y licencias permisivas; 2) evidencia pública de límites y precios (cuando apliquen); 3) viabilidad de despliegue local sin costes de software; 4) integración con protocolos MCP/A2A y frameworks de agentes; 5) una ruta clara de escalabilidad hacia producción.

Para orientar la lectura, la Tabla 1 muestra una matriz de criterios aplicados por categoría, con niveles de evaluación cualitativos (Alto/Medio/Bajo) según documentación oficial y madurez observada.

Para ilustrar el enfoque comparativo, la siguiente tabla resume los criterios clave por categoría.

Tabla 1. Matriz de criterios por categoría tecnológica

| Categoría | Capacidades clave | Limitaciones nivel gratuito | Madurez/Docs | Casos de uso | Compatibilidad | Portabilidad |
|---|---|---|---|---|---|---|
| LLM | Razonamiento, tool‑calling, multimodal | Cuotas RPM/TPM/RPD; variabilidad por proveedor | Alta en Llama/Gemini; media en variantes distill | Chat, RAG, coding, multimodal | OpenRouter, LangGraph, MCP | Auto‑host (GPU), cloud free |
| Vector DB | RAG, filtros, escalabilidad | Qdrant 1 GB; Pinecone 2 GB; Weaviate trial | Alta en todas; Chroma simple | Memoria semántica, búsqueda | LangChain/LangGraph, MCP | Local, cloud serverless |
| Colas | Throughput, garantías, orden | Recurso compartido local; tuning requerido | Alta en RabbitMQ/Kafka; media en NATS/NSQ | Workflows, eventos | LangGraph checkpoint, SK | Self‑host, managed |
| Agentes | Estado, persistencia, HITL | Herramientas enterprise pueden ser de pago | LangGraph 1.0; MAF emergente | Multiagente, gobierno | MCP/A2A, SK, AutoGen | SDK multiplataforma |
| Orquestación | Aislamiento, HA, escalado | Coste infra; complejidad | Alta en K8s; media en Swarm/Nomad | Microservicios, agentes | Docker/Podman | Local, on‑prem, cloud |
| Frontend | UX, E2E testing, i18n | N/A | Alta en React/Vue/Svelte | Apps agent, dashboards | Any UI library | Static hosting free |
| Observabilidad | Métricas/logs/alertas | Almacenamiento/retention | Alta en Prometheus/Grafana/ELK | Operación 24/7 | Exporters, Loki/ELK | Local, cloud |
| Almacenamiento | S3 API, durabilidad | Disco/IOPS local | MinIO alta; LocalStack media | Artefactos, datasets | S3 SDKs, MCP | Local, on‑prem |

Este marco se sustenta en documentación oficial de Mistral (modelos y ecosistema), la introducción y capacidades de Meta Llama 3.1/3.3, y la especificación de límites de tasa de Gemini 2.5 Flash[^6][^26][^4][^10].

## Línea base: qué es MiniMax Agent y cómo se evalúa superarlo

MiniMax Agent es un sistema multiagente de propósito general que formula soluciones de nivel experto mediante planificación multi‑paso, ejecuta subtareas complejas y coordina herramientas para tareas de largo plazo. En desarrollo de software, entrega aplicaciones web full‑stack con autenticación, funciones, base de datos e integración con pagos (ej., Stripe), y asegura estabilidad mediante pruebas E2E que simulan acciones de usuario. En PPT, ofrece diseño flexible y exporta con alta calidad; en deep research, integra búsqueda, APIs, navegador y Model Context Protocol (MCP) para generar informes con gráficos y análisis de código; y en multimodalidad, acepta archivos variados como entrada (PDF, audio, video, ZIP) y genera imágenes, audio y video[^1].

Su pricing y límites, definidos por planes y uso por tokens, incluyen paquetes para video, suscripciones de audio y un esquema por uso para modelos de texto. La documentación menciona ofertas gratuitas para nuevos usuarios y límites de tasa no siempre explícitos, con un modelo de créditos que el agente no puede predecir ni controlar en todos los casos. Además, no soporta el fine‑tuning y despliegue online de modelos open source, sugiriendo usar APIs externas para funciones similares[^3].

Superar esta línea base con un stack gratuito implica: 1) orquestación multiagente con estado duradero y persistencia para workflows largos; 2) tool‑calling y MCP integrados para extender capacidades con herramientas propias; 3) RAG robusto con filtros y memoria semántica; 4) pruebas E2E reproducibles (playwright/Selenium) y artefactos auditables; 5) multimodalidad pragmática (entrada texto/imágenes/audio y generación vía servicios gratuitos o pipelines propias); 6) observabilidad integral para detectar desvíos y garantizar calidad; y 7) portabilidad total, evitando lock‑in, con despliegue on‑prem/cloud.

La Tabla 2 compara capacidades clave de MiniMax Agent frente al stack open source propuesto.

Tabla 2. Capacidades clave de MiniMax Agent vs stack open source propuesto

| Capacidad | MiniMax Agent | Stack OSS propuesto | Enfoque de superació |
|---|---|---|---|
| Planificación multi‑paso | Sí, multiagente | Sí (LangGraph/MAF) | Estado durable, checkpoints, HITL[^1][^18] |
| Full‑stack + E2E | Sí | Sí (React/Vue/Svelte + Playwright) | Plantillas de proyecto y CI de pruebas[^1] |
| PPT | Sí, exportación de alta calidad | Sí (librerías + exportadores) | Plantillas y automatizar conversión |
| Deep research | Sí | Sí (RAG + MCP + navegador) | Orquestación robusta y trazabilidad |
| Multimodal (entrada/salida) | Sí | Parcial (entrada), salida gratuita | Integrar pipelines y APIs gratuitas[^3] |
| MCP y tool‑calling | Sí | Sí (MCP/A2A, LangGraph) | Extensión y interoperabilidad[^1][^18][^19] |
| Control de costes | Limitado por créditos | Total (self‑hosted) | Elección de modelos/lugares de ejecución |
| Fine‑tuning OSS | No | Sí (infra propia) | Entrenar/adaptar modelos locales |

Conclusión: la experiencia de usuario y las capacidades funcionales pueden igualarse; el control del estado y la extensibilidad vía MCP/A2A se convierten en ventajas diferenciales frente a MiniMax Agent, junto al coste marginal cero del software.

## Arquitectura de referencia del stack 100% gratuito

La arquitectura se organiza en ocho capas acopladas débilmente para maximizar flexibilidad, resiliencia y portabilidad:

- Capa de Modelos (LLM): agregadores gratuitos (OpenRouter) y modelos autoalojados (Llama 3.1/3.3 70B) con rutas de fallback.
- Capa de Recuperación (Vector DB): memoria semántica para RAG y filtros expresivos.
- Capa de Orquestación (Colas/Eventos): pipelines confiables, reintentos y rejugabilidad.
- Capa de Agentes (Runtime): grafos de agentes con estado duradero, persistencia, HITL y controles de calidad.
- Capa de Contenedores/Orquestación: aislamiento y despliegue reproducible, con opciones gratuitas.
- Capa de Frontend: interfaces para interacción y E2E testing.
- Capa de Observabilidad: métricas, logs y alertas; trazabilidad end‑to‑end.
- Capa de Almacenamiento: objetos S3 compatibles; datasets, artefactos y backups.

Flujos de extremo a extremo: 1) Una petición llega al frontend y se encola; 2) el agente (LangGraph/MAF) planifica y ejecuta steps, consultando RAG y llamando herramientas vía MCP/A2A; 3) se generan respuestas estructuradas y pruebas E2E; 4) se registran métricas y logs; 5) se almacenan artefactos en MinIO/LocalStack; 6) se presenta salida y se facilita revisión humana.

Patrones de diseño: grafo de agentes con estados persistidos, reintentos idempotentes, checkpoints manuales y automáticos, y moderación/quality gates integrados como middleware de LangGraph (p. ej., PII redaction, summarization, human approval)[^18]. La extensibilidad se logra con servidores MCP para herramientas propias (GitHub/GitLab, mapas, bases de datos) y comunicación A2A entre runtimes[^19].

Tabla 3. Mapa de componentes por capa y alternativas gratuitas

| Capa | Opción principal | Alternativas | Criterios de selección |
|---|---|---|---|
| Modelos | OpenRouter Llama 3.3 70B (free), Gemini 2.5 Flash | Llama 3.1 70B autoalojado; R1 Distill Llama 70B | Cuotas, razonamiento, tool‑calling[^4][^10] |
| Vector DB | Qdrant 1 GB | Chroma (local), Pinecone 2 GB, Weaviate trial | Capacidad, filtros, facilidad[^13][^14][^15][^16][^17] |
| Colas | Redis Streams | RabbitMQ, Kafka, NATS, NSQ | Garantías, orden, throughput[^21][^23] |
| Agentes | LangGraph 1.0 | Microsoft Agent Framework (MAF) | Persistencia, HITL, MCP/A2A[^18][^19] |
| Orquestación | Podman + Kubernetes | Docker Desktop/Hub, Swarm, Nomad | Costes, compatibilidad, HA[^27][^28][^29] |
| Frontend | React | Vue, Svelte | Ecosistema, rendimiento, E2E |
| Observabilidad | Prometheus + Grafana | ELK/OpenSearch | Estándar OSS, integración[^30][^31][^32] |
| Almacenamiento | MinIO | LocalStack | S3 API, on‑prem, durabilidad |

## Evaluación de componentes por categoría

### LLMs gratuitos

El panorama de LLMs con acceso gratuito incluye modelos de razonamiento y diálogo de alta calidad, tanto vía agregadores como autoalojados. OpenRouter ofrece variantes de 70B en modalidad gratuita (Llama 3.3 70B Instruct, R1 Distill Llama 70B, Shisa V2 Llama 3.3 70B), con diferentes especializaciones (bilingüe, razonamiento) y límites implícitos de proveedor. Gemini 2.5 Flash tiene un nivel gratuito con límites explícitos en solicitudes por minuto (RPM), tokens por minuto (TPM) y solicitudes por día (RPD), útil para flujos de baja latencia y escala moderada. Para control total, Llama 3.1/3.3 70B puede desplegarse en infraestructura propia (GPU) o a través de imágenes optimizadas (NIM), sacrificando latencia y conveniencia por soberanía y coste marginal del software[^4][^5][^10][^6][^8][^9][^26].

Casos de uso: chat, razonamiento paso a paso, tool‑calling y pipelines de RAG; algunos modelos incluyen capacidades multimodales o variantes distill orientadas a coding y workflows agentivos. Las limitaciones principales en niveles gratuitos son las cuotas y variabilidad por proveedor, y la necesidad de infraestructura GPU para autoalojado.

Tabla 4. Comparativa de LLMs gratuitos

| Modelo | Proveedor | Contexto | Tool‑calling | Multimodal | Cuotas/límites | Licenciamiento |
|---|---|---|---|---|---|---|
| Llama 3.3 70B Instruct | OpenRouter | Largo (varía) | Sí (framework) | Texto | Free tier (variante) | Open source (Meta)[^4][^26] |
| R1 Distill Llama 70B | OpenRouter | Medio‑largo | Sí | Texto | Free tier (variante) | Distill open source[^5] |
| Shisa V2 Llama 3.3 70B | OpenRouter | Medio‑largo | Sí | Texto (bilingüe) | Free tier (variante) | Open source[^9] |
| Gemini 2.5 Flash | Google | Extenso (incluye modos) | Sí | Imagen/audio (varía) | RPM/TPM/RPD (free) | API de Google[^10][^11] |
| Llama 3.1 70B (auto) | NGC/Together | Extenso | Sí | Texto | Sin cuotas (infra propia) | Open source[^8][^26] |

Nota: La disponibilidad y límites exactos de variantes gratuitas en OpenRouter varían por proveedor; se recomienda validar en cada tarjeta de modelo[^4][^5][^9].

### Bases vectoriales

Las bases vectoriales sostienen la memoria semántica y el RAG. Qdrant ofrece un clúster gratuito de 1 GB, con despliegue gestionado y alta disponibilidad, adecuado para prototipos y cargas pequeñas; su arquitectura soporta filtros avanzados y escalado horizontal. Chroma habilita desarrollo local sin fricciones y un cloud serverless respaldado por almacenamiento de objetos con créditos iniciales gratuitos. Pinecone Starter incluye hasta 2 GB y funcionalidades de base (sin backups por defecto) útiles para pequeñas apps; y Weaviate proporciona una prueba gratuita de 14 días y planes Flex/Plus para producción, con precios basados en dimensiones de vectores y almacenamiento[^13][^14][^15][^16][^17].

Tabla 5. Comparativa de bases vectoriales gratuitas

| Producto | Plan gratuito | Límite almacenamiento | Replicación/HA | Filtros/híbrida | Hosting |
|---|---|---|---|---|---|
| Qdrant | 1 GB forever | 1 GB | HA gestionada | Filtros avanzados, híbrida | Cloud gratuito + self‑host[^13] |
| Chroma | Local + créditos cloud | Ilimitado (local) | N/A local | Vector + texto + regex | Local; serverless cloud[^14][^17] |
| Pinecone | Starter 2 GB | 2 GB | Serverless | Dense/sparse | Cloud (AWS us‑east‑1)[^15][^16] |
| Weaviate | Trial 14 días | Trial | Shared | Híbrida, compresión | Cloud (GCP/AWS/Azure BYOC)[^17] |

### Sistemas de colas y streaming

Las colas y plataformas de streaming determinan la fiabilidad del flujo multiagente. Redis ofrece estructuras de datos versátiles (Streams, Pub/Sub, Lists, Sorted Sets) con alta velocidad y persistencia (AOF/RDB), adecuado para colas de trabajo y streaming de eventos con reintentos. RabbitMQ, basado en AMQP, garantiza entrega y orden en colas con patrones de enrutamiento flexibles y un ecosistema maduro. Apache Kafka entrega alto throughput, orden por partición y rejugabilidad nativa, idóneo para pipelines de eventos y streaming de datos. NATS aporta huella mínima y baja latencia, con JetStream para persistencia; NSQ simplifica el pub‑sub de alto volumen con baja latencia a costa de menos garantías y persistencia[^21][^23].

Tabla 6. Comparativa de colas/eventos

| Sistema | Throughput (orientativo) | Garantías de entrega | Orden | Persistencia | Rejugabilidad | Casos de uso |
|---|---|---|---|---|---|---|
| Redis Streams | Alto (memoria+disco) | At‑least‑once | Parcial por stream | AOF/RDB | Limitada | Colas de trabajo, eventos[^21] |
| RabbitMQ | Hasta decenas de miles/s | At‑least‑once | Sí (en cola) | Sí | No nativa | RPC, enrutamiento, workflows[^23] |
| Kafka | Hasta millones/s | At‑least/Exactly‑once | Sí (por partición) | Sí | Sí | Streaming, auditoría, CEP[^22][^23] |
| NATS | Millones/s | At‑most/least (JetStream) | Sí (stream) | Sí (JetStream) | Limitada | Edge, baja latencia[^23] |
| NSQ | Cientos de miles/s | At‑least‑once | No | Limitada | No | Pub‑sub simple, alto volumen[^23] |

### Frameworks de agentes

LangGraph 1.0 ofrece un runtime de agentes con estado duradero y persistencia incorporada, human‑in‑the‑loop, y middleware para moderación y control de calidad, facilitando la transición de prototipo a producción. Microsoft Agent Framework (MAF), aún emergente, se posiciona como motor open source para apps agentivas con énfasis en observabilidad, gobernanza, interoperabilidad vía protocolos A2A y MCP, y workflows como primitivos de primera clase. AutoGen sigue siendo un marco versátil para conversaciones multiagente y descomposición de tareas. CrewAI complementa con un modelo de colaboración y planes comerciales, pero su valor diferencial es la plataforma y servicios; el framework central es open source[^18][^19][^20][^25][^24].

Tabla 7. Comparativa de frameworks de agentes

| Framework | Persistencia | HITL | Observabilidad | MCP/A2A | Estado de producción | Coste |
|---|---|---|---|---|---|---|
| LangGraph 1.0 | Sí (durable state) | Sí | Sí (hooks, trazabilidad) | Integración MCP | Madurez OSS v1.0 | Gratis OSS[^18] |
| MAF | Enfoque enterprise | Sí | Énfasis en gobernanza | A2A + MCP | Emergente (preview) | Gratis OSS[^19][^20] |
| AutoGen | Básica (conversacional) | Integrable | Logging básico | Vía ecosistema | Establecido (OSS) | Gratis OSS[^25] |
| CrewAI | Plataforma + studio | Sí | Observabilidad en nube | Integrable | Comercial | OSS + SaaS[^24] |

### Contenedores y orquestación

Docker proporciona contenedores y un hub con planes y límites actualizados para 2025 (p. ej., restricciones de pulls/almacenamiento según suscripción). Podman opera sin daemon y es compatible con imágenes OCI, útil para entornos donde se prefiere evitar privilegios de daemon; no soporta Docker Swarm, por lo que migrar requiere considerar Kubernetes u otras opciones. Kubernetes es open source y puede desplegarse en modo gratuito en distintas distribuciones o en la nube con tiers sin coste; Docker Swarm y Nomad son alternativas más simples para casos acotados. Portainer simplifica la gestión de contenedores y clústeres con soporte para múltiples motores[^27][^28][^29].

Tabla 8. Comparativa de orquestación

| Opción | Coste | Complejidad | Compatibilidad imágenes | HA/Escalado | Casos de uso |
|---|---|---|---|---|---|
| Podman | Gratis | Media | OCI | Depende de plataforma | Entornos sin daemon[^28] |
| Docker Desktop/Hub | Gratis/Planes | Baja‑media | OCI | Local/cluster | Dev local, CI[^27] |
| Kubernetes | Gratis (software) | Alta | OCI | Nativo | Producción, microservicios[^29] |
| Docker Swarm | Gratis | Baja | OCI | Moderado | Simplicidad, stacks pequeños |
| Nomad | Gratis | Media | OCI | Bueno | Workloads batch/serve |

### Frontend

React, Vue y Svelte son opciones gratuitas con ecosistemas amplios. React destaca por su comunidad y librerías UI (MUI, Chakra UI, Ant Design, Radix/shadcn) y se integra bien con pruebas E2E (Playwright/Selenium). Vue prioriza simplicidad y productividad. Svelte ofrece bundles pequeños y rendimiento runtime elevado. La elección depende del perfil del equipo y requisitos de rendimiento y accesibilidad[^33][^34].

Tabla 9. Comparativa de frameworks frontend

| Framework | Rendimiento | Curva de aprendizaje | Ecosistema UI | Extensibilidad |
|---|---|---|---|---|
| React | Alta | Media | Muy amplio (MUI/Chakra/Ant/Radix) | Alta (SSR/Next, etc.)[^33] |
| Vue | Alta | Baja‑media | Amplio | Alta (ecosistema Vue) |
| Svelte | Muy alta | Media | En crecimiento | Alta (SvelteKit) |

### Monitoreo y observabilidad

Prometheus recolecta métricas y Grafana las visualiza con alertas; ELK/OpenSearch centraliza logs y búsquedas. Combinados, habilitan observabilidad integral para agentes y servicios: latencia por step, tasa de errores por herramienta, uso de tokens, reintentos y colas. Estas piezas son estándar open source, con amplia documentación y plantillas listas para usar[^30][^31][^32].

Tabla 10. Comparativa de observabilidad

| Componente | Tipo | Retención | Alertas | Integraciones | Costes de operación |
|---|---|---|---|---|---|
| Prometheus | Métricas | Configurable | Alertmanager | Exporters, Grafana | Bajo (local) |
| Grafana | Visualización | N/A | Sí (plugins) | Prometheus, ELK | Bajo |
| ELK/OpenSearch | Logs | Configurable | Watcher/Kibana | Beats, Fluentd | Medio‑alto (recursos) |

### Almacenamiento de objetos

MinIO es un almacenamiento de objetos S3 compatible, open source y autoalojado, adecuado para datos, artefactos y backups. LocalStack facilita desarrollo local emulando servicios AWS, con un tier gratuito para pruebas. Ambos soportan pipelines de agentes y RAG con durabilidad y costes predecibles[^35][^36].

Tabla 11. Comparativa de almacenamiento

| Opción | Compatibilidad S3 | Coste | Durabilidad | Casos de uso |
|---|---|---|---|---|
| MinIO | Total | Infra propia | Alta (replicación) | Objetos, datasets, artefactos[^35] |
| LocalStack | Emulación AWS | Gratis/Tiers | N/A (local) | Dev/test, prototipos[^36] |

## Arquitecturas candidatas para superar a MiniMax Agent

Se proponen tres arquitecturas que maximizan valor con coste cero de software:

- Arquitectura A (100% local): Llama 3.1/3.3 70B autoalojado, Qdrant 1 GB, Redis Streams, LangGraph, Podman+Nomad, React, Prometheus+Grafana+ELK, MinIO. Ventajas: soberanía total, coste marginal cero, control del estado y observabilidad; desventaja: operación compleja y límites de capacidad en vector DB.
- Arquitectura B (cloud gratuito híbrido): OpenRouter (Llama 3.3 70B free) + Qdrant 1 GB, RabbitMQ/Kafka gestionado free tier, LangGraph, Kubernetes free, React, observabilidad OSS, MinIO. Ventajas: simplicidad operativa y escalabilidad moderada; desventaja: cuotas de LLM y límites de capacidad.
- Arquitectura C (serverless‑first): Gemini 2.5 Flash free, Chroma Cloud serverless, NATS/JetStream, LangGraph en contenedores, React, observabilidad OSS, LocalStack. Ventajas: latencia baja y elasticidad; desventaja: límites RPM/TPM/RPD y dependencia de servicios cloud.

Tabla 12. Pros/contras por arquitectura

| Arquitectura | Coste software | Latencia | Escalabilidad | Complejidad operativa | Riesgo lock‑in |
|---|---|---|---|---|---|
| A (local) | 0 | Media | Media | Alta | Muy bajo |
| B (híbrida) | 0 | Media‑alta | Media‑alta | Media | Bajo |
| C (serverless) | 0 | Baja | Alta | Baja‑media | Medio‑alto |

Tabla 13. Mapeo de capacidades MiniMax → Componentes OSS

| Capacidad MiniMax | Componente OSS | Punto de control |
|---|---|---|
| Full‑stack + E2E | React + Playwright | Tests reproducibles y reportes[^1] |
| PPT | Librerías + exportadores | Plantillas y conversión automatizada |
| Deep research | Qdrant + MCP + navegador | RAG + tool‑calling + citación[^1] |
| Multimodal | Gemini Flash/entrada | Pipeline multimodal en límites[^3][^10] |
| Estado durable | LangGraph | Checkpoints, persistencia, HITL[^18] |
| Observabilidad | Prometheus/Grafana/ELK | SLIs de latencia/errores[^30] |
| Almacenamiento | MinIO/LocalStack | Artefactos y datasets[^35][^36] |

## Plan de implementación y roadmap

El roadmap se organiza en fases iterativas con objetivos claros y criterios de aceptación centrados en valor y estabilidad. La progresión propone comenzar con un prototipo local, endurecerlo con observabilidad y persistencia, y escalar gradualmente hacia cloud gratuito y resiliencia multiagente.

Tabla 14. Roadmap por fases

| Fase | Tareas | Dependencias | Entregables | Métricas objetivo |
|---|---|---|---|---|
| 1. Prototipo local | LangGraph + Qdrant + Redis Streams + MinIO; app React | SDKs y docs | Demo funcional, RAG básico | Latencia < 2 s/step; error rate < 3%[^18][^13][^21][^35] |
| 2. Endurecimiento | Observabilidad (Prom/Grafana/ELK); E2E; MCP tools | Exporters y runners | Dashboards, tests E2E | Cobertura E2E > 80%; alertas configuradas[^30] |
| 3. Escalado | Kubernetes/Podman; fallback LLM (OpenRouter/Gemini) | Infra y cuotas | Autoescalado y rutas de failover | Disponibilidad > 99%; throughput +50%[^27][^4][^10] |
| 4. Resiliencia multiagente | Checkpoints, HITL; NATS/Kafka | LangGraph/MAF | Orquestación robusta | Reintentos idempotentes; pérdida de mensajes ~0[^18][^23] |
| 5. Optimización | Rendimiento RAG, caching; compresión vectors | Chroma/Qdrant | Costes infra optimizados | Latencia RAG −30%; uso tokens −20%[^14][^13] |

Cada fase añade controles de calidad, trazabilidad y capacidad de recuperación, alineados con las capacidades de LangGraph para agentes en producción[^18].

## Riesgos, mitigaciones y limitaciones

Los riesgos clave se concentran en cuotas de APIs gratuitas, capacidad limitada de tiers gratuitos (vector DB), garantías de entrega en colas y la complejidad operativa del runtime de agentes.

- Cuotas LLM: Gemini 2.5 Flash limita RPM/TPM/RPD; OpenRouter puede variar por proveedor. Mitigación: rutas de fallback entre modelos y proveedores, caching y batch de prompts[^10][^4].
- Vector DB: Qdrant 1 GB y Pinecone 2 GB pueden saturarse. Mitigación: compresión de vectores, filtros agresivos, paginación y summarization en RAG; escalado a planes pagos si fuese imprescindible[^13][^15][^17].
- Colas: Redis Pub/Sub no garantiza rejugabilidad; NATS sin JetStream tiene límites. Mitigación: usar Streams o JetStream, patrones idempotentes, checkpoints[^21][^23].
- Orquestación: Kubernetes implica complejidad; Docker Desktop/Hub aplica límites de plan. Mitigación: usar Podman+Nomad o minikube/k3s para entornos ligeros, y CI/CD con límites claros[^27][^28][^29].
- Runtime agente: riesgos de drift y comportamiento no determinista. Mitigación: moderación, gates, human‑in‑the‑loop y estado durable con persistencia[^18][^19].

Tabla 15. Mapa de riesgos

| Riesgo | Impacto | Probabilidad | Mitigación | Indicadores de alerta |
|---|---|---|---|---|
| Cuotas LLM | Alto | Media | Fallback y caching | Errores 429, latencia variable[^10] |
| Capacidad vector DB | Medio | Alta | Compresión, filtros | QPS bajos, memoria agotada[^13][^15] |
| Pérdida de mensajes | Alto | Media | Streams/JetStream | Lag creciente, reintentos[^21][^23] |
| Complejidad K8s | Medio | Media | Podman/Nomad | Alarms de infraestructura[^29] |
| Drift del agente | Alto | Media | HITL, gates | Divergencia de output[^18] |

## Métricas de éxito y evaluación comparativa con MiniMax Agent

Las métricas deben medir calidad, rendimiento, fiabilidad y coste, y se comparan con la línea base de MiniMax Agent (funcionalidad y límites conocidos). El objetivo no es replicar cifras propietarias sino demostrar paridad en experiencia y mejoras en control y extensibilidad.

- Calidad: precisión en respuestas estructuradas, estabilidad de pruebas E2E, calidad de exportación PPT (verificable).
- Rendimiento: latencia por step, throughput por colas, tiempo de recuperación RAG.
- Fiabilidad: tasa de errores, reintentos, pérdida de mensajes, cumplimiento de SLOs.
- Coste: coste marginal de software (cero), coste operativo de infraestructura (optimizable).

Tabla 16. Cuadro de métricas

| Métrica | Definición | Objetivo | Método de medición | Fuente de datos |
|---|---|---|---|---|
| Latencia por step | Tiempo agente‑herramienta | < 2 s (prototipo) | Traces LangGraph + Prometheus | Métricas + logs[^18][^30] |
| Error rate | % de fallos | < 3% | Alertmanager + Grafana | Métricas/alertas[^31] |
| RAG recovery time | Búsqueda→respuesta | < 500 ms | Benchmarks Qdrant/Chroma | Métricas DB[^13][^14] |
| Throughput colas | Msg/s por pipeline | +50% Fase 3 | Load tests | Métricas Kafka/Redis[^22][^21] |
| E2E stability | % casos que pasan | > 80% | Playwright suite | Reportes CI |
| Coste infra | $/mes | Minimizar | Etiquetas cloud | Facturación |

## Apéndices

Glosario:

- Retrieval‑Augmented Generation (RAG): técnica que combina recuperación de documentos con generación de respuestas.
- Human‑in‑the‑loop (HITL): inclusión de revisión/aprobación humana en el ciclo del agente.
- Model Context Protocol (MCP): protocolo para exponer herramientas y recursos a modelos/agentes.
- Agent‑to‑Agent (A2A): protocolo de comunicación entre agentes.
- Solicitudes por minuto (RPM), tokens por minuto (TPM), solicitudes por día (RPD): medidas de límites de API.

Guías rápidas:

- Qdrant: clúster gratuito de 1 GB, Docker compose y dashboard para gestión; ideal para RAG local[^13].
- Chroma: instalación local con pip y servidor en local; integra con frameworks de agentes y LLMs[^14].
- LangGraph: patrones de persistencia y HITL; middleware para moderación y summarization[^18].

Referencias completas: ver sección “References” al final.

## References

[^1]: MiniMax Agent — User Guide. https://agent.minimax.io/docs/user-guide  
[^2]: MiniMax — Platform Overview. https://www.minimax.io/  
[^3]: MiniMax API — Pricing. https://platform.minimax.io/docs/guides/pricing  
[^4]: OpenRouter — Llama 3.3 70B Instruct (free). https://openrouter.ai/meta-llama/llama-3.3-70b-instruct:free  
[^5]: OpenRouter — DeepSeek R1 Distill Llama 70B (free). https://openrouter.ai/deepseek/deepseek-r1-distill-llama-70b:free  
[^6]: Mistral AI — Pricing. https://mistral.ai/pricing  
[^7]: Mistral AI — Models. https://docs.mistral.ai/getting-started/models  
[^8]: NVIDIA NGC — Llama‑3.1‑70B‑Instruct (NIM container). https://catalog.ngc.nvidia.com/orgs/nim/teams/meta/containers/llama-3.1-70b-instruct-pb25h1  
[^9]: OpenRouter — Shisa V2 Llama 3.3 70B (free). https://openrouter.ai/shisa-ai/shisa-v2-llama3.3-70b:free  
[^10]: Gemini API — Rate limits. https://ai.google.dev/gemini-api/docs/rate-limits  
[^11]: Vertex AI — Gemini 2.5 Flash. https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-5-flash  
[^12]: Llama — Official Site. https://www.llama.com/  
[^13]: Qdrant — Pricing (Cloud y Vector DB). https://qdrant.tech/pricing/  
[^14]: Chroma — Getting Started. https://docs.trychroma.com/getting-started  
[^15]: Pinecone — Pricing. https://www.pinecone.io/pricing/  
[^16]: Pinecone — Database limits. https://docs.pinecone.io/reference/api/database-limits  
[^17]: Weaviate — Pricing. https://weaviate.io/pricing  
[^18]: LangChain — LangChain y LangGraph 1.0. https://blog.langchain.com/langchain-langgraph-1dot0/  
[^19]: Microsoft Agent Framework — Overview. https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview  
[^20]: Microsoft Agent Framework — GitHub. https://github.com/microsoft/agent-framework  
[^21]: Redis — Messaging. https://redis.io/solutions/messaging/  
[^22]: Apache Kafka — Downloads. https://kafka.apache.org/downloads  
[^23]: Gcore — Comparison of NATS, RabbitMQ, NSQ, and Kafka. https://gcore.com/learning/nats-rabbitmq-nsq-kafka-comparison  
[^24]: ZenML — CrewAI Pricing Guide. https://www.zenml.io/blog/crewai-pricing  
[^25]: AutoGen — GitHub. https://github.com/microsoft/autogen  
[^26]: Meta AI — Introducing Llama 3.1. https://ai.meta.com/blog/meta-llama-3-1/  
[^27]: Docker — Pricing. https://www.docker.com/pricing/  
[^28]: SigNoz — Docker Alternatives. https://signoz.io/comparisons/docker-alternatives/  
[^29]: Uptrace — Kubernetes Alternatives. https://uptrace.dev/comparisons/kubernetes-alternatives  
[^30]: Last9 — Comparing ELK, Grafana, and Prometheus. https://last9.io/blog/elk-vs-grafana-vs-prometheus/  
[^31]: Robotalp — Best Free Open Source Monitoring Tools in 2025. https://robotalp.com/blog/best-free-open-source-monitoring-tools-in-2025/  
[^32]: Groundcover — Top Observability Tools. https://www.groundcover.com/blog/observability-tools  
[^33]: Imaginary Cloud — Best Front End Frameworks in 2025. https://www.imaginarycloud.com/blog/best-frontend-frameworks  
[^34]: Plain English — JS Frameworks Performance (2025). https://javascript.plainenglish.io/react-vs-vue-vs-angular-vs-svelte-framework-performance-reality-2025-52f1414cf0b8  
[^35]: DigitalOcean — Amazon S3 Alternatives. https://www.digitalocean.com/resources/articles/amazon-s3-alternatives  
[^36]: LocalStack — Awesome LocalStack (GitHub). https://github.com/localstack/awesome-localstack

---

Información adicional y vacíos reconocidos: algunas ofertas de “free” en LLMs vía agregadores dependen de terceros y pueden variar sin aviso; OpenRouter no expone en su landing una lista consolidada con límites detallados de todas las variantes gratuitas; el rendimiento real de modelos 70B autoalojados depende fuertemente de la infraestructura; los límites de Weaviate y Pinecone en tiers gratuitos están sujetos a cambios de plan; no existen benchmarks estandarizados y neutrales comparando Redis Streams, RabbitMQ y Kafka en escenarios multiagente heterogéneos; el soporte empresarial de algunos frameworks (p. ej., MAF) puede requerir planes comerciales o maduración del proyecto; LocalStack tiene diferencias con AWS real en ciertos servicios; y la latencia transcontinental en despliegues gratuitos puede afectar experiencia de usuario. Estas brechas deben monitorizarse y gestionarse con pruebas continuas, rutas de fallback y observabilidad detallada.