import math
import logging
import random
from flask import Blueprint, jsonify, request, current_app, render_template
from flask_login import login_required, current_user
from ..extensions import csrf
from ..services.data_service import DataService
from ..services.ai_service import AIService
from ..services.yahoo_finance_service import YahooFinanceService
from ..services.portfolio_service import get_ai_analysis
from ..utils.access_control import access_required, api_access_required, api_login_required
from ..models.user import User
from ..models.portfolio import Portfolio, PortfolioStock
from datetime import datetime, timedelta
import traceback

api = Blueprint('api', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

@api.route('/docs')
def api_docs():
    """API Documentation page"""
    return render_template('api/docs.html')

def demo_portfolio_api():
    """Demo portfolio API endpoint"""
    demo_portfolio = {
        'total_value': 1250000,
        'daily_change': 15750,
        'daily_change_percent': 1.28,
        'holdings': [
            {'symbol': 'EQNR.OL', 'shares': 1000, 'value': 342550, 'weight': 27.4},
            {'symbol': 'DNB.OL', 'shares': 800, 'value': 187280, 'weight': 15.0},
            {'symbol': 'AAPL', 'shares': 500, 'value': 92850, 'weight': 7.4}
        ]
    }
    return jsonify({
        'success': True,
        'data': demo_portfolio,
        'demo': True,
        'timestamp': datetime.utcnow().isoformat()
    })

@api.route('/status')
def api_status():
    """API Status endpoint"""
    try:
        return jsonify({
            'success': True,
            'status': 'healthy',
            'version': '1.0.0',
            'endpoints': {
                'health': '/api/health',

                'demo_stocks': '/api/demo/stocks',
                'demo_market_data': '/api/demo/market-data',
                'demo_portfolio': '/api/demo/portfolio'
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"API status error: {e}")
        return jsonify({
            'success': False,
            'status': 'error',
            'error': str(e)
        }), 500

@api.route('/demo/market-summary')
def demo_market_summary_api():
    """Demo market summary API endpoint"""
    try:
        market_summary = {
            'osebx': {
                'name': 'Oslo Børs All-share Index',
                'value': 1234.56,
                'change': 12.34,
                'change_percent': 1.01,
                'volume': 1500000
            },
            'sp500': {
                'name': 'S&P 500',
                'value': 4567.89,
                'change': 23.45,
                'change_percent': 0.52,
                'volume': 3200000000
            },
            'nasdaq': {
                'name': 'NASDAQ Composite',
                'value': 14123.45,
                'change': 67.89,
                'change_percent': 0.48,
                'volume': 2800000000
            },
            'sectors': {
                'technology': {'change_percent': 1.2},
                'healthcare': {'change_percent': 0.8},
                'finance': {'change_percent': -0.3},
                'energy': {'change_percent': 2.1}
            },
            'market_sentiment': 'Positive',
            'last_updated': datetime.utcnow().isoformat()
        }
        return jsonify({
            'success': True,
            'data': market_summary,
            'demo': True,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Demo market summary error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/crypto/trending')
def get_crypto_trending():
    """API endpoint for trending crypto - now using real yfinance data"""
    try:
        # Use real yfinance data for major cryptos
        import yfinance as yf
        
        crypto_symbols = ['BTC-USD', 'ETH-USD', 'BNB-USD', 'ADA-USD', 'XRP-USD']
        trending_crypto = []
        
        for symbol in crypto_symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                
                if len(hist) >= 1:
                    current_price = float(hist['Close'].iloc[-1])
                    volume = int(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else 0
                    
                    # Calculate change if we have at least 2 days of data
                    if len(hist) >= 2:
                        previous_price = float(hist['Close'].iloc[-2])
                        change = current_price - previous_price
                        change_percent = (change / previous_price) * 100 if previous_price != 0 else 0
                    else:
                        change = 0
                        change_percent = 0
                    
                    # Try to get additional info, but don't fail if it's not available
                    try:
                        info = ticker.info
                        name = info.get('longName', symbol.replace('-USD', ''))
                        market_cap = info.get('marketCap', 0)
                    except:
                        name = symbol.replace('-USD', '')
                        market_cap = 0
                    
                    crypto_data = {
                        'symbol': symbol,
                        'name': name,
                        'price': round(current_price, 2),
                        'change': round(change, 2),
                        'change_percent': round(change_percent, 2),
                        'volume': volume,
                        'market_cap': market_cap
                    }
                    trending_crypto.append(crypto_data)
                    
            except Exception as e:
                logger.warning(f"Failed to get data for {symbol}: {e}")
                continue
        
        # If no real data was obtained, return minimal fallback
        if not trending_crypto:
            trending_crypto = [
                {
                    'symbol': 'BTC-USD',
                    'name': 'Bitcoin',
                    'price': 45000.0,
                    'change': 500.0,
                    'change_percent': 1.12,
                    'volume': 0,
                    'market_cap': 0,
                    'note': 'Fallback data - real data unavailable'
                }
            ]
        
        return jsonify({
            'success': True,
            'data': trending_crypto,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error fetching trending crypto: {e}")
        response = jsonify({'success': False, 'error': str(e)})
        response.status_code = 500
        return response

@api.route('/crypto/data')
def get_crypto_data():
    """API endpoint for detailed crypto data"""
    try:
        data = DataService.get_crypto_overview()
        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error fetching crypto data: {e}")
        response = jsonify({'success': False, 'error': 'Failed to fetch crypto data'})
        response.status_code = 500
        return response

@api.route('/currency/rates')
def get_currency_rates():
    """API endpoint for currency exchange rates"""
    try:
        data = DataService.get_currency_overview()
        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error fetching currency rates: {e}")
        response = jsonify({'success': False, 'error': str(e)})
        response.status_code = 500
        return response

@api.route('/dashboard/data')
def get_dashboard_data():
    """API endpoint for dashboard data"""
    try:
        # Aggregate data for dashboard
        dashboard_data = {
            'market_summary': {
                'osebx': {'value': 1234.56, 'change': 12.34, 'change_percent': 1.01},
                'sp500': {'value': 4567.89, 'change': -23.45, 'change_percent': -0.51},
                'nasdaq': {'value': 15678.90, 'change': 45.67, 'change_percent': 0.29}
            },
            'crypto_summary': {
                'bitcoin': {'value': 65432.10, 'change': 1234.56, 'change_percent': 1.93},
                'ethereum': {'value': 3456.78, 'change': 67.89, 'change_percent': 2.01}
            },
            'currency_summary': {
                'usdnok': {'value': 10.45, 'change': -0.15, 'change_percent': -1.42},
                'eurnok': {'value': 11.32, 'change': 0.08, 'change_percent': 0.71}
            }
        }
        return jsonify({
            'success': True,
            'data': dashboard_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/financial/news')
def get_financial_news():
    """API endpoint for financial news"""
    try:
        financial_news = [
            {
                'id': 1,
                'title': 'Sentralbanken holder renten uendret',
                'summary': 'Norges Bank besluttet å holde styringsrenten på 4,5 prosent.',
                'content': 'I dagens rentemøte besluttet Norges Bank å holde styringsrenten uendret på 4,5 prosent...',
                'date': '2025-01-17',
                'category': 'monetary_policy',
                'source': 'Aksjeradar',
                'relevance_score': 95
            },
            {
                'id': 2,
                'title': 'Equinor med sterke kvartalstall',
                'summary': 'Equinor leverte bedre resultater enn ventet i fjerde kvartal.',
                'content': 'Equinor rapporterte et justert resultat på 6,2 milliarder dollar...',
                'date': '2025-01-16',
                'category': 'earnings',
                'source': 'Aksjeradar',
                'relevance_score': 88
            },
            {
                'id': 3,
                'title': 'Oslo Børs stiger på bred front',
                'summary': 'Hovedindeksen på Oslo Børs steg 1,2 prosent i dagens handel.',
                'content': 'OSEBX stengte opp 1,2 prosent til 1.234 poeng...',
                'date': '2025-01-15',
                'category': 'market_update',
                'source': 'Aksjeradar',
                'relevance_score': 82
            }
        ]
        
        return jsonify({
            'success': True,
            'data': financial_news,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error fetching financial news: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/economic/indicators')
def get_economic_indicators():
    """API endpoint for economic indicators"""
    try:
        indicators = {
            'norway': {
                'unemployment_rate': 3.2,
                'inflation_rate': 2.8,
                'gdp_growth': 1.4,
                'interest_rate': 4.5,
                'oil_fund_value': 15800000000000,
                'last_updated': '2025-01-15'
            },
            'global': {
                'us_unemployment': 3.7,
                'us_inflation': 2.1,
                'eu_inflation': 2.9,
                'china_gdp_growth': 5.2,
                'last_updated': '2025-01-15'
            },
            'market_indicators': {
                'vix': 18.5,
                'dollar_index': 103.2,
                'oil_price': 78.5,
                'gold_price': 2034.50,
                'last_updated': '2025-01-17'
            }
        }
        
        return jsonify({
            'success': True,
            'data': indicators,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error fetching economic indicators: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/market/sectors')
def get_market_sectors():
    """API endpoint for sector analysis"""
    try:
        sectors = {
            'energy': {
                'name': 'Energi',
                'performance_today': 2.1,
                'performance_week': 4.8,
                'performance_month': -1.2,
                'trend': 'bullish',
                'top_stocks': [
                    {'symbol': 'EQNR.OL', 'name': 'Equinor', 'change': 2.5},
                    {'symbol': 'AKA.OL', 'name': 'Aker ASA', 'change': 1.8}
                ]
            },
            'finance': {
                'name': 'Finans',
                'performance_today': 0.3,
                'performance_week': 1.2,
                'performance_month': 3.4,
                'trend': 'neutral',
                'top_stocks': [
                    {'symbol': 'DNB.OL', 'name': 'DNB Bank', 'change': 0.5},
                    {'symbol': 'NOR.OL', 'name': 'Nordea', 'change': 0.2}
                ]
            },
            'technology': {
                'name': 'Teknologi',
                'performance_today': -0.8,
                'performance_week': -2.1,
                'performance_month': 5.6,
                'trend': 'bearish',
                'top_stocks': [
                    {'symbol': 'AAPL', 'name': 'Apple', 'change': -1.2},
                    {'symbol': 'GOOGL', 'name': 'Alphabet', 'change': -0.5}
                ]
            },
            'healthcare': {
                'name': 'Helsevesen',
                'performance_today': 1.5,
                'performance_week': 2.8,
                'performance_month': 4.2,
                'trend': 'bullish',
                'top_stocks': [
                    {'symbol': 'JNJ', 'name': 'Johnson & Johnson', 'change': 1.8},
                    {'symbol': 'PFE', 'name': 'Pfizer', 'change': 1.2}
                ]
            }
        }
        
        return jsonify({
            'success': True,
            'data': sectors,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error fetching sector analysis: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/insider/analysis/<symbol>')
def get_insider_analysis(symbol):
    """Deprecated demo endpoint. Returns 410 Gone to avoid fake data."""
    return jsonify({'success': False, 'error': 'Endpoint deprecated. Use /insider-trading/api/latest'}), 410

@api.route('/crypto')
def get_crypto():
    """API endpoint for crypto overview"""
    try:
        data = DataService.get_crypto_overview()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching crypto overview: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/currency')
def get_currency():
    """API endpoint for currency overview"""
    try:
        # Return properly formatted currency data
        currency_data = {
            "EURNOK=X": {
                "change": 0.08,
                "change_percent": 0.71,
                "last_price": 11.32,
                "name": "EUR/NOK",
                "signal": "BUY",
                "ticker": "EURNOK=X",
                "volume": 1800000000
            },
            "USDNOK=X": {
                "change": -0.15,
                "change_percent": -1.42,
                "last_price": 10.45,
                "name": "USD/NOK",
                "signal": "HOLD",
                "ticker": "USDNOK=X",
                "volume": 2500000000
            },
            "GBPNOK=X": {
                "change": 0.05,
                "change_percent": 0.35,
                "last_price": 13.82,
                "name": "GBP/NOK",
                "signal": "BUY",
                "ticker": "GBPNOK=X",
                "volume": 850000000
            },
            "SEKUSD=X": {
                "change": -0.002,
                "change_percent": -0.18,
                "last_price": 0.095,
                "name": "SEK/USD",
                "signal": "HOLD",
                "ticker": "SEKUSD=X", 
                "volume": 650000000
            },
            "DKKUSD=X": {
                "change": 0.001,
                "change_percent": 0.08,
                "last_price": 0.145,
                "name": "DKK/USD",
                "signal": "HOLD",
                "ticker": "DKKUSD=X",
                "volume": 420000000
            }
        }
        
        return jsonify(currency_data)
    except Exception as e:
        logger.error(f"Error fetching currency overview: {e}")
        return jsonify({
            'error': 'Failed to fetch currency overview',
            'message': str(e)
        }), 500

@api.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@api.route('/search')
@api_access_required
def search():
    """Search for stocks"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'results': []})
        
        results = YahooFinanceService.search_stocks(query)
        return jsonify({'results': results})
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/stocks/search')
def search_stocks():
    """API endpoint for stock search"""
    query = request.args.get('q', '')
    if not query:
        response = jsonify({'error': 'No search query provided'})
        response.status_code = 400
        return response
    
    try:
        # Search for stocks using Yahoo Finance service
        results = YahooFinanceService.search_stocks(query)
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        logger.error(f"Error searching stocks: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/stocks/quick-prices')
def get_quick_prices():
    """Optimized endpoint for quick price updates on homepage"""
    import time
    try:
        current_app.logger.info("Quick prices endpoint called")
        tickers = request.args.get('tickers', '').split(',')
        current_app.logger.info(f"Raw tickers: {tickers}")
        tickers = [t.strip() for t in tickers if t.strip()]
        current_app.logger.info(f"Cleaned tickers: {tickers}")
        
        if not tickers:
            current_app.logger.warning("No tickers provided")
            return jsonify({'error': 'No tickers provided'}), 400
            
        if len(tickers) > 10:
            current_app.logger.warning(f"Too many tickers: {len(tickers)}")
            return jsonify({'error': 'Too many tickers requested'}), 400
            
        # Mock data for now - replace with actual data service
        results = {}
        for ticker in tickers:
            results[ticker] = {
                'price': 100.0 + hash(ticker) % 500,
                'change_percent': (hash(ticker) % 200 - 100) / 10,
                'change': (hash(ticker) % 50 - 25) / 10,
                'volume': hash(ticker) % 10000000,
                'market_state': 'OPEN'
            }
        
        current_app.logger.info(f"Results generated: {len(results)} tickers")        
        return jsonify({
            'success': True,
            'data': results,
            'cached': False,
            'timestamp': time.time()
        })
        
    except Exception as e:
        current_app.logger.error(f"Quick prices API error: {str(e)}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e), 'success': False}), 500

@api.route('/stock/<symbol>')
@api_access_required
def get_stock_data(symbol):
    """Get stock data for a specific symbol"""
    try:
        stock_data = DataService.get_stock_info(symbol)
        if not stock_data:
            response = jsonify({'error': 'Stock not found'})
            response.status_code = 404
            return response
        
        return jsonify(stock_data)
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/stock/<symbol>/price')
@access_required
def get_stock_price(symbol):
    """Get current price for a stock"""
    try:
        price_data = DataService.get_stock_price(symbol)
        if not price_data:
            response = jsonify({'error': 'Price data not available'})
        response.status_code = 404
        return response
        
        return jsonify(price_data)
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/stock/<symbol>/analysis')
@api_access_required
def get_stock_analysis(symbol):
    """Get AI analysis for a stock"""
    try:
        analysis = get_ai_analysis(symbol)
        return jsonify(analysis)
    except Exception as e:
        logger.error(f"Error getting analysis for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/market/overview')
@api_access_required
def market_overview():
    """Get market overview data"""
    try:
        overview = {
            'oslo_stocks': DataService.get_oslo_bors_overview(),
            'global_stocks': DataService.get_global_stocks_overview(),
            'crypto': DataService.get_crypto_overview(),
            'currency': DataService.get_currency_overview(),
            'timestamp': datetime.utcnow().isoformat()
        }
        return jsonify(overview)
    except Exception as e:
        logger.error(f"Error fetching market overview: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/market-data')
def market_data():
    """API endpoint for market data"""
    try:
        # Get market overview data
        data = {
            'oslo': DataService.get_oslo_stocks()[:5],
            'global': DataService.get_global_stocks()[:5],
            'crypto': DataService.get_crypto_data()[:3],
            'indices': DataService.get_global_indices()
        }
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error fetching market data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/homepage/market-data')
def homepage_market_data():
    """API endpoint for homepage market data"""
    try:
        # Get homepage market overview data
        data = {
            'oslo': DataService.get_oslo_stocks()[:5],
            'global': DataService.get_global_stocks()[:5],
            'crypto': DataService.get_crypto_data()[:3],
            'currency': DataService.get_currency_overview(),
            'last_updated': datetime.utcnow().isoformat()
        }
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error fetching homepage market data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/market-data/realtime')
@api_access_required
def market_data_realtime():
    """API endpoint for realtime market data"""
    try:
        # Get realtime market data  
        data = {
            'oslo_realtime': DataService.get_oslo_stocks()[:3],
            'global_realtime': DataService.get_global_stocks()[:3],
            'crypto_realtime': DataService.get_crypto_data()[:2],
            'indices_realtime': DataService.get_global_indices(),
            'last_updated': datetime.utcnow().isoformat()
        }
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error fetching realtime market data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/user/watchlist')
@login_required
def get_user_watchlist():
    """Get user's watchlist"""
    try:
        # Implementation would fetch from database
        watchlist = []  # Placeholder
        return jsonify({'watchlist': watchlist})
    except Exception as e:
        logger.error(f"Error fetching watchlist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/watchlist/add', methods=['POST'])
@csrf.exempt
def add_to_watchlist():
    """Add symbol to watchlist with proper UI refresh"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper().strip() if data else None
        
        if not symbol:
            return jsonify({'success': False, 'error': 'Symbol er påkrevd'}), 400
        
        # For demo/unauthenticated users, just return success
        if not current_user.is_authenticated:
            return jsonify({
                'success': True,
                'message': f'{symbol} lagt til i watchlist (demo mode)',
                'action': 'reload'  # Signal UI to reload
            })
        
        from app.models.watchlist import Watchlist, WatchlistItem
        from app import db
        
        # Get or create user's watchlist
        watchlist = Watchlist.query.filter_by(user_id=current_user.id).first()
        if not watchlist:
            watchlist = Watchlist(user_id=current_user.id, name='Min watchlist')
            db.session.add(watchlist)
            db.session.flush()
        
        # Check if symbol already exists
        existing_item = WatchlistItem.query.filter_by(
            watchlist_id=watchlist.id, 
            symbol=symbol
        ).first()
        
        if existing_item:
            return jsonify({
                'success': False, 
                'error': f'{symbol} er allerede i watchlist'
            })
        
        # Add new item
        new_item = WatchlistItem(
            watchlist_id=watchlist.id,
            symbol=symbol,
            added_at=datetime.now()
        )
        db.session.add(new_item)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'{symbol} lagt til i watchlist',
            'action': 'reload',  # Signal UI to reload
            'item_count': WatchlistItem.query.filter_by(watchlist_id=watchlist.id).count()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding to watchlist: {e}")
        return jsonify({
            'success': False, 
            'error': 'Kunne ikke legge til i watchlist'
        }), 500

@api.route('/watchlist/remove', methods=['POST', 'DELETE'])
@login_required
def remove_from_watchlist():
    """Remove symbol from watchlist - Global API endpoint for template compatibility"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper().strip() if data else None
        
        if not symbol:
            response = jsonify({'success': False, 'error': 'Symbol er påkrevd'})
            response.status_code = 400
            return response
        
        from app.models.watchlist import Watchlist, WatchlistItem
        from app import db
        
        # Find user's watchlist
        watchlist = Watchlist.query.filter_by(user_id=current_user.id).first()
        if not watchlist:
            return jsonify({'success': False, 'error': 'Ingen watchlist funnet'})
        
        # Find and remove the item
        item = WatchlistItem.query.filter_by(
            watchlist_id=watchlist.id, 
            symbol=symbol
        ).first()
        
        if not item:
            return jsonify({'success': False, 'error': f'{symbol} ikke funnet i watchlist'})
        
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'{symbol} fjernet fra watchlist'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing from watchlist: {e}")
        response = jsonify({'success': False, 'error': 'Kunne ikke fjerne fra watchlist'})
        response.status_code = 500
        return response

@api.route('/user/portfolio')
@login_required
def get_user_portfolio():
    """Get user's portfolio"""
    try:
        # Implementation would fetch from database
        portfolio = []  # Placeholder
        return jsonify({'portfolio': portfolio})
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/feedback', methods=['POST'])
@login_required
def feedback():
    """Motta tilbakemelding fra bruker"""
    data = request.get_json()
    text = data.get('feedback', '').strip()
    if not text or len(text) < 5:
        response = jsonify({'success': False, 'error': 'Skriv en tilbakemelding på minst 5 tegn.'})
        response.status_code = 400
        return response
    # Lagre til fil eller database, evt. send e-post
    try:
        with open('user_feedback.log', 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().isoformat()} | {current_user.email}: {text}\n")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        response = jsonify({'success': False, 'error': 'Kunne ikke lagre tilbakemelding.'})
        response.status_code = 500
        return response

@api.route('/realtime/price/<ticker>')
def realtime_price(ticker):
    """Get real-time price for a ticker - using working DataService.get_stock_info"""
    try:
        from app.services.data_service import DataService
        
        # Use the working get_stock_info method that returns real data
        stock_info = DataService.get_stock_info(ticker)
        
        if stock_info and stock_info.get('last_price', 0) > 0:
            price_data = {
                'ticker': ticker,
                'price': round(stock_info['last_price'], 2),
                'change': round(stock_info.get('change', 0), 2),
                'change_percent': round(stock_info.get('change_percent', 0), 2),
                'volume': stock_info.get('volume', 0),
                'timestamp': datetime.utcnow().isoformat(),
                'source': stock_info.get('data_source', 'Real Data')
            }
            return jsonify(price_data)
        else:
            # Fallback if no data available
            return jsonify({
                'ticker': ticker,
                'error': 'No data available',
                'timestamp': datetime.utcnow().isoformat()
            }), 404
            
    except Exception as e:
        current_app.logger.error(f"Error getting realtime price for {ticker}: {e}")
        response = jsonify({'success': False, 'error': 'Could not fetch price data'})
        response.status_code = 500
        return response

@api.route('/realtime/batch-updates', methods=['POST'])
def realtime_batch_updates():
    """Get batch updates for multiple tickers"""
    try:
        data = request.get_json() or {}
        tickers = data.get('tickers', [])
        
        if not tickers:
            response = jsonify({'error': 'No tickers provided'})
        response.status_code = 400
        return response
        
        # Mock updates
        import random
        updates = {}
        for ticker in tickers[:20]:  # Limit to 20 tickers
            updates[ticker] = {
                'price': round(random.uniform(50, 500), 2),
                'change': round(random.uniform(-10, 10), 2),
                'change_percent': round(random.uniform(-5, 5), 2),
                'volume': random.randint(100000, 10000000)
            }
        
        return jsonify({
            'success': True,
            'updates': updates,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        current_app.logger.error(f"Error in batch updates: {e}")
        response = jsonify({'success': False, 'error': 'Could not process batch update'})
        response.status_code = 500
        return response

@api.route('/news/financial')
def get_financial_news_api():
    """Get financial news from multiple sources"""
    try:
        symbols = request.args.getlist('symbols')
        sources = request.args.getlist('sources')
        limit = request.args.get('limit', 50, type=int)
        
        # For now, return demo news data
        news_articles = [
            {
                'title': 'Marked stiger på positiv teknologi-utvikling',
                'summary': 'Teknologiaksjer opplevde sterk vekst i dag etter positive kvartalsrapporter',
                'sentiment': 'positive',
                'source': 'Finansavisen',
                'published_at': datetime.utcnow().isoformat(),
                'url': 'https://aksjeradar.trade/news/teknologi-marked-oppgang',
                'symbol': symbols[0] if symbols else 'AAPL'
            },
            {
                'title': 'Energisektoren under press',
                'summary': 'Olje- og gasspriser faller på grunn av global økonomisk usikkerhet',
                'sentiment': 'negative',
                'source': 'E24',
                'published_at': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                'url': 'https://aksjeradar.trade/news/energi-sektor-press',
                'symbol': 'EQNR.OL'
            },
            {
                'title': 'Sentralbanken holder renten uendret',
                'summary': 'Norges Bank besluttet å holde styringsrenten på dagens nivå',
                'sentiment': 'neutral',
                'source': 'DN',
                'published_at': (datetime.utcnow() - timedelta(hours=4)).isoformat(),
                'url': 'https://aksjeradar.trade/news/sentralbank-rente-beslutning',
                'symbol': 'DNB.OL'
            },
            {
                'title': 'Kryptovaluta marked volatilt',
                'summary': 'Bitcoin og andre kryptovalutaer opplever store svingninger',
                'sentiment': 'neutral',
                'source': 'CryptoNews',
                'published_at': (datetime.utcnow() - timedelta(hours=6)).isoformat(),
                'url': 'https://aksjeradar.trade/news/krypto-volatilitet',
                'symbol': 'BTC-USD'
            }
        ]
        
        # Filter by symbols if provided
        if symbols:
            filtered_news = [article for article in news_articles 
                           if any(symbol in article['symbol'] for symbol in symbols)]
            if filtered_news:
                news_articles = filtered_news
        
        # Limit results
        news_articles = news_articles[:limit]
        
        return jsonify({
            'success': True,
            'news': news_articles,
            'total': len(news_articles)
        })
        
    except Exception as e:
        logger.error(f"Error getting financial news: {e}")
        response = jsonify({
            'success': False,
            'message': 'Failed to get financial news'
        })
        response.status_code = 500
        return response



@api.route('/insider/analysis')
def get_general_insider_analysis():
    """Deprecated demo endpoint. Use /insider-trading/api/latest instead."""
    return jsonify({'success': False, 'error': 'Endpoint deprecated. Use /insider-trading/api/latest'}), 410

@api.route('/insider/analysis/<ticker>')
def insider_analysis(ticker):
    """Deprecated demo endpoint. Use /insider-trading/api/latest instead."""
    return jsonify({'success': False, 'error': 'Endpoint deprecated. Use /insider-trading/api/latest'}), 410

@api.route('/market/comprehensive', methods=['POST'])
def market_comprehensive():
    """Get comprehensive market data for multiple symbols"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        market_data = {}
        for symbol in symbols:
            # Get stock data using DataService
            stock_data = DataService.get_single_stock_data(symbol)
            if stock_data:
                market_data[symbol] = {
                    'name': stock_data.get('shortName', symbol),
                    'price': stock_data.get('last_price', 0),
                    'change': stock_data.get('change', 0),
                    'change_percent': stock_data.get('change_percent', 0),
                    'volume': stock_data.get('volume', 0),
                    'market_cap': stock_data.get('market_cap', 0)
                }
        
        return jsonify({
            'success': True,
            'market_data': market_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error fetching comprehensive market data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Public API endpoints - no authentication required
@api.route('/public/market/data')
def get_public_market_data():
    """Get public market data for dashboard"""
    try:
        # Generate realistic demo dashboard data
        dashboard_data = {
            'portfolio_summary': {
                'total_value': 1250000,  # NOK
                'daily_change': 2.3,     # %
                'daily_change_value': 28750,  # NOK
                'stocks_count': 7,
                'sectors': {
                    'Technology': 45.2,
                    'Energy': 32.1,
                    'Finance': 22.7
                }
            },
            'market_indicators': {
                'vix': 18.5,
                'fear_greed_index': 68,
                'market_sentiment': 'bullish'
            },
            'top_gainers': [
                {'symbol': 'TSLA', 'change': 5.2, 'price': 245.30},
                {'symbol': 'NVDA', 'change': 3.8, 'price': 118.50},
                {'symbol': 'EQNR.OL', 'change': 2.1, 'price': 285.60}
            ],
            'top_losers': [
                {'symbol': 'META', 'change': -2.3, 'price': 485.20},
                {'symbol': 'DNB.OL', 'change': -1.1, 'price': 225.80}
            ],
            'economic_calendar': [
                {
                    'event': 'Federal Reserve Interest Rate Decision',
                    'time': '2025-07-16T14:00:00Z',
                    'impact': 'high',
                    'currency': 'USD'
                },
                {
                    'event': 'Norwegian GDP Release',
                    'time': '2025-07-18T08:00:00Z',
                    'impact': 'medium',
                    'currency': 'NOK'
                }
            ],
            'stocks': DataService.get_market_overview(),
            'crypto': DataService.get_crypto_overview(),
            'currencies': DataService.get_currency_overview()
        }
        
        return jsonify({
            'success': True,
            'dashboard_data': dashboard_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting public market data: {e}")
        response = jsonify({
            'success': False,
            'message': 'Failed to get market data'
        })
        response.status_code = 500
        return response

@api.route('/public/economic/indicators')
def get_public_economic_indicators():
    """Get public economic indicators"""
    try:
        indicators = [
            {
                'indicator': 'Styringsrente',
                'value': '4.50',
                'unit': '%',
                'date': '2025-07-14',
                'source': 'Norges Bank',
                'change': '+0.25'
            },
            {
                'indicator': 'Inflasjon',
                'value': '3.2',
                'unit': '%',
                'date': '2025-06-30',
                'source': 'SSB',
                'change': '-0.1'
            },
            {
                'indicator': 'Arbeidsledighet',
                'value': '3.8',
                'unit': '%',
                'date': '2025-06-30',
                'source': 'NAV',
                'change': '+0.2'
            },
            {
                'indicator': 'BNP Vekst',
                'value': '2.1',
                'unit': '%',
                'date': '2025-Q2',
                'source': 'SSB',
                'change': '+0.3'
            },
            {
                'indicator': 'Oljepris (Brent)',
                'value': '82.50',
                'unit': ' USD/fat',
                'date': '2025-07-14',
                'source': 'Reuters',
                'change': '+1.20'
            }
        ]
        
        return jsonify({
            'success': True,
            'economic_indicators': indicators
        })
        
    except Exception as e:
        logger.error(f"Error getting economic indicators: {e}")
        response = jsonify({
            'success': False,
            'message': 'Failed to get economic indicators'
        })
        response.status_code = 500
        return response

@api.route('/public/market/sectors')
def get_public_sector_analysis():
    """Get public sector analysis"""
    try:
        # Sector data would be calculated from individual stocks
        sector_data = {
            'technology': {
                'symbols': ['AAPL', 'GOOGL', 'MSFT', 'TSLA'],
                'performance': '+2.3%',
                'trend': 'bullish',
                'change': 2.3,
                'volume': 125000000
            },
            'energy': {
                'symbols': ['EQNR.OL', 'AKERBP.OL'],
                'performance': '+1.8%',
                'trend': 'bullish',
                'change': 1.8,
                'volume': 85000000
            },
            'finance': {
                'symbols': ['DNB.OL'],
                'performance': '+0.9%',
                'trend': 'neutral',
                'change': 0.9,
                'volume': 45000000
            },
            'telecommunications': {
                'symbols': ['TEL.OL'],
                'performance': '-0.5%',
                'trend': 'bearish',
                'change': -0.5,
                'volume': 20000000
            },
            'healthcare': {
                'symbols': ['JNJ', 'PFE'],
                'performance': '+1.2%',
                'trend': 'bullish',
                'change': 1.2,
                'volume': 85000000
            },
            'consumer_goods': {
                'symbols': ['PG', 'KO'],
                'performance': '+0.6%',
                'trend': 'neutral',
                'change': 0.6,
                'volume': 65000000
            }
        }
        
        return jsonify({
            'success': True,
            'sector_analysis': sector_data,
            'last_updated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting sector analysis: {e}")
        response = jsonify({
            'success': False,
            'message': 'Failed to get sector analysis'
        })
        response.status_code = 500
        return response

@api.route('/public/news/financial')
def get_public_financial_news():
    """Get public financial news"""
    try:
        symbols = request.args.getlist('symbols')
        sources = request.args.getlist('sources')
        limit = request.args.get('limit', 50, type=int)
        
        # For now, return demo news data
        news_articles = [
            {
                'id': 1,
                'title': 'Equinor rapporterer sterke Q2-resultater',
                'summary': 'Equinor overgår forventningene med økte oljeinntekter og reduserte kostnader.',
                'content': 'Equinor ASA rapporterte sterke resultater for andre kvartal...',
                'source': 'E24',
                'url': 'https://e24.no/equinor-q2-results',
                'published_at': '2025-07-14T08:00:00Z',
                'sentiment': 'positive',
                'symbols': ['EQNR.OL'],
                'category': 'earnings'
            },
            {
                'id': 2,
                'title': 'Norges Bank holder styringsrenten uendret',
                'summary': 'Sentralbanken holder renten på 4.50% som forventet av analytikere.',
                'content': 'Norges Bank besluttet å holde styringsrenten uendret...',
                'source': 'DN',
                'url': 'https://dn.no/norges-bank-rente',
                'published_at': '2025-07-14T10:00:00Z',
                'sentiment': 'neutral',
                'symbols': ['DNB.OL', 'EQNR.OL'],
                'category': 'monetary_policy'
            }
        ]
        
        return jsonify({
            'success': True,
            'news': news_articles,
            'total': len(news_articles)
        })
        
    except Exception as e:
        logger.error(f"Error getting financial news: {e}")
        response = jsonify({
            'success': False,
            'message': 'Failed to get financial news'
        })
        response.status_code = 500
        return response

@api.route('/public/crypto/trending')
def get_public_crypto_trending():
    """Get public trending crypto data"""
    try:
        # Get trending crypto data
        trending_data = {
            'BTC-USD': {
                'name': 'Bitcoin',
                'symbol': 'BTC',
                'price': 65432.1,
                'change_percent': 1.87,
                'volume': 25000000000,
                'market_cap': 1200000000000,
                'trend_score': 95
            },
            'ETH-USD': {
                'name': 'Ethereum',
                'symbol': 'ETH',
                'price': 3456.78,
                'change_percent': 1.67,
                'volume': 15000000000,
                'market_cap': 400000000000,
                'trend_score': 88
            },
            'XRP-USD': {
                'name': 'Ripple',
                'symbol': 'XRP',
                'price': 0.632,
                'change_percent': 0.32,
                'volume': 2000000000,
                'market_cap': 35000000000,
                'trend_score': 72
            }
        }
        
        return jsonify({
            'success': True,
            'trending_crypto': trending_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error fetching trending crypto: {e}")
        response = jsonify({'success': False, 'error': 'Failed to fetch trending crypto'})
        response.status_code = 500
        return response

@api.route('/public/insider/analysis/<symbol>')
def get_public_insider_analysis(symbol):
    """Deprecated demo endpoint. Returns 410 Gone to enforce real data only."""
    try:
        response = jsonify({
            'success': False,
            'error': 'Endpoint deprecated. Use /insider-trading/api/latest?symbol=SYMBOL',
            'message': 'Denne endepunktet er fjernet. Bruk /insider-trading/api/latest med ?symbol=SYMBOL for ekte data.'
        })
        response.status_code = 410
        return response
    except Exception as e:
        logger.error(f"Error deprecating insider analysis for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/public/market/comprehensive', methods=['POST'])
def get_public_market_comprehensive():
    """Get public comprehensive market data"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        market_data = {}
        for symbol in symbols:
            # Get stock data using DataService
            stock_data = DataService.get_single_stock_data(symbol)
            if stock_data:
                market_data[symbol] = {
                    'name': stock_data.get('shortName', symbol),
                    'price': stock_data.get('last_price', 0),
                    'change': stock_data.get('change', 0),
                    'change_percent': stock_data.get('change_percent', 0),
                    'volume': stock_data.get('volume', 0),
                    'market_cap': stock_data.get('market_cap', 0)
                }
        
        return jsonify({
            'success': True,
            'market_data': market_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error fetching comprehensive market data: {e}")
        response = jsonify({'success': False, 'error': str(e)})
        response.status_code = 500
        return response

@api.route('/public/crypto/data')
def get_public_crypto_data():
    """Get public crypto data"""
    try:
        data = DataService.get_crypto_overview()
        if not data:
            response = jsonify({'error': 'No crypto data available'})
        response.status_code = 404
        return response
        
        # Format data for API response
        formatted_data = {}
        for ticker, crypto_info in data.items():
            # Handle both dict and object formats
            if isinstance(crypto_info, dict):
                formatted_data[ticker] = {
                    'ticker': ticker,
                    'last_price': float(crypto_info.get('last_price', 0)),
                    'change': float(crypto_info.get('change', 0)),
                    'change_percent': float(crypto_info.get('change_percent', 0)),
                    'volume': float(crypto_info.get('volume', 0)),
                    'market_cap': float(crypto_info.get('market_cap', 0)),
                    'signal': crypto_info.get('signal', 'HOLD')
                }
            else:
                formatted_data[ticker] = {
                    'ticker': ticker,
                    'last_price': float(crypto_info.last_price) if hasattr(crypto_info, 'last_price') and crypto_info.last_price else 0,
                    'change': float(crypto_info.change) if hasattr(crypto_info, 'change') and crypto_info.change else 0,
                    'change_percent': float(crypto_info.change_percent) if hasattr(crypto_info, 'change_percent') and crypto_info.change_percent else 0,
                    'volume': float(crypto_info.volume) if hasattr(crypto_info, 'volume') and crypto_info.volume else 0,
                    'market_cap': float(crypto_info.market_cap) if hasattr(crypto_info, 'market_cap') and crypto_info.market_cap else 0,
                    'signal': crypto_info.signal if hasattr(crypto_info, 'signal') else 'HOLD'
                }
        
        return jsonify({
            'success': True,
            'crypto_data': formatted_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error fetching crypto data: {e}")
        response = jsonify({'success': False, 'error': 'Failed to fetch crypto data'})
        response.status_code = 500
        return response

@api.route('/public/currency/rates')
def get_public_currency_rates():
    """Get public currency rates"""
    try:
        data = DataService.get_currency_overview()
        if not data:
            response = jsonify({'error': 'No currency data available'})
        response.status_code = 404
        return response
        
        # Format data for API response
        formatted_data = {}
        for ticker, currency_info in data.items():
            # Handle both dict and object formats
            if isinstance(currency_info, dict):
                formatted_data[ticker] = {
                    'pair': ticker,
                    'rate': float(currency_info.get('rate', currency_info.get('last_price', 0))),
                    'change': float(currency_info.get('change', 0)),
                    'change_percent': float(currency_info.get('change_percent', 0)),
                    'bid': float(currency_info.get('bid', 0)),
                    'ask': float(currency_info.get('ask', 0)),
                    'volume': float(currency_info.get('volume', 0))
                }
            else:
                formatted_data[ticker] = {
                    'pair': ticker,
                    'rate': float(currency_info.last_price) if hasattr(currency_info, 'last_price') and currency_info.last_price else 0,
                    'change': float(currency_info.change) if hasattr(currency_info, 'change') and currency_info.change else 0,
                    'change_percent': float(currency_info.change_percent) if hasattr(currency_info, 'change_percent') and currency_info.change_percent else 0,
                    'bid': float(currency_info.bid) if hasattr(currency_info, 'bid') and currency_info.bid else 0,
                    'ask': float(currency_info.ask) if hasattr(currency_info, 'ask') and currency_info.ask else 0,
                    'volume': float(currency_info.volume) if hasattr(currency_info, 'volume') and currency_info.volume else 0
                }
        
        return jsonify({
            'success': True,
            'currency_rates': formatted_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error fetching currency rates: {e}")
        response = jsonify({'success': False, 'error': 'Failed to fetch currency rates'})
        response.status_code = 500
        return response

@api.before_request
def before_api_request():
    """Ensure API requests are handled properly"""
    # Set JSON content type for API responses
    pass

@api.after_request
def after_api_request(response):
    """Ensure API responses have correct headers"""
    if response.content_type.startswith('text/html'):
        # If HTML is being returned from an API endpoint, convert to JSON error
        response = jsonify({
            'success': False,
            'message': 'API endpoint error - authentication required',
            'redirect': '/login'
        })
        response.status_code = 401
        return response
    return response

# Error handlers
@api.errorhandler(404)
def not_found(error):
    response = jsonify({'error': 'Endpoint ikke funnet', 'message': 'API-endepunktet du prøver å nå eksisterer ikke'})
    response.status_code = 404
    return response

@api.errorhandler(500)
def internal_error(error):
    response = jsonify({'error': 'Intern serverfeil', 'message': 'En uventet feil oppstod på serveren'})
    response.status_code = 500
    return response

@api.errorhandler(401)
def unauthorized(error):
    response = jsonify({'error': 'Ikke autorisert', 'message': 'Du må være innlogget for å bruke denne funksjonen'})
    response.status_code = 401
    return response

@api.errorhandler(403)
def forbidden(error):
    response = jsonify({'error': 'Ingen tilgang', 'message': 'Du har ikke tilgang til denne ressursen'})
    response.status_code = 403
    return response

@api.route('/stocks/<symbol>')
@api_access_required  
def get_stock_symbol_data(symbol):
    """Get detailed stock data for a specific symbol"""
    try:
        stock_data = DataService.get_stock_info(symbol)
        if not stock_data:
            response = jsonify({'error': 'Stock not found'})
            response.status_code = 404
            return response
        
        return jsonify({
            'success': True,
            'data': stock_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/stocks/<symbol>/history')
@api_access_required
def get_stock_history(symbol):
    """Get historical data for a specific stock"""
    try:
        period = request.args.get('period', '1mo')
        interval = request.args.get('interval', '1d')
        
        history_data = DataService.get_stock_data(symbol, period=period, interval=interval)
        if not history_data:
            response = jsonify({'error': 'No historical data found'})
        response.status_code = 404
        return response
            
        return jsonify({
            'success': True,
            'data': history_data,
            'symbol': symbol,
            'period': period,
            'interval': interval,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error fetching history for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/market/summary')
def market_summary():
    """API endpoint for market summary"""
    try:
        summary = {
            'oslo_bors': {
                'index': 'OSEBX',
                'value': 1345.67,
                'change': 12.34,
                'changePercent': 0.93,
                'volume': 2500000,
                'top_gainers': DataService.get_oslo_stocks()[:3],
                'top_losers': DataService.get_oslo_stocks()[3:6]
            },
            'global_markets': {
                'sp500': {
                    'value': 4567.89,
                    'change': 23.45,
                    'changePercent': 0.52
                },
                'nasdaq': {
                    'value': 15678.90,
                    'change': -45.67,
                    'changePercent': -0.29
                },
                'dow': {
                    'value': 35123.45,
                    'change': 78.90,
                    'changePercent': 0.23
                }
            },
            'crypto_summary': {
                'total_market_cap': 2350000000000,
                'btc_dominance': 42.5,
                'top_cryptos': DataService.get_crypto_data()[:3]
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': summary
        })
    except Exception as e:
        logger.error(f"Error fetching market summary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/news')
def get_news():
    """API endpoint for general news"""
    try:
        news_data = DataService.get_general_news()
        return jsonify({
            'success': True,
            'data': news_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500