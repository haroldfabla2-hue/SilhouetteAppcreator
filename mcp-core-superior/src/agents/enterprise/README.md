# Google Workspace Integration - Documentación Completa

## Resumen

La integración completa con Google Workspace proporciona agentes especializados para todos los servicios principales de Google:

- **Google Docs**: Creación, edición y gestión de documentos
- **Google Sheets**: Análisis de datos, reportes y automatización
- **Google Drive**: Gestión de archivos y sincronización
- **Google Gmail**: Automatización de email y análisis de comunicaciones
- **Google Calendar**: Gestión de eventos y programación

## Características Principales

### 🔐 Autenticación OAuth2
- Configuración segura de credenciales
- Renovación automática de tokens
- Manejo de permisos granulares

### 🚀 APIs Completas
- Acceso a todas las funciones de Google Workspace
- Operaciones en lote para eficiencia
- Rate limiting inteligente

### 📊 Análisis Avanzado
- Análisis estadístico de datos
- Reportes automáticos
- Monitoreo y métricas

### 🔄 Automatización
- Respuestas automáticas
- Programación inteligente de reuniones
- Sincronización bidireccional

## Instalación y Configuración

### 1. Configuración del Proyecto Google

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear nuevo proyecto o seleccionar existente
3. Habilitar APIs necesarias:
   - Google Docs API
   - Google Sheets API
   - Google Drive API
   - Gmail API
   - Google Calendar API
   - Google Slides API
   - Google Forms API
   - Google Keep API

### 2. Crear Credenciales OAuth2

```bash
# En Google Cloud Console
1. Ir a "APIs & Services" > "Credentials"
2. Crear OAuth 2.0 Client ID
3. Tipo de aplicación: "Aplicación web"
4. URI de redirección autorizados: http://localhost:8080
5. Descargar archivo JSON de credenciales
```

### 3. Configuración del Agente

```python
from src.agents.enterprise import GoogleWorkspaceConfig, GoogleDocsAgent

# Configurar credenciales
config = GoogleWorkspaceConfig(
    client_id="your-client-id",
    client_secret="your-client-secret",
    project_id="your-project-id",
    credentials_file="path/to/credentials.json",
    token_file="path/to/token.pickle"
)

# Inicializar agente
docs_agent = GoogleDocsAgent(config)
```

## Agentes Disponibles

### GoogleDocsAgent

#### Funcionalidades
- Crear y editar documentos
- Aplicar estilos y formato
- Insertar tablas, listas e imágenes
- Convertir formatos
- Analizar contenido
- Buscar y reemplazar
- Gestionar permisos

#### Ejemplo de Uso

```python
from src.agents.enterprise import GoogleDocsAgent, GoogleWorkspaceConfig, DocumentTemplate, DocumentStyle, ElementType

# Configurar agente
config = GoogleWorkspaceConfig(
    client_id="your-client-id",
    client_secret="your-client-secret"
)
docs_agent = GoogleDocsAgent(config)

# Autenticar
await docs_agent.authenticate()

# Crear documento
result = await docs_agent.create_document(
    title="Reporte Mensual",
    content="Este es el contenido inicial del reporte."
)

if result.success:
    document_id = result.data['document_id']
    
    # Insertar tabla
    await docs_agent.insert_table(
        document_id=document_id,
        index=1,
        rows=5,
        columns=3,
        headers=["Producto", "Cantidad", "Precio"]
    )
    
    # Aplicar estilos
    await docs_agent.insert_text(
        document_id=document_id,
        index=1,
        text="RESUMEN EJECUTIVO",
        style=DocumentStyle.HEADING_1
    )
```

### GoogleSheetsAgent

#### Funcionalidades
- Crear y editar hojas de cálculo
- Análisis estadístico de datos
- Creación de gráficos dinámicos
- Tablas dinámicas (Pivot Tables)
- Importación y exportación de datos
- Automatización con fórmulas
- Reportes automáticos

#### Ejemplo de Uso

```python
from src.agents.enterprise import GoogleSheetsAgent, GoogleWorkspaceConfig, ChartType, ReportConfig, ChartConfig

# Configurar agente
config = GoogleWorkspaceConfig(
    client_id="your-client-id",
    client_secret="your-client-secret"
)
sheets_agent = GoogleSheetsAgent(config)
await sheets_agent.authenticate()

# Crear hoja de cálculo
result = await sheets_agent.create_spreadsheet(
    title="Análisis de Ventas",
    sheets=["Datos", "Gráficos", "Resumen"]
)

if result.success:
    spreadsheet_id = result.data['spreadsheet_id']
    
    # Escribir datos
    await sheets_agent.write_data(
        spreadsheet_id=spreadsheet_id,
        range_name="A1:D10",
        values=[
            ["Producto", "Enero", "Febrero", "Marzo"],
            ["Producto A", 100, 150, 200],
            ["Producto B", 80, 120, 90],
            # ... más datos
        ]
    )
    
    # Crear gráfico
    chart_config = ChartConfig(
        chart_type=ChartType.COLUMN,
        title="Ventas por Producto",
        data_range="A1:D4",
        position={"row": 10, "column": 1}
    )
    
    await sheets_agent.create_chart(
        spreadsheet_id=spreadsheet_id,
        sheet_name="Gráficos",
        config=chart_config
    )
    
    # Analizar datos
    analysis = await sheets_agent.analyze_data(
        spreadsheet_id=spreadsheet_id,
        range_name="A1:D10"
    )
    
    print(f"Análisis: {analysis.data}")
```

