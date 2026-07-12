# Deployment Guide

## Overview

Esta guía cubre todas las opciones de despliegue para MCP Core Superior, desde desarrollo local hasta producción enterprise-grade. Incluye configuraciones optimizadas para diferentes entornos y estrategias de escalabilidad.

## 🎯 Estrategias de Despliegue

### Comparación de Opciones
| Opción | Complexity | Scalability | Cost | Best For |
|--------|------------|-------------|------|----------|
| **Docker Compose** | ⭐ | ⭐⭐ | ⭐⭐⭐ | Desarrollo, Testing |
| **Docker Swarm** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Small-Medium Production |
| **Kubernetes** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | Enterprise Production |
| **Serverless** | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Variable Load |
| **Hybrid** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | Complex Systems |

## 🐳 Docker Deployment

### Production Docker Image

**Dockerfile**
```dockerfile
# Multi-stage build para optimizar tamaño
FROM python:3.11-slim as builder

# Instalar build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Stage final
FROM python:3.11-slim as runtime

# Instalar runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN groupadd --gid 1000 mcpuser \
    && useradd --uid 1000 --gid mcpuser --shell /bin/bash --create-home mcpuser

# Copiar virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar aplicación
COPY --chown=mcpuser:mcpuser . /app
WORKDIR /app

# Crear directorios necesarios
RUN mkdir -p /app/logs /app/data /app/models \
    && chown -R mcpuser:mcpuser /app

# Usuario no-root
USER mcpuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Exponer puertos
EXPOSE 8080

# Variables de entorno por defecto
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Comando por defecto
CMD ["uvicorn", "src.core.fastmcp_server:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
```

### Production Docker Compose

**docker-compose.prod.yml**
```yaml
version: '3.8'

services:
  # MCP Core Superior
  mcp-core-superior:
    image: mcp-core-superior:v2.0.0
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - VECTOR_DB_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres-vector:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379/0
      - RABBITMQ_URL=amqp://${RABBITMQ_USER}:${RABBITMQ_PASSWORD}@rabbitmq:5672/
      - CONTEXTFORGE_URL=${CONTEXTFORGE_URL}
      - JWT_SECRET=${JWT_SECRET}
      - MCP_MAX_CONCURRENT_TASKS=10
      - MCP_TASK_TIMEOUT=600
      - STREAMING_ENABLED=true
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs:rw
      - ./models:/app/models:ro
      - ./config:/app/config:ro
    depends_on:
      postgres:
        condition: service_healthy
      postgres-vector:
        condition: service_healthy
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.5'
        reservations:
          memory: 1G
          cpus: '0.5'
    networks:
      - mcp-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s

  # PostgreSQL Primary
  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8 --lc-collate=C --lc-ctype=C
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init-prod.sql:/docker-entrypoint-initdb.d/init.sql:ro
      - ./database/postgresql.conf:/etc/postgresql/postgresql.conf:ro
    ports:
      - "5432:5432"
    networks:
      - mcp-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
        reservations:
          memory: 2G
          cpus: '1'

  # PostgreSQL Vector (Read Replica)
  postgres-vector:
    image: pgvector/pgvector:pg15
    restart: unless-stopped
    environment:
      - POSTGRES_DB=${POSTGRES_DB}_vector
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8 --lc-collate=C --lc-ctype=C
    volumes:
      - postgres_vector_data:/var/lib/postgresql/data
      - ./database/init-vector.sql:/docker-entrypoint-initdb.d/init.sql:ro
    ports:
      - "5433:5432"
    networks:
      - mcp-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}_vector"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
        reservations:
          memory: 2G
          cpus: '1'

  # Redis Cluster
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - mcp-network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'

  # RabbitMQ
  rabbitmq:
    image: rabbitmq:3.12-management-alpine
    restart: unless-stopped
    environment:
      - RABBITMQ_DEFAULT_USER=${RABBITMQ_USER}
      - RABBITMQ_DEFAULT_PASS=${RABBITMQ_PASSWORD}
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
      - ./config/rabbitmq.conf:/etc/rabbitmq/rabbitmq.conf:ro
    ports:
      - "5672:5672"
      - "15672:15672"
    networks:
      - mcp-network
    healthcheck:
      test: rabbitmq-diagnostics -q ping
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'

  # NGINX Load Balancer
  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./config/nginx/conf.d:/etc/nginx/conf.d:ro
      - ./ssl:/etc/nginx/ssl:ro
      - nginx_logs:/var/log/nginx
    depends_on:
      - mcp-core-superior
    networks:
      - mcp-network
    healthcheck:
      test: ["CMD", "nginx", "-t"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
    driver: local
  postgres_vector_data:
    driver: local
  redis_data:
    driver: local
  rabbitmq_data:
    driver: local
  nginx_logs:
    driver: local

networks:
  mcp-network:
    driver: bridge
```

