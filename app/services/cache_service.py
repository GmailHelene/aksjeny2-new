"""
Redis Cache Service for Aksjeradar
Provides efficient caching for news feeds, market data, and API responses
"""

import redis
import json
import os
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
from functools import wraps
from flask import current_app
import logging

# Safe logger function for when outside app context
def safe_log_error(message):
    """Log error safely, even outside app context"""
    try:
        current_app.logger.error(message)
    except RuntimeError:
        # Outside app context, use standard logging
        logging.error(message)

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis cache service for performance optimization"""
    
    def __init__(self):
        # Connect to Redis with graceful fallback
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        try:
            self.redis_client = redis.Redis.from_url(
                redis_url, 
                decode_responses=True,
                socket_timeout=1,
                socket_connect_timeout=1
            )
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            # Only log in development or when explicitly enabled
            if os.getenv('FLASK_ENV') == 'development' or os.getenv('CACHE_LOGGING', '').lower() == 'true':
                logger.info("✅ Redis cache connected successfully")
        except Exception as e:
            # Silently disable cache in production
            self.redis_client = None
            self.enabled = False
            # Only log in development
            if os.getenv('FLASK_ENV') == 'development' or os.getenv('DEBUG', '').lower() == 'true':
                logger.debug(f"Redis cache disabled: {e}")
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Set a value in cache with TTL (time to live) in seconds
        Default TTL: 5 minutes
        """
        if not self.enabled:
            return False
            
        try:
            # Serialize complex objects to JSON
            if isinstance(value, (dict, list)):
                value = json.dumps(value, default=str)
            
            return self.redis_client.setex(key, ttl, value)
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache, returns None if not found or expired"""
        if not self.enabled:
            return None
            
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
                
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Return as string if not JSON
                return value
                
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        if not self.enabled:
            return False
            
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern"""
        if not self.enabled:
            return 0
            
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache invalidate error for pattern '{pattern}': {e}")
            return 0
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.enabled:
            return {"enabled": False, "status": "disabled"}
            
        try:
            info = self.redis_client.info()
            return {
                "enabled": True,
                "status": "connected",
                "memory_used": info.get('used_memory_human', 'N/A'),
                "keys": self.redis_client.dbsize(),
                "hits": info.get('keyspace_hits', 0),
                "misses": info.get('keyspace_misses', 0),
                "uptime": info.get('uptime_in_seconds', 0)
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"enabled": False, "status": "error", "error": str(e)}

# Global cache instance
cache = RedisCache()

def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        key_prefix: Optional prefix for cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix, func.__name__]
            
            # Include args and kwargs in key
            if args:
                key_parts.extend([str(arg) for arg in args])
            if kwargs:
                key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            
            cache_key = ":".join(filter(None, key_parts))
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache HIT for {cache_key}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache MISS for {cache_key}")
            result = func(*args, **kwargs)
            
            # Cache the result
            cache.set(cache_key, result, ttl)
            return result
            
        return wrapper
    return decorator

# Pre-defined cache durations for different data types
CACHE_DURATIONS = {
    'news_feeds': 300,        # 5 minutes
    'market_data': 60,        # 1 minute
    'stock_prices': 30,       # 30 seconds
    'analysis_results': 900,  # 15 minutes
    'user_data': 3600,        # 1 hour
    'static_content': 86400,  # 24 hours
}

def cache_news_feeds(func):
    """Specific decorator for news feeds with 5-minute cache"""
    return cached(ttl=CACHE_DURATIONS['news_feeds'], key_prefix="news")(func)

def cache_market_data(func):
    """Specific decorator for market data with 1-minute cache"""
    return cached(ttl=CACHE_DURATIONS['market_data'], key_prefix="market")(func)

def cache_analysis(func):
    """Specific decorator for analysis results with 15-minute cache"""
    return cached(ttl=CACHE_DURATIONS['analysis_results'], key_prefix="analysis")(func)

"""
Simple caching service for stock data
"""

class CacheService:
    def __init__(self):
        self.cache_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        self.memory_cache = {}
        
    def get_cache_path(self, key):
        """Get the file path for a cache key"""
        safe_key = key.replace('/', '_').replace('\\', '_')
        return os.path.join(self.cache_dir, f"{safe_key}.json")
    
    def get(self, key, max_age_minutes=5):
        """Get cached data if it exists and is not expired"""
        # Check memory cache first
        if key in self.memory_cache:
            data, timestamp = self.memory_cache[key]
            if datetime.now() - timestamp < timedelta(minutes=max_age_minutes):
                return data
        
        # Check file cache
        cache_path = self.get_cache_path(key)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    cache_data = json.load(f)
                    
                cached_time = datetime.fromisoformat(cache_data['timestamp'])
                if datetime.now() - cached_time < timedelta(minutes=max_age_minutes):
                    data = cache_data['data']
                    # Store in memory cache
                    self.memory_cache[key] = (data, cached_time)
                    return data
            except Exception as e:
                safe_log_error(f"Error reading cache for {key}: {e}")
        
        return None
    
    def set(self, key, data):
        """Store data in cache"""
        try:
            # Store in memory cache
            self.memory_cache[key] = (data, datetime.now())
            
            # Store in file cache
            cache_path = self.get_cache_path(key)
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)
                
        except Exception as e:
            current_app.logger.error(f"Error writing cache for {key}: {e}")
    
    def clear(self, key=None):
        """Clear cache for a specific key or all cache"""
        if key:
            # Clear specific key
            self.memory_cache.pop(key, None)
            cache_path = self.get_cache_path(key)
            if os.path.exists(cache_path):
                os.remove(cache_path)
        else:
            # Clear all cache
            self.memory_cache.clear()
            for file in os.listdir(self.cache_dir):
                if file.endswith('.json'):
                    os.remove(os.path.join(self.cache_dir, file))

