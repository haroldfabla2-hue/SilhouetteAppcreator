# Interfaz y experiencia de usuario de Claude (Anthropic): blueprint analítico

## Resumen ejecutivo

Claude articula una interfaz conversacional purposely minimalista que prioriza la concentración del usuario en la tarea, con una distribución en dos paneles: un área de chat centrada y un panel lateral (sidebar) para navegación e inspección rápida. Sobre este armazón, Claude introduce dos capacidades estructurales que amplían su alcance: Projects, como espacio compartido de conocimiento para equipos, y Artifacts, una ventana dedicada para crear, visualizar y compartir artefactos con estado y control de permisos. La combinación habilita un flujo de colaboración asíncrona, con instrucciones por proyecto y estados persistentes que sustentan tanto el trabajo iterativo como el handover efectivo entre miembros[^1][^2][^3][^4].

Desde la comparación de mercado, Claude se diferencia en cuatro vectores: una ventana de contexto muy amplia (hasta 200K tokens en Claude 3.5 Sonnet) apta para documentos extensos, una visión “Artifacts-first” que separa creación y conversación, Projects con permisos y base de conocimiento ampliada vía RAG, y una narrativa de privacidad y uso empresarial que evita saturar la interfaz con controles visibles, mostrando solo lo necesario en cada momento[^1][^8][^13][^17]. El resultado es una experiencia percibida como limpia, coherente y menos vistosa que la de algunos competidores, en favor de la concentración y la progresive disclosure de funciones complejas[^1].

Para organizaciones que valoran el contexto largo, la colaboración basada en conocimiento compartido y la separación entre conversación y producción de artefactos (p. ej., código, mini‑apps, diagramas), Claude ofrece una propuesta sólida. El trade‑off es doble: la minimalidad reduce el peso cognitivo, pero exige una curaduría interna para mantener la consistencia de Projects y una disciplina de versionado/estado en Artifacts. Adicionalmente, la ausencia de un sandbox de ejecución integrado en el chat y la falta de una guía pública exhaustiva del sistema de diseño invitan a robustecer la documentación de patrones internos y a adoptar estándares formales de accesibilidad[^1][^2][^3][^10][^11][^15].

## Metodología, alcance y fuentes

Este análisis se basa en: a) documentación oficial de Anthropic (producto, centro de ayuda y especificaciones funcionales); b) comparativas independientes de interfaces conversacionales que incluyen a Claude; c) fuentes de accesibilidad públicas, incluyendo pautas WCAG; y d) materiales de marca y diseño asociados a Anthropic. Se priorizan fuentes verificables, actualizadas y con foco explícito en UI/UX de Claude[^1][^2][^3][^4][^5][^7][^8][^9][^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^20][^21][^22][^23][^24].

Limitaciones del corpus: no existe una guía pública integral del sistema de diseño de la interfaz de Claude; faltan métricas formales de cumplimiento de accesibilidad (más allá de la existencia de VPAT bajo NDA); y la especificación técnica del manejo de archivos y límites por plan no está publicada de forma exhaustiva. Por ello, algunas inferencias visuales se apoyan en comparativas y materiales de branding de Anthropic[^14]. Línea temporal base: 5 de noviembre de 2025.

## Arquitectura de información y layout general

Claude adopta un layout de chat limpio con un sidebar persistente que lista conversaciones recientes y acceso rápido a Projects. La interfaz privilegia el foco en la conversación y aplica divulgación progresiva: funciones avanzadas (p. ej., selección de modos, Artifacts, búsqueda web) emergen solo cuando son necesarias, evitando saturar el plano principal[^1][^4][^5]. En web, un panel derecho puede alojar Artifacts; en móvil y escritorio, los principios se mantienen con reorganización adaptativa del contenido[^1][^21].

Para ilustrar la identidad visual en contexto, se presenta un detalle de interfaz que acompaña el posicionamiento de marca:

![Identidad visual y UI de Claude (captura del sistema de marca de Anthropic)](assets/images/claude_ui_overview.jpg)

Más allá de lo cosmético, esta estética traduce la promesa de seguridad y precisión en patrones de interacción mesurados, con densidad informativa controlada y estados visibles sin estridencias[^14][^22].

### Mapa de layout: navegación, chat, sidebar

