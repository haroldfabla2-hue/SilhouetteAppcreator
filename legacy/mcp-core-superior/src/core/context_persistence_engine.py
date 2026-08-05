"""
Sistema Avanzado de Persistencia de Contexto para MCP Core Superior
================================================================

Implementa:
1. Incremental context snapshots con compression
2. Hierarchical context storage (short/medium/long-term)
3. Semantic context clustering y similarity
4. Automatic context optimization y pruning
5. Cross-session context recovery
6. Context version control y diff
7. Distributed context storage con Redis/PostgreSQL
8. Context-aware agent initialization
9. Context compression algorithms
10. Fast context retrieval con índices
"""

import asyncio
import json
import zlib
import hashlib
import pickle
import logging
import uuid
import time
import gzip
import lz4.frame
from typing import Dict, List, Optional, Any, Union, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
import numpy as np
import asyncpg
import redis.asyncio as redis
import threading
from concurrent.futures import ThreadPoolExecutor

from .config import settings
from .exceptions import MCPCoreException, DatabaseException
from ..services.embedding_service import EmbeddingService
from ..services.vector_store_client import VectorStoreClient


class ContextTier(str, Enum):
    """Niveles jerárquicos de almacenamiento de contexto"""
    SHORT_TERM = "short_term"      # 0-30 minutos
    MEDIUM_TERM = "medium_term"    # 30 minutos - 24 horas
    LONG_TERM = "long_term"        # 24 horas - 30 días
    ARCHIVE = "archive"           # 30+ días


class ContextType(str, Enum):
    """Tipos de contexto"""
    CONVERSATION = "conversation"
    TASK = "task"
    AGENT_MEMORY = "agent_memory"
    WORKFLOW = "workflow"
    USER_PREFERENCES = "user_preferences"
    SYSTEM_STATE = "system_state"


class CompressionType(str, Enum):
    """Algoritmos de compresión disponibles"""
    NONE = "none"
    ZLIB = "zlib"
    GZIP = "gzip"
    LZ4 = "lz4"
    PICKLE = "pickle"


@dataclass
class ContextSnapshot:
    """Snapshot incremental de contexto"""
    snapshot_id: str
    parent_id: Optional[str]
    context_type: ContextType
    tier: ContextTier
    content: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    compression_type: CompressionType = CompressionType.NONE
    compressed_size: int = 0
    original_size: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.snapshot_id:
            self.snapshot_id = str(uuid.uuid4())
        if not self.original_size:
            self.original_size = len(json.dumps(self.content, default=str))
    
    def compress(self, compression_type: CompressionType = CompressionType.LZ4) -> bytes:
        """Comprimir contenido del snapshot"""
        if compression_type == CompressionType.NONE:
            return json.dumps(self.content, default=str).encode()
        elif compression_type == CompressionType.ZLIB:
            return zlib.compress(json.dumps(self.content, default=str).encode())
        elif compression_type == CompressionType.GZIP:
            return gzip.compress(json.dumps(self.content, default=str).encode())
        elif compression_type == CompressionType.LZ4:
            return lz4.frame.compress(json.dumps(self.content, default=str).encode())
        elif compression_type == CompressionType.PICKLE:
            return pickle.dumps(self.content)
        else:
            raise ValueError(f"Tipo de compresión no soportado: {compression_type}")
    
    def decompress(self, compressed_data: bytes) -> Dict[str, Any]:
        """Descomprimir contenido del snapshot"""
        if self.compression_type == CompressionType.NONE:
            return json.loads(compressed_data.decode())
        elif self.compression_type == CompressionType.ZLIB:
            return json.loads(zlib.decompress(compressed_data).decode())
        elif self.compression_type == CompressionType.GZIP:
            return json.loads(gzip.decompress(compressed_data).decode())
        elif self.compression_type == CompressionType.LZ4:
            return json.loads(lz4.frame.decompress(compressed_data).decode())
        elif self.compression_type == CompressionType.PICKLE:
            return pickle.loads(compressed_data)
        else:
            raise ValueError(f"Tipo de compresión no soportado: {self.compression_type}")


@dataclass
class ContextCluster:
    """Cluster semántico de contexto"""
    cluster_id: str
    snapshots: Set[str] = field(default_factory=set)
    centroid_embedding: Optional[List[float]] = None
    similarity_threshold: float = 0.7
    created_at: datetime = field(default_factory=datetime.now)
    last_merged: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.cluster_id:
            self.cluster_id = str(uuid.uuid4())


@dataclass 
class ContextVersion:
    """Versión de control de contexto"""
    version_id: str
    snapshot_id: str
    parent_version: Optional[str]
    changes: Dict[str, Any]
    diff: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    author: str = "system"
    message: str = ""
    
    def __post_init__(self):
        if not self.version_id:
            self.version_id = str(uuid.uuid4())


class ContextPersistenceEngine:
    """
    Motor principal de persistencia de contexto avanzado
    """
    
    def __init__(self):
        self.logger = logging.getLogger("mcp.context_persistence")
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStoreClient()
        self._redis_client: Optional[redis.Redis] = None
        self._db_pool: Optional[asyncpg.Pool] = None
        
        # Configuraciones de almacenamiento jerárquico
        self.tier_config = {
            ContextTier.SHORT_TERM: {
                "max_size_mb": 100,
                "max_age_hours": 0.5,
                "compression": CompressionType.LZ4,
                "storage": "redis"
            },
            ContextTier.MEDIUM_TERM: {
                "max_size_mb": 500,
                "max_age_hours": 24,
                "compression": CompressionType.ZLIB,
                "storage": "postgresql"
            },
            ContextTier.LONG_TERM: {
                "max_size_mb": 5000,
                "max_age_hours": 720,
                "compression": CompressionType.GZIP,
                "storage": "postgresql"
            },
            ContextTier.ARCHIVE: {
                "max_size_mb": 50000,
                "max_age_hours": 8760,
                "compression": CompressionType.GZIP,
                "storage": "postgresql"
            }
        }
        
        # Índices para recuperación rápida
        self.indexes = {
            "by_type": defaultdict(set),
            "by_user": defaultdict(set),
            "by_tier": defaultdict(set),
            "by_timestamp": deque(maxlen=10000),
            "similarity": defaultdict(dict)
        }
        
        # Cache en memoria para acceso rápido
        self._cache = {
            "snapshots": {},
            "clusters": {},
            "versions": {}
        }
        
        # Executor para operaciones intensivas
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Estado de inicialización
        self.is_initialized = False
    
    async def initialize(self) -> None:
        """Inicializar el motor de persistencia"""
        try:
            self.logger.info("Inicializando Context Persistence Engine...")
            
            # Inicializar conexiones
            await self._initialize_redis()
            await self._initialize_postgresql()
            
            # Inicializar servicios
            await self.embedding_service.initialize()
            await self.vector_store.initialize()
            
            # Crear esquemas de base de datos
            await self._create_database_schemas()
            
            # Cargar índices existentes
            await self._load_indexes()
            
            # Iniciar tareas de mantenimiento
            asyncio.create_task(self._maintenance_loop())
            
            self.is_initialized = True
            self.logger.info("Context Persistence Engine inicializado exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando Context Persistence Engine: {e}")
            raise MCPCoreException(f"Error de inicialización: {e}")
    
    async def _initialize_redis(self) -> None:
        """Inicializar cliente Redis"""
        try:
            self._redis_client = redis.from_url(
                settings.redis_url,
                **settings.get_redis_config()
            )
            await self._redis_client.ping()
            self.logger.info("Conexión Redis establecida")
        except Exception as e:
            self.logger.error(f"Error conectando a Redis: {e}")
            raise DatabaseException("Error conectando a Redis", "connect", original_error=e)
    
    async def _initialize_postgresql(self) -> None:
        """Inicializar pool de PostgreSQL"""
        try:
            self._db_pool = await asyncpg.create_pool(
                settings.database_url,
                **settings.get_database_config()
            )
            self.logger.info("Pool PostgreSQL establecido")
        except Exception as e:
            self.logger.error(f"Error conectando a PostgreSQL: {e}")
            raise DatabaseException("Error conectando a PostgreSQL", "connect", original_error=e)
    
    async def _create_database_schemas(self) -> None:
        """Crear esquemas de base de datos necesarios"""
        try:
            async with self._db_pool.acquire() as conn:
                # Tabla de snapshots
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS context_snapshots (
                        snapshot_id UUID PRIMARY KEY,
                        parent_id UUID REFERENCES context_snapshots(snapshot_id),
                        context_type TEXT NOT NULL,
                        tier TEXT NOT NULL,
                        content BYTEA,
                        metadata JSONB DEFAULT '{}',
                        embedding VECTOR(1536),
                        compression_type TEXT DEFAULT 'none',
                        compressed_size INTEGER DEFAULT 0,
                        original_size INTEGER DEFAULT 0,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        expires_at TIMESTAMP WITH TIME ZONE,
                        access_count INTEGER DEFAULT 0,
                        last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        user_id TEXT,
                        session_id TEXT,
                        INDEX idx_context_type (context_type),
                        INDEX idx_tier (tier),
                        INDEX idx_created_at (created_at),
                        INDEX idx_user_session (user_id, session_id),
                        INDEX idx_expires_at (expires_at)
                    )
                ''')
                
                # Tabla de clusters semánticos
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS context_clusters (
                        cluster_id UUID PRIMARY KEY,
                        snapshots UUID[] DEFAULT '{}',
                        centroid_embedding VECTOR(1536),
                        similarity_threshold FLOAT DEFAULT 0.7,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        last_merged TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        metadata JSONB DEFAULT '{}'
                    )
                ''')
                
                # Tabla de versiones de control
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS context_versions (
                        version_id UUID PRIMARY KEY,
                        snapshot_id UUID REFERENCES context_snapshots(snapshot_id),
                        parent_version UUID REFERENCES context_versions(version_id),
                        changes JSONB DEFAULT '{}',
                        diff JSONB DEFAULT '{}',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        author TEXT DEFAULT 'system',
                        message TEXT DEFAULT ''
                    )
                ''')
                
                # Tabla de índices de búsqueda
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS context_search_index (
                        id SERIAL PRIMARY KEY,
                        snapshot_id UUID REFERENCES context_snapshots(snapshot_id),
                        search_vector VECTOR(1536),
                        content_text TEXT,
                        keywords TEXT[],
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                ''')
                
                # Habilitar extensión pgvector si no está habilitada
                await conn.execute('CREATE EXTENSION IF NOT EXISTS vector;')
                
            self.logger.info("Esquemas de base de datos creados")
            
        except Exception as e:
            self.logger.error(f"Error creando esquemas: {e}")
            raise DatabaseException("Error creando esquemas", "create_schema", original_error=e)
    
    async def _load_indexes(self) -> None:
        """Cargar índices existentes desde base de datos"""
        try:
            async with self._db_pool.acquire() as conn:
                # Cargar snapshots recientes
                rows = await conn.fetch('''
                    SELECT snapshot_id, context_type, tier, created_at, user_id
                    FROM context_snapshots 
                    WHERE created_at > NOW() - INTERVAL '1 day'
                    ORDER BY created_at DESC 
                    LIMIT 10000
                ''')
                
                for row in rows:
                    self.indexes["by_type"][row['context_type']].add(row['snapshot_id'])
                    self.indexes["by_tier"][row['tier']].add(row['snapshot_id'])
                    if row['user_id']:
                        self.indexes["by_user"][row['user_id']].add(row['snapshot_id'])
                    self.indexes["by_timestamp"].append((row['created_at'], row['snapshot_id']))
                
            self.logger.info(f"Índices cargados: {len(self.indexes['by_timestamp'])} snapshots")
            
        except Exception as e:
            self.logger.error(f"Error cargando índices: {e}")
    
    async def create_snapshot(
        self,
        context_type: ContextType,
        content: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Crear snapshot incremental de contexto"""
        try:
            # Determinar tier apropiado
            tier = self._determine_tier(context_type, content, metadata)
            
            # Crear snapshot
            snapshot = ContextSnapshot(
                snapshot_id=str(uuid.uuid4()),
                parent_id=parent_id,
                context_type=context_type,
                tier=tier,
                content=content,
                metadata=metadata or {},
                user_id=user_id,
                session_id=session_id
            )
            
            # Generar embedding
            snapshot.embedding = await self._generate_context_embedding(content)
            
            # Aplicar compresión
            snapshot.compression_type = self.tier_config[tier]["compression"]
            compressed_data = snapshot.compress(snapshot.compression_type)
            snapshot.compressed_size = len(compressed_data)
            
            # Almacenar según tier
            await self._store_snapshot(snapshot, compressed_data)
            
            # Actualizar índices
            await self._update_indexes(snapshot)
            
            # Cachear
            self._cache["snapshots"][snapshot.snapshot_id] = snapshot
            
            # Verificar si necesita clustering
            await self._check_clustering(snapshot)
            
            self.logger.info(f"Snapshot creado: {snapshot.snapshot_id} ({tier.value})")
            return snapshot.snapshot_id
            
        except Exception as e:
            self.logger.error(f"Error creando snapshot: {e}")
            raise MCPCoreException(f"Error creando snapshot: {e}")
    
    def _determine_tier(
        self,
        context_type: ContextType,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]]
    ) -> ContextTier:
        """Determinar tier apropiado para el contexto"""
        # Lógica de determinación basada en tipo y contexto
        if context_type == ContextType.CONVERSATION:
            return ContextTier.SHORT_TERM
        elif context_type == ContextType.TASK:
            return ContextTier.MEDIUM_TERM
        elif context_type == ContextType.AGENT_MEMORY:
            return ContextTier.LONG_TERM
        else:
            return ContextTier.MEDIUM_TERM
    
    async def _generate_context_embedding(self, content: Dict[str, Any]) -> List[float]:
        """Generar embedding para contenido de contexto"""
        try:
            # Crear texto representativo del contexto
            context_text = self._extract_textual_content(content)
            
            # Generar embedding
            embeddings = await self.embedding_service.generate_embeddings([context_text])
            return embeddings[0]
            
        except Exception as e:
            self.logger.error(f"Error generando embedding: {e}")
            return [0.0] * settings.embedding_dimension
    
    def _extract_textual_content(self, content: Dict[str, Any]) -> str:
        """Extraer contenido textual del contexto"""
        textual_parts = []
        
        def extract_recursive(obj, depth=0):
            if depth > 10:  # Limitar profundidad
                return
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str):
                        textual_parts.append(value)
                    elif isinstance(value, (dict, list)):
                        extract_recursive(value, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, str):
                        textual_parts.append(item)
                    elif isinstance(item, (dict, list)):
                        extract_recursive(item, depth + 1)
        
        extract_recursive(content)
        return " ".join(textual_parts[:1000])  # Limitar longitud
    
    async def _store_snapshot(self, snapshot: ContextSnapshot, compressed_data: bytes) -> None:
        """Almacenar snapshot según su tier"""
        tier_config = self.tier_config[snapshot.tier]
        
        if tier_config["storage"] == "redis":
            await self._store_in_redis(snapshot, compressed_data)
        else:
            await self._store_in_postgresql(snapshot, compressed_data)
    
    async def _store_in_redis(self, snapshot: ContextSnapshot, compressed_data: bytes) -> None:
        """Almacenar snapshot en Redis"""
        try:
            key = f"context:snapshot:{snapshot.snapshot_id}"
            await self._redis_client.setex(
                key,
                int(timedelta(hours=self.tier_config[snapshot.tier]["max_age_hours"]).total_seconds()),
                compressed_data
            )
            
            # También almacenar metadatos
            metadata_key = f"context:metadata:{snapshot.snapshot_id}"
            await self._redis_client.setex(
                metadata_key,
                int(timedelta(hours=self.tier_config[snapshot.tier]["max_age_hours"]).total_seconds()),
                json.dumps(asdict(snapshot), default=str, separators=(',', ':'))
            )
            
        except Exception as e:
            self.logger.error(f"Error almacenando snapshot en Redis: {e}")
            raise DatabaseException("Error almacenando en Redis", "store", original_error=e)
    
    async def _store_in_postgresql(self, snapshot: ContextSnapshot, compressed_data: bytes) -> None:
        """Almacenar snapshot en PostgreSQL"""
        try:
            async with self._db_pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO context_snapshots (
                        snapshot_id, parent_id, context_type, tier, content, metadata,
                        embedding, compression_type, compressed_size, original_size,
                        created_at, expires_at, user_id, session_id
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ''',
                    snapshot.snapshot_id,
                    snapshot.parent_id,
                    snapshot.context_type.value,
                    snapshot.tier.value,
                    compressed_data,
                    json.dumps(snapshot.metadata, default=str),
                    snapshot.embedding,
                    snapshot.compression_type.value,
                    snapshot.compressed_size,
                    snapshot.original_size,
                    snapshot.created_at,
                    snapshot.expires_at,
                    getattr(snapshot, 'user_id', None),
                    getattr(snapshot, 'session_id', None)
                )
                
                # Crear índice de búsqueda
                if snapshot.embedding:
                    content_text = self._extract_textual_content(snapshot.content)
                    await conn.execute('''
                        INSERT INTO context_search_index (
                            snapshot_id, search_vector, content_text
                        ) VALUES ($1, $2, $3)
                    ''', snapshot.snapshot_id, snapshot.embedding, content_text)
                    
        except Exception as e:
            self.logger.error(f"Error almacenando snapshot en PostgreSQL: {e}")
            raise DatabaseException("Error almacenando en PostgreSQL", "store", original_error=e)
    
    async def _update_indexes(self, snapshot: ContextSnapshot) -> None:
        """Actualizar índices después de crear snapshot"""
        try:
            # Actualizar índices por tipo
            self.indexes["by_type"][snapshot.context_type.value].add(snapshot.snapshot_id)
            
            # Actualizar índices por tier
            self.indexes["by_tier"][snapshot.tier.value].add(snapshot.snapshot_id)
            
            # Actualizar índices por usuario
            user_id = getattr(snapshot, 'user_id', None)
            if user_id:
                self.indexes["by_user"][user_id].add(snapshot.snapshot_id)
            
            # Actualizar índice temporal
            self.indexes["by_timestamp"].append((snapshot.created_at, snapshot.snapshot_id))
            
        except Exception as e:
            self.logger.error(f"Error actualizando índices: {e}")
    
    async def retrieve_snapshot(self, snapshot_id: str) -> Optional[ContextSnapshot]:
        """Recuperar snapshot por ID"""
        try:
            # Verificar cache primero
            if snapshot_id in self._cache["snapshots"]:
                snapshot = self._cache["snapshots"][snapshot_id]
                snapshot.access_count += 1
                snapshot.last_accessed = datetime.now()
                return snapshot
            
            # Buscar en Redis primero (short-term)
            snapshot = await self._retrieve_from_redis(snapshot_id)
            if snapshot:
                self._cache["snapshots"][snapshot_id] = snapshot
                return snapshot
            
            # Buscar en PostgreSQL (medium/long-term)
            snapshot = await self._retrieve_from_postgresql(snapshot_id)
            if snapshot:
                self._cache["snapshots"][snapshot_id] = snapshot
                return snapshot
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error recuperando snapshot {snapshot_id}: {e}")
            return None
    
    async def _retrieve_from_redis(self, snapshot_id: str) -> Optional[ContextSnapshot]:
        """Recuperar snapshot desde Redis"""
        try:
            # Obtener metadatos
            metadata_key = f"context:metadata:{snapshot_id}"
            metadata_data = await self._redis_client.get(metadata_key)
            
            if not metadata_data:
                return None
            
            metadata = json.loads(metadata_data.decode())
            
            # Obtener contenido comprimido
            content_key = f"context:snapshot:{snapshot_id}"
            compressed_data = await self._redis_client.get(content_key)
            
            if not compressed_data:
                return None
            
            # Reconstruir snapshot
            snapshot = ContextSnapshot(
                snapshot_id=metadata['snapshot_id'],
                parent_id=metadata.get('parent_id'),
                context_type=ContextType(metadata['context_type']),
                tier=ContextTier(metadata['tier']),
                content={},  # Se llenará después
                metadata=metadata.get('metadata', {}),
                embedding=metadata.get('embedding'),
                compression_type=CompressionType(metadata['compression_type']),
                compressed_size=metadata['compressed_size'],
                original_size=metadata['original_size'],
                created_at=datetime.fromisoformat(metadata['created_at']),
                expires_at=datetime.fromisoformat(metadata['expires_at']) if metadata.get('expires_at') else None,
                access_count=metadata.get('access_count', 0),
                last_accessed=datetime.fromisoformat(metadata['last_accessed'])
            )
            
            # Descomprimir contenido
            snapshot.content = snapshot.decompress(compressed_data)
            
            return snapshot
            
        except Exception as e:
            self.logger.error(f"Error recuperando snapshot de Redis: {e}")
            return None
    
    async def _retrieve_from_postgresql(self, snapshot_id: str) -> Optional[ContextSnapshot]:
        """Recuperar snapshot desde PostgreSQL"""
        try:
            async with self._db_pool.acquire() as conn:
                row = await conn.fetchrow('''
                    SELECT * FROM context_snapshots WHERE snapshot_id = $1
                ''', snapshot_id)
                
                if not row:
                    return None
                
                # Descomprimir contenido
                content = {}
                if row['content']:
                    snapshot = ContextSnapshot(
                        snapshot_id=row['snapshot_id'],
                        parent_id=row['parent_id'],
                        context_type=ContextType(row['context_type']),
                        tier=ContextTier(row['tier']),
                        content={},
                        metadata=row['metadata'] or {},
                        embedding=row['embedding'],
                        compression_type=CompressionType(row['compression_type']),
                        compressed_size=row['compressed_size'],
                        original_size=row['original_size'],
                        created_at=row['created_at'],
                        expires_at=row['expires_at'],
                        access_count=row['access_count'],
                        last_accessed=row['last_accessed']
                    )
                    content = snapshot.decompress(row['content'])
                
                return ContextSnapshot(
                    snapshot_id=row['snapshot_id'],
                    parent_id=row['parent_id'],
                    context_type=ContextType(row['context_type']),
                    tier=ContextTier(row['tier']),
                    content=content,
                    metadata=row['metadata'] or {},
                    embedding=row['embedding'],
                    compression_type=CompressionType(row['compression_type']),
                    compressed_size=row['compressed_size'],
                    original_size=row['original_size'],
                    created_at=row['created_at'],
                    expires_at=row['expires_at'],
                    access_count=row['access_count'],
                    last_accessed=row['last_accessed']
                )
                
        except Exception as e:
            self.logger.error(f"Error recuperando snapshot de PostgreSQL: {e}")
            return None
    
    async def semantic_search(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 10,
        context_type: Optional[ContextType] = None,
        tier: Optional[ContextTier] = None
    ) -> List[Tuple[ContextSnapshot, float]]:
        """Búsqueda semántica rápida de contexto"""
        try:
            # Generar embedding de consulta
            query_embedding = await self._generate_context_embedding({"query": query})
            
            # Construir consulta SQL
            sql_conditions = ["1=1"]
            params = []
            param_count = 0
            
            if user_id:
                param_count += 1
                sql_conditions.append(f"user_id = ${param_count}")
                params.append(user_id)
            
            if session_id:
                param_count += 1
                sql_conditions.append(f"session_id = ${param_count}")
                params.append(session_id)
            
            if context_type:
                param_count += 1
                sql_conditions.append(f"context_type = ${param_count}")
                params.append(context_type.value)
            
            if tier:
                param_count += 1
                sql_conditions.append(f"tier = ${param_count}")
                params.append(tier.value)
            
            # Agregar embedding y límite
            param_count += 1
            sql_conditions.append(f"embedding IS NOT NULL")
            sql_conditions.append(f"created_at > NOW() - INTERVAL '30 days'")  # Solo contexto reciente
            
            where_clause = " AND ".join(sql_conditions)
            
            async with self._db_pool.acquire() as conn:
                rows = await conn.fetch(f'''
                    SELECT 
                        snapshot_id,
                        context_type,
                        tier,
                        metadata,
                        embedding,
                        created_at,
                        1 - (embedding <=> $1) as similarity
                    FROM context_snapshots
                    WHERE {where_clause}
                    ORDER BY similarity DESC
                    LIMIT ${param_count + 1}
                ''', query_embedding, *params, limit)
            
            results = []
            for row in rows:
                snapshot = await self.retrieve_snapshot(row['snapshot_id'])
                if snapshot:
                    results.append((snapshot, float(row['similarity'])))
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error en búsqueda semántica: {e}")
            return []
    
    async def _check_clustering(self, snapshot: ContextSnapshot) -> None:
        """Verificar si el snapshot necesita clustering semántico"""
        try:
            if not snapshot.embedding:
                return
            
            # Buscar cluster similar
            similar_cluster = await self._find_similar_cluster(snapshot.embedding)
            
            if similar_cluster:
                await self._add_to_cluster(snapshot, similar_cluster)
            else:
                await self._create_new_cluster(snapshot)
                
        except Exception as e:
            self.logger.error(f"Error en clustering: {e}")
    
    async def _find_similar_cluster(self, embedding: List[float]) -> Optional[ContextCluster]:
        """Encontrar cluster semánticamente similar"""
        try:
            # Usar Vector Store para búsqueda de clusters similares
            results = await self.vector_store.semantic_search(
                query="cluster context similarity",
                limit=5
            )
            
            for result in results:
                if result['similarity_score'] > 0.8:
                    cluster_id = result['metadata'].get('cluster_id')
                    if cluster_id and cluster_id in self._cache["clusters"]:
                        return self._cache["clusters"][cluster_id]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error buscando cluster similar: {e}")
            return None
    
    async def _add_to_cluster(self, snapshot: ContextSnapshot, cluster: ContextCluster) -> None:
        """Agregar snapshot a cluster existente"""
        try:
            cluster.snapshots.add(snapshot.snapshot_id)
            cluster.last_merged = datetime.now()
            
            # Actualizar centroid
            await self._update_cluster_centroid(cluster)
            
            # Almacenar cambios
            await self._store_cluster_update(cluster)
            
            self.logger.info(f"Snapshot {snapshot.snapshot_id} agregado al cluster {cluster.cluster_id}")
            
        except Exception as e:
            self.logger.error(f"Error agregando a cluster: {e}")
    
    async def _create_new_cluster(self, snapshot: ContextSnapshot) -> None:
        """Crear nuevo cluster para snapshot"""
        try:
            cluster = ContextCluster(
                cluster_id=str(uuid.uuid4()),
                snapshots={snapshot.snapshot_id},
                centroid_embedding=snapshot.embedding,
                metadata={"created_from": snapshot.snapshot_id}
            )
            
            # Almacenar cluster
            await self._store_cluster(cluster)
            
            # Cachear
            self._cache["clusters"][cluster.cluster_id] = cluster
            
            self.logger.info(f"Nuevo cluster creado: {cluster.cluster_id}")
            
        except Exception as e:
            self.logger.error(f"Error creando cluster: {e}")
    
    async def _update_cluster_centroid(self, cluster: ContextCluster) -> None:
        """Actualizar centroid del cluster"""
        try:
            # Obtener embeddings de todos los snapshots en el cluster
            embeddings = []
            for snapshot_id in cluster.snapshots:
                snapshot = await self.retrieve_snapshot(snapshot_id)
                if snapshot and snapshot.embedding:
                    embeddings.append(np.array(snapshot.embedding))
            
            if embeddings:
                # Calcular nuevo centroid
                centroid = np.mean(embeddings, axis=0).tolist()
                cluster.centroid_embedding = centroid
                
        except Exception as e:
            self.logger.error(f"Error actualizando centroid: {e}")
    
    async def _store_cluster(self, cluster: ContextCluster) -> None:
        """Almacenar cluster en base de datos"""
        try:
            async with self._db_pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO context_clusters (
                        cluster_id, snapshots, centroid_embedding, 
                        similarity_threshold, metadata
                    ) VALUES ($1, $2, $3, $4, $5)
                ''', 
                    cluster.cluster_id,
                    list(cluster.snapshots),
                    cluster.centroid_embedding,
                    cluster.similarity_threshold,
                    json.dumps(cluster.metadata)
                )
                
        except Exception as e:
            self.logger.error(f"Error almacenando cluster: {e}")
    
    async def _store_cluster_update(self, cluster: ContextCluster) -> None:
        """Almacenar actualización de cluster"""
        try:
            async with self._db_pool.acquire() as conn:
                await conn.execute('''
                    UPDATE context_clusters 
                    SET snapshots = $1, centroid_embedding = $2, 
                        last_merged = NOW(), metadata = $3
                    WHERE cluster_id = $4
                ''',
                    list(cluster.snapshots),
                    cluster.centroid_embedding,
                    json.dumps(cluster.metadata),
                    cluster.cluster_id
                )
                
        except Exception as e:
            self.logger.error(f"Error actualizando cluster: {e}")
    
    async def recover_session_context(
        self,
        user_id: str,
        session_id: str,
        max_age_hours: int = 24
    ) -> List[ContextSnapshot]:
        """Recuperar contexto completo de sesión"""
        try:
            snapshots = []
            
            async with self._db_pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT snapshot_id 
                    FROM context_snapshots
                    WHERE user_id = $1 AND session_id = $2 
                    AND created_at > NOW() - INTERVAL '%s hours'
                    ORDER BY created_at ASC
                ''' % max_age_hours, user_id, session_id)
                
                for row in rows:
                    snapshot = await self.retrieve_snapshot(row['snapshot_id'])
                    if snapshot:
                        snapshots.append(snapshot)
            
            self.logger.info(f"Contexto de sesión recuperado: {len(snapshots)} snapshots")
            return snapshots
            
        except Exception as e:
            self.logger.error(f"Error recoveriendo contexto de sesión: {e}")
            return []
    
    async def create_version(
        self,
        snapshot_id: str,
        changes: Dict[str, Any],
        author: str = "system",
        message: str = ""
    ) -> str:
        """Crear versión de control de snapshot"""
        try:
            # Obtener snapshot actual
            snapshot = await self.retrieve_snapshot(snapshot_id)
            if not snapshot:
                raise MCPCoreException(f"Snapshot no encontrado: {snapshot_id}")
            
            # Calcular diff con versión anterior
            previous_versions = await self._get_previous_versions(snapshot_id)
            if previous_versions:
                parent_version = previous_versions[0]  # Última versión
                diff = self._calculate_diff(parent_version, snapshot, changes)
            else:
                diff = {"added": changes, "removed": {}, "modified": {}}
            
            # Crear versión
            version = ContextVersion(
                version_id=str(uuid.uuid4()),
                snapshot_id=snapshot_id,
                parent_version=parent_version.version_id if previous_versions else None,
                changes=changes,
                diff=diff,
                author=author,
                message=message
            )
            
            # Almacenar versión
            await self._store_version(version)
            
            self.logger.info(f"Versión creada: {version.version_id}")
            return version.version_id
            
        except Exception as e:
            self.logger.error(f"Error creando versión: {e}")
            raise MCPCoreException(f"Error creando versión: {e}")
    
    def _calculate_diff(
        self,
        old_version: ContextVersion,
        new_snapshot: ContextSnapshot,
        changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calcular diff entre versiones"""
        # Implementación simplificada del cálculo de diff
        return {
            "changes": changes,
            "metadata_modified": len(changes.get("metadata", {})),
            "content_modified": "content" in changes
        }
    
    async def _get_previous_versions(self, snapshot_id: str) -> List[ContextVersion]:
        """Obtener versiones anteriores del snapshot"""
        try:
            async with self._db_pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT * FROM context_versions
                    WHERE snapshot_id = $1
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', snapshot_id)
                
                versions = []
                for row in rows:
                    version = ContextVersion(
                        version_id=row['version_id'],
                        snapshot_id=row['snapshot_id'],
                        parent_version=row['parent_version'],
                        changes=row['changes'],
                        diff=row['diff'],
                        created_at=row['created_at'],
                        author=row['author'],
                        message=row['message']
                    )
                    versions.append(version)
                
                return versions
                
        except Exception as e:
            self.logger.error(f"Error obteniendo versiones anteriores: {e}")
            return []
    
    async def _store_version(self, version: ContextVersion) -> None:
        """Almacenar versión en base de datos"""
        try:
            async with self._db_pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO context_versions (
                        version_id, snapshot_id, parent_version, 
                        changes, diff, author, message
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ''',
                    version.version_id,
                    version.snapshot_id,
                    version.parent_version,
                    json.dumps(version.changes),
                    json.dumps(version.diff),
                    version.author,
                    version.message
                )
                
        except Exception as e:
            self.logger.error(f"Error almacenando versión: {e}")
            raise DatabaseException("Error almacenando versión", "store", original_error=e)
    
    async def optimize_storage(self) -> Dict[str, Any]:
        """Optimización automática de almacenamiento"""
        try:
            results = {
                "pruned_snapshots": 0,
                "moved_to_tier": {},
                "compressed_snapshots": 0,
                "freed_space_mb": 0
            }
            
            # 1. Limpiar snapshots expirados
            expired_count = await self._cleanup_expired_snapshots()
            results["pruned_snapshots"] = expired_count
            
            # 2. Optimizar tiers
            tier_optimization = await self._optimize_tiers()
            results["moved_to_tier"] = tier_optimization
            
            # 3. Comprimir snapshots antiguos
            compression_results = await self._recompress_old_snapshots()
            results["compressed_snapshots"] = compression_results["count"]
            results["freed_space_mb"] = compression_results["space_saved"]
            
            # 4. Actualizar índices
            await self._rebuild_indexes()
            
            self.logger.info(f"Optimización completada: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error en optimización: {e}")
            return {}
    
    async def _cleanup_expired_snapshots(self) -> int:
        """Limpiar snapshots expirados"""
        try:
            async with self._db_pool.acquire() as conn:
                # Eliminar snapshots expirados
                result = await conn.execute('''
                    DELETE FROM context_snapshots 
                    WHERE expires_at IS NOT NULL AND expires_at < NOW()
                ''')
                
                deleted_count = int(result.split()[-1]) if result.split()[-1].isdigit() else 0
                
                # También limpiar de Redis
                await self._cleanup_expired_redis()
                
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Error limpiando snapshots expirados: {e}")
            return 0
    
    async def _cleanup_expired_redis(self) -> None:
        """Limpiar snapshots expirados de Redis"""
        try:
            # Redis maneja automáticamente expiración con TTL
            # Pero podemos hacer limpieza manual de claves huérfanas
            pattern = "context:snapshot:*"
            async for key in self._redis_client.scan_iter(pattern):
                ttl = await self._redis_client.ttl(key)
                if ttl <= 0:
                    await self._redis_client.delete(key)
                    metadata_key = key.replace("context:snapshot:", "context:metadata:")
                    await self._redis_client.delete(metadata_key)
                    
        except Exception as e:
            self.logger.error(f"Error limpiando Redis: {e}")
    
    async def _optimize_tiers(self) -> Dict[str, int]:
        """Optimizar distribución entre tiers"""
        try:
            moved_counts = defaultdict(int)
            
            # Mover snapshots según patrones de acceso
            async with self._db_pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT snapshot_id, tier, access_count, created_at
                    FROM context_snapshots
                    WHERE created_at < NOW() - INTERVAL '1 hour'
                    ORDER BY access_count DESC, created_at ASC
                ''')
                
                for row in rows:
                    current_tier = ContextTier(row['tier'])
                    access_count = row['access_count']
                    age_hours = (datetime.now() - row['created_at']).total_seconds() / 3600
                    
                    # Lógica de promoción/democion
                    new_tier = self._calculate_optimal_tier(current_tier, access_count, age_hours)
                    
                    if new_tier != current_tier:
                        await conn.execute('''
                            UPDATE context_snapshots SET tier = $1 WHERE snapshot_id = $2
                        ''', new_tier.value, row['snapshot_id'])
                        
                        moved_counts[new_tier.value] += 1
                        self.logger.info(f"Snapshot {row['snapshot_id']} movido de {current_tier.value} a {new_tier.value}")
            
            return dict(moved_counts)
            
        except Exception as e:
            self.logger.error(f"Error optimizando tiers: {e}")
            return {}
    
    def _calculate_optimal_tier(
        self,
        current_tier: ContextTier,
        access_count: int,
        age_hours: float
    ) -> ContextTier:
        """Calcular tier óptimo para snapshot"""
        # Lógica de promoción basada en acceso y edad
        if access_count > 50 and age_hours < 6:
            return ContextTier.SHORT_TERM  # Muy accedido, reciente
        elif access_count > 10 and age_hours < 24:
            return ContextTier.MEDIUM_TERM  # Moderadamente accedido
        elif age_hours > 168:  # 1 semana
            return ContextTier.ARCHIVE  # Muy antiguo
        else:
            return current_tier
    
    async def _recompress_old_snapshots(self) -> Dict[str, Any]:
        """Recomprimir snapshots antiguos para ahorrar espacio"""
        try:
            results = {"count": 0, "space_saved": 0}
            
            async with self._db_pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT snapshot_id, content, compression_type, original_size
                    FROM context_snapshots
                    WHERE created_at < NOW() - INTERVAL '7 days'
                    AND compression_type = 'none'
                    AND original_size > 1024  -- Solo snapshots grandes
                    LIMIT 100
                ''')
                
                for row in rows:
                    try:
                        # Descomprimir contenido original
                        content_data = row['content']
                        if isinstance(content_data, bytes):
                            content = pickle.loads(content_data)
                        else:
                            content = content_data
                        
                        # Aplicar compresión más eficiente
                        new_compression = CompressionType.GZIP
                        new_snapshot = ContextSnapshot(
                            snapshot_id=row['snapshot_id'],
                            context_type=ContextType.CONVERSATION,
                            tier=ContextTier.MEDIUM_TERM,
                            content=content,
                            compression_type=new_compression
                        )
                        
                        compressed_data = new_snapshot.compress(new_compression)
                        
                        # Actualizar en BD
                        await conn.execute('''
                            UPDATE context_snapshots 
                            SET content = $1, compression_type = $2, compressed_size = $3
                            WHERE snapshot_id = $4
                        ''', compressed_data, new_compression.value, len(compressed_data), row['snapshot_id'])
                        
                        space_saved = row['original_size'] - len(compressed_data)
                        results["space_saved"] += space_saved
                        results["count"] += 1
                        
                    except Exception as e:
                        self.logger.error(f"Error recomprimiendo snapshot {row['snapshot_id']}: {e}")
            
            results["space_saved"] = results["space_saved"] / (1024 * 1024)  # Convertir a MB
            return results
            
        except Exception as e:
            self.logger.error(f"Error recomprimiendo snapshots: {e}")
            return {"count": 0, "space_saved": 0}
    
    async def _rebuild_indexes(self) -> None:
        """Reconstruir índices para optimización"""
        try:
            # Limpiar índices actuales
            self.indexes = {
                "by_type": defaultdict(set),
                "by_user": defaultdict(set),
                "by_tier": defaultdict(set),
                "by_timestamp": deque(maxlen=10000),
                "similarity": defaultdict(dict)
            }
            
            # Recargar desde BD
            await self._load_indexes()
            
            self.logger.info("Índices reconstruidos")
            
        except Exception as e:
            self.logger.error(f"Error reconstruyendo índices: {e}")
    
    async def _maintenance_loop(self) -> None:
        """Loop de mantenimiento automático"""
        while True:
            try:
                await asyncio.sleep(3600)  # Cada hora
                
                # Ejecutar optimización
                optimization_results = await self.optimize_storage()
                
                # Limpiar cache si es necesario
                if len(self._cache["snapshots"]) > 5000:
                    await self._cleanup_cache()
                
                # Verificar salud de conexiones
                await self._health_check()
                
                self.logger.info(f"Mantenimiento completado: {optimization_results}")
                
            except Exception as e:
                self.logger.error(f"Error en loop de mantenimiento: {e}")
                await asyncio.sleep(300)  # Esperar 5 minutos antes de reintentar
    
    async def _cleanup_cache(self) -> None:
        """Limpiar cache para liberar memoria"""
        try:
            # Eliminar snapshots menos accedidos
            sorted_snapshots = sorted(
                self._cache["snapshots"].items(),
                key=lambda x: x[1].access_count
            )
            
            # Mantener solo los 2000 más accedidos
            snapshots_to_remove = len(sorted_snapshots) - 2000
            for i in range(snapshots_to_remove):
                snapshot_id = sorted_snapshots[i][0]
                del self._cache["snapshots"][snapshot_id]
            
            self.logger.info(f"Cache limpiado: {snapshots_to_remove} snapshots removidos")
            
        except Exception as e:
            self.logger.error(f"Error limpiando cache: {e}")
    
    async def _health_check(self) -> Dict[str, Any]:
        """Verificar salud de componentes"""
        health_status = {
            "redis": False,
            "postgresql": False,
            "embedding_service": False,
            "vector_store": False,
            "cache_size": len(self._cache["snapshots"]),
            "indexes_size": {
                "by_type": len(self.indexes["by_type"]),
                "by_user": len(self.indexes["by_user"]),
                "by_tier": len(self.indexes["by_tier"]),
                "by_timestamp": len(self.indexes["by_timestamp"])
            }
        }
        
        try:
            # Verificar Redis
            if self._redis_client:
                await self._redis_client.ping()
                health_status["redis"] = True
        except Exception as e:
            self.logger.error(f"Redis health check falló: {e}")
        
        try:
            # Verificar PostgreSQL
            if self._db_pool:
                async with self._db_pool.acquire() as conn:
                    await conn.fetchval('SELECT 1')
                health_status["postgresql"] = True
        except Exception as e:
            self.logger.error(f"PostgreSQL health check falló: {e}")
        
        try:
            # Verificar servicios
            health_status["embedding_service"] = hasattr(self.embedding_service, 'model')
            health_status["vector_store"] = self.vector_store.is_initialized
        except Exception as e:
            self.logger.error(f"Servicios health check falló: {e}")
        
        return health_status
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del motor de persistencia"""
        try:
            health = await self._health_check()
            
            # Estadísticas de base de datos
            db_stats = {}
            if self._db_pool:
                async with self._db_pool.acquire() as conn:
                    db_stats = {
                        "total_snapshots": await conn.fetchval('SELECT COUNT(*) FROM context_snapshots'),
                        "total_clusters": await conn.fetchval('SELECT COUNT(*) FROM context_clusters'),
                        "total_versions": await conn.fetchval('SELECT COUNT(*) FROM context_versions'),
                        "avg_snapshot_size": await conn.fetchval('SELECT AVG(original_size) FROM context_snapshots'),
                        "total_storage_mb": await conn.fetchval('''
                            SELECT SUM(compressed_size) / 1024.0 / 1024.0 FROM context_snapshots
                        ''')
                    }
            
            # Estadísticas de Redis
            redis_stats = {}
            if self._redis_client:
                info = await self._redis_client.info()
                redis_stats = {
                    "connected": health["redis"],
                    "memory_usage_mb": info.get("used_memory", 0) / 1024 / 1024,
                    "keys_count": await self._redis_client.dbsize()
                }
            
            return {
                "health": health,
                "database": db_stats,
                "redis": redis_stats,
                "cache": {
                    "snapshots_count": len(self._cache["snapshots"]),
                    "clusters_count": len(self._cache["clusters"]),
                    "versions_count": len(self._cache["versions"])
                },
                "performance": {
                    "avg_retrieval_time_ms": "calculated_on_demand",
                    "cache_hit_ratio": "calculated_on_demand",
                    "indexes_size": health["indexes_size"]
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {"error": str(e)}
    
    async def cleanup(self) -> None:
        """Limpiar recursos"""
        try:
            # Cerrar conexiones
            if self._redis_client:
                await self._redis_client.close()
            
            if self._db_pool:
                await self._db_pool.close()
            
            # Cerrar executor
            self._executor.shutdown(wait=True)
            
            # Limpiar cache
            self._cache.clear()
            
            self.logger.info("Context Persistence Engine cerrado")
            
        except Exception as e:
            self.logger.error(f"Error cerrando Context Persistence Engine: {e}")


# Instancia global del motor
context_persistence_engine = ContextPersistenceEngine()


# Funciones de conveniencia para uso global

async def initialize_context_persistence() -> None:
    """Inicializar motor de persistencia de contexto"""
    await context_persistence_engine.initialize()


async def create_context_snapshot(
    context_type: ContextType,
    content: Dict[str, Any],
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    parent_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Función de conveniencia para crear snapshot"""
    return await context_persistence_engine.create_snapshot(
        context_type=context_type,
        content=content,
        user_id=user_id,
        session_id=session_id,
        parent_id=parent_id,
        metadata=metadata
    )


async def retrieve_context_snapshot(snapshot_id: str) -> Optional[ContextSnapshot]:
    """Función de conveniencia para recuperar snapshot"""
    return await context_persistence_engine.retrieve_snapshot(snapshot_id)


async def search_context_semantic(
    query: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 10,
    context_type: Optional[ContextType] = None
) -> List[Tuple[ContextSnapshot, float]]:
    """Función de conveniencia para búsqueda semántica"""
    return await context_persistence_engine.semantic_search(
        query=query,
        user_id=user_id,
        session_id=session_id,
        limit=limit,
        context_type=context_type
    )


async def recover_session(
    user_id: str,
    session_id: str,
    max_age_hours: int = 24
) -> List[ContextSnapshot]:
    """Función de conveniencia para recuperación de sesión"""
    return await context_persistence_engine.recover_session_context(
        user_id=user_id,
        session_id=session_id,
        max_age_hours=max_age_hours
    )


async def get_context_engine_stats() -> Dict[str, Any]:
    """Función de conveniencia para obtener estadísticas"""
    return await context_persistence_engine.get_stats()


async def optimize_context_storage() -> Dict[str, Any]:
    """Función de conveniencia para optimización"""
    return await context_persistence_engine.optimize_storage()


# Context-aware agent initialization
async def initialize_agent_with_context(
    agent_name: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    context_requirements: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Inicializar agente con contexto relevante"""
    try:
        # Obtener contexto de sesión si está disponible
        session_context = []
        if user_id and session_id:
            session_context = await recover_session(user_id, session_id)
        
        # Buscar contexto relevante para el agente
        agent_context = []
        if context_requirements:
            for req_type in context_requirements.get("context_types", []):
                if isinstance(req_type, str):
                    req_type = ContextType(req_type)
                
                search_results = await search_context_semantic(
                    query=f"{agent_name} {req_type.value}",
                    user_id=user_id,
                    limit=context_requirements.get("max_contexts", 5)
                )
                
                for snapshot, similarity in search_results:
                    if similarity > 0.6:  # Umbral de relevancia
                        agent_context.append({
                            "snapshot_id": snapshot.snapshot_id,
                            "content": snapshot.content,
                            "similarity": similarity,
                            "type": snapshot.context_type.value
                        })
        
        initialization_context = {
            "agent_name": agent_name,
            "session_context_count": len(session_context),
            "relevant_context": agent_context[:10],  # Limitar contexto
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Crear snapshot del contexto de inicialización
        init_snapshot_id = await create_context_snapshot(
            context_type=ContextType.AGENT_MEMORY,
            content=initialization_context,
            user_id=user_id,
            session_id=session_id,
            metadata={
                "agent_name": agent_name,
                "initialization": True,
                "context_sources": ["session", "semantic_search"]
            }
        )
        
        self.logger.info(f"Agente {agent_name} inicializado con contexto (snapshot: {init_snapshot_id})")
        
        return {
            "initialization_snapshot_id": init_snapshot_id,
            "session_context": session_context[:5],  # Últimos 5 contextos de sesión
            "relevant_context": agent_context,
            "context_summary": {
                "total_sources": len(session_context) + len(agent_context),
                "primary_types": list(set(ctx.get("type") for ctx in agent_context if ctx.get("type")))
            }
        }
        
    except Exception as e:
        self.logger.error(f"Error inicializando agente con contexto: {e}")
        return {
            "error": str(e),
            "fallback_context": session_context[:3] if session_context else []
        }


# Exportar funciones principales
__all__ = [
    'ContextPersistenceEngine',
    'ContextSnapshot',
    'ContextCluster', 
    'ContextVersion',
    'ContextTier',
    'ContextType',
    'CompressionType',
    'context_persistence_engine',
    'initialize_context_persistence',
    'create_context_snapshot',
    'retrieve_context_snapshot',
    'search_context_semantic',
    'recover_session',
    'get_context_engine_stats',
    'optimize_context_storage',
    'initialize_agent_with_context'
]