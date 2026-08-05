#!/bin/bash

# Blue-Green Deployment Script para MCP Core Superior
# Permite despliegue sin interrupciones con rollback rápido

set -e

# Configuración
ENVIRONMENT=${ENVIRONMENT:-production}
NAMESPACE="mcp-core-superior"
SERVICE_NAME="mcp-core-service"
DEPLOYMENT_PREFIX="mcp-core"
COLOR=${COLOR:-blue}  # blue o green

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Función para verificar si kubectl está disponible
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl no está instalado o no está en el PATH"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "No se puede conectar al cluster de Kubernetes"
        exit 1
    fi
}

# Función para verificar si el namespace existe
check_namespace() {
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_error "Namespace $NAMESPACE no existe"
        exit 1
    fi
}

# Función para obtener la versión actual
get_current_version() {
    kubectl get deployment "$DEPLOYMENT_PREFIX-$COLOR" -n "$NAMESPACE" -o jsonpath='{.spec.template.metadata.labels.version}' 2>/dev/null || echo "unknown"
}

# Función para obtener la otra color
get_other_color() {
    if [ "$COLOR" = "blue" ]; then
        echo "green"
    else
        echo "blue"
    fi
}

# Función para verificar el estado del despliegue
check_deployment_status() {
    local color=$1
    local deployment="${DEPLOYMENT_PREFIX}-${color}"
    
    log "Verificando estado del deployment $deployment..."
    
    if ! kubectl get deployment "$deployment" -n "$NAMESPACE" &> /dev/null; then
        log_warning "Deployment $deployment no existe"
        return 1
    fi
    
    # Esperar a que esté listo
    if ! kubectl wait --for=condition=available --timeout=600s deployment/"$deployment" -n "$NAMESPACE"; then
        log_error "Deployment $deployment no está listo"
        return 1
    fi
    
    # Verificar health checks
    local pods=$(kubectl get pods -n "$NAMESPACE" -l "app=mcp-core,color=$color" -o name)
    local healthy_pods=0
    local total_pods=$(echo "$pods" | wc -l)
    
    for pod in $pods; do
        if kubectl exec "$pod" -n "$NAMESPACE" -- wget --quiet --tries=1 --spider http://localhost:8080/health; then
            ((healthy_pods++))
        fi
    done
    
    if [ "$healthy_pods" -eq "$total_pods" ] && [ "$total_pods" -gt 0 ]; then
        log_success "Deployment $deployment está saludable ($healthy_pods/$total_pods pods)"
        return 0
    else
        log_error "Deployment $deployment no está saludable ($healthy_pods/$total_pods pods)"
        return 1
    fi
}

# Función para ejecutar health checks completos
run_health_checks() {
    local color=$1
    local service="${SERVICE_NAME}-${color}"
    
    log "Ejecutando health checks completos para $color environment..."
    
    # Health check básico
    if ! kubectl get service "$service" -n "$NAMESPACE" &> /dev/null; then
        log_error "Service $service no existe"
        return 1
    fi
    
    # Verificar endpoints
    local endpoints=$(kubectl get endpoints "$service" -n "$NAMESPACE" -o jsonpath='{.subsets[*].addresses[*].ip}' | wc -w)
    if [ "$endpoints" -eq 0 ]; then
        log_error "Service $service no tiene endpoints disponibles"
        return 1
    fi
    
    # Test de conectividad interna
    local pod=$(kubectl get pod -n "$NAMESPACE" -l "app=mcp-core,color=$color" -o name | head -n 1)
    if [ -n "$pod" ]; then
        # Test de base de datos
        if ! kubectl exec "$pod" -n "$NAMESPACE" -- pg_isready -h postgres-service -U mcpuser; then
            log_error "Base de datos no está accesible desde $pod"
            return 1
        fi
        
        # Test de Redis
        if ! kubectl exec "$pod" -n "$NAMESPACE" -- redis-cli -h redis-service ping | grep -q PONG; then
            log_error "Redis no está accesible desde $pod"
            return 1
        fi
    fi
    
    log_success "Health checks completados para $color environment"
    return 0
}

