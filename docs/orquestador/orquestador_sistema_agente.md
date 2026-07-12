# Blueprint del Orquestrador Multi‑Agente Superior a MiniMax Agent

## 1. Resumen ejecutivo y objetivos

El objetivo de este documento es definir un sistema orquestador multi‑agente, modular y gobernable, que supere las capacidades del estado del arte representado por MiniMax Agent, con foco explícito en orquestación inteligente, paralelización efectiva, robustez ante fallos y observabilidad de extremo a extremo. El diseño integra modelos de lenguaje y herramientas a través de contratos bien definidos, un bus de eventos y un plan de implementación por fases, orientado a su uso con MiniMax M2 (gratuito hasta el 7 de noviembre) y conmutación posterior a modelos accesibles vía OpenRouter, como Llama 3.3 70B Instruct.

La propuesta se apoya en tres principios rectores:

- Orquestación explícita y medible. El sistema no deja la coordinación al azar del lenguaje; la implementa como lógica determinista con políticas de delegación, presupuestos y seguimiento de trazas unificadas[^1].
- Paralelización de dos niveles. La fase de “amplitud primero” activa múltiples subagentes en paralelo y cada subagente usa múltiples herramientas concurrentemente, reduciendo el tiempo de investigación hasta en un 90% con controles presupuestarios por tarea[^1].
- Observabilidad y recuperación como capacidades de primera clase. Se instrumenta cada llamada LLM y herramienta con OpenTelemetry, se reconstruyen causalidades por span y se aplican estrategias de recuperación adaptativas (reintentos con jitter, disyuntores y rollback por snapshots), respaldadas por evaluaciones automáticas y trazabilidad multiagente[^2][^4].

Resultados esperados frente a MiniMax Agent:

- Paralelismo superior. Orquestación de 3–5 subagentes por tarea y ≥3 herramientas concurrentes por subagente, con backpressure y ventanas dinámicas para evitar sobrecargas[^1].
- Trazabilidad completa. Spans y atributos estandarizados para agentes, herramientas y servidores MCP, con correlación cliente‑servidor bajo el mismo trace_id[^2].
- Recuperación robusta. Aislamiento por clústeres, disyuntores adaptativos, snapshots y control de consistencia causal para reanudar sin perder contexto[^4].
- Evaluación continua. “LLM‑as‑a‑Judge” y “code evaluations” para medir planificación, convergencia y calidad de citas; datos de entrada para bucles de auto‑mejora[^2][^1].

Integraciones clave:

- Modelos: MiniMax M2 (hasta el 7 de noviembre), luego OpenRouter con Llama 3.3 70B Instruct y alternativas gratuitas bajo presupuesto controlado[^6][^7].
- Capa de herramientas: Model Context Protocol (MCP) para conexión segura y bidireccional con datos y servicios, con trazabilidad unificada cliente‑servidor[^3][^2].
- Datos: PostgreSQL + pgvector para memoria semántica de largo plazo, con diseños multi‑tenant y prácticas de indexación/consulta eficientes[^9][^10][^11].
- Tiempo real y colas: Redis como bus de eventos y memoria operativa de sesión, con patrones de throughput y control de estado[^12][^13].

Métricas de éxito (objetivos propuestos; validar con pilotos):

- Reducción del tiempo de ciclo ≥40% vs. baseline monoagente en tareas complejas gracias a paralelización de dos niveles[^1].
- Convergencia en menos pasos (p50/p95), medido con code evaluations y trazas de trayectoria[^2].
- Reducción de costes por tarea mediante ruteo inteligente y presupuestos por tarea (tokens, tiempo, número de herramientas).
- Calidad del output (precisión, citación, completitud) validada por LLM‑as‑a‑Judge y evaluación humana selectiva[^1][^2].

Gaps de información relevantes para la planificación:

- Rate limits y latencias bajo carga del M2 en el período gratuito no están publicados; se mitigarán con ruteo alternativo (OpenRouter) y backpressure.
- La migración post‑7 nov a OpenRouter requiere selección de modelos concretos y presupuestos por caso de uso; se definirá tras pilotos con telemetría.
- Esquemas de datos detallados (tablas y particiones) dependen del dominio y se ajustarán con datos de piloto.

## 2. Estado del arte y posicionamiento competitivo

Los sistemas multi‑agente han demostrado ventajas en tareas de “amplitud primero” y exploración abierta, superando con claridad a enfoques de un solo agente cuando se gobierna explícitamente el paralelismo y el razonamiento intercalado. La experiencia de Anthropic en su sistema de investigación multi‑agente documenta mejoras sustantivas en consultas complejas, a costa de un consumo mayor de tokens que obliga a una disciplina presupuestaria y de selección de tareas de alto valor[^1]. La observabilidad, tal como la describe Arize, se convierte en la piedra angular que permite ver el “panorama interno” del agente: qué herramientas invocó, con qué parámetros, en qué orden y con qué resultados, así como detectar desviaciones en las rutas de razonamiento[^2].

Limitaciones frecuentes en sistemas multi‑agente:

