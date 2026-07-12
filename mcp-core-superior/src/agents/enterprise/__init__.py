"""
Enterprise Google Workspace Integration Package
Integración completa con Google Workspace para MCP Server Superior

Esta integración proporciona agentes especializados para:
- Google Docs: Creación y edición de documentos
- Google Sheets: Análisis de datos y reportes
- Google Drive: Gestión de archivos y sincronización
- Google Gmail: Automatización de email
- Google Calendar: Gestión de eventos y programación

Incluye autenticación OAuth2, APIs completas, workflows empresariales
y configuración centralizada.

Ejemplo de uso básico:

    from src.agents.enterprise import GoogleWorkspaceConfig, GoogleDocsAgent
    
    config = GoogleWorkspaceConfig(
        client_id="your-client-id",
        client_secret="your-client-secret"
    )
    
    agent = GoogleDocsAgent(config)
    await agent.authenticate()
    
    result = await agent.create_document("Mi Documento")
    print(f"Documento creado: {result.data['document_id']}")
"""

from .base_google_workspace_agent import (
    BaseGoogleWorkspaceAgent,
    GoogleWorkspaceService,
    GoogleWorkspaceConfig,
    AuthStatus,
    ApiResponse,
    OperationLog
)

from .google_docs_agent import (
    GoogleDocsAgent,
    DocumentStyle,
    ElementType,
    DocumentElement,
    DocumentTemplate,
    DocumentAnalysis
)

from .google_sheets_agent import (
    GoogleSheetsAgent,
    CellFormat,
    ChartType,
    PivotFunction,
    CellData,
    RangeData,
    ChartConfig,
    PivotConfig,
    DataAnalysis,
    ReportConfig
)

from .google_drive_agent import (
    GoogleDriveAgent,
    FileType,
    PermissionRole,
    FileStatus,
    FileMetadata,
    FolderStructure,
    SyncOperation,
    BatchOperation
)

from .google_gmail_agent import (
    GoogleGmailAgent,
    EmailLabel,
    AttachmentType,
    EmailPriority,
    EmailMessage,
    EmailFilter,
    EmailTemplate,
    EmailStatistics,
    ComposeRequest
)

from .google_calendar_agent import (
    GoogleCalendarAgent,
    EventStatus,
    EventVisibility,
    EventPriority,
    ReminderType,
    AttendeeStatus,
    EventTime,
    EventAttendee,
    EventReminder,
    CalendarEvent,
    Calendar,
    MeetingSlot,
    EventTemplate,
    ScheduleAnalysis
)

__all__ = [
    # Base
    'BaseGoogleWorkspaceAgent',
    'GoogleWorkspaceService',
    'GoogleWorkspaceConfig',
    'AuthStatus',
    'ApiResponse',
    'OperationLog',
    
    # Google Docs
    'GoogleDocsAgent',
    'DocumentStyle',
    'ElementType',
    'DocumentElement',
    'DocumentTemplate',
    'DocumentAnalysis',
    
    # Google Sheets
    'GoogleSheetsAgent',
    'CellFormat',
    'ChartType',
    'PivotFunction',
    'CellData',
    'RangeData',
    'ChartConfig',
    'PivotConfig',
    'DataAnalysis',
    'ReportConfig',
    
    # Google Drive
    'GoogleDriveAgent',
    'FileType',
    'PermissionRole',
    'FileStatus',
    'FileMetadata',
    'FolderStructure',
    'SyncOperation',
    'BatchOperation',
    
    # Google Gmail
    'GoogleGmailAgent',
    'EmailLabel',
    'AttachmentType',
    'EmailPriority',
    'EmailMessage',
    'EmailFilter',
    'EmailTemplate',
    'EmailStatistics',
    'ComposeRequest',
    
    # Google Calendar
    'GoogleCalendarAgent',
    'EventStatus',
    'EventVisibility',
    'EventPriority',
    'ReminderType',
    'AttendeeStatus',
    'EventTime',
    'EventAttendee',
    'EventReminder',
    'CalendarEvent',
    'Calendar',
    'MeetingSlot',
    'EventTemplate',
    'ScheduleAnalysis',
    
    # Configuración centralizada
    'GoogleWorkspaceEnterpriseConfig',
    'GoogleWorkspaceConfigManager',
    'GoogleWorkspaceEnterpriseInitializer',
    
    # Workflows empresariales
    'GoogleWorkspaceWorkflowManager'
]

# Configuración centralizada
from .config import (
    GoogleWorkspaceEnterpriseConfig,
    GoogleWorkspaceConfigManager,
    GoogleWorkspaceEnterpriseInitializer
)

from .examples import (
    GoogleWorkspaceWorkflowManager
)

# Información del paquete
__version__ = "1.0.0"
__author__ = "MCP Server Superior Team"
__description__ = "Integración completa con Google Workspace para MCP Server Superior"
__keywords__ = ["google", "workspace", "gmail", "drive", "docs", "sheets", "calendar", "mcp", "agents"]