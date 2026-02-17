import redis
import json
import pickle
import hashlib
import time
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
from flask import current_app
import threading
from functools import wraps

class CacheManager:
    """Advanced multi-layer cache management system"""
    
    def __init__(self, redis_url=None):
        try:
            self.redis_client = redis.Redis.from_url(redis_url or 'redis://localhost:6379', decode_responses=False)
            self.redis_available = True
        except:
            self.redis_client = None
            self.redis_available = False
            
        self.local_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'local_hits': 0,
            'redis_hits': 0
        }
        self.lock = threading.RLock()
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with multi-layer lookup"""
        try:
            # Check local cache first
            local_result = self._get_local(key)
            if local_result is not None:
                self.cache_stats['local_hits'] += 1
                self.cache_stats['hits'] += 1
                return local_result
            
            # Check Redis cache if available
            if self.redis_available:
                redis_result = self._get_redis(key)
                if redis_result is not None:
                    # Store in local cache for faster access
                    self._set_local(key, redis_result, ttl=300)  # 5 min local TTL
                    self.cache_stats['redis_hits'] += 1
                    self.cache_stats['hits'] += 1
                    return redis_result
            
            self.cache_stats['misses'] += 1
            return None
            
        except Exception as e:
            if current_app:
                current_app.logger.error(f"Cache get error for key {key}: {str(e)}")
            self.cache_stats['misses'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with multi-layer storage"""
        try:
            success = False
            
            # Set in Redis with longer TTL if available
            if self.redis_available:
                redis_success = self._set_redis(key, value, ttl)
                if redis_success:
                    success = True
            
            # Set in local cache with shorter TTL
            local_ttl = min(ttl, 300)  # Max 5 minutes for local cache
            local_success = self._set_local(key, value, local_ttl)
            if local_success:
                success = True
            
            if success:
                self.cache_stats['sets'] += 1
            
            return success
            
        except Exception as e:
            if current_app:
                current_app.logger.error(f"Cache set error for key {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from both cache layers"""
        try:
            success = False
            
            if self.redis_available:
                redis_success = self._delete_redis(key)
                if redis_success:
                    success = True
                    
            local_success = self._delete_local(key)
            if local_success:
                success = True
            
            if success:
                self.cache_stats['deletes'] += 1
            
            return success
            
        except Exception as e:
            if current_app:
                current_app.logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            total_deleted = 0
            
            # Clear from Redis if available
            if self.redis_available:
                try:
                    redis_keys = self.redis_client.keys(pattern)
                    if redis_keys:
                        redis_deleted = self.redis_client.delete(*redis_keys)
                        total_deleted += redis_deleted
                except:
                    pass
            
            # Clear from local cache
            with self.lock:
                keys_to_delete = [k for k in self.local_cache.keys() if self._match_pattern(k, pattern)]
                for key in keys_to_delete:
                    if key in self.local_cache:
                        del self.local_cache[key]
                        total_deleted += 1
            
            self.cache_stats['deletes'] += total_deleted
            return total_deleted
            
        except Exception as e:
            if current_app:
                current_app.logger.error(f"Cache clear pattern error for {pattern}: {str(e)}")
            return 0
    
    def get_stats(self) -> Dict:
        """Get cache performance statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'hit_rate': round(hit_rate, 2),
            'sets': self.cache_stats['sets'],
            'deletes': self.cache_stats['deletes'],
            'local_hits': self.cache_stats['local_hits'],
            'redis_hits': self.cache_stats['redis_hits'],
            'local_cache_size': len(self.local_cache),
            'redis_available': self.redis_available
        }
    
    def _get_local(self, key: str) -> Optional[Any]:
        """Get from local cache"""
        with self.lock:
            if key in self.local_cache:
                value, expires_at = self.local_cache[key]
                if datetime.now() < expires_at:
                    return value
                else:
                    del self.local_cache[key]
        return None
    
    def _set_local(self, key: str, value: Any, ttl: int) -> bool:
        """Set in local cache"""
        try:
            with self.lock:
                expires_at = datetime.now() + timedelta(seconds=ttl)
                self.local_cache[key] = (value, expires_at)
                
                # Clean up expired entries if cache is getting large
                if len(self.local_cache) > 1000:
                    self._cleanup_local_cache()
                
            return True
        except Exception:
            return False
    
    def _delete_local(self, key: str) -> bool:
        """Delete from local cache"""
        with self.lock:
            if key in self.local_cache:
                del self.local_cache[key]
                return True
        return False
    
    def _get_redis(self, key: str) -> Optional[Any]:
        """Get from Redis cache"""
        if not self.redis_available:
            return None
            
        try:
            data = self.redis_client.get(key)
            if data:
                return self._deserialize(data)
        except Exception:
            pass
        return None
    
    def _set_redis(self, key: str, value: Any, ttl: int) -> bool:
        """Set in Redis cache"""
        if not self.redis_available:
            return False
            
        try:
            serialized_data = self._serialize(value)
            return bool(self.redis_client.setex(key, ttl, serialized_data))
        except Exception:
            return False
    
    def _delete_redis(self, key: str) -> bool:
        """Delete from Redis cache"""
        if not self.redis_available:
            return False
            
        try:
            return bool(self.redis_client.delete(key))
        except Exception:
            return False
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage"""
        try:
            # Try JSON first for better readability
            return json.dumps(value, default=str).encode('utf-8')
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            return pickle.dumps(value)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage"""
        try:
            # Try JSON first
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            return pickle.loads(data)
    
    def _cleanup_local_cache(self):
        """Clean up expired entries from local cache"""
        now = datetime.now()
        expired_keys = [
            key for key, (value, expires_at) in self.local_cache.items()
            if now >= expires_at
        ]
        for key in expired_keys:
            del self.local_cache[key]
    
    def _match_pattern(self, key: str, pattern: str) -> bool:
        """Simple pattern matching for local cache"""
        import fnmatch
        return fnmatch.fnmatch(key, pattern)

# Cache decorators
def cached(ttl=3600, key_func=None):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__module__}.{func.__name__}:{_generate_key(*args, **kwargs)}"
            
            # Try to get from cache
            result = cache_manager.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

def invalidate_cache(pattern):
    """Decorator to invalidate cache after function execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            cache_manager.clear_pattern(pattern)
            return result
        return wrapper
    return decorator

def _generate_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments"""
    key_parts = []
    
    # Add positional arguments
    for arg in args:
        if hasattr(arg, 'id'):  # For model instances
            key_parts.append(f"{arg.__class__.__name__}:{arg.id}")
        else:
            key_parts.append(str(arg))
    
    # Add keyword arguments
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}:{v}")
    
    key_string = ":".join(key_parts)
    
    # Hash long keys
    if len(key_string) > 100:
        return hashlib.md5(key_string.encode()).hexdigest()
    
    return key_string

# Global cache manager instance
cache_manager = CacheManager()
