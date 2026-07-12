# Agentes Especializados MCP Superior

Este directorio contiene 8 nuevos agentes especializados diseñados para herramientas del mundo real, extendiendo las capacidades del sistema MCP Superior.

## 🚀 Agentes Implementados

### 1. Location Intelligence Agent
**Archivo:** `location_intelligence_agent.py`

**Descripción:** Agente de Inteligencia de Ubicación que integra con Google Maps API para proporcionar funcionalidades avanzadas de geolocalización.

**Capacidades:**
- Geocodificación (dirección a coordenadas GPS)
- Geocodificación inversa (coordenadas GPS a dirección)
- Búsqueda de lugares cercanos
- Cálculo de rutas y direcciones
- Matriz de distancias entre múltiples ubicaciones

**Endpoints principales:**
```python
# Geocodificación
await agent.geocode_address("Calle Mayor 15, Madrid")

# Búsqueda de lugares
await agent.search_places("restaurantes", location=(40.4168, -3.7038))

# Obtener direcciones
await agent.get_directions("Madrid", "Barcelona")

# Matriz de distancias
await agent.calculate_distance_matrix(["Madrid", "Barcelona"], ["Valencia", "Sevilla"])
```

### 2. Communication Agent
**Archivo:** `communication_agent.py`

**Descripción:** Agente de Comunicación que maneja email, SMS, notificaciones y gestión de contactos empresariales.

**Capacidades:**
- Envío y recepción de emails
- Gestión de contactos
- Envío de notificaciones push
- Plantillas de email
- Seguimiento de estado de mensajes

**Endpoints principales:**
```python
# Enviar email
await agent.send_email("test@example.com", "Asunto", "Cuerpo del mensaje")

# Agregar contacto
await agent.add_contact("Juan Pérez", "juan@company.com", phone="+34 600 123 456")

# Enviar notificación
await agent.send_notification(["user1", "user2"], "Título", "Mensaje importante")

# Buscar contactos
await agent.search_contacts("juan", filters={"company": "Tech Corp"})
```

### 3. Document Creation Agent
**Archivo:** `document_creation_agent.py`

**Descripción:** Agente de Creación de Documentos para generar, formatear y exportar documentos empresariales.

**Capacidades:**
- Creación de documentos en múltiples formatos
- Generación de hojas de cálculo
- Plantillas predefinidas
- Formateo automático
- Exportación entre formatos

**Endpoints principales:**
```python
# Crear documento
await agent.create_document(
    title="Reporte Mensual",
    content="Contenido del reporte...",
    format_type=DocumentFormat.PDF
)

# Crear hoja de cálculo
await agent.create_spreadsheet(
    name="Ventas 2024",
    headers=["Fecha", "Producto", "Cantidad", "Total"],
    data=[["2024-01-01", "Producto A", 100, 1500.00]]
)

# Usar plantilla
await agent.create_document(
    template_id="template_report",
    variables={"report_title": "Reporte Q1", "author": "Juan Pérez"}
)
```

### 4. Social Media Agent
**Archivo:** `social_media_agent.py`

**Descripción:** Agente de Redes Sociales para gestión multi-plataforma de contenido social.

**Capacidades:**
- Publicación en múltiples plataformas
- Programación de posts
- Análisis de hashtags
- Métricas y analíticas sociales
- Monitoreo de engagement

**Endpoints principales:**
```python
# Crear post
await agent.create_post(
    platform=SocialPlatform.TWITTER,
    content="¡Gran noticia! Acabamos de lanzar nuestro nuevo producto",
    hashtags=["#lanzamiento", "#innovación"],
    content_type=ContentType.TEXT
)

# Programar posts
await agent.schedule_posts([
    {
        "platform": "twitter",
        "content": "Post 1",
        "schedule_type": "optimal"
    }
])

# Obtener analíticas
await agent.get_analytics(platform=SocialPlatform.INSTAGRAM, date_range=30)

# Analizar hashtags
await agent.analyze_hashtags(["#tech", "#innovation"], [SocialPlatform.TWITTER])
```

### 5. Commerce Agent
**Archivo:** `commerce_agent.py`

