from datetime import datetime
from ..extensions import db

class Strategy(db.Model):
    __tablename__ = 'strategies'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    buy_rules = db.Column(db.JSON, nullable=True)
    sell_rules = db.Column(db.JSON, nullable=True)
    risk_rules = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict_basic(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_dict_full(self):
        return {
            'id': self.id,
            'name': self.name,
            'buy': self.buy_rules or {},
            'sell': self.sell_rules or {},
            'risk': self.risk_rules or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
