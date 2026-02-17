from datetime import datetime
from ..extensions import db

class StrategyVersion(db.Model):
    __tablename__ = 'strategy_versions'
    __table_args__ = (
        db.Index('ix_strategy_versions_strategy_version', 'strategy_id', 'version'),
    )
    id = db.Column(db.Integer, primary_key=True)
    strategy_id = db.Column(db.Integer, db.ForeignKey('strategies.id'), index=True, nullable=False)
    user_id = db.Column(db.Integer, index=True, nullable=False)
    version = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    buy_rules = db.Column(db.JSON)
    sell_rules = db.Column(db.JSON)
    risk_rules = db.Column(db.JSON)
    checksum = db.Column(db.String(64), index=True)  # sha256 hex digest of canonical serialized content
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'strategy_id': self.strategy_id,
            'version': self.version,
            'name': self.name,
            'buy': self.buy_rules,
            'sell': self.sell_rules,
            'risk': self.risk_rules,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
