"""
Integración de Agentes Especializados con el Orquestador Principal
===================================================================

Este módulo integra los agentes especializados de búsqueda web avanzada
con el sistema de orquestación existente del MCP Superior.

Características de la integración:
- Registro automático de agentes especializados
- Coordinación con agentes existentes
- Orquestación de tareas complejas
- Gestión de recursos y carga
- Monitoreo y métricas centralizadas

Autor: MCP Superior Integration Team
Versión: 1.0.0
"""

import sys
import os
import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

# Importar agentes especializados
try:
    from .agents.specialized import (
        ResearchAgent, DataMiningAgent, NewsIntelligenceAgent,
        create_agent_ensemble, list_specialized_agents
    )
    from .agents.multiagent_orchestrator_agent import MultiAgentOrchestratorAgent
except ImportError:
    # Fallback para casos especiales
    from agents.specialized import (
        ResearchAgent, DataMiningAgent, NewsIntelligenceAgent,
        create_agent_ensemble, list_specialized_agents
    )
    try:
        from agents.multiagent_orchestrator_agent import MultiAgentOrchestratorAgent
    except ImportError:
        MultiAgentOrchestratorAgent = None


@dataclass
class SpecializedAgentConfig:
    """Configuración para agentes especializados"""
    agent_type: str
    max_instances: int = 3
    timeout_seconds: int = 300
    priority: int = 5  # 1-10, 10 es máxima prioridad
    capabilities: List[str] = None
    dependencies: List[str] = None
    resource_limits: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if self.dependencies is None:
            self.dependencies = []
        if self.resource_limits is None:
            self.resource_limits = {}