La navegación superior consolida acciones globales (nuevo chat, acceso a Projects y Artifacts, configuración, búsqueda web). El sidebar facilita la continuidad: listar, renombrar y fijar conversaciones recientes, con tránsito fluido a Projects para organizar conocimiento compartido. El área de chat concentra la interacción usuario‑modelo, con controles en línea (copiar código, seleccionar artefacto a editar) y accesos contextuales a Artifacts cuando el contenido lo amerita[^1][^4][^5][^6].

![Esquema del layout (chat principal, sidebar, panel de Artifacts)](assets/images/claude_layout_map.png)

Esta disposición reduce el “salto cognitivo” entre acciones: el usuario permanece en el mismo plano visual mientras crea un artifact, alterna su versión o consulta la base de conocimiento del proyecto. En conjunto, prioriza foco y continuidad.

### Comparativa de layout: Claude vs competidores

Para situar a Claude en el panorama, la siguiente tabla sintetiza decisiones de layout y su impacto en el foco y la productividad.

| Herramienta | Chat principal | Sidebar | Paneles adicionales | Implicación en foco/productividad |
|---|---|---|---|---|
| ChatGPT | Chat minimalista | Historial colapsable | Canvas (pizarra visual), herramientas de análisis | Foco alto; Canvas añade capa visual opcional[^1] |
| Gemini | Chat Material | Historial + memoria | Integración Workspace | Contexto fuerte; puede dispersar atención por integraciones[^1] |
| Claude | Chat minimalista | Historial + Projects | Artifacts (panel derecho) | Foco y producción separada; iteración guiada por versiones[^1] |
| Poe | Chat + selector de bots | Historial por modelo | Multi‑bot side‑by‑side | Comparación ágil; mayor carga visual[^1] |
| LeChat | Chat directo | Historial mínimo | — | Bajo peso visual; funciones aún en evolución[^1] |
| DeepSeek | Chat + alternadores | Historial básico | Cadena de pensamiento visible | Transparencia educativa; posible distracción[^1] |

Claude se posiciona en el cuadrante foco/producción: evita dispersar la conversación y ofrece un espacio de trabajo paralelo cuando el contenido alcanza densidad propia.

## Funcionalidades de chat

El manejo de mensajes en Claude sigue un patrón familiar (regenerar, editar, copiar), al que se suman controles para tratar respuestas largas mediante vistas de esquema y la capacidad de alternar el foco entre múltiples Artifacts dentro de una misma conversación[^1][^2][^15]. El tratamiento de código es legible y orientado a la acción: resaltado de sintaxis, tablas en Markdown y botones de copia; no hay un sandbox de ejecución integrado en el chat, lo que desplaza tareas de run/execute a Artifacts u otros entornos[^1][^2].

![Ejemplo de bloque de código con acciones de copia](assets/images/claude_code_block.png)

En archivos, Claude admite cargas múltiples y, con Projects, introduce una base de conocimiento ampliable por RAG para elevar la precisión contextual. La creación/edición de archivos (documentos, hojas de cálculo, presentaciones, PDFs) se canaliza a través de Artifacts, donde el contenido se trata como entidades persistentes con versiones y opciones de exportación[^3][^7][^17][^20]. Esta separación favorece la trazabilidad y la colaboración asíncrona sin perder la continuidad del diálogo.

Para situar la amplitud funcional y su madurez relativa, el cuadro siguiente sintetiza capacidades y límites de la interfaz:

| Capacidad | Estado en Claude (web/desktop/móvil) | Madurez | Notas/Limitaciones |
|---|---|---|---|
| Regen/editar mensajes | Disponible en chat | Alta | Patrón estándar; iteración guiada por edición de prompts[^1] |
| Vista de esquema (largas respuestas) | Disponible | Media‑Alta | Manejo de salidas extensas sin perder el hilo[^1] |
| Resaltado de sintaxis | Disponible | Alta | Código legible con botones de copia[^1][^2] |
| Tablas Markdown | Disponible | Alta | Composición rápida de estructuras tabulares[^1] |
| Cargas múltiples de archivos | Disponible | Media‑Alta | Soporta múltiples adjuntos por turno[^1] |
| Projects + RAG | Disponible (Pro/Team/Enterprise) | Media | Conocimiento ampliable con RAG; permisos por proyecto[^7][^20] |
| Crear/editar archivos (docs, Excel, PPT, PDF) | En Artifacts | Media | “Create/edit files” canalizado vía Artifacts[^3] |
| Análisis de datos/Python | Anunciado como mejorado | Emergente | Revelado incremental; sin sandbox en chat[^1][^19] |
| Modo voz (móvil) | Disponible | Media | Entrada/salida de voz y resúmenes[^13][^21] |

