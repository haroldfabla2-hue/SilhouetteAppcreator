# Estrategias de implementación para superar MiniMax Agent: análisis comparativo, costos y plan óptimo

## 1. Resumen ejecutivo y decisión recomendada

Nuestro objetivo es superar, en un horizonte de 90 días, el rendimiento de MiniMax Agent en dos frentes: capacidad de agente (uso de herramientas y flujos complejos) y productividad para ingeniería de software. La restricción principal es hacerlo con un coste predecible y una arquitectura mantenible que no nos ate a un único proveedor. La evidencia técnica disponible muestra que MiniMax M1 ofrece una ventana de contexto de 1 millón de tokens, soporte de llamadas a función y un rendimiento competitivo en ingeniería de software (SWE-bench Verified ≈ 56%) y uso de herramientas (TAU-bench), lo que lo convierte en un referente sólido del estado del arte dentro de modelos de权重 abierta y razonamiento eficiente de test-time compute con Lightning Attention[^1][^2]. MiniMax M2, con arquitectura Mixture‑of‑Experts y 10 mil millones de parámetros activados, está diseñado para latencias inferiores y mayor throughput, posicionándose para flujos interactivos de agente[^5].

Comparando tres estrategias, la Estrategia C (mejor de ambos mundos) maximiza la relación valor‑riesgo: arranca con un MVP A1 que utiliza MiniMax M1 para flujos de contexto largo y llamadas a función críticas, y ya incorpora un bypass RAG (Generación aumentada por recuperación) con Llama 3 y un stack 100% open source para resiliencia y control de costes. En la fase A2, se completa la sustitución parcial de dependencias de MiniMax: orquestación con frameworks OSS, cacheo semántico, vectorización con PostgreSQL + pgvector/pgai, y se establecen motores duales con selección dinámica por SLA. El resultado es un sistema que combina rendimiento inicial competitivo (heredar benchmarks de M1) con independencia técnica progresiva, menor TCO y una ruta clara de escalado.

La decisión se apoya en tres pilares:
- Rendimiento: MiniMax M1 cubre de forma solvente tareas de contexto largo, SWE y uso de herramientas; MiniMax M2 aporta ventajas de eficiencia (MoE) en agentes interactivos[^1][^5].
- Riesgo y dependencia: la compatibilidad OSS y despliegues con vLLM permiten ejecutar M1 sin “vendor lock‑in” a su API; se mitiga con fallback OSS, cache y extracción temprana de valor[^3].
- Coste y time‑to‑market: un MVP en 30–45 días es viable con M1 y un stack OSS bien acotado; el TCO mejora al migrar tráfico intensivo a OSS en A2 y fijar dual‑run con selección por SLA[^16][^17].

Recomendación adoptada: Estrategia C, por su capacidad de entregar valor rápido, reducir dependencia de un solo proveedor y ofrecer una ruta de optimización de coste/latencia más robusta que A o B por separado.

### 1.1 Decisión y beneficios esperados

La Estrategia C entrega valor inmediato (MVP con MiniMax M1 en orquestación OSS) y crea, en paralelo, un bypass OSS funcional que permite desviar progresivamente las consultas más sensibles a coste y latencia. Los beneficios esperados incluyen:
- Rendimiento en contexto largo y agentes: se capitaliza la ventana de 1M tokens y el soporte nativo de llamadas a función de M1, fundamentales para tareas multi‑paso con acceso a herramientas[^1][^2].
- Reducción del TCO en el horizonte de 90 días: al introducir RAG con Llama 3 y pgvector/pgai para embeddings, más selección dinámica por SLA, se espera reducir entre 25% y 40% el gasto variable de tokens en cargas no críticas a las 8–12 semanas, con mayor ahorro en escenarios de alto volumen[^16].
- Flexibilidad y control: la arquitectura dual con selección por SLA y rutas de fallback permite ajustar el punto de equilibrio coste‑latencia‑calidad sin reescribir la capa de orquestación.

### 1.2 Riesgos clave y mitigaciones

