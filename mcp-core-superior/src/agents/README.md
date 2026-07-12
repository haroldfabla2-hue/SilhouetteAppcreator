# Wrappers de Agentes MCP - Documentación

## Descripción General

Este directorio contiene todos los wrappers de agentes MCP para el MCP Core Superior. Los wrappers proporcionan una interfaz estandarizada y robusta para interactuar con los diferentes agentes especializados del sistema.

## Estructura de Wrappers

### Agentes Principales

1. **ReasonerAgentWrapper** - Análisis de intención y definición de estrategia
2. **PlannerAgentWrapper** - Planificación y descomposición de tareas  
3. **ExecutorAgentWrapper** - Ejecución de herramientas y código
4. **VerifierAgentWrapper** - Verificación y validación de resultados
5. **MemoryManagerAgentWrapper** - Gestión de memoria y contexto

### Agentes Especializados

1. **AdvancedPythonExecutorAgent** - Ejecución segura de código Python
2. **WebScrapingAgentWrapper** - Web scraping con Playwright
3. **GitOperationsAgentWrapper** - Operaciones avanzadas de Git
4. **DatabaseOperationsAgentWrapper** - Operaciones de base de datos
5. **MultiAgentOrchestratorAgentWrapper** - Orquestación multi-agente
6. **FileProcessingAgentWrapper** - Procesamiento de archivos
7. **SearchEngineAgentWrapper** - Búsquedas y scraping

## Correcciones Realizadas

### 1. Configuración Centralizada
- ✅ Creado `config.py` con configuraciones para todos los agentes
- ✅ Manejo de dependencias y variables de entorno
- ✅ Validación de configuración por entorno
- ✅ Configuraciones de seguridad y recursos

### 2. Importaciones y Compatibilidad
- ✅ Corregidas importaciones absolutas/relativas problemáticas
- ✅ Agregados fallbacks para cuando el sistema base no esté disponible
- ✅ Manejo de excepciones robusto en importaciones
- ✅ Compatibilidad hacia atrás mantenida

### 3. Estructura de Wrappers
- ✅ Todos los agentes implementan `BaseAgentWrapper`
- ✅ Métodos requeridos implementados: `_initialize`, `process_request`, `health_check`
- ✅ Decorador `@handle_exceptions` aplicado
- ✅ Logging y métricas implementadas

### 4. Gestión de Dependencias
- ✅ Manejo de dependencias opcionales con try/except
- ✅ Configuración de límites de recursos por agente
- ✅ Validación de disponibilidad de servicios
- ✅ Timeouts y reintentos configurables

### 5. Sistema de Validación
- ✅ Validador automático de wrappers (`validate_wrappers.py`)
- ✅ Verificación de estructura y compatibilidad
- ✅ Pruebas de instanciación y funcionalidad básica

## Uso de los Wrappers

### Creación Básica

```python
from agents import create_agent_wrapper, AgentType

# Crear un agente específico
reasoner = create_agent_wrapper(AgentType.REASONER)

# Crear agente con configuración personalizada
executor = create_agent_wrapper(
    AgentType.PYTHON_EXECUTOR,
    security_level=SecurityLevel.RESTRICTED
)
```

### Uso Directo

```python
from agents.reasoner_wrapper import ReasonerAgentWrapper

# Instanciar wrapper
agent = ReasonerAgentWrapper()

# Usar método específico
result = await agent.analyze_intent(
    objective="Analizar datos de ventas",
    context={"department": "sales"}
)

# Usar método genérico
result = await agent.process_request({
    "operation": "analyze_intent",
    "objective": "Analizar datos de ventas",
    "context": {"department": "sales"}
})
```

### Gestión Multi-Agente

```python
from agents import create_all_agent_wrappers, get_all_agents_health_status

# Crear todos los agentes disponibles
agents = create_all_agent_wrappers()

# Verificar estado de todos
health = get_all_agents_health_status()
print(f"Agentes saludables: {health['summary']['healthy_agents']}")
```

## Configuración

### Variables de Entorno

```bash
# Configuraciones generales
MAX_CONCURRENT_TOOLS=5
AGENT_TIMEOUT_SECONDS=60
AGENT_RETRY_ATTEMPTS=3

# Configuraciones específicas por agente
REASONER_TIMEOUT=60
PYTHON_EXECUTOR_TIMEOUT=300
WEB_SCRAPING_TIMEOUT=180
GIT_OPERATIONS_TIMEOUT=120
```

### Configuración de Recursos

```python
from agents.config import agent_config_manager, AgentType

# Obtener configuración
config = agent_config_manager.get_config(AgentType.PYTHON_EXECUTOR)

# Actualizar configuración
config.resource_limits["max_memory_mb"] = 1024
agent_config_manager.update_config(AgentType.PYTHON_EXECUTOR, config)
```

## Validación

### Ejecutar Validador

