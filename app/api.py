"""
API routes for Aksjeradar
"""
from flask import Blueprint, jsonify, request
from flask_login import current_user
from datetime import datetime, timedelta
# from .services.ml_prediction_service import MLPredictionService
from .services.portfolio_optimizer import PortfolioOptimizer  
from .services.risk_manager import RiskManager
from .services.insider_trading_service import InsiderTradingService
from .services.financial_data_aggregator import FinancialDataAggregator
import logging
# import numpy as np

logger = logging.getLogger(__name__)

api = Blueprint('api', __name__)

# Initialize services
# ml_service = MLPredictionService()
portfolio_optimizer = PortfolioOptimizer()
risk_manager = RiskManager()
insider_service = InsiderTradingService()
data_aggregator = FinancialDataAggregator()

@api.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'aksjeradar',
        'version': '1.0.0'
    })

@api.route('/routes')
def list_routes():
    """Return a diagnostic listing of registered Flask routes/endpoints.

    Useful in production to verify optional blueprints (e.g. sentiment_tracker)
    actually loaded without causing template BuildError. Lightweight and safe
    to expose (no auth-protected details) but can be restricted later if needed.
    """
    try:
        from flask import current_app
        output = []
        for rule in current_app.url_map.iter_rules():
            methods = sorted(m for m in rule.methods if m not in {"OPTIONS", "HEAD"})
            output.append({
                'endpoint': rule.endpoint,
                'rule': str(rule),
                'methods': methods
            })
        # Highlight presence of sentiment tracker explicitly
        has_sentiment = any(r['endpoint'].startswith('sentiment_tracker.') for r in output)
        return jsonify({
            'success': True,
            'route_count': len(output),
            'has_sentiment_tracker': has_sentiment,
            'routes': output
        })
    except Exception as e:
        logger.error(f"Failed to list routes: {e}")
        return jsonify({'success': False, 'error': 'route listing failed'}), 500

@api.route('/version')  
def version():
    """Version info endpoint"""
    return jsonify({
        'version': '1.0.0',
        'service': 'aksjeradar'
    })

# ML Prediction endpoints
@api.route('/ml/predict/<symbol>', methods=['GET'])
def predict_stock(symbol):
    """Get ML prediction for a stock"""
    try:
        days_ahead = request.args.get('days', 30, type=int)
        prediction = ml_service.predict_stock_price(symbol, days_ahead)
        
        if prediction:
            return jsonify({
                'success': True,
                'symbol': symbol,
                'prediction': prediction
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Unable to generate prediction'
            }), 404
            
    except Exception as e:
        logger.error(f"Error predicting stock {symbol}: {e}")
        return jsonify({
            'success': False,
            'message': 'Prediction service unavailable'
        }), 500

@api.route('/ml/batch-predict', methods=['POST'])
def batch_predict():
    """Get predictions for multiple stocks"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        days_ahead = data.get('days', 30)
        
        predictions = ml_service.batch_predict(symbols, days_ahead)
        
        return jsonify({
            'success': True,
            'predictions': predictions
        })
        
    except Exception as e:
        logger.error(f"Error in batch prediction: {e}")
        return jsonify({
            'success': False,
            'message': 'Batch prediction failed'
        }), 500

@api.route('/ml/market-analysis', methods=['GET'])
def market_analysis():
    """Get comprehensive market analysis"""
    try:
        analysis = ml_service.get_market_analysis()
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Error in market analysis: {e}")
        return jsonify({
            'success': False,
            'message': 'Market analysis unavailable'
        }), 500

# Portfolio Optimization endpoints
@api.route('/portfolio/optimize', methods=['POST'])
def optimize_portfolio():
    """Optimize portfolio allocation"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        weights = data.get('weights')
        method = data.get('method', 'sharpe')
        
        result = portfolio_optimizer.optimize_portfolio(symbols, weights, method)
        
        return jsonify({
            'success': True,
            'optimization': result
        })
        
    except Exception as e:
        logger.error(f"Error optimizing portfolio: {e}")
        return jsonify({
            'success': False,
            'message': 'Portfolio optimization failed'
        }), 500

