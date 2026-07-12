"""
Tests completos para Google Workspace Integration
Testing unitario e integración para todos los agentes
"""

import pytest
import asyncio
import os
import tempfile
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Importar agentes
from src.agents.enterprise import (
    BaseGoogleWorkspaceAgent,
    GoogleWorkspaceConfig,
    GoogleDocsAgent,
    GoogleSheetsAgent,
    GoogleDriveAgent,
    GoogleGmailAgent,
    GoogleCalendarAgent,
    GoogleWorkspaceService,
    AuthStatus,
    DocumentTemplate,
    DocumentStyle,
    ElementType,
    ChartType,
    FileType,
    PermissionRole,
    EmailTemplate,
    CalendarEvent,
    EventTime,
    EventAttendee,
    EventReminder,
    ReminderType,
    ComposeRequest
)


class TestGoogleWorkspaceConfig:
    """Tests para configuración de Google Workspace"""
    
    def test_config_creation(self):
        """Test creación de configuración"""
        config = GoogleWorkspaceConfig(
            client_id="test-client-id",
            client_secret="test-client-secret",
            project_id="test-project"
        )
        
        assert config.client_id == "test-client-id"
        assert config.client_secret == "test-client-secret"
        assert config.project_id == "test-project"
        assert len(config.scopes) > 0
    
    def test_config_is_configured(self):
        """Test verificación de configuración"""
        # Configuración completa
        config_complete = GoogleWorkspaceConfig(
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
        assert config_complete.is_configured is True
        
        # Configuración incompleta
        config_incomplete = GoogleWorkspaceConfig()
        assert config_incomplete.is_configured is False


class TestBaseGoogleWorkspaceAgent:
    """Tests para agente base"""
    
    @pytest.fixture
    def config(self):
        """Configuración de prueba"""
        return GoogleWorkspaceConfig(
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
    
    @pytest.fixture
    def base_agent(self, config):
        """Agente base de prueba"""
        return BaseGoogleWorkspaceAgent(config)
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, base_agent):
        """Test inicialización del agente"""
        assert base_agent.auth_status == AuthStatus.NOT_AUTHENTICATED
        assert base_agent.services == {}
        assert len(base_agent.operation_history) == 0
    
    @pytest.mark.asyncio
    async def test_auth_status(self, base_agent):
        """Test obtención de estado de autenticación"""
        status = await base_agent.get_auth_status()
        
        assert "status" in status
        assert "configured" in status
        assert "credentials_exists" in status
        assert "active_services" in status
    
    @pytest.mark.asyncio
    async def test_health_check(self, base_agent):
        """Test health check básico"""
        # Sin configuración
        health = await base_agent.health_check()
        assert health["healthy"] is False
        assert "not configured" in health.get("error", "").lower()


class TestGoogleDocsAgent:
    """Tests para Google Docs Agent"""
    
    @pytest.fixture
    def config(self):
        return GoogleWorkspaceConfig(
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
    
    @pytest.fixture
    def docs_agent(self, config):
        return GoogleDocsAgent(config)
    
    @pytest.mark.asyncio
    async def test_create_document(self, docs_agent):
        """Test creación de documento"""
        # Mock del servicio
        with patch.object(docs_agent, 'docs_service') as mock_service:
            mock_service.documents().create().execute.return_value = {
                'documentId': 'test-doc-id'
            }
            
            result = await docs_agent.create_document("Test Document")
            
            assert result.success is True
            assert result.data['document_id'] == 'test-doc-id'
            assert 'url' in result.data
    
    @pytest.mark.asyncio
    async def test_insert_text(self, docs_agent):
        """Test inserción de texto"""
        with patch.object(docs_agent, 'docs_service') as mock_service:
            result = await docs_agent.insert_text(
                document_id='test-doc-id',
                index=1,
                text="Test text",
                style=DocumentStyle.NORMAL
            )
            
            assert result.success is True
            assert result.data['inserted_length'] == len("Test text")
    
    @pytest.mark.asyncio
    async def test_health_check(self, docs_agent):
        """Test health check del agente Docs"""
        health = await docs_agent.health_check()
        
        assert "healthy" in health
        assert "service" in health
        assert "Google Docs Agent" in health["service"]


class TestGoogleSheetsAgent:
    """Tests para Google Sheets Agent"""
    
    @pytest.fixture
    def config(self):
        return GoogleWorkspaceConfig(
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
    
    @pytest.fixture
    def sheets_agent(self, config):
        return GoogleSheetsAgent(config)
    
    @pytest.mark.asyncio
    async def test_create_spreadsheet(self, sheets_agent):
        """Test creación de hoja de cálculo"""
        with patch.object(sheets_agent, 'sheets_service') as mock_service:
            mock_service.spreadsheets().create().execute.return_value = {
                'properties': {'spreadsheetId': 'test-sheet-id'}
            }
            
            result = await sheets_agent.create_spreadsheet(
                title="Test Sheet",
                sheets=["Data", "Charts"]
            )
            
            assert result.success is True
            assert result.data['spreadsheet_id'] == 'test-sheet-id'
    
    @pytest.mark.asyncio
    async def test_write_read_data(self, sheets_agent):
        """Test escritura y lectura de datos"""
        with patch.object(sheets_agent, 'sheets_service') as mock_service:
            # Mock escritura
            mock_service.spreadsheets().values().update().execute.return_value = {
                'updatedCells': 6
            }
            
            # Mock lectura
            mock_service.spreadsheets().values().get().execute.return_value = {
                'values': [
                    ["Producto", "Ventas"],
                    ["A", "100"],
                    ["B", "200"]
                ]
            }
            
            # Escribir datos
            write_result = await sheets_agent.write_data(
                spreadsheet_id='test-sheet-id',
                range_name="A1:B3",
                values=[["Producto", "Ventas"], ["A", "100"], ["B", "200"]]
            )
            
            assert write_result.success is True
            assert write_result.data['updated_cells'] == 6
            
            # Leer datos
            read_result = await sheets_agent.read_data(
                spreadsheet_id='test-sheet-id',
                range_name="A1:B3"
            )
            
            assert read_result.success is True
            assert len(read_result.data['values']) == 3
            assert read_result.data['values'][0] == ["Producto", "Ventas"]
    
    @pytest.mark.asyncio
    async def test_export_to_csv(self, sheets_agent):
        """Test exportación a CSV"""
        with patch.object(sheets_agent, 'sheets_service') as mock_service:
            mock_service.spreadsheets().values().get().execute.return_value = {
                'values': [
                    ["Producto", "Ventas", "Precio"],
                    ["A", "100", "50"],
                    ["B", "200", "75"]
                ]
            }
            
            result = await sheets_agent.export_to_csv(
                spreadsheet_id='test-sheet-id',
                sheet_name="Data"
            )
            
            assert result.success is True
            assert 'csv_data' in result.data
            assert result.data['row_count'] == 3
            assert result.data['column_count'] == 3


class TestGoogleDriveAgent:
    """Tests para Google Drive Agent"""
    
    @pytest.fixture
    def config(self):
        return GoogleWorkspaceConfig(
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
    
    @pytest.fixture
    def drive_agent(self, config):
        return GoogleDriveAgent(config)
    
    @pytest.mark.asyncio
    async def test_create_folder(self, drive_agent):
        """Test creación de carpeta"""
        with patch.object(drive_agent, 'drive_service') as mock_service:
            mock_service.files().create().execute.return_value = {
                'id': 'test-folder-id',
                'name': 'Test Folder',
                'webViewLink': 'https://drive.google.com/folder/test-folder-id'
            }
            
            result = await drive_agent.create_folder(
                name="Test Folder",
                parent_folder_id='parent-id'
            )
            
            assert result.success is True
            assert result.data['folder_id'] == 'test-folder-id'
            assert result.data['name'] == 'Test Folder'
    
    @pytest.mark.asyncio
    async def test_upload_file(self, drive_agent):
        """Test subida de archivo"""
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test file content")
            temp_file = f.name
        
        try:
            with patch.object(drive_agent, 'drive_service') as mock_service:
                mock_service.files().create().execute.return_value = {
                    'id': 'test-file-id',
                    'name': 'test.txt',
                    'size': '1024',
                    'createdTime': '2024-01-01T00:00:00Z',
                    'modifiedTime': '2024-01-01T00:00:00Z',
                    'webViewLink': 'https://drive.google.com/file/test-file-id'
                }
                
                result = await drive_agent.upload_file(temp_file)
                
                assert result.success is True
                assert result.data['file_id'] == 'test-file-id'
                assert result.data['file_name'] == 'test.txt'
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_search_files(self, drive_agent):
        """Test búsqueda de archivos"""
        with patch.object(drive_agent, 'drive_service') as mock_service:
            mock_service.files().list().execute.return_value = {
                'files': [
                    {
                        'id': 'file1',
                        'name': 'Document.pdf',
                        'mimeType': 'application/pdf',
                        'size': '1024',
                        'createdTime': '2024-01-01T00:00:00Z',
                        'modifiedTime': '2024-01-01T00:00:00Z'
                    }
                ]
            }
            
            result = await drive_agent.search_files(
                query="pdf",
                file_type=FileType.PDF
            )
            
            assert result.success is True
            assert result.data['total_results'] == 1
            assert result.data['search_results'][0]['name'] == 'Document.pdf'


class TestGoogleGmailAgent:
    """Tests para Google Gmail Agent"""
    
    @pytest.fixture
    def config(self):
        return GoogleWorkspaceConfig(
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
    
    @pytest.fixture
    def gmail_agent(self, config):
        return GoogleGmailAgent(config)
    
    @pytest.mark.asyncio
    async def test_send_email(self, gmail_agent):
        """Test envío de email"""
        with patch.object(gmail_agent, 'gmail_service') as mock_service:
            mock_service.users().messages().send().execute.return_value = {
                'id': 'message-123',
                'threadId': 'thread-123'
            }
            
            compose_request = ComposeRequest(
                to=["recipient@example.com"],
                subject="Test Subject",
                body="Test body content"
            )
            
            result = await gmail_agent.send_email(compose_request)
            
            assert result.success is True
            assert result.data['message_id'] == 'message-123'
            assert result.data['thread_id'] == 'thread-123'
    
    @pytest.mark.asyncio
    async def test_get_unread_emails(self, gmail_agent):
        """Test obtención de emails no leídos"""
        with patch.object(gmail_agent, 'gmail_service') as mock_service:
            # Mock lista de mensajes
            mock_service.users().messages().list().execute.return_value = {
                'messages': [
                    {'id': 'msg1'},
                    {'id': 'msg2'}
                ]
            }
            
            # Mock detalles de mensaje
            mock_service.users().messages().get().execute.return_value = {
                'id': 'msg1',
                'threadId': 'thread1',
                'labelIds': ['INBOX', 'UNREAD'],
                'payload': {
                    'headers': [
                        {'name': 'Subject', 'value': 'Test Email'},
                        {'name': 'From', 'value': 'sender@example.com'}
                    ]
                },
                'snippet': 'Test email content'
            }
            
            result = await gmail_agent.get_unread_emails(limit=10)
            
            assert result.success is True
            assert result.data['total_count'] == 2
            assert len(result.data['emails']) == 2


class TestGoogleCalendarAgent:
    """Tests para Google Calendar Agent"""
    
    @pytest.fixture
    def config(self):
        return GoogleWorkspaceConfig(
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
    
    @pytest.fixture
    def calendar_agent(self, config):
        return GoogleCalendarAgent(config)
    
    @pytest.mark.asyncio
    async def test_create_event(self, calendar_agent):
        """Test creación de evento"""
        with patch.object(calendar_agent, 'calendar_service') as mock_service:
            mock_service.events().insert().execute.return_value = {
                'id': 'event-123',
                'summary': 'Test Event',
                'htmlLink': 'https://calendar.google.com/event/event-123'
            }
            
            calendar_event = CalendarEvent(
                summary="Test Event",
                description="Test description",
                start_time=EventTime(
                    date_time=datetime(2024, 11, 15, 14, 0),
                    timezone="UTC"
                ),
                end_time=EventTime(
                    date_time=datetime(2024, 11, 15, 15, 0),
                    timezone="UTC"
                ),
                attendees=[
                    EventAttendee(email="attendee@example.com")
                ],
                reminders=[
                    EventReminder(method=ReminderType.EMAIL, minutes_before_start=60)
                ]
            )
            
            result = await calendar_agent.create_event(calendar_event)
            
            assert result.success is True
            assert result.data['event']['summary'] == 'Test Event'
            assert result.data['event_id'] == 'event-123'
    
    @pytest.mark.asyncio
    async def test_find_available_slots(self, calendar_agent):
        """Test búsqueda de slots disponibles"""
        with patch.object(calendar_agent, 'calendar_service') as mock_service:
            # Mock calendario
            mock_service.calendarList().list().execute.return_value = {
                'items': [
                    {
                        'id': 'primary',
                        'timeZone': 'UTC',
                        'primary': True
                    }
                ]
            }
            
            # Mock lista de eventos vacía
            mock_service.events().list().execute.return_value = {
                'items': []
            }
            
            result = await calendar_agent.find_available_slots(
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=1),
                duration_minutes=60,
                attendees=["attendee@example.com"]
            )
            
            assert result.success is True
            assert result.data['total_slots'] > 0
            assert 'available_slots' in result.data
    
    @pytest.mark.asyncio
    async def test_schedule_meeting(self, calendar_agent):
        """Test programación automática de reunión"""
        with patch.object(calendar_agent, 'find_available_slots') as mock_find_slots:
            with patch.object(calendar_agent, 'create_event') as mock_create:
                # Mock slots disponibles
                mock_find_slots.return_value = type('Result', (), {
                    'success': True,
                    'data': {
                        'available_slots': [{
                            'start_time': datetime(2024, 11, 15, 14, 0),
                            'end_time': datetime(2024, 11, 15, 15, 0),
                            'score': 100.0
                        }]
                    }
                })()
                
                # Mock creación de evento
                mock_create.return_value = type('Result', (), {
                    'success': True,
                    'data': {
                        'event': {
                            'summary': 'Auto Scheduled Meeting',
                            'id': 'event-123'
                        }
                    }
                })()
                
                result = await calendar_agent.schedule_meeting(
                    title="Auto Meeting",
                    attendees=["attendee@example.com"],
                    duration_minutes=60
                )
                
                assert result.success is True
                assert result.data['meeting_scheduled'] is True
                assert result.data['event']['summary'] == 'Auto Scheduled Meeting'


class TestIntegration:
    """Tests de integración entre agentes"""
    
    @pytest.fixture
    def config(self):
        return GoogleWorkspaceConfig(
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
    
    @pytest.mark.asyncio
    async def test_workflow_crear_y_compartir_reporte(self, config):
        """Test flujo completo: crear reporte en Docs y compartir"""
        # Mock todos los servicios
        with patch.multiple(
            'src.agents.enterprise.google_docs_agent.GoogleDocsAgent',
            authenticate=AsyncMock(),
            get_service=AsyncMock()
        ):
            docs_agent = GoogleDocsAgent(config)
            
            with patch.object(docs_agent, 'docs_service') as mock_docs:
                # Mock creación de documento
                mock_docs.documents().create().execute.return_value = {
                    'documentId': 'doc-123',
                    'title': 'Reporte Mensual'
                }
                
                # Mock inserción de texto
                mock_docs.documents().batchUpdate().execute.return_value = {}
                
                # Crear documento
                result = await docs_agent.create_document(
                    title="Reporte Mensual",
                    content="Contenido inicial del reporte"
                )
                
                assert result.success is True
                assert result.data['document_id'] == 'doc-123'
    
    @pytest.mark.asyncio
    async def test_workflow_analisis_datos_y_grafico(self, config):
        """Test flujo: análisis de datos en Sheets y creación de gráfico"""
        sheets_agent = GoogleSheetsAgent(config)
        
        with patch.object(sheets_agent, 'sheets_service') as mock_sheets:
            # Mock creación de hoja
            mock_sheets.spreadsheets().create().execute.return_value = {
                'properties': {'spreadsheetId': 'sheet-123'}
            }
            
            # Mock escritura de datos
            mock_sheets.spreadsheets().values().update().execute.return_value = {
                'updatedCells': 9
            }
            
            # Mock batchUpdate para gráfico
            mock_sheets.spreadsheets().batchUpdate().execute.return_value = {
                'replies': [{
                    'addChart': {
                        'chart': {
                            'chartId': 123
                        }
                    }
                }]
            }
            
            # Crear hoja y agregar datos
            result = await sheets_agent.create_spreadsheet("Análisis de Ventas")
            assert result.success is True
            
            await sheets_agent.write_data(
                spreadsheet_id='sheet-123',
                range_name="A1:C4",
                values=[
                    ["Producto", "Ventas", "Meta"],
                    ["A", 100, 120],
                    ["B", 200, 180],
                    ["C", 150, 200]
                ]
            )
            
            # Crear gráfico
            from src.agents.enterprise import ChartConfig
            chart_config = ChartConfig(
                chart_type=ChartType.COLUMN,
                title="Ventas vs Meta",
                data_range="A1:C4",
                position={"row": 10, "column": 1}
            )
            
            chart_result = await sheets_agent.create_chart(
                spreadsheet_id='sheet-123',
                sheet_name="Charts",
                config=chart_config
            )
            
            assert chart_result.success is True


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])