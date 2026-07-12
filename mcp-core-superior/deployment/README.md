# MCP Core Superior - Deployment Configuration

Este directorio contiene toda la configuración necesaria para el despliegue completo de MCP Core Superior en entornos de desarrollo, staging y producción.

## 🚀 Características del Deployment

### Configuración Incluida

✅ **Multi-stage Dockerfile optimizado**
- Etapas de build y runtime separadas
- Optimización de tamaño de imagen
- Configuración de seguridad con usuario no-root
- Health checks integrados

✅ **Docker Compose para Development y Production**
- Configuración completa de servicios
- Bases de datos PostgreSQL y Vector DB
- Redis para cache
- Monitoring stack completo

✅ **Kubernetes Manifests**
- Deployments con auto-scaling
- Services e Ingress
- PersistentVolumes y ConfigMaps
- Secrets management
- ServiceMonitors para Prometheus

✅ **CI/CD Pipeline (GitHub Actions)**
- Validación automática de PRs
- Testing en múltiples versiones de Python
- Escaneo de seguridad
- Deployment automático
- Blue-green deployment strategy

✅ **Environment-specific Configurations**
- `.env.development`
- `.env.staging`
- `.env.production`

✅ **Health Checks y Readiness Probes**
- Liveness, readiness y startup probes
- Health checks personalizados
- Monitoreo de dependencias

✅ **Resource Limits y Requests**
- Configuración de CPU y memoria
- HPA y VPA para auto-scaling
- Límites específicos por servicio

✅ **Secrets Management**
- Kubernetes secrets
- Docker secrets
- Variables de entorno seguras

✅ **Monitoring Stack**
- Prometheus para métricas
- Grafana para dashboards
- Jaeger para distributed tracing
- AlertManager para alertas

✅ **Database Migrations**
- Scripts de inicialización
- Migraciones automáticas
- Datos de prueba

✅ **Blue-Green Deployment Strategy**
- Script automatizado de deployment
- Rollback rápido
- Switch de tráfico sin interrupciones

## 📁 Estructura de Archivos

```
deployment/
├── docker/                    # Configuración Docker
│   ├── Dockerfile            # Multi-stage Dockerfile
│   ├── docker-compose.yml    # Development environment
│   ├── docker-compose.prod.yml # Production environment
│   └── nginx.conf           # Configuración Nginx
├── kubernetes/               # Kubernetes manifests
│   ├── 01-namespace.yaml    # Namespaces
│   ├── 02-configmaps.yaml   # ConfigMaps
│   ├── 03-secrets.yaml      # Secrets
│   ├── 04-storage.yaml      # Storage
│   ├── 05-deployment.yaml   # Deployments
│   ├── 06-services.yaml     # Services
│   ├── 07-ingress.yaml      # Ingress
│   ├── 08-autoscaling.yaml  # HPA/VPA
│   ├── 09-servicemonitors.yaml # Prometheus ServiceMonitors
│   └── 10-alertrules.yaml   # Alerting rules
├── ci-cd/                   # CI/CD pipelines
│   └── workflows/          # GitHub Actions
│       ├── main.yml        # Main CI/CD workflow
│       └── pr-validation.yml # PR validation
├── scripts/                 # Utility scripts
│   ├── entrypoint.sh       # Container entrypoint
│   └── blue-green-deploy.sh # Blue-green deployment
├── database/               # Database configuration
│   ├── init-database.sh   # Database initialization
│   └── 01-init.sql        # Initial schema
├── monitoring/            # Monitoring configuration
│   ├── prometheus.yml     # Prometheus config
│   └── alertmanager.yml   # AlertManager config
├── configs/              # Environment configs
│   ├── .env.development
│   ├── .env.staging
│   └── .env.production
└── README.md             # Este archivo
```

## 🛠️ Configuración Inicial

### 1. Prerrequisitos

- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Kubernetes** 1.20+ (para deployment en K8s)
- **kubectl** configurado
- **AWS CLI** (si usas EKS)
- **Helm** 3.0+ (opcional)

### 2. Configuración de Secrets

**Para Kubernetes:**
```bash
# Crear secrets necesarios
kubectl create secret generic mcp-core-secrets \
  --from-literal=postgres_password=your_password \
  --from-literal=jwt_secret=your_jwt_secret \
  --from-literal=contextforge_api_key=your_api_key \
  --from-literal=redis_password=redis_password \
  -n mcp-core-superior
```

**Para Docker Swarm:**
```bash
echo "your_password" | docker secret create postgres_password -
echo "your_jwt_secret" | docker secret create jwt_secret -
```

