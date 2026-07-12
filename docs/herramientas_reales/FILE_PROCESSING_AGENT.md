# 📁 File Processing Agent - Guía Completa

## Descripción General

El **File Processing Agent** es un agente especializado que proporciona capacidades avanzadas de procesamiento de archivos, conversión de formatos, **OCR con Tesseract**, y análisis de documentos usando **herramientas reales**. Es una herramienta **operacional real** que procesa archivos PDF, Excel, CSV, imágenes y más con algoritmos reales de procesamiento.

**Estado**: ✅ **PRODUCCIÓN ACTIVA**  
**Tecnologías**: PyPDF2, pandas, openpyxl, PIL, Tesseract OCR, textract  
**Capacidades**: PDF processing, Excel/CSV analysis, OCR, compression, format conversion  
**Formatos**: PDF, Excel, CSV, JSON, ZIP, images (JPG, PNG, TIFF)  
**OCR**: 100+ idiomas, 95%+ accuracy

## 🎯 Capacidades Principales

### Procesamiento de Documentos PDF
- **Text Extraction**: Extracción de texto de PDFs simples y complejos
- **Image Extraction**: Extracción de imágenes embebidas
- **OCR Integration**: OCR para PDFs escaneados
- **Metadata Extraction**: Información del documento, autor, fechas
- **Page Analysis**: Análisis por página con coordenadas

### Procesamiento de Hojas de Cálculo
- **Excel Processing**: Lectura/escritura de archivos .xlsx, .xls
- **CSV Analysis**: Análisis y transformación de CSV
- **Data Validation**: Validación de datos con reglas custom
- **Pivot Tables**: Generación automática de tablas dinámicas
- **Chart Generation**: Creación de gráficos y visualizaciones

### OCR (Optical Character Recognition)
- **Multi-language OCR**: 100+ idiomas soportados
- **Image Processing**: Mejora de calidad antes de OCR
- **Table Recognition**: Reconocimiento de tablas en imágenes
- **Handwriting Recognition**: Reconocimiento básico de escritura
- **Accuracy Optimization**: Configuración para máxima precisión

### Compresión y Archivos
- **Multi-format Compression**: ZIP, GZ, BZ2, XZ
- **Archive Management**: Creación y extracción de archivos
- **Batch Processing**: Procesamiento masivo de archivos
- **Format Conversion**: Conversión entre formatos
- **Security Scanning**: Escaneo de virus en archivos

## 🛠️ Instalación y Configuración

### Prerrequisitos del Sistema

```bash
# Ubuntu/Devian
sudo apt-get update
sudo apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    tesseract-ocr-eng \
    poppler-utils \
    unrar \
    p7zip-full

# Instalar dependencias adicionales
sudo apt-get install -y \
    imagemagick \
    libmagickwand-dev \
    ghostscript \
    libreoffice
```

### Instalación de Dependencias Python

```bash
# Instalar librerías principales
pip install PyPDF2 pdfplumber pandas openpyxl xlrd
pip install Pillow tesseract pytesseract
pip install textract python-docx python-pptx
pip install opencv-python-headless pytesseract
pip install chardet charset-normalizer

# Para procesamiento avanzado
pip install camelot-py[cv] tabula-py
pip install python-magic-bin  # Windows
pip install xlsxwriter xlwings
```

### Variables de Entorno

```bash
# Configuración Tesseract
export TESSERACT_CMD=/usr/bin/tesseract
export TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

# Configuración de archivos
export FILE_PROCESSING_TEMP_DIR=/tmp/file_processing
export MAX_FILE_SIZE=100MB
export OCR_TIMEOUT=300
export BATCH_SIZE=10

# Configuración de seguridad
export ENABLE_VIRUS_SCAN=true
export ALLOWED_FILE_TYPES="pdf,xlsx,csv,json,zip,jpg,png,tiff"
export BLOCKED_EXTENSIONS="exe,bat,cmd,scr,pif"
```

## 📚 API Reference

### Procesamiento de PDFs

#### 1. Extracción de Texto de PDF

```http
POST /api/v1/tools/file_processing
Content-Type: application/json

{
    "agent": "file_processing",
    "action": "extract_pdf_text",
    "input_file": "/path/to/document.pdf",
    "options": {
        "extract_images": true,
        "extract_metadata": true,
        "pages": "all", // "1-10", "odd", "even"
        "ocr_fallback": true,
        "preserve_layout": false
    },
    "output_format": "structured_json",
    "save_intermediate": true
}
```

