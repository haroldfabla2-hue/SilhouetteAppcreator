#!/bin/bash
# Script de instalación para File Processing Agent MCP
# Instala dependencias del sistema y Python necesarias

set -e

echo "🚀 INSTALACIÓN DE FILE PROCESSING AGENT MCP"
echo "=============================================="

# Detectar sistema operativo
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*)    MACHINE=Cygwin;;
    MINGW*)     MACHINE=MinGw;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo "📍 Sistema operativo detectado: $MACHINE"

# Función para instalar dependencias en Ubuntu/Debian
install_ubuntu_deps() {
    echo "🐧 Instalando dependencias para Ubuntu/Debian..."
    
    # Actualizar repositorios
    sudo apt update
    
    # Instalar dependencias del sistema
    echo "📦 Instalando Tesseract OCR..."
    sudo apt install -y tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng
    
    echo "🎬 Instalando FFmpeg..."
    sudo apt install -y ffmpeg
    
    echo "📸 Instalando bibliotecas de imagen..."
    sudo apt install -y libjpeg-dev libpng-dev libtiff-dev libgif-dev libwebp-dev
    
    echo "🔊 Instalando bibliotecas de audio..."
    sudo apt install -y libasound2-dev portaudio19-dev
    
    echo "✅ Dependencias del sistema Ubuntu/Debian instaladas"
}

# Función para instalar dependencias en macOS
install_macos_deps() {
    echo "🍎 Instalando dependencias para macOS..."
    
    # Verificar si Homebrew está instalado
    if ! command -v brew &> /dev/null; then
        echo "⚠️ Homebrew no está instalado. Instalando..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    echo "🔍 Instalando dependencias con Homebrew..."
    brew install tesseract tesseract-lang
    brew install ffmpeg
    brew install portaudio
    
    echo "✅ Dependencias del sistema macOS instaladas"
}

# Función para instalar dependencias en Windows (manual)
install_windows_info() {
    echo "🪟 INSTALACIÓN PARA WINDOWS - PASOS MANUALES"
    echo "============================================="
    echo ""
    echo "1. Descargar e instalar Tesseract OCR:"
    echo "   👉 https://github.com/UB-Mannheim/tesseract/wiki"
    echo "   👉 Descargar tesseract-ocr-w64-setup-v5.x.x.exe"
    echo ""
    echo "2. Descargar e instalar FFmpeg:"
    echo "   👉 https://ffmpeg.org/download.html#build-windows"
    echo "   👉 Descargar ffmpeg-release-essentials.zip"
    echo ""
    echo "3. Añadir ambos al PATH del sistema:"
    echo "   👉 Panel de Control > Sistema > Configuración avanzada > Variables de entorno"
    echo "   👉 Añadir rutas de Tesseract y FFmpeg a PATH"
    echo ""
    echo "4. Reiniciar terminal después de la instalación"
    echo ""
}

# Función para instalar dependencias Python
install_python_deps() {
    echo "🐍 Instalando dependencias Python..."
    
    # Crear entorno virtual si no existe
    if [ ! -d ".venv" ]; then
        echo "📦 Creando entorno virtual..."
        python3 -m venv .venv
    fi
    
    # Activar entorno virtual
    echo "🔧 Activando entorno virtual..."
    source .venv/bin/activate
    
    # Actualizar pip
    echo "📚 Actualizando pip..."
    pip install --upgrade pip setuptools wheel
    
    # Instalar dependencias principales
    echo "🖼️ Instalando dependencias para procesamiento de imágenes..."
    pip install Pillow opencv-python
    
    echo "🔤 Instalando dependencias para OCR..."
    pip install pytesseract
    
    echo "📄 Instalando dependencias para documentos Office..."
    pip install python-docx openpyxl python-pptx
    
    echo "🎵 Instalando dependencias para audio..."
    pip install librosa mutagen
    
    echo "🎬 Instalando dependencias para video..."
    pip install ffmpeg-python
    
    echo "📱 Instalando dependencias para códigos QR..."
    pip install qrcode pyzbar
    
    echo "🔧 Instalando dependencias adicionales..."
    pip install chardet PyPDF2 pypdf soundfile piexif
    
    echo "🧪 Instalando dependencias de desarrollo..."
    pip install pytest pytest-asyncio black flake8
    
    echo "✅ Dependencias Python instaladas"
}

# Función para verificar instalación
verify_installation() {
    echo ""
    echo "🔍 VERIFICANDO INSTALACIÓN..."
    echo "=============================="
    
    # Activar entorno virtual si existe
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    # Verificar Python
    echo "🐍 Verificando Python..."
    python3 --version
    
    # Verificar dependencias Python principales
    echo ""
    echo "📦 Verificando dependencias Python:"
    
    python3 -c "
import sys
modules = [
    'PIL', 'cv2', 'pytesseract', 'docx', 'openpyxl', 'pptx',
    'librosa', 'mutagen', 'ffmpeg', 'qrcode', 'pyzbar'
]

failed = []
for module in modules:
    try:
        __import__(module)
        print(f'✅ {module} - OK')
    except ImportError:
        print(f'❌ {module} - FALTA')
        failed.append(module)

if failed:
    print(f'\n⚠️  Módulos faltantes: {failed}')
    sys.exit(1)
else:
    print('\n🎉 Todas las dependencias Python están instaladas')
"
    
    # Verificar dependencias del sistema
    echo ""
    echo "🔧 Verificando dependencias del sistema:"
    
    if command -v tesseract &> /dev/null; then
        echo "✅ Tesseract OCR - OK"
        tesseract --version | head -1
    else
        echo "❌ Tesseract OCR - NO ENCONTRADO"
    fi
    
    if command -v ffmpeg &> /dev/null; then
        echo "✅ FFmpeg - OK"
        ffmpeg -version | head -1 | cut -d' ' -f1-3
    else
        echo "❌ FFmpeg - NO ENCONTRADO"
    fi
    
    echo ""
    echo "✅ Verificación completada"
}

