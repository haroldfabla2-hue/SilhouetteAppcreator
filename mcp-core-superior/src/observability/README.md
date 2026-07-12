# Sistema de Structured Logging JSON para MCP Core Superior

Sistema completo de observabilidad y logging estructurado con formato JSON para el ecosistema MCP Core Superior.

## 🚀 Características Principales

### ✅ Implementadas

1. **JSON-structured logs** con campos estandarizados
2. **Log levels dinámicos** y filtros configurables
3. **Log correlation IDs** y tracing distribuido
4. **Log aggregation** y shipping a ELK stack
5. **Sensitive data filtering** y redaction automática
6. **Performance logging** para operaciones críticas
7. **Audit trails** para compliance
8. **Log rotation** y retention policies
9. **Error stack traces** estructuradas
10. **Integration** con todos los agentes MCP

## 📁 Estructura del Módulo

```
observability/
├── __init__.py              # Exports principales del módulo
├── structured_logger.py     # Logger principal con todas las funcionalidades
├── logging_config.py        # Configuraciones por entorno y agente
├── agent_integration.py     # Integración específica con agentes MCP
└── README.md               # Esta documentación
```

## 🔧 Uso Básico

### Configuración Inicial

```python
from src.observability import create_mcp_logger, initialize_mcp_logging

# Configuración simple
logger = create_mcp_logger("mi_agente", level=LogLevel.INFO)

# Configuración completa por entorno
loggers = initialize_mcp_logging('production')
```

### Logging Básico

```python
from src.observability import get_mcp_logger

logger = get_mcp_logger('database_operations')

# Logging básico
logger.info("Operación iniciada", user_id="user123", operation="read")
logger.debug("Información de debug", extra_field="valor")
logger.error("Error ocurrido", exception=e, error_code="DB001")

# Con contexto de correlación
with logger.operation_context("database_query"):
    result = execute_query()
    logger.info("Query ejecutada", records_affected=len(result))
```

### Decoradores para Automatización

```python
from src.observability.agent_integration import log_agent_execution

@log_agent_execution("file_processor")
def process_file(self, file_path: str):
    # El logging se maneja automáticamente
    return process_file_content(file_path)

@log_async_agent_execution("web_scraper")
async def scrape_website(self, url: str):
    # Logging automático para funciones async
    return await fetch_and_parse(url)
```

## 🏗️ Configuración Avanzada

### Por Entorno

```python
from src.observability.logging_config import configure_logging_for_environment

# Desarrollo
dev_logger = configure_logging_for_environment('development')

# Producción con ELK y Cloud Logging
prod_logger = configure_logging_for_environment('production')
```

### Configuración ELK Stack

```python
logger = create_mcp_logger(
    "mcp_service",
    level=LogLevel.INFO,
    config={
        'log_dir': '/var/log/mcp',
        'enable_elk': True,
        'elk_config': {
            'elasticsearch_url': 'http://elasticsearch:9200',
            'index_prefix': 'mcp-production-'
        }
    }
)
```

### Configuración Cloud Logging

```python
# AWS CloudWatch
logger = create_mcp_logger(
    "mcp_service",
    config={
        'enable_cloud': True,
        'cloud_config': {
            'provider': 'aws',
            'config': {
                'log_group': '/aws/mcp/production',
                'log_stream': 'mcp-logs'
            }
        }
    }
)

# Google Cloud Logging
logger = create_mcp_logger(
    "mcp_service",
    config={
        'enable_cloud': True,
        'cloud_config': {
            'provider': 'gcp',
            'config': {
                'project_id': 'my-project',
                'log_name': 'mcp-logs'
            }
        }
    }
)
```

## 📊 Performance y Auditoría

### Logging de Performance

```python
logger = get_mcp_logger('python_executor')
perf_logger = logger.get_performance_logger()

# Con métricas automáticas
result = perf_logger.log_operation("expensive_computation", 
                                 my_computation_function, data)
```

### Audit Trails

```python
logger = get_mcp_logger('auth_service')
audit_logger = logger.get_audit_logger()

# Log de accesos
audit_logger.log_access("user123", "/api/admin", "GET")

# Log de cambios de datos
audit_logger.log_data_change("user123", "user_profile", "UPDATE",
                           old_value="old@email.com", 
                           new_value="new@email.com")

# Log de eventos del sistema
audit_logger.log_system_event("SECURITY_BREACH", 
                            "Suspicious activity detected",
                            user_id="admin")
```

## 🔒 Filtrado de Datos Sensibles

El sistema filtra automáticamente datos sensibles:

```python
logger = get_mcp_logger('api_service')

# Estos valores serán reemplazados por ***REDACTED***
logger.info("Usuario logueado", 
           password="secret123",  # Será filtrado
           api_key="sk-abc123",   # Será filtrado
           email="user@example.com", # Será filtrado
           normal_data="this is fine")
```

