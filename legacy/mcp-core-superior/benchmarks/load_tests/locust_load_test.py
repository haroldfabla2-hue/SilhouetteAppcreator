#!/usr/bin/env python3
"""
Load Testing con Locust para MCP-Core-Superior vs MiniMax Agent
Pruebas de carga, estrés y escalabilidad
"""

import json
import random
import logging
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner
import time
from datetime import datetime
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPUser(HttpUser):
    """Simula usuario real interacting con MCP system"""
    wait_time = between(1, 3)  # Espera entre 1-3 segundos entre requests
    
    def on_start(self):
        """Inicialización cuando comienza un usuario virtual"""
        self.username = f"user_{self.environment.runner.quit}"
        self.token = "mock_jwt_token"  # En producción sería un token real
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    @task(10)
    def health_check(self):
        """Test de health check - más frecuente"""
        with self.client.get("/api/health", headers=self.headers, 
                           name="Health Check", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(5)
    def simple_task_execution(self):
        """Ejecutar tarea simple"""
        payload = {
            "task_type": "simple",
            "parameters": {
                "input": f"test_input_{random.randint(1, 1000)}",
                "complexity": "low"
            }
        }
        
        with self.client.post("/api/tasks/execute", 
                            json=payload, 
                            headers=self.headers,
                            name="Simple Task Execution",
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Task execution failed: {response.status_code}")
    
    @task(3)
    def complex_workflow(self):
        """Ejecutar workflow complejo"""
        payload = {
            "workflow_type": "data_processing",
            "steps": [
                {"action": "extract", "source": "api/data"},
                {"action": "transform", "operation": "clean"},
                {"action": "load", "destination": "database"}
            ],
            "parameters": {
                "batch_size": random.randint(10, 100),
                "timeout": 30
            }
        }
        
        with self.client.post("/api/workflows/execute", 
                            json=payload, 
                            headers=self.headers,
                            name="Complex Workflow",
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Workflow execution failed: {response.status_code}")
    
    @task(2)
    def database_operation(self):
        """Operación de base de datos"""
        operations = ["SELECT", "INSERT", "UPDATE", "DELETE"]
        operation = random.choice(operations)
        
        payload = {
            "query_type": operation,
            "table": "test_table",
            "data": {
                "field1": f"value_{random.randint(1, 100)}",
                "field2": random.randint(1, 1000),
                "timestamp": datetime.now().isoformat()
            }
        }
        
        with self.client.post(f"/api/database/{operation.lower()}", 
                            json=payload, 
                            headers=self.headers,
                            name=f"DB {operation}",
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Database {operation} failed: {response.status_code}")
    
    @task(2)
    def agent_execution(self):
        """Ejecución de agente específico"""
        agent_types = ["python_executor", "web_scraper", "git_operations", "database_ops"]
        agent_type = random.choice(agent_types)
        
        payload = {
            "agent_type": agent_type,
            "parameters": {
                "timeout": 60,
                "retry_count": 3,
                "complexity": random.choice(["low", "medium", "high"])
            },
            "input_data": f"test_data_{random.randint(1, 1000)}"
        }
        
        with self.client.post(f"/api/agents/{agent_type}/execute", 
                            json=payload, 
                            headers=self.headers,
                            name=f"Agent {agent_type}",
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Agent execution failed: {response.status_code}")
    
    @task(1)
    def streaming_request(self):
        """Request con streaming (más pesado)"""
        payload = {
            "stream_type": "data_analysis",
            "duration": random.randint(5, 30),
            "output_format": "json",
            "parameters": {
                "sample_rate": 1000,
                "buffer_size": 8192
            }
        }
        
        with self.client.post("/api/stream", 
                            json=payload, 
                            headers=self.headers,
                            name="Streaming Request",
                            catch_response=True,
                            stream=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Streaming failed: {response.status_code}")

class MiniMaxUser(HttpUser):
    """Simula usuario interactuando con MiniMax Agent"""
    wait_time = between(1, 3)
    weight = 1  # Mismo peso que MCPUser para comparación fair
    
    def on_start(self):
        self.username = f"minimax_user_{self.environment.runner.quit}"
        self.token = "mock_minimax_token"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    @task(10)
    def minimax_health(self):
        """Health check para MiniMax"""
        with self.client.get("/health", headers=self.headers, 
                           name="MiniMax Health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"MiniMax health failed: {response.status_code}")
    
    @task(5)
    def minimax_task(self):
        """Tarea simple para MiniMax"""
        payload = {
            "task": "process_data",
            "input": f"minimax_input_{random.randint(1, 1000)}",
            "priority": "normal"
        }
        
        with self.client.post("/api/task", 
                            json=payload, 
                            headers=self.headers,
                            name="MiniMax Task",
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"MiniMax task failed: {response.status_code}")
    
    @task(3)
    def minimax_workflow(self):
        """Workflow complejo para MiniMax"""
        payload = {
            "workflow": "data_pipeline",
            "stages": ["extract", "transform", "load"],
            "config": {
                "parallel": True,
                "timeout": 60
            }
        }
        
        with self.client.post("/api/workflow", 
                            json=payload, 
                            headers=self.headers,
                            name="MiniMax Workflow",
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"MiniMax workflow failed: {response.status_code}")

# Event listeners para logging y análisis
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Evento de inicio de test"""
    logger.info(f"🚀 Starting load test at {datetime.now()}")
    logger.info(f"Target hosts: MCP-Core-Superior: {environment.host}, MiniMax: {environment.host}")
    
    # Configurar environment variables para tracking
    os.environ['LOAD_TEST_START_TIME'] = str(datetime.now())

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Evento de fin de test"""
    logger.info(f"🏁 Load test completed at {datetime.now()}")
    
    # Generar análisis post-test
    stats = environment.stats
    
    logger.info("=" * 60)
    logger.info("LOAD TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Failed requests: {stats.total.num_failures}")
    logger.info(f"Success rate: {(1 - stats.total.num_failures/stats.total.num_requests)*100:.2f}%")
    logger.info(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    logger.info(f"Requests per second: {stats.total.current_rps:.2f}")
    
    # Guardar estadísticas detalladas
    with open('load_test_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'stats': {
                'total_requests': stats.total.num_requests,
                'failed_requests': stats.total.num_failures,
                'success_rate': (1 - stats.total.num_failures/stats.total.num_requests)*100,
                'avg_response_time': stats.total.avg_response_time,
                'percentiles': {
                    '50': stats.total.get_response_time_percentile(0.50),
                    '90': stats.total.get_response_time_percentile(0.90),
                    '95': stats.total.get_response_time_percentile(0.95),
                    '99': stats.total.get_response_time_percentile(0.99)
                },
                'current_rps': stats.total.current_rps,
                'peak_rps': stats.total.max rps
            }
        }, indent=2)

@events.request.add_listener
def on_request(environment, request, response, **kwargs):
    """Listener para cada request (logging detallado)"""
    if environment.runner.quit:
        return
    
    # Logging de requests lentos (>1 segundo)
    if response.response_time > 1000:
        logger.warning(f"Slow request detected: {request.name} took {response.response_time:.2f}ms")

# Configuración para distributed testing
if __name__ == "__main__":
    # Este script puede ejecutarse directamente o via locust command
    # Para distributed: locust -f locust_load_test.py --master
    # Para worker: locust -f locust_load_test.py --worker --master-host=IP
    pass