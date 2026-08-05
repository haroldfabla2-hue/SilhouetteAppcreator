#!/usr/bin/env python3
"""
SilhouetteMCP Server - Servidor FINAL Unificado
Desarrollado para: silhouettemcp.albertofarah.com
Versión: 4.0.0 - UNIFIED EDITION

Este servidor incluye TODAS las 6 categorías de agentes:
1. Maps Intelligence Agent (6 herramientas Google Maps)
2. Financial Intelligence Agent (9 herramientas)
3. Social Media + Travel Planning Agent (13 herramientas)
4. Content Creation Agent (8 herramientas)
5. Database Operations Agent (13 herramientas Supabase)
6. Research Intelligence Agent (2 herramientas)

TOTAL: 51 herramientas en un solo servidor unificado
Puerto: 8001
"""

import json
import hashlib
import secrets
import asyncio
import random
import logging
import threading
import time
import base64
import re
import csv
import io
import xml.etree.ElementTree as ET
import os
import uuid
import aiofiles
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum
import queue
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, Request, Depends, status, File, UploadFile, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, EmailStr, Field, validator
import uvicorn

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SilhouetteMCP-Unified")

# ==================== CONFIGURACIÓN DE AUTENTICACIÓN ====================
ADMIN_CREDENTIALS = {
    "email": os.getenv("ADMIN_EMAIL", "alberto.farahb@hotmail.com"),
    "password_hash": os.getenv("ADMIN_PASSWORD_HASH", hashlib.sha256("Fbalberto1910".encode()).hexdigest())
}

# Configuración de Supabase
SUPABASE_CONFIG = {
    "project_url": os.getenv("SUPABASE_URL", "https://your-project.supabase.co"),
    "service_role_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
    "anon_key": os.getenv("SUPABASE_ANON_KEY", ""),
    "project_id": os.getenv("SUPABASE_PROJECT_ID", "")
}

# Configuración del servidor unificado
app = FastAPI(
    title="SilhouetteMCP Server - FINAL UNIFIED",
    description="Servidor MCP unificado con TODOS los agentes y 51 herramientas",
    version="4.0.0-unified",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configurado para producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "Cache-Control", "X-Admin-Key"],
)

# Sistema de autenticación
security = HTTPBearer()

# ==================== ENUMS Y CLASES BASE ====================

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ContentType(Enum):
    TEXT = "text"
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    IMAGE = "image"

# ==================== MODELOS PYDANTIC ====================

class TaskRequest(BaseModel):
    agent_type: str
    tool_name: str
    parameters: Dict[str, Any]
    user_id: Optional[str] = None
    priority: int = 5
    callback_url: Optional[str] = None

class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class ToolInfo(BaseModel):
    name: str
    description: str
    category: str
    parameters: Dict[str, Any]
    example_usage: str

class AgentInfo(BaseModel):
    name: str
    description: str
    tools: List[ToolInfo]
    version: str = "1.0.0"

# ==================== STORE DE DATOS EN MEMORIA ====================

class InMemoryStore:
    def __init__(self):
        self.tasks: Dict[str, TaskResponse] = {}
        self.users: Dict[str, Dict] = {}
        self.cache: Dict[str, Any] = {}
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cache_hits": 0,
            "uptime_start": datetime.now()
        }
    
    def get_or_create_task(self, task_id: str) -> TaskResponse:
        if task_id not in self.tasks:
            self.tasks[task_id] = TaskResponse(
                task_id=task_id,
                status=TaskStatus.PENDING,
                created_at=datetime.now()
            )
        return self.tasks[task_id]
    
    def update_task(self, task_id: str, **kwargs):
        if task_id in self.tasks:
            for key, value in kwargs.items():
                setattr(self.tasks[task_id], key, value)

store = InMemoryStore()

# ==================== AGENTES Y HERRAMIENTAS ====================

