"""
Tests end-to-end para flujos completos de Microsoft 365.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Dict, Any

from src.microsoft365_integration import Microsoft365Integration
from src.agents.word_agent import WordAgent
from src.agents.excel_agent import ExcelAgent
from src.agents.powerpoint_agent import PowerPointAgent
from src.agents.outlook_agent import OutlookAgent
from src.agents.onedrive_agent import OneDriveAgent
from src.agents.teams_agent import TeamsAgent


@pytest.mark.e2e
class TestCompleteWorkflows:
    """Tests end-to-end para flujos completos."""

    @pytest.fixture
    async def integration_system(self, mock_settings, mock_authenticator, mock_graph_client, mock_redis):
        """Fixture para crear sistema de integración completo."""
        with patch('redis.Redis', return_value=mock_redis):
            integration = Microsoft365Integration(
                settings=mock_settings,
                authenticator=mock_authenticator,
                graph_client=mock_graph_client
            )
            return integration

    @pytest.mark.asyncio
    async def test_document_creation_to_teams_share_workflow(self, integration_system):
        """Test flujo completo: Crear documento → Compartir en Teams."""
        
        # 1. Crear documento en Word
        word_agent = integration_system.word_agent
        excel_agent = integration_system.excel_agent
        teams_agent = integration_system.teams_agent
        
        # Mock creación de documento Word
        word_response = {
            "id": "doc-123",
            "name": "Quarterly Report.docx",
            "webUrl": "https://word.com/edit/doc-123"
        }
        word_agent.graph_client.post.return_value = word_response
        
        # Mock adición de datos desde Excel
        excel_response = {
            "id": "workbook-456",
            "name": "Sales Data.xlsx"
        }
        excel_agent.graph_client.post.return_value = excel_response
        
        # Mock subida a OneDrive
        onedrive_response = {
            "id": "file-789",
            "name": "Quarterly Report.docx",
            "webUrl": "https://onedrive.live.com/redir?resid=file-789"
        }
        integration_system.onedrive_agent.graph_client.put.return_value = onedrive_response
        
        # Mock compartir en Teams
        teams_response = {
            "id": "message-456",
            "content": "Shared quarterly report with the team"
        }
        teams_agent.graph_client.post.return_value = teams_response
        
        # Ejecutar flujo completo
        document = await word_agent.create_document(
            title="Quarterly Report",
            content={
                "paragraphs": [{"text": "Q4 2024 Sales Report"}],
                "tables": [{"rows": [["Product", "Sales"], ["Widget A", 1000]]}]
            }
        )
        
        # Subir documento a OneDrive
        file_uploaded = await integration_system.onedrive_agent.upload_file(
            file_name="Quarterly Report.docx",
            file_content=b"Mock document content",
            parent_folder_id="root"
        )
        
        # Compartir en canal de Teams
        shared_message = await teams_agent.send_message(
            team_id="team-123",
            channel_id="general",
            content=f"Please review the quarterly report: {file_uploaded['webUrl']}"
        )
        
        # Verificaciones
        assert document["id"] == "doc-123"
        assert file_uploaded["id"] == "file-789"
        assert shared_message["id"] == "message-456"

    @pytest.mark.asyncio
    async def test_email_calendar_meeting_workflow(self, integration_system):
        """Test flujo: Enviar email → Programar reunión → Seguimiento."""
        
        outlook_agent = integration_system.outlook_agent
        teams_agent = integration_system.teams_agent
        
        # Mock envío de email inicial
        email_response = {
            "id": "message-123",
            "conversationId": "conv-456"
        }
        outlook_agent.graph_client.post.return_value = email_response
        
        # Mock creación de evento de calendario
        calendar_response = {
            "id": "event-789",
            "subject": "Project Kickoff Meeting",
            "joinUrl": "https://teams.microsoft.com/l/meetup-join/..."
        }
        outlook_agent.graph_client.post.return_value = calendar_response
        
        # Mock programación de reunión en Teams
        teams_meeting_response = {
            "id": "meeting-456",
            "joinUrl": "https://teams.microsoft.com/l/meetup-join/teams-kickoff"
        }
        teams_agent.graph_client.post.return_value = teams_meeting_response
        
        # Mock respuesta al email
        reply_response = {"id": "reply-789"}
        outlook_agent.graph_client.post.return_value = reply_response
        
        # 1. Enviar email de convocatoria
        email_sent = await outlook_agent.send_email(
            subject="Project Kickoff Meeting",
            body={
                "content_type": "HTML",
                "content": "<h2>Project Kickoff Meeting</h2><p>Please join us for the project kickoff.</p>"
            },
            to_recipients=[
                {"email_address": {"address": "team@company.com"}}
            ]
        )
        
        # 2. Programar evento en calendario
        meeting = await outlook_agent.schedule_meeting(
            subject="Project Kickoff Meeting",
            start={"date_time": "2024-01-15T10:00:00", "time_zone": "UTC"},
            end={"date_time": "2024-01-15T11:00:00", "time_zone": "UTC"},
            attendees=[
                {"email_address": {"address": "team@company.com"}}
            ],
            location="Conference Room A"
        )
        
        # 3. Crear reunión de Teams
        teams_meeting = await teams_agent.schedule_meeting(
            team_id="team-123",
            subject="Project Kickoff Meeting",
            start_date_time="2024-01-15T10:00:00Z",
            end_date_time="2024-01-15T11:00:00Z",
            attendees=["team@company.com"]
        )
        
        # 4. Responder al email inicial
        email_reply = await outlook_agent.reply_to_message(
            message_id="message-123",
            reply_text="Meeting details: Join via Teams link above."
        )
        
        # Verificaciones
        assert email_sent["id"] == "message-123"
        assert meeting["id"] == "event-789"
        assert teams_meeting["id"] == "meeting-456"
        assert email_reply["id"] == "reply-789"

    @pytest.mark.asyncio
    async def test_data_analysis_to_presentation_workflow(self, integration_system):
        """Test flujo: Análisis de datos → Crear presentación → Distribuir."""
        
        excel_agent = integration_system.excel_agent
        powerpoint_agent = integration_system.powerpoint_agent
        teams_agent = integration_system.teams_agent
        outlook_agent = integration_system.outlook_agent
        
        # Mock obtención de datos de Excel
        excel_data = {
            "value": [
                ["Product", "Q1", "Q2", "Q3", "Q4"],
                ["Widget A", 100, 120, 140, 160],
                ["Widget B", 80, 85, 90, 95],
                ["Widget C", 150, 155, 160, 165]
            ]
        }
        excel_agent.graph_client.get.return_value = excel_data
        
        # Mock creación de gráfico en Excel
        chart_response = {
            "id": "chart-123",
            "chartType": "columnChart",
            "title": "Quarterly Sales"
        }
        excel_agent.graph_client.post.return_value = chart_response
        
        # Mock creación de presentación PowerPoint
        presentation_response = {
            "id": "presentation-456",
            "name": "Sales Analysis Q4 2024.pptx"
        }
        powerpoint_agent.graph_client.post.return_value = presentation_response
        
        # Mock adición de diapositiva con gráfico
        slide_response = {
            "id": "slide-789",
            "layout": "title_content"
        }
        powerpoint_agent.graph_client.post.return_value = slide_response
        
        # Mock subida de presentación a OneDrive
        file_upload_response = {
            "id": "presentation-file-123",
            "name": "Sales Analysis Q4 2024.pptx",
            "webUrl": "https://onedrive.live.com/redir?resid=presentation-file-123"
        }
        integration_system.onedrive_agent.graph_client.put.return_value = file_upload_response
        
        # Mock envío de email con presentación
        email_response = {
            "id": "email-456",
            "subject": "Q4 2024 Sales Analysis"
        }
        outlook_agent.graph_client.post.return_value = email_response
        
        # 1. Analizar datos de Excel
        sales_data = await excel_agent.get_range_values(
            workbook_id="workbook-123",
            sheet_name="Sales",
            range_address="A1:E5"
        )
        
        # 2. Crear gráfico de análisis
        chart = await excel_agent.create_chart(
            workbook_id="workbook-123",
            sheet_name="Sales",
            chart_type="column",
            data_range="A1:E5",
            title="Quarterly Sales Analysis"
        )
        
        # 3. Crear presentación
        presentation = await powerpoint_agent.create_presentation(
            title="Q4 2024 Sales Analysis",
            slides=[
                {
                    "layout": "title_slide",
                    "title": "Sales Performance Q4 2024",
                    "content": "Comprehensive analysis of quarterly performance"
                },
                {
                    "layout": "title_content",
                    "title": "Key Insights",
                    "content": "Growth trends and performance metrics"
                }
            ]
        )
        
        # 4. Subir presentación a OneDrive
        uploaded_presentation = await integration_system.onedrive_agent.upload_file(
            file_name="Sales Analysis Q4 2024.pptx",
            file_content=b"Mock presentation content",
            parent_folder_id="presentations"
        )
        
        # 5. Enviar presentación por email
        sent_email = await outlook_agent.send_email(
            subject="Q4 2024 Sales Analysis",
            body={
                "content_type": "HTML",
                "content": f"<p>Please find attached the Q4 2024 sales analysis presentation.</p><p><a href='{uploaded_presentation['webUrl']}'>View Presentation</a></p>"
            },
            to_recipients=[
                {"email_address": {"address": "management@company.com"}},
                {"email_address": {"address": "sales-team@company.com"}}
            ],
            attachments=[{
                "name": "Sales Analysis Q4 2024.pptx",
                "content": "Mock attachment content"
            }]
        )
        
        # Verificaciones
        assert len(sales_data["value"]) == 4
        assert chart["id"] == "chart-123"
        assert presentation["id"] == "presentation-456"
        assert uploaded_presentation["id"] == "presentation-file-123"
        assert sent_email["id"] == "email-456"

    @pytest.mark.asyncio
    async def test_team_collaboration_workflow(self, integration_system):
        """Test flujo completo de colaboración en equipo."""
        
        teams_agent = integration_system.teams_agent
        onedrive_agent = integration_system.onedrive_agent
        outlook_agent = integration_system.outlook_agent
        word_agent = integration_system.word_agent
        
        # Mock creación de equipo
        team_response = {
            "id": "team-123",
            "displayName": "Product Development",
            "description": "Cross-functional product development team"
        }
        teams_agent.graph_client.post.return_value = team_response
        
        # Mock creación de canales
        general_channel = {"id": "channel-general", "displayName": "General"}
        dev_channel = {"id": "channel-dev", "displayName": "Development"}
        teams_agent.graph_client.post.side_effect = [general_channel, dev_channel]
        
        # Mock adición de miembros
        member_response = {"status": "204"}
        teams_agent.graph_client.post.return_value = member_response
        
        # Mock creación de documento colaborativo
        doc_response = {
            "id": "doc-456",
            "name": "Project Requirements.docx"
        }
        word_agent.graph_client.post.return_value = doc_response
        
        # Mock subida de documento
        file_response = {
            "id": "file-789",
            "name": "Project Requirements.docx"
        }
        onedrive_agent.graph_client.put.return_value = file_response
        
        # Mock compartir archivo en canal
        share_message = {"id": "message-123"}
        teams_agent.graph_client.post.return_value = share_message
        
        # Mock invitación por email
        invite_email = {"id": "invite-456"}
        outlook_agent.graph_client.post.return_value = invite_email
        
        # 1. Crear equipo
        team = await teams_agent.create_team(
            display_name="Product Development",
            description="Cross-functional product development team",
            template="standard"
        )
        
        # 2. Crear canales
        await teams_agent.create_channel(
            team_id="team-123",
            display_name="General",
            description="General team discussions"
        )
        
        await teams_agent.create_channel(
            team_id="team-123",
            display_name="Development",
            description="Technical development discussions"
        )
        
        # 3. Añadir miembros
        await teams_agent.add_team_member(
            team_id="team-123",
            user_id="user-dev1",
            role="member"
        )
        
        await teams_agent.add_team_member(
            team_id="team-123",
            user_id="user-dev2",
            role="member"
        )
        
        # 4. Crear documento colaborativo
        requirements_doc = await word_agent.create_document(
            title="Project Requirements",
            content={
                "paragraphs": [
                    {"text": "Project Requirements Document", "style": "Heading1"},
                    {"text": "This document outlines the project requirements.", "style": "Normal"}
                ]
            }
        )
        
        # 5. Subir documento a carpeta del equipo
        team_file = await onedrive_agent.upload_file(
            file_name="Project Requirements.docx",
            file_content=b"Mock document content",
            parent_folder_id="team-folder-123"
        )
        
        # 6. Compartir documento en canal
        shared_doc = await teams_agent.share_file_in_channel(
            team_id="team-123",
            channel_id="channel-dev",
            file_id="file-789",
            message="New project requirements document for review"
        )
        
        # 7. Enviar invitación por email
        team_invite = await outlook_agent.send_email(
            subject="Welcome to Product Development Team",
            body={
                "content_type": "HTML",
                "content": "<h2>Welcome to the team!</h2><p>You've been added to our Product Development team. Please review the project requirements document.</p>"
            },
            to_recipients=[
                {"email_address": {"address": "developer1@company.com"}},
                {"email_address": {"address": "developer2@company.com"}}
            ]
        )
        
        # Verificaciones
        assert team["id"] == "team-123"
        assert team["displayName"] == "Product Development"
        assert shared_doc["id"] == "message-123"
        assert team_invite["id"] == "invite-456"

    @pytest.mark.asyncio
    async def test_document_approval_workflow(self, integration_system):
        """Test flujo de aprobación de documentos."""
        
        word_agent = integration_system.word_agent
        teams_agent = integration_system.teams_agent
        outlook_agent = integration_system.outlook_agent
        
        # Mock creación de documento inicial
        initial_doc = {
            "id": "doc-123",
            "name": "Policy Document v1.docx"
        }
        word_agent.graph_client.post.return_value = initial_doc
        
        # Mock adición de comentarios
        comment_response = {"id": "comment-456"}
        word_agent.graph_client.post.return_value = comment_response
        
        # Mock envío de mensaje de revisión en Teams
        review_message = {"id": "message-789"}
        teams_agent.graph_client.post.return_value = review_message
        
        # Mock respuesta con comentarios
        review_response = {"id": "reply-123"}
        outlook_agent.graph_client.reply_to_message.return_value = review_response
        
        # Mock actualización de documento
        update_response = {"status": "204"}
        word_agent.graph_client.patch.return_value = update_response
        
        # Mock versión final
        final_doc = {
            "id": "doc-123-v2",
            "name": "Policy Document v2.docx"
        }
        word_agent.graph_client.post.return_value = final_doc
        
        # Mock notificación de aprobación
        approval_notification = {"id": "email-456"}
        outlook_agent.send_email.return_value = approval_notification
        
        # 1. Crear documento inicial
        document = await word_agent.create_document(
            title="Company Policy Document",
            content={
                "paragraphs": [
                    {"text": "Company Policy Document", "style": "Heading1"},
                    {"text": "Initial policy draft for review", "style": "Normal"}
                ]
            }
        )
        
        # 2. Añadir documento para revisión en Teams
        review_request = await teams_agent.send_message(
            team_id="team-123",
            channel_id="general",
            content=f"Please review the new policy document: {document['webUrl']}"
        )
        
        # 3. Añadir comentarios al documento
        await word_agent.add_comment(
            document_id="doc-123",
            comment="Section 2 needs more detail on compliance requirements.",
            range_start=100,
            range_end=200
        )
        
        # 4. Revisar comentarios por email
        review_email = await outlook_agent.reply_to_message(
            message_id="message-456",
            reply_text="Reviewed the policy. Added comments for improvements in Section 2."
        )
        
        # 5. Actualizar documento con cambios
        await word_agent.update_document_content(
            document_id="doc-123",
            content={
                "paragraphs": [
                    {"text": "Company Policy Document - Updated", "style": "Heading1"},
                    {"text": "Updated policy with compliance details", "style": "Normal"}
                ]
            }
        )
        
        # 6. Crear versión final
        final_version = await word_agent.create_document(
            title="Company Policy Document - Final",
            content={
                "paragraphs": [
                    {"text": "Company Policy Document - Final Version", "style": "Heading1"},
                    {"text": "Approved policy document", "style": "Normal"}
                ]
            }
        )
        
        # 7. Notificar aprobación
        approval_email = await outlook_agent.send_email(
            subject="Policy Document Approved",
            body={
                "content_type": "HTML",
                "content": "<h2>Policy Document Approved</h2><p>The updated policy document has been approved and is ready for implementation.</p>"
            },
            to_recipients=[
                {"email_address": {"address": "all-staff@company.com"}}
            ]
        )
        
        # Verificaciones
        assert document["id"] == "doc-123"
        assert review_request["id"] == "message-789"
        assert final_version["id"] == "doc-123-v2"
        assert approval_email["id"] == "email-456"

    @pytest.mark.asyncio
    async def test_meeting_workflow_with_file_sharing(self, integration_system):
        """Test flujo de reunión con compartir archivos."""
        
        outlook_agent = integration_system.outlook_agent
        teams_agent = integration_system.teams_agent
        excel_agent = integration_system.excel_agent
        powerpoint_agent = integration_system.powerpoint_agent
        
        # Mock creación de agenda en Excel
        agenda_workbook = {
            "id": "agenda-123",
            "name": "Meeting Agenda.xlsx"
        }
        excel_agent.graph_client.post.return_value = agenda_workbook
        
        # Mock creación de presentación
        presentation = {
            "id": "slides-456",
            "name": "Meeting Slides.pptx"
        }
        powerpoint_agent.graph_client.post.return_value = presentation
        
        # Mock programación de reunión
        meeting = {
            "id": "meeting-789",
            "subject": "Quarterly Review Meeting",
            "joinUrl": "https://teams.microsoft.com/l/meetup-join/..."
        }
        outlook_agent.graph_client.post.return_value = meeting
        
        # Mock programación de reunión en Teams
        teams_meeting = {
            "id": "teams-meeting-123",
            "joinUrl": "https://teams.microsoft.com/l/meetup-join/teams-review"
        }
        teams_agent.graph_client.post.return_value = teams_meeting
        
        # Mock subida de archivos
        file_response = {
            "id": "file-456",
            "name": "Meeting Materials.zip"
        }
        integration_system.onedrive_agent.graph_client.put.return_value = file_response
        
        # Mock compartir archivos en reunión
        file_share_message = {"id": "message-123"}
        teams_agent.graph_client.post.return_value = file_share_message
        
        # Mock envío de materiales por email
        materials_email = {"id": "email-789"}
        outlook_agent.graph_client.post.return_value = materials_email
        
        # 1. Crear agenda de reunión en Excel
        agenda = await excel_agent.create_workbook(
            title="Meeting Agenda",
            content={
                "worksheets": [{
                    "name": "Agenda",
                    "data": [
                        ["Time", "Topic", "Presenter"],
                        ["9:00", "Welcome & Introductions", "Manager"],
                        ["9:15", "Q4 Results Review", "Analyst"],
                        ["9:45", "Q1 Planning", "Team Lead"],
                        ["10:30", "Action Items", "All"]
                    ]
                }]
            }
        )
        
        # 2. Crear presentación de diapositivas
        slides = await powerpoint_agent.create_presentation(
            title="Quarterly Review",
            slides=[
                {
                    "layout": "title_slide",
                    "title": "Q4 2024 Review",
                    "content": "Quarterly performance and planning"
                },
                {
                    "layout": "title_content",
                    "title": "Key Achievements",
                    "content": "Major accomplishments this quarter"
                },
                {
                    "layout": "title_content",
                    "title": "Areas for Improvement",
                    "content": "Opportunities and challenges"
                }
            ]
        )
        
        # 3. Programar reunión
        scheduled_meeting = await outlook_agent.schedule_meeting(
            subject="Quarterly Review Meeting",
            start={"date_time": "2024-01-15T09:00:00", "time_zone": "UTC"},
            end={"date_time": "2024-01-15T11:00:00", "time_zone": "UTC"},
            attendees=[
                {"email_address": {"address": "team@company.com"}},
                {"email_address": {"address": "management@company.com"}}
            ],
            location="Conference Room A"
        )
        
        # 4. Crear reunión de Teams
        teams_meeting_created = await teams_agent.schedule_meeting(
            team_id="team-123",
            subject="Quarterly Review Meeting",
            start_date_time="2024-01-15T09:00:00Z",
            end_date_time="2024-01-15T11:00:00Z",
            attendees=["team@company.com", "management@company.com"]
        )
        
        # 5. Subir materiales de reunión
        materials = await integration_system.onedrive_agent.upload_file(
            file_name="Meeting Materials.zip",
            file_content=b"Mock meeting materials",
            parent_folder_id="meetings"
        )
        
        # 6. Compartir materiales en reunión
        shared_materials = await teams_agent.send_message(
            team_id="team-123",
            channel_id="general",
            content=f"Meeting materials ready: {materials['webUrl']}"
        )
        
        # 7. Enviar materiales por email
        materials_sent = await outlook_agent.send_email(
            subject="Quarterly Review Meeting - Materials",
            body={
                "content_type": "HTML",
                "content": f"<p>Please find attached the meeting materials.</p><p>Join meeting: {teams_meeting_created['joinUrl']}</p>"
            },
            to_recipients=[
                {"email_address": {"address": "team@company.com"}},
                {"email_address": {"address": "management@company.com"}}
            ],
            attachments=[{
                "name": "Meeting Materials.zip",
                "content": "Mock attachment"
            }]
        )
        
        # Verificaciones
        assert agenda["id"] == "agenda-123"
        assert slides["id"] == "slides-456"
        assert scheduled_meeting["id"] == "meeting-789"
        assert teams_meeting_created["id"] == "teams-meeting-123"
        assert shared_materials["id"] == "message-123"
        assert materials_sent["id"] == "email-789"

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery_workflow(self, integration_system):
        """Test manejo de errores y recuperación en flujo completo."""
        
        word_agent = integration_system.word_agent
        teams_agent = integration_system.teams_agent
        
        # Configurar respuestas de error simuladas
        error_responses = [
            Exception("Network timeout"),
            Exception("Rate limit exceeded"),
            {"id": "doc-123", "name": "Recovered Document.docx"}  # Éxito en reintento
        ]
        
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise error_responses[call_count - 1]
            return error_responses[call_count - 1]
        
        word_agent.graph_client.post.side_effect = side_effect
        
        # Mock recuperación exitosa en Teams
        teams_agent.graph_client.post.return_value = {
            "id": "message-123",
            "content": "Document recovered and shared successfully"
        }
        
        # Intentar crear documento con reintentos automáticos
        try:
            document = await word_agent.create_document(
                title="Important Document",
                content={"paragraphs": [{"text": "Critical business document"}]}
            )
            
            # Si llegamos aquí, la recuperación funcionó
            assert document["id"] == "doc-123"
            
            # Continuar con el flujo
            shared_message = await teams_agent.send_message(
                team_id="team-123",
                channel_id="general",
                content=f"New document available: {document['webUrl']}"
            )
            
            assert shared_message["id"] == "message-123"
            
        except Exception as e:
            pytest.fail(f"Error recovery failed: {e}")

    @pytest.mark.asyncio
    async def test_concurrent_operations_workflow(self, integration_system):
        """Test operaciones concurrentes en flujo completo."""
        
        word_agent = integration_system.word_agent
        excel_agent = integration_system.excel_agent
        powerpoint_agent = integration_system.powerpoint_agent
        teams_agent = integration_system.teams_agent
        
        # Mock respuestas exitosas para todas las operaciones
        word_agent.graph_client.post.return_value = {"id": "doc-123", "name": "Document.docx"}
        excel_agent.graph_client.post.return_value = {"id": "workbook-456", "name": "Data.xlsx"}
        powerpoint_agent.graph_client.post.return_value = {"id": "slides-789", "name": "Presentation.pptx"}
        teams_agent.graph_client.post.return_value = {"id": "message-123", "content": "Files shared"}
        
        # Ejecutar operaciones concurrentes
        tasks = [
            word_agent.create_document(
                title="Report Document",
                content={"paragraphs": [{"text": "Business report"}]}
            ),
            excel_agent.create_workbook(
                title="Sales Data",
                content={"worksheets": [{"name": "Sales", "data": [["Product", "Sales"]]}]}
            ),
            powerpoint_agent.create_presentation(
                title="Sales Presentation",
                slides=[{"layout": "title_slide", "title": "Sales Report"}]
            )
        ]
        
        # Esperar a que todas las operaciones terminen
        results = await asyncio.gather(*tasks)
        
        # Verificar que todas las operaciones tuvieron éxito
        assert len(results) == 3
        assert results[0]["id"] == "doc-123"
        assert results[1]["id"] == "workbook-456"
        assert results[2]["id"] == "slides-789"
        
        # Operación final de compartir todo en Teams
        share_task = teams_agent.send_message(
            team_id="team-123",
            channel_id="general",
            content="All project files have been created and are ready for review."
        )
        
        final_result = await share_task
        assert final_result["id"] == "message-123"