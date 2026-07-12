#!/usr/bin/env python3
"""
SilhouetteMCP - Content Creation Agent Expandido
MCP Server para Generación de Contenido Multimedia

Funcionalidades:
- Image Gen (2): gen_images, edit_images
- Audio Kit (3): get_voice_list, batch_text_to_audio, batch_text_to_music
- Video Kit (2): batch_text_to_video, batch_image_to_video
- Chart Kit (1): render_mermaid

Endpoints MCP:
- /mcp/content/images/generate
- /mcp/content/images/edit
- /mcp/content/audio/voices
- /mcp/content/audio/text-to-audio
- /mcp/content/audio/text-to-music
- /mcp/content/video/text-to-video
- /mcp/content/video/image-to-video
- /mcp/content/charts/mermaid

Autor: SilhouetteMCP Team
Fecha: 2025-11-05
"""

import asyncio
import json
import os
import time
import uuid
import base64
import aiofiles
import aiohttp
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue
from concurrent.futures import ThreadPoolExecutor

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Estados de tareas para el queue system"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ContentType(Enum):
    """Tipos de contenido soportados"""
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    CHART = "chart"

@dataclass
class TaskInfo:
    """Información de tareas para el queue system"""
    task_id: str
    task_type: str
    status: TaskStatus
    created_at: float
    updated_at: float
    input_data: Dict
    output_data: Optional[Dict] = None
    error_message: Optional[str] = None

class ContentValidation:
    """Validación de formatos y archivos multimedia"""
    
    ALLOWED_IMAGE_FORMATS = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}
    ALLOWED_AUDIO_FORMATS = {'.mp3', '.wav', '.pcm', '.m4a'}
    ALLOWED_VIDEO_FORMATS = {'.mp4', '.avi', '.mov', '.mkv'}
    ALLOWED_CHART_FORMATS = {'.png', '.svg', '.html'}
    
    MAX_FILE_SIZES = {
        ContentType.IMAGE: 50 * 1024 * 1024,  # 50MB
        ContentType.AUDIO: 200 * 1024 * 1024, # 200MB
        ContentType.VIDEO: 500 * 1024 * 1024, # 500MB
        ContentType.CHART: 10 * 1024 * 1024   # 10MB
    }
    
    @classmethod
    def validate_image_format(cls, file_path: str) -> bool:
        """Valida formato de imagen"""
        ext = Path(file_path).suffix.lower()
        return ext in cls.ALLOWED_IMAGE_FORMATS
    
    @classmethod
    def validate_audio_format(cls, file_path: str) -> bool:
        """Valida formato de audio"""
        ext = Path(file_path).suffix.lower()
        return ext in cls.ALLOWED_AUDIO_FORMATS
    
    @classmethod
    def validate_video_format(cls, file_path: str) -> bool:
        """Valida formato de video"""
        ext = Path(file_path).suffix.lower()
        return ext in cls.ALLOWED_VIDEO_FORMATS
    
    @classmethod
    def validate_file_size(cls, file_path: str, content_type: ContentType) -> bool:
        """Valida tamaño de archivo"""
        if not os.path.exists(file_path):
            return False
        file_size = os.path.getsize(file_path)
        max_size = cls.MAX_FILE_SIZES.get(content_type, 0)
        return file_size <= max_size
    
    @classmethod
    def validate_mime_type(cls, file_path: str, expected_type: ContentType) -> bool:
        """Valida tipo MIME basado en contenido esperado"""
        # Implementación simplificada - en producción usar python-magic
        if expected_type == ContentType.IMAGE:
            return cls.validate_image_format(file_path)
        elif expected_type == ContentType.AUDIO:
            return cls.validate_audio_format(file_path)
        elif expected_type == ContentType.VIDEO:
            return cls.validate_video_format(file_path)
        return False

