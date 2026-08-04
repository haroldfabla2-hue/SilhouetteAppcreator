"""
Modelos de mensajes para comunicación entre agentes
Basado en el contrato A2A definido en la arquitectura
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageIntent(str, Enum):
    """Tipos de intención de mensaje"""
    INFORMATION_REQUEST = "information_request"
    DELEGATION = "delegation"
    VALIDATION = "validation"
    SYNTHESIS = "synthesis"
    ERROR = "error"
    RESULT = "result"


class MessageStatus(str, Enum):
    """Estados de procesamiento de mensaje"""
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"
    TIMEOUT = "timeout"


class ErrorInfo(BaseModel):
    """Información de error"""
    code: str
    message: str
    retry_after: int | None = None
    retryable: bool = True


class Budget(BaseModel):
    """Presupuesto de recursos"""
    tokens: int | None = None
    time_seconds: int | None = None
    tools_max: int | None = 3


class AgentMessage(BaseModel):
    """
    Mensaje estándar entre agentes
    Implementa el contrato A2A definido en la arquitectura
    """
    # Identificadores
    message_id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    trace_id: str = Field(default_factory=lambda: f"trc_{uuid.uuid4().hex[:12]}")
    conversation_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Remitente/Destinatarios
    sender: str
    recipients: list[str]

    # Propósito
    intent: MessageIntent

    # Control de versión y causalidad
    context_version: str = "v1"
    causal_marks: dict[str, int] | None = None
    in_reply_to: str | None = None

    # Contenido
    payload: dict[str, Any]
    references: list[str] | None = None

    # Presupuesto
    budget: Budget | None = None

    # Estado
    status: MessageStatus = MessageStatus.PENDING
    errors: list[ErrorInfo] | None = None

    # Metadatos
    metadata: dict[str, Any] | None = None


class TaskDelegation(BaseModel):
    """Payload específico para delegación de tareas"""
    task_id: str
    objetivo: str
    tool_map: list[str]
    limites: Budget
    criterio_exito: str
    context: dict[str, Any] | None = None


class ValidationRequest(BaseModel):
    """Payload específico para validación"""
    trajectory_id: str
    criterios: list[str]
    thresholds: list[float]
    eval_type: str  # "llm_judge" o "code"


class SynthesisRequest(BaseModel):
    """Payload específico para síntesis"""
    inputs: list[dict[str, Any]]
    referencias: list[str] | None = None
    formato_salida: str
    citacion: bool = True


class AgentResponse(BaseModel):
    """Respuesta de un agente"""
    message_id: str
    original_message_id: str
    agent_id: str
    status: MessageStatus
    result: dict[str, Any] | None = None
    errors: list[ErrorInfo] | None = None
    execution_time_ms: float | None = None
    tokens_used: int | None = None
