from flask import Blueprint, render_template
import yfinance as yf

currency_bp = Blueprint('currency', __name__)

@currency_bp.route('/stocks/list/currency')
def currency_list():
    """Fix: Remove volume column showing 0"""
    currencies = ['USDNOK=X', 'EURNOK=X', 'GBPNOK=X', 'SEKNOK=X']
    currency_data = []
    
    for curr in currencies:
        ticker = yf.Ticker(curr)
        info = ticker.info
        hist = ticker.history(period="1d")
        
        currency_data.append({
            'symbol': curr.replace('=X', ''),
            'name': info.get('longName', curr),
            'price': info.get('regularMarketPrice', hist['Close'].iloc[-1] if not hist.empty else 0),
            'change': info.get('regularMarketChangePercent', 0),
            # Remove volume field - not relevant for currencies
            'day_high': info.get('dayHigh', 0),
            'day_low': info.get('dayLow', 0)
        })
    
    return render_template('stocks/currency_list.html', currencies=currency_data)
