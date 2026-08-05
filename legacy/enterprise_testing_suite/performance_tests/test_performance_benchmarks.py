"""
Performance Tests y Benchmarks para Integraciones Enterprise
"""

import pytest
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import json

from utils.base_utils import (
    TestResult, TestDataGenerator, MetricsCollector, APITester, test_logger
)
from config.test_config import *

class TestPerformanceBenchmarks:
    """Tests de benchmarks de performance"""
    
    @pytest.fixture
    def api_tester(self):
        return APITester(BASE_URL)
    
    def test_mcp_throughput_benchmark(self, api_tester):
        """Benchmark de throughput MCP"""
        # Arrange
        num_requests = 1000
        test_data = TestDataGenerator.generate_mcp_request_data()
        start_time = time.time()
        
        # Act
        successful_requests = 0
        failed_requests = 0
        response_times = []
        
        for i in range(num_requests):
            request_start = time.time()
            
            try:
                # Simular request MCP
                response = api_tester.post("/api/mcp/execute", json={
                    "tool": "python_executor",
                    "code": "print(f'Request {i}')",
                    "timeout": 30
                })
                
                request_duration = time.time() - request_start
                response_times.append(request_duration)
                
                if response.status_code == 200:
                    successful_requests += 1
                else:
                    failed_requests += 1
                    
            except Exception as e:
                failed_requests += 1
                test_logger.warning(f"Request {i} failed: {str(e)}")
        
        total_time = time.time() - start_time
        
        # Calcular métricas
        throughput = successful_requests / total_time
        avg_response_time = statistics.mean(response_times) if response_times else 0
        p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else 0
        
        # Assert
        assert successful_requests / num_requests >= 0.99, "Throughput below 99%"
        assert throughput >= PERFORMANCE_CONFIG["throughput_threshold"]
        assert avg_response_time <= PERFORMANCE_CONFIG["response_time_threshold"]
        
        # Registrar resultados
        benchmark_result = TestResult(
            test_name="mcp_throughput_benchmark",
            test_type="performance",
            status="PASSED",
            duration=total_time,
            timestamp=datetime.now().isoformat(),
            details={
                "throughput": throughput,
                "avg_response_time": avg_response_time,
                "p95_response_time": p95_response_time,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests
            }
        )
        
        test_logger.info(f"MCP throughput benchmark: {throughput:.2f} req/s, "
                        f"avg: {avg_response_time:.3f}s, p95: {p95_response_time:.3f}s")
    
    def test_database_performance_benchmark(self, api_tester):
        """Benchmark de performance de base de datos"""
        # Arrange
        num_operations = 500
        start_time = time.time()
        
        # Act
        operation_times = []
        
        for i in range(num_operations):
            op_start = time.time()
            
            try:
                # Operaciones CRUD aleatorias
                operation = i % 4
                
                if operation == 0:  # CREATE
                    user_data = TestDataGenerator.generate_user_data()
                    response = api_tester.post("/api/users", json=user_data)
                elif operation == 1:  # READ
                    response = api_tester.get("/api/users")
                elif operation == 2:  # UPDATE
                    user_data = TestDataGenerator.generate_user_data()
                    response = api_tester.put(f"/api/users/{user_data['id']}", json=user_data)
                else:  # DELETE
                    response = api_tester.delete("/api/users/123")
                
                op_duration = time.time() - op_start
                operation_times.append(op_duration)
                
            except Exception as e:
                test_logger.warning(f"DB operation {i} failed: {str(e)}")
        
        total_time = time.time() - start_time
        
        # Calcular métricas
        db_throughput = num_operations / total_time
        avg_op_time = statistics.mean(operation_times) if operation_times else 0
        p99_op_time = statistics.quantiles(operation_times, n=100)[98] if len(operation_times) > 100 else 0
        
        # Assert
        assert avg_op_time < 0.5, f"Average DB operation time too high: {avg_op_time:.3f}s"
        assert db_throughput > 10, f"DB throughput too low: {db_throughput:.2f} ops/s"
        
        test_logger.info(f"Database performance: {db_throughput:.2f} ops/s, "
                        f"avg: {avg_op_time:.3f}s, p99: {p99_op_time:.3f}s")
    
    def test_memory_performance_benchmark(self):
        """Benchmark de uso de memoria"""
        # Arrange
        import psutil
        process = psutil.Process()
        
        # Medir memoria inicial
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Act - Simular carga de trabajo intensa
        memory_usage_data = []
        
        for i in range(1000):
            # Simular operaciones que consumen memoria
            data_chunk = [f"data_{j}" for j in range(1000)]
            memory_usage_data.append(data_chunk)
            
            # Medir memoria cada 100 iteraciones
            if i % 100 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_usage_data.append(current_memory)
                
                # Forzar garbage collection
                import gc
                gc.collect()
        
        # Cleanup
        del memory_usage_data
        import gc
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024
        peak_memory = max(memory_usage_data) if memory_usage_data else final_memory
        memory_increase = final_memory - initial_memory
        
        # Assert
        assert memory_increase < 50, f"Memory increase too high: {memory_increase:.2f}MB"
        assert peak_memory < initial_memory + 100, f"Peak memory too high: {peak_memory:.2f}MB"
        
        test_logger.info(f"Memory performance: +{memory_increase:.2f}MB, peak: {peak_memory:.2f}MB")