- Dependencia de MiniMax (API/SLAs): mitigada mediante soporte OSS (vLLM/Transformers), despliegue propio de M1 cuando convenga y fallback con Llama 3/Qwen/Mistral para degradación controlada[^3][^6][^15].
- Gobernanza y cumplimiento: se prioriza cifrado en tránsito y reposo, control de acceso granular y auditoría; el pipeline de datos permanece bajo nuestro dominio con PostgreSQL/pgvector/pgai[^15].
- Coste y latencia: el patrón RAG reduce tokens en prompts largos; el cacheo semántico y la selección dinámica por SLA impiden que picos de tráfico se canalicen por modelos costosos; se monitoriza con LangFuse/Phoenix[^22][^23].

## 2. Definición del objetivo: ¿Qué significa superar a MiniMax Agent?

Definimos “superar” como mejorar de forma simultánea y sostenida: 
- Tasa de éxito de tareas multi‑paso con uso de herramientas (p. ej., TAU‑bench en dominios airline y retail).
- Resolución de issues de ingeniería de software en entornos realistas (SWE‑bench Verified).
- Latencia extremo a extremo y coste por conversación dentro de SLA acordados.

La evidencia disponible para MiniMax M1 reporta ≈56% en SWE‑bench Verified, así como resultados competitivos en TAU‑bench (airline/retail), además de una ventana de contexto nativa de 1M tokens y eficiencia en test‑time compute gracias a Lightning Attention[^1][^2]. Estos valores funcionan como objetivos cuantitativos iniciales para MVP. A falta de un benchmark completo y homogéneo de “MiniMax Agent” en dominios específicos del negocio, se utilizarán proxies (SWE‑bench, TAU‑bench, MRCR/LongBench‑v2) y se complementarán con pilotos internos blindados por NDAs para cerrar la brecha de información.

Información clave pendiente: detalle del stack “MiniMax Agent” (orquestación, políticas de herramientas, memoria, observabilidad), benchmarks internos de nuestro dominio y límites de latencia/costo objetivo. Éstos se recabarán en la fase de descubrimiento (Semana 1).

### 2.1 Métricas de éxito y umbrales

Para la decisión de avance (Exit/Next), se establecen umbrales de MVP y objetivos a 90 días:
- Éxito de tareas multi‑paso (herramientas): ≥50% en MVP; ≥58–60% a 90 días.
- SWE‑bench Verified: ≥50% en MVP; ≥56–58% a 90 días.
- Latencia p95: ≤6–8 s en MVP; ≤4–6 s a 90 días, con selección por SLA y degradaciones controladas.
- Coste por conversación: dentro de presupuesto pactado (ver Matriz de costes), con reducción ≥25% a 90 días vía RAG y cacheo.
- Calidad percibida (CSAT del stakeholder): ≥4/5 en MVP; ≥4.3/5 a 90 días.

## 3. Panorama técnico: capacidades MiniMax M1/M2 y implicaciones

MiniMax M1 es un modelo de razonamiento de atención híbrida a gran escala, de权重 abierta, con ventana de contexto nativa de 1 millón de tokens y soporte para llamadas a función. Está diseñado para escenarios de productividad complejos, destacando en ingeniería de software, uso de herramientas y tareas de contexto largo. La arquitectura incorpora Lightning Attention para escalar el compute de test‑time de forma eficiente; las variantes “40k/80k” gestionan presupuestos de razonamiento diferenciados. En pruebas publicadas, M1 alcanza ≈56% en SWE‑bench Verified y resultados competitivos en TAU‑bench[^1][^2]. 

MiniMax M2 se apoya en una arquitectura Mixture‑of‑Experts (MoE) con 10 mil millones de parámetros activados (≈230 mil millones totales) y apunta a agentes interactivos con menor latencia y mayor throughput. Su diseño favorece tiempos de respuesta más bajos, clave en experiencias de agente “online”, con despliegue disponible en repositorios públicos[^5].

Para orquestación y despliegue, la compatibilidad con vLLM y Transformers, así como el soporte de llamadas a función, permiten integrar M1/M2 en flujos de agente con patrones de out‑of‑the‑box y ejecución local o self‑hosted cuando sea necesario[^3]. Esta flexibilidad técnica habilita tanto la Estrategia A (híbrida) como la C (bypass OSS), reduciendo el riesgo de lock‑in.

