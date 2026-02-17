"""
Fixes demo redirect issues by creating a unified access control system.
This replaces conflicting access control systems that cause redirect loops.
"""

from flask import current_app, redirect, url_for, request, flash
from flask_login import current_user
from functools import wraps
import logging

# Exempt users who always get full access
EXEMPT_EMAILS = {
    'testuser@aksjeradar.trade', 
    'helene721@gmail.com', 
    'tonjekit91@gmail.com',
    'investor@aksjeradar.trade',    # Test user for investors
    'test@aksjeradar.trade'         # General test user with premium access
    # Note: Eirik fjernet fra exempt-liste for å blokkere premium
}

# Always accessible endpoints (no authentication required)
ALWAYS_ACCESSIBLE = {
    'main.index',
    'main.demo', 
    'main.login',
    'main.register',
    'main.logout',
    'main.privacy',
    'main.privacy_policy',
    'main.contact',
    'main.contact_submit',
    'main.forgot_password',
    'main.reset_password',
    'main.terms',
    'main.about',
    'main.help',
    'main.features',
    'main.translation_help',
    'main.set_language',
    'static',
    'main.service_worker',
    'main.manifest',
    'main.favicon',
    'main.offline',
    'main.offline_html',
    'diagnostic.auth_status',  # Diagnostic route
    'test.access_control_check'  # Diagnostic access control snapshot route
}

# Demo accessible endpoints (available for authenticated users)
DEMO_ACCESSIBLE = {
    'stocks.index',
    'stocks.search', 
    'stocks.list_currency',
    'stocks.details',        # Allow details page for demo users
    'analysis.index',
    'market.overview',
    'market.sectors',
    'market_intel.insider_trading',
    
    # Portfolio routes
    'portfolio.portfolio_overview',  # Basic portfolio view
    'portfolio.create_portfolio',    # Create portfolio
    'portfolio.view_portfolio',      # View portfolio
    'portfolio.index',               # Portfolio index
    'portfolio.delete_portfolio',    # Delete portfolio
    'portfolio.add_stock_to_portfolio',  # Add stock to portfolio
    'portfolio.remove_stock_from_portfolio',  # Remove stock from portfolio
    'portfolio.watchlist',           # Watchlist
    'portfolio.stock_tips',          # Stock tips
    'portfolio.stock_tips_feedback', # Stock tips feedback
    'portfolio.quick_add_stock',     # Quick add stock
    'portfolio.create_watchlist',    # Create watchlist
    'portfolio.add_to_watchlist',    # Add to watchlist
    'portfolio.add_tip',             # Add tip
    'portfolio.tip_feedback',        # Tip feedback
    'portfolio.watchlist',           # User's watchlist
    
    # Price alerts
    'price_alerts.index',  # Basic alerts view
    
    # Profile routes - accessible to all authenticated users
    'main.profile',          # Main blueprint profile route
    'main.update_profile',   # Update profile in main blueprint
    'profile.profile_page',  # Profile blueprint's profile page
    'profile.update_profile',  # Update profile in profile blueprint
    'profile.remove_favorite'  # Remove favorite in profile blueprint
}

# Premium endpoints (require active subscription)
PREMIUM_ONLY = {
    'stocks.list_stocks', 
    'stocks.list_oslo',
    'stocks.global_list',
    'stocks.list_crypto',
    'stocks.compare',
    'analysis.ai',
    'analysis.technical',
    'analysis.warren_buffett',
    'analysis.prediction',
    'analysis.market_overview',
    'portfolio.create_portfolio',
    'portfolio.view_portfolio',
    'portfolio.transactions',
    'market_intel.index'
}


def is_exempt_user():
    """Check if current user is exempt from access restrictions"""
    try:
        # current_user can be a LocalProxy resolving to None in certain isolated test contexts.
        cu = current_user if current_user is not None else None
    except Exception:
        cu = None

    is_authenticated = bool(getattr(cu, 'is_authenticated', False))
    has_email = bool(getattr(cu, 'email', None))
    email = getattr(cu, 'email', None) if has_email else None
    is_exempt = email in EXEMPT_EMAILS if email else False
    
    try:
        current_app.logger.info(f"EXEMPT CHECK: auth={is_authenticated}, has_email={has_email}, email={email}, is_exempt={is_exempt}")
    except Exception:
        pass  # Don't break on logging errors
    
    return is_authenticated and has_email and is_exempt


