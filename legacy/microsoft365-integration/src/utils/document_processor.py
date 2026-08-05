"""
Microsoft 365 - Document Processor
Procesador especializado para documentos Word y PDF
"""

import logging
import json
from typing import Dict, List, Optional, Any
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Procesador para documentos Word y archivos de texto"""
    
    def __init__(self):
        self.supported_formats = ['.docx', '.doc', '.txt', '.pdf']
        self.max_processing_size = 10 * 1024 * 1024  # 10MB
    
    async def process_word_document(self, content_bytes: bytes) -> str:
        """Procesar contenido de documento Word"""
        try:
            # En implementación real, esto usaría python-docx o similar
            # Por ahora, simulación del procesamiento
            
            if len(content_bytes) > self.max_processing_size:
                raise ValueError(f"Document too large: {len(content_bytes)} bytes")
            
            # Simular extracción de texto
            extracted_text = self._simulate_text_extraction(content_bytes)
            
            # Post-procesamiento del texto
            processed_text = self._post_process_text(extracted_text)
            
            logger.info(f"Document processed successfully, {len(processed_text)} characters extracted")
            return processed_text
            
        except Exception as e:
            logger.error(f"Error processing Word document: {str(e)}")
            raise
    
    async def convert_word_to_pdf(self, word_content: bytes) -> bytes:
        """Convertir documento Word a PDF"""
        try:
            # En implementación real, esto usaría una librería de conversión
            # Por ahora, simulación de conversión
            
            logger.info("Converting Word document to PDF")
            
            # Simular proceso de conversión
            pdf_content = word_content  # En implementación real sería un PDF real
            
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error converting Word to PDF: {str(e)}")
            raise
    
    async def analyze_document_structure(self, content: str) -> Dict:
        """Analizar estructura del documento"""
        try:
            # Análisis básico de estructura
            paragraphs = content.split('\n\n')
            words = content.split()
            sentences = re.split(r'[.!?]+', content)
            
            # Detectar encabezados (líneas cortas, posibles títulos)
            potential_headers = []
            for para in paragraphs:
                lines = para.split('\n')
                for line in lines:
                    if (len(line.strip()) > 0 and 
                        len(line.strip()) < 100 and 
                        line.strip().isupper()):
                        potential_headers.append(line.strip())
            
            # Detectar listas
            list_items = re.findall(r'^[\s]*[•\-\*\d+\.]\s+(.+)$', content, re.MULTILINE)
            
            # Detectar tablas (formato simple)
            table_rows = re.findall(r'\|(.+)\|', content)
            
            structure = {
                'total_paragraphs': len(paragraphs),
                'total_words': len(words),
                'total_sentences': len([s for s in sentences if s.strip()]),
                'potential_headers': potential_headers,
                'list_items': list_items,
                'potential_tables': len(table_rows),
                'character_count': len(content),
                'average_words_per_paragraph': round(len(words) / len(paragraphs), 2),
                'readability_score': self._calculate_readability_score(content),
                'processed_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Document structure analyzed: {len(paragraphs)} paragraphs, {len(words)} words")
            return structure
            
        except Exception as e:
            logger.error(f"Error analyzing document structure: {str(e)}")
            raise
    
    async def extract_metadata(self, content: str) -> Dict:
        """Extraer metadatos del documento"""
        try:
            metadata = {
                'title': self._extract_title(content),
                'author': self._extract_author_indicators(content),
                'creation_date': self._extract_date_indicators(content),
                'version': self._extract_version_info(content),
                'keywords': self._extract_keywords(content),
                'summary': self._generate_summary(content),
                'language': self._detect_language(content),
                'encoding': 'utf-8',
                'processed_at': datetime.utcnow().isoformat()
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            raise
    
    async def optimize_document(self, content: str) -> str:
        """Optimizar documento para mejor legibilidad"""
        try:
            # Limpiar espacios extra
            optimized = re.sub(r'\s+', ' ', content)
            
            # Normalizar saltos de línea
            optimized = re.sub(r'\n\s*\n\s*\n+', '\n\n', optimized)
            
            # Corregir espacios alrededor de puntuación
            optimized = re.sub(r'\s+([.,!?])', r'\1', optimized)
            
            # Normalizar guiones
            optimized = re.sub(r'--', '—', optimized)
            
            logger.info("Document optimized for readability")
            return optimized
            
        except Exception as e:
            logger.error(f"Error optimizing document: {str(e)}")
            raise
    
    def _simulate_text_extraction(self, content_bytes: bytes) -> str:
        """Simular extracción de texto de documento Word"""
        # En implementación real, esto extraería texto real del documento
        # Por ahora, retornamos un texto de ejemplo que simula un documento
        
        sample_text = """
        Documento de Ejemplo - Microsoft 365 Integration
        
        Este es un documento de ejemplo que demuestra las capacidades
        de procesamiento de documentos en la integración con Microsoft 365.
        
        Características principales:
        • Procesamiento automático de texto
        • Análisis de estructura
        • Extracción de metadatos
        • Optimización de contenido
        
        Introducción
        ============
        
        La integración con Microsoft 365 permite automatizar tareas
        relacionadas con documentos, incluyendo creación, edición,
        y análisis de contenido.
        
        Sección 1: Funcionalidades
        
        Esta sección describe las principales funcionalidades
        disponibles para el procesamiento de documentos.
        
        Tabla de contenidos:
        | Sección | Descripción |
        |---------|-------------|
        | 1.1 | Creación de documentos |
        | 1.2 | Edición y modificación |
        | 1.3 | Análisis de contenido |
        
        Conclusión
        =========
        
        Esta integración proporciona una solución completa para
        la gestión automatizada de documentos en el ecosistema
        de Microsoft 365.
        """
        
        return sample_text.strip()
    
    def _post_process_text(self, text: str) -> str:
        """Post-procesar texto extraído"""
        # Limpiar caracteres extra
        text = text.strip()
        
        # Normalizar formato
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            cleaned_line = line.strip()
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines)
    
    def _calculate_readability_score(self, content: str) -> float:
        """Calcular puntuación de legibilidad básica"""
        # Algoritmo simplificado de Flesch Reading Ease
        sentences = len(re.split(r'[.!?]+', content))
        words = len(content.split())
        syllables = sum(self._count_syllables(word) for word in content.split())
        
        if sentences == 0 or words == 0:
            return 0
        
        score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
        return max(0, min(100, score))
    
    def _count_syllables(self, word: str) -> int:
        """Contar sílabas en palabra (aproximación)"""
        word = word.lower().strip('.,!?')
        vowels = 'aeiouy'
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = is_vowel
        
        return max(1, syllable_count)
    
    def _extract_title(self, content: str) -> Optional[str]:
        """Extraer título del documento"""
        lines = content.split('\n')
        for line in lines[:5]:  # Buscar en las primeras 5 líneas
            line = line.strip()
            if line and len(line) < 100 and not line.startswith(' '):
                return line
        
        return None
    
    def _extract_author_indicators(self, content: str) -> Optional[str]:
        """Extraer indicadores de autor"""
        author_patterns = [
            r'Autor[:\s]+([^\n]+)',
            r'By[:\s]+([^\n]+)',
            r'Created by[:\s]+([^\n]+)',
            r'Revisado por[:\s]+([^\n]+)'
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_date_indicators(self, content: str) -> Optional[str]:
        """Extraer indicadores de fecha"""
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b',  # MM/DD/YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',  # YYYY/MM/DD
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group()
        
        return None
    
    def _extract_version_info(self, content: str) -> Optional[str]:
        """Extraer información de versión"""
        version_patterns = [
            r'Versión[:\s]+([^\n]+)',
            r'Vers[:\s]+([^\n]+)',
            r'v(\d+\.\d+)'
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip() if match.group(1) else match.group()
        
        return None
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extraer palabras clave del documento"""
        # Palabras comunes a excluir
        stop_words = {
            'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se',
            'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con',
            'para', 'al', 'del', 'los', 'las', 'una', 'como', 'o', 'si',
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would'
        }
        
        # Extraer palabras significativas
        words = re.findall(r'\b[a-zA-ZáéíóúñÑ]{3,}\b', content.lower())
        
        # Filtrar stop words y contar frecuencia
        word_freq = {}
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Obtener las 10 palabras más frecuentes
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        return [word for word, freq in keywords]
    
    def _generate_summary(self, content: str) -> str:
        """Generar resumen automático del documento"""
        # Algoritmo simplificado de resumen
        sentences = re.split(r'[.!?]+', content)
        
        # Puntuar oraciones por posición y palabras clave
        scored_sentences = []
        words = set(word.lower() for word in re.findall(r'\b[a-zA-Z]{3,}\b', content))
        
        for i, sentence in enumerate(sentences):
            if len(sentence.strip()) < 10:  # Ignorar oraciones muy cortas
                continue
                
            score = 0
            
            # Bonus por posición (primeras y últimas oraciones)
            if i < 3:
                score += 2
            if i >= len(sentences) - 2:
                score += 1
            
            # Bonus por longitud (oraciones moderadamente largas)
            word_count = len(sentence.split())
            if 10 <= word_count <= 25:
                score += 1
            
            # Bonus por palabras clave
            sentence_words = set(word.lower() for word in re.findall(r'\b[a-zA-Z]{3,}\b', sentence))
            keyword_matches = sentence_words.intersection(words)
            score += len(keyword_matches) * 0.1
            
            scored_sentences.append((sentence.strip(), score))
        
        # Seleccionar las mejores oraciones
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Tomar las 3 mejores oraciones y ordenarlas por posición original
        best_sentences = [s[0] for s in scored_sentences[:3]]
        
        # Ordenar por aparición en el texto original
        final_summary = []
        for sentence in best_sentences:
            for orig_sentence in sentences:
                if sentence in orig_sentence and orig_sentence not in final_summary:
                    final_summary.append(orig_sentence.strip())
                    break
        
        return '. '.join(final_summary[:3]) + '.'
    
    def _detect_language(self, content: str) -> str:
        """Detectar idioma del documento (simplificado)"""
        # Análisis muy básico de idioma
        spanish_indicators = ['que', 'para', 'con', 'como', 'por', 'del', 'una', 'uno', 'dos', 'tres']
        english_indicators = ['the', 'and', 'with', 'for', 'this', 'that', 'are', 'was', 'were']
        
        spanish_count = sum(1 for indicator in spanish_indicators if indicator in content.lower())
        english_count = sum(1 for indicator in english_indicators if indicator in content.lower())
        
        if spanish_count > english_count:
            return 'es'
        elif english_count > spanish_count:
            return 'en'
        else:
            return 'unknown'