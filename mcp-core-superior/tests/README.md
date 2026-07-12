# MCP Core Superior - Test Suite

## 📋 Descripción

Suite completa de unit tests para el MCP Core Superior con **target de 90%+ code coverage**. Incluye tests para todos los componentes del sistema usando pytest, async testing, y coverage reporting.

## 🏗️ Estructura de Tests

```
tests/
├── conftest.py                    # Configuración global de pytest y fixtures
├── test_agents/                   # Tests de los 12 Agentes MCP
│   └── __init__.py               # Tests para todos los agentes
├── test_observability/            # Tests del Sistema de Observabilidad
│   └── __init__.py               # OpenTelemetry, métricas, logging
├── test_security/                 # Tests del Sistema de Seguridad
│   └── __init__.py               # Auth, rate limiting, content scanning
├── test_technical/                # Tests de Diferenciadores Técnicos
│   └── __init__.py               # Context persistence, collaboration, routing
├── test_core/                     # Tests del Core System
│   └── __init__.py               # Config, FastMCP server, orchestration
└── test_integration/              # Tests de Integration Points
    └── __init__.py               # ContextForge, database, Redis
```

## 🎯 Cobertura de Tests

### ✅ Agentes MCP (12 tests completos)
- **Base Agent Wrapper** - Inicialización, lifecycle, request processing
- **Python Executor Agent** - Code execution, security analysis, sandbox
- **Git Operations Agent** - Repository operations, branching, merging
- **Web Scraping Agent** - URL scraping, bulk operations, content filtering
- **Database Operations Agent** - Query execution, transactions, schema ops
- **Search Engine Agent** - Web search, vector search, hybrid search
- **File Processing Agent** - File I/O, conversion, batch processing
- **MultiAgent Orchestrator Agent** - Task coordination, parallel execution
- **Memory Manager Wrapper** - Memory storage, retrieval, cleanup
- **Planner Wrapper** - Plan creation, optimization, resource allocation
- **Reasoner Wrapper** - Logical reasoning, pattern recognition
- **Verifier Wrapper** - Result verification, consistency checks

### ✅ Sistema de Observabilidad
- **OpenTelemetry System** - Span creation, tracing, error tracking
- **Advanced Metrics** - Agent metrics, system metrics, custom metrics
- **Structured Logging** - Contextual logging, correlation tracking
- **Dashboard Configuration** - Widget configuration, alerts
- **Agent Integration** - Agent instrumentation, operation tracking
- **FastMCP Integration** - Server instrumentation, request tracking

### ✅ Sistema de Seguridad
- **Auth System** - JWT tokens, user authentication, session management
- **Auth Middleware** - Request authentication, authorization
- **Auth Utils** - Token generation, password validation, OAuth
- **DDoS Protection** - Rate limiting, traffic analysis, IP blocking
- **Content Scanning** - SQL injection, XSS, malware detection
- **Security Configuration** - Auth config, rate limiting, compliance

### ✅ Diferenciadores Técnicos
- **Context Persistence Engine** - Storage, retrieval, compression, backup
- **Collaboration Engine** - Session creation, agent coordination
- **Intelligent Router** - Request routing, agent selection, load balancing
- **Context Utils** - Serialization, validation, versioning
- **Collaboration Utils** - Participant management, synchronization
- **Auto Healing Engine** - Health monitoring, anomaly detection
- **Parallel Execution Engine** - Task parallelization, resource allocation

### ✅ Core System
- **Config System** - Environment config, validation, security settings
- **FastMCP Server** - Server initialization, request handling, streaming
- **Orchestration System** - Task orchestration, agent coordination
- **System Exceptions** - Custom exception handling
- **Health Metrics** - Health assessment, monitoring, alerts
- **Deployer System** - Zero-downtime deployment, blue-green deployment

### ✅ Integration Points
- **ContextForge Client** - Context storage, retrieval, search, batch ops
- **Database Operations** - Connection pooling, queries, transactions
- **Vector Store Client** - Embedding generation, similarity search
- **Embedding Service** - Model loading, batch processing, caching
- **Redis Cache Integration** - Cache operations, expiration, statistics
- **Service Integration Patterns** - Service discovery, circuit breaker

## 🚀 Uso

### Requisitos
- Python 3.8+
- Todas las dependencias de desarrollo instaladas

### Instalación de Dependencias
```bash
# Instalar dependencias de testing
make install

# O manualmente
pip install -r test-requirements.txt
```

### Ejecutar Tests

#### 🚀 Ejecución Rápida (Recomendada)
```bash
# Ejecutar todos los tests con cobertura (target 90%+)
make test

# Solo tests unitarios (más rápido)
make test-unit

# Tests de desarrollo
make dev
```

#### 🎯 Ejecución Específica
```bash
# Tests por categoría
make test-agents          # Tests de agentes MCP
make test-security        # Tests de seguridad
make test-observability   # Tests de observabilidad
make test-core           # Tests del core system
make test-technical      # Tests de diferenciadores técnicos
make test-integration-points  # Tests de integration points

# Tests en paralelo
make parallel

# Tests de performance
make benchmark
```

#### ⚡ Opciones Avanzadas
```bash
# Con verbosidad
make test-verbose

# Parar en primer fallo
make test-fast-fail

# Incluir tests lentos
make test-slow

# Ejecutar archivo específico
make test-specific TEST_PATH=tests/test_agents/test_python_executor_agent.py
```

