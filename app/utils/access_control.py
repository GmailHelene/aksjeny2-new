"""
Unified trial and access control system for Aksjeradar
This replaces the multiple overlapping trial/restriction systems with a single, clean approach.
"""
from functools import wraps
from flask import jsonify, redirect, url_for, flash, request, session, current_app
from flask_login import current_user
from datetime import datetime, timedelta
from dateutil.parser import isoparse
import hashlib

# Exempt users who always get full access
EXEMPT_EMAILS = {
    'testuser@aksjeradar.trade', 
    'helene721@gmail.com', 
    'tonjekit91@gmail.com'
}

# Trial duration in minutes (15 minutes)
TRIAL_DURATION_MINUTES = 15

def api_login_required(f):
    """API-specific decorator that requires login and returns JSON responses"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import jsonify
        
        if not current_user.is_authenticated:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please log in to access this resource.',
                'code': 'LOGIN_REQUIRED'
            }), 401
            
        return f(*args, **kwargs)
    return decorated_function

def api_access_required(f):
    """API-specific decorator that returns JSON responses instead of redirects"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        import logging
        from flask import current_app, jsonify
        
        # First check if this is an exempt endpoint that should always be accessible
        if hasattr(current_app, 'config') and 'EXEMPT_ENDPOINTS' in current_app.config:
            exempt_endpoints = current_app.config.get('EXEMPT_ENDPOINTS', set())
            if request.endpoint in exempt_endpoints:
                return f(*args, **kwargs)
                
        logging.warning(f"[API_ACCESS_REQUIRED] Called for endpoint={request.endpoint} url={request.url} user_authenticated={current_user.is_authenticated}")
        
        # For authenticated users
        if current_user.is_authenticated:
            # Exempt users always have access
            if getattr(current_user, 'email', None) in EXEMPT_EMAILS:
                return f(*args, **kwargs)
                
            # Users with active subscription have access
            if hasattr(current_user, 'has_active_subscription') and current_user.has_active_subscription():
                return f(*args, **kwargs)
                
            # Check if user is in initial subscription period (10 minutes)
            if hasattr(current_user, 'subscription_start') and current_user.subscription_start:
                if datetime.utcnow() - current_user.subscription_start < timedelta(minutes=10):
                    return f(*args, **kwargs)
                    
            # No valid subscription - return JSON error instead of redirect
            return jsonify({
                'error': 'Access denied',
                'message': 'Your subscription has expired or is not active. Please upgrade to continue.',
                'code': 'SUBSCRIPTION_REQUIRED'
            }), 403
            
        # For unauthenticated users
        else:
            # Check trial status
            trial_status = _check_trial_access()
            
            if trial_status.get('active'):
                logging.warning("[API_ACCESS_REQUIRED] Trial active, allowing access.")
                return f(*args, **kwargs)
                
            # If trial is expired or not started, return JSON error instead of redirect
            logging.warning("[API_ACCESS_REQUIRED] Trial expired or not started, returning JSON error")
            return jsonify({
                'error': 'Access denied',
                'message': 'Trial has expired. Please sign up to continue.',
                'code': 'TRIAL_EXPIRED'
            }), 401
    
    return decorated_function

