from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_from_directory, session
from flask_login import current_user, login_required
from ..utils.access_control import access_required, demo_access

from ..models.user import User
from ..models.portfolio import Portfolio, PortfolioStock
from ..extensions import cache
from datetime import datetime, timedelta
import logging

# Safe imports for services that might not exist
try:
    from ..services.analysis_service import AnalysisService
except ImportError:
    AnalysisService = None

try:
    from ..services.advanced_technical_service import AdvancedTechnicalService
except ImportError:
    AdvancedTechnicalService = None

try:
    from ..services.ai_service import AIService
except ImportError:
    AIService = None

try:
    from ..services.data_service import DataService, OSLO_BORS_TICKERS, GLOBAL_TICKERS
except ImportError:
    DataService = None
    OSLO_BORS_TICKERS = ['EQNR.OL', 'DNB.OL', 'TEL.OL', 'YAR.OL', 'MOWI.OL']
    GLOBAL_TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']

# Set up logger
logger = logging.getLogger(__name__)

analysis = Blueprint('analysis', __name__, url_prefix='/analysis')

# NOTE: The lightweight '/analysis/sentiment' placeholder route has been
# removed to eliminate duplication and ensure the robust implementation
# in analysis.py is always used (with full fallback data + template keys).
# If this file is still imported, the absence of this route prevents
# accidental override and potential template errors.

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
@access_required  
def technical():
    """Advanced Technical analysis with comprehensive indicators and patterns"""
    try:
        symbol_raw = request.args.get('symbol') or request.form.get('symbol')
        if symbol_raw:
            try:
                from ..utils.symbol_utils import sanitize_symbol
                symbol, valid = sanitize_symbol(symbol_raw)
            except Exception:
                symbol = symbol_raw.strip().upper()
                valid = True if symbol else False
        else:
            symbol = None
            valid = False
        
        if symbol:
            technical_data = None
            try:
                import numpy as np
                import pandas as pd
            except Exception:
                np = None
                pd = None
            df = None
            if DataService and hasattr(DataService, 'get_historical_data') and pd is not None:
                try:
                    df = DataService.get_historical_data(symbol, period='6mo', interval='1d')
                except Exception:
                    df = None
            if df is not None and not getattr(df, 'empty', True):
                try:
                    closes = df['Close'] if 'Close' in df.columns else df.iloc[:,0]
                    # RSI
                    delta = closes.diff()
                    up = delta.clip(lower=0)
                    down = -delta.clip(upper=0)
                    roll = 14
                    avg_gain = up.rolling(roll).mean()
                    avg_loss = down.rolling(roll).mean()
                    rs = avg_gain / (avg_loss + 1e-9)
                    rsi = 100 - (100 / (1 + rs))
                    rsi_val = float(rsi.iloc[-1]) if len(rsi) > roll else None
                    # MACD
                    ema12 = closes.ewm(span=12, adjust=False).mean()
                    ema26 = closes.ewm(span=26, adjust=False).mean()
                    macd = ema12 - ema26
                    signal = macd.ewm(span=9, adjust=False).mean()
                    macd_val = float(macd.iloc[-1]) if len(macd) > 26 else None
                    macd_signal = float(signal.iloc[-1]) if len(signal) > 9 else None
                    # Volume
                    volume_val = float(df['Volume'].iloc[-1]) if 'Volume' in df.columns else None
                    last_price = float(closes.iloc[-1])
                    technical_data = {
                        'symbol': symbol,
                        'current_price': last_price,
                        'indicators': {
                            'rsi': round(rsi_val,2) if rsi_val else None,
                            'macd': round(macd_val,2) if macd_val else None,
                            'macd_signal': round(macd_signal,2) if macd_signal else None,
                            'volume': volume_val
                        }
                    }
                    # Supplement with real-time stock info if available
                    if DataService and hasattr(DataService, 'get_stock_info'):
                        try:
                            real_info = DataService.get_stock_info(symbol)
                            if real_info:
                                technical_data['name'] = real_info.get('name') or real_info.get('longName') or real_info.get('shortName')
                                technical_data['last_price'] = real_info.get('last_price') or last_price
                                technical_data['change'] = real_info.get('change')
                                technical_data['change_percent'] = real_info.get('change_percent')
                        except Exception as info_err:
                            logger.warning(f"Could not enrich technical data with real info for {symbol}: {info_err}")
                except Exception as calc_err:
                    logger.error(f"Technical calc error for {symbol}: {calc_err}")
                    technical_data = None
            if technical_data:
                return render_template('analysis/technical.html',
                                     symbol=symbol,
                                     technical_data=technical_data,
                                     show_analysis=True,
                                     show_search_prompt=False)
            else:
                return render_template('analysis/technical.html',
                                     symbol=symbol,
                                     technical_data=None,
                                     show_analysis=True,
                                     show_search_prompt=False,
                                     error=("Ugyldig symbol." if not valid else "Ingen tekniske data tilgjengelig for valgt ticker."))
        else:
            # Show technical analysis overview with popular stocks
            popular_stocks = []
            oslo_tickers = ['EQNR.OL', 'DNB.OL', 'YAR.OL', 'MOWI.OL', 'TEL.OL']
            global_tickers = ['AAPL', 'TSLA', 'MSFT', 'AMZN', 'GOOGL']
            
            for ticker in oslo_tickers + global_tickers:
                popular_stocks.append({
                    'symbol': ticker,
                    'name': ticker.replace('.OL', ' ASA'),
                    'price': 100.0 + hash(ticker) % 200,
                    'change_percent': (hash(ticker) % 10) - 5
                })
            
            return render_template('analysis/technical.html',
                                 popular_stocks=popular_stocks,
                                 show_analysis=False,
                                 show_search_prompt=True)
                                 
    except Exception as e:
        logger.error(f"Error in technical analysis: {e}")
        # Return fallback page
        return render_template('analysis/technical.html',
                             symbol=request.args.get('symbol', ''),
                             show_analysis=bool(request.args.get('symbol')),
                             error="Teknisk analyse er midlertidig utilgjengelig")

