"""
Utilidades Base para la Suite de Testing Enterprise
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

import pytest
import requests
from jinja2 import Template

from config.test_config import *

@dataclass
class TestResult:
    """Estructura estándar para resultados de tests"""
    test_name: str
    test_type: str
    status: str  # PASSED, FAILED, ERROR, SKIPPED
    duration: float
    timestamp: str
    details: Dict[str, Any]
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

class TestLogger:
    """Logger personalizado para la suite de testing"""
    
    def __init__(self, name: str, log_file: Path):
        self.name = name
        self.log_file = log_file
        
        # Crear logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, TEST_CONFIG["log_level"]))
        
        # Configurar formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Handler para archivo
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(f"{message} | Metadata: {kwargs}")
    
    def error(self, message: str, error: Exception = None, **kwargs):
        """Log error message"""
        if error:
            self.logger.error(f"{message} | Error: {str(error)} | Metadata: {kwargs}")
        else:
            self.logger.error(f"{message} | Metadata: {kwargs}")
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(f"{message} | Metadata: {kwargs}")
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(f"{message} | Metadata: {kwargs}")

class TestDataGenerator:
    """Generador de datos para tests"""
    
    @staticmethod
    def generate_user_data() -> Dict[str, Any]:
        """Genera datos de usuario aleatorio para tests"""
        return {
            "id": str(uuid.uuid4()),
            "username": f"test_user_{int(time.time())}",
            "email": f"test{int(time.time())}@example.com",
            "first_name": "Test",
            "last_name": "User",
            "role": "user",
            "created_at": datetime.now().isoformat(),
            "is_active": True
        }
    
    @staticmethod
    def generate_mcp_request_data() -> Dict[str, Any]:
        """Genera datos de request MCP para tests"""
        return {
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": "python_execute",
                "arguments": {
                    "code": "print('Hello World')",
                    "timeout": 30
                }
            },
            "timestamp": datetime.now().isoformat()
        }

class MetricsCollector:
    """Recolector de métricas para análisis de performance"""
    
    def __init__(self):
        self.metrics = {
            "response_times": [],
            "throughput": [],
            "error_counts": {},
            "resource_usage": {},
            "custom_metrics": {}
        }
    
    def record_response_time(self, endpoint: str, duration: float):
        """Registra tiempo de respuesta"""
        if endpoint not in self.metrics["response_times"]:
            self.metrics["response_times"][endpoint] = []
        self.metrics["response_times"][endpoint].append(duration)
    
    def record_error(self, endpoint: str, error_type: str):
        """Registra error"""
        if endpoint not in self.metrics["error_counts"]:
            self.metrics["error_counts"][endpoint] = {}
        
        if error_type not in self.metrics["error_counts"][endpoint]:
            self.metrics["error_counts"][endpoint][error_type] = 0
        
        self.metrics["error_counts"][endpoint][error_type] += 1
    
    def get_average_response_time(self, endpoint: str) -> float:
        """Calcula tiempo promedio de respuesta"""
        times = self.metrics["response_times"].get(endpoint, [])
        return sum(times) / len(times) if times else 0
    
    def get_percentile_response_time(self, endpoint: str, percentile: int) -> float:
        """Calcula percentil de tiempo de respuesta"""
        times = sorted(self.metrics["response_times"].get(endpoint, []))
        if not times:
            return 0
        
        index = int(len(times) * percentile / 100)
        return times[min(index, len(times) - 1)]

class ReportGenerator:
    """Generador de reportes de testing"""
    
    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
    
    def generate_html_report(self, results: List[TestResult], output_file: Path):
        """Genera reporte HTML"""
        template_path = self.template_dir / "test_report.html"
        
        if template_path.exists():
            with open(template_path) as f:
                template = Template(f.read())
        else:
            # Template por defecto
            template = Template("""
            <h1>Reporte de Testing Enterprise</h1>
            <h2>Resumen</h2>
            <p>Total de tests: {{ total_tests }}</p>
            <p>Tests passed: {{ passed_tests }}</p>
            <p>Tests failed: {{ failed_tests }}</p>
            <p>Tests errors: {{ error_tests }}</p>
            
            <h2>Detalles de Tests</h2>
            <table border="1">
                <tr>
                    <th>Test Name</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Error Message</th>
                </tr>
                {% for result in results %}
                <tr>
                    <td>{{ result.test_name }}</td>
                    <td>{{ result.test_type }}</td>
                    <td>{{ result.status }}</td>
                    <td>{{ "%.3f"|format(result.duration) }}s</td>
                    <td>{{ result.error_message or "-" }}</td>
                </tr>
                {% endfor %}
            </table>
            """)
        
        # Calcular estadísticas
        total_tests = len(results)
        passed_tests = len([r for r in results if r.status == "PASSED"])
        failed_tests = len([r for r in results if r.status == "FAILED"])
        error_tests = len([r for r in results if r.status == "ERROR"])
        
        html_content = template.render(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            error_tests=error_tests,
            results=results
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def generate_json_report(self, results: List[TestResult], output_file: Path):
        """Genera reporte JSON"""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(results),
                "passed": len([r for r in results if r.status == "PASSED"]),
                "failed": len([r for r in results if r.status == "FAILED"]),
                "errors": len([r for r in results if r.status == "ERROR"]),
                "success_rate": len([r for r in results if r.status == "PASSED"]) / len(results) * 100
            },
            "test_results": [asdict(result) for result in results]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)

class APITester:
    """Utilidad para testing de APIs"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """Realiza GET request"""
        return self.session.get(f"{self.base_url}{endpoint}", **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """Realiza POST request"""
        return self.session.post(f"{self.base_url}{endpoint}", **kwargs)
    
    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """Realiza PUT request"""
        return self.session.put(f"{self.base_url}{endpoint}", **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """Realiza DELETE request"""
        return self.session.delete(f"{self.base_url}{endpoint}", **kwargs)
    
    def health_check(self, endpoint: str = "/health") -> Dict[str, Any]:
        """Verifica salud de un endpoint"""
        try:
            response = self.get(endpoint, timeout=10)
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Instancias globales
test_logger = TestLogger("EnterpriseTestSuite", TEST_LOG_FILE)
metrics_collector = MetricsCollector()
report_generator = ReportGenerator(REPORTS_DIR)
api_tester = APITester(BASE_URL)
