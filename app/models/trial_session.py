from ..extensions import db
from datetime import datetime, timedelta
import hashlib

class TrialSession(db.Model):
    """Track trial sessions by device fingerprint to prevent reset by deleting cookies"""
    __tablename__ = 'trial_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    device_fingerprint = db.Column(db.String(128), unique=True, index=True, nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)  # IPv6 can be up to 45 chars
    user_agent = db.Column(db.Text, nullable=False)
    trial_start = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    is_expired = db.Column(db.Boolean, default=False)
    
    @staticmethod
    def create_device_fingerprint(ip_address, user_agent):
        """Create a unique fingerprint from IP and User-Agent"""
        combined = f"{ip_address}:{user_agent}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    @classmethod
    def get_or_create_session(cls, ip_address, user_agent):
        """Get existing session or create new one"""
        fingerprint = cls.create_device_fingerprint(ip_address, user_agent)
        
        session = cls.query.filter_by(device_fingerprint=fingerprint).first()
        if not session:
            session = cls(
                device_fingerprint=fingerprint,
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.session.add(session)
            db.session.commit()
        else:
            # Update last accessed time
            session.last_accessed = datetime.utcnow()
            db.session.commit()
            
        return session
    
    def is_trial_active(self, trial_duration_minutes=10):
        """Check if trial is still active (default 10 minutes)"""
        if self.is_expired:
            return False
            
        elapsed = datetime.utcnow() - self.trial_start
        return elapsed < timedelta(minutes=trial_duration_minutes)
    
    def expire_trial(self):
        """Manually expire the trial"""
        self.is_expired = True
        db.session.commit()
    
    def __repr__(self):
        return f'<TrialSession {self.device_fingerprint[:8]}... from {self.ip_address}>'
