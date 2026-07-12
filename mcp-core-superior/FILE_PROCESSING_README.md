# File Processing Agent MCP

## Descripción

El File Processing Agent MCP es un servidor MCP especializado en el procesamiento avanzado de archivos multimedia y documentos. Proporciona capacidades extensas para extraer, analizar, convertir y procesar una amplia variedad de formatos de archivo.

## 🎯 Características Principales

### 📄 Documentos Soportados
- **PDF**: Extracción de texto, análisis de metadata, detección de tablas
- **DOCX**: Procesamiento de texto, tablas, estilos y estructura
- **XLSX**: Análisis de hojas de cálculo y datos tabulares
- **PPTX**: Extracción de contenido de presentaciones
- **Texto**: TXT, MD, CSV, JSON, HTML con detección automática de codificación

### 🖼️ Imágenes
- **Formatos**: JPG, PNG, TIFF, GIF, BMP, WEBP, SVG
- **Análisis IA**: Descripción de contenido, detección de objetos
- **OCR**: Reconocimiento óptico de caracteres (español e inglés)
- **QR Codes**: Detección y decodificación de códigos QR
- **Conversión**: Entre formatos de imagen con control de calidad

### 🎵 Audio
- **Formatos**: MP3, WAV, FLAC, AAC, OGG
- **Metadata**: Extracción completa de información técnica
- **Análisis**: Waveform, características espectrales, MFCC
- **Conversión**: Entre formatos de audio

### 🎬 Video
- **Formatos**: MP4, AVI, MOV, MKV, WEBM
- **Metadata**: Información técnica completa
- **Frames**: Extracción de frames de ejemplo
- **Análisis**: Características de video y audio

## 🛠️ Herramientas MCP Disponibles

### 1. `extract_text_from_document`
Extrae texto de documentos con análisis avanzado.

**Parámetros:**
- `file_path`: Ruta al archivo de documento
- `encoding`: Codificación específica (opcional, default: utf-8)
- `extract_tables`: Extraer tablas de documentos (default: True)

**Ejemplo:**
```json
{
  "name": "extract_text_from_document",
  "arguments": {
    "file_path": "/path/to/document.pdf",
    "encoding": "utf-8",
    "extract_tables": true
  }
}
```

### 2. `analyze_image_with_ai`
Analiza imágenes usando IA para descripción, OCR y detección de objetos.

**Parámetros:**
- `file_path`: Ruta al archivo de imagen
- `analysis_type`: Tipo de análisis (basic, detailed, ocr, qr_detection, objects, full)
- `ocr_languages`: Idiomas para OCR (default: ["spa", "eng"])

**Ejemplo:**
```json
{
  "name": "analyze_image_with_ai",
  "arguments": {
    "file_path": "/path/to/image.png",
    "analysis_type": "full",
    "ocr_languages": ["spa", "eng"]
  }
}
```

### 3. `convert_file_format`
Convierte archivos entre formatos compatibles.

**Parámetros:**
- `input_file_path`: Ruta del archivo de entrada
- `output_format`: Formato de salida (pdf, txt, docx, xlsx, jpg, png, mp3, mp4)
- `output_file_path`: Ruta del archivo de salida
- `quality`: Calidad de conversión (1-100, default: 85)

**Ejemplo:**
```json
{
  "name": "convert_file_format",
  "arguments": {
    "input_file_path": "/path/to/image.png",
    "output_format": "jpg",
    "output_file_path": "/path/to/image.jpg",
    "quality": 90
  }
}
```

### 4. `extract_metadata`
Extrae metadata completa de cualquier archivo.

**Parámetros:**
- `file_path`: Ruta al archivo
- `include_content_analysis`: Incluir análisis de contenido básico (default: True)

**Ejemplo:**
```json
{
  "name": "extract_metadata",
  "arguments": {
    "file_path": "/path/to/audio.mp3",
    "include_content_analysis": true
  }
}
```

### 5. `process_audio_file`
Procesa archivos de audio para análisis técnico.

**Parámetros:**
- `file_path`: Ruta al archivo de audio
- `analysis_type`: Tipo de análisis (metadata, waveform, features, full)

**Ejemplo:**
```json
{
  "name": "process_audio_file",
  "arguments": {
    "file_path": "/path/to/audio.wav",
    "analysis_type": "full"
  }
}
```

### 6. `process_video_file`
Procesa archivos de video para análisis técnico.

**Parámetros:**
- `file_path`: Ruta al archivo de video
- `extract_frames`: Extraer frames de ejemplo (default: False)
- `frame_count`: Número de frames a extraer (default: 5)

**Ejemplo:**
```json
{
  "name": "process_video_file",
  "arguments": {
    "file_path": "/path/to/video.mp4",
    "extract_frames": true,
    "frame_count": 10
  }
}
```

### 7. `batch_process_files`
Procesa múltiples archivos en lote.

**Parámetros:**
- `file_paths`: Lista de rutas de archivos
- `operation`: Operación a realizar (extract_text, analyze_image, extract_metadata, auto)

**Ejemplo:**
```json
{
  "name": "batch_process_files",
  "arguments": {
    "file_paths": ["/path/to/file1.pdf", "/path/to/file2.jpg", "/path/to/file3.mp3"],
    "operation": "auto"
  }
}
```

## 🚀 Instalación y Configuración

### Dependencias del Sistema

#### Ubuntu/Debian:
```bash
# Instalar Tesseract OCR
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng

# Instalar FFmpeg
sudo apt install ffmpeg

# Instalar dependencias Python
pip install pillow opencv-python pytesseract python-docx openpyxl python-pptx librosa mutagen ffmpeg-python qrcode pyzbar
```

