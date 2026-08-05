"""
Microsoft 365 - Notification Handler
Gestor de notificaciones y alertas del sistema
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import json

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Tipos de notificaciones"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    CRITICAL = "critical"

class NotificationChannel(Enum):
    """Canales de notificación"""
    EMAIL = "email"
    TEAMS = "teams"
    WEBHOOK = "webhook"
    LOG = "log"
    SMS = "sms"
    DASHBOARD = "dashboard"

class NotificationPriority(Enum):
    """Prioridades de notificación"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationHandler:
    """Gestor centralizado de notificaciones y alertas"""
    
    def __init__(self, graph_client, config: Dict = None):
        self.graph_client = graph_client
        self.config = config or {}
        
        # Configuración de notificaciones
        self.notification_queue: List[Dict] = []
        self.notification_handlers: Dict[NotificationChannel, Callable] = {}
        self.notification_rules: Dict[str, Dict] = {}
        self.notification_history: List[Dict] = []
        
        # Configuración de rate limiting
        self.max_notifications_per_hour = 100
        self.notification_cooldown = 300  # 5 minutos
        
        # Configuración de templates
        self.message_templates = self._load_message_templates()
        
        logger.info("Notification handler initialized")
    
    async def send_notification(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        channels: List[NotificationChannel] = None,
        recipients: List[str] = None,
        metadata: Dict = None,
        template: str = None
    ) -> Dict:
        """Enviar notificación"""
        try:
            # Configurar parámetros por defecto
            channels = channels or [NotificationChannel.LOG]
            recipients = recipients or []
            metadata = metadata or {}
            
            # Crear objeto de notificación
            notification = {
                'id': f"notif_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                'title': title,
                'message': message,
                'type': notification_type.value,
                'priority': priority.value,
                'channels': [ch.value for ch in channels],
                'recipients': recipients,
                'metadata': metadata,
                'template': template,
                'created_at': datetime.utcnow().isoformat(),
                'status': 'pending'
            }
            
            # Aplicar template si se especifica
            if template:
                notification.update(await self._apply_template(notification, template))
            
            # Añadir a cola
            self.notification_queue.append(notification)
            
            # Procesar inmediatamente si es de alta prioridad
            if priority in [NotificationPriority.HIGH, NotificationPriority.URGENT]:
                await self._process_notification(notification)
            else:
                await self._queue_notification(notification)
            
            logger.info(f"Notification queued: {notification['id']} - {title}")
            
            return {
                'status': 'success',
                'notification_id': notification['id'],
                'queued_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'title': title
            }
    
    async def _process_notification(self, notification: Dict):
        """Procesar notificación"""
        try:
            notification['status'] = 'processing'
            notification['processed_at'] = datetime.utcnow().isoformat()
            
            # Enviar por cada canal especificado
            for channel_name in notification['channels']:
                try:
                    channel = NotificationChannel(channel_name)
                    await self._send_to_channel(channel, notification)
                    notification['status'] = 'sent'
                except Exception as e:
                    logger.error(f"Error sending notification to channel {channel_name}: {str(e)}")
                    notification['status'] = 'failed'
                    notification['error'] = str(e)
            
            # Añadir a historial
            self.notification_history.append(notification)
            
            # Limitar historial a últimos 1000 registros
            if len(self.notification_history) > 1000:
                self.notification_history = self.notification_history[-1000:]
            
        except Exception as e:
            logger.error(f"Error processing notification {notification['id']}: {str(e)}")
            notification['status'] = 'failed'
            notification['error'] = str(e)
    
    async def _send_to_channel(self, channel: NotificationChannel, notification: Dict):
        """Enviar notificación a canal específico"""
        if channel in self.notification_handlers:
            handler = self.notification_handlers[channel]
            await handler(notification)
        else:
            # Usar handler por defecto
            if channel == NotificationChannel.EMAIL:
                await self._send_email_notification(notification)
            elif channel == NotificationChannel.TEAMS:
                await self._send_teams_notification(notification)
            elif channel == NotificationChannel.WEBHOOK:
                await self._send_webhook_notification(notification)
            elif channel == NotificationChannel.LOG:
                await self._send_log_notification(notification)
            elif channel == NotificationChannel.DASHBOARD:
                await self._send_dashboard_notification(notification)
            else:
                logger.warning(f"No handler found for channel: {channel.value}")
    
    async def _send_email_notification(self, notification: Dict):
        """Enviar notificación por email"""
        try:
            # En implementación real, usaría el agente de Outlook
            logger.info(f"Email notification: {notification['title']}")
            
            # Simular envío de email
            email_data = {
                'subject': f"[Microsoft365 Integration] {notification['title']}",
                'body': notification['message'],
                'to_recipients': notification['recipients'],
                'priority': notification['priority']
            }
            
            # Aquí se integraría con el agente de Outlook
            # await self.outlook_agent.send_email(**email_data)
            
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            raise
    
    async def _send_teams_notification(self, notification: Dict):
        """Enviar notificación a Microsoft Teams"""
        try:
            # En implementación real, usaría el agente de Teams
            logger.info(f"Teams notification: {notification['title']}")
            
            # Simular mensaje en Teams
            teams_message = {
                'channel_name': 'general',
                'message': f"🔔 **{notification['title']}**\n\n{notification['message']}",
                'mentions': notification['recipients']
            }
            
            # Aquí se integraría con el agente de Teams
            # await self.teams_agent.send_message(**teams_message)
            
        except Exception as e:
            logger.error(f"Error sending Teams notification: {str(e)}")
            raise
    
    async def _send_webhook_notification(self, notification: Dict):
        """Enviar notificación a webhook"""
        try:
            webhook_url = self.config.get('webhook_url')
            if not webhook_url:
                raise ValueError("Webhook URL not configured")
            
            payload = {
                'type': notification['type'],
                'title': notification['title'],
                'message': notification['message'],
                'timestamp': notification['created_at'],
                'priority': notification['priority'],
                'metadata': notification['metadata']
            }
            
            logger.info(f"Webhook notification: {notification['title']}")
            # Aquí se enviaría al webhook usando aiohttp
            
        except Exception as e:
            logger.error(f"Error sending webhook notification: {str(e)}")
            raise
    
    async def _send_log_notification(self, notification: Dict):
        """Enviar notificación a log"""
        try:
            log_message = f"[{notification['type'].upper()}] {notification['title']}: {notification['message']}"
            
            if notification['type'] == 'error':
                logger.error(log_message)
            elif notification['type'] == 'warning':
                logger.warning(log_message)
            elif notification['type'] == 'critical':
                logger.critical(log_message)
            elif notification['type'] == 'success':
                logger.info(log_message)
            else:
                logger.info(log_message)
                
        except Exception as e:
            logger.error(f"Error sending log notification: {str(e)}")
    
    async def _send_dashboard_notification(self, notification: Dict):
        """Enviar notificación a dashboard"""
        try:
            # Aquí se guardaría en base de datos para el dashboard
            dashboard_notification = {
                'notification_id': notification['id'],
                'title': notification['title'],
                'message': notification['message'],
                'type': notification['type'],
                'timestamp': notification['created_at'],
                'is_read': False
            }
            
            logger.info(f"Dashboard notification: {notification['title']}")
            
        except Exception as e:
            logger.error(f"Error sending dashboard notification: {str(e)}")
    
    async def _queue_notification(self, notification: Dict):
        """Colocar notificación en cola para procesamiento posterior"""
        # En implementación real, esto usaría una cola como Redis o RabbitMQ
        logger.debug(f"Notification queued: {notification['id']}")
        
        # Procesar cola cada minuto
        asyncio.create_task(self._process_notification_queue())
    
    async def _process_notification_queue(self):
        """Procesar cola de notificaciones pendientes"""
        while self.notification_queue:
            notification = self.notification_queue.pop(0)
            try:
                await self._process_notification(notification)
            except Exception as e:
                logger.error(f"Error processing queued notification: {str(e)}")
            
            # Delay entre notificaciones
            await asyncio.sleep(1)
    
    async def _apply_template(self, notification: Dict, template_name: str) -> Dict:
        """Aplicar template a notificación"""
        template = self.message_templates.get(template_name, {})
        
        if not template:
            return {}
        
        # Aplicar template
        formatted = notification.copy()
        
        # Formatear título y mensaje
        if 'title_template' in template:
            formatted['title'] = template['title_template'].format(**notification)
        
        if 'message_template' in template:
            formatted['message'] = template['message_template'].format(**notification)
        
        return formatted
    
    def _load_message_templates(self) -> Dict:
        """Cargar templates de mensajes"""
        return {
            'license_expiring': {
                'title_template': 'License Expiring Soon',
                'message_template': 'License {license_name} for user {user_name} expires in {days_remaining} days',
                'channels': ['email', 'dashboard'],
                'priority': 'high'
            },
            'sync_completed': {
                'title_template': 'Sync Job Completed',
                'message_template': 'Sync job {job_name} completed successfully. {items_synced} items synced.',
                'channels': ['log', 'dashboard'],
                'priority': 'medium'
            },
            'sync_failed': {
                'title_template': 'Sync Job Failed',
                'message_template': 'Sync job {job_name} failed: {error_message}',
                'channels': ['email', 'teams', 'log'],
                'priority': 'high'
            },
            'api_rate_limit': {
                'title_template': 'API Rate Limit Warning',
                'message_template': 'API rate limit approaching: {current_usage}/{max_usage} requests',
                'channels': ['email', 'dashboard'],
                'priority': 'medium'
            },
            'system_error': {
                'title_template': 'System Error',
                'message_template': 'System error occurred: {error_description}',
                'channels': ['email', 'teams', 'log'],
                'priority': 'critical'
            }
        }
    
    async def register_channel_handler(
        self,
        channel: NotificationChannel,
        handler_func: Callable
    ):
        """Registrar handler personalizado para canal"""
        self.notification_handlers[channel] = handler_func
        logger.info(f"Custom handler registered for channel: {channel.value}")
    
    async def create_notification_rule(
        self,
        rule_name: str,
        condition: Callable,
        notification_config: Dict
    ):
        """Crear regla de notificación automática"""
        self.notification_rules[rule_name] = {
            'condition': condition,
            'config': notification_config,
            'created_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Notification rule created: {rule_name}")
    
    async def check_and_send_notifications(self):
        """Verificar condiciones y enviar notificaciones automáticas"""
        try:
            for rule_name, rule in self.notification_rules.items():
                try:
                    if await rule['condition']():
                        config = rule['config']
                        await self.send_notification(
                            title=config['title'],
                            message=config['message'],
                            notification_type=NotificationType(config.get('type', 'info')),
                            priority=NotificationPriority(config.get('priority', 'medium')),
                            channels=[NotificationChannel(ch) for ch in config.get('channels', ['log'])],
                            recipients=config.get('recipients', [])
                        )
                except Exception as e:
                    logger.error(f"Error evaluating notification rule {rule_name}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error checking notification rules: {str(e)}")
    
    async def get_notification_history(
        self,
        limit: int = 50,
        notification_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """Obtener historial de notificaciones"""
        try:
            filtered_history = self.notification_history.copy()
            
            # Filtrar por tipo
            if notification_type:
                filtered_history = [
                    n for n in filtered_history 
                    if n['type'] == notification_type
                ]
            
            # Filtrar por fecha
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
                filtered_history = [
                    n for n in filtered_history 
                    if datetime.fromisoformat(n['created_at']) >= start_dt
                ]
            
            if end_date:
                end_dt = datetime.fromisoformat(end_date)
                filtered_history = [
                    n for n in filtered_history 
                    if datetime.fromisoformat(n['created_at']) <= end_dt
                ]
            
            # Ordenar por fecha y limitar
            filtered_history.sort(key=lambda x: x['created_at'], reverse=True)
            return filtered_history[:limit]
            
        except Exception as e:
            logger.error(f"Error getting notification history: {str(e)}")
            return []
    
    async def get_notification_stats(self) -> Dict:
        """Obtener estadísticas de notificaciones"""
        try:
            total_notifications = len(self.notification_history)
            by_type = {}
            by_status = {}
            recent_24h = 0
            
            cutoff_24h = datetime.utcnow() - timedelta(hours=24)
            
            for notification in self.notification_history:
                # Por tipo
                ntype = notification['type']
                by_type[ntype] = by_type.get(ntype, 0) + 1
                
                # Por estado
                status = notification.get('status', 'unknown')
                by_status[status] = by_status.get(status, 0) + 1
                
                # Últimas 24 horas
                created_at = datetime.fromisoformat(notification['created_at'])
                if created_at >= cutoff_24h:
                    recent_24h += 1
            
            return {
                'total_notifications': total_notifications,
                'recent_24h': recent_24h,
                'by_type': by_type,
                'by_status': by_status,
                'pending_queue': len(self.notification_queue),
                'active_rules': len(self.notification_rules),
                'stats_generated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting notification stats: {str(e)}")
            return {'error': str(e)}
    
    async def clear_notification_history(self, days_old: int = 30) -> int:
        """Limpiar historial de notificaciones antiguas"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            original_count = len(self.notification_history)
            self.notification_history = [
                n for n in self.notification_history
                if datetime.fromisoformat(n['created_at']) >= cutoff_date
            ]
            
            cleared_count = original_count - len(self.notification_history)
            logger.info(f"Cleared {cleared_count} old notifications")
            
            return cleared_count
            
        except Exception as e:
            logger.error(f"Error clearing notification history: {str(e)}")
            return 0
    
    # Métodos de utilidad para casos comunes
    async def notify_sync_completion(
        self,
        job_name: str,
        items_synced: int,
        status: str = "success"
    ):
        """Notificar finalización de sync"""
        if status == "success":
            await self.send_notification(
                title="Sync Completed",
                message=f"Sync job '{job_name}' completed successfully. {items_synced} items synced.",
                notification_type=NotificationType.SUCCESS,
                priority=NotificationPriority.MEDIUM,
                template="sync_completed"
            )
        else:
            await self.send_notification(
                title="Sync Failed",
                message=f"Sync job '{job_name}' failed. {items_synced} items processed before failure.",
                notification_type=NotificationType.ERROR,
                priority=NotificationPriority.HIGH,
                template="sync_failed"
            )
    
    async def notify_license_warning(self, user_name: str, license_name: str, days_remaining: int):
        """Notificar advertencia de licencia"""
        await self.send_notification(
            title="License Expiring",
            message=f"License {license_name} for {user_name} expires in {days_remaining} days",
            notification_type=NotificationType.WARNING,
            priority=NotificationPriority.HIGH,
            template="license_expiring"
        )
    
    async def notify_system_error(self, error_description: str):
        """Notificar error del sistema"""
        await self.send_notification(
            title="System Error",
            message=error_description,
            notification_type=NotificationType.CRITICAL,
            priority=NotificationPriority.URGENT,
            template="system_error",
            channels=[NotificationChannel.EMAIL, NotificationChannel.TEAMS, NotificationChannel.LOG]
        )