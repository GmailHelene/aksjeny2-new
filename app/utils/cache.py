import time
import functools
from typing import Callable, Any, Dict, Tuple
from flask import jsonify
from .api_response import build_response
try:
    from app.constants import DataSource
except Exception:
    # Fallback if constants not yet importable in some contexts
    class DataSource:
        CACHE = "CACHE"
        UNKNOWN = "UNKNOWN"

class SimpleCacheStore:
    def __init__(self):
        self.store: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str, ttl: int):
        entry = self.store.get(key)
        if not entry:
            return None
        if (time.time() - entry['ts']) > ttl:
            self.store.pop(key, None)
            return None
        return entry['value']

    def set(self, key: str, value: Any):
        self.store[key] = {'value': value, 'ts': time.time()}

_GLOBAL_SIMPLE_CACHE = SimpleCacheStore()

def simple_cache(ttl: int = 30, key_func: Callable[..., str] = None):
    """Lightweight cache decorator.
    Assumes the wrapped function returns a tuple (response, status) or response object.
    Does NOT mutate original payload; caller should handle cache_hit logic externally if needed.
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key_base = key_func(*args, **kwargs) if key_func else f"{fn.__name__}:{args}:{kwargs}"
            cached = _GLOBAL_SIMPLE_CACHE.get(key_base, ttl)
            if cached is not None:
                return cached
            result = fn(*args, **kwargs)
            _GLOBAL_SIMPLE_CACHE.set(key_base, result)
            return result
        return wrapper
    return decorator

def cached_api(ttl: int = 30, key_func: Callable[..., str] = None, data_source_cached: str = None, data_source_fresh: str = None):
    """API-focused cache decorator wrapping functions that return (payload_dict, meta_dict) OR already-built Flask responses.

    Expected wrapped function contract (recommended):
        def fn(...):
            return { 'results': [...] }, { 'data_source': DataSource.DB }

    Decorator will:
      - Cache the tuple (payload, meta)
      - On hit: force cache_hit=True, set data_source to data_source_cached (default DataSource.CACHE)
      - On miss: uses provided meta['data_source'] or data_source_fresh
      - Feed into build_response(success=True, payload, **meta)

    If function already returns a Flask response (Response, status), it is passed through unchanged (no caching).
    """
    data_source_cached = data_source_cached or getattr(DataSource, 'CACHE', 'CACHE')
    data_source_fresh_default = data_source_fresh or getattr(DataSource, 'UNKNOWN', 'UNKNOWN')

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key = key_func(*args, **kwargs) if key_func else f"{fn.__name__}:{args}:{kwargs}"
            cached = _GLOBAL_SIMPLE_CACHE.get(key, ttl)
            if cached is not None:
                payload, meta = cached
                meta = dict(meta)
                # Force cache indicators
                meta['cache_hit'] = True
                meta['data_source'] = data_source_cached
                return build_response(True, payload, **meta)

            result = fn(*args, **kwargs)
            # Pass through already built responses (cannot safely introspect)
            try:
                # Heuristic: jsonify(...) returns a Response; tuple(Response, status) also possible.
                from flask import Response
                if isinstance(result, Response) or (isinstance(result, tuple) and isinstance(result[0], Response)):
                    return result
            except Exception:
                pass

            if not isinstance(result, tuple) or len(result) != 2:
                raise ValueError("cached_api wrapped function must return (payload_dict, meta_dict) when not returning a Response")
            payload, meta = result
            if not isinstance(payload, dict) or not isinstance(meta, dict):
                raise TypeError("cached_api expected (dict, dict) return when not returning Flask Response")
            meta = dict(meta)  # copy
            # Mark miss
            meta.setdefault('cache_hit', False)
            meta.setdefault('data_source', meta.get('data_source') or data_source_fresh_default)
            # Store raw payload/meta for future hits
            _GLOBAL_SIMPLE_CACHE.set(key, (payload, meta))
            return build_response(True, payload, **meta)
        return wrapper
    return decorator
