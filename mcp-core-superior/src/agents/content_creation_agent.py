"""
Content Creation Agent MCP - Agente de Creación de Contenido Multimedia
Integra con servicios de generación de contenido para crear imágenes, audio, video
y contenido multimedia empresarial.

Autor: Content Creation Agent
Versión: 1.0.0
"""

import asyncio
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import os
import base64
import io
from pathlib import Path

# Importar la estructura base del agente MCP
try:
    from .base_agent_wrapper import BaseAgentWrapper, AgentCapability
except ImportError:
    BaseAgentWrapper = object
    AgentCapability = None


class ContentType(Enum):
    """Tipos de contenido soportados"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    PRESENTATION = "presentation"
    INFOGRAPHIC = "infographic"
    SOCIAL_MEDIA_POST = "social_media_post"
    BLOG_POST = "blog_post"
    MARKETING_COPY = "marketing_copy"


class MediaFormat(Enum):
    """Formatos de medios soportados"""
    # Imagen
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    WEBP = "webp"
    SVG = "svg"
    
    # Audio
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    M4A = "m4a"
    
    # Video
    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"
    WEBM = "webm"
    
    # Documento
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"


class ToneStyle(Enum):
    """Tonos y estilos de contenido"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FORMAL = "formal"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    SALES = "sales"
    EDUCATIONAL = "educational"
    ENTERTAINING = "entertaining"


class VoiceType(Enum):
    """Tipos de voz para audio"""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"
    CHILD = "child"


