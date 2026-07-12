# Makefile para MCP Core Superior - Test Suite
# Target: 90%+ code coverage

.PHONY: help install test test-all test-unit test-integration test-agents test-security test-observability test-core test-technical test-integration-points coverage report clean benchmark parallel security-audit

# Variables
PYTHON := python
PIP := pip
PYTEST := python -m pytest
TEST_DIR := tests
COVERAGE_MIN := 90

# Colores para output
BOLD := \033[1m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
BLUE := \033[0;34m
RESET := \033[0m

# Mensaje de ayuda
help:
	@echo "$(BOLD)MCP Core Superior - Test Suite$(RESET)"
	@echo ""
	@echo "$(BOLD)Comandos disponibles:$(RESET)"
	@echo "  $(GREEN)make install$(RESET)              Instalar dependencias de testing"
	@echo "  $(GREEN)make test$(RESET)                 Ejecutar todos los tests con cobertura"
	@echo "  $(GREEN)make test-all$(RESET)            Ejecutar todos los tests (sin cobertura)"
	@echo "  $(GREEN)make test-unit$(RESET)           Ejecutar solo tests unitarios"
	@echo "  $(GREEN)make test-integration$(RESET)    Ejecutar solo tests de integración"
	@echo "  $(GREEN)make test-agents$(RESET)         Ejecutar tests de agentes MCP"
	@echo "  $(GREEN)make test-security$(RESET)       Ejecutar tests de seguridad"
	@echo "  $(GREEN)make test-observability$(RESET)  Ejecutar tests de observabilidad"
	@echo "  $(GREEN)make test-core$(RESET)           Ejecutar tests del core system"
	@echo "  $(GREEN)make test-technical$(RESET)      Ejecutar tests de diferenciadores técnicos"
	@echo "  $(GREEN)make test-integration-points$(RESET) Ejecutar tests de integration points"
	@echo "  $(GREEN)make coverage$(RESET)            Ejecutar tests con reporte de cobertura"
	@echo "  $(GREEN)make report$(RESET)              Generar reporte HTML de cobertura"
	@echo "  $(GREEN)make parallel$(RESET)            Ejecutar tests en paralelo"
	@echo "  $(GREEN)make benchmark$(RESET)           Ejecutar tests de performance"
	@echo "  $(GREEN)make security-audit$(RESET)      Ejecutar auditoría de seguridad"
	@echo "  $(GREEN)make clean$(RESET)               Limpiar archivos de test"
	@echo ""
	@echo "$(BOLD)Ejemplos:$(RESET)"
	@echo "  make test coverage=90"
	@echo "  make test-unit verbose=1"
	@echo "  make test-agents parallel=1"
	@echo "  make benchmark slow=1"

# Instalar dependencias
install:
	@echo "$(BLUE)[INFO]$(RESET) Instalando dependencias de testing..."
	$(PIP) install -r test-requirements.txt
	@echo "$(GREEN)[SUCCESS]$(RESET) Dependencias instaladas"

# Ejecutar todos los tests con cobertura (por defecto)
test: coverage

# Ejecutar todos los tests
test-all:
	@echo "$(BLUE)[INFO]$(RESET) Ejecutando todos los tests..."
	$(PYTEST) tests/ -v --tb=short --maxfail=5
	@echo "$(GREEN)[SUCCESS]$(RESET) Tests completados"

# Ejecutar tests unitarios
test-unit:
	@echo "$(BLUE)[INFO]$(RESET) Ejecutando tests unitarios..."
	$(PYTEST) tests/ -m "unit" -v --tb=short
	@echo "$(GREEN)[SUCCESS]$(RESET) Tests unitarios completados"

# Ejecutar tests de integración
test-integration:
	@echo "$(BLUE)[INFO]$(RESET) Ejecutando tests de integración..."
	$(PYTEST) tests/ -m "integration" -v --tb=short
	@echo "$(GREEN)[SUCCESS]$(RESET) Tests de integración completados"

# Ejecutar tests de agentes
test-agents:
	@echo "$(BLUE)[INFO]$(RESET) Ejecutando tests de agentes MCP..."
	$(PYTEST) tests/test_agents/ -v --tb=short
	@echo "$(GREEN)[SUCCESS]$(RESET) Tests de agentes completados"

# Ejecutar tests de seguridad
test-security:
	@echo "$(BLUE)[INFO]$(RESET) Ejecutando tests de seguridad..."
	$(PYTEST) tests/test_security/ -v --tb=short
	@echo "$(GREEN)[SUCCESS]$(RESET) Tests de seguridad completados"

# Ejecutar tests de observabilidad
test-observability:
	@echo "$(BLUE)[INFO]$(RESET) Ejecutando tests de observabilidad..."
	$(PYTEST) tests/test_observability/ -v --tb=short
	@echo "$(GREEN)[SUCCESS]$(RESET) Tests de observabilidad completados"

# Ejecutar tests del core
test-core:
	@echo "$(BLUE)[INFO]$(RESET) Ejecutando tests del core system..."
	$(PYTEST) tests/test_core/ -v --tb=short
	@echo "$(GREEN)[SUCCESS]$(RESET) Tests del core completados"

# Ejecutar tests de diferenciadores técnicos
test-technical:
	@echo "$(BLUE)[INFO]$(RESET) Ejecutando tests de diferenciadores técnicos..."
	$(PYTEST) tests/test_technical/ -v --tb=short
	@echo "$(GREEN)[SUCCESS]$(RESET) Tests técnicos completados"

# Ejecutar tests de integration points
test-integration-points:
	@echo "$(BLUE)[INFO]$(RESET) Ejecutando tests de integration points..."
	$(PYTEST) tests/test_integration/ -v --tb=short
	@echo "$(GREEN)[SUCCESS]$(RESET) Tests de integration points completados"

# Ejecutar tests con cobertura
coverage:
	@echo "$(BLUE)[INFO]$(RESET) Ejecutando tests con cobertura..."
	$(PYTEST) tests/ \
		--cov=src \
		--cov-report=term-missing \
		--cov-report=html \
		--cov-report=xml \
		--cov-fail-under=$(COVERAGE_MIN) \
		--junitxml=test-results.xml \
		-m "not slow" \
		-v
	@echo "$(GREEN)[SUCCESS]$(RESET) Cobertura mínima: $(COVERAGE_MIN)%"

# Generar reporte HTML
report:
	@echo "$(BLUE)[INFO]$(RESET) Generando reporte HTML..."
	@if [ -f "htmlcov/index.html" ]; then \
		echo "$(GREEN)[SUCCESS]$(RESET) Reporte generado en htmlcov/index.html"; \
		echo "$(BLUE)[INFO]$(RESET) Para abrir el reporte:"; \
		echo "  - Linux: xdg-open htmlcov/index.html"; \
		echo "  - macOS: open htmlcov/index.html"; \
		echo "  - Windows: start htmlcov/index.html"; \
	else \
		echo "$(YELLOW)[WARNING]$(RESET) Ejecute 'make coverage' primero para generar el reporte"; \
	fi

# Ejecutar tests en paralelo
parallel:
	@echo "$(BLUE)[INFO]$(RESET) Ejecutando tests en paralelo..."
	$(PYTEST) tests/ -n auto --tb=short -v
	@echo "$(GREEN)[SUCCESS]$(RESET) Tests en paralelo completados"

# Ejecutar tests de performance/benchmark
benchmark:
	@echo "$(BLUE)[INFO]$(RESET) Ejecutando tests de performance..."
	$(PYTEST) tests/ -m "benchmark" -v --tb=short
	@echo "$(GREEN)[SUCCESS]$(RESET) Tests de performance completados"

# Ejecutar tests incluyendo los lentos
test-slow:
	@echo "$(BLUE)[INFO]$(RESET) Ejecutando todos los tests (incluyendo lentos)..."
	$(PYTEST) tests/ -v --tb=short --timeout=600
	@echo "$(GREEN)[SUCCESS]$(RESET) Tests completos (incluyendo lentos)"

# Auditoría de seguridad
security-audit:
	@echo "$(BLUE)[INFO]$(RESET) Ejecutando auditoría de seguridad..."
	bandit -r src/ -f json -o security-report.json || true
	bandit -r src/ || true
	@echo "$(GREEN)[SUCCESS]$(RESET) Auditoría de seguridad completada"

# Verificar calidad del código
lint:
	@echo "$(BLUE)[INFO]$(RESET) Verificando calidad del código..."
	flake8 src/ tests/
	black --check src/ tests/
	isort --check-only src/ tests/
	@echo "$(GREEN)[SUCCESS]$(RESET) Calidad del código verificada"

# Formatear código
format:
	@echo "$(BLUE)[INFO]$(RESET) Formateando código..."
	black src/ tests/
	isort src/ tests/
	@echo "$(GREEN)[SUCCESS]$(RESET) Código formateado"

# Verificar tipos
type-check:
	@echo "$(BLUE)[INFO]$(RESET) Verificando tipos..."
	mypy src/
	@echo "$(GREEN)[SUCCESS]$(RESET) Verificación de tipos completada"

# Ejecutar tests con opciones específicas
test-verbose:
	$(PYTEST) tests/ -v -s

test-fast-fail:
	$(PYTEST) tests/ -x -v

test-specific:
	@echo "$(BLUE)[INFO]$(RESET) Ejecutando tests específicos..."
	@echo "Uso: make test-specific TEST_PATH=tests/test_agents/test_python_executor_agent.py"
	$(PYTEST) $(TEST_PATH) -v

# Limpiar archivos de test
clean:
	@echo "$(BLUE)[INFO]$(RESET) Limpiando archivos de test..."
	rm -rf htmlcov/ .pytest_cache/ test-results.xml coverage.xml
	rm -rf security-report.json
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)[SUCCESS]$(RESET) Limpieza completada"

# Ejecutar CI pipeline completo
ci: install clean lint type-check coverage
	@echo "$(GREEN)[SUCCESS]$(RESET) CI pipeline completado exitosamente"

# Ejecutar tests de desarrollo (rápido)
dev: install test-unit test-security test-observability
	@echo "$(GREEN)[SUCCESS]$(RESET) Tests de desarrollo completados"

# Ejecutar tests completos para release
release: install clean lint type-check test coverage security-audit
	@echo "$(GREEN)[SUCCESS]$(RESET) Tests de release completados"

# Mostrar estadísticas de cobertura
coverage-stats:
	@echo "$(BLUE)[INFO]$(RESET) Estadísticas de cobertura:"
	@if [ -f "coverage.xml" ]; then \
		grep "line-rate" coverage.xml | head -1 | sed 's/.*line-rate="\([0-9.]*\)".*/Cobertura: \1%/' | bc -l | xargs -I {} echo "  {}"; \
	else \
		echo "$(YELLOW)[WARNING]$(RESET) Ejecute 'make coverage' primero"; \
	fi

# Instalar pre-commit hooks
install-hooks:
	@echo "$(BLUE)[INFO]$(RESET) Instalando pre-commit hooks..."
	pre-commit install
	@echo "$(GREEN)[SUCCESS]$(RESET) Pre-commit hooks instalados"

# Ejecutar pre-commit en todos los archivos
pre-commit-run:
	@echo "$(BLUE)[INFO]$(RESET) Ejecutando pre-commit..."
	pre-commit run --all-files
	@echo "$(GREEN)[SUCCESS]$(RESET) Pre-commit completado"