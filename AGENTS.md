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

## Puesta en marcha

```bash
# 1. Dependencias (incluye silhouette-brain desde su repositorio)
pip install -e ".[dev,reasoning]"

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
superficie activa, o archivos `.pyc` versionados.

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

### El organismo (`backend/app/organism/`)

La capa que mantiene el sistema vivo **sin que nadie interactúe**. Es lo que
convierte un servidor que espera peticiones en algo que trabaja por su cuenta.

| Componente | Qué hace |
|---|---|
| `homeostasis.py` | Mide CPU, RAM y disco y clasifica el entorno. Bajo presión **espacia** la cadencia; nunca desactiva un motor. «Nunca perder capacidades, sólo adaptarlas.» |
| `circadian.py` | Cinco fases según el silencio: ACTIVE, ALERT, DROWSY, DREAMING, DEEP_REST. Cada una habilita distintos motores. |
| `vital_daemon.py` | El bucle vital: late, aísla fallos, persiste su ritmo y garantiza instancia única. |

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

### Simulaciones: ninguna

`backend/app/` no contiene simulaciones. La barrera de CI «Ninguna simulación en
backend/app» falla el build si reaparece un `mock_*`, `_simulate_*` o
`MockFastMCP`.

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

### Otros

- **Dos backends coexisten**: `silhouettemcp_server.py` (8001, activo) y
  `backend/main.py` (8000). Pendiente de consolidar en uno.
- **`code/` y `package/`** son volcados heredados de scripts sueltos con CORS
  abierto. No se sirven; pendientes de retirada. Están fuera del alcance de las
  barreras de CI precisamente por eso.
- **Historial de Git**: contuvo una clave de OpenRouter y una clave maestra. Se
  retiraron del índice, pero **siguen en el historial** hasta que se reescriba
  con `git filter-repo`. Las claves deben rotarse con independencia de eso.
- **`@app.on_event`** está deprecado; migrar a *lifespan* de FastAPI.
- **`backend/app/core/config.py`** usa `class Config` de Pydantic v1.
- **`frontend/`** (referenciado por `docker-compose.yml`) es una app React
  anterior a `mcp-dashboard`; decidir cuál sobrevive.

---

## Repositorio

- **Remoto:** `https://github.com/haroldfabla2-hue/SilhouetteAppcreator.git`
- **Rama:** `main`
- **Nunca** versione `.zip`, `__pycache__`, `.env` ni claves. El `.gitignore`
  está en UTF-8 (estuvo en UTF-16, lo que impedía a Git aplicar la primera regla).