**Respuesta:**
```json
{
    "status": "success",
    "data": {
        "text": "Contenido extraído del PDF...",
        "metadata": {
            "title": "Documento de Ejemplo",
            "author": "Autor del Documento",
            "creation_date": "2025-11-04T10:30:00Z",
            "page_count": 15,
            "file_size": "2.5MB"
        },
        "pages": [
            {
                "page_number": 1,
                "text": "Texto de la página 1...",
                "images": [
                    {
                        "path": "/tmp/page1_img1.png",
                        "coordinates": [100, 200, 300, 400]
                    }
                ]
            }
        ],
        "statistics": {
            "total_characters": 45000,
            "total_words": 7500,
            "total_pages": 15
        }
    },
    "files": {
        "text_output": "/tmp/extracted_text.txt",
        "images": ["/tmp/page1_img1.png", "/tmp/page2_img1.png"]
    }
}
```

#### 2. OCR para PDFs Escaneados

```http
POST /api/v1/tools/file_processing
Content-Type: application/json

{
    "agent": "file_processing",
    "action": "ocr_pdf_document",
    "input_file": "/path/to/scanned_document.pdf",
    "ocr_config": {
        "languages": ["spa", "eng"],
        "oem": 3, // LSTM Engine
        "psm": 6, // Uniform block of text
        "whitelist": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,;:!?- ",
        "custom_config": "--dpi 300"
    },
    "preprocessing": {
        "enhance_contrast": true,
        "deskew": true,
        "denoise": true,
        "binarize": true
    },
    "output_format": "structured_json",
    "include_coordinates": true
}
```

### Procesamiento de Excel y CSV

#### 3. Análisis de Excel

```http
POST /api/v1/tools/file_processing
Content-Type: application/json

{
    "agent": "file_processing",
    "action": "analyze_excel_file",
    "input_file": "/path/to/spreadsheet.xlsx",
    "analysis_config": {
        "detect_data_types": true,
        "summary_statistics": true,
        "missing_values_analysis": true,
        "duplicate_detection": true,
        "correlation_analysis": true
    },
    "operations": [
        {
            "operation": "filter",
            "sheet": "Sheet1",
            "column": "Sales",
            "condition": ">",
            "value": 1000
        },
        {
            "operation": "group_by",
            "sheet": "Sheet1",
            "group_column": "Region",
            "agg_column": "Sales",
            "agg_function": "sum"
        },
        {
            "operation": "create_pivot",
            "source_sheet": "Sheet1",
            "rows": ["Region"],
            "columns": ["Product"],
            "values": ["Sales", "Quantity"]
        }
    ],
    "output_format": "json",
    "save_charts": true
}
```

**Respuesta:**
```json
{
    "status": "success",
    "data": {
        "file_info": {
            "sheets": ["SalesData", "Products", "Regions"],
            "total_rows": 15000,
            "total_columns": 25,
            "file_size": "5.2MB"
        },
        "analysis": {
            "data_types": {
                "Sales": "numeric",
                "Date": "datetime",
                "Region": "categorical"
            },
            "summary_stats": {
                "Sales": {
                    "mean": 1250.50,
                    "median": 1100.00,
                    "std": 350.25,
                    "min": 100.00,
                    "max": 5000.00
                }
            },
            "missing_values": {
                "Sales": 15,
                "Date": 3,
                "Region": 0
            },
            "duplicates": {
                "total_rows": 45,
                "percentage": 0.3
            }
        },
        "operations": {
            "filtered_data": {
                "rows_matching": 8500,
                "filter_condition": "Sales > 1000"
            },
            "grouped_data": {
                "regions": ["North", "South", "East", "West"],
                "sales_by_region": {
                    "North": 125000,
                    "South": 98000,
                    "East": 145000,
                    "West": 87000
                }
            }
        }
    },
    "files": {
        "processed_excel": "/tmp/processed_analysis.xlsx",
        "charts": ["/tmp/sales_chart.png", "/tmp/region_chart.png"]
    }
}
```

#### 4. Procesamiento Masivo de CSV

