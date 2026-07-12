"""
Ejemplos de uso del PythonExecutorAgent con Sandbox Avanzado
Demuestra casos de uso prácticos y configuraciones avanzadas
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


class PythonExecutorExamples:
    """Ejemplos prácticos de uso del PythonExecutorAgent"""
    
    def __init__(self):
        self.agent = None
    
    async def setup(self, security_level: SecurityLevel = SecurityLevel.RESTRICTED):
        """Inicializar el agente"""
        print(f"🚀 Inicializando agente con seguridad {security_level.value}...")
        
        self.agent = AdvancedPythonExecutorAgent(
            security_level=security_level,
            default_resource_limits=ResourceLimits(
                max_memory_mb=512,
                max_cpu_seconds=15,
                timeout_seconds=30
            )
        )
        
        await self.agent.ensure_initialized()
        print("✅ Agente inicializado")
    
    async def example_1_basic_calculation(self):
        """Ejemplo 1: Cálculo básico seguro"""
        print("\n📊 Ejemplo 1: Cálculos matemáticos básicos")
        print("-" * 50)
        
        code = """
# Cálculos matemáticos seguros
import math

def calcular_estadisticas(numeros):
    \"\"\"Calcular estadísticas básicas\"\"\"
    if not numeros:
        return {}
    
    return {
        'media': sum(numeros) / len(numeros),
        'mediana': sorted(numeros)[len(numeros)//2],
        'desviacion_estandar': math.sqrt(sum((x - sum(numeros)/len(numeros))**2 for x in numeros) / len(numeros)),
        'maximo': max(numeros),
        'minimo': min(numeros)
    }

# Datos de ejemplo
datos = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
estadisticas = calcular_estadisticas(datos)

print("Estadísticas de los datos:")
for clave, valor in estadisticas.items():
    print(f"  {clave}: {valor:.2f}")
        """
        
        request = {
            "operation": "execute_code",
            "code": code,
            "security_level": "restricted"
        }
        
        result = await self.agent.process_request(request)
        print(f"✅ Ejecutado en {result['execution_result']['execution_time']:.3f}s")
        print(f"Output:\n{result['execution_result']['output']}")
    
    async def example_2_data_processing(self):
        """Ejemplo 2: Procesamiento de datos estructurados"""
        print("\n📋 Ejemplo 2: Procesamiento de datos estructurados")
        print("-" * 50)
        
        code = """
import json
from collections import Counter

def analizar_productos(productos):
    \"\"\"Analizar lista de productos\"\"\"
    if not productos:
        return {"error": "No hay productos"}
    
    # Análisis por categoría
    categorias = Counter(p.get('categoria', 'sin_categoria') for p in productos)
    
    # Análisis de precios
    precios = [p.get('precio', 0) for p in productos if isinstance(p.get('precio'), (int, float))]
    
    # Estadísticas de precios
    if precios:
        stats_precio = {
            'precio_promedio': sum(precios) / len(precios),
            'precio_maximo': max(precios),
            'precio_minimo': min(precios),
            'total_productos': len(precios)
        }
    else:
        stats_precio = {"error": "No hay precios válidos"}
    
    return {
        'total_productos': len(productos),
        'categorias': dict(categorias),
        'estadisticas_precio': stats_precio
    }

# Datos de ejemplo
productos_ejemplo = [
    {'id': 1, 'nombre': 'Laptop', 'categoria': 'Electrónicos', 'precio': 1200},
    {'id': 2, 'nombre': 'Mouse', 'categoria': 'Electrónicos', 'precio': 25},
    {'id': 3, 'nombre': 'Escritorio', 'categoria': 'Muebles', 'precio': 350},
    {'id': 4, 'nombre': 'Silla', 'categoria': 'Muebles', 'precio': 150},
    {'id': 5, 'nombre': 'Monitor', 'categoria': 'Electrónicos', 'precio': 400}
]

# Procesar datos
resultado = analizar_productos(productos_ejemplo)

print("Análisis de productos:")
print(json.dumps(resultado, indent=2, ensure_ascii=False))
        """
        
        request = {
            "operation": "execute_code",
            "code": code,
            "security_level": "restricted",
            "enable_profiling": True
        }
        
        result = await self.agent.process_request(request)
        print(f"✅ Ejecutado en {result['execution_result']['execution_time']:.3f}s")
        
        if result['execution_result']['profile_data']:
            profile = result['execution_result']['profile_data']
            print(f"📊 Profiling: {profile['total_functions']} funciones analizadas")
    
    async def example_3_algorithm_testing(self):
        """Ejemplo 3: Testing de algoritmos"""
        print("\n🧪 Ejemplo 3: Testing de algoritmos con validación")
        print("-" * 50)
        
        code = """
def busqueda_binaria(lista, objetivo):
    \"\"\"Implementación de búsqueda binaria\"\"\"
    if not lista:
        return -1
    
    izquierda, derecha = 0, len(lista) - 1
    
    while izquierda <= derecha:
        medio = (izquierda + derecha) // 2
        valor_medio = lista[medio]
        
        if valor_medio == objetivo:
            return medio
        elif valor_medio < objetivo:
            izquierda = medio + 1
        else:
            derecha = medio - 1
    
    return -1

def ordenamiento_burbuja(lista):
    \"\"\"Implementación de ordenamiento de burbuja\"\"\"
    n = len(lista)
    for i in range(n):
        for j in range(0, n - i - 1):
            if lista[j] > lista[j + 1]:
                lista[j], lista[j + 1] = lista[j + 1], lista[j]
    return lista

# Tests automáticos
def ejecutar_tests():
    resultados = []
    
    # Test 1: Búsqueda binaria
    lista_ordenada = [1, 3, 5, 7, 9, 11, 13, 15]
    
    # Caso exitoso
    indice = busqueda_binaria(lista_ordenada, 7)
    resultados.append(("Búsqueda binaria (encontrado)", indice == 3))
    
    # Caso no encontrado
    indice = busqueda_binaria(lista_ordenada, 8)
    resultados.append(("Búsqueda binaria (no encontrado)", indice == -1))
    
    # Test 2: Ordenamiento
    lista_desordenada = [64, 34, 25, 12, 22, 11, 90]
    lista_ordenada = ordenamiento_burbuja(lista_desordenada.copy())
    esperada = [11, 12, 22, 25, 34, 64, 90]
    resultados.append(("Ordenamiento burbuja", lista_ordenada == esperada))
    
    # Mostrar resultados
    print("Resultados de tests:")
    for test, resultado in resultados:
        status = "✅ PASS" if resultado else "❌ FAIL"
        print(f"  {status} {test}")
    
    return all(resultado for _, resultado in resultados)

# Ejecutar tests
todos_pass = ejecutar_tests()
print(f"\n🎯 Resultado general: {'Todos los tests pasaron' if todos_pass else 'Algunos tests fallaron'}")
        """
        
        request = {
            "operation": "run_tests",
            "code": code,
            "test_type": "comprehensive"
        }
        
        result = await self.agent.process_request(request)
        print(f"✅ Tests ejecutados")
        
        summary = result['summary']
        print(f"📊 Resumen: {summary['passed']}/{summary['total_tests']} tests pasados")
        
        for test_result in result['test_results']:
            status = "✅" if test_result['success'] else "❌"
            print(f"   {status} {test_result['test_name']}")
    
    async def example_4_security_analysis(self):
        """Ejemplo 4: Análisis de seguridad de código"""
        print("\n🔍 Ejemplo 4: Análisis de seguridad avanzado")
        print("-" * 50)
        
        # Código con algunos problemas potenciales
        code_with_issues = """
import json
import re

def procesar_datos_usuario(datos_json):
    \"\"\"Procesar datos de usuario desde JSON\"\"\"
    try:
        datos = json.loads(datos_json)
    except json.JSONDecodeError:
        return {"error": "JSON inválido"}
    
    # Validación básica
    if not isinstance(datos, dict):
        return {"error": "Datos deben ser un objeto"}
    
    # Procesamiento
    resultados = []
    for key, value in datos.items():
        # Limpiar entrada
        if isinstance(value, str):
            # Remover caracteres peligrosos
            valor_limpio = re.sub(r'[<>\"\\'\\';]', '', value)
            resultados.append(f"{key}: {valor_limpio}")
        else:
            resultados.append(f"{key}: {value}")
    
    return {"procesado": len(resultados), "datos": resultados}

# Ejemplo de uso (esto es seguro)
ejemplo_json = '{"nombre": "Juan", "edad": 30, "ciudad": "Madrid"}'
resultado = procesar_datos_usuario(ejemplo_json)
print("Resultado:", json.dumps(resultado, indent=2, ensure_ascii=False))
        """
        
        request = {
            "operation": "analyze_code",
            "code": code_with_issues,
            "security_level": "strict"
        }
        
        result = await self.agent.process_request(request)
        analysis = result['security_analysis']
        
        print(f"✅ Análisis de seguridad completado")
        print(f"🎯 Puntuación de riesgo: {analysis['risk_score']:.2f}")
        print(f"⚠️ Advertencias de seguridad: {len(analysis['security_warnings'])}")
        
        if analysis['security_warnings']:
            print("📋 Detalles de advertencias:")
            for warning in analysis['security_warnings'][:3]:  # Mostrar primeras 3
                print(f"   • {warning}")
        
        print(f"📊 Métricas de código:")
        for key, value in analysis['complexity_metrics'].items():
            print(f"   • {key}: {value}")
    
    async def example_5_performance_profiling(self):
        """Ejemplo 5: Profiling de performance"""
        print("\n⚡ Ejemplo 5: Profiling de performance")
        print("-" * 50)
        
        code = """
import time
from functools import lru_cache

def fibonacci_recursivo(n):
    \"\"\"Fibonacci recursivo (ineficiente)\"\"\"
    if n <= 1:
        return n
    return fibonacci_recursivo(n-1) + fibonacci_recursivo(n-2)

@lru_cache(maxsize=None)
def fibonacci_memoizado(n):
    \"\"\"Fibonacci con memoización (eficiente)\"\"\"
    if n <= 1:
        return n
    return fibonacci_memoizado(n-1) + fibonacci_memoizado(n-2)

def comparar_algoritmos():
    \"\"\"Comparar performance de dos enfoques\"\"\"
    n = 25
    
    # Fibonacci recursivo
    inicio = time.time()
    resultado1 = fibonacci_recursivo(n)
    tiempo1 = time.time() - inicio
    
    # Fibonacci memoizado
    inicio = time.time()
    resultado2 = fibonacci_memoizado(n)
    tiempo2 = time.time() - inicio
    
    print(f"Fibonacci({n}):")
    print(f"  Recursivo: {resultado1} - {tiempo1:.4f}s")
    print(f"  Memoizado: {resultado2} - {tiempo2:.4f}s")
    print(f"  Speedup: {tiempo1/tiempo2:.2f}x")
    
    return {
        'resultado': resultado1,
        'tiempo_recursivo': tiempo1,
        'tiempo_memoizado': tiempo2,
        'speedup': tiempo1/tiempo2
    }

# Ejecutar comparación
resultado = comparar_algoritmos()
        """
        
        request = {
            "operation": "profile_code",
            "code": code,
            "profile_type": "performance"
        }
        
        result = await self.agent.process_request(request)
        profile_data = result['profile_data']
        
        print(f"✅ Profiling completado")
        
        if profile_data.get('profile_successful'):
            print(f"📊 Funciones analizadas: {profile_data['total_functions']}")
            print(f"⏱️ Tiempo total: {profile_data['total_time']:.3f}s")
            
            if profile_data.get('top_functions'):
                print("🔝 Top 3 funciones más costosas:")
                for i, func in enumerate(profile_data['top_functions'][:3], 1):
                    print(f"   {i}. {func['function'][:50]}... - {func['total_time']:.3f}s")
    
    async def example_6_sandbox_execution(self):
        """Ejemplo 6: Ejecución en sandbox completo"""
        print("\n🔒 Ejemplo 6: Ejecución en sandbox completo")
        print("-" * 50)
        
        code = """
# Código para ejecutar en sandbox completo
import json

def procesamiento_complejo():
    \"\"\"Simular procesamiento complejo de datos\"\"\"
    
    # Simular datos de una API
    datos_api = {
        "usuarios": [
            {"id": 1, "nombre": "Ana", "edad": 25, "ciudad": "Madrid"},
            {"id": 2, "nombre": "Luis", "edad": 30, "ciudad": "Barcelona"},
            {"id": 3, "nombre": "María", "edad": 28, "ciudad": "Valencia"}
        ],
        "productos": [
            {"id": 101, "nombre": "Laptop", "precio": 1200},
            {"id": 102, "nombre": "Mouse", "precio": 25},
            {"id": 103, "nombre": "Teclado", "precio": 75}
        ]
    }
    
    # Análisis de datos
    usuarios_por_ciudad = {}
    for usuario in datos_api["usuarios"]:
        ciudad = usuario["ciudad"]
        usuarios_por_ciudad[ciudad] = usuarios_por_ciudad.get(ciudad, 0) + 1
    
    # Estadísticas de productos
    productos = datos_api["productos"]
    precio_promedio = sum(p["precio"] for p in productos) / len(productos)
    
    resultado = {
        "usuarios_por_ciudad": usuarios_por_ciudad,
        "total_usuarios": len(datos_api["usuarios"]),
        "precio_promedio_productos": round(precio_promedio, 2),
        "total_productos": len(datos_api["productos"])
    }
    
    print("Análisis completado:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    return resultado

# Ejecutar en sandbox
resultado_final = procesamiento_complejo()
        """
        
        request = {
            "operation": "execute_with_sandbox",
            "code": code,
            "sandbox_config": {
                "security_level": "moderate",
                "resource_limits": {
                    "max_memory_mb": 128,
                    "max_cpu_seconds": 8,
                    "timeout_seconds": 20
                }
            }
        }
        
        result = await self.agent.process_request(request)
        sandbox_result = result['sandbox_result']
        isolation = result['isolation_status']
        
        print(f"✅ Ejecución en sandbox completada")
        print(f"🎯 Éxito: {sandbox_result['success']}")
        print(f"⏱️ Tiempo de ejecución: {sandbox_result['execution_time']:.3f}s")
        print(f"💾 Memoria utilizada: {sandbox_result['memory_used']:.2f}MB")
        
        print(f"\n🔒 Estado de aislamiento:")
        print(f"   • Red aislada: {isolation['network_isolated']}")
        print(f"   • Límites de recursos: {isolation['resource_limits_enforced']}")
        print(f"   • Violaciones de seguridad: {isolation['security_violations']}")
    
    async def run_all_examples(self):
        """Ejecutar todos los ejemplos"""
        print("🎓 Ejemplos de PythonExecutorAgent con Sandbox Avanzado")
        print("=" * 70)
        
        # Inicializar agente con seguridad moderada
        await self.setup(SecurityLevel.RESTRICTED)
        
        # Ejecutar ejemplos
        try:
            await self.example_1_basic_calculation()
            await self.example_2_data_processing()
            await self.example_3_algorithm_testing()
            await self.example_4_security_analysis()
            await self.example_5_performance_profiling()
            await self.example_6_sandbox_execution()
            
            print("\n" + "=" * 70)
            print("🎉 Todos los ejemplos ejecutados exitosamente")
            print("\n📋 Resumen de capacidades demostradas:")
            print("   ✅ Ejecución segura de código Python")
            print("   ✅ Análisis de seguridad avanzado")
            print("   ✅ Testing automático de algoritmos")
            print("   ✅ Profiling de performance")
            print("   ✅ Validación de seguridad")
            print("   ✅ Ejecución en sandbox completo")
            print("   ✅ Monitoreo de recursos")
            
        except Exception as e:
            print(f"\n❌ Error en ejemplos: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Función principal para ejecutar ejemplos"""
    examples = PythonExecutorExamples()
    await examples.run_all_examples()


if __name__ == "__main__":
    # Configurar logging
    import logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Ejecutar ejemplos
    asyncio.run(main())