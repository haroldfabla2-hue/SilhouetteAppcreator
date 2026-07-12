#!/usr/bin/env python3
"""
Script de inicio rápido para el Sistema de Agentes
Interfaz unificada para ejecutar todas las operaciones de base de datos
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Añadir el directorio actual al path para importaciones
sys.path.append(str(Path(__file__).parent))

from backend.database.init_db import DatabaseInitializer
from backend.database.test_connection import ConnectionTester

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Configurar variables de entorno necesarias"""
    # Configurar variables por defecto si no existen
    env_defaults = {
        'POSTGRES_HOST': 'localhost',
        'POSTGRES_PORT': '5432',
        'POSTGRES_DB': 'agente_db',
        'POSTGRES_USER': 'postgres',
        'POSTGRES_PASSWORD': 'postgres_secure_password',
        'REDIS_HOST': 'localhost',
        'REDIS_PORT': '6379',
        'REDIS_DB': '0',
        'BACKEND_URL': 'http://localhost:8000',
        'FRONTEND_URL': 'http://localhost:3000',
        'PROMETHEUS_URL': 'http://localhost:9090',
        'GRAFANA_URL': 'http://localhost:3001'
    }
    
    for key, default_value in env_defaults.items():
        if key not in os.environ:
            os.environ[key] = default_value

def cmd_init(args):
    """Comando de inicialización completa"""
    logger.info("🚀 Iniciando configuración completa del sistema...")
    
    try:
        # Inicializar base de datos
        logger.info("📊 Inicializando base de datos...")
        initializer = DatabaseInitializer(
            host=args.host,
            port=args.port,
            database=args.database,
            user=args.user,
            password=args.password
        )
        
        success = initializer.initialize_database()
        
        if success:
            logger.info("🎉 ¡Inicialización completada exitosamente!")
            
            # Mostrar estadísticas
            stats = initializer.get_database_stats()
            logger.info("📈 Estadísticas finales:")
            for key, value in stats.items():
                logger.info(f"  {key}: {value}")
            
            return 0
        else:
            logger.error("💥 Error durante la inicialización")
            return 1
            
    except Exception as e:
        logger.error(f"💥 Error inesperado: {e}")
        return 1

def cmd_test(args):
    """Comando de pruebas de conectividad"""
    logger.info("🔍 Iniciando pruebas de conectividad...")
    
    try:
        tester = ConnectionTester()
        
        if args.service:
            # Prueba específica
            if args.service == 'postgres':
                success = tester.test_postgresql()
            elif args.service == 'redis':
                success = tester.test_redis()
            elif args.service == 'api':
                success = tester.test_http_service('Backend API', 
                                                 os.getenv('BACKEND_URL'), '/health')
            else:
                logger.error(f"❌ Servicio no reconocido: {args.service}")
                return 1
            
            return 0 if success else 1
        else:
            # Prueba completa
            success = tester.run_comprehensive_test()
            return 0 if success else 1
            
    except Exception as e:
        logger.error(f"💥 Error inesperado: {e}")
        return 1

def cmd_status(args):
    """Comando de estado del sistema"""
    logger.info("📊 Verificando estado del sistema...")
    
    try:
        # Probar PostgreSQL
        logger.info("🐘 Probando PostgreSQL...")
        initializer = DatabaseInitializer()
        postgres_ok = initializer.test_connection()
        
        # Probar Redis
        logger.info("🔴 Probando Redis...")
        tester = ConnectionTester()
        redis_ok = tester.test_redis()
        
        # Verificar contenedores Docker
        logger.info("🐳 Verificando contenedores...")
        import subprocess
        
        containers = ['agente_postgres', 'agente_redis', 'agente_backend', 'agente_frontend']
        container_status = {}
        
        for container in containers:
            try:
                result = subprocess.run(
                    ['docker', 'ps', '--format', '{{.Names}}'],
                    capture_output=True, text=True, timeout=10
                )
                container_status[container] = container in result.stdout
            except Exception:
                container_status[container] = False
        
        # Mostrar resumen
        logger.info("\n" + "="*50)
        logger.info("📋 ESTADO DEL SISTEMA")
        logger.info("="*50)
        
        services = [
            ('PostgreSQL', postgres_ok),
            ('Redis', redis_ok),
        ]
        
        for name, status in services:
            icon = "✅" if status else "❌"
            logger.info(f"{icon} {name}: {'OK' if status else 'ERROR'}")
        
        logger.info("\n🐳 Contenedores:")
        for container, running in container_status.items():
            icon = "✅" if running else "❌"
            logger.info(f"{icon} {container}: {'Ejecutándose' if running else 'Detenido'}")
        
        # Resultado general
        all_good = all([postgres_ok, redis_ok] + list(container_status.values()))
        
        logger.info("\n" + "-"*50)
        if all_good:
            logger.info("🎉 ¡SISTEMA COMPLETAMENTE OPERATIVO!")
        else:
            logger.warning("⚠️ ALGUNOS SERVICIOS TIENEN PROBLEMAS")
        
        logger.info("="*50)
        
        return 0 if all_good else 1
        
    except Exception as e:
        logger.error(f"💥 Error inesperado: {e}")
        return 1

def cmd_interactive(args):
    """Comando interactivo"""
    logger.info("🎮 Iniciando modo interactivo...")
    
    try:
        tester = ConnectionTester()
        tester.interactive_test()
        return 0
        
    except Exception as e:
        logger.error(f"💥 Error inesperado: {e}")
        return 1

def main():
    """Función principal"""
    # Configurar entorno
    setup_environment()
    
    # Crear parser principal
    parser = argparse.ArgumentParser(
        description="Sistema de Agentes - Gestión de Base de Datos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Inicialización completa
  %(prog)s init
  
  # Inicialización con configuración personalizada
  %(prog)s init --host localhost --port 5432
  
  # Probar todos los servicios
  %(prog)s test
  
  # Probar servicio específico
  %(prog)s test --service postgres
  
  # Ver estado del sistema
  %(prog)s status
  
  # Modo interactivo
  %(prog)s interactive
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # Comando init
    init_parser = subparsers.add_parser('init', help='Inicializar base de datos')
    init_parser.add_argument('--host', help='Host de PostgreSQL')
    init_parser.add_argument('--port', type=int, help='Puerto de PostgreSQL')
    init_parser.add_argument('--database', help='Nombre de la base de datos')
    init_parser.add_argument('--user', help='Usuario de PostgreSQL')
    init_parser.add_argument('--password', help='Contraseña de PostgreSQL')
    
    # Comando test
    test_parser = subparsers.add_parser('test', help='Probar conectividad')
    test_parser.add_argument('--service', choices=['postgres', 'redis', 'api'], 
                           help='Servicio específico a probar')
    
    # Comando status
    status_parser = subparsers.add_parser('status', help='Ver estado del sistema')
    
    # Comando interactive
    interactive_parser = subparsers.add_parser('interactive', help='Modo interactivo')
    
    # Parsear argumentos
    args = parser.parse_args()
    
    # Verificar si se proporcionó un comando
    if not args.command:
        parser.print_help()
        return 1
    
    # Ejecutar comando
    command_map = {
        'init': cmd_init,
        'test': cmd_test,
        'status': cmd_status,
        'interactive': cmd_interactive
    }
    
    return command_map[args.command](args)

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n⏹️ Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Error inesperado: {e}")
        sys.exit(1)