"""
Safe yfinance wrapper to handle missing yfinance dependency gracefully
"""
import logging

logger = logging.getLogger(__name__)

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
    logger.info("yfinance imported successfully")
except ImportError:
    yf = None
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance not available - using fallback data")

def safe_ticker(symbol):
    """Safely create a yfinance Ticker object, or return None if yfinance is not available"""
    if not YFINANCE_AVAILABLE or yf is None:
        logger.debug(f"yfinance not available for symbol: {symbol}")
        return None
    
    try:
        return yf.Ticker(symbol)
    except Exception as e:
        logger.error(f"Error creating ticker for {symbol}: {e}")
        return None

def get_fallback_price(symbol):
    """Get a fallback price when yfinance is not available"""
    # Generate a deterministic but varied price based on symbol hash
    import hashlib
    hash_value = int(hashlib.md5(symbol.encode()).hexdigest()[:8], 16)
    base_price = 100.0
    variation = (hash_value % 200) - 100  # -100 to +100
    return base_price + variation

def get_fallback_stock_info(symbol):
    """Get fallback stock info when yfinance is not available"""
    price = get_fallback_price(symbol)
    return {
        'symbol': symbol,
        'regularMarketPrice': price,
        'previousClose': price * 0.98,
        'marketCap': price * 10000000,
        'volume': 1000000,
        'shortName': symbol,
        'longName': f'{symbol} Company',
        'currency': 'USD' if '.OL' not in symbol else 'NOK',
        'exchange': 'OSL' if '.OL' in symbol else 'NASDAQ',
        'sector': 'Technology',
        'industry': 'Software',
        'beta': 1.0,
        'trailingPE': 15.0,
        'forwardPE': 12.0,
        'dividendYield': 0.02,
        'fiftyTwoWeekLow': price * 0.8,
        'fiftyTwoWeekHigh': price * 1.2,
        'averageVolume': 1500000,
        'note': 'Fallback data - yfinance not available'
    }

def get_fallback_history(symbol, period='1mo', interval='1d'):
    """Get fallback price history when yfinance is not available"""
    from datetime import datetime, timedelta
    
    # Generate fake but realistic price data
    base_price = get_fallback_price(symbol)
    days = 30 if period == '1mo' else 7
    
    # Create list of dicts with proper structure for compare.html
    history = []
    current_price = base_price
    
    for i in range(days, 0, -1):
        date = datetime.now() - timedelta(days=i)
        # Random walk with slight upward bias
        change = (hash(symbol) % 100 - 50) / 1000 + 0.001  # Deterministic variation
        current_price *= (1 + change)
        
        history.append({
            'date': date.strftime('%Y-%m-%d'),
            'open': round(current_price * 0.99, 2),
            'high': round(current_price * 1.02, 2),
            'low': round(current_price * 0.98, 2),
            'close': round(current_price, 2),
            'volume': 1000000 + (hash(symbol) % 500000)
        })
    
    return history
