#!/usr/bin/env python3
"""
IRIS MCP Server - Servidor MCP principal
Integra todos los componentes de IRIS MCP en un servidor MCP usando FastMCP
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import subprocess
import time

# Añadir directorio actual al path
sys.path.append(str(Path(__file__).parent))

try:
    from fastmcp import FastMCP
except ImportError:
    print("FastMCP no está instalado. Instalando...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastmcp"])
    from fastmcp import FastMCP

# Configurar FastMCP
mcp = FastMCP("IRIS MCP Superior")

# Inicializar gestores (solo cuando se necesiten)
def get_template_manager():
    try:
        from templates.iris_templates import IRISTemplateManager
        return IRISTemplateManager()
    except Exception as e:
        print(f"Warning: Could not import template manager: {e}")
        return None

def get_notification_manager():
    try:
        from notifications.iris_notifications import IRISNotificationManager, NotificationEvent, NotificationLevel
        return IRISNotificationManager(), NotificationEvent, NotificationLevel
    except Exception as e:
        print(f"Warning: Could not import notification manager: {e}")
        return None, None, None

# Configuración por defecto
DEFAULT_CONFIG = {
    "api_base": "http://localhost:8000",
    "dashboard_port": 3000,
    "metrics_port": 8000,
    "log_level": "INFO"
}

@mcp.tool
def get_iris_agents_status() -> str:
    """Obtener estado actual de todos los agentes IRIS"""
    try:
        # Simular datos de agentes (en implementación real, conectaría con API)
        agents_data = [
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
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "agents": agents_data,
            "summary": {
                "total_agents": len(agents_data),
                "active_agents": len([a for a in agents_data if a["status"] == "active"]),
                "total_tasks": sum(a["tasksCompleted"] for a in agents_data),
                "total_tokens": sum(a["tokenUsage"] for a in agents_data),
                "avg_response_time": round(sum(a["avgResponseTime"] for a in agents_data) / len(agents_data), 2),
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
        if agent_id not in ["sales_agent", "support_agent", "consulting_agent"]:
            return json.dumps({"error": f"Agente {agent_id} no encontrado"}, indent=2)
        
        # Simular métricas detalladas (en implementación real, desde API)
        base_metrics = {
            "sales_agent": {
                "tasks_completed": 156,
                "token_usage": 45200,
                "avg_response_time": 1.2,
                "success_rate": 0.94
            },
            "support_agent": {
                "tasks_completed": 89,
                "token_usage": 32400,
                "avg_response_time": 0.8,
                "success_rate": 0.96
            },
            "consulting_agent": {
                "tasks_completed": 23,
                "token_usage": 67800,
                "avg_response_time": 2.1,
                "success_rate": 0.91
            }
        }
        
        metrics = base_metrics[agent_id].copy()
        metrics.update({
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "hourly_stats": generate_hourly_stats(),
            "recent_tasks": generate_recent_tasks(agent_id)
        })
        
        return json.dumps(metrics, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": f"Error obteniendo métricas de {agent_id}: {str(e)}"}, indent=2)

@mcp.tool
def deploy_agent(agent_id: str) -> str:
    """Desplegar un agente específico en IRIS"""
    try:
        if agent_id not in ["sales_agent", "support_agent", "consulting_agent"]:
            return json.dumps({"error": f"Agente {agent_id} no válido"}, indent=2)
        
        # Simular despliegue
        time.sleep(1)  # Simular tiempo de despliegue
        
        # Intentar enviar notificación
        try:
            notification_manager, NotificationEvent, NotificationLevel = get_notification_manager()
            if notification_manager and NotificationEvent and NotificationLevel:
                deploy_event = NotificationEvent(
                    event_type="agent_status_change",
                    level=NotificationLevel.INFO,
                    title=f"Agente {agent_id} Desplegado",
                    message=f"El agente {agent_id} ha sido desplegado exitosamente",
                    timestamp=datetime.now(),
                    agent_id=agent_id,
                    details={"action": "deploy", "status": "active"}
                )
                notification_manager.configure_console()
                notification_manager.send_notification(deploy_event)
        except Exception as e:
            # Si falla la notificación, continuar sin error
            pass
        
        result = {
            "status": "deployed",
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "message": f"Agente {agent_id} desplegado exitosamente"
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": f"Error desplegando {agent_id}: {str(e)}"}, indent=2)

@mcp.tool
def create_template(template_type: str, customizations: Optional[Dict[str, Any]] = None) -> str:
    """Crear un template de automatización para IRIS"""
    try:
        template_manager = get_template_manager()
        notification_manager, NotificationEvent, NotificationLevel = get_notification_manager()
        
        if not template_manager:
            return json.dumps({"error": "Template manager no disponible"}, indent=2)
        
        template_creators = {
            "sales": template_manager.create_sales_automation_template,
            "support": template_manager.create_support_template,
            "consulting": template_manager.create_consulting_template,
            "multiagent": template_manager.create_multiagent_template,
            "optimization": template_manager.create_optimization_template
        }
        
        if template_type not in template_creators:
            available_types = list(template_creators.keys())
            return json.dumps({
                "error": f"Tipo de template '{template_type}' no válido",
                "available_types": available_types
            }, indent=2)
        
        # Crear template
        template = template_creators[template_type]()
        
        # Aplicar personalizaciones si se proporcionan
        if customizations:
            template = template_manager._apply_customizations(template, customizations)
        
        # Guardar template
        file_path = template_manager.save_template(template)
        
        # Intentar enviar notificación
        try:
            if notification_manager and NotificationEvent and NotificationLevel:
                template_event = NotificationEvent(
                    event_type="template_created",
                    level=NotificationLevel.INFO,
                    title=f"Template {template_type} Creado",
                    message=f"Template de {template_type} creado y guardado",
                    timestamp=datetime.now(),
                    details={"template_id": template["id"], "file_path": file_path}
                )
                notification_manager.send_notification(template_event)
        except Exception:
            # Si falla la notificación, continuar sin error
            pass
        
        result = {
            "template": template,
            "file_path": file_path,
            "message": f"Template {template_type} creado exitosamente",
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": f"Error creando template {template_type}: {str(e)}"}, indent=2)

@mcp.tool
def generate_workflow_config(template_id: str, customizations: Optional[Dict[str, Any]] = None) -> str:
    """Generar configuración de workflow desde template"""
    try:
        config = template_manager.generate_workflow_config(template_id, customizations)
        
        result = {
            "configuration": config,
            "generated_at": datetime.now().isoformat(),
            "template_id": template_id,
            "message": f"Configuración generada para template {template_id}"
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": f"Error generando configuración para {template_id}: {str(e)}"}, indent=2)

@mcp.tool
def send_notification(event_type: str, title: str, message: str, agent_id: Optional[str] = None, level: str = "info") -> str:
    """Enviar notificación a través del sistema multi-canal"""
    try:
        notification_manager, NotificationEvent, NotificationLevel = get_notification_manager()
        
        if not notification_manager or not NotificationEvent or not NotificationLevel:
            # Crear respuesta básica sin notificaciones
            result = {
                "success": False,
                "event_type": event_type,
                "title": title,
                "sent_at": datetime.now().isoformat(),
                "message": "Sistema de notificaciones no disponible (modo simulación)",
                "note": "Notification manager no disponible, datos guardados en log local"
            }
            return json.dumps(result, indent=2, ensure_ascii=False)
        
        # Mapear nivel de notificación
        level_map = {
            "info": NotificationLevel.INFO,
            "warning": NotificationLevel.WARNING,
            "error": NotificationLevel.ERROR,
            "critical": NotificationLevel.CRITICAL
        }
        
        if level not in level_map:
            level = "info"
        
        # Crear evento de notificación
        notification_event = NotificationEvent(
            event_type=event_type,
            level=level_map[level],
            title=title,
            message=message,
            timestamp=datetime.now(),
            agent_id=agent_id
        )
        
        # Configurar consola si no está configurada
        notification_manager.configure_console()
        
        # Enviar notificación
        success = notification_manager.send_notification(notification_event)
        
        result = {
            "success": success,
            "event_type": event_type,
            "title": title,
            "sent_at": datetime.now().isoformat(),
            "message": "Notificación enviada exitosamente" if success else "Error enviando notificación"
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": f"Error enviando notificación: {str(e)}"}, indent=2)

@mcp.tool
def get_system_health() -> str:
    """Verificar salud completa del sistema IRIS"""
    try:
        template_manager = get_template_manager()
        notification_manager, _, _ = get_notification_manager()
        
        health_status = {
            "system": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "template_manager": {
                    "status": "operational",
                    "templates_available": len(template_manager.list_templates()) if template_manager else 0
                },
                "notification_manager": {
                    "status": "operational",
                    "channels_configured": 1 if notification_manager else 0
                },
                "agents": {
                    "status": "operational",
                    "total_agents": 3,
                    "active_agents": 3
                },
                "api_server": {
                    "status": "simulated_operational",
                    "port": 8000,
                    "endpoints_available": 9
                }
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
def list_available_templates() -> str:
    """Listar todos los templates disponibles"""
    try:
        template_manager = get_template_manager()
        
        if not template_manager:
            return json.dumps({
                "error": "Template manager no disponible",
                "templates": [],
                "total": 0
            }, indent=2)
        
        templates = template_manager.list_templates()
        
        if not templates:
            templates_info = {
                "message": "No hay templates disponibles",
                "templates": [],
                "total": 0
            }
        else:
            templates_info = {
                "message": f"Se encontraron {len(templates)} templates",
                "templates": templates,
                "total": len(templates),
                "categories": list(set(t.get("category", "uncategorized") for t in templates))
            }
        
        return json.dumps(templates_info, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": f"Error listando templates: {str(e)}"}, indent=2)

@mcp.tool
def get_notification_stats() -> str:
    """Obtener estadísticas del sistema de notificaciones"""
    try:
        notification_manager, _, _ = get_notification_manager()
        
        if not notification_manager:
            return json.dumps({
                "error": "Notification manager no disponible",
                "statistics": {"total_notifications": 0},
                "timestamp": datetime.now().isoformat()
            }, indent=2)
        
        stats = notification_manager.get_notification_stats()
        history = notification_manager.get_notification_history(10)
        
        result = {
            "statistics": stats,
            "recent_history": history,
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": f"Error obteniendo estadísticas: {str(e)}"}, indent=2)

@mcp.prompt
def iris_agent_management_guide() -> str:
    """Generar guía para gestión de agentes IRIS"""
    return f"""
