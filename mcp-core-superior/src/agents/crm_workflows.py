"""
Workflows Automatizados - Automatización de Procesos CRM
Flujos de trabajo inteligentes para ventas, marketing y seguimiento
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod


class WorkflowTrigger(Enum):
    """Tipos de triggers para workflows"""
    LEAD_CREATED = "lead_created"
    LEAD_UPDATED = "lead_updated"
    LEAD_STAGE_CHANGED = "lead_stage_changed"
    OPPORTUNITY_CREATED = "opportunity_created"
    OPPORTUNITY_STAGE_CHANGED = "opportunity_stage_changed"
    OPPORTUNITY_WON = "opportunity_won"
    OPPORTUNITY_LOST = "opportunity_lost"
    ACCOUNT_CREATED = "account_created"
    ACTIVITY_COMPLETED = "activity_completed"
    TIME_BASED = "time_based"
    WEBHOOK_EVENT = "webhook_event"


class WorkflowAction(Enum):
    """Tipos de acciones en workflows"""
    CREATE_TASK = "create_task"
    SEND_EMAIL = "send_email"
    UPDATE_RECORD = "update_record"
    ASSIGN_TO_USER = "assign_to_user"
    CREATE_FOLLOW_UP = "create_follow_up"
    NOTIFY_TEAM = "notify_team"
    SYNC_DATA = "sync_data"
    SCORE_LEAD = "score_lead"
    TRIGGER_CAMPAIGN = "trigger_campaign"
    SCHEDULE_CALL = "schedule_call"


@dataclass
class WorkflowCondition:
    """Condición para workflow"""
    field: str
    operator: str  # equals, not_equals, contains, greater_than, less_than, etc.
    value: Any
    logic_operator: Optional[str] = None  # AND, OR


@dataclass
class WorkflowActionStep:
    """Paso de acción en workflow"""
    action_type: WorkflowAction
    parameters: Dict[str, Any]
    delay_seconds: Optional[int] = None
    condition: Optional[WorkflowCondition] = None


@dataclass
class WorkflowDefinition:
    """Definición de workflow"""
    name: str
    description: str
    platform: str
    trigger: WorkflowTrigger
    conditions: List[WorkflowCondition] = field(default_factory=list)
    actions: List[WorkflowActionStep] = field(default_factory=list)
    active: bool = True
    priority: int = 1


@dataclass
class WorkflowExecution:
    """Ejecución de workflow"""
    workflow_id: str
    trigger_data: Dict[str, Any]
    started_at: datetime
    status: str = "running"
    actions_completed: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class BaseWorkflowAction(ABC):
    """Clase base para acciones de workflow"""
    
    def __init__(self, parameters: Dict[str, Any]):
        self.parameters = parameters
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> bool:
        """Ejecutar acción"""
        pass


class CreateTaskAction(BaseWorkflowAction):
    """Crear tarea en CRM"""
    
    async def execute(self, context: Dict[str, Any]) -> bool:
        """Crear tarea de seguimiento"""
        try:
            task_data = {
                "subject": self.parameters.get("subject", "Seguimiento automático"),
                "description": self.parameters.get("description", ""),
                "due_date": self.parameters.get("due_date"),
                "priority": self.parameters.get("priority", "normal"),
                "assigned_to": self.parameters.get("assigned_to"),
                "related_to": context.get("record_id")
            }
            
            # Aquí se integraría con el CRM específico
            self.logger.info(f"Tarea creada: {task_data['subject']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error creando tarea: {str(e)}")
            return False


class SendEmailAction(BaseWorkflowAction):
    """Enviar email automatizado"""
    
    async def execute(self, context: Dict[str, Any]) -> bool:
        """Enviar email según plantilla"""
        try:
            email_data = {
                "to": self.parameters.get("to", context.get("email")),
                "subject": self.parameters.get("subject"),
                "template": self.parameters.get("template"),
                "variables": {
                    **context,
                    **self.parameters.get("variables", {})
                }
            }
            
            # Aquí se integraría con el sistema de email
            self.logger.info(f"Email enviado a: {email_data['to']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error enviando email: {str(e)}")
            return False


class UpdateRecordAction(BaseWorkflowAction):
    """Actualizar registro en CRM"""
    
    async def execute(self, context: Dict[str, Any]) -> bool:
        """Actualizar campos del registro"""
        try:
            update_data = self.parameters.get("fields", {})
            record_id = context.get("record_id")
            record_type = context.get("record_type")
            
            # Aquí se integraría con el CRM específico
            self.logger.info(f"Registro {record_id} actualizado: {update_data}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error actualizando registro: {str(e)}")
            return False


class AssignToUserAction(BaseWorkflowAction):
    """Asignar registro a usuario"""
    
    async def execute(self, context: Dict[str, Any]) -> bool:
        """Asignar registro según criterios"""
        try:
            assignment_criteria = self.parameters.get("criteria", {})
            record_id = context.get("record_id")
            
            # Lógica de asignación (round-robin, load-based, etc.)
            assigned_user = await self._determine_assignment(assignment_criteria, context)
            
            # Aquí se actualizaría la asignación en el CRM
            self.logger.info(f"Registro {record_id} asignado a {assigned_user}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error en asignación: {str(e)}")
            return False
    
    async def _determine_assignment(self, criteria: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Determinar usuario para asignación"""
        # Lógica simple: asignación round-robin
        users = criteria.get("users", ["user1", "user2", "user3"])
        current_index = time.time() % len(users)
        return users[int(current_index)]