def access_required(f):
    """Decorator to check if user has access to the resource"""
    @wraps(f)

    def decorated_function(*args, **kwargs):
        import logging
        from flask import current_app
        
        # First check if this is an exempt endpoint that should always be accessible
        if hasattr(current_app, 'config') and 'EXEMPT_ENDPOINTS' in current_app.config:
            exempt_endpoints = current_app.config.get('EXEMPT_ENDPOINTS', set())
            if request.endpoint in exempt_endpoints:
                return f(*args, **kwargs)
                
        # Only log warnings for actual access denials, not all requests
        # logging.warning(f"[ACCESS_REQUIRED] Called for endpoint={request.endpoint} url={request.url} user_authenticated={current_user.is_authenticated}")
        
        # For authenticated users
        if current_user.is_authenticated:
            # Exempt users always have access
            if getattr(current_user, 'email', None) in EXEMPT_EMAILS:
                return f(*args, **kwargs)
                
            # Users with active subscription have access
            if hasattr(current_user, 'has_active_subscription') and current_user.has_active_subscription():
                return f(*args, **kwargs)
                
            # Check if user is in initial subscription period (10 minutes)
            if hasattr(current_user, 'subscription_start') and current_user.subscription_start:
                if datetime.utcnow() - current_user.subscription_start < timedelta(minutes=10):
                    return f(*args, **kwargs)
                    
            # For authenticated users, allow access to basic functionality
            # This includes sentiment analysis, portfolio tips, and core features
            return f(*args, **kwargs)
            
        # For unauthenticated users - redirect directly to demo
        else:
            # All unauthenticated users should go to demo page
            from flask import redirect
            logging.warning(f"[ACCESS_REQUIRED] Unauthenticated user, redirecting to demo")
            return redirect('/demo?source=login_required')
    
    return decorated_function

def premium_required(f):
    """Decorator for premium-only features"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access premium features.', 'info')
            return redirect('/login')
        
        # Exempt emails always have access
        if current_user.email in EXEMPT_EMAILS:
            return f(*args, **kwargs)

        # Explicit deny list: ensure specific users can never escalate unintentionally
        DENY_PREMIUM_EMAILS = {
            'eiriktollan.berntsen@gmail.com',
            'eirik@aksjeradar.trade'
        }
        if getattr(current_user, 'email', None) in DENY_PREMIUM_EMAILS:
            flash('Denne kontoen har ikke premium tilgang.', 'warning')
            return redirect('/pricing')
        
        # Check for active subscription
        if hasattr(current_user, 'has_active_subscription') and current_user.has_active_subscription():
            return f(*args, **kwargs)
        
        # Premium features are not available during trial
        flash('This is a premium feature. Please upgrade to access.', 'warning')
        return redirect('/pricing')
    
    return decorated_function

def pro_required(f):
    """Decorator to require Pro subscription"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect('/login')
        
        # Check if user has pro subscription
        if not (hasattr(current_user, 'is_pro') and current_user.is_pro):
            flash('Denne funksjonen krever Pro-abonnement. Oppgrader for å få tilgang.', 'warning')
            return redirect('/pricing')
        
        return f(*args, **kwargs)
    return decorated_function

def is_exempt_user(user=None):
    """Check if a user is exempt from access restrictions"""
    if user is None:
        user = current_user
    
    if not user or not user.is_authenticated:
        return False
        
    user_email = getattr(user, 'email', None)
    return user_email in EXEMPT_EMAILS

def demo_access(f):
    """Demo access decorator - allows permanent access for demo features without time restrictions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Permanent demo access - no restrictions, no trial timers
        return f(*args, **kwargs)
    return decorated_function


def subscription_required(f):
    """
    Strict subscription requirement - NO TRIAL ACCESS
    This replaces @access_required for premium features only
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        import logging
        from flask import current_app
        
        # Check exempt endpoints first
        if hasattr(current_app, 'config') and 'EXEMPT_ENDPOINTS' in current_app.config:
            exempt_endpoints = current_app.config.get('EXEMPT_ENDPOINTS', set())
            if request.endpoint in exempt_endpoints:
                return f(*args, **kwargs)
                
        logging.warning(f"[SUBSCRIPTION_REQUIRED] Called for endpoint={request.endpoint} url={request.url} user_authenticated={current_user.is_authenticated}")
        
        # For authenticated users
        if current_user.is_authenticated:
            # Exempt users always have access
            if getattr(current_user, 'email', None) in EXEMPT_EMAILS:
                return f(*args, **kwargs)
                
            # Users with active subscription have access
            if hasattr(current_user, 'has_active_subscription') and current_user.has_active_subscription():
                return f(*args, **kwargs)
                
            # Check if user is in initial subscription period (10 minutes)
            if hasattr(current_user, 'subscription_start') and current_user.subscription_start:
                if datetime.utcnow() - current_user.subscription_start < timedelta(minutes=10):
                    return f(*args, **kwargs)
                    
            # No valid subscription, redirect to pricing page
            from flask import flash, redirect
            flash('Denne funksjonen krever et aktivt abonnement. Vennligst oppgrader for å fortsette.', 'warning')
            return redirect('/pricing')
            
        # For unauthenticated users - NO TRIAL ACCESS, redirect to demo
        else:
            from flask import Response
            location = '/demo?source=subscription_required'
            logging.warning(f"[SUBSCRIPTION_REQUIRED] Unauthenticated user, redirecting to {location}")
            return Response('', status=302, headers={'Location': location})
    
    return decorated_function

