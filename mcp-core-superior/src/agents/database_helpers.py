"""
Database Operations Agent Helpers
Utilidades y funciones auxiliares para operaciones de base de datos PostgreSQL + pgvector
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import json
import logging
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass
from enum import Enum

# Importaciones del agente principal
from .database_operations_agent import (
    DatabaseOperationsAgentWrapper,
    DatabaseConnectionConfig,
    PerformanceMetrics,
    ConnectionPoolStatus
)


class SQLQueryType(Enum):
    """Tipos de consultas SQL"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    DROP = "DROP"
    ALTER = "ALTER"
    TRUNCATE = "TRUNCATE"


class IndexType(Enum):
    """Tipos de índices PostgreSQL"""
    BTREE = "BTREE"
    HASH = "HASH"
    GIST = "GIST"
    GIN = "GIN"
    BRIN = "BRIN"
    IVFFLAT = "IVFFLAT"  # Para pgvector


@dataclass
class TableInfo:
    """Información de tabla"""
    table_name: str
    schema: str
    columns: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]]
    row_count: Optional[int] = None
    size_bytes: Optional[int] = None


@dataclass
class IndexInfo:
    """Información de índice"""
    index_name: str
    table_name: str
    schema: str
    index_type: str
    columns: List[str]
    unique: bool
    size_bytes: Optional[int] = None
    usage_stats: Optional[Dict[str, int]] = None


@dataclass
class QueryPlan:
    """Plan de ejecución de consulta"""
    query: str
    plan: List[Dict[str, Any]]
    execution_time_ms: float
    cost_estimate: float
    rows_returned: int


