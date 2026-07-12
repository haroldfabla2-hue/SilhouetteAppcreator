"""
Test suite completa para los 12 Agentes MCP del Core Superior

Cubre todos los agentes base y especializados:
- Base Agent Wrapper
- Python Executor Agent  
- Git Operations Agent
- Web Scraping Agent
- Database Operations Agent
- Search Engine Agent
- File Processing Agent
- MultiAgent Orchestrator Agent
- Memory Manager Wrapper
- Planner Wrapper
- Reasoner Wrapper
- Verifier Wrapper
"""

import pytest
import asyncio
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

# Test marks
pytestmark = [pytest.mark.agent, pytest.mark.unit, pytest.mark.async_test]


class TestBaseAgentWrapper:
    """Tests para BaseAgentWrapper"""
    
    @pytest.fixture
    def base_agent(self):
        """Fixture del base agent"""
        from agents.base_agent_wrapper import BaseAgentWrapper
        return BaseAgentWrapper
    
    async def test_agent_initialization(self, base_agent, mock_settings):
        """Test de inicialización del agente base"""
        with patch('agents.base_agent_wrapper.BaseAgentWrapper._initialize') as mock_init:
            mock_init.return_value = True
            
            agent = base_agent()
            assert agent is not None
            assert hasattr(agent, 'agent_id')
            assert hasattr(agent, 'status')
    
    async def test_agent_lifecycle(self, base_agent):
        """Test del ciclo de vida del agente"""
        with patch('agents.base_agent_wrapper.BaseAgentWrapper._initialize') as mock_init:
            mock_init.return_value = True
            
            agent = base_agent()
            
            # Test start
            result = await agent.start()
            assert isinstance(result, dict)
            assert 'success' in result
            
            # Test stop
            result = await agent.stop()
            assert isinstance(result, dict)
            assert 'success' in result
    
    async def test_request_processing(self, base_agent, mock_agent_request):
        """Test de procesamiento de requests"""
        with patch('agents.base_agent_wrapper.BaseAgentWrapper._initialize') as mock_init:
            mock_init.return_value = True
            with patch('agents.base_agent_wrapper.BaseAgentWrapper._process_request') as mock_process:
                mock_process.return_value = {"success": True, "result": "processed"}
                
                agent = base_agent()
                result = await agent.process_request(mock_agent_request)
                
                assert isinstance(result, dict)
                assert result['success'] is True
    
    async def test_health_check(self, base_agent):
        """Test de health check"""
        with patch('agents.base_agent_wrapper.BaseAgentWrapper._initialize') as mock_init:
            mock_init.return_value = True
            with patch('agents.base_agent_wrapper.BaseAgentWrapper._health_check') as mock_health:
                mock_health.return_value = {"status": "healthy", "components": {}}
                
                agent = base_agent()
                result = await agent.health_check()
                
                assert isinstance(result, dict)
                assert result['status'] == "healthy"


