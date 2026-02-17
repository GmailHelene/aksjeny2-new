import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Standard Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Mail settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Redis configuration
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Enhanced Authentication Settings
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=31)
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Cache Settings
    CACHE_TYPE = "redis"
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Security Settings
    WTF_CSRF_TIME_LIMIT = 3600
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', 'your-salt-here')
    
    # Two-Factor Authentication
    TOTP_ISSUER_NAME = "Aksjeradar"
    
    # API Rate Limits
    API_RATE_LIMIT_PER_MINUTE = int(os.environ.get('API_RATE_LIMIT_PER_MINUTE', '60'))
    API_RATE_LIMIT_PER_HOUR = int(os.environ.get('API_RATE_LIMIT_PER_HOUR', '1000'))
    
    # Stripe Configuration - Production Keys
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # Stripe Price IDs - Production Prices
    STRIPE_MONTHLY_PRICE_ID = os.environ.get('STRIPE_MONTHLY_PRICE_ID')
    STRIPE_YEARLY_PRICE_ID = os.environ.get('STRIPE_YEARLY_PRICE_ID')
    STRIPE_LIFETIME_PRICE_ID = os.environ.get('STRIPE_LIFETIME_PRICE_ID')
    
    # Additional Stripe Configuration
    STRIPE_WEBHOOK_ENDPOINT_SECRET = os.environ.get('STRIPE_WEBHOOK_ENDPOINT_SECRET', STRIPE_WEBHOOK_SECRET)
    VALIDATE_STRIPE_ON_STARTUP = os.environ.get('VALIDATE_STRIPE_ON_STARTUP', 'true').lower() == 'true'
    
    # Translation Services Configuration
    # ConveyThis: Get API key from https://app.conveythis.com/account/register/
    # After registration: Dashboard > Settings > API Key
    CONVEYTHIS_API_KEY = os.environ.get('CONVEYTHIS_API_KEY')  # Set your ConveyThis API key here
    GOOGLE_TRANSLATE_API_KEY = os.environ.get('GOOGLE_TRANSLATE_API_KEY')
    
    # Translation Settings
    DEFAULT_LANGUAGE = 'no'  # Norwegian as source
    SUPPORTED_LANGUAGES = ['no', 'en']  # Norwegian and English
    TRANSLATION_SERVICE = os.environ.get('TRANSLATION_SERVICE', 'browser')  # browser, conveythis, google

class DevelopmentConfig(Config):
    DEBUG = True
    SOCKETIO_FORCE_THREADING = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'
    SOCKETIO_FORCE_THREADING = True
    # Keep attributes available after commit to avoid DetachedInstanceError in tests
    SQLALCHEMY_SESSION_OPTIONS = {"expire_on_commit": False}

class ProductionConfig(Config):
    DEBUG = False
    IS_REAL_PRODUCTION = True
    
    # Production-specific settings
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_SSL_STRICT = True
    
    # Override with production values
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://user:pass@localhost/aksjeradar_prod'

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
ASSETS_VERSION = "1756734079"