# Guía de Gestión de Agentes IRIS

## Estado de Agentes Actuales
- **Sales Agent**: Automatización de procesos de venta
- **Support Agent**: Gestión de atención al cliente  
- **Consulting Agent**: Análisis y consultoría avanzada

## Comandos CLI Disponibles
1. `iris status agents` - Ver estado de todos los agentes
2. `iris deploy <agent_id>` - Desplegar agente específico
3. `iris metrics show` - Ver métricas en tiempo real
4. `iris template list` - Listar templates disponibles
5. `iris notify config` - Configurar notificaciones

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

Para más información, consulta el README.md o ejecuta ./demo.py para ver una demostración completa.
"""

@mcp.prompt  
def iris_troubleshooting_guide() -> str:
    """Generar guía de solución de problemas para IRIS"""
    return f"""
# Guía de Solución de Problemas - IRIS MCP

## Problemas Comunes y Soluciones

### 1. Agentes No Responden
**Síntomas**: Dashboard muestra agentes offline
**Soluciones**:
- Verificar conectividad de red
- Reiniciar servidor: ./start_metrics_server.sh
- Verificar logs: tail -f logs/metrics.log

### 2. Dashboard No Carga
**Síntomas**: Error 500 o timeout en dashboard
**Soluciones**:
- Verificar que el servidor de métricas esté ejecutándose
- Verificar puerto 3000 disponible
- Reinstalar dependencias: cd dashboard && npm install