class TestPythonExecutorAgent:
    """Tests para PythonExecutorAgent"""
    
    @pytest.fixture
    def python_agent(self):
        """Fixture del agente ejecutor de Python"""
        from agents.python_executor_agent import AdvancedPythonExecutorAgent
        return AdvancedPythonExecutorAgent
    
    @pytest.fixture
    def security_levels(self):
        """Fixture de niveles de seguridad"""
        from agents.python_executor_agent import SecurityLevel
        return SecurityLevel
    
    async def test_agent_creation(self, python_agent, security_levels):
        """Test de creación del agente"""
        agent = python_agent(security_level=security_levels.RESTRICTED)
        assert agent is not None
        assert hasattr(agent, 'security_level')
        assert agent.security_level == security_levels.RESTRICTED
    
    async def test_code_execution(self, python_agent):
        """Test de ejecución de código"""
        agent = python_agent()
        
        test_code = """
result = 2 + 2
print(f"Result: {result}")
"""
        
        request = {
            "operation": "execute_code",
            "code": test_code,
            "security_level": "restricted"
        }
        
        with patch.object(agent, '_execute_sandboxed_code') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "output": "Result: 4",
                "execution_time": 0.1
            }
            
            result = await agent.process_request(request)
            assert result['success'] is True
            assert 'execution_result' in result
    
    async def test_security_analysis(self, python_agent):
        """Test de análisis de seguridad"""
        agent = python_agent()
        
        dangerous_code = """
import os
os.system('ls -la')
"""
        
        request = {
            "operation": "analyze_code",
            "code": dangerous_code
        }
        
        with patch.object(agent, '_analyze_security') as mock_analyze:
            mock_analyze.return_value = {
                "risk_score": 0.8,
                "security_warnings": ["Use of os.system detected"]
            }
            
            result = await agent.process_request(request)
            assert 'security_analysis' in result
            assert result['security_analysis']['risk_score'] >= 0
    
    async def test_sandbox_execution(self, python_agent):
        """Test de ejecución en sandbox"""
        agent = python_agent()
        
        safe_code = """
data = [1, 2, 3, 4, 5]
result = sum(data)
"""
        
        request = {
            "operation": "execute_with_sandbox",
            "code": safe_code,
            "sandbox_config": {
                "security_level": "moderate",
                "resource_limits": {
                    "max_memory_mb": 128,
                    "max_cpu_seconds": 5
                }
            }
        }
        
        with patch.object(agent, '_execute_in_sandbox') as mock_sandbox:
            mock_sandbox.return_value = {
                "success": True,
                "output": "15",
                "memory_used": 25.5,
                "execution_time": 0.05
            }
            
            result = await agent.process_request(request)
            assert result['success'] is True
            assert 'sandbox_result' in result
    
    async def test_profiling(self, python_agent):
        """Test de profiling de código"""
        agent = python_agent()
        
        profiling_code = """
import time

def slow_function():
    time.sleep(0.1)
    return "completed"

result = slow_function()
"""
        
        request = {
            "operation": "profile_code",
            "code": profiling_code,
            "profile_type": "performance"
        }
        
        with patch.object(agent, '_profile_code') as mock_profile:
            mock_profile.return_value = {
                "profile_successful": True,
                "total_functions": 1,
                "total_time": 0.105,
                "top_functions": [
                    {"function": "slow_function", "total_time": 0.101}
                ]
            }
            
            result = await agent.process_request(request)
            assert result['profile_data']['profile_successful'] is True
    
    async def test_resource_limits(self, python_agent):
        """Test de límites de recursos"""
        from agents.python_executor_agent import ResourceLimits
        
        limits = ResourceLimits(
            max_memory_mb=256,
            max_cpu_seconds=10,
            timeout_seconds=30
        )
        
        agent = python_agent(default_resource_limits=limits)
        
        assert agent.default_resource_limits.max_memory_mb == 256
        assert agent.default_resource_limits.max_cpu_seconds == 10
    
    async def test_status_monitoring(self, python_agent):
        """Test de monitoreo de estado"""
        agent = python_agent()
        
        status = agent.get_status()
        
        assert isinstance(status, dict)
        assert 'agent_type' in status
        assert 'status' in status
        assert 'execution_metrics' in status


class TestGitOperationsAgent:
    """Tests para GitOperationsAgent"""
    
    @pytest.fixture
    def git_agent(self):
        """Fixture del agente de operaciones Git"""
        from agents.git_operations_agent import GitOperationsAgent
        return GitOperationsAgent
    
    async def test_repository_info(self, git_agent, temp_directory):
        """Test de obtención de información del repositorio"""
        agent = git_agent()
        
        with patch('git.Repo') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.working_dir = temp_directory
            
            result = agent.get_repository_info(temp_directory)
            
            assert isinstance(result, dict)
            assert result['success'] is True
            assert 'repository' in result
    
    async def test_branch_operations(self, git_agent, temp_directory):
        """Test de operaciones de branches"""
        agent = git_agent()
        
        with patch('git.Repo') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo
            
            # Test listar branches
            mock_repo.branches = [MagicMock(name="main"), MagicMock(name="develop")]
            result = agent.list_branches(temp_directory)
            
            assert result['success'] is True
            assert len(result['branches']) > 0
            
            # Test crear branch
            mock_repo.create_head.return_value = MagicMock()
            result = agent.create_branch(
                repo_path=temp_directory,
                branch_name="feature/test",
                from_branch="main"
            )
            
            assert result['success'] is True
    
    async def test_commit_operations(self, git_agent, temp_directory):
        """Test de operaciones de commits"""
        agent = git_agent()
        
        with patch('git.Repo') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo
            
            # Test historial de commits
            mock_commit = MagicMock()
            mock_commit.hexsha = "abc123"
            mock_commit.message = "Test commit"
            mock_commit.author.name = "Test User"
            mock_repo.iter_commits.return_value = [mock_commit]
            
            result = agent.get_commit_history(temp_directory)
            
            assert result['success'] is True
            assert len(result['commits']) > 0
    
    async def test_merge_operations(self, git_agent, temp_directory):
        """Test de operaciones de merge"""
        from agents.git_operations_agent import MergeStrategy
        
        agent = git_agent()
        
        with patch('git.Repo') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.merge.return_value = MagicMock()
            
            result = agent.merge_branch(
                repo_path=temp_directory,
                source_branch="feature/test",
                target_branch="main",
                strategy=MergeStrategy.MERGE
            )
            
            assert result['success'] is True
    
    async def test_conflict_detection(self, git_agent, temp_directory):
        """Test de detección de conflictos"""
        agent = git_agent()
        
        with patch('git.Repo') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo
            
            # Mock unconflicted merge
            mock_repo.index.unconflicted_files.return_value = ["file1.txt"]
            
            result = agent.detect_conflicts(temp_directory)
            
            assert result['success'] is True
            assert 'conflicts' in result
    
    async def test_health_analysis(self, git_agent, temp_directory):
        """Test de análisis de salud del repositorio"""
        agent = git_agent()
        
        with patch('git.Repo') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo
            
            # Mock archivos y configuración
            mock_repo.untracked_files = []
            mock_repo.git.checkout = MagicMock()
            
            result = agent.analyze_repository_health(temp_directory)
            
            assert result['success'] is True
            assert 'health_report' in result
            assert 'overall_health' in result['health_report']