```http
POST /api/v1/tools/file_processing
Content-Type: application/json

{
    "agent": "file_processing",
    "action": "batch_csv_processing",
    "input_files": [
        "/path/to/file1.csv",
        "/path/to/file2.csv",
        "/path/to/file3.csv"
    ],
    "processing_steps": [
        {
            "step": "standardize_encoding",
            "input_encoding": "auto-detect",
            "output_encoding": "utf-8"
        },
        {
            "step": "clean_data",
            "remove_duplicates": true,
            "handle_missing": "fill_mean",
            "remove_outliers": true,
            "outlier_method": "iqr",
            "outlier_threshold": 1.5
        },
        {
            "step": "validate_data",
            "email_validation": true,
            "date_validation": true,
            "numeric_validation": true,
            "custom_rules": [
                {
                    "column": "phone",
                    "pattern": "^\\+?[1-9]\\d{1,14}$",
                    "description": "International phone format"
                }
            ]
        },
        {
            "step": "transform_data",
            "normalize_text": true,
            "date_parsing": true,
            "case_conversion": "lower",
            "remove_whitespace": true
        }
    ],
    "output_config": {
        "output_format": "csv",
        "compression": "gzip",
        "include_processing_log": true
    },
    "validation": {
        "check_output_size": true,
        "validate_columns": true,
        "sample_check": 100
    }
}
```

### OCR Avanzado

#### 5. OCR de Imágenes

```http
POST /api/v1/tools/file_processing
Content-Type: application/json

{
    "agent": "file_processing",
    "action": "ocr_image_document",
    "input_file": "/path/to/scanned_document.jpg",
    "ocr_config": {
        "languages": ["spa", "eng"],
        "engine": "tesseract",
        "oem": 3,
        "psm": 6
    },
    "preprocessing": {
        "resize": {
            "width": 2000,
            "height": 2000,
            "maintain_aspect": true
        },
        "filters": [
            {"type": "grayscale"},
            {"type": "contrast_enhance", "factor": 1.5},
            {"type": "denoise", "method": "gaussian"},
            {"type": "sharpen", "kernel": [0, -1, 0, -1, 5, -1, 0, -1, 0]}
        ],
        "binarization": {
            "method": "adaptive",
            "block_size": 11,
            "constant": 2
        }
    },
    "output_options": {
        "include_confidence": true,
        "include_word_coordinates": true,
        "structure_detection": true,
        "table_detection": true
    }
}
```

#### 6. OCR de Tablas

```http
POST /api/v1/tools/file_processing
Content-Type: application/json

{
    "agent": "file_processing",
    "action": "ocr_table_extraction",
    "input_file": "/path/to/table_image.png",
    "table_config": {
        "detection_method": "opencv", // opencv, pytesseract
        "min_table_width": 100,
        "min_table_height": 50,
        "line_thickness": 2
    },
    "cell_detection": {
        "merge_horizontal": true,
        "merge_vertical": true,
        "handle_merged_cells": true
    },
    "output_format": "csv",
    "save_structure": true,
    "confidence_threshold": 0.7
}
```

### Compresión y Archivos

#### 7. Compresión Masiva

```http
POST /api/v1/tools/file_processing
Content-Type: application/json

{
    "agent": "file_processing",
    "action": "batch_compress_files",
    "input_directory": "/path/to/files",
    "compression_config": {
        "format": "zip", // zip, gz, bz2, xz
        "compression_level": 6,
        "exclude_patterns": ["*.tmp", "*.log", ".git"],
        "include_hidden_files": false
    },
    "organization": {
        "create_subdirs": true,
        "preserve_structure": true,
        "add_timestamp": true
    },
    "security": {
        "virus_scan": true,
        "max_file_size": "50MB",
        "allowed_extensions": ["pdf", "docx", "xlsx", "csv", "txt"]
    }
}
```

#### 8. Conversión de Formatos

```http
POST /api/v1/tools/file_processing
Content-Type: application/json

{
    "agent": "file_processing",
    "action": "convert_file_format",
    "input_file": "/path/to/document.pdf",
    "target_format": "docx",
    "conversion_options": {
        "preserve_formatting": true,
        "extract_images": true,
        "maintain_structure": true,
        "ocr_if_needed": true
    },
    "quality_settings": {
        "image_quality": 95,
        "text_preservation": "high",
        "layout_preservation": "best"
    }
}
```

## 💻 Ejemplos de Uso

### Ejemplo 1: Pipeline de Procesamiento Documental

