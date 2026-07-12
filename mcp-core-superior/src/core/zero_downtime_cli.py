"""
Utilidades y CLI para Zero-Downtime Deployer
Comandos útiles para gestionar deployments
"""

import asyncio
import logging
import json
import argparse
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime

from .zero_downtime_deployer import DeploymentStrategy
from .deployer_config import (
    get_deployment_config,
    validate_deployment_config,
    DEFAULT_DEV_CONFIG,
    DEFAULT_STAGING_CONFIG,
    DEFAULT_PROD_CONFIG
)
from .deployer_integrator import (
    DeploymentCoordinator,
    initialize_deployment_coordinator,
    shutdown_deployment_coordinator
)
from .config import settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp.deployer.cli")


class DeployerCLI:
    """Interface de línea de comandos para el deployer"""
    
    def __init__(self):
        self.coordinator: Optional[DeploymentCoordinator] = None
        
    async def run_command(self, args: argparse.Namespace) -> int:
        """Ejecutar comando CLI"""
        try:
            if args.command == "deploy":
                return await self._cmd_deploy(args)
            elif args.command == "status":
                return await self._cmd_status(args)
            elif args.command == "health":
                return await self._cmd_health(args)
            elif args.command == "rollback":
                return await self._cmd_rollback(args)
            elif args.command == "list-agents":
                return await self._cmd_list_agents(args)
            elif args.command == "agent":
                return await self._cmd_agent(args)
            elif args.command == "config":
                return await self._cmd_config(args)
            else:
                print(f"Comando desconocido: {args.command}")
                return 1
                
        except Exception as e:
            logger.error(f"Error ejecutando comando: {e}")
            return 1
    
    async def _cmd_deploy(self, args: argparse.Namespace) -> int:
        """Comando deploy"""
        environment = args.environment or "development"
        agent_list = args.agents.split(",") if args.agents else None
        strategy = args.strategy or "blue_green"
        
        print(f"🚀 Iniciando deployment - entorno: {environment}, estrategia: {strategy}")
        
        # Inicializar coordinador
        self.coordinator = await initialize_deployment_coordinator(environment)
        
        try:
            # Obtener configuración
            deployment_config = get_deployment_config(environment, agent_list)
            deployment_config["strategy"] = strategy
            
            # Validar configuración
            if not validate_deployment_config(deployment_config):
                print("❌ Configuración de deployment inválida")
                return 1
            
            # Deployer
            if agent_list and len(agent_list) == 1:
                success = await self.coordinator.deploy_single_agent(agent_list[0])
            else:
                success = await self.coordinator.deploy_all_agents(agent_list)
            
            if success:
                print("✅ Deployment completado exitosamente")
                return 0
            else:
                print("❌ Deployment falló")
                return 1
                
        finally:
            await shutdown_deployment_coordinator()
    
    async def _cmd_status(self, args: argparse.Namespace) -> int:
        """Comando status"""
        environment = args.environment or "development"
        
        print(f"📊 Obteniendo estado del sistema - entorno: {environment}")
        
        try:
            self.coordinator = await initialize_deployment_coordinator(environment)
            
            # Obtener estado
            status = await self.coordinator.get_system_status()
            
            # Mostrar estado
            print("\n=== ESTADO DEL SISTEMA ===")
            print(f"Timestamp: {status.get('timestamp')}")
            print(f"Modo de integración: {status.get('integration_mode')}")
            
            deployer = status.get('deployer', {})
            print(f"\n🔧 DEPLOYER:")
            print(f"  Estado: {deployer.get('status', 'unknown')}")
            print(f"  Deployment ID: {deployer.get('deployment_id', 'N/A')}")
            
            if 'metrics' in deployer:
                metrics = deployer['metrics']
                print(f"  Éxito: {metrics.get('success', False)}")
                print(f"  Duración: {metrics.get('duration', 0):.2f}s")
                print(f"  Health checks: {metrics.get('health_checks_passed', 0)}/{metrics.get('health_checks_failed', 0)}")
            
            orchestrator = status.get('orchestrator', {})
            print(f"\n🎭 ORQUESTADOR:")
            print(f"  Inicializado: {orchestrator.get('initialized', False)}")
            print(f"  Tareas activas: {orchestrator.get('active_tasks_count', 0)}")
            print(f"  Tareas completadas: {orchestrator.get('completed_tasks_count', 0)}")
            
            if status.get('last_deployment'):
                last_depl = status['last_deployment']
                print(f"\n📈 ÚLTIMO DEPLOYMENT:")
                print(f"  ID: {last_depl.get('deployment_id')}")
                print(f"  Éxito: {last_depl.get('success', False)}")
                print(f"  Timestamp: {last_depl.get('timestamp')}")
            
            return 0
            
        finally:
            await shutdown_deployment_coordinator()
    
    async def _cmd_health(self, args: argparse.Namespace) -> int:
        """Comando health"""
        environment = args.environment or "development"
        
        print(f"🏥 Realizando health check - entorno: {environment}")
        
        try:
            self.coordinator = await initialize_deployment_coordinator(environment)
            
            # Health check
            health = await self.coordinator.perform_health_check()
            
            # Mostrar resultado
            print("\n=== HEALTH CHECK ===")
            print(f"Estado general: {health.get('overall_status', 'unknown')}")
            print(f"Timestamp: {health.get('timestamp')}")
            
            components = health.get('components', {})
            
            print(f"\n🔧 DEPLOYER:")
            deployer_health = components.get('deployer', {})
            if isinstance(deployer_health, dict):
                print(f"  Status: {deployer_health.get('status', 'unknown')}")
            else:
                print(f"  Status: {deployer_health}")
            
            print(f"\n🎭 ORQUESTADOR:")
            orchestrator_health = components.get('orchestrator', {})
            if isinstance(orchestrator_health, dict):
                print(f"  Inicializado: {orchestrator_health.get('initialized', False)}")
                print(f"  Tareas activas: {orchestrator_health.get('active_tasks', 0)}")
            else:
                print(f"  Status: {orchestrator_health}")
            
            if health.get('error'):
                print(f"\n❌ ERROR: {health['error']}")
            
            return 0 if health.get('overall_status') == 'healthy' else 1
            
        finally:
            await shutdown_deployment_coordinator()
    
    async def _cmd_rollback(self, args: argparse.Namespace) -> int:
        """Comando rollback"""
        environment = args.environment or "development"
        deployment_id = args.deployment_id
        
        print(f"⏪ Iniciando rollback - entorno: {environment}")
        
        if not deployment_id:
            print("❌ Deployment ID requerido")
            return 1
        
        # En implementación real, se ejecutaría el rollback
        print(f"🔄 Rollback de deployment {deployment_id}")
        print("⚠️  Rollback no implementado completamente en esta versión")
        
        return 0
    
    async def _cmd_list_agents(self, args: argparse.Namespace) -> int:
        """Comando list-agents"""
        environment = args.environment or "development"
        
        print(f"📋 Listando agentes disponibles - entorno: {environment}")
        
        try:
            # Mostrar agentes disponibles
            agent_configs = {
                "file_processing": "Procesamiento de archivos",
                "database_operations": "Operaciones de base de datos", 
                "web_scraping": "Web scraping",
                "search_engine": "Motor de búsqueda",
                "python_executor": "Ejecución de Python",
                "multiagent_orchestrator": "Orquestador multi-agente"
            }
            
            print("\n=== AGENTES DISPONIBLES ===")
            for agent_id, description in agent_configs.items():
                print(f"  {agent_id}: {description}")
            
            print(f"\n💡 Uso: python -m zero_downtime_cli agent <agent_id> [opciones]")
            
            return 0
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    async def _cmd_agent(self, args: argparse.Namespace) -> int:
        """Comando agent"""
        agent_id = args.agent_id
        operation = args.operation or "deploy"
        
        if not agent_id:
            print("❌ Agent ID requerido")
            return 1
        
        environment = args.environment or "development"
        
        print(f"🤖 {operation.capitalize()} agente {agent_id} - entorno: {environment}")
        
        try:
            self.coordinator = await initialize_deployment_coordinator(environment)
            
            if operation == "deploy":
                success = await self.coordinator.deploy_single_agent(agent_id)
                if success:
                    print(f"✅ Agente {agent_id} deployado exitosamente")
                else:
                    print(f"❌ Deployment de agente {agent_id} falló")
                return 0 if success else 1
                
            elif operation == "status":
                # Mostrar status específico del agente
                print(f"📊 Status del agente {agent_id}")
                # En implementación real, se obtendría el status específico
                print("Status específico del agente no implementado completamente")
                return 0
                
            else:
                print(f"❌ Operación no válida: {operation}")
                return 1
                
        finally:
            await shutdown_deployment_coordinator()
    
    async def _cmd_config(self, args: argparse.Namespace) -> int:
        """Comando config"""
        environment = args.environment or "development"
        output_file = args.output
        
        print(f"⚙️  Generando configuración - entorno: {environment}")
        
        try:
            # Obtener configuración
            config = get_deployment_config(environment)
            
            # Mostrar o guardar
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(config, f, indent=2, default=str)
                print(f"✅ Configuración guardada en {output_file}")
            else:
                print("\n=== CONFIGURACIÓN ===")
                print(json.dumps(config, indent=2, default=str))
            
            return 0
            
        except Exception as e:
            print(f"Error: {e}")
            return 1