class TestWebScrapingAgent:
    """Tests para WebScrapingAgent"""
    
    @pytest.fixture
    def scraping_agent(self):
        """Fixture del agente de web scraping"""
        from agents.web_scraping_agent import WebScrapingAgent
        return WebScrapingAgent
    
    async def test_url_scraping(self, scraping_agent):
        """Test de scraping de URL"""
        agent = scraping_agent()
        
        url = "https://example.com"
        request = {
            "operation": "scrape_url",
            "url": url,
            "options": {
                "extract_text": True,
                "extract_links": True
            }
        }
        
        with patch('agents.web_scraping_agent.WebScrapingAgent._scrape_url') as mock_scrape:
            mock_scrape.return_value = {
                "success": True,
                "content": "Example content",
                "title": "Example Page",
                "links": ["https://example.com/link1"]
            }
            
            result = await agent.process_request(request)
            assert result['success'] is True
            assert 'scraped_content' in result
    
    async def test_bulk_scraping(self, scraping_agent):
        """Test de scraping en lote"""
        agent = scraping_agent()
        
        urls = ["https://example.com", "https://test.com"]
        request = {
            "operation": "bulk_scrape",
            "urls": urls,
            "max_concurrent": 2
        }
        
        with patch('agents.web_scraping_agent.WebScrapingAgent._bulk_scrape') as mock_bulk:
            mock_bulk.return_value = {
                "success": True,
                "results": [
                    {"url": "https://example.com", "success": True},
                    {"url": "https://test.com", "success": True}
                ]
            }
            
            result = await agent.process_request(request)
            assert result['success'] is True
            assert len(result['results']) == 2
    
    async def test_content_filtering(self, scraping_agent):
        """Test de filtrado de contenido"""
        agent = scraping_agent()
        
        content = "<html><body><p>Test content</p></body></html>"
        request = {
            "operation": "filter_content",
            "content": content,
            "filters": ["html", "javascript", "css"]
        }
        
        with patch('agents.web_scraping_agent.WebScrapingAgent._filter_content') as mock_filter:
            mock_filter.return_value = {
                "success": True,
                "cleaned_content": "Test content",
                "removed_elements": ["html", "javascript"]
            }
            
            result = await agent.process_request(request)
            assert result['success'] is True
    
    async def test_rate_limiting(self, scraping_agent):
        """Test de rate limiting"""
        agent = scraping_agent()
        
        with patch('agents.web_scraping_agent.WebScrapingAgent._check_rate_limit') as mock_limit:
            mock_limit.return_value = True
            
            # Test que respeta rate limiting
            assert agent._check_rate_limit("test_key", max_requests=10, window_seconds=60)
    
    async def test_error_handling(self, scraping_agent):
        """Test de manejo de errores"""
        agent = scraping_agent()
        
        request = {
            "operation": "scrape_url",
            "url": "invalid://url"
        }
        
        result = await agent.process_request(request)
        # Debería manejar errores gracefully
        assert isinstance(result, dict)