Para ilustrar estas diferencias, la siguiente tabla sintetiza atributos relevantes para agentes:

Tabla 1. Comparativa técnica M1 vs M2
| Atributo                          | MiniMax M1                                                | MiniMax M2                                                |
|-----------------------------------|-----------------------------------------------------------|-----------------------------------------------------------|
| Arquitectura                      | Atención híbrida (Lightning Attention)                    | Mixture‑of‑Experts (MoE)                                  |
| Parámetros (totales/activados)    | 456B totales; 45.9B activados por token                   | ≈230B totales; 10B activados                              |
| Ventana de contexto               | 1M tokens (nativa)                                        | ~200K+ tokens (reportado en análisis de upgrades)         |
| Soporte de herramientas           | Sí (function calling nativo)                              | Sí (enfocado a agentes interactivos)                      |
| Benchmarks destacados             | SWE‑bench ≈56%; TAU‑bench competitivo                     | Menor latencia y mayor throughput (objetivo de diseño)    |
| Compatibilidad despliegue         | vLLM, Transformers, function calling                      | Repositorio público (Hugging Face)                        |

Fuentes: especificaciones y guías técnicas publicadas[^1][^2][^3][^4][^5][^6].

### 3.1 Capacidades M1 para agentes

M1 ofrece capacidades de agente maduras: llamadas a función nativas, memoria de largo contexto y eficiencia en test‑time compute, con resultados robustos en contextos largos (p. ej., MRCR) y tareas de ingeniería de software (SWE‑bench). Esto se traduce en ventajas prácticas en flujos multi‑paso que requieren herramientas, trazabilidad y razonamiento prolongado[^1][^2].

### 3.2 Capacidades M2 para agentes

M2 prioriza latencia y throughput gracias a su MoE, ajustándose a escenarios interactivos con múltiples herramientas y cambios de estado frecuentes. En agentes conversacionales de alta intensidad (turnos rápidos y herramientas pesadas), su eficiencia puede convertirse en una ventaja operativa en producción[^5].

### 3.3 Implicaciones para el diseño

La decisión entre M1 y M2 depende del SLA:
- Si el objetivo es contexto extremo (1M tokens) y razonamiento sostenido, M1 es preferible.
- Si el objetivo es latencias agresivas con agentes interactivos de herramienta múltiple, M2 aporta eficiencia por su MoE. En ambos casos, la compatibilidad con vLLM/Transformers y function calling reduce la fricción de integración[^3].

## 4. Estrategia A: Híbrida MiniMax + Gratuitos

Arquitectura propuesta: M1/M2 como núcleo de razonamiento y uso de herramientas, acompañado de un stack OSS para RAG, orquestación y observabilidad. Despliegue con vLLM/Transformers y pipeline de knowledge con PostgreSQL + pgvector/pgai; orquestación con frameworks OSS (LangChain, AutoGen, Semantic Kernel) según el caso; y telemetría con LangFuse/Phoenix[^3][^10][^11][^12][^14][^19][^22][^23]. 

Dependencia de MiniMax: se mitiga al aprovechar pesos abiertos (M1), rutas de despliegue self‑hosted y un fallback OSS bien instrumentado. Esta estrategia acelera el time‑to‑market y permite validar rápidamente el valor del agente en contexto largo y uso de herramientas.

Tabla 2. Matriz de riesgos de dependencia (API/SLAs, coste, compatibilidad)
| Riesgo                                    | Descripción                                                       | Mitigación OSS                                                                 | Prioridad |
|-------------------------------------------|-------------------------------------------------------------------|---------------------------------------------------------------------------------|-----------|
| API/SLAs de MiniMax                       | Latencia o disponibilidad variable                                | Despliegue self‑hosted con vLLM; rutas de fallback a Llama/Qwen/Mistral[^3][^6] | Alta      |
| Coste por token (entrada/salida)          | Cargas intensivas elevan OPEX                                     | RAG para reducir tokens; cache semántico; selección por SLA[^15]                | Alta      |
| Compatibilidad de herramientas             | Cambios en contratos/formatos                                     | Abstracción vía framework (LangChain/AutoGen/SK) y MCP-like adapters[^10][^11]  | Media     |
| Gobernanza y cumplimiento                 | Datos sensibles en terceros                                        | Datos y vector store bajo nuestro dominio; cifrado y IAM                        | Alta      |

Tabla 3. Desglose de costos (Desarrollo/Operación) con y sin API comercial
| Componente                         | Con API comercial (referencia)                 | Sin API (OSS/self‑hosted)                                   | Notas |
|-----------------------------------|-----------------------------------------------|--------------------------------------------------------------|-------|
| Núcleo de agente (orquestación)   | $50k–$300k+ (inicial)[^16]                     | $40k–$200k+ (según complejidad)                              | Depende de integraciones |
| Uso de LLM (tokens)               | $1k–$5k/mes (típico)[^16]                      | Inferiore con RAG/cache y modelos más pequeños               | Reducción con patrones OSS |
| RAG/Infra de conocimiento         | $500–$2.5k/mes[^16]                            | OSS: PostgreSQL+pgvector/pgai[^19][^21]                      | Control total de datos |
| Observabilidad                    | $200–$1k/mes[^16]                              | OSS: LangFuse/Phoenix[^22][^23]                              | Trazabilidad y evaluación |
| Seguridad y mantenimiento         | $500–$2k/mes[^16]                              | IAM + auditoría interna                                     | Requisitos de cumplimiento |

### 4.1 Tiempo de desarrollo y rendimiento

Un MVP viable se alcanza en 30–45 días con M1, integrando herramientas clave y un RAG mínimo con pgvector/pgai. El rendimiento esperado hereda los resultados de M1 en SWE‑bench y TAU‑bench, con margen de mejora vía prompts/plantillas y un RAG que recorte tokens y eleve la precisión contextual[^1][^2][^21].

### 4.2 Costos y mantenimiento

El coste mensual operativo se alinea con los rangos de la industria para agentes, con la posibilidad de reducirlo significativamente mediante RAG, cacheo semántico y selección dinámica por SLA (ver Tabla 3). La mantenibilidad mejora al abstraer la orquestación con frameworks OSS, versionar prompts y modelar herramientas de forma modular[^16][^22].

## 5. Estrategia B: 100% Open Source

Diseño: LLMs open source (Llama 3/3.1, Qwen 2.5, Mistral, Gemma 2), embeddings (SBERT/BGE/Nomic), vectorización con PostgreSQL + pgvector/pgai, y orquestación con frameworks OSS. Esta vía evita dependencia de MiniMax, otorga control total de datos y permite optimizar OPEX; requiere mayor esfuerzo de integración, ajuste y operaciones[^15][^6][^19][^21].

Tabla 4. Stack 100% OSS: componentes y pros/contras
| Capa                 | Componente OSS                          | Pros                                                                 | Contras                                              |
|----------------------|-----------------------------------------|----------------------------------------------------------------------|------------------------------------------------------|
| LLM base             | Llama 3/3.1, Qwen 2.5, Mistral, Gemma 2 | Sin lock‑in, costo variable bajo, varias opciones de tamaño          | Ajustes finos necesarios; posible menor “out‑of‑the‑box” |
| Embeddings           | SBERT/BGE/Nomic                         | Multilingüe, tamaños variables, buen rendimiento en RAG              | Elección y evaluación requieren pruebas              |
| Vectorización        | PostgreSQL + pgvector/pgai              | Datos bajo nuestro control, SQL + vectores, simplifica pipelines     | Operaciones y tuning necesarios                      |
| Orquestación         | LangChain/AutoGen/Semantic Kernel       | Patrones de flujo/mensajería; integración flexible                   | Complejidad de integración y gobernanza de prompts   |
| Observabilidad       | LangFuse/Phoenix                         | Telemetría y evaluación integradas                                   | Curva de uso y operación                             |

Tabla 5. Estimaciones de tiempo y costo por fase
| Fase             | Duración estimada | Tareas clave                                        | Costo inicial (rango)      |
|------------------|-------------------|-----------------------------------------------------|----------------------------|
| Descubrimiento   | 2–3 semanas       | Casos de uso, KPIs, diseño de datos, riesgos        | $10k–$30k                  |
| Prototipo A0     | 3–4 semanas       | RAG mínimo, LLM OSS, orquestación básica            | $20k–$60k                  |
| Beta A1          | 4–6 semanas       | Observabilidad, seguridad, herramientas esenciales  | $40k–$100k                 |
| Producción A2    | 6–8 semanas       | Escalado, optimizaciones, dual‑run                  | $60k–$150k                 |

