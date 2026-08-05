"""
CONFIGURACIÓN PRINCIPAL - SISTEMA DE ORQUESTACIÓN MULTI-AGENTE OPTIMIZADO
Archivo de configuración y acceso rápido para el sistema completo optimizado
para 20+ agentes especializados con capacidades empresariales
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import json

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp.system.config")

# === CONFIGURACIÓN GLOBAL DEL SISTEMA ===

class OptimizedMultiAgentSystemConfig:
    """Configuración principal del sistema optimizado"""
    
    def __init__(self):
        self.system_name = "Optimized Multi-Agent System v2.0"
        self.version = "2.0-enterprise"
        self.created_at = datetime.now()
        
        # Configuración de agentes especializados
        self.agent_configs = self._load_agent_configs()
        
        # Configuración de optimización
        self.optimization_settings = {
            "enable_adaptive_routing": True,
            "enable_predictive_scaling": True,
            "enable_fault_tolerance": True,
            "enable_auto_optimization": True,
            "max_concurrent_workflows": 50,
            "max_concurrent_tools": 100,
            "auto_optimization_interval": 300,  # 5 minutos
            "health_check_interval": 30,  # 30 segundos
            "circuit_breaker_settings": {
                "failure_threshold": 5,
                "recovery_timeout": 60.0,
                "success_threshold": 3
            }
        }
        
        # Configuración de routing
        self.routing_settings = {
            "default_strategy": "learning_based",
            "fallback_strategies": ["capacity_based", "response_time"],
            "strategies": {
                "round_robin": {"enabled": True, "weight": 1},
                "weighted_round_robin": {"enabled": True, "weight": 2},
                "least_connections": {"enabled": True, "weight": 3},
                "response_time": {"enabled": True, "weight": 2},
                "learning_based": {"enabled": True, "weight": 5},  # Prioritario
                "capacity_based": {"enabled": True, "weight": 4},
                "cost_optimized": {"enabled": True, "weight": 2},
                "quality_based": {"enabled": True, "weight": 3}
            }
        }
        
        # Configuración de load balancing
        self.load_balancing_settings = {
            "default_strategy": "adaptive",
            "strategies": {
                "adaptive": {"enabled": True, "recommended": True},
                "weighted": {"enabled": True, "weight": 3},
                "least_connections": {"enabled": True, "weight": 4},
                "resource_based": {"enabled": True, "weight": 3},
                "predictive": {"enabled": True, "weight": 2}
            },
            "fault_tolerance": {
                "max_retries": 3,
                "retry_delay": 1.0,
                "exponential_backoff": True,
                "timeout_multiplier": 1.5
            }
        }
        
        # Configuración de benchmarks
        self.benchmark_settings = {
            "include_stress_tests": True,
            "stress_test_levels": ["light", "medium", "heavy"],
            "endurance_test_duration": 300,  # 5 minutos
            "monitoring_interval": 0.5,  # 500ms
            "output_formats": ["json", "txt", "html"]
        }
    
    def _load_agent_configs(self) -> Dict[str, Any]:
        """Cargar configuración de agentes especializados"""
        try:
            # Importar configuración de agentes
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
            
            from agents.specialized_agents import get_specialized_agents_config
            return get_specialized_agents_config()
        except Exception as e:
            logger.warning(f"Error cargando configuración de agentes: {e}")
            return self._get_default_agent_configs()
    
    def _get_default_agent_configs(self) -> Dict[str, Any]:
        """Configuración por defecto de agentes"""
        return {
            "data_processor_agent": {
                "category": "data_processing",
                "skills": ["data_cleaning", "transformation"],
                "max_concurrent_tasks": 8,
                "avg_response_time": 1.5,
                "success_rate": 0.92,
                "quality_score": 0.88
            },
            "python_executor_agent": {
                "category": "code_execution", 
                "skills": ["code_execution", "debugging"],
                "max_concurrent_tasks": 6,
                "avg_response_time": 2.0,
                "success_rate": 0.95,
                "quality_score": 0.90
            },
            "web_scraping_agent": {
                "category": "web_services",
                "skills": ["html_parsing", "data_extraction"],
                "max_concurrent_tasks": 4,
                "avg_response_time": 3.0,
                "success_rate": 0.88,
                "quality_score": 0.85
            }
            # ... más agentes se cargarían dinámicamente
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Obtener información completa del sistema"""
        return {
            "system": {
                "name": self.system_name,
                "version": self.version,
                "created_at": self.created_at.isoformat(),
                "status": "optimized"
            },
            "agents": {
                "total_count": len(self.agent_configs),
                "categories": self._get_agent_categories(),
                "performance": self._get_agent_performance_summary()
            },
            "optimization": self.optimization_settings,
            "routing": self.routing_settings,
            "load_balancing": self.load_balancing_settings,
            "benchmarks": self.benchmark_settings
        }
    
    def _get_agent_categories(self) -> Dict[str, int]:
        """Obtener conteo de agentes por categoría"""
        categories = {}
        for config in self.agent_configs.values():
            category = config.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
        return categories
    
    def _get_agent_performance_summary(self) -> Dict[str, Any]:
        """Obtener resumen de performance de agentes"""
        performance = {
            "avg_success_rate": 0,
            "avg_response_time": 0,
            "avg_quality_score": 0,
            "total_capacity": 0
        }
        
        if not self.agent_configs:
            return performance
        
        total_success_rate = sum(config.get("success_rate", 0) for config in self.agent_configs.values())
        total_response_time = sum(config.get("avg_response_time", 0) for config in self.agent_configs.values())
        total_quality = sum(config.get("quality_score", 0) for config in self.agent_configs.values())
        total_capacity = sum(config.get("max_concurrent_tasks", 0) for config in self.agent_configs.values())
        
        agent_count = len(self.agent_configs)
        performance["avg_success_rate"] = total_success_rate / agent_count
        performance["avg_response_time"] = total_response_time / agent_count
        performance["avg_quality_score"] = total_quality / agent_count
        performance["total_capacity"] = total_capacity
        
        return performance
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validar configuración del sistema"""
        issues = []
        warnings = []
        
        # Validar agentes
        if len(self.agent_configs) < 20:
            warnings.append(f"Solo {len(self.agent_configs)} agentes configurados (mínimo recomendado: 20)")
        
        # Validar estrategias de routing
        enabled_strategies = [
            name for name, config in self.routing_settings["strategies"].items()
            if config.get("enabled", False)
        ]
        if len(enabled_strategies) < 5:
            warnings.append(f"Solo {len(enabled_strategies)} estrategias de routing habilitadas")
        
        # Validar concurrencia
        if self.optimization_settings["max_concurrent_workflows"] < 10:
            warnings.append("Capacidad de workflows concurrentes muy baja")
        
        # Validar fault tolerance
        if not self.optimization_settings["enable_fault_tolerance"]:
            issues.append("Fault tolerance deshabilitado")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "score": max(0, 100 - len(issues) * 20 - len(warnings) * 10)
        }


class MultiAgentSystemManager:
    """Gestor principal del sistema multi-agente optimizado"""
    
    def __init__(self, config: Optional[OptimizedMultiAgentSystemConfig] = None):
        self.config = config or OptimizedMultiAgentSystemConfig()
        self.system = None
        self.is_initialized = False
        
    async def initialize(self) -> Dict[str, Any]:
        """Inicializar sistema completo"""
        try:
            logger.info("🚀 Inicializando Sistema Multi-Agente Optimizado...")
            
            # Validar configuración
            validation = self.config.validate_configuration()
            if not validation["valid"]:
                raise Exception(f"Configuración inválida: {validation['issues']}")
            
            if validation["warnings"]:
                logger.warning(f"Advertencias de configuración: {validation['warnings']}")
            
            # Importar sistema principal
            from demo_optimized_multiagent_system import OptimizedMultiAgentSystem
            self.system = OptimizedMultiAgentSystem()
            
            # Inicializar sistema
            status = await self.system.initialize()
            
            self.is_initialized = True
            
            logger.info("✅ Sistema inicializado exitosamente!")
            logger.info(f"   Configuración validada (score: {validation['score']}/100)")
            logger.info(f"   Agentes especializados: {len(self.config.agent_configs)}")
            
            return {
                "initialization": "success",
                "validation_score": validation["score"],
                "system_status": status,
                "config_info": self.config.get_system_info()
            }
            
        except Exception as e:
            logger.error(f"❌ Error inicializando sistema: {e}")
            raise
    
    async def run_demo(self) -> Dict[str, Any]:
        """Ejecutar demostración completa del sistema"""
        if not self.is_initialized:
            await self.initialize()
        
        logger.info("🎯 Ejecutando demostración completa...")
        
        try:
            results = await self.system.run_comprehensive_demo()
            return {
                "demo_status": "completed",
                "results": results,
                "performance_summary": self._extract_performance_summary(results)
            }
        except Exception as e:
            logger.error(f"❌ Error en demostración: {e}")
            raise
    
    async def run_benchmarks(self, include_stress: bool = True) -> Dict[str, Any]:
        """Ejecutar benchmarks del sistema"""
        if not self.is_initialized:
            await self.initialize()
        
        logger.info("📊 Ejecutando benchmarks del sistema...")
        
        try:
            from benchmarks.performance_benchmarks import run_complete_benchmark_suite
            
            suite = await run_complete_benchmark_suite(
                suite_name="System_Optimization_Benchmark",
                include_stress_tests=include_stress
            )
            
            return {
                "benchmark_status": "completed",
                "suite_results": suite.to_dict(),
                "performance_score": self._calculate_performance_score(suite)
            }
        except Exception as e:
            logger.error(f"❌ Error ejecutando benchmarks: {e}")
            raise
    
    async def stress_test(self, level: str = "medium") -> Dict[str, Any]:
        """Ejecutar stress test del sistema"""
        if not self.is_initialized:
            await self.initialize()
        
        logger.info(f"🔥 Ejecutando stress test ({level})...")
        
        stress_configs = {
            "light": {"workflows": 20, "tasks_per_workflow": 2},
            "medium": {"workflows": 50, "tasks_per_workflow": 3},
            "heavy": {"workflows": 100, "tasks_per_workflow": 5}
        }
        
        config = stress_configs.get(level, stress_configs["medium"])
        
        try:
            result = await self.system.orchestrator.execute_stress_test(
                concurrent_workflows=config["workflows"],
                tasks_per_workflow=config["tasks_per_workflow"]
            )
            
            return {
                "stress_test_status": "completed",
                "level": level,
                "configuration": config,
                "results": result,
                "system_resilience": self._assess_system_resilience(result)
            }
        except Exception as e:
            logger.error(f"❌ Error en stress test: {e}")
            raise
    
    def _extract_performance_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer resumen de performance de resultados"""
        metrics = results.get("success_metrics", {})
        
        return {
            "overall_success_rate": metrics.get("demo_success_rate", 0),
            "agents_tested": metrics.get("total_agents_tested", 0),
            "workflows_executed": metrics.get("total_workflows_executed", 0),
            "concurrent_capacity": metrics.get("concurrent_capacity", 0),
            "optimization_level": metrics.get("system_optimization_level", "unknown")
        }
    
    def _calculate_performance_score(self, suite) -> Dict[str, Any]:
        """Calcular score de performance del sistema"""
        overall_summary = suite.overall_summary
        
        # Calcular score basado en múltiples factores
        success_rate = overall_summary.get("overall_success_rate", 0)
        throughput = overall_summary.get("average_throughput", 0)
        total_operations = overall_summary.get("total_operations", 0)
        
        # Score ponderado
        performance_score = (
            success_rate * 40 +  # 40% peso para tasa de éxito
            min(throughput / 50, 1) * 30 +  # 30% peso para throughput (normalizado)
            min(total_operations / 1000, 1) * 30  # 30% peso para volumen (normalizado)
        ) * 100
        
        return {
            "overall_score": performance_score,
            "success_rate": success_rate,
            "throughput": throughput,
            "volume": total_operations,
            "grade": self._get_performance_grade(performance_score)
        }
    
    def _get_performance_grade(self, score: float) -> str:
        """Obtener grado de performance basado en score"""
        if score >= 90:
            return "A+ (Excelente)"
        elif score >= 80:
            return "A (Muy Bueno)"
        elif score >= 70:
            return "B (Bueno)"
        elif score >= 60:
            return "C (Aceptable)"
        else:
            return "D (Necesita Mejora)"
    
    def _assess_system_resilience(self, stress_results: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluar resiliencia del sistema"""
        success_rate = stress_results.get("results", {}).get("success_rate", 0)
        total_workflows = stress_results.get("configuration", {}).get("concurrent_workflows", 0)
        
        resilience_score = success_rate * 100
        resilience_level = "Alta" if success_rate > 0.9 else "Media" if success_rate > 0.7 else "Baja"
        
        return {
            "resilience_score": resilience_score,
            "resilience_level": resilience_level,
            "capacity_tested": total_workflows,
            "recommendations": self._get_resilience_recommendations(success_rate)
        }
    
    def _get_resilience_recommendations(self, success_rate: float) -> List[str]:
        """Obtener recomendaciones basadas en resiliencia"""
        recommendations = []
        
        if success_rate < 0.8:
            recommendations.append("Considerar aumentar número de agentes")
            recommendations.append("Revisar configuración de circuit breakers")
        elif success_rate < 0.9:
            recommendations.append("Optimizar estrategias de load balancing")
        else:
            recommendations.append("Sistema operando óptimamente")
        
        return recommendations
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado actual del sistema"""
        if not self.is_initialized:
            return {"status": "not_initialized"}
        
        try:
            status = await self.system.get_system_status()
            config_info = self.config.get_system_info()
            
            return {
                "system_status": status,
                "configuration": config_info,
                "health_check": await self.system.fastmcp_server.health_check() if self.system.fastmcp_server else {}
            }
        except Exception as e:
            logger.error(f"Error obteniendo estado: {e}")
            return {"status": "error", "error": str(e)}
    
    async def shutdown(self):
        """Shutdown del sistema"""
        if self.system:
            await self.system.shutdown()
        
        self.is_initialized = False
        logger.info("🛑 Sistema shutdown completado")


# === FUNCIONES DE ACCESO RÁPIDO ===

async def quick_start() -> MultiAgentSystemManager:
    """Inicio rápido del sistema optimizado"""
    manager = MultiAgentSystemManager()
    await manager.initialize()
    return manager

async def run_full_demo() -> Dict[str, Any]:
    """Ejecutar demostración completa con un solo comando"""
    manager = MultiAgentSystemManager()
    try:
        await manager.initialize()
        demo_results = await manager.run_demo()
        stress_results = await manager.stress_test("medium")
        
        return {
            "status": "completed",
            "demo": demo_results,
            "stress_test": stress_results,
            "system_ready": True
        }
    finally:
        await manager.shutdown()

async def run_benchmarks_only() -> Dict[str, Any]:
    """Ejecutar solo benchmarks del sistema"""
    manager = MultiAgentSystemManager()
    try:
        await manager.initialize()
        return await manager.run_benchmarks(include_stress=True)
    finally:
        await manager.shutdown()

def create_custom_config(**kwargs) -> OptimizedMultiAgentSystemConfig:
    """Crear configuración personalizada"""
    config = OptimizedMultiAgentSystemConfig()
    
    # Aplicar overrides
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        elif key in config.optimization_settings:
            config.optimization_settings[key] = value
        elif key in config.routing_settings:
            config.routing_settings[key] = value
        elif key in config.load_balancing_settings:
            config.load_balancing_settings[key] = value
    
    return config


# === EJEMPLO DE USO ===

async def main():
    """Ejemplo de uso del sistema optimizado"""
    
    print("🚀 SISTEMA DE ORQUESTACIÓN MULTI-AGENTE OPTIMIZADO")
    print("=" * 60)
    
    # Opción 1: Inicio rápido
    print("\n1️⃣ Inicio Rápido:")
    manager = await quick_start()
    status = await manager.get_system_status()
    print(f"   Estado: {status.get('system_status', {}).get('status', 'unknown')}")
    print(f"   Agentes: {len(manager.config.agent_configs)}")
    
    # Opción 2: Demostración completa
    print("\n2️⃣ Demostración Completa:")
    demo_results = await run_full_demo()
    print(f"   Status: {demo_results['status']}")
    print(f"   Sistema listo: {demo_results['system_ready']}")
    
    # Opción 3: Solo benchmarks
    print("\n3️⃣ Solo Benchmarks:")
    benchmark_results = await run_benchmarks_only()
    score = benchmark_results.get("performance_score", {})
    print(f"   Score: {score.get('overall_score', 0):.1f}")
    print(f"   Grado: {score.get('grade', 'N/A')}")
    
    print("\n✅ Sistema optimizado funcionando correctamente!")


if __name__ == "__main__":
    # Ejecutar ejemplo
    asyncio.run(main())