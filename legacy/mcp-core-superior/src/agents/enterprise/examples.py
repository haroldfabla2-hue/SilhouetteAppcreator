"""
Ejemplo completo de uso de Google Workspace Enterprise Agents
Demuestra integración entre todos los agentes para flujos de trabajo empresariales
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from pathlib import Path

from . import (
    GoogleWorkspaceEnterpriseConfig,
    GoogleWorkspaceConfigManager,
    GoogleWorkspaceEnterpriseInitializer,
    GoogleDocsAgent,
    GoogleSheetsAgent,
    GoogleDriveAgent,
    GoogleGmailAgent,
    GoogleCalendarAgent,
    GoogleWorkspaceService,
    DocumentTemplate,
    DocumentStyle,
    ElementType,
    ChartType,
    ChartConfig,
    PivotConfig,
    FileType,
    PermissionRole,
    EmailTemplate,
    ComposeRequest,
    EmailPriority,
    CalendarEvent,
    EventTime,
    EventAttendee,
    EventReminder,
    ReminderType
)


class GoogleWorkspaceWorkflowManager:
    """Gestor de flujos de trabajo completos con Google Workspace"""
    
    def __init__(self, config_path: str = "google_workspace_config.json"):
        self.config_manager = GoogleWorkspaceConfigManager(config_path)
        self.config = self.config_manager.load_config()
        self.logger = logging.getLogger(__name__)
        
        # Inicializar agentes
        self.agents = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Inicializar todos los agentes"""
        services = [
            (GoogleWorkspaceService.DOCS, GoogleDocsAgent),
            (GoogleWorkspaceService.SHEETS, GoogleSheetsAgent),
            (GoogleWorkspaceService.DRIVE, GoogleDriveAgent),
            (GoogleWorkspaceService.GMAIL, GoogleGmailAgent),
            (GoogleWorkspaceService.CALENDAR, GoogleCalendarAgent)
        ]
        
        for service, agent_class in services:
            try:
                agent_config = self.config_manager.create_agent_config(service, self.config)
                self.agents[service.value] = agent_class(agent_config)
                self.logger.info(f"Agente {service.value} inicializado")
            except Exception as e:
                self.logger.error(f"Error inicializando agente {service.value}: {e}")
    
    async def workflow_crear_reporte_ejecutivo(self, datos_ventas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Flujo completo: Crear reporte ejecutivo en Docs y distribuir por email
        
        Args:
            datos_ventas: Datos de ventas para el reporte
            
        Returns:
            Resultado del workflow
        """
        try:
            self.logger.info("Iniciando workflow: Crear Reporte Ejecutivo")
            
            # Paso 1: Crear documento en Google Docs
            docs_agent = self.agents['docs']
            await docs_agent.authenticate()
            
            report_template = DocumentTemplate(
                name="reporte_ejecutivo",
                description="Plantilla para reportes ejecutivos",
                elements=[
                    DocumentElement(
                        type=ElementType.PARAGRAPH,
                        content="REPORTE EJECUTIVO DE VENTAS",
                        style=DocumentStyle.HEADING_1
                    ),
                    DocumentElement(
                        type=ElementType.PARAGRAPH,
                        content="Resumen del período: {fecha}",
                        style=DocumentStyle.NORMAL
                    ),
                    DocumentElement(
                        type=ElementType.PARAGRAPH,
                        content="ANÁLISIS DE VENTAS",
                        style=DocumentStyle.HEADING_2
                    )
                ]
            )
            
            doc_result = await docs_agent.create_document(
                title=f"Reporte Ejecutivo - {datetime.now().strftime('%Y-%m-%d')}",
                template=report_template
            )
            
            if not doc_result.success:
                return {"success": False, "error": f"Error creando documento: {doc_result.error}"}
            
            document_id = doc_result.data['document_id']
            
            # Paso 2: Crear análisis de datos en Google Sheets
            sheets_agent = self.agents['sheets']
            
            # Preparar datos para el análisis
            headers = ["Producto", "Ventas Enero", "Ventas Febrero", "Ventas Marzo", "Total", "Meta", "Cumplimiento %"]
            analysis_data = [headers]
            
            total_ventas = 0
            for item in datos_ventas:
                ventas_enero = item.get('ventas_enero', 0)
                ventas_febrero = item.get('ventas_febrero', 0)
                ventas_marzo = item.get('ventas_marzo', 0)
                meta = item.get('meta', 100)
                total = ventas_enero + ventas_febrero + ventas_marzo
                cumplimiento = (total / meta) * 100 if meta > 0 else 0
                
                analysis_data.append([
                    item.get('producto', 'Producto'),
                    ventas_enero,
                    ventas_febrero,
                    ventas_marzo,
                    total,
                    meta,
                    round(cumplimiento, 2)
                ])
                
                total_ventas += total
            
            # Crear hoja de cálculo
            sheet_result = await sheets_agent.create_spreadsheet(
                title=f"Análisis Ventas - {datetime.now().strftime('%Y-%m-%d')}",
                sheets=["Datos", "Análisis", "Gráficos"]
            )
            
            if not sheet_result.success:
                return {"success": False, "error": f"Error creando hoja: {sheet_result.error}"}
            
            spreadsheet_id = sheet_result.data['spreadsheet_id']
            
            # Escribir datos
            await sheets_agent.write_data(
                spreadsheet_id=spreadsheet_id,
                range_name="A1:G10",
                values=analysis_data[:10]  # Limitar a 10 filas
            )
            
            # Crear gráfico
            chart_config = ChartConfig(
                chart_type=ChartType.COLUMN,
                title="Ventas por Producto",
                data_range="A1:F6",
                position={"row": 10, "column": 1}
            )
            
            await sheets_agent.create_chart(
                spreadsheet_id=spreadsheet_id,
                sheet_name="Gráficos",
                config=chart_config
            )
            
            # Paso 3: Crear evento de seguimiento en Calendar
            calendar_agent = self.agents['calendar']
            meeting_date = datetime.now() + timedelta(days=7, hours=14)  # Próxima semana
            
            follow_up_event = CalendarEvent(
                summary="Revisión Reporte Ejecutivo - Ventas",
                description=f"Revisión del reporte ejecutivo generado el {datetime.now().strftime('%Y-%m-%d')}",
                start_time=EventTime(
                    date_time=meeting_date,
                    timezone="UTC"
                ),
                end_time=EventTime(
                    date_time=meeting_date + timedelta(hours=1),
                    timezone="UTC"
                ),
                attendees=[
                    EventAttendee(email="gerencia@empresa.com"),
                    EventAttendee(email="ventas@empresa.com")
                ],
                reminders=[
                    EventReminder(method=ReminderType.EMAIL, minutes_before_start=1440),  # 1 día
                    EventReminder(method=ReminderType.POPUP, minutes_before_start=15)
                ]
            )
            
            await calendar_agent.create_event(follow_up_event)
            
            # Paso 4: Enviar resumen por email
            gmail_agent = self.agents['gmail']
            
            # Crear plantilla de resumen
            summary_template = EmailTemplate(
                name="reporte_ejecutivo_summary",
                subject="Reporte Ejecutivo de Ventas - {fecha}",
                body=f"""
Estimado Equipo,

Se ha generado el reporte ejecutivo de ventas correspondiente al {datetime.now().strftime('%Y-%m-%d')}.

RESUMEN:
- Total de ventas: {total_ventas:,}
- Productos analizados: {len(datos_ventas)}
- Documento: {doc_result.data.get('url', 'N/A')}
- Análisis detallado: {sheet_result.data.get('url', 'N/A')}

Se ha programado una reunión de seguimiento para revisar los resultados.

Saludos,
Sistema de Reportes Automatizados
                """,
                signature="Sistema Automatizado de Reportes"
            )
            
            # Enviar email de resumen
            compose_request = ComposeRequest(
                to=["gerencia@empresa.com", "ventas@empresa.com"],
                cc=["admin@empresa.com"],
                subject=f"Reporte Ejecutivo de Ventas - {datetime.now().strftime('%Y-%m-%d')}",
                body=summary_template.body,
                priority=EmailPriority.HIGH
            )
            
            email_result = await gmail_agent.send_email(compose_request)
            
            # Paso 5: Guardar archivos en Drive para archivo
            drive_agent = self.agents['drive']
            
            # Crear carpeta para el mes
            folder_name = f"Reportes_{datetime.now().strftime('%Y_%m')}"
            folder_result = await drive_agent.create_folder(folder_name)
            
            if folder_result.success:
                folder_id = folder_result.data['folder_id']
                
                # En un escenario real, aquí se subirían los archivos generados
                # Por ahora, solo registramos los IDs
                await drive_agent.share_file(
                    file_id=document_id,
                    email="gerencia@empresa.com",
                    role=PermissionRole.READER
                )
            
            self.logger.info("Workflow de reporte ejecutivo completado")
            
            return {
                "success": True,
                "workflow": "reporte_ejecutivo",
                "document_id": document_id,
                "spreadsheet_id": spreadsheet_id,
                "email_sent": email_result.success,
                "event_created": True,
                "total_ventas": total_ventas,
                "products_analyzed": len(datos_ventas)
            }
            
        except Exception as e:
            self.logger.error(f"Error en workflow: {e}")
            return {"success": False, "error": str(e)}
    
    async def workflow_coordinacion_reunion_completa(self, participantes: List[str], duracion_minutos: int = 60) -> Dict[str, Any]:
        """
        Flujo completo: Coordinar reunión desde programación hasta seguimiento
        
        Args:
            participantes: Lista de emails de participantes
            duracion_minutos: Duración de la reunión
            
        Returns:
            Resultado del workflow
        """
        try:
            self.logger.info("Iniciando workflow: Coordinación Completa de Reunión")
            
            # Paso 1: Buscar slot disponible
            calendar_agent = self.agents['calendar']
            
            slots_result = await calendar_agent.find_available_slots(
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=14),
                duration_minutes=duracion_minutos,
                attendees=participantes
            )
            
            if not slots_result.success or not slots_result.data['available_slots']:
                return {"success": False, "error": "No hay slots disponibles"}
            
            best_slot = slots_result.data['available_slots'][0]
            
            # Paso 2: Crear evento en calendario
            meeting_event = CalendarEvent(
                summary="Reunión de Coordinación de Proyecto",
                description=f"Reunión programada automáticamente para coordinación de proyecto.\n\nDuración: {duracion_minutos} minutos\nParticipantes: {', '.join(participantes)}",
                start_time=EventTime(
                    date_time=best_slot['start_time'],
                    timezone="UTC"
                ),
                end_time=EventTime(
                    date_time=best_slot['end_time'],
                    timezone="UTC"
                ),
                attendees=[EventAttendee(email=email) for email in participantes],
                reminders=[
                    EventReminder(method=ReminderType.EMAIL, minutes_before_start=60),
                    EventReminder(method=ReminderType.EMAIL, minutes_before_start=1440),  # 1 día
                    EventReminder(method=ReminderType.POPUP, minutes_before_start=15)
                ]
            )
            
            event_result = await calendar_agent.create_event(meeting_event)
            
            if not event_result.success:
                return {"success": False, "error": f"Error creando evento: {event_result.error}"}
            
            # Paso 3: Crear documento de agenda
            docs_agent = self.agents['docs']
            
            agenda_template = DocumentTemplate(
                name="agenda_reunion",
                description="Agenda estándar para reuniones",
                elements=[
                    DocumentElement(
                        type=ElementType.PARAGRAPH,
                        content="AGENDA DE REUNIÓN",
                        style=DocumentStyle.HEADING_1
                    ),
                    DocumentElement(
                        type=ElementType.PARAGRAPH,
                        content=f"Fecha: {best_slot['start_time'].strftime('%Y-%m-%d %H:%M')}",
                        style=DocumentStyle.NORMAL
                    ),
                    DocumentElement(
                        type=ElementType.PARAGRAPH,
                        content="1. Revisión de objetivos",
                        style=DocumentStyle.BULLET
                    ),
                    DocumentElement(
                        type=ElementType.PARAGRAPH,
                        content="2. Estado actual del proyecto",
                        style=DocumentStyle.BULLET
                    ),
                    DocumentElement(
                        type=ElementType.PARAGRAPH,
                        content="3. Próximos pasos",
                        style=DocumentStyle.BULLET
                    ),
                    DocumentElement(
                        type=ElementType.PARAGRAPH,
                        content="4. Acciones pendientes",
                        style=DocumentStyle.BULLET
                    )
                ]
            )
            
            agenda_result = await docs_agent.create_document(
                title=f"Agenda - Reunión {best_slot['start_time'].strftime('%Y-%m-%d')}",
                template=agenda_template
            )
            
            # Paso 4: Enviar invitaciones por email
            gmail_agent = self.agents['gmail']
            
            invitation_body = f"""
Estimados participantes,

Se ha programado una reunión de coordinación con los siguientes detalles:

📅 FECHA Y HORA: {best_slot['start_time'].strftime('%d/%m/%Y a las %H:%M')}
⏱️ DURACIÓN: {duracion_minutos} minutos
📍 MODALIDAD: Presencial/Virtual (según coordinación)
📋 AGENDA: Se compartirá documento adjunto

Se ha creado un documento de agenda que pueden revisar antes de la reunión.

Confirmen su asistencia respondiendo a este email.

Saludos,
Sistema de Coordinación de Reuniones
            """
            
            compose_request = ComposeRequest(
                to=participantes,
                subject=f"Invitación - Reunión de Coordinación - {best_slot['start_time'].strftime('%d/%m/%Y')}",
                body=invitation_body,
                priority=EmailPriority.NORMAL
            )
            
            # Adjuntar agenda si se creó exitosamente
            if agenda_result.success:
                # En implementación real, aquí se adjuntaría el documento
                pass
            
            email_result = await gmail_agent.send_email(compose_request)
            
            # Paso 5: Crear evento de seguimiento (24 horas después)
            follow_up_date = best_slot['start_time'] + timedelta(days=1, hours=9)
            
            follow_up_event = CalendarEvent(
                summary="Seguimiento - Reunión Coordinación",
                description="Seguimiento de acciones acordadas en la reunión de coordinación",
                start_time=EventTime(
                    date_time=follow_up_date,
                    timezone="UTC"
                ),
                end_time=EventTime(
                    date_time=follow_up_date + timedelta(minutes=30),
                    timezone="UTC"
                ),
                attendees=[EventAttendee(email=participantes[0])],  # Organizador principal
                reminders=[
                    EventReminder(method=ReminderType.EMAIL, minutes_before_start=60)
                ]
            )
            
            await calendar_agent.create_event(follow_up_event)
            
            self.logger.info("Workflow de coordinación de reunión completado")
            
            return {
                "success": True,
                "workflow": "coordinacion_reunion",
                "event_id": event_result.data['event_id'],
                "meeting_slot": {
                    "start_time": best_slot['start_time'].isoformat(),
                    "end_time": best_slot['end_time'].isoformat(),
                    "score": best_slot['score']
                },
                "agenda_created": agenda_result.success,
                "invitations_sent": email_result.success,
                "participants": participantes
            }
            
        except Exception as e:
            self.logger.error(f"Error en workflow: {e}")
            return {"success": False, "error": str(e)}
    
    async def workflow_automatizacion_comunicacion(self, criterios_busqueda: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flujo completo: Automatización de comunicación y seguimiento
        
        Args:
            criterios_busqueda: Criterios para buscar emails y generar respuestas
            
        Returns:
            Resultado del workflow
        """
        try:
            self.logger.info("Iniciando workflow: Automatización de Comunicación")
            
            gmail_agent = self.agents['gmail']
            calendar_agent = self.agents['calendar']
            
            # Paso 1: Buscar emails sin respuesta
            from . import EmailFilter
            
            filter_obj = EmailFilter(
                sender=criterios_busqueda.get('sender'),
                subject=criterios_busqueda.get('subject_pattern'),
                date_from=datetime.now() - timedelta(days=3),
                is_unread=True,
                max_results=20
            )
            
            emails_result = await gmail_agent.get_emails(filter_obj)
            
            if not emails_result.success:
                return {"success": False, "error": f"Error buscando emails: {emails_result.error}"}
            
            emails = emails_result.data['emails']
            processed_count = 0
            
            for email in emails:
                try:
                    # Paso 2: Analizar contenido y generar respuesta
                    email_content = email.get('body', '') or email.get('snippet', '')
                    
                    # Lógica simple de categorización
                    response_needed = False
                    response_template = None
                    
                    if 'urgent' in email_content.lower() or 'urgente' in email_content.lower():
                        response_needed = True
                        response_template = "respuesta_urgente"
                    elif 'reunión' in email_content.lower() or 'meeting' in email_content.lower():
                        response_needed = True
                        response_template = "respuesta_reunion"
                    elif 'pregunta' in email_content.lower() or 'question' in email_content.lower():
                        response_needed = True
                        response_template = "respuesta_pregunta"
                    
                    if response_needed:
                        # Paso 3: Enviar respuesta automática
                        response_body = self._generate_response(email_content, response_template)
                        
                        compose_request = ComposeRequest(
                            to=[email.get('sender', '')],
                            subject=f"Re: {email.get('subject', 'Sin asunto')}",
                            body=response_body,
                            priority=EmailPriority.NORMAL
                        )
                        
                        response_result = await gmail_agent.send_email(compose_request)
                        
                        # Paso 4: Crear evento de seguimiento si es relevante
                        if response_template == "respuesta_reunion":
                            # Programar seguimiento en 2 días
                            follow_up_date = datetime.now() + timedelta(days=2, hours=10)
                            
                            follow_up_event = CalendarEvent(
                                summary=f"Seguimiento - {email.get('subject', 'Sin asunto')}",
                                description=f"Seguimiento automático de email: {email.get('subject', '')}",
                                start_time=EventTime(
                                    date_time=follow_up_date,
                                    timezone="UTC"
                                ),
                                end_time=EventTime(
                                    date_time=follow_up_date + timedelta(minutes=30),
                                    timezone="UTC"
                                ),
                                attendees=[
                                    EventAttendee(email=email.get('sender', ''))
                                ],
                                reminders=[
                                    EventReminder(method=ReminderType.EMAIL, minutes_before_start=60)
                                ]
                            )
                            
                            await calendar_agent.create_event(follow_up_event)
                        
                        # Paso 5: Marcar email original como procesado
                        await gmail_agent.add_label(email['id'], "ProcesadoAutomatico")
                        processed_count += 1
                        
                except Exception as e:
                    self.logger.warning(f"Error procesando email {email.get('id', 'unknown')}: {e}")
                    continue
            
            # Paso 6: Generar reporte de automatización
            automation_stats = {
                "emails_found": len(emails),
                "emails_processed": processed_count,
                "response_rate": (processed_count / len(emails)) * 100 if emails else 0,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"Automatización completada: {processed_count}/{len(emails)} emails procesados")
            
            return {
                "success": True,
                "workflow": "automatizacion_comunicacion",
                "statistics": automation_stats,
                "criterios_busqueda": criterios_busqueda
            }
            
        except Exception as e:
            self.logger.error(f"Error en workflow: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_response(self, email_content: str, template_type: str) -> str:
        """Generar respuesta automática basada en el contenido"""
        responses = {
            "respuesta_urgente": f"""
Estimado/a,

Gracias por su email urgente. Hemos recibido su solicitud y la hemos marcado como prioritaria.

Nuestro equipo revisará su consulta y le responderá dentro de las próximas 2 horas.

Si tiene alguna pregunta adicional, no dude en contactarnos.

Saludos cordiales,
Equipo de Atención al Cliente
            """,
            "respuesta_reunion": f"""
Estimado/a,

Gracias por su interés en programar una reunión.

Para coordinar una reunión que se ajuste a su disponibilidad, por favor indíquenos:
1. Sus fechas preferidas
2. Duración estimada de la reunión
3. Modalidad (presencial/virtual)

Nuestro sistema automáticamente encontrará slots disponibles y le enviará propuestas.

Saludos,
Sistema de Coordinación
            """,
            "respuesta_pregunta": f"""
Estimado/a,

Gracias por su consulta.

Hemos recibido su pregunta y nuestro equipo especializado la está revisando. Le responderemos con la información más detallada posible.

Tiempo estimado de respuesta: 24 horas.

Saludos,
Equipo de Soporte
            """
        }
        
        return responses.get(template_type, "Gracias por su email. Le responderemos pronto.")
    
    async def workflow_analisis_productividad(self) -> Dict[str, Any]:
        """
        Análisis completo de productividad basado en datos de Google Workspace
        
        Returns:
            Resultado del análisis
        """
        try:
            self.logger.info("Iniciando workflow: Análisis de Productividad")
            
            # Paso 1: Análisis de calendario
            calendar_agent = self.agents['calendar']
            
            month_start = datetime.now().replace(day=1)
            month_end = month_start + timedelta(days=31)
            
            schedule_analysis = await calendar_agent.analyze_schedule(month_start, month_end)
            
            # Paso 2: Análisis de emails
            gmail_agent = self.agents['gmail']
            
            email_stats = await gmail_agent.get_email_statistics()
            
            # Paso 3: Crear reporte en Google Sheets
            sheets_agent = self.agents['sheets']
            
            report_result = await sheets_agent.create_spreadsheet(
                title=f"Análisis Productividad - {datetime.now().strftime('%Y-%m')}",
                sheets=["Calendario", "Emails", "Resumen"]
            )
            
            if report_result.success:
                spreadsheet_id = report_result.data['spreadsheet_id']
                
                # Datos de calendario
                calendar_data = [
                    ["Métrica", "Valor", "Descripción"],
                    ["Total eventos", schedule_analysis.data.get('total_events', 0)],
                    ["Tiempo ocupado %", f"{schedule_analysis.data.get('busy_time_percentage', 0):.1f}%"],
                    ["Día más ocupado", schedule_analysis.data.get('most_busy_day', 'N/A')],
                    ["Horas productivas", str(schedule_analysis.data.get('most_productive_hours', []))]
                ]
                
                await sheets_agent.write_data(
                    spreadsheet_id=spreadsheet_id,
                    range_name="Calendario!A1:C5",
                    values=calendar_data
                )
                
                # Datos de emails
                email_data = [
                    ["Métrica", "Valor", "Descripción"],
                    ["Total emails", email_stats.data.get('total_emails', 0)],
                    ["Emails sin leer", email_stats.data.get('unread_emails', 0)],
                    ["Emails enviados", email_stats.data.get('sent_emails', 0)],
                    ["Con adjuntos", email_stats.data.get('emails_with_attachments', 0)],
                    ["Remitente frecuente", email_stats.data.get('most_frequent_sender', 'N/A')]
                ]
                
                await sheets_agent.write_data(
                    spreadsheet_id=spreadsheet_id,
                    range_name="Emails!A1:C7",
                    values=email_data
                )
                
                # Resumen ejecutivo
                summary_data = [
                    ["RESUMEN EJECUTIVO DE PRODUCTIVIDAD"],
                    [""],
                    [f"Período analizado: {month_start.strftime('%Y-%m')}"],
                    [""],
                    ["CALENDARIO"],
                    [f"• Se registraron {schedule_analysis.data.get('total_events', 0)} eventos"],
                    [f"• {schedule_analysis.data.get('busy_time_percentage', 0):.1f}% del tiempo está ocupado"],
                    [f"• Día más activo: {schedule_analysis.data.get('most_busy_day', 'N/A')}"],
                    [""],
                    ["COMUNICACIÓN"],
                    [f"• {email_stats.data.get('total_emails', 0)} emails procesados"],
                    [f"• {email_stats.data.get('unread_emails', 0)} emails pendientes"],
                    [f"• {email_stats.data.get('emails_with_attachments', 0)} emails con documentos"],
                ]
                
                await sheets_agent.write_data(
                    spreadsheet_id=spreadsheet_id,
                    range_name="Resumen!A1:A15",
                    values=[[item] for item in summary_data]
                )
            
            self.logger.info("Análisis de productividad completado")
            
            return {
                "success": True,
                "workflow": "analisis_productividad",
                "schedule_analysis": schedule_analysis.data,
                "email_statistics": email_stats.data,
                "report_created": report_result.success,
                "spreadsheet_id": report_result.data.get('spreadsheet_id') if report_result.success else None
            }
            
        except Exception as e:
            self.logger.error(f"Error en workflow: {e}")
            return {"success": False, "error": str(e)}


async def demo_workflows():
    """Función de demostración de todos los workflows"""
    print("🚀 Demo: Google Workspace Enterprise Integration")
    print("=" * 50)
    
    # Crear configuración de ejemplo
    config_manager = GoogleWorkspaceConfigManager()
    
    # Crear archivo de configuración de ejemplo
    initializer = GoogleWorkspaceEnterpriseInitializer(config_manager)
    initializer.create_sample_config("demo_config.json")
    
    print("✅ Archivo de configuración de ejemplo creado: demo_config.json")
    print("📝 Por favor, edite el archivo con sus credenciales reales antes de ejecutar")
    
    # Crear datos de ejemplo
    sample_sales_data = [
        {"producto": "Producto A", "ventas_enero": 150, "ventas_febrero": 180, "ventas_marzo": 200, "meta": 500},
        {"producto": "Producto B", "ventas_enero": 100, "ventas_febrero": 120, "ventas_marzo": 90, "meta": 400},
        {"producto": "Producto C", "ventas_enero": 200, "ventas_febrero": 250, "ventas_marzo": 300, "meta": 700},
        {"producto": "Producto D", "ventas_enero": 80, "ventas_febrero": 95, "ventas_marzo": 110, "meta": 300}
    ]
    
    print("\n📊 Datos de ejemplo preparados:")
    print(f"   • {len(sample_sales_data)} productos")
    print(f"   • Período: Enero-Marzo 2024")
    
    # Crear workflow manager
    workflow_manager = GoogleWorkspaceWorkflowManager("demo_config.json")
    
    print("\n🔧 Workflow Manager inicializado")
    print("   Agentes disponibles:")
    for agent_name in workflow_manager.agents.keys():
        print(f"   • {agent_name.upper()}")
    
    print("\n" + "=" * 50)
    print("Para ejecutar los workflows completos:")
    print("1. Configure las credenciales en demo_config.json")
    print("2. Ejecute: await workflow_manager.workflow_crear_reporte_ejecutivo(sample_sales_data)")
    print("3. Ejecute: await workflow_manager.workflow_coordinacion_reunion_completa(['user@empresa.com'])")
    print("4. Ejecute: await workflow_manager.workflow_analisis_productividad()")
    print("=" * 50)


if __name__ == "__main__":
    # Configurar logging básico
    logging.basicConfig(level=logging.INFO)
    
    # Ejecutar demo
    asyncio.run(demo_workflows())