# 1. MAPS INTELLIGENCE AGENT (6 herramientas)
maps_agent_tools = [
    ToolInfo(
        name="geocode",
        description="Convierte una dirección en coordenadas geográficas",
        category="maps",
        parameters={
            "address": {"type": "string", "required": True, "description": "Dirección a geocodificar"}
        },
        example_usage='{"address": "Madrid, España"}'
    ),
    ToolInfo(
        name="reverse_geocode",
        description="Convierte coordenadas en dirección",
        category="maps",
        parameters={
            "latitude": {"type": "float", "required": True},
            "longitude": {"type": "float", "required": True}
        },
        example_usage='{"latitude": 40.4168, "longitude": -3.7038}'
    ),
    ToolInfo(
        name="search_places",
        description="Busca lugares cercanos usando Google Places",
        category="maps",
        parameters={
            "query": {"type": "string", "required": True},
            "location": {"type": "object", "required": False},
            "radius": {"type": "int", "required": False, "default": 1000}
        },
        example_usage='{"query": "restaurantes en Madrid", "radius": 5000}'
    ),
    ToolInfo(
        name="place_details",
        description="Obtiene detalles de un lugar específico",
        category="maps",
        parameters={
            "place_id": {"type": "string", "required": True}
        },
        example_usage='{"place_id": "ChIJn8i6H64cS4gRG1XMGd_mJ8o"}'
    ),
    ToolInfo(
        name="distance_matrix",
        description="Calcula distancia y tiempo de viaje",
        category="maps",
        parameters={
            "origins": {"type": "list", "required": True},
            "destinations": {"type": "list", "required": True},
            "mode": {"type": "string", "required": False, "default": "driving"}
        },
        example_usage='{"origins": ["Madrid"], "destinations": ["Barcelona"], "mode": "driving"}'
    ),
    ToolInfo(
        name="directions",
        description="Obtiene direcciones entre dos puntos",
        category="maps",
        parameters={
            "origin": {"type": "string", "required": True},
            "destination": {"type": "string", "required": True},
            "mode": {"type": "string", "required": False, "default": "driving"}
        },
        example_usage='{"origin": "Madrid", "destination": "Barcelona", "mode": "driving"}'
    )
]

maps_agent = AgentInfo(
    name="Maps Intelligence Agent",
    description="Agente especializado en servicios de geolocalización y mapas",
    tools=maps_agent_tools
)

# 2. FINANCIAL INTELLIGENCE AGENT (9 herramientas)
financial_agent_tools = [
    ToolInfo(
        name="stock_price",
        description="Obtiene el precio actual de una acción",
        category="finance",
        parameters={
            "symbol": {"type": "string", "required": True}
        },
        example_usage='{"symbol": "AAPL"}'
    ),
    ToolInfo(
        name="crypto_price",
        description="Obtiene el precio de criptomonedas",
        category="finance",
        parameters={
            "symbol": {"type": "string", "required": True}
        },
        example_usage='{"symbol": "BTC"}'
    ),
    ToolInfo(
        name="forex_rate",
        description="Obtiene tipo de cambio de divisas",
        category="finance",
        parameters={
            "from_currency": {"type": "string", "required": True},
            "to_currency": {"type": "string", "required": True}
        },
        example_usage='{"from_currency": "USD", "to_currency": "EUR"}'
    ),
    ToolInfo(
        name="market_news",
        description="Obtiene noticias del mercado financiero",
        category="finance",
        parameters={
            "query": {"type": "string", "required": False},
            "limit": {"type": "int", "required": False, "default": 10}
        },
        example_usage='{"query": "stock market", "limit": 20}'
    ),
    ToolInfo(
        name="company_info",
        description="Obtiene información de una empresa",
        category="finance",
        parameters={
            "symbol": {"type": "string", "required": True}
        },
        example_usage='{"symbol": "AAPL"}'
    ),
    ToolInfo(
        name="technical_analysis",
        description="Realiza análisis técnico de valores",
        category="finance",
        parameters={
            "symbol": {"type": "string", "required": True},
            "indicators": {"type": "list", "required": False}
        },
        example_usage='{"symbol": "AAPL", "indicators": ["RSI", "MACD"]}'
    ),
    ToolInfo(
        name="economic_indicators",
        description="Obtiene indicadores económicos",
        category="finance",
        parameters={
            "indicator": {"type": "string", "required": True},
            "country": {"type": "string", "required": False}
        },
        example_usage='{"indicator": "GDP", "country": "US"}'
    ),
    ToolInfo(
        name="portfolio_analytics",
        description="Analiza la composición de un portafolio",
        category="finance",
        parameters={
            "holdings": {"type": "list", "required": True},
            "benchmark": {"type": "string", "required": False}
        },
        example_usage='{"holdings": [{"symbol": "AAPL", "weight": 0.5}], "benchmark": "SPY"}'
    ),
    ToolInfo(
        name="financial_calendar",
        description="Obtiene eventos del calendario financiero",
        category="finance",
        parameters={
            "date": {"type": "string", "required": False},
            "events": {"type": "list", "required": False}
        },
        example_usage='{"date": "2024-03-15", "events": ["earnings", "dividends"]}'
    )
]

