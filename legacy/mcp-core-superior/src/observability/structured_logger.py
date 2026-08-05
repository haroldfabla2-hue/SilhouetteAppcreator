"""
Sistema de Structured Logging con Formato JSON para MCP Core Superior

Proporciona capacidades avanzadas de observabilidad para el ecosistema MCP incluyendo:
- Logging estructurado con formato JSON
- Correlation IDs y distributed tracing
- Métricas de performance
- Audit trails para compliance
- Filtrado de datos sensibles
- Integración con ELK stack y servicios cloud
"""

import json
import logging
import sys
import time
import uuid
import threading
import traceback
import os
import gzip
import shutil
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Callable, Union, Set
from enum import Enum
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
import queue
import re
from pathlib import Path


class LogLevel(Enum):
    """Niveles de log con prioridades"""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40
    CRITICAL = 50
    
    def __lt__(self, other):
        return self.value < other.value
    
    def __le__(self, other):
        return self.value <= other.value
    
    def __gt__(self, other):
        return self.value > other.value
    
    def __ge__(self, other):
        return self.value >= other.value


@dataclass
class LogContext:
    """Contexto de log con campos estandarizados"""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    level: str = "INFO"
    logger: str = "mcp"
    message: str = ""
    component: str = ""
    agent_id: str = ""
    correlation_id: str = ""
    trace_id: str = ""
    span_id: str = ""
    operation: str = ""
    duration_ms: Optional[float] = None
    status: str = "success"
    error_code: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    additional_fields: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el contexto a diccionario"""
        data = asdict(self)
        # Limpiar campos None
        return {k: v for k, v in data.items() if v is not None}


class SensitiveDataFilter:
    """Filtro para datos sensibles"""
    
    # Patrones de datos sensibles
    SENSITIVE_PATTERNS = {
        'password': r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']([^"\']+)["\']',
        'api_key': r'(?i)(api[_\s]?key|apikey|secret[_\s]?key)\s*[=:]\s*["\']([^"\']+)["\']',
        'token': r'(?i)(token|auth[_\s]?token|access[_\s]?token)\s*[=:]\s*["\']([^"\']+)["\']',
        'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    }
    
    def __init__(self):
        self.compiled_patterns = {
            name: re.compile(pattern, re.IGNORECASE) 
            for name, pattern in self.SENSITIVE_PATTERNS.items()
        }
    
    def filter_text(self, text: str, replacement: str = "***REDACTED***") -> str:
        """Filtra datos sensibles del texto"""
        filtered_text = text
        for name, pattern in self.compiled_patterns.items():
            filtered_text = pattern.sub(replacement, filtered_text)
        return filtered_text
    
    def filter_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filtra datos sensibles de un diccionario"""
        if not isinstance(data, dict):
            return data
        
        filtered = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Verificar si la clave es sensible
                if any(sensitive in key.lower() for sensitive in ['password', 'token', 'secret', 'key', 'auth']):
                    filtered[key] = "***REDACTED***"
                else:
                    filtered[key] = self.filter_text(value)
            elif isinstance(value, dict):
                filtered[key] = self.filter_dict(value)
            elif isinstance(value, list):
                filtered[key] = [self.filter_dict(item) if isinstance(item, dict) 
                               else self.filter_text(str(item)) if isinstance(item, str) 
                               else item for item in value]
            else:
                filtered[key] = value
        return filtered


class CorrelationContext:
    """Manejador de context correlation IDs"""
    
    _local = threading.local()
    
    @classmethod
    def get_correlation_id(cls) -> str:
        """Obtiene correlation ID del contexto actual"""
        return getattr(cls._local, 'correlation_id', '')
    
    @classmethod
    def set_correlation_id(cls, correlation_id: str):
        """Establece correlation ID en el contexto actual"""
        cls._local.correlation_id = correlation_id
    
    @classmethod
    def generate_correlation_id(cls) -> str:
        """Genera un nuevo correlation ID"""
        return f"mcp-{uuid.uuid4().hex[:16]}"
    
    @contextmanager
    def correlation_context(self, correlation_id: Optional[str] = None):
        """Context manager para correlation IDs"""
        if correlation_id is None:
            correlation_id = self.generate_correlation_id()
        
        old_correlation_id = self.get_correlation_id()
        self.set_correlation_id(correlation_id)
        
        try:
            yield correlation_id
        finally:
            self.set_correlation_id(old_correlation_id)


