"""
Microsoft 365 Integration - Logger Configuration
Configuración centralizada de logging
"""

import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Configuración de formato
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
JSON_FORMAT = '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'

# Configuración de colores para consola
class ColoredFormatter(logging.Formatter):
    """Formateador con colores para consola"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        if sys.stdout.isatty():  # Solo aplicar colores si es un terminal
            color = self.COLORS.get(record.levelname, '')
            record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)

def configure_logging(
    level: str = "INFO",
    format_type: str = "standard",
    enable_colors: bool = True,
    enable_file: bool = True,
    log_file: Optional[str] = None
) -> None:
    """Configurar sistema de logging"""
    
    # Configurar nivel
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configurar root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Limpiar handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Configurar formato
    if format_type == "json":
        formatter = logging.Formatter(JSON_FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
    else:
        if enable_colors and sys.stdout.isatty():
            formatter = ColoredFormatter(LOG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
        else:
            formatter = logging.Formatter(LOG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Handler para archivo si se habilita
    if enable_file:
        if not log_file:
            log_file = f"microsoft365_integration_{datetime.now().strftime('%Y%m%d')}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Configurar loggers específicos
    configure_service_loggers(level)

def configure_service_loggers(level: str) -> None:
    """Configurar loggers específicos de servicios"""
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Loggers de servicios
    service_loggers = [
        'microsoft365.graph',
        'microsoft365.auth',
        'microsoft365.word',
        'microsoft365.excel',
        'microsoft365.powerpoint',
        'microsoft365.outlook',
        'microsoft365.onedrive',
        'microsoft365.teams'
    ]
    
    for logger_name in service_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)

class StructuredLogger:
    """Logger estructurado para Microsoft 365 Integration"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, **kwargs) -> None:
        """Log con información adicional"""
        extra_data = self._format_extra_data(kwargs)
        self.logger.info(f"{message} {extra_data}")
    
    def error(self, message: str, **kwargs) -> None:
        """Log de error con contexto"""
        extra_data = self._format_extra_data(kwargs)
        self.logger.error(f"{message} {extra_data}")
    
    def warning(self, message: str, **kwargs) -> None:
        """Log de advertencia con contexto"""
        extra_data = self._format_extra_data(kwargs)
        self.logger.warning(f"{message} {extra_data}")
    
    def debug(self, message: str, **kwargs) -> None:
        """Log de debug con contexto"""
        extra_data = self._format_extra_data(kwargs)
        self.logger.debug(f"{message} {extra_data}")
    
    def critical(self, message: str, **kwargs) -> None:
        """Log crítico con contexto"""
        extra_data = self._format_extra_data(kwargs)
        self.logger.critical(f"{message} {extra_data}")
    
    def _format_extra_data(self, data: Dict[str, Any]) -> str:
        """Formatear datos adicionales"""
        if not data:
            return ""
        
        formatted = ", ".join(f"{k}={v}" for k, v in data.items())
        return f"[{formatted}]"

def get_logger(name: str) -> StructuredLogger:
    """Obtener logger configurado"""
    return StructuredLogger(name)