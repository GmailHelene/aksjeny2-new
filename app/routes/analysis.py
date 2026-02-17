from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_from_directory, session, make_response, g
from ..extensions import csrf  # imported for @csrf.exempt usage on JSON strategy endpoints
from flask_login import current_user, login_required
from ..utils.access_control import access_required, api_access_required, demo_access, premium_required
from ..models.user import User
from ..models.portfolio import Portfolio, PortfolioStock
from ..extensions import cache, db
from datetime import datetime, timedelta
try:
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover
    pd = None
import logging
import functools
import os
try:  # Safe optional imports for services used in API endpoints
    from ..services.analysis_service import AnalysisService  # type: ignore
except Exception:  # pragma: no cover
    AnalysisService = None  # fallback sentinel
try:
    from ..integrations.finnhub_api import FinnhubAPI  # type: ignore
except Exception:  # pragma: no cover
    FinnhubAPI = None

logger = logging.getLogger(__name__)

# Ensure blueprint is declared (was missing causing BuildError for 'analysis.index')
analysis = Blueprint('analysis', __name__, url_prefix='/analysis')

# Test helper: allow test client to force login without CSRF form (only active when TESTING config True)
@analysis.route('/test-force-login', methods=['POST'])
@csrf.exempt  # test helper
def test_force_login():  # pragma: no cover - only for tests
    from flask import current_app
    if not current_app.config.get('TESTING'):
        return jsonify({'success': False, 'error': 'Not available'}), 403
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    if not email:
        return jsonify({'success': False, 'error': 'Email required'}), 400
    try:
        from ..models.user import User  # lazy import
        from flask_login import login_user
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        login_user(user, remember=False)
        return jsonify({'success': True, 'user_id': user.id})
    except Exception as e:  # pragma: no cover
        return jsonify({'success': False, 'error': str(e)}), 500

def strategy_rate_limit(max_requests=30, window=60, methods=None, bucket_name=None):
    """Rate limit decorator with optional Redis backend (ZSET sliding window).
    - If REDIS_URL configured and redis import succeeds, uses Redis key per user+bucket.
    - Fallback: in-memory per-process deque (original behavior).
    - No sleeping: returns 429 immediately when limit exceeded.
    """
    from collections import defaultdict, deque
    # Lazy init shared memory store
    store = getattr(strategy_rate_limit, '_store', None)
    if store is None:
        store = defaultdict(lambda: deque())
        setattr(strategy_rate_limit, '_store', store)
    redis_client = getattr(strategy_rate_limit, '_redis', None)
    if redis_client is None:
        try:
            import redis  # type: ignore
            redis_url = os.environ.get('REDIS_URL') or current_app.config.get('REDIS_URL')
            if redis_url:
                redis_client = redis.from_url(redis_url)
                redis_client.ping()
                setattr(strategy_rate_limit, '_redis', redis_client)
            else:
                setattr(strategy_rate_limit, '_redis', None)
        except Exception:
            setattr(strategy_rate_limit, '_redis', None)
            redis_client = None
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if methods and request.method.upper() not in {m.upper() for m in methods}:
                return fn(*args, **kwargs)
            uid = getattr(current_user, 'id', 'anon')
            bucket = bucket_name or fn.__name__
            now = datetime.utcnow().timestamp()
            cutoff = now - window
            # Redis path
            if redis_client:
                try:
                    key = f"strategy_rl:{bucket}:{uid}"
                    pipe = redis_client.pipeline()
                    pipe.zremrangebyscore(key, 0, cutoff)
                    pipe.zcard(key)
                    results = pipe.execute()
                    current_count = results[1] if len(results) > 1 else 0
                    if current_count >= max_requests:
                        return jsonify({'success': False, 'error': 'Rate limit'}), 429
                    # add current ts
                    redis_client.zadd(key, {str(now): now})
                    redis_client.expire(key, window * 2)
                except Exception:
                    pass  # silently fall back to memory
            # In-memory fallback (or after redis failure)
            if not redis_client:
                dq = store[(bucket, uid)]
                while dq and dq[0] < cutoff:
                    dq.popleft()
                if len(dq) >= max_requests:
                    return jsonify({'success': False, 'error': 'Rate limit'}), 429
                dq.append(now)
            return fn(*args, **kwargs)
        return wrapper
    return decorator

@analysis.route('/ticker_suggestions')
@strategy_rate_limit(max_requests=60, window=60, methods=['GET'], bucket_name='ticker_suggestions')
def ticker_suggestions():
    """Return JSON list of ticker suggestions matching query param q (prefix match)."""
    q = (request.args.get('q') or '').upper().strip()
    if not q:
        return jsonify([])
    universe = [
        'EQNR.OL','DNB.OL','YAR.OL','MOWI.OL','TEL.OL',
        'AAPL','TSLA','MSFT','AMZN','GOOGL','NVDA','META','IBM','ORCL','NFLX','SHOP','AMD','INTC','BA','NIO','PLTR','SNOW','UBER'
    ]
    return jsonify([t for t in universe if t.startswith(q)][:10])

@analysis.before_request
def _analysis_set_correlation_id():
    try:
        import uuid
        from flask import g
        g.correlation_id = uuid.uuid4().hex
    except Exception:
        pass
"""Legacy recommendations routes removed.

The canonical implementation now lives in analysis_clean.recommendations.
This stub exists only to guard accidental imports; it issues a redirect.
"""
@analysis.route('/recommendations')
@analysis.route('/recommendations/<ticker>')
def recommendations(ticker: str = None):  # pragma: no cover - now thin delegate
    """Delegate to canonical implementation in analysis_clean without redirect loop.

    The previous implementation returned a 301 redirect to itself causing a loop.
    We import lazily to avoid circular imports and call the real view function directly.
    """
    try:
        from .analysis_clean import recommendations as clean_recommendations  # type: ignore
        return clean_recommendations(ticker)  # pass through symbol (ticker)
    except Exception as e:  # fallback: show error template
        try:
            logger.error(f"Failed delegating recommendations: {e}")
        except Exception:
            pass
        return render_template('error.html', error='Anbefalinger er midlertidig utilgjengelig.')

# Explicit alias preserving historic endpoint name used across many templates.
@analysis.route('/recommendation', endpoint='recommendation')
@analysis.route('/recommendation/<ticker>', endpoint='recommendation_with_ticker')  # distinct endpoint to avoid collision
def recommendation_alias(ticker: str = None):  # pragma: no cover - legacy alias forwards internally
    # Directly delegate instead of redirect to prevent loops
    return recommendations(ticker)

@analysis.route('/api/sentiment')
@access_required
def api_sentiment():
    """API endpoint for market sentiment analysis (resilient with graceful fallbacks)."""
    try:
        selected_symbol = (request.args.get('symbol') or request.args.get('ticker', '')).strip().upper()
        if not selected_symbol:
            try:
                market_sentiment = AnalysisService.get_market_sentiment_overview() if AnalysisService else {
                    'overall_score': 50,
                    'sentiment_label': 'Nøytral',
                    'error': 'Markedssentiment midlertidig utilgjengelig.',
                    'fallback': True
                }
                return make_response(jsonify(market_sentiment), 200)
            except Exception as e:
                logger.error(f"Error getting market sentiment: {e}")
                return make_response(jsonify({
                    'overall_score': 50,
                    'sentiment_label': 'Nøytral',
                    'error': 'Markedssentiment midlertidig utilgjengelig.',
                    'fallback': True
                }), 200)

        if not selected_symbol.replace('.', '').replace('-', '').isalnum():
            return make_response(jsonify({
                'success': False,
                'error': 'Ugyldig aksjesymbol.'
            }), 400)

        sentiment_data = None
        errors = []

        if AnalysisService:
            try:
                sentiment_data = AnalysisService.get_sentiment_analysis(selected_symbol)
            except Exception as e:
                errors.append(f"AnalysisService error: {e}")

        if not sentiment_data and FinnhubAPI:
            try:
                finnhub_sentiment = FinnhubAPI().get_sentiment(selected_symbol)
                if finnhub_sentiment:
                    sentiment_data = {
                        'overall_score': int((finnhub_sentiment.get('sentiment_score', 0.5) * 100)),
                        'sentiment_label': finnhub_sentiment.get('sentiment_label', 'Nøytral'),
                        'source': 'Finnhub',
                        'last_updated': finnhub_sentiment.get('last_updated')
                    }
            except Exception as e:
                errors.append(f"FinnhubAPI error: {e}")

        if not sentiment_data:
            sentiment_data = {
                'overall_score': 50,
                'sentiment_label': 'Nøytral',
                'error': 'Sentimentdata midlertidig utilgjengelig.',
                'fallback': True
            }
            if errors:
                logger.error(f"Sentiment analysis errors for {selected_symbol}: {', '.join(errors)}")

        return make_response(jsonify(sentiment_data), 200)
    except Exception as e:
        logger.error(f"Error in sentiment API: {e}")
        return make_response(jsonify({
            'success': False,
            'error': 'En feil oppstod under analysen. Vennligst prøv igjen senere.'
        }), 500)

@analysis.route('/sentiment')
@access_required
def sentiment():
    """Render sentiment analysis page (HTML) with resilient fallbacks.

    Query params: symbol or ticker. Always returns 200 with synthetic data if providers fail.
    """
    try:
        # Guarantee correlation_id existence (tests rely on a 32-char hex). If before_request failed, set it now.
        try:
            import uuid
            cid = getattr(g, 'correlation_id', None)
            if not cid or not isinstance(cid, str) or len(cid) != 32:
                g.correlation_id = uuid.uuid4().hex
        except Exception:
            pass
        symbol = (request.args.get('symbol') or request.args.get('ticker') or 'EQNR.OL').strip().upper()
        if not symbol.replace('.', '').replace('-', '').isalnum() or len(symbol) > 20:
            symbol = 'EQNR.OL'

        sentiment_data = None
        errors = []

        try:
            from ..services.analysis_service import AnalysisService as _AS  # type: ignore
        except Exception:
            _AS = None

        if _AS:
            try:
                sentiment_data = _AS.get_sentiment_analysis(symbol)
            except Exception as e:
                errors.append(f"AnalysisService error: {e}")

        if not sentiment_data:
            try:
                from ..integrations.finnhub_api import FinnhubAPI  # optional
                finnhub_sentiment = FinnhubAPI().get_sentiment(symbol)
                if finnhub_sentiment:
                    sentiment_data = {
                        'overall_score': int((finnhub_sentiment.get('sentiment_score', 0.5) * 100)),
                        'sentiment_label': finnhub_sentiment.get('sentiment_label', 'Nøytral'),
                        'source': 'Finnhub',
                        'last_updated': finnhub_sentiment.get('last_updated')
                    }
            except Exception as e:
                errors.append(f"FinnhubAPI error: {e}")

        if not sentiment_data:
            # Deterministic pseudo-random fallback baseline
            base_hash = sum(ord(c) for c in symbol) % 100
            overall = 45 + (base_hash % 11)
            sentiment_label = 'Bullish' if overall > 60 else 'Bearish' if overall < 40 else 'Nøytral'
            # Provide every key referenced in the large sentiment.html template to avoid AttributeError / undefined lookups
            sentiment_data = {
                'overall_score': overall,              # top summary
                'sentiment_label': sentiment_label,     # label
                'news_score': 0,                        # template uses sentiment_data.news_score
                'social_score': 0,                      # early section (get('social_score'))
                'social_sentiment': 0,                  # later section uses attribute style
                'social_mentions': 0,
                'news_count': 0,
                'volume_trend': 'Nøytral',
                'rsi_sentiment': 50 + ((base_hash % 10) - 5),
                'volatility': None,
                'trend': 'stable',
                'confidence': 0.0,
                'last_updated': None,
                'market_sentiment': 0,
                'fear_greed_index': 'N/A',
                'vix': 'N/A',
                'market_trend': 'neutral',
                'history': {
                    'dates': [],
                    'scores': []
                },
                'recent_news': [],
                'key_themes': [],
                'summary': None,
                'indicators': [],
                'recommendation': None,
                'fallback': True
            }

        # Ensure existing sentiment_data (from service or API) also has required keys to prevent template attribute errors
        required_keys = [
            'overall_score','sentiment_label','news_score','social_score','social_sentiment','social_mentions',
            'news_count','volume_trend','volatility','trend','confidence','last_updated','market_sentiment',
            'fear_greed_index','vix','market_trend','history','recent_news','key_themes','summary','indicators',
            'recommendation'
        ]
        for k in required_keys:
            if k not in sentiment_data:
                # Sensible neutral defaults
                sentiment_data[k] = 0 if 'score' in k or k in ('overall_score','confidence','market_sentiment') else [] if k in ('history','recent_news','key_themes','indicators') else None
        # Normalize history structure if present but not dict with dates/scores
        if isinstance(sentiment_data.get('history'), list):
            sentiment_data['history'] = {'dates': [], 'scores': []}

        # Final normalization: avoid None for numeric comparisons in template
        numeric_like = ['overall_score','news_score','social_score','social_sentiment','confidence','market_sentiment']
        for nk in numeric_like:
            if sentiment_data.get(nk) is None:
                sentiment_data[nk] = 0

        # Provide both 'sentiment' and legacy 'sentiment_data' for template compatibility
        return render_template(
            'analysis/sentiment.html',
            symbol=symbol,
            selected_symbol=symbol,
            sentiment=sentiment_data,
            sentiment_data=sentiment_data,  # legacy name used heavily in template
            errors=errors,
            correlation_id=getattr(g, 'correlation_id', None)
        )
    except Exception as e:
        current_app.logger.error(f"Sentiment page error: {e}")
        return render_template(
            'analysis/sentiment.html',
            symbol='EQNR.OL',
            selected_symbol='EQNR.OL',
            sentiment={
                'overall_score': 50,
                'sentiment_label': 'Nøytral',
                'fallback': True,
                'error': 'Midlertidig utilgjengelig'
            },
            sentiment_data={
                'overall_score': 50,
                'sentiment_label': 'Nøytral',
                'fallback': True,
                'error': 'Midlertidig utilgjengelig'
            },
            errors=['Fallback visning'],
            correlation_id=getattr(g, 'correlation_id', None)
        )

@analysis.route('/')
@access_required
def index():
    """Analysis main page - prevent redirect loops"""
    try:
        # Mock market summary data since external service has issues
        market_summary = {
            'market_status': 'Open',
            'trending_up': ['EQNR.OL', 'AAPL', 'TSLA'],
            'trending_down': ['DNB.OL', 'MSFT'],
            'market_sentiment': 'Positiv 📈',
            'fear_greed_index': 68
        }
        
        return render_template('analysis/index.html',
                             page_title="Analyse",
                             market_summary=market_summary,
                             buy_signals=23,
                             sell_signals=8,
                             neutral_signals=15,
                             market_sentiment='Positiv 📈')
    except Exception as e:
        logger.error(f"Error in analysis index: {str(e)}")
        return render_template('error.html',
                             error="Analyse siden er midlertidig utilgjengelig. Prøv igjen senere.")

