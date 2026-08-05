# PythonExecutorAgent con Sandbox Avanzado

## Descripción

El `AdvancedPythonExecutorAgent` es un agente MCP especializado en la ejecución segura de código Python con capacidades de sandbox avanzado, análisis de seguridad, testing automático y profiling de performance. Integra las funcionalidades del ejecutor Python base (`backend/tools/python_executor.py`) con capacidades MCP mejoradas para proporcionar un entorno de ejecución seguro y controlado.

## Características Principales

### 🔒 Seguridad Avanzada
- **Análisis AST**: Análisis sintáctico y semántico del código antes de la ejecución
- **Niveles de seguridad configurables**: Desde MINIMAL hasta MAXIMUM
- **Detección de patrones peligrosos**: Imports, llamadas, atributos peligrosos
- **Validación de dependencias**: Análisis de módulos y librerías utilizadas
- **Sandboxing completo**: Aislamiento de procesos, archivos y red

### ⚡ Performance y Monitoreo
- **Profiling detallado**: Análisis de tiempo y memoria por función
- **Límites de recursos**: Control de CPU, memoria, disco y descriptores de archivo
- **Métricas avanzadas**: Tiempo de ejecución, uso de memoria, estadísticas de éxito
- **Cache de análisis**: Optimización para análisis repetidos

### 🧪 Testing Automático
- **Tests básicos**: Sintaxis, seguridad básica, ejecución
- **Tests comprehensivos**: Dependencias, complejidad, cobertura
- **Validación de algoritmos**: Testing de correctness y performance
- **Análisis de cobertura**: Identificación de código no probado

### 🔍 Análisis de Código
- **Análisis de seguridad**: Puntuación de riesgo y recomendaciones
- **Métricas de complejidad**: Nivel de anidamiento, funciones, clases
- **Optimización**: Sugerencias basadas en profiling
- **Validación avanzada**: Chequeos múltiples de seguridad

## Instalación y Configuración

### Dependencias

```bash
# Dependencias básicas ya instaladas en el proyecto
pip install psutil memory_profiler

# Dependencias del sistema (opcional para network isolation)
# En Linux: requieren privilegios de root
sudo apt-get install iproute2  # Para network namespaces
```

### Inicialización Básica

```python
import asyncio
from src.agents.python_executor_agent import (
    AdvancedPythonExecutorAgent,
    SecurityLevel,
    ResourceLimits
)

async def setup_agent():
    # Crear agente con configuración personalizada
    agent = AdvancedPythonExecutorAgent(
        security_level=SecurityLevel.RESTRICTED,
        default_resource_limits=ResourceLimits(
            max_memory_mb=256,
            max_cpu_seconds=10,
            timeout_seconds=30
        )
    )
    
    await agent.ensure_initialized()
    return agent
```

## Niveles de Seguridad

### SecurityLevel.MINIMAL
- **Uso**: Desarrollo interno, código de confianza
- **Permisos**: 24 builtins, 17 módulos permitidos
- **Límites**: 1GB memoria, 30s CPU, 60s timeout

### SecurityLevel.RESTRICTED (Recomendado)
- **Uso**: Código de usuarios, general
- **Permisos**: 24 builtins, 3 módulos permitidos
- **Límites**: 512MB memoria, 15s CPU, 30s timeout

### SecurityLevel.MODERATE
- **Uso**: Código externo, mayor control
- **Permisos**: 8 builtins, 3 módulos permitidos
- **Límites**: 256MB memoria, 10s CPU, 20s timeout

### SecurityLevel.STRICT
- **Uso**: Código no confiable, testing
- **Permisos**: 6 builtins, 2 módulos permitidos
- **Límites**: 128MB memoria, 5s CPU, 15s timeout

### SecurityLevel.MAXIMUM
- **Uso**: Máxima seguridad, sandbox extremo
- **Permisos**: 4 builtins, 0 módulos permitidos
- **Límites**: 64MB memoria, 2s CPU, 10s timeout

## API Reference

### Operaciones Principales

#### 1. execute_code_advanced
Ejecutar código Python con análisis y límites de recursos.

