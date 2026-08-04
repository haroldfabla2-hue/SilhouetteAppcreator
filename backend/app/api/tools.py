"""
Endpoints para ejecución de herramientas
/api/v1/tools/execute
"""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tools", tags=["tools"])

# Modelos de request/response
class ToolRequest(BaseModel):
    """Request para ejecutar una herramienta"""
    tool_name: str = Field(..., description="Nombre de la herramienta a ejecutar")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Parámetros para la herramienta")
    executor_type: str = Field("general", description="Tipo de executor (general, code, web, docs)")
    user_id: str | None = Field(None, description="ID del usuario")
    timeout: int | None = Field(30, description="Timeout en segundos")
    async_mode: bool = Field(False, description="Si ejecutar de forma asíncrona")


class ToolResponse(BaseModel):
    """Response de ejecución de herramienta"""
    execution_id: str
    tool_name: str
    status: str  # "success", "error", "timeout"
    result: dict[str, Any] | None = None
    error: str | None = None
    execution_time_ms: int
    metadata: dict[str, Any] | None = None


class ToolsListResponse(BaseModel):
    """Response con lista de herramientas disponibles"""
    tools: list[dict[str, Any]]
    executors: list[str]
    total_tools: int


@router.get("/", response_model=ToolsListResponse)
async def list_available_tools():
    """
    Lista todas las herramientas disponibles organizadas por tipo de executor
    """
    # El catálogo sale del ToolManager, no de una lista escrita a mano: antes se
    # anunciaban 12 herramientas que podían no existir, y ninguna de las que sí
    # existían aparecía si no estaba en esa lista.
    try:
        manager = _get_tool_manager()
        herramientas = manager.list_tools()
    except Exception as e:
        logger.exception("No se pudo consultar el registro de herramientas")
        raise HTTPException(
            status_code=503,
            detail=f"El registro de herramientas no está disponible: {e}"
        ) from None

    ejecutores = sorted({t.get("executor_type", "general") for t in herramientas})
    return ToolsListResponse(
        tools=herramientas,
        executors=ejecutores or ["general"],
        total_tools=len(herramientas)
    )


@router.post("/execute", response_model=ToolResponse)
async def execute_tool(
    request: ToolRequest,
    background_tasks: BackgroundTasks
):
    """
    Ejecuta una herramienta específica

    - **tool_name**: Nombre de la herramienta
    - **parameters**: Parámetros para la herramienta
    - **executor_type**: Tipo de executor (general, code, web, docs)
    - **user_id**: ID del usuario (opcional)
    - **timeout**: Timeout en segundos (default: 30)
    - **async_mode**: Si ejecutar de forma asíncrona (default: False)
    """

    execution_id = f"exec_{uuid.uuid4().hex[:12]}"
    start_time = datetime.now()

    logger.info(f"Iniciando ejecución {execution_id}: {request.tool_name}")

    try:
        if request.async_mode:
            # Ejecutar en background y retornar ID de tracking
            background_tasks.add_task(
                _execute_tool_background,
                execution_id,
                request,
                start_time
            )

            return ToolResponse(
                execution_id=execution_id,
                tool_name=request.tool_name,
                status="started",
                execution_time_ms=0,
                metadata={"message": "Ejecución iniciada en background"}
            )

        # Ejecución síncrona
        result = await _execute_tool_sync(execution_id, request, start_time)
        return result

    except asyncio.TimeoutError:
        logger.warning(f"Timeout en ejecución {execution_id}")
        return ToolResponse(
            execution_id=execution_id,
            tool_name=request.tool_name,
            status="timeout",
            error="Ejecución timeout",
            execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
        )

    except Exception as e:
        logger.exception(f"Error en ejecución {execution_id}")
        return ToolResponse(
            execution_id=execution_id,
            tool_name=request.tool_name,
            status="error",
            error=str(e),
            execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
        )


@router.get("/execute/{execution_id}")
async def get_execution_status(execution_id: str):
    """
    Obtiene el estado de una ejecución asíncrona

    - **execution_id**: ID de la ejecución
    """

    # Devolver 200 con `status: not_implemented` hacía que un cliente que sólo
    # mira el código HTTP creyera que la consulta funcionó. 501 lo dice en el
    # protocolo, no sólo en el cuerpo.
    raise HTTPException(
        status_code=501,
        detail=(
            "El seguimiento de ejecuciones asíncronas no está implementado. "
            "Use async_mode=false para obtener el resultado en la misma llamada."
        ),
    )


async def _execute_tool_sync(
    execution_id: str,
    request: ToolRequest,
    start_time: datetime
) -> ToolResponse:
    """
    Ejecuta una herramienta de forma síncrona
    """

    # Antes, cada rama llamaba a una `_simulate_*` que devolvía datos
    # fabricados y siempre `status: success`. Ahora se ejecuta la herramienta
    # real del ToolManager; si no existe, se dice, en lugar de simularla.
    from backend.tools.tool_manager import ToolNotFoundError

    manager = _get_tool_manager()

    try:
        # ToolManager es síncrono; se ejecuta fuera del bucle de eventos para
        # no bloquear el resto de peticiones.
        loop = asyncio.get_running_loop()
        tool_result = await loop.run_in_executor(
            None, lambda: manager.execute_tool(request.tool_name, **request.parameters)
        )
    except ToolNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=(
                f"La herramienta '{request.tool_name}' no está registrada. "
                f"Disponibles: {', '.join(t['name'] for t in manager.list_tools())}"
            ),
        ) from exc

    execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

    # El estado lo decide la herramienta, no el hecho de haberla invocado.
    exito = getattr(tool_result, "success", True)
    datos = getattr(tool_result, "data", tool_result)
    error = getattr(tool_result, "error", None)

    return ToolResponse(
        execution_id=execution_id,
        tool_name=request.tool_name,
        status="success" if exito else "error",
        result=datos if exito else {"error": error},
        error=None if exito else str(error),
        execution_time_ms=execution_time
    )


_tool_manager: Any = None


def _get_tool_manager() -> Any:
    """ToolManager compartido, creado bajo demanda."""
    global _tool_manager
    if _tool_manager is None:
        from backend.tools.tool_manager import ToolManager

        _tool_manager = ToolManager()
    return _tool_manager


async def _execute_tool_background(
    execution_id: str,
    request: ToolRequest,
    start_time: datetime
):
    """
    Ejecuta una herramienta en background
    """
    logger.info(f"Ejecutando en background {execution_id}")

    try:
        result = await _execute_tool_sync(execution_id, request, start_time)
        # TODO: Guardar resultado en Redis para tracking
        logger.info(f"Background execution {execution_id} completed")

    except Exception:
        logger.exception(f"Error en background execution {execution_id}")
        # TODO: Guardar error en Redis para tracking


# Simulaciones de herramientas para pruebas