class ScoreLeadAction(BaseWorkflowAction):
    """Puntuar lead automáticamente"""
    
    async def execute(self, context: Dict[str, Any]) -> bool:
        """Calcular score de lead"""
        try:
            lead_data = context.get("record_data", {})
            scoring_rules = self.parameters.get("scoring_rules", {})
            
            score = 0
            criteria = scoring_rules.get("criteria", {})
            
            # Scoring basado en criterios
            for field, rules in criteria.items():
                field_value = lead_data.get(field)
                if field_value in rules.get("positive_values", []):
                    score += rules.get("positive_score", 0)
                elif field_value in rules.get("negative_values", []):
                    score += rules.get("negative_score", 0)
            
            # Actualizar score en CRM
            self.logger.info(f"Lead score calculado: {score}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error calculando score: {str(e)}")
            return False


class TriggerCampaignAction(BaseWorkflowAction):
    """Activar campaña de marketing"""
    
    async def execute(self, context: Dict[str, Any]) -> bool:
        """Activar campaña automatizada"""
        try:
            campaign_config = self.parameters.get("campaign_config", {})
            contact_data = context.get("record_data", {})
            
            # Aquí se integraría con el sistema de marketing automation
            self.logger.info(f"Campaña activada: {campaign_config.get('name')}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error activando campaña: {str(e)}")
            return False


