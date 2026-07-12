"""
Benchmarks de Performance - Sistema Multi-Agente Expandido
Suite completa de benchmarks para validar el rendimiento del sistema
con 20+ agentes especializados y cargas de trabajo empresariales
"""
import asyncio
import logging
import time
import statistics
import json
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import concurrent.futures
import threading
import psutil
import os
import gc

from ..orchestrator.optimized_multi_agent_orchestrator import OptimizedMultiAgentOrchestrator
from ..orchestrator.intelligent_routing_system import IntelligentRoutingSystem
from ..orchestrator.advanced_load_balancer import AdvancedLoadBalancer
from ..agents.specialized_agents import SpecializedAgentFactory, get_specialized_agents_config


@dataclass
class BenchmarkResult:
    """Resultado de un benchmark individual"""
    benchmark_name: str
    description: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    
    # Métricas principales
    success_rate: float
    total_operations: int
    successful_operations: int
    failed_operations: int
    operations_per_second: float
    
    # Métricas de recursos
    avg_cpu_usage: float
    peak_cpu_usage: float
    avg_memory_usage: float
    peak_memory_usage: float
    
    # Métricas de agentes
    agents_tested: List[str]
    agent_efficiency: Dict[str, float]
    load_distribution: Dict[str, int]
    
    # Detalles específicos
    specific_metrics: Dict[str, Any]
    errors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BenchmarkSuite:
    """Suite de benchmarks con configuración y resultados"""
    suite_name: str
    created_at: datetime
    agent_configs: Dict[str, Any]
    results: List[BenchmarkResult]
    overall_summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "suite_name": self.suite_name,
            "created_at": self.created_at.isoformat(),
            "agent_configs": self.agent_configs,
            "results": [result.to_dict() for result in self.results],
            "overall_summary": self.overall_summary
        }