- Explosión combinatorial de dependencias y estados. Cada agente mantiene estado a lo largo de múltiples llamadas; pequeños errores pueden amplificarse si no hay control de causalidad y checkpoints.
- Falta de observabilidad en MCP. Sin instrumentación específica, la comunicación cliente‑servidor MCP es un punto ciego. La instrumentación basada en OpenTelemetry cierra esa brecha, propagando contexto y unificando trazas[^2].
- Cuellos de botella por ejecución síncrona. La coordinación simplificada puede frenar el flujo; la asincronía controlada y el backpressure elevan el throughput, pero requieren gobernanza de colas y políticas de prioridad[^1].

Posicionamiento superior del sistema propuesto:

- Orquestación explícita. El orquestador no delega la coordinación al lenguaje, sino que la implementa con políticas de delegación, límites de tareas, presupuestos de tokens/tiempo y selección dinámica de herramientas, todo gobernado por telemetría y evaluación continua[^1][^2].
- Paralelización de dos niveles. La fase inicial de exploración dispara múltiples subagentes y, por subagente, múltiples herramientas concurrentes, maximizando cobertura y velocidad bajo límites presupuestarios[^1].
- Observabilidad unificada. Trazas por sesión, por tarea y por herramienta; evaluación de trayectorias y flujos de auto‑mejora basados en patrones de fallo observados[^2].

Para ilustrar el gap funcional frente a MiniMax Agent, se presenta la siguiente comparativa (cualitativa, sustentada en principios y prácticas validadas del estado del arte; datos específicos de MiniMax se tratarán como “no documentado” hasta validación propia):

Tabla 1. Comparativa funcional y operacional: MiniMax Agent vs. sistema propuesto

| Capacidad                     | MiniMax Agent (observado/esperado) | Sistema propuesto (diseño) | Fuente principal |
|------------------------------|-------------------------------------|-----------------------------|------------------|
| Orquestación                 | No documentado público exhaustivo   | Orquestador con políticas de delegación, límites y presupuestos; ruteo explícito | [^1][^2] |
| Paralelización               | No documentado                      | 3–5 subagentes por tarea; ≥3 herramientas concurrentes por subagente; backpressure | [^1] |
| Observabilidad               | Parcial/No estandarizada            | OpenTelemetry con spans por agente/herramienta; trazas multiagente y MCP cliente‑servidor | [^2] |
| Recuperación ante fallos     | No documentado                      | Disyuntores adaptativos, aislamiento por clúster, snapshots, relojes vectoriales | [^4] |
| Memoria semántica            | No documentado                      | PostgreSQL + pgvector; diseños multi‑tenant; indexación y consultas eficientes | [^9][^10][^11] |
| Integraciones de herramientas| Función calling; MCP no documentado | MCP para interoperabilidad segura y trazabilidad unificada | [^3][^2] |

El diseño propuesto se diferencia por convertir capacidades deseables en controles y contratos operacionales medibles, y por integrar observabilidad y resiliencia desde el inicio, en lugar de añadirlas a posteriori.

## 3. Arquitectura de alto nivel del orquestrador

La arquitectura adopta un patrón orquestador‑trabajador con bus de eventos, orquestación explícita y memoria compartida:

- Orquestador central. Coordina fases (amplitud, profundización, síntesis), dispara subagentes y evalúa su salida bajo presupuestos y límites. Contiene el plan maestro por tarea y adapta la estrategia según telemetría y evaluación.
- Bus de eventos y colas. Redis canaliza tareas, respuestas y señales de control (prioridades,cancelación). El orquestador emite eventos de “spawn” de subagentes, mientras que los agentes publican resultados y heartbeats.
- Memoria compartida. PostgreSQL + pgvector sirve como memoria semántica de largo plazo; Redis mantiene estado operativo de sesión y caché de corto plazo[^9][^12].
- Capa de herramientas vía MCP. Conecta agentes a herramientas/servidores MCP bajo un contrato estable, con trazabilidad unificada cliente‑servidor y control de contexto[^3][^2].

Gobernanza del estado:

- Checkpoints por fase. El orquestador registra snapshots del estado al cierre de cada etapa (amplitud, profundización, síntesis).
- Consistency marks. Relojes vectoriales/marcas lógicas en mensajes y estados para ordenar eventos sin perder causalidad.
- Versionado de contexto. Cada mensaje referencia el contexto_version para evitar races y facilitar rollback.
- Resiliencia y aislamiento. Agrupamiento de agentes por capacidades; límites de recursos por clúster; disyuntores entre clústeres para evitar fallos en cascada[^4].

Paralelización:

- Nivel 1 (subagentes). El orquestador activa de 3 a 5 subagentes en paralelo en la fase de amplitud.
- Nivel 2 (herramientas). Cada subagente invoca 3 o más herramientas en paralelo (p. ej., búsqueda, navegación, recuperación vectorial), siguiendo un patrón de “pensamiento intercalado” controlado[^1].

Observabilidad:

- Trazas OpenTelemetry. Spans para agentes, herramientas y servidores MCP, con atributos estandarizados (herramienta, modelo, tokens, latencia, resultado).
- Propagación de contexto. trace_id y span_id compartidos en cliente MCP y servidor MCP; trazas unificadas en la plataforma de observabilidad[^2].
- Trazas multiagente. Visualización de delegación, flujos y cuellos de botella; evaluación de trayectoria como métrica de adherencia al “camino dorado”[^2].

### 3.1 Componentes y responsabilidades

