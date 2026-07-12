"""
Ejemplo de uso del Git Operations Agent MCP

Este archivo demuestra cómo usar el Git Operations Agent para realizar
operaciones avanzadas de Git, integración con APIs, y workflows complejos.
"""

import asyncio
import os
from typing import Dict, Any

# Importar el agente
from src.agents.git_operations_agent import (
    GitOperationsAgent,
    GitProvider,
    MergeStrategy,
    ConflictResolution
)

async def ejemplo_operaciones_basicas():
    """Ejemplo de operaciones básicas de Git"""
    print("=== Operaciones Básicas de Git ===")
    
    async with GitOperationsAgent() as agent:
        # Clonar repositorio
        resultado = agent.clone_repository(
            url="https://github.com/ejemplo/repo.git",
            path="./test_repo",
            branch="main"
        )
        print(f"Clonar: {resultado}")
        
        # Obtener información del repositorio
        resultado = agent.get_repository_info("./test_repo")
        print(f"Info repositorio: {resultado}")
        
        # Listar branches
        resultado = agent.list_branches("./test_repo")
        print(f"Branches: {resultado}")

async def ejemplo_gestion_branches():
    """Ejemplo de gestión de branches"""
    print("\n=== Gestión de Branches ===")
    
    async with GitOperationsAgent() as agent:
        # Crear nueva branch
        resultado = agent.create_branch(
            repo_path="./test_repo",
            branch_name="feature/nueva-funcionalidad",
            from_branch="main"
        )
        print(f"Crear branch: {resultado}")
        
        # Cambiar a nueva branch
        resultado = agent.switch_branch(
            repo_path="./test_repo",
            branch_name="feature/nueva-funcionalidad"
        )
        print(f"Cambiar branch: {resultado}")

async def ejemplo_merge_rebase():
    """Ejemplo de operaciones merge y rebase"""
    print("\n=== Merge y Rebase ===")
    
    async with GitOperationsAgent() as agent:
        # Merge con estrategia específica
        resultado = agent.merge_branch(
            repo_path="./test_repo",
            source_branch="feature/nueva-funcionalidad",
            strategy=MergeStrategy.SQUASH,
            no_ff=True,
            message="Merge feature: nueva-funcionalidad"
        )
        print(f"Merge: {resultado}")
        
        # Rebase
        resultado = agent.rebase_branch(
            repo_path="./test_repo",
            source_branch="feature/desarrollo",
            onto_branch="main"
        )
        print(f"Rebase: {resultado}")

async def ejemplo_resolucion_conflictos():
    """Ejemplo de resolución de conflictos"""
    print("\n=== Resolución de Conflictos ===")
    
    async with GitOperationsAgent() as agent:
        # Detectar conflictos
        resultado = agent.detect_conflicts("./test_repo")
        print(f"Detectar conflictos: {resultado}")
        
        if resultado['success'] and resultado['conflicts']:
            conflicto = resultado['conflicts'][0]
            archivo = conflicto['file']
            
            # Resolver conflicto usando versión "their"
            resultado = agent.resolve_conflict(
                repo_path="./test_repo",
                file_path=archivo,
                resolution=ConflictResolution.THEIRS
            )
            print(f"Resolver conflicto: {resultado}")
            
            # Marcar como resuelto
            resultado = agent.mark_conflict_resolved(
                repo_path="./test_repo",
                file_path=archivo
            )
            print(f"Marcar resuelto: {resultado}")

async def ejemplo_analisis_commits():
    """Ejemplo de análisis de commits"""
    print("\n=== Análisis de Commits ===")
    
    async with GitOperationsAgent() as agent:
        # Historial de commits
        resultado = agent.get_commit_history(
            repo_path="./test_repo",
            since="2024-01-01",
            author="desarrollador"
        )
        print(f"Historial commits: {resultado}")
        
        # Buscar commits específicos
        resultado = agent.search_commits(
            repo_path="./test_repo",
            search_term="bug fix",
            search_type="message"
        )
        print(f"Buscar commits: {resultado}")
        
        # Analizar impacto de commit específico
        commit_hash = "abc123"
        resultado = agent.analyze_commit_impact(
            repo_path="./test_repo",
            commit_hash=commit_hash
        )
        print(f"Impacto commit: {resultado}")

