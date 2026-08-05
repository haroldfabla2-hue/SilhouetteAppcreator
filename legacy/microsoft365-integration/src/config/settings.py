"""
Microsoft 365 Integration - Core Configuration
Configuración centralizada para todos los servicios
"""

import os
from typing import Dict, List, Optional
from pydantic import BaseSettings, Field

class Microsoft365Settings(BaseSettings):
    """Configuración principal de Microsoft 365"""
    
    # Azure AD Configuration
    tenant_id: str = Field(..., env="AZURE_TENANT_ID")
    client_id: str = Field(..., env="AZURE_CLIENT_ID")
    client_secret: str = Field(..., env="AZURE_CLIENT_SECRET")
    
    # Microsoft Graph API
    graph_api_base_url: str = "https://graph.microsoft.com/v1.0"
    graph_api_scope: str = "https://graph.microsoft.com/.default"
    
    # Service Endpoints
    sharepoint_base_url: str = "https://{tenant}.sharepoint.com"
    onedrive_base_url: str = "https://{tenant}-my.sharepoint.com"
    teams_base_url: str = "https://teams.microsoft.com"
    
    # Authentication
    cache_location: str = "./token_cache.json"
    redirect_uri: str = "http://localhost:8080/auth/callback"
    
    # Rate Limiting
    requests_per_minute: int = 100
    requests_per_day: int = 10000
    
    # Retry Configuration
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Timeout Configuration
    request_timeout: int = 30
    long_running_timeout: int = 120
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

class ServiceConfiguration(BaseSettings):
    """Configuración específica por servicio"""
    
    # Word Online
    word_api_version: str = "v1.0"
    word_max_document_size: int = 10 * 1024 * 1024  # 10MB
    
    # Excel Online
    excel_api_version: str = "v1.0"
    excel_max_workbook_size: int = 50 * 1024 * 1024  # 50MB
    excel_max_worksheet_rows: int = 1048576  # 1M filas
    
    # PowerPoint
    powerpoint_api_version: str = "v1.0"
    powerpoint_max_presentation_size: int = 100 * 1024 * 1024  # 100MB
    
    # Outlook
    outlook_api_version: str = "v1.0"
    outlook_max_message_size: int = 25 * 1024 * 1024  # 25MB
    outlook_email_batch_size: int = 50
    
    # OneDrive
    onedrive_api_version: str = "v1.0"
    onedrive_max_file_size: int = 250 * 1024 * 1024  # 250MB
    onedrive_chunk_size: int = 32768  # 32KB chunks
    
    # Teams
    teams_api_version: str = "v1.0"
    teams_max_team_members: int = 10000
    teams_max_channel_members: int = 5000

class DatabaseSettings(BaseSettings):
    """Configuración de base de datos para sincronización"""
    
    database_url: str = Field(default="sqlite:///./microsoft365_data.db")
    database_echo: bool = False
    database_pool_size: int = 20
    database_max_overflow: int = 30
    
    # Redis Cache
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_key_prefix: str = "ms365:"
    redis_ttl: int = 3600  # 1 hora
    
    # Cache Configuration
    cache_enabled: bool = True
    cache_ttl: int = 300  # 5 minutos
    
    class Config:
        env_prefix = "MS365_DB_"

class SecuritySettings(BaseSettings):
    """Configuración de seguridad"""
    
    encryption_key: str = Field(..., env="MS365_ENCRYPTION_KEY")
    jwt_secret: str = Field(..., env="MS365_JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # 1 hora
    
    # Certificate Validation
    verify_ssl: bool = True
    ssl_cert_path: Optional[str] = None
    
    # IP Whitelist
    allowed_ips: List[str] = []
    
    class Config:
        env_prefix = "MS365_SEC_"

# Global Configuration Instance
settings = Microsoft365Settings()
service_config = ServiceConfiguration()
database_config = DatabaseSettings()
security_config = SecuritySettings()

# Service Endpoints
SERVICE_ENDPOINTS = {
    "graph": "https://graph.microsoft.com/v1.0",
    "sharepoint": "https://{tenant}.sharepoint.com",
    "teams": "https://teams.microsoft.com",
    "outlook": "https://outlook.office365.com",
    "onedrive": "https://{tenant}-my.sharepoint.com"
}

# API Permissions
GRAPH_PERMISSIONS = {
    "Files.ReadWrite.All": ["OneDrive", "SharePoint", "Word", "Excel", "PowerPoint"],
    "Mail.ReadWrite": ["Outlook"],
    "Calendars.ReadWrite": ["Outlook"],
    "Sites.ReadWrite.All": ["SharePoint", "Teams"],
    "Team.ReadBasic.All": ["Teams"],
    "User.Read.All": ["All Services"],
    "Directory.Read.All": ["All Services"]
}

# Rate Limits por Servicio
RATE_LIMITS = {
    "graph": {"requests_per_minute": 100, "requests_per_day": 10000},
    "word": {"requests_per_minute": 50, "requests_per_day": 5000},
    "excel": {"requests_per_minute": 30, "requests_per_day": 3000},
    "powerpoint": {"requests_per_minute": 25, "requests_per_day": 2500},
    "outlook": {"requests_per_minute": 75, "requests_per_day": 7500},
    "onedrive": {"requests_per_minute": 60, "requests_per_day": 6000},
    "teams": {"requests_per_minute": 40, "requests_per_day": 4000}
}