class DatabaseHelpers:
    """Clase de utilidades para Database Operations Agent"""
    
    def __init__(self, agent: DatabaseOperationsAgentWrapper):
        self.agent = agent
        self.logger = logging.getLogger(f"{__name__}.helpers")
    
    # === UTILIDADES DE CONSULTAS SQL ===
    
    def detect_query_type(self, query: str) -> SQLQueryType:
        """Detectar tipo de consulta SQL"""
        query_clean = query.strip().upper()
        
        for query_type in SQLQueryType:
            if query_clean.startswith(query_type.value):
                return query_type
        
        return SQLQueryType.SELECT  # Default
    
    def sanitize_sql_query(self, query: str) -> str:
        """Sanitizar consulta SQL básica"""
        # Remover comentarios
        lines = query.split('\n')
        clean_lines = []
        
        for line in lines:
            # Remover comentarios de línea
            if '--' in line:
                line = line[:line.index('--')]
            clean_lines.append(line.strip())
        
        return '\n'.join(clean_lines)
    
    def build_paginated_query(
        self,
        base_query: str,
        order_by: str,
        limit: int = 100,
        offset: int = 0
    ) -> str:
        """Construir consulta paginada"""
        safe_limit = max(1, min(limit, 1000))  # Límite máximo
        safe_offset = max(0, offset)
        
        # Agregar ORDER BY si no existe
        if "ORDER BY" not in base_query.upper():
            query = f"{base_query.rstrip(';')} ORDER BY {order_by}"
        else:
            query = base_query.rstrip(';')
        
        return f"{query} LIMIT {safe_limit} OFFSET {safe_offset}"
    
    def build_insert_query(
        self,
        table_name: str,
        data: Dict[str, Any],
        on_conflict: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Construir consulta INSERT segura"""
        columns = list(data.keys())
        placeholders = [f":{col}" for col in columns]
        
        query = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        """
        
        if on_conflict:
            query += f" ON CONFLICT {on_conflict}"
        
        return query, data
    
    def build_bulk_insert_query(
        self,
        table_name: str,
        data_list: List[Dict[str, Any]],
        on_conflict: Optional[str] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Construir consulta INSERT masiva"""
        if not data_list:
            raise ValueError("Lista de datos vacía")
        
        # Obtener columnas del primer registro
        columns = list(data_list[0].keys())
        
        # Crear placeholders para cada registro
        value_rows = []
        all_params = []
        
        for i, data in enumerate(data_list):
            if set(data.keys()) != set(columns):
                raise ValueError("Todos los registros deben tener las mismas columnas")
            
            placeholders = [f":{col}_{i}" for col in columns]
            value_rows.append(f"({', '.join(placeholders)})")
            
            # Agregar parámetros con sufijo de índice
            row_params = {f"{col}_{i}": data[col] for col in columns}
            all_params.append(row_params)
        
        # Combinar parámetros
        combined_params = {}
        for params in all_params:
            combined_params.update(params)
        
        query = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES {', '.join(value_rows)}
        """
        
        if on_conflict:
            query += f" ON CONFLICT {on_conflict}"
        
        return query, combined_params
    
    # === UTILIDADES DE BÚSQUEDA VECTORIAL ===
    
    def normalize_embedding(self, embedding: List[float]) -> List[float]:
        """Normalizar vector de embedding"""
        if not embedding:
            return []
        
        # Calcular norma
        import math
        norm = math.sqrt(sum(x * x for x in embedding))
        
        if norm == 0:
            return embedding
        
        # Normalizar
        return [x / norm for x in embedding]
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcular similitud coseno entre dos vectores"""
        if len(vec1) != len(vec2):
            raise ValueError("Los vectores deben tener la misma dimensión")
        
        import math
        
        # Calcular producto punto
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Calcular normas
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def distance_to_similarity(self, distance: float) -> float:
        """Convertir distancia euclidiana a similitud"""
        # Asumiendo distancia máxima de 2.0 para vectores normalizados
        max_distance = 2.0
        return max(0.0, 1.0 - (distance / max_distance))
    
    def build_vector_search_query(
        self,
        table_name: str,
        embedding_column: str = "embedding",
        additional_filters: Optional[str] = None
    ) -> str:
        """Construir consulta de búsqueda vectorial"""
        base_query = f"""
        SELECT *, ({embedding_column} <-> :query_embedding::vector) as distance
        FROM {table_name}
        WHERE {embedding_column} IS NOT NULL
        """
        
        if additional_filters:
            base_query += f" AND {additional_filters}"
        
        base_query += """
        ORDER BY {embedding_column} <-> :query_embedding::vector
        LIMIT :limit
        """
        
        return base_query
    
    # === UTILIDADES DE ESQUEMAS ===
    
    def build_create_table_sql(
        self,
        table_name: str,
        columns: List[Dict[str, Any]],
        if_not_exists: bool = True
    ) -> str:
        """Construir SQL para crear tabla"""
        column_defs = []
        
        for col in columns:
            col_def = f"{col['name']} {col['type']}"
            
            if not col.get('nullable', True):
                col_def += " NOT NULL"
            
            if col.get('primary_key'):
                col_def += " PRIMARY KEY"
            
            if col.get('unique'):
                col_def += " UNIQUE"
            
            if col.get('default') is not None:
                col_def += f" DEFAULT {col['default']}"
            
            column_defs.append(col_def)
        
        exists_clause = "IF NOT EXISTS " if if_not_exists else ""
        
        return f"CREATE TABLE {exists_clause}{table_name} ({', '.join(column_defs)})"
    
    def build_alter_table_sql(
        self,
        table_name: str,
        actions: List[Dict[str, Any]]
    ) -> List[str]:
        """Construir SQLs para ALTER TABLE"""
        sql_statements = []
        
        for action in actions:
            action_type = action.get('type')
            
            if action_type == 'add_column':
                col_def = f"{action['name']} {action['type']}"
                if not action.get('nullable', True):
                    col_def += " NOT NULL"
                sql_statements.append(f"ALTER TABLE {table_name} ADD COLUMN {col_def}")
            
            elif action_type == 'drop_column':
                sql_statements.append(f"ALTER TABLE {table_name} DROP COLUMN {action['name']}")
            
            elif action_type == 'alter_column':
                sql_statements.append(f"ALTER TABLE {table_name} ALTER COLUMN {action['name']} {action['definition']}")
            
            elif action_type == 'add_constraint':
                sql_statements.append(f"ALTER TABLE {table_name} ADD CONSTRAINT {action['name']} {action['definition']}")
        
        return sql_statements
    
    def build_create_index_sql(
        self,
        index_name: str,
        table_name: str,
        columns: List[str],
        index_type: IndexType = IndexType.BTREE,
        unique: bool = False,
        if_not_exists: bool = True
    ) -> str:
        """Construir SQL para crear índice"""
        exists_clause = "IF NOT EXISTS " if if_not_exists else ""
        columns_str = ", ".join(columns)
        
        unique_clause = "UNIQUE " if unique else ""
        
        return f"CREATE {unique_clause}INDEX {exists_clause}{index_name} ON {table_name} USING {index_type.value} ({columns_str})"
    
    # === UTILIDADES DE PERFORMANCE ===
    
    async def analyze_query_performance(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> QueryPlan:
        """Analizar performance de una consulta usando EXPLAIN"""
        explain_query = f"EXPLAIN ANALYZE {query}"
        
        start_time = datetime.now()
        
        try:
            result = await self.agent.process_request({
                "operation_type": "sql_query",
                "query": explain_query,
                "parameters": parameters or {}
            })
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return QueryPlan(
                query=query,
                plan=result.get('data', []),
                execution_time_ms=execution_time,
                cost_estimate=0.0,  # Se puede extraer del plan
                rows_returned=result.get('rows_affected', 0)
            )
            
        except Exception as e:
            self.logger.error(f"Error analizando performance de consulta: {e}")
            raise
    
    async def get_slow_queries(
        self,
        min_execution_time_ms: float = 1000.0
    ) -> List[Dict[str, Any]]:
        """Obtener consultas lentas del sistema"""
        try:
            result = await self.agent.process_request({
                "operation_type": "sql_query",
                "query": """
                SELECT query, calls, total_time, mean_time, stddev_time
                FROM pg_stat_statements
                WHERE mean_time > :min_time
                ORDER BY mean_time DESC
                LIMIT 20
                """,
                "parameters": {"min_time": min_execution_time_ms}
            })
            
            return result.get('data', [])
            
        except Exception as e:
            self.logger.error(f"Error obteniendo consultas lentas: {e}")
            return []
    
    async def get_database_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas generales de la base de datos"""
        stats_queries = {
            "database_size": "SELECT pg_database_size(current_database())",
            "table_count": "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'",
            "index_count": "SELECT count(*) FROM pg_indexes WHERE schemaname = 'public'",
            "active_connections": "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'",
            "cache_hit_ratio": "SELECT round(100.0 * sum(blks_hit) / (sum(blks_hit) + sum(blks_read)), 2) FROM pg_stat_database"
        }
        
        stats = {}
        
        for name, query in stats_queries.items():
            try:
                result = await self.agent.process_request({
                    "operation_type": "sql_query",
                    "query": query
                })
                
                if result.get('success') and result.get('data'):
                    stats[name] = result['data'][0]
                    
            except Exception as e:
                self.logger.warning(f"Error obteniendo estadística {name}: {e}")
                stats[name] = None
        
        return stats
    
    # === UTILIDADES DE BACKUP ===
    
    async def create_backup_with_timestamp(self, backup_dir: str = "./backups") -> str:
        """Crear backup con timestamp automático"""
        import os
        
        # Crear directorio si no existe
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.sql"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        result = await self.agent.process_request({
            "operation_type": "backup_restore",
            "backup_operation": "backup",
            "backup_path": backup_path
        })
        
        return result.get('backup_path', backup_path)
    
    async def get_backup_info(self, backup_path: str) -> Dict[str, Any]:
        """Obtener información de un archivo de backup"""
        import os
        
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Archivo de backup no encontrado: {backup_path}")
        
        stat = os.stat(backup_path)
        
        return {
            "file_path": backup_path,
            "file_size_bytes": stat.st_size,
            "file_size_human": self._format_bytes(stat.st_size),
            "created_timestamp": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_timestamp": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "exists": True
        }
    
    # === UTILIDADES DE MONITOREO ===
    
    async def get_comprehensive_health_check(self) -> Dict[str, Any]:
        """Verificación de salud completa del sistema"""
        health_checks = {}
        
        # Health check básico
        try:
            health = await self.agent.health_check()
            health_checks['basic'] = health
        except Exception as e:
            health_checks['basic'] = {'status': 'error', 'error': str(e)}
        
        # Métricas de performance
        try:
            perf_result = await self.agent.process_request({
                "operation_type": "monitoring",
                "monitor_type": "performance"
            })
            health_checks['performance'] = perf_result
        except Exception as e:
            health_checks['performance'] = {'error': str(e)}
        
        # Estado del pool
        try:
            pool_result = await self.agent.process_request({
                "operation_type": "connection_pool",
                "pool_operation": "status"
            })
            health_checks['pool'] = pool_result
        except Exception as e:
            health_checks['pool'] = {'error': str(e)}
        
        # Consolido resultado final
        overall_health = "healthy"
        issues = []
        
        if health_checks['basic'].get('status') != 'healthy':
            overall_health = "unhealthy"
            issues.append("Problemas básicos de conectividad")
        
        if health_checks.get('performance', {}).get('error'):
            overall_health = "degraded"
            issues.append("Problemas de performance")
        
        if health_checks.get('pool', {}).get('pool_metrics', {}).get('status') in ['degraded', 'critical']:
            overall_health = "degraded"
            issues.append("Problemas con pool de conexiones")
        
        return {
            "overall_status": overall_health,
            "health_checks": health_checks,
            "issues": issues,
            "timestamp": datetime.now().isoformat(),
            "recommendations": self._generate_health_recommendations(health_checks)
        }
    
    def _generate_health_recommendations(self, health_checks: Dict[str, Any]) -> List[str]:
        """Generar recomendaciones basadas en health checks"""
        recommendations = []
        
        # Recomendaciones de performance
        perf_data = health_checks.get('performance', {}).get('performance_metrics', {})
        cache_hit_ratio = perf_data.get('cache_hit_ratio', 0)
        
        if cache_hit_ratio < 95:
            recommendations.append(f"Cache hit ratio bajo ({cache_hit_ratio}%) - considerar aumentar shared_buffers")
        
        # Recomendaciones de pool
        pool_data = health_checks.get('pool', {}).get('pool_metrics', {})
        checked_out = pool_data.get('checked_out', 0)
        total = pool_data.get('total_connections', 0)
        
        if total > 0 and checked_out / total > 0.8:
            recommendations.append("Pool de conexiones cerca del límite - considerar aumentar pool_size")
        
        if not recommendations:
            recommendations.append("Sistema funcionando dentro de parámetros normales")
        
        return recommendations
    
    # === UTILIDADES GENERALES ===
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Formatear bytes en formato legible"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
    
    def validate_embedding_dimension(self, embedding: List[float], expected_dim: int = 1536) -> bool:
        """Validar dimensión de embedding"""
        return len(embedding) == expected_dim
    
    def create_safe_filename(self, name: str, extension: str = ".sql") -> str:
        """Crear nombre de archivo seguro"""
        import re
        
        # Remover caracteres no seguros
        safe_name = re.sub(r'[^\w\-_.]', '_', name)
        return f"{safe_name}{extension}"
    
    async def batch_process_queries(
        self,
        queries: List[Dict[str, Any]],
        batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        """Procesar consultas en lotes"""
        results = []
        
        for i in range(0, len(queries), batch_size):
            batch = queries[i:i + batch_size]
            
            # Procesar lote en paralelo
            tasks = []
            for query_data in batch:
                task = asyncio.create_task(
                    self.agent.process_request(query_data)
                )
                tasks.append(task)
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    results.append({"success": False, "error": str(result)})
                else:
                    results.append(result)
        
        return results


# === FUNCIONES DE CONVENIENCIA ===

async def create_database_agent(
    host: str = "localhost",
    port: int = 5432,
    database: str = "rag_database",
    user: str = "postgres",
    password: str = "password",
    **kwargs
) -> DatabaseOperationsAgentWrapper:
    """Crear y inicializar Database Operations Agent"""
    config = DatabaseConnectionConfig(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        **kwargs
    )
    
    agent = DatabaseOperationsAgentWrapper(config)
    await agent.ensure_initialized()
    
    return agent


async def quick_sql_query(
    query: str,
    parameters: Optional[Dict[str, Any]] = None,
    **db_config
) -> Dict[str, Any]:
    """Ejecutar consulta SQL rápida sin configuración manual"""
    agent = await create_database_agent(**db_config)
    
    try:
        return await agent.process_request({
            "operation_type": "sql_query",
            "query": query,
            "parameters": parameters or {}
        })
    finally:
        # Limpiar recursos
        agent.engine.dispose()


async def quick_vector_search(
    query_embedding: List[float],
    table_name: str,
    limit: int = 5,
    threshold: float = 0.7,
    **db_config
) -> Dict[str, Any]:
    """Búsqueda vectorial rápida"""
    agent = await create_database_agent(**db_config)
    
    try:
        return await agent.process_request({
            "operation_type": "vector_search",
            "query_embedding": query_embedding,
            "table_name": table_name,
            "limit": limit,
            "threshold": threshold
        })
    finally:
        agent.engine.dispose()


async def quick_health_check(**db_config) -> Dict[str, Any]:
    """Health check rápido del sistema"""
    agent = await create_database_agent(**db_config)
    
    try:
        return await agent.health_check()
    finally:
        agent.engine.dispose()


# === EJEMPLO DE USO ===

async def demo_database_helpers():
    """Demostración de uso de utilidades"""
    print("🚀 Demo de Database Helpers")
    
    # Crear agente
    agent = await create_database_agent()
    helpers = DatabaseHelpers(agent)
    
    # Ejemplo de consulta SQL
    query = "SELECT * FROM users WHERE created_at > $1"
    query_type = helpers.detect_query_type(query)
    print(f"Tipo de consulta: {query_type.value}")
    
    # Ejemplo de búsqueda vectorial
    embedding = [0.1] * 1536
    normalized = helpers.normalize_embedding(embedding)
    print(f"Embedding normalizado: {len(normalized)} dimensiones")
    
    # Ejemplo de estadísticas
    stats = await helpers.get_database_statistics()
    print(f"Estadísticas: {stats}")
    
    # Limpiar
    agent.engine.dispose()


if __name__ == "__main__":
    # Ejecutar demo
    asyncio.run(demo_database_helpers())