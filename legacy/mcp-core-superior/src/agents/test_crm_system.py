"""
Tests para el Sistema CRM Empresarial
Pruebas unitarias e integrales para todas las funcionalidades CRM
"""

import asyncio
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any

# Importar módulos CRM para testing
from crm_agents import (
    CRMIntegrationManager, CRMCredentials,
    SalesforceAgent, HubSpotAgent, PipedriveAgent, ZohoCRMAgent,
    CRMDataSyncAgent, CRMAnalyticsAgent
)
from crm_workflows import WorkflowManager, WorkflowTrigger
from crm_auth_security import CRMAuthManager, SecurityConfig
from crm_enterprise_system import CRMEnterpriseSystem, create_enterprise_config


class TestCRMIntegration:
    """Tests para integración CRM general"""
    
    @pytest.fixture
    async def integration_manager(self):
        """Fixture para manager de integración"""
        manager = CRMIntegrationManager()
        return manager
    
    @pytest.fixture
    def mock_credentials(self):
        """Fixture para credenciales de prueba"""
        return CRMCredentials(
            platform="salesforce",
            client_id="test_client_id",
            client_secret="test_client_secret",
            instance_url="https://test.salesforce.com"
        )
    
    @pytest.mark.asyncio
    async def test_salesforce_agent_initialization(self, mock_credentials):
        """Test inicialización agente Salesforce"""
        agent = SalesforceAgent(mock_credentials)
        
        # Mock del cliente
        with patch('aiohttp.ClientSession') as mock_session:
            mock_client = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_client
            
            await agent.initialize()
            
            assert agent.client is not None
            assert agent.credentials == mock_credentials
    
    @pytest.mark.asyncio
    async def test_hubspot_agent_initialization(self):
        """Test inicialización agente HubSpot"""
        credentials = CRMCredentials(
            platform="hubspot",
            client_id="test_client_id",
            client_secret="test_client_secret",
            api_key="test_api_key"
        )
        
        agent = HubSpotAgent(credentials)
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_client = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_client
            
            await agent.initialize()
            
            assert agent.client is not None
    
    @pytest.mark.asyncio
    async def test_create_lead_operations(self, integration_manager, mock_credentials):
        """Test operaciones de creación de leads"""
        # Registrar plataforma
        success = await integration_manager.initialize_platform("salesforce", mock_credentials)
        assert success
        
        # Datos de prueba
        lead_data = {
            "first_name": "Juan",
            "last_name": "Pérez",
            "company": "TechCorp",
            "email": "juan@techcorp.com"
        }
        
        # Ejecutar creación de lead
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 201
            mock_response.json.return_value = {"id": "lead_123", "success": True}
            mock_session.return_value.__aenter__.return_value = mock_response
            
            result = await integration_manager.execute_operation(
                "salesforce", "create_lead", lead_data
            )
            
            assert result["success"] is True
            assert "lead_id" in result
    
    @pytest.mark.asyncio
    async def test_data_sync_agent(self):
        """Test agente de sincronización"""
        sync_agent = CRMDataSyncAgent()
        
        sync_config = {
            "field_mappings": {
                "name": "name",
                "email": "email",
                "company": "company"
            }
        }
        
        # Mock del proceso de sincronización
        with patch.object(sync_agent, '_extract_data', return_value=[{"name": "Test"}]), \
             patch.object(sync_agent, '_transform_data', return_value=[{"name": "Test"}]), \
             patch.object(sync_agent, '_load_data', return_value={"loaded_records": 1}):
            
            result = await sync_agent.sync_between_platforms(
                "salesforce", "hubspot", sync_config
            )
            
            assert result["success"] is True
            assert "sync_job_id" in result


