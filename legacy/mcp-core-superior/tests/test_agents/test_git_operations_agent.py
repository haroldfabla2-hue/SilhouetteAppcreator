"""
Tests básicos para el Git Operations Agent

Este archivo contiene tests básicos para verificar el funcionamiento
correcto de las funcionalidades principales del agente.
"""

import os
import sys
import tempfile
import shutil
import asyncio
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents.git_operations_agent import (
    GitOperationsAgent,
    GitProvider,
    MergeStrategy,
    ConflictResolution
)

def setup_test_repo():
    """Configurar un repositorio de prueba"""
    # Crear directorio temporal
    test_dir = tempfile.mkdtemp(prefix='git_test_')
    repo_path = os.path.join(test_dir, 'test_repo')
    
    # Inicializar repositorio Git
    from git import Repo
    repo = Repo.init(repo_path)
    
    # Crear archivo inicial
    readme_path = os.path.join(repo_path, 'README.md')
    with open(readme_path, 'w') as f:
        f.write('# Test Repository\n\nEste es un repositorio de prueba.')
    
    # Crear archivo de Python
    py_file = os.path.join(repo_path, 'main.py')
    with open(py_file, 'w') as f:
        f.write('''#!/usr/bin/env python3
"""Archivo principal de prueba"""

def hello_world():
    return "Hello, World!"

if __name__ == "__main__":
    print(hello_world())
''')
    
    # Crear archivo de configuración
    config_file = os.path.join(repo_path, 'config.json')
    with open(config_file, 'w') as f:
        f.write('{"version": "1.0.0", "debug": true}')
    
    # Commit inicial
    repo.index.add(['README.md', 'main.py', 'config.json'])
    repo.index.commit('Commit inicial del repositorio de prueba')
    
    return test_dir, repo_path

def cleanup_test_repo(test_dir):
    """Limpiar repositorio de prueba"""
    try:
        shutil.rmtree(test_dir)
    except Exception as e:
        print(f"Error limpiando directorio de prueba: {e}")

async def test_repository_info():
    """Test de obtener información del repositorio"""
    print("🧪 Test: Información del repositorio")
    
    test_dir, repo_path = setup_test_repo()
    
    try:
        async with GitOperationsAgent() as agent:
            result = agent.get_repository_info(repo_path)
            
            assert result['success'] == True
            assert 'repository' in result
            assert result['repository']['path'] == repo_path
            
            print("✅ Test passed: Información del repositorio obtenida correctamente")
            return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        cleanup_test_repo(test_dir)

async def test_branch_operations():
    """Test de operaciones de branches"""
    print("\n🧪 Test: Operaciones de branches")
    
    test_dir, repo_path = setup_test_repo()
    
    try:
        async with GitOperationsAgent() as agent:
            # Test listar branches
            result = agent.list_branches(repo_path)
            assert result['success'] == True
            assert len(result['branches']) > 0
            
            # Test crear nueva branch
            result = agent.create_branch(
                repo_path=repo_path,
                branch_name="feature/test-branch",
                from_branch="master"
            )
            assert result['success'] == True
            
            # Test cambiar a nueva branch
            result = agent.switch_branch(
                repo_path=repo_path,
                branch_name="feature/test-branch"
            )
            assert result['success'] == True
            
            print("✅ Test passed: Operaciones de branches funcionan correctamente")
            return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        cleanup_test_repo(test_dir)

async def test_commit_operations():
    """Test de operaciones de commits"""
    print("\n🧪 Test: Operaciones de commits")
    
    test_dir, repo_path = setup_test_repo()
    
    try:
        async with GitOperationsAgent() as agent:
            # Test historial de commits
            result = agent.get_commit_history(repo_path)
            assert result['success'] == True
            assert len(result['commits']) > 0
            
            # Test obtener diff
            result = agent.get_diff(
                repo_path=repo_path,
                from_commit="HEAD~1",
                to_commit="HEAD"
            )
            assert result['success'] == True
            
            # Test cambios sin comprometer
            result = agent.get_uncommitted_changes(repo_path)
            assert result['success'] == True
            
            print("✅ Test passed: Operaciones de commits funcionan correctamente")
            return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        cleanup_test_repo(test_dir)

