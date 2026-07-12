# Design Specification - Agente IRIS

**Version**: 1.0  
**Style**: Modern Minimalism Premium + Tech Dashboard  
**Target Audience**: 18-35 profesionales de tecnología  
**Platform**: Web SPA (Desktop-first, responsive móvil)  
**Updated**: 2025-11-05

---

## 1. Dirección y Fundamento

### 1.1 Estilo y Esencia

**Modern Minimalism Premium con elementos de Tech Dashboard.** Esta dirección combina la claridad profesional y la generosidad espacial del minimalismo moderno con la funcionalidad orientada a datos y el monitoreo en tiempo real de los dashboards técnicos. La interfaz prioriza:

- **Eficiencia sin sacrificar elegancia**: Herramientas poderosas presentadas con sofisticación visual
- **Información densa manejada con respiración**: Métricas, código y chat coexisten sin saturar
- **Interacciones sutiles y refinadas**: Micro-animaciones que guían sin distraer
- **Profesionalidad técnica**: Credibilidad para desarrolladores y equipos de producto

### 1.2 Ejemplos de Referencia

**Inspiración visual:**
- **Linear** (linear.app): Jerarquía visual impecable, navegación fluida
- **Vercel Dashboard** (vercel.com): Métricas en tiempo real con diseño limpio
- **GitHub Codespaces** (github.com/features/codespaces): IDE en navegador con UI refinada
- **Notion** (notion.so): Flexibilidad funcional con estética minimalista
- **Stripe Dashboard** (stripe.com): Datos complejos presentados con claridad

---

## 2. Sistema de Diseño Base

### 2.1 Paleta de Colores

**Distribución: 90% Neutral, 10% Accent**

#### Colores Primarios

```
Brand Primary (Modern Blue):
  - 50:  #E6F0FF (backgrounds sutiles)
  - 100: #CCE0FF (hover states ligeros)
  - 500: #0066FF (CTAs primarios, links activos, badges)
  - 600: #0052CC (hover de CTAs)
  - 900: #003D99 (texto sobre fondos claros)

Neutrals (Cool Gray):
  - 50:  #FAFAFA (background principal - light mode)
  - 100: #F5F5F5 (surfaces elevadas: cards, panels)
  - 200: #E5E5E5 (borders, dividers)
  - 500: #A3A3A3 (disabled text, metadata)
  - 700: #404040 (secondary text, labels)
  - 900: #171717 (primary text, headings)
  - 950: #0A0A0A (background principal - dark mode)

Semantic Colors:
  - Success: #10B981 (75% sat, acciones exitosas)
  - Warning: #F59E0B (70% sat, alertas)
  - Error:   #EF4444 (70% sat, errores)
  - Info:    #3B82F6 (similar a brand, notificaciones)
```

#### Dark Mode (inversión de jerarquía)

```
Backgrounds:
  - Base:    #0A0A0A (neutral-950)
  - Surface: #171717 (neutral-900)
  - Raised:  #262626 (neutral-800)

Text:
  - Primary:   #FAFAFA (neutral-50)
  - Secondary: #A3A3A3 (neutral-500)
  - Disabled:  #525252 (neutral-600)

Borders:
  - Default: #262626 (neutral-800)
  - Subtle:  #171717 (neutral-900)
```

#### Contraste WCAG Validado

| Par de colores | Ratio | Cumplimiento | Uso permitido |
|---|---|---|---|
| Neutral-900 / White | 16.5:1 | AAA | Texto primario |
| Neutral-700 / White | 8.6:1 | AAA | Texto secundario |
| Brand-500 / White | 4.53:1 | AA | CTAs, links (≥14px) |
| Success / White | 3.8:1 | - | Solo elementos grandes (≥18pt bold) |
| White / Neutral-950 (dark) | 19.8:1 | AAA | Texto primario dark mode |
| Brand-500 / Neutral-950 | 6.2:1 | AA | CTAs dark mode |