El énfasis está en “producir fuera del chat” cuando el contenido cobra entidad propia, reservando el chat para ideación, coordinación e instrucciones.

## Características distintivas de Claude

Projects transforma el historial disperso en conocimiento compartido con instrucciones personalizadas y escalamiento RAG, adecuado para equipos que trabajan sobre corpus estables. Artifacts ofrece una ventana de trabajo separada con persistencia de estado, versionado y opciones de exportación/compartición segura; admite incluso “apps con IA” integradas y conexiones a servicios externos vía permisos granulares MCP. La “Analysis tool” y la capacidad de editar mensajes anteriores para ramificar el historial de chat añaden flexibilidad sin perder trazabilidad[^2][^3][^4][^17].

![Flujo de trabajo con Artifacts (crear, editar, alternar versiones)](assets/images/claude_artifacts_panel.png)

Esta separación conceptual entre conversación y producción reduce el acoplamiento: el diálogo guía, los artefactos materializan. Para equipos, el control de permisos y el aislamiento de datos por proyecto hacen viable el trabajo concurrente con garantías de gobernanza[^3][^4][^20].

### Projects: colaboración y escalabilidad del conocimiento

Projects habilita un “espacio de trabajo con memoria” donde los miembros pueden utilizar o editar instrucciones y base de conocimiento. Los permisos se articulan por roles (“puede usar”, “puede editar”), con opciones de compartición individual, masiva u organizacional, y un flujo de notificaciones por correo. La escalabilidad vía RAG permite ampliar la capacidad efectiva de contexto sin sacrificar precisión, manteniendo la calidad de las respuestas incluso cuando el volumen se aproxima a los límites de la ventana de contexto[^4][^20].

Para clarificar responsabilidades, el cuadro siguiente resume permisos y acciones:

| Permiso | Acciones habilitadas | Casos de uso |
|---|---|---|
| Puede usar | Ver conocimiento e instrucciones; chatear dentro del proyecto | Consumo y ejecución táctica |
| Puede editar | Modificar instrucciones/knowledge; añadir/eliminar miembros; actualizar configuración | Coordinación de conocimiento y gobierno |
| Creador | Ajustar visibilidad y compartir con individuos o toda la organización | Alta dirección y operación editorial[^4] |

### Artifacts: producción y visualización de artefactos

Artifacts aplica criterios de creación claros (contenido autónomo y sustancial), ofrece edición iterativa guiada por conversación, versionado y opciones de exportación (copiar, descargar). Su diseño soporta múltiples artifacts en paralelo, con control de cuál actualizar a través de un selector dedicado. El almacenamiento persistente puede ser personal o compartido, con confirmación explícita en el primer acceso a datos compartidos. Además, los artifacts pueden incorporar capacidades de IA y conectarse a herramientas externas bajo permisos granulares MCP[^2][^17].

La siguiente tabla sintetiza criterios y límites:

| Aspecto | Especificación | Implicación UX |
|---|---|---|
| Criterios de creación | Contenido autónomo y sustancial (típicamente >15 líneas) | Favorece separación chat/artefacto[^2] |
| Edición | Iteración por lenguaje natural con espejo en la ventana del artefacto | Feedback inmediato y trazabilidad[^2][^15] |
| Versionado | Alternar versiones del artefacto | Control de regresiones y exploración de alternativas[^2] |
| Exportación | Copiar y descargar | Handoff sin fricción a otros entornos[^2] |
| Límite de almacenamiento | 20 MB por artefacto (solo texto) | Enfatiza contenido textual; sin blobs[^2] |
| Persistencia | Personal o compartida con confirmación | Clarifica gobernanza de datos[^2][^17] |
| Integraciones | Permisos MCP granulares | Seguridad y menor superficie de riesgo[^2][^17] |

## Elementos visuales (branding, tipografía, color, iconos, movimiento)

La identidad visual de Anthropic, desarrollada con Geist, prioriza una imagen sobria y confiable, con acentos que aportan calidez sin distraer. Esta estética influye en la UI de Claude, que se percibe limpia y neutral, con jerarquías claras y animaciones sobrias que refuerzan estados sin generar ruido[^14][^23]. El patrón cromático y tipográfico no está publicado exhaustivamente para la UI de Claude, por lo que se infiere consistencia con la marca Anthropic y con las propiedades generales reportadas por análisis de terceros, incluyendo la mención de acentos morados en la interfaz[^1][^14].

