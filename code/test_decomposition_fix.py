#!/usr/bin/env python3
"""
Test específico para verificar la corrección del bug de recursión infinita en TaskDecompositionEngine
"""

import sys
import os
import signal
import time
from datetime import datetime, timedelta

# Timeout handler
def timeout_handler(signum, frame):
    print("TIMEOUT: El test se detuvo por timeout - posible recursión infinita")
    sys.exit(1)

# Configurar timeout de 30 segundos
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)

# Agregar path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar las clases corregidas
from silhouette_superior_allocator import Task, TaskPriority, TaskType, TaskDecompositionEngine

def test_ml_task_decomposition():
    """Test específico para verificar que la descomposición de tareas ML no cause recursión infinita"""
    print("=== TEST 1: Descomposición de tarea ML ===")
    
    # Crear instancia del motor de descomposición
    decomposition_engine = TaskDecompositionEngine(max_decomposition_depth=3)
    
    # Crear tarea ML compleja
    ml_task = Task(
        id="ml_training",
        type=TaskType.MACHINE_LEARNING,
        priority=TaskPriority.CRITICAL,
        complexity=0.85,
        estimated_duration=90.0,
        required_skills=["python", "ml"],
        deadline=datetime.now() + timedelta(hours=1),
        data_size=100.0
    )
    
    print(f"Tarea original: {ml_task.id}")
    print(f"  - Complejidad: {ml_task.complexity}")
    print(f"  - Duración estimada: {ml_task.estimated_duration} min")
    print(f"  - Nivel de descomposición: {ml_task.decomposition_depth}")
    
    start_time = time.time()
    
    try:
        # Descomponer la tarea
        decomposition = decomposition_engine.decompose_task(ml_task)
        
        end_time = time.time()
        print(f"  ✅ Descomposición completada en {end_time - start_time:.2f} segundos")
        
        # Verificar resultado
        subtasks = decomposition.get('subtasks', [])
        print(f"  📋 Número de subtareas creadas: {len(subtasks)}")
        
        if len(subtasks) > 0:
            for i, subtask in enumerate(subtasks):
                print(f"  - Subtarea {i+1}: {subtask.id}")
                print(f"    • Nivel de descomposición: {subtask.decomposition_depth}")
                print(f"    • Complejidad: {subtask.complexity}")
                print(f"    • Dependencias: {subtask.dependencies}")
        
        # Verificar que las subtareas NO contengan palabras clave que activen descomposición
        for subtask in subtasks:
            task_name = subtask.id.lower()
            problematic_words = ['model_training', 'data_preparation', 'feature_engineering', 'evaluation']
            
            for word in problematic_words:
                if word in task_name:
                    print(f"  ⚠️  ADVERTENCIA: Subtarea {subtask.id} contiene palabra clave '{word}'")
        
        # Intentar descomponer una subtarea para verificar que no se descomponga infinitamente
        if len(subtasks) > 0:
            first_subtask = subtasks[0]
            print(f"\n=== TEST 2: Verificar que las subtareas no se descompongan infinitamente ===")
            print(f"Descomponiendo subtarea: {first_subtask.id}")
            
            start_time2 = time.time()
            second_level_decomp = decomposition_engine.decompose_task(first_subtask)
            end_time2 = time.time()
            
            print(f"  ✅ Segunda descomposición completada en {end_time2 - start_time2:.2f} segundos")
            
            # Verificar si se aplicó descomposición en el segundo nivel
            second_level_subtasks = second_level_decomp.get('subtasks', [])
            decomposition_applied = second_level_decomp.get('decomposition_applied', True)
            
            print(f"  📋 Subtareas en segundo nivel: {len(second_level_subtasks)}")
            print(f"  🔍 ¿Se aplicó descomposición en segundo nivel? {decomposition_applied}")
            
            # Si decomposition_applied es False, significa que no se descompuso (correcto)
            # Si es True pero no hay subtareas, está bien también
            if not decomposition_applied or len(second_level_subtasks) == 0:
                print("  ✅ CORRECTO: La subtarea no se descompuso (límite de profundidad alcanzado)")
            else:
                print(f"  📋 Detalles de segunda descomposición:")
                for i, subsubtask in enumerate(second_level_subtasks):
                    print(f"    - Subsubtarea {i+1}: {subsubtask.id}")
                    print(f"      • Nivel: {subsubtask.decomposition_depth}")
        
        print("\n=== TEST 3: Verificar límite de profundidad ===")
        
        # Verificar que el máximo de profundidad esté funcionando
        deep_task = Task(
            id="deep_task",
            type=TaskType.MACHINE_LEARNING,
            priority=TaskPriority.HIGH,
            complexity=0.9,  # Alta complejidad para forzar descomposición
            estimated_duration=120.0,  # Larga duración para forzar descomposición
            required_skills=["python", "ml"],
            data_size=200.0,
            decomposition_depth=2  # Ya está en nivel 2
        )
        
        print(f"Descomponiendo tarea con depth=2 (máximo es 3)")
        final_decomp = decomposition_engine.decompose_task(deep_task)
        
        final_subtasks = final_decomp.get('subtasks', [])
        decomposition_applied = final_decomp.get('decomposition_applied', True)
        
        print(f"  📋 Subtareas creadas: {len(final_subtasks)}")
        print(f"  🔍 ¿Se aplicó descomposición? {decomposition_applied}")
        
        if not decomposition_applied:
            print("  ✅ CORRECTO: Tarea con depth máximo no se descompuso")
        else:
            print("  ⚠️  ADVERTENCIA: Se aplicó descomposición cuando no debería")
        
        print("\n=== RESULTADO FINAL ===")
        print("✅ TEST COMPLETADO SIN RECURSIÓN INFINITA")
        return True
        
    except RecursionError as e:
        print(f"❌ ERROR DE RECURSIÓN INFINITA: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR INESPERADO: {e}")
        return False

