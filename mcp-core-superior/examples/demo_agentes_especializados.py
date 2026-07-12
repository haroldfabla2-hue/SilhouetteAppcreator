"""
Ejemplos prácticos de uso de Agentes Especializados MCP

Este archivo demuestra casos de uso reales para cada uno de los 8 agentes
especializados implementados.

Casos de uso:
1. Análisis de mercado con Location Intelligence Agent
2. Campaña de marketing con Communication y Social Media Agents
3. Reporte financiero automático con Analytics Agent
4. Gestión de evento corporativo con Scheduling Agent
5. Generación de contenido multimedia con Content Creation Agent
6. Proceso completo de e-commerce con Commerce Agent
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Importar agentes
from agents.location_intelligence_agent import LocationIntelligenceAgent
from agents.communication_agent import CommunicationAgent
from agents.social_media_agent import SocialMediaAgent, SocialPlatform, ContentType
from agents.commerce_agent import CommerceAgent, ProductCategory
from agents.analytics_agent import AnalyticsAgent
from agents.scheduling_agent import SchedulingAgent, MeetingRequest
from agents.document_creation_agent import DocumentCreationAgent
from agents.content_creation_agent import ContentCreationAgent, ToneStyle, VoiceType


async def ejemplo_analisis_mercado():
    """
    Ejemplo 1: Análisis de mercado con Location Intelligence Agent
    
    Escenario: Una empresa quiere expandir sus operaciones a nuevas ciudades.
    Necesitan analizar ubicaciones potenciales, calcular distancias a proveedores
    y evaluar la viabilidad de cada ubicación.
    """
    print("🏢 === EJEMPLO 1: ANÁLISIS DE MERCADO CON LOCATION INTELLIGENCE ===\n")
    
    # Inicializar agente
    location_agent = LocationIntelligenceAgent()
    await location_agent._initialize()
    
    # 1. Geocodificar ubicaciones objetivo
    print("📍 Geocodificando ubicaciones objetivo...")
    
    ubicaciones = ["Madrid", "Barcelona", "Valencia", "Sevilla", "Bilbao"]
    coordenadas = {}
    
    for ubicacion in ubicaciones:
        response = await location_agent.geocode_address(ubicacion)
        if response.success:
            coordenadas[ubicacion] = {
                "lat": response.data.latitude,
                "lng": response.data.longitude
            }
            print(f"   ✅ {ubicacion}: {coordenadas[ubicacion]['lat']:.4f}, {coordenadas[ubicacion]['lng']:.4f}")
    
    # 2. Buscar lugares de interés (competidores, centros comerciales, etc.)
    print("\n🏪 Buscando lugares de interés en Madrid...")
    
    places_response = await location_agent.search_places(
        query="centros comerciales",
        location=(coordenadas["Madrid"]["lat"], coordenadas["Madrid"]["lng"]),
        radius=10000
    )
    
    if places_response.success:
        print(f"   ✅ Encontrados {len(places_response.data)} lugares:")
        for place in places_response.data[:3]:  # Mostrar solo los primeros 3
            print(f"      - {place.name}: {place.address} (Rating: {place.rating})")
    
    # 3. Calcular matriz de distancias entre todas las ciudades
    print("\n🗺️ Calculando matriz de distancias...")
    
    matrix_response = await location_agent.calculate_distance_matrix(ubicaciones, ubicaciones)
    
    if matrix_response.success:
        print("   ✅ Matriz de distancias (km):")
        print(f"      {'Ciudad':<12}", end="")
        for ciudad in ubicaciones:
            print(f"{ciudad[:8]:<10}", end="")
        print()
        
        for i, ciudad_origen in enumerate(ubicaciones):
            print(f"      {ciudad_origen:<12}", end="")
            for j, ciudad_destino in enumerate(ubicaciones):
                distancia_km = matrix_response.data[i][j]["distance_km"]
                print(f"{distancia_km:<10.0f}", end="")
            print()
    
    # 4. Obtener direcciones de ejemplo
    print("\n🚗 Calculando ruta Madrid-Barcelona...")
    
    directions_response = await location_agent.get_directions("Madrid", "Barcelona", "driving")
    
    if directions_response.success:
        route = directions_response.data
        print(f"   ✅ Distancia: {route.distance/1000:.0f} km")
        print(f"   ✅ Tiempo estimado: {route.duration/3600:.1f} horas")
        print(f"   ✅ Pasos de la ruta: {len(route.steps)}")
    
    # Mostrar estadísticas
    stats = location_agent.get_stats()
    print(f"\n📊 Estadísticas del agente:")
    print(f"   - Ubicaciones en cache: {stats['cached_locations']}")
    print(f"   - Lugares en cache: {stats['cached_places']}")
    
    return True


async def ejemplo_campana_marketing():
    """
    Ejemplo 2: Campaña de marketing con Communication y Social Media Agents
    
    Escenario: Una empresa lanza un nuevo producto y quiere coordinar
    una campaña de marketing que incluya emails, redes sociales y seguimiento.
    """
    print("\n\n📧 === EJEMPLO 2: CAMPAÑA DE MARKETING ===\n")
    
    # Inicializar agentes
    comm_agent = CommunicationAgent()
    social_agent = SocialMediaAgent()
    
    await comm_agent._initialize()
    await social_agent._initialize()
    
    # 1. Enviar emails de lanzamiento a clientes
    print("📧 Enviando emails de lanzamiento...")
    
    email_response = await comm_agent.send_email(
        to_recipients=["cliente1@empresa.com", "cliente2@empresa.com", "cliente3@empresa.com"],
        subject="🚀 ¡Nuevo Producto Disponible!",
        body="""
        Estimado cliente,
        
        Nos complace anunciarle el lanzamiento de nuestro nuevo producto revolucionário.
        
        ✅ Características principales:
        - Tecnología avanzada
        - Facilidad de uso
        - Precio competitivo
        
        🎁 Oferta especial: 20% de descuento por tiempo limitado
        
        ¡No se pierda esta oportunidad!
        
        Atentamente,
        El equipo de Marketing
        """,
        priority="high"
    )
    
    if email_response.success:
        print(f"   ✅ Email enviado exitosamente (ID: {email_response.message_id})")
    
    # 2. Crear posts para redes sociales
    print("\n📱 Creando contenido para redes sociales...")
    
    posts_content = [
        {
            "platform": SocialPlatform.TWITTER,
            "content": "🚀 ¡GRAN LANZAMIENTO! Nuestro nuevo producto está aquí. #Innovación #Tecnología #Lanzamiento",
            "content_type": ContentType.TEXT
        },
        {
            "platform": SocialPlatform.INSTAGRAM,
            "content": "✨ Behind the scenes de nuestro último desarrollo. ¡La innovación no tiene límites! #TechLife #Innovation",
            "content_type": ContentType.IMAGE,
            "hashtags": ["#tech", "#innovation", "#behindthescenes"]
        },
        {
            "platform": SocialPlatform.LINKEDIN,
            "content": "Empresa líder en tecnología lanza producto revolucionario que transformará el mercado.",
            "content_type": ContentType.TEXT
        }
    ]
    
    created_posts = []
    for post_data in posts_content:
        response = await social_agent.create_post(
            platform=post_data["platform"],
            content=post_data["content"],
            content_type=post_data["content_type"],
            hashtags=post_data.get("hashtags", [])
        )
        
        if response.success:
            created_posts.append(response.post_id)
            print(f"   ✅ Post creado para {post_data['platform'].value}")
    
    # 3. Programar posts adicionales
    print("\n📅 Programando posts adicionales...")
    
    scheduled_posts = [
        {
            "platform": "facebook",
            "content": "Oferta especial: 20% de descuento en nuestro nuevo producto",
            "content_type": "text"
        },
        {
            "platform": "instagram", 
            "content": "Testimonios de clientes satisfechos con nuestro nuevo producto",
            "content_type": "image"
        }
    ]
    
    schedule_response = await social_agent.schedule_posts(scheduled_posts, schedule_type="optimal")
    
    if schedule_response.success:
        print(f"   ✅ {schedule_response.details['posts_created']} posts programados")
    
    # 4. Obtener analíticas de redes sociales
    print("\n📈 Obteniendo analíticas de redes sociales...")
    
    analytics_response = await social_agent.get_analytics(platform=None, date_range=7)
    
    if analytics_response.success:
        print("   ✅ Resumen de analíticas:")
        for platform, data in analytics_response.details["analytics"].items():
            metrics = data["current_metrics"]
            print(f"      {platform}:")
            print(f"         - Seguidores: {metrics['followers']:,}")
            print(f"         - Tasa de engagement: {metrics['engagement_rate']:.1f}%")
            print(f"         - Reach: {metrics['reach']:,}")
    
    # 5. Enviar notificación de seguimiento
    print("\n🔔 Enviando notificación de seguimiento...")
    
    notification_response = await comm_agent.send_notification(
        recipients=["marketing-team", "sales-team"],
        title="Campaña de Lanzamiento - Actualización",
        message="La campaña de lanzamiento está en progreso. Revisar métricas de engagement.",
        notification_type="info"
    )
    
    if notification_response.success:
        print(f"   ✅ Notificación enviada (ID: {notification_response.message_id})")
    
    return True


async def ejemplo_reporte_financiero():
    """
    Ejemplo 3: Reporte financiero automático con Analytics Agent
    
    Escenario: Una empresa necesita generar reportes financieros automáticos
    con KPIs, análisis predictivo y dashboard ejecutivo.
    """
    print("\n\n📊 === EJEMPLO 3: REPORTE FINANCIERO AUTOMÁTICO ===\n")
    
    # Inicializar agente
    analytics_agent = AnalyticsAgent()
    await analytics_agent._initialize()
    
    # 1. Registrar KPIs del mes actual
    print("📈 Registrando KPIs del mes...")
    
    kpis_mes = [
        {"name": "Ingresos Mensuales", "value": 125000.0, "unit": "€", "target": 150000.0},
        {"name": "Margen de Ganancia", "value": 0.25, "unit": "%", "target": 0.30},
        {"name": "ROI", "value": 0.18, "unit": "%", "target": 0.20},
        {"name": "NPS", "value": 72, "unit": "puntos", "target": 75},
        {"name": "Tasa de Conversión", "value": 0.035, "unit": "%", "target": 0.040}
    ]
    
    for kpi in kpis_mes:
        response = await analytics_agent.track_kpi(
            kpi_name=kpi["name"],
            value=kpi["value"],
            unit=kpi["unit"],
            target=kpi["target"]
        )
        
        if response.success:
            change = kpi["change_percentage"] if "change_percentage" in kpi else "N/A"
            print(f"   ✅ {kpi['name']}: {kpi['value']} {kpi['unit']} (Meta: {kpi['target']} {kpi['unit']})")
    
    # 2. Generar reporte financiero del trimestre
    print("\n📋 Generando reporte financiero...")
    
    fecha_inicio = datetime.now() - timedelta(days=90)
    fecha_fin = datetime.now()
    
    report_response = await analytics_agent.generate_financial_report(
        date_range=(fecha_inicio, fecha_fin),
        include_forecasts=True
    )
    
    if report_response.success:
        print(f"   ✅ Reporte generado (ID: {report_response.report_id})")
        
        financial_metrics = report_response.details["financial_metrics"]
        print(f"   📊 Métricas financieras:")
        print(f"      - Ingresos: {financial_metrics['revenue']:,.0f} €")
        print(f"      - Costos: {financial_metrics['costs']:,.0f} €")
        print(f"      - Ganancia: {financial_metrics['profit']:,.0f} €")
        print(f"      - Margen bruto: {financial_metrics['gross_margin']:.1%}")
        print(f"      - ROI: {financial_metrics['roi']:.1%}")
        
        print(f"\n   💡 Insights:")
        for insight in report_response.details["insights"][:3]:
            print(f"      - {insight}")
    
    # 3. Generar predicción de ingresos
    print("\n🔮 Generando predicción de ingresos...")
    
    forecast_response = await analytics_agent.generate_forecast(
        metric_name="revenue",
        periods=6,
        forecast_type="linear"
    )
    
    if forecast_response.success:
        print(f"   ✅ Predicción generada")
        forecasts = forecast_response.details["forecasts"]
        
        print(f"   📈 Predicciones próximas 6 meses:")
        for forecast in forecasts[:3]:  # Mostrar primeros 3
            fecha = datetime.fromisoformat(forecast["date"]).strftime("%b %Y")
            valor = forecast["predicted_value"]
            print(f"      - {fecha}: {valor:,.0f} €")
    
    # 4. Obtener datos de dashboard ejecutivo
    print("\n📱 Cargando dashboard ejecutivo...")
    
    dashboard_response = await analytics_agent.get_dashboard_data("executive")
    
    if dashboard_response.success:
        print(f"   ✅ Dashboard cargado")
        
        dashboard_data = dashboard_response.details
        print(f"   📊 Widgets en dashboard: {len(dashboard_data['widgets'])}")
        
        for widget in dashboard_data["widgets"]:
            widget_type = widget["type"]
            print(f"      - {widget_type}")
            
            if widget_type == "kpi_card" and "data" in widget:
                data = widget["data"]
                print(f"        {data['name']}: {data['value']} {data['unit']}")
    
    return True


async def ejemplo_gestion_evento():
    """
    Ejemplo 4: Gestión de evento corporativo con Scheduling Agent
    
    Escenario: Una empresa organiza una conferencia y necesita coordinar
    horarios, encontrar salas disponibles y enviar invitaciones.
    """
    print("\n\n🗓️ === EJEMPLO 4: GESTIÓN DE EVENTO CORPORATIVO ===\n")
    
    # Inicializar agente
    scheduling_agent = SchedulingAgent()
    await scheduling_agent._initialize()
    
    # 1. Buscar slots disponibles para la conferencia
    print("🔍 Buscando slots disponibles para conferencia...")
    
    fecha_inicio = datetime.now() + timedelta(days=7)
    fecha_fin = datetime.now() + timedelta(days=14)
    
    slots_response = await scheduling_agent.find_meeting_slots(
        duration_minutes=480,  # 8 horas
        attendees=["speaker1@company.com", "speaker2@company.com", "attendee1@company.com"],
        date_range=(fecha_inicio, fecha_fin)
    )
    
    if slots_response.success:
        print(f"   ✅ Encontrados {len(slots_response.details['available_slots'])} slots:")
        
        for slot in slots_response.details["available_slots"][:3]:  # Mostrar top 3
            start_time = datetime.fromisoformat(slot["start_time"])
            end_time = datetime.fromisoformat(slot["end_time"])
            fecha_str = start_time.strftime("%d/%m/%Y %H:%M")
            print(f"      - {fecha_str} (Score: {slot['score']:.2f})")
    
    # 2. Crear evento principal de conferencia
    print("\n📅 Creando evento de conferencia...")
    
    fecha_evento = fecha_inicio + timedelta(hours=10)
    fecha_evento_fin = fecha_evento + timedelta(hours=8)
    
    event_response = await scheduling_agent.create_event(
        title="Conferencia Anual de Tecnología 2024",
        start_time=fecha_evento,
        end_time=fecha_evento_fin,
        description="Conferencia anual sobre las últimas tendencias en tecnología",
        location="Auditorio Principal",
        attendees=[
            {"name": "Dr. Juan Pérez", "email": "juan.perez@company.com"},
            {"name": "Dra. María García", "email": "maria.garcia@company.com"},
            {"name": "Carlos López", "email": "carlos.lopez@company.com"}
        ],
        reminder_minutes=[1440, 60]  # 24 horas y 1 hora antes
    )
    
    if event_response.success:
        print(f"   ✅ Evento creado (ID: {event_response.event_id})")
    
    # 3. Programar reunión de organización previa
    print("\n👥 Programando reunión de organización...")
    
    meeting_request = MeetingRequest(
        title="Reunión de Organización - Conferencia Tech 2024",
        duration_minutes=90,
        attendees=["organizador1@company.com", "organizador2@company.com", "coordinador@company.com"],
        description="Planificación final de la conferencia anual",
        location="Sala de Reuniones A",
        priority="high"
    )
    
    meeting_response = await scheduling_agent.schedule_meeting(meeting_request)
    
    if meeting_response.success:
        print(f"   ✅ Reunión programada (ID: {meeting_response.event_id})")
        scheduled_slot = meeting_response.details["scheduled_slot"]
        start_time = datetime.fromisoformat(scheduled_slot["start_time"])
        print(f"   📅 Fecha: {start_time.strftime('%d/%m/%Y a las %H:%M')}")
    
    # 4. Enviar invitaciones de calendario
    print("\n📧 Enviando invitaciones...")
    
    invite_response = await scheduling_agent.send_calendar_invite(
        event_id=event_response.event_id,
        attendees=["invitado1@empresa.com", "invitado2@empresa.com", "invitado3@empresa.com"],
        message="Te invitamos a nuestra conferencia anual. ¡Esperamos tu asistencia!"
    )
    
    if invite_response.success:
        print(f"   ✅ Invitaciones enviadas")
        print(f"   📧 Destinatarios: {invite_response.details['attendees_count']}")
        print(f"   🔗 URL de calendario: {invite_response.details['calendar_url']}")
    
    # 5. Obtener resumen de calendario
    print("\n📊 Generando resumen de calendario...")
    
    calendar_response = await scheduling_agent.get_calendar_overview(
        date_range=(fecha_inicio - timedelta(days=1), fecha_fin + timedelta(days=1))
    )
    
    if calendar_response.success:
        print(f"   ✅ Resumen generado")
        details = calendar_response.details
        print(f"   📅 Eventos en rango: {details['total_events']}")
        print(f"   ⏰ Horas de reuniones: {details['meeting_hours']}")
        
        if details['calendar_stats']['busiest_day']:
            print(f"   🔥 Día más ocupado: {details['calendar_stats']['busiest_day']}")
    
    return True


async def ejemplo_contenido_multimedia():
    """
    Ejemplo 5: Generación de contenido multimedia con Content Creation Agent
    
    Escenario: Una empresa necesita crear contenido multimedia para su
    campaña de marketing: imágenes, videos, audios y contenido textual.
    """
    print("\n\n🎨 === EJEMPLO 5: CREACIÓN DE CONTENIDO MULTIMEDIA ===\n")
    
    # Inicializar agente
    content_agent = ContentCreationAgent()
    await content_agent._initialize()
    
    # 1. Generar imagen promocional
    print("🖼️ Generando imagen promocional...")
    
    image_response = await content_agent.generate_image(
        prompt="Modern corporate office with innovative technology, professional atmosphere, blue and white color scheme",
        style=ToneStyle.PROFESSIONAL,
        dimensions=(1024, 1024)
    )
    
    if image_response.success:
        print(f"   ✅ Imagen generada (ID: {image_response.content_id})")
        print(f"   📁 Archivo: {image_response.details['file_path']}")
        print(f"   📏 Dimensiones: {image_response.details['dimensions']}")
        print(f"   ⭐ Calidad: {image_response.details['quality_score']:.2f}")
    
    # 2. Generar audio de presentación
    print("\n🎵 Generando audio de presentación...")
    
    audio_text = """
    Bienvenidos a nuestra presentación sobre innovación tecnológica. 
    Hoy descubriremos las últimas tendencias que están transformando el mundo empresarial.
    """
    
    audio_response = await content_agent.text_to_audio(
        text=audio_text,
        voice_type=VoiceType.FEMALE,
        language="es"
    )
    
    if audio_response.success:
        print(f"   ✅ Audio generado (ID: {audio_response.content_id})")
        print(f"   🎵 Duración: {audio_response.details['duration_seconds']:.1f} segundos")
        print(f"   🔊 Voz: {audio_response.details['voice_type']}")
        print(f"   📁 Archivo: {audio_response.details['file_path']}")
    
    # 3. Generar video promocional
    print("\n🎬 Generando video promocional...")
    
    video_response = await content_agent.text_to_video(
        prompt="Professional business presentation with modern graphics, smooth transitions, corporate style",
        duration_seconds=6
    )
    
    if video_response.success:
        print(f"   ✅ Video generado (ID: {video_response.content_id})")
        print(f"   🎥 Duración: {video_response.details['duration_seconds']} segundos")
        print(f"   📺 Resolución: {video_response.details['resolution']}")
        print(f"   📁 Archivo: {video_response.details['file_path']}")
    
    # 4. Generar contenido textual
    print("\n✍️ Generando contenido textual...")
    
    text_response = await content_agent.generate_text_content(
        prompt="Escribe un artículo sobre los beneficios de la transformación digital en las empresas",
        content_type=ContentType.BLOG_POST,
        tone=ToneStyle.EDUCATIONAL,
        target_audience="Ejecutivos empresariales"
    )
    
    if text_response.success:
        print(f"   ✅ Contenido generado (ID: {text_response.content_id})")
        print(f"   📝 Tipo: {text_response.details['content_type']}")
        print(f"   📊 Palabras: {text_response.details['word_count']}")
        print(f"   🎯 Audiencia: {text_response.details.get('target_audience', 'General')}")
        
        # Mostrar preview del contenido
        content_preview = text_response.details["content"][:200] + "..."
        print(f"   📄 Preview: {content_preview}")
    
    # 5. Generación en lote de múltiples contenidos
    print("\n📦 Generación en lote de contenidos...")
    
    from agents.content_creation_agent import ContentRequest
    
    batch_requests = [
        ContentRequest(
            content_type=ContentType.IMAGE,
            prompt="Infographic showing digital transformation benefits",
            style=ToneStyle.PROFESSIONAL,
            dimensions=(800, 600)
        ),
        ContentRequest(
            content_type=ContentType.AUDIO,
            prompt="Welcome message for new customers",
            voice_type=VoiceType.NEUTRAL,
            language="es"
        ),
        ContentRequest(
            content_type=ContentType.VIDEO,
            prompt="Product demonstration video",
            duration_seconds=10
        )
    ]
    
    batch_response = await content_agent.batch_generate_content(batch_requests)
    
    if batch_response.success:
        print(f"   ✅ Lote procesado:")
        print(f"      - Total solicitudes: {batch_response.details['total_requests']}")
        print(f"      - Exitosas: {batch_response.details['successful_generations']}")
        print(f"      - Fallidas: {batch_response.details['failed_generations']}")
        
        for result in batch_response.details["results"][:3]:
            print(f"      - {result['content_type']}: {result['status']}")
    
    # Mostrar estadísticas
    stats = content_agent.get_stats()
    print(f"\n📊 Estadísticas del agente:")
    print(f"   - Total contenidos generados: {stats['total_generated_content']}")
    print(f"   - Por tipo: {stats['content_by_type']}")
    print(f"   - Plantillas disponibles: {len(stats['templates_available'])}")
    
    return True


async def ejemplo_ecommerce_completo():
    """
    Ejemplo 6: Proceso completo de e-commerce con Commerce Agent
    
    Escenario: Cliente busca producto, compara precios, agrega al carrito
    y completa la compra.
    """
    print("\n\n🛒 === EJEMPLO 6: PROCESO COMPLETO E-COMMERCE ===\n")
    
    # Inicializar agente
    commerce_agent = CommerceAgent()
    await commerce_agent._initialize()
    
    # 1. Cliente busca un producto específico
    print("🔍 Cliente buscando 'laptop'...")
    
    search_response = await commerce_agent.search_products(
        query="laptop",
        category=ProductCategory.ELECTRONICS,
        min_price=800,
        max_price=1500,
        min_rating=4.0
    )
    
    if search_response.success:
        products = search_response.details["products"]
        print(f"   ✅ Encontrados {len(products)} productos:")
        
        for product in products[:3]:  # Mostrar top 3
            print(f"      - {product['name']}: {product['price']}€")
            print(f"        Rating: {product['rating']} ⭐ ({product['review_count']} reseñas)")
            print(f"        Marca: {product['brand']}")
    
    # 2. Comparar precios en múltiples plataformas
    print("\n💰 Comparando precios del primer producto...")
    
    if products:
        product_name = products[0]["name"]
        
        price_response = await commerce_agent.compare_prices(
            product_query=product_name,
            platforms=[EcommercePlatform.AMAZON, EcommercePlatform.EBAY, EcommercePlatform.SHOPIFY]
        )
        
        if price_response.success:
            comparison_results = price_response.details["comparison_results"]
            print(f"   ✅ Comparación de precios:")
            
            for result in comparison_results:
                print(f"      - {result['platform']}: {result['price']}€")
                print(f"        Envío: {result['shipping']}")
                print(f"        Tiempo: {result['delivery_time']}")
            
            best_deal = price_response.details["best_deal"]
            if best_deal:
                print(f"\n   🏆 Mejor oferta: {best_deal['platform']} - {best_deal['price']}€")
    
    # 3. Cliente crea carrito de compras
    print("\n🛒 Creando carrito de compras...")
    
    customer_info = {
        "email": "cliente@example.com",
        "name": "Ana García",
        "phone": "+34 600 123 456"
    }
    
    cart_response = await commerce_agent.create_cart(customer_info)
    
    if cart_response.success:
        cart_id = cart_response.transaction_id
        print(f"   ✅ Carrito creado (ID: {cart_id})")
        print(f"   👤 Cliente: {customer_info['name']}")
    
    # 4. Agregar productos al carrito
    print("\n➕ Agregando productos al carrito...")
    
    if products:
        for i, product in enumerate(products[:2]):  # Agregar primeros 2 productos
            add_response = await commerce_agent.add_to_cart(
                cart_id=cart_id,
                product_id=product["id"],
                quantity=i + 1,
                notes=f"Producto prioritario #{i+1}"
            )
            
            if add_response.success:
                print(f"   ✅ Agregado: {product['name']} x{add_response.details['quantity']}")
    
    # 5. Cliente procede al checkout
    print("\n💳 Procesando checkout...")
    
    shipping_address = {
        "street": "Calle Principal 123",
        "city": "Madrid",
        "postal_code": "28001",
        "country": "España"
    }
    
    checkout_response = await commerce_agent.checkout_cart(
        cart_id=cart_id,
        shipping_address=shipping_address,
        payment_method="credit_card",
        discount_code="DESCUENTO10"
    )
    
    if checkout_response.success:
        order_id = checkout_response.transaction_id
        details = checkout_response.details
        
        print(f"   ✅ Pedido completado (ID: {order_id})")
        print(f"   💰 Total: {details['total_amount']:.2f}€")
        print(f"   📦 Estado: {details['payment_status']}")
        print(f"   🚚 Entrega estimada: {details['estimated_delivery']}")
        print(f"   📋 Tracking: {details['tracking_number']}")
    
    # Mostrar estadísticas
    stats = commerce_agent.get_stats()
    print(f"\n📊 Estadísticas del agente:")
    print(f"   - Productos disponibles: {stats['total_products']}")
    print(f"   - Carritos activos: {stats['active_carts']}")
    print(f"   - Órdenes completadas: {stats['completed_orders']}")
    print(f"   - Plataformas soportadas: {len(stats['supported_platforms'])}")
    
    return True


async def main():
    """
    Función principal que ejecuta todos los ejemplos
    """
    print("🚀 === DEMOSTRACIÓN COMPLETA DE AGENTES ESPECIALIZADOS MCP ===\n")
    
    try:
        # Ejecutar ejemplos secuencialmente
        await ejemplo_analisis_mercado()
        await ejemplo_campana_marketing()
        await ejemplo_reporte_financiero()
        await ejemplo_gestion_evento()
        await ejemplo_contenido_multimedia()
        await ejemplo_ecommerce_completo()
        
        print("\n\n🎉 === DEMOSTRACIÓN COMPLETADA EXITOSAMENTE ===")
        print("✅ Todos los agentes especializados funcionando correctamente")
        print("\n📋 Resumen de funcionalidades demostradas:")
        print("   🗺️ Location Intelligence: Geocodificación, búsqueda de lugares, rutas")
        print("   📧 Communication: Email, notificaciones, gestión de contactos")
        print("   📱 Social Media: Creación de posts, programación, analíticas")
        print("   📊 Analytics: Reportes financieros, KPIs, predicciones")
        print("   🗓️ Scheduling: Gestión de eventos, coordinación de reuniones")
        print("   🎨 Content Creation: Imágenes, audio, video, texto")
        print("   🛒 Commerce: Búsqueda de productos, comparación, checkout")
        
    except Exception as e:
        print(f"\n❌ Error durante la demostración: {str(e)}")
        return False
    
    return True


if __name__ == "__main__":
    # Ejecutar demostración
    asyncio.run(main())