**Patrones filtrados automáticamente:**
- Contraseñas y secrets
- API keys y tokens
- Números de tarjetas de crédito
- Números de seguridad social
- Emails y teléfonos
- Cualquier campo con nombres sensibles (password, token, secret, key, auth)

## 🔍 Correlation IDs y Tracing

### Uso Básico

```python
logger = get_mcp_logger('orchestrator')

# Los correlation IDs se propagan automáticamente
with logger.operation_context("user_request", user_id="user123"):
    # Todas las operaciones dentro de este contexto tendrán el mismo correlation_id
    call_agent_1()
    call_agent_2()
    
    # Los logs mostrarán el correlation_id automáticamente
    logger.info("Operación interna", internal_data="value")
```

### Propagación Manual

```python
from src.observability.structured_logger import CorrelationContext

correlation_id = CorrelationContext.generate_correlation_id()

with CorrelationContext().correlation_context(correlation_id):
    # Usar el correlation_id en esta sección
    logger.info("Operación con correlation manual", correlation_id=correlation_id)
```

## 🎯 Integración con Agentes MCP

### Mixin de Logging

```python
from src.observability.agent_integration import AgentLoggingMixin

class DatabaseAgent(AgentLoggingMixin):
    def __init__(self):
        super().__init__()
        self.agent_name = "database_operations"
    
    def execute_query(self, query: str):
        with self.log_execution("execute_query", query_type="SELECT"):
            self.log_info("Ejecutando query", query=query[:100])  # Truncado para seguridad
            result = self._run_query(query)
            self.log_performance("query_execution", 45.2)  # 45.2ms
            return result
```

### Wrapper de Agentes

```python
from src.observability.agent_integration import create_logged_agent_wrapper

class OriginalAgent:
    def process_task(self, task):
        return f"Processed: {task}"

# Crear versión con logging automático
LoggedAgent = create_logged_agent_wrapper(OriginalAgent, "processed_agent")

agent = LoggedAgent()
result = agent.process_task("important_task")  # Logging automático
```

### Decoradores Específicos

```python
from src.observability.agent_integration import log_mcp_tool_execution

class WebScrapingAgent:
    @log_mcp_tool_execution("scrape_website", "web_scraper")
    def scrape_website(self, url: str):
        return fetch_page(url)
```

## 📈 Formato de Logs JSON

```json
{
  "timestamp": "2025-11-04T05:28:12.123Z",
  "level": "INFO",
  "logger": "mcp.database_operations",
  "message": "Query executed successfully",
  "component": "database",
  "agent_id": "db-agent-001",
  "correlation_id": "mcp-a1b2c3d4e5f6g7h8",
  "trace_id": "trace-db-001",
  "span_id": "span-query-001",
  "operation": "execute_query",
  "duration_ms": 45.2,
  "status": "success",
  "user_id": "user123",
  "session_id": "session-456",
  "additional_fields": {
    "records_affected": 15,
    "query_type": "SELECT"
  }
}
```

## 🛠️ Configuración por Agente

### Configuraciones Predefinidas

```python
from src.observability.logging_config import AGENT_SPECIFIC_CONFIGS

# Cada agente tiene configuración optimizada:
AGENT_SPECIFIC_CONFIGS = {
    'database_operations': {
        'level': LogLevel.DEBUG,
        'sensitive_operation': True
    },
    'python_executor': {
        'level': LogLevel.DEBUG,
        'high_performance': True
    },
    'web_scraping': {
        'level': LogLevel.INFO,
        'rate_limited': True
    }
    # ... más configuraciones
}
```

## 🏭 Tipos de Operaciones

```python
from src.observability.logging_config import configure_operational_logging

# Para operaciones críticas de performance
perf_logger = configure_operational_logging('performance_critical', 'python_executor')

# Para auditoría requerida
audit_logger = configure_operational_logging('audit_required', 'auth_service')

# Para sesiones de debug
debug_logger = configure_operational_logging('debug_session', 'orchestrator')

# Para investigación de errores
error_logger = configure_operational_logging('error_investigation', 'database_operations')
```

## 📊 Integración ELK Stack

### Configuración Elasticsearch

```python
from src.observability.structured_logger import ELKShipper

# Configurar shipper ELK
elk_shipper = ELKShipper(
    elasticsearch_url="http://elasticsearch:9200",
    index_prefix="mcp-logs-"
)

# Los logs se envían automáticamente a Elasticsearch
```

### Configuración Logstash

```python
# Los logs JSON estructurados son compatibles con Logstash input plugin
# El formato JSON permite parsing directo sin filtros adicionales
```

### Configuración Fluentd

