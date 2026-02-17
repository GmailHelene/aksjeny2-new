from ..extensions import db
from datetime import datetime

class UserNotificationPreferences(db.Model):
    """Unified notification preferences for all alert types and channels"""
    __tablename__ = 'user_notification_preferences'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)

    # Email
    email_enabled = db.Column(db.Boolean, default=True, nullable=False)
    email_price_alerts = db.Column(db.Boolean, default=True, nullable=False)
    email_news_alerts = db.Column(db.Boolean, default=True, nullable=False)
    email_portfolio_updates = db.Column(db.Boolean, default=True, nullable=False)
    email_watchlist_alerts = db.Column(db.Boolean, default=True, nullable=False)
    email_weekly_reports = db.Column(db.Boolean, default=True, nullable=False)

    # Push
    push_enabled = db.Column(db.Boolean, default=True, nullable=False)
    push_price_alerts = db.Column(db.Boolean, default=True, nullable=False)
    push_news_alerts = db.Column(db.Boolean, default=False, nullable=False)
    push_portfolio_updates = db.Column(db.Boolean, default=False, nullable=False)
    push_watchlist_alerts = db.Column(db.Boolean, default=True, nullable=False)
    push_weekly_reports = db.Column(db.Boolean, default=True, nullable=False)

    # In-app
    inapp_price_alerts = db.Column(db.Boolean, default=True, nullable=False)
    inapp_news_alerts = db.Column(db.Boolean, default=True, nullable=False)
    inapp_portfolio_updates = db.Column(db.Boolean, default=True, nullable=False)
    inapp_watchlist_alerts = db.Column(db.Boolean, default=True, nullable=False)
    inapp_weekly_reports = db.Column(db.Boolean, default=True, nullable=False)

    # Quiet hours
    quiet_hours_start = db.Column(db.String(5), default='22:00', nullable=False)
    quiet_hours_end = db.Column(db.String(5), default='08:00', nullable=False)
    timezone = db.Column(db.String(50), default='Europe/Oslo', nullable=False)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<UserNotificationPreferences for user {self.user_id}>'

    @staticmethod
    def get_or_create_for_user(user_id):
        prefs = UserNotificationPreferences.query.filter_by(user_id=user_id).first()
        if not prefs:
            prefs = UserNotificationPreferences(user_id=user_id)
            db.session.add(prefs)
            db.session.commit()
        return prefs