# Función para crear deployment con color específico
create_colored_deployment() {
    local color=$1
    local image_tag=$2
    local deployment="${DEPLOYMENT_PREFIX}-${color}"
    
    log "Creando deployment $deployment con imagen $image_tag..."
    
    # Crear el deployment
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $deployment
  namespace: $NAMESPACE
  labels:
    app: mcp-core
    component: application
    color: $color
    version: $image_tag
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: mcp-core
      component: application
      color: $color
  template:
    metadata:
      labels:
        app: mcp-core
        component: application
        color: $color
        version: $image_tag
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
        deployment.kubernetes.io/revision: "1"
    spec:
      serviceAccountName: mcp-core
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: mcp-core
        image: mcp-core-superior:$image_tag
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
          name: http
          protocol: TCP
        - containerPort: 8081
          name: mcp
          protocol: TCP
        - containerPort: 9090
          name: metrics
          protocol: TCP
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DEBUG
          value: "false"
        - name: COLOR
          value: "$color"
        - name: VERSION
          value: "$image_tag"
        # ... (resto de las variables de entorno del deployment original)
        resources:
          limits:
            memory: 2Gi
            cpu: 2
          requests:
            memory: 512Mi
            cpu: 500m
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 15
          failureThreshold: 5
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 10
          failureThreshold: 3
        startupProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 30
EOF
    
    log_success "Deployment $deployment creado"
}

# Función para crear service con color específico
create_colored_service() {
    local color=$1
    local service="${SERVICE_NAME}-${color}"
    
    log "Creando service $service para color $color..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: $service
  namespace: $NAMESPACE
  labels:
    app: mcp-core
    component: application
    color: $color
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "9090"
    prometheus.io/path: "/metrics"
spec:
  type: ClusterIP
  ports:
  - port: 8080
    targetPort: 8080
    protocol: TCP
    name: http
  - port: 8081
    targetPort: 8081
    protocol: TCP
    name: mcp
  - port: 9090
    targetPort: 9090
    protocol: TCP
    name: metrics
  selector:
    app: mcp-core
    component: application
    color: $color
EOF
    
    log_success "Service $service creado"
}

# Función para hacer switch del tráfico
switch_traffic() {
    local target_color=$1
    
    log "Cambiando tráfico a $target_color environment..."
    
    # Actualizar el servicio principal para apuntar al nuevo color
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: $SERVICE_NAME
  namespace: $NAMESPACE
  labels:
    app: mcp-core
    component: application
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "9090"
    prometheus.io/path: "/metrics"
spec:
  type: ClusterIP
  ports:
  - port: 8080
    targetPort: 8080
    protocol: TCP
    name: http
  - port: 8081
    targetPort: 8081
    protocol: TCP
    name: mcp
  - port: 9090
    targetPort: 9090
    protocol: TCP
    name: metrics
  selector:
    app: mcp-core
    component: application
    color: $target_color
EOF
    
    log_success "Tráfico cambiado a $target_color environment"
    
    # Esperar un momento para que el cambio se propague
    sleep 10
    
    # Verificar que el tráfico se está dirigiendo correctamente
    log "Verificando que el tráfico se dirige correctamente..."
    local endpoint_ip=$(kubectl get endpoints "$SERVICE_NAME" -n "$NAMESPACE" -o jsonpath='{.subsets[0].addresses[0].ip}' 2>/dev/null || echo "")
    
    if [ -n "$endpoint_ip" ]; then
        # Hacer una request de prueba
        if kubectl run -n "$NAMESPACE" --restart=Never --image=curlimages/curl:7.85.0 test-traffic --rm -i --tty --command -- curl -s -m 5 "http://$endpoint_ip:8080/health" | grep -q "healthy\|ok"; then
            log_success "Tráfico verificado - el endpoint está respondiendo correctamente"
        else
            log_warning "El tráfico podría no estar funcionando correctamente"
        fi
    fi
}

# Función para cleanup del environment anterior
cleanup_old_environment() {
    local old_color=$1
    
    log "Limpiando $old_color environment..."
    
    # Eliminar deployment anterior
    if kubectl get deployment "${DEPLOYMENT_PREFIX}-${old_color}" -n "$NAMESPACE" &> /dev/null; then
        kubectl delete deployment "${DEPLOYMENT_PREFIX}-${old_color}" -n "$NAMESPACE"
        log_success "Deployment ${DEPLOYMENT_PREFIX}-${old_color} eliminado"
    fi
    
    # Eliminar service anterior
    if kubectl get service "${SERVICE_NAME}-${old_color}" -n "$NAMESPACE" &> /dev/null; then
        kubectl delete service "${SERVICE_NAME}-${old_color}" -n "$NAMESPACE"
        log_success "Service ${SERVICE_NAME}-${old_color} eliminado"
    fi
}

