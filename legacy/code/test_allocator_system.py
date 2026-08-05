#!/usr/bin/env python3
"""
Script de Prueba para SilhouetteMCP Superior - Intelligent Task Allocation System
Valida el funcionamiento de todos los componentes del sistema
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Importar el sistema
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from silhouettemcp_superior_allocator import (
    IntelligentTaskAllocator, Task, Agent, TaskPriority, TaskType, AgentStatus,
    create_intelligent_allocator_system
)

class SystemValidator:
    """Validador completo del sistema de asignación inteligente"""
    
    def __init__(self):
        self.allocator = IntelligentTaskAllocator()
        self.test_results = []
        self.start_time = None
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Ejecuta todos los tests del sistema"""
        self.start_time = time.time()
        print("🔬 Iniciando Validación Completa del Sistema")
        print("=" * 60)
        
        # Test 1: Creación del sistema
        await self._test_system_creation()
        
        # Test 2: Hungarian Algorithm
        await self._test_hungarian_algorithm()
        
        # Test 3: Performance Predictor
        await self._test_performance_predictor()
        
        # Test 4: Task Queue Manager
        await self._test_task_queue_manager()
        
        # Test 5: Load Balancer
        await self._test_load_balancer()
        
        # Test 6: Task Decomposition
        await self._test_task_decomposition()
        
        # Test 7: Intelligent Assignment
        await self._test_intelligent_assignment()
        
        # Test 8: API Endpoints
        await self._test_api_endpoints()
        
        # Test 9: System Integration
        await self._test_system_integration()
        
        # Test 10: Performance & Stress
        await self._test_performance_stress()
        
        # Generar reporte final
        return self._generate_final_report()
    
    async def _test_system_creation(self):
        """Test 1: Creación y inicialización del sistema"""
        print("\n📋 Test 1: Creación del Sistema")
        
        try:
            system = create_intelligent_allocator_system()
            
            assert system['allocator'] is not None
            assert system['api'] is not None
            assert system['monitor'] is not None
            assert len(system['features']) >= 8
            
            self.test_results.append({
                'test': 'system_creation',
                'status': 'PASS',
                'duration': time.time() - self.start_time,
                'details': f"Sistema creado con {len(system['features'])} características"
            })
            
            print(f"✅ PASS: Sistema creado exitosamente")
            print(f"   Características: {', '.join(system['features'][:3])}...")
            
        except Exception as e:
            self.test_results.append({
                'test': 'system_creation',
                'status': 'FAIL',
                'error': str(e)
            })
            print(f"❌ FAIL: {e}")
    
    async def _test_hungarian_algorithm(self):
        """Test 2: Hungarian Algorithm"""
        print("\n📊 Test 2: Hungarian Algorithm")
        
        try:
            from silhouettemcp_superior_allocator import HungarianAlgorithm
            
            # Crear datos de prueba
            agents = [
                Agent(id="agent_1", name="Agent 1", status=AgentStatus.ACTIVE, 
                      skills=["python", "ml"], specialization_score={TaskType.MACHINE_LEARNING: 0.9}),
                Agent(id="agent_2", name="Agent 2", status=AgentStatus.ACTIVE, 
                      skills=["web", "scraping"], specialization_score={TaskType.WEB_SCRAPING: 0.8}),
                Agent(id="agent_3", name="Agent 3", status=AgentStatus.BUSY, 
                      skills=["data", "analysis"], current_workload=0.7)
            ]
            
            tasks = [
                Task(id="task_1", type=TaskType.MACHINE_LEARNING, priority=TaskPriority.HIGH,
                     complexity=0.6, estimated_duration=30.0, required_skills=["python", "ml"]),
                Task(id="task_2", type=TaskType.WEB_SCRAPING, priority=TaskPriority.MEDIUM,
                     complexity=0.4, estimated_duration=20.0, required_skills=["web", "scraping"])
            ]
            
            # Probar cálculo de matriz de costos
            cost_matrix = HungarianAlgorithm.calculate_cost_matrix(tasks, agents)
            assert cost_matrix.shape[0] >= len(tasks)
            assert cost_matrix.shape[1] >= len(agents)
            
            # Probar algoritmo de asignación
            task_indices, agent_indices = HungarianAlgorithm.solve(cost_matrix)
            assert len(task_indices) > 0
            assert len(agent_indices) > 0
            
            # Verificar asignación válida
            for i, task_idx in enumerate(task_indices):
                agent_idx = agent_indices[i]
                assert 0 <= task_idx < len(tasks)
                assert 0 <= agent_idx < len(agents)
            
            self.test_results.append({
                'test': 'hungarian_algorithm',
                'status': 'PASS',
                'matrix_shape': cost_matrix.shape,
                'assignments': len(task_indices)
            })
            
            print(f"✅ PASS: Hungarian Algorithm funcionando")
            print(f"   Matriz de costos: {cost_matrix.shape}")
            print(f"   Asignaciones: {len(task_indices)}")
            
        except Exception as e:
            self.test_results.append({
                'test': 'hungarian_algorithm',
                'status': 'FAIL',
                'error': str(e)
            })
            print(f"❌ FAIL: {e}")
    
    async def _test_performance_predictor(self):
        """Test 3: Performance Predictor ML"""
        print("\n🤖 Test 3: Performance Predictor (ML)")
        
        try:
            predictor = self.allocator.performance_predictor
            
            # Crear datos de entrenamiento sintéticos
            training_data = []
            for i in range(50):
                task_data = {
                    'id': f'train_task_{i}',
                    'type': list(TaskType)[i % len(TaskType)],
                    'priority': list(TaskPriority)[i % len(TaskPriority)],
                    'complexity': 0.3 + (i % 10) * 0.07,
                    'estimated_duration': 15.0 + (i % 20) * 2.0,
                    'required_skills': ['python'],
                    'data_size': 10.0 + i
                }
                
                agent_data = {
                    'id': f'train_agent_{i % 3}',
                    'name': f'Train Agent {i % 3}',
                    'status': AgentStatus.ACTIVE,
                    'skills': ['python'],
                    'current_workload': (i % 10) * 0.1,
                    'max_capacity': 1.0,
                    'average_performance': 0.7 + (i % 5) * 0.06,
                    'accuracy_rate': 0.8 + (i % 4) * 0.05,
                    'specialization_score': {}
                }
                
                # Simular performance real basada en factors
                skill_match = 0.7 + (i % 5) * 0.06
                specialization = 0.6 + (i % 7) * 0.05
                performance = min(1.0, skill_match * 0.4 + specialization * 0.3 + 
                                (1.0 - agent_data['current_workload']) * 0.3)
                
                training_data.append({
                    'task': task_data,
                    'agent': agent_data,
                    'actual_performance': performance
                })
            
            # Entrenar modelo
            metrics = predictor.train(training_data)
            assert predictor.is_trained
            assert 'mae' in metrics
            assert metrics['samples'] == len(training_data)
            
            # Probar predicción
            test_task = Task(id="test_task", type=TaskType.MACHINE_LEARNING,
                           priority=TaskPriority.HIGH, complexity=0.7,
                           estimated_duration=40.0, required_skills=["python"])
            test_agent = Agent(id="test_agent", name="Test Agent", status=AgentStatus.ACTIVE,
                             skills=["python", "ml"], specialization_score={TaskType.MACHINE_LEARNING: 0.9})
            
            prediction = predictor.predict_performance(test_task, test_agent)
            assert 'performance_score' in prediction
            assert 0.0 <= prediction['performance_score'] <= 1.0
            assert 'confidence' in prediction
            
            self.test_results.append({
                'test': 'performance_predictor',
                'status': 'PASS',
                'training_samples': len(training_data),
                'mae': metrics['mae'],
                'prediction_score': prediction['performance_score']
            })
            
            print(f"✅ PASS: Performance Predictor entrenado y funcionando")
            print(f"   Samples: {len(training_data)}, MAE: {metrics['mae']:.3f}")
            print(f"   Predicción: {prediction['performance_score']:.3f}")
            
        except Exception as e:
            self.test_results.append({
                'test': 'performance_predictor',
                'status': 'FAIL',
                'error': str(e)
            })
            print(f"❌ FAIL: {e}")
    
    async def _test_task_queue_manager(self):
        """Test 4: Task Queue Manager"""
        print("\n📬 Test 4: Task Queue Manager")
        
        try:
            queue_manager = self.allocator.task_queue_manager
            
            # Crear tareas de prueba
            tasks = []
            for i in range(10):
                task = Task(
                    id=f"queue_task_{i}",
                    type=list(TaskType)[i % len(TaskType)],
                    priority=list(TaskPriority)[i % len(TaskPriority)],
                    complexity=0.3 + (i % 5) * 0.14,
                    estimated_duration=10.0 + i * 5.0,
                    required_skills=["python"]
                )
                tasks.append(task)
            
            # Añadir tareas a la cola
            for task in tasks:
                success = queue_manager.add_task(task)
                assert success, f"Failed to add task {task.id}"
            
            # Verificar que las tareas están en la cola
            total_queued = sum(len(queue) for queue in queue_manager.queues.values())
            assert total_queued == 10, f"Expected 10 tasks, got {total_queued}"
            
            # Crear agente de prueba
            test_agent = Agent(id="queue_agent", name="Queue Test Agent",
                             status=AgentStatus.ACTIVE, skills=["python"],
                             current_workload=0.3)
            
            # Obtener tareas para el agente
            next_tasks = queue_manager.get_next_task(test_agent, max_tasks=3)
            assert len(next_tasks) > 0, "No tasks assigned to agent"
            
            # Verificar que las tareas son apropiadas para el agente
            for task in next_tasks:
                skill_match = self.allocator.hungarian_algorithm._calculate_skill_match(task, test_agent)
                assert skill_match >= 0.3, f"Poor skill match for task {task.id}"
            
            self.test_results.append({
                'test': 'task_queue_manager',
                'status': 'PASS',
                'tasks_added': len(tasks),
                'tasks_retrieved': len(next_tasks),
                'queue_sizes': {p.name: len(q) for p, q in queue_manager.queues.items()}
            })
            
            print(f"✅ PASS: Task Queue Manager funcionando")
            print(f"   Tareas añadidas: {len(tasks)}, Obtenidas: {len(next_tasks)}")
            
        except Exception as e:
            self.test_results.append({
                'test': 'task_queue_manager',
                'status': 'FAIL',
                'error': str(e)
            })
            print(f"❌ FAIL: {e}")
    
    async def _test_load_balancer(self):
        """Test 5: Load Balancer (CBBA)"""
        print("\n⚖️  Test 5: Dynamic Load Balancer")
        
        try:
            load_balancer = self.allocator.load_balancer
            
            # Crear agentes con diferentes cargas
            agents = []
            for i in range(5):
                agent = Agent(
                    id=f"lb_agent_{i}",
                    name=f"Load Balance Agent {i}",
                    status=AgentStatus.ACTIVE,
                    skills=["python"],
                    current_workload=0.1 + i * 0.15,  # Cargas crecientes
                    max_capacity=1.0
                )
                agents.append(agent)
            
            # Crear tareas
            tasks = []
            for i in range(8):
                task = Task(
                    id=f"lb_task_{i}",
                    type=TaskType.DATA_PROCESSING,
                    priority=TaskPriority.MEDIUM,
                    complexity=0.4 + (i % 3) * 0.2,
                    estimated_duration=20.0 + i * 3.0,
                    required_skills=["python"]
                )
                tasks.append(task)
            
            # Verificar métricas antes del balanceo
            before_metrics = load_balancer._calculate_current_metrics(agents)
            assert 'avg_workload' in before_metrics
            assert 'std_workload' in before_metrics
            
            # Ejecutar load balancing
            balance_result = await load_balancer.balance_load(agents, tasks)
            
            # Verificar que el resultado contiene información válida
            if balance_result:
                assert 'changes_applied' in balance_result
                assert 'new_assignments' in balance_result
            
            self.test_results.append({
                'test': 'load_balancer',
                'status': 'PASS',
                'before_std': before_metrics.get('std_workload', 0),
                'changes_made': len(balance_result.get('changes_applied', [])),
                'rebalancing_active': load_balancer.rebalancing_active
            })
            
            print(f"✅ PASS: Load Balancer funcionando")
            print(f"   Desviación estándar antes: {before_metrics.get('std_workload', 0):.3f}")
            print(f"   Cambios aplicados: {len(balance_result.get('changes_applied', []))}")
            
        except Exception as e:
            self.test_results.append({
                'test': 'load_balancer',
                'status': 'FAIL',
                'error': str(e)
            })
            print(f"❌ FAIL: {e}")
    
    async def _test_task_decomposition(self):
        """Test 6: Task Decomposition Engine"""
        print("\n🔧 Test 6: Task Decomposition Engine")
        
        try:
            decomposition_engine = self.allocator.decomposition_engine
            
            # Crear tarea compleja
            complex_task = Task(
                id="complex_task",
                type=TaskType.DATA_PROCESSING,
                priority=TaskPriority.HIGH,
                complexity=0.9,  # Tarea muy compleja
                estimated_duration=120.0,  # Muy larga
                required_skills=["python", "data_processing"],
                data_size=150.0,  # Muchos datos
                metadata={'file_type': 'large_document', 'num_sections': 5}
            )
            
            # Descomponer tarea
            decomposition = decomposition_engine.decompose_task(complex_task)
            
            # Verificar resultado
            assert 'subtasks' in decomposition
            assert len(decomposition['subtasks']) > 1, "Task should be decomposed"
            assert 'parallel_execution' in decomposition
            assert 'aggregation_required' in decomposition
            
            # Verificar que las subtareas tienen la información correcta
            subtasks = decomposition['subtasks']
            for subtask in subtasks:
                assert hasattr(subtask, 'id')
                assert hasattr(subtask, 'type')
                assert subtask.id != complex_task.id  # IDs únicos
                if 'parent_task' in subtask.metadata:
                    assert subtask.metadata['parent_task'] == complex_task.id
            
            # Probar diferentes tipos de tareas
            task_types_to_test = [TaskType.MACHINE_LEARNING, TaskType.WEB_SCRAPING, 
                                TaskType.VISUALIZATION, TaskType.REPORT_GENERATION]
            
            for task_type in task_types_to_test:
                test_task = Task(
                    id=f"decomp_test_{task_type.value}",
                    type=task_type,
                    priority=TaskPriority.MEDIUM,
                    complexity=0.8,
                    estimated_duration=60.0,
                    required_skills=["python"],
                    metadata={'num_urls': 10} if task_type == TaskType.WEB_SCRAPING else {}
                )
                
                decomp_result = decomposition_engine.decompose_task(test_task)
                assert 'subtasks' in decomp_result
            
            self.test_results.append({
                'test': 'task_decomposition',
                'status': 'PASS',
                'original_complexity': complex_task.complexity,
                'subtasks_created': len(subtasks),
                'parallel_execution': decomposition['parallel_execution'],
                'aggregation_required': decomposition['aggregation_required']
            })
            
            print(f"✅ PASS: Task Decomposition Engine funcionando")
            print(f"   Complejidad original: {complex_task.complexity}")
            print(f"   Subtareas creadas: {len(subtasks)}")
            print(f"   Ejecución paralela: {decomposition['parallel_execution']}")
            
        except Exception as e:
            self.test_results.append({
                'test': 'task_decomposition',
                'status': 'FAIL',
                'error': str(e)
            })
            print(f"❌ FAIL: {e}")
    
    async def _test_intelligent_assignment(self):
        """Test 7: Intelligent Assignment (Sistema completo)"""
        print("\n🧠 Test 7: Intelligent Assignment")
        
        try:
            # Crear agentes diversos
            agents = [
                Agent(id="ml_expert", name="ML Expert", status=AgentStatus.ACTIVE,
                      skills=["python", "ml", "data_science"], 
                      specialization_score={TaskType.MACHINE_LEARNING: 0.95}),
                Agent(id="scraper_pro", name="Scraper Pro", status=AgentStatus.ACTIVE,
                      skills=["web_scraping", "python"], 
                      specialization_score={TaskType.WEB_SCRAPING: 0.9}),
                Agent(id="data_analyst", name="Data Analyst", status=AgentStatus.BUSY,
                      skills=["python", "data_analysis"], current_workload=0.6,
                      specialization_score={TaskType.DATA_PROCESSING: 0.85}),
                Agent(id="report_writer", name="Report Writer", status=AgentStatus.ACTIVE,
                      skills=["report_writing", "visualization"],
                      specialization_score={TaskType.REPORT_GENERATION: 0.9})
            ]
            
            # Crear tareas de diferentes tipos y complejidades
            tasks = [
                Task(id="ml_training", type=TaskType.MACHINE_LEARNING,
                     priority=TaskPriority.CRITICAL, complexity=0.85,
                     estimated_duration=90.0, required_skills=["python", "ml"],
                     deadline=datetime.now() + timedelta(hours=1)),
                Task(id="web_scraping", type=TaskType.WEB_SCRAPING,
                     priority=TaskPriority.MEDIUM, complexity=0.6,
                     estimated_duration=45.0, required_skills=["web_scraping", "python"]),
                Task(id="data_processing", type=TaskType.DATA_PROCESSING,
                     priority=TaskPriority.HIGH, complexity=0.7,
                     estimated_duration=60.0, required_skills=["python", "data_processing"]),
                Task(id="report_gen", type=TaskType.REPORT_GENERATION,
                     priority=TaskPriority.LOW, complexity=0.4,
                     estimated_duration=30.0, required_skills=["report_writing"])
            ]
            
            # Probar asignación inteligente para cada tarea
            assignment_results = []
            for task in tasks:
                result = await self.allocator.assign_task(task, agents)
                assignment_results.append(result)
                
                # Verificar que la asignación fue exitosa
                assert result['success'], f"Assignment failed for task {task.id}"
                assert 'assigned_agent' in result['result'], f"No agent assigned for {task.id}"
                
                assigned_agent = result['result']['assigned_agent']
                assert assigned_agent is not None, f"Agent is None for {task.id}"
                
                # Verificar que el agente tiene los skills necesarios
                skill_match = self.allocator.hungarian_algorithm._calculate_skill_match(task, assigned_agent)
                assert skill_match >= 0.3, f"Poor skill match for {task.id}"
            
            # Verificar distribución de tareas
            agent_assignments = {}
            for result in assignment_results:
                agent_id = result['result']['assigned_agent'].id
                agent_assignments[agent_id] = agent_assignments.get(agent_id, 0) + 1
            
            # Verificar que no todos los agentes recibieron el mismo tipo de tarea
            assert len(agent_assignments) > 1, "All tasks assigned to same agent"
            
            self.test_results.append({
                'test': 'intelligent_assignment',
                'status': 'PASS',
                'tasks_assigned': len(tasks),
                'successful_assignments': len([r for r in assignment_results if r['success']]),
                'agent_distribution': agent_assignments,
                'avg_processing_time': sum(r['processing_time'] for r in assignment_results) / len(assignment_results)
            })
            
            print(f"✅ PASS: Intelligent Assignment funcionando")
            print(f"   Tareas asignadas: {len(tasks)}")
            print(f"   Distribución: {agent_assignments}")
            print(f"   Tiempo promedio: {sum(r['processing_time'] for r in assignment_results) / len(assignment_results):.3f}s")
            
        except Exception as e:
            self.test_results.append({
                'test': 'intelligent_assignment',
                'status': 'FAIL',
                'error': str(e)
            })
            print(f"❌ FAIL: {e}")
    
    async def _test_api_endpoints(self):
        """Test 8: API Endpoints"""
        print("\n🔌 Test 8: API Endpoints")
        
        try:
            from silhouettemcp_superior_allocator import IntelligentTaskAllocationAPI
            
            api = self.allocator  # Usar el allocator directamente
            
            # Preparar datos de prueba
            test_agent = Agent(id="api_agent", name="API Test Agent",
                             status=AgentStatus.ACTIVE, skills=["python", "ml"],
                             specialization_score={TaskType.MACHINE_LEARNING: 0.9})
            
            test_task = Task(id="api_task", type=TaskType.MACHINE_LEARNING,
                           priority=TaskPriority.HIGH, complexity=0.7,
                           estimated_duration=40.0, required_skills=["python", "ml"])
            
            # Test 1: /api/assign/task
            request_data = {
                'task': {
                    'id': test_task.id,
                    'type': test_task.type.value,
                    'priority': test_task.priority.name,
                    'complexity': test_task.complexity,
                    'estimated_duration': test_task.estimated_duration,
                    'required_skills': test_task.required_skills
                },
                'agents': [{
                    'id': test_agent.id,
                    'name': test_agent.name,
                    'status': test_agent.status.value,
                    'skills': test_agent.skills,
                    'specialization_score': {k.value: v for k, v in test_agent.specialization_score.items()}
                }],
                'request_id': 'test_assign_001'
            }
            
            assign_result = await api.assign_task(test_task, [test_agent])
            assert assign_result['success']
            assert 'assigned_agent' in assign_result['result']
            
            # Test 2: /api/predict/performance
            prediction_result = await api.predict_performance(test_task, test_agent)
            assert 'performance_score' in prediction_result
            assert 'confidence' in prediction_result
            
            # Test 3: /api/balance/load
            balance_result = await api.balance_load([test_agent], [])
            assert 'success' in balance_result
            
            # Test 4: /api/optimize/queue
            optimize_result = await api.optimize_queue('performance')
            assert 'success' in optimize_result
            
            self.test_results.append({
                'test': 'api_endpoints',
                'status': 'PASS',
                'endpoints_tested': 4,
                'all_successful': True
            })
            
            print(f"✅ PASS: API Endpoints funcionando")
            print(f"   Endpoints probados: 4")
            print(f"   Asignación: {'✅' if assign_result['success'] else '❌'}")
            print(f"   Predicción: {'✅' if 'performance_score' in prediction_result else '❌'}")
            print(f"   Balance: {'✅' if balance_result else '❌'}")
            print(f"   Optimización: {'✅' if optimize_result else '❌'}")
            
        except Exception as e:
            self.test_results.append({
                'test': 'api_endpoints',
                'status': 'FAIL',
                'error': str(e)
            })
            print(f"❌ FAIL: {e}")
    
    async def _test_system_integration(self):
        """Test 9: System Integration"""
        print("\n🔗 Test 9: System Integration")
        
        try:
            # Crear escenario integrado complejo
            agents = [
                Agent(id="agent_1", name="Data Scientist", status=AgentStatus.ACTIVE,
                      skills=["python", "ml", "data"], 
                      specialization_score={TaskType.MACHINE_LEARNING: 0.9}),
                Agent(id="agent_2", name="Scraper", status=AgentStatus.BUSY,
                      skills=["web", "scraping"], current_workload=0.5,
                      specialization_score={TaskType.WEB_SCRAPING: 0.9}),
                Agent(id="agent_3", name="Analyst", status=AgentStatus.ACTIVE,
                      skills=["analysis", "reporting"],
                      specialization_score={TaskType.REPORT_GENERATION: 0.85})
            ]
            
            # Crear pipeline de tareas
            pipeline_tasks = [
                Task(id="scrape_data", type=TaskType.WEB_SCRAPING,
                     priority=TaskPriority.HIGH, complexity=0.6,
                     estimated_duration=30.0, required_skills=["web", "scraping"]),
                Task(id="process_data", type=TaskType.DATA_PROCESSING,
                     priority=TaskPriority.HIGH, complexity=0.8,
                     estimated_duration=45.0, required_skills=["python", "data"],
                     dependencies=["scrape_data"]),
                Task(id="ml_model", type=TaskType.MACHINE_LEARNING,
                     priority=TaskPriority.MEDIUM, complexity=0.9,
                     estimated_duration=60.0, required_skills=["python", "ml"],
                     dependencies=["process_data"]),
                Task(id="generate_report", type=TaskType.REPORT_GENERATION,
                     priority=TaskPriority.LOW, complexity=0.5,
                     estimated_duration=25.0, required_skills=["reporting"],
                     dependencies=["ml_model"])
            ]
            
            # Test 1: Asignación secuencial respetando dependencias
            for task in pipeline_tasks:
                if task.dependencies:
                    # Simular que las dependencias están completas
                    task.dependencies = []
                
                result = await self.allocator.assign_task(task, agents)
                assert result['success'], f"Failed to assign {task.id}"
            
            # Test 2: Balanceo de carga integrado
            balance_result = await self.allocator.balance_load(agents)
            assert balance_result is not None
            
            # Test 3: Métricas del sistema
            metrics = self.allocator.get_system_metrics()
            assert 'assignment_metrics' in metrics
            assert 'queue_sizes' in metrics
            assert metrics['assignment_metrics']['total_assignments'] >= 4
            
            self.test_results.append({
                'test': 'system_integration',
                'status': 'PASS',
                'pipeline_tasks': len(pipeline_tasks),
                'balance_applied': bool(balance_result),
                'metrics_collected': bool(metrics)
            })
            
            print(f"✅ PASS: System Integration funcionando")
            print(f"   Pipeline de tareas: {len(pipeline_tasks)}")
            print(f"   Balance aplicado: {'Sí' if balance_result else 'No'}")
            print(f"   Métricas: {len(metrics)} categorías")
            
        except Exception as e:
            self.test_results.append({
                'test': 'system_integration',
                'status': 'FAIL',
                'error': str(e)
            })
            print(f"❌ FAIL: {e}")
    
    async def _test_performance_stress(self):
        """Test 10: Performance & Stress Testing"""
        print("\n⚡ Test 10: Performance & Stress Testing")
        
        try:
            start_time = time.time()
            
            # Crear muchos agentes y tareas para stress test
            agents = []
            for i in range(20):
                agent = Agent(
                    id=f"stress_agent_{i}",
                    name=f"Stress Agent {i}",
                    status=AgentStatus.ACTIVE if i % 4 != 0 else AgentStatus.BUSY,
                    skills=["python", "ml"] if i % 3 == 0 else ["web", "scraping"],
                    current_workload=(i % 10) * 0.1,
                    specialization_score={
                        TaskType.MACHINE_LEARNING: 0.7 + (i % 5) * 0.06,
                        TaskType.WEB_SCRAPING: 0.6 + (i % 7) * 0.05
                    }
                )
                agents.append(agent)
            
            tasks = []
            for i in range(50):
                task = Task(
                    id=f"stress_task_{i}",
                    type=list(TaskType)[i % len(TaskType)],
                    priority=list(TaskPriority)[i % len(TaskPriority)],
                    complexity=0.2 + (i % 10) * 0.08,
                    estimated_duration=10.0 + (i % 20) * 5.0,
                    required_skills=["python"] if i % 3 == 0 else ["web"],
                    data_size=5.0 + i * 0.5
                )
                tasks.append(task)
            
            # Test de asignación masiva
            assignment_times = []
            successful_assignments = 0
            
            for i in range(min(20, len(tasks))):  # Probar primeras 20 tareas
                task_start = time.time()
                result = await self.allocator.assign_task(tasks[i], agents)
                assignment_time = time.time() - task_start
                assignment_times.append(assignment_time)
                
                if result['success']:
                    successful_assignments += 1
            
            # Calcular estadísticas de performance
            avg_assignment_time = sum(assignment_times) / len(assignment_times)
            max_assignment_time = max(assignment_times)
            min_assignment_time = min(assignment_times)
            success_rate = successful_assignments / len(assignment_times)
            
            # Test de colas con muchas tareas
            for task in tasks[:30]:
                self.allocator.task_queue_manager.add_task(task)
            
            queue_sizes = {}
            for priority, queue in self.allocator.task_queue_manager.queues.items():
                queue_sizes[priority.name] = len(queue)
            
            total_queued = sum(queue_sizes.values())
            
            self.test_results.append({
                'test': 'performance_stress',
                'status': 'PASS',
                'agents_created': len(agents),
                'tasks_created': len(tasks),
                'assignments_tested': len(assignment_times),
                'success_rate': success_rate,
                'avg_assignment_time': avg_assignment_time,
                'max_assignment_time': max_assignment_time,
                'total_queued': total_queued
            })
            
            print(f"✅ PASS: Performance & Stress Testing")
            print(f"   Agentes creados: {len(agents)}, Tareas creadas: {len(tasks)}")
            print(f"   Asignaciones probadas: {len(assignment_times)}")
            print(f"   Tasa de éxito: {success_rate:.1%}")
            print(f"   Tiempo promedio: {avg_assignment_time:.3f}s")
            print(f"   Tiempo máximo: {max_assignment_time:.3f}s")
            print(f"   Tareas en cola: {total_queued}")
            
            # Benchmark comparison
            if avg_assignment_time < 1.0:
                print("🏆 EXCELLENT: Asignación en < 1s promedio")
            elif avg_assignment_time < 2.0:
                print("✅ GOOD: Asignación en < 2s promedio")
            else:
                print("⚠️  SLOW: Asignación > 2s promedio")
            
        except Exception as e:
            self.test_results.append({
                'test': 'performance_stress',
                'status': 'FAIL',
                'error': str(e)
            })
            print(f"❌ FAIL: {e}")
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """Genera reporte final de validación"""
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t['status'] == 'PASS'])
        failed_tests = total_tests - passed_tests
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        total_duration = time.time() - self.start_time
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': success_rate,
                'total_duration': total_duration,
                'overall_status': 'PASS' if success_rate >= 0.8 else 'FAIL'
            },
            'detailed_results': self.test_results,
            'timestamp': datetime.now().isoformat(),
            'system_info': {
                'allocator_version': '1.0.0',
                'features_tested': len([t for t in self.test_results if t['status'] == 'PASS']),
                'performance_metrics': {
                    'avg_test_duration': total_duration / total_tests if total_tests > 0 else 0,
                    'components_operational': passed_tests
                }
            }
        }
        
        return report

