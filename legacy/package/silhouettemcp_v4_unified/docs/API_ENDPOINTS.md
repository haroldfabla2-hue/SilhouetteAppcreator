# API Endpoints Documentation - SilhouetteMCP v4.0.0

## 📋 Información General

**Base URL**: `http://tu-servidor:8001`  
**API Version**: `4.0.0-unified`  
**Content Type**: `application/json`  
**Authentication**: Bearer token (admin) o API Key

### Autenticación

La API soporta múltiples métodos de autenticación:

```bash
# Via Bearer Token
Authorization: Bearer tu_token_aqui

# Via API Key
X-API-Key: tu_api_key_aqui

# Via Admin Key
X-Admin-Key: tu_admin_key_aqui
```

## 🏥 Health & Status Endpoints

### GET /health
Verifica el estado del servidor y servicios.

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2024-03-15T10:30:00Z",
    "uptime": "2 days, 5:32:15",
    "active_tasks": 3,
    "completed_tasks": 1247
}
```

### GET /
Endpoint raíz con información del servidor.

**Response:**
```json
{
    "name": "SilhouetteMCP Server - FINAL UNIFIED",
    "version": "4.0.0-unified",
    "description": "Servidor MCP unificado con TODOS los agentes y 51 herramientas",
    "agents_count": 6,
    "total_tools": 51,
    "status": "online",
    "uptime": "2 days, 5:32:15",
    "docs_url": "/docs",
    "redoc_url": "/redoc"
}
```

### GET /stats
Obtiene estadísticas detalladas del sistema.

**Response:**
```json
{
    "system_stats": {
        "total_requests": 15847,
        "successful_requests": 15421,
        "failed_requests": 426,
        "cache_hits": 8934,
        "uptime_start": "2024-03-13T05:00:00Z"
    },
    "agents_info": {
        "maps": {
            "name": "Maps Intelligence Agent",
            "tools_count": 6
        },
        "financial": {
            "name": "Financial Intelligence Agent",
            "tools_count": 9
        },
        "social_travel": {
            "name": "Social Media + Travel Planning Agent",
            "tools_count": 13
        },
        "content": {
            "name": "Content Creation Agent",
            "tools_count": 8
        },
        "database": {
            "name": "Database Operations Agent",
            "tools_count": 13
        },
        "research": {
            "name": "Research Intelligence Agent",
            "tools_count": 2
        }
    },
    "tasks_summary": {
        "total": 1247,
        "pending": 5,
        "processing": 3,
        "completed": 1239,
        "failed": 0
    }
}
```

## 🤖 Agent Management Endpoints

### GET /agents
Lista todos los agentes disponibles.

**Response:**
```json
{
    "agents": [
        {
            "id": "maps",
            "name": "Maps Intelligence Agent",
            "description": "Agente especializado en servicios de geolocalización y mapas",
            "tools_count": 6,
            "version": "1.0.0"
        },
        {
            "id": "financial",
            "name": "Financial Intelligence Agent",
            "description": "Agente especializado en análisis financiero y mercados",
            "tools_count": 9,
            "version": "1.0.0"
        }
    ]
}
```

### GET /agents/{agent_type}
Obtiene información detallada de un agente específico.

**Parameters:**
- `agent_type` (path): ID del agente (maps, financial, social_travel, content, database, research)

**Response:**
```json
{
    "id": "maps",
    "name": "Maps Intelligence Agent",
    "description": "Agente especializado en servicios de geolocalización y mapas",
    "tools": [
        {
            "name": "geocode",
            "description": "Convierte una dirección en coordenadas geográficas",
            "category": "maps",
            "parameters": {
                "address": {
                    "type": "string",
                    "required": true,
                    "description": "Dirección a geocodificar"
                }
            },
            "example_usage": "{\"address\": \"Madrid, España\"}"
        }
    ],
    "version": "1.0.0"
}
```

### GET /tools
Lista todas las herramientas disponibles.

**Response:**
```json
{
    "tools": [
        {
            "name": "geocode",
            "description": "Convierte una dirección en coordenadas geográficas",
            "category": "maps",
            "agent": "maps",
            "parameters": {
                "address": {
                    "type": "string",
                    "required": true,
                    "description": "Dirección a geocodificar"
                }
            },
            "example_usage": "{\"address\": \"Madrid, España\"}"
        }
    ]
}
```

## 🛠️ Tool Execution Endpoints

### POST /execute/{agent_type}/{tool_name}
Ejecuta una herramienta específica.

**Parameters:**
- `agent_type` (path): Tipo de agente
- `tool_name` (path): Nombre de la herramienta
- `parameters` (body): Parámetros para la herramienta

**Example Request:**
```json
{
    "address": "Madrid, España",
    "language": "es"
}
```

**Response:**
```json
{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "agent": "maps",
    "tool": "geocode",
    "parameters": {
        "address": "Madrid, España",
        "language": "es"
    },
    "result": {
        "latitude": 40.4168,
        "longitude": -3.7038,
        "formatted_address": "Madrid, España",
        "place_id": "ChIJn8i6H64cS4gRG1XMGd_mJ8o"
    },
    "processing_time": "0.85s",
    "timestamp": "2024-03-15T10:30:00Z"
}
```

## 📋 Task Management Endpoints

### POST /tasks
Crea una nueva tarea asíncrona.

**Request Body:**
```json
{
    "agent_type": "maps",
    "tool_name": "geocode",
    "parameters": {
        "address": "Madrid, España"
    },
    "user_id": "user123",
    "priority": 5,
    "callback_url": "https://tu-app.com/webhook/task-complete"
}
```

**Response:**
```json
{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "processing",
    "estimated_completion": "2024-03-15T10:30:05Z"
}
```

### GET /tasks/{task_id}
Obtiene el estado de una tarea.

**Response:**
```json
{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "result": {
        "latitude": 40.4168,
        "longitude": -3.7038
    },
    "error": null,
    "created_at": "2024-03-15T10:30:00Z",
    "completed_at": "2024-03-15T10:30:00.850Z"
}
```

### DELETE /tasks/{task_id}
Elimina una tarea.

**Response:**
```json
{
    "message": "Task '550e8400-e29b-41d4-a716-446655440000' deleted"
}
```

## 📁 File Management Endpoints

### POST /upload
Sube un archivo al servidor.

**Request:**
- `file` (form-data): Archivo a subir
- `folder` (form-data, opcional): Carpeta destino (default: "uploads")

**Response:**
```json
{
    "message": "Archivo subido exitosamente",
    "filename": "documento.pdf",
    "size": 2048576,
    "path": "/tmp/uploads/documento.pdf"
}
```

### GET /files/list
Lista archivos en un directorio.

**Query Parameters:**
- `folder` (query): Carpeta a listar (default: "uploads")

**Response:**
```json
{
    "files": [
        {
            "name": "documento.pdf",
            "size": 2048576,
            "modified": "2024-03-15T10:30:00Z"
        }
    ],
    "folder": "uploads"
}
```

### GET /files/dashboard
Sirve el dashboard HTML.

**Response:** HTML del dashboard (sirve archivo directamente)

## 🔍 Maps Intelligence Agent Endpoints

### POST /execute/maps/geocode
Convierte una dirección en coordenadas geográficas.

**Parameters:**
```json
{
    "address": "string (requerido) - Dirección a geocodificar",
    "language": "string (opcional) - Código de idioma (es, en, fr, etc.)"
}
```

### POST /execute/maps/reverse_geocode
Convierte coordenadas en dirección.

**Parameters:**
```json
{
    "latitude": "number (requerido) - Latitud",
    "longitude": "number (requerido) - Longitud",
    "language": "string (opcional) - Código de idioma"
}
```

### POST /execute/maps/search_places
Busca lugares cercanos usando Google Places.

**Parameters:**
```json
{
    "query": "string (requerido) - Consulta de búsqueda",
    "location": "object (opcional) - Objeto con lat/lng",
    "radius": "number (opcional) - Radio en metros (default: 1000)",
    "type": "string (opcional) - Tipo de lugar"
}
```

### POST /execute/maps/place_details
Obtiene detalles de un lugar específico.

**Parameters:**
```json
{
    "place_id": "string (requerido) - ID del lugar",
    "language": "string (opcional) - Código de idioma"
}
```

### POST /execute/maps/distance_matrix
Calcula distancia y tiempo de viaje.

**Parameters:**
```json
{
    "origins": "list (requerido) - Lista de puntos de origen",
    "destinations": "list (requerido) - Lista de puntos de destino",
    "mode": "string (opcional) - Modo de viaje (driving, walking, bicycling, transit)",
    "units": "string (opcional) - Unidades (metric, imperial)"
}
```

### POST /execute/maps/directions
Obtiene direcciones entre dos puntos.

**Parameters:**
```json
{
    "origin": "string (requerido) - Punto de origen",
    "destination": "string (requerido) - Punto de destino",
    "mode": "string (opcional) - Modo de viaje (driving, walking, bicycling, transit)",
    "waypoints": "list (opcional) - Puntos intermedios"
}
```

## 💰 Financial Intelligence Agent Endpoints

### POST /execute/financial/stock_price
Obtiene el precio actual de una acción.

**Parameters:**
```json
{
    "symbol": "string (requerido) - Símbolo de la acción (AAPL, GOOGL, etc.)",
    "source": "string (opcional) - Fuente de datos (yahoo, alpha_vantage, etc.)"
}
```

### POST /execute/financial/crypto_price
Obtiene el precio de criptomonedas.

**Parameters:**
```json
{
    "symbol": "string (requerido) - Símbolo de la criptomoneda (BTC, ETH, etc.)",
    "currency": "string (opcional) - Moneda de referencia (USD, EUR, etc.)"
}
```

### POST /execute/financial/forex_rate
Obtiene tipo de cambio de divisas.

**Parameters:**
```json
{
    "from_currency": "string (requerido) - Moneda origen (USD, EUR, etc.)",
    "to_currency": "string (requerido) - Moneda destino",
    "date": "string (opcional) - Fecha específica (YYYY-MM-DD)"
}
```

### POST /execute/financial/market_news
Obtiene noticias del mercado financiero.

**Parameters:**
```json
{
    "query": "string (opcional) - Términos de búsqueda",
    "limit": "number (opcional) - Número de noticias (default: 10)",
    "category": "string (opcional) - Categoría (business, technology, etc.)"
}
```

### POST /execute/financial/company_info
Obtiene información de una empresa.

**Parameters:**
```json
{
    "symbol": "string (requerido) - Símbolo de la empresa",
    "info_type": "string (opcional) - Tipo de información (profile, financials, etc.)"
}
```

### POST /execute/financial/technical_analysis
Realiza análisis técnico de valores.

**Parameters:**
```json
{
    "symbol": "string (requerido) - Símbolo del valor",
    "indicators": "list (opcional) - Indicadores técnicos (RSI, MACD, etc.)",
    "timeframe": "string (opcional) - Marco temporal (1d, 1h, etc.)"
}
```

### POST /execute/financial/economic_indicators
Obtiene indicadores económicos.

**Parameters:**
```json
{
    "indicator": "string (requerido) - Indicador (GDP, inflation, unemployment, etc.)",
    "country": "string (opcional) - Código de país (US, ES, etc.)",
    "start_date": "string (opcional) - Fecha inicio",
    "end_date": "string (opcional) - Fecha fin"
}
```

### POST /execute/financial/portfolio_analytics
Analiza la composición de un portafolio.

**Parameters:**
```json
{
    "holdings": "list (requerido) - Lista de activos y pesos",
    "benchmark": "string (opcional) - Índice de referencia",
    "analysis_type": "string (opcional) - Tipo de análisis"
}
```

### POST /execute/financial/financial_calendar
Obtiene eventos del calendario financiero.

**Parameters:**
```json
{
    "date": "string (opcional) - Fecha específica",
    "events": "list (opcional) - Tipos de eventos (earnings, dividends, etc.)",
    "symbols": "list (opcional) - Símbolos específicos"
}
```

## 📱 Social Media + Travel Planning Agent Endpoints

### POST /execute/social_travel/social_media_analytics
Analiza métricas de redes sociales.

**Parameters:**
```json
{
    "platform": "string (requerido) - Plataforma (twitter, instagram, facebook, etc.)",
    "account": "string (requerido) - Nombre de cuenta",
    "metrics": "list (opcional) - Métricas específicas",
    "date_range": "object (opcional) - Rango de fechas"
}
```

### POST /execute/social_travel/content_sentiment
Analiza el sentimiento de contenido social.

**Parameters:**
```json
{
    "text": "string (requerido) - Texto a analizar",
    "language": "string (opcional) - Idioma (default: 'es')",
    "analysis_type": "string (opcional) - Tipo de análisis"
}
```

### POST /execute/social_travel/trending_hashtags
Obtiene hashtags trending.

**Parameters:**
```json
{
    "platform": "string (requerido) - Plataforma",
    "location": "string (opcional) - Ubicación",
    "category": "string (opcional) - Categoría"
}
```

### POST /execute/social_travel/influencer_insights
Analiza perfiles de influencers.

**Parameters:**
```json
{
    "username": "string (requerido) - Nombre de usuario",
    "platform": "string (requerido) - Plataforma",
    "analysis_depth": "string (opcional) - Profundidad del análisis"
}
```

### POST /execute/social_travel/social_monitoring
Monitorea menciones de marca.

**Parameters:**
```json
{
    "brand": "string (requerido) - Nombre de la marca",
    "keywords": "list (opcional) - Palabras clave adicionales",
    "timeframe": "string (opcional) - Marco temporal"
}
```

### POST /execute/social_travel/content_calendar
Genera calendario de contenido.

**Parameters:**
```json
{
    "themes": "list (requerido) - Temas del contenido",
    "platforms": "list (requerido) - Plataformas objetivo",
    "start_date": "string (requerido) - Fecha de inicio",
    "frequency": "string (opcional) - Frecuencia (daily, weekly, etc.)"
}
```

### POST /execute/social_travel/travel_destination_search
Busca destinos de viaje.

**Parameters:**
```json
{
    "location": "string (requerido) - Ubicación base",
    "preferences": "list (opcional) - Preferencias (playa, montaña, cultura, etc.)",
    "budget": "string (opcional) - Presupuesto (low, medium, high)",
    "season": "string (opcional) - Temporada"
}
```

### POST /execute/social_travel/flight_search
Busca vuelos.

**Parameters:**
```json
{
    "origin": "string (requerido) - Aeropuerto origen (código IATA)",
    "destination": "string (requerido) - Aeropuerto destino",
    "departure_date": "string (requerido) - Fecha de ida (YYYY-MM-DD)",
    "return_date": "string (opcional) - Fecha de vuelta",
    "passengers": "number (opcional) - Número de pasajeros (default: 1)",
    "class": "string (opcional) - Clase (economy, business, first)"
}
```

### POST /execute/social_travel/hotel_search
Busca hoteles.

**Parameters:**
```json
{
    "destination": "string (requerido) - Destino",
    "checkin": "string (requerido) - Fecha de entrada (YYYY-MM-DD)",
    "checkout": "string (requerido) - Fecha de salida",
    "guests": "number (opcional) - Número de huéspedes (default: 2)",
    "rooms": "number (opcional) - Número de habitaciones",
    "stars": "number (opcional) - Calificación mínima"
}
```

### POST /execute/social_travel/activity_recommendations
Recomienda actividades.

**Parameters:**
```json
{
    "location": "string (requerido) - Ubicación",
    "category": "string (opcional) - Categoría de actividad",
    "budget": "string (opcional) - Presupuesto",
    "duration": "number (opcional) - Duración en horas"
}
```

### POST /execute/social_travel/travel_itinerary
Genera itinerario de viaje.

**Parameters:**
```json
{
    "destination": "string (requerido) - Destino",
    "duration": "number (requerido) - Duración en días",
    "interests": "list (opcional) - Intereses",
    "travel_style": "string (opcional) - Estilo de viaje",
    "budget_level": "string (opcional) - Nivel de presupuesto"
}
```

### POST /execute/social_travel/weather_forecast
Obtiene pronóstico del tiempo.

**Parameters:**
```json
{
    "location": "string (requerido) - Ubicación",
    "date": "string (opcional) - Fecha específica",
    "units": "string (opcional) - Unidades (celsius, fahrenheit)"
}
```

### POST /execute/social_travel/travel_cost_estimator
Estima costo de viaje.

**Parameters:**
```json
{
    "destination": "string (requerido) - Destino",
    "duration": "number (requerido) - Duración en días",
    "travelers": "number (opcional) - Número de viajeros (default: 2)",
    "luxury_level": "string (opcional) - Nivel de lujo (budget, medium, luxury)"
}
```

## 📝 Content Creation Agent Endpoints

### POST /execute/content/text_generation
Genera texto usando IA.

**Parameters:**
```json
{
    "prompt": "string (requerido) - Prompt para la generación",
    "max_tokens": "number (opcional) - Máximo número de tokens (default: 1000)",
    "temperature": "number (opcional) - Creatividad (0.0-1.0, default: 0.7)",
    "model": "string (opcional) - Modelo a usar",
    "style": "string (opcional) - Estilo del texto"
}
```

### POST /execute/content/image_generation
Genera imágenes usando IA.

**Parameters:**
```json
{
    "prompt": "string (requerido) - Descripción de la imagen",
    "style": "string (opcional) - Estilo artístico",
    "size": "string (opcional) - Tamaño (1024x1024, 512x512, etc.)",
    "quality": "string (opcional) - Calidad (standard, hd)",
    "format": "string (opcional) - Formato de salida"
}
```

### POST /execute/content/document_summarization
Resume documentos largos.

**Parameters:**
```json
{
    "content": "string (requerido) - Contenido a resumir",
    "max_length": "number (opcional) - Longitud máxima del resumen (default: 200)",
    "language": "string (opcional) - Idioma (default: 'es')",
    "style": "string (opcional) - Estilo del resumen"
}
```

### POST /execute/content/translation
Traduce texto entre idiomas.

**Parameters:**
```json
{
    "text": "string (requerido) - Texto a traducir",
    "source_language": "string (opcional) - Idioma origen (auto-detect si no se especifica)",
    "target_language": "string (requerido) - Idioma destino",
    "context": "string (opcional) - Contexto adicional"
}
```

### POST /execute/content/seo_optimization
Optimiza contenido para SEO.

**Parameters:**
```json
{
    "content": "string (requerido) - Contenido a optimizar",
    "target_keywords": "list (requerido) - Palabras clave objetivo",
    "meta_description": "string (opcional) - Meta descripción",
    "title": "string (opcional) - Título optimizado",
    "analysis_depth": "string (opcional) - Profundidad del análisis"
}
```

### POST /execute/content/tone_analysis
Analiza el tono del contenido.

**Parameters:**
```json
{
    "text": "string (requerido) - Texto a analizar",
    "analysis_type": "string (opcional) - Tipo de análisis (general, sentiment, formality)",
    "language": "string (opcional) - Idioma del texto"
}
```

### POST /execute/content/content_calendar
Genera calendario editorial.

**Parameters:**
```json
{
    "topics": "list (requerido) - Temas del contenido",
    "platforms": "list (requerido) - Plataformas objetivo",
    "start_date": "string (requerido) - Fecha de inicio",
    "frequency": "string (opcional) - Frecuencia (daily, weekly, monthly)",
    "content_types": "list (opcional) - Tipos de contenido"
}
```

### POST /execute/content/brand_voice_analysis
Analiza la voz de marca.

**Parameters:**
```json
{
    "text_samples": "list (requerido) - Muestras de texto de la marca",
    "brand_attributes": "list (opcional) - Atributos de marca esperados",
    "analysis_type": "string (opcional) - Tipo de análisis"
}
```

## 🗄️ Database Operations Agent Endpoints

### POST /execute/database/supabase_query
Ejecuta consulta en Supabase.

**Parameters:**
```json
{
    "table": "string (requerido) - Nombre de la tabla",
    "operation": "string (requerido) - Operación (select, insert, update, delete)",
    "conditions": "dict (opcional) - Condiciones WHERE",
    "data": "dict (opcional) - Datos para insertar/actualizar",
    "columns": "list (opcional) - Columnas específicas"
}
```

### POST /execute/database/supabase_insert
Inserta datos en Supabase.

**Parameters:**
```json
{
    "table": "string (requerido) - Nombre de la tabla",
    "data": "dict (requerido) - Datos a insertar",
    "returning": "list (opcional) - Campos a retornar"
}
```

### POST /execute/database/supabase_update
Actualiza datos en Supabase.

**Parameters:**
```json
{
    "table": "string (requerido) - Nombre de la tabla",
    "data": "dict (requerido) - Datos a actualizar",
    "conditions": "dict (requerido) - Condiciones WHERE",
    "returning": "list (opcional) - Campos a retornar"
}
```

### POST /execute/database/supabase_delete
Elimina datos de Supabase.

**Parameters:**
```json
{
    "table": "string (requerido) - Nombre de la tabla",
    "conditions": "dict (requerido) - Condiciones WHERE",
    "returning": "list (opcional) - Campos a retornar"
}
```

### POST /execute/database/supabase_create_table
Crea nueva tabla en Supabase.

**Parameters:**
```json
{
    "table_name": "string (requerido) - Nombre de la tabla",
    "columns": "dict (requerido) - Definición de columnas",
    "constraints": "list (opcional) - Restricciones",
    "indexes": "list (opcional) - Índices"
}
```

### POST /execute/database/supabase_schema_migration
Ejecuta migración de esquema.

**Parameters:**
```json
{
    "migration_name": "string (requerido) - Nombre de la migración",
    "sql": "string (requerido) - SQL de la migración",
    "description": "string (opcional) - Descripción de la migración"
}
```

### POST /execute/database/supabase_backup
Crea backup de la base de datos.

**Parameters:**
```json
{
    "backup_name": "string (requerido) - Nombre del backup",
    "tables": "list (opcional) - Tablas específicas",
    "include_schema": "boolean (opcional) - Incluir esquema (default: true)"
}
```

### POST /execute/database/supabase_restore
Restaura desde backup.

**Parameters:**
```json
{
    "backup_name": "string (requerido) - Nombre del backup",
    "tables": "list (opcional) - Tablas a restaurar",
    "overwrite": "boolean (opcional) - Sobrescribir datos existentes"
}
```

### POST /execute/database/supabase_user_management
Gestiona usuarios de Supabase.

**Parameters:**
```json
{
    "operation": "string (requerido) - Operación (create, update, delete, get)",
    "user_data": "dict (requerido) - Datos del usuario",
    "permissions": "list (opcional) - Permisos del usuario"
}
```

### POST /execute/database/supabase_realtime_subscription
Configura suscripción realtime.

**Parameters:**
```json
{
    "table": "string (requerido) - Nombre de la tabla",
    "channel": "string (requerido) - Canal de suscripción",
    "event": "string (opcional) - Evento específico (INSERT, UPDATE, DELETE)",
    "filter": "dict (opcional) - Filtros"
}
```

### POST /execute/database/supabase_storage_upload
Sube archivo a Supabase Storage.

**Parameters:**
```json
{
    "bucket": "string (requerido) - Nombre del bucket",
    "file_path": "string (requerido) - Ruta del archivo",
    "content": "string (requerido) - Contenido del archivo",
    "content_type": "string (opcional) - Tipo MIME",
    "metadata": "dict (opcional) - Metadatos del archivo"
}
```

### POST /execute/database/supabase_storage_download
Descarga archivo de Supabase Storage.

**Parameters:**
```json
{
    "bucket": "string (requerido) - Nombre del bucket",
    "file_path": "string (requerido) - Ruta del archivo",
    "download_path": "string (opcional) - Ruta de descarga local"
}
```

### POST /execute/database/supabase_storage_delete
Elimina archivo de Supabase Storage.

**Parameters:**
```json
{
    "bucket": "string (requerido) - Nombre del bucket",
    "file_path": "string (requerido) - Ruta del archivo",
    "permanently": "boolean (opcional) - Eliminar permanentemente"
}
```

## 🔍 Research Intelligence Agent Endpoints

### POST /execute/research/web_search
Realiza búsqueda web avanzada.

**Parameters:**
```json
{
    "query": "string (requerido) - Consulta de búsqueda",
    "num_results": "number (opcional) - Número de resultados (default: 10)",
    "search_type": "string (opcional) - Tipo de búsqueda (general, news, academic)",
    "language": "string (opcional) - Idioma de los resultados",
    "date_range": "object (opcional) - Rango de fechas"
}
```

### POST /execute/research/academic_research
Búsqueda en literatura académica.

**Parameters:**
```json
{
    "topic": "string (requerido) - Tema de investigación",
    "fields": "list (opcional) - Campos de estudio",
    "date_range": "dict (opcional) - Rango de fechas",
    "max_results": "number (opcional) - Máximo de resultados",
    "include_abstracts": "boolean (opcional) - Incluir resúmenes"
}
```

## 🚀 Ejemplos de Uso Completo

### Ejemplo 1: Geocodificación
```bash
curl -X POST "http://localhost:8001/execute/maps/geocode" \
  -H "Content-Type: application/json" \
  -d '{"address": "Madrid, España"}'