- Orquestador. Expone la interfaz de sesión/tarea; conserva el plan maestro, administra presupuestos y activa subagentes; integra evaluación y ruteo.
- Reasoner Agent. Con pensamiento extendido y razonamiento intercalado, propone estrategia y criterios de delegación, apoyado en trazas y memoria[^1].
- Planner Agent. Descompone tareas, define herramientas candidatas y límites de esfuerzo por subtarea; persiste el plan en memoria con referencias ligeras.
- Executor Agents. Ejecutores especializados (código, web, documentos, multimedia) invocan herramientas MCP en paralelo; guardan salidas estructuradas minimizando el “juego de teléfono”[^1].
- Verifier Agent. Ejecuta validaciones automáticas y evaluaciones LLM‑as‑a‑Judge y code evaluations; define criterios de aprobación y detección de desviaciones[^2].
- Memory Manager. Sintetiza y almacena insights en pgvector; consolida snapshots; gestiona versionado de contexto y políticas de retención[^9].
- Capa MCP. Conecta a servidores MCP con seguridad, control de acceso y trazabilidad unificada[^3][^2].

Interfaces clave: contrato de sesión (SessionCreate, SessionAppend), contrato de plan (PlanCreate, PlanUpdate, TaskSpawn, TaskDone), contrato de evaluación (EvaluateRun, EvaluateResult), contrato de memoria (PutMemories, QueryMemories). Versionado de APIs con语义版本 y políticas de deprecación.

### 3.2 Modelo de comunicación

Mensajes entre agentes y orquestador siguen un formato JSON con campos mínimos obligatorios y extensión libre por contexto:

- Identificadores y tiempo: message_id, trace_id, conversation_id, timestamp.
- Remitente/destinatarios: sender, recipients.
- Propósito: intent (información, delegación, validación, síntesis).
- Contenido y adjuntos: payload (estructurado), references (memoria, documentos).
- Control: context_version, causal_marks (reloj vectorial), budget (tokens/tiempo).
- Resultado: status, errors, tool_calls, tool_results.

Orden causal y resolución de conflictos se asegura por causal_marks y context_version; las respuestas deben referenciar in_reply_to cuando aplican. Las prioridades y el backpressure se codifican en headers y en el bus de eventos.

## 4. Agentes especializados: funciones y contratos

Las responsabilidades se dividen para separar preocupaciones y escalar el esfuerzo según complejidad:

- Reasoner Agent: define estrategia y límites; propone delegación y criterios de calidad.
- Planner Agent: descompone tareas en subtareas, selecciona herramientas MCP y establece límites de esfuerzo.
- Executor Agents: ejecutan con concurrencia controlada; minimizan el overhead de tokens escribiendo salidas estructuradas directamente y pasando referencias.
- Verifier Agent: valida y puntúa trayectorias, llamadas a herramientas, extracción de parámetros y reflexión; trigger la recuperación si se detecta desviación[^2].
- Memory Manager: consolida la memoria semántica en Postgres+pgvector, con resúmenes por fase y checkpoints[^9].

Contratos de APIs entre agentes:

- Intenciones explícitas (información_request, delegación, validación, síntesis) y semántica consistente entre componentes.
- Errores tipados con códigos y recomendaciones de reintento; políticas de reintento con jitter y presupuestos de reintentos por tarea.
- Trazas asociadas a cada contrato (trace_id, span_id por agente/herramienta).

Prompts y límites por rol:

- Reglas de escalado del esfuerzo según complejidad (p. ej., 1 agente para fact‑finding; 2–4 para comparaciones; ≥10 para investigación amplia), evitando duplicación y garantizando cobertura[^1].
- Salidas estructuradas y referencias ligeras al coordinador (archivos/uris) para reducir verbosidad y pérdida de información[^1].

Tabla 2. Mapa de agentes: entradas, salidas, métricas, SLIs/SLOs (propuestos)

| Agente            | Entradas principales                             | Salidas/artefactos                          | Métricas clave                         | SLIs/SLOs (objetivos)            |
|-------------------|---------------------------------------------------|---------------------------------------------|----------------------------------------|-----------------------------------|
| Reasoner          | Objetivo, contexto, memoria                       | Estrategia, criterios, límites              | Calidad de estrategia (score), tiempo  | ≤1.5 s p50, ≥0.8 score estrategia |
| Planner           | Estrategia, objetivos, herramientas disponibles   | Plan, subtareas, tool_map, límites          | Convergencia (code eval), adherencia   | p50 ≤ N pasos, p95 ≤ 1.5×N        |
| Executor (código) | Subtarea, tool_map, budget                        | Código, tests, logs                         | Éxito tests, latencia tool, tokens     | ≥95% tests passing p50            |
| Executor (web)    | Subtarea, herramientas web                        | Resultados web, evidencias                  | Relevancia, latencia, errores          | ≤800 ms p50, ≤2% errores          |
| Executor (docs)   | Subtarea, corpus, RAG                             | Extractos, citas                            | Precisión, completitud, citación       | ≥0.9 precisión, ≥0.8 completitud  |
| Verifier          | Trayectoria, outputs, contexto                    | Scores, aprobación, recomendaciones         | LLM‑as‑Judge, code eval                | ≥0.85 promedio scores             |
| Memory Manager    | Resultados parciales/finales                      | Síntesis, embeddings, snapshots             | Calidad de síntesis, latencia query    | p50 ≤ 200 ms, ≥0.85 calidad       |

Los SLIs/SLOs son objetivos iniciales propuestos para validación en pilotos y se ajustarán con telemetría real.

