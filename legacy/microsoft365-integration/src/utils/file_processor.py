"""
Microsoft 365 - File Processor
Procesador universal para archivos y operaciones de almacenamiento
"""

import logging
import os
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
from pathlib import Path
import mimetypes

logger = logging.getLogger(__name__)

class FileProcessor:
    """Procesador universal para archivos de todo tipo"""
    
    def __init__(self):
        self.supported_extensions = {
            'documents': ['.docx', '.doc', '.pdf', '.txt', '.rtf', '.odt'],
            'spreadsheets': ['.xlsx', '.xls', '.csv', '.ods'],
            'presentations': ['.pptx', '.ppt', '.odp'],
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
            'videos': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv'],
            'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'],
            'archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
            'code': ['.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml']
        }
        
        self.max_file_sizes = {
            'image': 10 * 1024 * 1024,  # 10MB
            'video': 500 * 1024 * 1024,  # 500MB
            'audio': 50 * 1024 * 1024,   # 50MB
            'document': 25 * 1024 * 1024, # 25MB
            'archive': 100 * 1024 * 1024, # 100MB
            'default': 50 * 1024 * 1024   # 50MB
        }
        
        logger.info("File processor initialized with universal file support")
    
    async def process_file(self, file_path: str, file_content: bytes) -> Dict:
        """Procesar archivo de cualquier tipo"""
        try:
            file_extension = Path(file_path).suffix.lower()
            file_category = self._categorize_file(file_extension)
            file_size = len(file_content)
            
            # Validar tamaño
            max_size = self.max_file_sizes.get(file_category, self.max_file_sizes['default'])
            if file_size > max_size:
                raise ValueError(f"File too large: {file_size} bytes, max allowed: {max_size} bytes")
            
            # Calcular hash del archivo
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Obtener metadatos básicos
            metadata = await self._extract_file_metadata(file_path, file_content, file_extension)
            
            # Procesar según tipo de archivo
            if file_category == 'documents':
                processed_content = await self._process_document(file_content, file_extension)
            elif file_category == 'spreadsheets':
                processed_content = await self._process_spreadsheet(file_content, file_extension)
            elif file_category == 'images':
                processed_content = await self._process_image(file_content, file_extension)
            elif file_category == 'videos':
                processed_content = await self._process_video(file_content, file_extension)
            elif file_category == 'audio':
                processed_content = await self._process_audio(file_content, file_extension)
            else:
                processed_content = await self._process_generic_file(file_content, file_extension)
            
            result = {
                'file_path': file_path,
                'file_extension': file_extension,
                'file_category': file_category,
                'file_size': file_size,
                'file_hash': file_hash,
                'metadata': metadata,
                'processed_content': processed_content,
                'mime_type': mimetypes.guess_type(file_path)[0],
                'processed_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"File processed successfully: {file_path} ({file_category})")
            return result
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            raise
    
    async def convert_file(
        self,
        source_file: bytes,
        source_extension: str,
        target_extension: str,
        conversion_options: Optional[Dict] = None
    ) -> bytes:
        """Convertir archivo a otro formato"""
        try:
            source_category = self._categorize_file(source_extension)
            target_category = self._categorize_file(target_extension)
            
            # Verificar compatibilidad de conversión
            if not self._is_conversion_supported(source_category, target_category):
                raise ValueError(f"Conversion from {source_extension} to {target_extension} not supported")
            
            # Realizar conversión
            conversion_options = conversion_options or {}
            
            if source_category == 'documents' and target_category == 'documents':
                return await self._convert_document(source_file, source_extension, target_extension, conversion_options)
            elif source_category == 'spreadsheets' and target_category == 'spreadsheets':
                return await self._convert_spreadsheet(source_file, source_extension, target_extension, conversion_options)
            elif source_category == 'images':
                return await self._convert_image(source_file, source_extension, target_extension, conversion_options)
            else:
                return await self._convert_generic(source_file, source_extension, target_extension, conversion_options)
            
        except Exception as e:
            logger.error(f"Error converting file from {source_extension} to {target_extension}: {str(e)}")
            raise
    
    async def analyze_file_content(self, file_content: bytes, file_extension: str) -> Dict:
        """Analizar contenido detallado del archivo"""
        try:
            analysis = {
                'file_extension': file_extension,
                'file_category': self._categorize_file(file_extension),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
            file_category = self._categorize_file(file_extension)
            
            if file_category == 'documents':
                analysis['document_analysis'] = await self._analyze_document_content(file_content, file_extension)
            elif file_category == 'spreadsheets':
                analysis['spreadsheet_analysis'] = await self._analyze_spreadsheet_content(file_content, file_extension)
            elif file_category == 'images':
                analysis['image_analysis'] = await self._analyze_image_content(file_content, file_extension)
            elif file_category == 'code':
                analysis['code_analysis'] = await self._analyze_code_content(file_content, file_extension)
            else:
                analysis['generic_analysis'] = await self._analyze_generic_content(file_content, file_extension)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing file content: {str(e)}")
            raise
    
    async def optimize_file(
        self,
        file_content: bytes,
        file_extension: str,
        optimization_options: Optional[Dict] = None
    ) -> bytes:
        """Optimizar archivo para reducir tamaño o mejorar calidad"""
        try:
            optimization_options = optimization_options or {}
            file_category = self._categorize_file(file_extension)
            
            if file_category == 'images':
                return await self._optimize_image(file_content, file_extension, optimization_options)
            elif file_category == 'documents':
                return await self._optimize_document(file_content, file_extension, optimization_options)
            elif file_category == 'videos':
                return await self._optimize_video(file_content, file_extension, optimization_options)
            else:
                logger.info(f"No optimization available for {file_category} files")
                return file_content
            
        except Exception as e:
            logger.error(f"Error optimizing file: {str(e)}")
            raise
    
    async def extract_text_content(self, file_content: bytes, file_extension: str) -> str:
        """Extraer contenido de texto de cualquier archivo"""
        try:
            file_category = self._categorize_file(file_extension)
            
            if file_category == 'documents':
                return await self._extract_text_from_document(file_content, file_extension)
            elif file_category == 'spreadsheets':
                return await self._extract_text_from_spreadsheet(file_content, file_extension)
            elif file_category == 'code':
                return file_content.decode('utf-8', errors='ignore')
            elif file_extension == '.txt':
                return file_content.decode('utf-8', errors='ignore')
            else:
                logger.warning(f"Text extraction not supported for {file_extension}")
                return ""
            
        except Exception as e:
            logger.error(f"Error extracting text from {file_extension}: {str(e)}")
            raise
    
    def _categorize_file(self, file_extension: str) -> str:
        """Categorizar archivo por extensión"""
        file_extension = file_extension.lower()
        
        for category, extensions in self.supported_extensions.items():
            if file_extension in extensions:
                return category
        
        return 'unknown'
    
    def _is_conversion_supported(self, source_category: str, target_category: str) -> bool:
        """Verificar si la conversión es compatible"""
        supported_conversions = {
            'documents': ['documents', 'text'],
            'spreadsheets': ['spreadsheets', 'csv'],
            'images': ['images'],
            'text': ['documents', 'spreadsheets']
        }
        
        return target_category in supported_conversions.get(source_category, [])
    
    async def _extract_file_metadata(self, file_path: str, file_content: bytes, file_extension: str) -> Dict:
        """Extraer metadatos básicos del archivo"""
        stat = os.stat(file_path) if os.path.exists(file_path) else None
        
        metadata = {
            'filename': Path(file_path).name,
            'file_path': file_path,
            'extension': file_extension,
            'size_bytes': len(file_content),
            'size_mb': round(len(file_content) / (1024 * 1024), 2),
            'mime_type': mimetypes.guess_type(file_path)[0],
            'created_date': datetime.utcnow().isoformat(),
            'modified_date': datetime.utcnow().isoformat()
        }
        
        if stat:
            metadata['created_date'] = datetime.fromtimestamp(stat.st_ctime).isoformat()
            metadata['modified_date'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        return metadata
    
    async def _process_document(self, file_content: bytes, file_extension: str) -> Dict:
        """Procesar archivo de documento"""
        return {
            'content_type': 'document',
            'extracted_text': await self.extract_text_content(file_content, file_extension),
            'page_count': 1,  # Simplificado
            'word_count': len((await self.extract_text_content(file_content, file_extension)).split()),
            'encoding': 'utf-8'
        }
    
    async def _process_spreadsheet(self, file_content: bytes, file_extension: str) -> Dict:
        """Procesar archivo de hoja de cálculo"""
        return {
            'content_type': 'spreadsheet',
            'sheet_count': 1,  # Simplificado
            'row_count': 100,  # Simulado
            'column_count': 10,  # Simulado
            'has_formulas': False
        }
    
    async def _process_image(self, file_content: bytes, file_extension: str) -> Dict:
        """Procesar archivo de imagen"""
        return {
            'content_type': 'image',
            'width': 1920,  # Simulado
            'height': 1080,  # Simulado
            'color_depth': 24,
            'has_transparency': file_extension.lower() in ['.png', '.gif']
        }
    
    async def _process_video(self, file_content: bytes, file_extension: str) -> Dict:
        """Procesar archivo de video"""
        return {
            'content_type': 'video',
            'duration_seconds': 60,  # Simulado
            'resolution': '1920x1080',  # Simulado
            'frame_rate': 30,  # Simulado
            'codec': 'h264'  # Simulado
        }
    
    async def _process_audio(self, file_content: bytes, file_extension: str) -> Dict:
        """Procesar archivo de audio"""
        return {
            'content_type': 'audio',
            'duration_seconds': 180,  # Simulado
            'sample_rate': 44100,  # Simulado
            'bit_rate': 128,  # Simulado
            'channels': 2  # Simulado
        }
    
    async def _process_generic_file(self, file_content: bytes, file_extension: str) -> Dict:
        """Procesar archivo genérico"""
        return {
            'content_type': 'generic',
            'encoding': 'binary' if file_extension not in ['.txt', '.json', '.xml'] else 'text'
        }
    
    async def _convert_document(self, source_content: bytes, source_ext: str, target_ext: str, options: Dict) -> bytes:
        """Convertir documento entre formatos"""
        logger.info(f"Converting document from {source_ext} to {target_ext}")
        # En implementación real, usaría librerías de conversión
        return source_content  # Por ahora retornar contenido original
    
    async def _convert_spreadsheet(self, source_content: bytes, source_ext: str, target_ext: str, options: Dict) -> bytes:
        """Convertir hoja de cálculo entre formatos"""
        logger.info(f"Converting spreadsheet from {source_ext} to {target_ext}")
        return source_content
    
    async def _convert_image(self, source_content: bytes, source_ext: str, target_ext: str, options: Dict) -> bytes:
        """Convertir imagen entre formatos"""
        logger.info(f"Converting image from {source_ext} to {target_ext}")
        return source_content
    
    async def _convert_generic(self, source_content: bytes, source_ext: str, target_ext: str, options: Dict) -> bytes:
        """Conversión genérica de archivos"""
        logger.info(f"Converting file from {source_ext} to {target_ext}")
        return source_content
    
    async def _analyze_document_content(self, file_content: bytes, file_extension: str) -> Dict:
        """Analizar contenido de documento"""
        text_content = await self.extract_text_content(file_content, file_extension)
        
        return {
            'character_count': len(text_content),
            'word_count': len(text_content.split()),
            'sentence_count': text_content.count('.') + text_content.count('!') + text_content.count('?'),
            'paragraph_count': text_content.count('\n\n') + 1,
            'language': 'unknown',  # Simplificado
            'has_tables': False,
            'has_images': False
        }
    
    async def _analyze_spreadsheet_content(self, file_content: bytes, file_extension: str) -> Dict:
        """Analizar contenido de hoja de cálculo"""
        return {
            'sheet_count': 1,
            'total_cells': 1000,  # Simulado
            'numeric_cells': 750,
            'text_cells': 250,
            'formula_cells': 50,
            'empty_cells': 200
        }
    
    async def _analyze_image_content(self, file_content: bytes, file_extension: str) -> Dict:
        """Analizar contenido de imagen"""
        return {
            'width': 1920,
            'height': 1080,
            'aspect_ratio': '16:9',
            'file_size_mb': round(len(file_content) / (1024 * 1024), 2),
            'color_depth': 24,
            'format': file_extension.lower().replace('.', '')
        }
    
    async def _analyze_code_content(self, file_content: bytes, file_extension: str) -> Dict:
        """Analizar contenido de código"""
        try:
            code_content = file_content.decode('utf-8', errors='ignore')
            
            return {
                'language': self._detect_programming_language(file_extension),
                'line_count': len(code_content.split('\n')),
                'character_count': len(code_content),
                'has_comments': '//' in code_content or '#' in code_content or '/*' in code_content,
                'complexity_score': self._calculate_code_complexity(code_content)
            }
        except Exception as e:
            logger.warning(f"Could not analyze code content: {str(e)}")
            return {'error': str(e)}
    
    async def _analyze_generic_content(self, file_content: bytes, file_extension: str) -> Dict:
        """Analizar contenido genérico"""
        return {
            'file_size_bytes': len(file_content),
            'file_size_kb': round(len(file_content) / 1024, 2),
            'file_size_mb': round(len(file_content) / (1024 * 1024), 2),
            'content_type': 'binary' if file_extension not in ['.txt', '.json', '.xml'] else 'text'
        }
    
    async def _optimize_image(self, file_content: bytes, file_extension: str, options: Dict) -> bytes:
        """Optimizar imagen"""
        logger.info("Optimizing image file")
        # En implementación real, reduciría calidad o dimensiones
        return file_content
    
    async def _optimize_document(self, file_content: bytes, file_extension: str, options: Dict) -> bytes:
        """Optimizar documento"""
        logger.info("Optimizing document file")
        return file_content
    
    async def _optimize_video(self, file_content: bytes, file_extension: str, options: Dict) -> bytes:
        """Optimizar video"""
        logger.info("Optimizing video file")
        return file_content
    
    async def _extract_text_from_document(self, file_content: bytes, file_extension: str) -> str:
        """Extraer texto de documento"""
        if file_extension == '.txt':
            return file_content.decode('utf-8', errors='ignore')
        else:
            # Para otros formatos, en implementación real usaría librerías específicas
            return "Text extraction not implemented for this format"
    
    async def _extract_text_from_spreadsheet(self, file_content: bytes, file_extension: str) -> str:
        """Extraer texto de hoja de cálculo"""
        return "Spreadsheet text extraction not implemented"
    
    def _detect_programming_language(self, file_extension: str) -> str:
        """Detectar lenguaje de programación por extensión"""
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.html': 'HTML',
            '.css': 'CSS',
            '.json': 'JSON',
            '.xml': 'XML',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust'
        }
        return language_map.get(file_extension.lower(), 'Unknown')
    
    def _calculate_code_complexity(self, code_content: str) -> float:
        """Calcular complejidad básica del código"""
        # Algoritmo simplificado basado en líneas y estructuras
        lines = code_content.split('\n')
        
        complexity = len(lines) * 0.1
        
        # Bonus por estructuras de control
        control_structures = ['if', 'for', 'while', 'switch', 'try', 'except', 'def', 'class']
        for line in lines:
            for structure in control_structures:
                if structure in line.lower():
                    complexity += 0.5
        
        return round(complexity, 2)