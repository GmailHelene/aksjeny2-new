"""
Price Alert Model for tracking user stock price alerts
"""
from ..extensions import db
from datetime import datetime, timedelta
from sqlalchemy import event, and_
import logging

logger = logging.getLogger(__name__)

class PriceAlert(db.Model):
    """Model for stock price alerts that users can set"""
    __tablename__ = 'price_alerts'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ticker = db.Column(db.String(20), nullable=False, index=True)  # Required by database
    symbol = db.Column(db.String(20), nullable=False, index=True)
    target_price = db.Column(db.Float, nullable=False)
    alert_type = db.Column(db.String(10), nullable=False)  # 'above' or 'below'
    current_price = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_triggered = db.Column(db.Boolean, default=False, nullable=False)  # Required by database
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    triggered_at = db.Column(db.DateTime, nullable=True)
    last_checked = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Email notification settings
    email_sent = db.Column(db.Boolean, default=False, nullable=False)
    email_enabled = db.Column(db.Boolean, default=True, nullable=False)
    browser_enabled = db.Column(db.Boolean, default=False, nullable=False)
    
    # Database-required notification fields  
    notify_email = db.Column(db.Boolean, default=True, nullable=False)
    notify_push = db.Column(db.Boolean, default=False, nullable=False)
    auto_disable = db.Column(db.Boolean, default=False, nullable=False)
    
    # Database-required price fields
    threshold_price = db.Column(db.Float, nullable=True)
    threshold_percent = db.Column(db.Float, nullable=True) 
    last_price = db.Column(db.Float, nullable=True)
    
    # Database-required timestamp
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Additional metadata
    company_name = db.Column(db.String(100), nullable=True)
    exchange = db.Column(db.String(10), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationship with User
    user = db.relationship('User', backref=db.backref('user_price_alerts', lazy='dynamic', cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<PriceAlert {self.symbol} {self.alert_type} {self.target_price} for user {self.user_id}>'
    
    def __init__(self, **kwargs):
        # Ensure ticker is set to same value as symbol if not provided
        if 'symbol' in kwargs and 'ticker' not in kwargs:
            kwargs['ticker'] = kwargs['symbol']
        super(PriceAlert, self).__init__(**kwargs)
        logger.info(f"Creating price alert for {self.symbol} at {self.target_price}")
    
    @property
    def status(self):
        """Get current status of the alert"""
        if not self.is_active:
            return 'disabled'
        elif self.triggered_at:
            return 'triggered'
        else:
            return 'active'
    
    @property
    def conditions_met(self):
        """Check if alert conditions are met"""
        if not self.is_active or not self.current_price:
            return False
        
        if self.alert_type == 'above':
            return self.current_price >= self.target_price
        elif self.alert_type == 'below':
            return self.current_price <= self.target_price
        
        return False
    
    def check_and_trigger(self, current_price):
        """Check if alert should be triggered and update status"""
        self.current_price = current_price
        self.last_checked = datetime.utcnow()
        
        if self.conditions_met and not self.triggered_at:
            self.triggered_at = datetime.utcnow()
            self.is_triggered = True  # Set database column
            self.is_active = False  # Deactivate after triggering
            logger.info(f"Price alert triggered for {self.symbol}: {current_price} {self.alert_type} {self.target_price}")
            return True
        
        return False
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'ticker': self.ticker or self.symbol,  # Template compatibility
            'target_price': self.target_price,
            'target_value': self.target_price,  # Template compatibility
            'alert_type': self.alert_type,
            'type': self.alert_type,  # Template compatibility
            'condition': self.alert_type,  # Template compatibility
            'current_price': self.current_price,
            'is_active': self.is_active,
            'active': self.is_active,  # Template compatibility
            'is_triggered': getattr(self, 'is_triggered', False),
            'triggered': getattr(self, 'is_triggered', False),  # Template compatibility
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'last_checked': self.last_checked.isoformat() if self.last_checked else None,
            'company_name': self.company_name,
            'exchange': self.exchange,
            'notes': self.notes,
            'email_enabled': self.email_enabled,
            'browser_enabled': self.browser_enabled
        }
    
    @staticmethod
    def get_active_alerts_for_user(user_id):
        """Get all active alerts for a user"""
        return PriceAlert.query.filter_by(
            user_id=user_id, 
            is_active=True
        ).order_by(PriceAlert.created_at.desc()).all()
    
    @staticmethod
    def get_alerts_for_symbol(symbol):
        """Get all active alerts for a specific symbol"""
        return PriceAlert.query.filter_by(
            symbol=symbol.upper(), 
            is_active=True
        ).all()

class EmailQueue(db.Model):
    """Lightweight queue for pending alert notification emails"""
    __tablename__ = 'email_queue'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, index=True, nullable=False)
    payload = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(20), default='pending', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    processed_at = db.Column(db.DateTime, nullable=True)
    error = db.Column(db.Text, nullable=True)

    @staticmethod
    def enqueue(user_id: int, payload: dict):
        try:
            item = EmailQueue(user_id=user_id, payload=payload, status='pending')
            db.session.add(item)
            db.session.commit()
            logger.info(f"EMAIL_QUEUE: enqueued notification for user={user_id}")
            return item
        except Exception as e:
            logger.error(f"EMAIL_QUEUE enqueue failed user={user_id} error={e}")
            try:
                db.session.rollback()
            except Exception:
                pass
            return None
    
    @staticmethod
    def cleanup_old_triggered_alerts():
        """Clean up triggered alerts older than 30 days"""
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        old_alerts = PriceAlert.query.filter(
            PriceAlert.triggered_at < cutoff_date,
            PriceAlert.is_active == False
        ).all()
        
        for alert in old_alerts:
            db.session.delete(alert)
        
        try:
            db.session.commit()
            return len(old_alerts)
        except Exception as commit_error:
            logger.error(f"Error committing alert cleanup: {commit_error}")
            db.session.rollback()
            return 0


class AlertNotificationSettings(db.Model):
    """User notification preferences for price alerts"""
    __tablename__ = 'alert_notification_settings'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Email notifications
    email_enabled = db.Column(db.Boolean, default=True, nullable=False)
    email_instant = db.Column(db.Boolean, default=True, nullable=False)  # Send immediately when triggered
    email_daily_summary = db.Column(db.Boolean, default=False, nullable=False)  # Daily summary of alerts
    
    # Frequency limits to prevent spam
    max_alerts_per_day = db.Column(db.Integer, default=10, nullable=False)
    max_alerts_per_hour = db.Column(db.Integer, default=3, nullable=False)
    
    # Language preference
    language = db.Column(db.String(5), default='no', nullable=False)  # 'no' for Norwegian, 'en' for English
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship with User
    user = db.relationship('User', backref=db.backref('alert_settings', uselist=False, cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<AlertNotificationSettings for user {self.user_id}>'
    
    @staticmethod
    def get_or_create_for_user(user_id):
        """Get existing settings or create default ones for user"""
        settings = AlertNotificationSettings.query.filter_by(user_id=user_id).first()
        if not settings:
            settings = AlertNotificationSettings(user_id=user_id)
            db.session.add(settings)
            db.session.commit()
        return settings


# Database event listener for automatic cleanup without committing inside event
@event.listens_for(PriceAlert, 'after_insert')
def cleanup_old_alerts(mapper, connection, target):
    """Automatically cleanup old, inactive, triggered alerts in the same transaction.

    Important: Never call session.commit() inside flush/mapper events. Use the provided
    connection and Core expressions so the work participates in the outer transaction.
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        tbl = PriceAlert.__table__
        delete_stmt = tbl.delete().where(
            and_(
                tbl.c.triggered_at < cutoff_date,
                tbl.c.is_active == False
            )
        )
        connection.execute(delete_stmt)
    except Exception as e:
        logger.error(f"Error during alert cleanup: {e}")
