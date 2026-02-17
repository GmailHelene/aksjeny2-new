from flask import Blueprint, render_template
from flask_login import current_user
from datetime import datetime

from ..auth.enhanced_auth import validate_session, require_subscription
from ..utils.cache_manager import cached, cache_manager

bp = Blueprint('main', __name__)

@bp.route('/')
@bp.route('/index')
@validate_session()
def index():
    """Enhanced homepage with optimized data loading"""
    # Get basic market data for non-authenticated users
    restricted = not current_user.is_authenticated or not current_user.has_subscription_level('basic')
    
    # Cache key based on user subscription level
    cache_key = f"homepage_data:{current_user.subscription_level if current_user.is_authenticated else 'anonymous'}"
    
    # Try to get cached data
    homepage_data = cache_manager.get(cache_key)
    
    if not homepage_data:
        # Generate fresh data
        homepage_data = {
            'restricted': restricted,
            'last_updated': datetime.now().strftime('%d.%m.%Y %H:%M'),
            'show_banner': not current_user.is_authenticated
        }
        
        # Cache for 5 minutes
        cache_manager.set(cache_key, homepage_data, ttl=300)
    
    return render_template('index.html', **homepage_data)

@bp.route('/dashboard')
@require_subscription('basic')
def dashboard():
    """Premium dashboard for subscribed users"""
    return render_template('dashboard.html')