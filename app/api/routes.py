from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user
from functools import wraps
import time
from datetime import datetime, timedelta
import redis
import json
import logging
from ..services.stock_service import StockService
from ..services.news_service import NewsService
from ..utils.cache_manager import cache_manager
from ..utils.rate_limiter import rate_limiter

api = Blueprint('api', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

# Helper functions
def get_company_name(ticker):
    """Get company name for ticker - mock implementation"""
    company_names = {
        'EQNR.OL': 'Equinor ASA',
        'DNB.OL': 'DNB Bank ASA',
        'TEL.OL': 'Telenor ASA',
        'NHY.OL': 'Norsk Hydro ASA',
        'YAR.OL': 'Yara International ASA',
        'AAPL': 'Apple Inc.',
        'GOOGL': 'Alphabet Inc.',
        'TSLA': 'Tesla Inc.',
        'MSFT': 'Microsoft Corporation',
        'AMZN': 'Amazon.com Inc.'
    }
    return company_names.get(ticker, ticker.replace('.OL', ''))

def generate_signal_from_real_data(data):
    """Generate trading signal based on real market data"""
    change_percent = data.get('regularMarketChangePercent', 0)
    if change_percent > 5:
        return {'signal': 'STRONG_BUY', 'confidence': 0.9}
    elif change_percent > 2:
        return {'signal': 'BUY', 'confidence': 0.7}
    elif change_percent < -5:
        return {'signal': 'STRONG_SELL', 'confidence': 0.9}
    elif change_percent < -2:
        return {'signal': 'SELL', 'confidence': 0.7}
    else:
        return {'signal': 'HOLD', 'confidence': 0.5}

def get_real_company_name(ticker, stock_info=None):
    """Get real company name from stock data, with fallback to ticker"""
    if stock_info:
        return stock_info.get('longName', stock_info.get('shortName', ticker))
    
    # Fallback for when stock_info is not available
    return ticker.replace('.OL', '')

def generate_mock_signal(data):
    """DEPRECATED: Generate mock trading signal - use generate_signal_from_real_data instead"""
    return generate_signal_from_real_data(data)

def get_company_name(ticker):
    """DEPRECATED: Get company name for ticker - use get_real_company_name instead"""
    return get_real_company_name(ticker)

# Rate limiting decorator
def api_rate_limit(max_requests=60, window=60):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if rate_limiter.wait_if_needed('api_request') > 0:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum {max_requests} requests per {window} seconds'
                }), 429
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@api.route('/stocks/quick-prices')
def get_quick_prices():
    """Optimized endpoint for quick price updates on homepage"""
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

@api.route('/homepage/market-data')
@api_rate_limit(max_requests=30, window=60)
def get_homepage_market_data():
    """Optimized endpoint for homepage market overview tables"""
    try:
        from ..services.data_service import DataService
        from ..services.technical_analysis import TechnicalAnalysis
        
        oslo_tickers = ['EQNR.OL', 'DNB.OL', 'TEL.OL', 'NHY.OL', 'YAR.OL']
        global_tickers = ['AAPL', 'GOOGL', 'TSLA', 'MSFT', 'AMZN']
        
        oslo_data = []
        global_data = []
        
        # Get real Oslo stock data
        for ticker in oslo_tickers:
            try:
                stock_info = DataService.get_stock_info(ticker)
                if stock_info:
                    current_price = stock_info.get('regularMarketPrice', stock_info.get('currentPrice', 0))
                    previous_close = stock_info.get('previousClose', current_price)
                    company_name = stock_info.get('longName', stock_info.get('shortName', ticker.replace('.OL', '')))
                    
                    change_percent = 0
                    if previous_close and previous_close > 0:
                        change_percent = ((current_price - previous_close) / previous_close) * 100
                    
                    # Generate real signal based on actual data
                    signal = generate_signal_from_real_data({'regularMarketChangePercent': change_percent})
                    
                    oslo_data.append({
                        'ticker': ticker,
                        'name': company_name,
                        'price': round(current_price, 2),
                        'change_percent': round(change_percent, 2),
                        'currency': 'NOK',
                        'signal': signal
                    })
            except Exception as e:
                current_app.logger.warning(f"Error getting data for {ticker}: {e}")
        
        # Get real global stock data
        for ticker in global_tickers:
            try:
                stock_info = DataService.get_stock_info(ticker)
                if stock_info:
                    current_price = stock_info.get('regularMarketPrice', stock_info.get('currentPrice', 0))
                    previous_close = stock_info.get('previousClose', current_price)
                    company_name = stock_info.get('longName', stock_info.get('shortName', ticker))
                    
                    change_percent = 0
                    if previous_close and previous_close > 0:
                        change_percent = ((current_price - previous_close) / previous_close) * 100
                    
                    # Generate real signal based on actual data
                    signal = generate_signal_from_real_data({'regularMarketChangePercent': change_percent})
                    
                    global_data.append({
                        'ticker': ticker,
                        'name': company_name,
                        'price': round(current_price, 2),
                        'change_percent': round(change_percent, 2),
                        'currency': 'USD',
                        'signal': signal
                    })
            except Exception as e:
                current_app.logger.warning(f"Error getting data for {ticker}: {e}")
        
        result = {
            'oslo': oslo_data,
            'global': global_data,
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': result,
            'cached': False,
            'timestamp': time.time()
        })
        
    except Exception as e:
        current_app.logger.error(f"Homepage market data API error: {str(e)}")
        return jsonify({'error': 'Kunne ikke hente markedsdata. Prøv igjen senere.'}), 500

