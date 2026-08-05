# AGENTS.md — Manual de arquitectura y protocolo operativo

**SilhouetteAppcreator** es un sistema multi-agente para desarrollo de software autónomo.

Este archivo es la referencia para cualquier agente o persona que trabaje en el
repositorio. Describe **lo que el código hace hoy**, no lo que se aspira a que
haga. Cuando una capacidad esté planificada pero no implementada, aquí aparecerá
marcada como tal.

---

## Regla primera: no declarar sin medir

Una auditoría de agosto de 2026 encontró que varios módulos publicados como
funcionales devolvían datos fijos, y que el script de verificación tenía su
resultado escrito a mano — por lo que el sistema reportaba «95,2 % EXCELENTE»
sin comprobar ningún comportamiento.

De ahí las tres reglas que rigen este repositorio:

1. **Un fallo debe parecer un fallo.** Nunca devuelva una cadena de éxito cuando
   una operación falle. Propague la excepción o devuelva un error explícito.
2. **Sin datos es una respuesta válida.** Si no hay observaciones, devuelva
   `None` o `available: false`. No invente una métrica plausible.
3. **Lo que no está en un test, no está hecho.** `python verificar_sistema.py`
   ejecuta la suite real; su salida es la única medida válida de progreso.

---

## Conectar una IA

```bash
python conectar.py              # qué hay conectado, qué falta y cómo arreglarlo
python conectar.py --arreglar   # aplica las reparaciones automáticas
python conectar.py --clave openrouter sk-or-v1-...
```

El asistente **sondea de verdad**: ejecuta cada agente instalado y llama a cada
API. Un CLI instalado sin sesión iniciada aparece como `[SIN SESION]`, no como
disponible; una clave revocada aparece como inválida aunque la variable exista.

| Vía | Cómo |
|---|---|
| Clave de API | `python conectar.py --clave <proveedor> <clave>`. Se valida antes de guardarla: si no funciona, no se escribe. |
| Cuenta de Google | `gemini` y elegir «Login with Google». Sin gestionar claves. |
| Suscripción de Claude | `claude` y escribir `/login`. |
| Local, sin coste | `ollama serve` — se detecta solo. |

Proveedores soportados: OpenRouter, OpenAI, Anthropic, Google AI, Groq,
DeepSeek, Zhipu, Moonshot, MiniMax, xAI, Mistral, Ollama, LM Studio y vLLM.

Agentes CLI soportados (12): Claude Code, Gemini CLI, Codex, Cursor Agent,
Antigravity, Aider, Qwen Code, OpenCode, Crush, Copilot CLI, Goose y Amp.
Añadir uno nuevo es añadir un `CLISpec` en `backend/app/core/cli_adapters.py`;
no hay que tocar el router.

---

## Puesta en marcha

```bash
# 1. Dependencias (incluye silhouette-brain desde su repositorio)
pip install -e ".[dev,reasoning,research,market]"

# 2. Configuración
cp .env.example .env
python -m backend.app.security.auth "su-contraseña"   # genere el hash
#    pegue el resultado en SILHOUETTE_ADMIN_PASSWORD_HASH y rellene el correo

# 3. Verificación
python verificar_sistema.py

# 4. Backend  ->  http://localhost:8001  (docs en /docs)
python silhouettemcp_server.py

# 5. Dashboard  ->  http://localhost:5173
cd mcp-dashboard && cp .env.example .env.local && pnpm install && pnpm dev
```

---

## Arquitectura

### Núcleo de orquestación

| Componente | Archivo | Qué hace |
|---|---|---|
| Router LLM | `backend/app/core/llm_router.py` | Llamadas reales vía httpx/LiteLLM, circuit breaker y rate limiter por proveedor, cadenas de fallback. **Instancia única compartida.** |
| Orquestador | `backend/app/orchestrator/multi_agent.py` | Coordina 5 agentes con fan-out/fan-in y recupera tareas huérfanas tras un reinicio. |
| Supervisor ejecutivo | `backend/app/orchestrator/executive_supervisor.py` | Jerarquía de 3 equipos. Métricas calculadas desde observaciones reales; detecta estancamientos por tiempo en vuelo. |
| Auto-mejora | `backend/app/evolution/agent_improver.py` | Ajusta perfiles de agente (temperatura, directivas, reintentos) y los **persiste** en `data/agent_profiles.json`. |
| Matriz de debate | `backend/app/swarm/debate_matrix.py` | Ciclo Creador → Crítico → Juez con **tres llamadas reales** al router. |

