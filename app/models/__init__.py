"""
Database models for Aksjeradar application
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Import db from the main app module
from .. import db

# Import existing models
from .user import User, DeviceTrialTracker
from .portfolio import Portfolio, PortfolioStock, Transaction
from .watchlist import Watchlist, WatchlistStock
from .trial_session import TrialSession
from .referral import Referral, ReferralDiscount
from .tip import StockTip
from .favorites import Favorites
from .activity import UserActivity
from .price_alert import PriceAlert, AlertNotificationSettings
from .strategy import Strategy
from .strategy_version import StrategyVersion
from .forum import ForumCategory, ForumTopic, ForumPost, ForumPostLike, ForumTopicView
from .achievements import Achievement, UserAchievement, UserStats

# Add new models to __all__
__all__ = [
    'User', 
    'DeviceTrialTracker',
    'Portfolio', 
    'PortfolioStock', 
    'Transaction',
    'Watchlist', 
    'WatchlistStock',
    'TrialSession',
    'Referral',
    'ReferralDiscount',
    'StockTip',
    'Favorites',
    'PriceAlert',
    'AlertNotificationSettings',
    'Strategy',
    'StrategyVersion',
    'ForumCategory',
    'ForumTopic', 
    'ForumPost',
    'ForumPostLike',
    'ForumTopicView',
    'Achievement',
    'UserAchievement', 
    'UserStats',
    'LoginAttempt',
    'UserSession',
    'ServiceRuntime'
]

class LoginAttempt(db.Model):
    __tablename__ = 'login_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    success = db.Column(db.Boolean, default=False, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<LoginAttempt {self.email} - {"Success" if self.success else "Failed"}>'

class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    user = db.relationship('User', backref=db.backref('sessions', lazy='dynamic'))
    
    def __repr__(self):
        return f'<UserSession {self.user_id} - {"Active" if self.is_active else "Inactive"}>'

class ServiceRuntime(db.Model):
    __tablename__ = 'service_runtime'

    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    last_start_time = db.Column(db.DateTime, nullable=True)
    start_count = db.Column(db.Integer, default=0, nullable=False)
    last_pid = db.Column(db.Integer, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @classmethod
    def record_start(cls, service_name: str):
        from sqlalchemy.exc import OperationalError
        try:
            inst = cls.query.filter_by(service_name=service_name).first()
            if not inst:
                inst = cls(service_name=service_name, start_count=0)
                db.session.add(inst)
            inst.start_count = (inst.start_count or 0) + 1
            inst.last_start_time = datetime.utcnow()
            try:
                import os as _os
                inst.last_pid = _os.getpid()
            except Exception:
                inst.last_pid = None
            db.session.commit()
            return inst
        except OperationalError:
            # Table might not exist yet during very early bootstrap
            db.session.rollback()
            return None
        except Exception:
            db.session.rollback()
            return None

    def to_dict(self):
        return {
            'service_name': self.service_name,
            'last_start_time': self.last_start_time.isoformat() if self.last_start_time else None,
            'start_count': self.start_count,
            'last_pid': self.last_pid,
        }
