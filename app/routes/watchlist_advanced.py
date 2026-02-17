from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from ..models.user import User
from ..models.watchlist import Watchlist, WatchlistItem
from ..extensions import db, mail, csrf
from ..utils.symbol_utils import sanitize_symbol
from ..utils.access_control import demo_access
from flask_mailman import EmailMessage
from datetime import datetime, timedelta
try:
    import yfinance as yf
except ImportError:
    yf = None
# import pandas as pd
# import numpy as np
import json
import os

watchlist_bp = Blueprint('watchlist_advanced', __name__)

# --- WATCHLIST API ENDPOINTS ---
@watchlist_bp.route('/api/watchlist/check/<symbol>', methods=['GET'])
@login_required
def check_watchlist(symbol):
    """Sjekk om aksje er i brukerens watchlist"""
    try:
        symbol, valid = sanitize_symbol(symbol)
        if not valid:
            return jsonify({'inWatchlist': False, 'error': 'Ugyldig symbol'}), 400
        watchlist = Watchlist.query.filter_by(user_id=current_user.id).order_by(Watchlist.id).first()
        if not watchlist:
            return jsonify({'inWatchlist': False})
        
        item = WatchlistItem.query.filter_by(watchlist_id=watchlist.id, symbol=symbol).first()
        return jsonify({
            'inWatchlist': bool(item),
            'watchlistId': watchlist.id if item else None
        })
    except Exception as e:
        current_app.logger.error(f"Error checking watchlist status: {str(e)}")
        return jsonify({'error': 'Could not check watchlist status'}), 500

@watchlist_bp.route('/api/watchlist/toggle', methods=['POST'])
@login_required
def toggle_watchlist():
    """Toggle aksje i watchlist"""
    try:
        data = request.get_json()
        if not data or 'symbol' not in data:
            return jsonify({'success': False, 'error': 'Symbol er påkrevd'}), 400
        
        raw_symbol = data['symbol']
        symbol, valid = sanitize_symbol(raw_symbol)
        if not valid:
            return jsonify({'success': False, 'error': 'Ugyldig symbol'}), 400
        
        # Get or create default watchlist
        watchlist = Watchlist.query.filter_by(user_id=current_user.id).order_by(Watchlist.id).first()
        if not watchlist:
            watchlist = Watchlist(name="Min Watchlist", user_id=current_user.id)
            db.session.add(watchlist)
            db.session.commit()
        
        # Check if already in list
        item = WatchlistItem.query.filter_by(watchlist_id=watchlist.id, symbol=symbol).first()
        
        if item:
            # Remove if exists
            db.session.delete(item)
            db.session.commit()
            return jsonify({
                'success': True,
                'inWatchlist': False,
                'message': f'{symbol} fjernet fra watchlist'
            })
        else:
            # Add if doesn't exist
            item = WatchlistItem(
                watchlist_id=watchlist.id,
                symbol=symbol,
                added_at=datetime.now()
            )
            db.session.add(item)
            db.session.commit()
            return jsonify({
                'success': True, 
                'inWatchlist': True,
                'message': f'{symbol} lagt til i watchlist'
            })
            
    except Exception as e:
        current_app.logger.error(f"Error toggling watchlist: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Kunne ikke oppdatere watchlist'
        }), 500