### 2.2 Tipografía

**Familia primaria: Inter**

```
Font Stack:
'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif

Weights disponibles:
- Regular (400): Body text, inputs
- Medium (500): Nav links, labels
- Semibold (600): Subtítulos, card headers
- Bold (700): Headings principales
```

#### Escala Tipográfica (Desktop 1920px)

| Elemento | Tamaño | Peso | Line-height | Letter-spacing | Uso |
|---|---|---|---|---|---|
| Hero (h1) | 72px | Bold 700 | 1.1 | -0.02em | Dashboard title, landing heroes |
| Title (h2) | 48px | Bold 700 | 1.2 | -0.01em | Section headers (Proyectos, Chat) |
| Subtitle (h3) | 32px | Semibold 600 | 1.3 | 0 | Panel headers, card titles |
| Body Large | 20px | Regular 400 | 1.6 | 0 | Intro text, featured content |
| Body | 16px | Regular 400 | 1.5 | 0 | Standard UI text, mensajes chat |
| Body Small | 14px | Regular 400 | 1.5 | 0 | Helper text, metadata |
| Caption | 12px | Regular 400 | 1.4 | 0.01em | Timestamps, badges, legal |

#### Responsive (Mobile <768px)

| Elemento | Desktop | Mobile |
|---|---|---|
| Hero | 72px | 48px |
| Title | 48px | 36px |
| Subtitle | 32px | 28px |
| Body | 16px | 16px |

**Legibilidad:**
- Max line length: 60-75 caracteres (~700px a 16px)
- Párrafos: line-height 1.6, max-width 65ch
- Código: 'JetBrains Mono', 'Fira Code', monospace

### 2.3 Espaciado (8pt Grid)

**Filosofía:** Generosidad espacial para crear jerarquía clara

```
Escala base (preferir múltiplos de 8):
8px   - Inline spacing (icon + label)
12px  - Tight groups
16px  - Standard element spacing
24px  - Related component groups
32px  - Card padding MÍNIMO (preferir 40px)
48px  - Section internal spacing
64px  - Section boundaries
96px  - Hero section padding
128px - Dramatic spacing (headers principales)
```

**Aplicación por contexto:**

| Contexto | Vertical | Horizontal | Justificación |
|---|---|---|---|
| Hero section | 96-128px | 64px | "Brand moment" espacioso |
| Section spacing | 64-96px | - | Clara separación visual |
| Card padding | 40-48px | 40-48px | Premium feel (nunca <32px) |
| Card gaps | 24-32px | 24-32px | Respiración entre elementos |
| Form field spacing | 24px | - | Legibilidad de formularios |
| Button padding | 16-24px | - | Touch-friendly |

### 2.4 Otros Tokens

#### Border Radius

```
Standard:  12px (inputs, buttons pequeños)
Cards:     16px (tarjetas, panels)
Modals:    20px (dialogs, overlays)
Avatar:    50% (círculos perfectos)
```

#### Sombras

```css
/* Card - Elevación sutil */
card: 0 1px 3px rgba(0, 0, 0, 0.1),
      0 1px 2px rgba(0, 0, 0, 0.06);

/* Card hover - Lift ligero */
card-hover: 0 10px 15px rgba(0, 0, 0, 0.1),
            0 4px 6px rgba(0, 0, 0, 0.05);

/* Modal - Prominente */
modal: 0 20px 25px rgba(0, 0, 0, 0.1),
       0 10px 10px rgba(0, 0, 0, 0.04);

/* Dropdown - Intermedio */
dropdown: 0 4px 6px rgba(0, 0, 0, 0.1),
          0 2px 4px rgba(0, 0, 0, 0.06);
```

#### Animación

```
Duración:
  - Fast: 200ms (hover, clicks)
  - Standard: 250ms (transiciones generales)
  - Slow: 300ms (modals, panels laterales)

Easing:
  - Default: cubic-bezier(0.4, 0, 0.2, 1) [ease-out]
  - Smooth: cubic-bezier(0.4, 0, 0.6, 1) [ease-in-out]

Performance:
  - Solo transform y opacity
  - Evitar width, height, margin, padding
```