def has_active_subscription():
    """Check if current user has an active subscription"""
    safe_auth = False
    try:
        safe_auth = bool(getattr(current_user, 'is_authenticated', False))
    except Exception:
        safe_auth = False
    if not safe_auth:
        try:
            current_app.logger.info("SUBSCRIPTION CHECK: User not authenticated")
        except Exception:
            pass
        return False
        
    # Exempt users always have access
    if is_exempt_user():
        try:
            current_app.logger.info(f"SUBSCRIPTION CHECK: User is exempt")
        except Exception:
            pass
        return True
        
    # Check subscription methods
    has_subscription_method = hasattr(current_user, 'has_active_subscription')
    if has_subscription_method:
        try:
            is_active = current_user.has_active_subscription()
            current_app.logger.info(f"SUBSCRIPTION CHECK: has_active_subscription() = {is_active}")
            return is_active
        except Exception as e:
            current_app.logger.error(f"Error calling has_active_subscription(): {e}")
        
    has_subscription_type = hasattr(current_user, 'subscription_type')
    if has_subscription_type:
        subscription_type = current_user.subscription_type
        is_premium = subscription_type in ['premium', 'pro', 'yearly', 'lifetime', 'active']
        try:
            current_app.logger.info(f"SUBSCRIPTION CHECK: subscription_type = {subscription_type}, is_premium = {is_premium}")
        except Exception:
            pass
        return is_premium
    
    # Enhanced fallback checks
    fallback_attrs = {
        'subscription_status': ['active', 'premium', 'pro', 'trial', 'yearly', 'lifetime'],
        'is_premium': True,
        'demo_access': True,
        'lifetime_access': True
    }
    
    for attr, valid_values in fallback_attrs.items():
        if hasattr(current_user, attr):
            attr_value = getattr(current_user, attr)
            if isinstance(valid_values, list):
                if attr_value in valid_values:
                    return True
            elif attr_value == valid_values:
                return True
    
    try:
        current_app.logger.info(f"SUBSCRIPTION CHECK: No subscription methods found")
    except Exception:
        pass
    return False


def get_access_level():
    """
    Get current user's access level
    Returns: 'admin', 'premium', 'demo', or 'none'
    """
    try:
        is_auth = current_user.is_authenticated
        current_app.logger.info(f"ACCESS LEVEL CHECK: is_authenticated = {is_auth}")
    except Exception:
        pass
    
    if is_exempt_user():
        try:
            current_app.logger.info("ACCESS LEVEL: admin (exempt user)")
        except Exception:
            pass
        return 'admin'
        
    if has_active_subscription():
        try:
            current_app.logger.info("ACCESS LEVEL: premium (active subscription)")
        except Exception:
            pass
        return 'premium'
        
    try:
        is_auth_demo = bool(getattr(current_user, 'is_authenticated', False))
    except Exception:
        is_auth_demo = False
    if is_auth_demo:
        try:
            current_app.logger.info("ACCESS LEVEL: demo (authenticated user)")
        except Exception:
            pass
        return 'demo'  # Authenticated users get demo access
    
    try:
        current_app.logger.info("ACCESS LEVEL: none (unauthenticated user)")
    except Exception:
        pass
    return 'none'


def check_endpoint_access(endpoint):
    """
    Check if current user can access the given endpoint
    Returns: (allowed: bool, redirect_to: str|None, message: str|None)
    """
    try:
        current_app.logger.info(f"CHECKING ACCESS FOR: {endpoint}")
    except Exception:
        pass
    
    # Always accessible endpoints
    if endpoint in ALWAYS_ACCESSIBLE:
        try:
            current_app.logger.info(f"ENDPOINT {endpoint} is ALWAYS_ACCESSIBLE")
        except Exception:
            pass
        return True, None, None
        
    access_level = get_access_level()
    try:
        current_app.logger.info(f"USER ACCESS LEVEL: {access_level}")
    except Exception:
        pass
    
    # Admin/exempt users can access everything
    if access_level == 'admin':
        try:
            current_app.logger.info(f"ADMIN ACCESS GRANTED for {endpoint}")
        except Exception:
            pass
        return True, None, None
        
    # Premium users can access everything except admin-only
    if access_level == 'premium':
        try:
            current_app.logger.info(f"PREMIUM ACCESS GRANTED for {endpoint}")
        except Exception:
            pass
        return True, None, None
        
    # Demo users can access demo endpoints
    if access_level == 'demo':
        if endpoint in DEMO_ACCESSIBLE:
            try:
                current_app.logger.info(f"DEMO ACCESS GRANTED for {endpoint} (in DEMO_ACCESSIBLE)")
            except Exception:
                pass
            return True, None, None
        elif endpoint in PREMIUM_ONLY:
            try:
                current_app.logger.info(f"DEMO ACCESS DENIED for {endpoint} (in PREMIUM_ONLY)")
            except Exception:
                pass
            return False, 'pricing.index', 'Denne funksjonen krever premium-abonnement'
        else:
            # Unknown endpoint - allow for backwards compatibility
            try:
                current_app.logger.info(f"DEMO ACCESS GRANTED for {endpoint} (unknown endpoint - backwards compat)")
            except Exception:
                pass
            return True, None, None
            
    # Unauthenticated users - redirect to demo for most things
    if access_level == 'none':
        if endpoint in DEMO_ACCESSIBLE or endpoint in PREMIUM_ONLY:
            try:
                current_app.logger.info(f"ANON ACCESS DENIED for {endpoint} - redirecting to demo")
            except Exception:
                pass
            return False, 'main.demo', 'Vennligst logg inn eller prøv demo-versjonen'
        else:
            try:
                current_app.logger.info(f"ANON ACCESS DENIED for {endpoint} - redirecting to login")
            except Exception:
                pass
            return False, 'main.login', 'Vennligst logg inn for å fortsette'


