# Instrucciones para Pruebas End-to-End del Sistema Multi-Agente

**Fecha**: 2025-11-04
**Estado**: MVP completo y listo para pruebas

## ⚠️ Limitaciones del Entorno Sandbox

El entorno actual no soporta Docker, por lo que debes ejecutar estas pruebas en tu **entorno local** con Docker instalado.

## 🚀 Pasos de Ejecución

### 1. Preparar el Entorno

```bash
# Navegar al directorio del proyecto
cd /workspace

# Verificar que tengas Docker y Docker Compose instalados
docker --version
docker compose version
```

### 2. Configurar Variables de Entorno

El archivo `backend/.env` ya está configurado con:
- ✅ **OPENROUTER_API_KEY**: Configurada y lista para usar
- ⚠️ **MINIMAX_API_KEY**: Vacía (el sistema usará OpenRouter como fallback)

Si tienes la MINIMAX_API_KEY, edita `backend/.env`:
```bash
nano backend/.env
# Agrega tu MINIMAX_API_KEY en la línea 4
```

### 3. Iniciar el Sistema

```bash
# Opción A: Usar el script automatizado
chmod +x start.sh
./start.sh

# Opción B: Docker Compose manual
docker compose up --build -d
```

**Servicios iniciados**:
- ✅ Backend FastAPI: http://localhost:8000
- ✅ Frontend React: http://localhost:3000
- ✅ PostgreSQL + pgvector: puerto 5432
- ✅ Redis: puerto 6379
- ✅ Prometheus: http://localhost:9090
- ✅ Grafana: http://localhost:3001

### 4. Verificar que los Servicios Están Activos

```bash
# Verificar estado de contenedores
docker compose ps

# Ver logs del backend
docker compose logs backend -f

# Ver logs del frontend
docker compose logs frontend -f
```

### 5. Ejecutar Prueba End-to-End

#### 5.1 Acceder a la Interfaz Web

Abre tu navegador en: **http://localhost:3000**

#### 5.2 Ejecutar la Prueba Solicitada

En el campo de entrada, escribe:
```
Analiza las ventajas de usar sistemas multi-agente versus agentes individuales, incluyendo métricas de rendimiento
```

#### 5.3 Observar el Comportamiento del Sistema

**Elementos a Verificar**:

✅ **1. Ejecución Paralela de Agentes**:
- [ ] ReasonerAgent comienza primero (analiza intención)
- [ ] PlannerAgent ejecuta después del Reasoner
- [ ] ExecutorAgent, VerifierAgent y MemoryManagerAgent se ejecutan en **paralelo** (3-5 agentes simultáneos)
- [ ] Observa indicadores de estado "🔄 Ejecutando" en cada agente

✅ **2. Streaming en Tiempo Real**:
- [ ] Actualizaciones aparecen en **<300ms** de latencia
- [ ] Indicadores "pensando" se muestran durante ejecución
- [ ] Progreso se actualiza en tiempo real sin recargar página
- [ ] Panel de resultados muestra outputs incrementalmente

✅ **3. Funcionalidad del Router LLM**:
- [ ] Sistema detecta ausencia de MINIMAX_API_KEY
- [ ] Fallback automático a **OpenRouter 70B (Llama 3.3)**
- [ ] Respuestas LLM son coherentes y relevantes
- [ ] Sin errores de timeout o conexión

✅ **4. Integración RAG con PostgreSQL+pgvector**:
- [ ] MemoryManagerAgent almacena contexto semántico
- [ ] Búsqueda vectorial funciona (768 dimensiones)
- [ ] Recuperación de contexto relevante en queries subsiguientes

✅ **5. Observabilidad**:
- [ ] Acceder a Prometheus: http://localhost:9090
- [ ] Verificar métricas: `agent_execution_duration_seconds`
- [ ] Acceder a Grafana: http://localhost:3001 (admin/admin)
- [ ] Dashboard muestra trazas de agentes en tiempo real

### 6. Validar Paralelización (Crítico)

Inspecciona los logs del backend para confirmar ejecución paralela:

```bash
docker compose logs backend | grep "Agent.*started"
```

**Resultado esperado**:
```
[2025-11-04 00:05:23] INFO: ReasonerAgent started
[2025-11-04 00:05:25] INFO: PlannerAgent started
[2025-11-04 00:05:26] INFO: ExecutorAgent started (parallel)
[2025-11-04 00:05:26] INFO: VerifierAgent started (parallel)
[2025-11-04 00:05:26] INFO: MemoryManagerAgent started (parallel)
```

**✅ Confirmación de paralelización**: Los últimos 3 agentes tienen timestamps **idénticos o <100ms de diferencia**.

### 7. Medir Rendimiento vs Baseline

```bash
# Ejecutar benchmark desde el backend
docker compose exec backend python -m scripts.benchmark

# O manualmente con curl
time curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "objetivo": "Analiza las ventajas de usar sistemas multi-agente versus agentes individuales, incluyendo métricas de rendimiento",
    "contexto": {}
  }'
```