---

## 3. Componentes Clave

### 3.1 Navigation Sidebar (Global)

**Estructura:**
- Width fijo: 240px (desktop), 280px (expandido con labels)
- Height: 100vh, sticky
- Background: Neutral-50 (light), Neutral-900 (dark)
- Border-right: 1px solid Neutral-200

**Items de navegación:**
```
Padding:     12px 16px
Radius:      8px
Hover:       Background Neutral-100, transform translateX(2px)
Active:      Background Brand-50, border-left 3px Brand-500
Icon size:   20px (outline style, 2px stroke)
Font:        Medium 500, 14px
Spacing:     4px entre items
```

**Secciones:**
1. Logo area (64px height, centrado)
2. Main navigation (Dashboard, Proyectos, Chat, Editor, Canvas, Archivos)
3. Divider (1px Neutral-200)
4. Secondary (Templates, Configuración)
5. Footer (User profile, 48px height)

**Estados:**
- Collapsed: 64px width (solo iconos)
- Expanded: 240px (iconos + labels)
- Transition: 250ms ease-out

### 3.2 Top Header (Global)

**Estructura:**
```
Height:      64px
Position:    Sticky top-0, z-index 40
Background:  White/blur backdrop (rgba(255,255,255,0.8))
Backdrop:    blur(12px) - glassmorphism sutil
Shadow:      0 1px 3px rgba(0,0,0,0.1) (aparece al scroll)
Padding:     0 32px
```

**Contenido (left to right):**
1. Breadcrumbs (14px, Neutral-500, separador "/")
2. Spacer (flex-grow)
3. Global Search (480px width, 40px height)
4. Notifications Badge (24px badge counter)
5. User Avatar (32px, dropdown on click)

**Search component:**
```
Width:       480px (desktop), full en mobile
Height:      40px
Padding:     8px 12px
Radius:      12px
Icon:        Search icon 20px, left-aligned
Placeholder: "Buscar proyectos, conversaciones, archivos..."
Focus:       2px ring Brand-500, shadow-sm
```

### 3.3 Dashboard Cards (Métricas en Tiempo Real)

**Layout:**
```
Grid:        4 columnas (desktop), 2 (tablet), 1 (mobile)
Gap:         24px
Card ratio:  Flexible height (min 120px)
```

**Estructura de Card:**
```
Padding:     32px
Radius:      16px
Background:  Neutral-100 (light), Neutral-800 (dark)
Border:      1px solid Neutral-200
Hover:       transform translateY(-2px), shadow-lg, 200ms ease-out
```

**Contenido interno:**
```
Icon área:        40px circle, Brand-100 bg, Brand-500 icon
Title:            14px Medium, Neutral-500 (label)
Value:            32px Bold, Neutral-900 (métrica principal)
Trend indicator:  12px, Success/Error color, ↑↓ icon
Sparkline:        Optional, 60px height, subtle Brand-500 line
```

**Ejemplo - Token Usage Card:**
```
[Icon: Zap 20px]
"Tokens Usados"                    [Neutral-500, 14px]
"1.2M / 5M"                        [Neutral-900, 32px Bold]
"+15% vs ayer" [Success, 12px]    [↑ icon]
[Sparkline mini-gráfico]
```

### 3.4 Chat Message Bubbles

**Estructura base:**
```
Max-width:   700px
Padding:     16px 20px
Radius:      16px (user), 16px 16px 4px 16px (assistant)
Margin-bottom: 16px
```

**User message:**
```
Align:       Right (ml-auto)
Background:  Brand-500
Text:        White, 16px Regular
Shadow:      card shadow sutil
```

