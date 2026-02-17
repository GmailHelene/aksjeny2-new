# API Response & Caching Patterns

This document summarizes the unified API response helper, data source constants, and caching decorators now available in the codebase.

## Response Helper (`app/utils/api_response.py`)

Primary functions:
- `ok(payload: dict, *, extra: dict = None, **meta)`
- `fail(error: str, *, message: str = None, data: dict = None, extra: dict = None, **meta)`

Behavior:
- Ensures consistent envelope fields: `success`, `cache_hit`, `data_source`, `authenticated`, optional `error`, `message`, pagination fields (`page`, `pages`, `total`).
- Infers `data_points` when not provided based on common list keys: `data`, `items`, `results`, `records`, `rows` or a single-key list payload.
- `extra` allows appending meta keys without overwriting existing ones.

Usage examples:
```python
from app.utils.api_response import ok, fail
from app.constants import DataSource

# Simple success
return ok({ 'items': records }, data_source=DataSource.DB)

# With pagination
return ok({ 'results': page_items }, page=page, pages=pages, total=total, data_source=DataSource.DB)

# Failure with details
return fail('NOT_FOUND', message='Symbol not found', data={'results': []}, data_source=DataSource.DB)

# Attaching extra metrics
return ok({'items': rows}, extra={'query_ms': elapsed}, data_source=DataSource.DB)
```

## Data Source Constants (`app/constants.py`)

Central definitions to avoid string typos:
```
DataSource.DB
DataSource.CACHE
DataSource.FALLBACK_SYNTHETIC
DataSource.EXTERNAL_API
DataSource.DB_ERROR_FALLBACK
DataSource.COMPUTED
DataSource.UNKNOWN
```
Add new values by extending the class—avoid modifying existing values to preserve analytics stability.

## Caching Utilities (`app/utils/cache.py`)

### `simple_cache(ttl=30, key_func=None)`
- Generic TTL cache storing the raw return value of the wrapped function.
- Use when your function already returns a full Flask response or complex tuple you will consume manually.

### `cached_api(ttl=30, key_func=None, data_source_cached=None, data_source_fresh=None)`
- Specialized for API endpoint internals.
- Wrapped function should return `(payload_dict, meta_dict)`; decorator converts to a standardized JSON response using `build_response`.
- On cache miss: uses `meta['data_source']` or provided `data_source_fresh` (default `UNKNOWN`).
- On cache hit: forces `cache_hit=True` and `data_source` becomes `data_source_cached` (default `CACHE`).

Example:
```python
from app.utils.cache import cached_api
from app.constants import DataSource

@cached_api(ttl=60, key_func=lambda user_id: f"user_dash::{user_id}", data_source_fresh=DataSource.DB)
def _load_dashboard(user_id):
    rows = fetch_rows(user_id)
    meta = { 'data_source': DataSource.DB, 'authenticated': True }
    return { 'items': rows }, meta
```

### Key Selection
- Always include user scoping when data is user-specific: `lambda: f"alerts::{current_user.id}"`.
- For symbol queries: `lambda symbol: f"chart::{symbol.upper()}"`.
- Avoid embedding large mutable objects (like full payloads) inside the key.

### When NOT to Cache
- Highly dynamic or side-effect endpoints (writes, state mutations).
- Security-sensitive responses that vary on permission checks beyond user id.
- Endpoints returning streaming / large binary data.

## Migration Guidelines
1. Replace manual `jsonify` usage with `ok` / `fail` for new endpoints.
2. Introduce `DataSource` value where applicable (DB, CACHE, EXTERNAL_API, etc.).
3. For read-heavy endpoints with stable results over short intervals, wrap internal data assembly in a `cached_api` function.
4. Add / adjust tests: first call `cache_hit == False`, second call `cache_hit == True`.

## Testing Patterns
```python
r1 = client.get('/notifications/api/price_alerts')
assert r1.get_json()['cache_hit'] is False
r2 = client.get('/notifications/api/price_alerts')
assert r2.get_json()['cache_hit'] is True
```
If using `cached_api`, you do not manually set `cache_hit`; decorator handles it.

## Error Handling
- Use `fail(code, message=..., data={...})` for recoverable errors (still HTTP 200 if part of business logic).
- For real HTTP errors (401, 403, 404), still permissible to return `fail(..., status_code=403)` by passing `status_code` via meta.

## Performance Notes
- Current cache is in-memory per process; not shared across workers.
- TTL eviction happens on access; no background sweeper.
- For scaling, you can implement a Redis-backed store with same interface (`get/set`).

## Future Extensions (Optional)
- Add invalidation hooks for CRUD mutations.
- Support per-user quotas in `cached_api`.
- Structured metrics collection (e.g., push timing & hit ratio to a monitoring service).

---
Questions or improvements: open a PR or add notes to this doc.
