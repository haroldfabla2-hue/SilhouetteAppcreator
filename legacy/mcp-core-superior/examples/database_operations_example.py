#!/usr/bin/env python3
"""
Ejemplo de uso del Database Operations Agent MCP
Demuestra las principales funcionalidades para PostgreSQL + pgvector
"""

import asyncio
import sys
import os
import json
from typing import Dict, Any

# Agregar path del src al PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.database_operations_agent import (
    DatabaseOperationsAgentWrapper,
    DatabaseConnectionConfig,
    DatabaseOperationType
)


async def main():
    """Ejemplo principal de uso del Database Operations Agent"""
    
    print("🚀 Database Operations Agent - Ejemplo de Uso")
    print("=" * 60)
    
    # Configuración de base de datos (puedes ajustar según tu setup)
    db_config = DatabaseConnectionConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "rag_database"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "password"),
        pool_size=10,
        max_overflow=20
    )
    
    print(f"📋 Configuración de BD: {db_config.host}:{db_config.port}/{db_config.database}")
    
    try:
        # Crear instancia del agente
        agent = DatabaseOperationsAgentWrapper(db_config)
        
        print("\n1️⃣ Inicializando Database Operations Agent...")
        await agent.ensure_initialized()
        print("✅ Agente inicializado correctamente")
        
        # === EJEMPLO 1: Verificar salud de la base de datos ===
        print("\n2️⃣ Verificando salud de la base de datos...")
        health_result = await agent._monitor_database({
            "monitor_type": "health"
        })
        
        if health_result.get("success"):
            print(f"✅ Base de datos saludable")
            print(f"   - Tiempo de respuesta: {health_result['response_time_ms']:.2f}ms")
            print(f"   - Tamaño BD: {health_result.get('database_size', 0) / (1024*1024):.2f} MB")
            print(f"   - Estado del pool: {health_result.get('pool_status')}")
        else:
            print(f"❌ Error de salud: {health_result.get('error')}")
        
        # === EJEMPLO 2: Listar tablas y esquemas ===
        print("\n3️⃣ Listando tablas y esquemas...")
        schema_result = await agent._manage_schema({
            "schema_operation": "list_tables"
        })
        
        if schema_result.get("success"):
            print(f"✅ Esquemas encontrados: {len(schema_result['schemas'])}")
            print(f"✅ Tablas encontradas: {len(schema_result['tables'])}")
            
            for table in schema_result['tables'][:3]:  # Mostrar solo las primeras 3
                print(f"   📊 {table['table_name']}: {len(table['columns'])} columnas")
        else:
            print(f"❌ Error listando esquemas: {schema_result.get('error')}")
        
        # === EJEMPLO 3: Ejecutar consulta SQL simple ===
        print("\n4️⃣ Ejecutando consulta SQL simple...")
        sql_result = await agent._execute_sql_query({
            "query": "SELECT current_database(), current_user, version() as db_version"
        })
        
        if sql_result.get("success"):
            print("✅ Consulta ejecutada exitosamente")
            data = sql_result.get('data', [])
            if data:
                row = data[0]
                print(f"   🗄️  Base de datos: {row.get('current_database')}")
                print(f"   👤 Usuario: {row.get('current_user')}")
                print(f"   📋 Versión: {row.get('db_version', '')[:50]}...")
            print(f"   ⏱️  Tiempo: {sql_result['execution_time_ms']:.2f}ms")
        else:
            print(f"❌ Error en consulta: {sql_result.get('error_message')}")
        
        # === EJEMPLO 4: Búsqueda vectorial (si existe tabla con embeddings) ===
        print("\n5️⃣ Probando búsqueda vectorial...")
        try:
            # Query de ejemplo con embedding simulado
            vector_result = await agent._perform_vector_search({
                "query_embedding": [0.1] * 1536,  # Embedding simulado de 1536 dimensiones
                "table_name": "knowledge_base",  # Cambiar según tu tabla
                "limit": 5,
                "threshold": 0.5
            })
            
            if vector_result.get("success"):
                print(f"✅ Búsqueda vectorial completada")
                print(f"   🔍 Resultados encontrados: {vector_result['total_matches']}")
                print(f"   ⏱️  Tiempo de búsqueda: {vector_result['search_time_ms']:.2f}ms")
                print(f"   🎯 Threshold usado: {vector_result['threshold_used']}")
            else:
                print(f"⚠️  Búsqueda vectorial: {vector_result.get('error_message', 'Sin resultados')}")
                
        except Exception as e:
            print(f"⚠️  Búsqueda vectorial no disponible: {str(e)}")
        
        # === EJEMPLO 5: Monitoreo de performance ===
        print("\n6️⃣ Monitoreando performance...")
        perf_result = await agent._monitor_database({
            "monitor_type": "performance"
        })
        
        if perf_result.get("success"):
            metrics = perf_result.get('performance_metrics', {})
            print(f"✅ Métricas de performance:")
            print(f"   🔗 Conexiones activas: {metrics.get('active_connections', 0)}")
            print(f"   📊 Cache hit ratio: {metrics.get('cache_hit_ratio', 0):.1f}%")
            print(f"   💾 Tamaño BD: {metrics.get('database_size_human', 'N/A')}")
            print(f"   📋 Tablas: {metrics.get('table_count', 0)}")
        else:
            print(f"❌ Error monitoreando performance: {perf_result.get('error')}")
        
        # === EJEMPLO 6: Gestión de índices ===
        print("\n7️⃣ Analizando índices...")
        try:
            index_result = await agent._manage_indexes({
                "index_operation": "analyze"
            })
            
            if index_result.get("success"):
                print(f"✅ Análisis de índices completado")
                analysis = index_result.get('index_analysis', [])
                print(f"   📈 Índices analizados: {len(analysis)}")
                
                unused = index_result.get('unused_indexes', [])
                if unused:
                    print(f"   ⚠️  Índices no utilizados: {len(unused)}")
                    for idx in unused[:3]:  # Mostrar solo los primeros 3
                        print(f"      - {idx['schema']}.{idx['table']}.{idx['index_name']}")
                else:
                    print("   ✅ Todos los índices están siendo utilizados")
            else:
                print(f"⚠️  Análisis de índices: {index_result.get('error', 'No disponible')}")
                
        except Exception as e:
            print(f"⚠️  Gestión de índices no disponible: {str(e)}")
        
        # === EJEMPLO 7: Estado del pool de conexiones ===
        print("\n8️⃣ Verificando pool de conexiones...")
        pool_result = await agent._manage_pool({
            "pool_operation": "status"
        })
        
        if pool_result.get("success"):
            pool_metrics = pool_result.get('pool_metrics', {})
            print(f"✅ Estado del pool:")
            print(f"   🔗 Total conexiones: {pool_metrics.get('total_connections', 0)}")
            print(f"   📤 En uso: {pool_metrics.get('checked_out', 0)}")
            print(f"   📈 Overflow: {pool_metrics.get('overflow', 0)}")
            print(f"   💚 Estado: {pool_result.get('pool_status', 'unknown')}")
        else:
            print(f"❌ Error verificando pool: {pool_result.get('error')}")
        
        # === MÉTRICAS FINALES DEL AGENTE ===
        print("\n9️⃣ Métricas del agente...")
        status = agent.get_status()
        print(f"✅ Estado del agente:")
        print(f"   📊 Estado: {status['status']}")
        print(f"   📈 Utilización: {status['utilization']:.1%}")
        print(f"   ✅ Tasa de éxito: {status['success_rate']:.1%}")
        print(f"   ⏱️  Respuesta promedio: {status['metrics'].get('response_times', [0])[0] if status['metrics'].get('response_times') else 0:.3f}s")
        
        print("\n🎉 Ejemplo completado exitosamente!")
        print("\n💡 Próximos pasos:")
        print("   - Configurar variables de entorno de base de datos")
        print("   - Probar con tu propia base de datos PostgreSQL + pgvector")
        print("   - Experimentar con diferentes operaciones")
        print("   - Revisar logs para más detalles")
        
    except Exception as e:
        print(f"\n❌ Error durante la ejecución: {str(e)}")
        print("\n🔧 Posibles soluciones:")
        print("   - Verificar que PostgreSQL esté ejecutándose")
        print("   - Confirmar credenciales de base de datos")
        print("   - Instalar dependencias: pip install psycopg2-binary sqlalchemy pgvector")
        print("   - Verificar que la extensión pgvector esté instalada en PostgreSQL")


async def test_specific_operations():
    """Test específico de operaciones críticas"""
    
    print("\n🧪 Test de Operaciones Específicas")
    print("=" * 40)
    
    db_config = DatabaseConnectionConfig()
    agent = DatabaseOperationsAgentWrapper(db_config)
    
    try:
        await agent.ensure_initialized()
        
        # Test de consultas simples
        test_queries = [
            "SELECT 1 as test_value",
            "SELECT current_timestamp as now",
            "SELECT version()"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\nTest {i}: {query[:30]}...")
            
            result = await agent._execute_sql_query({
                "query": query
            })
            
            if result.get("success"):
                print(f"✅ Exitoso en {result['execution_time_ms']:.2f}ms")
            else:
                print(f"❌ Falló: {result.get('error_message')}")
        
        # Test de monitoreo
        print("\nTest de monitoreo...")
        monitor_result = await agent._monitor_database({"monitor_type": "health"})
        print(f"✅ Monitoreo: {monitor_result.get('health_status', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Error en tests: {str(e)}")


if __name__ == "__main__":
    print("Iniciando ejemplo de Database Operations Agent...\n")
    
    # Configurar logging básico
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # Ejecutar ejemplo principal
        asyncio.run(main())
        
        # Ejecutar tests adicionales si se especifica
        if len(sys.argv) > 1 and sys.argv[1] == "--test":
            asyncio.run(test_specific_operations())
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Ejecución interrumpida por el usuario")
    except Exception as e:
        print(f"\n\n💥 Error fatal: {str(e)}")
        sys.exit(1)