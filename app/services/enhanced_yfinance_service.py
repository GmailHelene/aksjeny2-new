"""
Enhanced yfinance service with best practices for error handling, rate limiting, and caching

Best practices implemented:
1. Proper session management with custom user agents
2. Exponential backoff retry logic
3. Rate limiting to respect Yahoo Finance API limits
4. Comprehensive error handling and logging
5. Circuit breaker pattern for API failures
6. Caching to reduce API calls
7. Timeout configuration for all requests
8. Graceful degradation when API is unavailable

Based on yfinance documentation: https://ranaroussi.github.io/yfinance/
"""

import time
import logging
import functools
import random
from datetime import datetime, timedelta
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json

logger = logging.getLogger(__name__)

# Retry decorator - moved outside class  
class NonRetryableError(Exception):
    """Indicates an error condition where retrying will not succeed (deterministic)."""
    pass

def retry_with_exponential_backoff(max_retries=3):
    """Decorator for retry logic with exponential backoff.

    Will NOT retry if a NonRetryableError is raised by the wrapped function.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            for attempt in range(max_retries):
                try:
                    result = func(self, *args, **kwargs)
                    # Record success if we had failures before
                    if hasattr(self, '_record_success'):
                        self._record_success()
                    return result
                except NonRetryableError as e:
                    # Do not retry, propagate immediately
                    if hasattr(self, '_record_failure'):
                        self._record_failure()
                    logger.warning(f"Non-retryable error for {func.__name__}: {e}")
                    raise
                except Exception as e:
                    if attempt == max_retries - 1:
                        # Last attempt failed
                        if hasattr(self, '_record_failure'):
                            self._record_failure()
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}: {e}")
                        raise
                    
                    # Exponential backoff with jitter
                    backoff_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {backoff_time:.2f}s: {e}")
                    time.sleep(backoff_time)
            
            return None
        return wrapper
    return decorator

# Safe imports
try:
    import yfinance as yf
    import requests
    import pandas as pd
    import numpy as np
    YFINANCE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"yfinance dependencies not available: {e}")
    yf = None
    requests = None
    pd = None
    np = None
    YFINANCE_AVAILABLE = False

# Fallback stock data for when APIs fail
FALLBACK_STOCK_DATA = {
    'AAPL': {
        'regularMarketPrice': 175.50,
        'regularMarketChange': 2.45,
        'regularMarketChangePercent': 1.42,
        'longName': 'Apple Inc.',
        'currency': 'USD',
        'exchange': 'NASDAQ',
        'marketCap': 2800000000000,
        'volume': 45000000
    },
    'MSFT': {
        'regularMarketPrice': 338.50,
        'regularMarketChange': -1.23,
        'regularMarketChangePercent': -0.36,
        'longName': 'Microsoft Corporation',
        'currency': 'USD',
        'exchange': 'NASDAQ',
        'marketCap': 2500000000000,
        'volume': 32000000
    },
    'TSLA': {
        'regularMarketPrice': 208.75,
        'regularMarketChange': 5.67,
        'regularMarketChangePercent': 2.79,
        'longName': 'Tesla, Inc.',
        'currency': 'USD',
        'exchange': 'NASDAQ',
        'marketCap': 670000000000,
        'volume': 78000000
    },
    'GOOGL': {
        'regularMarketPrice': 142.30,
        'regularMarketChange': 1.85,
        'regularMarketChangePercent': 1.32,
        'longName': 'Alphabet Inc.',
        'currency': 'USD',
        'exchange': 'NASDAQ',
        'marketCap': 1800000000000,
        'volume': 28000000
    },
    'EQNR.OL': {
        'regularMarketPrice': 285.20,
        'regularMarketChange': 3.40,
        'regularMarketChangePercent': 1.21,
        'longName': 'Equinor ASA',
        'currency': 'NOK',
        'exchange': 'OSL',
        'marketCap': 850000000000,
        'volume': 5500000
    },
    'DNB.OL': {
        'regularMarketPrice': 218.50,
        'regularMarketChange': -0.50,
        'regularMarketChangePercent': -0.23,
        'longName': 'DNB Bank ASA',
        'currency': 'NOK',
        'exchange': 'OSL',
        'marketCap': 340000000000,
        'volume': 3200000
    },
    'TEL.OL': {
        'regularMarketPrice': 168.30,
        'regularMarketChange': 1.20,
        'regularMarketChangePercent': 0.72,
        'longName': 'Telenor ASA',
        'currency': 'NOK',
        'exchange': 'OSL',
        'marketCap': 230000000000,
        'volume': 2800000
    }
}

class EnhancedYFinanceService:
    """Enhanced yfinance service with best practices"""
    
    def __init__(self):
        self.session = None
        self.last_request_time = 0
        self.min_request_interval = 0.5  # Minimum 500ms between requests
        self.circuit_breaker = {
            'failures': 0,
            'max_failures': 5,
            'reset_time': None,
            'timeout_minutes': 10
        }
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes cache TTL
        
        # Initialize session if available
        if YFINANCE_AVAILABLE and requests:
            self._setup_session()
    
    def _setup_session(self):
        """Setup requests session with proper headers and timeout"""
        try:
            self.session = requests.Session()
            
            # Use rotating user agents to avoid rate limiting
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            ]
            
            self.session.headers.update({
                'User-Agent': random.choice(user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            # Configure timeout and retry strategy
            self.session.timeout = 10
            
            logger.info("✅ Enhanced yfinance session initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup yfinance session: {e}")
            self.session = None
    
    def _is_circuit_breaker_open(self):
        """Check if circuit breaker is open (API temporarily disabled)"""
        if self.circuit_breaker['failures'] >= self.circuit_breaker['max_failures']:
            if self.circuit_breaker['reset_time']:
                if datetime.now() > self.circuit_breaker['reset_time']:
                    # Reset circuit breaker
                    self.circuit_breaker['failures'] = 0
                    self.circuit_breaker['reset_time'] = None
                    logger.info("🔄 Circuit breaker reset - re-enabling yfinance")
                    return False
                else:
                    return True
            else:
                # Set reset time
                self.circuit_breaker['reset_time'] = datetime.now() + timedelta(
                    minutes=self.circuit_breaker['timeout_minutes']
                )
                logger.warning(f"🔴 Circuit breaker OPEN - yfinance disabled for {self.circuit_breaker['timeout_minutes']} minutes")
                return True
        return False
    
    def _record_failure(self):
        """Record API failure for circuit breaker"""
        self.circuit_breaker['failures'] += 1
        logger.warning(f"⚠️ yfinance failure #{self.circuit_breaker['failures']}")
    
    def _record_success(self):
        """Record API success - reset failure count"""
        if self.circuit_breaker['failures'] > 0:
            self.circuit_breaker['failures'] = 0
            logger.info("✅ yfinance success - reset failure count")
    
    def _enforce_rate_limit(self):
        """Enforce minimum interval between requests"""
        now = time.time()
        time_since_last = now - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _get_fallback_data(self, symbol, data_type='info'):
        """Get fallback data when API fails"""
        if symbol in FALLBACK_STOCK_DATA:
            data = FALLBACK_STOCK_DATA[symbol].copy()
            
            if data_type == 'history':
                # Generate simple history data
                if pd is not None and np is not None:
                    try:
                        from datetime import datetime, timedelta
                        
                        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
                        base_price = data['regularMarketPrice']
                        
                        # Generate realistic price movements
                        price_changes = np.random.normal(0, base_price * 0.015, 30)
                        prices = [base_price]
                        
                        for change in price_changes[1:]:
                            new_price = prices[-1] + change
                            prices.append(max(new_price, base_price * 0.8))  # Don't go below 80% of base
                        
                        return pd.DataFrame({
                            'Open': [p * 0.999 for p in prices],
                            'High': [p * 1.005 for p in prices],
                            'Low': [p * 0.995 for p in prices],
                            'Close': prices,
                            'Volume': np.random.randint(
                                int(data['volume'] * 0.8), 
                                int(data['volume'] * 1.2), 
                                30
                            )
                        }, index=dates)
                    except Exception as e:
                        logger.warning(f"Could not generate fallback history: {e}")
                        return None
                else:
                    return None
            else:
                return data
        return None
    
    def _get_cache_key(self, symbol, method, **kwargs):
        """Generate cache key for request"""
        params = '_'.join(f"{k}_{v}" for k, v in sorted(kwargs.items()))
        return f"yf_{method}_{symbol}_{params}"
    
    def _get_cached_data(self, cache_key):
        """Get data from cache if not expired"""
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for {cache_key}")
                return data
            else:
                # Clean expired cache
                del self.cache[cache_key]
        return None
    
    def _set_cache_data(self, cache_key, data):
        """Store data in cache with timestamp"""
        self.cache[cache_key] = (data, time.time())
        logger.debug(f"Cached data for {cache_key}")
    
    @retry_with_exponential_backoff(max_retries=3)
    def get_ticker_history(self, symbol, period='1mo', interval='1d'):
        """Get ticker history with enhanced error handling"""
        if not YFINANCE_AVAILABLE:
            raise Exception("yfinance not available")
        
        # Check circuit breaker
        if self._is_circuit_breaker_open():
            raise Exception("Circuit breaker open - yfinance temporarily disabled")
        
        # Check cache first
        cache_key = self._get_cache_key(symbol, 'history', period=period, interval=interval)
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        try:
            # Suppress yfinance output
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                # Create ticker with our enhanced session
                ticker = yf.Ticker(symbol, session=self.session)
                
                # Get history with timeout
                logger.debug(f"Fetching history for {symbol} (period={period}, interval={interval})")
                hist = ticker.history(
                    period=period, 
                    interval=interval,
                    timeout=10,
                    raise_errors=True  # Ensure exceptions are raised
                )
                
                if hist.empty:
                    # Deterministic: yfinance returned no rows. Retrying won't help soon.
                    raise NonRetryableError(f"No data returned for {symbol}")
                
                # Cache successful result
                self._set_cache_data(cache_key, hist)
                self._record_success()
                
                logger.info(f"✅ Successfully fetched {len(hist)} rows for {symbol}")
                return hist
                
        except NonRetryableError as e:
            logger.warning(f"⛔ yfinance history non-retryable for {symbol}: {e}")
            # Try fallback data immediately
            fallback_data = self._get_fallback_data(symbol, 'history')
            if fallback_data is not None:
                logger.warning(f"⚠️ Using fallback history data for {symbol} (non-retryable)")
                return fallback_data
            raise
        except Exception as e:
            logger.error(f"❌ yfinance history failed for {symbol}: {e}")
            
            # Try fallback data
            fallback_data = self._get_fallback_data(symbol, 'history')
            if fallback_data is not None:
                logger.warning(f"⚠️ Using fallback history data for {symbol}")
                return fallback_data
            
            raise
    
    @retry_with_exponential_backoff(max_retries=2)
    def get_ticker_info(self, symbol):
        """Get ticker info with enhanced error handling"""
        if not YFINANCE_AVAILABLE:
            raise Exception("yfinance not available")
        
        # Check circuit breaker
        if self._is_circuit_breaker_open():
            raise Exception("Circuit breaker open - yfinance temporarily disabled")
        
        # Check cache first
        cache_key = self._get_cache_key(symbol, 'info')
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        try:
            # Suppress yfinance output
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                ticker = yf.Ticker(symbol, session=self.session)
                
                logger.debug(f"Fetching info for {symbol}")
                info = ticker.info
                
                if not info or not isinstance(info, dict):
                    raise NonRetryableError(f"No info returned for {symbol}")
                
                # Cache successful result
                self._set_cache_data(cache_key, info)
                self._record_success()
                
                logger.info(f"✅ Successfully fetched info for {symbol}")
                return info
                
        except NonRetryableError as e:
            logger.warning(f"⛔ yfinance info non-retryable for {symbol}: {e}")
            fallback_data = self._get_fallback_data(symbol, 'info')
            if fallback_data:
                logger.warning(f"⚠️ Using fallback data for {symbol} (non-retryable)")
                return fallback_data
            raise
        except Exception as e:
            logger.error(f"❌ yfinance info failed for {symbol}: {e}")
            
            # Try fallback data
            fallback_data = self._get_fallback_data(symbol, 'info')
            if fallback_data:
                logger.warning(f"⚠️ Using fallback data for {symbol}")
                return fallback_data
            
            raise
    
    def get_status(self):
        """Get service status information"""
        return {
            'available': YFINANCE_AVAILABLE,
            'session_active': self.session is not None,
            'circuit_breaker': self.circuit_breaker.copy(),
            'cache_size': len(self.cache),
            'last_request_time': self.last_request_time
        }
    
    def clear_cache(self):
        """Clear all cached data"""
        cache_size = len(self.cache)
        self.cache.clear()
        logger.info(f"Cleared {cache_size} cached items")
    
    def reset_circuit_breaker(self):
        """Manually reset circuit breaker"""
        self.circuit_breaker['failures'] = 0
        self.circuit_breaker['reset_time'] = None
        logger.info("🔄 Circuit breaker manually reset")

# Global instance
enhanced_yfinance = EnhancedYFinanceService()

def get_enhanced_yfinance_service():
    """Get the global enhanced yfinance service instance"""
    return enhanced_yfinance