class SpecializedAgentsIntegration:
    """
    Integrador de agentes especializados con el orquestador principal
    
    Responsabilidades:
    - Registro automático de agentes especializados
    - Coordinación con agentes existentes
    - Orquestación de workflows complejos
    - Gestión de recursos y balanceado de carga
    - Monitoreo y métricas centralizadas
    """
    
    def __init__(self, orchestrator_agent: Optional[MultiAgentOrchestratorAgent] = None):
        self.logger = logging.getLogger(__name__)
        self.orchestrator = orchestrator_agent
        self.specialized_agents = {}
        self.agent_configs = {}
        self.agent_pools = {}
        self.active_workflows = {}
        self.metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "agent_usage_stats": {}
        }
        
        # Inicializar agentes especializados
        self._initialize_specialized_agents()
        
        self.logger.info("Integración de agentes especializados inicializada")
    
    def _initialize_specialized_agents(self):
        """Inicializa y configura agentes especializados"""
        
        # Configuraciones predeterminadas
        default_configs = {
            "research_agent": SpecializedAgentConfig(
                agent_type="research",
                max_instances=2,
                timeout_seconds=600,  # 10 minutos
                priority=7,
                capabilities=[
                    "investigacion_web_inteligente",
                    "analisis_credibilidad_fuentes",
                    "sintesis_informacion",
                    "deteccion_tendencias",
                    "verificacion_hechos"
                ],
                resource_limits={
                    "max_concurrent_searches": 5,
                    "max_memory_mb": 512,
                    "max_cpu_percent": 80
                }
            ),
            "data_mining_agent": SpecializedAgentConfig(
                agent_type="data_mining",
                max_instances=3,
                timeout_seconds=900,  # 15 minutos
                priority=6,
                capabilities=[
                    "extraccion_datos_multi_fuente",
                    "transformacion_limpieza_datos",
                    "analisis_estadistico",
                    "exportacion_multi_formato",
                    "programacion_extracciones"
                ],
                resource_limits={
                    "max_concurrent_extractions": 3,
                    "max_memory_mb": 1024,
                    "max_cpu_percent": 70
                }
            ),
            "news_intelligence_agent": SpecializedAgentConfig(
                agent_type="news_intelligence",
                max_instances=2,
                timeout_seconds=480,  # 8 minutos
                priority=8,
                capabilities=[
                    "agregacion_noticias_multi_fuente",
                    "deteccion_sesgos_mediaticos",
                    "analisis_sentimiento",
                    "seguimiento_tendencias",
                    "verificacion_credibilidad"
                ],
                resource_limits={
                    "max_concurrent_analyses": 4,
                    "max_memory_mb": 768,
                    "max_cpu_percent": 75
                }
            )
        }
        
        # Registrar configuraciones
        for agent_type, config in default_configs.items():
            self.agent_configs[agent_type] = config
        
        self.logger.info(f"Configuraciones inicializadas para {len(default_configs)} agentes especializados")
    
    def register_specialized_agent(self, agent_type: str, config: SpecializedAgentConfig):
        """
        Registra un agente especializado con configuración personalizada
        
        Args:
            agent_type: Tipo de agente ("research", "data_mining", "news_intelligence")
            config: Configuración del agente
        """
        
        try:
            # Validar configuración
            if agent_type not in ["research", "data_mining", "news_intelligence"]:
                raise ValueError(f"Tipo de agente no válido: {agent_type}")
            
            # Crear pool de agentes
            self.agent_pools[agent_type] = {
                "config": config,
                "agents": [],
                "available_agents": [],
                "busy_agents": [],
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0
            }
            
            # Inicializar instancias de agentes
            self._create_agent_instances(agent_type, config.max_instances)
            
            self.logger.info(f"Agente especializado registrado: {agent_type} ({config.max_instances} instancias)")
            
        except Exception as e:
            self.logger.error(f"Error registrando agente {agent_type}: {e}")
            raise
    
    def _create_agent_instances(self, agent_type: str, count: int):
        """Crea instancias de agentes especializados"""
        
        agent_class_map = {
            "research": ResearchAgent,
            "data_mining": DataMiningAgent,
            "news_intelligence": NewsIntelligenceAgent
        }
        
        agent_class = agent_class_map.get(agent_type)
        if not agent_class:
            raise ValueError(f"Clase de agente no encontrada: {agent_type}")
        
        pool = self.agent_pools[agent_type]
        
        for i in range(count):
            try:
                # Crear instancia del agente
                agent = agent_class()
                
                # Configurar agente con parámetros de la pool
                if hasattr(agent, 'config'):
                    config = pool["config"]
                    for key, value in config.resource_limits.items():
                        if key in agent.config:
                            agent.config[key] = value
                
                # Registrar en pool
                agent_info = {
                    "instance": agent,
                    "instance_id": f"{agent_type}_{i+1}",
                    "status": "available",
                    "last_used": None,
                    "execution_count": 0
                }
                
                pool["agents"].append(agent_info)
                pool["available_agents"].append(agent_info)
                
            except Exception as e:
                self.logger.error(f"Error creando instancia {i+1} de {agent_type}: {e}")
    
    def get_available_agent(self, agent_type: str, timeout: int = 30) -> Optional[Any]:
        """
        Obtiene un agente especializado disponible
        
        Args:
            agent_type: Tipo de agente requerido
            timeout: Timeout para obtener agente
            
        Returns:
            Instancia de agente o None si no disponible
        """
        
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            pool = self.agent_pools.get(agent_type)
            if not pool:
                self.logger.warning(f"Pool de agentes no encontrada: {agent_type}")
                return None
            
            # Buscar agente disponible
            if pool["available_agents"]:
                agent_info = pool["available_agents"].pop(0)
                agent_info["status"] = "busy"
                agent_info["last_used"] = asyncio.get_event_loop().time()
                pool["busy_agents"].append(agent_info)
                
                self.logger.debug(f"Agente obtenido: {agent_type} - {agent_info['instance_id']}")
                return agent_info["instance"]
            
            # Esperar un poco antes de reintentar
            await asyncio.sleep(0.1)
        
        self.logger.warning(f"Timeout obteniendo agente: {agent_type}")
        return None
    
    def release_agent(self, agent_type: str, agent_instance: Any):
        """Libera un agente especializado de vuelta al pool"""
        
        pool = self.agent_pools.get(agent_type)
        if not pool:
            self.logger.warning(f"Pool de agentes no encontrada: {agent_type}")
            return
        
        # Buscar y liberar el agente
        for agent_info in pool["busy_agents"]:
            if agent_info["instance"] == agent_instance:
                agent_info["status"] = "available"
                agent_info["execution_count"] += 1
                
                # Mover a lista de disponibles
                pool["busy_agents"].remove(agent_info)
                pool["available_agents"].append(agent_info)
                
                self.logger.debug(f"Agente liberado: {agent_type} - {agent_info['instance_id']}")
                return
        
        self.logger.warning(f"Agente no encontrado en pool: {agent_type}")
    
    async def execute_specialized_task(
        self,
        task_type: str,
        task_config: Dict[str, Any],
        agent_type: str,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta una tarea especializada usando agente del pool
        
        Args:
            task_type: Tipo de tarea
            task_config: Configuración de la tarea
            agent_type: Tipo de agente requerido
            timeout: Timeout para la ejecución
            
        Returns:
            Resultado de la tarea
        """
        
        task_id = f"task_{int(asyncio.get_event_loop().time() * 1000)}"
        start_time = asyncio.get_event_loop().time()
        
        self.logger.info(f"Iniciando tarea especializada: {task_id} ({agent_type})")
        
        # Obtener agente del pool
        agent = await self.get_available_agent(agent_type, timeout=timeout or 30)
        
        if not agent:
            error_result = {
                "task_id": task_id,
                "status": "failed",
                "error": f"No hay agentes {agent_type} disponibles",
                "execution_time": 0.0
            }
            self.metrics["failed_executions"] += 1
            return error_result
        
        try:
            # Mapear tareas a métodos de agente
            task_method_map = {
                "research_investigation": self._execute_research_task,
                "data_extraction": self._execute_data_mining_task,
                "news_analysis": self._execute_news_intelligence_task,
                "trend_analysis": self._execute_trend_analysis_task,
                "fact_checking": self._execute_fact_check_task,
                "data_pipeline": self._execute_data_pipeline_task
            }
            
            task_method = task_method_map.get(task_type)
            if not task_method:
                raise ValueError(f"Tipo de tarea no soportada: {task_type}")
            
            # Ejecutar tarea
            result = await task_method(agent, task_config)
            
            # Calcular tiempo de ejecución
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # Actualizar métricas
            self.metrics["total_executions"] += 1
            self.metrics["successful_executions"] += 1
            
            agent_stats = self.metrics["agent_usage_stats"].setdefault(agent_type, {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0
            })
            agent_stats["total_executions"] += 1
            agent_stats["successful_executions"] += 1
            
            # Actualizar tiempo promedio
            if self.metrics["average_execution_time"] == 0:
                self.metrics["average_execution_time"] = execution_time
            else:
                self.metrics["average_execution_time"] = (
                    (self.metrics["average_execution_time"] + execution_time) / 2
                )
            
            # Resultado exitoso
            success_result = {
                "task_id": task_id,
                "status": "completed",
                "result": result,
                "execution_time": execution_time,
                "agent_type": agent_type,
                "task_type": task_type
            }
            
            self.logger.info(f"Tarea completada: {task_id} ({execution_time:.2f}s)")
            return success_result
            
        except Exception as e:
            # Error en ejecución
            execution_time = asyncio.get_event_loop().time() - start_time
            
            self.metrics["total_executions"] += 1
            self.metrics["failed_executions"] += 1
            
            agent_stats = self.metrics["agent_usage_stats"].setdefault(agent_type, {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0
            })
            agent_stats["total_executions"] += 1
            agent_stats["failed_executions"] += 1
            
            error_result = {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "execution_time": execution_time,
                "agent_type": agent_type,
                "task_type": task_type
            }
            
            self.logger.error(f"Tarea fallida: {task_id} - {e}")
            return error_result
            
        finally:
            # Siempre liberar el agente
            self.release_agent(agent_type, agent)
    
    async def _execute_research_task(self, agent: ResearchAgent, config: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta tarea de investigación"""
        
        query = config.get("query", "")
        method = config.get("method", "exploratory")
        max_iterations = config.get("max_iterations", 5)
        
        # Mapear métodos
        method_map = {
            "systematic": ResearchMethod.SYSTEMATIC,
            "exploratory": ResearchMethod.EXPLORATORY,
            "academic": ResearchMethod.ACADEMIC,
            "fact_check": ResearchMethod.FACT_CHECK
        }
        
        research_method = method_map.get(method, ResearchMethod.EXPLORATORY)
        
        # Ejecutar investigación
        report = agent.conduct_research(
            query=query,
            method=research_method,
            max_iterations=max_iterations
        )
        
        return {
            "query": report.query,
            "confidence_score": report.confidence_score,
            "sources_evaluated": len(report.sources_evaluated),
            "insights": len(report.insights),
            "key_findings": report.key_findings,
            "executive_summary": report.executive_summary,
            "recommendations": report.recommendations
        }
    
    async def _execute_data_mining_task(self, agent: DataMiningAgent, config: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta tarea de minería de datos"""
        
        source_config = config.get("source_config", {})
        enable_validation = config.get("enable_validation", True)
        
        # Extraer datos
        dataset = agent.extract_data(
            source_config=source_config,
            enable_validation=enable_validation
        )
        
        # Análisis si se solicita
        analysis = None
        if config.get("include_analysis", False):
            analysis = agent.analyze_dataset(dataset)
        
        return {
            "dataset_name": dataset.name,
            "total_records": dataset.total_records,
            "quality_assessment": dataset.quality_assessment.value,
            "schema": dataset.schema,
            "analysis": analysis
        }
    
    async def _execute_news_intelligence_task(self, agent: NewsIntelligenceAgent, config: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta tarea de inteligencia de noticias"""
        
        categories = config.get("categories", ["technology"])
        time_range = config.get("time_range", "24h")
        
        # Convertir categorías
        category_map = {
            "technology": NewsCategory.TECHNOLOGY,
            "politics": NewsCategory.POLITICS,
            "economy": NewsCategory.ECONOMY,
            "business": NewsCategory.BUSINESS,
            "health": NewsCategory.HEALTH
        }
        
        news_categories = [category_map.get(cat, NewsCategory.TECHNOLOGY) for cat in categories]
        
        # Generar reporte de inteligencia
        report = agent.generate_intelligence_report(
            time_range=time_range,
            categories=news_categories
        )
        
        return {
            "total_articles": report.total_articles,
            "total_stories": report.total_stories,
            "trends_detected": len(report.trends_detected),
            "breaking_news": len(report.breaking_news),
            "sentiment_analysis": report.sentiment_analysis,
            "bias_analysis": report.bias_analysis,
            "recommendations": report.recommendations
        }
    
    async def _execute_trend_analysis_task(self, agent: NewsIntelligenceAgent, config: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta análisis de tendencias"""
        
        # Usar News Intelligence Agent para análisis de tendencias
        articles = agent.collect_news(
            categories=[NewsCategory.TECHNOLOGY],
            time_range="24h"
        )
        
        trends = agent.analyze_trends(articles)
        
        return {
            "trends_detected": len(trends),
            "top_trends": [
                {
                    "topic": trend.topic,
                    "article_count": trend.article_count,
                    "confidence_score": trend.confidence_score
                }
                for trend in trends[:5]
            ]
        }
    
    async def _execute_fact_check_task(self, agent: ResearchAgent, config: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta verificación de hechos"""
        
        statement = config.get("statement", "")
        
        fact_check = agent.fact_check_statement(statement)
        
        return {
            "statement": fact_check.get("statement", ""),
            "confidence_score": fact_check.get("confidence_score", 0.0),
            "supporting_sources": len(fact_check.get("supporting_sources", [])),
            "verification_results": fact_check.get("verification_results", {})
        }
    
    async def _execute_data_pipeline_task(self, agent: DataMiningAgent, config: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta pipeline completo de datos"""
        
        sources = config.get("sources", [])
        transformations = config.get("transformations", [])
        
        # Extracción batch
        datasets = agent.extract_batch(sources)
        
        # Aplicar transformaciones
        processed_datasets = []
        for dataset in datasets:
            if transformations:
                transformed = agent.transform_dataset(dataset, transformations)
                processed_datasets.append(transformed)
            else:
                processed_datasets.append(dataset)
        
        return {
            "datasets_processed": len(processed_datasets),
            "total_records": sum(ds.total_records for ds in processed_datasets),
            "datasets": [
                {
                    "name": ds.name,
                    "quality": ds.quality_assessment.value,
                    "record_count": ds.total_records
                }
                for ds in processed_datasets
            ]
        }
    
    async def orchestrate_complex_workflow(
        self,
        workflow_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Orquesta un workflow complejo usando múltiples agentes especializados
        
        Args:
            workflow_config: Configuración del workflow
            
        Returns:
            Resultado del workflow completo
        """
        
        workflow_id = f"workflow_{int(asyncio.get_event_loop().time() * 1000)}"
        workflow_steps = workflow_config.get("steps", [])
        
        self.logger.info(f"Iniciando workflow complejo: {workflow_id} ({len(workflow_steps)} pasos)")
        
        workflow_results = {
            "workflow_id": workflow_id,
            "status": "started",
            "steps_executed": [],
            "total_execution_time": 0.0,
            "final_result": {}
        }
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            for i, step_config in enumerate(workflow_steps):
                step_id = f"{workflow_id}_step_{i+1}"
                step_start_time = asyncio.get_event_loop().time()
                
                self.logger.info(f"Ejecutando paso {i+1}/{len(workflow_steps)}: {step_config.get('name', 'unnamed')}")
                
                # Ejecutar paso
                step_result = await self.execute_specialized_task(
                    task_type=step_config.get("task_type"),
                    task_config=step_config.get("task_config", {}),
                    agent_type=step_config.get("agent_type")
                )
                
                step_execution_time = asyncio.get_event_loop().time() - step_start_time
                
                # Registrar resultado del paso
                step_summary = {
                    "step_id": step_id,
                    "step_name": step_config.get("name", f"step_{i+1}"),
                    "status": step_result.get("status"),
                    "execution_time": step_execution_time,
                    "agent_type": step_result.get("agent_type"),
                    "result": step_result.get("result") if step_result.get("status") == "completed" else None,
                    "error": step_result.get("error") if step_result.get("status") == "failed" else None
                }
                
                workflow_results["steps_executed"].append(step_summary)
                
                # Si el paso falló, terminar workflow
                if step_result.get("status") == "failed":
                    workflow_results["status"] = "failed"
                    workflow_results["error"] = f"Error en paso {i+1}: {step_result.get('error')}"
                    break
            
            # Si todos los pasos fueron exitosos
            if workflow_results["status"] != "failed":
                workflow_results["status"] = "completed"
                
                # Consolidar resultados finales
                workflow_results["final_result"] = {
                    "total_steps": len(workflow_steps),
                    "successful_steps": len([s for s in workflow_results["steps_executed"] if s["status"] == "completed"]),
                    "failed_steps": len([s for s in workflow_results["steps_executed"] if s["status"] == "failed"]),
                    "consolidated_data": self._consolidate_workflow_results(workflow_results["steps_executed"])
                }
            
        except Exception as e:
            workflow_results["status"] = "error"
            workflow_results["error"] = str(e)
            self.logger.error(f"Error en workflow {workflow_id}: {e}")
        
        finally:
            workflow_results["total_execution_time"] = asyncio.get_event_loop().time() - start_time
        
        self.logger.info(f"Workflow completado: {workflow_id} ({workflow_results['total_execution_time']:.2f}s)")
        return workflow_results
    
    def _consolidate_workflow_results(self, steps_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Consolida resultados de pasos del workflow"""
        
        consolidated = {
            "research_results": [],
            "data_extractions": [],
            "news_analyses": [],
            "insights": [],
            "recommendations": []
        }
        
        for step in steps_results:
            if step["status"] == "completed" and step["result"]:
                result = step["result"]
                agent_type = step["agent_type"]
                
                if agent_type == "research" and "insights" in result:
                    consolidated["insights"].extend(result["insights"])
                    if "recommendations" in result:
                        consolidated["recommendations"].extend(result["recommendations"])
                
                elif agent_type == "data_mining" and "dataset_name" in result:
                    consolidated["data_extractions"].append(result)
                
                elif agent_type == "news_intelligence" and "trends_detected" in result:
                    consolidated["news_analyses"].append(result)
        
        return consolidated
    
    def get_agent_pool_status(self) -> Dict[str, Any]:
        """Obtiene estado de los pools de agentes especializados"""
        
        status = {}
        
        for agent_type, pool in self.agent_pools.items():
            config = pool["config"]
            
            status[agent_type] = {
                "config": {
                    "max_instances": config.max_instances,
                    "priority": config.priority,
                    "timeout_seconds": config.timeout_seconds,
                    "capabilities": config.capabilities
                },
                "pool_status": {
                    "total_agents": len(pool["agents"]),
                    "available_agents": len(pool["available_agents"]),
                    "busy_agents": len(pool["busy_agents"]),
                    "utilization_rate": (len(pool["busy_agents"]) / len(pool["agents"])) * 100 if pool["agents"] else 0
                },
                "execution_stats": {
                    "total_executions": pool["total_executions"],
                    "successful_executions": pool["successful_executions"],
                    "failed_executions": pool["failed_executions"],
                    "success_rate": (pool["successful_executions"] / pool["total_executions"]) * 100 if pool["total_executions"] > 0 else 0
                }
            }
        
        return status
    
    def get_integration_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de la integración"""
        
        return {
            "integration_metrics": self.metrics.copy(),
            "pool_status": self.get_agent_pool_status(),
            "active_workflows": len(self.active_workflows),
            "registered_agent_types": list(self.agent_pools.keys())
        }
    
    def shutdown(self):
        """Cierra la integración y libera recursos"""
        
        self.logger.info("Cerrando integración de agentes especializados...")
        
        # Resetear pools de agentes
        for agent_type in self.agent_pools:
            self.agent_pools[agent_type]["agents"].clear()
            self.agent_pools[agent_type]["available_agents"].clear()
            self.agent_pools[agent_type]["busy_agents"].clear()
        
        self.logger.info("Integración cerrada")


# Instancia global de la integración
_specialized_integration = None

def get_specialized_integration(orchestrator_agent: Optional[MultiAgentOrchestratorAgent] = None) -> SpecializedAgentsIntegration:
    """Obtiene la instancia global de integración de agentes especializados"""
    
    global _specialized_integration
    
    if _specialized_integration is None:
        _specialized_integration = SpecializedAgentsIntegration(orchestrator_agent)
    
    return _specialized_integration


# Funciones de conveniencia para uso directo
async def execute_research_task(
    query: str,
    method: str = "exploratory",
    max_iterations: int = 5
) -> Dict[str, Any]:
    """Ejecuta tarea de investigación directamente"""
    
    integration = get_specialized_integration()
    
    return await integration.execute_specialized_task(
        task_type="research_investigation",
        task_config={
            "query": query,
            "method": method,
            "max_iterations": max_iterations
        },
        agent_type="research"
    )


async def execute_data_extraction(
    source_config: Dict[str, Any],
    include_analysis: bool = False
) -> Dict[str, Any]:
    """Ejecuta extracción de datos directamente"""
    
    integration = get_specialized_integration()
    
    return await integration.execute_specialized_task(
        task_type="data_extraction",
        task_config={
            "source_config": source_config,
            "include_analysis": include_analysis
        },
        agent_type="data_mining"
    )


async def execute_news_analysis(
    categories: List[str] = ["technology"],
    time_range: str = "24h"
) -> Dict[str, Any]:
    """Ejecuta análisis de noticias directamente"""
    
    integration = get_specialized_integration()
    
    return await integration.execute_specialized_task(
        task_type="news_analysis",
        task_config={
            "categories": categories,
            "time_range": time_range
        },
        agent_type="news_intelligence"
    )


if __name__ == "__main__":
    # Ejemplo de uso de la integración
    async def demo_integration():
        print("🚀 Demostración de Integración de Agentes Especializados")
        print("=" * 55)
        
        # Obtener integración
        integration = get_specialized_integration()
        
        # Mostrar estado inicial
        print("\n📊 Estado inicial de pools:")
        status = integration.get_agent_pool_status()
        for agent_type, pool_status in status.items():
            print(f"  🔧 {agent_type}:")
            print(f"     Instancias: {pool_status['pool_status']['total_agents']}")
            print(f"     Disponibles: {pool_status['pool_status']['available_agents']}")
            print(f"     Ocupadas: {pool_status['pool_status']['busy_agents']}")
        
        # Ejecutar tarea de investigación
        print("\n🔬 Ejecutando tarea de investigación...")
        research_result = await execute_research_task(
            query="inteligencia artificial medicina",
            method="exploratory"
        )
        
        print(f"✅ Investigación completada:")
        print(f"   Status: {research_result['status']}")
        print(f"   Tiempo: {research_result['execution_time']:.2f}s")
        
        # Ejecutar extracción de datos
        print("\n⛏️ Ejecutando extracción de datos...")
        data_result = await execute_data_extraction({
            "type": "web_api",
            "url": "https://jsonplaceholder.typicode.com/posts",
            "params": {"_limit": "3"}
        })
        
        print(f"✅ Extracción completada:")
        print(f"   Status: {data_result['status']}")
        print(f"   Registros: {data_result['result']['total_records'] if data_result['status'] == 'completed' else 'N/A'}")
        
        # Mostrar métricas finales
        print("\n📈 Métricas finales:")
        metrics = integration.get_integration_metrics()
        print(f"   Total ejecuciones: {metrics['integration_metrics']['total_executions']}")
        print(f"   Ejecuciones exitosas: {metrics['integration_metrics']['successful_executions']}")
        print(f"   Tasa de éxito: {(metrics['integration_metrics']['successful_executions'] / max(1, metrics['integration_metrics']['total_executions'])) * 100:.1f}%")
        
        # Cerrar integración
        integration.shutdown()
        print("\n🔚 Integración cerrada correctamente")
    
    # Ejecutar demo
    asyncio.run(demo_integration())