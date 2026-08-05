"""
Configuración centralizada para Google Workspace Enterprise Agents
Manejo de credenciales, configuración y settings para todos los agentes
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
import asyncio

from .base_google_workspace_agent import GoogleWorkspaceConfig, GoogleWorkspaceService


@dataclass
class GoogleWorkspaceEnterpriseConfig:
    """Configuración completa para Google Workspace Enterprise"""
    
    # Credenciales OAuth2
    client_id: str = ""
    client_secret: str = ""
    project_id: str = ""
    
    # Archivos de configuración
    credentials_file: str = "google_credentials.json"
    token_file: str = "google_enterprise_token.pickle"
    
    # Scopes por servicio
    docs_scopes: List[str] = field(default_factory=lambda: [
        'https://www.googleapis.com/auth/documents'
    ])
    
    sheets_scopes: List[str] = field(default_factory=lambda: [
        'https://www.googleapis.com/auth/spreadsheets'
    ])
    
    drive_scopes: List[str] = field(default_factory=lambda: [
        'https://www.googleapis.com/auth/drive'
    ])
    
    gmail_scopes: List[str] = field(default_factory=lambda: [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ])
    
    calendar_scopes: List[str] = field(default_factory=lambda: [
        'https://www.googleapis.com/auth/calendar'
    ])
    
    # Configuración de rate limiting
    rate_limit_per_user: int = 100  # requests per 100 seconds
    rate_limit_per_project: int = 1000  # requests per 100 seconds
    request_interval_ms: int = 100  # minimum interval between requests
    
    # Configuración de logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: str = "google_workspace_enterprise.log"
    
    # Configuración de timeout
    auth_timeout: int = 300  # 5 minutos
    request_timeout: int = 30  # 30 segundos
    retry_attempts: int = 3
    retry_delay: float = 1.0  # segundos
    
    # Configuración de cache
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 hora
    cache_max_size: int = 1000  # entries
    
    # Configuración de métricas
    metrics_enabled: bool = True
    metrics_interval: int = 60  # segundos
    
    # Configuración de workspace
    workspace_name: str = "Default Workspace"
    organization_id: Optional[str] = None
    domain_restriction: Optional[str] = None


class GoogleWorkspaceConfigManager:
    """Gestor de configuración para Google Workspace Enterprise"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "google_workspace_config.json"
        self.logger = logging.getLogger(__name__)
        self._config: Optional[GoogleWorkspaceEnterpriseConfig] = None
        self._agent_configs: Dict[str, GoogleWorkspaceConfig] = {}
    
    def load_config(self, env_prefix: str = "GOOGLE_") -> GoogleWorkspaceEnterpriseConfig:
        """
        Cargar configuración desde archivo y variables de entorno
        
        Args:
            env_prefix: Prefijo para variables de entorno
            
        Returns:
            Configuración cargada
        """
        try:
            # Cargar desde archivo si existe
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    file_config = json.load(f)
            else:
                file_config = {}
            
            # Combinar con variables de entorno
            config_dict = {}
            
            # Credenciales OAuth2
            config_dict.update({
                'client_id': os.getenv(f"{env_prefix}CLIENT_ID", file_config.get('client_id', '')),
                'client_secret': os.getenv(f"{env_prefix}CLIENT_SECRET", file_config.get('client_secret', '')),
                'project_id': os.getenv(f"{env_prefix}PROJECT_ID", file_config.get('project_id', '')),
            })
            
            # Archivos de configuración
            config_dict.update({
                'credentials_file': os.getenv(f"{env_prefix}CREDENTIALS_FILE", 
                                             file_config.get('credentials_file', 'google_credentials.json')),
                'token_file': os.getenv(f"{env_prefix}TOKEN_FILE", 
                                      file_config.get('token_file', 'google_enterprise_token.pickle')),
            })
            
            # Rate limiting
            config_dict.update({
                'rate_limit_per_user': int(os.getenv(f"{env_prefix}RATE_LIMIT_USER", 
                                                    file_config.get('rate_limit_per_user', 100))),
                'rate_limit_per_project': int(os.getenv(f"{env_prefix}RATE_LIMIT_PROJECT", 
                                                       file_config.get('rate_limit_per_project', 1000))),
                'request_interval_ms': int(os.getenv(f"{env_prefix}REQUEST_INTERVAL", 
                                                   file_config.get('request_interval_ms', 100))),
            })
            
            # Timeouts
            config_dict.update({
                'auth_timeout': int(os.getenv(f"{env_prefix}AUTH_TIMEOUT", 
                                            file_config.get('auth_timeout', 300))),
                'request_timeout': int(os.getenv(f"{env_prefix}REQUEST_TIMEOUT", 
                                               file_config.get('request_timeout', 30))),
            })
            
            # Workspace settings
            config_dict.update({
                'workspace_name': os.getenv(f"{env_prefix}WORKSPACE_NAME", 
                                          file_config.get('workspace_name', 'Default Workspace')),
                'organization_id': os.getenv(f"{env_prefix}ORGANIZATION_ID", 
                                           file_config.get('organization_id')),
                'domain_restriction': os.getenv(f"{env_prefix}DOMAIN_RESTRICTION", 
                                              file_config.get('domain_restriction')),
            })
            
            # Crear configuración
            self._config = GoogleWorkspaceEnterpriseConfig(**config_dict)
            
            self.logger.info(f"Configuración cargada desde {self.config_path}")
            return self._config
            
        except Exception as e:
            self.logger.error(f"Error cargando configuración: {e}")
            raise
    
    def save_config(self, config: GoogleWorkspaceEnterpriseConfig):
        """
        Guardar configuración a archivo
        
        Args:
            config: Configuración a guardar
        """
        try:
            config_dict = {
                'client_id': config.client_id,
                'project_id': config.project_id,
                'credentials_file': config.credentials_file,
                'token_file': config.token_file,
                'rate_limit_per_user': config.rate_limit_per_user,
                'rate_limit_per_project': config.rate_limit_per_project,
                'request_interval_ms': config.request_interval_ms,
                'auth_timeout': config.auth_timeout,
                'request_timeout': config.request_timeout,
                'workspace_name': config.workspace_name,
                'organization_id': config.organization_id,
                'domain_restriction': config.domain_restriction,
                'log_level': config.log_level,
                'log_file': config.log_file,
                'cache_enabled': config.cache_enabled,
                'metrics_enabled': config.metrics_enabled
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            self.logger.info(f"Configuración guardada en {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Error guardando configuración: {e}")
            raise
    
    def create_agent_config(
        self, 
        service: GoogleWorkspaceService,
        config: Optional[GoogleWorkspaceEnterpriseConfig] = None
    ) -> GoogleWorkspaceConfig:
        """
        Crear configuración específica para un agente
        
        Args:
            service: Servicio de Google Workspace
            config: Configuración base (opcional)
            
        Returns:
            Configuración del agente
        """
        if config is None:
            config = self.get_config()
        
        # Seleccionar scopes según el servicio
        scopes_map = {
            GoogleWorkspaceService.DOCS: config.docs_scopes,
            GoogleWorkspaceService.SHEETS: config.sheets_scopes,
            GoogleWorkspaceService.DRIVE: config.drive_scopes,
            GoogleWorkspaceService.GMAIL: config.gmail_scopes,
            GoogleWorkspaceService.CALENDAR: config.calendar_scopes,
        }
        
        scopes = scopes_map.get(service, config.docs_scopes)
        
        # Crear configuración del agente
        agent_config = GoogleWorkspaceConfig(
            client_id=config.client_id,
            client_secret=config.client_secret,
            project_id=config.project_id,
            scopes=scopes,
            credentials_file=config.credentials_file,
            token_file=f"{service.value}_{config.token_file}",
            auth_timeout=config.auth_timeout
        )
        
        # Cachear configuración
        service_key = service.value
        self._agent_configs[service_key] = agent_config
        
        return agent_config
    
    def get_config(self) -> GoogleWorkspaceEnterpriseConfig:
        """Obtener configuración actual"""
        if self._config is None:
            self._config = self.load_config()
        return self._config
    
    def validate_config(self, config: GoogleWorkspaceEnterpriseConfig) -> List[str]:
        """
        Validar configuración y retornar errores
        
        Args:
            config: Configuración a validar
            
        Returns:
            Lista de errores de validación
        """
        errors = []
        
        # Validar credenciales
        if not config.client_id:
            errors.append("Client ID es requerido")
        
        if not config.client_secret:
            errors.append("Client Secret es requerido")
        
        if not config.project_id:
            errors.append("Project ID es requerido")
        
        # Validar archivos
        credentials_path = Path(config.credentials_file)
        if not credentials_path.exists() and not credentials_path.parent.exists():
            errors.append(f"Directorio de credenciales no existe: {credentials_path.parent}")
        
        # Validar límites de rate
        if config.rate_limit_per_user <= 0:
            errors.append("Rate limit por usuario debe ser positivo")
        
        if config.rate_limit_per_project <= 0:
            errors.append("Rate limit por proyecto debe ser positivo")
        
        # Validar timeouts
        if config.auth_timeout <= 0:
            errors.append("Timeout de autenticación debe ser positivo")
        
        if config.request_timeout <= 0:
            errors.append("Timeout de request debe ser positivo")
        
        return errors
    
    def setup_logging(self, config: GoogleWorkspaceEnterpriseConfig):
        """
        Configurar sistema de logging
        
        Args:
            config: Configuración de logging
        """
        log_level = getattr(logging, config.log_level.upper(), logging.INFO)
        
        # Crear directorio de logs si no existe
        log_file_path = Path(config.log_file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configurar formatter
        formatter = logging.Formatter(config.log_format)
        
        # Configurar file handler
        file_handler = logging.FileHandler(config.log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        
        # Configurar console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        
        # Configurar logger root
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        self.logger.info("Sistema de logging configurado")
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Obtener información del entorno"""
        return {
            "python_version": os.sys.version,
            "current_directory": os.getcwd(),
            "environment_variables": {k: v for k, v in os.environ.items() 
                                    if k.startswith("GOOGLE_")},
            "config_file_exists": os.path.exists(self.config_path),
            "credentials_file_exists": False  # Se verificaría con la config real
        }


class GoogleWorkspaceEnterpriseInitializer:
    """Inicializador completo del sistema Google Workspace Enterprise"""
    
    def __init__(self, config_manager: GoogleWorkspaceConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
    
    async def initialize_system(self) -> Dict[str, Any]:
        """
        Inicializar sistema completo
        
        Returns:
            Estado de inicialización
        """
        try:
            # 1. Cargar configuración
            config = self.config_manager.load_config()
            self.logger.info("Configuración cargada")
            
            # 2. Validar configuración
            errors = self.config_manager.validate_config(config)
            if errors:
                return {
                    "success": False,
                    "errors": errors,
                    "phase": "validation"
                }
            
            # 3. Configurar logging
            self.config_manager.setup_logging(config)
            self.logger.info("Sistema de logging configurado")
            
            # 4. Verificar conectividad
            connectivity_result = await self._check_connectivity(config)
            if not connectivity_result["success"]:
                return connectivity_result
            
            # 5. Inicializar agentes
            agents_initialized = await self._initialize_agents(config)
            
            return {
                "success": True,
                "phase": "initialization_complete",
                "agents_initialized": agents_initialized,
                "config": config.__dict__
            }
            
        except Exception as e:
            self.logger.error(f"Error en inicialización: {e}")
            return {
                "success": False,
                "error": str(e),
                "phase": "initialization"
            }
    
    async def _check_connectivity(self, config: GoogleWorkspaceEnterpriseConfig) -> Dict[str, Any]:
        """Verificar conectividad con Google APIs"""
        try:
            # Test básico de conectividad
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/auth/cloud-platform",
                    timeout=10.0
                )
                
                return {
                    "success": True,
                    "connectivity": "ok",
                    "phase": "connectivity_check"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error de conectividad: {str(e)}",
                "phase": "connectivity_check"
            }
    
    async def _initialize_agents(self, config: GoogleWorkspaceEnterpriseConfig) -> Dict[str, bool]:
        """Inicializar todos los agentes"""
        from .google_docs_agent import GoogleDocsAgent
        from .google_sheets_agent import GoogleSheetsAgent
        from .google_drive_agent import GoogleDriveAgent
        from .google_gmail_agent import GoogleGmailAgent
        from .google_calendar_agent import GoogleCalendarAgent
        
        agents = {
            "docs": GoogleDocsAgent,
            "sheets": GoogleSheetsAgent,
            "drive": GoogleDriveAgent,
            "gmail": GoogleGmailAgent,
            "calendar": GoogleCalendarAgent
        }
        
        initialized_agents = {}
        
        for agent_name, agent_class in agents.items():
            try:
                # Crear configuración específica del agente
                service = GoogleWorkspaceService(agent_name)
                agent_config = self.config_manager.create_agent_config(service, config)
                
                # Inicializar agente (sin autenticación real)
                agent = agent_class(agent_config)
                
                # Health check básico
                health = await agent.health_check()
                initialized_agents[agent_name] = health.get("healthy", False)
                
                self.logger.info(f"Agente {agent_name} inicializado: {health.get('healthy', False)}")
                
            except Exception as e:
                self.logger.error(f"Error inicializando agente {agent_name}: {e}")
                initialized_agents[agent_name] = False
        
        return initialized_agents
    
    def create_sample_config(self, output_path: str = "google_workspace_config.json"):
        """Crear archivo de configuración de ejemplo"""
        sample_config = {
            "client_id": "YOUR_CLIENT_ID_HERE",
            "client_secret": "YOUR_CLIENT_SECRET_HERE", 
            "project_id": "YOUR_PROJECT_ID_HERE",
            "credentials_file": "google_credentials.json",
            "token_file": "google_enterprise_token.pickle",
            "rate_limit_per_user": 100,
            "rate_limit_per_project": 1000,
            "request_interval_ms": 100,
            "auth_timeout": 300,
            "request_timeout": 30,
            "workspace_name": "Mi Organización",
            "organization_id": "",
            "domain_restriction": "",
            "log_level": "INFO",
            "log_file": "logs/google_workspace_enterprise.log",
            "cache_enabled": True,
            "metrics_enabled": True
        }
        
        with open(output_path, 'w') as f:
            json.dump(sample_config, f, indent=2)
        
        print(f"Archivo de configuración de ejemplo creado: {output_path}")
        print("Por favor, edita el archivo con tus credenciales reales")


# Instancia global del gestor de configuración
config_manager = GoogleWorkspaceConfigManager()