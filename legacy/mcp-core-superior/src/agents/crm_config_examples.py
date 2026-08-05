"""
Configuración de Ejemplo para Sistemas CRM
Configuraciones predefinidas para diferentes escenarios empresariales
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Any, Optional


# Configuración de Credenciales por Entorno
CRM_CREDENTIALS_CONFIG = {
    "development": {
        "salesforce": {
            "client_id": "YOUR_DEV_SALESFORCE_CLIENT_ID",
            "client_secret": "YOUR_DEV_SALESFORCE_CLIENT_SECRET",
            "instance_url": "https://your-dev-instance.salesforce.com",
            "username": "dev_user@company.com"
        },
        "hubspot": {
            "client_id": "YOUR_DEV_HUBSPOT_CLIENT_ID",
            "client_secret": "YOUR_DEV_HUBSPOT_CLIENT_SECRET",
            "api_key": "YOUR_DEV_HUBSPOT_API_KEY"
        },
        "pipedrive": {
            "api_key": "YOUR_DEV_PIPEDRIVE_API_KEY",
            "username": "dev_user"
        },
        "zoho": {
            "client_id": "YOUR_DEV_ZOHO_CLIENT_ID",
            "client_secret": "YOUR_DEV_ZOHO_CLIENT_SECRET"
        }
    },
    "staging": {
        "salesforce": {
            "client_id": "YOUR_STAGING_SALESFORCE_CLIENT_ID",
            "client_secret": "YOUR_STAGING_SALESFORCE_CLIENT_SECRET",
            "instance_url": "https://your-staging-instance.salesforce.com",
            "username": "staging_user@company.com"
        },
        "hubspot": {
            "client_id": "YOUR_STAGING_HUBSPOT_CLIENT_ID",
            "client_secret": "YOUR_STAGING_HUBSPOT_CLIENT_SECRET",
            "api_key": "YOUR_STAGING_HUBSPOT_API_KEY"
        },
        "pipedrive": {
            "api_key": "YOUR_STAGING_PIPEDRIVE_API_KEY",
            "username": "staging_user"
        },
        "zoho": {
            "client_id": "YOUR_STAGING_ZOHO_CLIENT_ID",
            "client_secret": "YOUR_STAGING_ZOHO_CLIENT_SECRET"
        }
    },
    "production": {
        "salesforce": {
            "client_id": "YOUR_PROD_SALESFORCE_CLIENT_ID",
            "client_secret": "YOUR_PROD_SALESFORCE_CLIENT_SECRET",
            "instance_url": "https://your-prod-instance.salesforce.com",
            "username": "prod_user@company.com"
        },
        "hubspot": {
            "client_id": "YOUR_PROD_HUBSPOT_CLIENT_ID",
            "client_secret": "YOUR_PROD_HUBSPOT_CLIENT_SECRET",
            "api_key": "YOUR_PROD_HUBSPOT_API_KEY"
        },
        "pipedrive": {
            "api_key": "YOUR_PROD_PIPEDRIVE_API_KEY",
            "username": "prod_user"
        },
        "zoho": {
            "client_id": "YOUR_PROD_ZOHO_CLIENT_ID",
            "client_secret": "YOUR_PROD_ZOHO_CLIENT_SECRET"
        }
    }
}


# Variables de Entorno Requeridas
REQUIRED_ENV_VARS = {
    "CRM_ENCRYPTION_KEY": "Clave de encriptación de 32 caracteres",
    "CRM_JWT_SECRET": "Secreto JWT para tokens de autenticación",
    "REDIS_URL": "URL de conexión Redis (opcional)",
    "SALESFORCE_CLIENT_ID": "ID de cliente de Salesforce",
    "SALESFORCE_CLIENT_SECRET": "Secreto de cliente de Salesforce",
    "HUBSPOT_CLIENT_ID": "ID de cliente de HubSpot",
    "HUBSPOT_CLIENT_SECRET": "Secreto de cliente de HubSpot",
    "PIPEDRIVE_API_KEY": "API Key de Pipedrive",
    "ZOHO_CLIENT_ID": "ID de cliente de Zoho CRM",
    "ZOHO_CLIENT_SECRET": "Secreto de cliente de Zoho CRM"
}


# Configuraciones de Mapeo de Campos
FIELD_MAPPINGS = {
    "lead": {
        "salesforce": {
            "FirstName": "first_name",
            "LastName": "last_name", 
            "Company": "company",
            "Email": "email",
            "Phone": "phone",
            "Title": "title",
            "Website": "website",
            "Industry": "industry",
            "NumberOfEmployees": "company_size"
        },
        "hubspot": {
            "firstname": "first_name",
            "lastname": "last_name",
            "company": "company", 
            "email": "email",
            "phone": "phone",
            "jobtitle": "title",
            "website": "website",
            "industry": "industry",
            "numemployees": "company_size"
        },
        "pipedrive": {
            "name": "full_name",
            "email": "email",
            "phone": "phone"
        },
        "zoho": {
            "First_Name": "first_name",
            "Last_Name": "last_name",
            "Company": "company",
            "Email": "email",
            "Phone": "phone",
            "Designation": "title",
            "Website": "website",
            "Industry": "industry"
        }
    },
    "opportunity": {
        "salesforce": {
            "Name": "name",
            "Amount": "amount",
            "StageName": "stage",
            "CloseDate": "close_date",
            "Description": "description",
            "Probability": "probability",
            "LeadSource": "source"
        },
        "hubspot": {
            "dealname": "name",
            "amount": "amount",
            "dealstage": "stage",
            "closedate": "close_date",
            "description": "description",
            "hs_probability_to_close": "probability",
            "hs_lead_status": "source"
        },
        "pipedrive": {
            "title": "name",
            "value": "amount",
            "currency": "currency",
            "status": "stage",
            "expected_close_date": "close_date"
        },
        "zoho": {
            "Potential_Name": "name",
            "Amount": "amount",
            "Stage": "stage",
            "Closing_Date": "close_date",
            "Description": "description",
            "Probability": "probability"
        }
    }
}


# Configuraciones de Webhooks por Plataforma
WEBHOOK_CONFIGS = {
    "salesforce": {
        "events": [
            "lead.created",
            "lead.updated", 
            "lead.deleted",
            "opportunity.created",
            "opportunity.updated",
            "opportunity.stage_changed",
            "account.created",
            "account.updated"
        ],
        "platform_events": [
            "ChangeEvent",  # Para Change Data Capture
            "LeadChangeEvent",
            "OpportunityChangeEvent"
        ],
        "webhook_url": "https://your-domain.com/webhooks/salesforce",
        "secret": "your_salesforce_webhook_secret"
    },
    "hubspot": {
        "events": [
            "contact.creation",
            "contact.propertyChange",
            "contact.deletion",
            "deal.creation", 
            "deal.propertyChange",
            "deal.stageChange",
            "company.creation",
            "company.propertyChange"
        ],
        "webhook_url": "https://your-domain.com/webhooks/hubspot",
        "secret": "your_hubspot_webhook_secret",
        "subscription_details": {
            "subscription_details": [
                {
                    "subscription_type": "contact.propertyChange",
                    "property_name": "email"
                },
                {
                    "subscription_type": "deal.propertyChange", 
                    "property_name": "dealstage"
                }
            ]
        }
    },
    "pipedrive": {
        "events": [
            "deal.added",
            "deal.updated",
            "deal.deleted",
            "person.added",
            "person.updated", 
            "person.deleted",
            "organization.added",
            "organization.updated"
        ],
        "webhook_url": "https://your-domain.com/webhooks/pipedrive",
        "secret": "your_pipedrive_webhook_secret"
    },
    "zoho": {
        "events": [
            "Leads.add",
            "Leads.edit",
            "Leads.convert",
            "Leads.delete",
            "Potentials.add",
            "Potentials.edit", 
            "Potentials.stageChange",
            "Potentials.close",
            "Accounts.add",
            "Accounts.edit",
            "Accounts.delete"
        ],
        "webhook_url": "https://your-domain.com/webhooks/zoho",
        "secret": "your_zoho_webhook_secret"
    }
}


# Configuraciones de Rate Limiting
RATE_LIMITS = {
    "salesforce": {
        "daily_limit": 15000,  # requests per day
        "hourly_limit": 3600,  # requests per hour
        "per_second_limit": 25  # requests per second
    },
    "hubspot": {
        "daily_limit": 10000,
        "hourly_limit": 1000,
        "per_second_limit": 10
    },
    "pipedrive": {
        "daily_limit": 5000,
        "hourly_limit": 500,
        "per_second_limit": 5
    },
    "zoho": {
        "daily_limit": 7000,
        "hourly_limit": 700,
        "per_second_limit": 7
    }
}


# Configuraciones de Sincronización
SYNC_CONFIGS = {
    "default": {
        "batch_size": 100,
        "sync_interval_minutes": 15,
        "conflict_resolution": "source_wins",
        "retry_attempts": 3,
        "retry_delay_seconds": 5,
        "incremental_sync": True,
        "field_validation": True,
        "log_sync_operations": True
    },
    "aggressive": {
        "batch_size": 50,
        "sync_interval_minutes": 5,
        "conflict_resolution": "target_wins",
        "retry_attempts": 5,
        "retry_delay_seconds": 2,
        "incremental_sync": True,
        "field_validation": True,
        "log_sync_operations": True
    },
    "conservative": {
        "batch_size": 200,
        "sync_interval_minutes": 60,
        "conflict_resolution": "manual",
        "retry_attempts": 1,
        "retry_delay_seconds": 30,
        "incremental_sync": False,
        "field_validation": True,
        "log_sync_operations": True
    }
}


# Configuraciones de Workflows Predefinidos
WORKFLOW_CONFIGS = {
    "lead_qualification": {
        "name": "Lead Qualification Workflow",
        "trigger": "lead_created",
        "conditions": [
            {
                "field": "email",
                "operator": "not_empty"
            },
            {
                "field": "company",
                "operator": "not_empty"
            }
        ],
        "actions": [
            {
                "type": "assign_to_user",
                "parameters": {
                    "assignment_method": "round_robin",
                    "users": ["sales_rep_1", "sales_rep_2", "sales_rep_3"]
                }
            },
            {
                "type": "create_task",
                "parameters": {
                    "subject": "Llamar a lead nuevo",
                    "due_date_offset_hours": 24,
                    "priority": "high"
                }
            },
            {
                "type": "send_email",
                "parameters": {
                    "template": "welcome_email",
                    "delay_minutes": 30
                }
            }
        ]
    },
    "opportunity_follow_up": {
        "name": "Opportunity Follow-up",
        "trigger": "opportunity_stage_changed",
        "conditions": [
            {
                "field": "stage",
                "operator": "equals",
                "value": "Proposal"
            }
        ],
        "actions": [
            {
                "type": "create_task",
                "parameters": {
                    "subject": "Seguimiento de propuesta",
                    "due_date_offset_hours": 48,
                    "priority": "high"
                }
            },
            {
                "type": "notify_team",
                "parameters": {
                    "channel": "slack",
                    "message": "Nueva propuesta enviada"
                }
            }
        ]
    },
    "lead_scoring": {
        "name": "Automatic Lead Scoring",
        "trigger": "lead_updated",
        "conditions": [
            {
                "field": "website_visits",
                "operator": "greater_than",
                "value": 5
            }
        ],
        "actions": [
            {
                "type": "score_lead",
                "parameters": {
                    "scoring_rules": {
                        "website_visits": {
                            "weight": 10,
                            "threshold": 5
                        },
                        "email_opens": {
                            "weight": 5,
                            "threshold": 3
                        },
                        "form_submissions": {
                            "weight": 20,
                            "threshold": 1
                        }
                    }
                }
            }
        ]
    }
}


# Configuraciones de Analytics
ANALYTICS_CONFIGS = {
    "default": {
        "metrics_to_track": [
            "total_leads",
            "qualified_leads", 
            "conversion_rate",
            "average_deal_size",
            "sales_cycle_length",
            "revenue_pipeline"
        ],
        "reporting_frequency": "daily",
        "real_time_metrics": True,
        "dashboards": ["sales_overview", "lead_sources", "pipeline_analysis"]
    },
    "detailed": {
        "metrics_to_track": [
            "total_leads",
            "qualified_leads",
            "conversion_rate",
            "average_deal_size", 
            "sales_cycle_length",
            "revenue_pipeline",
            "lead_source_performance",
            "rep_performance",
            "product_performance",
            "territory_analysis"
        ],
        "reporting_frequency": "hourly",
        "real_time_metrics": True,
        "dashboards": ["sales_overview", "lead_sources", "pipeline_analysis", "rep_performance", "forecasting"]
    }
}


# Templates de Email
EMAIL_TEMPLATES = {
    "welcome_email": {
        "subject": "¡Gracias por contactarnos, {name}!",
        "html_content": """
        <html>
        <body>
            <h2>¡Hola {name}!</h2>
            <p>Gracias por tu interés en nuestros servicios. Nuestro equipo se pondrá en contacto contigo pronto.</p>
            <p>Mientras tanto, puedes:</p>
            <ul>
                <li>Visitar nuestro sitio web: <a href="{website}">{website}</a></li>
                <li>Descargar nuestros recursos: <a href="{resources_url}">Recursos</a></li>
                <li>Programar una demo: <a href="{demo_url}">Agendar Demo</a></li>
            </ul>
            <p>¡Esperamos poder ayudarte!</p>
            <p>Saludos,<br>Equipo de {company_name}</p>
        </body>
        </html>
        """,
        "variables": ["name", "company_name", "website", "resources_url", "demo_url"]
    },
    "follow_up_email": {
        "subject": "Seguimiento de tu consulta - {company_name}",
        "html_content": """
        <html>
        <body>
            <h2>Hola {name}</h2>
            <p>Espero que estés bien. Te escribo para hacer seguimiento a tu consulta sobre {product_or_service}.</p>
            <p>¿Tienes alguna pregunta específica que podamos ayudarte a resolver?</p>
            <p>Estoy disponible para una llamada si prefieres hablar directamente.</p>
            <p>Saludos,<br>{rep_name}</p>
        </body>
        </html>
        """,
        "variables": ["name", "company_name", "product_or_service", "rep_name"]
    },
    "proposal_sent": {
        "subject": "Propuesta enviada - {project_name}",
        "html_content": """
        <html>
        <body>
            <h2>¡Propuesta lista!</h2>
            <p>Hola {name},</p>
            <p>He preparado una propuesta detallada para {project_name} según nuestros últimos comentarios.</p>
            <p>La propuesta incluye:</p>
            <ul>
                <li>Solución propuesta</li>
                <li>Timeline de implementación</li>
                <li>Inversión requerida</li>
                <li>ROI esperado</li>
            </ul>
            <p>Estoy disponible para revisar cualquier punto que necesites aclarar.</p>
            <p>Saludos,<br>{rep_name}</p>
        </body>
        </html>
        """,
        "variables": ["name", "project_name", "rep_name"]
    }
}


def load_credentials_from_env() -> Dict[str, Any]:
    """Cargar credenciales desde variables de entorno"""
    return {
        "salesforce": {
            "client_id": os.getenv("SALESFORCE_CLIENT_ID"),
            "client_secret": os.getenv("SALESFORCE_CLIENT_SECRET"),
            "instance_url": os.getenv("SALESFORCE_INSTANCE_URL"),
            "username": os.getenv("SALESFORCE_USERNAME")
        },
        "hubspot": {
            "client_id": os.getenv("HUBSPOT_CLIENT_ID"),
            "client_secret": os.getenv("HUBSPOT_CLIENT_SECRET"),
            "api_key": os.getenv("HUBSPOT_API_KEY")
        },
        "pipedrive": {
            "api_key": os.getenv("PIPEDRIVE_API_KEY"),
            "username": os.getenv("PIPEDRIVE_USERNAME")
        },
        "zoho": {
            "client_id": os.getenv("ZOHO_CLIENT_ID"),
            "client_secret": os.getenv("ZOHO_CLIENT_SECRET")
        }
    }


def validate_environment():
    """Validar variables de entorno requeridas"""
    missing_vars = []
    
    for var_name, description in REQUIRED_ENV_VARS.items():
        if not os.getenv(var_name):
            missing_vars.append(f"{var_name}: {description}")
    
    if missing_vars:
        raise ValueError(
            "Variables de entorno requeridas faltantes:\n" + 
            "\n".join(f"  - {var}" for var in missing_vars)
        )
    
    return True


def get_config_for_environment(env_name: str = "development") -> Dict[str, Any]:
    """Obtener configuración para entorno específico"""
    if env_name not in CRM_CREDENTIALS_CONFIG:
        raise ValueError(f"Entorno '{env_name}' no configurado")
    
    return {
        "credentials": CRM_CREDENTIALS_CONFIG[env_name],
        "field_mappings": FIELD_MAPPINGS,
        "webhooks": WEBHOOK_CONFIGS,
        "rate_limits": RATE_LIMITS,
        "sync": SYNC_CONFIGS["default"],
        "workflows": WORKFLOW_CONFIGS,
        "analytics": ANALYTICS_CONFIGS["default"],
        "email_templates": EMAIL_TEMPLATES
    }


if __name__ == "__main__":
    # Ejemplo de uso
    print("=== Configuración CRM Empresarial ===")
    
    try:
        # Validar entorno
        validate_environment()
        print("✓ Variables de entorno validadas")
        
        # Cargar credenciales
        creds = load_credentials_from_env()
        print("✓ Credenciales cargadas desde entorno")
        
        # Obtener configuración
        config = get_config_for_environment("development")
        print("✓ Configuración de desarrollo cargada")
        
        print("\nCredenciales disponibles:")
        for platform in creds:
            print(f"  - {platform}: {'✓' if any(creds[platform].values()) else '✗'}")
            
    except ValueError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")