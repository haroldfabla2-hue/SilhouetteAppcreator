"""
Google Gmail Agent - Agente Especializado para Google Gmail
Proporciona capacidades avanzadas de automatización de email, análisis de comunicaciones
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import email
import base64
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
import httpx

from .base_google_workspace_agent import (
    BaseGoogleWorkspaceAgent, 
    GoogleWorkspaceService, 
    GoogleWorkspaceConfig,
    ApiResponse
)
from ...core.exceptions import AgentException, handle_exceptions
from ...core.config import settings


class EmailLabel(Enum):
    """Etiquetas de Gmail"""
    INBOX = "INBOX"
    SENT = "SENT"
    DRAFT = "DRAFT"
    SPAM = "SPAM"
    TRASH = "TRASH"
    IMPORTANT = "IMPORTANT"
    STARRED = "STARRED"


class AttachmentType(Enum):
    """Tipos de adjunto"""
    PDF = "pdf"
    IMAGE = "image"
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    VIDEO = "video"
    ARCHIVE = "archive"
    OTHER = "other"


class EmailPriority(Enum):
    """Prioridad de email"""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class EmailMessage:
    """Mensaje de email"""
    id: str
    thread_id: str
    subject: str
    sender: str
    recipients: List[str]
    date: Optional[datetime] = None
    body: Optional[str] = None
    html_body: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    is_read: bool = False
    is_important: bool = False
    snippet: Optional[str] = None


@dataclass
class EmailFilter:
    """Filtro de búsqueda de email"""
    sender: Optional[str] = None
    recipient: Optional[str] = None
    subject: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    has_attachments: Optional[bool] = None
    is_unread: Optional[bool] = None
    labels: Optional[List[str]] = None
    query: Optional[str] = None
    max_results: int = 50


@dataclass
class EmailTemplate:
    """Plantilla de email"""
    name: str
    subject: str
    body: str
    html_body: Optional[str] = None
    signature: Optional[str] = None
    default_recipients: List[str] = field(default_factory=list)
    default_attachments: List[str] = field(default_factory=list)


@dataclass
class EmailStatistics:
    """Estadísticas de emails"""
    total_emails: int
    unread_emails: int
    sent_emails: int
    emails_with_attachments: int
    average_response_time: float
    most_frequent_sender: str
    recent_activity: List[Dict[str, Any]]


@dataclass
class ComposeRequest:
    """Request para composición de email"""
    to: List[str]
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    subject: str
    body: str
    html_body: Optional[str] = None
    attachments: Optional[List[str]] = None
    priority: EmailPriority = EmailPriority.NORMAL
    reply_to: Optional[str] = None
    template: Optional[EmailTemplate] = None


class GoogleGmailAgent(BaseGoogleWorkspaceAgent):
    """
    Agente Especializado para Google Gmail
    
    Funcionalidades:
    - Enviar emails automatizados
    - Leer y analizar mensajes
    - Gestionar etiquetas y filtros
    - Búsqueda avanzada de emails
    - Estadísticas de comunicación
    - Plantillas de email
    - Adjuntos y multimedia
    - Respuestas automáticas
    """
    
    def __init__(self, config: GoogleWorkspaceConfig):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.gmail_service = None
        self.email_templates: Dict[str, EmailTemplate] = {}
        self.auto_responses: Dict[str, EmailTemplate] = {}
        
        # Configurar capacidades específicas
        self.add_capability(AgentCapability.COMMUNICATION)
        self.add_capability(AgentCapability.AUTOMATION)
    
    async def initialize(self):
        """Inicializar servicio de Gmail"""
        await super().authenticate()
        self.gmail_service = await self.get_service(GoogleWorkspaceService.GMAIL)
    
    @handle_exceptions
    async def send_email(
        self,
        compose_request: ComposeRequest
    ) -> ApiResponse:
        """
        Enviar email
        
        Args:
            compose_request: Datos del email a enviar
            
        Returns:
            ApiResponse: Resultado del envío
        """
        try:
            # Crear mensaje
            message = MIMEMultipart()
            message['to'] = ', '.join(compose_request.to)
            
            if compose_request.cc:
                message['cc'] = ', '.join(compose_request.cc)
            
            if compose_request.bcc:
                message['bcc'] = ', '.join(compose_request.bcc)
            
            message['subject'] = compose_request.subject
            
            if compose_request.reply_to:
                message['reply-to'] = compose_request.reply_to
            
            # Cuerpo del email
            if compose_request.html_body:
                html_part = MIMEText(compose_request.html_body, 'html')
                message.attach(html_part)
                
                # Agregar versión texto plano
                text_part = MIMEText(compose_request.body, 'plain')
                message.attach(text_part)
            else:
                text_part = MIMEText(compose_request.body, 'plain')
                message.attach(text_part)
            
            # Agregar adjuntos
            if compose_request.attachments:
                for attachment_path in compose_request.attachments:
                    await self._attach_file(message, attachment_path)
            
            # Codificar mensaje
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Enviar email
            result = self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            self.logger.info(f"Email enviado: {compose_request.subject}")
            
            return ApiResponse(
                success=True,
                data={
                    'message_id': result.get('id'),
                    'thread_id': result.get('threadId'),
                    'to': compose_request.to,
                    'subject': compose_request.subject,
                    'sent_at': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            error_msg = f"Error enviando email: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def get_emails(
        self,
        email_filter: EmailFilter,
        format_type: str = 'full'
    ) -> ApiResponse:
        """
        Obtener emails según filtros
        
        Args:
            email_filter: Filtros de búsqueda
            format_type: Formato de respuesta (full, metadata, minimal)
            
        Returns:
            ApiResponse: Lista de emails
        """
        try:
            # Construir query de búsqueda
            query = self._build_search_query(email_filter)
            
            # Obtener mensajes
            result = self.gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=email_filter.max_results,
                labelIds=['INBOX'] if email_filter.labels else None
            ).execute()
            
            messages = result.get('messages', [])
            
            # Obtener detalles de cada mensaje
            email_list = []
            for message in messages:
                try:
                    email_data = self.gmail_service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format=format_type
                    ).execute()
                    
                    parsed_email = self._parse_email_message(email_data)
                    email_list.append(parsed_email)
                    
                except Exception as e:
                    self.logger.warning(f"Error procesando mensaje {message['id']}: {e}")
                    continue
            
            return ApiResponse(
                success=True,
                data={
                    'emails': email_list,
                    'total_count': len(email_list),
                    'query_used': query
                }
            )
            
        except Exception as e:
            error_msg = f"Error obteniendo emails: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def get_unread_emails(self, limit: int = 50) -> ApiResponse:
        """
        Obtener emails no leídos
        
        Args:
            limit: Límite de resultados
            
        Returns:
            ApiResponse: Lista de emails no leídos
        """
        try:
            filter_obj = EmailFilter(
                is_unread=True,
                max_results=limit
            )
            
            return await self.get_emails(filter_obj)
            
        except Exception as e:
            error_msg = f"Error obteniendo emails no leídos: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def search_emails(
        self,
        search_query: str,
        max_results: int = 50
    ) -> ApiResponse:
        """
        Búsqueda rápida de emails
        
        Args:
            search_query: Consulta de búsqueda
            max_results: Límite de resultados
            
        Returns:
            ApiResponse: Resultados de búsqueda
        """
        try:
            filter_obj = EmailFilter(
                query=search_query,
                max_results=max_results
            )
            
            return await self.get_emails(filter_obj)
            
        except Exception as e:
            error_msg = f"Error en búsqueda de emails: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def add_label(
        self,
        message_id: str,
        label_name: str
    ) -> ApiResponse:
        """
        Agregar etiqueta a email
        
        Args:
            message_id: ID del mensaje
            label_name: Nombre de la etiqueta
            
        Returns:
            ApiResponse: Resultado de la operación
        """
        try:
            # Crear etiqueta si no existe
            try:
                label = self.gmail_service.users().labels().create(
                    userId='me',
                    body={'name': label_name, 'labelListVisibility': 'labelShow'}
                ).execute()
            except HttpError:
                # Etiqueta ya existe, obtenerla
                labels = self.gmail_service.users().labels().list(userId='me').execute()
                label = next((l for l in labels.get('labels', []) if l['name'] == label_name), None)
            
            if not label:
                return ApiResponse(success=False, error="No se pudo crear/obtener etiqueta")
            
            # Agregar etiqueta al mensaje
            self.gmail_service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': [label['id']]}
            ).execute()
            
            return ApiResponse(
                success=True,
                data={
                    'message_id': message_id,
                    'label_added': label_name,
                    'label_id': label['id']
                }
            )
            
        except Exception as e:
            error_msg = f"Error agregando etiqueta: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def mark_as_read(self, message_id: str) -> ApiResponse:
        """
        Marcar email como leído
        
        Args:
            message_id: ID del mensaje
            
        Returns:
            ApiResponse: Resultado de la operación
        """
        try:
            self.gmail_service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            return ApiResponse(
                success=True,
                data={'message_id': message_id, 'marked_as_read': True}
            )
            
        except Exception as e:
            error_msg = f"Error marcando como leído: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def create_auto_response(
        self,
        trigger: str,
        response_template: EmailTemplate
    ) -> ApiResponse:
        """
        Crear respuesta automática
        
        Args:
            trigger: Trigger para activar respuesta
            response_template: Plantilla de respuesta
            
        Returns:
            ApiResponse: Resultado de la creación
        """
        try:
            self.auto_responses[trigger] = response_template
            
            # En un escenario real, esto crearía un filtro en Gmail
            self.logger.info(f"Respuesta automática creada: {trigger}")
            
            return ApiResponse(
                success=True,
                data={
                    'trigger': trigger,
                    'template_name': response_template.name,
                    'auto_response_created': True
                }
            )
            
        except Exception as e:
            error_msg = f"Error creando respuesta automática: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def get_email_statistics(self) -> ApiResponse:
        """
        Obtener estadísticas de emails
        
        Returns:
            ApiResponse: Estadísticas de comunicación
        """
        try:
            # Obtener emails recientes para análisis
            recent_filter = EmailFilter(
                date_from=datetime.now() - timedelta(days=30),
                max_results=1000
            )
            
            result = await self.get_emails(recent_filter)
            if not result.success:
                return result
            
            emails = result.data['emails']
            
            # Calcular estadísticas
            total_emails = len(emails)
            unread_emails = len([e for e in emails if not e.get('is_read', False)])
            sent_emails = len([e for e in emails if EmailLabel.SENT.value in e.get('labels', [])])
            emails_with_attachments = len([e for e in emails if e.get('attachments')])
            
            # Análisis de remitentes
            senders = [e.get('sender', '') for e in emails if e.get('sender')]
            most_frequent_sender = max(set(senders), key=senders.count) if senders else "N/A"
            
            # Actividad reciente (últimos 7 días)
            recent_cutoff = datetime.now() - timedelta(days=7)
            recent_activity = [
                {
                    'date': e.get('date', '').isoformat() if e.get('date') else '',
                    'sender': e.get('sender', ''),
                    'subject': e.get('subject', '')
                }
                for e in emails 
                if e.get('date') and e['date'] > recent_cutoff
            ]
            
            stats = EmailStatistics(
                total_emails=total_emails,
                unread_emails=unread_emails,
                sent_emails=sent_emails,
                emails_with_attachments=emails_with_attachments,
                average_response_time=0.0,  # Se calcularía con más análisis
                most_frequent_sender=most_frequent_sender,
                recent_activity=recent_activity
            )
            
            return ApiResponse(success=True, data=stats.__dict__)
            
        except Exception as e:
            error_msg = f"Error obteniendo estadísticas: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def send_template_email(
        self,
        template_name: str,
        recipients: List[str],
        subject_override: Optional[str] = None,
        body_override: Optional[str] = None
    ) -> ApiResponse:
        """
        Enviar email usando plantilla
        
        Args:
            template_name: Nombre de la plantilla
            recipients: Lista de destinatarios
            subject_override: Asunto personalizado
            body_override: Cuerpo personalizado
            
        Returns:
            ApiResponse: Resultado del envío
        """
        try:
            if template_name not in self.email_templates:
                return ApiResponse(success=False, error=f"Plantilla no encontrada: {template_name}")
            
            template = self.email_templates[template_name]
            
            compose_request = ComposeRequest(
                to=recipients,
                subject=subject_override or template.subject,
                body=body_override or template.body,
                html_body=template.html_body,
                attachments=template.default_attachments,
                reply_to=template.default_recipients[0] if template.default_recipients else None
            )
            
            return await self.send_email(compose_request)
            
        except Exception as e:
            error_msg = f"Error enviando email con plantilla: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def archive_emails(
        self,
        email_filter: EmailFilter
    ) -> ApiResponse:
        """
        Archivar emails que coinciden con filtros
        
        Args:
            email_filter: Filtros de emails a archivar
            
        Returns:
            ApiResponse: Resultado de la operación
        """
        try:
            # Obtener emails que coinciden
            result = await self.get_emails(email_filter)
            if not result.success:
                return result
            
            emails = result.data['emails']
            archived_count = 0
            
            for email_data in emails:
                try:
                    message_id = email_data['id']
                    # Remover de INBOX
                    self.gmail_service.users().messages().modify(
                        userId='me',
                        id=message_id,
                        body={'removeLabelIds': ['INBOX']}
                    ).execute()
                    archived_count += 1
                except Exception as e:
                    self.logger.warning(f"Error archivando email {email_data['id']}: {e}")
                    continue
            
            return ApiResponse(
                success=True,
                data={
                    'archived_count': archived_count,
                    'total_processed': len(emails)
                }
            )
            
        except Exception as e:
            error_msg = f"Error archivando emails: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    def _build_search_query(self, email_filter: EmailFilter) -> str:
        """Construir query de búsqueda para Gmail"""
        query_parts = []
        
        if email_filter.query:
            query_parts.append(email_filter.query)
        
        if email_filter.sender:
            query_parts.append(f"from:{email_filter.sender}")
        
        if email_filter.recipient:
            query_parts.append(f"to:{email_filter.recipient}")
        
        if email_filter.subject:
            query_parts.append(f"subject:{email_filter.subject}")
        
        if email_filter.date_from:
            query_parts.append(f"after:{email_filter.date_from.strftime('%Y/%m/%d')}")
        
        if email_filter.date_to:
            query_parts.append(f"before:{email_filter.date_to.strftime('%Y/%m/%d')}")
        
        if email_filter.has_attachments:
            query_parts.append("has:attachment")
        
        if email_filter.is_unread:
            query_parts.append("is:unread")
        
        if email_filter.labels:
            for label in email_filter.labels:
                query_parts.append(f"label:{label}")
        
        return ' '.join(query_parts)
    
    def _parse_email_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parsear mensaje de email de la API de Gmail"""
        headers = {h['name'].lower(): h['value'] for h in message_data.get('payload', {}).get('headers', [])}
        
        # Extraer información básica
        email_data = {
            'id': message_data['id'],
            'thread_id': message_data['threadId'],
            'subject': headers.get('subject', ''),
            'sender': headers.get('from', ''),
            'recipients': [headers.get('to', ''), headers.get('cc', '')],
            'date': headers.get('date', ''),
            'labels': message_data.get('labelIds', []),
            'is_read': 'UNREAD' not in message_data.get('labelIds', []),
            'is_important': 'IMPORTANT' in message_data.get('labelIds', []),
            'snippet': message_data.get('snippet', '')
        }
        
        # Parsear fecha
        date_str = headers.get('date', '')
        if date_str:
            try:
                # Parsear fecha RFC 2822
                from email.utils import parsedate_to_datetime
                email_data['date'] = parsedate_to_datetime(date_str)
            except:
                email_data['date'] = datetime.now()
        
        # Extraer cuerpo y adjuntos
        body_data = self._extract_email_body(message_data.get('payload', {}))
        email_data.update(body_data)
        
        return email_data
    
    def _extract_email_body(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer cuerpo y adjuntos del email"""
        result = {
            'body': '',
            'html_body': '',
            'attachments': []
        }
        
        if 'parts' in payload:
            # Email multipart
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain' and not result['body']:
                    result['body'] = self._decode_base64(part.get('body', {}).get('data', ''))
                elif part.get('mimeType') == 'text/html' and not result['html_body']:
                    result['html_body'] = self._decode_base64(part.get('body', {}).get('data', ''))
                elif part.get('filename'):
                    # Es un adjunto
                    result['attachments'].append({
                        'filename': part['filename'],
                        'mime_type': part.get('mimeType', ''),
                        'attachment_id': part.get('body', {}).get('attachmentId', '')
                    })
        elif payload.get('mimeType') == 'text/plain':
            result['body'] = self._decode_base64(payload.get('body', {}).get('data', ''))
        elif payload.get('mimeType') == 'text/html':
            result['html_body'] = self._decode_base64(payload.get('body', {}).get('data', ''))
        
        return result
    
    def _decode_base64(self, data: str) -> str:
        """Decodificar datos base64"""
        if not data:
            return ''
        
        try:
            return base64.urlsafe_b64decode(data + '==').decode('utf-8')
        except Exception:
            return ''
    
    async def _attach_file(self, message: MIMEMultipart, file_path: str):
        """Adjuntar archivo al email"""
        try:
            with open(file_path, 'rb') as f:
                attachment = MIMEApplication(f.read())
                attachment.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(file_path)}'
                )
                message.attach(attachment)
        except Exception as e:
            self.logger.warning(f"Error adjuntando archivo {file_path}: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar salud del agente Gmail"""
        try:
            # Verificar servicio base
            base_health = await super().health_check()
            
            if not base_health["healthy"]:
                return base_health
            
            # Test específico de Gmail API
            test_emails = await self.get_unread_emails(limit=5)
            
            if test_emails.success:
                return {
                    "healthy": True,
                    "service": "Google Gmail Agent",
                    "test_api_access": "passed",
                    "unread_emails_count": test_emails.data['total_count'],
                    "details": base_health
                }
            else:
                return {
                    "healthy": False,
                    "error": "Error accediendo a Gmail API",
                    "details": base_health
                }
                
        except Exception as e:
            return {
                "healthy": False,
                "error": f"Error en health check: {str(e)}",
                "service": "Google Gmail Agent"
            }