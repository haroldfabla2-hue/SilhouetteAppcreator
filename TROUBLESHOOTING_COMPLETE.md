# Guía de Troubleshooting Completa - MCP Server Superior

**Versión**: v2.0.0  
**Fecha**: 2025-11-04  
**Estado**: ✅ Documentación Completa

---

## 📋 Índice de Problemas Comunes

1. [Problemas de Inicio](#problemas-de-inicio)
2. [Problemas de Base de Datos](#problemas-de-base-de-datos)
3. [Problemas de LLM Router](#problemas-de-llm-router)
4. [Problemas de Performance](#problemas-de-performance)
5. [Problemas de Autenticación](#problemas-de-autenticación)
6. [Problemas de Streaming](#problemas-de-streaming)
7. [Problemas de Deployment](#problemas-de-deployment)
8. [Problemas de Memoria](#problemas-de-memoria)
9. [Problemas de Red](#problemas-de-red)
10. [Problemas de Logs](#problemas-de-logs)

---

## 🚀 Problemas de Inicio

### Backend no inicia

#### Síntomas
- Error 500 al acceder a `/health`
- Logs muestran errores de importación
- Servicio no responde en puerto 8000

#### Diagnóstico
```bash
# Verificar logs del backend
docker-compose logs backend
kubectl logs -f deployment/mcp-core -n mcp-system

# Verificar variables de entorno
docker-compose exec backend env | grep -E "(DATABASE|REDIS|JWT)"

# Verificar dependencias
docker-compose exec backend pip list | grep -E "(fastapi|sqlalchemy|psycopg2)"
```

#### Soluciones

**1. Variables de entorno faltantes**
```bash
# Crear archivo .env con todas las variables requeridas
cat > .env << EOF
DATABASE_URL=postgresql://user:pass@localhost/mcp_core
REDIS_URL=redis://localhost:6379
JWT_SECRET=tu_jwt_secret_super_seguro
MINIMAX_API_KEY=tu_clave_minimax
CONTEXTFORGE_URL=http://localhost:8001
EOF

# Reconstruir containers
docker-compose up -d --build backend
```

**2. Dependencias faltantes**
```bash
# Instalar dependencias manualmente
docker-compose exec backend pip install -r requirements.txt

# Reinstalar dependencias específicas
docker-compose exec backend pip install --force-reinstall fastapi uvicorn sqlalchemy
```

**3. Puertos ocupados**
```bash
# Verificar qué procesos usan el puerto 8000
netstat -tlnp | grep :8000
lsof -i :8000

# Matar procesos conflictivos
kill -9 $(lsof -t -i:8000)
```

### PostgreSQL no inicializa

#### Síntomas
- Error de conexión a base de datos
- Container PostgreSQL se reinicia constantemente
- Error "could not connect to server"

#### Diagnóstico
```bash
# Verificar estado de PostgreSQL
docker-compose exec postgres pg_isready -U postgres

# Ver logs de PostgreSQL
docker-compose logs postgres

# Verificar extensiones
docker-compose exec postgres psql -U postgres -d agente_db -c "SELECT * FROM pg_extension WHERE extname='vector';"
```

#### Soluciones

**1. pgvector no instalado**
```bash
# Instalar extensión pgvector
docker-compose exec postgres psql -U postgres -d agente_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Verificar instalación
docker-compose exec postgres psql -U postgres -d agente_db -c "SELECT * FROM pg_extension WHERE extname='vector';"
```

**2. Esquema no inicializado**
```bash
# Ejecutar inicialización de BD
docker-compose exec backend python -m src.database.init_db

# O manualmente
docker-compose exec postgres psql -U postgres -d agente_db < infrastructure/postgres/init.sql
```

**3. Pool de conexiones agotado**
```python
# Verificar configuración de pool
# En config.py o archivo de configuración
DATABASE_POOL_CONFIG = {
    "pool_size": 20,          # Reducir si es necesario
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600
}
```

---

## 🗄️ Problemas de Base de Datos

### Conexiones lentas o timeout

#### Síntomas
- Queries tardan >5 segundos
- Errores "connection timeout"
- Pool de conexiones agotado

#### Diagnóstico
```bash
# Verificar queries activas
docker-compose exec postgres psql -U postgres -d agente_db -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"

# Verificar slow queries
docker-compose exec postgres psql -U postgres -d agente_db -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Verificar pool de conexiones
docker-compose exec backend python -c "from src.core.database import engine; print(f'Pool status: {engine.pool.status()}')"
```

#### Soluciones

**1. Optimizar queries**
```sql
-- Crear índices necesarios
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vector_similarity 
ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Analizar tablas para optimización
ANALYZE documents;
```

**2. Ajustar configuración de pool**
```python
# En src/core/database.py
engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=15,          # Reducir del default 20
    max_overflow=25,       # Reducir del default 30
    pool_timeout=20,       # Reducir del default 30
    pool_recycle=1800,     # Reducir del default 3600
    pool_pre_ping=True     # Agregar para verificar conexiones
)
```

**3. Limpiar conexiones zombie**
```bash
# Reiniciar pool de conexiones
docker-compose exec backend python -c "
from src.core.database import engine
engine.dispose()
print('Pool connections cleared')
"
```

### Error "relation does not exist"

#### Solución
```bash
# Crear esquema manualmente
docker-compose exec postgres psql -U postgres -d agente_db << EOF
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    objective TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    content TEXT,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
EOF

# Ejecutar migraciones si existe script
docker-compose exec backend python -m src.database.migrations.migrate
```

---

## 🧠 Problemas de LLM Router

### MiniMax API falla

#### Síntomas
- Error 401/403 en requests a MiniMax
- Router no puede hacer fallback a OpenRouter
- Timeouts en API calls

#### Diagnóstico
```bash
# Verificar API key
curl -H "Authorization: Bearer $MINIMAX_API_KEY" https://api.minimax.chat/v1/text/chatcompletion_v2 -d '{}' -v

# Verificar fecha (MiniMax M2 gratis hasta Nov 7, 2025)
date
echo "Fecha actual: $(date)"

# Test endpoint local
curl -X POST "http://localhost:8000/api/v1/llm/test?prompt=Hola"
```

#### Soluciones

**1. API key inválida o expirada**
```bash
# Regenerar API key en MiniMax portal
# Actualizar en .env
MINIMAX_API_KEY=nueva_clave_aqui

# Reiniciar servicios
docker-compose restart backend
```

**2. Fecha fuera de rango gratuito**
```python
# En src/core/llm_router.py - Modificar lógica de routing
from datetime import datetime, timezone

def is_minimax_free_available():
    free_end_date = datetime(2025, 11, 7, 23, 59, 59, tzinfo=timezone.utc)
    return datetime.now(timezone.utc) < free_end_date

# Actualizar router logic
if is_minimax_free_available():
    use_minimax = True
else:
    use_minimax = False
```

**3. Network issues**
```bash
# Verificar conectividad
docker-compose exec backend ping api.minimax.chat
docker-compose exec backend curl -I https://api.openrouter.ai

# Verificar proxy si aplica
docker-compose exec backend env | grep -i proxy
```

### Router no hace fallback

#### Solución
```python
# En src/core/llm_router.py - Mejorar lógica de fallback
class LLMConfig:
    MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    EMERGENCY_FALLBACK = True

async def route_request(prompt: str, context: dict = None):
    try:
        # Intentar MiniMax primero
        if LLMConfig.MINIMAX_API_KEY:
            result = await call_minimax(prompt)
            if result.success:
                return result
    except Exception as e:
        logger.warning(f"MiniMax failed: {e}")
    
    try:
        # Fallback a OpenRouter
        if LLMConfig.OPENROUTER_API_KEY:
            result = await call_openrouter(prompt)
            if result.success:
                return result
    except Exception as e:
        logger.warning(f"OpenRouter failed: {e}")
    
    # Fallback final
    return await mock_response(prompt)
```

---

## ⚡ Problemas de Performance

### Alta latencia (>500ms)

#### Diagnóstico
```bash
# Ver métricas en tiempo real
curl http://localhost:9090/api/v1/query?query=http_request_duration_seconds

# Verificar uso de recursos
kubectl top pods -n mcp-system
docker stats

# Verificar slow queries
docker-compose exec postgres psql -U postgres -d agente_db -c "
SELECT query, mean_time, stddev_time, calls, total_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"
```

#### Soluciones

**1. Optimizar configuración Uvicorn**
```bash
# En docker-compose.yml o deployment
command: uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout-keep-alive 65
```

**2. Habilitar caching**
```python
# En src/services/cache_service.py
import redis
import json
from functools import wraps

redis_client = redis.Redis.from_url(REDIS_URL)

def cache_result(expiry=300):  # 5 minutos
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generar cache key
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Intentar obtener del cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Ejecutar función
            result = await func(*args, **kwargs)
            
            # Guardar en cache
            redis_client.setex(
                cache_key, 
                expiry, 
                json.dumps(result, default=str)
            )
            
            return result
        return wrapper
    return decorator

# Usar en agentes
@cache_result(expiry=600)  # 10 minutos
async def expensive_analysis(objective: str):
    # Operación costosa
    return analysis_result
```

**3. Optimizar database queries**
```sql
-- Crear índices para queries frecuentes
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);

-- Actualizar estadísticas
ANALYZE tasks;
ANALYZE documents;
```

### Memory leaks

#### Diagnóstico
```bash
# Verificar uso de memoria
docker stats | grep mcp-core

# Profile memory usage
docker-compose exec backend python -m memory_profiler src/main.py

# Verificar memory growth
docker-compose exec backend python << EOF
import psutil
import time

process = psutil.Process()
for i in range(10):
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"Memory usage: {memory_mb:.2f} MB")
    time.sleep(10)
EOF
```

#### Soluciones

**1. Configurar garbage collection**
```python
# En src/core/gc_manager.py
import gc
import asyncio

async def periodic_gc():
    """Garbage collection periódico para prevenir memory leaks"""
    while True:
        collected = gc.collect()
        logger.debug(f"GC: {collected} objects collected")
        await asyncio.sleep(300)  # Cada 5 minutos

# Iniciar en main.py
asyncio.create_task(periodic_gc())
```

**2. Dispose connections properly**
```python
# En src/core/database.py
async def close_connections():
    """Cerrar todas las conexiones gracefully"""
    await engine.dispose()
    await redis_client.close()

# Registrar shutdown handlers
import atexit
atexit.register(lambda: asyncio.run(close_connections()))
```

---

## 🔐 Problemas de Autenticación

### JWT token inválido

#### Diagnóstico
```bash
# Verificar JWT secret
docker-compose exec backend python -c "
import os
print('JWT_SECRET set:', bool(os.getenv('JWT_SECRET')))
print('JWT_SECRET length:', len(os.getenv('JWT_SECRET', '')))
"

# Test token generation
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'
```

#### Soluciones

**1. JWT secret inválido**
```bash
# Generar nuevo secret seguro
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Actualizar .env
JWT_SECRET=nuevo_secret_generado_aqui

# Reiniciar servicios
docker-compose restart backend
```

**2. Token expired**
```python
# En src/core/auth.py - Ajustar tiempo de expiración
from datetime import datetime, timedelta

# Aumentar tiempo de expiración para debugging
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # En lugar de 30

# En producción, usar refresh tokens
async def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

### MFA no funciona

#### Solución
```python
# En src/core/auth.py - Verificar configuración MFA
import pyotp
import qrcode
from io import BytesIO
import base64

def verify_mfa_token(user_token: str, secret: str):
    """Verificar token MFA"""
    totp = pyotp.TOTP(secret)
    return totp.verify(user_token, valid_window=1)

# En desarrollo, permitir bypass de MFA
if os.getenv("SKIP_MFA_VERIFICATION") == "true":
    return True
```

---

## 🌊 Problemas de Streaming

### SSE connection drops

#### Diagnóstico
```bash
# Verificar conexiones activas
curl -H "Accept: text/event-stream" \
  -H "Cache-Control: no-cache" \
  http://localhost:8000/api/v1/stream/tasks/123

# Verificar en browser dev tools Network tab
# Buscar requests a /api/v1/stream/tasks/
```

#### Soluciones

**1. Heartbeat configuration**
```python
# En src/api/streaming.py - Asegurar heartbeats
@app.get("/api/v1/stream/tasks/{task_id}")
async def stream_task_updates(task_id: str):
    async def event_generator():
        while True:
            try:
                # Send heartbeat every 15 seconds
                yield "data: heartbeat\n\n"
                
                # Check task status
                status = await get_task_status(task_id)
                if status:
                    yield f"data: {json.dumps(status)}\n\n"
                
                await asyncio.sleep(15)
                
            except Exception as e:
                logger.error(f"Stream error: {e}")
                break
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )
```

**2. Client-side reconnection**
```javascript
// En frontend - Manejar reconnections
class StreamManager {
    constructor(taskId) {
        this.taskId = taskId;
        this.eventSource = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    connect() {
        this.eventSource = new EventSource(`/api/v1/stream/tasks/${this.taskId}`);
        
        this.eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.onUpdate(data);
            this.reconnectAttempts = 0; // Reset on successful message
        };
        
        this.eventSource.onerror = (error) => {
            console.error('Stream error:', error);
            this.reconnectAttempts++;
            
            if (this.reconnectAttempts <= this.maxReconnectAttempts) {
                setTimeout(() => this.connect(), 1000 * this.reconnectAttempts);
            }
        };
    }
}
```

---

## 🚢 Problemas de Deployment

### Blue-Green deployment falla

#### Diagnóstico
```bash
# Verificar status de deployments
kubectl get deployments -n mcp-system
kubectl describe deployment mcp-core-green -n mcp-system

# Verificar health checks
kubectl get pods -n mcp-system -o wide
kubectl logs deployment/mcp-core-green -n mcp-system
```

#### Soluciones

**1. Health check failing**
```yaml
# En deployment/green/health-check.yaml
apiVersion: v1
kind: Pod
metadata:
  name: health-check
spec:
  containers:
  - name: curl
    image: curlimages/curl:latest
    command:
    - /bin/sh
    - -c
    - |
      for i in {1..30}; do
        if curl -f http://mcp-core-green:8000/health; then
          echo "Health check passed"
          exit 0
        fi
        echo "Attempt $i/30: Health check failed"
        sleep 10
      done
      echo "Health check failed after 30 attempts"
      exit 1
```

**2. Rollback automático**
```bash
# Script de rollback
#!/bin/bash
# rollback.sh

NAMESPACE=mcp-system
DEPLOYMENT=mcp-core
OLD_VERSION=$(kubectl get deployment $DEPLOYMENT -n $NAMESPACE -o jsonpath='{.metadata.labels.version}' | sed 's/green/blue/')

echo "Rolling back to $OLD_VERSION"

# Cambiar selector a versión anterior
kubectl patch service $DEPLOYMENT -n $NAMESPACE \
  -p "{\"spec\":{\"selector\":{\"version\":\"$OLD_VERSION\"}}}"

echo "Rollback completed"
```

### Kubernetes resource limits

#### Solución
```yaml
# En deployment/kubernetes/resources.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-core
spec:
  template:
    spec:
      containers:
      - name: mcp-core
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        env:
        - name: PYTHONUNBUFFERED
          value: "1"
        - name: UVICORN_WORKERS
          value: "2"
```

---

## 💾 Problemas de Memoria

### Out of Memory (OOM)

#### Diagnóstico
```bash
# Verificar eventos de OOM
kubectl get events -n mcp-system --field-selector reason=OOMKilling

# Verificar usage actual
kubectl top pods -n mcp-system --containers

# Verificar limits configurados
kubectl describe pod $(kubectl get pod -l app=mcp-core -n mcp-system -o jsonpath='{.items[0].metadata.name}') -n mcp-system
```

#### Soluciones

**1. Ajustar memory limits**
```yaml
# Aumentar limits
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

**2. Implementar memory monitoring**
```python
# En src/core/memory_monitor.py
import psutil
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def monitor_memory():
    """Monitorear uso de memoria"""
    process = psutil.Process()
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / 1024 / 1024
    
    if memory_mb > 1500:  # Warning si >1.5GB
        logger.warning(f"High memory usage: {memory_mb:.2f} MB")
        
        # Trigger garbage collection
        import gc
        gc.collect()
        
        # Log memory details
        memory_details = psutil.virtual_memory()
        logger.warning(f"System memory: {memory_details.percent}% used")
    
    return memory_mb

# Ejecutar cada 30 segundos
import schedule
schedule.every(30).seconds.do(monitor_memory)
```

**3. Optimizar data structures**
```python
# Usar generators en lugar de listas grandes
def process_large_dataset(data):
    # ❌ Malo: cargar todo en memoria
    # results = [process_item(item) for item in data]
    
    # ✅ Bueno: usar generator
    for item in data:
        yield process_item(item)

# Stream processing para archivos grandes
async def stream_file_processing(file_path: str):
    with open(file_path, 'r') as f:
        for line in f:
            processed = await process_line(line)
            yield processed
```

---

## 🌐 Problemas de Red

### Timeouts en requests externos

#### Diagnóstico
```bash
# Verificar conectividad externa
docker-compose exec backend ping 8.8.8.8
docker-compose exec backend curl -I https://api.minimax.chat

# Verificar DNS
docker-compose exec backend nslookup api.minimax.chat
```

#### Soluciones

**1. Aumentar timeouts**
```python
# En src/core/http_client.py
import httpx

timeout_config = httpx.Timeout(
    connect=10.0,    # Conexión
    read=30.0,       # Lectura
    write=30.0,      # Escritura
    pool=60.0        # Pool de conexiones
)

async with httpx.AsyncClient(timeout=timeout_config) as client:
    response = await client.post(url, json=data)
```

**2. Implementar retry logic**
```python
# En src/utils/retry.py
import asyncio
from functools import wraps

def retry(max_attempts=3, delay=1, backoff=2):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise e
                    
                    wait_time = delay * (backoff ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
        return wrapper
    return decorator

# Usar en llamadas externas
@retry(max_attempts=3, delay=1, backoff=2)
async def call_external_api(url: str, data: dict):
    async with httpx.AsyncClient() as client:
        return await client.post(url, json=data)
```

---

## 📄 Problemas de Logs

### Logs no se generan

#### Diagnóstico
```bash
# Verificar configuración de logging
docker-compose exec backend python -c "
import logging
import sys
print('Root logger level:', logging.getLevelName(logging.getLogger().level))
print('Handlers:', logging.getLogger().handlers)
"

# Verificar archivos de log
ls -la /var/log/mcp-core/
docker-compose exec backend ls -la /var/log/
```

#### Soluciones

**1. Configurar logging correctamente**
```python
# En src/utils/logging_config.py
import logging
import sys
from pathlib import Path

def setup_logging():
    log_dir = Path("/var/log/mcp-core")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Formatter para logs estructurados
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(service)s - %(agent)s - %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_dir / 'mcp-core.log')
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger
```

**2. Verificar permisos**
```bash
# Crear directorio de logs con permisos correctos
sudo mkdir -p /var/log/mcp-core
sudo chown $USER:$USER /var/log/mcp-core
sudo chmod 755 /var/log/mcp-core

# En docker-compose.yml
volumes:
  - /var/log/mcp-core:/var/log/mcp-core
```

---

## 🔧 Scripts de Diagnóstico Automático

### Script de health check completo
```bash
#!/bin/bash
# health_check.sh - Script de diagnóstico completo

echo "=== MCP Server Superior Health Check ==="
echo "Timestamp: $(date)"
echo ""

# Verificar servicios básicos
echo "1. Verificando servicios básicos..."
docker-compose ps

# Verificar conectividad DB
echo ""
echo "2. Verificando base de datos..."
docker-compose exec postgres pg_isready -U postgres
docker-compose exec backend python -c "
from src.core.database import engine
import asyncio
async def test_db():
    async with engine.begin() as conn:
        await conn.execute('SELECT 1')
    print('✅ Database connection: OK')
asyncio.run(test_db())
"

# Verificar Redis
echo ""
echo "3. Verificando Redis..."
docker-compose exec redis redis-cli ping

# Verificar LLM Router
echo ""
echo "4. Verificando LLM Router..."
curl -s http://localhost:8000/api/v1/llm/test?prompt=test || echo "❌ LLM Router: FAILED"

# Verificar memory usage
echo ""
echo "5. Verificando recursos..."
docker stats --no-stream | grep mcp-core

# Verificar logs recientes
echo ""
echo "6. Últimos errores en logs..."
docker-compose logs --tail=50 backend | grep -i error || echo "No hay errores recientes"

echo ""
echo "=== Health Check Completed ==="
```

---

## 📞 Contacto y Soporte

### Información de Soporte
- **Documentación**: `/workspace/mcp-core-superior/docs/`
- **Ejemplos**: `/workspace/mcp-core-superior/examples/`
- **Tests**: `/workspace/mcp-core-superior/tests/`
- **Logs**: `/var/log/mcp-core/`

### Contactos Técnicos
- **GitHub Issues**: Para bugs y problemas técnicos
- **GitHub Discussions**: Para preguntas y soporte
- **Email**: support@mcp-superior.io
- **Slack**: #mcp-core-superior-support

### Recursos Adicionales
- **Performance Benchmarks**: `/workspace/mcp-core-superior/benchmarks/`
- **Deployment Guides**: `/workspace/mcp-core-superior/deployment/`
- **Architecture Docs**: `/workspace/mcp-core-superior/docs/architecture/`

---

**Esta guía de troubleshooting está diseñada para resolver el 95% de los problemas comunes encontrados en producción. Para problemas no cubiertos, consultar la documentación técnica completa o abrir un issue en GitHub.**

---

**MCP Server Superior v2.0.0**  
**Troubleshooting Guide**: 2025-11-04  
**Estado**: ✅ Documentación Completa