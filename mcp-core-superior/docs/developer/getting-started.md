# Developer Guide - Getting Started

## 🎯 Bienvenido al Desarrollo

Esta guía está diseñada para ayudarte a comenzar a desarrollar con MCP Core Superior de manera rápida y eficiente. Cubre desde la configuración del entorno hasta el desarrollo de tu primera integración.

## 🚀 Quick Start (5 minutos)

### Prerequisitos
- Python 3.11 o superior
- Git
- Docker y Docker Compose
- 4GB+ RAM disponible

### Instalación Express
```bash
# Clonar el repositorio
git clone https://github.com/mcp-core-superior/mcp-core-superior.git
cd mcp-core-superior

# Instalar dependencias de desarrollo
pip install -e ".[dev]"

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# Ejecutar stack completo con Docker
docker-compose up -d

# Verificar instalación
python -c "import mcp_core_superior; print('✅ MCP Core Superior instalado correctamente')"
```

### Tu Primera Ejecución
```python
#!/usr/bin/env python3
"""
Tu primer script con MCP Core Superior
"""
import asyncio
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp.core import FastMCPServer

async def main():
    """Script básico para probar el sistema"""
    print("🚀 Iniciando MCP Core Superior...")
    
    # Configuración básica
    config = {
        "database_url": "postgresql://localhost/mcp_core_dev",
        "redis_url": "redis://localhost:6379",
        "contextforge_url": "http://localhost:8001",
        "log_level": "INFO"
    }
    
    # Crear y ejecutar servidor
    server = FastMCPServer(config)
    
    try:
        await server.start()
        print("✅ Servidor MCP Core Superior ejecutándose correctamente")
        print("🔌 Endpoint MCP: stdin/stdout")
        print("🌐 API REST: http://localhost:8080")
        print("📊 Health Check: http://localhost:8080/health")
        
        # Ejecutar indefinidamente
        await server.wait_for_shutdown()
        
    except Exception as e:
        print(f"❌ Error al iniciar servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

Ejecutar:
```bash
python quickstart.py
```

## 🛠️ Configuración del Entorno de Desarrollo

### Estructura del Proyecto
```
mcp-core-superior/
├── src/                          # Código fuente
│   ├── core/                     # Componentes principales
│   ├── agents/                   # Wrappers de agentes
│   ├── orchestrator/             # Orquestador multi-agente
│   ├── services/                 # Servicios auxiliares
│   ├── api/                      # APIs REST
│   ├── utils/                    # Utilidades
│   └── __init__.py
├── docs/                         # Documentación
├── examples/                     # Ejemplos de código
├── tests/                        # Suite de testing
├── config/                       # Configuraciones
├── scripts/                      # Scripts de utilidad
├── requirements.txt              # Dependencias principales
├── requirements-dev.txt          # Dependencias de desarrollo
├── .env.example                  # Ejemplo de variables de entorno
├── docker-compose.yml            # Stack completo
├── Dockerfile                    # Container de desarrollo
└── Makefile                      # Tareas automatizadas
```

### Variables de Entorno
```bash
# .env - Configuración de desarrollo
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database
DATABASE_URL=postgresql://mcp_user:mcp_pass@localhost:5432/mcp_core_dev
VECTOR_DB_URL=postgresql://mcp_user:mcp_pass@localhost:5432/mcp_vector_dev
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=20

# ContextForge Gateway
CONTEXTFORGE_URL=http://localhost:8001
CONTEXTFORGE_API_KEY=your_contextforge_api_key

# MCP Server
MCP_SERVER_PORT=8080
MCP_SERVER_HOST=0.0.0.0
MCP_MAX_CONCURRENT_TASKS=5
MCP_TASK_TIMEOUT=300

# Streaming
STREAMING_ENABLED=true
STREAMING_BUFFER_SIZE=1000
STREAMING_UPDATE_INTERVAL=1

# Security
JWT_SECRET=your-super-secret-jwt-key
ENCRYPTION_KEY=your-encryption-key

# Monitoring
PROMETHEUS_PORT=9090
JAEGER_COLLECTOR_PORT=14268

# ML/AI Services
LLM_PROVIDERS_CONFIG={"openai": {"api_key": "..."}}
INTELLIGENT_ROUTER_ENABLED=true
ML_MODEL_PATH=./models

