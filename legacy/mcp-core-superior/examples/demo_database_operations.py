#!/usr/bin/env python3
"""
Demo Completo del Database Operations Agent MCP
Demuestra todas las funcionalidades disponibles para PostgreSQL + pgvector
"""

import asyncio
import sys
import os
import json
import time
from typing import Dict, Any

# Agregar path del src al PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.database_operations_agent import (
    DatabaseOperationsAgentWrapper,
    DatabaseConnectionConfig,
    DatabaseOperationType
)
from agents.database_helpers import (
    DatabaseHelpers,
    create_database_agent,
    quick_sql_query,
    quick_vector_search,
    quick_health_check
)


class DatabaseOperationsDemo:
    """Demo completo del Database Operations Agent"""
    
    def __init__(self, db_config: DatabaseConnectionConfig):
        self.db_config = db_config
        self.agent = None
        self.helpers = None
    
    async def setup(self):
        """Configurar demo"""
        print("🔧 Configurando Database Operations Agent...")
        
        self.agent = DatabaseOperationsAgentWrapper(self.db_config)
        self.helpers = DatabaseHelpers(self.agent)
        
        # Inicializar agente
        await self.agent.ensure_initialized()
        
        print("✅ Agent configurado y conectado")
    
    async def demo_basic_operations(self):
        """Demo de operaciones básicas"""
        print("\n" + "="*60)
        print("📊 DEMO: Operaciones Básicas")
        print("="*60)
        
        # 1. Health Check
        print("\n1️⃣ Health Check Completo")
        health_result = await self.agent.process_request({
            "operation_type": "monitoring",
            "monitor_type": "health"
        })
        
        if health_result.get("success"):
            print("✅ Base de datos saludable")
            print(f"   - Tiempo de respuesta: {health_result.get('response_time_ms', 0):.2f}ms")
            print(f"   - Tamaño BD: {health_result.get('database_size', 0) / (1024*1024):.2f} MB")
        else:
            print(f"❌ Error de salud: {health_result.get('error', 'Unknown')}")
        
        # 2. SQL Query simple
        print("\n2️⃣ Ejecución de Consulta SQL")
        sql_result = await self.agent.process_request({
            "operation_type": "sql_query",
            "query": """
            SELECT 
                current_database() as database_name,
                current_user as current_user,
                now() as current_timestamp,
                version() as db_version
            """
        })
        
        if sql_result.get("success"):
            data = sql_result.get('data', [])
            if data:
                row = data[0]
                print("✅ Consulta ejecutada exitosamente")
                print(f"   📋 DB: {row.get('database_name')}")
                print(f"   👤 User: {row.get('current_user')}")
                print(f"   ⏰ Tiempo: {row.get('current_timestamp')}")
                print(f"   💻 Versión: {row.get('db_version', '')[:50]}...")
            print(f"   ⏱️  Tiempo ejecución: {sql_result['execution_time_ms']:.2f}ms")
        else:
            print(f"❌ Error: {sql_result.get('error_message')}")
        
        # 3. Información del sistema
        print("\n3️⃣ Información del Sistema")
        stats = await self.helpers.get_database_statistics()
        
        if stats:
            print("✅ Estadísticas del sistema:")
            print(f"   💾 Tamaño BD: {self.helpers._format_bytes(stats.get('database_size', 0))}")
            print(f"   📊 Tablas: {stats.get('table_count', 0)}")
            print(f"   🔗 Conexiones activas: {stats.get('active_connections', 0)}")
            print(f"   ⚡ Cache hit ratio: {stats.get('cache_hit_ratio', 0):.1f}%")
    
    async def demo_schema_management(self):
        """Demo de gestión de esquemas"""
        print("\n" + "="*60)
        print("🏗️  DEMO: Gestión de Esquemas")
        print("="*60)
        
        # 1. Listar tablas
        print("\n1️⃣ Listar Tablas")
        schema_result = await self.agent.process_request({
            "operation_type": "schema_management",
            "schema_operation": "list_tables"
        })
        
        if schema_result.get("success"):
            tables = schema_result.get('tables', [])
            schemas = schema_result.get('schemas', [])
            
            print(f"✅ Esquemas encontrados: {len(schemas)}")
            print(f"✅ Tablas encontradas: {len(tables)}")
            
            # Mostrar primeras tablas
            for i, table in enumerate(tables[:3]):
                print(f"   📊 {i+1}. {table['table_name']}: {len(table['columns'])} columnas")
            
            if len(tables) > 3:
                print(f"   ... y {len(tables) - 3} tablas más")
        else:
            print(f"❌ Error: {schema_result.get('error')}")
        
        # 2. Describir tabla (si existe)
        if schema_result.get("success") and schema_result.get("tables"):
            first_table = schema_result["tables"][0]["table_name"]
            
            print(f"\n2️⃣ Describir Tabla: {first_table}")
            table_result = await self.agent.process_request({
                "operation_type": "schema_management",
                "schema_operation": "describe_table",
                "table_name": first_table
            })
            
            if table_result.get("success"):
                print(f"✅ Estructura de tabla {first_table}:")
                
                columns = table_result.get('columns', [])
                for col in columns[:5]:  # Primeras 5 columnas
                    nullable = "NULL" if col.get('nullable') else "NOT NULL"
                    print(f"   📋 {col['name']} ({col['type']}) {nullable}")
                
                if len(columns) > 5:
                    print(f"   ... y {len(columns) - 5} columnas más")
                
                indexes = table_result.get('indexes', [])
                print(f"   🔍 Índices: {len(indexes)}")
            else:
                print(f"⚠️  No se pudo describir la tabla: {table_result.get('error')}")
    
    async def demo_vector_search(self):
        """Demo de búsqueda vectorial"""
        print("\n" + "="*60)
        print("🔍 DEMO: Búsqueda Vectorial")
        print("="*60)
        
        # Determinar tabla con embeddings
        target_table = "knowledge_base"  # Default, cambiar según tu schema
        
        print(f"\n1️⃣ Buscando en tabla: {target_table}")
        print("   (Esto requiere que la tabla tenga columna 'embedding')")
        
        # Crear embedding de ejemplo
        embedding_size = 1536
        query_embedding = [0.1, 0.2, 0.3] + [0.0] * (embedding_size - 3)
        
        try:
            vector_result = await self.agent.process_request({
                "operation_type": "vector_search",
                "query_embedding": query_embedding,
                "table_name": target_table,
                "limit": 5,
                "threshold": 0.5
            })
            
            if vector_result.get("success"):
                results = vector_result.get('results', [])
                print(f"✅ Búsqueda vectorial completada")
                print(f"   🎯 Resultados encontrados: {len(results)}")
                print(f"   ⏱️  Tiempo: {vector_result['search_time_ms']:.2f}ms")
                print(f"   📊 Threshold: {vector_result['threshold_used']}")
                
                # Mostrar primeros resultados
                for i, result in enumerate(results[:3]):
                    similarity = result.get('similarity', 0)
                    content_preview = result.get('content', '')[:50] + "..."
                    print(f"   {i+1}. Similitud: {similarity:.3f} - {content_preview}")
                
                if len(results) > 3:
                    print(f"   ... y {len(results) - 3} resultados más")
            else:
                print(f"⚠️  Búsqueda vectorial no disponible")
                print(f"   Razón: {vector_result.get('error_message', 'Sin datos vectoriales')}")
                
        except Exception as e:
            print(f"⚠️  Búsqueda vectorial no disponible: {str(e)}")
        
        # Demo de normalización de embedding
        print(f"\n2️⃣ Utilidades de Vector")
        normalized = self.helpers.normalize_embedding(query_embedding)
        print(f"   ✅ Embedding normalizado: {len(normalized)} dimensiones")
        print(f"   📊 Magnitud: {sum(x*x for x in normalized)**0.5:.6f}")
    
    async def demo_performance_monitoring(self):
        """Demo de monitoreo de performance"""
        print("\n" + "="*60)
        print("⚡ DEMO: Monitoreo de Performance")
        print("="*60)
        
        # 1. Performance metrics
        print("\n1️⃣ Métricas de Performance")
        perf_result = await self.agent.process_request({
            "operation_type": "monitoring",
            "monitor_type": "performance"
        })
        
        if perf_result.get("success"):
            metrics = perf_result.get('performance_metrics', {})
            
            print("✅ Métricas de performance:")
            print(f"   🔗 Conexiones activas: {metrics.get('active_connections', 0)}")
            print(f"   💾 Tamaño BD: {metrics.get('database_size_human', 'N/A')}")
            print(f"   📊 Cache hit ratio: {metrics.get('cache_hit_ratio', 0):.1f}%")
            print(f"   📋 Tablas: {metrics.get('table_count', 0)}")
        else:
            print(f"❌ Error obteniendo métricas: {perf_result.get('error')}")
        
        # 2. Connection pool status
        print("\n2️⃣ Estado del Pool de Conexiones")
        pool_result = await self.agent.process_request({
            "operation_type": "connection_pool",
            "pool_operation": "status"
        })
        
        if pool_result.get("success"):
            pool_metrics = pool_result.get('pool_metrics', {})
            
            print("✅ Estado del pool:")
            print(f"   🔗 Total: {pool_metrics.get('total_connections', 0)}")
            print(f"   📤 En uso: {pool_metrics.get('checked_out', 0)}")
            print(f"   📈 Overflow: {pool_metrics.get('overflow', 0)}")
            print(f"   💚 Estado: {pool_result.get('pool_status', 'unknown')}")
            
            # Calcular utilización
            total = pool_metrics.get('total_connections', 0)
            used = pool_metrics.get('checked_out', 0)
            if total > 0:
                utilization = (used / total) * 100
                print(f"   📊 Utilización: {utilization:.1f}%")
        else:
            print(f"❌ Error del pool: {pool_result.get('error')}")
        
        # 3. Index analysis (si está disponible)
        print("\n3️⃣ Análisis de Índices")
        try:
            index_result = await self.agent.process_request({
                "operation_type": "index_management",
                "index_operation": "analyze"
            })
            
            if index_result.get("success"):
                analysis = index_result.get('index_analysis', [])
                unused = index_result.get('unused_indexes', [])
                
                print(f"✅ Índices analizados: {len(analysis)}")
                print(f"⚠️  Índices no utilizados: {len(unused)}")
                
                if unused:
                    print("   Índices recomendados para remover:")
                    for idx in unused[:3]:
                        print(f"   - {idx['schema']}.{idx['table']}.{idx['index_name']}")
            else:
                print(f"⚠️  Análisis no disponible: {index_result.get('error')}")
                
        except Exception as e:
            print(f"⚠️  Análisis de índices no disponible: {str(e)}")
    
    async def demo_backup_operations(self):
        """Demo de operaciones de backup"""
        print("\n" + "="*60)
        print("💾 DEMO: Operaciones de Backup")
        print("="*60)
        
        # 1. Listar backups existentes
        print("\n1️⃣ Listar Backups Existentes")
        list_result = await self.agent.process_request({
            "operation_type": "backup_restore",
            "backup_operation": "list_backups",
            "backup_directory": "./backups"
        })
        
        if list_result.get("success"):
            backups = list_result.get('backups', [])
            
            print(f"✅ Backups encontrados: {len(backups)}")
            
            for backup in backups[:3]:  # Primeros 3
                filename = backup['filename']
                size = backup['size_bytes']
                created = backup['created_timestamp'][:19]  # Formato date
                print(f"   📁 {filename} ({self.helpers._format_bytes(size)}) - {created}")
            
            if len(backups) > 3:
                print(f"   ... y {len(backups) - 3} backups más")
        else:
            print("ℹ️  No hay backups existentes o directorio no encontrado")
        
        # 2. Crear backup (opcional - solo si se solicita)
        print(f"\n2️⃣ Crear Backup")
        print("   ⚠️  Esta operación puede tomar tiempo en bases de datos grandes")
        
        create_demo = input("   ¿Deseas crear un backup de demo? (s/N): ").lower().strip()
        
        if create_demo == 's':
            try:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_path = f"./backups/demo_backup_{timestamp}.sql"
                
                backup_result = await self.agent.process_request({
                    "operation_type": "backup_restore",
                    "backup_operation": "backup",
                    "backup_path": backup_path
                })
                
                if backup_result.get("success"):
                    print(f"✅ Backup creado exitosamente:")
                    print(f"   📁 Archivo: {backup_result['backup_path']}")
                    print(f"   ⏱️  Tiempo: {backup_result['backup_time_seconds']:.2f}s")
                    print(f"   💾 Tamaño: {self.helpers._format_bytes(backup_result['size_bytes'])}")
                else:
                    print(f"❌ Error creando backup: {backup_result.get('error')}")
                    
            except Exception as e:
                print(f"⚠️  Error creando backup: {str(e)}")
        else:
            print("   ⏭️  Omitiendo creación de backup")
    
    async def demo_agent_metrics(self):
        """Demo de métricas del agente"""
        print("\n" + "="*60)
        print("📈 DEMO: Métricas del Agente")
        print("="*60)
        
        # Estado general del agente
        print("\n1️⃣ Estado del Agente")
        status = self.agent.get_status()
        
        print("✅ Estado actual:")
        print(f"   📊 Estado: {status['status']}")
        print(f"   🔄 Listo: {status['is_ready']}")
        print(f"   💼 Ocupado: {status['is_busy']}")
        print(f"   📈 Utilización: {status['utilization']:.1%}")
        print(f"   ✅ Tasa de éxito: {status['success_rate']:.1%}")
        print(f"   📊 Total operaciones: {status['total_operations']}")
        
        # Métricas específicas
        print("\n2️⃣ Métricas Específicas")
        metrics = status.get('metrics', {})
        query_metrics = metrics.get('capability_usage', {})
        
        print("✅ Uso de capacidades:")
        for capability, count in query_metrics.items():
            print(f"   🔧 {capability}: {count} usos")
        
        # Health check del agente
        print("\n3️⃣ Health Check del Agente")
        health = await self.agent.health_check()
        
        print(f"✅ Salud del agente: {health['status']}")
        print(f"   🗄️  Conexión DB: {health.get('database_connection', 'unknown')}")
        print(f"   💚 Pool status: {health.get('pool_status', 'unknown')}")
        print(f"   ⏱️  Última actividad: {health.get('last_activity', 'unknown')[:19]}")
    
    async def demo_convenience_functions(self):
        """Demo de funciones de conveniencia"""
        print("\n" + "="*60)
        print("⚡ DEMO: Funciones de Conveniencia")
        print("="*60)
        
        print("\n1️⃣ Health Check Rápido")
        try:
            health = await quick_health_check(
                host=self.db_config.host,
                port=self.db_config.port,
                database=self.db_config.database,
                user=self.db_config.user,
                password=self.db_config.password
            )
            print(f"✅ Salud: {health['status']}")
            print(f"   🗄️  Conexión: {health['database_connection']}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n2️⃣ Consulta SQL Rápida")
        try:
            result = await quick_sql_query(
                "SELECT 1 as test, 'Database Operations Agent' as message",
                host=self.db_config.host,
                port=self.db_config.port,
                database=self.db_config.database,
                user=self.db_config.user,
                password=self.db_config.password
            )
            if result.get("success"):
                data = result['data'][0]
                print(f"✅ Resultado: {data['message']} - Valor: {data['test']}")
                print(f"   ⏱️  Tiempo: {result['execution_time_ms']:.2f}ms")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n3️⃣ Búsqueda Vectorial Rápida")
        try:
            embedding = [0.1, 0.2] + [0.0] * 1534  # 1536 dimensiones
            
            result = await quick_vector_search(
                query_embedding=embedding,
                table_name="knowledge_base",
                limit=3,
                threshold=0.5,
                host=self.db_config.host,
                port=self.db_config.port,
                database=self.db_config.database,
                user=self.db_config.user,
                password=self.db_config.password
            )
            
            if result.get("success"):
                results = result['results']
                print(f"✅ Búsqueda completada: {len(results)} resultados")
                print(f"   ⏱️  Tiempo: {result['search_time_ms']:.2f}ms")
            else:
                print(f"⚠️  Búsqueda no disponible: {result.get('error_message')}")
                
        except Exception as e:
            print(f"⚠️  Búsqueda no disponible: {str(e)}")
    
    async def run_complete_demo(self):
        """Ejecutar demo completo"""
        print("🚀 DATABASE OPERATIONS AGENT - DEMO COMPLETO")
        print("="*80)
        print(f"📋 Configuración:")
        print(f"   🏠 Host: {self.db_config.host}")
        print(f"   🔌 Puerto: {self.db_config.port}")
        print(f"   🗄️  Base de datos: {self.db_config.database}")
        print(f"   👤 Usuario: {self.db_config.user}")
        print(f"   🔗 Pool size: {self.db_config.pool_size}")
        
        try:
            # Setup
            await self.setup()
            
            # Ejecutar demos
            await self.demo_basic_operations()
            await self.demo_schema_management()
            await self.demo_vector_search()
            await self.demo_performance_monitoring()
            await self.demo_backup_operations()
            await self.demo_agent_metrics()
            await self.demo_convenience_functions()
            
            print("\n" + "="*80)
            print("🎉 DEMO COMPLETADO EXITOSAMENTE")
            print("="*80)
            print("\n📚 Recursos adicionales:")
            print("   📖 Documentación: docs/database_operations_agent.md")
            print("   🧪 Tests: tests/test_database_operations_agent.py")
            print("   🔧 Helpers: agents/database_helpers.py")
            print("   📝 Ejemplos: examples/database_operations_example.py")
            
        except Exception as e:
            print(f"\n❌ Error durante el demo: {str(e)}")
            print("\n🔧 Verificar:")
            print("   - PostgreSQL está ejecutándose")
            print("   - Credenciales de base de datos son correctas")
            print("   - Extensión pgvector está instalada")
            print("   - Dependencias están instaladas")
        
        finally:
            # Cleanup
            if self.agent and self.agent.engine:
                self.agent.engine.dispose()
                print("\n🧹 Recursos limpiados")


