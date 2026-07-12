# Suite de Tests - Microsoft 365 Integration

Este directorio contiene la suite completa de tests para el sistema de integración de Microsoft 365.

## 📋 Estructura de Tests

```
tests/
├── unit/                    # Tests unitarios
│   ├── test_word_agent.py      # Tests para Word Agent (521+ líneas)
│   ├── test_excel_agent.py     # Tests para Excel Agent (716+ líneas)
│   ├── test_powerpoint_agent.py # Tests para PowerPoint Agent (779+ líneas)
│   ├── test_outlook_agent.py   # Tests para Outlook Agent (721+ líneas)
│   ├── test_onedrive_agent.py  # Tests para OneDrive Agent (729+ líneas)
│   ├── test_teams_agent.py     # Tests para Teams Agent (916+ líneas)
│   └── test_utils.py           # Tests para utilidades (948+ líneas)
├── integration/             # Tests de integración
│   └── test_graph_client.py    # Tests para Graph API Client (650+ líneas)
├── e2e/                    # Tests end-to-end
│   └── test_workflows.py       # Tests de flujos completos (790+ líneas)
├── conftest.py             # Configuración y fixtures comunes
├── requirements.txt        # Dependencias de testing
└── mocks/                  # Archivos de mock (si necesario)
```

## 🚀 Ejecución de Tests

### Usando Makefile (Recomendado)
```bash
# Setup inicial
make install-dev
make test-setup

# Ejecutar toda la suite
make test-all

# Ejecutar por categoría
make test-unit          # Solo tests unitarios
make test-integration   # Solo tests de integración  
make test-e2e           # Solo tests end-to-end

# Tests específicos por agente
make test-word
make test-excel
make test-powerpoint
make test-outlook
make test-onedrive
make test-teams
make test-utils

# Tests rápidos
make test-fast          # Excluyendo tests lentos
make test-parallel      # Ejecución paralela

# Verificación de código
make lint               # Linting
make format             # Formateo automático
make coverage          # Reporte de cobertura
```

### Usando Script de Python
```bash
# Ejecutar script directamente
python run_tests.py --install-deps  # Instalar dependencias primero
python run_tests.py all            # Todos los tests
python run_tests.py unit           # Solo unitarios
python run_tests.py integration    # Solo integración
python run_tests.py e2e           # Solo end-to-end
python run_tests.py word          # Tests específicos
```

### Usando Pytest Directamente
```bash
# Tests unitarios
pytest tests/unit/ -v --cov=src

# Tests de integración
pytest tests/integration/ -v

# Tests end-to-end
pytest tests/e2e/ -v

# Tests específicos
pytest tests/unit/test_word_agent.py -v
pytest tests/integration/test_graph_client.py -v

# Con cobertura
pytest tests/ --cov=src --cov-report=html --cov-fail-under=85
```

## 📊 Cobertura de Tests

### Cobertura Objetivo
- **Tests Unitarios**: ≥ 85% de cobertura
- **Tests de Integración**: ≥ 80% de cobertura  
- **Tests End-to-End**: Cobertura funcional completa

### Comandos de Cobertura
```bash
# Generar reporte detallado
make coverage

# Reportes específicos
pytest tests/unit/ --cov=src --cov-report=term-missing
pytest tests/integration/ --cov=src/graph --cov-report=html:htmlcov/integration

# Combinar reportes
coverage combine
coverage report
coverage html
```

## 🏷️ Marcadores de Test

Los tests utilizan marcadores para categorización:

```python
# unit - Tests unitarios
@pytest.mark.unit
@pytest.mark.word  # Específico por agente

# integration - Tests de integración
@pytest.mark.integration
@pytest.mark.graph_api

# e2e - Tests end-to-end  
@pytest.mark.e2e

# rendimiento y especiales
@pytest.mark.slow      # Tests que toman tiempo
@pytest.mark.network   # Tests que requieren red
@pytest.mark.auth      # Tests de autenticación
@pytest.mark.mock      # Tests con mocks
```

## 🔧 Configuración

### pytest.ini
- Configuración centralizada de pytest
- Marcadores personalizados
- Configuración de cobertura (≥90%)
- Ignorar warnings específicos

### conftest.py
- Fixtures comunes para todos los tests
- Mocks configurados para Azure AD y Graph API
- Datos de ejemplo para diferentes servicios
- Manejo automático de Redis y MSAL

## 📈 Métricas de Calidad