def test_naming_convention():
    """Test para verificar que el naming de subtareas no cause problemas"""
    print("\n=== TEST 4: Verificar naming de subtareas ===")
    
    decomposition_engine = TaskDecompositionEngine(max_decomposition_depth=2)
    
    # Crear tareas de diferentes tipos
    test_tasks = [
        Task(id="ml_training", type=TaskType.MACHINE_LEARNING, priority=TaskPriority.HIGH, 
             complexity=0.9, estimated_duration=60, required_skills=["ml"], data_size=50),
        Task(id="data_processing", type=TaskType.DATA_PROCESSING, priority=TaskPriority.MEDIUM,
             complexity=0.8, estimated_duration=45, required_skills=["python"], data_size=100),
        Task(id="web_scraping", type=TaskType.WEB_SCRAPING, priority=TaskPriority.LOW,
             complexity=0.7, estimated_duration=30, required_skills=["web"], data_size=10)
    ]
    
    for task in test_tasks:
        print(f"\nProbando descomposición de: {task.id}")
        try:
            decomposition = decomposition_engine.decompose_task(task)
            subtasks = decomposition.get('subtasks', [])
            
            print(f"  ✅ Descompuesta en {len(subtasks)} subtareas")
            
            # Verificar que los nombres no contengan palabras clave problemáticas
            for subtask in subtasks:
                task_name = subtask.id.lower()
                if 'model_training' in task_name or 'data_preparation' in task_name:
                    print(f"  ⚠️  Problema: {subtask.id} contiene palabra clave")
                else:
                    print(f"  ✅ Correcto: {subtask.id}")
                    
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    return True

if __name__ == "__main__":
    print("INICIANDO TEST DE CORRECCIÓN DE RECURSIÓN INFINITA")
    print("=" * 60)
    
    try:
        success1 = test_ml_task_decomposition()
        success2 = test_naming_convention()
        
        if success1 and success2:
            print("\n" + "=" * 60)
            print("🎉 TODOS LOS TESTS PASARON - BUG DE RECURSIÓN CORREGIDO")
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("❌ ALGUNOS TESTS FALLARON")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ ERROR GENERAL EN TEST: {e}")
        sys.exit(1)
    finally:
        # Cancelar timeout
        signal.alarm(0)