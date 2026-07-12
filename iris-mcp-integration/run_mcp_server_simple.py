#!/usr/bin/env python3
"""
IRIS MCP Server - Versión simplificada para testing
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from fastmcp import FastMCP
except ImportError:
    print("FastMCP no está disponible, instalando...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastmcp"])
    from fastmcp import FastMCP

# Configurar FastMCP
mcp = FastMCP("IRIS MCP Superior")

# Datos simulados
SAMPLE_AGENTS = [
    {
        "id": "sales_agent",
        "name": "Sales Agent",
        "status": "active",
        "tasksCompleted": 156,
        "avgResponseTime": 1.2,
        "tokenUsage": 45200,
        "successRate": 0.94,
        "lastActivity": datetime.now().isoformat(),
        "capabilities": ["lead_qualification", "proposal_generation", "follow_up_automation"]
    },
    {
        "id": "support_agent",
        "name": "Support Agent", 
        "status": "active",
        "tasksCompleted": 89,
        "avgResponseTime": 0.8,
        "tokenUsage": 32400,
        "successRate": 0.96,
        "lastActivity": datetime.now().isoformat(),
        "capabilities": ["ticket_classification", "response_generation", "escalation_management"]
    },
    {
        "id": "consulting_agent",
        "name": "Consulting Agent",
        "status": "active",
        "tasksCompleted": 23,
        "avgResponseTime": 2.1,
        "tokenUsage": 67800,
        "successRate": 0.91,
        "lastActivity": datetime.now().isoformat(),
        "capabilities": ["data_analysis", "report_generation", "insight_generation"]
    }
]

SAMPLE_TEMPLATES = [
    {
        "id": "iris_sales_automation",
        "name": "Sales Automation Template",
        "category": "sales",
        "description": "Automatización completa de procesos de venta",
        "version": "1.0.0",
        "created": datetime.now().isoformat()
    },
    {
        "id": "iris_support_automation", 
        "name": "Support Automation Template",
        "category": "support",
        "description": "Automatización de atención al cliente",
        "version": "1.0.0",
        "created": datetime.now().isoformat()
    },
    {
        "id": "iris_consulting_analysis",
        "name": "Consulting Analysis Template",
        "category": "consulting", 
        "description": "Análisis avanzado para consultoría",
        "version": "1.0.0",
        "created": datetime.now().isoformat()
    }
]

@mcp.tool
def get_iris_agents_status() -> str:
    """Obtener estado actual de todos los agentes IRIS"""
    try:
        result = {
            "timestamp": datetime.now().isoformat(),
            "agents": SAMPLE_AGENTS,
            "summary": {
                "total_agents": len(SAMPLE_AGENTS),
                "active_agents": len([a for a in SAMPLE_AGENTS if a["status"] == "active"]),
                "total_tasks": sum(a["tasksCompleted"] for a in SAMPLE_AGENTS),
                "total_tokens": sum(a["tokenUsage"] for a in SAMPLE_AGENTS),
                "avg_response_time": round(sum(a["avgResponseTime"] for a in SAMPLE_AGENTS) / len(SAMPLE_AGENTS), 2),
                "system_health": "operational"
            }
        }
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Error obteniendo estado de agentes: {str(e)}"}, indent=2)

@mcp.tool
def get_agent_metrics(agent_id: str) -> str:
    """Obtener métricas detalladas de un agente específico"""
    try:
        if agent_id not in [a["id"] for a in SAMPLE_AGENTS]:
            return json.dumps({"error": f"Agente {agent_id} no encontrado"}, indent=2)
        
        agent = next(a for a in SAMPLE_AGENTS if a["id"] == agent_id)
        
        result = {
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "tasks_completed": agent["tasksCompleted"],
                "avg_response_time": agent["avgResponseTime"],
                "token_usage": agent["tokenUsage"],
                "success_rate": agent["successRate"],
                "status": agent["status"],
                "last_activity": agent["lastActivity"]
            }
        }
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Error obteniendo métricas de {agent_id}: {str(e)}"}, indent=2)

@mcp.tool
def deploy_agent(agent_id: str) -> str:
    """Desplegar un agente específico en IRIS"""
    try:
        if agent_id not in [a["id"] for a in SAMPLE_AGENTS]:
            return json.dumps({"error": f"Agente {agent_id} no válido"}, indent=2)
        
        result = {
            "status": "deployed",
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "message": f"Agente {agent_id} desplegado exitosamente",
            "deployment_time": "1.2s",
            "resources_allocated": "2GB RAM, 4 CPU cores"
        }
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Error desplegando {agent_id}: {str(e)}"}, indent=2)

@mcp.tool
def create_template(template_type: str, customizations: Optional[Dict[str, Any]] = None) -> str:
    """Crear un template de automatización para IRIS"""
    try:
        valid_types = ["sales", "support", "consulting", "multiagent", "optimization"]
        if template_type not in valid_types:
            return json.dumps({
                "error": f"Tipo de template '{template_type}' no válido",
                "available_types": valid_types
            }, indent=2)
        
        # Simular creación de template
        template_data = {
            "id": f"iris_{template_type}_automation",
            "name": f"{template_type.title()} Automation Template",
            "category": template_type,
            "description": f"Template de automatización para {template_type}",
            "version": "1.0.0",
            "created": datetime.now().isoformat(),
            "agents_count": 3,
            "capabilities": ["automation", "monitoring", "notifications"],
            "status": "created"
        }
        
        result = {
            "template": template_data,
            "file_path": f"iris_templates/iris_{template_type}_automation.json",
            "message": f"Template {template_type} creado exitosamente",
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Error creando template {template_type}: {str(e)}"}, indent=2)

@mcp.tool
def list_available_templates() -> str:
    """Listar todos los templates disponibles"""
    try:
        templates_info = {
            "message": f"Se encontraron {len(SAMPLE_TEMPLATES)} templates",
            "templates": SAMPLE_TEMPLATES,
            "total": len(SAMPLE_TEMPLATES),
            "categories": list(set(t["category"] for t in SAMPLE_TEMPLATES))
        }
        return json.dumps(templates_info, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Error listando templates: {str(e)}"}, indent=2)

@mcp.tool
def get_system_health() -> str:
    """Verificar salud completa del sistema IRIS"""
    try:
        health_status = {
            "system": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "template_manager": {"status": "operational", "templates_available": len(SAMPLE_TEMPLATES)},
                "notification_manager": {"status": "operational", "channels_configured": 1},
                "agents": {"status": "operational", "total_agents": 3, "active_agents": 3},
                "api_server": {"status": "operational", "port": 8000, "endpoints_available": 9}
            },
            "metrics": {
                "uptime": "99.9%",
                "avg_response_time": "1.4s",
                "last_updated": datetime.now().isoformat()
            }
        }
        return json.dumps(health_status, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Error verificando salud del sistema: {str(e)}"}, indent=2)

@mcp.tool
def send_notification(event_type: str, title: str, message: str, agent_id: Optional[str] = None, level: str = "info") -> str:
    """Enviar notificación a través del sistema multi-canal"""
    try:
        result = {
            "success": True,
            "event_type": event_type,
            "title": title,
            "message": message,
            "agent_id": agent_id,
            "level": level,
            "sent_at": datetime.now().isoformat(),
            "channels_used": ["console"],
            "message": "Notificación enviada exitosamente"
        }
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Error enviando notificación: {str(e)}"}, indent=2)

@mcp.tool
def get_notification_stats() -> str:
    """Obtener estadísticas del sistema de notificaciones"""
    try:
        stats = {
            "total_notifications": 15,
            "successful": 14,
            "failed": 1,
            "success_rate": 0.93,
            "event_type_distribution": {
                "agent_status_change": 8,
                "task_completed": 4,
                "system_alert": 3
            },
            "level_distribution": {
                "info": 10,
                "warning": 3,
                "error": 2
            }
        }
        
        result = {
            "statistics": stats,
            "recent_history": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "event_type": "agent_status_change",
                    "level": "info",
                    "success": True
                }
            ],
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Error obteniendo estadísticas: {str(e)}"}, indent=2)

@mcp.prompt
def iris_agent_management_guide() -> str:
    """Generar guía para gestión de agentes IRIS"""
    return """
