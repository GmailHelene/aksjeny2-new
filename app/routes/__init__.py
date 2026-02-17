"""
Clean route imports - remove duplicates and organize properly
"""
# Standard library imports
import os
import logging
from datetime import datetime, timedelta

# Flask imports
from flask import Flask, request, redirect, url_for, render_template, jsonify
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_migrate import Migrate

# Local imports - config and extensions
from ..config import Config
from ..extensions import db, login_manager, csrf, mail

# Configuration mapping
config = {
    'default': Config,
    'production': Config,
    'development': Config,
    'testing': Config
}

# NOTE: Removed eager blueprint imports to prevent a single missing optional module
# from breaking application startup (e.g., insider_trading, norwegian_intel, market_intel).
# Blueprints are now imported on-demand inside register_blueprints with granular
# try/except handling. This dramatically improves resilience during partial
# deployments or when pruning legacy / experimental route files.
#
# If you need to ensure a blueprint ALWAYS loads (hard failure if missing),
# include it in the "core" section inside register_blueprints.

# Remove these if they exist as separate files but are duplicates:
# from .dashboard import dashboard  # Consolidate into main
# from .external_data import external_data  # Consolidate into analysis

# This function has been consolidated with the one below
# def register_blueprints(app):
#     """Register all blueprints with the app"""
#     app.register_blueprint(main)
#     app.register_blueprint(stocks, url_prefix='/stocks')
#     app.register_blueprint(analysis, url_prefix='/analysis')
#     app.register_blueprint(portfolio, url_prefix='/portfolio')
#     app.register_blueprint(advanced_features, url_prefix='/advanced')
#     app.register_blueprint(advanced_features, url_prefix='/advanced-features')  # Support both URL patterns
#     app.register_blueprint(advanced_analytics, url_prefix='/advanced-analytics')  # Register advanced analytics with correct URL
#     app.register_blueprint(forum, url_prefix='/forum')
#     # app.register_blueprint(news, url_prefix='/news')  # Removed - file not found
#     app.register_blueprint(pricing, url_prefix='/pricing')
#     app.register_blueprint(insider_trading, url_prefix='/insider-trading')
#     app.register_blueprint(market_intel, url_prefix='/market-intel')
#     app.register_blueprint(pro_tools, url_prefix='/pro-tools')
#     app.register_blueprint(profile, url_prefix='/user')  # Register profile blueprint with /user prefix
#     
#     # Add insider trading to analysis blueprint instead of separate
#     # app.register_blueprint(insider_trading, url_prefix='/insider-trading')
def create_app(config_name='default'):
    """Production-ready app factory with Railway compatibility"""
    app = Flask(__name__)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)
    
    try:
        # Load config
        app.config.from_object(config[config_name])
        app.logger.info(f"✅ App created in {config_name} mode")
        
        # Basic app configuration
        configure_app(app, config[config_name])
        
        # Register custom unauthorized handler for Flask-Login
        from flask import request, redirect, url_for
        def aksjeradar_unauthorized():
            app.logger.warning(f"[UNAUTHORIZED HANDLER] endpoint={request.endpoint} url={request.url}")
            # Redirect to /demo for main/index routes
            if request.endpoint in ('main.index', 'main', 'main.landing', 'main.home', 'main.demo'):
                app.logger.warning("[UNAUTHORIZED HANDLER] Redirecting to /demo")
                return redirect(url_for('main.demo'))
            # Otherwise, default to login
            app.logger.warning("[UNAUTHORIZED HANDLER] Redirecting to /login")
            return redirect(url_for('main.login', next=request.url))
        
        login_manager.unauthorized_handler(aksjeradar_unauthorized)
        app.logger.info('Custom unauthorized handler registered for Flask-Login')
        
        # Initialize core extensions
        init_core_extensions(app, config[config_name])
        
        # Import database models early to ensure user_loader is registered
        try:
            from ..models import User, Portfolio, Watchlist
            from ..models.user import load_user
            app.logger.info("✅ Database models imported successfully")
        except Exception as e:
            app.logger.error(f"❌ Error importing database models: {e}")
            # Continue without models for now
        
        # Register blueprints
        register_blueprints(app)
        
        # Add context processors and error handlers
        setup_app_handlers(app)
        
        # Initialize database for production
        if config_name == 'production':
            setup_production_database(app)
        else:
            setup_lazy_database_init(app)
        
        # Register custom Jinja2 filters
        try:
            from ..utils.filters import register_filters
            register_filters(app)
        except ImportError:
            app.logger.warning("Could not import custom filters")
        
        # Register Norwegian formatting filters
        try:
            from ..utils.norwegian_formatter import register_norwegian_filters
            register_norwegian_filters(app)
        except ImportError:
            app.logger.warning("Could not import Norwegian filters")
        
        # Debug: Print all registered endpoints
        app.logger.info("Registered endpoints:")
        for rule in app.url_map.iter_rules():
            app.logger.info(f"Endpoint: {rule.endpoint} -> {rule}")
        app.logger.info("✅ App initialization complete")
        return app
        
    except Exception as e:
        app.logger.error(f"❌ Critical error during app creation: {e}")
        raise

