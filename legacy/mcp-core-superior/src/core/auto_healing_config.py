"""
Configuración Avanzada para Auto-Healing
Gestiona configuraciones dinámicas del sistema de auto-healing
"""
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

from .config import settings, Environment
from .auto_healing_engine import (
    HealthStatus, CircuitBreakerConfig, AutoScalingConfig, RecoveryStrategy
)


class ConfigurationSource(Enum):
    """Fuentes de configuración"""
    DEFAULT = "default"
    FILE = "file"
    ENVIRONMENT = "environment"
    RUNTIME = "runtime"
    DATABASE = "database"


@dataclass
class DynamicThresholds:
    """Umbrales dinámicos para detección de anomalías"""
    # Umbrales de recursos
    cpu_warning: float = 70.0
    cpu_critical: float = 85.0
    memory_warning: float = 75.0
    memory_critical: float = 90.0
    
    # Umbrales de aplicación
    response_time_warning: float = 1.0  # seconds
    response_time_critical: float = 2.5  # seconds
    error_rate_warning: float = 0.05  # 5%
    error_rate_critical: float = 0.10  # 10%
    
    # Umbrales de agentes
    agent_health_score_warning: float = 0.7
    agent_health_score_critical: float = 0.5
    agent_failure_prediction_warning: float = 0.6
    agent_failure_prediction_critical: float = 0.8
    
    # Umbrales de escalado
    scaling_trigger_cpu: float = 80.0
    scaling_trigger_memory: float = 85.0
    scaling_trigger_response_time: float = 2.0
    
    # Umbrales de recuperación automática
    auto_recovery_failure_threshold: int = 3
    auto_recovery_cooldown: int = 300  # seconds
    max_recovery_attempts: int = 5
    
    def to_dict(self) -> Dict[str, float]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'DynamicThresholds':
        return cls(**data)


@dataclass
class AgentSpecificConfig:
    """Configuración específica por agente"""
    agent_name: str
    
    # Circuit breaker específico
    circuit_breaker_enabled: bool = True
    circuit_breaker_failure_threshold: int = 3
    circuit_breaker_recovery_timeout: int = 30
    
    # Configuración de escalado
    scaling_enabled: bool = True
    min_instances: int = 1
    max_instances: int = 5
    target_utilization: float = 70.0
    
    # Configuración de recuperación
    auto_recovery_enabled: bool = True
    recovery_strategies: List[RecoveryStrategy] = field(default_factory=lambda: [
        RecoveryStrategy.RESTART_AGENT,
        RecoveryStrategy.GRACEFUL_DEGRADATION,
        RecoveryStrategy.CIRCUIT_BREAKER
    ])
    
    # Configuración de monitoreo
    health_check_interval: int = 30  # seconds
    metrics_collection_enabled: bool = True
    anomaly_detection_enabled: bool = True
    
    # Configuración específica del agente
    custom_thresholds: DynamicThresholds = field(default_factory=DynamicThresholds)
    fallback_behavior: str = "degraded"
    priority_level: int = 1  # 1=highest, 5=lowest
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["recovery_strategies"] = [strategy.value for strategy in self.recovery_strategies]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentSpecificConfig':
        data["recovery_strategies"] = [RecoveryStrategy(s) for s in data.get("recovery_strategies", [])]
        if "custom_thresholds" in data:
            data["custom_thresholds"] = DynamicThresholds.from_dict(data["custom_thresholds"])
        return cls(**data)


