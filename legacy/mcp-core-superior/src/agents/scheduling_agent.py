"""
Scheduling Agent MCP - Agente de Programación y Calendarios
Integra con servicios de calendarios para gestión de citas, coordinación
de reuniones, recordatorios y optimización de horarios.

Autor: Scheduling Agent
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
import calendar
import pytz
from collections import defaultdict

# Importar la estructura base del agente MCP
try:
    from .base_agent_wrapper import BaseAgentWrapper, AgentCapability
except ImportError:
    BaseAgentWrapper = object
    AgentCapability = None


class CalendarProvider(Enum):
    """Proveedores de calendario soportados"""
    GOOGLE = "google"
    OUTLOOK = "outlook"
    APPLE = "apple"
    CALDAV = "caldav"
    ICS = "ics"


class EventType(Enum):
    """Tipos de eventos"""
    MEETING = "meeting"
    APPOINTMENT = "appointment"
    TASK = "task"
    REMINDER = "reminder"
    BLOCKED_TIME = "blocked_time"
    AVAILABILITY = "availability"


class EventStatus(Enum):
    """Estados de eventos"""
    CONFIRMED = "confirmed"
    PENDING = "pending"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class RecurrencePattern(Enum):
    """Patrones de recurrencia"""
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"


@dataclass
class Event:
    """Estructura de datos para eventos"""
    id: str
    title: str
    description: str = ""
    start_time: datetime
    end_time: datetime
    event_type: EventType = EventType.MEETING
    status: EventStatus = EventStatus.CONFIRMED
    location: Optional[str] = None
    attendees: List[Dict[str, str]] = field(default_factory=list)
    recurrence: RecurrencePattern = RecurrencePattern.NONE
    recurrence_end: Optional[datetime] = None
    reminder_minutes: List[int] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TimeSlot:
    """Estructura de datos para franjas horarias disponibles"""
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    available: bool = True
    score: float = 0.0  # Score para optimización
    meeting_type: Optional[str] = None
    preferred: bool = False


@dataclass
class MeetingRequest:
    """Estructura de datos para solicitudes de reunión"""
    title: str
    duration_minutes: int
    attendees: List[str]
    preferred_times: List[datetime] = field(default_factory=list)
    time_range: Optional[Tuple[datetime, datetime]] = None
    location: Optional[str] = None
    description: str = ""
    priority: str = "medium"  # low, medium, high, urgent
    meeting_type: str = "meeting"


@dataclass
class SchedulingResponse:
    """Respuesta consolidada de programación"""
    success: bool
    event_id: str
    action: str
    timestamp: float
    execution_time: float
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class SchedulingAgent(BaseAgentWrapper if BaseAgentWrapper else object):
    """
    Agente de Programación que maneja calendarios, eventos,
    coordinación de reuniones y optimización de horarios.
    """
    
    def __init__(self):
        if BaseAgentWrapper:
            super().__init__(
                agent_name="SchedulingAgent",
                capabilities=[
                    AgentCapability.CALENDAR_MANAGEMENT if AgentCapability else "calendar_management",
                    AgentCapability.SCHEDULE_OPTIMIZATION if AgentCapability else "schedule_optimization",
                    AgentCapability.REMINDER_MANAGEMENT if AgentCapability else "reminder_management",
                    AgentCapability.MEETING_COORDINATION if AgentCapability else "meeting_coordination",
                    AgentCapability.TIME_SLOT_FINDING if AgentCapability else "time_slot_finding",
                ],
                max_concurrent=6,
                timeout_seconds=30,
                retry_attempts=2
            )
        
        self.logger = logging.getLogger(__name__)
        self._events: Dict[str, Event] = {}
        self._calendars: Dict[str, Dict[str, Any]] = {}
        self._time_slots: Dict[str, List[TimeSlot]] = {}
        self._reminders: List[Dict[str, Any]] = []
        
        # Configuración de zonas horarias
        self.timezone = pytz.timezone('Europe/Madrid')
        
        # Configuración de APIs simulada
        self.calendar_apis = {
            CalendarProvider.GOOGLE: {"api_key": "***", "client_id": "***"},
            CalendarProvider.OUTLOOK: {"client_id": "***", "client_secret": "***"},
        }
        
        # Horarios de trabajo simulados
        self.business_hours = {
            "monday": {"start": "09:00", "end": "18:00"},
            "tuesday": {"start": "09:00", "end": "18:00"},
            "wednesday": {"start": "09:00", "end": "18:00"},
            "thursday": {"start": "09:00", "end": "18:00"},
            "friday": {"start": "09:00", "end": "18:00"},
            "saturday": {"start": "10:00", "end": "14:00"},
            "sunday": {"start": "00:00", "end": "00:00"}  # Cerrado
        }
        
        # Cargar datos de ejemplo
        self._load_sample_data()
    
    async def _initialize(self):
        """Inicialización específica del agente"""
        await asyncio.sleep(0.1)
        self.logger.info("Scheduling Agent inicializado")
    
    def _load_sample_data(self):
        """Cargar datos de ejemplo"""
        # Eventos de ejemplo
        now = datetime.now(self.timezone)
        
        sample_events = [
            Event(
                id="event_1",
                title="Reunión de Equipo",
                description="Reunión semanal de seguimiento del equipo",
                start_time=now + timedelta(days=1, hours=9),
                end_time=now + timedelta(days=1, hours=10, minutes=30),
                location="Sala de Reuniones A",
                attendees=[
                    {"name": "Juan Pérez", "email": "juan@company.com"},
                    {"name": "María García", "email": "maria@company.com"}
                ],
                reminder_minutes=[30, 10]
            ),
            Event(
                id="event_2",
                title="Llamada con Cliente",
                description="Seguimiento de proyecto con cliente ABC",
                start_time=now + timedelta(days=2, hours=14),
                end_time=now + timedelta(days=2, hours=15),
                attendees=[
                    {"name": "Carlos López", "email": "carlos@abc.com"},
                    {"name": "Ana Ruiz", "email": "ana@company.com"}
                ],
                reminder_minutes=[15]
            ),
            Event(
                id="event_3",
                title="Presentación Producto",
                description="Presentación del nuevo producto a stakeholders",
                start_time=now + timedelta(days=3, hours=16),
                end_time=now + timedelta(days=3, hours=17, minutes=30),
                location="Auditorio Principal",
                attendees=[
                    {"name": "Director General", "email": "director@company.com"},
                    {"name": "Equipo Marketing", "email": "marketing@company.com"}
                ],
                reminder_minutes=[60, 15]
            )
        ]
        
        for event in sample_events:
            self._events[event.id] = event
        
        # Calendarios de ejemplo
        self._calendars["personal"] = {
            "name": "Calendario Personal",
            "provider": CalendarProvider.GOOGLE.value,
            "color": "#4285F4",
            "is_primary": True
        }
        
        self._calendars["work"] = {
            "name": "Calendario Laboral",
            "provider": CalendarProvider.GOOGLE.value,
            "color": "#34A853",
            "is_primary": False
        }
    
    def _parse_time(self, time_str: str) -> datetime:
        """Convertir string de tiempo a datetime"""
        hour, minute = map(int, time_str.split(':'))
        today = datetime.now(self.timezone).replace(hour=hour, minute=minute, second=0, microsecond=0)
        return today
    
    def _get_business_day_schedule(self, date: datetime) -> List[Tuple[datetime, datetime]]:
        """Obtener horarios de trabajo para un día específico"""
        day_name = calendar.day_name[date.weekday()].lower()
        schedule = self.business_hours.get(day_name, {"start": "00:00", "end": "00:00"})
        
        start_time = self._parse_time(schedule["start"])
        end_time = self._parse_time(schedule["end"])
        
        # Si el día es el mismo que hoy, ajustar al futuro
        if date.date() == datetime.now(self.timezone).date():
            if start_time <= datetime.now(self.timezone):
                start_time = datetime.now(self.timezone) + timedelta(hours=1)
        
        return [(start_time, end_time)] if schedule["start"] != "00:00" else []
    
    def _calculate_time_conflicts(
        self,
        events: List[Event],
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """Verificar conflictos de tiempo"""
        for event in events:
            if (start_time < event.end_time and end_time > event.start_time):
                return True
        return False
    
    def _find_available_slots(
        self,
        date_range: Tuple[datetime, datetime],
        duration_minutes: int,
        working_hours_only: bool = True
    ) -> List[TimeSlot]:
        """Encontrar slots de tiempo disponibles"""
        start_date, end_date = date_range
        slots = []
        
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        while current_date <= end_date:
            daily_schedule = self._get_business_day_schedule(current_date)
            
            for start_time, end_time in daily_schedule:
                slot_start = start_time
                
                while slot_start + timedelta(minutes=duration_minutes) <= end_time:
                    slot_end = slot_start + timedelta(minutes=duration_minutes)
                    
                    # Verificar conflictos con eventos existentes
                    conflicts = self._check_time_conflicts(slot_start, slot_end)
                    
                    if not conflicts or not working_hours_only:
                        # Calcular score basado en preferencias
                        score = self._calculate_slot_score(slot_start, duration_minutes)
                        
                        slots.append(TimeSlot(
                            start_time=slot_start,
                            end_time=slot_end,
                            duration_minutes=duration_minutes,
                            available=not conflicts,
                            score=score
                        ))
                    
                    slot_start += timedelta(minutes=30)  # Incrementar en 30 min
            
            current_date += timedelta(days=1)
        
        # Ordenar por score (mejor primero)
        slots.sort(key=lambda x: x.score, reverse=True)
        return slots[:20]  # Limitar a 20 mejores opciones
    
    def _check_time_conflicts(self, start_time: datetime, end_time: datetime) -> bool:
        """Verificar conflictos con eventos existentes"""
        for event in self._events.values():
            if (event.status != EventStatus.CANCELLED and
                start_time < event.end_time and end_time > event.start_time):
                return True
        return False
    
    def _calculate_slot_score(self, start_time: datetime, duration_minutes: int) -> float:
        """Calcular score de preferencia para un slot"""
        score = 0.0
        
        # Preferencia por horarios de mañana (9-12)
        if 9 <= start_time.hour < 12:
            score += 1.0
        
        # Preferencia por evitar inicio de semana lunes 9:00
        if start_time.weekday() == 0 and start_time.hour == 9:
            score -= 0.5
        
        # Preferencia por evitar horas de almuerzo (13-14)
        if 13 <= start_time.hour < 14:
            score -= 0.3
        
        # Preferencia por evitar viernes tarde después 16:00
        if start_time.weekday() == 4 and start_time.hour >= 16:
            score -= 0.4
        
        return score
    
    async def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        event_type: EventType = EventType.MEETING,
        description: str = "",
        location: Optional[str] = None,
        attendees: Optional[List[Dict[str, str]]] = None,
        reminder_minutes: Optional[List[int]] = None,
        recurrence: RecurrencePattern = RecurrencePattern.NONE
    ) -> SchedulingResponse:
        """Crear nuevo evento"""
        start_time_proc = time.time()
        
        try:
            event_id = f"event_{int(time.time() * 1000)}"
            
            # Verificar conflictos
            conflicts = self._check_time_conflicts(start_time, end_time)
            if conflicts:
                self.logger.warning(f"Creando evento con conflictos: {event_id}")
            
            # Crear evento
            event = Event(
                id=event_id,
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                event_type=event_type,
                location=location,
                attendees=attendees or [],
                reminder_minutes=reminder_minutes or [],
                recurrence=recurrence
            )
            
            self._events[event_id] = event
            
            self.logger.info(f"Evento creado: {event_id}")
            
            return SchedulingResponse(
                success=True,
                event_id=event_id,
                action="create_event",
                timestamp=time.time(),
                execution_time=time.time() - start_time_proc,
                details={
                    "title": event.title,
                    "start_time": event.start_time.isoformat(),
                    "end_time": event.end_time.isoformat(),
                    "attendees_count": len(event.attendees),
                    "has_conflicts": conflicts
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error creando evento: {str(e)}")
            return SchedulingResponse(
                success=False,
                event_id="",
                action="create_event",
                timestamp=time.time(),
                execution_time=time.time() - start_time_proc,
                error=str(e)
            )
    
    async def find_meeting_slots(
        self,
        duration_minutes: int,
        attendees: List[str],
        date_range: Optional[Tuple[datetime, datetime]] = None,
        preferred_time: Optional[datetime] = None
    ) -> SchedulingResponse:
        """Encontrar slots de tiempo para reunión"""
        start_time_proc = time.time()
        
        try:
            # Configurar rango de fechas si no se proporciona
            if not date_range:
                start_date = datetime.now(self.timezone)
                end_date = start_date + timedelta(days=14)  # Próximas 2 semanas
                date_range = (start_date, end_date)
            
            # Encontrar slots disponibles
            available_slots = self._find_available_slots(date_range, duration_minutes)
            
            # Filtrar por tiempo preferido si se especifica
            if preferred_time:
                preferred_date = preferred_time.date()
                available_slots = [
                    slot for slot in available_slots 
                    if slot.start_time.date() == preferred_date
                ]
            
            self.logger.info(f"Encontrados {len(available_slots)} slots disponibles")
            
            return SchedulingResponse(
                success=True,
                event_id="meeting_slots",
                action="find_meeting_slots",
                timestamp=time.time(),
                execution_time=time.time() - start_time_proc,
                details={
                    "duration_minutes": duration_minutes,
                    "attendees_count": len(attendees),
                    "available_slots": [
                        {
                            "start_time": slot.start_time.isoformat(),
                            "end_time": slot.end_time.isoformat(),
                            "duration_minutes": slot.duration_minutes,
                            "score": slot.score,
                            "available": slot.available
                        }
                        for slot in available_slots[:10]  # Top 10
                    ],
                    "date_range": {
                        "start": date_range[0].isoformat(),
                        "end": date_range[1].isoformat()
                    }
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error buscando slots de reunión: {str(e)}")
            return SchedulingResponse(
                success=False,
                event_id="",
                action="find_meeting_slots",
                timestamp=time.time(),
                execution_time=time.time() - start_time_proc,
                error=str(e)
            )
    
    async def schedule_meeting(self, meeting_request: MeetingRequest) -> SchedulingResponse:
        """Programar reunión automáticamente"""
        start_time_proc = time.time()
        
        try:
            # Encontrar el mejor slot disponible
            if meeting_request.time_range:
                date_range = meeting_request.time_range
            else:
                start_date = datetime.now(self.timezone)
                end_date = start_date + timedelta(days=7)
                date_range = (start_date, end_date)
            
            available_slots = self._find_available_slots(
                date_range, 
                meeting_request.duration_minutes
            )
            
            if not available_slots:
                raise ValueError("No hay slots disponibles para la reunión")
            
            # Tomar el mejor slot disponible
            best_slot = available_slots[0]
            
            # Crear evento
            event_resp = await self.create_event(
                title=meeting_request.title,
                start_time=best_slot.start_time,
                end_time=best_slot.end_time,
                description=meeting_request.description,
                location=meeting_request.location,
                event_type=EventType.MEETING,
                attendees=[{"name": attendee, "email": f"{attendee.replace(' ', '').lower()}@company.com"} 
                          for attendee in meeting_request.attendees]
            )
            
            if not event_resp.success:
                raise Exception("Error creando evento para reunión")
            
            self.logger.info(f"Reunión programada automáticamente: {event_resp.event_id}")
            
            return SchedulingResponse(
                success=True,
                event_id=event_resp.event_id,
                action="schedule_meeting",
                timestamp=time.time(),
                execution_time=time.time() - start_time_proc,
                details={
                    "meeting_request": meeting_request.__dict__,
                    "scheduled_slot": {
                        "start_time": best_slot.start_time.isoformat(),
                        "end_time": best_slot.end_time.isoformat(),
                        "score": best_slot.score
                    },
                    "optimization_score": best_slot.score
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error programando reunión: {str(e)}")
            return SchedulingResponse(
                success=False,
                event_id="",
                action="schedule_meeting",
                timestamp=time.time(),
                execution_time=time.time() - start_time_proc,
                error=str(e)
            )
    
    async def send_calendar_invite(
        self,
        event_id: str,
        attendees: List[str],
        message: Optional[str] = None
    ) -> SchedulingResponse:
        """Enviar invitación de calendario"""
        start_time_proc = time.time()
        
        try:
            if event_id not in self._events:
                raise ValueError(f"Evento no encontrado: {event_id}")
            
            event = self._events[event_id]
            
            # Simular envío de invitaciones
            await asyncio.sleep(0.1)
            
            # Generar URL de calendario (simulado)
            calendar_url = f"https://calendar.google.com/event?eid={event_id}"
            
            # Simular invitaciones enviadas
            invited_count = len(attendees)
            
            self.logger.info(f"Invitación enviada para evento {event_id}")
            
            return SchedulingResponse(
                success=True,
                event_id=event_id,
                action="send_calendar_invite",
                timestamp=time.time(),
                execution_time=time.time() - start_time_proc,
                details={
                    "attendees_count": invited_count,
                    "calendar_url": calendar_url,
                    "invitation_message": message or f"Invitación para: {event.title}",
                    "event_details": {
                        "title": event.title,
                        "start_time": event.start_time.isoformat(),
                        "end_time": event.end_time.isoformat(),
                        "location": event.location
                    }
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error enviando invitación: {str(e)}")
            return SchedulingResponse(
                success=False,
                event_id=event_id,
                action="send_calendar_invite",
                timestamp=time.time(),
                execution_time=time.time() - start_time_proc,
                error=str(e)
            )
    
    async def get_calendar_overview(
        self,
        date_range: Tuple[datetime, datetime],
        calendar_name: Optional[str] = None
    ) -> SchedulingResponse:
        """Obtener resumen de calendario"""
        start_time_proc = time.time()
        
        try:
            start_date, end_date = date_range
            
            # Filtrar eventos en el rango de fechas
            events_in_range = []
            for event in self._events.values():
                if (event.start_time >= start_date and 
                    event.start_time <= end_date and
                    event.status != EventStatus.CANCELLED):
                    events_in_range.append(event)
            
            # Ordenar por fecha
            events_in_range.sort(key=lambda x: x.start_time)
            
            # Calcular estadísticas
            total_events = len(events_in_range)
            meeting_hours = sum(
                (event.end_time - event.start_time).total_seconds() / 3600
                for event in events_in_range if event.event_type == EventType.MEETING
            )
            
            # Agrupar por día
            events_by_day = defaultdict(list)
            for event in events_in_range:
                day_key = event.start_time.strftime("%Y-%m-%d")
                events_by_day[day_key].append({
                    "id": event.id,
                    "title": event.title,
                    "start_time": event.start_time.strftime("%H:%M"),
                    "end_time": event.end_time.strftime("%H:%M"),
                    "type": event.event_type.value,
                    "location": event.location
                })
            
            self.logger.info(f"Resumen de calendario generado: {total_events} eventos")
            
            return SchedulingResponse(
                success=True,
                event_id="calendar_overview",
                action="get_calendar_overview",
                timestamp=time.time(),
                execution_time=time.time() - start_time_proc,
                details={
                    "date_range": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    },
                    "total_events": total_events,
                    "meeting_hours": round(meeting_hours, 1),
                    "events_by_day": dict(events_by_day),
                    "calendar_stats": {
                        "busiest_day": max(events_by_day.items(), key=lambda x: len(x[1]))[0] if events_by_day else None,
                        "average_events_per_day": round(total_events / max(len(events_by_day), 1), 1)
                    }
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error obteniendo resumen de calendario: {str(e)}")
            return SchedulingResponse(
                success=False,
                event_id="",
                action="get_calendar_overview",
                timestamp=time.time(),
                execution_time=time.time() - start_time_proc,
                error=str(e)
            )
    
    async def process_request(
        self,
        request: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Procesar request de programación
        
        Formatos soportados:
        - create_event: {"action": "create_event", "title": "Reunión", "start_time": "2024-01-15T10:00:00Z", "end_time": "2024-01-15T11:00:00Z"}
        - find_meeting_slots: {"action": "find_meeting_slots", "duration_minutes": 60, "attendees": ["Juan", "María"]}
        - schedule_meeting: {"action": "schedule_meeting", "title": "Reunión Importante", "duration_minutes": 90, "attendees": ["Carlos", "Ana"]}
        - send_calendar_invite: {"action": "send_calendar_invite", "event_id": "event_123", "attendees": ["email1@example.com"]}
        - get_calendar_overview: {"action": "get_calendar_overview", "start_date": "2024-01-01", "end_date": "2024-01-31"}
        """
        try:
            await self.ensure_initialized()
            
            action = request.get("action", "").lower()
            
            if action == "create_event":
                title = request.get("title", "")
                start_time_str = request.get("start_time")
                end_time_str = request.get("end_time")
                description = request.get("description", "")
                location = request.get("location")
                attendees = request.get("attendees", [])
                reminder_minutes = request.get("reminder_minutes", [])
                
                if not title or not start_time_str or not end_time_str:
                    raise ValueError("title, start_time y end_time son requeridos")
                
                # Convertir strings a datetime
                try:
                    start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                    end_time = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
                except:
                    # Fallback para formatos más simples
                    from datetime import datetime
                    start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")
                    end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M")
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="create_event",
                        capability=AgentCapability.CALENDAR_MANAGEMENT,
                        operation_func=self.create_event,
                        title=title,
                        start_time=start_time,
                        end_time=end_time,
                        description=description,
                        location=location,
                        attendees=attendees,
                        reminder_minutes=reminder_minutes
                    )
                else:
                    response = await self.create_event(
                        title, start_time, end_time, EventType.MEETING,
                        description, location, attendees, reminder_minutes
                    )
                
                return {
                    "success": response.success,
                    "event_id": response.event_id if response.success else None,
                    "details": response.details,
                    "error": response.error
                }
            
            elif action == "find_meeting_slots":
                duration_minutes = request.get("duration_minutes", 60)
                attendees = request.get("attendees", [])
                start_date_str = request.get("start_date")
                end_date_str = request.get("end_date")
                
                date_range = None
                if start_date_str and end_date_str:
                    try:
                        start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
                        end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
                        date_range = (start_date, end_date)
                    except:
                        pass
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="find_meeting_slots",
                        capability=AgentCapability.TIME_SLOT_FINDING,
                        operation_func=self.find_meeting_slots,
                        duration_minutes=int(duration_minutes),
                        attendees=attendees,
                        date_range=date_range
                    )
                else:
                    response = await self.find_meeting_slots(int(duration_minutes), attendees, date_range)
                
                return {
                    "success": response.success,
                    "available_slots": response.details.get("available_slots", []) if response.success else [],
                    "duration": response.details.get("duration_minutes", 0) if response.success else 0,
                    "error": response.error
                }
            
            elif action == "schedule_meeting":
                title = request.get("title", "")
                duration_minutes = request.get("duration_minutes", 60)
                attendees = request.get("attendees", [])
                description = request.get("description", "")
                location = request.get("location")
                
                if not title or not attendees:
                    raise ValueError("title y attendees son requeridos")
                
                meeting_request = MeetingRequest(
                    title=title,
                    duration_minutes=int(duration_minutes),
                    attendees=attendees,
                    description=description,
                    location=location
                )
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="schedule_meeting",
                        capability=AgentCapability.MEETING_COORDINATION,
                        operation_func=self.schedule_meeting,
                        meeting_request=meeting_request
                    )
                else:
                    response = await self.schedule_meeting(meeting_request)
                
                return {
                    "success": response.success,
                    "event_id": response.event_id if response.success else None,
                    "scheduled_slot": response.details.get("scheduled_slot", {}) if response.success else {},
                    "error": response.error
                }
            
            elif action == "send_calendar_invite":
                event_id = request.get("event_id")
                attendees = request.get("attendees", [])
                message = request.get("message")
                
                if not event_id or not attendees:
                    raise ValueError("event_id y attendees son requeridos")
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="send_calendar_invite",
                        capability=AgentCapability.CALENDAR_MANAGEMENT,
                        operation_func=self.send_calendar_invite,
                        event_id=event_id,
                        attendees=attendees,
                        message=message
                    )
                else:
                    response = await self.send_calendar_invite(event_id, attendees, message)
                
                return {
                    "success": response.success,
                    "calendar_url": response.details.get("calendar_url") if response.success else None,
                    "invited_count": response.details.get("attendees_count", 0) if response.success else 0,
                    "error": response.error
                }
            
            elif action == "get_calendar_overview":
                start_date_str = request.get("start_date")
                end_date_str = request.get("end_date")
                calendar_name = request.get("calendar_name")
                
                if not start_date_str or not end_date_str:
                    raise ValueError("start_date y end_date son requeridos")
                
                try:
                    start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
                    end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
                except:
                    from datetime import datetime
                    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="get_calendar_overview",
                        capability=AgentCapability.SCHEDULE_OPTIMIZATION,
                        operation_func=self.get_calendar_overview,
                        date_range=(start_date, end_date),
                        calendar_name=calendar_name
                    )
                else:
                    response = await self.get_calendar_overview((start_date, end_date), calendar_name)
                
                return {
                    "success": response.success,
                    "overview": response.details if response.success else {},
                    "total_events": response.details.get("total_events", 0) if response.success else 0,
                    "error": response.error
                }
            
            else:
                raise ValueError(f"Acción no soportada: {action}")
                
        except Exception as e:
            self.logger.error(f"Error procesando request de programación: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del agente"""
        return {
            "total_events": len(self._events),
            "calendars_count": len(self._calendars),
            "active_reminders": len(self._reminders),
            "agent_name": "SchedulingAgent",
            "supported_providers": [provider.value for provider in CalendarProvider],
            "event_types": [event_type.value for event_type in EventType],
            "business_hours": self.business_hours,
            "available_actions": [
                "create_event",
                "find_meeting_slots",
                "schedule_meeting",
                "send_calendar_invite",
                "get_calendar_overview"
            ]
        }