```python
request = {
    "operation": "execute_code",
    "code": "print('Hello, World!')",
    "security_level": "restricted",
    "resource_limits": {
        "max_memory_mb": 256,
        "max_cpu_seconds": 10,
        "timeout_seconds": 30
    },
    "enable_profiling": True,
    "enable_tests": True
}

result = await agent.process_request(request)
```

#### 2. analyze_code_security
Analizar seguridad del código sin ejecutarlo.

```python
request = {
    "operation": "analyze_code",
    "code": "import os; os.system('ls')",
    "security_level": "restricted"
}

result = await agent.process_request(request)
# Retorna: security_analysis, recommendations
```

#### 3. run_automatic_tests
Ejecutar tests automáticos en el código.

```python
request = {
    "operation": "run_tests",
    "code": "def test_function(): return True",
    "test_type": "comprehensive"
}

result = await agent.process_request(request)
# Retorna: test_results, summary
```

#### 4. profile_code_execution
Ejecutar profiling detallado de performance.

```python
request = {
    "operation": "profile_code",
    "code": "import time; time.sleep(1)",
    "profile_type": "performance"  # o "memory"
}

result = await agent.process_request(request)
# Retorna: profile_data, recommendations
```

#### 5. execute_with_sandbox
Ejecutar código en sandbox completamente aislado.

```python
request = {
    "operation": "execute_with_sandbox",
    "code": "result = 2 + 2; print(result)",
    "sandbox_config": {
        "security_level": "maximum",
        "resource_limits": {
            "max_memory_mb": 64,
            "max_cpu_seconds": 2
        }
    }
}

result = await agent.process_request(request)
# Retorna: sandbox_result, isolation_status
```

### Ejemplo de Uso Completo

```python
import asyncio
from src.agents.python_executor_agent import AdvancedPythonExecutorAgent, SecurityLevel

async def ejemplo_completo():
    # Configurar agente
    agent = AdvancedPythonExecutorAgent(
        security_level=SecurityLevel.RESTRICTED
    )
    await agent.ensure_initialized()
    
    # Código de ejemplo
    code = '''
def calcular_fibonacci(n):
    if n <= 1:
        return n
    return calcular_fibonacci(n-1) + calcular_fibonacci(n-2)

resultado = calcular_fibonacci(10)
print(f"Fibonacci(10) = {resultado}")
'''
    
    # Ejecutar con todas las funcionalidades
    request = {
        "operation": "execute_code",
        "code": code,
        "enable_profiling": True,
        "enable_tests": True
    }
    
    result = await agent.process_request(request)
    
    print("Resultado:", result)
    
    # Ver estado del agente
    status = agent.get_status()
    print("Estado:", status)

# Ejecutar ejemplo
asyncio.run(ejemplo_completo())
```

## Métricas y Monitoreo

### Métricas de Ejecución
```python
status = agent.get_status()
metrics = status['execution_metrics']

print(f"Total ejecuciones: {metrics['total_executions']}")
print(f"Exitosas: {metrics['successful_executions']}")
print(f"Tiempo promedio: {metrics['average_execution_time']:.3f}s")
print(f"Memoria promedio: {metrics['average_memory_usage']:.2f}MB")
```

### Health Check
```python
health = await agent.health_check()
print(f"Estado: {health['status']}")
print(f"Utilización: {health['utilization']:.2%}")
```

## Casos de Uso

### 1. Evaluación de Código de Usuario
```python
# Código potencialmente peligroso
user_code = '''
import subprocess
subprocess.run(["ls", "-la"])
'''

request = {
    "operation": "analyze_code",
    "code": user_code,
    "security_level": "strict"
}

# El agente detectará y bloqueará el acceso a subprocess
```

### 2. Testing de Algoritmos
```python
algorithm_code = '''
def busqueda_binaria(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

# Test
arr = [1, 3, 5, 7, 9]
result = busqueda_binaria(arr, 5)
'''

request = {
    "operation": "run_tests",
    "code": algorithm_code,
    "test_type": "comprehensive"
}
```