# Development Settings
HOT_RELOAD=true
AUTO_HEALING_ENABLED=false
BENCHMARKING_ENABLED=true
```

### Dependencies Management

**requirements.txt** (Producción)
```
# Core Framework
fastmcp>=0.3.0
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Database
sqlalchemy>=2.0.0
alembic>=1.12.0
asyncpg>=0.29.0
pgvector>=0.2.0
redis>=5.0.0
celery>=5.3.0

# Async and Concurrency
asyncio-mqtt>=0.16.0
aiohttp>=3.9.0
asyncio-throttle>=1.0.2

# ML/AI
scikit-learn>=1.3.0
numpy>=1.24.0
pandas>=2.0.0

# Security
pyjwt>=2.8.0
cryptography>=41.0.0
passlib>=1.7.4

# Monitoring
prometheus-client>=0.19.0
opentelemetry-api>=1.21.0
opentelemetry-sdk>=1.21.0

# Utilities
structlog>=23.2.0
click>=8.1.0
rich>=13.7.0
typer>=0.9.0
```

**requirements-dev.txt** (Desarrollo)
```
-r requirements.txt

# Development Tools
black>=23.11.0
isort>=5.12.0
flake8>=6.1.0
mypy>=1.7.0
pre-commit>=3.5.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.1
pytest-cov>=4.1.0
pytest-mock>=3.12.0
factory-boy>=3.3.0
httpx>=0.25.0

# Documentation
mkdocs>=1.5.0
mkdocs-material>=9.4.0
mkdocs-mermaid2-plugin>=1.1.1

# Debugging
ipdb>=0.13.13
py-spy>=0.3.14
memory-profiler>=0.61.0

# Code Quality
bandit>=1.7.5
safety>=2.3.0
```

### Docker Development Environment

**docker-compose.dev.yml**
```yaml
version: '3.8'

services:
  # Database principal
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: mcp_core_dev
      POSTGRES_USER: mcp_user
      POSTGRES_PASSWORD: mcp_pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init-dev.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mcp_user -d mcp_core_dev"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Vector Database
  postgres_vector:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: mcp_vector_dev
      POSTGRES_USER: mcp_user
      POSTGRES_PASSWORD: mcp_pass
    ports:
      - "5433:5432"
    volumes:
      - postgres_vector_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mcp_user -d mcp_vector_dev"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Cache Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Message Queue
  rabbitmq:
    image: rabbitmq:3-management-alpine
    environment:
      RABBITMQ_DEFAULT_USER: mcp_user
      RABBITMQ_DEFAULT_PASS: mcp_pass
    ports:
      - "5672:5672"
      - "15672:15672"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: rabbitmq-diagnostics -q ping
      interval: 30s
      timeout: 10s
      retries: 5

  # MCP Core Superior
  mcp-core:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8080:8080"
      - "9090:9090"  # Prometheus
    environment:
      - ENVIRONMENT=development
      - DATABASE_URL=postgresql://mcp_user:mcp_pass@postgres:5432/mcp_core_dev
      - VECTOR_DB_URL=postgresql://mcp_user:mcp_pass@postgres_vector:5432/mcp_vector_dev
      - REDIS_URL=redis://redis:6379/0
      - RABBITMQ_URL=amqp://mcp_user:mcp_pass@rabbitmq:5672/
    volumes:
      - ./src:/app/src:rw
      - ./config:/app/config:rw
      - ./logs:/app/logs:rw
    depends_on:
      postgres:
        condition: service_healthy
      postgres_vector:
        condition: service_healthy
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
    command: uvicorn src.core.fastmcp_server:app --host 0.0.0.0 --port 8080 --reload

  # ContextForge Gateway (simplificado para desarrollo)
  contextforge:
    image: contextforge/gateway:latest
    ports:
      - "8001:8001"
    environment:
      - DB_URL=postgresql://postgres:5432/contextforge
      - JWT_SECRET=development-secret
    depends_on:
      postgres:
        condition: service_healthy

  # Monitoring Stack
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9091:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  postgres_data:
  postgres_vector_data:
  redis_data:
  rabbitmq_data:
  prometheus_data:
  grafana_data:
```

**Dockerfile.dev**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copiar código fuente
COPY src/ ./src/
COPY config/ ./config/

# Crear directorio de logs
RUN mkdir -p /app/logs

# Usuario de desarrollo
RUN useradd -m -u 1000 developer && chown -R developer:developer /app
USER developer

# Puerto por defecto
EXPOSE 8080

# Comando por defecto
CMD ["uvicorn", "src.core.fastmcp_server:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
```

