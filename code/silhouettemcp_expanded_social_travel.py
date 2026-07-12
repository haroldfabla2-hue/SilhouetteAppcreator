#!/usr/bin/env python3
"""
Silhouette MCP Server - Versión Expandida con Integración de Redes Sociales y Viajes
Social Media Intelligence Agent + Travel Planning Agent

Herramientas incluidas:
- Social Media Intelligence (5 herramientas)
  - Twitter: twitter_search_tweets, twitter_get_user_info, twitter_get_user_tweets
  - Pinterest: pinterest_search_pins, pinterest_get_user_info

- Travel Planning (8 herramientas)  
  - Booking: flights_search, hotels_search, hotel_details
  - TripAdvisor: search_locations, nearby_search, location_details, reviews, photos

Endpoints MCP organizados por categoría:
- /mcp/social/twitter/*
- /mcp/social/pinterest/*
- /mcp/travel/booking/*
- /mcp/travel/tripadvisor/*
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import aiohttp
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    CallToolResult,
    GetPromptResult,
    ListPromptsResult,
    ListResourcesResult,
    ListToolsResult,
    Prompt,
    Resource,
    Tool,
    logging as mcp_logging,
)

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("silhouette-mcp-expanded")

# Inicializar servidor MCP
server = Server("silhouette-mcp-expanded-social-travel")

# =============================================================================
# SOCIAL MEDIA INTELLIGENCE AGENT
# =============================================================================

class SocialMediaIntelligenceAgent:
    """Agente para inteligencia de redes sociales"""
    
    def __init__(self):
        self.twitter_api_key = None
        self.pinterest_api_key = None
    
    async def twitter_search_tweets(
        self, 
        query: str, 
        count: int = 10,
        result_type: str = "recent",
        lang: str = "es"
    ) -> Dict[str, Any]:
        """Buscar tweets en Twitter"""
        try:
            # Simulación de búsqueda en Twitter
            # En implementación real, usarías la API de Twitter
            tweets_data = {
                "query": query,
                "count": count,
                "tweets": [
                    {
                        "id": f"tweet_{i}",
                        "text": f"Ejemplo de tweet sobre {query} #{i}",
                        "user": {
                            "id": f"user_{i}",
                            "screen_name": f"usuario_{i}",
                            "name": f"Usuario {i}",
                            "followers_count": 1000 + i * 100,
                        },
                        "created_at": datetime.now().isoformat(),
                        "retweet_count": i * 5,
                        "favorite_count": i * 10,
                        "engagement_score": (i * 5 + i * 10) / 100
                    }
                    for i in range(count)
                ],
                "metrics": {
                    "total_results": count,
                    "engagement_rate": 0.05,
                    "sentiment_score": 0.75,
                    "top_hashtags": ["#tendencia", "#noticias", "#social"],
                    "influencers": [f"@usuario_{i}" for i in range(3)]
                }
            }
            
            logger.info(f"Twitter search completed for query: {query}")
            return tweets_data
            
        except Exception as e:
            logger.error(f"Error in twitter_search_tweets: {str(e)}")
            return {"error": f"Error searching tweets: {str(e)}"}
    
    async def twitter_get_user_info(self, username: str) -> Dict[str, Any]:
        """Obtener información de usuario de Twitter"""
        try:
            # Simulación de obtención de información de usuario
            user_data = {
                "username": username,
                "user_id": f"user_{username}",
                "profile": {
                    "name": f"Usuario {username}",
                    "screen_name": username,
                    "description": f"Bio del usuario {username}",
                    "location": "España",
                    "url": f"https://twitter.com/{username}",
                    "verified": False,
                    "followers_count": 2500,
                    "following_count": 500,
                    "tweets_count": 1250,
                    "listed_count": 25,
                    "favourites_count": 850,
                    "created_at": "2020-01-01T00:00:00Z",
                    "profile_image_url": f"https://pbs.twimg.com/profile_images/{username}.jpg"
                },
                "analytics": {
                    "engagement_rate": 0.035,
                    "avg_likes_per_tweet": 12.5,
                    "avg_retweets_per_tweet": 3.2,
                    "posting_frequency": "2-3 tweets/day",
                    "influence_score": 7.5,
                    "top_mentions": ["@empresa", "@noticias", "@tendencia"]
                }
            }
            
            logger.info(f"Twitter user info retrieved for: {username}")
            return user_data
            
        except Exception as e:
            logger.error(f"Error in twitter_get_user_info: {str(e)}")
            return {"error": f"Error getting user info: {str(e)}"}
    
    async def twitter_get_user_tweets(
        self, 
        username: str, 
        count: int = 20,
        exclude_replies: bool = True
    ) -> Dict[str, Any]:
        """Obtener tweets de un usuario específico"""
        try:
            # Simulación de obtención de tweets del usuario
            tweets_data = {
                "username": username,
                "count": count,
                "tweets": [
                    {
                        "id": f"tweet_user_{i}",
                        "text": f"Tweet de @{username} sobre tema relevante #{i}",
                        "created_at": (datetime.now().timestamp() - i * 3600).isoformat(),
                        "favorite_count": 15 + i * 2,
                        "retweet_count": 5 + i,
                        "reply_count": i // 2,
                        "quote_count": i // 3,
                        "has_media": i % 3 == 0,
                        "engagement_score": ((15 + i * 2) + (5 + i)) / 100,
                        "sentiment": "positive" if i % 2 == 0 else "neutral"
                    }
                    for i in range(count)
                ],
                "summary": {
                    "total_likes": sum(15 + i * 2 for i in range(count)),
                    "total_retweets": sum(5 + i for i in range(count)),
                    "avg_engagement": 0.045,
                    "posting_trend": "stable",
                    "best_performing_hour": "18:00-19:00",
                    "top_categories": ["tecnología", "noticias", "entretenimiento"]
                }
            }
            
            logger.info(f"Twitter user tweets retrieved for: {username}")
            return tweets_data
            
        except Exception as e:
            logger.error(f"Error in twitter_get_user_tweets: {str(e)}")
            return {"error": f"Error getting user tweets: {str(e)}"}
    
    async def pinterest_search_pins(
        self, 
        query: str, 
        count: int = 25,
        board: Optional[str] = None
    ) -> Dict[str, Any]:
        """Buscar pines en Pinterest"""
        try:
            # Simulación de búsqueda en Pinterest
            pins_data = {
                "query": query,
                "count": count,
                "board_filter": board,
                "pins": [
                    {
                        "id": f"pin_{i}",
                        "title": f"Pinterest Pin sobre {query} #{i}",
                        "description": f"Descripción del pin {i} relacionado con {query}",
                        "image_url": f"https://images.pinterest.com/photos/{i}.jpg",
                        "link": f"https://pinterest.com/pin/{i}",
                        "pinner": {
                            "id": f"pinner_{i}",
                            "username": f"usuario_pinterest_{i}",
                            "name": f"Pinner {i}",
                            "followers": 1500 + i * 100,
                        },
                        "stats": {
                            "likes": 25 + i * 5,
                            "comments": i // 3,
                            "saves": 15 + i * 3,
                            "clicks": 50 + i * 10
                        },
                        "board": f"Board sobre {query}",
                        "created_at": datetime.now().isoformat(),
                        "engagement_rate": ((25 + i * 5) + (15 + i * 3)) / 1000
                    }
                    for i in range(count)
                ],
                "analytics": {
                    "total_impressions": count * 1000,
                    "avg_engagement": 0.035,
                    "top_categories": ["diseño", "moda", "lifestyle", "viajes"],
                    "trending_keywords": [query, f"trends_{query}", "inspiration"]
                }
            }
            
            logger.info(f"Pinterest search completed for query: {query}")
            return pins_data
            
        except Exception as e:
            logger.error(f"Error in pinterest_search_pins: {str(e)}")
            return {"error": f"Error searching Pinterest pins: {str(e)}"}
    
    async def pinterest_get_user_info(self, username: str) -> Dict[str, Any]:
        """Obtener información de usuario de Pinterest"""
        try:
            # Simulación de información de usuario de Pinterest
            user_data = {
                "username": username,
                "user_id": f"pinterest_user_{username}",
                "profile": {
                    "first_name": username.capitalize(),
                    "last_name": "Pinterest",
                    "username": username,
                    "bio": f"Creative user passionate about {username}",
                    "location": "Madrid, España",
                    "website": f"https://{username}.com",
                    "profile_image": f"https://images.pinterest.com/user_{username}.jpg",
                    "verified": False
                },
                "stats": {
                    "followers": 3500,
                    "following": 850,
                    "boards": 125,
                    "pins": 2750,
                    "monthly_views": 45000
                },
                "boards": [
                    {
                        "id": f"board_{i}",
                        "name": f"Board de {username} #{i}",
                        "description": f"Colección sobre tema {i}",
                        "pin_count": 50 + i * 10,
                        "followers": 100 + i * 20,
                        "category": ["diseño", "moda", "viajes", "comida"][i % 4]
                    }
                    for i in range(5)
                ],
                "analytics": {
                    "engagement_rate": 0.042,
                    "most_engaged_board": "Board de diseño",
                    "top_categories": ["diseño", "moda", "decoración"],
                    "optimal_posting_times": ["19:00-21:00", "12:00-14:00"],
                    "audience_demographics": {
                        "age_range": "25-34",
                        "gender": "70% mujeres",
                        "top_countries": ["España", "México", "Argentina"]
                    }
                }
            }
            
            logger.info(f"Pinterest user info retrieved for: {username}")
            return user_data
            
        except Exception as e:
            logger.error(f"Error in pinterest_get_user_info: {str(e)}")
            return {"error": f"Error getting Pinterest user info: {str(e)}"}

# =============================================================================
# TRAVEL PLANNING AGENT
# =============================================================================

class TravelPlanningAgent:
    """Agente para planificación de viajes"""
    
    def __init__(self):
        self.booking_api_key = None
        self.tripadvisor_api_key = None
    
    async def flights_search(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        travel_class: str = "economy"
    ) -> Dict[str, Any]:
        """Buscar vuelos en Booking"""
        try:
            # Simulación de búsqueda de vuelos
            flights_data = {
                "search_params": {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date,
                    "return_date": return_date,
                    "adults": adults,
                    "travel_class": travel_class
                },
                "flights": [
                    {
                        "id": f"flight_{i}",
                        "airline": ["Iberia", "Vueling", "Air Europa"][i % 3],
                        "flight_number": f"IB{1000 + i}",
                        "origin": origin,
                        "destination": destination,
                        "departure_time": f"08:{(30 + i * 15) % 60:02d}",
                        "arrival_time": f"10:{(45 + i * 15) % 60:02d}",
                        "duration": "2h 15m",
                        "price": 89.99 + i * 15.50,
                        "currency": "EUR",
                        "stops": 0 if i % 2 == 0 else 1,
                        "aircraft": ["A320", "B737", "A319"][i % 3],
                        "baggage_included": True,
                        "meal_included": i % 3 == 0,
                        "booking_class": travel_class
                    }
                    for i in range(5)
                ],
                "filters": {
                    "price_range": {"min": 89.99, "max": 164.99},
                    "duration_range": {"min": "2h 15m", "max": "4h 30m"},
                    "airlines": ["Iberia", "Vueling", "Air Europa"],
                    "departure_times": ["06:00-12:00", "12:00-18:00", "18:00-24:00"]
                },
                "recommendations": {
                    "best_value": "flight_1",
                    "shortest_duration": "flight_0",
                    "most_convenient": "flight_2"
                }
            }
            
            logger.info(f"Flight search completed: {origin} -> {destination}")
            return flights_data
            
        except Exception as e:
            logger.error(f"Error in flights_search: {str(e)}")
            return {"error": f"Error searching flights: {str(e)}"}
    
    async def hotels_search(
        self,
        destination: str,
        checkin_date: str,
        checkout_date: str,
        guests: int = 2,
        rooms: int = 1,
        budget_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """Buscar hoteles en Booking"""
        try:
            # Simulación de búsqueda de hoteles
            nights = 2  # Calculado basado en fechas
            hotels_data = {
                "search_params": {
                    "destination": destination,
                    "checkin_date": checkin_date,
                    "checkout_date": checkout_date,
                    "guests": guests,
                    "rooms": rooms,
                    "nights": nights
                },
                "hotels": [
                    {
                        "id": f"hotel_{i}",
                        "name": f"Hotel {destination} #{i}",
                        "address": f"Calle Principal {i}, {destination}",
                        "rating": 4.2 + i * 0.2,
                        "stars": 3 + i,
                        "price_per_night": 85.00 + i * 25.00,
                        "total_price": (85.00 + i * 25.00) * nights,
                        "currency": "EUR",
                        "images": [
                            f"https://images.booking.com/hotel_{i}_1.jpg",
                            f"https://images.booking.com/hotel_{i}_2.jpg"
                        ],
                        "amenities": [
                            "WiFi gratuito", "Aire acondicionado", "Desayuno incluido"
                        ] + (["Piscina", "Spa", "Gimnasio"] if i % 2 == 0 else []),
                        "cancellation_policy": "Gratuita hasta 24h antes",
                        "distance_to_center": f"{i * 0.5:.1f} km del centro",
                        "guest_review_score": 8.5 + i * 0.3,
                        "reviews_count": 150 + i * 25
                    }
                    for i in range(6)
                ],
                "filters": {
                    "price_range": {"min": 85.00, "max": 235.00},
                    "rating_range": {"min": 3.0, "max": 5.0},
                    "distance_range": {"min": "0.5km", "max": "3.0km"}
                },
                "booking_trends": {
                    "peak_season": "Junio-Agosto",
                    "avg_stay": "2-3 noches",
                    "popular_amenities": ["WiFi", "Desayuno", "Parking"]
                }
            }
            
            logger.info(f"Hotel search completed for: {destination}")
            return hotels_data
            
        except Exception as e:
            logger.error(f"Error in hotels_search: {str(e)}")
            return {"error": f"Error searching hotels: {str(e)}"}
    
    async def hotel_details(self, hotel_id: str) -> Dict[str, Any]:
        """Obtener detalles específicos de un hotel"""
        try:
            # Simulación de detalles del hotel
            hotel_details = {
                "hotel_id": hotel_id,
                "basic_info": {
                    "name": "Hotel Premium Plaza",
                    "address": "Plaza Mayor 1, Madrid",
                    "phone": "+34 91 123 4567",
                    "email": "info@hotelpremium.com",
                    "website": "https://www.hotelpremium.com"
                },
                "room_types": [
                    {
                        "type": "Habitación Estándar",
                        "size": "25 m²",
                        "capacity": "2 personas",
                        "bed_type": "Cama doble",
                        "price": 120.00,
                        "amenities": ["WiFi", "TV", "Aire acondicionado", "Minibar"]
                    },
                    {
                        "type": "Suite Junior",
                        "size": "40 m²",
                        "capacity": "3 personas",
                        "bed_type": "Cama doble + sofá cama",
                        "price": 180.00,
                        "amenities": ["WiFi", "TV", "Aire acondicionado", "Minibar", "Balcón", "Jacuzzi"]
                    }
                ],
                "services": [
                    "Recepción 24h",
                    "Servicio de habitaciones",
                    "Restaurante",
                    "Bar",
                    "Spa y centro de bienestar",
                    "Gimnasio",
                    "Parking (15€/día)",
                    "WiFi gratuito en todo el hotel"
                ],
                "policies": {
                    "check_in": "15:00",
                    "check_out": "12:00",
                    "cancellation": "Gratuita hasta 24h antes",
                    "pets": "Permitidas con cargo adicional",
                    "smoking": "Prohibido en habitaciones"
                },
                "nearby_attractions": [
                    "Plaza Mayor (100m)",
                    "Museo del Prado (500m)",
                    "Mercado de San Miguel (200m)",
                    "Palacio Real (800m)"
                ]
            }
            
            logger.info(f"Hotel details retrieved for: {hotel_id}")
            return hotel_details
            
        except Exception as e:
            logger.error(f"Error in hotel_details: {str(e)}")
            return {"error": f"Error getting hotel details: {str(e)}"}
    
    async def search_locations(
        self,
        query: str,
        location_type: str = "all",
        limit: int = 10
    ) -> Dict[str, Any]:
        """Buscar ubicaciones en TripAdvisor"""
        try:
            # Simulación de búsqueda de ubicaciones
            locations_data = {
                "query": query,
                "location_type": location_type,
                "locations": [
                    {
                        "id": f"location_{i}",
                        "name": f"{query} {['Centro', 'Norte', 'Sur', 'Este', 'Oeste'][i]}",
                        "type": ["ciudad", "monumento", "museo", "parque", "restaurante"][i % 5],
                        "address": f"Dirección {i}, {query}",
                        "city": query,
                        "country": "España",
                        "coordinates": {
                            "latitude": 40.4168 + i * 0.01,
                            "longitude": -3.7038 + i * 0.01
                        },
                        "rating": 4.0 + i * 0.2,
                        "review_count": 100 + i * 25,
                        "category": ["Turismo", "Cultura", "Gastronomía", "Naturaleza"][i % 4],
                        "description": f"Descubre {query} en esta {['ubicación única', 'zona histórica', 'área moderna', 'región cultural'][i % 4]}",
                        "best_time_to_visit": ["Primavera", "Otoño", "Verano", "Todo el año"][i % 4]
                    }
                    for i in range(limit)
                ],
                "search_analytics": {
                    "total_results": limit,
                    "avg_rating": 4.3,
                    "top_types": ["ciudad", "monumento", "museo"],
                    "popular_categories": ["Turismo", "Cultura"]
                }
            }
            
            logger.info(f"Location search completed for query: {query}")
            return locations_data
            
        except Exception as e:
            logger.error(f"Error in search_locations: {str(e)}")
            return {"error": f"Error searching locations: {str(e)}"}
    
    async def nearby_search(
        self,
        latitude: float,
        longitude: float,
        radius: int = 5,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Buscar lugares cercanos en TripAdvisor"""
        try:
            # Simulación de búsqueda de lugares cercanos
            nearby_data = {
                "search_center": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "radius": f"{radius} km"
                },
                "places": [
                    {
                        "id": f"place_{i}",
                        "name": f"Lugar Cercano {i}",
                        "category": category or ["restaurante", "hotel", "atracción", "tienda"][i % 4],
                        "distance": f"{i * 0.5 + 0.2:.1f} km",
                        "address": f"Calle Cercana {i}",
                        "rating": 4.1 + i * 0.15,
                        "review_count": 80 + i * 15,
                        "price_level": i % 4,
                        "cuisine_type": ["Mediterránea", "Internacional", "Local", "Fusión"][i % 4],
                        "opening_hours": {
                            "monday": "10:00-22:00",
                            "tuesday": "10:00-22:00",
                            "wednesday": "10:00-22:00",
                            "thursday": "10:00-22:00",
                            "friday": "10:00-23:00",
                            "saturday": "12:00-23:00",
                            "sunday": "12:00-21:00"
                        },
                        "special_features": ["Terraza", "WiFi gratis", "Parking", "Aire acondicionado"][i % 4] if i % 2 == 0 else None
                    }
                    for i in range(8)
                ],
                "area_info": {
                    "total_places": 8,
                    "avg_distance": "2.1 km",
                    "most_common_category": "restaurante",
                    "price_range": "€€",
                    "popular_dining_hours": "19:00-22:00"
                }
            }
            
            logger.info(f"Nearby search completed: {latitude}, {longitude}")
            return nearby_data
            
        except Exception as e:
            logger.error(f"Error in nearby_search: {str(e)}")
            return {"error": f"Error searching nearby places: {str(e)}"}
    
    async def location_details(self, location_id: str) -> Dict[str, Any]:
        """Obtener detalles específicos de una ubicación"""
        try:
            # Simulación de detalles de ubicación
            location_details = {
                "location_id": location_id,
                "basic_info": {
                    "name": "Museo Histórico Local",
                    "type": "museo",
                    "address": "Plaza de la Cultura 15, Madrid",
                    "phone": "+34 91 987 6543",
                    "website": "https://www.museohistorico.com",
                    "email": "info@museohistorico.com"
                },
                "description": {
                    "short": "Museo dedicado a la historia local con exposiciones permanentes y temporales",
                    "full": "Este museo ofrece una visión completa de la historia local desde la época romana hasta nuestros días. Cuenta con más de 10,000 piezas arqueológicas, arte sacro y objetos cotidianos de diferentes períodos históricos."
                },
                "visit_info": {
                    "opening_hours": {
                        "monday": "Cerrado",
                        "tuesday": "10:00-19:00",
                        "wednesday": "10:00-19:00",
                        "thursday": "10:00-19:00",
                        "friday": "10:00-20:00",
                        "saturday": "10:00-20:00",
                        "sunday": "10:00-14:00"
                    },
                    "admission": {
                        "adult": 12.00,
                        "student": 8.00,
                        "senior": 10.00,
                        "children_under_12": "Gratuito",
                        "groups_10+": "Descuento del 15%"
                    },
                    "guided_tours": {
                        "available": True,
                        "duration": "90 minutos",
                        "languages": ["Español", "Inglés", "Francés"],
                        "price": "5.00 adicional"
                    }
                },
                "highlights": [
                    "Exposición de mosaicos romanos",
                    "Colección de arte sacro medieval",
                    "Sala de arqueología local",
                    "Exposición temporal de fotografía histórica"
                ],
                "accessibility": {
                    "wheelchair_accessible": True,
                    "audio_guides": True,
                    "sign_language": False,
                    "large_print_brochures": True
                }
            }
            
            logger.info(f"Location details retrieved for: {location_id}")
            return location_details
            
        except Exception as e:
            logger.error(f"Error in location_details: {str(e)}")
            return {"error": f"Error getting location details: {str(e)}"}
    
    async def reviews(
        self,
        location_id: str,
        review_type: str = "all",
        limit: int = 10,
        sort_by: str = "relevance"
    ) -> Dict[str, Any]:
        """Obtener reseñas de TripAdvisor"""
        try:
            # Simulación de reseñas
            reviews_data = {
                "location_id": location_id,
                "review_type": review_type,
                "summary": {
                    "total_reviews": 1247,
                    "average_rating": 4.3,
                    "rating_distribution": {
                        "5_star": 623,
                        "4_star": 374,
                        "3_star": 125,
                        "2_star": 75,
                        "1_star": 50
                    }
                },
                "reviews": [
                    {
                        "id": f"review_{i}",
                        "user": {
                            "name": f"Usuario {i}",
                            "contributions": 15 + i * 5,
                            "helpful_votes": 20 + i * 3
                        },
                        "rating": 5 if i % 3 == 0 else 4,
                        "title": f"Experiencia {['excelente', 'muy buena', 'correcta', 'regular'][i % 4]}",
                        "text": f"Esta es una reseña detallada sobre el lugar {i}. La experiencia fue muy positiva con detalles específicos sobre el servicio, ambiente y calidad del lugar.",
                        "date": (datetime.now().timestamp() - i * 86400 * 7).isoformat(),
                        "trip_type": ["Solo", "En pareja", "En familia", "Negocios"][i % 4],
                        "travel_date": "2024-03",
                        "helpful": i % 2 == 0,
                        "photos": i % 3 == 0,
                        "language": "es"
                    }
                    for i in range(limit)
                ],
                "recent_trends": {
                    "positive_mentions": ["excelente servicio", "muy limpio", "buena ubicación"],
                    "areas_for_improvement": ["precio", "tiempo de espera", "ruido"],
                    "trending_keywords": ["recomendado", "volveremos", "calidad", "experiencia"]
                }
            }
            
            logger.info(f"Reviews retrieved for location: {location_id}")
            return reviews_data
            
        except Exception as e:
            logger.error(f"Error in reviews: {str(e)}")
            return {"error": f"Error getting reviews: {str(e)}"}
    
    async def photos(
        self,
        location_id: str,
        photo_type: str = "all",
        limit: int = 15
    ) -> Dict[str, Any]:
        """Obtener fotos de TripAdvisor"""
        try:
            # Simulación de fotos
            photos_data = {
                "location_id": location_id,
                "photo_type": photo_type,
                "total_photos": 156,
                "photos": [
                    {
                        "id": f"photo_{i}",
                        "url": f"https://images.tripadvisor.com/photo_{i}.jpg",
                        "thumbnail_url": f"https://images.tripadvisor.com/thumb_{i}.jpg",
                        "caption": f"Vista panorámica del lugar #{i}",
                        "upload_date": (datetime.now().timestamp() - i * 86400 * 30).isoformat(),
                        "photographer": {
                            "username": f"fotografo_{i}",
                            "contributions": 45 + i * 10
                        },
                        "dimensions": {
                            "width": 1024,
                            "height": 768
                        },
                        "photo_type": ["interior", "exterior", "comida", "ambiente", "detalle"][i % 5],
                        "helpful_votes": i * 2,
                        "is_official": i % 5 == 0
                    }
                    for i in range(limit)
                ],
                "categories": {
                    "exterior": 35,
                    "interior": 28,
                    "comida": 22,
                    "ambiente": 10,
                    "detalles": 5
                },
                "top_photographers": [f"fotografo_{i}" for i in range(3)]
            }
            
            logger.info(f"Photos retrieved for location: {location_id}")
            return photos_data
            
        except Exception as e:
            logger.error(f"Error in photos: {str(e)}")
            return {"error": f"Error getting photos: {str(e)}"}

