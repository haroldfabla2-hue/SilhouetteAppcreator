import click
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
from datetime import datetime
import time

# Importar el template manager
sys.path.append(str(Path(__file__).parent.parent))
from templates.iris_templates import IRISTemplateManager

class IRISCLIManager:
    """Gestor principal de CLI para IRIS"""
    
    def __init__(self, api_base: str = "http://localhost:8000"):
        self.api_base = api_base
        self.template_manager = IRISTemplateManager()
        
    def _api_call(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
        """Realizar llamada a la API de IRIS"""
        url = f"{self.api_base}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            click.echo(f"❌ Error de conexión con la API: {e}", err=True)
            return {"error": str(e)}
        except Exception as e:
            click.echo(f"❌ Error inesperado: {e}", err=True)
            return {"error": str(e)}
    
    def get_agents_status(self) -> Dict[str, Any]:
        """Obtener estado de todos los agentes"""
        return self._api_call("/agents")
    
    def get_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Obtener métricas de un agente específico"""
        return self._api_call(f"/agents/{agent_id}/metrics")
    
    def deploy_agent(self, agent_id: str) -> Dict[str, Any]:
        """Desplegar un agente específico"""
        return self._api_call(f"/agents/{agent_id}/deploy", method="POST")
    
    def stop_agent(self, agent_id: str) -> Dict[str, Any]:
        """Detener un agente específico"""
        return self._api_call(f"/agents/{agent_id}/stop", method="POST")
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del sistema"""
        return self._api_call("/metrics/summary")

@click.group()
@click.option('--api-base', default='http://localhost:8000', help='URL base de la API de IRIS')
@click.option('--verbose', '-v', is_flag=True, help='Modo verboso')
@click.pass_context
def iris_cli(ctx, api_base, verbose):
    """🔮 CLI Avanzada para Gestión de IRIS MCP Server"""
    ctx.ensure_object(dict)
    ctx.obj['api_base'] = api_base
    ctx.obj['verbose'] = verbose
    
    if verbose:
        click.echo(f"🔗 API Base URL: {api_base}")

@iris_cli.group()
def status():
    """📊 Consultar estado del sistema"""
    pass

@status.command()
@click.pass_context
def agents(ctx):
    """Mostrar estado de todos los agentes IRIS"""
    api_base = ctx.obj['api_base']
    verbose = ctx.obj['verbose']
    
    cli_manager = IRISCLIManager(api_base)
    
    click.echo("🔍 Consultando estado de agentes IRIS...")
    click.echo("=" * 50)
    
    result = cli_manager.get_agents_status()
    
    if "error" in result:
        click.echo(f"❌ Error: {result['error']}", err=True)
        return
    
    if "agents" not in result:
        click.echo("❌ No se pudieron obtener los datos de agentes")
        return
    
    agents = result["agents"]
    
    for agent in agents:
        # Icono de estado
        if agent["status"] == "active":
            status_icon = "🟢"
            status_color = "green"
        elif agent["status"] == "error":
            status_icon = "🔴"
            status_color = "red"
        else:
            status_icon = "🟡"
            status_color = "yellow"
        
        click.echo(f"{status_icon} {agent['agent']}")
        click.echo(f"   ID: {agent['id']}")
        click.echo(f"   Estado: {agent['status'].upper()}")
        click.echo(f"   Tareas: {agent.get('tasksCompleted', 0)}")
        click.echo(f"   Tokens: {agent.get('tokenUsage', 0):,}")
        click.echo(f"   Capacidades: {', '.join(agent.get('capabilities', []))}")
        
        if verbose:
            click.echo(f"   Última actividad: {agent.get('lastActivity', 'N/A')}")
        
        click.echo()
    
    click.echo(f"📊 Total agentes: {len(agents)}")
    
    active_count = len([a for a in agents if a["status"] == "active"])
    click.echo(f"🟢 Activos: {active_count}")
    click.echo(f"🟡 Inactivos: {len(agents) - active_count}")

@status.command()
@click.pass_context
def system(ctx):
    """Mostrar métricas del sistema completo"""
    api_base = ctx.obj['api_base']
    verbose = ctx.obj['verbose']
    
    cli_manager = IRISCLIManager(api_base)
    
    click.echo("📊 Métricas del sistema IRIS...")
    click.echo("=" * 50)
    
    result = cli_manager.get_system_metrics()
    
    if "error" in result:
        click.echo(f"❌ Error: {result['error']}", err=True)
        return
    
    summary = result.get("summary", {})
    
    click.echo("🤖 Resumen del Sistema:")
    click.echo(f"   Total agentes: {summary.get('total_agents', 0)}")
    click.echo(f"   Agentes activos: {summary.get('active_agents', 0)}")
    click.echo(f"   Total tareas: {summary.get('total_tasks', 0):,}")
    click.echo(f"   Total tokens: {summary.get('total_tokens', 0):,}")
    click.echo(f"   Tiempo respuesta promedio: {summary.get('avg_response_time', 0)}s")
    click.echo(f"   Salud del sistema: {summary.get('system_health', 'unknown')}")
    
    if verbose:
        click.echo(f"\n⏰ Última actualización: {result.get('timestamp', 'N/A')}")

@iris_cli.group()
def deploy():
    """🚀 Gestión de despliegue de agentes"""
    pass

@deploy.command()
@click.argument('agent_name')
@click.pass_context
def agent(ctx, agent_name):
    """Desplegar agente específico"""
    api_base = ctx.obj['api_base']
    
    cli_manager = IRISCLIManager(api_base)
    
    click.echo(f"🚀 Desplegando agente: {agent_name}")
    
    result = cli_manager.deploy_agent(agent_name)
    
    if "error" in result:
        click.echo(f"❌ Error desplegando agente: {result['error']}", err=True)
        return
    
    click.echo(f"✅ Agente {agent_name} desplegado exitosamente")
    click.echo(f"   Estado: {result.get('status', 'unknown')}")
    click.echo(f"   Timestamp: {result.get('timestamp', 'N/A')}")

@deploy.command()
@click.option('--all', 'deploy_all', is_flag=True, help='Desplegar todos los agentes')
@click.pass_context
def all_agents(ctx, deploy_all):
    """Desplegar todos los agentes"""
    api_base = ctx.obj['api_base']
    
    if not deploy_all:
        if not click.confirm('¿Desplegar todos los agentes?'):
            click.echo("Operación cancelada")
            return
    
    cli_manager = IRISCLIManager(api_base)
    
    click.echo("🚀 Desplegando todos los agentes...")
    
    result = cli_manager.get_agents_status()
    
    if "error" in result:
        click.echo(f"❌ Error: {result['error']}", err=True)
        return
    
    agents = result.get("agents", [])
    deployed = 0
    failed = 0
    
    for agent in agents:
        agent_id = agent["id"]
        click.echo(f"   Desplegando {agent_id}...")
        
        deploy_result = cli_manager.deploy_agent(agent_id)
        
        if "error" in deploy_result:
            click.echo(f"   ❌ Error en {agent_id}: {deploy_result['error']}")
            failed += 1
        else:
            click.echo(f"   ✅ {agent_id} desplegado")
            deployed += 1
    
    click.echo(f"\n📊 Resultado del despliegue:")
    click.echo(f"   ✅ Exitosos: {deployed}")
    click.echo(f"   ❌ Fallidos: {failed}")

@iris_cli.group()
def metrics():
    """📈 Consulta de métricas"""
    pass

@metrics.command()
@click.option('--agent', 'agent_name', help='Agente específico para métricas')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Formato de salida')
@click.pass_context
def show(ctx, agent_name, output_format):
    """Mostrar métricas en tiempo real"""
    api_base = ctx.obj['api_base']
    
    cli_manager = IRISCLIManager(api_base)
    
    if agent_name:
        click.echo(f"📊 Métricas de {agent_name}...")
        result = cli_manager.get_agent_metrics(agent_name)
    else:
        click.echo("📊 Métricas del sistema...")
        result = cli_manager.get_system_metrics()
    
    if "error" in result:
        click.echo(f"❌ Error: {result['error']}", err=True)
        return
    
    if output_format == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        _display_metrics_table(result)

@metrics.command()
@click.option('--interval', default=5, help='Intervalo de actualización en segundos')
@click.option('--duration', default=30, help='Duración de monitoreo en segundos')
@click.pass_context
def monitor(ctx, interval, duration):
    """Monitoreo continuo de métricas"""
    api_base = ctx.obj['api_base']
    
    cli_manager = IRISCLIManager(api_base)
    
    click.echo(f"🔍 Monitoreando métricas cada {interval}s por {duration}s...")
    click.echo("Presiona Ctrl+C para detener")
    
    start_time = time.time()
    update_count = 0
    
    try:
        while time.time() - start_time < duration:
            # Limpiar pantalla (simplificado)
            os.system('cls' if os.name == 'nt' else 'clear')
            
            click.echo(f"📊 Monitor IRIS - Actualización {update_count + 1}")
            click.echo(f"⏰ Tiempo transcurrido: {int(time.time() - start_time)}s")
            click.echo("=" * 50)
            
            result = cli_manager.get_system_metrics()
            
            if "error" not in result:
                summary = result.get("summary", {})
                click.echo(f"Agentes activos: {summary.get('active_agents', 0)}/{summary.get('total_agents', 0)}")
                click.echo(f"Tareas completadas: {summary.get('total_tasks', 0):,}")
                click.echo(f"Tokens procesados: {summary.get('total_tokens', 0):,}")
                click.echo(f"Salud del sistema: {summary.get('system_health', 'unknown')}")
            
            update_count += 1
            time.sleep(interval)
    
    except KeyboardInterrupt:
        click.echo(f"\n⏹️  Monitoreo detenido después de {update_count} actualizaciones")

def _display_metrics_table(result: Dict[str, Any]):
    """Mostrar métricas en formato tabla"""
    if "agents" in result:
        agents = result["agents"]
        click.echo("📊 Estado de Agentes:")
        click.echo("-" * 80)
        click.echo(f"{'Agente':<20} {'Estado':<10} {'Tareas':<10} {'Tokens':<15} {'Tiempo':<10}")
        click.echo("-" * 80)
        
        for agent in agents:
            name = agent.get("agent", "N/A")[:19]
            status = agent.get("status", "N/A")[:9]
            tasks = str(agent.get("tasksCompleted", 0))
            tokens = f"{agent.get('tokenUsage', 0):,}"
            response_time = f"{agent.get('avgResponseTime', 0)}s"
            
            click.echo(f"{name:<20} {status:<10} {tasks:<10} {tokens:<15} {response_time:<10}")
    
    elif "summary" in result:
        summary = result["summary"]
        click.echo("📊 Resumen del Sistema:")
        click.echo(f"Total agentes: {summary.get('total_agents', 0)}")
        click.echo(f"Agentes activos: {summary.get('active_agents', 0)}")
        click.echo(f"Total tareas: {summary.get('total_tasks', 0):,}")
        click.echo(f"Total tokens: {summary.get('total_tokens', 0):,}")
        click.echo(f"Promedio respuesta: {summary.get('avg_response_time', 0)}s")

@iris_cli.group()
def template():
    """📋 Gestión de templates"""
    pass

@template.command()
@click.option('--category', help='Filtrar por categoría')
@click.pass_context
def list(ctx, category):
    """Listar templates disponibles"""
    template_manager = ctx.obj.get('template_manager') or IRISTemplateManager()
    
    templates = template_manager.list_templates()
    
    if not templates:
        click.echo("📋 No hay templates disponibles")
        return
    
    if category:
        templates = [t for t in templates if t.get('category') == category]
        click.echo(f"📋 Templates en categoría '{category}':")
    else:
        click.echo("📋 Todos los templates disponibles:")
    
    click.echo("-" * 60)
    
    for template in templates:
        click.echo(f"📄 {template['name']}")
        click.echo(f"   ID: {template['id']}")
        click.echo(f"   Categoría: {template.get('category', 'N/A')}")
        click.echo(f"   Descripción: {template.get('description', 'N/A')}")
        click.echo(f"   Versión: {template.get('version', 'N/A')}")
        click.echo()

@template.command()
@click.argument('template_name')
@click.option('--output', '-o', help='Archivo de salida para la configuración')
@click.option('--customize', help='Archivo de personalizaciones JSON')
@click.pass_context
def generate(ctx, template_name, output, customize):
    """Generar configuración desde template"""
    template_manager = ctx.obj.get('template_manager') or IRISTemplateManager()
    
    click.echo(f"📋 Generando configuración desde template: {template_name}")
    
    # Cargar personalizaciones si se proporcionan
    customizations = None
    if customize:
        try:
            with open(customize, 'r', encoding='utf-8') as f:
                customizations = json.load(f)
            click.echo(f"✅ Personalizaciones cargadas desde {customize}")
        except Exception as e:
            click.echo(f"❌ Error cargando personalizaciones: {e}", err=True)
            return
    
    try:
        config = template_manager.generate_workflow_config(template_name, customizations)
        
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            click.echo(f"✅ Configuración guardada en: {output_path}")
        else:
            click.echo(json.dumps(config, indent=2, ensure_ascii=False))
    
    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
    except Exception as e:
        click.echo(f"❌ Error inesperado: {e}", err=True)

@template.command()
@click.argument('template_name')
@click.pass_context
def create(ctx, template_name):
    """Crear template desde tipo predefinido"""
    template_manager = ctx.obj.get('template_manager') or IRISTemplateManager()
    
    template_types = {
        "sales": template_manager.create_sales_automation_template,
        "support": template_manager.create_support_template,
        "consulting": template_manager.create_consulting_template,
        "multiagent": template_manager.create_multiagent_template,
        "optimization": template_manager.create_optimization_template
    }
    
    if template_name not in template_types:
        click.echo(f"❌ Tipo de template '{template_name}' no reconocido", err=True)
        click.echo(f"Tipos disponibles: {', '.join(template_types.keys())}")
        return
    
    click.echo(f"📋 Creando template: {template_name}")
    
    try:
        template = template_types[template_name]()
        file_path = template_manager.save_template(template)
        
        click.echo(f"✅ Template '{template_name}' creado exitosamente")
        click.echo(f"📁 Guardado en: {file_path}")
        
        # Mostrar resumen del template
        click.echo(f"\n📊 Resumen del template:")
        click.echo(f"   Nombre: {template['name']}")
        click.echo(f"   Categoría: {template['category']}")
        click.echo(f"   Agentes: {len(template['agents'])}")
        click.echo(f"   Versión: {template['version']}")
        
    except Exception as e:
        click.echo(f"❌ Error creando template: {e}", err=True)

@template.command()
@click.argument('template_id')
@click.pass_context
def validate(ctx, template_id):
    """Validar template"""
    template_manager = ctx.obj.get('template_manager') or IRISTemplateManager()
    
    click.echo(f"🔍 Validando template: {template_id}")
    
    try:
        template = template_manager.load_template(template_id)
        
        if not template:
            click.echo(f"❌ Template '{template_id}' no encontrado", err=True)
            return
        
        validation_result = template_manager.validate_template(template)
        
        if validation_result["valid"]:
            click.echo("✅ Template válido")
        else:
            click.echo("❌ Template inválido")
        
        # Mostrar errores
        if validation_result["errors"]:
            click.echo("\n🚨 Errores:")
            for error in validation_result["errors"]:
                click.echo(f"   • {error}")
        
        # Mostrar advertencias
        if validation_result["warnings"]:
            click.echo("\n⚠️  Advertencias:")
            for warning in validation_result["warnings"]:
                click.echo(f"   • {warning}")
        
        # Mostrar información
        if validation_result["info"]:
            click.echo("\nℹ️  Información:")
            for info in validation_result["info"]:
                click.echo(f"   • {info}")
    
    except Exception as e:
        click.echo(f"❌ Error validando template: {e}", err=True)

@iris_cli.group()
def notify():
    """🔔 Configuración de notificaciones"""
    pass

@notify.command()
@click.option('--type', 'notification_type',
              type=click.Choice(['email', 'webhook', 'console']),
              default='console', help='Tipo de notificación')
@click.option('--config', help='Archivo de configuración JSON')
@click.pass_context
def config(ctx, notification_type, config):
    """Configurar sistema de notificaciones"""
    click.echo(f"🔔 Configurando notificaciones: {notification_type}")
    
    if notification_type == 'email':
        _configure_email_notifications()
    elif notification_type == 'webhook':
        _configure_webhook_notifications()
    else:
        click.echo("✅ Notificaciones por consola ya están habilitadas")

def _configure_email_notifications():
    """Configurar notificaciones por email"""
    click.echo("📧 Configuración de notificaciones por email")
    click.echo("-" * 40)
    
    email = click.prompt('📧 Email', type=str)
    password = click.prompt('🔐 App password (o contraseña)', type=str, hide_input=True)
    smtp_server = click.prompt('🖥️  Servidor SMTP', default='smtp.gmail.com')
    smtp_port = click.prompt('🔌 Puerto SMTP', default=587, type=int)
    
    config = {
        "type": "email",
        "settings": {
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "email": email,
            "password": password,
            "security": "tls"
        },
        "events": [
            "agent_started",
            "agent_stopped", 
            "agent_error",
            "system_alert"
        ],
        "created_at": datetime.now().isoformat()
    }
    
    config_file = Path("iris_notification_config.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    
    click.echo(f"✅ Configuración guardada en: {config_file}")

def _configure_webhook_notifications():
    """Configurar notificaciones por webhook"""
    click.echo("🔗 Configuración de notificaciones por webhook")
    click.echo("-" * 40)
    
    webhook_url = click.prompt('🔗 URL del webhook', type=str)
    auth_token = click.prompt('🔐 Token de autenticación (opcional)', type=str, default='')
    
    config = {
        "type": "webhook",
        "settings": {
            "webhook_url": webhook_url,
            "auth_token": auth_token,
            "method": "POST",
            "content_type": "application/json"
        },
        "events": [
            "agent_status_change",
            "metric_threshold_exceeded",
            "system_error"
        ],
        "created_at": datetime.now().isoformat()
    }
    
    config_file = Path("iris_notification_config.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    
    click.echo(f"✅ Configuración guardada en: {config_file}")

@iris_cli.group()
def log():
    """📋 Gestión de logs"""
    pass

@log.command()
@click.argument('agent_name', required=False)
@click.option('--level', type=click.Choice(['debug', 'info', 'warning', 'error']), help='Nivel de log')
@click.option('--lines', default=50, help='Número de líneas a mostrar')
@click.pass_context
def show(ctx, agent_name, level, lines):
    """Ver logs de agente específico o todos"""
    if agent_name:
        click.echo(f"📋 Logs de {agent_name}")
    else:
        click.echo("📋 Logs de todos los agentes")
    
    click.echo(f"🔍 Últimas {lines} líneas")
    
    # Simular logs (en implementación real, conectar con sistema de logs)
    logs = _generate_sample_logs(agent_name, level, lines)
    
    for log_entry in logs:
        level_colors = {
            'DEBUG': 'blue',
            'INFO': 'green', 
            'WARNING': 'yellow',
            'ERROR': 'red'
        }
        color = level_colors.get(log_entry['level'], 'white')
        
        click.echo(f"[{log_entry['timestamp']}] {log_entry['level']}: {log_entry['message']}")
    
    click.echo(f"\n📊 Total entradas: {len(logs)}")

def _generate_sample_logs(agent_name: Optional[str], level: Optional[str], lines: int) -> List[Dict[str, Any]]:
    """Generar logs de ejemplo (simulado)"""
    import random
    
    agents = ["sales_agent", "support_agent", "consulting_agent"]
    levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
    messages = [
        "Agent started successfully",
        "Processing task queue",
        "Task completed",
        "Connection established",
        "Metrics updated",
        "Error in processing",
        "Timeout occurred",
        "Resource allocation"
    ]
    
    logs = []
    current_time = datetime.now()
    
    for i in range(lines):
        log_time = current_time - timedelta(minutes=i*2)
        selected_agent = agent_name or random.choice(agents)
        selected_level = level or random.choice(levels)
        selected_message = random.choice(messages)
        
        logs.append({
            "timestamp": log_time.strftime("%Y-%m-%d %H:%M:%S"),
            "level": selected_level,
            "agent": selected_agent,
            "message": selected_message
        })
    
    return logs[:lines]

@iris_cli.command()
@click.option('--full', is_flag=True, help='Mostrar información completa del sistema')
@click.pass_context
def health(ctx, full):
    """Verificar salud del sistema IRIS"""
    api_base = ctx.obj['api_base']
    
    click.echo("🔍 Verificando salud del sistema IRIS...")
    click.echo("=" * 50)
    
    # Verificar conectividad con API
    cli_manager = IRISCLIManager(api_base)
    api_result = cli_manager.get_agents_status()
    
    if "error" in api_result:
        click.echo("❌ API: No disponible")
        click.echo(f"   Error: {api_result['error']}")
    else:
        click.echo("✅ API: Disponible")
        if full:
            agents = api_result.get("agents", [])
            click.echo(f"   Agentes detectados: {len(agents)}")
    
    # Verificar templates
    template_manager = ctx.obj.get('template_manager') or IRISTemplateManager()
    templates = template_manager.list_templates()
    click.echo("✅ Templates: Disponibles")
    click.echo(f"   Templates instalados: {len(templates)}")
    
    # Verificar archivos de configuración
    config_files = [
        "iris_notification_config.json",
        "iris_templates/templates_index.json"
    ]
    
    click.echo("✅ Configuración:")
    for config_file in config_files:
        if Path(config_file).exists():
            click.echo(f"   ✅ {config_file}")
        else:
            click.echo(f"   ⚪ {config_file} (no configurado)")
    
    if full:
        click.echo("\n📊 Información del sistema:")
        click.echo(f"   CLI Version: 1.0.0")
        click.echo(f"   Python: {sys.version.split()[0]}")
        click.echo(f"   Directorio de trabajo: {os.getcwd()}")

@iris_cli.command()
@click.pass_context
def version(ctx):
    """Mostrar información de versión"""
    click.echo("🔮 IRIS MCP Server CLI")
    click.echo("=" * 30)
    click.echo("Versión: 1.0.0")
    click.echo("Autor: IRIS MCP Integration Team")
    click.echo("Descripción: CLI avanzada para gestión de agentes IRIS")
    click.echo("")
    click.echo("Comandos principales:")
    click.echo("  iris status agents    - Ver estado de agentes")
    click.echo("  iris deploy agent     - Desplegar agente")
    click.echo("  iris metrics show     - Ver métricas")
    click.echo("  iris template list    - Listar templates")
    click.echo("  iris notify config    - Configurar notificaciones")
    click.echo("  iris log show         - Ver logs")
    click.echo("")
    click.echo("Para más información: iris --help")

if __name__ == '__main__':
    # Inicializar contexto con template manager
    iris_cli(auto_envvar_prefix='IRIS_')