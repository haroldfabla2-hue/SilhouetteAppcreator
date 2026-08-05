"""
Microsoft 365 - Content Parser
Parser avanzado para análisis y procesamiento de contenido
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class ContentParser:
    """Parser avanzado para análisis y procesamiento de contenido"""
    
    def __init__(self):
        self.supported_formats = ['txt', 'json', 'xml', 'csv', 'html', 'markdown']
        self.max_content_size = 10 * 1024 * 1024  # 10MB
    
    async def parse_content(self, content: str, format_type: str) -> Dict:
        """Parsear contenido según formato"""
        try:
            if len(content.encode('utf-8')) > self.max_content_size:
                raise ValueError(f"Content too large: {len(content)} characters")
            
            if format_type not in self.supported_formats:
                raise ValueError(f"Unsupported format: {format_type}")
            
            if format_type == 'json':
                return await self._parse_json_content(content)
            elif format_type == 'xml':
                return await self._parse_xml_content(content)
            elif format_type == 'csv':
                return await self._parse_csv_content(content)
            elif format_type == 'html':
                return await self._parse_html_content(content)
            elif format_type == 'markdown':
                return await self._parse_markdown_content(content)
            else:
                return await self._parse_plain_text(content)
                
        except Exception as e:
            logger.error(f"Error parsing content as {format_type}: {str(e)}")
            raise
    
    async def analyze_content_structure(self, content: str) -> Dict:
        """Analizar estructura del contenido"""
        try:
            analysis = {
                'content_length': len(content),
                'word_count': len(content.split()),
                'character_count': len(content),
                'line_count': len(content.split('\n')),
                'paragraph_count': content.count('\n\n') + 1,
                'sentence_count': len(re.findall(r'[.!?]+', content)),
                'structure_elements': await self._identify_structure_elements(content),
                'content_type': self._detect_content_type(content),
                'complexity_metrics': await self._calculate_complexity_metrics(content),
                'analyzed_at': datetime.utcnow().isoformat()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing content structure: {str(e)}")
            raise
    
    async def extract_entities(self, content: str) -> Dict:
        """Extraer entidades nombradas del contenido"""
        try:
            entities = {
                'persons': self._extract_persons(content),
                'organizations': self._extract_organizations(content),
                'locations': self._extract_locations(content),
                'dates': self._extract_dates(content),
                'emails': self._extract_emails(content),
                'urls': self._extract_urls(content),
                'phone_numbers': self._extract_phone_numbers(content),
                'monetary_amounts': self._extract_monetary_amounts(content),
                'extracted_at': datetime.utcnow().isoformat()
            }
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            raise
    
    async def generate_summary(self, content: str, max_sentences: int = 3) -> str:
        """Generar resumen automático del contenido"""
        try:
            # Algoritmo de resumen basado en puntuación de oraciones
            sentences = self._split_sentences(content)
            
            if len(sentences) <= max_sentences:
                return content
            
            # Puntuación de oraciones
            sentence_scores = []
            for i, sentence in enumerate(sentences):
                score = await self._score_sentence(sentence, i, len(sentences), content)
                sentence_scores.append((sentence, score))
            
            # Seleccionar mejores oraciones
            sentence_scores.sort(key=lambda x: x[1], reverse=True)
            selected_sentences = [sent[0] for sent in sentence_scores[:max_sentences]]
            
            # Ordenar por posición original
            final_summary = []
            for sentence in selected_sentences:
                for orig_sentence in sentences:
                    if sentence == orig_sentence and orig_sentence not in final_summary:
                        final_summary.append(orig_sentence)
                        break
            
            summary = '. '.join(final_summary[:max_sentences])
            if not summary.endswith('.'):
                summary += '.'
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            raise
    
    async def detect_language(self, content: str) -> Dict:
        """Detectar idioma del contenido"""
        try:
            # Análisis básico de idioma
            words = content.lower().split()
            total_words = len(words)
            
            # Indicadores de idioma (muy básico)
            language_indicators = {
                'spanish': ['que', 'para', 'con', 'como', 'por', 'del', 'una', 'uno', 'dos', 'tres'],
                'english': ['the', 'and', 'with', 'for', 'this', 'that', 'are', 'was', 'were'],
                'french': ['que', 'pour', 'avec', 'comme', 'par', 'des', 'une', 'deux', 'trois'],
                'german': ['der', 'und', 'für', 'mit', 'wie', 'von', 'eine', 'zwei', 'drei'],
                'italian': ['che', 'per', 'con', 'come', 'di', 'una', 'due', 'tre'],
                'portuguese': ['que', 'para', 'com', 'como', 'por', 'uma', 'dois', 'três']
            }
            
            language_scores = {}
            for lang, indicators in language_indicators.items():
                score = sum(1 for word in words if word in indicators)
                language_scores[lang] = score / total_words if total_words > 0 else 0
            
            # Determinar idioma más probable
            if not language_scores or max(language_scores.values()) == 0:
                detected_language = 'unknown'
                confidence = 0.0
            else:
                detected_language = max(language_scores, key=language_scores.get)
                confidence = language_scores[detected_language]
            
            return {
                'detected_language': detected_language,
                'confidence': round(confidence, 4),
                'language_scores': language_scores,
                'total_words_analyzed': total_words,
                'detected_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error detecting language: {str(e)}")
            raise
    
    async def extract_keywords(self, content: str, max_keywords: int = 20) -> List[Dict]:
        """Extraer palabras clave del contenido"""
        try:
            # Limpiar y normalizar texto
            clean_text = re.sub(r'[^\w\s]', ' ', content.lower())
            words = clean_text.split()
            
            # Palabras vacías comunes
            stop_words = {
                'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
                'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
                'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
                'can', 'this', 'that', 'these', 'those', 'a', 'an', 'as', 'if', 'when',
                'where', 'how', 'what', 'who', 'which', 'why', 'all', 'any', 'both',
                'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
                'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'el', 'la',
                'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le',
                'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las', 'una'
            }
            
            # Filtrar palabras y contar frecuencia
            word_freq = {}
            for word in words:
                if len(word) >= 3 and word not in stop_words and word.isalpha():
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Calcular TF-IDF básico (simplificado)
            keywords = []
            total_words = len(words)
            
            for word, freq in word_freq.items():
                tf = freq / total_words
                # IDF simplificado (asumiendo documento único)
                idf = 1.0
                tfidf = tf * idf
                
                keywords.append({
                    'keyword': word,
                    'frequency': freq,
                    'tf_score': round(tf, 6),
                    'tfidf_score': round(tfidf, 6)
                })
            
            # Ordenar por TF-IDF y retornar top keywords
            keywords.sort(key=lambda x: x['tfidf_score'], reverse=True)
            
            return keywords[:max_keywords]
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            raise
    
    async def classify_content(self, content: str) -> Dict:
        """Clasificar tipo de contenido"""
        try:
            # Patrones para clasificar contenido
            classification_patterns = {
                'email': [r'\bTo:\b', r'\bSubject:\b', r'\bFrom:\b', r'\bSent:\b'],
                'technical': [r'\bfunction\b', r'\bclass\b', r'\bimport\b', r'\bdef\b', r'\bvar\b', r'\blet\b'],
                'legal': [r'\bwhereas\b', r'\bwhereof\b', r'\bherein\b', r'\bcontract\b', r'\bagreement\b'],
                'business': [r'\brevenue\b', r'\bprofit\b', r'\bstakeholders\b', r'\bstrategy\b', r'\broi\b'],
                'academic': [r'\babstract\b', r'\bmethodology\b', r'\breferences\b', r'\bbibliography\b', r'\bcitation\b'],
                'news': [r'\breported\b', r'\baccording\b', r'\bsources\b', r'\binvestigation\b'],
                'creative': [r'\bstory\b', r'\bnarrative\b', r'\bcharacters\b', r'\bplot\b', r'\bdialogue\b']
            }
            
            scores = {}
            content_lower = content.lower()
            
            for category, patterns in classification_patterns.items():
                score = 0
                for pattern in patterns:
                    matches = len(re.findall(pattern, content_lower))
                    score += matches
                scores[category] = score
            
            # Determinar categoría más probable
            if not scores or max(scores.values()) == 0:
                classification = 'general'
                confidence = 0.0
            else:
                classification = max(scores, key=scores.get)
                confidence = scores[classification] / len(content.split()) if content.split() else 0
            
            return {
                'classification': classification,
                'confidence': round(confidence, 4),
                'category_scores': scores,
                'content_length': len(content),
                'classified_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error classifying content: {str(e)}")
            raise
    
    async def _parse_json_content(self, content: str) -> Dict:
        """Parsear contenido JSON"""
        try:
            return {
                'parsed_data': json.loads(content),
                'format': 'json',
                'parsed_at': datetime.utcnow().isoformat()
            }
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
    
    async def _parse_xml_content(self, content: str) -> Dict:
        """Parsear contenido XML"""
        try:
            # Implementación simplificada usando regex
            # En implementación real usaría xml.etree.ElementTree
            
            # Extraer tags raíz
            root_match = re.match(r'<(\w+)', content)
            root_tag = root_match.group(1) if root_match else 'unknown'
            
            # Extraer elementos básicos
            elements = re.findall(r'<(\w+)[^>]*>([^<]*)</\1>', content)
            
            return {
                'root_tag': root_tag,
                'elements': elements,
                'format': 'xml',
                'parsed_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise ValueError(f"Invalid XML format: {str(e)}")
    
    async def _parse_csv_content(self, content: str) -> Dict:
        """Parsear contenido CSV"""
        try:
            lines = content.strip().split('\n')
            if not lines:
                raise ValueError("Empty CSV content")
            
            # Detectar delimitador
            delimiter = ',' if ',' in lines[0] else ';' if ';' in lines[0] else '\t'
            
            rows = [line.split(delimiter) for line in lines]
            headers = rows[0] if rows else []
            data_rows = rows[1:] if len(rows) > 1 else []
            
            return {
                'headers': headers,
                'data_rows': data_rows,
                'row_count': len(data_rows),
                'column_count': len(headers),
                'delimiter': delimiter,
                'format': 'csv',
                'parsed_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise ValueError(f"Invalid CSV format: {str(e)}")
    
    async def _parse_html_content(self, content: str) -> Dict:
        """Parsear contenido HTML"""
        try:
            # Extraer título
            title_match = re.search(r'<title[^>]*>([^<]*)</title>', content, re.IGNORECASE)
            title = title_match.group(1) if title_match else ''
            
            # Extraer encabezados
            headers = re.findall(r'<h[1-6][^>]*>([^<]*)</h[1-6]>', content, re.IGNORECASE)
            
            # Extraer párrafos
            paragraphs = re.findall(r'<p[^>]*>([^<]*)</p>', content, re.IGNORECASE)
            
            # Extraer enlaces
            links = re.findall(r'<a[^href]*href=["\']([^"\']*)["\'][^>]*>([^<]*)</a>', content, re.IGNORECASE)
            
            return {
                'title': title,
                'headers': headers,
                'paragraphs': paragraphs,
                'links': links,
                'header_count': len(headers),
                'paragraph_count': len(paragraphs),
                'link_count': len(links),
                'format': 'html',
                'parsed_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise ValueError(f"Invalid HTML format: {str(e)}")
    
    async def _parse_markdown_content(self, content: str) -> Dict:
        """Parsear contenido Markdown"""
        try:
            # Extraer encabezados
            headers = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
            
            # Extraer listas
            lists = re.findall(r'^[*\-+]\s+(.+)$', content, re.MULTILINE)
            numbered_lists = re.findall(r'^\d+\.\s+(.+)$', content, re.MULTILINE)
            
            # Extraer código
            code_blocks = re.findall(r'```[\s\S]*?```', content)
            inline_code = re.findall(r'`([^`]+)`', content)
            
            # Extraer enlaces
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
            
            return {
                'headers': headers,
                'lists': lists,
                'numbered_lists': numbered_lists,
                'code_blocks': code_blocks,
                'inline_code': inline_code,
                'links': links,
                'format': 'markdown',
                'parsed_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise ValueError(f"Invalid Markdown format: {str(e)}")
    
    async def _parse_plain_text(self, content: str) -> Dict:
        """Parsear texto plano"""
        try:
            # Análisis básico de texto plano
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            return {
                'paragraphs': paragraphs,
                'lines': lines,
                'paragraph_count': len(paragraphs),
                'line_count': len(lines),
                'format': 'text',
                'parsed_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise ValueError(f"Error parsing plain text: {str(e)}")
    
    def _split_sentences(self, content: str) -> List[str]:
        """Dividir contenido en oraciones"""
        sentences = re.split(r'[.!?]+', content)
        return [s.strip() for s in sentences if s.strip()]
    
    async def _score_sentence(self, sentence: str, position: int, total_sentences: int, full_content: str) -> float:
        """Puntuar oración para resumen"""
        score = 0
        
        # Bonus por posición (primeras y últimas oraciones)
        if position < 3:
            score += 2
        if position >= total_sentences - 2:
            score += 1
        
        # Bonus por longitud (oraciones moderadamente largas)
        word_count = len(sentence.split())
        if 10 <= word_count <= 25:
            score += 1
        
        # Bonus por palabras clave
        keywords = await self.extract_keywords(full_content, max_keywords=10)
        keyword_words = [kw['keyword'] for kw in keywords]
        
        sentence_words = set(word.lower() for word in sentence.split())
        keyword_matches = sentence_words.intersection(set(keyword_words))
        score += len(keyword_matches) * 0.5
        
        return score
    
    def _identify_structure_elements(self, content: str) -> List[Dict]:
        """Identificar elementos estructurales"""
        elements = []
        
        # Líneas que parecen títulos
        title_lines = []
        for i, line in enumerate(content.split('\n')):
            if (len(line.strip()) > 0 and len(line.strip()) < 100 and 
                line.strip().isupper() and not line.strip().endswith('.')):
                title_lines.append({'line': i + 1, 'text': line.strip()})
        
        elements.append({'type': 'titles', 'items': title_lines})
        
        # Listas
        list_items = re.findall(r'^[\s]*[•\-\*\d+\.]\s+(.+)$', content, re.MULTILINE)
        if list_items:
            elements.append({'type': 'lists', 'items': list_items})
        
        # Tablas (formato simple)
        table_rows = re.findall(r'\|(.+)\|', content)
        if table_rows:
            elements.append({'type': 'tables', 'items': table_rows})
        
        return elements
    
    def _detect_content_type(self, content: str) -> str:
        """Detectar tipo de contenido"""
        content_lower = content.lower()
        
        # Patrones de detección
        if any(pattern in content_lower for pattern in ['dear', 'sincerely', 'best regards']):
            return 'email'
        elif content.count('\n\n') > 10 and len(content.split('\n\n')) > 5:
            return 'article'
        elif content.count('\n') / len(content.split()) < 0.1:
            return 'paragraph'
        else:
            return 'mixed'
    
    async def _calculate_complexity_metrics(self, content: str) -> Dict:
        """Calcular métricas de complejidad"""
        words = content.split()
        sentences = self._split_sentences(content)
        
        # Métricas básicas
        avg_words_per_sentence = len(words) / len(sentences) if sentences else 0
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        # Complejidad léxica (vocabulario único / total palabras)
        unique_words = set(word.lower() for word in words if word.isalpha())
        lexical_diversity = len(unique_words) / len(words) if words else 0
        
        return {
            'avg_words_per_sentence': round(avg_words_per_sentence, 2),
            'avg_sentence_length': round(avg_sentence_length, 2),
            'lexical_diversity': round(lexical_diversity, 4),
            'unique_word_count': len(unique_words),
            'total_word_count': len(words)
        }
    
    def _extract_persons(self, content: str) -> List[str]:
        """Extraer nombres de personas (simplificado)"""
        # Patrón básico: Palabras Capitalizadas consecutivas
        pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
        matches = re.findall(pattern, content)
        return list(set(matches))  # Eliminar duplicados
    
    def _extract_organizations(self, content: str) -> List[str]:
        """Extraer nombres de organizaciones"""
        org_keywords = ['inc', 'corp', 'corporation', 'company', 'ltd', 'llc', 'group', 'international']
        pattern = r'\b[A-Z][a-z]*(?:\s+[A-Z][a-z]*)*\s+(?:' + '|'.join(org_keywords) + r')\b'
        return list(set(re.findall(pattern, content, re.IGNORECASE)))
    
    def _extract_locations(self, content: str) -> List[str]:
        """Extraer ubicaciones"""
        location_keywords = ['city', 'country', 'street', 'avenue', 'road', 'state', 'province']
        pattern = r'\b(?:' + '|'.join(location_keywords) + r')\s+of\s+[A-Z][a-z]+'
        return list(set(re.findall(pattern, content, re.IGNORECASE)))
    
    def _extract_dates(self, content: str) -> List[str]:
        """Extraer fechas"""
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b',
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        ]
        
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, content, re.IGNORECASE))
        
        return list(set(dates))
    
    def _extract_emails(self, content: str) -> List[str]:
        """Extraer direcciones de correo"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return list(set(re.findall(pattern, content)))
    
    def _extract_urls(self, content: str) -> List[str]:
        """Extraer URLs"""
        pattern = r'https?://[^\s]+'
        return list(set(re.findall(pattern, content)))
    
    def _extract_phone_numbers(self, content: str) -> List[str]:
        """Extraer números telefónicos"""
        pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        return list(set(re.findall(pattern, content)))
    
    def _extract_monetary_amounts(self, content: str) -> List[str]:
        """Extraer montos monetarios"""
        pattern = r'[$€£¥]\s?\d+(?:[.,]\d{3})*(?:[.,]\d{2})?'
        return list(set(re.findall(pattern, content)))