@dataclass
class AutoHealingConfiguration:
    """Configuración principal del sistema de auto-healing"""
    
    # Configuración general
    enabled: bool = True
    debug_mode: bool = False
    environment: Environment = Environment.DEVELOPMENT
    
    # Configuración de monitoreo
    monitoring_interval: int = 10  # seconds
    metrics_retention_hours: int = 24
    alert_cooldown: int = 300  # seconds
    
    # Configuración global de thresholds
    global_thresholds: DynamicThresholds = field(default_factory=DynamicThresholds)
    
    # Configuración de escalado automático
    auto_scaling_config: AutoScalingConfig = field(default_factory=AutoScalingConfig)
    
    # Configuración específica por agente
    agent_configs: Dict[str, AgentSpecificConfig] = field(default_factory=dict)
    
    # Configuración de circuit breakers globales
    global_circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    
    # Configuración de logging
    log_level: str = "INFO"
    log_metrics: bool = True
    log_recovery_actions: bool = True
    log_scaling_events: bool = True
    
    # Configuración de integración
    enable_webhook_notifications: bool = False
    webhook_url: Optional[str] = None
    enable_email_alerts: bool = False
    email_recipients: List[str] = field(default_factory=list)
    
    # Configuración de machine learning
    ml_enabled: bool = True
    ml_model_update_interval: int = 3600  # seconds
    ml_confidence_threshold: float = 0.8
    ml_training_data_retention_days: int = 7
    
    # Configuración de graceful degradation
    graceful_degradation_enabled: bool = True
    degradation_strategies: List[str] = field(default_factory=lambda: [
        "reduce_concurrency",
        "increase_timeouts", 
        "disable_non_essential_features",
        "fallback_to_cache"
    ])
    
    # Configuración de backup y restore
    enable_automatic_backup: bool = True
    backup_interval: int = 3600  # seconds
    backup_retention_days: int = 30
    restore_on_critical_failure: bool = True
    
    # Configuración de notificaciones
    notification_channels: Dict[str, bool] = field(default_factory=lambda: {
        "console": True,
        "file": False,
        "webhook": False,
        "email": False,
        "slack": False
    })
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["environment"] = self.environment.value
        data["global_thresholds"] = self.global_thresholds.to_dict()
        data["auto_scaling_config"] = asdict(self.auto_scaling_config)
        data["global_circuit_breaker"] = asdict(self.global_circuit_breaker)
        
        # Convertir agent configs
        data["agent_configs"] = {
            name: config.to_dict() 
            for name, config in self.agent_configs.items()
        }
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AutoHealingConfiguration':
        # Convertir enum values
        data["environment"] = Environment(data.get("environment", Environment.DEVELOPMENT.value))
        
        # Convertir objetos anidados
        if "global_thresholds" in data:
            data["global_thresholds"] = DynamicThresholds.from_dict(data["global_thresholds"])
        
        if "auto_scaling_config" in data:
            data["auto_scaling_config"] = AutoScalingConfig(**data["auto_scaling_config"])
        
        if "global_circuit_breaker" in data:
            data["global_circuit_breaker"] = CircuitBreakerConfig(**data["global_circuit_breaker"])
        
        # Convertir agent configs
        if "agent_configs" in data:
            data["agent_configs"] = {
                name: AgentSpecificConfig.from_dict(config_data)
                for name, config_data in data["agent_configs"].items()
            }
        
        return cls(**data)