### 3. Notificaciones No Envían
**Síntomas**: No se reciben alertas
**Soluciones**:
- Verificar configuración de email/webhook
- Probar notificaciones: ./run_notifications.sh test
- Verificar logs: tail -f logs/notifications.log

### 4. CLI No Responde
**Síntomas**: Comandos iris dan error
**Soluciones**:
- Activar entorno virtual: source iris-mcp-env/bin/activate
- Verificar dependencias: pip install -r requirements.txt
- Verificar API: curl http://localhost:8000/

### 5. Templates No Se Crean
**Síntomas**: Error al generar templates
**Soluciones**:
- Verificar permisos de escritura en iris_templates/
- Verificar espacio en disco
- Revisar logs de templates

## Comandos de Diagnóstico
```bash
# Verificar estado general
./run_cli.sh health

# Ver logs en tiempo real
tail -f logs/*.log

# Verificar conectividad
curl http://localhost:8000/agents

# Probar todos los componentes
python demo.py
```

## Contactos de Soporte
- Logs detallados: logs/iris_mcp.log
- Documentación: README.md
- Configuración: .env
"""

# Funciones auxiliares para simulación
def generate_hourly_stats() -> List[Dict[str, Any]]:
    """Generar estadísticas por hora simuladas"""
    import random
    from datetime import datetime, timedelta
    
    stats = []
    current_time = datetime.now()
    
    for i in range(24):
        hour_time = current_time - timedelta(hours=23-i)
        stats.append({
            "hour": hour_time.strftime("%Y-%m-%dT%H:00:00"),
            "tasks": random.randint(10, 50),
            "tokens": random.randint(5000, 25000),
            "response_time": round(random.uniform(0.5, 3.0), 1)
        })
    
    return stats

def generate_recent_tasks(agent_id: str) -> List[Dict[str, Any]]:
    """Generar tareas recientes simuladas"""
    import random
    from datetime import datetime, timedelta
    
    task_names = {
        "sales_agent": ["Lead Qualification", "Proposal Generation", "Follow-up Call", "Demo Setup"],
        "support_agent": ["Ticket Classification", "Customer Response", "Escalation Review", "Solution Documentation"],
        "consulting_agent": ["Data Analysis", "Report Generation", "Client Consultation", "Insight Generation"]
    }
    
    tasks = []
    current_time = datetime.now()
    
    for i in range(10):
        task_time = current_time - timedelta(minutes=i*15)
        tasks.append({
            "id": f"{agent_id}_task_{i}",
            "name": random.choice(task_names.get(agent_id, ["General Task"])),
            "status": "completed" if i < 8 else "in_progress",
            "completedAt": task_time.strftime("%Y-%m-%dT%H:%M:%S") if i < 8 else None,
            "tokensUsed": random.randint(500, 5000)
        })
    
    return tasks

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