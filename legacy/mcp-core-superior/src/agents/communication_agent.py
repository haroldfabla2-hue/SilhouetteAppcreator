"""
Communication Agent MCP - Agente de Comunicación
Integra con servicios de email, messaging y notificaciones para envío,
recepción y gestión de comunicaciones empresariales.

Autor: Communication Agent
Versión: 1.0.0
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Importar la estructura base del agente MCP
try:
    from .base_agent_wrapper import BaseAgentWrapper, AgentCapability
except ImportError:
    BaseAgentWrapper = object
    AgentCapability = None


class CommunicationType(Enum):
    """Tipos de comunicación"""
    EMAIL = "email"
    SMS = "sms"
    PUSH_NOTIFICATION = "push_notification"
    WEBHOOK = "webhook"


class MessageStatus(Enum):
    """Estados de mensajes"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


@dataclass
class Contact:
    """Estructura de datos para contactos"""
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    """Estructura de datos para mensajes"""
    id: str
    type: CommunicationType
    sender: str
    recipients: List[str]
    subject: str = ""
    body: str = ""
    attachments: List[str] = field(default_factory=list)
    status: MessageStatus = MessageStatus.PENDING
    priority: str = "normal"  # low, normal, high, urgent
    scheduled_time: Optional[datetime] = None
    sent_time: Optional[datetime] = None
    delivered_time: Optional[datetime] = None
    read_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmailTemplate:
    """Estructura de datos para plantillas de email"""
    id: str
    name: str
    subject: str
    body: str
    variables: List[str] = field(default_factory=list)
    category: str = "general"
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class CommunicationResponse:
    """Respuesta consolidada de comunicación"""
    success: bool
    message_id: str
    action: str
    timestamp: float
    execution_time: float
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class CommunicationAgent(BaseAgentWrapper if BaseAgentWrapper else object):
    """
    Agente de Comunicación que maneja email, SMS, notificaciones
    y gestión de contactos empresariales.
    """
    
    def __init__(self):
        if BaseAgentWrapper:
            super().__init__(
                agent_name="CommunicationAgent",
                capabilities=[
                    AgentCapability.EMAIL_SENDING if AgentCapability else "email_sending",
                    AgentCapability.EMAIL_RECEIVING if AgentCapability else "email_receiving",
                    AgentCapability.MESSAGING if AgentCapability else "messaging",
                    AgentCapability.NOTIFICATION_SENDING if AgentCapability else "notification_sending",
                    AgentCapability.CONTACT_MANAGEMENT if AgentCapability else "contact_management",
                ],
                max_concurrent=10,
                timeout_seconds=60,
                retry_attempts=2
            )
        
        self.logger = logging.getLogger(__name__)
        self._contacts: Dict[str, Contact] = {}
        self._messages: Dict[str, Message] = {}
        self._templates: Dict[str, EmailTemplate] = {}
        self._outbox: List[Message] = []
        
        # Configuración SMTP simulada
        self.smtp_config = {
            "host": "smtp.example.com",
            "port": 587,
            "username": "noreply@company.com",
            "password": "***",
            "use_tls": True
        }
        
        # Cargar datos de ejemplo
        self._load_sample_data()
    
    async def _initialize(self):
        """Inicialización específica del agente"""
        await asyncio.sleep(0.1)
        self.logger.info("Communication Agent inicializado")
    
    def _load_sample_data(self):
        """Cargar datos de ejemplo"""
        # Contactos de ejemplo
        sample_contacts = [
            Contact(
                id="contact_1",
                name="Juan Pérez",
                email="juan.perez@company.com",
                phone="+34 600 123 456",
                company="Tech Solutions S.L.",
                department="Ventas",
                tags=["cliente", "vip"]
            ),
            Contact(
                id="contact_2",
                name="María García",
                email="maria.garcia@company.com",
                phone="+34 600 654 321",
                company="Tech Solutions S.L.",
                department="Marketing",
                tags=["empleado", "equipo"]
            ),
            Contact(
                id="contact_3",
                name="Carlos López",
                email="carlos.lopez@partner.com",
                phone="+34 600 789 012",
                company="Partner Corp",
                tags=["proveedor", "partner"]
            )
        ]
        
        for contact in sample_contacts:
            self._contacts[contact.id] = contact
        
        # Plantillas de ejemplo
        sample_templates = [
            EmailTemplate(
                id="template_1",
                name="Bienvenida",
                subject="Bienvenido/a a {{company_name}}",
                body="""
                Hola {{name}},
                
                Te damos la bienvenida a {{company_name}}. 
                Estamos encantados de tenerte con nosotros.
                
                Atentamente,
                El equipo de {{company_name}}
                """,
                variables=["name", "company_name"],
                category="customer_service"
            ),
            EmailTemplate(
                id="template_2",
                name="Recordatorio de reunión",
                subject="Recordatorio: Reunión el {{date}}",
                body="""
                Hola {{name}},
                
                Te recordamos que tienes una reunión programada para el {{date}} a las {{time}}.
                
                Lugar: {{location}}
                
                Agenda:
                {{agenda}}
                
                ¡Te esperamos!
                """,
                variables=["name", "date", "time", "location", "agenda"],
                category="meetings"
            )
        ]
        
        for template in sample_templates:
            self._templates[template.id] = template
    
    def _validate_email(self, email: str) -> bool:
        """Validar formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _substitute_variables(self, text: str, variables: Dict[str, str]) -> str:
        """Sustituir variables en texto usando formato {{variable}}"""
        result = text
        for var, value in variables.items():
            result = result.replace(f"{{{{var}}}}", value)
            result = result.replace(f"{{var}}", value)
        return result
    
    async def send_email(
        self,
        to_recipients: Union[str, List[str]],
        subject: str,
        body: str,
        cc_recipients: Optional[List[str]] = None,
        bcc_recipients: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        priority: str = "normal",
        template_id: Optional[str] = None,
        template_variables: Optional[Dict[str, str]] = None
    ) -> CommunicationResponse:
        """Enviar email"""
        start_time = time.time()
        
        try:
            # Normalizar destinatarios
            if isinstance(to_recipients, str):
                to_recipients = [to_recipients]
            if cc_recipients is None:
                cc_recipients = []
            if bcc_recipients is None:
                bcc_recipients = []
            if attachments is None:
                attachments = []
            
            # Validar emails
            all_recipients = to_recipients + cc_recipients + bcc_recipients
            invalid_emails = [email for email in all_recipients if not self._validate_email(email)]
            
            if invalid_emails:
                raise ValueError(f"Emails inválidos: {invalid_emails}")
            
            # Aplicar plantilla si se especifica
            if template_id and template_id in self._templates:
                template = self._templates[template_id]
                if template_variables:
                    subject = self._substitute_variables(template.subject, template_variables)
                    body = self._substitute_variables(template.body, template_variables)
            
            # Crear mensaje
            message_id = f"msg_{int(time.time() * 1000)}"
            
            message = Message(
                id=message_id,
                type=CommunicationType.EMAIL,
                sender=self.smtp_config["username"],
                recipients=all_recipients,
                subject=subject,
                body=body,
                attachments=attachments,
                status=MessageStatus.SENT,
                priority=priority
            )
            
            # Simular envío de email
            # En implementación real: usar smtplib o API de servicio de email
            await asyncio.sleep(0.1)  # Simular tiempo de envío
            
            message.sent_time = datetime.now()
            message.status = MessageStatus.DELIVERED
            message.delivered_time = datetime.now()
            
            # Guardar mensaje
            self._messages[message_id] = message
            self._outbox.append(message)
            
            self.logger.info(f"Email enviado exitosamente: {message_id}")
            
            return CommunicationResponse(
                success=True,
                message_id=message_id,
                action="send_email",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                details={
                    "recipients_count": len(all_recipients),
                    "has_attachments": len(attachments) > 0,
                    "priority": priority
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error enviando email: {str(e)}")
            return CommunicationResponse(
                success=False,
                message_id="",
                action="send_email",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def send_notification(
        self,
        recipients: List[str],
        title: str,
        message: str,
        notification_type: str = "info",
        scheduled_time: Optional[datetime] = None
    ) -> CommunicationResponse:
        """Enviar notificación push"""
        start_time = time.time()
        
        try:
            message_id = f"notif_{int(time.time() * 1000)}"
            
            notification = Message(
                id=message_id,
                type=CommunicationType.PUSH_NOTIFICATION,
                sender="system",
                recipients=recipients,
                subject=title,
                body=message,
                status=MessageStatus.SENT,
                scheduled_time=scheduled_time
            )
            
            # Simular envío de notificación
            await asyncio.sleep(0.05)
            
            notification.sent_time = datetime.now()
            notification.status = MessageStatus.DELIVERED
            notification.delivered_time = datetime.now()
            
            self._messages[message_id] = notification
            
            self.logger.info(f"Notificación enviada: {message_id}")
            
            return CommunicationResponse(
                success=True,
                message_id=message_id,
                action="send_notification",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                details={
                    "recipients_count": len(recipients),
                    "notification_type": notification_type
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error enviando notificación: {str(e)}")
            return CommunicationResponse(
                success=False,
                message_id="",
                action="send_notification",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def add_contact(
        self,
        name: str,
        email: str,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        department: Optional[str] = None,
        tags: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> CommunicationResponse:
        """Agregar nuevo contacto"""
        start_time = time.time()
        
        try:
            # Validar email
            if not self._validate_email(email):
                raise ValueError(f"Email inválido: {email}")
            
            # Generar ID único
            contact_id = f"contact_{int(time.time() * 1000)}"
            
            contact = Contact(
                id=contact_id,
                name=name,
                email=email,
                phone=phone,
                company=company,
                department=department,
                tags=tags or [],
                custom_fields=custom_fields or {}
            )
            
            self._contacts[contact_id] = contact
            
            self.logger.info(f"Contacto agregado: {contact_id}")
            
            return CommunicationResponse(
                success=True,
                message_id=contact_id,
                action="add_contact",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                details={
                    "contact_name": name,
                    "contact_email": email
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error agregando contacto: {str(e)}")
            return CommunicationResponse(
                success=False,
                message_id="",
                action="add_contact",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def search_contacts(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> CommunicationResponse:
        """Buscar contactos"""
        start_time = time.time()
        
        try:
            # Filtrar contactos por query y filtros
            results = []
            
            for contact in self._contacts.values():
                # Buscar en nombre, email, empresa
                searchable_text = f"{contact.name} {contact.email} {contact.company or ''}".lower()
                
                if query.lower() in searchable_text:
                    # Aplicar filtros adicionales
                    if filters:
                        match = True
                        
                        if "company" in filters and contact.company != filters["company"]:
                            match = False
                        
                        if "department" in filters and contact.department != filters["department"]:
                            match = False
                        
                        if "tags" in filters:
                            required_tags = filters["tags"]
                            if not any(tag in contact.tags for tag in required_tags):
                                match = False
                        
                        if match:
                            results.append(contact)
                    else:
                        results.append(contact)
            
            return CommunicationResponse(
                success=True,
                message_id="search_results",
                action="search_contacts",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                details={
                    "results_count": len(results),
                    "query": query,
                    "contacts": [contact.__dict__ for contact in results]
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error buscando contactos: {str(e)}")
            return CommunicationResponse(
                success=False,
                message_id="",
                action="search_contacts",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def get_message_status(self, message_id: str) -> CommunicationResponse:
        """Obtener estado de un mensaje"""
        start_time = time.time()
        
        try:
            if message_id in self._messages:
                message = self._messages[message_id]
                
                return CommunicationResponse(
                    success=True,
                    message_id=message_id,
                    action="get_message_status",
                    timestamp=time.time(),
                    execution_time=time.time() - start_time,
                    details={
                        "message": message.__dict__,
                        "status": message.status.value,
                        "sent_time": message.sent_time.isoformat() if message.sent_time else None,
                        "delivered_time": message.delivered_time.isoformat() if message.delivered_time else None,
                        "read_time": message.read_time.isoformat() if message.read_time else None
                    }
                )
            else:
                raise ValueError(f"Mensaje no encontrado: {message_id}")
                
        except Exception as e:
            self.logger.error(f"Error obteniendo estado de mensaje: {str(e)}")
            return CommunicationResponse(
                success=False,
                message_id=message_id,
                action="get_message_status",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def process_request(
        self,
        request: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Procesar request de comunicación
        
        Formatos soportados:
        - send_email: {"action": "send_email", "to": "test@example.com", "subject": "Test", "body": "Hello"}
        - send_notification: {"action": "send_notification", "recipients": ["user1"], "title": "Alert", "message": "Important"}
        - add_contact: {"action": "add_contact", "name": "John Doe", "email": "john@example.com"}
        - search_contacts: {"action": "search_contacts", "query": "john", "filters": {"company": "Tech Corp"}}
        - get_message_status: {"action": "get_message_status", "message_id": "msg_123"}
        """
        try:
            await self.ensure_initialized()
            
            action = request.get("action", "").lower()
            
            if action == "send_email":
                to_recipients = request.get("to", request.get("recipients", []))
                subject = request.get("subject", "")
                body = request.get("body", "")
                cc = request.get("cc", [])
                bcc = request.get("bcc", [])
                attachments = request.get("attachments", [])
                priority = request.get("priority", "normal")
                template_id = request.get("template_id")
                template_vars = request.get("template_variables", {})
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="send_email",
                        capability=AgentCapability.EMAIL_SENDING,
                        operation_func=self.send_email,
                        to_recipients=to_recipients,
                        subject=subject,
                        body=body,
                        cc_recipients=cc,
                        bcc_recipients=bcc,
                        attachments=attachments,
                        priority=priority,
                        template_id=template_id,
                        template_variables=template_vars
                    )
                else:
                    response = await self.send_email(
                        to_recipients, subject, body, cc, bcc, attachments, priority, template_id, template_vars
                    )
                
                return {
                    "success": response.success,
                    "message_id": response.message_id,
                    "details": response.details,
                    "error": response.error
                }
            
            elif action == "send_notification":
                recipients = request.get("recipients", [])
                title = request.get("title", "")
                message = request.get("message", "")
                notification_type = request.get("type", "info")
                
                if not recipients or not message:
                    raise ValueError("Recipients y message son requeridos")
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="send_notification",
                        capability=AgentCapability.NOTIFICATION_SENDING,
                        operation_func=self.send_notification,
                        recipients=recipients,
                        title=title,
                        message=message,
                        notification_type=notification_type
                    )
                else:
                    response = await self.send_notification(recipients, title, message, notification_type)
                
                return {
                    "success": response.success,
                    "message_id": response.message_id,
                    "details": response.details,
                    "error": response.error
                }
            
            elif action == "add_contact":
                name = request.get("name")
                email = request.get("email")
                phone = request.get("phone")
                company = request.get("company")
                department = request.get("department")
                tags = request.get("tags", [])
                custom_fields = request.get("custom_fields", {})
                
                if not name or not email:
                    raise ValueError("Name y email son requeridos")
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="add_contact",
                        capability=AgentCapability.CONTACT_MANAGEMENT,
                        operation_func=self.add_contact,
                        name=name,
                        email=email,
                        phone=phone,
                        company=company,
                        department=department,
                        tags=tags,
                        custom_fields=custom_fields
                    )
                else:
                    response = await self.add_contact(name, email, phone, company, department, tags, custom_fields)
                
                return {
                    "success": response.success,
                    "contact_id": response.message_id,
                    "details": response.details,
                    "error": response.error
                }
            
            elif action == "search_contacts":
                query = request.get("query", "")
                filters = request.get("filters", {})
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="search_contacts",
                        capability=AgentCapability.CONTACT_MANAGEMENT,
                        operation_func=self.search_contacts,
                        query=query,
                        filters=filters
                    )
                else:
                    response = await self.search_contacts(query, filters)
                
                return {
                    "success": response.success,
                    "results": response.details.get("contacts", []) if response.success else [],
                    "count": response.details.get("results_count", 0) if response.success else 0,
                    "error": response.error
                }
            
            elif action == "get_message_status":
                message_id = request.get("message_id")
                if not message_id:
                    raise ValueError("message_id requerido")
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="get_message_status",
                        capability=AgentCapability.MESSAGING,
                        operation_func=self.get_message_status,
                        message_id=message_id
                    )
                else:
                    response = await self.get_message_status(message_id)
                
                return {
                    "success": response.success,
                    "message_details": response.details.get("message", {}) if response.success else None,
                    "status": response.details.get("status") if response.success else None,
                    "error": response.error
                }
            
            else:
                raise ValueError(f"Acción no soportada: {action}")
                
        except Exception as e:
            self.logger.error(f"Error procesando request de comunicación: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del agente"""
        return {
            "total_contacts": len(self._contacts),
            "total_messages": len(self._messages),
            "total_templates": len(self._templates),
            "outbox_count": len(self._outbox),
            "agent_name": "CommunicationAgent",
            "available_actions": [
                "send_email",
                "send_notification",
                "add_contact", 
                "search_contacts",
                "get_message_status"
            ]
        }