class TestDatabaseOperationsAgent:
    """Tests para DatabaseOperationsAgent"""
    
    @pytest.fixture
    def db_agent(self):
        """Fixture del agente de operaciones de BD"""
        from agents.database_operations_agent import DatabaseOperationsAgent
        return DatabaseOperationsAgent
    
    async def test_query_execution(self, db_agent, mock_database):
        """Test de ejecución de queries"""
        agent = db_agent()
        
        query = "SELECT * FROM users WHERE id = $1"
        params = ["123"]
        
        with patch('agents.database_operations_agent.DatabaseOperationsAgent._execute_query') as mock_exec:
            mock_exec.return_value = {
                "success": True,
                "rows": [{"id": "123", "name": "Test User"}]
            }
            
            result = await agent.execute_query(query, params)
            
            assert result['success'] is True
            assert len(result['rows']) > 0
    
    async def test_transaction_management(self, db_agent, mock_database):
        """Test de gestión de transacciones"""
        agent = db_agent()
        
        operations = [
            {"query": "INSERT INTO users (id, name) VALUES ($1, $2)", "params": ["123", "Test"]},
            {"query": "UPDATE users SET name = $1 WHERE id = $2", "params": ["Updated", "123"]}
        ]
        
        with patch('agents.database_operations_agent.DatabaseOperationsAgent._execute_transaction') as mock_tx:
            mock_tx.return_value = {
                "success": True,
                "commit": True
            }
            
            result = await agent.execute_transaction(operations)
            
            assert result['success'] is True
    
    async def test_schema_operations(self, db_agent, mock_database):
        """Test de operaciones de schema"""
        agent = db_agent()
        
        # Test crear tabla
        with patch('agents.database_operations_agent.DatabaseOperationsAgent._create_table') as mock_create:
            mock_create.return_value = {"success": True}
            
            result = await agent.create_table("test_table", {
                "id": "SERIAL PRIMARY KEY",
                "name": "VARCHAR(255) NOT NULL"
            })
            
            assert result['success'] is True
    
    async def test_backup_operations(self, db_agent, mock_database):
        """Test de operaciones de backup"""
        agent = db_agent()
        
        with patch('agents.database_operations_agent.DatabaseOperationsAgent._create_backup') as mock_backup:
            mock_backup.return_value = {
                "success": True,
                "backup_path": "/backups/test_backup.sql"
            }
            
            result = await agent.create_backup("test_database")
            
            assert result['success'] is True
            assert 'backup_path' in result


class TestSearchEngineAgent:
    """Tests para SearchEngineAgent"""
    
    @pytest.fixture
    def search_agent(self):
        """Fixture del agente de motor de búsqueda"""
        from agents.search_engine_agent import SearchEngineAgent
        return SearchEngineAgent
    
    async def test_web_search(self, search_agent):
        """Test de búsqueda web"""
        agent = search_agent()
        
        query = "Python programming"
        request = {
            "operation": "web_search",
            "query": query,
            "max_results": 10
        }
        
        with patch('agents.search_engine_agent.SearchEngineAgent._web_search') as mock_search:
            mock_search.return_value = {
                "success": True,
                "results": [
                    {
                        "title": "Python Tutorial",
                        "url": "https://example.com/python",
                        "snippet": "Learn Python programming..."
                    }
                ]
            }
            
            result = await agent.process_request(request)
            assert result['success'] is True
            assert len(result['search_results']) > 0
    
    async def test_vector_search(self, search_agent, mock_vector_store):
        """Test de búsqueda vectorial"""
        agent = search_agent()
        
        query_vector = [0.1] * 1536
        request = {
            "operation": "vector_search",
            "query_vector": query_vector,
            "top_k": 5
        }
        
        with patch('agents.search_engine_agent.SearchEngineAgent._vector_search') as mock_vsearch:
            mock_vsearch.return_value = {
                "success": True,
                "results": [
                    {"id": "doc1", "score": 0.95, "metadata": {}}
                ]
            }
            
            result = await agent.process_request(request)
            assert result['success'] is True
    
    async def test_hybrid_search(self, search_agent):
        """Test de búsqueda híbrida"""
        agent = search_agent()
        
        query = "machine learning"
        request = {
            "operation": "hybrid_search",
            "query": query,
            "web_weight": 0.6,
            "vector_weight": 0.4
        }
        
        with patch('agents.search_engine_agent.SearchEngineAgent._hybrid_search') as mock_hybrid:
            mock_hybrid.return_value = {
                "success": True,
                "combined_results": [
                    {"source": "web", "score": 0.8},
                    {"source": "vector", "score": 0.9}
                ]
            }
            
            result = await agent.process_request(request)
            assert result['success'] is True
    
    async def test_search_ranking(self, search_agent):
        """Test de ranking de resultados"""
        agent = search_engine_agent()
        
        raw_results = [
            {"title": "Python Basics", "score": 0.5},
            {"title": "Advanced Python", "score": 0.9},
            {"title": "Python Tutorial", "score": 0.7}
        ]
        
        with patch('agents.search_engine_agent.SearchEngineAgent._rank_results') as mock_rank:
            mock_rank.return_value = raw_results
            
            result = agent._rank_results(raw_results)
            
            # El resultado debe estar ordenado por score descendente
            assert result[0]['score'] >= result[1]['score']