## 5. Flujos de trabajo optimizados

El flujo principal se organiza en tres fases, con paralelización explícita y evaluación continua:

- Amplitud primero. El Reasoner define estrategia; el Planner descompone y el Orquestador dispara 3–5 subagentes en paralelo, cada uno con 3+ herramientas concurrentes (búsqueda, navegación, recuperación). Se impone un presupuesto de tokens/tiempo por subagente[^1].
- Profundización. Se iteran subtareas según evaluación intermedia; se introducen subagentes adicionales si el Verifier detecta brechas. El Memory Manager sintetiza hallazgos intermedios y actualiza la memoria en pgvector.
- Síntesis y verificación. El Verifier aplica LLM‑as‑a‑Judge y code evaluations sobre trayectoria y outputs; se produce el informe final con citación y evidencias.

Manejo de dependencias y concurrencia:

- Ventana dinámica de concurrencia por subagente según carga y backpressure.
- Orden causal con causal_marks y versionado de contexto para evitar condiciones de carrera.
- Control de reintentos: políticas con jitter y límites por subtarea; escalamiento a disyuntores si los errores persisten[^4].

Salidas estructuradas y reducción del “token overhead”:

- Los Ejecutores escriben salidas en storage externo (archivos/uris) y pasan referencias ligeras al orquestador, minimizando el “juego de teléfono” y la verbosidad[^1].

Ejemplo (investigación):

- N subagentes de investigación en paralelo; cada uno usa búsqueda y navegación concurrentemente; síntesis intermedia; posible creación deCitationAgent para localizar citas específicas al cierre[^1].

Tabla 3. Fases vs. entrada/salida/paralelismo/presupuesto/reintentos

| Fase          | Entradas                          | Paralelismo                   | Presupuesto (tareas)                           | Reintentos/recuperación               | Salidas                         |
|---------------|-----------------------------------|-------------------------------|-----------------------------------------------|---------------------------------------|----------------------------------|
| Amplitud      | Objetivo, estrategia, contexto    | 3–5 subagentes; ≥3 herramientas | Tokens/tiempo por subagente; límite herramientas | Reintentos con jitter; disyuntores si error sostenido | Hallazgos por subagente; evidencias |
| Profundización| Hallazgos, evaluación intermedia  | Ajuste dinámico de subagentes | Incremento selectivo de presupuesto si ROI alto | Backpressure; snapshots por fase       | Síntesis parcial; updates de memoria |
| Síntesis      | Síntesis parcial, evidencias      | Limitado; enfoque en verificación | Presupuesto de verificación (LLM‑as‑Judge, code eval) | Rollback a snapshot si inconsistencia  | Informe final con citas y métricas |

## 6. Capacidades superiores

La propuesta supera a MiniMax Agent por diseño en cuatro ejes:

- Orquestación inteligente. Políticas de delegación explícitas, ruteo de modelos por presupuesto/costo‑latencia, selección dinámica de herramientas con límites y evaluación continua[^1][^2].
- Paralelización efectiva. Dos niveles de concurrencia (subagentes y herramientas), controlados por ventanas dinámicas y backpressure, maximizando throughput sin perder calidad[^1].
- Recuperación robusta. Disyuntores adaptativos, aislamiento por clúster, snapshots y consistencia causal para reanudar desde el punto de error y mantener la colaboración sin fallos en cascada[^4].
- Observabilidad avanzada. Trazas OpenTelemetry multiagente, propagación en MCP y evaluaciones automatizadas para detectar desviaciones y oportunidades de mejora[^2].

Tabla 4. Matriz de capacidades superiores: criterio de éxito y evidencia

| Capacidad                  | Criterio de éxito                         | Evidencia/soporte |
|---------------------------|-------------------------------------------|-------------------|
| Orquestación inteligente  | Cumplimiento de políticas y límites; reducción de desvíos | Principios y patrones documentados; telemetría continua [^1][^2] |
| Paralelización efectiva   | Reducción de tiempo de ciclo ≥40%          | Paralelización de dos niveles; datos de reducción de tiempo en escenarios comparables [^1] |
| Recuperación robusta      | Reanudación sin intervención y sin pérdida de contexto | Disyuntores, aislamiento y snapshots; guías de resiliencia [^4] |
| Observabilidad avanzada   | Trazas unificadas y evaluación de trayectoria | OpenTelemetry, MCP tracing y evaluadores LLM [^2] |

## 7. Integraciones técnicas y ruteo de modelos

Criterios de ruteo:

- Disponibilidad y ventana gratuita (hasta 7 de nov) para M2; latencias observadas; coste por millón de tokens; límites de tasa y calidad objetivo.
- Post‑7 de nov, conmutación a OpenRouter para modelos como Llama 3.3 70B Instruct (API compatible con OpenAI; ventana de contexto amplia), con fallbacks y enrutamiento al mejor proveedor[^6][^7].

Conectores MCP:

- Seguridad (autenticación/autorización), control de contexto y trazabilidad unificada entre cliente y servidor MCP; instrumentación automática con OpenTelemetry para cerrar la brecha de visibilidad[^3][^2].

Persistencia:

- PostgreSQL + pgvector para embeddings, sesiones y trazas; prácticas de indexación (IVF/HNSW según caso) y optimización para cargas AI (incluyendo despliegues gestionados como Aurora con patrones multi‑tenant)[^9][^10][^11].

