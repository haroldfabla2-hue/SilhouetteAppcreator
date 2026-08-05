"""Proyectos: carpetas locales, ramas y espacios de trabajo aislados."""
from backend.app.projects.registry import Project, ProjectError, project_registry
from backend.app.projects.workspaces import (
    Workspace,
    WorkspaceError,
    workspace_manager,
)

__all__ = [
    "Project",
    "ProjectError",
    "Workspace",
    "WorkspaceError",
    "project_registry",
    "workspace_manager",
]