@analysis.route('/warren-buffett-simple', methods=['GET', 'POST'])
@access_required
def warren_buffett_simple():
    """Simplified Warren Buffett analysis (kept for reference / lightweight demo).

    NOTE: The enhanced unified implementation now lives in `routes/analysis.py`.
    This simplified version is exposed at /analysis/warren-buffett-simple to avoid
    duplicate route conflicts on /analysis/warren-buffett. Consider removing after
    verification period if no longer needed.
    TODO: After confirming /analysis/warren-buffett stable in production for 14 days,
    remove this route and associated simplified logic to reduce maintenance overhead.
    """
    ticker = request.args.get('ticker') or request.form.get('ticker')

    if ticker and request.method in ['GET', 'POST']:
        ticker = ticker.strip().upper()
        try:
            # Mock Warren Buffett analysis
            analysis_data = {
                'ticker': ticker,
                'buffett_score': 75.5,
                'intrinsic_value': 180.0,
                'current_price': 150.0,
                'margin_of_safety': 16.7
            }
            
            return render_template('analysis/warren_buffett.html',
                                 analysis=analysis_data,
                                 ticker=ticker)
                                      
        except Exception as e:
            logger.error(f"Error in Warren Buffett analysis for {ticker}: {e}")
            flash('Feil ved analyse. Prøv igjen senere.', 'error')

    # Show selection page (selection lists / no ticker submitted)
    try:
        oslo_stocks = {
            'EQNR.OL': {'name': 'Equinor ASA', 'last_price': 270.50, 'change_percent': 1.2},
            'DNB.OL': {'name': 'DNB Bank ASA', 'last_price': 185.20, 'change_percent': -0.8},
            'TEL.OL': {'name': 'Telenor ASA', 'last_price': 125.30, 'change_percent': 0.5},
            'YAR.OL': {'name': 'Yara International', 'last_price': 350.80, 'change_percent': 2.1},
            'MOWI.OL': {'name': 'Mowi ASA', 'last_price': 198.40, 'change_percent': -1.3}
        }
        global_stocks = {
            'AAPL': {'name': 'Apple Inc.', 'last_price': 185.00, 'change_percent': 0.9},
            'MSFT': {'name': 'Microsoft Corporation', 'last_price': 420.50, 'change_percent': 1.5},
            'GOOGL': {'name': 'Alphabet Inc.', 'last_price': 140.20, 'change_percent': -0.3},
            'TSLA': {'name': 'Tesla Inc.', 'last_price': 220.80, 'change_percent': 3.2},
            'AMZN': {'name': 'Amazon.com Inc.', 'last_price': 155.90, 'change_percent': 0.7}
        }
        return render_template('analysis/warren_buffett.html',
                               oslo_stocks=oslo_stocks,
                               global_stocks=global_stocks,
                               analysis=None)
    except Exception as e:
        logger.error(f"Error loading Buffett selection page: {e}")
        flash('Kunne ikke laste aksjeoversikt. Prøv igjen senere.', 'error')
        return render_template('analysis/warren_buffett.html',
                               oslo_stocks={},
                               global_stocks={},
                               analysis=None)