@dataclass
class PerformanceMetrics:
    """Métricas de performance"""
    operation: str = ""
    duration_ms: float = 0.0
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    io_ops: Optional[int] = None
    database_queries: Optional[int] = None
    external_calls: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PerformanceLogger:
    """Logger específico para métricas de performance"""
    
    def __init__(self, structured_logger: 'StructuredLogger'):
        self.logger = structured_logger
    
    def log_operation(self, operation: str, func: Callable, *args, **kwargs):
        """Log con métricas de performance"""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            result = func(*args, **kwargs)
            status = "success"
            error = None
        except Exception as e:
            result = None
            status = "error"
            error = str(e)
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            end_memory = self._get_memory_usage()
            
            metrics = PerformanceMetrics(
                operation=operation,
                duration_ms=duration_ms,
                memory_usage=end_memory - start_memory if start_memory else None
            )
            
            self.logger.info(
                f"Operation '{operation}' completed",
                operation=operation,
                duration_ms=duration_ms,
                status=status,
                error=error,
                performance_metrics=metrics.to_dict()
            )
        
        return result
    
    def _get_memory_usage(self) -> Optional[float]:
        """Obtiene uso actual de memoria en MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return None


class AuditLogger:
    """Logger específico para audit trails"""
    
    def __init__(self, structured_logger: 'StructuredLogger'):
        self.logger = structured_logger
    
    def log_access(self, user_id: str, resource: str, action: str, 
                   status: str = "success", details: Optional[Dict] = None):
        """Log de acceso a recursos"""
        self.logger.info(
            f"Access: {action} on {resource}",
            audit_type="access",
            user_id=user_id,
            resource=resource,
            action=action,
            status=status,
            details=details or {}
        )
    
    def log_data_change(self, user_id: str, resource: str, action: str, 
                       old_value: Optional[Any] = None, new_value: Optional[Any] = None):
        """Log de cambios de datos"""
        self.logger.info(
            f"Data change: {action} on {resource}",
            audit_type="data_change",
            user_id=user_id,
            resource=resource,
            action=action,
            old_value=old_value,
            new_value=new_value
        )
    
    def log_system_event(self, event_type: str, description: str, 
                        user_id: Optional[str] = None, details: Optional[Dict] = None):
        """Log de eventos del sistema"""
        self.logger.info(
            f"System event: {description}",
            audit_type="system_event",
            event_type=event_type,
            user_id=user_id,
            description=description,
            details=details or {}
        )


class LogAggregator:
    """Agregador de logs para envío en lotes"""
    
    def __init__(self, batch_size: int = 100, flush_interval: int = 30):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.logs_buffer: deque = deque(maxlen=10000)
        self.lock = threading.Lock()
        self.flusher_thread = threading.Thread(target=self._flush_worker, daemon=True)
        self.flusher_thread.start()
    
    def add_log(self, log_entry: Dict[str, Any]):
        """Añade log al buffer"""
        with self.lock:
            self.logs_buffer.append(log_entry)
            if len(self.logs_buffer) >= self.batch_size:
                self._flush_logs()
    
    def _flush_worker(self):
        """Worker thread para flush periódico"""
        while True:
            time.sleep(self.flush_interval)
            with self.lock:
                if self.logs_buffer:
                    self._flush_logs()
    
    def _flush_logs(self):
        """Flush logs a destinos configurados"""
        logs_to_send = list(self.logs_buffer)
        self.logs_buffer.clear()
        
        # Enviar a todos los destinos configurados
        for shipper in getattr(self, 'shippers', []):
            try:
                shipper.ship_logs(logs_to_send)
            except Exception as e:
                print(f"Error sending logs to {shipper}: {e}", file=sys.stderr)
    
    def add_shipper(self, shipper):
        """Añade shipper de logs"""
        if not hasattr(self, 'shippers'):
            self.shippers = []
        self.shippers.append(shipper)


class ELKShipper:
    """Shipper para ELK Stack (Elasticsearch, Logstash, Kibana)"""
    
    def __init__(self, elasticsearch_url: str, index_prefix: str = "mcp-logs-"):
        self.elasticsearch_url = elasticsearch_url
        self.index_prefix = index_prefix
        self.session = None
    
    def ship_logs(self, logs: List[Dict[str, Any]]):
        """Envía logs a Elasticsearch"""
        try:
            import requests
            if not self.session:
                self.session = requests.Session()
            
            index_name = f"{self.index_prefix}{datetime.now().strftime('%Y.%m.%d')}"
            
            bulk_data = []
            for log_entry in logs:
                bulk_data.append(json.dumps({"index": {"_index": index_name}}))
                bulk_data.append(json.dumps(log_entry))
            
            response = self.session.post(
                f"{self.elasticsearch_url}/_bulk",
                data='\n'.join(bulk_data) + '\n',
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code != 200:
                raise Exception(f"ELK ship failed: {response.status_code}")
                
        except ImportError:
            print("requests library not available for ELK shipping", file=sys.stderr)
        except Exception as e:
            print(f"Error shipping to ELK: {e}", file=sys.stderr)


class CloudLogShipper:
    """Shipper para servicios de cloud logging"""
    
    def __init__(self, provider: str, config: Dict[str, Any]):
        self.provider = provider.lower()
        self.config = config
        
        if self.provider == 'aws':
            self._init_aws()
        elif self.provider == 'gcp':
            self._init_gcp()
        elif self.provider == 'azure':
            self._init_azure()
    
    def _init_aws(self):
        """Inicializar AWS CloudWatch Logs"""
        try:
            import boto3
            self.client = boto3.client('logs', **self.config)
        except ImportError:
            print("boto3 library not available for AWS logging", file=sys.stderr)
    
    def _init_gcp(self):
        """Inicializar Google Cloud Logging"""
        try:
            from google.cloud import logging as gcp_logging
            self.client = gcp_logging.Client(**self.config)
        except ImportError:
            print("google-cloud-logging library not available for GCP logging", file=sys.stderr)
    
    def _init_azure(self):
        """Inicializar Azure Monitor Logs"""
        try:
            from azure.mgmt.monitor import MonitorManagementClient
            from azure.identity import DefaultAzureCredential
            self.client = MonitorManagementClient(
                DefaultAzureCredential(), 
                self.config.get('subscription_id')
            )
        except ImportError:
            print("azure libraries not available for Azure logging", file=sys.stderr)
    
    def ship_logs(self, logs: List[Dict[str, Any]]):
        """Envía logs al servicio cloud"""
        try:
            if self.provider == 'aws':
                self._ship_aws(logs)
            elif self.provider == 'gcp':
                self._ship_gcp(logs)
            elif self.provider == 'azure':
                self._ship_azure(logs)
        except Exception as e:
            print(f"Error shipping to {self.provider}: {e}", file=sys.stderr)
    
    def _ship_aws(self, logs: List[Dict[str, Any]]):
        """Enviar a AWS CloudWatch"""
        if hasattr(self, 'client'):
            log_group = self.config.get('log_group', 'mcp-logs')
            log_stream = self.config.get('log_stream', f"mcp-{int(time.time())}")
            
            events = [{
                'timestamp': int(time.time() * 1000),
                'message': json.dumps(log_entry)
            } for log_entry in logs]
            
            self.client.put_log_events(
                logGroupName=log_group,
                logStreamName=log_stream,
                logEvents=events
            )
    
    def _ship_gcp(self, logs: List[Dict[str, Any]]):
        """Enviar a Google Cloud Logging"""
        if hasattr(self, 'client'):
            logger = self.client.logger(self.config.get('log_name', 'mcp-logs'))
            for log_entry in logs:
                logger.log_struct(log_entry)
    
    def _ship_azure(self, logs: List[Dict[str, Any]]):
        """Enviar a Azure Monitor"""
        # Implementación básica para Azure
        # Se puede expandir con más detalles según necesidades
        pass


class LogRotator:
    """Manejador de rotación y retención de logs"""
    
    def __init__(self, log_dir: str, max_size_mb: int = 100, 
                 max_files: int = 10, compression: bool = True):
        self.log_dir = Path(log_dir)
        self.max_size_mb = max_size_mb
        self.max_files = max_files
        self.compression = compression
        self.log_files: Dict[str, Path] = {}
    
    def should_rotate(self, log_file: Path) -> bool:
        """Verifica si el archivo debe rotar"""
        if not log_file.exists():
            return False
        size_mb = log_file.stat().st_size / (1024 * 1024)
        return size_mb >= self.max_size_mb
    
    def rotate_log(self, log_file: Path):
        """Rota un archivo de log"""
        if not log_file.exists():
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Comprimir archivo actual
        if self.compression:
            compressed_file = log_file.with_suffix(f'.{timestamp}.gz')
            with open(log_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            rotated_file = log_file.with_suffix(f'.{timestamp}')
            log_file.rename(rotated_file)
        
        # Limpiar archivos antiguos
        self._cleanup_old_files()
    
    def _cleanup_old_files(self):
        """Limpia archivos de log antiguos"""
        pattern = f"*.{'gz' if self.compression else '*'}"
        files = sorted(self.log_dir.glob(pattern), 
                      key=lambda x: x.stat().st_mtime, reverse=True)
        
        for file_path in files[self.max_files:]:
            try:
                file_path.unlink()
            except Exception as e:
                print(f"Error deleting old log file {file_path}: {e}", file=sys.stderr)


class StructuredLogger:
    """Logger principal con formato JSON estructurado"""
    
    def __init__(self, name: str = "mcp", level: LogLevel = LogLevel.INFO,
                 log_dir: Optional[str] = None, enable_console: bool = True,
                 enable_file: bool = True, enable_elk: bool = False,
                 elk_config: Optional[Dict] = None, enable_cloud: bool = False,
                 cloud_config: Optional[Dict] = None):
        
        self.name = name
        self.level = level
        self.log_dir = log_dir
        self.sensitive_filter = SensitiveDataFilter()
        self.correlation_manager = CorrelationContext()
        
        # Configurar componentes
        self.performance_logger = PerformanceLogger(self)
        self.audit_logger = AuditLogger(self)
        self.log_aggregator = LogAggregator()
        
        # Configurar rotador de logs
        if log_dir and enable_file:
            self.log_rotator = LogRotator(log_dir)
            os.makedirs(log_dir, exist_ok=True)
        else:
            self.log_rotator = None
        
        # Configurar shippers
        if enable_elk and elk_config:
            elk_shipper = ELKShipper(**elk_config)
            self.log_aggregator.add_shipper(elk_shipper)
        
        if enable_cloud and cloud_config:
            cloud_shipper = CloudLogShipper(**cloud_config)
            self.log_aggregator.add_shipper(cloud_shipper)
        
        # Configurar handlers
        self.handlers = []
        if enable_console:
            self.handlers.append(self._setup_console_handler())
        if log_dir and enable_file:
            self.handlers.append(self._setup_file_handler())
    
    def _setup_console_handler(self) -> logging.Handler:
        """Configura handler de consola"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.level.value)
        return handler
    
    def _setup_file_handler(self) -> Optional[logging.Handler]:
        """Configura handler de archivo"""
        if not self.log_dir:
            return None
        
        log_file = Path(self.log_dir) / f"{self.name}.log"
        handler = logging.FileHandler(log_file)
        handler.setLevel(self.level.value)
        return handler
    
    def _create_log_entry(self, level: LogLevel, message: str, 
                         extra_fields: Optional[Dict] = None) -> LogContext:
        """Crea entrada de log estructurada"""
        extra_fields = extra_fields or {}
        
        # Filtrar datos sensibles
        message = self.sensitive_filter.filter_text(message)
        
        # Crear contexto de log
        context = LogContext(
            level=level.name,
            logger=self.name,
            message=message,
            correlation_id=self.correlation_manager.get_correlation_id(),
            **extra_fields
        )
        
        return context
    
    def _format_log_entry(self, context: LogContext) -> str:
        """Formatea entrada de log como JSON"""
        try:
            # Filtrar campos sensibles del contexto
            filtered_context = self.sensitive_filter.filter_dict(context.to_dict())
            return json.dumps(filtered_context, ensure_ascii=False, separators=(',', ':'))
        except Exception as e:
            # Fallback en caso de error de serialización
            fallback = {
                "timestamp": context.timestamp,
                "level": context.level,
                "logger": context.logger,
                "message": "Error serializing log entry",
                "error": str(e)
            }
            return json.dumps(fallback)
    
    def _emit_log(self, context: LogContext):
        """Emite log a todos los handlers"""
        formatted_entry = self._format_log_entry(context)
        
        # Enviar a handlers locales
        for handler in self.handlers:
            if hasattr(handler, 'level') and handler.level <= getattr(LogLevel, context.level):
                handler.emit(formatted_entry)
        
        # Enviar a agregador para shipping remoto
        self.log_aggregator.add_log(context.to_dict())
        
        # Verificar rotación de logs
        if self.log_rotator:
            for handler in self.handlers:
                if isinstance(handler, logging.FileHandler):
                    self.log_rotator.rotate_log(Path(handler.baseFilename))
    
    def trace(self, message: str, **extra_fields):
        """Log nivel TRACE"""
        context = self._create_log_entry(LogLevel.TRACE, message, extra_fields)
        self._emit_log(context)
    
    def debug(self, message: str, **extra_fields):
        """Log nivel DEBUG"""
        context = self._create_log_entry(LogLevel.DEBUG, message, extra_fields)
        self._emit_log(context)
    
    def info(self, message: str, **extra_fields):
        """Log nivel INFO"""
        context = self._create_log_entry(LogLevel.INFO, message, extra_fields)
        self._emit_log(context)
    
    def warn(self, message: str, **extra_fields):
        """Log nivel WARN"""
        context = self._create_log_entry(LogLevel.WARN, message, extra_fields)
        self._emit_log(context)
    
    def error(self, message: str, exception: Optional[Exception] = None, **extra_fields):
        """Log nivel ERROR"""
        extra_fields = extra_fields.copy()
        
        if exception:
            extra_fields.update({
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "stack_trace": traceback.format_exc()
            })
        
        context = self._create_log_entry(LogLevel.ERROR, message, extra_fields)
        self._emit_log(context)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **extra_fields):
        """Log nivel CRITICAL"""
        extra_fields = extra_fields.copy()
        
        if exception:
            extra_fields.update({
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "stack_trace": traceback.format_exc()
            })
        
        context = self._create_log_entry(LogLevel.CRITICAL, message, extra_fields)
        self._emit_log(context)
    
    @contextmanager
    def operation_context(self, operation: str, **extra_fields):
        """Context manager para operaciones con logging automático"""
        start_time = time.time()
        correlation_id = self.correlation_manager.generate_correlation_id()
        
        with self.correlation_manager.correlation_context(correlation_id):
            self.info(f"Starting operation: {operation}", 
                     operation=operation, **extra_fields)
            
            try:
                yield correlation_id
                duration_ms = (time.time() - start_time) * 1000
                self.info(f"Operation completed: {operation}", 
                         operation=operation, duration_ms=duration_ms, **extra_fields)
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self.error(f"Operation failed: {operation}", exception=e,
                          operation=operation, duration_ms=duration_ms, **extra_fields)
                raise
    
    def set_level(self, level: LogLevel):
        """Cambia nivel de log dinámicamente"""
        self.level = level
        for handler in self.handlers:
            handler.setLevel(level.value)
    
    def get_performance_logger(self) -> PerformanceLogger:
        """Obtiene logger de performance"""
        return self.performance_logger
    
    def get_audit_logger(self) -> AuditLogger:
        """Obtiene logger de audit"""
        return self.audit_logger


