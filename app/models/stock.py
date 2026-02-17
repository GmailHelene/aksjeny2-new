from datetime import datetime
from ..extensions import db

class Stock(db.Model):
    """Basic stock model for storing stock information"""
    __tablename__ = 'stocks'
    
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200))
    sector = db.Column(db.String(100))
    market = db.Column(db.String(50))  # oslo, nasdaq, etc.
    currency = db.Column(db.String(10), default='NOK')
    
    # Price information (cached)
    current_price = db.Column(db.Float)
    change_percent = db.Column(db.Float)
    volume = db.Column(db.BigInteger)
    market_cap = db.Column(db.BigInteger)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Stock {self.ticker}: {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'ticker': self.ticker,
            'name': self.name,
            'sector': self.sector,
            'market': self.market,
            'currency': self.currency,
            'current_price': self.current_price,
            'change_percent': self.change_percent,
            'volume': self.volume,
            'market_cap': self.market_cap,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
#         return f'<StockTip {self.ticker} - {self.tip_type}>'