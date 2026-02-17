"""
User Activity model for tracking user actions and events
"""
from datetime import datetime
from ..extensions import db

class UserActivity(db.Model):
    """Model for tracking user activities"""
    __tablename__ = 'user_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # 'buy', 'sell', 'watch', 'portfolio', 'alert'
    description = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('activities', lazy=True))
    
    def __init__(self, user_id, activity_type, description, details=None):
        self.user_id = user_id
        self.activity_type = activity_type
        self.description = description
        self.details = details
    
    @staticmethod
    def create_activity(user_id, activity_type, description, details=None):
        """Helper method to create and save a new activity"""
        try:
            activity = UserActivity(
                user_id=user_id,
                activity_type=activity_type,
                description=description,
                details=details
            )
            db.session.add(activity)
            db.session.commit()
            return activity
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating activity: {e}")
            return None
    
    @staticmethod
    def get_user_activities(user_id, limit=10):
        """Get recent activities for a user"""
        return UserActivity.query.filter_by(user_id=user_id)\
            .order_by(UserActivity.created_at.desc())\
            .limit(limit)\
            .all()
            
    def to_dict(self):
        """Convert activity to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'activity_type': self.activity_type,
            'description': self.description,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
