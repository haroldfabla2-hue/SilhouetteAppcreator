"""
Configuración específica del Sistema de Security Scanning y Data Redaction
Centraliza configuración para PII detection, vulnerability scanning, compliance, etc.
"""

import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum


class SecurityLevel(Enum):
    """Niveles de seguridad disponibles"""
    BASIC = "basic"
    STANDARD = "standard"
    HIGH = "high"
    MAXIMUM = "maximum"
    COMPREHENSIVE = "comprehensive"


class ComplianceFramework(Enum):
    """Frameworks de compliance soportados"""
    GDPR = "GDPR"
    CCPA = "CCPA"
    SOX = "SOX"
    HIPAA = "HIPAA"
    PCI_DSS = "PCI_DSS"


@dataclass
class PIISecurityConfig:
    """Configuración para detección y redacción de PII"""
    enabled: bool = True
    compliance_framework: ComplianceFramework = ComplianceFramework.GDPR
    confidence_threshold: float = 0.8
    preserve_format: bool = True
    mask_character: str = "*"
    mask_percentage: float = 0.75
    auto_redact: bool = True
    log_pii_access: bool = True
    pii_categories: List[str] = field(default_factory=lambda: [
        'email', 'phone', 'ssn', 'credit_card', 'ip_address', 
        'passport', 'driver_license', 'bank_account'
    ])


@dataclass
class VulnerabilityScanConfig:
    """Configuración para escaneo de vulnerabilidades"""
    enabled: bool = True
    scan_depth: SecurityLevel = SecurityLevel.COMPREHENSIVE
    auto_scan_schedule: str = "daily"  # hourly, daily, weekly, manual
    scan_timeout: int = 300  # 5 minutos
    max_concurrent_scans: int = 3
    auto_remediate: bool = False
    report_format: str = "json"  # json, html, pdf
    scan_agents: List[str] = field(default_factory=lambda: [
        'database_operations_agent', 'file_processing_agent', 
        'web_scraping_agent', 'python_executor_agent', 'git_operations_agent'
    ])
    exclude_paths: List[str] = field(default_factory=lambda: [
        '/static/', '/assets/', '/css/', '/js/', '/images/', 
        '/health', '/metrics', '/docs', '/swagger'
    ])


@dataclass
class RateLimitConfig:
    """Configuración para rate limiting"""
    enabled: bool = True
    default_rate_per_minute: int = 100
    burst_limit_per_10s: int = 10
    burst_window_seconds: int = 10
    cleanup_days: int = 7
    auto_block_threshold: int = 10
    block_duration_hours: int = 24
    endpoint_limits: Dict[str, int] = field(default_factory=lambda: {
        '/api/login': 5,
        '/api/register': 10,
        '/api/reset-password': 3,
        '/api/upload': 20,
        '/api/search': 100,
        '/api/export': 5,
        '/api/admin': 50
    })


@dataclass
class FileSecurityConfig:
    """Configuración para seguridad de archivos"""
    scanning_enabled: bool = True
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: List[str] = field(default_factory=lambda: [
        '.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv', '.json', '.xml'
    ])
    allowed_mime_types: List[str] = field(default_factory=lambda: [
        'text/plain', 'text/csv', 'application/pdf', 'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/json', 'text/xml'
    ])
    block_executable: bool = True
    antivirus_scan: bool = False
    quarantine_suspicious: bool = True
    virus_signature_db: Optional[str] = None


@dataclass
class ThreatIntelligenceConfig:
    """Configuración para threat intelligence"""
    enabled: bool = False
    feeds_urls: List[str] = field(default_factory=list)
    cache_ttl_seconds: int = 3600  # 1 hora
    auto_block_ips: bool = True
    block_threshold: int = 10
    reputation_threshold: float = 0.7
    update_frequency_hours: int = 24
    sources: List[str] = field(default_factory=lambda: [
        'otx_alienvault', 'abuseipdb', 'virustotal', 'malware_bazaar'
    ])


@dataclass
class ComplianceConfig:
    """Configuración para compliance monitoring"""
    gdpr_enabled: bool = True
    ccpa_enabled: bool = True
    sox_enabled: bool = True
    hipaa_enabled: bool = False
    pci_dss_enabled: bool = False
    audit_frequency: str = "monthly"  # weekly, monthly, quarterly
    auto_generate_reports: bool = False
    data_retention_days: int = 90
    consent_management: bool = True
    data_subject_rights: bool = True
    breach_notification: bool = True
    audit_trail: bool = True