@watchlist_bp.route('/api/watchlist/add', methods=['POST'])
def add_to_watchlist():
    """Add aksje til favorittlisten (hoved-watchlist)"""
    try:
        data = request.get_json()
        if not data or 'symbol' not in data:
            return jsonify({'success': False, 'error': 'Symbol er påkrevd'}), 400
        
        raw_symbol = data['symbol']
        symbol, valid = sanitize_symbol(raw_symbol)
        if not valid:
            return jsonify({'success': False, 'error': 'Ugyldig symbol'}), 400
        
        # For demo/unauthenticated users, just return success
        if not current_user.is_authenticated:
            return jsonify({
                'success': True,
                'favorite': True,
                'message': f'{symbol} lagt til i favoritter (demo mode).'
            })
        
        # Get or create default watchlist
        watchlist = Watchlist.query.filter_by(user_id=current_user.id).order_by(Watchlist.id).first()
        if not watchlist:
            watchlist = Watchlist(name="Min Watchlist", user_id=current_user.id)
            db.session.add(watchlist)
            db.session.commit()
        
        # Check if already in list
        existing_item = WatchlistItem.query.filter_by(watchlist_id=watchlist.id, symbol=symbol).first()
        if existing_item:
            return jsonify({
                'success': True,
                'favorite': True,
                'message': f'{symbol} er allerede i favoritter.'
            })
        
        # Add new item
        item = WatchlistItem(
            watchlist_id=watchlist.id,
            symbol=symbol,
            added_at=datetime.now()
        )
        db.session.add(item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'favorite': True,
            'message': f'{symbol} lagt til i favoritter.'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error adding to watchlist: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Kunne inte legge til i favoritter'
        }), 500


@watchlist_bp.route('/api/watchlist/remove', methods=['POST'])
@login_required
def remove_from_watchlist():
    """Fjern aksje fra favorittlisten (hoved-watchlist)"""
    try:
        data = request.get_json()
        if not data or 'symbol' not in data:
            return jsonify({'success': False, 'error': 'Symbol er påkrevd'}), 400
        
        raw_symbol = data['symbol']
        symbol, valid = sanitize_symbol(raw_symbol)
        if not valid:
            return jsonify({'success': False, 'error': 'Ugyldig symbol'}), 400
        watchlist = Watchlist.query.filter_by(user_id=current_user.id).order_by(Watchlist.id).first()
        
        if not watchlist:
            return jsonify({
                'success': False,
                'favorite': False,
                'message': 'Ingen favorittliste funnet.'
            }), 404
        
        item = WatchlistItem.query.filter_by(watchlist_id=watchlist.id, symbol=symbol).first()
        if not item:
            return jsonify({
                'success': False,
                'favorite': False,
                'message': f'{symbol} ikke i favoritter.'
            }), 404
        
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'favorite': False,
            'message': f'{symbol} fjernet fra favoritter.'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error removing from watchlist: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Kunne ikke fjerne fra favoritter'
        }), 500
    return jsonify({'favorite': False, 'message': f'{symbol} fjernet fra favoritter.'}), 200

