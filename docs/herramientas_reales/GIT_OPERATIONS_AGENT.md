# 🚀 Git Operations Agent - Guía Completa

## Descripción General

El **Git Operations Agent** es un agente especializado que proporciona capacidades completas de gestión de repositorios Git, integración con GitHub/GitLab APIs, automatización de CI/CD, y gestión de conflictos. Es una herramienta **real** que interactúa directamente con servicios Git y APIs de plataformas de desarrollo.

**Estado**: ✅ **PRODUCCIÓN ACTIVA**  
**Compatibilidad**: Git CLI, GitHub API, GitLab API  
**Versiones**: Git 2.0+, GitHub REST/GraphQL, GitLab REST API  

## 🎯 Capacidades Principales

### Operaciones Git Core
- **Clone, Branch, Commit, Push, Pull**: Operaciones completas de Git
- **Merge, Rebase, Cherry-pick**: Gestión avanzada de branches
- **Conflict Resolution**: Resolución automática y asistida de conflictos
- **Stash Management**: Guardado temporal de cambios

### Integración GitHub/GitLab
- **Repository Management**: Crear, clonar, eliminar repositorios
- **Pull Requests**: Crear, revisar, merge automático
- **Issues & Milestones**: Gestión completa de tickets
- **Releases & Tags**: Gestión de versiones y releases
- **Webhooks**: Configuración automática de eventos

### Automatización CI/CD
- **Pipeline Management**: Configuración automática de pipelines
- **Deployment Scripts**: Scripts de deployment automatizado
- **Environment Management**: Staging, production environments
- **Rollback Strategies**: Estrategias de rollback automático

## 🛠️ Instalación y Configuración

### Prerrequisitos

```bash
# Instalar Git (si no está instalado)
sudo apt-get install git  # Ubuntu/Debian
brew install git          # macOS
choco install git         # Windows

# Verificar instalación
git --version
# Debe mostrar: git version 2.x.x o superior
```

### Configuración de Credenciales

#### GitHub Integration

```bash
# Configurar token GitHub
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export GITHUB_USERNAME=tu-usuario-github
export GITHUB_REPO=mi-empresa/mi-repo

# Verificar configuración
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

#### GitLab Integration

```bash
# Configurar token GitLab
export GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx
export GITLAB_USERNAME=tu-usuario-gitlab
export GITLAB_PROJECT_ID=12345678

# Verificar configuración
curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" "https://gitlab.com/api/v4/projects/$GITLAB_PROJECT_ID"
```

#### Git SSH Keys (Opcional)

```bash
# Generar SSH key
ssh-keygen -t ed25519 -C "tu-email@empresa.com"

# Agregar a GitHub/GitLab
cat ~/.ssh/id_ed25519.pub
# Copiar y pegar en GitHub/GitLab SSH keys settings
```

## 📚 API Reference

### Operaciones Básicas de Git

#### 1. Clonar Repositorio

```http
POST /api/v1/tools/git
Content-Type: application/json

{
    "agent": "git_operations",
    "action": "clone_repository",
    "repo_url": "https://github.com/usuario/mi-repo.git",
    "target_path": "/tmp/mi-repo",
    "branch": "main",
    "depth": 1,
    "ssh_key": "path/to/ssh/key" // opcional
}
```

**Respuesta:**
```json
{
    "status": "success",
    "data": {
        "repository_path": "/tmp/mi-repo",
        "branch": "main",
        "commit": "abc123",
        "cloned_at": "2025-11-04T15:30:00Z"
    }
}
```

#### 2. Crear Branch

```http
POST /api/v1/tools/git
Content-Type: application/json

{
    "agent": "git_operations",
    "action": "create_branch",
    "repo_path": "/tmp/mi-repo",
    "branch_name": "feature/nueva-funcionalidad",
    "from_branch": "main",
    "checkout": true
}
```

#### 3. Commit y Push

```http
POST /api/v1/tools/git
Content-Type: application/json

{
    "agent": "git_operations",
    "action": "commit_and_push",
    "repo_path": "/tmp/mi-repo",
    "files": [
        {
            "path": "src/nueva_funcionalidad.py",
            "content": "def nueva_funcionalidad():\n    print('¡Hola mundo!')"
        },
        {
            "path": "README.md",
            "content": "# Mi Proyecto\\nNueva funcionalidad agregada"
        }
    ],
    "commit_message": "feat: add nueva funcionalidad",
    "push": true,
    "remote": "origin",
    "branch": "main"
}
```

### Operaciones GitHub API

#### 4. Crear Repositorio

```http
POST /api/v1/tools/git
Content-Type: application/json

