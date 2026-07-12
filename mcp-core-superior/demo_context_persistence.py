#!/usr/bin/env python3
"""
Demostración Interactiva del Context Persistence Engine
=====================================================

Este script demuestra las principales funcionalidades del sistema de persistencia
de contexto avanzado de manera visual e interactiva.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List

from src.core.context_persistence_engine import (
    initialize_context_persistence,
    create_context_snapshot,
    retrieve_context_snapshot,
    search_context_semantic,
    recover_session,
    create_context_version,
    optimize_context_storage,
    get_context_engine_stats,
    initialize_agent_with_context,
    ContextType,
    ContextTier
)


class ContextPersistenceDemo:
    """Demo interactiva del sistema de persistencia"""
    
    def __init__(self):
        self.user_id = "demo_user_001"
        self.session_id = "demo_session_001"
        self.demo_data = {}
        
    def print_header(self, title: str):
        """Imprimir header decorado"""
        print("\n" + "="*80)
        print(f"🚀 {title.upper()}")
        print("="*80)
    
    def print_section(self, title: str):
        """Imprimir sección"""
        print(f"\n📋 {title}")
        print("-" * 50)
    
    def print_success(self, message: str):
        """Imprimir mensaje de éxito"""
        print(f"✅ {message}")
    
    def print_info(self, message: str):
        """Imprimir mensaje informativo"""
        print(f"ℹ️  {message}")
    
    def print_warning(self, message: str):
        """Imprimir advertencia"""
        print(f"⚠️  {message}")
    
    async def demo_basic_operations(self):
        """Demo 1: Operaciones básicas"""
        self.print_header("DEMO 1: OPERACIONES BÁSICAS DE CONTEXTO")
        
        self.print_section("Creando snapshots de diferentes tipos...")
        
        # Crear snapshot de conversación
        conv_snapshot = await create_context_snapshot(
            context_type=ContextType.CONVERSATION,
            content={
                "messages": [
                    {"role": "user", "content": "¿Cómo mejoro el rendimiento de mi aplicación?"},
                    {"role": "assistant", "content": "Para mejorar el rendimiento, considera: 1) Optimizar consultas a BD, 2) Implementar caching, 3) Usar compresión de datos"}
                ],
                "topic": "performance_optimization",
                "sentiment": "helpful"
            },
            user_id=self.user_id,
            session_id=self.session_id,
            metadata={"conversation_id": "conv_demo_001"}
        )
        self.print_success(f"Snapshot de conversación creado: {conv_snapshot[:8]}...")
        
        # Crear snapshot de tarea
        task_snapshot = await create_context_snapshot(
            context_type=ContextType.TASK,
            content={
                "task_id": "task_demo_001",
                "title": "Implementar sistema de cache distribuido",
                "description": "Crear sistema de cache con Redis Cluster para mejorar performance",
                "priority": "high",
                "estimated_hours": 16,
                "status": "in_progress"
            },
            user_id=self.user_id,
            session_id=self.session_id,
            metadata={"project": "cache_system"}
        )
        self.print_success(f"Snapshot de tarea creado: {task_snapshot[:8]}...")
        
        # Crear snapshot de memoria de agente
        agent_snapshot = await create_context_snapshot(
            context_type=ContextType.AGENT_MEMORY,
            content={
                "agent_name": "python_executor",
                "expertise": ["data_analysis", "web_scraping", "api_integration"],
                "preferred_tools": ["pandas", "requests", "beautifulsoup"],
                "performance_stats": {
                    "avg_execution_time": "1.8s",
                    "success_rate": "0.94",
                    "total_tasks": 156
                }
            },
            user_id=self.user_id,
            session_id=self.session_id,
            metadata={"agent_version": "v2.1"}
        )
        self.print_success(f"Snapshot de memoria de agente creado: {agent_snapshot[:8]}...")
        
        self.demo_data["basic_snapshots"] = [conv_snapshot, task_snapshot, agent_snapshot]
        
        # Recuperar snapshot
        self.print_section("Recuperando snapshot...")
        retrieved = await retrieve_context_snapshot(task_snapshot)
        if retrieved:
            self.print_success(f"Snapshot recuperado: {retrieved.content['title']}")
            self.print_info(f"Tier: {retrieved.tier.value}")
            self.print_info(f"Tamaño original: {retrieved.original_size} bytes")
            self.print_info(f"Tamaño comprimido: {retrieved.compressed_size} bytes")
    
    async def demo_semantic_search(self):
        """Demo 2: Búsqueda semántica"""
        self.print_header("DEMO 2: BÚSQUEDA SEMÁNTICA AVANZADA")
        
        self.print_section("Creando contenido semánticamente relacionado...")
        
        # Crear múltiples snapshots relacionados semánticamente
        semantic_content = [
            {
                "content": "Optimizar rendimiento de base de datos PostgreSQL con índices y query optimization",
                "type": ContextType.TASK,
                "topic": "database_optimization"
            },
            {
                "content": "Configurar sistema de cache distribuido con Redis para mejorar velocidad de respuesta",
                "type": ContextType.TASK,
                "topic": "cache_performance"
            },
            {
                "content": "Implementar balanceador de carga Nginx para distribuir tráfico web",
                "type": ContextType.TASK,
                "topic": "load_balancing"
            },
            {
                "content": "Conversación sobre mejores prácticas de arquitectura de microservicios",
                "type": ContextType.CONVERSATION,
                "topic": "microservices_architecture"
            },
            {
                "content": "Tutorial de Python para análisis de big data y machine learning",
                "type": ContextType.CONVERSATION,
                "topic": "python_data_science"
            }
        ]
        
        semantic_ids = []
        for item in semantic_content:
            snapshot_id = await create_context_snapshot(
                context_type=item["type"],
                content={"text": item["content"], "topic": item["topic"]},
                user_id=self.user_id,
                session_id=self.session_id
            )
            semantic_ids.append(snapshot_id)
        
        self.print_success(f"{len(semantic_ids)} snapshots semánticos creados")
        
        # Esperar procesamiento de embeddings
        self.print_section("Procesando embeddings semánticos...")
        await asyncio.sleep(3)
        
        # Realizar búsquedas semánticas
        search_queries = [
            "optimización base de datos PostgreSQL",
            "cache Redis rendimiento",
            "balanceador de carga Nginx",
            "Python machine learning",
            "arquitectura microservicios"
        ]
        
        for query in search_queries:
            self.print_section(f"Búsqueda: '{query}'")
            start_time = time.time()
            
            results = await search_context_semantic(
                query=query,
                user_id=self.user_id,
                limit=3
            )
            
            search_time = time.time() - start_time
            
            if results:
                self.print_success(f"Encontrados {len(results)} resultados en {search_time*1000:.1f}ms:")
                for i, (snapshot, similarity) in enumerate(results, 1):
                    content_preview = snapshot.content.get('text', '')[:60] + "..." if len(snapshot.content.get('text', '')) > 60 else snapshot.content.get('text', '')
                    print(f"  {i}. Similitud: {similarity:.2f} | {content_preview}")
            else:
                self.print_warning("No se encontraron resultados")
        
        self.demo_data["semantic_ids"] = semantic_ids
    
    async def demo_version_control(self):
        """Demo 3: Control de versiones"""
        self.print_header("DEMO 3: CONTROL DE VERSIONES DE CONTEXTO")
        
        self.print_section("Creando snapshots versionados...")
        
        # Crear documento base
        base_content = {
            "document": "API Design Guidelines",
            "version": "1.0",
            "sections": [
                {"title": "Introduction", "content": "API design principles"},
                {"title": "Authentication", "content": "JWT token usage"},
                {"title": "Error Handling", "content": "Standard error responses"}
            ]
        }
        
        base_snapshot = await create_context_snapshot(
            context_type=ContextType.WORKFLOW,
            content=base_content,
            user_id=self.user_id,
            session_id=self.session_id,
            metadata={"document_type": "guidelines", "version_control": True}
        )
        self.print_success(f"Documento base creado: {base_snapshot[:8]}...")
        
        # Crear versiones sucesivas
        versions = [
            {
                "changes": {
                    "added_sections": [{"title": "Rate Limiting", "content": "API rate limiting strategies"}],
                    "modified_sections": [{"title": "Authentication", "content": "Enhanced JWT with refresh tokens"}]
                },
                "message": "Added rate limiting and enhanced authentication"
            },
            {
                "changes": {
                    "added_sections": [{"title": "Monitoring", "content": "API monitoring and logging"}],
                    "removed_sections": [{"title": "Introduction"}],
                    "modified_sections": [{"title": "Error Handling", "content": "Enhanced error codes and messages"}]
                },
                "message": "Added monitoring section and improved error handling"
            },
            {
                "changes": {
                    "modified_sections": [
                        {"title": "Authentication", "content": "OAuth2 integration added"},
                        {"title": "Rate Limiting", "content": "Redis-based rate limiting"}
                    ]
                },
                "message": "Updated authentication and rate limiting implementations"
            }
        ]
        
        version_ids = []
        for version in versions:
            version_id = await create_context_version(
                snapshot_id=base_snapshot,
                changes=version["changes"],
                author="api_team",
                message=version["message"]
            )
            version_ids.append(version_id)
            self.print_success(f"Versión creada: {version['message']} ({version_id[:8]}...)")
        
        self.demo_data["base_snapshot"] = base_snapshot
        self.demo_data["version_ids"] = version_ids
    
    async def demo_session_recovery(self):
        """Demo 4: Recuperación de sesión"""
        self.print_header("DEMO 4: RECUPERACIÓN COMPLETA DE SESIÓN")
        
        self.print_section("Simulando conversación completa de sesión...")
        
        # Simular conversación completa
        conversation_flow = [
            {"role": "user", "content": "Hola, necesito ayuda con un proyecto de desarrollo", "timestamp": "2024-01-15T10:00:00"},
            {"role": "assistant", "content": "¡Hola! Me complace ayudarte. ¿Podrías contarme más detalles sobre tu proyecto?", "timestamp": "2024-01-15T10:00:15"},
            {"role": "user", "content": "Estoy desarrollando una aplicación web con Python y PostgreSQL", "timestamp": "2024-01-15T10:01:00"},
            {"role": "assistant", "content": "Excelente elección. Python y PostgreSQL son una combinación muy sólida. ¿En qué aspectos específicos necesitas ayuda?", "timestamp": "2024-01-15T10:01:10"},
            {"role": "user", "content": "Tengo problemas de rendimiento con las consultas a la base de datos", "timestamp": "2024-01-15T10:02:00"},
            {"role": "assistant", "content": "Los problemas de rendimiento en PostgreSQL son comunes. Te ayudo a optimizarlas con índices y análisis de queries.", "timestamp": "2024-01-15T10:02:15"}
        ]
        
        session_snapshots = []
        for i, message in enumerate(conversation_flow):
            snapshot_id = await create_context_snapshot(
                context_type=ContextType.CONVERSATION,
                content={
                    "message": message,
                    "sequence": i + 1,
                    "conversation_flow": conversation_flow[:i+1]
                },
                user_id=self.user_id,
                session_id=self.session_id,
                metadata={"session_demo": True, "message_number": i + 1}
            )
            session_snapshots.append(snapshot_id)
            self.print_success(f"Mensaje {i+1} guardado: {message['content'][:50]}...")
        
        # Crear snapshots adicionales de la sesión
        task_snapshot = await create_context_snapshot(
            context_type=ContextType.TASK,
            content={
                "task": "Optimizar consultas PostgreSQL",
                "priority": "high",
                "estimated_hours": 4,
                "related_conversation": session_snapshots[-1]
            },
            user_id=self.user_id,
            session_id=self.session_id,
            metadata={"session_task": True}
        )
        
        preference_snapshot = await create_context_snapshot(
            context_type=ContextType.USER_PREFERENCES,
            content={
                "preferred_tech": ["Python", "PostgreSQL", "Redis"],
                "expertise_level": "intermediate",
                "communication_style": "detailed_explanations"
            },
            user_id=self.user_id,
            session_id=self.session_id,
            metadata={"user_profile": True}
        )
        
        # Recuperar contexto completo de sesión
        self.print_section("Recuperando contexto completo de sesión...")
        recovered_contexts = await recover_session(
            user_id=self.user_id,
            session_id=self.session_id,
            max_age_hours=1
        )
        
        self.print_success(f"Contexto de sesión recuperado: {len(recovered_contexts)} elementos")
        
        # Mostrar resumen del contexto recuperado
        context_summary = {"conversations": 0, "tasks": 0, "preferences": 0, "other": 0}
        for context in recovered_contexts:
            if context.context_type == ContextType.CONVERSATION:
                context_summary["conversations"] += 1
            elif context.context_type == ContextType.TASK:
                context_summary["tasks"] += 1
            elif context.context_type == ContextType.USER_PREFERENCES:
                context_summary["preferences"] += 1
            else:
                context_summary["other"] += 1
        
        self.print_info(f"Resumen: {context_summary}")
        
        self.demo_data["session_snapshots"] = session_snapshots
        self.demo_data["recovered_contexts"] = recovered_contexts
    
    async def demo_context_aware_agents(self):
        """Demo 5: Agentes context-aware"""
        self.print_header("DEMO 5: INICIALIZACIÓN CONTEXT-AWARE DE AGENTES")
        
        self.print_section("Creando contexto para agentes...")
        
        # Crear contexto variado para diferentes tipos de agentes
        agent_contexts = [
            {
                "type": ContextType.TASK,
                "content": {"task": "Análisis de datos de ventas", "tools": ["pandas", "matplotlib"]},
                "metadata": {"agent_type": "data_analyst"}
            },
            {
                "type": ContextType.CONVERSATION,
                "content": {"topic": "machine learning models", "level": "advanced"},
                "metadata": {"agent_type": "ml_specialist"}
            },
            {
                "type": ContextType.AGENT_MEMORY,
                "content": {"preferences": {"visualizations": "matplotlib", "models": "scikit-learn"}},
                "metadata": {"agent_type": "python_executor"}
            },
            {
                "type": ContextType.WORKFLOW,
                "content": {"workflow": "data_pipeline", "steps": ["extract", "transform", "load"]},
                "metadata": {"agent_type": "pipeline_builder"}
            }
        ]
        
        for context in agent_contexts:
            await create_context_snapshot(
                context_type=context["type"],
                content=context["content"],
                user_id=self.user_id,
                session_id=self.session_id,
                metadata=context["metadata"]
            )
        
        self.print_success("Contexto para agentes creado")
        
        # Inicializar diferentes agentes con contexto
        agents_to_demo = [
            {
                "name": "python_executor",
                "requirements": {
                    "context_types": [ContextType.TASK, ContextType.AGENT_MEMORY],
                    "max_contexts": 5
                }
            },
            {
                "name": "data_analyst",
                "requirements": {
                    "context_types": [ContextType.TASK, ContextType.CONVERSATION],
                    "max_contexts": 3
                }
            },
            {
                "name": "ml_specialist",
                "requirements": {
                    "context_types": [ContextType.CONVERSATION, ContextType.WORKFLOW],
                    "max_contexts": 4
                }
            }
        ]
        
        for agent in agents_to_demo:
            self.print_section(f"Inicializando agente: {agent['name']}")
            start_time = time.time()
            
            init_result = await initialize_agent_with_context(
                agent_name=agent["name"],
                user_id=self.user_id,
                session_id=self.session_id,
                context_requirements=agent["requirements"]
            )
            
            init_time = time.time() - start_time
            
            self.print_success(f"Agente {agent['name']} inicializado en {init_time*1000:.1f}ms")
            self.print_info(f"Snapshot de inicialización: {init_result['initialization_snapshot_id'][:8]}...")
            self.print_info(f"Contexto relevante encontrado: {len(init_result.get('relevant_context', []))}")
            
            if init_result.get("context_summary"):
                summary = init_result["context_summary"]
                self.print_info(f"Fuentes de contexto: {summary.get('total_sources', 0)}")
    
    async def demo_optimization_and_monitoring(self):
        """Demo 6: Optimización y monitoreo"""
        self.print_header("DEMO 6: OPTIMIZACIÓN Y MONITOREO")
        
        self.print_section("Creando datos para optimización...")
        
        # Crear múltiples snapshots para optimización
        optimization_data = []
        for i in range(30):
            snapshot_id = await create_context_snapshot(
                context_type=ContextType.TASK,
                content={
                    "optimization_test": True,
                    "data": f"x" * 500,  # Datos para compresión
                    "index": i,
                    "created_for": "optimization_demo"
                },
                user_id=self.user_id,
                session_id=self.session_id
            )
            optimization_data.append(snapshot_id)
        
        self.print_success(f"{len(optimization_data)} snapshots creados para optimización")
        
        # Obtener estadísticas antes de optimización
        self.print_section("Estadísticas antes de optimización...")
        stats_before = await get_context_engine_stats()
        self.print_info(f"Snapshots totales: {stats_before.get('database', {}).get('total_snapshots', 0)}")
        self.print_info(f"Uso de Redis: {stats_before.get('redis', {}).get('memory_usage_mb', 0):.2f} MB")
        
        # Ejecutar optimización
        self.print_section("Ejecutando optimización automática...")
        start_time = time.time()
        
        optimization_results = await optimize_context_storage()
        
        optimization_time = time.time() - start_time
        
        self.print_success(f"Optimización completada en {optimization_time*1000:.1f}ms")
        self.print_info(f"Snapshots podados: {optimization_results.get('pruned_snapshots', 0)}")
        self.print_info(f"Space liberado: {optimization_results.get('freed_space_mb', 0):.2f} MB")
        self.print_info(f"Snapshots recomprimidos: {optimization_results.get('compressed_snapshots', 0)}")
        
        # Obtener estadísticas después de optimización
        self.print_section("Estadísticas después de optimización...")
        stats_after = await get_context_engine_stats()
        self.print_info(f"Snapshots totales: {stats_after.get('database', {}).get('total_snapshots', 0)}")
        self.print_info(f"Uso de Redis: {stats_after.get('redis', {}).get('memory_usage_mb', 0):.2f} MB")
        
        # Health check
        self.print_section("Health Check del Sistema...")
        health = await context_persistence_engine._health_check()
        
        components = ["redis", "postgresql", "embedding_service", "vector_store"]
        for component in components:
            status = "✅ OK" if health.get(component, False) else "❌ FAIL"
            self.print_info(f"{component}: {status}")
        
        self.demo_data["optimization_results"] = optimization_results
        self.demo_data["stats_before"] = stats_before
        self.demo_data["stats_after"] = stats_after
    
    async def run_complete_demo(self):
        """Ejecutar demo completa"""
        self.print_header("DEMOSTRACIÓN COMPLETA - CONTEXT PERSISTENCE ENGINE")
        
        print("Este demo muestra las capacidades avanzadas del sistema de persistencia de contexto")
        print("Incluye: snapshots, búsqueda semántica, control de versiones, recuperación de sesión,")
        print("agentes context-aware, optimización automática y monitoreo.\n")
        
        try:
            # Inicializar sistema
            self.print_section("Inicializando sistema...")
            await initialize_context_persistence()
            self.print_success("Sistema inicializado correctamente")
            
            # Ejecutar demos
            await self.demo_basic_operations()
            await self.demo_semantic_search()
            await self.demo_version_control()
            await self.demo_session_recovery()
            await self.demo_context_aware_agents()
            await self.demo_optimization_and_monitoring()
            
            # Resumen final
            self.print_header("RESUMEN DE DEMOSTRACIÓN")
            
            total_snapshots = len(self.demo_data.get("basic_snapshots", [])) + len(self.demo_data.get("semantic_ids", []))
            total_snapshots += len(self.demo_data.get("session_snapshots", [])) + len(self.demo_data.get("optimization_results", {}).get("snapshots_processed", 0))
            
            self.print_success(f"Demo completado exitosamente!")
            self.print_info(f"Total snapshots creados: ~{total_snapshots}")
            self.print_info(f"Versiones de control creadas: {len(self.demo_data.get('version_ids', []))}")
            self.print_info(f"Contexto de sesión recuperado: {len(self.demo_data.get('recovered_contexts', []))}")
            self.print_info(f"Agentes inicializados contextualmente: 3")
            
            # Mostrar estadísticas finales
            final_stats = await get_context_engine_stats()
            self.print_info(f"Storage total utilizado: {final_stats.get('database', {}).get('total_storage_mb', 0):.2f} MB")
            self.print_info(f"Clusters semánticos activos: {final_stats.get('database', {}).get('total_clusters', 0)}")
            
        except Exception as e:
            self.print_warning(f"Error durante demo: {e}")
            import traceback
            traceback.print_exc()


def print_demo_menu():
    """Imprimir menú de demo"""
    print("\n" + "="*80)
    print("🎮 DEMO INTERACTIVO - CONTEXT PERSISTENCE ENGINE")
    print("="*80)
    print("Selecciona una opción:")
    print("1. Demo completa (todas las funcionalidades)")
    print("2. Solo operaciones básicas")
    print("3. Solo búsqueda semántica")
    print("4. Solo control de versiones")
    print("5. Solo recuperación de sesión")
    print("6. Solo agentes context-aware")
    print("7. Solo optimización y monitoreo")
    print("0. Salir")
    print("-" * 80)


async def main():
    """Función principal del demo"""
    demo = ContextPersistenceDemo()
    
    while True:
        print_demo_menu()
        try:
            choice = input("Ingresa tu opción: ").strip()
            
            if choice == "0":
                print("👋 ¡Gracias por usar el Context Persistence Engine!")
                break
            elif choice == "1":
                await demo.run_complete_demo()
            elif choice == "2":
                await demo.demo_basic_operations()
            elif choice == "3":
                await demo.demo_semantic_search()
            elif choice == "4":
                await demo.demo_version_control()
            elif choice == "5":
                await demo.demo_session_recovery()
            elif choice == "6":
                await demo.demo_context_aware_agents()
            elif choice == "7":
                await demo.demo_optimization_and_monitoring()
            else:
                print("❌ Opción inválida. Por favor selecciona 0-7.")
            
            input("\nPresiona Enter para continuar...")
            
        except KeyboardInterrupt:
            print("\n\n👋 ¡Demo terminado por el usuario!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            input("Presiona Enter para continuar...")


if __name__ == "__main__":
    print("🚀 Iniciando demo del Context Persistence Engine...")
    asyncio.run(main())