class TaskQueue:
    """Sistema de cola para procesamiento asíncrono"""
    
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.tasks: Dict[str, TaskInfo] = {}
        self.task_queue = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running = False
    
    def add_task(self, task_info: TaskInfo) -> str:
        """Añade tarea a la cola"""
        self.tasks[task_info.task_id] = task_info
        self.task_queue.put(task_info.task_id)
        return task_info.task_id
    
    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Obtiene información de tarea"""
        return self.tasks.get(task_id)
    
    def update_task_status(self, task_id: str, status: TaskStatus, 
                          output_data: Optional[Dict] = None, 
                          error_message: Optional[str] = None):
        """Actualiza estado de tarea"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = status
            task.updated_at = time.time()
            if output_data:
                task.output_data = output_data
            if error_message:
                task.error_message = error_message
    
    def start(self):
        """Inicia el procesamiento de la cola"""
        self.running = True
        worker_thread = threading.Thread(target=self._process_queue)
        worker_thread.daemon = True
        worker_thread.start()
        logger.info("TaskQueue iniciado con %d workers", self.max_workers)
    
    def stop(self):
        """Detiene el procesamiento de la cola"""
        self.running = False
        self.executor.shutdown(wait=True)
        logger.info("TaskQueue detenido")
    
    def _process_queue(self):
        """Procesa la cola de tareas"""
        while self.running:
            try:
                task_id = self.task_queue.get(timeout=1)
                task = self.tasks.get(task_id)
                if task:
                    self._process_single_task(task)
                self.task_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error("Error procesando cola: %s", str(e))
    
    def _process_single_task(self, task: TaskInfo):
        """Procesa una tarea individual"""
        try:
            self.update_task_status(task.task_id, TaskStatus.PROCESSING)
            
            # Simular procesamiento - aquí iría la lógica real
            time.sleep(2)  # Simulación de trabajo
            
            # Generar respuesta de ejemplo
            output_data = {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "status": "completed",
                "result": "Contenido procesado exitosamente",
                "created_at": datetime.now().isoformat()
            }
            
            self.update_task_status(task.task_id, TaskStatus.COMPLETED, output_data)
            logger.info("Tarea %s completada", task.task_id)
            
        except Exception as e:
            error_msg = str(e)
            self.update_task_status(task.task_id, TaskStatus.FAILED, error_message=error_msg)
            logger.error("Error procesando tarea %s: %s", task.task_id, error_msg)