@dataclass
class ContentRequest:
    """Estructura de datos para solicitudes de contenido"""
    content_type: ContentType
    prompt: str
    style: Optional[ToneStyle] = None
    tone: Optional[ToneStyle] = None
    target_audience: Optional[str] = None
    language: str = "es"
    format: Optional[MediaFormat] = None
    dimensions: Optional[Tuple[int, int]] = None
    duration_seconds: Optional[int] = None
    voice_type: Optional[VoiceType] = None
    background_music: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedContent:
    """Estructura de datos para contenido generado"""
    id: str
    content_type: ContentType
    content: Any  # Puede ser texto, path de archivo, base64, etc.
    format: MediaFormat
    metadata: Dict[str, Any] = field(default_factory=dict)
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    duration_seconds: Optional[float] = None
    dimensions: Optional[Tuple[int, int]] = None
    quality_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ContentResponse:
    """Respuesta consolidada de creación de contenido"""
    success: bool
    content_id: str
    action: str
    timestamp: float
    execution_time: float
    content_type: ContentType
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class ContentCreationAgent(BaseAgentWrapper if BaseAgentWrapper else object):
    """
    Agente de Creación de Contenido que maneja generación de imágenes,
    audio, video y otros contenidos multimedia.
    """
    
    def __init__(self):
        if BaseAgentWrapper:
            super().__init__(
                agent_name="ContentCreationAgent",
                capabilities=[
                    AgentCapability.CONTENT_GENERATION if AgentCapability else "content_generation",
                    AgentCapability.MULTIMEDIA_CREATION if AgentCapability else "multimedia_creation",
                    AgentCapability.TEXT_TO_AUDIO if AgentCapability else "text_to_audio",
                    AgentCapability.TEXT_TO_VIDEO if AgentCapability else "text_to_video",
                    AgentCapability.IMAGE_GENERATION if AgentCapability else "image_generation",
                ],
                max_concurrent=4,
                timeout_seconds=120,
                retry_attempts=2
            )
        
        self.logger = logging.getLogger(__name__)
        self._generated_content: Dict[str, GeneratedContent] = {}
        self._templates: Dict[str, Dict[str, Any]] = {}
        self._output_dir = Path("/tmp/generated_content")
        self._output_dir.mkdir(exist_ok=True)
        
        # APIs de servicios de contenido (simuladas)
        self.content_apis = {
            "image_generation": {"provider": "openai", "model": "dall-e-3"},
            "text_to_speech": {"provider": "elevenlabs", "model": "eleven_multilingual_v2"},
            "text_to_video": {"provider": "runway", "model": "gen3"},
            "ai_writing": {"provider": "openai", "model": "gpt-4"}
        }
        
        # Cargar plantillas predefinidas
        self._load_content_templates()
    
    async def _initialize(self):
        """Inicialización específica del agente"""
        await asyncio.sleep(0.1)
        self.logger.info("Content Creation Agent inicializado")
    
    def _load_content_templates(self):
        """Cargar plantillas de contenido"""
        self._templates = {
            "social_media_post": {
                "structure": "engaging_hook + value_proposition + call_to_action",
                "length": "50-150 palabras",
                "hashtags": "3-5 hashtags relevantes",
                "tone": ToneStyle.CREATIVE
            },
            "blog_post": {
                "structure": "headline + introduction + main_content + conclusion",
                "length": "500-2000 palabras",
                "tone": ToneStyle.EDUCATIONAL,
                "seo_optimized": True
            },
            "marketing_copy": {
                "structure": "problem + solution + benefits + urgency",
                "length": "200-500 palabras",
                "tone": ToneStyle.SALES,
                "persuasive_elements": True
            },
            "presentation_slide": {
                "structure": "clear_title + key_point + supporting_visuals",
                "length": "1-3 bullets por slide",
                "tone": ToneStyle.PROFESSIONAL,
                "visual_focus": True
            }
        }
    
    def _generate_content_id(self) -> str:
        """Generar ID único para contenido"""
        return f"content_{int(time.time() * 1000)}"
    
    async def generate_image(
        self,
        prompt: str,
        style: Optional[ToneStyle] = None,
        dimensions: Optional[Tuple[int, int]] = None,
        format: MediaFormat = MediaFormat.PNG
    ) -> ContentResponse:
        """Generar imagen usando IA"""
        start_time = time.time()
        
        try:
            content_id = self._generate_content_id()
            
            # Configurar dimensiones por defecto
            if not dimensions:
                dimensions = (1024, 1024)
            
            # Simular generación de imagen
            await asyncio.sleep(2.0)  # Tiempo realista para generación
            
            # Crear archivo simulado
            file_path = self._output_dir / f"{content_id}.{format.value}"
            
            # Simular contenido de imagen (en implementación real usar API de generación)
            with open(file_path, 'w') as f:
                f.write(f"Generated image content for prompt: {prompt}")
            
            # Obtener tamaño del archivo
            file_size = file_path.stat().st_size if file_path.exists() else 0
            
            # Calcular score de calidad simulado
            quality_score = 0.85 + (hash(prompt) % 100) / 1000  # 0.85-0.95
            
            generated_content = GeneratedContent(
                id=content_id,
                content_type=ContentType.IMAGE,
                content=f"Image data for: {prompt}",
                format=format,
                file_path=str(file_path),
                file_size=file_size,
                dimensions=dimensions,
                quality_score=quality_score,
                metadata={
                    "prompt": prompt,
                    "style": style.value if style else "default",
                    "generation_time": "2.0s",
                    "provider": "dall-e-3"
                }
            )
            
            self._generated_content[content_id] = generated_content
            
            self.logger.info(f"Imagen generada: {content_id}")
            
            return ContentResponse(
                success=True,
                content_id=content_id,
                action="generate_image",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                content_type=ContentType.IMAGE,
                details={
                    "file_path": str(file_path),
                    "dimensions": dimensions,
                    "format": format.value,
                    "file_size": file_size,
                    "quality_score": quality_score,
                    "prompt": prompt
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error generando imagen: {str(e)}")
            return ContentResponse(
                success=False,
                content_id="",
                action="generate_image",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                content_type=ContentType.IMAGE,
                error=str(e)
            )
    
    async def text_to_audio(
        self,
        text: str,
        voice_type: VoiceType = VoiceType.FEMALE,
        language: str = "es",
        format: MediaFormat = MediaFormat.MP3
    ) -> ContentResponse:
        """Convertir texto a audio"""
        start_time = time.time()
        
        try:
            content_id = self._generate_content_id()
            
            # Simular conversión de texto a audio
            await asyncio.sleep(1.5)
            
            # Calcular duración basada en longitud del texto (simulado)
            words_per_minute = 150  # Velocidad normal de habla
            estimated_duration = len(text.split()) / words_per_minute * 60
            
            # Crear archivo simulado
            file_path = self._output_dir / f"{content_id}.{format.value}"
            
            with open(file_path, 'w') as f:
                f.write(f"Audio content for text: {text[:100]}...")
            
            file_size = file_path.stat().st_size if file_path.exists() else 0
            
            generated_content = GeneratedContent(
                id=content_id,
                content_type=ContentType.AUDIO,
                content=f"Audio data for text: {text[:50]}...",
                format=format,
                file_path=str(file_path),
                file_size=file_size,
                duration_seconds=estimated_duration,
                quality_score=0.92,
                metadata={
                    "original_text": text,
                    "voice_type": voice_type.value,
                    "language": language,
                    "words_count": len(text.split()),
                    "estimated_duration": estimated_duration,
                    "provider": "elevenlabs"
                }
            )
            
            self._generated_content[content_id] = generated_content
            
            self.logger.info(f"Audio generado: {content_id}")
            
            return ContentResponse(
                success=True,
                content_id=content_id,
                action="text_to_audio",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                content_type=ContentType.AUDIO,
                details={
                    "file_path": str(file_path),
                    "duration_seconds": estimated_duration,
                    "format": format.value,
                    "voice_type": voice_type.value,
                    "language": language,
                    "word_count": len(text.split())
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error convirtiendo texto a audio: {str(e)}")
            return ContentResponse(
                success=False,
                content_id="",
                action="text_to_audio",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                content_type=ContentType.AUDIO,
                error=str(e)
            )
    
    async def text_to_video(
        self,
        prompt: str,
        duration_seconds: int = 6,
        format: MediaFormat = MediaFormat.MP4
    ) -> ContentResponse:
        """Generar video a partir de texto"""
        start_time = time.time()
        
        try:
            content_id = self._generate_content_id()
            
            # Validar duración
            if duration_seconds not in [6, 10]:
                duration_seconds = 6  # Valor por defecto
            
            # Simular generación de video
            await asyncio.sleep(5.0)  # Tiempo realista para generación de video
            
            # Crear archivo simulado
            file_path = self._output_dir / f"{content_id}.{format.value}"
            
            with open(file_path, 'w') as f:
                f.write(f"Video content for prompt: {prompt}")
            
            file_size = file_path.stat().st_size if file_path.exists() else 0
            
            generated_content = GeneratedContent(
                id=content_id,
                content_type=ContentType.VIDEO,
                content=f"Video data for: {prompt}",
                format=format,
                file_path=str(file_path),
                file_size=file_size,
                duration_seconds=duration_seconds,
                quality_score=0.88,
                metadata={
                    "prompt": prompt,
                    "duration": duration_seconds,
                    "resolution": "768P",
                    "fps": 24,
                    "provider": "runway_ml",
                    "generation_time": "5.0s"
                }
            )
            
            self._generated_content[content_id] = generated_content
            
            self.logger.info(f"Video generado: {content_id}")
            
            return ContentResponse(
                success=True,
                content_id=content_id,
                action="text_to_video",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                content_type=ContentType.VIDEO,
                details={
                    "file_path": str(file_path),
                    "duration_seconds": duration_seconds,
                    "format": format.value,
                    "resolution": "768P",
                    "prompt": prompt
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error generando video: {str(e)}")
            return ContentResponse(
                success=False,
                content_id="",
                action="text_to_video",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                content_type=ContentType.VIDEO,
                error=str(e)
            )
    
    async def generate_text_content(
        self,
        prompt: str,
        content_type: ContentType,
        tone: ToneStyle = ToneStyle.PROFESSIONAL,
        target_audience: Optional[str] = None,
        length: str = "medium"
    ) -> ContentResponse:
        """Generar contenido de texto"""
        start_time = time.time()
        
        try:
            content_id = self._generate_content_id()
            
            # Simular generación de contenido de texto
            await asyncio.sleep(1.0)
            
            # Aplicar plantilla si está disponible
            template = self._templates.get(content_type.value, {})
            
            # Generar contenido simulado
            if content_type == ContentType.BLOG_POST:
                generated_text = f"""# Título del Blog Post

{self._generate_text_with_prompt(prompt, 'introduction')}

## Sección Principal

{self._generate_text_with_prompt(prompt, 'main_content')}

## Conclusión

{self._generate_text_with_prompt(prompt, 'conclusion')}

---
*Contenido generado el {datetime.now().strftime('%d/%m/%Y')}*"""
            
            elif content_type == ContentType.SOCIAL_MEDIA_POST:
                hashtags = "#generado #ia #contenido #creativo"
                generated_text = f"🎯 {self._generate_text_with_prompt(prompt, 'social_post')} {hashtags}"
            
            elif content_type == ContentType.MARKETING_COPY:
                generated_text = f"""📢 OFERTA ESPECIAL

{self._generate_text_with_prompt(prompt, 'marketing_copy')}

🔥 ¡No te pierdas esta oportunidad única!

👉 ¡Contáctanos ahora!
"""
            
            else:
                generated_text = f"Contenido generado para: {prompt}\n\nTono: {tone.value}\nAudiencia: {target_audience or 'General'}"
            
            # Calcular estadísticas
            word_count = len(generated_text.split())
            character_count = len(generated_text)
            quality_score = 0.90 + (len(prompt) % 100) / 1000
            
            generated_content = GeneratedContent(
                id=content_id,
                content_type=content_type,
                content=generated_text,
                format=MediaFormat.HTML,  # Para contenido de texto
                quality_score=quality_score,
                metadata={
                    "prompt": prompt,
                    "tone": tone.value,
                    "target_audience": target_audience,
                    "word_count": word_count,
                    "character_count": character_count,
                    "length_category": length,
                    "template_used": template
                }
            )
            
            self._generated_content[content_id] = generated_content
            
            self.logger.info(f"Contenido de texto generado: {content_id}")
            
            return ContentResponse(
                success=True,
                content_id=content_id,
                action="generate_text_content",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                content_type=content_type,
                details={
                    "content": generated_text,
                    "content_type": content_type.value,
                    "word_count": word_count,
                    "character_count": character_count,
                    "tone": tone.value,
                    "quality_score": quality_score
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error generando contenido de texto: {str(e)}")
            return ContentResponse(
                success=False,
                content_id="",
                action="generate_text_content",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                content_type=ContentType.TEXT,
                error=str(e)
            )
    
    def _generate_text_with_prompt(self, prompt: str, section_type: str) -> str:
        """Generar texto para sección específica"""
        # Simulación simple de generación de texto
        templates = {
            "introduction": f"Este artículo trata sobre {prompt}. A continuación exploraremos los aspectos más importantes.",
            "main_content": f"En cuanto a {prompt}, es importante considerar varios factores clave que influyen en el resultado final.",
            "conclusion": f"En conclusión, {prompt} representa una oportunidad significativa para el crecimiento y desarrollo.",
            "social_post": f"Descubre todo sobre {prompt} en nuestro nuevo contenido. ¡Te va a encantar!",
            "marketing_copy": f"Con nuestra solución para {prompt}, lograrás resultados extraordinarios de manera rápida y eficiente."
        }
        
        return templates.get(section_type, f"Contenido relacionado con {prompt}")
    
    async def batch_generate_content(
        self,
        requests: List[ContentRequest]
    ) -> ContentResponse:
        """Generar múltiples contenidos en lote"""
        start_time = time.time()
        
        try:
            content_ids = []
            results = []
            
            # Procesar cada solicitud
            for request in requests:
                try:
                    if request.content_type == ContentType.IMAGE:
                        response = await self.generate_image(
                            prompt=request.prompt,
                            style=request.style,
                            dimensions=request.dimensions,
                            format=request.format or MediaFormat.PNG
                        )
                    
                    elif request.content_type == ContentType.AUDIO:
                        response = await self.text_to_audio(
                            text=request.prompt,
                            voice_type=request.voice_type or VoiceType.FEMALE,
                            language=request.language,
                            format=request.format or MediaFormat.MP3
                        )
                    
                    elif request.content_type == ContentType.VIDEO:
                        response = await self.text_to_video(
                            prompt=request.prompt,
                            duration_seconds=request.duration_seconds or 6,
                            format=request.format or MediaFormat.MP4
                        )
                    
                    else:
                        response = await self.generate_text_content(
                            prompt=request.prompt,
                            content_type=request.content_type,
                            tone=request.tone or ToneStyle.PROFESSIONAL,
                            target_audience=request.target_audience
                        )
                    
                    if response.success:
                        content_ids.append(response.content_id)
                        results.append({
                            "content_id": response.content_id,
                            "content_type": request.content_type.value,
                            "prompt": request.prompt,
                            "status": "success"
                        })
                    else:
                        results.append({
                            "content_id": None,
                            "content_type": request.content_type.value,
                            "prompt": request.prompt,
                            "status": "failed",
                            "error": response.error
                        })
                
                except Exception as e:
                    results.append({
                        "content_id": None,
                        "content_type": request.content_type.value,
                        "prompt": request.prompt,
                        "status": "error",
                        "error": str(e)
                    })
            
            self.logger.info(f"Generación en lote completada: {len(content_ids)}-downward exitosos")
            
            return ContentResponse(
                success=True,
                content_id="batch_generation",
                action="batch_generate_content",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                content_type=ContentType.TEXT,
                details={
                    "total_requests": len(requests),
                    "successful_generations": len(content_ids),
                    "failed_generations": len(requests) - len(content_ids),
                    "content_ids": content_ids,
                    "results": results
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error en generación en lote: {str(e)}")
            return ContentResponse(
                success=False,
                content_id="",
                action="batch_generate_content",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                content_type=ContentType.TEXT,
                error=str(e)
            )
    
    async def process_request(
        self,
        request: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Procesar request de creación de contenido
        
        Formatos soportados:
        - generate_image: {"action": "generate_image", "prompt": "Un gato en la luna", "style": "professional", "dimensions": [1024, 1024]}
        - text_to_audio: {"action": "text_to_audio", "text": "Hola mundo", "voice_type": "female", "language": "es"}
        - text_to_video: {"action": "text_to_video", "prompt": "Un paisaje hermoso", "duration_seconds": 6}
        - generate_text: {"action": "generate_text", "prompt": "Escribe un blog post sobre...", "content_type": "blog_post", "tone": "professional"}
        - batch_generate: {"action": "batch_generate", "requests": [{"content_type": "image", "prompt": "..."}]}
        """
        try:
            await self.ensure_initialized()
            
            action = request.get("action", "").lower()
            
            if action == "generate_image":
                prompt = request.get("prompt", "")
                style_str = request.get("style", "professional")
                dimensions = request.get("dimensions", [1024, 1024])
                format_str = request.get("format", "png")
                
                if not prompt:
                    raise ValueError("prompt es requerido para generar imagen")
                
                try:
                    style = ToneStyle(style_str)
                except ValueError:
                    style = ToneStyle.PROFESSIONAL
                
                try:
                    format_type = MediaFormat(format_str.lower())
                except ValueError:
                    format_type = MediaFormat.PNG
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="generate_image",
                        capability=AgentCapability.IMAGE_GENERATION,
                        operation_func=self.generate_image,
                        prompt=prompt,
                        style=style,
                        dimensions=tuple(dimensions) if dimensions else None,
                        format=format_type
                    )
                else:
                    response = await self.generate_image(
                        prompt, style, tuple(dimensions) if dimensions else None, format_type
                    )
                
                return {
                    "success": response.success,
                    "content_id": response.content_id if response.success else None,
                    "file_path": response.details.get("file_path") if response.success else None,
                    "dimensions": response.details.get("dimensions") if response.success else None,
                    "error": response.error
                }
            
            elif action == "text_to_audio":
                text = request.get("text", "")
                voice_type_str = request.get("voice_type", "female")
                language = request.get("language", "es")
                format_str = request.get("format", "mp3")
                
                if not text:
                    raise ValueError("text es requerido para convertir a audio")
                
                try:
                    voice_type = VoiceType(voice_type_str)
                except ValueError:
                    voice_type = VoiceType.FEMALE
                
                try:
                    format_type = MediaFormat(format_str.lower())
                except ValueError:
                    format_type = MediaFormat.MP3
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="text_to_audio",
                        capability=AgentCapability.TEXT_TO_AUDIO,
                        operation_func=self.text_to_audio,
                        text=text,
                        voice_type=voice_type,
                        language=language,
                        format=format_type
                    )
                else:
                    response = await self.text_to_audio(text, voice_type, language, format_type)
                
                return {
                    "success": response.success,
                    "content_id": response.content_id if response.success else None,
                    "file_path": response.details.get("file_path") if response.success else None,
                    "duration_seconds": response.details.get("duration_seconds") if response.success else None,
                    "voice_type": response.details.get("voice_type") if response.success else None,
                    "error": response.error
                }
            
            elif action == "text_to_video":
                prompt = request.get("prompt", "")
                duration = request.get("duration_seconds", 6)
                format_str = request.get("format", "mp4")
                
                if not prompt:
                    raise ValueError("prompt es requerido para generar video")
                
                try:
                    format_type = MediaFormat(format_str.lower())
                except ValueError:
                    format_type = MediaFormat.MP4
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="text_to_video",
                        capability=AgentCapability.TEXT_TO_VIDEO,
                        operation_func=self.text_to_video,
                        prompt=prompt,
                        duration_seconds=int(duration),
                        format=format_type
                    )
                else:
                    response = await self.text_to_video(prompt, int(duration), format_type)
                
                return {
                    "success": response.success,
                    "content_id": response.content_id if response.success else None,
                    "file_path": response.details.get("file_path") if response.success else None,
                    "duration_seconds": response.details.get("duration_seconds") if response.success else None,
                    "resolution": response.details.get("resolution") if response.success else None,
                    "error": response.error
                }
            
            elif action == "generate_text":
                prompt = request.get("prompt", "")
                content_type_str = request.get("content_type", "blog_post")
                tone_str = request.get("tone", "professional")
                target_audience = request.get("target_audience")
                length = request.get("length", "medium")
                
                if not prompt:
                    raise ValueError("prompt es requerido para generar texto")
                
                try:
                    content_type = ContentType(content_type_str)
                except ValueError:
                    content_type = ContentType.BLOG_POST
                
                try:
                    tone = ToneStyle(tone_str)
                except ValueError:
                    tone = ToneStyle.PROFESSIONAL
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="generate_text_content",
                        capability=AgentCapability.CONTENT_GENERATION,
                        operation_func=self.generate_text_content,
                        prompt=prompt,
                        content_type=content_type,
                        tone=tone,
                        target_audience=target_audience,
                        length=length
                    )
                else:
                    response = await self.generate_text_content(
                        prompt, content_type, tone, target_audience, length
                    )
                
                return {
                    "success": response.success,
                    "content_id": response.content_id if response.success else None,
                    "content": response.details.get("content") if response.success else None,
                    "word_count": response.details.get("word_count") if response.success else 0,
                    "content_type": response.details.get("content_type") if response.success else None,
                    "error": response.error
                }
            
            elif action == "batch_generate":
                requests_data = request.get("requests", [])
                
                if not requests_data:
                    raise ValueError("requests es requerido para generación en lote")
                
                content_requests = []
                for req_data in requests_data:
                    content_type_str = req_data.get("content_type", "text")
                    try:
                        content_type = ContentType(content_type_str)
                    except ValueError:
                        content_type = ContentType.TEXT
                    
                    content_request = ContentRequest(
                        content_type=content_type,
                        prompt=req_data.get("prompt", ""),
                        style=ToneStyle(req_data.get("style", "professional")) if req_data.get("style") else None,
                        tone=ToneStyle(req_data.get("tone", "professional")) if req_data.get("tone") else None,
                        target_audience=req_data.get("target_audience"),
                        language=req_data.get("language", "es"),
                        format=MediaFormat(req_data.get("format", "png")) if req_data.get("format") else None,
                        dimensions=tuple(req_data.get("dimensions", [1024, 1024])) if req_data.get("dimensions") else None,
                        duration_seconds=req_data.get("duration_seconds"),
                        voice_type=VoiceType(req_data.get("voice_type", "female")) if req_data.get("voice_type") else None
                    )
                    content_requests.append(content_request)
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="batch_generate_content",
                        capability=AgentCapability.MULTIMEDIA_CREATION,
                        operation_func=self.batch_generate_content,
                        requests=content_requests
                    )
                else:
                    response = await self.batch_generate_content(content_requests)
                
                return {
                    "success": response.success,
                    "content_ids": response.details.get("content_ids", []) if response.success else [],
                    "successful_count": response.details.get("successful_generations", 0) if response.success else 0,
                    "failed_count": response.details.get("failed_generations", 0) if response.success else 0,
                    "results": response.details.get("results", []) if response.success else [],
                    "error": response.error
                }
            
            else:
                raise ValueError(f"Acción no soportada: {action}")
                
        except Exception as e:
            self.logger.error(f"Error procesando request de creación de contenido: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del agente"""
        content_by_type = {}
        for content in self._generated_content.values():
            content_type = content.content_type.value
            content_by_type[content_type] = content_by_type.get(content_type, 0) + 1
        
        return {
            "total_generated_content": len(self._generated_content),
            "content_by_type": content_by_type,
            "templates_available": list(self._templates.keys()),
            "agent_name": "ContentCreationAgent",
            "supported_content_types": [ctype.value for ctype in ContentType],
            "supported_formats": [fmt.value for fmt in MediaFormat],
            "output_directory": str(self._output_dir),
            "available_actions": [
                "generate_image",
                "text_to_audio",
                "text_to_video",
                "generate_text",
                "batch_generate"
            ]
        }