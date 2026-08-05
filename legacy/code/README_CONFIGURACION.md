# SilhouetteMCP - Documentación de Configuración Centralizada

## Resumen

Se ha creado exitosamente el archivo `code/silhouettemcp_config.py` que contiene la configuración centralizada completa para el sistema SilhouetteMCP.

## Características Principales

### 📊 Configuración de Puertos

- **Sistemas Originales (8001-8002)**: 2 puertos para sistemas legacy
- **Sistemas Mejorados (8007-8024)**: 18 puertos para sistemas avanzados
- **Total**: 20 puertos configurados

### 🔒 Niveles de Seguridad

1. **BASIC**: Configuración básica para desarrollo
2. **ENHANCED**: Configuración mejorada para staging
3. **ENTERPRISE**: Configuración empresarial para producción
4. **MILITARY_GRADE**: Configuración militar para entornos críticos

### ⚖️ Balanceador de Carga

- **ROUND_ROBIN**: Distribución equitativa
- **WEIGHTED_ROUND_ROBIN**: Distribución ponderada
- **LEAST_CONNECTIONS**: Mínimo de conexiones
- **IP_HASH**: Hash de IP para afinidad
- **RANDOM**: Selección aleatoria

### 📈 Auto-Scaling

- **DEVELOPMENT**: 1-5 réplicas
- **STAGING**: 2-10 réplicas
- **PRODUCTION**: 3-30 réplicas
- **ENTERPRISE**: 5-100 réplicas con políticas avanzadas

### 🌐 Endpoints Unificados

Se han configurado 17 endpoints principales organizados en categorías:

- **Core**: Health checks, status del sistema
- **Agentes**: Ejecución y estado de agentes especializados
- **Base de Datos**: Consultas y salud de BD
- **Tareas**: Creación y gestión de tareas
- **Monitoreo**: Métricas y logs
- **Seguridad**: Verificaciones y estado
- **Auto-healing**: Disparador y estado de auto-reparación
- **Colaboración**: Sesiones y estado de colaboración

## Uso de la Configuración

### Cargar Configuración por Entorno

```python
from silhouettemcp_config import get_config_for_environment

# Para diferentes entornos
dev_config = get_config_for_environment("development")
prod_config = get_config_for_environment("production")
enterprise_config = get_config_for_environment("enterprise")
```

### Acceder a Puertos

```python
from silhouettemcp_config import SilhouetteMCPConfig

config = SilhouetteMCPConfig()

# Obtener todos los puertos
all_ports = config.get_all_ports()

# Obtener configuración específica
core_port = config.get_port_config(8001)
agent_ports = config.get_ports_by_type("agent")
```

### Trabajar con Endpoints

```python
# Obtener endpoint específico
health_endpoint = config.get_unified_endpoint("health_check")

# Filtrar por tags
status_endpoints = config.get_endpoints_by_tag("status")

# Filtrar por servicio
task_endpoints = config.get_endpoints_by_service("task_manager")
```

### Configuraciones de Seguridad

```python
# Obtener configuración de seguridad
security = config.get_security_config(SecurityLevel.ENTERPRISE)
print(f"JWT Expiration: {security.jwt_expiration}")
print(f"Encryption: {security.encryption_level}")
```

### Validación de Configuración

```python
# Validar configuración actual
validation = config.validate_config()
if validation["valid"]:
    print("Configuración válida")
else:
    for error in validation["errors"]:
        print(f"Error: {error}")
```

## Servicios por Categoría

### 🔧 Servicios Core
- `silhouettemcp_core` (Puerto 8001)
- `enhanced_core_engine` (Puerto 8007)

### 🚀 Servicios API y Gateway
- `silhouettemcp_api` (Puerto 8002)
- `enhanced_api_gateway` (Puerto 8008)

### 🗄️ Servicios de Datos
- `database_operations` (Puerto 8009)
- `vector_store` (Puerto 8010)

### 🤖 Agentes Especializados
- `analytics_agent` (Puerto 8011)
- `financial_agent` (Puerto 8012)
- `web_scraping_agent` (Puerto 8013)
- `git_operations_agent` (Puerto 8014)
- `python_executor_agent` (Puerto 8015)
- `search_engine_agent` (Puerto 8016)

### 🎼 Orquestación
- `multi_agent_orchestrator` (Puerto 8017)
- `task_manager` (Puerto 8018)

### 📊 Monitoreo
- `advanced_metrics` (Puerto 8019)
- `observability` (Puerto 8020)

### 🔒 Seguridad
- `security_system` (Puerto 8021)
- `ddos_protection` (Puerto 8022)

### 🔄 Auto-healing
- `auto_healing` (Puerto 8023)

### 🤝 Comunicación
- `collaboration_engine` (Puerto 8024)

## Variables de Entorno Recomendadas

```bash
# Configuración JWT
export JWT_SECRET_BASIC="basic-secret-key-2025"
export JWT_SECRET_ENHANCED="enhanced-secret-key-2025"
export JWT_SECRET_ENTERPRISE="enterprise-secret-key-2025"
export JWT_SECRET_MILITARY="military-grade-secret-key-2025"

# Entorno activo
export SILHOUETTE_ENV="production"
```

## Próximos Pasos

1. **Integrar** la configuración en el sistema principal
2. **Implementar** health checks en todos los servicios
3. **Configurar** el balanceador de carga con las estrategias definidas
4. **Activar** auto-scaling en el entorno apropiado
5. **Monitorear** el rendimiento usando los endpoints de métricas

## Notas Técnicas

- Todos los servicios enhanced usan HTTPS por defecto
- Los puertos originales mantienen HTTP para compatibilidad
- Los endpoints unificados proporcionan una interfaz consistente
- La configuración incluye validaciones automáticas
- Soporte completo para entornos dev/staging/prod/enterprise

¡La configuración centralizada está lista para su uso!