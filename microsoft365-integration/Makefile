# Microsoft 365 Integration - Makefile para Testing y Desarrollo

.PHONY: test test-unit test-integration test-e2e test-all install test-setup coverage lint clean help

# Configuración
PYTHON := python3
PIP := pip
SRC := src
TESTS := tests

# Targets principales
help:
	@echo "Microsoft 365 Integration - Comandos Disponibles:"
	@echo ""
	@echo "Testing:"
	@echo "  test-setup     - Instalar dependencias de desarrollo"
	@echo "  test-unit      - Ejecutar tests unitarios"
	@echo "  test-integration - Ejecutar tests de integración"
	@echo "  test-e2e       - Ejecutar tests end-to-end"
	@echo "  test-all       - Ejecutar toda la suite de tests"
	@echo "  test-word      - Tests específicos de Word Agent"
	@echo "  test-excel     - Tests específicos de Excel Agent"
	@echo "  test-teams     - Tests específicos de Teams Agent"
	@echo ""
	@echo "Calidad de código:"
	@echo "  lint           - Ejecutar linters (flake8, black, isort)"
	@echo "  format         - Formatear código automáticamente"
	@echo ""
	@echo "Reportes:"
	@echo "  coverage       - Generar reporte de cobertura"
	@echo "  reports        - Generar todos los reportes"
	@echo ""
	@echo "Utilidades:"
	@echo "  clean          - Limpiar archivos temporales"
	@echo "  install-dev    - Instalar dependencias de desarrollo"

# Setup de testing
test-setup:
	@echo "🔧 Configurando entorno de testing..."
	$(PIP) install -r tests/requirements.txt
	$(PIP) install -r requirements.txt
	@echo "✅ Entorno configurado"

install-dev: test-setup
	@echo "📦 Instalando dependencias de desarrollo..."
	$(PIP) install flake8 black isort mypy
	@echo "✅ Dependencias instaladas"

# Tests por categoría
test-unit:
	@echo "🧪 Ejecutando tests unitarios..."
	$(PYTHON) -m pytest $(TESTS)/unit/ -v --cov=$(SRC) --cov-report=term-missing --cov-report=html:htmlcov/unit --cov-fail-under=85

test-integration:
	@echo "🔗 Ejecutando tests de integración..."
	$(PYTHON) -m pytest $(TESTS)/integration/ -v --cov=$(SRC)/graph --cov-report=term-missing --cov-report=html:htmlcov/integration --cov-fail-under=80

test-e2e:
	@echo "🎯 Ejecutando tests end-to-end..."
	$(PYTHON) -m pytest $(TESTS)/e2e/ -v

test-all:
	@echo "🚀 Ejecutando suite completa de tests..."
	$(PYTHON) -m pytest $(TESTS)/ -v --cov=$(SRC) --cov-report=term-missing --cov-report=html:htmlcov --cov-fail-under=85 --html=test-reports/test-report.html --self-contained-html

# Tests específicos por agente
test-word:
	$(PYTHON) -m pytest $(TESTS)/unit/test_word_agent.py -v --cov=$(SRC)/agents --cov-report=term-missing

test-excel:
	$(PYTHON) -m pytest $(TESTS)/unit/test_excel_agent.py -v --cov=$(SRC)/agents --cov-report=term-missing

test-powerpoint:
	$(PYTHON) -m pytest $(TESTS)/unit/test_powerpoint_agent.py -v --cov=$(SRC)/agents --cov-report=term-missing

test-outlook:
	$(PYTHON) -m pytest $(TESTS)/unit/test_outlook_agent.py -v --cov=$(SRC)/agents --cov-report=term-missing

test-onedrive:
	$(PYTHON) -m pytest $(TESTS)/unit/test_onedrive_agent.py -v --cov=$(SRC)/agents --cov-report=term-missing

test-teams:
	$(PYTHON) -m pytest $(TESTS)/unit/test_teams_agent.py -v --cov=$(SRC)/agents --cov-report=term-missing

