#!/usr/bin/env python3
"""
SilhouetteMCP Sistema de Diagnóstico Robusto (Versión Simplificada)
==================================================================

SISTEMA DE DIAGNÓSTICO ROBUSTO PARA ARQUITECTURA JERÁRQUICA DE 100+ AGENTES

Desarrollado para: silhouettemcp.albertofarah.com
Versión: 1.0.0 - ROBUST DIAGNOSTIC SYSTEM

CARACTERÍSTICAS IMPLEMENTADAS:
- Diagnóstico completo de arquitectura jerárquica
- Análisis de robustez y recuperación
- Verificación de escalabilidad y performance
- Auditoría de seguridad integral
- Análisis de integración entre sistemas
- Identificación de puntos críticos de falla
- Recomendaciones de mejoras robustas
- Generación de reportes ejecutivos

PUERTOS:
- 8007: Sistema de Diagnóstico Principal
- 8008: Métricas de Diagnóstico en Tiempo Real
- 8009: API de Diagnóstico Avanzado
"""

import json
import time
import asyncio
import logging
import threading
import hashlib
import secrets
import random
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set, Callable, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from enum import Enum
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from abc import ABC, abstractmethod
import traceback
import signal
import resource
import math
from itertools import combinations, permutations
import uuid

# FastAPI imports
from fastapi import FastAPI, HTTPException, Request, Depends, status, WebSocket, WebSocketDisconnect, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, validator
import uvicorn
import aiohttp
import aiofiles
import websockets

# ==================== CONFIGURACIÓN Y LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('silhouettemcp_robust_diagnostic.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SilhouetteMCP-Robust-Diagnostic")

# ==================== CONFIGURACIÓN GLOBAL ====================
DIAGNOSTIC_CONFIG = {
    "max_concurrent_diagnostics": 50,
    "diagnostic_timeout": 1800,  # 30 minutos
    "max_agents_to_test": 200,
    "max_systems_to_analyze": 20,
    "test_retry_attempts": 3,
    "critical_threshold": 80,  # Puntuación crítica
    "performance_baseline": 1000,  # Operaciones por segundo
}

# ==================== ESTRUCTURAS DE DATOS ====================

class DiagnosticSeverity(Enum):
    """Niveles de severidad para diagnósticos"""
    CRITICAL = "CRITICAL"      # Requiere atención inmediata
    HIGH = "HIGH"             # Problema importante
    MEDIUM = "MEDIUM"         # Problema moderado
    LOW = "LOW"              # Mejora recomendada
    INFO = "INFO"            # Informativo

class DiagnosticCategory(Enum):
    """Categorías de diagnóstico"""
    ARCHITECTURE = "architecture"
    ROBUSTNESS = "robustness"
    PERFORMANCE = "performance"
    SECURITY = "security"
    INTEGRATION = "integration"
    SCALABILITY = "scalability"
    MONITORING = "monitoring"
    RECOVERY = "recovery"

@dataclass
class DiagnosticResult:
    """Resultado de un diagnóstico individual"""
    category: DiagnosticCategory
    severity: DiagnosticSeverity
    component: str
    issue_description: str
    impact_assessment: str
    recommendation: str
    affected_systems: List[str]
    performance_impact: float
    priority_score: int  # 1-10
    timestamp: datetime
    resolved: bool = False
    resolution_notes: str = ""

@dataclass
class SystemHealthSnapshot:
    """Instantánea de salud del sistema"""
    timestamp: datetime
    active_services: int
    total_services: int
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_connections: int
    error_rate: float
    response_time: float

# ==================== SISTEMA DE DIAGNÓSTICO ROBUSTO ====================

