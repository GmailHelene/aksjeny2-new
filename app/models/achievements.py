"""
User achievements and gamification system
"""
from .. import db
from datetime import datetime

class Achievement(db.Model):
    """Achievement definitions"""
    __tablename__ = 'achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), default='bi-trophy')  # Bootstrap icon
    badge_color = db.Column(db.String(20), default='warning')  # Bootstrap color
    points = db.Column(db.Integer, default=10)
    category = db.Column(db.String(50), default='general')  # general, trading, analysis, social
    requirement_type = db.Column(db.String(50), nullable=False)  # predictions, logins, favorites, etc.
    requirement_count = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Achievement {self.name}>'

class UserAchievement(db.Model):
    """User achievements tracking"""
    __tablename__ = 'user_achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    progress = db.Column(db.Integer, default=1)  # For multi-step achievements
    
    # Relationships
    user = db.relationship('User', backref='user_achievements')
    achievement = db.relationship('Achievement')
    
    def __repr__(self):
        return f'<UserAchievement {self.user_id}:{self.achievement_id}>'

class UserStats(db.Model):
    """User activity statistics for achievements"""
    __tablename__ = 'user_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Trading/Analysis stats
    predictions_made = db.Column(db.Integer, default=0)
    successful_predictions = db.Column(db.Integer, default=0)
    stocks_analyzed = db.Column(db.Integer, default=0)
    portfolios_created = db.Column(db.Integer, default=0)
    
    # Platform engagement
    total_logins = db.Column(db.Integer, default=0)
    consecutive_login_days = db.Column(db.Integer, default=0)
    last_login_date = db.Column(db.Date)
    forum_posts = db.Column(db.Integer, default=0)
    favorites_added = db.Column(db.Integer, default=0)
    
    # Points and level
    total_points = db.Column(db.Integer, default=0)
    current_level = db.Column(db.Integer, default=1)
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('stats', uselist=False))
    
    def __repr__(self):
        return f'<UserStats {self.user_id}>'
    
    def add_points(self, points):
        """Add points and check for level up"""
        self.total_points += points
        # Simple level calculation: level = points // 100
        new_level = (self.total_points // 100) + 1
        if new_level > self.current_level:
            self.current_level = new_level
            return True  # Level up occurred
        return False
    
    def get_level_progress(self):
        """Get progress to next level (0-100)"""
        points_in_current_level = self.total_points % 100
        return points_in_current_level
    
    def update_consecutive_logins(self):
        """Update consecutive login streak"""
        from datetime import date, timedelta
        
        today = date.today()
        if self.last_login_date:
            if self.last_login_date == today:
                return  # Already logged in today
            elif self.last_login_date == today - timedelta(days=1):
                self.consecutive_login_days += 1
            else:
                self.consecutive_login_days = 1
        else:
            self.consecutive_login_days = 1
        
        self.last_login_date = today
        self.total_logins += 1

def init_default_achievements():
    """Initialize default achievements"""
    achievements = [
        {
            'name': 'Første innlogging',
            'description': 'Velkommen til Aksjeradar!',
            'icon': 'bi-door-open',
            'badge_color': 'success',
            'points': 10,
            'category': 'general',
            'requirement_type': 'logins',
            'requirement_count': 1
        },
        {
            'name': 'Trofas bruker',
            'description': 'Logget inn 7 dager på rad',
            'icon': 'bi-calendar-check',
            'badge_color': 'primary',
            'points': 50,
            'category': 'general',
            'requirement_type': 'consecutive_logins',
            'requirement_count': 7
        },
        {
            'name': 'Aksje-entusiast',
            'description': 'Lagt til 10 aksjer i favoritter',
            'icon': 'bi-star-fill',
            'badge_color': 'warning',
            'points': 25,
            'category': 'trading',
            'requirement_type': 'favorites',
            'requirement_count': 10
        },
        {
            'name': 'Portefølje-mester',
            'description': 'Opprettet din første portefølje',
            'icon': 'bi-briefcase-fill',
            'badge_color': 'info',
            'points': 30,
            'category': 'trading',
            'requirement_type': 'portfolios',
            'requirement_count': 1
        },
        {
            'name': 'Analysator',
            'description': 'Analysert 50 forskjellige aksjer',
            'icon': 'bi-graph-up',
            'badge_color': 'danger',
            'points': 75,
            'category': 'analysis',
            'requirement_type': 'stocks_analyzed',
            'requirement_count': 50
        },
        {
            'name': 'Forum-deltaker',
            'description': 'Skrevet ditt første innlegg i forumet',
            'icon': 'bi-chat-square-text',
            'badge_color': 'secondary',
            'points': 20,
            'category': 'social',
            'requirement_type': 'forum_posts',
            'requirement_count': 1
        }
    ]
    
    for ach_data in achievements:
        existing = Achievement.query.filter_by(name=ach_data['name']).first()
        if not existing:
            achievement = Achievement(**ach_data)
            db.session.add(achievement)
    
    db.session.commit()

def check_user_achievements(user_id, stat_type, new_value):
    """Check if user earned any new achievements"""
    from ..models.user import User
    
    user = User.query.get(user_id)
    if not user:
        return []
    
    # Get user's current achievements
    earned_achievement_ids = [ua.achievement_id for ua in user.user_achievements]
    
    # Check for new achievements
    new_achievements = []
    available_achievements = Achievement.query.filter(
        Achievement.requirement_type == stat_type,
        Achievement.requirement_count <= new_value,
        ~Achievement.id.in_(earned_achievement_ids),
        Achievement.is_active == True
    ).all()
    
    for achievement in available_achievements:
        user_achievement = UserAchievement(
            user_id=user_id,
            achievement_id=achievement.id,
            progress=new_value
        )
        db.session.add(user_achievement)
        
        # Add points to user stats
        if user.stats:
            level_up = user.stats.add_points(achievement.points)
            if level_up:
                # Could trigger level up achievement here
                pass
        
        new_achievements.append(achievement)
    
    db.session.commit()
    return new_achievements