**Descripción:** Agente de Comercio Electrónico para búsqueda de productos, comparación de precios y gestión de carritos.

**Capacidades:**
- Búsqueda de productos con filtros avanzados
- Comparación de precios multi-plataforma
- Gestión de carritos de compras
- Procesamiento de checkout
- Seguimiento de órdenes

**Endpoints principales:**
```python
# Buscar productos
await agent.search_products(
    query="iPhone",
    category=ProductCategory.ELECTRONICS,
    min_price=1000,
    max_price=1500
)

# Comparar precios
await agent.compare_prices("iPhone 15", platforms=[EcommercePlatform.AMAZON, EcommercePlatform.EBAY])

# Crear carrito
await agent.create_cart({"email": "customer@example.com"})

# Agregar al carrito
await agent.add_to_cart("cart_123", "prod_1", quantity=2)

# Checkout
await agent.checkout_cart("cart_123", shipping_address={...})
```

### 6. Analytics Agent
**Archivo:** `analytics_agent.py`

**Descripción:** Agente de Analíticas para análisis financiero, seguimiento de KPIs y reportes empresariales.

**Capacidades:**
- Reportes financieros automáticos
- Seguimiento de KPIs en tiempo real
- Análisis predictivo
- Dashboards ejecutivos
- Alertas automáticas

**Endpoints principales:**
```python
# Generar reporte financiero
await agent.generate_financial_report(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)

# Registrar KPI
await agent.track_kpi("Ingresos Mensuales", 125000.0, "€", target=150000.0)

# Generar predicción
await agent.generate_forecast("revenue", periods=6, forecast_type="linear")

# Obtener datos de dashboard
await agent.get_dashboard_data("executive")
```

### 7. Scheduling Agent
**Archivo:** `scheduling_agent.py`

**Descripción:** Agente de Programación para gestión de calendarios, coordinación de reuniones y optimización de horarios.

**Capacidades:**
- Gestión completa de calendarios
- Programación automática de reuniones
- Búsqueda de slots disponibles
- Optimización de horarios
- Envío de invitaciones

**Endpoints principales:**
```python
# Crear evento
await agent.create_event(
    title="Reunión de Equipo",
    start_time=datetime(2024, 1, 15, 10, 0),
    end_time=datetime(2024, 1, 15, 11, 0),
    location="Sala A"
)

# Encontrar slots disponibles
await agent.find_meeting_slots(
    duration_minutes=60,
    attendees=["juan@company.com", "maria@company.com"],
    date_range=(start_date, end_date)
)

# Programar reunión automáticamente
await agent.schedule_meeting(meeting_request)

# Enviar invitación
await agent.send_calendar_invite("event_123", ["attendee1@example.com"])
```

### 8. Content Creation Agent
**Archivo:** `content_creation_agent.py`

**Descripción:** Agente de Creación de Contenido Multimedia para generar imágenes, audio, video y contenido textual.

**Capacidades:**
- Generación de imágenes con IA
- Conversión texto a audio
- Generación de videos a partir de texto
- Creación de contenido textual
- Generación en lote

**Endpoints principales:**
```python
# Generar imagen
await agent.generate_image(
    prompt="Un gato en la luna",
    style=ToneStyle.CREATIVE,
    dimensions=(1024, 1024)
)

# Convertir texto a audio
await agent.text_to_audio(
    text="Hola mundo, este es un mensaje de prueba",
    voice_type=VoiceType.FEMALE,
    language="es"
)

# Generar video
await agent.text_to_video(
    prompt="Un paisaje hermoso al atardecer",
    duration_seconds=6
)

# Generar contenido textual
await agent.generate_text_content(
    prompt="Escribe un blog post sobre inteligencia artificial",
    content_type=ContentType.BLOG_POST,
    tone=ToneStyle.EDUCATIONAL
)

# Generación en lote
await agent.batch_generate_content(content_requests)
```

## 🛠️ Configuración y Uso