![Muestras de paleta y tipografía de Anthropic (Geist)](assets/images/anthropic_color_palette.png)

En movimiento, la interfaz recurre a transiciones suaves y estados de “pensamiento” moderados, coherentes con un posicionamiento de seguridad y precisión. Para código, la legibilidad del resaltado y una tipografía monoespaciada adecuada son elementos constantes, con copy‑to‑clipboard como affordance principal[^1][^2].

![Ejemplo de UI con acentos y estilo sobrio](assets/images/anthropic_ui_example.jpg)

### Accesibilidad y tono visual

La accesibilidad en la UI de Claude debe evaluarse frente a criterios WCAG, particularmente operabilidad por teclado (Success Criterion 2.1.1), foco visible y contraste suficiente. La pauta 2.1.1 exige que toda la funcionalidad sea operable mediante teclado sin temporizaciones exigentes de pulsación. La existencia de un VPAT bajo NDA indica proceso, pero no sustituye pruebas propias ni garantiza conformidad total en todos los flujos. Por ello, se recomiendan auditorías regulares con lectores de pantalla, verificación de focus traps y aseguramiento de estados ARIA apropiados[^10][^11].

## Experiencia de usuario (workflow, accesibilidad, responsive, seguridad)

La experiencia se articula en torno a tareas recurrentes: ideación y drafting en el chat; creación de artifacts cuando el contenido alcanza entidad propia; y trabajo de equipo en Projects, donde las instrucciones y el conocimiento compartido guían respuestas y decisiones. Esta secuencia reduce la fricción entre exploración y producción, y habilita un handoff claro entre etapas y personas[^2][^4].

![Flujo típico: chat → artifact → colaboración en Projects](assets/images/claude_workflow_diagram.png)

En accesibilidad, los retos incluyen la operabilidad integral por teclado, la comunicación de estados del sistema de forma accesible y la retroalimentación sensorial suficiente. Los riesgos más citados por la comunidad se relacionan con compatibilidad de lectores de pantalla en ciertos flujos; mitigarlos requiere pruebas con NVDA/VoiceOver, verificaciones de focus management y etiquetado semántico consistente[^10][^11]. En responsive, los principios de web se trasladan a móvil/escritorio con ajustes de densidad, visibilidad del sidebar y disposición del panel de artifacts; el modo voz en móvil añade un canal natural para iniciación y resumen de tareas[^13][^21]. En seguridad/privacidad, el enfoque empresarial de Projects refuerza control de permisos y uso de RAG; la compartición segura de artifacts y permisos MCP apuntalan la gobernanza de datos a nivel de aplicación[^2][^4][^20].

Para operativizar la evaluación de accesibilidad, se propone el siguiente checklist:

| Criterio WCAG (ejemplos) | Estado en Claude (observado/esperado) | Evidencia/Fuente | Riesgo | Recomendación |
|---|---|---|---|---|
| SC 2.1.1 Teclado | Debe ser totalmente operable | WCAG 2.1.1; VPAT bajo NDA | Alto | Auditorías con teclado puro; corrección de focus traps[^10][^11] |
| Foco visible | Esperable por diseño minimalista | Prácticas estándar | Medio | Validar contraste de indicadores y persistencia |
| Contraste de texto | Esperable conforme | Comparativas generales | Medio | Pruebas automáticas y manuales por tema |
| Lectores de pantalla | Riesgo puntual reportado | Comunidad | Medio‑Alto | Pruebas con NVDA/VoiceOver; etiquetado ARIA |
| Estados y feedback | Presente pero sobrio | Observación de UI | Medio | Señales adicionales no intrusivas para eventos clave |

## Comparativa con ChatGPT y Gemini (foco en UI/UX)

Claude, ChatGPT y Gemini comparten un núcleo conversacional con sidebar, pero difieren en la forma de materializar trabajo y en el tratamiento del contexto largo. ChatGPT incorpora Canvas como pizarra visual y un ecosistema de extensiones/GPTs; Gemini se apalanca en la suite Workspace y funciones como Deep Research y ejecución de Python en chat. Claude prioriza Projects y Artifacts como columna vertebral del trabajo reproducible y compartido, con una ventana de contexto amplia y una separación estricta entre diálogo y artefacto[^1][^12][^13].