class WorkflowEngine:
    """Motor de ejecución de workflows"""
    
    def __init__(self):
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.running_executions: Dict[str, WorkflowExecution] = {}
        self.action_handlers = {
            WorkflowAction.CREATE_TASK: CreateTaskAction,
            WorkflowAction.SEND_EMAIL: SendEmailAction,
            WorkflowAction.UPDATE_RECORD: UpdateRecordAction,
            WorkflowAction.ASSIGN_TO_USER: AssignToUserAction,
            WorkflowAction.SCORE_LEAD: ScoreLeadAction,
            WorkflowAction.TRIGGER_CAMPAIGN: TriggerCampaignAction
        }
        self.logger = logging.getLogger("workflow_engine")
    
    def register_workflow(self, workflow: WorkflowDefinition):
        """Registrar workflow"""
        self.workflows[workflow.name] = workflow
        self.logger.info(f"Workflow registrado: {workflow.name}")
    
    async def trigger_workflow(self, trigger: WorkflowTrigger, trigger_data: Dict[str, Any]) -> str:
        """Disparar workflows basado en trigger"""
        execution_id = f"exec_{int(time.time())}_{len(self.running_executions)}"
        
        try:
            # Encontrar workflows que coincidan con el trigger
            matching_workflows = []
            for workflow in self.workflows.values():
                if workflow.trigger == trigger and workflow.active:
                    if await self._evaluate_conditions(workflow.conditions, trigger_data):
                        matching_workflows.append(workflow)
            
            if not matching_workflows:
                self.logger.info("No workflows matching trigger")
                return execution_id
            
            # Crear ejecución
            execution = WorkflowExecution(
                workflow_id=execution_id,
                trigger_data=trigger_data,
                started_at=datetime.now()
            )
            
            self.running_executions[execution_id] = execution
            
            # Ejecutar workflows en paralelo
            tasks = []
            for workflow in matching_workflows:
                task = asyncio.create_task(
                    self._execute_workflow(execution_id, workflow, trigger_data)
                )
                tasks.append(task)
            
            # Esperar a que todos terminen
            await asyncio.gather(*tasks, return_exceptions=True)
            
            return execution_id
            
        except Exception as e:
            self.logger.error(f"Error triggering workflows: {str(e)}")
            return execution_id
    
    async def _evaluate_conditions(self, conditions: List[WorkflowCondition], data: Dict[str, Any]) -> bool:
        """Evaluar condiciones del workflow"""
        if not conditions:
            return True
        
        results = []
        for condition in conditions:
            field_value = self._get_nested_value(data, condition.field)
            result = self._evaluate_condition(condition, field_value)
            results.append(result)
        
        # Aplicar lógica AND/OR (por defecto AND)
        final_result = True
        for result in results:
            final_result = final_result and result
        
        return final_result
    
    def _evaluate_condition(self, condition: WorkflowCondition, value: Any) -> bool:
        """Evaluar condición individual"""
        if condition.operator == "equals":
            return value == condition.value
        elif condition.operator == "not_equals":
            return value != condition.value
        elif condition.operator == "contains":
            return condition.value in str(value)
        elif condition.operator == "greater_than":
            return float(value) > float(condition.value)
        elif condition.operator == "less_than":
            return float(value) < float(condition.value)
        elif condition.operator == "greater_equal":
            return float(value) >= float(condition.value)
        elif condition.operator == "less_equal":
            return float(value) <= float(condition.value)
        else:
            return False
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Obtener valor anidado usando notación de puntos"""
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    
    async def _execute_workflow(self, execution_id: str, workflow: WorkflowDefinition, trigger_data: Dict[str, Any]):
        """Ejecutar workflow específico"""
        try:
            self.logger.info(f"Ejecuting workflow: {workflow.name}")
            
            execution = self.running_executions[execution_id]
            
            for step in workflow.actions:
                try:
                    # Evaluar condición del paso si existe
                    if step.condition and not await self._evaluate_conditions([step.condition], trigger_data):
                        continue
                    
                    # Delay si está especificado
                    if step.delay_seconds:
                        await asyncio.sleep(step.delay_seconds)
                    
                    # Ejecutar acción
                    handler_class = self.action_handlers.get(step.action_type)
                    if not handler_class:
                        self.logger.error(f"Handler no encontrado para acción: {step.action_type}")
                        continue
                    
                    handler = handler_class(step.parameters)
                    success = await handler.execute(trigger_data)
                    
                    if success:
                        execution.actions_completed.append(step.action_type.value)
                        self.logger.info(f"Acción completada: {step.action_type.value}")
                    else:
                        error_msg = f"Error en acción: {step.action_type.value}"
                        execution.errors.append(error_msg)
                        self.logger.error(error_msg)
                    
                except Exception as e:
                    error_msg = f"Error ejecutando paso {step.action_type.value}: {str(e)}"
                    execution.errors.append(error_msg)
                    self.logger.error(error_msg)
            
            # Marcar ejecución como completada
            execution.status = "completed" if not execution.errors else "completed_with_errors"
            self.logger.info(f"Workflow completado: {workflow.name}")
            
        except Exception as e:
            self.logger.error(f"Error ejecutando workflow {workflow.name}: {str(e)}")
            if execution_id in self.running_executions:
                self.running_executions[execution_id].status = "failed"


# Workflows predefinidos
def create_sales_workflows() -> List[WorkflowDefinition]:
    """Crear workflows de ventas predefinidos"""
    workflows = []
    
    # Workflow: Follow-up automático de lead
    lead_follow_up = WorkflowDefinition(
        name="lead_follow_up",
        description="Seguimiento automático de nuevos leads",
        platform="salesforce",
        trigger=WorkflowTrigger.LEAD_CREATED,
        conditions=[
            WorkflowCondition("source", "equals", "website")
        ],
        actions=[
            WorkflowActionStep(
                action_type=WorkflowAction.CREATE_TASK,
                parameters={
                    "subject": "Llamar a lead nuevo",
                    "description": "Seguimiento automático",
                    "due_date": (datetime.now() + timedelta(days=1)).isoformat(),
                    "priority": "high"
                }
            ),
            WorkflowActionStep(
                action_type=WorkflowAction.SEND_EMAIL,
                parameters={
                    "template": "welcome_email",
                    "subject": "¡Gracias por contactarnos!",
                    "variables": {"name": "Lead Name"}
                },
                delay_seconds=300  # 5 minutos
            )
        ]
    )
    
    # Workflow: Notificación de oportunidad importante
    opportunity_notification = WorkflowDefinition(
        name="opportunity_notification",
        description="Notificar oportunidades de alto valor",
        platform="salesforce",
        trigger=WorkflowTrigger.OPPORTUNITY_CREATED,
        conditions=[
            WorkflowCondition("amount", "greater_than", 50000)
        ],
        actions=[
            WorkflowActionStep(
                action_type=WorkflowAction.ASSIGN_TO_USER,
                parameters={
                    "criteria": {"users": ["senior_sales_rep"]}
                }
            ),
            WorkflowActionStep(
                action_type=WorkflowAction.NOTIFY_TEAM,
                parameters={
                    "message": "Nueva oportunidad de alto valor",
                    "channel": "slack"
                }
            )
        ]
    )
    
    # Workflow: Scoring automático de leads
    lead_scoring = WorkflowDefinition(
        name="lead_scoring",
        description="Puntuar leads automáticamente",
        platform="hubspot",
        trigger=WorkflowTrigger.LEAD_CREATED,
        actions=[
            WorkflowActionStep(
                action_type=WorkflowAction.SCORE_LEAD,
                parameters={
                    "scoring_rules": {
                        "criteria": {
                            "company_size": {
                                "positive_values": ["enterprise"],
                                "positive_score": 30,
                                "negative_values": ["small"],
                                "negative_score": 0
                            },
                            "budget": {
                                "positive_values": ["high"],
                                "positive_score": 25,
                                "negative_values": ["low"],
                                "negative_score": 0
                            }
                        }
                    }
                }
            )
        ]
    )
    
    # Workflow: Nurturing sequence
    nurturing_sequence = WorkflowDefinition(
        name="nurturing_sequence",
        description="Secuencia de nutrición de leads",
        platform="hubspot",
        trigger=WorkflowTrigger.LEAD_CREATED,
        conditions=[
            WorkflowCondition("lead_score", "less_than", 50)
        ],
        actions=[
            WorkflowActionStep(
                action_type=WorkflowAction.SEND_EMAIL,
                parameters={
                    "template": "educational_content",
                    "subject": "Recursos útiles para tu empresa",
                    "delay_seconds": 3600  # 1 hora
                }
            ),
            WorkflowActionStep(
                action_type=WorkflowAction.TRIGGER_CAMPAIGN,
                parameters={
                    "campaign_config": {
                        "name": "lead_nurturing",
                        "sequence_id": "sequence_001"
                    }
                },
                delay_seconds=86400  # 24 horas
            )
        ]
    )
    
    workflows.extend([lead_follow_up, opportunity_notification, lead_scoring, nurturing_sequence])
    return workflows


def create_marketing_workflows() -> List[WorkflowDefinition]:
    """Crear workflows de marketing predefinidos"""
    workflows = []
    
    # Workflow: Onboarding de contacto
    contact_onboarding = WorkflowDefinition(
        name="contact_onboarding",
        description="Onboarding automático de nuevos contactos",
        platform="hubspot",
        trigger=WorkflowTrigger.LEAD_CREATED,
        actions=[
            WorkflowActionStep(
                action_type=WorkflowAction.SEND_EMAIL,
                parameters={
                    "template": "welcome_series",
                    "subject": "¡Bienvenido a nuestra comunidad!"
                }
            ),
            WorkflowActionStep(
                action_type=WorkflowAction.TRIGGER_CAMPAIGN,
                parameters={
                    "campaign_config": {
                        "name": "welcome_series",
                        "sequence": ["email_1", "email_2", "email_3"]
                    }
                }
            )
        ]
    )
    
    workflows.append(contact_onboarding)
    return workflows


def create_pipeline_workflows() -> List[WorkflowDefinition]:
    """Crear workflows de pipeline predefinidos"""
    workflows = []
    
    # Workflow: Actualización de stage en Pipedrive
    stage_update_follow_up = WorkflowDefinition(
        name="stage_update_follow_up",
        description="Seguimiento cuando deal cambia de etapa",
        platform="pipedrive",
        trigger=WorkflowTrigger.OPPORTUNITY_STAGE_CHANGED,
        actions=[
            WorkflowActionStep(
                action_type=WorkflowAction.CREATE_TASK,
                parameters={
                    "subject": "Seguimiento post cambio de etapa",
                    "description": "Actividad automática de seguimiento",
                    "due_date": (datetime.now() + timedelta(hours=2)).isoformat()
                }
            ),
            WorkflowActionStep(
                action_type=WorkflowAction.UPDATE_RECORD,
                parameters={
                    "fields": {
                        "last_stage_change": datetime.now().isoformat(),
                        "stage_change_reason": "automatic_follow_up"
                    }
                }
            )
        ]
    )
    
    workflows.append(stage_update_follow_up)
    return workflows


# Manager de workflows
class WorkflowManager:
    """Gestor principal de workflows"""
    
    def __init__(self):
        self.engine = WorkflowEngine()
        self.logger = logging.getLogger("workflow_manager")
    
    async def initialize_default_workflows(self):
        """Inicializar workflows por defecto"""
        all_workflows = []
        all_workflows.extend(create_sales_workflows())
        all_workflows.extend(create_marketing_workflows())
        all_workflows.extend(create_pipeline_workflows())
        
        for workflow in all_workflows:
            self.engine.register_workflow(workflow)
        
        self.logger.info(f"Inicializados {len(all_workflows)} workflows")
    
    async def trigger_lead_created(self, lead_data: Dict[str, Any]):
        """Trigger: Lead creado"""
        execution_id = await self.engine.trigger_workflow(
            WorkflowTrigger.LEAD_CREATED, 
            lead_data
        )
        return execution_id
    
    async def trigger_opportunity_created(self, opportunity_data: Dict[str, Any]):
        """Trigger: Oportunidad creada"""
        execution_id = await self.engine.trigger_workflow(
            WorkflowTrigger.OPPORTUNITY_CREATED,
            opportunity_data
        )
        return execution_id
    
    async def trigger_stage_changed(self, record_data: Dict[str, Any]):
        """Trigger: Etapa cambiada"""
        execution_id = await self.engine.trigger_workflow(
            WorkflowTrigger.OPPORTUNITY_STAGE_CHANGED,
            record_data
        )
        return execution_id
    
    def get_workflow_status(self, execution_id: str) -> Dict[str, Any]:
        """Obtener estado de ejecución de workflow"""
        if execution_id not in self.engine.running_executions:
            return {"error": "Execution not found"}
        
        execution = self.engine.running_executions[execution_id]
        return {
            "execution_id": execution_id,
            "status": execution.status,
            "started_at": execution.started_at.isoformat(),
            "actions_completed": execution.actions_completed,
            "errors": execution.errors
        }


# Ejemplo de uso
async def demo_workflows():
    """Demostración de workflows"""
    manager = WorkflowManager()
    await manager.initialize_default_workflows()
    
    # Simular creación de lead
    lead_data = {
        "id": "lead_123",
        "source": "website",
        "name": "Juan Pérez",
        "email": "juan@example.com",
        "company": "Tech Corp",
        "budget": "high",
        "lead_score": 0
    }
    
    # Trigger workflow
    execution_id = await manager.trigger_lead_created(lead_data)
    print(f"Workflow triggered: {execution_id}")
    
    # Esperar un poco y verificar estado
    await asyncio.sleep(2)
    status = manager.get_workflow_status(execution_id)
    print(f"Workflow status: {json.dumps(status, indent=2, default=str)}")


if __name__ == "__main__":
    asyncio.run(demo_workflows())