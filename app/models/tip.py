from ..extensions import db
from datetime import datetime

class StockTip(db.Model):
    __tablename__ = 'stock_tips'
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), nullable=False)
    tip_type = db.Column(db.String(10), nullable=False)  # BUY, SELL, HOLD
    confidence = db.Column(db.String(10), nullable=False)  # HIGH, MEDIUM, LOW
    analysis = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def __repr__(self):
        return f"<StockTip {self.ticker} {self.tip_type} {self.confidence}>"
