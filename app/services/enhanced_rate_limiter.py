"""
Enhanced Rate Limiter with Circuit Breaker for Yahoo Finance API
Reduces 429 errors and improves reliability
"""
import time
import logging
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EnhancedRateLimiter:
    """Rate limiter with circuit breaker pattern for API resilience"""
    
    def __init__(self):
        self.requests = {}  # service_name -> list of request timestamps
        self.circuit_breakers = {}  # service_name -> circuit breaker state
        self.rate_limits = {
            'yahoo_finance': {
                'max_requests': 100,  # Very conservative
                'time_window': 3600,  # 1 hour
                'backoff_seconds': 60,  # Wait 1 minute between requests when rate limited
                'circuit_breaker': {
                    'failure_threshold': 5,  # Open circuit after 5 failures
                    'recovery_timeout': 300,  # Try to recover after 5 minutes
                    'success_threshold': 3   # Close circuit after 3 successes
                }
            },
            'default': {
                'max_requests': 1000,
                'time_window': 3600,
                'backoff_seconds': 1,
                'circuit_breaker': {
                    'failure_threshold': 10,
                    'recovery_timeout': 60,
                    'success_threshold': 5
                }
            }
        }
        
    def can_make_request(self, service_name: str = 'default') -> Tuple[bool, float]:
        """Check if request can be made, returns (can_request, wait_time)"""
        try:
            # Check circuit breaker first
            if self.is_circuit_open(service_name):
                recovery_time = self._get_circuit_recovery_time(service_name)
                if recovery_time > 0:
                    return False, recovery_time
                else:
                    # Try to half-open the circuit
                    self._set_circuit_half_open(service_name)
            
            # Get rate limit configuration
            config = self.rate_limits.get(service_name, self.rate_limits['default'])
            current_time = time.time()
            
            # Initialize request history if needed
            if service_name not in self.requests:
                self.requests[service_name] = []
            
            # Clean old requests outside time window
            cutoff_time = current_time - config['time_window']
            self.requests[service_name] = [
                req_time for req_time in self.requests[service_name] 
                if req_time > cutoff_time
            ]
            
            # Check if under rate limit
            if len(self.requests[service_name]) < config['max_requests']:
                return True, 0
            else:
                # Calculate wait time
                oldest_request = min(self.requests[service_name])
                wait_time = oldest_request + config['time_window'] - current_time
                return False, max(0, wait_time)
                
        except Exception as e:
            logger.error(f"Error in rate limiter for {service_name}: {e}")
            return True, 0  # Fail open
    
    def record_request(self, service_name: str = 'default'):
        """Record a successful request"""
        try:
            current_time = time.time()
            if service_name not in self.requests:
                self.requests[service_name] = []
            
            self.requests[service_name].append(current_time)
            
            # Record success for circuit breaker
            self.record_success(service_name)
            
        except Exception as e:
            logger.error(f"Error recording request for {service_name}: {e}")
    
    def record_failure(self, service_name: str = 'default', error_type: str = 'unknown'):
        """Record a failed request for circuit breaker"""
        try:
            current_time = time.time()
            
            if service_name not in self.circuit_breakers:
                self.circuit_breakers[service_name] = {
                    'state': 'closed',  # closed, open, half-open
                    'failure_count': 0,
                    'last_failure_time': None,
                    'success_count': 0
                }
            
            breaker = self.circuit_breakers[service_name]
            breaker['failure_count'] += 1
            breaker['last_failure_time'] = current_time
            breaker['success_count'] = 0  # Reset success count on failure
            
            # Check if we should open the circuit
            config = self.rate_limits.get(service_name, self.rate_limits['default'])
            if breaker['failure_count'] >= config['circuit_breaker']['failure_threshold']:
                breaker['state'] = 'open'
                logger.warning(f"Circuit breaker OPENED for {service_name} after {breaker['failure_count']} failures")
                
                # Special handling for rate limit errors
                if '429' in error_type or 'rate limit' in error_type.lower():
                    # Longer backoff for rate limit errors
                    breaker['last_failure_time'] = current_time + config['circuit_breaker']['recovery_timeout']
                    logger.warning(f"Extended backoff for rate limit error on {service_name}")
            
        except Exception as e:
            logger.error(f"Error recording failure for {service_name}: {e}")
    
    def record_success(self, service_name: str = 'default'):
        """Record a successful request for circuit breaker"""
        try:
            if service_name not in self.circuit_breakers:
                self.circuit_breakers[service_name] = {
                    'state': 'closed',
                    'failure_count': 0,
                    'last_failure_time': None,
                    'success_count': 0
                }
            
            breaker = self.circuit_breakers[service_name]
            breaker['success_count'] += 1
            
            # Check if we should close the circuit
            config = self.rate_limits.get(service_name, self.rate_limits['default'])
            if (breaker['state'] == 'half-open' and 
                breaker['success_count'] >= config['circuit_breaker']['success_threshold']):
                breaker['state'] = 'closed'
                breaker['failure_count'] = 0
                breaker['success_count'] = 0
                logger.info(f"Circuit breaker CLOSED for {service_name} after successful requests")
            
        except Exception as e:
            logger.error(f"Error recording success for {service_name}: {e}")
    
    def is_circuit_open(self, service_name: str = 'default') -> bool:
        """Check if circuit breaker is open"""
        try:
            if service_name not in self.circuit_breakers:
                return False
            
            breaker = self.circuit_breakers[service_name]
            return breaker['state'] == 'open'
            
        except Exception as e:
            logger.error(f"Error checking circuit breaker for {service_name}: {e}")
            return False
    
    def _get_circuit_recovery_time(self, service_name: str) -> float:
        """Get time until circuit can attempt recovery"""
        try:
            if service_name not in self.circuit_breakers:
                return 0
            
            breaker = self.circuit_breakers[service_name]
            if breaker['state'] != 'open' or not breaker['last_failure_time']:
                return 0
            
            config = self.rate_limits.get(service_name, self.rate_limits['default'])
            recovery_time = breaker['last_failure_time'] + config['circuit_breaker']['recovery_timeout']
            current_time = time.time()
            
            return max(0, recovery_time - current_time)
            
        except Exception as e:
            logger.error(f"Error calculating recovery time for {service_name}: {e}")
            return 0
    
    def _set_circuit_half_open(self, service_name: str):
        """Set circuit to half-open state for testing"""
        try:
            if service_name in self.circuit_breakers:
                self.circuit_breakers[service_name]['state'] = 'half-open'
                self.circuit_breakers[service_name]['success_count'] = 0
                logger.info(f"Circuit breaker set to HALF-OPEN for {service_name}")
                
        except Exception as e:
            logger.error(f"Error setting circuit half-open for {service_name}: {e}")
    
    def get_status(self, service_name: str = 'default') -> Dict:
        """Get current status for monitoring"""
        try:
            current_time = time.time()
            
            # Request rate info
            if service_name in self.requests:
                config = self.rate_limits.get(service_name, self.rate_limits['default'])
                cutoff_time = current_time - config['time_window']
                recent_requests = [
                    req_time for req_time in self.requests[service_name] 
                    if req_time > cutoff_time
                ]
                request_count = len(recent_requests)
            else:
                request_count = 0
            
            # Circuit breaker info
            if service_name in self.circuit_breakers:
                breaker = self.circuit_breakers[service_name]
                circuit_info = {
                    'state': breaker['state'],
                    'failure_count': breaker['failure_count'],
                    'success_count': breaker['success_count'],
                    'last_failure': breaker['last_failure_time']
                }
            else:
                circuit_info = {
                    'state': 'closed',
                    'failure_count': 0,
                    'success_count': 0,
                    'last_failure': None
                }
            
            can_request, wait_time = self.can_make_request(service_name)
            
            return {
                'service_name': service_name,
                'can_make_request': can_request,
                'wait_time': wait_time,
                'recent_requests': request_count,
                'circuit_breaker': circuit_info,
                'timestamp': current_time
            }
            
        except Exception as e:
            logger.error(f"Error getting status for {service_name}: {e}")
            return {'error': str(e)}
    
    def wait_if_needed(self, service_name: str = 'default', max_wait: float = 60) -> bool:
        """Wait if rate limited, returns True if wait completed, False if wait too long"""
        try:
            can_request, wait_time = self.can_make_request(service_name)
            
            if can_request:
                return True
            
            if wait_time > max_wait:
                logger.warning(f"Wait time {wait_time}s exceeds max wait {max_wait}s for {service_name}")
                return False
            
            if wait_time > 0:
                logger.info(f"Rate limited: waiting {wait_time:.1f}s for {service_name}")
                time.sleep(wait_time)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in wait_if_needed for {service_name}: {e}")
            return True  # Fail open

# Global instance
enhanced_rate_limiter = EnhancedRateLimiter()
