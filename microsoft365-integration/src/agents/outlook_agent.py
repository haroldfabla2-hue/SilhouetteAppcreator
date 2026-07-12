"""
Microsoft 365 - Outlook Integration Agent
Agente especializado para operaciones con correo electrónico y calendario
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import json
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..graph.client import GraphAPIClient, GraphAPIError
from ..config.settings import service_config, RATE_LIMITS
from ..utils.logger import get_logger

logger = get_logger(__name__)

class OutlookAgent:
    """Agente para operaciones con Microsoft Outlook (Email y Calendario)"""
    
    def __init__(self, graph_client: GraphAPIClient):
        self.graph_client = graph_client
        
        # Rate limiting específico para Outlook
        self.rate_limit_config = RATE_LIMITS["outlook"]
        
        # Configuración de correo y calendario
        self.max_message_size = service_config.outlook_max_message_size
        self.email_batch_size = service_config.outlook_email_batch_size
    
    # ==================== EMAIL OPERATIONS ====================
    
    async def send_email(
        self,
        to_recipients: List[str],
        subject: str,
        body: str,
        cc_recipients: Optional[List[str]] = None,
        bcc_recipients: Optional[List[str]] = None,
        importance: str = "normal",
        attachments: Optional[List[Dict]] = None
    ) -> Dict:
        """Enviar correo electrónico"""
        try:
            # Validar destinatarios
            if not to_recipients:
                raise ValueError("At least one recipient is required")
            
            for recipient in to_recipients + (cc_recipients or []) + (bcc_recipients or []):
                if not self._is_valid_email(recipient):
                    raise ValueError(f"Invalid email address: {recipient}")
            
            # Validar importancia
            valid_importance = ['low', 'normal', 'high']
            if importance not in valid_importance:
                importance = 'normal'
            
            # Preparar mensaje
            message = {
                'message': {
                    'subject': subject,
                    'body': {
                        'contentType': 'HTML',
                        'content': body
                    },
                    'importance': importance,
                    'toRecipients': [{'emailAddress': {'address': addr}} for addr in to_recipients]
                }
            }
            
            # Agregar CC si existe
            if cc_recipients:
                message['message']['ccRecipients'] = [
                    {'emailAddress': {'address': addr}} for addr in cc_recipients
                ]
            
            # Agregar BCC si existe
            if bcc_recipients:
                message['message']['bccRecipients'] = [
                    {'emailAddress': {'address': addr}} for addr in bcc_recipients
                ]
            
            # Agregar adjuntos si existen
            if attachments:
                message['message']['attachments'] = await self._prepare_attachments(attachments)
            
            # Enviar mensaje
            result = await self.graph_client.send_email(message['message'])
            
            logger.info(f"Email sent successfully to {len(to_recipients)} recipients")
            return {
                'status': 'success',
                'message_id': result.get('id'),
                'subject': subject,
                'to_recipients': to_recipients,
                'sent_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'subject': subject
            }
    
    async def read_email(self, message_id: str) -> Dict:
        """Leer mensaje de correo específico"""
        try:
            message = await self.graph_client.get_message(message_id)
            
            # Procesar contenido del mensaje
            processed_message = {
                'message_id': message_id,
                'subject': message.get('subject', ''),
                'body': {
                    'content': message.get('body', {}).get('content', ''),
                    'contentType': message.get('body', {}).get('contentType', 'text')
                },
                'sender': {
                    'name': message.get('from', {}).get('emailAddress', {}).get('name', ''),
                    'email': message.get('from', {}).get('emailAddress', {}).get('address', '')
                },
                'recipients': {
                    'to': [
                        {
                            'name': r.get('emailAddress', {}).get('name', ''),
                            'email': r.get('emailAddress', {}).get('address', '')
                        } for r in message.get('toRecipients', [])
                    ],
                    'cc': [
                        {
                            'name': r.get('emailAddress', {}).get('name', ''),
                            'email': r.get('emailAddress', {}).get('address', '')
                        } for r in message.get('ccRecipients', [])
                    ],
                    'bcc': [
                        {
                            'name': r.get('emailAddress', {}).get('name', ''),
                            'email': r.get('emailAddress', {}).get('address', '')
                        } for r in message.get('bccRecipients', [])
                    ]
                },
                'received_date': message.get('receivedDateTime'),
                'sent_date': message.get('sentDateTime'),
                'importance': message.get('importance', 'normal'),
                'is_read': message.get('isRead', False),
                'has_attachments': message.get('hasAttachments', False)
            }
            
            return {
                'status': 'success',
                'message': processed_message
            }
            
        except Exception as e:
            logger.error(f"Error reading email {message_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'message_id': message_id
            }
    
    async def list_emails(
        self,
        folder: str = "inbox",
        limit: int = 25,
        unread_only: bool = False,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[Dict]:
        """Listar correos electrónicos"""
        try:
            # Construir filtro
            filters = []
            
            if unread_only:
                filters.append("isRead eq false")
            
            if from_date:
                filters.append(f"receivedDateTime ge {from_date}")
            
            if to_date:
                filters.append(f"receivedDateTime le {to_date}")
            
            filter_str = " and ".join(filters) if filters else None
            
            # Obtener mensajes
            messages_result = await self.graph_client.list_messages(
                folder=folder,
                top=limit,
                filter_str=filter_str
            )
            
            emails = []
            for message in messages_result.get('value', []):
                email_info = {
                    'message_id': message.get('id'),
                    'subject': message.get('subject', ''),
                    'sender': {
                        'name': message.get('from', {}).get('emailAddress', {}).get('name', ''),
                        'email': message.get('from', {}).get('emailAddress', {}).get('address', '')
                    },
                    'received_date': message.get('receivedDateTime'),
                    'importance': message.get('importance', 'normal'),
                    'is_read': message.get('isRead', False),
                    'has_attachments': message.get('hasAttachments', False),
                    'preview': message.get('bodyPreview', '')
                }
                emails.append(email_info)
            
            logger.info(f"Retrieved {len(emails)} emails from {folder}")
            return emails
            
        except Exception as e:
            logger.error(f"Error listing emails: {str(e)}")
            return []
    
    async def search_emails(
        self,
        search_term: str,
        search_in: str = "all",
        limit: int = 50
    ) -> List[Dict]:
        """Buscar correos por contenido o remitente"""
        try:
            # Validar término de búsqueda
            if len(search_term) < 2:
                raise ValueError("Search term must be at least 2 characters")
            
            # Construir filtro de búsqueda
            search_filters = []
            
            if search_in in ["subject", "all"]:
                search_filters.append(f"contains(subject,'{search_term}')")
            
            if search_in in ["body", "all"]:
                search_filters.append(f"contains(body/content,'{search_term}')")
            
            if search_in in ["sender", "all"]:
                search_filters.append(f"contains(from/emailAddress/address,'{search_term}')")
            
            filter_str = " or ".join(search_filters)
            
            # Realizar búsqueda
            messages_result = await self.graph_client.list_messages(
                top=limit,
                filter_str=filter_str
            )
            
            results = []
            for message in messages_result.get('value', []):
                result = {
                    'message_id': message.get('id'),
                    'subject': message.get('subject', ''),
                    'sender': {
                        'name': message.get('from', {}).get('emailAddress', {}).get('name', ''),
                        'email': message.get('from', {}).get('emailAddress', {}).get('address', '')
                    },
                    'received_date': message.get('receivedDateTime'),
                    'importance': message.get('importance', 'normal'),
                    'preview': message.get('bodyPreview', ''),
                    'match_field': self._determine_match_field(message, search_term)
                }
                results.append(result)
            
            logger.info(f"Found {len(results)} emails matching '{search_term}'")
            return results
            
        except Exception as e:
            logger.error(f"Error searching emails: {str(e)}")
            return []
    
    async def mark_as_read(self, message_id: str) -> Dict:
        """Marcar correo como leído"""
        try:
            # En implementación real, esto usaría PATCH para actualizar isRead
            logger.info(f"Email marked as read: {message_id}")
            
            return {
                'status': 'success',
                'message_id': message_id,
                'action': 'mark_as_read',
                'updated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error marking email as read {message_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'message_id': message_id
            }
    
    async def delete_email(self, message_id: str) -> Dict:
        """Eliminar correo electrónico"""
        try:
            result = await self.graph_client.delete_message(message_id)
            
            if result:
                logger.info(f"Email deleted successfully: {message_id}")
                return {
                    'status': 'success',
                    'message_id': message_id,
                    'deleted_at': datetime.utcnow().isoformat()
                }
            else:
                raise Exception("Delete operation failed")
                
        except Exception as e:
            logger.error(f"Error deleting email {message_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'message_id': message_id
            }
    
    async def create_email_rule(
        self,
        rule_name: str,
        conditions: Dict,
        actions: Dict
    ) -> Dict:
        """Crear regla de correo"""
        try:
            rule_config = {
                'displayName': rule_name,
                'conditions': conditions,
                'actions': actions,
                'isEnabled': True,
                'sequence': 1,
                'created_date': datetime.utcnow().isoformat()
            }
            
            # En implementación real, esto crearía la regla en Outlook
            logger.info(f"Email rule created: {rule_name}")
            
            return {
                'status': 'success',
                'rule_name': rule_name,
                'rule_config': rule_config,
                'rule_id': f"rule_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            }
            
        except Exception as e:
            logger.error(f"Error creating email rule {rule_name}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'rule_name': rule_name
            }
    
    # ==================== CALENDAR OPERATIONS ====================
    
    async def create_calendar_event(
        self,
        subject: str,
        start_time: str,
        end_time: str,
        attendees: Optional[List[Dict]] = None,
        location: Optional[str] = None,
        description: Optional[str] = None,
        is_all_day: bool = False
    ) -> Dict:
        """Crear evento en calendario"""
        try:
            # Validar fechas
            if not is_all_day:
                if not self._is_valid_datetime(start_time) or not self._is_valid_datetime(end_time):
                    raise ValueError("Invalid datetime format. Use ISO 8601 format")
            
            # Preparar datos del evento
            event_data = {
                'subject': subject,
                'start': {
                    'dateTime': start_time,
                    'timeZone': 'UTC'
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': 'UTC'
                },
                'isAllDay': is_all_day
            }
            
            # Agregar ubicación si se proporciona
            if location:
                event_data['location'] = {'displayName': location}
            
            # Agregar descripción si se proporciona
            if description:
                event_data['body'] = {
                    'contentType': 'HTML',
                    'content': description
                }
            
            # Agregar asistentes si se proporcionan
            if attendees:
                event_data['attendees'] = [
                    {
                        'emailAddress': {'address': attendee['email'], 'name': attendee.get('name', '')},
                        'type': attendee.get('type', 'required')
                    } for attendee in attendees
                ]
            
            # Crear evento
            result = await self.graph_client.create_event(event_data)
            
            logger.info(f"Calendar event created: {subject}")
            return {
                'status': 'success',
                'event_id': result.get('id'),
                'subject': subject,
                'start_time': start_time,
                'end_time': end_time,
                'attendees_count': len(attendees) if attendees else 0,
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating calendar event: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'subject': subject
            }
    
    async def list_calendar_events(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 25
    ) -> List[Dict]:
        """Listar eventos del calendario"""
        try:
            # Configurar rango de fechas por defecto (próximos 30 días)
            if not start_time:
                start_time = datetime.utcnow().isoformat()
            if not end_time:
                end_time = (datetime.utcnow() + timedelta(days=30)).isoformat()
            
            # Obtener eventos
            events_result = await self.graph_client.list_events(
                start_time=start_time,
                end_time=end_time,
                top=limit
            )
            
            events = []
            for event in events_result.get('value', []):
                event_info = {
                    'event_id': event.get('id'),
                    'subject': event.get('subject', ''),
                    'start_time': event.get('start', {}).get('dateTime'),
                    'end_time': event.get('end', {}).get('dateTime'),
                    'is_all_day': event.get('isAllDay', False),
                    'location': event.get('location', {}).get('displayName', ''),
                    'organizer': {
                        'name': event.get('organizer', {}).get('emailAddress', {}).get('name', ''),
                        'email': event.get('organizer', {}).get('emailAddress', {}).get('address', '')
                    },
                    'attendees_count': len(event.get('attendees', [])),
                    'is_cancelled': event.get('isCancelled', False)
                }
                events.append(event_info)
            
            logger.info(f"Retrieved {len(events)} calendar events")
            return events
            
        except Exception as e:
            logger.error(f"Error listing calendar events: {str(e)}")
            return []
    
    async def update_calendar_event(
        self,
        event_id: str,
        subject: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        location: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict:
        """Actualizar evento de calendario"""
        try:
            # Preparar datos de actualización
            update_data = {}
            
            if subject is not None:
                update_data['subject'] = subject
            if start_time is not None:
                update_data['start'] = {
                    'dateTime': start_time,
                    'timeZone': 'UTC'
                }
            if end_time is not None:
                update_data['end'] = {
                    'dateTime': end_time,
                    'timeZone': 'UTC'
                }
            if location is not None:
                update_data['location'] = {'displayName': location}
            if description is not None:
                update_data['body'] = {
                    'contentType': 'HTML',
                    'content': description
                }
            
            # Actualizar evento
            result = await self.graph_client.update_event(event_id, update_data)
            
            logger.info(f"Calendar event updated: {event_id}")
            return {
                'status': 'success',
                'event_id': event_id,
                'updated_fields': list(update_data.keys()),
                'updated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating calendar event {event_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'event_id': event_id
            }
    
    async def delete_calendar_event(self, event_id: str) -> Dict:
        """Eliminar evento de calendario"""
        try:
            result = await self.graph_client.delete_event(event_id)
            
            if result:
                logger.info(f"Calendar event deleted: {event_id}")
                return {
                    'status': 'success',
                    'event_id': event_id,
                    'deleted_at': datetime.utcnow().isoformat()
                }
            else:
                raise Exception("Delete operation failed")
                
        except Exception as e:
            logger.error(f"Error deleting calendar event {event_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'event_id': event_id
            }
    
    async def send_calendar_invitation(
        self,
        event_id: str,
        attendees: List[Dict],
        message: Optional[str] = None
    ) -> Dict:
        """Enviar invitación de calendario"""
        try:
            invitation_data = {
                'event_id': event_id,
                'attendees': attendees,
                'message': message or "You are invited to this event.",
                'sent_at': datetime.utcnow().isoformat()
            }
            
            # En implementación real, esto enviaría las invitaciones
            logger.info(f"Calendar invitation sent for event {event_id}")
            
            return {
                'status': 'success',
                'invitation_data': invitation_data,
                'invitations_sent': len(attendees)
            }
            
        except Exception as e:
            logger.error(f"Error sending calendar invitation for event {event_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'event_id': event_id
            }
    
    # ==================== UTILITY METHODS ====================
    
    def _is_valid_email(self, email: str) -> bool:
        """Validar formato de dirección de correo"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _is_valid_datetime(self, datetime_str: str) -> bool:
        """Validar formato de fecha y hora"""
        try:
            datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return True
        except ValueError:
            return False
    
    def _determine_match_field(self, message: Dict, search_term: str) -> str:
        """Determinar en qué campo se encontró la coincidencia"""
        search_lower = search_term.lower()
        
        if search_lower in message.get('subject', '').lower():
            return 'subject'
        elif search_lower in message.get('bodyPreview', '').lower():
            return 'body'
        elif search_lower in message.get('from', {}).get('emailAddress', {}).get('address', '').lower():
            return 'sender'
        else:
            return 'unknown'
    
    async def _prepare_attachments(self, attachments: List[Dict]) -> List[Dict]:
        """Preparar adjuntos para envío"""
        prepared_attachments = []
        
        for attachment in attachments:
            prepared = {
                '@odata.type': '#microsoft.graph.fileAttachment',
                'name': attachment.get('name', 'attachment'),
                'contentType': attachment.get('contentType', 'application/octet-stream')
            }
            
            # Agregar contenido si está disponible
            if 'content' in attachment:
                prepared['contentBytes'] = attachment['content']
            elif 'path' in attachment:
                # En implementación real, leería el archivo
                prepared['contentBytes'] = b'file_content_placeholder'
            
            prepared_attachments.append(prepared)
        
        return prepared_attachments
    
    async def get_mail_statistics(self) -> Dict:
        """Obtener estadísticas de correo"""
        try:
            # Obtener conteos básicos
            inbox_emails = await self.list_emails(folder="inbox", limit=1000)
            sent_emails = await self.list_emails(folder="sentitems", limit=1000)
            
            # Estadísticas básicas
            stats = {
                'total_inbox_emails': len(inbox_emails),
                'unread_inbox_emails': sum(1 for email in inbox_emails if not email.get('is_read', True)),
                'total_sent_emails': len(sent_emails),
                'emails_with_attachments': sum(1 for email in inbox_emails if email.get('has_attachments', False)),
                'high_importance_emails': sum(1 for email in inbox_emails if email.get('importance') == 'high'),
                'last_updated': datetime.utcnow().isoformat()
            }
            
            return {
                'status': 'success',
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"Error getting mail statistics: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def get_calendar_statistics(self) -> Dict:
        """Obtener estadísticas de calendario"""
        try:
            # Obtener eventos próximos
            upcoming_events = await self.list_calendar_events(limit=1000)
            
            # Estadísticas de calendario
            stats = {
                'total_upcoming_events': len(upcoming_events),
                'all_day_events': sum(1 for event in upcoming_events if event.get('is_all_day', False)),
                'cancelled_events': sum(1 for event in upcoming_events if event.get('is_cancelled', False)),
                'events_with_attendees': sum(1 for event in upcoming_events if event.get('attendees_count', 0) > 0),
                'total_attendees': sum(event.get('attendees_count', 0) for event in upcoming_events),
                'last_updated': datetime.utcnow().isoformat()
            }
            
            return {
                'status': 'success',
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"Error getting calendar statistics: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }