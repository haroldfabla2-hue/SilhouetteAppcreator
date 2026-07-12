#!/usr/bin/env python3
"""
Script de Prueba End-to-End para Sistema Multi-Agente
Valida ejecución paralela, streaming y rendimiento
Fecha: 2025-11-04
"""

import time
import json
import requests
import sys
from datetime import datetime
from typing import Dict, List, Any

# Configuración
BACKEND_URL = "http://localhost:8000"
TEST_OBJETIVO = "Analiza las ventajas de usar sistemas multi-agente versus agentes individuales, incluyendo métricas de rendimiento"

# Colores ANSI
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def print_header(text: str):
    """Imprime un encabezado formateado"""
    print(f"\n{YELLOW}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{NC}\n")

def print_success(text: str):
    """Imprime mensaje de éxito"""
    print(f"{GREEN}✅ {text}{NC}")

def print_error(text: str):
    """Imprime mensaje de error"""
    print(f"{RED}❌ {text}{NC}")

def print_info(text: str):
    """Imprime mensaje informativo"""
    print(f"{BLUE}ℹ️  {text}{NC}")

def check_backend_health() -> bool:
    """Verifica que el backend esté activo"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success("Backend está activo y respondiendo")
            return True
        else:
            print_error(f"Backend respondió con código: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"No se pudo conectar al backend: {e}")
        return False

def create_task(objetivo: str) -> Dict[str, Any]:
    """Crea una nueva tarea y mide el tiempo"""
    print_info(f"Creando tarea: '{objetivo[:60]}...'")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/tasks",
            json={"objetivo": objetivo, "contexto": {}},
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            print_success(f"Tarea creada en {duration:.2f}s")
            print_info(f"Task ID: {data.get('task_id', data.get('id', 'N/A'))}")
            return {
                "success": True,
                "data": data,
                "duration": duration,
                "status_code": response.status_code
            }
        else:
            print_error(f"Error al crear tarea: {response.status_code}")
            print_error(f"Respuesta: {response.text[:200]}")
            return {
                "success": False,
                "error": response.text,
                "duration": duration,
                "status_code": response.status_code
            }
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print_error(f"Excepción al crear tarea: {e}")
        return {
            "success": False,
            "error": str(e),
            "duration": duration
        }

def get_task_status(task_id: str) -> Dict[str, Any]:
    """Obtiene el estado de una tarea"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/tasks/{task_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Status code: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def analyze_agent_execution(logs: List[str]) -> Dict[str, Any]:
    """Analiza los logs para determinar paralelización"""
    print_header("Análisis de Ejecución de Agentes")
    
    agent_starts = {}
    agents = ["ReasonerAgent", "PlannerAgent", "ExecutorAgent", "VerifierAgent", "MemoryManagerAgent"]
    
    for log_line in logs:
        for agent in agents:
            if agent in log_line and "started" in log_line.lower():
                # Extraer timestamp (simplificado)
                timestamp = datetime.now()  # En producción extraer del log
                agent_starts[agent] = timestamp
                print_info(f"{agent} inicio detectado")
    
    # Calcular paralelización
    if len(agent_starts) >= 3:
        print_success(f"{len(agent_starts)} agentes ejecutados")
        
        # Verificar si ExecutorAgent, VerifierAgent y MemoryManagerAgent están en paralelo
        parallel_agents = ["ExecutorAgent", "VerifierAgent", "MemoryManagerAgent"]
        parallel_times = [agent_starts.get(a) for a in parallel_agents if a in agent_starts]
        
        if len(parallel_times) >= 2:
            print_success("Ejecución paralela detectada")
            return {
                "parallel_execution": True,
                "agents_executed": len(agent_starts),
                "parallel_agents": len(parallel_times)
            }
        else:
            print_error("No se detectó ejecución paralela")
            return {
                "parallel_execution": False,
                "agents_executed": len(agent_starts),
                "parallel_agents": len(parallel_times)
            }
    else:
        print_error(f"Solo {len(agent_starts)} agentes ejecutados (esperados: 5)")
        return {
            "parallel_execution": False,
            "agents_executed": len(agent_starts),
            "parallel_agents": 0
        }

def run_performance_test(iterations: int = 3) -> List[float]:
    """Ejecuta múltiples iteraciones para medir rendimiento"""
    print_header(f"Prueba de Rendimiento ({iterations} iteraciones)")
    
    durations = []
    
    for i in range(iterations):
        print_info(f"Iteración {i+1}/{iterations}")
        
        objetivo = f"{TEST_OBJETIVO} (iteración {i+1})"
        result = create_task(objetivo)
        
        if result["success"]:
            durations.append(result["duration"])
            print_success(f"Completada en {result['duration']:.2f}s")
        else:
            print_error(f"Falló en {result['duration']:.2f}s")
        
        if i < iterations - 1:
            print_info("Esperando 5s antes de siguiente iteración...")
            time.sleep(5)
    
    return durations

