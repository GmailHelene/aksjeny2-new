"""
YFinance API rate limiting and retry mechanism
"""
import time
import logging
from functools import wraps
import random

logger = logging.getLogger(__name__)

class YFinanceRateLimiter:
    """Rate limiter for YFinance API to handle 429 errors"""
    
    def __init__(self):
        self.last_request_time = 0
        self.request_count = 0
        self.reset_time = 0
        self.min_delay = 1.0  # Minimum delay between requests
        self.max_retries = 3
        
    def wait_if_needed(self):
        """Wait if we need to respect rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last
            logger.info(f"Rate limiting: waiting {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        
    def handle_429_error(self, attempt):
        """Handle 429 rate limit error with exponential backoff"""
        if attempt >= self.max_retries:
            logger.error("Max retries exceeded for YFinance API")
            return False
            
        # Exponential backoff with jitter
        delay = (2 ** attempt) + random.uniform(0, 1)
        logger.warning(f"YFinance 429 error, retrying in {delay:.2f} seconds (attempt {attempt + 1}/{self.max_retries})")
        time.sleep(delay)
        return True

# Global rate limiter instance
rate_limiter = YFinanceRateLimiter()

def yfinance_retry(func):
    """Decorator to add retry logic and rate limiting to YFinance calls"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        for attempt in range(rate_limiter.max_retries):
            try:
                # Wait if needed for rate limiting
                rate_limiter.wait_if_needed()
                
                # Call the function
                result = func(*args, **kwargs)
                return result
                
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a 429 rate limit error
                if "429" in error_msg or "Too Many Requests" in error_msg:
                    if not rate_limiter.handle_429_error(attempt):
                        # Max retries exceeded, return fallback
                        logger.error(f"YFinance API rate limit exceeded for {func.__name__}")
                        return None
                    continue
                    
                # Check for other common YFinance errors
                elif "No data found" in error_msg or "404" in error_msg:
                    logger.warning(f"YFinance: No data found for {func.__name__}")
                    return None
                    
                # For other errors, log and return None
                else:
                    logger.error(f"YFinance API error in {func.__name__}: {e}")
                    return None
        
        # If we get here, all retries failed
        logger.error(f"All retries failed for {func.__name__}")
        return None
    
    return wrapper

def get_fallback_data(ticker):
    """Provide fallback data when YFinance fails"""
    return {
        'ticker': ticker,
        'last_price': 100.0,
        'change': 0.0,
        'change_percent': 0.0,
        'volume': 0,
        'name': ticker,
        'signal': 'HOLD',
        'market_cap': 0,
        'error': 'API rate limited - showing fallback data'
    }