Redis:

- Como bus de eventos, memoria operativa de sesión y cachés de baja latencia; patrones de throughput y coordinación de agentes según documentación y casos de aplicación[^12][^13].

Tabla 5. Integraciones: función y SLIs (objetivos propuestos)

| Componente              | Función                                   | SLIs (objetivos)                |
|-------------------------|-------------------------------------------|----------------------------------|
| MiniMax M2 (hasta 7/nov)| LLM primario en fase de amplitud/profundización | p50 latencia ≤ 1.2 s; uptime ≥ 99.5% |
| OpenRouter (Llama 70B)  | Fallback y procesamiento post‑migración   | p50 latencia ≤ 1.5 s; uptime ≥ 99.9% |
| MCP                     | Capa de herramientas y contexto            | ≤ 50 ms overhead de instrumentación |
| Postgres + pgvector     | Memoria semántica                          | p50 query ≤ 200 ms; ≥99.9% disponibilidad |
| Redis                   | Bus y caché                                 | p50 ≤ 5 ms; throughput ≥ 10k msgs/s |

Tabla 6. Ruteo de modelos: criterios y políticas (propuesta)

| Criterio                 | Política                                           |
|--------------------------|----------------------------------------------------|
| Coste por token          | Priorizar M2 mientras sea gratuito; luego ruteo por coste efectivo (entrada/salida) y calidad esperada[^6][^7] |
| Latencia                 | Seleccionar proveedor con menor p95 para la ventana requerida |
| Ventana de contexto      | Usar modelos con ventana suficiente (p. ej., 131k tokens para Llama 3.3 70B)[^7] |
| Límites de tasa          | Ajustar concurrencia y aplicar backpressure; fallback a OpenRouter si se superan thresholds |
| Calidad objetivo         | Medir con LLM‑as‑a‑Judge y code eval; re‑ruteo si score cae por debajo del umbral |

## 8. Observabilidad, telemetría y evaluación continua

La observabilidad se instrumenta como una funcionalidad central:

- OpenTelemetry. Cada agente y herramienta se instrumenta como spans con atributos clave (modelo, tokens_in/out, tool_name, latencia, éxito/fracaso, error_type). En MCP, se propaga el contexto para unificar trazas cliente‑servidor[^2].
- Trazas multiagente. Se visualizan interacciones, delegación y uso de herramientas; se reconstruyen causalidades y se detectan cuellos de botella y desvíos de trayectoria[^2].
- LLM‑as‑a‑Judge y code evaluations. Se evalúan trayectorias y outputs con rúbricas claras; se mide la convergencia en lotes de ejecuciones con número de pasos reales vs. mínimos[^2].
- Flujos de auto‑mejora. Telemetría y evaluaciones alimentan la refinería de prompts, la selección de herramientas y el ruteo de modelos; se valida el impacto re‑ejecutando en datos históricos[^2][^1].

Tabla 7. Catálogo de spans y atributos de trazabilidad (mínimos)

| Span                   | Atributos obligatorios                                                                 |
|------------------------|-----------------------------------------------------------------------------------------|
| llm.call               | model, provider, tokens_in, tokens_out, latency_ms, temperature, top_p, success, error_type |
| tool.call              | tool_name, tool_version, input_params, latency_ms, success, error_type, evidence_uri       |
| mcp.server.call        | server_id, method, request_id, latency_ms, success, error_type                              |
| agent.delegate         | from_agent, to_agent, intent, task_id, budget_tokens, latency_ms, success                   |
| verifier.eval          | eval_type (llm_judge/code), score, thresholds, inputs_hash, success                         |
| memory.write           | entity_type, embedding_model, vector_count, latency_ms, success                             |
| memory.query           | query_type, embedding_model, k, latency_ms, success, score                                 |

Tabla 8. Plantillas de evaluación (adaptación de prácticas)

| Caso de uso                    | Prompt/Plantilla (resumen)                                  | Métrica principal                 |
|-------------------------------|--------------------------------------------------------------|----------------------------------|
| Planificación de agentes      | Evaluar si la secuencia de delegación maximiza cobertura    | Adherencia al camino dorado      |
| Llamadas a herramientas       | Verificar selección y parámetros según intención del usuario| Eficiencia y corrección de llamadas |
| Selección de herramientas     | Valorar si la herramienta elegida es la más idónea          | Adecuación herramienta‑tarea     |
| Extracción de parámetros      | Comprobar exactitud y completitud de parámetros             | Precisión paramétrica            |
| Reflexión de agentes          | Evaluar calidad de auto‑crítica y ajustes                   | Mejora iterativa                 |
| Convergencia (code eval)      | Pasos reales vs. mínimos en lotes de consultas              | Puntuación de convergencia       |

Estas plantillas se adaptarán a cada dominio y se integrarán con la plataforma de observabilidad seleccionada[^2].

## 9. Gestión de estado y memoria

Modelo de memoria:

- Memoria de corto plazo en Redis. Estado operativo de sesión, colas de eventos, lockings livianos y heartbeats; soporte de backpressure y prioridades[^12].
- Memoria de largo plazo en PostgreSQL + pgvector. Embeddings de documentos, hechos, entidades y relaciones; snapshots de estado por fase; auditoría y retención governed[^9][^10][^11].

Políticas de retención y privacidad:

