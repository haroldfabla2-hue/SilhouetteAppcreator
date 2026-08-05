"""
Test simple para verificar que pytest funciona correctamente
"""

import pytest
import sys
import os

# Agregar src/ al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_simple():
    """Test básico"""
    assert 1 + 1 == 2

def test_import_src():
    """Test de importación de src"""
    try:
        import agents
        assert True
    except ImportError as e:
        pytest.fail(f"No se puede importar agents: {e}")

if __name__ == "__main__":
    test_simple()
    test_import_src()
    print("Tests básicos pasaron exitosamente")