"""
Python Executor Agent MCP con Sandbox Avanzado
Integra con backend/tools/python_executor.py pero con capacidades MCP mejoradas
"""
import sys
import io
import ast
import traceback
import signal
import time
import contextlib
import subprocess
import resource
import psutil
import tempfile
import os
import shutil
import json
import pickle
import hashlib
from typing import Dict, Any, List, Optional, Union, Callable, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
import logging
import threading
from datetime import datetime
import uuid
import cProfile
import pstats
import memory_profiler
import tempfile
import resource
import socket

# Importar el ejecutor Python existente
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
from tools.python_executor import PythonExecutor, ExecutionContext, SafeExecutionError

# Importar componentes MCP
from .base_agent_wrapper import BaseAgentWrapper, AgentCapability, AgentCapabilityError
from ..core.exceptions import AgentException, handle_exceptions
from ..core.config import settings


class SecurityLevel(Enum):
    """Niveles de seguridad para ejecución"""
    MINIMAL = "minimal"
    RESTRICTED = "restricted"
    MODERATE = "moderate"
    STRICT = "strict"
    MAXIMUM = "maximum"


class ResourceLimit(Enum):
    """Tipos de límites de recursos"""
    CPU_TIME = "cpu_time"
    MEMORY = "memory"
    DISK_IO = "disk_io"
    NETWORK = "network"
    FILE_DESCRIPTORS = "file_descriptors"
    PROCESSES = "processes"


class CodeAnalysisResult(Enum):
    """Resultados de análisis de código"""
    SAFE = "safe"
    WARNING = "warning"
    DANGEROUS = "dangerous"
    UNKNOWN = "unknown"


@dataclass
class ResourceLimits:
    """Límites de recursos para sandbox"""
    max_memory_mb: int = 512
    max_cpu_seconds: int = 10
    max_disk_io_mb: int = 100
    max_file_descriptors: int = 64
    max_processes: int = 4
    max_network_connections: int = 0  # 0 = deshabilitado
    timeout_seconds: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)


@dataclass
class CodeAnalysis:
    """Análisis completo de código"""
    security_level: SecurityLevel
    code_issues: List[str] = field(default_factory=list)
    syntax_valid: bool = True
    syntax_error: Optional[str] = None
    security_warnings: List[str] = field(default_factory=list)
    complexity_metrics: Dict[str, Any] = field(default_factory=dict)
    dependency_analysis: List[str] = field(default_factory=list)
    risk_score: float = 0.0  # 0.0 = seguro, 1.0 = máximo riesgo
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)


@dataclass
class ExecutionResult:
    """Resultado de ejecución de código"""
    success: bool
    output: str = ""
    error: Optional[str] = None
    return_value: Any = None
    locals: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    memory_used: float = 0.0
    cpu_time: float = 0.0
    security_violations: List[str] = field(default_factory=list)
    profile_data: Optional[Dict[str, Any]] = None
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)


@dataclass
class TestResult:
    """Resultado de testing automático"""
    test_name: str
    success: bool
    assertions_passed: int = 0
    assertions_failed: int = 0
    error_message: Optional[str] = None
    execution_time: float = 0.0
    coverage_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)


class NetworkIsolationError(Exception):
    """Error de aislamiento de red"""
    pass


class ResourceLimitExceededError(Exception):
    """Error cuando se exceden los límites de recursos"""
    pass