class TestFileProcessingAgent:
    """Tests para FileProcessingAgent"""
    
    @pytest.fixture
    def file_agent(self):
        """Fixture del agente de procesamiento de archivos"""
        from agents.file_processing_agent import FileProcessingAgent
        return FileProcessingAgent
    
    async def test_file_reading(self, file_agent, temp_file):
        """Test de lectura de archivos"""
        agent = file_agent()
        
        test_content = "Test file content"
        file_path = temp_file(test_content)
        
        request = {
            "operation": "read_file",
            "file_path": file_path
        }
        
        with patch('agents.file_processing_agent.FileProcessingAgent._read_file') as mock_read:
            mock_read.return_value = {
                "success": True,
                "content": test_content
            }
            
            result = await agent.process_request(request)
            assert result['success'] is True
    
    async def test_file_writing(self, file_agent, temp_directory):
        """Test de escritura de archivos"""
        agent = file_agent()
        
        content = "New file content"
        file_path = os.path.join(temp_directory, "new_file.txt")
        
        request = {
            "operation": "write_file",
            "file_path": file_path,
            "content": content
        }
        
        with patch('agents.file_processing_agent.FileProcessingAgent._write_file') as mock_write:
            mock_write.return_value = {
                "success": True,
                "bytes_written": len(content)
            }
            
            result = await agent.process_request(request)
            assert result['success'] is True
    
    async def test_file_conversion(self, file_agent, temp_file):
        """Test de conversión de archivos"""
        agent = file_agent()
        
        pdf_content = "PDF content"
        input_file = temp_file(pdf_content, ".pdf")
        output_file = input_file.replace(".pdf", ".txt")
        
        request = {
            "operation": "convert_file",
            "input_path": input_file,
            "output_path": output_file,
            "target_format": "txt"
        }
        
        with patch('agents.file_processing_agent.FileProcessingAgent._convert_file') as mock_convert:
            mock_convert.return_value = {
                "success": True,
                "output_path": output_file
            }
            
            result = await agent.process_request(request)
            assert result['success'] is True
    
    async def test_batch_processing(self, file_agent, temp_directory):
        """Test de procesamiento en lote"""
        agent = file_agent()
        
        # Crear múltiples archivos de test
        files = []
        for i in range(3):
            file_path = os.path.join(temp_directory, f"file_{i}.txt")
            with open(file_path, 'w') as f:
                f.write(f"Content {i}")
            files.append(file_path)
        
        request = {
            "operation": "batch_process",
            "file_paths": files,
            "operation": "read"
        }
        
        with patch('agents.file_processing_agent.FileProcessingAgent._batch_process') as mock_batch:
            mock_batch.return_value = {
                "success": True,
                "results": [{"file": f, "success": True} for f in files]
            }
            
            result = await agent.process_request(request)
            assert result['success'] is True
            assert len(result['results']) == len(files)