class FileManager:
    """Manejo de archivos multimedia"""
    
    def __init__(self, upload_dir: str = "uploads", output_dir: str = "outputs"):
        self.upload_dir = Path(upload_dir)
        self.output_dir = Path(output_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
    
    async def save_uploaded_file(self, file_data: bytes, filename: str, 
                                content_type: ContentType) -> str:
        """Guarda archivo subido"""
        # Validar formato
        temp_path = self.upload_dir / filename
        temp_path.write_bytes(file_data)
        
        if not ContentValidation.validate_file_size(str(temp_path), content_type):
            temp_path.unlink()
            raise ValueError(f"Archivo demasiado grande para {content_type.value}")
        
        # Mover a directorio final
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_filename = f"{timestamp}_{filename}"
        final_path = self.upload_dir / final_filename
        temp_path.rename(final_path)
        
        logger.info("Archivo guardado: %s", final_path)
        return str(final_path)
    
    async def save_generated_content(self, content_data: bytes, 
                                   filename: str, content_type: ContentType) -> str:
        """Guarda contenido generado"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_filename = f"generated_{timestamp}_{filename}"
        output_path = self.output_dir / final_filename
        
        async with aiofiles.open(output_path, 'wb') as f:
            await f.write(content_data)
        
        logger.info("Contenido guardado: %s", output_path)
        return str(output_path)
    
    def get_file_url(self, file_path: str) -> str:
        """Genera URL para acceder al archivo"""
        # En producción esto retornaría una URL HTTP/HTTPS
        return f"file://{file_path}"
    
    async def delete_file(self, file_path: str) -> bool:
        """Elimina archivo"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info("Archivo eliminado: %s", file_path)
                return True
        except Exception as e:
            logger.error("Error eliminando archivo %s: %s", file_path, str(e))
        return False

class ContentCreationAgent:
    """Agente principal de creación de contenido"""
    
    def __init__(self):
        self.task_queue = TaskQueue(max_workers=5)
        self.file_manager = FileManager()
        self.task_queue.start()
        
        # Configuración de endpoints MCP
        self.mcp_endpoints = {
            "/mcp/content/images/generate": self.generate_images,
            "/mcp/content/images/edit": self.edit_images,
            "/mcp/content/audio/voices": self.get_voice_list,
            "/mcp/content/audio/text-to-audio": self.batch_text_to_audio,
            "/mcp/content/audio/text-to-music": self.batch_text_to_music,
            "/mcp/content/video/text-to-video": self.batch_text_to_video,
            "/mcp/content/video/image-to-video": self.batch_image_to_video,
            "/mcp/content/charts/mermaid": self.render_mermaid
        }
    
    def get_mcp_endpoints(self) -> Dict[str, callable]:
        """Retorna todos los endpoints MCP disponibles"""
        return self.mcp_endpoints
    
    # ================================
    # IMAGE GENERATION TOOLS (2)
    # ================================
    
    async def generate_images(self, request_data: Dict) -> Dict:
        """
        Genera imágenes usando prompts de texto
        
        Args:
            request_data: {
                "prompts": ["prompt1", "prompt2"],
                "output_files": ["output1.png", "output2.png"],
                "reference_files": [[], []]  # opcional
            }
        """
        try:
            prompts = request_data.get("prompts", [])
            output_files = request_data.get("output_files", [])
            reference_files = request_data.get("reference_files", [])
            
            if not prompts or not output_files:
                raise ValueError("Se requieren prompts y output_files")
            
            # Crear ID de tarea para procesamiento asíncrono
            task_id = str(uuid.uuid4())
            
            # Crear tarea en cola
            task_info = TaskInfo(
                task_id=task_id,
                task_type="generate_images",
                status=TaskStatus.PENDING,
                created_at=time.time(),
                updated_at=time.time(),
                input_data=request_data
            )
            
            # Añadir a cola para procesamiento
            self.task_queue.add_task(task_info)
            
            # Simulación de generación de imágenes
            # En implementación real, aquí se llamaría a gen_images
            
            logger.info("Generación de imágenes iniciada - Task ID: %s", task_id)
            
            return {
                "status": "accepted",
                "task_id": task_id,
                "message": "Generación de imágenes iniciada",
                "estimated_time": len(prompts) * 30,  # 30 segundos por imagen
                "endpoints": {
                    "status": f"/mcp/content/task/{task_id}/status",
                    "download": f"/mcp/content/task/{task_id}/download"
                }
            }
            
        except Exception as e:
            logger.error("Error en generate_images: %s", str(e))
            return {"error": str(e)}
    
    async def edit_images(self, request_data: Dict) -> Dict:
        """
        Edita imágenes existentes usando prompts
        
        Args:
            request_data: {
                "base_image_file_paths": ["image1.png", "image2.png"],
                "prompts": ["edit prompt1", "edit prompt2"],
                "output_image_file_paths": ["output1.png", "output2.png"]
            }
        """
        try:
            base_image_file_paths = request_data.get("base_image_file_paths", [])
            prompts = request_data.get("prompts", [])
            output_image_file_paths = request_data.get("output_image_file_paths", [])
            
            if not all([base_image_file_paths, prompts, output_image_file_paths]):
                raise ValueError("Se requieren todos los campos requeridos")
            
            # Validar archivos base
            for img_path in base_image_file_paths:
                if not ContentValidation.validate_image_format(img_path):
                    raise ValueError(f"Formato no válido para imagen: {img_path}")
            
            task_id = str(uuid.uuid4())
            
            task_info = TaskInfo(
                task_id=task_id,
                task_type="edit_images",
                status=TaskStatus.PENDING,
                created_at=time.time(),
                updated_at=time.time(),
                input_data=request_data
            )
            
            self.task_queue.add_task(task_info)
            
            logger.info("Edición de imágenes iniciada - Task ID: %s", task_id)
            
            return {
                "status": "accepted",
                "task_id": task_id,
                "message": "Edición de imágenes iniciada",
                "estimated_time": len(base_image_file_paths) * 45,
                "endpoints": {
                    "status": f"/mcp/content/task/{task_id}/status",
                    "download": f"/mcp/content/task/{task_id}/download"
                }
            }
            
        except Exception as e:
            logger.error("Error en edit_images: %s", str(e))
            return {"error": str(e)}
    
    # ================================
    # AUDIO KIT TOOLS (3)
    # ================================
    
    async def get_voice_list(self, request_data: Dict) -> Dict:
        """
        Obtiene lista de voces disponibles
        
        Args:
            request_data: {}  # Parámetros opcionales
        """
        try:
            # Simulación de voces disponibles
            # En implementación real, aquí se llamaría a get_voice_list
            
            voices = [
                {"voice_id": "voice_001", "name": "María", "language": "es", "gender": "female"},
                {"voice_id": "voice_002", "name": "Carlos", "language": "es", "gender": "male"},
                {"voice_id": "voice_003", "name": "Ana", "language": "es", "gender": "female"},
                {"voice_id": "voice_004", "name": "Luis", "language": "es", "gender": "male"}
            ]
            
            return {
                "status": "success",
                "voices": voices,
                "total_voices": len(voices),
                "endpoint": "/mcp/content/audio/voices"
            }
            
        except Exception as e:
            logger.error("Error en get_voice_list: %s", str(e))
            return {"error": str(e)}
    
    async def batch_text_to_audio(self, request_data: Dict) -> Dict:
        """
        Convierte texto a audio
        
        Args:
            request_data: {
                "text_list": ["texto1", "texto2"],
                "voice_list": ["voice_001", "voice_002"],
                "output_file_list": ["output1.mp3", "output2.mp3"],
                "speed_list": [1.0, 1.2],  # opcional
                "pitch_list": [0, 1],       # opcional
                "volume_list": [5.0, 6.0],  # opcional
                "emotion_list": ["neutral", "happy"]  # opcional
            }
        """
        try:
            text_list = request_data.get("text_list", [])
            voice_list = request_data.get("voice_list", [])
            output_file_list = request_data.get("output_file_list", [])
            
            if not all([text_list, voice_list, output_file_list]):
                raise ValueError("Se requieren text_list, voice_list y output_file_list")
            
            # Validar tamaños de listas
            if len(text_list) != len(voice_list) or len(text_list) != len(output_file_list):
                raise ValueError("Las listas deben tener el mismo tamaño")
            
            task_id = str(uuid.uuid4())
            
            task_info = TaskInfo(
                task_id=task_id,
                task_type="batch_text_to_audio",
                status=TaskStatus.PENDING,
                created_at=time.time(),
                updated_at=time.time(),
                input_data=request_data
            )
            
            self.task_queue.add_task(task_info)
            
            estimated_time = len(text_list) * 15  # 15 segundos por audio
            
            return {
                "status": "accepted",
                "task_id": task_id,
                "message": "Conversión de texto a audio iniciada",
                "estimated_time": estimated_time,
                "endpoints": {
                    "status": f"/mcp/content/task/{task_id}/status",
                    "download": f"/mcp/content/task/{task_id}/download"
                }
            }
            
        except Exception as e:
            logger.error("Error en batch_text_to_audio: %s", str(e))
            return {"error": str(e)}
    
    async def batch_text_to_music(self, request_data: Dict) -> Dict:
        """
        Crea música a partir de texto y letras
        
        Args:
            request_data: {
                "prompt_list": ["descripción del estilo musical"],
                "lyrics_list": ["letras de la canción"],
                "output_file_list": ["output1.mp3", "output2.mp3"],
                "format_list": ["mp3"],    # opcional
                "bitrate_list": [128000],  # opcional
                "sample_rate_list": [44100] # opcional
            }
        """
        try:
            prompt_list = request_data.get("prompt_list", [])
            lyrics_list = request_data.get("lyrics_list", [])
            output_file_list = request_data.get("output_file_list", [])
            
            if not all([prompt_list, lyrics_list, output_file_list]):
                raise ValueError("Se requieren prompt_list, lyrics_list y output_file_list")
            
            task_id = str(uuid.uuid4())
            
            task_info = TaskInfo(
                task_id=task_id,
                task_type="batch_text_to_music",
                status=TaskStatus.PENDING,
                created_at=time.time(),
                updated_at=time.time(),
                input_data=request_data
            )
            
            self.task_queue.add_task(task_info)
            
            estimated_time = len(prompt_list) * 120  # 2 minutos por música
            
            return {
                "status": "accepted",
                "task_id": task_id,
                "message": "Creación de música iniciada",
                "estimated_time": estimated_time,
                "endpoints": {
                    "status": f"/mcp/content/task/{task_id}/status",
                    "download": f"/mcp/content/task/{task_id}/download"
                }
            }
            
        except Exception as e:
            logger.error("Error en batch_text_to_music: %s", str(e))
            return {"error": str(e)}
    
    # ================================
    # VIDEO KIT TOOLS (2)
    # ================================
    
    async def batch_text_to_video(self, request_data: Dict) -> Dict:
        """
        Genera videos a partir de prompts de texto
        
        Args:
            request_data: {
                "prompt_list": ["descripción del video"],
                "output_file_list": ["video1.mp4", "video2.mp4"],
                "duration_list": [6, 10],    # opcional
                "resolution_list": ["768P"]  # opcional
            }
        """
        try:
            prompt_list = request_data.get("prompt_list", [])
            output_file_list = request_data.get("output_file_list", [])
            duration_list = request_data.get("duration_list", [6] * len(prompt_list))
            resolution_list = request_data.get("resolution_list", ["768P"] * len(prompt_list))
            
            if not all([prompt_list, output_file_list]):
                raise ValueError("Se requieren prompt_list y output_file_list")
            
            # Validar duraciones
            for duration in duration_list:
                if duration not in [6, 10]:
                    raise ValueError("Duración debe ser 6 o 10 segundos")
            
            # Validar resoluciones
            for resolution in resolution_list:
                if resolution not in ["768P", "1080P"]:
                    raise ValueError("Resolución debe ser 768P o 1080P")
            
            task_id = str(uuid.uuid4())
            
            task_info = TaskInfo(
                task_id=task_id,
                task_type="batch_text_to_video",
                status=TaskStatus.PENDING,
                created_at=time.time(),
                updated_at=time.time(),
                input_data=request_data
            )
            
            self.task_queue.add_task(task_info)
            
            estimated_time = len(prompt_list) * 90  # 1.5 minutos por video
            
            return {
                "status": "accepted",
                "task_id": task_id,
                "message": "Generación de videos iniciada",
                "estimated_time": estimated_time,
                "endpoints": {
                    "status": f"/mcp/content/task/{task_id}/status",
                    "download": f"/mcp/content/task/{task_id}/download"
                }
            }
            
        except Exception as e:
            logger.error("Error en batch_text_to_video: %s", str(e))
            return {"error": str(e)}
    
    async def batch_image_to_video(self, request_data: Dict) -> Dict:
        """
        Genera videos a partir de imágenes
        
        Args:
            request_data: {
                "image_file_list": ["image1.png", "image2.jpg"],
                "prompt_list": ["descripción de la animación"],
                "output_file_list": ["video1.mp4", "video2.mp4"],
                "duration_list": [6, 10],        # opcional
                "resolution_list": ["768P"],     # opcional
                "reference_type_list": ["first_frame"] # opcional
            }
        """
        try:
            image_file_list = request_data.get("image_file_list", [])
            prompt_list = request_data.get("prompt_list", [])
            output_file_list = request_data.get("output_file_list", [])
            
            if not all([image_file_list, prompt_list, output_file_list]):
                raise ValueError("Se requieren image_file_list, prompt_list y output_file_list")
            
            # Validar imágenes
            for img_path in image_file_list:
                if not ContentValidation.validate_image_format(img_path):
                    raise ValueError(f"Formato no válido para imagen: {img_path}")
            
            task_id = str(uuid.uuid4())
            
            task_info = TaskInfo(
                task_id=task_id,
                task_type="batch_image_to_video",
                status=TaskStatus.PENDING,
                created_at=time.time(),
                updated_at=time.time(),
                input_data=request_data
            )
            
            self.task_queue.add_task(task_info)
            
            estimated_time = len(image_file_list) * 120  # 2 minutos por video
            
            return {
                "status": "accepted",
                "task_id": task_id,
                "message": "Generación de videos desde imágenes iniciada",
                "estimated_time": estimated_time,
                "endpoints": {
                    "status": f"/mcp/content/task/{task_id}/status",
                    "download": f"/mcp/content/task/{task_id}/download"
                }
            }
            
        except Exception as e:
            logger.error("Error en batch_image_to_video: %s", str(e))
            return {"error": str(e)}
    
    # ================================
    # CHART KIT TOOL (1)
    # ================================
    
    async def render_mermaid(self, request_data: Dict) -> Dict:
        """
        Renderiza diagramas Mermaid
        
        Args:
            request_data: {
                "mermaid_code": "graph TD; A-->B; B-->C;",
                "output_file_path": "diagram.png",
                "width": 1200,    # opcional
                "height": 800,    # opcional
                "title": "Mi Diagrama" # opcional
            }
        """
        try:
            mermaid_code = request_data.get("mermaid_code", "")
            output_file_path = request_data.get("output_file_path", "diagram.png")
            width = request_data.get("width", 1200)
            height = request_data.get("height", 800)
            title = request_data.get("title", "Mermaid Chart")
            
            if not mermaid_code or not output_file_path:
                raise ValueError("Se requieren mermaid_code y output_file_path")
            
            # Validar dimensiones
            if width <= 0 or height <= 0:
                raise ValueError("Las dimensiones deben ser positivas")
            
            task_id = str(uuid.uuid4())
            
            task_info = TaskInfo(
                task_id=task_id,
                task_type="render_mermaid",
                status=TaskStatus.PENDING,
                created_at=time.time(),
                updated_at=time.time(),
                input_data=request_data
            )
            
            self.task_queue.add_task(task_info)
            
            return {
                "status": "accepted",
                "task_id": task_id,
                "message": "Renderizado de diagrama iniciado",
                "estimated_time": 10,  # 10 segundos para diagrama
                "endpoints": {
                    "status": f"/mcp/content/task/{task_id}/status",
                    "download": f"/mcp/content/task/{task_id}/download"
                }
            }
            
        except Exception as e:
            logger.error("Error en render_mermaid: %s", str(e))
            return {"error": str(e)}
    
    # ================================
    # TASK MANAGEMENT ENDPOINTS
    # ================================
    
    async def get_task_status(self, task_id: str) -> Dict:
        """Obtiene el estado de una tarea"""
        task_info = self.task_queue.get_task(task_id)
        if not task_info:
            return {"error": "Tarea no encontrada"}
        
        return {
            "task_id": task_info.task_id,
            "task_type": task_info.task_type,
            "status": task_info.status.value,
            "created_at": datetime.fromtimestamp(task_info.created_at).isoformat(),
            "updated_at": datetime.fromtimestamp(task_info.updated_at).isoformat(),
            "output_data": task_info.output_data,
            "error_message": task_info.error_message
        }
    
    async def download_task_result(self, task_id: str) -> Dict:
        """Descarga el resultado de una tarea completada"""
        task_info = self.task_queue.get_task(task_id)
        if not task_info:
            return {"error": "Tarea no encontrada"}
        
        if task_info.status != TaskStatus.COMPLETED:
            return {"error": "Tarea no completada aún", "status": task_info.status.value}
        
        # Generar URLs de descarga para archivos generados
        download_urls = []
        if task_info.output_data and "generated_files" in task_info.output_data:
            for file_path in task_info.output_data["generated_files"]:
                download_urls.append(self.file_manager.get_file_url(file_path))
        
        return {
            "task_id": task_info.task_id,
            "status": "completed",
            "download_urls": download_urls,
            "result": task_info.output_data
        }
    
    async def cleanup_task(self, task_id: str) -> Dict:
        """Limpia una tarea y sus archivos asociados"""
        task_info = self.task_queue.get_task(task_id)
        if not task_info:
            return {"error": "Tarea no encontrada"}
        
        # Limpiar archivos generados
        if task_info.output_data and "generated_files" in task_info.output_data:
            for file_path in task_info.output_data["generated_files"]:
                await self.file_manager.delete_file(file_path)
        
        # Remover de la cola
        del self.task_queue.tasks[task_id]
        
        return {
            "status": "success",
            "message": f"Tarea {task_id} limpiada"
        }
    
    def get_mcp_server_info(self) -> Dict:
        """Información del servidor MCP"""
        return {
            "name": "SilhouetteMCP Content Creation Agent",
            "version": "1.0.0",
            "description": "Servidor MCP para generación de contenido multimedia",
            "endpoints": list(self.mcp_endpoints.keys()),
            "supported_formats": {
                "images": list(ContentValidation.ALLOWED_IMAGE_FORMATS),
                "audio": list(ContentValidation.ALLOWED_AUDIO_FORMATS),
                "video": list(ContentValidation.ALLOWED_VIDEO_FORMATS),
                "charts": list(ContentValidation.ALLOWED_CHART_FORMATS)
            },
            "max_file_sizes": {k.value: v for k, v in ContentValidation.MAX_FILE_SIZES.items()},
            "features": [
                "Generación de imágenes desde texto",
                "Edición de imágenes existentes",
                "Conversión de texto a audio",
                "Creación de música con letras",
                "Generación de videos desde texto",
                "Generación de videos desde imágenes",
                "Renderizado de diagramas Mermaid",
                "Sistema de cola para tareas pesadas",
                "Validación de formatos de archivo",
                "Upload y descarga de archivos",
                "Procesamiento asíncrono"
            ]
        }
    
    async def shutdown(self):
        """Cierra el agente limpiando recursos"""
        self.task_queue.stop()
        logger.info("Content Creation Agent cerrado")

# ================================
# MCP SERVER IMPLEMENTATION
# ================================

class ContentMCPHandler:
    """Manejador principal del servidor MCP"""
    
    def __init__(self):
        self.agent = ContentCreationAgent()
    
    async def handle_request(self, path: str, method: str, 
                           request_data: Dict) -> Dict:
        """Maneja requests HTTP/HTTPS"""
        
        # Endpoint de información del servidor
        if path == "/mcp/content/info":
            return self.agent.get_mcp_server_info()
        
        # Endpoints de tareas
        if path.startswith("/mcp/content/task/"):
            parts = path.split("/")
            if len(parts) >= 5:
                task_id = parts[4]
                if parts[5] == "status":
                    return await self.agent.get_task_status(task_id)
                elif parts[5] == "download":
                    return await self.agent.download_task_result(task_id)
                elif parts[5] == "cleanup":
                    return await self.agent.cleanup_task(task_id)
        
        # Endpoints de contenido
        if path in self.agent.mcp_endpoints:
            handler = self.agent.mcp_endpoints[path]
            return await handler(request_data)
        
        return {"error": "Endpoint no encontrado", "path": path}
    
    def list_available_tools(self) -> List[Dict]:
        """Lista todas las herramientas disponibles"""
        tools = []
        
        # Image Generation Tools
        tools.append({
            "name": "generate_images",
            "description": "Genera imágenes usando prompts de texto",
            "endpoint": "/mcp/content/images/generate",
            "category": "Image Generation",
            "parameters": {
                "prompts": ["string[]"],
                "output_files": ["string[]"],
                "reference_files": ["string[][] (optional)"]
            }
        })
        
        tools.append({
            "name": "edit_images",
            "description": "Edita imágenes existentes usando prompts",
            "endpoint": "/mcp/content/images/edit",
            "category": "Image Generation",
            "parameters": {
                "base_image_file_paths": ["string[]"],
                "prompts": ["string[]"],
                "output_image_file_paths": ["string[]"]
            }
        })
        
        # Audio Generation Tools
        tools.append({
            "name": "get_voice_list",
            "description": "Obtiene lista de voces disponibles",
            "endpoint": "/mcp/content/audio/voices",
            "category": "Audio Generation",
            "parameters": {}
        })
        
        tools.append({
            "name": "batch_text_to_audio",
            "description": "Convierte texto a audio",
            "endpoint": "/mcp/content/audio/text-to-audio",
            "category": "Audio Generation",
            "parameters": {
                "text_list": ["string[]"],
                "voice_list": ["string[]"],
                "output_file_list": ["string[]"],
                "speed_list": ["float[] (optional)"],
                "pitch_list": ["int[] (optional)"],
                "volume_list": ["float[] (optional)"],
                "emotion_list": ["string[] (optional)"]
            }
        })
        
        tools.append({
            "name": "batch_text_to_music",
            "description": "Crea música a partir de texto y letras",
            "endpoint": "/mcp/content/audio/text-to-music",
            "category": "Audio Generation",
            "parameters": {
                "prompt_list": ["string[]"],
                "lyrics_list": ["string[]"],
                "output_file_list": ["string[]"],
                "format_list": ["string[] (optional)"],
                "bitrate_list": ["int[] (optional)"],
                "sample_rate_list": ["int[] (optional)"]
            }
        })
        
        # Video Generation Tools
        tools.append({
            "name": "batch_text_to_video",
            "description": "Genera videos a partir de prompts de texto",
            "endpoint": "/mcp/content/video/text-to-video",
            "category": "Video Generation",
            "parameters": {
                "prompt_list": ["string[]"],
                "output_file_list": ["string[]"],
                "duration_list": ["int[] (optional)"],
                "resolution_list": ["string[] (optional)"]
            }
        })
        
        tools.append({
            "name": "batch_image_to_video",
            "description": "Genera videos a partir de imágenes",
            "endpoint": "/mcp/content/video/image-to-video",
            "category": "Video Generation",
            "parameters": {
                "image_file_list": ["string[]"],
                "prompt_list": ["string[]"],
                "output_file_list": ["string[]"],
                "duration_list": ["int[] (optional)"],
                "resolution_list": ["string[] (optional)"],
                "reference_type_list": ["string[] (optional)"]
            }
        })
        
        # Chart Generation Tools
        tools.append({
            "name": "render_mermaid",
            "description": "Renderiza diagramas Mermaid",
            "endpoint": "/mcp/content/charts/mermaid",
            "category": "Chart Generation",
            "parameters": {
                "mermaid_code": ["string"],
                "output_file_path": ["string"],
                "width": ["int (optional)"],
                "height": ["int (optional)"],
                "title": ["string (optional)"]
            }
        })
        
        return tools

# ================================
# MAIN APPLICATION
# ================================

async def main():
    """Función principal del servidor MCP"""
    handler = ContentMCPHandler()
    
    print("🎨 SilhouetteMCP - Content Creation Agent Expandido")
    print("=" * 60)
    print(f"Servidor iniciado: {datetime.now().isoformat()}")
    print()
    
    # Mostrar información del servidor
    server_info = handler.agent.get_mcp_server_info()
    print(f"📦 Nombre: {server_info['name']}")
    print(f"🔢 Versión: {server_info['version']}")
    print(f"📝 Descripción: {server_info['description']}")
    print()
    
    # Mostrar endpoints disponibles
    print("🌐 Endpoints MCP disponibles:")
    for endpoint in server_info['endpoints']:
        print(f"  • {endpoint}")
    print()
    
    # Mostrar formatos soportados
    print("📁 Formatos soportados:")
    for category, formats in server_info['supported_formats'].items():
        print(f"  {category.upper()}: {', '.join(formats)}")
    print()
    
    # Mostrar características
    print("✨ Características principales:")
    for feature in server_info['features']:
        print(f"  • {feature}")
    print()
    
    # Mostrar herramientas disponibles
    tools = handler.list_available_tools()
    print("🛠️ Herramientas disponibles:")
    for tool in tools:
        print(f"  • {tool['name']} ({tool['category']})")
        print(f"    {tool['description']}")
        print(f"    Endpoint: {tool['endpoint']}")
        print()
    
    print("🚀 Servidor listo para recibir requests")
    print("Presiona Ctrl+C para detener")
    
    try:
        # Mantener el servidor corriendo
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Cerrando servidor...")
        await handler.agent.shutdown()
        print("✅ Servidor cerrado exitosamente")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error("Error ejecutando servidor MCP: %s", str(e))
        print(f"❌ Error: {e}")