| Dimensión | Claude | ChatGPT | Gemini |
|---|---|---|---|
| Layout base | Chat + sidebar + Artifacts | Chat + sidebar + Canvas | Chat + Material + integraciones |
| Contexto largo | Hasta 200K tokens (Sonnet) | 8K/32K (Enterprise) | Diseñado para largas entradas (límite no público) |
| Producción de artefactos | Artifacts con versiones y exportación | Canvas (visual) + ADA (análisis) | Ejecución Python + generación de contenidos |
| Colaboración | Projects con permisos y RAG | Team/Enterprise (espacios compartidos) | Workspace (Docs/Drive/Meet) |
| Multimodalidad | Voz en móvil; enfoque texto‑céntrico | Voz, imagen, generación de imágenes | Voz, imagen, video; multilingüe |
| Seguridad/privacidad | Proyectos no entrenan sin consentimiento; MCP | Historial opt‑out; enterprise controls | Datos Workspace no entrenan; controles admin[^1][^12][^13][^18] |

La elección depende del equilibrio deseado entre foco y ecosistema: Claude favorece una producción separada, gobernada por proyectos y artefactos; ChatGPT ofrece una pizarra creativa y marketplace; Gemini integra productividad documental y multicloud.

## Recomendaciones estratégicas y oportunidades

- Profundizar en patrones de Projects: consolidar plantillas de instrucciones por dominio, catálogos de conocimiento por caso de uso y métricas de impacto (tiempo de onboarding, tasa de adopción, precisión percibida). Diseñar “rutas guiadas” de entrada para nuevos miembros que articulen conocimiento y artefactos desde el primer día[^4][^20].
- Formalizar un Design System para la UI de Claude: tokens de color/espaciado, tipografía, iconografía, estados y motion, con ejemplos de código y casos de borde. Alinear visualmente con la marca Anthropic, pero documentar variaciones específicas de la app para reducir deuda visual[^14][^23].
- Fortalecer accesibilidad y responsive: adoptar WCAG 2.1 AA como objetivo, con foco en operabilidad por teclado y focus management. Establecer un calendario de pruebas con lectores de pantalla y auditorías automáticas; publicar un resumen de accesibilidad con resultados clave[^10][^11].
- Potenciar Artifacts: ofrecer plantillas de artifacts por rol (p. ej., “componente UI”, “PRD”, “data memo”), versionado visual con diffs textuales, y vínculos vivos con Projects (p. ej., “artifact fuente de este requerimiento”). Mejorar el flujo de exportación/handoff (scripts de pre‑commit, checklists)[^2][^17].
- Clarificar multimodalidad y voz: definir una narrativa de estados de voz (idle, listening, processing) y su interacción con Projects/Artifacts; documentar claramente qué análisis/ediciones se habilitan por canal y plan[^13][^21].

## Apéndices

### Glosario

- Projects: espacios de trabajo con historial y base de conocimiento propios, instrucciones personalizadas y permisos de uso/edición para colaboración en equipo y escalamiento vía RAG[^4][^20].
- Artifacts: ventanas dedicadas para contenido autónomo (código, documentos, mini‑apps) con persistencia, versionado, exportación y compartición segura, incluyendo integraciones MCP[^2][^17].
- RAG (Retrieval Augmented Generation): mecanismo para ampliar el contexto efectivo del modelo consultando fuentes internas del proyecto, mejorando precisión y cobertura[^20].
- MCP (Model Context Protocol): sistema de permisos granulares para que artifacts y funciones accedan a herramientas/servicios externos bajo control del usuario[^2][^17].
- Contexto largo: capacidad de la ventana de tokens para procesar documentos extensos en una sola interacción (hasta 200K tokens en Claude 3.5 Sonnet)[^1].

### Checklist de accesibilidad aplicada a la interfaz de Claude

| Criterio | Cómo probarlo | Estado esperado |
|---|---|---|
| Teclado puro (SC 2.1.1) | Navegar sin ratón; ejecutar tareas comunes | Completo y sin trampas de foco[^10] |
| Foco visible | Cambios de foco perceptibles | Consistente en temas claro/oscuro |
| Contraste | Pruebas con herramientas automáticas | AA en textos y componentes |
| Lectores de pantalla | Pruebas con NVDA/VoiceOver | Etiquetado ARIA y orden semántico correctos |
| Estados del sistema | Feedback audible/visual opcional | No exclusivo por color; accesible[^11] |

### Especificaciones clave de Projects y Artifacts