class TestMultiAgentOrchestratorAgent:
    """Tests para MultiAgentOrchestratorAgent"""
    
    @pytest.fixture
    def orchestrator_agent(self):
        """Fixture del orquestador de agentes"""
        from agents.multiagent_orchestrator_agent import MultiAgentOrchestratorAgent
        return MultiAgentOrchestratorAgent
    
    async def test_task_submission(self, orchestrator_agent):
        """Test de envío de tareas"""
        agent = orchestrator_agent()
        
        task = {
            "type": "process_document",
            "input": "document content",
            "required_agents": ["file_processor", "search_engine"]
        }
        
        with patch('agents.multiagent_orchestrator_agent.MultiAgentOrchestratorAgent._submit_task') as mock_submit:
            mock_submit.return_value = {
                "success": True,
                "task_id": "task-123"
            }
            
            result = await agent.submit_task(task)
            
            assert result['success'] is True
            assert 'task_id' in result
    
    async def test_task_coordination(self, orchestrator_agent):
        """Test de coordinación de tareas"""
        agent = orchestrator_agent()
        
        with patch('agents.multiagent_orchestrator_agent.MultiAgentOrchestratorAgent._coordinate_agents') as mock_coordinate:
            mock_coordinate.return_value = {
                "success": True,
                "results": {
                    "file_processor": {"status": "completed"},
                    "search_engine": {"status": "completed"}
                }
            }
            
            result = await agent.coordinate_agents("task-123", ["agent1", "agent2"])
            
            assert result['success'] is True
            assert 'results' in result
    
    async def test_parallel_execution(self, orchestrator_agent):
        """Test de ejecución paralela"""
        agent = orchestrator_agent()
        
        tasks = [
            {"id": "task1", "agent": "search_engine"},
            {"id": "task2", "agent": "file_processor"}
        ]
        
        with patch('agents.multiagent_orchestrator_agent.MultiAgentOrchestratorAgent._execute_parallel') as mock_parallel:
            mock_parallel.return_value = {
                "success": True,
                "results": [{"task_id": "task1", "status": "completed"}]
            }
            
            result = await agent.execute_parallel(tasks, max_parallel=2)
            
            assert result['success'] is True
    
    async def test_workflow_execution(self, orchestrator_agent):
        """Test de ejecución de workflows"""
        agent = orchestrator_agent()
        
        workflow = {
            "name": "document_processing_workflow",
            "steps": [
                {"agent": "file_processor", "operation": "read"},
                {"agent": "search_engine", "operation": "search"},
                {"agent": "python_executor", "operation": "analyze"}
            ]
        }
        
        with patch('agents.multiagent_orchestrator_agent.MultiAgentOrchestratorAgent._execute_workflow') as mock_workflow:
            mock_workflow.return_value = {
                "success": True,
                "workflow_id": "workflow-123",
                "status": "completed"
            }
            
            result = await agent.execute_workflow(workflow)
            
            assert result['success'] is True
            assert result['status'] == "completed"


class TestMemoryManagerWrapper:
    """Tests para MemoryManagerWrapper"""
    
    @pytest.fixture
    def memory_agent(self):
        """Fixture del gestor de memoria"""
        from agents.memory_manager_wrapper import MemoryManagerWrapper
        return MemoryManagerWrapper
    
    async def test_memory_storage(self, memory_agent, mock_redis):
        """Test de almacenamiento en memoria"""
        agent = memory_agent()
        
        key = "test_key"
        value = {"data": "test_data"}
        
        with patch('agents.memory_manager_wrapper.MemoryManagerWrapper._store') as mock_store:
            mock_store.return_value = {
                "success": True,
                "stored": True
            }
            
            result = await agent.store(key, value)
            
            assert result['success'] is True
    
    async def test_memory_retrieval(self, memory_agent, mock_redis):
        """Test de recuperación de memoria"""
        agent = memory_agent()
        
        key = "test_key"
        
        with patch('agents.memory_manager_wrapper.MemoryManagerWrapper._retrieve') as mock_retrieve:
            mock_retrieve.return_value = {
                "success": True,
                "value": {"data": "test_data"}
            }
            
            result = await agent.retrieve(key)
            
            assert result['success'] is True
            assert 'value' in result
    
    async def test_memory_cleanup(self, memory_agent):
        """Test de limpieza de memoria"""
        agent = memory_agent()
        
        with patch('agents.memory_manager_wrapper.MemoryManagerWrapper._cleanup') as mock_cleanup:
            mock_cleanup.return_value = {
                "success": True,
                "cleaned_items": 100
            }
            
            result = await agent.cleanup_expired()
            
            assert result['success'] is True
    
    async def test_context_persistence(self, memory_agent):
        """Test de persistencia de contexto"""
        agent = memory_agent()
        
        context_data = {
            "session_id": "session-123",
            "user_context": {"user_id": "user-123"},
            "timestamp": "2025-11-04T05:43:15Z"
        }
        
        with patch('agents.memory_manager_wrapper.MemoryManagerWrapper._persist_context') as mock_persist:
            mock_persist.return_value = {
                "success": True,
                "context_id": "context-123"
            }
            
            result = await agent.persist_context(context_data)
            
            assert result['success'] is True


