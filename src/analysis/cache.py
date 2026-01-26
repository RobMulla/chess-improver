"""Analysis caching layer using Redis."""
import redis
import json
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class AnalysisCache:
    """Redis cache for Stockfish evaluations to avoid redundant analysis."""
    
    def __init__(self, host='localhost', port=6379, ttl=86400):
        """
        Initialize cache connection.
        
        Args:
            host: Redis host
            port: Redis port  
            ttl: Time to live in seconds (default 24 hours)
        """
        try:
            self.redis = redis.Redis(
                host=host,
                port=port,
                decode_responses=True,
                socket_connect_timeout=2
            )
            # Test connection
            self.redis.ping()
            self.enabled = True
            logger.info("✅ Redis cache connected")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"⚠️ Redis unavailable, caching disabled: {e}")
            self.redis = None
            self.enabled = False
        
        self.ttl = ttl
        self.cache_hits = 0
        self.cache_misses = 0
    
    def get_evaluation(self, fen: str) -> Optional[Dict]:
        """
        Get cached evaluation for a position.
        
        Args:
            fen: Position in FEN notation
            
        Returns:
            Cached evaluation dict or None if not found
        """
        if not self.enabled:
            return None
        
        try:
            key = f"eval:{fen}"
            cached = self.redis.get(key)
            
            if cached:
                self.cache_hits += 1
                logger.debug(f"Cache HIT for {fen[:20]}...")
                return json.loads(cached)
            else:
                self.cache_misses += 1
                logger.debug(f"Cache MISS for {fen[:20]}...")
                return None
                
        except Exception as e:
            logger.error(f"Cache read error: {e}")
            return None
    
    def set_evaluation(self, fen: str, result: Dict) -> bool:
        """
        Cache an evaluation result.
        
        Args:
            fen: Position in FEN notation
            result: Evaluation result dict
            
        Returns:
            True if cached successfully
        """
        if not self.enabled:
            return False
        
        try:
            key = f"eval:{fen}"
            self.redis.setex(key, self.ttl, json.dumps(result))
            logger.debug(f"Cached evaluation for {fen[:20]}...")
            return True
        except Exception as e:
            logger.error(f"Cache write error: {e}")
            return False
    
    def clear_all(self) -> int:
        """
        Clear all cached evaluations.
        
        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0
        
        try:
            keys = self.redis.keys("eval:*")
            if keys:
                deleted = self.redis.delete(*keys)
                logger.info(f"🗑️ Cleared {deleted} cached evaluations")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        if not self.enabled:
            return {"enabled": False}
        
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0
        
        try:
            info = self.redis.info()
            return {
                "enabled": True,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "hit_rate": f"{hit_rate:.1f}%",
                "total_keys": self.redis.dbsize(),
                "memory_used": info.get('used_memory_human', 'N/A')
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {"enabled": True, "error": str(e)}


# Global cache instance
_cache = None

def get_cache() -> AnalysisCache:
    """Get or create global cache instance."""
    global _cache
    if _cache is None:
        _cache = AnalysisCache()
    return _cache