```bash
# Ejecutar validación manual
python src/agents/validate_wrappers.py

# Validar desde código
from agents.validate_wrappers import AgentWrapperValidator
validator = AgentWrapperValidator()
results = await validator.validate_all_agents(Path("src/agents"))
```

### Validación Automática

```python
from agents import validate_agent_setup

# Validar setup completo
validation = validate_agent_setup()
print(f"Agentes listos: {validation['summary']['ready_agents']}")
```

## Manejo de Errores

### Excepciones Personalizadas

```python
from core.exceptions import AgentException, AgentNotAvailableException

try:
    result = await agent.process_request(request)
except AgentNotAvailableException as e:
    print(f"Agente no disponible: {e}")
except AgentException as e:
    print(f"Error de agente: {e.message}")
```

### Fallbacks

Los wrappers incluyen fallbacks para cuando servicios externos no estén disponibles:

```python
# Web scraping sin Playwright
if not PLAYWRIGHT_AVAILABLE:
    # Usar requests simple como fallback
    pass

# Git operations sin credenciales
if not GITHUB_TOKEN:
    # Usar solo operaciones locales
    pass
```

## Monitoreo y Métricas

### Estado de Agentes

```python
# Estado individual
status = await agent.health_check()
print(f"Estado: {status['status']}")

# Estado de todos los agentes
from agents import get_all_agents_health_status
all_status = get_all_agents_health_status()
```

### Métricas de Uso

```python
# Métricas específicas del agente
metrics = agent.get_status()
print(f"Uso: {metrics['utilization']:.1%}")
print(f"Operaciones exitosas: {metrics['successful_operations']}")

# Reset métricas
agent.reset_metrics()
```

## Seguridad

### Niveles de Seguridad

```python
from python_executor_agent import SecurityLevel

# Configurar nivel de seguridad
executor = AdvancedPythonExecutorAgent(
    security_level=SecurityLevel.RESTRICTED
)
```

### Límites de Recursos

```python
from python_executor_agent import ResourceLimits

# Configurar límites personalizados
limits = ResourceLimits(
    max_memory_mb=512,
    max_cpu_seconds=30,
    timeout_seconds=60
)
```

## Pruebas

### Ejecutar Pruebas

```bash
# Ejecutar pruebas de un agente específico
python -m pytest src/agents/test_reasoner_wrapper.py -v

# Ejecutar todas las pruebas
python -m pytest src/agents/test_*.py
```

### Pruebas de Integración

```python
import asyncio
from agents import create_all_agent_wrappers

async def test_all_agents():
    agents = create_all_agent_wrappers()
    
    for name, agent in agents.items():
        try:
            await agent.ensure_initialized()
            health = await agent.health_check()
            print(f"{name}: {health['status']}")
        except Exception as e:
            print(f"{name}: Error - {e}")

asyncio.run(test_all_agents())
```

## Troubleshooting

### Problemas Comunes

1. **Importaciones fallan**
   - Verificar que el directorio está en PYTHONPATH
   - Revisar dependencias con `pip install -r requirements.txt`

2. **Agentes no se inicializan**
   - Verificar variables de entorno requeridas
   - Revisar logs para errores específicos

3. **Timeouts frecuentes**
   - Aumentar timeout en configuración
   - Verificar disponibilidad de servicios externos

### Logs

Los wrappers usan logging estructurado:

```python
import logging
logging.getLogger("mcp.agents").setLevel(logging.DEBUG)
```

## Próximos Pasos

1. **Extender validaciones** con más pruebas automáticas
2. **Implementar health checks** más detallados
3. **Agregar métricas** personalizadas por agente
4. **Mejorar documentación** de APIs específicas
5. **Optimizar rendimiento** de inicialización

## Contribución

Para agregar un nuevo wrapper:

1. Crear archivo `nuevo_agente_agent.py`
2. Implementar `NuevoAgentWrapper(BaseAgentWrapper)`
3. Agregar configuración en `config.py`
4. Actualizar `__init__.py` con imports
5. Ejecutar validador para verificar compatibilidad
6. Agregar pruebas en directorio `tests/`

## Estructura de Archivos

```
src/agents/
├── __init__.py                 # Exports y factory functions
├── config.py                   # Configuración centralizada
├── base_agent_wrapper.py       # Clase base y utilidades
├── validate_wrappers.py        # Validador automático
├── reasoner_wrapper.py         # Wrapper ReasonerAgent
├── planner_wrapper.py          # Wrapper PlannerAgent
├── executor_wrapper.py         # Wrapper ExecutorAgent
├── verifier_wrapper.py         # Wrapper VerifierAgent
├── memory_manager_wrapper.py   # Wrapper MemoryManagerAgent
├── python_executor_agent.py    # Agente Python avanzado
├── web_scraping_agent.py       # Agente web scraping
├── git_operations_agent.py     # Agente operaciones Git
├── database_operations_agent.py # Agente operaciones BD
├── multiagent_orchestrator_agent.py # Orquestador
├── file_processing_agent.py    # Agente procesamiento archivos
└── search_engine_agent.py      # Agente búsqueda
```