{
    "agent": "git_operations",
    "action": "create_github_repository",
    "repo_name": "mi-nuevo-repo",
    "description": "Mi proyecto increíble",
    "private": false,
    "auto_init": true,
    "gitignore": "Python",
    "license": "MIT"
}
```

#### 5. Crear Pull Request

```http
POST /api/v1/tools/git
Content-Type: application/json

{
    "agent": "git_operations",
    "action": "create_pull_request",
    "repo": "mi-usuario/mi-repo",
    "base_branch": "main",
    "head_branch": "feature/nueva-funcionalidad",
    "title": "feat: agregar nueva funcionalidad",
    "body": "Implementación completa con tests y documentación",
    "reviewers": ["tech-lead", "senior-dev"],
    "labels": ["feature", "ready-for-review"],
    "auto_merge": true,
    "merge_method": "squash"
}
```

#### 6. Gestión de Issues

```http
POST /api/v1/tools/git
Content-Type: application/json

{
    "agent": "git_operations",
    "action": "create_github_issue",
    "repo": "mi-usuario/mi-repo",
    "title": "Bug en función de login",
    "body": "Descripción detallada del bug:\\n\\n1. Pasos para reproducir\\n2. Comportamiento esperado\\n3. Comportamiento actual",
    "labels": ["bug", "high-priority"],
    "assignees": ["developer1"],
    "milestone": "v1.0.0"
}
```

### Operaciones Avanzadas

#### 7. Resolver Conflictos

```http
POST /api/v1/tools/git
Content-Type: application/json

{
    "agent": "git_operations",
    "action": "resolve_merge_conflicts",
    "repo_path": "/tmp/mi-repo",
    "strategy": "ours", // ours, theirs, manual
    "conflict_files": ["src/app.py", "config.py"],
    "manual_resolutions": {
        "src/app.py": "console.log('Resolución manual')"
    },
    "commit_resolutions": true
}
```

#### 8. Automatización CI/CD

```http
POST /api/v1/tools/git
Content-Type: application/json

{
    "agent": "git_operations",
    "action": "setup_cicd_pipeline",
    "repo": "mi-usuario/mi-repo",
    "platform": "github_actions", // github_actions, gitlab_ci, jenkins
    "pipeline_config": {
        "python_version": "3.9",
        "tests": true,
        "deploy_staging": true,
        "deploy_production": true,
        "run_on": ["push", "pull_request"]
    }
}
```

## 💻 Ejemplos de Uso

### Ejemplo 1: Workflow Completo de Feature

```python
import requests
import json

# Configuración
base_url = "http://localhost:8000/api/v1/tools/git"
github_token = "tu-token-github"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {github_token}"
}

# Paso 1: Crear feature branch
step1 = requests.post(base_url, headers=headers, json={
    "agent": "git_operations",
    "action": "create_feature_branch",
    "repo_url": "https://github.com/mi-empresa/mi-proyecto",
    "base_branch": "main",
    "feature_branch": "feature/ai-integration",
    "checkout": True
})

print("Branch creada:", step1.json())

# Paso 2: Agregar archivos
step2 = requests.post(base_url, headers=headers, json={
    "agent": "git_operations", 
    "action": "add_files",
    "repo_path": "/tmp/mi-proyecto",
    "files": [
        {
            "path": "src/ai_service.py",
            "content": "class AIService:\\n    def __init__(self):\\n        self.model = load_model()\\n    \\n    def predict(self, data):\\n        return self.model.predict(data)"
        },
        {
            "path": "tests/test_ai_service.py", 
            "content": "import unittest\\nfrom src.ai_service import AIService\\n\\nclass TestAIService(unittest.TestCase):\\n    def test_predict(self):\\n        service = AIService()\\n        result = service.predict([1, 2, 3])\\n        self.assertIsNotNone(result)"
        }
    ]
})

print("Archivos agregados:", step2.json())