@analysis.route('/market-overview')
@analysis.route('/market_overview')
@access_required
def market_overview():
    """Market overview page with simplified error handling"""
    try:
        # Fallback market data
        oslo_data = {
            'EQNR.OL': {'name': 'Equinor ASA', 'last_price': 270.50, 'change_percent': 1.2, 'volume': 1250000, 'change': 3.20},
            'DNB.OL': {'name': 'DNB Bank ASA', 'last_price': 185.20, 'change_percent': -0.8, 'volume': 890000, 'change': -1.48},
            'TEL.OL': {'name': 'Telenor ASA', 'last_price': 125.30, 'change_percent': 0.5, 'volume': 720000, 'change': 0.63},
            'YAR.OL': {'name': 'Yara International', 'last_price': 350.80, 'change_percent': 2.1, 'volume': 450000, 'change': 7.22},
            'MOWI.OL': {'name': 'Mowi ASA', 'last_price': 198.40, 'change_percent': -1.3, 'volume': 680000, 'change': -2.61},
            'NHY.OL': {'name': 'Norsk Hydro ASA', 'last_price': 42.85, 'change_percent': 1.8, 'volume': 2100000, 'change': 0.76},
            'ORK.OL': {'name': 'Orkla ASA', 'last_price': 82.15, 'change_percent': 0.3, 'volume': 390000, 'change': 0.25},
            'SALM.OL': {'name': 'SalMar ASA', 'last_price': 485.20, 'change_percent': 2.8, 'volume': 180000, 'change': 13.21},
            'AKER.OL': {'name': 'Aker ASA', 'last_price': 520.00, 'change_percent': -0.9, 'volume': 75000, 'change': -4.71},
            'FRO.OL': {'name': 'Frontline plc', 'last_price': 155.90, 'change_percent': 3.4, 'volume': 620000, 'change': 5.12}
        }
        
        global_data = {
            'AAPL': {'name': 'Apple Inc.', 'last_price': 185.00, 'change_percent': 0.9, 'volume': 58000000, 'change': 1.65},
            'MSFT': {'name': 'Microsoft Corporation', 'last_price': 420.50, 'change_percent': 1.5, 'volume': 24000000, 'change': 6.22},
            'GOOGL': {'name': 'Alphabet Inc.', 'last_price': 140.20, 'change_percent': -0.3, 'volume': 28000000, 'change': -0.42},
            'TSLA': {'name': 'Tesla Inc.', 'last_price': 220.80, 'change_percent': 3.2, 'volume': 95000000, 'change': 6.84},
            'AMZN': {'name': 'Amazon.com Inc.', 'last_price': 155.90, 'change_percent': 0.7, 'volume': 41000000, 'change': 1.08},
            'NVDA': {'name': 'NVIDIA Corporation', 'last_price': 485.25, 'change_percent': 2.1, 'volume': 38000000, 'change': 9.98},
            'META': {'name': 'Meta Platforms Inc.', 'last_price': 328.75, 'change_percent': -1.2, 'volume': 18000000, 'change': -3.99},
            'NFLX': {'name': 'Netflix Inc.', 'last_price': 448.90, 'change_percent': 1.8, 'volume': 5200000, 'change': 7.94},
            'AMD': {'name': 'Advanced Micro Devices', 'last_price': 142.30, 'change_percent': 4.2, 'volume': 48000000, 'change': 5.74},
            'CRM': {'name': 'Salesforce Inc.', 'last_price': 285.40, 'change_percent': 0.8, 'volume': 3800000, 'change': 2.26}
        }
        
        crypto_data = {
            'BTC-USD': {'name': 'Bitcoin', 'price': 43500, 'change_24h': 2.5, 'volume': 25000000000, 'market_cap': 850000000000},
            'ETH-USD': {'name': 'Ethereum', 'price': 2650, 'change_24h': 1.8, 'volume': 12000000000, 'market_cap': 318000000000},
            'BNB-USD': {'name': 'BNB', 'price': 385, 'change_24h': -0.9, 'volume': 1800000000, 'market_cap': 57000000000},
            'ADA-USD': {'name': 'Cardano', 'price': 0.48, 'change_24h': 3.2, 'volume': 480000000, 'market_cap': 17000000000},
            'SOL-USD': {'name': 'Solana', 'price': 108.50, 'change_24h': 5.1, 'volume': 2400000000, 'market_cap': 48000000000},
            'XRP-USD': {'name': 'XRP', 'price': 0.62, 'change_24h': 1.4, 'volume': 1200000000, 'market_cap': 35000000000},
            'DOT-USD': {'name': 'Polkadot', 'price': 7.85, 'change_24h': 2.8, 'volume': 190000000, 'market_cap': 9800000000},
            'AVAX-USD': {'name': 'Avalanche', 'price': 38.20, 'change_24h': -1.6, 'volume': 820000000, 'market_cap': 15000000000}
        }
        
        currency_data = {
            'USDNOK=X': {'name': 'USD/NOK', 'rate': 10.25, 'change_percent': 0.5}
        }
        
        market_summaries = {
            'oslo': {'index_value': 1200.0, 'change': 12.5, 'change_percent': 1.05},
            'global_market': {'index_value': 4500.0, 'change': 45.2, 'change_percent': 1.01},
            'crypto': {'index_value': 43500.0, 'change': 1000.0, 'change_percent': 2.35},
            'currency': {'usd_nok': 10.25, 'usd_nok_change': 0.5}
        }
        
        return render_template('analysis/market_overview.html',
                             oslo_stocks=oslo_data,
                             global_stocks=global_data,
                             crypto_data=crypto_data,
                             currency=currency_data,
                             currency_data=currency_data,
                             market_summaries=market_summaries)
                             
    except Exception as e:
        logger.error(f"Critical error in market overview: {e}", exc_info=True)
        return render_template('error.html',
                             error="Markedsoversikt er midlertidig utilgjengelig. Prøv igjen senere.")