# Guía de Gestión de Agentes IRIS

## Estado de Agentes Actuales
- **Sales Agent**: Automatización de procesos de venta
- **Support Agent**: Gestión de atención al cliente  
- **Consulting Agent**: Análisis y consultoría avanzada

## Herramientas Disponibles
1. `get_iris_agents_status` - Ver estado de todos los agentes
2. `get_agent_metrics` - Métricas de agente específico
3. `deploy_agent` - Desplegar agente específico
4. `create_template` - Crear template de automatización
5. `list_available_templates` - Listar templates disponibles
6. `send_notification` - Enviar notificación
7. `get_notification_stats` - Estadísticas de notificaciones
8. `get_system_health` - Verificar salud del sistema

## Templates de Automatización
- **Sales Automation**: Lead qualification, proposal generation, follow-up
- **Support Automation**: Ticket classification, response generation
- **Consulting Analysis**: Data processing, insight generation, reporting

## Métricas Clave
- Tareas completadas por agente
- Tiempo de respuesta promedio
- Uso de tokens
- Tasa de éxito

## Notificaciones Soportadas
- Cambios de estado de agentes
- Métricas que exceden umbrales
- Errores del sistema
- Completado de tareas

Para más información, consulta el README.md.
"""

@mcp.prompt  
def iris_troubleshooting_guide() -> str:
    """Generar guía de solución de problemas para IRIS"""
    return """
# Guía de Solución de Problemas - IRIS MCP

## Herramientas de Diagnóstico
- `get_system_health` - Verificar estado general del sistema
- `get_iris_agents_status` - Verificar estado de agentes
- `get_notification_stats` - Estadísticas de notificaciones

## Problemas Comunes

### 1. Agentes No Responden
**Solución**: Verificar estado con `get_iris_agents_status`

### 2. Notificaciones No Funcionan
**Solución**: Verificar estadísticas con `get_notification_stats`

### 3. Templates No Se Crean
**Solución**: Listar disponibles con `list_available_templates`

## Contactos de Soporte
- Documentación: README.md
- Logs detallados: logs/iris_mcp.log
"""

def main():
    """Función principal del servidor MCP"""
    print("🚀 Iniciando IRIS MCP Superior Server...")
    print("🔮 Componentes disponibles:")
    print("  📊 Dashboard con métricas en tiempo real")
    print("  🔮 CLI avanzada para gestión")
    print("  📋 Sistema de templates")
    print("  🔔 Notificaciones multi-canal")
    print("  🤖 Gestión de agentes IRIS")
    print("")
    
    # Verificar que los directorios existan
    Path("logs").mkdir(exist_ok=True)
    Path("iris_templates").mkdir(exist_ok=True)
    
    # Ejecutar servidor MCP
    mcp.run()

if __name__ == "__main__":
    main()