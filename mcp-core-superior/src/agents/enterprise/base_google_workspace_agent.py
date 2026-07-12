"""
Base Google Workspace Agent - Agente Base para Integración Google Workspace
Proporciona autenticación OAuth2, manejo de APIs y funcionalidades comunes
para todos los servicios de Google Workspace (Docs, Sheets, Drive, Gmail, Calendar)
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import aiofiles
import pickle
from pathlib import Path

import httpx
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import set_user_agent

from ..base_agent_wrapper import BaseAgentWrapper, AgentCapability
from ...core.exceptions import AgentException, handle_exceptions
from ...core.config import settings


class GoogleWorkspaceService(Enum):
    """Servicios de Google Workspace"""
    DOCS = "docs"
    SHEETS = "sheets"
    DRIVE = "drive"
    GMAIL = "gmail"
    CALENDAR = "calendar"
    SLIDES = "slides"
    FORMS = "forms"
    KEEP = "keep"


class AuthStatus(Enum):
    """Estados de autenticación"""
    NOT_AUTHENTICATED = "not_authenticated"
    AUTHENTICATING = "authenticating"
    AUTHENTICATED = "authenticated"
    EXPIRED = "expired"
    ERROR = "error"


@dataclass
class GoogleWorkspaceConfig:
    """Configuración para Google Workspace"""
    client_id: str = ""
    client_secret: str = ""
    project_id: str = ""
    scopes: List[str] = field(default_factory=lambda: [
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/presentations',
        'https://www.googleapis.com/auth/forms.body.readonly',
        'https://www.googleapis.com/auth/keep',
    ])
    credentials_file: str = "google_credentials.json"
    token_file: str = "google_token.pickle"
    redirect_uri: str = "http://localhost:8080"
    auth_timeout: int = 300  # 5 minutos
    
    @property
    def is_configured(self) -> bool:
        """Verificar si está configurado"""
        return bool(self.client_id and self.client_secret and self.project_id)


@dataclass
class ApiResponse:
    """Respuesta de API de Google Workspace"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    request_id: Optional[str] = None


