# Agentes Especializados - APIs Financieras Avanzadas
# Integración profunda con Stripe, PayPal, Plaid, QuickBooks, Xero

from .financial_agent_wrapper import FinancialAgentMCPWrapper, create_financial_wrapper

# Re-exportar agentes individuales para acceso directo
from .financial.payment_processing_agent import PaymentProcessingAgent
from .financial.financial_analysis_agent import FinancialAnalysisAgent
from .financial.reconciliation_agent import ReconciliationAgent
from .financial.compliance_agent import ComplianceAgent
from .financial.risk_assessment_agent import RiskAssessmentAgent

# Re-exportar enums y dataclasses
from .financial.payment_processing_agent import PaymentMethod, SecurityLevel
from .financial.reconciliation_agent import ReconciliationSource, MatchStrategy
from .financial.compliance_agent import Regulation, RiskLevel as ComplianceRiskLevel
from .financial.risk_assessment_agent import RiskCategory

__all__ = [
    # Wrapper principal
    "FinancialAgentMCPWrapper",
    "create_financial_wrapper",
    
    # Agentes individuales
    "PaymentProcessingAgent",
    "FinancialAnalysisAgent", 
    "ReconciliationAgent",
    "ComplianceAgent",
    "RiskAssessmentAgent",
    
    # Enums
    "PaymentMethod",
    "SecurityLevel", 
    "ReconciliationSource",
    "MatchStrategy",
    "Regulation",
    "ComplianceRiskLevel",
    "RiskCategory"
]

# Configuración por defecto para desarrollo/testing
DEFAULT_FINANCIAL_CONFIG = {
    "stripe_secret_key": "sk_test_your_key_here",
    "stripe_publishable_key": "pk_test_your_key_here", 
    "paypal_client_id": "your_paypal_client_id",
    "paypal_client_secret": "your_paypal_secret",
    "plaid_client_id": "your_plaid_client_id",
    "plaid_secret": "your_plaid_secret",
    "encryption_key": "your_32_character_encryption_key_here",
    "jwt_secret": "your_jwt_secret_key_here",
    "compliance_db_path": "./compliance_data"
}

def get_financial_agents_info() -> dict:
    """
    Retorna información sobre los agentes financieros disponibles
    
    Returns:
        Diccionario con información de agentes
    """
    return {
        "payment_processing_agent": {
            "description": "Procesamiento de pagos con Stripe y PayPal",
            "capabilities": [
                "Procesamiento de pagos únicos",
                "Gestión de subscripciones recurrentes", 
                "Manejo de webhooks",
                "Seguridad PCI DSS",
                "Audit trails"
            ],
            "supported_providers": ["stripe", "paypal"],
            "supported_currencies": ["USD", "EUR", "GBP", "MXN"],
            "security_features": ["PCI DSS", "Encryption", "Audit Trail"]
        },
        "financial_analysis_agent": {
            "description": "Análisis financiero con integración Plaid",
            "capabilities": [
                "Conexión de cuentas bancarias",
                "Análisis de patrones de gasto", 
                "Análisis de flujo de caja",
                "Detección de anomalías",
                "Generación de reportes financieros"
            ],
            "supported_apis": ["plaid"],
            "analysis_types": ["spending_patterns", "cash_flow", "anomaly_detection"],
            "report_formats": ["json", "pdf", "excel"]
        },
        "reconciliation_agent": {
            "description": "Reconciliación automática entre sistemas contables",
            "capabilities": [
                "Reconciliación entre múltiples fuentes",
                "Matching inteligente de transacciones",
                "Validación automática de reconciliación", 
                "Detección de discrepancias",
                "Reportes de reconciliación"
            ],
            "supported_sources": ["bank", "stripe", "paypal", "quickbooks", "xero"],
            "matching_strategies": ["exact", "amount_date", "fuzzy", "intelligent"],
            "validation_features": ["confidence_scoring", "threshold_validation"]
        },
        "compliance_agent": {
            "description": "Gestión de compliance y reportes regulatorios",
            "capabilities": [
                "Evaluación PCI DSS",
                "Monitoreo AML",
                "Reportes SOX",
                "Gestión de audit trails",
                "Generación de reportes regulatorios"
            ],
            "supported_regulations": ["PCI_DSS", "SOX", "AML", "GDPR", "CCPA"],
            "compliance_types": ["automated_checks", "manual_validation", "continuous_monitoring"],
            "report_formats": ["pdf", "json", "excel"]
        },
        "risk_assessment_agent": {
            "description": "Evaluación y gestión de riesgos financieros",
            "capabilities": [
                "Evaluación de riesgo crediticio",
                "Análisis de riesgo de transacciones",
                "Evaluación de riesgo de portafolio",
                "Monitoreo continuo de riesgos",
                "Dashboards de riesgo"
            ],
            "risk_categories": ["credit", "operational", "market", "liquidity", "compliance"],
            "assessment_types": ["credit_scoring", "transaction_risk", "portfolio_risk"],
            "monitoring_features": ["real_time_alerts", "trend_analysis", "anomaly_detection"]
        }
    }

def validate_financial_config(config: dict) -> dict:
    """
    Valida configuración de agentes financieros
    
    Args:
        config: Configuración a validar
        
    Returns:
        Resultado de validación
    """
    required_keys = [
        "stripe_secret_key", "stripe_publishable_key", 
        "paypal_client_id", "paypal_client_secret",
        "plaid_client_id", "plaid_secret",
        "encryption_key", "jwt_secret"
    ]
    
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "missing_keys": []
    }
    
    # Verificar claves requeridas
    for key in required_keys:
        if key not in config:
            validation_result["missing_keys"].append(key)
            validation_result["valid"] = False
    
    # Validar formato de claves
    if "stripe_secret_key" in config:
        if not config["stripe_secret_key"].startswith("sk_"):
            validation_result["warnings"].append("Stripe secret key should start with 'sk_'")
    
    if "stripe_publishable_key" in config:
        if not config["stripe_publishable_key"].startswith("pk_"):
            validation_result["warnings"].append("Stripe publishable key should start with 'pk_'")
    
    # Validar longitud de claves de encriptación
    if "encryption_key" in config:
        if len(config["encryption_key"]) != 32:
            validation_result["errors"].append("Encryption key must be exactly 32 characters")
            validation_result["valid"] = False
    
    if "jwt_secret" in config:
        if len(config["jwt_secret"]) < 32:
            validation_result["warnings"].append("JWT secret should be at least 32 characters for security")
    
    validation_result["errors"].extend([f"Missing required key: {key}" for key in validation_result["missing_keys"]])
    
    return validation_result