### Environment Variables Production

**.env.production**
```bash
# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database
POSTGRES_DB=mcp_core_production
POSTGRES_USER=mcp_prod_user
POSTGRES_PASSWORD=secure_production_password_2024
DATABASE_URL=postgresql://mcp_prod_user:secure_production_password_2024@postgres:5432/mcp_core_production
VECTOR_DB_URL=postgresql://mcp_prod_user:secure_production_password_2024@postgres-vector:5432/mcp_core_production

# Redis
REDIS_PASSWORD=secure_redis_password_2024
REDIS_URL=redis://:secure_redis_password_2024@redis:6379/0

# Message Queue
RABBITMQ_USER=mcp_rabbit_user
RABBITMQ_PASSWORD=secure_rabbit_password_2024

# Security
JWT_SECRET=your-super-secure-jwt-secret-key-for-production-2024
ENCRYPTION_KEY=your-encryption-key-for-sensitive-data

# External Services
CONTEXTFORGE_URL=https://contextforge.yourdomain.com
CONTEXTFORGE_API_KEY=your-contextforge-api-key

# MCP Configuration
MCP_MAX_CONCURRENT_TASKS=10
MCP_TASK_TIMEOUT=600
MCP_MAX_MEMORY_MB=2048

# Streaming
STREAMING_ENABLED=true
STREAMING_BUFFER_SIZE=5000
STREAMING_UPDATE_INTERVAL=2

# Performance
WORKERS=4
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=100
KEEPALIVE_TIMEOUT=65
TIMEOUT=120

# Monitoring
PROMETHEUS_PORT=9090
JAEGER_COLLECTOR_URL=http://jaeger-collector:14268/api/traces
SENTRY_DSN=your-sentry-dsn

# SSL/TLS
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem

# Backup
BACKUP_ENABLED=true
BACKUP_SCHEDULE="0 2 * * *"  # Daily at 2 AM
BACKUP_RETENTION_DAYS=30
```

### Deployment Script

**deploy.sh**
```bash
#!/bin/bash
set -e

# Deploy script para producción
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="mcp-core-superior"
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.production"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que el archivo de entorno existe
if [ ! -f "$ENV_FILE" ]; then
    log_error "Archivo de entorno no encontrado: $ENV_FILE"
    exit 1
fi

# Cargar variables de entorno
source "$ENV_FILE"

# Función para verificar servicios
check_services() {
    log_info "Verificando servicios externos..."
    
    # Verificar que PostgreSQL esté disponible
    if ! pg_isready -h localhost -p 5432 -U "$POSTGRES_USER" > /dev/null 2>&1; then
        log_error "PostgreSQL no está disponible"
        exit 1
    fi
    
    # Verificar que Redis esté disponible
    if ! redis-cli -h localhost -p 6379 ping > /dev/null 2>&1; then
        log_error "Redis no está disponible"
        exit 1
    fi
    
    log_info "Servicios externos verificados correctamente"
}

# Función para hacer backup
backup_database() {
    if [ "$BACKUP_ENABLED" = "true" ]; then
        log_info "Creando backup de la base de datos..."
        
        BACKUP_DIR="./backups"
        mkdir -p "$BACKUP_DIR"
        
        BACKUP_FILE="$BACKUP_DIR/mcp_core_backup_$(date +%Y%m%d_%H%M%S).sql"
        
        pg_dump -h localhost -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "$BACKUP_FILE"
        
        if [ $? -eq 0 ]; then
            log_info "Backup creado: $BACKUP_FILE"
        else
            log_error "Error al crear backup"
            exit 1
        fi
        
        # Limpiar backups antiguos
        find "$BACKUP_DIR" -name "*.sql" -mtime +$BACKUP_RETENTION_DAYS -delete
    fi
}

# Función para desplegar
deploy() {
    log_info "Iniciando despliegue de $PROJECT_NAME..."
    
    # Construir imágenes
    log_info "Construyendo imágenes Docker..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build --no-cache
    
    # Levantar servicios
    log_info "Levantando servicios..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    # Esperar a que los servicios estén listos
    log_info "Esperando a que los servicios estén listos..."
    sleep 30
    
    # Verificar health check
    log_info "Verificando health checks..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
    
    # Ejecutar migraciones de BD si es necesario
    log_info "Ejecutando migraciones de base de datos..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T mcp-core-superior alembic upgrade head
    
    log_info "Despliegue completado exitosamente"
}

# Función para mostrar logs
show_logs() {
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs -f
}

# Función para limpiar
cleanup() {
    log_warn "Deteniendo y eliminando contenedores..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
    
    log_info "Limpieza completada"
}

# Menú de opciones
case "${1:-deploy}" in
    "deploy")
        check_services
        backup_database
        deploy
        ;;
    "logs")
        show_logs
        ;;
    "cleanup")
        cleanup
        ;;
    "backup")
        backup_database
        ;;
    *)
        echo "Uso: $0 {deploy|logs|cleanup|backup}"
        exit 1
        ;;
esac
```

