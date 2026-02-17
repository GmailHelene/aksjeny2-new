import redis
import time
from flask import current_app, has_app_context
from typing import Optional
import logging
import os
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter with optional Redis support"""
    
    def __init__(self, redis_url: Optional[str] = None):
        try:
            # Configure Redis if URL is provided
            self.redis_url = redis_url or os.environ.get('REDIS_URL')
            self.redis = None
            if self.redis_url:
                self.redis = redis.from_url(self.redis_url)
                self.redis.ping()  # Test connection
                logger.info("Rate limiter using Redis backend")
            else:
                logger.info("Rate limiter using in-memory backend")
        except Exception as e:
            logger.warning(f"Redis connection failed, using in-memory rate limiting: {str(e)}")
            self.redis = None
        
        # In-memory rate limiting (fallback or default)
        self.api_calls = defaultdict(lambda: deque(maxlen=1000))
        self.api_limits = {
            'yfinance': {'calls': 2, 'per_seconds': 60},  # 2 calls per minute
            'default': {'calls': 5, 'per_seconds': 60}    # 5 calls per minute
        }
    
    def _get_app_limit(self, api_name: str) -> dict:
        """Get rate limit from app config if available"""
        if has_app_context():
            config_key = f"RATE_LIMIT_{api_name.upper()}"
            if hasattr(current_app.config, config_key):
                return current_app.config[config_key]
        return self.api_limits.get(api_name, self.api_limits['default'])
    
    def wait_if_needed(self, api_name: str = 'default') -> float:
        """
        Check if we need to wait before making another API call
        Returns the wait time in seconds (0 if no wait needed)
        """
        limit_config = self._get_app_limit(api_name)
        max_calls = limit_config['calls']
        period_seconds = limit_config['per_seconds']
        
        now = datetime.now()
        cutoff_time = now - timedelta(seconds=period_seconds)
        
        # Use Redis if available
        if self.redis:
            try:
                # Trim old entries and count recent calls
                key = f"rate_limit:{api_name}"
                self.redis.zremrangebyscore(key, 0, cutoff_time.timestamp())
                recent_calls = self.redis.zcount(key, cutoff_time.timestamp(), float('inf'))
                
                if recent_calls >= max_calls:
                    # Get oldest timestamp in window
                    oldest = self.redis.zrange(key, 0, 0, withscores=True)
                    if oldest:
                        oldest_ts = oldest[0][1]
                        wait_time = period_seconds - (now.timestamp() - oldest_ts)
                        if wait_time > 0:
                            time.sleep(wait_time)
                            return wait_time
                
                # Record this call
                self.redis.zadd(key, {now.isoformat(): now.timestamp()})
                self.redis.expire(key, period_seconds * 2)  # Set expiry
                return 0
                
            except Exception as e:
                logger.warning(f"Redis rate limiting failed, falling back to in-memory: {str(e)}")
                # Fall through to in-memory implementation
        
        # In-memory implementation
        calls = self.api_calls[api_name]
        calls = [ts for ts in calls if ts > cutoff_time]
        self.api_calls[api_name] = deque(calls, maxlen=1000)
        
        if len(calls) >= max_calls:
            # Need to wait - calculate time
            oldest_call = min(calls)
            wait_time = (oldest_call + timedelta(seconds=period_seconds) - now).total_seconds()
            if wait_time > 0:
                time.sleep(wait_time)
                return wait_time
        
        # Record this call
        self.api_calls[api_name].append(now)
        return 0

# Singleton instance
rate_limiter = RateLimiter()