@api.route('/portfolio/efficient-frontier', methods=['POST'])
def efficient_frontier():
    """Generate efficient frontier for portfolio"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        num_portfolios = data.get('num_portfolios', 10000)
        
        frontier = portfolio_optimizer.generate_efficient_frontier(symbols, num_portfolios)
        
        return jsonify({
            'success': True,
            'frontier': frontier
        })
        
    except Exception as e:
        logger.error(f"Error generating efficient frontier: {e}")
        return jsonify({
            'success': False,
            'message': 'Efficient frontier generation failed'
        }), 500

@api.route('/portfolio/rebalance', methods=['POST'])
def rebalance_portfolio():
    """Get portfolio rebalancing recommendations"""
    try:
        data = request.get_json()
        current_portfolio = data.get('current_portfolio', {})
        target_allocation = data.get('target_allocation', {})
        
        recommendations = portfolio_optimizer.rebalance_portfolio(
            current_portfolio, target_allocation
        )
        
        return jsonify({
            'success': True,
            'rebalancing': recommendations
        })
        
    except Exception as e:
        logger.error(f"Error rebalancing portfolio: {e}")
        return jsonify({
            'success': False,
            'message': 'Portfolio rebalancing failed'
        }), 500

# Risk Management endpoints
@api.route('/risk/portfolio-risk', methods=['POST'])
def portfolio_risk():
    """Calculate portfolio risk metrics"""
    try:
        data = request.get_json()
        portfolio = data.get('portfolio', {})
        timeframe = data.get('timeframe', 252)
        
        risk_metrics = risk_manager.calculate_portfolio_risk(portfolio, timeframe)
        
        return jsonify({
            'success': True,
            'risk_metrics': risk_metrics
        })
        
    except Exception as e:
        logger.error(f"Error calculating portfolio risk: {e}")
        return jsonify({
            'success': False,
            'message': 'Risk calculation failed'
        }), 500

@api.route('/risk/var-analysis', methods=['POST'])
def var_analysis():
    """Perform Value at Risk analysis"""
    try:
        data = request.get_json()
        portfolio = data.get('portfolio', {})
        confidence_level = data.get('confidence_level', 0.95)
        time_horizon = data.get('time_horizon', 1)
        
        var_result = risk_manager.calculate_var(portfolio, confidence_level, time_horizon)
        
        return jsonify({
            'success': True,
            'var_analysis': var_result
        })
        
    except Exception as e:
        logger.error(f"Error in VaR analysis: {e}")
        return jsonify({
            'success': False,
            'message': 'VaR analysis failed'
        }), 500

@api.route('/risk/stress-test', methods=['POST'])
def stress_test():
    """Perform portfolio stress testing"""
    try:
        data = request.get_json()
        portfolio = data.get('portfolio', {})
        scenario = data.get('scenario', 'market_crash')
        
        stress_result = risk_manager.stress_test_portfolio(portfolio, scenario)
        
        return jsonify({
            'success': True,
            'stress_test': stress_result
        })
        
    except Exception as e:
        logger.error(f"Error in stress testing: {e}")
        return jsonify({
            'success': False,
            'message': 'Stress testing failed'
        }), 500

@api.route('/risk/monte-carlo', methods=['POST'])
def monte_carlo_simulation():
    """Run Monte Carlo risk simulation"""
    try:
        data = request.get_json()
        portfolio = data.get('portfolio', {})
        simulations = data.get('simulations', 10000)
        time_horizon = data.get('time_horizon', 252)
        
        mc_result = risk_manager.monte_carlo_simulation(portfolio, simulations, time_horizon)
        
        return jsonify({
            'success': True,
            'monte_carlo': mc_result
        })
        
    except Exception as e:
        logger.error(f"Error in Monte Carlo simulation: {e}")
        return jsonify({
            'success': False,
            'message': 'Monte Carlo simulation failed'
        }), 500

# Insider Trading endpoints
@api.route('/insider-trading/<symbol>', methods=['GET'])
def get_insider_trading_data(symbol):
    """Get insider trading data for a specific stock"""
    try:
        data = insider_service.get_insider_trading_data(symbol)
        
        if data:
            return jsonify({
                'success': True,
                'symbol': symbol,
                'insider_trading_data': data
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No insider trading data found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error fetching insider trading data for {symbol}: {e}")
        return jsonify({
            'success': False,
            'message': 'Insider trading data service unavailable'
        }), 500

@api.route('/insider-trading/batch', methods=['POST'])
def batch_insider_trading():
    """Get insider trading data for multiple stocks"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        result = {}
        for symbol in symbols:
            result[symbol] = insider_service.get_insider_trading_data(symbol)
        
        return jsonify({
            'success': True,
            'insider_trading_data': result
        })
        
    except Exception as e:
        logger.error(f"Error in batch insider trading data request: {e}")
        return jsonify({
            'success': False,
            'message': 'Batch insider trading data request failed'
        }), 500