class WatchlistAnalyzer:
    """AI-basert watchlist-analyse og varsling"""
    
    def __init__(self):
        self.alert_thresholds = {
            'price_change': 0.05,  # 5% prisendring
            'volume_spike': 2.0,   # 200% volum økning
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'macd_signal': True
        }
    
    def get_stock_data(self, symbol, period="5d"):
        """Hent ferske aksjedata"""
        try:
            if yf is not None:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                info = ticker.info
            else:
                # Return fallback data when yfinance is not available
                return {
                    'price': 100.0 + (hash(symbol) % 100),
                    'change': ((hash(symbol) % 21) - 10) / 10,
                    'change_percent': ((hash(symbol) % 21) - 10) / 10,
                    'volume': 1000000 + (hash(symbol) % 500000),
                    'sma20': 100.0,
                    'sma50': 100.0,
                    'rsi': 50.0,
                    'note': 'Fallback data - yfinance not available'
                }
            
            if hist.empty:
                return None
                
            latest = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else latest
            
            # Beregn tekniske indikatorer
            prices = hist['Close']
            
            # RSI beregning
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # MACD beregning
            ema12 = prices.ewm(span=12).mean()
            ema26 = prices.ewm(span=26).mean()
            macd = ema12 - ema26
            macd_signal = macd.ewm(span=9).mean()
            
            return {
                'symbol': symbol,
                'current_price': latest['Close'],
                'previous_price': previous['Close'],
                'price_change': (latest['Close'] - previous['Close']) / previous['Close'],
                'volume': latest['Volume'],
                'avg_volume': hist['Volume'].rolling(window=20).mean().iloc[-1],
                'rsi': rsi.iloc[-1] if not rsi.empty else 50,
                'macd': macd.iloc[-1] if not macd.empty else 0,
                'macd_signal': macd_signal.iloc[-1] if not macd_signal.empty else 0,
                'high_52w': info.get('fiftyTwoWeekHigh', latest['High']),
                'low_52w': info.get('fiftyTwoWeekLow', latest['Low']),
                'market_cap': info.get('marketCap', 0),
                'company_name': info.get('longName', symbol),
                'timestamp': datetime.now()
            }
        except Exception as e:
            current_app.logger.error(f"Feil ved henting av data for {symbol}: {e}")
            return None
    
    def analyze_alerts(self, stock_data, user_preferences):
        """Analyser om aksjen trigger noen varsler"""
        alerts = []
        
        if not stock_data:
            return alerts
        
        # Prisendring varsel
        if abs(stock_data['price_change']) >= self.alert_thresholds['price_change']:
            direction = "opp" if stock_data['price_change'] > 0 else "ned"
            alerts.append({
                'type': 'price_change',
                'severity': 'high' if abs(stock_data['price_change']) > 0.1 else 'medium',
                'title': f'{stock_data["symbol"]} - Stor prisendring',
                'message': f'Prisen har endret seg {stock_data["price_change"]:.1%} {direction} til {stock_data["current_price"]:.2f}',
                'action': 'Vurder å kjøpe/selge basert på din strategi'
            })
        
        # Volum spike
        if stock_data['volume'] > stock_data['avg_volume'] * self.alert_thresholds['volume_spike']:
            alerts.append({
                'type': 'volume_spike',
                'severity': 'medium',
                'title': f'{stock_data["symbol"]} - Volumspike',
                'message': f'Volumet er {stock_data["volume"] / stock_data["avg_volume"]:.1f}x høyere enn normalt',
                'action': 'Sjekk nyheter og markedssentiment'
            })
        
        # RSI varsler
        if stock_data['rsi'] <= self.alert_thresholds['rsi_oversold']:
            alerts.append({
                'type': 'rsi_oversold',
                'severity': 'medium',
                'title': f'{stock_data["symbol"]} - Oversolgt',
                'message': f'RSI på {stock_data["rsi"]:.1f} indikerer oversolgt tilstand',
                'action': 'Potensielt kjøpsmulighet hvis fundamentals er sterke'
            })
        elif stock_data['rsi'] >= self.alert_thresholds['rsi_overbought']:
            alerts.append({
                'type': 'rsi_overbought',
                'severity': 'medium',
                'title': f'{stock_data["symbol"]} - Overkjøpt',
                'message': f'RSI på {stock_data["rsi"]:.1f} indikerer overkjøpt tilstand',
                'action': 'Vurder å ta gevinst eller redusere posisjon'
            })
        
        # MACD crossover
        if stock_data['macd'] > stock_data['macd_signal']:
            alerts.append({
                'type': 'macd_bullish',
                'severity': 'low',
                'title': f'{stock_data["symbol"]} - Bullish MACD',
                'message': 'MACD har krysset over signallinjen',
                'action': 'Positivt momentum-signal'
            })
        
        # 52-ukers høyde/bunn
        current_price = stock_data['current_price']
        if current_price >= stock_data['high_52w'] * 0.98:  # Innenfor 2% av 52w high
            alerts.append({
                'type': '52w_high',
                'severity': 'high',
                'title': f'{stock_data["symbol"]} - Nær 52-ukers høyde',
                'message': f'Handlet til {current_price:.2f}, nær 52-ukers høyde på {stock_data["high_52w"]:.2f}',
                'action': 'Vurder å ta gevinst eller sett trailing stop'
            })
        elif current_price <= stock_data['low_52w'] * 1.02:  # Innenfor 2% av 52w low
            alerts.append({
                'type': '52w_low',
                'severity': 'high',
                'title': f'{stock_data["symbol"]} - Nær 52-ukers bunn',
                'message': f'Handlet til {current_price:.2f}, nær 52-ukers bunn på {stock_data["low_52w"]:.2f}',
                'action': 'Potensielt kjøpsmulighet hvis selskapet er fundamentalt sterkt'
            })
        
        return alerts
    
    def generate_weekly_ai_report(self, watchlist_items):
        """Generer ukentlig AI-rapport for watchlist"""
        report = {
            'period': 'Siste 7 dager',
            'generated_at': datetime.now(),
            'summary': {
                'total_stocks': len(watchlist_items),
                'alerts_generated': 0,
                'best_performer': None,
                'worst_performer': None,
                'recommendations': []
            },
            'stock_analysis': []
        }
        
        performances = []
        
        for item in watchlist_items:
            stock_data = self.get_stock_data(item.symbol, period="7d")
            if not stock_data:
                continue
            
            # Beregn 7-dagers performance
            try:
                if yf is not None:
                    ticker = yf.Ticker(item.symbol)
                    hist = ticker.history(period="7d")
                    if len(hist) > 1:
                        weekly_return = (hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]
                        performances.append({
                            'symbol': item.symbol,
                            'return': weekly_return,
                            'current_price': stock_data['current_price']
                        })
                else:
                    # Fallback when yfinance not available
                    weekly_return = ((hash(item.symbol) % 21) - 10) / 100  # Random-ish return -0.1 to +0.1
                    performances.append({
                        'symbol': item.symbol,
                        'return': weekly_return,
                        'current_price': stock_data.get('current_price', 100.0)
                    })
                    
                    # AI-analyse og anbefalinger
                    analysis = self.generate_ai_stock_analysis(stock_data, hist)
                    report['stock_analysis'].append(analysis)
                    
            except Exception as e:
                current_app.logger.error(f"Feil ved ukentlig analyse for {item.symbol}: {e}")
        
        # Finn beste og verste performer
        if performances:
            best = max(performances, key=lambda x: x['return'])
            worst = min(performances, key=lambda x: x['return'])
            
            report['summary']['best_performer'] = {
                'symbol': best['symbol'],
                'return': best['return'],
                'current_price': best['current_price']
            }
            
            report['summary']['worst_performer'] = {
                'symbol': worst['symbol'],
                'return': worst['return'],
                'current_price': worst['current_price']
            }
        
        # Generer overordnede anbefalinger
        report['summary']['recommendations'] = self.generate_portfolio_recommendations(performances)
        
        return report
    
    def generate_ai_stock_analysis(self, stock_data, hist_data):
        """Generer AI-analyse for enkeltaksje"""
        analysis = {
            'symbol': stock_data['symbol'],
            'company_name': stock_data['company_name'],
            'current_price': stock_data['current_price'],
            'ai_score': 0,
            'sentiment': 'neutral',
            'key_metrics': {},
            'recommendations': [],
            'risk_level': 'medium'
        }
        
        # Beregn AI-score basert på tekniske indikatorer
        score = 50  # Nøytral start
        
        # RSI-bidrag
        rsi = stock_data['rsi']
        if 40 <= rsi <= 60:
            score += 10  # Balansert RSI
        elif rsi < 30:
            score += 15  # Oversolgt - potensielt kjøp
        elif rsi > 70:
            score -= 10  # Overkjøpt
        
        # MACD-bidrag
        if stock_data['macd'] > stock_data['macd_signal']:
            score += 10  # Bullish momentum
        else:
            score -= 5
        
        # Volum-bidrag
        if stock_data['volume'] > stock_data['avg_volume'] * 1.5:
            score += 5  # Økt interesse
        
        # Prisutvikling siste uke
        if len(hist_data) > 5:
            weekly_return = (hist_data['Close'].iloc[-1] - hist_data['Close'].iloc[-5]) / hist_data['Close'].iloc[-5]
            if weekly_return > 0.02:
                score += 8
            elif weekly_return < -0.02:
                score -= 8
        
        analysis['ai_score'] = max(0, min(100, score))
        
        # Sentiment basert på score
        if analysis['ai_score'] >= 70:
            analysis['sentiment'] = 'bullish'
            analysis['risk_level'] = 'low'
        elif analysis['ai_score'] <= 30:
            analysis['sentiment'] = 'bearish'
            analysis['risk_level'] = 'high'
        else:
            analysis['sentiment'] = 'neutral'
            analysis['risk_level'] = 'medium'
        
        # Key metrics
        analysis['key_metrics'] = {
            'rsi': stock_data['rsi'],
            'macd': stock_data['macd'],
            'volume_ratio': stock_data['volume'] / stock_data['avg_volume'],
            'distance_from_52w_high': (stock_data['current_price'] / stock_data['high_52w'] - 1) * 100,
            'distance_from_52w_low': (stock_data['current_price'] / stock_data['low_52w'] - 1) * 100
        }
        
        # Generer anbefalinger
        analysis['recommendations'] = self.generate_stock_recommendations(analysis)
        
        return analysis
    
    def generate_stock_recommendations(self, analysis):
        """Generer AI-anbefalinger for aksje"""
        recommendations = []
        
        if analysis['ai_score'] >= 70:
            recommendations.append({
                'type': 'buy',
                'confidence': 'high',
                'reason': 'Sterke tekniske signaler og positivt momentum'
            })
        elif analysis['ai_score'] >= 60:
            recommendations.append({
                'type': 'hold',
                'confidence': 'medium',
                'reason': 'Balanserte indikatorer, avvent videre utvikling'
            })
        elif analysis['ai_score'] <= 30:
            recommendations.append({
                'type': 'sell',
                'confidence': 'medium',
                'reason': 'Svake tekniske signaler, vurder å redusere posisjon'
            })
        
        # Spesifikke anbefalinger basert på metrics
        if analysis['key_metrics']['rsi'] < 30:
            recommendations.append({
                'type': 'watch',
                'confidence': 'medium',
                'reason': 'Oversolgt tilstand kan gi kjøpsmulighet'
            })
        
        if analysis['key_metrics']['volume_ratio'] > 2:
            recommendations.append({
                'type': 'investigate',
                'confidence': 'high',
                'reason': 'Uvanlig høyt volum - sjekk nyheter og innsideinformasjon'
            })
        
        return recommendations
    
    def generate_portfolio_recommendations(self, performances):
        """Generer overordnede porteføljeanbefalinger"""
        recommendations = []
        
        if not performances:
            return recommendations
        
        # Analyser diversifisering og risiko
        returns = [p['return'] for p in performances]
        avg_return = np.mean(returns)
        volatility = np.std(returns)
        
        if avg_return > 0.02:  # 2% ukentlig avkastning
            recommendations.append({
                'type': 'positive',
                'title': 'Sterk porteføljeytelse',
                'message': f'Gjennomsnittlig ukentlig avkastning på {avg_return:.1%}',
                'action': 'Vurder å ta noe gevinst og rebalansere'
            })
        elif avg_return < -0.02:
            recommendations.append({
                'type': 'warning',
                'title': 'Svak porteføljeytelse',
                'message': f'Gjennomsnittlig ukentlig tap på {abs(avg_return):.1%}',
                'action': 'Vurder å kutte tapende posisjoner og diversifisere'
            })
        
        if volatility > 0.1:  # 10% volatilitet
            recommendations.append({
                'type': 'info',
                'title': 'Høy volatilitet',
                'message': f'Porteføljevolatilitet på {volatility:.1%}',
                'action': 'Vurder å legge til mer stabile aksjer'
            })
        
        return recommendations