def register_blueprints(app):
    """Register all blueprints"""
    blueprints_registered = []
    
    # Core blueprints that must be registered
    try:
        from .main import main
        app.register_blueprint(main)
        blueprints_registered.append('main')
        
        # Register auth blueprint
        from ..auth import auth
        app.register_blueprint(auth, url_prefix='/auth')
        blueprints_registered.append('auth')
        app.logger.info("✅ Registered auth blueprint")
        # Explicitly import and register portfolio blueprint
        from .portfolio import portfolio
        app.register_blueprint(portfolio, url_prefix='/portfolio')
        blueprints_registered.append('portfolio')
        
        # Explicitly import and register profile blueprint
        from .profile import profile
        app.register_blueprint(profile, url_prefix='/profile')
        blueprints_registered.append('profile')
        
        # Register Stripe blueprint
        try:
            from .stripe_routes import stripe_bp
            app.register_blueprint(stripe_bp)
            blueprints_registered.append('stripe')
            app.logger.info("✅ Registered Stripe blueprint")
        except ImportError as e:
            app.logger.warning(f"Could not import Stripe blueprint: {e}")
    except ImportError as e:
        app.logger.error(f"Failed to import main or portfolio blueprint: {e}")
        raise
    
    # Other blueprints with error handling
    blueprint_configs = [
        # (module_path, blueprint_variable_name, url_prefix)
        ('.stocks', 'stocks', '/stocks'),
        ('.api', 'api', None),
        ('.blog', 'blog', '/blog'),
        ('.forum', 'forum', '/forum'),
        ('.pricing', 'pricing', '/pricing'),
        # Optional analytics / advanced feature sets
        ('.advanced_features', 'advanced_features', '/advanced-features'),
        ('.advanced_analytics', 'advanced_analytics', '/advanced-analytics'),
        ('.pro_tools', 'pro_tools', '/pro-tools'),
        # Investor / marketing content
        ('.investor', 'investor', '/investor'),
        # User profile already core-registered under /profile
        # Notifications (API + web UI) - unified endpoint space
        ('.notifications', 'notifications_bp', '/notifications'),
        ('.notifications', 'notifications_web_bp', '/notifications'),
        # Watchlist & alerts related
        ('.watchlist', 'watchlist', '/watchlist'),
        ('.watchlist_api', 'watchlist_api', '/watchlist-api'),
        ('.price_alerts', 'price_alerts', '/price-alerts'),
        ('.alerts', 'alerts', '/alerts'),
        # Analysis & health
        ('.analysis', 'analysis', '/analysis'),
        ('.health', 'health', '/health'),
        # News (optional)
        ('.news', 'news_bp', '/news'),
        # Admin & feature flags
        ('.admin', 'admin', '/admin'),
        ('.features', 'features', '/features'),
    ]
    
    for module_path, blueprint_name, url_prefix in blueprint_configs:
        try:
            module = __import__(module_path, fromlist=[blueprint_name])
            blueprint = getattr(module, blueprint_name)
            
            if url_prefix:
                app.register_blueprint(blueprint, url_prefix=url_prefix)
            else:
                app.register_blueprint(blueprint)
            
            blueprints_registered.append(blueprint_name)
            app.logger.info(f"✅ Registered blueprint: {blueprint_name}")
            
        except ImportError as e:
            app.logger.warning(f"Could not import {blueprint_name}: {e}")
        except AttributeError as e:
            app.logger.warning(f"Blueprint {blueprint_name} not found in {module_path}: {e}")
        except Exception as e:
            app.logger.error(f"Error registering {blueprint_name}: {e}")
    
    app.logger.info(f"✅ Registered {len(blueprints_registered)} blueprints: {', '.join(blueprints_registered)}")
    
    # Register the realtime_api blueprint
    try:
        from .realtime_api import realtime_api
        app.register_blueprint(realtime_api)
        blueprints_registered.append('realtime_api')
        app.logger.info("✅ Registered realtime_api blueprint")
    except ImportError as e:
        app.logger.warning(f"Could not import realtime_api blueprint: {e}")
        
    # Register diagnostic tools blueprint
    try:
        from .details_debug import details_debug
        app.register_blueprint(details_debug, url_prefix='/stocks/details-debug')
        blueprints_registered.append('details_debug')
        app.logger.info("✅ Registered details_debug blueprint")
    except ImportError as e:
        app.logger.warning(f"Could not import details_debug blueprint: {e}")
        
    # Register diagnostic blueprint
    try:
        from .diagnostic import diagnostic
        app.register_blueprint(diagnostic, url_prefix='/diagnostic')
        blueprints_registered.append('diagnostic')
        app.logger.info("✅ Registered diagnostic blueprint")
    except ImportError as e:
        app.logger.warning(f"Could not import diagnostic blueprint: {e}")
        blueprints_registered.append('realtime_api')
        app.logger.info("✅ Registered realtime_api blueprint")
    except ImportError as e:
        app.logger.warning(f"Could not import realtime_api blueprint: {e}")