# Paso 3: Crear PR
step3 = requests.post(base_url, headers=headers, json={
    "agent": "git_operations",
    "action": "create_pull_request",
    "repo": "mi-empresa/mi-proyecto",
    "base_branch": "main", 
    "head_branch": "feature/ai-integration",
    "title": "feat: integrate AI service",
    "body": "Implementation of AI service with full test coverage",
    "reviewers": ["tech-lead"],
    "labels": ["feature", "ai"],
    "auto_merge": False
})

print("PR creado:", step3.json())
```

### Ejemplo 2: Gestión de Releases

```python
# Crear release con tags
release_workflow = requests.post(base_url, headers=headers, json={
    "agent": "git_operations",
    "action": "create_release",
    "repo": "mi-empresa/mi-proyecto",
    "tag_name": "v1.2.0",
    "release_name": "Release 1.2.0 - AI Features",
    "body": "## Cambios en esta versión\\n\\n### Nuevas características\\n- AI service integration\\n- Machine learning models\\n- Advanced analytics\\n\\n### Bug fixes\\n- Fixed memory leak\\n- Improved performance",
    "draft": False,
    "prerelease": False,
    "generate_release_notes": True
})
```

### Ejemplo 3: Sincronización de Múltiples Repos

```python
# Sincronizar repositorios
sync_repos = requests.post(base_url, headers=headers, json={
    "agent": "git_operations",
    "action": "sync_multiple_repos",
    "repositories": [
        {
            "url": "https://github.com/empresa/frontend-app",
            "sync_strategy": "merge_upstream"
        },
        {
            "url": "https://github.com/empresa/backend-api", 
            "sync_strategy": "rebase_ours"
        },
        {
            "url": "https://gitlab.com/empresa/mobile-app",
            "sync_strategy": "cherry_pick"
        }
    ],
    "create_prs": True,
    "auto_merge": False
})
```

## 🔧 Configuración Avanzada

### Variables de Entorno

```bash
# Configuración Git Global
export GIT_AUTHOR_NAME="Tu Nombre"
export GIT_AUTHOR_EMAIL="tu@empresa.com"
export GIT_COMMITTER_NAME="Tu Nombre"  
export GIT_COMMITTER_EMAIL="tu@empresa.com"

# Configuración GitHub
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export GITHUB_ORG="mi-empresa"
export GITHUB_DEFAULT_REPO="mi-proyecto"

# Configuración GitLab
export GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"
export GITLAB_GROUP="mi-grupo"
export GITLAB_DEFAULT_PROJECT="mi-proyecto"

# Configuración SSH
export GIT_SSH_COMMAND="ssh -i /path/to/ssh/key -o StrictHostKeyChecking=no"

# Configuración de timeouts
export GIT_OPERATION_TIMEOUT=300
export GITHUB_API_TIMEOUT=120
```

### Configuración de Hooks

```yaml
# hooks/pre-commit.yaml
hooks:
  - name: run_tests
    command: "pytest tests/"
  - name: lint_code
    command: "flake8 src/"
  - name: check_format
    command: "black --check src/"
  - name: security_scan
    command: "bandit -r src/"

# hooks/post-commit.yaml  
hooks:
  - name: notify_slack
    command: "./scripts/notify_slack.sh"
  - name: update_changelog
    command: "./scripts/update_changelog.sh"
```

### Configuración de Branch Protection

```json
{
  "protection_rules": {
    "main": {
      "required_status_checks": {
        "strict": true,
        "contexts": ["continuous-integration", "tests", "lint"]
      },
      "enforce_admins": true,
      "required_pull_request_reviews": {
        "required_approving_review_count": 2,
        "dismiss_stale_reviews": true
      },
      "restrictions": {
        "users": ["tech-lead", "senior-dev"],
        "teams": ["core-team"]
      }
    }
  }
}
```

## 📊 Monitoreo y Métricas

### Métricas de Performance

```python
# Métricas disponibles
metrics = {
    "clone_time": "time to clone repository",
    "push_throughput": "files per second", 
    "api_calls": "GitHub/GitLab API usage",
    "conflict_rate": "percentage of conflicts",
    "pr_merge_time": "time to merge PRs",
    "deployment_frequency": "deploys per day"
}
```

### Dashboard Grafana

Las métricas del Git Operations Agent están disponibles en Grafana:
- **Performance**: Tiempo de operaciones por tipo
- **Success Rates**: Tasas de éxito por operación
- **API Usage**: Uso de APIs GitHub/GitLab
- **Error Analysis**: Análisis de errores comunes

## 🚨 Troubleshooting

### Problemas Comunes

#### Error: Repository not found

```bash
# Verificar credenciales
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user