# Función para crear archivos de prueba
create_test_files() {
    echo ""
    echo "📝 CREANDO ARCHIVOS DE PRUEBA..."
    echo "================================"
    
    mkdir -p test_files
    
    # Crear archivo de texto de prueba
    cat > test_files/test_document.txt << 'EOF'
# Documento de Prueba

Este es un archivo de texto de prueba para el File Processing Agent.

## Características:
- Formato Markdown
- Múltiples líneas
- Caracteres especiales: áéíóú ñ ç

Contenido adicional para testing.
EOF
    
    # Crear archivo JSON de prueba
    cat > test_files/test_data.json << 'EOF'
{
  "name": "Test Document",
  "version": "1.0",
  "content": {
    "text": "Este es un documento de prueba",
    "metadata": {
      "created": "2025-11-04",
      "type": "test"
    }
  }
}
EOF
    
    # Crear CSV de prueba
    cat > test_files/test_data.csv << 'EOF'
nombre,edad,ciudad
Juan,25,Madrid
María,30,Barcelona
Carlos,28,Valencia
EOF
    
    echo "✅ Archivos de prueba creados en test_files/"
}

# Función para ejecutar pruebas
run_tests() {
    echo ""
    echo "🧪 EJECUTANDO PRUEBAS..."
    echo "========================"
    
    if [ -f "test_file_processing_agent.py" ]; then
        echo "Ejecutando script de pruebas del agente..."
        python3 test_file_processing_agent.py
    else
        echo "⚠️ Archivo de pruebas no encontrado"
    fi
}

# Función para mostrar información de uso
show_usage_info() {
    echo ""
    echo "📋 INFORMACIÓN DE USO"
    echo "====================="
    echo ""
    echo "🔧 Comandos disponibles:"
    echo "  python3 file_processing_server.py    - Ejecutar servidor MCP"
    echo "  python3 test_file_processing_agent.py - Ejecutar pruebas"
    echo ""
    echo "📁 Archivos importantes:"
    echo "  file_processing_agent.py     - Agente principal"
    echo "  file_processing_server.py    - Servidor MCP"
    echo "  file_processing_config.json  - Configuración"
    echo "  FILE_PROCESSING_README.md    - Documentación"
    echo ""
    echo "🖼️ Formatos soportados:"
    echo "  Documentos: PDF, DOCX, XLSX, PPTX, TXT, MD, CSV, JSON, HTML"
    echo "  Imágenes: JPG, PNG, TIFF, GIF, BMP, WEBP, SVG"
    echo "  Audio: MP3, WAV, FLAC, AAC, OGG"
    echo "  Video: MP4, AVI, MOV, MKV, WEBM"
    echo ""
}

# Menú principal
echo ""
echo "Selecciona una opción:"
echo "1) Instalación completa (recomendado)"
echo "2) Solo dependencias del sistema"
echo "3) Solo dependencias Python"
echo "4) Verificar instalación"
echo "5) Crear archivos de prueba"
echo "6) Ejecutar pruebas"
echo "7) Mostrar información de uso"
echo "8) Información para Windows"
echo "q) Salir"
echo ""

read -p "Opción [1-8, q]: " choice

case $choice in
    1)
        echo "🚀 INSTALACIÓN COMPLETA"
        echo "======================="
        
        # Instalar según el sistema
        case $MACHINE in
            Linux)
                install_ubuntu_deps
                ;;
            Mac)
                install_macos_deps
                ;;
            Cygwin|MinGw)
                install_windows_info
                exit 0
                ;;
            *)
                echo "⚠️ Sistema operativo no soportado automáticamente"
                echo "Por favor instalar manualmente: Tesseract, FFmpeg"
                ;;
        esac
        
        install_python_deps
        verify_installation
        create_test_files
        show_usage_info
        ;;
        
    2)
        echo "🔧 INSTALANDO DEPENDENCIAS DEL SISTEMA"
        echo "======================================"
        case $MACHINE in
            Linux)
                install_ubuntu_deps
                ;;
            Mac)
                install_macos_deps
                ;;
            Cygwin|MinGw)
                install_windows_info
                ;;
            *)
                echo "❌ Sistema operativo no soportado"
                exit 1
                ;;
        esac
        ;;
        
    3)
        echo "🐍 INSTALANDO DEPENDENCIAS PYTHON"
        echo "================================="
        install_python_deps
        verify_installation
        ;;
        
    4)
        echo "🔍 VERIFICANDO INSTALACIÓN"
        echo "========================="
        verify_installation
        ;;
        
    5)
        echo "📝 CREANDO ARCHIVOS DE PRUEBA"
        echo "============================="
        create_test_files
        ;;
        
    6)
        echo "🧪 EJECUTANDO PRUEBAS"
        echo "===================="
        run_tests
        ;;
        
    7)
        show_usage_info
        ;;
        
    8)
        install_windows_info
        ;;
        
    q|Q)
        echo "👋 Saliendo..."
        exit 0
        ;;
        
    *)
        echo "❌ Opción no válida"
        exit 1
        ;;
esac

echo ""
echo "🎉 Instalación completada exitosamente"
echo "📚 Consulta FILE_PROCESSING_README.md para más información"