Fuentes y rangos de costo de referencia[^16][^6][^10][^19][^21].

### 5.1 Rendimiento esperado

El rendimiento depende del LLM y la calidad del RAG. En context windows, Llama 3/3.1 ofrece ventanas estándar (≈8K tokens en variantes comunes), inferiores a M1; la calidad se compensa con RAG y chunking adecuados. La estrategia Óptima en B es seleccionar LLMs por caso de uso y ajustar embeddings y recuperadores para maximizar precisión y reducir tokens[^15].

### 5.2 Mantenibilidad y escalabilidad

PostgreSQL + pgvector/pgai simplifica la gestión de datos y embeddings, con escalabilidad razonable para aplicaciones de RAG; se complementa con patrones de despliegue (p. ej., Ollama) y prácticas MLOps para versionado y monitorización[^19][^21][^15].

## 6. Estrategia C (Recomendada): Mejor de ambos mundos

Arquitectura híbrida: M1/M2 para flujos críticos y contexto largo; Llama/Qwen/Mistral para RAG y degradaciones. La orquestación OSS aplica patrones de flujo/mensajería (LangChain/AutoGen/Semantic Kernel), con vectorización con pgvector/pgai, y observabilidad/eval con LangFuse/Phoenix. La selección dinámica por SLA y cacheo semántico optimiza latencia/coste manteniendo calidad[^10][^11][^12][^19][^22][^23].

Tabla 6. Mapa de sustitución: qué replicar, mejorar o sustituir
| Capacidad MiniMax                 | Decisión                      | Alternativa OSS/tecnología                    | Beneficio esperado                         | Complejidad |
|----------------------------------|-------------------------------|----------------------------------------------|--------------------------------------------|------------|
| Contexto largo (1M tokens)       | Replicar                      | M1self‑hosted; degradación con RAG           | Calidad en tareas complejas                 | Media      |
| Function calling                 | Replicar                      | Function calling M1 + abstracción en LangChain/AutoGen | Estabilidad de flujos con herramientas      | Media      |
| Orquestación de agentes          | Mejorar                       | AutoGen/Semantic Kernel                       | Mensajería estructurada y trazabilidad      | Media      |
| Observabilidad y evaluación      | Mejorar                       | LangFuse/Phoenix                              | Mejorar calidad y reducir fallos            | Baja       |
| RAG y vectorización              | Sustituir                     | PostgreSQL + pgvector/pgai                    | Control de datos y menor OPEX               | Baja       |
| Latencia en agentes interactivos | Mejorar (con M2)              | Dual‑run M2 vs M1                             | Mejor p95 latencia con alto throughput      | Media      |

### 6.1 Plan de implementación (30–60–90 días)

Fase A1 (0–30 días): MVP con M1self‑hosted, herramientas mínimas viables (core APIs), RAG básico (pgvector), evaluación inicial con LangFuse/Phoenix. Fase A2 (31–60 días): dual‑run con M1 y Llama/Qwen para RAG y degradaciones; expansión de herramientas; cache semántico. Fase A3 (61–90 días): optimizaciones avanzadas (routing por SLA, políticas de degradación), escalado operativo y endurecimiento de seguridad.

Tabla 7. Cronograma detallado y entregables por hito
| Hito     | Entregables clave                                 | Responsables           | Criterios de aceptación                         |
|----------|----------------------------------------------------|------------------------|-------------------------------------------------|
| A1 (D30) | M1self‑hosted; RAG mínimo; 3–5 herramientas        | Líder técnico, MLOps   | Éxito ≥50%; p95 ≤8 s; CSAT ≥4/5                 |
| A2 (D60) | Dual‑run; cache semántico; observabilidad avanzada | Ingeniería, QA         | Reducción OPEX ≥20%; fallos ↓; p95 ≤6–7 s       |
| A3 (D90) | Routing por SLA; endurecimiento seguridad; escalado| Arquitectura, SecOps   | Éxito ≥58–60%; p95 ≤4–6 s; reducción OPEX ≥25–40%|