async def test_merge_operations():
    """Test de operaciones de merge"""
    print("\n🧪 Test: Operaciones de merge")
    
    test_dir, repo_path = setup_test_repo()
    
    try:
        async with GitOperationsAgent() as agent:
            from git import Repo
            
            # Crear branch de feature
            result = agent.create_branch(
                repo_path=repo_path,
                branch_name="feature/test-merge",
                from_branch="master"
            )
            assert result['success'] == True
            
            # Hacer cambios en la branch de feature
            repo = Repo(repo_path)
            repo.git.checkout("feature/test-merge")
            
            test_file = os.path.join(repo_path, 'test_file.txt')
            with open(test_file, 'w') as f:
                f.write('Archivo de prueba para merge')
            
            repo.index.add(['test_file.txt'])
            repo.index.commit('Commit de prueba para merge')
            
            # Cambiar a master y hacer merge
            repo.git.checkout("master")
            
            result = agent.merge_branch(
                repo_path=repo_path,
                source_branch="feature/test-merge",
                strategy=MergeStrategy.MERGE
            )
            assert result['success'] == True
            
            print("✅ Test passed: Operaciones de merge funcionan correctamente")
            return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        cleanup_test_repo(test_dir)

async def test_conflict_detection():
    """Test de detección de conflictos"""
    print("\n🧪 Test: Detección de conflictos")
    
    test_dir, repo_path = setup_test_repo()
    
    try:
        async with GitOperationsAgent() as agent:
            from git import Repo
            
            # Crear branch de feature
            result = agent.create_branch(
                repo_path=repo_path,
                branch_name="feature/test-conflict",
                from_branch="master"
            )
            assert result['success'] == True
            
            # Modificar archivo en master
            repo = Repo(repo_path)
            repo.git.checkout("master")
            
            config_file = os.path.join(repo_path, 'config.json')
            with open(config_file, 'w') as f:
                f.write('{"version": "2.0.0", "debug": false}')
            
            repo.index.add(['config.json'])
            repo.index.commit('Cambio en master')
            
            # Modificar archivo en feature branch
            repo.git.checkout("feature/test-conflict")
            
            with open(config_file, 'w') as f:
                f.write('{"version": "1.5.0", "debug": true, "new_field": "value"}')
            
            repo.index.add(['config.json'])
            repo.index.commit('Cambio en feature branch')
            
            # Intentar merge para generar conflicto
            repo.git.checkout("master")
            
            try:
                repo.git.merge("feature/test-conflict")
                # Si llegamos aquí, no hubo conflicto (podría ser fast-forward)
                print("ℹ️ No se detectó conflicto (posible fast-forward)")
            except Exception:
                # Conflicto esperado
                pass
            
            # Detectar conflictos
            result = agent.detect_conflicts(repo_path)
            assert result['success'] == True
            
            print("✅ Test passed: Detección de conflictos funciona correctamente")
            return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        cleanup_test_repo(test_dir)

async def test_health_analysis():
    """Test de análisis de salud del repositorio"""
    print("\n🧪 Test: Análisis de salud del repositorio")
    
    test_dir, repo_path = setup_test_repo()
    
    try:
        async with GitOperationsAgent() as agent:
            # Agregar archivo .gitignore
            gitignore_path = os.path.join(repo_path, '.gitignore')
            with open(gitignore_path, 'w') as f:
                f.write('__pycache__/\n*.pyc\n.env\n')
            
            from git import Repo
            repo = Repo(repo_path)
            repo.index.add(['.gitignore'])
            repo.index.commit('Agregar .gitignore')
            
            # Analizar salud
            result = agent.analyze_repository_health(repo_path)
            assert result['success'] == True
            assert 'health_report' in result
            
            health = result['health_report']
            assert 'overall_health' in health
            assert 'issues' in health
            assert 'recommendations' in health
            assert 'statistics' in health
            
            print(f"✅ Test passed: Análisis de salud completado")
            print(f"   Salud general: {health['overall_health']}")
            print(f"   Issues encontrados: {len(health['issues'])}")
            print(f"   Recomendaciones: {len(health['recommendations'])}")
            
            return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        cleanup_test_repo(test_dir)

