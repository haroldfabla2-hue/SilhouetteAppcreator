"""
Ejemplos Prácticos - APIs Financieras Avanzadas
Casos de uso reales y implementaciones completas
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Importar agentes financieros
from src.agents.specialized.financial import (
    FinancialAgentMCPWrapper,
    create_financial_wrapper,
    PaymentProcessingAgent,
    FinancialAnalysisAgent,
    ReconciliationAgent,
    ComplianceAgent,
    RiskAssessmentAgent
)

class FinancialIntegrationExamples:
    """
    Ejemplos prácticos de integración con APIs financieras
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.wrapper = create_financial_wrapper(config)
    
    # ========== CASO DE USO 1: E-COMMERCE CON PAGOS RECURRENTES ==========
    
    async def ecommerce_payment_flow_example(self):
        """
        Ejemplo: E-commerce con suscripciones y análisis de churn
        """
        print("\n=== E-COMMERCE PAYMENT FLOW ===")
        
        # 1. Procesar pago inicial de suscripción
        print("1. Procesando pago inicial...")
        payment_result = await self.wrapper.mcp_process_payment(
            amount=99.99,
            currency="USD",
            method="stripe",
            customer_id="cust_123",
            payment_method_id="pm_123",
            user_id="ecommerce_user_1",
            context={"subscription_plan": "premium", "trial": False}
        )
        print(f"Pago procesado: {payment_result['transaction_id']}")
        
        # 2. Crear subscripción recurrente
        print("2. Creando subscripción recurrente...")
        subscription_result = await self.wrapper.mcp_create_subscription(
            customer_id="cust_123",
            price_id="price_monthly_premium",
            payment_method_id="pm_123",
            provider="stripe"
        )
        print(f"Subscripción creada: {subscription_result.get('subscription_id')}")
        
        # 3. Evaluar riesgo crediticio del cliente
        print("3. Evaluando riesgo crediticio...")
        risk_assessment = await self.wrapper.mcp_assess_credit_risk(
            customer_id="cust_123",
            application_data={
                "credit_score": 720,
                "debt_to_income": 0.25,
                "payment_history_score": 0.95,
                "employment_years": 5,
                "bankruptcies": 0
            }
        )
        print(f"Risk score: {risk_assessment['overall_score']}")
        
        # 4. Conectar cuenta bancaria para análisis
        print("4. Conectando cuenta bancaria...")
        bank_connection = await self.wrapper.mcp_connect_bank_account(
            user_id="ecommerce_user_1",
            public_token="public_sandbox_token_123"
        )
        print(f"Cuenta conectada: {bank_connection.get('institution_name')}")
        
        # 5. Análisis de patrones de gasto del cliente
        print("5. Analizando patrones de gasto...")
        spending_analysis = await self.wrapper.mcp_analyze_spending_patterns(
            user_id="ecommerce_user_1",
            period_days=30
        )
        print(f"Gasto mensual promedio: ${spending_analysis['analysis']['summary']['total_spending']:.2f}")
        
        # 6. Compliance check para nuevos usuarios
        print("6. Ejecutando compliance check...")
        compliance_result = await self.wrapper.mcp_run_compliance_assessment(
            regulations=["AML", "PCI_DSS"],
            assessment_type="automated",
            scope={"user_id": "cust_123", "verification_level": "enhanced"}
        )
        print(f"Compliance status: {compliance_result['overall_status']}")
        
        return {
            "payment_result": payment_result,
            "subscription_result": subscription_result,
            "risk_assessment": risk_assessment,
            "bank_connection": bank_connection,
            "spending_analysis": spending_analysis,
            "compliance_result": compliance_result
        }
    
    # ========== CASO DE USO 2: FINTECH DE PRÉSTAMOS ==========
    
    async def fintech_loan_evaluation_example(self):
        """
        Ejemplo: Fintech evaluando préstamo con análisis completo
        """
        print("\n=== FINTECH LOAN EVALUATION ===")
        
        # 1. Cliente solicita préstamo
        print("1. Procesando solicitud de préstamo...")
        application_data = {
            "requested_amount": 25000,
            "purpose": "home_improvement",
            "term_months": 36
        }
        
        # 2. Conectar cuenta bancaria del solicitante
        print("2. Conectando cuentas bancarias del solicitante...")
        bank_connection = await self.wrapper.mcp_connect_bank_account(
            user_id="loan_applicant_456",
            public_token="public_sandbox_token_456"
        )
        print(f"Instituciones conectadas: {bank_connection.get('accounts_count')}")
        
        # 3. Obtener saldos actuales
        print("3. Obteniendo saldos de cuentas...")
        account_balances = await self.wrapper.mcp_get_account_balances(user_id="loan_applicant_456")
        total_balance = sum(acc['balance'] for acc in account_balances['accounts'])
        print(f"Balance total: ${total_balance:.2f}")
        
        # 4. Análisis de flujo de caja
        print("4. Analizando flujo de caja...")
        cash_flow = await self.wrapper.mcp_analyze_cash_flow(
            user_id="loan_applicant_456",
            months=6
        )
        monthly_income = cash_flow['analysis']['summary']['average_monthly_income']
        monthly_expenses = cash_flow['analysis']['summary']['average_monthly_expenses']
        print(f"Ingreso promedio mensual: ${monthly_income:.2f}")
        print(f"Gastos promedio mensuales: ${monthly_expenses:.2f}")
        
        # 5. Evaluación completa de riesgo crediticio
        print("5. Evaluación de riesgo crediticio...")
        credit_assessment = await self.wrapper.mcp_assess_credit_risk(
            customer_id="loan_applicant_456",
            application_data={
                "requested_amount": 25000,
                "debt_to_income": monthly_expenses / monthly_income if monthly_income > 0 else 1.0,
                "credit_score": 680,
                "payment_history_score": 0.88,
                "employment_years": 3,
                "bankruptcies": 0,
                "previous_loans": 2,
                "default_history": 0
            },
            historical_data={
                "bank_account_age_months": 24,
                "avg_balance_6_months": total_balance,
                "transaction_frequency": "monthly"
            }
        )
        print(f"Risk score: {credit_assessment['overall_score']:.3f}")
        print(f"Risk level: {credit_assessment['risk_level']}")
        
        # 6. Compliance AML para préstamos
        print("6. Monitoreo AML...")
        # Simular transacciones del solicitante
        sample_transactions = [
            {"transaction_id": f"tx_{i}", "amount": 500 + i * 100, "merchant": "various"}
            for i in range(20)
        ]
        
        aml_monitoring = await self.wrapper.mcp_monitor_aml_activities(
            transactions=sample_transactions,
            risk_threshold=0.6
        )
        print(f"AML alerts: {len(aml_monitoring['aml_report']['aml_alerts'])}")
        
        # 7. Generar reporte financiero completo
        print("7. Generando reporte financiero...")
        financial_report = await self.wrapper.mcp_generate_financial_report(
            user_id="loan_applicant_456",
            report_type="lender_due_diligence",
            period_months=6
        )
        
        return {
            "application_data": application_data,
            "bank_connection": bank_connection,
            "account_balances": account_balances,
            "cash_flow_analysis": cash_flow,
            "credit_assessment": credit_assessment,
            "aml_monitoring": aml_monitoring,
            "financial_report": financial_report
        }
    
    # ========== CASO DE USO 3: MARKETPLACE DE PAGOS ==========
    
    async def marketplace_payment_reconciliation_example(self):
        """
        Ejemplo: Marketplace reconciliando pagos entre múltiples fuentes
        """
        print("\n=== MARKETPLACE PAYMENT RECONCILIATION ===")
        
        # 1. Simular transacciones del período
        print("1. Simulando transacciones del período...")
        period_start = datetime.now() - timedelta(days=30)
        period_end = datetime.now()
        
        # 2. Reconciliar Stripe vs PayPal
        print("2. Reconciliando Stripe vs PayPal...")
        stripe_paypal_recon = await self.wrapper.mcp_reconcile_transactions(
            start_date=period_start.strftime('%Y-%m-%d'),
            end_date=period_end.strftime('%Y-%m-%d'),
            source_1="stripe",
            source_2="paypal",
            confidence_threshold=0.85
        )
        print(f"Transacciones reconciliadas: {stripe_paypal_recon['summary']['matched_count']}")
        print(f"Discrepancias: ${stripe_paypal_recon['summary']['discrepancy_amount']:.2f}")
        
        # 3. Reconciliar con sistema contable (QuickBooks)
        print("3. Reconciliando con sistema contable...")
        quickbooks_recon = await self.wrapper.mcp_reconcile_transactions(
            start_date=period_start.strftime('%Y-%m-%d'),
            end_date=period_end.strftime('%Y-%m-%d'),
            source_1="stripe",
            source_2="quickbooks",
            confidence_threshold=0.80
        )
        
        # 4. Reconciliación múltiple automática
        print("4. Reconciliación múltiple automática...")
        multi_source_recon = await self.wrapper.mcp_auto_reconcile_multiple_sources(
            start_date=period_start.strftime('%Y-%m-%d'),
            end_date=period_end.strftime('%Y-%m-%d'),
            sources=["stripe", "paypal", "quickbooks", "bank"],
            primary_source="quickbooks"
        )
        
        # 5. Evaluar riesgo de transacciones de marketplace
        print("5. Evaluando riesgo de transacciones...")
        sample_transactions = [
            {
                "transaction_id": f"marketplace_tx_{i}",
                "amount": 150 + i * 25,
                "merchant_id": f"vendor_{i % 10}",
                "location": ["New York", "Los Angeles", "Chicago", "Miami"][i % 4],
                "timestamp": (datetime.now() - timedelta(days=i)).isoformat(),
                "customer_id": f"customer_{i % 50}"
            }
            for i in range(25)
        ]
        
        for tx_data in sample_transactions[:5]:  # Evaluar solo las primeras 5
            risk_profile = await self.wrapper.mcp_assess_transaction_risk(tx_data)
            print(f"Tx {tx_data['transaction_id']}: Risk score {risk_profile['overall_risk_score']:.3f}")
        
        # 6. Compliance y reportes regulatorios
        print("6. Generando reportes de compliance...")
        compliance_report = await self.wrapper.mcp_generate_regulatory_report(
            report_type="Marketplace_Transaction_Report",
            regulation="PCI_DSS",
            start_date=period_start.strftime('%Y-%m-%d'),
            end_date=period_end.strftime('%Y-%m-%d'),
            output_format="pdf"
        )
        
        return {
            "stripe_paypal_reconciliation": stripe_paypal_recon,
            "quickbooks_reconciliation": quickbooks_recon,
            "multi_source_reconciliation": multi_source_recon,
            "compliance_report": compliance_report
        }
    
    # ========== CASO DE USO 4: BANCO DIGITAL ==========
    
    async def digital_bank_risk_monitoring_example(self):
        """
        Ejemplo: Banco digital con monitoreo continuo de riesgos
        """
        print("\n=== DIGITAL BANK RISK MONITORING ===")
        
        # 1. Configuración de monitoreo continuo
        print("1. Configurando monitoreo continuo...")
        monitoring_config = {
            "entities": {
                "customer": ["cust_001", "cust_002", "cust_003"],
                "portfolio": ["portfolio_default", "portfolio_premium"]
            },
            "thresholds": {
                "credit_risk": 0.7,
                "transaction_risk": 0.8,
                "operational_risk": 0.6
            },
            "alert_frequency": "real_time"
        }
        
        # 2. Ejecutar monitoreo continuo
        print("2. Ejecutando monitoreo continuo...")
        monitoring_results = await self.wrapper.mcp_run_continuous_monitoring(monitoring_config)
        print(f"Entidades monitoreadas: {monitoring_results['entities_monitored']}")
        print(f"Alertas generadas: {monitoring_results['alerts_generated']}")
        
        # 3. Dashboard de riesgo para cada tipo de entidad
        print("3. Generando dashboards de riesgo...")
        
        # Dashboard para cliente
        customer_dashboard = await self.wrapper.mcp_generate_risk_dashboard(
            entity_type="customer",
            entity_id="cust_001",
            time_period="30d"
        )
        print(f"Cliente cust_001 - Risk level: {customer_dashboard['dashboard']['summary']['overall_risk_level']}")
        
        # Dashboard para portafolio
        portfolio_dashboard = await self.wrapper.mcp_generate_risk_dashboard(
            entity_type="portfolio",
            entity_id="portfolio_premium",
            time_period="90d"
        )
        print(f"Portafolio premium - Risk level: {portfolio_dashboard['dashboard']['summary']['overall_risk_level']}")
        
        # 4. Evaluación de riesgo de portafolio
        print("4. Evaluando riesgo de portafolio...")
        sample_portfolio = {
            "portfolio_id": "portfolio_premium",
            "holdings": [
                {"asset_class": "stocks", "value": 100000, "credit_rating": "A"},
                {"asset_class": "bonds", "value": 75000, "credit_rating": "AAA"},
                {"asset_class": "real_estate", "value": 50000, "credit_rating": "BBB"},
                {"asset_class": "cash", "value": 25000, "credit_rating": "AAA"}
            ]
        }
        
        portfolio_risk = await self.wrapper.mcp_assess_portfolio_risk(sample_portfolio)
        print(f"Portfolio VaR (95%): ${portfolio_risk['var_95']:,.2f}")
        print(f"Expected Shortfall: ${portfolio_risk['expected_shortfall']:,.2f}")
        
        # 5. Compliance continuo
        print("5. Evaluando compliance continuo...")
        pci_validation = await self.wrapper.mcp_validate_pci_dss_compliance()
        print(f"PCI DSS Score: {pci_validation['overall_score']:.2f}")
        
        # 6. Audit trail y reportes
        print("6. Generando reportes de auditoría...")
        audit_report = await self.wrapper.mcp_generate_audit_report(
            start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            end_date=datetime.now().strftime('%Y-%m-%d'),
            filters={"risk_level": "high"}
        )
        print(f"Eventos de auditoría: {audit_report['audit_report']['total_events']}")
        
        return {
            "monitoring_results": monitoring_results,
            "customer_dashboard": customer_dashboard,
            "portfolio_dashboard": portfolio_dashboard,
            "portfolio_risk": portfolio_risk,
            "pci_validation": pci_validation,
            "audit_report": audit_report
        }
    
    # ========== CASO DE USO 5: ANÁLISIS FINANCIERO AVANZADO ==========
    
    async def advanced_financial_analysis_example(self):
        """
        Ejemplo: Análisis financiero avanzado para planificación
        """
        print("\n=== ADVANCED FINANCIAL ANALYSIS ===")
        
        # 1. Conectar múltiples cuentas del usuario
        print("1. Conectando cuentas financieras...")
        accounts_connected = []
        
        # Cuenta principal
        main_account = await self.wrapper.mcp_connect_bank_account(
            user_id="financial_planning_user",
            public_token="main_account_token"
        )
        accounts_connected.append(main_account)
        
        # 2. Análisis completo de patrones de gasto
        print("2. Análisis de patrones de gasto...")
        spending_patterns = await self.wrapper.mcp_analyze_spending_patterns(
            user_id="financial_planning_user",
            period_days=90  # 3 meses
        )
        
        # Extraer insights clave
        total_spending = spending_patterns['analysis']['summary']['total_spending']
        top_category = max(
            spending_patterns['analysis']['patterns']['spending_by_category'].items(),
            key=lambda x: x[1]
        )
        print(f"Gasto total (90 días): ${total_spending:.2f}")
        print(f"Categoría principal: {top_category[0]} (${top_category[1]:.2f})")
        
        # 3. Análisis de flujo de caja a largo plazo
        print("3. Análisis de flujo de caja...")
        cash_flow_analysis = await self.wrapper.mcp_analyze_cash_flow(
            user_id="financial_planning_user",
            months=12  # Un año
        )
        
        net_flow = cash_flow_analysis['analysis']['summary']['net_flow']
        savings_rate = (net_flow / cash_flow_analysis['analysis']['summary']['total_income'] * 100) if cash_flow_analysis['analysis']['summary']['total_income'] > 0 else 0
        print(f"Flujo neto anual: ${net_flow:.2f}")
        print(f"Tasa de ahorro: {savings_rate:.1f}%")
        
        # 4. Detección de anomalías
        print("4. Detectando anomalías financieras...")
        anomaly_detection = await self.wrapper.mcp_detect_financial_anomalies(
            user_id="financial_planning_user",
            anomaly_threshold=2.5  # Más estricto
        )
        print(f"Anomalías detectadas: {len(anomaly_detection['anomalies'])}")
        
        # 5. Dashboard de riesgo financiero personal
        print("5. Dashboard de riesgo personal...")
        risk_dashboard = await self.wrapper.mcp_generate_risk_dashboard(
            entity_type="customer",
            entity_id="financial_planning_user",
            time_period="30d"
        )
        
        # 6. Reporte financiero completo
        print("6. Generando reporte financiero completo...")
        comprehensive_report = await self.wrapper.mcp_generate_financial_report(
            user_id="financial_planning_user",
            report_type="comprehensive_financial_analysis",
            period_months=3
        )
        
        # 7. Recomendaciones personalizadas
        print("7. Generando recomendaciones...")
        recommendations = []
        
        if savings_rate < 10:
            recommendations.append("Aumentar tasa de ahorro a 15% o superior")
        
        if len(anomaly_detection['anomalies']) > 0:
            recommendations.append("Revisar transacciones anómalas detectadas")
        
        # Analizar categorías de gasto para optimización
        spending_by_category = spending_patterns['analysis']['patterns']['spending_by_category']
        high_spending_categories = [cat for cat, amount in spending_by_category.items() if amount > total_spending * 0.3]
        
        if high_spending_categories:
            recommendations.append(f"Optimizar gastos en categorías: {', '.join(high_spending_categories)}")
        
        print("Recomendaciones:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
        
        return {
            "spending_patterns": spending_patterns,
            "cash_flow_analysis": cash_flow_analysis,
            "anomaly_detection": anomaly_detection,
            "risk_dashboard": risk_dashboard,
            "comprehensive_report": comprehensive_report,
            "recommendations": recommendations
        }

# ========== FUNCIÓN PRINCIPAL PARA EJECUTAR EJEMPLOS ==========

async def run_financial_examples():
    """
    Ejecuta todos los ejemplos de integración financiera
    """
    # Configuración de ejemplo (usar credenciales reales en producción)
    config = {
        "stripe_secret_key": "sk_test_your_stripe_secret_key",
        "stripe_publishable_key": "pk_test_your_stripe_publishable_key",
        "paypal_client_id": "your_paypal_client_id",
        "paypal_client_secret": "your_paypal_secret",
        "plaid_client_id": "your_plaid_client_id",
        "plaid_secret": "your_plaid_secret",
        "encryption_key": "your_32_character_encryption_key_1234",
        "jwt_secret": "your_jwt_secret_key_for_dev_32chars",
        "compliance_db_path": "./compliance_data"
    }
    
    # Crear instancia de ejemplos
    examples = FinancialIntegrationExamples(config)
    
    print("🚀 INICIANDO EJEMPLOS DE INTEGRACIÓN FINANCIERA")
    print("=" * 60)
    
    try:
        # Ejecutar todos los ejemplos
        results = {}
        
        # Ejemplo 1: E-commerce
        results['ecommerce'] = await examples.ecommerce_payment_flow_example()
        
        # Ejemplo 2: Fintech préstamos
        results['fintech_loans'] = await examples.fintech_loan_evaluation_example()
        
        # Ejemplo 3: Marketplace
        results['marketplace'] = await examples.marketplace_payment_reconciliation_example()
        
        # Ejemplo 4: Banco digital
        results['digital_bank'] = await examples.digital_bank_risk_monitoring_example()
        
        # Ejemplo 5: Análisis avanzado
        results['advanced_analysis'] = await examples.advanced_financial_analysis_example()
        
        print("\n✅ TODOS LOS EJEMPLOS COMPLETADOS EXITOSAMENTE")
        print("=" * 60)
        
        return results
        
    except Exception as e:
        print(f"\n❌ ERROR EJECUTANDO EJEMPLOS: {str(e)}")
        return None
    
    finally:
        # Cleanup
        await examples.wrapper.close()

# ========== EJEMPLOS ESPECÍFICOS PARA MCP ==========

async def simple_payment_example():
    """
    Ejemplo simple de procesamiento de pago para MCP
    """
    config = {
        "stripe_secret_key": "sk_test_simple_example",
        "stripe_publishable_key": "pk_test_simple_example",
        "paypal_client_id": "simple_paypal_id",
        "paypal_client_secret": "simple_paypal_secret",
        "plaid_client_id": "simple_plaid_id",
        "plaid_secret": "simple_plaid_secret",
        "encryption_key": "simple_32_char_encryption_key_1",
        "jwt_secret": "simple_jwt_secret_for_examples_only"
    }
    
    wrapper = create_financial_wrapper(config)
    
    try:
        # Procesar pago simple
        result = await wrapper.mcp_process_payment(
            amount=29.99,
            currency="USD",
            method="stripe"
        )
        return result
        
    finally:
        await wrapper.close()

async def simple_financial_analysis_example():
    """
    Ejemplo simple de análisis financiero para MCP
    """
    config = {
        "stripe_secret_key": "sk_test_analysis_example",
        "stripe_publishable_key": "pk_test_analysis_example",
        "paypal_client_id": "analysis_paypal_id",
        "paypal_client_secret": "analysis_paypal_secret",
        "plaid_client_id": "analysis_plaid_id",
        "plaid_secret": "analysis_plaid_secret",
        "encryption_key": "analysis_32_char_encryption_key_2",
        "jwt_secret": "analysis_jwt_secret_for_examples_only"
    }
    
    wrapper = create_financial_wrapper(config)
    
    try:
        # Conectar cuenta bancaria
        bank_result = await wrapper.mcp_connect_bank_account(
            user_id="demo_user",
            public_token="demo_public_token"
        )
        
        # Analizar patrones de gasto
        spending_result = await wrapper.mcp_analyze_spending_patterns(
            user_id="demo_user",
            period_days=30
        )
        
        return {
            "bank_connection": bank_result,
            "spending_analysis": spending_result
        }
        
    finally:
        await wrapper.close()

# ========== SCRIPT DE EJECUCIÓN ==========

if __name__ == "__main__":
    print("Ejecutando ejemplos de integración financiera...")
    
    # Ejecutar ejemplos principales
    results = asyncio.run(run_financial_examples())
    
    if results:
        print("\n📊 RESUMEN DE RESULTADOS:")
        for example_name, result in results.items():
            print(f"- {example_name}: ✅ Completado")
    
    print("\n🎯 Para ejecutar ejemplos individuales:")
    print("  python examples/financial_integration_examples.py simple_payment_example")
    print("  python examples/financial_integration_examples.py simple_financial_analysis_example")