```python
import requests
import json

# Configuración
base_url = "http://localhost:8000/api/v1/tools/file_processing"
headers = {"Content-Type": "application/json"}

# Pipeline completo de procesamiento documental
document_pipeline = requests.post(base_url, headers=headers, json={
    "agent": "file_processing",
    "action": "document_processing_pipeline",
    "input_files": [
        "/path/to/contract.pdf",
        "/path/to/invoice.pdf", 
        "/path/to/report.xlsx"
    ],
    "pipeline_config": {
        "pdf_processing": {
            "extract_text": True,
            "extract_images": True,
            "ocr_for_scanned": True,
            "extract_metadata": True
        },
        "excel_processing": {
            "analyze_structure": True,
            "validate_data": True,
            "create_summary": True
        },
        "data_extraction": {
            "key_fields": [
                {"pattern": "fecha", "field": "date"},
                {"pattern": "importe|total|amount", "field": "amount"},
                {"pattern": "cliente|customer", "field": "client"}
            ],
            "extract_to_json": True
        }
    },
    "output": {
        "format": "structured_json",
        "include_processing_log": True,
        "create_summary_report": True,
        "save_extracted_images": True
    }
})

result = document_pipeline.json()
print("Pipeline completado:", result["status"])
print(f"Archivos procesados: {len(result['processed_files'])}")
print(f"Campos extraídos: {result['extracted_fields']}")
```

### Ejemplo 2: OCR y Análisis de Documentos Escaneados

```python
# OCR masivo para documentos escaneados
ocr_batch = requests.post(base_url, headers=headers, json={
    "agent": "file_processing",
    "action": "batch_ocr_processing",
    "input_directory": "/path/to/scanned_documents",
    "file_patterns": ["*.pdf", "*.png", "*.jpg", "*.tiff"],
    "ocr_config": {
        "languages": ["spa"],
        "oem": 3,
        "psm": 6,
        "preprocessing": {
            "enhance_quality": True,
            "deskew": True,
            "denoise": True,
            "binarize": True
        }
    },
    "structure_detection": {
        "detect_tables": True,
        "detect_headers": True,
        "detect_footers": True,
        "detect_signatures": True
    },
    "output": {
        "save_text_files": True,
        "save_structured_json": True,
        "include_confidence_scores": True,
        "create_search_index": True
    }
})

result = ocr_batch.json()
print(f"Documentos OCR completados: {result['success_count']}")
print(f"Tiempo promedio por documento: {result['avg_processing_time']}")
```

### Ejemplo 3: Análisis Avanzado de Datos

```python
# Análisis completo de archivos de datos
data_analysis = requests.post(base_url, headers=headers, json={
    "agent": "file_processing",
    "action": "comprehensive_data_analysis",
    "input_files": [
        "/path/to/sales_data.csv",
        "/path/to/customer_data.xlsx"
    ],
    "analysis_config": {
        "statistical_analysis": {
            "descriptive_stats": True,
            "correlation_analysis": True,
            "outlier_detection": True,
            "distribution_analysis": True
        },
        "data_quality": {
            "missing_data_analysis": True,
            "duplicate_detection": True,
            "data_type_validation": True,
            "consistency_checks": True
        },
        "visualization": {
            "create_charts": True,
            "chart_types": ["histogram", "scatter", "heatmap", "box"],
            "save_high_res": True
        }
    },
    "ml_features": {
        "feature_engineering": True,
        "auto_encoding": True,
        "scaling": True,
        "clustering": True
    },
    "output": {
        "format": "comprehensive_report",
        "include_raw_data": False,
        "executive_summary": True,
        "technical_details": True
    }
})

result = data_analysis.json()
print("Análisis completado:")
print(f"- Registros procesados: {result['total_records']}")
print(f"- Calidad de datos: {result['data_quality_score']}/100")
print(f"- Insights generados: {len(result['insights'])}")
```

## 🔧 Configuración Avanzada

### Configuración de OCR

```yaml
# ocr_config.yaml
tesseract:
  path: "/usr/bin/tesseract"
  languages: ["spa", "eng", "fra", "deu"]
  tessdata_path: "/usr/share/tesseract-ocr/4.00/tessdata"
  
preprocessing:
  resize:
    max_width: 2000
    max_height: 2000
    maintain_aspect: true
    
  filters:
    - grayscale
    - contrast_enhance:
        factor: 1.5
    - denoise:
        method: gaussian
    - sharpen:
        kernel: [0, -1, 0, -1, 5, -1, 0, -1, 0]
    - deskew: true
    
  binarization:
    method: adaptive
    block_size: 11
    constant: 2

output:
  include_confidence: true
  include_coordinates: true
  include_structure: true
  format: "structured_json"
```

### Configuración de Procesamiento