@watchlist_bp.route('/')
@login_required
def watchlist_index():
    """Watchlist index with ETag caching based on user id and item count+latest update."""
    from ..models.watchlist import Watchlist, WatchlistItem
    try:
        watchlist = Watchlist.query.filter_by(user_id=current_user.id).order_by(Watchlist.id).first()
        item_count = 0
        last_updated = '0'
        if watchlist:
            items = WatchlistItem.query.filter_by(watchlist_id=watchlist.id).all()
            item_count = len(items)
            if items:
                # assume each has updated_at or created_at
                timestamps = []
                for it in items:
                    ts = getattr(it, 'updated_at', None) or getattr(it, 'created_at', None)
                    if ts:
                        timestamps.append(ts.isoformat())
                if timestamps:
                    last_updated = max(timestamps)
        import hashlib
        etag_base = f"watchlist:{current_user.id}:{item_count}:{last_updated}"
        etag = hashlib.sha1(etag_base.encode()).hexdigest()
        if request.headers.get('If-None-Match') == etag:
            return '', 304
        resp = render_template('watchlist/index.html', watchlists=[watchlist] if watchlist else [], demo_mode=False)
        response = current_app.make_response(resp)
        response.headers['ETag'] = etag
        return response
    except Exception as e:
        current_app.logger.error(f"Watchlist index error: {e}")
        return render_template('watchlist/index.html', watchlists=[], demo_mode=False)

