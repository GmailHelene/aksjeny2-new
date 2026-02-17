def get_exchange_url(ticker):
    """Get the exchange URL for buying a crypto currency"""
    
    # Handle common cryptocurrencies
    if ticker.endswith('-USD'):
        base = ticker.replace('-USD', '').upper()
        
        # Binance URLs
        if base in ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'XRP', 'DOT', 'LINK', 'AVAX']:
            return f"https://www.binance.com/en/trade/{base}_USDT"
            
        # Coinbase URLs
        elif base in ['BTC', 'ETH', 'XRP', 'ADA', 'SOL', 'AVAX', 'LINK']:
            return f"https://www.coinbase.com/price/{base.lower()}"
    
    return None # No exchange URL available for this ticker