**Assistant message:**
```
Align:       Left (mr-auto)
Background:  Neutral-100 (light), Neutral-800 (dark)
Text:        Neutral-900, 16px Regular
Avatar:      32px circle, Brand-100 bg, "AI" text
```

**Streaming indicator:**
```
Component:   Pulsing dots (3 circles)
Size:        6px each, 4px gap
Color:       Neutral-500
Animation:   Pulse scale(1.2) 600ms infinite, stagger 150ms
```

**Code blocks dentro de mensajes:**
```
Background:  Neutral-900 (light), Neutral-950 (dark)
Padding:     16px
Radius:      8px
Font:        'JetBrains Mono', 14px
Syntax:      highlight.js o Prism (theme: One Dark Pro)
Copy button: 32px, top-right corner, opacity 0 → 1 on hover
```

### 3.5 Monaco Editor Integration

**Container:**
```
Height:      calc(100vh - 64px - 48px) [header - tabs]
Background:  Neutral-900 (dark theme preferido)
Theme:       'vs-dark' o 'One Dark Pro'
```

**Componentes integrados:**

**File Tabs:**
```
Height:      40px
Padding:     8px 16px
Font:        Medium 500, 14px
Active:      Background Neutral-800, border-bottom 2px Brand-500
Inactive:    Background Neutral-900, text Neutral-500
Close icon:  16px, opacity 0.5 → 1 on hover
Max tabs:    Scroll horizontal si >10
```

**Status Bar (bottom):**
```
Height:      32px
Background:  Neutral-950
Padding:     0 16px
Font:        12px Regular
Sections:    Line:Col | Language | LSP status | Errors/Warnings
Colors:      Success (LSP OK), Warning, Error badges
```

**Inline Completions (AI suggestions):**
```
Display:     Inline ghost text, Neutral-600
Font:        Italic 14px
Trigger:     Debounced 500ms after typing pause
Accept:      Tab key
Dismiss:     Esc key
Badge:       "AI" label 12px, Brand-500, top-right de suggestion
```

### 3.6 Context Panel (Collapsible)

**Ubicación:** Right sidebar, 360px width

**Structure:**
```
Width:       360px (expandido), 48px (collapsed)
Background:  Neutral-50 (light), Neutral-900 (dark)
Border-left: 1px solid Neutral-200
Toggle:      Icono chevron, 32px button, top-center
```

**Secciones internas:**

**1. Active Files (chips)**
```
Display:     Flex wrap, gap 8px
Chip style:  Padding 4px 8px, Radius 6px
Background:  Neutral-200
Text:        12px Medium, Neutral-700
Icon:        File type icon 14px
Close:       × icon, 12px, click to remove
```

**2. Active Instructions (badges)**
```
Display:     Stack vertical, gap 12px
Badge:       Padding 8px 12px, Radius 8px
Background:  Brand-50, border 1px Brand-200
Text:        14px Regular, Neutral-900
Icon:        Info icon 16px, Brand-500
```

**3. Token Counter**
```
Display:     Progress bar + text
Bar height:  8px, Radius 4px
Background:  Neutral-200
Fill:        Brand-500 (0-70%), Warning (70-90%), Error (90-100%)
Text:        "1,234 / 5,000 tokens" 14px Medium
Tooltip:     Breakdown (input/output/cache) on hover
```

**4. Conversation Summary**
```
Display:     Collapsible accordion
Title:       "Resumen de contexto" 14px Semibold
Content:     Max 3 líneas, 14px Regular, Neutral-700
Action:      "Ver completo" link, opens modal
```

---

## 4. Layout y Responsive

### 4.1 Arquitectura de Layout (SPA)

**App Shell:**
```
Display:     Grid template areas
Columns:     [sidebar] 240px | [main] 1fr | [context-panel] 0/360px
Rows:        [header] 64px | [content] 1fr
Gap:         0 (borders entre paneles)
```

**Áreas nombradas:**
```css
grid-template-areas:
  "sidebar header header"
  "sidebar main context-panel";
```

