"""
Utilidades de logging para MCP Core Superior
"""
import logging
import sys
from typing import Optional
from datetime import datetime


def setup_logging(
    level: str = "INFO",
    format: str = "text",
    file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """
    Configurar logging del sistema
    
    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Formato (text, json)
        file: Archivo de log (opcional)
        console: Mostrar logs en consola
        
    Returns:
        Logger configurado
    """
    # Configurar nivel
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configurar formatter
    if format.lower() == "json":
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
            datefmt="%Y-%m-%dT%H:%M:%S"
        )
    else:
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Configurar handler de consola
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(numeric_level)
    
    # Configurar handler de archivo
    handlers = []
    if console:
        handlers.append(console_handler)
    
    if file:
        file_handler = logging.FileHandler(file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(numeric_level)
        handlers.append(file_handler)
    
    # Configurar logger raíz
    logging.basicConfig(
        level=numeric_level,
        handlers=handlers,
        force=True
    )
    
    # Configurar loggers de librerías
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    return logging.getLogger("mcp.core")


def get_logger(name: str) -> logging.Logger:
    """Obtener logger configurado"""
    return logging.getLogger(f"mcp.{name}")