@analysis.route('/technical', methods=['GET', 'POST'])
@analysis.route('/technical/', methods=['GET', 'POST'])
@analysis.route('/technical/<path:path_symbol>', methods=['GET'])
@analysis.route('/technical/symbol/<path:path_symbol>', methods=['GET'])
@access_required
def technical(path_symbol=None):
    """Advanced Technical analysis page & JSON endpoint with robust fallback.

    Behavior:
    - HTML default: render search prompt if no symbol.
    - ?format=json: returns structured JSON {success, symbol, data, data_source, cache_hit}.
    - Attempts real data (yfinance + pandas) when available; otherwise deterministic synthetic.
    - Caches both real & synthetic results (memory or Redis if configured).
    """
    want_json = request.args.get('format') == 'json'
    try:
        try:
            import pandas as _pandas  # type: ignore
        except Exception:  # pragma: no cover
            _pandas = None
        from time import time as _time
        CACHE_TTL = 180
        use_redis = False
        redis_client = None
        if 'REDIS_URL' in current_app.config or os.getenv('REDIS_URL'):
            try:
                import redis  # type: ignore
                redis_url = current_app.config.get('REDIS_URL') or os.getenv('REDIS_URL')
                redis_client = redis.from_url(redis_url)
                redis_client.ping()
                use_redis = True
            except Exception:
                use_redis = False
        global _TECH_CACHE  # type: ignore
        if '_TECH_CACHE' not in globals():  # type: ignore
            _TECH_CACHE = {}

        from typing import Optional
        def _build_synthetic(symbol: str, stock_info: Optional[dict]) -> dict:
            try:
                from ..services.data_service import FALLBACK_OSLO_DATA, FALLBACK_GLOBAL_DATA  # type: ignore
            except Exception:  # pragma: no cover
                FALLBACK_OSLO_DATA, FALLBACK_GLOBAL_DATA = {}, {}
            ticker_hash = abs(hash(symbol)) % 1000
            if stock_info and isinstance(stock_info, dict):
                company_name = stock_info.get('longName', stock_info.get('shortName', symbol))
                base_price = stock_info.get('regularMarketPrice', stock_info.get('currentPrice', 100 + ticker_hash % 400))
            else:
                if symbol in FALLBACK_OSLO_DATA:
                    data = FALLBACK_OSLO_DATA[symbol]
                    company_name = data.get('name', symbol)
                    base_price = data.get('last_price', 100 + ticker_hash % 400)
                elif symbol in FALLBACK_GLOBAL_DATA:
                    data = FALLBACK_GLOBAL_DATA[symbol]
                    company_name = data.get('name', symbol)
                    base_price = data.get('last_price', 100 + ticker_hash % 400)
                else:
                    company_name = symbol.replace('.OL', ' ASA').replace('.', ' ').title()
                    base_price = (50 + (ticker_hash % 450)) if symbol.endswith('.OL') else (20 + (ticker_hash % 480))
            rsi = 30 + (ticker_hash % 40)
            change_percent = -3.0 + (ticker_hash % 60) / 10.0
            change = base_price * (change_percent / 100)
            volume = 100000 + (ticker_hash % 2000000)
            macd = -1.0 + (ticker_hash % 20) / 10.0
            support = base_price * (0.95 + (ticker_hash % 5) / 100)
            resistance = base_price * (1.01 + (ticker_hash % 5) / 100)
            sma_20 = base_price * (0.98 + (ticker_hash % 4) / 100)
            sma_50 = base_price * (0.96 + (ticker_hash % 8) / 100)
            if rsi < 35 and macd > 0:
                signal, strength, reason = 'BUY', 'Strong', f'RSI oversold ({rsi:.1f}) with positive MACD'
            elif rsi > 65 and macd < 0:
                signal, strength, reason = 'SELL', 'Strong', f'RSI overbought ({rsi:.1f}) with negative MACD'
            elif base_price > sma_20 and base_price > sma_50:
                signal, strength, reason = 'BUY', 'Medium', 'Price above moving averages'
            elif base_price < sma_20 and base_price < sma_50:
                signal, strength, reason = 'SELL', 'Medium', 'Price below moving averages'
            else:
                signal, strength, reason = 'HOLD', 'Medium', 'Mixed technical signals'
            return {
                'symbol': symbol,
                'name': company_name,
                'last_price': round(base_price, 2),
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'volume': volume,
                'rsi': round(rsi, 1),
                'macd': round(macd, 3),
                'macd_signal': round(macd * 0.8, 3),
                'resistance': round(resistance, 2),
                'support': round(support, 2),
                'sma_20': round(sma_20, 2),
                'sma_50': round(sma_50, 2),
                'signal': signal,
                'signal_strength': strength,
                'signal_reason': reason,
                'is_real_data': False,
                'data_source': 'SYNTHETIC'
            }

        # Acquire raw symbol from query/form/path
        raw_symbol = None
        if request.args.get('symbol') or request.args.get('ticker'):
            raw_symbol = request.args.get('symbol') or request.args.get('ticker')
        elif request.form.get('symbol') or request.form.get('ticker'):
            raw_symbol = request.form.get('symbol') or request.form.get('ticker')
        elif path_symbol:
            raw_symbol = path_symbol
        if isinstance(raw_symbol, str):
            raw_symbol = raw_symbol.strip().strip('/')

        if not raw_symbol:
            if want_json:
                return jsonify({'success': False, 'symbol': '', 'error': 'symbol parameter required', 'data': {}})
            # Show popular stocks (basic overview) if no symbol
            popular_stocks = []
            try:
                from ..services.data_service import DataService  # type: ignore
                for ticker in ['EQNR.OL','DNB.OL','YAR.OL','MOWI.OL','TEL.OL','AAPL','TSLA','MSFT','AMZN','GOOGL']:
                    try:
                        info = DataService.get_stock_info(ticker)
                        if info:
                            price = info.get('regularMarketPrice', info.get('currentPrice', 0))
                            prev = info.get('previousClose', price)
                            cp = ((price - prev)/prev*100) if prev else 0
                            popular_stocks.append({'symbol': ticker, 'price': price, 'change_percent': round(cp,2)})
                    except Exception:
                        continue
            except Exception:
                pass
            return render_template('analysis/technical.html', symbol='', technical_data=None, popular_stocks=popular_stocks, show_search_prompt=True, show_analysis=False)

        from ..utils.symbol_utils import sanitize_symbol, COMMON_DEFAULT
        symbol, valid = sanitize_symbol(raw_symbol)
        if valid and '.' not in symbol:
            try:
                from ..services.data_service import FALLBACK_OSLO_DATA  # type: ignore
                if symbol + '.OL' in FALLBACK_OSLO_DATA:
                    symbol = symbol + '.OL'
            except Exception:
                pass
        if not valid:
            if want_json:
                return jsonify({'success': False, 'symbol': symbol, 'error': 'invalid symbol', 'data': {}})
            return render_template('analysis/technical.html', symbol=symbol or COMMON_DEFAULT, technical_data=None, show_analysis=False, error_message='Ugyldig symbol. Bruk kun A-Z, 0-9, punktum eller bindestrek (maks 15 tegn).')

        # Cache lookup
        if use_redis and redis_client:
            try:
                cached_raw = redis_client.get(f'tech:{symbol}')
                if cached_raw:
                    import json as _json
                    payload = _json.loads(cached_raw)
                    if want_json:
                        return jsonify({'success': True, 'symbol': symbol, 'data': payload, 'data_source': payload.get('data_source','CACHE'), 'cache_hit': True})
                    return render_template('analysis/technical.html', symbol=symbol, technical_data=payload, show_analysis=True, from_cache=True, cache_backend='redis')
            except Exception:
                pass
        else:
            cache_entry = _TECH_CACHE.get(symbol) if '_TECH_CACHE' in globals() else None  # type: ignore
            if cache_entry:
                ts_cached, payload = cache_entry.get('ts'), cache_entry.get('payload')
                if ts_cached and (_time() - ts_cached) < CACHE_TTL and payload:
                    if want_json:
                        return jsonify({'success': True, 'symbol': symbol, 'data': payload, 'data_source': payload.get('data_source','CACHE'), 'cache_hit': True})
                    return render_template('analysis/technical.html', symbol=symbol, technical_data=payload, show_analysis=True, from_cache=True, cache_backend='memory')

        # Attempt real data
        technical_data = None
        data_source = 'SYNTHETIC'
        try:
            if _pandas is not None:
                from ..services.data_service import DataService  # type: ignore
                from ..services.technical_analysis import calculate_comprehensive_technical_data  # type: ignore
                import yfinance as yf  # type: ignore
                stock_info = None
                try:
                    stock_info = DataService.get_stock_info(symbol)
                except Exception as e:
                    logger.warning(f'DataService failed for {symbol}: {e}')
                historical_data = None
                try:
                    ticker = yf.Ticker(symbol)
                    historical_data = ticker.history(period='6mo', interval='1d')
                    if historical_data is None or historical_data.empty:
                        historical_data = None
                except Exception as e:
                    logger.warning(f'yfinance history fail {symbol}: {e}')
                    historical_data = None
                if historical_data is not None:
                    try:
                        indicators = calculate_comprehensive_technical_data(historical_data)
                        if stock_info and isinstance(stock_info, dict):
                            current_price = stock_info.get('regularMarketPrice', stock_info.get('currentPrice', 0))
                            previous_close = stock_info.get('previousClose', current_price)
                            company_name = stock_info.get('longName', stock_info.get('shortName', symbol))
                        else:
                            current_price = float(historical_data['Close'].iloc[-1])
                            previous_close = float(historical_data['Close'].iloc[-2]) if len(historical_data) > 1 else current_price
                            company_name = symbol.replace('.OL',' ASA').replace('.',' ').title()
                        change = current_price - previous_close
                        change_percent = (change / previous_close * 100) if previous_close else 0
                        technical_data = {
                            'symbol': symbol,
                            'name': company_name,
                            'last_price': round(current_price,2),
                            'change': round(change,2),
                            'change_percent': round(change_percent,2),
                            'volume': int(historical_data['Volume'].iloc[-1]) if 'Volume' in historical_data else 0,
                            'rsi': round(indicators.get('rsi',50),1),
                            'macd': round(indicators.get('macd',0),3),
                            'macd_signal': round(indicators.get('macd_signal',0),3),
                            'resistance': round(indicators.get('bollinger_upper', current_price*1.02),2),
                            'support': round(indicators.get('bollinger_lower', current_price*0.98),2),
                            'sma_20': round(indicators.get('sma_20', current_price),2),
                            'sma_50': round(indicators.get('sma_50', current_price),2),
                            'signal': indicators.get('signal','HOLD'),
                            'signal_strength': indicators.get('signal_strength','Medium'),
                            'signal_reason': indicators.get('signal_reason','Technical analysis complete'),
                            'is_real_data': True,
                            'data_source': 'REAL'
                        }
                        data_source = 'REAL'
                    except Exception as real_err:
                        logger.error(f'Real technical calc failed {symbol}: {real_err}')
        except Exception as outer_real:
            logger.error(f'Real data path error {symbol}: {outer_real}')

        if technical_data is None:
            # Build synthetic fallback
            try:
                stock_info_for_syn = None
                try:
                    from ..services.data_service import DataService  # type: ignore
                    stock_info_for_syn = DataService.get_stock_info(symbol)
                except Exception:
                    pass
                technical_data = _build_synthetic(symbol, stock_info_for_syn)
                data_source = technical_data.get('data_source','SYNTHETIC')
            except Exception as syn_fail:
                logger.error(f'Synthetic build failed {symbol}: {syn_fail}')
                if want_json:
                    return jsonify({'success': False, 'symbol': symbol, 'error': 'unavailable', 'data': {}})
                return render_template('analysis/technical.html', symbol=symbol, technical_data=None, show_analysis=False, error_message=f'Teknisk analyse for {symbol} er ikke tilgjengelig.')

        # Cache result
        try:
            if use_redis and redis_client:
                import json as _json
                redis_client.setex(f'tech:{symbol}', CACHE_TTL, _json.dumps(technical_data))
            else:
                _TECH_CACHE[symbol] = {'ts': _time(), 'payload': technical_data}
        except Exception:
            pass

        if want_json:
            return jsonify({'success': True, 'symbol': symbol, 'data': technical_data, 'data_source': data_source, 'cache_hit': False})
        return render_template('analysis/technical.html', symbol=symbol, technical_data=technical_data, show_analysis=True, is_real_data=technical_data.get('is_real_data', False))
    except Exception as e:
        logger.error(f'Error in technical analysis route: {e}')
        if want_json:
            return jsonify({'success': False, 'symbol': request.args.get('symbol',''), 'error': 'service unavailable', 'data': {}})
        return render_template('analysis/technical.html', symbol=request.args.get('symbol',''), show_analysis=bool(request.args.get('symbol')), error='Teknisk analyse er midlertidig utilgjengelig')

def _generate_buffett_metrics(ticker, stock_info=None):
    """Generate Warren Buffett style metrics for a stock"""
    import random
    from datetime import datetime, timedelta
    
    # Create deterministic but varied data based on ticker
    ticker_hash = sum(ord(c) for c in ticker)
    random.seed(ticker_hash)
    
    # Base metrics on real data if available
    if stock_info and isinstance(stock_info, dict):
        price = stock_info.get('regularMarketPrice', stock_info.get('currentPrice', 50 + (ticker_hash % 450)))
        pe_ratio = stock_info.get('forwardPE', 15 + (ticker_hash % 25))
        dividend_yield = stock_info.get('dividendYield', 2 + (ticker_hash % 4))
    else:
        # Generate realistic fallback data
        price = 50 + (ticker_hash % 450) if ticker.endswith('.OL') else 20 + (ticker_hash % 280)
        pe_ratio = 15 + (ticker_hash % 25)
        dividend_yield = 2 + (ticker_hash % 4)
    
    # Calculate Buffett-style metrics
    metrics = {
        'price': round(price, 2),
        'pe_ratio': round(pe_ratio, 2),
        'dividend_yield': round(dividend_yield, 2),
        'profit_margin': round(8 + (ticker_hash % 22), 2),
        'debt_to_equity': round(0.5 + (ticker_hash % 15) / 10, 2),
        'current_ratio': round(1.2 + (ticker_hash % 28) / 10, 2),
        'roe': round(12 + (ticker_hash % 18), 2),
        'market_position': random.choice(['Strong', 'Medium', 'Growing']),
        'competitive_advantage': random.choice(['High', 'Medium', 'Developing']),
        'management_quality': random.choice(['Excellent', 'Good', 'Fair']),
    }
    
    # Historical performance
    metrics['historical_performance'] = []
    base_year = datetime.now().year - 5
    base_revenue = 1000 + (ticker_hash % 9000)
    base_profit = base_revenue * (0.05 + (ticker_hash % 15) / 100)
    
    for i in range(5):
        year_data = {
            'year': base_year + i,
            'revenue': round(base_revenue * (1 + (0.05 * i + (ticker_hash % 10) / 100)), 1),
            'profit': round(base_profit * (1 + (0.07 * i + (ticker_hash % 8) / 100)), 1),
            'margin': round(8 + (ticker_hash % 12) + (i * 0.5), 1)
        }
        metrics['historical_performance'].append(year_data)
    
    return metrics

