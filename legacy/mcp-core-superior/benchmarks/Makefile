# Performance Benchmarking Suite - Makefile
# Automatización de tareas comunes para benchmarking MCP-Core-Superior vs MiniMax Agent

.PHONY: help install setup demo benchmark-full benchmark-performance load-test-locust load-test-artillery analysis clean test-deps check-agents view-results

# Variables
PYTHON := python3
PIP := pip3
BENCHMARK_DIR := benchmarks
SCRIPTS_DIR := benchmarks/scripts
TOOLS_DIR := benchmarks/tools
LOAD_TESTS_DIR := benchmarks/load_tests

# Colores para output
BOLD := \033[1m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
BLUE := \033[0;34m
NC := \033[0m

help: ## Mostrar ayuda
	@echo "$(BOLD)Performance Benchmarking Suite - Comandos Disponibles$(NC)"
	@echo "=============================================="
	@echo ""
	@echo "$(GREEN)Configuración:$(NC)"
	@echo "  $(YELLOW)make install$(NC)     - Instalar dependencias Python"
	@echo "  $(YELLOW)make setup$(NC)       - Configuración completa del entorno"
	@echo "  $(YELLOW)make test-deps$(NC)   - Verificar dependencias"
	@echo ""
	@echo "$(GREEN)Ejecución de Benchmarks:$(NC)"
	@echo "  $(YELLOW)make demo$(NC)        - Ejecutar demo con datos simulados"
	@echo "  $(YELLOW)make benchmark-full$(NC) - Ejecutar suite completa de benchmarks"
	@echo "  $(YELLOW)make benchmark-performance$(NC) - Solo tests de performance"
	@echo "  $(YELLOW)make load-test-locust$(NC) - Load testing con Locust"
	@echo "  $(YELLOW)make load-test-artillery$(NC) - Load testing con Artillery"
	@echo ""
	@echo "$(GREEN)Análisis:$(NC)"
	@echo "  $(YELLOW)make analysis$(NC)    - Generar análisis comparativo"
	@echo "  $(YELLOW)make view-results$(NC) - Abrir dashboard de resultados"
	@echo ""
	@echo "$(GREEN)Utilidades:$(NC)"
	@echo "  $(YELLOW)make check-agents$(NC) - Verificar estado de agentes"
	@echo "  $(YELLOW)make clean$(NC)        - Limpiar resultados y datos temporales"
	@echo "  $(YELLOW)make monitor$(NC)      - Monitorear sistema durante benchmarks"
	@echo ""
	@echo "$(GREEN)Desarrollo:$(NC)"
	@echo "  $(YELLOW)make test$(NC)         - Ejecutar tests unitarios"
	@echo "  $(YELLOW)make lint$(NC)         - Verificar código con flake8"
	@echo "  $(YELLOW)make format$(NC)       - Formatear código con black"

install: ## Instalar dependencias Python
	@echo "$(BLUE)[INFO]$(NC) Instalando dependencias Python..."
	$(PIP) install --user -r $(BENCHMARK_DIR)/requirements.txt
	@echo "$(GREEN)[SUCCESS]$(NC) Dependencias instaladas"

setup: ## Configuración completa del entorno
	@echo "$(BLUE)[INFO]$(NC) Configurando entorno de benchmarking..."
	@if [ -f "$(BENCHMARK_DIR)/setup_benchmarks.sh" ]; then \
		chmod +x $(BENCHMARK_DIR)/setup_benchmarks.sh; \
		$(BENCHMARK_DIR)/setup_benchmarks.sh; \
	else \
		echo "$(RED)[ERROR]$(NC) Script de setup no encontrado"; \
		exit 1; \
	fi
	@echo "$(GREEN)[SUCCESS]$(NC) Entorno configurado"

demo: ## Ejecutar demo con datos simulados
	@echo "$(BLUE)[INFO]$(NC) Ejecutando demo de benchmarks..."
	$(PYTHON) $(BENCHMARK_DIR)/demo_benchmark.py
	@echo "$(GREEN)[SUCCESS]$(NC) Demo completada. Revisa demo_results/"

benchmark-full: ## Ejecutar suite completa de benchmarks
	@echo "$(BLUE)[INFO]$(NC) Ejecutando suite completa de benchmarks..."
	@make check-agents || echo "$(YELLOW)[WARNING]$(NC) Algunos agentes no están disponibles"
	$(PYTHON) $(SCRIPTS_DIR)/benchmark_orchestrator.py
	@echo "$(GREEN)[SUCCESS]$(NC) Benchmark completo finalizado"

benchmark-performance: ## Solo tests de performance (más rápido)
	@echo "$(BLUE)[INFO]$(NC) Ejecutando solo tests de performance..."
	$(PYTHON) $(SCRIPTS_DIR)/performance_benchmarker.py
	@echo "$(GREEN)[SUCCESS]$(NC) Tests de performance completados"

load-test-locust: ## Load testing con Locust
	@echo "$(BLUE)[INFO]$(NC) Ejecutando load testing con Locust..."
	@echo "$(YELLOW)[INFO]$(NC) Asegúrate de que los agentes estén ejecutándose en puertos 8000 y 8001"
	@if command -v locust >/dev/null 2>&1; then \
		locust -f $(LOAD_TESTS_DIR)/locust_load_test.py --host=http://localhost:8000 --headless --users=50 --spawn-rate=10 --run-time=2m --csv=$(BENCHMARK_DIR)/reports/mcp_locust; \
		echo "$(GREEN)[SUCCESS]$(NC) Locust test completado para MCP-Core-Superior"; \
	else \
		echo "$(RED)[ERROR]$(NC) Locust no está instalado. Ejecute 'make install'"; \
	fi

load-test-artillery: ## Load testing con Artillery
	@echo "$(BLUE)[INFO]$(NC) Ejecutando load testing con Artillery..."
	@if command -v artillery >/dev/null 2>&1; then \
		$(PYTHON) $(LOAD_TESTS_DIR)/artillery_load_test.py; \
		artillery run $(BENCHMARK_DIR)/configs/mcp_load_test.yml --output $(BENCHMARK_DIR)/reports/mcp_artillery.json; \
		echo "$(GREEN)[SUCCESS]$(NC) Artillery test completado"; \
	else \
		echo "$(RED)[ERROR]$(NC) Artillery no está instalado. Ejecute 'make install'"; \
	fi

analysis: ## Generar análisis comparativo
	@echo "$(BLUE)[INFO]$(NC) Generando análisis comparativo..."
	$(PYTHON) $(TOOLS_DIR)/comparative_analysis.py
	@echo "$(GREEN)[SUCCESS]$(NC) Análisis completado. Revisa benchmarks/analysis/"

view-results: ## Abrir dashboard de resultados
	@echo "$(BLUE)[INFO]$(NC) Abriendo dashboard de resultados..."
	@if [ -f "$(BENCHMARK_DIR)/reports/interactive_dashboard.html" ]; then \
		open $(BENCHMARK_DIR)/reports/interactive_dashboard.html 2>/dev/null || \
		xdg-open $(BENCHMARK_DIR)/reports/interactive_dashboard.html 2>/dev/null || \
		echo "$(YELLOW)[INFO]$(NC) Abre manualmente: $(BENCHMARK_DIR)/reports/interactive_dashboard.html"; \
	elif [ -f "$(BENCHMARK_DIR)/demo_results/demo_dashboard.html" ]; then \
		open $(BENCHMARK_DIR)/demo_results/demo_dashboard.html 2>/dev/null || \
		xdg-open $(BENCHMARK_DIR)/demo_results/demo_dashboard.html 2>/dev/null || \
		echo "$(YELLOW)[INFO]$(NC) Abre manualmente: $(BENCHMARK_DIR)/demo_results/demo_dashboard.html"; \
	else \
		echo "$(RED)[ERROR]$(NC) Dashboard no encontrado. Ejecuta 'make demo' primero"; \
	fi

check-agents: ## Verificar estado de agentes
	@echo "$(BLUE)[INFO]$(NC) Verificando estado de agentes..."
	@echo "Verificando MCP-Core-Superior (puerto 8000)..."
	@if curl -s http://localhost:8000/api/health >/dev/null; then \
		echo "$(GREEN)✅ MCP-Core-Superior: ACTIVO$(NC)"; \
	else \
		echo "$(RED)❌ MCP-Core-Superior: NO DISPONIBLE$(NC)"; \
		echo "$(YELLOW)   Inicia con: cd $(PROJECT_ROOT) && python src/core/fastmcp_server.py$(NC)"; \
	fi
	@echo "Verificando MiniMax Agent (puerto 8001)..."
	@if curl -s http://localhost:8001/health >/dev/null; then \
		echo "$(GREEN)✅ MiniMax Agent: ACTIVO$(NC)"; \
	else \
		echo "$(RED)❌ MiniMax Agent: NO DISPONIBLE$(NC)"; \
		echo "$(YELLOW)   Asegúrate de que el puerto 8001 esté disponible$(NC)"; \
	fi

clean: ## Limpiar resultados y datos temporales
	@echo "$(BLUE)[INFO]$(NC) Limpiando archivos temporales..."
	@rm -rf $(BENCHMARK_DIR)/reports/* \
	        $(BENCHMARK_DIR)/analysis/* \
	        $(BENCHMARK_DIR)/logs/* \
	        $(BENCHMARK_DIR)/demo_results/* \
	        $(BENCHMARK_DIR)/results/* \
	        *.csv \
	        *.log
	@echo "$(GREEN)[SUCCESS]$(NC) Limpieza completada"

monitor: ## Monitorear sistema durante benchmarks
	@echo "$(BLUE)[INFO]$(NC) Iniciando monitor del sistema..."
	@if [ -f "$(TOOLS_DIR)/system_monitor.py" ]; then \
		$(PYTHON) $(TOOLS_DIR)/system_monitor.py; \
	else \
		echo "$(RED)[ERROR]$(NC) Script de monitoreo no encontrado"; \
	fi

test: ## Ejecutar tests unitarios
	@echo "$(BLUE)[INFO]$(NC) Ejecutando tests unitarios..."
	@if command -v pytest >/dev/null 2>&1; then \
		pytest $(BENCHMARK_DIR)/tests/ -v; \
	else \
		echo "$(YELLOW)[INFO]$(NC) pytest no está instalado. Instalando..."; \
		$(PIP) install --user pytest pytest-asyncio; \
		pytest $(BENCHMARK_DIR)/tests/ -v; \
	fi

lint: ## Verificar código con flake8
	@echo "$(BLUE)[INFO]$(NC) Verificando código con flake8..."
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 $(BENCHMARK_DIR)/scripts/ $(BENCHMARK_DIR)/tools/ --max-line-length=100 --ignore=E203,W503; \
	else \
		echo "$(YELLOW)[INFO]$(NC) flake8 no está instalado. Instalando..."; \
		$(PIP) install --user flake8; \
		flake8 $(BENCHMARK_DIR)/scripts/ $(BENCHMARK_DIR)/tools/ --max-line-length=100 --ignore=E203,W503; \
	fi

format: ## Formatear código con black
	@echo "$(BLUE)[INFO]$(NC) Formateando código con black..."
	@if command -v black >/dev/null 2>&1; then \
		black $(BENCHMARK_DIR)/scripts/ $(BENCHMARK_DIR)/tools/ --line-length=100; \
	else \
		echo "$(YELLOW)[INFO]$(NC) black no está instalado. Instalando..."; \
		$(PIP) install --user black; \
		black $(BENCHMARK_DIR)/scripts/ $(BENCHMARK_DIR)/tools/ --line-length=100; \
	fi

test-deps: ## Verificar dependencias
	@echo "$(BLUE)[INFO]$(NC) Verificando dependencias..."
	@echo "Verificando Python 3.8+..."
	@$(PYTHON) -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" && echo "$(GREEN)✅ Python OK$(NC)" || echo "$(RED)❌ Python 3.8+ requerido$(NC)"
	@echo "Verificando dependencias críticas..."
	@$(PYTHON) -c "import numpy" && echo "$(GREEN)✅ numpy$(NC)" || echo "$(RED)❌ numpy$(NC)"
	@$(PYTHON) -c "import pandas" && echo "$(GREEN)✅ pandas$(NC)" || echo "$(RED)❌ pandas$(NC)"
	@$(PYTHON) -c "import matplotlib" && echo "$(GREEN)✅ matplotlib$(NC)" || echo "$(RED)❌ matplotlib$(NC)"
	@echo "Verificando herramientas de load testing..."
	@command -v locust >/dev/null 2>&1 && echo "$(GREEN)✅ locust$(NC)" || echo "$(YELLOW)⚠️  locust (opcional)$(NC)"
	@command -v artillery >/dev/null 2>&1 && echo "$(GREEN)✅ artillery$(NC)" || echo "$(YELLOW)⚠️  artillery (opcional)$(NC)"

# Tareas de desarrollo específicas
quick-test: ## Test rápido solo con demo
	@echo "$(BLUE)[INFO]$(NC) Ejecutando test rápido (demo + verificación básica)..."
	@make demo
	@make check-agents

full-workflow: ## Flujo completo: setup -> demo -> benchmark
	@echo "$(BLUE)[INFO]$(NC) Ejecutando flujo completo..."
	@make setup
	@make demo
	@make benchmark-performance
	@make analysis
	@echo "$(GREEN)[SUCCESS]$(NC) Flujo completo finalizado"

# Ayuda para configurar agentes
setup-agents: ## Mostrar ayuda para configurar agentes
	@echo "$(BLUE)CONFIGURACIÓN DE AGENTES PARA BENCHMARKING$(NC)"
	@echo "=========================================="
	@echo ""
	@echo "$(GREEN)1. MCP-Core-Superior:$(NC)"
	@echo "   cd $(PROJECT_ROOT)"
	@echo "   python src/core/fastmcp_server.py"
	@echo "   (Se ejecutará en http://localhost:8000)"
	@echo ""
	@echo "$(GREEN)2. MiniMax Agent:$(NC)"
	@echo "   Asegúrate de que esté ejecutándose en http://localhost:8001"
	@echo "   O modifica la configuración en benchmarks/configs/benchmark_config.yaml"
	@echo ""
	@echo "$(GREEN)3. Verificar estado:$(NC)"
	@echo "   make check-agents"

# Tareas de reporte
report-html: ## Generar reporte HTML de resultados
	@echo "$(BLUE)[INFO]$(NC) Generando reporte HTML..."
	@if [ -f "$(BENCHMARK_DIR)/reports/benchmark_report.html" ]; then \
		open $(BENCHMARK_DIR)/reports/benchmark_report.html 2>/dev/null || \
		echo "$(YELLOW)[INFO]$(NC) Abre manualmente: $(BENCHMARK_DIR)/reports/benchmark_report.html"; \
	else \
		echo "$(RED)[ERROR]$(NC) Reporte HTML no encontrado"; \
	fi

# Tarea para mostrar estadísticas
stats: ## Mostrar estadísticas del último benchmark
	@echo "$(BLUE)[INFO]$(NC) Estadísticas del último benchmark..."
	@if [ -f "$(BENCHMARK_DIR)/reports/benchmark_results.json" ]; then \
		$(PYTHON) -c "import json; data=json.load(open('$(BENCHMARK_DIR)/reports/benchmark_results.json')); print(f'Total de tests: {len(data.get(\"results\", []))}'); print(f'Duración: {data.get(\"execution_summary\", {}).get(\"total_duration\", \"N/A\")}');"; \
	else \
		echo "$(YELLOW)[INFO]$(NC) No se encontraron resultados. Ejecuta 'make benchmark-full' primero"; \
	fi