class TestLoadTesting:
    """Tests de carga progresiva hasta 100+ usuarios"""
    
    @pytest.mark.parametrize("concurrent_users", [10, 25, 50, 100, 250, 500, 1000])
    def test_progressive_load_test(self, concurrent_users):
        """Test de carga progresiva"""
        # Arrange
        api_tester = APITester(BASE_URL)
        requests_per_user = 20
        results = {
            "successful": 0,
            "failed": 0,
            "response_times": [],
            "status_codes": {}
        }
        
        def simulate_user(user_id):
            user_results = {
                "successful": 0,
                "failed": 0,
                "times": []
            }
            
            for i in range(requests_per_user):
                start_time = time.time()
                
                try:
                    response = api_tester.get(f"/api/load-test/user/{user_id}/request/{i}")
                    duration = time.time() - start_time
                    
                    if response.status_code == 200:
                        user_results["successful"] += 1
                        user_results["times"].append(duration)
                    else:
                        user_results["failed"] += 1
                        
                    # Registrar código de estado
                    results["status_codes"][response.status_code] = \
                        results["status_codes"].get(response.status_code, 0) + 1
                        
                except Exception:
                    user_results["failed"] += 1
            
            return user_results
        
        # Act
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(simulate_user, i) for i in range(concurrent_users)]
            
            for future in as_completed(futures):
                try:
                    user_result = future.result()
                    results["successful"] += user_result["successful"]
                    results["failed"] += user_result["failed"]
                    results["response_times"].extend(user_result["times"])
                except Exception as e:
                    results["failed"] += requests_per_user
                    test_logger.error(f"User thread failed: {str(e)}")
        
        total_time = time.time() - start_time
        
        # Calcular métricas
        total_requests = concurrent_users * requests_per_user
        success_rate = results["successful"] / total_requests
        throughput = results["successful"] / total_time
        error_rate = (total_requests - results["successful"]) / total_requests * 100
        
        # Assert
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below threshold"
        assert error_rate <= PERFORMANCE_CONFIG["error_rate_threshold"], \
            f"Error rate {error_rate:.2f}% above threshold"
        
        # Métricas de tiempo de respuesta
        if results["response_times"]:
            avg_response_time = statistics.mean(results["response_times"])
            p95_response_time = statistics.quantiles(results["response_times"], n=20)[18]
            
            assert avg_response_time < PERFORMANCE_CONFIG["response_time_threshold"]
            assert p95_response_time < PERFORMANCE_CONFIG["response_time_threshold"] * 2
        
        # Registrar resultados
        test_logger.info(f"Load test {concurrent_users} users: "
                        f"success_rate={success_rate:.2%}, "
                        f"throughput={throughput:.2f} req/s, "
                        f"avg_time={avg_response_time:.3f}s" if results["response_times"] else "")
    
    def test_sustained_load_test(self):
        """Test de carga sostenida"""
        # Arrange
        api_tester = APITester(BASE_URL)
        concurrent_users = 50
        test_duration = 60  # 1 minuto
        requests_per_minute = 100
        
        results = {
            "requests_made": 0,
            "successful": 0,
            "failed": 0,
            "response_times": []
        }
        
        def sustained_user():
            start_time = time.time()
            while time.time() - start_time < test_duration:
                try:
                    request_start = time.time()
                    response = api_tester.get("/api/sustained-load/test")
                    request_time = time.time() - request_start
                    
                    results["requests_made"] += 1
                    
                    if response.status_code == 200:
                        results["successful"] += 1
                        results["response_times"].append(request_time)
                    else:
                        results["failed"] += 1
                        
                except Exception:
                    results["requests_made"] += 1
                    results["failed"] += 1
                
                # Pausa entre requests
                time.sleep(60 / requests_per_minute)
        
        # Act
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(sustained_user) for _ in range(concurrent_users)]
            
            # Esperar a que termine
            for future in as_completed(futures):
                future.result()
        
        actual_duration = time.time() - start_time
        
        # Calcular métricas
        throughput = results["successful"] / actual_duration
        error_rate = results["failed"] / results["requests_made"] * 100 if results["requests_made"] > 0 else 0
        
        # Assert
        assert error_rate < 5.0, f"Error rate too high: {error_rate:.2f}%"
        assert throughput > 50, f"Throughput too low: {throughput:.2f} req/s"
        
        # Verificar que el sistema no se degrada significativamente
        if len(results["response_times"]) > 20:
            first_half = results["response_times"][:len(results["response_times"])//2]
            second_half = results["response_times"][len(results["response_times"])//2:]
            
            first_avg = statistics.mean(first_half)
            second_avg = statistics.mean(second_half)
            
            # La segunda mitad no debería ser significativamente más lenta
            assert second_avg < first_avg * 1.5, "Performance degradation detected"
        
        test_logger.info(f"Sustained load test: {results['successful']} successful, "
                        f"{throughput:.2f} req/s, {error_rate:.2f}% errors")

class TestStressTesting:
    """Tests de estrés del sistema"""
    
    def test_memory_stress_test(self):
        """Test de estrés de memoria"""
        # Arrange
        import psutil
        process = psutil.Process()
        
        memory_usage = []
        stress_data = []
        
        def allocate_memory():
            # Simular alta carga de memoria
            for i in range(100):
                data = [0] * 1000000  # 1M integers = ~4MB
                stress_data.append(data)
                
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_usage.append(current_memory)
                
                if current_memory > 500:  # Límite de seguridad
                    break
                
                time.sleep(0.1)
        
        def perform_io_intensive_operations():
            # Operaciones intensivas de I/O
            for i in range(1000):
                # Simular operaciones de disco
                with open(f"/tmp/stress_test_{i}.tmp", "w") as f:
                    f.write("x" * 10000)
                
                # Leer el archivo
                with open(f"/tmp/stress_test_{i}.tmp", "r") as f:
                    f.read()
                
                # Limpiar
                import os
                try:
                    os.remove(f"/tmp/stress_test_{i}.tmp")
                except:
                    pass
        
        # Act
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(allocate_memory),
                executor.submit(allocate_memory),
                executor.submit(perform_io_intensive_operations),
                executor.submit(perform_io_intensive_operations)
            ]
            
            # Esperar a que terminen
            for future in as_completed(futures):
                future.result()
        
        duration = time.time() - start_time
        
        # Cleanup
        del stress_data
        import gc
        gc.collect()
        
        # Assert
        peak_memory = max(memory_usage) if memory_usage else 0
        assert peak_memory < 1000, f"Peak memory too high: {peak_memory:.2f}MB"
        assert duration < 30, f"Stress test took too long: {duration:.2f}s"
        
        test_logger.info(f"Memory stress test: peak={peak_memory:.2f}MB, duration={duration:.2f}s")
    
    def test_concurrent_connection_stress(self):
        """Test de estrés de conexiones concurrentes"""
        # Arrange
        api_tester = APITester(BASE_URL)
        num_connections = 200
        
        results = {
            "successful_connections": 0,
            "failed_connections": 0,
            "connection_times": []
        }
        
        def make_connection(conn_id):
            try:
                start_time = time.time()
                
                # Simular múltiples requests por conexión
                for i in range(5):
                    response = api_tester.get(f"/api/connection-test/{conn_id}/{i}")
                    
                    if response.status_code != 200:
                        raise Exception(f"Request {i} failed with status {response.status_code}")
                    
                    time.sleep(0.01)  # Pequeña pausa
                
                connection_time = time.time() - start_time
                results["successful_connections"] += 1
                results["connection_times"].append(connection_time)
                
            except Exception as e:
                results["failed_connections"] += 1
                test_logger.warning(f"Connection {conn_id} failed: {str(e)}")
        
        # Act
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_connections) as executor:
            futures = [executor.submit(make_connection, i) for i in range(num_connections)]
            
            for future in as_completed(futures):
                future.result()
        
        total_time = time.time() - start_time
        
        # Assert
        success_rate = results["successful_connections"] / num_connections
        assert success_rate >= 0.90, f"Connection success rate too low: {success_rate:.2%}"
        
        if results["connection_times"]:
            avg_connection_time = statistics.mean(results["connection_times"])
            assert avg_connection_time < 10.0, f"Average connection time too high: {avg_connection_time:.2f}s"
        
        test_logger.info(f"Connection stress test: {results['successful_connections']}/{num_connections} successful")