@dataclass
class OperationLog:
    """Log de operación de Google Workspace"""
    timestamp: datetime
    service: GoogleWorkspaceService
    operation: str
    success: bool
    execution_time_ms: float
    user: str
    resource_id: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseGoogleWorkspaceAgent(BaseAgentWrapper):
    """
    Agente Base para Google Workspace
    
    Proporciona:
    - Autenticación OAuth2
    - Gestión de credenciales
    - Construcción de servicios
    - Manejo de errores
    - Logging y monitoreo
    - Rate limiting
    """
    
    def __init__(self, config: GoogleWorkspaceConfig):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.auth_status = AuthStatus.NOT_AUTHENTICATED
        self.credentials: Optional[Credentials] = None
        self.services: Dict[str, Any] = {}
        self.operation_history: List[OperationLog] = []
        self.rate_limiter = asyncio.Lock()
        self.last_request_time = 0
        
        # Configurar scopes según el servicio
        self._setup_capabilities()
    
    def _setup_capabilities(self):
        """Configurar capacidades del agente"""
        self.add_capability(AgentCapability.DOCUMENT_PROCESSING)
        self.add_capability(AgentCapability.DATA_ANALYSIS)
        self.add_capability(AgentCapability.AUTOMATION)
        self.add_capability(AgentCapability.WEB_SCRAPING)
    
    @handle_exceptions
    async def authenticate(self, force_refresh: bool = False) -> ApiResponse:
        """
        Autenticar con Google Workspace usando OAuth2
        
        Args:
            force_refresh: Forzar renovación de token
            
        Returns:
            ApiResponse: Resultado de autenticación
        """
        start_time = datetime.now()
        
        try:
            self.auth_status = AuthStatus.AUTHENTICATING
            
            # Verificar credenciales existentes
            if not force_refresh and self.credentials and self.credentials.valid:
                self.auth_status = AuthStatus.AUTHENTICATED
                self.logger.info("Credenciales válidas encontradas")
                return ApiResponse(
                    success=True,
                    data={"status": "authenticated", "method": "existing_token"},
                    execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
                )
            
            # Cargar o crear credenciales
            credentials = await self._load_or_create_credentials()
            
            if not credentials or not credentials.valid:
                # Iniciar flujo OAuth2
                flow = InstalledAppFlow.from_client_config(
                    {
                        "web": {
                            "client_id": self.config.client_id,
                            "client_secret": self.config.client_secret,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "redirect_uris": [self.config.redirect_uri]
                        }
                    },
                    scopes=self.config.scopes
                )
                
                credentials = flow.run_local_server(port=0, timeout=self.config.auth_timeout)
            
            # Guardar credenciales
            await self._save_credentials(credentials)
            
            self.credentials = credentials
            self.auth_status = AuthStatus.AUTHENTICATED
            
            self.logger.info("Autenticación exitosa con Google Workspace")
            
            return ApiResponse(
                success=True,
                data={"status": "authenticated", "method": "oauth2"},
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        except Exception as e:
            self.auth_status = AuthStatus.ERROR
            error_msg = f"Error en autenticación: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(
                success=False,
                error=error_msg,
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    async def _load_or_create_credentials(self) -> Optional[Credentials]:
        """Cargar o crear credenciales"""
        token_file = Path(self.config.token_file)
        
        if token_file.exists():
            try:
                async with aiofiles.open(token_file, 'rb') as f:
                    content = await f.read()
                    credentials = pickle.loads(content)
                    
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                    await self._save_credentials(credentials)
                
                return credentials
            except Exception as e:
                self.logger.warning(f"No se pudieron cargar credenciales existentes: {e}")
        
        return None
    
    async def _save_credentials(self, credentials: Credentials):
        """Guardar credenciales"""
        token_file = Path(self.config.token_file)
        
        try:
            async with aiofiles.open(token_file, 'wb') as f:
                pickle.dump(credentials, f)
            
            # Configurar permisos restrictivos
            os.chmod(token_file, 0o600)
            self.logger.debug("Credenciales guardadas")
            
        except Exception as e:
            self.logger.error(f"Error guardando credenciales: {e}")
    
    @handle_exceptions
    async def get_service(self, service_name: GoogleWorkspaceService) -> Any:
        """
        Obtener servicio de Google Workspace
        
        Args:
            service_name: Nombre del servicio
            
        Returns:
            Servicio de Google API
        """
        if self.auth_status != AuthStatus.AUTHENTICATED:
            raise AgentException("No autenticado con Google Workspace")
        
        if service_name.value in self.services:
            return self.services[service_name.value]
        
        # Construir servicio
        try:
            service = build(
                service_name.value,
                'v1',
                credentials=self.credentials,
                cache_discovery=False
            )
            
            self.services[service_name.value] = service
            self.logger.debug(f"Servicio {service_name.value} inicializado")
            return service
            
        except Exception as e:
            error_msg = f"Error inicializando servicio {service_name.value}: {str(e)}"
            self.logger.error(error_msg)
            raise AgentException(error_msg)
    
    @handle_exceptions
    async def execute_api_call(
        self, 
        service_name: GoogleWorkspaceService,
        method: str,
        endpoint: str,
        **kwargs
    ) -> ApiResponse:
        """
        Ejecutar llamada API con rate limiting y manejo de errores
        
        Args:
            service_name: Servicio de Google Workspace
            method: Método HTTP
            endpoint: Endpoint de la API
            **kwargs: Parámetros adicionales
            
        Returns:
            ApiResponse: Resultado de la llamada API
        """
        start_time = datetime.now()
        
        try:
            # Rate limiting
            async with self.rate_limiter:
                await self._apply_rate_limit()
            
            # Obtener servicio
            service = await self.get_service(service_name)
            service_method = getattr(service, endpoint.split('/')[0])()
            
            # Ejecutar llamada
            response = await asyncio.to_thread(
                getattr(service_method, method),
                **kwargs
            )
            
            # Log operación
            await self._log_operation(
                service_name=service_name,
                operation=f"{method.upper()} {endpoint}",
                success=True,
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                metadata={"endpoint": endpoint, "params": kwargs}
            )
            
            return ApiResponse(
                success=True,
                data=response,
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        except HttpError as e:
            error_msg = f"Error HTTP en API de {service_name.value}: {e}"
            self.logger.error(error_msg)
            
            await self._log_operation(
                service_name=service_name,
                operation=f"{method.upper()} {endpoint}",
                success=False,
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                error=str(e)
            )
            
            return ApiResponse(
                success=False,
                error=error_msg,
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        except Exception as e:
            error_msg = f"Error ejecutando API {service_name.value}: {str(e)}"
            self.logger.error(error_msg)
            
            return ApiResponse(
                success=False,
                error=error_msg,
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    async def _apply_rate_limit(self):
        """Aplicar rate limiting (100 req/100seg usuario, 1000 req/100seg por proyecto)"""
        current_time = datetime.now().timestamp()
        time_since_last = current_time - self.last_request_time
        
        # Mínimo 100ms entre requests
        if time_since_last < 0.1:
            await asyncio.sleep(0.1 - time_since_last)
        
        self.last_request_time = datetime.now().timestamp()
    
    async def _log_operation(
        self,
        service_name: GoogleWorkspaceService,
        operation: str,
        success: bool,
        execution_time_ms: float,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log de operación"""
        log_entry = OperationLog(
            timestamp=datetime.now(),
            service=service_name,
            operation=operation,
            success=success,
            execution_time_ms=execution_time_ms,
            user="current_user",  # Obtener del contexto
            error=error,
            metadata=metadata or {}
        )
        
        self.operation_history.append(log_entry)
        
        # Mantener solo últimas 1000 operaciones
        if len(self.operation_history) > 1000:
            self.operation_history = self.operation_history[-1000:]
        
        # Log en archivo
        self.logger.info(
            f"Google Workspace {service_name.value}: {operation} - "
            f"{'SUCCESS' if success else 'FAILED'} "
            f"({execution_time_ms:.2f}ms)"
        )
    
    async def get_auth_status(self) -> Dict[str, Any]:
        """Obtener estado de autenticación"""
        return {
            "status": self.auth_status.value,
            "configured": self.config.is_configured,
            "credentials_exists": Path(self.config.token_file).exists(),
            "last_operation": self.operation_history[-1].__dict__ if self.operation_history else None,
            "active_services": list(self.services.keys())
        }
    
    async def revoke_authentication(self) -> ApiResponse:
        """Revocar autenticación"""
        try:
            if self.credentials and hasattr(self.credentials, 'token'):
                # Revocar token en Google
                async with httpx.AsyncClient() as client:
                    await client.post(
                        "https://oauth2.googleapis.com/revoke",
                        data={"token": self.credentials.token},
                        headers={'content-type': 'application/x-www-form-urlencoded'}
                    )
            
            # Limpiar archivos locales
            token_file = Path(self.config.token_file)
            if token_file.exists():
                token_file.unlink()
            
            # Limpiar estado
            self.credentials = None
            self.services.clear()
            self.auth_status = AuthStatus.NOT_AUTHENTICATED
            
            return ApiResponse(
                success=True,
                data={"status": "revoked"}
            )
            
        except Exception as e:
            error_msg = f"Error revocando autenticación: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(
                success=False,
                error=error_msg
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar salud del agente"""
        try:
            # Verificar autenticación
            auth_status = await self.get_auth_status()
            
            if not auth_status["configured"]:
                return {
                    "healthy": False,
                    "error": "Google Workspace no configurado",
                    "details": auth_status
                }
            
            # Test de conectividad
            if auth_status["status"] == "authenticated":
                # Intentar una llamada simple a Drive API
                drive_service = await self.get_service(GoogleWorkspaceService.DRIVE)
                about = drive_service.about().get(fields="user").execute()
                
                return {
                    "healthy": True,
                    "service": "Google Workspace Base Agent",
                    "user": about.get("user", {}),
                    "details": auth_status
                }
            else:
                return {
                    "healthy": False,
                    "error": "No autenticado",
                    "details": auth_status
                }
                
        except Exception as e:
            return {
                "healthy": False,
                "error": f"Error en health check: {str(e)}",
                "service": "Google Workspace Base Agent"
            }