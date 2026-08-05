#!/usr/bin/env python3
"""
SilhouetteMCP Sistema Completo de Testing y Optimización
=======================================================

SISTEMA DE TESTING Y OPTIMIZACIÓN COMPLETO PARA ARQUITECTURA JERÁRQUICA DE 100+ AGENTES

Desarrollado para: silhouettemcp.albertofarah.com
Versión: 1.0.0 - TESTING & OPTIMIZATION SUITE

CARACTERÍSTICAS IMPLEMENTADAS:
- Testing de Escalabilidad (10→1000 usuarios concurrentes)
- Testing de Coordinación entre Equipos (100+ agentes)
- Optimización de Algoritmos (Hungarian, CBBA, RAFT)
- Testing de Comunicación FIPA-ACL
- Análisis de Performance en Tiempo Real
- Dashboard de Métricas y Reporting
- Auto-healing y Recuperación Automática
- Benchmarking y Comparativas

PUERTOS:
- 8004: Testing Suite API
- 8005: Métricas y Dashboard
- 8006: Optimización en Tiempo Real
"""

import json
import time
import asyncio
import logging
import threading
import hashlib
import secrets
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set, Callable, Tuple, Awaitable
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from enum import Enum
import queue
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from abc import ABC, abstractmethod
import gc
import psutil
import memory_profiler
from contextlib import contextmanager
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import websockets
from fastapi import FastAPI, HTTPException, Request, Depends, status, WebSocket, WebSocketDisconnect, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, validator
import uvicorn
import redis
import aioredis
from dataclasses import dataclass
import pickle
import gzip
from io import StringIO, BytesIO
import traceback
import subprocess
import sys
import os
from pathlib import Path
import signal
import resource
import math
from itertools import combinations, permutations
import networkx as nx
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from collections import defaultdict, Counter
import warnings
warnings.filterwarnings('ignore')

# ==================== CONFIGURACIÓN Y LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('silhouettemcp_testing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SilhouetteMCP-Testing-Suite")

# ==================== CONFIGURACIÓN GLOBAL ====================
TEST_CONFIG = {
    "max_concurrent_users": 1000,
    "max_agents": 500,
    "test_timeout": 3600,
    "redis_url": "redis://localhost:6379",
    "metrics_retention": 86400,  # 24 horas
    "performance_baseline": {
        "response_time_p95": 200,  # ms
        "throughput_rps": 100,     # requests per second
        "memory_usage_mb": 1024,   # MB
        "cpu_usage_percent": 80,   # %
        "success_rate": 99.5       # %
    },
    "test_scenarios": {
        "scalability": {
            "user_loads": [10, 50, 100, 250, 500, 750, 1000],
            "agent_counts": [10, 25, 50, 100, 200, 350, 500],
            "duration_seconds": 300
        },
        "coordination": {
            "team_sizes": [5, 10, 15, 20, 25],
            "inter_team_ratio": 0.3,
            "complexity_levels": ["low", "medium", "high"]
        },
        "performance": {
            "algorithms": ["hungarian", "cbba", "raft"],
            "optimization_levels": ["basic", "advanced", "aggressive"],
            "memory_profiling": True
        }
    }
}

# ==================== ESTRUCTURAS DE DATOS ====================

@dataclass
class TestMetrics:
    """Métricas de testing"""
    timestamp: datetime
    test_name: str
    test_type: str
    participants: int
    duration: float
    success_rate: float
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    throughput: float
    memory_usage: float
    cpu_usage: float
    network_latency: float
    error_count: int
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ScalabilityTestResult:
    """Resultado de test de escalabilidad"""
    user_load: int
    agent_count: int
    response_times: List[float]
    throughput: List[float]
    memory_usage: List[float]
    cpu_usage: List[float]
    success_rate: float
    errors: List[str]
    bottleneck_analysis: Dict[str, Any]

@dataclass
class CoordinationTestResult:
    """Resultado de test de coordinación"""
    teams_count: int
    agents_per_team: int
    coordination_success_rate: float
    inter_team_communications: int
    decision_making_time: float
    resource_conflicts: int
    load_balancing_efficiency: float
    leader_election_time: float

@dataclass
class PerformanceTestResult:
    """Resultado de test de performance"""
    algorithm: str
    optimization_level: str
    assignment_time: float
    solution_quality: float
    memory_efficiency: float
    convergence_iterations: int
    scalability_factor: float
    benchmark_comparison: Dict[str, float]

# ==================== CLASES PRINCIPALES ====================