async def ejemplo_visualizacion_diffs():
    """Ejemplo de visualización de diffs"""
    print("\n=== Visualización de Diffs ===")
    
    async with GitOperationsAgent() as agent:
        # Obtener diff entre commits
        resultado = agent.get_diff(
            repo_path="./test_repo",
            from_commit="HEAD~1",
            to_commit="HEAD"
        )
        print(f"Diff commits: {resultado}")
        
        # Cambios no comprometidos
        resultado = agent.get_uncommitted_changes("./test_repo")
        print(f"Cambios sin commit: {resultado}")

async def ejemplo_integracion_github():
    """Ejemplo de integración con GitHub API"""
    print("\n=== Integración con GitHub ===")
    
    # Configurar token de GitHub (usar variable de entorno)
    os.environ['GITHUB_TOKEN'] = 'tu_token_aqui'
    
    async with GitOperationsAgent() as agent:
        # Crear Pull Request
        resultado = await agent.create_pull_request_github(
            repo_owner="usuario",
            repo_name="repositorio",
            title="Nueva funcionalidad",
            body="Descripción del PR",
            head="feature/nueva-funcionalidad",
            base="main"
        )
        print(f"Crear PR: {resultado}")
        
        # Obtener Pull Requests
        resultado = await agent.get_pull_requests_github(
            repo_owner="usuario",
            repo_name="repositorio",
            state="open"
        )
        print(f"PRs abiertos: {resultado}")
        
        # Información del repositorio
        resultado = await agent.get_repository_info_github(
            repo_owner="usuario",
            repo_name="repositorio"
        )
        print(f"Info repo GitHub: {resultado}")

async def ejemplo_integracion_gitlab():
    """Ejemplo de integración con GitLab API"""
    print("\n=== Integración con GitLab ===")
    
    # Configurar token de GitLab
    os.environ['GITLAB_TOKEN'] = 'tu_token_gitlab'
    
    async with GitOperationsAgent() as agent:
        # Crear Merge Request
        resultado = await agent.create_merge_request_gitlab(
            project_id="123456",
            title="Nueva funcionalidad",
            description="Descripción del MR",
            source_branch="feature/nueva-funcionalidad",
            target_branch="main"
        )
        print(f"Crear MR: {resultado}")

async def ejemplo_ci_cd():
    """Ejemplo de integración CI/CD"""
    print("\n=== Integración CI/CD ===")
    
    async with GitOperationsAgent() as agent:
        # Analizar pipeline CI/CD
        resultado = agent.analyze_ci_cd_pipeline("./test_repo")
        print(f"Análisis CI/CD: {resultado}")
        
        # Obtener workflow runs de GitHub
        resultado = await agent.get_workflow_runs_github(
            repo_owner="usuario",
            repo_name="repositorio"
        )
        print(f"Workflow runs: {resultado}")
        
        # Disparar pipeline manualmente
        resultado = agent.trigger_ci_cd_pipeline(
            repo_path="./test_repo",
            workflow_name="ci-pipeline.yml",
            ref="main"
        )
        print(f"Disparar pipeline: {resultado}")

async def ejemplo_webhooks():
    """Ejemplo de manejo de webhooks"""
    print("\n=== Manejo de Webhooks ===")
    
    async with GitOperationsAgent() as agent:
        # Crear configuración de webhook
        resultado = agent.create_webhook_config(
            provider=GitProvider.GITHUB,
            repo_url="https://github.com/usuario/repo.git",
            secret="mi_secreto_webhook"
        )
        print(f"Config webhook: {resultado}")
        
        # Configurar handler de webhook
        resultado = agent.setup_webhook_handler(
            repo_path="./test_repo",
            webhook_config={
                'events': ['push', 'pull_request'],
                'secret': 'mi_secreto'
            }
        )
        print(f"Setup handler: {resultado}")

