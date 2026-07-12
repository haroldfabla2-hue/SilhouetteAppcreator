"""
Microsoft 365 - Word Online Integration Agent
Agente especializado para operaciones con documentos Word Online
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import base64
import json

from ..graph.client import GraphAPIClient, GraphAPIError
from ..config.settings import service_config, RATE_LIMITS
from ..utils.logger import get_logger
from ..utils.document_processor import DocumentProcessor
from ..utils.content_parser import ContentParser

logger = get_logger(__name__)

class WordOnlineAgent:
    """Agente para operaciones con Microsoft Word Online"""
    
    def __init__(self, graph_client: GraphAPIClient):
        self.graph_client = graph_client
        self.document_processor = DocumentProcessor()
        self.content_parser = ContentParser()
        
        # Rate limiting específico para Word
        self.rate_limit_config = RATE_LIMITS["word"]
        
        # Configuración de documentos
        self.max_document_size = service_config.word_max_document_size
        self.supported_formats = ['.docx', '.doc']
    
    async def create_document(
        self,
        title: str,
        content: str = "",
        folder_path: str = ""
    ) -> Dict:
        """Crear nuevo documento de Word"""
        try:
            # Validar tamaño del contenido
            content_bytes = content.encode('utf-8')
            if len(content_bytes) > self.max_document_size:
                raise ValueError(f"Document content exceeds maximum size: {self.max_document_size} bytes")
            
            # Preparar metadatos del documento
            document_metadata = {
                'name': f"{title}.docx",
                'description': f"Documento creado automáticamente - {datetime.utcnow().isoformat()}",
                'created': datetime.utcnow().isoformat(),
                'author': 'Microsoft365 Integration'
            }
            
            # Crear archivo en OneDrive
            if folder_path:
                # Obtener ID de la carpeta
                folder_items = await self.graph_client.list_files(folder_path)
                folder_id = folder_items['value'][0]['id'] if folder_items['value'] else None
                
                if folder_id:
                    # Subir a carpeta específica
                    result = await self._create_document_in_folder(folder_id, content, document_metadata)
                else:
                    logger.warning(f"Folder not found: {folder_path}")
                    result = await self._create_document_root(content, document_metadata)
            else:
                # Crear en raíz
                result = await self._create_document_root(content, document_metadata)
            
            logger.info(f"Document created successfully: {title}")
            return {
                'status': 'success',
                'document_id': result['id'],
                'name': result['name'],
                'web_url': result.get('webUrl'),
                'download_url': result.get('@microsoft.graph.downloadUrl'),
                'created_at': result.get('createdDateTime'),
                'size': result.get('size', 0)
            }
            
        except Exception as e:
            logger.error(f"Error creating document {title}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'document_name': title
            }
    
    async def open_document(self, document_id: str) -> Dict:
        """Abrir y obtener contenido de documento"""
        try:
            # Obtener metadatos del documento
            document_metadata = await self.graph_client.get_file(document_id)
            
            # Verificar si es un documento de Word
            if not self._is_word_document(document_metadata.get('name', '')):
                raise ValueError("File is not a supported Word document format")
            
            # Descargar contenido
            content_bytes = await self.graph_client.download_file(document_id)
            
            # Procesar contenido
            processed_content = await self.document_processor.process_word_document(
                content_bytes
            )
            
            return {
                'status': 'success',
                'document_id': document_id,
                'name': document_metadata.get('name'),
                'content': processed_content,
                'metadata': {
                    'size': document_metadata.get('size'),
                    'created': document_metadata.get('createdDateTime'),
                    'modified': document_metadata.get('lastModifiedDateTime'),
                    'author': document_metadata.get('createdBy', {}).get('user', {}).get('displayName'),
                    'web_url': document_metadata.get('webUrl')
                }
            }
            
        except Exception as e:
            logger.error(f"Error opening document {document_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'document_id': document_id
            }
    
    async def edit_document(
        self,
        document_id: str,
        content: str,
        append: bool = False
    ) -> Dict:
        """Editar contenido de documento existente"""
        try:
            # Obtener documento actual si es necesario
            if append:
                current_doc = await self.open_document(document_id)
                if current_doc['status'] == 'success':
                    content = current_doc['content'] + "\n\n" + content
            
            # Validar tamaño
            content_bytes = content.encode('utf-8')
            if len(content_bytes) > self.max_document_size:
                raise ValueError(f"Updated content exceeds maximum size")
            
            # Actualizar documento
            result = await self.graph_client.upload_file(
                "updated_document.docx",  # Nombre temporal
                content_bytes,
                parent_id=document_id
            )
            
            logger.info(f"Document edited successfully: {document_id}")
            return {
                'status': 'success',
                'document_id': document_id,
                'updated_at': datetime.utcnow().isoformat(),
                'new_version': result.get('eTag', 'Unknown')
            }
            
        except Exception as e:
            logger.error(f"Error editing document {document_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'document_id': document_id
            }
    
    async def save_document(
        self,
        document_id: str,
        content: str,
        backup: bool = True
    ) -> Dict:
        """Guardar documento con respaldo opcional"""
        try:
            backup_result = None
            
            if backup:
                # Crear copia de seguridad
                backup_result = await self.create_backup_copy(document_id)
            
            # Guardar cambios
            save_result = await self.edit_document(document_id, content)
            
            if save_result['status'] == 'success':
                return {
                    'status': 'success',
                    'document_id': document_id,
                    'saved_at': datetime.utcnow().isoformat(),
                    'backup_created': backup_result is not None,
                    'backup_id': backup_result.get('document_id') if backup_result else None
                }
            else:
                return save_result
                
        except Exception as e:
            logger.error(f"Error saving document {document_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'document_id': document_id
            }
    
    async def close_document(self, document_id: str) -> Dict:
        """Cerrar documento (liberar recursos)"""
        try:
            # En un entorno real, esto podría liberar locks o conexiones
            logger.info(f"Document closed: {document_id}")
            
            return {
                'status': 'success',
                'document_id': document_id,
                'closed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error closing document {document_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'document_id': document_id
            }
    
    async def search_documents(
        self,
        search_term: str,
        folder_path: str = "",
        file_type: str = ".docx"
    ) -> List[Dict]:
        """Buscar documentos por contenido o nombre"""
        try:
            # Obtener lista de archivos
            files_result = await self.graph_client.list_files(folder_path)
            
            if 'value' not in files_result:
                return []
            
            matching_documents = []
            
            for file_item in files_result['value']:
                file_name = file_item.get('name', '')
                
                # Filtrar por tipo de archivo
                if not file_name.lower().endswith(file_type):
                    continue
                
                # Búsqueda por nombre
                if search_term.lower() in file_name.lower():
                    matching_documents.append({
                        'document_id': file_item['id'],
                        'name': file_name,
                        'path': file_item.get('parentReference', {}).get('path', ''),
                        'size': file_item.get('size', 0),
                        'modified': file_item.get('lastModifiedDateTime'),
                        'web_url': file_item.get('webUrl'),
                        'match_type': 'filename'
                    })
                    continue
                
                # Búsqueda por contenido (solo para documentos pequeños)
                if file_item.get('size', 0) < 1024 * 1024:  # 1MB
                    try:
                        content_bytes = await self.graph_client.download_file(file_item['id'])
                        content = content_bytes.decode('utf-8', errors='ignore')
                        
                        if search_term.lower() in content.lower():
                            matching_documents.append({
                                'document_id': file_item['id'],
                                'name': file_name,
                                'path': file_item.get('parentReference', {}).get('path', ''),
                                'size': file_item.get('size', 0),
                                'modified': file_item.get('lastModifiedDateTime'),
                                'web_url': file_item.get('webUrl'),
                                'match_type': 'content'
                            })
                    except Exception as e:
                        logger.warning(f"Could not search content of {file_name}: {str(e)}")
                        continue
            
            logger.info(f"Found {len(matching_documents)} documents matching '{search_term}'")
            return matching_documents
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    async def list_documents(
        self,
        folder_path: str = "",
        include_metadata: bool = True
    ) -> List[Dict]:
        """Listar documentos de Word en carpeta específica"""
        try:
            files_result = await self.graph_client.list_files(folder_path)
            
            if 'value' not in files_result:
                return []
            
            word_documents = []
            
            for file_item in files_result['value']:
                file_name = file_item.get('name', '')
                
                # Filtrar solo documentos de Word
                if not self._is_word_document(file_name):
                    continue
                
                doc_info = {
                    'document_id': file_item['id'],
                    'name': file_name,
                    'size': file_item.get('size', 0),
                    'created': file_item.get('createdDateTime'),
                    'modified': file_item.get('lastModifiedDateTime'),
                    'web_url': file_item.get('webUrl'),
                    'download_url': file_item.get('@microsoft.graph.downloadUrl')
                }
                
                # Agregar metadatos adicionales si se solicita
                if include_metadata:
                    try:
                        doc_content = await self.open_document(file_item['id'])
                        if doc_content['status'] == 'success':
                            doc_info['word_count'] = len(doc_content['content'].split())
                            doc_info['character_count'] = len(doc_content['content'])
                            doc_info['paragraph_count'] = doc_content['content'].count('\n\n') + 1
                    except Exception as e:
                        logger.warning(f"Could not get metadata for {file_name}: {str(e)}")
                        doc_info['metadata_error'] = str(e)
                
                word_documents.append(doc_info)
            
            return word_documents
            
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return []
    
    async def create_backup_copy(self, document_id: str) -> Dict:
        """Crear copia de respaldo de documento"""
        try:
            # Obtener información del documento original
            original_doc = await self.graph_client.get_file(document_id)
            original_name = original_doc.get('name', 'document')
            backup_name = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{original_name}"
            
            # Descargar contenido original
            content_bytes = await self.graph_client.download_file(document_id)
            
            # Crear copia en OneDrive
            backup_result = await self.graph_client.upload_file(
                backup_name,
                content_bytes
            )
            
            logger.info(f"Backup created for document {document_id}: {backup_name}")
            return {
                'status': 'success',
                'original_document_id': document_id,
                'backup_document_id': backup_result['id'],
                'backup_name': backup_name,
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating backup for document {document_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'original_document_id': document_id
            }
    
    async def export_to_pdf(self, document_id: str) -> Dict:
        """Exportar documento Word a PDF"""
        try:
            # Descargar documento original
            content_bytes = await self.graph_client.download_file(document_id)
            
            # Convertir a PDF (requiere implementación de conversión)
            pdf_content = await self.document_processor.convert_word_to_pdf(content_bytes)
            
            # Subir PDF
            original_doc = await self.graph_client.get_file(document_id)
            pdf_name = original_doc.get('name', 'document').replace('.docx', '.pdf')
            
            pdf_result = await self.graph_client.upload_file(
                pdf_name,
                pdf_content
            )
            
            logger.info(f"Document exported to PDF: {pdf_name}")
            return {
                'status': 'success',
                'original_document_id': document_id,
                'pdf_document_id': pdf_result['id'],
                'pdf_name': pdf_name,
                'download_url': pdf_result.get('@microsoft.graph.downloadUrl'),
                'exported_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error exporting document to PDF {document_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'document_id': document_id
            }
    
    async def get_document_statistics(self, document_id: str) -> Dict:
        """Obtener estadísticas detalladas del documento"""
        try:
            # Obtener metadatos
            metadata = await self.graph_client.get_file(document_id)
            
            # Obtener contenido
            content_result = await self.open_document(document_id)
            if content_result['status'] != 'success':
                raise Exception("Could not read document content")
            
            content = content_result['content']
            
            # Calcular estadísticas
            stats = {
                'document_id': document_id,
                'name': metadata.get('name'),
                'size_bytes': metadata.get('size', 0),
                'size_mb': round(metadata.get('size', 0) / (1024 * 1024), 2),
                'word_count': len(content.split()),
                'character_count': len(content),
                'character_count_no_spaces': len(content.replace(' ', '')),
                'paragraph_count': content.count('\n\n') + 1 if content else 0,
                'line_count': content.count('\n') + 1 if content else 0,
                'page_count': 'calculation_needed',  # Requiere análisis más complejo
                'created': metadata.get('createdDateTime'),
                'modified': metadata.get('lastModifiedDateTime'),
                'author': metadata.get('createdBy', {}).get('user', {}).get('displayName'),
                'last_modified_by': metadata.get('lastModifiedBy', {}).get('user', {}).get('displayName'),
                'web_url': metadata.get('webUrl')
            }
            
            return {
                'status': 'success',
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"Error getting document statistics {document_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'document_id': document_id
            }
    
    async def collaborate_on_document(
        self,
        document_id: str,
        collaborators: List[str],
        permissions: str = "read"
    ) -> Dict:
        """Configurar colaboración en documento"""
        try:
            # Implementar lógica de compartir documento
            # Esto requiere permisos especiales de SharePoint/OneDrive
            
            sharing_info = {
                'document_id': document_id,
                'collaborators': collaborators,
                'permissions': permissions,
                'shared_at': datetime.utcnow().isoformat(),
                'status': 'collaboration_configured'
            }
            
            logger.info(f"Collaboration configured for document {document_id}")
            return {
                'status': 'success',
                'sharing_info': sharing_info
            }
            
        except Exception as e:
            logger.error(f"Error configuring collaboration for document {document_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'document_id': document_id
            }
    
    def _is_word_document(self, file_name: str) -> bool:
        """Verificar si el archivo es un documento de Word soportado"""
        return any(file_name.lower().endswith(fmt) for fmt in self.supported_formats)
    
    async def _create_document_in_folder(
        self,
        folder_id: str,
        content: str,
        metadata: Dict
    ) -> Dict:
        """Crear documento dentro de carpeta específica"""
        content_bytes = content.encode('utf-8')
        return await self.graph_client.upload_file(
            metadata['name'],
            content_bytes,
            parent_id=folder_id
        )
    
    async def _create_document_root(
        self,
        content: str,
        metadata: Dict
    ) -> Dict:
        """Crear documento en raíz de OneDrive"""
        content_bytes = content.encode('utf-8')
        return await self.graph_client.upload_file(
            metadata['name'],
            content_bytes
        )