def _is_exempt_user():
    """Check if current user is exempt (admin)"""
    return (current_user.is_authenticated and 
            hasattr(current_user, 'email') and 
            current_user.email in EXEMPT_EMAILS)

def _has_active_subscription():
    """Check if user has active subscription with better error handling"""
    if not current_user.is_authenticated:
        return False
        
    try:
        # Check multiple possible subscription attributes
        has_sub = False
        if hasattr(current_user, 'has_subscription') and current_user.has_subscription:
            has_sub = True
        elif hasattr(current_user, 'has_active_subscription') and callable(current_user.has_active_subscription):
            has_sub = current_user.has_active_subscription()
        elif hasattr(current_user, 'subscription_type') and current_user.subscription_type != 'free':
            has_sub = True
            
        return has_sub
    except Exception as e:
        # Log error but don't crash
        if hasattr(current_app, 'logger'):
            current_app.logger.error(f"Error checking subscription: {e}")
        return False

def _check_trial_access():
    """
    Check trial access status.
    Returns 15-minute trial for new visitors, unlimited demo access for demo pages.
    """
    # Check if this is a demo page request - give unlimited access
    if hasattr(request, 'endpoint') and request.endpoint == 'main.demo':
        return {
            'active': True,
            'start_time': datetime.utcnow(),
            'remaining_minutes': 999999,  # Unlimited for demo
            'expired': False,
            'demo_mode': True
        }
    
    # For non-demo pages, check if user should get trial access
    device_fingerprint = _get_device_fingerprint()
    trial_key = f"trial_{device_fingerprint}"
    
    # Check session first
    trial_start_str = session.get(trial_key)
    
    # Check cookie as backup
    if not trial_start_str:
        trial_start_str = request.cookies.get(trial_key)
    
    now = datetime.utcnow()
    
    # If no trial found, start new trial for premium endpoints
    if not trial_start_str:
        trial_start = now
        session[trial_key] = trial_start.isoformat()
        session.permanent = True
        return {
            'active': True,
            'start_time': trial_start,
            'remaining_minutes': TRIAL_DURATION_MINUTES,
            'expired': False,
            'demo_mode': False
        }
    
    # Parse existing trial start time
    try:
        trial_start = datetime.fromisoformat(trial_start_str)
    except (ValueError, TypeError):
        # Invalid format - start new trial
        trial_start = now
        session[trial_key] = trial_start.isoformat()
        return {
            'active': True,
            'start_time': trial_start,
            'remaining_minutes': TRIAL_DURATION_MINUTES,
            'expired': False,
            'demo_mode': False
        }
    
    # Check if trial has expired
    elapsed = now - trial_start
    trial_active = elapsed <= timedelta(minutes=TRIAL_DURATION_MINUTES)
    
    remaining_minutes = max(0, TRIAL_DURATION_MINUTES - int(elapsed.total_seconds() / 60))
    
    return {
        'active': trial_active,
        'start_time': trial_start,
        'remaining_minutes': remaining_minutes,
        'expired': not trial_active,
        'demo_mode': False
    }
    # DISABLED:     """
    # DISABLED:     Check trial access status.
    # DISABLED:     Returns dict with 'active' (bool) and 'start_time' (datetime)
    # DISABLED:     """
    # DISABLED:     device_fingerprint = _get_device_fingerprint()
    # DISABLED:     trial_key = f"trial_{device_fingerprint}"
    # DISABLED:     # Check session first
    # DISABLED:     trial_start_str = session.get(trial_key)
    # DISABLED:     # Check cookie as backup
    # DISABLED:     if not trial_start_str:
    # DISABLED:         trial_start_str = request.cookies.get(trial_key)
    # DISABLED:     now = datetime.utcnow()
    # DISABLED:     # If no trial found, start new trial ONLY if accessing a premium endpoint
    # DISABLED:     # Demo page should NOT start new trials
    # DISABLED:     if not trial_start_str:
    # DISABLED:         # Don't auto-start trial for demo page
    # DISABLED:         if request.endpoint == 'main.demo':
    # DISABLED:             return {
    # DISABLED:                 'active': False,
    # DISABLED:                 'start_time': None,
    # DISABLED:                 'remaining_minutes': 0,
    # DISABLED:                 'expired': True,
    # DISABLED:                 'no_trial_started': True
    # DISABLED:             }
    # DISABLED:         trial_start = now
    # DISABLED:         session[trial_key] = trial_start.isoformat()
    # DISABLED:         session.permanent = True
    # DISABLED:         # DEBUG: Starting new trial for device (logging disabled for security)
    # DISABLED:         return {
    # DISABLED:             'active': True,
    # DISABLED:             'start_time': trial_start,
    # DISABLED:             'remaining_minutes': TRIAL_DURATION_MINUTES,
    # DISABLED:             'expired': False
    # DISABLED:         }
    # DISABLED:     # Parse existing trial start time
    # DISABLED:     try:
    # DISABLED:         trial_start = datetime.fromisoformat(trial_start_str)
    # DISABLED:     except (ValueError, TypeError):
    # DISABLED:         # Invalid format - if on demo page, don't restart trial
    # DISABLED:         if request.endpoint == 'main.demo':
    # DISABLED:             return {
    # DISABLED:                 'active': False,
    # DISABLED:                 'start_time': None,
    # DISABLED:                 'remaining_minutes': 0,
    # DISABLED:                 'expired': True,
    # DISABLED:                 'no_trial_started': True
    # DISABLED:             }
    # DISABLED:         trial_start = now
    # DISABLED:         session[trial_key] = trial_start.isoformat()
    # DISABLED:         # DEBUG: Invalid trial format, starting new trial for device (logging disabled for security)
    # DISABLED:         return {
    # DISABLED:             'active': True,
    # DISABLED:             'start_time': trial_start,
    # DISABLED:             'remaining_minutes': TRIAL_DURATION_MINUTES,
    # DISABLED:             'expired': False
    # DISABLED:         }
    # DISABLED:     # Check if trial has expired
    # DISABLED:     elapsed = now - trial_start
    # DISABLED:     trial_active = elapsed <= timedelta(minutes=TRIAL_DURATION_MINUTES)
    # DISABLED:     remaining_minutes = max(0, TRIAL_DURATION_MINUTES - int(elapsed.total_seconds() / 60))
    # DISABLED:     # DEBUG: Trial check - elapsed time and status (logging disabled for security)
    # DISABLED:     return {
    # DISABLED:         'active': trial_active,
    # DISABLED:         'start_time': trial_start,
    # DISABLED:         'remaining_minutes': remaining_minutes,
    # DISABLED:         'expired': not trial_active
    # DISABLED:     }
