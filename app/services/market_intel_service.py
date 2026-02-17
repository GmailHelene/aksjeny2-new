import os
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Simple in-memory cache (process-local). Each entry: {'data': X, 'exp': epoch_seconds}
_cache: Dict[str, Dict[str, Any]] = {}

def _cache_get(key: str):
    entry = _cache.get(key)
    if not entry:
        return None
    if entry['exp'] < time.time():
        _cache.pop(key, None)
        return None
    return entry['data']

def _cache_set(key: str, data, ttl: int = 300):  # default 5m
    _cache[key] = {'data': data, 'exp': time.time() + ttl}

# --- Real Data Fetchers ---
# Each returns structured data OR an empty structure. No mock/synthetic placeholders.

ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
FINNHUB_KEY = os.getenv('FINNHUB_API_KEY')
FINNHUB_SECRET = os.getenv('FINNHUB_SECRET')

HEADERS = {
    'User-Agent': 'Aksjeradar/1.0 (+https://aksjeradar.trade)'
}

def fetch_economic_indicators_real() -> Dict[str, Any]:
    """Fetch macro indicators (Brent oil spot proxy + NOK/EUR FX rate).

    Data sources (no fabrication):
      - Brent oil: https://www.investing.com/commodities/brent-oil (HTML scrape fallback) OR empty if blocked.
      - FX NOK/EUR: ECB rates (https://api.exchangerate.host/latest?base=EUR) -> invert for EUR/NOK.

    Returns dict with available keys only. Missing values omitted instead of faked.
    Cached for 5 minutes.
    """
    cache_key = 'econ:macro'
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    result: Dict[str, Any] = {}
    # Fetch Brent oil (best-effort)
    try:
        import re
        from bs4 import BeautifulSoup  # noqa: F401
        # Lightweight attempt; if site blocks bots this will fail gracefully
        resp = requests.get('https://www.investing.com/commodities/brent-oil', timeout=10, headers=HEADERS)
        if resp.status_code == 200 and '<html' in resp.text.lower():
            m = re.search(r"data-test=\"instrument-price-last\"[^>]*>([0-9.,]+)<", resp.text)
            if m:
                price_str = m.group(1).replace(',', '')
                try:
                    result['brent_oil_usd'] = float(price_str)
                except ValueError:
                    pass
    except Exception as e:
        logger.warning(f"Brent oil fetch failed: {e}")

    # Fetch EUR base FX rates and derive EUR/NOK and NOK/EUR
    try:
        fx_resp = requests.get('https://api.exchangerate.host/latest?base=EUR&symbols=NOK', timeout=8, headers=HEADERS)
        if fx_resp.status_code == 200:
            js = fx_resp.json()
            nok_rate = (js.get('rates') or {}).get('NOK')
            if isinstance(nok_rate, (int, float)):
                result['eur_nok'] = nok_rate
                try:
                    result['nok_eur'] = 1.0 / nok_rate if nok_rate else None
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f"FX rate fetch failed: {e}")

    _cache_set(cache_key, result, ttl=300)
    return result

def fetch_crypto_fear_greed_real() -> Dict[str, Any]:
    """Fetch crypto fear & greed index from alternative.me API."""
    cache_key = 'crypto:fear_greed'
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    try:
        resp = requests.get('https://api.alternative.me/fng/', timeout=8, headers=HEADERS)
        if resp.status_code != 200:
            logger.warning(f"FNG API HTTP {resp.status_code}")
            return {}
        js = resp.json()
        data_list = js.get('data') or []
        if not data_list:
            return {}
        latest = data_list[0]
        result = {
            'value': int(latest.get('value')) if latest.get('value') and latest.get('value').isdigit() else None,
            'classification': latest.get('value_classification'),
            'timestamp': latest.get('timestamp')
        }
        _cache_set(cache_key, result, ttl=180)
        return result
    except Exception as e:
        logger.error(f"Fear & Greed fetch failed: {e}")
        return {}

def fetch_insider_trades_real() -> Dict[str, List[Dict[str, Any]]]:
    """Fetch insider trades for a small symbol set using Finnhub (if API key present).

    Endpoint: https://finnhub.io/api/v1/stock/insider-transactions?symbol=XXX
    We limit symbols to a short curated list to avoid rate limits.
    Structure returned: { symbol: [ {transaction_date, reporting_name, transaction_type, securities_transacted, price}, ... ] }
    Empty dict if unavailable. No fabrication.
    Cached 15 minutes.
    """
    if not FINNHUB_KEY:
        return {}
    cache_key = 'insider:trades'
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    symbols = ['AAPL', 'MSFT', 'NVDA']  # Extend with Oslo tickers once stable source integrated
    aggregated: Dict[str, List[Dict[str, Any]]] = {}
    for sym in symbols:
        try:
            resp = requests.get('https://finnhub.io/api/v1/stock/insider-transactions', params={'symbol': sym, 'token': FINNHUB_KEY}, timeout=10, headers={'X-Finnhub-Secret': FINNHUB_SECRET, **HEADERS})
            if resp.status_code != 200:
                logger.warning(f"Finnhub insider HTTP {resp.status_code} {sym}")
                continue
            js = resp.json() or {}
            data = js.get('data') or []
            normalized = []
            for it in data[:15]:  # limit per symbol
                try:
                    normalized.append({
                        'transaction_date': it.get('transactionDate'),
                        'reporting_name': it.get('name'),
                        'transaction_type': it.get('transactionCode'),
                        'securities_transacted': it.get('change'),
                        'price': it.get('tradePrice')
                    })
                except Exception:
                    continue
            if normalized:
                aggregated[sym] = normalized
        except Exception as e:
            logger.error(f"Insider trades fetch failed {sym}: {e}")
            continue
    _cache_set(cache_key, aggregated, ttl=900)
    return aggregated