### GoogleDriveAgent

#### Funcionalidades
- Subir y descargar archivos
- Gestión de carpetas y estructura
- Búsqueda avanzada de archivos
- Gestión de permisos y compartir
- Sincronización bidireccional
- Versionado de archivos
- Operaciones en lote

#### Ejemplo de Uso

```python
from src.agents.enterprise import GoogleDriveAgent, GoogleWorkspaceConfig, FileType, PermissionRole

# Configurar agente
config = GoogleWorkspaceConfig(
    client_id="your-client-id",
    client_secret="your-client-secret"
)
drive_agent = GoogleDriveAgent(config)
await drive_agent.authenticate()

# Crear carpeta
folder_result = await drive_agent.create_folder("Proyectos 2024")
if folder_result.success:
    folder_id = folder_result.data['folder_id']
    
    # Subir archivo
    upload_result = await drive_agent.upload_file(
        file_path="/path/to/document.pdf",
        parent_folder_id=folder_id
    )
    
    if upload_result.success:
        file_id = upload_result.data['file_id']
        
        # Compartir archivo
        await drive_agent.share_file(
            file_id=file_id,
            email="colaborador@empresa.com",
            role=PermissionRole.WRITER
        )
        
        # Buscar archivos
        search_result = await drive_agent.search_files(
            query="documentos importantes",
            file_type=FileType.PDF
        )
        
        print(f"Archivos encontrados: {search_result.data['total_results']}")
```

### GoogleGmailAgent

#### Funcionalidades
- Enviar emails automatizados
- Leer y analizar mensajes
- Gestionar etiquetas y filtros
- Búsqueda avanzada de emails
- Estadísticas de comunicación
- Plantillas de email
- Adjuntos y multimedia

#### Ejemplo de Uso

```python
from src.agents.enterprise import GoogleGmailAgent, GoogleWorkspaceConfig, EmailTemplate, ComposeRequest, EmailPriority

# Configurar agente
config = GoogleWorkspaceConfig(
    client_id="your-client-id",
    client_secret="your-client-secret"
)
gmail_agent = GoogleGmailAgent(config)
await gmail_agent.authenticate()

# Crear plantilla
template = EmailTemplate(
    name="weekly_report",
    subject="Reporte Semanal - {fecha}",
    body="Estimado equipo,\n\nAdjunto el reporte semanal...",
    signature="Saludos,\nEquipo de Desarrollo"
)

# Guardar plantilla
gmail_agent.email_templates["weekly_report"] = template

# Enviar email con plantilla
result = await gmail_agent.send_template_email(
    template_name="weekly_report",
    recipients=["equipo@empresa.com"],
    subject_override="Reporte Semanal - 15 Nov 2024"
)

if result.success:
    print(f"Email enviado: {result.data['message_id']}")

# Obtener emails no leídos
unread_emails = await gmail_agent.get_unread_emails(limit=10)
print(f"Emails no leídos: {unread_emails.data['total_count']}")
```

### GoogleCalendarAgent

#### Funcionalidades
- Crear y gestionar eventos
- Búsqueda inteligente de disponibilidad
- Programación automática de reuniones
- Recordatorios y notificaciones
- Gestión de múltiples calendarios
- Análisis de patrones de programación
- Integración con otros servicios

#### Ejemplo de Uso

```python
from src.agents.enterprise import GoogleCalendarAgent, GoogleWorkspaceConfig, CalendarEvent, EventAttendee, EventReminder, ReminderType

# Configurar agente
config = GoogleWorkspaceConfig(
    client_id="your-client-id",
    client_secret="your-client-secret"
)
calendar_agent = GoogleCalendarAgent(config)
await calendar_agent.authenticate()

# Programar reunión automáticamente
result = await calendar_agent.schedule_meeting(
    title="Revisión de Proyecto",
    attendees=["jefe@empresa.com", "desarrollador@empresa.com"],
    duration_minutes=60,
    location="Sala de Conferencias A"
)

if result.success:
    print(f"Reunión programada: {result.data['event']['summary']}")
    
    # Crear evento personalizado
    calendar_event = CalendarEvent(
        summary="Sesión de Entrenamiento",
        description="Entrenamiento en nuevas tecnologías",
        location="Sala de Entrenamiento",
        start_time=EventTime(
            date_time=datetime(2024, 11, 15, 14, 0),  # 15 Nov, 2 PM
            timezone="America/New_York"
        ),
        end_time=EventTime(
            date_time=datetime(2024, 11, 15, 16, 0),
            timezone="America/New_York"
        ),
        attendees=[
            EventAttendee(email="equipo@empresa.com")
        ],
        reminders=[
            EventReminder(method=ReminderType.EMAIL, minutes_before_start=60),
            EventReminder(method=ReminderType.POPUP, minutes_before_start=15)
        ]
    )
    
    await calendar_agent.create_event(calendar_event)
    
    # Buscar slots disponibles
    available_slots = await calendar_agent.find_available_slots(
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=7),
        duration_minutes=90,
        attendees=["equipo@empresa.com"]
    )
    
    print(f"Slots disponibles: {available_slots.data['total_slots']}")
```