## ☸️ Kubernetes Deployment

### Namespace y RBAC

**namespace.yaml**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: mcp-core-superior
  labels:
    name: mcp-core-superior
    environment: production
```

**rbac.yaml**
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: mcp-core-superior
  namespace: mcp-core-superior
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: mcp-core-superior
  name: mcp-core-superior-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "endpoints"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: mcp-core-superior-rolebinding
  namespace: mcp-core-superior
subjects:
- kind: ServiceAccount
  name: mcp-core-superior
  namespace: mcp-core-superior
roleRef:
  kind: Role
  name: mcp-core-superior-role
  apiGroup: rbac.authorization.k8s.io
```

### ConfigMaps y Secrets

**configmap.yaml**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mcp-core-superior-config
  namespace: mcp-core-superior
data:
  # Configuración general
  ENVIRONMENT: "production"
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  
  # MCP Configuration
  MCP_MAX_CONCURRENT_TASKS: "10"
  MCP_TASK_TIMEOUT: "600"
  STREAMING_ENABLED: "true"
  
  # Performance
  WORKERS: "4"
  MAX_REQUESTS: "1000"
  KEEPALIVE_TIMEOUT: "65"
  
  # Monitoring
  PROMETHEUS_ENABLED: "true"
  JAEGER_ENABLED: "true"
  
  # Database
  POSTGRES_INIT: "true"
  VECTOR_DB_ENABLED: "true"
  
  # Redis
  REDIS_SENTINEL_MODE: "false"
  
  # External Services
  CONTEXTFORGE_URL: "https://contextforge.yourdomain.com"
  
  # NGINX Configuration
  NGINX_WORKER_PROCESSES: "auto"
  NGINX_WORKER_CONNECTIONS: "1024"
```

**secrets.yaml**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mcp-core-superior-secrets
  namespace: mcp-core-superior
type: Opaque
stringData:
  # Database
  DATABASE_URL: "postgresql://username:password@postgres-service:5432/mcp_core"
  VECTOR_DB_URL: "postgresql://username:password@postgres-vector-service:5432/mcp_vector"
  
  # Redis
  REDIS_URL: "redis://:password@redis-service:6379/0"
  
  # Security
  JWT_SECRET: "your-jwt-secret-key"
  ENCRYPTION_KEY: "your-encryption-key"
  
  # External APIs
  CONTEXTFORGE_API_KEY: "your-contextforge-api-key"
  
  # Monitoring
  SENTRY_DSN: "your-sentry-dsn"
  JAEGER_COLLECTOR_URL: "http://jaeger-collector:14268/api/traces"
```

### PostgreSQL Deployment