Fuentes de prácticas y arquitectura de referencia[^15][^16][^20][^24].

### 6.2 Costos y mantenimiento

Inversión inicial: $50k–$300k+ según complejidad y herramientas integradas; operación mensual típica de $3.2k–$13k (tokens, RAG, observabilidad, seguridad), ajustable con OSS y RAG. El escalado se soporta con selección por SLA y dimensionamiento de infraestructura, manteniendo gobernanza y seguridad bajo nuestro control[^16].

## 7. Análisis transversal comparativo

Comparando A, B y C:
- Tiempo de desarrollo: A y C permiten MVP más rápido (30–45 días); B exige más integración y ajuste (60–90 días para parity funcional).
- Rendimiento esperado: C hereda M1/M2 y habilita degradación/optimización OSS; A compite en calidad con dependencia mayor; B puede acercarse con buen RAG pero con más esfuerzo.
- Costos: C ofrece mejor TCO al combinar API crítica con OSS para cargas sensibles; B minimiza OPEX pero con inversión inicial mayor.
- Mantenibilidad y escalabilidad: C facilita gobernanza y observabilidad, con rutas claras de mejora; B requiere disciplina operativa en MLOps.
- Ventajas competitivas: C logra diferenciación por flexibilidad y SLA; A por velocidad; B por control total y privacidad.

Tabla 8. Matriz comparativa A vs B vs C
| Criterio           | Estrategia A (Híbrida)         | Estrategia B (100% OSS)               | Estrategia C (Híbrida óptima)               |
|--------------------|---------------------------------|---------------------------------------|---------------------------------------------|
| Time‑to‑market     | 30–45 días (MVP)                | 60–90 días (paridad)                  | 30–45 días (MVP)                            |
| Rendimiento        | Alto (M1/M2)                    | Medio‑alto (depende de RAG)           | Alto (M1/M2) + OSS optimizado               |
| TCO                | Medio                           | Bajo a medio                          | Bajo‑medio                                  |
| Dependencia        | Alta (API/SLAs MiniMax)         | Baja                                   | Media (controlada con fallback OSS)         |
| Mantenibilidad     | Media (vLLM/Transformers)       | Media‑alta (operaciones OSS)          | Alta (orquestación OSS + dual‑run)          |
| Escalabilidad      | Alta (vLLM/self‑hosted)         | Media‑alta (PostgreSQL + pgvector)    | Alta (routing por SLA, cache, MoE/M1)       |

### 7.1 Sostenibilidad técnica ylock‑in

Para evitar dependencia excesiva, se propone: abstracción de orquestación (frameworks OSS), compatibilidad y despliegue con vLLM/Transformers, selección dinámica por SLA y rutas de fallback, además de almacenamiento y observabilidad bajo control interno[^3].

## 8. Gobernanza, seguridad y cumplimiento

Se requiere cifrado en tránsito y en reposo, control de acceso granular, auditoría y registros; todo ello alineado con normativas como GDPR, HIPAA y SOC 2. La integración segura con herramientas (GitHub, Jira, Slack) debe seguir principios de mínimo privilegio y segregación de secretos. La evaluación y observabilidad de agentes con LangFuse/Phoenix asegura trazabilidad y mejora continua[^22][^23][^26].

Tabla 9. Controles de seguridad y cumplimiento por capa
| Capa                 | Controles clave                                                     | Herramientas/Prácticas                |
|----------------------|---------------------------------------------------------------------|---------------------------------------|
| Datos                | Cifrado E2E; clasificación; DLP                                     | IAM, KMS; políticas de acceso         |
| Aplicación           | Autenticación/Autorización; MFA; OAuth; auditoría                  | LangFuse/Phoenix para trazabilidad    |
| Infraestructura      | Network policies; hardening; secretos gestionados                  | CI/CD con controles de cumplimiento   |
| Integraciones        | Scopes mínimos; rotación de tokens; logging                         | Registro y revisión de accesos        |

### 8.1 Gestión de riesgos operativos

Se establecen límites de tasa y quotas por tenant, mecanismos de degradación controlada (fallback OSS), y políticas de coste/uso con alertas. El plan de respuesta a incidentes define roles, playbooks de contención y comunicación a stakeholders[^16].

