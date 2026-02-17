from ..extensions import db
from sqlalchemy.exc import IntegrityError
from datetime import datetime

class Favorites(db.Model):
    """Model for user favorite stocks"""
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(255))
    exchange = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to user
    user = db.relationship('User', backref=db.backref('favorites', lazy='dynamic'))
    
    # Ensure unique symbol per user
    __table_args__ = (db.UniqueConstraint('user_id', 'symbol', name='unique_user_symbol'),)
    
    def __repr__(self):
        return f'<Favorite {self.symbol} for user {self.user_id}>'
    
    @classmethod
    def is_favorite(cls, user_id, symbol):
        """Check if a stock is favorited by a user"""
        return cls.query.filter_by(user_id=user_id, symbol=symbol).first() is not None
    
    @classmethod
    def add_favorite(cls, user_id, symbol, name=None, exchange=None):
        """Add a stock to favorites with improved error handling"""
        from ..extensions import db
        
        # Check for existing favorite first
        existing = cls.query.filter_by(user_id=user_id, symbol=symbol).first()
        if existing:
            return existing

        favorite = cls(
            user_id=user_id,
            symbol=symbol,
            name=name,
            exchange=exchange
        )
        
        try:
            db.session.add(favorite)
            db.session.commit()
            return favorite
        except IntegrityError:
            # Handle concurrent insertions
            db.session.rollback()
            return cls.query.filter_by(user_id=user_id, symbol=symbol).first()
        except Exception as e:
            # Log error and rollback
            db.session.rollback()
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error adding favorite {symbol} for user {user_id}: {e}")
            raise
    
    @classmethod
    def remove_favorite(cls, user_id, symbol):
        """Remove a stock from favorites with improved error handling"""
        from ..extensions import db
        
        try:
            favorite = cls.query.filter_by(user_id=user_id, symbol=symbol).first()
            if favorite:
                db.session.delete(favorite)
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error removing favorite {symbol} for user {user_id}: {e}")
            raise
    
    @classmethod
    def get_user_favorites(cls, user_id):
        """Get all favorites for a user"""
        return cls.query.filter_by(user_id=user_id).order_by(cls.created_at.desc()).all()