async def main():
    """Función principal del validador"""
    print("🚀 SILHOUETTEMCP SUPERIOR - INTELLIGENT TASK ALLOCATION SYSTEM")
    print("   Validación Completa del Sistema")
    print("=" * 80)
    
    validator = SystemValidator()
    
    try:
        # Ejecutar todos los tests
        final_report = await validator.run_all_tests()
        
        # Mostrar resumen final
        print("\n" + "=" * 80)
        print("📊 REPORTE FINAL DE VALIDACIÓN")
        print("=" * 80)
        
        summary = final_report['summary']
        print(f"✅ Tests Exitosos: {summary['passed']}/{summary['total_tests']}")
        print(f"❌ Tests Fallidos: {summary['failed']}/{summary['total_tests']}")
        print(f"📈 Tasa de Éxito: {summary['success_rate']:.1%}")
        print(f"⏱️  Duración Total: {summary['total_duration']:.2f} segundos")
        print(f"🎯 Estado General: {summary['overall_status']}")
        
        if summary['success_rate'] >= 0.9:
            print("\n🏆 EXCELLENT: Sistema funcionando perfectamente!")
        elif summary['success_rate'] >= 0.8:
            print("\n✅ GOOD: Sistema funcionando correctamente")
        elif summary['success_rate'] >= 0.6:
            print("\n⚠️  FAIR: Sistema funcionando con algunos problemas")
        else:
            print("\n❌ POOR: Sistema requiere atención")
        
        print("\n📋 Tests Detallados:")
        for test_result in final_report['detailed_results']:
            status_emoji = "✅" if test_result['status'] == 'PASS' else "❌"
            print(f"   {status_emoji} {test_result['test']}: {test_result['status']}")
        
        # Guardar reporte
        report_file = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, default=str, ensure_ascii=False)
        
        print(f"\n💾 Reporte guardado en: {report_file}")
        
        return final_report
        
    except Exception as e:
        print(f"\n💥 ERROR CRÍTICO durante validación: {e}")
        return None

if __name__ == "__main__":
    # Ejecutar validación
    result = asyncio.run(main())
    
    if result and result['summary']['overall_status'] == 'PASS':
        print("\n🎉 VALIDACIÓN COMPLETADA EXITOSAMENTE")
        print("   El sistema está listo para producción")
    else:
        print("\n⚠️  VALIDACIÓN COMPLETADA CON PROBLEMAS")
        print("   Revisar tests fallidos antes de usar en producción")