"""
Tests unitarios para Location Intelligence Agent
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch
import sys
import os

# Añadir el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.location_intelligence_agent import (
    LocationIntelligenceAgent, LocationData, PlaceData, RouteData, LocationType
)


class TestLocationIntelligenceAgent:
    """Tests para LocationIntelligenceAgent"""
    
    @pytest.fixture
    async def agent(self):
        """Fixture para crear agente de prueba"""
        agent = LocationIntelligenceAgent()
        await agent._initialize()
        return agent
    
    def test_agent_initialization(self, agent):
        """Test inicialización del agente"""
        assert agent.agent_name == "LocationIntelligenceAgent"
        assert agent.is_ready
        assert len(agent.capabilities) > 0
    
    def test_calculate_distance(self, agent):
        """Test cálculo de distancia con fórmula Haversine"""
        # Coordenadas de Madrid y Barcelona
        distance = agent._calculate_distance(40.4168, -3.7038, 41.3851, 2.1734)
        
        # La distancia debe ser aproximadamente 504 km
        assert 500000 < distance < 510000  # En metros
    
    @pytest.mark.asyncio
    async def test_geocode_address_madrid(self, agent):
        """Test geocodificación de Madrid"""
        response = await agent.geocode_address("Madrid, España")
        
        assert response.success
        assert response.location_type == LocationType.GEOCODING
        assert response.data.latitude == 40.4168
        assert response.data.longitude == -3.7038
        assert response.data.confidence > 0.9
    
    @pytest.mark.asyncio
    async def test_geocode_address_barcelona(self, agent):
        """Test geocodificación de Barcelona"""
        response = await agent.geocode_address("Barcelona, España")
        
        assert response.success
        assert response.location_type == LocationType.GEOCODING
        assert response.data.latitude == 41.3851
        assert response.data.longitude == 2.1734
    
    @pytest.mark.asyncio
    async def test_geocode_cache_functionality(self, agent):
        """Test funcionalidad de cache en geocodificación"""
        address = "Valencia, España"
        
        # Primera llamada
        response1 = await agent.geocode_address(address)
        assert response1.success
        
        # Segunda llamada (debería usar cache)
        response2 = await agent.geocode_address(address)
        assert response2.success
        assert response2.metadata.get("cached") is True
    
    @pytest.mark.asyncio
    async def test_reverse_geocode(self, agent):
        """Test geocodificación inversa"""
        response = await agent.reverse_geocode(40.4168, -3.7038)
        
        assert response.success
        assert response.location_type == LocationType.REVERSE_GEOCODING
        assert "Madrid" in response.data.address
    
    @pytest.mark.asyncio
    async def test_search_places(self, agent):
        """Test búsqueda de lugares"""
        response = await agent.search_places("restaurantes", location=(40.4168, -3.7038))
        
        assert response.success
        assert response.location_type == LocationType.PLACE_SEARCH
        assert isinstance(response.data, list)
        assert len(response.data) > 0
        
        # Verificar estructura de lugar
        place = response.data[0]
        assert hasattr(place, 'name')
        assert hasattr(place, 'address')
        assert hasattr(place, 'latitude')
        assert hasattr(place, 'longitude')
    
    @pytest.mark.asyncio
    async def test_search_places_with_filter(self, agent):
        """Test búsqueda de lugares con filtro de tipo"""
        response = await agent.search_places(
            "hotel", 
            location=(40.4168, -3.7038),
            place_type="lodging"
        )
        
        assert response.success
        assert response.location_type == LocationType.PLACE_SEARCH
        # Los resultados deben estar filtrados por tipo
        places = response.data
        for place in places:
            assert "lodging" in place.types or "hotel" in place.types
    
    @pytest.mark.asyncio
    async def test_get_directions(self, agent):
        """Test obtención de direcciones"""
        response = await agent.get_directions("Madrid", "Barcelona")
        
        assert response.success
        assert response.location_type == LocationType.DIRECTIONS
        assert response.data.origin == "Madrid"
        assert response.data.destination == "Barcelona"
        assert response.data.distance > 0
        assert response.data.duration > 0
        assert len(response.data.steps) > 0
    
    @pytest.mark.asyncio
    async def test_get_directions_different_modes(self, agent):
        """Test direcciones con diferentes modos de transporte"""
        modes = ["driving", "walking", "transit"]
        
        for mode in modes:
            response = await agent.get_directions("Madrid", "Barcelona", travel_mode=mode)
            assert response.success
            assert response.data is not None
    
    @pytest.mark.asyncio
    async def test_calculate_distance_matrix(self, agent):
        """Test matriz de distancias"""
        origins = ["Madrid", "Barcelona"]
        destinations = ["Valencia", "Sevilla"]
        
        response = await agent.calculate_distance_matrix(origins, destinations)
        
        assert response.success
        assert response.location_type == LocationType.DISTANCE_MATRIX
        assert isinstance(response.data, list)
        assert len(response.data) == len(origins)
        
        # Verificar estructura de matriz
        for i, row in enumerate(response.data):
            assert len(row) == len(destinations)
            assert row[0]["origin"] == origins[i]
    
    @pytest.mark.asyncio
    async def test_process_request_geocode(self, agent):
        """Test procesamiento de request de geocodificación"""
        request = {
            "action": "geocode",
            "address": "Madrid, España"
        }
        
        response = await agent.process_request(request)
        
        assert response["success"]
        assert response["data"]["latitude"] == 40.4168
        assert response["data"]["longitude"] == -3.7038
    
    @pytest.mark.asyncio
    async def test_process_request_reverse_geocode(self, agent):
        """Test procesamiento de request de geocodificación inversa"""
        request = {
            "action": "reverse_geocode",
            "latitude": 40.4168,
            "longitude": -3.7038
        }
        
        response = await agent.process_request(request)
        
        assert response["success"]
        assert "Madrid" in response["data"]["address"]
    
    @pytest.mark.asyncio
    async def test_process_request_search_places(self, agent):
        """Test procesamiento de request de búsqueda de lugares"""
        request = {
            "action": "search_places",
            "query": "restaurantes",
            "location": [40.4168, -3.7038],
            "radius": 5000
        }
        
        response = await agent.process_request(request)
        
        assert response["success"]
        assert isinstance(response["data"], list)
        assert len(response["data"]) > 0
    
    @pytest.mark.asyncio
    async def test_process_request_directions(self, agent):
        """Test procesamiento de request de direcciones"""
        request = {
            "action": "directions",
            "origin": "Madrid",
            "destination": "Barcelona",
            "travel_mode": "driving"
        }
        
        response = await agent.process_request(request)
        
        assert response["success"]
        assert response["data"]["distance"] > 0
        assert response["data"]["duration"] > 0
    
    @pytest.mark.asyncio
    async def test_process_request_distance_matrix(self, agent):
        """Test procesamiento de request de matriz de distancias"""
        request = {
            "action": "distance_matrix",
            "origins": ["Madrid", "Barcelona"],
            "destinations": ["Valencia", "Sevilla"]
        }
        
        response = await agent.process_request(request)
        
        assert response["success"]
        assert isinstance(response["data"], list)
        assert len(response["data"]) == 2
        assert len(response["data"][0]) == 2
    
    @pytest.mark.asyncio
    async def test_process_request_invalid_action(self, agent):
        """Test procesamiento de request con acción inválida"""
        request = {
            "action": "invalid_action"
        }
        
        with pytest.raises(ValueError):
            await agent.process_request(request)
    
    @pytest.mark.asyncio
    async def test_process_request_missing_parameters(self, agent):
        """Test procesamiento de request con parámetros faltantes"""
        request = {
            "action": "geocode"
            # Falta "address"
        }
        
        response = await agent.process_request(request)
        
        assert not response["success"]
        assert "error" in response
    
    def test_get_stats(self, agent):
        """Test obtención de estadísticas"""
        stats = agent.get_stats()
        
        assert "agent_name" in stats
        assert "cached_locations" in stats
        assert "available_actions" in stats
        assert "geocode" in stats["available_actions"]
        assert "search_places" in stats["available_actions"]
        assert "directions" in stats["available_actions"]
        assert "distance_matrix" in stats["available_actions"]


class TestLocationData:
    """Tests para LocationData"""
    
    def test_location_data_creation(self):
        """Test creación de LocationData"""
        location = LocationData(
            address="Calle Mayor 15, Madrid",
            latitude=40.4168,
            longitude=-3.7038
        )
        
        assert location.address == "Calle Mayor 15, Madrid"
        assert location.latitude == 40.4168
        assert location.longitude == -3.7038
        assert location.confidence == 0.0
        assert location.timestamp > 0
    
    def test_location_data_post_init(self):
        """Test post-inicialización de LocationData"""
        location = LocationData(
            address="https://example.com",
            latitude=40.4168,
            longitude=-3.7038
        )
        
        # El dominio se extrae de la URL
        assert location.domain == "example.com"


class TestPlaceData:
    """Tests para PlaceData"""
    
    def test_place_data_creation(self):
        """Test creación de PlaceData"""
        place = PlaceData(
            place_id="place_123",
            name="Restaurante El Sabor",
            address="Calle Mayor 15, Madrid",
            latitude=40.4168,
            longitude=-3.7038
        )
        
        assert place.place_id == "place_123"
        assert place.name == "Restaurante El Sabor"
        assert place.latitude == 40.4168
        assert place.longitude == -3.7038
        assert place.types == []


class TestRouteData:
    """Tests para RouteData"""
    
    def test_route_data_creation(self):
        """Test creación de RouteData"""
        route = RouteData(
            origin="Madrid",
            destination="Barcelona",
            distance=500000,  # 500 km en metros
            duration=18000    # 5 horas en segundos
        )
        
        assert route.origin == "Madrid"
        assert route.destination == "Barcelona"
        assert route.distance == 500000
        assert route.duration == 18000
        assert route.steps == []


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v"])