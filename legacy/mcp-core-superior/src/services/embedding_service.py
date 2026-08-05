"""
Servicio de Embeddings
"""
import logging
import numpy as np
import hashlib
from typing import List, Dict, Any
from datetime import datetime

from ..core.config import settings
from ..core.exceptions import MCPCoreException


class EmbeddingService:
    """Servicio para generación de embeddings"""
    
    def __init__(self):
        self.logger = logging.getLogger("mcp.services.embedding")
        self.model = settings.embedding_model
        self.dimension = settings.embedding_dimension
        self._cache = {}
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generar embeddings para lista de textos"""
        try:
            self.logger.info(f"Generating embeddings for {len(texts)} texts")
            
            embeddings = []
            for text in texts:
                embedding = await self._generate_single_embedding(text)
                embeddings.append(embedding)
            
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Error generating embeddings: {e}")
            raise MCPCoreException(f"Error generando embeddings: {e}")
    
    async def _generate_single_embedding(self, text: str) -> List[float]:
        """Generar embedding para un texto individual"""
        # Verificar cache
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self._cache:
            return self._cache[text_hash]
        
        # Generar embedding determinístico
        seed = int(text_hash[:8], 16) % (2**32)
        np.random.seed(seed)
        
        # Generar vector normalizado
        embedding = np.random.normal(0, 1, self.dimension)
        embedding = embedding / np.linalg.norm(embedding)
        embedding_list = embedding.tolist()
        
        # Cachear resultado
        self._cache[text_hash] = embedding_list
        
        # Limitar cache size
        if len(self._cache) > 1000:
            # Remover entradas más antiguas (simplificado)
            self._cache = dict(list(self._cache.items())[-500:])
        
        return embedding_list
    
    async def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calcular similitud coseno entre dos embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calcular similitud coseno
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def clear_cache(self) -> None:
        """Limpiar cache de embeddings"""
        self._cache.clear()
        self.logger.info("Embedding cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        return {
            "cache_size": len(self._cache),
            "max_cache_size": 1000,
            "cache_hit_ratio": "calculated_on_next_requests"
        }