@watchlist_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_watchlist():
    """Opprett ny watchlist"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        
        if not name:
            flash('Navn er påkrevd', 'error')
            return redirect(url_for('watchlist_advanced.create_watchlist'))
        
        watchlist = Watchlist(
            name=name,
            description=description,
            user_id=current_user.id
        )
        
        db.session.add(watchlist)
        db.session.commit()
        
        flash(f'Watchlist "{name}" opprettet!', 'success')
        return redirect(url_for('watchlist_advanced.view_watchlist', id=watchlist.id))
    
    return render_template('watchlist/create.html')

@watchlist_bp.route('/<int:id>')
@login_required
def view_watchlist(id):
    """Vis spesifikk watchlist"""
    watchlist = Watchlist.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    # Hent ferske data for alle aksjer
    analyzer = WatchlistAnalyzer()
    stock_data = []
    
    for item in watchlist.items:
        try:
            data = analyzer.get_stock_data(item.symbol)
            if data:
                # Generer alerts for denne aksjen using the new notification settings
                user_preferences = current_user.get_notification_settings()
                alerts = analyzer.analyze_alerts(data, user_preferences)
                data['alerts'] = alerts
                stock_data.append(data)
            else:
                # Fallback: show basic info even if data fetch fails
                fallback_data = {
                    'symbol': item.symbol,
                    'name': item.symbol,
                    'current_price': 100.0 + (hash(item.symbol) % 100),
                    'price_change': ((hash(item.symbol) % 21) - 10) / 100,
                    'volume': 1000000 + (hash(item.symbol) % 500000),
                    'note': 'Demo data - kunne ikke hente ferske priser',
                    'alerts': []
                }
                stock_data.append(fallback_data)
        except Exception as e:
            current_app.logger.error(f"Error getting data for {item.symbol}: {e}")
            # Still show the stock with fallback data
            fallback_data = {
                'symbol': item.symbol,
                'name': item.symbol,
                'current_price': 100.0,
                'price_change': 0.0,
                'volume': 1000000,
                'note': 'Feil ved henting av data',
                'alerts': []
            }
            stock_data.append(fallback_data)
    
    return render_template('watchlist/view.html', watchlist=watchlist, stock_data=stock_data)

@watchlist_bp.route('/<int:id>/add_stock', methods=['POST'])
@login_required
def add_stock(id):
    """Legg til aksje i watchlist med forbedret error handling"""
    try:
        watchlist = Watchlist.query.filter_by(id=id, user_id=current_user.id).first()
        if not watchlist:
            flash('Watchlist ikke funnet', 'error')
            return redirect(url_for('watchlist_advanced.index'))
        
        symbol = request.form.get('symbol', '').upper().strip()
        notes = request.form.get('notes', '')
        
        if not symbol:
            flash('Ticker-symbol er påkrevd', 'error')
            return redirect(url_for('watchlist_advanced.view_watchlist', id=id))
        
        # Sjekk om aksjen allerede er i watchlist
        existing = WatchlistItem.query.filter_by(watchlist_id=id, symbol=symbol).first()
        if existing:
            flash(f'{symbol} er allerede i watchlist', 'warning')
            return redirect(url_for('watchlist_advanced.view_watchlist', id=id))
        
        # Create new watchlist item directly without complex validation
        item = WatchlistItem(
            watchlist_id=id,
            symbol=symbol,
            notes=notes,
            added_at=datetime.now()
        )
        
        db.session.add(item)
        db.session.commit()
        
        current_app.logger.info(f"Successfully added {symbol} to watchlist {id} for user {current_user.id}")
        flash(f'✅ {symbol} lagt til i watchlist!', 'success')
        
        # Force reload of the watchlist page
        return redirect(url_for('watchlist_advanced.view_watchlist', id=id))
        
    except Exception as e:
        current_app.logger.error(f"Error adding stock to watchlist: {e}")
        db.session.rollback()
        flash('❌ Feil ved tillegging av aksje til watchlist', 'error')
        return redirect(url_for('watchlist_advanced.view_watchlist', id=id))

@watchlist_bp.route('/item/<int:item_id>/remove', methods=['POST'])
@login_required
def remove_stock(item_id):
    """Fjern aksje fra watchlist"""
    item = WatchlistItem.query.get_or_404(item_id)
    watchlist = Watchlist.query.filter_by(id=item.watchlist_id, user_id=current_user.id).first_or_404()
    
    symbol = item.symbol
    db.session.delete(item)
    db.session.commit()
    
    flash(f'{symbol} fjernet fra watchlist', 'success')
    return redirect(url_for('watchlist_advanced.view_watchlist', id=watchlist.id))

@watchlist_bp.route('/api/alerts')
@login_required
def get_all_alerts():
    """API-endpoint for å hente alle aktive alerts fra alle watchlists"""
    try:
        # Get all user's watchlists
        watchlists = Watchlist.query.filter_by(user_id=current_user.id).all()
        
        analyzer = WatchlistAnalyzer()
        all_alerts = []
        
        for watchlist in watchlists:
            for item in watchlist.items:
                try:
                    stock_data = analyzer.get_stock_data(item.symbol)
                    if stock_data:
                        # Use the new notification settings method
                        user_preferences = current_user.get_notification_settings()
                        alerts = analyzer.analyze_alerts(stock_data, user_preferences)
                        for alert in alerts:
                            alert['symbol'] = item.symbol
                            alert['watchlist_name'] = watchlist.name
                            all_alerts.append(alert)
                except Exception as e:
                    # Skip individual stock errors
                    current_app.logger.warning(f"Error analyzing alerts for {item.symbol}: {e}")
                    continue
        
        return jsonify({
            'alerts': all_alerts,
            'count': len(all_alerts),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching alerts: {e}")
        return jsonify({
            'alerts': [],
            'count': 0,
            'error': 'Could not load alerts',
            'timestamp': datetime.now().isoformat()
        })

@watchlist_bp.route('/api/alerts/<int:watchlist_id>')
@login_required
def get_alerts(watchlist_id):
    """API-endpoint for å hente aktive alerts"""
    watchlist = Watchlist.query.filter_by(id=watchlist_id, user_id=current_user.id).first_or_404()
    
    analyzer = WatchlistAnalyzer()
    all_alerts = []
    
    for item in watchlist.items:
        stock_data = analyzer.get_stock_data(item.symbol)
        if stock_data:
            # Use the new notification settings method
            user_preferences = current_user.get_notification_settings()
            alerts = analyzer.analyze_alerts(stock_data, user_preferences)
            for alert in alerts:
                alert['symbol'] = item.symbol
                alert['watchlist_name'] = watchlist.name
                all_alerts.append(alert)
    
    return jsonify({
        'alerts': all_alerts,
        'count': len(all_alerts),
        'timestamp': datetime.now().isoformat()
    })

@watchlist_bp.route('/api/weekly_report/<int:watchlist_id>')
@login_required
def get_weekly_report(watchlist_id):
    """API-endpoint for ukentlig AI-rapport"""
    watchlist = Watchlist.query.filter_by(id=watchlist_id, user_id=current_user.id).first_or_404()
    
    analyzer = WatchlistAnalyzer()
    report = analyzer.generate_weekly_ai_report(watchlist.items)
    
    return jsonify(report)

@watchlist_bp.route('/send_weekly_report')
def send_weekly_reports():
    """Scheduled task: Send ukentlige rapporter til alle brukere"""
    try:
        users_with_watchlists = User.query.join(Watchlist).filter(User.email_notifications == True).all()
        
        for user in users_with_watchlists:
            watchlists = Watchlist.query.filter_by(user_id=user.id).all()
            
            if not watchlists:
                continue
            
            analyzer = WatchlistAnalyzer()
            combined_report = {
                'user': user.username,
                'watchlists': [],
                'generated_at': datetime.now()
            }
            
            for watchlist in watchlists:
                if watchlist.items:
                    report = analyzer.generate_weekly_ai_report(watchlist.items)
                    report['watchlist_name'] = watchlist.name
                    combined_report['watchlists'].append(report)
            
            # Send e-post
            if combined_report['watchlists']:
                send_weekly_email(user, combined_report)
        
        return jsonify({'status': 'success', 'message': 'Ukentlige rapporter sendt'})
        
    except Exception as e:
        current_app.logger.error(f"Feil ved sending av ukentlige rapporter: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def send_weekly_email(user, report_data):
    """Send ukentlig AI-rapport via e-post"""
    try:
        subject = f"📊 Ukentlig AI-rapport fra Aksjeradar"
        
        # Generer HTML-innhold
        html_content = render_template('email/weekly_report.html', 
                                     user=user, 
                                     report=report_data)
        
        msg = EmailMessage(
            subject=subject,
            recipients=[user.email],
            html=html_content,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER')
        )
        
        mail.send(msg)
        current_app.logger.info(f"Ukentlig rapport sendt til {user.email}")
        
    except Exception as e:
        current_app.logger.error(f"Feil ved sending av e-post til {user.email}: {e}")

@watchlist_bp.route('/delete/<int:id>', methods=['POST'])
@demo_access
def delete_watchlist(id):
    """Slett en watchlist"""
    try:
        # For demo users, just return success without actual deletion
        if not current_user.is_authenticated:
            return jsonify({
                'success': True,
                'message': 'Demo: Watchlist deletion simulated'
            })
        
        watchlist = Watchlist.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        
        # Slett alle items først
        WatchlistItem.query.filter_by(watchlist_id=id).delete()
        
        # Så slett watchlist
        db.session.delete(watchlist)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Watchlist "{watchlist.name}" ble slettet'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error deleting watchlist {id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Kunne ikke slette watchlist'
        }), 500

@watchlist_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def notification_settings():
    """Varslingsinnstillinger"""
    if request.method == 'POST':
        try:
            # Get form data
            form_data = request.form.to_dict()
            
            # Convert checkboxes to booleans (unchecked checkboxes don't send data)
            settings = {
                'price_alerts': 'price_alerts' in form_data,
                'price_change_alerts': 'price_change_alerts' in form_data,
                'news_alerts': 'news_alerts' in form_data,
                'earnings_alerts': 'earnings_alerts' in form_data,
                'analyst_alerts': 'analyst_alerts' in form_data,
                'notification_frequency': form_data.get('notification_frequency', 'instant'),
                'email_notifications': 'email_notifications' in form_data,
                'push_notifications': 'push_notifications' in form_data
            }
            
            # Update user notification settings
            success = current_user.update_notification_settings(settings)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Varslingsinnstillinger oppdatert!'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Kunne ikke oppdatere innstillinger'
                }), 500
                
        except Exception as e:
            current_app.logger.error(f"Error updating notification settings: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Feil ved oppdatering av varselinnstillinger'
            }), 500
    
    # GET request - load current settings
    try:
        user_settings = current_user.get_notification_settings()
        return render_template('watchlist/settings.html', 
                             user=current_user, 
                             settings=user_settings)
    except Exception as e:
        current_app.logger.error(f"Error loading notification settings: {str(e)}")
        return render_template('watchlist/settings.html', 
                             user=current_user, 
                             settings={})