## 🏃‍♂️ Workflow de Desarrollo

### Comandos Básicos (Makefile)
```makefile
# Desarrollo
dev:          # Iniciar entorno de desarrollo
up:           # Levantar todos los servicios
down:         # Detener todos los servicios
logs:         # Ver logs de todos los servicios
restart:      # Reiniciar servicios

# Código
lint:         # Ejecutar linters
format:       # Formatear código
type-check:   # Verificación de tipos
test:         # Ejecutar tests
test-cov:     # Tests con cobertura

# Base de datos
db-migrate:   # Ejecutar migraciones
db-reset:     # Resetear base de datos
db-seed:      # Poblar con datos de prueba

# Documentación
docs:         # Generar documentación
docs-serve:   # Servir documentación localmente

# Utilidades
clean:        # Limpiar archivos temporales
shell:        # Abrir shell en contenedor
```

### Ciclo de Desarrollo Típico

1. **Iniciar entorno**
   ```bash
   make dev
   ```

2. **Desarrollar código**
   ```bash
   # Los cambios se recargan automáticamente
   # Editar archivos en src/
   ```

3. **Ejecutar tests**
   ```bash
   make test
   make test-cov
   ```

4. **Verificar código**
   ```bash
   make lint
   make format
   make type-check
   ```

5. **Revisar documentación**
   ```bash
   make docs-serve
   # Abrir http://localhost:8000
   ```

### Hot Reload Configuration
```python
# src/core/config.py - Configuración para desarrollo
import os
from pydantic import BaseSettings

class DevelopmentConfig(BaseSettings):
    """Configuración específica para desarrollo"""
    
    environment: str = "development"
    debug: bool = True
    log_level: str = "DEBUG"
    
    # Hot reload settings
    hot_reload: bool = True
    auto_reload: bool = True
    
    # Performance settings for dev
    workers: int = 1
    reload_dirs: list[str] = ["src/"]
    
    class Config:
        env_prefix = "MCP_CORE_"
        case_sensitive = False
```

## 🧪 Testing en Desarrollo

### Test Structure
```
tests/
├── unit/                    # Tests unitarios
│   ├── test_agents/
│   ├── test_orchestrator/
│   ├── test_services/
│   └── test_utils/
├── integration/             # Tests de integración
│   ├── test_mcp_protocol/
│   ├── test_database/
│   └── test_external_apis/
├── e2e/                     # Tests end-to-end
│   ├── test_workflows/
│   └── test_user_scenarios/
├── fixtures/                # Datos de prueba
├── conftest.py             # Configuración global
└── pytest.ini             # Configuración pytest
```

### Configuración de Testing
```python
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --cov=src
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml
markers =
    unit: marca tests unitarios
    integration: marca tests de integración
    e2e: marca tests end-to-end
    slow: marca tests lentos
    external: marca tests que dependen de servicios externos
```

### Writing Tests
```python
# tests/unit/test_agents/test_reasoner_agent.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.agents import ReasonerAgentWrapper

class TestReasonerAgentWrapper:
    """Test suite para ReasonerAgent wrapper"""
    
    @pytest.fixture
    def agent_wrapper(self):
        """Fixture para crear wrapper de agente"""
        config = {
            "database_url": "postgresql://test/test",
            "redis_url": "redis://test"
        }
        return ReasonerAgentWrapper(config)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_intent_success(self, agent_wrapper):
        """Test de análisis de intención exitoso"""
        # Arrange
        objective = "Crear dashboard de ventas"
        context = {"domain": "analytics"}
        
        # Act
        result = await agent_wrapper.analyze_intent(objective, context)
        
        # Assert
        assert result["intent_analysis"]["primary_intent"] == "create_analytics_dashboard"
        assert result["intent_analysis"]["confidence_score"] > 0.7
        assert result["strategy_definition"]["approach"] is not None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_intent_validation_error(self, agent_wrapper):
        """Test de validación de entrada inválida"""
        # Arrange
        invalid_objective = ""  # Too short
        
        # Act & Assert
        with pytest.raises(ValueError, match="Objective must be at least"):
            await agent_wrapper.analyze_intent(invalid_objective)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_database_integration(self, agent_wrapper, test_db):
        """Test de integración con base de datos"""
        # Arrange
        objective = "Test integration"
        
        # Act
        result = await agent_wrapper.analyze_intent(objective)
        
        # Assert
        # Verificar que se guardó el contexto en BD
        context_record = await test_db.get_context(result["metadata"]["conversation_id"])
        assert context_record is not None
```

