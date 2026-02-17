"""
Simple cache service to reduce API calls
"""
import time
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SimpleCache:
    """Simple in-memory cache with TTL"""
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_config = {
            'stock_info': 3600,     # 60 minutes for stock info (increased from 30 min)
            'stock_data': 1800,     # 30 minutes for stock data (increased from 5 min)
            'news': 7200,           # 120 minutes for news (increased from 60 min)
            'rate_limit_fallback': 120,  # 2 minutes for 429 error fallback
            'default': 1800         # 30 minutes default (increased from 15 min)
        }
    
    def get(self, key: str, cache_type: str = 'default') -> Optional[Any]:
        """Get value from cache if not expired"""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        ttl = self.ttl_config.get(cache_type, self.ttl_config['default'])
        
        if time.time() - entry['timestamp'] > ttl:
            # Expired, remove from cache
            del self.cache[key]
            return None
        
        logger.debug(f"Cache hit for key: {key}")
        return entry['data']
    
    def set(self, key: str, value: Any, cache_type: str = 'default') -> None:
        """Set value in cache with timestamp"""
        self.cache[key] = {
            'data': value,
            'timestamp': time.time()
        }
        logger.debug(f"Cache set for key: {key}")
    
    def clear(self) -> None:
        """Clear all cache"""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def cleanup_expired(self) -> None:
        """Remove expired entries from cache"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.cache.items():
            # Use default TTL for cleanup
            if current_time - entry['timestamp'] > self.ttl_config['default']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

# Global cache instance
simple_cache = SimpleCache()
