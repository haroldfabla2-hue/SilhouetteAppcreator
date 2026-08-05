"""
Microsoft 365 - Main Integration Class
Orquestador principal que coordina todos los agentes y servicios
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from .config.settings import settings, service_config, database_config, security_config
from .auth.azure_ad import auth_client
from .graph.client import GraphAPIClient
from .agents.word_agent import WordOnlineAgent
from .agents.excel_agent import ExcelOnlineAgent
from .agents.powerpoint_agent import PowerPointAgent
from .agents.outlook_agent import OutlookAgent
from .agents.onedrive_agent import OneDriveAgent
from .agents.teams_agent import TeamsAgent
from .utils.logger import get_logger, configure_logging
from .utils.sync_manager import SyncManager
from .utils.license_manager import LicenseManager
from .utils.notification_handler import NotificationHandler
from .utils.retry_handler import RetryHandler
from .utils.rate_limiter import RateLimiter

logger = get_logger(__name__)

class Microsoft365Integration:
    """
    Clase principal que orquesta la integración completa de Microsoft 365
    Proporciona una interfaz unificada para todos los servicios
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializar la integración de Microsoft 365
        
        Args:
            config: Configuración opcional personalizada
        """
        self.config = config or {}
        self.is_initialized = False
        
        # Cliente Graph API principal
        self.graph_client: Optional[GraphAPIClient] = None
        
        # Agentes especializados
        self.word_agent: Optional[WordOnlineAgent] = None
        self.excel_agent: Optional[ExcelOnlineAgent] = None
        self.powerpoint_agent: Optional[PowerPointAgent] = None
        self.outlook_agent: Optional[OutlookAgent] = None
        self.onedrive_agent: Optional[OneDriveAgent] = None
        self.teams_agent: Optional[TeamsAgent] = None
        
        # Utilidades
        self.sync_manager: Optional[SyncManager] = None
        self.license_manager: Optional[LicenseManager] = None
        self.notification_handler: Optional[NotificationHandler] = None
        self.retry_handler: Optional[RetryHandler] = None
        self.rate_limiter: Optional[RateLimiter] = None
        
        # Estado del sistema
        self.system_status: Dict = {
            'initialized': False,
            'last_health_check': None,
            'services_status': {},
            'errors': []
        }
        
        logger.info("Microsoft 365 Integration initialized")
    
    async def initialize(self) -> Dict:
        """Inicializar todos los componentes de la integración"""
        try:
            if self.is_initialized:
                return {
                    'status': 'warning',
                    'message': 'Integration already initialized',
                    'initialized_at': self.system_status.get('initialized_at')
                }
            
            logger.info("Initializing Microsoft 365 Integration...")
            
            # Configurar logging
            self._configure_logging()
            
            # Inicializar cliente Graph API
            self.graph_client = GraphAPIClient()
            await self.graph_client.start_session()
            
            # Inicializar agentes
            self._initialize_agents()
            
            # Inicializar utilidades
            self._initialize_utilities()
            
            # Realizar health check inicial
            health_check = await self.health_check()
            
            # Actualizar estado
            self.is_initialized = True
            self.system_status.update({
                'initialized': True,
                'initialized_at': datetime.utcnow().isoformat(),
                'services_status': health_check.get('services', {}),
                'last_health_check': health_check.get('timestamp')
            })
            
            logger.info("Microsoft 365 Integration initialized successfully")
            
            return {
                'status': 'success',
                'message': 'Integration initialized successfully',
                'health_check': health_check,
                'initialized_at': self.system_status['initialized_at']
            }
            
        except Exception as e:
            logger.error(f"Error initializing Microsoft 365 Integration: {str(e)}")
            self.system_status['errors'].append({
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
                'component': 'initialization'
            })
            return {
                'status': 'error',
                'error': str(e),
                'initialized_at': datetime.utcnow().isoformat()
            }
    
    def _configure_logging(self):
        """Configurar sistema de logging"""
        log_config = self.config.get('logging', {})
        configure_logging(
            level=log_config.get('level', settings.log_level),
            format_type=log_config.get('format', 'standard'),
            enable_colors=log_config.get('colors', True),
            enable_file=log_config.get('file', True)
        )
    
    def _initialize_agents(self):
        """Inicializar todos los agentes especializados"""
        if not self.graph_client:
            raise RuntimeError("Graph client must be initialized first")
        
        self.word_agent = WordOnlineAgent(self.graph_client)
        self.excel_agent = ExcelOnlineAgent(self.graph_client)
        self.powerpoint_agent = PowerPointAgent(self.graph_client)
        self.outlook_agent = OutlookAgent(self.graph_client)
        self.onedrive_agent = OneDriveAgent(self.graph_client)
        self.teams_agent = TeamsAgent(self.graph_client)
        
        logger.info("All agents initialized")
    
    def _initialize_utilities(self):
        """Inicializar utilidades y gestores"""
        if not self.graph_client:
            raise RuntimeError("Graph client must be initialized first")
        
        # Inicializar gestores
        self.sync_manager = SyncManager(self.graph_client)
        self.license_manager = LicenseManager(self.graph_client)
        self.notification_handler = NotificationHandler(self.graph_client, self.config.get('notifications', {}))
        
        # Inicializar manejadores
        self.retry_handler = RetryHandler(
            max_retries=self.config.get('max_retries', settings.max_retries),
            base_delay=self.config.get('retry_delay', settings.retry_delay)
        )
        
        self.rate_limiter = RateLimiter(
            requests_per_minute=self.config.get('requests_per_minute', settings.requests_per_minute)
        )
        
        # Configurar programador de sincronización
        asyncio.create_task(self.sync_manager.start_sync_scheduler())
        
        logger.info("All utilities initialized")
    
    async def health_check(self) -> Dict:
        """Realizar verificación de salud del sistema"""
        try:
            logger.info("Performing health check...")
            
            health_result = {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'services': {},
                'overall_status': 'healthy'
            }
            
            service_checks = []
            
            # Verificar Graph API
            if self.graph_client:
                try:
                    graph_health = await self.graph_client.health_check()
                    health_result['services']['graph_api'] = graph_health
                    service_checks.append(graph_health.get('status') == 'healthy')
                except Exception as e:
                    health_result['services']['graph_api'] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
                    service_checks.append(False)
            
            # Verificar agentes
            agents = {
                'word': self.word_agent,
                'excel': self.excel_agent,
                'powerpoint': self.powerpoint_agent,
                'outlook': self.outlook_agent,
                'onedrive': self.onedrive_agent,
                'teams': self.teams_agent
            }
            
            for agent_name, agent in agents.items():
                if agent:
                    health_result['services'][agent_name] = {
                        'status': 'available',
                        'last_check': datetime.utcnow().isoformat()
                    }
                    service_checks.append(True)
                else:
                    health_result['services'][agent_name] = {
                        'status': 'unavailable',
                        'error': 'Agent not initialized'
                    }
                    service_checks.append(False)
            
            # Verificar gestores
            if self.sync_manager:
                health_result['services']['sync_manager'] = {
                    'status': 'available',
                    'last_check': datetime.utcnow().isoformat()
                }
                service_checks.append(True)
            
            if self.license_manager:
                health_result['services']['license_manager'] = {
                    'status': 'available',
                    'last_check': datetime.utcnow().isoformat()
                }
                service_checks.append(True)
            
            if self.notification_handler:
                health_result['services']['notification_handler'] = {
                    'status': 'available',
                    'last_check': datetime.utcnow().isoformat()
                }
                service_checks.append(True)
            
            # Determinar estado general
            if all(service_checks):
                health_result['overall_status'] = 'healthy'
            elif any(service_checks):
                health_result['overall_status'] = 'degraded'
            else:
                health_result['overall_status'] = 'unhealthy'
                health_result['status'] = 'unhealthy'
            
            # Actualizar estado del sistema
            self.system_status.update({
                'last_health_check': health_result['timestamp'],
                'services_status': health_result['services']
            })
            
            logger.info(f"Health check completed: {health_result['overall_status']}")
            return health_result
            
        except Exception as e:
            logger.error(f"Error during health check: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'overall_status': 'unhealthy'
            }
    
    # ==================== API UNIFICADA ====================
    
    async def create_document(self, title: str, content: str = "", doc_type: str = "word") -> Dict:
        """Crear documento usando el agente apropiado"""
        if not self.is_initialized:
            raise RuntimeError("Integration not initialized")
        
        if doc_type.lower() == "word":
            return await self.word_agent.create_document(title, content)
        elif doc_type.lower() == "excel":
            return await self.excel_agent.create_workbook(title)
        elif doc_type.lower() == "powerpoint":
            return await self.powerpoint_agent.create_presentation(title)
        else:
            raise ValueError(f"Unsupported document type: {doc_type}")
    
    async def send_email(self, to_recipients: List[str], subject: str, body: str) -> Dict:
        """Enviar email usando el agente de Outlook"""
        if not self.is_initialized or not self.outlook_agent:
            raise RuntimeError("Integration not initialized")
        
        return await self.outlook_agent.send_email(to_recipients, subject, body)
    
    async def upload_file(self, file_path: str, content: bytes) -> Dict:
        """Subir archivo a OneDrive"""
        if not self.is_initialized or not self.onedrive_agent:
            raise RuntimeError("Integration not initialized")
        
        return await self.onedrive_agent.upload_file(file_path, content)
    
    async def create_team(self, team_name: str, description: str = "") -> Dict:
        """Crear equipo en Teams"""
        if not self.is_initialized or not self.teams_agent:
            raise RuntimeError("Integration not initialized")
        
        return await self.teams_agent.create_team(team_name, description)
    
    # ==================== GESTIÓN DE DATOS ====================
    
    async def sync_data(self, source: str, target: str, sync_config: Dict = None) -> Dict:
        """Sincronizar datos entre servicios"""
        if not self.is_initialized or not self.sync_manager:
            raise RuntimeError("Integration not initialized")
        
        # Crear trabajo de sincronización
        job_result = await self.sync_manager.create_sync_job(
            job_name=f"{source}_to_{target}",
            source_service=source,
            target_service=target,
            sync_config=sync_config or {}
        )
        
        if job_result['status'] == 'success':
            # Ejecutar sincronización
            exec_result = await self.sync_manager.execute_sync_job(
                job_result['job_id'], 
                force=True
            )
            
            # Notificar resultado
            if exec_result.get('success'):
                await self.notification_handler.notify_sync_completion(
                    job_result['job_name'],
                    exec_result.get('stats', {}).get('items_synced', 0),
                    'success'
                )
            else:
                await self.notification_handler.notify_sync_completion(
                    job_result['job_name'],
                    exec_result.get('stats', {}).get('items_failed', 0),
                    'failed'
                )
            
            return exec_result
        
        return job_result
    
    async def get_system_stats(self) -> Dict:
        """Obtener estadísticas del sistema"""
        if not self.is_initialized:
            return {'error': 'Integration not initialized'}
        
        stats = {
            'system_status': self.system_status.copy(),
            'services': {},
            'performance': {},
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Obtener estadísticas de gestores
        if self.sync_manager:
            try:
                sync_status = await self.sync_manager.get_sync_status()
                stats['services']['sync'] = sync_status
            except Exception as e:
                logger.error(f"Error getting sync stats: {str(e)}")
                stats['services']['sync'] = {'error': str(e)}
        
        if self.notification_handler:
            try:
                notif_stats = await self.notification_handler.get_notification_stats()
                stats['services']['notifications'] = notif_stats
            except Exception as e:
                logger.error(f"Error getting notification stats: {str(e)}")
                stats['services']['notifications'] = {'error': str(e)}
        
        # Estadísticas de Graph API
        if self.graph_client:
            try:
                graph_stats = await self.graph_client.get_api_quota()
                stats['services']['graph_api'] = graph_stats
            except Exception as e:
                logger.error(f"Error getting Graph API stats: {str(e)}")
                stats['services']['graph_api'] = {'error': str(e)}
        
        return stats
    
    async def export_data(self, export_type: str = "json") -> Dict:
        """Exportar datos de configuración y estado"""
        if not self.is_initialized:
            return {'error': 'Integration not initialized'}
        
        export_data = {
            'export_type': export_type,
            'export_timestamp': datetime.utcnow().isoformat(),
            'system_info': {
                'version': '1.0.0',
                'initialized_at': self.system_status.get('initialized_at'),
                'last_health_check': self.system_status.get('last_health_check')
            },
            'configuration': {
                'graph_api_url': settings.graph_api_base_url,
                'services_enabled': list(self.system_status.get('services_status', {}).keys())
            },
            'current_status': self.system_status,
            'statistics': await self.get_system_stats()
        }
        
        return {
            'status': 'success',
            'export_data': export_data
        }
    
    # ==================== GESTIÓN DE CERRADO ====================
    
    async def shutdown(self) -> Dict:
        """Cerrar la integración de forma ordenada"""
        try:
            logger.info("Shutting down Microsoft 365 Integration...")
            
            shutdown_info = {
                'shutdown_started': datetime.utcnow().isoformat(),
                'components_shutdown': []
            }
            
            # Cerrar Graph API client
            if self.graph_client:
                await self.graph_client.close_session()
                shutdown_info['components_shutdown'].append('graph_client')
            
            # Cancelar tareas en segundo plano
            # (En implementación real, esto cancelaría las tareas del sync scheduler, etc.)
            
            # Actualizar estado
            self.is_initialized = False
            self.system_status.update({
                'shutdown_at': datetime.utcnow().isoformat(),
                'shutdown_completed': True
            })
            
            logger.info("Microsoft 365 Integration shutdown completed")
            
            shutdown_info['shutdown_completed'] = datetime.utcnow().isoformat()
            
            return {
                'status': 'success',
                'shutdown_info': shutdown_info
            }
            
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'shutdown_started': datetime.utcnow().isoformat()
            }
    
    # ==================== PROPERTIES ====================
    
    @property
    def word(self) -> WordOnlineAgent:
        """Acceso al agente de Word"""
        if not self.word_agent:
            raise RuntimeError("Word agent not initialized")
        return self.word_agent
    
    @property
    def excel(self) -> ExcelOnlineAgent:
        """Acceso al agente de Excel"""
        if not self.excel_agent:
            raise RuntimeError("Excel agent not initialized")
        return self.excel_agent
    
    @property
    def powerpoint(self) -> PowerPointAgent:
        """Acceso al agente de PowerPoint"""
        if not self.powerpoint_agent:
            raise RuntimeError("PowerPoint agent not initialized")
        return self.powerpoint_agent
    
    @property
    def outlook(self) -> OutlookAgent:
        """Acceso al agente de Outlook"""
        if not self.outlook_agent:
            raise RuntimeError("Outlook agent not initialized")
        return self.outlook_agent
    
    @property
    def onedrive(self) -> OneDriveAgent:
        """Acceso al agente de OneDrive"""
        if not self.onedrive_agent:
            raise RuntimeError("OneDrive agent not initialized")
        return self.onedrive_agent
    
    @property
    def teams(self) -> TeamsAgent:
        """Acceso al agente de Teams"""
        if not self.teams_agent:
            raise RuntimeError("Teams agent not initialized")
        return self.teams_agent
    
    @property
    def sync(self) -> SyncManager:
        """Acceso al gestor de sincronización"""
        if not self.sync_manager:
            raise RuntimeError("Sync manager not initialized")
        return self.sync_manager
    
    @property
    def licenses(self) -> LicenseManager:
        """Acceso al gestor de licencias"""
        if not self.license_manager:
            raise RuntimeError("License manager not initialized")
        return self.license_manager
    
    @property
    def notifications(self) -> NotificationHandler:
        """Acceso al gestor de notificaciones"""
        if not self.notification_handler:
            raise RuntimeError("Notification handler not initialized")
        return self.notification_handler


# Instancia global (patrón singleton para casos simples)
_integration_instance: Optional[Microsoft365Integration] = None

def get_integration(config: Optional[Dict] = None) -> Microsoft365Integration:
    """Obtener instancia global de la integración"""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = Microsoft365Integration(config)
    return _integration_instance