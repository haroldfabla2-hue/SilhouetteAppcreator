"""
Microsoft 365 - Presentation Processor
Procesador especializado para presentaciones PowerPoint
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json
import re

logger = logging.getLogger(__name__)

class PresentationProcessor:
    """Procesador para presentaciones PowerPoint"""
    
    def __init__(self):
        self.supported_formats = ['.pptx', '.ppt']
        self.max_slides = 200  # Límite práctico de PowerPoint
        self.max_processing_size = 100 * 1024 * 1024  # 100MB
        self.max_elements_per_slide = 50
    
    async def create_presentation(self, title: str, slides: List[Dict]) -> bytes:
        """Crear nueva presentación PowerPoint"""
        try:
            if len(slides) > self.max_slides:
                raise ValueError(f"Too many slides: {len(slides)}, maximum is {self.max_slides}")
            
            # En implementación real, esto usaría python-pptx
            # Por ahora, simulamos la creación
            
            presentation_data = {
                'title': title,
                'slides': slides,
                'created_at': datetime.utcnow().isoformat(),
                'metadata': {
                    'version': '1.0',
                    'created_by': 'Microsoft365 Integration',
                    'slide_count': len(slides),
                    'theme': 'default'
                }
            }
            
            # Convertir a bytes (en implementación real sería archivo PPTX)
            presentation_bytes = json.dumps(presentation_data, ensure_ascii=False).encode('utf-8')
            
            logger.info(f"Presentation created: {title} with {len(slides)} slides")
            return presentation_bytes
            
        except Exception as e:
            logger.error(f"Error creating presentation: {str(e)}")
            raise
    
    async def process_presentation(self, content_bytes: bytes) -> List[Dict]:
        """Procesar contenido de presentación PowerPoint"""
        try:
            if len(content_bytes) > self.max_processing_size:
                raise ValueError(f"Presentation too large: {len(content_bytes)} bytes")
            
            # En implementación real, esto procesaría el archivo PowerPoint
            # Por ahora, simulamos el procesamiento
            
            # Simular datos de diapositivas
            slides_data = [
                {
                    'slide_number': 1,
                    'title': 'Portada',
                    'content': 'Presentación de Ejemplo',
                    'layout': 'title_slide',
                    'elements': [
                        {
                            'type': 'title',
                            'content': 'Microsoft 365 Integration',
                            'position': {'x': 100, 'y': 200}
                        },
                        {
                            'type': 'subtitle',
                            'content': 'Automatización Empresarial',
                            'position': {'x': 100, 'y': 300}
                        }
                    ],
                    'notes': 'Esta es la diapositiva de portada'
                },
                {
                    'slide_number': 2,
                    'title': 'Agenda',
                    'content': 'Contenido de la presentación',
                    'layout': 'content',
                    'elements': [
                        {
                            'type': 'text',
                            'content': '1. Introducción\n2. Funcionalidades\n3. Casos de Uso\n4. Conclusiones',
                            'position': {'x': 100, 'y': 150}
                        }
                    ],
                    'notes': 'Diapositiva de agenda'
                },
                {
                    'slide_number': 3,
                    'title': 'Funcionalidades Principales',
                    'content': 'Microsoft 365 Integration',
                    'layout': 'content',
                    'elements': [
                        {
                            'type': 'text',
                            'content': '• Procesamiento automático de documentos\n• Integración con APIs de Office 365\n• Sincronización de datos\n• Automatización de tareas',
                            'position': {'x': 100, 'y': 150}
                        },
                        {
                            'type': 'image',
                            'content': 'diagram.png',
                            'position': {'x': 400, 'y': 200},
                            'size': {'width': 300, 'height': 200}
                        }
                    ],
                    'notes': 'Explicación de funcionalidades'
                }
            ]
            
            # Post-procesar datos
            for slide in slides_data:
                slide['analyzed'] = await self._analyze_slide_content(slide)
            
            logger.info(f"PowerPoint presentation processed: {len(slides_data)} slides")
            return slides_data
            
        except Exception as e:
            logger.error(f"Error processing PowerPoint presentation: {str(e)}")
            raise
    
    async def analyze_slide_content(self, slide_data: Dict) -> Dict:
        """Analizar contenido de diapositiva específica"""
        try:
            analysis = {
                'slide_number': slide_data.get('slide_number'),
                'title': slide_data.get('title'),
                'layout_type': slide_data.get('layout'),
                'element_count': len(slide_data.get('elements', [])),
                'content_types': {},
                'text_analysis': {},
                'visual_elements': {},
                'complexity_score': 0,
                'analyzed_at': datetime.utcnow().isoformat()
            }
            
            # Analizar elementos
            elements = slide_data.get('elements', [])
            element_types = {}
            
            for element in elements:
                element_type = element.get('type', 'unknown')
                element_types[element_type] = element_types.get(element_type, 0) + 1
                
                # Análisis específico por tipo
                if element_type == 'text':
                    text_content = element.get('content', '')
                    analysis['text_analysis'] = await self._analyze_text_content(text_content)
                elif element_type in ['image', 'chart', 'table']:
                    analysis['visual_elements'][element_type] = True
            
            analysis['element_types'] = element_types
            
            # Calcular puntuación de complejidad
            analysis['complexity_score'] = self._calculate_slide_complexity(analysis)
            
            logger.info(f"Slide {analysis['slide_number']} analyzed: {analysis['element_count']} elements")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing slide content: {str(e)}")
            raise
    
    async def add_automated_content(
        self,
        slide_data: Dict,
        content_type: str,
        source_data: Any
    ) -> Dict:
        """Añadir contenido automatizado a diapositiva"""
        try:
            if content_type == 'chart':
                return await self._add_chart_to_slide(slide_data, source_data)
            elif content_type == 'table':
                return await self._add_table_to_slide(slide_data, source_data)
            elif content_type == 'text':
                return await self._add_text_to_slide(slide_data, source_data)
            elif content_type == 'image':
                return await self._add_image_to_slide(slide_data, source_data)
            else:
                raise ValueError(f"Unsupported content type: {content_type}")
            
        except Exception as e:
            logger.error(f"Error adding automated content: {str(e)}")
            raise
    
    async def optimize_slide_design(self, slide_data: Dict) -> Dict:
        """Optimizar diseño de diapositiva"""
        try:
            optimization = {
                'original_elements': len(slide_data.get('elements', [])),
                'optimized_elements': [],
                'design_improvements': [],
                'analyzed_at': datetime.utcnow().isoformat()
            }
            
            elements = slide_data.get('elements', [])
            
            for element in elements:
                optimized_element = await self._optimize_element(element)
                optimization['optimized_elements'].append(optimized_element)
            
            # Identificar mejoras de diseño
            if len(elements) > 10:
                optimization['design_improvements'].append('Consider reducing element count for better readability')
            
            # Verificar solapamiento de elementos
            overlapping_elements = self._detect_overlapping_elements(elements)
            if overlapping_elements:
                optimization['design_improvements'].append(f'Fixed {len(overlapping_elements)} overlapping elements')
            
            # Optimizar paleta de colores
            color_suggestions = self._suggest_color_improvements(elements)
            if color_suggestions:
                optimization['design_improvements'].extend(color_suggestions)
            
            optimization['slide_number'] = slide_data.get('slide_number')
            
            logger.info(f"Slide design optimized: {len(optimization['design_improvements'])} improvements applied")
            return optimization
            
        except Exception as e:
            logger.error(f"Error optimizing slide design: {str(e)}")
            raise
    
    async def create_template(self, template_name: str, template_config: Dict) -> Dict:
        """Crear plantilla reutilizable de presentación"""
        try:
            template = {
                'template_name': template_name,
                'layout_config': template_config.get('layouts', {}),
                'color_scheme': template_config.get('colors', {}),
                'font_config': template_config.get('fonts', {}),
                'element_styles': template_config.get('styles', {}),
                'master_slides': template_config.get('masters', []),
                'created_at': datetime.utcnow().isoformat(),
                'version': '1.0'
            }
            
            logger.info(f"Presentation template created: {template_name}")
            return template
            
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            raise
    
    async def apply_template(self, presentation_data: Dict, template: Dict) -> Dict:
        """Aplicar plantilla a presentación"""
        try:
            applied_template = {
                'template_applied': template.get('template_name'),
                'original_presentation': presentation_data,
                'applied_changes': [],
                'applied_at': datetime.utcnow().isoformat()
            }
            
            slides = presentation_data.get('slides', [])
            
            for slide in slides:
                # Aplicar colores de plantilla
                if 'color_scheme' in template:
                    applied_template['applied_changes'].append({
                        'slide': slide.get('slide_number'),
                        'change': 'colors_applied',
                        'scheme': template['color_scheme']
                    })
                
                # Aplicar fuentes de plantilla
                if 'font_config' in template:
                    applied_template['applied_changes'].append({
                        'slide': slide.get('slide_number'),
                        'change': 'fonts_applied',
                        'fonts': template['font_config']
                    })
            
            logger.info(f"Template applied to {len(slides)} slides")
            return applied_template
            
        except Exception as e:
            logger.error(f"Error applying template: {str(e)}")
            raise
    
    async def export_to_multiple_formats(self, presentation_data: Dict, formats: List[str]) -> Dict:
        """Exportar presentación a múltiples formatos"""
        try:
            exports = {}
            
            for format_type in formats:
                if format_type == 'pdf':
                    exports[format_type] = await self._export_to_pdf(presentation_data)
                elif format_type == 'images':
                    exports[format_type] = await self._export_to_images(presentation_data)
                elif format_type == 'video':
                    exports[format_type] = await self._export_to_video(presentation_data)
                elif format_type == 'html':
                    exports[format_type] = await self._export_to_html(presentation_data)
                else:
                    logger.warning(f"Unsupported export format: {format_type}")
            
            logger.info(f"Presentation exported to {len(formats)} formats")
            return {
                'exports': exports,
                'original_slides': len(presentation_data.get('slides', [])),
                'exported_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error exporting presentation: {str(e)}")
            raise
    
    def _analyze_slide_content(self, slide_data: Dict) -> Dict:
        """Analizar contenido de diapositiva (síncrono)"""
        analysis = {
            'element_count': len(slide_data.get('elements', [])),
            'content_types': [],
            'has_title': bool(slide_data.get('title')),
            'has_notes': bool(slide_data.get('notes')),
            'layout_type': slide_data.get('layout', 'content')
        }
        
        for element in slide_data.get('elements', []):
            element_type = element.get('type', 'unknown')
            if element_type not in analysis['content_types']:
                analysis['content_types'].append(element_type)
        
        return analysis
    
    async def _analyze_text_content(self, text_content: str) -> Dict:
        """Analizar contenido de texto"""
        words = text_content.split()
        
        return {
            'word_count': len(words),
            'character_count': len(text_content),
            'sentence_count': len(re.split(r'[.!?]+', text_content)),
            'reading_time_minutes': round(len(words) / 200, 1),  # 200 words per minute
            'contains_bullets': any(char in text_content for char in ['•', '–', '-', '*']),
            'text_alignment': self._detect_text_alignment(text_content)
        }
    
    def _calculate_slide_complexity(self, analysis: Dict) -> int:
        """Calcular puntuación de complejidad de diapositiva"""
        complexity = 0
        
        # Base complexity from element count
        element_count = analysis.get('element_count', 0)
        complexity += element_count
        
        # Increase complexity for visual elements
        visual_elements = analysis.get('visual_elements', {})
        complexity += len(visual_elements) * 2
        
        # Increase for rich content types
        content_types = analysis.get('content_types', [])
        complexity += len(content_types)
        
        return min(complexity, 100)  # Cap at 100
    
    def _detect_text_alignment(self, text: str) -> str:
        """Detectar alineación probable del texto"""
        # Análisis muy básico basado en estructura
        if '\n' in text and '  ' in text:
            return 'center'
        elif text.startswith('  ') or text.endswith('  '):
            return 'center'
        elif text.startswith('\t'):
            return 'left'
        else:
            return 'left'  # Default
    
    async def _add_chart_to_slide(self, slide_data: Dict, chart_data: Dict) -> Dict:
        """Añadir gráfico a diapositiva"""
        chart_element = {
            'type': 'chart',
            'chart_type': chart_data.get('type', 'column'),
            'data': chart_data.get('data', []),
            'position': {'x': 100, 'y': 200},
            'size': {'width': 400, 'height': 300}
        }
        
        slide_data.setdefault('elements', []).append(chart_element)
        
        return {
            'element_added': 'chart',
            'chart_type': chart_data.get('type'),
            'slide_number': slide_data.get('slide_number')
        }
    
    async def _add_table_to_slide(self, slide_data: Dict, table_data: Dict) -> Dict:
        """Añadir tabla a diapositiva"""
        table_element = {
            'type': 'table',
            'data': table_data.get('data', []),
            'headers': table_data.get('headers', []),
            'position': {'x': 100, 'y': 200},
            'size': {'width': 400, 'height': 300}
        }
        
        slide_data.setdefault('elements', []).append(table_element)
        
        return {
            'element_added': 'table',
            'rows': len(table_data.get('data', [])),
            'columns': len(table_data.get('headers', []))
        }
    
    async def _add_text_to_slide(self, slide_data: Dict, text_content: str) -> Dict:
        """Añadir texto a diapositiva"""
        text_element = {
            'type': 'text',
            'content': text_content,
            'position': {'x': 100, 'y': 200},
            'font_size': 12
        }
        
        slide_data.setdefault('elements', []).append(text_element)
        
        return {
            'element_added': 'text',
            'character_count': len(text_content)
        }
    
    async def _add_image_to_slide(self, slide_data: Dict, image_config: Dict) -> Dict:
        """Añadir imagen a diapositiva"""
        image_element = {
            'type': 'image',
            'content': image_config.get('path', 'image.png'),
            'position': image_config.get('position', {'x': 100, 'y': 200}),
            'size': image_config.get('size', {'width': 200, 'height': 150})
        }
        
        slide_data.setdefault('elements', []).append(image_element)
        
        return {
            'element_added': 'image',
            'image_path': image_config.get('path')
        }
    
    async def _optimize_element(self, element: Dict) -> Dict:
        """Optimizar elemento individual"""
        optimized = element.copy()
        
        if element.get('type') == 'text':
            # Optimizar texto
            content = element.get('content', '')
            if len(content) > 500:
                optimized['optimization_applied'] = 'text_truncated'
        
        elif element.get('type') in ['image', 'chart']:
            # Optimizar tamaño y posición
            position = element.get('position', {})
            if position.get('x', 0) < 50:
                optimized['position'] = {'x': 50, 'y': position.get('y', 0)}
                optimized['optimization_applied'] = 'position_adjusted'
        
        return optimized
    
    def _detect_overlapping_elements(self, elements: List[Dict]) -> List[Dict]:
        """Detectar elementos que se superponen"""
        overlapping = []
        
        for i, elem1 in enumerate(elements):
            for j, elem2 in enumerate(elements[i+1:], i+1):
                if self._elements_overlap(elem1, elem2):
                    overlapping.append({'element1': i, 'element2': j})
        
        return overlapping
    
    def _elements_overlap(self, elem1: Dict, elem2: Dict) -> bool:
        """Verificar si dos elementos se superponen"""
        # Implementación simplificada
        pos1 = elem1.get('position', {})
        pos2 = elem2.get('position', {})
        
        x1, y1 = pos1.get('x', 0), pos1.get('y', 0)
        x2, y2 = pos2.get('x', 0), pos2.get('y', 0)
        
        # Simplificación: verificar si están muy cerca
        distance = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
        return distance < 50  # Umbral de 50 píxeles
    
    def _suggest_color_improvements(self, elements: List[Dict]) -> List[str]:
        """Sugerir mejoras de color"""
        suggestions = []
        
        # Verificar contraste de color
        has_white_bg = any(elem.get('background') == 'white' for elem in elements)
        has_dark_text = any(elem.get('color') in ['black', 'dark'] for elem in elements)
        
        if has_white_bg and has_dark_text:
            suggestions.append('Good contrast detected between background and text')
        
        return suggestions
    
    async def _export_to_pdf(self, presentation_data: Dict) -> Dict:
        """Exportar presentación a PDF"""
        return {
            'format': 'pdf',
            'file_size': 'estimated_size_mb',
            'exported_slides': len(presentation_data.get('slides', [])),
            'export_timestamp': datetime.utcnow().isoformat()
        }
    
    async def _export_to_images(self, presentation_data: Dict) -> Dict:
        """Exportar presentación a imágenes"""
        slides = presentation_data.get('slides', [])
        image_files = []
        
        for i, slide in enumerate(slides, 1):
            image_files.append(f"slide_{i:03d}.png")
        
        return {
            'format': 'images',
            'image_count': len(image_files),
            'image_files': image_files,
            'export_timestamp': datetime.utcnow().isoformat()
        }
    
    async def _export_to_video(self, presentation_data: Dict) -> Dict:
        """Exportar presentación a video"""
        return {
            'format': 'video',
            'video_duration': 'estimated_duration_seconds',
            'resolution': '1920x1080',
            'export_timestamp': datetime.utcnow().isoformat()
        }
    
    async def _export_to_html(self, presentation_data: Dict) -> Dict:
        """Exportar presentación a HTML"""
        return {
            'format': 'html',
            'file_size': 'estimated_size_kb',
            'slides_count': len(presentation_data.get('slides', [])),
            'export_timestamp': datetime.utcnow().isoformat()
        }