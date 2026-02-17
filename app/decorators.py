# Decorators module for access control and functionality
from functools import wraps
from flask import current_app, request, jsonify, redirect, url_for
from flask_login import current_user
import logging

logger = logging.getLogger(__name__)

# Re-export csrf_protect from security service for convenience
try:
    from .services.security_service import csrf_protect  # type: ignore
except Exception:
    # Fallback no-op if security service isn't available during early imports
    def csrf_protect(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated

def demo_access(f):
    """Legacy demo_access decorator (no-op).
    Historically used to gate demo-only routes. We keep it as a no-op so
    imports across blueprints don't fail, while EKTE-only enforcement happens
    inside the route implementations.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated

def access_required(f):
    """
    Decorator that checks if user has access to premium features.
    Falls back gracefully if subscription check fails.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # If user is not logged in, require login
            if not current_user.is_authenticated:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                return redirect(url_for('auth.login'))
            
            # Check if user has premium access
            if hasattr(current_user, 'has_premium_access') and current_user.has_premium_access():
                return f(*args, **kwargs)
            
            # Check exempt emails
            exempt_emails = current_app.config.get('EXEMPT_EMAILS', [])
            if current_user.email in exempt_emails:
                return f(*args, **kwargs)
            
            # For JSON/API requests, return JSON error instead of redirect
            is_api_request = (request.is_json or 
                              '/api/' in request.path or 
                              request.content_type and 'application/json' in request.content_type or
                              request.headers.get('Accept', '').find('application/json') != -1)
            
            if is_api_request:
                return jsonify({
                    'error': 'Premium access required',
                    'message': 'This feature requires a premium subscription'
                }), 403
            
            # For regular requests, redirect to pricing
            try:
                return redirect(url_for('pricing.index'))
            except:
                # Fallback to demo if pricing route doesn't exist
                return redirect(url_for('main.demo'))
            
        except Exception as e:
            logger.warning(f"Access check failed: {e}")
            # Fail open - allow access if check fails
            return f(*args, **kwargs)
    
    return decorated_function