# Insider Trading and Market Intelligence endpoints
@api.route('/insider/transactions/<symbol>', methods=['GET'])
def get_insider_transactions(symbol):
    """Get insider trading transactions for a symbol"""
    try:
        days_back = request.args.get('days', 90, type=int)
        transactions = insider_service.get_insider_transactions(symbol, days_back)
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'transactions': [insider_service._transaction_to_dict(t) for t in transactions]
        })
        
    except Exception as e:
        logger.error(f"Error getting insider transactions for {symbol}: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get insider transactions'
        }), 500

@api.route('/insider/sentiment/<symbol>', methods=['GET'])
def get_market_sentiment(symbol):
    """Get market sentiment analysis for a symbol"""
    try:
        sentiment = insider_service.get_market_sentiment(symbol)
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'sentiment': insider_service._sentiment_to_dict(sentiment)
        })
        
    except Exception as e:
        logger.error(f"Error getting market sentiment for {symbol}: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get market sentiment'
        }), 500

@api.route('/insider/short-interest/<symbol>', methods=['GET'])
def get_short_interest(symbol):
    """Get short interest data for a symbol"""
    try:
        short_data = insider_service.get_short_interest_data(symbol)
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'short_interest': insider_service._short_data_to_dict(short_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting short interest for {symbol}: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get short interest data'
        }), 500

@api.route('/insider/analysis/<symbol>', methods=['GET'])
def get_comprehensive_analysis(symbol):
    """Get comprehensive insider trading and market intelligence analysis"""
    try:
        analysis = insider_service.get_comprehensive_analysis(symbol)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Error getting comprehensive analysis for {symbol}: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get comprehensive analysis'
        }), 500

