"""Notification models for Aksjeradar"""
from ..extensions import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
import enum

class NotificationType(enum.Enum):
    """Types of notifications"""
    PRICE_ALERT = "price_alert"
    VOLUME_ALERT = "volume_alert"
    NEWS_ALERT = "news_alert"
    AI_PREDICTION = "ai_prediction"
    PORTFOLIO_UPDATE = "portfolio_update"
    MARKET_ALERT = "market_alert"
    SYSTEM_ALERT = "system_alert"

class NotificationPriority(enum.Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Notification(db.Model):
    """User notifications"""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Changed from 'user.id' to 'users.id'
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(Enum(NotificationType), nullable=False, default=NotificationType.SYSTEM_ALERT)
    priority = Column(Enum(NotificationPriority), nullable=False, default=NotificationPriority.MEDIUM)
    
    # Related data
    ticker = Column(String(20), nullable=True)  # For stock-related notifications
    price = Column(Float, nullable=True)     # For price alerts
    threshold = Column(Float, nullable=True) # Alert threshold
    
    # Status tracking
    is_read = Column(Boolean, default=False, nullable=False)
    is_sent = Column(Boolean, default=False, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    
    # Push notification tracking
    push_sent = Column(Boolean, default=False, nullable=False)
    push_sent_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships - will be added after User model is imported
    # user = relationship('User', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.title} for user {self.user_id}>'
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()
    
    def mark_as_sent(self):
        """Mark notification as sent"""
        self.is_sent = True
        self.sent_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.type.value,
            'priority': self.priority.value,
            'ticker': self.ticker,
            'price': self.price,
            'threshold': self.threshold,
            'is_read': self.is_read,
            'is_sent': self.is_sent,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

class NotificationSettings(db.Model):
    """User notification preferences"""
    __tablename__ = 'notification_settings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)  # Changed from 'user.id' to 'users.id'
    
    # Email notifications
    email_enabled = Column(Boolean, default=True, nullable=False)
    email_price_alerts = Column(Boolean, default=True, nullable=False)
    email_news_alerts = Column(Boolean, default=True, nullable=False)
    email_ai_predictions = Column(Boolean, default=True, nullable=False)
    email_portfolio_updates = Column(Boolean, default=True, nullable=False)
    email_market_alerts = Column(Boolean, default=True, nullable=False)
    
    # Push notifications
    push_enabled = Column(Boolean, default=True, nullable=False)
    push_price_alerts = Column(Boolean, default=True, nullable=False)
    push_news_alerts = Column(Boolean, default=False, nullable=False)
    push_ai_predictions = Column(Boolean, default=True, nullable=False)
    push_portfolio_updates = Column(Boolean, default=False, nullable=False)
    push_market_alerts = Column(Boolean, default=True, nullable=False)
    
    # Push subscription data (for web push)
    push_subscription = Column(Text, nullable=True)  # JSON string
    
    # Timing preferences
    quiet_hours_start = Column(String(5), default='22:00', nullable=False)  # HH:MM format
    quiet_hours_end = Column(String(5), default='08:00', nullable=False)    # HH:MM format
    timezone = Column(String(50), default='Europe/Oslo', nullable=False)
    
    # User preferences (new fields)
    language = Column(String(8), default='nb', nullable=False)  # 'nb', 'en', etc.
    display_mode = Column(String(16), default='auto', nullable=False)  # 'light', 'dark', 'auto'
    number_format = Column(String(16), default='norwegian', nullable=False)  # 'norwegian', 'us', etc.
    dashboard_widgets = Column(Text, nullable=True)  # JSON string of enabled widgets
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships - will be added after User model is imported
    # user = relationship('User', backref='notification_settings', uselist=False)
    
    def __repr__(self):
        return f'<NotificationSettings for user {self.user_id}>'
    
    def is_quiet_hours(self):
        """Check if current time is within quiet hours"""
        from datetime import time
        import pytz
        
        try:
            tz = pytz.timezone(self.timezone)
            current_time = datetime.now(tz).time()
            
            start_time = time(*map(int, self.quiet_hours_start.split(':')))
            end_time = time(*map(int, self.quiet_hours_end.split(':')))
            
            if start_time <= end_time:
                return start_time <= current_time <= end_time
            else:  # Overnight quiet hours
                return current_time >= start_time or current_time <= end_time
        except:
            return False  # Default to not quiet hours if parsing fails

class AIModel(db.Model):
    """AI/ML model tracking and metadata"""
    __tablename__ = 'ai_models'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    model_type = Column(String(50), nullable=False)  # 'price_prediction', 'sentiment', 'recommendation'
    version = Column(String(20), nullable=False)
    
    # Model metadata
    description = Column(Text, nullable=True)
    features = Column(Text, nullable=True)  # JSON string of feature names
    parameters = Column(Text, nullable=True)  # JSON string of hyperparameters
    
    # Performance metrics
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)  # For regression models
    
    # Training information
    training_data_size = Column(Integer, nullable=True)
    training_date = Column(DateTime, nullable=True)
    training_duration = Column(Integer, nullable=True)  # Seconds
    
    # Status
    is_active = Column(Boolean, default=False, nullable=False)
    is_production = Column(Boolean, default=False, nullable=False)
    
    # File paths
    model_path = Column(String(255), nullable=True)
    scaler_path = Column(String(255), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<AIModel {self.id}: {self.name} v{self.version}>'

class PredictionLog(db.Model):
    """Log of AI predictions for tracking accuracy"""
    __tablename__ = 'prediction_logs'
    
    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey('ai_models.id'), nullable=False)
    ticker = Column(String(20), nullable=False)
    
    # Prediction data
    prediction_type = Column(String(50), nullable=False)  # 'price', 'direction', 'recommendation'
    predicted_value = Column(Float, nullable=True)
    predicted_direction = Column(String(10), nullable=True)  # 'up', 'down', 'neutral'
    confidence = Column(Float, nullable=True)  # 0-1 confidence score
    
    # Input data snapshot
    input_features = Column(Text, nullable=True)  # JSON string
    market_conditions = Column(Text, nullable=True)  # JSON string
    
    # Prediction context
    prediction_horizon = Column(Integer, nullable=False)  # Days ahead
    current_price = Column(Float, nullable=True)
    
    # Validation (filled when prediction period expires)
    actual_value = Column(Float, nullable=True)
    actual_direction = Column(String(10), nullable=True)
    is_correct = Column(Boolean, nullable=True)
    accuracy_score = Column(Float, nullable=True)
    
    # Metadata
    prediction_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    validation_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    model = relationship('AIModel', backref='predictions')
    
    def __repr__(self):
        return f'<PredictionLog {self.id}: {self.ticker} by model {self.model_id}>'