**postgres-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: mcp-core-superior
spec:
  serviceName: postgres-service
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          valueFrom:
            configMapKeyRef:
              name: mcp-core-superior-config
              key: POSTGRES_DB
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: mcp-core-superior-secrets
              key: DATABASE_URL
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mcp-core-superior-secrets
              key: DATABASE_URL
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        - name: init-scripts
          mountPath: /docker-entrypoint-initdb.d
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - $(POSTGRES_USER)
            - -d
            - $(POSTGRES_DB)
          initialDelaySeconds: 60
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - $(POSTGRES_USER)
            - -d
            - $(POSTGRES_DB)
          initialDelaySeconds: 30
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
      storageClassName: fast-ssd
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: mcp-core-superior
spec:
  type: ClusterIP
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
    name: postgres
```

### Redis Deployment

**redis-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: mcp-core-superior
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command:
        - redis-server
        - --requirepass
        - $(REDIS_PASSWORD)
        - --appendonly
        - "yes"
        - --maxmemory
        - "512mb"
        - --maxmemory-policy
        - "allkeys-lru"
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mcp-core-superior-secrets
              key: REDIS_PASSWORD
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-storage
          mountPath: /data
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - redis-cli
            - -a
            - $(REDIS_PASSWORD)
            - ping
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - redis-cli
            - -a
            - $(REDIS_PASSWORD)
            - ping
          initialDelaySeconds: 5
          periodSeconds: 5
  volumes:
  - name: redis-storage
    emptyDir:
      sizeLimit: 1Gi
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: mcp-core-superior
spec:
  type: ClusterIP
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
    name: redis
```

### MCP Core Superior Deployment

**mcp-core-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-core-superior
  namespace: mcp-core-superior
  labels:
    app: mcp-core-superior
    version: v2.0.0
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: mcp-core-superior
  template:
    metadata:
      labels:
        app: mcp-core-superior
        version: v2.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: mcp-core-superior
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: mcp-core-superior
        image: mcp-core-superior:v2.0.0
        ports:
        - containerPort: 8080
          name: http
          protocol: TCP
        - containerPort: 9090
          name: metrics
          protocol: TCP
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: mcp-core-superior-secrets
              key: DATABASE_URL
        - name: VECTOR_DB_URL
          valueFrom:
            secretKeyRef:
              name: mcp-core-superior-secrets
              key: VECTOR_DB_URL
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: mcp-core-superior-secrets
              key: REDIS_URL
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: mcp-core-superior-secrets
              key: JWT_SECRET
        - name: CONTEXTFORGE_API_KEY
          valueFrom:
            secretKeyRef:
              name: mcp-core-superior-secrets
              key: CONTEXTFORGE_API_KEY
        envFrom:
        - configMapRef:
            name: mcp-core-superior-config
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
          readOnly: true
        - name: logs-volume
          mountPath: /app/logs
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          capabilities:
            drop:
            - ALL
      volumes:
      - name: config-volume
        configMap:
          name: mcp-core-superior-config
      - name: logs-volume
        emptyDir:
          sizeLimit: 10Gi
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - mcp-core-superior
              topologyKey: kubernetes.io/hostname
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-core-superior-service
  namespace: mcp-core-superior
  labels:
    app: mcp-core-superior
spec:
  type: ClusterIP
  selector:
    app: mcp-core-superior
  ports:
  - port: 8080
    targetPort: 8080
    name: http
    protocol: TCP
  - port: 9090
    targetPort: 9090
    name: metrics
    protocol: TCP
```

### Horizontal Pod Autoscaler

**hpa.yaml**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mcp-core-superior-hpa
  namespace: mcp-core-superior
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mcp-core-superior
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: active_requests
      target:
        type: AverageValue
        averageValue: "100"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 2
        periodSeconds: 60
```

### Ingress Configuration

**ingress.yaml**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mcp-core-superior-ingress
  namespace: mcp-core-superior
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "600"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "600"
spec:
  tls:
  - hosts:
    - api.mcp-core-superior.io
    secretName: mcp-core-superior-tls
  rules:
  - host: api.mcp-core-superior.io
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: mcp-core-superior-service
            port:
              number: 8080
```

### Kubernetes Deployment Script

**k8s-deploy.sh**
```bash
#!/bin/bash
set -e

