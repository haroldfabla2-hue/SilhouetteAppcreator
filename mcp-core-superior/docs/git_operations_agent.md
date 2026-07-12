# Git Operations Agent MCP

Un agente completo para operaciones avanzadas de Git, integración con APIs de GitHub/GitLab, CI/CD, webhooks y testing automatizado.

## 🚀 Características Principales

### Operaciones Básicas de Git
- **Clone**: Clonar repositorios con opciones de depth, branch específica, y modo bare
- **Pull**: Obtener cambios del repositorio remoto con manejo de conflictos
- **Push**: Enviar cambios con opciones de force y branch específica
- **Status**: Obtener información completa del repositorio

### Gestión de Branches
- **Crear**: Crear nuevas branches desde cualquier branch existente
- **Eliminar**: Eliminar branches locales y remotas (con force si es necesario)
- **Cambiar**: Cambiar entre branches existentes
- **Listar**: Listar branches locales y remotas
- **Información**: Obtener detalles de branches (ahead/behind, tracking, etc.)

### Merge y Rebase
- **Merge**: Merge con estrategias múltiples (merge, rebase, squash, fast-forward)
- **Rebase**: Rebase interactivo y continuo
- **Conflictos**: Detección automática de conflictos durante merge/rebase
- **Abort**: Cancelar operaciones en progreso

### Resolución de Conflictos
- **Detección**: Detectar automáticamente archivos con conflictos
- **Análisis**: Análisis detallado de marcadores de conflicto
- **Resolución**: Resolución automática usando ours/theirs o contenido personalizado
- **Seguimiento**: Marcar conflictos como resueltos

### Análisis de Commits
- **Historial**: Obtener historial completo con filtros (fecha, autor, branch)
- **Detalles**: Información detallada de commits (archivos, líneas, padres)
- **Impacto**: Análisis de impacto de commits específicos
- **Búsqueda**: Búsqueda por mensaje, autor o archivos

### Visualización de Diffs
- **Diffs**: Generar diffs entre commits, branch o estado actual
- **Estadísticas**: Estadísticas de cambios (archivos, líneas, inserciones/eliminaciones)
- **Cambios no comprometidos**: Mostrar cambios en staging area y working directory

### Integración con APIs (GitHub/GitLab)
- **Pull Requests**: Crear y gestionar PRs en GitHub
- **Merge Requests**: Crear MRs en GitLab
- **Repositorios**: Obtener información de repositorios
- **Workflows**: Obtener información de CI/CD workflows
- **Rate Limiting**: Manejo inteligente de límites de API

### Integración CI/CD
- **Análisis**: Analizar configuración de workflows (.github/workflows/)
- **Workflows**: Obtener ejecuciones de workflows
- **Trigger**: Disparar pipelines manualmente
- **Monitor**: Monitorear estado de ejecuciones

### Manejo de Webhooks
- **Configuración**: Crear configuraciones de webhook para GitHub/GitLab
- **Handlers**: Generar handlers automáticos para webhooks
- **Eventos**: Manejo de eventos push, PR, workflow runs, issues

### Testing Automatizado
- **Configuración**: Configurar ambiente de testing (pytest, unittest, jest)
- **Ejecución**: Ejecutar tests con timeout y manejo de errores
- **Reportes**: Generar reportes en HTML y JSON
- **Cobertura**: Análisis de cobertura de código

### Múltiples Remotes
- **Agregar**: Agregar nuevos remotes con configuración automática
- **Eliminar**: Eliminar remotes existentes
- **Actualizar**: Cambiar URLs de remotes
- **Sincronizar**: Sincronización selectiva con remotes específicos

### Workflows Complejos
- **Feature Branches**: Workflow completo para desarrollo de features
- **Releases**: Workflow automatizado para releases con tags
- **Hotfixes**: Workflow para hotfixes críticos
- **Merges**: Workflow completo para merges con estrategias

### Análisis de Salud
- **Repositorio**: Análisis completo de la salud del repositorio
- **Estructura**: Verificación de estructura básica (README, .gitignore, etc.)
- **Optimización**: Recomendaciones de optimización y mejores prácticas
- **Métricas**: Estadísticas de tamaño, branches, commits recientes

## 📦 Instalación

### Dependencias Requeridas

```bash
pip install GitPython aiohttp pyyaml
```

### Variables de Entorno

```bash
export GITHUB_TOKEN="tu_token_de_github"
export GITLAB_TOKEN="tu_token_de_gitlab"
export BITBUCKET_USERNAME="tu_usuario"
export BITBUCKET_APP_PASSWORD="tu_app_password"
```

## 🔧 Uso Básico

### Clonar Repositorio

```python
from src.agents.git_operations_agent import GitOperationsAgent

async with GitOperationsAgent() as agent:
    resultado = agent.clone_repository(
        url="https://github.com/usuario/repo.git",
        path="./mi_repo",
        branch="main",
        depth=10
    )
    print(resultado)
```

### Gestionar Branches

```python
# Crear nueva branch
resultado = agent.create_branch(
    repo_path="./mi_repo",
    branch_name="feature/nueva-funcionalidad",
    from_branch="main"
)

# Cambiar a branch
resultado = agent.switch_branch(
    repo_path="./mi_repo",
    branch_name="feature/nueva-funcionalidad"
)
```

### Merge y Rebase

```python
# Merge con squash
resultado = agent.merge_branch(
    repo_path="./mi_repo",
    source_branch="feature/nueva-funcionalidad",
    strategy=MergeStrategy.SQUASH,
    no_ff=True,
    message="Merge feature: nueva-funcionalidad"
)
```

