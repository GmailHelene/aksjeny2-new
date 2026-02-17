from ..extensions import db
from datetime import datetime
import uuid
import string
import random

class Referral(db.Model):
    """Model for tracking referrals between users"""
    __tablename__ = 'referrals'
    
    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    referred_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    referral_code = db.Column(db.String(20), unique=True, nullable=False)
    email_used = db.Column(db.String(120), nullable=True)  # Email used for referral
    is_completed = db.Column(db.Boolean, default=False)  # True when referred user subscribes
    discount_used = db.Column(db.Boolean, default=False)  # True when referrer uses their discount
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    referrer = db.relationship('User', foreign_keys=[referrer_id], backref='sent_referrals')
    referred_user = db.relationship('User', foreign_keys=[referred_user_id], backref='received_referral')
    
    @staticmethod
    def generate_referral_code():
        """Generate a unique referral code"""
        while True:
            # Generate 8-character alphanumeric code
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not Referral.query.filter_by(referral_code=code).first():
                return code
    
    def __repr__(self):
        return f'<Referral {self.referral_code}>'

class ReferralDiscount(db.Model):
    """Model for tracking referral discounts"""
    __tablename__ = 'referral_discounts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    referral_id = db.Column(db.Integer, db.ForeignKey('referrals.id'), nullable=False)
    discount_percentage = db.Column(db.Float, default=20.0)  # 20% discount
    is_used = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=True)  # Optional expiration
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='referral_discounts')
    referral = db.relationship('Referral', backref='discount')
    
    def is_valid(self):
        """Check if discount is still valid"""
        if self.is_used:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True
    
    def __repr__(self):
        return f'<ReferralDiscount {self.discount_percentage}% for User {self.user_id}>'
