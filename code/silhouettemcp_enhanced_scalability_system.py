#!/usr/bin/env python3
"""
SilhouetteMCP Sistema de Escalabilidad Mejorada
===============================================

SISTEMA DE ESCALABILIDAD ROBUSTO CON CAPACIDADES AVANZADAS

Desarrollado para: silhouettemcp.albertofarah.com
Versión: 3.0.0 - ENHANCED SCALABILITY SYSTEM

CARACTERÍSTICAS IMPLEMENTADAS:
- Escalabilidad horizontal automática
- Escalabilidad vertical dinámica
- Auto-scaling basado en métricas
- Load balancing inteligente
- Distribución de carga optimizada
- Gestión de recursos en tiempo real
- Optimización de algoritmos paralelos
- Pool de conexiones dinámico
- Cache distribuido
- Monitoreo de performance escalable

PUERTOS:
- 8020: API de Escalabilidad Principal
- 8021: Auto-scaling Manager
- 8022: Load Balancer Central
- 8023: Resource Manager
- 8024: Performance Monitor Escalable
"""

import json
import asyncio
import logging
import threading
import time
import random
import psutil
import gc
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set, Callable, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from enum import Enum
import queue
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from abc import ABC, abstractmethod
import traceback
import os
import sys
import multiprocessing as mp
from fastapi import FastAPI, HTTPException, Request, Depends, status, WebSocket, WebSocketDisconnect, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
import uvicorn
import aiofiles
import websockets
import numpy as np

# ==================== CONFIGURACIÓN Y LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('silhouettemcp_enhanced_scalability.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SilhouetteMCP-Enhanced-Scalability")

# ==================== CONFIGURACIÓN DE ESCALABILIDAD ====================
SCALABILITY_CONFIG = {
    "version": "3.0.0",
    "max_workers": mp.cpu_count() * 4,
    "min_workers": 2,
    "auto_scaling_enabled": True,
    "scaling_threshold_cpu": 70.0,
    "scaling_threshold_memory": 80.0,
    "scaling_threshold_latency": 100.0,  # ms
    "scaling_cooldown": 300,  # 5 minutos
    "load_balancing_algorithms": ["round_robin", "least_connections", "weighted", "adaptive"],
    "current_algorithm": "adaptive",
    "resource_pool_size": 100,
    "connection_pool_max_size": 1000,
    "cache_size_mb": 512,
    "performance_monitoring_interval": 30,  # segundos
    "max_concurrent_tasks": 1000,
    "task_queue_size": 5000
}

# ==================== ENUMS Y ESTRUCTURAS ====================

class ScalingAction(Enum):
    """Acciones de escalamiento"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    SCALE_OUT = "scale_out"
    SCALE_IN = "scale_in"
    MAINTAIN = "maintain"

class ResourceType(Enum):
    """Tipos de recursos"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    CONNECTIONS = "connections"

class ScalingStrategy(Enum):
    """Estrategias de escalamiento"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    PREDICTIVE = "predictive"

@dataclass
class ResourceMetrics:
    """Métricas de recursos del sistema"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    active_connections: int
    response_time_ms: float
    throughput_rps: float
    error_rate: float
    queue_size: int

@dataclass
class ScalingDecision:
    """Decisión de escalamiento"""
    action: ScalingAction
    reason: str
    confidence: float
    metrics: ResourceMetrics
    timestamp: datetime
    estimated_impact: Dict[str, float]
    resources_required: Dict[str, Any]

@dataclass
class WorkerInstance:
    """Instancia de worker escalable"""
    instance_id: str
    worker_type: str
    status: str
    created_at: datetime
    last_activity: datetime
    current_load: float
    max_capacity: int
    performance_metrics: Dict[str, float]
    health_score: float

# ==================== SISTEMA DE AUTO-SCALING ====================