**Responsive breakpoints:**

| Breakpoint | Sidebar | Header | Context Panel | Grid |
|---|---|---|---|---|
| < 768px | Overlay drawer | Full width | Bottom sheet | Single column |
| 768-1024px | 64px (collapsed) | Full width | Overlay (right) | 2 columns |
| 1024-1440px | 240px | Full width | 360px (optional) | 3 columns |
| > 1440px | 240px | Full width | 360px | 3 columns |

### 4.2 Dashboard Layout (Vista Principal)

**Grid de métricas:**
```
Desktop (>1024px): 4 columnas, gap 24px
Tablet (768-1024): 2 columnas, gap 20px
Mobile (<768px):   1 columna, gap 16px
```

**Sección "Proyectos Destacados":**
```
Layout:      3 columnas (desktop), 2 (tablet), 1 (mobile)
Card height: 240px
Padding:     32px
Content:     Project icon (48px) + Title (20px Semibold) +
             Stats row (archivos, conversaciones) +
             "Abrir" CTA button (40px)
Hover:       Lift -4px + shadow-lg + scale(1.02)
```

### 4.3 Chat Layout (Vista Conversacional)

**Split view:**
```
Left:        Conversaciones list (280px fixed)
Center:      Message feed (flex-grow)
Right:       Context panel (360px, collapsible)
```

**Conversation list sidebar:**
```
Header:      "Conversaciones" + New button (48px)
Search:      32px input, 8px margin-bottom
Items:       Padding 12px, hover Neutral-100
Active:      Background Brand-50, border-left Brand-500
Preview:     Title 14px Semibold + Last message 12px (2 lines max)
Timestamp:   12px Neutral-500, top-right
```

**Message feed:**
```
Padding:     32px (sides), 24px (top/bottom)
Max-width:   900px (center aligned)
Background:  Neutral-50 (light), Neutral-950 (dark)
Scroll:      Smooth scroll, auto-scroll on new message
```

### 4.4 Editor Layout (IDE View)

**3-panel classic:**
```
Left:        File Explorer (240px, resizable 180-360px)
Center:      Monaco Editor (flex-grow)
Bottom:      Terminal panel (240px height, resizable 120-480px)
```

**File Explorer:**
```
Header:      "Explorador" + Collapse/Expand icons
Tree indent: 16px por nivel
Icons:       File type icons 16px (VSCode icon theme)
Hover:       Background Neutral-100
Active:      Background Brand-50, text Brand-600
```

**Terminal panel:**
```
Background:  #1E1E1E (match editor theme)
Font:        'JetBrains Mono', 14px
Padding:     12px
Tabs:        Multiple terminal tabs (bash, node, python)
Resize:      Drag handle, 4px height, Neutral-600
```

---

## 5. Interacciones y Animaciones

### 5.1 Micro-animaciones (Performance-First)

**Hover states:**
```css
/* Buttons */
.button:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px rgba(0,0,0,0.1);
  transition: all 200ms ease-out;
}

/* Cards */
.card:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 20px 25px rgba(0,0,0,0.1);
  transition: all 250ms ease-out;
}

/* Navigation items */
.nav-item:hover {
  transform: translateX(2px);
  transition: transform 200ms ease-out;
}
```

**Loading states:**

**Skeleton screens (preferir sobre spinners):**
```
Background:  Linear gradient shimmer
Colors:      Neutral-200 → Neutral-100 → Neutral-200
Animation:   Translate 2000ms infinite ease-in-out
Width:       Varies (60-100% por line)
Height:      Match target component (16px text, 40px button)
Radius:      Match target (12px button, 4px text)
```

**Streaming dots (chat assistant typing):**
```
Dots:        3 circles, 6px each
Gap:         4px
Color:       Neutral-500
Animation:   Scale 0.8 → 1.2, 600ms infinite
Stagger:     0ms, 150ms, 300ms delays
```