def _update_trial_cookie(response, start_time):
    """Update trial tracking cookie"""
    device_fingerprint = _get_device_fingerprint()
    trial_key = f"trial_{device_fingerprint}"
    response.set_cookie(
        trial_key, 
        start_time.isoformat(), 
        max_age=60*60*24*7,  # 7 days
        httponly=True
    )

def _handle_no_access():
    """Handle when user has no access (trial expired, no subscription)"""
    try:
        # Differentiate between authenticated and unauthenticated users
        if current_user.is_authenticated:
            # For logged-in users without subscription, redirect to pricing
            if _is_ajax_request():
                return jsonify({
                    'error': 'Access denied',
                    'message': 'Subscription required',
                    'redirect': '/pricing'
                }), 403
            
            flash('Denne funksjonen krever et aktivt abonnement. Vennligst oppgrader for å få tilgang.', 'warning')
            return redirect('/pricing')
        else:
            # For anonymous users (trial expired), redirect to demo
            if _is_ajax_request():
                return jsonify({
                    'error': 'Access denied',
                    'message': 'Trial expired',
                    'redirect': '/demo?source=trial_expired'
                }), 403
            
            # Don't show trial expired messages - redirect silently
            return redirect(url_for('main.demo', source='trial_expired'))
    except Exception as e:
        # Fallback - basic response if redirects fail
        return "Access denied - please subscribe or login", 403