- Retención por tipo de dato (p. ej., trazas, salidas estructuradas, embeddings) con ventanas definidas por sensibilidad y valor operativo.
- Cifrado en tránsito y en reposo; control de acceso por roles; auditoría de accesos y de transferencia de contexto.

Consistencia y resolución de conflictos:

- Relojes vectoriales/marcas lógicas para ordenar cambios; snapshots antes de cambios relevantes; rollback a estados previos known‑good; validación de estado antes de reanudar operaciones[^4].

Diseño multi‑tenant:

- Aislamiento por tenant (schema/filas/particiones); límites de recursos por clúster de agentes; colas separadas por tenant para evitar interferencias.

Tabla 9. Mapa de datos: tipos, almacenamiento, retención, cifrado y acceso

| Tipo de dato           | Almacenamiento         | Retención (propuesta)       | Cifrado            | Control de acceso           |
|------------------------|------------------------|-----------------------------|--------------------|-----------------------------|
| Sesiones               | Redis + Postgres       | 30–90 días                  | En reposo + tránsito| RBAC por tenant/usuario     |
| Trazas/span            | Postgres (OLTP)        | 90–180 días                 | En reposo + tránsito| RBAC + auditoría            |
| Documentos/evidencias  | Object storage +索引   | 180–365 días                | En reposo + tránsito| RBAC + registros de acceso  |
| Embeddings             | Postgres + pgvector    | 365+ días (según valor)     | En reposo + tránsito| RBAC por tenant             |
| Checkpoints/snapshots  | Postgres               | 30–90 días                  | En reposo + tránsito| Acceso restringido (SRE)    |
| Configs/políticas      | Postgres               |版本化; según compliance     | En reposo + tránsito| Admin/seguridad             |

## 10. Recuperación de errores y robustez

El sistema adopta estrategias específicas para agentes con estado:

- Degradación con gracia. Timeouts basados en p95 para inferencias; canales de función reducida cuando fallan rutas primarias; priorización de mensajes críticos bajo carga; acuses ligeros, ordenación por timestamp y resolución de conflictos; backpressure adaptativo y rutas de escalada[^4].
- Disyuntores entre clústeres. Activación basada en métricas (tasas de éxito, tiempos de respuesta, frecuencia de errores); reintroducción gradual de tráfico y decisiones compartidas entre agentes del clúster afectado[^4].
- Aislamiento con preservación de colaboración. Agrupar agentes por capacidades y limitar acceso a recursos; patrones de mamparo (bulkhead); detección y alertas descentralizadas; colaboración mediante paso de mensajes ligero[^4].
- Orden de recuperación. Identificar agentes críticos por grafos de dependencia; recuperación por etapas; equilibrio entre orquestación central y coordinación distribuida; priorizar según impacto empresarial[^4].
- Sincronización de estado. Instantáneas periódicas; resolución de conflictos; relojes vectoriales/lógicas; validación de estado restaurado; rollback; alineación gradual para evitar sobrecargas[^4].
- Recuperación coordinada vs independiente vs híbrida. Selección según el alcance del fallo y las interdependencias.

Tabla 10. Matriz de fallos vs. estrategia de contención y recuperación

| Tipo de fallo                   | Contención                                | Recuperación                                  |
|---------------------------------|-------------------------------------------|-----------------------------------------------|
| Timeout de inferencia           | Backpressure; reducir concurrencia        | Reintentos con jitter; fallback de modelo     |
| Error de herramienta externa    | Disyuntor hacia clúster; canal reducido   | Retry programado; aislar herramienta          |
| Pérdida de mensajes             | Acuses ligeros; reenvío por prioridad     | Reconstrucción por snapshots; causal_marks    |
| Inconsistencia de estado        | Pausa coordinada; validación de estado    | Rollback a snapshot; reconciliación           |
| Sobrecarga del bus (Redis)      | Priorización; rate limiting               | Rebalanceo de colas; incremento temporal de capacidad |
| Fallo de dependencia interagente| Aislamiento por clúster; escalate         | Recuperación por etapas; híbrido según alcance|

## 11. Contratos de APIs entre agentes (contratos A2A)

El contrato inter‑agente se define por un esquema JSON que asegura semántica consistente y trazabilidad.

Esquema JSON mínimo del mensaje:

- message_id (string), trace_id (string), conversation_id (string), timestamp (ISO‑8601).
- sender (string), recipients (lista de strings).
- intent (string; p. ej., información_request, delegación, validación, síntesis).
- context_version (string), causal_marks (objeto).
- payload (objeto estructurado), references (lista de uris).
- budget (tokens, tiempo, herramientas_max), status (string), errors (lista de objetos).

Códigos de error y recomendaciones de reintento:

- invalid_request (400): corregir parámetros; no reintentar.
- tool_failure (502): reintentar con jitter (exponencial) hasta N veces; activar disyuntor si persiste.
- rate_limited (429): aplicar backpressure; reducir concurrencia; reintentar tras ventana.
- timeout (504): reducir ventana de concurrencia; fallback de modelo; reintento controlado.
- state_conflict (409): pausar; validar snapshots; reconciliar causal_marks; rollback si necesario.

Versionado semántico:

- Cambios compatibles hacia atrás incrementan versión menor; no compatibles incrementan versión mayor con periodo de deprecación y compatibilidad multiplexada.

Ejemplos de payloads (pseudocampos):