### Memoria cognitiva

`backend/app/services/silhouette_brain_service.py` es un adaptador sobre el
paquete [`silhouette-brain`](https://github.com/haroldfabla2-hue/silhouette-brain),
que implementa los cuatro niveles de verdad:

```
WORKING (LRU/Redis) -> EPISODIC (SQLite) -> SEMANTIC (vectores) -> DEEP (grafo)
```

Funciona sin servicios externos (SQLite + grafo en memoria + embedder sin
dependencias) y sube a Redis/Neo4j/fastembed cuando se configuran. Si el paquete
no está instalado, el servicio reporta `available: false` y lanza
`BrainUnavailable` — no devuelve estadísticas inventadas.

### Trabajo sobre proyectos reales

Cuatro capas que convierten «varios agentes llamando a un modelo» en un equipo
que trabaja sobre carpetas y ramas del usuario. Nacieron de una auditoría que
comparó lo que se decía del sistema con lo que el código hacía: la sesión
compartida, la asignación de modelo por agente y el aislamiento se daban por
implementados y no existían.

| Componente | Archivo | Qué hace |
|---|---|---|
| Sesión compartida | `core/session.py` | Un `session_id` por objetivo. `compose_prompt()` inyecta el objetivo, lo que ya aportaron los otros agentes y los recuerdos recuperados; `run_with_context()` persiste cada contribución en la memoria. Sin esto cada agente partía de cero. |
| Modelo por agente | `core/agent_models.py` | `DEFAULT_POLICIES` asigna proveedor y temperatura a cada agente (razonador → Claude Code, ejecutor web → Gemini, verificador a 0.05). `resolve_provider()` devuelve `None` si el preferido no está disponible — **nunca** uno que no lo esté. |
| Proyectos locales | `projects/registry.py` | Carpetas registradas explícitamente; registrar es el consentimiento. `FORBIDDEN_ROOTS` bloquea `~`, Escritorio, Documentos y raíces del sistema. `unregister()` **no borra nada**. Persiste en `data/projects.json`. |
| Ramas y aislamiento | `projects/workspaces.py` | Worktrees de git reales: `reserve()` crea la rama `silhouette/<agente>-<tarea>` en `.silhouette-worktrees/`, `integrate()` prueba con `merge-tree --write-tree` y **aborta** si hay conflicto, `release()` conserva las ramas sin integrar. |
| CLIs | `core/cli_manager.py` | Instala y autentica los 12 CLIs soportados. `install()` comprueba que el binario **resuelva** después (npm sale con 0 sin dejarlo en el PATH); `open_login_terminal()` abre una terminal real para el OAuth, porque el login no se puede hacer sin interacción. |

En el dashboard esto es la pestaña **Proyectos** (`ProjectsPanel.tsx`):
registrar carpeta, listar y crear ramas, ver los espacios de cada agente,
instalar y autenticar CLIs.

### Seguridad

| Módulo | Responsabilidad |
|---|---|
| `security/auth.py` | Credenciales desde el entorno, hash PBKDF2 con sal, tokens de sesión opacos y caducables. **Falla en cerrado** si no hay administrador. |
| `security/workspace.py` | Confina toda ruta a la raíz del proyecto; bloquea secretos, `.git` y material criptográfico. Resuelve enlaces simbólicos antes de comprobar. |
| `security/process_policy.py` | Lista blanca de aplicaciones lanzables. **Vacía por defecto** = capacidad desactivada. |
| `security/prompt_injection_guard.py` | Clasificador graduado (NONE→CRITICAL) sobre el guardián de silhouette-brain, más patrones en español. |
| `logic_engine/z3_verifier.py` | Invariantes de seguridad con Z3 cuando está disponible. **Falla en cerrado.** |

---

## Reglas para agentes que modifiquen este repositorio

### Antes de declarar una tarea completada

```bash
python verificar_sistema.py
```

Debe terminar con `ESTADO: TODO CORRECTO` y código de salida 0. Cualquier otra
cosa significa que la tarea no está terminada.

### Calidad exigida en CI

```bash
ruff check backend/app/security backend/app/swarm backend/app/logic_engine \
           backend/app/evolution backend/app/orchestrator/executive_supervisor.py \
           backend/app/services/silhouette_brain_service.py tests
mypy          # estricto sobre los módulos nuevos
pytest        # 163 tests, sin servicios externos
```

`.github/workflows/ci.yml` incluye además **barreras de seguridad** que fallan el
build si reaparece cualquiera de estos problemas: secretos versionados, claves de
API en el árbol, credenciales escritas en el código, CORS con comodín en una
superficie activa, archivos `.pyc` versionados, simulaciones fuera de
`legacy/`, importaciones desde `legacy/`, respuestas fabricadas en el router
o en los agentes, y métricas de salud con cifras fijas.

### Al añadir un endpoint

- Todo lo que escriba en disco, lance procesos, borre datos o toque credenciales
  lleva `admin=Depends(verify_admin)`.
- Toda ruta de archivo pasa por `resolve_within_workspace()`.
- Todo nombre de aplicación pasa por `plan_launch()`.
- Añada el caso a `tests/test_api_security.py`.

### Variables de entorno

Ver `.env.example`. Las dos obligatorias para operar:
`SILHOUETTE_ADMIN_EMAIL` y `SILHOUETTE_ADMIN_PASSWORD_HASH`.

---

### Jerarquía dinámica y bucle autónomo

Portados de Silhouette Agency OS. Es la capa que hace que el sistema trabaje solo:

| Componente | Archivo | Qué hace |
|---|---|---|
| Introspección | `backend/app/evolution/introspection.py` | Observa la telemetría del supervisor y **deriva objetivos** donde detecta degradación. Sin observaciones suficientes no deriva nada. |
| Fábrica de equipos | `backend/app/orchestrator/squad_factory.py` | Un modelo diseña el organigrama (roles, niveles CORE/SPECIALIST/WORKER, líder). Recluta agentes existentes antes de crear nuevos. |
| Bucle de evolución | `backend/app/evolution/evolution_scheduler.py` | Ciclo en segundo plano: introspección → calibración → formación de equipos → verificación. |

El ciclo cierra sobre sí mismo: un objetivo sólo se marca completado cuando la
métrica que lo originó ha mejorado de verdad (`_close_resolved_goals`). Es lo
que distingue evolucionar de simular que se evoluciona.

```bash
curl -X POST localhost:8001/api/evolution/start   -H "Authorization: Bearer $TOKEN"
curl      localhost:8001/api/evolution/status
curl      localhost:8001/api/evolution/goals
curl      localhost:8001/api/squads
```

### Herramientas reales (`backend/app/tools/`)

Cada módulo sustituye a una capacidad que en `legacy/` devolvía datos inventados.

| Módulo | Sustituye a | Qué hace ahora |
|---|---|---|
| `git_agent.py` | `git_operations_agent.py` (5 métodos `_simulate_*`) | Comandos git reales: estado, ramas, historial, merge y detección de conflictos con `merge-tree` (sin tocar el árbol de trabajo). Rutas confinadas al workspace; nombres de rama validados contra inyección de opciones. |
| `research.py` | `expanded_research.py` (patentes e inventores con `random.choice()`) | arXiv + Semantic Scholar, APIs públicas y gratuitas. XML parseado con `defusedxml`. Las patentes se declaran no implementadas en lugar de fingirse. |
| `market_data.py` | `expanded_finance.py` (`random.uniform(10, 500)` como precio) | Cotizaciones e histórico reales vía `yfinance`, con advertencia de retardo en cada respuesta. |

```bash
curl "localhost:8001/api/git/info?path=."         -H "Authorization: Bearer $TOKEN"
curl "localhost:8001/api/research/search?query=monte+carlo+tree+search"
curl "localhost:8001/api/market/quote?symbol=MSFT"
```

### El organismo (`backend/app/organism/`)

La capa que mantiene el sistema vivo **sin que nadie interactúe**. Es lo que
convierte un servidor que espera peticiones en algo que trabaja por su cuenta.

| Componente | Qué hace |
|---|---|
| `homeostasis.py` | Mide CPU, RAM y disco y clasifica el entorno. Bajo presión **espacia** la cadencia; nunca desactiva un motor. «Nunca perder capacidades, sólo adaptarlas.» |
| `circadian.py` | Cinco fases según el silencio: ACTIVE, ALERT, DROWSY, DREAMING, DEEP_REST. Cada una habilita distintos motores. |
| `vital_daemon.py` | El bucle vital: late, aísla fallos, persiste su ritmo y garantiza instancia única. |
| `cognitive_organs.py` | Los cuatro motores de `silhouette-brain` (Curiosity, Janitor, Dreamer, Evolution) registrados como órganos. Corren durante el sueño porque reescriben la memoria. |
| `self_healing.py` | Diagnóstico medido (recursos, órganos, agentes, estancamiento) y reparación real: libera tareas colgadas y recalibra agentes degradados. |

Los motores cognitivos son la pieza biomimética del ciclo. La Curiosidad merece
una nota: **sólo genera preguntas, nunca hechos** — la misma regla que rige el
proyecto. Un test (`test_ningun_motor_queda_sin_fase`) impide que un órgano
quede registrado sin fase circadiana, un fallo que ya ocurrió una vez: tres
motores se registraron pero no estaban en `PHASE_ENGINES`, así que nunca se
habrían ejecutado.

```bash
curl      localhost:8001/api/cognition/engines
curl -X POST localhost:8001/api/cognition/run-all -H "Authorization: Bearer $TOKEN"
curl      localhost:8001/api/health/diagnose
curl -X POST localhost:8001/api/health/heal      -H "Authorization: Bearer $TOKEN"
```

El comportamiento que da: **mientras trabajas, el organismo se aparta y sólo
late; cuando te vas, consolida memoria, deriva objetivos y recalibra agentes.**
En fase ACTIVE sólo se ejecuta `heartbeat` para no competir por recursos con tu
petición. A partir de 45 minutos de silencio empieza la introspección; a las 2
horas entra en DREAMING y consolida.

Tres propiedades no negociables, cada una con tests que las defienden:

1. **Un órgano que revienta jamás tumba al organismo.** Se registra su fallo, se
   marca su salud y el resto sigue latiendo. Ni un fallo del propio
   planificador detiene el bucle.
2. **El ritmo sobrevive al reinicio**, así que arrancar no dispara todo a la vez.
3. **Instancia única**, tanto entre procesos (fichero con PID) como dentro del
   mismo proceso (registro en memoria).

```bash
curl -X POST localhost:8001/api/organism/awaken -H "Authorization: Bearer $TOKEN"
curl      localhost:8001/api/organism/vitals
curl -X POST localhost:8001/api/organism/tick   -H "Authorization: Bearer $TOKEN"
```

---

## Deuda conocida (declarada, no oculta)

### Simulaciones: ninguna en la superficie activa

Toda la superficie activa —los 107 archivos `.py` que se ejecutan— está libre de
datos fabricados. Dos barreras de CI lo mantienen así: una prohíbe simulaciones
fuera de `legacy/` y `tests/`, y otra impide importar código archivado.

Los mocks **dentro de `tests/`** son legítimos y están permitidos: simular una
dependencia en un test es ingeniería correcta. Lo que no se admite es que
código de producción devuelva datos inventados.

### El archivo histórico (`legacy/`)

9 directorios con 354 archivos `.py` (222.898 líneas) se apartaron a `legacy/`
con `git mv`, **íntegros y con su historial**. Eran huérfanos completos: ni
`backend/`, ni el servidor, ni `docker-compose.yml` importaban una línea de
ahí. 39 de sus archivos de producción fabricaban datos — el más ilustrativo,
un «Research Intelligence Agent» que generaba números de patente e inventores
con `random.choice()`.

Nada se ha perdido. Para recuperar o portar algo, ver `legacy/README.md`.

Lo que se retiró y por qué importaba cada caso:

| Antes | Ahora |
|---|---|
| `api/memory.py`: `_simulate_memory_storage`, `_simulate_memory_clear`, `mock_results`, estadísticas escritas a mano (1247 memorias, 245,7 MB) | Delegan en `SilhouetteBrainService`; el borrado selectivo devuelve 501 en vez de un conteo inventado |
| `api/tools.py`: cinco `_simulate_*` y un catálogo de 12 herramientas escrito a mano | Ejecuta el `ToolManager` real; el catálogo sale del registro; 404 si la herramienta no existe |
| `api/tasks.py`: stream de cinco fases con progreso fijo por temporizador; resultados de tarea inventados para cualquier id | Retransmite las actualizaciones reales del `TaskManager`; 404 si la tarea no existe |
| `agents/executor.py`: `mock_search`, «Contenido simulado de X», `success: True` fijo, PDF con marcador de posición, artefactos `artifact://` que no se escribían | Errores explícitos cuando falta la herramienta; el éxito lo decide la herramienta; PDF real con pypdf; artefactos escritos en disco |
| `agents/verifier.py`: dos de tres comprobaciones fijadas a `True` | Detecta contradicciones y dependencias colgantes de verdad |
| `agents/mcts_planner.py`: `random.uniform()` en la evaluación | Desempate determinista derivado del plan: mismo plan, misma puntuación |
| `core/dynamic_mcp_factory.py`: `MockFastMCP` reportado como `status: active` | Lanza `MCPFactoryUnavailable` si FastMCP no está instalado |
| `core/llm_router.py`: descartaba toda respuesta que contuviera la palabra «error» | Sólo descarta sus propios marcadores de degradación, y sólo al principio |

### Resuelto

Estos puntos estuvieron abiertos y ya no lo están. Se dejan anotados porque
saber qué se arregló evita volver a introducirlo:

| Era | Estado |
|---|---|
| Dos backends con configuración divergente | Una sola aplicación; `backend/main.py` la reexporta para el puerto 8000 |
| Los routers `/api/v1` sin ninguna autenticación | Montados con `Depends(verify_admin)`; 401 sin token |
| `@app.on_event` deprecado | Migrado a `lifespan` |
| `class Config` de Pydantic v1 | Migrado a `SettingsConfigDict` |
| `code/`, `package/` y 7 directorios más en la raíz | En `legacy/`, aislados por CI |
| Correo del administrador escrito en el código | Sale del entorno |
| Chequeos de salud con cifras fijas (`1247` consultas, `2.1%` de error, siempre `healthy`) | Ping real a base de datos y Redis; estadísticas reales del router |
| `task_manager` pedía un bucle de eventos al importarse | Se programa en el arranque |
| Cada agente empezaba sin saber qué habían hecho los demás | `core/session.py`: sesión con identificador, contexto compartido inyectado en el prompt y contribuciones persistidas |
| Todos los agentes compartían un único router sin política propia | `core/agent_models.py`: proveedor y temperatura por agente, sin recurrir a uno no disponible |
| El sistema sólo sabía operar sobre su propio directorio | `projects/registry.py`: carpetas locales registradas, con raíces del sistema bloqueadas |
| El «aislamiento» entre agentes concurrentes era una descripción | `projects/workspaces.py`: worktrees de git reales, integración que aborta ante conflicto |
| El instalador de CLIs usaba `shell=True` y creía al código de salida | `core/cli_manager.py`: sin shell, y se verifica que el binario resuelva |

### Pendiente

- **Historial de Git**: contuvo una clave de OpenRouter y una clave maestra. Se
  retiraron del índice, pero **siguen en el historial** hasta que se reescriba
  con `git filter-repo`. Rotar las claves es independiente de eso, y prioritario.
- **Seguimiento asíncrono de herramientas** (`api/tools.py`): devuelve 501. Para
  implementarlo hace falta Redis; se declara en lugar de fingirse.
- **Búsqueda de patentes** (`tools/research.py`): lanza `NotImplementedError`.
  Requiere elegir una API externa — PatentsView es gratuita con registro; Google
  Patents y EPO OPS son de pago. Es una decisión de producto.
- **`frontend/`** (referenciado por `docker-compose.yml`) es una app React
  anterior a `mcp-dashboard`; decidir cuál sobrevive.

---

## Repositorio

- **Remoto:** `https://github.com/haroldfabla2-hue/SilhouetteAppcreator.git`
- **Rama:** `main`
- **Nunca** versione `.zip`, `__pycache__`, `.env` ni claves. El `.gitignore`
  está en UTF-8 (estuvo en UTF-16, lo que impedía a Git aplicar la primera regla).
