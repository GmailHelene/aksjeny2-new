"""
Mobile Trading Interface Blueprint
=================================

Modern mobile-first trading interface with touch-optimized controls,
responsive design, and quick trade execution capabilities.
"""

from flask import Blueprint, request, jsonify, render_template, session
from flask_login import login_required, current_user
from ..utils.access_control import access_required
from ..utils.symbol_utils import sanitize_symbol
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

mobile_trading = Blueprint('mobile_trading', __name__, url_prefix='/mobile-trading')

@mobile_trading.route('/')
@login_required  # Change from demo_access to login_required
def mobile_dashboard():
    """Mobile trading dashboard"""
    try:
        return render_template('mobile_trading/dashboard.html',
                             title='Mobile Trading Dashboard')
    except Exception as e:
        logger.error(f"Mobile dashboard error: {e}")
        return render_template('error.html', error=str(e)), 500

@mobile_trading.route('/quick-trade')
@access_required
def quick_trade():
    """Quick trade interface for mobile"""
    try:
        return render_template('mobile_trading/quick_trade.html',
                             title='Quick Trade')
    except Exception as e:
        logger.error(f"Quick trade error: {e}")
        return render_template('error.html', error=str(e)), 500

@mobile_trading.route('/portfolio')
@access_required
def mobile_portfolio():
    """Mobile-optimized portfolio view"""
    try:
        return render_template('mobile_trading/portfolio.html',
                             title='Mobile Portfolio')
    except Exception as e:
        logger.error(f"Mobile portfolio error: {e}")
        return render_template('error.html', error=str(e)), 500

@mobile_trading.route('/watchlist')
@access_required
def mobile_watchlist():
    """Mobile watchlist interface"""
    try:
        return render_template('mobile_trading/watchlist.html',
                             title='Mobile Watchlist')
    except Exception as e:
        logger.error(f"Mobile watchlist error: {e}")
        return render_template('error.html', error=str(e)), 500

@mobile_trading.route('/charts')
@access_required
def mobile_charts():
    """Mobile-optimized charts"""
    try:
        return render_template('mobile_trading/charts.html',
                             title='Mobile Charts')
    except Exception as e:
        logger.error(f"Mobile charts error: {e}")
        return render_template('error.html', error=str(e)), 500