### 3. Configuración de Variables de Entorno

Copia las configuraciones de entorno apropiadas:
```bash
# Para desarrollo
cp configs/.env.development .env

# Para staging
cp configs/.env.staging .env

# Para producción
cp configs/.env.production .env
```

## 🚀 Deployment Guides

### Development Environment

1. **Iniciar servicios:**
```bash
cd deployment/docker
docker-compose up -d
```

2. **Verificar estado:**
```bash
docker-compose ps
```

3. **Acceder a servicios:**
- API: http://localhost:8080
- MCP Protocol: http://localhost:8081
- Grafana: http://localhost:3000 (admin/devgrafana)
- Prometheus: http://localhost:9091
- Jaeger: http://localhost:16686
- PgAdmin: http://localhost:5050 (admin@mcp.com/devadmin)

### Production Environment

#### Opción 1: Docker Compose (Standalone)

1. **Configurar secrets:**
```bash
# Crear secretos externos
echo "production_password" | docker secret create postgres_password -
# ... crear otros secretos
```

2. **Iniciar servicios:**
```bash
cd deployment/docker
docker-compose -f docker-compose.prod.yml up -d
```

#### Opción 2: Kubernetes

1. **Aplicar manifests:**
```bash
kubectl apply -f deployment/kubernetes/
```

2. **Verificar deployment:**
```bash
kubectl get pods -n mcp-core-superior
kubectl get services -n mcp-core-superior
```

3. **Acceder a servicios:**
```bash
# Obtener IP del LoadBalancer
kubectl get svc nginx-service -n mcp-core-superior
```

### Blue-Green Deployment

1. **Deployment manual:**
```bash
chmod +x deployment/scripts/blue-green-deploy.sh
./deployment/scripts/blue-green-deploy.sh deploy v1.2.3
```

2. **Rollback:**
```bash
./deployment/scripts/blue-green-deploy.sh rollback
```

3. **Verificar estado:**
```bash
./deployment/scripts/blue-green-deploy.sh status
```

## 📊 Monitoring y Observabilidad

### Métricas Disponibles

- **Aplicación:** Métricas de la aplicación MCP Core
- **Base de Datos:** PostgreSQL y Vector DB
- **Cache:** Redis
- **Infraestructura:** Kubernetes nodes y pods
- **Red:** Métricas de red y throughput

### Dashboards de Grafana

- **MCP Core Dashboard:** Métricas de la aplicación principal
- **Database Dashboard:** Métricas de base de datos
- **Infrastructure Dashboard:** Métricas de infraestructura
- **Business Metrics:** Métricas de negocio específicas

### Alertas Configuradas

- **Críticas:** Fallos de servicio, alta latencia, errores 5xx
- **Warnings:** Alto uso de recursos, conexiones lentas
- **Información:** Deployments, cambios de configuración

### Acceso a Dashboards

- **Grafana:** https://grafana.mcp-core-superior.com
- **Prometheus:** https://prometheus.mcp-core-superior.com
- **Jaeger:** https://jaeger.mcp-core-superior.com
- **AlertManager:** https://alertmanager.mcp-core-superior.com

## 🔧 CI/CD Pipeline

### GitHub Actions Workflows

1. **Main Workflow** (`main.yml`):
   - Se ejecuta en push a `main`, `develop` o tags
   - Valida código, ejecuta tests
   - Escaneo de seguridad
   - Deployment automático

2. **PR Validation** (`pr-validation.yml`):
   - Se ejecuta en pull requests
   - Validaciones de código
   - Tests automáticos
   - Comentarios automáticos en PR

### Triggers del CI/CD

- **Push a `develop`:** Deploy a staging
- **Push a `main`:** Deploy a producción
- **Tags `v*`:** Deploy a producción con version tag
- **Pull Requests:** Validaciones automáticas
- **Manual dispatch:** Deployment manual

### Configuración de Secrets en GitHub

Configurar los siguientes secrets en el repository:

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
AWS_EKS_RESOURCE_GROUP
AWS_EKS_CLUSTER_NAME
SONAR_TOKEN
SLACK_WEBHOOK_URL
GITHUB_TOKEN (automático)
```

## 🗄️ Base de Datos

### Esquema de Base de Datos

La base de datos incluye los siguientes schemas:
- `mcp_core`: Aplicaciones, agentes, tareas
- `agents`: Ejecuciones y procesamiento
- `context`: Sesiones y mensajes de contexto
- `security`: Logs de auditoría
- `monitoring`: Health checks y métricas
- `tasks`: Gestión de tareas

### Migraciones

```bash
# Ejecutar migraciones manualmente
kubectl exec -it <postgres-pod> -n mcp-core-superior -- bash -c "
  psql -U mcpuser -d mcp_core -f /docker-entrypoint-initdb.d/01-init.sql
