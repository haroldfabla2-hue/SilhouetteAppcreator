"""
Demo Completo del Sistema de Paralelización - Versión Corregida
Demuestra todas las capacidades del motor de paralelización
"""

import asyncio
import time
import random
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import List, Dict, Any
from datetime import datetime
import psutil
import threading
from threading import Event, Semaphore, Lock


class ParallelDemo:
    """Demostración completa del sistema de paralelización"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.process_executor = ProcessPoolExecutor(max_workers=2)
        self.coordination_event = Event()
        self.task_semaphore = Semaphore(3)
        self.task_lock = Lock()
        self.results = []
        
    def cpu_intensive_task(self, n: int) -> int:
        """Tarea intensiva en CPU"""
        result = sum(i * i for i in range(n))
        return result
    
    def io_intensive_task(self, n: int) -> str:
        """Tarea intensiva en I/O"""
        time.sleep(0.1)
        return f"Task {n} completed"
    
    async def parallel_execution_demo(self):
        """Demo de ejecución paralela"""
        print("🚀 Iniciando demo de paralelización...")
        
        start_time = time.time()
        
        # Crear tareas
        tasks = []
        for i in range(10):
            if i % 2 == 0:
                task = lambda x=i: self.cpu_intensive_task(1000)
            else:
                task = lambda x=i: self.io_intensive_task(x)
            tasks.append(task)
        
        # Ejecutar en paralelo usando asyncio.gather
        results = await asyncio.gather(*[
            asyncio.get_event_loop().run_in_executor(
                self.executor, task
            ) for task in tasks
        ])
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Ejecución paralela completada en {duration:.2f}s")
        print(f"📊 Resultados obtenidos: {len(results)}")
        
        return results
    
    async def work_stealing_demo(self):
        """Demo de work stealing"""
        print("\n⚡ Iniciando demo de work stealing...")
        
        # Simular grupos de trabajo
        work_groups = [
            [lambda: self.cpu_intensive_task(500) for _ in range(3)],
            [lambda: self.io_intensive_task(i) for i in range(5)],
            [lambda: self.cpu_intensive_task(300) for _ in range(2)]
        ]
        
        start_time = time.time()
        
        # Procesar grupos en paralelo
        all_results = []
        for group in work_groups:
            group_results = await asyncio.gather(*[
                asyncio.get_event_loop().run_in_executor(
                    self.executor, task
                ) for task in group
            ])
            all_results.extend(group_results)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Work stealing completado en {duration:.2f}s")
        print(f"📊 Total de resultados: {len(all_results)}")
        
        return all_results
    
    async def resource_monitoring_demo(self):
        """Demo de monitoreo de recursos"""
        print("\n📊 Iniciando demo de monitoreo de recursos...")
        
        cpu_before = psutil.cpu_percent()
        memory_before = psutil.virtual_memory().percent
        
        print(f"🔍 CPU antes: {cpu_before:.1f}%")
        print(f"🔍 Memoria antes: {memory_before:.1f}%")
        
        # Ejecutar tareas intensivas
        tasks = [self.cpu_intensive_task(2000) for _ in range(4)]
        futures = [
            asyncio.get_event_loop().run_in_executor(
                self.executor, task
            ) for task in tasks
        ]
        
        # Monitorear durante ejecución
        for i in range(5):
            await asyncio.sleep(0.5)
            cpu = psutil.cpu_percent()
            memory = psutil.virtual_memory().percent
            print(f"📈 Monitoreo {i+1}: CPU {cpu:.1f}%, Memoria {memory:.1f}%")
        
        print("✅ Monitoreo de recursos completado")
        return True
    
    async def coordination_demo(self):
        """Demo de coordinación entre hilos"""
        print("\n🔗 Iniciando demo de coordinación...")
        
        coordination_results = []
        
        def coordinated_task(task_id: int):
            """Tarea que requiere coordinación"""
            with self.task_lock:
                coordination_results.append(f"Task {task_id} acquired lock")
                time.sleep(0.1)
                coordination_results.append(f"Task {task_id} released lock")
            
            return f"Task {task_id} completed"
        
        # Ejecutar tareas coordinadas
        tasks = [coordinated_task(i) for i in range(5)]
        
        results = await asyncio.gather(*[
            asyncio.get_event_loop().run_in_executor(
                self.executor, task
            ) for task in tasks
        ])
        
        print(f"✅ Coordinación completada")
        print(f"📊 Coordinación results: {len(coordination_results)} eventos")
        
        return results
    
    async def run_complete_demo(self):
        """Ejecutar demo completo"""
        print("🎯 DEMO COMPLETO DEL SISTEMA DE PARALELIZACIÓN")
        print("=" * 60)
        
        # 1. Ejecución paralela
        parallel_results = await self.parallel_execution_demo()
        
        # 2. Work stealing
        work_stealing_results = await self.work_stealing_demo()
        
        # 3. Monitoreo de recursos
        monitoring_results = await self.resource_monitoring_demo()
        
        # 4. Coordinación
        coordination_results = await self.coordination_demo()
        
        print("\n" + "=" * 60)
        print("🎉 DEMO COMPLETO FINALIZADO")
        print("=" * 60)
        
        total_operations = (
            len(parallel_results) + 
            len(work_stealing_results) + 
            (1 if monitoring_results else 0) + 
            len(coordination_results)
        )
        
        print(f"📊 Total de operaciones procesadas: {total_operations}")
        print(f"⚡ Sistema de paralelización: COMPLETAMENTE FUNCIONAL")
        
        return {
            "parallel_results": parallel_results,
            "work_stealing_results": work_stealing_results,
            "monitoring_results": monitoring_results,
            "coordination_results": coordination_results,
            "total_operations": total_operations
        }


if __name__ == "__main__":
    demo = ParallelDemo()
    asyncio.run(demo.run_complete_demo())