def unified_access_required(f):
    """
    Unified access control decorator that replaces all other access decorators
    Prevents redirect loops by using consistent logic
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_app.logger.info(f"ACCESS CHECK for {request.endpoint} - URL: {request.url}")
        
        # Get user information for debugging
        user_id = getattr(current_user, 'id', 'anonymous')
        is_auth = current_user.is_authenticated
        user_email = getattr(current_user, 'email', 'none') if is_auth else 'none'
        
        current_app.logger.info(f"USER: id={user_id}, auth={is_auth}, email={user_email}")
        
        # Skip check if we're already on an always-accessible page
        if request.endpoint in ALWAYS_ACCESSIBLE:
            current_app.logger.info(f"ALWAYS ACCESSIBLE: {request.endpoint}")
            return f(*args, **kwargs)
            
        # Prevent redirect loops for demo page
        if request.endpoint == 'main.demo':
            current_app.logger.info(f"DEMO PAGE: {request.endpoint}")
            return f(*args, **kwargs)
            
        # Check access
        access_level = get_access_level()
        current_app.logger.info(f"ACCESS LEVEL: {access_level}")
        
        allowed, redirect_to, message = check_endpoint_access(request.endpoint)
        current_app.logger.info(f"ACCESS CHECK RESULT: allowed={allowed}, redirect_to={redirect_to}, message={message}")
        
        if allowed:
            current_app.logger.info(f"ACCESS GRANTED for {request.endpoint}")
            return f(*args, **kwargs)
        else:
            if message:
                flash(message, 'info')
                current_app.logger.info(f"ACCESS DENIED: {message}")
            
            # Prevent infinite redirects
            if redirect_to and redirect_to != request.endpoint:
                try:
                    current_app.logger.info(f"Access denied for {request.endpoint}, redirecting to {redirect_to}")
                    return redirect(url_for(redirect_to))
                except Exception as e:
                    current_app.logger.error(f"Redirect error: {e}")
                    # Fallback to safe redirect
                    return redirect(url_for('main.index'))
            else:
                # Fallback for edge cases
                current_app.logger.info(f"FALLBACK REDIRECT to main.index")
                return redirect(url_for('main.index'))
                
    return decorated_function


def safe_demo_access(f):
    """
    Safe demo access decorator that prevents redirect loops
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Always allow access to demo page to prevent loops
        if request.endpoint == 'main.demo':
            return f(*args, **kwargs)
            
        # Check if user should have access to this demo feature
        access_level = get_access_level()
        
        if access_level in ['admin', 'premium', 'demo']:
            return f(*args, **kwargs)
        else:
            # Unauthenticated users can still access demo pages
            return f(*args, **kwargs)
            
    return decorated_function


def premium_required(f):
    """
    Decorator for premium-only features - redirects to pricing
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        access_level = get_access_level()
        
        if access_level in ['admin', 'premium']:
            return f(*args, **kwargs)
        else:
            flash('Denne funksjonen krever premium-abonnement', 'warning')
            if current_user.is_authenticated:
                return redirect(url_for('pricing.index'))
            else:
                return redirect(url_for('main.login', next=request.url))
                
    return decorated_function


def api_access_required(f):
    """
    API-specific access control with JSON responses
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import jsonify
        
        access_level = get_access_level()
        
        # API endpoints require at least demo access
        if access_level == 'none':
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please log in to access this API',
                'code': 'LOGIN_REQUIRED'
            }), 401
            
        # Check specific endpoint requirements
        allowed, _, _ = check_endpoint_access(request.endpoint)
        
        if not allowed:
            return jsonify({
                'error': 'Access denied',
                'message': 'This feature requires premium subscription',
                'code': 'PREMIUM_REQUIRED'
            }), 403
            
        return f(*args, **kwargs)
        
    return decorated_function


# Logging function for debugging
def log_access_attempt(endpoint, user_id=None, access_level=None):
    """Log access attempts for debugging"""
    try:
        current_app.logger.info(
            f"Access attempt: endpoint={endpoint}, "
            f"user_id={user_id or 'anonymous'}, "
            f"access_level={access_level or get_access_level()}"
        )
    except Exception:
        pass  # Don't break on logging errors


# Export commonly used functions
__all__ = [
    'unified_access_required',
    'safe_demo_access', 
    'premium_required',
    'api_access_required',
    'get_access_level',
    'check_endpoint_access',
    'is_exempt_user',
    'has_active_subscription'
]
