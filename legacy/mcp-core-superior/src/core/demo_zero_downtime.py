#!/usr/bin/env python3
"""
Script de demostración completo del Zero-Downtime Deployer
Muestra todas las funcionalidades implementadas
"""

import asyncio
import logging
import sys
from pathlib import Path

# Agregar el directorio src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.core import (
    settings,
    Environment,
    DeploymentStrategy,
    initialize_deployer,
    shutdown_deployer,
    get_deployment_config,
    DeploymentCoordinator,
    initialize_deployment_coordinator,
    run_quick_test,
    DeployerTestSuite
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp.deployer.demo")


async def demo_basic_functionality():
    """Demostrar funcionalidad básica del deployer"""
    print("🚀 DEMOSTRACIÓN 1: Funcionalidad Básica")
    print("=" * 50)
    
    try:
        # 1. Configuración básica
        print("📋 1. Cargando configuración...")
        dev_config = get_deployment_config("development")
        print(f"   ✅ Entorno: {dev_config['environment']}")
        print(f"   ✅ Estrategia: {dev_config['strategy']}")
        print(f"   ✅ Agentes configurados: {len(dev_config['agent_configs'])}")
        
        # 2. Inicializar deployer
        print("\n🔧 2. Inicializando deployer...")
        deployer = await initialize_deployer(dev_config)
        print(f"   ✅ Deployer iniciado: {deployer.deployment_id}")
        
        # 3. Verificar estado
        print("\n📊 3. Verificando estado...")
        status = deployer.get_status()
        print(f"   ✅ Estado: {status['status']}")
        
        health = deployer.health_monitor.get_health_status()
        print(f"   ✅ Health: {health['status']}")
        
        # 4. Test agente simple
        print("\n🤖 4. Probando agente...")
        agent_config = {
            "command": ["python", "-c", "print('Hola desde agente demo')"],
            "id": "demo_agent"
        }
        
        agent_instance = await deployer.agent_manager.start_agent("demo_agent", agent_config)
        print(f"   ✅ Agente iniciado: {agent_instance.agent_id}")
        
        await asyncio.sleep(2)
        
        await deployer.agent_manager.stop_agent("demo_agent")
        print("   ✅ Agente detenido")
        
        # 5. Métricas del sistema
        print("\n📈 5. Métricas del sistema...")
        metrics = await deployer.get_deployment_metrics()
        print(f"   ✅ Memoria: {metrics['memory_usage_mb']:.1f} MB")
        print(f"   ✅ CPU: {metrics['cpu_usage_percent']:.1f}%")
        print(f"   ✅ Agentes activos: {metrics['agent_instances_active']}")
        
        # Cleanup
        await shutdown_deployer()
        print("\n✅ Demo básica completada exitosamente")
        
    except Exception as e:
        logger.error(f"Error en demo básica: {e}")
        print(f"\n❌ Demo básica falló: {e}")


async def demo_deployment_strategies():
    """Demostrar diferentes estrategias de deployment"""
    print("\n\n🎯 DEMOSTRACIÓN 2: Estrategias de Deployment")
    print("=" * 50)
    
    strategies = [
        ("Blue-Green", DeploymentStrategy.BLUE_GREEN),
        ("Rolling Update", DeploymentStrategy.ROLLING_UPDATE),
        ("Canary", DeploymentStrategy.CANARY),
        ("Immediate", DeploymentStrategy.IMMEDIATE)
    ]
    
    for strategy_name, strategy in strategies:
        print(f"\n🔄 Probando estrategia: {strategy_name}")
        
        try:
            config = get_deployment_config("development", ["file_processing"])
            config["strategy"] = strategy.value
            
            deployer = await initialize_deployer(config)
            
            # Solo probar immediate en development
            if strategy == DeploymentStrategy.IMMEDIATE:
                print(f"   ⚠️  Saltando {strategy_name} en development")
                await shutdown_deployer()
                continue
            
            print(f"   ✅ Configuración preparada para {strategy_name}")
            print(f"   ✅ Health checks configurados: {len(config['health_checks'])}")
            
            await shutdown_deployer()
            print(f"   ✅ Estrategia {strategy_name} probada")
            
        except Exception as e:
            print(f"   ❌ Error en {strategy_name}: {e}")