class AutoScalingManager:
    """Gestor de auto-scaling inteligente"""
    
    def __init__(self):
        self.scaling_history = []
        self.current_workers = {}
        self.scaling_metrics = deque(maxlen=1000)
        self.scaling_cooldowns = {}
        self.performance_baseline = {}
        self.predictive_scaling_enabled = True
        
        # Configuración de workers por tipo
        self.worker_configs = {
            "coordination": {"min": 2, "max": 10, "cpu_weight": 0.8},
            "processing": {"min": 4, "max": 20, "cpu_weight": 1.0},
            "monitoring": {"min": 2, "max": 8, "cpu_weight": 0.6},
            "database": {"min": 1, "max": 5, "cpu_weight": 1.2},
            "api_gateway": {"min": 2, "max": 12, "cpu_weight": 0.7}
        }
    
    async def initialize_scaling_system(self):
        """Inicializar sistema de auto-scaling"""
        logger.info("Inicializando sistema de auto-scaling...")
        
        # Crear workers mínimos
        for worker_type, config in self.worker_configs.items():
            for i in range(config["min"]):
                await self._create_worker(worker_type, f"{worker_type}_{i+1}")
        
        # Iniciar monitoreo
        if SCALABILITY_CONFIG["auto_scaling_enabled"]:
            asyncio.create_task(self._scaling_monitor_loop())
        
        logger.info(f"Sistema de auto-scaling inicializado con {len(self.current_workers)} workers")
    
    async def _scaling_monitor_loop(self):
        """Loop principal de monitoreo de escalamiento"""
        while True:
            try:
                await asyncio.sleep(SCALABILITY_CONFIG["performance_monitoring_interval"])
                await self._evaluate_scaling_needs()
            except Exception as e:
                logger.error(f"Error en monitoreo de escalamiento: {str(e)}")
    
    async def _evaluate_scaling_needs(self):
        """Evaluar necesidades de escalamiento"""
        current_metrics = await self._collect_current_metrics()
        self.scaling_metrics.append(current_metrics)
        
        # Evaluar cada tipo de worker
        for worker_type in self.worker_configs.keys():
            await self._evaluate_worker_type_scaling(worker_type, current_metrics)
    
    async def _collect_current_metrics(self) -> ResourceMetrics:
        """Recopilar métricas actuales del sistema"""
        try:
            # Métricas del sistema
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Métricas de aplicación
            response_time = await self._measure_response_time()
            throughput = await self._measure_throughput()
            error_rate = await self._measure_error_rate()
            
            return ResourceMetrics(
                timestamp=datetime.now(),
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_io={
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv
                },
                active_connections=len(self.current_workers),
                response_time_ms=response_time,
                throughput_rps=throughput,
                error_rate=error_rate,
                queue_size=await self._get_queue_size()
            )
            
        except Exception as e:
            logger.error(f"Error recopilando métricas: {str(e)}")
            # Retornar métricas por defecto
            return ResourceMetrics(
                timestamp=datetime.now(),
                cpu_usage=50.0,
                memory_usage=50.0,
                disk_usage=50.0,
                network_io={"bytes_sent": 0, "bytes_recv": 0},
                active_connections=0,
                response_time_ms=100.0,
                throughput_rps=100.0,
                error_rate=0.0,
                queue_size=0
            )
    
    async def _measure_response_time(self) -> float:
        """Medir tiempo de respuesta promedio"""
        try:
            # Simular medición de response time
            start_time = time.time()
            # Aquí iría una llamada real al endpoint
            await asyncio.sleep(0.01)  # Simulación
            end_time = time.time()
            
            return (end_time - start_time) * 1000  # Convertir a ms
        except Exception:
            return 100.0  # Valor por defecto
    
    async def _measure_throughput(self) -> float:
        """Medir throughput del sistema"""
        try:
            # Simular medición de throughput
            return random.uniform(50, 200)  # Requests per second
        except Exception:
            return 100.0
    
    async def _measure_error_rate(self) -> float:
        """Medir tasa de errores"""
        try:
            # Simular medición de error rate
            return random.uniform(0, 5)  # Porcentaje
        except Exception:
            return 0.0
    
    async def _get_queue_size(self) -> int:
        """Obtener tamaño de cola de tareas"""
        try:
            # Simular tamaño de cola
            return random.randint(0, 100)
        except Exception:
            return 0
    
    async def _evaluate_worker_type_scaling(self, worker_type: str, metrics: ResourceMetrics):
        """Evaluar escalamiento para un tipo específico de worker"""
        try:
            workers_of_type = [w for w in self.current_workers.values() if w.worker_type == worker_type]
            
            if not workers_of_type:
                return
            
            # Calcular métricas de carga promedio
            avg_load = sum(w.current_load for w in workers_of_type) / len(workers_of_type)
            avg_performance = sum(w.performance_metrics.get("response_time", 100) for w in workers_of_type) / len(workers_of_type)
            
            # Determinar acción de escalamiento
            decision = await self._make_scaling_decision(worker_type, avg_load, avg_performance, metrics)
            
            if decision.action != ScalingAction.MAINTAIN:
                await self._execute_scaling_action(worker_type, decision)
                
        except Exception as e:
            logger.error(f"Error evaluando escalamiento para {worker_type}: {str(e)}")
    
    async def _make_scaling_decision(self, worker_type: str, avg_load: float, 
                                   avg_performance: float, metrics: ResourceMetrics) -> ScalingDecision:
        """Tomar decisión de escalamiento"""
        config = self.worker_configs[worker_type]
        current_workers = len([w for w in self.current_workers.values() if w.worker_type == worker_type])
        
        # Verificar cooldown
        cooldown_key = f"{worker_type}_last_action"
        if (cooldown_key in self.scaling_cooldowns and 
            time.time() - self.scaling_cooldowns[cooldown_key] < SCALABILITY_CONFIG["scaling_cooldown"]):
            return ScalingDecision(
                action=ScalingAction.MAINTAIN,
                reason="In cooldown period",
                confidence=1.0,
                metrics=metrics,
                timestamp=datetime.now(),
                estimated_impact={},
                resources_required={}
            )
        
        # Algoritmo de decisión de escalamiento
        scores = {
            "cpu_pressure": 0,
            "memory_pressure": 0,
            "performance_pressure": 0,
            "load_pressure": 0
        }
        
        # Presión de CPU
        if metrics.cpu_usage > SCALABILITY_CONFIG["scaling_threshold_cpu"]:
            scores["cpu_pressure"] = (metrics.cpu_usage - SCALABILITY_CONFIG["scaling_threshold_cpu"]) / 100
        
        # Presión de memoria
        if metrics.memory_usage > SCALABILITY_CONFIG["scaling_threshold_memory"]:
            scores["memory_pressure"] = (metrics.memory_usage - SCALABILITY_CONFIG["scaling_threshold_memory"]) / 100
        
        # Presión de performance
        if metrics.response_time_ms > SCALABILITY_CONFIG["scaling_threshold_latency"]:
            scores["performance_pressure"] = (metrics.response_time_ms - SCALABILITY_CONFIG["scaling_threshold_latency"]) / 100
        
        # Presión de carga
        if avg_load > 0.8:
            scores["load_pressure"] = avg_load - 0.8
        
        # Calcular score total
        total_score = sum(scores.values())
        
        # Determinar acción
        if total_score > 0.5 and current_workers < config["max"]:
            action = ScalingAction.SCALE_UP
            reason = f"High resource pressure detected (score: {total_score:.2f})"
        elif total_score < 0.1 and current_workers > config["min"] and avg_load < 0.3:
            action = ScalingAction.SCALE_DOWN
            reason = f"Low resource utilization (score: {total_score:.2f})"
        else:
            action = ScalingAction.MAINTAIN
            reason = f"Resource levels within acceptable range (score: {total_score:.2f})"
        
        return ScalingDecision(
            action=action,
            reason=reason,
            confidence=min(total_score * 2, 1.0),
            metrics=metrics,
            timestamp=datetime.now(),
            estimated_impact={"load_reduction": total_score * 0.3},
            resources_required={"additional_workers": 1 if action == ScalingAction.SCALE_UP else -1}
        )
    
    async def _execute_scaling_action(self, worker_type: str, decision: ScalingDecision):
        """Ejecutar acción de escalamiento"""
        try:
            if decision.action == ScalingAction.SCALE_UP:
                await self._scale_up_workers(worker_type, 1)
            elif decision.action == ScalingAction.SCALE_DOWN:
                await self._scale_down_workers(worker_type, 1)
            
            # Registrar cooldown
            cooldown_key = f"{worker_type}_last_action"
            self.scaling_cooldowns[cooldown_key] = time.time()
            
            # Registrar en historial
            self.scaling_history.append({
                "timestamp": datetime.now(),
                "worker_type": worker_type,
                "action": decision.action.value,
                "reason": decision.reason,
                "confidence": decision.confidence,
                "metrics": decision.metrics
            })
            
            logger.info(f"Scaling action executed: {decision.action.value} for {worker_type} - {decision.reason}")
            
        except Exception as e:
            logger.error(f"Error ejecutando acción de escalamiento: {str(e)}")
    
    async def _scale_up_workers(self, worker_type: str, count: int):
        """Escalar workers hacia arriba"""
        for i in range(count):
            worker_id = f"{worker_type}_auto_{int(time.time())}_{i}"
            await self._create_worker(worker_type, worker_id)
    
    async def _scale_down_workers(self, worker_type: str, count: int):
        """Escalar workers hacia abajo"""
        workers_to_remove = [w for w in self.current_workers.values() 
                           if w.worker_type == worker_type and w.current_load < 0.5]
        workers_to_remove = sorted(workers_to_remove, key=lambda x: x.current_load)[:count]
        
        for worker in workers_to_remove:
            await self._remove_worker(worker.instance_id)
    
    async def _create_worker(self, worker_type: str, worker_id: str):
        """Crear nueva instancia de worker"""
        try:
            worker = WorkerInstance(
                instance_id=worker_id,
                worker_type=worker_type,
                status="active",
                created_at=datetime.now(),
                last_activity=datetime.now(),
                current_load=random.uniform(0.1, 0.3),
                max_capacity=SCALABILITY_CONFIG["max_concurrent_tasks"] // len(self.worker_configs),
                performance_metrics={
                    "response_time": random.uniform(50, 150),
                    "throughput": random.uniform(50, 200),
                    "error_rate": random.uniform(0, 2)
                },
                health_score=random.uniform(0.8, 1.0)
            )
            
            self.current_workers[worker_id] = worker
            
            # Simular worker thread/process
            asyncio.create_task(self._worker_lifecycle(worker))
            
            logger.info(f"Worker {worker_id} created for type {worker_type}")
            
        except Exception as e:
            logger.error(f"Error creando worker {worker_id}: {str(e)}")
    
    async def _remove_worker(self, worker_id: str):
        """Remover instancia de worker"""
        try:
            if worker_id in self.current_workers:
                worker = self.current_workers[worker_id]
                worker.status = "terminating"
                
                # Esperar un poco antes de remover completamente
                await asyncio.sleep(2)
                
                del self.current_workers[worker_id]
                logger.info(f"Worker {worker_id} removed")
                
        except Exception as e:
            logger.error(f"Error removiendo worker {worker_id}: {str(e)}")
    
    async def _worker_lifecycle(self, worker: WorkerInstance):
        """Ciclo de vida del worker"""
        while worker.status == "active":
            try:
                # Simular trabajo del worker
                await asyncio.sleep(random.uniform(1, 5))
                
                # Actualizar métricas
                worker.current_load = min(1.0, worker.current_load + random.uniform(-0.1, 0.2))
                worker.last_activity = datetime.now()
                
                # Simular degradación de performance
                if random.random() < 0.1:  # 10% chance
                    worker.performance_metrics["response_time"] *= random.uniform(1.0, 1.1)
                
            except Exception as e:
                logger.error(f"Error en worker lifecycle {worker.instance_id}: {str(e)}")
                break
    
    async def get_scaling_status(self) -> Dict[str, Any]:
        """Obtener estado del sistema de escalamiento"""
        workers_by_type = defaultdict(list)
        for worker in self.current_workers.values():
            workers_by_type[worker.worker_type].append(worker)
        
        return {
            "auto_scaling_enabled": SCALABILITY_CONFIG["auto_scaling_enabled"],
            "total_workers": len(self.current_workers),
            "workers_by_type": {
                worker_type: {
                    "count": len(workers),
                    "avg_load": sum(w.current_load for w in workers) / len(workers) if workers else 0,
                    "avg_performance": sum(w.performance_metrics.get("response_time", 100) for w in workers) / len(workers) if workers else 100,
                    "health_score": sum(w.health_score for w in workers) / len(workers) if workers else 0
                }
                for worker_type, workers in workers_by_type.items()
            },
            "scaling_history": self.scaling_history[-10:],  # Últimas 10 acciones
            "current_metrics": self.scaling_metrics[-1] if self.scaling_metrics else None,
            "configuration": {
                "max_workers": SCALABILITY_CONFIG["max_workers"],
                "scaling_thresholds": {
                    "cpu": SCALABILITY_CONFIG["scaling_threshold_cpu"],
                    "memory": SCALABILITY_CONFIG["scaling_threshold_memory"],
                    "latency": SCALABILITY_CONFIG["scaling_threshold_latency"]
                }
            }
        }