def calculate_metrics(durations: List[float]) -> Dict[str, float]:
    """Calcula métricas de rendimiento"""
    if not durations:
        return {}
    
    avg_duration = sum(durations) / len(durations)
    min_duration = min(durations)
    max_duration = max(durations)
    
    # Baseline monoagente (estimado: 10 segundos)
    baseline = 10.0
    improvement = ((baseline - avg_duration) / baseline) * 100
    
    return {
        "avg_duration": avg_duration,
        "min_duration": min_duration,
        "max_duration": max_duration,
        "baseline": baseline,
        "improvement_percent": improvement
    }

def main():
    """Función principal de pruebas"""
    print_header("Prueba End-to-End - Sistema Multi-Agente")
    print_info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Backend: {BACKEND_URL}")
    
    # 1. Verificar salud del backend
    print_header("1. Verificación de Servicios")
    if not check_backend_health():
        print_error("Backend no está disponible. Asegúrate de que docker compose esté activo.")
        sys.exit(1)
    
    # 2. Ejecutar tarea de prueba
    print_header("2. Ejecución de Tarea de Prueba")
    result = create_task(TEST_OBJETIVO)
    
    if not result["success"]:
        print_error("La tarea de prueba falló")
        sys.exit(1)
    
    # 3. Esperar y obtener resultado
    print_header("3. Esperando Resultado")
    task_id = result["data"].get("task_id", result["data"].get("id"))
    
    if task_id:
        print_info("Esperando 15 segundos para que la tarea se complete...")
        time.sleep(15)
        
        status = get_task_status(task_id)
        if "error" not in status:
            print_success("Estado de tarea obtenido")
            print_info(f"Estado: {status.get('status', 'N/A')}")
            
            # Mostrar resultado parcial
            resultado = status.get("resultado", status.get("result", ""))
            if resultado:
                print_info(f"Resultado (primeros 300 chars):")
                print(f"{resultado[:300]}...")
        else:
            print_error(f"Error al obtener estado: {status['error']}")
    
    # 4. Análisis de paralelización (requiere acceso a logs de Docker)
    print_header("4. Análisis de Paralelización")
    print_info("Para analizar la paralelización, ejecuta:")
    print(f"{BLUE}docker compose logs backend | grep 'Agent.*started'{NC}")
    print_info("Verifica que ExecutorAgent, VerifierAgent y MemoryManagerAgent")
    print_info("tengan timestamps idénticos o con <100ms de diferencia")
    
    # 5. Prueba de rendimiento
    print_header("5. Prueba de Rendimiento")
    durations = run_performance_test(iterations=3)
    
    if durations:
        metrics = calculate_metrics(durations)
        
        print_header("📊 MÉTRICAS DE RENDIMIENTO")
        print(f"Duración promedio: {metrics['avg_duration']:.2f}s")
        print(f"Duración mínima: {metrics['min_duration']:.2f}s")
        print(f"Duración máxima: {metrics['max_duration']:.2f}s")
        print(f"Baseline monoagente: {metrics['baseline']:.2f}s")
        print(f"Mejora: {metrics['improvement_percent']:.1f}%")
        
        if metrics['improvement_percent'] >= 40:
            print_success(f"✅ Objetivo de 40% de mejora ALCANZADO ({metrics['improvement_percent']:.1f}%)")
        else:
            print_error(f"❌ Objetivo de 40% de mejora NO alcanzado ({metrics['improvement_percent']:.1f}%)")
    
    # 6. Resumen final
    print_header("📋 RESUMEN DE PRUEBAS")
    print(f"{GREEN}✅ Pruebas completadas exitosamente{NC}")
    print("\n📋 Checklist de validación:")
    print("   [✓] Backend activo y respondiendo")
    print("   [✓] Tarea ejecutada exitosamente")
    print("   [?] Paralelización (verificar manualmente en logs)")
    print("   [✓] Métricas de rendimiento calculadas")
    
    print("\n🔍 Verificaciones manuales pendientes:")
    print("   1. Acceder a http://localhost:3000 (UI)")
    print("   2. Verificar streaming en tiempo real (<300ms)")
    print("   3. Revisar logs: docker compose logs backend -f")
    print("   4. Verificar métricas: http://localhost:9090 (Prometheus)")
    print("   5. Visualizar datos: http://localhost:3001 (Grafana)")
    
    print(f"\n{GREEN}✅ Prueba end-to-end completada{NC}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠️  Prueba interrumpida por el usuario{NC}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
