"""
Load Testing con Locust para 100+ usuarios concurrentes
"""

from locust import HttpUser, task, between, events
import time
import json
import random
from datetime import datetime

from utils.base_utils import TestDataGenerator, TestLogger
from config.test_config import *

class EnterpriseLoadUser(HttpUser):
    """Usuario simulado para load testing"""
    
    wait_time = between(1, 3)  # Esperar entre 1-3 segundos entre requests
    
    def on_start(self):
        """Setup inicial del usuario"""
        self.logger = TestLogger(f"LoadUser_{self.user_count}", PROJECT_ROOT / "logs" / "load_test.log")
        self.user_data = TestDataGenerator.generate_user_data()
        self.token = None
        
        # Autenticación inicial
        self._authenticate()
    
    def _authenticate(self):
        """Autenticar usuario"""
        try:
            auth_data = {
                "username": self.user_data["username"],
                "password": "test_password_123"
            }
            
            response = self.client.post("/api/auth/login", json=auth_data)
            
            if response.status_code == 200:
                auth_result = response.json()
                self.token = auth_result.get("access_token")
                self.logger.info(f"User {self.user_data['username']} authenticated successfully")
            else:
                self.logger.warning(f"Authentication failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
    
    @task(3)
    def health_check_load(self):
        """Test de carga del health check"""
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        
        with self.client.get(
            "/health",
            headers=headers,
            name="Health Check",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(5)
    def mcp_tool_execution_load(self):
        """Test de carga de ejecución de herramientas MCP"""
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        
        mcp_requests = [
            {
                "tool": "python_executor",
                "code": "print('Load test Python execution')",
                "timeout": 30
            },
            {
                "tool": "database_query",
                "query": "SELECT 1 as test",
                "timeout": 10
            },
            {
                "tool": "file_processor", 
                "operation": "list",
                "path": "/tmp",
                "timeout": 5
            }
        ]
        
        request_data = random.choice(mcp_requests)
        
        with self.client.post(
            "/api/mcp/execute",
            json=request_data,
            headers=headers,
            name="MCP Tool Execution",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"MCP execution failed: {response.status_code}")
    
    @task(4)
    def database_operations_load(self):
        """Test de carga de operaciones de base de datos"""
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        
        operations = [
            ("GET", "/api/users"),
            ("GET", "/api/users/profile"),
            ("POST", "/api/users", self.user_data),
            ("PUT", f"/api/users/{self.user_data['id']}", {"email": f"updated_{self.user_data['id']}@example.com"})
        ]
        
        method, endpoint, data = random.choice(operations)
        
        with self.client.request(
            method,
            endpoint,
            json=data,
            headers=headers,
            name=f"DB {method} {endpoint}",
            catch_response=True
        ) as response:
            if response.status_code in [200, 201, 204]:
                response.success()
            elif response.status_code == 401:
                response.failure(f"Authentication required: {response.status_code}")
            else:
                response.failure(f"Database operation failed: {response.status_code}")
    
    @task(2)
    def api_stress_test(self):
        """Test de estrés de API"""
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        
        # Simular operaciones de alto impacto
        stress_endpoints = [
            "/api/admin/system/metrics",
            "/api/analytics/dashboard",
            "/api/reports/generate",
            "/api/batch/process"
        ]
        
        endpoint = random.choice(stress_endpoints)
        
        with self.client.get(
            endpoint,
            headers=headers,
            name="Stress Test Endpoint",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                # Para stress tests, fallos pueden ser esperados
                if response.status_code in [429, 503]:  # Rate limited o Service unavailable
                    response.success()
                else:
                    response.failure(f"Stress test failed: {response.status_code}")
    
    @task(1)
    def file_operations_load(self):
        """Test de carga de operaciones de archivos"""
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        
        file_operations = [
            ("POST", "/api/files/upload", {"filename": "test_load.txt", "content": "x" * 1000}),
            ("GET", "/api/files/list"),
            ("GET", "/api/files/download/test_load.txt")
        ]
        
        method, endpoint, data = random.choice(file_operations)
        
        with self.client.request(
            method,
            endpoint,
            json=data,
            headers=headers,
            name=f"File {method}",
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"File operation failed: {response.status_code}")

class AdminLoadUser(HttpUser):
    """Usuario administrador para load testing"""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """Setup de usuario administrador"""
        self.logger = TestLogger(f"AdminLoadUser_{self.user_count}", PROJECT_ROOT / "logs" / "admin_load.log")
        self.admin_token = self._admin_authenticate()
    
    def _admin_authenticate(self):
        """Autenticación de administrador"""
        auth_data = {
            "username": "admin",
            "password": "admin_password_123"
        }
        
        response = self.client.post("/api/auth/admin/login", json=auth_data)
        
        if response.status_code == 200:
            auth_result = response.json()
            return auth_result.get("access_token")
        
        return None
    
    @task(2)
    def admin_monitoring(self):
        """Monitor de carga para administradores"""
        headers = {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}
        
        with self.client.get(
            "/api/admin/monitoring/system",
            headers=headers,
            name="Admin System Monitoring",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Admin monitoring failed: {response.status_code}")
    
    @task(1)
    def admin_user_management(self):
        """Gestión de usuarios bajo carga"""
        headers = {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}
        
        with self.client.get(
            "/api/admin/users/list",
            headers=headers,
            name="Admin User Management",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Admin user management failed: {response.status_code}")

class BurstLoadUser(HttpUser):
    """Usuario para test de ráfagas de carga"""
    
    wait_time = between(0.1, 0.5)  # Muy rápido para generar ráfagas
    
    def on_start(self):
        """Setup para ráfagas"""
        self.logger = TestLogger(f"BurstLoadUser_{self.user_count}", PROJECT_ROOT / "logs" / "burst_load.log")
    
    @task(10)
    def burst_health_checks(self):
        """Ráfaga de health checks"""
        with self.client.get(
            "/health",
            name="Burst Health Check",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Burst health check failed: {response.status_code}")

# Event handlers para métricas personalizadas
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Listener para inicio de test"""
    logger = TestLogger("LoadTestStart", PROJECT_ROOT / "logs" / "load_test.log")
    logger.info(f"Load test starting with {environment.runner.target_user_count} users")
    logger.info(f"Host: {environment.host}")
    logger.info(f"Test will run until all users complete")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Listener para fin de test"""
    logger = TestLogger("LoadTestStop", PROJECT_ROOT / "logs" / "load_test.log")
    
    # Estadísticas finales
    stats = environment.stats
    
    logger.info("Load test completed")
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Failures: {stats.total.num_failures}")
    logger.info(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    logger.info(f"99th percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    logger.info(f"Requests per second: {stats.total.current_rps:.2f}")

@events.request.add_listener
def on_request(environment, request, response, **kwargs):
    """Listener para cada request"""
    # Registrar requests lentos (>2 segundos)
    if response.response_time > 2000:
        logger = TestLogger("SlowRequests", PROJECT_ROOT / "logs" / "slow_requests.log")
        logger.warning(
            f"Slow request detected: {request.name} took {response.response_time:.2f}ms"
        )

# Configuración de escenarios de carga
class ProgressiveLoadTest:
    """Escenario de carga progresiva"""
    
    @staticmethod
    def create_progressive_scenario():
        """Crea escenario de carga progresiva"""
        return {
            "scenarios": [
                {
                    "name": "Light Load",
                    "users": 50,
                    "duration": "2m",
                    "description": "Carga ligera inicial"
                },
                {
                    "name": "Moderate Load", 
                    "users": 150,
                    "duration": "3m",
                    "description": "Carga moderada"
                },
                {
                    "name": "Heavy Load",
                    "users": 300,
                    "duration": "5m", 
                    "description": "Carga pesada"
                },
                {
                    "name": "Peak Load",
                    "users": 500,
                    "duration": "2m",
                    "description": "Carga pico"
                },
                {
                    "name": "Stress Test",
                    "users": 1000,
                    "duration": "1m",
                    "description": "Test de estrés"
                }
            ]
        }

class SpikeLoadTest:
    """Escenario de spike load"""
    
    @staticmethod 
    def create_spike_scenario():
        """Crea escenario de spike load"""
        return {
            "spike_patterns": [
                {
                    "name": "Normal to Spike",
                    "baseline_users": 50,
                    "spike_users": 500,
                    "spike_duration": "30s",
                    "recovery_duration": "2m"
                },
                {
                    "name": "Gradual Increase",
                    "start_users": 25,
                    "peak_users": 750,
                    "ramp_up_time": "3m",
                    "peak_duration": "1m"
                }
            ]
        }

# Exportar configuraciones
LOAD_TEST_SCENARIOS = {
    "progressive": ProgressiveLoadTest.create_progressive_scenario(),
    "spike": SpikeLoadTest.create_spike_scenario()
}

if __name__ == "__main__":
    # Comando para ejecutar load tests
    # locust -f load_tests.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 300s --csv=load_test_results
    print("Load testing scenarios configured")
    print("To run: locust -f load_tests.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 300s")