# Duplicate sentiment route removed in favor of unified implementation in analysis.py
# (left commented intentionally for historical context / potential reference)
# @analysis.route('/sentiment')
# @access_required
# def sentiment():
#     pass

@analysis.route('/recommendations')
@analysis.route('/recommendations/')
@analysis.route('/recommendations/<symbol>')
@access_required
def recommendations(symbol=None):
    """Stock recommendations.

    Policy: No fabricated AI/analyst data for authenticated premium users.
    Demo/free users still see illustrative demo content (clearly marked).
    """
    try:
        premium_real = current_user.is_authenticated

        # Detail view
        if symbol:
            symbol = symbol.strip().upper()
            if premium_real:
                real_info = None
                if DataService and hasattr(DataService, 'get_stock_info'):
                    try:
                        real_info = DataService.get_stock_info(symbol)
                    except Exception as ds_err:
                        logger.warning(f"DataService error for {symbol}: {ds_err}")
                ai_detail = None
                if hasattr(DataService, 'get_ticker_specific_ai_recommendation'):
                    try:
                        ai_detail = DataService.get_ticker_specific_ai_recommendation(symbol)
                    except Exception as ai_err:
                        logger.warning(f"AI recommendation fetch error for {symbol}: {ai_err}")
                if real_info:
                    price = (real_info.get('last_price') or real_info.get('regularMarketPrice')
                             or real_info.get('currentPrice'))
                    if not price:
                        price = real_info.get('price') or 0
                    rating = None
                    confidence = None
                    risk_level = None
                    timeframe = None
                    reasons = []
                    risks = []
                    target_price = None
                    upside = None
                    if ai_detail:
                        rating = ai_detail.get('recommendation') or ai_detail.get('rating')
                        confidence = ai_detail.get('confidence') or ai_detail.get('confidence_score')
                        risk_level = ai_detail.get('risk_level') or ai_detail.get('risk')
                        timeframe = ai_detail.get('timeframe') or '12 mnd'
                        reasons = ai_detail.get('reasons') or []
                        target_price = ai_detail.get('price_target') or ai_detail.get('target_price')
                        if price and target_price:
                            try:
                                upside = round(((target_price / price) - 1) * 100, 1)
                            except Exception:
                                upside = None
                    detail = {
                        'symbol': symbol,
                        'name': real_info.get('name') or real_info.get('longName') or real_info.get('shortName') or symbol,
                        'current_price': price,
                        'target_price': target_price,
                        'upside': upside,
                        'rating': rating,
                        'confidence': confidence,
                        'risk_level': risk_level,
                        'timeframe': timeframe,
                        'reasons': reasons,
                        'risks': risks,
                        'sector': real_info.get('sector'),
                        'analyst_count': None,
                        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'price_targets': None,
                        'analyst_ratings': None,
                        'key_metrics': {
                            'pe_ratio': real_info.get('trailingPE') or real_info.get('pe_ratio'),
                            'pb_ratio': real_info.get('priceToBook') or real_info.get('pb_ratio'),
                            'dividend_yield': real_info.get('dividendYield'),
                            'roe': None
                        },
                        'real_data': True,
                        'demo': False,
                        'simulated': False,
                        'notice': 'Ekte data lastet' + (' med AI-analyse' if ai_detail else ' (AI-detaljer ikke tilgjengelig)')
                    }
                else:
                    # Premium bruker men ingen real_info: vis tom mal, ikke demo
                    detail = {
                        'symbol': symbol,
                        'name': symbol,
                        'current_price': None,
                        'target_price': None,
                        'upside': None,
                        'rating': None,
                        'confidence': None,
                        'risk_level': None,
                        'timeframe': None,
                        'reasons': [],
                        'risks': [],
                        'sector': None,
                        'analyst_count': None,
                        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'price_targets': None,
                        'analyst_ratings': None,
                        'key_metrics': {},
                        'real_data': False,
                        'demo': False,
                        'simulated': True,
                        'notice': 'Ingen ekte data tilgjengelig – tom mal.'
                    }
                return render_template('analysis/recommendation_detail.html',
                                       recommendation=detail,
                                       symbol=symbol,
                                       page_title=f"Anbefaling for {symbol}")
            # Demo detail (free/unauthenticated)
            hash_seed = abs(hash(symbol)) % 1000
            demo_detail = {
                'symbol': symbol,
                'name': f"{symbol.replace('.OL', ' ASA').replace('-USD', '')} (Demo)",
                'current_price': None,
                'target_price': None,
                'upside': None,
                'rating': None,
                'confidence': None,
                'risk_level': None,
                'timeframe': '12 months',
                'reasons': ['(Demo) Illustrativ grunn'],
                'risks': ['(Demo) Illustrativ risiko'],
                'sector': 'Demo',
                'analyst_count': 0,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'price_targets': None,
                'analyst_ratings': None,
                'key_metrics': {},
                'demo': True,
                'real_data': False,
                'simulated': False,
                'notice': 'Demo-data. Logg inn / oppgrader for ekte markedsinfo.'
            }
            return render_template('analysis/recommendation_detail.html',
                                   recommendation=demo_detail,
                                   symbol=symbol,
                                   page_title=f"Anbefaling (Demo) {symbol}")

        # Overview list
        if premium_real:
            from ..services.data_service import DataService as _DS  # type: ignore
            try:
                oslo_overview = _DS.get_oslo_bors_overview() or {}
            except Exception as e:
                logger.warning(f"Oslo overview fetch failed: {e}")
                oslo_overview = {}
            try:
                global_overview = _DS.get_global_stocks_overview() or {}
            except Exception as e:
                logger.warning(f"Global overview fetch failed: {e}")
                global_overview = {}

            def _real(d):
                return {k: v for k, v in d.items() if v.get('source') != 'GUARANTEED DATA'}
            oslo_real = _real(oslo_overview)
            global_real = _real(global_overview)

            all_real = {}
            all_real.update(oslo_real)
            all_real.update(global_real)

            if not all_real:
                empty_real = {
                    'featured_picks': [],
                    'top_performers': [],
                    'sector_recommendations': {},
                    'market_outlook': None,
                    'demo': False,
                    'real_data': True,
                    'notice': 'Ingen ekte markedsdata tilgjengelig akkurat nå.'
                }
                return render_template('analysis/recommendations.html',
                                       recommendations=empty_real,
                                       page_title="AI Anbefalinger")

            # Konstruer sektor mapping hvis mulig (bruk name heuristikk hvis sektor ikke finnes)
            # For nå mangler sektorinfo i oversikt-data; vi grupperer etter enkel regel (første bokstav) som placeholder
            # Dette er ekte avledet struktur (ikke påstand om AI/analyst), derfor lov å vise.
            sector_perf = {}
            for sym, data in all_real.items():
                sector = data.get('sector') or f"SEKTOR-{sym[0]}"  # midlertidig heuristikk
                chg_pct = data.get('change_percent')
                if chg_pct is None:
                    continue
                bucket = sector_perf.setdefault(sector, {'symbols': 0, 'change_sum': 0.0})
                bucket['symbols'] += 1
                try:
                    bucket['change_sum'] += float(chg_pct)
                except Exception:
                    pass

            sector_recommendations = {}
            for sector, agg in sector_perf.items():
                avg = agg['change_sum'] / agg['symbols'] if agg['symbols'] else 0.0
                if avg > 1.0:
                    rating = 'OVERWEIGHT'
                elif avg < -1.0:
                    rating = 'UNDERWEIGHT'
                else:
                    rating = 'NEUTRAL'
                sector_recommendations[sector] = {
                    'rating': rating,
                    'outlook': f"Gj.sn endring {avg:.2f}% basert på {agg['symbols']} aksjer",
                    'drivers': []
                }

            # Topp bevegere som "featured" (ikke AI anbefalinger, bare markert movers)
            movers = []
            for sym, data in all_real.items():
                try:
                    movers.append((sym, float(data.get('change_percent', 0)), data))
                except Exception:
                    continue
            movers.sort(key=lambda x: x[1], reverse=True)
            top = movers[:5]
            featured = []
            for sym, pct, data in top:
                price = data.get('last_price') or data.get('price') or 0
                featured.append({
                    'symbol': sym,
                    'name': data.get('name', sym),
                    'current_price': price,
                    'target_price': None,  # Ikke generere fiktivt kursmål
                    'upside': None,        # Ingen kalkulert oppside
                    'rating': 'HOLD',      # Nøytral; vi genererer ikke AI rating
                    'confidence': 0,       # Ingen AI confidence
                    'risk_level': None,
                    'timeframe': None,
                    'reasons': ["Nylig positiv kursbevegelse" if pct > 0 else "Nylig negativ kursbevegelse"],
                    'sector': data.get('sector'),
                    'analyst_count': None,
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M')
                })

            # Market outlook avledet
            pos = sum(1 for _, pct, _ in movers if pct > 0)
            neg = sum(1 for _, pct, _ in movers if pct < 0)
            total_considered = len(movers) or 1
            breadth = pos / total_considered
            if breadth > 0.6:
                sentiment = 'POSITIV'
            elif breadth < 0.4:
                sentiment = 'NEGATIV'
            else:
                sentiment = 'NØYTRAL'
            market_outlook = {
                'overall_sentiment': sentiment,
                'key_themes': [f"Markedsbredde {breadth*100:.0f}% positiv"],
                'risk_factors': ["Automatisk generert – ingen AI analyse"],
                'generated_from': 'REAL DATA'
            }

            real_overview = {
                'featured_picks': featured,
                'top_performers': featured,  # gjenbruk for nå
                'sector_recommendations': sector_recommendations,
                'market_outlook': market_outlook,
                'demo': False,
                'real_data': True,
                'notice': 'Ekte markedsdata – ingen AI-prisanslag eller kursmål generert.'
            }
            return render_template('analysis/recommendations.html',
                                   recommendations=real_overview,
                                   page_title="AI Anbefalinger (Ekte data – begrenset)")

        # Demo overview
        demo_overview = {
            'featured_picks': [
                {'symbol': 'DNB.OL','name': 'DNB Bank ASA','current_price': 185.20,'target_price': 210.00,'upside': 13.4,'rating': 'STRONG_BUY','confidence': 92,'risk_level': 'Medium','timeframe': '12 months','reasons': ['(Demo) Eksempel'], 'sector': 'Banking','analyst_count': 0,'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M')},
                {'symbol': 'EQNR.OL','name': 'Equinor ASA','current_price': 270.50,'target_price': 295.00,'upside': 9.1,'rating': 'BUY','confidence': 88,'risk_level': 'Medium','timeframe': '12 months','reasons': ['(Demo) Eksempel'],'sector': 'Energy','analyst_count': 0,'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M')},
                {'symbol': 'AAPL','name': 'Apple Inc.','current_price': 185.00,'target_price': 210.00,'upside': 13.5,'rating': 'BUY','confidence': 85,'risk_level': 'Low','timeframe': '12 months','reasons': ['(Demo) Eksempel'],'sector': 'Technology','analyst_count': 0,'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M')}
            ],
            'top_performers': [],
            'sector_recommendations': {},
            'market_outlook': None,
            'demo': True,
            'real_data': False,
            'notice': 'Demo-visning. Ingen ekte anbefalingstall.'
        }
        return render_template('analysis/recommendations.html',
                               recommendations=demo_overview,
                               page_title="AI Anbefalinger (Demo)")
    except Exception as e:
        logger.error(f"Error in recommendations: {e}")
        return render_template('error.html',
                               error="Anbefalinger er midlertidig utilgjengelig.")

