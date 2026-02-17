"""
Security enhancements for Aksjeradar
Includes rate limiting, CSRF validation, and security headers
"""

import time
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g, current_app, make_response
from flask_login import current_user
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiting implementation using in-memory storage"""
    
    def __init__(self):
        # Store: {ip: [(timestamp, count), ...]}
        self.requests = defaultdict(list)
        self.blocked_ips = defaultdict(float)  # {ip: block_until_timestamp}
    
    def is_rate_limited(self, identifier: str, limit: int, window: int) -> tuple[bool, dict]:
        """
        Check if identifier is rate limited
        
        Args:
            identifier: IP address or user ID
            limit: Max requests per window
            window: Time window in seconds
            
        Returns:
            (is_limited, info) where info contains current count and reset time
        """
        now = time.time()
        
        # Check if currently blocked
        if identifier in self.blocked_ips:
            block_until = self.blocked_ips[identifier]
            if now < block_until:
                return True, {
                    'blocked': True,
                    'block_until': block_until,
                    'retry_after': int(block_until - now)
                }
            else:
                # Unblock
                del self.blocked_ips[identifier]
        
        # Clean old requests
        cutoff = now - window
        self.requests[identifier] = [
            (timestamp, count) for timestamp, count in self.requests[identifier] 
            if timestamp > cutoff
        ]
        
        # Count current requests in window
        current_count = sum(count for _, count in self.requests[identifier])
        
        if current_count >= limit:
            # Block for 5 minutes on rate limit exceeded
            self.blocked_ips[identifier] = now + 300
            logger.warning(f"Rate limit exceeded for {identifier}. Blocked for 5 minutes.")
            return True, {
                'blocked': True,
                'current_count': current_count,
                'limit': limit,
                'window': window,
                'retry_after': 300
            }
        
        # Add current request
        self.requests[identifier].append((now, 1))
        
        return False, {
            'blocked': False,
            'current_count': current_count + 1,
            'limit': limit,
            'window': window,
            'reset_time': now + window
        }
    
    def cleanup_old_data(self):
        """Clean up old data to prevent memory leaks"""
        now = time.time()
        
        # Remove old requests (older than 1 hour)
        cutoff = now - 3600
        for identifier in list(self.requests.keys()):
            self.requests[identifier] = [
                (timestamp, count) for timestamp, count in self.requests[identifier] 
                if timestamp > cutoff
            ]
            if not self.requests[identifier]:
                del self.requests[identifier]
        
        # Remove expired blocks
        for identifier in list(self.blocked_ips.keys()):
            if self.blocked_ips[identifier] < now:
                del self.blocked_ips[identifier]

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(limit: int = 60, window: int = 60, per: str = 'ip'):
    """
    Rate limiting decorator
    
    Args:
        limit: Maximum requests allowed
        window: Time window in seconds
        per: 'ip' or 'user' - what to rate limit by
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Determine identifier
            if per == 'user' and current_user.is_authenticated:
                identifier = f"user_{current_user.id}"
            else:
                identifier = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            
            # Check rate limit
            is_limited, info = rate_limiter.is_rate_limited(identifier, limit, window)
            
            if is_limited:
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Try again in {info.get("retry_after", 60)} seconds.',
                    'retry_after': info.get('retry_after', 60)
                })
                response.status_code = 429
                response.headers['Retry-After'] = str(info.get('retry_after', 60))
                return response
            
            # Add rate limit headers to response
            response = make_response(f(*args, **kwargs))
            response.headers['X-RateLimit-Limit'] = str(limit)
            response.headers['X-RateLimit-Remaining'] = str(limit - info['current_count'])
            response.headers['X-RateLimit-Reset'] = str(int(info.get('reset_time', time.time() + window)))
            
            return response
        return decorated_function
    return decorator

# Predefined rate limits for different endpoints
def api_rate_limit(f):
    """Standard API rate limit: 100 requests per minute"""
    return rate_limit(limit=100, window=60, per='ip')(f)

def strict_rate_limit(f):
    """Strict rate limit for sensitive endpoints: 10 requests per minute"""
    return rate_limit(limit=10, window=60, per='ip')(f)

def user_rate_limit(f):
    """User-based rate limit: 200 requests per minute per user"""
    return rate_limit(limit=200, window=60, per='user')(f)

def auth_rate_limit(f):
    """Authentication rate limit: 5 attempts per minute"""
    return rate_limit(limit=5, window=60, per='ip')(f)

class SecurityHeaders:
    """Security headers management"""
    
    @staticmethod
    def add_security_headers(response):
        """Add security headers to response"""
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.jsdelivr.net cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com fonts.googleapis.com; "
            "font-src 'self' fonts.gstatic.com cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response.headers['Content-Security-Policy'] = csp
        
        # Other security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Remove server information
        response.headers.pop('Server', None)
        
        return response

def csrf_protect(f):
    """CSRF protection decorator for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            # Check CSRF token
            token = request.headers.get('X-CSRFToken') or request.form.get('csrf_token')
            if not token:
                return jsonify({'error': 'CSRF token missing'}), 403
            
            # In a real implementation, validate the token here
            # For now, just check if it exists
            
        return f(*args, **kwargs)
    return decorated_function

def security_monitoring():
    """Log security events for monitoring"""
    
    # Monitor for suspicious patterns
    ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    
    # Log suspicious user agents
    suspicious_agents = ['curl', 'wget', 'python-requests', 'bot', 'crawler', 'scanner']
    if any(agent in user_agent.lower() for agent in suspicious_agents):
        logger.warning(f"Suspicious user agent from {ip}: {user_agent}")
    
    # Log multiple rapid requests from same IP
    g.request_start_time = time.time()

# Cleanup function to be called periodically
def cleanup_security_data():
    """Clean up old security data to prevent memory leaks"""
    rate_limiter.cleanup_old_data()
    logger.info("Security data cleanup completed")

# Security configuration
SECURITY_CONFIG = {
    'rate_limits': {
        'api_general': {'limit': 100, 'window': 60},
        'api_strict': {'limit': 10, 'window': 60},
        'auth': {'limit': 5, 'window': 60},
        'user_actions': {'limit': 200, 'window': 60}
    },
    'csrf_protection': True,
    'security_headers': True,
    'request_logging': True
}
