"""
Global Access Control Middleware for Aksjeradar
Redirects unauthorized users to demo/login pages
"""

from flask import request, redirect, url_for, g, current_app
from flask_login import current_user
from functools import wraps

# Protected routes that require authentication or demo access
PROTECTED_ROUTES = [
    '/stocks/',
    '/analysis/',
    '/portfolio/',
    '/news/',
    '/pricing/',
    '/admin/',
    '/features/',
    '/pro-tools/',
    '/market-intel/',
    '/backtest/',
    '/advanced/',
    '/advanced-analytics/',
    '/portfolio-advanced/'
]

# Routes that are always public (no auth required)
PUBLIC_ROUTES = [
    '/',
    '/index',
    '/login',
    '/register',
    '/demo',
    '/forgot-password',
    '/reset-password',
    '/contact',
    '/about',
    '/terms',
    '/privacy',
    '/help',
    '/service-worker.js',
    '/manifest.json',
    '/favicon.ico',
    '/static/',
    '/offline',
    '/logout'
]

def is_route_protected(path):
    """Check if a route requires authentication"""
    for protected_route in PROTECTED_ROUTES:
        if path.startswith(protected_route):
            return True
    return False

def is_route_public(path):
    """Check if a route is public"""
    for public_route in PUBLIC_ROUTES:
        if path.startswith(public_route):
            return True
    return False

def has_valid_access():
    """Check if user has valid access (logged in with subscription or demo access)"""
    if not current_user.is_authenticated:
        return False
    
    # Check if user has active subscription or demo access
    try:
        # Check for subscription status
        if hasattr(current_user, 'subscription_status'):
            if current_user.subscription_status in ['active', 'trial', 'demo']:
                return True
        
        # Check for demo access flag
        if hasattr(current_user, 'demo_access'):
            if current_user.demo_access:
                return True
                
        # Check for lifetime access
        if hasattr(current_user, 'lifetime_access'):
            if current_user.lifetime_access:
                return True
    except Exception as e:
        current_app.logger.warning(f"Error checking user access: {e}")
    
    return False

def apply_global_access_control():
    """Apply global access control before each request"""
    # Skip access control for static files and API health checks
    if (request.endpoint and 
        (request.endpoint.startswith('static') or 
         request.endpoint.endswith('health_check') or
         request.endpoint.endswith('api_status'))):
        return
    
    # Get request path
    path = request.path
    
    # Skip if route is public
    if is_route_public(path):
        return
    
    # Check if route is protected
    if is_route_protected(path):
        # Check if user has valid access
        if not has_valid_access():
            # Redirect to demo page for unauthorized access
            if not current_user.is_authenticated:
                current_app.logger.info(f"Unauthorized access to {path} - redirecting to login")
                return redirect(url_for('main.login', next=request.url))
            else:
                current_app.logger.info(f"User {current_user.id} attempted access to {path} without subscription - redirecting to demo")
                return redirect(url_for('main.demo'))

def access_required_decorator(f):
    """Decorator for routes that require authentication and subscription"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('main.login', next=request.url))
        
        if not has_valid_access():
            return redirect(url_for('main.demo'))
        
        return f(*args, **kwargs)
    return decorated_function

def demo_access_decorator(f):
    """Decorator for routes that allow demo access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('main.demo'))
        
        return f(*args, **kwargs)
    return decorated_function
