"""
Rate limiting service to prevent API abuse
"""
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter to manage API call frequency"""
    
    def __init__(self):
        self.api_calls = defaultdict(deque)
        self.limits = {
            'yahoo_finance': {
                'requests_per_minute': 2,   # Ultra conservative - 2 per minute
                'requests_per_hour': 30,    # Only 30 per hour to avoid 429
                'delay_between_calls': 20.0, # 20 seconds between calls
                'burst_delay': 30.0        # 30 seconds after bursts
            },
            'yfinance': {
                'requests_per_minute': 2,   # Same ultra conservative limits
                'requests_per_hour': 30,    
                'delay_between_calls': 20.0,
                'burst_delay': 30.0        
            },
            'default': {
                'requests_per_minute': 100,
                'requests_per_hour': 3000,
                'delay_between_calls': 0.5,
                'burst_delay': 1.0
            }
        }
        self.circuit_breaker = {
            'yahoo_finance': {
                'failure_count': 0,
                'last_failure': None,
                'circuit_open': False,
                'recovery_time': 600  # 10 minutes recovery time
            }
        }
        self.last_call_time = {}
    
    def can_make_request(self, api_name='default'):
        """Check if we can make a request to the API"""
        now = datetime.now()
        limits = self.limits.get(api_name, self.limits['default'])
        
        # Check minimum delay between calls
        last_call = self.last_call_time.get(api_name)
        if last_call:
            time_since_last = (now - last_call).total_seconds()
            if time_since_last < limits['delay_between_calls']:
                return False, limits['delay_between_calls'] - time_since_last
        
        # Clean old entries
        calls = self.api_calls[api_name]
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        # Remove calls older than an hour
        while calls and calls[0] < hour_ago:
            calls.popleft()
        
        # Count calls in the last minute and hour
        calls_last_minute = sum(1 for call_time in calls if call_time > minute_ago)
        calls_last_hour = len(calls)
        
        # Check limits
        if calls_last_minute >= limits['requests_per_minute']:
            return False, 60 - (now - minute_ago).total_seconds()
        
        if calls_last_hour >= limits['requests_per_hour']:
            return False, 3600 - (now - hour_ago).total_seconds()
        
        return True, 0
    
    def record_request(self, api_name='default'):
        """Record that a request was made"""
        now = datetime.now()
        self.api_calls[api_name].append(now)
        self.last_call_time[api_name] = now
        logger.debug(f"Recorded {api_name} API call at {now}")
    
    def wait_if_needed(self, api_name='default'):
        """Wait if necessary before making a request"""
        can_request, wait_time = self.can_make_request(api_name)
        if not can_request:
            logger.info(f"Rate limit reached for {api_name}, waiting {wait_time:.2f} seconds")
            time.sleep(wait_time + 0.1)  # Add small buffer
        
        self.record_request(api_name)
    
    def record_429_error(self, api_name='default'):
        """Record a 429 error and implement circuit breaker logic"""
        if api_name not in self.circuit_breaker:
            return
            
        breaker = self.circuit_breaker[api_name]
        breaker['failure_count'] += 1
        breaker['last_failure'] = datetime.now()
        
        # Open circuit if too many failures
        if breaker['failure_count'] >= 2:  # Lower threshold
            breaker['circuit_open'] = True
            logger.warning(f"Circuit breaker opened for {api_name} due to repeated 429 errors")
    
    def is_circuit_open(self, api_name='default'):
        """Check if circuit breaker is open"""
        if api_name not in self.circuit_breaker:
            return False
            
        breaker = self.circuit_breaker[api_name]
        if not breaker['circuit_open']:
            return False
            
        # Check if recovery time has passed
        if breaker['last_failure']:
            time_since_failure = (datetime.now() - breaker['last_failure']).total_seconds()
            if time_since_failure > breaker['recovery_time']:
                # Reset circuit breaker
                breaker['circuit_open'] = False
                breaker['failure_count'] = 0
                logger.info(f"Circuit breaker reset for {api_name}")
                return False
                
        return True
    
    def record_success(self, api_name='default'):
        """Record a successful request"""
        if api_name in self.circuit_breaker:
            # Reset failure count on success
            self.circuit_breaker[api_name]['failure_count'] = 0
    
    def reset_circuit_breaker(self, api_name='default'):
        """Manually reset circuit breaker for an API"""
        if api_name in self.circuit_breaker:
            breaker = self.circuit_breaker[api_name]
            breaker['circuit_open'] = False
            breaker['failure_count'] = 0
            breaker['last_failure'] = None
            logger.info(f"Circuit breaker manually reset for {api_name}")
            return True
        return False
    
    def get_circuit_status(self, api_name='default'):
        """Get current circuit breaker status"""
        if api_name not in self.circuit_breaker:
            return {'status': 'not_configured'}
        
        breaker = self.circuit_breaker[api_name]
        return {
            'status': 'open' if breaker['circuit_open'] else 'closed',
            'failure_count': breaker['failure_count'],
            'last_failure': breaker['last_failure'],
            'recovery_time': breaker['recovery_time']
        }

# Global rate limiter instance
rate_limiter = RateLimiter()
