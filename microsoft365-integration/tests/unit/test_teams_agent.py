"""
Tests unitarios para Teams Agent.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Dict, Any

from src.agents.teams_agent import TeamsAgent
from src.graph.client import GraphAPIClient
from src.auth.azure_ad import AzureADAuthenticator


@pytest.mark.unit
@pytest.mark.teams
class TestTeamsAgent:
    """Tests para TeamsAgent."""

    @pytest.fixture
    def teams_agent(self, mock_graph_client, mock_authenticator):
        """Fixture para crear instancia de TeamsAgent."""
        return TeamsAgent(
            graph_client=mock_graph_client,
            authenticator=mock_authenticator
        )

    @pytest.mark.asyncio
    async def test_init(self, teams_agent):
        """Test inicialización de TeamsAgent."""
        assert teams_agent.graph_client is not None
        assert teams_agent.authenticator is not None
        assert teams_agent.base_url == "https://graph.microsoft.com/v1.0"

    @pytest.mark.asyncio
    async def test_create_team(self, teams_agent, sample_team_content, mock_graph_client):
        """Test creación de equipo."""
        mock_response = {
            "id": "test-team-id",
            "displayName": sample_team_content["display_name"],
            "description": sample_team_content["description"],
            "isArchived": False
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await teams_agent.create_team(
            display_name=sample_team_content["display_name"],
            description=sample_team_content["description"],
            template=sample_team_content["template"]
        )
        
        assert result["id"] == "test-team-id"
        assert result["displayName"] == sample_team_content["display_name"]
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_team(self, teams_agent, mock_graph_client):
        """Test obtención de equipo."""
        team_id = "test-team-id"
        mock_response = {
            "id": team_id,
            "displayName": "Test Team",
            "description": "Test team description",
            "isArchived": False,
            "visibility": "private"
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await teams_agent.get_team(team_id)
        
        assert result["id"] == team_id
        assert result["displayName"] == "Test Team"
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_team(self, teams_agent, mock_graph_client):
        """Test actualización de equipo."""
        team_id = "test-team-id"
        update_data = {
            "displayName": "Updated Team Name",
            "description": "Updated team description"
        }
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await teams_agent.update_team(team_id, **update_data)
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_archive_team(self, teams_agent, mock_graph_client):
        """Test archivado de equipo."""
        team_id = "test-team-id"
        
        mock_response = {"status": "204"}
        mock_graph_client.post.return_value = mock_response
        
        result = await teams_agent.archive_team(team_id)
        
        assert result["status"] == "204"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_unarchive_team(self, teams_agent, mock_graph_client):
        """Test desarchivado de equipo."""
        team_id = "test-team-id"
        
        mock_response = {"status": "204"}
        mock_graph_client.post.return_value = mock_response
        
        result = await teams_agent.unarchive_team(team_id)
        
        assert result["status"] == "204"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_team(self, teams_agent, mock_graph_client):
        """Test eliminación de equipo."""
        team_id = "test-team-id"
        
        mock_response = {"status": "204"}
        mock_graph_client.delete.return_value = mock_response
        
        result = await teams_agent.delete_team(team_id)
        
        assert result["status"] == "204"
        mock_graph_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_channel(self, teams_agent, mock_graph_client):
        """Test creación de canal."""
        team_id = "test-team-id"
        channel_data = {
            "display_name": "General",
            "description": "General channel for team discussions"
        }
        
        mock_response = {
            "id": "test-channel-id",
            "displayName": channel_data["display_name"],
            "description": channel_data["description"],
            "membershipType": "standard"
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await teams_agent.create_channel(
            team_id=team_id,
            **channel_data
        )
        
        assert result["id"] == "test-channel-id"
        assert result["displayName"] == channel_data["display_name"]
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_channel(self, teams_agent, mock_graph_client):
        """Test obtención de canal."""
        team_id = "test-team-id"
        channel_id = "test-channel-id"
        
        mock_response = {
            "id": channel_id,
            "displayName": "General",
            "description": "General channel",
            "membershipType": "standard"
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await teams_agent.get_channel(team_id, channel_id)
        
        assert result["id"] == channel_id
        assert result["displayName"] == "General"
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_channel(self, teams_agent, mock_graph_client):
        """Test actualización de canal."""
        team_id = "test-team-id"
        channel_id = "test-channel-id"
        update_data = {
            "displayName": "Updated Channel Name",
            "description": "Updated channel description"
        }
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await teams_agent.update_channel(
            team_id=team_id,
            channel_id=channel_id,
            **update_data
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_channel(self, teams_agent, mock_graph_client):
        """Test eliminación de canal."""
        team_id = "test-team-id"
        channel_id = "test-channel-id"
        
        mock_response = {"status": "204"}
        mock_graph_client.delete.return_value = mock_response
        
        result = await teams_agent.delete_channel(team_id, channel_id)
        
        assert result["status"] == "204"
        mock_graph_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_team_channels(self, teams_agent, mock_graph_client):
        """Test obtención de canales del equipo."""
        team_id = "test-team-id"
        mock_response = {
            "value": [
                {
                    "id": "channel-1",
                    "displayName": "General",
                    "description": "General channel"
                },
                {
                    "id": "channel-2",
                    "displayName": "Development",
                    "description": "Development discussions"
                }
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await teams_agent.get_team_channels(team_id)
        
        assert len(result["value"]) == 2
        assert result["value"][0]["displayName"] == "General"
        assert result["value"][1]["displayName"] == "Development"
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message(self, teams_agent, mock_graph_client):
        """Test envío de mensaje."""
        team_id = "test-team-id"
        channel_id = "test-channel-id"
        message_data = {
            "content": "Hello team! This is a test message.",
            "message_type": "text"
        }
        
        mock_response = {
            "id": "message-123",
            "channelId": channel_id,
            "from": {"user": {"displayName": "Team Member"}},
            "content": message_data["content"]
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await teams_agent.send_message(
            team_id=team_id,
            channel_id=channel_id,
            **message_data
        )
        
        assert result["id"] == "message-123"
        assert result["content"] == message_data["content"]
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_with_attachments(self, teams_agent, mock_graph_client):
        """Test envío de mensaje con adjuntos."""
        team_id = "test-team-id"
        channel_id = "test-channel-id"
        message_data = {
            "content": "Please see the attached document.",
            "attachments": [
                {
                    "contentType": "reference",
                    "content": "{\"id\": \"file-id\"}"
                }
            ]
        }
        
        mock_response = {
            "id": "message-123",
            "content": message_data["content"]
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await teams_agent.send_message(
            team_id=team_id,
            channel_id=channel_id,
            **message_data
        )
        
        assert result["id"] == "message-123"
        assert "content" in result
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_message(self, teams_agent, mock_graph_client):
        """Test obtención de mensaje."""
        team_id = "test-team-id"
        channel_id = "test-channel-id"
        message_id = "message-123"
        
        mock_response = {
            "id": message_id,
            "channelId": channel_id,
            "content": "Test message content",
            "from": {"user": {"displayName": "User"}},
            "createdDateTime": "2024-01-01T00:00:00Z"
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await teams_agent.get_message(
            team_id=team_id,
            channel_id=channel_id,
            message_id=message_id
        )
        
        assert result["id"] == message_id
        assert result["content"] == "Test message content"
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_message(self, teams_agent, mock_graph_client):
        """Test actualización de mensaje."""
        team_id = "test-team-id"
        channel_id = "test-channel-id"
        message_id = "message-123"
        new_content = "Updated message content"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await teams_agent.update_message(
            team_id=team_id,
            channel_id=channel_id,
            message_id=message_id,
            content=new_content
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_message(self, teams_agent, mock_graph_client):
        """Test eliminación de mensaje."""
        team_id = "test-team-id"
        channel_id = "test-channel-id"
        message_id = "message-123"
        
        mock_response = {"status": "204"}
        mock_graph_client.delete.return_value = mock_response
        
        result = await teams_agent.delete_message(
            team_id=team_id,
            channel_id=channel_id,
            message_id=message_id
        )
        
        assert result["status"] == "204"
        mock_graph_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_channel_messages(self, teams_agent, mock_graph_client):
        """Test obtención de mensajes del canal."""
        team_id = "test-team-id"
        channel_id = "test-channel-id"
        mock_response = {
            "value": [
                {
                    "id": "message-1",
                    "content": "Message 1",
                    "from": {"user": {"displayName": "User 1"}}
                },
                {
                    "id": "message-2",
                    "content": "Message 2",
                    "from": {"user": {"displayName": "User 2"}}
                }
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await teams_agent.get_channel_messages(
            team_id=team_id,
            channel_id=channel_id,
            limit=10
        )
        
        assert len(result["value"]) == 2
        assert result["value"][0]["content"] == "Message 1"
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_team_member(self, teams_agent, mock_graph_client):
        """Test adición de miembro al equipo."""
        team_id = "test-team-id"
        user_id = "user-123"
        role = "member"
        
        mock_response = {"status": "204"}
        mock_graph_client.post.return_value = mock_response
        
        result = await teams_agent.add_team_member(
            team_id=team_id,
            user_id=user_id,
            role=role
        )
        
        assert result["status"] == "204"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_team_member(self, teams_agent, mock_graph_client):
        """Test remoción de miembro del equipo."""
        team_id = "test-team-id"
        user_id = "user-123"
        
        mock_response = {"status": "204"}
        mock_graph_client.delete.return_value = mock_response
        
        result = await teams_agent.remove_team_member(team_id, user_id)
        
        assert result["status"] == "204"
        mock_graph_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_team_members(self, teams_agent, mock_graph_client):
        """Test obtención de miembros del equipo."""
        team_id = "test-team-id"
        mock_response = {
            "value": [
                {
                    "id": "member-1",
                    "displayName": "John Doe",
                    "userId": "user-123",
                    "role": "owner"
                },
                {
                    "id": "member-2",
                    "displayName": "Jane Smith",
                    "userId": "user-456",
                    "role": "member"
                }
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await teams_agent.get_team_members(team_id)
        
        assert len(result["value"]) == 2
        assert result["value"][0]["role"] == "owner"
        assert result["value"][1]["role"] == "member"
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_schedule_meeting(self, teams_agent, mock_graph_client):
        """Test programación de reunión."""
        team_id = "test-team-id"
        meeting_data = {
            "subject": "Team Standup",
            "start_date_time": "2024-01-15T09:00:00Z",
            "end_date_time": "2024-01-15T09:30:00Z",
            "attendees": ["user1@example.com", "user2@example.com"]
        }
        
        mock_response = {
            "id": "meeting-123",
            "subject": meeting_data["subject"],
            "joinUrl": "https://teams.microsoft.com/l/meetup-join/...",
            "startDateTime": meeting_data["start_date_time"],
            "endDateTime": meeting_data["end_date_time"]
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await teams_agent.schedule_meeting(
            team_id=team_id,
            **meeting_data
        )
        
        assert result["id"] == "meeting-123"
        assert "joinUrl" in result
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_team_meetings(self, teams_agent, mock_graph_client):
        """Test obtención de reuniones del equipo."""
        team_id = "test-team-id"
        start_date = "2024-01-01T00:00:00Z"
        end_date = "2024-01-31T23:59:59Z"
        
        mock_response = {
            "value": [
                {
                    "id": "meeting-1",
                    "subject": "Weekly Standup",
                    "startDateTime": "2024-01-15T09:00:00Z",
                    "endDateTime": "2024-01-15T09:30:00Z"
                },
                {
                    "id": "meeting-2",
                    "subject": "Sprint Review",
                    "startDateTime": "2024-01-20T14:00:00Z",
                    "endDateTime": "2024-01-20T15:00:00Z"
                }
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await teams_agent.get_team_meetings(
            team_id=team_id,
            start_date=start_date,
            end_date=end_date
        )
        
        assert len(result["value"]) == 2
        assert result["value"][0]["subject"] == "Weekly Standup"
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_share_file_in_channel(self, teams_agent, mock_graph_client):
        """Test compartir archivo en canal."""
        team_id = "test-team-id"
        channel_id = "test-channel-id"
        file_id = "file-123"
        
        mock_response = {
            "id": "message-123",
            "content": "Shared a file",
            "attachments": [
                {
                    "contentType": "reference",
                    "content": f"{{\"id\": \"{file_id}\"}}"
                }
            ]
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await teams_agent.share_file_in_channel(
            team_id=team_id,
            channel_id=channel_id,
            file_id=file_id,
            message="Here's the file you requested"
        )
        
        assert result["id"] == "message-123"
        assert "attachments" in result
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_channel_tab(self, teams_agent, mock_graph_client):
        """Test creación de pestaña en canal."""
        team_id = "test-team-id"
        channel_id = "test-channel-id"
        tab_data = {
            "display_name": "Project Dashboard",
            "teamsApp_id": "com.microsoft.teamspace.tab.web",
            "content_url": "https://dashboard.example.com",
            "website_url": "https://dashboard.example.com"
        }
        
        mock_response = {
            "id": "tab-123",
            "displayName": tab_data["display_name"],
            "teamsApp": {"id": tab_data["teamsApp_id"]}
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await teams_agent.create_channel_tab(
            team_id=team_id,
            channel_id=channel_id,
            **tab_data
        )
        
        assert result["id"] == "tab-123"
        assert result["displayName"] == tab_data["display_name"]
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_channel_tabs(self, teams_agent, mock_graph_client):
        """Test obtención de pestañas del canal."""
        team_id = "test-team-id"
        channel_id = "test-channel-id"
        mock_response = {
            "value": [
                {
                    "id": "tab-1",
                    "displayName": "Project Board",
                    "teamsApp": {"id": "com.microsoft.teamspace.tab.web"}
                },
                {
                    "id": "tab-2",
                    "displayName": "Wiki",
                    "teamsApp": {"id": "com.microsoft.teamspace.tab.wiki"}
                }
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await teams_agent.get_channel_tabs(
            team_id=team_id,
            channel_id=channel_id
        )
        
        assert len(result["value"]) == 2
        assert result["value"][0]["displayName"] == "Project Board"
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_channel_tab(self, teams_agent, mock_graph_client):
        """Test actualización de pestaña de canal."""
        team_id = "test-team-id"
        channel_id = "test-channel-id"
        tab_id = "tab-123"
        update_data = {
            "display_name": "Updated Tab Name",
            "content_url": "https://updated-dashboard.example.com"
        }
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await teams_agent.update_channel_tab(
            team_id=team_id,
            channel_id=channel_id,
            tab_id=tab_id,
            **update_data
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_channel_tab(self, teams_agent, mock_graph_client):
        """Test remoción de pestaña de canal."""
        team_id = "test-team-id"
        channel_id = "test-channel-id"
        tab_id = "tab-123"
        
        mock_response = {"status": "204"}
        mock_graph_client.delete.return_value = mock_response
        
        result = await teams_agent.remove_channel_tab(
            team_id=team_id,
            channel_id=channel_id,
            tab_id=tab_id
        )
        
        assert result["status"] == "204"
        mock_graph_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notification(self, teams_agent, mock_graph_client):
        """Test envío de notificación."""
        team_id = "test-team-id"
        channel_id = "test-channel-id"
        notification_data = {
            "type": "message",
            "text": "This is an important notification!",
            "importance": "high"
        }
        
        mock_response = {"status": "202"}
        mock_graph_client.post.return_value = mock_response
        
        result = await teams_agent.send_notification(
            team_id=team_id,
            channel_id=channel_id,
            **notification_data
        )
        
        assert result["status"] == "202"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_messages(self, teams_agent, mock_graph_client):
        """Test búsqueda de mensajes."""
        team_id = "test-team-id"
        channel_id = "test-channel-id"
        search_query = "urgent bug"
        
        mock_response = {
            "value": [
                {
                    "id": "message-1",
                    "content": "Found an urgent bug in production",
                    "from": {"user": {"displayName": "Developer 1"}}
                },
                {
                    "id": "message-2",
                    "content": "The urgent bug has been fixed",
                    "from": {"user": {"displayName": "Developer 2"}}
                }
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await teams_agent.search_messages(
            team_id=team_id,
            channel_id=channel_id,
            query=search_query
        )
        
        assert len(result["value"]) == 2
        assert all("urgent" in message["content"].lower() for message in result["value"])

    @pytest.mark.asyncio
    async def test_get_team_activity(self, teams_agent, mock_graph_client):
        """Test obtención de actividad del equipo."""
        team_id = "test-team-id"
        mock_response = {
            "activity_count": 45,
            "active_users": 12,
            "messages_today": 28,
            "meetings_this_week": 8,
            "top_channels": [
                {"name": "General", "message_count": 15},
                {"name": "Development", "message_count": 10},
                {"name": "Support", "message_count": 8}
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await teams_agent.get_team_activity(team_id)
        
        assert result["activity_count"] == 45
        assert result["active_users"] == 12
        assert len(result["top_channels"]) == 3
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_team_from_group(self, teams_agent, mock_graph_client):
        """Test creación de equipo desde grupo existente."""
        group_id = "group-123"
        team_config = {
            "displayName": "New Team from Group",
            "description": "Team created from existing group",
            "template": "standard"
        }
        
        mock_response = {
            "id": "new-team-id",
            "displayName": team_config["displayName"],
            "description": team_config["description"]
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await teams_agent.create_team_from_group(
            group_id=group_id,
            **team_config
        )
        
        assert result["id"] == "new-team-id"
        assert result["displayName"] == team_config["displayName"]
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_clone_team(self, teams_agent, mock_graph_client):
        """Test clonación de equipo."""
        source_team_id = "source-team-id"
        clone_data = {
            "displayName": "Cloned Team",
            "description": "Clone of source team",
            "includeChannels": True,
            "includeMembers": False
        }
        
        mock_response = {
            "id": "cloned-team-id",
            "displayName": clone_data["displayName"],
            "description": clone_data["description"]
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await teams_agent.clone_team(
            source_team_id=source_team_id,
            **clone_data
        )
        
        assert result["id"] == "cloned-team-id"
        assert result["displayName"] == clone_data["displayName"]
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_network_error(self, teams_agent, error_scenarios):
        """Test manejo de errores de red."""
        teams_agent.graph_client.get.side_effect = error_scenarios["network_error"]
        
        with pytest.raises(Exception) as exc_info:
            await teams_agent.get_team("test-team-id")
        
        assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_error_handling_unauthorized(self, teams_agent, rate_limit_responses):
        """Test manejo de errores de autorización."""
        teams_agent.graph_client.get.return_value = rate_limit_responses["unauthorized"]
        
        with pytest.raises(Exception) as exc_info:
            await teams_agent.get_team("test-team-id")
        
        assert "Unauthorized" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, teams_agent, rate_limit_responses):
        """Test manejo de rate limiting."""
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return rate_limit_responses["rate_limited"]
            return rate_limit_responses["success"]
        
        teams_agent.graph_client.get.side_effect = side_effect
        
        with patch.object(teams_agent, '_retry_with_backoff') as mock_retry:
            mock_retry.return_value = rate_limit_responses["success"]
            
            result = await teams_agent.get_team("test-team-id")
            
            assert mock_retry.called

    @pytest.mark.asyncio
    async def test_batch_channel_operations(self, teams_agent, mock_graph_client):
        """Test operaciones en lote de canales."""
        team_id = "test-team-id"
        operations = [
            {"method": "POST", "url": f"/teams/{team_id}/channels", "body": {"displayName": "Channel 1"}},
            {"method": "POST", "url": f"/teams/{team_id}/channels", "body": {"displayName": "Channel 2"}},
            {"method": "PATCH", "url": f"/teams/{team_id}/channels/channel-1", "body": {"description": "Updated"}}
        ]
        
        mock_responses = [
            {"id": "channel-1", "displayName": "Channel 1", "status": "201"},
            {"id": "channel-2", "displayName": "Channel 2", "status": "201"},
            {"status": "204"}
        ]
        mock_graph_client.batch_request.return_value = mock_responses
        
        results = await teams_agent.batch_channel_operations(team_id, operations)
        
        assert len(results) == 3
        assert results[0]["id"] == "channel-1"
        assert results[1]["id"] == "channel-2"

    @pytest.mark.asyncio
    async def test_get_team_statistics(self, teams_agent, mock_graph_client):
        """Test obtención de estadísticas de equipo."""
        team_id = "test-team-id"
        mock_response = {
            "member_count": 25,
            "channel_count": 8,
            "message_count_last_week": 145,
            "meeting_count_this_month": 12,
            "files_shared_this_month": 35,
            "active_members_count": 18
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await teams_agent.get_team_statistics(team_id)
        
        assert result["member_count"] == 25
        assert result["channel_count"] == 8
        assert result["active_members_count"] == 18
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_team_settings(self, teams_agent, mock_graph_client):
        """Test configuración de equipo."""
        team_id = "test-team-id"
        settings = {
            "allow_guest_user": False,
            "allow_stickers_and_memes": True,
            "allow_team_mentions": True,
            "allow_channel_mentions": True
        }
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await teams_agent.set_team_settings(
            team_id=team_id,
            **settings
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_team_data(self, teams_agent, mock_graph_client):
        """Test exportación de datos del equipo."""
        team_id = "test-team-id"
        export_options = {
            "include_messages": True,
            "include_files": True,
            "include_members": True,
            "date_range": "last_month"
        }
        
        mock_response = {
            "export_id": "export-123",
            "status": "processing",
            "download_url": None
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await teams_agent.export_team_data(
            team_id=team_id,
            **export_options
        )
        
        assert result["export_id"] == "export-123"
        assert result["status"] == "processing"
        mock_graph_client.post.assert_called_once()