def _generate_buffett_recommendation(metrics):
    """Generate a Buffett-style investment recommendation"""
    # Analyze metrics using Buffett's principles
    score = 0
    reasons = []
    
    # PE ratio analysis
    if metrics['pe_ratio'] < 15:
        score += 20
        reasons.append("Fornuftig verdivurdering med P/E under 15")
    elif metrics['pe_ratio'] < 20:
        score += 10
        reasons.append("Akseptabel P/E-verdi under 20")
    
    # Dividend analysis
    if metrics['dividend_yield'] > 3:
        score += 15
        reasons.append("God dividendeavkastning over 3%")
    elif metrics['dividend_yield'] > 2:
        score += 10
        reasons.append("Akseptabel dividendeavkastning over 2%")
    
    # Debt analysis
    if metrics['debt_to_equity'] < 0.5:
        score += 20
        reasons.append("Konservativ gjeldsgrad under 0.5")
    elif metrics['debt_to_equity'] < 1:
        score += 10
        reasons.append("Håndterbar gjeldsgrad under 1.0")
    
    # Profitability
    if metrics['roe'] > 15:
        score += 20
        reasons.append("Sterk egenkapitalavkastning over 15%")
    elif metrics['roe'] > 10:
        score += 10
        reasons.append("God egenkapitalavkastning over 10%")
    
    # Market position
    if metrics['market_position'] == 'Strong':
        score += 15
        reasons.append("Sterk markedsposisjon")
    elif metrics['market_position'] == 'Medium':
        score += 10
        reasons.append("Etablert markedsposisjon")
    
    # Generate recommendation
    if score >= 75:
        recommendation = {
            'rating': 'strong_buy',
            'action': 'Kjøp',
            'summary': 'Sterkt kjøp - Oppfyller Buffetts investeringskriterier',
            'confidence': 0.9
        }
    elif score >= 60:
        recommendation = {
            'rating': 'buy',
            'action': 'Kjøp',
            'summary': 'Kjøp - God match med Buffetts prinsipper',
            'confidence': 0.75
        }
    elif score >= 40:
        recommendation = {
            'rating': 'hold',
            'action': 'Hold',
            'summary': 'Hold - Noen positive faktorer, men ikke optimal',
            'confidence': 0.6
        }
    else:
        recommendation = {
            'rating': 'pass',
            'action': 'Avvent',
            'summary': 'Ikke kjøp - Oppfyller ikke Buffetts kriterier',
            'confidence': 0.8
        }
    
    recommendation['score'] = score
    recommendation['reasons'] = reasons
    return recommendation

@analysis.route('/warren-buffett', methods=['GET', 'POST'])
@analysis.route('/warren_buffett', methods=['GET', 'POST'])  # Backwards compatibility
@access_required
def warren_buffett():
    """Unified Warren Buffett analysis (enhanced version).

    Refactored to share logic and reduce duplication with simplified variant
    in analysis_clean. Provides deterministic demo data when real analysis
    services (DataService/BuffettAnalyzer) fail, while guaranteeing all
    template fields are populated to avoid runtime Jinja errors.
    """
    from datetime import datetime

    def _stock_lists():
        oslo = {
            'EQNR.OL': {'name': 'Equinor ASA', 'sector': 'Energi'},
            'DNB.OL': {'name': 'DNB Bank ASA', 'sector': 'Finans'},
            'MOWI.OL': {'name': 'Mowi ASA', 'sector': 'Sjømat'},
            'TEL.OL': {'name': 'Telenor ASA', 'sector': 'Telekom'},
            'NHY.OL': {'name': 'Norsk Hydro ASA', 'sector': 'Materialer'},
            'YAR.OL': {'name': 'Yara International ASA', 'sector': 'Materialer'},
            'ORK.OL': {'name': 'Orkla ASA', 'sector': 'Forbruksvarer'}
        }
        global_map = {
            'AAPL': {'name': 'Apple Inc.', 'sector': 'Teknologi'},
            'MSFT': {'name': 'Microsoft Corporation', 'sector': 'Teknologi'},
            'GOOGL': {'name': 'Alphabet Inc.', 'sector': 'Teknologi'},
            'BRK-B': {'name': 'Berkshire Hathaway', 'sector': 'Finans'},
            'JNJ': {'name': 'Johnson & Johnson', 'sector': 'Helse'},
            'PG': {'name': 'Procter & Gamble', 'sector': 'Forbruksvarer'},
            'KO': {'name': 'The Coca-Cola Company', 'sector': 'Forbruksvarer'}
        }
        return oslo, global_map

    def _generate_demo_analysis(ticker: str):
        th = sum(ord(c) for c in ticker)
        price = 100 + (th % 300)
        pe_ratio = 10 + (th % 25)
        dividend_yield = (th % 8) / 2.0
        profit_margin = 5 + (th % 20)
        debt_to_equity = (th % 15) / 10.0
        current_ratio = 1.0 + (th % 20) / 10.0
        roe = 8 + (th % 15)
        score = 50
        if pe_ratio < 20: score += 10
        if dividend_yield > 2: score += 10
        if profit_margin > 15: score += 10
        if debt_to_equity < 0.5: score += 10
        if current_ratio > 1.5: score += 5
        if roe > 15: score += 5
        if score >= 85:
            action = 'KJØP'; reasons = ['Utmerket finansiell helse', 'Sterke konkurransefortrinn', 'Attraktiv verdsettelse']; risk_level='Lav'
        elif score >= 70:
            action = 'HOLD'; reasons = ['Solid selskap', 'Moderat verdsettelse', 'Stabil inntjening']; risk_level='Medium'
        else:
            action = 'VURDER'; reasons = ['Høy risiko', 'Usikker lønnsomhet', 'Må undersøkes nærmere']; risk_level='Høy'
        action_map = {'KJØP': 'Strong Buy','HOLD':'Hold','VURDER':'Watch'}
        recommendation_string = action_map.get(action, action)
        management_snapshot = {
            'capital_allocation': 70 + (score % 21),
            'shareholder_friendly': 65 + (score % 26),
            'assessment': 'Sterk og disiplinert kapitalallokering' if score >= 70 else 'Potensial for forbedring'
        }
        fair_value = round(price * (0.85 if score < 60 else 0.95 if score < 80 else 1.05), 2)
        confidence = min(95, 60 + int(score / 4))
        quality_score = 'Excellent' if score >= 85 else 'Good' if score >= 70 else 'Average'
        return {
            'ticker': ticker,
            'company_name': ticker.replace('.OL', ' ASA') if '.OL' in ticker else f'{ticker} Inc.',
            'metrics': {
                'price': price,
                'pe_ratio': pe_ratio,
                'dividend_yield': dividend_yield,
                'profit_margin': profit_margin,
                'debt_to_equity': debt_to_equity,
                'current_ratio': current_ratio,
                'roe': roe
            },
            'buffett_score': score,
            'recommendation': recommendation_string,
            'recommendation_obj': {
                'action': recommendation_string,
                'score': score,
                'risk_level': risk_level,
                'reasons': reasons
            },
            'recommendation_details': {
                'score': score,
                'action': action,
                'reasons': reasons,
                'risk_level': risk_level
            },
            'fair_value': fair_value,
            'confidence': confidence,
            'management': management_snapshot,
            'quality_score': quality_score,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'is_fallback': True
        }

    # Parse ticker
    ticker = (request.form.get('ticker') if request.method == 'POST' else request.args.get('ticker', '')).strip().upper()
    oslo_stocks, global_stocks = _stock_lists()
    analysis_data = None

    if ticker:
        logger.info(f"Buffett analysis requested for {ticker}")
        if not ticker.replace('.', '').replace('-', '').replace('_', '').isalnum():
            flash('Ugyldig aksjesymbol. Prøv med f.eks. EQNR.OL eller AAPL.', 'warning')
        else:
            # Try real analysis first if services available
            real_ok = False
            if 'BuffettAnalyzer' in globals() and BuffettAnalyzer and DataService:
                try:
                    stock_info = DataService.get_stock_info(ticker)
                    real_analysis = BuffettAnalyzer.analyze_stock(ticker)
                    if real_analysis:
                        # Normalize to template format
                        analysis_data = {
                            'ticker': ticker,
                            'company_name': stock_info.get('longName', ticker) if stock_info else ticker,
                            'metrics': real_analysis.get('metrics', {}),
                            'buffett_score': real_analysis.get('score', 0),
                            'recommendation': real_analysis.get('recommendation', 'Hold'),
                            'recommendation_obj': real_analysis.get('recommendation_obj', {}),
                            'recommendation_details': real_analysis.get('recommendation_details', {}),
                            'fair_value': real_analysis.get('fair_value'),
                            'confidence': real_analysis.get('confidence', 60),
                            'management': real_analysis.get('management', {}),
                            'quality_score': real_analysis.get('quality_score', 'Average'),
                            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
                            'is_fallback': False
                        }
                        real_ok = True
                        logger.info(f"Real Buffett analysis generated for {ticker}")
                except Exception as real_err:
                    logger.warning(f"Real Buffett analysis failed for {ticker}: {real_err}")
            if not real_ok:
                analysis_data = _generate_demo_analysis(ticker)

    return render_template(
        'analysis/warren_buffett.html',
        analysis=analysis_data,
        error=None,
        oslo_stocks=oslo_stocks,
        global_stocks=global_stocks,
        ticker=ticker or '',
        title="Warren Buffett Analyse",
        description="Analyser aksjer med Warren Buffetts investeringsprinsipper"
    )


