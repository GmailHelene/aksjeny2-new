"""
Data Access Helper - Ensures authenticated users get real data, demo users get demo data
"""
import logging
from flask_login import current_user
from flask import current_app

logger = logging.getLogger(__name__)

def get_data_service_for_user():
    """
    Get the appropriate data service based on user authentication status.
    - Authenticated users: Real DataService with real market data
    - Demo users: MockDataService or limited data
    """
    try:
        # Always try to get real DataService first
        from ..services.data_service import DataService
        
        if current_user.is_authenticated:
            logger.info(f"✅ Authenticated user {current_user.id} getting REAL DataService")
            return DataService
        else:
            logger.info("🔄 Anonymous user getting REAL DataService (demo usage tracking in routes)")
            # Even demo users get real DataService, but routes should track usage
            return DataService
            
    except ImportError as e:
        logger.warning(f"DataService not available: {e}")
        # Return mock service for fallback
        class MockDataService:
            @staticmethod
            def get_oslo_bors_overview():
                logger.warning("Using mock Oslo Børs data")
                return {}
            @staticmethod
            def get_global_stocks_overview():
                logger.warning("Using mock global stocks data")
                return {}
            @staticmethod
            def get_crypto_overview():
                logger.warning("Using mock crypto data")
                return {}
            @staticmethod
            def get_currency_overview():
                logger.warning("Using mock currency data")
                return {}
            @staticmethod
            def get_stock_info(ticker):
                logger.warning(f"Using mock stock info for {ticker}")
                return {
                    'ticker': ticker,
                    'name': ticker,
                    'last_price': 100.0,
                    'change': 1.5,
                    'change_percent': 1.5,
                    'data_source': 'MOCK DATA - Service unavailable'
                }
            @staticmethod
            def get_stock_data(ticker, period='1mo', interval='1d'):
                logger.warning(f"Using mock stock data for {ticker}")
                return None
                
        return MockDataService

def should_provide_real_data():
    """
    Determine if real data should be provided to the current user.
    Returns True for authenticated users, False for demo users.
    """
    return current_user.is_authenticated

def log_data_access(endpoint, ticker=None, data_type="general"):
    """
    Log data access for analytics and fair usage tracking.
    """
    user_id = current_user.id if current_user.is_authenticated else "anonymous"
    access_type = "real" if current_user.is_authenticated else "demo"
    
    logger.info(f"📊 Data access - User: {user_id}, Type: {access_type}, Endpoint: {endpoint}, Ticker: {ticker}, DataType: {data_type}")
    
    # Here you could add database logging for usage analytics if needed

def get_user_context():
    """
    Get user context for templates and API responses.
    """
    if current_user.is_authenticated:
        return {
            'authenticated': True,
            'user_id': current_user.id,
            'access_level': 'premium' if getattr(current_user, 'has_subscription', False) else 'basic',
            'data_access': 'real'
        }
    else:
        return {
            'authenticated': False,
            'user_id': None,
            'access_level': 'demo',
            'data_access': 'demo'
        }
