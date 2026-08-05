"""
Formateador de respuestas para MCP Core Superior
"""
from typing import Any, Dict, List, Optional
import json
from datetime import datetime


class ResponseFormatter:
    """Formateador de respuestas del sistema"""
    
    @staticmethod
    def format_success(
        data: Any,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Formatear respuesta exitosa"""
        response = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        if message:
            response["message"] = message
        
        if metadata:
            response["metadata"] = metadata
        
        return response
    
    @staticmethod
    def format_error(
        error: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Formatear respuesta de error"""
        response = {
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "error": error
        }
        
        if code:
            response["error_code"] = code
        
        if details:
            response["error_details"] = details
        
        return response
    
    @staticmethod
    def format_agent_status(agent_name: str, status_data: Dict[str, Any]) -> str:
        """Formatear estado de agente para display"""
        lines = [
            f"🤖 {agent_name.upper()} AGENT STATUS",
            "=" * 50,
            f"Estado: {status_data.get('status', 'unknown')}",
            f"Listo: {'✅' if status_data.get('is_ready') else '❌'}",
            f"Ocupado: {'🔄' if status_data.get('is_busy') else '🟢'}",
            f"Utilización: {status_data.get('utilization', 0):.1%}",
            f"Operaciones activas: {status_data.get('current_operations', 0)}",
            f"Tasa de éxito: {status_data.get('success_rate', 0):.1%}",
            f"Última actividad: {status_data.get('last_activity', 'n/a')}",
            "",
            "Capacidades:",
        ]
        
        capabilities = status_data.get('capabilities', [])
        for cap in capabilities:
            lines.append(f"  • {cap}")
        
        return "\\n".join(lines)
    
    @staticmethod
    def format_system_overview(system_status: Dict[str, Any]) -> str:
        """Formatear vista general del sistema"""
        lines = [
            "🏗️ MCP CORE SUPERIOR - SISTEMA COMPLETO",
            "=" * 60,
            ""
        ]
        
        # Información del servidor
        server_info = system_status.get("server_info", {})
        lines.extend([
            f"📊 Servidor: {server_info.get('name', 'Unknown')} v{server_info.get('version', 'Unknown')}",
            f"🌍 Entorno: {server_info.get('environment', 'Unknown')}",
            f"🐛 Debug: {'Activado' if server_info.get('debug') else 'Desactivado'}",
            ""
        ])
        
        # Estado de agentes
        agents = system_status.get("agents", {})
        if agents:
            lines.append("🤖 ESTADO DE AGENTES:")
            for agent_name, agent_status in agents.items():
                status = agent_status.get('status', 'unknown')
                icon = {"ready": "🟢", "busy": "🟡", "error": "🔴"}.get(status, "⚪")
                lines.append(f"  {icon} {agent_name}: {status}")
            lines.append("")
        
        # Capacidades
        capabilities = system_status.get("capabilities", [])
        if capabilities:
            lines.append("⚡ CAPACIDADES DISPONIBLES:")
            for cap in capabilities:
                lines.append(f"  ✓ {cap}")
            lines.append("")
        
        return "\\n".join(lines)
    
    @staticmethod
    def format_json(data: Any, indent: int = 2) -> str:
        """Formatear datos como JSON legible"""
        return json.dumps(data, indent=indent, ensure_ascii=False, default=str)
    
    @staticmethod
    def format_table(headers: List[str], rows: List[List[str]]) -> str:
        """Formatear datos como tabla"""
        if not headers or not rows:
            return ""
        
        # Calcular anchos de columnas
        col_widths = [len(header) for header in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Crear líneas de tabla
        lines = []
        
        # Header
        header_line = " | ".join(
            header.ljust(col_widths[i]) 
            for i, header in enumerate(headers)
        )
        lines.append(header_line)
        lines.append("-" * len(header_line))
        
        # Rows
        for row in rows:
            row_line = " | ".join(
                str(cell).ljust(col_widths[i]) 
                for i, cell in enumerate(row)
            )
            lines.append(row_line)
        
        return "\\n".join(lines)
