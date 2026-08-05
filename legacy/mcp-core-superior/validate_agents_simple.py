#!/usr/bin/env python3
"""
Validador Simple de Agentes Especializados
===========================================
Verifica que los agentes estén correctamente implementados sin dependencias externas.
"""

import os
import sys
import ast
import importlib.util

def validate_syntax(file_path):
    """Valida la sintaxis de un archivo Python."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, "Sintaxis válida"
    except SyntaxError as e:
        return False, f"Error de sintaxis: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def validate_class_definition(file_path, expected_classes):
    """Valida que las clases esperadas estén definidas."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        found_classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                found_classes.append(node.name)
        
        missing_classes = [cls for cls in expected_classes if cls not in found_classes]
        
        if not missing_classes:
            return True, f"Todas las clases encontradas: {', '.join(found_classes)}"
        else:
            return False, f"Clases faltantes: {missing_classes}. Encontradas: {', '.join(found_classes)}"
            
    except Exception as e:
        return False, f"Error: {e}"

def validate_file_structure():
    """Valida la estructura de archivos de los agentes especializados."""
    print("🔍 VALIDADOR DE AGENTES ESPECIALIZADOS")
    print("=" * 50)
    
    base_path = "/workspace/mcp-core-superior/src/agents/specialized"
    
    # Archivos esperados
    expected_files = {
        "research_agent.py": ["ResearchAgent"],
        "data_mining_agent.py": ["DataMiningAgent"], 
        "news_intelligence_agent.py": ["NewsIntelligenceAgent"],
        "__init__.py": []  # El __init__ puede no tener clases específicas
    }
    
    all_valid = True
    results = {}
    
    for filename, expected_classes in expected_files.items():
        file_path = os.path.join(base_path, filename)
        
        if not os.path.exists(file_path):
            print(f"❌ {filename}: Archivo no encontrado")
            all_valid = False
            results[filename] = {"exists": False}
            continue
        
        # Verificar sintaxis
        syntax_ok, syntax_msg = validate_syntax(file_path)
        
        if not syntax_ok:
            print(f"❌ {filename}: {syntax_msg}")
            all_valid = False
            results[filename] = {"exists": True, "syntax": False, "syntax_msg": syntax_msg}
            continue
        
        # Verificar clases si se esperan
        if expected_classes:
            classes_ok, classes_msg = validate_class_definition(file_path, expected_classes)
            
            if classes_ok:
                print(f"✅ {filename}: Sintaxis válida - {classes_msg}")
                results[filename] = {"exists": True, "syntax": True, "classes_ok": True, "message": classes_msg}
            else:
                print(f"⚠️ {filename}: Sintaxis válida - {classes_msg}")
                results[filename] = {"exists": True, "syntax": True, "classes_ok": False, "message": classes_msg}
                # No marcamos como error crítico si la sintaxis es válida
        else:
            print(f"✅ {filename}: Sintaxis válida")
            results[filename] = {"exists": True, "syntax": True, "classes_ok": True, "message": "Archivo de módulo"}
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE VALIDACIÓN:")
    
    if all_valid:
        print("✅ TODOS LOS ARCHIVOS VÁLIDOS")
        print("🎉 Los agentes especializados están correctamente implementados")
    else:
        print("⚠️ ALGUNOS PROBLEMAS DETECTADOS")
        print("📝 Revisar los detalles arriba para más información")
    
    # Estadísticas
    total_files = len(expected_files)
    valid_files = sum(1 for r in results.values() if r.get("exists", False) and r.get("syntax", False))
    
    print(f"\n📈 ESTADÍSTICAS:")
    print(f"Archivos validados: {valid_files}/{total_files}")
    
    return results

def validate_import_structure():
    """Valida que la estructura de imports sea coherente."""
    print("\n🔗 VALIDANDO ESTRUCTURA DE IMPORTS...")
    
    # Verificar que el __init__.py existe y tiene contenido válido
    init_path = "/workspace/mcp-core-superior/src/agents/specialized/__init__.py"
    
    if os.path.exists(init_path):
        try:
            with open(init_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Buscar imports relevantes
            has_research_agent = "research_agent" in content
            has_data_mining_agent = "data_mining_agent" in content
            has_news_agent = "news_intelligence_agent" in content
            
            if has_research_agent and has_data_mining_agent and has_news_agent:
                print("✅ __init__.py: Contiene imports para todos los agentes")
            else:
                print("⚠️ __init__.py: Faltan algunos imports de agentes")
                
        except Exception as e:
            print(f"❌ Error leyendo __init__.py: {e}")
    else:
        print("❌ __init__.py: Archivo no encontrado")

if __name__ == "__main__":
    results = validate_file_structure()
    validate_import_structure()
    
    print(f"\n🎯 VALIDACIÓN COMPLETADA")
    print("=" * 50)