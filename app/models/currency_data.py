"""Currency data model and utilities"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class CurrencyData:
    """Currency data structure"""
    pair: str  # Currency pair (e.g., 'USDNOK')
    from_currency: str  # Base currency (e.g., 'USD')
    to_currency: str  # Quote currency (e.g., 'NOK')
    rate: float  # Exchange rate
    change_percent_24h: float  # 24-hour percent change
    volume: float  # Trading volume
    trend: str  # Current trend ('up', 'down', 'stable')
    high_24h: float  # 24-hour high
    low_24h: float  # 24-hour low
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self):
        """Convert to dictionary format"""
        return {
            'pair': self.pair,
            'from_currency': self.from_currency,
            'to_currency': self.to_currency,
            'rate': self.rate,
            'change_percent_24h': self.change_percent_24h,
            'volume': self.volume,
            'trend': self.trend,
            'high_24h': self.high_24h,
            'low_24h': self.low_24h,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CurrencyData':
        """Create instance from dictionary"""
        timestamp = None
        if 'timestamp' in data:
            try:
                timestamp = datetime.fromisoformat(data['timestamp'])
            except (ValueError, TypeError):
                pass
        
        return cls(
            pair=data['pair'],
            from_currency=data['from_currency'],
            to_currency=data['to_currency'],
            rate=float(data['rate']),
            change_percent_24h=float(data['change_percent_24h']),
            volume=float(data['volume']),
            trend=data['trend'],
            high_24h=float(data['high_24h']),
            low_24h=float(data['low_24h']),
            timestamp=timestamp
        )
