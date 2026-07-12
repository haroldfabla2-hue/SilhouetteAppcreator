"""
API Endpoints y Webhooks - Configuración REST API para Sistemas CRM
Endpoints unificados para Salesforce, HubSpot, Pipedrive, Zoho CRM
"""

import asyncio
import logging
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import aiohttp
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel


class EndpointType(Enum):
    """Tipos de endpoints"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    BULK = "bulk"
    WEBHOOK = "webhook"
    SYNC = "sync"


@dataclass
class APIEndpoint:
    """Configuración de endpoint API"""
    path: str
    method: str
    platform: str
    entity_type: str
    required_fields: List[str]
    optional_fields: List[str]
    rate_limit: int  # requests per minute
    timeout: int  # seconds


@dataclass
class WebhookEndpoint:
    """Configuración de webhook"""
    platform: str
    events: List[str]
    signature_header: str
    secret: str
    retry_policy: Dict[str, int]


# Configuración de endpoints por plataforma
CRM_API_ENDPOINTS = {
    "salesforce": {
        "leads": {
            "create": APIEndpoint(
                path="/api/v1/crm/salesforce/leads",
                method="POST",
                platform="salesforce",
                entity_type="lead",
                required_fields=["FirstName", "LastName", "Company"],
                optional_fields=["Email", "Phone", "Title", "Website"],
                rate_limit=100,
                timeout=30
            ),
            "get": APIEndpoint(
                path="/api/v1/crm/salesforce/leads/{lead_id}",
                method="GET",
                platform="salesforce",
                entity_type="lead",
                required_fields=["lead_id"],
                optional_fields=[],
                rate_limit=200,
                timeout=15
            ),
            "list": APIEndpoint(
                path="/api/v1/crm/salesforce/leads",
                method="GET",
                platform="salesforce",
                entity_type="lead",
                required_fields=[],
                optional_fields=["limit", "offset", "filter"],
                rate_limit=100,
                timeout=20
            )
        },
        "opportunities": {
            "create": APIEndpoint(
                path="/api/v1/crm/salesforce/opportunities",
                method="POST",
                platform="salesforce",
                entity_type="opportunity",
                required_fields=["Name", "StageName", "CloseDate"],
                optional_fields=["Amount", "Probability", "Description"],
                rate_limit=100,
                timeout=30
            ),
            "update": APIEndpoint(
                path="/api/v1/crm/salesforce/opportunities/{opp_id}",
                method="PUT",
                platform="salesforce",
                entity_type="opportunity",
                required_fields=["opp_id"],
                optional_fields=["StageName", "Amount", "CloseDate"],
                rate_limit=100,
                timeout=20
            )
        },
        "accounts": {
            "create": APIEndpoint(
                path="/api/v1/crm/salesforce/accounts",
                method="POST",
                platform="salesforce",
                entity_type="account",
                required_fields=["Name"],
                optional_fields=["Phone", "Website", "Industry", "BillingAddress"],
                rate_limit=100,
                timeout=30
            )
        }
    },
    "hubspot": {
        "contacts": {
            "create": APIEndpoint(
                path="/api/v1/crm/hubspot/contacts",
                method="POST",
                platform="hubspot",
                entity_type="contact",
                required_fields=["email"],
                optional_fields=["firstname", "lastname", "phone", "company"],
                rate_limit=100,
                timeout=30
            ),
            "list": APIEndpoint(
                path="/api/v1/crm/hubspot/contacts",
                method="GET",
                platform="hubspot",
                entity_type="contact",
                required_fields=[],
                optional_fields=["limit", "offset", "property"],
                rate_limit=100,
                timeout=20
            )
        },
        "deals": {
            "create": APIEndpoint(
                path="/api/v1/crm/hubspot/deals",
                method="POST",
                platform="hubspot",
                entity_type="deal",
                required_fields=["dealname", "amount"],
                optional_fields=["closedate", "dealstage", "pipeline"],
                rate_limit=100,
                timeout=30
            )
        },
        "companies": {
            "create": APIEndpoint(
                path="/api/v1/crm/hubspot/companies",
                method="POST",
                platform="hubspot",
                entity_type="company",
                required_fields=["name"],
                optional_fields=["domain", "industry", "phone"],
                rate_limit=100,
                timeout=30
            )
        }
    },
    "pipedrive": {
        "persons": {
            "create": APIEndpoint(
                path="/api/v1/crm/pipedrive/persons",
                method="POST",
                platform="pipedrive",
                entity_type="person",
                required_fields=["name"],
                optional_fields=["email", "phone", "organization_id"],
                rate_limit=100,
                timeout=30
            ),
            "get": APIEndpoint(
                path="/api/v1/crm/pipedrive/persons/{person_id}",
                method="GET",
                platform="pipedrive",
                entity_type="person",
                required_fields=["person_id"],
                optional_fields=[],
                rate_limit=200,
                timeout=15
            )
        },
        "deals": {
            "create": APIEndpoint(
                path="/api/v1/crm/pipedrive/deals",
                method="POST",
                platform="pipedrive",
                entity_type="deal",
                required_fields=["title", "value", "currency"],
                optional_fields=["person_id", "organization_id", "pipeline_id"],
                rate_limit=100,
                timeout=30
            ),
            "update_stage": APIEndpoint(
                path="/api/v1/crm/pipedrive/deals/{deal_id}/stage",
                method="PUT",
                platform="pipedrive",
                entity_type="deal",
                required_fields=["deal_id", "stage_id"],
                optional_fields=[],
                rate_limit=100,
                timeout=20
            )
        },
        "organizations": {
            "create": APIEndpoint(
                path="/api/v1/crm/pipedrive/organizations",
                method="POST",
                platform="pipedrive",
                entity_type="organization",
                required_fields=["name"],
                optional_fields=["people_count", "cc_email", "address"],
                rate_limit=100,
                timeout=30
            )
        }
    },
    "zoho": {
        "leads": {
            "create": APIEndpoint(
                path="/api/v1/crm/zoho/leads",
                method="POST",
                platform="zoho",
                entity_type="lead",
                required_fields=["Last_Name", "Company"],
                optional_fields=["First_Name", "Email", "Phone", "Website"],
                rate_limit=100,
                timeout=30
            )
        },
        "potentials": {
            "create": APIEndpoint(
                path="/api/v1/crm/zoho/potentials",
                method="POST",
                platform="zoho",
                entity_type="potential",
                required_fields=["Potential_Name", "Stage"],
                optional_fields=["Amount", "Closing_Date", "Probability"],
                rate_limit=100,
                timeout=30
            )
        },
        "accounts": {
            "create": APIEndpoint(
                path="/api/v1/crm/zoho/accounts",
                method="POST",
                platform="zoho",
                entity_type="account",
                required_fields=["Account_Name"],
                optional_fields=["Website", "Phone", "Industry", "Billing_City"],
                rate_limit=100,
                timeout=30
            )
        }
    }
}

# Configuración de webhooks por plataforma
CRM_WEBHOOKS = {
    "salesforce": WebhookEndpoint(
        platform="salesforce",
        events=[
            "lead.created", "lead.updated", "lead.deleted",
            "opportunity.created", "opportunity.updated", "opportunity.stage_changed",
            "account.created", "account.updated"
        ],
        signature_header="X-Salesforce-Signature",
        secret="your_salesforce_webhook_secret",
        retry_policy={"max_retries": 3, "backoff_factor": 1.5}
    ),
    "hubspot": WebhookEndpoint(
        platform="hubspot",
        events=[
            "contact.creation", "contact.propertyChange", "contact.deletion",
            "deal.creation", "deal.propertyChange", "deal.stageChange",
            "company.creation", "company.propertyChange"
        ],
        signature_header="X-HubSpot-Signature",
        secret="your_hubspot_webhook_secret",
        retry_policy={"max_retries": 5, "backoff_factor": 2.0}
    ),
    "pipedrive": WebhookEndpoint(
        platform="pipedrive",
        events=[
            "deal.added", "deal.updated", "deal.deleted",
            "person.added", "person.updated", "person.deleted",
            "organization.added", "organization.updated"
        ],
        signature_header="X-Pipedrive-Signature",
        secret="your_pipedrive_webhook_secret",
        retry_policy={"max_retries": 3, "backoff_factor": 1.0}
    ),
    "zoho": WebhookEndpoint(
        platform="zoho",
        events=[
            "Leads.add", "Leads.edit", "Leads.convert", "Leads.delete",
            "Potentials.add", "Potentials.edit", "Potentials.stageChange", "Potentials.close",
            "Accounts.add", "Accounts.edit", "Accounts.delete"
        ],
        signature_header="X-Zoho-Signature",
        secret="your_zoho_webhook_secret",
        retry_policy={"max_retries": 3, "backoff_factor": 1.2}
    )
}


# Modelos Pydantic para validación de datos
class LeadCreateRequest(BaseModel):
    """Request para crear lead"""
    platform: str
    first_name: Optional[str] = None
    last_name: str
    company: str
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    website: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "platform": "salesforce",
                "first_name": "Juan",
                "last_name": "Pérez",
                "company": "Empresa ABC",
                "email": "juan.perez@empresa.com",
                "phone": "+34 123 456 789",
                "title": "Director de Ventas",
                "website": "https://empresa.com"
            }
        }


class OpportunityCreateRequest(BaseModel):
    """Request para crear oportunidad"""
    platform: str
    name: str
    stage: str
    amount: float
    close_date: str
    description: Optional[str] = None
    probability: Optional[float] = None
    account_id: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "platform": "hubspot",
                "name": "Venta Licencia Software",
                "stage": "qualified",
                "amount": 50000.0,
                "close_date": "2025-12-31",
                "description": "Venta de licencia anual",
                "probability": 75.0
            }
        }


class ContactCreateRequest(BaseModel):
    """Request para crear contacto"""
    platform: str
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "platform": "pipedrive",
                "name": "María García",
                "email": "maria.garcia@empresa.com",
                "phone": "+34 987 654 321",
                "company": "Empresa XYZ",
                "title": "CTO"
            }
        }


class SyncRequest(BaseModel):
    """Request para sincronización"""
    source_platform: str
    target_platform: str
    entity_type: str
    field_mappings: Dict[str, str]
    filters: Optional[Dict[str, Any]] = None
    batch_size: Optional[int] = 100
    
    class Config:
        schema_extra = {
            "example": {
                "source_platform": "salesforce",
                "target_platform": "hubspot",
                "entity_type": "lead",
                "field_mappings": {
                    "FirstName": "firstname",
                    "LastName": "lastname",
                    "Company": "company",
                    "Email": "email"
                },
                "filters": {"created_after": "2025-01-01"},
                "batch_size": 50
            }
        }


class WebhookPayload(BaseModel):
    """Payload de webhook"""
    platform: str
    event_type: str
    record_id: str
    record_data: Dict[str, Any]
    timestamp: datetime
    signature: Optional[str] = None


# FastAPI Application
app = FastAPI(
    title="CRM Integration API",
    description="API unificada para integración con sistemas CRM empresariales",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

security = HTTPBearer()

# Rate limiting storage (en producción usar Redis)
rate_limits = {}
webhook_queues = []


async def verify_rate_limit(client_id: str, endpoint: APIEndpoint) -> bool:
    """Verificar límite de tasa para endpoint"""
    current_minute = int(asyncio.get_event_loop().time() // 60)
    key = f"{client_id}:{endpoint.path}:{current_minute}"
    
    if key not in rate_limits:
        rate_limits[key] = 0
    
    rate_limits[key] += 1
    
    return rate_limits[key] <= endpoint.rate_limit


async def verify_webhook_signature(request: Request, webhook_config: WebhookEndpoint) -> bool:
    """Verificar firma de webhook"""
    signature = request.headers.get(webhook_config.signature_header)
    if not signature:
        return False
    
    # Obtener cuerpo de la solicitud
    body = await request.body()
    
    # Calcular firma esperada
    expected_signature = hmac.new(
        webhook_config.secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


# Endpoints principales de la API
@app.post("/api/v1/crm/{platform}/leads")
async def create_lead(
    platform: str,
    lead_request: LeadCreateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Crear lead en plataforma CRM específica"""
    try:
        # Verificar que la plataforma esté soportada
        if platform not in CRM_API_ENDPOINTS:
            raise HTTPException(status_code=404, detail=f"Plataforma {platform} no soportada")
        
        # Verificar rate limit
        endpoint = CRM_API_ENDPOINTS[platform]["leads"]["create"]
        if not await verify_rate_limit("api_user", endpoint):
            raise HTTPException(status_code=429, detail="Rate limit excedido")
        
        # Validar campos requeridos
        required_fields = endpoint.required_fields
        missing_fields = []
        
        if platform == "salesforce":
            required_data = {
                "FirstName": lead_request.first_name,
                "LastName": lead_request.last_name,
                "Company": lead_request.company
            }
        elif platform == "hubspot":
            required_data = {
                "email": lead_request.email or lead_request.last_name
            }
        
        for field in required_fields:
            if field not in required_data or not required_data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            raise HTTPException(status_code=400, detail=f"Campos requeridos faltantes: {missing_fields}")
        
        # Aquí iría la lógica de integración real
        # Por ahora simulamos una respuesta exitosa
        return {
            "success": True,
            "platform": platform,
            "record_id": f"crm_{platform}_lead_{int(asyncio.get_event_loop().time())}",
            "data": required_data,
            "created_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@app.get("/api/v1/crm/{platform}/leads")
async def list_leads(
    platform: str,
    limit: int = 100,
    offset: int = 0,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Listar leads de plataforma CRM"""
    try:
        if platform not in CRM_API_ENDPOINTS:
            raise HTTPException(status_code=404, detail=f"Plataforma {platform} no soportada")
        
        endpoint = CRM_API_ENDPOINTS[platform]["leads"]["list"]
        if not await verify_rate_limit("api_user", endpoint):
            raise HTTPException(status_code=429, detail="Rate limit excedido")
        
        # Simular respuesta de leads
        return {
            "success": True,
            "platform": platform,
            "total": 150,
            "offset": offset,
            "limit": limit,
            "leads": [
                {
                    "id": f"lead_{i}",
                    "first_name": f"Nombre{i}",
                    "last_name": f"Apellido{i}",
                    "company": f"Empresa{i}",
                    "email": f"email{i}@empresa.com",
                    "created_at": (datetime.now() - timedelta(days=i)).isoformat()
                }
                for i in range(min(limit, 10))
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@app.post("/api/v1/crm/{platform}/opportunities")
async def create_opportunity(
    platform: str,
    opportunity_request: OpportunityCreateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Crear oportunidad en plataforma CRM específica"""
    try:
        if platform not in CRM_API_ENDPOINTS:
            raise HTTPException(status_code=404, detail=f"Plataforma {platform} no soportada")
        
        endpoint = CRM_API_ENDPOINTS[platform]["opportunities"]["create"]
        if not await verify_rate_limit("api_user", endpoint):
            raise HTTPException(status_code=429, detail="Rate limit excedido")
        
        # Validar campos requeridos
        opportunity_data = {
            "name": opportunity_request.name,
            "stage": opportunity_request.stage,
            "amount": opportunity_request.amount,
            "close_date": opportunity_request.close_date,
            "description": opportunity_request.description,
            "probability": opportunity_request.probability
        }
        
        return {
            "success": True,
            "platform": platform,
            "record_id": f"crm_{platform}_opp_{int(asyncio.get_event_loop().time())}",
            "data": opportunity_data,
            "created_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@app.post("/api/v1/crm/sync")
async def sync_data(
    sync_request: SyncRequest,
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Iniciar sincronización entre plataformas CRM"""
    try:
        sync_job_id = f"sync_{sync_request.source_platform}_{sync_request.target_platform}_{int(asyncio.get_event_loop().time())}"
        
        # Añadir tarea en background
        background_tasks.add_task(
            execute_sync_job,
            sync_job_id,
            sync_request
        )
        
        return {
            "success": True,
            "sync_job_id": sync_job_id,
            "status": "queued",
            "message": "Trabajo de sincronización agregado a la cola"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


async def execute_sync_job(sync_job_id: str, sync_request: SyncRequest):
    """Ejecutar trabajo de sincronización en background"""
    try:
        # Simular proceso de sincronización
        await asyncio.sleep(2)  # Simular trabajo
        
        # Aquí iría la lógica real de sincronización
        # usando el CRMIntegrationManager
        
        print(f"Trabajo de sincronización {sync_job_id} completado")
        
    except Exception as e:
        print(f"Error en trabajo de sincronización {sync_job_id}: {str(e)}")


# Webhooks endpoints
@app.post("/webhooks/{platform}")
async def handle_webhook(
    platform: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """Recibir webhook de plataforma CRM"""
    try:
        if platform not in CRM_WEBHOOKS:
            raise HTTPException(status_code=404, detail=f"Webhook para {platform} no configurado")
        
        webhook_config = CRM_WEBHOOKS[platform]
        
        # Verificar firma del webhook
        if not await verify_webhook_signature(request, webhook_config):
            raise HTTPException(status_code=401, detail="Firma de webhook inválida")
        
        # Obtener payload
        payload = await request.json()
        
        # Procesar webhook en background
        background_tasks.add_task(
            process_webhook,
            platform,
            payload,
            webhook_config
        )
        
        return {"success": True, "message": "Webhook recibido correctamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando webhook: {str(e)}")


async def process_webhook(platform: str, payload: Dict[str, Any], webhook_config: WebhookEndpoint):
    """Procesar payload de webhook"""
    try:
        webhook_data = {
            "platform": platform,
            "event_type": payload.get("event_type", "unknown"),
            "record_id": payload.get("record_id"),
            "record_data": payload.get("data", {}),
            "timestamp": datetime.now().isoformat(),
            "processed": False
        }
        
        # Añadir a cola de procesamiento
        webhook_queues.append(webhook_data)
        
        # Procesar según tipo de evento
        if "lead" in webhook_data["event_type"]:
            await process_lead_webhook(platform, webhook_data)
        elif "opportunity" in webhook_data["event_type"] or "deal" in webhook_data["event_type"]:
            await process_opportunity_webhook(platform, webhook_data)
        elif "account" in webhook_data["event_type"] or "company" in webhook_data["event_type"]:
            await process_account_webhook(platform, webhook_data)
        
        # Marcar como procesado
        webhook_data["processed"] = True
        
    except Exception as e:
        print(f"Error procesando webhook de {platform}: {str(e)}")


async def process_lead_webhook(platform: str, webhook_data: Dict[str, Any]):
    """Procesar webhook de lead"""
    event_type = webhook_data["event_type"]
    record_data = webhook_data["record_data"]
    
    if "created" in event_type or "added" in event_type:
        print(f"Nuevo lead creado en {platform}: {record_data.get('id')}")
    elif "updated" in event_type or "edited" in event_type:
        print(f"Lead actualizado en {platform}: {record_data.get('id')}")
    elif "deleted" in event_type:
        print(f"Lead eliminado en {platform}: {webhook_data['record_id']}")


async def process_opportunity_webhook(platform: str, webhook_data: Dict[str, Any]):
    """Procesar webhook de oportunidad"""
    event_type = webhook_data["event_type"]
    record_data = webhook_data["record_data"]
    
    if "created" in event_type or "added" in event_type:
        print(f"Nueva oportunidad creada en {platform}: {record_data.get('id')}")
    elif "stage" in event_type:
        print(f"Etapa de oportunidad cambiada en {platform}: {record_data.get('id')}")
    elif "closed" in event_type or "won" in event_type:
        print(f"Oportunidad cerrada en {platform}: {record_data.get('id')}")


async def process_account_webhook(platform: str, webhook_data: Dict[str, Any]):
    """Procesar webhook de cuenta"""
    event_type = webhook_data["event_type"]
    record_data = webhook_data["record_data"]
    
    if "created" in event_type or "added" in event_type:
        print(f"Nueva cuenta creada en {platform}: {record_data.get('id')}")
    elif "updated" in event_type or "edited" in event_type:
        print(f"Cuenta actualizada en {platform}: {record_data.get('id')}")


# Endpoints de estado y monitoreo
@app.get("/health")
async def health_check():
    """Verificación de salud del sistema"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "crm_integrations": "operational",
            "webhooks": "operational",
            "sync_engine": "operational"
        }
    }


@app.get("/api/v1/crm/status")
async def crm_status():
    """Estado de integraciones CRM"""
    return {
        "platforms": {
            "salesforce": {"status": "connected", "last_sync": datetime.now().isoformat()},
            "hubspot": {"status": "connected", "last_sync": datetime.now().isoformat()},
            "pipedrive": {"status": "connected", "last_sync": datetime.now().isoformat()},
            "zoho": {"status": "connected", "last_sync": datetime.now().isoformat()}
        },
        "total_webhooks_processed": len(webhook_queues),
        "sync_jobs_queued": 0
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api_endpoints:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )