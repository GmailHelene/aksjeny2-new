"""
Stock service for fetching stock data
"""

class StockService:
    """Service for fetching stock data"""
    
    def __init__(self):
        pass
    
    def get_stock_data(self, ticker, include_historical=True):
        """Get stock data for a ticker"""
        # Placeholder implementation
        return {
            'regularMarketPrice': 100.0,
            'regularMarketChangePercent': 1.5,
            'regularMarketChange': 1.5,
            'regularMarketVolume': 1000000,
            'marketState': 'OPEN'
        }