NAMESPACE="mcp-core-superior"
APP_NAME="mcp-core-superior"
VERSION="v2.0.0"

log_info() {
    echo "[INFO] $1"
}

log_error() {
    echo "[ERROR] $1" >&2
}

# Verificar kubectl
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl no está instalado"
    exit 1
fi

# Crear namespace si no existe
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Aplicar RBAC
kubectl apply -f rbac.yaml -n $NAMESPACE

# Aplicar ConfigMap y Secrets
kubectl apply -f configmap.yaml -n $NAMESPACE
kubectl apply -f secrets.yaml -n $NAMESPACE

# Desplegar servicios de base de datos
log_info "Desplegando PostgreSQL..."
kubectl apply -f postgres-deployment.yaml -n $NAMESPACE

log_info "Desplegando Redis..."
kubectl apply -f redis-deployment.yaml -n $NAMESPACE

# Esperar a que PostgreSQL esté listo
log_info "Esperando a que PostgreSQL esté listo..."
kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=300s

# Ejecutar migraciones
log_info "Ejecutando migraciones de base de datos..."
kubectl run db-migration \
    --image=mcp-core-superior:$VERSION \
    --restart=Never \
    --rm \
    -i \
    --env="DATABASE_URL=$(kubectl get secret mcp-core-superior-secrets -n $NAMESPACE -o jsonpath='{.data.DATABASE_URL}' | base64 -d)" \
    --env="ENVIRONMENT=production" \
    --command -- alembic upgrade head

# Desplegar aplicación principal
log_info "Desplegando MCP Core Superior..."
kubectl apply -f mcp-core-deployment.yaml -n $NAMESPACE
kubectl apply -f hpa.yaml -n $NAMESPACE

# Aplicar Ingress
log_info "Configurando Ingress..."
kubectl apply -f ingress.yaml -n $NAMESPACE

# Verificar despliegue
log_info "Verificando estado del despliegue..."
kubectl rollout status deployment/mcp-core-superior -n $NAMESPACE --timeout=600s

# Verificar pods
log_info "Estado de los pods:"
kubectl get pods -n $NAMESPACE

# Verificar servicios
log_info "Estado de los servicios:"
kubectl get services -n $NAMESPACE

log_info "Despliegue completado exitosamente"
```

## 🚀 Serverless Deployment

### AWS Lambda Configuration

**lambda-deployment.yml**
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: 'MCP Core Superior Serverless'

Parameters:
  Environment:
    Type: String
    Default: production
    AllowedValues: [development, staging, production]

Globals:
  Function:
    Runtime: python3.11
    Timeout: 300
    MemorySize: 512
    Environment:
      Variables:
        ENVIRONMENT: !Ref Environment
        LOG_LEVEL: INFO
    DeadLetterQueue:
      Type: SQS
      TargetArn: !GetAtt DLQ.Arn
  Api:
    TracingConfig:
      Mode: Active
    Cors:
      AllowMethods: "'GET,POST,OPTIONS'"
      AllowHeaders: "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
      AllowOrigin: "'*'"

Resources:
  # Function principal
  MCPCoreFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub "${Environment}-mcp-core-superior"
      CodeUri: ./
      Handler: src.lambda_handler.handler
      Layers:
        - !Ref CommonLayer
      Environment:
        Variables:
          DATABASE_URL: !Ref DatabaseUrl
          VECTOR_DB_URL: !Ref VectorDbUrl
          REDIS_URL: !Ref RedisUrl
          CONTEXTFORGE_URL: !Ref ContextForgeUrl
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /{proxy+}
            Method: ANY
        HealthEvent:
          Type: Api
          Properties:
            Path: /health
            Method: GET
      ReservedConcurrency: 10
      Layers:
        - !Ref DependenciesLayer

  # Layers
  DependenciesLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      LayerName: !Sub "${Environment}-mcp-core-deps"
      Description: Dependencies para MCP Core Superior
      ContentUri: ./lambda-layers/dependencies
      CompatibleRuntimes:
        - python3.11

  CommonLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      LayerName: !Sub "${Environment}-mcp-core-common"
      Description: Common utilities para MCP Core
      ContentUri: ./lambda-layers/common
      CompatibleRuntimes:
        - python3.11

  # Dead Letter Queue
  DLQ:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: !Sub "${Environment}-mcp-core-dlq"
      MessageRetentionPeriod: 1209600  # 14 days

  # IAM Role
  ExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        - PolicyName: CloudWatchAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - logs:CreateLogGroup
                  - logs:CreateLogStream
                  - logs:PutLogEvents
                Resource: '*'
        - PolicyName: ParameterStoreAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - ssm:GetParameter
                  - ssm:GetParameters
                  - ssm:GetParameterByPath
                Resource: '*'

Outputs:
  ApiUrl:
    Description: "API Gateway endpoint URL"
    Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/${Environment}/"
  FunctionName:
    Description: "Nombre de la función Lambda"
    Value: !Ref MCPCoreFunction
```

