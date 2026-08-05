#!/usr/bin/env python3
"""
Demo Script para Performance Benchmarking Suite
Ejecuta una demostración completa del sistema de benchmarking
"""

import asyncio
import time
import json
import logging
from pathlib import Path
from datetime import datetime
import sys
import os

# Agregar el directorio de scripts al path
sys.path.append(str(Path(__file__).parent / "scripts"))

from performance_benchmarker import PerformanceBenchmarker

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BenchmarkDemo:
    """Demo de la suite de benchmarking"""
    
    def __init__(self):
        self.demo_results_dir = Path("demo_results")
        self.demo_results_dir.mkdir(exist_ok=True)
        
    def print_banner(self):
        """Mostrar banner de la demo"""
        banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🚀 PERFORMANCE BENCHMARKING SUITE DEMO                                    ║
║   MCP-Core-Superior vs MiniMax Agent                                       ║
║                                                                              ║
║   Esta demo ejecutará una suite completa de benchmarks                     ║
║   comparando el rendimiento de ambos sistemas                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def print_demo_info(self):
        """Mostrar información de la demo"""
        info = """
📋 MÉTRICAS QUE SE EVALUARÁN:

1. 📊 Latencia de Respuesta
   - Tiempo promedio de respuesta por request
   - Percentiles (50, 90, 95, 99)
   
2. ⚡ Throughput (Requests/segundo)
   - Capacidad de procesamiento
   - Escalabilidad con múltiples usuarios
   
3. 💾 Memory Usage y Resource Consumption
   - Consumo de memoria durante carga
   - Eficiencia de recursos
   
4. 📈 Escalabilidad con Usuarios Concurrentes
   - Performance con 1, 5, 10, 25, 50, 100 usuarios
   - Degradación de performance
   
5. 🎯 Success Rate y Accuracy
   - Tasa de éxito en operaciones
   - Precisión de respuestas
   
6. 💰 Cost per Operation
   - Costo promedio por operación
   - Eficiencia económica
   
7. 🔄 Time to Complete Complex Workflows
   - Tiempo de workflows multi-paso
   - Procesamiento paralelo
   
8. ❄️ Cold Start Time
   - Tiempo de inicio en frío
   - Time to first request
   
9. 🗄️ Database Query Performance
   - Performance en consultas SELECT, INSERT, UPDATE, DELETE
   - Latencia de base de datos
   
10. 🌐 Network Overhead
    - Overhead de headers y payload
    - Eficiencia de comunicación

⏱️  DURACIÓN ESTIMADA: 10-15 minutos
🔧 REQUISITOS: Ambos agentes deben estar ejecutándose
        """
        print(info)
    
    async def simulate_benchmark_execution(self):
        """Simular ejecución de benchmarks con datos realistas"""
        logger.info("🚀 Iniciando simulación de benchmarks...")
        
        # Datos simulados realistas
        simulated_results = []
        
        # Simular latencia (MCP generalmente más rápido)
        mcp_latencies = [85, 92, 78, 110, 95, 88, 102, 90, 96, 89]
        minimax_latencies = [145, 152, 138, 165, 148, 155, 140, 162, 150, 147]
        
        simulated_results.extend([
            self._create_result("latency", "mcp_core_superior", "avg_latency", 
                              sum(mcp_latencies)/len(mcp_latencies), "ms"),
            self._create_result("latency", "minimax_agent", "avg_latency", 
                              sum(minimax_latencies)/len(minimax_latencies), "ms")
        ])
        
        # Simular throughput (MCP maneja más requests)
        mcp_throughput = [145, 152, 148, 140, 155, 150, 142, 147, 153, 149]
        minimax_throughput = [95, 102, 98, 92, 105, 100, 94, 99, 103, 97]
        
        simulated_results.extend([
            self._create_result("throughput", "mcp_core_superior", "requests_per_second", 
                              sum(mcp_throughput)/len(mcp_throughput), "req/s"),
            self._create_result("throughput", "minimax_agent", "requests_per_second", 
                              sum(minimax_throughput)/len(minimax_throughput), "req/s")
        ])
        
        # Simular memory usage
        simulated_results.extend([
            self._create_result("memory", "mcp_core_superior", "memory_usage", 245, "MB"),
            self._create_result("memory", "minimax_agent", "memory_usage", 312, "MB")
        ])
        
        # Simular success rate
        simulated_results.extend([
            self._create_result("accuracy", "mcp_core_superior", "success_rate", 98.5, "percent"),
            self._create_result("accuracy", "minimax_agent", "success_rate", 96.2, "percent")
        ])
        
        # Simular escalabilidad
        for users in [1, 5, 10, 25, 50, 100]:
            # MCP mantiene mejor performance
            mcp_perf = max(95 - users * 0.1, 70)
            minimax_perf = max(75 - users * 0.2, 40)
            
            simulated_results.extend([
                self._create_result("scalability", "mcp_core_superior", "performance_score", 
                                  mcp_perf, "percent", {"concurrent_users": users}),
                self._create_result("scalability", "minimax_agent", "performance_score", 
                                  minimax_perf, "percent", {"concurrent_users": users})
            ])
        
        # Simular cost analysis
        simulated_results.extend([
            self._create_result("cost", "mcp_core_superior", "cost_per_operation", 0.8, "USD"),
            self._create_result("cost", "minimax_agent", "cost_per_operation", 1.2, "USD")
        ])
        
        # Simular workflow time
        workflows = ["multi_step_processing", "parallel_execution", "data_pipeline"]
        for workflow in workflows:
            mcp_time = 2500 + len(workflow) * 100
            minimax_time = 3500 + len(workflow) * 150
            
            simulated_results.extend([
                self._create_result("workflow_time", "mcp_core_superior", "completion_time", 
                                  mcp_time, "ms", {"workflow": workflow}),
                self._create_result("workflow_time", "minimax_agent", "completion_time", 
                                  minimax_time, "ms", {"workflow": workflow})
            ])
        
        # Simular cold start
        simulated_results.extend([
            self._create_result("cold_start", "mcp_core_superior", "startup_time", 1200, "ms"),
            self._create_result("cold_start", "minimax_agent", "startup_time", 2100, "ms")
        ])
        
        # Simular database performance
        query_types = ["SELECT", "INSERT", "UPDATE", "DELETE"]
        for query_type in query_types:
            mcp_query_time = 15 + hash(query_type) % 10
            minimax_query_time = 25 + hash(query_type) % 15
            
            simulated_results.extend([
                self._create_result("database", "mcp_core_superior", "query_time", 
                                  mcp_query_time, "ms", {"query_type": query_type}),
                self._create_result("database", "minimax_agent", "query_time", 
                                  minimax_query_time, "ms", {"query_type": query_type})
            ])
        
        # Simular network overhead
        simulated_results.extend([
            self._create_result("network", "mcp_core_superior", "overhead", 850, "bytes"),
            self._create_result("network", "minimax_agent", "overhead", 1200, "bytes")
        ])
        
        return simulated_results
    
    def _create_result(self, test_name, agent_name, metric_name, value, unit, additional_data=None):
        """Crear resultado de benchmark simulado"""
        from performance_benchmarker import BenchmarkResult
        
        return BenchmarkResult(
            test_name=test_name,
            agent_name=agent_name,
            metric_name=metric_name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            additional_data=additional_data or {}
        )
    
    def analyze_simulated_results(self, results):
        """Analizar resultados simulados"""
        logger.info("📊 Analizando resultados simulados...")
        
        # Separar resultados por agente
        mcp_results = [r for r in results if r.agent_name == "mcp_core_superior"]
        minimax_results = [r for r in results if r.agent_name == "minimax_agent"]
        
        analysis = {
            "summary": {
                "total_tests": len(results),
                "mcp_tests": len(mcp_results),
                "minimax_tests": len(minimax_results)
            },
            "mcp_performance": {},
            "minimax_performance": {},
            "comparative_analysis": {},
            "winner": None
        }
        
        # Analizar métricas principales
        metrics_to_analyze = ["latency", "throughput", "memory", "accuracy"]
        
        for metric in metrics_to_analyze:
            mcp_metric_results = [r for r in mcp_results if metric in r.test_name]
            minimax_metric_results = [r for r in minimax_results if metric in r.test_name]
            
            if mcp_metric_results and minimax_metric_results:
                mcp_avg = sum(r.value for r in mcp_metric_results) / len(mcp_metric_results)
                minimax_avg = sum(r.value for r in minimax_metric_results) / len(minimax_metric_results)
                
                analysis["mcp_performance"][metric] = mcp_avg
                analysis["minimax_performance"][metric] = minimax_avg
                
                # Determinar ganador
                if metric in ["latency", "memory"]:  # Menor es mejor
                    winner = "mcp_core_superior" if mcp_avg < minimax_avg else "minimax_agent"
                else:  # Mayor es mejor
                    winner = "mcp_core_superior" if mcp_avg > minimax_avg else "minimax_agent"
                
                analysis["comparative_analysis"][metric] = {
                    "mcp_value": mcp_avg,
                    "minimax_value": minimax_avg,
                    "winner": winner,
                    "difference_percent": abs((mcp_avg - minimax_avg) / min(mcp_avg, minimax_avg)) * 100
                }
        
        # Determinar ganador general
        mcp_wins = sum(1 for analysis_data in analysis["comparative_analysis"].values() 
                      if analysis_data["winner"] == "mcp_core_superior")
        minimax_wins = sum(1 for analysis_data in analysis["comparative_analysis"].values() 
                          if analysis_data["winner"] == "minimax_agent")
        
        if mcp_wins > minimax_wins:
            analysis["winner"] = "MCP-Core-Superior"
        elif minimax_wins > mcp_wins:
            analysis["winner"] = "MiniMax Agent"
        else:
            analysis["winner"] = "Empate"
        
        analysis["wins"] = {"mcp": mcp_wins, "minimax": minimax_wins}
        
        return analysis
    
    def print_results_summary(self, analysis):
        """Imprimir resumen de resultados"""
        print("\n" + "="*80)
        print("📊 RESULTADOS DE LA DEMO")
        print("="*80)
        
        print(f"\n🏆 GANADOR GENERAL: {analysis['winner']}")
        print(f"   Victorias MCP-Core-Superior: {analysis['wins']['mcp']}")
        print(f"   Victorias MiniMax Agent: {analysis['wins']['minimax']}")
        
        print(f"\n📈 MÉTRICAS DETALLADAS:")
        for metric, data in analysis["comparative_analysis"].items():
            winner_name = "MCP-Core-Superior" if data["winner"] == "mcp_core_superior" else "MiniMax Agent"
            print(f"\n   {metric.title()}:")
            print(f"     🟢 MCP-Core-Superior: {data['mcp_value']:.2f}")
            print(f"     🔴 MiniMax Agent: {data['minimax_value']:.2f}")
            print(f"     🏆 Ganador: {winner_name}")
            print(f"     📊 Diferencia: {data['difference_percent']:.1f}%")
        
        print(f"\n💡 RECOMENDACIONES:")
        if analysis["winner"] == "MCP-Core-Superior":
            print("   ✅ MCP-Core-Superior muestra superioridad en performance")
            print("   📈 Considerar usar MCP-Core-Superior para producción")
            print("   🔍 Investigar qué optimizaciones hace MCP mejor")
        elif analysis["winner"] == "MiniMax Agent":
            print("   ✅ MiniMax Agent muestra mejor performance en algunos aspectos")
            print("   📊 Evaluar costo-beneficio vs MCP-Core-Superior")
        else:
            print("   ⚖️ Ambos agentes muestran performance comparable")
            print("   🎯 Considerar factores adicionales (costo, facilidad de uso, etc.)")
        
        print("\n⚠️  NOTA IMPORTANTE:")
        print("   Esta es una demo con datos simulados.")
        print("   Para resultados reales, ejecuta la suite completa de benchmarks.")
    
    def save_demo_results(self, results, analysis):
        """Guardar resultados de la demo"""
        demo_data = {
            "demo_metadata": {
                "demo_type": "simulated_benchmark",
                "timestamp": datetime.now().isoformat(),
                "note": "Datos simulados para demostración"
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "agent_name": r.agent_name,
                    "metric_name": r.metric_name,
                    "value": r.value,
                    "unit": r.unit,
                    "timestamp": r.timestamp.isoformat(),
                    "additional_data": r.additional_data
                } for r in results
            ],
            "analysis": analysis
        }
        
        demo_file = self.demo_results_dir / "demo_benchmark_results.json"
        with open(demo_file, 'w') as f:
            json.dump(demo_data, f, indent=2, default=str)
        
        logger.info(f"Resultados de demo guardados en: {demo_file}")
    
    def create_demo_dashboard(self, analysis):
        """Crear dashboard simple para la demo"""
        dashboard_html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Demo - Performance Benchmark Dashboard</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .winner {{ background: linear-gradient(45deg, #4CAF50, #45a049); color: white; padding: 20px; border-radius: 10px; font-size: 1.5em; font-weight: bold; text-align: center; margin: 20px 0; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 30px 0; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 4px solid #007bff; }}
        .metric-title {{ font-size: 1.2em; font-weight: bold; margin-bottom: 10px; }}
        .agent-row {{ display: flex; justify-content: space-between; margin: 5px 0; }}
        .mcp {{ color: #4CAF50; font-weight: bold; }}
        .minimax {{ color: #f44336; font-weight: bold; }}
        .winner-indicator {{ background: #28a745; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; }}
        .note {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Performance Benchmark Demo Dashboard</h1>
            <p>MCP-Core-Superior vs MiniMax Agent - Resultados Simulados</p>
            <p>Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        </div>
        
        <div class="winner">
            🏆 Ganador: {analysis['winner']}
            <br>
            <small>MCP: {analysis['wins']['mcp']} victorias | MiniMax: {analysis['wins']['minimax']} victorias</small>
        </div>
        
        <div class="metrics-grid">
"""
        
        for metric, data in analysis["comparative_analysis"].items():
            mcp_winner = data["winner"] == "mcp_core_superior"
            winner_class = "mcp" if mcp_winner else "minimax"
            
            dashboard_html += f"""
            <div class="metric-card">
                <div class="metric-title">{metric.title()}</div>
                <div class="agent-row">
                    <span class="mcp">MCP-Core-Superior:</span>
                    <span>{data['mcp_value']:.2f}</span>
                </div>
                <div class="agent-row">
                    <span class="minimax">MiniMax Agent:</span>
                    <span>{data['minimax_value']:.2f}</span>
                </div>
                <div style="text-align: center; margin-top: 10px;">
                    <span class="winner-indicator">Ganador: {'MCP' if mcp_winner else 'MiniMax'}</span>
                </div>
                <div style="text-align: center; margin-top: 5px; font-size: 0.9em; color: #666;">
                    Diferencia: {data['difference_percent']:.1f}%
                </div>
            </div>
"""
        
        dashboard_html += f"""
        </div>
        
        <div class="note">
            <strong>⚠️ Nota Importante:</strong> Estos son datos simulados para demostración. 
            Para obtener resultados reales, ejecuta la suite completa de benchmarks:
            <code>python scripts/benchmark_orchestrator.py</code>
        </div>
        
        <div style="text-align: center; margin-top: 30px; color: #666;">
            <p>Para ejecutar benchmarks reales:</p>
            <p><code>cd benchmarks && ./setup_benchmarks.sh && python scripts/benchmark_orchestrator.py</code></p>
        </div>
    </div>
</body>
</html>
        """
        
        dashboard_file = self.demo_results_dir / "demo_dashboard.html"
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            f.write(dashboard_html)
        
        logger.info(f"Dashboard de demo guardado en: {dashboard_file}")
    
    async def run_demo(self):
        """Ejecutar demo completa"""
        self.print_banner()
        self.print_demo_info()
        
        input("\nPresiona Enter para continuar con la demo...")
        
        print("\n🚀 Ejecutando simulación de benchmarks...")
        start_time = time.time()
        
        # Simular progreso
        progress_steps = [
            "Inicializando métricas...",
            "Ejecutando tests de latencia...",
            "Midiendo throughput...",
            "Analizando memory usage...",
            "Probando escalabilidad...",
            "Evaluando accuracy...",
            "Calculando costos...",
            "Ejecutando workflows...",
            "Midiendo cold start...",
            "Probando database queries...",
            "Analizando network overhead...",
            "Generando reportes..."
        ]
        
        for i, step in enumerate(progress_steps):
            print(f"   [{i+1:2d}/{len(progress_steps)}] {step}")
            await asyncio.sleep(0.5)  # Simular trabajo
        
        # Ejecutar simulación
        results = await self.simulate_benchmark_execution()
        analysis = self.analyze_simulated_results(results)
        
        end_time = time.time()
        print(f"\n✅ Demo completada en {end_time - start_time:.2f} segundos")
        
        # Mostrar resultados
        self.print_results_summary(analysis)
        
        # Guardar resultados
        self.save_demo_results(results, analysis)
        self.create_demo_dashboard(analysis)
        
        print(f"\n📁 Archivos generados:")
        print(f"   • {self.demo_results_dir}/demo_benchmark_results.json")
        print(f"   • {self.demo_results_dir}/demo_dashboard.html")
        
        print(f"\n🎯 PARA EJECUTAR BENCHMARKS REALES:")
        print(f"   1. cd benchmarks")
        print(f"   2. ./setup_benchmarks.sh")
        print(f"   3. python scripts/benchmark_orchestrator.py")
        
        return analysis

async def main():
    """Función principal"""
    demo = BenchmarkDemo()
    
    try:
        await demo.run_demo()
        
        print("\n" + "="*80)
        print("✅ DEMO COMPLETADA EXITOSAMENTE")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante demo: {str(e)}")
        logger.error(f"Error en demo: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())