"
```

### Backup y Restore

```bash
# Backup
./deployment/database/init-database.sh backup backup_$(date +%Y%m%d).sql

# Restore
psql -h postgres -U mcpuser -d mcp_core < backup_20231201.sql
```

## 🔒 Seguridad

### Medidas Implementadas

- **Container Security:** Usuario no-root, filesystem read-only
- **Network Security:** Network policies, Ingress restrictions
- **Secrets Management:** Kubernetes secrets, no secrets en código
- **RBAC:** Service accounts con permisos mínimos
- **TLS/SSL:** Certificados para HTTPS
- **Security Headers:** Configuración de headers de seguridad
- **Rate Limiting:** Protección contra DDoS
- **Scanning:** Vulnerability scanning automático

### Compliance

- **OWASP Top 10:** Implementación de mejores prácticas
- **CIS Benchmarks:** Configuraciones de seguridad
- **GDPR:** Gestión de datos personales
- **SOC 2:** Controles de seguridad

## 📈 Performance y Escalabilidad

### Auto-scaling Configurado

- **HPA:** Horizontal Pod Autoscaler (CPU/Memory/Requests)
- **VPA:** Vertical Pod Autoscaler (recomendaciones)
- **Cluster Autoscaler:** Auto-scaling de nodos

### Optimizaciones

- **Database:** Conexión pooling, índices optimizados
- **Cache:** Redis para cache distribuido
- **CDN:** Configuración para contenido estático
- **Load Balancing:** Nginx como reverse proxy
- **Resource Limits:** Límites específicos por servicio

### Métricas de Performance

- **Response Time:** P95 y P99 métricas
- **Throughput:** Requests por segundo
- **Error Rate:** Porcentaje de errores
- **Resource Usage:** CPU, memoria, disco, red

## 🐛 Troubleshooting

### Problemas Comunes

1. **Pods en CrashLoopBackOff:**
```bash
kubectl describe pod <pod-name> -n mcp-core-superior
kubectl logs <pod-name> -n mcp-core-superior
```

2. **Problemas de Base de Datos:**
```bash
kubectl exec -it <postgres-pod> -n mcp-core-superior -- psql -U mcpuser -d mcp_core
```

3. **Problemas de Red:**
```bash
kubectl get endpoints -n mcp-core-superior
kubectl describe service <service-name> -n mcp-core-superior
```

4. **Problemas de Performance:**
- Verificar métricas en Grafana
- Revisar logs de aplicación
- Verificar uso de recursos

### Logs

```bash
# Logs de aplicación
kubectl logs -l app=mcp-core -n mcp-core-superior

# Logs de base de datos
kubectl logs -l app=postgres -n mcp-core-superior

# Logs de Redis
kubectl logs -l app=redis -n mcp-core-superior
```

### Debugging Tools

```bash
# Crear pod de debug
kubectl run debug-pod --image=busybox -it --rm -- sh

# Verificar conectividad
nslookup mcp-core-service.mcp-core-superior.svc.cluster.local
```

## 📚 Documentación Adicional

- [API Documentation](../docs/api/)
- [Architecture Documentation](../docs/architecture/)
- [Deployment Runbooks](../docs/runbooks/)
- [Monitoring Guide](../docs/monitoring/)
- [Security Guide](../docs/security/)

## 🤝 Contribución

Para contribuir a este sistema de deployment:

1. Fork el repository
2. Crear feature branch
3. Implementar cambios con tests
4. Validar con workflows de CI/CD
5. Crear Pull Request

### Checklist de Deployment

- [ ] Tests pasan
- [ ] Security scan limpio
- [ ] Performance acceptable
- [ ] Documentación actualizada
- [ ] Configuración validada
- [ ] Rollback plan preparado

## 📞 Soporte

Para soporte técnico:
- **Email:** devops@mcp-core-superior.com
- **Slack:** #devops-support
- **Jira:** MCP-DEPLOY project

## 📋 Changelog

### v1.0.0 (2024-01-15)
- ✅ Configuración completa de Docker deployment
- ✅ Kubernetes manifests con blue-green deployment
- ✅ CI/CD pipeline con GitHub Actions
- ✅ Monitoring stack completo
- ✅ Database migrations y inicialización
- ✅ Scripts de automatización
- ✅ Documentación completa

---

**MCP Core Superior Deployment Configuration v1.0.0**  
*Desarrollado por el equipo de DevOps de MCP Core Superior*