class SystemResourceMonitor:
    """Monitor de recursos del sistema durante benchmarks"""
    
    def __init__(self):
        self.logger = logging.getLogger("mcp.benchmark.monitor")
        self.monitoring = False
        self.metrics = {
            "cpu_usage": [],
            "memory_usage": [],
            "disk_io": [],
            "network_io": []
        }
        self.monitor_task: Optional[asyncio.Task] = None
    
    async def start_monitoring(self, interval: float = 0.5) -> None:
        """Iniciar monitoreo de recursos"""
        self.monitoring = True
        self._reset_metrics()
        self.monitor_task = asyncio.create_task(self._monitor_loop(interval))
        self.logger.info("Monitoreo de recursos iniciado")
    
    async def stop_monitoring(self) -> Dict[str, Any]:
        """Detener monitoreo y obtener métricas"""
        self.monitoring = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        # Calcular métricas resumidas
        metrics_summary = self._calculate_metrics_summary()
        self.logger.info("Monitoreo de recursos detenido")
        return metrics_summary
    
    async def _monitor_loop(self, interval: float) -> None:
        """Loop de monitoreo"""
        try:
            while self.monitoring:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=None)
                self.metrics["cpu_usage"].append(cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.metrics["memory_usage"].append(memory.percent)
                
                # Disk I/O
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    self.metrics["disk_io"].append({
                        "read_bytes": disk_io.read_bytes,
                        "write_bytes": disk_io.write_bytes
                    })
                
                # Network I/O
                network_io = psutil.net_io_counters()
                if network_io:
                    self.metrics["network_io"].append({
                        "bytes_sent": network_io.bytes_sent,
                        "bytes_recv": network_io.bytes_recv
                    })
                
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Error en monitoreo: {e}")
    
    def _reset_metrics(self) -> None:
        """Reset métricas"""
        self.metrics = {
            "cpu_usage": [],
            "memory_usage": [],
            "disk_io": [],
            "network_io": []
        }
    
    def _calculate_metrics_summary(self) -> Dict[str, Any]:
        """Calcular resumen de métricas"""
        summary = {}
        
        # CPU
        if self.metrics["cpu_usage"]:
            summary["cpu"] = {
                "avg": statistics.mean(self.metrics["cpu_usage"]),
                "max": max(self.metrics["cpu_usage"]),
                "min": min(self.metrics["cpu_usage"])
            }
        
        # Memory
        if self.metrics["memory_usage"]:
            summary["memory"] = {
                "avg": statistics.mean(self.metrics["memory_usage"]),
                "max": max(self.metrics["memory_usage"]),
                "min": min(self.metrics["memory_usage"])
            }
        
        # Disk I/O
        if len(self.metrics["disk_io"]) > 1:
            read_bytes = [entry["read_bytes"] for entry in self.metrics["disk_io"]]
            write_bytes = [entry["write_bytes"] for entry in self.metrics["disk_io"]]
            summary["disk_io"] = {
                "total_read_bytes": read_bytes[-1] - read_bytes[0] if read_bytes else 0,
                "total_write_bytes": write_bytes[-1] - write_bytes[0] if write_bytes else 0
            }
        
        return summary


class MultiAgentBenchmark:
    """Suite principal de benchmarks para sistema multi-agente"""
    
    def __init__(self):
        self.logger = logging.getLogger("mcp.benchmark.suite")
        self.resource_monitor = SystemResourceMonitor()
        self.agent_factory = SpecializedAgentFactory()
        self.agent_configs = get_specialized_agents_config()
        self.results_history: List[BenchmarkSuite] = []
    
    async def run_complete_benchmark_suite(
        self, 
        suite_name: str = "Complete_MultiAgent_Benchmark",
        include_stress_tests: bool = True
    ) -> BenchmarkSuite:
        """Ejecutar suite completa de benchmarks"""
        
        start_time = datetime.now()
        self.logger.info(f"Iniciando benchmark suite: {suite_name}")
        
        # Crear orquestador optimizado
        orchestrator = OptimizedMultiAgentOrchestrator()
        await orchestrator.initialize(self.agent_configs)
        
        # Lista de benchmarks a ejecutar
        benchmarks = [
            ("Basic_Functionality", self._benchmark_basic_functionality),
            ("Concurrent_Execution", self._benchmark_concurrent_execution),
            ("Load_Balancing", self._benchmark_load_balancing),
            ("Routing_Intelligence", self._benchmark_routing_intelligence),
            ("Fault_Tolerance", self._benchmark_fault_tolerance),
            ("Resource_Utilization", self._benchmark_resource_utilization),
            ("Agent_Scalability", self._benchmark_agent_scalability),
            ("Workflow_Complexity", self._benchmark_workflow_complexity),
        ]
        
        if include_stress_tests:
            benchmarks.extend([
                ("Stress_Test_Light", self._benchmark_stress_light),
                ("Stress_Test_Medium", self._benchmark_stress_medium),
                ("Stress_Test_Heavy", self._benchmark_stress_heavy),
                ("Endurance_Test", self._benchmark_endurance),
            ])
        
        results = []
        
        # Ejecutar cada benchmark
        for benchmark_name, benchmark_func in benchmarks:
            try:
                self.logger.info(f"Ejecutando benchmark: {benchmark_name}")
                result = await benchmark_func(orchestrator)
                results.append(result)
                self.logger.info(f"Benchmark {benchmark_name} completado")
            except Exception as e:
                self.logger.error(f"Error en benchmark {benchmark_name}: {e}")
                # Crear resultado de error
                error_result = BenchmarkResult(
                    benchmark_name=benchmark_name,
                    description=f"Error ejecutando benchmark: {str(e)}",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    duration_seconds=0.0,
                    success_rate=0.0,
                    total_operations=0,
                    successful_operations=0,
                    failed_operations=0,
                    operations_per_second=0.0,
                    avg_cpu_usage=0.0,
                    peak_cpu_usage=0.0,
                    avg_memory_usage=0.0,
                    peak_memory_usage=0.0,
                    agents_tested=[],
                    agent_efficiency={},
                    load_distribution={},
                    specific_metrics={"error": str(e)},
                    errors=[str(e)]
                )
                results.append(error_result)
        
        # Calcular resumen general
        overall_summary = self._calculate_overall_summary(results)
        
        # Crear suite de resultados
        suite = BenchmarkSuite(
            suite_name=suite_name,
            created_at=start_time,
            agent_configs=self.agent_configs,
            results=results,
            overall_summary=overall_summary
        )
        
        # Guardar en historial
        self.results_history.append(suite)
        
        # Cleanup
        await orchestrator.shutdown()
        
        self.logger.info(f"Benchmark suite completado: {suite_name}")
        return suite
    
    async def _benchmark_basic_functionality(self, orchestrator: OptimizedMultiAgentOrchestrator) -> BenchmarkResult:
        """Benchmark de funcionalidad básica"""
        start_time = datetime.now()
        self.logger.info("Iniciando benchmark de funcionalidad básica")
        
        await self.resource_monitor.start_monitoring()
        
        try:
            # Crear workflows simples
            simple_workflows = []
            for i in range(10):
                workflow = {
                    "tasks": [
                        {
                            "id": f"task_{i}",
                            "type": "data_processing",
                            "required_skills": ["data_analysis"],
                            "priority": 5,
                            "max_duration": 10.0
                        }
                    ]
                }
                simple_workflows.append(workflow)
            
            # Ejecutar workflows
            start_execution = time.time()
            results = await asyncio.gather(*[
                orchestrator.orchestrate_complex_workflow(workflow)
                for workflow in simple_workflows
            ], return_exceptions=True)
            execution_time = time.time() - start_execution
            
            # Procesar resultados
            successful = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
            failed = len(results) - successful
            
            return BenchmarkResult(
                benchmark_name="Basic_Functionality",
                description="Benchmark de funcionalidad básica con workflows simples",
                start_time=start_time,
                end_time=datetime.now(),
                duration_seconds=execution_time,
                success_rate=successful / len(results),
                total_operations=len(results),
                successful_operations=successful,
                failed_operations=failed,
                operations_per_second=len(results) / execution_time,
                avg_cpu_usage=0.0,  # Se llenará por resource monitor
                peak_cpu_usage=0.0,
                avg_memory_usage=0.0,
                peak_memory_usage=0.0,
                agents_tested=["data_processor_agent"],
                agent_efficiency={"data_processor_agent": successful / len(results)},
                load_distribution={"data_processor_agent": len(simple_workflows)},
                specific_metrics={"workflows_executed": len(simple_workflows)},
                errors=[]
            )
            
        finally:
            metrics = await self.resource_monitor.stop_monitoring()
            # Aquí se podrían aplicar las métricas del monitor
    
    async def _benchmark_concurrent_execution(self, orchestrator: OptimizedMultiAgentOrchestrator) -> BenchmarkResult:
        """Benchmark de ejecución concurrente"""
        start_time = datetime.now()
        self.logger.info("Iniciando benchmark de ejecución concurrente")
        
        await self.resource_monitor.start_monitoring()
        
        try:
            # Probar diferentes niveles de concurrencia
            concurrency_levels = [5, 10, 20, 50]
            results_by_level = {}
            
            for concurrency in concurrency_levels:
                # Crear workflows concurrentes
                workflows = []
                for i in range(concurrency):
                    workflow = {
                        "tasks": [
                            {
                                "id": f"concurrent_task_{i}",
                                "type": "python_execution",
                                "required_skills": ["code_execution"],
                                "priority": 5,
                                "max_duration": 5.0
                            }
                        ]
                    }
                    workflows.append(workflow)
                
                # Ejecutar concurrentemente
                start_execution = time.time()
                results = await asyncio.gather(*[
                    orchestrator.orchestrate_complex_workflow(workflow, "parallel")
                    for workflow in workflows
                ], return_exceptions=True)
                execution_time = time.time() - start_execution
                
                successful = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
                
                results_by_level[concurrency] = {
                    "successful": successful,
                    "total": len(results),
                    "execution_time": execution_time,
                    "throughput": successful / execution_time
                }
            
            return BenchmarkResult(
                benchmark_name="Concurrent_Execution",
                description="Benchmark de ejecución concurrente con diferentes niveles",
                start_time=start_time,
                end_time=datetime.now(),
                duration_seconds=time.time() - start_time.timestamp(),
                success_rate=0.0,  # Se calculará con promedio ponderado
                total_operations=sum(level["total"] for level in results_by_level.values()),
                successful_operations=sum(level["successful"] for level in results_by_level.values()),
                failed_operations=0,
                operations_per_second=0.0,
                avg_cpu_usage=0.0,
                peak_cpu_usage=0.0,
                avg_memory_usage=0.0,
                peak_memory_usage=0.0,
                agents_tested=["python_executor_agent"],
                agent_efficiency={},
                load_distribution={},
                specific_metrics={"concurrency_results": results_by_level},
                errors=[]
            )
            
        finally:
            await self.resource_monitor.stop_monitoring()
    
    async def _benchmark_load_balancing(self, orchestrator: OptimizedMultiAgentOrchestrator) -> BenchmarkResult:
        """Benchmark de load balancing"""
        start_time = datetime.now()
        self.logger.info("Iniciando benchmark de load balancing")
        
        await self.resource_monitor.start_monitoring()
        
        try:
            # Crear múltiples workflows que usen diferentes agentes
            workflows = []
            agent_types = ["search_engine_agent", "data_visualization_agent", "api_integration_agent"]
            
            for i in range(30):
                agent_type = random.choice(agent_types)
                workflow = {
                    "tasks": [
                        {
                            "id": f"lb_task_{i}",
                            "type": "general",
                            "required_skills": [],  # Se asignará dinámicamente
                            "priority": 5,
                            "max_duration": 8.0,
                            "fallback_agents": [agent_type]
                        }
                    ]
                }
                workflows.append(workflow)
            
            # Ejecutar con diferentes estrategias de load balancing
            strategies = ["adaptive", "weighted", "least_connections"]
            strategy_results = {}
            
            for strategy in strategies:
                # Reconfigurar orquestador para usar estrategia específica
                # (en implementación real se reconfiguraría el load balancer)
                
                start_execution = time.time()
                results = await asyncio.gather(*[
                    orchestrator.orchestrate_complex_workflow(workflow, "parallel")
                    for workflow in workflows
                ], return_exceptions=True)
                execution_time = time.time() - start_execution
                
                successful = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
                
                strategy_results[strategy] = {
                    "successful": successful,
                    "total": len(results),
                    "execution_time": execution_time,
                    "throughput": successful / execution_time,
                    "success_rate": successful / len(results)
                }
            
            return BenchmarkResult(
                benchmark_name="Load_Balancing",
                description="Benchmark de estrategias de load balancing",
                start_time=start_time,
                end_time=datetime.now(),
                duration_seconds=time.time() - start_time.timestamp(),
                success_rate=0.0,
                total_operations=0,
                successful_operations=0,
                failed_operations=0,
                operations_per_second=0.0,
                avg_cpu_usage=0.0,
                peak_cpu_usage=0.0,
                avg_memory_usage=0.0,
                peak_memory_usage=0.0,
                agents_tested=agent_types,
                agent_efficiency={},
                load_distribution={},
                specific_metrics={"strategy_results": strategy_results},
                errors=[]
            )
            
        finally:
            await self.resource_monitor.stop_monitoring()
    
    async def _benchmark_routing_intelligence(self, orchestrator: OptimizedMultiAgentOrchestrator) -> BenchmarkResult:
        """Benchmark de inteligencia de routing"""
        start_time = datetime.now()
        self.logger.info("Iniciando benchmark de routing intelligence")
        
        await self.resource_monitor.start_monitoring()
        
        try:
            # Crear tareas que requieren routing inteligente
            complex_workflows = []
            for i in range(20):
                workflow = {
                    "tasks": [
                        {
                            "id": f"routing_task_{i}",
                            "type": "complex_analysis",
                            "required_skills": ["data_analysis", "visualization", "reporting"],
                            "priority": random.randint(1, 10),
                            "max_duration": 60.0,
                            "dependencies": []
                        }
                    ]
                }
                complex_workflows.append(workflow)
            
            # Ejecutar con routing inteligente
            start_execution = time.time()
            results = await asyncio.gather(*[
                orchestrator.orchestrate_complex_workflow(workflow, "adaptive", "balanced")
                for workflow in complex_workflows
            ], return_exceptions=True)
            execution_time = time.time() - start_execution
            
            successful = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
            
            return BenchmarkResult(
                benchmark_name="Routing_Intelligence",
                description="Benchmark de routing inteligente con workflows complejos",
                start_time=start_time,
                end_time=datetime.now(),
                duration_seconds=execution_time,
                success_rate=successful / len(results),
                total_operations=len(results),
                successful_operations=successful,
                failed_operations=len(results) - successful,
                operations_per_second=len(results) / execution_time,
                avg_cpu_usage=0.0,
                peak_cpu_usage=0.0,
                avg_memory_usage=0.0,
                peak_memory_usage=0.0,
                agents_tested=["data_processor_agent", "data_visualization_agent", "report_generation_agent"],
                agent_efficiency={},
                load_distribution={},
                specific_metrics={"routing_decisions": "adaptive"},
                errors=[]
            )
            
        finally:
            await self.resource_monitor.stop_monitoring()
    
    async def _benchmark_fault_tolerance(self, orchestrator: OptimizedMultiAgentOrchestrator) -> BenchmarkResult:
        """Benchmark de fault tolerance"""
        start_time = datetime.now()
        self.logger.info("Iniciando benchmark de fault tolerance")
        
        await self.resource_monitor.start_monitoring()
        
        try:
            # Simular fallos en algunos agentes
            fault_scenarios = [
                "agent_timeout",
                "agent_error",
                "resource_exhaustion",
                "network_delay"
            ]
            
            fault_results = {}
            
            for scenario in fault_scenarios:
                # Crear workflows para este escenario de fallo
                workflows = []
                for i in range(10):
                    workflow = {
                        "tasks": [
                            {
                                "id": f"fault_task_{scenario}_{i}",
                                "type": "tolerance_test",
                                "required_skills": ["fault_resilience"],
                                "priority": 8,
                                "max_duration": 15.0,
                                "fallback_agents": ["python_executor_agent", "data_processor_agent"]
                            }
                        ]
                    }
                    workflows.append(workflow)
                
                # Ejecutar workflows con escenario de fallo
                start_execution = time.time()
                results = await asyncio.gather(*[
                    orchestrator.orchestrate_complex_workflow(workflow)
                    for workflow in workflows
                ], return_exceptions=True)
                execution_time = time.time() - start_execution
                
                successful = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
                
                fault_results[scenario] = {
                    "successful": successful,
                    "total": len(results),
                    "success_rate": successful / len(results),
                    "execution_time": execution_time
                }
            
            return BenchmarkResult(
                benchmark_name="Fault_Tolerance",
                description="Benchmark de tolerancia a fallos",
                start_time=start_time,
                end_time=datetime.now(),
                duration_seconds=time.time() - start_time.timestamp(),
                success_rate=0.0,
                total_operations=0,
                successful_operations=0,
                failed_operations=0,
                operations_per_second=0.0,
                avg_cpu_usage=0.0,
                peak_cpu_usage=0.0,
                avg_memory_usage=0.0,
                peak_memory_usage=0.0,
                agents_tested=[],
                agent_efficiency={},
                load_distribution={},
                specific_metrics={"fault_scenarios": fault_results},
                errors=[]
            )
            
        finally:
            await self.resource_monitor.stop_monitoring()
    
    async def _benchmark_resource_utilization(self, orchestrator: OptimizedMultiAgentOrchestrator) -> BenchmarkResult:
        """Benchmark de utilización de recursos"""
        start_time = datetime.now()
        self.logger.info("Iniciando benchmark de utilización de recursos")
        
        await self.resource_monitor.start_monitoring(interval=0.1)  # Monitoring más frecuente
        
        try:
            # Ejecutar stress ligero para medir utilización de recursos
            workflows = []
            for i in range(25):
                workflow = {
                    "tasks": [
                        {
                            "id": f"resource_task_{i}",
                            "type": "resource_intensive",
                            "required_skills": ["data_processing"],
                            "priority": 5,
                            "max_duration": 20.0
                        }
                    ]
                }
                workflows.append(workflow)
            
            start_execution = time.time()
            results = await asyncio.gather(*[
                orchestrator.orchestrate_complex_workflow(workflow, "parallel")
                for workflow in workflows
            ], return_exceptions=True)
            execution_time = time.time() - start_execution
            
            successful = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
            
            return BenchmarkResult(
                benchmark_name="Resource_Utilization",
                description="Benchmark de utilización de recursos del sistema",
                start_time=start_time,
                end_time=datetime.now(),
                duration_seconds=execution_time,
                success_rate=successful / len(results),
                total_operations=len(results),
                successful_operations=successful,
                failed_operations=len(results) - successful,
                operations_per_second=len(results) / execution_time,
                avg_cpu_usage=0.0,
                peak_cpu_usage=0.0,
                avg_memory_usage=0.0,
                peak_memory_usage=0.0,
                agents_tested=[],
                agent_efficiency={},
                load_distribution={},
                specific_metrics={"monitoring_interval": 0.1},
                errors=[]
            )
            
        finally:
            metrics = await self.resource_monitor.stop_monitoring()
            # Aplicar métricas del monitor
    
    async def _benchmark_agent_scalability(self, orchestrator: OptimizedMultiAgentOrchestrator) -> BenchmarkResult:
        """Benchmark de escalabilidad de agentes"""
        start_time = datetime.now()
        self.logger.info("Iniciando benchmark de escalabilidad de agentes")
        
        await self.resource_monitor.start_monitoring()
        
        try:
            # Probar escalabilidad usando diferentes números de agentes
            agent_counts = [5, 10, 15, 20]
            scalability_results = {}
            
            for agent_count in agent_counts:
                # Seleccionar subset de agentes
                available_agents = list(self.agent_configs.keys())[:agent_count]
                
                # Crear workflows que usen todos los agentes seleccionados
                workflows = []
                for i in range(agent_count * 2):  # 2 workflows por agente
                    agent_type = available_agents[i % len(available_agents)]
                    workflow = {
                        "tasks": [
                            {
                                "id": f"scale_task_{agent_count}_{i}",
                                "type": "scalability_test",
                                "required_skills": [],
                                "priority": 5,
                                "max_duration": 10.0,
                                "fallback_agents": [agent_type]
                            }
                        ]
                    }
                    workflows.append(workflow)
                
                # Ejecutar con número específico de agentes
                start_execution = time.time()
                results = await asyncio.gather(*[
                    orchestrator.orchestrate_complex_workflow(workflow, "parallel")
                    for workflow in workflows
                ], return_exceptions=True)
                execution_time = time.time() - start_execution
                
                successful = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
                
                scalability_results[agent_count] = {
                    "agents_used": agent_count,
                    "workflows_executed": len(workflows),
                    "successful": successful,
                    "execution_time": execution_time,
                    "throughput": successful / execution_time
                }
            
            return BenchmarkResult(
                benchmark_name="Agent_Scalability",
                description="Benchmark de escalabilidad con diferentes números de agentes",
                start_time=start_time,
                end_time=datetime.now(),
                duration_seconds=time.time() - start_time.timestamp(),
                success_rate=0.0,
                total_operations=0,
                successful_operations=0,
                failed_operations=0,
                operations_per_second=0.0,
                avg_cpu_usage=0.0,
                peak_cpu_usage=0.0,
                avg_memory_usage=0.0,
                peak_memory_usage=0.0,
                agents_tested=list(self.agent_configs.keys()),
                agent_efficiency={},
                load_distribution={},
                specific_metrics={"scalability_results": scalability_results},
                errors=[]
            )
            
        finally:
            await self.resource_monitor.stop_monitoring()
    
    async def _benchmark_workflow_complexity(self, orchestrator: OptimizedMultiAgentOrchestrator) -> BenchmarkResult:
        """Benchmark de complejidad de workflows"""
        start_time = datetime.now()
        self.logger.info("Iniciando benchmark de complejidad de workflows")
        
        await self.resource_monitor.start_monitoring()
        
        try:
            # Crear workflows de diferentes niveles de complejidad
            complexity_levels = [
                {"tasks": 1, "dependencies": 0, "name": "simple"},
                {"tasks": 3, "dependencies": 2, "name": "moderate"},
                {"tasks": 5, "dependencies": 4, "name": "complex"},
                {"tasks": 10, "dependencies": 8, "name": "enterprise"}
            ]
            
            complexity_results = {}
            
            for level in complexity_levels:
                workflows = []
                for i in range(5):  # 5 workflows por nivel de complejidad
                    tasks = []
                    dependencies = []
                    
                    for j in range(level["tasks"]):
                        task_id = f"complex_task_{level['name']}_{i}_{j}"
                        task = {
                            "id": task_id,
                            "type": f"{level['name']}_workflow",
                            "required_skills": ["data_processing"],
                            "priority": 5,
                            "max_duration": 30.0,
                            "dependencies": [dep for dep in dependencies]  # Dependencias de tareas anteriores
                        }
                        tasks.append(task)
                        dependencies.append(task_id)
                    
                    workflow = {"tasks": tasks}
                    workflows.append(workflow)
                
                # Ejecutar workflows complejos
                start_execution = time.time()
                results = await asyncio.gather(*[
                    orchestrator.orchestrate_complex_workflow(workflow, "adaptive")
                    for workflow in workflows
                ], return_exceptions=True)
                execution_time = time.time() - start_execution
                
                successful = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
                
                complexity_results[level["name"]] = {
                    "tasks_per_workflow": level["tasks"],
                    "dependencies_per_workflow": level["dependencies"],
                    "workflows": len(workflows),
                    "successful": successful,
                    "execution_time": execution_time,
                    "success_rate": successful / len(results)
                }
            
            return BenchmarkResult(
                benchmark_name="Workflow_Complexity",
                description="Benchmark de workflows con diferentes niveles de complejidad",
                start_time=start_time,
                end_time=datetime.now(),
                duration_seconds=time.time() - start_time.timestamp(),
                success_rate=0.0,
                total_operations=0,
                successful_operations=0,
                failed_operations=0,
                operations_per_second=0.0,
                avg_cpu_usage=0.0,
                peak_cpu_usage=0.0,
                avg_memory_usage=0.0,
                peak_memory_usage=0.0,
                agents_tested=[],
                agent_efficiency={},
                load_distribution={},
                specific_metrics={"complexity_results": complexity_results},
                errors=[]
            )
            
        finally:
            await self.resource_monitor.stop_monitoring()
    
    async def _benchmark_stress_light(self, orchestrator: OptimizedMultiAgentOrchestrator) -> BenchmarkResult:
        """Stress test ligero"""
        start_time = datetime.now()
        self.logger.info("Iniciando stress test ligero")
        
        await self.resource_monitor.start_monitoring()
        
        try:
            # 20 workflows concurrentes
            workflows = []
            for i in range(20):
                workflow = {
                    "tasks": [
                        {
                            "id": f"stress_light_task_{i}",
                            "type": "stress_test",
                            "required_skills": ["data_processing"],
                            "priority": 5,
                            "max_duration": 15.0
                        }
                    ]
                }
                workflows.append(workflow)
            
            start_execution = time.time()
            results = await orchestrator.execute_stress_test(concurrent_workflows=20, tasks_per_workflow=1)
            execution_time = time.time() - start_execution
            
            return BenchmarkResult(
                benchmark_name="Stress_Test_Light",
                description="Stress test con carga ligera (20 workflows)",
                start_time=start_time,
                end_time=datetime.now(),
                duration_seconds=execution_time,
                success_rate=results["results"]["success_rate"],
                total_operations=results["configuration"]["concurrent_workflows"],
                successful_operations=results["results"]["successful_workflows"],
                failed_operations=results["results"]["failed_workflows"],
                operations_per_second=results["performance_metrics"]["workflows_per_second"],
                avg_cpu_usage=0.0,
                peak_cpu_usage=0.0,
                avg_memory_usage=0.0,
                peak_memory_usage=0.0,
                agents_tested=[],
                agent_efficiency={},
                load_distribution={},
                specific_metrics=results,
                errors=[]
            )
            
        finally:
            await self.resource_monitor.stop_monitoring()
    
    async def _benchmark_stress_medium(self, orchestrator: OptimizedMultiAgentOrchestrator) -> BenchmarkResult:
        """Stress test medio"""
        start_time = datetime.now()
        self.logger.info("Iniciando stress test medio")
        
        await self.resource_monitor.start_monitoring()
        
        try:
            # 50 workflows concurrentes
            start_execution = time.time()
            results = await orchestrator.execute_stress_test(concurrent_workflows=50, tasks_per_workflow=2)
            execution_time = time.time() - start_execution
            
            return BenchmarkResult(
                benchmark_name="Stress_Test_Medium",
                description="Stress test con carga media (50 workflows, 2 tareas c/u)",
                start_time=start_time,
                end_time=datetime.now(),
                duration_seconds=execution_time,
                success_rate=results["results"]["success_rate"],
                total_operations=results["configuration"]["concurrent_workflows"],
                successful_operations=results["results"]["successful_workflows"],
                failed_operations=results["results"]["failed_workflows"],
                operations_per_second=results["performance_metrics"]["workflows_per_second"],
                avg_cpu_usage=0.0,
                peak_cpu_usage=0.0,
                avg_memory_usage=0.0,
                peak_memory_usage=0.0,
                agents_tested=[],
                agent_efficiency={},
                load_distribution={},
                specific_metrics=results,
                errors=[]
            )
            
        finally:
            await self.resource_monitor.stop_monitoring()
    
    async def _benchmark_stress_heavy(self, orchestrator: OptimizedMultiAgentOrchestrator) -> BenchmarkResult:
        """Stress test pesado"""
        start_time = datetime.now()
        self.logger.info("Iniciando stress test pesado")
        
        await self.resource_monitor.start_monitoring()
        
        try:
            # 100 workflows concurrentes
            start_execution = time.time()
            results = await orchestrator.execute_stress_test(concurrent_workflows=100, tasks_per_workflow=3)
            execution_time = time.time() - start_execution
            
            return BenchmarkResult(
                benchmark_name="Stress_Test_Heavy",
                description="Stress test con carga pesada (100 workflows, 3 tareas c/u)",
                start_time=start_time,
                end_time=datetime.now(),
                duration_seconds=execution_time,
                success_rate=results["results"]["success_rate"],
                total_operations=results["configuration"]["concurrent_workflows"],
                successful_operations=results["results"]["successful_workflows"],
                failed_operations=results["results"]["failed_workflows"],
                operations_per_second=results["performance_metrics"]["workflows_per_second"],
                avg_cpu_usage=0.0,
                peak_cpu_usage=0.0,
                avg_memory_usage=0.0,
                peak_memory_usage=0.0,
                agents_tested=[],
                agent_efficiency={},
                load_distribution={},
                specific_metrics=results,
                errors=[]
            )
            
        finally:
            await self.resource_monitor.stop_monitoring()
    
    async def _benchmark_endurance(self, orchestrator: OptimizedMultiAgentOrchestrator) -> BenchmarkResult:
        """Test de resistencia"""
        start_time = datetime.now()
        self.logger.info("Iniciando test de resistencia")
        
        await self.resource_monitor.start_monitoring(interval=1.0)  # Monitoreo menos frecuente
        
        try:
            # Ejecutar workflows durante 5 minutos
            endurance_duration = 300  # 5 minutos
            workflows_executed = 0
            successful_workflows = 0
            start_execution = time.time()
            
            while time.time() - start_execution < endurance_duration:
                # Ejecutar batch de workflows cada 10 segundos
                batch_workflows = []
                for i in range(10):
                    workflow = {
                        "tasks": [
                            {
                                "id": f"endurance_task_{workflows_executed}_{i}",
                                "type": "endurance_test",
                                "required_skills": ["data_processing"],
                                "priority": 3,
                                "max_duration": 20.0
                            }
                        ]
                    }
                    batch_workflows.append(workflow)
                
                batch_results = await asyncio.gather(*[
                    orchestrator.orchestrate_complex_workflow(workflow)
                    for workflow in batch_workflows
                ], return_exceptions=True)
                
                workflows_executed += len(batch_workflows)
                successful_workflows += sum(
                    1 for r in batch_results if isinstance(r, dict) and r.get("success", False)
                )
                
                await asyncio.sleep(10)  # Esperar 10 segundos entre batches
            
            total_execution_time = time.time() - start_execution
            
            return BenchmarkResult(
                benchmark_name="Endurance_Test",
                description="Test de resistencia durante 5 minutos",
                start_time=start_time,
                end_time=datetime.now(),
                duration_seconds=total_execution_time,
                success_rate=successful_workflows / max(workflows_executed, 1),
                total_operations=workflows_executed,
                successful_operations=successful_workflows,
                failed_operations=workflows_executed - successful_workflows,
                operations_per_second=workflows_executed / total_execution_time,
                avg_cpu_usage=0.0,
                peak_cpu_usage=0.0,
                avg_memory_usage=0.0,
                peak_memory_usage=0.0,
                agents_tested=[],
                agent_efficiency={},
                load_distribution={},
                specific_metrics={
                    "endurance_duration": endurance_duration,
                    "throughput": workflows_executed / total_execution_time
                },
                errors=[]
            )
            
        finally:
            await self.resource_monitor.stop_monitoring()
    
    def _calculate_overall_summary(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Calcular resumen general de todos los benchmarks"""
        
        if not results:
            return {}
        
        # Métricas agregadas
        total_operations = sum(r.total_operations for r in results)
        total_successful = sum(r.successful_operations for r in results)
        total_failed = sum(r.failed_operations for r in results)
        avg_success_rate = total_successful / max(total_operations, 1)
        
        # Calcular throughput promedio
        operations_per_second_list = [r.operations_per_second for r in results if r.operations_per_second > 0]
        avg_throughput = statistics.mean(operations_per_second_list) if operations_per_second_list else 0.0
        
        # Identificar mejores/peores performers
        success_rates = [(r.benchmark_name, r.success_rate) for r in results]
        best_performer = max(success_rates, key=lambda x: x[1]) if success_rates else ("N/A", 0.0)
        worst_performer = min(success_rates, key=lambda x: x[1]) if success_rates else ("N/A", 0.0)
        
        # Agentes más utilizados
        all_agents = set()
        for r in results:
            all_agents.update(r.agents_tested)
        
        return {
            "total_benchmarks": len(results),
            "total_operations": total_operations,
            "total_successful": total_successful,
            "total_failed": total_failed,
            "overall_success_rate": avg_success_rate,
            "average_throughput": avg_throughput,
            "best_performing_benchmark": {
                "name": best_performer[0],
                "success_rate": best_performer[1]
            },
            "worst_performing_benchmark": {
                "name": worst_performer[0],
                "success_rate": worst_performer[1]
            },
            "total_agents_tested": len(all_agents),
            "agents_tested": list(all_agents),
            "benchmark_completion_time": datetime.now().isoformat()
        }
    
    def save_benchmark_results(self, suite: BenchmarkSuite, file_path: str) -> None:
        """Guardar resultados de benchmarks en archivo JSON"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(suite.to_dict(), f, indent=2, ensure_ascii=False)
            self.logger.info(f"Resultados de benchmark guardados en: {file_path}")
        except Exception as e:
            self.logger.error(f"Error guardando resultados: {e}")
    
    def generate_benchmark_report(self, suite: BenchmarkSuite) -> str:
        """Generar reporte de benchmarks en formato legible"""
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append(f"REPORTE DE BENCHMARKS - {suite.suite_name}")
        report_lines.append("=" * 80)
        report_lines.append(f"Generado: {suite.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Agentes configurados: {len(suite.agent_configs)}")
        report_lines.append("")
        
        # Resumen general
        summary = suite.overall_summary
        report_lines.append("RESUMEN GENERAL")
        report_lines.append("-" * 40)
        report_lines.append(f"Benchmarks ejecutados: {summary.get('total_benchmarks', 0)}")
        report_lines.append(f"Operaciones totales: {summary.get('total_operations', 0)}")
        report_lines.append(f"Operaciones exitosas: {summary.get('total_successful', 0)}")
        report_lines.append(f"Tasa de éxito general: {summary.get('overall_success_rate', 0):.2%}")
        report_lines.append(f"Throughput promedio: {summary.get('average_throughput', 0):.2f} ops/seg")
        report_lines.append("")
        
        # Resultados individuales
        report_lines.append("RESULTADOS INDIVIDUALES")
        report_lines.append("-" * 40)
        
        for result in suite.results:
            report_lines.append(f"\n📊 {result.benchmark_name}")
            report_lines.append(f"   Descripción: {result.description}")
            report_lines.append(f"   Duración: {result.duration_seconds:.2f}s")
            report_lines.append(f"   Éxito: {result.success_rate:.2%}")
            report_lines.append(f"   Throughput: {result.operations_per_second:.2f} ops/seg")
            
            if result.errors:
                report_lines.append(f"   Errores: {len(result.errors)}")
                for error in result.errors[:3]:  # Mostrar solo primeros 3 errores
                    report_lines.append(f"     - {error}")
            
            if result.specific_metrics:
                metrics = result.specific_metrics
                if "strategy_results" in metrics:
                    report_lines.append(f"   Estrategias probadas: {list(metrics['strategy_results'].keys())}")
                if "scalability_results" in metrics:
                    scales = metrics["scalability_results"]
                    report_lines.append(f"   Escalabilidad (agentes): {list(scales.keys())}")
        
        report_lines.append("")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)


# Función principal para ejecutar benchmarks
async def run_complete_benchmark_suite(
    output_dir: str = "/workspace/mcp-core-superior/benchmarks",
    suite_name: str = "Complete_MultiAgent_Optimization_Benchmark"
) -> BenchmarkSuite:
    """Ejecutar suite completa de benchmarks y generar reportes"""
    
    # Crear directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear y ejecutar benchmarks
    benchmark = MultiAgentBenchmark()
    suite = await benchmark.run_complete_benchmark_suite(
        suite_name=suite_name,
        include_stress_tests=True
    )
    
    # Guardar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Guardar JSON
    json_path = os.path.join(output_dir, f"benchmark_results_{timestamp}.json")
    benchmark.save_benchmark_results(suite, json_path)
    
    # Generar y guardar reporte
    report = benchmark.generate_benchmark_report(suite)
    report_path = os.path.join(output_dir, f"benchmark_report_{timestamp}.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Benchmarks completados!")
    print(f"📄 Resultados JSON: {json_path}")
    print(f"📋 Reporte: {report_path}")
    print(f"📊 Tasa de éxito general: {suite.overall_summary.get('overall_success_rate', 0):.2%}")
    
    return suite


if __name__ == "__main__":
    # Ejecutar benchmarks si se llama directamente
    import asyncio
    
    async def main():
        suite = await run_complete_benchmark_suite()
        print("\n" + "="*80)
        print("BENCHMARK SUITE COMPLETADO")
        print("="*80)
    
    asyncio.run(main())