```yaml
# processing_config.yaml
file_processing:
  max_file_size: "100MB"
  max_batch_size: 50
  temp_directory: "/tmp/file_processing"
  cleanup_temp_files: true
  
  security:
    virus_scan: true
    allowed_extensions:
      - pdf
      - xlsx
      - csv
      - json
      - zip
      - jpg
      - png
      - tiff
    blocked_extensions:
      - exe
      - bat
      - cmd
      - scr
      - pif
      
  performance:
    parallel_processing: true
    max_workers: 4
    memory_limit: "2GB"
    timeout: 300
    
pdf_processing:
  engine: "pdfplumber"  # pdfplumber, PyPDF2, pymupdf
  extract_images: true
  extract_metadata: true
  ocr_fallback: true
  
excel_processing:
  engine: "openpyxl"  # openpyxl, xlrd
  read_only: false
  data_only: false
  keep_vba: true
```

## 📊 Monitoreo y Métricas

### Métricas de Performance

```python
# Métricas disponibles
metrics = {
    "processing_performance": {
        "files_processed_per_hour": "files/hour throughput",
        "average_processing_time": "time per file by type",
        "ocr_accuracy": "percentage accuracy by language",
        "success_rate": "percentage of successful operations"
    },
    "resource_usage": {
        "memory_usage": "peak memory usage",
        "cpu_usage": "CPU utilization during processing",
        "disk_io": "read/write operations",
        "temp_storage": "temporary file usage"
    },
    "quality_metrics": {
        "ocr_confidence": "average OCR confidence scores",
        "extraction_completeness": "percentage of text extracted",
        "data_accuracy": "validation success rate",
        "format_compatibility": "format support success"
    }
}
```

### Dashboard de Monitoreo

Las métricas están disponibles en:
- **Processing Overview**: Archivos procesados, tiempo promedio, éxito
- **OCR Quality**: Precisión de OCR por idioma, scores de confianza
- **Resource Usage**: Memoria, CPU, almacenamiento temporal
- **Format Support**: Éxito por tipo de archivo, errores comunes

## 🚨 Troubleshooting

### Problemas Comunes

#### Error: Tesseract no encontrado

```python
# Verificar instalación de Tesseract
tesseract_check = requests.post(base_url, headers=headers, json={
    "agent": "file_processing",
    "action": "check_dependencies",
    "check_tesseract": True,
    "check_languages": True
})

print("Estado de dependencias:", tesseract_check.json())

# Instalar idiomas faltantes
# sudo apt-get install tesseract-ocr-spa tesseract-ocr-eng
```

#### Error: Archivos muy grandes

```python
# Configurar límites y chunking
large_file_config = {
    "agent": "file_processing",
    "action": "process_large_file",
    "input_file": "/path/to/large_document.pdf",
    "chunking": {
        "enabled": True,
        "chunk_size_mb": 10,
        "overlap_pages": 5
    },
    "memory_optimization": {
        "stream_processing": True,
        "temp_dir": "/large_temp",
        "cleanup_interval": "each_chunk"
    }
}

large_file_processing = requests.post(base_url, headers=headers, json=large_file_config)
```

#### Error: OCR de baja calidad

```python
# Optimizar preprocessing para mejor OCR
ocr_optimization = {
    "agent": "file_processing",
    "action": "optimize_ocr_quality",
    "input_file": "/path/to/poor_quality_image.jpg",
    "preprocessing": {
        "enhance_resolution": True,
        "upscale_factor": 2,
        "noise_reduction": "advanced",
        "contrast_enhancement": True,
        "edge_enhancement": True
    },
    "ocr_config": {
        "psm": 3,  # Fully automatic page segmentation
        "oem": 1,  # Legacy engine only
        "tesseract_config": "--dpi 300 --psm 3"
    },
    "postprocessing": {
        "spell_check": True,
        "language_model": True,
        "context_correction": True
    }
}
```

### Debugging Avanzado

```bash
# Ver logs del agente
docker-compose logs file-processing-agent

# Habilitar debug detallado
export FILE_PROCESSING_DEBUG=true
export TESSERACT_DEBUG=1

# Verificar dependencias
python -c "import cv2, PIL, pandas; print('Dependencies OK')"
tesseract --version
pdftotext -v
```

## 🔒 Seguridad y Compliance

### Mejores Prácticas de Seguridad

1. **File Validation**: Validación completa de tipos de archivo
2. **Virus Scanning**: Escaneo automático de antivirus
3. **Sandbox Processing**: Procesamiento en sandbox aislado
4. **Temporary Files**: Limpieza automática de archivos temporales
5. **Access Control**: Restricción de acceso por usuario

### Configuración de Seguridad

