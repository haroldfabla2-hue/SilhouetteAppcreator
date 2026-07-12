"""
Validadores de entrada para MCP Core Superior
"""
from typing import Any, Dict, List, Optional, Union
import re
from datetime import datetime


def validate_input(data: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validar datos de entrada según esquema
    
    Args:
        data: Datos a validar
        schema: Esquema de validación
        
    Returns:
        Resultado de validación con errores si los hay
    """
    errors = []
    
    # Validar tipo requerido
    required_type = schema.get("type")
    if required_type and not isinstance(data, required_type):
        errors.append(f"Se esperaba tipo {required_type.__name__}, recibido {type(data).__name__}")
        return {"valid": False, "errors": errors}
    
    # Validar lista de tipos permitidos
    allowed_types = schema.get("allowed_types")
    if allowed_types and not any(isinstance(data, t) for t in allowed_types):
        errors.append(f"Tipo no permitido. Permitidos: {[t.__name__ for t in allowed_types]}")
        return {"valid": False, "errors": errors}
    
    # Validar campos requeridos (para dicts)
    if isinstance(data, dict):
        required_fields = schema.get("required_fields", [])
        for field in required_fields:
            if field not in data:
                errors.append(f"Campo requerido faltante: {field}")
    
    # Validar valor mínimo/máximo (para números)
    if isinstance(data, (int, float)):
        min_value = schema.get("min")
        max_value = schema.get("max")
        
        if min_value is not None and data < min_value:
            errors.append(f"Valor {data} menor que mínimo {min_value}")
        
        if max_value is not None and data > max_value:
            errors.append(f"Valor {data} mayor que máximo {max_value}")
    
    # Validar longitud (para strings)
    if isinstance(data, str):
        min_length = schema.get("min_length")
        max_length = schema.get("max_length")
        
        if min_length is not None and len(data) < min_length:
            errors.append(f"Longitud {len(data)} menor que mínimo {min_length}")
        
        if max_length is not None and len(data) > max_length:
            errors.append(f"Longitud {len(data)} mayor que máximo {max_length}")
    
    # Validar patrón (regex para strings)
    if isinstance(data, str):
        pattern = schema.get("pattern")
        if pattern and not re.match(pattern, data):
            errors.append(f"Valor no cumple patrón: {pattern}")
    
    # Validar valores permitidos
    allowed_values = schema.get("allowed_values")
    if allowed_values is not None and data not in allowed_values:
        errors.append(f"Valor {data} no en lista permitida: {allowed_values}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def sanitize_input(data: Any, rules: Dict[str, Any]) -> Any:
    """
    Sanitizar datos de entrada
    
    Args:
        data: Datos a sanitizar
        rules: Reglas de sanitización
        
    Returns:
        Datos sanitizados
    """
    # Sanitizar strings
    if isinstance(data, str):
        # Remover caracteres peligrosos
        dangerous_chars = rules.get("remove_chars", [])
        for char in dangerous_chars:
            data = data.replace(char, "")
        
        # Strip whitespace
        if rules.get("strip", True):
            data = data.strip()
        
        # Convertir a lowercase
        if rules.get("lowercase", False):
            data = data.lower()
        
        # Truncar longitud máxima
        max_length = rules.get("max_length")
        if max_length and len(data) > max_length:
            data = data[:max_length]
        
        # Reemplazar espacios
        replace_spaces = rules.get("replace_spaces")
        if replace_spaces:
            data = data.replace(" ", replace_spaces)
    
    # Sanitizar listas
    elif isinstance(data, list):
        max_items = rules.get("max_items")
        if max_items and len(data) > max_items:
            data = data[:max_items]
        
        # Recursivamente sanitizar items
        item_rules = rules.get("item_rules", {})
        if item_rules:
            data = [sanitize_input(item, item_rules) for item in data]
    
    # Sanitizar diccionarios
    elif isinstance(data, dict):
        # Filtrar campos permitidos
        allowed_fields = rules.get("allowed_fields")
        if allowed_fields:
            data = {k: v for k, v in data.items() if k in allowed_fields}
        
        # Recursivamente sanitizar valores
        for key, value in data.items():
            key_rules = rules.get(f"field_{key}", {})
            if key_rules:
                data[key] = sanitize_input(value, key_rules)
    
    return data


def validate_objective(objective: str) -> Dict[str, Any]:
    """Validar objetivo de tarea"""
    if not objective or not isinstance(objective, str):
        return {
            "valid": False,
            "errors": ["Objective debe ser un string no vacío"]
        }
    
    errors = []
    
    if len(objective) < 10:
        errors.append("Objective muy corto (mínimo 10 caracteres)")
    
    if len(objective) > 1000:
        errors.append("Objective muy largo (máximo 1000 caracteres)")
    
    # Verificar que no sea solo espacios
    if not objective.strip():
        errors.append("Objective no puede ser solo espacios")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def validate_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """Validar contexto de tarea"""
    if not isinstance(context, dict):
        return {
            "valid": False,
            "errors": ["Context debe ser un diccionario"]
        }
    
    # Validar campos específicos del contexto
    context_schema = {
        "user_id": {"type": str, "max_length": 100},
        "conversation_id": {"type": str, "max_length": 100},
        "timestamp": {"type": str},
        "session_data": {"type": dict},
        "preferences": {"type": dict}
    }
    
    errors = []
    for field, schema in context_schema.items():
        if field in context:
            field_result = validate_input(context[field], schema)
            if not field_result["valid"]:
                errors.extend([f"{field}: {err}" for err in field_result["errors"]])
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def validate_quality_threshold(threshold: Union[int, float]) -> Dict[str, Any]:
    """Validar umbral de calidad"""
    if not isinstance(threshold, (int, float)):
        return {
            "valid": False,
            "errors": ["Threshold debe ser un número"]
        }
    
    if threshold < 0.0 or threshold > 1.0:
        return {
            "valid": False,
            "errors": ["Threshold debe estar entre 0.0 y 1.0"]
        }
    
    return {"valid": True, "errors": []}


def validate_parallel_settings(max_concurrent: int) -> Dict[str, Any]:
    """Validar configuraciones de paralelización"""
    if not isinstance(max_concurrent, int):
        return {
            "valid": False,
            "errors": ["max_concurrent debe ser un entero"]
        }
    
    if max_concurrent < 1:
        return {
            "valid": False,
            "errors": ["max_concurrent debe ser al menos 1"]
        }
    
    if max_concurrent > 10:
        return {
            "valid": False,
            "errors": ["max_concurrent no puede ser mayor a 10"]
        }
    
    return {"valid": True, "errors": []}


def validate_tool_parameters(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Validar parámetros de herramientas"""
    schemas = {
        "reasoner_analyze_intent": {
            "objective": {"type": str, "required": True},
            "context": {"type": dict, "required": False},
            "conversation_id": {"type": str, "required": False},
            "user_id": {"type": str, "required": False}
        },
        "planner_create_execution_plan": {
            "objective": {"type": str, "required": True},
            "analysis": {"type": dict, "required": True},
            "constraints": {"type": dict, "required": False},
            "parallel_agents": {"type": bool, "required": False}
        },
        "orchestrate_multitask": {
            "objective": {"type": str, "required": True},
            "context": {"type": dict, "required": False},
            "user_id": {"type": str, "required": False},
            "streaming_enabled": {"type": bool, "required": False},
            "quality_threshold": {"type": (int, float), "required": False}
        }
    }
    
    if tool_name not in schemas:
        return {
            "valid": True,
            "errors": []
        }
    
    schema = schemas[tool_name]
    errors = []
    
    # Validar campos requeridos
    for field, field_schema in schema.items():
        if field_schema.get("required", False) and field not in parameters:
            errors.append(f"Campo requerido faltante: {field}")
            continue
        
        if field in parameters:
            field_result = validate_input(parameters[field], field_schema)
            if not field_result["valid"]:
                errors.extend([f"{field}: {err}" for err in field_result["errors"]])
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def validate_streaming_request(
    task_id: str,
    duration: Optional[int] = None
) -> Dict[str, Any]:
    """Validar request de streaming"""
    errors = []
    
    if not task_id or not isinstance(task_id, str):
        errors.append("task_id debe ser un string no vacío")
    
    if duration is not None:
        if not isinstance(duration, int):
            errors.append("duration debe ser un entero")
        elif duration < 1 or duration > 3600:
            errors.append("duration debe estar entre 1 y 3600 segundos")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def sanitize_filename(filename: str) -> str:
    """Sanitizar nombre de archivo"""
    # Remover caracteres peligrosos
    dangerous_chars = ['/', '\\\\', '..', '<', '>', ':', '\"', '|', '?', '*']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # Remover espacios al inicio y final
    filename = filename.strip()
    
    # Limitar longitud
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = f"{name[:250]}.{ext}" if ext else filename[:255]
    
    return filename or "sanitized_file"


def validate_date_string(date_str: str) -> Dict[str, Any]:
    """Validar string de fecha"""
    try:
        datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return {"valid": True, "errors": []}
    except ValueError:
        return {
            "valid": False,
            "errors": ["Formato de fecha inválido. Usar ISO format: YYYY-MM-DDTHH:MM:SS"]
        }
