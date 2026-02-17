"""
Enhanced API Caching and Rate Limiting Service
Provides intelligent caching, request deduplication, and rate limiting
"""

import time
import hashlib
import json
import threading
from collections import defaultdict, deque
from typing import Dict, Any, Optional, Callable
from functools import wraps
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Thread-safe rate limiter using token bucket algorithm"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
        self.lock = threading.RLock()
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for given key"""
        with self.lock:
            now = time.time()
            cutoff = now - self.window_seconds
            
            # Remove old requests
            while self.requests[key] and self.requests[key][0] < cutoff:
                self.requests[key].popleft()
            
            # Check if under limit
            if len(self.requests[key]) < self.max_requests:
                self.requests[key].append(now)
                return True
            
            return False
    
    def time_until_allowed(self, key: str) -> float:
        """Get seconds until next request is allowed"""
        with self.lock:
            if not self.requests[key]:
                return 0
            
            oldest_request = self.requests[key][0]
            return max(0, oldest_request + self.window_seconds - time.time())

class CacheEntry:
    """Represents a cached entry with metadata"""
    
    def __init__(self, data: Any, ttl: int = 300, tags: list = None):
        self.data = data
        self.created_at = time.time()
        self.ttl = ttl
        self.tags = tags or []
        self.access_count = 0
        self.last_accessed = time.time()
    
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        return time.time() > self.created_at + self.ttl
    
    def access(self):
        """Record access for LRU tracking"""
        self.access_count += 1
        self.last_accessed = time.time()

class IntelligentCache:
    """Advanced caching with TTL, LRU eviction, and tagging"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.tag_index: Dict[str, set] = defaultdict(set)
        self.lock = threading.RLock()
    
    def _make_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if exists and not expired"""
        with self.lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            if entry.is_expired():
                self._remove_entry(key)
                return None
            
            entry.access()
            return entry.data
    
    def set(self, key: str, value: Any, ttl: int = None, tags: list = None) -> None:
        """Set cached value with optional TTL and tags"""
        with self.lock:
            # Remove existing entry if present
            if key in self.cache:
                self._remove_entry(key)
            
            # Evict if at capacity
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            # Add new entry
            entry = CacheEntry(value, ttl or self.default_ttl, tags)
            self.cache[key] = entry
            
            # Update tag index
            if tags:
                for tag in tags:
                    self.tag_index[tag].add(key)
    
    def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate all entries with given tag"""
        with self.lock:
            keys_to_remove = list(self.tag_index[tag])
            for key in keys_to_remove:
                self._remove_entry(key)
            return len(keys_to_remove)
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        with self.lock:
            import re
            regex = re.compile(pattern)
            keys_to_remove = [key for key in self.cache.keys() if regex.search(key)]
            for key in keys_to_remove:
                self._remove_entry(key)
            return len(keys_to_remove)
    
    def _remove_entry(self, key: str) -> None:
        """Remove entry and update tag index"""
        if key in self.cache:
            entry = self.cache[key]
            for tag in entry.tags:
                self.tag_index[tag].discard(key)
                if not self.tag_index[tag]:
                    del self.tag_index[tag]
            del self.cache[key]
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self.cache:
            return
        
        lru_key = min(self.cache.keys(), 
                     key=lambda k: self.cache[k].last_accessed)
        self._remove_entry(lru_key)
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries"""
        with self.lock:
            expired_keys = [key for key, entry in self.cache.items() 
                          if entry.is_expired()]
            for key in expired_keys:
                self._remove_entry(key)
            return len(expired_keys)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_entries = len(self.cache)
            expired_count = sum(1 for entry in self.cache.values() 
                              if entry.is_expired())
            total_accesses = sum(entry.access_count for entry in self.cache.values())
            
            return {
                'total_entries': total_entries,
                'expired_entries': expired_count,
                'total_accesses': total_accesses,
                'cache_utilization': total_entries / self.max_size,
                'tag_count': len(self.tag_index)
            }

class RequestDeduplicator:
    """Prevents duplicate concurrent requests"""
    
    def __init__(self):
        self.pending_requests: Dict[str, Any] = {}
        self.lock = threading.RLock()
    
    def get_or_execute(self, key: str, func: Callable, *args, **kwargs):
        """Get pending result or execute function"""
        with self.lock:
            if key in self.pending_requests:
                # Return the pending result
                return self.pending_requests[key]
            
            # Create and store the result
            try:
                result = func(*args, **kwargs)
                self.pending_requests[key] = result
                return result
            except Exception as e:
                # Don't cache exceptions
                raise e
            finally:
                # Clean up pending request
                self.pending_requests.pop(key, None)

class EnhancedAPIService:
    """Enhanced API service with caching, rate limiting, and optimization"""
    
    def __init__(self, cache_size: int = 1000, default_ttl: int = 300):
        self.cache = IntelligentCache(cache_size, default_ttl)
        self.deduplicator = RequestDeduplicator()
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.request_stats = defaultdict(lambda: {'count': 0, 'total_time': 0, 'errors': 0})
        self.lock = threading.RLock()
    
    def add_rate_limiter(self, name: str, max_requests: int, window_seconds: int):
        """Add a rate limiter for specific API"""
        self.rate_limiters[name] = RateLimiter(max_requests, window_seconds)
    
    def cached_request(self, cache_key: str = None, ttl: int = None, 
                      tags: list = None, rate_limit: str = None):
        """Decorator for caching API requests"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                key = cache_key or self.cache._make_key(func.__name__, *args, **kwargs)
                
                # Check rate limiting
                if rate_limit and rate_limit in self.rate_limiters:
                    limiter = self.rate_limiters[rate_limit]
                    if not limiter.is_allowed(key):
                        wait_time = limiter.time_until_allowed(key)
                        raise Exception(f"Rate limit exceeded. Retry in {wait_time:.1f} seconds")
                
                # Try cache first
                cached_result = self.cache.get(key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_result
                
                # Use deduplicator for concurrent requests
                def execute_request():
                    start_time = time.time()
                    try:
                        logger.debug(f"Executing {func.__name__}")
                        result = func(*args, **kwargs)
                        
                        # Cache successful result
                        self.cache.set(key, result, ttl, tags)
                        
                        # Update stats
                        duration = time.time() - start_time
                        self.request_stats[func.__name__]['count'] += 1
                        self.request_stats[func.__name__]['total_time'] += duration
                        
                        return result
                    except Exception as e:
                        # Update error stats
                        self.request_stats[func.__name__]['errors'] += 1
                        raise e
                
                return self.deduplicator.get_or_execute(key, execute_request)
            
            return wrapper
        return decorator
    
    def invalidate_cache(self, pattern: str = None, tags: list = None):
        """Invalidate cache entries by pattern or tags"""
        invalidated_count = 0
        
        if tags:
            for tag in tags:
                invalidated_count += self.cache.invalidate_by_tag(tag)
        
        if pattern:
            invalidated_count += self.cache.invalidate_pattern(pattern)
        
        logger.info(f"Invalidated {invalidated_count} cache entries")
        return invalidated_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive API service statistics"""
        cache_stats = self.cache.stats()
        
        # Calculate request statistics
        request_stats = {}
        for func_name, stats in self.request_stats.items():
            avg_time = (stats['total_time'] / stats['count']) if stats['count'] > 0 else 0
            error_rate = (stats['errors'] / stats['count']) if stats['count'] > 0 else 0
            
            request_stats[func_name] = {
                'total_requests': stats['count'],
                'total_errors': stats['errors'],
                'average_response_time': avg_time,
                'error_rate': error_rate
            }
        
        return {
            'cache': cache_stats,
            'requests': request_stats,
            'rate_limiters': {name: len(limiter.requests) 
                            for name, limiter in self.rate_limiters.items()}
        }
    
    def cleanup(self):
        """Cleanup expired cache entries"""
        return self.cache.cleanup_expired()

# Global instance
api_service = EnhancedAPIService()

# Decorator shortcuts
def cached_api_call(ttl: int = 300, tags: list = None, rate_limit: str = None):
    """Shortcut decorator for caching API calls"""
    return api_service.cached_request(ttl=ttl, tags=tags, rate_limit=rate_limit)

# Example usage in external APIs service
def setup_rate_limiters():
    """Setup rate limiters for different APIs"""
    # Financial Modeling Prep: 250 calls per day = ~10 per hour to be safe
    api_service.add_rate_limiter('fmp', 10, 3600)  # 10 requests per hour
    
    # Alpha Vantage: 5 calls per minute
    api_service.add_rate_limiter('alpha_vantage', 5, 60)
    
    # Alternative.me: No official limit, but be conservative
    api_service.add_rate_limiter('alternative', 60, 3600)  # 60 per hour
    
    # Internal APIs: More generous limits
    api_service.add_rate_limiter('internal', 1000, 3600)  # 1000 per hour

# Background cleanup task
def start_cleanup_scheduler():
    """Start background task to cleanup expired cache entries"""
    import threading
    import time
    
    def cleanup_task():
        while True:
            try:
                cleaned = api_service.cleanup()
                if cleaned > 0:
                    logger.info(f"Cleaned up {cleaned} expired cache entries")
                time.sleep(300)  # Run every 5 minutes
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                time.sleep(60)  # Wait before retrying
    
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    logger.info("Started cache cleanup scheduler")

# Initialize on import
setup_rate_limiters()
start_cleanup_scheduler()
