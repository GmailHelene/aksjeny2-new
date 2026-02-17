from ..extensions import db
from datetime import datetime

class Watchlist(db.Model):
    __tablename__ = 'watchlists'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Alert settings
    price_alerts_enabled = db.Column(db.Boolean, default=True)
    technical_alerts_enabled = db.Column(db.Boolean, default=True)
    news_alerts_enabled = db.Column(db.Boolean, default=True)
    weekly_report_enabled = db.Column(db.Boolean, default=True)
    
    # Relationships - using backref for consistency  
    items = db.relationship('WatchlistItem', backref='watchlist', lazy=True, cascade='all, delete-orphan')
    # NOTE: user relationship is defined in User model via backref
    
    def __repr__(self):
        return f'<Watchlist {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'items_count': len(self.items),
            'settings': {
                'price_alerts_enabled': self.price_alerts_enabled,
                'technical_alerts_enabled': self.technical_alerts_enabled,
                'news_alerts_enabled': self.news_alerts_enabled,
                'weekly_report_enabled': self.weekly_report_enabled
            }
        }

class WatchlistItem(db.Model):
    __tablename__ = 'watchlist_items'
    
    id = db.Column(db.Integer, primary_key=True)
    watchlist_id = db.Column(db.Integer, db.ForeignKey('watchlists.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Alert preferences for this specific stock
    price_threshold_up = db.Column(db.Float)  # Alert when price goes above this
    price_threshold_down = db.Column(db.Float)  # Alert when price goes below this
    rsi_alerts = db.Column(db.Boolean, default=True)
    volume_alerts = db.Column(db.Boolean, default=True)
    
    # Performance tracking
    entry_price = db.Column(db.Float)  # Price when added to watchlist
    target_price = db.Column(db.Float)  # User's target price
    stop_loss = db.Column(db.Float)  # User's stop loss level
    
    # Relationship - using backref for consistency
    # NOTE: watchlist relationship is defined in Watchlist model via backref
    
    def __repr__(self):
        return f'<WatchlistItem {self.symbol}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'watchlist_id': self.watchlist_id,
            'symbol': self.symbol,
            'notes': self.notes,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'price_threshold_up': self.price_threshold_up,
            'price_threshold_down': self.price_threshold_down,
            'entry_price': self.entry_price,
            'target_price': self.target_price,
            'stop_loss': self.stop_loss,
            'rsi_alerts': self.rsi_alerts,
            'volume_alerts': self.volume_alerts
        }

class WatchlistStock(db.Model):
    """Legacy model - kept for backward compatibility"""
    __tablename__ = 'watchlist_stocks'
    id = db.Column(db.Integer, primary_key=True)
    watchlist_id = db.Column(db.Integer, db.ForeignKey('watchlists.id'))
    ticker = db.Column(db.String(20))
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    price_alert_high = db.Column(db.Float, nullable=True)
    price_alert_low = db.Column(db.Float, nullable=True)
    notes = db.Column(db.String(256))

class WatchlistAlert(db.Model):
    __tablename__ = 'watchlist_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    watchlist_item_id = db.Column(db.Integer, db.ForeignKey('watchlist_items.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # price_change, rsi, volume, etc.
    severity = db.Column(db.String(20), default='medium')  # low, medium, high
    
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    action_recommended = db.Column(db.Text)
    
    triggered_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    dismissed_at = db.Column(db.DateTime)
    
    # Alert data (JSON)
    alert_data = db.Column(db.JSON)
    
    # Relationships
    watchlist_item = db.relationship('WatchlistItem', backref='alerts', lazy=True)
    
    def __repr__(self):
        return f'<WatchlistAlert {self.title}>'
    
    def mark_as_read(self):
        self.read_at = datetime.utcnow()
        db.session.commit()
    
    def dismiss(self):
        self.dismissed_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'watchlist_item_id': self.watchlist_item_id,
            'symbol': self.watchlist_item.symbol if self.watchlist_item else None,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'message': self.message,
            'action_recommended': self.action_recommended,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'dismissed_at': self.dismissed_at.isoformat() if self.dismissed_at else None,
            'alert_data': self.alert_data,
            'is_read': self.read_at is not None,
            'is_dismissed': self.dismissed_at is not None
        }