class TestWorkflows:
    """Tests para workflows automatizados"""
    
    @pytest.fixture
    def workflow_manager(self):
        """Fixture para manager de workflows"""
        return WorkflowManager()
    
    @pytest.mark.asyncio
    async def test_workflow_initialization(self, workflow_manager):
        """Test inicialización de workflows"""
        await workflow_manager.initialize_default_workflows()
        
        # Verificar que se inicializaron workflows
        assert len(workflow_manager.engine.workflows) > 0
    
    @pytest.mark.asyncio
    async def test_lead_created_workflow(self, workflow_manager):
        """Test workflow de lead creado"""
        await workflow_manager.initialize_default_workflows()
        
        lead_data = {
            "id": "lead_123",
            "name": "Juan Pérez",
            "email": "juan@techcorp.com",
            "source": "website",
            "company": "TechCorp"
        }
        
        execution_id = await workflow_manager.trigger_lead_created(lead_data)
        
        assert execution_id is not None
        assert "exec_" in execution_id
        
        # Esperar ejecución
        await asyncio.sleep(1)
        
        # Verificar estado
        status = workflow_manager.get_workflow_status(execution_id)
        assert status["status"] in ["completed", "running"]
    
    @pytest.mark.asyncio
    async def test_workflow_conditions(self):
        """Test evaluación de condiciones"""
        from crm_workflows import WorkflowCondition, WorkflowActionStep, WorkflowDefinition
        
        # Crear condición
        condition = WorkflowCondition(
            field="company_size",
            operator="equals",
            value="enterprise"
        )
        
        # Datos que cumplen la condición
        data = {"company_size": "enterprise", "budget": "high"}
        
        # Evaluar condición
        result = await WorkflowManager()._evaluate_conditions([condition], data)
        assert result is True
        
        # Datos que NO cumplen la condición
        data = {"company_size": "small", "budget": "low"}
        result = await WorkflowManager()._evaluate_conditions([condition], data)
        assert result is False


class TestAuthentication:
    """Tests para sistema de autenticación"""
    
    @pytest.fixture
    def security_config(self):
        """Fixture para configuración de seguridad"""
        return SecurityConfig(
            encryption_key="test_encryption_key_1234567890123456",
            jwt_secret_key="test_jwt_secret_key_123456789",
            redis_url=None  # No usar Redis en tests
        )
    
    @pytest.fixture
    def auth_manager(self, security_config):
        """Fixture para manager de autenticación"""
        return CRMAuthManager(security_config)
    
    @pytest.mark.asyncio
    async def test_user_authentication(self, auth_manager):
        """Test autenticación de usuario"""
        # Almacenar credenciales de prueba
        auth_manager.store_credentials("salesforce", "test_user", {
            "username": "test_user",
            "password": "secure_password",
            "client_id": "test_client_id"
        })
        
        # Simular autenticación
        session = await auth_manager.authenticate_user(
            username="test_user",
            password="secure_password",
            platform="salesforce",
            ip_address="127.0.0.1",
            user_agent="test_agent"
        )
        
        assert session is not None
        assert session.user_id == "test_user"
        assert session.platform == "salesforce"
        assert session.is_active is True
    
    @pytest.mark.asyncio
    async def test_token_verification(self, auth_manager):
        """Test verificación de tokens"""
        # Generar token
        token = auth_manager.token_manager.generate_access_token({
            "user_id": "test_user",
            "platform": "salesforce"
        })
        
        # Verificar token
        decoded = auth_manager.token_manager.verify_token(token)
        
        assert decoded is not None
        assert decoded["user_id"] == "test_user"
        assert decoded["platform"] == "salesforce"
    
    @pytest.mark.asyncio
    async def test_session_management(self, auth_manager):
        """Test gestión de sesiones"""
        # Crear sesión
        session = auth_manager.session_manager.create_session(
            user_id="test_user",
            platform="salesforce",
            ip_address="127.0.0.1",
            user_agent="test_agent",
            config=auth_manager.security_config
        )
        
        # Validar sesión
        validated_session = auth_manager.validate_session(session.session_id)
        assert validated_session is not None
        assert validated_session.session_id == session.session_id
        
        # Invalidar sesión
        auth_manager.invalidate_session(session.session_id)
        
        # Verificar que se invalidó
        validated_session = auth_manager.validate_session(session.session_id)
        assert validated_session is None