# AJAX/JSON endpoint for dynamic Buffett analysis
@analysis.route('/api/warren-buffett', methods=['GET'])
@demo_access  # Changed from @access_required to allow demo access
def warren_buffett_api():
    """Warren Buffett API with robust error handling"""
    try:
        ticker = request.args.get('ticker', '').strip().upper()
        if not ticker or not ticker.replace('.', '').replace('-', '').replace('_', '').isalnum():
            return jsonify({'success': False, 'error': 'Ugyldig aksjesymbol.'}), 400
        
        logger.info(f"Warren Buffett API request for ticker: {ticker}")
        
        # Try to get real stock data
        stock_info = None
        if DataService:
            try:
                stock_info = DataService.get_stock_info(ticker)
                logger.info(f"Got stock data for {ticker}")
            except Exception as data_error:
                logger.warning(f"DataService failed for {ticker}: {data_error}")
                stock_info = None
        
        # Try to get real analysis
        real_analysis = None
        if BuffettAnalyzer:
            try:
                real_analysis = BuffettAnalyzer.analyze_stock(ticker)
                logger.info(f"Got Buffett analysis for {ticker}")
            except Exception as analysis_error:
                logger.warning(f"BuffettAnalyzer failed for {ticker}: {analysis_error}")
                real_analysis = None
        
        # Generate fallback metrics if needed
        try:
            metrics = _generate_buffett_metrics(ticker, stock_info)
            recommendation = _generate_buffett_recommendation(metrics)
        except Exception as fallback_error:
            logger.error(f"Error generating fallback metrics: {fallback_error}")
            # Ultra-simple fallback
            ticker_hash = sum(ord(c) for c in ticker)
            metrics = {
                'price': 100 + (ticker_hash % 200),
                'pe_ratio': 15 + (ticker_hash % 10),
                'dividend_yield': 2 + (ticker_hash % 3),
                'profit_margin': 10 + (ticker_hash % 15),
                'debt_to_equity': 0.5 + (ticker_hash % 10) / 10,
                'current_ratio': 1.5 + (ticker_hash % 10) / 10,
                'roe': 12 + (ticker_hash % 8),
                'market_position': 'Good',
                'competitive_advantage': 'Medium',
                'management_quality': 'Good'
            }
            recommendation = {
                'score': 65,
                'action': 'HOLD',
                'reasons': ['Fallback analysis - basert på generelle prinsipper'],
                'risk_level': 'Medium'
            }
        
        # Build response data
        analysis_data = real_analysis if real_analysis else {
            'ticker': ticker,
            'company_name': stock_info.get('longName', stock_info.get('shortName', ticker.replace('.OL', ' ASA'))) if stock_info else ticker,
            'metrics': metrics,
            'buffett_score': recommendation['score'],
            'recommendation': recommendation,
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'is_fallback': not bool(real_analysis)
        }
        
        logger.info(f"Successfully generated Buffett analysis for {ticker}")
        return jsonify({'success': True, 'analysis': analysis_data})
        
    except Exception as e:
        logger.error(f"Critical error in Warren Buffett API for ticker {ticker}: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': 'En feil oppstod under analysen. Prøv igjen senere.'}), 500
@analysis.route('/market-overview')
@analysis.route('/market_overview')
@access_required
def market_overview():
    """Market overview page with REAL data from DataService - Performance Optimized"""
    try:
        logger.info("🔄 Loading market overview with OPTIMIZED data loading")
        # Ensure DataService is imported in this scope (threaded fetch needs it)
        try:
            from ..services.data_service import DataService  # type: ignore
        except Exception as imp_err:
            logger.warning(f"Could not import DataService in market_overview: {imp_err}")
        
        # Initialize empty data containers
        oslo_data = {}
        global_data = {}
        crypto_data = {}
        currency_data = {}
        errors = []
        
        # Try to get data with timeout protection (cross-platform)
        try:
            import threading
            import time
            
            data_results = {'oslo': {}, 'global': {}, 'crypto': {}, 'currency': {}}
            
            def fetch_data_thread():
                try:
                    if DataService:
                        data_results['oslo'] = DataService.get_oslo_bors_overview() or {}
                        data_results['global'] = DataService.get_global_stocks_overview() or {}
                        data_results['crypto'] = DataService.get_crypto_overview() or {}
                        data_results['currency'] = DataService.get_currency_overview() or {}
                except Exception as e:
                    logger.warning(f"DataService error in thread: {e}")
            
            # Start data fetching thread with 5-second timeout
            data_thread = threading.Thread(target=fetch_data_thread)
            data_thread.daemon = True
            data_thread.start()
            data_thread.join(timeout=5.0)
            
            if data_thread.is_alive():
                logger.warning("⚠️ DataService timeout after 5 seconds - returning partial/empty real data (no synthetic fallback)")
                errors.append("Tidsavbrudd mot dataservice – viser det som er tilgjengelig.")
            
            oslo_data = data_results['oslo']
            global_data = data_results['global']
            crypto_data = data_results['crypto']
            currency_data = data_results['currency']
                
        except Exception as data_error:
            logger.warning(f"⚠️ DataService feil ({data_error}) – ingen fallback brukes, viser tomme seksjoner")
            errors.append("Kunne ikke laste markedsdata nå – prøv å oppdatere siden om litt.")
        
        logger.info(f"✅ Market data attempt - Oslo: {len(oslo_data)}, Global: {len(global_data)}, Crypto: {len(crypto_data)}, FX: {len(currency_data)}")
        
        # Ny policy: VIS både ekte og simulert data, men merk simulert tydelig.
        # Identifiser real vs simulert (guaranteed) uten å skjule simulert.
        def _split_real_and_sim(dataset):
            real = {}
            simulated = {}
            for k, v in dataset.items():
                if v.get('source') == 'GUARANTEED DATA':
                    simulated[k] = v
                else:
                    real[k] = v
            return real, simulated

        oslo_real, oslo_simulated = _split_real_and_sim(oslo_data)
        global_real, global_simulated = _split_real_and_sim(global_data)

        # Informative meldinger hvis kun simulert data finnes
        if oslo_simulated and not oslo_real:
            errors.append("Viser simulert Oslo Børs data (kun fallback tilgjengelig nå).")
        if global_simulated and not global_real:
            errors.append("Viser simulert global aksjedata (kun fallback tilgjengelig nå).")

        # Slå sammen igjen men behold sorteringsorden (real først, deretter simulert)
        def _merge_with_flag(real_dict, sim_dict):
            merged = {}
            # Real data først
            for k, v in real_dict.items():
                v = dict(v)
                v['is_simulated'] = False
                merged[k] = v
            # Simulert data etterpå
            for k, v in sim_dict.items():
                v = dict(v)
                v['is_simulated'] = True
                merged[k] = v
            return merged

        oslo_data = _merge_with_flag(oslo_real, oslo_simulated)
        global_data = _merge_with_flag(global_real, global_simulated)

        # Fast calculation of market summaries based only on real data
        oslo_avg = (sum(d.get('last_price', 0) for d in oslo_data.values()) / len(oslo_data)) if oslo_data else None
        global_avg = (sum(d.get('last_price', 0) for d in global_data.values()) / len(global_data)) if global_data else None
        
        market_summaries = {
            'oslo': {
                'index_value': round(oslo_avg, 2) if oslo_avg is not None else None,
                'change': round(sum(d.get('change', 0) for d in oslo_data.values()), 2) if oslo_data else None,
                'change_percent': round(sum(d.get('change_percent', 0) for d in oslo_data.values()) / len(oslo_data), 2) if oslo_data else None
            },
            'global_market': {
                'index_value': round(global_avg, 2) if global_avg is not None else None,
                'change': round(sum(d.get('change', 0) for d in global_data.values()), 2) if global_data else None, 
                'change_percent': round(sum(d.get('change_percent', 0) for d in global_data.values()) / len(global_data), 2) if global_data else None
            },
            'crypto': {
                'index_value': crypto_data.get('BTC-USD', {}).get('last_price') if crypto_data.get('BTC-USD') else None,
                'change': crypto_data.get('BTC-USD', {}).get('change') if crypto_data.get('BTC-USD') else None,
                'change_percent': crypto_data.get('BTC-USD', {}).get('change_percent') if crypto_data.get('BTC-USD') else None
            },
            'currency': {
                'usd_nok': currency_data.get('USD-NOK', {}).get('rate') if currency_data.get('USD-NOK') else None,
                'usd_nok_change': currency_data.get('USD-NOK', {}).get('change_percent') if currency_data.get('USD-NOK') else None
            }
        }
        
        # Fast market summary
        market_summary = {
            'oslo_stocks_count': len(oslo_data),
            'oslo_real_count': len(oslo_real),
            'oslo_simulated_count': len(oslo_simulated),
            'global_stocks_count': len(global_data),
            'global_real_count': len(global_real),
            'global_simulated_count': len(global_simulated),
            'crypto_count': len(crypto_data),
            'currency_count': len(currency_data)
        }
        
        return render_template('analysis/market_overview.html',
                             oslo_stocks=oslo_data,
                             global_stocks=global_data,
                             crypto_data=crypto_data,
                             currency=currency_data,
                             currency_data=currency_data,
                             market_summaries=market_summaries,
                             market_summary=market_summary,
                             errors=errors if errors else None,
                             has_simulated_oslo=bool(oslo_simulated),
                             has_simulated_global=bool(global_simulated))
                             
    except Exception as e:
        logger.error(f"Critical error in market overview: {e}", exc_info=True)
        return render_template('error.html',
                             error="Markedsoversikt er midlertidig utilgjengelig. Prøv igjen senere.")

def _generate_sentiment_indicators(symbol):
    """Return REAL (beregnede) tekniske indikatorer når mulig.

    Autentisitets-regel: Ingen pseudo-random generering i EKTE_ONLY modus for innloggede.
    Hvis beregning/innhenting feiler returneres tom liste og en meta-warning kan legges på stedet der funksjonen brukes.
    """
    from flask import current_app
    indicators = []
    warnings = []
    try:
        # Forsøk å gjenbruke eksisterende tekniske tjenester
        # Preferert rekkefølge: advanced_technical_service -> technical_analysis -> safe_yfinance
        try:
            from app.services.advanced_technical_service import get_indicator_set as adv_get
        except Exception:
            adv_get = None
        try:
            from app.services.technical_analysis import TechnicalAnalysisService as BasicTA
        except Exception:
            BasicTA = None
        try:
            from app.services.safe_yfinance import SafeYFinance
        except Exception:
            SafeYFinance = None

        data_points = {}
        # MACD, RSI, SMA beregnes hvis mulig
        if adv_get:
            try:
                adv = adv_get(symbol, indicators=["rsi", "macd", "sma50", "sma200"], max_points=200)
                data_points.update(adv or {})
            except Exception as e:
                warnings.append(f"advanced_ta_failed: {e}")
        elif BasicTA:
            try:
                ta = BasicTA(symbol)
                rsi_v = ta.calculate_rsi(period=14)
                macd_vals = ta.calculate_macd()
                sma50 = ta.calculate_sma(50)
                sma200 = ta.calculate_sma(200)
                data_points.update({
                    'rsi': rsi_v.get('value') if isinstance(rsi_v, dict) else rsi_v,
                    'macd': macd_vals.get('macd') if isinstance(macd_vals, dict) else macd_vals,
                    'macd_signal': macd_vals.get('signal') if isinstance(macd_vals, dict) else None,
                    'sma50': sma50,
                    'sma200': sma200
                })
            except Exception as e:
                warnings.append(f"basic_ta_failed: {e}")

        # Hent volum / pris historikk for momentum proxy hvis mangler
        if SafeYFinance and ('rsi' not in data_points or 'sma50' not in data_points):
            try:
                yf_client = SafeYFinance()
                hist = yf_client.get_history(symbol, period='6mo', interval='1d') or []
                if hist:
                    closes = [row['close'] for row in hist if 'close' in row]
                    if len(closes) >= 2:
                        momentum = (closes[-1] - closes[-2]) / closes[-2] if closes[-2] else 0
                        data_points.setdefault('momentum', momentum)
            except Exception as e:
                warnings.append(f"history_fetch_failed: {e}")

        # Konverter til visningsstruktur (bare reelle tall beholdes)
        mapping = [
            ('RSI (14)', 'rsi'),
            ('MACD', 'macd'),
            ('MACD Signal', 'macd_signal'),
            ('SMA 50', 'sma50'),
            ('SMA 200', 'sma200'),
            ('Momentum (1d)', 'momentum')
        ]
        for label, key in mapping:
            val = data_points.get(key)
            if isinstance(val, (int, float)) and val is not None:
                indicators.append({'name': label, 'value': val})

    except Exception as e:  # Absolutt fallback
        warnings.append(f"indicator_generation_failed: {e}")

    # I tråd med EKTE_ONLY: ikke generer tall hvis tomt.
    if not indicators:
        if current_app and current_app.config.get('EKTE_ONLY'):
            # Returner tomt; stedet i kallet kan bruke warnings
            return []
    return indicators

def _generate_sentiment_recommendation(symbol):
    """Generate a sentiment-based recommendation"""
    from flask import current_app
    # I EKTE_ONLY skal vi ikke konstruere pseudoanalyse uten ekte kilde.
    if current_app and current_app.config.get('EKTE_ONLY'):
        return {
            'type': None,
            'action': None,
            'reasoning': None,
            'confidence': None,
            'warning': 'Ingen ekte anbefalingskilde tilgjengelig enda'
        }
    # Behold eksisterende (legacy) generering for ikke-EKTE modus hvis ønsket senere
    return {
        'type': None,
        'action': None,
        'reasoning': None,
        'confidence': None
    }

def _generate_news_articles(symbol):
    """Returner tom liste i EKTE_ONLY – pseudoartikler ikke tillatt.

    Legacy (ikke-EKTE) generering er fjernet for å unngå utilsiktet bruk.
    Ekte nyheter skal hentes via news_service aggregator.
    """
    from flask import current_app
    if current_app and current_app.config.get('EKTE_ONLY'):
        return []
    return []

def _generate_sentiment_history(symbol):
    """Generate historical sentiment data.
    EKTE_ONLY: Do not fabricate synthetic sentiment history; return empty.
    Non-EKTE path retains legacy deterministic pseudo generation (if ever used).
    """
    from flask import current_app
    if current_app and current_app.config.get('EKTE_ONLY'):
        return {'dates': [], 'scores': []}
    import random
    from datetime import datetime, timedelta
    symbol_hash = sum(ord(c) for c in symbol)
    random.seed(symbol_hash)
    trend_direction = 1 if symbol_hash % 2 == 0 else -1
    dates = []
    scores = []
    now = datetime.now()
    base_score = (symbol_hash % 40) + 30
    for i in range(30, -1, -1):
        date = now - timedelta(days=i)
        dates.append(date.strftime('%Y-%m-%d'))
        day_variation = (random.random() - 0.5) * 10
        trend_effect = (i / 30) * 15 * trend_direction
        spike = (random.random() - 0.5) * 20 if random.random() < 0.1 else 0
        score = base_score + day_variation + trend_effect + spike
        score = max(10, min(90, score))
        scores.append(round(score, 1))
    return {'dates': dates, 'scores': scores}

# Old recommendations function - disabled to avoid route conflicts
# @analysis.route('/recommendations')
# @analysis.route('/recommendations/')
# @analysis.route('/recommendations/<symbol>')
@access_required
def recommendations_old(symbol=None):
    """AI-powered stock recommendations and ratings"""
    try:
        # If specific symbol requested, get detailed recommendation
        if symbol:
            # Helper to clean dict for JSON serialization
            def clean_dict(d):
                from jinja2.runtime import Undefined
                if isinstance(d, dict):
                    return {k: clean_dict(v) for k, v in d.items() if not isinstance(v, Undefined)}
                elif isinstance(d, list):
                    return [clean_dict(v) for v in d]
                elif isinstance(d, Undefined):
                    return None
                return d
            symbol = symbol.strip().upper()
            # Mock detailed recommendation data for specific symbol
            hash_seed = abs(hash(symbol)) % 1000
            sentiment_data = {}  # Provide a default empty dict for demonstration
            sentiment_data = clean_dict(sentiment_data)
            detailed_recommendation = {
                'symbol': symbol,
                'name': f"{symbol.replace('.OL', ' ASA').replace('-USD', '')} Company",
                'current_price': 100 + (hash_seed % 200),
                'target_price': (100 + (hash_seed % 200)) * 1.15,
                'upside': 15.0 + (hash_seed % 20),
                'rating': ['STRONG_BUY', 'BUY', 'HOLD', 'SELL'][hash_seed % 4],
                'confidence': 70 + (hash_seed % 25),
                'risk_level': ['Low', 'Medium', 'High'][hash_seed % 3],
                'timeframe': '12 months',
                'reasons': [
                    'Strong fundamentals and earnings growth',
                    'Market leadership position in sector',
                    'Favorable industry trends and tailwinds',
                    'Solid financial metrics and balance sheet',
                    'Positive analyst sentiment and upgrades'
                ],
                'risks': [
                    'Market volatility and economic uncertainty',
                    'Competitive pressure in sector',
                    'Regulatory changes potential impact',
                    'Currency fluctuation risks'
                ],
                'sector': ['Technology', 'Banking', 'Energy', 'Healthcare', 'Consumer'][hash_seed % 5],
                'analyst_count': 5 + (hash_seed % 15),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'price_targets': {
                    'high': (100 + (hash_seed % 200)) * 1.25,
                    'average': (100 + (hash_seed % 200)) * 1.15,
                    'low': (100 + (hash_seed % 200)) * 1.05
                },
                'analyst_ratings': {
                    'strong_buy': hash_seed % 5,
                    'buy': hash_seed % 8,
                    'hold': hash_seed % 6,
                    'sell': hash_seed % 3,
                    'strong_sell': hash_seed % 2
                },
                'key_metrics': {
                    'pe_ratio': 15.0 + (hash_seed % 20),
                    'pb_ratio': 1.5 + (hash_seed % 3),
                    'dividend_yield': 2.0 + (hash_seed % 5),
                    'roe': 10.0 + (hash_seed % 20)
                }
            }
            return render_template('analysis/recommendation_detail.html',
                                 recommendation=detailed_recommendation,
                                 symbol=symbol,
                                 page_title=f"Anbefaling for {symbol}")
        
        # Generate comprehensive mock recommendations data for overview
        recommendations_data = {
            'featured_picks': [
                {
                    'symbol': 'DNB.OL',
                    'name': 'DNB Bank ASA',
                    'current_price': 185.20,
                    'target_price': 210.00,
                    'upside': 13.4,
                    # ... rest of featured_picks ...
                },
                # ... other featured picks ...
            ],
            # ... rest of recommendations_data ...
        }
        # Now handle symbol-specific recommendation
        if symbol:
            # Helper to clean dict for JSON serialization
            def clean_dict(d):
                from jinja2.runtime import Undefined
                if isinstance(d, dict):
                    return {k: clean_dict(v) for k, v in d.items() if not isinstance(v, Undefined)}
                elif isinstance(d, list):
                    return [clean_dict(v) for v in d]
                elif isinstance(d, Undefined):
                    return None
                return d
            symbol = symbol.strip().upper()
            # Mock detailed recommendation data for specific symbol
            hash_seed = abs(hash(symbol)) % 1000
            sentiment_data = {}  # Provide a default empty dict for demonstration
            sentiment_data = clean_dict(sentiment_data)
            detailed_recommendation = {
                'symbol': symbol,
                'name': f"{symbol.replace('.OL', ' ASA').replace('-USD', '')} Company",
                'current_price': 100 + (hash_seed % 200),
                'target_price': (100 + (hash_seed % 200)) * 1.15,
                'upside': 15.0 + (hash_seed % 20),
                'rating': ['STRONG_BUY', 'BUY', 'HOLD', 'SELL'][hash_seed % 4],
                'confidence': 70 + (hash_seed % 25),
                'risk_level': ['Low', 'Medium', 'High'][hash_seed % 3],
                'timeframe': '12 months',
                'reasons': [
                    'Strong fundamentals and earnings growth',
                    'Market leadership position in sector',
                    'Favorable industry trends and tailwinds',
                    'Solid financial metrics and balance sheet',
                    'Positive analyst sentiment and upgrades'
                ],
                'risks': [
                    'Market volatility and economic uncertainty',
                    'Competitive pressure in sector',
                    'Regulatory changes potential impact',
                    'Currency fluctuation risks'
                ],
                'sector': ['Technology', 'Banking', 'Energy', 'Healthcare', 'Consumer'][hash_seed % 5],
                'analyst_count': 5 + (hash_seed % 15),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'price_targets': {
                    'high': (100 + (hash_seed % 200)) * 1.25,
                    'average': (100 + (hash_seed % 200)) * 1.15,
                    'low': (100 + (hash_seed % 200)) * 1.05
                },
                'analyst_ratings': {
                    'strong_buy': hash_seed % 5,
                    'buy': hash_seed % 8,
                    'hold': hash_seed % 6,
                    'sell': hash_seed % 3,
                    'strong_sell': hash_seed % 2
                },
                'key_metrics': {
                    'pe_ratio': 15.0 + (hash_seed % 20),
                    'pb_ratio': 1.5 + (hash_seed % 3),
                    'dividend_yield': 2.0 + (hash_seed % 5),
                    'roe': 10.0 + (hash_seed % 20)
                }
            }
            return render_template('analysis/recommendation_detail.html',
                                 recommendation=detailed_recommendation,
                                 symbol=symbol,
                                 page_title=f"Anbefaling for {symbol}")
        # If no symbol, continue with recommendations_data logic
                             
    except Exception as e:
        logger.error(f"Error in recommendations: {e}")
        return render_template('error.html',
                             error="Anbefalinger er midlertidig utilgjengelig.")

@analysis.route('/screener', methods=['GET', 'POST'])
@access_required
def screener():
    """Stock screener with basic functionality"""
    logger.info(f"Screener route accessed - Method: {request.method}")
    try:
        results = []
        logger.info("Starting screener processing...")
        # Short-circuit in EKTE_ONLY: never fabricate demo screener rows
        if current_app.config.get('EKTE_ONLY'):
            available_filters = {
                'Valuation': {}, 'Financial Health': {}, 'Growth': {}, 'Dividends': {}
            }
            preset_screens = {}
            return render_template('analysis/screener.html',
                                   results=results,
                                   show_results=False,
                                   available_filters=available_filters,
                                   preset_screens=preset_screens,
                                   filter_display_names={},
                                   selected_filters=[],
                                   ekte_only=True)
        
        # Define available filters for the screener
        available_filters = {
            'Valuation': {
                'pe_ratio': 'P/E Ratio',
                'pb_ratio': 'P/B Ratio',
                'price_to_sales': 'Price/Sales',
                'ev_ebitda': 'EV/EBITDA'
            },
            'Financial Health': {
                'debt_equity': 'Debt/Equity',
                'current_ratio': 'Current Ratio',
                'roe': 'Return on Equity',
                'roa': 'Return on Assets'
            },
            'Growth': {
                'revenue_growth': 'Revenue Growth',
                'earnings_growth': 'Earnings Growth',
                'eps_growth': 'EPS Growth'
            },
            'Dividends': {
                'dividend_yield': 'Dividend Yield',
                'payout_ratio': 'Payout Ratio',
                'dividend_growth': 'Dividend Growth'
            }
        }
        
        preset_screens = {
            'value_stocks': {
                'pe_ratio_max': 15,
                'pb_ratio_max': 2.0,
                'debt_equity_max': 0.5
            },
            'growth_stocks': {
                'earnings_growth_min': 15,
                'revenue_growth_min': 10,
                'pe_ratio_max': 30
            },
            'dividend_stocks': {
                'dividend_yield_min': 3.0,
                'payout_ratio_max': 80,
                'debt_equity_max': 0.6
            }
        }
        
        # Track selected filters for template
        selected_filters = request.form.getlist('filters') if request.method == 'POST' else []
        preset = request.form.get('preset', '') if request.method == 'POST' else ''
        
        if request.method == 'POST' and not current_app.config.get('EKTE_ONLY'):
            # Generate different results based on preset selection
            if preset == 'value_stocks':
                results = [
                    {
                        'ticker': 'EQNR.OL',
                        'name': 'Equinor ASA',
                        'company': 'Equinor ASA',
                        'price': 320.50,
                        'change_percent': 2.5,
                        'volume': '1.2M',
                        'market_cap': '1020B',
                        'pe_ratio': 12.4,
                        'pb_ratio': 1.8,
                        'rsi': 45.2,
                        'recommendation': 'BUY',
                        'dividend_yield': 5.2,
                        'sector': 'Energy',
                        'industry': 'Oil & Gas'
                    },
                    {
                        'ticker': 'TEL.OL',
                        'name': 'Telenor ASA',
                        'company': 'Telenor ASA',
                        'price': 145.80,
                        'change_percent': 1.2,
                        'volume': '650K',
                        'market_cap': '195B',
                        'pe_ratio': 14.8,
                        'pb_ratio': 1.5,
                        'rsi': 48.7,
                        'recommendation': 'BUY',
                        'dividend_yield': 6.8,
                        'sector': 'Telecommunications',
                        'industry': 'Wireless'
                    }
                ]
            elif preset == 'growth_stocks':
                results = [
                    {
                        'ticker': 'AAPL',
                        'name': 'Apple Inc.',
                        'company': 'Apple Inc.',
                        'price': 182.34,
                        'change_percent': 3.8,
                        'volume': '45.2M',
                        'market_cap': '2850B',
                        'pe_ratio': 28.5,
                        'pb_ratio': 8.2,
                        'rsi': 62.1,
                        'recommendation': 'BUY',
                        'dividend_yield': 0.5,
                        'sector': 'Technology',
                        'industry': 'Consumer Electronics'
                    },
                    {
                        'ticker': 'NVDA',
                        'name': 'NVIDIA Corporation',
                        'company': 'NVIDIA Corporation',
                        'price': 485.76,
                        'change_percent': 5.2,
                        'volume': '25.8M',
                        'market_cap': '1200B',
                        'pe_ratio': 29.8,
                        'pb_ratio': 12.4,
                        'rsi': 68.4,
                        'recommendation': 'STRONG_BUY',
                        'dividend_yield': 0.3,
                        'sector': 'Technology',
                        'industry': 'Semiconductors'
                    }
                ]
            elif preset == 'dividend_stocks':
                results = [
                    {
                        'ticker': 'DNB.OL',
                        'name': 'DNB Bank ASA',
                        'company': 'DNB Bank ASA',
                        'price': 185.20,
                        'change_percent': 1.8,
                        'volume': '890K',
                        'market_cap': '280B',
                        'pe_ratio': 11.2,
                        'pb_ratio': 1.2,
                        'rsi': 52.1,
                        'recommendation': 'HOLD',
                        'dividend_yield': 6.2,
                        'sector': 'Financial',
                        'industry': 'Banking'
                    },
                    {
                        'ticker': 'NHY.OL',
                        'name': 'Norsk Hydro ASA',
                        'company': 'Norsk Hydro ASA',
                        'price': 68.45,
                        'change_percent': 0.8,
                        'volume': '1.8M',
                        'market_cap': '140B',
                        'pe_ratio': 9.8,
                        'pb_ratio': 1.1,
                        'rsi': 44.6,
                        'recommendation': 'BUY',
                        'dividend_yield': 7.5,
                        'sector': 'Materials',
                        'industry': 'Aluminum'
                    }
                ]
            else:
                # Default mixed results for custom filters
                results = [
                    {
                        'ticker': 'TSLA',
                        'name': 'Tesla Inc.',
                        'company': 'Tesla Inc.',
                        'price': 245.67,
                        'change_percent': -1.2,
                        'volume': '85.4M',
                        'market_cap': '780B',
                        'pe_ratio': 65.2,
                        'pb_ratio': 9.8,
                        'rsi': 38.9,
                        'recommendation': 'HOLD',
                        'dividend_yield': 0.0,
                        'sector': 'Automotive',
                        'industry': 'Electric Vehicles'
                    },
                    {
                        'ticker': 'MOWI.OL',
                        'name': 'Mowi ASA',
                        'company': 'Mowi ASA',
                        'price': 215.30,
                        'change_percent': 2.1,
                        'volume': '420K',
                        'market_cap': '112B',
                        'pe_ratio': 18.6,
                        'pb_ratio': 2.8,
                        'rsi': 55.7,
                        'recommendation': 'BUY',
                        'dividend_yield': 4.2,
                        'sector': 'Consumer Staples',
                        'industry': 'Aquaculture'
                    }
                ]
        
        # Process filter names before template rendering
        filter_display_names = {}
        for category in available_filters.values():
            filter_display_names.update(category)

        logger.info("Rendering screener template...")
        return render_template('analysis/screener.html',
                             results=results,
                             show_results=bool(results),
                             available_filters=available_filters,
                             preset_screens=preset_screens,
                             filter_display_names=filter_display_names,
                             selected_filters=selected_filters)
                             
    except Exception as e:
        import traceback
        logger.error(f"Error in screener: {e}")
        logger.error(f"Screener traceback: {traceback.format_exc()}")
        return render_template('error.html',
                             error=f"Screener error: {str(e)}")

@analysis.route('/benjamin-graham', methods=['GET', 'POST'])
@access_required
def benjamin_graham():
    """Benjamin Graham value analysis"""
    ticker = request.args.get('ticker') or request.form.get('ticker')
    if ticker:
        ticker = ticker.strip().upper()
        # Always return mock analysis for any ticker
        analysis_data = {
            'ticker': ticker,
            'graham_score': 78.5,
            'intrinsic_value': 195.00,
            'current_price': 185.20,
            'margin_of_safety': 5.3,
            'criteria_met': ['Low P/E ratio', 'Strong balance sheet', 'Consistent earnings'],
            'criteria_failed': ['Limited growth'],
            'criteria_results': {
                'low_pe_ratio': {
                    'criterion': {'name': 'Low P/E ratio', 'description': 'P/E ratio under 15'},
                    'value': 11.2,
                    'passed': True
                },
                'strong_balance_sheet': {
                    'criterion': {'name': 'Strong balance sheet', 'description': 'Solid financial position'},
                    'value': 'Yes',
                    'passed': True
                },
                'consistent_earnings': {
                    'criterion': {'name': 'Consistent earnings', 'description': 'Stable earnings over time'},
                    'value': 'Yes',
                    'passed': True
                },
                'limited_growth': {
                    'criterion': {'name': 'Limited growth', 'description': 'Growth below sector average'},
                    'value': 'Low',
                    'passed': False
                }
            },
            'financial_metrics': {'pe_ratio': 11.2, 'pb_ratio': 1.1},
            'recommendation': {
                'action': 'BUY',
                'reasoning': f"Graham score of 78.5 indicates strong value proposition"
            },
            'company_name': f"Company Analysis for {ticker}",
            'sector': 'Financial Services'
        }
        return render_template('analysis/benjamin_graham_select.html', analysis=analysis_data, ticker=ticker)
    # Show selection page if no ticker
    oslo_stocks = {
        'EQNR.OL': {'name': 'Equinor ASA', 'last_price': 270.50},
        'DNB.OL': {'name': 'DNB Bank ASA', 'last_price': 185.20}
    }
    global_stocks = {
        'AAPL': {'name': 'Apple Inc.', 'last_price': 185.00},
        'MSFT': {'name': 'Microsoft Corporation', 'last_price': 420.50}
    }
    return render_template('analysis/benjamin_graham_select.html', oslo_stocks=oslo_stocks, global_stocks=global_stocks, analysis=None)

@analysis.route('/sentiment-view')
@access_required  
def sentiment_view():
    """Sentiment analysis view"""
    return redirect(url_for('analysis.sentiment'))

@analysis.route('/insider-trading')
@demo_access
def insider_trading():
    """Redirect to dedicated insider trading page"""
    return redirect(url_for('market_intel.insider_trading'))

# API Endpoints
@analysis.route('/api/technical/<symbol>')
@access_required
def api_technical_data(symbol):
    """API endpoint for technical data"""
    try:
        # Mock technical data
        data = {
            'ticker': symbol.upper(),
            'current_price': 320.50,
            'change': 5.20,
            'change_percent': 1.65,
            'volume': 1250000,
            'indicators': {
                'rsi': 62.5,
                'macd': 2.15,
                'macd_signal': 1.85,
                'sma_20': 315.20,
                'sma_50': 310.80,
                'sma_200': 295.40
            },
            'patterns': ['Ascending Triangle'],
            'recommendation': 'BUY',
            'momentum': 'Bullish',
            'volatility': 0.25,
            'volume_analysis': 'Above Average'
        }
        
        return jsonify({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        logger.error(f"Error in API technical data for {symbol}: {e}")
        # Return fallback data instead of 500 error
        return jsonify({
            'success': True,
            'data': {
                'ticker': symbol.upper(),
                'current_price': 150.00,
                'change': 0.00,
                'change_percent': 0.00,
                'volume': 500000,
                'indicators': {
                    'rsi': 50.0,
                    'macd': 0.0,
                    'macd_signal': 0.0,
                    'sma_20': 150.00,
                    'sma_50': 150.00,
                    'sma_200': 150.00
                },
                'patterns': ['No Pattern Detected'],
                'recommendation': 'HOLD',
                'momentum': 'Neutral',
                'volatility': 0.15,
                'volume_analysis': 'Average',
                'error': 'Technical data temporarily unavailable - showing fallback data',
                'fallback': True
            }
        })

@analysis.route('/ai')
@analysis.route('/ai/<ticker>')
@access_required
def ai(ticker=None):
    """AI-powered stock analysis (EKTE_ONLY safe).
    In EKTE_ONLY mode we DO NOT fabricate AI outputs. We only render form or
    empty neutral page when a ticker is supplied. Any previously random or
    pseudo predictive fields (confidence %, target price, narrative) removed.
    """
    try:
        if not ticker:
            ticker = request.args.get('ticker') or request.form.get('ticker')
        if not ticker:
            return render_template('analysis/ai_form.html')
        ticker = ticker.strip().upper()
        # If authenticity flag set, skip mock assembly entirely
        if current_app.config.get('EKTE_ONLY'):
            return render_template('analysis/ai.html', analysis=None, ticker=ticker, ekte_only=True)
        cache_key = f"ai_analysis_{ticker}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        # Non‑EKTE path (retain previous structure but mark as simulated)
        ai_analysis = {
            'ticker': ticker,
            'sentiment': None,
            'summary': 'Simulert AI-analyse (ikke EKTE_ONLY)',
            'prediction': None,
            'factors': [],
            'technical_factors': [],
            'fundamental_factors': [],
            'economic_indicators': {},
            'risk_assessment': {}
        }
        result = render_template('analysis/ai.html', analysis=ai_analysis, ticker=ticker, simulated=True)
        cache.set(cache_key, result, timeout=900)
        return result
    except Exception as e:
        logger.error(f'AI analysis error: {str(e)}')
        flash(f'Feil ved lasting av AI-analyse: {str(e)}', 'error')
        return render_template('analysis/ai_form.html')

@analysis.route('/short-analysis')
@analysis.route('/short-analysis/<ticker>')
@demo_access
def short_analysis(ticker=None):
    """Short selling analysis"""
    try:
        # Check for ticker in URL path or GET parameter
        if not ticker:
            ticker = request.args.get('ticker')
        
        if ticker:
            cache_key = f"short_analysis_{ticker}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data
            
            # Mock short analysis data with all required fields
            short_data = {
                'ticker': ticker.upper(),
                'short_interest': {
                    'current': 12.5,  # Add current field
                    'percentage': 12.5,
                    'change': -2.1,  # Add change field for template
                    'shares_short': 2500000,
                    'days_to_cover': 3.2,
                    'trend': 'Increasing'
                },
                'analysis': {
                    'recommendation': 'Avoid shorting',
                    'risk_level': 'High',
                    'reasoning': 'Strong fundamentals and positive momentum'
                },
                'key_metrics': [
                    {'metric': 'Borrow rate', 'value': '2.5%'},
                    {'metric': 'Float shorted', 'value': '12.5%'},
                    {'metric': 'Short squeeze risk', 'value': 'Medium'}
                ]
            }
            
            result = render_template('analysis/short_analysis.html', 
                                   short_data=short_data,
                                   ticker=ticker)
            cache.set(cache_key, result, timeout=1800)
            return result
        else:
            return render_template('analysis/short_analysis_select.html')
    except Exception as e:
        flash(f'Feil ved lasting av short-analyse: {str(e)}', 'error')
        return render_template('analysis/short_analysis_select.html')

@analysis.route('/ai-predictions')
@analysis.route('/ai-predictions/<ticker>')
@access_required
def ai_predictions(ticker=None):
    """AI predictions (disabled for EKTE_ONLY)."""
    try:
        if not ticker:
            ticker = request.args.get('ticker')
        if not ticker:
            return render_template('analysis/ai_predictions_select.html')
        ticker = ticker.strip().upper()
        if current_app.config.get('EKTE_ONLY'):
            return render_template('analysis/ai_predictions.html', predictions=None, ticker=ticker, ekte_only=True)
        cache_key = f"ai_predictions_{ticker}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        predictions = {
            'ticker': ticker,
            'predicted_values': [],
            'dates': []
        }
        result = render_template('analysis/ai_predictions.html', predictions=predictions, ticker=ticker, simulated=True)
        cache.set(cache_key, result, timeout=900)
        return result
    except Exception as e:
        flash(f'Feil ved lasting av AI-prediksjoner: {str(e)}', 'error')
        return render_template('analysis/ai_predictions_select.html')

@analysis.route('/fundamental', methods=['GET', 'POST'])
@analysis.route('/fundamental/', methods=['GET', 'POST'])
@access_required
def fundamental():
    """Fundamental analysis"""
    try:
        ticker = None
        
        # Handle POST requests (form submissions)
        if request.method == 'POST':
            ticker = request.form.get('ticker')
        # Handle GET requests with query parameter (without symbol in URL)
        else:
            ticker = request.args.get('ticker')
            
        if ticker and ticker.strip():
            ticker = ticker.strip().upper()
            logger.info(f"Fundamental analysis requested for: {ticker}")
            
            # Enhanced mock fundamental analysis data
            fundamental_data = {
                'ticker': ticker,
                'company_name': f"{ticker} Corporation",
                'longName': f"{ticker} Corporation",  # For template compatibility
                'sector': 'Technology' if ticker in ['AAPL', 'MSFT', 'GOOGL', 'TSLA'] else 'Energy' if ticker.endswith('.OL') else 'Financial',
                'industry': 'Software' if ticker in ['AAPL', 'MSFT', 'GOOGL'] else 'Oil & Gas' if ticker.endswith('.OL') else 'Banking',
                'market_cap': 2.5e12 if ticker == 'AAPL' else 1.2e9,
                'marketCap': 2.5e12 if ticker == 'AAPL' else 1.2e9,  # Template expects this key
                'beta': 1.2,  # For template compatibility
                'revenue': 2.5e11 if ticker == 'AAPL' else 1.5e10,  # Add revenue
                'revenue_growth': 12.4,
                'eps_growth': 15.2,
                'financial_metrics': {
                    'pe_ratio': 24.5,
                    'peg_ratio': 1.2,
                    'price_to_book': 3.8,
                    'debt_to_equity': 0.65,
                    'roe': 18.5,
                    'roa': 12.3,
                    'current_ratio': 1.8,
                    'quick_ratio': 1.4,
                    'profit_margin': 21.2,
                    'operating_margin': 28.5
                },
                'valuation': {
                    'fair_value': 165.0,
                    'current_price': 152.0,
                    'upside_potential': 8.5,
                    'target_price': 170.0,
                    'rating': 'BUY',
                    'analyst_rating': 'Strong Buy',
                    'price_target_confidence': 'High'
                },
                'growth_metrics': {
                    'revenue_growth_5y': 12.4,
                    'earnings_growth_5y': 15.2,
                    'dividend_yield': 2.4,
                    'dividend_growth_5y': 8.1,
                    'eps_growth_ttm': 18.7,
                    'revenue_growth_ttm': 11.3
                },
                'financial_health': {
                    'debt_to_assets': 0.28,
                    'interest_coverage': 12.5,
                    'altman_z_score': 3.2,
                    'piotroski_score': 7,
                    'financial_strength': 'Strong'
                },
                'key_ratios': {
                    'price_to_sales': 5.8,
                    'price_to_cash_flow': 18.2,
                    'enterprise_value_to_ebitda': 15.6,
                    'book_value_per_share': 4.2
                },
                'analysis_summary': {
                    'strengths': [
                        'Strong revenue growth',
                        'Healthy profit margins',
                        'Low debt levels',
                        'Consistent dividend payments'
                    ],
                    'weaknesses': [
                        'High valuation multiples',
                        'Increased competition',
                        'Market saturation risk'
                    ],
                    'recommendation': 'BUY',
                    'confidence_level': 'High',
                    'time_horizon': '12 months'
                }
            }
            
            logger.info(f"Rendering fundamental analysis for {ticker}")
            result = render_template('analysis/fundamental.html', 
                                   symbol=ticker,
                                   ticker=ticker,
                                   analysis_data=fundamental_data,
                                   data=fundamental_data,
                                   stock_info=fundamental_data)
            return result
        else:
            logger.info("Fundamental analysis - no ticker provided")
            return render_template('analysis/fundamental_select.html')
            
    except Exception as e:
        logger.error(f'Error in fundamental analysis for {ticker}: {str(e)}')
        flash(f'Feil ved lasting av fundamental analyse: {str(e)}', 'error')
        return render_template('analysis/fundamental_select.html', 
                             error=f"Kunne ikke laste fundamental analyse for {ticker}")

@analysis.route('/technical-analysis/<symbol>')
@access_required
def technical_analysis(symbol):
    """Alternative route for technical analysis with symbol parameter"""
    return redirect(url_for('analysis.technical', ticker=symbol))

@analysis.route('/screener-view')
@access_required
def screener_view():
    """Screener view page"""
    return render_template('analysis/screener_view.html', title='Aksje Screener')

## Legacy comprehensive recommendation view removed (consolidated).
# (Previously heavy demo implementation retained in git history.)
# Removed decorators prevent duplicate route registration.
def _legacy_recommendation_full(ticker=None):  # pragma: no cover
    """Investment recommendations page with comprehensive analysis"""
    from datetime import datetime, timedelta
    from ..services.data_service import DataService
    from ..services.enhanced_yfinance_service import EnhancedYFinanceService
    from flask import flash, redirect, url_for
    
    # Check for ticker in both path and query parameters
    if not ticker:
        ticker = request.args.get('ticker')
    
    # If specific ticker is provided, focus on that stock
    if ticker:
        try:
            ticker = ticker.upper().strip()
            logger.info(f"Generating specific recommendation for ticker: {ticker}")
            
            # Generate ticker-specific recommendation analysis
            base_hash = abs(hash(ticker)) % 1000
            
            # Create a class-like object to match template expectations
            class RecommendationData:
                def __init__(self, data):
                    for key, value in data.items():
                        setattr(self, key, value)
            
            # Create realistic but demo recommendation data for the specific ticker
            ticker_recommendation_data = {
                'ticker': ticker,
                'name': f"Analysis for {ticker}",
                'company_name': f"Analysis for {ticker}",
                'sector': 'Financial Services' if 'DNB' in ticker else 'Technology',
                'rating': 'KJØP' if base_hash % 3 == 0 else 'HOLD' if base_hash % 3 == 1 else 'SELG',
                'recommendation': 'KJØP' if base_hash % 3 == 0 else 'HOLD' if base_hash % 3 == 1 else 'SELG',
                'target_price': 100 + (base_hash % 200),
                'current_price': 90 + (base_hash % 150),
                'upside': round(((100 + (base_hash % 200)) / (90 + (base_hash % 150)) - 1) * 100, 2),
                'upside_percent': round(((100 + (base_hash % 200)) / (90 + (base_hash % 150)) - 1) * 100, 2),
                'risk_level': 'Moderat',
                'timeframe': '6-12 måneder',
                'time_horizon': '6-12 måneder',
                'confidence': 70 + (base_hash % 20),
                'analyst_rating': 3.5 + (base_hash % 15) / 10,
                'strengths': [
                    f'Strong market position for {ticker}',
                    'Solid financial metrics',
                    'Good growth prospects',
                    'Experienced management team'
                ],
                'risks': [
                    'Market volatility',
                    'Sector-specific challenges',
                    'Economic uncertainty'
                ],
                'recent_news': f'Latest analysis shows positive outlook for {ticker}',
                'dividend_yield': (base_hash % 8) + 1,
                'pe_ratio': 10 + (base_hash % 20),
                'detailed_analysis': {
                    'technical_score': 60 + (base_hash % 30),
                    'fundamental_score': 55 + (base_hash % 35),
                    'sentiment_score': 50 + (base_hash % 40),
                    'overall_score': 55 + (base_hash % 35)
                },
                'price_targets': RecommendationData({
                    'high': 120 + (base_hash % 50),
                    'average': 100 + (base_hash % 30),
                    'low': 80 + (base_hash % 40)
                })
            }
            
            ticker_recommendation = RecommendationData(ticker_recommendation_data)
            
            # Return ticker-specific recommendation template
            return render_template('analysis/recommendation_detail.html', 
                                 title=f'Anbefaling for {ticker}',
                                 symbol=ticker,
                                 ticker=ticker,
                                 recommendation=ticker_recommendation,
                                 last_updated=datetime.now())
                                 
        except Exception as e:
            logger.error(f"Error generating recommendation for {ticker}: {e}")
            flash(f'Kunne ikke generere anbefaling for {ticker}. Viser generell oversikt.', 'warning')
            return redirect(url_for('analysis.recommendation'))
    
    # Comprehensive investment recommendations data
    recommendations = {
        'norwegian_stocks': [
            {
                'ticker': 'DNB.OL',
                'company_name': 'DNB Bank ASA',
                'sector': 'Finansielle tjenester',
                'recommendation': 'KJØP',
                'target_price': 190.00,
                'current_price': 175.20,
                'upside_percent': 8.44,
                'risk_level': 'Moderat',
                'time_horizon': '6-12 måneder',
                'analyst_rating': 4.2,
                'strengths': [
                    'Markedsledende posisjon i Norge',
                    'Sterk kapitalbase og likviditet',
                    'Robust utbyttepolitikk',
                    'Diversifisert forretningsmodell'
                ],
                'risks': [
                    'Renteendringer kan påvirke marginer',
                    'Kreditttap ved økonomisk nedgang',
                    'Regulatoriske endringer'
                ],
                'recent_news': 'Rapporterte sterke Q4-resultater med økt utlånsvolum',
                'dividend_yield': 6.8,
                'pe_ratio': 12.5
            },
            {
                'ticker': 'EQNR.OL',
                'company_name': 'Equinor ASA',
                'sector': 'Energi',
                'recommendation': 'KJØP',
                'target_price': 295.00,
                'current_price': 278.40,
                'upside_percent': 5.96,
                'risk_level': 'Høy',
                'time_horizon': '12-18 måneder',
                'analyst_rating': 4.0,
                'strengths': [
                    'Ledende posisjon innen offshore vind',
                    'Sterke kontantstrømmer fra olje og gass',
                    'Ambisiøse klimamål og grønn omstilling',
                    'Teknologisk ekspertise og innovasjon'
                ],
                'risks': [
                    'Volatilitet i olje- og gasspriser',
                    'Klimapolitiske endringer',
                    'Høye investeringskostnader i fornybar energi'
                ],
                'recent_news': 'Kunngjorde nye offshore vindprosjekter i Storbritannia',
                'dividend_yield': 4.2,
                'pe_ratio': 14.8
            },
            {
                'ticker': 'NEL.OL',
                'company_name': 'Nel ASA',
                'sector': 'Ren energi',
                'recommendation': 'HOLD',
                'target_price': 8.50,
                'current_price': 7.85,
                'upside_percent': 8.28,
                'risk_level': 'Høy',
                'time_horizon': '18-24 måneder',
                'analyst_rating': 3.5,
                'strengths': [
                    'Teknologileder innen hydrogenløsninger',
                    'Stor ordrereserve og pipeline',
                    'Støtte fra EU Green Deal',
                    'Strategiske partnerskap globalt'
                ],
                'risks': [
                    'Høy volatilitet og spekulativ karakter',
                    'Avhengig av statlige subsidier',
                    'Intens konkurranse i hydrogensektoren'
                ],
                'recent_news': 'Signerte stor elektrolysekontrakt i Tyskland',
                'dividend_yield': 0.0,
                'pe_ratio': None
            }
        ],
        'international_stocks': [
            {
                'ticker': 'AAPL',
                'company_name': 'Apple Inc.',
                'sector': 'Teknologi',
                'recommendation': 'KJØP',
                'target_price': 210.00,
                'current_price': 192.50,
                'upside_percent': 9.09,
                'risk_level': 'Moderat',
                'time_horizon': '6-12 måneder',
                'analyst_rating': 4.5,
                'strengths': [
                    'Sterk merkevare og kundeprogramlojalitet',
                    'Diversifisert produktportefølje',
                    'Sterke kontantstrømmer og balanse',
                    'Innovasjon innen AI og AR/VR'
                ],
                'risks': [
                    'Høy verdsettelse sammenlignet med historiske nivåer',
                    'Avhengighet av iPhone-salg',
                    'Geopolitiske spenninger med Kina'
                ],
                'recent_news': 'Lanserte nye AI-funksjoner i iOS 18',
                'dividend_yield': 0.5,
                'pe_ratio': 28.5
            },
            {
                'ticker': 'NVDA',
                'company_name': 'NVIDIA Corporation',
                'sector': 'Halvledere',
                'recommendation': 'KJØP',
                'target_price': 520.00,
                'current_price': 485.20,
                'upside_percent': 7.18,
                'risk_level': 'Høy',
                'time_horizon': '12-18 måneder',
                'analyst_rating': 4.8,
                'strengths': [
                    'Dominerer AI-chip-markedet',
                    'Sterk vekst i datasenterprodukter',
                    'Teknologisk moat og innovasjon',
                    'Ekspanderende adresserbart marked'
                ],
                'risks': [
                    'Høy verdsettelse og forventninger',
                    'Syklisk halvledermarked',
                    'Økt konkurranse fra AMD og Intel'
                ],
                'recent_news': 'Rapporterte rekordresultater drevet av AI-etterspørsel',
                'dividend_yield': 0.03,
                'pe_ratio': 65.2
            }
        ],
        'sector_themes': [
            {
                'theme': 'Fornybar Energi og Klimateknologi',
                'description': 'Kraftig vekst forventes i sektoren drevet av klimapolitikk og teknologiutvikling',
                'recommended_stocks': ['NEL.OL', 'EQNR.OL', 'ENPH', 'TSLA'],
                'time_horizon': '2-5 år',
                'risk_level': 'Høy',
                'potential_return': '15-25% årlig'
            },
            {
                'theme': 'Kunstig Intelligens og Teknologi',
                'description': 'AI-revolusjon driver vekst i cloud, halvledere og programvare',
                'recommended_stocks': ['NVDA', 'MSFT', 'GOOGL', 'AAPL'],
                'time_horizon': '1-3 år',
                'risk_level': 'Moderat-Høy',
                'potential_return': '10-20% årlig'
            },
            {
                'theme': 'Nordiske Finansaksjer',
                'description': 'Stabile utbyttebetalere med solide fundamentale forhold',
                'recommended_stocks': ['DNB.OL', 'SEB-A.ST', 'DANSKE.CO'],
                'time_horizon': '1-2 år',
                'risk_level': 'Lav-Moderat',
                'potential_return': '8-12% årlig'
            }
        ],
        'portfolio_models': [
            {
                'name': 'Konservativ Vekst',
                'description': 'Stabile aksjer med moderat risiko og jevn avkastning',
                'allocation': {
                    'Nordiske finansaksjer': 40,
                    'Amerikanske blue chips': 35,
                    'Obligasjoner': 20,
                    'Kontanter': 5
                },
                'expected_return': '6-8% årlig',
                'volatility': 'Lav',
                'recommended_for': 'Konservative investorer, pensjonssparing'
            },
            {
                'name': 'Balansert Vekst',
                'description': 'Diversifisert portefølje med moderat til høy vekstpotensial',
                'allocation': {
                    'Teknologiaksjer': 30,
                    'Norske aksjer': 25,
                    'Internasjonale aksjer': 25,
                    'Fornybar energi': 15,
                    'Kontanter': 5
                },
                'expected_return': '8-12% årlig',
                'volatility': 'Moderat',
                'recommended_for': 'Langsiktige investorer med moderat risikotoleranse'
            },
            {
                'name': 'Aggressiv Vekst',
                'description': 'Høy vekst fokusert på teknologi og fremvoksende sektorer',
                'allocation': {
                    'AI og teknologi': 40,
                    'Fornybar energi': 25,
                    'Vekstaksjer': 20,
                    'Kryptovaluta': 10,
                    'Kontanter': 5
                },
                'expected_return': '12-20% årlig',
                'volatility': 'Høy',
                'recommended_for': 'Unge investorer med høy risikotoleranse'
            }
        ]
    }
    
    # Market insights and analysis
    market_insights = {
        'current_environment': {
            'market_sentiment': 'Forsiktig optimistisk',
            'key_drivers': [
                'AI-revolusjon fortsetter å drive teknologiaksjer',
                'Sentralbankers rentepolitikk påvirker valg',
                'Grønn omstilling skaper nye investeringsmuligheter',
                'Geopolitiske forhold skaper usikkerhet'
            ],
            'opportunities': [
                'AI og maskinlæring teknologier',
                'Fornybar energi og energilagring',
                'Nordiske kvalitetsaksjer med høye utbytter',
                'Cybersikkerhet og digital infrastruktur'
            ],
            'risks': [
                'Inflasjon og renteendringer',
                'Geopolitiske spenninger',
                'Oververdsettelse i enkelte sektorer',
                'Regulatoriske endringer innen teknologi'
            ]
        },
        'quarterly_outlook': {
            'q1_2024': 'Fokus på earnings season og rentebeslutninger',
            'q2_2024': 'Sommertradition og potensielle volatilitet',
            'q3_2024': 'Tilbake til normal handel etter sommerferien',
            'q4_2024': 'Årsresultater og utsikter for 2025'
        }
    }
    
    return render_template('analysis/recommendation.html', 
                         title='Investeringsanbefalinger',
                         recommendations=recommendations,
                         market_insights=market_insights,
                         last_updated=datetime.now())

@analysis.route('/prediction')
@access_required  
def prediction():
    """AI prediction analysis page"""
    # Demo predictions data
    predictions_oslo = {
        'DNB.OL': {
            'price_prediction': 185.50,
            'confidence': 78,
            'trend': 'UP',
            'data_period': '60 dager',
            'trend_period': '5-30 dager',
            'last_price': 175.20,
            'next_price': 185.50,
            'change_percent': 5.88,
            'confidence': 'HIGH'
        },
        'EQNR.OL': {
            'price_prediction': 290.25,
            'confidence': 82,
            'trend': 'UP',
            'data_period': '60 dager', 
            'trend_period': '5-30 dager',
            'last_price': 278.40,
            'next_price': 290.25,
            'change_percent': 4.26,
            'confidence': 'HIGH'
        },
        'TEL.OL': {
            'price_prediction': 165.75,
            'confidence': 75,
            'trend': 'STABLE',
            'data_period': '60 dager',
            'trend_period': '5-30 dager',
            'last_price': 162.30,
            'next_price': 165.75,
            'change_percent': 2.13,
            'confidence': 'MEDIUM'
        }
    }
    
    # Demo global predictions data
    predictions_global = {
        'AAPL': {
            'price_prediction': 195.75,
            'confidence': 85,
            'trend': 'UP',
            'data_period': '60 dager',
            'trend_period': '5-30 dager',
            'last_price': 185.20,
            'next_price': 195.75,
            'change_percent': 5.69,
            'confidence': 'HIGH'
        },
        'TSLA': {
            'price_prediction': 245.80,
            'confidence': 79,
            'trend': 'UP',
            'data_period': '60 dager', 
            'trend_period': '5-30 dager',
            'last_price': 238.45,
            'next_price': 245.80,
            'change_percent': 3.08,
            'confidence': 'MEDIUM'
        },
        'MSFT': {
            'price_prediction': 425.30,
            'confidence': 88,
            'trend': 'UP',
            'data_period': '60 dager',
            'trend_period': '5-30 dager',
            'last_price': 415.25,
            'next_price': 425.30,
            'change_percent': 2.42,
            'confidence': 'HIGH'
        }
    }
    
    return render_template('analysis/prediction.html', 
                         title='AI Prognoser',
                         predictions_oslo=predictions_oslo,
                         predictions_global=predictions_global)

@analysis.route('/currency-overview')
@premium_required
def currency_overview():
    """Currency market overview with error handling"""
    from datetime import datetime
    
    try:
        # Try to get real currency data first
        currency_data = DataService.get_currency_overview() if hasattr(DataService, 'get_currency_overview') else None
        
        if currency_data and isinstance(currency_data, dict):
            # Use real data if available
            currencies = currency_data
        else:
            # Fallback to demo currency data
            currencies = {
                'USD/NOK': {
                    'rate': 10.85,
                    'change': 0.12,
                    'change_percent': 1.12,
                    'high': 10.95,
                    'low': 10.70,
                    'volume': 1200000,
                    'signal': 'BUY',
                    'name': 'USD/NOK'
                },
                'EUR/NOK': {
                    'rate': 11.75,
                    'change': -0.05,
                    'change_percent': -0.42,
                    'high': 11.80,
                    'low': 11.60,
                    'volume': 950000,
                    'signal': 'HOLD',
                    'name': 'EUR/NOK'
                },
                'GBP/NOK': {
                    'rate': 13.65,
                    'change': 0.08,
                    'change_percent': 0.59,
                    'high': 13.75,
                    'low': 13.50,
                    'volume': 800000,
                    'signal': 'SELL',
                    'name': 'GBP/NOK'
                }
            }
        
        return render_template('analysis/currency_overview.html', 
                             title='Valutaoversikt',
                             currencies=currencies,
                             now=datetime.now())
    
    except Exception as e:
        logger.error(f"Error in currency overview: {e}")
        # Provide minimal fallback currency data
        fallback_currencies = {
            'USD/NOK': {
                'rate': 10.85,
                'change': 0.0,
                'change_percent': 0.0,
                'high': 10.85,
                'low': 10.85,
                'volume': 0,
                'signal': 'HOLD',
                'name': 'USD/NOK'
            }
        }
        
        return render_template('analysis/currency_overview.html', 
                             title='Valutaoversikt',
                             currencies=fallback_currencies,
                             now=datetime.now(),
                             error="Data ikke tilgjengelig for øyeblikket")

@analysis.route('/oslo-overview')
@access_required
def oslo_overview():
    """Oslo Børs market overview"""
    return render_template('analysis/oslo_overview.html', title='Oslo Børs Oversikt')

@analysis.route('/global-overview')
@access_required
def global_overview():
    """Global market overview"""
    return render_template('analysis/global_overview.html', title='Global Markeds Oversikt')

@analysis.route('/tradingview')
@demo_access
def tradingview():
    """TradingView Charts Analysis - Enhanced with demo support"""
    raw_symbol = request.args.get('symbol', 'AAPL') or 'AAPL'

    # Server-side symbol sanitization & validation
    try:
        cleaned = raw_symbol.upper().strip()
        # Allow letters, numbers, dot, dash, slash, equals (for forex like EURUSD=X), and crypto dash
        allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-=/")
        cleaned = ''.join(ch for ch in cleaned if ch in allowed_chars)
        # Basic length guard
        if len(cleaned) == 0 or len(cleaned) > 20:
            cleaned = 'AAPL'
        # Normalize some common variants
        if cleaned.endswith('.OSL') and not cleaned.endswith('.OL'):
            cleaned = cleaned.replace('.OSL', '.OL')
        symbol = cleaned
    except Exception:
        symbol = 'AAPL'
    
    # Get stock info for the symbol if available
    stock_info = {}
    try:
        if DataService:
            stock_info = DataService.get_stock_info(symbol) or {}
    except Exception as e:
        logger.warning(f"Could not fetch stock info for {symbol}: {e}")
    
    try:
        return render_template('analysis/tradingview.html', 
                             title='TradingView Charts',
                             symbol=symbol,
                             stock_info=stock_info,
                             sanitized=True)
    except Exception as e:
        logger.error(f"Error loading TradingView page: {e}")
        return render_template('analysis/tradingview.html', 
                             title='TradingView Charts',
                             symbol=symbol,
                             stock_info={},
                             error=True,
                             sanitized=True)

@analysis.route('/backtest')
@access_required
def backtest():
    """Backtesting functionality"""
    return render_template('analysis/backtest.html', title='Backtest Strategier')

@analysis.route('/strategy-builder')
@access_required
def strategy_builder():
    """Strategy builder functionality with persisted user strategies."""
    user_strategies = []
    try:
        from ..models.strategy import Strategy  # type: ignore
        if current_user.is_authenticated:
            user_strategies = (Strategy.query
                               .filter_by(user_id=current_user.id)
                               .order_by(Strategy.created_at.desc())
                               .limit(50).all())
    except Exception as e:
        try:
            logger.warning(f"Could not load strategies: {e}")
        except Exception:
            pass
    return render_template('analysis/strategy_builder.html',
                           title='Strategibygger',
                           strategies=user_strategies)

@analysis.route('/api/strategies', methods=['GET', 'POST'])
@analysis.route('/api/v1/strategies', methods=['GET', 'POST'])
@api_access_required
# CSRF exempt: JSON API used by SPA/JS fetch; protected by authentication + rate limiting.
# Form-based endpoints retain CSRF. Re-evaluate if public write exposure is introduced.
@csrf.exempt  # type: ignore
@strategy_rate_limit(max_requests=30, window=60, methods=['POST'])
def api_strategies():
    """Create or list user strategies with validation & duplicate checks.

    POST JSON: { name: str, buy: {...}, sell: {...}, risk: {...} }
    Rules:
      - Name required (2-120 chars)
      - Reject duplicate names (case-insensitive) per user
      - buy/sell/risk must be objects (or omitted)
    Returns JSON with success flag and details.
    """
    try:
        from ..extensions import db
        from ..models.strategy import Strategy  # type: ignore

        if request.method == 'POST':
            # Ensure checksum column exists (legacy DB hotfix). In production use migrations instead.
            try:
                from sqlalchemy import inspect as _insp, text as _text
                insp = _insp(db.engine)
                cols = {c['name'] for c in insp.get_columns('strategy_versions')}
                if 'checksum' not in cols:
                    db.engine.execute(_text('ALTER TABLE strategy_versions ADD COLUMN checksum VARCHAR(64)'))
            except Exception:
                pass
            data = request.get_json(silent=True) or {}
            # Build name set for duplicate detection
            existing_names_lower = set()
            try:
                existing_names_lower = {s.name.lower() for s in Strategy.query.filter_by(user_id=current_user.id).with_entities(Strategy.name).all()}
            except Exception:
                pass
            from ..utils.strategy_validation import validate_strategy_payload, StrategyValidationError  # type: ignore
            try:
                name, buy_rules, sell_rules, risk_rules = validate_strategy_payload(data, existing_names_lower=existing_names_lower)
            except StrategyValidationError as ve:
                return jsonify({'success': False, 'error': str(ve)}), ve.status
            if name is None:
                return jsonify({'success': False, 'error': 'Strateginavn mangler'}), 400

            strat = Strategy(
                user_id=current_user.id,
                name=name,
                buy_rules=buy_rules,
                sell_rules=sell_rules,
                risk_rules=risk_rules,
            )

            try:
                db.session.add(strat)
                db.session.commit()
                # Create initial version snapshot with retry if checksum column missing
                from sqlalchemy import text as _text
                snapshot_attempted = False
                for attempt in range(2):
                    try:
                        from ..models.strategy_version import StrategyVersion  # type: ignore
                        import hashlib, json as _json
                        payload = {
                            'name': strat.name,
                            'buy': strat.buy_rules or {},
                            'sell': strat.sell_rules or {},
                            'risk': strat.risk_rules or {}
                        }
                        checksum = hashlib.sha256(_json.dumps(payload, sort_keys=True).encode('utf-8')).hexdigest()
                        ver = StrategyVersion(
                            strategy_id=strat.id,
                            user_id=current_user.id,
                            version=1,
                            name=strat.name,
                            buy_rules=strat.buy_rules,
                            sell_rules=strat.sell_rules,
                            risk_rules=strat.risk_rules,
                            checksum=checksum
                        )
                        db.session.add(ver)
                        db.session.commit()
                        snapshot_attempted = True
                        break
                    except Exception as ver_err:
                        db.session.rollback()
                        # Attempt hotfix for missing checksum column then retry once
                        if attempt == 0:
                            try:
                                db.engine.execute(_text('ALTER TABLE strategy_versions ADD COLUMN checksum VARCHAR(64)'))
                            except Exception:
                                pass
                            continue
                        try: logger.warning(f"Strategy version create failed id={strat.id} err={ver_err}")
                        except Exception: pass
                try:
                    logger.info(f"Strategy created id={strat.id} user={current_user.id} name='{strat.name}'")
                except Exception:
                    pass
            except Exception as db_err:
                db.session.rollback()
                try:
                    logger.error(f"Strategy commit failed: {db_err}")
                except Exception:
                    pass
                return jsonify({'success': False, 'error': 'Kunne ikke lagre strategi'}), 500

            return jsonify({'success': True, 'id': strat.id, 'name': strat.name})

        # GET list
        strategies = []
        if current_user.is_authenticated:
            try:
                strategies = (Strategy.query
                               .filter_by(user_id=current_user.id)
                               .order_by(Strategy.created_at.desc())
                               .limit(200).all())
            except Exception as q_err:
                try:
                    logger.error(f"Strategy query failed: {q_err}")
                except Exception:
                    pass
        return jsonify({'success': True, 'strategies': [s.to_dict_basic() for s in strategies]})
    except Exception as e:
        try:
            logger.error(f"Strategy API error: {e}")
        except Exception:
            pass
        return jsonify({'success': False, 'error': 'Strategi API feil'}), 500

@analysis.route('/api/strategies/<int:strategy_id>', methods=['GET', 'PUT', 'PATCH', 'DELETE'])
@analysis.route('/api/v1/strategies/<int:strategy_id>', methods=['GET', 'PUT', 'PATCH', 'DELETE'])
@api_access_required
@csrf.exempt  # type: ignore
@strategy_rate_limit(max_requests=60, window=60, methods=['PUT','PATCH','DELETE'])
def api_strategy_single(strategy_id):
    """Retrieve, update or delete a single strategy.
    Methods:
      GET    -> return full strategy (including rules)
      PATCH/PUT JSON keys: name, buy, sell, risk
      DELETE -> remove strategy
    """
    try:
        from ..extensions import db
        from ..models.strategy import Strategy  # type: ignore
        strat = Strategy.query.filter_by(id=strategy_id, user_id=current_user.id).first()
        if not strat:
            return jsonify({'success': False, 'error': 'Strategi ikke funnet'}), 404

        if request.method == 'GET':
            # Compute ETag from latest version checksum if present
            etag = None
            try:
                from ..models.strategy_version import StrategyVersion  # type: ignore
                latest = StrategyVersion.query.filter_by(strategy_id=strategy_id).order_by(StrategyVersion.version.desc()).first()
                if latest and latest.checksum:
                    etag = f'W/"{latest.checksum}"'
            except Exception:
                pass
            if etag and request.headers.get('If-None-Match') == etag:
                resp = make_response('', 304)
                resp.headers['ETag'] = etag
                return resp
            payload = {'success': True, 'strategy': strat.to_dict_full()}
            resp = jsonify(payload)
            if etag:
                resp.headers['ETag'] = etag
            return resp

        if request.method in ('PUT','PATCH'):
            # Ensure checksum column exists (legacy DB hotfix). In production use migrations instead.
            try:
                from sqlalchemy import inspect as _insp, text as _text
                insp = _insp(db.engine)
                cols = {c['name'] for c in insp.get_columns('strategy_versions')}
                if 'checksum' not in cols:
                    db.engine.execute(_text('ALTER TABLE strategy_versions ADD COLUMN checksum VARCHAR(64)'))
            except Exception:
                pass
            data = request.get_json(silent=True) or {}
            changed = False
            from ..utils.strategy_validation import validate_strategy_payload, StrategyValidationError  # type: ignore
            try:
                name, buy, sell, risk = validate_strategy_payload(data)
            except StrategyValidationError as ve:
                return jsonify({'success': False, 'error': str(ve)}), ve.status
            if name is not None and name != strat.name:
                # Duplicate check excluding self
                from sqlalchemy import func
                dup = Strategy.query.filter(Strategy.user_id==current_user.id, func.lower(Strategy.name)==name.lower(), Strategy.id!=strat.id).first()
                if dup:
                    return jsonify({'success': False, 'error': 'Strateginavn finnes allerede'}), 409
                strat.name = name
                changed = True
            for incoming, attr in [(buy,'buy_rules'),(sell,'sell_rules'),(risk,'risk_rules')]:
                if incoming is not None:
                    setattr(strat, attr, incoming)
                    changed = True
            if not changed:
                return jsonify({'success': True, 'strategy': strat.to_dict_full(), 'message': 'Ingen endringer'}), 200

            try:
                db.session.commit()
                # Create new version snapshot (increment)
                try:
                    from ..models.strategy_version import StrategyVersion  # type: ignore
                    import hashlib, json as _json
                    for attempt in range(2):
                        try:
                            # Determine next version & avoid duplicate snapshot via checksum
                            last_version = 0
                            last_checksum = None
                            try:
                                last_obj = StrategyVersion.query.filter_by(strategy_id=strat.id).order_by(StrategyVersion.version.desc()).first()
                                if last_obj:
                                    last_version = last_obj.version
                                    last_checksum = last_obj.checksum
                            except Exception:
                                pass
                            payload = {
                                'name': strat.name,
                                'buy': strat.buy_rules or {},
                                'sell': strat.sell_rules or {},
                                'risk': strat.risk_rules or {}
                            }
                            checksum = hashlib.sha256(_json.dumps(payload, sort_keys=True).encode('utf-8')).hexdigest()
                            if checksum != last_checksum:  # only snapshot if changed
                                ver = StrategyVersion(
                                    strategy_id=strat.id,
                                    user_id=current_user.id,
                                    version=last_version + 1,
                                    name=strat.name,
                                    buy_rules=strat.buy_rules,
                                    sell_rules=strat.sell_rules,
                                    risk_rules=strat.risk_rules,
                                    checksum=checksum
                                )
                                db.session.add(ver)
                                db.session.commit()
                            else:
                                try: logger.info(f"Strategy update produced no content change; snapshot skipped id={strat.id}")
                                except Exception: pass
                            break
                        except Exception as ver_err:
                            db.session.rollback()
                            if attempt == 0:
                                from sqlalchemy import text as _text
                                try:
                                    db.engine.execute(_text('ALTER TABLE strategy_versions ADD COLUMN checksum VARCHAR(64)'))
                                except Exception:
                                    pass
                                continue
                            try: logger.warning(f"Strategy version update failed id={strat.id} err={ver_err}")
                            except Exception: pass
                except Exception as ver_err:
                    db.session.rollback()
                    try: logger.warning(f"Strategy version update failed id={strat.id} err={ver_err}")
                    except Exception: pass
                try:
                    logger.info(f"Strategy updated id={strat.id} user={current_user.id}")
                except Exception:
                    pass
            except Exception as commit_err:
                db.session.rollback()
                try:
                    logger.error(f"Strategy update failed id={strat.id} err={commit_err}")
                except Exception:
                    pass
                return jsonify({'success': False, 'error': 'Kunne ikke oppdatere'}), 500
            return jsonify({'success': True, 'strategy': strat.to_dict_full()})

        # DELETE
        try:
            db.session.delete(strat)
            db.session.commit()
            try:
                logger.info(f"Strategy deleted id={strategy_id} user={current_user.id}")
            except Exception:
                pass
            return jsonify({'success': True, 'deleted': strategy_id})
        except Exception as del_err:
            db.session.rollback()
            try:
                logger.error(f"Strategy delete failed id={strategy_id} err={del_err}")
            except Exception:
                pass
            return jsonify({'success': False, 'error': 'Kunne ikke slette'}), 500
    except Exception as e:
        try:
            logger.error(f"Single strategy API error: {e}")
        except Exception:
            pass
        return jsonify({'success': False, 'error': 'Strategi API feil'}), 500

@analysis.route('/api/strategies/<int:strategy_id>/backtest', methods=['POST'])
@analysis.route('/api/v1/strategies/<int:strategy_id>/backtest', methods=['POST'])
@access_required
@strategy_rate_limit(max_requests=25, window=300, methods=['POST'])
def api_strategy_backtest(strategy_id):
    """Run a lightweight (stub) backtest for a strategy.
    Accepts optional JSON: { "symbol": "DNB.OL", "period": "6M" }
    Returns simulated metrics to be replaced by real engine later.
    """
    try:
        from ..models.strategy import Strategy  # type: ignore
        strat = Strategy.query.filter_by(id=strategy_id, user_id=current_user.id).first()
        if not strat:
            return jsonify({'success': False, 'error': 'Strategi ikke funnet'}), 404

        payload = request.get_json(silent=True) or {}
        symbol = (payload.get('symbol') or 'DNB.OL').upper()
        period = payload.get('period') or '6M'

        # Dummy metrics (could integrate real backtester)
        import random, math
        base_return = random.uniform(4, 15)  # %
        volatility = random.uniform(5, 18)   # %
        sharpe = round(base_return / (volatility if volatility else 1), 2)
        trades = random.randint(5, 25)
        win_rate = random.uniform(35, 70)
        max_dd = random.uniform(-12, -4)

        result = {
            'symbol': symbol,
            'period': period,
            'metrics': {
                'return_pct': round(base_return,2),
                'volatility_pct': round(volatility,2),
                'sharpe': sharpe,
                'trades': trades,
                'win_rate_pct': round(win_rate,1),
                'max_drawdown_pct': round(max_dd,2)
            }
        }
        try:
            logger.info(f"Strategy backtest stub id={strategy_id} user={current_user.id} symbol={symbol} period={period}")
        except Exception:
            pass
        return jsonify({'success': True, 'backtest': result})
    except Exception as e:
        try:
            logger.error(f"Backtest error strategy={strategy_id}: {e}")
        except Exception:
            pass
        return jsonify({'success': False, 'error': 'Backtest feil'}), 500

@analysis.route('/api/strategies/<int:strategy_id>/versions', methods=['GET'])
@analysis.route('/api/v1/strategies/<int:strategy_id>/versions', methods=['GET'])
@access_required
def api_strategy_versions(strategy_id):
    """Return ordered version history (latest first) for a strategy.
    Query Params:
      page (int, optional, default 1)
      per_page (int, optional, default 50, max 200)
      include_checksum=1 to include checksum field in each version object
    Legacy behavior (no params) still returns up to 200 latest versions.
    """
    try:
        # Hotfix ensure checksum column exists before query
        try:
            from sqlalchemy import inspect as _insp, text as _text
            insp = _insp(db.engine)
            cols = {c['name'] for c in insp.get_columns('strategy_versions')}
            if 'checksum' not in cols:
                db.engine.execute(_text('ALTER TABLE strategy_versions ADD COLUMN checksum VARCHAR(64)'))
        except Exception:
            pass
        from ..models.strategy import Strategy  # type: ignore
        from ..models.strategy_version import StrategyVersion  # type: ignore
        strat = Strategy.query.filter_by(id=strategy_id, user_id=current_user.id).first()
        if not strat:
            return jsonify({'success': False, 'error': 'Strategi ikke funnet'}), 404
        include_checksum = request.args.get('include_checksum') in ('1','true','yes')
        page = request.args.get('page', type=int) or 1
        per_page = request.args.get('per_page', type=int) or 50
        if per_page > 200: per_page = 200
        if page < 1: page = 1
        query = (StrategyVersion.query
                 .filter_by(strategy_id=strategy_id)
                 .order_by(StrategyVersion.version.desc()))
        total = query.count()
        items = query.offset((page-1)*per_page).limit(per_page).all()
        out = []
        for v in items:
            d = v.to_dict()
            if include_checksum:
                d['checksum'] = v.checksum
            out.append(d)
        return jsonify({'success': True, 'versions': out, 'page': page, 'per_page': per_page, 'total': total})
    except Exception as e:
        try:
            logger.error(f"Versions fetch error strategy={strategy_id}: {e}")
        except Exception:
            pass
        return jsonify({'success': False, 'error': 'Kunne ikke hente versjoner'}), 500

@analysis.route('/api/strategies/<int:strategy_id>/rollback/<int:version_id>', methods=['POST'])
@analysis.route('/api/v1/strategies/<int:strategy_id>/rollback/<int:version_id>', methods=['POST'])
@access_required
@strategy_rate_limit(max_requests=20, window=300, methods=['POST'])
def api_strategy_rollback(strategy_id, version_id):
    """Rollback a strategy to a previous version by creating a new head snapshot.
    Does not mutate historical version rows; creates a new version (last+1) with content of selected version.
    """
    try:
        from ..models.strategy import Strategy  # type: ignore
        from ..models.strategy_version import StrategyVersion  # type: ignore
        strat = Strategy.query.filter_by(id=strategy_id, user_id=current_user.id).first()
        if not strat:
            return jsonify({'success': False, 'error': 'Strategi ikke funnet'}), 404
        target_version = (StrategyVersion.query
                           .filter_by(id=version_id, strategy_id=strategy_id)
                           .first())
        if not target_version:
            return jsonify({'success': False, 'error': 'Versjon ikke funnet'}), 404
        # Determine next version number
        last_version = 0
        try:
            last_obj = (StrategyVersion.query
                        .filter_by(strategy_id=strategy_id)
                        .order_by(StrategyVersion.version.desc()).first())
            if last_obj:
                last_version = last_obj.version
        except Exception:
            pass
        # Apply fields to strategy
        changed = False
        for attr, val in [('name', target_version.name),
                          ('buy_rules', target_version.buy_rules),
                          ('sell_rules', target_version.sell_rules),
                          ('risk_rules', target_version.risk_rules)]:
            if getattr(strat, attr) != val:
                setattr(strat, attr, val)
                changed = True
        try:
            if changed:
                db.session.commit()
        except Exception as commit_err:
            db.session.rollback()
            try: logger.error(f"Rollback commit failed strategy={strategy_id} err={commit_err}")
            except Exception: pass
            return jsonify({'success': False, 'error': 'Kunne ikke rulle tilbake'}), 500
        # Create new version snapshot regardless (captures state)
        try:
            import hashlib, json as _json
            payload = {
                'name': strat.name,
                'buy': strat.buy_rules or {},
                'sell': strat.sell_rules or {},
                'risk': strat.risk_rules or {}
            }
            checksum = hashlib.sha256(_json.dumps(payload, sort_keys=True).encode('utf-8')).hexdigest()
            from ..models.strategy_version import StrategyVersion  # type: ignore
            # Avoid duplicate (rare: rollback to identical current state)
            latest = StrategyVersion.query.filter_by(strategy_id=strategy_id).order_by(StrategyVersion.version.desc()).first()
            if latest and latest.checksum == checksum:
                new_ver = latest  # reuse, do not create duplicate
            else:
                new_ver = StrategyVersion(
                    strategy_id=strategy_id,
                    user_id=current_user.id,
                    version=last_version + 1,
                    name=strat.name,
                    buy_rules=strat.buy_rules,
                    sell_rules=strat.sell_rules,
                    risk_rules=strat.risk_rules,
                    checksum=checksum
                )
                db.session.add(new_ver)
                db.session.commit()
        except Exception as ver_err:
            db.session.rollback()
            try: logger.warning(f"Rollback snapshot creation failed strategy={strategy_id} err={ver_err}")
            except Exception: pass
            return jsonify({'success': False, 'error': 'Kunne ikke opprette versjon etter rollback'}), 500
        try:
            logger.info(f"Strategy rollback applied strategy={strategy_id} to version_id={version_id} new_version={new_ver.version}")
        except Exception:
            pass
        return jsonify({'success': True, 'strategy': strat.to_dict_full(), 'new_version': new_ver.version})
    except Exception as e:
        try: logger.error(f"Rollback error strategy={strategy_id} version={version_id}: {e}")
        except Exception: pass
        return jsonify({'success': False, 'error': 'Rollback feil'}), 500

@analysis.route('/api/strategies/<int:strategy_id>/diff/<int:v1>/<int:v2>', methods=['GET'])
@analysis.route('/api/v1/strategies/<int:strategy_id>/diff/<int:v1>/<int:v2>', methods=['GET'])
@access_required
def api_strategy_version_diff(strategy_id, v1, v2):
    """Return a structural diff between two strategy versions.
    Short-circuits if checksums equal.
    Response: {
      success: true,
      identical: bool,
      checksum_equal: bool,
      left_version: v1,
      right_version: v2,
      diff: { 'fields_changed': [...], 'details': { field: {left:..., right:...} } }
    }
    """
    try:
        from ..models.strategy import Strategy  # type: ignore
        from ..models.strategy_version import StrategyVersion  # type: ignore
        strat = Strategy.query.filter_by(id=strategy_id, user_id=current_user.id).first()
        if not strat:
            return jsonify({'success': False, 'error': 'Strategi ikke funnet'}), 404
        q = StrategyVersion.query.filter_by(strategy_id=strategy_id)
        left = q.filter_by(version=v1).first()
        right = q.filter_by(version=v2).first()
        if not left or not right:
            return jsonify({'success': False, 'error': 'Versjon(er) ikke funnet'}), 404
        checksum_equal = (left.checksum and right.checksum and left.checksum == right.checksum)
        if checksum_equal:
            return jsonify({'success': True, 'identical': True, 'checksum_equal': True, 'left_version': v1, 'right_version': v2, 'diff': {'fields_changed': [], 'details': {}}})
        # Build field-level diff
        fields = ['name','buy_rules','sell_rules','risk_rules']
        changed = []
        details = {}
        for f in fields:
            lv = getattr(left, f)
            rv = getattr(right, f)
            if lv != rv:
                changed.append(f.replace('_rules','').replace('name','name'))
                details[f] = {'left': lv, 'right': rv}
        return jsonify({'success': True, 'identical': len(changed)==0, 'checksum_equal': False, 'left_version': v1, 'right_version': v2, 'diff': {'fields_changed': changed, 'details': details}})
    except Exception as e:
        try: logger.error(f"Version diff error strategy={strategy_id} v1={v1} v2={v2}: {e}")
        except Exception: pass
        return jsonify({'success': False, 'error': 'Diff feil'}), 500

@analysis.route('/api/strategies/limiter/metrics', methods=['GET'])
@analysis.route('/api/v1/strategies/limiter/metrics', methods=['GET'])
@access_required
def api_strategy_limiter_metrics():
    """Expose lightweight snapshot of in-memory limiter queues (sizes only) and Redis status.
    Returns: { success, redis: {enabled: bool}, buckets: { bucket: {user_id: count } } }
    Only intended for debugging/admin; could later restrict to admin.
    """
    try:
        store = getattr(strategy_rate_limit, '_store', {})
        redis_client = getattr(strategy_rate_limit, '_redis', None)
        summary = {}
        for (bucket, uid), dq in store.items():
            summary.setdefault(bucket, {})[str(uid)] = len(dq)
        return jsonify({'success': True, 'redis': {'enabled': bool(redis_client)}, 'buckets': summary})
    except Exception as e:
        try: logger.error(f"Limiter metrics error: {e}")
        except Exception: pass
        return jsonify({'success': False, 'error': 'Metrics feil'}), 500

