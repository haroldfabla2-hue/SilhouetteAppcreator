"""
Tests unitarios para Outlook Agent.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Dict, Any

from src.agents.outlook_agent import OutlookAgent
from src.graph.client import GraphAPIClient
from src.auth.azure_ad import AzureADAuthenticator


@pytest.mark.unit
@pytest.mark.outlook
class TestOutlookAgent:
    """Tests para OutlookAgent."""

    @pytest.fixture
    def outlook_agent(self, mock_graph_client, mock_authenticator):
        """Fixture para crear instancia de OutlookAgent."""
        return OutlookAgent(
            graph_client=mock_graph_client,
            authenticator=mock_authenticator
        )

    @pytest.mark.asyncio
    async def test_init(self, outlook_agent):
        """Test inicialización de OutlookAgent."""
        assert outlook_agent.graph_client is not None
        assert outlook_agent.authenticator is not None
        assert outlook_agent.base_url == "https://graph.microsoft.com/v1.0"

    @pytest.mark.asyncio
    async def test_send_email(self, outlook_agent, sample_email_content, mock_graph_client):
        """Test envío de email."""
        mock_response = {
            "id": "test-message-id",
            "conversationId": "conversation-123",
            "isDeliveryReceiptRequested": False
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await outlook_agent.send_email(
            subject=sample_email_content["subject"],
            body=sample_email_content["body"],
            to_recipients=sample_email_content["to_recipients"]
        )
        
        assert result["id"] == "test-message-id"
        assert "conversationId" in result
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_with_attachments(self, outlook_agent, sample_email_content, mock_graph_client):
        """Test envío de email con adjuntos."""
        mock_response = {"id": "test-message-id"}
        mock_graph_client.post.return_value = mock_response
        
        result = await outlook_agent.send_email(
            subject=sample_email_content["subject"],
            body=sample_email_content["body"],
            to_recipients=sample_email_content["to_recipients"],
            attachments=sample_email_content["attachments"]
        )
        
        assert result["id"] == "test-message-id"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_with_cc_bcc(self, outlook_agent, sample_email_content, mock_graph_client):
        """Test envío de email con CC y BCC."""
        mock_response = {"id": "test-message-id"}
        mock_graph_client.post.return_value = mock_response
        
        cc_recipients = [{"email_address": {"address": "cc@example.com"}}]
        bcc_recipients = [{"email_address": {"address": "bcc@example.com"}}]
        
        result = await outlook_agent.send_email(
            subject=sample_email_content["subject"],
            body=sample_email_content["body"],
            to_recipients=sample_email_content["to_recipients"],
            cc_recipients=cc_recipients,
            bcc_recipients=bcc_recipients
        )
        
        assert result["id"] == "test-message-id"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_message(self, outlook_agent, mock_graph_client):
        """Test obtención de mensaje."""
        message_id = "test-message-id"
        mock_response = {
            "id": message_id,
            "subject": "Test Message",
            "from": {"email_address": {"address": "sender@example.com"}},
            "to_recipients": [{"email_address": {"address": "recipient@example.com"}}]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await outlook_agent.get_message(message_id)
        
        assert result["id"] == message_id
        assert result["subject"] == "Test Message"
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_message(self, outlook_agent, mock_graph_client):
        """Test eliminación de mensaje."""
        message_id = "test-message-id"
        
        mock_response = {"status": "204"}
        mock_graph_client.delete.return_value = mock_response
        
        result = await outlook_agent.delete_message(message_id)
        
        assert result["status"] == "204"
        mock_graph_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_as_read(self, outlook_agent, mock_graph_client):
        """Test marcar como leído."""
        message_id = "test-message-id"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await outlook_agent.mark_as_read(message_id)
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_as_unread(self, outlook_agent, mock_graph_client):
        """Test marcar como no leído."""
        message_id = "test-message-id"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await outlook_agent.mark_as_unread(message_id)
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_move_message(self, outlook_agent, mock_graph_client):
        """Test mover mensaje a carpeta."""
        message_id = "test-message-id"
        folder_id = "folder-123"
        
        mock_response = {"id": "test-message-id", "parentFolderId": folder_id}
        mock_graph_client.patch.return_value = mock_response
        
        result = await outlook_agent.move_message(message_id, folder_id)
        
        assert result["parentFolderId"] == folder_id
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_folder(self, outlook_agent, mock_graph_client):
        """Test creación de carpeta."""
        folder_name = "Important"
        parent_folder_id = None
        
        mock_response = {
            "id": "folder-123",
            "displayName": folder_name,
            "parentFolderId": parent_folder_id
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await outlook_agent.create_folder(folder_name, parent_folder_id)
        
        assert result["displayName"] == folder_name
        assert result["id"] == "folder-123"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_calendar_event(self, outlook_agent, sample_calendar_event, mock_graph_client):
        """Test creación de evento de calendario."""
        mock_response = {
            "id": "event-123",
            "subject": sample_calendar_event["subject"],
            "start": sample_calendar_event["start"],
            "end": sample_calendar_event["end"]
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await outlook_agent.create_calendar_event(
            subject=sample_calendar_event["subject"],
            start=sample_calendar_event["start"],
            end=sample_calendar_event["end"],
            attendees=sample_calendar_event["attendees"]
        )
        
        assert result["id"] == "event-123"
        assert result["subject"] == sample_calendar_event["subject"]
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_calendar_event(self, outlook_agent, mock_graph_client):
        """Test obtención de evento de calendario."""
        event_id = "event-123"
        mock_response = {
            "id": event_id,
            "subject": "Team Meeting",
            "start": {"date_time": "2024-01-15T10:00:00", "time_zone": "UTC"},
            "end": {"date_time": "2024-01-15T11:00:00", "time_zone": "UTC"}
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await outlook_agent.get_calendar_event(event_id)
        
        assert result["id"] == event_id
        assert result["subject"] == "Team Meeting"
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_calendar_event(self, outlook_agent, mock_graph_client):
        """Test actualización de evento de calendario."""
        event_id = "event-123"
        update_data = {
            "subject": "Updated Meeting",
            "location": {"display_name": "Conference Room A"}
        }
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await outlook_agent.update_calendar_event(event_id, **update_data)
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_calendar_event(self, outlook_agent, mock_graph_client):
        """Test eliminación de evento de calendario."""
        event_id = "event-123"
        
        mock_response = {"status": "204"}
        mock_graph_client.delete.return_value = mock_response
        
        result = await outlook_agent.delete_calendar_event(event_id)
        
        assert result["status"] == "204"
        mock_graph_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_schedule_meeting(self, outlook_agent, sample_calendar_event, mock_graph_client):
        """Test programación de reunión."""
        mock_response = {"id": "event-123"}
        mock_graph_client.post.return_value = mock_response
        
        result = await outlook_agent.schedule_meeting(
            subject=sample_calendar_event["subject"],
            start=sample_calendar_event["start"],
            end=sample_calendar_event["end"],
            attendees=sample_calendar_event["attendees"],
            location=sample_calendar_event["location"]["display_name"]
        )
        
        assert result["id"] == "event-123"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_accept_meeting(self, outlook_agent, mock_graph_client):
        """Test aceptar reunión."""
        event_id = "event-123"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await outlook_agent.accept_meeting(event_id)
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_decline_meeting(self, outlook_agent, mock_graph_client):
        """Test declinar reunión."""
        event_id = "event-123"
        reason = "Conflict with another meeting"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await outlook_agent.decline_meeting(event_id, reason=reason)
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_tentatively_accept_meeting(self, outlook_agent, mock_graph_client):
        """Test aceptación tentativa de reunión."""
        event_id = "event-123"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await outlook_agent.tentatively_accept_meeting(event_id)
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_contact(self, outlook_agent, mock_graph_client):
        """Test creación de contacto."""
        contact_data = {
            "givenName": "John",
            "surname": "Doe",
            "email_addresses": [{"address": "john.doe@example.com", "name": "John Doe"}],
            "business_phones": ["+1234567890"],
            "job_title": "Software Engineer"
        }
        
        mock_response = {
            "id": "contact-123",
            "displayName": "John Doe",
            "email_addresses": [{"address": "john.doe@example.com", "name": "John Doe"}]
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await outlook_agent.create_contact(**contact_data)
        
        assert result["id"] == "contact-123"
        assert result["displayName"] == "John Doe"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_contact(self, outlook_agent, mock_graph_client):
        """Test obtención de contacto."""
        contact_id = "contact-123"
        mock_response = {
            "id": contact_id,
            "displayName": "John Doe",
            "givenName": "John",
            "surname": "Doe",
            "email_addresses": [{"address": "john.doe@example.com"}]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await outlook_agent.get_contact(contact_id)
        
        assert result["id"] == contact_id
        assert result["displayName"] == "John Doe"
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_contacts(self, outlook_agent, mock_graph_client):
        """Test búsqueda de contactos."""
        search_term = "John"
        mock_response = {
            "value": [
                {
                    "id": "contact-1",
                    "displayName": "John Doe",
                    "email_addresses": [{"address": "john.doe@example.com"}]
                },
                {
                    "id": "contact-2",
                    "displayName": "John Smith",
                    "email_addresses": [{"address": "john.smith@example.com"}]
                }
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await outlook_agent.search_contacts(search_term)
        
        assert len(result["value"]) == 2
        assert all("John" in contact["displayName"] for contact in result["value"])

    @pytest.mark.asyncio
    async def test_get_calendar_view(self, outlook_agent, mock_graph_client):
        """Test obtención de vista de calendario."""
        start_date = "2024-01-15T00:00:00Z"
        end_date = "2024-01-22T23:59:59Z"
        
        mock_response = {
            "value": [
                {
                    "id": "event-1",
                    "subject": "Meeting 1",
                    "start": {"date_time": "2024-01-16T10:00:00", "time_zone": "UTC"},
                    "end": {"date_time": "2024-01-16T11:00:00", "time_zone": "UTC"}
                },
                {
                    "id": "event-2",
                    "subject": "Meeting 2",
                    "start": {"date_time": "2024-01-18T14:00:00", "time_zone": "UTC"},
                    "end": {"date_time": "2024-01-18T15:30:00", "time_zone": "UTC"}
                }
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await outlook_agent.get_calendar_view(start_date, end_date)
        
        assert len(result["value"]) == 2
        assert all("subject" in event for event in result["value"])

    @pytest.mark.asyncio
    async def test_get_messages(self, outlook_agent, mock_graph_client):
        """Test obtención de mensajes."""
        folder_id = "inbox"
        mock_response = {
            "value": [
                {
                    "id": "message-1",
                    "subject": "Email 1",
                    "from": {"email_address": {"address": "sender1@example.com"}}
                },
                {
                    "id": "message-2",
                    "subject": "Email 2",
                    "from": {"email_address": {"address": "sender2@example.com"}}
                }
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await outlook_agent.get_messages(folder_id=folder_id, limit=10)
        
        assert len(result["value"]) == 2
        assert all("subject" in message for message in result["value"])

    @pytest.mark.asyncio
    async def test_reply_to_message(self, outlook_agent, mock_graph_client):
        """Test responder a mensaje."""
        message_id = "message-123"
        reply_text = "Thank you for your email."
        
        mock_response = {"id": "reply-message-123"}
        mock_graph_client.post.return_value = mock_response
        
        result = await outlook_agent.reply_to_message(message_id, reply_text)
        
        assert result["id"] == "reply-message-123"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_reply_all_to_message(self, outlook_agent, mock_graph_client):
        """Test responder a todos."""
        message_id = "message-123"
        reply_text = "Thank you everyone."
        
        mock_response = {"id": "reply-all-123"}
        mock_graph_client.post.return_value = mock_response
        
        result = await outlook_agent.reply_all_to_message(message_id, reply_text)
        
        assert result["id"] == "reply-all-123"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_forward_message(self, outlook_agent, mock_graph_client):
        """Test reenviar mensaje."""
        message_id = "message-123"
        forward_to = [{"email_address": {"address": "forward@example.com"}}]
        
        mock_response = {"id": "forward-123"}
        mock_graph_client.post.return_value = mock_response
        
        result = await outlook_agent.forward_message(message_id, forward_to)
        
        assert result["id"] == "forward-123"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_out_of_office(self, outlook_agent, mock_graph_client):
        """Test configurar ausencia temporal."""
        oof_data = {
            "state": "enabled",
            "externalAudience": "all",
            "internalReply": "I'm currently out of office. I'll respond when I return.",
            "externalReply": "Thank you for your email."
        }
        
        mock_response = {"status": "204"}
        mock_graph_client.post.return_value = mock_response
        
        result = await outlook_agent.set_out_of_office(**oof_data)
        
        assert result["status"] == "204"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_out_of_office(self, outlook_agent, mock_graph_client):
        """Test obtener configuración de ausencia temporal."""
        mock_response = {
            "value": {
                "state": "enabled",
                "internalReply": "I'm out of office",
                "externalReply": "Thank you"
            }
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await outlook_agent.get_out_of_office()
        
        assert result["value"]["state"] == "enabled"
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_signature(self, outlook_agent, mock_graph_client):
        """Test creación de firma."""
        signature_text = """--
        John Doe
        Software Engineer
        john.doe@company.com
        +1 (555) 123-4567"""
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await outlook_agent.create_signature(
            signature_text=signature_text,
            is_default=True
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_vacation_calendar(self, outlook_agent, mock_graph_client):
        """Test configurar calendario de vacaciones."""
        vacation_data = {
            "start_date": "2024-02-01",
            "end_date": "2024-02-05",
            "message": "On vacation"
        }
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await outlook_agent.set_vacation_calendar(**vacation_data)
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_free_busy_info(self, outlook_agent, mock_graph_client):
        """Test obtener información de disponibilidad."""
        attendees = [
            {"email_address": {"address": "user1@example.com"}},
            {"email_address": {"address": "user2@example.com"}}
        ]
        start_time = "2024-01-15T09:00:00Z"
        end_time = "2024-01-15T17:00:00Z"
        
        mock_response = {
            "value": [
                {
                    "email_address": "user1@example.com",
                    "availability": "free"
                },
                {
                    "email_address": "user2@example.com",
                    "availability": "busy"
                }
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await outlook_agent.get_free_busy_info(
            attendees=attendees,
            start_time=start_time,
            end_time=end_time
        )
        
        assert len(result["value"]) == 2
        assert result["value"][0]["availability"] == "free"

    @pytest.mark.asyncio
    async def test_create_calendar_group(self, outlook_agent, mock_graph_client):
        """Test creación de grupo de calendarios."""
        group_name = "Work Calendars"
        
        mock_response = {
            "id": "group-123",
            "name": group_name,
            "change_key": "change-key-123"
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await outlook_agent.create_calendar_group(group_name)
        
        assert result["name"] == group_name
        assert result["id"] == "group-123"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_network_error(self, outlook_agent, error_scenarios):
        """Test manejo de errores de red."""
        outlook_agent.graph_client.get.side_effect = error_scenarios["network_error"]
        
        with pytest.raises(Exception) as exc_info:
            await outlook_agent.get_message("test-message-id")
        
        assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_error_handling_invalid_email(self, outlook_agent, mock_graph_client):
        """Test manejo de email inválido."""
        mock_graph_client.post.side_effect = Exception("Invalid email format")
        
        with pytest.raises(Exception) as exc_info:
            await outlook_agent.send_email(
                subject="Test",
                body={"content_type": "Text", "content": "Test"},
                to_recipients=[{"email_address": {"address": "invalid-email"}}]
            )
        
        assert "Invalid email format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, outlook_agent, rate_limit_responses):
        """Test manejo de rate limiting."""
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return rate_limit_responses["rate_limited"]
            return rate_limit_responses["success"]
        
        outlook_agent.graph_client.get.side_effect = side_effect
        
        with patch.object(outlook_agent, '_retry_with_backoff') as mock_retry:
            mock_retry.return_value = rate_limit_responses["success"]
            
            result = await outlook_agent.get_message("test-message-id")
            
            assert mock_retry.called

    @pytest.mark.asyncio
    async def test_batch_email_operations(self, outlook_agent, mock_graph_client):
        """Test operaciones en lote de emails."""
        operations = [
            {
                "method": "POST",
                "url": "/me/sendMail",
                "body": {
                    "message": {"subject": "Email 1"},
                    "saveToSentItems": True
                }
            },
            {
                "method": "POST",
                "url": "/me/sendMail",
                "body": {
                    "message": {"subject": "Email 2"},
                    "saveToSentItems": True
                }
            }
        ]
        
        mock_responses = [
            {"id": "message-1"},
            {"id": "message-2"}
        ]
        mock_graph_client.batch_request.return_value = mock_responses
        
        results = await outlook_agent.batch_send_emails(operations)
        
        assert len(results) == 2
        assert all("id" in result for result in results)

    @pytest.mark.asyncio
    async def test_search_messages(self, outlook_agent, mock_graph_client):
        """Test búsqueda de mensajes."""
        search_query = "important project"
        mock_response = {
            "value": [
                {
                    "id": "message-1",
                    "subject": "Important Project Update",
                    "from": {"email_address": {"address": "colleague@example.com"}}
                },
                {
                    "id": "message-2",
                    "subject": "Project Deadlines",
                    "from": {"email_address": {"address": "manager@example.com"}}
                }
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await outlook_agent.search_messages(search_query)
        
        assert len(result["value"]) == 2
        assert all("project" in message["subject"].lower() for message in result["value"])

    @pytest.mark.asyncio
    async def test_get_unread_count(self, outlook_agent, mock_graph_client):
        """Test obtención de contador de no leídos."""
        mock_response = {
            "@odata.count": 15
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await outlook_agent.get_unread_count()
        
        assert result["@odata.count"] == 15
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_snooze_message(self, outlook_agent, mock_graph_client):
        """Test posponer mensaje."""
        message_id = "message-123"
        snooze_time = "2024-01-20T10:00:00Z"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await outlook_agent.snooze_message(message_id, snooze_time)
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()