### Lambda Handler

**src/lambda_handler.py**
```python
"""
Lambda handler para MCP Core Superior
"""
import json
import logging
from typing import Dict, Any
from mangum import Mangum
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from src.core.fastmcp_server import FastMCPServer

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Crear aplicación FastAPI
app = FastAPI(title="MCP Core Superior", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancia del servidor MCP
mcp_server = FastMCPServer()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": "aws-lambda"
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    # Verificar dependencias
    try:
        # TODO: Verificar conectividad con servicios externos
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not_ready"}, 503

@app.post("/mcp-tools/{tool_name}")
async def mcp_tool_proxy(tool_name: str, request: Request):
    """Proxy para herramientas MCP"""
    try:
        # Obtener parámetros de la request
        params = await request.json() if request.headers.get("content-type") == "application/json" else {}
        
        # Ejecutar herramienta MCP
        result = await mcp_server.execute_tool(tool_name, params)
        
        return Response(
            content=json.dumps(result),
            media_type="application/json",
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        return Response(
            content=json.dumps({"error": str(e)}),
            media_type="application/json",
            status_code=500
        )

@app.post("/orchestrate")
async def orchestrate_multitask(request: Request):
    """Orquestación multi-agente"""
    try:
        params = await request.json()
        result = await mcp_server.orchestrate_multitask(**params)
        
        return Response(
            content=json.dumps(result),
            media_type="application/json",
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error in orchestration: {e}")
        return Response(
            content=json.dumps({"error": str(e)}),
            media_type="application/json",
            status_code=500
        )

# Handler para AWS Lambda
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    """Lambda handler principal"""
    return handler(event, context)
```

### Serverless Framework Configuration

**serverless.yml**
```yaml
service: mcp-core-superior

frameworkVersion: '3'

provider:
  name: aws
  runtime: python3.11
  region: us-east-1
  stage: ${opt:stage, 'dev'}
  environment:
    ENVIRONMENT: ${self:provider.stage}
    LOG_LEVEL: INFO
  iam:
    role:
      statements:
        - Effect: Allow
          Action:
            - ssm:GetParameter
            - ssm:GetParameters
          Resource: '*'

plugins:
  - serverless-python-requirements
  - serverless-domain-manager

functions:
  api:
    handler: src.lambda_handler.handler
    timeout: 300
    memorySize: 512
    events:
      - http:
          path: /{proxy+}
          method: ANY
          cors: true
      - http:
          path: /health
          method: GET
          cors: true
      - http:
          path: /orchestrate
          method: POST
          cors: true

  orchestrate:
    handler: src.lambda_handler.orchestrate_multitask
    timeout: 900  # 15 minutos max
    memorySize: 1024
    events:
      - http:
          path: /multi-agent
          method: POST
          cors: true

package:
  patterns:
    - '!tests/**'
    - '!docs/**'
    - '!.git/**'
    - '!*.md'

custom:
  pythonRequirements:
    layer: true
    dockerFile: ./Dockerfile.lambda
  customDomain:
    domainName: api.mcp-core-superior.${self:provider.stage}.example.com
    basePath: ''
    stage: ${self:provider.stage}
    createRoute53Record: true
    certificateName: '*.example.com'
```

## 🔄 Hybrid Deployment

### Component Distribution

