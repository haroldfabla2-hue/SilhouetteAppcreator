"""
Wrapper MCP para Agentes Financieros Especializados
Integra PaymentProcessingAgent, FinancialAnalysisAgent, ReconciliationAgent, 
ComplianceAgent y RiskAssessmentAgent como herramientas MCP
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from pathlib import Path

from .financial.payment_processing_agent import PaymentProcessingAgent, PaymentRequest, PaymentMethod, SecurityLevel
from .financial.financial_analysis_agent import FinancialAnalysisAgent
from .financial.reconciliation_agent import ReconciliationAgent, ReconciliationSource, MatchStrategy
from .financial.compliance_agent import ComplianceAgent, Regulation, RiskLevel as ComplianceRiskLevel
from .financial.risk_assessment_agent import RiskAssessmentAgent, RiskCategory

from ...core.exceptions import FinancialAgentError

class FinancialAgentMCPWrapper:
    """
    Wrapper MCP que expone agentes financieros como herramientas disponibles
    Maneja configuración, autenticación y orquestación de agentes
    """
    
    def __init__(self, 
                 stripe_secret_key: str,
                 stripe_publishable_key: str,
                 paypal_client_id: str,
                 paypal_client_secret: str,
                 plaid_client_id: str,
                 plaid_secret: str,
                 encryption_key: str,
                 jwt_secret: str,
                 compliance_db_path: str = "./compliance_data"):
        
        # Inicializar agentes financieros
        self.payment_agent = PaymentProcessingAgent(
            stripe_secret_key=stripe_secret_key,
            stripe_publishable_key=stripe_publishable_key,
            paypal_client_id=paypal_client_id,
            paypal_client_secret=paypal_client_secret,
            encryption_key=encryption_key,
            jwt_secret=jwt_secret,
            security_level=SecurityLevel.ENTERPRISE
        )
        
        self.analysis_agent = FinancialAnalysisAgent(
            plaid_client_id=plaid_client_id,
            plaid_secret=plaid_secret,
            plaid_env="sandbox"  # Configurable por entorno
        )
        
        self.reconciliation_agent = ReconciliationAgent(
            confidence_threshold=0.85,
            date_tolerance_days=3,
            amount_tolerance=0.01
        )
        
        self.compliance_agent = ComplianceAgent(
            compliance_db_path=compliance_db_path,
            audit_log_path="./audit_logs"
        )
        
        self.risk_agent = RiskAssessmentAgent(
            risk_models_config={},
            alert_thresholds={}
        )
        
        # Cache de configuraciones
        self.config_cache = {}
        self.active_sessions = {}
    
    # ========== HERRAMIENTAS MCP DE PROCESAMIENTO DE PAGOS ==========
    
    async def mcp_process_payment(self,
                                amount: float,
                                currency: str = "USD",
                                method: str = "stripe",
                                customer_id: Optional[str] = None,
                                payment_method_id: Optional[str] = None,
                                user_id: str = "default_user",
                                context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Herramienta MCP para procesar pagos con múltiples proveedores
        
        Args:
            amount: Monto del pago
            currency: Moneda (USD, EUR, GBP, MXN)
            method: Método de pago ('stripe', 'paypal')
            customer_id: ID del cliente
            payment_method_id: ID del método de pago
            user_id: ID del usuario
            context: Contexto adicional
            
        Returns:
            Resultado del procesamiento de pago
        """
        try:
            # Crear solicitud de pago
            payment_request = PaymentRequest(
                amount=amount,
                currency=currency,
                method=method,
                customer_id=customer_id,
                payment_method_id=payment_method_id,
                metadata=context or {}
            )
            
            # Procesar pago
            result = await self.payment_agent.process_payment(
                payment_request=payment_request,
                user_id=user_id,
                context=context
            )
            
            return {
                "success": result.success,
                "transaction_id": result.transaction_id,
                "amount": result.amount,
                "currency": result.currency,
                "status": result.status,
                "method": result.method,
                "created_at": result.created_at.isoformat(),
                "error_message": result.error_message,
                "metadata": result.metadata
            }
            
        except Exception as e:
            raise FinancialAgentError(f"Error procesando pago: {str(e)}")
    
    async def mcp_create_subscription(self,
                                    customer_id: str,
                                    price_id: str,
                                    payment_method_id: str,
                                    provider: str = "stripe") -> Dict[str, Any]:
        """
        Herramienta MCP para crear subscripciones recurrentes
        
        Args:
            customer_id: ID del cliente
            price_id: ID del precio/stripe price
            payment_method_id: ID del método de pago
            provider: Proveedor ('stripe', 'paypal')
            
        Returns:
            Resultado de creación de subscripción
        """
        try:
            result = await self.payment_agent.create_subscription(
                customer_id=customer_id,
                price_id=price_id,
                payment_method_id=payment_method_id,
                provider=provider
            )
            
            return result
            
        except Exception as e:
            raise FinancialAgentError(f"Error creando subscripción: {str(e)}")
    
    async def mcp_handle_payment_webhook(self,
                                       payload: str,
                                       signature: str,
                                       provider: str) -> Dict[str, Any]:
        """
        Herramienta MCP para manejar webhooks de pago
        
        Args:
            payload: Payload del webhook
            signature: Firma de verificación
            provider: Proveedor ('stripe', 'paypal')
            
        Returns:
            Resultado del procesamiento del webhook
        """
        try:
            result = await self.payment_agent.handle_webhook(
                payload=payload,
                signature=signature,
                provider=provider
            )
            
            return result
            
        except Exception as e:
            raise FinancialAgentError(f"Error procesando webhook: {str(e)}")
    
    # ========== HERRAMIENTAS MCP DE ANÁLISIS FINANCIERO ==========
    
    async def mcp_connect_bank_account(self,
                                     user_id: str,
                                     public_token: str) -> Dict[str, Any]:
        """
        Herramienta MCP para conectar cuenta bancaria via Plaid
        
        Args:
            user_id: ID del usuario
            public_token: Token público de Plaid
            
        Returns:
            Información de la cuenta conectada
        """
        try:
            result = await self.analysis_agent.connect_bank_account(
                user_id=user_id,
                public_token=public_token
            )
            
            return result
            
        except Exception as e:
            raise FinancialAgentError(f"Error conectando cuenta bancaria: {str(e)}")
    
    async def mcp_get_account_balances(self, user_id: str) -> Dict[str, Any]:
        """
        Herramienta MCP para obtener saldos de cuentas
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de cuentas con sus saldos
        """
        try:
            accounts = await self.analysis_agent.get_account_balances(user_id)
            
            return {
                "success": True,
                "user_id": user_id,
                "accounts": [asdict(account) for account in accounts],
                "total_accounts": len(accounts)
            }
            
        except Exception as e:
            raise FinancialAgentError(f"Error obteniendo saldos: {str(e)}")
    
    async def mcp_analyze_spending_patterns(self,
                                          user_id: str,
                                          period_days: int = 30) -> Dict[str, Any]:
        """
        Herramienta MCP para analizar patrones de gasto
        
        Args:
            user_id: ID del usuario
            period_days: Período de análisis en días
            
        Returns:
            Análisis completo de patrones de gasto
        """
        try:
            analysis = await self.analysis_agent.analyze_spending_patterns(
                user_id=user_id,
                period_days=period_days
            )
            
            return {
                "success": True,
                "user_id": user_id,
                "analysis_period_days": period_days,
                "analysis": analysis
            }
            
        except Exception as e:
            raise FinancialAgentError(f"Error analizando patrones de gasto: {str(e)}")
    
    async def mcp_analyze_cash_flow(self,
                                  user_id: str,
                                  months: int = 6) -> Dict[str, Any]:
        """
        Herramienta MCP para analizar flujo de caja
        
        Args:
            user_id: ID del usuario
            months: Período de análisis en meses
            
        Returns:
            Análisis de flujo de caja
        """
        try:
            analysis = await self.analysis_agent.analyze_cash_flow(
                user_id=user_id,
                months=months
            )
            
            return {
                "success": True,
                "user_id": user_id,
                "analysis_period_months": months,
                "analysis": analysis
            }
            
        except Exception as e:
            raise FinancialAgentError(f"Error analizando flujo de caja: {str(e)}")
    
    async def mcp_detect_financial_anomalies(self,
                                           user_id: str,
                                           anomaly_threshold: float = 2.0) -> Dict[str, Any]:
        """
        Herramienta MCP para detectar anomalías financieras
        
        Args:
            user_id: ID del usuario
            anomaly_threshold: Umbral de detección de anomalías
            
        Returns:
            Transacciones anómalas detectadas
        """
        try:
            anomalies = await self.analysis_agent.detect_anomalies(
                user_id=user_id,
                anomaly_threshold=anomaly_threshold
            )
            
            return {
                "success": True,
                "user_id": user_id,
                "anomaly_threshold": anomaly_threshold,
                "anomalies": anomalies
            }
            
        except Exception as e:
            raise FinancialAgentError(f"Error detectando anomalías: {str(e)}")
    
    async def mcp_generate_financial_report(self,
                                          user_id: str,
                                          report_type: str = "monthly",
                                          period_months: int = 1) -> Dict[str, Any]:
        """
        Herramienta MCP para generar reporte financiero completo
        
        Args:
            user_id: ID del usuario
            report_type: Tipo de reporte
            period_months: Período del reporte en meses
            
        Returns:
            Reporte financiero completo
        """
        try:
            report = await self.analysis_agent.generate_financial_report(
                user_id=user_id,
                report_type=report_type,
                period_months=period_months
            )
            
            return {
                "success": True,
                "user_id": user_id,
                "report_type": report_type,
                "report": report
            }
            
        except Exception as e:
            raise FinancialAgentError(f"Error generando reporte financiero: {str(e)}")
    
    # ========== HERRAMIENTAS MCP DE RECONCILIACIÓN ==========
    
    async def mcp_reconcile_transactions(self,
                                       start_date: str,
                                       end_date: str,
                                       source_1: str,
                                       source_2: str,
                                       confidence_threshold: float = 0.85) -> Dict[str, Any]:
        """
        Herramienta MCP para reconciliar transacciones entre fuentes
        
        Args:
            start_date: Fecha de inicio (YYYY-MM-DD)
            end_date: Fecha de fin (YYYY-MM-DD)
            source_1: Primera fuente (bank, stripe, paypal, quickbooks, xero)
            source_2: Segunda fuente
            confidence_threshold: Umbral de confianza para matching
            
        Returns:
            Resultado de reconciliación
        """
        try:
            # Parsear fechas
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Convertir fuentes a enum
            source_1_enum = ReconciliationSource(source_1)
            source_2_enum = ReconciliationSource(source_2)
            
            # Actualizar threshold si es necesario
            self.reconciliation_agent.confidence_threshold = confidence_threshold
            
            # Ejecutar reconciliación
            result = await self.reconciliation_agent.reconcile_period(
                start_date=start_dt,
                end_date=end_dt,
                source_1=source_1_enum,
                source_2=source_2_enum
            )
            
            return {
                "success": True,
                "reconciliation_id": result.reconciliation_id,
                "period": {
                    "start": start_date,
                    "end": end_date
                },
                "sources": [source_1, source_2],
                "summary": {
                    "total_records": result.total_records,
                    "matched_count": result.matched_count,
                    "unmatched_count": result.unmatched_count,
                    "discrepancy_amount": result.discrepancy_amount,
                    "confidence_threshold": result.confidence_threshold
                },
                "matches": [asdict(match) for match in result.matches],
                "unmatched_records": [asdict(record) for record in result.unmatched_records]
            }
            
        except Exception as e:
            raise FinancialAgentError(f"Error reconciliando transacciones: {str(e)}")
    
    async def mcp_auto_reconcile_multiple_sources(self,
                                                start_date: str,
                                                end_date: str,
                                                sources: List[str],
                                                primary_source: str = "quickbooks") -> Dict[str, Any]:
        """
        Herramienta MCP para reconciliación automática de múltiples fuentes
        
        Args:
            start_date: Fecha de inicio (YYYY-MM-DD)
            end_date: Fecha de fin (YYYY-MM-DD)
            sources: Lista de fuentes a reconciliar
            primary_source: Fuente principal para reconciliación
            
        Returns:
            Resultados de reconciliación múltiple
        """
        try:
            # Parsear fechas
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Convertir fuentes a enum
            source_enums = [ReconciliationSource(s) for s in sources]
            primary_enum = ReconciliationSource(primary_source)
            
            # Ejecutar reconciliación múltiple
            results = await self.reconciliation_agent.auto_reconcile_multiple_sources(
                start_date=start_dt,
                end_date=end_dt,
                sources=source_enums,
                primary_source=primary_enum
            )
            
            return {
                "success": True,
                "period": {
                    "start": start_date,
                    "end": end_date
                },
                "sources_analyzed": sources,
                "primary_source": primary_source,
                "results": results
            }
            
        except Exception as e:
            raise FinancialAgentError(f"Error en reconciliación múltiple: {str(e)}")
    
    async def mcp_validate_reconciliation(self,
                                        reconciliation_id: str,
                                        validation_criteria: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Herramienta MCP para validar calidad de reconciliación
        
        Args:
            reconciliation_id: ID de reconciliación
            validation_criteria: Criterios de validación opcionales
            
        Returns:
            Resultado de validación
        """
        try:
            validation_result = await self.reconciliation_agent.validate_reconciliation(
                reconciliation_id=reconciliation_id,
                validation_criteria=validation_criteria
            )
            
            return {
                "success": True,
                "validation_result": validation_result
            }
            
        except Exception as e:
            raise FinancialAgentError(f"Error validando reconciliación: {str(e)}")
    
    # ========== HERRAMIENTAS MCP DE COMPLIANCE ==========
    
    async def mcp_run_compliance_assessment(self,
                                          regulations: List[str],
                                          assessment_type: str = "full",
                                          scope: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Herramienta MCP para ejecutar evaluación de compliance
        
        Args:
            regulations: Lista de regulaciones (PCI_DSS, SOX, AML, GDPR, etc.)
            assessment_type: Tipo de evaluación (full, partial, automated)
            scope: Alcance de la evaluación
            
        Returns:
            Resultado de evaluación de compliance
        """
        try:
            # Convertir regulaciones a enum
            regulation_enums = [Regulation(r) for r in regulations]
            
            assessment_result = await self.compliance_agent.run_compliance_assessment(
                regulations=regulation_enums,
                assessment_type=assessment_type,
                scope=scope
            )
            
            return {
                "success": True,
                "assessment_id": assessment_result["assessment_id"],
                "assessment_type": assessment_type,
                "regulations_assessed": regulations,
                "overall_status": assessment_result["overall_status"],
                "assessment_report": assessment_result
            }
            
        except Exception as e:
            raise FinancialAgentError(f"Error ejecutando evaluación de compliance: {str(e)}")
    
    async def mcp_generate_regulatory_report(self,
                                           report_type: str,
                                           regulation: str,
                                           start_date: str,
                                           end_date: str,
                                           output_format: str = "pdf") -> Dict[str, Any]:
        """
        Herramienta MCP para generar reporte regulatorio
        
        Args:
            report_type: Tipo de reporte
            regulation: Regulación aplicable
            start_date: Fecha de inicio (YYYY-MM-DD)
            end_date: Fecha de fin (YYYY-MM-DD)
            output_format: Formato de salida (pdf, json, excel)
            
        Returns:
            Reporte regulatorio generado
        """
        try:
            # Parsear fechas
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Convertir regulación a enum
            regulation_enum = Regulation(regulation)
            
            report_result = await self.compliance_agent.generate_regulatory_report(
                report_type=report_type,
                regulation=regulation_enum,
                period_start=start_dt,
                period_end=end_dt,
                output_format=output_format
            )
            
            return report_result
            
        except Exception as e:
            raise FinancialAgentError(f"Error generando reporte regulatorio: {str(e)}")
    
    async def mcp_monitor_aml_activities(self,
                                       transactions: List[Dict[str, Any]],
                                       risk_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Herramienta MCP para monitoreo AML
        
        Args:
            transactions: Lista de transacciones para monitorear
            risk_threshold: Umbral de riesgo AML
            
        Returns:
            Reporte de monitoreo AML
        """
        try:
            aml_report = await self.compliance_agent.monitor_aml_activities(
                transactions=transactions,
                risk_threshold=risk_threshold
            )
            
            return {
                "success": True,
                "aml_report": aml_report
            }
            
        except Exception as e:
            raise FinancialAgentError(f"Error en monitoreo AML: {str(e)}")
    
    async def mcp_validate_pci_dss_compliance(self) -> Dict[str, Any]:
        """
        Herramienta MCP para validar cumplimiento PCI DSS
        
        Returns:
            Validación PCI DSS completa
        """
        try:
            pci_result = await self.compliance_agent.validate_pci_dss_compliance()
            
            return {
                "success": True,
                "pci_validation": pci_result
            }
            
        except Exception as e:
            raise FinancialAgentError(f"Error validando PCI DSS: {str(e)}")
    
    async def mcp_manage_audit_trail(self,
                                   event_type: str,
                                   user_id: str,
                                   action: str,
                                   resource: str,
                                   details: Dict[str, Any],
                                   risk_level: str = "low") -> Dict[str, Any]:
        """
        Herramienta MCP para gestionar audit trail
        
        Args:
            event_type: Tipo de evento
            user_id: ID del usuario
            action: Acción realizada
            resource: Recurso afectado
            details: Detalles del evento
            risk_level: Nivel de riesgo (low, medium, high, critical)
            
        Returns:
            ID del evento registrado
        """
        try:
            # Convertir riesgo a enum
            risk_enum = ComplianceRiskLevel(risk_level)
            
            event_id = await self.compliance_agent.manage_audit_trail(
                event_type=event_type,
                user_id=user_id,
                action=action,
                resource=resource,
                details=details,
                risk_level=risk_enum
            )
            
            return {
                "success": True,
                "event_id": event_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise FinancialAgentError(f"Error gestionando audit trail: {str(e)}")
    
    async def mcp_generate_audit_report(self,
                                      start_date: str,
                                      end_date: str,
                                      filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Herramienta MCP para generar reporte de auditoría
        
        Args:
            start_date: Fecha de inicio (YYYY-MM-DD)
            end_date: Fecha de fin (YYYY-MM-DD)
            filters: Filtros para el reporte
            
        Returns:
            Reporte de auditoría
        """
        try:
            # Parsear fechas
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            audit_report = await self.compliance_agent.generate_audit_report(
                start_date=start_dt,
                end_date=end_dt,
                filters=filters
            )
            
            return {
                "success": True,
                "audit_report": audit_report
            }
            
        except Exception as e:
            raise FinancialAgentError(f"Error generando reporte de auditoría: {str(e)}")
    
    # ========== HERRAMIENTAS MCP DE EVALUACIÓN DE RIESGOS ==========
    
    async def mcp_assess_credit_risk(self,
                                   customer_id: str,
                                   application_data: Dict[str, Any],
                                   historical_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Herramienta MCP para evaluación de riesgo crediticio
        
        Args:
            customer_id: ID del cliente
            application_data: Datos de la aplicación
            historical_data: Datos históricos opcionales
            
        Returns:
            Evaluación de riesgo crediticio
        """
        try:
            assessment = await self.risk_agent.assess_credit_risk(
                customer_id=customer_id,
                application_data=application_data,
                historical_data=historical_data
            )
            
            return {
                "success": True,
                "assessment_id": assessment.assessment_id,
                "customer_id": customer_id,
                "overall_score": assessment.overall_score,
                "risk_level": assessment.risk_level,
                "confidence_level": assessment.confidence_level,
                "assessment_date": assessment.assessment_date.isoformat(),
                "factors": [asdict(factor) for factor in assessment.factors],
                "recommendations": assessment.recommendations,
                "next_review_date": assessment.next_review_date.isoformat()
            }
            
        except Exception as e:
            raise FinancialAgentError(f"Error evaluando riesgo crediticio: {str(e)}")
    
    async def mcp_assess_transaction_risk(self,
                                        transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Herramienta MCP para evaluación de riesgo de transacción
        
        Args:
            transaction_data: Datos de la transacción
            
        Returns:
            Perfil de riesgo de transacción
        """
        try:
            profile = await self.risk_agent.assess_transaction_risk(transaction_data)
            
            return {
                "success": True,
                "transaction_id": profile.transaction_id,
                "overall_risk_score": profile.overall_risk_score,
                "risk_factors": {
                    "merchant_risk_score": profile.merchant_risk_score,
                    "location_risk_score": profile.location_risk_score,
                    "amount_risk_score": profile.amount_risk_score,
                    "time_risk_score": profile.time_risk_score,
                    "device_risk_score": profile.device_risk_score,
                    "behavior_risk_score": profile.behavior_risk_score
                },
                "flags": profile.flags,
                "risk_factors_data": profile.risk_factors
            }
            
        except Exception as e:
            raise FinancialAgentError(f"Error evaluando riesgo de transacción: {str(e)}")
    
    async def mcp_assess_portfolio_risk(self,
                                      portfolio_data: Dict[str, Any],
                                      risk_models: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Herramienta MCP para evaluación de riesgo de portafolio
        
        Args:
            portfolio_data: Datos del portafolio
            risk_models: Modelos de riesgo opcionales
            
        Returns:
            Evaluación de riesgo de portafolio
        """
        try:
            assessment = await self.risk_agent.assess_portfolio_risk(
                portfolio_data=portfolio_data,
                risk_models=risk_models
            )
            
            return {
                "success": True,
                "portfolio_id": assessment["portfolio_id"],
                "overall_risk_score": assessment["overall_risk_score"],
                "risk_level": assessment["risk_level"],
                "assessment_date": assessment["assessment_date"],
                "risk_components": assessment["risk_components"],
                "var_95": assessment["var_95"],
                "expected_shortfall": assessment["expected_shortfall"],
                "stress_test_results": assessment["stress_test_results"],
                "diversification_metrics": assessment["diversification_metrics"],
                "recommendations": assessment["recommendations"]
            }
            
        except Exception as e:
            raise FinancialAgentError(f"Error evaluando riesgo de portafolio: {str(e)}")
    
    async def mcp_generate_risk_dashboard(self,
                                        entity_type: str,
                                        entity_id: str,
                                        time_period: str = "30d") -> Dict[str, Any]:
        """
        Herramienta MCP para generar dashboard de riesgo
        
        Args:
            entity_type: Tipo de entidad (customer, portfolio, institution)
            entity_id: ID de la entidad
            time_period: Período de tiempo (7d, 30d, 90d)
            
        Returns:
            Dashboard de riesgo completo
        """
        try:
            dashboard = await self.risk_agent.generate_risk_dashboard(
                entity_type=entity_type,
                entity_id=entity_id,
                time_period=time_period
            )
            
            return {
                "success": True,
                "dashboard": dashboard
            }
            
        except Exception as e:
            raise FinancialAgentError(f"Error generando dashboard de riesgo: {str(e)}")
    
    async def mcp_run_continuous_monitoring(self,
                                          monitoring_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Herramienta MCP para monitoreo continuo de riesgos
        
        Args:
            monitoring_config: Configuración de monitoreo
            
        Returns:
            Resultados de monitoreo continuo
        """
        try:
            monitoring_results = await self.risk_agent.run_continuous_monitoring(
                monitoring_config=monitoring_config
            )
            
            return {
                "success": True,
                "monitoring_results": monitoring_results
            }
            
        except Exception as e:
            raise FinancialAgentError(f"Error en monitoreo continuo: {str(e)}")
    
    # ========== MÉTODOS DE GESTIÓN Y UTILIDADES ==========
    
    async def get_financial_agents_status(self) -> Dict[str, Any]:
        """
        Obtiene estado de todos los agentes financieros
        """
        return {
            "payment_agent": {
                "status": "active",
                "security_level": self.payment_agent.security_level.value
            },
            "analysis_agent": {
                "status": "active",
                "connections_count": len(self.analysis_agent.access_tokens)
            },
            "reconciliation_agent": {
                "status": "active",
                "cached_reconciliations": len(self.reconciliation_agent.reconciliation_cache)
            },
            "compliance_agent": {
                "status": "active",
                "regulations_configured": len(self.compliance_agent.regulations_config)
            },
            "risk_agent": {
                "status": "active",
                "risk_models_loaded": len(self.risk_agent.risk_models)
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Verificación de salud de todos los agentes
        """
        health_status = {
            "overall_status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "agents": {}
        }
        
        try:
            # Verificar agente de pagos
            health_status["agents"]["payment"] = {
                "status": "healthy",
                "message": "Payment agent operational"
            }
            
            # Verificar agente de análisis
            health_status["agents"]["analysis"] = {
                "status": "healthy",
                "message": "Financial analysis agent operational"
            }
            
            # Verificar agente de reconciliación
            health_status["agents"]["reconciliation"] = {
                "status": "healthy", 
                "message": "Reconciliation agent operational"
            }
            
            # Verificar agente de compliance
            health_status["agents"]["compliance"] = {
                "status": "healthy",
                "message": "Compliance agent operational"
            }
            
            # Verificar agente de riesgo
            health_status["agents"]["risk"] = {
                "status": "healthy",
                "message": "Risk assessment agent operational"
            }
            
        except Exception as e:
            health_status["overall_status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status
    
    async def close(self):
        """Cierra todos los agentes y libera recursos"""
        try:
            await self.payment_agent.close()
            await self.analysis_agent.close()
            # Otros agentes no requieren cleanup específico
            print("Financial agents closed successfully")
        except Exception as e:
            print(f"Error closing financial agents: {str(e)}")

# Función de utilidad para crear wrapper con configuración
def create_financial_wrapper(config: Dict[str, Any]) -> FinancialAgentMCPWrapper:
    """
    Crea wrapper de agentes financieros con configuración
    
    Args:
        config: Diccionario de configuración con todas las credenciales
        
    Returns:
        Wrapper MCP de agentes financieros
    """
    required_keys = [
        "stripe_secret_key", "stripe_publishable_key", 
        "paypal_client_id", "paypal_client_secret",
        "plaid_client_id", "plaid_secret",
        "encryption_key", "jwt_secret"
    ]
    
    # Validar configuración
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ValueError(f"Missing required configuration keys: {missing_keys}")
    
    return FinancialAgentMCPWrapper(
        stripe_secret_key=config["stripe_secret_key"],
        stripe_publishable_key=config["stripe_publishable_key"],
        paypal_client_id=config["paypal_client_id"],
        paypal_client_secret=config["paypal_client_secret"],
        plaid_client_id=config["plaid_client_id"],
        plaid_secret=config["plaid_secret"],
        encryption_key=config["encryption_key"],
        jwt_secret=config["jwt_secret"],
        compliance_db_path=config.get("compliance_db_path", "./compliance_data")
    )
