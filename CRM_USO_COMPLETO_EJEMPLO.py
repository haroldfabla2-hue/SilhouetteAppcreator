"""
Uso Completo del Sistema CRM Empresarial
Ejemplo práctico de integración de todos los componentes
"""

import asyncio
import json
from datetime import datetime

# Importar sistema CRM completo
try:
    from mcp_core_superior.src.agents import (
        CRMEnterpriseSystem, 
        create_enterprise_config,
        CRMCredentials,
        CRMIntegrationManager,
        WorkflowManager
    )
    from mcp_core_superior.src.agents.crm_enterprise_system import CRMPlatform, CRMConfiguration
    
    # Configuración para el sistema
    config = create_enterprise_config()
    
    print("=== Sistema CRM Empresarial - Uso Completo ===")
    print(f"Plataformas habilitadas: {[p.value for p in config.enabled_platforms]}")
    print(f"Workflows: {config.workflows_enabled}")
    print(f"Analytics: {config.analytics_enabled}")
    
    # Crear instancia del sistema
    crm_system = CRMEnterpriseSystem(config)
    
    # Ejemplo de uso completo
    async def demo_crm_usage():
        """Demostración de uso completo"""
        
        print("\n🚀 Inicializando Sistema CRM...")
        success = await crm_system.initialize()
        
        if success:
            print("✅ Sistema inicializado correctamente")
            
            # 1. Crear lead
            print("\n👥 1. Creando Lead en Salesforce")
            lead_data = {
                "first_name": "Ana",
                "last_name": "García", 
                "company": "TechCorp",
                "email": "ana@techcorp.com",
                "phone": "+34 123 456 789"
            }
            
            result = await crm_system.create_lead("salesforce", lead_data)
            print(f"   Resultado: {result}")
            
            # 2. Crear oportunidad
            print("\n💼 2. Creando Oportunidad en HubSpot")
            opp_data = {
                "dealname": "Licencia Enterprise",
                "amount": 50000,
                "dealstage": "qualifiedtobuy",
                "pipeline": "default"
            }
            
            result = await crm_system.create_opportunity("hubspot", opp_data)
            print(f"   Resultado: {result}")
            
            # 3. Sincronizar datos
            print("\n🔄 3. Sincronizando Plataformas")
            sync_result = await crm_system.run_full_sync()
            print(f"   Sincronización: {sync_result.get('success', False)}")
            
            # 4. Generar reporte
            print("\n📊 4. Generando Reporte Consolidado")
            date_range = {
                "start": (datetime.now() - timedelta(days=7)).isoformat(),
                "end": datetime.now().isoformat()
            }
            
            report = await crm_system.generate_consolidated_report(date_range)
            print(f"   Reporte generado: {report.get('success', False)}")
            
            # 5. Estado del sistema
            print("\n📋 5. Estado del Sistema")
            status = crm_system.get_system_status()
            print(f"   Estado: {status['system_status']}")
            print(f"   Plataformas activas: {status['system_metrics']['active_platforms']}")
            
        else:
            print("❌ Error inicializando sistema")
    
    # Ejecutar demo
    asyncio.run(demo_crm_usage())
    
except ImportError as e:
    print(f"❌ Error importando módulos CRM: {e}")
    print("⚠️  Asegúrate de que todos los archivos CRM estén en su lugar")
    
except Exception as e:
    print(f"❌ Error durante la ejecución: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50)
print("✅ Integración CRM Empresarial Completada")
print("="*50)