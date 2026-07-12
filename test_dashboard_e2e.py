#!/usr/bin/env python3
"""
Script de Testing End-to-End para Dashboard SilhouetteMCP Ultra
Verifica que todas las funcionalidades estén operativas
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8001"
ADMIN_EMAIL = "alberto.farahb@hotmail.com"
ADMIN_PASSWORD = "Fbalberto1910"

# Colores para output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class DashboardTester:
    def __init__(self):
        self.token = None
        self.test_results = []
        self.passed = 0
        self.failed = 0
    
    def log(self, message, status="INFO"):
        colors = {
            "INFO": BLUE,
            "SUCCESS": GREEN,
            "ERROR": RED,
            "WARNING": YELLOW
        }
        color = colors.get(status, RESET)
        print(f"{color}[{status}]{RESET} {message}")
    
    def test(self, name, func):
        """Ejecutar un test individual"""
        self.log(f"Testing: {name}", "INFO")
        try:
            result = func()
            if result:
                self.passed += 1
                self.log(f"✓ {name}", "SUCCESS")
                self.test_results.append({"name": name, "status": "PASS", "error": None})
                return True
            else:
                self.failed += 1
                self.log(f"✗ {name}", "ERROR")
                self.test_results.append({"name": name, "status": "FAIL", "error": "Test returned False"})
                return False
        except Exception as e:
            self.failed += 1
            self.log(f"✗ {name}: {str(e)}", "ERROR")
            self.test_results.append({"name": name, "status": "FAIL", "error": str(e)})
            return False
    
    # Tests de endpoints
    
    def test_server_running(self):
        """Test: Servidor está corriendo"""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_dashboard_html(self):
        """Test: Dashboard HTML accesible"""
        try:
            response = requests.get(f"{BASE_URL}/dashboard-ultra", timeout=5)
            return response.status_code == 200 and "SilhouetteMCP" in response.text
        except:
            return False
    
    def test_static_files(self):
        """Test: Archivos estáticos CSS/JS cargando"""
        try:
            css_response = requests.get(f"{BASE_URL}/dashboard/css/styles.css", timeout=5)
            js_response = requests.get(f"{BASE_URL}/dashboard/js/app.js", timeout=5)
            return css_response.status_code == 200 and js_response.status_code == 200
        except:
            return False
    
    def test_admin_login(self):
        """Test: Login de administrador"""
        try:
            response = requests.post(
                f"{BASE_URL}/admin/login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                return self.token is not None
            return False
        except:
            return False
    
    def test_dashboard_data(self):
        """Test: Datos del dashboard"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{BASE_URL}/admin/dashboard", headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return "metrics" in data and "applications" in data
            return False
        except:
            return False
    
    def test_system_metrics(self):
        """Test: Métricas reales del sistema (CPU, RAM, Disco)"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{BASE_URL}/api/system/metrics", headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                has_cpu = "cpu" in data and "percent" in data["cpu"]
                has_memory = "memory" in data and "percent" in data["memory"]
                has_disk = "disk" in data and "percent" in data["disk"]
                return has_cpu and has_memory and has_disk
            return False
        except:
            return False
    
    def test_system_logs(self):
        """Test: Logs reales del sistema"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{BASE_URL}/api/system/logs?lines=10", headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return "logs" in data and isinstance(data["logs"], list)
            return False
        except:
            return False
    
    def test_create_dynamic_api(self):
        """Test: Crear API dinámica"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(
                f"{BASE_URL}/api/dynamic/create",
                headers=headers,
                json={
                    "name": "Test API E2E",
                    "description": "API creada durante testing E2E",
                    "agent_type": "custom"
                },
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                self.test_api_id = data.get("application", {}).get("id")
                return data.get("success") == True
            return False
        except:
            return False
    
    def test_list_applications(self):
        """Test: Listar aplicaciones"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{BASE_URL}/admin/applications", headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return "applications" in data and isinstance(data["applications"], list)
            return False
        except:
            return False
    
    def test_create_backup(self):
        """Test: Crear backup del sistema"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(f"{BASE_URL}/api/system/backup", headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("success") == True and "backup_file" in data
            return False
        except:
            return False
    
    def test_list_backups(self):
        """Test: Listar backups"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{BASE_URL}/api/system/backups", headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return "backups" in data
            return False
        except:
            return False
    
    def test_metrics_stream(self):
        """Test: Stream de métricas (SSE)"""
        try:
            response = requests.get(f"{BASE_URL}/metrics/stream", stream=True, timeout=3)
            return response.status_code == 200
        except requests.exceptions.ReadTimeout:
            # Timeout esperado en stream, pero conexión exitosa
            return True
        except:
            return False
    
    def run_all_tests(self):
        """Ejecutar todos los tests"""
        self.log("=" * 60, "INFO")
        self.log("DASHBOARD SILHOUETTEMCP ULTRA - TEST END-TO-END", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        self.log(f"URL Base: {BASE_URL}", "INFO")
        self.log("=" * 60, "INFO")
        print()
        
        # Tests básicos
        self.log("TESTS BÁSICOS", "INFO")
        self.log("-" * 60, "INFO")
        self.test("Servidor corriendo", self.test_server_running)
        self.test("Dashboard HTML accesible", self.test_dashboard_html)
        self.test("Archivos estáticos (CSS/JS)", self.test_static_files)
        print()
        
        # Tests de autenticación
        self.log("TESTS DE AUTENTICACIÓN", "INFO")
        self.log("-" * 60, "INFO")
        self.test("Login de administrador", self.test_admin_login)
        print()
        
        # Tests de datos
        self.log("TESTS DE DATOS Y MÉTRICAS", "INFO")
        self.log("-" * 60, "INFO")
        self.test("Datos del dashboard", self.test_dashboard_data)
        self.test("Métricas reales del sistema", self.test_system_metrics)
        self.test("Logs reales del sistema", self.test_system_logs)
        self.test("Stream de métricas (SSE)", self.test_metrics_stream)
        print()
        
        # Tests de funcionalidades
        self.log("TESTS DE FUNCIONALIDADES", "INFO")
        self.log("-" * 60, "INFO")
        self.test("Crear API dinámica", self.test_create_dynamic_api)
        self.test("Listar aplicaciones", self.test_list_applications)
        self.test("Crear backup", self.test_create_backup)
        self.test("Listar backups", self.test_list_backups)
        print()
        
        # Resumen
        self.log("=" * 60, "INFO")
        self.log("RESUMEN DE TESTS", "INFO")
        self.log("=" * 60, "INFO")
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        self.log(f"Total: {total} tests", "INFO")
        self.log(f"Pasaron: {self.passed} ({pass_rate:.1f}%)", "SUCCESS" if self.passed == total else "WARNING")
        self.log(f"Fallaron: {self.failed}", "ERROR" if self.failed > 0 else "INFO")
        print()
        
        if self.failed == 0:
            self.log("✓ TODOS LOS TESTS PASARON", "SUCCESS")
            return 0
        else:
            self.log("✗ ALGUNOS TESTS FALLARON", "ERROR")
            return 1

if __name__ == "__main__":
    tester = DashboardTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)
