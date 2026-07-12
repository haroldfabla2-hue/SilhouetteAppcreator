"""
Git Operations Agent MCP - Agente completo para operaciones avanzadas de Git

Este agente proporciona capacidades avanzadas de gestión de repositorios Git,
incluyendo operaciones básicas, gestión de branches, resolución de conflictos,
integración con GitHub/GitLab APIs, CI/CD, webhooks y workflows complejos.
"""

import os
import json
import asyncio
import subprocess
import tempfile
import shutil
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import yaml
import logging
from git import Repo, GitCommandError, InvalidGitRepositoryError, NoSuchPathError
from git.exc import GitError

# Imports del sistema MCP
try:
    from agents.base_agent_wrapper import BaseAgentWrapper, AgentCapability
    from core.exceptions import AgentException, handle_exceptions
    BASE_WRAPPER_AVAILABLE = True
except ImportError:
    try:
        from .base_agent_wrapper import BaseAgentWrapper, AgentCapability
        from ..core.exceptions import AgentException, handle_exceptions
        BASE_WRAPPER_AVAILABLE = True
    except ImportError:
        # Fallback cuando el sistema base no está disponible
        from enum import Enum
        
        class AgentCapability(Enum):
            TOOL_INVOCATION = "tool_invocation"
            CONCURRENT_EXECUTION = "concurrent_execution"
        
        class BaseAgentWrapper:
            def __init__(self, **kwargs):
                self.agent_name = kwargs.get('agent_name', 'git_operations')
                self.status = 'ready'
                self.capabilities = kwargs.get('capabilities', [])
            
            async def execute_operation(self, *args, **kwargs):
                return {"success": False, "error": "Sistema base no disponible"}
            
            async def ensure_initialized(self):
                pass
            
            async def health_check(self):
                return {"status": "unavailable", "reason": "Base system not loaded"}
        
        class AgentException(Exception):
            def __init__(self, message, agent_name=None, operation=None):
                super().__init__(message)
                self.message = message
                self.agent_name = agent_name
                self.operation = operation
        
        def handle_exceptions(func):
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    raise AgentException(str(e), "git_operations", func.__name__)
            return wrapper

# Importar configuración de agentes
try:
    from .config import get_safe_settings, AgentType, AgentConfig, agent_config_manager
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    
    # Fallback de configuración
    def get_safe_settings():
        return type('Settings', (), {
            'max_concurrent_tools': 3,
            'agent_timeout_seconds': 120,
            'agent_retry_attempts': 2,
            'agent_retry_delay': 1.0
        })()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitProvider(Enum):
    """Tipos de proveedores de Git soportados"""
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    GENERIC = "generic"


class MergeStrategy(Enum):
    """Estrategias de merge disponibles"""
    MERGE = "merge"
    REBASE = "rebase"
    SQUASH = "squash"
    FAST_FORWARD = "ff-only"


class ConflictResolution(Enum):
    """Tipos de resolución de conflictos"""
    THEIRS = "theirs"
    OURS = "ours"
    MANUAL = "manual"


@dataclass
class GitRepository:
    """Estructura para información de repositorio"""
    path: str
    url: str
    provider: GitProvider
    default_branch: str
    current_branch: str
    remotes: Dict[str, str]
    last_commit: Optional[str] = None
    commit_count: int = 0
    status: Optional[str] = None


@dataclass
class CommitInfo:
    """Información detallada de un commit"""
    hash: str
    message: str
    author: str
    email: str
    date: datetime
    files_changed: List[str]
    insertions: int = 0
    deletions: int = 0
    parent_hashes: List[str] = None
    branch: Optional[str] = None


@dataclass
class BranchInfo:
    """Información de una branch"""
    name: str
    is_local: bool
    is_remote: bool
    tracking_branch: Optional[str] = None
    ahead: int = 0
    behind: int = 0
    last_commit: Optional[str] = None
    merge_base: Optional[str] = None


@dataclass
class ConflictInfo:
    """Información de conflictos"""
    file: str
    status: str
    our_version: str
    their_version: str
    base_version: str
    conflict_type: str


@dataclass
class PullRequest:
    """Información de Pull Request"""
    id: str
    title: str
    source_branch: str
    target_branch: str
    author: str
    state: str
    url: str
    description: str
    created_at: datetime
    updated_at: datetime
    commits: List[CommitInfo]
    reviewers: List[str]
    labels: List[str]
    conflicts: List[ConflictInfo] = None


@dataclass
class WorkflowRun:
    """Información de workflow de CI/CD"""
    id: str
    workflow_name: str
    status: str
    conclusion: str
    branch: str
    commit: str
    url: str
    start_time: datetime
    end_time: Optional[datetime]
    duration: Optional[int]
    jobs: List[Dict[str, Any]]