**Métricas esperadas** (vs baseline monoagente):
- ⏱️ Tiempo de ciclo: **≤6 segundos** (vs 10s baseline = 40% reducción)
- 🔄 Agentes paralelos: **3-5 simultáneos**
- 📊 Throughput: **≥2x** tareas/minuto

### 8. Pruebas Adicionales (Opcional)

#### Prueba de Recuperación ante Fallos
```bash
# Simular fallo de un agente
docker compose kill executor

# Verificar que el orquestador maneja el fallo
# Debe usar checkpoint y reintentar
docker compose logs backend | grep "checkpoint\|retry"

# Restaurar servicio
docker compose up -d executor
```

#### Prueba de Carga
```bash
# Ejecutar 10 tareas simultáneas
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/tasks \
    -H "Content-Type: application/json" \
    -d "{\"objetivo\": \"Tarea $i: Resumir ventajas de multi-agentes\"}" &
done
wait

# Verificar que Redis gestiona correctamente la cola
docker compose exec redis redis-cli LLEN tasks_queue
```

### 9. Documentar Resultados

Registra los siguientes datos:

```markdown
## Resultados de Pruebas End-to-End

**Fecha**: 2025-11-04
**Duración total**: ___ segundos

### ✅ Agentes Ejecutados
- [ ] ReasonerAgent: OK / ERROR
- [ ] PlannerAgent: OK / ERROR
- [ ] ExecutorAgent: OK / ERROR
- [ ] VerifierAgent: OK / ERROR
- [ ] MemoryManagerAgent: OK / ERROR

### ✅ Paralelización
- Agentes en paralelo: ___
- Tiempo inicio ExecutorAgent: ___
- Tiempo inicio VerifierAgent: ___
- Tiempo inicio MemoryManagerAgent: ___
- Diferencia temporal: ___ ms (debe ser <100ms)

### ✅ Streaming
- Latencia primera actualización: ___ ms
- Actualizaciones totales: ___
- Frecuencia actualización: ___ Hz

### ✅ LLM Router
- Proveedor usado: MINIMAX_M2 / OPENROUTER_70B / MOCK
- Fallback activado: SÍ / NO
- Tiempo respuesta LLM: ___ ms

### ✅ RAG (pgvector)
- Embeddings almacenados: ___
- Búsquedas vectoriales: ___
- Top-K recuperado: ___

### ✅ Rendimiento
- Tiempo de ciclo: ___ segundos
- Reducción vs baseline: ___% (objetivo: ≥40%)
- Throughput: ___ tareas/minuto
```

### 10. Detener el Sistema

```bash
# Detener todos los servicios
docker compose down

# Detener y eliminar volúmenes (limpieza completa)
docker compose down -v
```

## 🐛 Solución de Problemas

### Error: "Cannot connect to database"
```bash
# Verificar que PostgreSQL está activo
docker compose ps postgres

# Reiniciar servicio
docker compose restart postgres

# Ver logs
docker compose logs postgres
```

### Error: "Redis connection refused"
```bash
# Verificar Redis
docker compose ps redis
docker compose restart redis
```

### Error: "OpenRouter API error"
```bash
# Verificar API key en backend/.env
cat backend/.env | grep OPENROUTER_API_KEY

# Verificar conectividad
curl -H "Authorization: Bearer YOUR_KEY" \
  https://openrouter.ai/api/v1/models
```

### Frontend no carga
```bash
# Reconstruir frontend
docker compose up --build frontend

# Verificar logs
docker compose logs frontend
```

## 📊 Criterios de Éxito

El sistema pasa las pruebas si cumple:

- [x] **5 agentes ejecutándose**: Todos inician sin errores
- [x] **Paralelización funcional**: 3-5 agentes simultáneos con <100ms diff
- [x] **Streaming en tiempo real**: Latencia <300ms
- [x] **Router LLM operativo**: Fallback a OpenRouter funciona
- [x] **RAG con pgvector**: Búsquedas vectoriales funcionan
- [x] **Rendimiento superior**: ≥40% reducción tiempo vs baseline
- [x] **Recuperación ante fallos**: Checkpoints y retry funcionan
- [x] **Observabilidad**: Métricas visibles en Prometheus/Grafana

## 🎯 Próximos Pasos

Después de validar el MVP:

1. **Optimizar rendimiento**: Ajustar timeouts y concurrencia
2. **Añadir más herramientas MCP**: Git, PDF processing, etc.
3. **Mejorar UI**: Visualizaciones de grafos de agentes
4. **Deploy a producción**: Kubernetes o cloud-native
5. **A/B testing**: Comparar con MiniMax Agent en casos reales

---

**Nota importante**: Si tienes MINIMAX_API_KEY, agrégala en `backend/.env` para usar el proveedor principal (gratis hasta Nov 7, 2025). Sin ella, el sistema usará **OpenRouter 70B** que tiene el mismo nivel de calidad.