@mobile_trading.route('/api/quick-quote/<symbol>')
@access_required
def api_quick_quote(symbol):
    """API for quick stock quotes on mobile"""
    try:
        # Mock data for demonstration
        quote_data = {
            'success': True,
            'symbol': symbol.upper(),
            'price': 150.25,
            'change': 2.35,
            'change_percent': 1.59,
            'volume': 1234567,
            'market_cap': '2.5T',
            'pe_ratio': 28.5,
            'day_high': 152.80,
            'day_low': 148.10,
            'bid': 150.20,
            'ask': 150.30,
            'last_updated': datetime.now().isoformat(),
            'market_status': 'open'
        }
        
        return jsonify(quote_data)
        
    except Exception as e:
        logger.error(f"Quick quote API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_trading.route('/api/place-order', methods=['POST'])
@access_required
def api_place_order():
    """API for placing orders on mobile"""
    try:
        data = request.get_json()
        
        # Validate order data
        required_fields = ['symbol', 'action', 'quantity', 'order_type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Mock order placement
        order_data = {
            'success': True,
            'order_id': f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'symbol': data['symbol'].upper(),
            'action': data['action'],  # 'buy' or 'sell'
            'quantity': data['quantity'],
            'order_type': data['order_type'],  # 'market', 'limit', 'stop'
            'price': data.get('price'),
            'status': 'pending',
            'timestamp': datetime.now().isoformat(),
            'estimated_total': data['quantity'] * data.get('price', 150.25)
        }
        
        return jsonify(order_data)
        
    except Exception as e:
        logger.error(f"Place order API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_trading.route('/api/portfolio-summary')
@access_required
def api_portfolio_summary():
    """API for mobile portfolio summary"""
    try:
        # Mock portfolio data
        portfolio_data = {
            'success': True,
            'total_value': 125432.50,
            'daily_change': 2341.20,
            'daily_change_percent': 1.91,
            'buying_power': 15000.00,
            'positions_count': 8,
            'top_positions': [
                {
                    'symbol': 'AAPL',
                    'shares': 100,
                    'current_price': 150.25,
                    'market_value': 15025.00,
                    'unrealized_pnl': 525.00,
                    'unrealized_pnl_percent': 3.61
                },
                {
                    'symbol': 'MSFT',
                    'shares': 50,
                    'current_price': 285.40,
                    'market_value': 14270.00,
                    'unrealized_pnl': -230.00,
                    'unrealized_pnl_percent': -1.59
                },
                {
                    'symbol': 'GOOGL',
                    'shares': 25,
                    'current_price': 2345.60,
                    'market_value': 58640.00,
                    'unrealized_pnl': 1640.00,
                    'unrealized_pnl_percent': 2.88
                }
            ],
            'recent_orders': [
                {
                    'order_id': 'ORD20250723143022',
                    'symbol': 'TSLA',
                    'action': 'buy',
                    'quantity': 10,
                    'price': 245.80,
                    'status': 'filled',
                    'timestamp': '2025-07-23T14:30:22'
                }
            ],
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify(portfolio_data)
        
    except Exception as e:
        logger.error(f"Portfolio summary API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_trading.route('/api/watchlist', methods=['GET', 'POST'])
@access_required
def api_mobile_watchlist():
    """API for mobile watchlist"""
    try:
        if request.method == 'POST':
            # Handle adding stock to watchlist
            data = request.get_json()
            symbol = data.get('symbol', '').upper().strip()
            name = data.get('name', '')
            
            if not symbol:
                return jsonify({
                    'success': False,
                    'error': 'Symbol is required'
                }), 400
            
            # In demo mode, just return success
            return jsonify({
                'success': True,
                'message': f'{symbol} added to watchlist successfully!'
            })
        
        # GET request - return watchlist data
        # Mock watchlist data
        watchlist_data = {
            'success': True,
            'watchlist': [
                {
                    'symbol': 'AAPL',
                    'name': 'Apple Inc.',
                    'price': 150.25,
                    'change': 2.35,
                    'change_percent': 1.59,
                    'volume': 65432100,
                    'market_cap': '2.5T'
                },
                {
                    'symbol': 'MSFT',
                    'name': 'Microsoft Corporation',
                    'price': 285.40,
                    'change': -1.85,
                    'change_percent': -0.64,
                    'volume': 23456789,
                    'market_cap': '2.1T'
                },
                {
                    'symbol': 'GOOGL',
                    'name': 'Alphabet Inc.',
                    'price': 2345.60,
                    'change': 15.80,
                    'change_percent': 0.68,
                    'volume': 1234567,
                    'market_cap': '1.8T'
                },
                {
                    'symbol': 'TSLA',
                    'name': 'Tesla, Inc.',
                    'price': 245.80,
                    'change': -5.20,
                    'change_percent': -2.07,
                    'volume': 45678901,
                    'market_cap': '780B'
                },
                {
                    'symbol': 'NVDA',
                    'name': 'NVIDIA Corporation',
                    'price': 445.25,
                    'change': 8.75,
                    'change_percent': 2.00,
                    'volume': 34567890,
                    'market_cap': '1.1T'
                }
            ],
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify(watchlist_data)
        
    except Exception as e:
        logger.error(f"Mobile watchlist API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_trading.route('/api/watchlist/<symbol>', methods=['DELETE'])
@access_required
def api_remove_from_watchlist(symbol):
    """Remove stock from mobile watchlist"""
    try:
        symbol = symbol.upper().strip()
        
        # In demo mode, just return success
        return jsonify({
            'success': True,
            'message': f'{symbol} removed from watchlist successfully!'
        })
        
    except Exception as e:
        logger.error(f"Remove from watchlist API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_trading.route('/api/market-status')
@access_required
def api_market_status():
    """API for market status on mobile"""
    try:
        current_time = datetime.now()
        
        market_status = {
            'success': True,
            'markets': {
                'nyse': {
                    'status': 'open',
                    'next_open': '2025-07-24T09:30:00',
                    'next_close': '2025-07-23T16:00:00'
                },
                'nasdaq': {
                    'status': 'open',
                    'next_open': '2025-07-24T09:30:00',
                    'next_close': '2025-07-23T16:00:00'
                },
                'oslo_bors': {
                    'status': 'closed',
                    'next_open': '2025-07-24T09:00:00',
                    'next_close': '2025-07-24T16:30:00'
                }
            },
            'market_indices': {
                'sp500': {
                    'value': 4567.89,
                    'change': 23.45,
                    'change_percent': 0.52
                },
                'nasdaq': {
                    'value': 14567.32,
                    'change': -45.67,
                    'change_percent': -0.31
                },
                'dow': {
                    'value': 35432.10,
                    'change': 156.78,
                    'change_percent': 0.44
                },
                'osebx': {
                    'value': 1234.56,
                    'change': 5.67,
                    'change_percent': 0.46
                }
            },
            'timestamp': current_time.isoformat()
        }
        
        return jsonify(market_status)
        
    except Exception as e:
        logger.error(f"Market status API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_trading.route('/api/stock-search')
@access_required
def api_stock_search():
    """API for stock search on mobile"""
    try:
        query = request.args.get('q', '').strip().upper()
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query required'
            }), 400
        
        # Mock search results
        all_stocks = [
            {'symbol': 'AAPL', 'name': 'Apple Inc.', 'exchange': 'NASDAQ'},
            {'symbol': 'MSFT', 'name': 'Microsoft Corporation', 'exchange': 'NASDAQ'},
            {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'exchange': 'NASDAQ'},
            {'symbol': 'TSLA', 'name': 'Tesla, Inc.', 'exchange': 'NASDAQ'},
            {'symbol': 'AMZN', 'name': 'Amazon.com, Inc.', 'exchange': 'NASDAQ'},
            {'symbol': 'NVDA', 'name': 'NVIDIA Corporation', 'exchange': 'NASDAQ'},
            {'symbol': 'META', 'name': 'Meta Platforms, Inc.', 'exchange': 'NASDAQ'},
            {'symbol': 'NFLX', 'name': 'Netflix, Inc.', 'exchange': 'NASDAQ'},
            {'symbol': 'NEL', 'name': 'Nel ASA', 'exchange': 'OSE'},
            {'symbol': 'EQUI', 'name': 'Equinor ASA', 'exchange': 'OSE'}
        ]
        
        # Filter results based on query
        results = [
            stock for stock in all_stocks
            if query in stock['symbol'] or query in stock['name'].upper()
        ]
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results[:10],  # Limit to 10 results
            'total_results': len(results)
        })
        
    except Exception as e:
        logger.error(f"Stock search API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_trading.route('/api/price-alerts', methods=['GET', 'POST'])
@access_required
def api_price_alerts():
    """API for price alerts management"""
    try:
        if request.method == 'POST':
            # Create new price alert with enhanced validation
            data = request.get_json() or {}

            raw_symbol = data.get('symbol')
            if not raw_symbol:
                return jsonify({'success': False, 'message': 'Symbol er påkrevd'}), 400
            symbol, valid = sanitize_symbol(raw_symbol)
            if not valid:
                return jsonify({'success': False, 'message': 'Ugyldig symbol'}), 400

            # Standardize and validate condition
            condition = data.get('condition', '').lower().strip()
            if condition not in ['above', 'below', 'over', 'under']:
                return jsonify({'success': False, 'message': 'Ugyldig betingelse. Bruk "over" eller "under".'}), 400
            if condition == 'over':
                condition = 'above'
            elif condition == 'under':
                condition = 'below'

            # Either target price or percent threshold (or both) must be provided
            target_price = None
            percent_threshold = None

            if data.get('target_price') is not None and data.get('target_price') != '':
                try:
                    target_price = float(data.get('target_price'))
                    if target_price <= 0:
                        raise ValueError
                except (ValueError, TypeError):
                    return jsonify({'success': False, 'message': 'Ugyldig målpris. Angi et positivt tall.'}), 400

            if data.get('percent') is not None and data.get('percent') != '':
                try:
                    percent_threshold = float(data.get('percent'))
                    if abs(percent_threshold) > 50:
                        return jsonify({'success': False, 'message': 'Prosent terskel må være innen ±50%'}), 400
                except (ValueError, TypeError):
                    return jsonify({'success': False, 'message': 'Ugyldig prosent terskel'}), 400

            if target_price is None and percent_threshold is None:
                return jsonify({'success': False, 'message': 'Mangler målpris eller prosent terskel'}), 400

            # Duplicate prevention (best-effort; skip if model missing)
            try:
                from ..models.price_alert import PriceAlert  # type: ignore
                existing = PriceAlert.query.filter_by(user_id=current_user.id, ticker=symbol, alert_type=condition).first()
                if existing:
                    return jsonify({'success': False, 'message': 'Varsel finnes allerede'}), 409
            except Exception:
                pass

            alert_id = f"ALERT{datetime.now().strftime('%Y%m%d%H%M%S')}"
            alert_data = {
                'success': True,
                'message': 'Prisvarsel opprettet',
                'alert_id': alert_id,
                'symbol': symbol,
                'condition': condition,
                'target_price': target_price,
                'percent_threshold': percent_threshold,
                'current_price': data.get('current_price', 0),
                'enabled': True,
                'created': datetime.now().isoformat()
            }
            logger.info(f"Price alert created: {alert_data}")
            return jsonify(alert_data)
        
        else:
            # Get existing alerts (demo data)
            raw_filter = request.args.get('symbol', '')
            if raw_filter:
                symbol_filter, valid = sanitize_symbol(raw_filter)
                if not valid:
                    return jsonify({'success': False, 'alerts': [], 'count': 0, 'message': 'Ugyldig symbolfilter'}), 400
            else:
                symbol_filter = ''
            
            alerts = [
                {
                    'alert_id': 'ALERT20250723140000',
                    'symbol': 'AAPL',
                    'condition': 'above',
                    'target_price': 220.50,
                    'current_price': 215.75,
                    'enabled': True,
                    'created': '2025-07-23T14:00:00',
                    'percent_to_target': 2.2
                },
                {
                    'alert_id': 'ALERT20250723135800',
                    'symbol': 'EQNR.OL',
                    'condition': 'below',
                    'target_price': 250.00,
                    'current_price': 265.80,
                    'enabled': True,
                    'created': '2025-07-23T13:58:00',
                    'percent_to_target': -5.9
                }
            ]
            
            # Filter by symbol if requested
            if symbol_filter:
                alerts = [alert for alert in alerts if alert['symbol'] == symbol_filter]
            
            return jsonify({
                'success': True,
                'alerts': alerts,
                'count': len(alerts)
            })
            
    except Exception as e:
        logger.error(f"Error in price alerts API: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'En teknisk feil oppstod. Prøv igjen senere.'
        }), 500
