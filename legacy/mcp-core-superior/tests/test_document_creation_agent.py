"""
Tests unitarios para Document Creation Agent
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch
import sys
import os
from pathlib import Path

# Añadir el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.document_creation_agent import (
    DocumentCreationAgent, DocumentTemplate, DocumentContent, SpreadsheetData, 
    DocumentType, DocumentFormat
)


class TestDocumentCreationAgent:
    """Tests para DocumentCreationAgent"""
    
    @pytest.fixture
    async def agent(self):
        """Fixture para crear agente de prueba"""
        agent = DocumentCreationAgent()
        await agent._initialize()
        return agent
    
    def test_agent_initialization(self, agent):
        """Test inicialización del agente"""
        assert agent.agent_name == "DocumentCreationAgent"
        assert agent.is_ready
        assert len(agent.capabilities) > 0
        assert len(agent._templates) > 0  # Debe cargar plantillas predefinidas
        assert agent.output_dir.exists()
    
    def test_substitute_variables(self, agent):
        """Test sustitución de variables en texto"""
        template = "Hola {{name}}, bienvenido a {{company_name}}. Tu ID es {{user_id}}"
        variables = {
            "name": "Juan",
            "company_name": "Tech Corp",
            "user_id": "12345"
        }
        
        result = agent._substitute_variables(template, variables)
        
        assert "Juan" in result
        assert "Tech Corp" in result
        assert "12345" in result
        assert "{{name}}" not in result
        assert "{{company_name}}" not in result
        assert "{{user_id}}" not in result
    
    @pytest.mark.asyncio
    async def test_create_document_basic(self, agent):
        """Test creación básica de documento"""
        response = await agent.create_document(
            title="Documento de Prueba",
            content="Este es el contenido del documento.",
            format_type=DocumentFormat.TXT
        )
        
        assert response.success
        assert response.action == "create_document"
        assert response.document_id is not None
        assert response.file_path is not None
        assert "Documento de Prueba" in agent._documents[response.document_id].title
    
    @pytest.mark.asyncio
    async def test_create_document_with_template(self, agent):
        """Test creación de documento con plantilla"""
        variables = {
            "report_title": "Reporte Mensual de Ventas",
            "report_date": "2024-01-15",
            "author": "Ana García",
            "department": "Ventas",
            "executive_summary": "Las ventas aumentaron 15% este mes",
            "detailed_analysis": "Análisis detallado por región...",
            "conclusions": "Conclusiones positivas sobre el crecimiento",
            "recommendations": "Recomendaciones para el próximo mes",
            "generated_date": datetime.now().strftime("%d/%m/%Y")
        }
        
        response = await agent.create_document(
            template_id="template_report",
            variables=variables,
            format_type=DocumentFormat.MD
        )
        
        assert response.success
        assert response.action == "create_document"
        assert response.details["template_used"] == "template_report"
        
        # Verificar que las variables se sustituyeron
        document = agent._documents[response.document_id]
        assert "Reporte Mensual de Ventas" in document.content
        assert "Ana García" in document.content
    
    @pytest.mark.asyncio
    async def test_create_spreadsheet_basic(self, agent):
        """Test creación básica de hoja de cálculo"""
        headers = ["Fecha", "Producto", "Cantidad", "Precio", "Total"]
        data = [
            ["2024-01-01", "Producto A", 10, 25.50, 255.00],
            ["2024-01-02", "Producto B", 5, 30.00, 150.00],
            ["2024-01-03", "Producto A", 8, 25.50, 204.00]
        ]
        
        response = await agent.create_spreadsheet(
            name="Ventas Enero 2024",
            headers=headers,
            data=data
        )
        
        assert response.success
        assert response.action == "create_spreadsheet"
        assert response.document_id is not None
        assert response.file_path is not None
        
        details = response.details
        assert details["name"] == "Ventas Enero 2024"
        assert details["headers"] == headers
        assert details["rows_count"] == 3
        assert details["columns_count"] == 5
    
    @pytest.mark.asyncio
    async def test_create_spreadsheet_empty_data(self, agent):
        """Test creación de hoja de cálculo con datos vacíos"""
        headers = ["Columna 1", "Columna 2", "Columna 3"]
        data = []
        
        response = await agent.create_spreadsheet(
            name="Hoja Vacía",
            headers=headers,
            data=data
        )
        
        assert response.success
        assert response.details["rows_count"] == 0
        assert response.details["columns_count"] == 3
    
    @pytest.mark.asyncio
    async def test_format_document(self, agent):
        """Test formateo de documento"""
        # Primero crear un documento
        create_response = await agent.create_document(
            title="Documento a Formatear",
            content="Contenido original del documento."
        )
        
        document_id = create_response.document_id
        
        # Luego formatearlo
        formatting_options = {
            "font_family": "Arial",
            "font_size": 12,
            "margins": {"top": 2.5, "bottom": 2.5, "left": 3.0, "right": 3.0}
        }
        
        format_response = await agent.format_document(
            document_id=document_id,
            formatting_options=formatting_options
        )
        
        assert format_response.success
        assert format_response.action == "format_document"
        assert format_response.file_path is not None
        
        # Verificar que se aplicó el formato
        document = agent._documents[document_id]
        assert "formatting" in document.metadata
        assert document.modified_at is not None
    
    @pytest.mark.asyncio
    async def test_format_document_not_found(self, agent):
        """Test formateo de documento inexistente"""
        response = await agent.format_document(
            document_id="nonexistent_document",
            formatting_options={}
        )
        
        assert not response.success
        assert "no encontrado" in response.error
    
    @pytest.mark.asyncio
    async def test_export_document(self, agent):
        """Test exportación de documento a otro formato"""
        # Crear documento
        create_response = await agent.create_document(
            title="Documento para Exportar",
            content="Contenido del documento a exportar."
        )
        
        document_id = create_response.document_id
        
        # Exportar a HTML
        export_response = await agent.export_document(
            document_id=document_id,
            target_format=DocumentFormat.HTML
        )
        
        assert export_response.success
        assert export_response.action == "export_document"
        assert export_response.file_path is not None
        assert export_response.details["target_format"] == "html"
        assert export_response.details["exported_at"] is not None
    
    @pytest.mark.asyncio
    async def test_export_document_invalid_format(self, agent):
        """Test exportación con formato inválido"""
        create_response = await agent.create_document(
            title="Test Document",
            content="Test content"
        )
        
        response = await agent.export_document(
            document_id=create_response.document_id,
            target_format="invalid_format"
        )
        
        assert not response.success
        assert "no soportado" in response.error
    
    @pytest.mark.asyncio
    async def test_list_templates(self, agent):
        """Test listado de plantillas"""
        response = await agent.list_templates()
        
        assert response.success
        assert response.action == "list_templates"
        
        details = response.details
        assert "templates" in details
        
        templates = details["templates"]
        assert len(templates) > 0
        
        # Verificar estructura de plantillas
        for template in templates:
            assert "id" in template
            assert "name" in template
            assert "type" in template
            assert "variables" in template
            assert "variables_count" in template
    
    @pytest.mark.asyncio
    async def test_process_request_create_document(self, agent):
        """Test procesamiento de request de creación de documento"""
        request = {
            "action": "create_document",
            "title": "Test Document",
            "content": "Test content",
            "format": "txt"
        }
        
        response = await agent.process_request(request)
        
        assert response["success"]
        assert "document_id" in response
        assert "file_path" in response
        assert "details" in response
    
    @pytest.mark.asyncio
    async def test_process_request_create_spreadsheet(self, agent):
        """Test procesamiento de request de creación de hoja de cálculo"""
        request = {
            "action": "create_spreadsheet",
            "name": "Test Spreadsheet",
            "headers": ["Column1", "Column2"],
            "data": [["Value1", "Value2"]],
            "sheet_formats": {"header_row": {"bold": True}}
        }
        
        response = await agent.process_request(request)
        
        assert response["success"]
        assert "document_id" in response
        assert "file_path" in response
        assert response["details"]["name"] == "Test Spreadsheet"
    
    @pytest.mark.asyncio
    async def test_process_request_format_document(self, agent):
        """Test procesamiento de request de formateo"""
        # Crear documento primero
        create_request = {
            "action": "create_document",
            "title": "Document to Format",
            "content": "Content"
        }
        create_response = await agent.process_request(create_request)
        
        format_request = {
            "action": "format_document",
            "document_id": create_response["document_id"],
            "formatting_options": {"font_size": 14}
        }
        
        response = await agent.process_request(format_request)
        
        assert response["success"]
        assert "document_id" in response
        assert "file_path" in response
    
    @pytest.mark.asyncio
    async def test_process_request_export_document(self, agent):
        """Test procesamiento de request de exportación"""
        # Crear documento primero
        create_request = {
            "action": "create_document",
            "title": "Document to Export",
            "content": "Content"
        }
        create_response = await agent.process_request(create_request)
        
        export_request = {
            "action": "export_document",
            "document_id": create_response["document_id"],
            "target_format": "html"
        }
        
        response = await agent.process_request(export_request)
        
        assert response["success"]
        assert "document_id" in response
        assert "file_path" in response
    
    def test_get_stats(self, agent):
        """Test obtención de estadísticas"""
        stats = agent.get_stats()
        
        assert "agent_name" in stats
        assert "total_documents" in stats
        assert "total_spreadsheets" in stats
        assert "total_templates" in stats
        assert "output_directory" in stats
        assert "supported_formats" in stats
        assert "available_actions" in stats
        
        # Verificar formatos soportados
        formats = stats["supported_formats"]
        assert "txt" in formats
        assert "html" in formats
        assert "md" in formats
        assert "xlsx" in formats
        
        # Verificar acciones disponibles
        actions = stats["available_actions"]
        assert "create_document" in actions
        assert "create_spreadsheet" in actions
        assert "format_document" in actions
        assert "export_document" in actions
        assert "list_templates" in actions


class TestDocumentTemplate:
    """Tests para DocumentTemplate"""
    
    def test_template_creation(self):
        """Test creación de plantilla"""
        template = DocumentTemplate(
            id="template_1",
            name="Reporte Empresarial",
            type=DocumentType.WORD,
            content="Contenido con {{variable1}} y {{variable2}}",
            variables=["variable1", "variable2"],
            style_config={"font_size": 12}
        )
        
        assert template.id == "template_1"
        assert template.name == "Reporte Empresarial"
        assert template.type == DocumentType.WORD
        assert "{{variable1}}" in template.content
        assert "variable1" in template.variables
        assert template.style_config["font_size"] == 12


class TestDocumentContent:
    """Tests para DocumentContent"""
    
    def test_document_content_creation(self):
        """Test creación de contenido de documento"""
        content = DocumentContent(
            title="Mi Documento",
            content="Este es el contenido del documento.",
            author="Juan Pérez",
            sections=[{"title": "Introducción", "content": "Texto de introducción"}],
            images=["image1.jpg"],
            tables=[["Header1", "Header2"], ["Data1", "Data2"]]
        )
        
        assert content.title == "Mi Documento"
        assert content.author == "Juan Pérez"
        assert len(content.sections) == 1
        assert len(content.images) == 1
        assert len(content.tables) == 2
        assert content.created_at is not None


class TestSpreadsheetData:
    """Tests para SpreadsheetData"""
    
    def test_spreadsheet_data_creation(self):
        """Test creación de datos de hoja de cálculo"""
        sheets = {
            "Sheet1": [["A1", "B1"], ["A2", "B2"]],
            "Sheet2": [["C1", "D1"], ["C2", "D2"]]
        }
        
        spreadsheet = SpreadsheetData(
            name="Mi Hoja de Cálculo",
            sheets=sheets,
            headers=["Columna A", "Columna B"],
            data_types={"Columna A": "text", "Columna B": "number"}
        )
        
        assert spreadsheet.name == "Mi Hoja de Cálculo"
        assert len(spreadsheet.sheets) == 2
        assert spreadsheet.headers == ["Columna A", "Columna B"]
        assert spreadsheet.data_types["Columna A"] == "text"


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v"])