def setup_production_database(app):
    """Setup database for production with proper error handling"""
    try:
        with app.app_context():
            # Create database tables if they don't exist
            db.create_all()
            app.logger.info("✅ Database tables created/verified")
            
            # Set up exempt users for production
            setup_exempt_users(app)
            
    except Exception as e:
        app.logger.error(f"❌ Production database setup failed: {e}")

def setup_exempt_users(app):
    """Set up exempt users for production"""
    try:
        from ..models.user import User
        
        exempt_users = [
            {'email': 'helene721@gmail.com', 'username': 'helene721', 'password': 'aksjeradar2024', 'lifetime': False},
            {'email': 'tonjekit91@gmail.com', 'username': 'tonjekit91', 'password': 'aksjeradar2024', 'lifetime': True},
            {'email': 'testuser@aksjeradar.trade', 'username': 'helene_luxus', 'password': 'aksjeradar2024', 'lifetime': False},
            {'email': 'investor@aksjeradar.trade', 'username': 'investor', 'password': 'aksjeradar2024', 'lifetime': True},
            {'email': 'test@aksjeradar.trade', 'username': 'testuser', 'password': 'aksjeradar2024', 'lifetime': True}
        ]
        for user_data in exempt_users:
            user = User.query.filter_by(email=user_data['email']).first()
            if not user:
                user = User(
                    email=user_data['email'],
                    username=user_data['username'],
                    is_admin=True,
                    trial_used=False
                )
                user.set_password(user_data['password'])
                db.session.add(user)
            # Oppdater alltid til riktig pro/lifetime-status
            if user_data['lifetime']:
                user.has_subscription = True
                user.subscription_type = 'lifetime'
                user.subscription_start = datetime.utcnow()
                user.subscription_end = None
            else:
                user.has_subscription = True
                user.subscription_type = 'premium'
                user.subscription_start = datetime.utcnow()
                user.subscription_end = datetime.utcnow() + timedelta(days=365)
            user.is_admin = True
            user.trial_used = True
        db.session.commit()
        app.logger.info("✅ Exempt users configured with correct pro/lifetime access")
        
    except Exception as e:
        app.logger.error(f"❌ Failed to set up exempt users: {e}")

def configure_app(app, config_obj):
    """Configure app settings and security headers"""
    # Database configuration - Railway compatibility
    database_url = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    
    # Fix postgres:// to postgresql:// for Railway
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'echo': os.getenv('SQL_ECHO', 'False').lower() == 'true'
    }
    
    # Security settings
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())
    app.config['SESSION_COOKIE_SECURE'] = getattr(config_obj, 'SESSION_COOKIE_SECURE', False)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
    
    # Add EXEMPT_ENDPOINTS to app config - endpoints that should always be accessible
    app.config['EXEMPT_ENDPOINTS'] = {
        'main.login', 'main.register', 'main.logout', 'main.privacy', 'main.privacy_policy',
        'main.offline', 'main.offline_html', 'static', 'favicon', 
        'main.service_worker', 'main.manifest', 'main.version', 'main.contact', 'main.contact_submit',
        'main.subscription', 'main.subscription_plans', 'main.payment_success', 'main.payment_cancel',
        'main.forgot_password', 'main.reset_password', 'main.demo', 'main.index',
        'stocks.index', 'stocks.search', 'analysis.index', 'main.referrals', 'main.send_referral',
        'pricing.pricing_page', 'pricing.index'
    }
    
    # Add security headers
    @app.after_request
    def add_security_headers(response):
        # Content type protection
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Clickjacking protection
        response.headers['X-Frame-Options'] = 'DENY'
        
        # XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https: *; "
            "font-src 'self' https: data:; "
            "connect-src 'self' https: wss:; "
            "frame-src 'self' https://js.stripe.com; "
            "object-src 'none'; "
            "base-uri 'self';"
        )
        response.headers['Content-Security-Policy'] = csp
        
        # Additional security headers
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        
        return response

