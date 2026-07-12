# Content Structure Plan - Agente IRIS

## 1. Inventario de Materiales

**Archivos de Investigación:**
- `docs/ui_trends_ai_assistants_2025.md` (45,000+ palabras, tendencias UI/UX)
- `docs/ui_analysis_gemini.md` (15,000+ palabras, análisis Gemini)
- `docs/ui_analysis_chatgpt.md` (18,000+ palabras, análisis ChatGPT)
- `docs/ui_analysis_claude.md` (análisis Claude)
- `docs/ui_analysis_minimax_agent.md` (análisis MiniMax)
- `docs/ai_context_management/context_optimization_strategies.md` (25,000+ palabras)
- `docs/ai_context_management/project_conversation_patterns.md` (22,000+ palabras)
- `docs/ai_context_management/web_code_editors_analysis.md` (28,000+ palabras)
- `docs/investigacion_completa_minimax_agent_iris.md` (capacidades IRIS)

**Assets Visuales:**
- Ningún asset visual previo (se crearán según el diseño)

**Datos Dinámicos (API/Backend):**
- Métricas MCP Server en tiempo real
- Conversaciones y mensajes (streaming)
- Proyectos y archivos del usuario
- Configuraciones y preferencias
- Templates predefinidos
- Historial de actividad

## 2. Estructura de la Aplicación

**Tipo:** SPA (Single Page Application)

**Razonamiento:** La naturaleza de IRIS requiere:
- Cambio fluido entre contextos (proyectos, conversaciones, editor)
- Estado compartido entre múltiples vistas (contexto activo, archivos abiertos)
- Interacciones en tiempo real (streaming de respuestas, métricas en vivo)
- Editor de código integrado con terminal y preview
- Navegación rápida sin recargas de página
- Gestión compleja de estado (múltiples conversaciones, proyectos)

## 3. Estructura de Vistas/Secciones

### Vista 1: Dashboard Principal (`/`)

**Propósito:** Centro de control y métricas del sistema

**Componentes y Patrones:**

| Sección | Component Pattern | Data Source | Content/Funcionalidad | Visual Asset |
|---------|------------------|-------------|----------------------|--------------|
| Header Global | Top App Bar | - | Logo, búsqueda global, notificaciones, perfil | Logo IRIS |
| Sidebar de Navegación | Navigation Rail | - | Dashboard, Proyectos, Chat, Editor, Templates, Config | Iconos SVG |
| Métricas en Tiempo Real | Data Card Grid (4 cards) | API MCP Server | Tokens usados/disponibles, Proyectos activos, Conversaciones activas, Rendimiento | - |
| Actividad Reciente | Timeline/Feed | API actividad | Últimas 10 acciones del usuario | - |
| Proyectos Destacados | Card Grid (3 cols) | API proyectos | Proyectos con más actividad reciente | - |
| Quick Actions | Action Button Group | - | Nuevo proyecto, Nueva conversación, Nuevo archivo | - |

---

### Vista 2: Gestión de Proyectos (`/projects`)

**Propósito:** Organizar y administrar proyectos

**Componentes y Patrones:**

| Sección | Component Pattern | Data Source | Content/Funcionalidad | Visual Asset |
|---------|------------------|-------------|----------------------|--------------|
| Header de Proyectos | Page Header | - | Título "Proyectos", botón "Nuevo Proyecto", búsqueda | - |
| Lista de Proyectos | Card Grid (responsive) | API proyectos | Nombre, descripción, última actividad, # archivos, # conversaciones | - |
| Vista Detalle Proyecto | Sidebar + Main Content | API proyecto/:id | Archivos del proyecto, conversaciones, configuraciones, miembros | - |
| Árbol de Archivos | Tree View | API archivos | Estructura jerárquica de archivos y carpetas | Iconos por tipo |
| Drag & Drop Zone | File Upload Component | - | Subir archivos y carpetas | - |
| Filtros y Ordenamiento | Filter Bar | - | Por fecha, tipo, tamaño, actividad | - |

---

### Vista 3: Sistema de Chat (`/chat`)

**Propósito:** Interfaz conversacional con IA

**Componentes y Patrones:**