#### macOS:
```bash
# Usando Homebrew
brew install tesseract ffmpeg

# Dependencias Python
pip install pillow opencv-python pytesseract python-docx openpyxl python-pptx librosa mutagen ffmpeg-python qrcode pyzbar
```

#### Windows:
```powershell
# Instalar desde:
# https://github.com/UB-Mannheim/tesseract/wiki
# https://ffmpeg.org/download.html#build-windows

pip install pillow opencv-python pytesseract python-docx openpyxl python-pptx librosa mutagen ffmpeg-python qrcode pyzbar
```

### Ejecución del Servidor

#### 1. Servidor MCP Directo:
```bash
cd mcp-core-superior
python3 file_processing_server.py
```

#### 2. Usar con Cliente MCP:
```bash
# Usando el archivo de configuración
mcp use file_processing_config.json
```

#### 3. Ejecutar Pruebas:
```bash
python3 test_file_processing_agent.py
```

## 📊 Ejemplos de Uso

### Ejemplo 1: Extraer Texto de PDF
```python
import asyncio
from agents.file_processing_agent import FileProcessingAgentMCP

async def extract_pdf_text():
    agent = FileProcessingAgentMCP()
    
    result = await agent.call_tool("extract_text_from_document", {
        "file_path": "documento.pdf",
        "extract_tables": True
    })
    
    if result["success"]:
        print(f"Texto extraído: {result['data']['text'][:200]}...")
        print(f"Páginas: {result['data']['pages']}")
    else:
        print(f"Error: {result['error']}")

asyncio.run(extract_pdf_text())
```

### Ejemplo 2: Analizar Imagen con OCR
```python
async def analyze_image():
    agent = FileProcessingAgentMCP()
    
    result = await agent.call_tool("analyze_image_with_ai", {
        "file_path": "imagen.png",
        "analysis_type": "full",
        "ocr_languages": ["spa", "eng"]
    })
    
    if result["success"]:
        data = result["data"]
        print(f"Descripción: {data.get('description', 'N/A')}")
        print(f"Texto OCR: {data.get('ocr_text', 'N/A')}")
        print(f"Códigos QR: {data.get('qr_codes', [])}")
```

### Ejemplo 3: Procesamiento en Lote
```python
async def batch_process():
    agent = FileProcessingAgentMCP()
    
    result = await agent.call_tool("batch_process_files", {
        "file_paths": [
            "doc1.pdf",
            "imagen1.jpg", 
            "audio1.mp3"
        ],
        "operation": "auto"
    })
    
    if result["success"]:
        data = result["data"]
        print(f"Archivos procesados: {data['processed_count']}")
        print(f"Errores: {data['error_count']}")
```

## ⚙️ Configuración Avanzada

### Límites y Restricciones
- **Tamaño máximo de archivo**: 50MB
- **Archivos por lote**: Máximo 50
- **Idiomas OCR**: Español (spa) e Inglés (eng)
- **Calidad de conversión**: 1-100% (default: 85%)

### Codificaciones Soportadas
- UTF-8 (default)
- Latin-1
- CP1252
- Detección automática

## 🐛 Resolución de Problemas

### Error: "Tesseract no está disponible"
**Solución**: Instalar Tesseract OCR
```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr tesseract-ocr-spa

# macOS
brew install tesseract

# Verificar instalación
tesseract --version
```

### Error: "FFmpeg no está disponible"
**Solución**: Instalar FFmpeg
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Verificar instalación
ffmpeg -version
```

### Error: "OpenCV no está disponible"
**Solución**: Instalar OpenCV
```bash
pip install opencv-python
```

### Error: "Bibliotecas de audio no disponibles"
**Solución**: Instalar librosa
```bash
pip install librosa
```

### Problemas de Memoria
- Reducir tamaño de archivos procesados
- Procesar archivos en lotes más pequeños
- Aumentar memoria disponible para Python

## 📈 Rendimiento

### Optimizaciones
- **Procesamiento asíncrono**: Todas las operaciones son no-bloqueantes
- **Detección automática de tipo**: No requiere especificar formato
- **Cache de resultados**: Evita reprocesamiento innecesario
- **Validación de archivos**: Previene errores antes del procesamiento

### Benchmarks Aproximados
- **PDF (100 páginas)**: ~5-10 segundos
- **Imagen HD**: ~1-3 segundos
- **Audio (5 min)**: ~2-5 segundos
- **Video (720p, 10 min)**: ~10-20 segundos

## 🔧 Desarrollo y Extensión

### Añadir Nuevos Formatos
1. Extender `supported_extensions` en el constructor
2. Implementar método de extracción específico
3. Añadir casos en `extract_text_from_document` o `analyze_image_with_ai`
4. Actualizar `get_tools()` con descripción del nuevo formato

### Añadir Nuevas Herramientas
1. Crear nuevo método `_[nombre_herramienta]`
2. Añadir entrada en `get_tools()`
3. Añadir caso en `call_tool()`
4. Documentar en este README

### Personalizar OCR
- Modificar `ocr_languages` para añadir más idiomas
- Instalar paquetes de idioma Tesseract adicionales
- Ajustar configuración de confianza y precisión

## 📄 Licencia

Este agente MCP es parte del proyecto mcp-core-superior y sigue la misma licencia.

## 🤝 Contribuciones

Para contribuir al File Processing Agent:

1. Fork del repositorio
2. Crear branch de feature
3. Implementar mejoras con tests
4. Submit pull request

## 📞 Soporte

- **Issues**: Crear issue en GitHub
- **Documentación**: Este README
- **Ejemplos**: `test_file_processing_agent.py`

---

**Versión**: 1.0.0  
**Última actualización**: 2025-11-04  
**Mantenido por**: Equipo MCP Core Superior