class TestAnalytics:
    """Tests para sistema de analytics"""
    
    @pytest.fixture
    def analytics_agent(self):
        """Fixture para agente de analytics"""
        return CRMAnalyticsAgent()
    
    @pytest.mark.asyncio
    async def test_generate_sales_report(self, analytics_agent):
        """Test generación de reporte de ventas"""
        date_range = {
            "start": "2025-01-01T00:00:00Z",
            "end": "2025-01-31T23:59:59Z"
        }
        
        platforms = ["salesforce", "hubspot"]
        
        result = await analytics_agent.generate_sales_report(date_range, platforms)
        
        assert result["success"] is True
        assert "report_id" in result
        assert "data" in result
        assert "metrics" in result["data"]
    
    @pytest.mark.asyncio
    async def test_consolidated_metrics(self, analytics_agent):
        """Test cálculo de métricas consolidadas"""
        platform_metrics = {
            "salesforce": {
                "total_leads": 100,
                "qualified_leads": 25,
                "opportunities": 15,
                "deals_closed": 5,
                "revenue": 75000
            },
            "hubspot": {
                "total_leads": 80,
                "qualified_leads": 30,
                "opportunities": 20,
                "deals_closed": 8,
                "revenue": 120000
            }
        }
        
        consolidated = await analytics_agent._calculate_consolidated_metrics(platform_metrics)
        
        # Verificar totales
        assert consolidated["total_leads"] == 180
        assert consolidated["qualified_leads"] == 55
        assert consolidated["opportunities"] == 35
        assert consolidated["deals_closed"] == 13
        assert consolidated["revenue"] == 195000
        
        # Verificar métricas calculadas
        expected_conversion_rate = 13 / 180  # deals_closed / total_leads
        assert abs(consolidated["overall_conversion_rate"] - expected_conversion_rate) < 0.01