# Verificar permisos
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/repos/usuario/repo
```

#### Error: Permission denied

```bash
# Verificar SSH keys
ssh -T git@github.com
ssh -T git@gitlab.com

# Agregar SSH key si es necesario
ssh-add ~/.ssh/id_rsa
```

#### Error: Merge conflicts

```python
# Resolución automática de conflictos
conflict_resolution = requests.post(base_url, headers=headers, json={
    "agent": "git_operations",
    "action": "auto_resolve_conflicts", 
    "repo_path": "/tmp/repo",
    "strategy": "ours",
    "prefer_ours_on": ["*.py", "*.js"],
    "prefer_theirs_on": ["*.json", "*.yml"]
})
```

### Logs y Debugging

```bash
# Ver logs del agente
docker-compose logs git-operations-agent

# Debug mode
export GIT_VERBOSE=true
export DEBUG_GIT_OPS=true

# Testing
curl -X POST http://localhost:8000/api/v1/tools/git \
  -H "Content-Type: application/json" \
  -d '{"agent": "git_operations", "action": "test_connection"}'
```

## 🔒 Seguridad

### Mejores Prácticas

1. **Tokens**: Usar tokens con permisos mínimos
2. **SSH Keys**: Configurar SSH keys en lugar de HTTPS cuando sea posible
3. **Webhooks**: Verificar signatures de webhooks
4. **Branch Protection**: Proteger branches principales
5. **Audit**: Habilitar audit logs en GitHub/GitLab

### Configuración de Seguridad

```json
{
  "security_config": {
    "require_2fa": true,
    "allowed_users": ["@empresa/team-dev"],
    "blocked_keywords": ["password", "secret", "key"],
    "max_file_size": "10MB",
    "scan_for_secrets": true
  }
}
```

## 📈 Optimización

### Performance Tips

1. **Shallow Clone**: Usar `--depth 1` para clones rápidos
2. **Sparse Checkout**: Solo checkout de archivos necesarios
3. **LFS**: Usar Git LFS para archivos grandes
4. **Caching**: Cache de credenciales y configuraciones
5. **Batch Operations**: Operaciones en lote cuando sea posible

### Configuración de Optimización

```bash
# Configuración Git performance
git config --global core.preloadindex true
git config --global core.fscache true
git config --global gc.auto 256

# Cache de credenciales
git config --global credential.helper cache
git config --global credential.helper 'cache --timeout=3600'
```

## 🎯 Casos de Uso Empresariales

### 1. Automatización de CI/CD

```python
# Pipeline completo automatizado
pipeline = {
    "trigger": "push_to_feature_branch",
    "steps": [
        "run_unit_tests",
        "run_integration_tests", 
        "security_scan",
        "create_docker_image",
        "deploy_to_staging",
        "run_smoke_tests",
        "create_pr_with_changelog"
    ],
    "on_success": "merge_to_main",
    "on_failure": "notify_team"
}
```

### 2. Gestión de Releases

```python
# Proceso de release automatizado
release_process = {
    "trigger": "tag_v*.*.*",
    "steps": [
        "run_full_test_suite",
        "update_version_files",
        "generate_changelog",
        "create_github_release",
        "build_docker_images", 
        "deploy_to_production",
        "send_notification"
    ]
}
```

### 3. Compliance y Audit

```python
# Proceso de compliance
compliance_check = {
    "checks": [
        "license_compliance",
        "security_scan", 
        "code_quality",
        "documentation_check"
    ],
    "reporting": {
        "generate_report": True,
        "send_to_compliance": True,
        "block_on_violations": False
    }
}
```

---

## 📞 Soporte

**Documentación API**: http://localhost:8000/docs#/Git%20Operations  
**Issues**: GitHub Issues en el repositorio del proyecto  
**Logs**: http://localhost:8000/logs/git-operations  
**Métricas**: http://localhost:3001 (Grafana dashboard)

---

**🚀 Estado**: **HERRAMIENTA REAL OPERATIVA**  
**📅 Última Actualización**: 2025-11-04  
**✅ Producción**: **READY FOR ENTERPRISE USE**