| Función | Especificación | Fuente |
|---|---|---|
| Projects — permisos | Puede usar / Puede editar / Creadores | Help Center[^4] |
| Projects — RAG | Escalamiento del conocimiento (≈10×) | Support[^20] |
| Artifacts — creación | Contenido autónomo y sustancial | Help Center[^2] |
| Artifacts — versiones | Selector de versiones y edición iterativa | Help Center[^2] |
| Artifacts — límites | 20 MB por artifact; solo texto | Help Center[^2] |
| Artifacts — integraciones | Permisos MCP granulares | Support[^17] |
| Modo voz (móvil) | Entrada/salida y resúmenes | VentureBeat; The New Stack[^13][^21] |
| Contexto largo | Hasta 200K tokens (Sonnet) | Anthropic[^1][^8] |
| Crear/editar archivos | En Artifacts (Excel, Word, PPT, PDF) | Anthropic[^3] |

## Referencias

[^1]: Comparing Conversational AI Tool User Interfaces 2025 - IntuitionLabs. https://intuitionlabs.ai/articles/conversational-ai-ui-comparison-2025  
[^2]: Help Center: What are Artifacts and how do I use them? https://support.claude.com/en/articles/9487310-what-are-artifacts-and-how-do-i-use-them  
[^3]: Anthropic: Claude can now create and edit files. https://www.anthropic.com/news/create-files  
[^4]: Help Center: What are projects? https://support.claude.com/en/articles/9517075-what-are-projects  
[^5]: Claude (sitio oficial). https://claude.ai/  
[^6]: Claude Product Overview. https://www.claude.com/product/overview  
[^7]: Anthropic: Collaborate with Claude on Projects. https://www.anthropic.com/news/projects  
[^8]: Introducing Claude 3.5 Sonnet. https://www.anthropic.com/news/claude-3-5-sonnet  
[^9]: Zapier: Claude 4.5 — guía de modelos y chatbot. https://zapier.com/blog/claude-ai/  
[^10]: W3C WAI: Understanding Success Criterion 2.1.1 (Keyboard). https://www.w3.org/WAI/WCAG21/Understanding/keyboard.html  
[^11]: AudioEye: WCAG Guidelines Apply to AI-Generated Content. https://www.audioeye.com/post/wcag-guidelines-ai-generated-content/  
[^12]: Zapier: Claude vs. ChatGPT (2025). https://zapier.com/blog/claude-vs-chatgpt/  
[^13]: VentureBeat: Anthropic debuts conversational voice mode for Claude mobile apps. https://venturebeat.com/ai/anthropic-debuts-conversational-voice-mode-for-claude-mobile-apps/  
[^14]: Geist: Anthropic (Brand & Design System). https://geist.co/work/anthropic  
[^15]: LogRocket: Implementing Claude's Artifacts feature for UI visualization. https://blog.logrocket.com/implementing-claudes-artifacts-feature-ui-visualization/  
[^16]: eWeek: Claude AI Review (2025) — Features, Pros, and Cons. https://www.eweek.com/artificial-intelligence/claude-ai-review/  
[^17]: Anthropic Support: Prototype AI-powered apps with Claude Artifacts. https://support.anthropic.com/en/articles/11649438-prototype-ai-powered-apps-with-claude-artifacts  
[^18]: AWS: Anthropic on Bedrock. https://aws.amazon.com/bedrock/anthropic/  
[^19]: Simon Willison: Claude's new Code Interpreter. https://simonwillison.net/2025/Sep/9/claude-code-interpreter/  
[^20]: Anthropic Support: RAG for Projects. https://support.anthropic.com/en/articles/11473015-retrieval-augmented-generation-rag-for-projects  
[^21]: The New Stack: Anthropic's Claude Code comes to web and mobile. https://thenewstack.io/anthropics-claude-code-comes-to-web-and-mobile/  
[^22]: Anthropic Economic Index: AI's impact on software development. https://www.anthropic.com/research/impact-software-development  
[^23]: Anthropic Logo (SVG). https://geist-studio.files.svdcdn.com/production/assets/anthropic/Anthropic-Logo-16x9.svg  
[^24]: Anthropic Color Palette (SVG). https://geist-studio.files.svdcdn.com/production/assets/anthropic/Anthropic_ColorPalette.svg

---

Nota sobre brechas de información: no se dispone de una guía pública completa del sistema de diseño de la interfaz de Claude, ni de métricas formales de accesibilidad más allá del VPAT bajo NDA; los detalles exhaustivos del manejo de archivos por plan y límites de adjuntos no están publicados de forma completa; la especificación del “Analysis tool” evoluciona de manera incremental; y las políticas de memoria a largo plazo y su configuración en UI no están descritas en detalle[^10][^11][^14].