async def ejemplo_testing():
    """Ejemplo de testing automatizado"""
    print("\n=== Testing Automatizado ===")
    
    async with GitOperationsAgent() as agent:
        # Configurar ambiente de testing
        resultado = agent.setup_test_environment(
            repo_path="./test_repo",
            test_framework="pytest"
        )
        print(f"Setup testing: {resultado}")
        
        # Ejecutar tests
        resultado = agent.run_tests(
            repo_path="./test_repo",
            test_command="python -m pytest tests/ -v"
        )
        print(f"Ejecutar tests: {resultado}")
        
        # Generar reporte de tests
        resultado = agent.generate_test_report(
            repo_path="./test_repo",
            output_format="html"
        )
        print(f"Reporte tests: {resultado}")

async def ejemplo_multiples_remotes():
    """Ejemplo de manejo de múltiples remotes"""
    print("\n=== Múltiples Remotes ===")
    
    async with GitOperationsAgent() as agent:
        # Listar remotes
        resultado = agent.list_remotes("./test_repo")
        print(f"Listar remotes: {resultado}")
        
        # Agregar nuevo remote
        resultado = agent.add_remote(
            repo_path="./test_repo",
            name="backup",
            url="https://github.com/usuario/backup.git"
        )
        print(f"Agregar remote: {resultado}")
        
        # Sincronizar con remote específico
        resultado = agent.sync_with_remote(
            repo_path="./test_repo",
            remote_name="backup",
            direction="pull"
        )
        print(f"Sincronizar remote: {resultado}")

async def ejemplo_workflows_complejos():
    """Ejemplo de workflows complejos"""
    print("\n=== Workflows Complejos ===")
    
    async with GitOperationsAgent() as agent:
        # Workflow de feature branch
        resultado = agent.create_feature_branch_workflow(
            repo_path="./test_repo",
            feature_name="nueva-api",
            base_branch="develop"
        )
        print(f"Workflow feature: {resultado}")
        
        # Workflow de release
        resultado = agent.create_release_workflow(
            repo_path="./test_repo",
            version="1.2.0",
            release_notes="Nuevo release con mejoras"
        )
        print(f"Workflow release: {resultado}")
        
        # Workflow de hotfix
        resultado = agent.create_hotfix_workflow(
            repo_path="./test_repo",
            fix_description="Corregir bug crítico en login",
            production_branch="main"
        )
        print(f"Workflow hotfix: {resultado}")
        
        # Workflow de merge completo
        resultado = agent.create_merge_workflow(
            repo_path="./test_repo",
            source_branch="feature/nueva-funcionalidad",
            target_branch="main",
            merge_strategy=MergeStrategy.SQUASH
        )
        print(f"Workflow merge: {resultado}")

async def ejemplo_analisis_salud():
    """Ejemplo de análisis de salud del repositorio"""
    print("\n=== Análisis de Salud del Repositorio ===")
    
    async with GitOperationsAgent() as agent:
        resultado = agent.analyze_repository_health("./test_repo")
        print(f"Análisis de salud: {resultado}")

async def main():
    """Función principal para ejecutar todos los ejemplos"""
    print("Git Operations Agent - Ejemplos de Uso")
    print("=====================================")
    
    # Nota: Algunos ejemplos requieren configuración de tokens
    # y repositorios reales para funcionar completamente
    
    try:
        await ejemplo_operaciones_basicas()
        await ejemplo_gestion_branches()
        await ejemplo_merge_rebase()
        await ejemplo_resolucion_conflictos()
        await ejemplo_analisis_commits()
        await ejemplo_visualizacion_diffs()
        await ejemplo_ci_cd()
        await ejemplo_webhooks()
        await ejemplo_testing()
        await ejemplo_multiples_remotes()
        await ejemplo_workflows_complejos()
        await ejemplo_analisis_salud()
        
        print("\n=== Ejemplos Completados ===")
        
    except Exception as e:
        print(f"Error ejecutando ejemplos: {e}")

if __name__ == "__main__":
    # Ejecutar ejemplos
    asyncio.run(main())