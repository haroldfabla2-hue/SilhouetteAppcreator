"""
Validador de compatibilidad para wrappers de agentes MCP
Verifica que todos los wrappers tengan las dependencias correctas y funcionen adecuadamente
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentWrapperValidator:
    """Validador para wrappers de agentes"""
    
    def __init__(self):
        self.validation_results = {}
        self.required_modules = [
            "asyncio",
            "logging", 
            "datetime",
            "uuid",
            "time"
        ]
    
    def validate_imports(self, agent_file: Path) -> Dict[str, Any]:
        """Validar importaciones de un wrapper de agente"""
        try:
            # Leer contenido del archivo
            with open(agent_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar imports básicos
            missing_imports = []
            for module in self.required_modules:
                if f"import {module}" not in content and f"from {module}" not in content:
                    missing_imports.append(module)
            
            # Verificar import de base_agent_wrapper
            has_base_import = "from .base_agent_wrapper import" in content or "from agents.base_agent_wrapper import" in content
            
            # Verificar importaciones problemáticas específicas
            problematic_patterns = [
                "from agents.base_agent_wrapper import BaseAgentWrapper, AgentCapability",
                "from core.exceptions import AgentException, handle_exceptions",
                "from ..core.exceptions import AgentException, handle_exceptions"
            ]
            
            has_proper_imports = any(pattern in content for pattern in problematic_patterns)
            
            return {
                "file": str(agent_file),
                "status": "ok" if not missing_imports and has_proper_imports else "warning",
                "missing_imports": missing_imports,
                "has_base_imports": has_proper_imports,
                "file_size": len(content),
                "line_count": content.count('\n')
            }
        
        except Exception as e:
            return {
                "file": str(agent_file),
                "status": "error",
                "error": str(e)
            }
    
    def validate_structure(self, agent_file: Path) -> Dict[str, Any]:
        """Validar estructura de clase del wrapper"""
        try:
            with open(agent_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar que tiene clase wrapper
            wrapper_patterns = [
                "class *AgentWrapper(BaseAgentWrapper)",
                "class *Wrapper(BaseAgentWrapper)"
            ]
            
            import re
            has_wrapper_class = any(
                re.search(pattern, content) for pattern in wrapper_patterns
            )
            
            # Verificar métodos requeridos
            required_methods = [
                "def __init__",
                "async def _initialize", 
                "async def process_request",
                "async def health_check"
            ]
            
            missing_methods = []
            for method in required_methods:
                if method not in content:
                    missing_methods.append(method)
            
            return {
                "file": str(agent_file),
                "has_wrapper_class": has_wrapper_class,
                "missing_required_methods": missing_methods,
                "structure_valid": has_wrapper_class and len(missing_methods) == 0
            }
        
        except Exception as e:
            return {
                "file": str(agent_file),
                "status": "error",
                "error": str(e)
            }
    
    async def test_instantiation(self, agent_file: Path) -> Dict[str, Any]:
        """Probar instanciación del wrapper"""
        try:
            # Agregar el directorio al path para importar
            agent_dir = agent_file.parent
            import sys
            if str(agent_dir) not in sys.path:
                sys.path.insert(0, str(agent_dir))
            
            # Obtener nombre del módulo
            module_name = agent_file.stem
            
            # Importar módulo
            module = __import__(module_name)
            
            # Buscar clase wrapper
            wrapper_classes = []
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    attr_name.endswith('Wrapper') and 
                    attr_name != 'BaseAgentWrapper'):
                    wrapper_classes.append(attr_name)
            
            if not wrapper_classes:
                return {
                    "file": str(agent_file),
                    "status": "warning",
                    "message": "No se encontraron clases wrapper"
                }
            
            # Intentar instanciar cada wrapper encontrado
            instances = {}
            for class_name in wrapper_classes:
                try:
                    wrapper_class = getattr(module, class_name)
                    instance = wrapper_class()
                    instances[class_name] = "created"
                except Exception as e:
                    instances[class_name] = f"error: {str(e)}"
            
            return {
                "file": str(agent_file),
                "status": "ok" if instances else "warning",
                "wrapper_classes_found": wrapper_classes,
                "instantiation_results": instances
            }
        
        except Exception as e:
            return {
                "file": str(agent_file),
                "status": "error",
                "error": str(e)
            }
    
    async def validate_agent(self, agent_file: Path) -> Dict[str, Any]:
        """Validación completa de un agente"""
        logger.info(f"Validando agente: {agent_file.name}")
        
        # Validar imports
        import_result = self.validate_imports(agent_file)
        
        # Validar estructura
        structure_result = self.validate_structure(agent_file)
        
        # Probar instanciación
        instantiation_result = await self.test_instantiation(agent_file)
        
        # Combinar resultados
        result = {
            "file": str(agent_file),
            "agent_name": agent_file.stem,
            "import_validation": import_result,
            "structure_validation": structure_result,
            "instantiation_test": instantiation_result,
            "overall_status": self._determine_overall_status([
                import_result, structure_result, instantiation_result
            ])
        }
        
        logger.info(f"Validación de {agent_file.name}: {result['overall_status']}")
        return result
    
    def _determine_overall_status(self, results: List[Dict[str, Any]]) -> str:
        """Determinar estado general basado en resultados individuales"""
        if any(r.get("status") == "error" for r in results):
            return "error"
        elif any(r.get("status") == "warning" for r in results):
            return "warning"
        elif all(r.get("status") == "ok" for r in results):
            return "ok"
        else:
            return "unknown"
    
    async def validate_all_agents(self, agents_dir: Path) -> Dict[str, Any]:
        """Validar todos los agentes en el directorio"""
        logger.info(f"Validando todos los agentes en: {agents_dir}")
        
        # Buscar archivos de agentes
        agent_files = [
            f for f in agents_dir.glob("*.py") 
            if f.name.startswith(".") or "__" in f.name
        ]
        agent_files = [f for f in agents_dir.glob("*.py") if f not in agent_files]
        
        # Validar cada agente
        agent_results = []
        for agent_file in agent_files:
            result = await self.validate_agent(agent_file)
            agent_results.append(result)
        
        # Generar resumen
        summary = self._generate_summary(agent_results)
        
        return {
            "agents_directory": str(agents_dir),
            "validation_results": agent_results,
            "summary": summary,
            "timestamp": asyncio.get_event_loop().time()
        }
    
    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generar resumen de validaciones"""
        total = len(results)
        ok_count = sum(1 for r in results if r["overall_status"] == "ok")
        warning_count = sum(1 for r in results if r["overall_status"] == "warning")
        error_count = sum(1 for r in results if r["overall_status"] == "error")
        
        return {
            "total_agents": total,
            "ok_agents": ok_count,
            "warning_agents": warning_count,
            "error_agents": error_count,
            "success_rate": ok_count / total if total > 0 else 0,
            "status": "ok" if error_count == 0 else "partial" if warning_count > 0 else "error"
        }