def create_argument_parser() -> argparse.ArgumentParser:
    """Crear parser de argumentos"""
    parser = argparse.ArgumentParser(
        description="CLI para Zero-Downtime Deployer de MCP Core Superior",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Deployer todos los agentes en desarrollo
  python -m zero_downtime_cli deploy --environment development

  # Deployer agentes específicos en staging
  python -m zero_downtime_cli deploy --environment staging --agents file_processing,database_operations

  # Ver estado del sistema
  python -m zero_downtime_cli status --environment production

  # Health check
  python -m zero_downtime_cli health --environment production

  # Deployer agente individual
  python -m zero_downtime_cli agent file_processing --environment development

  # Generar configuración
  python -m zero_downtime_cli config --environment production --output config.json
        """
    )
    
    parser.add_argument("--log-level", default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Nivel de logging")
    
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")
    
    # Comando deploy
    deploy_parser = subparsers.add_parser("deploy", help="Deployer agentes")
    deploy_parser.add_argument("--environment", "-e", default="development",
                              choices=["development", "staging", "production"],
                              help="Entorno de deployment")
    deploy_parser.add_argument("--agents", "-a", 
                              help="Lista de agentes a deployer (separados por comas)")
    deploy_parser.add_argument("--strategy", "-s", default="blue_green",
                              choices=["blue_green", "rolling_update", "canary", "immediate"],
                              help="Estrategia de deployment")
    
    # Comando status
    status_parser = subparsers.add_parser("status", help="Obtener estado del sistema")
    status_parser.add_argument("--environment", "-e", default="development",
                              choices=["development", "staging", "production"],
                              help="Entorno")
    
    # Comando health
    health_parser = subparsers.add_parser("health", help="Health check del sistema")
    health_parser.add_argument("--environment", "-e", default="development",
                              choices=["development", "staging", "production"],
                              help="Entorno")
    
    # Comando rollback
    rollback_parser = subparsers.add_parser("rollback", help="Rollback de deployment")
    rollback_parser.add_argument("--environment", "-e", default="development",
                                choices=["development", "staging", "production"],
                                help="Entorno")
    rollback_parser.add_argument("--deployment-id", required=True,
                                help="ID del deployment a rollback")
    
    # Comando list-agents
    list_parser = subparsers.add_parser("list-agents", help="Listar agentes disponibles")
    list_parser.add_argument("--environment", "-e", default="development",
                            choices=["development", "staging", "production"],
                            help="Entorno")
    
    # Comando agent
    agent_parser = subparsers.add_parser("agent", help="Gestionar agente individual")
    agent_parser.add_argument("agent_id", help="ID del agente")
    agent_parser.add_argument("--operation", "-o", default="deploy",
                             choices=["deploy", "status", "stop"],
                             help="Operación a realizar")
    agent_parser.add_argument("--environment", "-e", default="development",
                             choices=["development", "staging", "production"],
                             help="Entorno")
    
    # Comando config
    config_parser = subparsers.add_parser("config", help="Generar configuración")
    config_parser.add_argument("--environment", "-e", default="development",
                              choices=["development", "staging", "production"],
                              help="Entorno")
    config_parser.add_argument("--output", "-o",
                              help="Archivo de salida (opcional, stdout por defecto)")
    
    return parser


async def main():
    """Función principal CLI"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Configurar logging
    logging.getLogger("mcp").setLevel(getattr(logging, args.log_level))
    
    # Ejecutar comando
    cli = DeployerCLI()
    return await cli.run_command(args)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))