@analysis.route('/screener', methods=['GET', 'POST'])
@access_required
def screener():
    """Stock screener with basic functionality"""
    try:
        results = []
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
        
        if request.method == 'POST':
            # Mock screener results
            results = [
                {
                    'ticker': 'EQNR.OL',
                    'name': 'Equinor ASA',
                    'price': 320.50,
                    'change_percent': 2.5,
                    'volume': '1.2M',
                    'market_cap': '1020B',
                    'pe_ratio': 12.4,
                    'dividend_yield': 5.2,
                    'sector': 'Energy'
                }
            ]
        
        return render_template('analysis/screener.html',
                             results=results,
                             show_results=bool(results),
                             preset_screens=preset_screens)
                             
    except Exception as e:
        logger.error(f"Error in screener: {e}")
        return render_template('error.html',
                             error="Screener er midlertidig utilgjengelig.")

@analysis.route('/benjamin-graham', methods=['GET', 'POST'])
@access_required
def benjamin_graham():
    """Benjamin Graham value analysis"""
    try:
        ticker = request.args.get('ticker') or request.form.get('ticker')
        if ticker:
            ticker = ticker.strip().upper()
            
            # Mock analysis data
            analysis_data = {
                'ticker': ticker,
                'graham_score': 78.5,
                'intrinsic_value': 195.00,
                'current_price': 185.20,
                'margin_of_safety': 5.3,
                'criteria_met': ['Low P/E ratio', 'Strong balance sheet', 'Consistent earnings'],
                'criteria_failed': ['Limited growth'],
                'financial_metrics': {'pe_ratio': 11.2, 'pb_ratio': 1.1},
                'recommendation': {
                    'action': 'BUY',
                    'reasoning': f"Graham score of 78.5 indicates strong value proposition"
                },
                'company_name': f"Company Analysis for {ticker}",
                'sector': 'Financial Services'
            }

            return render_template('analysis/benjamin_graham_select.html',
                                 analysis=analysis_data, ticker=ticker)
        
        # Show selection page
        oslo_stocks = {
            'EQNR.OL': {'name': 'Equinor ASA', 'last_price': 270.50},
            'DNB.OL': {'name': 'DNB Bank ASA', 'last_price': 185.20}
        }
        global_stocks = {
            'AAPL': {'name': 'Apple Inc.', 'last_price': 185.00},
            'MSFT': {'name': 'Microsoft Corporation', 'last_price': 420.50}
        }
        return render_template('analysis/benjamin_graham_select.html',
                             oslo_stocks=oslo_stocks, global_stocks=global_stocks, analysis=None)
    except Exception as e:
        logger.error(f"Error in Benjamin Graham analysis: {e}")
        return render_template('error.html', error="Benjamin Graham analyse er midlertidig utilgjengelig.")