# Factory function para crear logger configurado
def create_mcp_logger(component: str = "mcp", 
                     level: LogLevel = LogLevel.INFO,
                     config: Optional[Dict] = None) -> StructuredLogger:
    """
    Factory function para crear logger MCP configurado
    
    Args:
        component: Nombre del componente/agente MCP
        level: Nivel de log
        config: Configuración adicional
    
    Returns:
        StructuredLogger configurado
    """
    config = config or {}
    
    return StructuredLogger(
        name=f"mcp.{component}",
        level=level,
        log_dir=config.get('log_dir'),
        enable_console=config.get('enable_console', True),
        enable_file=config.get('enable_file', True),
        enable_elk=config.get('enable_elk', False),
        elk_config=config.get('elk_config'),
        enable_cloud=config.get('enable_cloud', False),
        cloud_config=config.get('cloud_config')
    )


# Configuración por defecto para diferentes agentes MCP
AGENT_LOGGERS = {
    'database_operations': lambda: create_mcp_logger('database_operations', 
                                                   LogLevel.DEBUG),
    'file_processing': lambda: create_mcp_logger('file_processing', 
                                                LogLevel.INFO),
    'git_operations': lambda: create_mcp_logger('git_operations', 
                                               LogLevel.INFO),
    'multiagent_orchestrator': lambda: create_mcp_logger('multiagent_orchestrator', 
                                                        LogLevel.DEBUG),
    'python_executor': lambda: create_mcp_logger('python_executor', 
                                                LogLevel.DEBUG),
    'reasoner': lambda: create_mcp_logger('reasoner', 
                                         LogLevel.INFO),
    'search_engine': lambda: create_mcp_logger('search_engine', 
                                              LogLevel.INFO),
    'verifier': lambda: create_mcp_logger('verifier', 
                                         LogLevel.INFO),
    'web_scraping': lambda: create_mcp_logger('web_scraping', 
                                             LogLevel.INFO),
    'executor_wrapper': lambda: create_mcp_logger('executor_wrapper', 
                                                 LogLevel.DEBUG),
    'planner_wrapper': lambda: create_mcp_logger('planner_wrapper', 
                                                LogLevel.DEBUG),
    'memory_manager': lambda: create_mcp_logger('memory_manager', 
                                               LogLevel.INFO)
}