def init_core_extensions(app, config_obj):
    """Initialize only core extensions for faster startup"""
    # Core database and auth
    db.init_app(app)
    login_manager.init_app(app)
    
    # CSRF protection
    csrf = CSRFProtect()
    csrf.init_app(app)
    
    # Configure Flask-Login with secure cookie settings
    # Removed login_manager.login_view to allow custom access control and redirects
    login_manager.login_message = ''
    login_manager.login_message_category = 'info'
    login_manager.session_protection = 'strong'
    login_manager.remember_cookie_duration = timedelta(days=30)
    login_manager.remember_cookie_name = getattr(config_obj, 'REMEMBER_COOKIE_NAME', 'remember_token')
    login_manager.remember_cookie_httponly = getattr(config_obj, 'REMEMBER_COOKIE_HTTPONLY', True)

    # Set remember cookie secure flag for production
    login_manager.remember_cookie_secure = getattr(config_obj, 'REMEMBER_COOKIE_SECURE', False)

    login_manager.refresh_view = 'main.login'
    login_manager.needs_refresh_message = ''
    
    # Mail (lazy init)
    mail.init_app(app)
    
    # Database migrations
    migrate = Migrate(app, db)

def setup_lazy_database_init(app):
    """Setup lazy database initialization"""
    @app.before_request
    def init_database():
        """Initialize database models on first request"""
        # Only initialize once
        if hasattr(app, '_database_models_imported'):
            return
            
        try:
            # Import models here to ensure they're registered with SQLAlchemy
            from ..models import User, Portfolio, Watchlist
            from ..models.notifications import (
                Notification, PriceAlert, NotificationSettings, 
                AIModel, PredictionLog
            )
            # Ensure user_loader is imported and registered
            from ..models.user import load_user
            app._database_models_imported = True
            app.logger.info("Database models imported successfully")
        except Exception as e:
            app.logger.error(f"Error importing database models: {e}")

def setup_app_handlers(app):
    """Setup context processors and error handlers"""
    @app.context_processor
    def utility_processor():
        from flask_login import current_user
        from flask import session, g
        from flask_wtf.csrf import generate_csrf
        
        try:
            from app.utils.access_control import get_trial_status
            trial_status = get_trial_status()
        except:
            trial_status = None
        
        # Make current_user and login status available globally
        login_status = {
            'current_user': current_user,
            'is_authenticated': current_user.is_authenticated if current_user else False,
            'user_email': current_user.email if current_user and current_user.is_authenticated else None,
            'user_name': current_user.username if current_user and current_user.is_authenticated else None,
            'datetime': datetime,
            'csrf_token': generate_csrf,
            'trial_status': trial_status
        }
        
        # Also set in g for template access
        g.current_user = current_user
        g.is_authenticated = current_user.is_authenticated if current_user else False
        
        return login_status
    
    @app.template_filter('now')
    def now_filter(format_string):
        """Template filter for current timestamp"""
        return datetime.now().strftime(format_string)
    
    # Add error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors"""
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Endpoint ikke funnet'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        app.logger.error(f'Server Error: {error}')
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Intern serverfeil'}), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected errors"""
        app.logger.error(f'Unexpected error: {error}', exc_info=True)
        if request.path.startswith('/api/'):
            return jsonify({'error': 'En uventet feil oppstod'}), 500
        return render_template('errors/500.html'), 500
    
    # Add CSRF error handler
    @app.errorhandler(400)
    def handle_csrf_error(e):
        """Handle CSRF errors gracefully"""
        from flask import redirect, url_for
        
        # Check if this is a CSRF error
        if isinstance(e, CSRFError) or 'csrf' in str(e).lower():
            app.logger.warning(f'CSRF error: {str(e)}')
            
            # Redirect based on request path
            if 'checkout' in request.path:
                return redirect(url_for('main.subscription'))
            elif 'login' in request.path:
                return redirect(url_for('main.login'))
            else:
                return redirect(url_for('main.index'))
        
        # If not a CSRF error, return standard 400 page
        return render_template('errors/400.html'), 400
    
    # Add specific CSRF error handler  
    @app.errorhandler(CSRFError)
    def handle_csrf_error_specific(e):
        """Handle CSRFError specifically"""
        from flask import redirect, url_for
        
        app.logger.warning(f'CSRFError: {str(e)}')
        
        if 'checkout' in request.path:
            return redirect(url_for('main.subscription'))
        elif 'login' in request.path:
            return redirect(url_for('main.login'))
        else:
            return redirect(url_for('main.index'))
    
    @app.context_processor
    def inject_utils():
        """Make utility functions available in templates"""
        return dict(
            now=datetime.utcnow,
            datetime=datetime
        )