async def test_workflow_operations():
    """Test de workflows complejos"""
    print("\n🧪 Test: Workflows complejos")
    
    test_dir, repo_path = setup_test_repo()
    
    try:
        async with GitOperationsAgent() as agent:
            # Test feature branch workflow
            result = agent.create_feature_branch_workflow(
                repo_path=repo_path,
                feature_name="test-workflow",
                base_branch="master"
            )
            assert result['success'] == True
            assert 'workflow_type' in result
            
            # Test release workflow
            result = agent.create_release_workflow(
                repo_path=repo_path,
                version="1.0.0",
                release_notes="Test release"
            )
            assert result['success'] == True
            
            # Test hotfix workflow
            result = agent.create_hotfix_workflow(
                repo_path=repo_path,
                fix_description="Test hotfix",
                production_branch="master"
            )
            assert result['success'] == True
            
            print("✅ Test passed: Workflows complejos funcionan correctamente")
            return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        cleanup_test_repo(test_dir)

async def test_multiple_remotes():
    """Test de múltiples remotes"""
    print("\n🧪 Test: Múltiples remotes")
    
    test_dir, repo_path = setup_test_repo()
    
    try:
        async with GitOperationsAgent() as agent:
            # Test listar remotes (debería tener origin)
            result = agent.list_remotes(repo_path)
            assert result['success'] == True
            
            # Test agregar remote
            result = agent.add_remote(
                repo_path=repo_path,
                name="backup",
                url="https://github.com/test/backup.git"
            )
            assert result['success'] == True
            
            # Test listar remotes después de agregar
            result = agent.list_remotes(repo_path)
            assert result['success'] == True
            assert len(result['remotes']) >= 2  # origin + backup
            
            # Test actualizar remote
            result = agent.update_remote(
                repo_path=repo_path,
                name="backup",
                new_url="https://github.com/test/new_backup.git"
            )
            assert result['success'] == True
            
            # Test eliminar remote
            result = agent.remove_remote(
                repo_path=repo_path,
                name="backup"
            )
            assert result['success'] == True
            
            print("✅ Test passed: Operaciones de múltiples remotes funcionan correctamente")
            return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        cleanup_test_repo(test_dir)

async def test_testing_environment():
    """Test de ambiente de testing"""
    print("\n🧪 Test: Ambiente de testing")
    
    test_dir, repo_path = setup_test_repo()
    
    try:
        async with GitOperationsAgent() as agent:
            # Test setup de ambiente pytest
            result = agent.setup_test_environment(
                repo_path=repo_path,
                test_framework="pytest"
            )
            assert result['success'] == True
            assert 'test_directory' in result
            
            # Verificar que se creó el directorio de tests
            tests_dir = os.path.join(repo_path, 'tests')
            assert os.path.exists(tests_dir)
            
            # Verificar archivo de configuración
            config_file = os.path.join(repo_path, 'pytest.ini')
            assert os.path.exists(config_file)
            
            print("✅ Test passed: Ambiente de testing configurado correctamente")
            return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        cleanup_test_repo(test_dir)

async def run_all_tests():
    """Ejecutar todos los tests"""
    print("🧪 Iniciando tests del Git Operations Agent")
    print("=" * 50)
    
    tests = [
        test_repository_info,
        test_branch_operations,
        test_commit_operations,
        test_merge_operations,
        test_conflict_detection,
        test_health_analysis,
        test_workflow_operations,
        test_multiple_remotes,
        test_testing_environment
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} falló con excepción: {e}")
            failed += 1
        
        # Pequeña pausa entre tests
        await asyncio.sleep(0.1)
    
    print("\n" + "=" * 50)
    print(f"📊 Resumen de tests:")
    print(f"   ✅ Pasados: {passed}")
    print(f"   ❌ Fallidos: {failed}")
    print(f"   📈 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 ¡Todos los tests pasaron exitosamente!")
        return True
    else:
        print(f"\n⚠️ {failed} test(s) fallaron")
        return False

if __name__ == "__main__":
    # Ejecutar tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)