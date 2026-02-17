import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Basic configurations - ensure proper fallbacks
    SECRET_KEY = os.getenv('SECRET_KEY') or 'dev-key-change-this-in-production-secure-2025'
    WTF_CSRF_SECRET_KEY = os.getenv('WTF_CSRF_SECRET_KEY') or 'csrf-key-change-this-in-production-secure-2025'
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Session and Cookie Security Configuration
    PERMANENT_SESSION_LIFETIME = 14400  # 4 hours
    SESSION_PERMANENT = True
    SESSION_COOKIE_NAME = 'aksjeradar_session'
    SESSION_COOKIE_HTTPONLY = True  # Prevent XSS access to session cookies
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection while allowing normal navigation
    
    # CSRF Protection - Increase token lifetime to prevent expiration issues
    WTF_CSRF_TIME_LIMIT = 14400  # 4 hours (default is 3600 = 1 hour)
    WTF_CSRF_SSL_STRICT = False  # Allow CSRF over HTTP for development
    WTF_CSRF_ENABLED = True
    
    # Remember Me Cookie Security
    REMEMBER_COOKIE_NAME = 'aksjeradar_remember'
    REMEMBER_COOKIE_DURATION = 2592000  # 30 days in seconds
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Database configuration with connection pool settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'echo': os.getenv('SQL_ECHO', 'False').lower() == 'true'
    }
    
    # Stripe configuration with secure fallback values and null checks
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY') or 'sk_test_dummy_key_for_development_only'
    STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY') or 'pk_test_dummy_key_for_development_only'
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLIC_KEY') or 'pk_test_dummy_key_for_development_only'
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET') or 'whsec_dummy_webhook_secret_for_development'
    
    # Price IDs for different subscription tiers with secure fallbacks
    STRIPE_MONTHLY_PRICE_ID = os.getenv('STRIPE_MONTHLY_PRICE_ID') or 'price_monthly_default_dev'
    STRIPE_YEARLY_PRICE_ID = os.getenv('STRIPE_YEARLY_PRICE_ID') or 'price_yearly_default_dev'
    STRIPE_LIFETIME_PRICE_ID = os.getenv('STRIPE_LIFETIME_PRICE_ID') or 'price_lifetime_default_dev'
    
    # Mail configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER') or os.getenv('MAIL_USERNAME')
    
    # API Keys with safe fallbacks
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') or None
    YAHOO_FINANCE_API_KEY = os.getenv('YAHOO_FINANCE_API_KEY') or None
    FMP_API_KEY = os.getenv('FMP_API_KEY') or 'demo'
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY') or 'demo'
    POLYGON_API_KEY = os.getenv('POLYGON_API_KEY') or None
    FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY') or None
    
    # Server configuration for proper URL generation
    SERVER_NAME = os.getenv('SERVER_NAME')  # Set to 'aksjeradar.trade' in production
    PREFERRED_URL_SCHEME = os.getenv('PREFERRED_URL_SCHEME', 'https' if not DEBUG else 'http')
    
    # API endpoints that should be accessible without authentication
    EXEMPT_ENDPOINTS = {
        'api.get_crypto_trending',
        'api.get_economic_indicators', 
        'api.get_market_sectors',
        'api.search_stocks',
        'api.market_data',
        'api.market_summary',
        'api.get_news',
        'api.get_crypto_data',
        'api.get_currency_rates',
        'api.health_check'
    }

    # File upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Export folder for generated reports
    EXPORT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports')
    
    # Cache configuration
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'memory://')

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    IS_REAL_PRODUCTION = False
    # Override dangerous settings for development
    WTF_CSRF_SSL_STRICT = False

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    IS_REAL_PRODUCTION = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing
    # Provide a SERVER_NAME so url_for can be used outside a request context in tests
    SERVER_NAME = 'localhost.test'
    # Keep attributes available after commit to prevent DetachedInstanceError in tests
    SQLALCHEMY_SESSION_OPTIONS = {"expire_on_commit": False}

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    IS_REAL_PRODUCTION = True
    
    # Use DATABASE_URL from Railway/production environment
    database_url = os.getenv('DATABASE_URL') or os.getenv('SQLALCHEMY_DATABASE_URI') or 'sqlite:///app.db'
    
    # Fix postgres:// to postgresql:// if needed (Railway compatibility)
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = database_url
    
    # Security settings for production
    WTF_CSRF_SSL_STRICT = True
    PREFERRED_URL_SCHEME = 'https'
    
    # Secure cookie settings for production
    SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS
    SESSION_COOKIE_SAMESITE = 'Lax'  # Protect against CSRF
    REMEMBER_COOKIE_SECURE = True  # Remember me cookies only over HTTPS

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}