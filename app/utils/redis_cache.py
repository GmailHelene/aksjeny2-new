# Redis Caching Implementation for Aksjeradar
"""
Redis caching implementation for news feeds and expensive operations
"""

import redis
import json
import pickle
from datetime import timedelta
from functools import wraps
from flask import current_app
import logging
import os

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis cache manager for Aksjeradar"""
    
    def __init__(self, app=None):
        self.redis_client = None
        self.enabled = False
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize Redis with Flask app"""
        try:
            redis_url = app.config.get('REDIS_URL', os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=False,  # We'll handle encoding manually
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            logger.info("Redis cache initialized successfully")
            
        except Exception as e:
            logger.warning(f"Redis cache initialization failed: {e}")
            self.redis_client = None
            self.enabled = False
    
    def get(self, key):
        """Get value from cache"""
        if not self.redis_client or not self.enabled:
            return None
        
        try:
            value = self.redis_client.get(f"aksjeradar:{key}")
            if value:
                return pickle.loads(value)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
        
        return None
    
    def set(self, key, value, timeout=3600):
        """Set value in cache with timeout (default 1 hour)"""
        if not self.redis_client or not self.enabled:
            return False
        
        try:
            serialized = pickle.dumps(value)
            return self.redis_client.setex(f"aksjeradar:{key}", timeout, serialized)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key):
        """Delete key from cache"""
        if not self.redis_client or not self.enabled:
            return False
        
        try:
            return self.redis_client.delete(f"aksjeradar:{key}")
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def flush_all(self):
        """Clear all cache"""
        if not self.redis_client or not self.enabled:
            return False
        
        try:
            return self.redis_client.flushdb()
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False
    
    def flush_pattern(self, pattern):
        """Delete all keys matching pattern"""
        if not self.redis_client or not self.enabled:
            return False
        
        try:
            keys = self.redis_client.keys(f"aksjeradar:{pattern}")
            if keys:
                return self.redis_client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Cache flush pattern error for {pattern}: {e}")
            return False
    
    def exists(self, key):
        """Check if key exists"""
        if not self.redis_client or not self.enabled:
            return False
        
        try:
            return bool(self.redis_client.exists(f"aksjeradar:{key}"))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def get_stats(self):
        """Get cache statistics"""
        if not self.redis_client or not self.enabled:
            return {"enabled": False, "status": "Redis not available"}
        
        try:
            info = self.redis_client.info()
            return {
                "enabled": True,
                "status": "Connected",
                "used_memory": info.get('used_memory_human', 'N/A'),
                "connected_clients": info.get('connected_clients', 0),
                "keyspace_hits": info.get('keyspace_hits', 0),
                "keyspace_misses": info.get('keyspace_misses', 0)
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"enabled": False, "status": f"Error: {e}"}
            if value:
                return pickle.loads(value)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
        
        return None
    
    def set(self, key, value, timeout=3600):
        """Set value in cache with timeout (default 1 hour)"""
        if not self.redis_client:
            return False
        
        try:
            serialized = pickle.dumps(value)
            return self.redis_client.setex(key, timeout, serialized)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key):
        """Delete key from cache"""
        if not self.redis_client:
            return False
        
        try:
            return self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def flush_all(self):
        """Clear all cache"""
        if not self.redis_client:
            return False
        
        try:
            return self.redis_client.flushdb()
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False

# Global cache instance
cache = RedisCache()

def cached(timeout=3600, key_prefix=""):
    """
    Decorator for caching function results
    
    Args:
        timeout: Cache timeout in seconds (default 1 hour)
        key_prefix: Optional prefix for cache key
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}:{f.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cache miss for {cache_key}, result cached")
            
            return result
        return wrapper
    return decorator

# Specific cache decorators for different data types
def cache_news_feeds(timeout=900):  # 15 minutes for news
    """Cache decorator specifically for news feeds"""
    return cached(timeout=timeout, key_prefix="news_feeds")

def cache_market_data(timeout=300):  # 5 minutes for market data
    """Cache decorator specifically for market data"""
    return cached(timeout=timeout, key_prefix="market_data")

def cache_analysis_results(timeout=1800):  # 30 minutes for analysis
    """Cache decorator specifically for analysis results"""
    return cached(timeout=timeout, key_prefix="analysis")

def cache_user_data(timeout=600):  # 10 minutes for user-specific data
    """Cache decorator specifically for user data"""
    return cached(timeout=timeout, key_prefix="user_data")

def cache_stock_data(timeout=300):  # 5 minutes for stock data
    """Cache decorator specifically for stock data"""
    return cached(timeout=timeout, key_prefix="stocks")

# Cache management functions
def clear_news_cache():
    """Clear all news-related cache"""
    cache.flush_pattern("news_*")

def clear_market_cache():
    """Clear all market data cache"""
    cache.flush_pattern("market_*")

def clear_analysis_cache():
    """Clear all analysis cache"""
    cache.flush_pattern("analysis_*")

def clear_all_cache():
    """Clear entire cache"""
    cache.flush_all()

def get_cache_stats():
    """Get cache statistics"""
    return cache.get_stats()