@dataclass
class SecurityHeadersConfig:
    """Configuración para security headers"""
    enabled: bool = True
    strict_mode: bool = True
    hsts_enabled: bool = True
    hsts_max_age: int = 31536000  # 1 año
    include_subdomains: bool = True
    preload: bool = False
    xss_protection: bool = True
    frame_options: str = "DENY"  # DENY, SAMEORIGIN
    content_type_options: bool = True
    referrer_policy: str = "strict-origin-when-cross-origin"
    csp_enabled: bool = True
    csp_level: SecurityLevel = SecurityLevel.STANDARD
    custom_csp_directives: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecuritySystemConfig:
    """Configuración principal del sistema de seguridad"""
    # Componentes principales
    pii_config: PIISecurityConfig = field(default_factory=PIISecurityConfig)
    vulnerability_config: VulnerabilityScanConfig = field(default_factory=VulnerabilityScanConfig)
    rate_limit_config: RateLimitConfig = field(default_factory=RateLimitConfig)
    file_security_config: FileSecurityConfig = field(default_factory=FileSecurityConfig)
    threat_intel_config: ThreatIntelligenceConfig = field(default_factory=ThreatIntelligenceConfig)
    compliance_config: ComplianceConfig = field(default_factory=ComplianceConfig)
    headers_config: SecurityHeadersConfig = field(default_factory=SecurityHeadersConfig)
    
    # Configuración general
    logging_enabled: bool = True
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    database_path: str = "/tmp/security_system.db"
    backup_enabled: bool = True
    backup_retention_days: int = 30
    encryption_enabled: bool = False
    performance_monitoring: bool = True
    alert_on_critical: bool = True
    
    # Configuración de entorno
    environment: str = "development"  # development, testing, staging, production
    debug_mode: bool = False
    testing_mode: bool = False
    
    def __post_init__(self):
        """Ajustes post-inicialización"""
        # Ajustar configuración según entorno
        self._apply_environment_config()
    
    def _apply_environment_config(self):
        """Aplica configuraciones específicas por entorno"""
        env_configs = {
            'development': {
                'debug_mode': True,
                'log_level': 'DEBUG',
                'strict_mode': False,
                'auto_remediate': False,
                'alert_on_critical': False
            },
            'testing': {
                'debug_mode': True,
                'log_level': 'INFO',
                'pii_config': PIISecurityConfig(enabled=False),
                'file_security_config': FileSecurityConfig(scanning_enabled=False),
                'threat_intel_config': ThreatIntelligenceConfig(enabled=False)
            },
            'staging': {
                'debug_mode': False,
                'log_level': 'INFO',
                'strict_mode': True,
                'alert_on_critical': True,
                'auto_remediate': False
            },
            'production': {
                'debug_mode': False,
                'log_level': 'WARNING',
                'strict_mode': True,
                'encryption_enabled': True,
                'backup_enabled': True,
                'performance_monitoring': True,
                'alert_on_critical': True,
                'auto_remediate': False  # Cambiar a True con cuidado
            }
        }
        
        if self.environment in env_configs:
            env_config = env_configs[self.environment]
            for key, value in env_config.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                elif '_config' in key:
                    config_attr = key[:-7]  # Remover '_config'
                    if hasattr(self, config_attr):
                        config_obj = getattr(self, config_attr)
                        if hasattr(config_obj, 'enabled'):
                            setattr(config_obj, 'enabled', value)