async def main():
    """Función principal de validación"""
    # Obtener directorio de agentes
    agents_dir = Path(__file__).parent
    validator = AgentWrapperValidator()
    
    print("🔍 Iniciando validación de wrappers de agentes MCP...")
    print(f"📁 Directorio: {agents_dir}")
    
    # Validar todos los agentes
    results = await validator.validate_all_agents(agents_dir)
    
    # Mostrar resultados
    print("\n" + "="*80)
    print("📊 RESUMEN DE VALIDACIÓN")
    print("="*80)
    
    summary = results["summary"]
    print(f"📈 Total de agentes: {summary['total_agents']}")
    print(f"✅ Agentes OK: {summary['ok_agents']}")
    print(f"⚠️  Agentes con advertencias: {summary['warning_agents']}")
    print(f"❌ Agentes con errores: {summary['error_agents']}")
    print(f"📊 Tasa de éxito: {summary['success_rate']:.1%}")
    print(f"🎯 Estado general: {summary['status'].upper()}")
    
    # Mostrar detalles de agentes problemáticos
    print("\n" + "-"*80)
    print("🔍 DETALLES DE VALIDACIÓN")
    print("-"*80)
    
    for result in results["validation_results"]:
        status_emoji = {
            "ok": "✅",
            "warning": "⚠️ ",
            "error": "❌"
        }.get(result["overall_status"], "❓")
        
        print(f"{status_emoji} {result['agent_name']}")
        
        if result["overall_status"] == "error":
            print(f"   ❌ Error crítico detectado")
        
        if result["overall_status"] == "warning":
            print(f"   ⚠️  Problemas menores detectados")
        
        if result["overall_status"] == "ok":
            print(f"   ✅ Validación exitosa")
    
    return results


if __name__ == "__main__":
    # Ejecutar validación
    results = asyncio.run(main())
    
    # Guardar resultados
    output_file = Path(__file__).parent / "validation_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        import json
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Resultados guardados en: {output_file}")