### Importación
```python
# Importar agentes
from agents.location_intelligence_agent import LocationIntelligenceAgent
from agents.communication_agent import CommunicationAgent
from agents.document_creation_agent import DocumentCreationAgent
from agents.social_media_agent import SocialMediaAgent
from agents.commerce_agent import CommerceAgent
from agents.analytics_agent import AnalyticsAgent
from agents.scheduling_agent import SchedulingAgent
from agents.content_creation_agent import ContentCreationAgent

# Inicializar agentes
location_agent = LocationIntelligenceAgent()
communication_agent = CommunicationAgent()
# ... etc
```

### Procesamiento de Requests
Todos los agentes siguen un patrón consistente para el procesamiento de requests:

```python
# Formato estándar de request
request = {
    "action": "nombre_accion",
    "parametro1": "valor1",
    "parametro2": "valor2"
}

# Procesar request
response = await agent.process_request(request)
```

### Manejo de Respuestas
Todos los agentes devuelven respuestas consistentes:

```python
{
    "success": True,           # Boolean indicando éxito
    "data": {...},            # Datos resultantes
    "error": None,            # Mensaje de error si falló
    "execution_time": 1.23    # Tiempo de ejecución en segundos
}
```

## 📊 Capacidades Principales

### Capacidad de Concurrencia
- **Location Intelligence:** 5 operaciones simultáneas
- **Communication:** 10 operaciones simultáneas
- **Document Creation:** 5 operaciones simultáneas
- **Social Media:** 8 operaciones simultáneas
- **Commerce:** 6 operaciones simultáneas
- **Analytics:** 4 operaciones simultáneas
- **Scheduling:** 6 operaciones simultáneas
- **Content Creation:** 4 operaciones simultáneas

### Timeouts y Retry
- **Timeouts:** 30-120 segundos según el agente
- **Reintentos:** 2-3 intentos automáticos
- **Recuperación:** Sistema de recuperación automática de errores

### Integración con APIs Externas
- **Google Maps:** Geocodificación y mapas
- **Gmail/Outlook:** Gestión de email
- **Redes Sociales:** Twitter, Facebook, Instagram, LinkedIn
- **E-commerce:** Amazon, eBay, Shopify, WooCommerce
- **IA Generativa:** OpenAI, DALL-E, Midjourney
- **TTS/STT:** ElevenLabs, Google Speech-to-Text

## 🧪 Testing

Cada agente incluye tests unitarios y de integración:

```bash
# Ejecutar tests específicos
python -m pytest tests/test_location_intelligence_agent.py -v
python -m pytest tests/test_communication_agent.py -v
# ... etc

# Ejecutar todos los tests
python -m pytest tests/ -v
```

## 📈 Métricas y Monitoreo

Cada agente incluye:
- **Métricas de rendimiento:** Tiempo de respuesta, éxito/fallo
- **Uso de capacidades:** Tracking de capacidades utilizadas
- **Health checks:** Verificación de estado de salud
- **Logs estructurados:** Registro detallado de operaciones

## 🔧 Personalización

Los agentes son altamente configurables:

```python
# Configuración personalizada
agent = LocationIntelligenceAgent(
    timeout_seconds=45,
    retry_attempts=3,
    max_concurrent=10
)

# Habilitar/deshabilitar capacidades
agent.set_maintenance_mode(True)
agent.reset_metrics()
```

## 📚 Ejemplos Prácticos

Ver directorio `examples/` para casos de uso completos:
- Análisis de mercado con Location Intelligence
- Campaña de marketing con Social Media Agent
- Reporte financiero automático con Analytics Agent
- Gestión de eventos corporativos con Scheduling Agent

## 🚀 Próximas Funcionalidades

- [ ] Integración con más APIs de terceros
- [ ] Machine Learning para optimización automática
- [ ] Dashboards web en tiempo real
- [ ] API REST completa para cada agente
- [ ] Plugins y extensiones personalizables
- [ ] Integración con sistemas empresariales (SAP, Salesforce, etc.)

## 🤝 Contribución

Para contribuir nuevos agentes o mejorar existentes:
1. Seguir la estructura base del `BaseAgentWrapper`
2. Implementar capacidades específicas en el enum `AgentCapability`
3. Incluir documentación completa y ejemplos
4. Añadir tests unitarios y de integración
5. Seguir convenciones de nomenclatura establecidas

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver archivo `LICENSE` para más detalles.