def _get_device_fingerprint():
    """Create a simple device fingerprint"""
    fingerprint_data = f"{request.remote_addr}:{request.headers.get('User-Agent', '')}"
    return hashlib.md5(fingerprint_data.encode()).hexdigest()

def _is_ajax_request():
    """Check if request is AJAX"""
    return (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
            request.headers.get('Content-Type', '').startswith('application/json') or
            request.headers.get('Accept', '').startswith('application/json'))

def get_trial_status():
    """Get current trial status for templates"""
    if _is_exempt_user() or _has_active_subscription():
        return {
            'active': True,
            'unlimited': True,
            'remaining_minutes': None,
            'expired': False
        }
    
    trial_status = _check_trial_access()
    return trial_status

def get_access_level():
    """Get current user's access level for templates"""
    if _is_exempt_user():
        return 'admin'
    elif _has_active_subscription():
        return 'subscriber'
    elif _check_trial_access()['active']:
        return 'trial'
    else:
        return 'restricted'

def get_trial_time_remaining():
    """Get trial time remaining in seconds (for backward compatibility)"""
    if _is_exempt_user() or _has_active_subscription():
        return None  # Unlimited access
    
    trial_status = _check_trial_access()
    if trial_status['active']:
        return trial_status['remaining_minutes'] * 60  # Convert to seconds
    else:
        return 0  # Trial expired

def is_demo_user():
    """Check if current user is a demo user (backward compatibility)"""
    # Demo users are essentially trial users without active subscriptions
    return not _is_exempt_user() and not _has_active_subscription()

def is_trial_active():
    """Check if trial is currently active (backward compatibility)"""
    if _is_exempt_user() or _has_active_subscription():
        return True  # These users have unlimited access
    
    trial_status = _check_trial_access()
    return trial_status['active']

def check_access_and_redirect():
    """Check access and redirect if necessary - STRICT ACCESS CONTROL"""
    from flask import request, redirect, url_for
    from flask_login import current_user
    
    # Always allow access to exempt users (admin accounts)
    if current_user.is_authenticated and is_exempt_user():
        return None
    
    # Public endpoints that should always be accessible
    public_endpoints = {
        'main.demo', 'main.login', 'main.register', 
        'main.about', 'main.contact', 'main.terms', 'main.privacy',
        'health.health_check', 'static', 'main.landing',
        'pricing.pricing_page', 'pricing.subscription', 'pricing.manage_subscription',
        'pricing.stripe_webhook', 'pricing.cancel_subscription',
        'stocks.compare',  # Stock comparison tool should be accessible to all users
        'stocks.search'   # Stock search functionality should be accessible to all users
    }
    
    # API endpoints that should be accessible for demo functionality
    api_endpoints = {
        'api.demo_market_data_api', 'api.get_crypto_trending', 'api.get_economic_indicators',
        'api.get_market_sectors', 'api.search_stocks', 'api.market_data',
        'api.get_currency_rates', 'health.health_check'
    }
    
    if request.endpoint in public_endpoints or request.endpoint in api_endpoints:
        return None
    
    # For ALL other endpoints, check if user has access
    # Check if user has active subscription
    if current_user.is_authenticated and _has_active_subscription():
        return None  # Allow access for paying users
    
    # No access - redirect to demo for EVERYONE else
    # This includes: main.index, all analysis routes, stocks, portfolio, etc.
    return redirect(url_for('main.demo', source='access_required'))
