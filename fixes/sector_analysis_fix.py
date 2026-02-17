from flask import Blueprint, render_template, jsonify
import yfinance as yf

sector_bp = Blueprint('sector_analysis', __name__)

@sector_bp.route('/market-intel/sector-analysis')
def sector_analysis():
    try:
        # Hent sektordata fra yfinance
        sectors = {
            'Technology': ['AAPL', 'MSFT', 'GOOGL'],
            'Finance': ['JPM', 'BAC', 'WFC'],
            'Energy': ['XOM', 'CVX', 'COP']
        }
        
        sector_data = {}
        for sector, tickers in sectors.items():
            sector_performance = []
            for ticker in tickers:
                stock = yf.Ticker(ticker)
                info = stock.info
                sector_performance.append({
                    'ticker': ticker,
                    'price': info.get('regularMarketPrice', 0),
                    'change': info.get('regularMarketChangePercent', 0)
                })
            sector_data[sector] = sector_performance
            
        return render_template('sector_analysis.html', sectors=sector_data)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@sector_bp.route('/external-data/market-intelligence')
def market_intelligence():
    try:
        # Hent markedsdata
        indices = ['^GSPC', '^DJI', '^IXIC']
        market_data = []
        
        for index in indices:
            ticker = yf.Ticker(index)
            info = ticker.info
            market_data.append({
                'symbol': index,
                'price': info.get('regularMarketPrice', 0),
                'change': info.get('regularMarketChangePercent', 0)
            })
            
        return render_template('market_intelligence.html', data=market_data)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@sector_bp.route('/external-data/analyst-coverage')
def analyst_coverage():
    try:
        # Hent analytikerdata
        popular_stocks = ['AAPL', 'TSLA', 'AMZN']
        analyst_data = []
        
        for stock in popular_stocks:
            ticker = yf.Ticker(stock)
            recommendations = ticker.recommendations
            if recommendations is not None and not recommendations.empty:
                latest = recommendations.iloc[-1]
                analyst_data.append({
                    'ticker': stock,
                    'firm': latest.get('Firm', 'N/A'),
                    'rating': latest.get('To Grade', 'N/A'),
                    'action': latest.get('Action', 'N/A')
                })
                
        return render_template('analyst_coverage.html', data=analyst_data)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500
