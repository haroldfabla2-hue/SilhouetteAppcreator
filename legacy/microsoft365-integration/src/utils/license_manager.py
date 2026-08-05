"""
Microsoft 365 - License Manager
Gestor de licencias y cumplimiento de Microsoft 365
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json

logger = logging.getLogger(__name__)

class LicenseType(Enum):
    """Tipos de licencias de Microsoft 365"""
    OFFICE_365_BUSINESS = "O365_BUSINESS"
    OFFICE_365_BUSINESS_PREMIUM = "O365_BUSINESS_PREMIUM"
    OFFICE_365_ENTERPRISE_E1 = "O365_ENTERPRISE_E1"
    OFFICE_365_ENTERPRISE_E3 = "O365_ENTERPRISE_E3"
    OFFICE_365_ENTERPRISE_E5 = "O365_ENTERPRISE_E5"
    DYNAMICS_365_BUSINESS_CENTRAL = "DYN365_BUSINESS_CENTRAL"
    POWER_PLATFORM_PLUS = "POWER_PLATFORM_PLUS"
    SHAREPOINT_PLAN_2 = "SHAREPOINT_PLAN_2"
    EXCHANGE_ONLINE_PLAN_2 = "EXCHANGE_ONLINE_PLAN_2"
    TEAMS_EXPLORATORY = "TEAMS_EXPLORATORY"

class LicenseStatus(Enum):
    """Estados de licencia"""
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    WARNING = "warning"
    UNKNOWN = "unknown"

class LicenseManager:
    """Gestor de licencias y cumplimiento de Microsoft 365"""
    
    def __init__(self, graph_client):
        self.graph_client = graph_client
        self.license_policies: Dict[str, Dict] = {}
        self.user_licenses: Dict[str, Dict] = {}
        self.license_assignments: Dict[str, Dict] = {}
        
        # Configuración de monitoreo
        self.warning_days = 30  # Días antes de expiración para advertencia
        self.critical_days = 7  # Días antes de expiración para crítico
        
        logger.info("License manager initialized")
    
    async def get_license_information(self, user_id: str = None) -> Dict:
        """Obtener información de licencias"""
        try:
            if user_id:
                return await self._get_user_license_info(user_id)
            else:
                return await self._get_all_licenses_info()
                
        except Exception as e:
            logger.error(f"Error getting license information: {str(e)}")
            return {'error': str(e)}
    
    async def _get_user_license_info(self, user_id: str) -> Dict:
        """Obtener información de licencia de usuario específico"""
        try:
            # En implementación real, esto obtendría información de Graph API
            user_info = await self.graph_client.get_user(user_id)
            
            # Simular información de licencia
            license_info = {
                'user_id': user_id,
                'user_display_name': user_info.get('displayName', 'Unknown'),
                'licenses': [
                    {
                        'sku_id': 'O365_BUSINESS_PREMIUM',
                        'sku_name': 'Office 365 Business Premium',
                        'status': LicenseStatus.ACTIVE.value,
                        'assigned_date': '2024-01-01',
                        'expiration_date': '2025-01-01',
                        'services': ['WORD', 'EXCEL', 'POWERPOINT', 'OUTLOOK', 'ONEDRIVE', 'TEAMS']
                    }
                ],
                'total_licenses': 1,
                'active_licenses': 1,
                'license_compliance': True,
                'last_checked': datetime.utcnow().isoformat()
            }
            
            return {
                'status': 'success',
                'license_info': license_info
            }
            
        except Exception as e:
            logger.error(f"Error getting user license info for {user_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'user_id': user_id
            }
    
    async def _get_all_licenses_info(self) -> Dict:
        """Obtener información de todas las licencias de la organización"""
        try:
            # En implementación real, esto obtendría información de Graph API
            
            # Simular información de licencias organizacionales
            org_licenses = {
                'organization_id': 'organization_123',
                'organization_name': 'Empresa de Ejemplo',
                'total_licenses': 100,
                'assigned_licenses': 85,
                'available_licenses': 15,
                'license_usage_percentage': 85.0,
                'license_breakdown': [
                    {
                        'sku_name': 'Office 365 Business Premium',
                        'total_purchased': 50,
                        'assigned': 42,
                        'available': 8,
                        'cost_per_license': 22.00,
                        'monthly_cost': 1100.00
                    },
                    {
                        'sku_name': 'Office 365 Enterprise E3',
                        'total_purchased': 30,
                        'assigned': 25,
                        'available': 5,
                        'cost_per_license': 32.00,
                        'monthly_cost': 800.00
                    },
                    {
                        'sku_name': 'Microsoft Teams Exploratory',
                        'total_purchased': 20,
                        'assigned': 18,
                        'available': 2,
                        'cost_per_license': 0.00,
                        'monthly_cost': 0.00
                    }
                ],
                'compliance_status': 'compliant',
                'last_audit': datetime.utcnow().isoformat(),
                'next_audit': (datetime.utcnow() + timedelta(days=30)).isoformat()
            }
            
            return {
                'status': 'success',
                'organization_licenses': org_licenses
            }
            
        except Exception as e:
            logger.error(f"Error getting organization licenses: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def assign_license(
        self,
        user_id: str,
        license_sku: str,
        assignment_options: Dict = None
    ) -> Dict:
        """Asignar licencia a usuario"""
        try:
            assignment_options = assignment_options or {}
            
            # Crear asignación de licencia
            assignment_data = {
                'user_id': user_id,
                'sku_id': license_sku,
                'assigned_by': 'system',
                'assigned_date': datetime.utcnow().isoformat(),
                'options': assignment_options,
                'status': 'pending'
            }
            
            # En implementación real, esto asignaría la licencia vía Graph API
            logger.info(f"License assignment initiated: {user_id} <- {license_sku}")
            
            # Simular proceso de asignación
            assignment_result = {
                'assignment_id': f"assign_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'user_id': user_id,
                'sku_id': license_sku,
                'status': 'completed',
                'assigned_date': datetime.utcnow().isoformat(),
                'services_enabled': self._get_services_for_sku(license_sku)
            }
            
            return {
                'status': 'success',
                'assignment_result': assignment_result
            }
            
        except Exception as e:
            logger.error(f"Error assigning license {license_sku} to user {user_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'user_id': user_id,
                'license_sku': license_sku
            }
    
    async def revoke_license(self, user_id: str, license_sku: str, reason: str = "") -> Dict:
        """Revocar licencia de usuario"""
        try:
            # En implementación real, esto revocaría la licencia vía Graph API
            logger.info(f"License revocation initiated: {user_id} <- {license_sku} (Reason: {reason})")
            
            revocation_result = {
                'revocation_id': f"revoke_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'user_id': user_id,
                'sku_id': license_sku,
                'reason': reason,
                'status': 'completed',
                'revoked_date': datetime.utcnow().isoformat(),
                'services_disabled': self._get_services_for_sku(license_sku)
            }
            
            return {
                'status': 'success',
                'revocation_result': revocation_result
            }
            
        except Exception as e:
            logger.error(f"Error revoking license {license_sku} from user {user_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'user_id': user_id,
                'license_sku': license_sku
            }
    
    async def check_license_compliance(self) -> Dict:
        """Verificar cumplimiento de licencias"""
        try:
            compliance_results = {
                'check_date': datetime.utcnow().isoformat(),
                'total_users': 85,
                'compliant_users': 82,
                'non_compliant_users': 3,
                'compliance_rate': 96.47,
                'issues': [],
                'recommendations': []
            }
            
            # Simular problemas de cumplimiento
            compliance_results['issues'] = [
                {
                    'user_id': 'user_1',
                    'issue': 'expired_license',
                    'description': 'License expired 5 days ago',
                    'severity': 'critical'
                },
                {
                    'user_id': 'user_2',
                    'issue': 'suspended_license',
                    'description': 'License suspended due to non-payment',
                    'severity': 'high'
                }
            ]
            
            # Generar recomendaciones
            compliance_results['recommendations'] = [
                'Renew 3 licenses that are expiring within 30 days',
                'Review license assignments for inactive users',
                'Consider downgrading unused premium licenses'
            ]
            
            return {
                'status': 'success',
                'compliance_results': compliance_results
            }
            
        except Exception as e:
            logger.error(f"Error checking license compliance: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def generate_license_report(self, report_type: str = "summary") -> Dict:
        """Generar reporte de licencias"""
        try:
            report_data = {
                'report_type': report_type,
                'generated_at': datetime.utcnow().isoformat(),
                'report_period': {
                    'start_date': (datetime.utcnow() - timedelta(days=30)).isoformat(),
                    'end_date': datetime.utcnow().isoformat()
                }
            }
            
            if report_type == "summary":
                report_data.update(await self._generate_summary_report())
            elif report_type == "detailed":
                report_data.update(await self._generate_detailed_report())
            elif report_type == "usage":
                report_data.update(await self._generate_usage_report())
            else:
                raise ValueError(f"Unsupported report type: {report_type}")
            
            return {
                'status': 'success',
                'report_data': report_data
            }
            
        except Exception as e:
            logger.error(f"Error generating license report: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def _generate_summary_report(self) -> Dict:
        """Generar reporte resumen"""
        return {
            'summary': {
                'total_licenses': 100,
                'assigned_licenses': 85,
                'available_licenses': 15,
                'monthly_cost': 1900.00,
                'annual_cost': 22800.00,
                'cost_per_user': 22.35,
                'usage_rate': 85.0
            },
            'top_licenses': [
                {'sku': 'O365_BUSINESS_PREMIUM', 'assigned': 42, 'cost': 1100.00},
                {'sku': 'O365_ENTERPRISE_E3', 'assigned': 25, 'cost': 800.00}
            ],
            'cost_trends': {
                'current_month': 1900.00,
                'previous_month': 1850.00,
                'trend': '+2.7%'
            }
        }
    
    async def _generate_detailed_report(self) -> Dict:
        """Generar reporte detallado"""
        return {
            'detailed_analysis': {
                'license_utilization_by_department': {
                    'IT': {'assigned': 15, 'utilization': 93.3},
                    'Sales': {'assigned': 25, 'utilization': 89.3},
                    'Marketing': {'assigned': 20, 'utilization': 95.0},
                    'HR': {'assigned': 10, 'utilization': 90.0},
                    'Finance': {'assigned': 15, 'utilization': 86.7}
                },
                'service_usage': {
                    'WORD': 85,
                    'EXCEL': 82,
                    'POWERPOINT': 78,
                    'OUTLOOK': 95,
                    'ONEDRIVE': 88,
                    'TEAMS': 92
                },
                'license_expiration_warnings': [
                    {'user_id': 'user_1', 'license': 'O365_BUSINESS_PREMIUM', 'expires_in_days': 15},
                    {'user_id': 'user_2', 'license': 'O365_ENTERPRISE_E3', 'expires_in_days': 22}
                ]
            }
        }
    
    async def _generate_usage_report(self) -> Dict:
        """Generar reporte de uso"""
        return {
            'usage_metrics': {
                'active_users_last_30_days': 78,
                'inactive_users_last_30_days': 7,
                'average_daily_active_users': 75,
                'peak_usage_day': 'Tuesday',
                'lowest_usage_day': 'Sunday'
            },
            'service_usage_patterns': {
                'morning_peak': '09:00-11:00',
                'afternoon_peak': '14:00-16:00',
                'evening_usage': '35%',
                'weekend_usage': '15%'
            },
            'recommendations': [
                'Consider license optimization for 7 inactive users',
                'Teams usage is high - consider additional licenses',
                'PowerPoint usage is low - evaluate training needs'
            ]
        }
    
    def _get_services_for_sku(self, sku_id: str) -> List[str]:
        """Obtener servicios incluidos en un SKU"""
        service_mapping = {
            'O365_BUSINESS_PREMIUM': ['WORD', 'EXCEL', 'POWERPOINT', 'OUTLOOK', 'ONEDRIVE', 'TEAMS'],
            'O365_ENTERPRISE_E3': ['WORD', 'EXCEL', 'POWERPOINT', 'OUTLOOK', 'ONEDRIVE', 'TEAMS', 'SHAREPOINT'],
            'O365_ENTERPRISE_E5': ['WORD', 'EXCEL', 'POWERPOINT', 'OUTLOOK', 'ONEDRIVE', 'TEAMS', 'SHAREPOINT', 'EXCHANGE'],
            'DYN365_BUSINESS_CENTRAL': ['BUSINESS_CENTRAL'],
            'POWER_PLATFORM_PLUS': ['POWER_AUTOMATE', 'POWER_BI', 'POWER_APPS']
        }
        return service_mapping.get(sku_id, [])
    
    async def optimize_licenses(self) -> Dict:
        """Optimizar asignación de licencias"""
        try:
            optimization_results = {
                'optimization_date': datetime.utcnow().isoformat(),
                'total_potential_savings': 440.00,
                'recommended_actions': [],
                'current_waste': 8.5  # percentage
            }
            
            # Simular recomendaciones de optimización
            optimization_results['recommended_actions'] = [
                {
                    'action': 'downgrade',
                    'user_id': 'user_15',
                    'current_license': 'O365_ENTERPRISE_E5',
                    'recommended_license': 'O365_BUSINESS_PREMIUM',
                    'monthly_savings': 10.00
                },
                {
                    'action': 'remove',
                    'user_id': 'user_23',
                    'reason': 'inactive_90_days',
                    'monthly_savings': 22.00
                },
                {
                    'action': 'upgrade',
                    'user_id': 'user_8',
                    'current_license': 'O365_BUSINESS_PREMIUM',
                    'recommended_license': 'O365_ENTERPRISE_E3',
                    'additional_cost': 10.00,
                    'reason': 'requires_power_automate'
                }
            ]
            
            # Calcular ahorros totales
            total_savings = sum(
                action.get('monthly_savings', 0)
                for action in optimization_results['recommended_actions']
            )
            optimization_results['total_potential_savings'] = total_savings
            
            return {
                'status': 'success',
                'optimization_results': optimization_results
            }
            
        except Exception as e:
            logger.error(f"Error optimizing licenses: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def get_license_analytics(self) -> Dict:
        """Obtener analíticas avanzadas de licencias"""
        try:
            analytics = {
                'generated_at': datetime.utcnow().isoformat(),
                'key_metrics': {
                    'license_efficiency': 87.3,
                    'cost_optimization_score': 8.5,
                    'compliance_score': 96.47,
                    'user_satisfaction': 4.2
                },
                'predictions': {
                    'next_month_cost': 1950.00,
                    'projected_license_needs': 92,
                    'renewal_urgency': 'medium'
                },
                'benchmarks': {
                    'industry_average_cost_per_user': 25.00,
                    'current_cost_per_user': 22.35,
                    'cost_position': 'below_average'
                },
                'alerts': [
                    {
                        'type': 'license_expiration',
                        'description': '3 licenses expire within 30 days',
                        'severity': 'medium',
                        'action_required': True
                    }
                ]
            }
            
            return {
                'status': 'success',
                'analytics': analytics
            }
            
        except Exception as e:
            logger.error(f"Error getting license analytics: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }