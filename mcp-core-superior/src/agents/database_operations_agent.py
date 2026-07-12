"""
Database Operations Agent MCP para PostgreSQL + pgvector
Proporciona operaciones avanzadas de base de datos incluyendo búsqueda vectorial,
gestión de esquemas, migración de datos, optimización y monitoreo
"""

from typing import Dict, Any, List, Optional, Union
import asyncio
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import os
import subprocess
import tempfile
import time
from contextlib import contextmanager

from sqlalchemy import create_engine, text, MetaData, Table, Column, inspect, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import psycopg2
import psycopg2.extras
from pgvector.psycopg2 import register_vector

from .base_agent_wrapper import BaseAgentWrapper, AgentCapability
from ..core.exceptions import AgentException, handle_exceptions
from ..core.config import settings


class DatabaseOperationType(Enum):
    """Tipos de operaciones de base de datos"""
    SQL_QUERY = "sql_query"
    VECTOR_SEARCH = "vector_search"
    SCHEMA_MANAGEMENT = "schema_management"
    DATA_MIGRATION = "data_migration"
    BACKUP_RESTORE = "backup_restore"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    CONNECTION_POOL = "connection_pool"
    INDEX_MANAGEMENT = "index_management"
    MONITORING = "monitoring"


class ConnectionPoolStatus(Enum):
    """Estados del pool de conexiones"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"


@dataclass
class DatabaseConnectionConfig:
    """Configuración de conexión a PostgreSQL"""
    host: str = "localhost"
    port: int = 5432
    database: str = "rag_database"
    user: str = "postgres"
    password: str = "password"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    ssl_mode: str = "prefer"
    
    @property
    def database_url(self) -> str:
        """Generar URL de conexión"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class QueryExecutionResult:
    """Resultado de ejecución de consulta"""
    query: str
    execution_time_ms: float
    rows_affected: int
    result_data: List[Dict[str, Any]]
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VectorSearchResult:
    """Resultado de búsqueda vectorial"""
    query_embedding: List[float]
    results: List[Dict[str, Any]]
    search_time_ms: float
    total_matches: int
    threshold_used: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Métricas de performance de base de datos"""
    active_connections: int
    total_connections: int
    cache_hit_ratio: float
    query_avg_time_ms: float
    slow_queries_count: int
    table_sizes: Dict[str, int]
    index_usage: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)


class DatabaseOperationsAgentWrapper(BaseAgentWrapper):
    """
    Agent MCP para operaciones de PostgreSQL + pgvector
    
    Capacidades:
    - Ejecución de consultas SQL
    - Búsqueda vectorial semántica
    - Gestión de esquemas
    - Migración de datos
    - Backup/restore
    - Optimización de performance
    - Gestión de pool de conexiones
    - Gestión de índices
    - Monitoreo y métricas
    """
    
    def __init__(self, db_config: Optional[DatabaseConnectionConfig] = None):
        # Definir capacidades del agente
        capabilities = [
            AgentCapability.DATABASE_OPERATIONS,
            AgentCapability.SCHEMA_MANAGEMENT,
            AgentCapability.DATA_MIGRATION,
            AgentCapability.PERFORMANCE_OPTIMIZATION
        ]
        
        # Agregar capacidades específicas del Database Operations Agent
        if not hasattr(AgentCapability, 'DATABASE_OPERATIONS'):
            AgentCapability.DATABASE_OPERATIONS = "database_operations"
        if not hasattr(AgentCapability, 'SCHEMA_MANAGEMENT'):
            AgentCapability.SCHEMA_MANAGEMENT = "schema_management"
        if not hasattr(AgentCapability, 'DATA_MIGRATION'):
            AgentCapability.DATA_MIGRATION = "data_migration"
        if not hasattr(AgentCapability, 'PERFORMANCE_OPTIMIZATION'):
            AgentCapability.PERFORMANCE_OPTIMIZATION = "performance_optimization"
        
        super().__init__(
            agent_name="database_operations",
            capabilities=capabilities,
            max_concurrent=5,
            timeout_seconds=300,
            retry_attempts=3,
            retry_delay=2.0
        )
        
        # Configuración de base de datos
        self.db_config = db_config or DatabaseConnectionConfig()
        self.engine = None
        self.session_factory = None
        self.connection_pool_status = ConnectionPoolStatus.OFFLINE
        
        # Métricas y estadísticas
        self.query_metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "avg_execution_time_ms": 0.0,
            "slow_queries": [],
            "vector_searches": 0,
            "schema_operations": 0
        }
        
        # Configuración de logging
        self.logger = logging.getLogger("mcp.agents.database_operations")
        self.performance_logger = logging.getLogger("mcp.agents.database_operations.performance")
    
    async def _initialize(self) -> None:
        """Inicializar conexión a PostgreSQL + pgvector"""
        try:
            self.logger.info("Inicializando Database Operations Agent...")
            
            # Crear engine con pool de conexiones
            self.engine = create_engine(
                self.db_config.database_url,
                poolclass=QueuePool,
                pool_size=self.db_config.pool_size,
                max_overflow=self.db_config.max_overflow,
                pool_timeout=self.db_config.pool_timeout,
                pool_recycle=self.db_config.pool_recycle,
                echo=False,  # Solo activar para debugging
                future=True
            )
            
            # Crear factory de sesiones
            self.session_factory = sessionmaker(bind=self.engine)
            
            # Test de conexión
            await self._test_connection()
            
            # Registrar extensión pgvector
            await self._ensure_pgvector_extension()
            
            # Verificar estado del pool
            await self._check_pool_status()
            
            self.connection_pool_status = ConnectionPoolStatus.HEALTHY
            self.logger.info("Database Operations Agent inicializado correctamente")
            
        except Exception as e:
            self.connection_pool_status = ConnectionPoolStatus.OFFLINE
            self.logger.error(f"Error inicializando Database Operations Agent: {e}")
            raise AgentException(
                f"Error de inicialización: {str(e)}",
                self.agent_name,
                "initialize",
                error_code="DATABASE_ERROR"
            )
    
    async def _test_connection(self) -> None:
        """Probar conexión a base de datos"""
        try:
            with self.engine.connect() as conn:
                # Test básico
                result = conn.execute(text("SELECT 1 as test"))
                result.fetchone()
                
                # Verificar versión PostgreSQL
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                self.logger.info(f"PostgreSQL versión: {version.split(',')[0]}")
                
        except Exception as e:
            raise AgentException(
                f"Error probando conexión: {str(e)}",
                self.agent_name,
                "test_connection",
                error_code="DATABASE_CONNECTION_FAILED"
            )
    
    async def _ensure_pgvector_extension(self) -> None:
        """Asegurar que la extensión pgvector esté disponible"""
        try:
            with self.engine.connect() as conn:
                # Habilitar extensión pgvector
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                
                # Verificar que esté habilitada
                result = conn.execute(text(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                ))
                
                if not result.fetchone()[0]:
                    raise AgentException(
                        "Extensión pgvector no disponible",
                        self.agent_name,
                        "ensure_pgvector",
                        error_code="VECTOR_DB_ERROR"
                    )
                
                # Registrar tipos vector para psycopg2
                register_vector(conn.connection)
                
                self.logger.info("Extensión pgvector verificada")
                
        except Exception as e:
            self.logger.error(f"Error configurando pgvector: {e}")
            raise
    
    async def _check_pool_status(self) -> ConnectionPoolStatus:
        """Verificar estado del pool de conexiones"""
        try:
            pool = self.engine.pool
            
            # Obtener estadísticas del pool
            total_connections = pool.size()
            checked_out = pool.checkedout()
            overflow = pool.overflow()
            
            status = {
                "total_connections": total_connections,
                "checked_out": checked_out,
                "overflow": overflow,
                "max_overflow": self.db_config.max_overflow,
                "status": "healthy"
            }
            
            # Determinar estado
            if checked_out > total_connections * 0.8:
                self.connection_pool_status = ConnectionPoolStatus.DEGRADED
                status["status"] = "degraded"
                self.logger.warning("Pool de conexiones cerca del límite")
            elif checked_out >= total_connections + overflow:
                self.connection_pool_status = ConnectionPoolStatus.CRITICAL
                status["status"] = "critical"
                self.logger.error("Pool de conexiones al máximo")
            else:
                self.connection_pool_status = ConnectionPoolStatus.HEALTHY
                status["status"] = "healthy"
            
            self.logger.debug(f"Estado del pool: {status}")
            return self.connection_pool_status
            
        except Exception as e:
            self.connection_pool_status = ConnectionPoolStatus.OFFLINE
            self.logger.error(f"Error verificando pool: {e}")
            return ConnectionPoolStatus.OFFLINE
    
    async def process_request(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Procesar request de operaciones de base de datos"""
        operation_type = request.get("operation_type")
        
        if not operation_type:
            raise AgentException(
                "operation_type es requerido",
                self.agent_name,
                "process_request",
                error_code="INVALID_REQUEST"
            )
        
        # Mapear operaciones a capacidades
        operation_mapping = {
            DatabaseOperationType.SQL_QUERY.value: AgentCapability.DATABASE_OPERATIONS,
            DatabaseOperationType.VECTOR_SEARCH.value: AgentCapability.DATABASE_OPERATIONS,
            DatabaseOperationType.SCHEMA_MANAGEMENT.value: AgentCapability.SCHEMA_MANAGEMENT,
            DatabaseOperationType.DATA_MIGRATION.value: AgentCapability.DATA_MIGRATION,
            DatabaseOperationType.PERFORMANCE_OPTIMIZATION.value: AgentCapability.PERFORMANCE_OPTIMIZATION,
            DatabaseOperationType.CONNECTION_POOL.value: AgentCapability.DATABASE_OPERATIONS,
            DatabaseOperationType.INDEX_MANAGEMENT.value: AgentCapability.SCHEMA_MANAGEMENT,
            DatabaseOperationType.MONITORING.value: AgentCapability.PERFORMANCE_OPTIMIZATION,
            DatabaseOperationType.BACKUP_RESTORE.value: AgentCapability.DATA_MIGRATION
        }
        
        capability = operation_mapping.get(operation_type)
        if not capability:
            raise AgentException(
                f"Tipo de operación no soportado: {operation_type}",
                self.agent_name,
                "process_request",
                error_code="INVALID_REQUEST"
            )
        
        return await self.execute_operation(
            operation_name=operation_type,
            capability=capability,
            operation_func=self._dispatch_operation,
            request=request,
            context=context
        )
    
    @handle_exceptions
    async def _dispatch_operation(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Despachar operación específica"""
        operation_type = request.get("operation_type")
        
        operations = {
            DatabaseOperationType.SQL_QUERY.value: self._execute_sql_query,
            DatabaseOperationType.VECTOR_SEARCH.value: self._perform_vector_search,
            DatabaseOperationType.SCHEMA_MANAGEMENT.value: self._manage_schema,
            DatabaseOperationType.DATA_MIGRATION.value: self._migrate_data,
            DatabaseOperationType.BACKUP_RESTORE.value: self._backup_restore,
            DatabaseOperationType.PERFORMANCE_OPTIMIZATION.value: self._optimize_performance,
            DatabaseOperationType.CONNECTION_POOL.value: self._manage_pool,
            DatabaseOperationType.INDEX_MANAGEMENT.value: self._manage_indexes,
            DatabaseOperationType.MONITORING.value: self._monitor_database
        }
        
        operation_func = operations.get(operation_type)
        if not operation_func:
            raise AgentException(
                f"Operación no implementada: {operation_type}",
                self.agent_name,
                "dispatch_operation",
                error_code="NOT_IMPLEMENTED"
            )
        
        return await operation_func(request, context)
    
    # === OPERACIONES DE CONSULTA SQL ===
    
    async def _execute_sql_query(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ejecutar consulta SQL"""
        query = request.get("query")
        params = request.get("parameters", {})
        
        if not query:
            raise AgentException(
                "Query SQL es requerida",
                self.agent_name,
                "execute_sql_query",
                error_code="INVALID_REQUEST"
            )
        
        start_time = time.time()
        
        try:
            with self.engine.connect() as conn:
                # Preparar consulta
                if params:
                    stmt = text(query).bindparams(**params)
                else:
                    stmt = text(query)
                
                # Ejecutar
                result = conn.execute(stmt)
                
                # Obtener resultados
                if result.returns_rows:
                    rows = result.fetchall()
                    columns = result.keys()
                    data = [dict(zip(columns, row)) for row in rows]
                    rows_affected = len(rows)
                else:
                    data = []
                    rows_affected = result.rowcount or 0
                
                execution_time = (time.time() - start_time) * 1000
                
                # Actualizar métricas
                self._update_query_metrics(execution_time, True)
                
                return {
                    "success": True,
                    "query": query,
                    "execution_time_ms": execution_time,
                    "rows_affected": rows_affected,
                    "data": data,
                    "metadata": {
                        "query_type": "SELECT" if query.strip().upper().startswith("SELECT") else "WRITE",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
        except SQLAlchemyError as e:
            execution_time = (time.time() - start_time) * 1000
            self._update_query_metrics(execution_time, False)
            
            raise AgentException(
                f"Error ejecutando query: {str(e)}",
                self.agent_name,
                "execute_sql_query",
                error_code="DATABASE_QUERY_ERROR",
                original_error=e
            )
    
    # === BÚSQUEDA VECTORIAL ===
    
    async def _perform_vector_search(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Realizar búsqueda vectorial con pgvector"""
        query_embedding = request.get("query_embedding")
        table_name = request.get("table_name")
        limit = request.get("limit", 5)
        threshold = request.get("threshold", 0.7)
        
        if not query_embedding or not table_name:
            raise AgentException(
                "query_embedding y table_name son requeridos",
                self.agent_name,
                "vector_search",
                error_code="INVALID_REQUEST"
            )
        
        start_time = time.time()
        
        try:
            with self.engine.connect() as conn:
                # Asegurar que la extensión vector esté disponible
                register_vector(conn.connection)
                
                # Query de búsqueda vectorial usando <-> (distancia euclidiana)
                search_query = text(f"""
                    SELECT *, (embedding <-> :query_embedding::vector) as distance
                    FROM {table_name}
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <-> :query_embedding::vector
                    LIMIT :limit
                """)
                
                # Preparar parámetros
                embedding_str = f"[{','.join(map(str, query_embedding))}]"
                
                result = conn.execute(search_query, {
                    "query_embedding": embedding_str,
                    "limit": limit
                })
                
                rows = result.fetchall()
                columns = [col for col in result.keys() if col != 'distance'] + ['distance']
                
                # Procesar resultados
                search_results = []
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    similarity = 1.0 - (row_dict['distance'] or 1.0)
                    
                    # Filtrar por threshold
                    if similarity >= threshold:
                        row_dict['similarity'] = similarity
                        row_dict['distance'] = row_dict['distance']
                        search_results.append(row_dict)
                
                search_time = (time.time() - start_time) * 1000
                
                # Actualizar métricas
                self.query_metrics["vector_searches"] += 1
                
                return {
                    "success": True,
                    "query_embedding": query_embedding,
                    "table_name": table_name,
                    "search_time_ms": search_time,
                    "results": search_results,
                    "total_matches": len(search_results),
                    "threshold_used": threshold,
                    "metadata": {
                        "search_type": "vector_similarity",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
        except SQLAlchemyError as e:
            search_time = (time.time() - start_time) * 1000
            raise AgentException(
                f"Error en búsqueda vectorial: {str(e)}",
                self.agent_name,
                "vector_search",
                error_code="VECTOR_DB_ERROR",
                original_error=e
            )
    
    # === GESTIÓN DE ESQUEMAS ===
    
    async def _manage_schema(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Gestionar esquema de base de datos"""
        operation = request.get("schema_operation")
        
        if operation == "list_tables":
            return await self._list_tables()
        elif operation == "describe_table":
            return await self._describe_table(request.get("table_name"))
        elif operation == "create_table":
            return await self._create_table(request.get("table_schema"))
        elif operation == "drop_table":
            return await self._drop_table(request.get("table_name"))
        else:
            raise AgentException(
                f"Operación de schema no soportada: {operation}",
                self.agent_name,
                "manage_schema",
                error_code="INVALID_REQUEST"
            )
    
    async def _list_tables(self) -> Dict[str, Any]:
        """Listar todas las tablas"""
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            schemas = inspector.get_schema_names()
            
            table_details = []
            for table in tables:
                columns = inspector.get_columns(table)
                indexes = inspector.get_indexes(table)
                
                table_details.append({
                    "table_name": table,
                    "columns": [{"name": col["name"], "type": str(col["type"]), "nullable": col["nullable"]} for col in columns],
                    "indexes": [{"name": idx["name"], "unique": idx["unique"], "columns": idx["column_names"]} for idx in indexes]
                })
            
            return {
                "success": True,
                "schemas": schemas,
                "tables": table_details,
                "metadata": {
                    "total_tables": len(tables),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            raise AgentException(
                f"Error listando tablas: {str(e)}",
                self.agent_name,
                "list_tables",
                error_code="SCHEMA_ERROR"
            )
    
    async def _describe_table(self, table_name: str) -> Dict[str, Any]:
        """Describir estructura de una tabla"""
        try:
            inspector = inspect(self.engine)
            
            columns = inspector.get_columns(table_name)
            indexes = inspector.get_indexes(table_name)
            foreign_keys = inspector.get_foreign_keys(table_name)
            
            return {
                "success": True,
                "table_name": table_name,
                "columns": [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col["nullable"],
                        "default": str(col.get("default", "")),
                        "autoincrement": col.get("autoincrement", False)
                    }
                    for col in columns
                ],
                "indexes": indexes,
                "foreign_keys": foreign_keys,
                "metadata": {
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            raise AgentException(
                f"Error describiendo tabla {table_name}: {str(e)}",
                self.agent_name,
                "describe_table",
                error_code="SCHEMA_ERROR"
            )
    
    async def _create_table(self, table_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Crear nueva tabla"""
        table_name = table_schema.get("table_name")
        columns = table_schema.get("columns", [])
        
        if not table_name or not columns:
            raise AgentException(
                "table_name y columns son requeridos",
                self.agent_name,
                "create_table",
                error_code="INVALID_REQUEST"
            )
        
        try:
            # Construir SQL para crear tabla
            column_defs = []
            for col in columns:
                col_def = f"{col['name']} {col['type']}"
                if not col.get("nullable", True):
                    col_def += " NOT NULL"
                if col.get("primary_key"):
                    col_def += " PRIMARY KEY"
                column_defs.append(col_def)
            
            create_sql = f"CREATE TABLE {table_name} ({', '.join(column_defs)})"
            
            with self.engine.connect() as conn:
                conn.execute(text(create_sql))
                conn.commit()
            
            return {
                "success": True,
                "table_name": table_name,
                "sql": create_sql,
                "metadata": {
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            raise AgentException(
                f"Error creando tabla: {str(e)}",
                self.agent_name,
                "create_table",
                error_code="SCHEMA_ERROR"
            )
    
    async def _drop_table(self, table_name: str) -> Dict[str, Any]:
        """Eliminar tabla"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                conn.commit()
            
            return {
                "success": True,
                "table_name": table_name,
                "metadata": {
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            raise AgentException(
                f"Error eliminando tabla {table_name}: {str(e)}",
                self.agent_name,
                "drop_table",
                error_code="SCHEMA_ERROR"
            )
    
    # === MIGRACIÓN DE DATOS ===
    
    async def _migrate_data(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Migrar datos entre tablas"""
        source_table = request.get("source_table")
        target_table = request.get("target_table")
        batch_size = request.get("batch_size", 1000)
        
        if not source_table or not target_table:
            raise AgentException(
                "source_table y target_table son requeridos",
                self.agent_name,
                "migrate_data",
                error_code="INVALID_REQUEST"
            )
        
        try:
            total_migrated = 0
            start_time = time.time()
            
            with self.engine.connect() as conn:
                # Obtener estructura de tabla fuente
                inspector = inspect(self.engine)
                columns = [col["name"] for col in inspector.get_columns(source_table)]
                
                # Migrar en lotes
                while True:
                    query = text(f"""
                        SELECT * FROM {source_table}
                        ORDER BY id
                        LIMIT :batch_size
                        OFFSET :offset
                    """)
                    
                    result = conn.execute(query, {"batch_size": batch_size, "offset": total_migrated})
                    
                    if not result.rowcount:
                        break
                    
                    rows = result.fetchall()
                    
                    if not rows:
                        break
                    
                    # Insertar en tabla destino
                    insert_query = text(f"""
                        INSERT INTO {target_table} ({', '.join(columns)})
                        VALUES ({', '.join([f':{i}' for i in range(len(columns))])})
                        ON CONFLICT (id) DO NOTHING
                    """)
                    
                    for row in rows:
                        params = {f"{i}": row[i] for i in range(len(row))}
                        conn.execute(insert_query, params)
                    
                    conn.commit()
                    total_migrated += len(rows)
                    
                    if len(rows) < batch_size:
                        break
            
            migration_time = time.time() - start_time
            
            return {
                "success": True,
                "source_table": source_table,
                "target_table": target_table,
                "total_migrated": total_migrated,
                "migration_time_seconds": migration_time,
                "metadata": {
                    "batch_size": batch_size,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            raise AgentException(
                f"Error migrando datos: {str(e)}",
                self.agent_name,
                "migrate_data",
                error_code="DATABASE_ERROR"
            )
    
    # === BACKUP Y RESTORE ===
    
    async def _backup_restore(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Realizar backup/restore de base de datos"""
        operation = request.get("backup_operation")
        
        if operation == "backup":
            return await self._create_backup(request.get("backup_path"))
        elif operation == "restore":
            return await self._restore_backup(request.get("backup_path"))
        elif operation == "list_backups":
            return await self._list_backups(request.get("backup_directory", "."))
        else:
            raise AgentException(
                f"Operación de backup no soportada: {operation}",
                self.agent_name,
                "backup_restore",
                error_code="INVALID_REQUEST"
            )
    
    async def _create_backup(self, backup_path: Optional[str] = None) -> Dict[str, Any]:
        """Crear backup usando pg_dump"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backup_{timestamp}.sql"
        
        try:
            # Comando pg_dump
            cmd = [
                "pg_dump",
                "-h", self.db_config.host,
                "-p", str(self.db_config.port),
                "-U", self.db_config.user,
                "-d", self.db_config.database,
                "-f", backup_path,
                "--verbose"
            ]
            
            # Configurar variables de entorno
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_config.password
            
            start_time = time.time()
            process = subprocess.run(cmd, env=env, capture_output=True, text=True)
            backup_time = time.time() - start_time
            
            if process.returncode != 0:
                raise Exception(f"pg_dump falló: {process.stderr}")
            
            return {
                "success": True,
                "backup_path": backup_path,
                "backup_time_seconds": backup_time,
                "size_bytes": os.path.getsize(backup_path) if os.path.exists(backup_path) else 0,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "command": " ".join(cmd)
                }
            }
            
        except Exception as e:
            raise AgentException(
                f"Error creando backup: {str(e)}",
                self.agent_name,
                "create_backup",
                error_code="DATABASE_ERROR"
            )
    
    async def _restore_backup(self, backup_path: str) -> Dict[str, Any]:
        """Restaurar backup usando psql"""
        if not os.path.exists(backup_path):
            raise AgentException(
                f"Archivo de backup no encontrado: {backup_path}",
                self.agent_name,
                "restore_backup",
                error_code="NOT_FOUND"
            )
        
        try:
            # Comando psql para restore
            cmd = [
                "psql",
                "-h", self.db_config.host,
                "-p", str(self.db_config.port),
                "-U", self.db_config.user,
                "-d", self.db_config.database,
                "-f", backup_path,
                "--verbose"
            ]
            
            # Configurar variables de entorno
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_config.password
            
            start_time = time.time()
            process = subprocess.run(cmd, env=env, capture_output=True, text=True)
            restore_time = time.time() - start_time
            
            if process.returncode != 0:
                raise Exception(f"psql falló: {process.stderr}")
            
            return {
                "success": True,
                "backup_path": backup_path,
                "restore_time_seconds": restore_time,
                "output": process.stdout,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "command": " ".join(cmd)
                }
            }
            
        except Exception as e:
            raise AgentException(
                f"Error restaurando backup: {str(e)}",
                self.agent_name,
                "restore_backup",
                error_code="DATABASE_ERROR"
            )
    
    async def _list_backups(self, backup_directory: str) -> Dict[str, Any]:
        """Listar archivos de backup disponibles"""
        try:
            if not os.path.exists(backup_directory):
                return {"success": True, "backups": []}
            
            backup_files = []
            for file in os.listdir(backup_directory):
                if file.endswith(('.sql', '.dump', '.backup')):
                    file_path = os.path.join(backup_directory, file)
                    stat = os.stat(file_path)
                    
                    backup_files.append({
                        "filename": file,
                        "path": file_path,
                        "size_bytes": stat.st_size,
                        "created_timestamp": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified_timestamp": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            # Ordenar por fecha de creación
            backup_files.sort(key=lambda x: x["created_timestamp"], reverse=True)
            
            return {
                "success": True,
                "backup_directory": backup_directory,
                "backups": backup_files,
                "metadata": {
                    "total_backups": len(backup_files),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            raise AgentException(
                f"Error listando backups: {str(e)}",
                self.agent_name,
                "list_backups",
                error_code="DATABASE_ERROR"
            )
    
    # === OPTIMIZACIÓN DE PERFORMANCE ===
    
    async def _optimize_performance(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Optimizar performance de base de datos"""
        optimization_type = request.get("optimization_type")
        
        if optimization_type == "analyze":
            return await self._analyze_performance()
        elif optimization_type == "reindex":
            return await self._reindex_database()
        elif optimization_type == "vacuum":
            return await self._vacuum_database()
        elif optimization_type == "update_stats":
            return await self._update_statistics()
        else:
            # Análisis completo de performance
            return await self._full_performance_analysis()
    
    async def _analyze_performance(self) -> Dict[str, Any]:
        """Analizar performance actual"""
        try:
            with self.engine.connect() as conn:
                # Obtener métricas de performance
                queries = [
                    ("active_connections", text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")),
                    ("total_connections", text("SELECT count(*) FROM pg_stat_activity")),
                    ("cache_hit_ratio", text("SELECT round(100.0 * sum(blks_hit) / (sum(blks_hit) + sum(blks_read)), 2) FROM pg_stat_database")),
                    ("slow_queries", text("SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 5"))
                ]
                
                results = {}
                for name, query in queries:
                    try:
                        result = conn.execute(query)
                        results[name] = result.fetchall()
                    except Exception as e:
                        results[name] = {"error": str(e)}
                
                # Obtener tamaños de tablas
                tables_query = text("""
                    SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                    FROM pg_tables 
                    WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC 
                    LIMIT 20
                """)
                
                table_sizes = conn.execute(tables_query).fetchall()
                
                return {
                    "success": True,
                    "performance_metrics": {
                        "active_connections": results["active_connections"][0][0] if results["active_connections"] else 0,
                        "total_connections": results["total_connections"][0][0] if results["total_connections"] else 0,
                        "cache_hit_ratio": float(results["cache_hit_ratio"][0][0]) if results["cache_hit_ratio"] else 0.0,
                        "slow_queries": results["slow_queries"]
                    },
                    "table_sizes": [{"table": f"{row[0]}.{row[1]}", "size": row[2]} for row in table_sizes],
                    "metadata": {
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
        except Exception as e:
            raise AgentException(
                f"Error analizando performance: {str(e)}",
                self.agent_name,
                "analyze_performance",
                error_code="DATABASE_ERROR"
            )
    
    async def _reindex_database(self) -> Dict[str, Any]:
        """Reindexar base de datos"""
        try:
            start_time = time.time()
            
            with self.engine.connect() as conn:
                # Reindexar todas las tablas
                conn.execute(text("REINDEX DATABASE postgres"))
                conn.commit()
            
            reindex_time = time.time() - start_time
            
            return {
                "success": True,
                "operation": "reindex_database",
                "execution_time_seconds": reindex_time,
                "metadata": {
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            raise AgentException(
                f"Error reindexando: {str(e)}",
                self.agent_name,
                "reindex_database",
                error_code="DATABASE_ERROR"
            )
    
    async def _vacuum_database(self) -> Dict[str, Any]:
        """Ejecutar VACUUM en la base de datos"""
        try:
            start_time = time.time()
            
            with self.engine.connect() as conn:
                conn.execute(text("VACUUM ANALYZE"))
                conn.commit()
            
            vacuum_time = time.time() - start_time
            
            return {
                "success": True,
                "operation": "vacuum_database",
                "execution_time_seconds": vacuum_time,
                "metadata": {
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            raise AgentException(
                f"Error ejecutando VACUUM: {str(e)}",
                self.agent_name,
                "vacuum_database",
                error_code="DATABASE_ERROR"
            )
    
    async def _update_statistics(self) -> Dict[str, Any]:
        """Actualizar estadísticas de la base de datos"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("ANALYZE"))
                conn.commit()
            
            return {
                "success": True,
                "operation": "update_statistics",
                "metadata": {
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            raise AgentException(
                f"Error actualizando estadísticas: {str(e)}",
                self.agent_name,
                "update_statistics",
                error_code="DATABASE_ERROR"
            )
    
    async def _full_performance_analysis(self) -> Dict[str, Any]:
        """Análisis completo de performance"""
        results = {}
        
        # Ejecutar todas las verificaciones
        try:
            analysis_types = [
                ("performance", self._analyze_performance),
                ("index_usage", self._get_index_usage),
                ("query_performance", self._get_query_performance),
                ("connection_stats", self._get_connection_stats)
            ]
            
            for analysis_name, analysis_func in analysis_types:
                try:
                    result = await analysis_func()
                    results[analysis_name] = result
                except Exception as e:
                    results[analysis_name] = {"error": str(e)}
            
            # Recomendaciones basadas en análisis
            recommendations = self._generate_performance_recommendations(results)
            
            return {
                "success": True,
                "analysis_results": results,
                "recommendations": recommendations,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "analysis_type": "full"
                }
            }
            
        except Exception as e:
            raise AgentException(
                f"Error en análisis completo: {str(e)}",
                self.agent_name,
                "full_performance_analysis",
                error_code="DATABASE_ERROR"
            )
    
    async def _get_index_usage(self) -> Dict[str, Any]:
        """Obtener uso de índices"""
        try:
            with self.engine.connect() as conn:
                query = text("""
                    SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
                    FROM pg_stat_user_indexes
                    ORDER BY idx_tup_read DESC
                """)
                
                results = conn.execute(query).fetchall()
                
                return {
                    "success": True,
                    "index_usage": [
                        {
                            "schema": row[0],
                            "table": row[1],
                            "index": row[2],
                            "reads": row[3],
                            "fetches": row[4]
                        } for row in results
                    ]
                }
                
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_query_performance(self) -> Dict[str, Any]:
        """Obtener performance de consultas"""
        try:
            with self.engine.connect() as conn:
                query = text("""
                    SELECT query, calls, total_time, mean_time, stddev_time
                    FROM pg_stat_statements
                    ORDER BY total_time DESC
                    LIMIT 10
                """)
                
                results = conn.execute(query).fetchall()
                
                return {
                    "success": True,
                    "query_performance": [
                        {
                            "query": row[0][:100] + "..." if len(row[0]) > 100 else row[0],
                            "calls": row[1],
                            "total_time_ms": row[2],
                            "mean_time_ms": row[3],
                            "stddev_time_ms": row[4]
                        } for row in results
                    ]
                }
                
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_connection_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de conexiones"""
        try:
            with self.engine.connect() as conn:
                query = text("""
                    SELECT state, count(*)
                    FROM pg_stat_activity
                    GROUP BY state
                """)
                
                results = conn.execute(query).fetchall()
                
                return {
                    "success": True,
                    "connection_stats": {
                        state: count for state, count in results
                    }
                }
                
        except Exception as e:
            return {"error": str(e)}
    
    def _generate_performance_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generar recomendaciones de performance"""
        recommendations = []
        
        try:
            perf_data = analysis_results.get("performance", {}).get("performance_metrics", {})
            
            # Recomendaciones basadas en cache hit ratio
            cache_hit_ratio = perf_data.get("cache_hit_ratio", 0)
            if cache_hit_ratio < 90:
                recommendations.append("Cache hit ratio bajo - considerar aumentar shared_buffers")
            
            # Recomendaciones basadas en conexiones activas
            active_connections = perf_data.get("active_connections", 0)
            if active_connections > self.db_config.pool_size * 0.8:
                recommendations.append("Alto número de conexiones activas - considerar aumentar pool_size")
            
            # Recomendaciones basadas en consultas lentas
            slow_queries = perf_data.get("slow_queries", [])
            if slow_queries and len(slow_queries) > 0:
                recommendations.append("Se detectaron consultas lentas - revisar y optimizar índices")
            
        except Exception:
            recommendations.append("Error generando recomendaciones específicas")
        
        if not recommendations:
            recommendations.append("Performance de base de datos dentro de parámetros normales")
        
        return recommendations
    
    # === GESTIÓN DE POOL DE CONEXIONES ===
    
    async def _manage_pool(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Gestionar pool de conexiones"""
        operation = request.get("pool_operation")
        
        if operation == "status":
            return await self._get_pool_status()
        elif operation == "metrics":
            return await self._get_pool_metrics()
        elif operation == "clear":
            return await self._clear_pool()
        else:
            raise AgentException(
                f"Operación de pool no soportada: {operation}",
                self.agent_name,
                "manage_pool",
                error_code="INVALID_REQUEST"
            )
    
    async def _get_pool_status(self) -> Dict[str, Any]:
        """Obtener estado del pool de conexiones"""
        pool = self.engine.pool
        
        return {
            "success": True,
            "pool_status": self.connection_pool_status.value,
            "pool_metrics": {
                "total_connections": pool.size(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
                "max_overflow": self.db_config.max_overflow,
                "pool_size": self.db_config.pool_size
            },
            "metadata": {
                "timestamp": datetime.now().isoformat()
            }
        }
    
    async def _get_pool_metrics(self) -> Dict[str, Any]:
        """Obtener métricas detalladas del pool"""
        pool = self.engine.pool
        
        return {
            "success": True,
            "pool_metrics": {
                "size": pool.size(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
                "status": self.connection_pool_status.value
            },
            "agent_metrics": self.query_metrics.copy(),
            "metadata": {
                "timestamp": datetime.now().isoformat()
            }
        }
    
    async def _clear_pool(self) -> Dict[str, Any]:
        """Limpiar todas las conexiones del pool"""
        try:
            self.engine.pool.dispose()
            
            # Recrear pool
            self.engine = create_engine(
                self.db_config.database_url,
                poolclass=QueuePool,
                pool_size=self.db_config.pool_size,
                max_overflow=self.db_config.max_overflow,
                pool_timeout=self.db_config.pool_timeout,
                pool_recycle=self.db_config.pool_recycle,
                echo=False,
                future=True
            )
            
            self.session_factory = sessionmaker(bind=self.engine)
            
            self.connection_pool_status = ConnectionPoolStatus.HEALTHY
            
            return {
                "success": True,
                "operation": "clear_pool",
                "metadata": {
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            self.connection_pool_status = ConnectionPoolStatus.OFFLINE
            raise AgentException(
                f"Error limpiando pool: {str(e)}",
                self.agent_name,
                "clear_pool",
                error_code="DATABASE_ERROR"
            )
    
    # === GESTIÓN DE ÍNDICES ===
    
    async def _manage_indexes(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Gestionar índices de base de datos"""
        operation = request.get("index_operation")
        
        if operation == "list":
            return await self._list_indexes()
        elif operation == "create":
            return await self._create_index(request.get("index_spec"))
        elif operation == "drop":
            return await self._drop_index(request.get("index_name"))
        elif operation == "analyze":
            return await self._analyze_index_usage()
        elif operation == "optimize":
            return await self._optimize_indexes()
        else:
            raise AgentException(
                f"Operación de índice no soportada: {operation}",
                self.agent_name,
                "manage_indexes",
                error_code="INVALID_REQUEST"
            )
    
    async def _list_indexes(self) -> Dict[str, Any]:
        """Listar todos los índices"""
        try:
            with self.engine.connect() as conn:
                query = text("""
                    SELECT schemaname, tablename, indexname, indexdef
                    FROM pg_indexes
                    WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                    ORDER BY schemaname, tablename, indexname
                """)
                
                results = conn.execute(query).fetchall()
                
                indexes = []
                for row in results:
                    indexes.append({
                        "schema": row[0],
                        "table": row[1],
                        "index_name": row[2],
                        "definition": row[3]
                    })
                
                return {
                    "success": True,
                    "indexes": indexes,
                    "metadata": {
                        "total_indexes": len(indexes),
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
        except Exception as e:
            raise AgentException(
                f"Error listando índices: {str(e)}",
                self.agent_name,
                "list_indexes",
                error_code="DATABASE_ERROR"
            )
    
    async def _create_index(self, index_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Crear nuevo índice"""
        index_name = index_spec.get("index_name")
        table_name = index_spec.get("table_name")
        columns = index_spec.get("columns", [])
        index_type = index_spec.get("index_type", "BTREE")
        
        if not index_name or not table_name or not columns:
            raise AgentException(
                "index_name, table_name y columns son requeridos",
                self.agent_name,
                "create_index",
                error_code="INVALID_REQUEST"
            )
        
        try:
            columns_str = ", ".join(columns)
            create_sql = f"CREATE INDEX {index_name} ON {table_name} USING {index_type} ({columns_str})"
            
            with self.engine.connect() as conn:
                conn.execute(text(create_sql))
                conn.commit()
            
            return {
                "success": True,
                "index_name": index_name,
                "sql": create_sql,
                "metadata": {
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            raise AgentException(
                f"Error creando índice: {str(e)}",
                self.agent_name,
                "create_index",
                error_code="DATABASE_ERROR"
            )
    
    async def _drop_index(self, index_name: str) -> Dict[str, Any]:
        """Eliminar índice"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
                conn.commit()
            
            return {
                "success": True,
                "index_name": index_name,
                "metadata": {
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            raise AgentException(
                f"Error eliminando índice {index_name}: {str(e)}",
                self.agent_name,
                "drop_index",
                error_code="DATABASE_ERROR"
            )
    
    async def _analyze_index_usage(self) -> Dict[str, Any]:
        """Analizar uso de índices"""
        try:
            with self.engine.connect() as conn:
                query = text("""
                    SELECT 
                        schemaname, tablename, indexname,
                        idx_tup_read, idx_tup_fetch,
                        idx_scan,
                        CASE WHEN idx_scan = 0 THEN 'unused' ELSE 'used' END as usage_status
                    FROM pg_stat_user_indexes
                    ORDER BY idx_scan DESC
                """)
                
                results = conn.execute(query).fetchall()
                
                index_analysis = []
                for row in results:
                    index_analysis.append({
                        "schema": row[0],
                        "table": row[1],
                        "index_name": row[2],
                        "reads": row[3],
                        "fetches": row[4],
                        "scans": row[5],
                        "usage_status": row[6]
                    })
                
                # Identificar índices no utilizados
                unused_indexes = [idx for idx in index_analysis if idx["usage_status"] == "unused"]
                
                return {
                    "success": True,
                    "index_analysis": index_analysis,
                    "unused_indexes": unused_indexes,
                    "recommendations": [
                        f"Índice {idx['schema']}.{idx['table']}.{idx['index_name']} no está siendo utilizado" 
                        for idx in unused_indexes
                    ],
                    "metadata": {
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
        except Exception as e:
            raise AgentException(
                f"Error analizando índices: {str(e)}",
                self.agent_name,
                "analyze_index_usage",
                error_code="DATABASE_ERROR"
            )
    
    async def _optimize_indexes(self) -> Dict[str, Any]:
        """Optimizar índices"""
        try:
            start_time = time.time()
            
            with self.engine.connect() as conn:
                # Reindexar todas las tablas de usuario
                conn.execute(text("REINDEX DATABASE postgres"))
                conn.commit()
            
            optimize_time = time.time() - start_time
            
            return {
                "success": True,
                "operation": "optimize_indexes",
                "execution_time_seconds": optimize_time,
                "metadata": {
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            raise AgentException(
                f"Error optimizando índices: {str(e)}",
                self.agent_name,
                "optimize_indexes",
                error_code="DATABASE_ERROR"
            )
    
    # === MONITOREO ===
    
    async def _monitor_database(self, request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Monitorear estado de base de datos"""
        monitor_type = request.get("monitor_type", "full")
        
        if monitor_type == "health":
            return await self._health_check()
        elif monitor_type == "performance":
            return await self._monitor_performance()
        elif monitor_type == "connections":
            return await self._monitor_connections()
        else:
            return await self._full_monitoring()
    
    async def _health_check(self) -> Dict[str, Any]:
        """Verificar salud de base de datos"""
        try:
            start_time = time.time()
            
            with self.engine.connect() as conn:
                # Test básico de conexión
                conn.execute(text("SELECT 1"))
                
                # Verificar espacio en disco
                disk_usage = conn.execute(text("""
                    SELECT pg_database_size(current_database()) as database_size
                """)).fetchone()
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "health_status": "healthy",
                "response_time_ms": response_time,
                "database_size": disk_usage[0] if disk_usage else 0,
                "pool_status": self.connection_pool_status.value,
                "metadata": {
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "health_status": "unhealthy",
                "error": str(e),
                "pool_status": ConnectionPoolStatus.OFFLINE.value,
                "metadata": {
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    async def _monitor_performance(self) -> Dict[str, Any]:
        """Monitorear performance de base de datos"""
        try:
            with self.engine.connect() as conn:
                queries = [
                    ("active_connections", text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")),
                    ("cache_hit_ratio", text("SELECT round(100.0 * sum(blks_hit) / (sum(blks_hit) + sum(blks_read)), 2) FROM pg_stat_database")),
                    ("database_size", text("SELECT pg_database_size(current_database())")),
                    ("table_count", text("SELECT count(*) FROM pg_tables WHERE schemaname = 'public'"))
                ]
                
                results = {}
                for name, query in queries:
                    try:
                        result = conn.execute(query)
                        results[name] = result.fetchone()[0]
                    except:
                        results[name] = 0
            
            return {
                "success": True,
                "performance_metrics": {
                    "active_connections": results.get("active_connections", 0),
                    "cache_hit_ratio": results.get("cache_hit_ratio", 0.0),
                    "database_size_bytes": results.get("database_size", 0),
                    "database_size_human": self._format_bytes(results.get("database_size", 0)),
                    "table_count": results.get("table_count", 0)
                },
                "pool_status": self.connection_pool_status.value,
                "metadata": {
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            raise AgentException(
                f"Error monitoreando performance: {str(e)}",
                self.agent_name,
                "monitor_performance",
                error_code="DATABASE_ERROR"
            )
    
    async def _monitor_connections(self) -> Dict[str, Any]:
        """Monitorear conexiones de base de datos"""
        try:
            with self.engine.connect() as conn:
                # Estadísticas de conexiones
                conn_stats = conn.execute(text("""
                    SELECT state, count(*) as count
                    FROM pg_stat_activity
                    GROUP BY state
                """)).fetchall()
                
                # Procesos por usuario
                user_stats = conn.execute(text("""
                    SELECT usename, count(*) as count
                    FROM pg_stat_activity
                    GROUP BY usename
                    ORDER BY count DESC
                """)).fetchall()
                
                # Pool metrics
                pool = self.engine.pool
                
                return {
                    "success": True,
                    "connection_statistics": {
                        state: count for state, count in conn_stats
                    },
                    "user_statistics": {
                        user: count for user, count in user_stats
                    },
                    "pool_statistics": {
                        "pool_size": pool.size(),
                        "checked_out": pool.checkedout(),
                        "overflow": pool.overflow(),
                        "status": self.connection_pool_status.value
                    },
                    "metadata": {
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
        except Exception as e:
            raise AgentException(
                f"Error monitoreando conexiones: {str(e)}",
                self.agent_name,
                "monitor_connections",
                error_code="DATABASE_ERROR"
            )
    
    async def _full_monitoring(self) -> Dict[str, Any]:
        """Monitoreo completo de base de datos"""
        results = {}
        
        try:
            monitor_types = [
                ("health", self._health_check),
                ("performance", self._monitor_performance),
                ("connections", self._monitor_connections),
                ("indexes", self._analyze_index_usage)
            ]
            
            for monitor_name, monitor_func in monitor_types:
                try:
                    result = await monitor_func()
                    results[monitor_name] = result
                except Exception as e:
                    results[monitor_name] = {"error": str(e)}
            
            # Agregar métricas del agente
            results["agent_metrics"] = {
                "query_metrics": self.query_metrics.copy(),
                "agent_status": self.get_status()
            }
            
            return {
                "success": True,
                "monitoring_results": results,
                "overall_status": "healthy" if all(
                    r.get("success", False) for r in results.values() if isinstance(r, dict)
                ) else "degraded",
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "monitoring_type": "full"
                }
            }
            
        except Exception as e:
            raise AgentException(
                f"Error en monitoreo completo: {str(e)}",
                self.agent_name,
                "full_monitoring",
                error_code="DATABASE_ERROR"
            )
    
    # === MÉTODOS AUXILIARES ===
    
    def _update_query_metrics(self, execution_time_ms: float, success: bool) -> None:
        """Actualizar métricas de consultas"""
        self.query_metrics["total_queries"] += 1
        
        if success:
            self.query_metrics["successful_queries"] += 1
            
            # Actualizar tiempo promedio
            total_time = (self.query_metrics["avg_execution_time_ms"] * 
                         (self.query_metrics["successful_queries"] - 1) + execution_time_ms)
            self.query_metrics["avg_execution_time_ms"] = (
                total_time / self.query_metrics["successful_queries"]
            )
            
            # Identificar consultas lentas (> 1000ms)
            if execution_time_ms > 1000:
                self.query_metrics["slow_queries"].append({
                    "timestamp": datetime.now().isoformat(),
                    "execution_time_ms": execution_time_ms
                })
                
                # Mantener solo las últimas 10 consultas lentas
                if len(self.query_metrics["slow_queries"]) > 10:
                    self.query_metrics["slow_queries"] = self.query_metrics["slow_queries"][-10:]
        else:
            self.query_metrics["failed_queries"] += 1
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Formatear bytes en formato legible"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Obtener métricas de performance actuales"""
        try:
            with self.engine.connect() as conn:
                # Obtener métricas básicas
                active_connections = conn.execute(text(
                    "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
                )).fetchone()[0]
                
                total_connections = conn.execute(text(
                    "SELECT count(*) FROM pg_stat_activity"
                )).fetchone()[0]
                
                cache_hit_ratio = conn.execute(text(
                    "SELECT round(100.0 * sum(blks_hit) / (sum(blks_hit) + sum(blks_read)), 2) FROM pg_stat_database"
                )).fetchone()[0] or 0.0
                
                # Obtener tamaños de tablas
                table_sizes = conn.execute(text("""
                    SELECT tablename, pg_total_relation_size('public.'||tablename) as size
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY size DESC
                    LIMIT 10
                """)).fetchall()
                
                return PerformanceMetrics(
                    active_connections=active_connections,
                    total_connections=total_connections,
                    cache_hit_ratio=float(cache_hit_ratio),
                    query_avg_time_ms=self.query_metrics["avg_execution_time_ms"],
                    slow_queries_count=len(self.query_metrics["slow_queries"]),
                    table_sizes={table: size for table, size in table_sizes},
                    index_usage={}
                )
                
        except Exception as e:
            self.logger.error(f"Error obteniendo métricas de performance: {e}")
            return PerformanceMetrics(
                active_connections=0,
                total_connections=0,
                cache_hit_ratio=0.0,
                query_avg_time_ms=0.0,
                slow_queries_count=0,
                table_sizes={}
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check del Database Operations Agent"""
        try:
            await self.ensure_initialized()
            
            # Test de conexión
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Verificar estado del pool
            pool_status = await self._check_pool_status()
            
            health_status = {
                "agent_name": self.agent_name,
                "status": "healthy" if pool_status != ConnectionPoolStatus.OFFLINE else "unhealthy",
                "database_connection": "active",
                "pool_status": pool_status.value,
                "is_ready": self.is_ready,
                "is_busy": self.is_busy,
                "utilization": self.utilization,
                "last_activity": self.last_activity.isoformat(),
                "query_metrics": self.query_metrics.copy(),
                "database_config": {
                    "host": self.db_config.host,
                    "port": self.db_config.port,
                    "database": self.db_config.database,
                    "pool_size": self.db_config.pool_size
                }
            }
            
            return health_status
            
        except Exception as e:
            self.connection_pool_status = ConnectionPoolStatus.OFFLINE
            return {
                "agent_name": self.agent_name,
                "status": "unhealthy",
                "database_connection": "failed",
                "error": str(e),
                "pool_status": ConnectionPoolStatus.OFFLINE.value
            }
    
    def __str__(self) -> str:
        return f"DatabaseOperationsAgent(status={self.connection_pool_status.value}, queries={self.query_metrics['total_queries']})"
    
    def __repr__(self) -> str:
        return (
            f"DatabaseOperationsAgent("
            f"agent_name='{self.agent_name}', "
            f"pool_status='{self.connection_pool_status.value}', "
            f"total_queries={self.query_metrics['total_queries']}, "
            f"vector_searches={self.query_metrics['vector_searches']}, "
            f"success_rate={self.query_metrics['successful_queries'] / max(self.query_metrics['total_queries'], 1):.2%}"
            f")"
        )