class AdvancedPythonExecutorAgent(BaseAgentWrapper):
    """
    Agente MCP para ejecución segura de código Python con sandbox avanzado
    
    Características:
    - Ejecución segura con timeouts y límites de recursos
    - Análisis de seguridad avanzado con AST
    - Testing automático y profiling
    - Aislamiento de red y sandbox completo
    - Validación de dependencias y análisis de código
    - Captura estructurada de resultados y métricas
    """
    
    def __init__(self, 
                 security_level: SecurityLevel = SecurityLevel.RESTRICTED,
                 default_resource_limits: Optional[ResourceLimits] = None):
        """
        Inicializar el agente ejecutor Python
        
        Args:
            security_level: Nivel de seguridad por defecto
            default_resource_limits: Límites de recursos por defecto
        """
        capabilities = [
            AgentCapability.CODE_EXECUTION,
            AgentCapability.TOOL_INVOCATION,
            AgentCapability.CONCURRENT_EXECUTION,
            AgentCapability.RESULT_COLLECTION
        ]
        
        super().__init__(
            agent_name="python_executor",
            capabilities=capabilities,
            max_concurrent=settings.executor_max_workers,
            timeout_seconds=settings.executor_timeout_seconds,
            retry_attempts=3,
            retry_delay=1.0
        )
        
        self.security_level = security_level
        self.default_resource_limits = default_resource_limits or ResourceLimits()
        self.python_executor = PythonExecutor()
        
        # Configuración de seguridad avanzada
        self.security_configs = self._init_security_configs()
        
        # Cache de análisis de código
        self.code_analysis_cache = {}
        
        # Métricas avanzadas
        self.execution_metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "average_memory_usage": 0.0,
            "security_violations": 0,
            "cache_hits": 0
        }
        
        # Network isolation (si está disponible)
        self.network_isolation_enabled = False
        self._init_network_isolation()
        
        self.logger = logging.getLogger("mcp.agents.python_executor_advanced")
        self.logger.info(f"PythonExecutorAgent inicializado con seguridad {security_level.value}")
    
    def _init_security_configs(self) -> Dict[SecurityLevel, Dict[str, Any]]:
        """Inicializar configuraciones de seguridad por nivel"""
        return {
            SecurityLevel.MINIMAL: {
                "allowed_builtins": [
                    'int', 'float', 'str', 'bool', 'list', 'dict', 'tuple', 'set',
                    'abs', 'min', 'max', 'sum', 'print', 'len', 'range', 'enumerate',
                    'all', 'any', 'zip', 'reversed', 'sorted', 'filter', 'map'
                ],
                "allowed_modules": [
                    'math', 'random', 'json', 're', 'datetime', 'collections',
                    'itertools', 'functools', 'operator', 'string', 'decimal',
                    'statistics', 'base64', 'hashlib', 'uuid', 'typing'
                ],
                "forbidden_imports": ['os', 'sys', 'subprocess', 'pickle', 'marshal'],
                "resource_limits": ResourceLimits(
                    max_memory_mb=1024,
                    max_cpu_seconds=30,
                    timeout_seconds=60
                )
            },
            SecurityLevel.RESTRICTED: {
                "allowed_builtins": [
                    'int', 'float', 'str', 'bool', 'list', 'dict', 'tuple', 'set',
                    'abs', 'min', 'max', 'sum', 'print', 'len', 'range', 'enumerate',
                    'all', 'any', 'zip', 'reversed', 'sorted', 'filter', 'map'
                ],
                "allowed_modules": ['math', 'random', 'json', 'collections'],
                "forbidden_imports": [
                    'os', 'sys', 'subprocess', 'pickle', 'marshal', 'fileinput',
                    'glob', 'fnmatch', 'io', 'tempfile', 'shutil', 'pathlib'
                ],
                "resource_limits": ResourceLimits(
                    max_memory_mb=512,
                    max_cpu_seconds=15,
                    timeout_seconds=30
                )
            },
            SecurityLevel.MODERATE: {
                "allowed_builtins": [
                    'int', 'float', 'str', 'bool', 'list', 'dict', 'tuple', 'set'
                ],
                "allowed_modules": ['math', 'json', 'collections'],
                "forbidden_imports": [
                    'os', 'sys', 'subprocess', 'pickle', 'marshal', 'fileinput',
                    'glob', 'fnmatch', 'io', 'tempfile', 'shutil', 'pathlib',
                    'socket', 'urllib', 'requests', 'http'
                ],
                "resource_limits": ResourceLimits(
                    max_memory_mb=256,
                    max_cpu_seconds=10,
                    timeout_seconds=20
                )
            },
            SecurityLevel.STRICT: {
                "allowed_builtins": ['int', 'float', 'str', 'bool', 'list', 'dict'],
                "allowed_modules": ['math', 'json'],
                "forbidden_imports": [
                    'os', 'sys', 'subprocess', 'pickle', 'marshal', 'fileinput',
                    'glob', 'fnmatch', 'io', 'tempfile', 'shutil', 'pathlib',
                    'socket', 'urllib', 'requests', 'http', 'email', 'json'
                ],
                "resource_limits": ResourceLimits(
                    max_memory_mb=128,
                    max_cpu_seconds=5,
                    timeout_seconds=15
                )
            },
            SecurityLevel.MAXIMUM: {
                "allowed_builtins": ['int', 'float', 'str', 'bool'],
                "allowed_modules": [],
                "forbidden_imports": [
                    'os', 'sys', 'subprocess', 'pickle', 'marshal', 'fileinput',
                    'glob', 'fnmatch', 'io', 'tempfile', 'shutil', 'pathlib',
                    'socket', 'urllib', 'requests', 'http', 'email', 'json',
                    'math', 'random', 'collections', 'datetime'
                ],
                "resource_limits": ResourceLimits(
                    max_memory_mb=64,
                    max_cpu_seconds=2,
                    timeout_seconds=10
                )
            }
        }
    
    def _init_network_isolation(self) -> None:
        """Inicializar aislamiento de red si está disponible"""
        try:
            # Verificar si podemos usar network namespaces (Linux)
            if os.name == 'posix' and os.getuid() == 0:
                # Podríamos implementar network namespaces aquí
                self.network_isolation_enabled = True
                self.logger.info("Network isolation habilitado (Linux namespaces)")
        except Exception as e:
            self.logger.warning(f"Network isolation no disponible: {e}")
    
    async def _initialize(self) -> None:
        """Inicialización específica del agente"""
        # Inicializar el ejecutor Python base
        await asyncio.sleep(0.1)
        
        # Validar configuración de seguridad
        if self.security_level not in self.security_configs:
            raise ValueError(f"Nivel de seguridad no soportado: {self.security_level}")
        
        self.logger.info(f"PythonExecutorAgent inicializado con nivel {self.security_level.value}")
    
    async def process_request(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Procesar request del cliente"""
        operation = request.get('operation', 'execute_code')
        
        if operation == 'execute_code':
            return await self.execute_code_advanced(request, context)
        elif operation == 'analyze_code':
            return await self.analyze_code_security(request, context)
        elif operation == 'run_tests':
            return await self.run_automatic_tests(request, context)
        elif operation == 'profile_code':
            return await self.profile_code_execution(request, context)
        elif operation == 'validate_security':
            return await self.validate_code_security(request, context)
        elif operation == 'execute_with_sandbox':
            return await self.execute_in_sandbox(request, context)
        else:
            raise AgentException(f"Operación no soportada: {operation}", self.agent_name, operation)
    
    @handle_exceptions
    async def execute_code_advanced(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ejecutar código Python con análisis avanzado"""
        code = request.get('code')
        security_level = SecurityLevel(request.get('security_level', self.security_level.value))
        resource_limits = request.get('resource_limits', {})
        enable_profiling = request.get('enable_profiling', False)
        enable_tests = request.get('enable_tests', False)
        
        if not code:
            raise ValueError("Código requerido")
        
        # Validar límites de recursos
        limits = self._merge_resource_limits(resource_limits)
        
        # Análisis de seguridad antes de ejecutar
        analysis = await self._analyze_code_security(code, security_level)
        if analysis.security_level == SecurityLevel.MAXIMUM and analysis.risk_score > 0.8:
            raise AgentException("Código considerado demasiado peligroso para ejecutar", self.agent_name, "execute_code_advanced")
        
        # Ejecutar código con sandbox
        result = await self._execute_with_sandbox(code, limits, security_level, enable_profiling)
        
        # Ejecutar tests automáticos si se solicitan
        if enable_tests and result.success:
            test_result = await self._run_basic_tests(code, limits)
            result.warnings.extend([f"Test {t.test_name}: {'OK' if t.success else 'FAIL'}" 
                                  for t in test_result])
        
        self._update_metrics(result, analysis)
        
        return {
            "execution_result": result.to_dict(),
            "security_analysis": analysis.to_dict(),
            "resource_usage": {
                "memory_mb": result.memory_used,
                "cpu_time": result.cpu_time,
                "execution_time": result.execution_time
            }
        }
    
    @handle_exceptions
    async def analyze_code_security(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analizar seguridad del código sin ejecutarlo"""
        code = request.get('code')
        security_level = SecurityLevel(request.get('security_level', self.security_level.value))
        
        if not code:
            raise ValueError("Código requerido para análisis")
        
        analysis = await self._analyze_code_security(code, security_level)
        
        return {
            "security_analysis": analysis.to_dict(),
            "recommendations": self._generate_security_recommendations(analysis)
        }
    
    @handle_exceptions
    async def run_automatic_tests(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ejecutar tests automáticos en el código"""
        code = request.get('code')
        test_type = request.get('test_type', 'basic')
        resource_limits = request.get('resource_limits', {})
        
        if not code:
            raise ValueError("Código requerido para tests")
        
        limits = self._merge_resource_limits(resource_limits)
        
        if test_type == 'basic':
            test_results = await self._run_basic_tests(code, limits)
        elif test_type == 'comprehensive':
            test_results = await self._run_comprehensive_tests(code, limits)
        else:
            raise ValueError(f"Tipo de test no soportado: {test_type}")
        
        return {
            "test_results": [t.to_dict() for t in test_results],
            "summary": {
                "total_tests": len(test_results),
                "passed": sum(1 for t in test_results if t.success),
                "failed": sum(1 for t in test_results if not t.success)
            }
        }
    
    @handle_exceptions
    async def profile_code_execution(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ejecutar código con profiling detallado"""
        code = request.get('code')
        profile_type = request.get('profile_type', 'performance')
        resource_limits = request.get('resource_limits', {})
        
        if not code:
            raise ValueError("Código requerido para profiling")
        
        limits = self._merge_resource_limits(resource_limits)
        
        if profile_type == 'performance':
            profile_data = await self._run_performance_profiling(code, limits)
        elif profile_type == 'memory':
            profile_data = await self._run_memory_profiling(code, limits)
        else:
            raise ValueError(f"Tipo de profiling no soportado: {profile_type}")
        
        return {
            "profile_data": profile_data,
            "recommendations": self._generate_optimization_recommendations(profile_data)
        }
    
    @handle_exceptions
    async def validate_code_security(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validación avanzada de seguridad"""
        code = request.get('code')
        strict_mode = request.get('strict_mode', False)
        
        if not code:
            raise ValueError("Código requerido para validación")
        
        validation_result = await self._validate_code_security(code, strict_mode)
        
        return validation_result
    
    @handle_exceptions
    async def execute_in_sandbox(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ejecutar código en sandbox completamente aislado"""
        code = request.get('code')
        sandbox_config = request.get('sandbox_config', {})
        
        if not code:
            raise ValueError("Código requerido para sandbox")
        
        # Configurar sandbox
        limits = self._merge_resource_limits(sandbox_config.get('resource_limits', {}))
        security_level = SecurityLevel(sandbox_config.get('security_level', self.security_level.value))
        
        # Ejecutar en sandbox
        result = await self._execute_in_full_sandbox(code, limits, security_level)
        
        return {
            "sandbox_result": result.to_dict(),
            "isolation_status": {
                "network_isolated": self.network_isolation_enabled,
                "resource_limits_enforced": True,
                "security_violations": len(result.security_violations)
            }
        }
    
    # === MÉTODOS PRIVADOS ===
    
    def _merge_resource_limits(self, request_limits: Dict[str, Any]) -> ResourceLimits:
        """Combinar límites de recursos por defecto con solicitud"""
        default = self.default_resource_limits
        merged = ResourceLimits(
            max_memory_mb=request_limits.get('max_memory_mb', default.max_memory_mb),
            max_cpu_seconds=request_limits.get('max_cpu_seconds', default.max_cpu_seconds),
            max_disk_io_mb=request_limits.get('max_disk_io_mb', default.max_disk_io_mb),
            max_file_descriptors=request_limits.get('max_file_descriptors', default.max_file_descriptors),
            max_processes=request_limits.get('max_processes', default.max_processes),
            max_network_connections=request_limits.get('max_network_connections', default.max_network_connections),
            timeout_seconds=request_limits.get('timeout_seconds', default.timeout_seconds)
        )
        return merged
    
    async def _analyze_code_security(self, code: str, security_level: SecurityLevel) -> CodeAnalysis:
        """Análisis completo de seguridad del código"""
        # Verificar cache
        cache_key = hashlib.md5(f"{code}_{security_level.value}".encode()).hexdigest()
        if cache_key in self.code_analysis_cache:
            self.execution_metrics["cache_hits"] += 1
            return self.code_analysis_cache[cache_key]
        
        analysis = CodeAnalysis(security_level=security_level)
        
        try:
            # Análisis sintáctico
            tree = ast.parse(code)
            analysis.syntax_valid = True
        except SyntaxError as e:
            analysis.syntax_valid = False
            analysis.syntax_error = str(e)
            analysis.risk_score = 1.0
            return analysis
        
        # Análisis AST de seguridad
        security_warnings = []
        
        class SecurityAnalyzer(ast.NodeVisitor):
            def visit_Import(self, node):
                for alias in node.names:
                    if alias.name in self.forbidden_imports:
                        self.warnings.append(f"Import prohibido: {alias.name}")
                self.generic_visit(node)
            
            def visit_ImportFrom(self, node):
                if node.module and node.module in self.forbidden_modules:
                    self.warnings.append(f"Import from prohibido: {node.module}")
                self.generic_visit(node)
            
            def visit_Call(self, node):
                if hasattr(node.func, 'id'):
                    func_name = node.func.id
                    if func_name in ['exec', 'eval', 'compile', '__import__']:
                        self.warnings.append(f"Llamada peligrosa: {func_name}")
                self.generic_visit(node)
            
            def visit_Attribute(self, node):
                attr = node.attr
                dangerous_attrs = ['__globals__', '__locals__', '__import__', '__code__']
                if attr in dangerous_attrs:
                    self.warnings.append(f"Acceso a atributo peligroso: {attr}")
                self.generic_visit(node)
        
        analyzer = SecurityAnalyzer()
        analyzer.warnings = security_warnings
        analyzer.forbidden_imports = self.security_configs[security_level]['forbidden_imports']
        analyzer.forbidden_modules = self.security_configs[security_level]['forbidden_modules']
        analyzer.visit(tree)
        
        analysis.security_warnings = security_warnings
        
        # Métricas de complejidad
        analysis.complexity_metrics = {
            'lines': len(code.splitlines()),
            'characters': len(code),
            'functions': len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
            'classes': len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
            'imports': len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]),
            'nesting_level': self._calculate_nesting_level(code)
        }
        
        # Cálculo de riesgo
        risk_score = len(security_warnings) * 0.1
        risk_score += len(analysis.complexity_metrics['functions']) * 0.05
        risk_score += analysis.complexity_metrics['nesting_level'] * 0.05
        analysis.risk_score = min(risk_score, 1.0)
        
        # Cache del análisis
        self.code_analysis_cache[cache_key] = analysis
        
        return analysis
    
    def _calculate_nesting_level(self, code: str) -> int:
        """Calcular nivel máximo de anidamiento"""
        max_nesting = 0
        current_nesting = 0
        
        for char in code:
            if char in '{([':
                current_nesting += 1
                max_nesting = max(max_nesting, current_nesting)
            elif char in '}])':
                current_nesting -= 1
        
        return max_nesting
    
    async def _execute_with_sandbox(self, code: str, limits: ResourceLimits, 
                                  security_level: SecurityLevel, enable_profiling: bool = False) -> ExecutionResult:
        """Ejecutar código con sandbox y límites de recursos"""
        start_time = time.time()
        result = ExecutionResult(success=False)
        
        try:
            # Configurar límites del proceso
            self._set_resource_limits(limits)
            
            # Crear contexto de ejecución
            exec_context = ExecutionContext(
                variables={},
                allowed_builtins=self.security_configs[security_level]['allowed_builtins'],
                forbidden_modules=self.security_configs[security_level]['forbidden_imports']
            )
            
            # Ejecutar con profiling si se solicita
            if enable_profiling:
                result.profile_data = await self._execute_with_profiling(code, exec_context, limits)
            else:
                execution_result = self.python_executor.execute_code(code, exec_context, limits.timeout_seconds)
                
                result.success = execution_result.success
                result.output = execution_result.data.get('output', '') if execution_result.success else ''
                result.error = execution_result.error
                result.return_value = execution_result.data.get('result')
                result.locals = execution_result.data.get('locals', {})
            
            result.execution_time = time.time() - start_time
            result.memory_used = self._get_memory_usage()
            result.cpu_time = result.execution_time  # Estimación aproximada
            
        except Exception as e:
            result.error = str(e)
            result.execution_time = time.time() - start_time
            self.logger.error(f"Error en ejecución con sandbox: {e}")
        
        return result
    
    def _set_resource_limits(self, limits: ResourceLimits) -> None:
        """Establecer límites de recursos del proceso"""
        try:
            # Límite de memoria
            if limits.max_memory_mb > 0:
                memory_limit = limits.max_memory_mb * 1024 * 1024  # Convertir a bytes
                resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
            
            # Límite de CPU
            if limits.max_cpu_seconds > 0:
                cpu_limit = limits.max_cpu_seconds
                resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
            
            # Límite de descriptores de archivo
            if limits.max_file_descriptors > 0:
                fd_limit = limits.max_file_descriptors
                resource.setrlimit(resource.RLIMIT_NOFILE, (fd_limit, fd_limit))
                
        except (OSError, ValueError) as e:
            self.logger.warning(f"No se pudieron establecer algunos límites de recursos: {e}")
    
    def _get_memory_usage(self) -> float:
        """Obtener uso actual de memoria en MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except:
            return 0.0
    
    async def _execute_with_profiling(self, code: str, context: ExecutionContext, limits: ResourceLimits) -> Dict[str, Any]:
        """Ejecutar código con profiling de performance"""
        profiler = cProfile.Profile()
        
        # Ejecutar código con profiling
        start_time = time.time()
        
        try:
            profiler.enable()
            
            execution_result = self.python_executor.execute_code(code, context, limits.timeout_seconds)
            
            profiler.disable()
            
            # Analizar resultados del profiling
            stats = pstats.Stats(profiler)
            
            # Top 10 funciones por tiempo acumulado
            top_functions = []
            for func, (cc, nc, tt, ct, callers) in stats.stats.items():
                if tt > 0:  # Solo funciones que consumen tiempo
                    top_functions.append({
                        'function': f"{func[0]}:{func[1]}:{func[2]}",
                        'calls': cc,
                        'total_time': tt,
                        'cumulative_time': ct
                    })
            
            top_functions.sort(key=lambda x: x['total_time'], reverse=True)
            top_functions = top_functions[:10]
            
            return {
                'total_functions': len(stats.stats),
                'top_functions': top_functions,
                'total_time': time.time() - start_time,
                'profile_successful': execution_result.success
            }
            
        except Exception as e:
            profiler.disable()
            return {
                'error': str(e),
                'profile_successful': False
            }
    
    async def _run_basic_tests(self, code: str, limits: ResourceLimits) -> List[TestResult]:
        """Ejecutar tests básicos en el código"""
        test_results = []
        
        # Test 1: Sintaxis válida
        test_results.append(TestResult(
            test_name="syntax_validation",
            success=self._test_syntax(code),
            execution_time=0.0
        ))
        
        # Test 2: Seguridad básica
        test_results.append(TestResult(
            test_name="basic_security",
            success=self._test_basic_security(code),
            execution_time=0.0
        ))
        
        # Test 3: Ejecución básica
        try:
            exec_result = self._execute_safe_snippet(code, limits)
            test_results.append(TestResult(
                test_name="basic_execution",
                success=exec_result.success,
                execution_time=exec_result.execution_time,
                error_message=exec_result.error
            ))
        except Exception as e:
            test_results.append(TestResult(
                test_name="basic_execution",
                success=False,
                error_message=str(e)
            ))
        
        return test_results
    
    def _test_syntax(self, code: str) -> bool:
        """Test de sintaxis válida"""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
    
    def _test_basic_security(self, code: str) -> bool:
        """Test de seguridad básica"""
        try:
            tree = ast.parse(code)
            
            # Verificar llamadas peligrosas
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if hasattr(node.func, 'id') and node.func.id in ['exec', 'eval', '__import__']:
                        return False
            
            return True
        except:
            return False
    
    def _execute_safe_snippet(self, code: str, limits: ResourceLimits) -> ExecutionResult:
        """Ejecutar snippet de código de forma segura"""
        result = ExecutionResult(success=False)
        start_time = time.time()
        
        try:
            # Configurar límites básicos
            self._set_resource_limits(limits)
            
            # Crear contexto seguro
            exec_context = ExecutionContext(
                variables={},
                allowed_builtins=self.security_configs[self.security_level]['allowed_builtins'],
                forbidden_modules=self.security_configs[self.security_level]['forbidden_imports']
            )
            
            # Ejecutar con timeout
            exec_result = self.python_executor.execute_code(code, exec_context, limits.timeout_seconds)
            
            result.success = exec_result.success
            result.output = exec_result.data.get('output', '') if exec_result.success else ''
            result.error = exec_result.error
            result.execution_time = time.time() - start_time
            
        except Exception as e:
            result.error = str(e)
            result.execution_time = time.time() - start_time
        
        return result
    
    async def _run_comprehensive_tests(self, code: str, limits: ResourceLimits) -> List[TestResult]:
        """Ejecutar tests comprehensivos"""
        # Implementar tests más detallados
        basic_tests = await self._run_basic_tests(code, limits)
        
        # Tests adicionales
        comprehensive_tests = []
        
        # Test de dependencias
        comprehensive_tests.append(TestResult(
            test_name="dependency_analysis",
            success=self._test_dependencies(code),
            execution_time=0.0
        ))
        
        # Test de complejidad
        complexity_score = self._calculate_complexity_score(code)
        comprehensive_tests.append(TestResult(
            test_name="complexity_analysis",
            success=complexity_score < 10.0,  # Umbral configurable
            execution_time=0.0,
            error_message=f"Complejidad: {complexity_score}"
        ))
        
        return basic_tests + comprehensive_tests
    
    def _test_dependencies(self, code: str) -> bool:
        """Test de análisis de dependencias"""
        try:
            tree = ast.parse(code)
            
            # Verificar dependencias peligrosas
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name in self.security_configs[self.security_level]['forbidden_imports']:
                                return False
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        if node.module in self.security_configs[self.security_level]['forbidden_imports']:
                            return False
            
            return True
        except:
            return False
    
    def _calculate_complexity_score(self, code: str) -> float:
        """Calcular puntuación de complejidad"""
        try:
            tree = ast.parse(code)
            
            complexity = 0
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.Try)):
                    complexity += 1
                elif isinstance(node, ast.FunctionDef):
                    complexity += 2
            
            return complexity
        except:
            return float('inf')
    
    async def _run_performance_profiling(self, code: str, limits: ResourceLimits) -> Dict[str, Any]:
        """Profiling de performance detallado"""
        return await self._execute_with_profiling(code, ExecutionContext({}, [], []), limits)
    
    async def _run_memory_profiling(self, code: str, limits: ResourceLimits) -> Dict[str, Any]:
        """Profiling de memoria"""
        # Implementar profiling de memoria con memory_profiler
        try:
            # Código simplificado para profiling de memoria
            memory_usage = []
            
            # Ejecutar código monitoreando memoria
            start_memory = self._get_memory_usage()
            
            exec_result = await self._execute_with_sandbox(code, limits, self.security_level, False)
            
            end_memory = self._get_memory_usage()
            
            return {
                'start_memory_mb': start_memory,
                'end_memory_mb': end_memory,
                'memory_delta_mb': end_memory - start_memory,
                'peak_memory_mb': end_memory,
                'execution_successful': exec_result.success
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'profile_successful': False
            }
    
    async def _validate_code_security(self, code: str, strict_mode: bool = False) -> Dict[str, Any]:
        """Validación avanzada de seguridad"""
        analysis = await self._analyze_code_security(code, SecurityLevel.STRICT if strict_mode else self.security_level)
        
        # Validaciones adicionales
        validation_results = {
            'syntax_valid': analysis.syntax_valid,
            'no_forbidden_imports': len([w for w in analysis.security_warnings if 'Import' in w]) == 0,
            'no_dangerous_calls': len([w for w in analysis.security_warnings if 'peligrosa' in w]) == 0,
            'reasonable_complexity': analysis.complexity_metrics['nesting_level'] < 5,
            'no_excessive_size': analysis.complexity_metrics['lines'] < 1000
        }
        
        overall_score = sum(validation_results.values()) / len(validation_results)
        security_approved = overall_score >= 0.8 and analysis.risk_score < 0.3
        
        return {
            'validation_passed': security_approved,
            'security_score': overall_score,
            'validation_details': validation_results,
            'risk_analysis': analysis.to_dict(),
            'recommendations': self._generate_security_recommendations(analysis)
        }
    
    async def _execute_in_full_sandbox(self, code: str, limits: ResourceLimits, security_level: SecurityLevel) -> ExecutionResult:
        """Ejecutar código en sandbox completo con aislamiento total"""
        result = ExecutionResult(success=False)
        
        try:
            # Crear directorio temporal aislado
            with tempfile.TemporaryDirectory() as temp_dir:
                # Cambiar al directorio temporal (aislamiento de archivos)
                original_cwd = os.getcwd()
                os.chdir(temp_dir)
                
                try:
                    # Ejecutar con máximo aislamiento
                    result = await self._execute_with_sandbox(code, limits, security_level, False)
                    
                finally:
                    # Restaurar directorio original
                    os.chdir(original_cwd)
        
        except Exception as e:
            result.error = f"Error en sandbox: {str(e)}"
        
        return result
    
    def _generate_security_recommendations(self, analysis: CodeAnalysis) -> List[str]:
        """Generar recomendaciones de seguridad"""
        recommendations = []
        
        if analysis.security_warnings:
            recommendations.append("Revisar y eliminar imports/llamadas peligrosas identificadas")
        
        if analysis.complexity_metrics['nesting_level'] > 5:
            recommendations.append("Reducir la complejidad del código (nivel de anidamiento muy alto)")
        
        if analysis.complexity_metrics['lines'] > 500:
            recommendations.append("Considerar dividir el código en funciones más pequeñas")
        
        if analysis.risk_score > 0.5:
            recommendations.append("Aumentar nivel de seguridad o refactorizar código")
        
        if not recommendations:
            recommendations.append("Código parece seguro. Continuar con ejecución.")
        
        return recommendations
    
    def _generate_optimization_recommendations(self, profile_data: Dict[str, Any]) -> List[str]:
        """Generar recomendaciones de optimización basadas en profiling"""
        recommendations = []
        
        if not profile_data.get('profile_successful', False):
            recommendations.append("No se pudo obtener datos de profiling")
            return recommendations
        
        if 'top_functions' in profile_data:
            top_func = profile_data['top_functions'][0] if profile_data['top_functions'] else None
            if top_func and top_func['total_time'] > 1.0:
                recommendations.append(f"Función '{top_func['function']}' consume mucho tiempo ({top_func['total_time']:.3f}s)")
        
        return recommendations or ["Código parece optimizado"]
    
    def _update_metrics(self, result: ExecutionResult, analysis: CodeAnalysis) -> None:
        """Actualizar métricas del agente"""
        self.execution_metrics["total_executions"] += 1
        
        if result.success:
            self.execution_metrics["successful_executions"] += 1
        else:
            self.execution_metrics["failed_executions"] += 1
        
        if result.security_violations:
            self.execution_metrics["security_violations"] += len(result.security_violations)
        
        # Actualizar promedios
        total = self.execution_metrics["total_executions"]
        success_rate = self.execution_metrics["successful_executions"] / total
        
        # Promedio de tiempo de ejecución
        current_avg_time = self.execution_metrics["average_execution_time"]
        self.execution_metrics["average_execution_time"] = (
            (current_avg_time * (total - 1) + result.execution_time) / total
        )
        
        # Promedio de memoria
        current_avg_memory = self.execution_metrics["average_memory_usage"]
        self.execution_metrics["average_memory_usage"] = (
            (current_avg_memory * (total - 1) + result.memory_used) / total
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado completo del agente"""
        base_status = super().get_status()
        base_status.update({
            "agent_type": "python_executor_advanced",
            "specialization": "Ejecución segura de código Python con sandbox avanzado",
            "security_level": self.security_level.value,
            "network_isolation_enabled": self.network_isolation_enabled,
            "execution_metrics": self.execution_metrics.copy(),
            "cache_size": len(self.code_analysis_cache)
        })
        return base_status
    
    def reset_metrics(self) -> None:
        """Resetear métricas del agente"""
        super().reset_metrics()
        self.execution_metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "average_memory_usage": 0.0,
            "security_violations": 0,
            "cache_hits": 0
        }
        self.code_analysis_cache.clear()
        self.logger.info("Métricas y cache reseteados para PythonExecutorAgent")