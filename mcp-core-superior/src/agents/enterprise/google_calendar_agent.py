"""
Google Calendar Agent - Agente Especializado para Google Calendar
Proporciona capacidades avanzadas de gestión de eventos, programación y coordinación
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import pytz
from zoneinfo import ZoneInfo

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


class EventStatus(Enum):
    """Estados de evento"""
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"


class EventVisibility(Enum):
    """Visibilidad de evento"""
    DEFAULT = "default"
    PUBLIC = "public"
    PRIVATE = "private"
    CONFIDENTIAL = "confidential"


class EventPriority(Enum):
    """Prioridad de evento"""
    LOW = 1
    NORMAL = 3
    HIGH = 5
    URGENT = 7


class ReminderType(Enum):
    """Tipos de recordatorio"""
    EMAIL = "email"
    POPUP = "popup"
    SMS = "sms"


class AttendeeStatus(Enum):
    """Estados de asistentes"""
    NEEDS_ACTION = "needsAction"
    DECLINED = "declined"
    TENTATIVE = "tentative"
    ACCEPTED = "accepted"


@dataclass
class EventTime:
    """Tiempo de evento"""
    date_time: Optional[datetime] = None
    date: Optional[str] = None  # Para eventos de día completo
    timezone: str = "UTC"


@dataclass
class EventAttendee:
    """Asistente a evento"""
    email: str
    display_name: Optional[str] = None
    organizer: bool = False
    status: AttendeeStatus = AttendeeStatus.NEEDS_ACTION
    optional: bool = False


@dataclass
class EventReminder:
    """Recordatorio de evento"""
    method: ReminderType
    minutes_before_start: int


@dataclass
class CalendarEvent:
    """Evento de calendario"""
    id: Optional[str] = None
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[EventTime] = None
    end_time: Optional[EventTime] = None
    attendees: List[EventAttendee] = field(default_factory=list)
    reminders: List[EventReminder] = field(default_factory=list)
    status: EventStatus = EventStatus.CONFIRMED
    visibility: EventVisibility = EventVisibility.DEFAULT
    priority: EventPriority = EventPriority.NORMAL
    color_id: Optional[str] = None
    recurrence: List[str] = field(default_factory=list)
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    creator: Optional[str] = None
    organizer: Optional[str] = None


@dataclass
class Calendar:
    """Calendario"""
    id: str
    summary: str
    description: Optional[str] = None
    primary: bool = False
    timezone: str = "UTC"
    color_id: Optional[str] = None
    access_role: Optional[str] = None
    can_edit: bool = False
    can_share: bool = False


@dataclass
class MeetingSlot:
    """Slot de reunión disponible"""
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    attendees: List[str]
    score: float  # Puntuación de conveniencia


@dataclass
class EventTemplate:
    """Plantilla de evento"""
    name: str
    summary_template: str
    description_template: str
    default_duration: int
    default_attendees: List[str] = field(default_factory=list)
    default_reminders: List[EventReminder] = field(default_factory=list)
    default_location: Optional[str] = None


@dataclass
class ScheduleAnalysis:
    """Análisis de programación"""
    total_events: int
    busy_time_percentage: float
    most_busy_day: str
    most_productive_hours: List[int]
    upcoming_events: List[Dict[str, Any]]
    time_conflicts: List[Dict[str, Any]]


class GoogleCalendarAgent(BaseGoogleWorkspaceAgent):
    """
    Agente Especializado para Google Calendar
    
    Funcionalidades:
    - Crear y gestionar eventos
    - Búsqueda inteligente de disponibilidad
    - Programación automática de reuniones
    - Recordatorios y notificaciones
    - Gestión de múltiples calendarios
    - Análisis de patrones de programación
    - Integración con otros servicios
    - Colaboración en tiempo real
    """
    
    def __init__(self, config: GoogleWorkspaceConfig):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.calendar_service = None
        self.event_templates: Dict[str, EventTemplate] = {}
        self.user_timezone = "UTC"
        
        # Configurar capacidades específicas
        self.add_capability(AgentCapability.SCHEDULING)
        self.add_capability(AgentCapability.AUTOMATION)
        self.add_capability(AgentCapability.COMMUNICATION)
    
    async def initialize(self):
        """Inicializar servicio de Calendar"""
        await super().authenticate()
        self.calendar_service = await self.get_service(GoogleWorkspaceService.CALENDAR)
        
        # Obtener configuración del usuario
        await self._setup_user_preferences()
    
    async def _setup_user_preferences(self):
        """Configurar preferencias del usuario"""
        try:
            # Obtener configuración del usuario
            calendar_list = self.calendar_service.calendarList().list().execute()
            
            # Establecer zona horaria del usuario
            primary_calendar = next((c for c in calendar_list.get('items', []) if c.get('primary')), None)
            if primary_calendar:
                self.user_timezone = primary_calendar.get('timeZone', 'UTC')
            
        except Exception as e:
            self.logger.warning(f"Error configurando preferencias: {e}")
    
    @handle_exceptions
    async def create_event(
        self,
        calendar_event: CalendarEvent,
        calendar_id: str = 'primary'
    ) -> ApiResponse:
        """
        Crear evento en calendario
        
        Args:
            calendar_event: Datos del evento
            calendar_id: ID del calendario
            
        Returns:
            ApiResponse: Resultado de la creación
        """
        try:
            # Preparar datos del evento
            event_data = self._event_to_api_format(calendar_event)
            
            # Crear evento
            result = self.calendar_service.events().insert(
                calendarId=calendar_id,
                body=event_data,
                sendNotifications=True
            ).execute()
            
            created_event = self._event_from_api_format(result)
            
            self.logger.info(f"Evento creado: {created_event.summary}")
            
            return ApiResponse(
                success=True,
                data={
                    'event': created_event.__dict__,
                    'event_id': result['id'],
                    'html_link': result.get('htmlLink', ''),
                    'calendar_id': calendar_id
                }
            )
            
        except Exception as e:
            error_msg = f"Error creando evento: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def get_event(
        self,
        event_id: str,
        calendar_id: str = 'primary'
    ) -> ApiResponse:
        """
        Obtener evento específico
        
        Args:
            event_id: ID del evento
            calendar_id: ID del calendario
            
        Returns:
            ApiResponse: Datos del evento
        """
        try:
            result = self.calendar_service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            calendar_event = self._event_from_api_format(result)
            
            return ApiResponse(
                success=True,
                data=calendar_event.__dict__
            )
            
        except Exception as e:
            error_msg = f"Error obteniendo evento: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def update_event(
        self,
        event_id: str,
        calendar_event: CalendarEvent,
        calendar_id: str = 'primary'
    ) -> ApiResponse:
        """
        Actualizar evento existente
        
        Args:
            event_id: ID del evento
            calendar_event: Nuevos datos del evento
            calendar_id: ID del calendario
            
        Returns:
            ApiResponse: Resultado de la actualización
        """
        try:
            event_data = self._event_to_api_format(calendar_event)
            
            result = self.calendar_service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event_data,
                sendNotifications=True
            ).execute()
            
            updated_event = self._event_from_api_format(result)
            
            self.logger.info(f"Evento actualizado: {updated_event.summary}")
            
            return ApiResponse(
                success=True,
                data={
                    'event': updated_event.__dict__,
                    'updated': True
                }
            )
            
        except Exception as e:
            error_msg = f"Error actualizando evento: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def delete_event(
        self,
        event_id: str,
        calendar_id: str = 'primary'
    ) -> ApiResponse:
        """
        Eliminar evento
        
        Args:
            event_id: ID del evento
            calendar_id: ID del calendario
            
        Returns:
            ApiResponse: Resultado de la eliminación
        """
        try:
            self.calendar_service.events().delete(
                calendarId=calendar_id,
                eventId=event_id,
                sendNotifications=True
            ).execute()
            
            return ApiResponse(
                success=True,
                data={
                    'event_id': event_id,
                    'deleted': True
                }
            )
            
        except Exception as e:
            error_msg = f"Error eliminando evento: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def list_events(
        self,
        start_time: datetime,
        end_time: datetime,
        calendar_id: str = 'primary',
        max_results: int = 100
    ) -> ApiResponse:
        """
        Listar eventos en rango de tiempo
        
        Args:
            start_time: Tiempo de inicio
            end_time: Tiempo de fin
            calendar_id: ID del calendario
            max_results: Máximo número de resultados
            
        Returns:
            ApiResponse: Lista de eventos
        """
        try:
            result = self.calendar_service.events().list(
                calendarId=calendar_id,
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = []
            for event_data in result.get('items', []):
                calendar_event = self._event_from_api_format(event_data)
                events.append(calendar_event.__dict__)
            
            return ApiResponse(
                success=True,
                data={
                    'events': events,
                    'total_count': len(events),
                    'time_range': {
                        'start': start_time.isoformat(),
                        'end': end_time.isoformat()
                    }
                }
            )
            
        except Exception as e:
            error_msg = f"Error listando eventos: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def find_available_slots(
        self,
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int,
        attendees: List[str],
        work_hours: Tuple[int, int] = (9, 17),  # 9 AM - 5 PM
        excluded_weekends: bool = True
    ) -> ApiResponse:
        """
        Encontrar slots de tiempo disponibles
        
        Args:
            start_date: Fecha de inicio de búsqueda
            end_date: Fecha de fin de búsqueda
            duration_minutes: Duración requerida en minutos
            attendees: Lista de asistentes
            work_hours: Horario de trabajo (inicio, fin)
            excluded_weekends: Excluir fines de semana
            
        Returns:
            ApiResponse: Slots de tiempo disponibles
        """
        try:
            available_slots = []
            current_date = start_date.date()
            end_date = end_date.date()
            
            while current_date <= end_date:
                # Saltar fines de semana si está configurado
                if excluded_weekends and current_date.weekday() >= 5:
                    current_date += timedelta(days=1)
                    continue
                
                # Verificar disponibilidad de asistentes
                day_slots = await self._find_day_available_slots(
                    current_date, duration_minutes, attendees, work_hours
                )
                
                available_slots.extend(day_slots)
                current_date += timedelta(days=1)
            
            # Ordenar slots por puntuación
            available_slots.sort(key=lambda x: x.score, reverse=True)
            
            return ApiResponse(
                success=True,
                data={
                    'available_slots': [slot.__dict__ for slot in available_slots],
                    'total_slots': len(available_slots),
                    'search_criteria': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'duration_minutes': duration_minutes,
                        'attendees': attendees
                    }
                }
            )
            
        except Exception as e:
            error_msg = f"Error buscando slots disponibles: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def schedule_meeting(
        self,
        title: str,
        attendees: List[str],
        duration_minutes: int,
        preferred_times: Optional[List[Tuple[datetime, datetime]]] = None,
        location: Optional[str] = None,
        description: Optional[str] = None
    ) -> ApiResponse:
        """
        Programar reunión automáticamente
        
        Args:
            title: Título de la reunión
            attendees: Lista de asistentes
            duration_minutes: Duración de la reunión
            preferred_times: Horarios preferidos
            location: Ubicación
            description: Descripción
            
        Returns:
            ApiResponse: Evento programado
        """
        try:
            # Buscar slots disponibles
            search_start = datetime.now()
            search_end = search_start + timedelta(days=30)  # Buscar en próximo mes
            
            slots_result = await self.find_available_slots(
                search_start,
                search_end,
                duration_minutes,
                attendees
            )
            
            if not slots_result.success:
                return slots_result
            
            available_slots = slots_result.data['available_slots']
            
            if not available_slots:
                return ApiResponse(
                    success=False,
                    error="No hay slots disponibles en el rango especificado"
                )
            
            # Seleccionar mejor slot
            best_slot = available_slots[0]
            
            # Crear evento
            calendar_event = CalendarEvent(
                summary=title,
                description=description or f"Reunión programada automáticamente",
                location=location,
                start_time=EventTime(
                    date_time=best_slot['start_time'],
                    timezone=self.user_timezone
                ),
                end_time=EventTime(
                    date_time=best_slot['end_time'],
                    timezone=self.user_timezone
                ),
                attendees=[
                    EventAttendee(email=attendee) for attendee in attendees
                ],
                reminders=[
                    EventReminder(method=ReminderType.EMAIL, minutes_before_start=60),
                    EventReminder(method=ReminderType.POPUP, minutes_before_start=15)
                ]
            )
            
            # Crear evento en calendario
            create_result = await self.create_event(calendar_event)
            
            if create_result.success:
                return ApiResponse(
                    success=True,
                    data={
                        'meeting_scheduled': True,
                        'event': create_result.data['event'],
                        'selected_slot': best_slot,
                        'attendees_conflicted': []
                    }
                )
            else:
                return create_result
            
        except Exception as e:
            error_msg = f"Error programando reunión: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def create_recurring_event(
        self,
        calendar_event: CalendarEvent,
        recurrence_rule: str  # Ej: "RRULE:FREQ=WEEKLY;COUNT=10"
    ) -> ApiResponse:
        """
        Crear evento recurrente
        
        Args:
            calendar_event: Datos del evento
            recurrence_rule: Regla de recurrencia
            
        Returns:
            ApiResponse: Resultado de la creación
        """
        try:
            # Agregar regla de recurrencia
            calendar_event.recurrence = [recurrence_rule]
            
            return await self.create_event(calendar_event)
            
        except Exception as e:
            error_msg = f"Error creando evento recurrente: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def get_calendar_list(self) -> ApiResponse:
        """
        Obtener lista de calendarios del usuario
        
        Returns:
            ApiResponse: Lista de calendarios
        """
        try:
            result = self.calendar_service.calendarList().list().execute()
            
            calendars = []
            for calendar_data in result.get('items', []):
                calendar = Calendar(
                    id=calendar_data['id'],
                    summary=calendar_data['summary'],
                    description=calendar_data.get('description', ''),
                    primary=calendar_data.get('primary', False),
                    timezone=calendar_data.get('timeZone', 'UTC'),
                    color_id=calendar_data.get('colorId', ''),
                    access_role=calendar_data.get('accessRole', ''),
                    can_edit=calendar_data.get('accessRole') in ['writer', 'owner'],
                    can_share=calendar_data.get('accessRole') == 'owner'
                )
                calendars.append(calendar.__dict__)
            
            return ApiResponse(
                success=True,
                data={
                    'calendars': calendars,
                    'primary_calendar': next((c for c in calendars if c['primary']), None)
                }
            )
            
        except Exception as e:
            error_msg = f"Error obteniendo calendarios: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def analyze_schedule(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> ApiResponse:
        """
        Analizar patrones de programación
        
        Args:
            start_date: Fecha de inicio del análisis
            end_date: Fecha de fin del análisis
            
        Returns:
            ApiResponse: Análisis de programación
        """
        try:
            # Obtener eventos en el período
            events_result = await self.list_events(start_date, end_date)
            if not events_result.success:
                return events_result
            
            events = events_result.data['events']
            
            # Analizar datos
            analysis = self._analyze_schedule_patterns(events, start_date, end_date)
            
            return ApiResponse(success=True, data=analysis.__dict__)
            
        except Exception as e:
            error_msg = f"Error analizando programación: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def send_calendar_invitation(
        self,
        event_id: str,
        additional_attendees: List[str],
        calendar_id: str = 'primary'
    ) -> ApiResponse:
        """
        Enviar invitación adicional a evento
        
        Args:
            event_id: ID del evento
            additional_attendees: Nuevos asistentes
            calendar_id: ID del calendario
            
        Returns:
            ApiResponse: Resultado de la operación
        """
        try:
            # Obtener evento actual
            event_result = await self.get_event(event_id, calendar_id)
            if not event_result.success:
                return event_result
            
            event_data = event_result.data
            event_data['attendees'].extend([
                {'email': attendee} for attendee in additional_attendees
            ])
            
            # Actualizar evento
            calendar_event = CalendarEvent(**event_data)
            return await self.update_event(event_id, calendar_event, calendar_id)
            
        except Exception as e:
            error_msg = f"Error enviando invitación: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    def _event_to_api_format(self, calendar_event: CalendarEvent) -> Dict[str, Any]:
        """Convertir CalendarEvent a formato de API"""
        event_data = {
            'summary': calendar_event.summary,
            'status': calendar_event.status.value,
            'visibility': calendar_event.visibility.value,
            'priority': calendar_event.priority.value
        }
        
        if calendar_event.description:
            event_data['description'] = calendar_event.description
        
        if calendar_event.location:
            event_data['location'] = calendar_event.location
        
        # Configurar tiempos
        if calendar_event.start_time and calendar_event.end_time:
            event_data['start'] = {}
            event_data['end'] = {}
            
            if calendar_event.start_time.date_time:
                event_data['start']['dateTime'] = calendar_event.start_time.date_time.isoformat()
                event_data['start']['timeZone'] = calendar_event.start_time.timezone
            
            if calendar_event.end_time.date_time:
                event_data['end']['dateTime'] = calendar_event.end_time.date_time.isoformat()
                event_data['end']['timeZone'] = calendar_event.end_time.timezone
        
        # Configurar asistentes
        if calendar_event.attendees:
            event_data['attendees'] = [
                {
                    'email': attendee.email,
                    'displayName': attendee.display_name,
                    'organizer': attendee.organizer,
                    'optional': attendee.optional
                }
                for attendee in calendar_event.attendees
            ]
        
        # Configurar recordatorios
        if calendar_event.reminders:
            event_data['reminders'] = {
                'useDefault': False,
                'overrides': [
                    {
                        'method': reminder.method.value,
                        'minutes': reminder.minutes_before_start
                    }
                    for reminder in calendar_event.reminders
                ]
            }
        
        return event_data
    
    def _event_from_api_format(self, event_data: Dict[str, Any]) -> CalendarEvent:
        """Convertir datos de API a CalendarEvent"""
        start_time = None
        end_time = None
        
        if 'start' in event_data:
            if 'dateTime' in event_data['start']:
                start_time = EventTime(
                    date_time=datetime.fromisoformat(event_data['start']['dateTime'].replace('Z', '+00:00')),
                    timezone=event_data['start'].get('timeZone', 'UTC')
                )
            elif 'date' in event_data['start']:
                start_time = EventTime(date=event_data['start']['date'])
        
        if 'end' in event_data:
            if 'dateTime' in event_data['end']:
                end_time = EventTime(
                    date_time=datetime.fromisoformat(event_data['end']['dateTime'].replace('Z', '+00:00')),
                    timezone=event_data['end'].get('timeZone', 'UTC')
                )
            elif 'date' in event_data['end']:
                end_time = EventTime(date=event_data['end']['date'])
        
        # Convertir asistentes
        attendees = []
        for attendee_data in event_data.get('attendees', []):
            attendees.append(EventAttendee(
                email=attendee_data['email'],
                display_name=attendee_data.get('displayName', ''),
                organizer=attendee_data.get('organizer', False),
                optional=attendee_data.get('optional', False)
            ))
        
        # Convertir recordatorios
        reminders = []
        for reminder_data in event_data.get('reminders', {}).get('overrides', []):
            reminders.append(EventReminder(
                method=ReminderType(reminder_data['method']),
                minutes_before_start=reminder_data['minutes']
            ))
        
        return CalendarEvent(
            id=event_data.get('id'),
            summary=event_data.get('summary', ''),
            description=event_data.get('description', ''),
            location=event_data.get('location', ''),
            start_time=start_time,
            end_time=end_time,
            attendees=attendees,
            reminders=reminders,
            status=EventStatus(event_data.get('status', 'confirmed')),
            visibility=EventVisibility(event_data.get('visibility', 'default')),
            priority=EventPriority(event_data.get('priority', 3)),
            color_id=event_data.get('colorId'),
            recurrence=event_data.get('recurrence', []),
            created=datetime.fromisoformat(event_data.get('created', '').replace('Z', '+00:00')) if event_data.get('created') else None,
            updated=datetime.fromisoformat(event_data.get('updated', '').replace('Z', '+00:00')) if event_data.get('updated') else None,
            creator=event_data.get('creator', {}).get('email', ''),
            organizer=event_data.get('organizer', {}).get('email', '')
        )
    
    async def _find_day_available_slots(
        self,
        date: datetime.date,
        duration_minutes: int,
        attendees: List[str],
        work_hours: Tuple[int, int]
    ) -> List[MeetingSlot]:
        """Encontrar slots disponibles en un día específico"""
        try:
            # Obtener eventos existentes del día
            day_start = datetime.combine(date, datetime.min.time())
            day_end = datetime.combine(date, datetime.max.time())
            
            events_result = await self.list_events(day_start, day_end)
            if not events_result.success:
                return []
            
            busy_periods = []
            for event in events_result.data['events']:
                if event.get('start_time', {}).get('date_time') and event.get('end_time', {}).get('date_time'):
                    busy_periods.append({
                        'start': datetime.fromisoformat(event['start_time']['date_time'].replace('Z', '+00:00')),
                        'end': datetime.fromisoformat(event['end_time']['date_time'].replace('Z', '+00:00'))
                    })
            
            # Generar slots de tiempo de trabajo
            work_start, work_end = work_hours
            current_time = day_start.replace(hour=work_start, minute=0, second=0, microsecond=0)
            end_time = day_start.replace(hour=work_end, minute=0, second=0, microsecond=0)
            
            available_slots = []
            
            while current_time + timedelta(minutes=duration_minutes) <= end_time:
                slot_end = current_time + timedelta(minutes=duration_minutes)
                
                # Verificar si el slot está libre
                is_available = True
                for busy_period in busy_periods:
                    if (current_time < busy_period['end'] and 
                        slot_end > busy_period['start']):
                        is_available = False
                        break
                
                if is_available:
                    # Calcular puntuación del slot
                    score = self._calculate_slot_score(current_time, slot_end, attendees)
                    
                    available_slots.append(MeetingSlot(
                        start_time=current_time,
                        end_time=slot_end,
                        duration_minutes=duration_minutes,
                        attendees=attendees,
                        score=score
                    ))
                
                current_time += timedelta(minutes=30)  # Slot de 30 minutos
            
            return available_slots
            
        except Exception as e:
            self.logger.warning(f"Error buscando slots para {date}: {e}")
            return []
    
    def _calculate_slot_score(
        self,
        start_time: datetime,
        end_time: datetime,
        attendees: List[str]
    ) -> float:
        """Calcular puntuación de conveniencia de un slot"""
        score = 100.0
        
        # Penalizar horarios fuera de horario laboral
        hour = start_time.hour
        if hour < 9 or hour > 17:
            score -= 30
        
        # Preferir horarios de media mañana y media tarde
        if 10 <= hour <= 11 or 14 <= hour <= 16:
            score += 20
        
        # Penalizar muy temprano o muy tarde
        if hour < 8 or hour > 18:
            score -= 40
        
        # Preferir slots de una duración estándar
        duration = (end_time - start_time).total_seconds() / 60
        if 30 <= duration <= 60:
            score += 10
        
        return max(0, score)
    
    def _analyze_schedule_patterns(
        self,
        events: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime
    ) -> ScheduleAnalysis:
        """Analizar patrones de programación"""
        total_duration = (end_date - start_date).total_seconds() / 3600  # horas
        
        busy_time = 0
        events_by_day = {}
        events_by_hour = {}
        upcoming_events = []
        
        for event in events:
            # Calcular duración del evento
            if (event.get('start_time', {}).get('date_time') and 
                event.get('end_time', {}).get('date_time')):
                start = datetime.fromisoformat(event['start_time']['date_time'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(event['end_time']['date_time'].replace('Z', '+00:00'))
                duration = (end - start).total_seconds() / 3600
                busy_time += duration
                
                # Analizar por día
                day_key = start.strftime('%A')
                events_by_day[day_key] = events_by_day.get(day_key, 0) + 1
                
                # Analizar por hora
                hour_key = start.hour
                events_by_hour[hour_key] = events_by_hour.get(hour_key, 0) + 1
                
                # Eventos próximos
                if start > datetime.now():
                    upcoming_events.append({
                        'title': event.get('summary', ''),
                        'start_time': start.isoformat(),
                        'duration_hours': duration
                    })
        
        # Encontrar día más ocupado
        most_busy_day = max(events_by_day, key=events_by_day.get) if events_by_day else "N/A"
        
        # Encontrar horas más productivas
        most_productive_hours = sorted(
            events_by_hour.keys(),
            key=lambda h: events_by_hour[h],
            reverse=True
        )[:3]
        
        busy_percentage = (busy_time / total_duration) * 100 if total_duration > 0 else 0
        
        return ScheduleAnalysis(
            total_events=len(events),
            busy_time_percentage=busy_percentage,
            most_busy_day=most_busy_day,
            most_productive_hours=most_productive_hours,
            upcoming_events=upcoming_events[:10],  # Top 10 eventos próximos
            time_conflicts=[]  # Se calcularía con análisis adicional
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar salud del agente Google Calendar"""
        try:
            # Verificar servicio base
            base_health = await super().health_check()
            
            if not base_health["healthy"]:
                return base_health
            
            # Test específico de Calendar API
            test_events = await self.list_events(
                datetime.now(),
                datetime.now() + timedelta(days=1),
                max_results=10
            )
            
            if test_events.success:
                return {
                    "healthy": True,
                    "service": "Google Calendar Agent",
                    "test_api_access": "passed",
                    "events_count": test_events.data['total_count'],
                    "timezone": self.user_timezone,
                    "details": base_health
                }
            else:
                return {
                    "healthy": False,
                    "error": "Error accediendo a Calendar API",
                    "details": base_health
                }
                
        except Exception as e:
            return {
                "healthy": False,
                "error": f"Error en health check: {str(e)}",
                "service": "Google Calendar Agent"
            }