@analysis.route('/sentiment-view')
@access_required  
def sentiment_view():
    """Sentiment analysis view"""
    return redirect(url_for('analysis.sentiment'))

@analysis.route('/insider-trading')
@access_required
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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analysis.route('/ai')
@analysis.route('/ai/<ticker>')
@access_required
def ai(ticker=None):
    """AI-powered stock analysis"""
    try:
        # Get ticker from URL parameter, query string, or form
        if not ticker:
            ticker = request.args.get('ticker') or request.form.get('ticker')
        
        if ticker:
            ticker = ticker.strip().upper()
            cache_key = f"ai_analysis_{ticker}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data
            # Demo-advarsel for innloggede brukere
            demo_warning = None
            if current_user.is_authenticated:
                demo_warning = "Dette er kun en demo. Ingen reelle AI-data tilgjengelig for innloggede brukere."
            ai_analysis = None
            result = render_template('analysis/ai.html', 
                                   analysis=ai_analysis,
                                   ticker=ticker,
                                   demo_warning=demo_warning)
            cache.set(cache_key, result, timeout=1800)
            return result
        else:
            return render_template('analysis/ai_form.html', demo_warning="Dette er kun en demo. Ingen reelle AI-data tilgjengelig.")
    except Exception as e:
        logger.error(f'AI analysis error: {str(e)}')
        flash(f'Feil ved lasting av AI-analyse: {str(e)}', 'error')
        return render_template('analysis/ai_form.html')

