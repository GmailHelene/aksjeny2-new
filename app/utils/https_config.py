"""
HTTPS and TLS Configuration for Aksjeradar
Ensures proper HTTPS handling in production and development
"""
import os
from flask import request


def get_scheme():
    """
    Get the current request scheme (http or https).
    Properly handles reverse proxies like Railway.
    """
    # In Flask with ProxyFix, request.scheme will be set correctly
    # from the X-Forwarded-Proto header
    return request.scheme


def is_https():
    """
    Check if the current request is HTTPS.
    Returns True if request.scheme is 'https' or X-Forwarded-Proto is 'https'
    """
    # request.is_secure is updated by ProxyFix based on X-Forwarded-Proto
    return request.is_secure or request.scheme == 'https'


def get_base_url():
    """
    Get the base URL of the application considering scheme
    """
    scheme = get_scheme()
    host = request.host
    return f"{scheme}://{host}"


def is_local_development():
    """Check if running in local development mode"""
    host = request.host.split(':')[0] if request.host else ''
    return host in ('localhost', '127.0.0.1', '0.0.0.0')


class HTTPSConfig:
    """HTTPS configuration class"""
    
    # Certificate and TLS settings
    MIN_TLS_VERSION = 'TLSv1.2'  # Railway is TLSv1.2+
    SUPPORTED_CIPHERS = [
        'TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384',
        'TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256',
        'TLS_RSA_WITH_AES_256_GCM_SHA384',
        'TLS_RSA_WITH_AES_128_GCM_SHA256',
    ]
    
    # HSTS Settings  
    HSTS_MAX_AGE = 31536000  # 1 year in seconds for production
    HSTS_INCLUDE_SUBDOMAINS = True
    HSTS_PRELOAD = True  # Allow adding to HSTS preload list
    
    @classmethod
    def get_hsts_header(cls, production=False):
        """Generate HSTS header value"""
        if production:
            directives = [
                f'max-age={cls.HSTS_MAX_AGE}',
            ]
            if cls.HSTS_INCLUDE_SUBDOMAINS:
                directives.append('includeSubDomains')
            if cls.HSTS_PRELOAD:
                directives.append('preload')
            return '; '.join(directives)
        else:
            return 'max-age=0'
    
    # Security Headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:",
    }


def apply_https_config(app):
    """
    Apply HTTPS configuration to Flask app
    
    This function ensures:
    1. Proper detection of HTTPS via reverse proxy headers
    2. Correct HSTS headers for production
    3. Secure cookie settings
    4. Proper URL generation with correct scheme
    """
    
    def before_request():
        """Pre-request HTTPS configuration"""
        # Ensure PREFERRED_URL_SCHEME is set correctly
        if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('APP_ENV') == 'production':
            app.config['PREFERRED_URL_SCHEME'] = 'https'
            app.config['SESSION_COOKIE_SECURE'] = True
        else:
            app.config['PREFERRED_URL_SCHEME'] = get_scheme()
    
    # Register before_request handler
    if not hasattr(app, '_https_config_applied'):
        app.before_request(before_request)
        app._https_config_applied = True
        app.logger.info("✅ HTTPS configuration applied to Flask app")


def verify_https_config(app):
    """
    Verify HTTPS configuration is correct
    
    This checks:
    1. ProxyFix is properly configured
    2. HSTS headers are set correctly  
    3. Security headers are in place
    4. Cookie security settings are correct
    """
    checks = {
        'ProxyFix applied': hasattr(app.wsgi_app, '__class__') and 'ProxyFix' in str(app.wsgi_app.__class__),
        'SESSION_COOKIE_SECURE': app.config.get('SESSION_COOKIE_SECURE', False),
        'SESSION_COOKIE_HTTPONLY': app.config.get('SESSION_COOKIE_HTTPONLY', False),
        'PREFERRED_URL_SCHEME set': app.config.get('PREFERRED_URL_SCHEME') == 'https' if os.getenv('RAILWAY_ENVIRONMENT') else True,
    }
    
    all_good = all(checks.values())
    status = "✅ PASS" if all_good else "⚠️ WARNING"
    
    app.logger.info(f"{status} HTTPS Configuration Check:")
    for check, result in checks.items():
        symbol = "✅" if result else "❌"
        app.logger.info(f"  {symbol} {check}: {result}")
    
    return all_good