```

### Ejemplo 2: Precio de acción
```bash
curl -X POST "http://localhost:8001/execute/financial/stock_price" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL"}'
```

### Ejemplo 3: Búsqueda de vuelos
```bash
curl -X POST "http://localhost:8001/execute/social_travel/flight_search" \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "MAD",
    "destination": "BCN", 
    "departure_date": "2024-05-01",
    "passengers": 2
  }'
```

### Ejemplo 4: Generación de contenido
```bash
curl -X POST "http://localhost:8001/execute/content/text_generation" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Escribe un artículo sobre inteligencia artificial",
    "max_tokens": 500,
    "style": "profesional"
  }'
```

### Ejemplo 5: Consulta a base de datos
```bash
curl -X POST "http://localhost:8001/execute/database/supabase_query" \
  -H "Content-Type: application/json" \
  -d '{
    "table": "users",
    "operation": "select",
    "conditions": {"active": true}
  }'
```

## 🔐 Seguridad y Rate Limiting

### Rate Limiting
- **Default**: 100 requests por minuto por IP
- **Authenticated**: 1000 requests por minuto
- **Admin**: 5000 requests por minuto

### Headers de Rate Limiting
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1647427200
```

### Códigos de Error Comunes
- `400`: Bad Request - Parámetros inválidos
- `401`: Unauthorized - Autenticación requerida
- `403`: Forbidden - Permisos insuficientes
- `429`: Too Many Requests - Rate limit excedido
- `500`: Internal Server Error - Error del servidor
- `503`: Service Unavailable - Servicio temporalmente no disponible

## 📊 Monitoreo y Métricas

### Prometheus Metrics
El servidor expone métricas en `/metrics` para Prometheus:

- `silhouettemcp_requests_total`: Total de requests
- `silhouettemcp_request_duration_seconds`: Duración de requests
- `silhouettemcp_active_tasks`: Tareas activas
- `silhouettemcp_agent_tools_used`: Uso de herramientas por agente

### Health Checks
- `/health`: Health check básico
- `/health/detailed`: Health check detallado con métricas
- `/health/readiness`: Readiness probe
- `/health/liveness`: Liveness probe

---

Esta documentación cubre todos los endpoints disponibles en SilhouetteMCP v4.0.0. Para más detalles sobre implementación específica, consulta la documentación de cada agente individual.