@analysis.route('/short-analysis')
@analysis.route('/short-analysis/<ticker>')
@access_required
def short_analysis(ticker=None):
    """Short selling analysis"""
    try:
        if ticker:
            cache_key = f"short_analysis_{ticker}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data
            demo_warning = None
            if current_user.is_authenticated:
                demo_warning = "Dette er kun en demo. Ingen reelle short-data tilgjengelig for innloggede brukere."
            short_data = None
            result = render_template('analysis/short_analysis.html', 
                                   short_data=short_data,
                                   ticker=ticker,
                                   demo_warning=demo_warning)
            cache.set(cache_key, result, timeout=1800)
            return result
        else:
            return render_template('analysis/short_analysis_select.html', demo_warning="Dette er kun en demo. Ingen reelle short-data tilgjengelig.")
    except Exception as e:
        flash(f'Feil ved lasting av short-analyse: {str(e)}', 'error')
        return render_template('analysis/short_analysis_select.html')

@analysis.route('/ai-predictions')
@analysis.route('/ai-predictions/<ticker>')
@access_required
def ai_predictions(ticker=None):
    """AI predictions for stocks"""
    try:
        if ticker:
            cache_key = f"ai_predictions_{ticker}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data
            demo_warning = None
            if current_user.is_authenticated:
                demo_warning = "Dette er kun en demo. Ingen reelle AI-prediksjoner tilgjengelig for innloggede brukere."
            predictions = None
            result = render_template('analysis/ai_predictions.html', 
                                   predictions=predictions,
                                   ticker=ticker,
                                   demo_warning=demo_warning)
            cache.set(cache_key, result, timeout=1800)
            return result
        else:
            return render_template('analysis/ai_predictions_select.html', demo_warning="Dette er kun en demo. Ingen reelle AI-prediksjoner tilgjengelig.")
    except Exception as e:
        flash(f'Feil ved lasting av AI-prediksjoner: {str(e)}', 'error')
        return render_template('analysis/ai_predictions_select.html')