class SecurityConfigManager:
    """Gestor de configuración del sistema de seguridad"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.path.join(
            os.path.dirname(__file__), 'security_config.json'
        )
        self.config = self._load_config()
    
    def _load_config(self) -> SecuritySystemConfig:
        """Carga configuración desde archivo o variables de entorno"""
        # Intentar cargar desde archivo
        if os.path.exists(self.config_file):
            try:
                import json
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                return self._dict_to_config(config_data)
            except Exception as e:
                print(f"Error cargando configuración: {e}")
        
        # Cargar desde variables de entorno
        env_config = self._load_from_environment()
        if env_config:
            return SecuritySystemConfig(**env_config)
        
        # Configuración por defecto
        return SecuritySystemConfig()
    
    def _load_from_environment(self) -> Dict[str, Any]:
        """Carga configuración desde variables de entorno"""
        env_vars = {}
        
        # Mapeo de variables de entorno
        env_mapping = {
            'SEC_ENVIRONMENT': ('environment', str),
            'SEC_PII_ENABLED': ('pii_config.enabled', lambda x: x.lower() == 'true'),
            'SEC_PII_COMPLIANCE': ('pii_config.compliance_framework', ComplianceFramework),
            'SEC_VULN_SCAN_ENABLED': ('vulnerability_config.enabled', lambda x: x.lower() == 'true'),
            'SEC_RATE_LIMIT': ('rate_limit_config.default_rate_per_minute', int),
            'SEC_MAX_FILE_SIZE': ('file_security_config.max_file_size', int),
            'SEC_LOG_LEVEL': ('log_level', str),
            'SEC_DB_PATH': ('database_path', str),
            'SEC_ENCRYPTION': ('encryption_enabled', lambda x: x.lower() == 'true'),
            'SEC_ALERTS': ('alert_on_critical', lambda x: x.lower() == 'true'),
            'SEC_THREAT_INTEL': ('threat_intel_config.enabled', lambda x: x.lower() == 'true'),
        }
        
        for env_var, (config_path, converter) in env_mapping.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    if callable(converter):
                        env_vars[config_path] = converter(env_value)
                    else:
                        env_vars[config_path] = converter(env_value)
                except (ValueError, TypeError) as e:
                    print(f"Error convirtiendo {env_var}: {env_value} - {e}")
        
        return env_vars
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> SecuritySystemConfig:
        """Convierte diccionario a objeto de configuración"""
        # Implementación simplificada
        return SecuritySystemConfig(**config_dict)
    
    def get_config(self) -> SecuritySystemConfig:
        """Obtiene configuración actual"""
        return self.config
    
    def update_config(self, updates: Dict[str, Any]) -> SecuritySystemConfig:
        """Actualiza configuración"""
        for key, value in updates.items():
            keys = key.split('.')
            obj = self.config
            
            # Navegar hasta el objeto padre
            for k in keys[:-1]:
                if hasattr(obj, k):
                    obj = getattr(obj, k)
                else:
                    break
            
            # Actualizar valor
            final_key = keys[-1]
            if hasattr(obj, final_key):
                setattr(obj, final_key, value)
        
        self._save_config()
        return self.config
    
    def _save_config(self):
        """Guarda configuración a archivo"""
        try:
            import json
            
            def config_to_dict(obj):
                """Convierte objeto de configuración a diccionario"""
                if hasattr(obj, '__dataclass_fields__'):
                    return {field.name: config_to_dict(getattr(obj, field.name)) 
                           for field in obj.__dataclass_fields__.values()}
                elif isinstance(obj, (list, tuple)):
                    return [config_to_dict(item) for item in obj]
                elif isinstance(obj, dict):
                    return {k: config_to_dict(v) for k, v in obj.items()}
                else:
                    return obj
            
            config_dict = config_to_dict(self.config)
            
            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=2, default=str)
        
        except Exception as e:
            print(f"Error guardando configuración: {e}")
    
    def validate_config(self) -> Dict[str, List[str]]:
        """Valida configuración actual"""
        errors = []
        warnings = []
        
        # Validar paths
        if not self.config.database_path:
            errors.append("Database path is required")
        
        # Validar rate limits
        if self.config.rate_limit_config.default_rate_per_minute <= 0:
            errors.append("Default rate limit must be positive")
        
        if self.config.rate_limit_config.burst_limit_per_10s > self.config.rate_limit_config.default_rate_per_minute:
            warnings.append("Burst limit should not exceed default rate limit")
        
        # Validar tamaños de archivo
        if self.config.file_security_config.max_file_size <= 0:
            errors.append("Max file size must be positive")
        
        if self.config.file_security_config.max_file_size > 100 * 1024 * 1024:
            warnings.append("Max file size is very large (>100MB)")
        
        # Validar timeouts
        if self.config.vulnerability_config.scan_timeout <= 0:
            errors.append("Vulnerability scan timeout must be positive")
        
        # Validar thresholds
        if not 0 <= self.config.pii_config.confidence_threshold <= 1:
            errors.append("PII confidence threshold must be between 0 and 1")
        
        # Validar URLs de threat intelligence
        if self.config.threat_intel_config.enabled and not self.config.threat_intel_config.feeds_urls:
            warnings.append("Threat intelligence enabled but no feed URLs configured")
        
        return {
            'errors': errors,
            'warnings': warnings
        }
    
    def reset_to_defaults(self, environment: Optional[str] = None) -> SecuritySystemConfig:
        """Resetea configuración a valores por defecto"""
        if environment:
            self.config.environment = environment
        
        self.config = SecuritySystemConfig(environment=self.config.environment)
        self._save_config()
        return self.config
    
    def export_config(self, format: str = 'json') -> str:
        """Exporta configuración"""
        def config_to_dict(obj):
            if hasattr(obj, '__dataclass_fields__'):
                return {field.name: config_to_dict(getattr(obj, field.name)) 
                       for field in obj.__dataclass_fields__.values()}
            elif isinstance(obj, (list, tuple)):
                return [config_to_dict(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: config_to_dict(v) for k, v in obj.items()}
            elif hasattr(obj, 'value'):  # Enum
                return obj.value
            else:
                return obj
        
        config_dict = config_to_dict(self.config)
        
        if format == 'json':
            import json
            return json.dumps(config_dict, indent=2, default=str)
        elif format == 'yaml':
            import yaml
            return yaml.dump(config_dict, default_flow_style=False)
        else:
            return str(config_dict)


# Instancia global de configuración
security_config_manager = SecurityConfigManager()
default_security_config = security_config_manager.get_config()


# Configuraciones predefinidas por entorno
PREDEFINED_CONFIGS = {
    'development': SecuritySystemConfig(
        environment='development',
        debug_mode=True,
        log_level='DEBUG',
        pii_config=PIISecurityConfig(enabled=True, auto_redact=False),
        vulnerability_config=VulnerabilityScanConfig(
            enabled=True, 
            scan_depth=SecurityLevel.BASIC,
            auto_scan_schedule='manual'
        ),
        headers_config=SecurityHeadersConfig(strict_mode=False),
        threat_intel_config=ThreatIntelligenceConfig(enabled=False),
        compliance_config=ComplianceConfig(
            audit_frequency='manual',
            auto_generate_reports=False
        )
    ),
    
    'testing': SecuritySystemConfig(
        environment='testing',
        debug_mode=True,
        log_level='INFO',
        pii_config=PIISecurityConfig(enabled=False),
        vulnerability_config=VulnerabilityScanConfig(
            enabled=True,
            scan_depth=SecurityLevel.BASIC
        ),
        file_security_config=FileSecurityConfig(scanning_enabled=False),
        threat_intel_config=ThreatIntelligenceConfig(enabled=False),
        compliance_config=ComplianceConfig(
            gdpr_enabled=False,
            ccpa_enabled=False,
            sox_enabled=False
        )
    ),
    
    'staging': SecuritySystemConfig(
        environment='staging',
        debug_mode=False,
        log_level='INFO',
        pii_config=PIISecurityConfig(enabled=True, auto_redact=True),
        vulnerability_config=VulnerabilityScanConfig(
            enabled=True,
            scan_depth=SecurityLevel.STANDARD,
            auto_scan_schedule='daily'
        ),
        headers_config=SecurityHeadersConfig(strict_mode=True),
        threat_intel_config=ThreatIntelligenceConfig(enabled=True),
        compliance_config=ComplianceConfig(
            audit_frequency='weekly',
            auto_generate_reports=True
        ),
        alert_on_critical=True
    ),
    
    'production': SecuritySystemConfig(
        environment='production',
        debug_mode=False,
        log_level='WARNING',
        pii_config=PIISecurityConfig(
            enabled=True, 
            auto_redact=True, 
            compliance_framework=ComplianceFramework.GDPR,
            log_pii_access=True
        ),
        vulnerability_config=VulnerabilityScanConfig(
            enabled=True,
            scan_depth=SecurityLevel.HIGH,
            auto_scan_schedule='daily',
            auto_remediate=False  # Cambiar a True con precaución
        ),
        headers_config=SecurityHeadersConfig(
            strict_mode=True,
            hsts_enabled=True,
            csp_enabled=True,
            csp_level=SecurityLevel.HIGH
        ),
        threat_intel_config=ThreatIntelligenceConfig(
            enabled=True,
            auto_block_ips=True,
            block_threshold=5
        ),
        compliance_config=ComplianceConfig(
            gdpr_enabled=True,
            ccpa_enabled=True,
            sox_enabled=True,
            audit_frequency='weekly',
            auto_generate_reports=True,
            breach_notification=True
        ),
        encryption_enabled=True,
        backup_enabled=True,
        alert_on_critical=True,
        performance_monitoring=True
    )
}


def get_security_config(environment: Optional[str] = None) -> SecuritySystemConfig:
    """Obtiene configuración de seguridad para entorno específico"""
    env = environment or os.getenv('MCP_ENVIRONMENT', 'development')
    return PREDEFINED_CONFIGS.get(env, PREDEFINED_CONFIGS['development'])


def create_security_config(**kwargs) -> SecuritySystemConfig:
    """Crea configuración personalizada"""
    base_config = get_security_config()
    
    # Actualizar con parámetros personalizados
    for key, value in kwargs.items():
        if hasattr(base_config, key):
            setattr(base_config, key, value)
    
    return base_config