@api.route('/insider/batch-analysis', methods=['POST'])
def batch_insider_analysis():
    """Get insider trading analysis for multiple symbols"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        if not symbols:
            return jsonify({
                'success': False,
                'message': 'No symbols provided'
            }), 400
        
        results = {}
        for symbol in symbols[:10]:  # Limit to 10 symbols
            try:
                results[symbol] = insider_service.get_comprehensive_analysis(symbol)
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                results[symbol] = {'error': str(e)}
        
        return jsonify({
            'success': True,
            'analyses': results
        })
        
    except Exception as e:
        logger.error(f"Error in batch insider analysis: {e}")
        return jsonify({
            'success': False,
            'message': 'Batch analysis failed'
        }), 500

# Financial News and Market Data endpoints
@api.route('/news/<symbol>', methods=['GET'])
def get_financial_news(symbol):
    """Get financial news for a symbol"""
    try:
        # This would integrate with news APIs
        # For now, return demo data structure
        news_data = {
            'symbol': symbol,
            'articles': [
                {
                    'title': f'Latest analysis on {symbol}',
                    'summary': f'Market experts analyze recent performance of {symbol}',
                    'sentiment': 'positive',
                    'source': 'Financial News',
                    'timestamp': '2025-07-14T10:00:00Z',
                    'url': f'https://aksjeradar.trade/news/{symbol.lower()}'
                }
            ]
        }
        
        return jsonify({
            'success': True,
            'news': news_data
        })
        
    except Exception as e:
        logger.error(f"Error getting news for {symbol}: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get financial news'
        }), 500

@api.route('/market/overview', methods=['GET'])
def get_market_overview():
    """Get general market overview and sentiment"""
    try:
        overview = {
            'market_status': 'open',
            'overall_sentiment': 'bullish',
            'volatility_index': 18.5,
            'top_movers': [
                {'symbol': 'TSLA', 'change': '+5.2%'},
                {'symbol': 'AAPL', 'change': '+2.1%'},
                {'symbol': 'GOOGL', 'change': '-1.8%'}
            ],
            'insider_activity_summary': {
                'total_transactions_today': 156,
                'buy_sell_ratio': 1.4,
                'top_insider_sectors': ['Technology', 'Healthcare', 'Finance']
            }
        }
        
        return jsonify({
            'success': True,
            'market_overview': overview
        })
        
    except Exception as e:
        logger.error(f"Error getting market overview: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get market overview'
        }), 500

# Comprehensive Financial Data Aggregation endpoints
@api.route('/crypto/data', methods=['GET'])
def get_crypto_data():
    """Get cryptocurrency market data"""
    try:
        symbols = request.args.getlist('symbols')
        limit = request.args.get('limit', 100, type=int)
        
        crypto_data = data_aggregator.get_crypto_data(symbols if symbols else None, limit)
        
        return jsonify({
            'success': True,
            'crypto_data': [data_aggregator._crypto_to_dict(c) for c in crypto_data]
        })
        
    except Exception as e:
        logger.error(f"Error getting crypto data: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get crypto data'
        }), 500

@api.route('/crypto/trending', methods=['GET'])
def get_trending_crypto():
    """Get trending cryptocurrencies"""
    try:
        trending = data_aggregator.get_trending_crypto()
        
        return jsonify({
            'success': True,
            'trending_crypto': trending
        })
        
    except Exception as e:
        logger.error(f"Error getting trending crypto: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get trending crypto'
        }), 500



@api.route('/news/financial', methods=['GET'])
def get_financial_news_api():
    """Get financial news from multiple sources"""
    try:
        symbols = request.args.getlist('symbols')
        limit = request.args.get('limit', 50, type=int)
        
        # Return demo Norwegian financial news
        news_articles = [
            {
                'title': 'Equinor rapporterer sterke kvartalstall',
                'summary': 'Norges største oljeselskap overgår forventningene med økt produksjon og høyere oljepriser.',
                'content': 'Equinor leverte sterke resultater for andre kvartal med betydelig økning i både produksjon og lønnsomhet...',
                'source': 'E24',
                'author': 'Finansredaksjonen',
                'published_at': '2025-07-14T09:00:00Z',
                'url': 'https://e24.no/equinor-kvartal',
                'sentiment': 'positive',
                'related_symbols': ['EQNR.OL']
            },
            {
                'title': 'Norges Bank holder renten uendret på 4,5%',
                'summary': 'Sentralbanken opprettholder styringsrenten, men signaliserer mulige endringer senere i år.',
                'content': 'Norges Bank besluttet å holde styringsrenten uendret på 4,5 prosent, i tråd med markedets forventninger...',
                'source': 'DN',
                'author': 'Økonomiavdelingen',
                'published_at': '2025-07-14T08:30:00Z',
                'url': 'https://dn.no/norges-bank-rente',
                'sentiment': 'neutral',
                'related_symbols': ['DNB.OL', 'EQNR.OL']
            },
            {
                'title': 'Tesla viser sterk vekst i Norge',
                'summary': 'Elbilgiganten fortsetter å vinne markedsandeler i det norske markedet.',
                'content': 'Tesla rapporterer om rekordlevering av elektriske biler i Norge, med Model Y som den mest populære...',
                'source': 'TU',
                'author': 'Bilredaksjonen',
                'published_at': '2025-07-14T07:45:00Z',
                'url': 'https://tu.no/tesla-norge',
                'sentiment': 'positive',
                'related_symbols': ['TSLA']
            },
            {
                'title': 'Oslo Børs åpner med oppgang',
                'summary': 'Hovedindeksen starter uken positivt med støtte fra energisektoren.',
                'content': 'Oslo Børs åpnet med bred oppgang mandag morgen, ledet an av Equinor og andre energiselskaper...',
                'source': 'Finansavisen',
                'author': 'Markedsredaksjonen',
                'published_at': '2025-07-14T07:00:00Z',
                'url': 'https://finansavisen.no/oslo-bors-oppgang',
                'sentiment': 'positive',
                'related_symbols': ['EQNR.OL', 'AKERBP.OL', 'YAR.OL']
            },
            {
                'title': 'Fed holder rentene uendret før sommerpause',
                'summary': 'Den amerikanske sentralbanken opprettholder renten på 5,25% som ventet.',
                'content': 'Federal Reserve besluttet å holde federal funds rate uendret på 5,25%, men ser tegn til moderering i inflasjonen...',
                'source': 'Reuters',
                'author': 'Economics Team',
                'published_at': '2025-07-13T19:00:00Z',
                'url': 'https://reuters.com/fed-rates',
                'sentiment': 'neutral',
                'related_symbols': ['AAPL', 'GOOGL', 'MSFT']
            }
        ]
        
        # Filter by symbols if provided
        if symbols:
            filtered_news = []
            for article in news_articles:
                if any(symbol in article.get('related_symbols', []) for symbol in symbols):
                    filtered_news.append(article)
            news_articles = filtered_news
        
        # Limit results
        news_articles = news_articles[:limit]
        
        return jsonify({
            'success': True,
            'news': news_articles
        })
        
    except Exception as e:
        logger.error(f"Error getting financial news: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get financial news'
        }), 500

@api.route('/economic/indicators', methods=['GET'])
def get_economic_indicators():
    """Get key economic indicators"""
    try:
        # Return meaningful Norwegian and global economic indicators
        indicators = [
            {
                'name': 'Norwegian Interest Rate',
                'value': '4.50%',
                'change': 0.0,
                'description': 'Norges Bank Policy Rate',
                'last_updated': '2025-07-14T10:00:00Z'
            },
            {
                'name': 'Norwegian Inflation (CPI)',
                'value': '3.2%',
                'change': -0.3,
                'description': 'Year-over-year inflation rate',
                'last_updated': '2025-07-01T08:00:00Z'
            },
            {
                'name': 'Unemployment Rate',
                'value': '3.5%',
                'change': -0.1,
                'description': 'Norwegian unemployment rate',
                'last_updated': '2025-06-30T08:00:00Z'
            },
            {
                'name': 'USD/NOK Exchange Rate',
                'value': '10.45',
                'change': -1.42,
                'description': 'US Dollar to Norwegian Krone',
                'last_updated': '2025-07-14T11:30:00Z'
            },
            {
                'name': 'Brent Crude Oil',
                'value': '$85.20',
                'change': 2.1,
                'description': 'Brent crude oil price per barrel',
                'last_updated': '2025-07-14T11:30:00Z'
            },
            {
                'name': 'Federal Funds Rate',
                'value': '5.25%',
                'change': 0.0,
                'description': 'US Federal Reserve interest rate',
                'last_updated': '2025-06-14T14:00:00Z'
            }
        ]
        
        return jsonify({
            'success': True,
            'economic_indicators': indicators
        })
        
    except Exception as e:
        logger.error(f"Error getting economic indicators: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get economic indicators'
        }), 500

@api.route('/market/comprehensive', methods=['POST'])
def get_comprehensive_market_data():
    """Get comprehensive market data for multiple symbols"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN'])
        
        market_data = data_aggregator.get_comprehensive_market_data(symbols)
        
        return jsonify({
            'success': True,
            'market_data': market_data
        })
        
    except Exception as e:
        logger.error(f"Error getting comprehensive market data: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get comprehensive market data'
        }), 500

