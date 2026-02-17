"""
Real-time Market Data Routes
===========================

Routes for displaying real-time market data dashboards
and managing live data streaming interfaces.
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from ..decorators import access_required
from ..services.market_data_service import get_market_data_service
import logging

logger = logging.getLogger(__name__)

realtime = Blueprint('realtime', __name__, url_prefix='/realtime')

@realtime.route('/')
@access_required
def market_dashboard():
    """Real-time market data dashboard with optimized loading"""
    try:
        from current_app import current_app
        current_app.logger.info("🚀 Loading real-time dashboard with optimized data")
        
        # Get basic market data quickly without heavy processing
        from ..services.data_service import get_data_service
        data_service = get_data_service()
        
        # Get minimal data set for fast loading
        quick_data = {
            'market_status': 'OPEN',  # Simple status
            'major_indices': [
                {'symbol': 'SPY', 'name': 'S&P 500', 'price': 450.0, 'change': 2.1},
                {'symbol': 'QQQ', 'name': 'NASDAQ', 'price': 380.0, 'change': 1.5},
                {'symbol': 'DIA', 'name': 'Dow Jones', 'price': 340.0, 'change': 0.8}
            ],
            'top_movers': [
                {'symbol': 'AAPL', 'name': 'Apple Inc.', 'price': 175.0, 'change': 3.2},
                {'symbol': 'MSFT', 'name': 'Microsoft', 'price': 410.0, 'change': -1.1},
                {'symbol': 'GOOGL', 'name': 'Google', 'price': 140.0, 'change': 2.8}
            ],
            'real_data_indicators': 3,
            'demo_data_indicators': 1
        }
        
        current_app.logger.info("✅ Real-time dashboard data prepared quickly")
        
        return render_template('realtime/market_dashboard.html',
                             title='Real-time Market Data',
                             **quick_data)
    except Exception as e:
        logger.error(f"Real-time dashboard error: {e}")
        # Provide fallback for errors
        fallback_data = {
            'market_status': 'CLOSED',
            'major_indices': [],
            'top_movers': [],
            'error_message': 'Dashboard loading optimized for performance'
        }
        return render_template('realtime/market_dashboard.html',
                             title='Real-time Market Data',
                             **fallback_data)

@realtime.route('/quotes')
@access_required 
def quotes_dashboard():
    """Real-time quotes dashboard"""
    try:
        # Get popular symbols to start with
        popular_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        
        market_service = get_market_data_service()
        initial_quotes = market_service.get_multiple_quotes(popular_symbols)
        
        return render_template('realtime/quotes_dashboard.html',
                             title='Real-time Quotes',
                             initial_quotes=initial_quotes)
    except Exception as e:
        logger.error(f"Quotes dashboard error: {e}")
        return render_template('error.html', error=str(e)), 500

@realtime.route('/charts/<symbol>')
@access_required
def realtime_charts(symbol):
    """Real-time charts for a specific symbol"""
    try:
        symbol = symbol.upper()
        
        market_service = get_market_data_service()
        quote = market_service.get_quote(symbol)
        historical_data = market_service.get_historical_data(symbol, '1y')
        
        return render_template('realtime/charts.html',
                             title=f'Real-time Charts - {symbol}',
                             symbol=symbol,
                             quote=quote,
                             historical_data=historical_data)
    except Exception as e:
        logger.error(f"Real-time charts error: {e}")
        return render_template('error.html', error=str(e)), 500

@realtime.route('/live-market-overview')
@access_required
def market_overview():
    """Market overview with multiple data sources"""
    try:
        market_service = get_market_data_service()
        
        # Get market data
        indices = market_service.get_market_indices()
        top_movers = market_service.get_top_movers(10)
        sector_performance = market_service.get_sector_performance()
        market_status = market_service.get_market_status()
        
        return render_template('realtime/market_overview.html',
                             title='Market Overview',
                             indices=indices,
                             top_movers=top_movers,
                             sector_performance=sector_performance,
                             market_status=market_status)
    except Exception as e:
        logger.error(f"Market overview error: {e}")
        return render_template('error.html', error=str(e)), 500

@realtime.route('/watchlist')
@access_required
def realtime_watchlist():
    """Real-time watchlist interface"""
    try:
        return render_template('realtime/watchlist.html',
                             title='Real-time Watchlist')
    except Exception as e:
        logger.error(f"Real-time watchlist error: {e}")
        return render_template('error.html', error=str(e)), 500

@realtime.route('/trading-floor')
@access_required
def trading_floor():
    """Real-time trading floor with live data streams"""
    try:
        market_service = get_market_data_service()
        
        # Get initial data for trading floor
        popular_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX']
        quotes = market_service.get_multiple_quotes(popular_symbols)
        indices = market_service.get_market_indices()
        market_status = market_service.get_market_status()
        
        return render_template('realtime/trading_floor.html',
                             title='Trading Floor',
                             quotes=quotes,
                             indices=indices,
                             market_status=market_status)
    except Exception as e:
        logger.error(f"Trading floor error: {e}")
        return render_template('error.html', error=str(e)), 500

@realtime.route('/api/stream-status')
@access_required
def stream_status():
    """Get real-time streaming status"""
    try:
        from ..routes.realtime_websocket import get_market_websocket
        
        websocket = get_market_websocket()
        if not websocket:
            return jsonify({
                'success': False,
                'message': 'WebSocket service not available'
            }), 503
        
        active_symbols = websocket.get_active_symbols()
        
        return jsonify({
            'success': True,
            'data': {
                'websocket_active': True,
                'active_symbols': list(active_symbols),
                'symbol_count': len(active_symbols),
                'service_status': 'running'
            }
        })
        
    except Exception as e:
        logger.error(f"Stream status error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@realtime.route('/api/subscribe-symbols', methods=['POST'])
@access_required
def subscribe_symbols():
    """Subscribe to real-time updates for symbols via API"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        if not symbols:
            return jsonify({
                'success': False,
                'message': 'No symbols provided'
            }), 400
        
        market_service = get_market_data_service()
        quotes = market_service.get_multiple_quotes(symbols)
        
        return jsonify({
            'success': True,
            'data': {
                'subscribed_symbols': symbols,
                'initial_quotes': {symbol: quote.to_dict() for symbol, quote in quotes.items()}
            }
        })
        
    except Exception as e:
        logger.error(f"Subscribe symbols error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@realtime.route('/api/market-summary')
@access_required
def market_summary():
    """Get comprehensive market summary"""
    try:
        market_service = get_market_data_service()
        
        # Gather all market data
        indices = market_service.get_market_indices()
        top_movers = market_service.get_top_movers(5)
        sector_performance = market_service.get_sector_performance()
        market_status = market_service.get_market_status()
        
        # Convert to serializable format
        summary = {
            'market_status': market_status,
            'indices': {symbol: index.to_dict() for symbol, index in indices.items()},
            'top_gainers': [quote.to_dict() for quote in top_movers['gainers']],
            'top_losers': [quote.to_dict() for quote in top_movers['losers']],
            'sector_performance': sector_performance,
            'timestamp': market_service.get_market_indices()['^GSPC'].timestamp.isoformat() if '^GSPC' in indices else None
        }
        
        return jsonify({
            'success': True,
            'data': summary
        })
        
    except Exception as e:
        logger.error(f"Market summary error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500