## Integración con el Sistema

### Con el Orquestador

Los agentes Google Workspace están integrados con el sistema de orquestación multi-agente:

```python
from src.agents.enterprise import (
    GoogleDocsAgent, 
    GoogleSheetsAgent, 
    GoogleGmailAgent,
    GoogleCalendarAgent
)

# Crear instancias de agentes
docs_agent = GoogleDocsAgent(config)
sheets_agent = GoogleSheetsAgent(config)
gmail_agent = GoogleGmailAgent(config)
calendar_agent = GoogleCalendarAgent(config)

# El orquestador puede usar estos agentes para tareas complejas
```

### Contexto de Colaboración

Los agentes pueden trabajar juntos para flujos de trabajo complejos:

```python
# Ejemplo: Generar reporte mensual y enviar por email
async def generar_y_enviar_reporte():
    # 1. Crear documento en Google Docs
    docs_result = await docs_agent.create_document("Reporte Mensual")
    
    # 2. Poblar con datos de Google Sheets
    data = await sheets_agent.read_data(spreadsheet_id, "Datos!A1:Z100")
    # ... procesar datos
    
    # 3. Programar envío por email
    calendar_event = CalendarEvent(
        summary="Enviar Reporte Mensual",
        start_time=EventTime(date_time=next_friday_2pm),
        attendees=[EventAttendee(email="gerencia@empresa.com")]
    )
    await calendar_agent.create_event(calendar_event)
```

## Configuración Avanzada

### Rate Limiting

```python
# Configurar límites de rate
config = GoogleWorkspaceConfig(
    client_id="...",
    client_secret="...",
    # Los límites se aplican automáticamente
    # 100 requests/100seg por usuario
    # 1000 requests/100seg por proyecto
)
```

### Manejo de Errores

```python
# Todos los agentes manejan errores automáticamente
try:
    result = await docs_agent.create_document("Test")
    if not result.success:
        print(f"Error: {result.error}")
        # Manejar error específico
except Exception as e:
    # Error no capturado - revisar logs
    print(f"Error inesperado: {e}")
```

### Logging y Monitoreo

```python
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Los agentes registran automáticamente:
# - Operaciones realizadas
# - Tiempos de ejecución
# - Errores y warnings
# - Métricas de performance
```

## Mejores Prácticas

### 1. Autenticación
- Manejar tokens de forma segura
- Renovar tokens antes de que expiren
- Revocar acceso cuando no se necesite

### 2. Rate Limiting
- Respetar límites de API
- Implementar backoff exponencial
- Monitorear cuotas de uso

### 3. Manejo de Datos
- Validar datos antes de enviar
- Manejar límites de tamaño
- Implementar retry logic

### 4. Seguridad
- No exponer credenciales
- Validar permisos de usuario
- Auditar accesos regulares

## Troubleshooting

### Errores Comunes

#### Error de Autenticación
```python
# Verificar configuración
auth_status = await agent.get_auth_status()
print(f"Estado: {auth_status}")

# Re-autenticar si es necesario
if auth_status["status"] == "expired":
    await agent.authenticate(force_refresh=True)
```

#### Error de Rate Limit
```python
# Implementar backoff
import asyncio

async def hacer_llamada_con_retry(agent, operation, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await operation()
        except Exception as e:
            if "rate limit" in str(e).lower():
                await asyncio.sleep(2 ** attempt)  # Backoff exponencial
                continue
            raise
```

#### Error de Permisos
```python
# Verificar scopes y permisos
try:
    result = await agent.operation()
except Exception as e:
    if "insufficient permissions" in str(e).lower():
        print("Verificar permisos de la aplicación en Google Cloud Console")
```

### Logs de Diagnóstico

```python
# Habilitar logging detallado
import logging
logging.getLogger('src.agents.enterprise').setLevel(logging.DEBUG)

# Verificar health check
health = await agent.health_check()
print(f"Salud del agente: {health}")
```

## Contribuciones

Para contribuir al desarrollo de la integración Google Workspace:

1. Fork del repositorio
2. Crear rama feature
3. Implementar funcionalidad
4. Agregar tests
5. Documentar cambios
6. Crear Pull Request

## Soporte

- Documentación: Ver archivos en `/docs/`
- Issues: Reportar en el repositorio del proyecto
- Email: soporte@mcpsuperior.com

## Licencia

Este módulo está licenciado bajo la misma licencia del proyecto MCP Server Superior.