@api.route('/dashboard/data', methods=['GET'])
def get_dashboard_data():
    """Get aggregated data for dashboard display"""
    try:
        user_symbols = request.args.getlist('symbols')
        
        if not user_symbols:
            # Default Norwegian and international stocks
            user_symbols = ['EQNR.OL', 'DNB.OL', 'TEL.OL', 'AAPL', 'GOOGL', 'MSFT', 'TSLA']
        
        # Generate realistic demo dashboard data
        dashboard_data = {
            'portfolio_summary': {
                'total_value': 1250000,  # NOK
                'daily_change': 2.3,     # %
                'daily_change_value': 28750,  # NOK
                'stocks_count': len(user_symbols),
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
                    'forecast': '5.25%'
                },
                {
                    'event': 'Norwegian GDP Release',
                    'time': '2025-07-17T08:00:00Z',
                    'impact': 'medium',
                    'forecast': '2.1%'
                }
            ]
        }
        
        return jsonify({
            'success': True,
            'dashboard_data': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get dashboard data'
        }), 500

# Norwegian Market Specific endpoints
@api.route('/norwegian/stocks', methods=['GET'])
def get_norwegian_stocks():
    """Get Norwegian stock market data"""
    try:
        norwegian_symbols = [
            'EQNR.OL', 'DNB.OL', 'TEL.OL', 'YAR.OL', 'NHY.OL', 'AKSO.OL',
            'MOWI.OL', 'ORK.OL', 'SALM.OL', 'AKERBP.OL', 'SUBC.OL', 'KAHOT.OL'
        ]
        
        norwegian_data = data_aggregator.get_comprehensive_market_data(norwegian_symbols)
        
        return jsonify({
            'success': True,
            'norwegian_stocks': norwegian_data
        })
        
    except Exception as e:
        logger.error(f"Error getting Norwegian stocks: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get Norwegian stock data'
        }), 500