### Integración con GitHub

```python
# Crear Pull Request
resultado = await agent.create_pull_request_github(
    repo_owner="usuario",
    repo_name="repositorio", 
    title="Nueva funcionalidad",
    body="Descripción del PR",
    head="feature/nueva-funcionalidad",
    base="main"
)
```

## 🔍 APIs Disponibles

### Operaciones Básicas
- `clone_repository()`
- `pull_changes()`
- `push_changes()`
- `get_repository_info()`

### Gestión de Branches
- `create_branch()`
- `delete_branch()`
- `switch_branch()`
- `list_branches()`
- `get_branch_info()`

### Merge y Rebase
- `merge_branch()`
- `rebase_branch()`
- `abort_rebase()`
- `continue_rebase()`

### Conflictos
- `detect_conflicts()`
- `resolve_conflict()`
- `mark_conflict_resolved()`

### Commits y Análisis
- `get_commit_history()`
- `analyze_commit_impact()`
- `search_commits()`

### Diffs
- `get_diff()`
- `get_uncommitted_changes()`

### APIs Externas
- `create_pull_request_github()`
- `get_pull_requests_github()`
- `create_merge_request_gitlab()`
- `get_repository_info_github()`

### CI/CD
- `analyze_ci_cd_pipeline()`
- `get_workflow_runs_github()`
- `trigger_ci_cd_pipeline()`

### Webhooks
- `create_webhook_config()`
- `setup_webhook_handler()`

### Testing
- `setup_test_environment()`
- `run_tests()`
- `generate_test_report()`

### Múltiples Remotes
- `add_remote()`
- `remove_remote()`
- `update_remote()`
- `list_remotes()`
- `sync_with_remote()`

### Workflows Complejos
- `create_feature_branch_workflow()`
- `create_release_workflow()`
- `create_hotfix_workflow()`
- `create_merge_workflow()`

### Análisis
- `analyze_repository_health()`

## 📊 Estructura de Datos

### GitRepository
```python
@dataclass
class GitRepository:
    path: str
    url: str
    provider: GitProvider
    default_branch: str
    current_branch: str
    remotes: Dict[str, str]
    last_commit: Optional[str]
    commit_count: int
    status: Optional[str]
```

### CommitInfo
```python
@dataclass
class CommitInfo:
    hash: str
    message: str
    author: str
    email: str
    date: datetime
    files_changed: List[str]
    insertions: int
    deletions: int
    parent_hashes: List[str]
    branch: Optional[str]
```

### BranchInfo
```python
@dataclass
class BranchInfo:
    name: str
    is_local: bool
    is_remote: bool
    tracking_branch: Optional[str]
    ahead: int
    behind: int
    last_commit: Optional[str]
    merge_base: Optional[str]
```

## 🔧 Configuración Avanzada

### Workflow de Feature Branch Completo

```python
resultado = agent.create_feature_branch_workflow(
    repo_path="./mi_repo",
    feature_name="api-nueva",
    base_branch="develop"
)

# El workflow incluye:
# 1. Cambiar a branch base
# 2. Pull de cambios remotos
# 3. Crear nueva branch
# 4. Configurar tracking
# 5. Retornar instrucciones paso a paso
```

### Análisis de Salud del Repositorio

```python
resultado = agent.analyze_repository_health("./mi_repo")

# Incluye análisis de:
# - Estructura básica (README, .gitignore)
# - Estado de working directory
# - Número de branches
# - Commits recientes
# - Tamaño del repositorio
# - Configuración de remotes
# - Presencia de CI/CD
```

## 🚨 Manejo de Errores

El agente maneja automáticamente:
- **Timeouts**: Comandos Git con timeout de 300 segundos
- **Rate Limiting**: Verificación de límites de API
- **Conflictos**: Detección y resolución de conflictos
- **Permisos**: Manejo de errores de permisos
- **Repositorios**: Validación de repositorios Git válidos

## 🔒 Seguridad

- **Tokens**: Uso seguro de tokens de API
- **Comandos**: Validación de comandos Git
- **Rate Limiting**: Protección contra abuso de APIs
- **Error Handling**: Manejo seguro de errores sin exposición de datos sensibles

## 📈 Métricas y Monitoreo

El agente proporciona métricas sobre:
- **Comandos Git**: Tiempo de ejecución, éxito/fallo
- **API Calls**: Número de llamadas, rate limits
- **Conflicts**: Detección y resolución de conflictos
- **Test Results**: Resultados de testing automatizado
- **Repository Health**: Score de salud del repositorio

## 🤝 Contribución

Este agente está diseñado para ser extensible. Se pueden agregar nuevas funcionalidades mediante:

1. Nuevos métodos en la clase `GitOperationsAgent`
2. Nuevas integraciones con APIs externas
3. Estrategias adicionales de merge/rebase
4. Nuevos tipos de workflows

## 📝 Notas Importantes

- El agente requiere Python 3.7+
- Algunos ejemplos requieren tokens de API reales
- Las operaciones que involucran APIs externas tienen rate limiting
- Los workflows complejos incluyen validaciones y rollback automático
- Se recomienda usar virtual environments para aislar dependencias

## 🆘 Soporte

Para reportar problemas o solicitar nuevas funcionalidades:
1. Revisa la documentación existente
2. Verifica que los tokens de API estén correctamente configurados
3. Ejecuta los ejemplos para validar funcionalidad básica
4. Contacta al equipo de desarrollo para issues específicos