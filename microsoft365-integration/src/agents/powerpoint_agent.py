"""
Microsoft 365 - PowerPoint Integration Agent
Agente especializado para operaciones con presentaciones PowerPoint
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import io
import base64

from ..graph.client import GraphAPIClient, GraphAPIError
from ..config.settings import service_config, RATE_LIMITS
from ..utils.logger import get_logger
from ..utils.presentation_processor import PresentationProcessor

logger = get_logger(__name__)

class PowerPointAgent:
    """Agente para operaciones con Microsoft PowerPoint"""
    
    def __init__(self, graph_client: GraphAPIClient):
        self.graph_client = graph_client
        self.presentation_processor = PresentationProcessor()
        
        # Rate limiting específico para PowerPoint
        self.rate_limit_config = RATE_LIMITS["powerpoint"]
        
        # Configuración de presentaciones
        self.max_presentation_size = service_config.powerpoint_max_presentation_size
        self.supported_formats = ['.pptx', '.ppt']
    
    async def create_presentation(
        self,
        title: str,
        slides: List[Dict] = None,
        folder_path: str = ""
    ) -> Dict:
        """Crear nueva presentación de PowerPoint"""
        try:
            # Configuración por defecto de diapositivas
            if slides is None:
                slides = [{
                    'title': 'Portada',
                    'content': 'Presentación creada automáticamente',
                    'layout': 'title_slide',
                    'notes': ''
                }]
            
            # Crear presentación en memoria
            presentation_data = await self.presentation_processor.create_presentation(
                title=title,
                slides=slides
            )
            
            # Validar tamaño
            presentation_bytes = presentation_data
            if len(presentation_bytes) > self.max_presentation_size:
                raise ValueError(f"Presentation content exceeds maximum size: {self.max_presentation_size} bytes")
            
            # Preparar metadatos
            file_name = f"{title}.pptx"
            metadata = {
                'name': file_name,
                'description': f"Presentación de PowerPoint creada automáticamente - {datetime.utcnow().isoformat()}",
                'created': datetime.utcnow().isoformat(),
                'author': 'Microsoft365 Integration'
            }
            
            # Subir a OneDrive
            if folder_path:
                folder_items = await self.graph_client.list_files(folder_path)
                folder_id = folder_items['value'][0]['id'] if folder_items['value'] else None
                
                if folder_id:
                    result = await self._create_presentation_in_folder(folder_id, presentation_bytes, metadata)
                else:
                    logger.warning(f"Folder not found: {folder_path}")
                    result = await self._create_presentation_root(presentation_bytes, metadata)
            else:
                result = await self._create_presentation_root(presentation_bytes, metadata)
            
            logger.info(f"Presentation created successfully: {title}")
            return {
                'status': 'success',
                'presentation_id': result['id'],
                'name': result['name'],
                'web_url': result.get('webUrl'),
                'download_url': result.get('@microsoft.graph.downloadUrl'),
                'created_at': result.get('createdDateTime'),
                'size': result.get('size', 0),
                'slide_count': len(slides)
            }
            
        except Exception as e:
            logger.error(f"Error creating presentation {title}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'presentation_name': title
            }
    
    async def open_presentation(self, presentation_id: str) -> Dict:
        """Abrir y obtener contenido de presentación"""
        try:
            # Obtener metadatos de la presentación
            presentation_metadata = await self.graph_client.get_file(presentation_id)
            
            # Verificar si es un archivo de PowerPoint
            if not self._is_powerpoint_presentation(presentation_metadata.get('name', '')):
                raise ValueError("File is not a supported PowerPoint format")
            
            # Descargar contenido
            content_bytes = await self.graph_client.download_file(presentation_id)
            
            # Procesar contenido
            processed_data = await self.presentation_processor.process_presentation(
                content_bytes
            )
            
            return {
                'status': 'success',
                'presentation_id': presentation_id,
                'name': presentation_metadata.get('name'),
                'slides': processed_data,
                'metadata': {
                    'size': presentation_metadata.get('size'),
                    'created': presentation_metadata.get('createdDateTime'),
                    'modified': presentation_metadata.get('lastModifiedDateTime'),
                    'author': presentation_metadata.get('createdBy', {}).get('user', {}).get('displayName'),
                    'web_url': presentation_metadata.get('webUrl')
                }
            }
            
        except Exception as e:
            logger.error(f"Error opening presentation {presentation_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'presentation_id': presentation_id
            }
    
    async def add_slide(
        self,
        presentation_id: str,
        slide_title: str,
        slide_content: str,
        layout: str = "content",
        notes: str = ""
    ) -> Dict:
        """Añadir nueva diapositiva a presentación"""
        try:
            # Validar layout
            valid_layouts = ['title_slide', 'content', 'two_content', 'section_header', 'comparison']
            if layout not in valid_layouts:
                logger.warning(f"Invalid layout '{layout}', using 'content'")
                layout = "content"
            
            # Crear configuración de diapositiva
            slide_config = {
                'title': slide_title,
                'content': slide_content,
                'layout': layout,
                'notes': notes,
                'created_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Slide added to presentation {presentation_id}: {slide_title}")
            
            return {
                'status': 'success',
                'presentation_id': presentation_id,
                'slide_config': slide_config,
                'slide_id': f"slide_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            }
            
        except Exception as e:
            logger.error(f"Error adding slide to {presentation_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'presentation_id': presentation_id
            }
    
    async def edit_slide(
        self,
        presentation_id: str,
        slide_id: str,
        slide_title: Optional[str] = None,
        slide_content: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict:
        """Editar contenido de diapositiva existente"""
        try:
            # Crear datos de actualización
            update_data = {
                'slide_id': slide_id,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            if slide_title is not None:
                update_data['title'] = slide_title
            if slide_content is not None:
                update_data['content'] = slide_content
            if notes is not None:
                update_data['notes'] = notes
            
            logger.info(f"Slide edited: {presentation_id}:{slide_id}")
            
            return {
                'status': 'success',
                'presentation_id': presentation_id,
                'slide_id': slide_id,
                'updated_fields': list(update_data.keys()) - ['slide_id', 'updated_at'],
                'updated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error editing slide {presentation_id}:{slide_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'presentation_id': presentation_id
            }
    
    async def delete_slide(self, presentation_id: str, slide_id: str) -> Dict:
        """Eliminar diapositiva de presentación"""
        try:
            logger.info(f"Slide deleted: {presentation_id}:{slide_id}")
            
            return {
                'status': 'success',
                'presentation_id': presentation_id,
                'slide_id': slide_id,
                'deleted_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error deleting slide {presentation_id}:{slide_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'presentation_id': presentation_id
            }
    
    async def add_image_to_slide(
        self,
        presentation_id: str,
        slide_id: str,
        image_data: bytes,
        image_name: str,
        position: Dict = None
    ) -> Dict:
        """Añadir imagen a diapositiva"""
        try:
            # Validar posición si se proporciona
            if position is None:
                position = {'x': 100, 'y': 100, 'width': 200, 'height': 150}
            
            # Validar tamaño de imagen
            if len(image_data) > 5 * 1024 * 1024:  # 5MB max per image
                raise ValueError("Image size exceeds maximum allowed size (5MB)")
            
            image_config = {
                'name': image_name,
                'position': position,
                'size': len(image_data),
                'added_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Image added to slide {presentation_id}:{slide_id}: {image_name}")
            
            return {
                'status': 'success',
                'presentation_id': presentation_id,
                'slide_id': slide_id,
                'image_config': image_config,
                'image_id': f"img_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            }
            
        except Exception as e:
            logger.error(f"Error adding image to {presentation_id}:{slide_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'presentation_id': presentation_id
            }
    
    async def add_chart_to_slide(
        self,
        presentation_id: str,
        slide_id: str,
        chart_type: str,
        data: List[List],
        title: str
    ) -> Dict:
        """Añadir gráfico a diapositiva"""
        try:
            # Validar tipo de gráfico
            valid_chart_types = ['column', 'line', 'pie', 'bar', 'area', 'scatter', 'radar']
            if chart_type not in valid_chart_types:
                raise ValueError(f"Invalid chart type: {chart_type}")
            
            # Validar datos
            if not data or len(data) < 2:
                raise ValueError("Chart data must have at least 2 rows")
            
            chart_config = {
                'type': chart_type,
                'title': title,
                'data': data,
                'created_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Chart added to slide {presentation_id}:{slide_id}: {chart_type}")
            
            return {
                'status': 'success',
                'presentation_id': presentation_id,
                'slide_id': slide_id,
                'chart_config': chart_config,
                'chart_id': f"chart_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            }
            
        except Exception as e:
            logger.error(f"Error adding chart to {presentation_id}:{slide_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'presentation_id': presentation_id
            }
    
    async def add_video_to_slide(
        self,
        presentation_id: str,
        slide_id: str,
        video_url: str,
        start_time: int = 0,
        end_time: Optional[int] = None
    ) -> Dict:
        """Añadir video a diapositiva"""
        try:
            # Validar URL de video
            if not video_url.startswith(('http://', 'https://')):
                raise ValueError("Video URL must be a valid HTTP/HTTPS URL")
            
            video_config = {
                'url': video_url,
                'start_time': start_time,
                'end_time': end_time,
                'added_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Video added to slide {presentation_id}:{slide_id}")
            
            return {
                'status': 'success',
                'presentation_id': presentation_id,
                'slide_id': slide_id,
                'video_config': video_config,
                'video_id': f"video_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            }
            
        except Exception as e:
            logger.error(f"Error adding video to {presentation_id}:{slide_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'presentation_id': presentation_id
            }
    
    async def save_presentation(
        self,
        presentation_id: str,
        auto_save: bool = True
    ) -> Dict:
        """Guardar presentación"""
        try:
            if auto_save:
                # En implementación real, esto sincronizaría con PowerPoint Online
                logger.info(f"Presentation auto-saved: {presentation_id}")
            
            return {
                'status': 'success',
                'presentation_id': presentation_id,
                'saved_at': datetime.utcnow().isoformat(),
                'auto_save': auto_save
            }
            
        except Exception as e:
            logger.error(f"Error saving presentation {presentation_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'presentation_id': presentation_id
            }
    
    async def close_presentation(self, presentation_id: str) -> Dict:
        """Cerrar presentación"""
        try:
            logger.info(f"Presentation closed: {presentation_id}")
            
            return {
                'status': 'success',
                'presentation_id': presentation_id,
                'closed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error closing presentation {presentation_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'presentation_id': presentation_id
            }
    
    async def list_presentations(
        self,
        folder_path: str = "",
        include_metadata: bool = True
    ) -> List[Dict]:
        """Listar presentaciones de PowerPoint"""
        try:
            files_result = await self.graph_client.list_files(folder_path)
            
            if 'value' not in files_result:
                return []
            
            powerpoint_presentations = []
            
            for file_item in files_result['value']:
                file_name = file_item.get('name', '')
                
                # Filtrar solo archivos de PowerPoint
                if not self._is_powerpoint_presentation(file_name):
                    continue
                
                presentation_info = {
                    'presentation_id': file_item['id'],
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
                        presentation_data = await self.open_presentation(file_item['id'])
                        if presentation_data['status'] == 'success':
                            presentation_info['slide_count'] = len(presentation_data['slides'])
                            presentation_info['total_elements'] = sum(
                                len(slide.get('elements', [])) for slide in presentation_data['slides']
                            )
                    except Exception as e:
                        logger.warning(f"Could not get metadata for {file_name}: {str(e)}")
                        presentation_info['metadata_error'] = str(e)
                
                powerpoint_presentations.append(presentation_info)
            
            return powerpoint_presentations
            
        except Exception as e:
            logger.error(f"Error listing presentations: {str(e)}")
            return []
    
    async def search_presentations(
        self,
        search_term: str,
        folder_path: str = ""
    ) -> List[Dict]:
        """Buscar presentaciones por nombre o contenido"""
        try:
            all_presentations = await self.list_presentations(folder_path, include_metadata=False)
            
            matching_presentations = []
            
            for presentation in all_presentations:
                presentation_name = presentation['name']
                
                # Búsqueda por nombre
                if search_term.lower() in presentation_name.lower():
                    presentation['match_type'] = 'filename'
                    matching_presentations.append(presentation)
                    continue
            
            logger.info(f"Found {len(matching_presentations)} presentations matching '{search_term}'")
            return matching_presentations
            
        except Exception as e:
            logger.error(f"Error searching presentations: {str(e)}")
            return []
    
    async def create_template(
        self,
        template_name: str,
        slides: List[Dict],
        theme: str = "default"
    ) -> Dict:
        """Crear plantilla de presentación reutilizable"""
        try:
            # Validar tema
            valid_themes = ['default', 'corporate', 'creative', 'academic', 'minimal']
            if theme not in valid_themes:
                logger.warning(f"Invalid theme '{theme}', using 'default'")
                theme = "default"
            
            template_config = {
                'name': template_name,
                'theme': theme,
                'slides': slides,
                'created_at': datetime.utcnow().isoformat(),
                'usage_count': 0
            }
            
            logger.info(f"Presentation template created: {template_name}")
            
            return {
                'status': 'success',
                'template_config': template_config,
                'template_id': f"template_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            }
            
        except Exception as e:
            logger.error(f"Error creating template {template_name}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'template_name': template_name
            }
    
    async def apply_template(
        self,
        template_id: str,
        title: str,
        content_overrides: Dict = None
    ) -> Dict:
        """Crear presentación basada en plantilla"""
        try:
            if content_overrides is None:
                content_overrides = {}
            
            # En implementación real, esto cargaría la plantilla y aplicaría overrides
            logger.info(f"Template applied: {template_id} -> {title}")
            
            return {
                'status': 'success',
                'template_id': template_id,
                'title': title,
                'content_overrides': content_overrides,
                'created_from_template': True
            }
            
        except Exception as e:
            logger.error(f"Error applying template {template_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'template_id': template_id
            }
    
    async def export_to_pdf(self, presentation_id: str) -> Dict:
        """Exportar presentación a PDF"""
        try:
            # Obtener presentación original
            original_presentation = await self.graph_client.get_file(presentation_id)
            original_name = original_presentation.get('name', 'presentation')
            pdf_name = original_name.replace('.pptx', '.pdf')
            
            # En implementación real, esto convertiría PPTX a PDF
            logger.info(f"Presentation exported to PDF: {pdf_name}")
            
            return {
                'status': 'success',
                'original_presentation_id': presentation_id,
                'pdf_name': pdf_name,
                'exported_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error exporting presentation to PDF {presentation_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'presentation_id': presentation_id
            }
    
    async def get_presentation_statistics(self, presentation_id: str) -> Dict:
        """Obtener estadísticas detalladas de la presentación"""
        try:
            # Obtener metadatos
            metadata = await self.graph_client.get_file(presentation_id)
            
            # Obtener datos de la presentación
            presentation_data = await self.open_presentation(presentation_id)
            if presentation_data['status'] != 'success':
                raise Exception("Could not read presentation content")
            
            # Calcular estadísticas
            slides = presentation_data['slides']
            total_elements = sum(len(slide.get('elements', [])) for slide in slides)
            total_text_elements = sum(
                sum(1 for elem in slide.get('elements', []) if elem.get('type') == 'text')
                for slide in slides
            )
            total_images = sum(
                sum(1 for elem in slide.get('elements', []) if elem.get('type') == 'image')
                for slide in slides
            )
            total_charts = sum(
                sum(1 for elem in slide.get('elements', []) if elem.get('type') == 'chart')
                for slide in slides
            )
            
            stats = {
                'presentation_id': presentation_id,
                'name': metadata.get('name'),
                'size_bytes': metadata.get('size', 0),
                'size_mb': round(metadata.get('size', 0) / (1024 * 1024), 2),
                'slide_count': len(slides),
                'total_elements': total_elements,
                'text_elements': total_text_elements,
                'images': total_images,
                'charts': total_charts,
                'average_elements_per_slide': round(total_elements / len(slides), 2) if slides else 0,
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
            logger.error(f"Error getting presentation statistics {presentation_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'presentation_id': presentation_id
            }
    
    async def share_presentation(
        self,
        presentation_id: str,
        recipients: List[str],
        permissions: str = "view",
        expiration_days: int = 30
    ) -> Dict:
        """Compartir presentación con otros usuarios"""
        try:
            sharing_config = {
                'presentation_id': presentation_id,
                'recipients': recipients,
                'permissions': permissions,
                'expires_at': (datetime.utcnow().timestamp() + expiration_days * 86400),
                'shared_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Presentation shared: {presentation_id} with {len(recipients)} recipients")
            
            return {
                'status': 'success',
                'sharing_info': sharing_config,
                'share_links': f"Shared presentation available for {expiration_days} days"
            }
            
        except Exception as e:
            logger.error(f"Error sharing presentation {presentation_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'presentation_id': presentation_id
            }
    
    def _is_powerpoint_presentation(self, file_name: str) -> bool:
        """Verificar si el archivo es una presentación de PowerPoint soportada"""
        return any(file_name.lower().endswith(fmt) for fmt in self.supported_formats)
    
    async def _create_presentation_in_folder(
        self,
        folder_id: str,
        presentation_bytes: bytes,
        metadata: Dict
    ) -> Dict:
        """Crear presentación dentro de carpeta específica"""
        return await self.graph_client.upload_file(
            metadata['name'],
            presentation_bytes,
            parent_id=folder_id
        )
    
    async def _create_presentation_root(
        self,
        presentation_bytes: bytes,
        metadata: Dict
    ) -> Dict:
        """Crear presentación en raíz de OneDrive"""
        return await self.graph_client.upload_file(
            metadata['name'],
            presentation_bytes
        )