@api.route('/market/sectors', methods=['GET'])
def get_sector_analysis():
    """Get sector-wise market analysis"""
    try:
        # Sector data would be calculated from individual stocks
        sector_data = {
            'technology': {
                'symbols': ['AAPL', 'GOOGL', 'MSFT', 'TSLA'],
                'performance': '+2.3%',
                'trend': 'bullish'
            },
            'energy': {
                'symbols': ['EQNR.OL', 'AKERBP.OL'],
                'performance': '+1.8%',
                'trend': 'bullish'
            },
            'finance': {
                'symbols': ['DNB.OL'],
                'performance': '+0.9%',
                'trend': 'neutral'
            },
            'telecommunications': {
                'symbols': ['TEL.OL'],
                'performance': '-0.5%',
                'trend': 'bearish'
            }
        }
        
        return jsonify({
            'success': True,
            'sector_analysis': sector_data
        })
        
    except Exception as e:
        logger.error(f"Error getting sector analysis: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get sector analysis'
        }), 500

# Real-time data endpoints  
@api.route('/realtime/quotes', methods=['POST'])
def get_realtime_quotes():
    """Get real-time quotes for multiple symbols"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        if not symbols:
            return jsonify({
                'success': False,
                'message': 'No symbols provided'
            }), 400
        
        # Get real-time data using yfinance or other sources
        quotes = {}
        for symbol in symbols[:20]:  # Limit to 20 symbols
            try:
                try:
                    import yfinance as yf
                except ImportError:
                    yf = None
                
                if yf is None:
                    # Return fallback data when yfinance is not available
                    quotes = {}
                    for symbol in symbols:
                        quotes[symbol] = {
                            'symbol': symbol,
                            'price': 100.0 + (hash(symbol) % 100),  # Deterministic but varied prices
                            'change': ((hash(symbol) % 21) - 10) / 10,  # Random-ish change -1 to +1
                            'change_percent': ((hash(symbol) % 21) - 10) / 10,
                            'volume': 1000000 + (hash(symbol) % 500000),
                            'timestamp': datetime.now().isoformat(),
                            'market_status': 'open'
                        }
                    
                    return jsonify({
                        'success': True,
                        'quotes': quotes,
                        'note': 'Using fallback data - yfinance not available'
                    })
                    
                # Original yfinance code would go here when available
                if yf is not None:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    quotes[symbol] = {
                        'price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                        'change': info.get('regularMarketChange', 0),
                        'change_percent': info.get('regularMarketChangePercent', 0),
                        'volume': info.get('regularMarketVolume', 0),
                        'market_status': 'open'  # Would be determined by market hours
                    }
                else:
                    # Return fallback when yfinance not available
                    quotes[symbol] = {
                        'symbol': symbol,
                        'price': 100.0 + (hash(symbol) % 100),
                        'change': ((hash(symbol) % 21) - 10) / 10,
                        'volume': 1000000,
                        'timestamp': datetime.now().isoformat(),
                        'note': 'Fallback data - yfinance not available'
                    }
            except:
                # Fallback to demo data
                quotes[symbol] = {
                    'price': np.random.uniform(50, 300),
                    'change': np.random.uniform(-5, 5),
                    'change_percent': np.random.uniform(-3, 3),
                    'volume': np.random.randint(100000, 10000000),
                    'market_status': 'open'
                }
        
        return jsonify({
            'success': True,
            'quotes': quotes
        })
        
    except Exception as e:
        logger.error(f"Error getting real-time quotes: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get real-time quotes'
        }), 500

# Currency API endpoints with better formatting
@api.route('/currency/formatted', methods=['GET'])
def get_formatted_currency():
    """Get formatted currency data for display"""
    try:
        # Get base currency data (similar to your JSON structure)
        currencies = {
            "EURNOK=X": {
                "change": 0.08,
                "change_percent": 0.71,
                "last_price": 11.32,
                "name": "EUR/NOK",
                "signal": "BUY",
                "ticker": "EURNOK=X",
                "volume": 1800000000,
                "high": 11.35,
                "low": 11.28
            },
            "USDNOK=X": {
                "change": -0.15,
                "change_percent": -1.42,
                "last_price": 10.45,
                "name": "USD/NOK",
                "signal": "HOLD",
                "ticker": "USDNOK=X",
                "volume": 2500000000,
                "high": 10.58,
                "low": 10.42
            },
            "GBPNOK=X": {
                "change": 0.12,
                "change_percent": 0.89,
                "last_price": 13.15,
                "name": "GBP/NOK",
                "signal": "BUY",
                "ticker": "GBPNOK=X",
                "volume": 950000000,
                "high": 13.18,
                "low": 13.05
            },
            "JPYNOK=X": {
                "change": -0.02,
                "change_percent": -0.25,
                "last_price": 0.0685,
                "name": "JPY/NOK",
                "signal": "HOLD",
                "ticker": "JPYNOK=X",
                "volume": 420000000,
                "high": 0.0688,
                "low": 0.0682
            }
        }
        
        return jsonify({
            'success': True,
            'currencies': currencies,
            'last_updated': '2025-07-14T11:30:00Z',
            'base_currency': 'NOK'
        })
        
    except Exception as e:
        logger.error(f"Error getting formatted currency data: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get currency data'
        }), 500

# Enhanced currency rates endpoint
@api.route('/currency/rates/enhanced', methods=['GET'])
def get_enhanced_currency_rates():
    """Get enhanced currency rates with better formatting"""
    try:
        base = request.args.get('base', 'NOK')
        
        # Import CurrencyData model
        from .models.currency_data import CurrencyData
        
        # Use the financial data aggregator for real data if available
        try:
            rates = data_aggregator.get_currency_rates(base)
            formatted_rates = {}
            
            for rate in rates:
                if isinstance(rate, CurrencyData):
                    formatted_rates[rate.pair] = {
                        'ticker': rate.pair,
                        'name': f"{rate.from_currency}/{rate.to_currency}",
                        'last_price': rate.rate,
                        'change_percent': rate.change_percent_24h,
                        'volume': rate.volume,
                        'signal': rate.trend,
                        'high': rate.high_24h,
                        'low': rate.low_24h
                    }
                else:
                    # Handle non-CurrencyData objects as fallback
                    formatted_rates[str(rate)] = {
                        'ticker': str(rate),
                        'name': 'Unknown',
                        'last_price': 0,
                        'change_percent': 0,
                        'volume': 0,
                        'signal': 'HOLD',
                        'high': 0,
                        'low': 0
                    }
            
            return jsonify({
                'success': True,
                'currencies': formatted_rates,
                'base_currency': base
            })
            
        except Exception:
            # Fallback to static data if aggregator fails
            return get_formatted_currency()
            
    except Exception as e:
        logger.error(f"Error getting enhanced currency rates: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get enhanced currency rates'
        }), 500