financial_agent = AgentInfo(
    name="Financial Intelligence Agent",
    description="Agente especializado en análisis financiero y mercados",
    tools=financial_agent_tools
)

# 3. SOCIAL MEDIA + TRAVEL PLANNING AGENT (13 herramientas)
social_travel_agent_tools = [
    ToolInfo(
        name="social_media_analytics",
        description="Analiza métricas de redes sociales",
        category="social_travel",
        parameters={
            "platform": {"type": "string", "required": True},
            "account": {"type": "string", "required": True}
        },
        example_usage='{"platform": "twitter", "account": "@example"}'
    ),
    ToolInfo(
        name="content_sentiment",
        description="Analiza el sentimiento de contenido social",
        category="social_travel",
        parameters={
            "text": {"type": "string", "required": True},
            "language": {"type": "string", "required": False, "default": "es"}
        },
        example_usage='{"text": "Me encanta este producto", "language": "es"}'
    ),
    ToolInfo(
        name="trending_hashtags",
        description="Obtiene hashtags trending",
        category="social_travel",
        parameters={
            "platform": {"type": "string", "required": True},
            "location": {"type": "string", "required": False}
        },
        example_usage='{"platform": "twitter", "location": "ES"}'
    ),
    ToolInfo(
        name="influencer_insights",
        description="Analiza perfiles de influencers",
        category="social_travel",
        parameters={
            "username": {"type": "string", "required": True},
            "platform": {"type": "string", "required": True}
        },
        example_usage='{"username": "@influencer", "platform": "instagram"}'
    ),
    ToolInfo(
        name="social_monitoring",
        description="Monitorea menciones de marca",
        category="social_travel",
        parameters={
            "brand": {"type": "string", "required": True},
            "keywords": {"type": "list", "required": False}
        },
        example_usage='{"brand": "miempresa", "keywords": ["producto", "servicio"]}'
    ),
    ToolInfo(
        name="content_calendar",
        description="Genera calendario de contenido",
        category="social_travel",
        parameters={
            "themes": {"type": "list", "required": True},
            "platforms": {"type": "list", "required": True},
            "start_date": {"type": "string", "required": True}
        },
        example_usage='{"themes": ["producto"], "platforms": ["instagram"], "start_date": "2024-03-01"}'
    ),
    ToolInfo(
        name="travel_destination_search",
        description="Busca destinos de viaje",
        category="social_travel",
        parameters={
            "location": {"type": "string", "required": True},
            "preferences": {"type": "list", "required": False}
        },
        example_usage='{"location": "España", "preferences": ["playa", "cultura"]}'
    ),
    ToolInfo(
        name="flight_search",
        description="Busca vuelos",
        category="social_travel",
        parameters={
            "origin": {"type": "string", "required": True},
            "destination": {"type": "string", "required": True},
            "departure_date": {"type": "string", "required": True},
            "return_date": {"type": "string", "required": False}
        },
        example_usage='{"origin": "MAD", "destination": "BCN", "departure_date": "2024-05-01"}'
    ),
    ToolInfo(
        name="hotel_search",
        description="Busca hoteles",
        category="social_travel",
        parameters={
            "destination": {"type": "string", "required": True},
            "checkin": {"type": "string", "required": True},
            "checkout": {"type": "string", "required": True},
            "guests": {"type": "int", "required": False, "default": 2}
        },
        example_usage='{"destination": "Madrid", "checkin": "2024-05-01", "checkout": "2024-05-05"}'
    ),
    ToolInfo(
        name="activity_recommendations",
        description="Recomienda actividades",
        category="social_travel",
        parameters={
            "location": {"type": "string", "required": True},
            "category": {"type": "string", "required": False},
            "budget": {"type": "string", "required": False}
        },
        example_usage='{"location": "Madrid", "category": "cultura", "budget": "medio"}'
    ),
    ToolInfo(
        name="travel_itinerary",
        description="Genera itinerario de viaje",
        category="social_travel",
        parameters={
            "destination": {"type": "string", "required": True},
            "duration": {"type": "int", "required": True},
            "interests": {"type": "list", "required": False}
        },
        example_usage='{"destination": "Madrid", "duration": 3, "interests": ["museos", "gastronomía"]}'
    ),
    ToolInfo(
        name="weather_forecast",
        description="Obtiene pronóstico del tiempo",
        category="social_travel",
        parameters={
            "location": {"type": "string", "required": True},
            "date": {"type": "string", "required": False}
        },
        example_usage='{"location": "Madrid", "date": "2024-05-01"}'
    ),
    ToolInfo(
        name="travel_cost_estimator",
        description="Estima costo de viaje",
        category="social_travel",
        parameters={
            "destination": {"type": "string", "required": True},
            "duration": {"type": "int", "required": True},
            "travelers": {"type": "int", "required": False, "default": 2},
            "luxury_level": {"type": "string", "required": False, "default": "medium"}
        },
        example_usage='{"destination": "Barcelona", "duration": 4, "travelers": 2, "luxury_level": "medium"}'
    )
]

social_travel_agent = AgentInfo(
    name="Social Media + Travel Planning Agent",
    description="Agente especializado en redes sociales y planificación de viajes",
    tools=social_travel_agent_tools
)

# 4. CONTENT CREATION AGENT (8 herramientas)
content_agent_tools = [
    ToolInfo(
        name="text_generation",
        description="Genera texto usando IA",
        category="content",
        parameters={
            "prompt": {"type": "string", "required": True},
            "max_tokens": {"type": "int", "required": False, "default": 1000},
            "temperature": {"type": "float", "required": False, "default": 0.7}
        },
        example_usage='{"prompt": "Escribe un artículo sobre...", "max_tokens": 500}'
    ),
    ToolInfo(
        name="image_generation",
        description="Genera imágenes usando IA",
        category="content",
        parameters={
            "prompt": {"type": "string", "required": True},
            "style": {"type": "string", "required": False},
            "size": {"type": "string", "required": False, "default": "1024x1024"}
        },
        example_usage='{"prompt": "Un paisaje montañoso al atardecer", "style": "realista"}'
    ),
    ToolInfo(
        name="document_summarization",
        description="Resume documentos largos",
        category="content",
        parameters={
            "content": {"type": "string", "required": True},
            "max_length": {"type": "int", "required": False, "default": 200},
            "language": {"type": "string", "required": False, "default": "es"}
        },
        example_usage='{"content": "texto largo...", "max_length": 150}'
    ),
    ToolInfo(
        name="translation",
        description="Traduce texto entre idiomas",
        category="content",
        parameters={
            "text": {"type": "string", "required": True},
            "source_language": {"type": "string", "required": False},
            "target_language": {"type": "string", "required": True}
        },
        example_usage='{"text": "Hello world", "target_language": "es"}'
    ),
    ToolInfo(
        name="seo_optimization",
        description="Optimiza contenido para SEO",
        category="content",
        parameters={
            "content": {"type": "string", "required": True},
            "target_keywords": {"type": "list", "required": True},
            "meta_description": {"type": "string", "required": False}
        },
        example_usage='{"content": "texto...", "target_keywords": ["keyword1", "keyword2"]}'
    ),
    ToolInfo(
        name="tone_analysis",
        description="Analiza el tono del contenido",
        category="content",
        parameters={
            "text": {"type": "string", "required": True},
            "analysis_type": {"type": "string", "required": False, "default": "general"}
        },
        example_usage='{"text": "Me encanta este producto", "analysis_type": "sentiment"}'
    ),
    ToolInfo(
        name="content_calendar",
        description="Genera calendario editorial",
        category="content",
        parameters={
            "topics": {"type": "list", "required": True},
            "platforms": {"type": "list", "required": True},
            "start_date": {"type": "string", "required": True},
            "frequency": {"type": "string", "required": False, "default": "daily"}
        },
        example_usage='{"topics": ["tecnología"], "platforms": ["blog"], "start_date": "2024-03-01"}'
    ),
    ToolInfo(
        name="brand_voice_analysis",
        description="Analiza la voz de marca",
        category="content",
        parameters={
            "text_samples": {"type": "list", "required": True},
            "brand_attributes": {"type": "list", "required": False}
        },
        example_usage='{"text_samples": ["texto1", "texto2"], "brand_attributes": ["profesional", "amigable"]}'
    )
]

content_agent = AgentInfo(
    name="Content Creation Agent",
    description="Agente especializado en creación y optimización de contenido",
    tools=content_agent_tools
)

# 5. DATABASE OPERATIONS AGENT (13 herramientas Supabase)
database_agent_tools = [
    ToolInfo(
        name="supabase_query",
        description="Ejecuta consulta en Supabase",
        category="database",
        parameters={
            "table": {"type": "string", "required": True},
            "operation": {"type": "string", "required": True},
            "conditions": {"type": "dict", "required": False},
            "data": {"type": "dict", "required": False}
        },
        example_usage='{"table": "users", "operation": "select", "conditions": {"id": 1}}'
    ),
    ToolInfo(
        name="supabase_insert",
        description="Inserta datos en Supabase",
        category="database",
        parameters={
            "table": {"type": "string", "required": True},
            "data": {"type": "dict", "required": True}
        },
        example_usage='{"table": "users", "data": {"name": "Juan", "email": "juan@example.com"}}'
    ),
    ToolInfo(
        name="supabase_update",
        description="Actualiza datos en Supabase",
        category="database",
        parameters={
            "table": {"type": "string", "required": True},
            "data": {"type": "dict", "required": True},
            "conditions": {"type": "dict", "required": True}
        },
        example_usage='{"table": "users", "data": {"name": "Juan"}, "conditions": {"id": 1}}'
    ),
    ToolInfo(
        name="supabase_delete",
        description="Elimina datos de Supabase",
        category="database",
        parameters={
            "table": {"type": "string", "required": True},
            "conditions": {"type": "dict", "required": True}
        },
        example_usage='{"table": "users", "conditions": {"id": 1}}'
    ),
    ToolInfo(
        name="supabase_create_table",
        description="Crea nueva tabla en Supabase",
        category="database",
        parameters={
            "table_name": {"type": "string", "required": True},
            "columns": {"type": "dict", "required": True}
        },
        example_usage='{"table_name": "products", "columns": {"id": "SERIAL PRIMARY KEY", "name": "VARCHAR(255)"}}'
    ),
    ToolInfo(
        name="supabase_schema_migration",
        description="Ejecuta migración de esquema",
        category="database",
        parameters={
            "migration_name": {"type": "string", "required": True},
            "sql": {"type": "string", "required": True}
        },
        example_usage='{"migration_name": "add_column", "sql": "ALTER TABLE users ADD COLUMN age INTEGER;"}'
    ),
    ToolInfo(
        name="supabase_backup",
        description="Crea backup de la base de datos",
        category="database",
        parameters={
            "backup_name": {"type": "string", "required": True},
            "tables": {"type": "list", "required": False}
        },
        example_usage='{"backup_name": "backup_2024_03_15", "tables": ["users", "products"]}'
    ),
    ToolInfo(
        name="supabase_restore",
        description="Restaura desde backup",
        category="database",
        parameters={
            "backup_name": {"type": "string", "required": True}
        },
        example_usage='{"backup_name": "backup_2024_03_15"}'
    ),
    ToolInfo(
        name="supabase_user_management",
        description="Gestiona usuarios de Supabase",
        category="database",
        parameters={
            "operation": {"type": "string", "required": True},
            "user_data": {"type": "dict", "required": True}
        },
        example_usage='{"operation": "create", "user_data": {"email": "user@example.com"}}'
    ),
    ToolInfo(
        name="supabase_realtime_subscription",
        description="Configura suscripción realtime",
        category="database",
        parameters={
            "table": {"type": "string", "required": True},
            "channel": {"type": "string", "required": True}
        },
        example_usage='{"table": "users", "channel": "users_changes"}'
    ),
    ToolInfo(
        name="supabase_storage_upload",
        description="Sube archivo a Supabase Storage",
        category="database",
        parameters={
            "bucket": {"type": "string", "required": True},
            "file_path": {"type": "string", "required": True},
            "content": {"type": "string", "required": True}
        },
        example_usage='{"bucket": "avatars", "file_path": "user1.jpg", "content": "base64content"}'
    ),
    ToolInfo(
        name="supabase_storage_download",
        description="Descarga archivo de Supabase Storage",
        category="database",
        parameters={
            "bucket": {"type": "string", "required": True},
            "file_path": {"type": "string", "required": True}
        },
        example_usage='{"bucket": "avatars", "file_path": "user1.jpg"}'
    ),
    ToolInfo(
        name="supabase_storage_delete",
        description="Elimina archivo de Supabase Storage",
        category="database",
        parameters={
            "bucket": {"type": "string", "required": True},
            "file_path": {"type": "string", "required": True}
        },
        example_usage='{"bucket": "avatars", "file_path": "user1.jpg"}'
    )
]

database_agent = AgentInfo(
    name="Database Operations Agent",
    description="Agente especializado en operaciones de base de datos Supabase",
    tools=database_agent_tools
)

# 6. RESEARCH INTELLIGENCE AGENT (2 herramientas)
research_agent_tools = [
    ToolInfo(
        name="web_search",
        description="Realiza búsqueda web avanzada",
        category="research",
        parameters={
            "query": {"type": "string", "required": True},
            "num_results": {"type": "int", "required": False, "default": 10},
            "search_type": {"type": "string", "required": False, "default": "general"}
        },
        example_usage='{"query": "inteligencia artificial tendencias 2024", "num_results": 20}'
    ),
    ToolInfo(
        name="academic_research",
        description="Búsqueda en literatura académica",
        category="research",
        parameters={
            "topic": {"type": "string", "required": True},
            "fields": {"type": "list", "required": False},
            "date_range": {"type": "dict", "required": False}
        },
        example_usage='{"topic": "machine learning", "fields": ["computer science"], "date_range": {"start": "2020", "end": "2024"}}'
    )
]

research_agent = AgentInfo(
    name="Research Intelligence Agent",
    description="Agente especializado en investigación y búsqueda de información",
    tools=research_agent_tools
)

# ==================== REGISTRO DE AGENTES ====================

AGENTS = {
    "maps": maps_agent,
    "financial": financial_agent,
    "social_travel": social_travel_agent,
    "content": content_agent,
    "database": database_agent,
    "research": research_agent
}

# ==================== FUNCIONES DE UTILIDAD ====================

def authenticate_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Autentica usando admin credentials"""
    # Aquí implementarías la lógica de autenticación real
    # Por ahora, permitimos acceso si se proporciona algún token
    return credentials.credentials

def generate_task_id():
    """Genera ID único para tareas"""
    return str(uuid.uuid4())

def simulate_processing_delay(complexity=1):
    """Simula tiempo de procesamiento"""
    base_delay = complexity * 0.5
    return min(base_delay, 3.0)  # Máximo 3 segundos

# ==================== ENDPOINTS DE LA API ====================

@app.get("/")
async def root():
    """Endpoint raíz con información del servidor"""
    return {
        "name": "SilhouetteMCP Server - FINAL UNIFIED",
        "version": "4.0.0-unified",
        "description": "Servidor MCP unificado con TODOS los agentes y 51 herramientas",
        "agents_count": len(AGENTS),
        "total_tools": sum(len(agent.tools) for agent in AGENTS.values()),
        "status": "online",
        "uptime": str(datetime.now() - store.stats["uptime_start"]),
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Endpoint de salud del sistema"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": str(datetime.now() - store.stats["uptime_start"]),
        "active_tasks": len([t for t in store.tasks.values() if t.status == TaskStatus.PROCESSING]),
        "completed_tasks": len([t for t in store.tasks.values() if t.status == TaskStatus.COMPLETED])
    }

@app.get("/agents")
async def get_agents():
    """Lista todos los agentes disponibles"""
    agents_info = []
    for agent_id, agent in AGENTS.items():
        agents_info.append({
            "id": agent_id,
            "name": agent.name,
            "description": agent.description,
            "tools_count": len(agent.tools),
            "version": agent.version
        })
    return {"agents": agents_info}

@app.get("/agents/{agent_type}")
async def get_agent_info(agent_type: str):
    """Obtiene información detallada de un agente"""
    if agent_type not in AGENTS:
        raise HTTPException(status_code=404, detail=f"Agente '{agent_type}' no encontrado")
    
    agent = AGENTS[agent_type]
    return {
        "id": agent_type,
        "name": agent.name,
        "description": agent.description,
        "tools": [tool.dict() for tool in agent.tools],
        "version": agent.version
    }

@app.get("/tools")
async def get_all_tools():
    """Lista todas las herramientas disponibles"""
    all_tools = []
    for agent_id, agent in AGENTS.items():
        for tool in agent.tools:
            all_tools.append({
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "agent": agent_id,
                "parameters": tool.parameters,
                "example_usage": tool.example_usage
            })
    return {"tools": all_tools}

@app.get("/stats")
async def get_statistics():
    """Obtiene estadísticas del sistema"""
    return {
        "system_stats": store.stats,
        "agents_info": {
            agent_id: {
                "name": agent.name,
                "tools_count": len(agent.tools)
            }
            for agent_id, agent in AGENTS.items()
        },
        "tasks_summary": {
            "total": len(store.tasks),
            "pending": len([t for t in store.tasks.values() if t.status == TaskStatus.PENDING]),
            "processing": len([t for t in store.tasks.values() if t.status == TaskStatus.PROCESSING]),
            "completed": len([t for t in store.tasks.values() if t.status == TaskStatus.COMPLETED]),
            "failed": len([t for t in store.tasks.values() if t.status == TaskStatus.FAILED])
        }
    }

# ==================== ENDPOINTS DE EJECUCIÓN DE HERRAMIENTAS ====================

@app.post("/execute/{agent_type}/{tool_name}")
async def execute_tool(
    agent_type: str,
    tool_name: str,
    request: Request,
    parameters: Dict[str, Any] = {}
):
    """Ejecuta una herramienta específica"""
    
    # Validar agente
    if agent_type not in AGENTS:
        raise HTTPException(status_code=404, detail=f"Agente '{agent_type}' no encontrado")
    
    agent = AGENTS[agent_type]
    
    # Validar herramienta
    tool = None
    for t in agent.tools:
        if t.name == tool_name:
            tool = t
            break
    
    if not tool:
        raise HTTPException(status_code=404, detail=f"Herramienta '{tool_name}' no encontrada en agente '{agent_type}'")
    
    # Generar tarea
    task_id = generate_task_id()
    
    # Simular procesamiento
    complexity = len(parameters) + (1 if agent_type == "financial" else 0)
    delay = simulate_processing_delay(complexity)
    
    # Crear respuesta simulada
    result = {
        "task_id": task_id,
        "agent": agent_type,
        "tool": tool_name,
        "parameters": parameters,
        "result": f"Resultado simulado para {tool_name}",
        "processing_time": f"{delay:.2f}s",
        "timestamp": datetime.now().isoformat()
    }
    
    # Actualizar estadísticas
    store.stats["total_requests"] += 1
    store.stats["successful_requests"] += 1
    
    return result

@app.post("/tasks")
async def create_task(task_request: TaskRequest):
    """Crea una nueva tarea"""
    task_id = generate_task_id()
    
    # Validar agente y herramienta
    if task_request.agent_type not in AGENTS:
        raise HTTPException(status_code=404, detail=f"Agente '{task_request.agent_type}' no encontrado")
    
    agent = AGENTS[task_request.agent_type]
    tool_exists = any(tool.name == task_request.tool_name for tool in agent.tools)
    
    if not tool_exists:
        raise HTTPException(status_code=404, detail=f"Herramienta '{task_request.tool_name}' no encontrada")
    
    # Crear tarea en el store
    task = store.get_or_create_task(task_id)
    task.status = TaskStatus.PROCESSING
    
    return {
        "task_id": task_id,
        "status": "processing",
        "estimated_completion": (datetime.now() + timedelta(seconds=5)).isoformat()
    }

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Obtiene el estado de una tarea"""
    if task_id not in store.tasks:
        raise HTTPException(status_code=404, detail=f"Tarea '{task_id}' no encontrada")
    
    task = store.tasks[task_id]
    return task.dict()

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Elimina una tarea"""
    if task_id not in store.tasks:
        raise HTTPException(status_code=404, detail=f"Tarea '{task_id}' no encontrada")
    
    del store.tasks[task_id]
    return {"message": f"Tarea '{task_id}' eliminada"}

# ==================== ENDPOINTS DE ARCHIVOS ====================

@app.get("/files/dashboard")
async def get_dashboard():
    """Sirve el dashboard HTML"""
    return FileResponse("/app/dashboard/silhouettemcp_dashboard_expanded.html")

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder: str = Form("uploads")
):
    """Sube un archivo"""
    try:
        # Crear directorio si no existe
        upload_dir = Path(f"/tmp/{folder}")
        upload_dir.mkdir(exist_ok=True)
        
        # Guardar archivo
        file_path = upload_dir / file.filename
        content = await file.read()
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        return {
            "message": "Archivo subido exitosamente",
            "filename": file.filename,
            "size": len(content),
            "path": str(file_path)
        }
    except Exception as e:
        logger.error(f"Error subiendo archivo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error subiendo archivo: {str(e)}")

@app.get("/files/list")
async def list_files(folder: str = "uploads"):
    """Lista archivos en un directorio"""
    try:
        upload_dir = Path(f"/tmp/{folder}")
        if not upload_dir.exists():
            return {"files": []}
        
        files = []
        for file_path in upload_dir.iterdir():
            if file_path.is_file():
                files.append({
                    "name": file_path.name,
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        
        return {"files": files, "folder": folder}
    except Exception as e:
        logger.error(f"Error listando archivos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listando archivos: {str(e)}")

# ==================== CONFIGURACIÓN DE INICIO ====================

def main():
    """Función principal para iniciar el servidor"""
    print("=" * 80)
    print("🚀 SILHOUETTEMCP SERVER - FINAL UNIFIED EDITION v4.0.0")
    print("=" * 80)
    print(f"📊 Agentes configurados: {len(AGENTS)}")
    print(f"🔧 Total herramientas: {sum(len(agent.tools) for agent in AGENTS.values())}")
    print(f"🌐 Puerto: {os.getenv('PORT', 8001)}")
    print(f"🔗 URL: http://localhost:{os.getenv('PORT', 8001)}")
    print("=" * 80)
    
    # Mostrar resumen de agentes
    print("\n📋 AGENTES DISPONIBLES:")
    for agent_id, agent in AGENTS.items():
        print(f"  • {agent.name} ({agent_id}): {len(agent.tools)} herramientas")
    
    print("\n🔧 HERRAMIENTAS POR CATEGORÍA:")
    categories = {}
    for agent in AGENTS.values():
        for tool in agent.tools:
            if tool.category not in categories:
                categories[tool.category] = 0
            categories[tool.category] += 1
    
    for category, count in categories.items():
        print(f"  • {category.title()}: {count} herramientas")
    
    print("\n" + "=" * 80)
    print("✅ Servidor listo para recibir requests")
    print("📚 Documentación: http://localhost:8001/docs")
    print("🔍 Health Check: http://localhost:8001/health")
    print("=" * 80)
    
    # Iniciar servidor
    uvicorn.run(
        "silhouettemcp_server_unified:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8001)),
        reload=False,
        workers=1
    )

if __name__ == "__main__":
    main()