class ConfigurationManager:
    """Gestor de configuración para auto-healing"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.logger = logging.getLogger("mcp.config.manager")
        self.config_file = config_file or "auto_healing_config.json"
        self.config: Optional[AutoHealingConfiguration] = None
        self.config_source: ConfigurationSource = ConfigurationSource.DEFAULT
        self.last_updated: Optional[datetime] = None
        self.config_watchers: List[callable] = []
        
        # Cache de configuraciones por agente
        self._agent_config_cache: Dict[str, AgentSpecificConfig] = {}
    
    async def initialize(self) -> AutoHealingConfiguration:
        """Inicializar configuración desde múltiples fuentes"""
        self.logger.info("Initializing Auto-Healing configuration...")
        
        # Intentar cargar desde archivo
        config = await self._load_from_file()
        if config:
            self.config = config
            self.config_source = ConfigurationSource.FILE
            self.last_updated = datetime.now()
            self.logger.info(f"Configuration loaded from file: {self.config_file}")
            return config
        
        # Intentar cargar desde variables de entorno
        config = await self._load_from_environment()
        if config:
            self.config = config
            self.config_source = ConfigurationSource.ENVIRONMENT
            self.last_updated = datetime.now()
            self.logger.info("Configuration loaded from environment variables")
            return config
        
        # Usar configuración por defecto
        self.config = self._create_default_config()
        self.config_source = ConfigurationSource.DEFAULT
        self.logger.info("Using default configuration")
        
        return self.config
    
    async def _load_from_file(self) -> Optional[AutoHealingConfiguration]:
        """Cargar configuración desde archivo"""
        try:
            if not Path(self.config_file).exists():
                return None
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return AutoHealingConfiguration.from_dict(data)
            
        except Exception as e:
            self.logger.error(f"Error loading configuration from file: {e}")
            return None
    
    async def _load_from_environment(self) -> Optional[AutoHealingConfiguration]:
        """Cargar configuración desde variables de entorno"""
        try:
            # Verificar si hay variables de entorno relevantes
            env_configs = {
                "AUTO_HEALING_ENABLED": "enabled",
                "AUTO_HEALING_DEBUG": "debug_mode",
                "AUTO_HEALING_MONITORING_INTERVAL": "monitoring_interval",
                "AUTO_HEALING_LOG_LEVEL": "log_level"
            }
            
            if not any(os.getenv(key) for key in env_configs.keys()):
                return None
            
            # Crear configuración base
            config = self._create_default_config()
            
            # Aplicar variables de entorno
            for env_key, config_key in env_configs.items():
                env_value = os.getenv(env_key)
                if env_value:
                    if config_key in ["enabled", "debug_mode"]:
                        setattr(config, config_key, env_value.lower() in ["true", "1", "yes"])
                    elif config_key in ["monitoring_interval"]:
                        setattr(config, config_key, int(env_value))
                    else:
                        setattr(config, config_key, env_value)
            
            return config
            
        except Exception as e:
            self.logger.error(f"Error loading configuration from environment: {e}")
            return None
    
    def _create_default_config(self) -> AutoHealingConfiguration:
        """Crear configuración por defecto"""
        config = AutoHealingConfiguration()
        
        # Configurar agentes específicos
        agent_configs = [
            "reasoner", "planner", "executor", "verifier", 
            "memory_manager", "orchestrator", "streaming"
        ]
        
        for agent_name in agent_configs:
            agent_config = AgentSpecificConfig(agent_name=agent_name)
            
            # Configuración específica por agente
            if agent_name == "executor":
                agent_config.circuit_breaker_failure_threshold = 5
                agent_config.min_instances = 2
                agent_config.max_instances = 8
                agent_config.priority_level = 1
            
            elif agent_name == "planner":
                agent_config.circuit_breaker_failure_threshold = 3
                agent_config.min_instances = 1
                agent_config.max_instances = 4
                agent_config.priority_level = 2
            
            elif agent_name == "reasoner":
                agent_config.circuit_breaker_failure_threshold = 4
                agent_config.min_instances = 1
                agent_config.max_instances = 6
                agent_config.priority_level = 2
            
            elif agent_name == "orchestrator":
                agent_config.circuit_breaker_failure_threshold = 2
                agent_config.min_instances = 2
                agent_config.max_instances = 4
                agent_config.priority_level = 1
            
            config.agent_configs[agent_name] = agent_config
        
        return config
    
    def get_config(self) -> AutoHealingConfiguration:
        """Obtener configuración actual"""
        if self.config is None:
            raise ValueError("Configuration not initialized")
        return self.config
    
    def get_agent_config(self, agent_name: str) -> AgentSpecificConfig:
        """Obtener configuración específica de un agente"""
        if agent_name in self._agent_config_cache:
            return self._agent_config_cache[agent_name]
        
        config = self.get_config()
        
        # Obtener configuración específica o crear una por defecto
        agent_config = config.agent_configs.get(agent_name)
        if agent_config is None:
            agent_config = AgentSpecificConfig(agent_name=agent_name)
            config.agent_configs[agent_name] = agent_config
        
        self._agent_config_cache[agent_name] = agent_config
        return agent_config
    
    async def update_config(self, 
                          updates: Dict[str, Any], 
                          source: ConfigurationSource = ConfigurationSource.RUNTIME) -> bool:
        """Actualizar configuración"""
        try:
            if self.config is None:
                raise ValueError("Configuration not initialized")
            
            # Crear copia profunda de la configuración actual
            import copy
            new_config = copy.deepcopy(self.config)
            
            # Aplicar actualizaciones
            self._apply_updates(new_config, updates)
            
            # Validar configuración actualizada
            if not self._validate_config(new_config):
                raise ValueError("Updated configuration validation failed")
            
            # Aplicar cambios
            old_config = self.config
            self.config = new_config
            self.config_source = source
            self.last_updated = datetime.now()
            
            # Limpiar cache
            self._agent_config_cache.clear()
            
            # Notificar watchers
            await self._notify_config_watchers(old_config, new_config)
            
            self.logger.info(f"Configuration updated from {source.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating configuration: {e}")
            return False
    
    def _apply_updates(self, config: AutoHealingConfiguration, updates: Dict[str, Any]):
        """Aplicar actualizaciones a la configuración"""
        for key, value in updates.items():
            if hasattr(config, key):
                current_value = getattr(config, key)
                
                if isinstance(current_value, DynamicThresholds) and isinstance(value, dict):
                    # Actualizar thresholds dinámicos
                    for thresh_key, thresh_value in value.items():
                        if hasattr(current_value, thresh_key):
                            setattr(current_value, thresh_key, thresh_value)
                
                elif isinstance(current_value, AgentSpecificConfig) and isinstance(value, dict):
                    # Actualizar configuración de agente
                    for agent_key, agent_value in value.items():
                        if hasattr(current_value, agent_key):
                            setattr(current_value, agent_key, agent_value)
                
                else:
                    # Actualización directa
                    setattr(config, key, value)
    
    def _validate_config(self, config: AutoHealingConfiguration) -> bool:
        """Validar configuración"""
        try:
            # Validaciones básicas
            if config.monitoring_interval < 1 or config.monitoring_interval > 300:
                self.logger.error("Invalid monitoring_interval")
                return False
            
            if config.metrics_retention_hours < 1 or config.metrics_retention_hours > 168:
                self.logger.error("Invalid metrics_retention_hours")
                return False
            
            # Validar configuración de agentes
            for agent_name, agent_config in config.agent_configs.items():
                if agent_config.min_instances < 1:
                    self.logger.error(f"Invalid min_instances for agent {agent_name}")
                    return False
                
                if agent_config.max_instances < agent_config.min_instances:
                    self.logger.error(f"max_instances < min_instances for agent {agent_name}")
                    return False
                
                if not agent_config.recovery_strategies:
                    self.logger.error(f"No recovery strategies configured for agent {agent_name}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation error: {e}")
            return False
    
    async def save_config(self, file_path: Optional[str] = None) -> bool:
        """Guardar configuración a archivo"""
        try:
            if self.config is None:
                raise ValueError("Configuration not initialized")
            
            target_file = file_path or self.config_file
            
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2, default=str)
            
            self.logger.info(f"Configuration saved to {target_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False
    
    def register_config_watcher(self, watcher: callable):
        """Registrar watcher para cambios de configuración"""
        self.config_watchers.append(watcher)
    
    async def _notify_config_watchers(self, old_config: AutoHealingConfiguration, new_config: AutoHealingConfiguration):
        """Notificar a watchers sobre cambios de configuración"""
        for watcher in self.config_watchers:
            try:
                await watcher(old_config, new_config)
            except Exception as e:
                self.logger.error(f"Error notifying config watcher: {e}")
    
    def get_thresholds_for_agent(self, agent_name: str) -> DynamicThresholds:
        """Obtener thresholds específicos para un agente"""
        agent_config = self.get_agent_config(agent_name)
        
        # Combinar thresholds globales con específicos del agente
        global_thresholds = self.config.global_thresholds
        agent_thresholds = agent_config.custom_thresholds
        
        # Crear merged thresholds
        merged_thresholds = DynamicThresholds()
        
        # Copiar valores globales
        for field_name in asdict(global_thresholds):
            setattr(merged_thresholds, field_name, getattr(global_thresholds, field_name))
        
        # Override con valores específicos del agente
        for field_name in asdict(agent_thresholds):
            value = getattr(agent_thresholds, field_name)
            if value != getattr(DynamicThresholds(), field_name):  # Si no es el valor por defecto
                setattr(merged_thresholds, field_name, value)
        
        return merged_thresholds
    
    def reload_config(self) -> bool:
        """Recargar configuración desde fuente original"""
        try:
            self.logger.info("Reloading configuration...")
            
            # Guardar cache actual
            old_config = self.config
            old_source = self.config_source
            
            # Reinicializar
            new_config = asyncio.run(self.initialize())
            
            if new_config:
                self.logger.info(f"Configuration reloaded from {self.config_source.value}")
                return True
            else:
                # Restaurar configuración anterior
                self.config = old_config
                self.config_source = old_source
                self.logger.warning("Failed to reload configuration, keeping previous")
                return False
                
        except Exception as e:
            self.logger.error(f"Error reloading configuration: {e}")
            return False


# ==================== INSTANCIA GLOBAL ====================

# Instancia global del gestor de configuración
_config_manager: Optional[ConfigurationManager] = None

async def get_config_manager(config_file: Optional[str] = None) -> ConfigurationManager:
    """Obtener instancia global del gestor de configuración"""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigurationManager(config_file)
        await _config_manager.initialize()
    
    return _config_manager


def create_default_config() -> AutoHealingConfiguration:
    """Crear configuración por defecto"""
    manager = ConfigurationManager()
    return manager._create_default_config()


# ==================== UTILITY FUNCTIONS ====================

def merge_configurations(base: AutoHealingConfiguration, 
                        override: AutoHealingConfiguration) -> AutoHealingConfiguration:
    """Combinar dos configuraciones (base con override)"""
    import copy
    merged = copy.deepcopy(base)
    
    # Aplicar overrides de nivel superior
    for key, value in asdict(override).items():
        if hasattr(merged, key) and key != "agent_configs":
            if isinstance(getattr(merged, key), DynamicThresholds) and isinstance(value, dict):
                # Merge thresholds
                current_thresholds = getattr(merged, key)
                override_thresholds = DynamicThresholds.from_dict(value)
                
                for field_name in asdict(current_thresholds):
                    override_value = getattr(override_thresholds, field_name)
                    if override_value != getattr(DynamicThresholds(), field_name):
                        setattr(current_thresholds, field_name, override_value)
            else:
                setattr(merged, key, value)
    
    # Merge agent configs
    for agent_name, agent_config in override.agent_configs.items():
        if agent_name in merged.agent_configs:
            # Merge existing agent config
            base_agent_config = merged.agent_configs[agent_name]
            for field_name, value in asdict(agent_config).items():
                if hasattr(base_agent_config, field_name):
                    setattr(base_agent_config, field_name, value)
        else:
            # Add new agent config
            merged.agent_configs[agent_name] = agent_config
    
    return merged


async def export_config_to_file(config: AutoHealingConfiguration, 
                               file_path: str, 
                               format_type: str = "json") -> bool:
    """Exportar configuración a archivo"""
    try:
        if format_type == "json":
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
        
        return True
        
    except Exception as e:
        logging.error(f"Error exporting configuration: {e}")
        return False


async def import_config_from_file(file_path: str, 
                                 format_type: str = "json") -> Optional[AutoHealingConfiguration]:
    """Importar configuración desde archivo"""
    try:
        if format_type == "json":
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return AutoHealingConfiguration.from_dict(data)
        else:
            raise ValueError(f"Unsupported import format: {format_type}")
        
    except Exception as e:
        logging.error(f"Error importing configuration: {e}")
        return None


if __name__ == "__main__":
    # Ejemplo de uso
    async def main():
        # Crear gestor de configuración
        manager = await get_config_manager("test_auto_healing_config.json")
        
        # Mostrar configuración actual
        config = manager.get_config()
        print("Current configuration:")
        print(json.dumps(config.to_dict(), indent=2, default=str))
        
        # Actualizar configuración
        updates = {
            "enabled": True,
            "debug_mode": True,
            "global_thresholds": {
                "cpu_warning": 60.0,
                "memory_warning": 70.0
            }
        }
        
        success = await manager.update_config(updates)
        print(f"Configuration update successful: {success}")
        
        # Guardar configuración
        await manager.save_config()
        
        # Obtener configuración de agente específico
        executor_config = manager.get_agent_config("executor")
        print(f"Executor config: {executor_config.to_dict()}")
        
        # Obtener thresholds para agente
        thresholds = manager.get_thresholds_for_agent("reasoner")
        print(f"Reasoner thresholds: {thresholds.to_dict()}")
    
    asyncio.run(main())