- delegación: { task_id, objetivo, tool_map, límites, criterio_éxito }
- validación: { trajectory_id, criterios, thresholds, eval_type }
- síntesis: { inputs, referencias, formato_salida, citación }

Tabla 11. Diccionario de campos del contrato A2A (mínimos y extensiones)

| Campo              | Tipo      | Obligatorio | Descripción                                          |
|--------------------|-----------|-------------|------------------------------------------------------|
| message_id         | string    | Sí          | Identificador único del mensaje                      |
| trace_id           | string    | Sí          | Identificador de traza                               |
| conversation_id    | string    | Sí          | Identificador de sesión/tarea                        |
| timestamp          | string    | Sí          | Marca de tiempo ISO‑8601                             |
| sender             | string    | Sí          | Agente emisor                                        |
| recipients         | lista     | Sí          | Agentes destinatarios                                |
| intent             | string    | Sí          | Intención del mensaje                                |
| context_version    | string    | Sí          | Versión del contexto                                 |
| causal_marks       | objeto    | Opcional    | Reloj vectorial/marcas lógicas                       |
| payload            | objeto    | Sí          | Contenido estructurado                               |
| references         | lista     | Opcional    | URIs de evidencias/salidas                           |
| budget             | objeto    | Opcional    | Límites de tokens/tiempo/herramientas                |
| status             | string    | Sí          | Estado de procesamiento                              |
| errors             | lista     | Opcional    | Detalles de error tipados                            |

## 12. Plan de implementación por fases

Fase 1 (MVP, semanas 1–4):

- Orquestador básico con contratos A2A y bus Redis.
- Integración M2 (gratis hasta 7 de nov) y fallback mínimo a OpenRouter.
- Executor de código con herramientas MCP básicas.
- Observabilidad mínima: spans de LLM y herramientas; trazas iniciales.

Fase 2 (semanas 5–8):

- Executors web y documentos; Memoria Manager y pgvector.
- Observabilidad avanzada: trazabilidad MCP cliente‑servidor; plantillas LLM‑as‑a‑Judge.
- Paralelización de dos niveles con backpressure y prioridades.

Fase 3 (semanas 9–12):

- Recuperación de errores robusta: disyuntores, aislamiento por clúster, snapshots.
- Evaluaciones continuas y auto‑mejora; ruteo inteligente de modelos con budgets.

Criterios de salida (go/no‑go):

- Cumplimiento de SLIs básicos (latencias p50, tasas de éxito).
- Convergencia dentro de umbrales en code evaluations.
- Reducción de tiempo de ciclo ≥20% vs. baseline en tareas piloto.

Riesgos y mitigaciones:

- Dependencia del periodo gratuito de M2: preparar conmutación a OpenRouter y configurar ruteo y budgets.
- Variabilidad de latencias y rate limits: instrumentar y aplicar backpressure; pruebas de carga progresivas.
- Costes de tokens: presupuestos por tarea y evaluación continua; usar rutas de menor coste con calidad suficiente.

Tabla 12. Cronograma por fase: entregables, dependencias y métricas

| Fase  | Entregables clave                             | Dependencias                     | Métricas de salida                      |
|-------|-----------------------------------------------|----------------------------------|-----------------------------------------|
| 1     | Orquestador, contratos A2A, M2+fallback, executor código, observabilidad básica | Acceso M2, Redis                 | p50 latencia ≤ 1.5 s; ≥95% éxito básico |
| 2     | Executors web/docs, Memory Manager, pgvector, MCP tracing, LLM‑as‑a‑Judge | MCP servers, Postgres+pgvector   | ≥0.8 score LLM‑as‑a‑Judge               |
| 3     | Recuperación robusta, disyuntores, snapshots, evaluaciones y ruteo | Telemetría, colas Redis          | Reducción tiempo ciclo ≥40% vs baseline |

## 13. Métricas, SLIs/SLOs y KPIs

SLIs/SLOs por componente (objetivos propuestos):

- LLM (inferencias): p50 ≤ 1.5 s; p95 ≤ 3 s; tasa de éxito ≥ 98%; coste por token controlado por ruteo.
- Herramientas MCP: p50 ≤ 800 ms; p95 ≤ 2 s; tasa de error ≤ 2%.
- Memoria semántica (pgvector): p50 ≤ 200 ms; p95 ≤ 500 ms; disponibilidad ≥ 99.9%.
- Orquestador: spawning ≤ 50 ms; adherencia a presupuestos ≥ 95%; divergencias de trayectoria ≤ 5%.
- Recuperación: tiempo de reanudación ≤ 5 s; pérdida de contexto 0; falsos positivos de disyuntor ≤ 1%.

KPIs de negocio:

- Tiempo medio de ciclo por tarea.
- Coste por tarea (tokens + herramientas).
- Calidad del output (LLM‑as‑a‑Judge; evaluación humana selectiva).
- Tasa de convergencia y pasos promedio vs. mínimos.
- Porcentaje de tareas sin intervención.

Estrategia de evaluación continua:

- Conjunto de tareas de referencia con verdad fundamental.
- Rúbricas para LLM‑as‑a‑Judge (precisión factual, citación, completitud, eficiencia).
- Code evaluations para convergencia y adherencia a caminos eficientes.
- Bucles de auto‑mejora basados en patrones de fallo y regresiones detectadas[^2][^1].

