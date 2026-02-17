def get_stock_data(ticker):
    # Hent aksjedata fra API
    if ticker:
        try:
            import requests
            response = requests.get(f'http://localhost:5002/stocks/quick-prices?tickers={ticker}', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'data' in data:
                    stock = data['data'].get(ticker)
                    if stock:
                        stock['ticker'] = ticker
                        return stock
        except Exception as api_error:
            pass
    return None

def generate_demo_data(ticker):
    # Dummy implementation: Replace with real demo data logic
    return {'ticker': ticker, 'price': 50.0, 'name': 'Demo Data'}
