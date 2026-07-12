"""
Tests y ejemplos para PythonExecutorAgent con Sandbox Avanzado
Demuestra todas las capacidades implementadas
"""
import asyncio
import sys
import os
from typing import Dict, Any

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.agents.python_executor_agent import (
    AdvancedPythonExecutorAgent,
    SecurityLevel,
    ResourceLimits
)


class PythonExecutorAgentTester:
    """Tester para demostrar capacidades del PythonExecutorAgent"""
    
    def __init__(self):
        self.agent = None
    
    async def setup(self):
        """Inicializar el agente"""
        print("🚀 Inicializando PythonExecutorAgent...")
        
        self.agent = AdvancedPythonExecutorAgent(
            security_level=SecurityLevel.RESTRICTED,
            default_resource_limits=ResourceLimits(
                max_memory_mb=256,
                max_cpu_seconds=10,
                timeout_seconds=30
            )
        )
        
        await self.agent.ensure_initialized()
        print("✅ Agente inicializado correctamente")
    
    async def test_basic_execution(self):
        """Test de ejecución básica"""
        print("\n📝 Test 1: Ejecución básica de código")
        
        code = """
# Código simple y seguro
result = []
for i in range(5):
    result.append(i * 2)

print("Resultado:", result)
sum_result = sum(result)
print("Suma:", sum_result)
        """
        
        request = {
            "operation": "execute_code",
            "code": code,
            "security_level": "restricted",
            "enable_profiling": False
        }
        
        try:
            result = await self.agent.process_request(request)
            print("✅ Código ejecutado exitosamente")
            print(f"   Output: {result['execution_result']['output'][:100]}...")
            print(f"   Tiempo: {result['execution_result']['execution_time']:.3f}s")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def test_security_analysis(self):
        """Test de análisis de seguridad"""
        print("\n🔍 Test 2: Análisis de seguridad")
        
        # Código potencialmente peligroso
        dangerous_code = """
import os
import subprocess

def execute_command():
    # Esto debería ser detectado como peligroso
    result = os.system("ls -la")
    return result

# Llamada peligrosa
execute_command()
        """
        
        request = {
            "operation": "analyze_code",
            "code": dangerous_code,
            "security_level": "restricted"
        }
        
        try:
            result = await self.agent.process_request(request)
            analysis = result['security_analysis']
            print("✅ Análisis completado")
            print(f"   Nivel de riesgo: {analysis['risk_score']:.2f}")
            print(f"   Advertencias: {len(analysis['security_warnings'])}")
            if analysis['security_warnings']:
                print(f"   Detalles: {analysis['security_warnings'][:3]}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def test_automatic_tests(self):
        """Test de testing automático"""
        print("\n🧪 Test 3: Testing automático")
        
        code_with_function = """
def calcular_area_rectangulo(largo, ancho):
    \"\"\"Calcula el área de un rectángulo\"\"\"
    if largo < 0 or ancho < 0:
        raise ValueError("Las dimensiones deben ser positivas")
    return largo * ancho

def suma_lista(numeros):
    \"\"\"Suma una lista de números\"\"\"
    total = 0
    for num in numeros:
        total += num
    return total

# Tests básicos
area = calcular_area_rectangulo(5, 3)
print("Área:", area)

numeros = [1, 2, 3, 4, 5]
total = suma_lista(numeros)
print("Suma:", total)
        """
        
        request = {
            "operation": "run_tests",
            "code": code_with_function,
            "test_type": "basic"
        }
        
        try:
            result = await self.agent.process_request(request)
            test_results = result['test_results']
            summary = result['summary']
            
            print("✅ Tests ejecutados")
            print(f"   Tests pasados: {summary['passed']}/{summary['total_tests']}")
            
            for test in test_results:
                status = "✅" if test['success'] else "❌"
                print(f"   {status} {test['test_name']}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def test_profiling(self):
        """Test de profiling"""
        print("\n⚡ Test 4: Profiling de performance")
        
        # Código que consume tiempo
        profiling_code = """
import time

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def procesar_datos():
    \"\"\"Simular procesamiento pesado\"\"\"
    datos = []
    for i in range(1000):
        datos.append(fibonacci(20))
    
    # Procesamiento adicional
    total = sum(datos)
    print(f"Procesamiento completado. Total: {total}")
    return total

# Ejecutar
resultado = procesar_datos()
        """
        
        request = {
            "operation": "profile_code",
            "code": profiling_code,
            "profile_type": "performance"
        }
        
        try:
            result = await self.agent.process_request(request)
            profile_data = result['profile_data']
            
            print("✅ Profiling completado")
            if profile_data.get('profile_successful'):
                print(f"   Funciones analizadas: {profile_data['total_functions']}")
                print(f"   Tiempo total: {profile_data['total_time']:.3f}s")
                
                if profile_data.get('top_functions'):
                    print("   Top función:")
                    top_func = profile_data['top_functions'][0]
                    print(f"     {top_func['function']}: {top_func['total_time']:.3f}s")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def test_security_validation(self):
        """Test de validación de seguridad"""
        print("\n🛡️ Test 5: Validación de seguridad")
        
        safe_code = """
def procesar_datos(lista):
    \"\"\"Procesa una lista de datos de forma segura\"\"\"
    resultado = []
    
    for item in lista:
        if isinstance(item, (int, float)):
            resultado.append(item * 2)
        else:
            print(f"Ignorando item inválido: {item}")
    
    return resultado

# Ejecutar
datos = [1, 2, 3, 4, 5]
resultado = procesar_datos(datos)
print("Resultado:", resultado)
        """
        
        request = {
            "operation": "validate_security",
            "code": safe_code,
            "strict_mode": False
        }
        
        try:
            result = await self.agent.process_request(request)
            validation = result
            
            print("✅ Validación de seguridad completada")
            print(f"   Validación pasada: {validation['validation_passed']}")
            print(f"   Puntuación de seguridad: {validation['security_score']:.2f}")
            
            details = validation['validation_details']
            for check, passed in details.items():
                status = "✅" if passed else "❌"
                print(f"   {status} {check}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def test_sandbox_execution(self):
        """Test de ejecución en sandbox"""
        print("\n🔒 Test 6: Ejecución en sandbox")
        
        sandbox_code = """
import json

def analizar_datos():
    \"\"\"Analizar datos en sandbox completo\"\"\"
    datos = {
        "numeros": [1, 2, 3, 4, 5],
        "texto": "Datos de prueba",
        "operaciones": {
            "suma": sum([1, 2, 3, 4, 5]),
            "promedio": sum([1, 2, 3, 4, 5]) / 5
        }
    }
    
    print("Datos procesados:")
    print(json.dumps(datos, indent=2))
    
    return datos

# Ejecutar en sandbox
resultado = analizar_datos()
        """
        
        request = {
            "operation": "execute_with_sandbox",
            "code": sandbox_code,
            "sandbox_config": {
                "security_level": "moderate",
                "resource_limits": {
                    "max_memory_mb": 128,
                    "max_cpu_seconds": 5,
                    "timeout_seconds": 15
                }
            }
        }
        
        try:
            result = await self.agent.process_request(request)
            sandbox_result = result['sandbox_result']
            isolation = result['isolation_status']
            
            print("✅ Ejecución en sandbox completada")
            print(f"   Éxito: {sandbox_result['success']}")
            print(f"   Tiempo: {sandbox_result['execution_time']:.3f}s")
            print(f"   Memoria: {sandbox_result['memory_used']:.2f}MB")
            print(f"   Red aislada: {isolation['network_isolated']}")
            print(f"   Violaciones: {isolation['security_violations']}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def test_status_monitoring(self):
        """Test de monitoreo de estado"""
        print("\n📊 Test 7: Monitoreo de estado")
        
        # Obtener estado del agente
        status = self.agent.get_status()
        
        print("✅ Estado del agente:")
        print(f"   Tipo: {status['agent_type']}")
        print(f"   Estado: {status['status']}")
        print(f"   Listo: {status['is_ready']}")
        print(f"   Utilización: {status['utilization']:.2%}")
        print(f"   Nivel de seguridad: {status['security_level']}")
        print(f"   Aislamiento de red: {status['network_isolation_enabled']}")
        
        # Métricas de ejecución
        metrics = status['execution_metrics']
        print("\n📈 Métricas de ejecución:")
        print(f"   Total ejecuciones: {metrics['total_executions']}")
        print(f"   Exitosas: {metrics['successful_executions']}")
        print(f"   Fallidas: {metrics['failed_executions']}")
        print(f"   Violaciones de seguridad: {metrics['security_violations']}")
        print(f"   Tiempo promedio: {metrics['average_execution_time']:.3f}s")
        print(f"   Memoria promedio: {metrics['average_memory_usage']:.2f}MB")
    
    async def run_all_tests(self):
        """Ejecutar todos los tests"""
        print("🧪 Iniciando suite completa de tests para PythonExecutorAgent")
        print("=" * 60)
        
        try:
            await self.setup()
            
            # Ejecutar todos los tests
            await self.test_basic_execution()
            await self.test_security_analysis()
            await self.test_automatic_tests()
            await self.test_profiling()
            await self.test_security_validation()
            await self.test_sandbox_execution()
            await self.test_status_monitoring()
            
            print("\n" + "=" * 60)
            print("🎉 Suite de tests completada exitosamente")
            
        except Exception as e:
            print(f"\n❌ Error general en tests: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Función principal para ejecutar tests"""
    tester = PythonExecutorAgentTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    # Configurar logging básico
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Ejecutar tests
    asyncio.run(main())