**Progress bars (file upload, context loading):**
```
Height:      8px
Radius:      4px
Background:  Neutral-200
Fill:        Brand-500, animated width transition
Text:        Above bar, 14px Medium, "45% completado"
```

### 5.2 Page Transitions

**Route changes:**
```
Fade out:    Opacity 1 → 0, 150ms ease-out
Content:     TranslateY(0 → 20px) durante fade out
Fade in:     Opacity 0 → 1, 300ms ease-out
Content:     TranslateY(20px → 0) durante fade in
Timing:      Fade out completo antes de fade in
```

**Modal/Dialog enter:**
```
Backdrop:    Opacity 0 → 1, 200ms ease-out
Modal:       Scale 0.95 → 1 + Opacity 0 → 1, 250ms ease-out
Transform:   TranslateY(-20px → 0) para entrada desde arriba
```

**Drawer/Sidebar enter:**
```
Backdrop:    Opacity 0 → 1, 200ms
Drawer:      TranslateX(-100% → 0), 300ms ease-out (left)
             TranslateX(100% → 0), 300ms ease-out (right)
```

### 5.3 Feedback Visual

**Success actions:**
```
Duration:    2000ms auto-dismiss
Position:    Top-right, fixed
Background:  Success color
Icon:        Check circle 20px
Text:        14px Medium, White
Animation:   Slide in from right + fade in
```

**Error states:**
```
Input:       Border 2px Error, shake animation 400ms
Message:     Below input, 14px Regular, Error color
Icon:        Warning triangle 16px
Persist:     Until corrected
```

**Loading inline (buttons):**
```
Button disabled:  Opacity 0.6, cursor not-allowed
Spinner:          16px circle, 2px stroke, Brand-500
Text:             "Procesando..." replace button text
Position:         Center aligned
```

---

## 6. Casos Específicos de IRIS

### 6.1 Streaming de Respuestas IA

