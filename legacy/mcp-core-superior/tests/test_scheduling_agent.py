"""
Tests unitarios para Scheduling Agent
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# Añadir el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.scheduling_agent import (
    SchedulingAgent, CalendarEvent, Meeting, Task, RecurringEvent,
    CalendarPlatform, EventStatus, Priority, Reminder
)


class TestSchedulingAgent:
    """Tests para SchedulingAgent"""
    
    @pytest.fixture
    async def agent(self):
        """Fixture para crear agente de prueba"""
        agent = SchedulingAgent()
        await agent._initialize()
        return agent
    
    def test_agent_initialization(self, agent):
        """Test inicialización del agente"""
        assert agent.agent_name == "SchedulingAgent"
        assert agent.is_ready
        assert len(agent.capabilities) > 0
        assert len(agent._events) > 0  # Debe cargar eventos de ejemplo
        assert len(agent._tasks) > 0  # Debe cargar tareas de ejemplo
    
    @pytest.mark.asyncio
    async def test_create_event_basic(self, agent):
        """Test creación básica de evento"""
        event_data = {
            "title": "Reunión de Prueba",
            "description": "Reunión para testing",
            "start_time": "2024-12-01T10:00:00",
            "end_time": "2024-12-01T11:00:00",
            "platform": "google_calendar"
        }
        
        event = await agent.create_event(**event_data)
        
        assert isinstance(event, CalendarEvent)
        assert event.title == event_data["title"]
        assert event.platform == CalendarPlatform.GOOGLE_CALENDAR
        assert event.status == EventStatus.SCHEDULED
    
    @pytest.mark.asyncio
    async def test_create_event_wrong_platform(self, agent):
        """Test creación de evento con plataforma inválida"""
        event_data = {
            "title": "Evento Test",
            "description": "Evento para test",
            "start_time": "2024-12-01T10:00:00",
            "end_time": "2024-12-01T11:00:00",
            "platform": "invalid_platform"
        }
        
        with pytest.raises(ValueError, match="Plataforma no soportada"):
            await agent.create_event(**event_data)
    
    @pytest.mark.asyncio
    async def test_create_event_invalid_time(self, agent):
        """Test creación de evento con tiempo inválido"""
        event_data = {
            "title": "Evento Tiempo Inválido",
            "description": "Evento con tiempo inválido",
            "start_time": "2024-12-01T11:00:00",
            "end_time": "2024-12-01T10:00:00",  # End time antes de start time
            "platform": "google_calendar"
        }
        
        with pytest.raises(ValueError, match="La hora de fin debe ser posterior"):
            await agent.create_event(**event_data)
    
    @pytest.mark.asyncio
    async def test_update_event(self, agent):
        """Test actualización de evento"""
        # Crear evento primero
        event_data = {
            "title": "Evento a Actualizar",
            "description": "Evento para actualizar",
            "start_time": "2024-12-01T14:00:00",
            "end_time": "2024-12-01T15:00:00",
            "platform": "outlook_calendar"
        }
        
        event = await agent.create_event(**event_data)
        
        update_data = {
            "title": "Evento Actualizado",
            "description": "Evento actualizado exitosamente"
        }
        
        updated_event = await agent.update_event(event.id, **update_data)
        
        assert updated_event.title == update_data["title"]
        assert updated_event.description == update_data["description"]
        assert updated_event.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_update_event_nonexistent(self, agent):
        """Test actualización de evento inexistente"""
        with pytest.raises(ValueError, match="Evento no encontrado"):
            await agent.update_event("nonexistent_id", title="Nuevo Título")
    
    @pytest.mark.asyncio
    async def test_delete_event(self, agent):
        """Test eliminación de evento"""
        # Crear evento primero
        event_data = {
            "title": "Evento a Eliminar",
            "description": "Evento para eliminar",
            "start_time": "2024-12-01T16:00:00",
            "end_time": "2024-12-01T17:00:00",
            "platform": "google_calendar"
        }
        
        event = await agent.create_event(**event_data)
        event_id = event.id
        
        result = await agent.delete_event(event_id)
        assert result == True
        
        # Verificar que ya no existe
        events = await agent.get_events("2024-12-01")
        assert not any(e.id == event_id for e in events)
    
    @pytest.mark.asyncio
    async def test_get_events_by_date(self, agent):
        """Test obtención de eventos por fecha"""
        events = await agent.get_events("2024-12-01")
        
        assert isinstance(events, list)
        # Debe retornar eventos que coincidan con la fecha
        if events:
            event = events[0]
            assert isinstance(event, CalendarEvent)
    
    @pytest.mark.asyncio
    async def test_get_events_by_date_range(self, agent):
        """Test obtención de eventos por rango de fechas"""
        events = await agent.get_events("2024-12-01", "2024-12-31")
        
        assert isinstance(events, list)
        # Verificar que todos los eventos están en el rango
        for event in events:
            event_date = datetime.fromisoformat(event.start_time.replace('Z', '+00:00'))
            start_range = datetime.strptime("2024-12-01", "%Y-%m-%d")
            end_range = datetime.strptime("2024-12-31", "%Y-%m-%d")
            assert start_range <= event_date <= end_range
    
    @pytest.mark.asyncio
    async def test_get_event_details(self, agent):
        """Test obtención de detalles de evento"""
        first_event = agent._events[0]
        event = await agent.get_event_details(first_event.id)
        
        assert isinstance(event, CalendarEvent)
        assert event.id == first_event.id
        assert event.title is not None
        assert event.start_time is not None
    
    @pytest.mark.asyncio
    async def test_get_event_details_nonexistent(self, agent):
        """Test obtención de detalles de evento inexistente"""
        with pytest.raises(ValueError, match="Evento no encontrado"):
            await agent.get_event_details("nonexistent_id")
    
    @pytest.mark.asyncio
    async def test_schedule_meeting_basic(self, agent):
        """Test programación básica de reunión"""
        meeting_data = {
            "title": "Reunión de Proyecto",
            "description": "Revisión del proyecto",
            "start_time": "2024-12-02T09:00:00",
            "end_time": "2024-12-02T10:30:00",
            "participants": ["usuario1@example.com", "usuario2@example.com"],
            "platform": "google_calendar"
        }
        
        meeting = await agent.schedule_meeting(**meeting_data)
        
        assert isinstance(meeting, Meeting)
        assert meeting.title == meeting_data["title"]
        assert len(meeting.participants) == len(meeting_data["participants"])
        assert meeting.platform == CalendarPlatform.GOOGLE_CALENDAR
        assert meeting.status == EventStatus.SCHEDULED
    
    @pytest.mark.asyncio
    async def test_schedule_meeting_with_location(self, agent):
        """Test programación de reunión con ubicación"""
        meeting_data = {
            "title": "Reunión Presencial",
            "description": "Reunión en oficina",
            "start_time": "2024-12-02T14:00:00",
            "end_time": "2024-12-02T15:00:00",
            "participants": ["jefe@example.com"],
            "location": "Sala de Conferencias A",
            "platform": "outlook_calendar"
        }
        
        meeting = await agent.schedule_meeting(**meeting_data)
        
        assert isinstance(meeting, Meeting)
        assert meeting.location == meeting_data["location"]
        assert meeting.platform == CalendarPlatform.OUTLOOK_CALENDAR
    
    @pytest.mark.asyncio
    async def test_reschedule_meeting(self, agent):
        """Test reprogramación de reunión"""
        # Crear reunión primero
        meeting_data = {
            "title": "Reunión a Reprogramar",
            "description": "Reunión original",
            "start_time": "2024-12-03T10:00:00",
            "end_time": "2024-12-03T11:00:00",
            "participants": ["user@example.com"],
            "platform": "google_calendar"
        }
        
        meeting = await agent.schedule_meeting(**meeting_data)
        
        # Reprogramar
        new_start = "2024-12-03T15:00:00"
        new_end = "2024-12-03T16:00:00"
        
        rescheduled_meeting = await agent.reschedule_meeting(
            meeting.id, new_start, new_end
        )
        
        assert rescheduled_meeting.start_time == new_start
        assert rescheduled_meeting.end_time == new_end
        assert rescheduled_meeting.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_find_available_slots_basic(self, agent):
        """Test búsqueda básica de horarios disponibles"""
        start_date = "2024-12-01"
        end_date = "2024-12-07"
        duration_minutes = 60
        participants = ["usuario1@example.com"]
        
        slots = await agent.find_available_slots(start_date, end_date, duration_minutes, participants)
        
        assert isinstance(slots, list)
        # Debe retornar al menos algunos horarios disponibles
        assert len(slots) > 0
        
        # Verificar formato de los slots
        if slots:
            slot = slots[0]
            assert "start_time" in slot
            assert "end_time" in slot
    
    @pytest.mark.asyncio
    async def test_find_available_slots_no_availability(self, agent):
        """Test búsqueda de horarios cuando no hay disponibilidad"""
        start_date = "2024-12-01"
        end_date = "2024-12-01"
        duration_minutes = 480  # 8 horas - muy largo para un día
        participants = ["usuario1@example.com"]
        
        slots = await agent.find_available_slots(start_date, end_date, duration_minutes, participants)
        
        # Puede retornar lista vacía o slots mínimos
        assert isinstance(slots, list)
    
    @pytest.mark.asyncio
    async def test_set_reminder(self, agent):
        """Test configuración de recordatorio"""
        event_id = agent._events[0].id
        reminder_data = {
            "minutes_before": 15,
            "message": "Recordatorio de reunión"
        }
        
        reminder = await agent.set_reminder(event_id, **reminder_data)
        
        assert isinstance(reminder, Reminder)
        assert reminder.event_id == event_id
        assert reminder.minutes_before == reminder_data["minutes_before"]
        assert reminder.message == reminder_data["message"]
    
    @pytest.mark.asyncio
    async def test_set_reminder_invalid_event(self, agent):
        """Test configuración de recordatorio para evento inexistente"""
        with pytest.raises(ValueError, match="Evento no encontrado"):
            await agent.set_reminder("nonexistent_event", 15, "Recordatorio")
    
    @pytest.mark.asyncio
    async def test_create_recurring_event(self, agent):
        """Test creación de evento recurrente"""
        recurrence_data = {
            "title": "Reunión Semanal",
            "description": "Reunión semanal del equipo",
            "start_time": "2024-12-01T10:00:00",
            "end_time": "2024-12-01T11:00:00",
            "recurrence_pattern": "weekly",
            "recurrence_count": 4,  # 4 semanas
            "platform": "google_calendar"
        }
        
        recurring_event = await agent.create_recurring_event(**recurrence_data)
        
        assert isinstance(recurring_event, RecurringEvent)
        assert recurring_event.title == recurrence_data["title"]
        assert recurring_event.recurrence_pattern == "weekly"
        assert recurring_event.recurrence_count == 4
    
    @pytest.mark.asyncio
    async def test_create_task_basic(self, agent):
        """Test creación básica de tarea"""
        task_data = {
            "title": "Tarea de Prueba",
            "description": "Descripción de la tarea",
            "due_date": "2024-12-05T17:00:00",
            "priority": Priority.HIGH,
            "platform": "google_calendar"
        }
        
        task = await agent.create_task(**task_data)
        
        assert isinstance(task, Task)
        assert task.title == task_data["title"]
        assert task.due_date == task_data["due_date"]
        assert task.priority == Priority.HIGH
        assert task.status == "pending"
    
    @pytest.mark.asyncio
    async def test_create_task_default_priority(self, agent):
        """Test creación de tarea con prioridad por defecto"""
        task_data = {
            "title": "Tarea Prioridad Media",
            "description": "Descripción",
            "due_date": "2024-12-05T17:00:00",
            "platform": "google_calendar"
            # Sin especificar prioridad
        }
        
        task = await agent.create_task(**task_data)
        
        assert task.priority == Priority.MEDIUM  # Prioridad por defecto
    
    @pytest.mark.asyncio
    async def test_update_task_status(self, agent):
        """Test actualización de estado de tarea"""
        # Crear tarea primero
        task_data = {
            "title": "Tarea a Actualizar",
            "description": "Tarea para actualizar",
            "due_date": "2024-12-05T17:00:00",
            "platform": "outlook_calendar"
        }
        
        task = await agent.create_task(**task_data)
        
        # Actualizar a completado
        updated_task = await agent.update_task_status(task.id, "completed")
        
        assert updated_task.status == "completed"
        assert updated_task.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_get_tasks_by_priority(self, agent):
        """Test obtención de tareas por prioridad"""
        high_priority_tasks = await agent.get_tasks_by_priority(Priority.HIGH)
        
        assert isinstance(high_priority_tasks, list)
        # Todas las tareas retornadas deben tener prioridad alta
        for task in high_priority_tasks:
            assert task.priority == Priority.HIGH
    
    @pytest.mark.asyncio
    async def test_get_overdue_tasks(self, agent):
        """Test obtención de tareas vencidas"""
        overdue_tasks = await agent.get_overdue_tasks()
        
        assert isinstance(overdue_tasks, list)
        # Todas las tareas retornadas deben estar vencidas
        for task in overdue_tasks:
            due_date = datetime.fromisoformat(task.due_date.replace('Z', '+00:00'))
            now = datetime.now()
            assert due_date < now
    
    @pytest.mark.asyncio
    async def test_cancel_event(self, agent):
        """Test cancelación de evento"""
        # Crear evento primero
        event_data = {
            "title": "Evento a Cancelar",
            "description": "Evento para cancelar",
            "start_time": "2024-12-04T10:00:00",
            "end_time": "2024-12-04T11:00:00",
            "platform": "google_calendar"
        }
        
        event = await agent.create_event(**event_data)
        
        result = await agent.cancel_event(event.id)
        assert result == True
        
        # Verificar que el estado cambió
        updated_event = await agent.get_event_details(event.id)
        assert updated_event.status == EventStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_send_meeting_invitations(self, agent):
        """Test envío de invitaciones de reunión"""
        meeting_id = agent._events[0].id
        participants = ["invitado1@example.com", "invitado2@example.com"]
        
        result = await agent.send_meeting_invitations(meeting_id, participants)
        
        assert result == True
        # Verificar que las invitaciones se enviaron
        meeting = await agent.get_event_details(meeting_id)
        assert len(meeting.participants) >= len(participants)
    
    @pytest.mark.asyncio
    async def test_sync_calendar(self, agent):
        """Test sincronización de calendario"""
        result = await agent.sync_calendar("google_calendar")
        
        assert isinstance(result, dict)
        assert "synced_events" in result
        assert "updated_events" in result
        assert isinstance(result["synced_events"], int)
        assert isinstance(result["updated_events"], int)
    
    @pytest.mark.asyncio
    async def test_get_calendar_summary(self, agent):
        """Test obtención de resumen de calendario"""
        start_date = "2024-12-01"
        end_date = "2024-12-07"
        
        summary = await agent.get_calendar_summary(start_date, end_date)
        
        assert "total_events" in summary
        assert "total_tasks" in summary
        assert "upcoming_events" in summary
        assert "completed_tasks" in summary
        assert "busy_hours" in summary
        
        assert isinstance(summary["total_events"], int)
        assert isinstance(summary["total_tasks"], int)
        assert isinstance(summary["busy_hours"], (int, float))
    
    @pytest.mark.asyncio
    async def test_get_daily_schedule(self, agent):
        """Test obtención de horario diario"""
        date = "2024-12-01"
        schedule = await agent.get_daily_schedule(date)
        
        assert isinstance(schedule, list)
        # Los eventos deben estar ordenados por hora
        if len(schedule) > 1:
            for i in range(len(schedule) - 1):
                current_time = datetime.fromisoformat(schedule[i]["start_time"].replace('Z', '+00:00'))
                next_time = datetime.fromisoformat(schedule[i + 1]["start_time"].replace('Z', '+00:00'))
                assert current_time <= next_time
    
    def test_get_supported_platforms(self, agent):
        """Test obtención de plataformas soportadas"""
        platforms = agent.get_supported_platforms()
        
        assert isinstance(platforms, list)
        assert CalendarPlatform.GOOGLE_CALENDAR in platforms
        assert CalendarPlatform.OUTLOOK_CALENDAR in platforms
        assert CalendarPlatform.APPLE_CALENDAR in platforms
    
    @pytest.mark.asyncio
    async def test_bulk_reschedule_events(self, agent):
        """Test reprogramación masiva de eventos"""
        # Seleccionar algunos eventos
        event_ids = [e.id for e in agent._events[:2]]
        time_offset_hours = 1  # Mover todos 1 hora adelante
        
        result = await agent.bulk_reschedule_events(event_ids, time_offset_hours)
        
        assert result == True
        
        # Verificar que algunos eventos se reprogramaron
        reprogrammed_count = 0
        for event_id in event_ids:
            event = await agent.get_event_details(event_id)
            if event.updated_at is not None:
                reprogrammed_count += 1
        
        assert reprogrammed_count > 0
    
    @pytest.mark.asyncio
    async def test_create_time_block(self, agent):
        """Test creación de bloque de tiempo"""
        block_data = {
            "title": "Tiempo de Trabajo Enfocado",
            "start_time": "2024-12-05T09:00:00",
            "end_time": "2024-12-05T11:00:00",
            "platform": "google_calendar"
        }
        
        block = await agent.create_time_block(**block_data)
        
        assert isinstance(block, CalendarEvent)
        assert block.title == block_data["title"]
        assert block.is_time_block == True
        assert block.status == EventStatus.BLOCKED
    
    @pytest.mark.asyncio
    async def test_get_productivity_metrics(self, agent):
        """Test obtención de métricas de productividad"""
        start_date = "2024-12-01"
        end_date = "2024-12-07"
        
        metrics = await agent.get_productivity_metrics(start_date, end_date)
        
        assert "events_completed" in metrics
        assert "tasks_completed" in metrics
        assert "total_meeting_hours" in metrics
        assert "focus_time_hours" in metrics
        assert "productivity_score" in metrics
        
        assert isinstance(metrics["events_completed"], int)
        assert isinstance(metrics["tasks_completed"], int)
        assert isinstance(metrics["total_meeting_hours"], (int, float))
        assert isinstance(metrics["productivity_score"], (int, float))
    
    @pytest.mark.asyncio
    async def test_handle_exceptions_invalid_datetime(self, agent):
        """Test manejo de excepciones con datetime inválido"""
        with pytest.raises(ValueError, match="Formato de fecha/hora inválido"):
            await agent.create_event(
                title="Test Event",
                description="Test Description",
                start_time="invalid_datetime",
                end_time="2024-12-01T11:00:00",
                platform="google_calendar"
            )
    
    @pytest.mark.asyncio
    async def test_handle_exceptions_network_error(self, agent):
        """Test manejo de excepciones de red"""
        # Simular un error de red mockeando requests
        with patch('agents.scheduling_agent.requests.post') as mock_post:
            mock_post.side_effect = Exception("Error de red simulado")
            
            with pytest.raises(Exception):
                await agent.create_event(
                    title="Test Event",
                    description="Test Description",
                    start_time="2024-12-01T10:00:00",
                    end_time="2024-12-01T11:00:00",
                    platform="google_calendar"
                )


class TestSchedulingDataClasses:
    """Tests para las clases de datos del agente de programación"""
    
    def test_calendar_event_creation(self):
        """Test creación de objeto CalendarEvent"""
        event = CalendarEvent(
            id="event_test",
            title="Test Event",
            description="Test Description",
            start_time="2024-12-01T10:00:00",
            end_time="2024-12-01T11:00:00",
            platform=CalendarPlatform.GOOGLE_CALENDAR,
            status=EventStatus.SCHEDULED,
            created_at=datetime.now()
        )
        
        assert event.id == "event_test"
        assert event.title == "Test Event"
        assert event.platform == CalendarPlatform.GOOGLE_CALENDAR
        assert event.status == EventStatus.SCHEDULED
    
    def test_meeting_creation(self):
        """Test creación de objeto Meeting"""
        meeting = Meeting(
            id="meeting_test",
            title="Test Meeting",
            description="Test Meeting Description",
            start_time="2024-12-01T10:00:00",
            end_time="2024-12-01T11:00:00",
            participants=["user1@example.com", "user2@example.com"],
            location="Sala de Conferencias",
            platform=CalendarPlatform.GOOGLE_CALENDAR,
            status=EventStatus.SCHEDULED,
            created_at=datetime.now()
        )
        
        assert meeting.id == "meeting_test"
        assert meeting.title == "Test Meeting"
        assert len(meeting.participants) == 2
        assert meeting.location == "Sala de Conferencias"
    
    def test_task_creation(self):
        """Test creación de objeto Task"""
        task = Task(
            id="task_test",
            title="Test Task",
            description="Test Task Description",
            due_date="2024-12-01T17:00:00",
            priority=Priority.HIGH,
            status="pending",
            platform=CalendarPlatform.GOOGLE_CALENDAR,
            created_at=datetime.now()
        )
        
        assert task.id == "task_test"
        assert task.title == "Test Task"
        assert task.due_date == "2024-12-01T17:00:00"
        assert task.priority == Priority.HIGH
        assert task.status == "pending"
    
    def test_recurring_event_creation(self):
        """Test creación de objeto RecurringEvent"""
        recurring_event = RecurringEvent(
            id="recurring_test",
            title="Weekly Meeting",
            description="Weekly Team Meeting",
            start_time="2024-12-01T10:00:00",
            end_time="2024-12-01T11:00:00",
            recurrence_pattern="weekly",
            recurrence_count=4,
            platform=CalendarPlatform.GOOGLE_CALENDAR,
            status=EventStatus.SCHEDULED,
            created_at=datetime.now()
        )
        
        assert recurring_event.id == "recurring_test"
        assert recurring_event.recurrence_pattern == "weekly"
        assert recurring_event.recurrence_count == 4
    
    def test_reminder_creation(self):
        """Test creación de objeto Reminder"""
        reminder = Reminder(
            id="reminder_test",
            event_id="event_test",
            minutes_before=15,
            message="Meeting reminder",
            sent=False,
            created_at=datetime.now()
        )
        
        assert reminder.id == "reminder_test"
        assert reminder.event_id == "event_test"
        assert reminder.minutes_before == 15
        assert reminder.message == "Meeting reminder"
        assert reminder.sent == False


if __name__ == "__main__":
    # Ejecutar tests específicos si se ejecuta directamente
    pytest.main([__file__, "-v"])