@api.route('/news/latest')
@api_rate_limit(max_requests=20, window=60)
def get_latest_news():
    """Optimized endpoint for latest financial news"""
    try:
        limit = min(int(request.args.get('limit', 6)), 20)
        category = request.args.get('category', 'general')
        
        # Try to get real news from NewsService
        try:
            news_articles = NewsService.get_latest_news(category=category, limit=limit)
            if news_articles:
                return jsonify({
                    'success': True,
                    'articles': news_articles,
                    'cached': False,
                    'timestamp': time.time()
                })
        except Exception as e:
            logger.warning(f"Error fetching real news: {e}")
        
        # If real news is not available, show error instead of fake news
        return jsonify({
            'success': False,
            'error': 'Nyheter er ikke tilgjengelig for øyeblikket',
            'articles': [],
            'cached': False,
            'timestamp': time.time()
        })
        
    except Exception as e:
        current_app.logger.error(f"Latest news API error: {str(e)}")
        return jsonify({'error': 'Kunne ikke hente nyheter. Prøv igjen senere.'}), 500

@api.route('/market/status')
@api_rate_limit(max_requests=30, window=60)
def get_market_status():
    """Get current market status for Oslo Børs and NYSE"""
    try:
        now = datetime.now()
        oslo_hour = now.hour
        oslo_minute = now.minute
        oslo_weekday = now.weekday()
        
        oslo_open = (
            oslo_weekday < 5 and
            ((oslo_hour > 9) or (oslo_hour == 9 and oslo_minute >= 0)) and
            ((oslo_hour < 16) or (oslo_hour == 16 and oslo_minute <= 30))
        )
        
        nyse_open = (
            oslo_weekday < 5 and
            ((oslo_hour > 15) or (oslo_hour == 15 and oslo_minute >= 30)) and
            (oslo_hour < 22)
        )
        
        result = {
            'oslo': {
                'open': oslo_open,
                'name': 'Oslo Børs',
                'timezone': 'Europe/Oslo',
                'hours': '09:00-16:30 CET/CEST'
            },
            'nyse': {
                'open': nyse_open,
                'name': 'NYSE',
                'timezone': 'America/New_York',
                'hours': '09:30-16:00 ET (15:30-22:00 Oslo)'
            },
            'current_time': now.isoformat(),
            'oslo_time': now.strftime('%H:%M')
        }
        
        return jsonify({
            'success': True,
            'data': result,
            'cached': False,
            'timestamp': time.time()
        })
        
    except Exception as e:
        current_app.logger.error(f"Market status API error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/crypto/trending')
@api_rate_limit(max_requests=20, window=60)
def get_trending_crypto():
    """Get trending cryptocurrencies"""
    try:
        trending_cryptos = [
            {
                'symbol': 'BTC-USD',
                'name': 'Bitcoin',
                'price': 65432.10,
                'change_percent': 2.5,
                'volume': 25000000000,
                'market_cap': 1200000000000
            },
            {
                'symbol': 'ETH-USD',
                'name': 'Ethereum',
                'price': 3456.78,
                'change_percent': 1.8,
                'volume': 15000000000,
                'market_cap': 400000000000
            },
            {
                'symbol': 'ADA-USD',
                'name': 'Cardano',
                'price': 0.485,
                'change_percent': 3.2,
                'volume': 750000000,
                'market_cap': 15000000000
            }
        ]
        
        return jsonify({
            'success': True,
            'trending_crypto': trending_cryptos,
            'timestamp': time.time()
        })
        
    except Exception as e:
        current_app.logger.error(f"Trending crypto API error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/economic/indicators')
@api_rate_limit(max_requests=10, window=60)
def get_economic_indicators():
    """Get key economic indicators"""
    try:
        indicators = {
            'norway': {
                'inflation_rate': 2.8,
                'unemployment_rate': 3.4,
                'interest_rate': 4.5,
                'gdp_growth': 2.1,
                'oil_price_brent': 85.4
            },
            'global': {
                'us_inflation': 3.2,
                'us_unemployment': 3.8,
                'fed_rate': 5.25,
                'eur_usd': 1.08,
                'gold_price': 2015.5
            },
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'indicators': indicators,
            'timestamp': time.time()
        })
        
    except Exception as e:
        current_app.logger.error(f"Economic indicators API error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/market/sectors')
@api_rate_limit(max_requests=20, window=60)
def get_sector_analysis():
    """Get sector-wise market analysis"""
    try:
        sectors = [
            {
                'name': 'Energi',
                'performance': 2.5,
                'volume': 15000000000,
                'top_stocks': ['EQNR.OL', 'AKERBP.OL'],
                'sentiment': 'positive'
            },
            {
                'name': 'Teknologi',
                'performance': 1.8,
                'volume': 8000000000,
                'top_stocks': ['AAPL', 'GOOGL', 'MSFT'],
                'sentiment': 'positive'
            },
            {
                'name': 'Finans',
                'performance': -0.5,
                'volume': 6000000000,
                'top_stocks': ['DNB.OL', 'JPM'],
                'sentiment': 'neutral'
            }
        ]
        
        return jsonify({
            'success': True,
            'sectors': sectors,
            'timestamp': time.time()
        })
        
    except Exception as e:
        current_app.logger.error(f"Sector analysis API error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/currency')
def get_currency_rates():
    """Get formatted currency rates"""
    try:
        currency_data = {
            'USDNOK=X': {
                'ticker': 'USDNOK=X',
                'name': 'USD/NOK',
                'last_price': 10.45,
                'change': -0.15,
                'change_percent': -1.42,
                'signal': 'HOLD',
                'volume': 2500000000
            },
            'EURNOK=X': {
                'ticker': 'EURNOK=X', 
                'name': 'EUR/NOK',
                'last_price': 11.32,
                'change': 0.08,
                'change_percent': 0.71,
                'signal': 'BUY',
                'volume': 1800000000
            }
        }
        
        return jsonify(currency_data)
        
    except Exception as e:
        current_app.logger.error(f"Currency API error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Error handlers
@api.errorhandler(404)
def api_not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@api.errorhandler(500)
def api_internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@api.errorhandler(429)
def api_rate_limit_exceeded(error):
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Too many requests, please try again later'
    }), 429

# Insider Trading API endpoints
@api.route('/insider-trading/latest')
@api_rate_limit(max_requests=60, window=60)
def insider_trading_latest():
    """API endpoint for latest insider trading data"""
    try:
        from ..services.data_service import DataService
        from ..utils.access_control import _is_exempt_user, _has_active_subscription
        
        # Check access level - exempt users or subscribers get access
        has_access = _is_exempt_user() or _has_active_subscription()
        if not has_access:
            return jsonify({
                'error': 'Access denied',
                'message': 'Premium subscription required',
                'demo': True
            }), 403
        
        # Query params
        limit = request.args.get('limit', 50, type=int)
        symbol = (request.args.get('symbol') or '').strip()
        tx_filter = (request.args.get('transaction_type') or '').strip().lower()  # 'buy'|'sell'
        period_days = request.args.get('period', 30, type=int)

        # Get real insider data via DataService (symbol-scoped if provided)
        insider_data = DataService.get_insider_trading_data(symbol if symbol else None) or []

        # Filter by transaction type if requested
        if tx_filter in {'buy', 'purchase', 'kjøp'}:
            insider_data = [t for t in insider_data if str(t.get('transaction_type','')).lower() in {'buy','purchase','kjøp'}]
        elif tx_filter in {'sell', 'sale', 'salg'}:
            insider_data = [t for t in insider_data if str(t.get('transaction_type','')).lower() in {'sell','sale','salg'}]

        # Filter by period (days back)
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(days=max(1, min(period_days, 365)))
        def _parse_date(dv):
            if not dv:
                return None
            if isinstance(dv, datetime):
                return dv
            s = str(dv)
            for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f', '%d.%m.%Y'):
                try:
                    return datetime.strptime(s[:26], fmt)
                except Exception:
                    continue
            try:
                return datetime.fromisoformat(s)
            except Exception:
                return None
        insider_data = [t for t in insider_data if (_parse_date(t.get('date')) or datetime.utcnow()) >= cutoff]

        # Sort desc by date
        insider_data.sort(key=lambda t: _parse_date(t.get('date')) or datetime.min, reverse=True)

        # Map to consistent schema for frontend
        transactions = []
        for trade in insider_data[:limit]:
            if hasattr(trade, '__dict__'):
                transactions.append({
                    'symbol': getattr(trade, 'symbol', 'N/A'),
                    'date': getattr(trade, 'transaction_date', None) or getattr(trade, 'date', None),
                    'insider': getattr(trade, 'insider_name', 'Ukjent'),
                    'position': getattr(trade, 'title', '') or getattr(trade, 'position', ''),
                    'transaction_type': getattr(trade, 'transaction_type', 'Ukjent'),
                    'shares': getattr(trade, 'shares', 0),
                    'price': getattr(trade, 'price', 0),
                    'value': getattr(trade, 'value', None) or getattr(trade, 'total_value', None),
                    'company': getattr(trade, 'company', '') or getattr(trade, 'company_name', '')
                })
            else:
                transactions.append({
                    'symbol': trade.get('symbol', 'N/A'),
                    'date': trade.get('date'),
                    'insider': trade.get('insider', trade.get('insider_name', 'Ukjent')),
                    'position': trade.get('position', trade.get('role', '')),
                    'transaction_type': trade.get('transaction_type', 'Ukjent'),
                    'shares': trade.get('shares', trade.get('quantity', 0)),
                    'price': trade.get('price', 0),
                    'value': trade.get('value', trade.get('total_value', None)),
                    'company': trade.get('company', trade.get('company_name', ''))
                })

        return jsonify({'success': True, 'transactions': transactions, 'count': len(transactions)})
    except Exception as e:
        current_app.logger.error(f"Error in insider trading API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/insider-trading/trending')
@api_rate_limit(max_requests=30, window=60)
def insider_trading_trending():
    """Get trending insider trading stocks"""
    try:
        # Try to get real trending data from ExternalAPIService
        try:
            from ..services.external_apis import ExternalAPIService
            
            # Get real insider trading data for popular Norwegian stocks
            popular_tickers = ['EQNR.OL', 'DNB.OL', 'TEL.OL', 'NHY.OL', 'YAR.OL', 'MOWI.OL', 'YAR.OL']
            trending = []
            
            for ticker in popular_tickers:
                try:
                    insider_data = ExternalAPIService.get_insider_trading(ticker, limit=10)
                    if insider_data:
                        recent_activity = len(insider_data)
                        
                        # Calculate trend based on recent transactions
                        buy_count = sum(1 for trade in insider_data if 
                                      trade.get('transaction_type', '').upper() in ['BUY', 'KJØP'])
                        sell_count = len(insider_data) - buy_count
                        
                        if buy_count > sell_count * 1.5:
                            trend = 'bullish'
                        elif sell_count > buy_count * 1.5:
                            trend = 'bearish'
                        else:
                            trend = 'neutral'
                        
                        trending.append({
                            'symbol': ticker.replace('.OL', ''),
                            'recent_activity': str(recent_activity),
                            'trend': trend
                        })
                except Exception as e:
                    logger.warning(f"Error getting insider data for {ticker}: {e}")
                    continue
            
            # Sort by activity level
            trending.sort(key=lambda x: int(x['recent_activity']), reverse=True)
            
            if trending:
                return jsonify({'success': True, 'trending': trending[:8]})
                
        except ImportError:
            logger.warning("ExternalAPIService not available for insider trading trending")
        except Exception as e:
            logger.warning(f"Error getting real trending data: {e}")
        
        # If real data is not available, show error instead of fake data
        return jsonify({
            'success': False, 
            'error': 'Insider trading trending data is not available at this time',
            'trending': []
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in trending endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/insider-trading/export')
@api_rate_limit(max_requests=10, window=60)
def insider_trading_export():
    """Export insider trading data"""
    try:
        from ..utils.access_control import verify_demo_access
        
        if not verify_demo_access():
            return jsonify({
                'error': 'Access denied', 
                'message': 'Demo access required'
            }), 403
            
        # Mock export functionality
        return jsonify({
            'success': True,
            'download_url': '/downloads/insider_trading_export.csv',
            'message': 'Export ready for download'
        })
    except Exception as e:
        current_app.logger.error(f"Error in export endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/insider-trading/stats')
@api_rate_limit(max_requests=30, window=60)
def insider_trading_stats():
    """Get insider trading statistics"""
    try:
        # Try to get real statistics from ExternalAPIService
        try:
            from ..services.external_apis import ExternalAPIService
            
            # Get real insider trading data for calculation
            popular_tickers = ['EQNR.OL', 'DNB.OL', 'TEL.OL', 'NHY.OL', 'YAR.OL', 'MOWI.OL']
            all_transactions = []
            
            for ticker in popular_tickers:
                try:
                    insider_data = ExternalAPIService.get_insider_trading(ticker, limit=50)
                    if insider_data:
                        all_transactions.extend(insider_data)
                except Exception as e:
                    logger.warning(f"Error getting insider data for {ticker}: {e}")
                    continue
            
            if all_transactions:
                # Calculate real statistics
                total_transactions = len(all_transactions)
                
                buy_count = sum(1 for trade in all_transactions if 
                              trade.get('transaction_type', '').upper() in ['BUY', 'KJØP'])
                sell_count = total_transactions - buy_count
                buy_sell_ratio = buy_count / max(sell_count, 1)
                
                # Calculate average transaction value
                values = [trade.get('value', 0) for trade in all_transactions if trade.get('value', 0) > 0]
                average_transaction_value = sum(values) / len(values) if values else 0
                
                # Find most active stock
                ticker_counts = {}
                for trade in all_transactions:
                    ticker = trade.get('symbol', '').replace('.OL', '')
                    ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1
                
                most_active_stock = max(ticker_counts.items(), key=lambda x: x[1])[0] if ticker_counts else 'N/A'
                
                # Calculate sector distribution (simplified)
                sector_map = {
                    'EQNR': 'Oil & Gas',
                    'DNB': 'Banking', 
                    'TEL': 'Telecommunications',
                    'NHY': 'Materials',
                    'YAR': 'Materials',
                    'MOWI': 'Food Production'
                }
                
                sector_counts = {}
                for trade in all_transactions:
                    ticker = trade.get('symbol', '').replace('.OL', '')
                    sector = sector_map.get(ticker, 'Other')
                    sector_counts[sector] = sector_counts.get(sector, 0) + 1
                
                top_sectors = [{'sector': sector, 'count': count} 
                             for sector, count in sorted(sector_counts.items(), 
                                                       key=lambda x: x[1], reverse=True)[:3]]
                
                stats = {
                    'total_transactions': total_transactions,
                    'buy_sell_ratio': round(buy_sell_ratio, 2),
                    'average_transaction_value': int(average_transaction_value),
                    'most_active_stock': most_active_stock,
                    'top_sectors': top_sectors
                }
                
                return jsonify({'success': True, 'stats': stats})
                
        except ImportError:
            logger.warning("ExternalAPIService not available for insider trading stats")
        except Exception as e:
            logger.warning(f"Error calculating real statistics: {e}")
        
        # If real data is not available, show error instead of fake statistics
        return jsonify({
            'success': False, 
            'error': 'Insider trading statistics are not available at this time',
            'stats': {
                'total_transactions': 0,
                'buy_sell_ratio': 0,
                'average_transaction_value': 0,
                'most_active_stock': 'N/A',
                'top_sectors': []
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in stats endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