## 9. Roadmap de implementación detallada (Estrategia C)

Mapa de capacidades del agente:
- Herramientas: GitHub/Jira/Slack, APIs internas.
- Memoria/contexto: sesión y largo plazo (documentos, issues).
- Planificación: objetivos y tareas, con políticas de reintento.
- Orquestación: LangChain/AutoGen/Semantic Kernel según patrón.
- Observabilidad/evaluación: LangFuse/Phoenix (trazas, calidad, latencia).
- Datos y RAG: PostgreSQL + pgvector/pgai; embeddings y chunking.

Tabla 10. Plan 30–60–90 con tareas, responsables, entregables, métricas
| Fase | Tareas clave                                            | Responsable       | Entregable                           | Métricas clave                  |
|------|---------------------------------------------------------|-------------------|--------------------------------------|---------------------------------|
| A1   | M1self‑hosted; RAG mínimo; 3–5 herramientas             | Líder técnico     | MVP operativo                        | Éxito ≥50%; p95 ≤8 s            |
| A2   | Dual‑run; cache semántico; observabilidad avanzada      | Ingeniería/QA     | Sistema dual estable                 | OPEX ↓≥20%; fallos ↓            |
| A3   | Routing por SLA; seguridad endurecida; escalado         | Arquitectura/SecOps | Producción estable                   | Éxito ≥58–60%; p95 ≤4–6 s       |

Tabla 11. KPIs y umbrales por fase (latencia, calidad, coste, éxito)
| KPI                    | A1 (MVP)                 | A2 (Dual‑run)            | A3 (Optimizado)           |
|------------------------|--------------------------|--------------------------|---------------------------|
| Éxito de tareas        | ≥50%                     | ≥55%                     | ≥58–60%                   |
| p95 latencia           | ≤8 s                     | ≤6–7 s                   | ≤4–6 s                    |
| Coste por conversación | Dentro de presupuesto    | −20% vs A1               | −25–40% vs A1             |
| CSAT (stakeholder)     | ≥4/5                     | ≥4.2/5                   | ≥4.3/5                    |

Fuentes de mejores prácticas para ejecución y evaluación[^20][^24][^22][^23].

## 10. Anexos

Especificaciones y benchmarks M1/M2, comparativas de precios de tokens (Llama 3 vs M1), modelos OSS alternativos, costos por fase y componentes de stack OSS se consolidan en los anexos para facilitar la reutilización de información técnica y económica.

Tabla 12. Benchmarks M1/M2: SWE‑bench, TAU‑bench, MRCR/LongBench‑v2
| Benchmark                 | M1 (40k) | M1 (80k) | M2 (nota de diseño)        |
|---------------------------|----------|----------|----------------------------|
| SWE‑bench Verified        | 55.6%    | 56.0%    | N/A (objetivo: menor latencia) |
| TAU‑bench (airline/retail)| 60–67%   | 62–67%   | Optimizado para throughput |
| MRCR 128k / 1M            | 76–58    | 73–56    | N/A                        |
| LongBench‑v2              | ~61      | ~61.5    | N/A                        |

Fuentes: especificaciones y guías públicas[^1][^2][^5].

Tabla 13. Precios por millón de tokens (Llama 3 vs M1)
| Modelo                   | Entrada (por 1M tokens) | Salida (por 1M tokens) | Observación                          |
|--------------------------|-------------------------|-------------------------|--------------------------------------|
| Llama 3 70B Instruct     | $0.30                   | $0.40                   | OSS (según proveedor/plataforma)     |
| MiniMax M1               | $0.40 (0–200k)          | $2.20                   | Primer nivel más rentable que DeepSeek R1; segundo nivel no comparable |

Fuentes: comparativas publicadas[^8][^1].

Tabla 14. Estimaciones de costos por fase (desarrollo, integración, operación)
| Fase             | Desarrollo inicial | Integración (herramientas/DevOps) | Operación mensual (rango)        |
|------------------|--------------------|------------------------------------|-----------------------------------|
| Descubrimiento   | $10k–$30k          | N/A                                | N/A                               |
| Prototipo A0     | $20k–$60k          | $10k–$25k                          | $2k–$6k                           |
| Beta A1          | $40k–$100k         | $20k–$40k                          | $3.2k–$13k                        |
| Producción A2    | $60k–$150k         | $30k–$60k                          | Ajustado por tráfico y SLA        |

