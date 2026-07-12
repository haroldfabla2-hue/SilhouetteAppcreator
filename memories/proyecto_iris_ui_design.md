# Diseño UI del Agente IRIS

## Estado Actual
- **Tarea**: Diseñar interfaz completa SPA para agente IRIS
- **Estilo elegido**: Modern Minimalism Premium + Tech Dashboard
- **Fecha**: 2025-11-05

## Funcionalidades Requeridas
1. Dashboard principal (métricas MCP Server en tiempo real)
2. Sistema de chat conversacional (streaming, múltiples conversaciones)
3. Gestión de proyectos (crear, organizar, subir archivos)
4. Editor de código tipo VS Code (Monaco, LSP, terminal)
5. Canvas interactivo (similar a Gemini Canvas)
6. Gestión de archivos (drag & drop, versionado)
7. Sistema de templates
8. Configuración y notificaciones
9. Gestión inteligente de contexto

## Investigaciones Disponibles
- UI trends 2024-2025 (streaming, GenUI, multimodal)
- Análisis UI: Gemini, ChatGPT, Claude, MiniMax
- Editores código web: Monaco, CodeMirror, LSP
- Gestión contexto: RAG, chunking, memoria
- Patrones proyectos múltiples

## Archivos Generados ✅
1. ✅ Content Structure Plan (`docs/content-structure-plan.md`)
   - 9 vistas principales mapeadas
   - Componentes y patrones por sección
   - Arquitectura de navegación SPA
   
2. ✅ Design Specification (`docs/design-specification.md`)
   - Sistema de colores validado WCAG
   - Tipografía completa (Inter)
   - 6 componentes principales especificados
   - Layout responsive y animaciones
   - 866 líneas de especificaciones
   
3. ✅ Design Tokens JSON (`docs/design-tokens.json`)
   - Formato W3C estándar
   - 264 líneas de tokens
   - Compatible con Tailwind/CSS Variables
   
## Decisiones Clave de Diseño
- Paleta: Cool Gray + Modern Blue (#0066FF)
- Espaciado: 8pt grid, generoso (48-96px sections)
- Radius: 12-16px (moderno, suave)
- Animación: 200-300ms, ease-out
- Editor: Monaco con tema One Dark Pro
- Chat: Streaming con indicadores visuales
- Contexto: Panel lateral con token meter
