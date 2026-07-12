#!/usr/bin/env python3
"""
🎨 Sistema de Templates y Casos de Uso - MCP Server Superior
============================================================

Generador de templates y casos de uso predefinidos

Autor: MiniMax Agent
Fecha: 2025-11-04
Versión: 1.0.0
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any
import subprocess
import sys

# Colores
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_banner():
    """Banner del sistema de templates"""
    banner = f"""
{Colors.BLUE}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════════════════╗
║                       🎨 SISTEMA DE TEMPLATES Y CASOS DE USO                 ║
║                         MCP Server Superior v3.1.0                           ║
║                    Templates Predefinidos - De Idea a Código en Minutos      ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Colors.END}

{Colors.GREEN}✅ Templates listos para usar{Colors.END}
{Colors.GREEN}✅ Casos de uso documentados{Colors.END}
{Colors.GREEN}✅ Código de ejemplo incluido{Colors.END}
{Colors.GREEN}✅ Configuraciones automáticas{Colors.END}
"""
    print(banner)

class TemplateManager:
    """Gestor de templates del sistema"""
    
    def __init__(self):
        self.templates_dir = Path("templates")
        self.templates_dir.mkdir(exist_ok=True)
        
        # Crear directorios de templates
        (self.templates_dir / "agent_configs").mkdir(exist_ok=True)
        (self.templates_dir / "use_cases").mkdir(exist_ok=True)
        (self.templates_dir / "code_examples").mkdir(exist_ok=True)
        (self.templates_dir / "workflows").mkdir(exist_ok=True)

    def create_agent_templates(self):
        """Crear templates de configuración de agentes"""
        print(f"\n{Colors.BLUE}🔧 Creando templates de agentes...{Colors.END}")
        
        # Template Git Operations Agent
        git_config = {
            "agent_name": "Git Operations Agent",
            "description": "Automatiza operaciones de Git, GitHub y GitLab",
            "enabled": True,
            "capabilities": [
                "Repository creation and management",
                "Branch operations and merges",
                "Pull request automation",
                "Issue tracking and management",
                "Release preparation"
            ],
            "api_keys_required": ["GITHUB_TOKEN", "GITLAB_TOKEN"],
            "configuration": {
                "max_concurrent_operations": 5,
                "auto_commit_messages": True,
                "branch_prefix": "feature/",
                "default_branch": "main"
            },
            "code_example": '''
# Ejemplo de uso del Git Operations Agent
import asyncio
from mcp_agents.git_agent import GitAgent

async def example_git_operations():
    git_agent = GitAgent()
    
    # Crear repositorio
    repo = await git_agent.create_repository(
        name="mi-proyecto",
        description="Mi proyecto awesome",
        private=False
    )
    
    # Crear branch
    await git_agent.create_branch(
        repository=repo["name"],
        branch_name="feature/nueva-funcionalidad",
        from_branch="main"
    )
    
    # Hacer commit
    await git_agent.commit_changes(
        repository=repo["name"],
        files=["src/main.py", "README.md"],
        message="Add: Nueva funcionalidad increíble"
    )

# Ejecutar ejemplo
asyncio.run(example_git_operations())
            '''
        }
        
        # Template Web Scraping Agent
        web_config = {
            "agent_name": "Web Scraping Agent",
            "description": "Navegación web automatizada y extracción de datos",
            "enabled": True,
            "capabilities": [
                "JavaScript rendering",
                "Form automation",
                "Data extraction",
                "Screenshot capture",
                "Multi-page navigation"
            ],
            "configuration": {
                "user_agent": "MCP-Scraper-Bot/1.0",
                "timeout": 30,
                "max_pages": 100,
                "screenshot_on_error": True
            },
            "code_example": '''
# Ejemplo de uso del Web Scraping Agent
import asyncio
from mcp_agents.web_agent import WebAgent

async def example_web_scraping():
    web_agent = WebAgent()
    
    # Navegar a sitio web
    await web_agent.navigate("https://ejemplo.com")
    
    # Extraer datos de tabla
    data = await web_agent.extract_table_data("table.products")
    
    # Capturar screenshot
    await web_agent.take_screenshot("page_screenshot.png")
    
    # Llenar formulario
    await web_agent.fill_form({
        "email": "usuario@ejemplo.com",
        "password": "mi_password"
    })

# Ejecutar ejemplo
asyncio.run(example_web_scraping())
            '''
        }
        
        # Template Database Agent
        db_config = {
            "agent_name": "Database Operations Agent",
            "description": "Operaciones de base de datos y análisis de datos",
            "enabled": True,
            "capabilities": [
                "CRUD operations",
                "Schema management",
                "Query optimization",
                "Data import/export",
                "Backup automation"
            ],
            "configuration": {
                "connection_pool_size": 10,
                "query_timeout": 60,
                "auto_backup": True,
                "backup_interval_hours": 24
            },
            "code_example": '''
# Ejemplo de uso del Database Agent
import asyncio
from mcp_agents.database_agent import DatabaseAgent

async def example_database_operations():
    db_agent = DatabaseAgent()
    
    # Crear tabla
    await db_agent.create_table(
        "usuarios",
        {
            "id": "SERIAL PRIMARY KEY",
            "nombre": "VARCHAR(100)",
            "email": "VARCHAR(150) UNIQUE",
            "fecha_registro": "TIMESTAMP DEFAULT NOW()"
        }
    )
    
    # Insertar datos
    await db_agent.insert("usuarios", {
        "nombre": "Juan Pérez",
        "email": "juan@ejemplo.com"
    })
    
    # Consultar datos
    usuarios = await db_agent.query("SELECT * FROM usuarios")
    print(usuarios)

# Ejecutar ejemplo
asyncio.run(example_database_operations())
            '''
        }
        
        # Guardar templates
        templates = {
            "git_operations": git_config,
            "web_scraping": web_config,
            "database_operations": db_config
        }
        
        for name, config in templates.items():
            with open(self.templates_dir / "agent_configs" / f"{name}.json", "w") as f:
                json.dump(config, f, indent=2)
        
        print(f"  {Colors.GREEN}✅ 3 templates de agentes creados{Colors.END}")

    def create_use_case_templates(self):
        """Crear templates de casos de uso"""
        print(f"\n{Colors.BLUE}📋 Creando casos de uso predefinidos...{Colors.END}")
        
        # Caso de uso: Automatización de Desarrollo
        dev_case = {
            "title": "Automatización Completa de Desarrollo",
            "description": "Setup completo para equipos de desarrollo con Git, CI/CD y deployment",
            "difficulty": "Intermedio",
            "time_estimate": "30 minutos",
            "use_cases": [
                "Automatización de commits y PRs",
                "Deployment automático",
                "Testing y quality assurance",
                "Documentation generation"
            ],
            "agents_used": ["git_operations", "file_processing", "web_scraping"],
            "prerequisites": [
                "API key de GitHub o GitLab",
                "Acceso a repositorio de código",
                "Configuración de CI/CD (opcional)"
            ],
            "steps": [
                {
                    "step": 1,
                    "title": "Configurar Git Operations Agent",
                    "description": "Conectar con repositorio de GitHub/GitLab",
                    "command": "python setup_wizard.py --agent git --config"
                },
                {
                    "step": 2,
                    "title": "Configurar workflow de commits",
                    "description": "Automatizar commits con mensajes estructurados",
                    "code": '''
import asyncio
from mcp_agents.git_agent import GitAgent

async def setup_auto_commits():
    git_agent = GitAgent()
    
    # Configurar hooks de commit automático
    await git_agent.setup_auto_commit_hooks({
        "pattern": "*.py",
        "message_template": "feat: {files} - Automated commit",
        "lint_check": True
    })
                    '''
                },
                {
                    "step": 3,
                    "title": "Configurar deployment automático",
                    "description": "Deploy automático cuando se hace merge",
                    "code": '''
# Configurar webhooks para deployment automático
WEBHOOK_CONFIG = {
    "events": ["push", "pull_request"],
    "deployment_branch": "main",
    "auto_deploy": True,
    "notification_webhook": "https://hooks.slack.com/..."
}
                    '''
                }
            ],
            "next_steps": [
                "Configurar monitoreo de performance",
                "Implementar testing automatizado",
                "Configurar alertas de error"
            ]
        }
        
        # Caso de uso: Extracción de Datos Masiva
        data_case = {
            "title": "Extracción de Datos Masiva",
            "description": "Pipeline completo para extraer y procesar datos de múltiples fuentes",
            "difficulty": "Avanzado",
            "time_estimate": "45 minutos",
            "use_cases": [
                "Web scraping a gran escala",
                "Análisis de competencia",
                "Monitoring de precios",
                "Research de mercado"
            ],
            "agents_used": ["web_scraping", "file_processing", "database_operations"],
            "prerequisites": [
                "Proxy/VPN configurado (para múltiples requests)",
                "Base de datos para almacenar resultados",
                "Almacenamiento para archivos descargados"
            ],
            "steps": [
                {
                    "step": 1,
                    "title": "Configurar Web Scraping Agent",
                    "description": "Setup para scraping masivo",
                    "configuration": {
                        "max_concurrent_sessions": 10,
                        "delay_between_requests": 2,
                        "user_agents": ["Bot1", "Bot2", "Bot3"],
                        "proxy_rotation": True
                    }
                },
                {
                    "step": 2,
                    "title": "Crear pipeline de procesamiento",
                    "description": "Pipeline para limpiar y estructurar datos",
                    "code": '''
import asyncio
from mcp_agents.web_agent import WebAgent
from mcp_agents.file_agent import FileAgent

async def data_extraction_pipeline(urls):
    web_agent = WebAgent()
    file_agent = FileAgent()
    
    # Extraer datos de todas las URLs
    for url in urls:
        data = await web_agent.extract_structured_data(url)
        await file_agent.save_json(f"data/extracted_{url.hash()}.json", data)
    '''
                }
            ]
        }
        
        # Caso de uso: Business Intelligence Automatizado
        bi_case = {
            "title": "Business Intelligence Automatizado",
            "description": "Sistema automatizado de análisis de datos y reportes",
            "difficulty": "Intermedio",
            "time_estimate": "35 minutos",
            "use_cases": [
                "Reportes automáticos",
                "Análisis de tendencias",
                "KPIs en tiempo real",
                "Alertas de negocio"
            ],
            "agents_used": ["database_operations", "file_processing", "search_agent"],
            "prerequisites": [
                "Acceso a base de datos de negocio",
                "Configuración de métricas clave",
                "Sistema de almacenamiento de reportes"
            ]
        }
        
        use_cases = {
            "desarrollo_automatizado": dev_case,
            "extraccion_datos_masiva": data_case,
            "business_intelligence": bi_case
        }
        
        for name, case in use_cases.items():
            with open(self.templates_dir / "use_cases" / f"{name}.json", "w") as f:
                json.dump(case, f, indent=2)
        
        print(f"  {Colors.GREEN}✅ 3 casos de uso creados{Colors.END}")

    def create_code_examples(self):
        """Crear ejemplos de código completos"""
        print(f"\n{Colors.BLUE}💻 Creando ejemplos de código...{Colors.END}")
        
        # Ejemplo: Multi-agent workflow
        workflow_example = '''
"""
Ejemplo: Workflow Multi-Agente Completo
=====================================
Este ejemplo muestra cómo coordinar múltiples agentes para una tarea compleja.
"""

import asyncio
from mcp_agents import GitAgent, WebAgent, FileAgent, DatabaseAgent

async def complete_project_setup():
    """
    Setup completo de un proyecto que incluye:
    1. Crear repositorio en GitHub
    2. Extraer template de sitio web
    3. Procesar archivos y configurar base de datos
    4. Deployment automatizado
    """
    
    # Inicializar agentes
    git_agent = GitAgent()
    web_agent = WebAgent()
    file_agent = FileAgent()
    db_agent = DatabaseAgent()
    
    print("🚀 Iniciando setup completo del proyecto...")
    
    # 1. Crear repositorio
    repo = await git_agent.create_repository(
        name="mi-proyecto-awesome",
        description="Proyecto creado con MCP Server Superior",
        private=False
    )
    print(f"✅ Repositorio creado: {repo['name']}")
    
    # 2. Clonar y configurar proyecto
    await git_agent.clone_repository(
        repo["clone_url"],
        "./mi-proyecto"
    )
    print("✅ Proyecto clonado")
    
    # 3. Procesar archivos de template
    template_files = await file_agent.get_template_files("web-app")
    for file_path, content in template_files.items():
        await file_agent.write_file(f"mi-proyecto/{file_path}", content)
    print("✅ Template aplicado")
    
    # 4. Configurar base de datos
    await db_agent.create_tables_from_schema("web-app-schema.sql")
    print("✅ Base de datos configurada")
    
    # 5. Commit y push inicial
    await git_agent.commit_all_changes(
        repository=repo["name"],
        message="Initial commit: Project setup with MCP Server Superior"
    )
    await git_agent.push_repository(repo["name"])
    print("✅ Cambios subidos a GitHub")
    
    # 6. Deployment (si está configurado)
    try:
        await git_agent.trigger_deployment(
            repository=repo["name"],
            branch="main"
        )
        print("✅ Deployment iniciado")
    except Exception as e:
        print(f"⚠️  Deployment no configurado: {e}")
    
    print("🎉 Setup completo finalizado!")

# Ejecutar ejemplo
if __name__ == "__main__":
    asyncio.run(complete_project_setup())
        '''
        
        # Ejemplo: Data extraction pipeline
        data_pipeline = '''
"""
Ejemplo: Pipeline de Extracción de Datos
======================================
Extrae datos de múltiples fuentes y genera reportes automatizados.
"""

import asyncio
from mcp_agents import WebAgent, FileAgent, DatabaseAgent
import json
from datetime import datetime

async def extract_market_data():
    """
    Extrae datos de mercado de múltiples fuentes y genera reporte
    """
    
    web_agent = WebAgent()
    file_agent = FileAgent()
    db_agent = DatabaseAgent()
    
    # URLs de sitios a monitorear
    target_sites = [
        "https://ejemplo1.com/productos",
        "https://ejemplo2.com/precios",
        "https://ejemplo3.com/ofertas"
    ]
    
    all_data = []
    
    for site in target_sites:
        print(f"🔍 Extrayendo datos de {site}...")
        
        # Extraer datos estructurados
        try:
            data = await web_agent.extract_structured_data(site)
            data["source"] = site
            data["extracted_at"] = datetime.now().isoformat()
            all_data.append(data)
        except Exception as e:
            print(f"❌ Error extrayendo de {site}: {e}")
    
    # Guardar datos en archivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    await file_agent.save_json(f"data/market_data_{timestamp}.json", all_data)
    
    # Guardar en base de datos
    for item in all_data:
        await db_agent.insert("market_data", item)
    
    # Generar reporte
    await generate_market_report(all_data)
    
    print("✅ Pipeline de extracción completado")

async def generate_market_report(data):
    """
    Genera reporte automatizado de los datos extraídos
    """
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_sources": len(data),
        "summary": {
            "total_products": sum(len(item.get("products", [])) for item in data),
            "price_range": {
                "min": min(item.get("min_price", float('inf')) for item in data if item.get("min_price")),
                "max": max(item.get("max_price", 0) for item in data if item.get("max_price"))
            }
        },
        "recommendations": [
            "Monitor price changes in next 24h",
            "Check for new product launches",
            "Review competitor pricing"
        ]
    }
    
    await file_agent.save_json("reports/market_analysis.json", report)
    print("📊 Reporte generado: reports/market_analysis.json")

# Ejecutar ejemplo
if __name__ == "__main__":
    asyncio.run(extract_market_data())
        '''
        
        # Guardar ejemplos
        examples = {
            "multi_agent_workflow.py": workflow_example,
            "data_extraction_pipeline.py": data_pipeline
        }
        
        for filename, content in examples.items():
            with open(self.templates_dir / "code_examples" / filename, "w") as f:
                f.write(content)
        
        print(f"  {Colors.GREEN}✅ 2 ejemplos de código creados{Colors.END}")

    def create_wizards(self):
        """Crear wizards guiados"""
        print(f"\n{Colors.BLUE}🧙‍♂️ Creando wizards guiados...{Colors.END}")
        
        # Wizard de configuración de agentes
        agent_wizard = '''
"""
Wizard de Configuración de Agentes
==================================
Configuración paso a paso de agentes específicos
"""

import json
import asyncio
from pathlib import Path

def interactive_agent_setup():
    """
    Setup interactivo para configurar agentes
    """
    
    print("🧙‍♂️ Wizard de Configuración de Agentes MCP Server Superior")
    print("=" * 60)
    
    # Paso 1: Seleccionar agentes
    print("\\n1️⃣ ¿Qué agentes quieres configurar?")
    available_agents = {
        "1": {"name": "Git Operations", "description": "Automatización de Git y repositorios"},
        "2": {"name": "Web Scraping", "description": "Extracción de datos web"},
        "3": {"name": "Database Operations", "description": "Gestión de bases de datos"},
        "4": {"name": "File Processing", "description": "Procesamiento de archivos"},
        "5": {"name": "Search Engine", "description": "Búsquedas web automatizadas"}
    }
    
    for key, agent in available_agents.items():
        print(f"  {key}. {agent['name']}: {agent['description']}")
    
    selected = input("\\nSelecciona agentes (números separados por comas): ")
    selected_agents = [available_agents[num.strip()] for num in selected.split(",") if num.strip() in available_agents]
    
    # Paso 2: Configurar APIs
    print("\\n2️⃣ Configuración de APIs y credenciales")
    
    api_config = {}
    for agent in selected_agents:
        print(f"\\n🔑 Configurando {agent['name']}:")
        agent_name = agent['name'].lower().replace(" ", "_")
        
        if "git" in agent_name:
            github_token = input("GitHub Personal Access Token: ")
            gitlab_token = input("GitLab Personal Access Token (opcional): ")
            api_config["github_token"] = github_token
            if gitlab_token:
                api_config["gitlab_token"] = gitlab_token
                
        elif "web" in agent_name:
            proxy_list = input("Proxy list (opcional, separadas por comas): ")
            api_config["proxies"] = proxy_list.split(",") if proxy_list else []
            
        elif "database" in agent_name:
            db_url = input("Database connection string: ")
            api_config["database_url"] = db_url
    
    # Paso 3: Generar configuración
    print("\\n3️⃣ Generando configuración...")
    
    config = {
        "enabled_agents": [agent["name"].lower().replace(" ", "_") for agent in selected_agents],
        "api_keys": api_config,
        "settings": {
            "max_concurrent_operations": 5,
            "timeout_seconds": 30,
            "retry_attempts": 3
        }
    }
    
    # Guardar configuración
    with open("config/agents_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("✅ Configuración guardada en config/agents_config.json")
    print("\\n🎉 ¡Configuración completada!")
    
    return config

# Ejecutar wizard
if __name__ == "__main__":
    interactive_agent_setup()
        '''
        
        with open(self.templates_dir / "agent_wizard.py", "w") as f:
            f.write(agent_wizard)
        
        print(f"  {Colors.GREEN}✅ 1 wizard guiado creado{Colors.END}")

def list_available_templates():
    """Listar templates disponibles"""
    manager = TemplateManager()
    
    print(f"\n{Colors.BOLD}📚 TEMPLATES DISPONIBLES{Colors.END}")
    print("=" * 50)
    
    # Listar agentes
    agent_configs = (manager.templates_dir / "agent_configs").glob("*.json")
    if agent_configs:
        print(f"\n{Colors.CYAN}🤖 Configuraciones de Agentes:{Colors.END}")
        for config in agent_configs:
            print(f"  • {config.stem}")
    
    # Listar casos de uso
    use_cases = (manager.templates_dir / "use_cases").glob("*.json")
    if use_cases:
        print(f"\n{Colors.CYAN}📋 Casos de Uso:{Colors.END}")
        for case in use_cases:
            with open(case) as f:
                data = json.load(f)
                print(f"  • {data['title']} ({data['difficulty']})")
    
    # Listar ejemplos de código
    code_examples = (manager.templates_dir / "code_examples").glob("*.py")
    if code_examples:
        print(f"\n{Colors.CYAN}💻 Ejemplos de Código:{Colors.END}")
        for example in code_examples:
            print(f"  • {example.stem}")
    
    # Listar wizards
    wizards = list((manager.templates_dir).glob("*_wizard.py"))
    if wizards:
        print(f"\n{Colors.CYAN}🧙‍♂️ Wizards Guíados:{Colors.END}")
        for wizard in wizards:
            print(f"  • {wizard.stem}")

def create_templates():
    """Crear todos los templates"""
    print_banner()
    
    manager = TemplateManager()
    
    print(f"{Colors.PURPLE}🎨 Generando sistema completo de templates...{Colors.END}")
    
    # Crear todos los templates
    manager.create_agent_templates()
    manager.create_use_case_templates()
    manager.create_code_examples()
    manager.create_wizards()
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 SISTEMA DE TEMPLATES COMPLETADO!{Colors.END}")
    
    # Mostrar resumen
    list_available_templates()
    
    print(f"\n{Colors.CYAN}📖 CÓMO USAR:{Colors.END}")
    print(f"1. {Colors.WHITE}Ver templates:     {Colors.GREEN}python templates.py --list{Colors.END}")
    print(f"2. {Colors.WHITE}Aplicar template: {Colors.GREEN}python templates.py --apply git_operations{Colors.END}")
    print(f"3. {Colors.WHITE}Ejecutar wizard:  {Colors.GREEN}python templates/agent_wizard.py{Colors.END}")
    print(f"4. {Colors.WHITE}Ver ejemplos:     {Colors.GREEN}cd templates/code_examples && python ejemplo.py{Colors.END}")

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sistema de Templates y Casos de Uso")
    parser.add_argument("--create", action="store_true", help="Crear todos los templates")
    parser.add_argument("--list", action="store_true", help="Listar templates disponibles")
    
    args = parser.parse_args()
    
    if args.create:
        create_templates()
    elif args.list:
        list_available_templates()
    else:
        # Por defecto, crear templates
        create_templates()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())