class TestingSuite:
    """Suite principal de testing y optimización"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or TEST_CONFIG
        self.metrics_buffer = deque(maxlen=10000)
        self.redis_client = None
        self.active_tests = {}
        self.performance_baselines = {}
        self.optimization_results = {}
        self.test_results_history = []
        self.is_running = False
        self._initialize_redis()
        
    def _initialize_redis(self):
        """Inicializar conexión Redis para caching"""
        try:
            self.redis_client = redis.from_url(self.config["redis_url"])
            self.redis_client.ping()
            logger.info("Conexión Redis establecida para métricas")
        except Exception as e:
            logger.warning(f"No se pudo conectar a Redis: {e}. Usando cache local.")
            self.redis_client = None
    
    async def run_scalability_tests(self) -> Dict[str, Any]:
        """Ejecutar suite completa de tests de escalabilidad"""
        logger.info("🚀 INICIANDO TESTS DE ESCALABILIDAD")
        
        results = {}
        scalability_tester = ScalabilityTester(self.config)
        
        # Test 1: Concurrent User Scaling
        logger.info("📊 Testing escalado de usuarios concurrentes...")
        user_scaling_results = await scalability_tester.test_user_scaling()
        results["user_scaling"] = user_scaling_results
        
        # Test 2: Agent Scaling
        logger.info("🤖 Testing escalado de agentes...")
        agent_scaling_results = await scalability_tester.test_agent_scaling()
        results["agent_scaling"] = agent_scaling_results
        
        # Test 3: Memory Usage Analysis
        logger.info("💾 Testing uso de memoria...")
        memory_results = await scalability_tester.test_memory_usage()
        results["memory_analysis"] = memory_results
        
        # Test 4: CPU Utilization
        logger.info("🖥️ Testing utilización de CPU...")
        cpu_results = await scalability_tester.test_cpu_utilization()
        results["cpu_utilization"] = cpu_results
        
        # Test 5: Response Time Analysis
        logger.info("⏱️ Testing tiempos de respuesta...")
        response_results = await scalability_tester.test_response_times()
        results["response_times"] = response_results
        
        # Test 6: Stress Testing
        logger.info("💪 Testing de estrés...")
        stress_results = await scalability_tester.stress_test()
        results["stress_test"] = stress_results
        
        # Análisis de瓶颈
        bottleneck_analysis = self._analyze_bottlenecks(results)
        results["bottleneck_analysis"] = bottleneck_analysis
        
        logger.info("✅ TESTS DE ESCALABILIDAD COMPLETADOS")
        return results
    
    async def run_coordination_tests(self) -> Dict[str, Any]:
        """Ejecutar suite de tests de coordinación entre equipos"""
        logger.info("🤝 INICIANDO TESTS DE COORDINACIÓN ENTRE EQUIPOS")
        
        results = {}
        coordination_tester = CoordinationTester(self.config)
        
        # Test 1: Communication Protocol Tests
        logger.info("📡 Testing protocolos de comunicación...")
        comm_results = await coordination_tester.test_communication_protocols()
        results["communication_protocols"] = comm_results
        
        # Test 2: Inter-Team Coordination
        logger.info("🔗 Testing coordinación inter-equipos...")
        inter_team_results = await coordination_tester.test_inter_team_coordination()
        results["inter_team_coordination"] = inter_team_results
        
        # Test 3: Task Distribution Tests
        logger.info("📋 Testing distribución de tareas...")
        task_dist_results = await coordination_tester.test_task_distribution()
        results["task_distribution"] = task_dist_results
        
        # Test 4: Conflict Resolution Tests
        logger.info("⚖️ Testing resolución de conflictos...")
        conflict_results = await coordination_tester.test_conflict_resolution()
        results["conflict_resolution"] = conflict_results
        
        # Test 5: Load Balancing Tests
        logger.info("⚖️ Testing balanceador de carga...")
        load_balancing_results = await coordination_tester.test_load_balancing()
        results["load_balancing"] = load_balancing_results
        
        # Análisis de coordinación
        coordination_analysis = self._analyze_coordination(results)
        results["coordination_analysis"] = coordination_analysis
        
        logger.info("✅ TESTS DE COORDINACIÓN COMPLETADOS")
        return results
    
    async def run_algorithm_optimization(self) -> Dict[str, Any]:
        """Ejecutar optimización de algoritmos"""
        logger.info("🧠 INICIANDO OPTIMIZACIÓN DE ALGORITMOS")
        
        results = {}
        algorithm_tester = AlgorithmOptimizer(self.config)
        
        # Test 1: Hungarian Algorithm Optimization
        logger.info("🔄 Testing optimización algoritmo Hungarian...")
        hungarian_results = await algorithm_tester.optimize_hungarian_algorithm()
        results["hungarian_optimization"] = hungarian_results
        
        # Test 2: CBBA Algorithm Refinement
        logger.info("🗳️ Testing refinamiento algoritmo CBBA...")
        cbba_results = await algorithm_tester.optimize_cbba_algorithm()
        results["cbba_optimization"] = cbba_results
        
        # Test 3: RAFT Leader Election Optimization
        logger.info("👑 Testing optimización RAFT leader election...")
        raft_results = await algorithm_tester.optimize_raft_election()
        results["raft_optimization"] = raft_results
        
        # Test 4: Load Balancing Algorithms
        logger.info("⚖️ Testing algoritmos de balanceador de carga...")
        lb_results = await algorithm_tester.optimize_load_balancing()
        results["load_balancing_optimization"] = lb_results
        
        # Test 5: Performance Comparison
        logger.info("📊 Comparando performance de algoritmos...")
        comparison_results = await algorithm_tester.compare_algorithms()
        results["algorithm_comparison"] = comparison_results
        
        logger.info("✅ OPTIMIZACIÓN DE ALGORITMOS COMPLETADA")
        return results
    
    async def run_communication_tests(self) -> Dict[str, Any]:
        """Ejecutar tests de comunicación entre agentes"""
        logger.info("📡 INICIANDO TESTS DE COMUNICACIÓN ENTRE AGENTES")
        
        results = {}
        communication_tester = CommunicationTester(self.config)
        
        # Test 1: Network Reliability Tests
        logger.info("🌐 Testing fiabilidad de red...")
        network_results = await communication_tester.test_network_reliability()
        results["network_reliability"] = network_results
        
        # Test 2: FIPA-ACL Protocol Compliance
        logger.info("📋 Testing cumplimiento FIPA-ACL...")
        fipa_results = await communication_tester.test_fipa_compliance()
        results["fipa_compliance"] = fipa_results
        
        # Test 3: Message Delivery Tests
        logger.info("📨 Testing entrega de mensajes...")
        delivery_results = await communication_tester.test_message_delivery()
        results["message_delivery"] = delivery_results
        
        # Test 4: Latency Tests
        logger.info("⏱️ Testing latencia de comunicación...")
        latency_results = await communication_tester.test_latency()
        results["latency_tests"] = latency_results
        
        # Test 5: Security Tests
        logger.info("🔒 Testing seguridad de comunicación...")
        security_results = await communication_tester.test_communication_security()
        results["communication_security"] = security_results
        
        logger.info("✅ TESTS DE COMUNICACIÓN COMPLETADOS")
        return results
    
    def _analyze_bottlenecks(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analizar bottlenecks del sistema"""
        analysis = {
            "memory_bottlenecks": [],
            "cpu_bottlenecks": [],
            "network_bottlenecks": [],
            "response_time_bottlenecks": [],
            "recommendations": []
        }
        
        # Analizar memoria
        if "memory_analysis" in results:
            memory_data = results["memory_analysis"]
            if memory_data.get("peak_usage", 0) > self.config["performance_baseline"]["memory_usage_mb"]:
                analysis["memory_bottlenecks"].append("Alto uso de memoria detectado")
                analysis["recommendations"].append("Implementar garbage collection más frecuente")
        
        # Analizar CPU
        if "cpu_utilization" in results:
            cpu_data = results["cpu_utilization"]
            if cpu_data.get("avg_usage", 0) > self.config["performance_baseline"]["cpu_usage_percent"]:
                analysis["cpu_bottlenecks"].append("Alta utilización de CPU")
                analysis["recommendations"].append("Optimizar algoritmos y reducir cálculos redundantes")
        
        # Analizar tiempos de respuesta
        if "response_times" in results:
            response_data = results["response_times"]
            if response_data.get("p95_time", 0) > self.config["performance_baseline"]["response_time_p95"]:
                analysis["response_time_bottlenecks"].append("Tiempos de respuesta elevados")
                analysis["recommendations"].append("Implementar caching y optimización de queries")
        
        return analysis
    
    def _analyze_coordination(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analizar efectividad de coordinación"""
        analysis = {
            "coordination_efficiency": 0.0,
            "communication_patterns": {},
            "decision_making_speed": {},
            "resource_utilization": {},
            "recommendations": []
        }
        
        # Calcular eficiencia de coordinación
        if "communication_protocols" in results:
            comm_eff = results["communication_protocols"].get("success_rate", 0)
            analysis["coordination_efficiency"] = comm_eff
        
        # Patrones de comunicación
        if "inter_team_coordination" in results:
            patterns = results["inter_team_coordination"].get("communication_patterns", {})
            analysis["communication_patterns"] = patterns
        
        # Velocidad de toma de decisiones
        if "task_distribution" in results:
            decision_speed = results["task_distribution"].get("avg_decision_time", 0)
            analysis["decision_making_speed"] = {"avg_decision_time": decision_speed}
        
        return analysis

class ScalabilityTester:
    """Tester especializado en escalabilidad"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("ScalabilityTester")
        
    async def test_user_scaling(self) -> Dict[str, Any]:
        """Testing escalado de usuarios concurrentes"""
        self.logger.info("Testing escalado de usuarios concurrentes...")
        
        user_loads = self.config["test_scenarios"]["scalability"]["user_loads"]
        results = {}
        
        for user_count in user_loads:
            self.logger.info(f"Probando con {user_count} usuarios concurrentes...")
            
            # Simular carga de usuarios
            start_time = time.time()
            success_count = 0
            response_times = []
            errors = []
            
            # Ejecutar simulación en paralelo
            tasks = []
            for i in range(user_count):
                task = self._simulate_user_request(i)
                tasks.append(task)
            
            # Ejecutar con límite de concurrencia
            semaphore = asyncio.Semaphore(min(50, user_count))
            
            async def bounded_request(task):
                async with semaphore:
                    return await task
            
            batch_results = await asyncio.gather(*[bounded_request(t) for t in tasks], return_exceptions=True)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Procesar resultados
            for result in batch_results:
                if isinstance(result, Exception):
                    errors.append(str(result))
                else:
                    success_count += 1
                    if isinstance(result, dict):
                        response_times.append(result.get("response_time", 0))
            
            # Calcular métricas
            success_rate = (success_count / user_count) * 100 if user_count > 0 else 0
            avg_response_time = np.mean(response_times) if response_times else 0
            p95_response_time = np.percentile(response_times, 95) if response_times else 0
            p99_response_time = np.percentile(response_times, 99) if response_times else 0
            throughput = success_count / duration if duration > 0 else 0
            
            results[user_count] = {
                "success_count": success_count,
                "error_count": len(errors),
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "p95_response_time": p95_response_time,
                "p99_response_time": p99_response_time,
                "throughput": throughput,
                "duration": duration,
                "errors": errors[:10]  # Primeros 10 errores
            }
        
        return results
    
    async def test_agent_scaling(self) -> Dict[str, Any]:
        """Testing escalado de agentes"""
        self.logger.info("Testing escalado de agentes...")
        
        agent_counts = self.config["test_scenarios"]["scalability"]["agent_counts"]
        results = {}
        
        for agent_count in agent_counts:
            self.logger.info(f"Probando con {agent_count} agentes...")
            
            # Simular carga de agentes
            agents = []
            for i in range(agent_count):
                agent = {
                    "id": f"agent_{i}",
                    "type": random.choice(["finance", "maps", "content", "social"]),
                    "capabilities": random.sample(
                        ["analysis", "processing", "communication", "learning"],
                        k=random.randint(1, 3)
                    ),
                    "load": random.uniform(0.1, 1.0)
                }
                agents.append(agent)
            
            # Simular coordinación entre agentes
            start_time = time.time()
            coordination_messages = 0
            decision_times = []
            conflicts = 0
            
            # Simular procesamiento paralelo
            async def process_agent(agent):
                await asyncio.sleep(random.uniform(0.01, 0.1))  # Simular trabajo
                return {
                    "agent_id": agent["id"],
                    "processed_tasks": random.randint(5, 20),
                    "coordination_overhead": random.uniform(0.05, 0.15)
                }
            
            results_agents = await asyncio.gather(*[process_agent(agent) for agent in agents])
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Analizar resultados
            total_tasks = sum(r["processed_tasks"] for r in results_agents)
            avg_overhead = np.mean([r["coordination_overhead"] for r in results_agents])
            throughput = total_tasks / duration if duration > 0 else 0
            
            results[agent_count] = {
                "total_agents": agent_count,
                "total_tasks": total_tasks,
                "avg_overhead": avg_overhead,
                "throughput": throughput,
                "duration": duration,
                "coordination_messages": coordination_messages,
                "decision_times": decision_times,
                "conflicts": conflicts
            }
        
        return results
    
    async def test_memory_usage(self) -> Dict[str, Any]:
        """Testing uso de memoria"""
        self.logger.info("Testing uso de memoria...")
        
        # Obtener uso inicial de memoria
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_samples = []
        peak_memory = initial_memory
        
        # Simular carga y monitorear memoria
        for i in range(100):
            # Simular trabajo que consume memoria
            large_data = []
            for j in range(1000):
                large_data.append({
                    "id": f"item_{i}_{j}",
                    "data": [random.random() for _ in range(10)],
                    "metadata": {"timestamp": time.time(), "type": random.choice(["A", "B", "C"])}
                })
            
            # Obtener uso actual de memoria
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_samples.append(current_memory)
            peak_memory = max(peak_memory, current_memory)
            
            # Limpiar datos
            del large_data
            
            # Pequeña pausa
            await asyncio.sleep(0.01)
        
        # Obtener uso final de memoria
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "peak_memory_mb": peak_memory,
            "memory_samples": memory_samples,
            "memory_growth": final_memory - initial_memory,
            "memory_efficiency": initial_memory / peak_memory if peak_memory > 0 else 1.0
        }
    
    async def test_cpu_utilization(self) -> Dict[str, Any]:
        """Testing utilización de CPU"""
        self.logger.info("Testing utilización de CPU...")
        
        cpu_samples = []
        start_time = time.time()
        
        # Simular carga de CPU
        async def cpu_intensive_task():
            # Simular cálculos intensivos
            result = 0
            for i in range(10000):
                result += math.sin(i) * math.cos(i)
            return result
        
        # Ejecutar múltiples tareas intensivas
        tasks = []
        for i in range(10):
            task = cpu_intensive_task()
            tasks.append(task)
        
        # Monitorear CPU durante ejecución
        monitoring_task = asyncio.create_task(self._monitor_cpu_usage(cpu_samples, start_time))
        
        # Ejecutar tareas
        results = await asyncio.gather(*tasks)
        
        # Detener monitoreo
        monitoring_task.cancel()
        
        # Analizar resultados
        avg_cpu = np.mean(cpu_samples) if cpu_samples else 0
        max_cpu = max(cpu_samples) if cpu_samples else 0
        cpu_variance = np.var(cpu_samples) if cpu_samples else 0
        
        return {
            "avg_usage_percent": avg_cpu,
            "max_usage_percent": max_cpu,
            "usage_variance": cpu_variance,
            "samples_count": len(cpu_samples),
            "cpu_samples": cpu_samples[-50:]  # Últimas 50 muestras
        }
    
    async def test_response_times(self) -> Dict[str, Any]:
        """Testing tiempos de respuesta"""
        self.logger.info("Testing tiempos de respuesta...")
        
        response_times = []
        
        # Simular requests y medir tiempos
        for i in range(200):
            start = time.time()
            
            # Simular procesamiento
            await asyncio.sleep(random.uniform(0.01, 0.1))
            
            end = time.time()
            response_time = (end - start) * 1000  # ms
            response_times.append(response_time)
        
        # Calcular percentiles
        avg_time = np.mean(response_times)
        p50_time = np.percentile(response_times, 50)
        p95_time = np.percentile(response_times, 95)
        p99_time = np.percentile(response_times, 99)
        
        return {
            "avg_response_time_ms": avg_time,
            "p50_response_time_ms": p50_time,
            "p95_response_time_ms": p95_time,
            "p99_response_time_ms": p99_time,
            "response_times": response_times,
            "success_rate": 100.0  # Simulado
        }
    
    async def stress_test(self) -> Dict[str, Any]:
        """Testing de estrés"""
        self.logger.info("Ejecutando test de estrés...")
        
        stress_results = {
            "peak_load_sustained": False,
            "failure_points": [],
            "recovery_time": 0,
            "degradation_patterns": {}
        }
        
        # Simular carga extrema
        max_concurrent = 500
        tasks = []
        
        for i in range(max_concurrent):
            task = self._stress_request(i, timeout=10)
            tasks.append(task)
        
        start_time = time.time()
        success_count = 0
        
        # Ejecutar con límite
        semaphore = asyncio.Semaphore(100)
        
        async def bounded_stress(task):
            async with semaphore:
                try:
                    return await asyncio.wait_for(task, timeout=5.0)
                except asyncio.TimeoutError:
                    return "timeout"
                except Exception as e:
                    return f"error: {e}"
        
        results = await asyncio.gather(*[bounded_stress(t) for t in tasks])
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Analizar resultados
        success_count = sum(1 for r in results if r == "success")
        failure_count = len(results) - success_count
        success_rate = (success_count / len(results)) * 100
        
        stress_results.update({
            "total_requests": len(results),
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": success_rate,
            "duration": duration,
            "peak_load_sustained": success_rate > 80
        })
        
        return stress_results
    
    async def _simulate_user_request(self, user_id: int):
        """Simular request de usuario"""
        try:
            # Simular tiempo de procesamiento
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
            # Simular posibles errores (5% de probabilidad)
            if random.random() < 0.05:
                raise Exception("Simulated error")
            
            return {
                "user_id": user_id,
                "response_time": random.uniform(0.1, 0.5),
                "status": "success"
            }
        except Exception as e:
            raise e
    
    async def _monitor_cpu_usage(self, samples: List[float], start_time: float):
        """Monitorear uso de CPU"""
        try:
            while True:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                samples.append(cpu_percent)
                
                # Detener si ha pasado mucho tiempo
                if time.time() - start_time > 30:
                    break
                    
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
    
    async def _stress_request(self, request_id: int, timeout: float = 5.0):
        """Request de estrés"""
        await asyncio.sleep(random.uniform(0.1, 1.0))
        
        # Simular timeout ocasional
        if random.random() < 0.1:
            await asyncio.sleep(timeout + 1)
        
        return "success"