### 3. Profiling de Performance
```python
slow_code = '''
def fibonacci_recursive(n):
    if n <= 1:
        return n
    return fibonacci_recursive(n-1) + fibonacci_recursive(n-2)

result = fibonacci_recursive(30)
'''

request = {
    "operation": "profile_code",
    "code": slow_code,
    "profile_type": "performance"
}
```

## Límites de Recursos

### Configuración de Límites
```python
custom_limits = ResourceLimits(
    max_memory_mb=512,        # Límite de memoria
    max_cpu_seconds=15,       # Límite de CPU
    max_disk_io_mb=100,       # Límite de I/O de disco
    max_file_descriptors=64,  # Límite de descriptores
    max_processes=4,          # Límite de procesos
    max_network_connections=0, # 0 = red deshabilitada
    timeout_seconds=30        # Timeout general
)
```

### Efectos de los Límites
- **Memoria**: Exceder causa `MemoryError` controlado
- **CPU**: Exceder causa `ResourceLimitExceededError`
- **Red**: Conexiones bloqueadas en sandbox
- **Archivos**: Acceso solo al directorio temporal de sandbox

## Seguridad y Consideraciones

### Patrones Detectados como Peligrosos
- Importaciones peligrosas: `os`, `sys`, `subprocess`, etc.
- Llamadas peligrosas: `exec`, `eval`, `compile`, `__import__`
- Atributos peligrosos: `__globals__`, `__locals__`, `__code__`
- Nombres de función peligrosos: funciones que empiezan con `__`

### Limitaciones del Sandboxing
- **Network Isolation**: Requiere Linux con privilegios root
- **Resource Limits**: Pueden no aplicarse en todos los sistemas
- **File System**: Solo aislamiento básico implementado
- **Process Isolation**: Limitado por el sistema operativo

### Recomendaciones de Uso
1. **Siempre usar nivel de seguridad apropiado** para el contexto
2. **Configurar límites de recursos** según la aplicación
3. **Monitorear métricas** de ejecución regularmente
4. **Validar código** antes de ejecutar en producción
5. **Usar sandbox** para código de fuentes no confiables

## Troubleshooting

### Problemas Comunes

#### Error: "SecurityLevel no soportado"
```python
# ❌ Incorrecto
agent = AdvancedPythonExecutorAgent(security_level="invalid")

# ✅ Correcto
from src.agents.python_executor_agent import SecurityLevel
agent = AdvancedPythonExecutorAgent(security_level=SecurityLevel.RESTRICTED)
```

#### Timeout frecuente
```python
# Aumentar límites
limits = ResourceLimits(
    timeout_seconds=60,  # Más tiempo
    max_cpu_seconds=30   # Más CPU
)
```

#### Violaciones de seguridad
```python
# Usar nivel más permisivo para código de confianza
agent = AdvancedPythonExecutorAgent(
    security_level=SecurityLevel.MINIMAL
)
```

### Logs y Debugging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# El agente emite logs detallados de todas las operaciones
```

## Testing

### Ejecutar Tests
```bash
cd mcp-core-superior
python tests/test_python_executor_agent.py
```

### Ejecutar Ejemplos
```bash
cd mcp-core-superior
python examples/python_executor_examples.py
```

## Contribución

Para contribuir al desarrollo del PythonExecutorAgent:

1. **Análisis de código**: Implementar nuevos detectores de patrones peligrosos
2. **Sandboxing**: Mejorar aislamiento de red y procesos  
3. **Testing**: Agregar nuevos tipos de tests automáticos
4. **Performance**: Optimizar profiling y métricas
5. **Documentación**: Mejorar ejemplos y casos de uso

## Changelog

### v1.0.0
- ✅ Implementación inicial completa
- ✅ Integración con python_executor.py existente
- ✅ 5 niveles de seguridad configurables
- ✅ Análisis AST avanzado
- ✅ Testing automático básico y comprehensivo
- ✅ Profiling de performance y memoria
- ✅ Sandbox completo con aislamiento de red
- ✅ Métricas y monitoreo avanzados
- ✅ Cache de análisis de código
- ✅ Validación de seguridad múltiple

## Licencia

Este agente forma parte del proyecto MCP Core Superior y hereda su licencia.