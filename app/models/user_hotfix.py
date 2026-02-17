from ..extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from sqlalchemy import text

class DeviceTrialTracker(db.Model):
    """Track trial usage per device to prevent abuse by clearing cookies"""
    __tablename__ = 'device_trial_tracker'
    
    id = db.Column(db.Integer, primary_key=True)
    device_fingerprint = db.Column(db.String(32), unique=True, index=True, nullable=False)
    trial_start_time = db.Column(db.DateTime, default=datetime.utcnow)
    trial_used = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DeviceTrialTracker {self.device_fingerprint}>'
    
    def trial_expired(self):
        """Check if trial period has expired - Always returns False as trials are permanently disabled"""
        return False

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    portfolios = db.relationship('Portfolio', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    watchlists = db.relationship('Watchlist', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    # Subscription fields
    has_subscription = db.Column(db.Boolean, default=False)
    subscription_type = db.Column(db.String(20), default='free')
    subscription_start = db.Column(db.DateTime, nullable=True)
    subscription_end = db.Column(db.DateTime, nullable=True)
    trial_used = db.Column(db.Boolean, default=False)
    trial_start = db.Column(db.DateTime, nullable=True)
    stripe_customer_id = db.Column(db.String(128), nullable=True)
    reports_used_this_month = db.Column(db.Integer, default=0)
    last_reset_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Basic settings (only safe columns that exist in DB)
    language = db.Column(db.String(10), default='no')
    notification_settings = db.Column(db.Text, nullable=True)
    
    # COMMENTED OUT PROBLEMATIC COLUMNS - WILL ADD BACK AFTER DB MIGRATION
    # email_notifications = db.Column(db.Boolean, default=True, nullable=True)
    # price_alerts = db.Column(db.Boolean, default=True, nullable=True)
    # market_news = db.Column(db.Boolean, default=True, nullable=True)
    # first_name = db.Column(db.String(50), nullable=True)
    # last_name = db.Column(db.String(50), nullable=True)
    # two_factor_enabled = db.Column(db.Boolean, default=False, nullable=False)
    # two_factor_secret = db.Column(db.String(32), nullable=True)
    # email_verified = db.Column(db.Boolean, default=True, nullable=False)
    # is_locked = db.Column(db.Boolean, default=False, nullable=False)
    # last_login = db.Column(db.DateTime, nullable=True)
    # login_count = db.Column(db.Integer, default=0, nullable=False)
    # reset_token = db.Column(db.String(100), nullable=True)
    # reset_token_expires = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    # Property methods for missing columns (fallback values)
    @property
    def email_notifications(self):
        return True
    
    @property
    def price_alerts(self):
        return True
    
    @property
    def market_news(self):
        return True
    
    @property
    def first_name(self):
        return None
    
    @property
    def last_name(self):
        return None
    
    @property
    def two_factor_enabled(self):
        return False
    
    @property
    def two_factor_secret(self):
        return None
    
    @property
    def email_verified(self):
        return True
    
    @property
    def is_locked(self):
        return False
    
    @property
    def last_login(self):
        return None
    
    @property
    def login_count(self):
        return 0
    
    @property
    def reset_token(self):
        return None
    
    @property
    def reset_token_expires(self):
        return None
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False
    
    def get_user_preferences(self):
        """Get user notification preferences with safe fallbacks"""
        return {
            'email_notifications': True,
            'price_alerts': True,
            'market_news': True,
            'language': self.language or 'no'
        }

# Login manager user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
