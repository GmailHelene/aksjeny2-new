"""
Dashboard service for handling dashboard data and functionality
"""
from ..models.user import User
from ..models.portfolio import Portfolio, PortfolioStock, Transaction
from ..models.watchlist import Watchlist, WatchlistItem
from ..models.activity import UserActivity
from datetime import datetime, timedelta
from sqlalchemy import desc
from .market_data_service import MarketDataService
from .ai_recommendation_service import AIRecommendationService
import logging

logger = logging.getLogger(__name__)

class DashboardService:
    def __init__(self):
        """Initialize the dashboard service with required dependencies"""
        self.market_data = MarketDataService()
        self.ai_recommendations = AIRecommendationService()

    def get_user_investments(self, user_id):
        """Get user's current investments summary"""
        try:
            # Get user's portfolios
            portfolios = Portfolio.query.filter_by(user_id=user_id).all()
            
            total_invested = 0
            total_value = 0
            total_gain = 0
            total_gain_percent = 0
            portfolio_count = len(portfolios)
            
            for portfolio in portfolios:
                # Sum up portfolio values
                if hasattr(portfolio, 'total_value') and portfolio.total_value:
                    total_value += portfolio.total_value
                if hasattr(portfolio, 'total_invested') and portfolio.total_invested:
                    total_invested += portfolio.total_invested
            
            # Calculate gains
            if total_invested > 0:
                total_gain = total_value - total_invested
                total_gain_percent = (total_gain / total_invested) * 100
            
            return {
                'total_invested': total_invested,
                'total_value': total_value,
                'total_gain': total_gain,
                'total_gain_percent': total_gain_percent,
                'portfolio_count': portfolio_count
            }
        except Exception as e:
            logger.error(f"Error getting user investments: {e}")
            return {
                'total_invested': 0,
                'total_value': 0,
                'total_gain': 0,
                'total_gain_percent': 0,
                'portfolio_count': 0
            }
    
    def get_user_activities(self, user_id, limit=5):
        """Get user's recent activities"""
        try:
            activities = UserActivity.query.filter_by(user_id=user_id)\
                .order_by(desc(UserActivity.created_at))\
                .limit(limit)\
                .all()
            
            return [{
                'activity_type': activity.activity_type,
                'description': activity.description,
                'timestamp': activity.created_at,
                'details': activity.details
            } for activity in activities]
        except Exception as e:
            logger.error(f"Error getting user activities: {e}")
            return []
    
    def get_portfolio_performance(self, user_id):
        """Get portfolio performance metrics"""
        try:
            # Get all user's portfolios
            portfolios = Portfolio.query.filter_by(user_id=user_id).all()
            
            # Initialize metrics
            best_performing = None
            worst_performing = None
            recent_transactions = []
            
            for portfolio in portfolios:
                # Calculate portfolio performance
                performance = 0
                if hasattr(portfolio, 'total_invested') and hasattr(portfolio, 'total_value'):
                    if portfolio.total_invested > 0:
                        performance = ((portfolio.total_value - portfolio.total_invested) / portfolio.total_invested) * 100
                
                # Update best/worst performing
                if best_performing is None or performance > best_performing['performance']:
                    best_performing = {
                        'name': portfolio.name,
                        'performance': performance,
                        'value': portfolio.total_value if hasattr(portfolio, 'total_value') else 0
                    }
                if worst_performing is None or performance < worst_performing['performance']:
                    worst_performing = {
                        'name': portfolio.name,
                        'performance': performance,
                        'value': portfolio.total_value if hasattr(portfolio, 'total_value') else 0
                    }
                
                # Get recent transactions
                if hasattr(portfolio, 'transactions'):
                    for transaction in portfolio.transactions:
                        recent_transactions.append({
                            'type': transaction.transaction_type,
                            'symbol': transaction.symbol,
                            'shares': transaction.shares,
                            'price': transaction.price,
                            'date': transaction.date
                        })
            
            # Sort transactions by date
            recent_transactions.sort(key=lambda x: x['date'], reverse=True)
            recent_transactions = recent_transactions[:5]  # Keep only 5 most recent
            
            return {
                'best_performing': best_performing,
                'worst_performing': worst_performing,
                'recent_transactions': recent_transactions
            }
        except Exception as e:
            logger.error(f"Error getting portfolio performance: {e}")
            return {
                'best_performing': None,
                'worst_performing': None,
                'recent_transactions': []
            }

    def get_market_data(self):
        """Get live market data summary"""
        try:
            return self.market_data.get_market_summary()
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return {
                'osebx': {'value': 0, 'change': 0, 'change_percent': 0},
                'usd_nok': {'rate': 0, 'change': 0, 'change_percent': 0},
                'btc': {'price': 0, 'change': 0, 'change_percent': 0},
                'market_open': False,
                'last_update': datetime.now().isoformat()
            }

    def get_ai_recommendations(self, user_id, limit=2):
        """Get AI-driven stock recommendations for user"""
        try:
            return self.ai_recommendations.get_recommendations(user_id, limit)
        except Exception as e:
            logger.error(f"Error getting AI recommendations: {e}")
            return []
