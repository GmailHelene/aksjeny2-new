import time
import pytest

# This test ensures the technical cache in stocks blueprint invalidates after TTL.
# It assumes the cache key format tech::<SYMBOL>::1d and global _TECH_CACHE + TECH_CACHE_TTL_SECONDS.

@pytest.mark.parametrize("symbol", ["AAPL"])  # keep deterministic
def test_technical_cache_expiry(auth_client, symbol):
    client, _user = auth_client if isinstance(auth_client, tuple) else (auth_client, None)
    # Reset cache state for deterministic behavior (may have been primed by prior tests)
    from app.routes.stocks import _TECH_CACHE, _TECH_FIRST_REQUEST_TRACKER
    for s in [symbol.upper()]:
        _TECH_CACHE.pop(f"tech::{s}::1d", None)
        if s in _TECH_FIRST_REQUEST_TRACKER:
            _TECH_FIRST_REQUEST_TRACKER.discard(s)

    # First request: expect cache miss (data-tech-cache-hit="false")
    r1 = client.get(f"/stocks/details/{symbol}")
    assert r1.status_code == 200
    assert 'data-tech-cache-hit="false"' in r1.text

    # Second request immediately: should be hit
    r2 = client.get(f"/stocks/details/{symbol}")
    assert r2.status_code == 200
    assert 'data-tech-cache-hit="true"' in r2.text

    # Access the application context to manipulate cache timestamp
    from app.routes.stocks import _TECH_CACHE, TECH_CACHE_TTL_SECONDS
    cache_key = f"tech::{symbol.upper()}::1d"
    assert cache_key in _TECH_CACHE

    # Force expiration by rewinding stored timestamp beyond TTL
    _TECH_CACHE[cache_key]['ts'] -= (TECH_CACHE_TTL_SECONDS + 5)

    # Third request after manual expiry: should be miss again (false)
    r3 = client.get(f"/stocks/details/{symbol}")
    assert r3.status_code == 200
    assert 'data-tech-cache-hit="false"' in r3.text

    # Final request to ensure it re-caches
    r4 = client.get(f"/stocks/details/{symbol}")
    assert r4.status_code == 200
    assert 'data-tech-cache-hit="true"' in r4.text