def fetch_earnings_calendar_real() -> List[Dict[str, Any]]:
    """Attempt to gather upcoming earnings using Finnhub if available.
    Returns [] on failure or if keys missing.
    """
    if not FINNHUB_KEY:
        return []
    cache_key = 'earnings:upcoming'
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    try:
        # 7-day window
        start = datetime.utcnow().date()
        end = start + timedelta(days=7)
        params = {
            'from': str(start),
            'to': str(end),
            'token': FINNHUB_KEY
        }
        resp = requests.get('https://finnhub.io/api/v1/calendar/earnings', params=params, timeout=10, headers={'X-Finnhub-Secret': FINNHUB_SECRET, **HEADERS})
        if resp.status_code != 200:
            logger.warning(f"Finnhub earnings HTTP {resp.status_code}")
            return []
        js = resp.json() or {}
        items = js.get('earningsCalendar') or []
        normalized = []
        for it in items[:50]:  # limit display
            normalized.append({
                'symbol': it.get('symbol'),
                'date': it.get('date'),
                'when': it.get('hour') or '',
                'eps_estimated': it.get('epsEstimate'),
                'revenue_estimated': it.get('revenueEstimate'),
                'eps_actual': it.get('epsActual')
            })
        _cache_set(cache_key, normalized, ttl=600)
        return normalized
    except Exception as e:
        logger.error(f"Earnings calendar fetch failed: {e}")
        return []

def fetch_sector_performance_real() -> List[Dict[str, Any]]:
    """Fetch sector performance (Finnhub) if API key present.

    Endpoint: https://finnhub.io/api/v1/stock/sector-performance
    Returns list of { sector, change_percentage } entries.
    Empty list if unavailable.
    Cached 10 minutes.
    """
    if not FINNHUB_KEY:
        return []
    cache_key = 'sector:performance'
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    try:
        resp = requests.get('https://finnhub.io/api/v1/stock/sector-performance', params={'token': FINNHUB_KEY}, timeout=10, headers={'X-Finnhub-Secret': FINNHUB_SECRET, **HEADERS})
        if resp.status_code != 200:
            logger.warning(f"Finnhub sector performance HTTP {resp.status_code}")
            return []
        data = resp.json() or []
        normalized = []
        for it in data:
            sector = it.get('sector')
            change = it.get('change')
            if sector is None or change is None:
                continue
            # change is typically a percentage (float)
            try:
                change_val = float(change)
            except Exception:
                continue
            normalized.append({'sector': sector, 'change_percentage': change_val})
        _cache_set(cache_key, normalized, ttl=600)
        return normalized
    except Exception as e:
        logger.error(f"Sector performance fetch failed: {e}")
        return []

def fetch_market_news_real() -> List[Dict[str, Any]]:
    """Fetch general market news from Finnhub if API key present.
    Returns [] if not available.
    """
    if not FINNHUB_KEY:
        return []
    cache_key = 'news:general'
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    try:
        params = {'category': 'general', 'token': FINNHUB_KEY}
        resp = requests.get('https://finnhub.io/api/v1/news', params=params, timeout=10, headers={'X-Finnhub-Secret': FINNHUB_SECRET, **HEADERS})
        if resp.status_code != 200:
            logger.warning(f"Finnhub news HTTP {resp.status_code}")
            return []
        data = resp.json() or []
        normalized = []
        for art in data[:30]:  # limit
            normalized.append({
                'title': art.get('headline'),
                'text': art.get('summary'),
                'published_date': datetime.utcfromtimestamp(art.get('datetime', 0)).strftime('%Y-%m-%d') if art.get('datetime') else None,
                'symbol': None,  # could parse related
                'url': art.get('url'),
                'site': art.get('source'),
                'image': art.get('image')
            })
        _cache_set(cache_key, normalized, ttl=300)
        return normalized
    except Exception as e:
        logger.error(f"Market news fetch failed: {e}")
        return []

__all__ = [
    'fetch_economic_indicators_real',
    'fetch_crypto_fear_greed_real',
    'fetch_insider_trades_real',
    'fetch_earnings_calendar_real',
    'fetch_sector_performance_real',
    'fetch_market_news_real'
]
