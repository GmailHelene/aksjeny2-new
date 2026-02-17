"""
User statistics tracking model.
"""
from datetime import datetime
from ..extensions import db

class UserStats(db.Model):
    """Model for tracking user statistics and achievements"""
    __tablename__ = 'user_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Achievement tracking
    stocks_analyzed = db.Column(db.Integer, default=0)
    portfolios_created = db.Column(db.Integer, default=0)
    watchlists_created = db.Column(db.Integer, default=0)
    alerts_created = db.Column(db.Integer, default=0)
    logins_count = db.Column(db.Integer, default=0)
    days_active = db.Column(db.Integer, default=0)
    
    # Feature usage tracking
    sentiment_analyses = db.Column(db.Integer, default=0)
    technical_analyses = db.Column(db.Integer, default=0)
    buffett_analyses = db.Column(db.Integer, default=0)
    screener_searches = db.Column(db.Integer, default=0)
    portfolio_updates = db.Column(db.Integer, default=0)
    alerts_triggered = db.Column(db.Integer, default=0)
    
    # Activity timestamps
    first_login = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    last_analysis = db.Column(db.DateTime, nullable=True)
    last_portfolio_update = db.Column(db.DateTime, nullable=True)
    last_alert_created = db.Column(db.DateTime, nullable=True)
    
    # Achievement flags
    completed_profile = db.Column(db.Boolean, default=False)
    verified_email = db.Column(db.Boolean, default=False)
    added_first_stock = db.Column(db.Boolean, default=False)
    created_first_alert = db.Column(db.Boolean, default=False)
    shared_first_analysis = db.Column(db.Boolean, default=False)
    
    # Feature discovery
    used_sentiment = db.Column(db.Boolean, default=False)
    used_technical = db.Column(db.Boolean, default=False)
    used_buffett = db.Column(db.Boolean, default=False)
    used_screener = db.Column(db.Boolean, default=False)
    used_alerts = db.Column(db.Boolean, default=False)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('stats', uselist=False))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserStats for User {self.user_id}>'
    
    @classmethod
    def get_or_create(cls, user_id):
        """Get existing stats or create new ones for user"""
        stats = cls.query.filter_by(user_id=user_id).first()
        if not stats:
            stats = cls(user_id=user_id)
            db.session.add(stats)
            db.session.commit()
        return stats
    
    def update_login(self):
        """Update login related statistics"""
        self.last_login = datetime.utcnow()
        self.logins_count += 1
        db.session.commit()
    
    def increment_stat(self, stat_name, commit=True):
        """Increment a statistic by 1"""
        if hasattr(self, stat_name):
            current_value = getattr(self, stat_name)
            if isinstance(current_value, int):
                setattr(self, stat_name, current_value + 1)
                if commit:
                    db.session.commit()
                return True
        return False
    
    def set_flag(self, flag_name, value=True, commit=True):
        """Set a boolean flag"""
        if hasattr(self, flag_name):
            current_value = getattr(self, flag_name)
            if isinstance(current_value, bool):
                setattr(self, flag_name, value)
                if commit:
                    db.session.commit()
                return True
        return False
    
    def update_timestamp(self, field_name, commit=True):
        """Update a timestamp field to current time"""
        if hasattr(self, field_name):
            setattr(self, field_name, datetime.utcnow())
            if commit:
                db.session.commit()
            return True
        return False
    
    def get_achievement_progress(self):
        """Get achievement completion status"""
        achievements = {
            'profile_complete': {
                'name': 'Fullført Profil',
                'completed': self.completed_profile,
                'description': 'Opprett en fullstendig brukerprofil'
            },
            'email_verified': {
                'name': 'Verifisert E-post',
                'completed': self.verified_email,
                'description': 'Bekreft e-postadressen din'
            },
            'first_stock': {
                'name': 'Første Investering',
                'completed': self.added_first_stock,
                'description': 'Legg til din første aksje i porteføljen'
            },
            'first_alert': {
                'name': 'Første Varsling',
                'completed': self.created_first_alert,
                'description': 'Opprett ditt første prisvarsel'
            },
            'first_share': {
                'name': 'Første Deling',
                'completed': self.shared_first_analysis,
                'description': 'Del din første analyse'
            },
            'feature_explorer': {
                'name': 'Funksjonsutforsker',
                'completed': all([
                    self.used_sentiment,
                    self.used_technical,
                    self.used_buffett,
                    self.used_screener,
                    self.used_alerts
                ]),
                'description': 'Prøv alle hovedfunksjonene'
            }
        }
        
        return {
            'achievements': achievements,
            'total_completed': sum(1 for a in achievements.values() if a['completed']),
            'total_available': len(achievements)
        }
    
    def get_usage_stats(self):
        """Get user usage statistics"""
        return {
            'analyses': {
                'sentiment': self.sentiment_analyses,
                'technical': self.technical_analyses,
                'buffett': self.buffett_analyses,
                'screener': self.screener_searches
            },
            'portfolio': {
                'updates': self.portfolio_updates,
                'alerts': self.alerts_created,
                'alerts_triggered': self.alerts_triggered
            },
            'engagement': {
                'logins': self.logins_count,
                'days_active': self.days_active
            }
        }
