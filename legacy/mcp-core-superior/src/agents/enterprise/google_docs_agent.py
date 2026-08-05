"""
Google Docs Agent - Agente Especializado para Google Docs
Proporciona capacidades avanzadas de creación, edición y gestión de documentos
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
import httpx

from .base_google_workspace_agent import (
    BaseGoogleWorkspaceAgent, 
    GoogleWorkspaceService, 
    GoogleWorkspaceConfig,
    ApiResponse
)
from ...core.exceptions import AgentException, handle_exceptions
from ...core.config import settings


class DocumentStyle(Enum):
    """Estilos de documento"""
    NORMAL = "NORMAL_TEXT_RUN"
    HEADING_1 = "HEADING_1"
    HEADING_2 = "HEADING_2"
    HEADING_3 = "HEADING_3"
    BULLET = "BULLET"
    NUMBERED = "NUMBERED_LIST"
    QUOTE = "QUOTE"
    CODE = "CODE"


class ElementType(Enum):
    """Tipos de elementos en documento"""
    PARAGRAPH = "paragraph"
    TABLE = "table"
    LIST = "list"
    IMAGE = "image"
    CHART = "chart"
    BOOKMARK = "bookmark"
    FOOTER = "footer"
    HEADER = "header"


@dataclass
class DocumentElement:
    """Elemento de documento"""
    type: ElementType
    content: Any
    style: Optional[DocumentStyle] = None
    index: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentTemplate:
    """Plantilla de documento"""
    name: str
    description: str
    elements: List[DocumentElement]
    default_style: DocumentStyle = DocumentStyle.NORMAL


@dataclass
class DocumentAnalysis:
    """Análisis de documento"""
    word_count: int
    character_count: int
    paragraph_count: int
    sentence_count: int
    page_count: Optional[int] = None
    readability_score: Optional[float] = None
    language: Optional[str] = None
    last_modified: Optional[datetime] = None


class GoogleDocsAgent(BaseGoogleWorkspaceAgent):
    """
    Agente Especializado para Google Docs
    
    Funcionalidades:
    - Crear y editar documentos
    - Aplicar estilos y formato
    - Insertar tablas, listas e imágenes
    - Convertir formatos
    - Analizar contenido
    - Buscar y reemplazar
    - Gestionar permisos
    - Colaboración en tiempo real
    """
    
    def __init__(self, config: GoogleWorkspaceConfig):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.docs_service = None
        
        # Configurar capacidades específicas
        self.add_capability(AgentCapability.DOCUMENT_PROCESSING)
        self.add_capability(AgentCapability.TEXT_GENERATION)
    
    async def initialize(self):
        """Inicializar servicio de Docs"""
        await super().authenticate()
        self.docs_service = await self.get_service(GoogleWorkspaceService.DOCS)
    
    @handle_exceptions
    async def create_document(
        self, 
        title: str,
        content: Optional[str] = None,
        template: Optional[DocumentTemplate] = None
    ) -> ApiResponse:
        """
        Crear nuevo documento
        
        Args:
            title: Título del documento
            content: Contenido inicial
            template: Plantilla a usar
            
        Returns:
            ApiResponse: Resultado con ID del documento
        """
        try:
            # Crear documento
            document = {
                'title': title
            }
            
            result = self.docs_service.documents().create(body=document).execute()
            document_id = result.get('documentId')
            
            # Aplicar contenido inicial si se proporciona
            if content:
                await self.insert_text(document_id, 1, content)
            
            # Aplicar plantilla si se proporciona
            if template:
                await self.apply_template(document_id, template)
            
            self.logger.info(f"Documento creado: {document_id}")
            
            return ApiResponse(
                success=True,
                data={
                    'document_id': document_id,
                    'title': title,
                    'url': f"https://docs.google.com/document/d/{document_id}/edit"
                }
            )
            
        except Exception as e:
            error_msg = f"Error creando documento: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def get_document_content(self, document_id: str) -> ApiResponse:
        """
        Obtener contenido completo del documento
        
        Args:
            document_id: ID del documento
            
        Returns:
            ApiResponse: Contenido del documento
        """
        try:
            result = self.docs_service.documents().get(
                documentId=document_id
            ).execute()
            
            content = self._parse_document_content(result)
            
            return ApiResponse(
                success=True,
                data=content
            )
            
        except Exception as e:
            error_msg = f"Error obteniendo contenido: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def insert_text(
        self, 
        document_id: str, 
        index: int, 
        text: str,
        style: Optional[DocumentStyle] = None
    ) -> ApiResponse:
        """
        Insertar texto en posición específica
        
        Args:
            document_id: ID del documento
            index: Posición donde insertar
            text: Texto a insertar
            style: Estilo a aplicar
            
        Returns:
            ApiResponse: Resultado de la operación
        """
        try:
            requests = []
            
            # Insertar texto
            requests.append({
                'insertText': {
                    'location': {'index': index},
                    'text': text
                }
            })
            
            # Aplicar estilo si se especifica
            if style:
                text_length = len(text)
                requests.append({
                    'updateTextStyle': {
                        'range': {
                            'startIndex': index,
                            'endIndex': index + text_length
                        },
                        'textStyle': {
                            'namedStyleType': style.value
                        },
                        'fields': 'namedStyleType'
                    }
                })
            
            # Ejecutar batchUpdate
            body = {'requests': requests}
            self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body=body
            ).execute()
            
            return ApiResponse(success=True, data={'inserted_length': len(text)})
            
        except Exception as e:
            error_msg = f"Error insertando texto: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def insert_table(
        self, 
        document_id: str, 
        index: int, 
        rows: int, 
        columns: int,
        headers: Optional[List[str]] = None
    ) -> ApiResponse:
        """
        Insertar tabla en documento
        
        Args:
            document_id: ID del documento
            index: Posición donde insertar
            rows: Número de filas
            columns: Número de columnas
            headers: Encabezados de columna
            
        Returns:
            ApiResponse: Resultado de la operación
        """
        try:
            requests = [{
                'insertTable': {
                    'location': {'index': index},
                    'rows': rows,
                    'columns': columns
                }
            }]
            
            # Agregar encabezados si se proporcionan
            if headers and len(headers) == columns:
                requests.append({
                    'updateTableCellStyle': {
                        'tableRange': {
                            'rowIndex': 0,
                            'columnIndex': 0,
                            'rowSpan': 1,
                            'columnSpan': columns
                        },
                        'tableCellStyle': {
                            'backgroundColor': {
                                'color': {'rgbColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}}
                            }
                        },
                        'fields': 'backgroundColor'
                    }
                })
            
            body = {'requests': requests}
            self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body=body
            ).execute()
            
            return ApiResponse(success=True, data={'table_size': f"{rows}x{columns}"})
            
        except Exception as e:
            error_msg = f"Error insertando tabla: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def apply_template(
        self, 
        document_id: str, 
        template: DocumentTemplate
    ) -> ApiResponse:
        """
        Aplicar plantilla a documento
        
        Args:
            document_id: ID del documento
            template: Plantilla a aplicar
            
        Returns:
            ApiResponse: Resultado de la operación
        """
        try:
            # Aplicar elementos de plantilla
            current_index = 1
            for element in template.elements:
                if element.type == ElementType.PARAGRAPH:
                    await self.insert_text(
                        document_id, 
                        current_index, 
                        str(element.content),
                        element.style or template.default_style
                    )
                    current_index += len(str(element.content)) + 1
                
                elif element.type == ElementType.TABLE:
                    # Lógica para insertar tabla desde elemento
                    pass
            
            return ApiResponse(success=True, data={'template_applied': template.name})
            
        except Exception as e:
            error_msg = f"Error aplicando plantilla: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def analyze_document(self, document_id: str) -> ApiResponse:
        """
        Analizar documento para extraer métricas
        
        Args:
            document_id: ID del documento
            
        Returns:
            ApiResponse: Análisis del documento
        """
        try:
            result = self.docs_service.documents().get(
                documentId=document_id
            ).execute()
            
            analysis = self._analyze_document_content(result)
            
            return ApiResponse(success=True, data=analysis)
            
        except Exception as e:
            error_msg = f"Error analizando documento: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def search_and_replace(
        self, 
        document_id: str, 
        search_text: str, 
        replacement_text: str
    ) -> ApiResponse:
        """
        Buscar y reemplazar texto
        
        Args:
            document_id: ID del documento
            search_text: Texto a buscar
            replacement_text: Texto de reemplazo
            
        Returns:
            ApiResponse: Resultado de la operación
        """
        try:
            # Obtener contenido para análisis
            content_result = await self.get_document_content(document_id)
            if not content_result.success:
                return content_result
            
            content = content_result.data
            text = content.get('text', '')
            
            # Contar ocurrencias
            occurrences = text.count(search_text)
            
            # Realizar reemplazos usando API
            requests = [{
                'replaceAllText': {
                    'containsText': {'text': search_text},
                    'replaceText': replacement_text
                }
            }]
            
            body = {'requests': requests}
            self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body=body
            ).execute()
            
            return ApiResponse(
                success=True,
                data={'replacements_made': occurrences}
            )
            
        except Exception as e:
            error_msg = f"Error en búsqueda y reemplazo: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def export_document(
        self, 
        document_id: str, 
        format: str = 'pdf',
        folder_id: Optional[str] = None
    ) -> ApiResponse:
        """
        Exportar documento a otro formato
        
        Args:
            document_id: ID del documento
            format: Formato de exportación (pdf, docx, txt, html)
            folder_id: ID de carpeta de destino (opcional)
            
        Returns:
            ApiResponse: Resultado de la exportación
        """
        try:
            # URL de exportación
            export_url = f"https://docs.google.com/document/d/{document_id}/export"
            
            params = {'format': format}
            headers = {
                'Authorization': f'Bearer {self.credentials.token}'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    export_url,
                    params=params,
                    headers=headers
                )
                
                if response.status_code == 200:
                    # Guardar archivo
                    filename = f"document_{document_id}.{format}"
                    if folder_id:
                        filename = f"folder_{folder_id}/{filename}"
                    
                    # Aquí se guardaría el archivo
                    return ApiResponse(
                        success=True,
                        data={
                            'filename': filename,
                            'format': format,
                            'size_bytes': len(response.content)
                        }
                    )
                else:
                    return ApiResponse(
                        success=False,
                        error=f"Error en exportación: {response.status_code}"
                    )
            
        except Exception as e:
            error_msg = f"Error exportando documento: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    def _parse_document_content(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Parsear contenido del documento"""
        content = {
            'title': document.get('title', ''),
            'text': '',
            'elements': [],
            'structure': []
        }
        
        text_parts = []
        
        for element in document.get('body', {}).get('content', []):
            if 'paragraph' in element:
                paragraph = element['paragraph']
                paragraph_text = ''
                
                for run in paragraph.get('elements', []):
                    if 'textRun' in run:
                        paragraph_text += run['textRun'].get('content', '')
                
                text_parts.append(paragraph_text)
                content['elements'].append({
                    'type': 'paragraph',
                    'text': paragraph_text
                })
            
            elif 'table' in element:
                content['elements'].append({
                    'type': 'table',
                    'content': element['table']
                })
        
        content['text'] = ''.join(text_parts)
        return content
    
    def _analyze_document_content(self, document: Dict[str, Any]) -> DocumentAnalysis:
        """Analizar contenido del documento"""
        content = self._parse_document_content(document)
        text = content['text']
        
        # Calcular métricas básicas
        word_count = len(text.split())
        character_count = len(text)
        paragraph_count = len([e for e in content['elements'] if e['type'] == 'paragraph'])
        sentence_count = text.count('.') + text.count('!') + text.count('?')
        
        return DocumentAnalysis(
            word_count=word_count,
            character_count=character_count,
            paragraph_count=paragraph_count,
            sentence_count=sentence_count,
            last_modified=datetime.now()  # Se obtendría de metadata real
        )
    
    @handle_exceptions
    async def share_document(
        self, 
        document_id: str, 
        email: str, 
        role: str = 'reader'
    ) -> ApiResponse:
        """
        Compartir documento con usuario
        
        Args:
            document_id: ID del documento
            email: Email del usuario
            role: Rol (reader, writer, owner)
            
        Returns:
            ApiResponse: Resultado del compartir
        """
        try:
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }
            
            drive_service = await self.get_service(GoogleWorkspaceService.DRIVE)
            drive_service.permissions().create(
                fileId=document_id,
                body=permission
            ).execute()
            
            return ApiResponse(
                success=True,
                data={'shared_with': email, 'role': role}
            )
            
        except Exception as e:
            error_msg = f"Error compartiendo documento: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar salud del agente Google Docs"""
        try:
            # Verificar servicio base
            base_health = await super().health_check()
            
            if not base_health["healthy"]:
                return base_health
            
            # Test específico de Docs API
            test_doc = await self.create_document(
                title="Health Check Test",
                content="Test de conectividad"
            )
            
            if test_doc.success:
                # Limpiar documento de prueba
                document_id = test_doc.data['document_id']
                # Aquí se eliminaría el documento de prueba
                
                return {
                    "healthy": True,
                    "service": "Google Docs Agent",
                    "test_creation": "passed",
                    "details": base_health
                }
            else:
                return {
                    "healthy": False,
                    "error": "Error en creación de documento",
                    "details": base_health
                }
                
        except Exception as e:
            return {
                "healthy": False,
                "error": f"Error en health check: {str(e)}",
                "service": "Google Docs Agent"
            }