def get_agent_logger(agent_name: str) -> StructuredLogger:
    """
    Obtiene logger configurado para agente específico
    
    Args:
        agent_name: Nombre del agente
    
    Returns:
        StructuredLogger configurado para el agente
    """
    if agent_name in AGENT_LOGGERS:
        return AGENT_LOGGERS[agent_name]()
    
    # Logger por defecto si no se encuentra específico
    return create_mcp_logger(agent_name)


# Decorador para logging automático de funciones
def log_operation(operation_name: Optional[str] = None, 
                 level: LogLevel = LogLevel.INFO):
    """
    Decorador para logging automático de funciones
    
    Args:
        operation_name: Nombre de la operación (usa nombre de función si no se proporciona)
        level: Nivel de log
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__name__}"
            
            # Obtener logger del contexto global o crear uno por defecto
            logger = globals().get('current_logger', create_mcp_logger(func.__module__))
            
            with logger.operation_context(op_name):
                try:
                    result = func(*args, **kwargs)
                    logger.log(op_name, f"Function {func.__name__} completed", level)
                    return result
                except Exception as e:
                    logger.error(f"Function {func.__name__} failed", exception=e)
                    raise
        
        return wrapper
    return decorator


# Configuración global del logger
current_logger: Optional[StructuredLogger] = None


def set_current_logger(logger: StructuredLogger):
    """Establece logger global actual"""
    global current_logger
    current_logger = logger


def get_current_logger() -> StructuredLogger:
    """Obtiene logger global actual"""
    global current_logger
    if current_logger is None:
        current_logger = create_mcp_logger('global')
    return current_logger


# Ejemplo de uso y configuración
if __name__ == "__main__":
    # Configuración de ejemplo
    logger = create_mcp_logger(
        component="test",
        level=LogLevel.DEBUG,
        config={
            'log_dir': './logs',
            'enable_console': True,
            'enable_file': True,
            'enable_elk': False,
            'enable_cloud': False
        }
    )
    
    # Ejemplo de uso
    with logger.operation_context("test_operation", user_id="user123"):
        logger.info("Iniciando operación de prueba")
        logger.debug("Información de debug", extra_field="valor")
        
        try:
            # Simular operación
            time.sleep(0.1)
            raise ValueError("Error de prueba")
        except Exception as e:
            logger.error("Error en operación", exception=e)
        
        logger.info("Operación completada")
    
    # Ejemplo de audit logging
    audit = logger.get_audit_logger()
    audit.log_access("user123", "/api/data", "GET")
    audit.log_data_change("user123", "user_profile", "UPDATE", 
                         old_value="old_email", new_value="new_email")
    
    # Ejemplo de performance logging
    perf = logger.get_performance_logger()
    def expensive_operation():
        time.sleep(0.05)
        return "result"
    
    result = perf.log_operation("expensive_op", expensive_operation)
    print(f"Resultado: {result}")