```yaml
# security_config.yaml
security:
  file_validation:
    magic_number_check: true
    extension_verification: true
    size_limits:
      max_file_size: "100MB"
      max_batch_size: 50
      
  virus_scanning:
    enabled: true
    scan_engine: "clamav"
    quarantine_suspicious: true
    
  sandbox:
    enabled: true
    memory_limit: "1GB"
    cpu_limit: "50%"
    disk_quota: "2GB"
    network_isolation: true
    
  cleanup:
    auto_cleanup: true
    temp_file_ttl: 3600  # 1 hour
    retention_policy: "secure_deletion"
```

## 📈 Optimización

### Performance Tips

1. **Batch Processing**: Procesar múltiples archivos en lote
2. **Parallel Processing**: Usar múltiples workers
3. **Memory Management**: Streaming para archivos grandes
4. **Caching**: Cache de resultados de OCR frecuentes
5. **Hardware**: Usar SSD para mejor I/O

### Configuración de Optimización

```yaml
# optimization_config.yaml
optimization:
  processing:
    parallel_workers: 4
    batch_size: 20
    chunk_processing: true
    streaming_mode: true
    
  memory:
    stream_processing: true
    max_memory_usage: "2GB"
    garbage_collection: "aggressive"
    
  storage:
    temp_storage_type: "ramdisk"
    cache_ocr_results: true
    cache_ttl: 3600
    
  hardware:
    use_gpu_ocr: false  # Enable for faster OCR
    enable_mmx: true
    use_sse: true
```

## 🎯 Casos de Uso Empresariales

### 1. Automatización de Facturación

```python
# Sistema automatizado de procesamiento de facturas
invoice_processing = {
    "input_sources": [
        "email_attachments",
        "upload_portal", 
        "api_endpoint"
    ],
    "processing_pipeline": [
        "extract_from_pdf",
        "ocr_if_needed",
        "parse_invoice_data",
        "validate_against_database",
        "extract_line_items",
        "calculate_totals"
    ],
    "data_extraction": {
        "vendor_info": {"patterns": ["empresa", "proveedor"]},
        "invoice_number": {"patterns": ["factura", "#"]},
        "date": {"patterns": ["fecha", "date"]},
        "amount": {"patterns": ["importe", "total", "amount"]},
        "line_items": {"extract_table": True}
    },
    "validation": {
        "check_duplicate": True,
        "validate_totals": True,
        "match_vendor": True
    },
    "output": {
        "structured_data": True,
        "audit_trail": True,
        "integrate_with_erp": True
    }
}
```

### 2. Procesamiento de Contratos

```python
# Sistema de análisis de contratos
contract_analysis = {
    "document_types": ["contracts", "agreements", "nda"],
    "analysis_features": {
        "key_terms_extraction": {
            "parties": True,
            "dates": True,
            "obligations": True,
            "termination": True,
            "payment_terms": True
        },
        "risk_assessment": {
            "clause_analysis": True,
            "risk_scoring": True,
            "compliance_check": True
        },
        "summarization": {
            "executive_summary": True,
            "key_points": True,
            "action_items": True
        }
    },
    "nlp_features": {
        "entity_recognition": True,
        "sentiment_analysis": True,
        "contract_type_classification": True
    },
    "integration": {
        "legal_database": True,
        "approval_workflow": True,
        "signature_tracking": True
    }
}
```

### 3. Digitalización de Archivos

```python
# Proyecto de digitalización masiva
digitization_project = {
    "scope": {
        "document_types": ["historical", "current", "archives"],
        "volume": "100K+ documents",
        "timeline": "6 months"
    },
    "processing": {
        "batch_ocr": True,
        "quality_control": True,
        "manual_review_queue": True,
        "automated_qc": True
    },
    "organization": {
        "metadata_extraction": True,
        "auto_classification": True,
        "search_indexing": True,
        "access_control": True
    },
    "quality": {
        "ocr_accuracy_target": "95%+",
        "manual_review_rate": "5%",
        "quality_metrics": "comprehensive"
    }
}
```

---

## 📞 Soporte

**Documentación API**: http://localhost:8000/docs#/File%20Processing  
**Issues**: GitHub Issues en el repositorio del proyecto  
**Logs**: http://localhost:8000/logs/file-processing  
**Métricas**: http://localhost:3001 (Grafana dashboard)

---

**🚀 Estado**: **HERRAMIENTA REAL OPERATIVA**  
**📅 Última Actualización**: 2025-11-04  
**✅ Producción**: **READY FOR ENTERPRISE FILE PROCESSING**
