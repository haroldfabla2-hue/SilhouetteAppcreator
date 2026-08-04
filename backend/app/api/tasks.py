"""
Endpoints para streaming de tareas
/api/v1/tasks/{id}/stream
"""
import asyncio
import logging
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..services.task_manager import TaskStatus, task_manager
from ..services.task_orchestrator_integrator import get_task_orchestrator_integrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["tasks"])

# Modelos de request/response
class ExecuteTaskRequest(BaseModel):
    """Request para ejecutar una tarea"""
    objective: str = Field(..., description="Objetivo o tarea a cumplir")
    user_id: str | None = Field(None, description="ID del usuario que solicita la tarea")
    context: dict[str, Any] | None = Field(None, description="Contexto adicional para la ejecución")
class TaskUpdate(BaseModel):
    """Update de tarea para streaming"""
    task_id: str
    status: Literal[
        "started",
        "in_progress",
        "completed",
        "error",
        "cancelled",
        # Estados que sólo emite el stream, no la tarea en sí.
        "not_found",
        "stream_timeout",
    ]
    phase: str | None = Field(None, description="Fase actual del proceso")
    progress: float | None = Field(None, description="Progreso (0.0-1.0)", ge=0.0, le=1.0)
    message: str | None = Field(None, description="Mensaje descriptivo")
    result: dict[str, Any] | None = Field(None, description="Resultado parcial")
    agent_updates: dict[str, Any] | None = Field(None, description="Updates por agente")
    metadata: dict[str, Any] | None = Field(None, description="Metadatos adicionales")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class TaskStreamConfig(BaseModel):
    """Configuración para streaming de tareas"""
    update_frequency: float = Field(1.0, description="Frecuencia de updates en segundos", ge=0.1, le=10.0)
    include_results: bool = Field(True, description="Incluir resultados parciales")
    include_agent_details: bool = Field(False, description="Incluir detalles por agente")
    max_duration: int = Field(300, description="Duración máxima en segundos", ge=30, le=1800)


@router.post("/create")
async def create_task(
    objective: str,
    user_id: str | None = None,
    metadata: dict[str, Any] | None = None
):
    """
    Crea una nueva tarea para procesar

    - **objective**: Objetivo o tarea a cumplir
    - **user_id**: ID del usuario que solicita la tarea
    - **metadata**: Metadatos adicionales
    """

    try:
        logger.info(f"Creando nueva tarea: {objective}")

        # Crear tarea en TaskManager
        task_id = task_manager.create_task(
            objective=objective,
            user_id=user_id,
            metadata=metadata
        )

        # Inicializar tarea como started
        await task_manager.update_task(
            task_id=task_id,
            status=TaskStatus.STARTED,
            message="Tarea creada e iniciada"
        )

        return {
            "task_id": task_id,
            "status": "created",
            "objective": objective,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "stream_url": f"/api/v1/tasks/{task_id}/stream"
        }

    except Exception as e:
        logger.exception("Error creando tarea")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/execute")
async def execute_task(
    request: ExecuteTaskRequest,
    execute_async: bool = Query(True, description="Ejecutar de forma asíncrona")
):
    """
    Ejecuta una tarea usando el MultiAgentOrchestrator real

    - **request**: Datos de la tarea a ejecutar
    - **execute_async**: Si ejecutar de forma asíncrona (recomendado)
    """

    try:
        logger.info(f"Ejecutando tarea: {request.objective}")

        # Crear tarea en TaskManager
        task_id = task_manager.create_task(
            objective=request.objective,
            user_id=request.user_id,
            metadata=request.context
        )

        # Obtener integrador
        integrator = get_task_orchestrator_integrator()

        if execute_async:
            # Ejecutar asíncronamente
            await integrator.execute_task_async(
                task_id=task_id,
                objective=request.objective,
                user_id=request.user_id,
                context=request.context
            )

            return {
                "task_id": task_id,
                "status": "started",
                "objective": request.objective,
                "user_id": request.user_id,
                "execution_mode": "async",
                "stream_url": f"/api/v1/tasks/{task_id}/stream",
                "status_url": f"/api/v1/tasks/{task_id}/status",
                "message": "Tarea ejecutándose de forma asíncrona"
            }
        else:
            # Ejecutar de forma síncrona (bloqueante)
            result = await integrator.execute_task_with_tracking(
                task_id=task_id,
                objective=request.objective,
                user_id=request.user_id,
                context=request.context
            )

            return {
                "task_id": task_id,
                "status": "completed",
                "objective": request.objective,
                "user_id": request.user_id,
                "execution_mode": "sync",
                "result": result,
                "completed_at": datetime.now().isoformat()
            }

    except Exception as e:
        logger.exception("Error ejecutando tarea")

        # Marcar como error si la tarea se creó
        if 'task_id' in locals():
            await task_manager.update_task(
                task_id=task_id,
                status=TaskStatus.ERROR,
                message=f"Error en ejecución: {str(e)}",
                error=str(e)
            )

        raise HTTPException(status_code=500, detail=f"Error ejecutando tarea: {str(e)}")


