"""
Integración del Sistema de Structured Logging con Agentes MCP

Proporciona adaptadores y decoradores para integrar el logging estructurado
con los agentes MCP existentes.
"""

import functools
import asyncio
import inspect
import time
from typing import Any, Callable, Dict, Optional, Union
from .structured_logger import StructuredLogger, LogLevel, get_current_logger
from .logging_config import get_mcp_logger


class MCPAgentLogger:
    """Adaptador de logging para agentes MCP"""
    
    def __init__(self, agent_name: str, agent_instance: Any = None):
        self.agent_name = agent_name
        self.agent_instance = agent_instance
        self.logger = get_mcp_logger(agent_name)
        self.correlation_id = None
        
        # Registrar métodos de logging en el agente
        self._inject_logging_methods()
    
    def _inject_logging_methods(self):
        """Inyecta métodos de logging en la instancia del agente"""
        if not self.agent_instance:
            return
        
        # Métodos de logging a inyectar
        logging_methods = {
            'debug': self.logger.debug,
            'info': self.logger.info,
            'warn': self.logger.warn,
            'error': self.logger.error,
            'critical': self.logger.critical,
            'trace': self.logger.trace,
            'log_operation': self.logger.operation_context
        }
        
        for method_name, method_func in logging_methods.items():
            if not hasattr(self.agent_instance, method_name):
                setattr(self.agent_instance, method_name, method_func)


def log_agent_execution(agent_name: str, 
                       operation_type: str = "execute",
                       level: LogLevel = LogLevel.INFO):
    """
    Decorador para logging automático de ejecución de agentes
    
    Args:
        agent_name: Nombre del agente
        operation_type: Tipo de operación
        level: Nivel de log
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_mcp_logger(agent_name)
            
            # Extraer parámetros relevantes del método
            method_params = {}
            sig = inspect.signature(func)
            
            # Intentar extraer información de self si existe
            if args and hasattr(args[0], '__dict__'):
                instance = args[0]
                method_params['agent_instance'] = type(instance).__name__
            
            # Extraer parámetros de la función
            for param_name, param_value in zip(sig.parameters.keys(), args[1:], 
                                             list(sig.parameters.keys())[1:]):
                if isinstance(param_value, (str, int, float, bool)):
                    method_params[param_name] = param_value
            
            with logger.operation_context(f"{operation_type}.{func.__name__}", 
                                        agent=agent_name, **method_params):
                try:
                    logger.info(f"Starting {operation_type}: {func.__name__}", 
                              function=func.__name__)
                    
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    duration = (time.time() - start_time) * 1000
                    
                    logger.info(f"Completed {operation_type}: {func.__name__}", 
                              function=func.__name__, 
                              duration_ms=duration,
                              status="success")
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"Failed {operation_type}: {func.__name__}", 
                               exception=e,
                               function=func.__name__,
                               status="error")
                    raise
        
        return wrapper
    return decorator


def log_async_agent_execution(agent_name: str, 
                             operation_type: str = "execute",
                             level: LogLevel = LogLevel.INFO):
    """
    Decorador para logging automático de agentes asíncronos
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_mcp_logger(agent_name)
            
            # Extraer información del método
            method_params = {}
            if args and hasattr(args[0], '__dict__'):
                instance = args[0]
                method_params['agent_instance'] = type(instance).__name__
            
            with logger.operation_context(f"{operation_type}.{func.__name__}", 
                                        agent=agent_name, **method_params):
                try:
                    logger.info(f"Starting async {operation_type}: {func.__name__}")
                    
                    start_time = time.time()
                    result = await func(*args, **kwargs)
                    duration = (time.time() - start_time) * 1000
                    
                    logger.info(f"Completed async {operation_type}: {func.__name__}", 
                              duration_ms=duration, status="success")
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"Failed async {operation_type}: {func.__name__}", 
                               exception=e, status="error")
                    raise
        
        return async_wrapper
    return decorator