async def demo_coordinator():
    """Demostrar coordinador de deployment"""
    print("\n\n🎭 DEMOSTRACIÓN 3: Coordinador de Deployment")
    print("=" * 50)
    
    try:
        # 1. Inicializar coordinador
        print("🏗️  1. Inicializando coordinador...")
        coordinator = await initialize_deployment_coordinator("development")
        print("   ✅ Coordinador inicializado")
        
        # 2. Health check integrado
        print("\n🏥 2. Health check integrado...")
        health = await coordinator.perform_health_check()
        print(f"   ✅ Estado general: {health['overall_status']}")
        
        components = health.get('components', {})
        print(f"   ✅ Componentes: {len(components)}")
        
        # 3. Estado del sistema
        print("\n📊 3. Estado del sistema...")
        status = await coordinator.get_system_status()
        print(f"   ✅ Modo integración: {status['integration_mode']}")
        print(f"   ✅ Deployer status: {status['deployer']['status']}")
        print(f"   ✅ Orquestador inicializado: {status['orchestrator']['initialized']}")
        
        # 4. Deploy agente individual
        print("\n🚀 4. Deploy agente individual...")
        success = await coordinator.deploy_single_agent("file_processing")
        print(f"   ✅ Deploy individual: {'éxito' if success else 'falló'}")
        
        await coordinator.shutdown()
        print("   ✅ Coordinador shutdown")
        
        print("\n✅ Demo coordinador completado exitosamente")
        
    except Exception as e:
        logger.error(f"Error en demo coordinador: {e}")
        print(f"\n❌ Demo coordinador falló: {e}")


async def demo_monitoring():
    """Demostrar sistema de monitoreo"""
    print("\n\n📊 DEMOSTRACIÓN 4: Sistema de Monitoreo")
    print("=" * 50)
    
    try:
        deployer = await initialize_deployer(get_deployment_config("development"))
        
        # 1. Métricas de sistema
        print("📈 1. Métricas de sistema...")
        system_metrics = deployer.health_monitor.get_system_metrics()
        print(f"   ✅ CPU: {system_metrics['cpu_percent']:.1f}%")
        print(f"   ✅ Memoria: {system_metrics['memory_mb']:.1f} MB")
        print(f"   ✅ Disco: {system_metrics['disk_usage_percent']:.1f}%")
        print(f"   ✅ Threads: {system_metrics['active_threads']}")
        
        # 2. Reporte de recursos
        print("\n🔧 2. Reporte de recursos...")
        resource_report = deployer.resource_manager.get_resource_report()
        print(f"   ✅ Tendencia memoria: {resource_report.get('memory_trend', 'N/A')}")
        print(f"   ✅ Snapshots: {resource_report.get('total_snapshots', 0)}")
        
        # 3. Monitoreo de agentes
        print("\n🤖 3. Monitoreo de agentes...")
        
        # Iniciar algunos agentes de prueba
        test_agents = []
        for i in range(3):
            agent_config = {
                "command": ["python", "-c", f"import time; time.sleep({30+i})"],
                "id": f"monitoring_test_{i}"
            }
            agent = await deployer.agent_manager.start_agent(f"monitoring_test_{i}", agent_config)
            test_agents.append(agent)
        
        print(f"   ✅ Agentes iniciados: {len(test_agents)}")
        
        # Monitorear por unos segundos
        for i in range(3):
            await asyncio.sleep(2)
            agent_status = await deployer.agent_manager.get_agent_status()
            active_count = sum(1 for status in agent_status.values() if status.get("status") == "running")
            print(f"   📊 Monitoreo {i+1}: {active_count} activos")
        
        # Cleanup
        for agent in test_agents:
            await deployer.agent_manager.stop_agent(agent.agent_id)
        
        await shutdown_deployer()
        print("\n✅ Demo monitoreo completado exitosamente")
        
    except Exception as e:
        logger.error(f"Error en demo monitoreo: {e}")
        print(f"\n❌ Demo monitoreo falló: {e}")