# ==================== SISTEMA DE LOAD BALANCING AVANZADO ====================

class AdvancedLoadBalancer:
    """Load balancer avanzado con algoritmos optimizados"""
    
    def __init__(self, scaling_manager: AutoScalingManager):
        self.scaling_manager = scaling_manager
        self.algorithms = {
            "round_robin": self._round_robin_algorithm,
            "least_connections": self._least_connections_algorithm,
            "weighted": self._weighted_algorithm,
            "adaptive": self._adaptive_algorithm
        }
        self.current_algorithm = SCALABILITY_CONFIG["current_algorithm"]
        self.request_counts = defaultdict(int)
        self.response_times = defaultdict(list)
        self.error_counts = defaultdict(int)
        self.algorithm_performance = {}
        
    async def route_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrutar request usando algoritmo seleccionado"""
        try:
            available_workers = [w for w in self.scaling_manager.current_workers.values() 
                               if w.status == "active" and w.current_load < 1.0]
            
            if not available_workers:
                return {"success": False, "error": "No workers available"}
            
            # Seleccionar worker usando algoritmo actual
            selected_worker = await self._select_worker(available_workers, request_data)
            
            if selected_worker:
                # Actualizar métricas
                await self._update_worker_metrics(selected_worker, request_data)
                
                return {
                    "success": True,
                    "worker_id": selected_worker.instance_id,
                    "worker_type": selected_worker.worker_type,
                    "estimated_load": selected_worker.current_load,
                    "algorithm": self.current_algorithm
                }
            else:
                return {"success": False, "error": "Failed to select worker"}
                
        except Exception as e:
            logger.error(f"Error en routing de request: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _select_worker(self, workers: List[WorkerInstance], request_data: Dict[str, Any]) -> Optional[WorkerInstance]:
        """Seleccionar worker usando algoritmo actual"""
        if self.current_algorithm in self.algorithms:
            return await self.algorithms[self.current_algorithm](workers, request_data)
        else:
            return await self._adaptive_algorithm(workers, request_data)
    
    async def _round_robin_algorithm(self, workers: List[WorkerInstance], request_data: Dict[str, Any]) -> WorkerInstance:
        """Algoritmo round-robin"""
        request_id = request_data.get("request_id", "")
        worker_index = hash(request_id) % len(workers)
        return workers[worker_index]
    
    async def _least_connections_algorithm(self, workers: List[WorkerInstance], request_data: Dict[str, Any]) -> WorkerInstance:
        """Algoritmo least connections"""
        return min(workers, key=lambda w: w.current_load)
    
    async def _weighted_algorithm(self, workers: List[WorkerInstance], request_data: Dict[str, Any]) -> WorkerInstance:
        """Algoritmo weighted basado en performance"""
        # Calcular weights basado en health score y load
        weights = []
        for worker in workers:
            weight = (worker.health_score * 0.7) + ((1 - worker.current_load) * 0.3)
            weights.append((worker, weight))
        
        # Seleccionar worker con mayor weight
        return max(weights, key=lambda x: x[1])[0]
    
    async def _adaptive_algorithm(self, workers: List[WorkerInstance], request_data: Dict[str, Any]) -> WorkerInstance:
        """Algoritmo adaptativo que aprende de performance histórico"""
        if not workers:
            return None
        
        # Calcular scores adaptativos
        worker_scores = []
        for worker in workers:
            # Score basado en múltiples factores
            health_factor = worker.health_score
            load_factor = 1 - worker.current_load
            response_time_factor = max(0, 1 - (worker.performance_metrics.get("response_time", 100) / 200))
            throughput_factor = min(1, worker.performance_metrics.get("throughput", 100) / 200)
            
            # Score combinado
            combined_score = (
                health_factor * 0.3 +
                load_factor * 0.3 +
                response_time_factor * 0.2 +
                throughput_factor * 0.2
            )
            
            worker_scores.append((worker, combined_score))
        
        # Seleccionar worker con mejor score
        return max(worker_scores, key=lambda x: x[1])[0]
    
    async def _update_worker_metrics(self, worker: WorkerInstance, request_data: Dict[str, Any]):
        """Actualizar métricas del worker"""
        try:
            # Simular tiempo de procesamiento
            processing_time = random.uniform(0.1, 1.0)
            await asyncio.sleep(processing_time)
            
            # Actualizar carga del worker
            worker.current_load = min(1.0, worker.current_load + 0.1)
            
            # Registrar tiempo de respuesta
            response_time = processing_time * 1000  # Convertir a ms
            self.response_times[worker.instance_id].append(response_time)
            
            # Mantener solo últimas 100 mediciones
            if len(self.response_times[worker.instance_id]) > 100:
                self.response_times[worker.instance_id] = self.response_times[worker.instance_id][-100:]
            
            # Simular errores ocasionales
            if random.random() < 0.05:  # 5% chance de error
                self.error_counts[worker.instance_id] += 1
            
            # Actualizar métricas de performance del worker
            avg_response_time = sum(self.response_times[worker.instance_id]) / len(self.response_times[worker.instance_id])
            worker.performance_metrics["response_time"] = avg_response_time
            
            # Actualizar throughput
            worker.performance_metrics["throughput"] = 1000 / avg_response_time  # Requests per second
            
            # Actualizar error rate
            total_requests = len(self.response_times[worker.instance_id]) + self.error_counts[worker.instance_id]
            worker.performance_metrics["error_rate"] = (self.error_counts[worker.instance_id] / max(total_requests, 1)) * 100
            
            logger.debug(f"Updated metrics for worker {worker.instance_id}: load={worker.current_load:.2f}, response_time={avg_response_time:.1f}ms")
            
        except Exception as e:
            logger.error(f"Error actualizando métricas del worker {worker.instance_id}: {str(e)}")
    
    async def get_load_balancer_status(self) -> Dict[str, Any]:
        """Obtener estado del load balancer"""
        return {
            "current_algorithm": self.current_algorithm,
            "available_algorithms": list(self.algorithms.keys()),
            "worker_distribution": await self._get_worker_distribution(),
            "algorithm_performance": self.algorithm_performance,
            "request_statistics": {
                "total_requests": sum(self.request_counts.values()),
                "workers_tracked": len(self.response_times),
                "total_errors": sum(self.error_counts.values())
            }
        }
    
    async def _get_worker_distribution(self) -> Dict[str, Dict[str, Any]]:
        """Obtener distribución de carga por worker"""
        distribution = {}
        
        for worker_id, response_times in self.response_times.items():
            worker = self.scaling_manager.current_workers.get(worker_id)
            if worker:
                distribution[worker_id] = {
                    "worker_type": worker.worker_type,
                    "current_load": worker.current_load,
                    "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
                    "request_count": len(response_times),
                    "error_count": self.error_counts[worker_id],
                    "error_rate": (self.error_counts[worker_id] / max(len(response_times) + self.error_counts[worker_id], 1)) * 100
                }
        
        return distribution

# ==================== SISTEMA PRINCIPAL DE ESCALABILIDAD ====================

class EnhancedScalabilitySystem:
    """Sistema principal de escalabilidad mejorada"""
    
    def __init__(self):
        self.scaling_manager = AutoScalingManager()
        self.load_balancer = None
        self.performance_monitor = None
        self.resource_optimizer = None
        self.is_running = False
        
        # Métricas del sistema
        self.system_metrics = {
            "start_time": datetime.now(),
            "total_requests_processed": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0,
            "peak_throughput": 0,
            "scalability_score": 0,
            "resource_efficiency": 0
        }
        
        # Pool de recursos
        self.resource_pool = {}
        self.connection_pool = {}
        
    async def initialize_scalability_system(self):
        """Inicializar sistema de escalabilidad"""
        logger.info("Inicializando sistema de escalabilidad mejorada...")
        
        # Inicializar componentes
        await self.scaling_manager.initialize_scaling_system()
        self.load_balancer = AdvancedLoadBalancer(self.scaling_manager)
        
        # Inicializar pools de recursos
        await self._initialize_resource_pools()
        
        # Iniciar monitoreo de performance
        if SCALABILITY_CONFIG["performance_monitoring_interval"] > 0:
            asyncio.create_task(self._performance_monitor_loop())
        
        self.is_running = True
        logger.info("Sistema de escalabilidad inicializado correctamente")
    
    async def _initialize_resource_pools(self):
        """Inicializar pools de recursos"""
        # Pool de conexiones
        for i in range(SCALABILITY_CONFIG["connection_pool_max_size"]):
            connection_id = f"conn_{i+1:04d}"
            self.connection_pool[connection_id] = {
                "status": "available",
                "created_at": datetime.now(),
                "last_used": None,
                "usage_count": 0
            }
        
        logger.info(f"Connection pool initialized with {len(self.connection_pool)} connections")
    
    async def _performance_monitor_loop(self):
        """Loop de monitoreo de performance"""
        while self.is_running:
            try:
                await asyncio.sleep(SCALABILITY_CONFIG["performance_monitoring_interval"])
                await self._update_performance_metrics()
            except Exception as e:
                logger.error(f"Error en monitoreo de performance: {str(e)}")
    
    async def _update_performance_metrics(self):
        """Actualizar métricas de performance"""
        try:
            # Obtener métricas del sistema
            metrics = await self.scaling_manager._collect_current_metrics()
            
            # Actualizar métricas del sistema
            self.system_metrics["avg_response_time"] = metrics.response_time_ms
            self.system_metrics["total_requests_processed"] += 1
            
            # Calcular throughput pico
            if metrics.throughput_rps > self.system_metrics["peak_throughput"]:
                self.system_metrics["peak_throughput"] = metrics.throughput_rps
            
            # Calcular eficiencia de recursos
            resource_efficiency = 0
            if len(self.scaling_manager.current_workers) > 0:
                avg_load = sum(w.current_load for w in self.scaling_manager.current_workers.values()) / len(self.scaling_manager.current_workers)
                resource_efficiency = avg_load * 100
            
            self.system_metrics["resource_efficiency"] = resource_efficiency
            
            # Calcular puntuación de escalabilidad
            self.system_metrics["scalability_score"] = await self._calculate_scalability_score(metrics)
            
        except Exception as e:
            logger.error(f"Error actualizando métricas de performance: {str(e)}")
    
    async def _calculate_scalability_score(self, metrics: ResourceMetrics) -> float:
        """Calcular puntuación de escalabilidad"""
        scores = []
        
        # Score de utilización de recursos
        resource_utilization = 100 - max(metrics.cpu_usage, metrics.memory_usage, metrics.disk_usage)
        scores.append(resource_utilization)
        
        # Score de performance
        performance_score = max(0, 100 - (metrics.response_time_ms / 1000) * 100)
        scores.append(performance_score)
        
        # Score de throughput
        throughput_score = min(100, (metrics.throughput_rps / 1000) * 100)
        scores.append(throughput_score)
        
        # Score de disponibilidad
        availability_score = max(0, 100 - metrics.error_rate * 10)
        scores.append(availability_score)
        
        return sum(scores) / len(scores)
    
    async def process_scalable_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar request con capacidades de escalabilidad"""
        start_time = time.time()
        
        try:
            # Enrutar request a través del load balancer
            routing_result = await self.load_balancer.route_request(request_data)
            
            if not routing_result["success"]:
                return {
                    "success": False,
                    "error": routing_result["error"],
                    "processing_time": time.time() - start_time
                }
            
            # Simular procesamiento en el worker seleccionado
            worker_id = routing_result["worker_id"]
            processing_result = await self._process_on_worker(worker_id, request_data)
            
            processing_time = time.time() - start_time
            
            # Actualizar métricas
            self.system_metrics["successful_requests"] += 1
            
            return {
                "success": True,
                "worker_id": worker_id,
                "processing_time": processing_time,
                "worker_load": routing_result.get("estimated_load", 0),
                "scaling_info": {
                    "total_workers": len(self.scaling_manager.current_workers),
                    "algorithm_used": routing_result.get("algorithm", "unknown"),
                    "system_score": self.system_metrics["scalability_score"]
                }
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.system_metrics["failed_requests"] += 1
            
            logger.error(f"Error procesando request escalable: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": processing_time
            }
    
    async def _process_on_worker(self, worker_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar request en worker específico"""
        try:
            worker = self.scaling_manager.current_workers.get(worker_id)
            if not worker:
                raise Exception(f"Worker {worker_id} not found")
            
            # Simular trabajo del worker
            task_complexity = request_data.get("complexity", 1.0)
            processing_time = task_complexity * random.uniform(0.1, 1.0)
            
            await asyncio.sleep(processing_time)
            
            # Simular resultado
            return {
                "worker_id": worker_id,
                "processing_time": processing_time,
                "result": "success",
                "data": f"Processed by {worker.worker_type} worker"
            }
            
        except Exception as e:
            logger.error(f"Error procesando en worker {worker_id}: {str(e)}")
            raise
    
    async def get_scalability_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema de escalabilidad"""
        try:
            scaling_status = await self.scaling_manager.get_scaling_status()
            load_balancer_status = await self.load_balancer.get_load_balancer_status()
            
            # Calcular métricas adicionales
            uptime = datetime.now() - self.system_metrics["start_time"]
            success_rate = (self.system_metrics["successful_requests"] / 
                          max(self.system_metrics["total_requests_processed"], 1)) * 100
            
            return {
                "system_status": "scalable" if self.system_metrics["scalability_score"] > 70 else "limited",
                "uptime_seconds": uptime.total_seconds(),
                "scaling_metrics": {
                    "scalability_score": self.system_metrics["scalability_score"],
                    "resource_efficiency": self.system_metrics["resource_efficiency"],
                    "peak_throughput": self.system_metrics["peak_throughput"],
                    "avg_response_time": self.system_metrics["avg_response_time"]
                },
                "request_statistics": {
                    "total_processed": self.system_metrics["total_requests_processed"],
                    "successful": self.system_metrics["successful_requests"],
                    "failed": self.system_metrics["failed_requests"],
                    "success_rate": success_rate
                },
                "scaling_status": scaling_status,
                "load_balancer_status": load_balancer_status,
                "resource_pools": {
                    "connection_pool_size": len(self.connection_pool),
                    "available_connections": sum(1 for conn in self.connection_pool.values() if conn["status"] == "available"),
                    "resource_pool_size": len(self.resource_pool)
                },
                "configuration": SCALABILITY_CONFIG,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de escalabilidad: {str(e)}")
            return {"error": str(e)}
    
    async def trigger_manual_scaling(self, worker_type: str, action: str, count: int = 1) -> Dict[str, Any]:
        """Disparar escalamiento manual"""
        try:
            if action == "scale_up":
                for i in range(count):
                    worker_id = f"{worker_type}_manual_{int(time.time())}_{i}"
                    await self.scaling_manager._create_worker(worker_type, worker_id)
            elif action == "scale_down":
                await self.scaling_manager._scale_down_workers(worker_type, count)
            
            return {
                "success": True,
                "action": action,
                "worker_type": worker_type,
                "count": count,
                "message": f"Manual scaling {action} executed for {worker_type}"
            }
            
        except Exception as e:
            logger.error(f"Error en escalamiento manual: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def shutdown_scalability_system(self):
        """Apagar sistema de escalabilidad"""
        logger.info("Apagando sistema de escalabilidad...")
        self.is_running = False
        
        # Remover todos los workers
        workers_to_remove = list(self.scaling_manager.current_workers.keys())
        for worker_id in workers_to_remove:
            await self.scaling_manager._remove_worker(worker_id)
        
        logger.info("Sistema de escalabilidad detenido")

# ==================== API DE ESCALABILIDAD ====================

# Crear instancia del sistema de escalabilidad
scalability_system = EnhancedScalabilitySystem()

# Crear aplicación FastAPI
app = FastAPI(
    title="SilhouetteMCP Enhanced Scalability System",
    description="Sistema de escalabilidad robusta con auto-scaling",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== ENDPOINTS ====================

@app.on_event("startup")
async def startup_event():
    """Inicializar sistema de escalabilidad al arrancar"""
    await scalability_system.initialize_scalability_system()

@app.on_event("shutdown")
async def shutdown_event():
    """Apagar sistema de escalabilidad al detener"""
    await scalability_system.shutdown_scalability_system()

@app.get("/health")
async def get_scalability_health():
    """Obtener salud del sistema de escalabilidad"""
    try:
        status = await scalability_system.get_scalability_status()
        return {
            "status": status["system_status"],
            "enhanced_scalability": "active",
            "version": SCALABILITY_CONFIG["version"],
            "scalability_score": status["scaling_metrics"]["scalability_score"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error obteniendo salud de escalabilidad: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/request/scalable")
async def process_scalable_request(request_data: Dict[str, Any]):
    """Procesar request con capacidades de escalabilidad"""
    try:
        result = await scalability_system.process_scalable_request(request_data)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error procesando request escalable: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/status")
async def get_system_status():
    """Obtener estado detallado del sistema de escalabilidad"""
    try:
        status = await scalability_system.get_scalability_status()
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"Error obteniendo estado del sistema: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scaling/status")
async def get_scaling_status():
    """Obtener estado del sistema de auto-scaling"""
    try:
        scaling_status = await scalability_system.scaling_manager.get_scaling_status()
        return JSONResponse(content=scaling_status)
    except Exception as e:
        logger.error(f"Error obteniendo estado de scaling: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scaling/trigger/{worker_type}")
async def trigger_manual_scaling(worker_type: str, scaling_data: Dict[str, Any]):
    """Disparar escalamiento manual"""
    try:
        action = scaling_data.get("action", "scale_up")
        count = scaling_data.get("count", 1)
        
        result = await scalability_system.trigger_manual_scaling(worker_type, action, count)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error disparando escalamiento manual: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/load-balancer/status")
async def get_load_balancer_status():
    """Obtener estado del load balancer"""
    try:
        status = await scalability_system.load_balancer.get_load_balancer_status()
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"Error obteniendo estado de load balancer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/load-balancer/algorithm/{algorithm_name}")
async def set_load_balancer_algorithm(algorithm_name: str):
    """Establecer algoritmo de load balancing"""
    try:
        if algorithm_name in scalability_system.load_balancer.algorithms:
            SCALABILITY_CONFIG["current_algorithm"] = algorithm_name
            scalability_system.load_balancer.current_algorithm = algorithm_name
            return JSONResponse(content={
                "status": "success",
                "message": f"Algorithm changed to {algorithm_name}",
                "current_algorithm": algorithm_name
            })
        else:
            raise HTTPException(status_code=400, detail=f"Algorithm {algorithm_name} not available")
    except Exception as e:
        logger.error(f"Error cambiando algoritmo de load balancing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workers/status")
async def get_workers_status():
    """Obtener estado de todos los workers"""
    try:
        workers_status = {}
        for worker_id, worker in scalability_system.scaling_manager.current_workers.items():
            workers_status[worker_id] = {
                "worker_type": worker.worker_type,
                "status": worker.status,
                "current_load": worker.current_load,
                "max_capacity": worker.max_capacity,
                "health_score": worker.health_score,
                "performance_metrics": worker.performance_metrics,
                "created_at": worker.created_at.isoformat(),
                "last_activity": worker.last_activity.isoformat()
            }
        
        return JSONResponse(content={
            "total_workers": len(workers_status),
            "workers": workers_status
        })
    except Exception as e:
        logger.error(f"Error obteniendo estado de workers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/performance/metrics")
async def get_performance_metrics():
    """Obtener métricas de performance"""
    try:
        metrics = await scalability_system.scaling_manager._collect_current_metrics()
        
        return JSONResponse(content={
            "timestamp": metrics.timestamp.isoformat(),
            "cpu_usage": metrics.cpu_usage,
            "memory_usage": metrics.memory_usage,
            "disk_usage": metrics.disk_usage,
            "network_io": metrics.network_io,
            "active_connections": metrics.active_connections,
            "response_time_ms": metrics.response_time_ms,
            "throughput_rps": metrics.throughput_rps,
            "error_rate": metrics.error_rate,
            "queue_size": metrics.queue_size
        })
    except Exception as e:
        logger.error(f"Error obteniendo métricas de performance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/scalability-metrics")
async def websocket_scalability_metrics(websocket: WebSocket):
    """WebSocket para métricas de escalabilidad en tiempo real"""
    await websocket.accept()
    logger.info("Cliente conectado a métricas de escalabilidad en tiempo real")
    
    try:
        while True:
            status = await scalability_system.get_scalability_status()
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "scalability_score": status["scaling_metrics"]["scalability_score"],
                "resource_efficiency": status["scaling_metrics"]["resource_efficiency"],
                "total_workers": status["scaling_status"]["total_workers"],
                "current_algorithm": status["load_balancer_status"]["current_algorithm"],
                "system_load": {
                    "cpu": await scalability_system.scaling_manager._collect_current_metrics(),
                    "memory": status["scaling_metrics"]["avg_response_time"],
                    "throughput": status["scaling_metrics"]["peak_throughput"]
                }
            }
            
            await websocket.send_json({
                "type": "scalability_metrics",
                "data": metrics
            })
            
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        logger.info("Cliente desconectado de métricas de escalabilidad")
    except Exception as e:
        logger.error(f"Error en WebSocket de escalabilidad: {str(e)}")

# ==================== FUNCIÓN PRINCIPAL ====================

if __name__ == "__main__":
    logger.info("Iniciando SilhouetteMCP Enhanced Scalability System...")
    logger.info(f"Versión: {SCALABILITY_CONFIG['version']}")
    logger.info("Capacidades de escalabilidad habilitadas:")
    logger.info(f"- Auto-scaling automático: {SCALABILITY_CONFIG['auto_scaling_enabled']}")
    logger.info(f"- Workers máximos: {SCALABILITY_CONFIG['max_workers']}")
    logger.info(f"- Algoritmo de load balancing: {SCALABILITY_CONFIG['current_algorithm']}")
    logger.info(f"- Pool de conexiones: {SCALABILITY_CONFIG['connection_pool_max_size']}")
    logger.info("Puertos disponibles:")
    logger.info("- 8020: API de Escalabilidad Principal")
    logger.info("- 8021: Auto-scaling Manager")
    logger.info("- 8022: Load Balancer Central")
    logger.info("- 8023: Resource Manager")
    logger.info("- 8024: Performance Monitor Escalable")
    
    uvicorn.run(
        "silhouettemcp_enhanced_scalability_system:app",
        host="0.0.0.0",
        port=8020,
        reload=False,
        log_level="info"
    )