# Función para rollback
rollback() {
    local current_color=$1
    local target_color=$2
    
    log_error "Iniciando rollback de $current_color a $target_color..."
    
    switch_traffic "$target_color"
    
    log_success "Rollback completado - tráfico dirigido a $target_color"
    
    # Limpiar deployment actual
    cleanup_old_environment "$current_color"
}

# Función principal de deployment
deploy() {
    local image_tag=${1:-latest}
    
    log "Iniciando blue-green deployment para MCP Core Superior"
    log "Color actual: $COLOR"
    log "Nueva versión: $image_tag"
    
    # Verificaciones previas
    check_kubectl
    check_namespace
    
    # Determinar el color destino
    local other_color=$(get_other_color)
    
    log "Creando nuevo $other_color environment con versión $image_tag..."
    
    # Crear deployment y service para el nuevo color
    create_colored_deployment "$other_color" "$image_tag"
    create_colored_service "$other_color"
    
    # Esperar a que esté listo
    log "Esperando a que el nuevo $other_color environment esté listo..."
    if ! check_deployment_status "$other_color"; then
        log_error "El nuevo $other_color environment no está listo"
        exit 1
    fi
    
    # Ejecutar health checks
    if ! run_health_checks "$other_color"; then
        log_error "Health checks fallaron para $other_color environment"
        rollback "$other_color" "$COLOR"
        exit 1
    fi
    
    # Cambiar tráfico
    log "Cambiando tráfico a $other_color environment..."
    switch_traffic "$other_color"
    
    # Cleanup del environment anterior
    log "Limpiando $COLOR environment..."
    cleanup_old_environment "$COLOR"
    
    log_success "Blue-green deployment completado exitosamente"
    log "Versión actual: $image_tag"
    log "Color activo: $other_color"
}

# Función para mostrar estado
status() {
    log "Estado actual del blue-green deployment:"
    
    echo
    log "Deployments:"
    kubectl get deployments -n "$NAMESPACE" -l "app=mcp-core"
    
    echo
    log "Services:"
    kubectl get services -n "$NAMESPACE" -l "app=mcp-core"
    
    echo
    log "Pods:"
    kubectl get pods -n "$NAMESPACE" -l "app=mcp-core"
}

# Función para mostrar ayuda
show_help() {
    echo "Blue-Green Deployment Script para MCP Core Superior"
    echo
    echo "Uso: $0 [COMANDO] [OPCIONES]"
    echo
    echo "Comandos:"
    echo "  deploy [TAG]     Desplegar nueva versión (blue-green)"
    echo "  rollback         Hacer rollback al environment anterior"
    echo "  status           Mostrar estado actual"
    echo "  help             Mostrar esta ayuda"
    echo
    echo "Variables de entorno:"
    echo "  COLOR           Color actual (blue|green, default: blue)"
    echo "  NAMESPACE       Namespace de Kubernetes (default: mcp-core-superior)"
    echo "  ENVIRONMENT     Entorno (development|staging|production)"
    echo
    echo "Ejemplos:"
    echo "  $0 deploy v1.2.3"
    echo "  $0 deploy latest"
    echo "  $0 rollback"
    echo "  COLOR=green $0 deploy v1.3.0"
}

# Función principal
main() {
    case "${1:-help}" in
        deploy)
            deploy "${2:-latest}"
            ;;
        rollback)
            check_kubectl
            check_namespace
            
            # Determinar colors actual y objetivo
            local current_color=$(kubectl get service "$SERVICE_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.selector.color}' 2>/dev/null || echo "unknown")
            local other_color=$(get_other_color)
            
            if [ "$current_color" = "unknown" ]; then
                log_error "No se puede determinar el color actual"
                exit 1
            fi
            
            rollback "$current_color" "$other_color"
            ;;
        status)
            check_kubectl
            status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Comando desconocido: $1"
            show_help
            exit 1
            ;;
    esac
}

# Verificar argumentos
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

# Ejecutar función principal
main "$@"