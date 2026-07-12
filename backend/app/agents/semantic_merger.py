import subprocess
import os
import re
import asyncio
import ast
from typing import List
from backend.app.core.llm_router import LLMRouter

class SemanticMerger:
    def __init__(self, llm_router: LLMRouter):
        """
        Initializes the SemanticMerger with an LLMRouter instance.
        """
        self.llm_router = llm_router

    async def merge_and_resolve(self, target_branch: str, source_branch: str) -> None:
        """
        Merges source_branch into target_branch. If conflicts occur,
        uses the LLMRouter to logically resolve them.
        """
        # Ensure we are on the target branch
        subprocess.run(["git", "checkout", target_branch], check=True, capture_output=True)
        
        # 1. Run git merge --no-commit <source_branch> via subprocess
        result = subprocess.run(
            ["git", "merge", "--no-commit", source_branch],
            capture_output=True,
            text=True
        )

        # 2. If the merge fails due to conflicts (exit code != 0)
        if result.returncode != 0:
            print("Merge conflicts detected. Resolving with AI...")
            success = await self._resolve_conflicts()
            if not success:
                print("Merge resolution failed syntax validation. Aborting merge.")
                subprocess.run(["git", "merge", "--abort"], capture_output=True)
                return
        else:
            print("Merge successful without conflicts.")

        # 5. Run git add (handled in _resolve_conflicts for conflicted files, but let's add all)
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        
        # Run git commit
        commit_msg = "Semantic merge resolved by AI"
        subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True)
        print(f"Committed merge: {commit_msg}")

    async def _resolve_conflicts(self) -> bool:
        # Get list of conflicted files
        status_result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=U"],
            capture_output=True,
            text=True,
            check=True
        )
        conflicted_files = [f for f in status_result.stdout.strip().split('\n') if f]

        for file_path in conflicted_files:
            if not os.path.exists(file_path):
                continue
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Read the conflicted files, extract the conflict blocks, and resolve
            resolved_content = await self._resolve_file_content(file_path, content)
            
            # Syntax verification for Python files
            if file_path.endswith('.py'):
                try:
                    ast.parse(resolved_content)
                except SyntaxError as e:
                    print(f"Syntax error in resolved AI code for {file_path}: {e}")
                    return False

            # 4. Write the AI's response back to the file, removing the conflict markers.
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(resolved_content)

            # 5. Run git add for the resolved file
            subprocess.run(["git", "add", file_path], check=True)
            
        return True

    async def _resolve_file_content(self, file_path: str, content: str) -> str:
        # Match conflict blocks (<<<<<<< ... ======= ... >>>>>>> ...)
        conflict_pattern = re.compile(
            r'<<<<<<< [^\n]*\n(.*?)\n=======\n(.*?)\n>>>>>>>[^\n]*\n?',
            re.DOTALL
        )
        
        # Find all conflict blocks
        conflicts = list(conflict_pattern.finditer(content))
        if not conflicts:
            return content
            
        resolved_blocks = []
        for match in conflicts:
            head_content = match.group(1)
            incoming_content = match.group(2)
            
            # 3. Construct a prompt for the LLMRouter
            prompt = (
                f"You are an AI assistant resolving a git merge conflict in the file '{file_path}'.\n"
                f"Please logically resolve the conflict between the following two blocks of code.\n"
                f"Output ONLY the resolved code without any explanation, markdown formatting, or conflict markers.\n\n"
                f"=== HEAD (Current Branch) ===\n{head_content}\n\n"
                f"=== INCOMING (Source Branch) ===\n{incoming_content}\n"
            )
            
            try:
                # Proper async call to LLMRouter
                resolved = await self.llm_router.chat_completion(prompt=prompt, enable_fallback=True)
                
                resolved = resolved.strip()
                if resolved.startswith('```'):
                    resolved = '\n'.join(resolved.split('\n')[1:])
                if resolved.endswith('```'):
                    resolved = '\n'.join(resolved.split('\n')[:-1])
                    
                resolved_blocks.append(resolved.strip() + '\n')
            except Exception as e:
                print(f"Error calling LLM for {file_path}: {e}")
                # Fallback to HEAD
                resolved_blocks.append(head_content + '\n')

        # Reconstruct the file with resolved blocks
        result_content = content
        for i, match in enumerate(reversed(conflicts)):
            start, end = match.span()
            result_content = result_content[:start] + resolved_blocks[-(i+1)] + result_content[end:]
            
        return result_content