# Global cache instance - This is the old CacheService, kept for backward compatibility
_legacy_cache_service = None

def get_legacy_cache_service():
    global _legacy_cache_service
    if _legacy_cache_service is None:
        _legacy_cache_service = CacheService()
    return _legacy_cache_service

"""
Cache service for storing and retrieving cached data with freshness tracking
"""

class CacheServiceV2:
    """Service for handling data caching with Redis"""
    
    def __init__(self):
        self.redis_client = None
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection - gracefully handle unavailability"""
        try:
            # Use environment variables directly if no app context
            import os
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)),
                decode_responses=True,
                socket_timeout=1,  # Quick timeout for development
                socket_connect_timeout=1
            )
            # Test connection
            self.redis_client.ping()
            # Only log success if we have an app context
            try:
                from flask import current_app
                current_app.logger.info("✅ Redis cache connected")
            except RuntimeError:
                pass  # No app context, that's fine
        except (redis.ConnectionError, redis.TimeoutError, Exception):
            # Silently fall back to in-memory cache
            self.redis_client = None
            self._memory_cache = {}
            # Only log in development/debug mode
            if os.getenv('FLASK_ENV') == 'development' or os.getenv('DEBUG', '').lower() == 'true':
                try:
                    from flask import current_app
                    current_app.logger.debug("Redis not available, using in-memory cache")
                except RuntimeError:
                    pass  # No app context, that's fine
    
    def get(self, key: str, max_age_minutes: int = 5) -> Optional[Any]:
        """Get value from cache"""
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                safe_log_error(f"Cache get error: {e}")
        else:
            # Fallback to memory cache
            if key in self._memory_cache:
                value, expiry = self._memory_cache[key]
                if expiry > time.time():
                    return value
                else:
                    del self._memory_cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL in seconds"""
        if self.redis_client:
            try:
                self.redis_client.setex(key, ttl, json.dumps(value))
            except Exception as e:
                safe_log_error(f"Cache set error: {e}")
        else:
            # Fallback to memory cache
            self._memory_cache[key] = (value, time.time() + ttl)
    
    def delete(self, key: str):
        """Delete value from cache"""
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                current_app.logger.error(f"Cache delete error: {e}")
        else:
            self._memory_cache.pop(key, None)
    
    def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        if self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                current_app.logger.error(f"Cache clear pattern error: {e}")
        else:
            # For memory cache, clear matching keys
            keys_to_delete = [k for k in self._memory_cache.keys() if pattern.replace('*', '') in k]
            for key in keys_to_delete:
                del self._memory_cache[key]
    
    def get_with_freshness(self, key: str) -> Dict[str, Any]:
        """Get value with freshness indicator"""
        value = self.get(key)
        if value:
            # Extract timestamp if stored with data
            if isinstance(value, dict) and '_cached_at' in value:
                cached_at = datetime.fromisoformat(value['_cached_at'])
                age_seconds = (datetime.utcnow() - cached_at).total_seconds()
                
                # Determine freshness
                if age_seconds < 60:
                    freshness = 'live'
                    freshness_text = 'Sanntid'
                elif age_seconds < 300:
                    freshness = 'fresh'
                    freshness_text = f'{int(age_seconds // 60)} min siden'
                elif age_seconds < 3600:
                    freshness = 'recent'
                    freshness_text = f'{int(age_seconds // 60)} min siden'
                else:
                    freshness = 'stale'
                    freshness_text = f'{int(age_seconds // 3600)} timer siden'
                
                return {
                    'data': value,
                    'freshness': freshness,
                    'freshness_text': freshness_text,
                    'cached_at': cached_at
                }
        
        return {
            'data': None,
            'freshness': 'missing',
            'freshness_text': 'Ingen data',
            'cached_at': None
        }


def cache_result(ttl: int = 300, key_prefix: str = None):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_prefix:
                cache_key = f"{key_prefix}:{func.__name__}"
            else:
                cache_key = f"func:{func.__name__}"
            
            # Add args to key if present
            if args:
                cache_key += f":{':'.join(str(arg) for arg in args)}"
            if kwargs:
                cache_key += f":{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
            
            # Try to get from cache
            cache_service = get_cache_service()
            cached = cache_service.get(cache_key)
            if cached is not None:
                return cached
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache with timestamp
            if isinstance(result, dict):
                result['_cached_at'] = datetime.utcnow().isoformat()
            else:
                result = {
                    'data': result,
                    '_cached_at': datetime.utcnow().isoformat()
                }
            
            cache_service = get_cache_service()
            cache_service.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# Global cache service instance - initialized lazily
cache_service = None

def get_cache_service():
    """Get the global cache service instance, initializing it if needed."""
    global cache_service
    if cache_service is None:
        cache_service = CacheServiceV2()
    return cache_service