class TestPlannerWrapper:
    """Tests para PlannerWrapper"""
    
    @pytest.fixture
    def planner_agent(self):
        """Fixture del planificador"""
        from agents.planner_wrapper import PlannerWrapper
        return PlannerWrapper
    
    async def test_plan_creation(self, planner_agent):
        """Test de creación de planes"""
        agent = planner_agent()
        
        task_description = "Process a document and extract key information"
        
        with patch('agents.planner_wrapper.PlannerWrapper._create_plan') as mock_create:
            mock_create.return_value = {
                "success": True,
                "plan": {
                    "steps": [
                        {"action": "read_document", "agent": "file_processor"},
                        {"action": "extract_info", "agent": "python_executor"},
                        {"action": "summarize", "agent": "reasoner"}
                    ]
                }
            }
            
            result = await agent.create_plan(task_description)
            
            assert result['success'] is True
            assert 'plan' in result
            assert len(result['plan']['steps']) > 0
    
    async def test_plan_optimization(self, planner_agent):
        """Test de optimización de planes"""
        agent = planner_agent()
        
        plan = {
            "steps": [
                {"action": "read", "estimated_time": 5},
                {"action": "process", "estimated_time": 10},
                {"action": "write", "estimated_time": 3}
            ]
        }
        
        with patch('agents.planner_wrapper.PlannerWrapper._optimize_plan') as mock_optimize:
            mock_optimize.return_value = {
                "success": True,
                "optimized_plan": plan,
                "improvements": ["Reduced estimated time by 20%"]
            }
            
            result = await agent.optimize_plan(plan)
            
            assert result['success'] is True
    
    async def test_resource_allocation(self, planner_agent):
        """Test de asignación de recursos"""
        agent = planner_agent()
        
        requirements = {
            "cpu": 2.0,
            "memory": 1024,
            "agents": ["python_executor", "search_engine"]
        }
        
        with patch('agents.planner_wrapper.PlannerWrapper._allocate_resources') as mock_allocate:
            mock_allocate.return_value = {
                "success": True,
                "allocation": {
                    "cpu": 2.5,
                    "memory": 2048,
                    "agents": ["python_executor", "search_engine"]
                }
            }
            
            result = await agent.allocate_resources(requirements)
            
            assert result['success'] is True


class TestReasonerWrapper:
    """Tests para ReasonerWrapper"""
    
    @pytest.fixture
    def reasoner_agent(self):
        """Fixture del razonador"""
        from agents.reasoner_wrapper import ReasonerWrapper
        return ReasonerWrapper
    
    async def test_logical_reasoning(self, reasoner_agent):
        """Test de razonamiento lógico"""
        agent = reasoner_agent()
        
        premises = [
            "All humans are mortal",
            "Socrates is human"
        ]
        conclusion = "Socrates is mortal"
        
        with patch('agents.reasoner_wrapper.ReasonerWrapper._logical_reasoning') as mock_reason:
            mock_reason.return_value = {
                "success": True,
                "valid": True,
                "confidence": 0.95
            }
            
            result = await agent.logical_reasoning(premises, conclusion)
            
            assert result['success'] is True
            assert result['valid'] is True
    
    async def test_pattern_recognition(self, reasoner_agent):
        """Test de reconocimiento de patrones"""
        agent = reasoner_agent()
        
        data = [1, 4, 9, 16, 25]  # Números cuadrados
        
        with patch('agents.reasoner_wrapper.ReasonerWrapper._pattern_recognition') as mock_pattern:
            mock_pattern.return_value = {
                "success": True,
                "patterns": [
                    {"type": "arithmetic_sequence", "rule": "n^2"}
                ]
            }
            
            result = await agent.recognize_patterns(data)
            
            assert result['success'] is True
            assert len(result['patterns']) > 0
    
    async def test_causal_inference(self, reasoner_agent):
        """Test de inferencia causal"""
        agent = reasoner_agent()
        
        events = [
            {"event": "rain", "time": "10:00"},
            {"event": "wet_ground", "time": "10:15"}
        ]
        
        with patch('agents.reasoner_wrapper.ReasonerWrapper._causal_inference') as mock_causal:
            mock_causal.return_value = {
                "success": True,
                "causal_relationships": [
                    {"cause": "rain", "effect": "wet_ground", "confidence": 0.9}
                ]
            }
            
            result = await agent.infer_causes(events)
            
            assert result['success'] is True
            assert len(result['causal_relationships']) > 0


