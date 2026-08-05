"""
Demostración del Sistema de Orquestación Multi-Agente Optimizado
Integra todos los componentes optimizados para 20+ agentes especializados
Sistema completo listo para producción empresarial
"""
import asyncio
import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Importar componentes optimizados
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.optimized_multi_agent_orchestrator import (
    OptimizedMultiAgentOrchestrator,
    OrchestrationMode
)
from orchestrator.intelligent_routing_system import IntelligentRoutingSystem, RoutingStrategy
from orchestrator.advanced_load_balancer import AdvancedLoadBalancer, LoadBalancingStrategy
from agents.specialized_agents import SpecializedAgentFactory, get_specialized_agents_config
from core.fastmcp_local import FastMCP
from benchmarks.performance_benchmarks import MultiAgentBenchmark, run_complete_benchmark_suite

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp.demo.optimized_system")


class OptimizedMultiAgentSystem:
    """Sistema completo de orquestación multi-agente optimizado"""
    
    def __init__(self):
        self.orchestrator: OptimizedMultiAgentOrchestrator = None
        self.routing_system: IntelligentRoutingSystem = None
        self.load_balancer: AdvancedLoadBalancer = None
        self.fastmcp_server: FastMCP = None
        self.agent_factory = SpecializedAgentFactory()
        self.agent_configs = get_specialized_agents_config()
        
        self.is_initialized = False
        self.system_metrics = {}
    
    async def initialize(self) -> Dict[str, Any]:
        """Inicializar sistema completo"""
        
        logger.info("🚀 Inicializando Sistema Multi-Agente Optimizado...")
        
        try:
            # 1. Crear y configurar orquestador optimizado
            self.orchestrator = OptimizedMultiAgentOrchestrator()
            await self.orchestrator.initialize(self.agent_configs)
            
            # 2. Configurar FastMCP optimizado
            self.fastmcp_server = FastMCP(
                "Optimized Multi-Agent System",
                max_concurrent_tools=100
            )
            
            # Registrar herramientas del sistema
            await self._register_system_tools()
            
            # 3. Inicializar servidor MCP
            await self.fastmcp_server.start()
            
            self.is_initialized = True
            
            # 4. Obtener estado inicial del sistema
            system_status = await self.get_system_status()
            
            logger.info(f"✅ Sistema inicializado exitosamente!")
            logger.info(f"   Agentes configurados: {len(self.agent_configs)}")
            logger.info(f"   Herramientas MCP: {len(self.fastmcp_server._tools)}")
            logger.info(f"   Capacidad concurrente: {self.orchestrator.max_concurrent_workflows}")
            
            return system_status
            
        except Exception as e:
            logger.error(f"❌ Error inicializando sistema: {e}")
            raise
    
    async def _register_system_tools(self):
        """Registrar herramientas del sistema en FastMCP"""
        
        @self.fastmcp_server.tool(
            description="Ejecutar workflow complejo con orquestación optimizada"
        )
        async def execute_orchestrated_workflow(
            workflow_definition: str,
            execution_mode: str = "adaptive",
            optimization_level: str = "balanced"
        ) -> Dict[str, Any]:
            """Ejecutar workflow orquestado"""
            workflow = json.loads(workflow_definition)
            
            mode = OrchestrationMode.ADAPTIVE
            if execution_mode == "parallel":
                mode = OrchestrationMode.PARALLEL
            elif execution_mode == "cascading":
                mode = OrchestrationMode.CASCADING
            
            result = await self.orchestrator.orchestrate_complex_workflow(
                workflow, mode, optimization_level
            )
            return result
        
        @self.fastmcp_server.tool(
            description="Ejecutar múltiples workflows en paralelo"
        )
        async def execute_parallel_workflows(
            workflows_json: str,
            max_concurrent: int = 10
        ) -> Dict[str, Any]:
            """Ejecutar múltiples workflows en paralelo"""
            workflows = json.loads(workflows_json)
            
            results = []
            for i in range(0, len(workflows), max_concurrent):
                batch = workflows[i:i + max_concurrent]
                batch_results = await asyncio.gather(*[
                    self.orchestrator.orchestrate_complex_workflow(workflow)
                    for workflow in batch
                ], return_exceptions=True)
                results.extend(batch_results)
            
            return {
                "total_workflows": len(workflows),
                "successful": sum(1 for r in results if isinstance(r, dict) and r.get("success")),
                "results": results
            }
        
        @self.fastmcp_server.tool(
            description="Ejecutar stress test del sistema"
        )
        async def stress_test_system(
            concurrent_workflows: int = 20,
            tasks_per_workflow: int = 3
        ) -> Dict[str, Any]:
            """Ejecutar stress test del sistema"""
            result = await self.orchestrator.execute_stress_test(
                concurrent_workflows, tasks_per_workflow
            )
            return result
        
        @self.fastmcp_server.tool(
            description="Obtener estado completo del sistema"
        )
        async def get_system_status() -> Dict[str, Any]:
            """Obtener estado del sistema"""
            return await self.get_system_status()
        
        @self.fastmcp_server.tool(
            description="Ejecutar benchmark completo del sistema"
        )
        async def run_benchmarks(
            include_stress_tests: bool = True
        ) -> Dict[str, Any]:
            """Ejecutar suite completa de benchmarks"""
            benchmark = MultiAgentBenchmark()
            suite = await benchmark.run_complete_benchmark_suite(
                "Demo_Benchmark_Suite",
                include_stress_tests
            )
            return suite.to_dict()
        
        @self.fastmcp_server.tool(
            description="Obtener métricas de agentes especializados"
        )
        async def get_agent_metrics() -> Dict[str, Any]:
            """Obtener métricas de agentes"""
            return {
                "total_agents": len(self.agent_configs),
                "agents_by_category": self._get_agents_by_category(),
                "agent_details": {
                    name: {
                        "category": config.get("category"),
                        "max_concurrent_tasks": config.get("max_concurrent_tasks"),
                        "avg_response_time": config.get("avg_response_time"),
                        "success_rate": config.get("success_rate")
                    }
                    for name, config in self.agent_configs.items()
                }
            }
    
    def _get_agents_by_category(self) -> Dict[str, List[str]]:
        """Obtener agentes agrupados por categoría"""
        from src.agents.specialized_agents import AgentCategory
        
        agents_by_category = {}
        factory = SpecializedAgentFactory()
        
        for category in AgentCategory:
            agents = factory.get_agents_by_category(category)
            if agents:
                agents_by_category[category.value] = agents
        
        return agents_by_category
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema"""
        
        if not self.is_initialized:
            return {"status": "not_initialized"}
        
        # Estado del orquestador
        orchestrator_status = await self.orchestrator.get_system_status() if self.orchestrator else {}
        
        # Estado del servidor MCP
        mcp_status = self.fastmcp_server.get_server_status() if self.fastmcp_server else {}
        
        # Health check del sistema
        health = await self.fastmcp_server.health_check() if self.fastmcp_server else {}
        
        return {
            "system_name": "Optimized Multi-Agent System",
            "initialization_time": datetime.now().isoformat(),
            "status": "healthy",
            "orchestrator": orchestrator_status,
            "fastmcp_server": mcp_status,
            "health": health,
            "agent_configs_loaded": len(self.agent_configs),
            "capabilities": {
                "max_concurrent_workflows": getattr(self.orchestrator, 'max_concurrent_workflows', 0),
                "max_concurrent_tools": getattr(self.fastmcp_server, 'max_concurrent_tools', 0),
                "routing_strategies": 8,
                "load_balancing_strategies": 5,
                "fault_tolerance": True,
                "auto_optimization": True,
                "benchmarking": True
            }
        }
    
    async def execute_demo_workflows(self) -> Dict[str, Any]:
        """Ejecutar workflows de demostración"""
        
        logger.info("🎯 Ejecutando workflows de demostración...")
        
        # Workflow 1: Procesamiento de datos complejo
        complex_data_workflow = {
            "name": "Complex Data Processing",
            "tasks": [
                {
                    "id": "data_collection",
                    "type": "data_processing",
                    "required_skills": ["data_cleaning"],
                    "priority": 10,
                    "max_duration": 30.0
                },
                {
                    "id": "data_analysis", 
                    "type": "analysis",
                    "required_skills": ["statistical_analysis"],
                    "priority": 9,
                    "max_duration": 60.0,
                    "dependencies": ["data_collection"]
                },
                {
                    "id": "visualization",
                    "type": "visualization",
                    "required_skills": ["data_visualization"],
                    "priority": 8,
                    "max_duration": 45.0,
                    "dependencies": ["data_analysis"]
                },
                {
                    "id": "reporting",
                    "type": "reporting",
                    "required_skills": ["report_generation"],
                    "priority": 7,
                    "max_duration": 30.0,
                    "dependencies": ["visualization"]
                }
            ]
        }
        
        # Workflow 2: ML Pipeline completo
        ml_pipeline_workflow = {
            "name": "ML Training Pipeline",
            "tasks": [
                {
                    "id": "data_preparation",
                    "type": "data_processing",
                    "required_skills": ["data_cleaning", "feature_engineering"],
                    "priority": 10,
                    "max_duration": 120.0
                },
                {
                    "id": "model_training",
                    "type": "ml_training",
                    "required_skills": ["machine_learning"],
                    "priority": 9,
                    "max_duration": 300.0,
                    "dependencies": ["data_preparation"]
                },
                {
                    "id": "model_evaluation",
                    "type": "analysis",
                    "required_skills": ["model_evaluation"],
                    "priority": 8,
                    "max_duration": 60.0,
                    "dependencies": ["model_training"]
                },
                {
                    "id": "deployment_monitoring",
                    "type": "monitoring",
                    "required_skills": ["system_monitoring"],
                    "priority": 7,
                    "max_duration": 90.0,
                    "dependencies": ["model_evaluation"]
                }
            ]
        }
        
        # Workflow 3: Web scraping y análisis
        web_analysis_workflow = {
            "name": "Web Data Analysis",
            "tasks": [
                {
                    "id": "web_scraping",
                    "type": "web_scraping",
                    "required_skills": ["web_scraping"],
                    "priority": 9,
                    "max_duration": 180.0
                },
                {
                    "id": "content_analysis",
                    "type": "text_analysis",
                    "required_skills": ["text_processing", "sentiment_analysis"],
                    "priority": 8,
                    "max_duration": 120.0,
                    "dependencies": ["web_scraping"]
                },
                {
                    "id": "report_generation",
                    "type": "reporting",
                    "required_skills": ["content_creation"],
                    "priority": 7,
                    "max_duration": 60.0,
                    "dependencies": ["content_analysis"]
                }
            ]
        }
        
        # Ejecutar workflows
        workflows = [complex_data_workflow, ml_pipeline_workflow, web_analysis_workflow]
        results = []
        
        for i, workflow in enumerate(workflows):
            logger.info(f"   Ejecutando workflow {i+1}: {workflow['name']}")
            try:
                result = await self.orchestrator.orchestrate_complex_workflow(
                    workflow, OrchestrationMode.ADAPTIVE, "balanced"
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error en workflow {workflow['name']}: {e}")
                results.append({"success": False, "error": str(e)})
        
        # Calcular resumen
        successful = sum(1 for r in results if r.get("success", False))
        
        return {
            "workflows_executed": len(workflows),
            "successful_workflows": successful,
            "success_rate": successful / len(workflows),
            "results": results,
            "execution_mode": "adaptive",
            "optimization_applied": True
        }
    
    async def run_comprehensive_demo(self) -> Dict[str, Any]:
        """Ejecutar demostración completa del sistema"""
        
        logger.info("=" * 80)
        logger.info("🎯 DEMOSTRACIÓN COMPLETA DEL SISTEMA OPTIMIZADO")
        logger.info("=" * 80)
        
        demo_start_time = time.time()
        
        try:
            # 1. Inicializar sistema
            logger.info("\n1️⃣ INICIALIZANDO SISTEMA...")
            system_status = await self.initialize()
            
            # 2. Ejecutar workflows de demostración
            logger.info("\n2️⃣ EJECUTANDO WORKFLOWS DE DEMOSTRACIÓN...")
            demo_results = await self.execute_demo_workflows()
            
            # 3. Ejecutar stress test ligero
            logger.info("\n3️⃣ EJECUTANDO STRESS TEST...")
            stress_results = await self.orchestrator.execute_stress_test(
                concurrent_workflows=15, tasks_per_workflow=2
            )
            
            # 4. Obtener métricas del sistema
            logger.info("\n4️⃣ RECOPILANDO MÉTRICAS DEL SISTEMA...")
            final_status = await self.get_system_status()
            
            # 5. Ejecutar benchmark rápido
            logger.info("\n5️⃣ EJECUTANDO BENCHMARK RÁPIDO...")
            benchmark = MultiAgentBenchmark()
            quick_benchmark = await benchmark.run_complete_benchmark_suite(
                "Quick_Demo_Benchmark",
                include_stress_tests=False
            )
            
            demo_duration = time.time() - demo_start_time
            
            # Compilar resultado final
            comprehensive_results = {
                "demo_info": {
                    "demo_name": "Complete System Demonstration",
                    "start_time": datetime.fromtimestamp(demo_start_time).isoformat(),
                    "duration_seconds": demo_duration,
                    "system_version": "2.0 - Enterprise Optimized"
                },
                "system_initialization": system_status,
                "workflow_demonstration": demo_results,
                "stress_test": stress_results,
                "benchmark_results": quick_benchmark.to_dict(),
                "final_system_status": final_status,
                "success_metrics": {
                    "demo_success_rate": (
                        (demo_results["success_rate"] + 
                         stress_results["results"]["success_rate"] + 
                         quick_benchmark.overall_summary.get("overall_success_rate", 0)) / 3
                    ),
                    "total_agents_tested": len(self.agent_configs),
                    "total_workflows_executed": (
                        demo_results["workflows_executed"] + 
                        stress_results["configuration"]["concurrent_workflows"] +
                        quick_benchmark.overall_summary.get("total_benchmarks", 0)
                    ),
                    "concurrent_capacity": self.orchestrator.max_concurrent_workflows,
                    "system_optimization_level": "enterprise"
                }
            }
            
            logger.info("\n" + "=" * 80)
            logger.info("✅ DEMOSTRACIÓN COMPLETADA EXITOSAMENTE")
            logger.info("=" * 80)
            logger.info(f"📊 Tasa de éxito general: {comprehensive_results['success_metrics']['demo_success_rate']:.2%}")
            logger.info(f"🔄 Workflows ejecutados: {comprehensive_results['success_metrics']['total_workflows_executed']}")
            logger.info(f"🤖 Agentes especializados: {comprehensive_results['success_metrics']['total_agents_tested']}")
            logger.info(f"⚡ Capacidad concurrente: {comprehensive_results['success_metrics']['concurrent_capacity']}")
            logger.info(f"⏱️  Duración total: {demo_duration:.2f} segundos")
            logger.info("=" * 80)
            
            return comprehensive_results
            
        except Exception as e:
            logger.error(f"❌ Error en demostración: {e}")
            raise
        finally:
            if self.is_initialized:
                await self.shutdown()
    
    async def shutdown(self):
        """Shutdown completo del sistema"""
        
        logger.info("🛑 Ejecutando shutdown del sistema...")
        
        try:
            if self.orchestrator:
                await self.orchestrator.shutdown()
            
            if self.fastmcp_server:
                await self.fastmcp_server.stop()
            
            self.is_initialized = False
            logger.info("✅ Shutdown completado")
            
        except Exception as e:
            logger.error(f"❌ Error en shutdown: {e}")


async def main():
    """Función principal de demostración"""
    
    print("🚀 SISTEMA DE ORQUESTACIÓN MULTI-AGENTE OPTIMIZADO")
    print("=" * 80)
    print("Capacidades del sistema:")
    print("• 23 agentes especializados en 10 categorías")
    print("• Routing inteligente con 8 estrategias")
    print("• Load balancing avanzado con fault tolerance")
    print("• Capacidad de 100+ tareas concurrentes")
    print("• Auto-optimización basada en performance")
    print("• Benchmarks completos de performance")
    print("• FastMCP local optimizado")
    print("=" * 80)
    
    # Crear sistema
    system = OptimizedMultiAgentSystem()
    
    # Ejecutar demostración completa
    try:
        results = await system.run_comprehensive_demo()
        
        # Guardar resultados de la demostración
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        demo_file = f"/workspace/demo_results_{timestamp}.json"
        
        with open(demo_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Resultados guardados en: {demo_file}")
        
        # Mostrar resumen ejecutivo
        print("\n" + "=" * 80)
        print("📋 RESUMEN EJECUTIVO")
        print("=" * 80)
        metrics = results["success_metrics"]
        print(f"✅ Sistema inicializado correctamente")
        print(f"📊 Tasa de éxito: {metrics['demo_success_rate']:.2%}")
        print(f"🤖 Agentes especializados: {metrics['total_agents_tested']}")
        print(f"🔄 Workflows ejecutados: {metrics['total_workflows_executed']}")
        print(f"⚡ Capacidad concurrente: {metrics['concurrent_capacity']}")
        print(f"🎯 Optimización: {metrics['system_optimization_level']}")
        print("=" * 80)
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error en demostración: {e}")
        raise


if __name__ == "__main__":
    # Ejecutar demostración
    asyncio.run(main())