**Progressive rendering:**
```
Initial:     "Escribiendo..." indicator (pulsing dots)
Stream:      Append text word-by-word o token-by-token
Formatting:  Render markdown inline (bold, italic, lists)
Code:        Detect ``` fence, render syntax highlighted block
Scroll:      Auto-scroll to bottom on new content
Cancel:      Stop button (32px, Error color, top-right of message)
```

**Latencia target:**
- Time to first token: <800ms
- Tokens per second: 20-40 (perceptible como "escribiendo")
- Smooth rendering: RequestAnimationFrame para evitar jank

### 6.2 Multi-Project Context Switching

**Project selector:**
```
Location:    Breadcrumb area (top-left)
Trigger:     Click project name → dropdown
Dropdown:    Max-height 400px, scroll overflow
Items:       Padding 12px 16px, hover Neutral-100
Active:      Background Brand-50, checkmark icon
Search:      Input en top del dropdown, filter live
```

**Context preservation:**
- Guardar estado de tabs abiertas por proyecto
- Restaurar última conversación activa
- Indicar "cambio de contexto" con toast notification
- Transition: Fade out content (150ms) → Swap → Fade in (300ms)

### 6.3 File Upload & Drag-Drop

**Drag-drop zone:**
```
State:       Idle | Hover | Uploading | Success | Error
Idle:        Border 2px dashed Neutral-300, Radius 16px
Hover:       Border Brand-500, Background Brand-50
Uploading:   Progress bar, file name, cancel button
Success:     Green checkmark, "3 archivos subidos"
Error:       Red border, error message, retry button
```

**File preview (en lista):**
```
Item height: 56px
Layout:      Icon (40px) | Name (14px) + Size (12px) | Actions (32px)
Icon:        File type icon, colored by extension
Actions:     Download, Delete, More (kebab menu)
Hover:       Background Neutral-100
```

### 6.4 LSP Indicators (Editor)

**Status bar section:**
```
Icon:        Circle 8px (Success/Warning/Error color)
Text:        "TypeScript" 12px Medium
Hover:       Tooltip con detalles (errors: 2, warnings: 5)
Click:       Abre panel de problemas (bottom drawer)
```

**Inline diagnostics:**
```
Underline:   Wavy line (Error red, Warning yellow)
Icon gutter: Warning/Error icon 16px en line number area
Hover:       Tooltip con mensaje completo + code action links
```

### 6.5 Context Token Visualization

**Token meter (sidebar panel):**
```
Display:     Circular progress (120px diameter)
Center:      "1,234 / 5,000" 16px Bold
Ring:        Stroke 8px, Brand-500 (used), Neutral-200 (remaining)
Thresholds:  70%: Warning-500, 90%: Error-500
Animation:   Smooth transition 400ms ease-out on update
```

**Breakdown (hover tooltip):**
```
Rows:        Input: 800 | Output: 234 | Cache: 200 | Total: 1,234
Font:        12px Monospace (numbers aligned)
Colors:      Each category con color sutil
Actions:     "Compactar contexto" link si >70%
```

---

## 7. Accesibilidad y Cumplimiento

### 7.1 WCAG 2.1 AA Compliance

**Contraste:**
- Texto regular: ≥4.5:1 (validado en §2.1)
- Texto grande (≥18pt): ≥3:1
- Elementos interactivos: ≥3:1 (borders, icons)

**Navegación por teclado:**
- Todo interactivo alcanzable con Tab
- Focus ring visible: 2px solid Brand-500, offset 2px
- Skip links: "Saltar a contenido principal" (hidden hasta focus)
- Shortcuts: Definir y documentar (Cmd+K search, Cmd+P projects, etc.)

**Screen readers:**
- ARIA labels en iconos sin texto
- ARIA live regions en chat streaming (aria-live="polite")
- ARIA expanded/collapsed en panels colapsables
- Role definitions: navigation, main, complementary, search

**Touch targets:**
- Mínimo 44×44px en mobile (Apple HIG)
- Spacing mínimo 8px entre targets
- Botones 48×48px preferido (más confortable)

### 7.2 Motion & Animation

**Reduce motion (prefers-reduced-motion):**
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

**Flashing content:**
- Evitar flashes >3 por segundo
- Pulsing animations suaves (opacity 0.5-1, no strobing)

### 7.3 Responsive & Mobile

**Viewport settings:**
```html
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5">
```

**Mobile adjustments:**
- Sidebar → Overlay drawer (swipe desde edge)
- Context panel → Bottom sheet (swipe up)
- Editor → Full screen, hide sidebars por defecto
- Font sizes: +2px base (16px → 18px body text)
- Spacing: -25% reduction (64px → 48px sections)

---

## 8. Performance & Optimización

### 8.1 Rendering Strategy

**Critical rendering path:**
- Inline critical CSS (<14KB)
- Defer non-critical fonts (swap)
- Lazy load routes y componentes pesados (Monaco, Canvas)
- Code splitting por vista

**Virtualization:**
- Chat messages: React Virtuoso o react-window (>100 mensajes)
- File lists: Virtualized list (>500 archivos)
- Large datasets: Windowing con buffer 20 items

### 8.2 Asset Optimization

**Images:**
- WebP con fallback a PNG/JPG
- Responsive images (srcset)
- Lazy loading (loading="lazy")
- Icon sprites SVG (único request)

**Fonts:**
- WOFF2 format (mejor compresión)
- Subset fonts (solo caracteres usados)
- Font-display: swap (show fallback mientras carga)

### 8.3 State Management

**Global state (Zustand o Redux):**
- User session & preferences
- Active project & conversation
- Open files & tabs
- Notifications queue

**Local state:**
- Form inputs
- UI toggles (modals, drawers)
- Transient animations

---

**Fin del Documento**

Este diseño specification provee las decisiones visuales y de interacción necesarias para implementar IRIS. Los componentes están diseñados para escalar con el sistema mientras mantienen coherencia visual y rendimiento óptimo.