class GitOperationsAgent:
    """Agente principal para operaciones avanzadas de Git"""
    
    def __init__(self):
        self.session = None
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.gitlab_token = os.getenv('GITLAB_TOKEN')
        self.bitbucket_username = os.getenv('BITBUCKET_USERNAME')
        self.bitbucket_app_password = os.getenv('BITBUCKET_APP_PASSWORD')
        
        # Rate limiting para APIs
        self.api_calls = {}
        self.rate_limits = {
            'github': {'requests_per_hour': 5000, 'current': 0},
            'gitlab': {'requests_per_hour': 3600, 'current': 0},
            'bitbucket': {'requests_per_hour': 1000, 'current': 0}
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _check_rate_limit(self, provider: str) -> bool:
        """Verificar límites de tasa para APIs"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        # Limpiar llamadas antiguas
        if provider in self.api_calls:
            self.api_calls[provider] = [
                call_time for call_time in self.api_calls[provider]
                if call_time > hour_ago
            ]
        
        # Verificar límite
        return len(self.api_calls.get(provider, [])) < self.rate_limits[provider]['requests_per_hour']
    
    def _track_api_call(self, provider: str):
        """Rastrear llamada a API"""
        if provider not in self.api_calls:
            self.api_calls[provider] = []
        self.api_calls[provider].append(datetime.now())
    
    def _execute_git_command(self, repo_path: str, command: List[str]) -> Dict[str, Any]:
        """Ejecutar comando git de forma segura"""
        try:
            # Cambiar al directorio del repositorio
            original_dir = os.getcwd()
            os.chdir(repo_path)
            
            # Ejecutar comando
            result = subprocess.run(
                ['git'] + command,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            os.chdir(original_dir)
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Command timed out',
                'stdout': '',
                'stderr': '',
                'return_code': -1
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stdout': '',
                'stderr': '',
                'return_code': -1
            }
    
    def _parse_git_output(self, output: str) -> List[Dict[str, str]]:
        """Parsear salida de comandos git"""
        lines = output.strip().split('\n')
        result = []
        
        for line in lines:
            if line:
                result.append({'line': line})
        
        return result
    
    # ========== OPERACIONES BÁSICAS DE GIT ==========
    
    def clone_repository(self, url: str, path: str, branch: Optional[str] = None, 
                        depth: Optional[int] = None, bare: bool = False) -> Dict[str, Any]:
        """Clonar un repositorio"""
        try:
            clone_args = []
            
            if branch:
                clone_args.extend(['--branch', branch])
            if depth:
                clone_args.extend(['--depth', str(depth)])
            if bare:
                clone_args.append('--bare')
            
            repo = Repo.clone_from(url, path, multi_options=clone_args)
            
            return {
                'success': True,
                'message': f'Repositorio clonado exitosamente en {path}',
                'repository': GitRepository(
                    path=path,
                    url=url,
                    provider=self._detect_provider(url),
                    default_branch=repo.active_branch.name,
                    current_branch=repo.active_branch.name,
                    remotes={remote.name: remote.url for remote in repo.remotes},
                    last_commit=repo.head.commit.hexsha[:8],
                    commit_count=len(list(repo.iter_commits()))
                )
            }
        except GitCommandError as e:
            return {
                'success': False,
                'error': f'Error al clonar repositorio: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error inesperado: {str(e)}'
            }
    
    def pull_changes(self, repo_path: str, remote: str = 'origin', 
                    branch: Optional[str] = None) -> Dict[str, Any]:
        """Obtener cambios del repositorio remoto"""
        try:
            repo = Repo(repo_path)
            
            # Actualizar remote
            result = self._execute_git_command(repo_path, ['remote', 'update'])
            if not result['success']:
                return {
                    'success': False,
                    'error': f'Error al actualizar remote: {result["stderr"]}'
                }
            
            # Hacer pull
            result = self._execute_git_command(repo_path, ['pull', remote] + 
                                            ([branch] if branch else []))
            
            if result['success']:
                return {
                    'success': True,
                    'message': 'Cambios obtenidos exitosamente',
                    'output': result['stdout']
                }
            else:
                return {
                    'success': False,
                    'error': f'Error al hacer pull: {result["stderr"]}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def push_changes(self, repo_path: str, remote: str = 'origin', 
                    branch: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
        """Enviar cambios al repositorio remoto"""
        try:
            push_args = ['push']
            if force:
                push_args.append('--force')
            
            push_args.extend([remote] + ([branch] if branch else []))
            
            result = self._execute_git_command(repo_path, push_args)
            
            if result['success']:
                return {
                    'success': True,
                    'message': 'Cambios enviados exitosamente',
                    'output': result['stdout']
                }
            else:
                return {
                    'success': False,
                    'error': f'Error al hacer push: {result["stderr"]}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_repository_info(self, repo_path: str) -> Dict[str, Any]:
        """Obtener información completa del repositorio"""
        try:
            repo = Repo(repo_path)
            
            # Información básica
            remotes = {remote.name: remote.url for remote in repo.remotes}
            
            # Estado actual
            if repo.head.is_detached:
                status = 'detached'
                current_branch = None
            else:
                status = repo.git.status()
                current_branch = repo.active_branch.name
            
            # Último commit
            last_commit = repo.head.commit.hexsha[:8] if repo.head.commit else None
            commit_count = len(list(repo.iter_commits()))
            
            # Branches locales y remotas
            local_branches = [branch.name for branch in repo.branches]
            remote_branches = [branch.name for branch in repo.remote().refs]
            
            # Tags
            tags = [tag.name for tag in repo.tags]
            
            repository = GitRepository(
                path=repo_path,
                url=remotes.get('origin', ''),
                provider=self._detect_provider(remotes.get('origin', '')),
                default_branch=repo.active_branch.name,
                current_branch=current_branch,
                remotes=remotes,
                last_commit=last_commit,
                commit_count=commit_count,
                status=status
            )
            
            return {
                'success': True,
                'repository': repository,
                'local_branches': local_branches,
                'remote_branches': remote_branches,
                'tags': tags,
                'is_dirty': repo.is_dirty(),
                'is_detached': repo.head.is_detached
            }
            
        except InvalidGitRepositoryError:
            return {
                'success': False,
                'error': 'No es un repositorio Git válido'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _detect_provider(self, url: str) -> GitProvider:
        """Detectar el proveedor de Git basado en la URL"""
        if 'github.com' in url.lower():
            return GitProvider.GITHUB
        elif 'gitlab.com' in url.lower():
            return GitProvider.GITLAB
        elif 'bitbucket.org' in url.lower():
            return GitProvider.BITBUCKET
        else:
            return GitProvider.GENERIC
    
    # ========== GESTIÓN DE BRANCHES ==========
    
    def create_branch(self, repo_path: str, branch_name: str, 
                     from_branch: Optional[str] = None) -> Dict[str, Any]:
        """Crear una nueva branch"""
        try:
            repo = Repo(repo_path)
            
            # Determinar branch base
            if from_branch:
                # Cambiar a la branch base si no está activa
                if repo.active_branch.name != from_branch:
                    repo.git.checkout(from_branch)
            
            # Crear nueva branch
            result = self._execute_git_command(repo_path, ['checkout', '-b', branch_name])
            
            if result['success']:
                return {
                    'success': True,
                    'message': f'Branch {branch_name} creada exitosamente',
                    'branch': branch_name
                }
            else:
                return {
                    'success': False,
                    'error': f'Error al crear branch: {result["stderr"]}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_branch(self, repo_path: str, branch_name: str, 
                     force: bool = False, remote: Optional[str] = None) -> Dict[str, Any]:
        """Eliminar una branch"""
        try:
            if remote:
                # Eliminar branch remota
                result = self._execute_git_command(repo_path, ['push', remote, '--delete', branch_name])
            else:
                # Eliminar branch local
                delete_flag = '-D' if force else '-d'
                result = self._execute_git_command(repo_path, [delete_flag, branch_name])
            
            if result['success']:
                return {
                    'success': True,
                    'message': f'Branch {branch_name} eliminada exitosamente',
                    'branch': branch_name,
                    'remote': remote
                }
            else:
                return {
                    'success': False,
                    'error': f'Error al eliminar branch: {result["stderr"]}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def switch_branch(self, repo_path: str, branch_name: str) -> Dict[str, Any]:
        """Cambiar a una branch"""
        try:
            result = self._execute_git_command(repo_path, ['checkout', branch_name])
            
            if result['success']:
                return {
                    'success': True,
                    'message': f'Cambiado a branch {branch_name}',
                    'branch': branch_name
                }
            else:
                return {
                    'success': False,
                    'error': f'Error al cambiar de branch: {result["stderr"]}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_branches(self, repo_path: str, local: bool = True, 
                     remote: bool = True) -> Dict[str, Any]:
        """Listar branches"""
        try:
            branches = []
            
            if local:
                result = self._execute_git_command(repo_path, ['branch', '--list'])
                if result['success']:
                    local_branches = result['stdout'].strip().split('\n')
                    for branch in local_branches:
                        if branch.strip():
                            current = '* ' in branch
                            name = branch.strip().replace('* ', '')
                            branches.append({
                                'name': name,
                                'current': current,
                                'type': 'local'
                            })
            
            if remote:
                result = self._execute_git_command(repo_path, ['branch', '-r'])
                if result['success']:
                    remote_branches = result['stdout'].strip().split('\n')
                    for branch in remote_branches:
                        if branch.strip():
                            name = branch.strip()
                            branches.append({
                                'name': name,
                                'current': False,
                                'type': 'remote'
                            })
            
            return {
                'success': True,
                'branches': branches
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_branch_info(self, repo_path: str, branch_name: str) -> Dict[str, Any]:
        """Obtener información detallada de una branch"""
        try:
            # Obtener información de ahead/behind
            result = self._execute_git_command(repo_path, ['rev-list', '--count', '--left-right', 
                                                         f'origin/{branch_name}...{branch_name}'])
            
            ahead = 0
            behind = 0
            
            if result['success'] and result['stdout'].strip():
                counts = result['stdout'].strip().split()
                if len(counts) == 2:
                    behind = int(counts[0])
                    ahead = int(counts[1])
            
            # Último commit de la branch
            result = self._execute_git_command(repo_path, ['log', '-1', '--format=%H', branch_name])
            last_commit = result['stdout'].strip() if result['success'] else None
            
            # Merge base
            result = self._execute_git_command(repo_path, ['merge-base', 'origin/main', branch_name])
            merge_base = result['stdout'].strip() if result['success'] else None
            
            branch_info = BranchInfo(
                name=branch_name,
                is_local=True,
                is_remote=f'origin/{branch_name}' in str(result),
                tracking_branch=f'origin/{branch_name}',
                ahead=ahead,
                behind=behind,
                last_commit=last_commit,
                merge_base=merge_base
            )
            
            return {
                'success': True,
                'branch_info': branch_info
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ========== MERGE Y REBASE ==========
    
    def merge_branch(self, repo_path: str, source_branch: str, 
                    strategy: MergeStrategy = MergeStrategy.MERGE,
                    no_ff: bool = False, message: Optional[str] = None) -> Dict[str, Any]:
        """Hacer merge de una branch"""
        try:
            repo = Repo(repo_path)
            
            merge_args = []
            if no_ff:
                merge_args.append('--no-ff')
            
            if message:
                merge_args.extend(['-m', message])
            
            # Cambiar a la branch objetivo (main/develop)
            target_branch = repo.active_branch.name
            repo.git.checkout(target_branch)
            
            # Hacer merge
            merge_command = ['merge'] + merge_args + [source_branch]
            result = self._execute_git_command(repo_path, merge_command)
            
            if result['success']:
                return {
                    'success': True,
                    'message': f'Merge de {source_branch} completado exitosamente',
                    'target_branch': target_branch,
                    'source_branch': source_branch,
                    'strategy': strategy.value
                }
            else:
                return {
                    'success': False,
                    'error': f'Error en merge: {result["stderr"]}',
                    'may_have_conflicts': 'CONFLICT' in result['stdout']
                }
        except GitCommandError as e:
            return {
                'success': False,
                'error': f'Error en merge: {str(e)}',
                'conflict_detected': True
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def rebase_branch(self, repo_path: str, source_branch: str, 
                     onto_branch: Optional[str] = None) -> Dict[str, Any]:
        """Hacer rebase de una branch"""
        try:
            repo = Repo(repo_path)
            
            if onto_branch:
                result = self._execute_git_command(repo_path, ['rebase', onto_branch, source_branch])
            else:
                result = self._execute_git_command(repo_path, ['rebase', source_branch])
            
            if result['success']:
                return {
                    'success': True,
                    'message': f'Rebase de {source_branch} completado exitosamente',
                    'source_branch': source_branch,
                    'onto_branch': onto_branch
                }
            else:
                return {
                    'success': False,
                    'error': f'Error en rebase: {result["stderr"]}',
                    'may_have_conflicts': 'CONFLICT' in result['stdout']
                }
        except GitCommandError as e:
            return {
                'success': False,
                'error': f'Error en rebase: {str(e)}',
                'conflict_detected': True
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def abort_rebase(self, repo_path: str) -> Dict[str, Any]:
        """Cancelar un rebase en progreso"""
        try:
            result = self._execute_git_command(repo_path, ['rebase', '--abort'])
            
            if result['success']:
                return {
                    'success': True,
                    'message': 'Rebase cancelado exitosamente'
                }
            else:
                return {
                    'success': False,
                    'error': f'Error al cancelar rebase: {result["stderr"]}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def continue_rebase(self, repo_path: str) -> Dict[str, Any]:
        """Continuar un rebase después de resolver conflictos"""
        try:
            result = self._execute_git_command(repo_path, ['rebase', '--continue'])
            
            if result['success']:
                return {
                    'success': True,
                    'message': 'Rebase continuado exitosamente'
                }
            else:
                return {
                    'success': False,
                    'error': f'Error al continuar rebase: {result["stderr"]}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ========== RESOLUCIÓN DE CONFLICTOS ==========
    
    def detect_conflicts(self, repo_path: str) -> Dict[str, Any]:
        """Detectar conflictos en el repositorio"""
        try:
            result = self._execute_git_command(repo_path, ['diff', '--name-only', '--diff-filter=U'])
            
            conflicts = []
            if result['success'] and result['stdout']:
                conflict_files = result['stdout'].strip().split('\n')
                
                for file in conflict_files:
                    if file.strip():
                        # Obtener información detallada del conflicto
                        conflict_info = self._analyze_conflict(repo_path, file.strip())
                        conflicts.append(conflict_info)
            
            return {
                'success': True,
                'conflicts': conflicts,
                'total_conflicts': len(conflicts)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_conflict(self, repo_path: str, file_path: str) -> Dict[str, Any]:
        """Analizar un conflicto específico"""
        try:
            result = self._execute_git_command(repo_path, ['diff', file_path])
            
            conflict_info = {
                'file': file_path,
                'status': 'conflicted',
                'has_conflicts': '<<<<<<<' in result['stdout'] or '>>>>>>>' in result['stdout'],
                'conflict_markers': self._extract_conflict_markers(result['stdout'])
            }
            
            return conflict_info
        except Exception as e:
            return {
                'file': file_path,
                'status': 'error',
                'error': str(e)
            }
    
    def _extract_conflict_markers(self, diff_content: str) -> List[Dict[str, str]]:
        """Extraer marcadores de conflicto del contenido"""
        markers = []
        
        lines = diff_content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('<<<<<<< '):
                markers.append({
                    'type': 'start',
                    'line': i,
                    'content': line[8:]  # Remove <<<<<<< prefix
                })
            elif line.startswith('======='):
                markers.append({
                    'type': 'separator',
                    'line': i,
                    'content': line[7:]  # Remove ======= prefix
                })
            elif line.startswith('>>>>>>> '):
                markers.append({
                    'type': 'end',
                    'line': i,
                    'content': line[7:]  # Remove >>>>>>> prefix
                })
        
        return markers
    
    def resolve_conflict(self, repo_path: str, file_path: str, 
                        resolution: ConflictResolution, custom_content: Optional[str] = None) -> Dict[str, Any]:
        """Resolver un conflicto específico"""
        try:
            file_abs_path = os.path.join(repo_path, file_path)
            
            if resolution == ConflictResolution.THEIRS:
                # Usar versión "their" (entrada)
                result = self._execute_git_command(repo_path, ['checkout', '--theirs', file_path])
            elif resolution == ConflictResolution.OURS:
                # Usar versión "our" (salida)
                result = self._execute_git_command(repo_path, ['checkout', '--ours', file_path])
            elif resolution == ConflictResolution.MANUAL and custom_content:
                # Contenido personalizado
                with open(file_abs_path, 'w', encoding='utf-8') as f:
                    f.write(custom_content)
                result = {'success': True, 'stdout': '', 'stderr': ''}
            else:
                return {
                    'success': False,
                    'error': 'Resolución inválida o contenido personalizado faltante'
                }
            
            if result['success']:
                return {
                    'success': True,
                    'message': f'Conflicto en {file_path} resuelto usando {resolution.value}',
                    'file': file_path,
                    'resolution': resolution.value
                }
            else:
                return {
                    'success': False,
                    'error': f'Error al resolver conflicto: {result["stderr"]}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def mark_conflict_resolved(self, repo_path: str, file_path: str) -> Dict[str, Any]:
        """Marcar un conflicto como resuelto"""
        try:
            result = self._execute_git_command(repo_path, ['add', file_path])
            
            if result['success']:
                return {
                    'success': True,
                    'message': f'Conflicto en {file_path} marcado como resuelto',
                    'file': file_path
                }
            else:
                return {
                    'success': False,
                    'error': f'Error al marcar conflicto como resuelto: {result["stderr"]}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ========== ANÁLISIS DE COMMITS ==========
    
    def get_commit_history(self, repo_path: str, since: Optional[str] = None, 
                          until: Optional[str] = None, author: Optional[str] = None,
                          branch: Optional[str] = None) -> Dict[str, Any]:
        """Obtener historial de commits"""
        try:
            repo = Repo(repo_path)
            
            # Construir comando git log
            log_args = ['log', '--oneline', '--decorate']
            
            if since:
                log_args.extend(['--since', since])
            if until:
                log_args.extend(['--until', until])
            if author:
                log_args.extend(['--author', author])
            if branch:
                log_args.append(branch)
            
            result = self._execute_git_command(repo_path, log_args)
            
            commits = []
            if result['success'] and result['stdout']:
                commit_lines = result['stdout'].strip().split('\n')
                
                for line in commit_lines:
                    if line:
                        parts = line.split(' ', 1)
                        if len(parts) == 2:
                            hash_part, message = parts
                            
                            # Obtener información detallada del commit
                            commit_info = self._get_commit_details(repo_path, hash_part)
                            commits.append(commit_info)
            
            return {
                'success': True,
                'commits': commits,
                'total_commits': len(commits)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_commit_details(self, repo_path: str, commit_hash: str) -> CommitInfo:
        """Obtener detalles completos de un commit"""
        try:
            repo = Repo(repo_path)
            commit = repo.commit(commit_hash)
            
            # Archivos modificados
            files_changed = []
            insertions = 0
            deletions = 0
            
            for commit_file in commit.stats.files:
                files_changed.append(commit_file)
                if commit_file in commit.stats.files:
                    insertions += commit.stats.files[commit_file]['insertions']
                    deletions += commit_stats.files[commit_file]['deletions']
            
            return CommitInfo(
                hash=commit.hexsha,
                message=commit.message.strip(),
                author=commit.author.name,
                email=commit.author.email,
                date=datetime.fromtimestamp(commit.committed_date),
                files_changed=files_changed,
                insertions=insertions,
                deletions=deletions,
                parent_hashes=[p.hexsha for p in commit.parents],
                branch=repo.active_branch.name if not repo.head.is_detached else None
            )
        except Exception as e:
            logger.error(f"Error obteniendo detalles del commit {commit_hash}: {e}")
            return CommitInfo(
                hash=commit_hash,
                message='Error',
                author='Unknown',
                email='unknown@example.com',
                date=datetime.now(),
                files_changed=[]
            )
    
    def analyze_commit_impact(self, repo_path: str, commit_hash: str) -> Dict[str, Any]:
        """Analizar el impacto de un commit específico"""
        try:
            repo = Repo(repo_path)
            commit = repo.commit(commit_hash)
            
            # Archivos afectados
            changed_files = []
            added_files = []
            modified_files = []
            deleted_files = []
            
            # Comparar con commit anterior
            if commit.parents:
                parent = commit.parents[0]
                diff = parent.diff(commit)
                
                for item in diff:
                    if item.change_type == 'A':
                        added_files.append(item.a_path)
                    elif item.change_type == 'M':
                        modified_files.append(item.a_path)
                    elif item.change_type == 'D':
                        deleted_files.append(item.a_path)
                    changed_files.append(item.a_path)
            
            # Estadísticas
            total_lines = commit.stats.total['lines']
            additions = commit.stats.total['insertions']
            deletions = commit.stats.total['deletions']
            
            # Archivos por tipo
            file_types = {}
            for file_path in changed_files:
                ext = os.path.splitext(file_path)[1].lower()
                if ext:
                    file_types[ext] = file_types.get(ext, 0) + 1
            
            return {
                'success': True,
                'commit_hash': commit_hash,
                'impact_summary': {
                    'changed_files': len(changed_files),
                    'added_files': len(added_files),
                    'modified_files': len(modified_files),
                    'deleted_files': len(deleted_files),
                    'total_lines': total_lines,
                    'additions': additions,
                    'deletions': deletions,
                    'net_lines': additions - deletions
                },
                'files': {
                    'changed': changed_files,
                    'added': added_files,
                    'modified': modified_files,
                    'deleted': deleted_files
                },
                'file_types': file_types
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def search_commits(self, repo_path: str, search_term: str, 
                      search_type: str = 'message') -> Dict[str, Any]:
        """Buscar commits por criterios específicos"""
        try:
            if search_type == 'message':
                result = self._execute_git_command(repo_path, ['log', '--grep', search_term, '--oneline'])
            elif search_type == 'author':
                result = self._execute_git_command(repo_path, ['log', '--author', search_term, '--oneline'])
            elif search_type == 'file':
                result = self._execute_git_command(repo_path, ['log', '--follow', search_term, '--oneline'])
            else:
                return {
                    'success': False,
                    'error': f'Tipo de búsqueda no soportado: {search_type}'
                }
            
            commits = []
            if result['success'] and result['stdout']:
                commit_lines = result['stdout'].strip().split('\n')
                
                for line in commit_lines:
                    if line:
                        parts = line.split(' ', 1)
                        if len(parts) == 2:
                            hash_part, message = parts
                            commits.append({
                                'hash': hash_part,
                                'message': message,
                                'details': self._get_commit_details(repo_path, hash_part)
                            })
            
            return {
                'success': True,
                'search_term': search_term,
                'search_type': search_type,
                'commits': commits,
                'total_results': len(commits)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ========== VISUALIZACIÓN DE DIFFS ==========
    
    def get_diff(self, repo_path: str, from_commit: Optional[str] = None, 
                to_commit: Optional[str] = None, file_path: Optional[str] = None,
                unified: int = 3) -> Dict[str, Any]:
        """Obtener diff entre commits o estado actual"""
        try:
            diff_args = ['diff']
            if unified:
                diff_args.extend(['-U', str(unified)])
            
            if from_commit and to_commit:
                diff_args.extend([from_commit, to_commit])
            elif to_commit:
                diff_args.append(to_commit)
            elif file_path:
                diff_args.append(file_path)
            else:
                # Estado de trabajo actual
                pass
            
            result = self._execute_git_command(repo_path, diff_args)
            
            if result['success']:
                # Parsear diff para obtener estadísticas
                stats = self._parse_diff_stats(result['stdout'])
                
                return {
                    'success': True,
                    'diff': result['stdout'],
                    'statistics': stats,
                    'from_commit': from_commit,
                    'to_commit': to_commit
                }
            else:
                return {
                    'success': False,
                    'error': f'Error generando diff: {result["stderr"]}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_diff_stats(self, diff_content: str) -> Dict[str, int]:
        """Parsear estadísticas de un diff"""
        stats = {'files_changed': 0, 'insertions': 0, 'deletions': 0}
        
        # Buscar líneas que empiecen con "+" o "-" (excluyendo +++ y ---)
        lines = diff_content.split('\n')
        current_file = None
        
        for line in lines:
            if line.startswith('diff --git'):
                stats['files_changed'] += 1
            elif line.startswith('+++') or line.startswith('---'):
                continue  # Skip header lines
            elif line.startswith('+') and not line.startswith('+++'):
                stats['insertions'] += 1
            elif line.startswith('-') and not line.startswith('---'):
                stats['deletions'] += 1
        
        return stats
    
    def get_uncommitted_changes(self, repo_path: str) -> Dict[str, Any]:
        """Obtener cambios no comprometidos"""
        try:
            # Diferentes tipos de cambios
            changes = {}
            
            # Cambios en staging area
            result = self._execute_git_command(repo_path, ['diff', '--cached', '--name-status'])
            if result['success']:
                staged_changes = self._parse_status_output(result['stdout'])
                changes['staged'] = staged_changes
            
            # Cambios en working directory
            result = self._execute_git_command(repo_path, ['diff', '--name-status'])
            if result['success']:
                unstaged_changes = self._parse_status_output(result['stdout'])
                changes['unstaged'] = unstaged_changes
            
            # Archivos no trackeados
            result = self._execute_git_command(repo_path, ['ls-files', '--others', '--exclude-standard'])
            if result['success']:
                untracked_files = result['stdout'].strip().split('\n') if result['stdout'].strip() else []
                changes['untracked'] = [{'file': f, 'status': 'untracked'} for f in untracked_files]
            
            return {
                'success': True,
                'changes': changes,
                'total_files': sum(len(v) for v in changes.values())
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_status_output(self, output: str) -> List[Dict[str, str]]:
        """Parsear salida de git status"""
        changes = []
        
        if not output.strip():
            return changes
        
        lines = output.strip().split('\n')
        for line in lines:
            if line:
                parts = line.split('\t', 1)
                if len(parts) == 2:
                    status, file = parts
                    changes.append({
                        'file': file,
                        'status': status
                    })
        
        return changes
    
    # ========== INTEGRACIÓN CON GITHUB/GITLAB APIs ==========
    
    async def create_pull_request_github(self, repo_owner: str, repo_name: str, 
                                       title: str, body: str, head: str, base: str,
                                       draft: bool = False) -> Dict[str, Any]:
        """Crear Pull Request en GitHub"""
        if not self.github_token:
            return {'success': False, 'error': 'Token de GitHub no configurado'}
        
        if not self._check_rate_limit('github'):
            return {'success': False, 'error': 'Límite de tasa excedido para GitHub'}
        
        try:
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            data = {
                'title': title,
                'body': body,
                'head': head,
                'base': base,
                'draft': draft
            }
            
            self._track_api_call('github')
            async with self.session.post(url, headers=headers, json=data) as response:
                result = await response.json()
                
                if response.status == 201:
                    return {
                        'success': True,
                        'pull_request': result,
                        'url': result['html_url']
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Error API GitHub: {result.get("message", "Unknown error")}'
                    }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_pull_requests_github(self, repo_owner: str, repo_name: str, 
                                     state: str = 'open') -> Dict[str, Any]:
        """Obtener Pull Requests de GitHub"""
        if not self.github_token:
            return {'success': False, 'error': 'Token de GitHub no configurado'}
        
        if not self._check_rate_limit('github'):
            return {'success': False, 'error': 'Límite de tasa excedido para GitHub'}
        
        try:
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            params = {'state': state}
            
            self._track_api_call('github')
            async with self.session.get(url, headers=headers, params=params) as response:
                result = await response.json()
                
                if response.status == 200:
                    pull_requests = []
                    for pr in result:
                        pull_request = PullRequest(
                            id=str(pr['number']),
                            title=pr['title'],
                            source_branch=pr['head']['ref'],
                            target_branch=pr['base']['ref'],
                            author=pr['user']['login'],
                            state=pr['state'],
                            url=pr['html_url'],
                            description=pr['body'] or '',
                            created_at=datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00')),
                            updated_at=datetime.fromisoformat(pr['updated_at'].replace('Z', '+00:00')),
                            commits=[],  # Se puede obtener con otra llamada API
                            reviewers=[r['login'] for r in pr.get('requested_reviewers', [])],
                            labels=[label['name'] for label in pr.get('labels', [])]
                        )
                        pull_requests.append(pull_request)
                    
                    return {
                        'success': True,
                        'pull_requests': pull_requests,
                        'total': len(pull_requests)
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Error API GitHub: {result.get("message", "Unknown error")}'
                    }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def create_merge_request_gitlab(self, project_id: str, title: str, 
                                        description: str, source_branch: str,
                                        target_branch: str) -> Dict[str, Any]:
        """Crear Merge Request en GitLab"""
        if not self.gitlab_token:
            return {'success': False, 'error': 'Token de GitLab no configurado'}
        
        if not self._check_rate_limit('gitlab'):
            return {'success': False, 'error': 'Límite de tasa excedido para GitLab'}
        
        try:
            url = f"https://gitlab.com/api/v4/projects/{project_id}/merge_requests"
            headers = {
                'PRIVATE-TOKEN': self.gitlab_token,
                'Content-Type': 'application/json'
            }
            data = {
                'title': title,
                'description': description,
                'source_branch': source_branch,
                'target_branch': target_branch
            }
            
            self._track_api_call('gitlab')
            async with self.session.post(url, headers=headers, json=data) as response:
                result = await response.json()
                
                if response.status == 201:
                    return {
                        'success': True,
                        'merge_request': result,
                        'url': result.get('web_url', '')
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Error API GitLab: {result.get("message", "Unknown error")}'
                    }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_repository_info_github(self, repo_owner: str, repo_name: str) -> Dict[str, Any]:
        """Obtener información de repositorio desde GitHub"""
        if not self.github_token:
            return {'success': False, 'error': 'Token de GitHub no configurado'}
        
        if not self._check_rate_limit('github'):
            return {'success': False, 'error': 'Límite de tasa excedido para GitHub'}
        
        try:
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            self._track_api_call('github')
            async with self.session.get(url, headers=headers) as response:
                result = await response.json()
                
                if response.status == 200:
                    return {
                        'success': True,
                        'repository': result,
                        'stats': {
                            'stars': result.get('stargazers_count', 0),
                            'forks': result.get('forks_count', 0),
                            'watchers': result.get('watchers_count', 0),
                            'open_issues': result.get('open_issues_count', 0)
                        }
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Error API GitHub: {result.get("message", "Unknown error")}'
                    }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ========== INTEGRACIÓN CI/CD ==========
    
    async def get_workflow_runs_github(self, repo_owner: str, repo_name: str, 
                                     workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """Obtener ejecuciones de workflows de GitHub Actions"""
        if not self.github_token:
            return {'success': False, 'error': 'Token de GitHub no configurado'}
        
        if not self._check_rate_limit('github'):
            return {'success': False, 'error': 'Límite de tasa excedido para GitHub'}
        
        try:
            if workflow_id:
                url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows/{workflow_id}/runs"
            else:
                url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs"
            
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            self._track_api_call('github')
            async with self.session.get(url, headers=headers) as response:
                result = await response.json()
                
                if response.status == 200:
                    workflow_runs = []
                    for run in result.get('workflow_runs', []):
                        workflow_run = WorkflowRun(
                            id=str(run['id']),
                            workflow_name=run.get('name', 'Unknown'),
                            status=run.get('status', 'unknown'),
                            conclusion=run.get('conclusion', 'unknown'),
                            branch=run.get('head_branch', ''),
                            commit=run.get('head_sha', ''),
                            url=run.get('html_url', ''),
                            start_time=datetime.fromisoformat(run['created_at'].replace('Z', '+00:00')),
                            end_time=datetime.fromisoformat(run['updated_at'].replace('Z', '+00:00')) if run.get('updated_at') else None,
                            duration=None,  # Se puede calcular si hay datos
                            jobs=[]  # Se puede obtener con otra llamada API
                        )
                        workflow_runs.append(workflow_run)
                    
                    return {
                        'success': True,
                        'workflow_runs': workflow_runs,
                        'total': len(workflow_runs)
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Error API GitHub: {result.get("message", "Unknown error")}'
                    }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_ci_cd_pipeline(self, repo_path: str, 
                             config_file: str = '.github/workflows/') -> Dict[str, Any]:
        """Analizar configuración de pipeline CI/CD"""
        try:
            analysis = {
                'has_ci_cd': False,
                'platform': None,
                'workflows': [],
                'quality_checks': [],
                'deployment_stages': [],
                'test_strategies': []
            }
            
            workflows_dir = os.path.join(repo_path, config_file)
            if not os.path.exists(workflows_dir):
                return {
                    'success': True,
                    'analysis': analysis
                }
            
            analysis['has_ci_cd'] = True
            analysis['platform'] = 'github_actions'
            
            # Analizar archivos de workflow
            for file_name in os.listdir(workflows_dir):
                if file_name.endswith(('.yml', '.yaml')):
                    file_path = os.path.join(workflows_dir, file_name)
                    workflow_analysis = self._analyze_workflow_file(file_path)
                    analysis['workflows'].append(workflow_analysis)
            
            return {
                'success': True,
                'analysis': analysis
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_workflow_file(self, file_path: str) -> Dict[str, Any]:
        """Analizar un archivo de workflow específico"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                workflow_content = yaml.safe_load(f)
            
            analysis = {
                'file': os.path.basename(file_path),
                'name': workflow_content.get('name', 'Unnamed'),
                'triggers': workflow_content.get('on', []),
                'jobs': [],
                'steps': []
            }
            
            # Analizar jobs
            jobs = workflow_content.get('jobs', {})
            for job_name, job_config in jobs.items():
                job_analysis = {
                    'name': job_name,
                    'runs_on': job_config.get('runs-on', 'unknown'),
                    'steps': len(job_config.get('steps', [])),
                    'uses_cache': 'cache' in str(job_config).lower(),
                    'has_tests': any('test' in step.lower() if isinstance(step, dict) else False 
                                   for step in job_config.get('steps', []))
                }
                analysis['jobs'].append(job_analysis)
                analysis['steps'].extend(job_config.get('steps', []))
            
            return analysis
        except Exception as e:
            return {
                'file': os.path.basename(file_path),
                'error': str(e)
            }
    
    def trigger_ci_cd_pipeline(self, repo_path: str, workflow_name: str, 
                             ref: str = 'main') -> Dict[str, Any]:
        """Disparar pipeline CI/CD manualmente"""
        try:
            # Para GitHub Actions, necesitaríamos usar la API
            # Por ahora, retornamos información sobre cómo hacerlo
            
            return {
                'success': True,
                'message': f'Pipeline {workflow_name} puede ser disparado manualmente',
                'instructions': [
                    f'Ve al repositorio en GitHub',
                    f'Ve a Actions tab',
                    f'Selecciona workflow {workflow_name}',
                    f'Haz click en "Run workflow"',
                    f'Usa ref: {ref}'
                ],
                'api_endpoint': '/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ========== WEBHOOKS ==========
    
    def setup_webhook_handler(self, repo_path: str, webhook_config: Dict[str, Any]) -> Dict[str, Any]:
        """Configurar manejador de webhooks"""
        try:
            webhook_script_path = os.path.join(repo_path, 'webhook_handler.py')
            
            webhook_script = self._generate_webhook_script(webhook_config)
            
            with open(webhook_script_path, 'w', encoding='utf-8') as f:
                f.write(webhook_script)
            
            # Configurar Git para usar el webhook
            git_hooks_path = os.path.join(repo_path, '.git', 'hooks')
            os.chmod(webhook_script_path, 0o755)  # Make executable
            
            return {
                'success': True,
                'message': f'Webhook handler configurado en {webhook_script_path}',
                'config': webhook_config
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_webhook_script(self, config: Dict[str, Any]) -> str:
        """Generar script Python para manejar webhooks"""
        script_template = '''#!/usr/bin/env python3
"""
Webhook Handler para Git Repository
Configurado automáticamente por Git Operations Agent
"""

import os
import sys
import json
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def handle_push_event(payload):
    """Manejar evento de push"""
    logger.info(f"Push event: {payload['ref']} - {payload['pusher']['name']}")
    
    # Auto-deploy en branch específica
    if payload['ref'] == 'refs/heads/main':
        logger.info("Deploying to production")
        # Agregar lógica de deployment
    
    # Trigger CI/CD
    logger.info("Triggering CI/CD pipeline")

def handle_pull_request_event(payload):
    """Manejar evento de pull request"""
    action = payload['action']
    pr = payload['pull_request']
    
    logger.info(f"PR {action}: {pr['title']} by {pr['user']['login']}")
    
    # Auto-review o auto-merge basado en reglas
    if action == 'opened':
        logger.info("Running automated tests on PR")
    
    if action == 'closed' and pr['merged']:
        logger.info(f"PR merged: {pr['title']}")

def handle_workflow_run_event(payload):
    """Manejar evento de workflow run"""
    workflow_run = payload['workflow_run']
    conclusion = workflow_run['conclusion']
    
    logger.info(f"Workflow {workflow_run['name']} completed with conclusion: {conclusion}")
    
    # Notificar o tomar acciones basadas en resultado
    if conclusion == 'failure':
        logger.error("CI/CD pipeline failed - sending notifications")
    
    if conclusion == 'success':
        logger.info("CI/CD pipeline succeeded - proceeding with deployment")

def main():
    """Función principal del webhook handler"""
    try:
        # Leer payload del webhook
        payload = json.loads(sys.stdin.read())
        
        # Determinar tipo de evento
        event = os.environ.get('GIT_EVENT', 'unknown')
        
        # Manejar evento específico
        if event == 'push':
            handle_push_event(payload)
        elif event == 'pull_request':
            handle_pull_request_event(payload)
        elif event == 'workflow_run':
            handle_workflow_run_event(payload)
        else:
            logger.warning(f"Unhandled event type: {event}")
        
        logger.info("Webhook processed successfully")
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
'''
        return script_template
    
    def create_webhook_config(self, provider: GitProvider, repo_url: str, 
                            secret: str = None) -> Dict[str, Any]:
        """Crear configuración de webhook para diferentes proveedores"""
        webhook_config = {
            'provider': provider.value,
            'url': repo_url,
            'events': [
                'push',
                'pull_request',
                'pull_request_review',
                'workflow_run',
                'issues'
            ],
            'active': True
        }
        
        if secret:
            webhook_config['secret'] = secret
        
        if provider == GitProvider.GITHUB:
            webhook_config['config'] = {
                'content_type': 'json',
                'insecure_ssl': '0'
            }
        elif provider == GitProvider.GITLAB:
            webhook_config['config'] = {
                'enable_ssl_verification': True
            }
        
        return {
            'success': True,
            'webhook_config': webhook_config
        }
    
    # ========== TESTING AUTOMATIZADO ==========
    
    def run_tests(self, repo_path: str, test_command: str = 'python -m pytest') -> Dict[str, Any]:
        """Ejecutar tests automatizados"""
        try:
            # Cambiar al directorio del repositorio
            original_dir = os.getcwd()
            os.chdir(repo_path)
            
            # Ejecutar comando de tests
            result = subprocess.run(
                test_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutos timeout
            )
            
            os.chdir(original_dir)
            
            # Analizar resultados
            test_results = self._parse_test_results(result.stdout, result.stderr)
            
            return {
                'success': True,
                'test_command': test_command,
                'exit_code': result.returncode,
                'passed': test_results['passed'],
                'failed': test_results['failed'],
                'errors': test_results['errors'],
                'total': test_results['total'],
                'coverage': test_results.get('coverage'),
                'output': result.stdout,
                'stderr': result.stderr,
                'duration': test_results.get('duration', 0)
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Tests timed out after 10 minutes',
                'test_command': test_command
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'test_command': test_command
            }
    
    def _parse_test_results(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parsear resultados de tests"""
        results = {
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'total': 0,
            'duration': 0,
            'coverage': None
        }
        
        # Parsear output de pytest
        if 'passed' in stdout:
            lines = stdout.split('\n')
            for line in lines:
                if 'passed' in line and 'failed' in line:
                    # Parse: "5 passed, 2 failed in 10.5s"
                    match = re.search(r'(\d+)\s+passed.*?(\d+)\s+failed.*?in\s+([\d.]+)s', line)
                    if match:
                        results['passed'] = int(match.group(1))
                        results['failed'] = int(match.group(2))
                        results['duration'] = float(match.group(3))
                        results['total'] = results['passed'] + results['failed']
                        break
        
        # Buscar coverage
        if 'coverage' in stdout.lower():
            coverage_match = re.search(r'TOTAL.*?(\d+)%', stdout)
            if coverage_match:
                results['coverage'] = int(coverage_match.group(1))
        
        return results
    
    def setup_test_environment(self, repo_path: str, test_framework: str = 'pytest') -> Dict[str, Any]:
        """Configurar ambiente de testing"""
        try:
            setup_commands = []
            
            if test_framework == 'pytest':
                setup_commands.extend([
                    'pip install pytest',
                    'pip install pytest-cov',
                    'pip install pytest-mock'
                ])
            elif test_framework == 'unittest':
                setup_commands.append('pip install coverage')
            elif test_framework == 'jest':
                setup_commands.extend([
                    'npm install --save-dev jest',
                    'npm install --save-dev @types/jest'
                ])
            
            # Crear directorio de tests
            tests_dir = os.path.join(repo_path, 'tests')
            os.makedirs(tests_dir, exist_ok=True)
            
            # Crear archivo de configuración básico
            if test_framework == 'pytest':
                config_file = os.path.join(repo_path, 'pytest.ini')
                with open(config_file, 'w') as f:
                    f.write('''[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=. --cov-report=term-missing --cov-report=html
''')
            elif test_framework == 'unittest':
                config_file = os.path.join(repo_path, 'coverage.ini')
                with open(config_file, 'w') as f:
                    f.write('''[run]
source = .
omit = 
    */tests/*
    */test_*
    setup.py
''')
            
            return {
                'success': True,
                'message': f'Ambiente de testing configurado para {test_framework}',
                'setup_commands': setup_commands,
                'test_directory': tests_dir,
                'config_file': config_file
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_test_report(self, repo_path: str, output_format: str = 'html') -> Dict[str, Any]:
        """Generar reporte de tests"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if output_format == 'html':
                report_path = os.path.join(repo_path, f'test_report_{timestamp}.html')
                coverage_path = os.path.join(repo_path, f'coverage_report_{timestamp}.html')
                
                # Generar reporte HTML
                result = subprocess.run([
                    'python', '-m', 'pytest', '--html=' + report_path,
                    '--self-contained-html', '--cov=.', '--cov-report=html:' + coverage_path
                ], capture_output=True, text=True, cwd=repo_path)
                
                return {
                    'success': True,
                    'report_path': report_path,
                    'coverage_path': coverage_path,
                    'format': 'html',
                    'command_used': 'pytest with html reporting'
                }
            
            elif output_format == 'json':
                report_path = os.path.join(repo_path, f'test_report_{timestamp}.json')
                
                result = subprocess.run([
                    'python', '-m', 'pytest', '--json-report', '--json-report-file=' + report_path
                ], capture_output=True, text=True, cwd=repo_path)
                
                return {
                    'success': True,
                    'report_path': report_path,
                    'format': 'json',
                    'command_used': 'pytest with json reporting'
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ========== MÚLTIPLES REMOTES ==========
    
    def add_remote(self, repo_path: str, name: str, url: str, fetch: bool = True) -> Dict[str, Any]:
        """Agregar un nuevo remote"""
        try:
            result = self._execute_git_command(repo_path, ['remote', 'add', name, url])
            
            if result['success']:
                if fetch:
                    fetch_result = self._execute_git_command(repo_path, ['fetch', name])
                    fetch_success = fetch_result['success']
                else:
                    fetch_success = None
                
                return {
                    'success': True,
                    'message': f'Remote {name} agregado exitosamente',
                    'remote_name': name,
                    'remote_url': url,
                    'fetched': fetch_success
                }
            else:
                return {
                    'success': False,
                    'error': f'Error al agregar remote: {result["stderr"]}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def remove_remote(self, repo_path: str, name: str) -> Dict[str, Any]:
        """Eliminar un remote"""
        try:
            result = self._execute_git_command(repo_path, ['remote', 'remove', name])
            
            if result['success']:
                return {
                    'success': True,
                    'message': f'Remote {name} eliminado exitosamente',
                    'remote_name': name
                }
            else:
                return {
                    'success': False,
                    'error': f'Error al eliminar remote: {result["stderr"]}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_remote(self, repo_path: str, name: str, new_url: str) -> Dict[str, Any]:
        """Actualizar URL de un remote"""
        try:
            result = self._execute_git_command(repo_path, ['remote', 'set-url', name, new_url])
            
            if result['success']:
                return {
                    'success': True,
                    'message': f'URL del remote {name} actualizada exitosamente',
                    'remote_name': name,
                    'new_url': new_url
                }
            else:
                return {
                    'success': False,
                    'error': f'Error al actualizar remote: {result["stderr"]}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_remotes(self, repo_path: str) -> Dict[str, Any]:
        """Listar todos los remotes"""
        try:
            result = self._execute_git_command(repo_path, ['remote', '-v'])
            
            remotes = []
            if result['success'] and result['stdout']:
                lines = result['stdout'].strip().split('\n')
                for line in lines:
                    if line:
                        parts = line.split()
                        if len(parts) >= 2:
                            name = parts[0]
                            url = parts[1]
                            operation = parts[2] if len(parts) > 2 else '(fetch)'
                            operation = operation.strip('()')
                            
                            # Agrupar por nombre de remote
                            existing = next((r for r in remotes if r['name'] == name), None)
                            if existing:
                                existing['operations'].append(operation)
                            else:
                                remotes.append({
                                    'name': name,
                                    'url': url,
                                    'operations': [operation]
                                })
            
            return {
                'success': True,
                'remotes': remotes,
                'total_remotes': len(remotes)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def sync_with_remote(self, repo_path: str, remote_name: str, 
                        direction: str = 'pull') -> Dict[str, Any]:
        """Sincronizar con un remote específico"""
        try:
            if direction == 'pull':
                result = self._execute_git_command(repo_path, ['pull', remote_name, '--all'])
            elif direction == 'fetch':
                result = self._execute_git_command(repo_path, ['fetch', remote_name])
            elif direction == 'push':
                result = self._execute_git_command(repo_path, ['push', remote_name, '--all'])
            else:
                return {
                    'success': False,
                    'error': f'Dirección no válida: {direction}'
                }
            
            if result['success']:
                return {
                    'success': True,
                    'message': f'Sincronización {direction} con {remote_name} completada',
                    'remote': remote_name,
                    'direction': direction,
                    'output': result['stdout']
                }
            else:
                return {
                    'success': False,
                    'error': f'Error en sincronización: {result["stderr"]}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ========== WORKFLOWS COMPLEJOS ==========
    
    def create_feature_branch_workflow(self, repo_path: str, feature_name: str, 
                                     base_branch: str = 'main') -> Dict[str, Any]:
        """Crear workflow completo para desarrollo de features"""
        try:
            workflow_steps = []
            
            # 1. Asegurar que estamos en la branch base
            repo = Repo(repo_path)
            current_branch = repo.active_branch.name
            
            if current_branch != base_branch:
                repo.git.checkout(base_branch)
                workflow_steps.append(f'Cambiado a branch {base_branch}')
            
            # 2. Pull de cambios remotos
            result = self._execute_git_command(repo_path, ['pull', 'origin', base_branch])
            if result['success']:
                workflow_steps.append('Obtenidos últimos cambios de origin/main')
            
            # 3. Crear nueva branch de feature
            feature_branch = f'feature/{feature_name}'
            result = self._execute_git_command(repo_path, ['checkout', '-b', feature_branch])
            if result['success']:
                workflow_steps.append(f'Creada branch de feature: {feature_branch}')
            
            # 4. Configurar tracking si es necesario
            workflow_steps.append('Branch de feature lista para desarrollo')
            
            return {
                'success': True,
                'workflow_type': 'feature_branch',
                'feature_name': feature_name,
                'feature_branch': feature_branch,
                'base_branch': base_branch,
                'steps': workflow_steps,
                'instructions': [
                    f'Desarrolla tu feature en la branch {feature_branch}',
                    f'Haz commits regularmente con mensajes descriptivos',
                    'Ejecuta tests antes de commit',
                    f'Cuando termines, haz push de la branch: git push -u origin {feature_branch}',
                    'Crea Pull Request desde GitHub/GitLab'
                ]
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_release_workflow(self, repo_path: str, version: str, 
                               release_notes: Optional[str] = None) -> Dict[str, Any]:
        """Crear workflow para releases"""
        try:
            workflow_steps = []
            
            # 1. Cambiar a main branch
            repo = Repo(repo_path)
            repo.git.checkout('main')
            workflow_steps.append('Cambiado a main branch')
            
            # 2. Pull de cambios
            result = self._execute_git_command(repo_path, ['pull', 'origin', 'main'])
            if result['success']:
                workflow_steps.append('Obtenidos últimos cambios')
            
            # 3. Crear tag de release
            tag_name = f'v{version}'
            if release_notes:
                result = self._execute_git_command(repo_path, ['tag', '-a', tag_name, '-m', release_notes])
            else:
                result = self._execute_git_command(repo_path, ['tag', tag_name])
            
            if result['success']:
                workflow_steps.append(f'Creado tag de release: {tag_name}')
            
            # 4. Push del tag
            result = self._execute_git_command(repo_path, ['push', 'origin', tag_name])
            if result['success']:
                workflow_steps.append('Tag enviado a origin')
            
            return {
                'success': True,
                'workflow_type': 'release',
                'version': version,
                'tag_name': tag_name,
                'steps': workflow_steps,
                'next_steps': [
                    'El release trigger automáticamente workflows CI/CD',
                    'GitHub/GitLab creará automáticamente el release',
                    'Deploy automático si está configurado'
                ]
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_hotfix_workflow(self, repo_path: str, fix_description: str, 
                              production_branch: str = 'main') -> Dict[str, Any]:
        """Crear workflow para hotfixes"""
        try:
            workflow_steps = []
            
            # 1. Cambiar a producción branch
            repo = Repo(repo_path)
            repo.git.checkout(production_branch)
            workflow_steps.append(f'Cambiado a {production_branch}')
            
            # 2. Crear branch de hotfix
            hotfix_branch = f'hotfix/{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            result = self._execute_git_command(repo_path, ['checkout', '-b', hotfix_branch])
            if result['success']:
                workflow_steps.append(f'Creada branch de hotfix: {hotfix_branch}')
            
            # 3. Aplicar fix (esto dependería de la naturaleza del fix)
            workflow_steps.append('Aplicar el fix en los archivos necesarios')
            
            # 4. Commit del fix
            commit_message = f'hotfix: {fix_description}'
            result = self._execute_git_command(repo_path, ['add', '-A'])
            if result['success']:
                result = self._execute_git_command(repo_path, ['commit', '-m', commit_message])
                if result['success']:
                    workflow_steps.append(f'Commit del hotfix: {commit_message}')
            
            return {
                'success': True,
                'workflow_type': 'hotfix',
                'hotfix_branch': hotfix_branch,
                'fix_description': fix_description,
                'steps': workflow_steps,
                'instructions': [
                    'Realiza los cambios necesarios para el hotfix',
                    'Ejecuta tests exhaustivos',
                    'Haz commit con mensaje descriptivo',
                    f'Haz push: git push -u origin {hotfix_branch}',
                    'Crea Pull Request dirigido a producción',
                    'Merge después de revisión y tests'
                ]
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_merge_workflow(self, repo_path: str, source_branch: str, 
                             target_branch: str, merge_strategy: MergeStrategy = MergeStrategy.MERGE) -> Dict[str, Any]:
        """Crear workflow completo para merges"""
        try:
            workflow_steps = []
            
            # 1. Cambiar a target branch
            repo = Repo(repo_path)
            repo.git.checkout(target_branch)
            workflow_steps.append(f'Cambiado a target branch: {target_branch}')
            
            # 2. Actualizar target branch
            result = self._execute_git_command(repo_path, ['pull', 'origin', target_branch])
            if result['success']:
                workflow_steps.append(f'Obtenidos últimos cambios de {target_branch}')
            
            # 3. Determinar estrategia de merge
            if merge_strategy == MergeStrategy.MERGE:
                result = self._execute_git_command(repo_path, ['merge', source_branch])
                strategy_msg = 'merge'
            elif merge_strategy == MergeStrategy.REBASE:
                result = self._execute_git_command(repo_path, ['rebase', source_branch])
                strategy_msg = 'rebase'
            elif merge_strategy == MergeStrategy.SQUASH:
                result = self._execute_git_command(repo_path, ['merge', '--squash', source_branch])
                if result['success']:
                    result = self._execute_git_command(repo_path, ['commit', '-m', f'Squashed commits from {source_branch}'])
                strategy_msg = 'squash'
            
            if result['success']:
                workflow_steps.append(f'{strategy_msg.capitalize()} completado exitosamente')
                
                # 4. Push si no hay conflictos
                result = self._execute_git_command(repo_path, ['push', 'origin', target_branch])
                if result['success']:
                    workflow_steps.append('Cambios enviados a origin')
                
                return {
                    'success': True,
                    'workflow_type': 'merge',
                    'source_branch': source_branch,
                    'target_branch': target_branch,
                    'strategy': merge_strategy.value,
                    'steps': workflow_steps,
                    'merge_successful': True
                }
            else:
                # Merge conflictos detectados
                workflow_steps.append(f'Conflicto detectado durante {strategy_msg}')
                
                # Detectar archivos con conflictos
                result = self._execute_git_command(repo_path, ['diff', '--name-only', '--diff-filter=U'])
                conflict_files = result['stdout'].strip().split('\n') if result['success'] else []
                
                return {
                    'success': False,
                    'workflow_type': 'merge',
                    'source_branch': source_branch,
                    'target_branch': target_branch,
                    'strategy': merge_strategy.value,
                    'steps': workflow_steps,
                    'conflict_detected': True,
                    'conflict_files': conflict_files,
                    'resolution_instructions': [
                        'Resuelve los conflictos en los archivos listados',
                        'Ejecuta tests para verificar que todo funciona',
                        'Haz git add en los archivos resueltos',
                        'Continúa el merge:',
                        '  - Para merge: git commit',
                        '  - Para rebase: git rebase --continue',
                        f'Haz push: git push origin {target_branch}'
                    ]
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_repository_health(self, repo_path: str) -> Dict[str, Any]:
        """Analizar la salud general del repositorio"""
        try:
            repo = Repo(repo_path)
            health_report = {
                'overall_health': 'good',
                'issues': [],
                'recommendations': [],
                'statistics': {},
                'last_analysis': datetime.now().isoformat()
            }
            
            # 1. Verificar estructura básica
            if not os.path.exists(os.path.join(repo_path, '.gitignore')):
                health_report['issues'].append('Falta archivo .gitignore')
                health_report['recommendations'].append('Crear archivo .gitignore para excluir archivos innecesarios')
            
            # 2. Verificar README
            readme_files = ['README.md', 'README.md', 'README.txt', 'README']
            has_readme = any(os.path.exists(os.path.join(repo_path, f)) for f in readme_files)
            if not has_readme:
                health_report['issues'].append('Falta archivo README')
                health_report['recommendations'].append('Crear README con descripción del proyecto')
            
            # 3. Verificar estado de working directory
            if repo.is_dirty():
                health_report['issues'].append('Working directory tiene cambios no comprometidos')
                health_report['recommendations'].append('Hacer commit de cambios pendientes o discard')
            
            # 4. Verificar branches
            local_branches = [b.name for b in repo.branches]
            if len(local_branches) > 10:
                health_report['issues'].append('Demasiadas branches locales')
                health_report['recommendations'].append('Limpiar branches que ya no son necesarias')
            
            # 5. Verificar commits recientes
            try:
                recent_commits = list(repo.iter_commits(max_count=10))
                if not recent_commits:
                    health_report['issues'].append('No hay commits recientes')
                    health_report['recommendations'].append('Considerar hacer commits más frecuentemente')
            except GitError:
                health_report['issues'].append('Error accediendo al historial de commits')
            
            # 6. Verificar tamaño del repositorio
            repo_size = self._get_directory_size(repo_path)
            health_report['statistics']['size_mb'] = round(repo_size / (1024 * 1024), 2)
            
            if repo_size > 100 * 1024 * 1024:  # 100MB
                health_report['issues'].append('Repositorio muy grande (>100MB)')
                health_report['recommendations'].append('Considerar usar Git LFS para archivos grandes')
            
            # 7. Verificar configuración de remotes
            remotes = {r.name: r.url for r in repo.remotes}
            if 'origin' not in remotes:
                health_report['issues'].append('No hay remote "origin" configurado')
                health_report['recommendations'].append('Configurar remote origin para backup y colaboración')
            
            # 8. VerificarCI/CD
            ci_cd_analysis = self.analyze_ci_cd_pipeline(repo_path)
            if ci_cd_analysis['success'] and ci_cd_analysis['analysis']['has_ci_cd']:
                health_report['statistics']['has_ci_cd'] = True
            else:
                health_report['recommendations'].append('Considerar configurar CI/CD pipeline')
            
            # Determinar salud general
            if len(health_report['issues']) == 0:
                health_report['overall_health'] = 'excellent'
            elif len(health_report['issues']) <= 2:
                health_report['overall_health'] = 'good'
            elif len(health_report['issues']) <= 4:
                health_report['overall_health'] = 'fair'
            else:
                health_report['overall_health'] = 'poor'
            
            return {
                'success': True,
                'health_report': health_report
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_directory_size(self, directory_path: str) -> int:
        """Calcular tamaño total del directorio"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception:
            pass
        return total_size


# ========== MCP TOOL FUNCTIONS ==========

def create_git_operations_agent():
    """Crear instancia del agente de operaciones Git"""
    return GitOperationsAgent()


# Funciones para herramientas MCP
async def mcp_clone_repository(url: str, path: str, branch: Optional[str] = None, 
                              depth: Optional[int] = None, bare: bool = False):
    """Clonar un repositorio Git"""
    async with GitOperationsAgent() as agent:
        return agent.clone_repository(url, path, branch, depth, bare)


async def mcp_pull_changes(repo_path: str, remote: str = 'origin', branch: Optional[str] = None):
    """Obtener cambios del repositorio remoto"""
    async with GitOperationsAgent() as agent:
        return agent.pull_changes(repo_path, remote, branch)


async def mcp_push_changes(repo_path: str, remote: str = 'origin', 
                         branch: Optional[str] = None, force: bool = False):
    """Enviar cambios al repositorio remoto"""
    async with GitOperationsAgent() as agent:
        return agent.push_changes(repo_path, remote, branch, force)


async def mcp_get_repository_info(repo_path: str):
    """Obtener información completa del repositorio"""
    async with GitOperationsAgent() as agent:
        return agent.get_repository_info(repo_path)


async def mcp_create_branch(repo_path: str, branch_name: str, from_branch: Optional[str] = None):
    """Crear una nueva branch"""
    async with GitOperationsAgent() as agent:
        return agent.create_branch(repo_path, branch_name, from_branch)


async def mcp_delete_branch(repo_path: str, branch_name: str, 
                          force: bool = False, remote: Optional[str] = None):
    """Eliminar una branch"""
    async with GitOperationsAgent() as agent:
        return agent.delete_branch(repo_path, branch_name, force, remote)


async def mcp_switch_branch(repo_path: str, branch_name: str):
    """Cambiar a una branch"""
    async with GitOperationsAgent() as agent:
        return agent.switch_branch(repo_path, branch_name)


async def mcp_merge_branch(repo_path: str, source_branch: str, 
                         strategy: str = 'merge', no_ff: bool = False, message: Optional[str] = None):
    """Hacer merge de una branch"""
    async with GitOperationsAgent() as agent:
        merge_strategy = MergeStrategy(strategy)
        return agent.merge_branch(repo_path, source_branch, merge_strategy, no_ff, message)


async def mcp_detect_conflicts(repo_path: str):
    """Detectar conflictos en el repositorio"""
    async with GitOperationsAgent() as agent:
        return agent.detect_conflicts(repo_path)


async def mcp_get_commit_history(repo_path: str, since: Optional[str] = None, 
                                until: Optional[str] = None, author: Optional[str] = None):
    """Obtener historial de commits"""
    async with GitOperationsAgent() as agent:
        return agent.get_commit_history(repo_path, since, until, author)


async def mcp_get_diff(repo_path: str, from_commit: Optional[str] = None, 
                     to_commit: Optional[str] = None, file_path: Optional[str] = None):
    """Obtener diff entre commits o estado actual"""
    async with GitOperationsAgent() as agent:
        return agent.get_diff(repo_path, from_commit, to_commit, file_path)


async def mcp_create_pull_request_github(repo_owner: str, repo_name: str, title: str, 
                                       body: str, head: str, base: str, draft: bool = False):
    """Crear Pull Request en GitHub"""
    async with GitOperationsAgent() as agent:
        return await agent.create_pull_request_github(repo_owner, repo_name, title, body, head, base, draft)


async def mcp_run_tests(repo_path: str, test_command: str = 'python -m pytest'):
    """Ejecutar tests automatizados"""
    async with GitOperationsAgent() as agent:
        return agent.run_tests(repo_path, test_command)


async def mcp_analyze_repository_health(repo_path: str):
    """Analizar la salud general del repositorio"""
    async with GitOperationsAgent() as agent:
        return agent.analyze_repository_health(repo_path)


async def mcp_create_feature_branch_workflow(repo_path: str, feature_name: str, base_branch: str = 'main'):
    """Crear workflow completo para desarrollo de features"""
    async with GitOperationsAgent() as agent:
        return agent.create_feature_branch_workflow(repo_path, feature_name, base_branch)


if __name__ == "__main__":
    # Función de prueba básica
    async def test_agent():
        """Función de prueba para el agente"""
        print("Iniciando pruebas del Git Operations Agent...")
        
        # Crear directorio temporal para pruebas
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = os.path.join(temp_dir, 'test_repo')
            
            # Simular un repositorio Git para pruebas
            os.makedirs(repo_path)
            repo = Repo.init(repo_path)
            
            # Crear archivo de prueba
            test_file = os.path.join(repo_path, 'test.txt')
            with open(test_file, 'w') as f:
                f.write('Archivo de prueba')
            
            # Agregar archivo y hacer commit
            repo.index.add(['test.txt'])
            repo.index.commit('Commit inicial de prueba')
            
            async with GitOperationsAgent() as agent:
                # Probar obtener información del repositorio
                result = agent.get_repository_info(repo_path)
                print(f"Información del repositorio: {result}")
                
                # Probar crear branch
                result = agent.create_branch(repo_path, 'test-branch')
                print(f"Crear branch: {result}")
                
                # Probar análisis de salud
                result = agent.analyze_repository_health(repo_path)
                print(f"Análisis de salud: {result}")
                
                print("Pruebas completadas!")
    
    # Ejecutar pruebas
    asyncio.run(test_agent())

class GitOperationsAgentWrapper(BaseAgentWrapper):
    """
    Wrapper MCP para GitOperationsAgent
    
    Proporciona capacidades de gestión de repositorios Git:
    - Operaciones básicas de Git (commit, push, pull, merge)
    - Gestión de branches y tags
    - Resolución de conflictos
    - Integración con GitHub/GitLab APIs
    - Análisis de salud del repositorio
    - CI/CD y workflows
    """
    
    def __init__(self):
        capabilities = [
            AgentCapability.TOOL_INVOCATION,
            AgentCapability.CONCURRENT_EXECUTION
        ]
        
        super().__init__(
            agent_name="git_operations",
            capabilities=capabilities,
            max_concurrent=get_safe_settings().max_concurrent_tools,
            timeout_seconds=get_safe_settings().agent_timeout_seconds,
            retry_attempts=get_safe_settings().agent_retry_attempts,
            retry_delay=get_safe_settings().agent_retry_delay
        )
        
        self.logger = logging.getLogger("mcp.agents.git_operations")
        self._session = None
    
    async def _initialize(self) -> None:
        """Inicialización específica del GitOperationsAgent"""
        self.logger.info("Inicializando GitOperationsAgent...")
        
        # Aquí se conectaría con el GitOperationsAgent real
        # Por ahora simulamos la inicialización
        await asyncio.sleep(0.1)
        
        self.logger.info("GitOperationsAgent inicializado correctamente")
    
    async def process_request(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Procesar request de operaciones Git
        
        Args:
            request: Request del cliente
                - operation: Operación a realizar (get_info, create_branch, merge, etc.)
                - repo_path: Ruta al repositorio
                - params: Parámetros específicos de la operación
            context: Contexto adicional
            
        Returns:
            Resultado de la operación Git
        """
        return await self.execute_operation(
            operation_name="git_operation",
            capability=AgentCapability.TOOL_INVOCATION,
            operation_func=self._execute_git_operation,
            request=request,
            context=context
        )
    
    @handle_exceptions
    async def _execute_git_operation(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ejecutar operación Git específica"""
        
        operation = request.get("operation")
        repo_path = request.get("repo_path")
        params = request.get("params", {})
        
        if not operation:
            raise AgentException(
                "Operación es requerida para Git operations",
                self.agent_name,
                "execute_git_operation"
            )
        
        self.logger.info(f"Ejecutando operación Git: {operation}")
        
        # Aquí se conectaría con el GitOperationsAgent real
        # Por ahora simulamos la ejecución
        
        # Simular tiempo de procesamiento
        await asyncio.sleep(0.1)
        
        # Simulación de resultados según operación
        operation_results = {
            "get_repository_info": self._simulate_get_info(repo_path, params),
            "create_branch": self._simulate_create_branch(repo_path, params),
            "merge_branch": self._simulate_merge_branch(repo_path, params),
            "get_commit_history": self._simulate_get_history(repo_path, params),
            "detect_conflicts": self._simulate_detect_conflicts(repo_path, params),
            "analyze_health": self._simulate_analyze_health(repo_path, params)
        }
        
        if operation not in operation_results:
            raise AgentException(
                f"Operación Git no soportada: {operation}",
                self.agent_name,
                "execute_git_operation"
            )
        
        result = operation_results[operation]
        
        self.logger.info(f"Operación Git completada: {operation}")
        
        return {
            "operation": operation,
            "repo_path": repo_path,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    def _simulate_get_info(self, repo_path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simular obtención de información del repositorio"""
        return {
            "path": repo_path,
            "url": "https://github.com/example/repo.git",
            "provider": "github",
            "default_branch": "main",
            "current_branch": "main",
            "last_commit": "abc123",
            "commit_count": 100
        }
    
    def _simulate_create_branch(self, repo_path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simular creación de branch"""
        branch_name = params.get("branch_name", "new-branch")
        from_branch = params.get("from_branch", "main")
        
        return {
            "branch_name": branch_name,
            "from_branch": from_branch,
            "created": True,
            "switched_to": True
        }
    
    def _simulate_merge_branch(self, repo_path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simular merge de branch"""
        source_branch = params.get("source_branch")
        strategy = params.get("strategy", "merge")
        
        return {
            "source_branch": source_branch,
            "strategy": strategy,
            "merged": True,
            "conflicts": 0
        }
    
    def _simulate_get_history(self, repo_path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simular obtención de historial"""
        return {
            "commits": [
                {
                    "hash": "abc123",
                    "message": "Initial commit",
                    "author": "Developer",
                    "date": "2024-01-01T00:00:00Z"
                }
            ],
            "total": 1
        }
    
    def _simulate_detect_conflicts(self, repo_path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simular detección de conflictos"""
        return {
            "conflicts_found": 0,
            "conflicts": []
        }
    
    def _simulate_analyze_health(self, repo_path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simular análisis de salud"""
        return {
            "overall_health": "good",
            "issues": [],
            "recommendations": [
                "Repo healthy"
            ]
        }
    
    # Métodos específicos de la interfaz MCP
    
    async def get_repository_info(self, repo_path: str) -> Dict[str, Any]:
        """Obtener información completa del repositorio"""
        request = {
            "operation": "get_repository_info",
            "repo_path": repo_path
        }
        return await self.process_request(request)
    
    async def create_branch(self, repo_path: str, branch_name: str, from_branch: Optional[str] = None) -> Dict[str, Any]:
        """Crear una nueva branch"""
        request = {
            "operation": "create_branch",
            "repo_path": repo_path,
            "params": {
                "branch_name": branch_name,
                "from_branch": from_branch
            }
        }
        return await self.process_request(request)
    
    async def merge_branch(self, repo_path: str, source_branch: str, strategy: str = "merge") -> Dict[str, Any]:
        """Hacer merge de una branch"""
        request = {
            "operation": "merge_branch",
            "repo_path": repo_path,
            "params": {
                "source_branch": source_branch,
                "strategy": strategy
            }
        }
        return await self.process_request(request)
    
    async def get_commit_history(self, repo_path: str, since: Optional[str] = None, 
                               until: Optional[str] = None, author: Optional[str] = None) -> Dict[str, Any]:
        """Obtener historial de commits"""
        request = {
            "operation": "get_commit_history",
            "repo_path": repo_path,
            "params": {
                "since": since,
                "until": until,
                "author": author
            }
        }
        return await self.process_request(request)
    
    async def detect_conflicts(self, repo_path: str) -> Dict[str, Any]:
        """Detectar conflictos en el repositorio"""
        request = {
            "operation": "detect_conflicts",
            "repo_path": repo_path
        }
        return await self.process_request(request)
    
    async def analyze_repository_health(self, repo_path: str) -> Dict[str, Any]:
        """Análisis completo de salud del repositorio"""
        request = {
            "operation": "analyze_health",
            "repo_path": repo_path
        }
        return await self.process_request(request)
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check del GitOperationsAgent"""
        try:
            await self.ensure_initialized()
            
            return {
                "agent_name": self.agent_name,
                "status": "healthy",
                "git_operations_available": True,
                "repository_access": "ready",
                "api_tokens_configured": bool(
                    os.getenv('GITHUB_TOKEN') or 
                    os.getenv('GITLAB_TOKEN') or
                    os.getenv('BITBUCKET_USERNAME')
                )
            }
        except Exception as e:
            return {
                "agent_name": self.agent_name,
                "status": "unhealthy",
                "error": str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado del GitOperationsAgent"""
        base_status = super().get_status()
        base_status.update({
            "agent_type": "git_operations",
            "specialization": "Operaciones avanzadas de Git y gestión de repositorios",
            "git_executable_available": self._check_git_availability(),
            "provider_tokens": {
                "github": bool(os.getenv('GITHUB_TOKEN')),
                "gitlab": bool(os.getenv('GITLAB_TOKEN')),
                "bitbucket": bool(os.getenv('BITBUCKET_USERNAME'))
            }
        })
        return base_status
    
    def _check_git_availability(self) -> bool:
        """Verificar si Git está disponible en el sistema"""
        try:
            subprocess.run(['git', '--version'], 
                          capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


# Función helper para crear instancia
def create_git_operations_agent_wrapper() -> GitOperationsAgentWrapper:
    """Crear instancia del wrapper GitOperations"""
    return GitOperationsAgentWrapper()
