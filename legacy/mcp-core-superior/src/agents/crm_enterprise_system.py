"""
Configuración Completa del Sistema CRM Empresarial
Integración unificada de Salesforce, HubSpot, Pipedrive y Zoho CRM
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Importar todos los módulos CRM
from .crm_agents import (
    CRMIntegrationManager, CRMCredentials, CRMClientFactory,
    SalesforceAgent, HubSpotAgent, PipedriveAgent, ZohoCRMAgent,
    CRMDataSyncAgent, CRMAnalyticsAgent
)
from .crm_api_endpoints import app, CRM_API_ENDPOINTS, CRM_WEBHOOKS
from .crm_workflows import WorkflowManager, create_sales_workflows, create_marketing_workflows
from .crm_auth_security import (
    CRMAuthManager, SecurityConfig, AuthCredentials,
    CRM_SECURITY_CONFIGS
)


class CRMPlatform(Enum):
    """Plataformas CRM soportadas"""
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    PIPEDRIVE = "pipedrive"
    ZOHO = "zoho"


@dataclass
class CRMConfiguration:
    """Configuración principal del sistema CRM"""
    # Configuración general
    enabled_platforms: List[CRMPlatform]
    default_sync_interval_minutes: int = 15
    max_concurrent_operations: int = 10
    batch_size: int = 100
    
    # Configuración de seguridad
    encryption_enabled: bool = True
    jwt_enabled: bool = True
    session_timeout_minutes: int = 30
    rate_limit_requests_per_hour: int = 1000
    
    # Configuración de workflows
    workflows_enabled: bool = True
    auto_assign_leads: bool = True
    auto_follow_up: bool = True
    lead_scoring_enabled: bool = True
    
    # Configuración de sincronización
    sync_on_create: bool = True
    sync_on_update: bool = True
    sync_conflicts_resolution: str = "source_wins"  # source_wins, target_wins, manual
    
    # Configuración de analytics
    analytics_enabled: bool = True
    real_time_metrics: bool = True
    reporting_frequency_hours: int = 24
    
    # Configuración de notificaciones
    email_notifications: bool = True
    slack_notifications: bool = False
    webhook_notifications: bool = True
    
    # Configuración de backup
    data_backup_enabled: bool = True
    backup_retention_days: int = 30
    auto_cleanup_old_records: bool = False


class CRMEnterpriseSystem:
    """Sistema CRM Empresarial completo"""
    
    def __init__(self, config: CRMConfiguration):
        self.config = config
        self.logger = logging.getLogger("crm_enterprise_system")
        
        # Componentes principales
        self.integration_manager = CRMIntegrationManager()
        self.auth_manager = None
        self.workflow_manager = None
        self.analytics_agent = CRMAnalyticsAgent()
        self.data_sync_agent = CRMDataSyncAgent()
        
        # Estado del sistema
        self.is_initialized = False
        self.platform_status = {}
        self.system_metrics = {}
        
        # Configuración de seguridad
        self.security_config = SecurityConfig(
            encryption_key="enterprise_encryption_key_2025",
            jwt_secret_key="enterprise_jwt_secret_2025",
            token_expiry_hours=24,
            session_timeout_minutes=config.session_timeout_minutes,
            rate_limit_requests=config.rate_limit_requests_per_hour,
            redis_url="redis://localhost:6379"
        )
        
        self.logger.info("Sistema CRM Empresarial inicializado")
    
    async def initialize(self) -> bool:
        """Inicializar el sistema completo"""
        try:
            self.logger.info("Iniciando inicialización del sistema CRM...")
            
            # 1. Inicializar sistema de autenticación
            self.auth_manager = CRMAuthManager(self.security_config)
            await self._initialize_authentication()
            
            # 2. Configurar workflows
            if self.config.workflows_enabled:
                self.workflow_manager = WorkflowManager()
                await self._initialize_workflows()
            
            # 3. Inicializar plataformas CRM
            await self._initialize_platforms()
            
            # 4. Configurar APIs y webhooks
            await self._setup_apis_and_webhooks()
            
            # 5. Inicializar componentes de analytics
            if self.config.analytics_enabled:
                await self._initialize_analytics()
            
            # 6. Configurar tareas automáticas
            await self._setup_automated_tasks()
            
            self.is_initialized = True
            self.logger.info("Sistema CRM Empresarial inicializado correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error en inicialización: {str(e)}")
            return False
    
    async def _initialize_authentication(self):
        """Inicializar sistema de autenticación"""
        # Registrar plataformas en el sistema de auth
        for platform_config in CRM_SECURITY_CONFIGS.items():
            platform, config = platform_config
            self.auth_manager.register_platform(platform, config)
        
        self.logger.info("Sistema de autenticación configurado")
    
    async def _initialize_workflows(self):
        """Inicializar workflows por defecto"""
        await self.workflow_manager.initialize_default_workflows()
        self.logger.info("Workflows inicializados")
    
    async def _initialize_platforms(self):
        """Inicializar plataformas CRM"""
        for platform_enum in self.config.enabled_platforms:
            platform = platform_enum.value
            
            try:
                # Crear credenciales de ejemplo (en producción, cargar desde BD segura)
                credentials = self._create_platform_credentials(platform)
                
                # Inicializar plataforma
                success = await self.integration_manager.initialize_platform(platform, credentials)
                
                self.platform_status[platform] = {
                    "status": "connected" if success else "failed",
                    "last_sync": datetime.now().isoformat(),
                    "initialized": success
                }
                
                if success:
                    self.logger.info(f"Plataforma {platform} inicializada")
                else:
                    self.logger.error(f"Error inicializando {platform}")
                    
            except Exception as e:
                self.logger.error(f"Error configurando {platform}: {str(e)}")
                self.platform_status[platform] = {
                    "status": "error",
                    "error": str(e),
                    "initialized": False
                }
    
    def _create_platform_credentials(self, platform: str) -> CRMCredentials:
        """Crear credenciales para plataforma (ejemplo)"""
        if platform == "salesforce":
            return CRMCredentials(
                platform=platform,
                client_id="your_salesforce_client_id",
                client_secret="your_salesforce_client_secret",
                instance_url="https://your-instance.salesforce.com"
            )
        elif platform == "hubspot":
            return CRMCredentials(
                platform=platform,
                client_id="your_hubspot_client_id",
                client_secret="your_hubspot_client_secret",
                api_key="your_hubspot_api_key"
            )
        elif platform == "pipedrive":
            return CRMCredentials(
                platform=platform,
                api_key="your_pipedrive_api_key",
                username="your_pipedrive_username"
            )
        elif platform == "zoho":
            return CRMCredentials(
                platform=platform,
                client_id="your_zoho_client_id",
                client_secret="your_zoho_client_secret"
            )
        else:
            raise ValueError(f"Plataforma no soportada: {platform}")
    
    async def _setup_apis_and_webhooks(self):
        """Configurar APIs y webhooks"""
        # Los endpoints ya están definidos en crm_api_endpoints.py
        self.logger.info("APIs y webhooks configurados")
    
    async def _initialize_analytics(self):
        """Inicializar sistema de analytics"""
        # El analytics agent ya está inicializado
        self.logger.info("Sistema de analytics inicializado")
    
    async def _setup_automated_tasks(self):
        """Configurar tareas automáticas"""
        tasks = [
            self._periodic_sync_task(),
            self._cleanup_task(),
            self._metrics_collection_task()
        ]
        
        # Ejecutar tareas en background
        for task in tasks:
            asyncio.create_task(task)
        
        self.logger.info("Tareas automáticas configuradas")
    
    async def _periodic_sync_task(self):
        """Tarea de sincronización periódica"""
        while True:
            try:
                if self.is_initialized and self.config.sync_on_update:
                    await self.run_scheduled_sync()
                await asyncio.sleep(self.config.default_sync_interval_minutes * 60)
            except Exception as e:
                self.logger.error(f"Error en sincronización periódica: {str(e)}")
                await asyncio.sleep(300)  # Esperar 5 minutos antes de reintentar
    
    async def _cleanup_task(self):
        """Tarea de limpieza de datos"""
        while True:
            try:
                if self.config.auto_cleanup_old_records:
                    await self._cleanup_old_data()
                await asyncio.sleep(86400)  # Ejecutar cada 24 horas
            except Exception as e:
                self.logger.error(f"Error en limpieza: {str(e)}")
                await asyncio.sleep(3600)  # Esperar 1 hora
    
    async def _metrics_collection_task(self):
        """Tarea de recolección de métricas"""
        while True:
            try:
                if self.config.analytics_enabled:
                    await self._collect_system_metrics()
                await asyncio.sleep(300)  # Cada 5 minutos
            except Exception as e:
                self.logger.error(f"Error recolectando métricas: {str(e)}")
                await asyncio.sleep(300)
    
    async def create_lead(self, platform: str, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear lead en plataforma específica"""
        try:
            # Ejecutar operación
            result = await self.integration_manager.execute_operation(
                platform, "create_lead", lead_data
            )
            
            # Trigger workflows si está habilitado
            if self.config.workflows_enabled and result.get("success"):
                await self.workflow_manager.trigger_lead_created(lead_data)
            
            # Sincronizar si está configurado
            if self.config.sync_on_create:
                await self._sync_lead_to_other_platforms(platform, lead_data)
            
            self.logger.info(f"Lead creado en {platform}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error creando lead en {platform}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def create_opportunity(self, platform: str, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear oportunidad en plataforma específica"""
        try:
            result = await self.integration_manager.execute_operation(
                platform, "create_opportunity", opportunity_data
            )
            
            # Trigger workflows
            if self.config.workflows_enabled and result.get("success"):
                await self.workflow_manager.trigger_opportunity_created(opportunity_data)
            
            # Sincronizar a otras plataformas
            if self.config.sync_on_create:
                await self._sync_opportunity_to_other_platforms(platform, opportunity_data)
            
            self.logger.info(f"Oportunidad creada en {platform}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error creando oportunidad en {platform}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def run_full_sync(self, sync_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecutar sincronización completa entre plataformas"""
        try:
            if not sync_config:
                sync_config = {
                    "field_mappings": {
                        "name": "name",
                        "email": "email",
                        "company": "company",
                        "phone": "phone"
                    },
                    "sync_conflicts": self.config.sync_conflicts_resolution
                }
            
            result = await self.integration_manager.sync_all_platforms(sync_config)
            
            self.logger.info("Sincronización completa ejecutada")
            return result
            
        except Exception as e:
            self.logger.error(f"Error en sincronización completa: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def run_scheduled_sync(self):
        """Ejecutar sincronización programada"""
        sync_config = {
            "incremental": True,
            "since_last_sync": True,
            "field_mappings": {"auto_detect": True}
        }
        
        return await self.run_full_sync(sync_config)
    
    async def generate_consolidated_report(self, date_range: Dict[str, str] = None) -> Dict[str, Any]:
        """Generar reporte consolidado de todas las plataformas"""
        try:
            if not date_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                date_range = {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            
            # Generar reporte usando analytics agent
            report = await self.analytics_agent.generate_sales_report(
                date_range, 
                [p.value for p in self.config.enabled_platforms]
            )
            
            # Añadir métricas del sistema
            report["system_metrics"] = self.system_metrics
            report["platform_status"] = self.platform_status
            
            self.logger.info("Reporte consolidado generado")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generando reporte: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _sync_lead_to_other_platforms(self, source_platform: str, lead_data: Dict[str, Any]):
        """Sincronizar lead a otras plataformas"""
        for platform_enum in self.config.enabled_platforms:
            platform = platform_enum.value
            if platform != source_platform:
                try:
                    # Transformar datos según la plataforma
                    transformed_data = self._transform_lead_data(lead_data, platform)
                    await self.integration_manager.execute_operation(
                        platform, "create_lead", transformed_data
                    )
                except Exception as e:
                    self.logger.error(f"Error sincronizando lead a {platform}: {str(e)}")
    
    async def _sync_opportunity_to_other_platforms(self, source_platform: str, opportunity_data: Dict[str, Any]):
        """Sincronizar oportunidad a otras plataformas"""
        for platform_enum in self.config.enabled_platforms:
            platform = platform_enum.value
            if platform != source_platform:
                try:
                    transformed_data = self._transform_opportunity_data(opportunity_data, platform)
                    await self.integration_manager.execute_operation(
                        platform, "create_opportunity", transformed_data
                    )
                except Exception as e:
                    self.logger.error(f"Error sincronizando oportunidad a {platform}: {str(e)}")
    
    def _transform_lead_data(self, lead_data: Dict[str, Any], target_platform: str) -> Dict[str, Any]:
        """Transformar datos de lead para plataforma destino"""
        # Mapeos básicos por plataforma
        mappings = {
            "salesforce": {
                "first_name": "FirstName",
                "last_name": "LastName",
                "company": "Company",
                "email": "Email"
            },
            "hubspot": {
                "firstname": "firstname",
                "lastname": "lastname",
                "company": "company",
                "email": "email"
            },
            "pipedrive": {
                "name": "name",
                "email": "email"
            },
            "zoho": {
                "First_Name": "First_Name",
                "Last_Name": "Last_Name",
                "Company": "Company",
                "Email": "Email"
            }
        }
        
        if target_platform in mappings:
            transformed = {}
            source_mapping = mappings[target_platform]
            for source_field, target_field in source_mapping.items():
                if source_field in lead_data:
                    transformed[target_field] = lead_data[source_field]
            return transformed
        
        return lead_data.copy()
    
    def _transform_opportunity_data(self, opp_data: Dict[str, Any], target_platform: str) -> Dict[str, Any]:
        """Transformar datos de oportunidad para plataforma destino"""
        # Mapeos básicos por plataforma
        mappings = {
            "salesforce": {
                "name": "Name",
                "amount": "Amount",
                "stage": "StageName",
                "close_date": "CloseDate"
            },
            "hubspot": {
                "dealname": "dealname",
                "amount": "amount",
                "pipeline": "pipeline",
                "dealstage": "dealstage"
            },
            "pipedrive": {
                "title": "title",
                "value": "value",
                "currency": "currency"
            },
            "zoho": {
                "Potential_Name": "Potential_Name",
                "Amount": "Amount",
                "Stage": "Stage",
                "Closing_Date": "Closing_Date"
            }
        }
        
        if target_platform in mappings:
            transformed = {}
            source_mapping = mappings[target_platform]
            for source_field, target_field in source_mapping.items():
                if source_field in opp_data:
                    transformed[target_field] = opp_data[source_field]
            return transformed
        
        return opp_data.copy()
    
    async def _cleanup_old_data(self):
        """Limpiar datos antiguos"""
        # Implementar limpieza de datos antiguos
        self.logger.info("Limpieza de datos antiguos ejecutada")
    
    async def _collect_system_metrics(self):
        """Recolectar métricas del sistema"""
        self.system_metrics = {
            "timestamp": datetime.now().isoformat(),
            "active_platforms": len([p for p in self.platform_status.values() if p.get("status") == "connected"]),
            "total_platforms": len(self.config.enabled_platforms),
            "workflows_active": self.workflow_manager is not None,
            "sync_enabled": self.config.sync_on_create or self.config.sync_on_update
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema"""
        return {
            "system_status": "operational" if self.is_initialized else "initializing",
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "enabled_platforms": [p.value for p in self.config.enabled_platforms],
                "sync_enabled": self.config.sync_on_create or self.config.sync_on_update,
                "workflows_enabled": self.config.workflows_enabled,
                "analytics_enabled": self.config.analytics_enabled
            },
            "platform_status": self.platform_status,
            "system_metrics": self.system_metrics
        }


# Configuración predefinidas para diferentes escenarios
def create_sales_heavy_config() -> CRMConfiguration:
    """Configuración para empresas enfocadas en ventas"""
    return CRMConfiguration(
        enabled_platforms=[CRMPlatform.SALESFORCE, CRMPlatform.PIPEDRIVE],
        auto_assign_leads=True,
        lead_scoring_enabled=True,
        workflows_enabled=True,
        analytics_enabled=True,
        real_time_metrics=True
    )


def create_marketing_heavy_config() -> CRMConfiguration:
    """Configuración para empresas enfocadas en marketing"""
    return CRMConfiguration(
        enabled_platforms=[CRMPlatform.HUBSPOT, CRMPlatform.ZOHO],
        workflows_enabled=True,
        sync_conflicts_resolution="source_wins",
        email_notifications=True,
        reporting_frequency_hours=12
    )


def create_enterprise_config() -> CRMConfiguration:
    """Configuración para grandes empresas"""
    return CRMConfiguration(
        enabled_platforms=list(CRMPlatform),
        max_concurrent_operations=50,
        batch_size=500,
        workflows_enabled=True,
        analytics_enabled=True,
        real_time_metrics=True,
        data_backup_enabled=True,
        auto_cleanup_old_records=True,
        rate_limit_requests_per_hour=10000
    )


# Demo completo del sistema
async def demo_enterprise_crm_system():
    """Demostración completa del sistema CRM empresarial"""
    
    print("=== DEMO: Sistema CRM Empresarial ===")
    
    # 1. Crear configuración
    config = create_enterprise_config()
    system = CRMEnterpriseSystem(config)
    
    # 2. Inicializar sistema
    print("1. Inicializando sistema...")
    init_success = await system.initialize()
    print(f"   Inicialización: {'✓' if init_success else '✗'}")
    
    if not init_success:
        print("Error en inicialización. Abortando demo.")
        return
    
    # 3. Mostrar estado del sistema
    print("\n2. Estado del sistema:")
    status = system.get_system_status()
    print(f"   Estado: {status['system_status']}")
    print(f"   Plataformas activas: {status['system_metrics']['active_platforms']}/{status['system_metrics']['total_platforms']}")
    
    # 4. Crear lead de ejemplo
    print("\n3. Creando lead de ejemplo...")
    lead_data = {
        "first_name": "Juan",
        "last_name": "Pérez",
        "company": "TechCorp Solutions",
        "email": "juan.perez@techcorp.com",
        "phone": "+34 123 456 789",
        "title": "Director de Ventas"
    }
    
    lead_result = await system.create_lead("salesforce", lead_data)
    print(f"   Resultado: {lead_result}")
    
    # 5. Crear oportunidad
    print("\n4. Creando oportunidad...")
    opportunity_data = {
        "name": "Licencia Enterprise TechCorp",
        "stage": "Qualification",
        "amount": 75000,
        "close_date": "2025-12-31",
        "description": "Venta de licencia anual para 500 usuarios"
    }
    
    opp_result = await system.create_opportunity("salesforce", opportunity_data)
    print(f"   Resultado: {opp_result}")
    
    # 6. Ejecutar sincronización
    print("\n5. Ejecutando sincronización...")
    sync_result = await system.run_full_sync()
    print(f"   Sincronización completada: {sync_result.get('success', False)}")
    
    # 7. Generar reporte
    print("\n6. Generando reporte consolidado...")
    date_range = {
        "start": (datetime.now() - timedelta(days=7)).isoformat(),
        "end": datetime.now().isoformat()
    }
    
    report = await system.generate_consolidated_report(date_range)
    print(f"   Reporte generado: {report.get('success', False)}")
    
    # 8. Mostrar métricas finales
    print("\n7. Métricas del sistema:")
    final_status = system.get_system_status()
    for platform, platform_info in final_status['platform_status'].items():
        status_icon = "✓" if platform_info.get('status') == 'connected' else "✗"
        print(f"   {platform}: {status_icon} {platform_info.get('status', 'unknown')}")
    
    print("\n=== DEMO COMPLETADO ===")


if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ejecutar demo
    asyncio.run(demo_enterprise_crm_system())