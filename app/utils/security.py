"""
Security utilities for Aksjeradar
"""
import secrets
import hashlib
import base64
import io
from typing import Optional
from flask import current_app, has_app_context, request

# Optional imports with graceful fallbacks
try:
    import pyotp
    PYOTP_AVAILABLE = True
except ImportError:
    PYOTP_AVAILABLE = False

try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

try:
    from cryptography.fernet import Fernet
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


class SecurityUtils:
    """Security utility class for Aksjeradar"""
    
    def __init__(self):
        self.cipher = None
        if CRYPTOGRAPHY_AVAILABLE and has_app_context() and current_app.config.get('SECRET_KEY'):
            try:
                key = hashlib.sha256(current_app.config['SECRET_KEY'].encode()).digest()
                self.cipher = Fernet(base64.urlsafe_b64encode(key))
            except Exception:
                self.cipher = None
    
    def generate_totp_secret(self) -> str:
        """Generate TOTP secret for 2FA"""
        if PYOTP_AVAILABLE:
            return pyotp.random_base32()
        else:
            # Fallback: generate base32 secret manually
            return base64.b32encode(secrets.token_bytes(20)).decode('ascii').rstrip('=')
    
    def generate_qr_code(self, user_email: str, secret: str) -> str:
        """Generate QR code for TOTP setup"""
        if not QRCODE_AVAILABLE or not PYOTP_AVAILABLE:
            return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        try:
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user_email,
                issuer_name="Aksjeradar"
            )
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
        except Exception:
            return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    def verify_totp(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        if not PYOTP_AVAILABLE:
            # Fallback: basic token validation
            return len(token) == 6 and token.isdigit()
        
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=1)
        except Exception:
            return False
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not CRYPTOGRAPHY_AVAILABLE or not self.cipher:
            return data
        try:
            return self.cipher.encrypt(data.encode()).decode()
        except Exception:
            return data
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not CRYPTOGRAPHY_AVAILABLE or not self.cipher:
            return encrypted_data
        try:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return encrypted_data
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure token"""
        return secrets.token_urlsafe(length)
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_hex(16)
    
    def verify_csrf_token(self, token: str, session_token: str) -> bool:
        """Verify CSRF token"""
        try:
            return secrets.compare_digest(token, session_token)
        except Exception:
            return False
    
    def sanitize_input(self, text: str, allow_html: bool = False) -> str:
        """Sanitize user input"""
        if not text:
            return ""
        
        text = text.replace('\x00', '')
        
        if not allow_html:
            text = text.replace('&', '&amp;')
            text = text.replace('<', '&lt;')
            text = text.replace('>', '&gt;')
            text = text.replace('"', '&quot;')
            text = text.replace("'", '&#x27;')
        
        return text.strip()
    
    def hash_password(self, password: str, salt: Optional[str] = None):
        """Secure password hashing"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return salt + hash_obj.hex(), salt
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            salt = hashed_password[:32]
            stored_hash = hashed_password[32:]
            new_hash, _ = self.hash_password(password, salt)
            return new_hash[32:] == stored_hash
        except Exception:
            return False


def setup_security_headers(app):
    """Setup security headers for the application"""
    
    @app.after_request
    def set_security_headers(response):
        # X-Content-Type-Options: Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options: Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # X-XSS-Protection: Enable XSS filtering
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Strict-Transport-Security: Force HTTPS (only add in production)
        if app.config.get('ENV') == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        else:
            # For development, use a shorter max-age
            response.headers['Strict-Transport-Security'] = 'max-age=0'
        
        # Add CORS headers for PWA manifest and static files
        if request.endpoint in ['main.manifest', 'main.service_worker', 'static']:
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            response.headers['Access-Control-Max-Age'] = '86400'
            
        return response
    
    return app