async def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Demo del Database Operations Agent")
    parser.add_argument("--host", default="localhost", help="Host de PostgreSQL")
    parser.add_argument("--port", type=int, default=5432, help="Puerto de PostgreSQL")
    parser.add_argument("--database", default="rag_database", help="Nombre de base de datos")
    parser.add_argument("--user", default="postgres", help="Usuario de PostgreSQL")
    parser.add_argument("--password", default="password", help="Password de PostgreSQL")
    parser.add_argument("--pool-size", type=int, default=10, help="Tamaño del pool")
    
    args = parser.parse_args()
    
    # Configurar desde variables de entorno si están disponibles
    host = os.getenv("DB_HOST", args.host)
    port = int(os.getenv("DB_PORT", args.port))
    database = os.getenv("DB_NAME", args.database)
    user = os.getenv("DB_USER", args.user)
    password = os.getenv("DB_PASSWORD", args.password)
    
    # Configuración de base de datos
    db_config = DatabaseConnectionConfig(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        pool_size=args.pool_size
    )
    
    # Crear y ejecutar demo
    demo = DatabaseOperationsDemo(db_config)
    await demo.run_complete_demo()


if __name__ == "__main__":
    # Configurar logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrumpido por el usuario")
    except Exception as e:
        print(f"\n\n💥 Error fatal: {str(e)}")
        sys.exit(1)