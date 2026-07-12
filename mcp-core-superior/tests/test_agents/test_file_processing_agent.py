"""
Unit tests para FileProcessingAgent
Procesamiento avanzado de archivos multimedia y documentos
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any, List
import json
import tempfile
import os

import sys
import os as sys_os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Mock dependencies
with patch.dict('sys.modules', {
    'cv2': Mock(),
    'PIL': Mock(),
    'pytesseract': Mock(),
    'openpyxl': Mock(),
    'pptx': Mock(),
    'librosa': Mock(),
    'mutagen': Mock(),
    'ffmpeg': Mock(),
    'qrcode': Mock(),
    'backend.tools.file_processor': Mock()
}):
    from src.agents.file_processing_agent import FileProcessingAgentMCP


class TestFileProcessingAgentMCP:
    """Test suite para FileProcessingAgentMCP"""
    
    @pytest.fixture
    def file_agent(self):
        """Fixture para crear instancia del FileProcessingAgent"""
        return FileProcessingAgentMCP()
    
    @pytest.fixture
    def temp_file(self):
        """Fixture para crear archivo temporal"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"Test content")
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_initialization(self, file_agent):
        """Test inicialización del FileProcessingAgent"""
        assert file_agent is not None
        assert file_agent.logger is not None
        assert file_agent.file_processor is not None
        assert hasattr(file_agent, 'allowed_mime_types')
    
    @pytest.mark.asyncio
    async def test_extract_text_from_pdf(self, file_agent):
        """Test extracción de texto de PDF"""
        with patch.object(file_agent, 'extract_text_from_pdf') as mock_extract:
            mock_extract.return_value = {
                "success": True,
                "text": "Texto extraído del PDF",
                "pages": 3,
                "metadata": {"title": "Document PDF"}
            }
            
            result = await file_agent.extract_text_from_pdf("/path/to/document.pdf")
            
            assert "success" in result
            assert "text" in result
            assert "pages" in result
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_extract_text_from_docx(self, file_agent):
        """Test extracción de texto de DOCX"""
        with patch.object(file_agent, 'extract_text_from_docx') as mock_extract:
            mock_extract.return_value = {
                "success": True,
                "text": "Texto extraído del DOCX",
                "paragraphs": 5,
                "metadata": {"title": "Document DOCX"}
            }
            
            result = await file_agent.extract_text_from_docx("/path/to/document.docx")
            
            assert "success" in result
            assert "text" in result
            assert "paragraphs" in result
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_process_excel_file(self, file_agent):
        """Test procesamiento de archivo Excel"""
        with patch.object(file_agent, 'process_excel_file') as mock_process:
            mock_process.return_value = {
                "success": True,
                "sheets": ["Sheet1", "Sheet2"],
                "data": {
                    "Sheet1": [["Name", "Age"], ["John", "30"]],
                    "Sheet2": [["Product", "Price"], ["Widget", "10.99"]]
                },
                "metadata": {"total_rows": 3, "total_cols": 2}
            }
            
            result = await file_agent.process_excel_file("/path/to/spreadsheet.xlsx")
            
            assert "success" in result
            assert "sheets" in result
            assert "data" in result
            assert len(result["sheets"]) == 2
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_extract_text_from_image_ocr(self, file_agent):
        """Test extracción de texto de imagen con OCR"""
        with patch.object(file_agent, 'extract_text_from_image') as mock_extract:
            mock_extract.return_value = {
                "success": True,
                "text": "Texto extraído via OCR",
                "confidence": 0.95,
                "language": "eng",
                "bbox": [[0, 0, 100, 20]]
            }
            
            result = await file_agent.extract_text_from_image("/path/to/image.png")
            
            assert "success" in result
            assert "text" in result
            assert "confidence" in result
            assert "language" in result
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_analyze_image_content(self, file_agent):
        """Test análisis de contenido de imagen"""
        with patch.object(file_agent, 'analyze_image_content') as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "objects_detected": ["person", "car", "tree"],
                "colors": ["blue", "white", "green"],
                "dimensions": {"width": 1920, "height": 1080},
                "format": "JPEG",
                "size_mb": 2.5
            }
            
            result = await file_agent.analyze_image_content("/path/to/photo.jpg")
            
            assert "success" in result
            assert "objects_detected" in result
            assert "colors" in result
            assert "dimensions" in result
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_process_audio_file(self, file_agent):
        """Test procesamiento de archivo de audio"""
        with patch.object(file_agent, 'process_audio_file') as mock_process:
            mock_process.return_value = {
                "success": True,
                "duration_seconds": 180.5,
                "sample_rate": 44100,
                "channels": 2,
                "bitrate": "320kbps",
                "metadata": {"artist": "Test Artist", "title": "Test Song"},
                "transcription": "Letra de la canción extraída"
            }
            
            result = await file_agent.process_audio_file("/path/to/audio.mp3")
            
            assert "success" in result
            assert "duration_seconds" in result
            assert "metadata" in result
            assert "transcription" in result
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_process_video_file(self, file_agent):
        """Test procesamiento de archivo de video"""
        with patch.object(file_agent, 'process_video_file') as mock_process:
            mock_process.return_value = {
                "success": True,
                "duration_seconds": 3600,
                "resolution": "1920x1080",
                "fps": 30,
                "codec": "H.264",
                "size_mb": 500,
                "transcription": "Texto del video extraído",
                "key_frames": 10
            }
            
            result = await file_agent.process_video_file("/path/to/video.mp4")
            
            assert "success" in result
            assert "duration_seconds" in result
            assert "resolution" in result
            assert "transcription" in result
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_extract_metadata(self, file_agent):
        """Test extracción de metadata"""
        with patch.object(file_agent, 'extract_metadata') as mock_metadata:
            mock_metadata.return_value = {
                "success": True,
                "file_type": "image/jpeg",
                "size_bytes": 1048576,
                "created": "2025-01-01T12:00:00Z",
                "modified": "2025-01-01T12:00:00Z",
                "mime_type": "image/jpeg",
                "encoding": "UTF-8"
            }
            
            result = await file_agent.extract_metadata("/path/to/file")
            
            assert "success" in result
            assert "file_type" in result
            assert "size_bytes" in result
            assert "mime_type" in result
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_convert_file_format(self, file_agent):
        """Test conversión de formato de archivo"""
        with patch.object(file_agent, 'convert_file_format') as mock_convert:
            mock_convert.return_value = {
                "success": True,
                "output_path": "/path/to/converted/file.pdf",
                "source_format": "docx",
                "target_format": "pdf",
                "conversion_time_seconds": 5.2
            }
            
            result = await file_agent.convert_file_format(
                "/path/to/document.docx",
                "/path/to/output.pdf"
            )
            
            assert "success" in result
            assert "output_path" in result
            assert "source_format" in result
            assert "target_format" in result
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_process_csv_data(self, file_agent):
        """Test procesamiento de datos CSV"""
        with patch.object(file_agent, 'process_csv_data') as mock_process:
            mock_process.return_value = {
                "success": True,
                "columns": ["Name", "Age", "City"],
                "rows": [["John", "30", "NYC"], ["Jane", "25", "LA"]],
                "total_rows": 2,
                "data_types": {"Name": "string", "Age": "integer", "City": "string"},
                "statistics": {"avg_age": 27.5, "unique_cities": 2}
            }
            
            result = await file_agent.process_csv_data("/path/to/data.csv")
            
            assert "success" in result
            assert "columns" in result
            assert "rows" in result
            assert "data_types" in result
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_process_json_data(self, file_agent):
        """Test procesamiento de datos JSON"""
        with patch.object(file_agent, 'process_json_data') as mock_process:
            mock_process.return_value = {
                "success": True,
                "data": {"key1": "value1", "key2": {"nested": "value2"}},
                "keys": ["key1", "key2"],
                "data_types": {"key1": "string", "key2": "object"},
                "structure_valid": True
            }
            
            result = await file_agent.process_json_data("/path/to/data.json")
            
            assert "success" in result
            assert "data" in result
            assert "keys" in result
            assert "structure_valid" in result
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_extract_qr_code(self, file_agent):
        """Test extracción de código QR"""
        with patch.object(file_agent, 'extract_qr_code') as mock_extract:
            mock_extract.return_value = {
                "success": True,
                "qr_data": "https://example.com",
                "qr_type": "URL",
                "confidence": 0.98,
                "bbox": [[0, 0], [100, 0], [100, 100], [0, 100]]
            }
            
            result = await file_agent.extract_qr_code("/path/to/qr_image.png")
            
            assert "success" in result
            assert "qr_data" in result
            assert "qr_type" in result
            assert "confidence" in result
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_batch_process_files(self, file_agent):
        """Test procesamiento en lote de archivos"""
        files = [
            "/path/to/file1.pdf",
            "/path/to/file2.jpg", 
            "/path/to/file3.mp3"
        ]
        
        with patch.object(file_agent, 'batch_process_files') as mock_batch:
            mock_batch.return_value = {
                "success": True,
                "total_files": 3,
                "successful": 3,
                "failed": 0,
                "results": [
                    {"file": files[0], "success": True, "type": "pdf"},
                    {"file": files[1], "success": True, "type": "image"},
                    {"file": files[2], "success": True, "type": "audio"}
                ]
            }
            
            result = await file_agent.batch_process_files(files)
            
            assert "success" in result
            assert "total_files" in result
            assert "successful" in result
            assert "results" in result
            assert result["total_files"] == 3
            assert result["successful"] == 3
    
    @pytest.mark.asyncio
    async def test_compress_image(self, file_agent):
        """Test compresión de imagen"""
        with patch.object(file_agent, 'compress_image') as mock_compress:
            mock_compress.return_value = {
                "success": True,
                "output_path": "/path/to/compressed/image.jpg",
                "original_size_mb": 5.2,
                "compressed_size_mb": 1.8,
                "compression_ratio": 0.65,
                "quality": 85
            }
            
            result = await file_agent.compress_image(
                "/path/to/large_image.jpg",
                "/path/to/output.jpg",
                quality=85
            )
            
            assert "success" in result
            assert "output_path" in result
            assert "compression_ratio" in result
            assert "quality" in result
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_resize_image(self, file_agent):
        """Test redimensionamiento de imagen"""
        with patch.object(file_agent, 'resize_image') as mock_resize:
            mock_resize.return_value = {
                "success": True,
                "output_path": "/path/to/resized/image.jpg",
                "original_size": {"width": 1920, "height": 1080},
                "new_size": {"width": 800, "height": 600},
                "aspect_ratio_maintained": True
            }
            
            result = await file_agent.resize_image(
                "/path/to/original.jpg",
                "/path/to/resized.jpg",
                width=800,
                height=600
            )
            
            assert "success" in result
            assert "output_path" in result
            assert "original_size" in result
            assert "new_size" in result
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_extract_tables_from_image(self, file_agent):
        """Test extracción de tablas de imagen"""
        with patch.object(file_agent, 'extract_tables_from_image') as mock_extract:
            mock_extract.return_value = {
                "success": True,
                "tables_found": 2,
                "tables": [
                    {
                        "table_id": 1,
                        "rows": [["Header1", "Header2"], ["Data1", "Data2"]],
                        "confidence": 0.92
                    },
                    {
                        "table_id": 2,
                        "rows": [["Col1", "Col2"], ["Val1", "Val2"]],
                        "confidence": 0.88
                    }
                ]
            }
            
            result = await file_agent.extract_tables_from_image("/path/to/table_image.png")
            
            assert "success" in result
            assert "tables_found" in result
            assert "tables" in result
            assert len(result["tables"]) == 2
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_detect_file_type(self, file_agent):
        """Test detección de tipo de archivo"""
        test_cases = [
            ("/path/to/document.pdf", "pdf"),
            ("/path/to/image.jpg", "image"),
            ("/path/to/audio.mp3", "audio"),
            ("/path/to/video.mp4", "video"),
            ("/path/to/data.json", "json")
        ]
        
        for file_path, expected_type in test_cases:
            with patch.object(file_agent, 'detect_file_type') as mock_detect:
                mock_detect.return_value = {
                    "success": True,
                    "file_type": expected_type,
                    "mime_type": f"application/{expected_type}",
                    "extension": f".{expected_type}"
                }
                
                result = await file_agent.detect_file_type(file_path)
                
                assert result["success"] is True
                assert result["file_type"] == expected_type
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_file(self, file_agent):
        """Test manejo de errores - archivo inválido"""
        with patch.object(file_agent, 'process_file') as mock_process:
            mock_process.side_effect = FileNotFoundError("File not found")
            
            with pytest.raises(FileNotFoundError):
                await file_agent.process_file("/nonexistent/file.pdf")
    
    @pytest.mark.asyncio
    async def test_error_handling_unsupported_format(self, file_agent):
        """Test manejo de errores - formato no soportado"""
        with patch.object(file_agent, 'process_file') as mock_process:
            mock_process.return_value = {
                "success": False,
                "error": "Unsupported file format",
                "supported_formats": ["pdf", "docx", "jpg", "png", "mp3", "mp4"]
            }
            
            result = await file_agent.process_file("/path/to/file.xyz")
            
            assert result["success"] is False
            assert "Unsupported file format" in result["error"]
            assert "supported_formats" in result
    
    @pytest.mark.asyncio
    async def test_error_handling_corrupted_file(self, file_agent):
        """Test manejo de errores - archivo corrupto"""
        with patch.object(file_agent, 'process_file') as mock_process:
            mock_process.return_value = {
                "success": False,
                "error": "File appears to be corrupted",
                "error_code": "CORRUPTED_FILE",
                "suggestion": "Try to repair or re-download the file"
            }
            
            result = await file_agent.process_file("/path/to/corrupted.pdf")
            
            assert result["success"] is False
            assert "corrupted" in result["error"].lower()
            assert "suggestion" in result
    
    @pytest.mark.asyncio
    async def test_file_validation(self, file_agent):
        """Test validación de archivo"""
        with patch.object(file_agent, 'validate_file') as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "file_size": 1048576,
                "mime_type": "application/pdf",
                "checksum": "abc123def456",
                "virus_scan": "clean"
            }
            
            result = await file_agent.validate_file("/path/to/document.pdf")
            
            assert "valid" in result
            assert "file_size" in result
            assert "mime_type" in result
            assert "checksum" in result
            assert "virus_scan" in result
            assert result["valid"] is True
    
    @pytest.mark.asyncio
    async def test_create_thumbnail(self, file_agent):
        """Test creación de thumbnail"""
        with patch.object(file_agent, 'create_thumbnail') as mock_thumb:
            mock_thumb.return_value = {
                "success": True,
                "thumbnail_path": "/path/to/thumbnails/image_thumb.jpg",
                "thumbnail_size": (150, 150),
                "original_size": (1920, 1080),
                "format": "JPEG"
            }
            
            result = await file_agent.create_thumbnail(
                "/path/to/large_image.jpg",
                size=(150, 150)
            )
            
            assert "success" in result
            assert "thumbnail_path" in result
            assert "thumbnail_size" in result
            assert result["success"] is True
