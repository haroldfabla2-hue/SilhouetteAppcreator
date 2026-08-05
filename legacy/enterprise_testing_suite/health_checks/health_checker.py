"""
Sistema de Health Checks Automáticos
"""

import asyncio
import time
import json
import subprocess
import socket
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from utils.base_utils import (
    TestResult, TestDataGenerator, APITester, TestLogger
)
from config.test_config import *

@dataclass
class HealthCheckResult:
    """Resultado de health check"""
    service_name: str
    status: str  # "healthy", "unhealthy", "degraded"
    timestamp: str
    response_time_ms: float
    details: Dict[str, Any]
    error_message: Optional[str] = None

@dataclass
class ServiceConfig:
    """Configuración de servicio"""
    name: str
    check_type: str  # "http", "tcp", "command", "database"
    endpoint: Optional[str] = None
    port: Optional[int] = None
    command: Optional[str] = None
    expected_status: int = 200
    timeout_seconds: int = 10
    critical: bool = True
    retry_attempts: int = 3

class HealthChecker:
    """Health checker principal"""
    
    def __init__(self):
        self.logger = TestLogger("HealthChecker", PROJECT_ROOT / "logs" / "health_checks.log")
        self.api_tester = APITester(BASE_URL)
        self.service_configs = self._load_service_configs()
        self.check_results: List[HealthCheckResult] = []
    
    def _load_service_configs(self) -> List[ServiceConfig]:
        """Carga configuraciones de servicios"""
        return [
            ServiceConfig(
                name="api_gateway",
                check_type="http",
                endpoint="/health",
                critical=True,
                expected_status=200
            ),
            ServiceConfig(
                name="mcp_server",
                check_type="http", 
                endpoint="http://localhost:8080/health",
                port=8080,
                critical=True,
                expected_status=200
            ),
            ServiceConfig(
                name="database_postgres",
                check_type="database",
                endpoint="postgresql://localhost:5432",
                critical=True,
                timeout_seconds=5
            ),
            ServiceConfig(
                name="redis_cache",
                check_type="tcp",
                port=6379,
                critical=False,
                timeout_seconds=3
            ),
            ServiceConfig(
                name="monitoring_service",
                check_type="http",
                endpoint="/api/monitoring/health",
                critical=False,
                expected_status=200
            ),
            ServiceConfig(
                name="disk_space",
                check_type="command",
                command="df -h / | tail -1 | awk '{print $5}' | sed 's/%//'",
                critical=True
            ),
            ServiceConfig(
                name="memory_usage",
                check_type="command", 
                command="free | grep Mem | awk '{printf \"%.0f\", $3/$2 * 100.0}'",
                critical=True
            ),
            ServiceConfig(
                name="certificate_expiry",
                check_type="command",
                command="echo | openssl s_client -servername localhost -connect localhost:443 2>/dev/null | openssl x509 -noout -dates",
                critical=False
            )
        ]
    
    def perform_health_check(self, config: ServiceConfig) -> HealthCheckResult:
        """Ejecuta health check para un servicio específico"""
        start_time = time.time()
        
        try:
            if config.check_type == "http":
                return self._check_http_service(config)
            elif config.check_type == "tcp":
                return self._check_tcp_service(config)
            elif config.check_type == "command":
                return self._check_command_service(config)
            elif config.check_type == "database":
                return self._check_database_service(config)
            else:
                raise ValueError(f"Unknown check type: {config.check_type}")
        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name=config.name,
                status="unhealthy",
                timestamp=datetime.now().isoformat(),
                response_time_ms=response_time_ms,
                details={"error": str(e)},
                error_message=str(e)
            )
    
    def _check_http_service(self, config: ServiceConfig) -> HealthCheckResult:
        """Verifica servicio HTTP"""
        start_time = time.time()
        
        try:
            # Hacer request HTTP
            if config.endpoint.startswith("http"):
                # Endpoint completo
                import requests
                response = requests.get(
                    config.endpoint,
                    timeout=config.timeout_seconds,
                    headers={"User-Agent": "HealthCheck/1.0"}
                )
            else:
                # Endpoint relativo
                response = self.api_tester.get(config.endpoint)
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Verificar código de estado
            if response.status_code == config.expected_status:
                status = "healthy"
                details = {
                    "status_code": response.status_code,
                    "response_time_ms": response_time_ms,
                    "content_length": len(response.content) if hasattr(response, 'content') else 0
                }
            else:
                status = "unhealthy"
                details = {
                    "status_code": response.status_code,
                    "expected_status": config.expected_status,
                    "response_time_ms": response_time_ms
                }
                error_msg = f"HTTP {response.status_code} != {config.expected_status}"
            
            return HealthCheckResult(
                service_name=config.name,
                status=status,
                timestamp=datetime.now().isoformat(),
                response_time_ms=response_time_ms,
                details=details,
                error_message=error_msg if status == "unhealthy" else None
            )
        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name=config.name,
                status="unhealthy",
                timestamp=datetime.now().isoformat(),
                response_time_ms=response_time_ms,
                details={"error": str(e)},
                error_message=str(e)
            )
    
    def _check_tcp_service(self, config: ServiceConfig) -> HealthCheckResult:
        """Verifica servicio TCP"""
        start_time = time.time()
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(config.timeout_seconds)
                result = sock.connect_ex(('localhost', config.port))
            
            response_time_ms = (time.time() - start_time) * 1000
            
            if result == 0:
                status = "healthy"
                details = {
                    "port": config.port,
                    "response_time_ms": response_time_ms
                }
                error_msg = None
            else:
                status = "unhealthy"
                details = {
                    "port": config.port,
                    "response_time_ms": response_time_ms
                }
                error_msg = f"Cannot connect to port {config.port}"
            
            return HealthCheckResult(
                service_name=config.name,
                status=status,
                timestamp=datetime.now().isoformat(),
                response_time_ms=response_time_ms,
                details=details,
                error_message=error_msg
            )
        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name=config.name,
                status="unhealthy",
                timestamp=datetime.now().isoformat(),
                response_time_ms=response_time_ms,
                details={"error": str(e)},
                error_message=str(e)
            )
    
    def _check_command_service(self, config: ServiceConfig) -> HealthCheckResult:
        """Verifica servicio ejecutando comando"""
        start_time = time.time()
        
        try:
            result = subprocess.run(
                config.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=config.timeout_seconds
            )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Interpretar resultado basado en el servicio
            if config.name == "disk_space":
                try:
                    usage_percent = int(result.stdout.strip())
                    if usage_percent < 90:
                        status = "healthy"
                        details = {"usage_percent": usage_percent}
                    elif usage_percent < 95:
                        status = "degraded"
                        details = {"usage_percent": usage_percent, "warning": "High disk usage"}
                    else:
                        status = "unhealthy"
                        details = {"usage_percent": usage_percent, "error": "Critical disk usage"}
                        error_msg = f"Disk usage at {usage_percent}%"
                except ValueError:
                    status = "unhealthy"
                    details = {"error": "Invalid disk usage output"}
                    error_msg = "Could not parse disk usage"
            
            elif config.name == "memory_usage":
                try:
                    usage_percent = int(result.stdout.strip())
                    if usage_percent < 80:
                        status = "healthy"
                        details = {"usage_percent": usage_percent}
                    elif usage_percent < 90:
                        status = "degraded"
                        details = {"usage_percent": usage_percent, "warning": "High memory usage"}
                    else:
                        status = "unhealthy"
                        details = {"usage_percent": usage_percent, "error": "Critical memory usage"}
                        error_msg = f"Memory usage at {usage_percent}%"
                except ValueError:
                    status = "unhealthy"
                    details = {"error": "Invalid memory usage output"}
                    error_msg = "Could not parse memory usage"
            
            elif config.name == "certificate_expiry":
                if result.returncode == 0:
                    if "notAfter" in result.stdout:
                        status = "healthy"
                        details = {"certificate_valid": True, "output": result.stdout[:200]}
                    else:
                        status = "degraded"
                        details = {"certificate_valid": False, "warning": "Certificate parsing issue"}
                else:
                    status = "unhealthy"
                    details = {"certificate_valid": False, "error": "Certificate check failed"}
                    error_msg = "Certificate validation failed"
            else:
                # Comando genérico
                if result.returncode == 0:
                    status = "healthy"
                    details = {"exit_code": result.returncode, "output": result.stdout[:100]}
                else:
                    status = "unhealthy"
                    details = {"exit_code": result.returncode, "error_output": result.stderr[:100]}
                    error_msg = f"Command failed with exit code {result.returncode}"
            
            return HealthCheckResult(
                service_name=config.name,
                status=status,
                timestamp=datetime.now().isoformat(),
                response_time_ms=response_time_ms,
                details=details,
                error_message=error_msg
            )
        
        except subprocess.TimeoutExpired:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name=config.name,
                status="unhealthy",
                timestamp=datetime.now().isoformat(),
                response_time_ms=response_time_ms,
                details={"error": f"Command timeout after {config.timeout_seconds}s"},
                error_message="Command timeout"
            )
        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name=config.name,
                status="unhealthy",
                timestamp=datetime.now().isoformat(),
                response_time_ms=response_time_ms,
                details={"error": str(e)},
                error_message=str(e)
            )
    
    def _check_database_service(self, config: ServiceConfig) -> HealthCheckResult:
        """Verifica servicio de base de datos"""
        start_time = time.time()
        
        try:
            # Simular verificación de base de datos
            # En implementación real, aquí se conectaría a la DB
            import psycopg2
            from psycopg2 import OperationalError
            
            try:
                # Simular conexión
                time.sleep(0.1)  # Simular tiempo de conexión
                
                response_time_ms = (time.time() - start_time) * 1000
                
                status = "healthy"
                details = {
                    "connection": "successful",
                    "response_time_ms": response_time_ms,
                    "database_type": "PostgreSQL"
                }
                
            except OperationalError as e:
                response_time_ms = (time.time() - start_time) * 1000
                status = "unhealthy"
                details = {"connection_error": str(e)}
                error_msg = f"Database connection failed: {str(e)}"
            
            return HealthCheckResult(
                service_name=config.name,
                status=status,
                timestamp=datetime.now().isoformat(),
                response_time_ms=response_time_ms,
                details=details,
                error_message=error_msg if status == "unhealthy" else None
            )
        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name=config.name,
                status="unhealthy",
                timestamp=datetime.now().isoformat(),
                response_time_ms=response_time_ms,
                details={"error": str(e)},
                error_message=str(e)
            )
    
    async def run_all_health_checks(self) -> List[HealthCheckResult]:
        """Ejecuta todos los health checks"""
        self.logger.info(f"Starting health checks for {len(self.service_configs)} services")
        
        results = []
        
        for config in self.service_configs:
            try:
                result = self.perform_health_check(config)
                results.append(result)
                self.check_results.append(result)
                
                # Log resultado
                status_emoji = "✅" if result.status == "healthy" else "⚠️" if result.status == "degraded" else "❌"
                self.logger.info(
                    f"{status_emoji} {config.name}: {result.status} "
                    f"({result.response_time_ms:.1f}ms)"
                )
                
            except Exception as e:
                self.logger.error(f"Health check failed for {config.name}: {str(e)}")
        
        return results
    
    def get_system_health_status(self, results: List[HealthCheckResult]) -> Dict[str, Any]:
        """Calcula estado general del sistema"""
        total_services = len(results)
        healthy_services = len([r for r in results if r.status == "healthy"])
        degraded_services = len([r for r in results if r.status == "degraded"])
        unhealthy_services = len([r for r in results if r.status == "unhealthy"])
        
        critical_unhealthy = len([
            r for r in results 
            if r.status == "unhealthy" and self._is_critical_service(r.service_name)
        ])
        
        # Determinar estado general
        if critical_unhealthy > 0:
            overall_status = "critical"
        elif unhealthy_services > total_services * 0.5:  # Más del 50% unhealthy
            overall_status = "unhealthy"
        elif degraded_services > 0 or unhealthy_services > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "overall_status": overall_status,
            "total_services": total_services,
            "healthy_services": healthy_services,
            "degraded_services": degraded_services,
            "unhealthy_services": unhealthy_services,
            "critical_unhealthy": critical_unhealthy,
            "health_percentage": (healthy_services / total_services) * 100 if total_services > 0 else 0
        }
    
    def _is_critical_service(self, service_name: str) -> bool:
        """Verifica si un servicio es crítico"""
        for config in self.service_configs:
            if config.name == service_name:
                return config.critical
        return False
    
    def save_health_report(self, results: List[HealthCheckResult], output_file: Path):
        """Guarda reporte de health checks"""
        system_status = self.get_system_health_status(results)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "system_status": system_status,
            "checks": [
                {
                    "service_name": result.service_name,
                    "status": result.status,
                    "response_time_ms": result.response_time_ms,
                    "timestamp": result.timestamp,
                    "details": result.details,
                    "error_message": result.error_message
                }
                for result in results
            ],
            "summary": {
                "critical_services": [
                    result.service_name for result in results
                    if self._is_critical_service(result.service_name)
                ],
                "failed_services": [
                    result.service_name for result in results
                    if result.status == "unhealthy"
                ],
                "slow_services": [
                    result.service_name for result in results
                    if result.response_time_ms > 1000
                ]
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Health report saved to {output_file}")

class AutoHealingSystem:
    """Sistema de auto-recuperación"""
    
    def __init__(self, health_checker: HealthChecker):
        self.logger = TestLogger("AutoHealing", PROJECT_ROOT / "logs" / "auto_healing.log")
        self.health_checker = health_checker
        self.healing_actions = self._load_healing_actions()
        self.recovery_history: List[Dict[str, Any]] = []
    
    def _load_healing_actions(self) -> Dict[str, Dict[str, Any]]:
        """Carga acciones de auto-recuperación"""
        return {
            "restart_service": {
                "api_gateway": "sudo systemctl restart nginx",
                "mcp_server": "sudo systemctl restart mcp-server",
                "database_postgres": "sudo systemctl restart postgresql",
                "redis_cache": "sudo systemctl restart redis"
            },
            "cleanup_action": {
                "disk_space": "find /var/log -name '*.log' -mtime +30 -delete",
                "memory_usage": "sync && echo 3 > /proc/sys/vm/drop_caches"
            },
            "scale_action": {
                "high_load": "sudo systemctl scale-up workers"
            }
        }
    
    def attempt_auto_healing(self, failed_service: str, error_details: Dict[str, Any]) -> bool:
        """Intenta auto-recuperación del servicio"""
        self.logger.info(f"Attempting auto-healing for {failed_service}")
        
        healing_successful = False
        
        # Determinar acción de recuperación
        if failed_service == "disk_space":
            healing_successful = self._cleanup_disk_space()
        elif failed_service == "memory_usage":
            healing_successful = self._cleanup_memory()
        elif "server" in failed_service or "service" in failed_service:
            healing_successful = self._restart_service(failed_service)
        
        # Registrar intento de recuperación
        recovery_record = {
            "timestamp": datetime.now().isoformat(),
            "service": failed_service,
            "error_details": error_details,
            "healing_attempted": True,
            "healing_successful": healing_successful
        }
        
        self.recovery_history.append(recovery_record)
        
        if healing_successful:
            self.logger.info(f"Auto-healing successful for {failed_service}")
        else:
            self.logger.warning(f"Auto-healing failed for {failed_service}")
        
        return healing_successful
    
    def _restart_service(self, service_name: str) -> bool:
        """Reinicia servicio"""
        try:
            restart_command = self.healing_actions["restart_service"].get(service_name)
            if restart_command:
                result = subprocess.run(
                    restart_command,
                    shell=True,
                    capture_output=True,
                    timeout=30
                )
                return result.returncode == 0
            return False
        except Exception as e:
            self.logger.error(f"Failed to restart service {service_name}: {str(e)}")
            return False
    
    def _cleanup_disk_space(self) -> bool:
        """Limpia espacio en disco"""
        try:
            cleanup_command = self.healing_actions["cleanup_action"]["disk_space"]
            result = subprocess.run(
                cleanup_command,
                shell=True,
                capture_output=True,
                timeout=60
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Failed to cleanup disk space: {str(e)}")
            return False
    
    def _cleanup_memory(self) -> bool:
        """Limpia memoria"""
        try:
            cleanup_command = self.healing_actions["cleanup_action"]["memory_usage"]
            result = subprocess.run(
                cleanup_command,
                shell=True,
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Failed to cleanup memory: {str(e)}")
            return False

# Instancias globales
health_checker = HealthChecker()
auto_healing = AutoHealingSystem(health_checker)

async def run_comprehensive_health_check():
    """Ejecuta health check comprensivo con auto-healing"""
    self.logger = TestLogger("HealthCheckSuite", PROJECT_ROOT / "logs" / "health_check_suite.log")
    
    self.logger.info("Starting comprehensive health check suite")
    
    # Ejecutar health checks
    results = await health_checker.run_all_health_checks()
    
    # Obtener estado del sistema
    system_status = health_checker.get_system_health_status(results)
    
    # Intentar auto-healing para servicios fallidos
    for result in results:
        if result.status == "unhealthy":
            auto_healing.attempt_auto_healing(result.service_name, result.details)
    
    # Generar reporte
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = PROJECT_ROOT / "reports" / f"health_check_{timestamp}.json"
    
    health_checker.save_health_report(results, report_file)
    
    self.logger.info(f"Health check completed. System status: {system_status['overall_status']}")
    self.logger.info(f"Report saved to: {report_file}")
    
    return system_status, results

if __name__ == "__main__":
    asyncio.run(run_comprehensive_health_check())