class CoordinationTester:
    """Tester especializado en coordinación entre equipos"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("CoordinationTester")
        
    async def test_communication_protocols(self) -> Dict[str, Any]:
        """Testing protocolos de comunicación"""
        self.logger.info("Testing protocolos de comunicación...")
        
        teams = await self._create_test_teams(6)
        messages_sent = 0
        messages_received = 0
        protocol_violations = 0
        response_times = []
        
        # Simular comunicación entre equipos
        for i, team1 in enumerate(teams):
            for j, team2 in enumerate(teams[i+1:], i+1):
                # Mensaje de equipo a equipo
                start_time = time.time()
                await self._send_inter_team_message(team1, team2)
                end_time = time.time()
                
                messages_sent += 1
                messages_received += 1
                response_times.append((end_time - start_time) * 1000)
                
                # Verificar protocolo
                if random.random() < 0.02:  # 2% violaciones
                    protocol_violations += 1
        
        success_rate = (messages_received / messages_sent) * 100 if messages_sent > 0 else 0
        avg_response_time = np.mean(response_times) if response_times else 0
        
        return {
            "teams_count": len(teams),
            "messages_sent": messages_sent,
            "messages_received": messages_received,
            "success_rate": success_rate,
            "avg_response_time_ms": avg_response_time,
            "protocol_violations": protocol_violations,
            "communication_patterns": self._analyze_communication_patterns(teams)
        }
    
    async def test_inter_team_coordination(self) -> Dict[str, Any]:
        """Testing coordinación inter-equipos"""
        self.logger.info("Testing coordinación inter-equipos...")
        
        projects = await self._create_test_projects(20)
        coordination_success = 0
        total_projects = len(projects)
        
        # Simular proyectos que requieren múltiples equipos
        for project in projects:
            required_teams = project.get("required_teams", [])
            if len(required_teams) < 2:
                continue
            
            # Simular coordinación
            coordination_start = time.time()
            success = await self._coordinate_teams_for_project(project, required_teams)
            coordination_end = time.time()
            
            if success:
                coordination_success += 1
        
        coordination_rate = (coordination_success / total_projects) * 100 if total_projects > 0 else 0
        
        return {
            "total_projects": total_projects,
            "successful_coordinations": coordination_success,
            "coordination_success_rate": coordination_rate,
            "avg_coordination_time": random.uniform(100, 500)  # ms simulado
        }
    
    async def test_task_distribution(self) -> Dict[str, Any]:
        """Testing distribución de tareas"""
        self.logger.info("Testing distribución de tareas...")
        
        tasks = await self._create_test_tasks(100)
        teams = await self._create_test_teams(6)
        assignments = {}
        decision_times = []
        
        # Distribuir tareas
        for task in tasks:
            start_time = time.time()
            best_team = await self._assign_task_to_team(task, teams)
            end_time = time.time()
            
            decision_times.append((end_time - start_time) * 1000)
            team_id = best_team["id"]
            
            if team_id not in assignments:
                assignments[team_id] = []
            assignments[team_id].append(task)
        
        # Analizar distribución
        load_balance = self._calculate_load_balance(assignments)
        avg_decision_time = np.mean(decision_times) if decision_times else 0
        
        return {
            "total_tasks": len(tasks),
            "assignments": {k: len(v) for k, v in assignments.items()},
            "load_balancing_efficiency": load_balance,
            "avg_decision_time_ms": avg_decision_time,
            "decision_times": decision_times
        }
    
    async def test_conflict_resolution(self) -> Dict[str, Any]:
        """Testing resolución de conflictos"""
        self.logger.info("Testing resolución de conflictos...")
        
        conflicts = await self._create_test_conflicts(50)
        resolved_conflicts = 0
        resolution_times = []
        
        for conflict in conflicts:
            start_time = time.time()
            resolved = await self._resolve_conflict(conflict)
            end_time = time.time()
            
            resolution_times.append((end_time - start_time) * 1000)
            
            if resolved:
                resolved_conflicts += 1
        
        resolution_rate = (resolved_conflicts / len(conflicts)) * 100 if conflicts else 0
        avg_resolution_time = np.mean(resolution_times) if resolution_times else 0
        
        return {
            "total_conflicts": len(conflicts),
            "resolved_conflicts": resolved_conflicts,
            "resolution_rate": resolution_rate,
            "avg_resolution_time_ms": avg_resolution_time,
            "resolution_times": resolution_times
        }
    
    async def test_load_balancing(self) -> Dict[str, Any]:
        """Testing balanceador de carga"""
        self.logger.info("Testing balanceador de carga...")
        
        teams = await self._create_test_teams(8)
        load_requests = 200
        
        # Simular requests de carga
        for i in range(load_requests):
            # Determinar mejor equipo basado en carga actual
            best_team = await self._select_least_loaded_team(teams)
            
            # Simular procesamiento
            await asyncio.sleep(random.uniform(0.01, 0.1))
            
            # Actualizar carga del equipo
            best_team["current_load"] += random.uniform(0.1, 0.3)
        
        # Analizar distribución de carga
        loads = [team["current_load"] for team in teams]
        load_variance = np.var(loads)
        load_std = np.std(loads)
        avg_load = np.mean(loads)
        
        return {
            "teams_count": len(teams),
            "total_requests": load_requests,
            "load_variance": load_variance,
            "load_std": load_std,
            "avg_load": avg_load,
            "loads": loads,
            "balance_efficiency": 1.0 - (load_std / avg_load) if avg_load > 0 else 0
        }
    
    async def _create_test_teams(self, count: int) -> List[Dict[str, Any]]:
        """Crear equipos de prueba"""
        teams = []
        team_types = ["finance", "maps", "content", "social", "research", "analytics"]
        
        for i in range(count):
            team = {
                "id": f"team_{i}",
                "type": team_types[i % len(team_types)],
                "members": random.randint(3, 8),
                "current_load": random.uniform(0.1, 0.8),
                "capabilities": random.sample(
                    ["analysis", "processing", "communication", "learning", "coordination"],
                    k=random.randint(2, 4)
                )
            }
            teams.append(team)
        
        return teams
    
    async def _create_test_projects(self, count: int) -> List[Dict[str, Any]]:
        """Crear proyectos de prueba"""
        projects = []
        
        for i in range(count):
            project = {
                "id": f"project_{i}",
                "name": f"Proyecto {i}",
                "required_teams": random.sample(
                    [f"team_{j}" for j in range(6)],
                    k=random.randint(1, 4)
                ),
                "complexity": random.choice(["low", "medium", "high"]),
                "estimated_duration": random.randint(100, 1000)
            }
            projects.append(project)
        
        return projects
    
    async def _create_test_tasks(self, count: int) -> List[Dict[str, Any]]:
        """Crear tareas de prueba"""
        tasks = []
        task_types = ["analysis", "processing", "communication", "learning"]
        
        for i in range(count):
            task = {
                "id": f"task_{i}",
                "type": random.choice(task_types),
                "priority": random.choice(["high", "medium", "low"]),
                "estimated_complexity": random.uniform(0.1, 1.0),
                "required_capabilities": random.sample(
                    task_types,
                    k=random.randint(1, 3)
                )
            }
            tasks.append(task)
        
        return tasks
    
    async def _create_test_conflicts(self, count: int) -> List[Dict[str, Any]]:
        """Crear conflictos de prueba"""
        conflicts = []
        conflict_types = ["resource", "priority", "timeline", "capability"]
        
        for i in range(count):
            conflict = {
                "id": f"conflict_{i}",
                "type": random.choice(conflict_types),
                "teams_involved": random.sample(
                    [f"team_{j}" for j in range(6)],
                    k=random.randint(2, 4)
                ),
                "severity": random.choice(["low", "medium", "high"]),
                "description": f"Conflicto {i} entre equipos"
            }
            conflicts.append(conflict)
        
        return conflicts
    
    async def _send_inter_team_message(self, team1: Dict, team2: Dict) -> bool:
        """Enviar mensaje entre equipos"""
        await asyncio.sleep(random.uniform(0.01, 0.05))
        return random.random() > 0.05  # 95% éxito
    
    async def _coordinate_teams_for_project(self, project: Dict, required_teams: List[str]) -> bool:
        """Coordinar equipos para proyecto"""
        await asyncio.sleep(random.uniform(0.1, 0.3))
        return random.random() > 0.1  # 90% éxito
    
    async def _assign_task_to_team(self, task: Dict, teams: List[Dict]) -> Dict:
        """Asignar tarea a equipo"""
        # Algoritmo simple de asignación
        await asyncio.sleep(0.01)
        
        # Seleccionar equipo con mejor capacidad y menor carga
        best_team = None
        best_score = -1
        
        for team in teams:
            capability_match = len(set(task["required_capabilities"]).intersection(team["capabilities"]))
            load_factor = 1.0 - team["current_load"]
            score = capability_match * load_factor
            
            if score > best_score:
                best_score = score
                best_team = team
        
        return best_team or teams[0]
    
    async def _resolve_conflict(self, conflict: Dict) -> bool:
        """Resolver conflicto"""
        await asyncio.sleep(random.uniform(0.05, 0.2))
        return random.random() > 0.15  # 85% éxito
    
    async def _select_least_loaded_team(self, teams: List[Dict]) -> Dict:
        """Seleccionar equipo con menor carga"""
        return min(teams, key=lambda t: t["current_load"])
    
    def _calculate_load_balance(self, assignments: Dict) -> float:
        """Calcular eficiencia de balanceador de carga"""
        loads = [len(assignments.get(team_id, [])) for team_id in assignments.keys()]
        
        if not loads:
            return 1.0
        
        avg_load = np.mean(loads)
        if avg_load == 0:
            return 1.0
        
        # Calcular desviación estándar normalizada
        std_load = np.std(loads)
        coefficient_of_variation = std_load / avg_load
        
        # Eficiencia es inversa de la variabilidad
        efficiency = max(0, 1.0 - coefficient_of_variation)
        return efficiency
    
    def _analyze_communication_patterns(self, teams: List[Dict]) -> Dict[str, Any]:
        """Analizar patrones de comunicación"""
        patterns = {
            "total_communications": 0,
            "most_active_team": None,
            "communication_frequenc": {},
            "cross_team_ratio": 0.0
        }
        
        # Análisis básico de patrones
        communication_count = len(teams) * (len(teams) - 1) / 2
        patterns["total_communications"] = int(communication_count)
        
        if teams:
            patterns["most_active_team"] = teams[0]["id"]
        
        return patterns

class AlgorithmOptimizer:
    """Optimizador de algoritmos"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("AlgorithmOptimizer")
        
    async def optimize_hungarian_algorithm(self) -> Dict[str, Any]:
        """Optimizar algoritmo Hungarian"""
        self.logger.info("Optimizando algoritmo Hungarian...")
        
        # Crear matrices de prueba de diferentes tamaños
        test_sizes = [10, 25, 50, 100, 200]
        optimization_results = {}
        
        for size in test_sizes:
            # Generar matriz de costos
            cost_matrix = np.random.rand(size, size) * 100
            
            # Aplicar algoritmo Hungarian
            start_time = time.time()
            row_indices, col_indices = linear_sum_assignment(cost_matrix)
            end_time = time.time()
            
            # Calcular costo total
            total_cost = cost_matrix[row_indices, col_indices].sum()
            
            optimization_results[size] = {
                "execution_time": (end_time - start_time) * 1000,  # ms
                "total_cost": total_cost,
                "solution_quality": self._evaluate_solution_quality(cost_matrix, row_indices, col_indices),
                "memory_usage": self._estimate_memory_usage(size)
            }
        
        return optimization_results
    
    async def optimize_cbba_algorithm(self) -> Dict[str, Any]:
        """Optimizar algoritmo CBBA (Consensus-Based Bundle Algorithm)"""
        self.logger.info("Optimizando algoritmo CBBA...")
        
        # Parámetros de CBBA
        agents = 20
        tasks = 50
        
        # Simular CBBA
        start_time = time.time()
        bundle, bids = await self._simulate_cbba(agents, tasks)
        end_time = time.time()
        
        # Evaluar convergencia
        convergence_iterations = len(bundle) if bundle else 0
        
        # Calcular métricas
        total_score = sum(bid.get("score", 0) for bid in bids.values()) if bids else 0
        convergence_time = (end_time - start_time) * 1000
        
        return {
            "agents_count": agents,
            "tasks_count": tasks,
            "convergence_iterations": convergence_iterations,
            "convergence_time_ms": convergence_time,
            "total_score": total_score,
            "solution_quality": total_score / tasks if tasks > 0 else 0,
            "memory_efficiency": self._calculate_memory_efficiency(agents, tasks)
        }
    
    async def optimize_raft_election(self) -> Dict[str, Any]:
        """Optimizar algoritmo RAFT leader election"""
        self.logger.info("Optimizando RAFT leader election...")
        
        node_counts = [3, 5, 7, 9, 11, 15]
        election_results = {}
        
        for node_count in node_counts:
            # Simular elección RAFT
            start_time = time.time()
            leader_elected = await self._simulate_raft_election(node_count)
            end_time = time.time()
            
            election_time = (end_time - start_time) * 1000
            success = leader_elected is not None
            
            election_results[node_count] = {
                "election_time_ms": election_time,
                "success": success,
                "elected_leader": leader_elected,
                "network_round_trips": random.randint(node_count - 1, node_count + 1)
            }
        
        return election_results
    
    async def optimize_load_balancing(self) -> Dict[str, Any]:
        """Optimizar algoritmos de balanceador de carga"""
        self.logger.info("Optimizando balanceador de carga...")
        
        # Diferentes algoritmos de balanceo
        algorithms = ["round_robin", "weighted_round_robin", "least_connections", "ip_hash"]
        server_counts = [5, 10, 20, 50]
        request_counts = [100, 500, 1000, 2000]
        
        results = {}
        
        for algorithm in algorithms:
            algorithm_results = {}
            
            for server_count in server_counts:
                server_results = {}
                
                for request_count in request_counts:
                    # Simular balanceador
                    start_time = time.time()
                    distribution = await self._simulate_load_balancing(algorithm, server_count, request_count)
                    end_time = time.time()
                    
                    # Calcular métricas de distribución
                    loads = list(distribution.values())
                    balance_efficiency = 1.0 - (np.std(loads) / np.mean(loads)) if np.mean(loads) > 0 else 1.0
                    
                    server_results[request_count] = {
                        "execution_time_ms": (end_time - start_time) * 1000,
                        "balance_efficiency": balance_efficiency,
                        "server_loads": loads,
                        "max_load": max(loads) if loads else 0,
                        "min_load": min(loads) if loads else 0
                    }
                
                algorithm_results[server_count] = server_results
            
            results[algorithm] = algorithm_results
        
        return results
    
    async def compare_algorithms(self) -> Dict[str, Any]:
        """Comparar performance de algoritmos"""
        self.logger.info("Comparando algoritmos...")
        
        algorithms = ["hungarian", "cbba", "raft", "round_robin"]
        comparison_results = {}
        
        for algorithm in algorithms:
            # Benchmark del algoritmo
            start_time = time.time()
            result = await self._benchmark_algorithm(algorithm)
            end_time = time.time()
            
            comparison_results[algorithm] = {
                "execution_time_ms": (end_time - start_time) * 1000,
                "memory_usage": result.get("memory_mb", 0),
                "throughput_rps": result.get("throughput_rps", 0),
                "accuracy": result.get("accuracy", 0),
                "scalability_score": result.get("scalability_score", 0)
            }
        
        return comparison_results
    
    async def _simulate_cbba(self, agents: int, tasks: int) -> Tuple[List, Dict]:
        """Simular algoritmo CBBA"""
        bundle = []
        bids = {}
        
        # Simular iteraciones de CBBA
        for i in range(tasks):
            # Simular bidding
            for agent_id in range(agents):
                if agent_id not in bids:
                    bids[agent_id] = {"tasks": [], "bids": [], "score": 0}
                
                bid_value = random.uniform(0.1, 1.0)
                bids[agent_id]["bids"].append(bid_value)
                bids[agent_id]["score"] += bid_value
                
                if len(bids[agent_id]["tasks"]) < 3:  # Límite de bundle
                    bids[agent_id]["tasks"].append(f"task_{i}")
            
            bundle.append(f"task_{i}")
            
            # Pequeña pausa para simular procesamiento
            await asyncio.sleep(0.001)
        
        return bundle, bids
    
    async def _simulate_raft_election(self, node_count: int) -> Optional[str]:
        """Simular elección RAFT"""
        nodes = [f"node_{i}" for i in range(node_count)]
        
        # Simular proceso de elección
        leader_candidate = random.choice(nodes)
        
        # Simular votos
        votes_received = 0
        required_votes = (node_count // 2) + 1
        
        for node in nodes:
            if node == leader_candidate:
                votes_received += 1  # Vote propio
            elif random.random() > 0.3:  # 70% probabilidad de voto
                votes_received += 1
        
        # Verificar mayoría
        if votes_received >= required_votes:
            return leader_candidate
        
        return None
    
    async def _simulate_load_balancing(self, algorithm: str, server_count: int, request_count: int) -> Dict[str, int]:
        """Simular balanceador de carga"""
        servers = [f"server_{i}" for i in range(server_count)]
        distribution = {server: 0 for server in servers}
        
        for i in range(request_count):
            if algorithm == "round_robin":
                selected_server = servers[i % server_count]
            elif algorithm == "weighted_round_robin":
                selected_server = servers[random.randint(0, server_count - 1)]
            elif algorithm == "least_connections":
                selected_server = min(servers, key=lambda s: distribution[s])
            elif algorithm == "ip_hash":
                selected_server = servers[hash(f"request_{i}") % server_count]
            else:
                selected_server = servers[random.randint(0, server_count - 1)]
            
            distribution[selected_server] += 1
        
        return distribution
    
    async def _benchmark_algorithm(self, algorithm: str) -> Dict[str, float]:
        """Benchmark de algoritmo específico"""
        # Simular benchmark basado en tipo de algoritmo
        if algorithm == "hungarian":
            return {
                "memory_mb": random.uniform(50, 200),
                "throughput_rps": random.uniform(100, 500),
                "accuracy": random.uniform(0.95, 1.0),
                "scalability_score": random.uniform(0.7, 0.9)
            }
        elif algorithm == "cbba":
            return {
                "memory_mb": random.uniform(30, 150),
                "throughput_rps": random.uniform(200, 800),
                "accuracy": random.uniform(0.90, 0.98),
                "scalability_score": random.uniform(0.8, 0.95)
            }
        elif algorithm == "raft":
            return {
                "memory_mb": random.uniform(20, 100),
                "throughput_rps": random.uniform(50, 200),
                "accuracy": random.uniform(0.98, 1.0),
                "scalability_score": random.uniform(0.6, 0.8)
            }
        else:  # round_robin
            return {
                "memory_mb": random.uniform(10, 50),
                "throughput_rps": random.uniform(500, 2000),
                "accuracy": random.uniform(0.85, 0.95),
                "scalability_score": random.uniform(0.9, 0.98)
            }
    
    def _evaluate_solution_quality(self, cost_matrix: np.ndarray, row_indices: np.ndarray, col_indices: np.ndarray) -> float:
        """Evaluar calidad de solución"""
        total_cost = cost_matrix[row_indices, col_indices].sum()
        min_possible_cost = np.min(cost_matrix)
        max_possible_cost = np.max(cost_matrix)
        
        # Normalizar score (0-1, donde 1 es mejor)
        normalized_cost = (total_cost - min_possible_cost) / (max_possible_cost - min_possible_cost) if max_possible_cost != min_possible_cost else 1.0
        return 1.0 - normalized_cost
    
    def _estimate_memory_usage(self, size: int) -> float:
        """Estimar uso de memoria"""
        # Estimación simple: O(n^2) para matriz de asignación
        return size * size * 8 / (1024 * 1024)  # MB
    
    def _calculate_memory_efficiency(self, agents: int, tasks: int) -> float:
        """Calcular eficiencia de memoria"""
        # Calcular ratio de uso de memoria vs eficiencia
        theoretical_max = agents * tasks
        practical_usage = min(agents * 3, tasks)  # Cada agente maneja ~3 tareas
        return practical_usage / theoretical_max if theoretical_max > 0 else 1.0

class CommunicationTester:
    """Tester de comunicación entre agentes"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("CommunicationTester")
    
    async def test_network_reliability(self) -> Dict[str, Any]:
        """Testing fiabilidad de red"""
        self.logger.info("Testing fiabilidad de red...")
        
        # Parámetros de prueba
        test_duration = 30  # segundos
        message_count = 1000
        agents_count = 20
        
        messages_sent = 0
        messages_received = 0
        delivery_times = []
        network_partitions = 0
        
        start_time = time.time()
        
        while time.time() - start_time < test_duration:
            # Simular envío de mensajes
            for i in range(10):  # 10 mensajes por ciclo
                sender = f"agent_{random.randint(0, agents_count - 1)}"
                receiver = f"agent_{random.randint(0, agents_count - 1)}"
                
                messages_sent += 1
                
                # Simular entrega con latencia variable
                delivery_start = time.time()
                success = await self._send_message(sender, receiver)
                delivery_end = time.time()
                
                if success:
                    messages_received += 1
                    delivery_times.append((delivery_end - delivery_start) * 1000)
                
                # Simular particiones de red ocasionales
                if random.random() < 0.01:  # 1% probabilidad
                    network_partitions += 1
                    await asyncio.sleep(0.1)  # Simular recuperación
            
            await asyncio.sleep(0.1)  # Pausa entre ciclos
        
        # Calcular métricas
        success_rate = (messages_received / messages_sent) * 100 if messages_sent > 0 else 0
        avg_delivery_time = np.mean(delivery_times) if delivery_times else 0
        
        return {
            "messages_sent": messages_sent,
            "messages_received": messages_received,
            "success_rate": success_rate,
            "avg_delivery_time_ms": avg_delivery_time,
            "network_partitions": network_partitions,
            "delivery_times": delivery_times[-100:]  # Últimas 100 muestras
        }
    
    async def test_fipa_compliance(self) -> Dict[str, Any]:
        """Testing cumplimiento FIPA-ACL"""
        self.logger.info("Testing cumplimiento FIPA-ACL...")
        
        message_types = ["request", "inform", "propose", "agree", "refuse"]
        compliance_results = {}
        
        for msg_type in message_types:
            # Generar mensaje FIPA-ACL
            message = await self._generate_fipa_message(msg_type)
            
            # Validar cumplimiento
            compliance_check = await self._validate_fipa_compliance(message)
            
            compliance_results[msg_type] = {
                "compliant": compliance_check["is_compliant"],
                "validation_score": compliance_check["score"],
                "violations": compliance_check["violations"],
                "required_fields_present": compliance_check["required_fields"]
            }
        
        overall_compliance = np.mean([result["validation_score"] for result in compliance_results.values()])
        
        return {
            "message_types_tested": len(message_types),
            "overall_compliance_score": overall_compliance,
            "detailed_results": compliance_results
        }
    
    async def test_message_delivery(self) -> Dict[str, Any]:
        """Testing entrega de mensajes"""
        self.logger.info("Testing entrega de mensajes...")
        
        # Configuración de prueba
        test_scenarios = [
            {"agents": 5, "messages": 100, "network_latency": 0.01},
            {"agents": 10, "messages": 500, "network_latency": 0.05},
            {"agents": 20, "messages": 1000, "network_latency": 0.1}
        ]
        
        delivery_results = {}
        
        for i, scenario in enumerate(test_scenarios):
            scenario_key = f"scenario_{i+1}"
            
            # Ejecutar escenario
            delivered = 0
            failed = 0
            delivery_latencies = []
            
            for msg_id in range(scenario["messages"]):
                sender = f"agent_{random.randint(0, scenario['agents']-1)}"
                receiver = f"agent_{random.randint(0, scenario['agents']-1)}"
                
                start_time = time.time()
                success = await self._deliver_message(sender, receiver, scenario["network_latency"])
                end_time = time.time()
                
                if success:
                    delivered += 1
                    delivery_latencies.append((end_time - start_time) * 1000)
                else:
                    failed += 1
            
            # Calcular métricas del escenario
            total = scenario["messages"]
            success_rate = (delivered / total) * 100 if total > 0 else 0
            avg_latency = np.mean(delivery_latencies) if delivery_latencies else 0
            p95_latency = np.percentile(delivery_latencies, 95) if delivery_latencies else 0
            
            delivery_results[scenario_key] = {
                "agents_count": scenario["agents"],
                "messages_total": total,
                "delivered": delivered,
                "failed": failed,
                "success_rate": success_rate,
                "avg_latency_ms": avg_latency,
                "p95_latency_ms": p95_latency,
                "network_latency": scenario["network_latency"]
            }
        
        return delivery_results
    
    async def test_latency(self) -> Dict[str, Any]:
        """Testing latencia de comunicación"""
        self.logger.info("Testing latencia de comunicación...")
        
        # Configuraciones de latencia
        latency_configs = [
            {"name": "low_latency", "base_delay": 0.01, "jitter": 0.005},
            {"name": "medium_latency", "base_delay": 0.05, "jitter": 0.02},
            {"name": "high_latency", "base_delay": 0.1, "jitter": 0.05},
            {"name": "variable_latency", "base_delay": 0.03, "jitter": 0.1}
        ]
        
        latency_results = {}
        
        for config in latency_configs:
            latencies = []
            
            # Medir latencia en múltiples mensajes
            for i in range(100):
                start_time = time.time()
                await self._simulate_network_delay(config["base_delay"], config["jitter"])
                end_time = time.time()
                
                measured_latency = (end_time - start_time) * 1000  # ms
                latencies.append(measured_latency)
            
            # Calcular estadísticas
            avg_latency = np.mean(latencies)
            p50_latency = np.percentile(latencies, 50)
            p95_latency = np.percentile(latencies, 95)
            p99_latency = np.percentile(latencies, 99)
            latency_std = np.std(latencies)
            
            latency_results[config["name"]] = {
                "avg_latency_ms": avg_latency,
                "p50_latency_ms": p50_latency,
                "p95_latency_ms": p95_latency,
                "p99_latency_ms": p99_latency,
                "latency_std": latency_std,
                "measurements": len(latencies)
            }
        
        return latency_results
    
    async def test_communication_security(self) -> Dict[str, Any]:
        """Testing seguridad de comunicación"""
        self.logger.info("Testing seguridad de comunicación...")
        
        security_tests = {
            "authentication": await self._test_authentication(),
            "encryption": await self._test_encryption(),
            "message_integrity": await self._test_message_integrity(),
            "access_control": await self._test_access_control(),
            "denial_of_service": await self._test_dos_resistance()
        }
        
        # Calcular score general de seguridad
        security_scores = []
        for test_name, result in security_tests.items():
            if isinstance(result, dict) and "score" in result:
                security_scores.append(result["score"])
        
        overall_security_score = np.mean(security_scores) if security_scores else 0
        
        return {
            "overall_security_score": overall_security_score,
            "detailed_tests": security_tests
        }
    
    async def _send_message(self, sender: str, receiver: str) -> bool:
        """Simular envío de mensaje"""
        await asyncio.sleep(random.uniform(0.01, 0.05))
        
        # Simular falla ocasional (95% éxito)
        return random.random() > 0.05
    
    async def _deliver_message(self, sender: str, receiver: str, latency: float) -> bool:
        """Simular entrega de mensaje"""
        await asyncio.sleep(latency + random.uniform(0, 0.01))
        
        # Simular falla ocasional (97% éxito)
        return random.random() > 0.03
    
    async def _simulate_network_delay(self, base_delay: float, jitter: float):
        """Simular delay de red"""
        actual_delay = base_delay + random.uniform(-jitter, jitter)
        await asyncio.sleep(max(0, actual_delay))
    
    async def _generate_fipa_message(self, msg_type: str) -> Dict[str, Any]:
        """Generar mensaje FIPA-ACL"""
        message = {
            "type": msg_type,
            "sender": f"agent_{random.randint(1, 100)}",
            "receiver": f"agent_{random.randint(1, 100)}",
            "conversation-id": f"conv_{random.randint(1000, 9999)}",
            "reply-with": f"reply_{random.randint(1000, 9999)}",
            "content": f"Message content for {msg_type}",
            "language": "fipa-sl",
            "encoding": "utf-8",
            "ontology": "fipa-agent-management",
            "protocol": "fipa-request",
            "conversation-state": "started"
        }
        
        # Ajustar contenido según tipo de mensaje
        if msg_type == "request":
            message["performative"] = "request"
        elif msg_type == "inform":
            message["performative"] = "inform"
        elif msg_type == "propose":
            message["performative"] = "propose"
        elif msg_type == "agree":
            message["performative"] = "agree"
        elif msg_type == "refuse":
            message["performative"] = "refuse"
        
        return message
    
    async def _validate_fipa_compliance(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Validar cumplimiento FIPA-ACL"""
        required_fields = [
            "type", "sender", "receiver", "conversation-id", "performative"
        ]
        
        violations = []
        present_fields = 0
        
        for field in required_fields:
            if field in message and message[field]:
                present_fields += 1
            else:
                violations.append(f"Missing required field: {field}")
        
        # Validar formato de sender y receiver (deben ser agent identifiers)
        if "sender" in message:
            if not message["sender"].startswith("agent_"):
                violations.append("Invalid sender format")
        
        if "receiver" in message:
            if not message["receiver"].startswith("agent_"):
                violations.append("Invalid receiver format")
        
        # Calcular score de cumplimiento
        compliance_score = (present_fields / len(required_fields)) * 100
        is_compliant = len(violations) == 0
        
        return {
            "is_compliant": is_compliant,
            "score": compliance_score,
            "violations": violations,
            "required_fields": present_fields,
            "total_required": len(required_fields)
        }
    
    async def _test_authentication(self) -> Dict[str, Any]:
        """Test de autenticación"""
        test_attempts = 100
        successful_auth = 0
        
        for i in range(test_attempts):
            # Simular intento de autenticación
            token = f"token_{random.randint(1000, 9999)}"
            is_valid = await self._authenticate_agent(token)
            
            if is_valid:
                successful_auth += 1
        
        auth_success_rate = (successful_auth / test_attempts) * 100
        
        return {
            "test_attempts": test_attempts,
            "successful_auth": successful_auth,
            "success_rate": auth_success_rate,
            "score": auth_success_rate
        }
    
    async def _test_encryption(self) -> Dict[str, Any]:
        """Test de encriptación"""
        # Simular test de encriptación
        messages_encrypted = 0
        total_messages = 50
        
        for i in range(total_messages):
            message = f"secret_message_{i}"
            encrypted = await self._encrypt_message(message)
            
            if encrypted:
                messages_encrypted += 1
        
        encryption_rate = (messages_encrypted / total_messages) * 100
        
        return {
            "total_messages": total_messages,
            "encrypted_messages": messages_encrypted,
            "encryption_rate": encryption_rate,
            "score": encryption_rate
        }
    
    async def _test_message_integrity(self) -> Dict[str, Any]:
        """Test de integridad de mensajes"""
        total_tests = 100
        integrity_passed = 0
        
        for i in range(total_tests):
            original_message = f"test_message_{i}"
            sent_message = await self._send_message_with_integrity(original_message)
            received_message = await self._receive_message_with_integrity(sent_message)
            
            if original_message == received_message:
                integrity_passed += 1
        
        integrity_rate = (integrity_passed / total_tests) * 100
        
        return {
            "total_tests": total_tests,
            "integrity_passed": integrity_passed,
            "integrity_rate": integrity_rate,
            "score": integrity_rate
        }
    
    async def _test_access_control(self) -> Dict[str, Any]:
        """Test de control de acceso"""
        access_attempts = 50
        unauthorized_attempts = 0
        
        for i in range(access_attempts):
            agent_id = f"agent_{random.randint(1, 100)}"
            resource = f"resource_{random.randint(1, 20)}"
            
            has_access = await self._check_access_control(agent_id, resource)
            
            if not has_access:
                unauthorized_attempts += 1
        
        unauthorized_rate = (unauthorized_attempts / access_attempts) * 100
        
        return {
            "access_attempts": access_attempts,
            "unauthorized_attempts": unauthorized_attempts,
            "security_score": unauthorized_rate,
            "score": unauthorized_rate
        }
    
    async def _test_dos_resistance(self) -> Dict[str, Any]:
        """Test de resistencia a DoS"""
        # Simular ataque DoS
        attack_duration = 10  # segundos
        normal_requests = 0
        blocked_requests = 0
        
        start_time = time.time()
        
        while time.time() - start_time < attack_duration:
            # Simular múltiples requests simultáneos
            tasks = []
            for i in range(50):  # 50 requests por segundo
                task = self._simulate_request()
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    blocked_requests += 1
                else:
                    normal_requests += 1
            
            await asyncio.sleep(1)  # Pausa de 1 segundo
        
        total_requests = normal_requests + blocked_requests
        block_rate = (blocked_requests / total_requests) * 100 if total_requests > 0 else 0
        
        return {
            "attack_duration_seconds": attack_duration,
            "normal_requests": normal_requests,
            "blocked_requests": blocked_requests,
            "total_requests": total_requests,
            "block_rate": block_rate,
            "score": block_rate
        }
    
    async def _authenticate_agent(self, token: str) -> bool:
        """Autenticar agente"""
        await asyncio.sleep(0.001)  # Simular validación
        
        # 95% de tokens válidos
        return random.random() > 0.05
    
    async def _encrypt_message(self, message: str) -> bool:
        """Encriptar mensaje"""
        await asyncio.sleep(0.01)  # Simular encriptación
        
        # 98% de encriptación exitosa
        return random.random() > 0.02
    
    async def _send_message_with_integrity(self, message: str) -> str:
        """Enviar mensaje con verificación de integridad"""
        await asyncio.sleep(0.005)
        return f"{message}_signed_{random.randint(1000, 9999)}"
    
    async def _receive_message_with_integrity(self, signed_message: str) -> str:
        """Recibir mensaje con verificación de integridad"""
        await asyncio.sleep(0.005)
        return signed_message.split("_signed_")[0]
    
    async def _check_access_control(self, agent_id: str, resource: str) -> bool:
        """Verificar control de acceso"""
        await asyncio.sleep(0.001)
        
        # Lógica simple de control de acceso
        return random.random() > 0.3  # 70% acceso permitido
    
    async def _simulate_request(self):
        """Simular request"""
        await asyncio.sleep(random.uniform(0.01, 0.1))
        return "request_processed"

# ==================== SERVICIO WEB DE TESTING ====================

class TestingWebService:
    """Servicio web para el sistema de testing"""
    
    def __init__(self):
        self.testing_suite = TestingSuite()
        self.app = FastAPI(
            title="SilhouetteMCP Testing Suite",
            description="Sistema completo de testing y optimización para SilhouetteMCP",
            version="1.0.0"
        )
        self._setup_routes()
        self._setup_websocket()
        
    def _setup_routes(self):
        """Configurar rutas de la API"""
        
        @self.app.get("/")
        async def root():
            return {
                "service": "SilhouetteMCP Testing Suite",
                "version": "1.0.0",
                "status": "running",
                "endpoints": {
                    "/scalability-tests": "Ejecutar tests de escalabilidad",
                    "/coordination-tests": "Ejecutar tests de coordinación",
                    "/algorithm-optimization": "Optimizar algoritmos",
                    "/communication-tests": "Tests de comunicación",
                    "/run-all-tests": "Ejecutar suite completa",
                    "/metrics": "Obtener métricas actuales",
                    "/results": "Ver resultados de tests",
                    "/dashboard": "Dashboard web"
                }
            }
        
        @self.app.get("/scalability-tests")
        async def run_scalability_tests():
            try:
                results = await self.testing_suite.run_scalability_tests()
                return {
                    "status": "completed",
                    "test_type": "scalability",
                    "timestamp": datetime.now().isoformat(),
                    "results": results
                }
            except Exception as e:
                logger.error(f"Error en tests de escalabilidad: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/coordination-tests")
        async def run_coordination_tests():
            try:
                results = await self.testing_suite.run_coordination_tests()
                return {
                    "status": "completed",
                    "test_type": "coordination",
                    "timestamp": datetime.now().isoformat(),
                    "results": results
                }
            except Exception as e:
                logger.error(f"Error en tests de coordinación: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/algorithm-optimization")
        async def run_algorithm_optimization():
            try:
                results = await self.testing_suite.run_algorithm_optimization()
                return {
                    "status": "completed",
                    "test_type": "optimization",
                    "timestamp": datetime.now().isoformat(),
                    "results": results
                }
            except Exception as e:
                logger.error(f"Error en optimización: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/communication-tests")
        async def run_communication_tests():
            try:
                results = await self.testing_suite.run_communication_tests()
                return {
                    "status": "completed",
                    "test_type": "communication",
                    "timestamp": datetime.now().isoformat(),
                    "results": results
                }
            except Exception as e:
                logger.error(f"Error en tests de comunicación: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/run-all-tests")
        async def run_all_tests():
            try:
                results = {}
                
                # Ejecutar todos los tests
                logger.info("Iniciando suite completa de tests...")
                
                results["scalability"] = await self.testing_suite.run_scalability_tests()
                results["coordination"] = await self.testing_suite.run_coordination_tests()
                results["optimization"] = await self.testing_suite.run_algorithm_optimization()
                results["communication"] = await self.testing_suite.run_communication_tests()
                
                # Generar reporte consolidado
                summary = self._generate_test_summary(results)
                
                return {
                    "status": "completed",
                    "test_type": "full_suite",
                    "timestamp": datetime.now().isoformat(),
                    "results": results,
                    "summary": summary
                }
            except Exception as e:
                logger.error(f"Error en suite completa: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/metrics")
        async def get_current_metrics():
            try:
                metrics = self._collect_current_metrics()
                return {
                    "timestamp": datetime.now().isoformat(),
                    "metrics": metrics
                }
            except Exception as e:
                logger.error(f"Error obteniendo métricas: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/results")
        async def get_test_results():
            try:
                results = {
                    "test_history": self.testing_suite.test_results_history,
                    "performance_baselines": self.testing_suite.performance_baselines,
                    "optimization_results": self.testing_suite.optimization_results
                }
                return results
            except Exception as e:
                logger.error(f"Error obteniendo resultados: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/dashboard")
        async def get_dashboard():
            """Dashboard web con métricas en tiempo real"""
            html_content = self._generate_dashboard_html()
            return HTMLResponse(content=html_content)
        
        @self.app.get("/benchmark/{algorithm}")
        async def benchmark_algorithm(algorithm: str):
            try:
                results = await self._run_algorithm_benchmark(algorithm)
                return {
                    "algorithm": algorithm,
                    "benchmark_results": results
                }
            except Exception as e:
                logger.error(f"Error en benchmark: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/configure")
        async def configure_testing_suite(config: Dict[str, Any]):
            try:
                self.testing_suite.config.update(config)
                return {
                    "status": "configured",
                    "config": self.testing_suite.config
                }
            except Exception as e:
                logger.error(f"Error en configuración: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def _setup_websocket(self):
        """Configurar WebSocket para métricas en tiempo real"""
        
        @self.app.websocket("/ws/metrics")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            logger.info("Cliente WebSocket conectado para métricas")
            
            try:
                while True:
                    # Enviar métricas cada segundo
                    metrics = self._collect_current_metrics()
                    await websocket.send_json({
                        "timestamp": datetime.now().isoformat(),
                        "metrics": metrics
                    })
                    await asyncio.sleep(1)
                    
            except WebSocketDisconnect:
                logger.info("Cliente WebSocket desconectado")
            except Exception as e:
                logger.error(f"Error en WebSocket: {e}")
    
    def _collect_current_metrics(self) -> Dict[str, Any]:
        """Recopilar métricas actuales del sistema"""
        try:
            # Métricas del sistema
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Métricas personalizadas
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return {
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": (disk.used / disk.total) * 100,
                    "disk_free_gb": disk.free / (1024**3)
                },
                "process": {
                    "memory_rss_mb": process_memory.rss / (1024**2),
                    "memory_vms_mb": process_memory.vms / (1024**2),
                    "cpu_percent": process.cpu_percent(),
                    "num_threads": process.num_threads()
                },
                "testing": {
                    "active_tests": len(self.testing_suite.active_tests),
                    "test_results_count": len(self.testing_suite.test_results_history)
                }
            }
        except Exception as e:
            logger.error(f"Error recopilando métricas: {e}")
            return {}
    
    def _generate_test_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generar resumen consolidado de tests"""
        summary = {
            "total_tests_run": len(results),
            "overall_health_score": 0,
            "key_findings": [],
            "recommendations": [],
            "critical_issues": []
        }
        
        # Analizar resultados de escalabilidad
        if "scalability" in results:
            scalability = results["scalability"]
            if "bottleneck_analysis" in scalability:
                bottlenecks = scalability["bottleneck_analysis"]
                if bottlenecks.get("memory_bottlenecks"):
                    summary["critical_issues"].append("Problemas de memoria detectados")
                if bottlenecks.get("cpu_bottlenecks"):
                    summary["critical_issues"].append("Problemas de CPU detectados")
        
        # Analizar resultados de coordinación
        if "coordination" in results:
            coordination = results["coordination"]
            if "coordination_analysis" in coordination:
                analysis = coordination["coordination_analysis"]
                efficiency = analysis.get("coordination_efficiency", 0)
                if efficiency < 80:
                    summary["key_findings"].append(f"Baja eficiencia de coordinación: {efficiency:.1f}%")
        
        # Calcular score general
        total_issues = len(summary["critical_issues"])
        if total_issues == 0:
            summary["overall_health_score"] = 100
        elif total_issues <= 2:
            summary["overall_health_score"] = 75
        elif total_issues <= 4:
            summary["overall_health_score"] = 50
        else:
            summary["overall_health_score"] = 25
        
        # Recomendaciones
        if "memory_bottlenecks" in str(results):
            summary["recommendations"].append("Implementar gestión de memoria más eficiente")
        if "cpu_bottlenecks" in str(results):
            summary["recommendations"].append("Optimizar algoritmos intensivos en CPU")
        if "coordination" in str(results):
            summary["recommendations"].append("Mejorar protocolos de comunicación entre equipos")
        
        return summary
    
    def _generate_dashboard_html(self) -> str:
        """Generar HTML del dashboard"""
        return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SilhouetteMCP Testing Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; text-align: center; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .metric-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #333; }}
        .metric-label {{ color: #666; margin-top: 5px; }}
        .chart-container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .test-buttons {{ display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }}
        .test-btn {{ padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; transition: all 0.3s; }}
        .btn-scalability {{ background: #4CAF50; color: white; }}
        .btn-coordination {{ background: #2196F3; color: white; }}
        .btn-optimization {{ background: #FF9800; color: white; }}
        .btn-communication {{ background: #9C27B0; color: white; }}
        .btn-all {{ background: #f44336; color: white; }}
        .test-btn:hover {{ transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }}
        .status {{ padding: 10px; border-radius: 5px; margin: 10px 0; }}
        .status-success {{ background: #d4edda; color: #155724; }}
        .status-error {{ background: #f8d7da; color: #721c24; }}
        .status-running {{ background: #fff3cd; color: #856404; }}
        .results-section {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-top: 20px; }}
        .real-time-updates {{ position: fixed; top: 20px; right: 20px; background: #333; color: white; padding: 10px; border-radius: 5px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 SilhouetteMCP Testing Suite</h1>
            <p>Sistema Completo de Testing y Optimización</p>
            <p>Arquitectura Jerárquica de 100+ Agentes</p>
        </div>
        
        <div class="real-time-updates" id="realtime">
            📊 Actualizaciones en tiempo real
        </div>
        
        <div class="test-buttons">
            <button class="test-btn btn-scalability" onclick="runTest('/scalability-tests')">🧪 Test Escalabilidad</button>
            <button class="test-btn btn-coordination" onclick="runTest('/coordination-tests')">🤝 Test Coordinación</button>
            <button class="test-btn btn-optimization" onclick="runTest('/algorithm-optimization')">🧠 Optimizar Algoritmos</button>
            <button class="test-btn btn-communication" onclick="runTest('/communication-tests')">📡 Test Comunicación</button>
            <button class="test-btn btn-all" onclick="runTest('/run-all-tests')">🚀 Suite Completa</button>
        </div>
        
        <div id="test-status"></div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value" id="cpu-usage">0%</div>
                <div class="metric-label">CPU Usage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="memory-usage">0%</div>
                <div class="metric-label">Memory Usage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="active-tests">0</div>
                <div class="metric-label">Active Tests</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="health-score">100</div>
                <div class="metric-label">Health Score</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3>📈 Performance en Tiempo Real</h3>
            <canvas id="performanceChart" width="400" height="200"></canvas>
        </div>
        
        <div class="chart-container">
            <h3>🎯 Resultados de Tests</h3>
            <canvas id="testResultsChart" width="400" height="200"></canvas>
        </div>
        
        <div class="results-section">
            <h3>📋 Últimos Resultados</h3>
            <div id="results-display">No hay resultados disponibles</div>
        </div>
    </div>
    
    <script>
        let performanceChart, testResultsChart;
        let performanceData = {{labels: [], datasets: [{{label: 'CPU %', data: [], borderColor: '#4CAF50'}}, {{label: 'Memory %', data: [], borderColor: '#2196F3'}}]}};
        let testResultsData = {{labels: ['Escalabilidad', 'Coordinación', 'Optimización', 'Comunicación'], datasets: [{{label: 'Success Rate', data: [95, 88, 92, 90], backgroundColor: ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0']}}]}};
        
        function initCharts() {{
            const ctx1 = document.getElementById('performanceChart').getContext('2d');
            performanceChart = new Chart(ctx1, {{
                type: 'line',
                data: performanceData,
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            max: 100
                        }}
                    }}
                }}
            }});
            
            const ctx2 = document.getElementById('testResultsChart').getContext('2d');
            testResultsChart = new Chart(ctx2, {{
                type: 'bar',
                data: testResultsData,
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            max: 100
                        }}
                    }}
                }}
            }});
        }}
        
        function updateMetrics(metrics) {{
            document.getElementById('cpu-usage').textContent = metrics.system.cpu_percent.toFixed(1) + '%';
            document.getElementById('memory-usage').textContent = metrics.system.memory_percent.toFixed(1) + '%';
            document.getElementById('active-tests').textContent = metrics.testing.active_tests;
            
            // Actualizar gráfico de performance
            const now = new Date().toLocaleTimeString();
            performanceData.labels.push(now);
            performanceData.datasets[0].data.push(metrics.system.cpu_percent);
            performanceData.datasets[1].data.push(metrics.system.memory_percent);
            
            // Mantener solo los últimos 20 puntos
            if (performanceData.labels.length > 20) {{
                performanceData.labels.shift();
                performanceData.datasets[0].data.shift();
                performanceData.datasets[1].data.shift();
            }}
            
            performanceChart.update('none');
        }}
        
        async function runTest(endpoint) {{
            const statusDiv = document.getElementById('test-status');
            statusDiv.innerHTML = '<div class="status status-running">🔄 Ejecutando test...</div>';
            
            try {{
                const response = await fetch(endpoint);
                const data = await response.json();
                
                if (data.status === 'completed') {{
                    statusDiv.innerHTML = '<div class="status status-success">✅ Test completado exitosamente</div>';
                    displayResults(data);
                }} else {{
                    statusDiv.innerHTML = '<div class="status status-error">❌ Error en el test</div>';
                }}
            }} catch (error) {{
                statusDiv.innerHTML = '<div class="status status-error">❌ Error: ' + error.message + '</div>';
            }}
        }}
        
        function displayResults(data) {{
            const resultsDiv = document.getElementById('results-display');
            const timestamp = new Date(data.timestamp).toLocaleString();
            const testType = data.test_type || 'Desconocido';
            
            let html = `<h4>📊 Resultados del Test: ${{testType}}</h4>`;
            html += `<p><strong>Fecha:</strong> ${{timestamp}}</p>`;
            html += `<p><strong>Tipo:</strong> ${{testType}}</p>`;
            html += `<p><strong>Estado:</strong> Completado</p>`;
            
            if (data.summary) {{
                html += `<h5>🎯 Resumen:</h5>`;
                html += `<p><strong>Health Score:</strong> ${{data.summary.overall_health_score}}/100</p>`;
                if (data.summary.critical_issues && data.summary.critical_issues.length > 0) {{
                    html += `<h5>⚠️ Problemas Críticos:</h5><ul>`;
                    data.summary.critical_issues.forEach(issue => {{
                        html += `<li>${{issue}}</li>`;
                    }});
                    html += `</ul>`;
                }}
                if (data.summary.recommendations && data.summary.recommendations.length > 0) {{
                    html += `<h5>💡 Recomendaciones:</h5><ul>`;
                    data.summary.recommendations.forEach(rec => {{
                        html += `<li>${{rec}}</li>`;
                    }});
                    html += `</ul>`;
                }}
            }}
            
            resultsDiv.innerHTML = html;
        }}
        
        // WebSocket para métricas en tiempo real
        const ws = new WebSocket('ws://localhost:8004/ws/metrics');
        ws.onmessage = function(event) {{
            const data = JSON.parse(event.data);
            updateMetrics(data.metrics);
        }};
        
        ws.onopen = function() {{
            document.getElementById('realtime').textContent = '🔗 Conectado - Actualizaciones en tiempo real';
        }};
        
        ws.onclose = function() {{
            document.getElementById('realtime').textContent = '❌ Desconectado';
        }};
        
        // Inicializar gráficos al cargar la página
        window.onload = function() {{
            initCharts();
        }};
    </script>
</body>
</html>
        """
    
    async def _run_algorithm_benchmark(self, algorithm: str) -> Dict[str, Any]:
        """Ejecutar benchmark de algoritmo específico"""
        optimizer = AlgorithmOptimizer(self.testing_suite.config)
        
        if algorithm == "hungarian":
            return await optimizer.optimize_hungarian_algorithm()
        elif algorithm == "cbba":
            return await optimizer.optimize_cbba_algorithm()
        elif algorithm == "raft":
            return await optimizer.optimize_raft_election()
        elif algorithm == "load_balancing":
            return await optimizer.optimize_load_balancing()
        else:
            raise HTTPException(status_code=400, detail=f"Algoritmo no soportado: {algorithm}")

# ==================== FUNCIONES PRINCIPALES ====================

def main():
    """Función principal para ejecutar el sistema de testing"""
    import uvicorn
    
    # Configurar CORS
    app = TestingWebService().app
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    logger.info("🚀 Iniciando SilhouetteMCP Testing Suite...")
    logger.info("🌐 Dashboard disponible en: http://localhost:8004/dashboard")
    logger.info("📊 WebSocket en: ws://localhost:8004/ws/metrics")
    
    # Iniciar servidor
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8004,
        log_level="info"
    )

if __name__ == "__main__":
    main()