### Tests Unitarios (4,350+ líneas)
- **Word Agent**: 541 líneas de tests
- **Excel Agent**: 716 líneas de tests  
- **PowerPoint Agent**: 779 líneas de tests
- **Outlook Agent**: 721 líneas de tests
- **OneDrive Agent**: 729 líneas de tests
- **Teams Agent**: 916 líneas de tests
- **Utils**: 948 líneas de tests

### Tests de Integración (650+ líneas)
- Graph API Client completo
- Manejo de rate limiting
- Procesamiento en lotes
- Sincronización delta
- Gestión de webhooks

### Tests End-to-End (790+ líneas)
- Flujo: Documento → Teams → Colaboración
- Flujo: Email → Calendario → Reunión Teams
- Flujo: Análisis de datos → Presentación → Distribución
- Flujo: Creación equipo → Canales → Miembros → Documentos
- Flujo: Aprobación de documentos
- Flujo: Reunión con materiales compartidos
- Manejo de errores y recuperación
- Operaciones concurrentes

## 🐛 Debugging

### Tests con Debug
```bash
# Modo debug con más detalles
make test-debug

# Ejecutar test específico en detalle
pytest tests/unit/test_word_agent.py::TestWordAgent::test_create_document -v -s

# Tests con breakpoint
pytest tests/unit/test_utils.py -v -s --pdb
```

### Logs en Tests
```bash
# Ver logs durante tests
pytest tests/ -v -s --log-cli-level=DEBUG

# Tests con captura de salida
pytest tests/ -v --capture=no
```

## ⚡ Optimización de Tests

### Ejecución Paralela
```bash
# Automática con pytest-xdist
pytest tests/ -n auto

# Con número específico de workers
pytest tests/ -n 4
```

### Tests Rápidos
```bash
# Excluyendo tests marcados como slow
pytest tests/ -m "not slow"

# Solo primeros fallos
pytest tests/ --maxfail=5

# Tests de una categoría específica
pytest tests/unit/ -m "unit and word"
```

## 📁 Reportes Generados

```bash
# Directorio de reportes
test-reports/
├── all-tests.xml          # Reporte JUnit
├── test-report.html       # Reporte HTML interactivo
├── unit-tests.xml         # Tests unitarios
├── integration-tests.xml  # Tests integración
├── e2e-tests.xml         # Tests end-to-end

# Cobertura
htmlcov/
├── index.html            # Reporte principal
├── unit/                 # Cobertura unitarios
└── integration/          # Cobertura integración
```

## 🔄 CI/CD Integration

### GitHub Actions / GitLab CI
```yaml
# Ejemplo de configuración
- name: Install dependencies
  run: make install-dev

- name: Run tests
  run: make ci-test

- name: Linting  
  run: make ci-lint

- name: Upload coverage
  uses: codecov/codecov-action@v1
```

### Pre-commit Hooks
```bash
# Instalar pre-commit
pip install pre-commit

# Configurar hooks
pre-commit install

# Ejecutar manualmente
pre-commit run --all-files
```

## 🧪 Casos de Test Cubiertos

### Funcionalidades Core
- ✅ Autenticación Azure AD
- ✅ Operaciones CRUD en todos los servicios
- ✅ Manejo de rate limiting
- ✅ Reintentos automáticos
- ✅ Circuit breaker pattern
- ✅ Procesamiento en lotes
- ✅ Sincronización delta
- ✅ Gestión de errores
- ✅ Webhooks y notificaciones

### Escenarios de Error
- ✅ Timeouts de red
- ✅ Rate limiting (429)
- ✅ Errores de autenticación (401)
- ✅ Recursos no encontrados (404)
- ✅ Errores del servidor (5xx)
- ✅ Conexiones interrumpidas
- ✅ Tokens expirados
- ✅ Permisos insuficientes

### Performance y Escalabilidad  
- ✅ Operaciones concurrentes
- ✅ Archivos grandes (upload sessions)
- ✅ Lotes de operaciones
- ✅ Cache de tokens
- ✅ Rate limiting distribuido
- ✅ Backoff exponencial

## 📞 Soporte

Para problemas con la suite de tests:

1. **Verificar dependencias**: `make install-dev`
2. **Limpiar cache**: `make clean`
3. **Tests rápidos**: `make test-fast`
4. **Debug específico**: `pytest tests/unit/test_X.py -v -s`

### Logs Útiles
```bash
# Habilitar logs detallados
export LOG_LEVEL=DEBUG
pytest tests/ -v -s

# Logs de coverage
export COVERAGE_DEBUG=1
pytest tests/ --cov=src --cov-report=term-missing
```