### 📊 Coverage y Reportes

#### Coverage Report
```bash
# Generar reporte de cobertura
make coverage

# Ver estadísticas de cobertura
make coverage-stats

# Generar reporte HTML
make report

# Ver reporte en navegador (automático)
make report
```

#### Reportes Adicionales
```bash
# Reporte JUnit XML (para CI)
pytest --junitxml=test-results.xml

# Reporte XML de cobertura (para CI)
pytest --cov=src --cov-report=xml
```

### 🧹 Limpieza
```bash
# Limpiar archivos de test
make clean

# Limpiar todo y reinstalar dependencias
make clean
make install
```

## 🏃‍♂️ Script de Línea de Comandos

Además del Makefile, puedes usar el script `run_tests.sh`:

```bash
# Ejecutar todos los tests con cobertura
./run_tests.sh --all --coverage

# Ejecutar tests específicos
./run_tests.sh --agents --parallel
./run_tests.sh --security --verbose
./run_tests.sh --keyword "test_auth"

# Mostrar ayuda
./run_tests.sh --help
```

## 🔧 Configuración

### pytest.ini
El archivo `pytest.ini` contiene la configuración principal:
- Marcadores personalizados (`unit`, `integration`, `agent`, etc.)
- Configuración de cobertura (target 90%+)
- Configuración de async testing
- Logging para tests

### Variables de Entorno
```bash
# Configuración de test
export MCP_CORE_ENVIRONMENT=test
export MCP_CORE_DEBUG=true
export MCP_CORE_JWT_SECRET=test-secret
export MCP_CORE_DATABASE_URL=postgresql://test:test@localhost:5432/test_db
export MCP_CORE_REDIS_URL=redis://localhost:6379/0
```

### Fixtures Personalizadas
El archivo `conftest.py` proporciona fixtures comunes:
- `mock_settings` - Mock de configuración
- `mock_database` - Mock de base de datos
- `mock_redis` - Mock de Redis
- `mock_contextforge` - Mock de ContextForge
- `sample_test_data` - Datos de prueba comunes

## 📈 Métricas de Calidad

### Coverage Targets
- **Target mínimo**: 90%
- **Agentes**: 95%
- **Core System**: 90%
- **Security**: 92%
- **Integration**: 85%

### Quality Gates
```bash
# Ejecutar pipeline completo de calidad
make ci

# Verificar calidad del código
make lint

# Verificar tipos
make type-check

# Auditoría de seguridad
make security-audit
```

## 🧪 Testing Patterns

### Async Testing
Todos los tests usan async/await con pytest-asyncio:
```python
async def test_async_operation():
    result = await some_async_function()
    assert result['success'] is True
```

### Mocking Strategy
- Servicios externos: Mock completamente
- Bases de datos: Mock de pool de conexiones
- Redis: Mock de cliente
- APIs externas: Mock de respuestas HTTP

### Fixtures Composition
```python
async def test_with_fixtures(mock_database, mock_redis, sample_test_data):
    # Usar fixtures para setup
    result = await process_with_mocks(mock_database, mock_redis, sample_test_data)
    assert result['success'] is True
```

## 🔄 CI/CD Integration

### GitHub Actions
```yaml
- name: Run Tests
  run: make ci
  
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

### Local Development
```bash
# Pre-commit hooks
make install-hooks

# Ejecutar pre-commit
make pre-commit-run
```

## 📊 Monitoreo de Calidad

### Coverage Trends
- Los reportes HTML muestran coverage por archivo
- Historial de coverage en CI
- Alertas si coverage < 90%

### Performance
- Tests lentos marcados con `@pytest.mark.slow`
- Timeouts configurados para evitar hangs
- Tests paralelos disponibles

### Debugging
```bash
# Tests con más verbosidad
pytest tests/test_agents/ -v -s --tb=long

# Ejecutar test específico con debugging
pytest tests/test_agents/test_python_executor_agent.py::test_specific_function -v -s
```

## 🚨 Troubleshooting

### Errores Comunes

#### Import Errors
```bash
# Asegurar que PYTHONPATH incluye src/
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

#### Coverage Below 90%
```bash
# Identificar archivos con baja cobertura
coverage report --show-missing

# Generar reporte HTML detallado
coverage html
```

#### Async Test Failures
```bash
# Verificar configuración asyncio
pytest --asyncio-mode=auto

# Tests específicos async
pytest -m "async_test"
```

#### Slow Tests
```bash
# Ejecutar solo tests rápidos
make test-unit

# Identificar tests lentos
pytest tests/ --durations=10
```

## 📚 Referencias

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)

## 🤝 Contribuir

Al agregar nuevos tests:
1. Seguir patrones de naming: `test_feature_scenario()`
2. Usar fixtures apropiadas
3. Incluir marcadores relevantes
4. Mantener coverage > 90%
5. Documentar casos complejos

```python
@pytest.mark.agent
@pytest.mark.unit
async def test_new_agent_feature():
    """Test de nueva funcionalidad del agente"""
    # Test implementation
    pass
```

---

**🎯 Target**: 90%+ code coverage mantenido  
**⚡ Performance**: Tests completan en < 5 minutos  
**🔒 Security**: Auditoría automática de código  
**📊 Quality**: Gates de calidad automáticos