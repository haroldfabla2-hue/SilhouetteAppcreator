"""
Location Intelligence Agent MCP - Agente de Inteligencia de Ubicación
Integra con Google Maps API para proporcionar geocodificación, búsqueda de lugares,
direcciones, cálculos de distancia y análisis geoespacial avanzado.

Autor: Location Intelligence Agent
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
import math

# Importar la estructura base del agente MCP
try:
    from .base_agent_wrapper import BaseAgentWrapper, AgentCapability
except ImportError:
    BaseAgentWrapper = object
    AgentCapability = None


class LocationType(Enum):
    """Tipos de ubicaciones disponibles"""
    GEOCODING = "geocoding"
    REVERSE_GEOCODING = "reverse_geocoding"
    PLACE_SEARCH = "place_search"
    DIRECTIONS = "directions"
    DISTANCE_MATRIX = "distance_matrix"


@dataclass
class LocationData:
    """Estructura de datos para información de ubicación"""
    address: str
    latitude: float
    longitude: float
    formatted_address: str = ""
    place_id: str = ""
    types: List[str] = field(default_factory=list)
    confidence: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class PlaceData:
    """Estructura de datos para lugares"""
    place_id: str
    name: str
    address: str
    latitude: float
    longitude: float
    rating: Optional[float] = None
    types: List[str] = field(default_factory=list)
    photos: List[str] = field(default_factory=list)
    opening_hours: Optional[Dict[str, Any]] = None
    website: Optional[str] = None
    phone_number: Optional[str] = None
    price_level: Optional[int] = None


@dataclass
class RouteData:
    """Estructura de datos para rutas"""
    origin: str
    destination: str
    distance: float  # en metros
    duration: float  # en segundos
    steps: List[Dict[str, Any]] = field(default_factory=list)
    polyline: str = ""
    traffic_info: Optional[Dict[str, Any]] = None


@dataclass
class LocationResponse:
    """Respuesta consolidada de ubicación"""
    success: bool
    data: Any
    query: str
    location_type: LocationType
    timestamp: float
    execution_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class LocationIntelligenceAgent(BaseAgentWrapper if BaseAgentWrapper else object):
    """
    Agente de Inteligencia de Ubicación que proporciona funcionalidades
    avanzadas de mapas y geolocalización.
    """
    
    def __init__(self):
        if BaseAgentWrapper:
            super().__init__(
                agent_name="LocationIntelligenceAgent",
                capabilities=[
                    AgentCapability.GEOCODING if AgentCapability else "geocoding",
                    AgentCapability.REVERSE_GEOCODING if AgentCapability else "reverse_geocoding",
                    AgentCapability.PLACE_SEARCH if AgentCapability else "place_search",
                    AgentCapability.DIRECTIONS if AgentCapability else "directions",
                    AgentCapability.DISTANCE_CALCULATION if AgentCapability else "distance_calculation",
                    AgentCapability.MAPS_API if AgentCapability else "maps_api",
                ],
                max_concurrent=5,
                timeout_seconds=30,
                retry_attempts=3
            )
        
        self.logger = logging.getLogger(__name__)
        self._locations_cache = {}
        self._places_cache = {}
        
    async def _initialize(self):
        """Inicialización específica del agente"""
        # Simular carga de APIs de mapas
        await asyncio.sleep(0.1)
        self.logger.info("Location Intelligence Agent inicializado")
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcular distancia usando fórmula de Haversine"""
        R = 6371000  # Radio de la Tierra en metros
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) * math.sin(delta_lon / 2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    async def geocode_address(self, address: str) -> LocationResponse:
        """Convertir dirección a coordenadas GPS"""
        start_time = time.time()
        
        try:
            # Verificar cache
            if address in self._locations_cache:
                location = self._locations_cache[address]
                return LocationResponse(
                    success=True,
                    data=location,
                    query=address,
                    location_type=LocationType.GEOCODING,
                    timestamp=time.time(),
                    execution_time=time.time() - start_time,
                    metadata={"cached": True}
                )
            
            # Simular geocodificación (en implementación real usar Google Maps API)
            # Por ahora simulamos con datos ficticios
            if "madrid" in address.lower():
                latitude, longitude = 40.4168, -3.7038
            elif "barcelona" in address.lower():
                latitude, longitude = 41.3851, 2.1734
            elif "valencia" in address.lower():
                latitude, longitude = 39.4699, -0.3763
            else:
                # Coordenadas por defecto (España)
                latitude, longitude = 40.4168, -3.7038
            
            location = LocationData(
                address=address,
                latitude=latitude,
                longitude=longitude,
                formatted_address=f"{address}, España",
                confidence=0.95
            )
            
            # Guardar en cache
            self._locations_cache[address] = location
            
            return LocationResponse(
                success=True,
                data=location,
                query=address,
                location_type=LocationType.GEOCODING,
                timestamp=time.time(),
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"Error en geocodificación: {str(e)}")
            return LocationResponse(
                success=False,
                data=None,
                query=address,
                location_type=LocationType.GEOCODING,
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                metadata={"error": str(e)}
            )
    
    async def reverse_geocode(self, latitude: float, longitude: float) -> LocationResponse:
        """Convertir coordenadas GPS a dirección"""
        start_time = time.time()
        
        try:
            # Verificar cache
            cache_key = f"{latitude:.6f},{longitude:.6f}"
            if cache_key in self._locations_cache:
                location = self._locations_cache[cache_key]
                return LocationResponse(
                    success=True,
                    data=location,
                    query=f"{latitude},{longitude}",
                    location_type=LocationType.REVERSE_GEOCODING,
                    timestamp=time.time(),
                    execution_time=time.time() - start_time,
                    metadata={"cached": True}
                )
            
            # Simular geocodificación inversa
            # Determinar ciudad basada en coordenadas
            if 41.3 < latitude < 41.4 and 2.1 < longitude < 2.2:
                address = "Barcelona, España"
            elif 39.4 < latitude < 39.5 and -0.4 < longitude < -0.3:
                address = "Valencia, España"
            elif 40.4 < latitude < 40.5 and -3.8 < longitude < -3.6:
                address = "Madrid, España"
            else:
                address = f"Dirección cerca de {latitude:.4f}, {longitude:.4f}"
            
            location = LocationData(
                address=address,
                latitude=latitude,
                longitude=longitude,
                formatted_address=address,
                confidence=0.90
            )
            
            # Guardar en cache
            self._locations_cache[cache_key] = location
            
            return LocationResponse(
                success=True,
                data=location,
                query=f"{latitude},{longitude}",
                location_type=LocationType.REVERSE_GEOCODING,
                timestamp=time.time(),
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"Error en geocodificación inversa: {str(e)}")
            return LocationResponse(
                success=False,
                data=None,
                query=f"{latitude},{longitude}",
                location_type=LocationType.REVERSE_GEOCODING,
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                metadata={"error": str(e)}
            )
    
    async def search_places(
        self, 
        query: str, 
        location: Optional[Tuple[float, float]] = None,
        radius: int = 5000,
        place_type: Optional[str] = None
    ) -> LocationResponse:
        """Buscar lugares cercanos"""
        start_time = time.time()
        
        try:
            # Simular búsqueda de lugares
            places = []
            
            # Lugares de ejemplo
            example_places = [
                PlaceData(
                    place_id="place_1",
                    name="Restaurante El Sabor",
                    address="Calle Mayor 15, Madrid",
                    latitude=40.4178,
                    longitude=-3.7042,
                    rating=4.5,
                    types=["restaurant", "food"]
                ),
                PlaceData(
                    place_id="place_2", 
                    name="Hotel Central",
                    address="Plaza España 1, Madrid",
                    latitude=40.4189,
                    longitude=-3.7033,
                    rating=4.2,
                    types=["lodging", "hotel"]
                ),
                PlaceData(
                    place_id="place_3",
                    name="Centro Comercial Plaza",
                    address="Calle Serrano 50, Madrid",
                    latitude=40.4162,
                    longitude=-3.7020,
                    rating=3.8,
                    types=["shopping_mall", "store"]
                )
            ]
            
            # Filtrar por tipo si se especifica
            if place_type:
                example_places = [p for p in example_places if place_type in p.types]
            
            places = example_places[:5]  # Limitar a 5 resultados
            
            return LocationResponse(
                success=True,
                data=places,
                query=query,
                location_type=LocationType.PLACE_SEARCH,
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                metadata={
                    "places_found": len(places),
                    "search_radius": radius,
                    "search_location": location
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error en búsqueda de lugares: {str(e)}")
            return LocationResponse(
                success=False,
                data=None,
                query=query,
                location_type=LocationType.PLACE_SEARCH,
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                metadata={"error": str(e)}
            )
    
    async def get_directions(
        self,
        origin: str,
        destination: str,
        travel_mode: str = "driving"
    ) -> LocationResponse:
        """Obtener direcciones entre dos puntos"""
        start_time = time.time()
        
        try:
            # Simular obtención de direcciones
            # En implementación real, usar Google Maps Directions API
            
            # Obtener coordenadas
            origin_resp = await self.geocode_address(origin)
            dest_resp = await self.geocode_address(destination)
            
            if not origin_resp.success or not dest_resp.success:
                raise Exception("No se pudieron obtener coordenadas de origen o destino")
            
            origin_coords = origin_resp.data
            dest_coords = dest_resp.data
            
            # Calcular distancia
            distance = self._calculate_distance(
                origin_coords.latitude, origin_coords.longitude,
                dest_coords.latitude, dest_coords.longitude
            )
            
            # Estimar tiempo de viaje (simulado)
            speeds = {
                "driving": 50,  # km/h promedio
                "walking": 5,   # km/h promedio
                "transit": 30   # km/h promedio en transporte público
            }
            
            speed = speeds.get(travel_mode, 50)
            duration = (distance / 1000) / speed * 3600  # Convertir a segundos
            
            # Simular pasos de ruta
            steps = [
                {
                    "instruction": f"Iniciar en {origin}",
                    "distance": 100,
                    "duration": 30
                },
                {
                    "instruction": f"Dirigirse hacia {destination}",
                    "distance": distance - 200,
                    "duration": duration - 60
                },
                {
                    "instruction": f"Llegar a {destination}",
                    "distance": 100,
                    "duration": 30
                }
            ]
            
            route = RouteData(
                origin=origin,
                destination=destination,
                distance=distance,
                duration=duration,
                steps=steps
            )
            
            return LocationResponse(
                success=True,
                data=route,
                query=f"{origin} -> {destination}",
                location_type=LocationType.DIRECTIONS,
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                metadata={
                    "travel_mode": travel_mode,
                    "distance_km": round(distance / 1000, 2),
                    "duration_minutes": round(duration / 60, 1)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error obteniendo direcciones: {str(e)}")
            return LocationResponse(
                success=False,
                data=None,
                query=f"{origin} -> {destination}",
                location_type=LocationType.DIRECTIONS,
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                metadata={"error": str(e)}
            )
    
    async def calculate_distance_matrix(
        self,
        origins: List[str],
        destinations: List[str]
    ) -> LocationResponse:
        """Calcular matriz de distancias entre múltiples ubicaciones"""
        start_time = time.time()
        
        try:
            matrix = []
            
            # Obtener coordenadas de todas las ubicaciones
            origin_coords = []
            dest_coords = []
            
            for origin in origins:
                resp = await self.geocode_address(origin)
                if resp.success:
                    origin_coords.append(resp.data)
                else:
                    origin_coords.append(None)
            
            for dest in destinations:
                resp = await self.geocode_address(dest)
                if resp.success:
                    dest_coords.append(resp.data)
                else:
                    dest_coords.append(None)
            
            # Calcular matriz de distancias
            for i, origin in enumerate(origins):
                row = []
                for j, dest in enumerate(destinations):
                    if origin_coords[i] and dest_coords[j]:
                        distance = self._calculate_distance(
                            origin_coords[i].latitude, origin_coords[i].longitude,
                            dest_coords[j].latitude, dest_coords[j].longitude
                        )
                        row.append({
                            "origin": origin,
                            "destination": dest,
                            "distance": distance,
                            "distance_km": round(distance / 1000, 2)
                        })
                    else:
                        row.append({
                            "origin": origin,
                            "destination": dest,
                            "distance": None,
                            "distance_km": None,
                            "error": "No se pudieron obtener coordenadas"
                        })
                matrix.append(row)
            
            return LocationResponse(
                success=True,
                data=matrix,
                query=f"Matrix: {origins} -> {destinations}",
                location_type=LocationType.DISTANCE_MATRIX,
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                metadata={
                    "origins_count": len(origins),
                    "destinations_count": len(destinations),
                    "matrix_size": f"{len(origins)}x{len(destinations)}"
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error calculando matriz de distancias: {str(e)}")
            return LocationResponse(
                success=False,
                data=None,
                query=f"Matrix: {origins} -> {destinations}",
                location_type=LocationType.DISTANCE_MATRIX,
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                metadata={"error": str(e)}
            )
    
    async def process_request(
        self,
        request: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Procesar request de ubicación
        
        Formatos soportados:
        - geocode: {"action": "geocode", "address": "Calle Mayor 15, Madrid"}
        - reverse_geocode: {"action": "reverse_geocode", "latitude": 40.4168, "longitude": -3.7038}
        - search_places: {"action": "search_places", "query": "restaurantes", "location": [40.4168, -3.7038]}
        - directions: {"action": "directions", "origin": "Madrid", "destination": "Barcelona"}
        - distance_matrix: {"action": "distance_matrix", "origins": ["Madrid", "Barcelona"], "destinations": ["Valencia", "Sevilla"]}
        """
        try:
            await self.ensure_initialized()
            
            action = request.get("action", "").lower()
            
            if action == "geocode":
                address = request.get("address")
                if not address:
                    raise ValueError("Dirección requerida para geocodificación")
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="geocode",
                        capability=AgentCapability.GEOCODING,
                        operation_func=self.geocode_address,
                        address=address
                    )
                else:
                    response = await self.geocode_address(address)
                
                return {
                    "success": response.success,
                    "data": response.data.__dict__ if hasattr(response.data, '__dict__') else response.data,
                    "metadata": response.metadata
                }
            
            elif action == "reverse_geocode":
                latitude = request.get("latitude")
                longitude = request.get("longitude")
                
                if latitude is None or longitude is None:
                    raise ValueError("Latitud y longitud requeridas")
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="reverse_geocode",
                        capability=AgentCapability.REVERSE_GEOCODING,
                        operation_func=self.reverse_geocode,
                        latitude=latitude,
                        longitude=longitude
                    )
                else:
                    response = await self.reverse_geocode(latitude, longitude)
                
                return {
                    "success": response.success,
                    "data": response.data.__dict__ if hasattr(response.data, '__dict__') else response.data,
                    "metadata": response.metadata
                }
            
            elif action == "search_places":
                query = request.get("query")
                location = request.get("location")
                radius = request.get("radius", 5000)
                place_type = request.get("place_type")
                
                if not query:
                    raise ValueError("Query de búsqueda requerido")
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="search_places",
                        capability=AgentCapability.PLACE_SEARCH,
                        operation_func=self.search_places,
                        query=query,
                        location=location,
                        radius=radius,
                        place_type=place_type
                    )
                else:
                    response = await self.search_places(query, location, radius, place_type)
                
                return {
                    "success": response.success,
                    "data": [p.__dict__ for p in response.data] if response.data else None,
                    "metadata": response.metadata
                }
            
            elif action == "directions":
                origin = request.get("origin")
                destination = request.get("destination")
                travel_mode = request.get("travel_mode", "driving")
                
                if not origin or not destination:
                    raise ValueError("Origen y destino requeridos")
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="directions",
                        capability=AgentCapability.DIRECTIONS,
                        operation_func=self.get_directions,
                        origin=origin,
                        destination=destination,
                        travel_mode=travel_mode
                    )
                else:
                    response = await self.get_directions(origin, destination, travel_mode)
                
                return {
                    "success": response.success,
                    "data": response.data.__dict__ if hasattr(response.data, '__dict__') else response.data,
                    "metadata": response.metadata
                }
            
            elif action == "distance_matrix":
                origins = request.get("origins", [])
                destinations = request.get("destinations", [])
                
                if not origins or not destinations:
                    raise ValueError("Orígenes y destinos requeridos")
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="distance_matrix",
                        capability=AgentCapability.DISTANCE_CALCULATION,
                        operation_func=self.calculate_distance_matrix,
                        origins=origins,
                        destinations=destinations
                    )
                else:
                    response = await self.calculate_distance_matrix(origins, destinations)
                
                return {
                    "success": response.success,
                    "data": response.data,
                    "metadata": response.metadata
                }
            
            else:
                raise ValueError(f"Acción no soportada: {action}")
                
        except Exception as e:
            self.logger.error(f"Error procesando request de ubicación: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del agente"""
        return {
            "cached_locations": len(self._locations_cache),
            "cached_places": len(self._places_cache),
            "agent_name": "LocationIntelligenceAgent",
            "available_actions": [
                "geocode",
                "reverse_geocode", 
                "search_places",
                "directions",
                "distance_matrix"
            ]
        }