import os
import subprocess
import docker
from typing import Iterator

class HybridSandboxManager:
    """
    Component 1 of Enterprise Architecture: A Hybrid Sandbox using Git Worktrees and Docker.
    """
    def __init__(self, repo_path: str = "."):
        self.repo_path = os.path.abspath(repo_path)
        self.docker_client = docker.from_env()

    def create_sandbox(self, branch_name: str, task_id: str) -> str:
        """
        Creates a new git worktree for a specific task.
        """
        worktree_path = os.path.join(self.repo_path, ".worktrees", task_id)
        
        subprocess.run(
            ["git", "worktree", "add", "-b", branch_name, worktree_path],
            cwd=self.repo_path,
            check=True
        )
        return worktree_path

    def execute_in_sandbox(self, worktree_path: str, command: str) -> Iterator[bytes]:
        """
        Executes a command inside a Docker container with the worktree mounted.
        Dynamically mounts CLI authentication paths if they exist to allow
        the container to use CLI LLM providers.
        """
        volumes = {
            os.path.abspath(worktree_path): {
                'bind': '/workspace',
                'mode': 'rw'
            }
        }
        
        # Mount host CLI configs for AI authentication
        home_dir = os.path.expanduser("~")
        for cli_path in [".config", ".claude", ".gemini", ".codex"]:
            host_path = os.path.join(home_dir, cli_path)
            if os.path.exists(host_path):
                volumes[host_path] = {
                    'bind': f'/root/{cli_path}',
                    'mode': 'ro'
                }
                
        container = self.docker_client.containers.run(
            image="python:3.10-slim",
            command=command,
            volumes=volumes,
            working_dir="/workspace",
            mem_limit='1g',
            detach=True,
            auto_remove=True
        )
        
        return container.logs(stream=True)

    def cleanup_sandbox(self, worktree_path: str, branch_name: str):
        """
        Removes the git worktree and deletes the corresponding branch.
        """
        subprocess.run(
            ["git", "worktree", "remove", "--force", worktree_path],
            cwd=self.repo_path,
            check=True
        )
        
        subprocess.run(
            ["git", "branch", "-D", branch_name],
            cwd=self.repo_path,
            check=True
        )