```python
# Configuración Fluentd para logs MCP
<source>
  @type tail
  path /var/log/mcp/*.log
  pos_file /var/log/mcp/mcp.log.pos
  tag mcp.logs
  format json
</source>
```

## 🚀 Ejemplos de Uso Completo

### Agente Completo con Logging

```python
from src.observability.agent_integration import AgentLoggingMixin, log_agent_execution
from src.observability import get_mcp_logger

class FileProcessingAgent(AgentLoggingMixin):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.agent_name = "file_processing"
        
        self.log_info("FileProcessingAgent initialized", config=config)
    
    @log_agent_execution("file_processor", "process")
    def process_file(self, file_path: str, output_dir: str):
        """Procesa un archivo con logging automático"""
        self.log_info("Processing file", file_path=file_path)
        
        try:
            with self.log_execution("file_read"):
                data = self._read_file(file_path)
            
            with self.log_execution("file_transform"):
                processed_data = self._transform_data(data)
            
            with self.log_execution("file_write"):
                result_path = self._write_file(processed_data, output_dir)
            
            self.log_info("File processed successfully", 
                         input_file=file_path,
                         output_file=result_path)
            
            return result_path
            
        except Exception as e:
            self.log_error("File processing failed", exception=e, 
                          file_path=file_path)
            raise
    
    @log_async_agent_execution("file_processor", "batch_process")
    async def batch_process(self, file_paths: list):
        """Procesamiento asíncrono con logging"""
        results = []
        
        for file_path in file_paths:
            try:
                result = await self.process_file_async(file_path)
                results.append(result)
                self.log_performance("file_process", 123.4)
            except Exception as e:
                self.log_error("Batch file processing failed", exception=e)
                continue
        
        return results
    
    def _read_file(self, path):
        # Implementación específica
        pass
    
    def _transform_data(self, data):
        # Implementación específica
        pass
    
    def _write_file(self, data, path):
        # Implementación específica
        pass
```

### Configuración de Sistema Completo

```python
# main.py - Configuración inicial del sistema
from src.observability.logging_config import initialize_mcp_logging
from src.observability.agent_integration import integrate_logging_with_agent

def setup_mcp_logging():
    """Configuración inicial del sistema de logging"""
    
    # Determinar entorno
    environment = os.getenv('MCP_ENV', 'development')
    
    # Inicializar todos los loggers
    loggers = initialize_mcp_logging(environment)
    
    # Integrar con agentes existentes
    agents = load_mcp_agents()  # Función para cargar agentes
    
    for agent in agents:
        integrate_logging_with_agent(agent, agent.__class__.__name__)
    
    return loggers

# En el inicio de la aplicación
loggers = setup_mcp_logging()

# Los agentes ahora tendrán logging automático
for agent in agents:
    agent.start()  # Con logging automático
```

## 🔧 Configuración Avanzada

### Variables de Entorno

```bash
# .env
MCP_ENV=production
MCP_LOG_LEVEL=INFO
MCP_LOG_DIR=/var/log/mcp
MCP_ELK_ENABLED=true
MCP_ELASTICSEARCH_URL=http://elasticsearch:9200
MCP_CLOUD_LOGGING=aws
MCP_AWS_LOG_GROUP=/aws/mcp/production
```

### Archivo de Configuración

```yaml
# logging.yaml
logging:
  environment: production
  level: INFO
  outputs:
    console:
      enabled: false
    file:
      enabled: true
      directory: /var/log/mcp
      rotation:
        max_size_mb: 100
        max_files: 10
        compression: true
    elk:
      enabled: true
      elasticsearch_url: http://elasticsearch:9200
      index_prefix: mcp-production-
    cloud:
      enabled: true
      provider: aws
      config:
        log_group: /aws/mcp/production
        log_stream: mcp-logs
```

## 📝 Notas de Implementación

- **Thread Safety**: El sistema es thread-safe usando threading.local() para correlation IDs
- **Performance**: Logging asíncrono con agregación en lotes para minimizar impacto
- **Compatibilidad**: Compatible con Python 3.7+ y todas las librerías MCP existentes
- **Extensibilidad**: Sistema modular que permite añadir nuevos shippers y filtros
- **Security**: Filtrado automático de datos sensibles y sanitización de logs

## 🤝 Contribución

Este sistema de logging está diseñado para ser extensible y fácil de mantener. Para añadir nuevas funcionalidades:

1. Extender las clases existentes en `structured_logger.py`
2. Añadir nuevas configuraciones en `logging_config.py`
3. Crear integraciones específicas en `agent_integration.py`
4. Actualizar esta documentación

## 📞 Soporte

Para soporte técnico o consultas sobre el sistema de logging, contactar al equipo de observabilidad MCP.