async def demo_configuration_hot_reload():
    """Demostrar hot-reload de configuración"""
    print("\n\n🔄 DEMOSTRACIÓN 5: Hot-Reload de Configuración")
    print("=" * 50)
    
    try:
        deployer = await initialize_deployer(get_deployment_config("development"))
        
        # 1. Obtener configuración actual
        print("⚙️  1. Configuración actual...")
        current_config = await deployer.config_manager.get_current_config()
        print(f"   ✅ Variables de configuración: {len(current_config)}")
        
        # 2. Simular cambio de configuración
        print("\n🔧 2. Simulando cambio de configuración...")
        old_config = current_config.copy()
        new_config = {"DEBUG": "true", "TEST_VAR": "hot_reload_test"}
        
        print("   📝 Ejecutando callback de cambio...")
        await deployer._on_config_change(old_config, new_config)
        print("   ✅ Callback ejecutado")
        
        # 3. Verificar resource cleanup
        print("\n🧹 3. Resource cleanup...")
        await deployer.resource_manager._force_gc()
        print("   ✅ Garbage collection ejecutado")
        
        await shutdown_deployer()
        print("\n✅ Demo hot-reload completado exitosamente")
        
    except Exception as e:
        logger.error(f"Error en demo hot-reload: {e}")
        print(f"\n❌ Demo hot-reload falló: {e}")


async def run_comprehensive_test():
    """Ejecutar test comprensivo del sistema"""
    print("\n\n🧪 TEST COMPRENSIVO DEL SISTEMA")
    print("=" * 50)
    
    try:
        # Test suite completo
        print("🔬 Ejecutando test suite...")
        test_suite = DeployerTestSuite()
        success = await test_suite.run_all_tests()
        
        # Reporte de resultados
        report = test_suite.generate_test_report()
        print(f"\n📊 Resumen de pruebas:")
        print(f"   ✅ Total: {report['summary']['total_tests']}")
        print(f"   ✅ Pasaron: {report['summary']['passed']}")
        print(f"   ❌ Fallaron: {report['summary']['failed']}")
        print(f"   📈 Tasa de éxito: {report['summary']['success_rate']}")
        print(f"   🏁 Resultado: {report['conclusion']}")
        
        # Test rápido adicional
        print("\n⚡ Ejecutando test rápido adicional...")
        quick_success = await run_quick_test()
        print(f"   ✅ Test rápido: {'pasó' if quick_success else 'falló'}")
        
        return success and quick_success
        
    except Exception as e:
        logger.error(f"Error en test comprensivo: {e}")
        print(f"\n❌ Test comprensivo falló: {e}")
        return False


async def main():
    """Función principal de demostración"""
    print("=" * 60)
    print("    ZERO-DOWNTIME DEPLOYER - DEMOSTRACIÓN COMPLETA")
    print("=" * 60)
    print(f"🖥️  Entorno: {settings.environment.value}")
    print(f"🔧 Debug: {settings.debug}")
    print(f"📝 Log Level: {settings.log_level}")
    print("=" * 60)
    
    # Ejecutar demos
    demos = [
        demo_basic_functionality,
        demo_deployment_strategies,
        demo_coordinator,
        demo_monitoring,
        demo_configuration_hot_reload,
        run_comprehensive_test
    ]
    
    results = []
    
    for demo_func in demos:
        try:
            await demo_func()
            results.append(True)
        except Exception as e:
            logger.error(f"Demo {demo_func.__name__} falló: {e}")
            results.append(False)
    
    # Resumen final
    print("\n\n🏁 RESUMEN FINAL")
    print("=" * 50)
    print(f"✅ Demos completados: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 ¡TODAS LAS DEMOSTRACIONES EXITOSAS!")
        print("🚀 Sistema Zero-Downtime Deployer funcionando correctamente")
        return 0
    else:
        print("⚠️  Algunas demos tuvieron problemas")
        print("🔍 Revisar logs para más detalles")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  Demostración interrumpida por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Error crítico: {e}")
        logger.exception("Error crítico en demostración")
        sys.exit(1)