test-utils:
	$(PYTHON) -m pytest $(TESTS)/unit/test_utils.py -v --cov=$(SRC)/utils --cov-report=term-missing

test-graph:
	$(PYTHON) -m pytest $(TESTS)/integration/test_graph_client.py -v --cov=$(SRC)/graph --cov-report=term-missing

# Tests con diferentes configuraciones
test-fast:
	@echo "⚡ Ejecutando tests rápidos (excluyendo slow)..."
	$(PYTHON) -m pytest $(TESTS)/ -v -m "not slow" --maxfail=5

test-parallel:
	@echo "🚀 Ejecutando tests en paralelo..."
	$(PYTHON) -m pytest $(TESTS)/ -v -n auto --cov=$(SRC) --cov-report=term-missing

test-debug:
	@echo "🐛 Ejecutando tests en modo debug..."
	$(PYTHON) -m pytest $(TESTS)/ -v -s --tb=long --maxfail=1

# Calidad de código
lint:
	@echo "🔍 Ejecutando linters..."
	@echo "--- Flake8 ---"
	flake8 $(SRC)/ --max-line-length=88 --extend-ignore=E203,W503
	@echo "--- Black ---"
	black --check $(SRC)/
	@echo "--- isort ---"
	isort --check-only $(SRC)/
	@echo "✅ Linting completado"

format:
	@echo "🎨 Formateando código..."
	black $(SRC)/ $(TESTS)/
	isort $(SRC)/ $(TESTS)/
	@echo "✅ Código formateado"

type-check:
	@echo "🔍 Verificación de tipos..."
	mypy $(SRC)/ --ignore-missing-imports
	@echo "✅ Verificación de tipos completada"

# Reportes
coverage:
	@echo "📊 Generando reporte de cobertura..."
	$(PYTHON) -m coverage run -m pytest $(TESTS)/
	$(PYTHON) -m coverage report
	$(PYTHON) -m coverage html
	@echo "📁 Reporte disponible en htmlcov/index.html"

reports: coverage
	@echo "📋 Generando todos los reportes..."
	$(PYTHON) -m pytest $(TESTS)/ --html=test-reports/report.html --self-contained-html --cov=$(SRC) --cov-report=html
	@echo "📁 Reportes en test-reports/"

# Utilidades
clean:
	@echo "🧹 Limpiando archivos temporales..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage .pytest_cache htmlcov test-reports
	@echo "✅ Limpieza completada"

clean-all: clean
	@echo "🧹 Limpiando todo..."
	rm -rf .mypy_cache dist build *.egg-info
	@echo "✅ Limpieza total completada"

# CI/CD
ci-test:
	@echo "🤖 Ejecutando tests para CI..."
	$(PYTHON) -m pytest $(TESTS)/ -v --cov=$(SRC) --cov-fail-under=85 --cov-report=xml --junit-xml=test-reports/junit.xml

ci-lint: lint type-check
	@echo "✅ CI linting completado"

# Desarrollo rápido
dev-setup: install-dev test-setup
	@echo "🚀 Entorno de desarrollo configurado"

quick-test: test-fast lint
	@echo "⚡ Tests rápidos y linting completados"

# Benchmarking
benchmark:
	@echo "⚡ Ejecutando benchmarks..."
	$(PYTHON) -m pytest $(TESTS)/ --benchmark-only --benchmark-html=benchmark-report.html

# Documentación
docs-check:
	@echo "📚 Verificando documentación..."
	python -m pytest --doctest-modules $(SRC)/

# Validación de configuración
validate-config:
	@echo "⚙️ Validando configuración..."
	@python -c "from src.config.settings import Settings; print('✅ Configuración válida')" || echo "❌ Error en configuración"

# Tests de rendimiento específicos
test-performance:
	@echo "🚀 Tests de rendimiento..."
	$(PYTHON) -m pytest $(TESTS)/ -v --benchmark-only -m "slow"