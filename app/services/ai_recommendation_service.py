"""
AI recommendation service for generating stock recommendations
"""
from datetime import datetime
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
import numpy as np
from ..models.user import User
from ..models.portfolio import Portfolio, PortfolioStock
from ..models.watchlist import Watchlist, WatchlistItem
from ..services.market_data_service import MarketDataService

logger = logging.getLogger(__name__)

@dataclass
class StockRecommendation:
    symbol: str
    action: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float
    expected_return: float
    time_horizon: str
    rationale: str
    risk_level: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self):
        return {
            'symbol': self.symbol,
            'action': self.action,
            'confidence': self.confidence,
            'expected_return': self.expected_return,
            'time_horizon': self.time_horizon,
            'rationale': self.rationale,
            'risk_level': self.risk_level,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class AIRecommendationService:
    def __init__(self):
        """Initialize the AI recommendation service"""
        self.market_data = MarketDataService()
        self._last_update = {}
        self._recommendations_cache = {}
    
    def get_user_risk_profile(self, user_id: int) -> str:
        """Calculate user's risk profile based on portfolio history"""
        try:
            # Get user's portfolios and trading history
            portfolios = Portfolio.query.filter_by(user_id=user_id).all()
            
            if not portfolios:
                return 'moderate'  # Default risk profile
                
            # Analyze portfolio diversity
            all_stocks = []
            for portfolio in portfolios:
                stocks = PortfolioStock.query.filter_by(portfolio_id=portfolio.id).all()
                all_stocks.extend(stocks)
            
            if not all_stocks:
                return 'moderate'
                
            # Calculate metrics
            unique_stocks = len(set(stock.ticker for stock in all_stocks))
            avg_position_size = sum(stock.shares * stock.purchase_price for stock in all_stocks) / len(all_stocks)
            
            # Simple risk profile logic
            if unique_stocks > 20 and avg_position_size < 10000:
                return 'conservative'
            elif unique_stocks < 5 or avg_position_size > 50000:
                return 'aggressive'
            else:
                return 'moderate'
                
        except Exception as e:
            logger.error(f"Error calculating risk profile: {e}")
            return 'moderate'  # Default fallback
    
    def get_recommendations(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Get personalized stock recommendations for user"""
        try:
            # Get user's risk profile
            risk_profile = self.get_user_risk_profile(user_id)
            
            # Example recommendations (replace with real AI model later)
            recommendations = []
            
            if risk_profile == 'conservative':
                recommendations.extend([
                    StockRecommendation(
                        symbol='DNB.OL',
                        action='HOLD',
                        confidence=78,
                        expected_return=3.0,
                        time_horizon='6 mnd',
                        rationale='Stabil bank med god inntjening',
                        risk_level='Lav'
                    ),
                    StockRecommendation(
                        symbol='TEL.OL', 
                        action='BUY',
                        confidence=82,
                        expected_return=5.0,
                        time_horizon='12 mnd',
                        rationale='Solid telecom med stabil vekst',
                        risk_level='Lav'
                    )
                ])
            elif risk_profile == 'aggressive':
                recommendations.extend([
                    StockRecommendation(
                        symbol='FLNG.OL',
                        action='BUY',
                        confidence=94,
                        expected_return=12.0,
                        time_horizon='3 mnd',
                        rationale='Sterk vekst i energisektoren',
                        risk_level='Høy'
                    ),
                    StockRecommendation(
                        symbol='KING.OL',
                        action='BUY',
                        confidence=88,
                        expected_return=15.0,
                        time_horizon='6 mnd',
                        rationale='Teknologileder med stort potensial',
                        risk_level='Høy'
                    )
                ])
            else:  # moderate
                recommendations.extend([
                    StockRecommendation(
                        symbol='EQNR.OL',
                        action='BUY',
                        confidence=94,
                        expected_return=12.0,
                        time_horizon='6 mnd',
                        rationale='Basert på din risikoprofil',
                        risk_level='Moderat'
                    ),
                    StockRecommendation(
                        symbol='YAR.OL',
                        action='HOLD',
                        confidence=86,
                        expected_return=8.0,
                        time_horizon='12 mnd',
                        rationale='God verdsettelse',
                        risk_level='Moderat'
                    )
                ])
            
            # Sort by confidence and limit
            recommendations.sort(key=lambda x: x.confidence, reverse=True)
            recommendations = recommendations[:limit]
            
            # Convert to dict format
            return [rec.to_dict() for rec in recommendations]
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []  # Empty list as fallback