class TestPerformanceRegression:
    """Tests de regresión de performance"""
    
    def test_performance_regression_detection(self):
        """Test de detección de regresión de performance"""
        # Arrange - Datos históricos simulados
        historical_baseline = {
            "api_response_time": 0.15,  # segundos
            "db_query_time": 0.08,
            "memory_usage": 150,  # MB
            "cpu_usage": 25  # porcentaje
        }
        
        # Act - Ejecutar pruebas actuales
        current_metrics = {}
        
        # Test API response time
        api_tester = APITester(BASE_URL)
        start_time = time.time()
        api_tester.get("/api/health")
        api_response_time = time.time() - start_time
        current_metrics["api_response_time"] = api_response_time
        
        # Test DB query time
        db_start = time.time()
        api_tester.get("/api/users")
        db_query_time = time.time() - db_start
        current_metrics["db_query_time"] = db_query_time
        
        # Test memory usage
        import psutil
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024
        current_metrics["memory_usage"] = memory_usage
        
        # Test CPU usage
        cpu_start = psutil.cpu_percent(interval=1)
        current_metrics["cpu_usage"] = cpu_start
        
        # Assert - Verificar regresiones
        regressions = []
        
        # Tolerancia del 20% para regresiones
        tolerance = 0.20
        
        for metric, current_value in current_metrics.items():
            baseline_value = historical_baseline[metric]
            regression_threshold = baseline_value * (1 + tolerance)
            
            if current_value > regression_threshold:
                regressions.append({
                    "metric": metric,
                    "baseline": baseline_value,
                    "current": current_value,
                    "regression": ((current_value - baseline_value) / baseline_value) * 100
                })
        
        assert len(regressions) == 0, f"Performance regressions detected: {regressions}"
        
        test_logger.info(f"Performance regression test passed. Current metrics: {current_metrics}")

if __name__ == "__main__":
    pytest.main([__file__])