# =============================================================================
# HERRAMIENTAS MCP - SOCIAL MEDIA
# =============================================================================

# Agente de redes sociales
social_agent = SocialMediaIntelligenceAgent()

@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """Lista todas las herramientas disponibles organizadas por categoría"""
    tools = [
        # Twitter Tools
        Tool(
            name="twitter_search_tweets",
            description="Buscar tweets en Twitter con análisis de engagement y métricas",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Términos de búsqueda para los tweets"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Número de tweets a retornar (default: 10)",
                        "default": 10
                    },
                    "result_type": {
                        "type": "string",
                        "description": "Tipo de resultados: recent, popular, mixed (default: recent)",
                        "default": "recent"
                    },
                    "lang": {
                        "type": "string",
                        "description": "Idioma de los tweets (default: es)",
                        "default": "es"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="twitter_get_user_info",
            description="Obtener información detallada de usuario de Twitter con analytics",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Nombre de usuario de Twitter (sin @)"
                    }
                },
                "required": ["username"]
            }
        ),
        Tool(
            name="twitter_get_user_tweets",
            description="Obtener tweets recientes de un usuario específico con métricas",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Nombre de usuario de Twitter (sin @)"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Número de tweets a retornar (default: 20)",
                        "default": 20
                    },
                    "exclude_replies": {
                        "type": "boolean",
                        "description": "Excluir respuestas (default: True)",
                        "default": True
                    }
                },
                "required": ["username"]
            }
        ),
        
        # Pinterest Tools
        Tool(
            name="pinterest_search_pins",
            description="Buscar pins en Pinterest con análisis de engagement",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Términos de búsqueda para los pins"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Número de pins a retornar (default: 25)",
                        "default": 25
                    },
                    "board": {
                        "type": "string",
                        "description": "Filtro por board específico (opcional)",
                        "default": None
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="pinterest_get_user_info",
            description="Obtener información completa de usuario de Pinterest con estadísticas",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Nombre de usuario de Pinterest"
                    }
                },
                "required": ["username"]
            }
        ),
        
        # Booking.com Travel Tools
        Tool(
            name="flights_search",
            description="Buscar vuelos en Booking.com con múltiples opciones y filtros",
            inputSchema={
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "Ciudad o aeropuerto de origen (código IATA)"
                    },
                    "destination": {
                        "type": "string",
                        "description": "Ciudad o aeropuerto de destino (código IATA)"
                    },
                    "departure_date": {
                        "type": "string",
                        "description": "Fecha de salida (YYYY-MM-DD)"
                    },
                    "return_date": {
                        "type": "string",
                        "description": "Fecha de vuelta (YYYY-MM-DD, opcional)",
                        "default": None
                    },
                    "adults": {
                        "type": "integer",
                        "description": "Número de adultos (default: 1)",
                        "default": 1
                    },
                    "travel_class": {
                        "type": "string",
                        "description": "Clase de viaje: economy, business, first (default: economy)",
                        "default": "economy"
                    }
                },
                "required": ["origin", "destination", "departure_date"]
            }
        ),
        Tool(
            name="hotels_search",
            description="Buscar hoteles en Booking.com con precios y amenities",
            inputSchema={
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": "Ciudad de destino"
                    },
                    "checkin_date": {
                        "type": "string",
                        "description": "Fecha de entrada (YYYY-MM-DD)"
                    },
                    "checkout_date": {
                        "type": "string",
                        "description": "Fecha de salida (YYYY-MM-DD)"
                    },
                    "guests": {
                        "type": "integer",
                        "description": "Número de huéspedes (default: 2)",
                        "default": 2
                    },
                    "rooms": {
                        "type": "integer",
                        "description": "Número de habitaciones (default: 1)",
                        "default": 1
                    },
                    "budget_range": {
                        "type": "string",
                        "description": "Rango de presupuesto (ej: '50-150')",
                        "default": None
                    }
                },
                "required": ["destination", "checkin_date", "checkout_date"]
            }
        ),
        Tool(
            name="hotel_details",
            description="Obtener detalles completos de un hotel específico",
            inputSchema={
                "type": "object",
                "properties": {
                    "hotel_id": {
                        "type": "string",
                        "description": "ID del hotel en Booking.com"
                    }
                },
                "required": ["hotel_id"]
            }
        ),
        
        # TripAdvisor Travel Tools
        Tool(
            name="search_locations",
            description="Buscar ubicaciones en TripAdvisor por tipo y categoría",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Términos de búsqueda para la ubicación"
                    },
                    "location_type": {
                        "type": "string",
                        "description": "Tipo de ubicación: all, city, attraction, restaurant (default: all)",
                        "default": "all"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Número máximo de resultados (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="nearby_search",
            description="Buscar lugares cercanos usando coordenadas GPS",
            inputSchema={
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Latitud decimal"
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitud decimal"
                    },
                    "radius": {
                        "type": "integer",
                        "description": "Radio de búsqueda en km (default: 5)",
                        "default": 5
                    },
                    "category": {
                        "type": "string",
                        "description": "Categoría específica (opcional)",
                        "default": None
                    }
                },
                "required": ["latitude", "longitude"]
            }
        ),
        Tool(
            name="location_details",
            description="Obtener información detallada de una ubicación específica",
            inputSchema={
                "type": "object",
                "properties": {
                    "location_id": {
                        "type": "string",
                        "description": "ID de la ubicación en TripAdvisor"
                    }
                },
                "required": ["location_id"]
            }
        ),
        Tool(
            name="reviews",
            description="Obtener reseñas de TripAdvisor con análisis de sentimientos",
            inputSchema={
                "type": "object",
                "properties": {
                    "location_id": {
                        "type": "string",
                        "description": "ID de la ubicación en TripAdvisor"
                    },
                    "review_type": {
                        "type": "string",
                        "description": "Tipo de reseñas: all, positive, negative (default: all)",
                        "default": "all"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Número de reseñas a retornar (default: 10)",
                        "default": 10
                    },
                    "sort_by": {
                        "type": "string",
                        "description": "Ordenar por: relevance, date, rating (default: relevance)",
                        "default": "relevance"
                    }
                },
                "required": ["location_id"]
            }
        ),
        Tool(
            name="photos",
            description="Obtener fotos de ubicaciones de TripAdvisor",
            inputSchema={
                "type": "object",
                "properties": {
                    "location_id": {
                        "type": "string",
                        "description": "ID de la ubicación en TripAdvisor"
                    },
                    "photo_type": {
                        "type": "string",
                        "description": "Tipo de fotos: all, interior, exterior, food (default: all)",
                        "default": "all"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Número de fotos a retornar (default: 15)",
                        "default": 15
                    }
                },
                "required": ["location_id"]
            }
        )
    ]
    
    return ListToolsResult(tools=tools)

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Manejar la ejecución de herramientas"""
    try:
        # Social Media Intelligence Tools
        if name == "twitter_search_tweets":
            result = await social_agent.twitter_search_tweets(**arguments)
        elif name == "twitter_get_user_info":
            result = await social_agent.twitter_get_user_info(**arguments)
        elif name == "twitter_get_user_tweets":
            result = await social_agent.twitter_get_user_tweets(**arguments)
        elif name == "pinterest_search_pins":
            result = await social_agent.pinterest_search_pins(**arguments)
        elif name == "pinterest_get_user_info":
            result = await social_agent.pinterest_get_user_info(**arguments)
        
        # Travel Planning Tools
        elif name == "flights_search":
            travel_agent = TravelPlanningAgent()
            result = await travel_agent.flights_search(**arguments)
        elif name == "hotels_search":
            travel_agent = TravelPlanningAgent()
            result = await travel_agent.hotels_search(**arguments)
        elif name == "hotel_details":
            travel_agent = TravelPlanningAgent()
            result = await travel_agent.hotel_details(**arguments)
        elif name == "search_locations":
            travel_agent = TravelPlanningAgent()
            result = await travel_agent.search_locations(**arguments)
        elif name == "nearby_search":
            travel_agent = TravelPlanningAgent()
            result = await travel_agent.nearby_search(**arguments)
        elif name == "location_details":
            travel_agent = TravelPlanningAgent()
            result = await travel_agent.location_details(**arguments)
        elif name == "reviews":
            travel_agent = TravelPlanningAgent()
            result = await travel_agent.reviews(**arguments)
        elif name == "photos":
            travel_agent = TravelPlanningAgent()
            result = await travel_agent.photos(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        return CallToolResult(
            content=[
                {
                    "type": "text",
                    "text": json.dumps(result, ensure_ascii=False, indent=2)
                }
            ]
        )
        
    except Exception as e:
        logger.error(f"Error calling tool {name}: {str(e)}")
        return CallToolResult(
            content=[
                {
                    "type": "text",
                    "text": f"Error ejecutando {name}: {str(e)}"
                }
            ],
            isError=True
        )

# =============================================================================
# ENDPOINTS MCP ORGANIZADOS POR CATEGORÍA
# =============================================================================

# Configuración de endpoints para diferentes categorías
MCP_ENDPOINTS = {
    "social": {
        "twitter": {
            "base_path": "/mcp/social/twitter",
            "tools": ["twitter_search_tweets", "twitter_get_user_info", "twitter_get_user_tweets"],
            "description": "API de Twitter para análisis de redes sociales"
        },
        "pinterest": {
            "base_path": "/mcp/social/pinterest", 
            "tools": ["pinterest_search_pins", "pinterest_get_user_info"],
            "description": "API de Pinterest para búsqueda de contenido visual"
        }
    },
    "travel": {
        "booking": {
            "base_path": "/mcp/travel/booking",
            "tools": ["flights_search", "hotels_search", "hotel_details"],
            "description": "API de Booking.com para búsqueda de vuelos y hoteles"
        },
        "tripadvisor": {
            "base_path": "/mcp/travel/tripadvisor",
            "tools": ["search_locations", "nearby_search", "location_details", "reviews", "photos"],
            "description": "API de TripAdvisor para información de destinos y reseñas"
        }
    }
}

def get_endpoint_info():
    """Obtener información de endpoints organizados por categoría"""
    return {
        "server_name": "silhouette-mcp-expanded-social-travel",
        "version": "2.0.0",
        "total_tools": 13,
        "categories": {
            "social_media_intelligence": {
                "description": "Agente de inteligencia para redes sociales",
                "total_tools": 5,
                "platforms": ["Twitter", "Pinterest"]
            },
            "travel_planning": {
                "description": "Agente de planificación de viajes",
                "total_tools": 8,
                "platforms": ["Booking.com", "TripAdvisor"]
            }
        },
        "endpoints": MCP_ENDPOINTS,
        "documentation": {
            "social_twitter": "Búsqueda y análisis de tweets, información de usuarios",
            "social_pinterest": "Búsqueda de pins y análisis de usuarios",
            "travel_booking": "Búsqueda de vuelos y hoteles con precios",
            "travel_tripadvisor": "Ubicaciones, reseñas y fotos de destinos"
        }
    }

# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Función principal del servidor MCP"""
    try:
        # Mostrar información de endpoints
        endpoint_info = get_endpoint_info()
        logger.info("=== SILHOUETTE MCP EXPANDED - REDES SOCIALES Y VIAJES ===")
        logger.info(f"Servidor: {endpoint_info['server_name']}")
        logger.info(f"Versión: {endpoint_info['version']}")
        logger.info(f"Total de herramientas: {endpoint_info['total_tools']}")
        
        logger.info("\n📱 SOCIAL MEDIA INTELLIGENCE:")
        logger.info(f"  - {endpoint_info['categories']['social_media_intelligence']['total_tools']} herramientas")
        logger.info(f"  - Plataformas: {', '.join(endpoint_info['categories']['social_media_intelligence']['platforms'])}")
        
        logger.info("\n✈️ TRAVEL PLANNING:")
        logger.info(f"  - {endpoint_info['categories']['travel_planning']['total_tools']} herramientas")
        logger.info(f"  - Plataformas: {', '.join(endpoint_info['categories']['travel_planning']['platforms'])}")
        
        logger.info("\n🌐 ENDPOINTS MCP ORGANIZADOS:")
        for category, platforms in endpoint_info['endpoints'].items():
            logger.info(f"\n  📂 {category.upper()}:")
            for platform, info in platforms.items():
                logger.info(f"    🔗 {info['base_path']}/*")
                logger.info(f"       Herramientas: {len(info['tools'])}")
                logger.info(f"       Descripción: {info['description']}")
        
        # Iniciar el servidor MCP
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="silhouette-mcp-expanded-social-travel",
                    server_version="2.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )
            
    except KeyboardInterrupt:
        logger.info("🛑 Servidor detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error en el servidor: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Servidor MCP finalizado correctamente")
    except Exception as e:
        logger.error(f"❌ Error crítico: {str(e)}")
        exit(1)