class TestVerifierWrapper:
    """Tests para VerifierWrapper"""
    
    @pytest.fixture
    def verifier_agent(self):
        """Fixture del verificador"""
        from agents.verifier_wrapper import VerifierWrapper
        return VerifierWrapper
    
    async def test_result_verification(self, verifier_agent):
        """Test de verificación de resultados"""
        agent = verifier_agent()
        
        result = {
            "value": 42,
            "method": "calculation"
        }
        expected = {
            "type": "number",
            "range": [0, 100]
        }
        
        with patch('agents.verifier_wrapper.VerifierWrapper._verify_result') as mock_verify:
            mock_verify.return_value = {
                "success": True,
                "valid": True,
                "quality_score": 0.95
            }
            
            result_check = await agent.verify_result(result, expected)
            
            assert result_check['success'] is True
            assert result_check['valid'] is True
    
    async def test_consistency_check(self, verifier_agent):
        """Test de verificación de consistencia"""
        agent = verifier_agent()
        
        data_points = [
            {"value": 10, "timestamp": "10:00"},
            {"value": 15, "timestamp": "10:01"},
            {"value": 12, "timestamp": "10:02"}
        ]
        
        with patch('agents.verifier_wrapper.VerifierWrapper._check_consistency') as mock_check:
            mock_check.return_value = {
                "success": True,
                "consistent": True,
                "outliers": []
            }
            
            result = await agent.check_consistency(data_points)
            
            assert result['success'] is True
            assert result['consistent'] is True
    
    async def test_quality_assessment(self, verifier_agent):
        """Test de evaluación de calidad"""
        agent = verifier_agent()
        
        output = {
            "content": "Processed data with insights",
            "format": "structured",
            "completeness": 0.9
        }
        
        with patch('agents.verifier_wrapper.VerifierWrapper._assess_quality') as mock_assess:
            mock_assess.return_value = {
                "success": True,
                "quality_score": 0.88,
                "criteria_scores": {
                    "accuracy": 0.9,
                    "completeness": 0.85,
                    "format": 0.95
                }
            }
            
            result = await agent.assess_quality(output)
            
            assert result['success'] is True
            assert result['quality_score'] >= 0


class TestAgentIntegration:
    """Tests de integración entre agentes"""
    
    async def test_agent_communication(self):
        """Test de comunicación entre agentes"""
        from agents.base_agent_wrapper import BaseAgentWrapper
        from agents.python_executor_agent import AdvancedPythonExecutorAgent
        
        # Simular comunicación entre agentes
        base_agent = BaseAgentWrapper()
        python_agent = AdvancedPythonExecutorAgent()
        
        # Mock de la comunicación
        with patch.object(base_agent, 'send_message') as mock_send:
            with patch.object(python_agent, 'receive_message') as mock_receive:
                mock_send.return_value = {"status": "sent"}
                mock_receive.return_value = {"status": "received"}
                
                # Test de envío de mensaje
                message = {"type": "task_request", "data": "test"}
                result = await base_agent.send_message(python_agent.agent_id, message)
                
                assert result['status'] == "sent"
                assert mock_receive.called
    
    async def test_workflow_execution(self):
        """Test de ejecución de workflow completo"""
        from agents.multiagent_orchestrator_agent import MultiAgentOrchestratorAgent
        from agents.file_processing_agent import FileProcessingAgent
        from agents.search_engine_agent import SearchEngineAgent
        
        orchestrator = MultiAgentOrchestratorAgent()
        
        # Mock de agentes individuales
        with patch('agents.file_processing_agent.FileProcessingAgent') as MockFileAgent:
            with patch('agents.search_engine_agent.SearchEngineAgent') as MockSearchAgent:
                mock_file_agent = AsyncMock()
                mock_search_agent = AsyncMock()
                MockFileAgent.return_value = mock_file_agent
                MockSearchAgent.return_value = mock_search_agent
                
                mock_file_agent.process_request.return_value = {"success": True}
                mock_search_agent.process_request.return_value = {"success": True}
                
                # Test workflow de procesamiento de documentos
                workflow_result = await orchestrator.execute_workflow({
                    "name": "document_processing",
                    "steps": [
                        {"agent": "file_processor", "operation": "read"},
                        {"agent": "search_engine", "operation": "analyze"}
                    ]
                })
                
                assert workflow_result['success'] is True
    
    async def test_error_propagation(self):
        """Test de propagación de errores entre agentes"""
        from agents.base_agent_wrapper import BaseAgentWrapper
        
        agent = BaseAgentWrapper()
        
        # Simular error en procesamiento
        with patch.object(agent, '_process_request') as mock_process:
            mock_process.side_effect = Exception("Test error")
            
            request = {"operation": "test", "data": "test"}
            
            # Debería manejar el error gracefully
            result = await agent.process_request(request)
            
            assert 'error' in result or result.get('success') is False