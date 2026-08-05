"""
Tests unitarios para Communication Agent
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch
import sys
import os

# Añadir el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.communication_agent import (
    CommunicationAgent, Contact, Message, EmailTemplate, CommunicationType, MessageStatus
)


class TestCommunicationAgent:
    """Tests para CommunicationAgent"""
    
    @pytest.fixture
    async def agent(self):
        """Fixture para crear agente de prueba"""
        agent = CommunicationAgent()
        await agent._initialize()
        return agent
    
    def test_agent_initialization(self, agent):
        """Test inicialización del agente"""
        assert agent.agent_name == "CommunicationAgent"
        assert agent.is_ready
        assert len(agent.capabilities) > 0
        assert len(agent._contacts) > 0  # Debe cargar datos de ejemplo
        assert len(agent._templates) > 0  # Debe cargar plantillas de ejemplo
    
    def test_validate_email_valid(self, agent):
        """Test validación de emails válidos"""
        valid_emails = [
            "test@example.com",
            "user.name@company.co.uk",
            "user+tag@domain.com"
        ]
        
        for email in valid_emails:
            assert agent._validate_email(email)
    
    def test_validate_email_invalid(self, agent):
        """Test validación de emails inválidos"""
        invalid_emails = [
            "invalidemail",
            "@domain.com",
            "user@",
            "user@domain",
            "user@.com"
        ]
        
        for email in invalid_emails:
            assert not agent._validate_email(email)
    
    def test_substitute_variables(self, agent):
        """Test sustitución de variables en texto"""
        template = "Hola {{name}}, bienvenido a {{company_name}}"
        variables = {
            "name": "Juan",
            "company_name": "Tech Corp"
        }
        
        result = agent._substitute_variables(template, variables)
        
        assert "Juan" in result
        assert "Tech Corp" in result
        assert "{{name}}" not in result
        assert "{{company_name}}" not in result
    
    @pytest.mark.asyncio
    async def test_send_email_basic(self, agent):
        """Test envío básico de email"""
        response = await agent.send_email(
            to_recipients="test@example.com",
            subject="Test Email",
            body="Este es un email de prueba"
        )
        
        assert response.success
        assert response.action == "send_email"
        assert response.message_id is not None
        assert response.details["recipients_count"] == 1
    
    @pytest.mark.asyncio
    async def test_send_email_multiple_recipients(self, agent):
        """Test envío de email a múltiples destinatarios"""
        recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]
        
        response = await agent.send_email(
            to_recipients=recipients,
            subject="Email Grupal",
            body="Este email es para múltiples usuarios"
        )
        
        assert response.success
        assert response.details["recipients_count"] == 3
    
    @pytest.mark.asyncio
    async def test_send_email_with_template(self, agent):
        """Test envío de email con plantilla"""
        response = await agent.send_email(
            to_recipients="newuser@example.com",
            subject="",
            body="",
            template_id="template_1",
            template_variables={
                "name": "Ana",
                "company_name": "Mi Empresa"
            }
        )
        
        assert response.success
        assert "Ana" in agent._messages[response.message_id].body
        assert "Mi Empresa" in agent._messages[response.message_id].body
    
    @pytest.mark.asyncio
    async def test_send_email_invalid_recipients(self, agent):
        """Test envío de email con destinatarios inválidos"""
        response = await agent.send_email(
            to_recipients="invalid-email",
            subject="Test",
            body="Test"
        )
        
        assert not response.success
        assert "Emails inválidos" in response.error
    
    @pytest.mark.asyncio
    async def test_send_notification(self, agent):
        """Test envío de notificación"""
        response = await agent.send_notification(
            recipients=["user1", "user2"],
            title="Alerta Importante",
            message="Hay una actualización del sistema disponible",
            notification_type="warning"
        )
        
        assert response.success
        assert response.action == "send_notification"
        assert response.message_id is not None
        assert response.details["recipients_count"] == 2
        assert response.details["notification_type"] == "warning"
    
    @pytest.mark.asyncio
    async def test_add_contact(self, agent):
        """Test agregar nuevo contacto"""
        initial_count = len(agent._contacts)
        
        response = await agent.add_contact(
            name="Pedro Martínez",
            email="pedro@company.com",
            phone="+34 600 999 888",
            company="Tech Solutions S.L.",
            department="Desarrollo",
            tags=["empleado", "desarrollador"]
        )
        
        assert response.success
        assert len(agent._contacts) == initial_count + 1
        assert "Pedro Martínez" in [c.name for c in agent._contacts.values()]
    
    @pytest.mark.asyncio
    async def test_add_contact_invalid_email(self, agent):
        """Test agregar contacto con email inválido"""
        response = await agent.add_contact(
            name="Test User",
            email="invalid-email"
        )
        
        assert not response.success
        assert "Email inválido" in response.error
    
    @pytest.mark.asyncio
    async def test_search_contacts_basic(self, agent):
        """Test búsqueda básica de contactos"""
        response = await agent.search_contacts("Juan")
        
        assert response.success
        assert response.details["results_count"] > 0
        
        # Verificar que Juan Pérez aparece en los resultados
        contacts = response.details["contacts"]
        juan_found = any("Juan" in contact["name"] for contact in contacts)
        assert juan_found
    
    @pytest.mark.asyncio
    async def test_search_contacts_with_filters(self, agent):
        """Test búsqueda de contactos con filtros"""
        response = await agent.search_contacts(
            query="",
            filters={"department": "Ventas"}
        )
        
        assert response.success
        # Verificar que todos los resultados son del departamento de Ventas
        contacts = response.details["contacts"]
        for contact in contacts:
            if contact.get("department"):
                assert contact["department"] == "Ventas"
    
    @pytest.mark.asyncio
    async def test_search_contacts_by_tags(self, agent):
        """Test búsqueda de contactos por tags"""
        response = await agent.search_contacts(
            query="",
            filters={"tags": ["cliente"]}
        )
        
        assert response.success
        contacts = response.details["contacts"]
        # Verificar que todos los contactos tienen el tag "cliente"
        for contact in contacts:
            assert "cliente" in contact["tags"]
    
    @pytest.mark.asyncio
    async def test_get_message_status(self, agent):
        """Test obtener estado de mensaje"""
        # Primero crear un mensaje
        send_response = await agent.send_email(
            to_recipients="test@example.com",
            subject="Test",
            body="Test message"
        )
        
        message_id = send_response.message_id
        
        # Luego obtener el estado
        status_response = await agent.get_message_status(message_id)
        
        assert status_response.success
        assert status_response.details["status"] == "delivered"
        assert status_response.details["message"]["id"] == message_id
    
    @pytest.mark.asyncio
    async def test_get_message_status_not_found(self, agent):
        """Test obtener estado de mensaje inexistente"""
        response = await agent.get_message_status("nonexistent_message_id")
        
        assert not response.success
        assert "no encontrado" in response.error
    
    @pytest.mark.asyncio
    async def test_process_request_send_email(self, agent):
        """Test procesamiento de request de envío de email"""
        request = {
            "action": "send_email",
            "to": "test@example.com",
            "subject": "Test Email",
            "body": "Contenido del email",
            "priority": "high"
        }
        
        response = await agent.process_request(request)
        
        assert response["success"]
        assert "message_id" in response
        assert response["details"]["recipients_count"] == 1
    
    @pytest.mark.asyncio
    async def test_process_request_send_notification(self, agent):
        """Test procesamiento de request de notificación"""
        request = {
            "action": "send_notification",
            "recipients": ["user1", "user2"],
            "title": "Notificación",
            "message": "Mensaje importante",
            "type": "info"
        }
        
        response = await agent.process_request(request)
        
        assert response["success"]
        assert "message_id" in response
        assert response["details"]["recipients_count"] == 2
    
    @pytest.mark.asyncio
    async def test_process_request_add_contact(self, agent):
        """Test procesamiento de request de agregar contacto"""
        request = {
            "action": "add_contact",
            "name": "Test User",
            "email": "test@company.com",
            "phone": "+34 600 123 456",
            "company": "Test Corp",
            "tags": ["cliente"]
        }
        
        response = await agent.process_request(request)
        
        assert response["success"]
        assert "contact_id" in response
        assert response["details"]["contact_name"] == "Test User"
    
    @pytest.mark.asyncio
    async def test_process_request_search_contacts(self, agent):
        """Test procesamiento de request de búsqueda de contactos"""
        request = {
            "action": "search_contacts",
            "query": "Juan",
            "filters": {"company": "Tech Solutions S.L."}
        }
        
        response = await agent.process_request(request)
        
        assert response["success"]
        assert "results" in response
        assert response["count"] > 0
    
    @pytest.mark.asyncio
    async def test_process_request_get_message_status(self, agent):
        """Test procesamiento de request de estado de mensaje"""
        # Primero crear un mensaje
        send_response = await agent.send_email(
            to_recipients="test@example.com",
            subject="Test",
            body="Test"
        )
        
        request = {
            "action": "get_message_status",
            "message_id": send_response.message_id
        }
        
        response = await agent.process_request(request)
        
        assert response["success"]
        assert "message_details" in response
        assert "status" in response
    
    @pytest.mark.asyncio
    async def test_process_request_invalid_action(self, agent):
        """Test procesamiento de request con acción inválida"""
        request = {
            "action": "invalid_action"
        }
        
        with pytest.raises(ValueError):
            await agent.process_request(request)
    
    def test_get_stats(self, agent):
        """Test obtención de estadísticas"""
        stats = agent.get_stats()
        
        assert "agent_name" in stats
        assert "total_contacts" in stats
        assert "total_messages" in stats
        assert "total_templates" in stats
        assert "outbox_count" in stats
        assert "available_actions" in stats
        
        # Verificar acciones disponibles
        actions = stats["available_actions"]
        assert "send_email" in actions
        assert "send_notification" in actions
        assert "add_contact" in actions
        assert "search_contacts" in actions
        assert "get_message_status" in actions


class TestContact:
    """Tests para Contact"""
    
    def test_contact_creation(self):
        """Test creación de contacto"""
        contact = Contact(
            id="contact_123",
            name="Juan Pérez",
            email="juan@company.com",
            phone="+34 600 123 456",
            company="Tech Corp",
            department="Desarrollo"
        )
        
        assert contact.id == "contact_123"
        assert contact.name == "Juan Pérez"
        assert contact.email == "juan@company.com"
        assert contact.phone == "+34 600 123 456"
        assert contact.company == "Tech Corp"
        assert contact.department == "Desarrollo"
        assert contact.tags == []
        assert contact.custom_fields == {}
    
    def test_contact_with_tags(self):
        """Test creación de contacto con tags"""
        contact = Contact(
            id="contact_456",
            name="María García",
            email="maria@company.com",
            tags=["cliente", "vip", "europeo"]
        )
        
        assert "cliente" in contact.tags
        assert "vip" in contact.tags
        assert "europeo" in contact.tags


class TestMessage:
    """Tests para Message"""
    
    def test_message_creation_email(self):
        """Test creación de mensaje de email"""
        message = Message(
            id="msg_123",
            type=CommunicationType.EMAIL,
            sender="sender@company.com",
            recipients=["recipient@company.com"],
            subject="Test Subject",
            body="Test Body",
            priority="high"
        )
        
        assert message.id == "msg_123"
        assert message.type == CommunicationType.EMAIL
        assert message.sender == "sender@company.com"
        assert message.recipients == ["recipient@company.com"]
        assert message.subject == "Test Subject"
        assert message.body == "Test Body"
        assert message.priority == "high"
        assert message.status == MessageStatus.PENDING


class TestEmailTemplate:
    """Tests para EmailTemplate"""
    
    def test_template_creation(self):
        """Test creación de plantilla de email"""
        template = EmailTemplate(
            id="template_1",
            name="Bienvenida",
            subject="Bienvenido/a a {{company_name}}",
            body="Hola {{name}}, te damos la bienvenida...",
            variables=["name", "company_name"]
        )
        
        assert template.id == "template_1"
        assert template.name == "Bienvenida"
        assert "{{company_name}}" in template.subject
        assert "{{name}}" in template.body
        assert "name" in template.variables
        assert "company_name" in template.variables


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v"])