**hybrid-deployment.yml**
```yaml
# Distribución híbrida para máxima escalabilidad
# Componentes de baja latencia en Edge
# Componentes computation-heavy en Cloud

apiVersion: v1
kind: ConfigMap
metadata:
  name: hybrid-config
data:
  # Edge components
  EDGE_COMPONENTS: "routing,auth,caching,static_content"
  
  # Cloud components  
  CLOUD_COMPONENTS: "orchestrator,database,ml_models,analytics"
  
  # Connection strategy
  CONNECTION_TIMEOUT: "30s"
  RETRY_ATTEMPTS: "3"
  CIRCUIT_BREAKER_THRESHOLD: "5"
```

## 📊 Monitoring and Observability

### Prometheus Configuration

**prometheus.yml**
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "mcp_core_rules.yml"

scrape_configs:
  - job_name: 'mcp-core-superior'
    static_configs:
      - targets: ['mcp-core-superior:9090']
    scrape_interval: 10s
    metrics_path: /metrics
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
      
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
      
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']
```

### Grafana Dashboards

**grafana-dashboard.json**
```json
{
  "dashboard": {
    "id": null,
    "title": "MCP Core Superior",
    "tags": ["mcp", "ai", "orchestration"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Requests per Second",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(mcp_core_requests_total[5m])",
            "legendFormat": "RPS"
          }
        ]
      },
      {
        "id": 2,
        "title": "Agent Response Times",
        "type": "heatmap",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(mcp_core_agent_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "rate(mcp_core_errors_total[5m]) * 100",
            "legendFormat": "Error Rate %"
          }
        ]
      }
    ]
  }
}
```

## 🛡️ Security Considerations

### Production Security Checklist
- [ ] HTTPS/TLS habilitado en todos los endpoints
- [ ] Autenticación JWT validada
- [ ] Rate limiting configurado
- [ ] CORS configurado correctamente
- [ ] Headers de seguridad configurados
- [ ] Secret management implementado
- [ ] Audit logging habilitado
- [ ] Container scanning realizado
- [ ] Network policies configuradas
- [ ] Backup encryption habilitado

### SSL/TLS Configuration
```nginx
# nginx.conf - Configuración SSL
server {
    listen 443 ssl http2;
    server_name api.mcp-core-superior.io;
    
    # Certificados SSL
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # Configuración SSL moderna
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    
    # Headers de seguridad
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Proxy a aplicación
    location / {
        proxy_pass http://mcp-core-superior;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔧 Deployment Automation

### GitOps Workflow

**argo-application.yaml**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: mcp-core-superior
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/mcp-core-superior/deployments
    targetRevision: main
    path: kubernetes
    helm:
      valueFiles:
        - values-production.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: mcp-core-superior
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

### CI/CD Pipeline

**.github/workflows/deploy.yml**
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
          
      - name: Run tests
        run: |
          pytest tests/ --cov=src --cov-report=xml
          
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build and push Docker image
        env:
          DOCKER_REGISTRY: ${{ secrets.DOCKER_REGISTRY }}
        run: |
          docker build -t $DOCKER_REGISTRY/mcp-core-superior:${{ github.sha }} .
          docker push $DOCKER_REGISTRY/mcp-core-superior:${{ github.sha }}
          
      - name: Update deployment
        run: |
          # Update image en Kubernetes deployment
          kubectl set image deployment/mcp-core-superior \
            mcp-core-superior=$DOCKER_REGISTRY/mcp-core-superior:${{ github.sha }}
```

---

## 📝 Deployment Checklist

### Pre-deployment
- [ ] Tests pasan completamente
- [ ] Variables de entorno configuradas
- [ ] Base de datos migrada
- [ ] Certificados SSL válidos
- [ ] Backup de la base de datos creado
- [ ] Monitoreo configurado
- [ ] Alertas configuradas

### During Deployment
- [ ] Rolling update iniciado
- [ ] Health checks pasando
- [ ] Métricas en monitoreo normal
- [ ] Logs revisados

### Post-deployment
- [ ] Aplicación responde correctamente
- [ ] Funcionalidades críticas verificadas
- [ ] Performance dentro de límites esperados
- [ ] No hay errores en logs
- [ ] Backup automático configurado
- [ ] Documentación actualizada

---

**Próximos pasos**: Después del despliegue, revisar [Security Guide](../security/overview.md) para configuraciones de seguridad avanzadas.