Tabla 13. Catálogo de SLIs/SLOs y KPIs (objetivos iniciales)

| Métrica                         | Definición                              | Objetivo (propuesto)            |
|---------------------------------|-----------------------------------------|----------------------------------|
| llm.p50_latency                 | Latencia p50 por inferencia             | ≤ 1.5 s                          |
| llm.error_rate                  | % de fallos (timeouts/excepciones)      | ≤ 2%                             |
| tool.p50_latency                | Latencia p50 de herramientas             | ≤ 800 ms                         |
| pgvector.query.p50              | Latencia p50 de búsqueda vectorial       | ≤ 200 ms                         |
| budget.adherence                | % de tareas dentro de presupuesto        | ≥ 95%                            |
| trajectory.convergence_score    | Pasos reales vs mínimos                  | ≥ 0.85                           |
| output.quality                  | Score LLM‑as‑a‑Judge                     | ≥ 0.85                           |
| recovery.resume_time            | Tiempo de reanudación tras fallo         | ≤ 5 s                            |
| business.cycle_time             | Tiempo de ciclo por tarea                | −40% vs. baseline                |
| business.cost_per_task          | Coste total por tarea                    | −30% vs. baseline (post‑migración) |

## 14. Anexos

Plantillas de prompts y políticas de delegación:

- Reasoner: “Dado el objetivo y el contexto, define estrategia de amplitud primero, límites de tokens por subagente y criterios de delegación.”  
- Planner: “Descompón en subtareas, selecciona herramientas MCP candidatas y asigna límites de esfuerzo por subtarea.”  
- Executor: “Ejecuta con concurrencia controlada; escribe salidas estructuradas y registra evidencias con referencias ligeras.”  
- Verifier: “Evalúa trayectoria y outputs con rúbrica; aplica LLM‑as‑a‑Judge y code evaluations; recomienda recuperación si score < umbral.”[^1][^2]

Ejemplos JSON para contratos A2A (reutilizables):

- Delegación:
  ```
  {
    "message_id": "msg_001",
    "trace_id": "trc_123",
    "conversation_id": "conv_456",
    "timestamp": "2025-11-03T23:20:30Z",
    "sender": "orchestrator",
    "recipients": ["executor_code"],
    "intent": "delegación",
    "context_version": "v1",
    "payload": {
      "task_id": "task_code_789",
      "objetivo": "Implementar función X con tests",
      "tool_map": ["mcp://tools/python", "mcp://tools/shell"],
      "límites": {"tokens": 4000, "tiempo_s": 120, "herramientas_max": 3},
      "criterio_éxito": "tests passing ≥95%"
    },
    "status": "pending"
  }
  ```
- Validación:
  ```
  {
    "message_id": "msg_002",
    "trace_id": "trc_123",
    "conversation_id": "conv_456",
    "timestamp": "2025-11-03T23:21:00Z",
    "sender": "verifier",
    "recipients": ["orchestrator"],
    "intent": "validación",
    "context_version": "v1",
    "payload": {
      "trajectory_id": "trj_456",
      "criterios": ["precisión", "citación", "completitud"],
      "thresholds": [0.9, 0.8, 0.85],
      "eval_type": "llm_judge"
    },
    "status": "done"
  }
  ```

Glosario de términos:

- MCP (Model Context Protocol). Estándar abierto para conectar aplicaciones de IA a fuentes de datos y herramientas de forma segura y bidireccional, con soporte para trazabilidad y control de contexto[^3].
- LLM‑as‑a‑Judge. Práctica de evaluar salidas y trayectorias de agentes usando un LLM como juez, con rúbricas claras y métricas reproducibles[^2].
- Code evaluations. Comprobaciones programáticas para medir la convergencia y adherencia de trayectorias, con lotes de ejecuciones y puntuación comparativa[^2].
- Snapshot/Checkpoint. Imagen del estado del sistema en un punto del tiempo para permitir recuperación y rollback.
- Backpressure. Técnica para controlar la presión en colas y recursos, ajustando tasas de entrada o concurrentes para evitar sobrecarga.
- Disyuntor (Circuit Breaker). Mecanismo que interrumpe llamadas hacia componentes que fallan de forma sostenida, permitiendo recuperación gradual.

Referencias

[^1]: Anthropic Engineering. “How we built our multi‑agent research system.”  
[^2]: Arize AI. “Agent Observability and Tracing.”  
[^3]: Model Context Protocol. “What is the Model Context Protocol (MCP)?”  
[^4]: Galileo. “Multi‑Agent AI Failure Recovery That Actually Works.”  
[^5]: Shakudo. “Top 9 AI Agent Frameworks.”  
[^6]: CometAPI. “Minimax M2 API.”  
[^7]: OpenRouter. “Llama 3.3 70B Instruct – API, Providers, Stats.”  
[^8]: Tiger Data. “PostgreSQL as a Vector Database: A Pgvector Tutorial.”  
[^9]: pgvector GitHub. “Open‑source vector similarity search for Postgres.”  
[^10]: AWS Blog. “Multi‑tenant vector search with Amazon Aurora PostgreSQL and Bedrock knowledge bases.”  
[^11]: Salesforce Engineering. “Optimizing Postgres for AI Workloads: Integrating pgvector.”  
[^12]: Redis Docs. “How agents work | Docs – Redis.”  
[^13]: Redis Blog. “Introducing Haink: Redis applied AI agent.”