@analysis.route('/fundamental', methods=['GET', 'POST'])
@analysis.route('/fundamental/', methods=['GET', 'POST'])
@analysis.route('/fundamental/<ticker>', methods=['GET', 'POST'])
@access_required
def fundamental(ticker=None):
    """Fundamental analysis"""
    try:
        # Get ticker from URL parameter or query string
        if not ticker:
            ticker = request.args.get('ticker') or request.form.get('ticker')
            
        if ticker and ticker.strip():
            ticker = ticker.strip().upper()
            logger.info(f"Fundamental analysis requested for: {ticker}")
            fundamental_data = None
            if DataService and hasattr(DataService, 'get_stock_info'):
                try:
                    info = DataService.get_stock_info(ticker)
                    if info:
                        # Map available fields to expected keys
                        fundamental_data = {
                            'ticker': ticker,
                            'company_name': info.get('name', f"{ticker} Corporation"),
                            'sector': info.get('sector', 'Ukjent'),
                            'market_cap': info.get('market_cap'),
                            'current_price': info.get('last_price'),
                            'financial_metrics': {
                                'pe_ratio': info.get('pe_ratio'),
                                'pb_ratio': info.get('pb_ratio'),
                                'dividend_yield': info.get('dividend_yield'),
                                'roe': info.get('roe'),
                                'debt_to_equity': info.get('debt_to_equity'),
                            },
                            'analysis_summary': {
                                'strengths': info.get('strengths', []),
                                'weaknesses': info.get('weaknesses', []),
                                'recommendation': info.get('recommendation', 'Ingen'),
                                'confidence_level': info.get('confidence', 'Ukjent'),
                                'time_horizon': info.get('horizon', '12 months')
                            }
                        }
                except Exception as svc_err:
                    logger.error(f"DataService fundamental error for {ticker}: {svc_err}")
                    fundamental_data = None
            if fundamental_data:
                logger.info(f"Rendering real fundamental analysis for {ticker}")
                result = render_template('analysis/fundamental.html', 
                                       symbol=ticker,
                                       ticker=ticker,
                                       analysis_data=fundamental_data,
                                       data=fundamental_data)
                return result
            else:
                logger.info(f"No real data for {ticker}, showing info message.")
                return render_template('analysis/fundamental.html', 
                                       symbol=ticker,
                                       ticker=ticker,
                                       analysis_data=None,
                                       data=None,
                                       error="Ingen fundamentaldata tilgjengelig for valgt ticker.")
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

@analysis.route('/recommendation')
@access_required
def recommendation():
    """Investment recommendations page"""
    return render_template('analysis/recommendation.html', title='Investeringsanbefalinger')

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
@access_required
def currency_overview():
    """Currency market overview"""
    from datetime import datetime
    
    from ..routes.dashboard import get_currency_rates
    rates = get_currency_rates()
    # Convert rates dict to expected currencies format for template
    currencies = {}
    for k, v in rates.items():
        pair = f"{k}/NOK"
        currencies[pair] = {
            'rate': v,
            'change': None,
            'change_percent': None
        }
    return render_template('analysis/currency_overview.html', 
                         title='Valutaoversikt',
                         currencies=currencies,
                         now=datetime.now())

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