Fuente: rangos comparativos y factores de costo[^16].

Tabla 15. Componentes del stack OSS y roles
| Componente        | Rol en la solución                            |
|-------------------|-----------------------------------------------|
| Llama/Qwen/Mistral/Gemma | LLM base y degradación                    |
| SBERT/BGE/Nomic   | Embeddings para RAG                           |
| pgvector/pgai     | Vectorización y búsqueda semántica            |
| LangChain/AutoGen/Semantic Kernel | Orquestación y mensajería        |
| LangFuse/Phoenix  | Observabilidad y evaluación                   |

Fuente: stack OSS emergente[^15][^19][^21][^10][^11][^12].

Información pendiente (gaps): detalle del stack “MiniMax Agent” (orquestación, herramientas, memoria), benchmarks internos específicos del dominio, precios y SLAs de M2 más allá de notas públicas, restricciones de licencia de modelos OSS (uso comercial), volúmenes y patrones de tráfico, requisitos regulatorios internos, y estrategia de migración de datos. Se recabarán en el descubrimiento (Semana 1) y se incorporarán a la arquitectura y al plan de riesgos.

---

## Referencias

[^1]: MiniMax‑M1: The First Open‑Weight Hybrid‑Attention Inference Model. https://www.minimax.io/news/minimaxm1  
[^2]: MiniMax‑M1 GitHub (specs, benchmarks y guías). https://github.com/MiniMax-AI/MiniMax-M1  
[^3]: vLLM Documentation (despliegue y compatibilidad). https://docs.vllm.ai/en/latest/  
[^4]: MiniMaxAI/MiniMax‑M2 (Hugging Face). https://huggingface.co/MiniMaxAI/MiniMax-M2  
[^5]: MiniMax M2 & Agent: Ingenious in Simplicity. https://www.minimax.io/news/minimax-m2  
[^6]: Top 10 open source LLMs for 2025 (NetApp Instaclustr). https://www.instaclustr.com/education/open-source-ai/top-10-open-source-llms-for-2025/  
[^8]: Llama 3 70B Instruct vs MiniMax M1 – Comparative Analysis (Galaxy.ai). https://blog.galaxy.ai/compare/llama-3-70b-instruct-vs-minimax-m1  
[^10]: Top 7 Free AI Agent Frameworks [2025] (Botpress). https://botpress.com/blog/ai-agent-frameworks  
[^11]: LangChain (GitHub). https://github.com/hwchase17/langchain  
[^12]: Rasa (GitHub). https://github.com/RasaHQ/rasa  
[^14]: Haystack (GitHub). https://github.com/deepset-ai/haystack  
[^15]: The Emerging Open‑Source AI Stack (TigerData). https://www.tigerdata.com/blog/the-emerging-open-source-ai-stack  
[^16]: AI Agent Development Cost: Full Breakdown for 2025 (Azilen). https://www.azilen.com/blog/ai-agent-development-cost/  
[^19]: pgvector (GitHub). https://github.com/pgvector/pgvector  
[^20]: FastAPI (documentación oficial). https://fastapi.tiangolo.com  
[^21]: pgai (GitHub). https://github.com/timescale/pgai  
[^22]: LangFuse (observabilidad de LLMs). https://langfuse.com  
[^23]: Phoenix (Arize AI) – Observabilidad/evaluación. https://github.com/Arize-ai/phoenix  
[^24]: McKinsey – The State of AI (Early 2024). https://www.mckinsey.com/~/media/mckinsey/business%20functions/quantumblack/our%20insights/the%20state%20of%20ai/2024/the-state-of-ai-in-early-2024-final.pdf  
[^25]: Llama (Meta) – Sitio oficial. https://www.llama.com  
[^26]: Top 5 Open‑Source AI Agent Alternatives to Manus AI in 2025 (Simular AI). https://www.simular.ai/post/top-5-open-source-ai-agent-alternatives-to-manus-ai-in-2025