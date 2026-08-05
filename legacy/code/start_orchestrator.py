#!/usr/bin/env python3
"""
Script de inicio para SilhouetteMCP Integration Orchestrator
===========================================================

Script simplificado para iniciar el orquestador de integración
de forma fácil y rápida.

Uso:
    python start_orchestrator.py

Opciones:
    --port PORT    Puerto para el servidor (default: 8025)
    --host HOST    Host para el servidor (default: 0.0.0.0)
    --help         Mostrar ayuda
"""

import argparse
import asyncio
import sys
import os

# Agregar el directorio actual al path para importaciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from silhouettemcp_integration_orchestrator import SilhouetteMCPIntegrationOrchestrator

def main():
    """Función principal del script de inicio"""
    parser = argparse.ArgumentParser(
        description="SilhouetteMCP Integration Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python start_orchestrator.py                    # Iniciar con configuración por defecto
  python start_orchestrator.py --port 9000       # Usar puerto personalizado
  python start_orchestrator.py --host 127.0.0.1  # Usar host local
        """
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8025,
        help='Puerto para el servidor (default: 8025)'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host para el servidor (default: 0.0.0.0)'
    )
    
    args = parser.parse_args()
    
    # Validar argumentos
    if not (1 <= args.port <= 65535):
        print("❌ Error: El puerto debe estar entre 1 y 65535")
        sys.exit(1)
    
    print("🚀 Iniciando SilhouetteMCP Integration Orchestrator...")
    print(f"📍 Configuración: {args.host}:{args.port}")
    
    # Configuración personalizada
    config = {
        'host': args.host,
        'port': args.port,
        'secret_key': 'silhouettemcp_secret_key_2025',
        'enable_websocket': True,
        'enable_monitoring': True,
        'enable_auto_scaling': True,
        'health_check_interval': 30,
        'auto_scaling_interval': 60,
        'monitoring_interval': 10
    }
    
    try:
        # Crear e iniciar orquestador
        orchestrator = SilhouetteMCPIntegrationOrchestrator(config)
        
        # Mostrar información de inicio
        print("\n" + "=" * 80)
        print("🎯 SilhouetteMCP Integration Orchestrator")
        print("=" * 80)
        print(f"🌐 API HTTP: http://{config['host']}:{config['port']}")
        print(f"🔗 WebSocket: ws://{config['host']}:{config['port']}/ws/{'{client_id}'}")
        print(f"📊 Métricas: http://{config['host']}:{config['port']}/metrics")
        print(f"❤️  Salud: http://{config['host']}:{config['port']}/health")
        print("=" * 80)
        print("📋 Servicios registrados:")
        print("  • silhouettemcp_core (8001)")
        print("  • silhouettemcp_server (8002)")
        print("  • enhanced_scalability (8010)")
        print("  • enhanced_security (8011)")
        print("  • hierarchical_architecture (8012)")
        print("  • robust_diagnostic (8013)")
        print("  • comprehensive_verification (8014)")
        print("  • expanded_content (8015)")
        print("  • expanded_finance (8016)")
        print("  • expanded_maps (8017)")
        print("  • expanded_research (8018)")
        print("  • expanded_social_travel (8019)")
        print("  • expanded_supabase (8020)")
        print("  • superior_allocator (8021)")
        print("  • comprehensive_diagnostic (8022)")
        print("  • enhanced_architecture (8023)")
        print("  • server_unified (8024)")
        print("=" * 80)
        print("⚡ Características habilitadas:")
        print("  ✅ Comunicación bidireccional WebSocket/HTTP")
        print("  ✅ Configuración automática de seguridad")
        print("  ✅ Auto-healing y load balancing")
        print("  ✅ Auto-scaling dinámico")
        print("  ✅ Endpoints unificados")
        print("  ✅ Monitoreo centralizado")
        print("=" * 80)
        print("⏹️  Presiona Ctrl+C para detener el orquestador")
        print("=" * 80)
        
        # Ejecutar orquestador
        orchestrator.run()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Deteniendo orquestador por solicitud del usuario...")
        print("✅ Orquestador detenido exitosamente")
    except Exception as e:
        print(f"\n❌ Error iniciando orquestador: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()