@router.get("/{task_id}/stream")
async def stream_task_updates(
    task_id: str = Path(..., description="ID de la tarea"),
    update_frequency: float = Query(1.0, description="Frecuencia de updates en segundos"),
    include_results: bool = Query(True, description="Incluir resultados parciales"),
    include_agent_details: bool = Query(False, description="Incluir detalles por agente"),
    max_duration: int = Query(300, description="Duración máxima en segundos")
):
    """
    Stream de updates en tiempo real para una tarea específica

    - **task_id**: ID de la tarea a seguir
    - **update_frequency**: Frecuencia de updates (0.1-10.0 segundos)
    - **include_results**: Si incluir resultados parciales
    - **include_agent_details**: Si incluir detalles por agente
    - **max_duration**: Duración máxima del stream (30-1800 segundos)
    """

    logger.info(f"Iniciando stream para tarea: {task_id}")

    # Validar parámetros
    if not 0.1 <= update_frequency <= 10.0:
        raise HTTPException(status_code=400, detail="update_frequency debe estar entre 0.1 y 10.0")

    if not 30 <= max_duration <= 1800:
        raise HTTPException(status_code=400, detail="max_duration debe estar entre 30 y 1800 segundos")

    # Verificar que la tarea existe
    task_info = await task_manager.get_task(task_id)
    if not task_info:
        raise HTTPException(status_code=404, detail=f"Tarea no encontrada: {task_id}")

    # Generar stream usando TaskManager real
    return StreamingResponse(
        task_manager.stream_task_updates(
            task_id=task_id,
            update_frequency=update_frequency,
            max_duration=max_duration
        ),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/{task_id}/status")
async def get_task_status(task_id: str):
    """
    Obtiene el estado actual de una tarea

    - **task_id**: ID de la tarea
    """

    try:
        # Obtener estado real del TaskManager
        status_info = await task_manager.get_task_status(task_id)

        if not status_info:
            raise HTTPException(status_code=404, detail=f"Tarea no encontrada: {task_id}")

        # Calcular estimación de finalización si está en progreso
        if status_info["status"] == "in_progress" and status_info.get("progress", 0) > 0:
            # Estimación simple basada en progreso
            elapsed = (datetime.now() - datetime.fromisoformat(status_info["updated_at"])).total_seconds()
            if elapsed > 0:
                remaining_estimate = elapsed * (1 - status_info["progress"]) / status_info["progress"]
                estimated_completion = datetime.now() + timedelta(seconds=remaining_estimate)
                status_info["estimated_completion"] = estimated_completion.isoformat()

        return status_info

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error obteniendo estado de tarea {task_id}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/{task_id}/results")
async def get_task_results(
    task_id: str,
    include_intermediate: bool = Query(False, description="Incluir resultados intermedios")
):
    """
    Obtiene los resultados finales de una tarea

    - **task_id**: ID de la tarea
    - **include_intermediate**: Si incluir resultados intermedios
    """

    # Antes se devolvía una tarea completada inventada — con 150 registros,
    # 298,5 s de duración y 0,045 $ de coste — para cualquier identificador,
    # incluidos los que no existían.
    from ..services.task_manager import task_manager

    tarea = await task_manager.get_task(task_id)
    if tarea is None:
        raise HTTPException(
            status_code=404,
            detail=f"No existe ninguna tarea con identificador '{task_id}'."
        )

    respuesta: dict[str, Any] = {
        "task_id": tarea.task_id,
        "status": tarea.status.value if hasattr(tarea.status, "value") else str(tarea.status),
        "created_at": getattr(tarea, "created_at", None),
        "updated_at": getattr(tarea, "updated_at", None),
        "final_result": getattr(tarea, "result", None),
        "error": getattr(tarea, "error", None),
    }

    if include_intermediate:
        # Sólo se devuelven los pasos que la tarea realmente registró.
        respuesta["intermediate_results"] = getattr(tarea, "steps", []) or []

    return respuesta


@router.delete("/{task_id}")
async def cancel_task(task_id: str):
    """
    Cancela una tarea en ejecución

    - **task_id**: ID de la tarea a cancelar
    """

    try:
        logger.info(f"Cancelando tarea: {task_id}")

        # Cancelar tarea en TaskManager
        success = await task_manager.delete_task(task_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Tarea no encontrada: {task_id}")

        return {
            "task_id": task_id,
            "status": "cancelled",
            "cancelled_at": datetime.now().isoformat(),
            "message": "Tarea cancelada por solicitud del usuario"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error cancelando tarea {task_id}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/list")
async def list_tasks(
    user_id: str | None = Query(None, description="Filtrar por usuario"),
    status: str | None = Query(None, description="Filtrar por estado"),
    limit: int = Query(20, description="Número máximo de resultados", ge=1, le=100),
    offset: int = Query(0, description="Offset para paginación", ge=0)
):
    """
    Lista tareas con filtros opcionales

    - **user_id**: Filtrar por usuario específico
    - **status**: Filtrar por estado (created, started, in_progress, completed, error, cancelled)
    - **limit**: Número máximo de resultados (1-100)
    - **offset**: Offset para paginación
    """

    try:
        # Convertir status string a enum
        status_enum = None
        if status:
            try:
                status_enum = TaskStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Estado inválido: {status}")

        # Obtener tareas del TaskManager real
        tasks = await task_manager.list_tasks(
            user_id=user_id,
            status=status_enum,
            limit=limit,
            offset=offset
        )

        return {
            "tasks": tasks,
            "total": len(tasks),
            "limit": limit,
            "offset": offset,
            "has_more": len(tasks) == limit
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error listando tareas")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# Funciones auxiliares para streaming
async def _generate_task_updates(
    task_id: str,
    update_frequency: float,
    include_results: bool,
    include_agent_details: bool,
    max_duration: int
) -> AsyncGenerator[str, None]:
    """Emite las actualizaciones REALES de una tarea.

    Antes esta función recorría una lista fija de cinco fases con progreso
    predefinido (0.2, 0.4, 0.8, 0.9, 1.0) y las emitía por temporizador, sin
    mirar la tarea: cualquier identificador producía el mismo avance ficticio y
    terminaba anunciando "Tarea completada exitosamente".

    Ahora se suscribe al TaskManager y retransmite lo que la tarea reporta. Si
    la tarea no existe, lo dice y cierra.
    """
    from ..services.task_manager import task_manager

    start_time = datetime.now()

    tarea = await task_manager.get_task(task_id)
    if tarea is None:
        error = TaskUpdate(
            task_id=task_id,
            status="not_found",
            message=f"No existe ninguna tarea con identificador '{task_id}'.",
        )
        yield f"data: {error.json()}\n\n"
        yield "data: [DONE]\n\n"
        return

    cola: asyncio.Queue = asyncio.Queue()
    task_manager.subscribe(task_id, cola)

    try:
        while True:
            transcurrido = (datetime.now() - start_time).total_seconds()
            if transcurrido >= max_duration:
                timeout = TaskUpdate(
                    task_id=task_id,
                    status="stream_timeout",
                    message=f"El stream se cerró tras {max_duration} s sin que la tarea terminara.",
                    metadata={"elapsed_seconds": transcurrido},
                )
                yield f"data: {timeout.json()}\n\n"
                break

            try:
                actualizacion = await asyncio.wait_for(
                    cola.get(), timeout=max(update_frequency, 1.0)
                )
            except asyncio.TimeoutError:
                # Sin novedades: se emite un latido para mantener viva la conexión.
                yield ": keep-alive\n\n"
                continue

            update = TaskUpdate(
                task_id=task_id,
                status=str(actualizacion.get("status", "in_progress")),
                phase=actualizacion.get("phase"),
                progress=actualizacion.get("progress"),
                message=actualizacion.get("message", ""),
                result=actualizacion.get("result") if include_results else None,
                agent_updates=actualizacion.get("agent_updates") if include_agent_details else None,
                metadata={"elapsed_seconds": (datetime.now() - start_time).total_seconds()},
            )
            yield f"data: {update.json()}\n\n"

            if update.status in ("completed", "failed", "cancelled"):
                break

        yield "data: [DONE]\n\n"

    except asyncio.CancelledError:
        logger.info(f"Stream cancelado para tarea {task_id}")
        raise
    except Exception as e:
        logger.exception(f"Error en stream de tarea {task_id}")
        fallo = TaskUpdate(
            task_id=task_id,
            status="error",
            message=f"Error en el stream: {e}",
        )
        yield f"data: {fallo.json()}\n\n"
        yield "data: [DONE]\n\n"
    finally:
        task_manager.unsubscribe(task_id, cola)