| Sección | Component Pattern | Data Source | Content/Funcionalidad | Visual Asset |
|---------|------------------|-------------|----------------------|--------------|
| Lista de Conversaciones | Sidebar List | API conversaciones | Historial de conversaciones por proyecto | - |
| Área de Mensajes | Message Feed (streaming) | API mensajes | Burbujas de usuario/asistente, streaming en tiempo real | - |
| Input de Chat | Message Input Bar | - | Textarea con auto-resize, botones voz/adjuntos | Iconos SVG |
| Indicadores de Contexto | Context Chips | API contexto | Archivos activos, instrucciones, tokens usados | - |
| Panel de Contexto | Collapsible Panel | API contexto | Visualización detallada de contexto activo | - |
| Sugerencias de Seguimiento | Suggestion Chips | API sugerencias | "Siguiente paso" sugerido por IA | - |
| Estado de Streaming | Loading Indicator | - | Indicador "escribiendo..." con animación | - |

---

### Vista 4: Editor de Código (`/editor`)

**Propósito:** IDE completo en el navegador

**Componentes y Patrones:**

| Sección | Component Pattern | Data Source | Content/Funcionalidad | Visual Asset |
|---------|------------------|-------------|----------------------|--------------|
| Explorador de Archivos | Tree View Sidebar | API archivos | Navegación de archivos del proyecto activo | Iconos por tipo |
| Editor Monaco | Monaco Editor | Archivo activo | Edición de código con syntax highlighting, IntelliSense | - |
| Tabs de Archivos | Tab Bar | Archivos abiertos | Pestañas de archivos abiertos con indicadores de cambios | - |
| Terminal Integrado | Terminal Panel (xterm.js) | WebSocket pty | Terminal bash/shell interactivo | - |
| Panel de Preview | Preview Frame | - | Live preview de aplicaciones web | - |
| LSP Indicators | Status Bar | LSP server | Errores, warnings, sugerencias del LSP | Iconos SVG |
| AI Inline Completions | Inline Suggestion Overlay | API AI | Sugerencias de código IA con streaming | - |

---

### Vista 5: Canvas Interactivo (`/canvas`)

**Propósito:** Workspace visual para iteración con IA

**Componentes y Patrones:**

| Sección | Component Pattern | Data Source | Content/Funcionalidad | Visual Asset |
|---------|------------------|-------------|----------------------|--------------|
| Canvas Principal | Rich Text/Code Editor | Canvas activo | Edición de texto o código con IA | - |
| Toolbar de Acciones | Action Toolbar | - | Ajustar longitud, tono, depurar, traducir, etc. | Iconos SVG |
| Chat Lateral | Sidebar Chat | API canvas chat | Chat contextual del canvas actual | - |
| Versionado | Version Timeline | API versiones | Historial de versiones con restauración | - |
| Preview Mode | Split View | - | Vista previa en tiempo real del contenido | - |
| Export Options | Modal Dialog | - | Exportar a PDF, Markdown, HTML, etc. | - |

---

### Vista 6: Gestión de Archivos (`/files`)

**Propósito:** Administración centralizada de archivos

**Componentes y Patrones:**

| Sección | Component Pattern | Data Source | Content/Funcionalidad | Visual Asset |
|---------|------------------|-------------|----------------------|--------------|
| Vista de Galería | Grid/List Toggle | API archivos | Vista de archivos con miniaturas o lista | Miniaturas |
| Upload Zone | Drag & Drop Area | - | Subir archivos y carpetas con drag & drop | Icono upload |
| Filtros Avanzados | Filter Sidebar | - | Por tipo, proyecto, fecha, tamaño, tags | - |
| Sincronización | Sync Status Bar | API sync | Estado de sincronización entre conversaciones | Icono sync |
| Versionado de Archivos | Version History Panel | API versiones | Ver y restaurar versiones anteriores | - |
| Acciones en Batch | Bulk Action Toolbar | - | Mover, copiar, eliminar múltiples archivos | - |

---

### Vista 7: Sistema de Templates (`/templates`)

**Propósito:** Plantillas predefinidas y personalizadas

**Componentes y Patrones:**

| Sección | Component Pattern | Data Source | Content/Funcionalidad | Visual Asset |
|---------|------------------|-------------|----------------------|--------------|
| Galería de Templates | Card Grid | API templates | Templates predefinidos y del usuario | Previews |
| Categorías | Category Tabs | - | Por tipo: Código, Documentos, Proyectos, Prompts | - |
| Vista Previa | Modal Preview | Template seleccionado | Preview del template con detalles | - |
| Editor de Template | Form Editor | Template activo | Crear/editar templates personalizados | - |
| Variables y Parámetros | Form Fields | - | Definir variables del template | - |
| Acciones | Action Buttons | - | Usar template, Editar, Duplicar, Eliminar | - |