def log_agent_method_calls(agent_name: str):
    """
    Decorador para logging automático de llamadas a métodos de agentes
    """
    def decorator(cls):
        original_init = cls.__init__
        original_methods = [name for name, method in inspect.getmembers(cls, inspect.isfunction)
                          if not name.startswith('_')]
        
        @functools.wraps(original_init)
        def new_init(self, *args, **kwargs):
            result = original_init(self, *args, **kwargs)
            
            # Injectar logger en la instancia
            if hasattr(self, 'logger'):
                logger = get_mcp_logger(agent_name)
                setattr(self, 'logger', logger)
                setattr(self, 'agent_name', agent_name)
            
            return result
        
        # Aplicar logging a todos los métodos públicos
        for method_name in original_methods:
            if hasattr(cls, method_name):
                original_method = getattr(cls, method_name)
                
                if inspect.iscoroutinefunction(original_method):
                    logged_method = log_async_agent_execution(agent_name)(original_method)
                else:
                    logged_method = log_agent_execution(agent_name)(original_method)
                
                setattr(cls, method_name, logged_method)
        
        cls.__init__ = new_init
        return cls
    
    return decorator


class AgentLoggingMixin:
    """Mixin para añadir capacidades de logging a agentes MCP"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_mcp_logger(getattr(self, 'agent_name', self.__class__.__name__))
        self.agent_name = getattr(self, 'agent_name', self.__class__.__name__)
    
    def log_execution(self, operation: str, **kwargs):
        """Log de ejecución con contexto automático"""
        return self.logger.operation_context(operation, **kwargs)
    
    def log_info(self, message: str, **kwargs):
        """Log informativo"""
        self.logger.info(message, agent=self.agent_name, **kwargs)
    
    def log_error(self, message: str, exception: Exception = None, **kwargs):
        """Log de error con excepción opcional"""
        self.logger.error(message, exception=exception, agent=self.agent_name, **kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """Log de debug"""
        self.logger.debug(message, agent=self.agent_name, **kwargs)
    
    def log_performance(self, operation: str, duration_ms: float, **kwargs):
        """Log específico para métricas de performance"""
        self.logger.info(f"Performance: {operation}", 
                        operation=operation, 
                        duration_ms=duration_ms,
                        agent=self.agent_name,
                        **kwargs)
    
    def log_audit_event(self, event_type: str, details: Dict, **kwargs):
        """Log de eventos de auditoría"""
        audit_logger = self.logger.get_audit_logger()
        audit_logger.log_system_event(
            event_type=event_type,
            description=f"Audit event from {self.agent_name}",
            details=details,
            **kwargs
        )


def create_logged_agent_wrapper(agent_class, agent_name: str, 
                               additional_config: Optional[Dict] = None):
    """
    Crea un wrapper para un agente que incluye logging automático
    
    Args:
        agent_class: Clase del agente
        agent_name: Nombre del agente para logging
        additional_config: Configuración adicional
    
    Returns:
        Clase wrapper con logging integrado
    """
    
    class LoggedAgentWrapper(AgentLoggingMixin, agent_class):
        def __init__(self, *args, **kwargs):
            self.agent_name = agent_name
            super().__init__(*args, **kwargs)
            
            # Log de inicialización
            self.log_info(f"Agent {agent_name} initialized", 
                         agent_config=additional_config or {})
        
        def __getattribute__(self, name):
            # Interceptar métodos para logging automático
            if not name.startswith('_') and hasattr(super(), name):
                attr = super().__getattribute__(name)
                if callable(attr) and not name in ['log_execution', 'log_info', 'log_error', 
                                                  'log_debug', 'log_performance', 'log_audit_event']:
                    
                    @functools.wraps(attr)
                    def logged_method(*args, **kwargs):
                        with self.log_execution(f"{self.agent_name}.{name}"):
                            try:
                                result = attr(*args, **kwargs)
                                self.log_debug(f"Method {name} completed successfully")
                                return result
                            except Exception as e:
                                self.log_error(f"Method {name} failed", exception=e)
                                raise
                    
                    return logged_method
            
            return super().__getattribute__(name)
    
    LoggedAgentWrapper.__name__ = f"Logged{agent_class.__name__}"
    return LoggedAgentWrapper


# Integración específica con agentes MCP existentes
AGENT_INTEGRATIONS = {
    'database_operations': {
        'log_sensitive_operations': True,
        'audit_data_access': True,
        'performance_monitoring': True
    },
    'file_processing': {
        'log_file_operations': True,
        'performance_monitoring': True
    },
    'git_operations': {
        'audit_repository_changes': True,
        'log_commits': True
    },
    'multiagent_orchestrator': {
        'trace_agent_interactions': True,
        'performance_monitoring': True,
        'correlation_tracking': True
    },
    'python_executor': {
        'log_code_execution': True,
        'performance_monitoring': True,
        'security_logging': True
    },
    'reasoner': {
        'log_reasoning_steps': True,
        'trace_decision_making': True
    },
    'search_engine': {
        'log_search_queries': True,
        'performance_monitoring': True
    },
    'web_scraping': {
        'log_scraping_activities': True,
        'performance_monitoring': True
    }
}


def get_agent_integration_config(agent_name: str) -> Dict[str, Any]:
    """Obtiene configuración de integración para un agente específico"""
    return AGENT_INTEGRATIONS.get(agent_name, {})


def integrate_logging_with_agent(agent_instance, agent_name: str) -> MCPAgentLogger:
    """
    Integra logging con una instancia de agente existente
    
    Args:
        agent_instance: Instancia del agente
        agent_name: Nombre del agente
    
    Returns:
        MCPAgentLogger configurado
    """
    
    integration_config = get_agent_integration_config(agent_name)
    
    # Crear logger específico para el agente
    agent_logger = MCPAgentLogger(agent_name, agent_instance)
    
    # Añadir métodos específicos según la configuración
    if integration_config.get('log_sensitive_operations'):
        def log_sensitive_operation(self, operation: str, data: Any):
            self.logger.info(f"Sensitive operation: {operation}", 
                           operation=operation,
                           sensitive_data=True)
        
        if not hasattr(agent_instance, 'log_sensitive_operation'):
            setattr(agent_instance, 'log_sensitive_operation', 
                   log_sensitive_operation.__get__(agent_instance, type(agent_instance)))
    
    if integration_config.get('audit_data_access'):
        def log_data_access(self, resource: str, action: str, user_id: str = None):
            audit_logger = self.logger.get_audit_logger()
            audit_logger.log_access(user_id or "system", resource, action)
        
        if not hasattr(agent_instance, 'log_data_access'):
            setattr(agent_instance, 'log_data_access', 
                   log_data_access.__get__(agent_instance, type(agent_instance)))
    
    return agent_logger


# Utilidades para logging de herramientas MCP
def log_mcp_tool_execution(tool_name: str, agent_name: str):
    """Decorador específico para logging de herramientas MCP"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_mcp_logger(agent_name)
            
            with logger.operation_context(f"tool.{tool_name}", 
                                        tool=tool_name, agent=agent_name):
                logger.info(f"Executing MCP tool: {tool_name}")
                
                try:
                    result = func(*args, **kwargs)
                    logger.info(f"MCP tool {tool_name} completed successfully")
                    return result
                except Exception as e:
                    logger.error(f"MCP tool {tool_name} failed", exception=e)
                    raise
        
        return wrapper
    return decorator


# Ejemplo de integración
if __name__ == "__main__":
    # Ejemplo 1: Usar el mixin de logging
    class ExampleAgent(AgentLoggingMixin):
        def __init__(self):
            super().__init__()
            self.agent_name = "example_agent"
        
        def process_data(self, data):
            with self.log_execution("process_data", data_size=len(str(data))):
                self.log_info("Processing data")
                return f"Processed: {data}"
        
        def error_operation(self):
            self.log_info("Starting error operation")
            raise ValueError("Test error")
    
    # Ejemplo 2: Crear wrapper con logging
    class SimpleAgent:
        def __init__(self):
            pass
        
        def execute(self, task):
            return f"Executed: {task}"
    
    LoggedSimpleAgent = create_logged_agent_wrapper(SimpleAgent, "simple_agent")
    
    # Ejemplo de uso
    agent = ExampleAgent()
    result = agent.process_data("test data")
    print(result)
    
    # Ejemplo con wrapper
    logged_agent = LoggedSimpleAgent()
    result = logged_agent.execute("test task")
    print(result)