### Running Tests
```bash
# Ejecutar todos los tests
make test

# Ejecutar solo tests unitarios
pytest tests/unit/ -v

# Ejecutar tests específicos
pytest tests/unit/test_agents/test_reasoner_agent.py::TestReasonerAgentWrapper::test_analyze_intent_success

# Tests con cobertura
pytest tests/ --cov=src --cov-report=html

# Tests en paralelo
pytest tests/ -n auto

# Tests con marcadores
pytest -m unit          # Solo tests unitarios
pytest -m "not slow"    # Excluir tests lentos
pytest -m "integration and not external"  # Tests de integración locales
```

## 📝 Code Quality & Standards

### Configuración de Linters
```python
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["mcp_core_superior"]
sections = ["FUTURE", "STDLIB", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.flake8]
max-line-length = 88
extend-ignore = ["E203", "W503"]
exclude = [".git", "__pycache__", "build", "dist", ".venv"]
per-file-ignores = ["__init__.py:F401"]
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: check-toml
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ["--max-line-length=88", "--extend-ignore=E203"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: ["--strict"]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]

  - repo: https://github.com/Lucas-C/pre-commit-hooks-safety
    rev: v1.3.2
    hooks:
      - id: python-safety-dependencies-check
```

### Install Pre-commit
```bash
# Instalar hooks de pre-commit
pre-commit install

# Ejecutar en todos los archivos
pre-commit run --all-files

# Saltar hooks (usar solo en desarrollo)
git commit --no-verify -m "commit message"
```

## 🐛 Debugging & Profiling

### Debug Configuration
```python
# .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "MCP Core Superior",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/src/core/fastmcp_server.py",
            "console": "integratedTerminal",
            "justMyCode": false,
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            }
        },
        {
            "name": "Run Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/", "-v"],
            "console": "integratedTerminal",
            "justMyCode": false
        },
        {
            "name": "Debug Test",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["${file}", "-v", "-s"],
            "console": "integratedTerminal",
            "justMyCode": false
        }
    ]
}
```

### Logging Configuration
```python
# src/utils/logging_config.py
import logging
import sys
from pathlib import Path
import structlog
from structlog.typing import EventDict, Processor

def configure_logging(environment: str = "development"):
    """Configurar logging estructurado"""
    
    # Procesadores base
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ]
    
    if environment == "development":
        # Pretty printing en desarrollo
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    
    # Configurar structlog
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configurar logging estándar
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if environment == "development" else logging.INFO,
    )
```

### Profiling Tools
```python
# profiling_example.py
import cProfile
import pstats
from io import StringIO
import asyncio
from src.core import FastMCPServer

async def profile_example():
    """Ejemplo de profiling de una operación"""
    
    # Configurar profiler
    pr = cProfile.Profile()
    pr.enable()
    
    # Operación a perfilar
    server = FastMCPServer(config)
    result = await server.orchestrate_multitask(
        objective="Test profiling",
        streaming_enabled=False
    )
    
    pr.disable()
    
    # Analizar resultados
    s = StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 funciones
    
    print("=== PROFILING RESULTS ===")
    print(s.getvalue())

# Memory profiling
from memory_profiler import profile

@profile
def memory_intensive_operation():
    """Operación que consume mucha memoria"""
    data = []
    for i in range(100000):
        data.append([j for j in range(100)])
    return data

# Performance monitoring
import time
import functools

def timing_decorator(func):
    """Decorator para medir tiempo de ejecución"""
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.2f} seconds")
        return result
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.2f} seconds")
        return result
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

# Usage
@timing_decorator
async def example_operation():
    await asyncio.sleep(1)
    return "completed"
```

## 📚 Recursos Adicionales

### Documentación Interna
- [Architecture Overview](../architecture/overview.md)
- [API Reference](../api/openapi.md)
- [Contributing Guide](contributing.md)

### Links Útiles
- [FastMCP Documentation](https://fastmcp.readthedocs.io/)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)

### Comunidad
- [GitHub Repository](https://github.com/mcp-core-superior)
- [GitHub Issues](https://github.com/mcp-core-superior/issues)
- [Discord Community](https://discord.gg/mcp-core-superior)

---

**Próximos pasos**: Una vez configurado el entorno, continúa con [Development Setup](setup.md) para configuraciones avanzadas.