---

### Vista 8: Configuración (`/settings`)

**Propósito:** Configuración del usuario y del sistema

**Componentes y Patrones:**

| Sección | Component Pattern | Data Source | Content/Funcionalidad | Visual Asset |
|---------|------------------|-------------|----------------------|--------------|
| Navegación de Configuración | Settings Sidebar | - | General, Proyectos, API Keys, Notificaciones, Privacidad | - |
| Panel General | Settings Panel | API user | Perfil, tema, idioma, preferencias | Avatar usuario |
| API Keys | Secure Input Fields | API keys | Gestión de API keys de OpenAI, Anthropic, etc. | Iconos providers |
| Configuración de Proyectos | Project Settings Panel | API config | Instrucciones por defecto, modelos, límites | - |
| Notificaciones | Notification Preferences | API notif | Canales y tipos de notificaciones | - |
| Privacidad y Datos | Privacy Controls | API privacy | Retención, derecho al olvido, exportar datos | - |

---

### Vista 9: Sistema de Notificaciones

**Propósito:** Centro de notificaciones y alertas

**Componentes y Patrones:**

| Sección | Component Pattern | Data Source | Content/Funcionalidad | Visual Asset |
|---------|------------------|-------------|----------------------|--------------|
| Panel de Notificaciones | Dropdown Panel | API notificaciones | Lista de notificaciones recientes | - |
| Toast Notifications | Toast Component | Eventos en tiempo real | Notificaciones temporales no intrusivas | - |
| Indicador de Badge | Badge Counter | API count | Contador de notificaciones no leídas | - |
| Tipos de Notificaciones | Categorized List | - | Por tipo: Sistema, Proyectos, Conversaciones, Alertas | Iconos SVG |
| Acciones Rápidas | Inline Actions | - | Marcar como leída, ir al contexto, descartar | - |

---

## 4. Navegación y Arquitectura de Información

**Patrón de Navegación:** Sidebar principal persistente + contenido dinámico

**Jerarquía:**
```
App Shell
├── Global Header (búsqueda, notificaciones, perfil)
├── Sidebar de Navegación (siempre visible)
│   ├── Dashboard
│   ├── Proyectos
│   ├── Chat
│   ├── Editor
│   ├── Canvas
│   ├── Archivos
│   ├── Templates
│   └── Configuración
└── Área de Contenido Principal (cambia según ruta)
    └── Paneles contextuales (según vista activa)
```

**Gestión de Estado:**
- Proyecto activo global
- Conversación activa global
- Archivos abiertos en editor
- Contexto de IA activo
- Preferencias de usuario
- Estado de sincronización

**Navegación entre Contextos:**
- Breadcrumbs para ubicación en jerarquía
- Tabs para elementos abiertos simultáneamente
- Búsqueda global con resultados por tipo
- Atajos de teclado para navegación rápida
- Historial de navegación (back/forward)

## 5. Análisis de Contenido

**Densidad de Información:** Alta

La aplicación maneja múltiples capas de información simultáneamente:
- Estado en tiempo real (métricas, streaming)
- Estructura jerárquica (proyectos, archivos, conversaciones)
- Datos complejos (código, contexto de IA, versionado)
- Interacciones multimodales (texto, voz, archivos)

**Balance de Contenido:**
- **Datos Dinámicos:** 70% (API, tiempo real, streaming)
- **Visualización de Estado:** 20% (indicadores, badges, barras de progreso)
- **Contenido Estático:** 10% (labels, instrucciones, ayuda)

**Tipo de Contenido:** Aplicación orientada a datos y acciones

**Complejidad Funcional:** Muy alta
- Múltiples flujos de trabajo simultáneos
- Gestión de contexto compleja
- Sincronización en tiempo real
- Integración de editor de código completo
- Sistema de IA con streaming y sugerencias

**Implicaciones de Diseño:**
- Necesidad de jerarquía visual clara y consistente
- Indicadores de estado omnipresentes pero no intrusivos
- Patrones de carga y streaming bien definidos
- Feedback inmediato en todas las acciones
- Gestión de errores granular y contextual
- Performance crítico (virtualización, lazy loading)
- Accesibilidad en componentes dinámicos (ARIA live regions)