class TestEnterpriseSystem:
    """Tests para sistema empresarial completo"""
    
    @pytest.fixture
    def enterprise_config(self):
        """Fixture para configuración empresarial"""
        from crm_enterprise_system import CRMConfiguration, CRMPlatform
        return CRMConfiguration(
            enabled_platforms=[CRMPlatform.SALESFORCE, CRMPlatform.HUBSPOT],
            workflows_enabled=True,
            analytics_enabled=True,
            sync_on_create=True
        )
    
    @pytest.fixture
    def enterprise_system(self, enterprise_config):
        """Fixture para sistema empresarial"""
        return CRMEnterpriseSystem(enterprise_config)
    
    @pytest.mark.asyncio
    async def test_system_initialization(self, enterprise_system):
        """Test inicialización del sistema empresarial"""
        with patch('aiohttp.ClientSession'):
            result = await enterprise_system.initialize()
            
            assert result is True
            assert enterprise_system.is_initialized is True
    
    @pytest.mark.asyncio
    async def test_create_lead_integration(self, enterprise_system):
        """Test creación de lead con integración completa"""
        # Inicializar sistema
        with patch('aiohttp.ClientSession'):
            await enterprise_system.initialize()
        
        lead_data = {
            "first_name": "María",
            "last_name": "García",
            "company": "InnovateCorp",
            "email": "maria@innovatecorp.com"
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 201
            mock_response.json.return_value = {"id": "lead_456", "success": True}
            mock_session.return_value.__aenter__.return_value = mock_response
            
            result = await enterprise_system.create_lead("salesforce", lead_data)
            
            assert result["success"] is True
            assert "lead_id" in result
    
    @pytest.mark.asyncio
    async def test_sync_operations(self, enterprise_system):
        """Test operaciones de sincronización"""
        # Inicializar sistema
        with patch('aiohttp.ClientSession'):
            await enterprise_system.initialize()
        
        sync_config = {
            "field_mappings": {
                "name": "name",
                "email": "email"
            }
        }
        
        with patch.object(enterprise_system.integration_manager, 'sync_all_platforms') as mock_sync:
            mock_sync.return_value = {"success": True, "synced_records": 50}
            
            result = await enterprise_system.run_full_sync(sync_config)
            
            assert result["success"] is True
            assert "sync_results" in result
    
    def test_system_status(self, enterprise_system):
        """Test estado del sistema"""
        status = enterprise_system.get_system_status()
        
        assert "system_status" in status
        assert "configuration" in status
        assert "platform_status" in status
        assert "system_metrics" in status


class TestAPIs:
    """Tests para APIs REST"""
    
    @pytest.mark.asyncio
    async def test_api_endpoints_availability(self):
        """Test disponibilidad de endpoints de API"""
        # Importar app de FastAPI
        from crm_api_endpoints import app
        
        # Test de que la app se inicializa correctamente
        assert app is not None
        assert app.title == "CRM Integration API"
    
    @pytest.mark.asyncio
    async def test_webhook_endpoints(self):
        """Test endpoints de webhook"""
        # Test configuración de webhooks
        from crm_api_endpoints import CRM_WEBHOOKS
        
        assert "salesforce" in CRM_WEBHOOKS
        assert "hubspot" in CRM_WEBHOOKS
        assert "pipedrive" in CRM_WEBHOOKS
        assert "zoho" in CRM_WEBHOOKS
        
        # Verificar estructura de webhook
        for platform, webhook_config in CRM_WEBHOOKS.items():
            assert hasattr(webhook_config, 'events')
            assert hasattr(webhook_config, 'signature_header')
            assert hasattr(webhook_config, 'secret')
            assert len(webhook_config.events) > 0


class TestSecurity:
    """Tests para sistema de seguridad"""
    
    def test_encryption_manager(self):
        """Test manager de cifrado"""
        from crm_auth_security import EncryptionManager
        
        key = "test_encryption_key_1234567890123456"
        manager = EncryptionManager(key)
        
        # Test cifrado/descifrado
        original_data = "sensitive_crm_data"
        encrypted = manager.encrypt(original_data)
        decrypted = manager.decrypt(encrypted)
        
        assert encrypted != original_data
        assert decrypted == original_data
    
    def test_password_manager(self):
        """Test manager de contraseñas"""
        from crm_auth_security import PasswordManager
        
        manager = PasswordManager()
        
        # Test hash/verify
        password = "secure_password_123"
        hashed = manager.hash_password(password)
        
        assert manager.verify_password(password, hashed) is True
        assert manager.verify_password("wrong_password", hashed) is False
    
    def test_rate_limiting(self):
        """Test limitador de tasa"""
        from crm_auth_security import RateLimiter
        
        limiter = RateLimiter()
        
        # Primera solicitud debe pasar
        assert limiter.is_rate_limited("user_123", 5) is False
        
        # Múltiples solicitudes
        for i in range(6):
            limiter.is_rate_limited("user_123", 5)
        
        # La 7ª debe estar limitada
        assert limiter.is_rate_limited("user_123", 5) is True


# Configuración de pytest
def pytest_configure(config):
    """Configuración global de pytest"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )


# Tests de integración completos
class TestIntegrationFlows:
    """Tests para flujos de integración completos"""
    
    @pytest.mark.asyncio
    async def test_complete_lead_lifecycle(self):
        """Test ciclo completo de vida de un lead"""
        # 1. Crear sistema
        config = create_enterprise_config()
        system = CRMEnterpriseSystem(config)
        
        with patch('aiohttp.ClientSession'):
            await system.initialize()
        
        # 2. Crear lead
        lead_data = {
            "first_name": "Carlos",
            "last_name": "Rodríguez",
            "company": "Enterprise Solutions",
            "email": "carlos@enterprise.com"
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 201
            mock_response.json.return_value = {"id": "lead_789", "success": True}
            mock_session.return_value.__aenter__.return_value = mock_response
            
            result = await system.create_lead("salesforce", lead_data)
            assert result["success"] is True
        
        # 3. Verificar que se activaron workflows
        assert system.workflow_manager is not None
        
        # 4. Verificar sincronización
        assert system.config.sync_on_create is True
        
        # 5. Verificar analytics
        assert system.analytics_agent is not None
    
    @pytest.mark.asyncio
    async def test_multi_platform_sync(self):
        """Test sincronización entre múltiples plataformas"""
        config = create_enterprise_config()
        system = CRMEnterpriseSystem(config)
        
        with patch('aiohttp.ClientSession'):
            await system.initialize()
        
        # Ejecutar sincronización completa
        with patch.object(system.integration_manager, 'sync_all_platforms') as mock_sync:
            mock_sync.return_value = {"success": True, "sync_results": {}}
            
            result = await system.run_full_sync()
            assert result["success"] is True


# Comando para ejecutar tests
if __name__ == "__main__":
    print("Ejecutando tests del sistema CRM empresarial...")
    
    # Configurar pytest
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])