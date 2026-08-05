"""
Configuración Global de la Suite de Testing Enterprise
"""

import os
import sys
from pathlib import Path

# Paths del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
MCP_CORE_DIR = PROJECT_ROOT / "mcp-core-superior"
MCP_GATEWAY_DIR = PROJECT_ROOT / "mcp-context-forge"

# URLs y Endpoints
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
API_URL = f"{BASE_URL}/api/v1"
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8080")

# Base de datos de testing
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://test_user:test_password@localhost:5432/test_enterprise_db"
)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Configuración de testing
TEST_CONFIG = {
    "timeout": 30,
    "retries": 3,
    "parallel_workers": 4,
    "coverage_threshold": 95,
    "max_test_duration": 300,  # 5 minutos
    "log_level": "INFO"
}

# Configuración de performance
PERFORMANCE_CONFIG = {
    "load_test_users": 100,
    "max_load_users": 1000,
    "ramp_up_time": 60,
    "test_duration": 300,
    "response_time_threshold": 2.0,  # segundos
    "throughput_threshold": 100,  # requests/segundo
    "error_rate_threshold": 1.0  # porcentaje
}

# Configuración de seguridad
SECURITY_CONFIG = {
    "vulnerability_scan_enabled": True,
    "penetration_test_enabled": True,
    "encryption_validation": True,
    "auth_validation": True,
    "rate_limit_validation": True,
    "sql_injection_test": True,
    "xss_test": True
}

# Configuración de monitoreo
MONITORING_CONFIG = {
    "metrics_enabled": True,
    "alerts_enabled": True,
    "health_check_interval": 30,  # segundos
    "alert_thresholds": {
        "cpu_usage": 80,
        "memory_usage": 85,
        "disk_usage": 90,
        "response_time": 5.0,
        "error_rate": 5.0
    }
}

# Configuración de compliance
COMPLIANCE_CONFIG = {
    "gdpr_validation": True,
    "sox_validation": True,
    "hipaa_validation": True,
    "pci_dss_validation": False,  # Si no se maneja pagos
    "audit_logging": True,
    "data_retention_validation": True
}

# Archivos de logs
LOG_DIR = PROJECT_ROOT / "logs"
TEST_LOG_FILE = LOG_DIR / "test_execution.log"
PERFORMANCE_LOG_FILE = LOG_DIR / "performance_results.log"
SECURITY_LOG_FILE = LOG_DIR / "security_results.log"

# Directorios de reportes
REPORTS_DIR = PROJECT_ROOT / "reports"
COVERAGE_DIR = REPORTS_DIR / "coverage"
PERFORMANCE_REPORTS_DIR = REPORTS_DIR / "performance"
SECURITY_REPORTS_DIR = REPORTS_DIR / "security"
COMPLIANCE_REPORTS_DIR = REPORTS_DIR / "compliance"

# Crear directorios si no existen
for directory in [LOG_DIR, REPORTS_DIR, COVERAGE_DIR, PERFORMANCE_REPORTS_DIR, 
                  SECURITY_REPORTS_DIR, COMPLIANCE_REPORTS_DIR]:
    directory.mkdir(exist_ok=True)