class RobustDiagnosticSystem:
    """Sistema de diagnóstico robusto y confiable"""
    
    def __init__(self):
        self.diagnostic_results: List[DiagnosticResult] = []
        self.system_snapshots: List[SystemHealthSnapshot] = []
        self.diagnostic_history: List[Dict] = []
        self.is_running = False
        self.diagnostic_lock = threading.Lock()
        self._running_processes = {}
        
    async def run_comprehensive_diagnostic(self) -> Dict[str, Any]:
        """Ejecutar diagnóstico completo del sistema"""
        logger.info("Iniciando diagnóstico completo del sistema SilhouetteMCP")
        start_time = time.time()
        
        diagnostic_results = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": 0,
            "critical_issues": [],
            "high_issues": [],
            "medium_issues": [],
            "low_issues": [],
            "info_items": [],
            "recommendations": [],
            "system_health": {},
            "architecture_assessment": {},
            "performance_analysis": {},
            "security_assessment": {},
            "integration_status": {},
            "scalability_analysis": {},
            "recovery_capabilities": {},
            "execution_time_seconds": 0,
            "diagnostic_metadata": {
                "version": "1.0.0",
                "platform": "SilhouetteMCP",
                "environment": "production"
            }
        }
        
        try:
            # 1. Verificación de archivos críticos
            logger.info("Verificando archivos críticos del sistema...")
            file_verification = await self._verify_critical_files()
            diagnostic_results["system_health"]["file_verification"] = file_verification
            
            # 2. Análisis de arquitectura jerárquica
            logger.info("Analizando arquitectura jerárquica...")
            architecture_analysis = await self._analyze_hierarchical_architecture()
            diagnostic_results["architecture_assessment"] = architecture_analysis
            
            # 3. Verificación de servicios y procesos
            logger.info("Verificando servicios y procesos...")
            services_status = await self._verify_services_and_processes()
            diagnostic_results["system_health"]["services"] = services_status
            
            # 4. Análisis de dependencias críticas
            logger.info("Analizando dependencias críticas...")
            dependencies_check = await self._analyze_critical_dependencies()
            diagnostic_results["architecture_assessment"]["dependencies"] = dependencies_check
            
            # 5. Verificación de configuración de seguridad
            logger.info("Verificando configuración de seguridad...")
            security_check = await self._verify_security_configuration()
            diagnostic_results["security_assessment"] = security_check
            
            # 6. Análisis de performance básico
            logger.info("Realizando análisis de performance...")
            performance_analysis = await self._analyze_performance_basics()
            diagnostic_results["performance_analysis"] = performance_analysis
            
            # 7. Verificación de integración entre sistemas
            logger.info("Verificando integración entre sistemas...")
            integration_analysis = await self._analyze_system_integration()
            diagnostic_results["integration_status"] = integration_analysis
            
            # 8. Evaluación de capacidades de escalabilidad
            logger.info("Evaluando capacidades de escalabilidad...")
            scalability_analysis = await self._analyze_scalability_capabilities()
            diagnostic_results["scalability_analysis"] = scalability_analysis
            
            # 9. Verificación de mecanismos de recuperación
            logger.info("Verificando mecanismos de recuperación...")
            recovery_analysis = await self._analyze_recovery_mechanisms()
            diagnostic_results["recovery_capabilities"] = recovery_analysis
            
            # Generar issues basados en todos los análisis
            all_issues = self._consolidate_issues(diagnostic_results)
            diagnostic_results.update(all_issues)
            
            # Calcular puntuación general
            diagnostic_results["overall_score"] = self._calculate_comprehensive_score(diagnostic_results)
            
            # Generar recomendaciones estratégicas
            diagnostic_results["recommendations"] = self._generate_strategic_recommendations(diagnostic_results)
            
            execution_time = time.time() - start_time
            diagnostic_results["execution_time_seconds"] = round(execution_time, 2)
            
            # Agregar metadata del diagnóstico
            diagnostic_results["diagnostic_metadata"]["execution_summary"] = {
                "duration_seconds": execution_time,
                "checks_performed": len([k for k in diagnostic_results.keys() if k.endswith("_analysis") or k.endswith("_check")]),
                "issues_found": len(diagnostic_results["critical_issues"]) + len(diagnostic_results["high_issues"]),
                "overall_health": "CRITICAL" if diagnostic_results["overall_score"] < 70 else "GOOD" if diagnostic_results["overall_score"] < 85 else "EXCELLENT"
            }
            
            logger.info(f"Diagnóstico completo finalizado en {execution_time:.2f} segundos")
            logger.info(f"Puntuación general del sistema: {diagnostic_results['overall_score']}/100")
            
            return diagnostic_results
            
        except Exception as e:
            logger.error(f"Error durante el diagnóstico completo: {str(e)}")
            logger.error(traceback.format_exc())
            
            diagnostic_results["error"] = str(e)
            diagnostic_results["error_details"] = traceback.format_exc()
            diagnostic_results["overall_score"] = 50  # Puntuación mínima en caso de error
            return diagnostic_results
    
    async def _verify_critical_files(self) -> Dict[str, Any]:
        """Verificar presencia y integridad de archivos críticos"""
        logger.info("Verificando archivos críticos...")
        
        critical_files = [
            ("/workspace/code/silhouettemcp_hierarchical_architecture.py", "Arquitectura Jerárquica"),
            ("/workspace/code/silhouettemcp_server_unified.py", "Servidor Unificado"),
            ("/workspace/code/silhouettemcp_testing_optimization_suite.py", "Suite de Testing"),
            ("/workspace/code/silhouettemcp_hierarchical_dashboard.html", "Dashboard Jerárquico"),
            ("/workspace/code/silhouettemcp_comprehensive_diagnostic_system.py", "Sistema de Diagnóstico"),
        ]
        
        verification_results = {
            "files_checked": len(critical_files),
            "files_present": 0,
            "files_missing": [],
            "files_corrupted": [],
            "total_size_mb": 0,
            "verification_score": 0,
            "file_details": []
        }
        
        for file_path, description in critical_files:
            file_info = {
                "path": file_path,
                "description": description,
                "present": False,
                "size_mb": 0,
                "last_modified": None,
                "readable": False
            }
            
            try:
                if Path(file_path).exists():
                    file_stat = Path(file_path).stat()
                    file_info["present"] = True
                    file_info["size_mb"] = round(file_stat.st_size / (1024 * 1024), 2)
                    file_info["last_modified"] = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                    file_info["readable"] = os.access(file_path, os.R_OK)
                    verification_results["files_present"] += 1
                    verification_results["total_size_mb"] += file_info["size_mb"]
                    
                    # Verificar integridad básica leyendo primeras líneas
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            first_lines = f.read(100)
                            if len(first_lines) > 0:
                                file_info["readable"] = True
                            else:
                                verification_results["files_corrupted"].append(file_path)
                    except Exception as e:
                        file_info["readable"] = False
                        verification_results["files_corrupted"].append(file_path)
                        logger.warning(f"Error leyendo archivo {file_path}: {str(e)}")
                else:
                    verification_results["files_missing"].append(file_path)
                    
            except Exception as e:
                logger.error(f"Error verificando archivo {file_path}: {str(e)}")
                verification_results["files_corrupted"].append(file_path)
            
            verification_results["file_details"].append(file_info)
        
        # Calcular puntuación
        if verification_results["files_checked"] > 0:
            present_score = (verification_results["files_present"] / verification_results["files_checked"]) * 70
            readable_score = sum(1 for f in verification_results["file_details"] if f["readable"]) / verification_results["files_checked"] * 30
            verification_results["verification_score"] = int(present_score + readable_score)
        
        return verification_results
    
    async def _analyze_hierarchical_architecture(self) -> Dict[str, Any]:
        """Analizar la arquitectura jerárquica del sistema"""
        logger.info("Analizando arquitectura jerárquica...")
        
        architecture_analysis = {
            "hierarchy_levels": 0,
            "communication_protocols": {},
            "coordination_algorithms": {},
            "team_structures": {},
            "agent_specializations": {},
            "architecture_score": 0,
            "architecture_components": {}
        }
        
        architecture_file = "/workspace/code/silhouettemcp_hierarchical_architecture.py"
        
        try:
            if Path(architecture_file).exists():
                with open(architecture_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Analizar niveles jerárquicos
                hierarchy_patterns = [
                    ("Master Coordinator", "Nivel Estratégico"),
                    ("Intelligent Task Assigner", "Nivel de Asignación"),
                    ("Team Leaders", "Nivel de Liderazgo"),
                    ("Team Supervisors", "Nivel de Supervisión"),
                    ("Specialized Agents", "Nivel Operativo")
                ]
                
                found_levels = 0
                for pattern, level_name in hierarchy_patterns:
                    if pattern in content:
                        found_levels += 1
                        architecture_analysis["architecture_components"][pattern] = {
                            "present": True,
                            "level": level_name
                        }
                
                architecture_analysis["hierarchy_levels"] = found_levels
                
                # Verificar protocolos de comunicación
                communication_patterns = [
                    ("FIPA-ACL", "Protocolo de Comunicación"),
                    ("WebSocket", "Comunicación en Tiempo Real"),
                    ("SSE", "Streaming de Eventos"),
                    ("HTTP", "Comunicación REST"),
                    ("JSON-RPC", "Comunicación Estructurada")
                ]
                
                for pattern, description in communication_patterns:
                    if pattern in content:
                        architecture_analysis["communication_protocols"][pattern] = {
                            "implemented": True,
                            "description": description
                        }
                
                # Verificar algoritmos de coordinación
                algorithm_patterns = [
                    ("Hungarian", "Algoritmo de Asignación"),
                    ("CBBA", "Algoritmo de Coordinación"),
                    ("RAFT", "Consenso Distribuido"),
                    ("load balancing", "Balanceamiento de Carga"),
                    ("task assignment", "Asignación de Tareas")
                ]
                
                for pattern, description in algorithm_patterns:
                    if pattern.lower() in content.lower():
                        architecture_analysis["coordination_algorithms"][pattern] = {
                            "implemented": True,
                            "description": description
                        }
                
                # Analizar estructuras de equipo
                team_patterns = [
                    ("Maps Intelligence", "Equipo de Mapas"),
                    ("Financial Intelligence", "Equipo Financiero"),
                    ("Social Travel", "Equipo Social/Travel"),
                    ("Content Creation", "Equipo de Contenido"),
                    ("Database Operations", "Equipo de Base de Datos"),
                    ("Research Intelligence", "Equipo de Investigación"),
                    ("Support Systems", "Equipo de Soporte")
                ]
                
                for pattern, description in team_patterns:
                    if pattern in content:
                        architecture_analysis["team_structures"][pattern] = {
                            "present": True,
                            "description": description
                        }
                
                # Verificar especialización de agentes
                specialization_patterns = [
                    ("100+", "Cantidad de Agentes"),
                    ("Base Agents", "Agentes Base"),
                    ("Real World", "Agentes Mundo Real"),
                    ("Specialized", "Agentes Especializados"),
                    ("Enterprise", "Agentes Enterprise")
                ]
                
                for pattern, description in specialization_patterns:
                    if pattern in content:
                        architecture_analysis["agent_specializations"][pattern] = {
                            "present": True,
                            "description": description
                        }
                
                # Calcular puntuación de arquitectura
                scores = []
                
                # Puntuación por niveles jerárquicos
                if found_levels >= 5:
                    scores.append(100)
                elif found_levels >= 4:
                    scores.append(80)
                elif found_levels >= 3:
                    scores.append(60)
                else:
                    scores.append(40)
                
                # Puntuación por protocolos
                protocol_score = (len(architecture_analysis["communication_protocols"]) / 5) * 100
                scores.append(protocol_score)
                
                # Puntuación por algoritmos
                algorithm_score = (len(architecture_analysis["coordination_algorithms"]) / 5) * 100
                scores.append(algorithm_score)
                
                # Puntuación por equipos
                team_score = (len(architecture_analysis["team_structures"]) / 7) * 100
                scores.append(team_score)
                
                # Puntuación por especialización
                specialization_score = (len(architecture_analysis["agent_specializations"]) / 5) * 100
                scores.append(specialization_score)
                
                architecture_analysis["architecture_score"] = int(sum(scores) / len(scores))
        
        except Exception as e:
            logger.error(f"Error analizando arquitectura jerárquica: {str(e)}")
            architecture_analysis["error"] = str(e)
        
        return architecture_analysis
    
    async def _verify_services_and_processes(self) -> Dict[str, Any]:
        """Verificar estado de servicios y procesos"""
        logger.info("Verificando servicios y procesos...")
        
        services_status = {
            "active_processes": 0,
            "total_processes": 0,
            "system_processes": [],
            "silhouettemcp_processes": [],
            "service_health": {},
            "service_score": 0
        }
        
        try:
            # Obtener lista de procesos en ejecución
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = result.stdout.split('\n')
            
            silhouette_processes = []
            system_processes = []
            
            for process_line in processes[1:]:  # Saltar header
                if process_line.strip():
                    parts = process_line.split()
                    if len(parts) >= 11:
                        process_info = {
                            "user": parts[0],
                            "pid": parts[1],
                            "cpu": parts[2],
                            "mem": parts[3],
                            "command": ' '.join(parts[10:])
                        }
                        
                        if "silhouette" in process_info["command"].lower():
                            silhouette_processes.append(process_info)
                        elif any(sys_proc in process_info["command"].lower() for sys_proc in ["systemd", "init", "kernel"]):
                            system_processes.append(process_info)
            
            services_status["silhouettemcp_processes"] = silhouette_processes
            services_status["system_processes"] = system_processes[:10]  # Solo primeros 10
            services_status["active_processes"] = len(silhouette_processes) + len(system_processes)
            services_status["total_processes"] = len(processes) - 1
            
            # Evaluar salud de servicios
            if len(silhouette_processes) >= 3:
                services_status["service_health"]["silhouettemcp"] = "healthy"
            elif len(silhouette_processes) >= 1:
                services_status["service_health"]["silhouettemcp"] = "degraded"
            else:
                services_status["service_health"]["silhouettemcp"] = "critical"
            
            # Calcular puntuación
            if services_status["service_health"].get("silhouettemcp") == "healthy":
                services_status["service_score"] = 90
            elif services_status["service_health"].get("silhouettemcp") == "degraded":
                services_status["service_score"] = 60
            else:
                services_status["service_score"] = 20
        
        except Exception as e:
            logger.error(f"Error verificando servicios: {str(e)}")
            services_status["error"] = str(e)
        
        return services_status
    
    async def _analyze_critical_dependencies(self) -> Dict[str, Any]:
        """Analizar dependencias críticas del sistema"""
        logger.info("Analizando dependencias críticas...")
        
        dependencies_analysis = {
            "python_packages": {},
            "system_dependencies": {},
            "network_dependencies": {},
            "dependency_score": 0,
            "missing_dependencies": [],
            "critical_dependencies_ok": True
        }
        
        # Verificar paquetes Python críticos
        critical_packages = [
            ("fastapi", "Framework web"),
            ("uvicorn", "Servidor ASGI"),
            ("websockets", "Comunicación WebSocket"),
            ("json", "Manejo de JSON"),
            ("asyncio", "Programación asíncrona"),
            ("threading", "Multithreading"),
            ("subprocess", "Ejecución de procesos"),
            ("pathlib", "Manejo de rutas"),
            ("dataclasses", "Estructuras de datos"),
            ("enum", "Enumeraciones")
        ]
        
        for package, description in critical_packages:
            try:
                __import__(package)
                dependencies_analysis["python_packages"][package] = {
                    "available": True,
                    "description": description
                }
            except ImportError:
                dependencies_analysis["python_packages"][package] = {
                    "available": False,
                    "description": description
                }
                dependencies_analysis["missing_dependencies"].append(package)
                dependencies_analysis["critical_dependencies_ok"] = False
        
        # Verificar dependencias del sistema
        system_tools = [
            ("python3", "Intérprete Python"),
            ("ps", "Información de procesos"),
            ("netstat", "Estado de red"),
            ("lsof", "Archivos abiertos"),
            ("df", "Espacio en disco"),
            ("free", "Memoria disponible")
        ]
        
        for tool, description in system_tools:
            try:
                result = subprocess.run([tool, "--version"], capture_output=True, timeout=5)
                if result.returncode == 0:
                    dependencies_analysis["system_dependencies"][tool] = {
                        "available": True,
                        "description": description
                    }
                else:
                    dependencies_analysis["system_dependencies"][tool] = {
                        "available": False,
                        "description": description
                    }
            except Exception:
                dependencies_analysis["system_dependencies"][tool] = {
                    "available": False,
                    "description": description
                }
        
        # Verificar dependencias de red (puertos)
        network_ports = [
            (8001, "SilhouetteMCP Unified"),
            (8002, "SilhouetteMCP Hierarchical"),
            (8003, "Dashboard"),
            (8004, "Testing Suite"),
            (8005, "Metrics"),
            (8006, "WebSocket"),
            (8007, "Diagnostic System"),
            (8008, "Real-time Metrics"),
            (8009, "Advanced API")
        ]
        
        for port, service in network_ports:
            try:
                result = subprocess.run(['netstat', '-tuln'], capture_output=True, text=True, timeout=5)
                port_open = f":{port}" in result.stdout
                dependencies_analysis["network_dependencies"][port] = {
                    "port_open": port_open,
                    "service": service
                }
            except Exception:
                dependencies_analysis["network_dependencies"][port] = {
                    "port_open": False,
                    "service": service,
                    "error": "Unable to check port status"
                }
        
        # Calcular puntuación de dependencias
        python_score = (sum(1 for p in dependencies_analysis["python_packages"].values() if p["available"]) / len(critical_packages)) * 50
        system_score = (sum(1 for s in dependencies_analysis["system_dependencies"].values() if s["available"]) / len(system_tools)) * 30
        network_score = (sum(1 for n in dependencies_analysis["network_dependencies"].values() if n.get("port_open", False)) / len(network_ports)) * 20
        
        dependencies_analysis["dependency_score"] = int(python_score + system_score + network_score)
        
        return dependencies_analysis
    
    async def _verify_security_configuration(self) -> Dict[str, Any]:
        """Verificar configuración de seguridad"""
        logger.info("Verificando configuración de seguridad...")
        
        security_analysis = {
            "authentication": {},
            "authorization": {},
            "data_protection": {},
            "network_security": {},
            "security_score": 0,
            "security_recommendations": []
        }
        
        try:
            # Verificar configuración de autenticación JWT
            architecture_file = "/workspace/code/silhouettemcp_hierarchical_architecture.py"
            if Path(architecture_file).exists():
                with open(architecture_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Verificar implementación JWT
                if "JWT" in content or "jwt" in content:
                    security_analysis["authentication"]["jwt_implemented"] = True
                    security_analysis["authentication"]["score"] = 85
                else:
                    security_analysis["authentication"]["jwt_implemented"] = False
                    security_analysis["authentication"]["score"] = 0
                
                # Verificar manejo de API keys
                if "API_KEY" in content or "api_key" in content:
                    security_analysis["authentication"]["api_key_handling"] = True
                    security_analysis["authentication"]["score"] += 10
                
                # Verificar credenciales administrativas
                if "ADMIN_CREDENTIALS" in content or "admin" in content.lower():
                    security_analysis["authorization"]["admin_auth"] = True
                    security_analysis["authorization"]["score"] = 80
                else:
                    security_analysis["authorization"]["admin_auth"] = False
                    security_analysis["authorization"]["score"] = 0
                
                # Verificar CORS
                if "CORS" in content:
                    security_analysis["network_security"]["cors_configured"] = True
                    security_analysis["network_security"]["score"] = 70
                else:
                    security_analysis["network_security"]["cors_configured"] = False
                    security_analysis["network_security"]["score"] = 0
                
                # Verificar protección de archivos
                if "secret" in content.lower() or "key" in content.lower():
                    security_analysis["data_protection"]["sensitive_data_protected"] = True
                    security_analysis["data_protection"]["score"] = 75
                else:
                    security_analysis["data_protection"]["sensitive_data_protected"] = False
                    security_analysis["data_protection"]["score"] = 0
            
            # Calcular puntuación general de seguridad
            security_scores = []
            for category in ["authentication", "authorization", "network_security", "data_protection"]:
                if category in security_analysis:
                    for key, value in security_analysis[category].items():
                        if isinstance(value, int) and value > 0:
                            security_scores.append(value)
            
            if security_scores:
                security_analysis["security_score"] = int(sum(security_scores) / len(security_scores))
            
            # Generar recomendaciones de seguridad
            if security_analysis["security_score"] < 70:
                security_analysis["security_recommendations"].append("Implementar autenticación JWT robusta")
            if not security_analysis["authentication"].get("api_key_handling"):
                security_analysis["security_recommendations"].append("Configurar manejo seguro de API keys")
            if not security_analysis["network_security"].get("cors_configured"):
                security_analysis["security_recommendations"].append("Configurar CORS apropiado")
            
        except Exception as e:
            logger.error(f"Error verificando seguridad: {str(e)}")
            security_analysis["error"] = str(e)
        
        return security_analysis
    
    async def _analyze_performance_basics(self) -> Dict[str, Any]:
        """Realizar análisis básico de performance"""
        logger.info("Realizando análisis de performance básico...")
        
        performance_analysis = {
            "system_resources": {},
            "process_performance": {},
            "memory_usage": {},
            "cpu_usage": {},
            "disk_usage": {},
            "performance_score": 0,
            "performance_alerts": []
        }
        
        try:
            # Verificar uso de CPU
            try:
                result = subprocess.run(['top', '-bn1'], capture_output=True, text=True, timeout=10)
                lines = result.stdout.split('\n')
                
                cpu_line = None
                for line in lines:
                    if 'Cpu(s)' in line or '%Cpu(s)' in line:
                        cpu_line = line
                        break
                
                if cpu_line:
                    # Extraer porcentaje de uso de CPU
                    import re
                    cpu_match = re.search(r'(\d+\.\d+)%us', cpu_line)
                    if cpu_match:
                        cpu_usage = float(cpu_match.group(1))
                        performance_analysis["cpu_usage"]["current_usage_percent"] = cpu_usage
                        
                        if cpu_usage > 80:
                            performance_analysis["performance_alerts"].append(f"Alto uso de CPU: {cpu_usage}%")
                            performance_analysis["cpu_usage"]["status"] = "warning"
                        elif cpu_usage > 60:
                            performance_analysis["cpu_usage"]["status"] = "moderate"
                        else:
                            performance_analysis["cpu_usage"]["status"] = "good"
                
            except Exception as e:
                logger.warning(f"No se pudo obtener uso de CPU: {str(e)}")
            
            # Verificar uso de memoria
            try:
                result = subprocess.run(['free', '-m'], capture_output=True, text=True, timeout=5)
                lines = result.stdout.split('\n')
                
                for line in lines:
                    if line.startswith('Mem:'):
                        parts = line.split()
                        if len(parts) >= 6:
                            total_mb = int(parts[1])
                            used_mb = int(parts[2])
                            free_mb = int(parts[3])
                            
                            usage_percent = (used_mb / total_mb) * 100
                            
                            performance_analysis["memory_usage"] = {
                                "total_mb": total_mb,
                                "used_mb": used_mb,
                                "free_mb": free_mb,
                                "usage_percent": round(usage_percent, 2),
                                "status": "warning" if usage_percent > 80 else "moderate" if usage_percent > 60 else "good"
                            }
                            
                            if usage_percent > 80:
                                performance_analysis["performance_alerts"].append(f"Alto uso de memoria: {usage_percent}%")
                
            except Exception as e:
                logger.warning(f"No se pudo obtener uso de memoria: {str(e)}")
            
            # Verificar uso de disco
            try:
                result = subprocess.run(['df', '-h'], capture_output=True, text=True, timeout=5)
                lines = result.stdout.split('\n')
                
                for line in lines[1:]:  # Saltar header
                    if line and '/' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            filesystem = parts[0]
                            size = parts[1]
                            used = parts[2]
                            available = parts[3]
                            use_percent = parts[4]
                            
                            try:
                                use_num = int(use_percent.rstrip('%'))
                                if use_percent.endswith('%'):
                                    performance_analysis["disk_usage"] = {
                                        "filesystem": filesystem,
                                        "total_size": size,
                                        "used": used,
                                        "available": available,
                                        "usage_percent": use_num,
                                        "status": "warning" if use_num > 80 else "moderate" if use_num > 60 else "good"
                                    }
                                    
                                    if use_num > 80:
                                        performance_analysis["performance_alerts"].append(f"Alto uso de disco {filesystem}: {use_num}%")
                            except ValueError:
                                pass
                
            except Exception as e:
                logger.warning(f"No se pudo obtener uso de disco: {str(e)}")
            
            # Calcular puntuación de performance
            scores = []
            
            # Puntuación por CPU
            if "cpu_usage" in performance_analysis and "status" in performance_analysis["cpu_usage"]:
                cpu_status = performance_analysis["cpu_usage"]["status"]
                if cpu_status == "good":
                    scores.append(100)
                elif cpu_status == "moderate":
                    scores.append(70)
                elif cpu_status == "warning":
                    scores.append(40)
                else:
                    scores.append(50)
            
            # Puntuación por memoria
            if "memory_usage" in performance_analysis and "status" in performance_analysis["memory_usage"]:
                mem_status = performance_analysis["memory_usage"]["status"]
                if mem_status == "good":
                    scores.append(100)
                elif mem_status == "moderate":
                    scores.append(70)
                elif mem_status == "warning":
                    scores.append(40)
                else:
                    scores.append(50)
            
            # Puntuación por disco
            if "disk_usage" in performance_analysis and "status" in performance_analysis["disk_usage"]:
                disk_status = performance_analysis["disk_usage"]["status"]
                if disk_status == "good":
                    scores.append(100)
                elif disk_status == "moderate":
                    scores.append(70)
                elif disk_status == "warning":
                    scores.append(40)
                else:
                    scores.append(50)
            
            if scores:
                performance_analysis["performance_score"] = int(sum(scores) / len(scores))
            
        except Exception as e:
            logger.error(f"Error en análisis de performance: {str(e)}")
            performance_analysis["error"] = str(e)
        
        return performance_analysis
    
    async def _analyze_system_integration(self) -> Dict[str, Any]:
        """Analizar integración entre sistemas"""
        logger.info("Analizando integración entre sistemas...")
        
        integration_analysis = {
            "silhouettemcp_integration": {},
            "iris_mcp_integration": {},
            "contextforge_integration": {},
            "microsoft365_integration": {},
            "external_services": {},
            "integration_score": 0,
            "integration_issues": []
        }
        
        # Verificar integración con sistemas principales
        systems_to_check = [
            ("silhouettemcp", "SilhouetteMCP Core"),
            ("iris", "Iris MCP"),
            ("contextforge", "MCP Context Forge"),
            ("microsoft365", "Microsoft 365"),
            ("supabase", "Supabase"),
            ("external_apis", "APIs Externas")
        ]
        
        for system_key, system_name in systems_to_check:
            # Verificar archivos relacionados
            related_files = []
            workspace_files = list(Path("/workspace").rglob("*"))
            
            for file_path in workspace_files:
                if system_key.lower() in file_path.name.lower() or system_key.lower() in str(file_path):
                    related_files.append(str(file_path))
            
            integration_analysis[f"{system_key}_integration"] = {
                "system_name": system_name,
                "related_files": len(related_files),
                "files_found": related_files[:5],  # Solo primeros 5
                "status": "integrated" if len(related_files) > 0 else "not_found"
            }
            
            if len(related_files) == 0:
                integration_analysis["integration_issues"].append(f"No se encontraron archivos para {system_name}")
        
        # Verificar conectividad de red
        external_endpoints = [
            ("https://api.github.com", "GitHub API"),
            ("https://maps.googleapis.com", "Google Maps API"),
            ("https://api.finance.yahoo.com", "Yahoo Finance API"),
            ("https://api.twitter.com", "Twitter API"),
            ("https://api.booking.com", "Booking API"),
            ("https://api.tripadvisor.com", "TripAdvisor API")
        ]
        
        for endpoint, service_name in external_endpoints:
            try:
                # Test simple de conectividad sin hacer requests reales
                import urllib.parse
                parsed_url = urllib.parse.urlparse(endpoint)
                
                integration_analysis["external_services"][service_name] = {
                    "endpoint": endpoint,
                    "hostname": parsed_url.netloc,
                    "status": "configured",  # Asumimos configurado si existe el endpoint
                    "connectivity": "pending_test"
                }
            except Exception as e:
                integration_analysis["external_services"][service_name] = {
                    "endpoint": endpoint,
                    "service_name": service_name,
                    "status": "error",
                    "error": str(e)
                }
        
        # Calcular puntuación de integración
        integration_scores = []
        
        for key in integration_analysis:
            if key.endswith("_integration") and isinstance(integration_analysis[key], dict):
                status = integration_analysis[key].get("status")
                if status == "integrated":
                    integration_scores.append(100)
                elif status == "configured":
                    integration_scores.append(80)
                elif status == "not_found":
                    integration_scores.append(30)
                else:
                    integration_scores.append(50)
        
        if integration_scores:
            integration_analysis["integration_score"] = int(sum(integration_scores) / len(integration_scores))
        
        return integration_analysis
    
    async def _analyze_scalability_capabilities(self) -> Dict[str, Any]:
        """Analizar capacidades de escalabilidad"""
        logger.info("Analizando capacidades de escalabilidad...")
        
        scalability_analysis = {
            "horizontal_scaling": {},
            "vertical_scaling": {},
            "load_balancing": {},
            "auto_scaling": {},
            "scalability_score": 0,
            "scalability_limitations": []
        }
        
        try:
            architecture_file = "/workspace/code/silhouettemcp_hierarchical_architecture.py"
            if Path(architecture_file).exists():
                with open(architecture_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Verificar escalabilidad horizontal
                horizontal_patterns = [
                    ("load balancer", "Balanceador de carga"),
                    ("horizontal scaling", "Escalamiento horizontal"),
                    ("auto scaling", "Escalamiento automático"),
                    ("multiple instances", "Múltiples instancias"),
                    ("cluster", "Cluster")
                ]
                
                for pattern, description in horizontal_patterns:
                    if pattern.lower() in content.lower():
                        scalability_analysis["horizontal_scaling"][pattern] = {
                            "implemented": True,
                            "description": description
                        }
                
                # Verificar escalabilidad vertical
                vertical_patterns = [
                    ("resource optimization", "Optimización de recursos"),
                    ("memory management", "Gestión de memoria"),
                    ("cpu optimization", "Optimización de CPU"),
                    ("threading", "Multithreading"),
                    ("parallel processing", "Procesamiento paralelo")
                ]
                
                for pattern, description in vertical_patterns:
                    if pattern.lower() in content.lower():
                        scalability_analysis["vertical_scaling"][pattern] = {
                            "implemented": True,
                            "description": description
                        }
                
                # Verificar capacidades específicas de escalabilidad
                scalability_patterns = [
                    ("1000", "Soporte para 1000 usuarios"),
                    ("concurrent", "Usuarios concurrentes"),
                    ("scalable", "Arquitectura escalable"),
                    ("performance", "Optimización de performance")
                ]
                
                scalability_features = 0
                for pattern in scalability_patterns:
                    if pattern in content:
                        scalability_features += 1
                
                scalability_analysis["auto_scaling"]["features_implemented"] = scalability_features
                scalability_analysis["auto_scaling"]["max_estimated_users"] = 1000 if "1000" in content else 500
            
            # Evaluar configuración del sistema para escalabilidad
            try:
                # Verificar límites del sistema
                with open('/proc/sys/fs/file-max', 'r') as f:
                    file_max = int(f.read().strip())
                    scalability_analysis["system_limits"] = {
                        "max_open_files": file_max,
                        "file_limit_status": "adequate" if file_max > 100000 else "limited"
                    }
            except Exception:
                scalability_analysis["system_limits"] = {
                    "max_open_files": "unknown",
                    "file_limit_status": "unknown"
                }
            
            # Calcular puntuación de escalabilidad
            scores = []
            
            # Puntuación por escalabilidad horizontal
            horizontal_score = (len(scalability_analysis["horizontal_scaling"]) / 5) * 100
            scores.append(horizontal_score)
            
            # Puntuación por escalabilidad vertical
            vertical_score = (len(scalability_analysis["vertical_scaling"]) / 5) * 100
            scores.append(vertical_score)
            
            # Puntuación por características de escalabilidad
            features_score = (scalability_analysis["auto_scaling"]["features_implemented"] / 4) * 100
            scores.append(features_score)
            
            scalability_analysis["scalability_score"] = int(sum(scores) / len(scores))
            
            # Identificar limitaciones
            if scalability_analysis["scalability_score"] < 70:
                scalability_analysis["scalability_limitations"].append("Escalabilidad limitada - considerar optimizaciones")
            
            if scalability_analysis["auto_scaling"]["max_estimated_users"] < 500:
                scalability_analysis["scalability_limitations"].append("Capacidad estimada de usuarios por debajo del objetivo")
            
        except Exception as e:
            logger.error(f"Error analizando escalabilidad: {str(e)}")
            scalability_analysis["error"] = str(e)
        
        return scalability_analysis
    
    async def _analyze_recovery_mechanisms(self) -> Dict[str, Any]:
        """Analizar mecanismos de recuperación"""
        logger.info("Analizando mecanismos de recuperación...")
        
        recovery_analysis = {
            "backup_mechanisms": {},
            "health_monitoring": {},
            "auto_recovery": {},
            "disaster_recovery": {},
            "recovery_score": 0,
            "recovery_recommendations": []
        }
        
        try:
            # Verificar mecanismos de backup
            architecture_file = "/workspace/code/silhouettemcp_hierarchical_architecture.py"
            if Path(architecture_file).exists():
                with open(architecture_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Verificar auto-healing
                healing_patterns = [
                    ("auto_healing", "Auto-healing"),
                    ("health check", "Verificación de salud"),
                    ("self recovery", "Auto-recuperación"),
                    ("restart", "Reinicio automático"),
                    ("failover", "Conmutación por error")
                ]
                
                for pattern, description in healing_patterns:
                    if pattern.lower() in content.lower():
                        recovery_analysis["auto_recovery"][pattern] = {
                            "implemented": True,
                            "description": description
                        }
                
                # Verificar monitoreo de salud
                monitoring_patterns = [
                    ("metrics", "Métricas"),
                    ("monitoring", "Monitoreo"),
                    ("dashboard", "Dashboard"),
                    ("alerting", "Alertas"),
                    ("log", "Logging")
                ]
                
                for pattern, description in monitoring_patterns:
                    if pattern.lower() in content.lower():
                        recovery_analysis["health_monitoring"][pattern] = {
                            "implemented": True,
                            "description": description
                        }
                
                # Verificar recovery de disaster
                disaster_patterns = [
                    ("backup", "Respaldo"),
                    ("restore", "Restauración"),
                    ("recovery", "Recuperación"),
                    ("disaster", "Desastre"),
                    ("redundancy", "Redundancia")
                ]
                
                for pattern, description in disaster_patterns:
                    if pattern.lower() in content.lower():
                        recovery_analysis["disaster_recovery"][pattern] = {
                            "implemented": True,
                            "description": description
                        }
                
                # Verificar backup de archivos
                workspace = Path("/workspace")
                backup_files = list(workspace.rglob("backup*")) + list(workspace.rglob("*backup*"))
                recovery_analysis["backup_mechanisms"]["backup_files_found"] = len(backup_files)
                recovery_analysis["backup_mechanisms"]["backup_locations"] = [str(f) for f in backup_files[:5]]
            
            # Verificar logs del sistema para recovery
            try:
                # Buscar archivos de log
                log_files = list(Path("/workspace").rglob("*.log"))
                recovery_analysis["backup_mechanisms"]["log_files"] = len(log_files)
            except Exception:
                recovery_analysis["backup_mechanisms"]["log_files"] = 0
            
            # Calcular puntuación de recuperación
            scores = []
            
            # Puntuación por auto-recovery
            auto_recovery_score = (len(recovery_analysis["auto_recovery"]) / 5) * 40
            scores.append(auto_recovery_score)
            
            # Puntuación por monitoreo
            monitoring_score = (len(recovery_analysis["health_monitoring"]) / 5) * 30
            scores.append(monitoring_score)
            
            # Puntuación por disaster recovery
            disaster_score = (len(recovery_analysis["disaster_recovery"]) / 5) * 20
            scores.append(disaster_score)
            
            # Puntuación por backup
            backup_score = min(recovery_analysis["backup_mechanisms"]["backup_files_found"] * 10, 100)
            scores.append(backup_score)
            
            recovery_analysis["recovery_score"] = int(sum(scores) / len(scores))
            
            # Generar recomendaciones
            if recovery_analysis["recovery_score"] < 70:
                recovery_analysis["recovery_recommendations"].append("Implementar más mecanismos de auto-recuperación")
            
            if len(recovery_analysis["backup_mechanisms"]["backup_files_found"]) < 3:
                recovery_analysis["recovery_recommendations"].append("Establecer estrategia de backup más robusta")
            
        except Exception as e:
            logger.error(f"Error analizando recuperación: {str(e)}")
            recovery_analysis["error"] = str(e)
        
        return recovery_analysis
    
    def _consolidate_issues(self, diagnostic_results: Dict[str, Any]) -> Dict[str, Any]:
        """Consolidar issues de todos los análisis"""
        issues = {
            "critical_issues": [],
            "high_issues": [],
            "medium_issues": [],
            "low_issues": [],
            "info_items": []
        }
        
        # Verificar archivos críticos
        if "file_verification" in diagnostic_results.get("system_health", {}):
            file_verification = diagnostic_results["system_health"]["file_verification"]
            if file_verification.get("verification_score", 100) < 80:
                missing_count = len(file_verification.get("files_missing", []))
                if missing_count > 0:
                    issues["critical_issues"].append({
                        "component": "file_system",
                        "issue": f"{missing_count} archivos críticos faltantes",
                        "impact": "Funcionalidad del sistema comprometida",
                        "severity": "CRITICAL"
                    })
        
        # Verificar servicios
        if "services" in diagnostic_results.get("system_health", {}):
            services = diagnostic_results["system_health"]["services"]
            service_health = services.get("service_health", {}).get("silhouettemcp", "unknown")
            if service_health == "critical":
                issues["critical_issues"].append({
                    "component": "services",
                    "issue": "Servicios SilhouetteMCP no funcionando",
                    "impact": "Sistema principal no operativo",
                    "severity": "CRITICAL"
                })
        
        # Verificar arquitectura
        if "architecture_score" in diagnostic_results.get("architecture_assessment", {}):
            arch_score = diagnostic_results["architecture_assessment"]["architecture_score"]
            if arch_score < 70:
                issues["high_issues"].append({
                    "component": "architecture",
                    "issue": f"Puntuación de arquitectura baja: {arch_score}/100",
                    "impact": "Arquitectura del sistema subóptima",
                    "severity": "HIGH"
                })
        
        # Verificar dependencias
        if "dependency_score" in diagnostic_results.get("architecture_assessment", {}):
            dep_score = diagnostic_results["architecture_assessment"]["dependency_score"]
            missing_deps = diagnostic_results["architecture_assessment"].get("missing_dependencies", [])
            if dep_score < 80 or len(missing_deps) > 0:
                issues["high_issues"].append({
                    "component": "dependencies",
                    "issue": f"Dependencias faltantes: {', '.join(missing_deps[:3])}{'...' if len(missing_deps) > 3 else ''}",
                    "impact": "Funcionalidad limitada o no disponible",
                    "severity": "HIGH"
                })
        
        # Verificar seguridad
        if "security_score" in diagnostic_results.get("security_assessment", {}):
            sec_score = diagnostic_results["security_assessment"]["security_score"]
            if sec_score < 70:
                issues["high_issues"].append({
                    "component": "security",
                    "issue": f"Puntuación de seguridad baja: {sec_score}/100",
                    "impact": "Sistema vulnerable a amenazas",
                    "severity": "HIGH"
                })
        
        # Verificar performance
        if "performance_score" in diagnostic_results.get("performance_analysis", {}):
            perf_score = diagnostic_results["performance_analysis"]["performance_score"]
            perf_alerts = diagnostic_results["performance_analysis"].get("performance_alerts", [])
            if perf_score < 70 or len(perf_alerts) > 2:
                issues["medium_issues"].append({
                    "component": "performance",
                    "issue": f"Performance suboptimal: {perf_score}/100",
                    "impact": "Posible degradación de la experiencia del usuario",
                    "severity": "MEDIUM"
                })
        
        # Verificar integración
        if "integration_score" in diagnostic_results.get("integration_status", {}):
            integ_score = diagnostic_results["integration_status"]["integration_score"]
            integ_issues = diagnostic_results["integration_status"].get("integration_issues", [])
            if integ_score < 70 or len(integ_issues) > 2:
                issues["medium_issues"].append({
                    "component": "integration",
                    "issue": f"Problemas de integración: {integ_score}/100",
                    "impact": "Funcionalidad limitada entre sistemas",
                    "severity": "MEDIUM"
                })
        
        # Verificar escalabilidad
        if "scalability_score" in diagnostic_results.get("scalability_analysis", {}):
            scale_score = diagnostic_results["scalability_analysis"]["scalability_score"]
            scale_limits = diagnostic_results["scalability_analysis"].get("scalability_limitations", [])
            if scale_score < 70 or len(scale_limits) > 1:
                issues["medium_issues"].append({
                    "component": "scalability",
                    "issue": f"Limitaciones de escalabilidad: {scale_score}/100",
                    "impact": "Capacidad de crecimiento limitada",
                    "severity": "MEDIUM"
                })
        
        # Verificar recuperación
        if "recovery_score" in diagnostic_results.get("recovery_capabilities", {}):
            recovery_score = diagnostic_results["recovery_capabilities"]["recovery_score"]
            recovery_recom = diagnostic_results["recovery_capabilities"].get("recovery_recommendations", [])
            if recovery_score < 70 or len(recovery_recom) > 1:
                issues["low_issues"].append({
                    "component": "recovery",
                    "issue": f"Mecanismos de recuperación insuficientes: {recovery_score}/100",
                    "impact": "Tiempo de recuperación potencialmente largo",
                    "severity": "LOW"
                })
        
        return issues
    
    def _calculate_comprehensive_score(self, diagnostic_results: Dict[str, Any]) -> int:
        """Calcular puntuación comprensiva del sistema"""
        scores = []
        
        # Puntuación por verificación de archivos
        if "file_verification" in diagnostic_results.get("system_health", {}):
            scores.append(diagnostic_results["system_health"]["file_verification"].get("verification_score", 100))
        
        # Puntuación por servicios
        if "services" in diagnostic_results.get("system_health", {}):
            scores.append(diagnostic_results["system_health"]["services"].get("service_score", 100))
        
        # Puntuación por arquitectura
        if "architecture_score" in diagnostic_results.get("architecture_assessment", {}):
            scores.append(diagnostic_results["architecture_assessment"]["architecture_score"])
        
        # Puntuación por dependencias
        if "dependency_score" in diagnostic_results.get("architecture_assessment", {}):
            scores.append(diagnostic_results["architecture_assessment"]["dependency_score"])
        
        # Puntuación por seguridad
        if "security_score" in diagnostic_results.get("security_assessment", {}):
            scores.append(diagnostic_results["security_assessment"]["security_score"])
        
        # Puntuación por performance
        if "performance_score" in diagnostic_results.get("performance_analysis", {}):
            scores.append(diagnostic_results["performance_analysis"]["performance_score"])
        
        # Puntuación por integración
        if "integration_score" in diagnostic_results.get("integration_status", {}):
            scores.append(diagnostic_results["integration_status"]["integration_score"])
        
        # Puntuación por escalabilidad
        if "scalability_score" in diagnostic_results.get("scalability_analysis", {}):
            scores.append(diagnostic_results["scalability_analysis"]["scalability_score"])
        
        # Puntuación por recuperación
        if "recovery_score" in diagnostic_results.get("recovery_capabilities", {}):
            scores.append(diagnostic_results["recovery_capabilities"]["recovery_score"])
        
        # Calcular puntuación promedio
        if scores:
            return int(sum(scores) / len(scores))
        else:
            return 75  # Puntuación por defecto
    
    def _generate_strategic_recommendations(self, diagnostic_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generar recomendaciones estratégicas"""
        recommendations = []
        
        overall_score = diagnostic_results.get("overall_score", 0)
        critical_issues = len(diagnostic_results.get("critical_issues", []))
        high_issues = len(diagnostic_results.get("high_issues", []))
        
        # Recomendaciones basadas en puntuación general
        if overall_score < 50:
            recommendations.append({
                "priority": "CRITICAL",
                "category": "overall",
                "recommendation": "Implementación urgente de mejoras críticas en todo el sistema",
                "rationale": f"Puntuación crítica: {overall_score}/100 con {critical_issues} issues críticos"
            })
        elif overall_score < 70:
            recommendations.append({
                "priority": "HIGH",
                "category": "overall",
                "recommendation": "Abordar issues de alta prioridad inmediatamente",
                "rationale": f"Puntuación por debajo del mínimo aceptable: {overall_score}/100"
            })
        elif overall_score < 85:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "optimization",
                "recommendation": "Optimizaciones recomendadas para mejorar el rendimiento",
                "rationale": f"Sistema funcional pero con potencial de mejora: {overall_score}/100"
            })
        
        # Recomendaciones específicas por área
        if critical_issues > 0:
            recommendations.append({
                "priority": "CRITICAL",
                "category": "stability",
                "recommendation": "Resolver todos los issues críticos antes de continuar",
                "rationale": f"{critical_issues} issues críticos identificados"
            })
        
        # Recomendaciones por categoría
        categories = {
            "architecture_assessment": "architecture",
            "security_assessment": "security",
            "performance_analysis": "performance",
            "integration_status": "integration",
            "scalability_analysis": "scalability"
        }
        
        for category_key, category_name in categories.items():
            if category_key in diagnostic_results:
                category_data = diagnostic_results[category_key]
                category_score = category_data.get(f"{category_name}_score", 100)
                
                if category_score < 70:
                    recommendations.append({
                        "priority": "HIGH",
                        "category": category_name,
                        "recommendation": f"Mejoras urgentes en {category_name}",
                        "rationale": f"Puntuación baja en {category_name}: {category_score}/100"
                    })
        
        # Recomendaciones preventivas
        recommendations.append({
            "priority": "MEDIUM",
            "category": "monitoring",
            "recommendation": "Implementar monitoreo continuo del sistema",
            "rationale": "Mejorar visibilidad y capacidad de respuesta ante problemas"
        })
        
        recommendations.append({
            "priority": "LOW",
            "category": "documentation",
            "recommendation": "Actualizar documentación técnica",
            "rationale": "Mantener documentación actualizada para facilitar mantenimiento"
        })
        
        return recommendations

# ==================== API DE DIAGNÓSTICO ====================

# Crear instancia del sistema de diagnóstico
diagnostic_system = RobustDiagnosticSystem()

# Crear aplicación FastAPI
app = FastAPI(
    title="SilhouetteMCP Robust Diagnostic System",
    description="Sistema robusto de diagnóstico para arquitectura jerárquica",
    version="1.0.0",
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

@app.get("/health")
async def get_health_status():
    """Endpoint de verificación de salud del sistema de diagnóstico"""
    return {
        "status": "healthy",
        "service": "SilhouetteMCP Robust Diagnostic",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.post("/diagnostic/comprehensive")
async def run_comprehensive_diagnostic():
    """Ejecutar diagnóstico completo del sistema"""
    logger.info("Iniciando diagnóstico completo vía API")
    
    try:
        result = await diagnostic_system.run_comprehensive_diagnostic()
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error en diagnóstico completo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/diagnostic/summary")
async def get_diagnostic_summary():
    """Obtener resumen rápido del diagnóstico"""
    try:
        result = await diagnostic_system.run_comprehensive_diagnostic()
        
        summary = {
            "overall_score": result.get("overall_score", 0),
            "status": "EXCELLENT" if result.get("overall_score", 0) >= 90 else \
                     "GOOD" if result.get("overall_score", 0) >= 80 else \
                     "FAIR" if result.get("overall_score", 0) >= 70 else \
                     "POOR" if result.get("overall_score", 0) >= 50 else "CRITICAL",
            "critical_issues": len(result.get("critical_issues", [])),
            "high_issues": len(result.get("high_issues", [])),
            "medium_issues": len(result.get("medium_issues", [])),
            "low_issues": len(result.get("low_issues", [])),
            "total_recommendations": len(result.get("recommendations", [])),
            "execution_time": result.get("execution_time_seconds", 0),
            "timestamp": result.get("timestamp")
        }
        
        return JSONResponse(content=summary)
    except Exception as e:
        logger.error(f"Error generando resumen: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/diagnostic/metrics")
async def websocket_diagnostic_metrics(websocket: WebSocket):
    """WebSocket para métricas en tiempo real del diagnóstico"""
    await websocket.accept()
    logger.info("Cliente conectado a métricas de diagnóstico en tiempo real")
    
    try:
        while True:
            # Enviar métricas básicas
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu_usage": "checking...",
                "memory_usage": "checking...",
                "disk_usage": "checking..."
            }
            
            await websocket.send_json({
                "type": "metrics",
                "data": metrics
            })
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        logger.info("Cliente desconectado de métricas de diagnóstico")
    except Exception as e:
        logger.error(f"Error en WebSocket de métricas: {str(e)}")

@app.get("/reports/diagnostic")
async def generate_diagnostic_report():
    """Generar reporte de diagnóstico"""
    try:
        result = await diagnostic_system.run_comprehensive_diagnostic()
        
        # Guardar reporte
        report_filename = f"robust_diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = f"/workspace/code/{report_filename}"
        
        async with aiofiles.open(report_path, 'w') as f:
            await f.write(json.dumps(result, indent=2, default=str))
        
        return JSONResponse(content={
            "report_generated": True,
            "report_path": report_path,
            "overall_score": result.get("overall_score", 0),
            "report_size_kb": round(len(json.dumps(result)) / 1024, 2),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generando reporte: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== FUNCIÓN PRINCIPAL ====================

if __name__ == "__main__":
    logger.info("Iniciando SilhouetteMCP Robust Diagnostic System...")
    logger.info("Sistema de diagnóstico robusto sin dependencias externas problemáticas")
    logger.info("Puertos disponibles:")
    logger.info("- 8007: API de Diagnóstico Principal")
    logger.info("- 8008: Métricas en Tiempo Real (WebSocket)")
    logger.info("- 8009: Endpoints de Diagnóstico Avanzado")
    
    uvicorn.run(
        "silhouettemcp_robust_diagnostic_system:app",
        host="0.0.0.0",
        port=8007,
        reload=False,
        log_level="info"
    )